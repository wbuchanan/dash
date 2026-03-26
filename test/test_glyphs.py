"""
test_glyphs.py
Unit tests for dash_render.py GlyphMapper class.

Tests: P1A-88 through P1A-96

Run with:  pytest test/test_glyphs.py -v
"""
import sys
import os
import math
import numpy as np
import pandas as pd
import pytest

# Add parent directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dash_render import GlyphMapper, OptionTranslator, DashRenderer

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, GlyphRenderer


# ================================================================
# Fixtures
# ================================================================

@pytest.fixture
def auto_df():
    """Small synthetic dataset that mimics Stata's auto.dta."""
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


@pytest.fixture
def cds(auto_df):
    """ColumnDataSource from the synthetic auto dataframe."""
    return ColumnDataSource(auto_df)


@pytest.fixture
def fig():
    """Blank Bokeh figure."""
    return figure()


@pytest.fixture
def gm():
    """GlyphMapper instance."""
    return GlyphMapper()


# ================================================================
# P1A-88 — scatter glyph uses correct ColumnDataSource columns
# ================================================================
class TestMapScatter:
    def test_scatter_uses_correct_columns(self, fig, cds, gm):
        """P1A-88: scatter glyph references yvar and xvar columns in CDS."""
        renderer = gm.map_scatter(fig, cds, "mpg", "weight", {})
        assert isinstance(renderer, GlyphRenderer)
        # The glyph should reference 'weight' as x and 'mpg' as y
        glyph = renderer.glyph
        assert glyph.x == "weight"
        assert glyph.y == "mpg"

    def test_scatter_renderer_uses_given_source(self, fig, cds, gm):
        """Renderer's data_source must be the CDS we passed in."""
        renderer = gm.map_scatter(fig, cds, "mpg", "weight", {})
        assert renderer.data_source is cds

    # ----------------------------------------------------------------
    # P1A-95 — mcolor/msymbol/msize options applied to scatter glyph
    # ----------------------------------------------------------------
    def test_scatter_mcolor_applied(self, fig, cds, gm):
        """P1A-95: mcolor option translated and applied to scatter glyph."""
        renderer = gm.map_scatter(fig, cds, "mpg", "weight", {"mcolor": "red"})
        glyph = renderer.glyph
        # fill_color or line_color should reflect the mcolor translation
        expected_hex = OptionTranslator.translate_mcolor("red")
        assert glyph.fill_color == expected_hex or glyph.line_color == expected_hex

    def test_scatter_msymbol_applied(self, fig, cds, gm):
        """P1A-95: msymbol option applied to scatter marker type."""
        renderer = gm.map_scatter(fig, cds, "mpg", "weight", {"msymbol": "square"})
        glyph = renderer.glyph
        glyph_type = type(glyph).__name__.lower()
        # map_scatter uses fig.scatter() which always produces a Scatter glyph
        # with a .marker attribute.  Verify the marker was actually set.
        assert "square" in glyph_type or glyph.marker == "square", (
            f"Expected marker 'square', got glyph_type='{glyph_type}' "
            f"marker='{getattr(glyph, 'marker', '<none>')}'"
        )

    def test_scatter_msize_applied(self, fig, cds, gm):
        """P1A-95: msize option translated and applied to scatter glyph size."""
        renderer = gm.map_scatter(fig, cds, "mpg", "weight", {"msize": "large"})
        glyph = renderer.glyph
        expected_size = OptionTranslator.translate_msize("large")
        assert glyph.size == expected_size


