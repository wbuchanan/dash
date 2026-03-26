"""
test_phase4_plots.py
Unit tests for GlyphMapper Phase 4 plot types:
  pcspike, pcarrow, pcbarrow, tsline, tsrline, mspline, map_function

Tests: P4-01 through P4-70

Run with:  pytest test/test_phase4_plots.py -v
"""
import sys
import os
import math
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dash_render import GlyphMapper, DashRenderer

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, GlyphRenderer


# ================================================================
# Fixtures
# ================================================================

@pytest.fixture
def pc_df():
    """Paired-coordinate dataset: four columns for (x1,y1) → (x2,y2)."""
    np.random.seed(7)
    n = 10
    return pd.DataFrame({
        "x1": np.random.uniform(0, 5, n),
        "y1": np.random.uniform(0, 5, n),
        "x2": np.random.uniform(5, 10, n),
        "y2": np.random.uniform(5, 10, n),
    })


@pytest.fixture
def pc_cds(pc_df):
    return ColumnDataSource(pc_df)


@pytest.fixture
def ts_df():
    """Time-series dataset with two y-series and a time axis."""
    t = np.linspace(0, 4 * math.pi, 30)
    return pd.DataFrame({
        "t":    t,
        "y1":   np.sin(t),
        "y2":   np.cos(t),
        "yval": np.sin(t) + 0.5,
    })


@pytest.fixture
def ts_cds(ts_df):
    return ColumnDataSource(ts_df)


@pytest.fixture
def fig():
    return figure()


@pytest.fixture
def gm():
    return GlyphMapper()


# ================================================================
# P4-01  pcspike returns a list with one Segment GlyphRenderer
# ================================================================
class TestMapPcspike:
    def test_pcspike_returns_list(self, fig, pc_cds, gm):
        """P4-01: map_pcspike returns a list."""
        result = gm.map_pcspike(fig, pc_cds, "y1", "x1", "y2", "x2", {})
        assert isinstance(result, list), "map_pcspike must return a list"

    def test_pcspike_contains_glyph_renderer(self, fig, pc_cds, gm):
        """P4-02: map_pcspike list contains at least one GlyphRenderer."""
        result = gm.map_pcspike(fig, pc_cds, "y1", "x1", "y2", "x2", {})
        assert len(result) >= 1
        assert isinstance(result[0], GlyphRenderer)

    def test_pcspike_glyph_is_segment(self, fig, pc_cds, gm):
        """P4-03: map_pcspike uses a Segment glyph."""
        from bokeh.models.glyphs import Segment
        result = gm.map_pcspike(fig, pc_cds, "y1", "x1", "y2", "x2", {})
        assert isinstance(result[0].glyph, Segment), (
            f"Expected Segment glyph, got {type(result[0].glyph).__name__}"
        )

    def test_pcspike_segment_columns(self, fig, pc_cds, gm):
        """P4-04: Segment glyph references the correct paired-coordinate columns."""
        from bokeh.models.glyphs import Segment
        result = gm.map_pcspike(fig, pc_cds, "y1", "x1", "y2", "x2", {})
        glyph = result[0].glyph
        assert glyph.x0 == "x1"
        assert glyph.y0 == "y1"
        assert glyph.x1 == "x2"
        assert glyph.y1 == "y2"

    def test_pcspike_drops_nan_rows(self, fig, gm):
        """P4-05: map_pcspike silently drops rows with NaN in any coordinate."""
        df = pd.DataFrame({
            "x1": [1.0, 2.0, float("nan"), 4.0],
            "y1": [1.0, float("nan"), 3.0, 4.0],
            "x2": [5.0, 6.0, 7.0, 8.0],
            "y2": [5.0, 6.0, 7.0, 8.0],
        })
        cds = ColumnDataSource(df)
        result = gm.map_pcspike(figure(), cds, "y1", "x1", "y2", "x2", {})
        src_data = result[0].data_source.data
        # Only rows 0 and 3 are complete; length of each column should be 2
        assert len(src_data["x1"]) == 2

    def test_pcspike_lcolor_option_applied(self, fig, pc_cds, gm):
        """P4-06: lcolor option is applied to the segment line color."""
        result = gm.map_pcspike(fig, pc_cds, "y1", "x1", "y2", "x2", {"lcolor": "red"})
        assert result[0].glyph.line_color == "#ff0000"

    def test_pcspike_lwidth_option_applied(self, fig, pc_cds, gm):
        """P4-07: lwidth option is applied to the segment line width."""
        result = gm.map_pcspike(fig, pc_cds, "y1", "x1", "y2", "x2", {"lwidth": "thick"})
        assert result[0].glyph.line_width == 2.5


