"""Every histogram layer is drawn in the scheme's histogram style
(WP-30 P1.4a).

Measured in StataNow 19.5 (`graph export' SVG, 03oct2026;
test/fixtures/scheme_layer_truth.json): twoway fills a histogram in `color
histogram' at `intensity histogram' and outlines it in `color
histogram_line' at `linewidth histogram' (style/shadestyle-histogram.style,
style/linestyle-histogram.style) -- s2color khaki #CAC27E outlined stone
#D7D29E -- and draws a second histogram layer in the same style.  dash drew
the bar p# cycle with a white outline: #1a476f, then #90353b.
"""

import json
import os
import sys

import pytest
from bokeh.models import GlyphRenderer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_scheme_resolution import MODES, _draw, _props_scheme  # noqa: E402
from test_scheme_review_fixes import _user_scheme  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures",
                        "scheme_layer_truth.json")
with open(_FIXTURE, encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)


def _col(v):
    return str(getattr(v, "value", v)).lower()


def _quads(plots, scheme, mode):
    d = _draw(tp._spec(plots, {"scheme": scheme}), mode)
    return [r.glyph for r in d.figures[0].renderers
            if isinstance(r, GlyphRenderer) and not dr._dash_is_swatch(r)
            and type(r.glyph).__name__ == "Quad"]


def _style(q):
    return (_col(q.fill_color), _col(q.line_color),
            round(float(q.fill_alpha), 4), round(float(q.line_alpha), 4))


@pytest.mark.parametrize("mode", MODES)
class TestTheSchemesHistogramStyle:
    def test_the_line_width_is_the_schemes(self, mode):
        """`linewidth histogram': medium under s2color, vthin under
        stcolor (the colours are checked against twoway below)."""
        for name in ("s2color", "stcolor"):
            q = _quads([plot_for("histogram")], name, mode)[0]
            sp = dr.SchemeParser(name)
            assert q.line_width == pytest.approx(sp.histogram_line_width)


class TestTheParser:
    def test_attributes_from_props_alone(self):
        """The served app and fallback() rebuild the scheme from its
        property dict: the histogram style must come from it alone."""
        attrs = ("histogram_color", "histogram_alpha", "histogram_line_color",
                 "histogram_line_alpha", "histogram_intensity",
                 "histogram_line_width", "p_symbol_hollow",
                 "p_symbol_factor", "p_markline_colors")
        bad = []
        for n in sorted(dr.SchemeParser._BUILTIN_NAMES):
            sp = dr.SchemeParser(n)
            rb = _props_scheme(sp._props)
            bad += [(n, a) for a in attrs
                    if getattr(sp, a) != getattr(rb, a)]
        fb, s2 = dr.SchemeParser.fallback(), dr.SchemeParser("s2color")
        bad += [("fallback", a) for a in attrs
                if getattr(fb, a) != getattr(s2, a)]
        assert not bad, bad


# ---------------------------------------------------------------------------
# twoway's own SVG: every histogram probe, one test per mode
# ---------------------------------------------------------------------------

#: A probe's command as dash plots.
_OPTS = {"histogram mpg, fcolor(red)": {"fcolor": "red"},
         "histogram mpg, color(red)": {"color": "red"},
         "histogram mpg, lcolor(blue)": {"lcolor": "blue"},
         "histogram mpg, fcolor(navy)": {"fcolor": "navy"},
         "histogram mpg": {}}


def _twoway_style(p):
    fill = next(e for e in p["elements"]
                if e["kind"] == "rect" and e["fill"] not in (None, "none"))
    line = next(e for e in p["elements"]
                if e["kind"] == "rect" and e["fill"] == "none")
    return (fill["fill"], line["stroke"],
            fill["fill_opacity"] if fill["fill_opacity"] is not None else 1.0,
            line["stroke_opacity"] if line["stroke_opacity"] is not None
            else 1.0)


@pytest.mark.parametrize("mode", MODES)
class TestTwowaysHistogram:
    def test_each_probe(self, mode, tmp_path, monkeypatch):
        """Fill, outline and their opacities equal twoway's on every
        histogram probe (two layers: every layer)."""
        _user_scheme(tmp_path, monkeypatch, "w24h.scheme", [
            "#include s2color", "color histogram red",
            "intensity histogram inten50", "color histogram_line blue",
            "linewidth histogram vthick"])
        bad = []
        for pid, p in sorted(TRUTH["probes"].items()):
            if p["group"] not in ("histogram", "histogram_opt"):
                continue
            n = 2 if p["command"].startswith("(") else 1
            plots = [plot_for("histogram", _OPTS.get(p["command"], {}))] * n
            scheme = ("w24h.scheme" if p["scheme"] == "w24h"
                      else p["scheme"])
            want = _twoway_style(p)
            got = [_style(q) for q in _quads(plots, scheme, mode)]
            if got != [want] * n:
                bad.append(f"{pid}: twoway {want}, dash {got}")
        assert not bad, bad
