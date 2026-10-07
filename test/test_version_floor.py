"""Regression tests for the declared Python/Bokeh/pandas/numpy floor
(GAPS2 K2).

``dash_setup.sthlp:70``, ``dash.pkg:17`` and ``dash_setup.ado:60,73,146``
declared and enforced Python 3.8+ and bokeh>=3.0 -- but every render,
saved or served, imports ``CustomJSTicker``, present only from bokeh
3.6.0, so an installed bokeh 3.0-3.5 passed ``dash_setup`` and then every
``dash`` command failed with r(7102); the generated server app had no
``from __future__ import annotations`` and 55 annotations Python
evaluates at import, raising ``TypeError`` on Python 3.8 and 3.9.

DISCOVERY Q8 settles the floor as what is tested today: the ``stata``
baseline of ``test/conftest.py`` -- Python 3.13, bokeh 3.8, pandas 2.3,
numpy 2.3 -- declared in every file that names a minimum, with pandas
declared by dash itself because bokeh 3.9 dropped it as a required
dependency.

WP-30 P1.33: the Python floor is measured, not the stata baseline's Python.
The floor matrix (scripts/floor_matrix.sh, make test-floor) runs both
suites under older Pythons with the stata and the dev pins, and
test/conftest.py keeps a baseline only for a stack they pass under; the
declared floor, _dash_pymin, is the lowest of those Pythons.  The served
app's child is started with ``-P``, which needs Python 3.11, so the floor
can never go below it.
"""
import ast
import json
import os
import re
import sys
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import _BASELINES, make_data_json  # noqa: E402
from test_program_coverage_map import _ado_programs, _logical_lines  # noqa: E402


