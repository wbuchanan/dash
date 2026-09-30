"""test_packaging.py — regression tests for the ``net install`` packaging blocker.

Background
----------
``dash.pkg`` is the manifest Stata's ``net install`` reads.  Everything a user
ends up with after installing is exactly what that manifest declares — nothing
else from the development tree comes along.  ``dash.pkg`` currently declares six
files and omits ``schemes/``, while
``SchemeParser._SCHEMES_DIR`` resolves to ``<dir of dash_render.py>/schemes``.
After an install that directory does not exist, so every scheme lookup fails,
and ``DashRenderer.__init__``'s recovery path calls ``SchemeParser("s2color")``
*outside* the ``try``, where the identical failure is uncaught.
``GlyphMapper.__init__`` has the same defect.

No pre-existing test can catch this because the whole suite runs from the repo,
where ``schemes/`` happens to sit next to ``dash_render.py``.

These tests therefore never import the repo's ``dash_render``.  They stage the
declared files into a fresh temp directory, load ``dash_render.py`` *from that
directory* by path, and exercise it there — which is what a user gets.

Layouts
-------
Stata's ``f`` directive installs a file under its basename, so a manifest entry
such as ``f schemes/s2color.scheme`` may well land as ``s2color.scheme`` in the
install root rather than in a ``schemes/`` subdirectory.  Rather than assume
either behaviour, the staging fixture is parametrised over both layouts
(``flat`` and ``as-declared``); the package must survive either one.  Task 02-02
settles the question empirically with a real local ``net install``.
"""
from __future__ import annotations

import importlib.util
import itertools
import json
import os
import re
import shutil
import sys

import pytest

# --------------------------------------------------------------------------
# Repo layout
# --------------------------------------------------------------------------

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG_FILE = os.path.join(REPO_ROOT, "dash.pkg")

#: Sources that are shipped and therefore may reference other shipped files.
SHIPPED_SOURCES = ("dash.ado", "dash_setup.ado", "dash_render.py")

#: Directories that hold development-only material, never installed content.
EXCLUDED_DIRS = frozenset({
    ".git", ".claude", ".ultraplan", ".pytest_cache", ".ruff_cache",
    "__pycache__", "test", "examples", "scripts",
})

#: Extensions a runtime file reference can plausibly carry.
_REF_EXTENSIONS = ("ado", "mata", "py", "sthlp", "scheme")

_LOAD_COUNTER = itertools.count()


# --------------------------------------------------------------------------
# Manifest parsing / staging helpers
# --------------------------------------------------------------------------

def parse_pkg_files(pkg_path: str = PKG_FILE) -> list[str]:
    """Return the file paths declared for installation by a ``.pkg`` manifest.

    Handles the ``f``/``F`` directives (``f filename``) and the platform-
    specific ``g``/``G`` directive (``g platform filename``).  Description
    lines (``d``) and everything else are ignored.
    """
    declared: list[str] = []
    with open(pkg_path, encoding="utf-8") as fh:
        for raw in fh:
            parts = raw.strip().split()
            if len(parts) < 2:
                continue
            directive = parts[0]
            if directive in ("f", "F"):
                declared.append(parts[1])
            elif directive in ("g", "G") and len(parts) >= 3:
                declared.append(parts[2])
    return declared


def stage_package(dest: str, layout: str = "flat") -> list[str]:
    """Copy exactly the files ``dash.pkg`` declares into *dest*.

    This is a pure-``shutil`` model of ``net install`` — no network, no Stata,
    and deliberately nothing that the manifest does not name.

    Args:
        dest:   Directory to install into (must already exist).
        layout: ``"flat"`` installs each file under its basename (Stata's
                documented ``f`` behaviour); ``"as-declared"`` preserves any
                directory component written in the manifest.

    Returns:
        The list of staged absolute paths.
    """
    declared = parse_pkg_files()
    assert declared, f"{PKG_FILE} declares no installable files"

    staged: list[str] = []
    for rel in declared:
        src = os.path.join(REPO_ROOT, rel)
        assert os.path.isfile(src), (
            f"dash.pkg declares {rel!r} but {src} does not exist in the repo; "
            "net install would fail outright."
        )
        if layout == "flat":
            target = os.path.join(dest, os.path.basename(rel))
        else:
            target = os.path.join(dest, rel)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy2(src, target)
        staged.append(target)
    return staged


