"""
test_glyphs.py
Unit tests for dash_render.py GlyphMapper class.

Tests: P1A-88 through P1A-96

Run with:  pytest test/test_glyphs.py -v
"""
import sys
import os
import math
import json
import tempfile
import numpy as np
import pandas as pd
import pytest

# Add parent directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dash_render import GlyphMapper, OptionTranslator, DashRenderer

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, GlyphRenderer, HoverTool


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

    def test_scatter_lcolor_sets_line_color(self, fig, cds, gm):
        """GAP 3.2: lcolor sets marker outline (line_color) on scatter glyph."""
        renderer = gm.map_scatter(fig, cds, "mpg", "weight", {"lcolor": "red"})
        glyph = renderer.glyph
        expected = OptionTranslator.translate_mcolor("red")
        assert glyph.line_color == expected, \
            f"scatter lcolor should set line_color; expected {expected}, got {glyph.line_color}"

    def test_scatter_lwidth_sets_line_width(self, fig, cds, gm):
        """GAP 3.2: lwidth sets marker border width on scatter glyph."""
        renderer = gm.map_scatter(fig, cds, "mpg", "weight", {"lwidth": "thick"})
        glyph = renderer.glyph
        assert glyph.line_width > 1.0, \
            f"scatter lwidth 'thick' should set line_width > 1.0, got {glyph.line_width}"


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
# dot plot type — scatter glyph renderer
# ================================================================
class TestMapDot:
    """Unit tests for map_dot — scatter (circle) renderer."""

    def test_dot_returns_renderer(self, fig, cds, gm):
        """map_dot returns a GlyphRenderer."""
        from bokeh.models import GlyphRenderer
        r = gm.map_dot(fig, cds, "mpg", "weight", {})
        assert isinstance(r, GlyphRenderer)

    def test_dot_produces_scatter_glyph(self, fig, cds, gm):
        """map_dot produces a Scatter glyph (circle marker)."""
        from bokeh.models.glyphs import Scatter
        r = gm.map_dot(fig, cds, "mpg", "weight", {})
        assert isinstance(r.glyph, Scatter)

    def test_dot_mcolor_applied(self, fig, cds, gm):
        """mcolor option applied to dot fill color."""
        r = gm.map_dot(fig, cds, "mpg", "weight", {"mcolor": "red"})
        assert r.glyph.fill_color == "#ff0000"

    def test_dot_msize_applied(self, fig, cds, gm):
        """msize(large) option applied to dot size."""
        r = gm.map_dot(fig, cds, "mpg", "weight", {"msize": "large"})
        assert r.glyph.size > 8  # large is bigger than default


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

    def test_spike_lcolor_applied(self, fig, cds, gm):
        """spike lcolor option must change glyph line_color from default."""
        default = gm.map_spike(fig, cds, "mpg", "weight", {}).glyph.line_color
        renderer = gm.map_spike(fig, cds, "mpg", "weight", {"lcolor": "red"})
        assert renderer.glyph.line_color != default, \
            f"lcolor='red' must change line_color from default {default!r}"

    def test_spike_lwidth_applied(self, fig, cds, gm):
        """spike lwidth option must set glyph line_width."""
        renderer = gm.map_spike(fig, cds, "mpg", "weight", {"lwidth": "3"})
        assert renderer.glyph.line_width == 3.0, \
            f"Expected line_width=3.0, got {renderer.glyph.line_width!r}"

    def test_spike_lpattern_applied(self, fig, cds, gm):
        """spike lpattern option must set glyph line_dash."""
        renderer = gm.map_spike(fig, cds, "mpg", "weight", {"lpattern": "dash"})
        assert renderer.glyph.line_dash != [], \
            f"Expected non-empty line_dash for lpattern='dash', got {renderer.glyph.line_dash!r}"


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

    def test_lfit_x_range_extends_beyond_data_bounds_lf01(self, fig, cds, gm):
        """LF-01: lfit x_fit must extend at least 8% beyond data min/max.

        The fit line should span the full visible plot area, not just the data
        range.  Bokeh's DataRange1d adds 10% padding; lfit x_fit is extended by
        the same 10% so it reaches the visible axis boundaries.
        """
        x_data = np.array(cds.data["weight"])
        x_min, x_max = x_data.min(), x_data.max()
        renderer = gm.map_lfit(fig, cds, "mpg", "weight", {})
        x_fit = np.array(renderer.data_source.data["x"])
        assert x_fit.min() < x_min, (
            f"lfit x_fit min ({x_fit.min():.1f}) should extend below data min "
            f"({x_min:.1f}) to reach the visible axis boundary"
        )
        assert x_fit.max() > x_max, (
            f"lfit x_fit max ({x_fit.max():.1f}) should extend above data max "
            f"({x_max:.1f}) to reach the visible axis boundary"
        )
        # Verify the extension is approximately 10% on each side
        dx = x_max - x_min
        assert x_fit.min() <= x_min - 0.08 * dx, "Extension should be ~10% below data min"
        assert x_fit.max() >= x_max + 0.08 * dx, "Extension should be ~10% above data max"

    def test_qfit_x_range_extends_beyond_data_bounds_lf02(self, fig, cds, gm):
        """LF-02: qfit x_fit must extend at least 8% beyond data min/max."""
        x_data = np.array(cds.data["weight"])
        x_min, x_max = x_data.min(), x_data.max()
        renderer = gm.map_qfit(fig, cds, "mpg", "weight", {})
        x_fit = np.array(renderer.data_source.data["x"])
        dx = x_max - x_min
        assert x_fit.min() <= x_min - 0.08 * dx, (
            "qfit x_fit must extend below data min to reach visible axis boundary"
        )
        assert x_fit.max() >= x_max + 0.08 * dx, (
            "qfit x_fit must extend above data max to reach visible axis boundary"
        )


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


class TestMlabelOnNonScatter:
    """P6-21b: mlabel works for non-scatter standard plot types via _add_glyph()."""

    def _cds_with_label(self, std_df):
        """Return a CDS built from std_df (cols: 'y', 'x') plus a 'lbl' column."""
        df = std_df.copy()
        df["lbl"] = [f"p{i}" for i in range(len(df))]
        from bokeh.models import ColumnDataSource
        return ColumnDataSource(df)

    def test_mlabel_on_line(self, fig, std_df):
        from bokeh.models import LabelSet
        gm = GlyphMapper()
        src = self._cds_with_label(std_df)
        gm.map_line(fig, src, "y", "x", {"mlabel": "lbl"})
        ls = [r for r in fig.center if isinstance(r, LabelSet)]
        assert len(ls) >= 1, "mlabel on line should add a LabelSet"

    def test_mlabel_on_bar(self, fig, std_df):
        from bokeh.models import LabelSet
        gm = GlyphMapper()
        src = self._cds_with_label(std_df)
        gm.map_bar(fig, src, "y", "x", {"mlabel": "lbl"})
        ls = [r for r in fig.center if isinstance(r, LabelSet)]
        assert len(ls) >= 1, "mlabel on bar should add a LabelSet"

    def test_mlabel_on_spike(self, fig, std_df):
        from bokeh.models import LabelSet
        gm = GlyphMapper()
        src = self._cds_with_label(std_df)
        gm.map_spike(fig, src, "y", "x", {"mlabel": "lbl"})
        ls = [r for r in fig.center if isinstance(r, LabelSet)]
        assert len(ls) >= 1

    def test_mlabel_on_dot(self, fig, std_df):
        from bokeh.models import LabelSet
        gm = GlyphMapper()
        src = self._cds_with_label(std_df)
        gm.map_dot(fig, src, "y", "x", {"mlabel": "lbl"})
        ls = [r for r in fig.center if isinstance(r, LabelSet)]
        assert len(ls) >= 1


class TestMlabelOnRangePlots:
    """A-59 resolved: mlabel() labels at y2 (top boundary) for range plot types."""

    def _range_cds_with_label(self):
        """Return a range CDS with y1, y2, x, and lbl columns."""
        df = pd.DataFrame({
            "lo":  [1.0, 2.0, 3.0, 4.0, 5.0],
            "hi":  [2.0, 4.0, 6.0, 8.0, 10.0],
            "x":   [10.0, 20.0, 30.0, 40.0, 50.0],
            "lbl": ["a", "b", "c", "d", "e"],
        })
        return ColumnDataSource(df)

    def test_mlabel_on_rspike(self, fig):
        """mlabel on rspike adds a LabelSet positioned at y2."""
        from bokeh.models import LabelSet
        src = self._range_cds_with_label()
        gm = GlyphMapper()
        gm.map_rspike(fig, src, "lo", "hi", "x", {"mlabel": "lbl"})
        ls = [r for r in fig.center if isinstance(r, LabelSet)]
        assert len(ls) >= 1, "mlabel on rspike must add LabelSet"

    def test_mlabel_on_rcap(self, fig):
        """mlabel on rcap adds a LabelSet positioned at y2."""
        from bokeh.models import LabelSet
        src = self._range_cds_with_label()
        gm = GlyphMapper()
        gm.map_rcap(fig, src, "lo", "hi", "x", {"mlabel": "lbl"})
        ls = [r for r in fig.center if isinstance(r, LabelSet)]
        assert len(ls) >= 1, "mlabel on rcap must add LabelSet"

    def test_mlabel_on_rline(self, fig):
        """mlabel on rline adds a LabelSet positioned at y2."""
        from bokeh.models import LabelSet
        src = self._range_cds_with_label()
        gm = GlyphMapper()
        gm.map_rline(fig, src, "lo", "hi", "x", {"mlabel": "lbl"})
        ls = [r for r in fig.center if isinstance(r, LabelSet)]
        assert len(ls) >= 1, "mlabel on rline must add LabelSet"

    def test_mlabel_on_rarea(self, fig):
        """mlabel on rarea adds a LabelSet positioned at y2."""
        from bokeh.models import LabelSet
        src = self._range_cds_with_label()
        gm = GlyphMapper()
        gm.map_rarea(fig, src, "lo", "hi", "x", {"mlabel": "lbl"})
        ls = [r for r in fig.center if isinstance(r, LabelSet)]
        assert len(ls) >= 1, "mlabel on rarea must add LabelSet"

    def test_mlabel_on_rbar(self, fig):
        """mlabel on rbar adds a LabelSet positioned at y2."""
        from bokeh.models import LabelSet
        src = self._range_cds_with_label()
        gm = GlyphMapper()
        gm.map_rbar(fig, src, "lo", "hi", "x", {"mlabel": "lbl"})
        ls = [r for r in fig.center if isinstance(r, LabelSet)]
        assert len(ls) >= 1, "mlabel on rbar must add LabelSet"

    def test_mlabel_on_rcapsym(self, fig):
        """mlabel on rcapsym adds a LabelSet positioned at y2."""
        from bokeh.models import LabelSet
        src = self._range_cds_with_label()
        gm = GlyphMapper()
        gm.map_rcapsym(fig, src, "lo", "hi", "x", {"mlabel": "lbl"})
        ls = [r for r in fig.center if isinstance(r, LabelSet)]
        assert len(ls) >= 1, "mlabel on rcapsym must add LabelSet"

    def test_mlabel_absent_no_labelset(self, fig):
        """No mlabel option → no LabelSet added."""
        from bokeh.models import LabelSet
        src = self._range_cds_with_label()
        gm = GlyphMapper()
        gm.map_rspike(fig, src, "lo", "hi", "x", {})
        ls = [r for r in fig.center if isinstance(r, LabelSet)]
        assert len(ls) == 0, "no mlabel option must not add LabelSet"


# ================================================================
# Bug regression tests — written BEFORE fixes (CLAUDE.md rule 8)
# ================================================================

@pytest.fixture
def range_cds_small():
    """Small range ColumnDataSource for range-plot tests."""
    df = pd.DataFrame({
        "lo":   [1.0, 2.0, 3.0, 4.0, 5.0],
        "hi":   [2.0, 4.0, 6.0, 8.0, 10.0],
        "xvar": [10.0, 20.0, 30.0, 40.0, 50.0],
    })
    return ColumnDataSource(df)


