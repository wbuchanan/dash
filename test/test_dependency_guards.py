"""
test_dependency_guards.py
Regression tests for graceful degradation when an OPTIONAL third-party
plotting dependency is not installed.

Four smoother/fit glyphs imported a heavy library lazily, inside the mapping
method, and none of those imports was guarded (verified in dash_render.py at
the time):

    from scipy import stats as scipy_stats                       -> map_lfitci
    from statsmodels...smoothers_lowess import lowess            -> map_lowess
    scipy.stats.gaussian_kde                                     -> map_kdensity
    from scipy.interpolate import PchipInterpolator              -> map_mspline

All four are gone, not guarded: map_kdensity implements Stata's kernels
directly (S07); map_lowess is Stata's own smoother in numpy, map_mspline the
cross-median cubic spline twoway draws, and map_lfitci a weighted least
squares with dash's own t quantile (WP-18, test_statistical_truth.py).  Each
must now draw with the package entirely unavailable and must not reach for
it.  The guard shape below is kept for the record and for any optional
import a later layer adds.

When the library is missing the ModuleNotFoundError escapes the mapper and
kills the whole render, so a user loses the entire dashboard because one
optional smoother could not be drawn.

REQUIRED BEHAVIOUR (the shape these tests pin down) is the one already used by
the slider dtype guard at dash_render.py:7203 -- warnings.warn() naming the
problem and telling the user how to fix it, then carry on with an empty
renderer instead of raising:

    1. emit a UserWarning naming the missing library AND pointing at dash_setup
    2. return the same renderer shape the populated path returns
    3. that renderer's ColumnDataSource is empty
    4. DO NOT raise

Per CLAUDE.md rule 8 these tests are written to FAIL against the current
unguarded code (the ModuleNotFoundError escapes) and to pass after the guard
is added.

NOTE ON map_qfitci: the plan attributed the scipy import at :2404 to both
map_lfitci and map_qfitci.  That is not what the code does -- map_qfitci
(dash_render.py:2456) uses numpy.polyfit plus GlyphMapper._bootstrap_ci and
imports nothing from scipy.  TestQfitciNeedsNoScipy below is a control test
documenting that verified fact; it passes today and must keep passing.

Run with:  pytest test/test_dependency_guards.py -v
"""
import builtins
import contextlib
import os
import sys

import numpy as np
import pytest

# Add parent directory (same bootstrap as test/test_glyphs.py)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dash_render import GlyphMapper

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, GlyphRenderer


# ================================================================
# Helpers
# ================================================================

@contextlib.contextmanager
def blocked_import(root: str):
    """Make every ``import`` of *root* (or ``root.anything``) fail.

    The four imports under test are lazy -- they execute inside the mapping
    method on every call -- so patching ``builtins.__import__`` intercepts
    them even when the real library is installed and already cached in
    ``sys.modules``: the IMPORT_NAME opcode calls ``__import__`` regardless.

    Imports of every *other* module are delegated to the real ``__import__``
    so Bokeh/numpy machinery inside the mapper keeps working.
    """
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == root or name.startswith(root + "."):
            raise ModuleNotFoundError(f"No module named '{root}'", name=root)
        return real_import(name, globals, locals, fromlist, level)

    builtins.__import__ = fake_import
    try:
        yield
    finally:
        builtins.__import__ = real_import


def as_renderers(result):
    """Normalise a mapper return value (renderer or list) to a list."""
    return list(result) if isinstance(result, (list, tuple)) else [result]


def assert_empty_source(result, context: str):
    """Every returned renderer must carry a ColumnDataSource with no rows."""
    renderers = as_renderers(result)
    assert renderers, f"{context}: expected at least one renderer, got {result!r}"
    for r in renderers:
        assert isinstance(r, GlyphRenderer), (
            f"{context}: expected a GlyphRenderer, got {type(r).__name__}"
        )
        data = r.data_source.data
        for col, values in data.items():
            assert len(values) == 0, (
                f"{context}: degraded renderer column {col!r} should be empty, "
                f"has {len(values)} rows"
            )


