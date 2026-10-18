"""test_colorvar_line_levels.py -- colorvar() on a line plot draws one
line per colour level, as twoway draws it (WP-32, D39 D-15f).

The defect: a Bokeh ``Line`` takes one colour, so dash drew a line, a
tsline, an rline's bounds and connected's line in the colour of its first
point's level (section 15's D-15f); the maintainer ruled the line coloured
as twoway colours it.

Measured 18oct2026 (StataNow 19.5, s2color and stcolor, SVG export of
``twoway line y x, colorvar(z) colordiscrete`` and the same without
colordiscrete, with connect(stairstep) and on connected) on x 1..6,
y 11 2 13 4 15 6:

* z 1 1 2 2 1 3: twoway draws one path per level through that level's
  points in plot order -- level 1 ``M x1 L x2 L x5``, level 2 ``M x3 L
  x4`` -- and level 3's one point draws nothing; it does not colour the
  segments between levels at all;
* z 1 . 2 2 . 3: the missing rows are a path of their own in the
  colormissing() colour (#808080: ``M x2 L x5``);
* connect(stairstep) steps within each level's path;
* the paths are drawn missing first, then the levels in order.

``line_L01`` of test/fixtures/colorvar_types_truth.json (auto, colorvar
rep78 sort) draws five such paths, five strokes.
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest
from bokeh.models import Legend, Line

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from js_runner import requires_node  # noqa: E402
from test_join_order import (_figs_of, _saved, _saved_move,  # noqa: E402
                             _served, _served_figs, _served_move)

MODES = ("saved", "served")

_D = pd.DataFrame({
    "x": [1, 2, 3, 4, 5, 6],
    "y": [11, 2, 13, 4, 15, 6],
    "z": [1, 1, 2, 2, 1, 3],
    "zm": [1, np.nan, 2, 2, np.nan, 3],
    "foreign": [0, 1, 0, 1, 1, 0],
}, dtype=float)
_D["y2"] = _D["y"] + 1


def _pl(ptype="line", y="y", **o):
    if ptype in ("rline", "tsrline"):
        return {"type": ptype, "yvar1": y, "yvar2": "y2", "xvar": "x",
                "options": o}
    return {"type": ptype, "yvar": y, "xvar": "x", "options": o}


def _spec(plots, filt=False):
    bo = {"filter": "foreign, type(dropdown)"} if filt else {}
    return tp._spec(graphs=[("g1", plots, {}, {})], build_options=bo)


def _fig(mode, plots):
    if mode == "saved":
        r = _saved(_spec(plots), _D)
        return _figs_of(r._last_layout_root)[0]
    return _served_figs(_served(_spec(plots), _D))[0]


def _lines(fig):
    return [g for g in fig.renderers if isinstance(g.glyph, Line)]


def _paths(fig):
    """{colour: x values} of each line that has a point, in drawn order."""
    out = []
    for g in _lines(fig):
        xs = [float(v) for v in dr._dash_float_values(g.data_source.data["x"])
              if v == v]
        if xs:
            out.append((g.glyph.line_color, xs))
    return out


def _key_colours(fig):
    """{label: colour} of the colorvar() key."""
    for side in (fig.right, fig.left, fig.above, fig.below, fig.center):
        for m in side:
            if isinstance(m, Legend) and m.name == dr._COLORVAR_LEGEND_NAME:
                return {str(it.label["value"]): it.renderers[0].glyph.fill_color
                        for it in m.items if it.renderers}
    return {}


@pytest.mark.parametrize("mode", MODES)
class TestOneLinePerLevel:

    @pytest.mark.parametrize("ptype", ["line", "tsline", "connected"])
    def test_the_measured_paths(self, mode, ptype):
        fig = _fig(mode, [_pl(ptype, colorvar="z", colordiscrete="yes")])
        keys = _key_colours(fig)
        assert sorted(keys) == ["1", "2", "3"]
        got = sorted((c, tuple(xs)) for c, xs in _paths(fig))
        want = sorted([(keys["1"], (1.0, 2.0, 5.0)),
                       (keys["2"], (3.0, 4.0)), (keys["3"], (6.0,))])
        assert got == want

    def test_a_continuous_colorvar_too(self, mode):
        """Without colordiscrete each level is a bin of the colour bar:
        z's three values three lines."""
        fig = _fig(mode, [_pl(colorvar="z")])
        paths = _paths(fig)
        assert sorted(tuple(xs) for _c, xs in paths) == [
            (1.0, 2.0, 5.0), (3.0, 4.0), (6.0,)]
        assert len({c for c, _xs in paths}) == 3

    def test_missing_levels_are_one_grey_line(self, mode):
        fig = _fig(mode, [_pl(colorvar="zm", colordiscrete="yes")])
        paths = _paths(fig)
        assert ("#808080", [2.0, 5.0]) in paths
        assert paths[0] == ("#808080", [2.0, 5.0])  # drawn first

    def test_stairstep_steps_within_a_level(self, mode):
        fig = _fig(mode, [_pl(colorvar="z", colordiscrete="yes",
                              connect="stairstep")])
        keys = _key_colours(fig)
        [one] = [g for g in _lines(fig) if g.glyph.line_color == keys["1"]]
        d = one.data_source.data
        pts = list(zip(dr._dash_float_values(d["x"]),
                       dr._dash_float_values(d["y"])))
        assert pts == [(1.0, 11.0), (2.0, 11.0), (2.0, 2.0), (5.0, 2.0),
                       (5.0, 15.0)]

    @pytest.mark.parametrize("ptype", ["rline", "tsrline"])
    def test_each_bound_is_one_line_a_level(self, mode, ptype):
        fig = _fig(mode, [_pl(ptype, colorvar="z", colordiscrete="yes")])
        keys = _key_colours(fig)
        got = sorted((c, tuple(xs)) for c, xs in _paths(fig))
        one = [(keys["1"], (1.0, 2.0, 5.0)), (keys["2"], (3.0, 4.0)),
               (keys["3"], (6.0,))]
        assert got == sorted(one + one)

    def test_one_key(self, mode):
        fig = _fig(mode, [_pl("connected", colorvar="z",
                              colordiscrete="yes")])
        legends = [m for side in (fig.right, fig.left, fig.above,
                                  fig.below, fig.center)
                   for m in side if isinstance(m, Legend)
                   and m.name == dr._COLORVAR_LEGEND_NAME]
        assert len(legends) == 1


def _moved_paths(mode, plots):
    spec = _spec(plots, filt=True)
    if mode == "saved":
        r = _saved_move(spec, _D, ("Select", "Foreign"))
        return _paths(_figs_of(r._last_layout_root)[0]), \
            len(_lines(_figs_of(r._last_layout_root)[0]))
    doc, _ = _served_move(spec, _D, ("Select", "Foreign"))
    fig = _served_figs(doc)[0]
    return _paths(fig), len(_lines(fig))


class TestAfterAMove:

    @requires_node
    def test_saved(self):
        self._check("saved")

    def test_served(self):
        self._check("served")

    @staticmethod
    def _check(mode):
        """Foreign keeps x 2 4 5 (z 1 2 1): level 1 is x 2 5, level 2 the
        one point at 4, as twoway draws the Foreign rows; the page keeps
        its lines (the served redraw pairs them by position)."""
        plots = [_pl(colorvar="z", colordiscrete="yes")]
        before = len(_lines(_fig(mode, plots)))
        paths, n = _moved_paths(mode, plots)
        assert n == before
        assert sorted(tuple(xs) for _c, xs in paths) == [(2.0, 5.0),
                                                          (4.0,)]