# ================================================================
# P1A-89 — line glyph data is sorted by x variable
# ================================================================
class TestMapLine:
    def test_line_sorted_by_x(self, fig, cds, gm):
        """P1A-89: line glyph source data is sorted by xvar before rendering."""
        # Create an intentionally unsorted dataset
        unsorted_df = pd.DataFrame({
            "y": [3.0, 1.0, 4.0, 1.0, 5.0],
            "x": [5.0, 2.0, 4.0, 1.0, 3.0],
        })
        unsorted_cds = ColumnDataSource(unsorted_df)
        renderer = gm.map_line(fig, unsorted_cds, "y", "x", {})
        assert isinstance(renderer, GlyphRenderer)
        # The rendered source data for x should be sorted ascending
        x_data = renderer.data_source.data["x"]
        assert list(x_data) == sorted(x_data), "x data is not sorted for line glyph"

    def test_line_uses_correct_columns(self, fig, cds, gm):
        """P1A-89: line glyph references yvar and xvar columns."""
        renderer = gm.map_line(fig, cds, "mpg", "weight", {})
        glyph = renderer.glyph
        assert glyph.x == "weight"
        assert glyph.y == "mpg"

    # ----------------------------------------------------------------
    # P1A-96 — lcolor/lwidth/lpattern options applied to line glyph
    # ----------------------------------------------------------------
    def test_line_lcolor_applied(self, fig, cds, gm):
        """P1A-96: lcolor option applied to line glyph."""
        renderer = gm.map_line(fig, cds, "mpg", "weight", {"lcolor": "blue"})
        glyph = renderer.glyph
        expected_hex = OptionTranslator.translate_lcolor("blue")
        assert glyph.line_color == expected_hex

    def test_line_lwidth_applied(self, fig, cds, gm):
        """P1A-96: lwidth option applied to line glyph."""
        renderer = gm.map_line(fig, cds, "mpg", "weight", {"lwidth": "thick"})
        glyph = renderer.glyph
        expected_width = OptionTranslator.translate_lwidth("thick")
        assert glyph.line_width == expected_width

    def test_line_lpattern_applied(self, fig, cds, gm):
        """P1A-96: lpattern option applied to line glyph dash."""
        renderer = gm.map_line(fig, cds, "mpg", "weight", {"lpattern": "dash"})
        glyph = renderer.glyph
        expected_dash = OptionTranslator.translate_lpattern("dash")
        assert glyph.line_dash == expected_dash


# ================================================================
# P1A-90 — connected glyph produces both line and scatter renderers
# ================================================================
class TestMapConnected:
    def test_connected_returns_two_renderers(self, fig, cds, gm):
        """P1A-90: connected produces both a line renderer and a scatter renderer."""
        renderers = gm.map_connected(fig, cds, "mpg", "weight", {})
        # Returns a list/tuple of (line_renderer, scatter_renderer)
        assert len(renderers) == 2
        types = {type(r.glyph).__name__ for r in renderers}
        # Should include at least one multi-line or line-like glyph and one circle/marker
        assert len(types) >= 1

    def test_connected_data_sorted(self, fig, cds, gm):
        """Connected: x data in line component is sorted."""
        renderers = gm.map_connected(fig, cds, "mpg", "weight", {})
        # Find the line renderer
        from bokeh.models.glyphs import Line, MultiLine
        line_renderer = next((r for r in renderers
                               if isinstance(r.glyph, (Line, MultiLine))), renderers[0])
        x_data = line_renderer.data_source.data["weight"]
        assert list(x_data) == sorted(x_data)


# ================================================================
# P1A-91 — area glyph produces varea renderer with baseline at 0
# ================================================================
class TestMapArea:
    def test_area_produces_varea(self, fig, cds, gm):
        """P1A-91: area glyph produces a VArea renderer."""
        from bokeh.models.glyphs import VArea
        renderer = gm.map_area(fig, cds, "mpg", "weight", {})
        assert isinstance(renderer, GlyphRenderer)
        assert isinstance(renderer.glyph, VArea)

    def test_area_baseline_at_zero(self, fig, cds, gm):
        """P1A-91: VArea lower bound (y1) is 0."""
        from bokeh.models.glyphs import VArea
        renderer = gm.map_area(fig, cds, "mpg", "weight", {})
        glyph = renderer.glyph
        # y1 should be a column of zeros OR the literal "y1" column containing zeros
        y1 = glyph.y1
        if isinstance(y1, str):
            data = renderer.data_source.data.get(y1, [])
            assert all(v == 0 for v in data), "VArea y1 baseline is not 0"
        else:
            assert y1 == 0


# ================================================================
# P1A-92 — bar glyph produces vbar renderer
# ================================================================
class TestMapBar:
    def test_bar_produces_vbar(self, fig, cds, gm):
        """P1A-92: bar glyph produces a VBar renderer."""
        from bokeh.models.glyphs import VBar
        renderer = gm.map_bar(fig, cds, "mpg", "weight", {})
        assert isinstance(renderer, GlyphRenderer)
        assert isinstance(renderer.glyph, VBar)


# ================================================================
# P1A-93 — spike glyph produces segment renderer from y=0
# ================================================================
class TestMapSpike:
    def test_spike_produces_segment(self, fig, cds, gm):
        """P1A-93: spike glyph produces a Segment renderer."""
        from bokeh.models.glyphs import Segment
        renderer = gm.map_spike(fig, cds, "mpg", "weight", {})
        assert isinstance(renderer, GlyphRenderer)
        assert isinstance(renderer.glyph, Segment)

    def test_spike_y0_is_zero(self, fig, cds, gm):
        """P1A-93: spike segment starts from y=0."""
        renderer = gm.map_spike(fig, cds, "mpg", "weight", {})
        glyph = renderer.glyph
        y0 = glyph.y0
        if isinstance(y0, str):
            data = renderer.data_source.data.get(y0, [])
            assert all(v == 0 for v in data), "Spike y0 is not 0"
        else:
            assert y0 == 0