# ================================================================
# P4-08  pcarrow returns a list with one Segment GlyphRenderer
# ================================================================
class TestMapPcarrow:
    def test_pcarrow_returns_list(self, fig, pc_cds, gm):
        """P4-08: map_pcarrow returns a list."""
        result = gm.map_pcarrow(fig, pc_cds, "y1", "x1", "y2", "x2", {})
        assert isinstance(result, list)

    def test_pcarrow_contains_glyph_renderer(self, fig, pc_cds, gm):
        """P4-09: map_pcarrow list contains at least one GlyphRenderer (segment)."""
        result = gm.map_pcarrow(fig, pc_cds, "y1", "x1", "y2", "x2", {})
        assert len(result) >= 1
        assert isinstance(result[0], GlyphRenderer)

    def test_pcarrow_segment_glyph(self, fig, pc_cds, gm):
        """P4-10: The returned renderer uses a Segment glyph (the arrow shaft)."""
        from bokeh.models.glyphs import Segment
        result = gm.map_pcarrow(fig, pc_cds, "y1", "x1", "y2", "x2", {})
        assert isinstance(result[0].glyph, Segment)

    def test_pcarrow_adds_arrow_layouts(self, fig, pc_cds, gm):
        """P4-11: map_pcarrow adds Arrow layout annotations to the figure."""
        from bokeh.models import Arrow
        gm.map_pcarrow(fig, pc_cds, "y1", "x1", "y2", "x2", {})
        # Arrow annotations go into fig.center (not fig.renderers)
        arrow_layouts = fig.select({"type": Arrow})
        # One Arrow per data row (10 rows in pc_cds)
        assert len(arrow_layouts) == len(pc_cds.data["x1"])

    def test_pcarrow_uses_open_head(self, fig, pc_cds, gm):
        """P4-12: Arrow annotations use OpenHead arrowheads."""
        from bokeh.models import Arrow, OpenHead
        gm.map_pcarrow(fig, pc_cds, "y1", "x1", "y2", "x2", {})
        arrow_layouts = fig.select({"type": Arrow})
        for arrow in arrow_layouts:
            assert isinstance(arrow.end, OpenHead)

    def test_pcarrow_drops_nan_rows(self, fig, gm):
        """P4-13: map_pcarrow drops NaN rows before rendering."""
        from bokeh.models import Arrow
        df = pd.DataFrame({
            "x1": [1.0, float("nan"), 3.0],
            "y1": [1.0, 2.0, 3.0],
            "x2": [4.0, 5.0, 6.0],
            "y2": [4.0, 5.0, 6.0],
        })
        cds = ColumnDataSource(df)
        tfig = figure()
        result = gm.map_pcarrow(tfig, cds, "y1", "x1", "y2", "x2", {})
        # Only 2 clean rows → 2 Arrow annotations
        arrow_layouts = tfig.select({"type": Arrow})
        assert len(arrow_layouts) == 2

    def test_pcarrow_lcolor_option(self, fig, pc_cds, gm):
        """P4-14: lcolor option is applied to the Arrow annotation line color."""
        result = gm.map_pcarrow(fig, pc_cds, "y1", "x1", "y2", "x2", {"lcolor": "navy"})
        from bokeh.models import Arrow
        arrow_layouts = fig.select({"type": Arrow})
        assert arrow_layouts[0].line_color == "#1a476f"