def assert_populated_source(result, context: str):
    """At least one returned renderer must carry actual data."""
    renderers = as_renderers(result)
    assert renderers, f"{context}: expected at least one renderer, got {result!r}"
    total = 0
    for r in renderers:
        assert isinstance(r, GlyphRenderer), (
            f"{context}: expected a GlyphRenderer, got {type(r).__name__}"
        )
        total += sum(len(v) for v in r.data_source.data.values())
    assert total > 0, f"{context}: renderer data source is empty, expected data"


def assert_guard_warning(record, library: str, context: str):
    """The degradation warning must name the library and mention dash_setup."""
    messages = [str(w.message) for w in record]
    assert messages, f"{context}: no warning captured"
    hits = [
        m for m in messages
        if library.lower() in m.lower() and "dash_setup" in m.lower()
    ]
    assert hits, (
        f"{context}: expected a UserWarning naming {library!r} AND mentioning "
        f"dash_setup; captured warnings were {messages!r}"
    )


def assert_no_import_of(method, package: str, context: str):
    """*method*'s source neither imports *package* nor asks _optional_import
    for it.  Prose (a docstring or comment explaining WHY the package is
    gone) is not an import and must not decide this."""
    import inspect
    import re
    code = "\n".join(
        line.split("#", 1)[0] for line in inspect.getsource(method).splitlines()
    )
    assert not re.search(rf"^\s*(from|import)\s+{package}\b", code, re.M), (
        f"{context} imports {package} again"
    )
    assert not re.search(rf"_optional_import\([^)]*{package}", code), (
        f"{context} asks _optional_import for {package} again"
    )


def call_expecting_graceful(fn, context: str):
    """Call *fn*, failing loudly if the optional-dependency error escapes.

    This makes the headline failure message the actual defect ("the exception
    escaped") rather than a downstream symptom such as pytest.warns reporting
    DID NOT WARN.
    """
    try:
        return fn()
    except BaseException as exc:  # noqa: BLE001 - the whole point of the test
        pytest.fail(
            f"{context} raised {type(exc).__name__}: {exc} instead of "
            f"degrading gracefully (warn + empty renderer)"
        )


# ================================================================
# Fixtures
# ================================================================

@pytest.fixture
def fig():
    """Blank Bokeh figure."""
    return figure()


@pytest.fixture
def gm():
    """GlyphMapper instance."""
    return GlyphMapper()


@pytest.fixture
def fit_cds():
    """ColumnDataSource with enough well-behaved points for any smoother."""
    rng = np.random.RandomState(0)
    n = 30
    x = np.linspace(1, 10, n)
    y = 2 * x + rng.randn(n)
    return ColumnDataSource({"y": y, "x": x})


# ================================================================
# map_lowess  --  NO LONGER NEEDS statsmodels
# ================================================================
# WP-18 replaced statsmodels' lowess (it=3 bisquare iterations, a nearest-
# by-distance neighbourhood, one value per tied x) with Stata's smoother:
# a stable sort by x, a symmetric window of 2k+1 observations BY INDEX,
# tricube weights, one local line per observation.  Measured 23sep2026:
# statsmodels was 3.7e-2 .. 4.4e-1 of the y range away from `lowess` on
# every fixture dataset; the numpy rule reproduces all 20 probes to 2e-13
# (test_statistical_truth.py::TestLowessIsStatasSmoother).  The guard these
# tests pinned is gone because the dependency is.
class TestLowessNeedsNoOptionalDependency:

    def test_lowess_populated(self, fig, fit_cds, gm):
        result = gm.map_lowess(fig, fit_cds, "y", "x", {})
        assert_populated_source(result, "map_lowess")

    def test_lowess_populated_even_without_statsmodels(self, fig, fit_cds, gm):
        """The whole point of dropping statsmodels: no optional import left."""
        import warnings
        with blocked_import("statsmodels"):
            with warnings.catch_warnings(record=True) as record:
                warnings.simplefilter("always")
                result = gm.map_lowess(fig, fit_cds, "y", "x", {})
        assert_populated_source(result, "map_lowess without statsmodels")
        assert not [w for w in record if "statsmodels" in str(w.message)], (
            "map_lowess still reaches for statsmodels somewhere"
        )

    def test_lowess_source_has_no_statsmodels_import(self):
        """Guard against statsmodels creeping back into the lowess path."""
        assert_no_import_of(GlyphMapper.map_lowess, "statsmodels", "map_lowess")


