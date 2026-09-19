"""
test_dependency_guards.py
Regression tests for graceful degradation when an OPTIONAL third-party
plotting dependency is not installed.

Four smoother/fit glyphs import a heavy library lazily, inside the mapping
method, and none of those imports is guarded (verified in dash_render.py):

    dash_render.py:2404   from scipy import stats as scipy_stats           -> map_lfitci
    dash_render.py:2547   from statsmodels...smoothers_lowess import lowess -> map_lowess
    (map_kdensity used scipy.stats.gaussian_kde here until S07; it now
     implements Stata's kernels directly and needs no optional dependency.)
    dash_render.py:4001   from scipy.interpolate import PchipInterpolator  -> map_mspline

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
# map_lowess  --  statsmodels  (dash_render.py:2547)
# ================================================================
class TestLowessStatsmodelsGuard:

    def test_lowess_populated_when_statsmodels_available(self, fig, fit_cds, gm):
        """With statsmodels importable, map_lowess returns a populated renderer.

        statsmodels is currently broken under this interpreter
        (ModuleNotFoundError: packaging), so this SKIPS rather than errors.
        """
        pytest.importorskip(
            "statsmodels.nonparametric.smoothers_lowess",
            reason="statsmodels not importable in this interpreter",
        )
        result = gm.map_lowess(fig, fit_cds, "y", "x", {})
        assert_populated_source(result, "map_lowess with statsmodels present")

    def test_lowess_missing_statsmodels_warns_and_degrades(self, fig, fit_cds, gm):
        """map_lowess must warn + return an empty renderer, not raise."""
        import warnings
        with blocked_import("statsmodels"):
            with warnings.catch_warnings(record=True) as record:
                warnings.simplefilter("always")
                result = call_expecting_graceful(
                    lambda: gm.map_lowess(fig, fit_cds, "y", "x", {}), "map_lowess"
                )
        assert_guard_warning(record, "statsmodels", "map_lowess")
        assert_empty_source(result, "map_lowess without statsmodels")

    def test_lowess_missing_statsmodels_does_not_raise(self, fig, fit_cds, gm):
        """The bare no-raise contract, isolated from the warning assertion."""
        import warnings
        with blocked_import("statsmodels"):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                try:
                    result = gm.map_lowess(fig, fit_cds, "y", "x", {})
                except BaseException as exc:  # noqa: BLE001 - intentional
                    pytest.fail(
                        f"map_lowess raised {type(exc).__name__}: {exc} instead "
                        f"of degrading gracefully"
                    )
        assert result is not None


# ================================================================
# map_lfitci  --  scipy.stats  (dash_render.py:2404)
# ================================================================
class TestLfitciScipyGuard:

    def test_lfitci_populated_when_scipy_available(self, fig, fit_cds, gm):
        pytest.importorskip("scipy.stats", reason="scipy not importable")
        result = gm.map_lfitci(fig, fit_cds, "y", "x", {})
        assert len(as_renderers(result)) == 2, (
            "map_lfitci must return [line_renderer, band_renderer]"
        )
        assert_populated_source(result, "map_lfitci with scipy present")

    def test_lfitci_missing_scipy_warns_and_degrades(self, fig, fit_cds, gm):
        import warnings
        with blocked_import("scipy"):
            with warnings.catch_warnings(record=True) as record:
                warnings.simplefilter("always")
                result = call_expecting_graceful(
                    lambda: gm.map_lfitci(fig, fit_cds, "y", "x", {}), "map_lfitci"
                )
        assert_guard_warning(record, "scipy", "map_lfitci")
        assert len(as_renderers(result)) == 2, (
            "degraded map_lfitci must keep the 2-renderer return shape"
        )
        assert_empty_source(result, "map_lfitci without scipy")

    def test_lfitci_missing_scipy_does_not_raise(self, fig, fit_cds, gm):
        import warnings
        with blocked_import("scipy"):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                try:
                    result = gm.map_lfitci(fig, fit_cds, "y", "x", {})
                except BaseException as exc:  # noqa: BLE001 - intentional
                    pytest.fail(
                        f"map_lfitci raised {type(exc).__name__}: {exc} instead "
                        f"of degrading gracefully"
                    )
        assert result is not None


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
# map_mspline  --  scipy.interpolate.PchipInterpolator  (dash_render.py:4001)
# ================================================================
class TestMsplineScipyGuard:

    def test_mspline_populated_when_scipy_available(self, fig, fit_cds, gm):
        pytest.importorskip("scipy.interpolate", reason="scipy not importable")
        result = gm.map_mspline(fig, fit_cds, "y", "x", {})
        assert isinstance(result, list), "map_mspline must return a list"
        assert_populated_source(result, "map_mspline with scipy present")

    def test_mspline_missing_scipy_warns_and_degrades(self, fig, fit_cds, gm):
        import warnings
        with blocked_import("scipy"):
            with warnings.catch_warnings(record=True) as record:
                warnings.simplefilter("always")
                result = call_expecting_graceful(
                    lambda: gm.map_mspline(fig, fit_cds, "y", "x", {}), "map_mspline"
                )
        assert_guard_warning(record, "scipy", "map_mspline")
        assert isinstance(result, list), (
            "degraded map_mspline must keep the list return shape"
        )
        assert_empty_source(result, "map_mspline without scipy")

    def test_mspline_missing_scipy_does_not_raise(self, fig, fit_cds, gm):
        import warnings
        with blocked_import("scipy"):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                try:
                    result = gm.map_mspline(fig, fit_cds, "y", "x", {})
                except BaseException as exc:  # noqa: BLE001 - intentional
                    pytest.fail(
                        f"map_mspline raised {type(exc).__name__}: {exc} instead "
                        f"of degrading gracefully"
                    )
        assert result is not None


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