def _read(rel):
    with open(os.path.join(_ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def _flat(text):
    return " ".join(text.split())


def _stata_baseline():
    b = _BASELINES["stata"]
    return b["python"], b["bokeh"], b["numpy"], b["pandas"]


def _setup_ado_floor():
    text = _read("dash_setup.ado")
    pymin = re.search(r'return local pymin "([^"]+)"', text)
    bokeh = re.search(r'local\s+min_bokeh\s+"([^"]+)"', text)
    numpy = re.search(r'local\s+min_numpy\s+"([^"]+)"', text)
    pandas = re.search(r'local\s+min_pandas\s+"([^"]+)"', text)
    assert pymin and bokeh and numpy and pandas, (
        "the floor lines were not found in dash_setup.ado")
    return pymin.group(1), bokeh.group(1), numpy.group(1), pandas.group(1)


class TestTheFloorIsTheTestedBaseline:
    def test_dash_setup_declares_the_stata_baseline(self):
        _py, bo, nu, pa = _setup_ado_floor()
        _want_py, want_bo, want_nu, want_pa = _stata_baseline()
        assert bo == want_bo, (bo, want_bo)
        assert nu == want_nu, (nu, want_nu)
        assert pa == want_pa, (pa, want_pa)

    def test_the_python_floor_is_the_lowest_baseline_python(self):
        """WP-30 P1.33: the floor is the lowest Python both suites pass
        under, which test/conftest.py's baselines record."""
        lowest = min((b["python"] for b in _BASELINES.values()),
                     key=lambda v: tuple(map(int, v.split("."))))
        assert _setup_ado_floor()[0] == lowest

    def test_every_declaration_agrees_with_dash_setup(self):
        py, bo, nu, pa = _setup_ado_floor()

        pkg = _read("dash.pkg")
        assert ("Requires: Python %s+, bokeh>=%s, numpy>=%s, pandas>=%s."
                % (py, bo, nu, pa)) in pkg, pkg

        ado = _read("dash.ado")
        assert ("Python %s+" % py) in ado, ado

        help_ = _flat(_read("dash.sthlp"))
        assert ("{ul:Python %s+}" % py) in help_, help_
        assert ("bokeh>=%s, numpy>=%s, pandas>=%s"
                % (bo, nu, pa)) in help_, help_

        shelp = _flat(_read("dash_setup.sthlp"))
        assert ("Python %s or later" % py) in shelp, shelp
        assert ("{opt bokeh}}%s or later" % bo) in shelp, shelp
        assert ("{opt numpy}}%s or later" % nu) in shelp, shelp
        assert ("{opt pandas}}%s or later" % pa) in shelp, shelp
        assert ("below %s" % py) in shelp, shelp
        assert ("one below %s is reported" % bo) in shelp, shelp

        changelog = _flat(_read("CHANGELOG.md"))
        rq_start = changelog.index("### Requirements")
        rq_end = changelog.index("### ", rq_start + 10)
        rq = changelog[rq_start:rq_end]
        assert ("Python %s" % py) in rq, rq
        assert ("bokeh >= %s" % bo) in rq, rq

    def test_the_old_floor_is_named_nowhere_it_matters(self):
        """Precise patterns, not bare substrings: several files carry
        narrative comments that mention old numbers as historical or
        illustrative examples (a docstring's "e.g. 3.8", the story of a
        version() bug measured against "2.4" and "3.0"), which are not
        the declared floor and must not make this test fail."""
        ado_setup = _read("dash_setup.ado")
        for pattern in (r'local\s+min_bokeh\s+"3\.0"',
                        r'local\s+min_numpy\s+"1\.23"',
                        r'local\s+min_pandas\s+"2\.0"',
                        r'return local pymin "3\.8"'):
            assert not re.search(pattern, ado_setup), pattern
        assert "Python 3.8+" not in _read("dash.ado")
        for rel in ("dash.pkg", "dash.sthlp", "dash_setup.sthlp"):
            text = _read(rel)
            for needle in ("Python 3.8", "bokeh>=3.0", "3.0 or later",
                          "1.23 or later", "2.0 or later"):
                assert needle not in text, (rel, needle)
        # WP-30 P1.33: the measured floor replaced 3.13.
        assert 'return local pymin "3.13"' not in ado_setup
        assert "will not install or import reliably" not in ado_setup
        for rel in ("dash.ado", "dash.pkg", "dash.sthlp", "dash_setup.sthlp"):
            text = _read(rel)
            for needle in ("Python 3.13+", "{ul:Python 3.13+}",
                           "Python 3.13 or later"):
                assert needle not in text, (rel, needle)

    def test_the_upgrade_line_names_the_linked_interpreter(self, monkeypatch, capsys):
        """Q27: dash_setup's below-minimum branch prints the pip command
        for the interpreter Stata is linked to, never the bare word
        'python' -- installing with a different interpreter than the one
        Stata runs against would upgrade the wrong Python.

        WP-29 P0.19: the line is built by dash_setup_lib.stata_shell_line,
        which names the resolved c(python_exec) and quotes it for the shell
        (a bare `bokeh>=3.8' is a redirection to a file named =3.8)."""
        import importlib.util
        import types
        ado = _read("dash_setup.ado")
        m = re.search(r"program define _dash_pip_command.*?\bend\b", ado,
                      re.S)
        assert m, "no _dash_pip_command program in dash_setup.ado"
        body = m.group(0)
        assert "stata_shell_line()" in body, body
        assert ">=" in body, body
        below = ado[ado.find('"below"'):]
        below = below[:below.find('"unverified"')]
        assert re.search(r'_dash_pip_command "`pkg\'" "`minver\'" upgrade', below), below
        assert "python -m pip install --upgrade" not in below, below
        spec = importlib.util.spec_from_file_location(
            "dash_setup_lib_floor", os.path.join(_ROOT, "dash_setup_lib.py"))
        lib = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lib)
        loc = {"spec": "bokeh>=3.8", "how": "upgrade"}
        sfi = types.ModuleType("sfi")
        sfi.Macro = types.SimpleNamespace(getLocal=lambda k: loc.get(k, ""),
                                          setLocal=loc.__setitem__)
        exp = {"\x60c(python_exec)'": "/opt/My Python/bin/python3",
               "\x60c(pwd)'": "/tmp"}
        sfi.SFIToolkit = types.SimpleNamespace(macroExpand=exp.__getitem__)
        monkeypatch.setitem(sys.modules, "sfi", sfi)
        lib.stata_shell_line()
        want = "'/opt/My Python/bin/python3' -m pip install 'bokeh>=3.8'"
        assert loc["pip_cmd"] == want
        assert "To upgrade: " + want in capsys.readouterr().out


class TestTheFloorAdmitsTheServedLauncher:
    """WP-30 P1.33: dash serve starts the app as ``sys.executable -P``
    (_dash_launch_app), a flag Python 3.10 refuses ("Unknown option: -P",
    rc 2), so the declared floor may never go below 3.11."""

    def test_the_launch_flags_need_no_newer_python_than_the_floor(self):
        import importlib.util
        import inspect
        spec = importlib.util.spec_from_file_location(
            "dash_setup_lib_launch", os.path.join(_ROOT, "dash_setup_lib.py"))
        lib = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lib)
        assert '"-P"' in inspect.getsource(dr._dash_launch_app)
        floor = lib.version_tuple(_setup_ado_floor()[0])
        assert floor >= (3, 11), floor
        assert lib.safe_flags(floor) == ["-P"]