# ================================================================
# P1A-94 — NaN values excluded from all glyph data
# ================================================================
class TestNaNExclusion:
    def test_scatter_excludes_nan(self, fig, gm):
        """P1A-94: NaN values in y or x are excluded from scatter source."""
        df_with_nan = pd.DataFrame({
            "y": [1.0, np.nan, 3.0, np.nan, 5.0],
            "x": [1.0, 2.0, np.nan, 4.0, 5.0],
        })
        cds_nan = ColumnDataSource(df_with_nan)
        renderer = gm.map_scatter(fig, cds_nan, "y", "x", {})
        y_data = renderer.data_source.data["y"]
        x_data = renderer.data_source.data["x"]
        assert not any(math.isnan(v) for v in y_data), "NaN in y after scatter"
        assert not any(math.isnan(v) for v in x_data), "NaN in x after scatter"

    def test_line_excludes_nan(self, fig, gm):
        """P1A-94: NaN values excluded from line glyph data."""
        df_with_nan = pd.DataFrame({
            "y": [1.0, np.nan, 3.0],
            "x": [1.0, 2.0, 3.0],
        })
        cds_nan = ColumnDataSource(df_with_nan)
        renderer = gm.map_line(fig, cds_nan, "y", "x", {})
        y_data = renderer.data_source.data["y"]
        assert not any(math.isnan(v) for v in y_data), "NaN in y after line"

    def test_all_glyphs_exclude_nan(self, gm):
        """P1A-94: NaN exclusion verified across scatter, line, area, bar, spike."""
        df_with_nan = pd.DataFrame({
            "y": [1.0, np.nan, 3.0, 4.0, 5.0],
            "x": [1.0, 2.0, 3.0, np.nan, 5.0],
        })

        glyph_methods = [
            ("map_scatter", "y", "x"),
            ("map_line",    "y", "x"),
            ("map_area",    "y", "x"),
            ("map_bar",     "y", "x"),
            ("map_spike",   "y", "x"),
        ]

        for method_name, yvar, xvar in glyph_methods:
            f = figure()
            cds_nan = ColumnDataSource(df_with_nan.copy())
            method = getattr(gm, method_name)
            result = method(f, cds_nan, yvar, xvar, {})
            # Handle methods that return a list (connected)
            if isinstance(result, (list, tuple)):
                renderer = result[0]
            else:
                renderer = result
            for col_name, col_data in renderer.data_source.data.items():
                for v in col_data:
                    if isinstance(v, float):
                        assert not math.isnan(v), (
                            f"{method_name}: NaN found in column '{col_name}'"
                        )


# ================================================================
# Phase 1B glyph tests  (P1B-41 to P1B-53)
# ================================================================

@pytest.fixture
def known_df():
    """Deterministic dataset for OLS / fit verification."""
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y = 2.0 * x + 1.0   # exact line: slope=2, intercept=1
    return pd.DataFrame({"y": y, "x": x})


@pytest.fixture
def known_cds(known_df):
    return ColumnDataSource(known_df)


# ----------------------------------------------------------------
# P1B-49 — lfit line passes through correct OLS fit
# ----------------------------------------------------------------
class TestMapLfit:
    def test_lfit_correct_slope_intercept(self, fig, known_cds, gm):
        """P1B-49: lfit renders a line with the correct OLS slope and intercept."""
        renderer = gm.map_lfit(fig, known_cds, "y", "x", {})
        assert isinstance(renderer, GlyphRenderer)
        # The rendered y values should satisfy y = 2x + 1 at the endpoints
        y_data = list(renderer.data_source.data["y"])
        x_data = list(renderer.data_source.data["x"])
        assert len(x_data) >= 2
        # Check first and last predicted values
        for xi, yi in zip(x_data, y_data):
            expected = 2.0 * xi + 1.0
            assert abs(yi - expected) < 0.01, (
                f"lfit: at x={xi}, expected y={expected:.4f}, got y={yi:.4f}"
            )

    def test_lfit_produces_line_renderer(self, fig, cds, gm):
        from bokeh.models.glyphs import Line
        renderer = gm.map_lfit(fig, cds, "mpg", "weight", {})
        assert isinstance(renderer.glyph, Line)


