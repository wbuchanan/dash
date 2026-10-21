"""Strict mode: what `make check' runs pytest in (WP-25, TR-25.2).

Under DASH_STRICT=1 conftest.py stops a run whose interpreter or libraries
differ from their baseline before any test runs, and turns a run with any
skip red at its end -- a skip is not a pass.  Without it both stay what they
were: a warning, and a skip.  The helpers are tested directly, and the hooks
by running a throwaway suite, with a copy of conftest.py, in a subprocess of
this interpreter, serially and under xdist.
"""
import ast
import os
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import conftest as C  # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# The helpers
# ---------------------------------------------------------------------------

class TestTheBaselines:

    def test_each_interpreter_has_one(self):
        assert set(C._BASELINES) == {"stata", "dev", "py311", "py311-dev",
                                     "py312", "py312-dev"}
        for env in C._BASELINES.values():
            assert set(env) == {"python", "bokeh", "pandas", "numpy", "scipy"}

    def test_the_running_environment_is_read_as_major_minor(self):
        actual = C._running_env()
        assert actual["python"] == "%d.%d" % sys.version_info[:2]
        for pkg in ("bokeh", "pandas", "numpy", "scipy"):
            assert actual[pkg].count(".") == 1, (pkg, actual[pkg])

    def test_the_baseline_is_the_one_named_or_the_one_whose_python_runs(self):
        assert C._baseline_name({"python": "3.13"}) == "stata"
        assert C._baseline_name({"python": "3.14"}) == "dev"
        assert C._baseline_name({"python": "3.9"}) == "dev"
        assert C._baseline_name({"python": "3.14"}, "stata") == "stata"
        # WP-30 P1.33: the floor matrix's stacks, the full match first.
        assert C._baseline_name({"python": "3.11"}) == "py311"
        assert C._baseline_name({"python": "3.12"}) == "py312"
        assert C._baseline_name(dict(C._BASELINES["py311-dev"])) == "py311-dev"
        assert C._baseline_name(dict(C._BASELINES["py312"])) == "py312"

    def test_each_older_python_runs_both_pin_sets(self):
        """WP-30 P1.33: every Python of the floor matrix carries the stata
        pins (py3NN) and the dev pins (py3NN-dev), and is older than the
        stata baseline's."""
        def pins(env):
            return {k: v for k, v in env.items() if k != "python"}

        def vt(v):
            return tuple(int(x) for x in v.split("."))

        older = [k for k in C._BASELINES
                 if k.startswith("py3") and not k.endswith("-dev")]
        assert older, "no py3NN baseline"
        for name in older:
            dev = C._BASELINES[name + "-dev"]
            assert pins(C._BASELINES[name]) == pins(C._BASELINES["stata"])
            assert pins(dev) == pins(C._BASELINES["dev"])
            assert dev["python"] == C._BASELINES[name]["python"]
            assert vt(C._BASELINES[name]["python"]) < vt(
                C._BASELINES["stata"]["python"])

    def test_a_drift_names_each_pin_missed(self):
        base = {"python": "3.13", "bokeh": "3.8"}
        assert C._env_drift({"python": "3.13", "bokeh": "3.8"}, base) == {}
        assert C._env_drift({"python": "3.13", "bokeh": "3.9"}, base) == {
            "bokeh": ("3.8", "3.9")}
        assert C._env_drift({"python": "3.13"}, base) == {
            "bokeh": ("3.8", "missing")}

    def test_the_problem_is_empty_for_a_match_and_names_a_drift(self):
        stata = dict(C._BASELINES["stata"])
        assert C._drift_problem(stata) == ""
        drifted = dict(stata, pandas="3.0")
        problem = C._drift_problem(drifted, "stata")
        assert "stata baseline" in problem
        assert "pandas: baseline 2.3, running 3.0" in problem

    def test_an_unknown_baseline_is_named(self):
        problem = C._drift_problem(C._running_env(), "nosuch")
        assert "DASH_BASELINE=nosuch names no baseline" in problem

    def test_strict_is_dash_strict_1(self, monkeypatch):
        monkeypatch.delenv("DASH_STRICT", raising=False)
        assert not C._strict()
        monkeypatch.setenv("DASH_STRICT", "0")
        assert not C._strict()
        monkeypatch.setenv("DASH_STRICT", "1")
        assert C._strict()


class _Report:
    def __init__(self, nodeid, skipped, longrepr=None, wasxfail=None):
        self.nodeid = nodeid
        self.skipped = skipped
        self.longrepr = longrepr
        if wasxfail is not None:
            self.wasxfail = wasxfail