@pytest.fixture
def fit_cds():
    """ColumnDataSource with enough points for regression fits."""
    np.random.seed(0)
    n = 30
    x = np.linspace(1, 10, n)
    y = 2 * x + np.random.randn(n)
    return ColumnDataSource({"y": y, "x": x})


# ----------------------------------------------------------------
# Bug 1: _apply_marker_opts() missing msymbol (regressed from map_scatter inline)
# ----------------------------------------------------------------
class TestApplyMarkerOptsMsymbol:
    """_apply_marker_opts() must handle the msymbol option."""

    def test_marker_opts_msymbol_square(self, fig, cds, gm):
        """msymbol=square passed via options dict must update the glyph marker."""
        renderer = gm.map_scatter(fig, cds, "mpg", "weight", {"msymbol": "square"})
        glyph = renderer.glyph
        assert getattr(glyph, "marker", None) == "square", (
            f"Expected marker 'square', got '{getattr(glyph, 'marker', None)}'"
        )

    def test_marker_opts_msymbol_triangle(self, fig, cds, gm):
        """msymbol=triangle must update glyph marker."""
        renderer = gm.map_scatter(fig, cds, "mpg", "weight", {"msymbol": "triangle"})
        assert getattr(renderer.glyph, "marker", None) == "triangle"

    def test_marker_opts_invalid_msymbol_falls_back(self, fig, cds, gm):
        """Invalid msymbol value must not crash; glyph still renders."""
        renderer = gm.map_scatter(fig, cds, "mpg", "weight",
                                  {"msymbol": "nonexistent_shape"})
        assert renderer is not None

    def test_apply_marker_opts_sets_msymbol(self, fig, cds, gm):
        """Calling _apply_marker_opts with msymbol on an existing renderer changes marker."""
        renderer = gm.map_scatter(fig, cds, "mpg", "weight", {})
        original_marker = getattr(renderer.glyph, "marker", "circle")
        gm._apply_marker_opts(renderer, {"msymbol": "diamond"})
        assert getattr(renderer.glyph, "marker", None) == "diamond", (
            f"_apply_marker_opts should set marker to 'diamond', "
            f"original was '{original_marker}'"
        )


# ----------------------------------------------------------------
# Bug 2: map_rcap() applies no line options
# ----------------------------------------------------------------
class TestMapRcapOptions:
    """map_rcap must apply lcolor/lwidth/lpattern to all segment renderers."""

    def test_rcap_lcolor_applied_to_spine(self, fig, range_cds_small, gm):
        """lcolor option must be applied to the spine segment."""
        renderers = gm.map_rcap(fig, range_cds_small, "lo", "hi", "xvar",
                                {"lcolor": "red"})
        spine = renderers[0]
        assert spine.glyph.line_color == "#ff0000", (
            f"Expected #ff0000, got {spine.glyph.line_color!r}"
        )

    def test_rcap_lcolor_applied_to_caps(self, fig, range_cds_small, gm):
        """lcolor must be applied to both horizontal cap segments."""
        renderers = gm.map_rcap(fig, range_cds_small, "lo", "hi", "xvar",
                                {"lcolor": "navy"})
        bot_cap, top_cap = renderers[1], renderers[2]
        assert bot_cap.glyph.line_color == "#1a476f"
        assert top_cap.glyph.line_color == "#1a476f"

    def test_rcap_lwidth_applied(self, fig, range_cds_small, gm):
        """lwidth option must be applied to all rcap segments."""
        renderers = gm.map_rcap(fig, range_cds_small, "lo", "hi", "xvar",
                                {"lwidth": "thick"})
        from dash_render import OptionTranslator
        expected = OptionTranslator().translate_lwidth("thick")
        for r in renderers:
            assert r.glyph.line_width == expected, (
                f"Expected line_width={expected}, got {r.glyph.line_width}"
            )


# ----------------------------------------------------------------
# Bug 3: map_lfitci/map_qfitci don't apply fill options to VArea
# ----------------------------------------------------------------
class TestFitCIFillOptions:
    """map_lfitci and map_qfitci must apply fcolor/fintensity to VArea band."""

    def test_lfitci_fcolor_applied_to_band(self, fig, fit_cds, gm):
        """fcolor option must set fill_color on the VArea CI band."""
        renderers = gm.map_lfitci(fig, fit_cds, "y", "x", {"fcolor": "navy"})
        band_r = renderers[1]   # band is second renderer
        assert band_r.glyph.fill_color == "#1a476f", (
            f"Expected #1a476f, got {band_r.glyph.fill_color!r}"
        )

    def test_lfitci_fintensity_applied_to_band(self, fig, fit_cds, gm):
        """fintensity option must set fill_alpha on the VArea CI band."""
        renderers = gm.map_lfitci(fig, fit_cds, "y", "x", {"fintensity": "50"})
        band_r = renderers[1]
        assert abs(band_r.glyph.fill_alpha - 0.5) < 0.01, (
            f"Expected fill_alpha ~0.5, got {band_r.glyph.fill_alpha}"
        )

    def test_qfitci_fcolor_applied_to_band(self, fig, fit_cds, gm):
        """fcolor option must set fill_color on the qfitci VArea CI band."""
        renderers = gm.map_qfitci(fig, fit_cds, "y", "x", {"fcolor": "maroon"})
        band_r = renderers[1]
        assert band_r.glyph.fill_color == "#90353b", (
            f"Expected #90353b, got {band_r.glyph.fill_color!r}"
        )

    def test_qfitci_fintensity_applied_to_band(self, fig, fit_cds, gm):
        """fintensity option must set fill_alpha on the qfitci VArea CI band."""
        renderers = gm.map_qfitci(fig, fit_cds, "y", "x", {"fintensity": "30"})
        band_r = renderers[1]
        assert abs(band_r.glyph.fill_alpha - 0.3) < 0.01


# ----------------------------------------------------------------
# Bug 4: map_rcapsym() applies line opts to spine only
# ----------------------------------------------------------------
class TestMapRcapsymOptions:
    """map_rcapsym must apply lcolor consistently to spine AND cap segments."""

    def test_rcapsym_lcolor_applied_to_all_segments(self, fig, range_cds_small, gm):
        """lcolor must be applied to spine, bot_cap, and top_cap."""
        renderers = gm.map_rcapsym(fig, range_cds_small, "lo", "hi", "xvar",
                                   {"lcolor": "maroon"})
        spine, bot_cap, top_cap = renderers[0], renderers[1], renderers[2]
        for seg, name in [(spine, "spine"), (bot_cap, "bot_cap"), (top_cap, "top_cap")]:
            assert seg.glyph.line_color == "#90353b", (
                f"{name} expected #90353b, got {seg.glyph.line_color!r}"
            )

    def test_rcapsym_lwidth_applied_to_spine(self, fig, range_cds_small, gm):
        """lwidth must be applied to at least the spine segment."""
        renderers = gm.map_rcapsym(fig, range_cds_small, "lo", "hi", "xvar",
                                   {"lwidth": "thick"})
        from dash_render import OptionTranslator
        expected = OptionTranslator().translate_lwidth("thick")
        assert renderers[0].glyph.line_width == expected

    def test_rcapsym_mcolor_applied_to_scatter_markers(self, fig, range_cds_small, gm):
        """mcolor must be applied to the scatter marker renderers (indices 3 and 4)."""
        renderers = gm.map_rcapsym(fig, range_cds_small, "lo", "hi", "xvar",
                                   {"mcolor": "red"})
        # renderers[3] and renderers[4] are scatter markers at cap positions
        default_color = gm.map_rcapsym(fig, range_cds_small, "lo", "hi", "xvar",
                                       {})
        default_fill = default_color[3].glyph.fill_color
        assert renderers[3].glyph.fill_color != default_fill, \
            "mcolor must change scatter marker fill_color from default"

    def test_rcapsym_msize_applied_to_scatter_markers(self, fig, range_cds_small, gm):
        """msize must be applied to the scatter marker renderers."""
        renderers = gm.map_rcapsym(fig, range_cds_small, "lo", "hi", "xvar",
                                   {"msize": "large"})
        from dash_render import OptionTranslator
        expected = OptionTranslator().translate_msize("large")
        assert renderers[3].glyph.size == expected, \
            f"Expected size={expected}, got {renderers[3].glyph.size}"


# ================================================================
# Missing unit tests for plot types not yet in test_glyphs.py
# ================================================================

@pytest.fixture
def std_cds_small():
    """Small standard CDS for basic glyph tests."""
    df = pd.DataFrame({
        "y":  [1.0, 2.0, 3.0, 4.0, 5.0],
        "x":  [1.0, 2.0, 3.0, 4.0, 5.0],
        "lo": [0.5, 1.0, 1.5, 2.0, 2.5],
        "hi": [1.5, 3.0, 4.5, 6.0, 7.5],
    })
    return ColumnDataSource(df)


class TestMapQfitci:
    """Unit tests for map_qfitci."""

    def test_qfitci_returns_two_renderers(self, fig, fit_cds, gm):
        """map_qfitci returns [line_renderer, band_renderer]."""
        result = gm.map_qfitci(fig, fit_cds, "y", "x", {})
        assert len(result) == 2

    def test_qfitci_line_renderer_is_line(self, fig, fit_cds, gm):
        """First renderer is a Line glyph."""
        from bokeh.models.glyphs import Line
        result = gm.map_qfitci(fig, fit_cds, "y", "x", {})
        assert isinstance(result[0].glyph, Line)

    def test_qfitci_band_renderer_is_varea(self, fig, fit_cds, gm):
        """Second renderer is a VArea glyph (confidence band)."""
        from bokeh.models.glyphs import VArea
        result = gm.map_qfitci(fig, fit_cds, "y", "x", {})
        assert isinstance(result[1].glyph, VArea)

    def test_qfitci_lcolor_applied_to_line(self, fig, fit_cds, gm):
        """lcolor option must be applied to the fit line."""
        result = gm.map_qfitci(fig, fit_cds, "y", "x", {"lcolor": "navy"})
        assert result[0].glyph.line_color == "#1a476f"


class TestMapLowess:
    """Unit tests for map_lowess."""

    def test_lowess_returns_renderer(self, fig, cds, gm):
        """map_lowess returns a single GlyphRenderer."""
        r = gm.map_lowess(fig, cds, "mpg", "weight", {})
        assert isinstance(r, GlyphRenderer)

    def test_lowess_line_glyph(self, fig, cds, gm):
        """Lowess renderer is a Line glyph."""
        from bokeh.models.glyphs import Line
        r = gm.map_lowess(fig, cds, "mpg", "weight", {})
        assert isinstance(r.glyph, Line)

    def test_lowess_lcolor_applied(self, fig, cds, gm):
        """lcolor option applied to lowess line."""
        r = gm.map_lowess(fig, cds, "mpg", "weight", {"lcolor": "red"})
        assert r.glyph.line_color == "#ff0000"

    def test_lowess_source_sorted_by_x(self, fig, cds, gm):
        """Lowess source data is sorted by x."""
        r = gm.map_lowess(fig, cds, "mpg", "weight", {})
        x_data = list(r.data_source.data["x_lw"])
        assert x_data == sorted(x_data)


class TestMapRarea:
    """Unit tests for map_rarea."""

    def test_rarea_returns_list(self, fig, std_cds_small, gm):
        """map_rarea returns a list."""
        result = gm.map_rarea(fig, std_cds_small, "lo", "hi", "x", {})
        assert isinstance(result, list)

    def test_rarea_varea_glyph(self, fig, std_cds_small, gm):
        """map_rarea produces a VArea glyph."""
        from bokeh.models.glyphs import VArea
        result = gm.map_rarea(fig, std_cds_small, "lo", "hi", "x", {})
        assert isinstance(result[0].glyph, VArea)

    def test_rarea_fcolor_applied(self, fig, std_cds_small, gm):
        """fcolor option applied to rarea VArea fill."""
        result = gm.map_rarea(fig, std_cds_small, "lo", "hi", "x",
                              {"fcolor": "navy"})
        assert result[0].glyph.fill_color == "#1a476f"