# ================================================================
# map_lfitci  --  NO LONGER NEEDS scipy
# ================================================================
# WP-18 gave lfitci weights (aw/fw/pw) and the stdf/stdr band types.
# scipy's linregress takes no weights, so the fit is a weighted least
# squares in numpy and the band is the same stdp/stdf/stdr algebra qfitci
# already used, with dash's own scipy-free t quantile (_t_ppf).  The guard
# these tests pinned is gone because the dependency is.
class TestLfitciNeedsNoOptionalDependency:

    def test_lfitci_populated(self, fig, fit_cds, gm):
        result = gm.map_lfitci(fig, fit_cds, "y", "x", {})
        assert len(as_renderers(result)) == 2, (
            "map_lfitci must return [line_renderer, band_renderer]"
        )
        assert_populated_source(result, "map_lfitci")

    def test_lfitci_populated_even_without_scipy(self, fig, fit_cds, gm):
        import warnings
        with blocked_import("scipy"):
            with warnings.catch_warnings(record=True) as record:
                warnings.simplefilter("always")
                result = gm.map_lfitci(fig, fit_cds, "y", "x", {})
        assert len(as_renderers(result)) == 2
        assert_populated_source(result, "map_lfitci without scipy")
        assert not [w for w in record if "scipy" in str(w.message)], (
            "map_lfitci still reaches for scipy somewhere"
        )

    def test_lfitci_source_has_no_scipy_import(self):
        assert_no_import_of(GlyphMapper.map_lfitci, "scipy", "map_lfitci")


# ================================================================
# map_kdensity  --  NO LONGER NEEDS scipy
# ================================================================
# S07 replaced scipy.stats.gaussian_kde with Stata's own kernel definitions
# (_KERNELS in dash_render.py).  gaussian_kde can only ever be Gaussian, so it
# could not express kernel() at all, and Stata's default kernel is
# epanechnikov.  The guard these tests used to pin is therefore gone -- not
# because the requirement was dropped, but because the dependency was.  The
# tests below assert the STRONGER property that replaced it: kdensity works
# with scipy entirely unavailable.
class TestKdensityNeedsNoOptionalDependency:

    def test_kdensity_populated(self, fig, fit_cds, gm):
        result = gm.map_kdensity(fig, fit_cds, "y", {})
        assert_populated_source(result, "map_kdensity")

    def test_kdensity_populated_even_without_scipy(self, fig, fit_cds, gm):
        """The whole point of dropping gaussian_kde: no optional import left."""
        import warnings
        with blocked_import("scipy"):
            with warnings.catch_warnings(record=True) as record:
                warnings.simplefilter("always")
                result = gm.map_kdensity(fig, fit_cds, "y", {})
        assert_populated_source(result, "map_kdensity without scipy")
        assert not [w for w in record if "scipy" in str(w.message)], (
            "map_kdensity still reaches for scipy somewhere"
        )

    def test_kdensity_source_has_no_scipy_import(self):
        """Guard against gaussian_kde creeping back into the kdensity path."""
        import inspect
        from dash_render import GlyphMapper as _GM
        # Strip comments: the method explains in prose WHY scipy is gone, and
        # that explanation must not be what makes this test pass or fail.
        code = "\n".join(
            line.split("#", 1)[0]
            for line in inspect.getsource(_GM.map_kdensity).splitlines()
        )
        assert "gaussian_kde" not in code, "gaussian_kde is back in map_kdensity"
        assert "scipy" not in code, "map_kdensity imports scipy again"


# ================================================================
# map_mspline  --  NO LONGER NEEDS scipy
# ================================================================
# WP-18 replaced scipy's PchipInterpolator through every observation (14.0
# mpg away from `twoway mspline` on auto, bands()/n() ignored) with what
# twoway draws: the cross medians of bands() equal-width bands as knots and
# a natural cubic spline through them, n() points between adjacent knots,
# in numpy (test_statistical_truth.py::TestMsplineAgainstStata).  The guard
# these tests pinned is gone because the dependency is.
class TestMsplineNeedsNoOptionalDependency:

    def test_mspline_populated(self, fig, fit_cds, gm):
        result = gm.map_mspline(fig, fit_cds, "y", "x", {})
        assert isinstance(result, list), "map_mspline must return a list"
        assert_populated_source(result, "map_mspline")

    def test_mspline_populated_even_without_scipy(self, fig, fit_cds, gm):
        import warnings
        with blocked_import("scipy"):
            with warnings.catch_warnings(record=True) as record:
                warnings.simplefilter("always")
                result = gm.map_mspline(fig, fit_cds, "y", "x", {})
        assert isinstance(result, list), "map_mspline must return a list"
        assert_populated_source(result, "map_mspline without scipy")
        assert not [w for w in record if "scipy" in str(w.message)], (
            "map_mspline still reaches for scipy somewhere"
        )

    def test_mspline_source_has_no_scipy_import(self):
        assert_no_import_of(GlyphMapper.map_mspline, "scipy", "map_mspline")


