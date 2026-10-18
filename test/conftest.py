"""
conftest.py — Shared pytest fixtures for the dash test suite.

Centralises commonly-used fixtures so individual test files don't each
define their own copy of auto_df, make_spec, make_dr, etc.
"""
import __future__
import contextlib
import importlib.util
import itertools
import sys
import os
import json
import re
import symtable
import tempfile
import time
import types
import warnings

try:
    import fcntl
except ImportError:          # Windows: no advisory locks, no guard
    fcntl = None

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Every temporary file the suite makes goes to one folder per test process
# (each xdist worker and the controller), removed when the process ends.
# Dozens of modules call tempfile.mkdtemp at import or per test and never
# remove the folder; before this, each full run left 15-20 GB in the
# system temporary directory and filled the disk (18oct2026).  TMPDIR is
# set too, so served apps, Stata-free subprocesses and headless Chrome
# write there as well.  A folder an interrupted run left behind is swept
# once it is a day old.
_TMP_PREFIX = "dash_pytest_"


def _remove_tmp(path):
    import shutil
    shutil.rmtree(path, ignore_errors=True)


def _sweep_stale_tmp(root, age=86400):
    now = time.time()
    try:
        names = os.listdir(root)
    except OSError:
        return
    for name in names:
        p = os.path.join(root, name)
        try:
            if (name.startswith(_TMP_PREFIX) and os.path.isdir(p)
                    and now - os.stat(p).st_mtime > age):
                _remove_tmp(p)
        except OSError:
            pass


def _use_process_tmp():
    import atexit
    root = tempfile.gettempdir()
    _sweep_stale_tmp(root)
    d = tempfile.mkdtemp(prefix=_TMP_PREFIX, dir=root)
    os.environ["TMPDIR"] = d
    tempfile.tempdir = d
    atexit.register(_remove_tmp, d)


if not os.path.basename(tempfile.gettempdir()).startswith(_TMP_PREFIX):
    _use_process_tmp()

from bokeh.models import ColumnDataSource
from bokeh.plotting import figure

from dash_render import DashRenderer, GlyphMapper, OptionTranslator, SchemeParser


def pytest_configure(config):
    """Register the markers this suite uses.

    Declared here rather than in pytest.ini because the repository's
    ``.git/info/exclude`` carries ``*.ini``, so a pytest.ini would not be
    tracked and the marker would be unregistered for everyone else -- pytest
    would then warn on every run and ``-m 'not serve'`` would silently select
    nothing.
    """
    config.addinivalue_line(
        "markers",
        "serve: starts a real `bokeh serve` subprocess; slow. "
        "Deselect with -m 'not serve'.",
    )
    config.addinivalue_line(
        "markers",
        "release: the release tier (Chrome, nested pytest runs, subprocess "
        "sweeps, large files).  A run of the whole suite leaves it out "
        "unless DASH_TEST_TIER=release or -m names release (make "
        "test-release); a file, a node id, -k or --lf runs it.",
    )
    config.addinivalue_line(
        "markers",
        "batch: the batch-end tier (test_mode_parity.py).  A run of the "
        "whole suite leaves it out unless DASH_TEST_TIER is batch or "
        "release or -m names batch (make test-all, make test-batch); a "
        "file, a node id, -k or --lf runs it.",
    )
    if not config.pluginmanager.hasplugin("xdist"):
        # xdist registers this itself; without xdist the marks on the parity
        # corpus must still be known, or every run warns.
        config.addinivalue_line(
            "markers", "xdist_group(name): run these tests on one worker")
    # DASH_SUITE_TIMING=<path>: write a per-test/file/worker timing report.
    from test import suite_timing
    suite_timing.register(config)


# ============================================================
# One full-suite run at a time
# ============================================================
# A full run is CPU-bound and, under xdist, saturates every core: two at
# once each take twice as long, and agents were launching a second run to
# "check on" the first.  The invocation that covers the whole suite takes a
# per-user, machine-wide advisory lock at session start and a second one
# exits at once, naming the holder.  A targeted run (a file, a node id, -k,
# --lf) or a collect-only run never takes it.  xdist workers never take it;
# the controller holds it for them.

_SUITE_LOCK = os.environ.get(
    "DASH_SUITE_LOCK",
    os.path.join("/tmp", "dash-full-suite-%s.lock" % os.getuid()),
)