class TestTheFloorInterpretersBehaveAlike:
    """WP-30 P1.33, found by the floor matrix (the py311 and py312 legs):
    dash serve's child registers the app's handed-over source in linecache
    so a traceback shows the app's lines although the child never opens
    app.py.  Before 3.13 the default sys.excepthook is the C printer, which
    reads the line from disk and ignores linecache, so on 3.11 and 3.12 the
    traceback named the file and line but not the text.  Below 3.13 the
    bootstrap now prints uncaught exceptions with the traceback module (on
    3.13 a replaced hook would turn an uncaught KeyboardInterrupt's -SIGINT
    exit into 1, so 3.13 keeps its own).  The child is told it runs 3.12
    by replacing sys.version_info before the bootstrap starts."""

    def test_the_child_prints_tracebacks_from_the_handed_over_source(
            self, tmp_path):
        import subprocess
        src = ("import sys, traceback\n"
               "print(sys.excepthook is traceback.print_exception,"
               " flush=True)\n"
               "def f():\n"
               "    raise ValueError('boom in the floor app')\n"
               "f()\n")
        app = os.path.join(str(tmp_path), "never", "app.py")
        frame = dr._dash_app_frame(src.encode("utf-8"))
        older = "import sys; sys.version_info = (3, 12, 12, 'final', 0)\n"
        r = subprocess.run([sys.executable, "-P", "-c",
                            older + dr._DASH_BOOT, app],
                           input=frame, capture_output=True, timeout=60,
                           cwd=str(tmp_path))
        assert r.stdout.decode().split() == ["True"], r.stderr
        err = r.stderr.decode()
        assert r.returncode == 1
        assert 'File "%s", line 4, in f' % app in err, err
        assert "raise ValueError('boom in the floor app')" in err, err


# ----------------------------------------------------------------------
# WP-30 P1.35: the Stata floor.  Every program said `version 16.0', which
# implied a Stata 16 support never stated, tested or enforced; only StataNow
# 19.5 was ever run.  The floor is now 19: declared by every program's
# `version' line, named once in dash_setup.ado (`_dash_statamin') and once
# in dash.ado (`_dash_require_stata', since a program of one ado-file cannot
# be called from another), enforced as the first statement of `dash' and
# `dash_setup', and stated in dash.pkg, both help files and CHANGELOG.
# ----------------------------------------------------------------------

# The programs that must run on the Stata they refuse (version 13), and
# the constants that declare no `version' at all.  The set is closed: a
# later section that needs another exemption adds it here with its reason.
_GUARDS = {"_dash_require_stata", "_dash_stata_ok", "_dash_setup_stata"}
_CONSTANTS = {"_dash_statamin", "_dash_pymin"}
_ENTRIES = {"dash", "dash_setup"}
_ADOS = ("dash.ado", "dash_setup.ado")


def _bodies_of(text):
    """``{program: [logical code lines between its define and its end]}``;
    a program defined twice keeps its last definition."""
    lines = text.split("\n")
    out = {}
    for name, (first, last) in _ado_programs(text).items():
        out[name] = [code for _, code in
                     _logical_lines("\n".join(lines[first:last - 1]))]
    return out


def _bodies(rel):
    return _bodies_of(_read(rel))


def _statamin():
    found = re.findall(r'return local statamin "([^"]+)"',
                       _read("dash_setup.ado"))
    assert len(found) == 1, found
    return found[0]


def _all_bodies():
    out = {}
    for rel in _ADOS:
        out.update(_bodies(rel))
    return out