# ================================================================
# Control: map_qfitci has NO scipy dependency
# ================================================================
class TestQfitciNeedsNoScipy:
    """map_qfitci (dash_render.py:2456) uses numpy.polyfit + _bootstrap_ci.

    It imports nothing from scipy, so it must keep working -- fully populated,
    no warning, no exception -- even with scipy unavailable.  This test passes
    against the current code and guards against a future 'fix' that bolts an
    unnecessary scipy import (or a spurious degradation) onto qfitci.
    """

    def test_qfitci_works_without_scipy(self, fig, fit_cds, gm):
        import warnings
        with blocked_import("scipy"):
            with warnings.catch_warnings(record=True) as record:
                warnings.simplefilter("always")
                result = gm.map_qfitci(fig, fit_cds, "y", "x", {})
        assert len(as_renderers(result)) == 2, (
            "map_qfitci must return [line_renderer, band_renderer]"
        )
        assert_populated_source(result, "map_qfitci without scipy")
        dep_warnings = [
            str(w.message) for w in record
            if "scipy" in str(w.message).lower()
        ]
        assert not dep_warnings, (
            f"map_qfitci needs no scipy; it must not warn about it: {dep_warnings!r}"
        )


# ================================================================
# WP-30 P1.32: render-time dependency guards
# ================================================================
# numpy, pandas or bokeh missing or broken, or a Python below dash's floor,
# used to end in a bare ModuleNotFoundError or SyntaxError naming no
# remedy.  The renderer and the served app's header now stop in one line
# naming dash_setup (_dash_dep_fail): exit status 1 as a program, an
# ImportError as a module or under Stata (with the line in the local
# _dd_err), and dash.ado checks the same before any Python of a command
# runs (_dash_require_deps).

import ast as _ast_s25
import inspect as _inspect_s25
import json as _json_s25
import re as _re_s25
import subprocess as _sp_s25
import textwrap as _tw_s25

_S25_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_RENDER = os.path.join(_S25_ROOT, "dash_render.py")
_FLOOR = "3.11"  # _dash_pymin; test_version_floor.py pins every copy equal


def _run(code, *args, cwd=None):
    """Run ``code`` in a fresh ``sys.executable -B``; (rc, stdout, stderr)."""
    p = _sp_s25.run([sys.executable, "-B", "-c", code] + list(args),
                    capture_output=True, text=True, timeout=120, cwd=cwd)
    return p.returncode, p.stdout, p.stderr


def _block(pkg):
    return "import sys; sys.modules[%r] = None\n" % pkg


def _old(ver):
    return ("import sys, collections; sys.version_info = collections."
            "namedtuple('version_info', 'major minor micro releaselevel "
            "serial')(*%r)\n" % (ver,))


def _as_main(path, *argv):
    return ("import runpy, sys; sys.argv = %r; runpy.run_path(%r, "
            "run_name='__main__')\n" % ([os.path.basename(path)] + list(argv),
                                        path))


def _build_app(tmp_path):
    sys.path.insert(0, os.path.dirname(__file__))
    from test_version_floor import TestTheGeneratedAppEvaluatesNoAnnotationAtImport as _T
    src = _T()._built(tmp_path)
    return str(tmp_path / "app.py"), src


def _body(name):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from test_program_coverage_map import _ado_programs, _logical_lines
    with open(os.path.join(_S25_ROOT, "dash.ado"), encoding="utf-8") as fh:
        text = fh.read()
    progs = _ado_programs(text)
    assert name in progs, "dash.ado defines no program %s" % name
    first, last = progs[name]
    return [line for n, line in _logical_lines(text) if first < n < last]