# ================================================================
# P4-15  pcbarrow returns a list with one Segment GlyphRenderer
# ================================================================
class TestMapPcbarrow:
    def test_pcbarrow_returns_list(self, fig, pc_cds, gm):
        """P4-15: map_pcbarrow returns a list."""
        result = gm.map_pcbarrow(fig, pc_cds, "y1", "x1", "y2", "x2", {})
        assert isinstance(result, list)

    def test_pcbarrow_contains_segment(self, fig, pc_cds, gm):
        """P4-16: map_pcbarrow list contains a Segment GlyphRenderer."""
        from bokeh.models.glyphs import Segment
        result = gm.map_pcbarrow(fig, pc_cds, "y1", "x1", "y2", "x2", {})
        assert isinstance(result[0].glyph, Segment)

    def test_pcbarrow_adds_arrow_layouts(self, fig, pc_cds, gm):
        """P4-17: map_pcbarrow adds Arrow layout annotations."""
        from bokeh.models import Arrow
        gm.map_pcbarrow(fig, pc_cds, "y1", "x1", "y2", "x2", {})
        arrow_layouts = fig.select({"type": Arrow})
        assert len(arrow_layouts) == len(pc_cds.data["x1"])

    def test_pcbarrow_uses_normal_head_on_both_ends(self, fig, pc_cds, gm):
        """P4-18: pcbarrow uses NormalHead on both start and end of each Arrow."""
        from bokeh.models import Arrow, NormalHead
        gm.map_pcbarrow(fig, pc_cds, "y1", "x1", "y2", "x2", {})
        arrow_layouts = fig.select({"type": Arrow})
        for arrow in arrow_layouts:
            assert isinstance(arrow.end, NormalHead), (
                f"Expected NormalHead at end, got {type(arrow.end).__name__}"
            )
            assert isinstance(arrow.start, NormalHead), (
                f"Expected NormalHead at start, got {type(arrow.start).__name__}"
            )

    def test_pcbarrow_drops_nan_rows(self, fig, gm):
        """P4-19: map_pcbarrow drops NaN rows before rendering."""
        from bokeh.models import Arrow
        df = pd.DataFrame({
            "x1": [1.0, 2.0, float("nan")],
            "y1": [1.0, 2.0, 3.0],
            "x2": [4.0, 5.0, 6.0],
            "y2": [4.0, 5.0, 6.0],
        })
        cds = ColumnDataSource(df)
        tfig = figure()
        gm.map_pcbarrow(tfig, cds, "y1", "x1", "y2", "x2", {})
        arrow_layouts = tfig.select({"type": Arrow})
        assert len(arrow_layouts) == 2

    def test_pcbarrow_differs_from_pcarrow_head_type(self, fig, pc_cds, gm):
        """P4-20: pcbarrow head type (NormalHead) is different from pcarrow (OpenHead)."""
        from bokeh.models import Arrow, NormalHead, OpenHead
        tfig1 = figure()
        tfig2 = figure()
        gm.map_pcarrow(tfig1, pc_cds, "y1", "x1", "y2", "x2", {})
        gm.map_pcbarrow(tfig2, pc_cds, "y1", "x1", "y2", "x2", {})
        pa_arrows = tfig1.select({"type": Arrow})
        pb_arrows = tfig2.select({"type": Arrow})
        assert isinstance(pa_arrows[0].end, OpenHead)
        assert isinstance(pb_arrows[0].end, NormalHead)