def _load_sv_generator():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "gen_string_varlists_cscript_floor",
        os.path.join(_ROOT, "scripts", "gen_string_varlists_cscript.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestTheStataFloor:
    def test_dash_setup_names_the_stata_floor_once(self):
        bodies = _bodies("dash_setup.ado")
        assert "_dash_statamin" in bodies, "no _dash_statamin in dash_setup.ado"
        assert bodies["_dash_statamin"] == ['return local statamin "19"'], (
            bodies["_dash_statamin"])
        assert _statamin() == "19"

    def test_dash_ado_holds_the_same_floor(self):
        bodies = _bodies("dash.ado")
        assert "_dash_require_stata" in bodies, (
            "no _dash_require_stata in dash.ado")
        want = "local floor %s" % _statamin()
        assert want in bodies["_dash_require_stata"], (
            want, bodies["_dash_require_stata"])

    @pytest.mark.parametrize("rel", _ADOS)
    def test_every_program_declares_version_19(self, rel):
        bad = [(name, body[0] if body else None)
               for name, body in sorted(_bodies(rel).items())
               if name not in _GUARDS | _CONSTANTS | _ENTRIES
               and (not body or body[0] != "version 19")]
        assert not bad, "%s: %d programs do not open with version 19: %r" % (
            rel, len(bad), bad)

    def test_no_version_16_line_remains(self):
        for rel in _ADOS + ("scripts/wire_option_reporting.py",
                            "scripts/gen_string_varlists_cscript.py"):
            m = re.search(r"version\s+16\.0", _read(rel))
            assert m is None, (rel, _read(rel)[:m.start()].count("\n") + 1)

    def test_the_guard_is_the_first_statement_of_dash_and_dash_setup(self):
        dash = _bodies("dash.ado")["dash"]
        assert dash[:2] == ["_dash_require_stata", "version 19"], dash[:3]
        assert dash.index("_dash_require_mata") > 1, dash[:4]
        setup = _bodies("dash_setup.ado")["dash_setup"]
        assert setup[:2] == ["_dash_setup_stata", "version 19"], setup[:3]
        first_syntax = next(i for i, ln in enumerate(setup)
                            if ln.startswith("syntax"))
        assert first_syntax > 1, setup[:4]

    def test_the_guards_declare_no_version_above_13(self):
        bodies = _all_bodies()
        for name in sorted(_GUARDS):
            assert name in bodies, "no program %s" % name
            body = bodies[name]
            m = re.fullmatch(r"version (\d+(?:\.\d+)?)", body[0] if body else "")
            assert m and float(m.group(1)) <= 13, (name, body[:1])
            others = [ln for ln in body[1:] if re.match(r"version\b", ln)]
            assert not others, (name, others)
        for name in sorted(_CONSTANTS):
            assert name in bodies, "no program %s" % name
            assert not [ln for ln in bodies[name]
                        if re.match(r"version\b", ln)], (name, bodies[name])

    def test_the_guards_need_nothing_newer_than_stata_13(self):
        bodies = _all_bodies()
        newer = re.compile(r"\bstrtrim\(|\bustr\w*\(|\bregexm\(|\bpython\b|"
                           r"_dash_say|\bversion\s+(1[4-9]|[2-9]\d)")
        for name in sorted(_GUARDS):
            assert name in bodies, "no program %s" % name
            body = bodies[name]
            hits = [ln for ln in body if newer.search(ln)]
            assert not hits, (name, hits)
            calls = {m.group(0) for m in
                     (re.match(r"_dash_\w+", ln) for ln in body) if m}
            assert calls <= {"_dash_stata_ok", "_dash_statamin"}, (name, calls)

    def test_the_refusal_is_r9_in_dashs_words(self):
        bodies = _all_bodies()
        said = ('display as error "dash requires Stata `floor\' or later; '
                'this is Stata ')
        for name in ("_dash_require_stata", "_dash_setup_stata"):
            assert name in bodies, "no program %s" % name
            body = bodies[name]
            assert any(ln.startswith(said) for ln in body), (name, body)
            assert "exit 9" in body, (name, body)

    def test_every_stata_declaration_agrees(self):
        n = _statamin()
        tested = "Stata %s or later; tested on StataNow 19.5 (MP), macOS arm64" % n
        pkg = _read("dash.pkg").split("\n")
        assert "d Requires: %s." % tested in pkg, pkg
        assert any("Measured on MP only" in ln for ln in pkg), pkg
        help_ = _read("dash.sthlp")
        deps = _flat(help_[help_.index("{marker dependencies}"):
                           help_.index("{marker author}")])
        assert tested in deps, deps
        assert "Measured on MP only" in deps, deps
        shelp = _flat(_read("dash_setup.sthlp"))
        assert tested in shelp, shelp
        assert "Measured on MP only" in shelp, shelp
        changelog = _flat(_read("CHANGELOG.md"))
        rq_start = changelog.index("### Requirements")
        rq_end = changelog.index("### ", rq_start + 10)
        assert ("Stata %s or later" % n) in changelog[rq_start:rq_end]
        for rel in _ADOS:
            bad = [(name, body[:1]) for name, body in
                   sorted(_bodies(rel).items())
                   if name not in _GUARDS | _CONSTANTS | _ENTRIES
                   and body[:1] != ["version %s" % n]]
            assert not bad, (rel, bad)
        for name in _ENTRIES:
            assert ("version %s" % n) == _all_bodies()[name][1], name

    def test_dash_setup_reports_the_stata_line(self):
        text = _read("dash_setup.ado")
        line = ('display as text "  Stata .............. {res}OK{txt} '
                '(version `c(stata_version)\')"')
        hline = text.index('display as text "{hline 60}"')
        python = text.index('python: import sys; from sfi import Macro; '
                            'Macro.setLocal("pyver"')
        assert line in text, "dash_setup reports no Stata line"
        assert hline < text.index(line) < python

    def test_the_generators_emit_version_19(self):
        wire = _read("scripts/wire_option_reporting.py")
        assert "program define _dash_report_ignored\n    version 19\n" in wire
        mod = _load_sv_generator()
        assert "    version 19" in mod._sv_case_program().split("\n")
        assert "version 16.0" not in mod.render()

    def test_the_restated_comparators_match_the_shipped_ones(self):
        restated = _bodies("test/test_env_guards.cscript")
        shipped = _bodies("dash.ado")
        for name in ("_dash_stata_ok", "_dash_python_ok"):
            assert name in shipped, "no %s in dash.ado" % name
            assert name in restated, "no restated %s" % name
            assert restated[name] == shipped[name], (
                name, restated[name], shipped[name])


class TestTheGeneratedAppEvaluatesNoAnnotationAtImport:
    def _built(self, tmp_path):
        import pandas as pd
        df = pd.DataFrame({"mpg": [22.0], "weight": [2930.0]})
        spec = {
            "graphs": [{"name": "g1", "graph_options": {"name": "g1"},
                       "plots": [{"type": "scatter", "yvar": "mpg",
                                  "xvar": "weight", "options": {}}],
                       "options": {}}],
            "kpis": [],
            "build_options": {"layout": "auto", "registry": "g1",
                              "level": "95", "formats": {}},
        }
        sp = tmp_path / "spec.json"
        dp = tmp_path / "data.json"
        sp.write_text(json.dumps(spec))
        dp.write_text(json.dumps(make_data_json(df)))
        out = tmp_path / "app.py"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(str(sp), str(dp)).build(str(out))
        return out.read_text()

    def test_the_future_import_is_the_first_statement(self, tmp_path):
        src = self._built(tmp_path)
        tree = ast.parse(src)
        assert isinstance(tree.body[0], ast.Expr)  # the module docstring
        assert isinstance(tree.body[1], ast.ImportFrom), ast.dump(
            tree.body[1])
        assert tree.body[1].module == "__future__"
        assert any(a.name == "annotations" for a in tree.body[1].names)

    def test_pep585_and_pep604_annotations_are_deferred(self, tmp_path):
        src = self._built(tmp_path)
        tree = ast.parse(src)
        future_ok = (isinstance(tree.body[1], ast.ImportFrom)
                    and tree.body[1].module == "__future__"
                    and any(a.name == "annotations"
                           for a in tree.body[1].names))

        def _is_deferred_shape(node):
            if isinstance(node, ast.BinOp) and isinstance(node.op,
                                                           ast.BitOr):
                return True
            if isinstance(node, ast.Subscript):
                base = node.value
                name = getattr(base, "id", None)
                if name in ("list", "dict", "tuple", "set", "frozenset",
                           "type"):
                    return True
            return False

        found = []
        seen = 0
        for node in ast.walk(tree):
            annots = []
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                annots.append(node.returns)
                for a in (list(node.args.args)
                         + list(node.args.posonlyargs)
                         + list(node.args.kwonlyargs)):
                    annots.append(a.annotation)
            elif isinstance(node, ast.AnnAssign):
                annots.append(node.annotation)
            for a in annots:
                if a is None:
                    continue
                seen += 1
                if _is_deferred_shape(a):
                    found.append(a)
        assert seen > 20, seen  # the walker actually saw annotations
        assert found == [] or future_ok