def _one_line(err):
    lines = [ln for ln in err.strip().split("\n") if ln.strip()]
    assert len(lines) == 1, err
    assert "Traceback" not in err, err
    return lines[0]


class TestTheRendererRefusesWithTheRemedy:
    @pytest.mark.parametrize("pkg", ["numpy", "pandas", "bokeh"])
    def test_a_missing_package_is_one_line_naming_dash_setup(self, pkg, tmp_path):
        rc, _out, err = _run(_block(pkg) + _as_main(
            _RENDER, "--spec", "x", "--data", "y", "--output", "z.html"),
            cwd=str(tmp_path))
        assert rc == 1, err
        line = _one_line(err)
        assert line.startswith("dash: could not import %s for the Python at "
                               % pkg), line
        assert sys.executable in line, line
        assert line.endswith("; run dash_setup"), line

    def test_a_package_that_will_not_import_is_named_with_its_reason(self, tmp_path):
        """jinja2 is a dependency of bokeh's, not of numpy or pandas at
        import: blocking it breaks bokeh only."""
        rc, _out, err = _run(_block("jinja2") + _as_main(
            _RENDER, "--spec", "x", "--data", "y", "--output", "z.html"),
            cwd=str(tmp_path))
        assert rc == 1, err
        line = _one_line(err)
        assert "could not import bokeh" in line and "jinja2" in line, line

    def test_a_python_below_the_floor_is_refused_before_any_import(self, tmp_path):
        rc, _out, err = _run(_old((3, 6, 15, "final", 0)) + _block("numpy")
                             + _as_main(_RENDER, "--spec", "x"),
                             cwd=str(tmp_path))
        assert rc == 1, err
        line = _one_line(err)
        assert "Python 3.6.15" in line, line
        assert "Python %s or later" % _FLOOR in line, line
        assert "dash_setup" in line and "numpy" not in line, line

    def test_under_stata_the_refusal_is_an_import_error_and_a_local(self, tmp_path):
        pre = ("import sys, types, json, importlib.util, runpy\n"
               "LOC = {}\n"
               "sfi = types.ModuleType('sfi')\n"
               "sfi.Macro = types.SimpleNamespace(setLocal=LOC.__setitem__, "
               "getLocal=LOC.get)\n"
               "sys.modules['sfi'] = sfi\n" + _block("pandas"))
        code = pre + (
            "out = []\n"
            "for how in ('module', 'main'):\n"
            "    LOC.clear()\n"
            "    try:\n"
            "        if how == 'module':\n"
            "            s = importlib.util.spec_from_file_location('_dash_render_export', %r)\n"
            "            m = importlib.util.module_from_spec(s)\n"
            "            s.loader.exec_module(m)\n"
            "        else:\n"
            "            runpy.run_path(%r, run_name='__main__')\n"
            "    except BaseException as e:\n"
            "        out.append([type(e).__name__, str(e), dict(LOC)])\n"
            "print(json.dumps(out))\n" % (_RENDER, _RENDER))
        rc, out, err = _run(code, cwd=str(tmp_path))
        assert rc == 0, err
        got = _json_s25.loads(out.strip().split("\n")[-1])
        assert len(got) == 2, got
        for name, msg, loc in got:
            assert name == "ImportError", got
            assert loc.get("_dd_err") == msg, got
            assert "pandas" in msg and "dash_setup" in msg, got

    @pytest.mark.skipif(not (os.path.exists("/usr/local/bin/python3.6")
                             and os.path.exists("/usr/local/bin/python3.7")),
                        reason="needs /usr/local/bin/python3.6 and python3.7")
    def test_the_old_interpreters_here_get_the_remedy(self, tmp_path):
        args = [_RENDER, "--spec", "s.json", "--data", "d.json",
                "--output", "o.html"]
        p6 = _sp_s25.run(["/usr/local/bin/python3.6", "-B"] + args,
                         capture_output=True, text=True, timeout=120,
                         cwd=str(tmp_path))
        assert "SyntaxError" in p6.stderr, p6.stderr
        assert ("dash needs Python %s or later: link a newer Python, then "
                "run dash_setup" % _FLOOR) in p6.stderr, p6.stderr
        p7 = _sp_s25.run(["/usr/local/bin/python3.7", "-B"] + args,
                         capture_output=True, text=True, timeout=120,
                         cwd=str(tmp_path))
        assert p7.returncode == 1, p7.stderr
        line = _one_line(p7.stderr)
        assert line.startswith("dash: Python 3.7."), line
        assert "older than dash needs" in line, line