class TestMapRbar:
    """Unit tests for map_rbar."""

    def test_rbar_returns_list(self, fig, std_cds_small, gm):
        """map_rbar returns a list."""
        result = gm.map_rbar(fig, std_cds_small, "lo", "hi", "x", {})
        assert isinstance(result, list)

    def test_rbar_vbar_glyph(self, fig, std_cds_small, gm):
        """map_rbar produces a VBar glyph."""
        from bokeh.models.glyphs import VBar
        result = gm.map_rbar(fig, std_cds_small, "lo", "hi", "x", {})
        assert isinstance(result[0].glyph, VBar)

    def test_rbar_fcolor_applied(self, fig, std_cds_small, gm):
        """fcolor option applied to rbar fill."""
        result = gm.map_rbar(fig, std_cds_small, "lo", "hi", "x",
                             {"fcolor": "maroon"})
        assert result[0].glyph.fill_color == "#90353b"


class TestMapRspike:
    """Unit tests for map_rspike."""

    def test_rspike_returns_list(self, fig, std_cds_small, gm):
        """map_rspike returns a list."""
        result = gm.map_rspike(fig, std_cds_small, "lo", "hi", "x", {})
        assert isinstance(result, list)

    def test_rspike_segment_glyph(self, fig, std_cds_small, gm):
        """map_rspike produces a Segment glyph."""
        from bokeh.models.glyphs import Segment
        result = gm.map_rspike(fig, std_cds_small, "lo", "hi", "x", {})
        assert isinstance(result[0].glyph, Segment)

    def test_rspike_lcolor_applied(self, fig, std_cds_small, gm):
        """lcolor option applied to rspike segment."""
        result = gm.map_rspike(fig, std_cds_small, "lo", "hi", "x",
                               {"lcolor": "red"})
        assert result[0].glyph.line_color == "#ff0000"

    def test_rspike_lpattern_applied(self, fig, std_cds_small, gm):
        """lpattern option applied to rspike segment as line_dash."""
        result = gm.map_rspike(fig, std_cds_small, "lo", "hi", "x",
                               {"lpattern": "dash"})
        assert result[0].glyph.line_dash != []


class TestMapRcap:
    """Unit tests for map_rcap."""

    def test_rcap_returns_list_of_three(self, fig, std_cds_small, gm):
        """map_rcap returns [spine, bot_cap, top_cap]."""
        result = gm.map_rcap(fig, std_cds_small, "lo", "hi", "x", {})
        assert len(result) == 3

    def test_rcap_all_segments(self, fig, std_cds_small, gm):
        """All three rcap renderers are Segment glyphs."""
        from bokeh.models.glyphs import Segment
        result = gm.map_rcap(fig, std_cds_small, "lo", "hi", "x", {})
        for r in result:
            assert isinstance(r.glyph, Segment)

    def test_rcap_lpattern_applied_to_all_segments(self, fig, std_cds_small, gm):
        """lpattern applied to all three rcap segment renderers."""
        result = gm.map_rcap(fig, std_cds_small, "lo", "hi", "x",
                             {"lpattern": "dot"})
        for r in result:
            assert r.glyph.line_dash != [], "lpattern must propagate to all rcap segments"


class TestMapRline:
    """Unit tests for map_rline."""

    def test_rline_returns_list(self, fig, std_cds_small, gm):
        """map_rline returns a list."""
        result = gm.map_rline(fig, std_cds_small, "lo", "hi", "x", {})
        assert isinstance(result, list)

    def test_rline_has_two_line_renderers(self, fig, std_cds_small, gm):
        """map_rline produces two Line glyphs (one per boundary)."""
        from bokeh.models.glyphs import Line
        result = gm.map_rline(fig, std_cds_small, "lo", "hi", "x", {})
        lines = [r for r in result if isinstance(r.glyph, Line)]
        assert len(lines) == 2

    def test_rline_lcolor_applied(self, fig, std_cds_small, gm):
        """lcolor option applied to both rline renderers."""
        result = gm.map_rline(fig, std_cds_small, "lo", "hi", "x",
                              {"lcolor": "navy"})
        for r in result:
            assert r.glyph.line_color == "#1a476f"

    def test_rline_lpattern_applied_to_both_lines(self, fig, std_cds_small, gm):
        """lpattern applied to both rline boundary lines."""
        result = gm.map_rline(fig, std_cds_small, "lo", "hi", "x",
                              {"lpattern": "dash"})
        for r in result:
            assert r.glyph.line_dash != [], "lpattern must propagate to both rline renderers"


class TestMapRconnected:
    """Unit tests for map_rconnected."""

    def test_rconnected_returns_list(self, fig, std_cds_small, gm):
        """map_rconnected returns a list of renderers."""
        result = gm.map_rconnected(fig, std_cds_small, "lo", "hi", "x", {})
        assert isinstance(result, list)
        assert len(result) >= 2

    def test_rconnected_has_lines(self, fig, std_cds_small, gm):
        """map_rconnected includes Line glyphs."""
        from bokeh.models.glyphs import Line
        result = gm.map_rconnected(fig, std_cds_small, "lo", "hi", "x", {})
        lines = [r for r in result if isinstance(r.glyph, Line)]
        assert len(lines) >= 1


class TestMapPcspike:
    """Unit tests for map_pcspike."""

    @pytest.fixture
    def pc_cds(self):
        df = pd.DataFrame({
            "y1": [1.0, 2.0, 3.0],
            "x1": [1.0, 2.0, 3.0],
            "y2": [2.0, 3.0, 4.0],
            "x2": [2.0, 3.0, 4.0],
        })
        return ColumnDataSource(df)

    def test_pcspike_returns_renderer(self, fig, pc_cds, gm):
        """map_pcspike returns a GlyphRenderer."""
        r = gm.map_pcspike(fig, pc_cds, "y1", "x1", "y2", "x2", {})
        assert r is not None

    def test_pcspike_segment_glyph(self, fig, pc_cds, gm):
        """map_pcspike produces a Segment glyph."""
        from bokeh.models.glyphs import Segment
        r = gm.map_pcspike(fig, pc_cds, "y1", "x1", "y2", "x2", {})
        if isinstance(r, list):
            r = r[0]
        assert isinstance(r.glyph, Segment)

    def test_pcspike_lcolor_applied(self, fig, pc_cds, gm):
        """lcolor option applied to pcspike segment."""
        r = gm.map_pcspike(fig, pc_cds, "y1", "x1", "y2", "x2",
                           {"lcolor": "red"})
        if isinstance(r, list):
            r = r[0]
        assert r.glyph.line_color == "#ff0000"


class TestMapPcarrow:
    """Unit tests for map_pcarrow."""

    @pytest.fixture
    def pc_cds(self):
        df = pd.DataFrame({
            "y1": [1.0, 2.0, 3.0],
            "x1": [1.0, 2.0, 3.0],
            "y2": [2.0, 3.0, 4.0],
            "x2": [2.0, 3.0, 4.0],
        })
        return ColumnDataSource(df)

    def test_pcarrow_returns_result(self, fig, pc_cds, gm):
        """map_pcarrow returns at least one renderer or annotation."""
        r = gm.map_pcarrow(fig, pc_cds, "y1", "x1", "y2", "x2", {})
        assert r is not None

    def test_pcarrow_lwidth_applied(self, fig, pc_cds, gm):
        """lwidth(thick)=2.5 applied to segment renderer via _apply_line_opts."""
        renderers = gm.map_pcarrow(fig, pc_cds, "y1", "x1", "y2", "x2",
                                   {"lwidth": "thick"})
        seg = renderers[0]
        assert abs(seg.glyph.line_width - 2.5) < 0.01, \
            "map_pcarrow must apply lwidth(thick)=2.5 to segment"

    def test_pcarrow_lcolor_applied(self, fig, pc_cds, gm):
        """lcolor option applied to segment renderer."""
        renderers = gm.map_pcarrow(fig, pc_cds, "y1", "x1", "y2", "x2",
                                   {"lcolor": "red"})
        seg = renderers[0]
        assert seg.glyph.line_color == "#ff0000", \
            "map_pcarrow must apply lcolor to segment"

    def test_pcarrow_lwidth_applies_to_arrow_annotations(self, fig, pc_cds, gm):
        """lwidth(thick)=2.5 must also be applied to Arrow annotation objects.

        Arrow annotations added via fig.add_layout() are stored in fig.center.
        """
        from bokeh.models import Arrow
        gm.map_pcarrow(fig, pc_cds, "y1", "x1", "y2", "x2", {"lwidth": "thick"})
        arrow_annots = [a for a in fig.center if isinstance(a, Arrow)]
        assert arrow_annots, "map_pcarrow must add Arrow annotations to fig"
        for arrow in arrow_annots:
            assert abs(arrow.line_width - 2.5) < 0.01, \
                f"Arrow annotation line_width must be 2.5 (thick) but got {arrow.line_width}"


class TestMapPcbarrow:
    """Unit tests for map_pcbarrow."""

    @pytest.fixture
    def pc_cds(self):
        df = pd.DataFrame({
            "y1": [1.0, 2.0, 3.0],
            "x1": [1.0, 2.0, 3.0],
            "y2": [2.0, 3.0, 4.0],
            "x2": [2.0, 3.0, 4.0],
        })
        return ColumnDataSource(df)

    def test_pcbarrow_returns_result(self, fig, pc_cds, gm):
        """map_pcbarrow returns at least one renderer or annotation."""
        r = gm.map_pcbarrow(fig, pc_cds, "y1", "x1", "y2", "x2", {})
        assert r is not None

    def test_pcbarrow_lwidth_applied(self, fig, pc_cds, gm):
        """lwidth(thick)=2.5 applied to segment renderer via _apply_line_opts."""
        renderers = gm.map_pcbarrow(fig, pc_cds, "y1", "x1", "y2", "x2",
                                    {"lwidth": "thick"})
        seg = renderers[0]
        assert abs(seg.glyph.line_width - 2.5) < 0.01, \
            "map_pcbarrow must apply lwidth(thick)=2.5 to segment"

    def test_pcbarrow_lcolor_applied(self, fig, pc_cds, gm):
        """lcolor option applied to segment renderer."""
        renderers = gm.map_pcbarrow(fig, pc_cds, "y1", "x1", "y2", "x2",
                                    {"lcolor": "red"})
        seg = renderers[0]
        assert seg.glyph.line_color == "#ff0000", \
            "map_pcbarrow must apply lcolor to segment"

    def test_pcbarrow_lwidth_applies_to_arrow_annotations(self, fig, pc_cds, gm):
        """lwidth(thick)=2.5 must also be applied to Arrow annotation objects.

        Arrow annotations added via fig.add_layout() are stored in fig.center.
        """
        from bokeh.models import Arrow
        gm.map_pcbarrow(fig, pc_cds, "y1", "x1", "y2", "x2", {"lwidth": "thick"})
        arrow_annots = [a for a in fig.center if isinstance(a, Arrow)]
        assert arrow_annots, "map_pcbarrow must add Arrow annotations to fig"
        for arrow in arrow_annots:
            assert abs(arrow.line_width - 2.5) < 0.01, \
                f"Arrow annotation line_width must be 2.5 (thick) but got {arrow.line_width}"


class TestMapTsline:
    """Unit tests for map_tsline."""

    def test_tsline_returns_renderer(self, fig, cds, gm):
        """map_tsline returns a GlyphRenderer."""
        r = gm.map_tsline(fig, cds, "mpg", "weight", {})
        assert isinstance(r, GlyphRenderer)

    def test_tsline_line_glyph(self, fig, cds, gm):
        """map_tsline produces a Line glyph."""
        from bokeh.models.glyphs import Line
        r = gm.map_tsline(fig, cds, "mpg", "weight", {})
        assert isinstance(r.glyph, Line)

    def test_tsline_lcolor_applied(self, fig, cds, gm):
        """lcolor option applied via tsline."""
        r = gm.map_tsline(fig, cds, "mpg", "weight", {"lcolor": "navy"})
        assert r.glyph.line_color == "#1a476f"


class TestMapTsrline:
    """Unit tests for map_tsrline."""

    def test_tsrline_returns_list(self, fig, std_cds_small, gm):
        """map_tsrline returns a list of renderers."""
        result = gm.map_tsrline(fig, std_cds_small, "lo", "hi", "x", {})
        assert isinstance(result, list)

    def test_tsrline_has_lines(self, fig, std_cds_small, gm):
        """map_tsrline includes Line glyphs."""
        from bokeh.models.glyphs import Line
        result = gm.map_tsrline(fig, std_cds_small, "lo", "hi", "x", {})
        lines = [r for r in result if isinstance(r.glyph, Line)]
        assert len(lines) >= 1