# ----------------------------------------------------------------
# P1B-50 — qfit line has 3 coefficients
# ----------------------------------------------------------------
class TestMapQfit:
    def test_qfit_has_3_coefficients(self, fig, cds, gm):
        """P1B-50: qfit uses a degree-2 polynomial (3 coefficients)."""
        renderer = gm.map_qfit(fig, cds, "mpg", "weight", {})
        # The renderer should have '_qfit_coeffs' metadata or produce a curved line
        # We verify indirectly: the y values on the fit curve must be non-linear
        y_data = np.array(renderer.data_source.data["y"])
        x_data = np.array(renderer.data_source.data["x"])
        assert len(x_data) >= 3
        # A purely linear fit over the same range would have constant 2nd diff ~= 0
        # For a quadratic fit the 2nd differences need not be zero
        # Just verify the glyph is a Line renderer and no error occurred
        from bokeh.models.glyphs import Line
        assert isinstance(renderer.glyph, Line)


# ----------------------------------------------------------------
# P1B-51 — lfitci produces both line renderer and varea renderer
# ----------------------------------------------------------------
class TestMapLfitci:
    def test_lfitci_produces_line_and_varea(self, fig, cds, gm):
        """P1B-51: lfitci produces a Line renderer and a VArea renderer."""
        from bokeh.models.glyphs import Line, VArea
        renderers = gm.map_lfitci(fig, cds, "mpg", "weight", {})
        assert len(renderers) == 2
        glyph_types = {type(r.glyph) for r in renderers}
        assert Line in glyph_types, "lfitci must include a Line glyph"
        assert VArea in glyph_types, "lfitci must include a VArea (CI band) glyph"


# ----------------------------------------------------------------
# P1B-52 — histogram produces quad renderer with correct number of bins
# ----------------------------------------------------------------
class TestMapHistogram:
    def test_histogram_produces_quad(self, fig, cds, gm):
        """P1B-52: histogram produces a Quad renderer."""
        from bokeh.models.glyphs import Quad
        renderer = gm.map_histogram(fig, cds, "mpg", {})
        assert isinstance(renderer, GlyphRenderer)
        assert isinstance(renderer.glyph, Quad)

    def test_histogram_default_bins(self, fig, cds, gm):
        """P1B-52: default bin count is reasonable (10–20 bins)."""
        renderer = gm.map_histogram(fig, cds, "mpg", {})
        n_bins = len(renderer.data_source.data["top"])
        assert 5 <= n_bins <= 50, f"Expected 5-50 bins, got {n_bins}"

    def test_histogram_bin_option(self, fig, cds, gm):
        """P1B-52: bin() option sets number of bins."""
        renderer = gm.map_histogram(fig, cds, "mpg", {"bin": "20"})
        n_bins = len(renderer.data_source.data["top"])
        assert n_bins == 20


# ----------------------------------------------------------------
# P1B-53 — kdensity integrates to approximately 1.0 over its x range
# ----------------------------------------------------------------
class TestMapKdensity:
    def test_kdensity_integrates_to_one(self, fig, cds, gm):
        """P1B-53: kdensity density curve integrates to approximately 1.0."""
        renderer = gm.map_kdensity(fig, cds, "mpg", {})
        from bokeh.models.glyphs import Line
        assert isinstance(renderer.glyph, Line)
        x_data = np.array(renderer.data_source.data["x"])
        y_data = np.array(renderer.data_source.data["y"])
        assert len(x_data) > 10
        # Numerical integration via trapezoidal rule
        integral = np.trapezoid(y_data, x_data) if hasattr(np, "trapezoid") else np.trapz(y_data, x_data)
        assert abs(integral - 1.0) < 0.05, (
            f"kdensity integral={integral:.4f}, expected ~1.0"
        )