def _is_dep_fail_try(node):
    if not isinstance(node, _ast_s25.Try):
        return False
    if not any(isinstance(n, (_ast_s25.Import, _ast_s25.ImportFrom))
               for n in node.body):
        return False
    return True


def _check_guarded_top_level(tree):
    """The import layout both files keep; returns the problems."""
    bad = []
    std = set(sys.stdlib_module_names) | {"__future__"}
    first_try = None
    version_if = None
    for i, node in enumerate(tree.body):
        if isinstance(node, (_ast_s25.Import, _ast_s25.ImportFrom)):
            names = ([a.name for a in node.names]
                     if isinstance(node, _ast_s25.Import) else [node.module])
            for n in names:
                if (n or "").split(".")[0] not in std:
                    bad.append("line %d imports %s outside a guard"
                               % (node.lineno, n))
        elif _is_dep_fail_try(node):
            if first_try is None:
                first_try = i
            h = node.handlers
            ok = (len(h) == 1 and isinstance(h[0].type, _ast_s25.Name)
                  and h[0].type.id == "Exception" and h[0].name == "_dash_e"
                  and len(h[0].body) == 1
                  and isinstance(h[0].body[0], _ast_s25.Expr)
                  and isinstance(h[0].body[0].value, _ast_s25.Call)
                  and getattr(h[0].body[0].value.func, "id", "") == "_dash_dep_fail")
            if not ok:
                bad.append("line %d: the guard's handler is not one "
                           "_dash_dep_fail call" % node.lineno)
        elif (isinstance(node, _ast_s25.If) and version_if is None
              and "version_info" in _ast_s25.dump(node.test)):
            version_if = i
    if first_try is None:
        bad.append("no guarded import")
    elif version_if is None or version_if > first_try:
        bad.append("the version check does not precede the first guard")
    return bad


class TestTheGuardKeepsAHealthyImport:
    def test_every_unguarded_top_level_import_is_the_standard_library(self):
        with open(_RENDER, encoding="utf-8") as fh:
            tree = _ast_s25.parse(fh.read())
        assert _check_guarded_top_level(tree) == []

    def test_both_files_parse_at_python_3_7(self):
        sys.path.insert(0, os.path.join(_S25_ROOT, "scripts", "fncov"))
        import fncov_report
        with open(_RENDER, encoding="utf-8") as fh:
            render = _ast_s25.parse(fh.read(), feature_version=(3, 7))
        app = _ast_s25.parse(fncov_report.sample_app_source(),
                             feature_version=(3, 7))
        # Both reach the guard on 3.7-3.10: each defines _dash_dep_fail.
        for tree in (render, app):
            assert any(isinstance(n, _ast_s25.FunctionDef)
                       and n.name == "_dash_dep_fail" for n in tree.body)