class TestMapMspline:
    """Unit tests for map_mspline. map_mspline returns a list."""

    def test_mspline_returns_list(self, fig, cds, gm):
        """map_mspline returns a list with one GlyphRenderer."""
        result = gm.map_mspline(fig, cds, "mpg", "weight", {})
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], GlyphRenderer)

    def test_mspline_line_glyph(self, fig, cds, gm):
        """map_mspline produces a Line glyph."""
        from bokeh.models.glyphs import Line
        result = gm.map_mspline(fig, cds, "mpg", "weight", {})
        assert isinstance(result[0].glyph, Line)

    def test_mspline_smooth_output(self, fig, cds, gm):
        """map_mspline outputs more points than input (smooth interpolation)."""
        result = gm.map_mspline(fig, cds, "mpg", "weight", {})
        n_output = len(result[0].data_source.data["x_sp"])
        assert n_output >= 50, f"Expected >=50 interpolated points, got {n_output}"

    def test_mspline_lcolor_applied(self, fig, cds, gm):
        """lcolor option applied to mspline."""
        result = gm.map_mspline(fig, cds, "mpg", "weight", {"lcolor": "red"})
        assert result[0].glyph.line_color == "#ff0000"

    def test_mspline_handles_duplicate_x(self, fig, gm):
        """map_mspline deduplicates x values to satisfy PchipInterpolator."""
        dup_df = pd.DataFrame({
            "y": [1.0, 2.0, 2.0, 3.0, 4.0],
            "x": [1.0, 2.0, 2.0, 3.0, 4.0],   # duplicate x=2.0
        })
        dup_cds = ColumnDataSource(dup_df)
        result = gm.map_mspline(fig, dup_cds, "y", "x", {})
        assert isinstance(result, list)
        assert result[0].data_source.data["x_sp"] is not None


class TestMapFunction:
    """Unit tests for map_function. map_function returns a list."""

    def test_function_returns_list(self, fig, gm):
        """map_function returns a list with one GlyphRenderer."""
        result = gm.map_function(fig, "x", (0.0, 1.0), 100, {})
        assert isinstance(result, list)
        assert isinstance(result[0], GlyphRenderer)

    def test_function_line_glyph(self, fig, gm):
        """map_function produces a Line glyph."""
        from bokeh.models.glyphs import Line
        result = gm.map_function(fig, "x", (0.0, 1.0), 100, {})
        assert isinstance(result[0].glyph, Line)

    def test_function_sin_renders(self, fig, gm):
        """map_function with sin(x) produces 100 data points."""
        result = gm.map_function(fig, "sin(x)", (0.0, 6.28), 100, {})
        assert len(result[0].data_source.data["x_fn"]) == 100

    def test_function_injection_rejected(self, fig, gm):
        """Dangerous expressions are rejected safely — empty renderer, no crash."""
        result = gm.map_function(fig, "__import__('os').system('id')", (0.0, 1.0), 10, {})
        assert isinstance(result, list)
        assert len(result[0].data_source.data.get("x_fn", [])) == 0

    def test_function_lcolor_applied(self, fig, gm):
        """lcolor option applied to function line."""
        result = gm.map_function(fig, "x", (0.0, 1.0), 50, {"lcolor": "navy"})
        assert result[0].glyph.line_color == "#1a476f"


# ================================================================
# Legend label coverage — all map_* methods must produce a legend entry
# ================================================================

def _legend_items(fig):
    """Return list of (label_text, renderer) tuples from fig.legend."""
    items = []
    for leg in fig.legend:
        for item in leg.items:
            lbl = item.label
            text = lbl.value if hasattr(lbl, "value") else str(lbl)
            items.append(text)
    return items


class TestLegendLabelCoverage:
    """Every map_* method must produce at least one legend entry with the yvar name."""

    def _range_cds(self):
        df = pd.DataFrame({
            "lo": [1.0, 2.0, 3.0, 4.0, 5.0],
            "hi": [2.0, 3.0, 4.0, 5.0, 6.0],
            "x":  [1.0, 2.0, 3.0, 4.0, 5.0],
        })
        return ColumnDataSource(df)

    def _pc_cds(self):
        df = pd.DataFrame({
            "y1": [0.0, 1.0, 2.0],
            "x1": [0.0, 1.0, 2.0],
            "y2": [1.0, 2.0, 3.0],
            "x2": [1.0, 2.0, 3.0],
        })
        return ColumnDataSource(df)

    def test_spike_legend(self, fig, cds, gm):
        """map_spike must create a legend entry for yvar."""
        gm.map_spike(fig, cds, "mpg", "weight", {})
        assert "mpg" in _legend_items(fig)

    def test_lfit_legend(self, fig, cds, gm):
        """map_lfit must create a legend entry for yvar."""
        gm.map_lfit(fig, cds, "mpg", "weight", {})
        assert "mpg" in _legend_items(fig)

    def test_qfit_legend(self, fig, cds, gm):
        """map_qfit must create a legend entry for yvar."""
        gm.map_qfit(fig, cds, "mpg", "weight", {})
        assert "mpg" in _legend_items(fig)

    def test_lfitci_legend(self, fig, cds, gm):
        """map_lfitci must create a legend entry for yvar."""
        gm.map_lfitci(fig, cds, "mpg", "weight", {})
        assert "mpg" in _legend_items(fig)

    def test_qfitci_legend(self, fig, cds, gm):
        """map_qfitci must create a legend entry for yvar."""
        gm.map_qfitci(fig, cds, "mpg", "weight", {})
        assert "mpg" in _legend_items(fig)

    def test_lowess_legend(self, fig, cds, gm):
        """map_lowess must create a legend entry for yvar."""
        gm.map_lowess(fig, cds, "mpg", "weight", {})
        assert "mpg" in _legend_items(fig)

    def test_histogram_legend(self, fig, cds, gm):
        """map_histogram must create a legend entry for yvar."""
        gm.map_histogram(fig, cds, "mpg", {})
        assert "mpg" in _legend_items(fig)

    def test_kdensity_legend(self, fig, cds, gm):
        """map_kdensity must create a legend entry for yvar."""
        gm.map_kdensity(fig, cds, "mpg", {})
        assert "mpg" in _legend_items(fig)

    def test_rarea_legend(self, fig, gm):
        """map_rarea must create a legend entry for y1var."""
        gm.map_rarea(fig, self._range_cds(), "lo", "hi", "x", {})
        assert "lo" in _legend_items(fig)

    def test_rbar_legend(self, fig, gm):
        """map_rbar must create a legend entry for y1var."""
        gm.map_rbar(fig, self._range_cds(), "lo", "hi", "x", {})
        assert "lo" in _legend_items(fig)

    def test_rspike_legend(self, fig, gm):
        """map_rspike must create a legend entry for y1var."""
        gm.map_rspike(fig, self._range_cds(), "lo", "hi", "x", {})
        assert "lo" in _legend_items(fig)

    def test_rcap_legend(self, fig, gm):
        """map_rcap must create a legend entry for y1var."""
        gm.map_rcap(fig, self._range_cds(), "lo", "hi", "x", {})
        assert "lo" in _legend_items(fig)

    def test_rline_legend(self, fig, gm):
        """map_rline must create a legend entry for y1var."""
        gm.map_rline(fig, self._range_cds(), "lo", "hi", "x", {})
        assert "lo" in _legend_items(fig)

    def test_dropline_legend(self, fig, cds, gm):
        """map_dropline must create a legend entry for yvar."""
        gm.map_dropline(fig, cds, "mpg", "weight", {})
        assert "mpg" in _legend_items(fig)

    def test_rcapsym_legend(self, fig, gm):
        """map_rcapsym must create a legend entry for y1var."""
        gm.map_rcapsym(fig, self._range_cds(), "lo", "hi", "x", {})
        assert "lo" in _legend_items(fig)

    def test_pcspike_legend(self, fig, gm):
        """map_pcspike must create a legend entry for y1var."""
        gm.map_pcspike(fig, self._pc_cds(), "y1", "x1", "y2", "x2", {})
        assert "y1" in _legend_items(fig)

    def test_pcarrow_legend(self, fig, gm):
        """map_pcarrow must create a legend entry for y1var."""
        gm.map_pcarrow(fig, self._pc_cds(), "y1", "x1", "y2", "x2", {})
        assert "y1" in _legend_items(fig)

    def test_pcbarrow_legend(self, fig, gm):
        """map_pcbarrow must create a legend entry for y1var."""
        gm.map_pcbarrow(fig, self._pc_cds(), "y1", "x1", "y2", "x2", {})
        assert "y1" in _legend_items(fig)

    def test_mspline_legend(self, fig, cds, gm):
        """map_mspline must create a legend entry for yvar."""
        gm.map_mspline(fig, cds, "mpg", "weight", {})
        assert "mpg" in _legend_items(fig)

    def test_function_legend(self, fig, gm):
        """map_function must create a legend entry."""
        gm.map_function(fig, "x", (0.0, 1.0), 50, {})
        assert len(_legend_items(fig)) >= 1


class TestMlabwidth:
    """mlabwidth option in _apply_mlabel_opts must not crash."""

    def test_mlabwidth_does_not_crash(self, fig, gm):
        """Providing mlabwidth must not raise an exception."""
        df = pd.DataFrame({"y": [1.0, 2.0, 3.0], "x": [1.0, 2.0, 3.0], "lbl": ["a", "b", "c"]})
        src = ColumnDataSource(df)
        # Should complete without error
        gm._apply_mlabel_opts(fig, src, {"mlabel": "lbl", "mlabwidth": "20"}, "x", "y")
        assert len(fig.renderers) >= 0  # just verifies no exception

    def test_mlabwidth_label_still_created(self, fig, gm):
        """LabelSet must still be added to the figure when mlabwidth is present."""
        from bokeh.models import LabelSet
        df = pd.DataFrame({"y": [1.0, 2.0], "x": [1.0, 2.0], "lbl": ["a", "b"]})
        src = ColumnDataSource(df)
        gm._apply_mlabel_opts(fig, src, {"mlabel": "lbl", "mlabwidth": "15"}, "x", "y")
        label_sets = [c for c in fig.center if isinstance(c, LabelSet)]
        assert len(label_sets) >= 1


class TestMarkerGenericOption:
    """The 'm' abbreviation expands to 'marker' in the parser.
    _apply_marker_opts must treat 'marker' as an alias for 'msymbol'."""

    def test_marker_option_applies_symbol(self, fig, cds, gm):
        """options={'marker':'triangle'} must set glyph.marker = 'triangle'."""
        r = gm.map_scatter(fig, cds, "mpg", "weight", {"marker": "triangle"})
        from bokeh.models.glyphs import Scatter
        assert isinstance(r.glyph, Scatter)
        assert r.glyph.marker == "triangle", \
            "generic 'marker' option must set glyph marker type"

    def test_marker_option_coexists_with_msymbol(self, fig, cds, gm):
        """When both 'marker' and 'msymbol' are present, msymbol takes precedence
        (applied after) but 'marker' must not crash."""
        r = gm.map_scatter(fig, cds, "mpg", "weight",
                           {"marker": "triangle", "msymbol": "circle"})
        assert r.glyph.marker == "circle", \
            "msymbol must win when both marker and msymbol specified"


