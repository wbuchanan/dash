"""
test_range_plots.py
Unit tests for GlyphMapper range plot types (rarea, rbar, rspike, rcap, rline, rconnected).

Tests: P2-64, P2-65, P2-66

Run with:  pytest test/test_range_plots.py -v
"""
import sys
import os
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dash_render import GlyphMapper

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, GlyphRenderer


# ================================================================
# Fixtures
# ================================================================

@pytest.fixture
def range_df():
    """Dataset with yvar1, yvar2, xvar for range plot testing."""
    x = np.linspace(0, 10, 20)
    return pd.DataFrame({
        "yvar1": x * 0.5,
        "yvar2": x * 1.5,
        "xvar":  x,
    })


@pytest.fixture
def range_cds(range_df):
    return ColumnDataSource(range_df)


@pytest.fixture
def fig():
    return figure()


@pytest.fixture
def gm():
    return GlyphMapper()


# ================================================================
# P2-64 — rarea produces varea with upper/lower columns
# ================================================================
class TestMapRarea:
    def test_rarea_produces_varea(self, fig, range_cds, gm):
        """P2-64: rarea produces a VArea renderer."""
        from bokeh.models.glyphs import VArea
        result = gm.map_rarea(fig, range_cds, "yvar1", "yvar2", "xvar", {})
        assert isinstance(result, list), "map_rarea must return a list"
        renderer = result[0]
        assert isinstance(renderer, GlyphRenderer)
        assert isinstance(renderer.glyph, VArea), (
            f"Expected VArea glyph, got {type(renderer.glyph).__name__}"
        )

    def test_rarea_uses_correct_columns(self, fig, range_cds, gm):
        """P2-64: rarea VArea references y1 and y2 columns."""
        from bokeh.models.glyphs import VArea
        result = gm.map_rarea(fig, range_cds, "yvar1", "yvar2", "xvar", {})
        renderer = result[0]
        glyph = renderer.glyph
        # y1 and y2 should map to the yvar1 and yvar2 columns (or renamed equivalents)
        y1_col = glyph.y1
        y2_col = glyph.y2
        assert y1_col in renderer.data_source.data or y1_col == "yvar1"
        assert y2_col in renderer.data_source.data or y2_col == "yvar2"


# ================================================================
# P2-65 — rbar produces vbar with bottom/top columns
# ================================================================
class TestMapRbar:
    def test_rbar_produces_vbar(self, fig, range_cds, gm):
        """P2-65: rbar produces a VBar renderer."""
        from bokeh.models.glyphs import VBar
        result = gm.map_rbar(fig, range_cds, "yvar1", "yvar2", "xvar", {})
        assert isinstance(result, list), "map_rbar must return a list"
        renderer = result[0]
        assert isinstance(renderer, GlyphRenderer)
        assert isinstance(renderer.glyph, VBar), (
            f"Expected VBar glyph, got {type(renderer.glyph).__name__}"
        )

    def test_rbar_bottom_top_columns(self, fig, range_cds, gm):
        """P2-65: rbar VBar uses bottom and top columns."""
        from bokeh.models.glyphs import VBar
        result = gm.map_rbar(fig, range_cds, "yvar1", "yvar2", "xvar", {})
        renderer = result[0]
        glyph = renderer.glyph
        # bottom should reference yvar1 (lower bound) and top yvar2 (upper)
        assert glyph.bottom in renderer.data_source.data or glyph.bottom == "yvar1"
        assert glyph.top    in renderer.data_source.data or glyph.top    == "yvar2"


# ================================================================
# P2-66 — rcap produces segment renderer with end caps
# ================================================================
class TestMapRcap:
    def test_rcap_produces_segment(self, fig, range_cds, gm):
        """P2-66: rcap produces at least one Segment renderer (main spike)."""
        from bokeh.models.glyphs import Segment
        renderers = gm.map_rcap(fig, range_cds, "yvar1", "yvar2", "xvar", {})
        # rcap may return a list of renderers (main + caps) or a single renderer
        if isinstance(renderers, (list, tuple)):
            segment_found = any(isinstance(r.glyph, Segment) for r in renderers)
        else:
            segment_found = isinstance(renderers.glyph, Segment)
        assert segment_found, "rcap must include at least one Segment glyph"

    def test_rcap_has_caps(self, fig, range_cds, gm):
        """P2-66: rcap produces horizontal cap marks (at least 2 renderers)."""
        renderers = gm.map_rcap(fig, range_cds, "yvar1", "yvar2", "xvar", {})
        n_renderers = len(renderers) if isinstance(renderers, (list, tuple)) else 1
        # map_rcap always returns exactly [spine, bot_cap, top_cap] — 3 renderers
        assert n_renderers == 3, (
            f"Expected exactly 3 renderers (spine + 2 caps), got {n_renderers}"
        )


# ================================================================
# Additional range plot smoke tests
# ================================================================
class TestRangePlotsSmoke:
    """Smoke tests: each range plot method runs without error."""

    def test_rspike_no_error(self, fig, range_cds, gm):
        from bokeh.models.glyphs import Segment
        renderer = gm.map_rspike(fig, range_cds, "yvar1", "yvar2", "xvar", {})
        r = renderer[0] if isinstance(renderer, (list, tuple)) else renderer
        assert isinstance(r.glyph, Segment)

    def test_rline_no_error(self, fig, range_cds, gm):
        result = gm.map_rline(fig, range_cds, "yvar1", "yvar2", "xvar", {})
        assert result is not None

    def test_rconnected_no_error(self, fig, range_cds, gm):
        result = gm.map_rconnected(fig, range_cds, "yvar1", "yvar2", "xvar", {})
        assert result is not None

    def test_dot_no_error(self, fig, range_cds, gm):
        result = gm.map_dot(fig, range_cds, "yvar1", "xvar", {})
        assert result is not None


# ================================================================
# Regression: BUG-3 — rbar legend color must match fill, not show white
# ================================================================

class TestRbarLegendColor:
    """BUG-3 regression: map_rbar must not use line_color='white' which causes
    the legend swatch to appear white rather than the fill color."""

    def test_rbar_no_white_line_color(self, fig, range_cds, gm):
        """BUG-3: vbar glyph must not have line_color='white'."""
        renderers = gm.map_rbar(fig, range_cds, "yvar1", "yvar2", "xvar", {})
        r = renderers[0] if isinstance(renderers, list) else renderers
        glyph = r.glyph
        # line_color should not be white — it should be transparent (line_alpha=0)
        lc = getattr(glyph, "line_color", None)
        assert lc != "white", (
            "map_rbar must not set line_color='white'; use line_alpha=0 instead "
            "so the legend swatch shows the fill color, not a white border"
        )

    def test_rbar_line_alpha_zero_or_no_border(self, fig, range_cds, gm):
        """BUG-3b: the bar's border is never white.  Flipped (WP-31 E8):
        it was transparent (line_alpha=0); twoway outlines each bar in its
        plot colour (test/fixtures/colour_width_edges_truth.json ol.rbar),
        so the border is the scheme's p1, opaque."""
        renderers = gm.map_rbar(fig, range_cds, "yvar1", "yvar2", "xvar", {})
        r = renderers[0] if isinstance(renderers, list) else renderers
        glyph = r.glyph
        assert glyph.line_color == gm.scheme.p_other_band_styles[0]["line"]
        assert glyph.line_alpha == 1.0