class TestTheServedAppGuardsItsImports:
    @pytest.mark.parametrize("pkg", ["numpy", "pandas", "bokeh"])
    def test_the_app_refuses_a_missing_package_in_one_line(self, pkg, tmp_path):
        app, _src = _build_app(tmp_path)
        rc, _out, err = _run(_block(pkg) + _as_main(app, "--port", "5999"),
                             cwd=str(tmp_path))
        assert rc == 1, err
        line = _one_line(err)
        assert ("could not import %s" % pkg) in line, line
        assert line.endswith("; run dash_setup"), line

    def test_under_bokeh_serve_the_refusal_is_an_import_error(self, tmp_path):
        app, _src = _build_app(tmp_path)
        code = _block("pandas") + (
            "import runpy\n"
            "try:\n"
            "    runpy.run_path(%r, run_name='bokeh_app_s25')\n"
            "except BaseException as e:\n"
            "    print(type(e).__name__)\n"
            "    print(str(e))\n" % app)
        rc, out, err = _run(code, cwd=str(tmp_path))
        assert rc == 0, err
        kind, msg = out.strip().split("\n")[-2:]
        assert kind == "ImportError", out
        assert "pandas" in msg and "dash_setup" in msg, out

    def test_the_app_refuses_a_python_below_the_floor(self, tmp_path):
        app, _src = _build_app(tmp_path)
        rc, _out, err = _run(_old((3, 6, 15, "final", 0)) + _block("numpy")
                             + _as_main(app, "--port", "5999"),
                             cwd=str(tmp_path))
        assert rc == 1, err
        line = _one_line(err)
        assert "Python 3.6.15" in line and ("Python %s or later" % _FLOOR) in line, line
        assert "numpy" not in line, line

    def test_the_header_guards_before_any_package_import(self, tmp_path):
        import dash_render as dr
        _app, src = _build_app(tmp_path)
        tree = _ast_s25.parse(src)
        lines = src.split("\n")
        fut = tree.body[1]
        assert isinstance(fut, _ast_s25.ImportFrom) and fut.module == "__future__"
        assert "dash needs Python %s or later" % _FLOOR in lines[fut.lineno - 1]
        assert _check_guarded_top_level(tree) == []
        first_try = next(i for i, n in enumerate(tree.body) if _is_dep_fail_try(n))
        const = next(i for i, n in enumerate(tree.body)
                     if isinstance(n, _ast_s25.Assign)
                     and getattr(n.targets[0], "id", "") == "_DASH_MIN_PYTHON")
        assert const < first_try
        fn = next(n for n in tree.body if isinstance(n, _ast_s25.FunctionDef)
                  and n.name == "_dash_dep_fail")
        got = "\n".join(lines[fn.lineno - 1:fn.end_lineno])
        want = _tw_s25.dedent(_inspect_s25.getsource(dr._dash_dep_fail)).rstrip("\n")
        assert got == want
        guarded = [_ast_s25.dump(s) for n in tree.body if _is_dep_fail_try(n)
                   for s in n.body]
        assert any("tornado" in d for d in guarded)


class TestTheVersionNote:
    def test_the_installed_versions_need_no_note(self):
        import dash_render as dr
        assert dr._dash_dep_versions() == ("", "")

    def test_numpy_or_pandas_below_the_minimum_is_noted(self, monkeypatch):
        import dash_render as dr
        monkeypatch.setattr(dr.np, "__version__", "2.1.3")
        refuse, note = dr._dash_dep_versions()
        assert refuse == ""
        assert "numpy 2.1.3" in note and "2.3" in note and "pandas" not in note
        monkeypatch.setattr(dr.pd, "__version__", "2.2.0")
        refuse, note = dr._dash_dep_versions()
        assert refuse == ""
        assert "numpy 2.1.3" in note and "pandas 2.2.0" in note, note
        assert note.count("dash goes on") == 1, note

    @pytest.mark.parametrize("text", ["dev", ""])
    def test_an_unreadable_version_is_not_noted(self, monkeypatch, text):
        import dash_render as dr
        monkeypatch.setattr(dr.np, "__version__", text)
        assert dr._dash_dep_versions() == ("", "")