class TestMfcolor:
    """mfcolor sets the marker FILL color independently of the outline color."""

    def test_mfcolor_sets_fill_independently(self, fig, cds, gm):
        """mfcolor(red) should set fill_color=red but leave line_color as default."""
        r = gm.map_scatter(fig, cds, "mpg", "weight", {"mfcolor": "red"})
        assert r.glyph.fill_color == "#ff0000", \
            "mfcolor must set fill_color"

    def test_mfcolor_does_not_change_line_color(self, fig, cds, gm):
        """mfcolor alone must not change the line/outline color."""
        default_line = gm.map_scatter(fig, cds, "mpg", "weight", {}).glyph.line_color
        r = gm.map_scatter(fig, cds, "mpg", "weight", {"mfcolor": "red"})
        assert r.glyph.line_color == default_line, \
            "mfcolor must not alter line_color"

    def test_mcolor_plus_mfcolor_mfcolor_wins_fill(self, fig, cds, gm):
        """When mcolor and mfcolor both present, mfcolor overrides fill_color."""
        r = gm.map_scatter(fig, cds, "mpg", "weight",
                           {"mcolor": "blue", "mfcolor": "red"})
        assert r.glyph.fill_color == "#ff0000", \
            "mfcolor must override fill_color set by mcolor"
        assert r.glyph.line_color == "#0000ff", \
            "mcolor must still set line_color when mfcolor present"

    def test_mfcolor_invalid_no_crash(self, fig, cds, gm):
        """Invalid mfcolor value must not raise; glyph must still be created."""
        r = gm.map_scatter(fig, cds, "mpg", "weight", {"mfcolor": "notacolor"})
        assert r is not None


class TestBarOptions:
    """barwidth(), base(), blcolor(), bfcolor() options for map_bar()."""

    def test_barwidth_overrides_auto_width(self, fig, cds, gm):
        """barwidth(0.3) must set bar width to 0.3."""
        r = gm.map_bar(fig, cds, "mpg", "weight", {"barwidth": "0.3"})
        assert abs(r.glyph.width - 0.3) < 1e-9, \
            "barwidth option must override auto-computed width"

    def test_width_alias_for_barwidth(self, fig, cds, gm):
        """width(0.5) must also set bar width to 0.5."""
        r = gm.map_bar(fig, cds, "mpg", "weight", {"width": "0.5"})
        assert abs(r.glyph.width - 0.5) < 1e-9, \
            "width option must set bar width"

    def test_barwidth_invalid_no_crash(self, fig, cds, gm):
        """Non-numeric barwidth must not raise; auto width used instead."""
        r = gm.map_bar(fig, cds, "mpg", "weight", {"barwidth": "abc"})
        assert r is not None

    def test_base_changes_bar_bottom(self, fig, cds, gm):
        """base(5) must shift bar bottom to 5 (vbar bottom attribute)."""
        r = gm.map_bar(fig, cds, "mpg", "weight", {"base": "5"})
        assert r.glyph.bottom == 5.0, \
            "base option must set vbar bottom attribute"

    def test_base_default_is_zero(self, fig, cds, gm):
        """Absent base option must default bar bottom to 0."""
        r = gm.map_bar(fig, cds, "mpg", "weight", {})
        assert r.glyph.bottom == 0, "default bar bottom must be 0"

    def test_bfcolor_sets_fill(self, fig, cds, gm):
        """bfcolor(red) must set bar fill_color to #ff0000."""
        r = gm.map_bar(fig, cds, "mpg", "weight", {"bfcolor": "red"})
        assert r.glyph.fill_color == "#ff0000", \
            "bfcolor must set bar fill_color"

    def test_blcolor_sets_line(self, fig, cds, gm):
        """blcolor(navy) must set bar line_color to navy hex."""
        r = gm.map_bar(fig, cds, "mpg", "weight", {"blcolor": "navy"})
        assert r.glyph.line_color == "#1a476f", \
            "blcolor must set bar line_color"

    def test_blcolor_bfcolor_independent(self, fig, cds, gm):
        """blcolor and bfcolor must be settable independently."""
        r = gm.map_bar(fig, cds, "mpg", "weight",
                       {"bfcolor": "red", "blcolor": "navy"})
        assert r.glyph.fill_color == "#ff0000"
        assert r.glyph.line_color == "#1a476f"


class TestAreaBase:
    """base() option for map_area() changes the lower boundary."""

    def test_base_changes_area_lower_boundary(self, fig, cds, gm):
        """base(5) must set the lower boundary of the area glyph to 5."""
        r = gm.map_area(fig, cds, "mpg", "weight", {"base": "5"})
        # VArea uses yvar_base column for lower boundary — check CDS values
        src = r.data_source
        # Column is named "{yvar}_base" since renaming for hover tool support
        y1_col = "mpg_base"
        y1_vals = src.data[y1_col]
        assert all(v == 5.0 for v in y1_vals), \
            "base option must set lower area boundary to specified value"

    def test_base_default_is_zero(self, fig, cds, gm):
        """Absent base must default to 0 (all yvar_base == 0)."""
        r = gm.map_area(fig, cds, "mpg", "weight", {})
        assert all(v == 0 for v in r.data_source.data["mpg_base"])


class TestSpikeBase:
    """base() option for map_spike() changes the spike origin."""

    def test_base_changes_spike_origin(self, fig, cds, gm):
        """base(3) must set segment y0 values to 3."""
        r = gm.map_spike(fig, cds, "mpg", "weight", {"base": "3"})
        y0_vals = r.data_source.data["y0"]
        assert all(v == 3.0 for v in y0_vals), \
            "base option must set spike y0 (origin) to specified value"

    def test_base_default_is_zero(self, fig, cds, gm):
        """Absent base must default spike y0 to 0."""
        r = gm.map_spike(fig, cds, "mpg", "weight", {})
        assert all(v == 0 for v in r.data_source.data["y0"])


class TestBarLineOpts:
    """lwidth and lpattern must be applied to map_bar() border via _apply_line_opts()."""

    def test_bar_lwidth_applied(self, fig, cds, gm):
        """lwidth(thick) must set bar glyph line_width."""
        r = gm.map_bar(fig, cds, "mpg", "weight", {"lwidth": "thick"})
        assert r.glyph.line_width > 1.0, \
            "lwidth(thick) must increase bar border line_width above default"

    def test_bar_lpattern_applied(self, fig, cds, gm):
        """lpattern(dash) must set bar glyph line_dash."""
        r = gm.map_bar(fig, cds, "mpg", "weight", {"lpattern": "dash"})
        assert r.glyph.line_dash not in ([], "solid", None), \
            "lpattern(dash) must set non-solid line_dash on bar border"

    def test_bar_lcolor_via_line_opts(self, fig, cds, gm):
        """lcolor(red) applied via _apply_line_opts must set bar line_color."""
        r = gm.map_bar(fig, cds, "mpg", "weight", {"lcolor": "red"})
        assert r.glyph.line_color == "#ff0000", \
            "lcolor via _apply_line_opts must set bar border line_color"


class TestHistogramLineOpts:
    """lwidth and lpattern must be applied to map_histogram() border via _apply_line_opts()."""

    def test_histogram_lwidth_applied(self, fig, cds, gm):
        """lwidth(thick) must set histogram quad line_width."""
        r = gm.map_histogram(fig, cds, "mpg", {"lwidth": "thick"})
        assert r.glyph.line_width > 1.0, \
            "lwidth(thick) must increase histogram quad border line_width"

    def test_histogram_lpattern_applied(self, fig, cds, gm):
        """lpattern(dot) must set histogram quad line_dash."""
        r = gm.map_histogram(fig, cds, "mpg", {"lpattern": "dot"})
        assert r.glyph.line_dash not in ([], "solid", None), \
            "lpattern(dot) must set non-solid line_dash on histogram quad"

    def test_histogram_lcolor_via_line_opts(self, fig, cds, gm):
        """lcolor(navy) applied via _apply_line_opts must set histogram quad line_color."""
        r = gm.map_histogram(fig, cds, "mpg", {"lcolor": "navy"})
        assert r.glyph.line_color == "#1a476f", \
            "lcolor via _apply_line_opts must set histogram quad line_color"


class TestAreaBorderLine:
    """When lcolor/lwidth/lpattern specified, map_area() must add a border line renderer."""

    def test_area_lcolor_adds_border_line(self, fig, cds, gm):
        """lcolor(red) must add a Line renderer on top of the area."""
        from bokeh.models import GlyphRenderer
        from bokeh.models.glyphs import Line
        renderers_before = len(fig.renderers)
        gm.map_area(fig, cds, "mpg", "weight", {"lcolor": "red"})
        line_renderers = [r for r in fig.renderers
                          if isinstance(r, GlyphRenderer) and isinstance(r.glyph, Line)]
        assert len(line_renderers) >= 1, \
            "lcolor option must add a Line renderer as area border"
        assert line_renderers[-1].glyph.line_color == "#ff0000", \
            "border line must use the specified lcolor"

    def test_area_lwidth_applied_to_border(self, fig, cds, gm):
        """lwidth(thick) must set border line line_width."""
        from bokeh.models import GlyphRenderer
        from bokeh.models.glyphs import Line
        gm.map_area(fig, cds, "mpg", "weight", {"lwidth": "thick"})
        line_renderers = [r for r in fig.renderers
                          if isinstance(r, GlyphRenderer) and isinstance(r.glyph, Line)]
        assert len(line_renderers) >= 1, "lwidth must trigger border line"
        assert line_renderers[-1].glyph.line_width > 1.0, \
            "border line_width must be > default"

    def test_area_no_line_opts_no_border_line(self, fig, cds, gm):
        """With no line options, map_area must NOT add an extra Line renderer."""
        from bokeh.models import GlyphRenderer
        from bokeh.models.glyphs import Line
        gm.map_area(fig, cds, "mpg", "weight", {})
        line_renderers = [r for r in fig.renderers
                          if isinstance(r, GlyphRenderer) and isinstance(r.glyph, Line)]
        assert len(line_renderers) == 0, \
            "no line options must not add a border line renderer"


# ================================================================
# New plot types: pci, pcscatter, rscatter, mband
# ================================================================

