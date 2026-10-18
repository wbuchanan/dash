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