class TestTheGuardOrder:
    def test_the_dependency_guard_follows_the_mata_guard_and_spares_clear(self):
        body = _body("dash")
        want = ["_dash_require_mata",
                'mata: st_local("_dd_sub",',
                'if "`_dd_sub\'" != "clear" {',
                "_dash_require_deps",
                "mata: _dash_prefix_word()",
                '"`_subcmd\'" ==']
        pos = []
        for w in want:
            hit = [i for i, line in enumerate(body) if line.startswith(w) or (w.startswith('"') and w in line)]
            assert hit, "dash has no line %r" % w
            pos.append(hit[0])
        assert pos == sorted(pos), list(zip(want, pos))

    def test_the_loader_and_the_render_run_the_guard_first(self):
        body = _body("_dash_xm_load")
        assert body[:3] == ["version 19", "_dash_require_python",
                            "_dash_require_deps"], body[:3]
        ex = [i for i, line in enumerate(body) if "exec_module(_dash_xm)" in line]
        assert body[ex[0]].startswith("capture python:"), body[ex[0]]
        assert body[ex[0] + 2] == "local _dd_n : length local _dd_err", body[ex[0] + 2]
        text = "\n".join(body)
        for name in ("_dd_err", "_dd_refuse", "_dd_note"):
            assert "`%s'" % name not in text, name
        render = _body("_dash_do_render")
        rp = render.index("_dash_require_python")
        assert render[rp + 1] == "_dash_require_deps"
        # Every other program running python: reaches the guard first,
        # directly or through the loader or the private folder's opener.
        from test_program_coverage_map import _ado_programs
        with open(os.path.join(_S25_ROOT, "dash.ado"), encoding="utf-8") as fh:
            names = _ado_programs(fh.read())
        late = []
        for name in names:
            if name in ("_dash_require_deps", "_dash_tmp_clear"):
                continue
            body_n = _body(name)
            py = [i for i, ln in enumerate(body_n)
                  if _re_s25.match(r"(capture\s+)?python\b", ln)]
            if not py:
                continue
            guard = [i for i, ln in enumerate(body_n)
                     if ln.split(" ")[0] in ("_dash_require_deps",
                                              "_dash_xm_load", "_dash_tmp_open")]
            # Flipped (WP-31 D15): a captured loader whose next line takes
            # the branch only on success guards what that branch runs --
            # _dash_prepare_spec asks for Stata's own ticks so, and a
            # failure leaves every axis to the renderer's model.
            guard += [i for i, ln in enumerate(body_n)
                      if ln == "capture _dash_xm_load"
                      and i + 1 < len(body_n)
                      and body_n[i + 1] == "if _rc == 0 {"]
            guard.sort()
            if not guard or guard[0] > py[0]:
                late.append(name)
        assert late == [], late

    def test_the_guard_decides_from_values(self):
        body = _body("_dash_require_deps")
        py = [line for line in body if "python:" in line]
        assert py and all(line.startswith("capture python:") for line in py), py
        text = "\n".join(body)
        for name in ("_dd_v", "_dd_miss", "_dd_chk"):
            assert 'setLocal("%s"' % name in text, name
        assert not _re_s25.search(r"\b_rc\b", text), text


class TestTheBlockHelper:
    def test_missing_and_broken_restore_every_module(self, tmp_path):
        code = """
import sys, os, types, importlib.util
sys.path.insert(0, %r)
import json, dep_block as B
orig = sys.modules["json"]
B.block("json", "missing")
try:
    import json as j1
    raise SystemExit("missing json imported")
except ImportError:
    pass
assert B.restore() and sys.modules["json"] is orig
B.block("json", "broken")
assert importlib.util.find_spec("json") is not None
try:
    import json as j2
    raise SystemExit("broken json imported")
except ImportError as e:
    assert "json" in str(e)
assert B.restore() and sys.modules["json"] is orig
vi = sys.version_info
B.fake_version((3, 6, 15, "final", 0))
assert sys.version_info.major == 3 and sys.version_info[:2] == (3, 6)
fake = types.ModuleType("fakepkg"); fake.__version__ = "9.9"
sys.modules["fakepkg"] = fake
B.fake_package_version("fakepkg", "1.0")
assert fake.__version__ == "1.0"
real_sfi = types.ModuleType("sfi"); real_sfi.Macro = object()
sys.modules["sfi"] = real_sfi
B.sfi_flaky()
try:
    from sfi import Macro
    raise SystemExit("flaky sfi answered first")
except ImportError:
    pass
from sfi import Macro
assert Macro is real_sfi.Macro and B._HITS[0] == 1
tmp = %r
os.mkdir(os.path.join(tmp, "dash-%%d" %% os.getuid()), 0o700)
run = B.plant_run(tmp)
assert os.path.isdir(run)
pp = os.environ.get("PYTHONPATH")
d = B.child_stub()
assert os.path.exists(os.path.join(d, "pandas.py")) and os.environ["PYTHONPATH"] == d
assert B.restore()
assert sys.version_info is vi and fake.__version__ == "9.9"
assert sys.modules["sfi"] is real_sfi
assert os.environ.get("PYTHONPATH") == pp and not os.path.exists(d)
print("ok")
""" % (os.path.dirname(os.path.abspath(__file__)), str(tmp_path))
        rc, out, err = _run(code, cwd=str(tmp_path))
        assert rc == 0 and out.strip().endswith("ok"), err