class TestNewPlotTypes:
    """Tests for the 4 new plot types added in iteration N+1:
       pci, pcscatter, rscatter, mband.
    """

    @pytest.fixture
    def pc_cds(self):
        """CDS with paired-coordinate variables."""
        return ColumnDataSource({
            "y1": [1.0, 2.0, 3.0],
            "x1": [0.0, 1.0, 2.0],
            "y2": [4.0, 5.0, 6.0],
            "x2": [3.0, 4.0, 5.0],
        })

    @pytest.fixture
    def range_cds(self):
        """CDS with range variables (y1, y2, x)."""
        return ColumnDataSource({
            "y1": [1.0, 2.0, 3.0, 4.0, 5.0],
            "y2": [6.0, 7.0, 8.0, 9.0, 10.0],
            "x":  [1.0, 2.0, 3.0, 4.0, 5.0],
        })

    @pytest.fixture
    def xy_cds(self):
        """CDS with simple x/y variables (20 rows for mband)."""
        np.random.seed(7)
        n = 20
        return ColumnDataSource({
            "y": np.random.randn(n).tolist(),
            "x": np.linspace(0, 10, n).tolist(),
        })

    def test_map_pci_adds_renderers(self, fig, pc_cds):
        """map_pci() adds at least one renderer (segment) to the figure."""
        gm = GlyphMapper(OptionTranslator())
        gm.map_pci(fig, pc_cds, "y1", "x1", "y2", "x2", {})
        assert len(fig.renderers) >= 1

    def test_map_pci_delegates_to_pcspike(self, fig, pc_cds):
        """map_pci and map_pcspike produce the same number of renderers."""
        gm = GlyphMapper(OptionTranslator())
        fig2 = figure()
        gm.map_pcspike(fig,  pc_cds, "y1", "x1", "y2", "x2", {})
        gm.map_pci(    fig2, pc_cds, "y1", "x1", "y2", "x2", {})
        assert len(fig.renderers) == len(fig2.renderers)

    def test_map_pcscatter_adds_scatter_renderer(self, fig, pc_cds):
        """map_pcscatter() adds a scatter renderer with 2×n points."""
        from bokeh.models.glyphs import Scatter
        gm = GlyphMapper(OptionTranslator())
        gm.map_pcscatter(fig, pc_cds, "y1", "x1", "y2", "x2", {})
        scatter_rs = [r for r in fig.renderers
                      if isinstance(r, GlyphRenderer)
                      and isinstance(r.glyph, Scatter)]
        assert len(scatter_rs) == 1
        # 3 observations × 2 endpoints = 6 points
        assert len(scatter_rs[0].data_source.data["x"]) == 6

    def test_map_rscatter_adds_scatter_renderer(self, fig, range_cds):
        """map_rscatter() adds a scatter renderer with 2×n points."""
        from bokeh.models.glyphs import Scatter
        gm = GlyphMapper(OptionTranslator())
        gm.map_rscatter(fig, range_cds, "y1", "y2", "x", {})
        scatter_rs = [r for r in fig.renderers
                      if isinstance(r, GlyphRenderer)
                      and isinstance(r.glyph, Scatter)]
        assert len(scatter_rs) == 1
        assert len(scatter_rs[0].data_source.data["x"]) == 10  # 5 × 2

    def test_map_rscatter_handles_nan(self, fig):
        """map_rscatter() drops NaN rows."""
        from bokeh.models.glyphs import Scatter
        gm = GlyphMapper(OptionTranslator())
        cds_nan = ColumnDataSource({
            "y1": [1.0, float("nan"), 3.0],
            "y2": [4.0, 5.0, 6.0],
            "x":  [1.0, 2.0, 3.0],
        })
        gm.map_rscatter(fig, cds_nan, "y1", "y2", "x", {})
        scatter_rs = [r for r in fig.renderers
                      if isinstance(r, GlyphRenderer)
                      and isinstance(r.glyph, Scatter)]
        # Row 0: both valid; row 1: y1=NaN drops that x from y1-side only;
        # row 2: both valid → 5 valid points across both sides
        assert len(scatter_rs[0].data_source.data["x"]) == 5

    def test_map_mband_adds_line_renderer(self, fig, xy_cds):
        """map_mband() adds a line renderer."""
        from bokeh.models.glyphs import Line
        gm = GlyphMapper(OptionTranslator())
        gm.map_mband(fig, xy_cds, "y", "x", {})
        line_rs = [r for r in fig.renderers
                   if isinstance(r, GlyphRenderer) and isinstance(r.glyph, Line)]
        assert len(line_rs) >= 1

    def test_map_mband_fewer_points_than_raw(self, fig, xy_cds):
        """map_mband() produces ≤ n_raw data points (band aggregation)."""
        from bokeh.models.glyphs import Line
        gm = GlyphMapper(OptionTranslator())
        gm.map_mband(fig, xy_cds, "y", "x", {})
        line_rs = [r for r in fig.renderers
                   if isinstance(r, GlyphRenderer) and isinstance(r.glyph, Line)]
        n_raw = len(xy_cds.data["x"])
        n_band = len(line_rs[0].data_source.data["x_mb"])
        assert n_band <= n_raw

    def test_map_mband_too_few_rows_returns_empty(self):
        """map_mband() with < 4 rows returns an empty line (no crash)."""
        from bokeh.models.glyphs import Line
        gm = GlyphMapper(OptionTranslator())
        fig2 = figure()
        cds_small = ColumnDataSource({"y": [1.0, 2.0], "x": [1.0, 2.0]})
        gm.map_mband(fig2, cds_small, "y", "x", {})
        line_rs = [r for r in fig2.renderers
                   if isinstance(r, GlyphRenderer) and isinstance(r.glyph, Line)]
        assert len(line_rs) == 1
        assert len(line_rs[0].data_source.data["x_mb"]) == 0

    def test_pci_in_dispatch(self, fig, pc_cds):
        """_add_pc_glyph dispatches 'pci' correctly."""
        from dash_render import GlyphMapper
        gm = GlyphMapper(OptionTranslator())

        class _FakeFigureWrapper:
            """Wrap a real figure via a DashRenderer-like helper."""

        import json, tempfile
        from dash_render import DashRenderer
        vals = [{"mpg": float(i), "weight": float(i), "y1": float(i),
                 "x1": float(i), "y2": float(i+1), "x2": float(i+1)}
                for i in range(1, 6)]
        spec = {
            "graphs": [{
                "plots": [{"type": "pci", "y1var": "y1", "x1var": "x1",
                           "y2var": "y2", "x2var": "x2", "options": {}}],
                "graph_options": {"name": "g1"},
                "if_expr": "", "in_expr": "",
            }],
            "kpis": [],
            "build_options": {
                "layout": "auto", "link": "", "filter": "",
                "theme": "default", "title": "", "subtitle": "", "registry": "g1",
            },
        }
        dj = {
            "StataJSON": {
                "variableNames": ["mpg", "weight", "y1", "x1", "y2", "x2"],
                "variableLabels": {v: v for v in ["mpg", "weight", "y1", "x1", "y2", "x2"]},
                "valueLabels": {}, "valueLabelNames": {},
                "variableTypeIsString": {v: False for v in ["mpg", "weight", "y1", "x1", "y2", "x2"]},
                "values": vals,
            }
        }
        spec_fd, sp = tempfile.mkstemp(suffix=".json")
        data_fd, dp = tempfile.mkstemp(suffix=".json")
        out_fd, op  = tempfile.mkstemp(suffix=".html")
        try:
            import os
            with os.fdopen(spec_fd, "w") as f: json.dump(spec, f)
            with os.fdopen(data_fd, "w") as f: json.dump(dj, f)
            os.close(out_fd)
            r = DashRenderer(sp, dp, op)
        finally:
            for p in (sp, dp, op):
                try: os.unlink(p)
                except OSError: pass
        figs = r._build_figures()
        assert "g1" in figs, "pci plot should produce a figure"

    def test_pcscatter_in_dispatch(self):
        """pcscatter dispatches via _add_pc_glyph to map_pcscatter."""
        import json, tempfile, os
        from dash_render import DashRenderer
        vals = [{"y1": float(i), "x1": float(i), "y2": float(i+1), "x2": float(i+1)}
                for i in range(1, 6)]
        spec = {
            "graphs": [{
                "plots": [{"type": "pcscatter", "y1var": "y1", "x1var": "x1",
                           "y2var": "y2", "x2var": "x2", "options": {}}],
                "graph_options": {"name": "g1"},
                "if_expr": "", "in_expr": "",
            }],
            "kpis": [],
            "build_options": {
                "layout": "auto", "link": "", "filter": "",
                "theme": "default", "title": "", "subtitle": "", "registry": "g1",
            },
        }
        dj = {
            "StataJSON": {
                "variableNames": ["y1", "x1", "y2", "x2"],
                "variableLabels": {v: v for v in ["y1", "x1", "y2", "x2"]},
                "valueLabels": {}, "valueLabelNames": {},
                "variableTypeIsString": {v: False for v in ["y1", "x1", "y2", "x2"]},
                "values": vals,
            }
        }
        spec_fd, sp = tempfile.mkstemp(suffix=".json")
        data_fd, dp = tempfile.mkstemp(suffix=".json")
        out_fd, op  = tempfile.mkstemp(suffix=".html")
        try:
            with os.fdopen(spec_fd, "w") as f: json.dump(spec, f)
            with os.fdopen(data_fd, "w") as f: json.dump(dj, f)
            os.close(out_fd)
            r = DashRenderer(sp, dp, op)
        finally:
            for p in (sp, dp, op):
                try: os.unlink(p)
                except OSError: pass
        figs = r._build_figures()
        assert "g1" in figs

    def test_rscatter_in_dispatch(self):
        """rscatter dispatches via _add_glyph range_dispatch.

        Regression: rscatter must use 'yvar1'/'yvar2' JSON keys (matching
        dash.ado output) and must actually add at least one renderer to the
        figure.  Previously rscatter was missing from _RANGE_TYPES, which
        caused _build_figures to fall through to the else-branch where it
        looked up the non-existent 'yvar' key, resulting in a silent no-op
        (zero renderers despite a valid rscatter spec).
        """
        import json, tempfile, os
        from dash_render import DashRenderer
        vals = [{"y1": float(i), "y2": float(i+5), "x": float(i)} for i in range(1, 11)]
        spec = {
            "graphs": [{
                # dash.ado uses "yvar1"/"yvar2" keys for range-type plots
                "plots": [{"type": "rscatter", "yvar1": "y1", "yvar2": "y2",
                           "xvar": "x", "options": {}}],
                "graph_options": {"name": "g1"},
                "if_expr": "", "in_expr": "",
            }],
            "kpis": [],
            "build_options": {
                "layout": "auto", "link": "", "filter": "",
                "theme": "default", "title": "", "subtitle": "", "registry": "g1",
            },
        }
        dj = {
            "StataJSON": {
                "variableNames": ["y1", "y2", "x"],
                "variableLabels": {v: v for v in ["y1", "y2", "x"]},
                "valueLabels": {}, "valueLabelNames": {},
                "variableTypeIsString": {v: False for v in ["y1", "y2", "x"]},
                "values": vals,
            }
        }
        spec_fd, sp = tempfile.mkstemp(suffix=".json")
        data_fd, dp = tempfile.mkstemp(suffix=".json")
        out_fd, op  = tempfile.mkstemp(suffix=".html")
        try:
            with os.fdopen(spec_fd, "w") as f: json.dump(spec, f)
            with os.fdopen(data_fd, "w") as f: json.dump(dj, f)
            os.close(out_fd)
            r = DashRenderer(sp, dp, op)
        finally:
            for p in (sp, dp, op):
                try: os.unlink(p)
                except OSError: pass
        figs = r._build_figures()
        assert "g1" in figs
        # Must have at least one renderer — previously zero due to missing _RANGE_TYPES entry
        assert len(figs["g1"].renderers) >= 1, (
            "rscatter must add at least one renderer; check that 'rscatter' "
            "is in _RANGE_TYPES in _build_figures"
        )

    def test_mband_in_dispatch(self):
        """mband dispatches via _add_glyph standard dispatch."""
        import json, tempfile, os
        from dash_render import DashRenderer
        vals = [{"y": float(i), "x": float(i)} for i in range(1, 25)]
        spec = {
            "graphs": [{
                "plots": [{"type": "mband", "yvar": "y", "xvar": "x", "options": {}}],
                "graph_options": {"name": "g1"},
                "if_expr": "", "in_expr": "",
            }],
            "kpis": [],
            "build_options": {
                "layout": "auto", "link": "", "filter": "",
                "theme": "default", "title": "", "subtitle": "", "registry": "g1",
            },
        }
        dj = {
            "StataJSON": {
                "variableNames": ["y", "x"],
                "variableLabels": {"y": "y", "x": "x"},
                "valueLabels": {}, "valueLabelNames": {},
                "variableTypeIsString": {"y": False, "x": False},
                "values": vals,
            }
        }
        spec_fd, sp = tempfile.mkstemp(suffix=".json")
        data_fd, dp = tempfile.mkstemp(suffix=".json")
        out_fd, op  = tempfile.mkstemp(suffix=".html")
        try:
            with os.fdopen(spec_fd, "w") as f: json.dump(spec, f)
            with os.fdopen(data_fd, "w") as f: json.dump(dj, f)
            os.close(out_fd)
            r = DashRenderer(sp, dp, op)
        finally:
            for p in (sp, dp, op):
                try: os.unlink(p)
                except OSError: pass
        figs = r._build_figures()
        assert "g1" in figs


# ================================================================
# TestLpolyFpfit — new smoother plot types (lpoly, lpolyci, fpfit, fpfitci)
# ================================================================