# ================================================================
# P4-21  tsline delegates to map_line
# ================================================================
class TestMapTsline:
    def test_tsline_returns_glyph_renderer(self, fig, ts_cds, gm):
        """P4-21: map_tsline returns a GlyphRenderer."""
        result = gm.map_tsline(fig, ts_cds, "yval", "t", {})
        assert isinstance(result, GlyphRenderer)

    def test_tsline_produces_line_glyph(self, fig, ts_cds, gm):
        """P4-22: map_tsline produces a Line glyph (not scatter or bar)."""
        from bokeh.models.glyphs import Line
        result = gm.map_tsline(fig, ts_cds, "yval", "t", {})
        assert isinstance(result.glyph, Line), (
            f"Expected Line glyph, got {type(result.glyph).__name__}"
        )

    def test_tsline_matches_map_line_output(self, fig, ts_cds, gm):
        """P4-23: map_tsline and map_line produce the same glyph type."""
        from bokeh.models.glyphs import Line
        fig2 = figure()
        r1 = gm.map_tsline(fig, ts_cds, "yval", "t", {})
        r2 = gm.map_line(fig2, ts_cds, "yval", "t", {})
        assert isinstance(r1.glyph, Line)
        assert isinstance(r2.glyph, Line)

    def test_tsline_lcolor_option_applied(self, fig, ts_cds, gm):
        """P4-24: lcolor option is propagated through tsline to the Line glyph."""
        result = gm.map_tsline(fig, ts_cds, "yval", "t", {"lcolor": "maroon"})
        assert result.glyph.line_color == "#90353b"

    def test_tsline_sorts_by_x(self, gm):
        """P4-25: tsline sorts by x (time) axis before rendering."""
        from bokeh.models.glyphs import Line
        # Create shuffled time series
        rng = np.random.default_rng(1)
        t = np.arange(10, dtype=float)
        y = np.sin(t)
        idx = rng.permutation(10)
        df = pd.DataFrame({"t": t[idx], "y": y[idx]})
        cds = ColumnDataSource(df)
        tfig = figure()
        r = gm.map_tsline(tfig, cds, "y", "t", {})
        assert isinstance(r.glyph, Line)
        # Source data should be sorted by t
        src_t = list(r.data_source.data["t"])
        assert src_t == sorted(src_t)


# ================================================================
# P4-26  tsrline delegates to map_rline
# ================================================================
class TestMapTsrline:
    def test_tsrline_returns_list(self, fig, ts_cds, gm):
        """P4-26: map_tsrline returns a list."""
        result = gm.map_tsrline(fig, ts_cds, "y1", "y2", "t", {})
        assert isinstance(result, list)

    def test_tsrline_returns_two_renderers(self, fig, ts_cds, gm):
        """P4-27: map_tsrline returns two Line renderers (lower + upper)."""
        result = gm.map_tsrline(fig, ts_cds, "y1", "y2", "t", {})
        assert len(result) == 2

    def test_tsrline_both_are_line_glyphs(self, fig, ts_cds, gm):
        """P4-28: Both renderers returned by tsrline are Line glyphs."""
        from bokeh.models.glyphs import Line
        result = gm.map_tsrline(fig, ts_cds, "y1", "y2", "t", {})
        for r in result:
            assert isinstance(r.glyph, Line)

    def test_tsrline_matches_rline_output_count(self, fig, ts_cds, gm):
        """P4-29: tsrline and rline return the same number of renderers."""
        fig2 = figure()
        r_ts = gm.map_tsrline(fig, ts_cds, "y1", "y2", "t", {})
        r_rl = gm.map_rline(fig2, ts_cds, "y1", "y2", "t", {})
        assert len(r_ts) == len(r_rl)

    def test_tsrline_lcolor_propagates_to_renderers(self, fig, ts_cds, gm):
        """P4-30: lcolor option is propagated to both line renderers."""
        result = gm.map_tsrline(fig, ts_cds, "y1", "y2", "t", {"lcolor": "red"})
        for r in result:
            assert r.glyph.line_color == "#ff0000"


