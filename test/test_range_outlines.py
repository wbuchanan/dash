"""rarea and rbar outlines from the scheme (WP-31 E8).

Measured in StataNow 19.5 (`graph export' SVG, 16oct2026;
test/fixtures/colour_width_edges_truth.json ol.*,
scripts/extract_colour_width_edges_truth.do): twoway strokes rarea's
polygon in color p# (navy #1a476f under s2color, #90353b under
pstyle(p2), #1a85ff under stcolor) at twice the medium line's width,
clipped to the polygon so its inner half shows -- as wide as `line ...,
lwidth(medium)' (8.64 of 17.28 SVG units) -- and outlines each rbar in
color p# (the fill is that colour at inten80).  dash drew rarea with no
stroke and rbar with an invisible (alpha 0) Bokeh-default line.

rarea's outline is two Lines on the layer's own source, the lower and
upper bounds, styled from SchemeParser.p_other_band_styles (the
linestyle p#other chain, which ends at the same colour and width as
twoway's p#area chain); twoway's closing edges at the two x ends are not
drawn (documented).
"""
import json
import os
import sys

import pytest
from bokeh.models import GlyphRenderer

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_scheme_resolution import MODES, _draw  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

with open(os.path.join(_HERE, "fixtures", "colour_width_edges_truth.json"),
          encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)

T = dr.OptionTranslator
#: dash's pixels per twoway SVG unit (0.1 pt).
PX_PER_UNIT = 0.1 * T.PX_PER_PT


def _stroke(key, tag):
    """(colour, visible width in SVG units) of the probe's stroked shape."""
    for e in TRUTH[key]["elements"]:
        if e[0] == tag and e[2] not in ("", "none", "#eaf2f3", "#ffffff",
                                        "#f0f0f0", "#000000"):
            w = float(e[3])
            return e[2], (w / 2 if e[7] == "clip" else w)
    raise AssertionError(key)


def _renderers(mode, plots, scheme="s2color"):
    d = _draw(tp._spec(plots, {"scheme": scheme}), mode)
    return [r for r in d.figures[0].renderers
            if isinstance(r, GlyphRenderer) and not dr._dash_is_swatch(r)]


def _rarea(mode, options=None, scheme="s2color"):
    return _renderers(mode, [plot_for("rarea", dict(options or {}))], scheme)


@pytest.mark.parametrize("mode", MODES)
class TestRareaOutline:
    @pytest.mark.parametrize("key, options, scheme", [
        ("ol.rarea", {}, "s2color"),
        ("ol.rarea_p2", {"pstyle": "p2"}, "s2color"),
        ("ol.rarea_stcolor", {}, "stcolor")])
    def test_two_outlines(self, mode, key, options, scheme):
        rs = _rarea(mode, options, scheme)
        assert [type(r.glyph).__name__ for r in rs] == ["VArea", "Line",
                                                        "Line"]
        colour, width = _stroke(key, "use")
        # As wide as the scheme's medium line, as twoway's visible half is
        # (ol.line_medium); under stcolor twoway's whole graph is drawn at
        # its 4.5-inch size reference (9.72 units) where dash draws every
        # line at 8.64 -- a size-reference difference outside E8, so there
        # the outline is held to dash's own line.
        line_w = _renderers(mode, [plot_for("line")], scheme)[0].glyph.line_width
        for r in rs[1:]:
            assert "dash_rarea_outline" in r.tags
            assert r.glyph.line_color == colour
            assert r.glyph.line_width == pytest.approx(line_w)
            if scheme == "s2color":
                assert r.glyph.line_width == pytest.approx(
                    width * PX_PER_UNIT)
            assert list(r.glyph.line_dash) == []
            assert r.data_source is rs[0].data_source
        assert {rs[1].glyph.y, rs[2].glyph.y} == {"mpg", "price"}

    def test_alcolor_wins(self, mode):
        rs = _rarea(mode, {"alcolor": "red", "alwidth": "thick"})
        assert len(rs) == 3
        for r in rs[1:]:
            assert r.glyph.line_color == "#ff0000"
            assert r.glyph.line_width > _rarea(mode)[1].glyph.line_width

    def test_lcolor_and_color_reach_it(self, mode):
        assert _rarea(mode, {"lcolor": "red"})[1].glyph.line_color == \
            "#ff0000"
        assert _rarea(mode, {"color": "red"})[1].glyph.line_color == \
            "#ff0000"


@pytest.mark.parametrize("mode", MODES)
class TestRbarOutline:
    @pytest.mark.parametrize("key, options, scheme", [
        ("ol.rbar", {}, "s2color"),
        ("ol.rbar_stcolor", {}, "stcolor")])
    def test_default_outline(self, mode, key, options, scheme):
        rs = _renderers(mode, [plot_for("rbar", options)], scheme)
        g = rs[0].glyph
        colour, width = _stroke(key, "rect")
        assert g.line_color == colour
        assert g.line_alpha == 1.0
        if scheme == "s2color":
            # stcolor's rbar outline is 6.48 units where dash draws
            # linewidth p#bar's 5.76: a width-chain difference outside E8,
            # recorded in the section's hand-back.
            assert g.line_width == pytest.approx(width * PX_PER_UNIT)

    def test_blcolor_wins(self, mode):
        rs = _renderers(mode, [plot_for("rbar", {"blcolor": "red"})])
        assert rs[0].glyph.line_color == "#ff0000"