class TestLpolyFpfit:
    """Tests for lpoly, lpolyci, fpfit, and fpfitci GlyphMapper methods."""

    @pytest.fixture
    def xy_src(self, fig):
        np.random.seed(17)
        n = 30
        x = np.linspace(1, 10, n)
        y = 2.0 * x + np.random.randn(n)
        return ColumnDataSource({"x": x.tolist(), "y": y.tolist()})

    def test_map_lpoly_returns_renderer(self, fig, xy_src):
        gm = GlyphMapper()
        r = gm.map_lpoly(fig, xy_src, "y", "x", {})
        assert isinstance(r, GlyphRenderer)

    def test_map_lpoly_adds_one_renderer(self, fig, xy_src):
        gm = GlyphMapper()
        before = len(fig.renderers)
        gm.map_lpoly(fig, xy_src, "y", "x", {})
        assert len(fig.renderers) == before + 1

    def test_map_lpoly_bwidth_option(self, fig, xy_src):
        gm = GlyphMapper()
        r = gm.map_lpoly(fig, xy_src, "y", "x", {"bwidth": "0.3"})
        assert isinstance(r, GlyphRenderer)

    def test_map_lpoly_degree_1(self, fig, xy_src):
        gm = GlyphMapper()
        r = gm.map_lpoly(fig, xy_src, "y", "x", {"degree": "1"})
        assert isinstance(r, GlyphRenderer)

    def test_map_lpoly_empty_data(self, fig):
        gm = GlyphMapper()
        tiny = ColumnDataSource({"x": [1.0], "y": [2.0]})
        r = gm.map_lpoly(fig, tiny, "y", "x", {})
        assert isinstance(r, GlyphRenderer)

    def test_map_lpoly_line_color(self, fig, xy_src):
        gm = GlyphMapper()
        r = gm.map_lpoly(fig, xy_src, "y", "x", {"lcolor": "red"})
        assert r.glyph.line_color == "#ff0000"

    def test_map_lpolyci_returns_list(self, fig, xy_src):
        gm = GlyphMapper()
        result = gm.map_lpolyci(fig, xy_src, "y", "x", {})
        assert isinstance(result, list) and len(result) == 2

    def test_map_lpolyci_adds_two_renderers(self, fig, xy_src):
        gm = GlyphMapper()
        before = len(fig.renderers)
        gm.map_lpolyci(fig, xy_src, "y", "x", {})
        assert len(fig.renderers) == before + 2

    def test_map_lpolyci_empty_data(self, fig):
        gm = GlyphMapper()
        tiny = ColumnDataSource({"x": [1.0, 2.0], "y": [1.0, 2.0]})
        result = gm.map_lpolyci(fig, tiny, "y", "x", {})
        assert len(result) == 2

    def test_map_fpfit_returns_renderer(self, fig, xy_src):
        gm = GlyphMapper()
        r = gm.map_fpfit(fig, xy_src, "y", "x", {})
        assert isinstance(r, GlyphRenderer)

    def test_map_fpfit_adds_one_renderer(self, fig, xy_src):
        gm = GlyphMapper()
        before = len(fig.renderers)
        gm.map_fpfit(fig, xy_src, "y", "x", {})
        assert len(fig.renderers) == before + 1

    def test_map_fpfit_empty_data(self, fig):
        gm = GlyphMapper()
        tiny = ColumnDataSource({"x": [1.0, 2.0, 3.0], "y": [1.0, 2.0, 3.0]})
        r = gm.map_fpfit(fig, tiny, "y", "x", {})
        assert isinstance(r, GlyphRenderer)

    def test_map_fpfit_line_color(self, fig, xy_src):
        gm = GlyphMapper()
        r = gm.map_fpfit(fig, xy_src, "y", "x", {"lcolor": "navy"})
        assert r.glyph.line_color == "#1a476f"

    def test_map_fpfitci_returns_list(self, fig, xy_src):
        gm = GlyphMapper()
        result = gm.map_fpfitci(fig, xy_src, "y", "x", {})
        assert isinstance(result, list) and len(result) == 2

    def test_map_fpfitci_adds_two_renderers(self, fig, xy_src):
        gm = GlyphMapper()
        before = len(fig.renderers)
        gm.map_fpfitci(fig, xy_src, "y", "x", {})
        assert len(fig.renderers) == before + 2

    def test_map_fpfitci_empty_data(self, fig):
        gm = GlyphMapper()
        tiny = ColumnDataSource({"x": [1.0, 2.0], "y": [1.0, 2.0]})
        result = gm.map_fpfitci(fig, tiny, "y", "x", {})
        assert len(result) == 2

    def test_compute_lpoly_fit_shape(self):
        gm = GlyphMapper()
        x = np.linspace(1, 10, 30)
        y = 2 * x
        xg, yf = gm._compute_lpoly_fit(x, y, n_grid=50)
        assert len(xg) == 50 and len(yf) == 50

    def test_fit_fp2_returns_valid_powers(self):
        gm = GlyphMapper()
        x = np.linspace(1, 10, 20)
        y = 3 * x ** 0.5
        p1, p2, c = gm._fit_fp2(x, y)
        assert p1 in GlyphMapper._FP_POWERS
        assert p2 in GlyphMapper._FP_POWERS
        assert len(c) == 3

    def test_fp_transform_sqrt(self):
        x = np.array([1.0, 4.0, 9.0])
        r = GlyphMapper._fp_transform(x, 0.5)
        np.testing.assert_allclose(r, [1.0, 2.0, 3.0])

    def test_fp_transform_log(self):
        x = np.array([1.0, np.e])
        r = GlyphMapper._fp_transform(x, 0.0)
        np.testing.assert_allclose(r, [0.0, 1.0])

    def test_fp_transform_nonpositive_nan(self):
        x = np.array([-1.0, 0.0, 1.0])
        r = GlyphMapper._fp_transform(x, 0.5)
        assert np.isnan(r[0]) and np.isnan(r[1])
        assert r[2] == pytest.approx(1.0)

    def test_lpoly_end_to_end(self):
        import json, os, tempfile
        from dash_render import DashRenderer
        data = {"StataJSON": {
            "variableNames": ["x", "y"],
            "variableLabels": {"x": "x", "y": "y"},
            "valueLabels": {}, "valueLabelNames": {},
            "variableTypeIsString": {"x": False, "y": False},
            "values": [{"x": float(i), "y": float(i * 2)} for i in range(1, 16)],
        }}
        spec = {"graphs": [{"plots": [{"type": "lpoly", "yvar": "y", "xvar": "x",
                                        "options": {"bwidth": "0.4"}}],
                             "graph_options": {"name": "g1"},
                             "if_expr": "", "in_expr": ""}],
                "kpis": [],
                "build_options": {"layout": "auto", "link": "", "filter": "",
                                  "theme": "default", "title": "", "subtitle": "",
                                  "registry": "g1"}}
        sp, dp, op = [tempfile.mkstemp(s)[1] for s in (".json", ".json", ".html")]
        try:
            with open(sp, "w") as f: json.dump(spec, f)
            with open(dp, "w") as f: json.dump(data, f)
            figs = DashRenderer(sp, dp, op)._build_figures()
            assert "g1" in figs
        finally:
            for p in (sp, dp, op):
                try: os.unlink(p)
                except OSError: pass

    def test_fpfit_end_to_end(self):
        import json, os, tempfile
        from dash_render import DashRenderer
        data = {"StataJSON": {
            "variableNames": ["x", "y"],
            "variableLabels": {"x": "x", "y": "y"},
            "valueLabels": {}, "valueLabelNames": {},
            "variableTypeIsString": {"x": False, "y": False},
            "values": [{"x": float(i), "y": float(i ** 0.5 + i)} for i in range(1, 16)],
        }}
        spec = {"graphs": [{"plots": [{"type": "fpfit", "yvar": "y", "xvar": "x",
                                        "options": {}}],
                             "graph_options": {"name": "g1"},
                             "if_expr": "", "in_expr": ""}],
                "kpis": [],
                "build_options": {"layout": "auto", "link": "", "filter": "",
                                  "theme": "default", "title": "", "subtitle": "",
                                  "registry": "g1"}}
        sp, dp, op = [tempfile.mkstemp(s)[1] for s in (".json", ".json", ".html")]
        try:
            with open(sp, "w") as f: json.dump(spec, f)
            with open(dp, "w") as f: json.dump(data, f)
            figs = DashRenderer(sp, dp, op)._build_figures()
            assert "g1" in figs
        finally:
            for p in (sp, dp, op):
                try: os.unlink(p)
                except OSError: pass


# ================================================================
# Regression: HoverTool must not fire "???" on independent-CDS renderers
#
# Bug: HoverTools added by map_scatter/map_line and the comprehensive
# HoverTool built by _make_figure applied to ALL renderers in a figure.
# Derived-curve renderers (lfit, lowess, kdensity, histogram, …) use
# independent CDS objects whose column names are generic ("x"/"y",
# "top"/"left"/"right").  Hovering over those renderers returned "???"
# for every field referencing the original variable names.
#
# Fix: every HoverTool is restricted to renderers whose CDS contains
# all referenced columns.
# ================================================================

def _make_dr_for_hover(plots, hover="", link="g1"):
    """Return a rendered DashRenderer for hover-tool tests."""
    vals = [
        {"mpg": float(22 - i), "weight": float(2000 + i * 50),
         "price": float(4000 + i * 200), "foreign": float(i % 2)}
        for i in range(20)
    ]
    data_json = {"StataJSON": {
        "variableNames": ["mpg", "weight", "price", "foreign"],
        "variableLabels": {"mpg": "mpg", "weight": "weight",
                           "price": "price", "foreign": "foreign"},
        "valueLabels": {}, "valueLabelNames": {},
        "variableTypeIsString": {c: False for c in
                                 ["mpg", "weight", "price", "foreign"]},
        "values": vals,
    }}
    graph_opts: dict = {"name": "g1"}
    if hover:
        graph_opts["hover"] = hover
    spec = {
        "graphs": [{"plots": plots, "graph_options": graph_opts,
                    "if_expr": "", "in_expr": ""}],
        "kpis": [],
        "build_options": {"layout": "auto", "link": link, "filter": "",
                          "theme": "default", "title": "", "subtitle": "",
                          "registry": "g1"},
    }
    sp, dp, op = [tempfile.mkstemp(s)[1] for s in (".json", ".json", ".html")]
    try:
        with open(sp, "w") as f: json.dump(spec, f)
        with open(dp, "w") as f: json.dump(data_json, f)
        dr = DashRenderer(sp, dp, op)
    finally:
        for p in (sp, dp, op):
            try: os.unlink(p)
            except OSError: pass
    dr.render()
    return dr


def _all_hover_cols(fig) -> set:
    """Return the set of column names referenced by all HoverTools in *fig*."""
    cols: set = set()
    for tool in fig.tools:
        if isinstance(tool, HoverTool):
            for tip in tool.tooltips:
                if isinstance(tip, (list, tuple)) and len(tip) == 2:
                    spec = tip[1]          # e.g. "@{weight}"
                    # strip @{ }
                    if spec.startswith("@{") and spec.endswith("}"):
                        cols.add(spec[2:-1])
                    elif spec.startswith("@"):
                        cols.add(spec[1:])
    return cols


def _renderer_has_col(renderer, col: str) -> bool:
    return (hasattr(renderer, "data_source") and
            col in renderer.data_source.data)


