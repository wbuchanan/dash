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


# ---------------------------------------------------------------------------
# A continuous colorvar(): twoway's levels, not the colour bar's 256 bins
# (WP-32, BUGS.md "colorvar() on a line splits a continuous variable into
# the colour bar's 256 bins where twoway draws its key's few levels")
# ---------------------------------------------------------------------------

def _continuous(z):
    n = len(z)
    return pd.DataFrame({"x": np.arange(1.0, n + 1), "y": np.arange(n) % 3.0,
                         "z": np.asarray(z, dtype=float),
                         "foreign": np.zeros(n)})


#: Measured 18oct2026 (StataNow 19.5, default scheme, SVG export of
#: ``twoway line y x, colorvar(z)`` on x = 1..101, y = mod(_n, 3), z a
#: float): each path's first and last x and its stroke.  twoway's cuts
#: are its colour key's labels (0 .2 .4 .6 .8 1; 0 20 40 60 80; 1,000
#: 1,500 2,000 2,500), a cut below the variable's minimum dropped, and its
#: levels the intervals (-inf, c0], (c0, c1], ..., (ck, +inf) in the
#: colour rule's n + 1 colours; the minimum, on the first cut, is a level
#: of one point, which draws nothing.  dash split the line by the colour
#: bar's 256 bins: 101 lines for the first case.
_TWOWAY_LEVELS = (
    ("unit", np.float32(np.arange(101) / 100.0),
     [((1, 1), "#0000ff"), ((2, 20), "#00aaff"), ((21, 40), "#00ffaa"),
      ((41, 60), "#00ff00"), ((61, 80), "#aaff00"), ((81, 101), "#ffaa00")]),
    ("by_0_73", np.float32(np.arange(101) * 0.73),
     [((1, 1), "#0000ff"), ((2, 28), "#00cbff"), ((29, 55), "#00ff65"),
      ((56, 83), "#65ff00"), ((84, 101), "#ffcc00")]),
    ("from_1000", np.float32(1000 + np.arange(101) * 13.0),
     [((1, 1), "#0000ff"), ((2, 39), "#00ffff"), ((40, 77), "#00ff00"),
      ((78, 101), "#ffff00")]),
)


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("name,z,want", _TWOWAY_LEVELS,
                         ids=[c[0] for c in _TWOWAY_LEVELS])
def test_a_continuous_colorvar_is_split_at_twoways_levels(mode, name, z,
                                                          want):
    spec = _spec([_pl(colorvar="z")])
    df = _continuous(z)
    if mode == "saved":
        fig = _figs_of(_saved(spec, df)._last_layout_root)[0]
    else:
        fig = _served_figs(_served(spec, df))[0]
    got = sorted(((int(xs[0]), int(xs[-1])), str(c).lower())
                 for c, xs in _paths(fig))
    assert [g[0] for g in got] == [w[0] for w in sorted(want)], (name, got)
    # The colours within 1/255 a channel, as _dash_colorrule_palette is
    # matched to twoway's (dash 0xcc where twoway writes 0xcb).
    for (_r, c), (_rw, cw) in zip(got, sorted(want)):
        assert max(abs(int(c[j:j + 2], 16) - int(cw[j:j + 2], 16))
                   for j in (1, 3, 5)) <= 1, (name, c, cw)


@pytest.mark.parametrize("mode", MODES)
def test_the_key_has_twoways_levels(mode):
    """The key is twoway's: one colour a level, its bins the cuts."""
    from bokeh.models import ColorBar
    spec = _spec([_pl(colorvar="z")])
    df = _continuous(np.float32(1000 + np.arange(101) * 13.0))
    if mode == "saved":
        fig = _figs_of(_saved(spec, df)._last_layout_root)[0]
    else:
        fig = _served_figs(_served(spec, df))[0]
    [bar] = [m for side in (fig.right, fig.left, fig.above, fig.below,
                            fig.center) for m in side
             if isinstance(m, ColorBar)]
    m = bar.color_mapper
    assert [str(c).lower() for c in m.palette] == [
        "#0000ff", "#00ffff", "#00ff00", "#ffff00", "#ff0000"]
    # Five bins of 500 from 500: (.., 1000], (1000, 1500], ... (2500, ..).
    assert (m.low, m.high) == pytest.approx((500.0, 3000.0))
    # A value on a cut takes the level below, as twoway's (c0, c1] does.
    # Flipped (WP-42 CV-8): the bar was the levels' own mapper; it is now
    # its own mapper over twoway's axis range exactly (so a tick on its low
    # end is drawn), and the levels are the line plan's stepped mapper.
    [plan] = [r._dash_cvar for r in fig.renderers
              if (getattr(r, "_dash_cvar", None) or {}).get("kind")
              == "steps"]
    assert plan["bar"] is m and plan["mapper"] is not m
    assert dr.GlyphMapper._colorvar_level_index(
        {"field": "z", "transform": plan["mapper"]},
        [1000.0, 1000.5, 1500.0]).tolist() == [0, 1, 1]
    assert list(bar.ticker.ticks) == [1000.0, 1500.0, 2000.0, 2500.0]