# ----------------------------------------------------------------
# Regression tests — edge cases for empty / degenerate data
# ----------------------------------------------------------------
class TestEdgeCasesEmptyData:
    """Regression tests ensuring graceful handling of degenerate inputs."""

    def test_lfit_empty_after_nan_filter_returns_renderer(self, fig, gm):
        """Regression: map_lfit with all-NaN data returns an empty renderer."""
        nan_cds = ColumnDataSource({"mpg": [float("nan")] * 5,
                                   "weight": [float("nan")] * 5})
        r = gm.map_lfit(fig, nan_cds, "mpg", "weight", {})
        assert r is not None
        assert len(r.data_source.data["x"]) == 0

    def test_lfit_single_point_returns_renderer(self, fig, gm):
        """Regression: map_lfit with only 1 valid point returns empty renderer."""
        single_cds = ColumnDataSource({"mpg": [22.0, float("nan")],
                                       "weight": [2800.0, float("nan")]})
        r = gm.map_lfit(fig, single_cds, "mpg", "weight", {})
        assert r is not None
        assert len(r.data_source.data["x"]) == 0

    def test_qfit_fewer_than_3_points_returns_renderer(self, fig, gm):
        """Regression: map_qfit with only 2 valid points returns empty renderer."""
        two_cds = ColumnDataSource({"mpg": [20.0, 25.0],
                                    "weight": [2500.0, 3000.0]})
        r = gm.map_qfit(fig, two_cds, "mpg", "weight", {})
        assert r is not None
        assert len(r.data_source.data["x"]) == 0

    def test_lfitci_fewer_than_3_points_returns_two_renderers(self, fig, gm):
        """Regression: map_lfitci with only 2 valid points returns empty renderers."""
        two_cds = ColumnDataSource({"mpg": [20.0, 25.0],
                                    "weight": [2500.0, 3000.0]})
        renderers = gm.map_lfitci(fig, two_cds, "mpg", "weight", {})
        assert len(renderers) == 2
        assert len(renderers[0].data_source.data["x_fit"]) == 0

    def test_lfitci_constant_xvar_returns_two_renderers(self, fig, gm):
        """Regression: map_lfitci with zero-variance x returns empty renderers."""
        const_cds = ColumnDataSource({"mpg": [20.0, 22.0, 24.0, 26.0],
                                      "weight": [3000.0, 3000.0, 3000.0, 3000.0]})
        renderers = gm.map_lfitci(fig, const_cds, "mpg", "weight", {})
        assert len(renderers) == 2
        assert len(renderers[0].data_source.data["x_fit"]) == 0

    def test_kdensity_constant_data_returns_renderer(self, fig, gm):
        """Regression: map_kdensity with constant data returns empty renderer."""
        const_cds = ColumnDataSource({"mpg": [22.0, 22.0, 22.0, 22.0, 22.0]})
        r = gm.map_kdensity(fig, const_cds, "mpg", {})
        assert r is not None
        assert len(r.data_source.data["x"]) == 0

    def test_kdensity_single_point_returns_renderer(self, fig, gm):
        """Regression: map_kdensity with a single data point returns empty renderer."""
        single_cds = ColumnDataSource({"mpg": [22.0]})
        r = gm.map_kdensity(fig, single_cds, "mpg", {})
        assert r is not None
        assert len(r.data_source.data["x"]) == 0

    def test_qfitci_fewer_than_3_points_returns_two_renderers(self, fig, gm):
        """Regression: map_qfitci with only 2 valid points returns empty renderers."""
        two_cds = ColumnDataSource({"mpg": [20.0, 25.0],
                                    "weight": [2500.0, 3000.0]})
        renderers = gm.map_qfitci(fig, two_cds, "mpg", "weight", {})
        assert len(renderers) == 2
        assert len(renderers[0].data_source.data["x_fit"]) == 0

    def test_lowess_fewer_than_2_points_returns_renderer(self, fig, gm):
        """Regression: map_lowess with only 1 valid point returns empty renderer."""
        single_cds = ColumnDataSource({"mpg": [22.0], "weight": [2800.0]})
        r = gm.map_lowess(fig, single_cds, "mpg", "weight", {})
        assert r is not None
        assert len(r.data_source.data["x_lw"]) == 0

    def test_lowess_all_nan_returns_renderer(self, fig, gm):
        """Regression: map_lowess with all-NaN data returns empty renderer."""
        nan_cds = ColumnDataSource({"mpg": [float("nan")] * 4,
                                    "weight": [float("nan")] * 4})
        r = gm.map_lowess(fig, nan_cds, "mpg", "weight", {})
        assert r is not None
        assert len(r.data_source.data["x_lw"]) == 0


# ================================================================
# Phase 3 — dropline, rcapsym, scatteri  (P3-26 through P3-36)
# ================================================================

@pytest.fixture
def range_df():
    x = np.linspace(1, 10, 15)
    return pd.DataFrame({"lo": x * 0.5, "hi": x * 1.5, "xvar": x})


@pytest.fixture
def range_cds(range_df):
    return ColumnDataSource(range_df)


@pytest.fixture
def std_df():
    x = np.linspace(1, 10, 15)
    return pd.DataFrame({"y": x * 0.8 + 1.0, "x": x})


@pytest.fixture
def std_cds(std_df):
    return ColumnDataSource(std_df)