class TestTheSkipRecord:

    def test_a_skip_is_recorded_with_its_reason(self, monkeypatch):
        monkeypatch.setattr(C, "_SKIPPED", [])
        C.pytest_runtest_logreport(_Report(
            "t.py::a", True, ("t.py", 3, "Skipped: no fixture")))
        assert C._SKIPPED == [("t.py::a", "Skipped: no fixture")]

    def test_a_pass_and_an_xfail_are_not(self, monkeypatch):
        monkeypatch.setattr(C, "_SKIPPED", [])
        C.pytest_runtest_logreport(_Report("t.py::b", False))
        C.pytest_runtest_logreport(_Report(
            "t.py::c", True, ("t.py", 4, "reason"), wasxfail="known"))
        assert C._SKIPPED == []

    def test_a_module_skipped_at_collection_is_recorded(self, monkeypatch):
        monkeypatch.setattr(C, "_SKIPPED", [])
        C.pytest_collectreport(_Report(
            "t.py", True, ("t.py", 1, "could not import 'fcntl'")))
        C.pytest_collectreport(_Report("u.py", False))
        assert C._SKIPPED == [("t.py", "could not import 'fcntl'")]

    def test_the_reason_of_a_report_that_is_not_a_triple(self):
        assert C._skip_reason(_Report("x", True, "plain text")) == "plain text"

    def test_the_verdict_is_empty_without_skips_and_lists_them(self):
        assert C._strict_verdict([]) == []
        lines = C._strict_verdict([("t.py::a", "why")])
        assert "1 test(s) skipped" in lines[0]
        assert lines[1] == "  t.py::a -- why"


# ---------------------------------------------------------------------------
# The hooks, on a throwaway suite
# ---------------------------------------------------------------------------

_PASSES = "def test_passes():\n    assert True\n"
_SKIPS = ("import pytest\n\n\ndef test_skips():\n"
          "    pytest.skip('a fixture this machine lacks')\n")


def _suite(tmp_path, *files):
    shutil.copy(os.path.join(_HERE, "conftest.py"), tmp_path / "conftest.py")
    for i, text in enumerate(files):
        (tmp_path / ("test_throwaway_%d.py" % i)).write_text(text)
    return tmp_path


def _run(suite, strict, baseline=None, workers="0"):
    env = {k: v for k, v in os.environ.items()
           if k not in ("DASH_STRICT", "DASH_BASELINE", "PYTEST_ADDOPTS",
                        "PYTEST_PLUGINS")}
    env["DASH_SUITE_LOCK"] = str(suite / "suite.lock")
    # The copy of conftest.py imports dash_render, which lives at the root.
    env["PYTHONPATH"] = os.pathsep.join(
        p for p in (os.path.dirname(_HERE), env.get("PYTHONPATH", "")) if p)
    if strict:
        env["DASH_STRICT"] = "1"
    if baseline:
        env["DASH_BASELINE"] = baseline
    return subprocess.run(
        [sys.executable, "-m", "pytest", str(suite), "-q",
         "-p", "no:cacheprovider", "-n", workers],
        cwd=str(suite), env=env, capture_output=True, text=True, timeout=300)


def _this_baseline():
    return C._baseline_name(C._running_env())


def _other_baseline():
    return "dev" if _this_baseline() == "stata" else "stata"


@pytest.mark.skipif(C._drift_problem(C._running_env()) != "",
                    reason="this interpreter matches no baseline")
class TestStrictModeOnARun:

    def test_a_skip_is_a_skip_outside_strict_mode(self, tmp_path):
        r = _run(_suite(tmp_path, _PASSES, _SKIPS), strict=False)
        assert r.returncode == 0, r.stdout + r.stderr
        assert "1 skipped" in r.stdout

    @pytest.mark.parametrize("workers", ["0", "2"])
    def test_a_skip_turns_a_strict_run_red(self, tmp_path, workers):
        r = _run(_suite(tmp_path, _PASSES, _SKIPS), strict=True,
                 baseline=_this_baseline(), workers=workers)
        assert r.returncode == 1, r.stdout + r.stderr
        assert "strict mode (DASH_STRICT=1): 1 test(s) skipped" in r.stdout
        assert "a fixture this machine lacks" in r.stdout

    def test_a_strict_run_with_no_skip_passes(self, tmp_path):
        r = _run(_suite(tmp_path, _PASSES), strict=True,
                 baseline=_this_baseline())
        assert r.returncode == 0, r.stdout + r.stderr

    def test_a_failure_stays_a_failure(self, tmp_path):
        r = _run(_suite(tmp_path, "def test_fails():\n    assert False\n"),
                 strict=True, baseline=_this_baseline())
        assert r.returncode == 1, r.stdout + r.stderr

    def test_the_wrong_baseline_stops_a_strict_run_before_any_test(
            self, tmp_path):
        r = _run(_suite(tmp_path, _PASSES), strict=True,
                 baseline=_other_baseline())
        assert r.returncode == 4, r.stdout + r.stderr
        out = r.stdout + r.stderr
        assert "differs from the %s baseline" % _other_baseline() in out
        assert "passed" not in r.stdout

    def test_the_wrong_baseline_is_only_a_warning_outside_strict_mode(
            self, tmp_path):
        r = _run(_suite(tmp_path, _PASSES), strict=False,
                 baseline=_other_baseline())
        assert r.returncode == 0, r.stdout + r.stderr
        assert "differs from the %s baseline" % _other_baseline() in r.stdout


