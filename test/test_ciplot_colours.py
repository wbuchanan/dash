"""fitplot() and ciplot() colours as twoway draws them (WP-31 C4b).

Measured in StataNow 19.5 (`graph export' SVG, 16oct2026;
test/fixtures/colour_width_edges_truth.json c4b.<scheme>.<view>,
scripts/extract_colour_width_edges_truth.do), lfitci mpg weight under
s2color and stcolor:

- fitplot(scatter) draws the fit's markers in the layer's p1 colour
  (navy, #1a85ff), as dash drew them;
- ciplot(rarea) is the default band (ci_area fill, ci_arealine outline);
- ciplot(rline) and ciplot(rcap) draw the limits in the band's outline
  colour, gs12 #c0c0c0 under s2color and #e0e0e0 under stcolor, at the
  band's outline width -- not in p1, which dash drew.
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

SCHEMES = ("s2color", "stcolor")
_CHROME = ("", "none", "#eaf2f3", "#ffffff", "#f0f0f0", "#000000")


def _glyphs(mode, options, scheme):
    d = _draw(tp._spec([plot_for("lfitci", options)], {"scheme": scheme}),
              mode)
    return [r.glyph for r in d.figures[0].renderers
            if isinstance(r, GlyphRenderer) and not dr._dash_is_swatch(r)]


def _strokes(key, tag):
    """The distinct stroke colours twoway drew with *tag*, but chrome."""
    return {e[2] for e in TRUTH[key]["elements"]
            if e[0] == tag and e[2] not in _CHROME}


def _fit_colour(scheme):
    return _strokes(f"c4b.{scheme}.default", "path").pop()


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("scheme", SCHEMES)
class TestCiplotColours:
    def test_rline_limits_are_the_bands_outline(self, mode, scheme):
        key = f"c4b.{scheme}.ciplot_rline"
        band = _strokes(key, "path") - {_fit_colour(scheme)}
        assert len(band) == 1
        gs = _glyphs(mode, {"ciplot": "rline"}, scheme)
        lines = [g for g in gs if type(g).__name__ == "Line"]
        assert len(lines) == 3
        assert {g.line_color for g in lines[:2]} == band
        assert lines[2].line_color == _fit_colour(scheme)

    def test_rcap_is_the_bands_outline(self, mode, scheme):
        key = f"c4b.{scheme}.ciplot_rcap"
        band = _strokes(key, "line") - {_fit_colour(scheme)}
        assert len(band) == 1
        gs = _glyphs(mode, {"ciplot": "rcap"}, scheme)
        caps = [g for g in gs if type(g).__name__ in ("Segment", "Scatter")]
        assert caps and {g.line_color for g in caps} == band
        fit = [g for g in gs if type(g).__name__ == "Line"]
        assert fit[-1].line_color == _fit_colour(scheme)

    def test_fitplot_scatter_is_the_layers_colour(self, mode, scheme):
        key = f"c4b.{scheme}.fitplot_scatter"
        fills = {e[1] for e in TRUTH[key]["elements"] if e[0] == "circle"
                 and e[1] not in _CHROME}
        gs = _glyphs(mode, {"fitplot": "scatter"}, scheme)
        sc = [g for g in gs if type(g).__name__ == "Scatter"]
        assert {g.fill_color for g in sc} == fills

    def test_rarea_is_the_default_band(self, mode, scheme):
        a = [(type(g).__name__, getattr(g, "fill_color", None),
              getattr(g, "line_color", None))
             for g in _glyphs(mode, {"ciplot": "rarea"}, scheme)]
        b = [(type(g).__name__, getattr(g, "fill_color", None),
              getattr(g, "line_color", None))
             for g in _glyphs(mode, {}, scheme)]
        assert a == b

    def test_a_colour_option_still_wins(self, mode, scheme):
        gs = _glyphs(mode, {"ciplot": "rline", "alcolor": "red"}, scheme)
        assert {g.line_color for g in gs[:2]} == {"#ff0000"}