# ================================================================
# P4-31  mspline produces a smooth cubic spline line
# ================================================================
class TestMapMspline:
    def test_mspline_returns_list(self, fig, ts_cds, gm):
        """P4-31: map_mspline returns a list."""
        result = gm.map_mspline(fig, ts_cds, "yval", "t", {})
        assert isinstance(result, list)

    def test_mspline_contains_line_renderer(self, fig, ts_cds, gm):
        """P4-32: map_mspline list contains a Line GlyphRenderer."""
        from bokeh.models.glyphs import Line
        result = gm.map_mspline(fig, ts_cds, "yval", "t", {})
        assert len(result) >= 1
        assert isinstance(result[0].glyph, Line)

    def test_mspline_uses_200_grid_points(self, fig, ts_cds, gm):
        """P4-33: mspline evaluates on a 200-point grid by default."""
        result = gm.map_mspline(fig, ts_cds, "yval", "t", {})
        src_data = result[0].data_source.data
        assert len(src_data["x_ms"]) == 200

    def test_mspline_grid_spans_data_range(self, fig, ts_cds, gm):
        """P4-34: mspline grid spans from data min to max of x."""
        t_min = float(np.min(ts_cds.data["t"]))
        t_max = float(np.max(ts_cds.data["t"]))
        result = gm.map_mspline(fig, ts_cds, "yval", "t", {})
        src_x = result[0].data_source.data["x_ms"]
        assert abs(float(src_x[0]) - t_min) < 1e-9
        assert abs(float(src_x[-1]) - t_max) < 1e-9

    def test_mspline_drops_nan(self, gm):
        """P4-35: mspline silently drops NaN observations."""
        from bokeh.models.glyphs import Line
        df = pd.DataFrame({
            "t": [0.0, 1.0, float("nan"), 3.0, 4.0],
            "y": [0.0, 1.0, float("nan"), 3.0, 4.0],
        })
        cds = ColumnDataSource(df)
        tfig = figure()
        result = gm.map_mspline(tfig, cds, "y", "t", {})
        assert isinstance(result[0].glyph, Line)
        assert len(result[0].data_source.data["x_ms"]) == 200

    def test_mspline_insufficient_points_returns_empty_renderer(self, gm):
        """P4-36: mspline with fewer than 2 valid points returns an empty line renderer."""
        from bokeh.models.glyphs import Line
        df = pd.DataFrame({"t": [1.0], "y": [1.0]})
        cds = ColumnDataSource(df)
        tfig = figure()
        result = gm.map_mspline(tfig, cds, "y", "t", {})
        assert isinstance(result[0].glyph, Line)
        # Empty source
        assert len(result[0].data_source.data["x_ms"]) == 0

    def test_mspline_default_line_color(self, fig, ts_cds, gm):
        """P4-37: mspline uses the expected default green color."""
        result = gm.map_mspline(fig, ts_cds, "yval", "t", {})
        assert result[0].glyph.line_color == "#2ca02c"

    def test_mspline_lcolor_option_applied(self, fig, ts_cds, gm):
        """P4-38: lcolor option overrides the default spline color."""
        result = gm.map_mspline(fig, ts_cds, "yval", "t", {"lcolor": "navy"})
        assert result[0].glyph.line_color == "#1a476f"

    def test_mspline_interpolation_is_smooth(self, gm):
        """P4-39: mspline interpolation is smoother than linear interpolation."""
        # For a sinusoidal curve, PCHIP should match values at input points closely
        t = np.linspace(0, 2 * math.pi, 20)
        y = np.sin(t)
        df = pd.DataFrame({"t": t, "y": y})
        cds = ColumnDataSource(df)
        tfig = figure()
        result = gm.map_mspline(tfig, cds, "y", "t", {})
        x_ms = np.array(result[0].data_source.data["x_ms"])
        y_ms = np.array(result[0].data_source.data["y_ms"])
        # Spline values should closely match sin at interior grid points
        expected = np.sin(x_ms)
        max_err = np.max(np.abs(y_ms - expected))
        assert max_err < 0.01, f"mspline max error {max_err:.6f} exceeds threshold 0.01"