def _covers_whole_suite(args, rootpath, *, keyword="", lastfailed=False,
                        collectonly=False):
    """True when a pytest invocation runs the entire suite.

    ``args`` are the positional arguments pytest received (``config.args``)
    and ``rootpath`` is ``config.rootpath``.  No arguments means the root,
    which is the whole suite; so is the ``test`` directory.  A file, a node
    id, ``-k``, ``--lf`` or ``--collect-only`` is not.
    """
    if keyword or lastfailed or collectonly:
        return False
    root = os.path.abspath(str(rootpath))
    whole = {root, os.path.join(root, "test")}
    for a in (args or [root]):
        p = os.path.abspath(str(a).split("::", 1)[0].rstrip("/"))
        if p not in whole:
            return False
    return True


def pytest_sessionstart(session):
    cfg = session.config
    # Strict mode (WP-25): a run under another environment than its
    # baseline stops before any test.  The controller decides; xdist
    # workers inherit its verdict by never starting.
    if _strict() and not hasattr(cfg, "workerinput"):
        problem = _drift_problem(_running_env(),
                                 os.environ.get("DASH_BASELINE", ""))
        if problem:
            raise pytest.UsageError("strict mode (DASH_STRICT=1): " + problem)
    if fcntl is None or hasattr(cfg, "workerinput"):
        return
    if not _covers_whole_suite(
            cfg.args, cfg.rootpath,
            keyword=cfg.getoption("keyword", ""),
            lastfailed=cfg.getoption("lf", False),
            collectonly=cfg.getoption("collectonly", False)):
        return
    fh = open(_SUITE_LOCK, "a+")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        fh.seek(0)
        holder = fh.read().strip() or "unknown"
        fh.close()
        raise pytest.UsageError(
            "a full test-suite run is already in progress (%s). Wait for it "
            "and read its log, or run only the tests you changed: a file, a "
            "node id, -k, or --lf." % holder)
    fh.seek(0)
    fh.truncate()
    fh.write("pid %d, started %s, argv %s" % (
        os.getpid(), time.strftime("%Y-%m-%d %H:%M:%S"),
        " ".join(sys.argv[1:])[:200]))
    fh.flush()
    cfg._dash_suite_lock = fh


def pytest_sessionfinish(session, exitstatus):
    # Strict mode (WP-25): any skip turns a run that passed red.
    cfg = session.config
    if _strict() and not hasattr(cfg, "workerinput"):
        lines = _strict_verdict(_SKIPPED)
        if lines:
            tr = cfg.pluginmanager.get_plugin("terminalreporter")
            for line in lines:
                if tr is not None:
                    tr.write_line(line)
                else:
                    print(line)
            if session.exitstatus == 0:
                session.exitstatus = pytest.ExitCode.TESTS_FAILED
    fh = getattr(session.config, "_dash_suite_lock", None)
    if fh is not None:
        try:
            fcntl.flock(fh, fcntl.LOCK_UN)
            fh.close()
        except OSError:
            pass



#: DASH_TEST_TIER: "batch" keeps the batch tier in a run of the whole
#: suite; "release" keeps the release tier and the batch tier.
TIER_ENV = "DASH_TEST_TIER"

#: The tiers a value of DASH_TEST_TIER keeps.
_TIERS_KEPT = {"batch": ("batch",), "release": ("batch", "release")}


def _runs_tier(mark, args, rootpath, *, keyword="", lastfailed=False,
               collectonly=False, markexpr="", tier=""):
    """Whether a run keeps the tests marked *mark* (``release``: WP-30 test
    performance D; ``batch``: test_mode_parity.py, run at batch ends and at
    release).  A run of the whole suite (``_covers_whole_suite``) is the
    fast default and leaves them out, unless *tier* (DASH_TEST_TIER) keeps
    *mark* or the mark expression *markexpr* names it; any narrower run --
    a file, a node id, -k, --lf, --collect-only -- keeps them."""
    if mark in _TIERS_KEPT.get(tier, ()) or re.search(
            r"\b%s\b" % re.escape(mark), markexpr or ""):
        return True
    return not _covers_whole_suite(args, rootpath, keyword=keyword,
                                   lastfailed=lastfailed,
                                   collectonly=collectonly)


def _runs_release_tier(args, rootpath, **kw):
    """``_runs_tier`` for the release tier."""
    return _runs_tier("release", args, rootpath, **kw)