def load_staged_render(install_dir: str):
    """Import ``dash_render.py`` from *install_dir* by path, not from the repo.

    A fresh module name per call keeps each staged copy independent of both the
    repo's ``dash_render`` and of other staged copies, so ``_SCHEMES_DIR`` is
    recomputed from the staged file's own location.
    """
    path = os.path.join(install_dir, "dash_render.py")
    assert os.path.isfile(path), (
        f"dash_render.py was not staged into {install_dir}; "
        "check the f-lines in dash.pkg."
    )
    name = f"dash_render_staged_{next(_LOAD_COUNTER)}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return name, module


def write_minimal_inputs(directory: str) -> tuple[str, str]:
    """Write a minimal master-spec / data JSON pair and return their paths."""
    spec = {
        "build_options": {
            "theme": "default", "layout": "auto", "title": "T",
            "subtitle": "", "link": "", "filter": "", "filter_position": "top",
        },
        "graphs": [{
            "name": "g1",
            "plots": [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}],
            "graph_options": {},
        }],
        "kpis": [],
    }
    data = {
        "values": [{"x": 1.0, "y": 2.0}, {"x": 2.0, "y": 3.0}, {"x": 3.0, "y": 5.0}],
        "variableLabels": {},
        "valueLabels": {},
        "valueLabelNames": {},
        "variableTypeIsString": {"x": False, "y": False},
    }
    spec_path = os.path.join(directory, "spec.json")
    data_path = os.path.join(directory, "data.json")
    with open(spec_path, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    with open(data_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    return spec_path, data_path


# --------------------------------------------------------------------------
# Fixture
# --------------------------------------------------------------------------

@pytest.fixture(params=["flat", "as-declared"])
def staged_install(request, tmp_path, monkeypatch):
    """A clean install directory holding only what ``dash.pkg`` declares.

    Yields ``(module, install_dir)`` where *module* is ``dash_render`` loaded
    from that directory.  The working directory is moved to the install root
    for the duration, so the repo's own ``schemes/`` can never leak in via a
    relative lookup — a user running ``dash`` is not standing in this repo.
    """
    install_dir = tmp_path / "install"
    install_dir.mkdir()
    stage_package(str(install_dir), layout=request.param)
    monkeypatch.chdir(install_dir)

    name, module = load_staged_render(str(install_dir))
    try:
        yield module, str(install_dir)
    finally:
        sys.modules.pop(name, None)


# --------------------------------------------------------------------------
# Test 1 — the packaged install must produce a usable DashRenderer
# --------------------------------------------------------------------------

def test_dashrenderer_constructs_from_packaged_install(staged_install, tmp_path):
    """Constructing DashRenderer from a manifest-only install must not raise.

    Today this raises ``ValueError: dash: scheme 's2color' not found ...`` —
    the scheme lookup fails because ``schemes/`` was never shipped, and the
    fallback in ``DashRenderer.__init__`` re-runs the same failing lookup
    outside the ``try``.  Every ``dash`` command would end this way for every
    user who installed the package.

    The constructor is called without a ``pytest.raises`` guard on purpose: the
    failure this test reports should be the real exception and traceback.
    """
    module, _install_dir = staged_install
    spec_path, data_path = write_minimal_inputs(str(tmp_path))
    out_path = os.path.join(str(tmp_path), "out.html")

    renderer = module.DashRenderer(spec_path, data_path, out_path)

    # A renderer with an unusable scheme is no better than one that raised.
    assert renderer.scheme is not None, "DashRenderer produced no scheme object"
    color = renderer.scheme.default_color(0, "scatter")
    assert isinstance(color, str) and color.startswith("#"), (
        f"scheme returned an unusable default color: {color!r}"
    )


# --------------------------------------------------------------------------
# Test 2 — same defect, same fix, in GlyphMapper
# --------------------------------------------------------------------------

def test_glyphmapper_constructs_from_packaged_install(staged_install):
    """GlyphMapper's default-scheme construction must not raise either.

    ``GlyphMapper.__init__`` calls ``SchemeParser("s2color")`` directly when no
    scheme is passed, with no guard at all, so it fails the same way under a
    missing ``schemes/`` directory.
    """
    module, _install_dir = staged_install

    mapper = module.GlyphMapper()

    assert mapper.scheme is not None, "GlyphMapper produced no scheme object"
    color = mapper.scheme.default_color(0, "scatter")
    assert isinstance(color, str) and color.startswith("#"), (
        f"scheme returned an unusable default color: {color!r}"
    )


# --------------------------------------------------------------------------
# Test 3 — manifest completeness (catches the *next* omission)
# --------------------------------------------------------------------------

def _repo_file_index() -> dict[str, str]:
    """Map basename → repo-relative path for every candidate shippable file."""
    index: dict[str, str] = {}
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for filename in filenames:
            if filename.startswith("."):
                continue
            rel = os.path.relpath(os.path.join(dirpath, filename), REPO_ROOT)
            index.setdefault(filename, rel.replace(os.sep, "/"))
    return index


def _referenced_repo_files() -> set[str]:
    """Repo files named literally inside the shipped sources.

    A reference only counts when a file of that name actually exists in the
    repo, which keeps generated names and prose out of the required set.
    """
    import re

    pattern = re.compile(
        r"[A-Za-z0-9_][A-Za-z0-9_.\-/]*\.(?:" + "|".join(_REF_EXTENSIONS) + r")"
    )
    index = _repo_file_index()
    found: set[str] = set()
    for source in SHIPPED_SOURCES:
        source_path = os.path.join(REPO_ROOT, source)
        # A source that is not there was skipped in silence, and every file
        # only it names dropped out of the required set with it.
        if not os.path.isfile(source_path):
            pytest.fail(f"shipped source {source} is missing, so the files "
                        f"it names are no longer required; update "
                        f"SHIPPED_SOURCES")
        with open(source_path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        for match in pattern.finditer(text):
            basename = os.path.basename(match.group(0))
            if basename in index:
                found.add(index[basename])
    return found


#: The package's own files, required whatever the sources' text says: the
#: two commands, their help files (``help dash``, ``help dash_setup``), the
#: Mata source dash.ado compiles and the renderer it runs.  The help files
#: were required only because comments name them -- measured 24sep2026,
#: every mention of dash.sthlp and dash_setup.sthlp in the shipped sources
#: is a comment -- so a manifest that dropped one would pass the day those
#: comments were reworded.
_PACKAGE_FILES = ("dash.ado", "dash_setup.ado", "dash.sthlp",
                  "dash_setup.sthlp", "dash_parse.mata", "dash_render.py")


def _findfile_targets() -> set[str]:
    """The files the shipped ado sources locate with ``findfile`` at run
    time, read from their code (comments dropped)."""
    import re

    out: set[str] = set()
    for source in SHIPPED_SOURCES:
        if not source.endswith(".ado"):
            continue
        with open(os.path.join(REPO_ROOT, source), encoding="utf-8") as fh:
            for line in fh:
                if line.lstrip().startswith("*"):
                    continue
                out.update(re.findall(r"\bfindfile\s+([A-Za-z0-9_][\w.\-]*)",
                                      line.split("//", 1)[0]))
    return out


def _shipped_scheme_files() -> "list[str]":
    """Every ``dash-<name>.scheme`` scheme file in the package root."""
    return sorted(f for f in os.listdir(REPO_ROOT)
                  if f.startswith("dash-") and f.endswith(".scheme")
                  and os.path.isfile(os.path.join(REPO_ROOT, f)))


def test_the_repo_has_no_schemes_directory():
    """WP-28: the shipped schemes live in the package root, not schemes/."""
    assert not os.path.exists(os.path.join(REPO_ROOT, "schemes"))


def test_the_root_holds_exactly_the_twenty_dash_files_the_manifest_ships():
    """WP-28: ``f dash-<name>.scheme`` for each of the twenty, and no other
    ``dash-*.scheme`` in the root."""
    declared = sorted(d for d in parse_pkg_files()
                      if re.fullmatch(r"dash-[a-z0-9_]+\.scheme", d))
    assert len(declared) == 20, declared
    assert _shipped_scheme_files() == declared
    assert not [d for d in parse_pkg_files()
                if d.endswith(".scheme") and d not in declared]


def _required_runtime_files() -> set[str]:
    """Every repo file the installed package needs at run time.

    Scheme files are collected as every ``dash-*.scheme`` in the package root
    rather than by listing names, so a scheme added later becomes a
    manifest requirement automatically, with no edit to this test.
    """
    required: set[str] = set()

    # The package's own files and what its code findfile()s, named here and
    # not left to the text scan -- which is guarded by them: it must see
    # every file the code locates, or it has gone blind (a pattern that no
    # longer matches found nothing, and nothing here said so).
    referenced = _referenced_repo_files()  # fails first on a lost source
    targets = _findfile_targets()
    assert targets, "the shipped ado files findfile nothing any more"
    for name in _PACKAGE_FILES + tuple(sorted(targets)):
        assert os.path.isfile(os.path.join(REPO_ROOT, name)), name
        required.add(name)
    seen = {os.path.basename(r) for r in referenced}
    unseen = sorted(targets - seen)
    assert not unseen, (
        f"the reference scan does not see {unseen}, which the code "
        f"locates at run time")

    scheme_files = set(_shipped_scheme_files())

    # Guard the guard: if the files ever vanish, this test must not go quiet.
    assert scheme_files, (
        f"no dash-*.scheme scheme files found in {REPO_ROOT}; "
        "the manifest-completeness test would silently stop checking them."
    )

    required |= scheme_files
    required |= referenced
    return required


def test_pkg_manifest_lists_every_runtime_file():
    """``dash.pkg`` must declare every file the installed package reads.

    Matching is by declared path *or* basename, so the test is agnostic to
    whether task 02-02 ends up writing ``f schemes/s2color.scheme`` or
    ``f s2color.scheme``.
    """
    declared = parse_pkg_files()
    declared_keys = {d.replace(os.sep, "/") for d in declared}
    declared_keys |= {os.path.basename(d) for d in declared}

    # A manifest entry with no file behind it breaks the install just as badly.
    for rel in declared:
        assert os.path.isfile(os.path.join(REPO_ROOT, rel)), (
            f"dash.pkg declares {rel!r}, which does not exist in the repo"
        )

    missing = sorted(
        rel for rel in _required_runtime_files()
        if rel not in declared_keys and os.path.basename(rel) not in declared_keys
    )

    assert not missing, (
        "dash.pkg omits files the package needs at run time, so net install "
        "produces a broken package. Missing:\n  " + "\n  ".join(missing)
    )


#: What the package root may hold besides the files dash.pkg ships: the
#: manifests, the repository's documents and its build configuration.
#: Development scripts go in scripts/ and examples in examples/: three
#: regen_*.py scripts sat in the root beside the shipped sources until WP-26
#: (TR-26.9, 24sep2026) moved them to scripts/.
_ROOT_ALSO = frozenset({
    "dash.pkg", "stata.toc", ".gitignore", "Makefile", "pyproject.toml",
    "AGENTS.md", "BUGS.md", "CHANGELOG.md", "CLAUDE.md", "GAPS.md",
    "GAPS2.md", "REMAINING.md", "ROADMAP.md",
})


def test_the_package_root_holds_only_what_ships_and_the_repositorys_own():
    """Every file git tracks in the package root is one dash.pkg ships, or
    one of the manifests, documents and configuration named above."""
    import subprocess

    p = subprocess.run(["git", "-C", REPO_ROOT, "ls-files"],
                       capture_output=True, text=True)
    if p.returncode != 0:
        pytest.skip("not a git working tree")
    shipped = {d for d in parse_pkg_files() if "/" not in d}
    assert "dash.ado" in shipped and "dash_render.py" in shipped
    root = sorted(f for f in p.stdout.splitlines()
                  if "/" not in f and os.path.exists(os.path.join(REPO_ROOT, f)))
    stray = [f for f in root if f not in shipped and f not in _ROOT_ALSO]
    assert not stray, (
        "the package root holds files that neither ship nor belong to the "
        "repository's documents or configuration; move them to scripts/ or "
        "examples/: " + ", ".join(stray))


class TestNoUnsuppressableBrowserWindow:
    """``dash build`` opened a browser window and there was no way to stop it.

    Every ``shell open`` / ``start`` / ``xdg-open`` in ``dash.ado`` fired
    unconditionally, so a do-file run in batch — or a certification run that
    builds twenty dashboards — opened one window per build, in rapid
    succession, on whatever machine was running it.

    ``nobrowser`` is the user-facing option and ``$dash_nobrowser`` is the
    session-wide switch the test runner sets once. This asserts mechanically
    that no launcher call is left outside a guard, which is the part that
    would silently come back.
    """

    #: A Stata command that hands a line to the operating system: shell,
    #: its synonyms and `!', after any prefix; or Mata's stata()/_stata()
    #: given one.  Read from code lines only.
    _SHELL = re.compile(
        r"^\s*(?:(?:capture|cap|quietly|qui|noisily|noi)\s+)*"
        r"(?:(?:shell|xshell|winexec|unix)\b|!)"
        r"|\b_?stata\(\s*\"(?:shell|xshell|winexec|unix)\b")
    #: The programs that decide whether a window opens: the one-line form's
    #: and the one `dash build' and `dash serve' share.  Each must read the
    #: switches (test_each_decision_reads_the_switches).
    _DECIDERS = ("_dash_browser_wanted", "_dash_dashboard_browser")

    @staticmethod
    def _ado_lines():
        path = os.path.join(REPO_ROOT, "dash.ado")
        with open(path, encoding="utf-8") as fh:
            return fh.read().splitlines()

    @staticmethod
    def _code(line):
        """A line's code: nothing of a comment line, and a trailing //
        comment cut."""
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("*"):
            return ""
        return line.split(" //", 1)[0]

    def test_every_launcher_call_sits_inside_a_guard(self):
        """One program hands a page to the shell, only when asked to, and
        each of its callers decides first.

        A structural guard over dash.ado's text, deliberately: the opener
        runs a platform's command (`open', `xdg-open', `start'), and a
        certification run cannot open windows to show that it would not.
        The behaviour is held by the opener's own cases --
        test_serve_browser.cscript SB-18 (dryrun runs nothing) and SB-20
        ($dash_nobrowser runs nothing) -- and test_help_claims_2.cscript
        HC2-31..36.  This counted six shell lines, the three platforms'
        openers on each of the two paths, until both paths went through
        _dash_open_page (WP-24); a shell line anywhere else, an opener
        reached without its switches read, or a caller that no decision
        guards now fails it.
        """
        lines = self._ado_lines()
        shells, calls, prog = [], [], None
        # Logical lines: a line ending in /// continues on the next, and a
        # `!' there is an expression's not, not a command (measured: the
        # layout check's `!regexm(' continuations).
        logical, cur, first = [], "", None
        for i, line in enumerate(lines):
            if first is None:
                first = i
            raw = line.rstrip()
            if raw.endswith("///"):
                cur += self._code(raw[:-3]) + " "
                continue
            logical.append((first, cur + self._code(line)))
            cur, first = "", None
        for i, code in logical:
            m = re.match(r"program define (\w+)", lines[i])
            if m:
                prog = m.group(1)
            if self._SHELL.search(code):
                shells.append((prog, i))
            if re.match(r"^\s*_dash_open_page\b", code):
                calls.append(i)
        # Exactly one line hands anything to the operating system, in the
        # opener.
        assert [p for p, _ in shells] == ["_dash_open_page"], (
            "dash.ado hands a line to the shell outside _dash_open_page: "
            + ", ".join(f"{p} (line {i + 1})" for p, i in shells))
        # ...and it runs only when neither dryrun nor $dash_nobrowser says
        # not to: the `if' it sits in reads both.
        (_, at), = shells
        guard = next(self._code(lines[j]) for j in range(at - 1, at - 6, -1)
                     if self._code(lines[j]).strip().startswith("if "))
        assert "dryrun" in guard and "${dash_nobrowser}" in guard, guard
        # Two callers -- the one-line form and dash build -- each just after
        # the decision that guards it.
        assert len(calls) == 2, [c + 1 for c in calls]
        unguarded = []
        for i in calls:
            window = "\n".join(self._code(l) for l in lines[max(0, i - 12):i])
            if not any(d in window for d in self._DECIDERS):
                unguarded.append(f"dash.ado:{i + 1}: {lines[i].strip()}")
        assert not unguarded, (
            "a browser launcher runs with nothing able to suppress it:\n"
            + "\n".join(unguarded)
        )

    def _program_body(self, name):
        lines = self._ado_lines()
        start = next(i for i, l in enumerate(lines)
                     if l.startswith(f"program define {name}"))
        end = next(i for i in range(start + 1, len(lines))
                   if lines[i].strip() == "end")
        return "\n".join(l.split("//", 1)[0] for l in lines[start:end])

    def test_each_decision_reads_the_switches(self):
        """Both decisions read $dash_nobrowser and nodraw; the shared one
        reads the command's nobrowser option as well."""
        for name in self._DECIDERS:
            body = self._program_body(name)
            assert "${dash_nobrowser}" in body, (
                f"{name} does not read $dash_nobrowser")
            assert ('"nodraw":"nodraw"' in body
                    or "_dash_registry_nodraw" in body), (
                f"{name} does not read nodraw")
        assert "`nobrowser'" in self._program_body("_dash_dashboard_browser")

    def _declared_options(self, name):
        """Every option token program *name*'s first ``syntax [, ///``
        block declares, as written (``TABS(string asis)`` is ``TABS``).
        Read from the raw lines: _program_body drops ``//`` comments, and
        with them the ``///`` continuations the block is made of."""
        import re

        lines = self._ado_lines()
        start = next(i for i, l in enumerate(lines)
                     if re.match(r"program define %s\s*(,|$)"
                                 % re.escape(name), l))
        end = next(i for i in range(start + 1, len(lines))
                   if lines[i].strip() == "end")
        body = "\n".join(lines[start:end])
        m = re.search(r"^\s*syntax \[, ///\n(.*?)^\s*\]\s*$", body,
                      re.MULTILINE | re.DOTALL)
        assert m, f"no multi-line syntax block in {name}"
        found = []
        for line in m.group(1).splitlines():
            code = line.replace("///", " ")
            code = re.sub(r"\([^)]*\)", " ", code)
            found += re.findall(r"[A-Za-z_][A-Za-z0-9_]*", code)
        return found

    def test_the_build_command_accepts_nobrowser(self):
        """``dash build`` declares ``nobrowser`` and hands it to the
        decision that opens the window.

        A structural guard over dash.ado, deliberately: whether Stata's
        ``syntax`` takes the option needs Stata, and the certification
        scripts run it -- test_serve_options.cscript [7/7] asserts rc 0 for
        ``dash build, ... nobrowser``, as do the 22 scripts whose builds
        pass it, and test_serve_browser.cscript SB-02 shows the decision
        keeps the window shut for it.  This looked for ``NOBRowser``
        anywhere in dash.ado, where _dash_dashboard_browser,
        _dash_prepare_spec and _dash_serve_spec declare it too: with the
        option deleted from _dash_build's own syntax, and with _dash_build
        no longer passing it on, it passed (measured 24sep2026).  Now it
        reads _dash_build's own syntax block and its own call."""
        import re

        declared = self._declared_options("_dash_build")
        # The reader sees the options around it (a pattern that stopped
        # matching would find nothing and pass the check below it).
        assert "SAVing" in declared and "REPLACE" in declared, declared
        assert declared.count("NOBRowser") == 1, (
            f"dash build has no nobrowser option, so a batch do-file cannot "
            f"stop it opening a window: {declared}")
        code = "\n".join(l for l in self._program_body("_dash_build")
                         .splitlines() if not l.lstrip().startswith("*"))
        assert re.search(r"^\s*_dash_dashboard_browser, `nobrowser'\s*$",
                         code, re.MULTILINE), (
            "dash build no longer hands its nobrowser option to the "
            "decision that opens the window")

    def test_the_global_switch_is_honoured_on_both_paths(self):
        path = os.path.join(REPO_ROOT, "dash.ado")
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        assert src.count("${dash_nobrowser}") >= 2, (
            "the session-wide switch reaches only one of the two paths that "
            "open a browser"
        )

    def test_nodraw_suppresses_the_window(self):
        """Stata's own nodraw means build it but do not display it."""
        path = os.path.join(REPO_ROOT, "dash.ado")
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        assert '"nodraw":"nodraw"' in src, (
            "nodraw is parsed and does not stop the browser opening"
        )