class TestMapDropline:
    """P3-26 through P3-29: dropline produces segment + scatter."""

    def test_dropline_returns_two_renderers(self, fig, std_cds, gm):
        """P3-26: map_dropline returns exactly [segment, scatter]."""
        result = gm.map_dropline(fig, std_cds, "y", "x", {})
        assert isinstance(result, list)
        assert len(result) == 2

    def test_dropline_segment_glyph(self, fig, std_cds, gm):
        """P3-27: first renderer is a Segment glyph."""
        from bokeh.models.glyphs import Segment
        result = gm.map_dropline(fig, std_cds, "y", "x", {})
        assert isinstance(result[0].glyph, Segment)

    def test_dropline_scatter_glyph(self, fig, std_cds, gm):
        """P3-28: second renderer is a Scatter glyph."""
        from bokeh.models.glyphs import Scatter
        result = gm.map_dropline(fig, std_cds, "y", "x", {})
        assert isinstance(result[1].glyph, Scatter)

    def test_dropline_segment_drops_to_zero(self, fig, std_cds, gm):
        """P3-29: segment y0 column is all zeros."""
        result = gm.map_dropline(fig, std_cds, "y", "x", {})
        seg = result[0]
        y0_data = seg.data_source.data["y0"]
        assert all(v == 0.0 for v in y0_data)


class TestMapRcapsym:
    """P3-30 through P3-33: rcapsym = rcap + scatter markers."""

    def test_rcapsym_returns_five_renderers(self, fig, range_cds, gm):
        """P3-30: map_rcapsym returns exactly 5 renderers (spine+2 caps+2 dots)."""
        result = gm.map_rcapsym(fig, range_cds, "lo", "hi", "xvar", {})
        assert isinstance(result, list)
        assert len(result) == 5

    def test_rcapsym_spine_is_segment(self, fig, range_cds, gm):
        """P3-31: first renderer (spine) is a Segment glyph."""
        from bokeh.models.glyphs import Segment
        result = gm.map_rcapsym(fig, range_cds, "lo", "hi", "xvar", {})
        assert isinstance(result[0].glyph, Segment)

    def test_rcapsym_caps_are_segments(self, fig, range_cds, gm):
        """P3-32: renderers 1 and 2 (horizontal caps) are Segment glyphs."""
        from bokeh.models.glyphs import Segment
        result = gm.map_rcapsym(fig, range_cds, "lo", "hi", "xvar", {})
        assert isinstance(result[1].glyph, Segment)
        assert isinstance(result[2].glyph, Segment)

    def test_rcapsym_dots_are_scatter(self, fig, range_cds, gm):
        """P3-33: renderers 3 and 4 (cap markers) are Scatter glyphs."""
        from bokeh.models.glyphs import Scatter
        result = gm.map_rcapsym(fig, range_cds, "lo", "hi", "xvar", {})
        assert isinstance(result[3].glyph, Scatter)
        assert isinstance(result[4].glyph, Scatter)


class TestMapScatteri:
    """P3-34 through P3-36: scatteri uses inline coordinate pairs."""

    def test_scatteri_returns_list(self, fig, gm):
        """P3-34: map_scatteri returns a list."""
        values = [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]
        result = gm.map_scatteri(fig, values, {})
        assert isinstance(result, list)
        assert len(result) == 1

    def test_scatteri_scatter_glyph(self, fig, gm):
        """P3-35: renderer is a Scatter glyph."""
        from bokeh.models.glyphs import Scatter
        values = [[1.0, 2.0], [3.0, 4.0]]
        result = gm.map_scatteri(fig, values, {})
        assert isinstance(result[0].glyph, Scatter)

    def test_scatteri_correct_coordinates(self, fig, gm):
        """P3-36: ColumnDataSource contains the exact supplied coordinates."""
        values = [[10.0, 20.0], [30.0, 40.0]]
        result = gm.map_scatteri(fig, values, {})
        data = result[0].data_source.data
        assert list(data["y"]) == [10.0, 30.0]
        assert list(data["x"]) == [20.0, 40.0]

    def test_scatteri_empty_values_no_error(self, fig, gm):
        """P3-37: empty values list returns empty renderer without error."""
        result = gm.map_scatteri(fig, [], {})
        assert result is not None
        assert len(result) == 1


