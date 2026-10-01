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
        # Arrow annotations go into fig.center (not fig.renderers): ONE,
        # drawing a head on each row of the shaft's source (10 in pc_cds).
        arrow_layouts = fig.select({"type": Arrow})
        assert len(arrow_layouts) == 1
        assert _heads_drawn(fig) == len(pc_cds.data["x1"])

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
        # Only 2 clean rows → 2 heads
        assert _heads_drawn(tfig) == 2

    def test_pcarrow_lcolor_option(self, fig, pc_cds, gm):
        """P4-14: lcolor option is applied to the Arrow annotation line color."""
        result = gm.map_pcarrow(fig, pc_cds, "y1", "x1", "y2", "x2", {"lcolor": "magenta"})
        from bokeh.models import Arrow
        arrow_layouts = fig.select({"type": Arrow})
        assert arrow_layouts[0].line_color == "#ff00ff"


def _heads_drawn(fig):
    """The heads a figure's Arrow annotations draw: one per row of the
    source each reads its coordinates from (the shaft's copy), or one for
    an annotation of literal coordinates."""
    from bokeh.models import Arrow
    n = 0
    for a in fig.select({"type": Arrow}):
        f = getattr(a.x_start, "field", None) or (
            a.x_start.get("field") if isinstance(a.x_start, dict) else None)
        n += len(a.source.data[f]) if f else 1
    return n


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
        assert len(fig.select({"type": Arrow})) == 1
        assert _heads_drawn(fig) == len(pc_cds.data["x1"])

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
        assert len(tfig.select({"type": Arrow})) == 1
        assert _heads_drawn(tfig) == 2

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

    # twoway mspline (WP-18) is the cross medians of bands() equal-width
    # x bands joined by a natural cubic spline, drawn at the K knots plus
    # n() points between each adjacent pair.  Until WP-18 dash drew a
    # PCHIP through every observation on a fixed 200-point grid, which was
    # 14 mpg from Stata's curve on auto; these four tests pinned that.
    # The knots and the spline are recomputed here independently of
    # dash_render, so the tests do not grade the renderer by itself.

    @staticmethod
    def _knots(x, y, bands):
        """Cross medians of *bands* equal-width bands, the last one closed."""
        x = np.asarray(x, float)
        y = np.asarray(y, float)
        edges = np.linspace(x.min(), x.max(), bands + 1)
        kx, ky = [], []
        for i in range(bands):
            hi = (x <= edges[i + 1]) if i == bands - 1 else (x < edges[i + 1])
            inside = (x >= edges[i]) & hi
            if inside.any():
                kx.append(np.median(x[inside]))
                ky.append(np.median(y[inside]))
        return np.array(kx), np.array(ky)

    @staticmethod
    def _natural_spline(kx, ky, xs):
        """The natural cubic spline through (kx, ky), solved directly."""
        k = len(kx)
        h = np.diff(kx)
        a = np.zeros((k, k))
        rhs = np.zeros(k)
        a[0, 0] = a[-1, -1] = 1.0          # zero curvature at both ends
        for i in range(1, k - 1):
            a[i, i - 1] = h[i - 1]
            a[i, i] = 2.0 * (h[i - 1] + h[i])
            a[i, i + 1] = h[i]
            rhs[i] = 6.0 * ((ky[i + 1] - ky[i]) / h[i]
                            - (ky[i] - ky[i - 1]) / h[i - 1])
        m = np.linalg.solve(a, rhs)
        out = np.empty(len(xs))
        for j, xv in enumerate(xs):
            i = min(max(int(np.searchsorted(kx, xv, side="right")) - 1, 0), k - 2)
            dl, dr = xv - kx[i], kx[i + 1] - xv
            out[j] = (m[i] * dr ** 3 / (6 * h[i]) + m[i + 1] * dl ** 3 / (6 * h[i])
                      + (ky[i] / h[i] - m[i] * h[i] / 6) * dr
                      + (ky[i + 1] / h[i] - m[i + 1] * h[i] / 6) * dl)
        return out

    def test_mspline_draws_k_minus_1_times_n_plus_k_points(self, fig, ts_cds, gm):
        """P4-33: (K-1)*n + K points, n() defaulting to 10.

        The fixture's 30 evenly spaced t fill all of the default
        round(min(10*log10(30), sqrt(30))) = 5 bands, so K = 5 and the
        default curve has 45 points; n() and bands() move the count.
        """
        default_bands = int(round(min(10 * math.log10(30), math.sqrt(30))))
        assert default_bands == 5
        result = gm.map_mspline(fig, ts_cds, "yval", "t", {})
        assert len(result[0].data_source.data["x_sp"]) == 4 * 10 + 5
        result = gm.map_mspline(figure(), ts_cds, "yval", "t", {"n": "4"})
        assert len(result[0].data_source.data["x_sp"]) == 4 * 4 + 5
        result = gm.map_mspline(figure(), ts_cds, "yval", "t",
                                {"bands": "3", "n": "1"})
        assert len(result[0].data_source.data["x_sp"]) == 2 * 1 + 3

    def test_mspline_spans_the_first_to_the_last_knot(self, fig, ts_cds, gm):
        """P4-34: the curve runs from the first band's median x to the last's.

        It does NOT reach the data's own ends, which is what twoway
        draws: the end points are cross medians, not observations.
        """
        t = np.asarray(ts_cds.data["t"], float)
        y = np.asarray(ts_cds.data["yval"], float)
        kx, _ = self._knots(t, y, 5)
        result = gm.map_mspline(fig, ts_cds, "yval", "t", {})
        src_x = np.asarray(result[0].data_source.data["x_sp"], float)
        assert src_x[0] == pytest.approx(kx[0], abs=1e-12)
        assert src_x[-1] == pytest.approx(kx[-1], abs=1e-12)
        assert src_x[0] > t.min() and src_x[-1] < t.max()

    def test_mspline_drops_nan(self, gm):
        """P4-35: a NaN observation is dropped and changes nothing else.

        The four usable rows get the default max(round(min(10*log10(4),
        sqrt(4))), min(4, 2)) = 2 bands, knots (0.5, 0.5) and (3.5, 3.5),
        and with two knots Stata plots the knots alone -- the same curve as
        the four rows without the NaN one.
        """
        from bokeh.models.glyphs import Line
        df = pd.DataFrame({
            "t": [0.0, 1.0, float("nan"), 3.0, 4.0],
            "y": [0.0, 1.0, float("nan"), 3.0, 4.0],
        })
        result = gm.map_mspline(figure(), ColumnDataSource(df), "y", "t", {})
        assert isinstance(result[0].glyph, Line)
        d = result[0].data_source.data
        clean = gm.map_mspline(figure(), ColumnDataSource(df.dropna()),
                               "y", "t", {})[0].data_source.data
        assert np.asarray(d["x_sp"], float).tolist() == pytest.approx([0.5, 3.5])
        assert np.asarray(d["y_sp"], float).tolist() == pytest.approx([0.5, 3.5])
        np.testing.assert_array_equal(np.asarray(d["x_sp"], float),
                                      np.asarray(clean["x_sp"], float))
        np.testing.assert_array_equal(np.asarray(d["y_sp"], float),
                                      np.asarray(clean["y_sp"], float))

    def test_mspline_insufficient_points_returns_empty_renderer(self, gm):
        """P4-36: mspline on one valid point draws that point, as twoway
        mspline's serset holds it (BUGS.md, S3 batch; measured 24sep2026),
        and on none an empty line renderer."""
        from bokeh.models.glyphs import Line
        df = pd.DataFrame({"t": [1.0], "y": [1.0]})
        cds = ColumnDataSource(df)
        tfig = figure()
        result = gm.map_mspline(tfig, cds, "y", "t", {})
        assert isinstance(result[0].glyph, Line)
        assert list(result[0].data_source.data["x_sp"]) == [1.0]
        assert list(result[0].data_source.data["y_sp"]) == [1.0]
        cds0 = ColumnDataSource(pd.DataFrame({"t": [float("nan")],
                                              "y": [1.0]}))
        result = gm.map_mspline(figure(), cds0, "y", "t", {})
        assert len(result[0].data_source.data["x_sp"]) == 0

    def test_mspline_default_line_color(self, fig, ts_cds, gm):
        """P4-37: mspline uses the scheme's default line color (index 0)."""
        result = gm.map_mspline(fig, ts_cds, "yval", "t", {})
        expected_color = gm.scheme.default_color(0, "line")
        assert result[0].glyph.line_color == expected_color

    def test_mspline_lcolor_option_applied(self, fig, ts_cds, gm):
        """P4-38: lcolor option overrides the default spline color."""
        result = gm.map_mspline(fig, ts_cds, "yval", "t", {"lcolor": "magenta"})
        assert result[0].glyph.line_color == "#ff00ff"

    def test_mspline_is_the_natural_spline_through_the_cross_medians(self, gm):
        """P4-39: the curve is the natural cubic spline through the knots.

        It passes through every cross median (every (n+1)-th point is a
        knot) and between them equals a natural cubic spline solved
        directly; the fixture comparison against Stata's own plotted
        points is test_statistical_truth.py::TestMsplineAgainstStata.
        The data are uneven on purpose, so equal-width bands hold unequal
        counts and each knot's median x is not its band's midpoint.
        """
        rng = np.random.default_rng(3)
        t = np.sort(rng.uniform(0, 2 * math.pi, 40) ** 1.3)
        y = np.sin(t) + rng.normal(0, 0.2, 40)
        result = gm.map_mspline(figure(), ColumnDataSource({"t": t, "y": y}),
                                "y", "t", {"bands": "6", "n": "7"})
        x_sp = np.asarray(result[0].data_source.data["x_sp"], float)
        y_sp = np.asarray(result[0].data_source.data["y_sp"], float)
        kx, ky = self._knots(t, y, 6)
        assert len(kx) >= 4, "the test data must give an interior knot or two"
        assert len(x_sp) == (len(kx) - 1) * 7 + len(kx)
        np.testing.assert_allclose(x_sp[::8], kx, rtol=0, atol=1e-12)
        np.testing.assert_allclose(y_sp[::8], ky, rtol=0, atol=1e-12)
        np.testing.assert_allclose(y_sp, self._natural_spline(kx, ky, x_sp),
                                   rtol=0, atol=1e-10)


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
        """P4-44: map_function evaluates correctly for a constant expression.

        Flipped (WP-29 P0.6): Stata's constant is _pi; ``twoway function y
        = pi`` is r(111), so ``pi`` draws nothing."""
        result = gm.map_function(fig, "_pi", (0, 1), 10, {})
        src = result[0].data_source.data
        # The loop below is over the points drawn: none drew, none failed.
        assert len(src["y_fn"]) == 10, len(src["y_fn"])
        for y in src["y_fn"]:
            assert abs(float(y) - math.pi) < 1e-9
        result = gm.map_function(fig, "pi", (0, 1), 10, {})
        assert len(result[0].data_source.data["y_fn"]) == 0

    def test_function_y_values_correct_for_quadratic(self, fig, gm):
        """P4-45: map_function evaluates x*x correctly."""
        result = gm.map_function(fig, "x * x", (0, 4), 5, {})
        src = result[0].data_source.data
        assert len(src["y_fn"]) == 5, len(src["y_fn"])
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
        # np.allclose of two empty arrays is True: an expression the mapper
        # refused drew nothing and passed.  Every point is drawn.
        assert len(src["y_fn"]) == 50, len(src["y_fn"])
        x_vals = np.array(src["x_fn"])
        y_vals = np.array(src["y_fn"])
        assert np.allclose(y_vals, np.cos(x_vals), atol=1e-12)

    def test_function_exp_expression(self, fig, gm):
        """P4-48: map_function evaluates exp(x) correctly."""
        result = gm.map_function(fig, "exp(x)", (0, 2), 10, {})
        src = result[0].data_source.data
        assert len(src["y_fn"]) == 10, len(src["y_fn"])
        x_vals = np.array(src["x_fn"])
        y_vals = np.array(src["y_fn"])
        assert np.allclose(y_vals, np.exp(x_vals), atol=1e-12)

    def test_function_log_expression(self, fig, gm):
        """P4-49: map_function evaluates log(x) correctly for x>0."""
        result = gm.map_function(fig, "log(x)", (1, math.e), 10, {})
        src = result[0].data_source.data
        assert len(src["y_fn"]) == 10, len(src["y_fn"])
        x_vals = np.array(src["x_fn"])
        y_vals = np.array(src["y_fn"])
        assert np.allclose(y_vals, np.log(x_vals), atol=1e-12)

    def test_function_sqrt_expression(self, fig, gm):
        """P4-50: map_function evaluates sqrt(x) correctly."""
        result = gm.map_function(fig, "sqrt(x)", (0, 4), 5, {})
        src = result[0].data_source.data
        assert len(src["y_fn"]) == 5, len(src["y_fn"])
        x_vals = np.array(src["x_fn"])
        y_vals = np.array(src["y_fn"])
        assert np.allclose(y_vals, np.sqrt(x_vals), atol=1e-12)

    def test_function_combined_expression(self, fig, gm):
        """P4-51: map_function evaluates a combined expression correctly."""
        result = gm.map_function(fig, "sin(x) + cos(x)", (0, math.pi), 20, {})
        src = result[0].data_source.data
        assert len(src["y_fn"]) == 20, len(src["y_fn"])
        x_vals = np.array(src["x_fn"])
        y_vals = np.array(src["y_fn"])
        expected = np.sin(x_vals) + np.cos(x_vals)
        assert np.allclose(y_vals, expected, atol=1e-12)

    def test_function_default_line_color(self, fig, gm):
        """P4-52: map_function takes its colour from the scheme.

        This used to require `#d62728' -- matplotlib's red -- which is what
        the mapper drew whatever scheme was set, so a function plot was the
        one layer on the page that ignored the scheme entirely. It takes the
        scheme's first line colour now, as every other layer does.
        """
        result = gm.map_function(fig, "x", (0, 1), 10, {})
        assert result[0].glyph.line_color == \
            gm.scheme.default_color(0, "line")

    def test_function_colour_follows_the_scheme(self, fig):
        """Two schemes, two colours -- a literal would make these equal."""
        import dash_render as _dr
        a = _dr.GlyphMapper(scheme=_dr.SchemeParser("s2color"))
        b = _dr.GlyphMapper(scheme=_dr.SchemeParser("economist"))
        from bokeh.plotting import figure as _figure
        ca = a.map_function(_figure(), "x", (0, 1), 10, {})[0].glyph.line_color
        cb = b.map_function(_figure(), "x", (0, 1), 10, {})[0].glyph.line_color
        assert ca != cb, "the function line is the same under both schemes"

    def test_function_lcolor_option(self, fig, gm):
        """P4-53: lcolor option overrides the default function line color."""
        result = gm.map_function(fig, "x", (0, 1), 10, {"lcolor": "magenta"})
        assert result[0].glyph.line_color == "#ff00ff"

    # ----------------------------------------------------------------
    # Security: the points-free fallback's grammar
    # ----------------------------------------------------------------
    # "Drew nothing" alone proves nothing about the grammar: an evaluation
    # error would also draw nothing.  The verdict is read where it is made
    # -- only a tree _stata_fn_parse accepted reaches _stata_fn_eval (WP-29
    # P0.6; map_function holds no eval() at all) -- through a spy on the
    # evaluator; and each test beside it runs a payload that WOULD draw if
    # the grammar let it through.

    @pytest.fixture
    def evaluated(self, monkeypatch):
        """The expressions map_function handed to its evaluator.

        Flipped (WP-29 P0.6): map_function no longer calls eval(); the
        points-free fallback's acceptance point is _stata_fn_eval, which
        receives only a tree _stata_fn_parse accepted."""
        import dash_render as _dr
        seen = []
        real = _dr._stata_fn_eval

        def spy(tree, x):
            seen.append(tree)
            return real(tree, x)

        monkeypatch.setattr(_dr, "_stata_fn_eval", spy)
        return seen

    def test_the_eval_spy_sees_an_accepted_expression(self, fig, gm,
                                                      evaluated):
        """Guards the guard: a spy that never fires would pass every
        rejection below."""
        result = gm.map_function(fig, "sin(x)", (0, 1), 10, {})
        assert len(result[0].data_source.data["y_fn"]) == 10
        assert len(evaluated) == 1

    def test_function_rejects_import_expression(self, fig, gm, evaluated):
        """P4-54: map_function rejects expressions containing 'import'."""
        result = gm.map_function(fig, "__import__('os')", (0, 1), 10, {})
        # Must not raise; returns empty renderer
        src = result[0].data_source.data
        assert len(src["x_fn"]) == 0
        assert not evaluated, "__import__ reached the evaluator"

    def test_function_rejects_open_builtin(self, fig, gm, evaluated):
        """P4-55: map_function rejects expressions that call 'open'."""
        result = gm.map_function(fig, "open('/etc/passwd')", (0, 1), 10, {})
        src = result[0].data_source.data
        assert len(src["x_fn"]) == 0
        assert not evaluated, "open() reached the evaluator"

    def test_function_rejects_attribute_access(self, fig, gm, evaluated):
        """P4-56: map_function rejects attribute access (e.g., os.getcwd)."""
        result = gm.map_function(fig, "x.real", (0, 1), 10, {})
        src = result[0].data_source.data
        assert len(src["x_fn"]) == 0
        # A call through an attribute of an allowed function draws the
        # function if accepted.
        result = gm.map_function(fig, "sin.__call__(x)", (0, 1), 10, {})
        assert len(result[0].data_source.data["x_fn"]) == 0
        assert not evaluated, "an attribute access reached the evaluator"

    def test_function_rejects_unknown_name(self, fig, gm, evaluated):
        """P4-57: map_function rejects expressions containing disallowed names."""
        result = gm.map_function(fig, "os", (0, 1), 10, {})
        src = result[0].data_source.data
        assert len(src["x_fn"]) == 0
        assert not evaluated, "an unknown name reached the evaluator"

    def test_function_rejects_disallowed_function_call(self, fig, gm,
                                                       evaluated):
        """P4-58: map_function rejects calls to functions not in the whitelist."""
        result = gm.map_function(fig, "eval('1+1')", (0, 1), 10, {})
        src = result[0].data_source.data
        assert len(src["x_fn"]) == 0
        assert not evaluated, "eval() reached the evaluator"

    def test_function_rejects_list_comprehension(self, fig, gm, evaluated):
        """P4-59: map_function rejects list comprehension expressions."""
        result = gm.map_function(fig, "[i for i in range(10)]", (0, 1), 10, {})
        src = result[0].data_source.data
        assert len(src["x_fn"]) == 0
        # One that needs no builtin draws ten points if accepted.
        result = gm.map_function(fig, "[sin(v) for v in x]", (0, 1), 10, {})
        assert len(result[0].data_source.data["x_fn"]) == 0
        assert not evaluated, "a comprehension reached the evaluator"

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

    def test_function_rejects_keyword_args(self, fig, gm, evaluated):
        """P4-62: map_function rejects function calls with keyword arguments."""
        result = gm.map_function(fig, "sin(x=x)", (0, 1), 10, {})
        src = result[0].data_source.data
        assert len(src["x_fn"]) == 0
        # numpy takes out=None, so this one draws sin(x) if accepted.
        result = gm.map_function(fig, "sin(x, out=None)", (0, 1), 10, {})
        assert len(result[0].data_source.data["x_fn"]) == 0
        assert not evaluated, "a keyword argument reached the evaluator"

    def test_function_pi_constant_accessible(self, fig, gm):
        """P4-63: map_function makes Stata's _pi available in expressions.

        Flipped (WP-29 P0.6): twoway refuses ``pi`` (r(111)); its constant
        is ``_pi``."""
        result = gm.map_function(fig, "sin(_pi * x)", (0, 1), 5, {})
        src = result[0].data_source.data
        assert len(src["x_fn"]) == 5
        x_vals = np.array(src["x_fn"])
        y_vals = np.array(src["y_fn"])
        assert np.allclose(y_vals, np.sin(math.pi * x_vals), atol=1e-12)

    def test_function_e_constant_accessible(self, fig, gm):
        """P4-64: Euler's number is reached as Stata reaches it, exp(1).

        Flipped (WP-29 P0.6): twoway refuses ``e`` (r(111)); ``e * x``
        now draws nothing, and ``exp(1) * x`` draws e*x."""
        result = gm.map_function(fig, "e * x", (1, 3), 3, {})
        assert len(result[0].data_source.data["y_fn"]) == 0
        result = gm.map_function(fig, "exp(1) * x", (1, 3), 3, {})
        src = result[0].data_source.data
        assert len(src["y_fn"]) == 3, len(src["y_fn"])
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