# ================================================================
# P4-40  map_function plots a mathematical expression
# ================================================================
class TestMapFunction:
    def test_function_returns_list(self, fig, gm):
        """P4-40: map_function returns a list."""
        result = gm.map_function(fig, "sin(x)", (0, 3.14159), 100, {})
        assert isinstance(result, list)

    def test_function_contains_line_renderer(self, fig, gm):
        """P4-41: map_function list contains a Line GlyphRenderer."""
        from bokeh.models.glyphs import Line
        result = gm.map_function(fig, "x * x", (0, 10), 100, {})
        assert len(result) >= 1
        assert isinstance(result[0].glyph, Line)

    def test_function_correct_n_points(self, fig, gm):
        """P4-42: map_function evaluates on exactly n_points grid points."""
        result = gm.map_function(fig, "x + 1", (0, 5), 50, {})
        src = result[0].data_source.data
        assert len(src["x_fn"]) == 50

    def test_function_x_range_spans_correctly(self, fig, gm):
        """P4-43: map_function grid spans from x_range[0] to x_range[1]."""
        result = gm.map_function(fig, "x", (2.0, 7.0), 100, {})
        src = result[0].data_source.data
        assert abs(src["x_fn"][0] - 2.0) < 1e-9
        assert abs(src["x_fn"][-1] - 7.0) < 1e-9

    def test_function_y_values_correct_for_constant(self, fig, gm):
        """P4-44: map_function evaluates correctly for a constant expression."""
        result = gm.map_function(fig, "pi", (0, 1), 10, {})
        src = result[0].data_source.data
        for y in src["y_fn"]:
            assert abs(float(y) - math.pi) < 1e-9

    def test_function_y_values_correct_for_quadratic(self, fig, gm):
        """P4-45: map_function evaluates x*x correctly."""
        result = gm.map_function(fig, "x * x", (0, 4), 5, {})
        src = result[0].data_source.data
        x_vals = src["x_fn"]
        y_vals = src["y_fn"]
        for x, y in zip(x_vals, y_vals):
            assert abs(float(y) - float(x) ** 2) < 1e-9

    def test_function_sin_expression(self, fig, gm):
        """P4-46: map_function evaluates sin(x) correctly."""
        result = gm.map_function(fig, "sin(x)", (0, math.pi), 100, {})
        src = result[0].data_source.data
        x_vals = np.array(src["x_fn"])
        y_vals = np.array(src["y_fn"])
        expected = np.sin(x_vals)
        assert np.allclose(y_vals, expected, atol=1e-12)

    def test_function_cos_expression(self, fig, gm):
        """P4-47: map_function evaluates cos(x) correctly."""
        result = gm.map_function(fig, "cos(x)", (0, math.pi), 50, {})
        src = result[0].data_source.data
        x_vals = np.array(src["x_fn"])
        y_vals = np.array(src["y_fn"])
        assert np.allclose(y_vals, np.cos(x_vals), atol=1e-12)

    def test_function_exp_expression(self, fig, gm):
        """P4-48: map_function evaluates exp(x) correctly."""
        result = gm.map_function(fig, "exp(x)", (0, 2), 10, {})
        src = result[0].data_source.data
        x_vals = np.array(src["x_fn"])
        y_vals = np.array(src["y_fn"])
        assert np.allclose(y_vals, np.exp(x_vals), atol=1e-12)

    def test_function_log_expression(self, fig, gm):
        """P4-49: map_function evaluates log(x) correctly for x>0."""
        result = gm.map_function(fig, "log(x)", (1, math.e), 10, {})
        src = result[0].data_source.data
        x_vals = np.array(src["x_fn"])
        y_vals = np.array(src["y_fn"])
        assert np.allclose(y_vals, np.log(x_vals), atol=1e-12)

    def test_function_sqrt_expression(self, fig, gm):
        """P4-50: map_function evaluates sqrt(x) correctly."""
        result = gm.map_function(fig, "sqrt(x)", (0, 4), 5, {})
        src = result[0].data_source.data
        x_vals = np.array(src["x_fn"])
        y_vals = np.array(src["y_fn"])
        assert np.allclose(y_vals, np.sqrt(x_vals), atol=1e-12)

    def test_function_combined_expression(self, fig, gm):
        """P4-51: map_function evaluates a combined expression correctly."""
        result = gm.map_function(fig, "sin(x) + cos(x)", (0, math.pi), 20, {})
        src = result[0].data_source.data
        x_vals = np.array(src["x_fn"])
        y_vals = np.array(src["y_fn"])
        expected = np.sin(x_vals) + np.cos(x_vals)
        assert np.allclose(y_vals, expected, atol=1e-12)

    def test_function_default_line_color(self, fig, gm):
        """P4-52: map_function uses the expected default red color."""
        result = gm.map_function(fig, "x", (0, 1), 10, {})
        assert result[0].glyph.line_color == "#d62728"

    def test_function_lcolor_option(self, fig, gm):
        """P4-53: lcolor option overrides the default function line color."""
        result = gm.map_function(fig, "x", (0, 1), 10, {"lcolor": "navy"})
        assert result[0].glyph.line_color == "#1a476f"

    # ----------------------------------------------------------------
    # Security: AST whitelist enforcement
    # ----------------------------------------------------------------

    def test_function_rejects_import_expression(self, fig, gm):
        """P4-54: map_function rejects expressions containing 'import'."""
        result = gm.map_function(fig, "__import__('os')", (0, 1), 10, {})
        # Must not raise; returns empty renderer
        src = result[0].data_source.data
        assert len(src["x_fn"]) == 0

    def test_function_rejects_open_builtin(self, fig, gm):
        """P4-55: map_function rejects expressions that call 'open'."""
        result = gm.map_function(fig, "open('/etc/passwd')", (0, 1), 10, {})
        src = result[0].data_source.data
        assert len(src["x_fn"]) == 0

    def test_function_rejects_attribute_access(self, fig, gm):
        """P4-56: map_function rejects attribute access (e.g., os.getcwd)."""
        result = gm.map_function(fig, "x.real", (0, 1), 10, {})
        src = result[0].data_source.data
        assert len(src["x_fn"]) == 0

    def test_function_rejects_unknown_name(self, fig, gm):
        """P4-57: map_function rejects expressions containing disallowed names."""
        result = gm.map_function(fig, "os", (0, 1), 10, {})
        src = result[0].data_source.data
        assert len(src["x_fn"]) == 0

    def test_function_rejects_disallowed_function_call(self, fig, gm):
        """P4-58: map_function rejects calls to functions not in the whitelist."""
        result = gm.map_function(fig, "eval('1+1')", (0, 1), 10, {})
        src = result[0].data_source.data
        assert len(src["x_fn"]) == 0

    def test_function_rejects_list_comprehension(self, fig, gm):
        """P4-59: map_function rejects list comprehension expressions."""
        result = gm.map_function(fig, "[i for i in range(10)]", (0, 1), 10, {})
        src = result[0].data_source.data
        assert len(src["x_fn"]) == 0

    def test_function_rejects_syntax_error(self, fig, gm):
        """P4-60: map_function handles syntax errors gracefully (returns empty renderer)."""
        result = gm.map_function(fig, "sin(x", (0, 1), 10, {})
        src = result[0].data_source.data
        assert len(src["x_fn"]) == 0

    def test_function_rejects_empty_expression(self, fig, gm):
        """P4-61: map_function handles empty expression string gracefully."""
        result = gm.map_function(fig, "", (0, 1), 10, {})
        src = result[0].data_source.data
        assert len(src["x_fn"]) == 0

    def test_function_rejects_keyword_args(self, fig, gm):
        """P4-62: map_function rejects function calls with keyword arguments."""
        result = gm.map_function(fig, "sin(x=x)", (0, 1), 10, {})
        src = result[0].data_source.data
        assert len(src["x_fn"]) == 0

    def test_function_pi_constant_accessible(self, fig, gm):
        """P4-63: map_function makes pi constant available in expressions."""
        result = gm.map_function(fig, "sin(pi * x)", (0, 1), 5, {})
        src = result[0].data_source.data
        assert len(src["x_fn"]) == 5
        x_vals = np.array(src["x_fn"])
        y_vals = np.array(src["y_fn"])
        assert np.allclose(y_vals, np.sin(math.pi * x_vals), atol=1e-12)

    def test_function_e_constant_accessible(self, fig, gm):
        """P4-64: map_function makes e constant available in expressions."""
        result = gm.map_function(fig, "e * x", (1, 3), 3, {})
        src = result[0].data_source.data
        x_vals = np.array(src["x_fn"])
        y_vals = np.array(src["y_fn"])
        assert np.allclose(y_vals, math.e * x_vals, atol=1e-12)