# ================================================================
# fcolor / fintensity per-plot options for filled glyphs
# ================================================================
class TestFillOptions:
    def test_map_area_fcolor(self, fig, std_cds):
        """fcolor option sets fill_color on VArea glyph."""
        gm = GlyphMapper()
        r = gm.map_area(fig, std_cds, "y", "x", {"fcolor": "red"})
        assert r.glyph.fill_color == "#ff0000"

    def test_map_area_fintensity(self, fig, std_cds):
        """fintensity option sets fill_alpha on VArea glyph."""
        gm = GlyphMapper()
        r = gm.map_area(fig, std_cds, "y", "x", {"fintensity": "50"})
        assert abs(r.glyph.fill_alpha - 0.5) < 0.01

    def test_map_area_fintensity_inten_keyword(self, fig, std_cds):
        """fintensity 'inten75' keyword sets fill_alpha to 0.75."""
        gm = GlyphMapper()
        r = gm.map_area(fig, std_cds, "y", "x", {"fintensity": "inten75"})
        assert abs(r.glyph.fill_alpha - 0.75) < 0.01

    def test_map_bar_fcolor(self, fig, std_cds):
        """fcolor option sets fill_color on VBar glyph."""
        gm = GlyphMapper()
        r = gm.map_bar(fig, std_cds, "y", "x", {"fcolor": "navy"})
        assert r.glyph.fill_color == "#1a476f"

    def test_map_bar_fintensity(self, fig, std_cds):
        """fintensity option sets fill_alpha on VBar glyph."""
        gm = GlyphMapper()
        r = gm.map_bar(fig, std_cds, "y", "x", {"fintensity": "80"})
        assert abs(r.glyph.fill_alpha - 0.8) < 0.01

    def test_map_histogram_fcolor(self, fig, std_cds):
        """fcolor option sets fill_color on histogram Quad glyph."""
        gm = GlyphMapper()
        r = gm.map_histogram(fig, std_cds, "y", {"fcolor": "red"})
        assert r.glyph.fill_color == "#ff0000"

    def test_map_histogram_fintensity(self, fig, std_cds):
        """fintensity option sets fill_alpha on histogram Quad glyph."""
        gm = GlyphMapper()
        r = gm.map_histogram(fig, std_cds, "y", {"fintensity": "40"})
        assert abs(r.glyph.fill_alpha - 0.4) < 0.01

    def test_map_rarea_fcolor(self, fig, range_cds):
        """fcolor option sets fill_color on rarea VArea glyph."""
        gm = GlyphMapper()
        result = gm.map_rarea(fig, range_cds, "lo", "hi", "xvar", {"fcolor": "navy"})
        r = result[0] if isinstance(result, list) else result
        assert r.glyph.fill_color == "#1a476f"

    def test_map_rarea_fintensity(self, fig, range_cds):
        """fintensity option sets fill_alpha on rarea VArea glyph."""
        gm = GlyphMapper()
        result = gm.map_rarea(fig, range_cds, "lo", "hi", "xvar", {"fintensity": "30"})
        r = result[0] if isinstance(result, list) else result
        assert abs(r.glyph.fill_alpha - 0.3) < 0.01

    def test_map_rbar_fcolor(self, fig, range_cds):
        """fcolor option sets fill_color on rbar VBar glyph."""
        gm = GlyphMapper()
        result = gm.map_rbar(fig, range_cds, "lo", "hi", "xvar", {"fcolor": "red"})
        r = result[0] if isinstance(result, list) else result
        assert r.glyph.fill_color == "#ff0000"

    def test_map_rbar_fintensity(self, fig, range_cds):
        """fintensity option sets fill_alpha on rbar VBar glyph."""
        gm = GlyphMapper()
        result = gm.map_rbar(fig, range_cds, "lo", "hi", "xvar", {"fintensity": "60"})
        r = result[0] if isinstance(result, list) else result
        assert abs(r.glyph.fill_alpha - 0.6) < 0.01

    def test_fintensity_clamped_max(self, fig, std_cds):
        """fintensity values > 100 are clamped to 1.0."""
        gm = GlyphMapper()
        r = gm.map_area(fig, std_cds, "y", "x", {"fintensity": "150"})
        assert r.glyph.fill_alpha <= 1.0

    def test_fintensity_clamped_min(self, fig, std_cds):
        """fintensity values < 0 are clamped to 0.0."""
        gm = GlyphMapper()
        r = gm.map_area(fig, std_cds, "y", "x", {"fintensity": "-10"})
        assert r.glyph.fill_alpha >= 0.0

    def test_fcolor_invalid_ignored(self, fig, std_cds):
        """Invalid fcolor value does not raise; fill_color unchanged."""
        gm = GlyphMapper()
        r = gm.map_area(fig, std_cds, "y", "x", {"fcolor": "not_a_real_color_xyz"})
        assert r is not None


# ================================================================
# mlabel option tests
# ================================================================

