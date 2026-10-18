"""test_scheme_key_readers.py -- the scheme keys BUGS.md "Five scheme keys
are parsed and read by nothing" named, each read as twoway reads it
(WP-32, D39 item 1).

Measured 18oct2026 (StataNow 19.5, SVG export, s2color and a user scheme
``#include s2color`` plus the one key, on the ado-path for the session
only; the SVGs compared with their random clip-path ids masked):

* ``gridringstyle zyx2legend_ring #`` draws ``twoway contour depth
  northing easting`` (sandstone) and ``twoway scatter mpg weight,
  colorvar(price)`` (auto) as s2color with ``clegend(ring(#))`` does, for
  0, 1 and 2; ring 0 puts the colour key inside the plot region at its
  position (3, the right edge), the plot region taking the graph's width;
  1, 2 and s2color's 4 draw alike with no other key on that side, and
  beside ``legend(pos(3))`` (ring 3) ring 2 is drawn between the plot and
  the legend where 4 is drawn outside it.
"""
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import test_mode_parity as tp  # noqa: E402
from test_scheme_resolution import MODES, _draw  # noqa: E402
from test_scheme_review_fixes import _user_scheme  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402


def _keys(fig):
    """{side: [type name, ...]} of the legends and colour bars, in order."""
    out = {}
    for side in ("left", "right", "above", "below", "center"):
        names = [type(m).__name__ for m in getattr(fig, side)
                 if type(m).__name__ in ("Legend", "ColorBar",
                                         "ContourColorBar")]
        if names:
            out[side] = names
    return out


def _bar(fig):
    for side in ("left", "right", "above", "below", "center"):
        for m in getattr(fig, side):
            if type(m).__name__ in ("ColorBar", "ContourColorBar"):
                return side, m
    return None, None


_PLOTS = {
    "scatter": lambda: [plot_for("scatter", {"colorvar": "price"})],
    "contour": lambda: [plot_for("contour")],
}


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("kind", sorted(_PLOTS))
class TestTheColourKeysRing:

    def _side(self, mode, kind, go=None, bo=None):
        spec = tp._spec(_PLOTS[kind](), bo or {}, go or {})
        side, bar = _bar(_draw(spec, mode).figures[0])
        return side, (bar.location if side == "center" else None)

    def test_s2color_draws_it_outside(self, mode, kind):
        assert self._side(mode, kind) == ("right", None)

    def test_clegend_ring_0_draws_it_inside(self, mode, kind):
        assert self._side(mode, kind, {"clegend": "ring(0)"}) == (
            "center", "center_right")
        assert self._side(mode, kind, {"clegend": "ring(0) pos(9)"}) == (
            "center", "center_left")
        assert self._side(mode, kind, {"clegend": "ring(1)"}) == (
            "right", None)

    def test_the_schemes_ring_is_the_default(self, mode, kind, tmp_path,
                                             monkeypatch):
        _user_scheme(tmp_path, monkeypatch, "wzr0.scheme",
                     ["#include s2color", "gridringstyle zyx2legend_ring 0"])
        assert self._side(mode, kind, bo={"scheme": "wzr0"}) == (
            "center", "center_right")
        # clegend(ring()) still wins.
        assert self._side(mode, kind, {"clegend": "ring(2)"},
                          {"scheme": "wzr0"}) == ("right", None)


@pytest.mark.parametrize("mode", MODES)
def test_the_ring_orders_the_key_beside_the_legend(mode):
    plots = [plot_for("scatter", {"colorvar": "price"}),
             plot_for("scatter", {})]
    plots[1]["yvar"] = "price"

    def order(go):
        figs = _draw(tp._spec(plots, {}, dict(go, legend="pos(3)")),
                     mode).figures
        return _keys(figs[0]).get("right")

    # Bokeh draws a side's first model nearest the plot.
    assert order({}) == ["Legend", "ColorBar"]
    assert order({"clegend": "ring(2)"}) == ["ColorBar", "Legend"]


# ---------------------------------------------------------------------------
# `vertical_text text_option': text()'s vertical alignment
# ---------------------------------------------------------------------------
#
# Measured 18oct2026 (s2color, SVG, ``twoway scatter mpg weight, text(30
# 3000 "TXT")``): a user scheme's `vertical_text text_option top', `bottom'
# and `baseline' draw byte for byte as text()'s alignment(top), (bottom)
# and (baseline), at the default size and at size(huge).  The baseline is
# below the point by 0.35 of the text size at middle, 0.20 at top and
# bottom (alike) and 0.50 at baseline; two lines shift together.  dash
# drew every alignment at middle and named alignment().

#: The text's shift from middle's place, up, in units of its size.
_VALIGN_SHIFT = {"middle": 0.0, "top": 0.15, "bottom": 0.15,
                 "baseline": -0.15}


def _text_labels(go, bo, mode, opts=""):
    import test_added_text as tat
    spec = tat._spec([tat._at(30, 3000, ["TXT"], opts)], go=go, bo=bo)
    return tat._all_labels(spec, "saved" if mode == "standalone" else
                           "served")


def _shift_px(lab):
    import test_added_text as tat
    return tat._pt(lab.text_font_size) * 96.0 / 72.0


@pytest.mark.parametrize("mode", MODES)
class TestTextVerticalAlignment:

    @pytest.mark.parametrize("valign", sorted(_VALIGN_SHIFT))
    @pytest.mark.parametrize("size", ["", " size(huge)"])
    def test_alignment_shifts_the_text(self, mode, valign, size):
        (lab,) = _text_labels({}, {"scheme": "s2color"}, mode,
                              f"alignment({valign}){size}")
        want = _VALIGN_SHIFT[valign] * _shift_px(lab)
        assert lab.y_offset == pytest.approx(want, abs=0.01)
        assert lab.x_offset == pytest.approx(0.0, abs=0.01)

    def test_the_schemes_alignment_is_the_default(self, mode, tmp_path,
                                                  monkeypatch):
        _user_scheme(tmp_path, monkeypatch, "wtvb.scheme",
                     ["#include s2color", "vertical_text text_option "
                      "baseline"])
        (lab,) = _text_labels({}, {"scheme": "wtvb"}, mode)
        assert lab.y_offset == pytest.approx(-0.15 * _shift_px(lab),
                                             abs=0.01)
        (lab,) = _text_labels({}, {"scheme": "wtvb"}, mode,
                              "alignment(middle)")
        assert lab.y_offset == pytest.approx(0.0, abs=0.01)

    def test_a_vertical_text_shifts_across(self, mode):
        """orientation(vertical): the shift is along the text's own up,
        which is screen left."""
        (lab,) = _text_labels({}, {"scheme": "s2color"}, mode,
                              "alignment(top) orientation(vertical)")
        assert lab.x_offset == pytest.approx(-0.15 * _shift_px(lab),
                                             abs=0.01)
        assert lab.y_offset == pytest.approx(0.0, abs=0.01)