# ---------------------------------------------------------------------------
# WP-33 TR-23: the tests that skipped on a measured false premise.  Strict
# mode already fails any skip at the gate; this static guard reads their
# source and fails on any skip site left in them (D-33-11.i).
# ---------------------------------------------------------------------------

_STANDING_SKIP_NODES = (
    "test/test_graph_text.py::TestBounds",
    "test/test_graph_text.py::TestOtherSmclDirectives::test_each_directive",
    "test/test_mode_parity.py::TestTheExportsAgree"
    "::test_the_moves_reach_the_exports",
)

_SKIP_CALLS = ("pytest.skip", "pytest.importorskip", "pytest.xfail")


def _dotted(node):
    """The dotted name of a Name/Attribute chain, or "" for anything
    else (a call's own function is read through)."""
    if isinstance(node, ast.Call):
        node = node.func
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return ""
    parts.append(node.id)
    return ".".join(reversed(parts))


def _skip_sites(node):
    """``"<file>:<line>: <what>"`` for each skip site in the class (and
    the method, when the node names one) *node* names: a ``mark.skip`` or
    ``mark.skipif`` decorator, bare or called, and a call of
    ``pytest.skip``, ``pytest.importorskip`` or ``pytest.xfail``.  A node
    naming no class or method is a site too."""
    path, _, rest = node.partition("::")
    names = rest.split("::")
    with open(os.path.join(os.path.dirname(_HERE), path),
              encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    cls = [c for c in tree.body
           if isinstance(c, ast.ClassDef) and c.name == names[0]]
    if not cls:
        return ["%s not found" % node]
    funcs = [f for f in cls[0].body
             if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if len(names) > 1:
        funcs = [f for f in funcs if f.name == names[1]]
        if not funcs:
            return ["%s not found" % node]
    out = []
    for f in funcs:
        for d in f.decorator_list:
            name = _dotted(d)
            if name.endswith("mark.skip") or name.endswith("mark.skipif"):
                out.append("%s:%d: @%s on %s" % (path, d.lineno, name,
                                                 f.name))
        for c in ast.walk(f):
            if isinstance(c, ast.Call) and _dotted(c.func) in _SKIP_CALLS:
                out.append("%s:%d: %s() in %s" % (path, c.lineno,
                                                  _dotted(c.func), f.name))
    return out


class TestNoStandingSkip:

    def test_none_of_them_can_skip(self):
        assert [s for n in _STANDING_SKIP_NODES
                for s in _skip_sites(n)] == []

    def test_the_reader_finds_each_kind_of_site(self, tmp_path,
                                                monkeypatch):
        """The reader sees decorators bare and called, the three calls,
        and a node that names nothing."""
        src = ("import pytest\n\n\nclass TestX:\n"
               "    @pytest.mark.skip\n    def test_a(self):\n"
               "        pass\n\n"
               "    @pytest.mark.skipif(True, reason='r')\n"
               "    def test_b(self):\n        pytest.skip('s')\n\n"
               "    def test_c(self):\n        pytest.importorskip('m')\n"
               "        pytest.xfail('x')\n\n"
               "    def test_d(self):\n        assert True\n")
        (tmp_path / "test").mkdir()
        (tmp_path / "test" / "test_x.py").write_text(src)
        monkeypatch.setattr(
            sys.modules[__name__], "_HERE", str(tmp_path / "test"))
        assert len(_skip_sites("test/test_x.py::TestX")) == 5
        assert _skip_sites("test/test_x.py::TestX::test_d") == []
        assert _skip_sites("test/test_x.py::TestY") == [
            "test/test_x.py::TestY not found"]
        assert _skip_sites("test/test_x.py::TestX::test_z") == [
            "test/test_x.py::TestX::test_z not found"]