# ================================================================
# P4-65  DashRenderer dispatches PC types via _make_figure
# ================================================================
class TestPhase4DispatchIntegration:
    """Integration tests: verify _make_figure correctly dispatches Phase 4 types."""

    def _make_renderer(self, plot_type: str, extra_plot_keys: dict = None) -> DashRenderer:
        """Build a minimal DashRenderer for integration dispatch tests."""
        import json, tempfile, os
        np.random.seed(1)
        n = 10
        df_data = {
            "x1": list(np.linspace(0, 4, n)),
            "y1": list(np.random.uniform(0, 4, n)),
            "x2": list(np.linspace(5, 9, n)),
            "y2": list(np.random.uniform(5, 9, n)),
            "t":  list(np.linspace(0, 4 * math.pi, n)),
            "y":  list(np.sin(np.linspace(0, 4 * math.pi, n))),
            "yb": list(np.cos(np.linspace(0, 4 * math.pi, n))),
        }

        base_plot = {"type": plot_type, "options": {}}
        if extra_plot_keys:
            base_plot.update(extra_plot_keys)

        spec = {
            "graphs": [{
                "graph_options": {"name": "g1", "title": "Test"},
                "plots": [base_plot],
            }],
            "kpis": [],
            "build_options": {"layout": "auto"},
        }
        data_spec = {
            "variableNames": list(df_data.keys()),
            "values": [{k: v[i] for k, v in df_data.items()} for i in range(n)],
            "variableLabels": {},
            "valueLabelNames": {},
            "valueLabels": {},
            "variableTypeIsString": {},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as sf:
            json.dump(spec, sf)
            spec_path = sf.name
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as df_f:
            json.dump(data_spec, df_f)
            data_path = df_f.name

        renderer = DashRenderer(spec_path, data_path)
        os.unlink(spec_path)
        os.unlink(data_path)
        return renderer

    def test_pcspike_dispatched_by_make_figure(self):
        """P4-65: _make_figure dispatches pcspike through _add_pc_glyph."""
        r = self._make_renderer("pcspike", {
            "y1var": "y1", "x1var": "x1", "y2var": "y2", "x2var": "x2",
        })
        # If dispatch works, render() should complete without error
        html_out = r.render()
        assert "bokeh" in html_out.lower()

    def test_pcarrow_dispatched_by_make_figure(self):
        """P4-66: _make_figure dispatches pcarrow through _add_pc_glyph."""
        r = self._make_renderer("pcarrow", {
            "y1var": "y1", "x1var": "x1", "y2var": "y2", "x2var": "x2",
        })
        html_out = r.render()
        assert "bokeh" in html_out.lower()

    def test_pcbarrow_dispatched_by_make_figure(self):
        """P4-67: _make_figure dispatches pcbarrow through _add_pc_glyph."""
        r = self._make_renderer("pcbarrow", {
            "y1var": "y1", "x1var": "x1", "y2var": "y2", "x2var": "x2",
        })
        html_out = r.render()
        assert "bokeh" in html_out.lower()

    def test_tsline_dispatched_by_make_figure(self):
        """P4-68: _make_figure dispatches tsline correctly."""
        r = self._make_renderer("tsline", {"yvar": "y", "xvar": "t"})
        html_out = r.render()
        assert "bokeh" in html_out.lower()

    def test_mspline_dispatched_by_make_figure(self):
        """P4-69: _make_figure dispatches mspline correctly."""
        r = self._make_renderer("mspline", {"yvar": "y", "xvar": "t"})
        html_out = r.render()
        assert "bokeh" in html_out.lower()

    def test_function_dispatched_by_make_figure(self):
        """P4-70: _make_figure dispatches function type correctly."""
        import json, tempfile, os
        n = 5
        df_data = {"x": list(np.linspace(0, 1, n))}
        spec = {
            "graphs": [{
                "graph_options": {"name": "g1", "title": "Test"},
                "plots": [{
                    "type": "function",
                    "expr": "sin(x)",
                    "options": {"range": "0 1", "n": "50"},
                }],
            }],
            "kpis": [],
            "build_options": {"layout": "auto"},
        }
        data_spec = {
            "variableNames": ["x"],
            "values": [{"x": i / (n - 1)} for i in range(n)],
            "variableLabels": {},
            "valueLabelNames": {},
            "valueLabels": {},
            "variableTypeIsString": {},
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as sf:
            json.dump(spec, sf)
            spec_path = sf.name
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as df_f:
            json.dump(data_spec, df_f)
            data_path = df_f.name
        renderer = DashRenderer(spec_path, data_path)
        os.unlink(spec_path)
        os.unlink(data_path)
        html_out = renderer.render()
        assert "bokeh" in html_out.lower()