def _deselect_tier(config, items, mark):
    """Drop the tests marked *mark* from *items* when this run leaves that
    tier out, and report them as deselected; returns them."""
    if _runs_tier(
            mark, config.args, config.rootpath,
            keyword=config.getoption("keyword", ""),
            lastfailed=config.getoption("lf", False),
            collectonly=config.getoption("collectonly", False),
            markexpr=config.getoption("markexpr", ""),
            tier=os.environ.get(TIER_ENV, "")):
        return []
    dropped = [i for i in items if i.get_closest_marker(mark)]
    if dropped:
        keep = [i for i in items if not i.get_closest_marker(mark)]
        items[:] = keep
        config.hook.pytest_deselected(items=dropped)
    return dropped


def _deselect_release_tier(config, items):
    """``_deselect_tier`` for the release tier."""
    return _deselect_tier(config, items, "release")


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    """Keep every comparison of one parity corpus entry on one xdist worker.

    test_mode_parity.py renders each corpus entry once per process and
    compares it eleven ways.  Spread across twelve workers under the default
    distribution each entry was rendered about seven times.  With
    ``--dist loadgroup`` (pyproject.toml) a group runs on a single worker,
    so an entry renders once.  A test module cannot implement this hook;
    only a conftest can.

    ``tryfirst``: an xdist worker reads the ``xdist_group`` marks in its own
    implementation of this hook, which pluggy called first because xdist
    registers it after this conftest is loaded -- so until 07oct2026 no
    mark was there to read and nothing was grouped (test_xdist_groups.py).

    First, a run of the whole suite drops the release tier and the batch
    tier (``_deselect_tier``).
    """
    _deselect_release_tier(config, items)
    _deselect_tier(config, items, "batch")
    for item in items:
        if not item.nodeid.startswith("test/test_mode_parity.py"):
            continue
        params = getattr(getattr(item, "callspec", None), "params", {})
        name = params.get("name")
        if name:
            item.add_marker(pytest.mark.xdist_group(name="parity:" + str(name)))

# ============================================================
# subtests under pytest 8
# ============================================================
# pytest 9 ships the subtests fixture; Stata's Python (make test) carries
# pytest 8.4 without the pytest-subtests plugin, and every test taking
# the fixture errored there.  The stand-in runs each subtest inline, so
# the first failing subtest fails its test.

class _InlineSubtests:

    def test(self, msg=None, **kwargs):
        return contextlib.nullcontext()


if (importlib.util.find_spec("_pytest.subtests") is None
        and importlib.util.find_spec("pytest_subtests") is None):
    @pytest.fixture
    def subtests():
        return _InlineSubtests()


# ============================================================
# An empty global Bokeh document for every test
# ============================================================
# A generated server app calls make_document(curdoc()) when it is imported,
# so each app a test exec's leaves 1 root and about 46 models in the
# process-global document.  Nothing cleared it, Bokeh walks it on every
# later operation, and the served render path slowed from 0.19 s to about
# 1.8 s per test over a run.  See test_bokeh_document_hygiene.py.
# Its document callbacks go too (WP-30 P1.15c): a by() app attaches its
# stacked view to document_ready, and Bokeh copies the global document's
# callbacks into every document file_html() makes (embed.util._new_doc),
# so a later test's saved page carried another app's hook.

@pytest.fixture(autouse=True)
def _clear_bokeh_curdoc():
    yield
    try:
        from bokeh.io import curdoc
        curdoc().clear()
        curdoc().callbacks._js_event_callbacks.clear()
    except Exception:
        pass