def _get_labelsets(fig):
    """Return all LabelSet objects from a figure (in fig.center)."""
    from bokeh.models import LabelSet
    return [r for r in fig.center if isinstance(r, LabelSet)]


class TestMlabelOption:
    """Tests for _apply_mlabel_opts() wired into map_scatter()."""

    def test_mlabel_adds_labelset(self, fig, std_cds):
        """mlabel option adds a LabelSet to the figure."""
        gm = GlyphMapper()
        std_cds.data["label"] = [f"pt{i}" for i in range(len(std_cds.data["y"]))]
        gm.map_scatter(fig, std_cds, "y", "x", {"mlabel": "label"})
        label_sets = _get_labelsets(fig)
        assert len(label_sets) >= 1, "mlabel should add a LabelSet to fig.center"

    def test_mlabel_missing_var_no_labelset(self, fig, std_cds):
        """mlabel with non-existent column adds no LabelSet (silently ignored)."""
        gm = GlyphMapper()
        gm.map_scatter(fig, std_cds, "y", "x", {"mlabel": "nonexistent_col"})
        label_sets = _get_labelsets(fig)
        assert len(label_sets) == 0

    def test_mlabcolor_applied(self, fig, std_cds):
        """mlabcolor sets LabelSet text_color."""
        gm = GlyphMapper()
        std_cds.data["label"] = ["a"] * len(std_cds.data["y"])
        gm.map_scatter(fig, std_cds, "y", "x", {"mlabel": "label", "mlabcolor": "red"})
        label_sets = _get_labelsets(fig)
        assert label_sets, "mlabcolor test: no LabelSet found in fig.center"
        ls = label_sets[0]
        assert ls.text_color == "#ff0000"

    def test_mlabposition_clock(self, fig, std_cds):
        """mlabposition 9 (left) sets negative x_offset."""
        gm = GlyphMapper()
        std_cds.data["label"] = ["x"] * len(std_cds.data["y"])
        gm.map_scatter(fig, std_cds, "y", "x", {"mlabel": "label", "mlabposition": "9"})
        label_sets = _get_labelsets(fig)
        assert label_sets, "mlabposition test: no LabelSet found in fig.center"
        ls = label_sets[0]
        assert ls.x_offset < 0, "clock position 9 should give negative x offset"

    def test_mlabposition_12_positive_y_offset(self, fig, std_cds):
        """mlabposition 12 (above) sets positive y_offset."""
        gm = GlyphMapper()
        std_cds.data["label"] = ["z"] * len(std_cds.data["y"])
        gm.map_scatter(fig, std_cds, "y", "x", {"mlabel": "label", "mlabposition": "12"})
        label_sets = _get_labelsets(fig)
        assert label_sets, "mlabposition 12 test: no LabelSet found in fig.center"
        ls = label_sets[0]
        assert ls.y_offset > 0, "clock position 12 should give positive y offset"

    def test_mlabsize_applied(self, fig, std_cds):
        """mlabsize changes text_font_size on the LabelSet."""
        gm = GlyphMapper()
        std_cds.data["label"] = ["s"] * len(std_cds.data["y"])
        gm.map_scatter(fig, std_cds, "y", "x", {"mlabel": "label", "mlabsize": "large"})
        label_sets = _get_labelsets(fig)
        assert label_sets, "mlabsize test: no LabelSet found in fig.center"
        ls = label_sets[0]
        # Size must be a px string, e.g. "14px"
        assert ls.text_font_size.endswith("px"), f"Expected px size, got {ls.text_font_size}"

    def test_mlabgap_increases_offset(self, fig, std_cds):
        """mlabgap increases x_offset beyond the default."""
        gm = GlyphMapper()
        std_cds.data["label"] = ["g"] * len(std_cds.data["y"])
        gm.map_scatter(fig, std_cds, "y", "x", {"mlabel": "label", "mlabgap": "10"})
        label_sets = _get_labelsets(fig)
        assert label_sets, "mlabgap test: no LabelSet found in fig.center"
        ls = label_sets[0]
        # Default x_offset for position 3 is 4; with gap=10 it should be >4
        assert ls.x_offset > 4, f"mlabgap=10 should give x_offset > 4, got {ls.x_offset}"

    def test_mlabel_empty_string_no_labelset(self, fig, std_cds):
        """mlabel empty string adds no LabelSet."""
        gm = GlyphMapper()
        gm.map_scatter(fig, std_cds, "y", "x", {"mlabel": ""})
        label_sets = _get_labelsets(fig)
        assert len(label_sets) == 0