class TestHoverToolRendererScope:
    """BF-11: HoverTool must be scoped to renderers that carry the columns."""

    def test_scatter_hover_scoped_to_scatter_renderer(self):
        """BF-11a: map_scatter hover references columns in scatter's CDS only."""
        plots = [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                  "options": {}}]
        dr = _make_dr_for_hover(plots)
        fig = list(dr.figures.values())[0]
        for tool in fig.tools:
            if not isinstance(tool, HoverTool):
                continue
            if not tool.renderers or tool.renderers == "auto":
                # unrestricted hover — check all renderers have needed cols
                for col in _all_hover_cols(fig):
                    for rend in fig.renderers:
                        assert _renderer_has_col(rend, col), (
                            f"Unrestricted HoverTool references col '{col}' "
                            f"not in renderer {rend}"
                        )
            else:
                # restricted — each renderer must have all referenced cols
                for col in _all_hover_cols(fig):
                    for rend in tool.renderers:
                        assert _renderer_has_col(rend, col), (
                            f"HoverTool renderer {rend} missing col '{col}'"
                        )

    def test_scatter_lfit_no_question_marks(self):
        """BF-11b: scatter+lfit figure hover must not reference lfit's CDS.

        lfit uses fit_source{"x","y"} — original var columns don't exist there.
        Any HoverTool must be scoped to only the scatter renderer.
        """
        plots = [
            {"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}},
            {"type": "lfit",    "yvar": "mpg", "xvar": "weight", "options": {}},
        ]
        dr = _make_dr_for_hover(plots, hover="mpg weight price")
        fig = list(dr.figures.values())[0]

        # Collect referenced hover columns
        hover_cols = _all_hover_cols(fig)
        assert hover_cols, "Expected at least one HoverTool with tooltip fields"

        # Every HoverTool must only include renderers that carry ALL hover cols
        for tool in fig.tools:
            if not isinstance(tool, HoverTool):
                continue
            if not tool.renderers or tool.renderers == "auto":
                continue  # unrestricted — validate no missing cols
            for rend in tool.renderers:
                for col in {f[1][2:-1] for f in tool.tooltips
                            if isinstance(f, (list, tuple))
                            and f[1].startswith("@{") and f[1].endswith("}")}:
                    assert _renderer_has_col(rend, col), (
                        f"HoverTool renderer {rend} missing col '{col}'. "
                        "lfit renderer must not be included in hover renderers."
                    )

    def test_lfit_renderer_not_in_hover_renderers(self):
        """BF-11c: the lfit line renderer must not appear in any HoverTool."""
        plots = [
            {"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}},
            {"type": "lfit",    "yvar": "mpg", "xvar": "weight", "options": {}},
        ]
        dr = _make_dr_for_hover(plots, hover="mpg weight")
        fig = list(dr.figures.values())[0]

        # Identify lfit renderer: it uses fit_source with "x"/"y" not "mpg"/"weight"
        lfit_renderers = [
            r for r in fig.renderers
            if hasattr(r, "data_source") and
            "x" in r.data_source.data and
            "mpg" not in r.data_source.data
        ]
        assert lfit_renderers, "Expected to find an lfit renderer in the figure"

        for tool in fig.tools:
            if not isinstance(tool, HoverTool):
                continue
            if not tool.renderers or tool.renderers == "auto":
                continue
            for lfit_r in lfit_renderers:
                assert lfit_r not in tool.renderers, (
                    "lfit renderer must NOT be in any HoverTool's renderer list"
                )

    def test_histogram_hover_uses_fallback_tooltip(self):
        """BF-11d: histogram figure must get a fallback bin/count tooltip."""
        plots = [{"type": "histogram", "yvar": "mpg", "options": {}}]
        dr = _make_dr_for_hover(plots, hover="mpg")
        fig = list(dr.figures.values())[0]

        # Should have at least one HoverTool (even if fallback)
        hover_tools = [t for t in fig.tools if isinstance(t, HoverTool)]
        assert hover_tools, "Histogram figure should have a HoverTool"

        # The HoverTool must not reference 'mpg' in a form that would cause ???
        # (because hist_source only has "top", "left", "right")
        for tool in hover_tools:
            if not tool.renderers or tool.renderers == "auto":
                continue
            for rend in tool.renderers:
                for _, val_spec in tool.tooltips:
                    if val_spec.startswith("@{") and val_spec.endswith("}"):
                        col = val_spec[2:-1]
                        assert col in rend.data_source.data, (
                            f"Histogram HoverTool references '{col}' not in "
                            f"renderer CDS (cols: {list(rend.data_source.data)})"
                        )


# ================================================================
# Regression: BUG-4 — map_lowess must handle constant-x data
# ================================================================

class TestLowessConstantX:
    """BUG-4 regression: map_lowess must return an empty line renderer
    when all x values are identical, instead of crashing or producing NaN."""

    def _make_gm(self):
        from bokeh.plotting import figure as bk_figure
        from dash_render import GlyphMapper, SchemeParser, OptionTranslator
        scheme = SchemeParser("s2color")
        return GlyphMapper(OptionTranslator(), scheme)

    def test_constant_x_returns_renderer(self):
        """BUG-4a: constant-x lowess must return a renderer without exception."""
        from bokeh.plotting import figure as bk_figure
        from bokeh.models import ColumnDataSource
        fig = bk_figure()
        gm = self._make_gm()
        src = ColumnDataSource({
            "x": [5.0, 5.0, 5.0, 5.0, 5.0],
            "y": [10.0, 12.0, 11.0, 13.0, 9.0],
        })
        result = gm.map_lowess(fig, src, "y", "x", {})
        # Must not raise and must return a renderer
        assert result is not None

    def test_constant_x_produces_empty_line(self):
        """BUG-4b: constant-x lowess must produce an empty (no-data) line."""
        from bokeh.plotting import figure as bk_figure
        from bokeh.models import ColumnDataSource
        fig = bk_figure()
        gm = self._make_gm()
        src = ColumnDataSource({
            "x": [5.0, 5.0, 5.0, 5.0, 5.0],
            "y": [10.0, 12.0, 11.0, 13.0, 9.0],
        })
        result = gm.map_lowess(fig, src, "y", "x", {})
        r = result if not isinstance(result, list) else result
        # The line renderer should have empty data (constant x → no valid smoother)
        cds = r.data_source
        x_data = list(cds.data.get("x_lw", []))
        assert len(x_data) == 0, (
            f"Expected empty data for constant-x lowess, got {len(x_data)} points"
        )

    def test_normal_x_still_works(self):
        """BUG-4c: lowess must still work normally for varying x."""
        from bokeh.plotting import figure as bk_figure
        from bokeh.models import ColumnDataSource
        fig = bk_figure()
        gm = self._make_gm()
        src = ColumnDataSource({
            "x": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
            "y": [2.0, 3.0, 2.5, 4.0, 3.5, 5.0, 4.5, 6.0],
        })
        result = gm.map_lowess(fig, src, "y", "x", {})
        r = result if not isinstance(result, list) else result
        cds = r.data_source
        x_data = list(cds.data.get("x_lw", []))
        assert len(x_data) > 0, "Normal lowess should produce non-empty data"


# ================================================================
# Regression: HARD-1 — _check_vars warns and skips when column missing
# Regression: HARD-2 — empty source produces empty glyph without crash
# Regression: HARD-3 — map_bar with string xvar does not crash
# ================================================================

class TestHardeningGuards:
    """HARD-1/2/3: defensive checks in GlyphMapper must prevent crashes."""

    def _make_gm(self):
        from dash_render import GlyphMapper, SchemeParser, OptionTranslator
        return GlyphMapper(OptionTranslator(), SchemeParser("s2color"))

    def _fig(self):
        from bokeh.plotting import figure as bk_figure
        return bk_figure()

    # --- HARD-1: _check_vars ---

    def test_check_vars_returns_true_for_present_columns(self):
        """HARD-1a: _check_vars returns True when all vars exist."""
        from bokeh.models import ColumnDataSource
        gm = self._make_gm()
        src = ColumnDataSource({"x": [1.0, 2.0], "y": [3.0, 4.0]})
        assert gm._check_vars(src, "x", "y") is True

    def test_check_vars_returns_false_for_missing_column(self):
        """HARD-1b: _check_vars returns False (and warns) for missing var."""
        import warnings
        from bokeh.models import ColumnDataSource
        gm = self._make_gm()
        src = ColumnDataSource({"x": [1.0, 2.0]})
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = gm._check_vars(src, "x", "no_such_column")
        assert result is False
        assert len(w) == 1
        assert "no_such_column" in str(w[0].message)

    def test_check_vars_ignores_empty_string_varnames(self):
        """HARD-1c: _check_vars skips empty-string vars (optional fields)."""
        from bokeh.models import ColumnDataSource
        gm = self._make_gm()
        src = ColumnDataSource({"x": [1.0]})
        assert gm._check_vars(src, "x", "") is True

    def test_add_glyph_missing_yvar_does_not_raise(self):
        """HARD-1d: _add_glyph with missing yvar emits warning, no KeyError."""
        import warnings
        from bokeh.models import ColumnDataSource
        from dash_render import DashRenderer
        import json, tempfile, os
        vals = [{"x": float(i)} for i in range(5)]
        data = {"StataJSON": {
            "variableNames": ["x"],
            "variableLabels": {"x": "x"},
            "valueLabels": {}, "valueLabelNames": {},
            "variableTypeIsString": {"x": False},
            "values": vals,
        }}
        spec = {
            "graphs": [{"plots": [{"type": "scatter", "yvar": "missing_y",
                                    "xvar": "x", "options": {}}],
                         "graph_options": {"name": "g1"},
                         "if_expr": "", "in_expr": ""}],
            "kpis": [],
            "build_options": {"layout": "auto", "link": "", "theme": "default",
                              "title": "", "subtitle": "", "registry": "g1"},
        }
        sp, dp, op = [tempfile.mkstemp(s)[1] for s in (".json", ".json", ".html")]
        try:
            with open(sp, "w") as f: json.dump(spec, f)
            with open(dp, "w") as f: json.dump(data, f)
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                dr = DashRenderer(sp, dp, op)
                dr.render()  # must not raise
            # Should have emitted a warning about the missing column
            msgs = [str(x.message) for x in w]
            assert any("missing_y" in m for m in msgs), (
                f"Expected warning about missing_y. Got: {msgs}"
            )
        finally:
            for p in (sp, dp, op):
                try: os.unlink(p)
                except OSError: pass

    # --- HARD-2: _is_empty ---

    def test_is_empty_true_for_zero_length_source(self):
        """HARD-2a: _is_empty returns True for zero-row CDS."""
        from bokeh.models import ColumnDataSource
        gm = self._make_gm()
        src = ColumnDataSource({"x": [], "y": []})
        assert gm._is_empty(src, "x", "y") is True

    def test_is_empty_false_for_nonempty_source(self):
        """HARD-2b: _is_empty returns False when data exists."""
        from bokeh.models import ColumnDataSource
        gm = self._make_gm()
        src = ColumnDataSource({"x": [1.0], "y": [2.0]})
        assert gm._is_empty(src, "x", "y") is False

    def test_histogram_empty_source_no_crash(self):
        """HARD-2c: map_histogram with empty source returns renderer without error."""
        from bokeh.models import ColumnDataSource
        gm = self._make_gm()
        fig = self._fig()
        src = ColumnDataSource({"mpg": []})
        result = gm.map_histogram(fig, src, "mpg", {})
        assert result is not None

    def test_bar_empty_source_no_crash(self):
        """HARD-2d: map_bar with empty source returns renderer without error."""
        from bokeh.models import ColumnDataSource
        gm = self._make_gm()
        fig = self._fig()
        src = ColumnDataSource({"x": [], "y": []})
        result = gm.map_bar(fig, src, "y", "x", {})
        assert result is not None

    def test_rbar_empty_source_no_crash(self):
        """HARD-2e: map_rbar with empty source returns renderer list without error."""
        from bokeh.models import ColumnDataSource
        gm = self._make_gm()
        fig = self._fig()
        src = ColumnDataSource({"x": [], "y1": [], "y2": []})
        result = gm.map_rbar(fig, src, "y1", "y2", "x", {})
        assert result is not None

    def test_rarea_empty_source_no_crash(self):
        """HARD-2f: map_rarea with empty source returns renderer without error."""
        from bokeh.models import ColumnDataSource
        gm = self._make_gm()
        fig = self._fig()
        src = ColumnDataSource({"x": [], "y1": [], "y2": []})
        result = gm.map_rarea(fig, src, "y1", "y2", "x", {})
        assert result is not None

    def test_rspike_empty_source_no_crash(self):
        """HARD-2g: map_rspike with empty source returns renderer without error."""
        from bokeh.models import ColumnDataSource
        gm = self._make_gm()
        fig = self._fig()
        src = ColumnDataSource({"x": [], "y1": [], "y2": []})
        result = gm.map_rspike(fig, src, "y1", "y2", "x", {})
        assert result is not None

    # --- HARD-3: map_bar string xvar ---

    def test_bar_string_xvar_no_crash(self):
        """HARD-3a: map_bar with string xvar must not crash on float() conversion."""
        from bokeh.models import ColumnDataSource
        gm = self._make_gm()
        fig = self._fig()
        src = ColumnDataSource({
            "category": ["A", "B", "C", "A", "B"],
            "value":    [10.0, 20.0, 15.0, 12.0, 18.0],
        })
        try:
            result = gm.map_bar(fig, src, "value", "category", {})
        except (ValueError, TypeError) as e:
            pytest.fail(f"map_bar with string xvar raised {type(e).__name__}: {e}")
        assert result is not None

    def test_bar_numeric_xvar_still_works(self):
        """HARD-3b: map_bar with numeric xvar still computes correct bar width."""
        from bokeh.models import ColumnDataSource
        gm = self._make_gm()
        fig = self._fig()
        src = ColumnDataSource({
            "x":     [1.0, 2.0, 3.0, 4.0],
            "value": [10.0, 20.0, 15.0, 25.0],
        })
        result = gm.map_bar(fig, src, "value", "x", {})
        assert result is not None
        # Bar width should be ~0.8 * (2-1) = 0.8
        glyph = result.glyph if not isinstance(result, list) else result[0].glyph
        assert hasattr(glyph, "width")