# ============================================================
# Generated server apps: each block of text compiled once (WP-30 A3)
# ============================================================
# A generated server app is about 26,000 lines, and the tests compiled every
# one they loaded: 0.14 s of the 0.4 s a served render cost them (measured
# 07oct2026), for a text that differs from the previous app's in a line or
# two -- the embedded spec and data.  load_app and exec_app run the exact
# text of the app they are given, compiled in blocks: each top-level
# statement (with what follows it up to the next one) is compiled once per
# process, keyed by its exact text, its first line and the compiler flags
# it needs, and the blocks run in order in the module's namespace.
#
# What makes that the same program as the file compiled whole:
#   * the blocks are consecutive slices that cover the text exactly, each
#     cut where a line starts in column 0 with a name or a decorator, and
#     merged with the next until it compiles on its own -- a cut inside a
#     string, a bracket or a decorated definition does not;
#   * each block is compiled at its own line numbers, so tracebacks, the
#     code's lines and a class's __firstlineno__ are the file's;
#   * the module's __future__ flags apply from the block that imports them,
#     and every block ends with a dead ``if 0: import ...`` of the names the
#     module imports at its top level: the compiler emits a different call
#     for an attribute of an imported name, and a block compiled alone would
#     not know which names those are;
#   * the module's own annotations, which the compiler sets up at the top
#     of the module, are all in the first block;
#   * a text with a bare carriage return, one that warns as it compiles, and
#     one with any block that will not compile alone is compiled whole, as
#     before.
# test_app_loader.py checks that every function and class code object of a
# real app is equal to the whole compile's.  Nothing here patches the import
# system.

#: A line that may start a top-level statement: a name or a decorator in
#: column 0 -- not a string's prefix, and not a clause continuing a compound
#: statement.
_APP_BLOCK_START = re.compile(
    r"^(?![rRbBuUfFtT]{1,2}['\"])(?!(?:else|elif|except|finally)\b)"
    r"[A-Za-z_@]", re.M)
#: Every __future__ feature's compiler flag.
_APP_FUTURE_FLAGS = 0
for _feature in __future__.all_feature_names:
    _APP_FUTURE_FLAGS |= getattr(__future__, _feature).compiler_flag
#: The most blocks either cache holds; the older half goes when it is full.
_APP_CACHE_MAX = 8192
#: Block text -> (names imported at its top level, whether it annotates a
#: top-level name), None when it does not parse alone, or _APP_WARNS.
_APP_BLOCK_INFO = {}
#: (block text, compiler flags, dead-import tail, first line) -> code
#: object compiled under a placeholder file name, or None.
_APP_BLOCK_CODE = {}
#: Counters for test_app_loader.py: blocks compiled, blocks reused, and texts
#: compiled whole.
APP_LOADER_STATS = {"compiled": 0, "reused": 0, "whole": 0}
_APP_MISSING = object()
_APP_WARNS = object()
_APP_PLACEHOLDER = "<dash app block>"


