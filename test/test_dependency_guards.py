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