#: Measured 18oct2026 (StataNow 19.5, s2color, SVG export of ``twoway
#: line y x, colorvar(z) zscale(log)`` on x = 1..101, y = mod(_n, 3), z a
#: float): zscale(log) puts the key on a log axis but leaves the levels
#: as they are on a linear one -- the cuts are the key's natscale labels
#: (20 .. 100; 2,000 .. 10,000; 10 .. 50), a label below the minimum
#: dropped, in n + 1 colours of the rule.  dash split the line by the log
#: bar's 256 bins: 101 lines for each case.
_TWOWAY_LOG_LEVELS = (
    ("one_to_101", np.float32(np.arange(1, 102)),
     [((1, 20), "#0000ff"), ((21, 40), "#00cbff"), ((41, 60), "#00ff65"),
      ((61, 80), "#65ff00"), ((81, 100), "#ffcc00"), ((101, 101),
                                                      "#ff0000")]),
    ("decades", np.float32(10 ** (np.arange(101) / 25.0)),
     [((1, 83), "#0000ff"), ((84, 91), "#00cbff"), ((92, 95), "#00ff65"),
      ((96, 98), "#65ff00"), ((99, 101), "#ffcc00")]),
    ("halves", np.float32(1 + np.arange(101) * 0.5),
     [((1, 19), "#0000ff"), ((20, 39), "#00cbff"), ((40, 59), "#00ff65"),
      ((60, 79), "#65ff00"), ((80, 99), "#ffcc00"), ((100, 101),
                                                     "#ff0000")]),
)


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("name,z,want", _TWOWAY_LOG_LEVELS,
                         ids=[c[0] for c in _TWOWAY_LOG_LEVELS])
def test_zscale_log_keeps_twoways_levels(mode, name, z, want):
    spec = tp._spec(graphs=[("g1", [_pl(colorvar="z")], {"zscale": "log"},
                             {})])
    df = _continuous(z)
    if mode == "saved":
        fig = _figs_of(_saved(spec, df)._last_layout_root)[0]
    else:
        fig = _served_figs(_served(spec, df))[0]
    got = sorted(((int(xs[0]), int(xs[-1])), str(c).lower())
                 for c, xs in _paths(fig))
    # A level of one point draws nothing in twoway; dash keeps its source.
    want = sorted(want)
    assert [g[0] for g in got] == [w[0] for w in want], (name, got)
    for (_r, c), (_rw, cw) in zip(got, want):
        assert max(abs(int(c[j:j + 2], 16) - int(cw[j:j + 2], 16))
                   for j in (1, 3, 5)) <= 1, (name, c, cw)


@pytest.mark.parametrize("mode", MODES)
def test_zscale_log_key_is_stepped_on_a_log_bar(mode):
    """The key stays on a log axis, its colours the levels' (each bin the
    colour of the level its centre falls in), ticked at the cuts."""
    from bokeh.models import ColorBar, LogColorMapper
    spec = tp._spec(graphs=[("g1", [_pl(colorvar="z")], {"zscale": "log"},
                             {})])
    df = _continuous(np.float32(10 ** (np.arange(101) / 25.0)))
    if mode == "saved":
        fig = _figs_of(_saved(spec, df)._last_layout_root)[0]
    else:
        fig = _served_figs(_served(spec, df))[0]
    [bar] = [m for side in (fig.right, fig.left, fig.above, fig.below,
                            fig.center) for m in side
             if isinstance(m, ColorBar)]
    m = bar.color_mapper
    assert isinstance(m, LogColorMapper)
    lev = dr.GlyphMapper._colorvar_level_index(
        {"field": "z", "transform": m}, [1.0, 2500.0, 4500.0, 9000.0])
    pal = [str(c).lower() for c in m.palette]
    assert len({pal[k] for k in lev}) == 4
    # The bar holds the five levels the data reach (1 to 10,000), not the
    # rule's 256 steps.
    assert len(set(pal)) == 5
    assert [t for t in bar.ticker.ticks if t > 0] == [
        2000.0, 4000.0, 6000.0, 8000.0, 10000.0]