def _app_cache_put(cache, key, value):
    """Store *value*, dropping the older half of *cache* when it is full."""
    if len(cache) >= _APP_CACHE_MAX:
        for old in list(itertools.islice(cache, len(cache) // 2)):
            del cache[old]
    cache[key] = value


def _app_block_info(text):
    """``(imported names, annotates)`` for a block's top level, None when
    the block does not parse alone, or _APP_WARNS when parsing it warns --
    a warning the whole compile must then raise where the caller sees it."""
    hit = _APP_BLOCK_INFO.get(text, _APP_MISSING)
    if hit is not _APP_MISSING:
        return hit
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            table = symtable.symtable(text, _APP_PLACEHOLDER, "exec")
        except (SyntaxError, ValueError):
            table = None
    if caught:
        info = _APP_WARNS
    elif table is None:
        info = None
    else:
        syms = table.get_symbols()
        info = (frozenset(s.get_name() for s in syms if s.is_imported()),
                any(s.is_annotated() for s in syms))
    _app_cache_put(_APP_BLOCK_INFO, text, info)
    return info


def _app_blocks(source):
    """``([(start, end)], imported names)``: the offsets of the blocks that
    cover *source* exactly, and the names its top level imports; or None
    when it is to be compiled whole."""
    if "\r" in source:
        return None
    bounds = [0] + [m.start() for m in _APP_BLOCK_START.finditer(source)
                    if m.start()] + [len(source)]
    spans, imported, annotated = [], set(), -1
    i = 0
    while i < len(bounds) - 1:
        j = i + 1
        info = _app_block_info(source[bounds[i]:bounds[j]])
        while info is None:
            j += 1
            if j == len(bounds):
                return None
            info = _app_block_info(source[bounds[i]:bounds[j]])
        if info is _APP_WARNS:
            return None
        imported |= info[0]
        if info[1]:
            annotated = len(spans)
        spans.append((bounds[i], bounds[j]))
        i = j
    if annotated > 0:
        spans = [(0, spans[annotated][1])] + spans[annotated + 1:]
    return spans, frozenset(imported)


def _app_block_code(text, flags, tail, line):
    """*text* compiled with its first line at *line*, or None when it does
    not compile alone or warns as it compiles."""
    key = (text, flags, tail, line)
    hit = _APP_BLOCK_CODE.get(key, _APP_MISSING)
    if hit is not _APP_MISSING:
        if hit is not None:
            APP_LOADER_STATS["reused"] += 1
        return hit
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            code = compile("\n" * (line - 1) + text + tail, _APP_PLACEHOLDER,
                           "exec", flags=flags, dont_inherit=True)
        except (SyntaxError, ValueError):
            code = None
    if caught:
        code = None
    if code is not None:
        APP_LOADER_STATS["compiled"] += 1
    _app_cache_put(_APP_BLOCK_CODE, key, code)
    return code


def _app_code_in(code, filename):
    """*code* and every code object nested in it, as compiled from
    *filename*."""
    consts = code.co_consts
    if any(isinstance(c, types.CodeType) for c in consts):
        consts = tuple(_app_code_in(c, filename)
                       if isinstance(c, types.CodeType) else c
                       for c in consts)
    return code.replace(co_filename=filename, co_consts=consts)


def compile_app(source, filename):
    """The code objects that run *source*, the text of a generated server
    app, as a module compiled from *filename* would run, in order."""
    whole = None
    plan = _app_blocks(source)
    if plan is not None:
        spans, imported = plan
        tail = ("if 0: import %s\n" % ", ".join(sorted(imported))
                if imported else "")
        codes, flags, line, pos = [], 0, 1, 0
        for start, end in spans:
            text = source[start:end]
            line += source.count("\n", pos, start)
            pos = start
            sep = "" if (not tail or not text or text.endswith("\n")) else "\n"
            code = _app_block_code(text, flags, sep + tail, line)
            if code is None:
                break
            flags |= code.co_flags & _APP_FUTURE_FLAGS
            codes.append(_app_code_in(code, filename))
        else:
            whole = codes
    if whole is None:
        APP_LOADER_STATS["whole"] += 1
        whole = [compile(source, filename, "exec", dont_inherit=True)]
    return whole


def exec_app(source, filename, namespace):
    """Run *source*, a generated app's text, in *namespace* as the module
    compiled from *filename* would run; returns *namespace*."""
    for code in compile_app(source, filename):
        exec(code, namespace)
    return namespace



def _no_page(*_a, **_k):
    """``file_html``'s stand-in where the page is not kept: a page with no
    script, so the renderer's seal and head splice still run on it."""
    return "<!DOCTYPE html>\n<html><head></head><body></body></html>"


def render_models(renderer):
    """``renderer.render()`` for its models alone: every model is built and
    finished as for the page, but Bokeh's serialisation of the page
    (``file_html``, about two fifths of a render) is skipped.  A test that
    reads the page, or a model's ``document``, calls ``render()``.
    Returns *renderer*."""
    from unittest import mock
    mod = sys.modules[type(renderer).__module__]
    with mock.patch.object(mod, "file_html", _no_page):
        renderer.render()
    return renderer


def load_app(path, name):
    """Import the generated app at *path* as module *name*, as
    ``spec.loader.exec_module`` would -- the same module attributes and the
    same text, read and decoded as the import system reads it -- with its
    blocks compiled once per process (see above).  Like ``exec_module`` it
    does not enter the module in ``sys.modules``."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    with open(spec.origin, "rb") as fh:
        source = importlib.util.decode_source(fh.read())
    exec_app(source, spec.origin, module.__dict__)
    return module


# ============================================================
# Environment pinning
# ============================================================
# The suite runs under two interpreters, with different libraries (WP-25):
#
#   stata   /opt/anaconda3/bin/python3, Stata's c(python_exec): the Python
#           every Stata-built dashboard is rendered with, so the one that
#           ships
#   dev     /opt/homebrew/bin/python3, the development interpreter
#
# A green run under one proves nothing about the other.  Measured 24sep2026,
# the first time the suite ran under Stata's Python: its bokeh 3.8 let the
# served app admit a websocket origin bokeh 3.9 refuses, and its pandas 2.3
# blanked a whole date column over one far-future value.  Each run is held
# to the baseline DASH_BASELINE names, or else to the one whose Python it
# runs.  Outside strict mode a drift is a warning -- a developer on another
# machine is legitimately on another build -- but never silent.  In strict
# mode (DASH_STRICT=1, which `make check' sets) it stops the run before any
# test, and any skip turns the run red at its end: a skip is not a pass.
#
# WP-30 P1.33: py311, py311-dev, py312 and py312-dev are the floor matrix's
# stacks (scripts/floor_matrix.sh, make test-floor): the stata pins and the
# dev pins on an older Python, each held by test/requirements-stata.txt or
# test/requirements-dev.txt.  Every entry is a stack both suites pass under,
# and the lowest entry's Python is the declared floor, dash_setup's
# _dash_pymin (test/test_version_floor.py).

_BASELINES = {
    "stata": {"python": "3.13", "bokeh": "3.8", "pandas": "2.3",
              "numpy": "2.3", "scipy": "1.16"},
    "dev": {"python": "3.14", "bokeh": "3.9", "pandas": "3.0",
            "numpy": "2.4", "scipy": "1.17"},
    "py311": {"python": "3.11", "bokeh": "3.8", "pandas": "2.3",
              "numpy": "2.3", "scipy": "1.16"},
    "py311-dev": {"python": "3.11", "bokeh": "3.9", "pandas": "3.0",
                  "numpy": "2.4", "scipy": "1.17"},
    "py312": {"python": "3.12", "bokeh": "3.8", "pandas": "2.3",
              "numpy": "2.3", "scipy": "1.16"},
    "py312-dev": {"python": "3.12", "bokeh": "3.9", "pandas": "3.0",
                  "numpy": "2.4", "scipy": "1.17"},
}


def _mm(version: str) -> str:
    """Return the major.minor prefix of a version string."""
    parts = str(version).split(".")
    return ".".join(parts[:2])


def _running_env() -> dict:
    """The major.minor of the running Python and of each pinned library."""
    import importlib

    actual = {"python": _mm("%d.%d" % sys.version_info[:2])}
    for pkg in ("bokeh", "pandas", "numpy", "scipy"):
        try:
            actual[pkg] = _mm(importlib.import_module(pkg).__version__)
        except Exception:
            actual[pkg] = "missing"
    return actual


def _baseline_name(actual: dict, requested: str = "") -> str:
    """The baseline to hold *actual* to, in three steps: *requested*
    (DASH_BASELINE) when given; else the first baseline *actual* matches in
    every pin; else the first whose Python matches; else "dev".  The full
    match comes first because an older Python has two baselines (py311 and
    py311-dev, WP-30 P1.33), and the first by Python alone is wrong for the
    second's stack."""
    if requested:
        return requested
    for name, env in _BASELINES.items():
        if not _env_drift(actual, env):
            return name
    for name, env in _BASELINES.items():
        if env["python"] == actual.get("python"):
            return name
    return "dev"


def _env_drift(actual: dict, baseline: dict) -> dict:
    """``{pin: (baseline, running)}`` for each pin *actual* misses; empty
    when the running environment matches *baseline*."""
    return {k: (v, actual.get(k, "missing")) for k, v in baseline.items()
            if actual.get(k, "missing") != v}


def _strict() -> bool:
    """Whether this run is strict: DASH_STRICT=1."""
    return os.environ.get("DASH_STRICT", "") == "1"


STATA_BASE_DEFAULT = "/Applications/StataNow/ado/base"
STATA_PLUS_DEFAULT = "~/Library/Application Support/Stata/ado/plus"


def stata_base():
    """Stata's base ado tree: DASH_STATA_BASE, else StataNow's (WP-30 P1.34)."""
    return os.environ.get("DASH_STATA_BASE") or STATA_BASE_DEFAULT


def stata_plus():
    """Stata's PLUS tree: DASH_STATA_PLUS, else the macOS default."""
    return os.path.expanduser(os.environ.get("DASH_STATA_PLUS") or STATA_PLUS_DEFAULT)


def _drift_problem(actual: dict, requested: str = "") -> str:
    """Why *actual* fails its baseline, or "" when it does not."""
    name = _baseline_name(actual, requested)
    if name not in _BASELINES:
        return ("DASH_BASELINE=%s names no baseline; the baselines are %s "
                "(test/conftest.py)." % (name, ", ".join(sorted(_BASELINES))))
    drift = _env_drift(actual, _BASELINES[name])
    if not drift:
        return ""
    return ("the environment differs from the %s baseline (%s); see "
            "_BASELINES in test/conftest.py." % (name, ", ".join(
                f"{k}: baseline {want}, running {got}"
                for k, (want, got) in drift.items())))


def _skip_reason(report) -> str:
    """The reason a skipped report gives."""
    longrepr = report.longrepr
    if isinstance(longrepr, tuple) and len(longrepr) == 3:
        return str(longrepr[2])
    return str(longrepr)


#: (node id, reason) for every test or module skipped in this process.
_SKIPPED: "list[tuple[str, str]]" = []


def pytest_runtest_logreport(report):
    """Record each skipped test for strict mode's verdict.  Under xdist the
    controller receives every worker's reports through this hook."""
    if report.skipped and not hasattr(report, "wasxfail"):
        _SKIPPED.append((report.nodeid, _skip_reason(report)))


def pytest_collectreport(report):
    """Record a module skipped whole at collection (``importorskip``)."""
    if report.skipped:
        _SKIPPED.append((report.nodeid, _skip_reason(report)))


def _strict_verdict(skipped: "list[tuple[str, str]]") -> "list[str]":
    """Strict mode's report on the skips of a run: empty when there were
    none, else the lines to print."""
    if not skipped:
        return []
    lines = ["strict mode (DASH_STRICT=1): %d test(s) skipped, and a skip is "
             "not a pass:" % len(skipped)]
    lines += ["  %s -- %s" % (nodeid, reason) for nodeid, reason in skipped]
    return lines


@pytest.fixture(scope="session", autouse=True)
def pinned_environment():
    """Warn when the interpreter or its libraries drift from their baseline.
    In strict mode the drift has already stopped the run (pytest_sessionstart)."""
    import warnings

    actual = _running_env()
    problem = _drift_problem(actual, os.environ.get("DASH_BASELINE", ""))
    if problem:
        warnings.warn("dash test suite: " + problem + " Results may not be "
                      "comparable to a run under the baseline.", UserWarning)
    return actual


# ============================================================
# Core dataset fixture
# ============================================================

@pytest.fixture
def auto_df():
    """Synthetic 74-row dataset mimicking Stata's auto.dta.

    Used across GlyphMapper, filter, KPI, and pipeline tests.
    Seed is fixed so tests are deterministic.
    """
    np.random.seed(42)
    n = 74
    return pd.DataFrame({
        "mpg":    np.random.randint(12, 40, n).astype(float),
        "weight": np.random.randint(1760, 4840, n).astype(float),
        "price":  np.random.randint(3291, 15906, n).astype(float),
        "length": np.random.randint(142, 233, n).astype(float),
        "foreign": np.random.choice([0, 1], n).astype(float),
        "rep78":   np.random.choice([1.0, 2.0, 3.0, 4.0, 5.0, np.nan], n),
    })


# ============================================================
# Bokeh primitives
# ============================================================

@pytest.fixture
def cds(auto_df):
    """ColumnDataSource built from the synthetic auto DataFrame."""
    return ColumnDataSource(auto_df)


@pytest.fixture
def fig():
    """Blank Bokeh Figure suitable for mapper tests."""
    return figure()


@pytest.fixture
def gm():
    """Default GlyphMapper instance (s2color scheme)."""
    scheme = SchemeParser("s2color")
    return GlyphMapper(OptionTranslator(), scheme)


# ============================================================
# DashRenderer helpers
# ============================================================

def make_spec(
    plots: list,
    *,
    link: str = "",
    filters: "list | None" = None,
    hover: str = "",
    graph_name: str = "g1",
    theme: str = "default",
    extra_graphs: "list | None" = None,
    kpis: "list | None" = None,
) -> dict:
    """Build a minimal DashRenderer spec dict from a list of plot dicts.

    Args:
        plots:         List of plot spec dicts (type, yvar, xvar, options).
        link:          Link spec string, e.g. ``"g1"`` or ``"_all"``.
        filters:       List of filter spec dicts for build_options.filters.
        hover:         Space-separated hover variable list for graph_options.
        graph_name:    Name for the single graph (default ``"g1"``).
        theme:         Bokeh scheme name (default ``"default"``).
        extra_graphs:  Additional graph specs to include alongside the main one.
        kpis:          List of KPI spec dicts.

    Returns:
        A dict conforming to the DashRenderer spec format.
    """
    go: dict = {"name": graph_name}
    if hover:
        go["hover"] = hover

    graphs = [{"plots": plots, "graph_options": go,
                "if_expr": "", "in_expr": ""}]
    if extra_graphs:
        graphs.extend(extra_graphs)

    build: dict = {
        "layout": "auto",
        "link": link,
        "theme": theme,
        "title": "",
        "subtitle": "",
        "registry": graph_name,
    }
    if filters:
        build["filters"] = filters

    return {
        "graphs": graphs,
        "kpis": kpis or [],
        "build_options": build,
    }


def make_data_json(
    df: pd.DataFrame,
    value_labels: "dict | None" = None,
    value_label_names: "dict | None" = None,
    variable_labels: "dict | None" = None,
) -> dict:
    """Serialise a DataFrame to the StataJSON wrapper dict.

    ``variableLabels`` is written as Stata's exporter writes it: an
    unlabelled variable's label is ``""``, exactly what
    ``dash_render._dash_write_stata_data`` writes for it.  This helper used
    to give every variable a label equal to its name, which hid WP-29 P0.3
    (unlabelled variables drawn with blank titles, keys and tooltip rows).

    Args:
        df:               DataFrame whose columns become variableNames.
        value_labels:     Optional ``{labelset: {code: text}}`` mapping.
        value_label_names: Optional ``{varname: labelset}`` mapping.
        variable_labels:  Optional ``{varname: label}``; a variable not named
                          is unlabelled (``""``).

    Returns:
        A ``{"StataJSON": {...}}`` dict suitable for writing to a data JSON file.
    """
    varnames = list(df.columns)
    values = []
    for _, row in df.iterrows():
        entry: dict = {}
        for col in varnames:
            val = row[col]
            entry[col] = None if (isinstance(val, float) and np.isnan(val)) else val
        values.append(entry)

    return {"StataJSON": {
        "variableNames": varnames,
        "variableLabels": {v: (variable_labels or {}).get(v, "")
                           for v in varnames},
        "valueLabels": value_labels or {},
        "valueLabelNames": value_label_names or {},
        # BOTH keys: real jsonio emits "variableIsString", while
        # StataAllToJSON's advertised field list says "variableTypeIsString".
        # This helper used to fabricate only the latter, so dash's string-
        # column detection was never exercised against the key production
        # actually sends -- and the bug that every string and date column was
        # coerced to NaN was invisible to the whole suite.
        "variableTypeIsString": {v: False for v in varnames},
        "variableIsString": {v: False for v in varnames},
        "values": values,
    }}


def make_dr(
    plots: list,
    df: "pd.DataFrame | None" = None,
    *,
    link: str = "",
    filters: "list | None" = None,
    hover: str = "",
    graph_name: str = "g1",
    value_labels: "dict | None" = None,
    value_label_names: "dict | None" = None,
    render: bool = True,
) -> DashRenderer:
    """Build (and optionally render) a DashRenderer from inline Python data.

    Args:
        plots:        List of plot spec dicts.
        df:           DataFrame for the data file.  Defaults to a small
                      synthetic 10-row auto-like dataset when ``None``.
        link:         Link spec for build_options.
        filters:      Filter specs for build_options.filters.
        hover:        Hover variable string for graph_options.hover.
        graph_name:   Graph name (default ``"g1"``).
        value_labels: Optional value-label mapping.
        value_label_names: Optional variable→labelset mapping.
        render:       If ``True`` (default) call ``dr.render()`` before
                      returning.

    Returns:
        A DashRenderer instance (rendered if *render* is True).
    """
    if df is None:
        np.random.seed(42)
        n = 10
        df = pd.DataFrame({
            "mpg":    np.linspace(15, 35, n),
            "weight": np.linspace(2000, 4000, n),
            "price":  np.linspace(4000, 12000, n),
            "foreign": [0.0, 1.0] * (n // 2),
        })

    spec = make_spec(
        plots, link=link, filters=filters, hover=hover, graph_name=graph_name
    )
    data = make_data_json(df, value_labels=value_labels,
                          value_label_names=value_label_names)

    sp, dp, op = [tempfile.mkstemp(s)[1] for s in (".json", ".json", ".html")]
    try:
        with open(sp, "w") as f:
            json.dump(spec, f)
        with open(dp, "w") as f:
            json.dump(data, f)
        dr = DashRenderer(sp, dp, op)
        if render:
            render_models(dr)
    finally:
        for p in (sp, dp, op):
            try:
                os.unlink(p)
            except OSError:
                pass
    return dr
