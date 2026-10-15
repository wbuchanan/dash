"""WP-31 E6: line-width edges (section 33).

``*#`` on a line width multiplied a default that was already floored at
0.3 pt, so ``xline(3000, lwidth(*2))`` under a scheme whose xyline is
vvthin drew twice the floor (0.8 px) where twoway draws the floor
(test/fixtures/axis_look_truth.json, 10 SVG units a point):

* lw_vvthin, lw_star2_vvthin and lw_star10_vvthin all draw 3.0 units: vvthin
  (0.0288 pt) times 2 or 10 is still under the 0.3 pt floor, so twoway
  multiplies the unfloored width and floors after;
* lw_star2_medium draws 17.28 units, twice medium's 8.64;
* lw_bound_10000 is drawn and lw_bound_20000 is r(198) "gm_linewidth must
  be between 0.000 and 1.0e+04" (the refusal is section 32's rules token).

While iterating: ``python3 -m pytest test/test_line_width_edges.py -q``.
"""
import os
import re
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_axis_look_options as tal  # noqa: E402

T = dr.OptionTranslator
_T = tal._T
_MODES = ("saved", "served")


def _xline_width(key):
    return [v["width"] for v in _T[key]["vlines"]
            if 1300 < v["x1"] < 2000 and v["y2"] < 200][0]


class TestTheFixture:
    def test_widths(self):
        assert _xline_width("lw_vvthin") == 3.0
        assert _xline_width("lw_star2_vvthin") == 3.0
        assert _xline_width("lw_star10_vvthin") == 3.0
        assert _xline_width("lw_star2_medium") == pytest.approx(
            2 * _xline_width("lw_medium"))
        assert _T["lw_bound_10000"]["rc"] == 0
        assert (_T["lw_bound_20000"]["rc"], _T["lw_bound_20000"]["log"]) == (
            198, ["gm_linewidth must be between 0.000 and 1.0e+04"])


class TestFloorAfterMultiply:
    def test_sub_floor_default(self):
        assert T.translate_lwidth("*2", default_pt=0.1) == pytest.approx(
            T.line_px(0.2)) == pytest.approx(0.4)
        vv = T._LWIDTH_RS["vvthin"] * T.PT_PER_RS
        assert T.translate_lwidth("*10", default_pt=vv) == pytest.approx(
            _xline_width("lw_star10_vvthin") / 10 * T.PX_PER_PT)

    def test_precedence(self):
        assert T.translate_lwidth("*2", default_px=10.0,
                                  default_pt=0.1) == pytest.approx(0.4)

    def test_px_fallback(self):
        assert T.translate_lwidth("*2", default_px=0.4) == pytest.approx(0.8)
        assert T.translate_lwidth("*2") == pytest.approx(
            T.line_px(2 * T._LWIDTH_RS["medium"] * T.PT_PER_RS))


class TestCallSites:
    def test_no_floored_default(self):
        # The chrome sites whose default is a scheme role pass the role's
        # unfloored points.
        with open(os.path.join(_HERE, "..", "dash_render.py"),
                  encoding="utf-8") as fh:
            src = fh.read()
        for role in ("xyline", "tick", "major_grid", "axisline"):
            assert 'linewidth_pt("%s")' % role in src, role
        calls = re.findall(r"translate_lwidth\(([^)]*line_px\()", src)
        assert not calls, calls

    def test_scheme_points(self):
        s = dr.SchemeParser("s2color")
        assert s.linewidth_pt("xyline") == pytest.approx(0.864)
        assert s.linewidth_pt("tick") == pytest.approx(0.576)
        assert s.linewidth_pt("dots") == pytest.approx(0.0288)
        assert s.linewidth_pt("nosuchrole") == pytest.approx(0.864)


class TestDrawn:
    def _vvthin(self, monkeypatch):
        orig = dr.SchemeParser.linewidth_pt

        def lw(self, role):
            if role == "xyline":
                return T._LWIDTH_RS["vvthin"] * T.PT_PER_RS
            return orig(self, role)
        monkeypatch.setattr(dr.SchemeParser, "linewidth_pt", lw)

    @pytest.mark.parametrize("mode", ["saved"])
    def test_xline_star2(self, mode, monkeypatch):
        self._vvthin(monkeypatch)
        f, _m = tal._figs(mode, {"xline": "3000, lwidth(*2)"})
        from bokeh.models import Span
        sp = [m for m in f.center if isinstance(m, Span)] + \
            [r for r in f.renderers if type(r).__name__ == "Span"]
        widths = [s.line_width for s in sp]
        if not widths:
            from bokeh.models import Arrow
            widths = [a.line_width for a in f.center if isinstance(a, Arrow)]
        assert widths and widths[0] == pytest.approx(
            _xline_width("lw_star2_vvthin") / 10 * T.PX_PER_PT)

    @pytest.mark.parametrize("mode", _MODES)
    def test_xline_star2_medium(self, mode):
        f, _m = tal._figs(mode, {"xline": "3000, lwidth(*2)"})
        from bokeh.models import Span
        widths = [m.line_width for m in list(f.center) + list(f.renderers)
                  if isinstance(m, Span)]
        if not widths:
            from bokeh.models import Arrow
            widths = [a.line_width for a in f.center if isinstance(a, Arrow)]
        assert widths[0] == pytest.approx(
            _xline_width("lw_star2_medium") / 10 * T.PX_PER_PT)

    @pytest.mark.parametrize("mode", _MODES)
    def test_tick_and_grid_defaults(self, mode):
        f, _m = tal._figs(mode, {"ylabel": ", grid tlwidth(*2) glwidth(*2)"})
        s = dr.SchemeParser("s2color")
        ax = tal._axis(f, "y")
        assert ax.major_tick_line_width == pytest.approx(
            T.line_px(2 * s.linewidth_pt("tick")))
        assert tal._grid(f, "y").grid_line_width == pytest.approx(
            T.line_px(2 * s.linewidth_pt("major_grid")))
