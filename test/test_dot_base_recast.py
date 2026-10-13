"""
test_dot_base_recast.py -- dot's base() widens the y axis and recast() on
dot is named, as twoway reads them (WP-31 B5a).

The defect (measured at 4e2bd90): ``dash dot mpg weight, base(50)`` wrote
base to the spec and drew the axis as if it were absent; ``recast()`` on
dot returned from _dash_recast_opt before anything was set, so it was
dropped with no note.

twoway (StataNow 19.5, scripts/extract_rbar_dot_truth.do, fixture
test/fixtures/rbar_dot_truth.json): base(50) widens the y scale to 50
(curmax 50, curmin 10) and leaves the ticks at 10(10)40, as an explicit
bar base() does (yxview.class:1583-1587 register_with_scale); base(0)
widens it to 0.  ``twoway dot mpg weight, recast(line)`` and
``recast(scatter)`` are rc 0 and draw exactly the dot graph (11248
circles, no path), so twoway reads the option and draws nothing of it.

D-03.c, the branch the fixture selects: (iii) rc 0 and the SVG is still
dot's -> recast() on dot is named in the note.  Not taken: (i) the SVG
is the target's -> dot takes the yx recast route; (ii) rc 198 -> refused
with twoway's line.
"""
import json
import os
import re
import sys

import pytest
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure as bk_figure

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")
sys.path.insert(0, _HERE)
sys.path.insert(0, _ROOT)

import dash_render as dr  # noqa: E402
import test_bar_range_geometry as bg  # noqa: E402
import test_mode_parity as tp  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "rbar_dot_truth.json")
with open(_FIXTURE, encoding="utf-8") as _fh:
    _T = json.load(_fh)

_MODES = ("saved", "served")


def _dot(**o):
    return {"type": "dot", "yvar": "mpg", "xvar": "weight", "options": o}


def _map(o):
    gm = bg._gm()
    src = ColumnDataSource({"x": [1.0, 2.0, 3.0], "y": [14.0, 22.0, 30.0]})
    rs = gm.map_dot(bk_figure(), src, "y", "x", o)
    # map_dot returns map_scatter's one renderer (a list on some paths).
    return list(rs) if isinstance(rs, (list, tuple)) else [rs]


def _yfig(mode, tmp_path, **o):
    figs, notes = bg._figs(mode, tmp_path, bg._spec([_dot(**o)]), tp._DF)
    [f] = figs
    return f, notes


def _yticks(f):
    t = f.yaxis[0].ticker
    base = t if hasattr(t, "ticks") else dict(t.args or {}).get("base")
    return list(getattr(base, "ticks", None) or [])


class TestTheFixture:

    def test_twoways_base_widens_the_scale_only(self):
        d = _T["dot"]
        assert d["base_50"]["curmax"] == 50.0
        assert d["base_50"]["curmin"] == d["base_none"]["curmin"]
        assert d["base_0"]["curmin"] == 0.0
        assert d["base_50"]["ticks"] == d["base_none"]["ticks"]


class TestDotBase:

    def test_the_extent_includes_base(self):
        rs = _map({"base": "50"})
        assert rs and all(getattr(r, "_dash_axis_include", None)
                          == {"y": 50.0} for r in rs)
        assert dr._dash_layer_extent(rs, "y_range_name", "default",
                                     role="base") == (50.0, 50.0)
        # No tick input, as bar's explicit base() is not.
        assert dr._dash_layer_extent(rs, "y_range_name", "default") == \
            (14.0, 30.0)

    def test_no_base_no_tag(self):
        for o in ({}, {"base": ""}):
            rs = _map(o)
            assert not any(hasattr(r, "_dash_axis_include") for r in rs), o
            assert dr._dash_layer_extent(rs, "y_range_name", "default",
                                         role="base") is None

    @pytest.mark.parametrize("mode", _MODES)
    def test_both_modes(self, mode, tmp_path):
        f0, _ = _yfig(mode, tmp_path)
        f, notes = _yfig(mode, tmp_path, base="50")
        assert f0.y_range.end < 50
        assert f.y_range.end >= 50
        # The lower end stays at the data's (twoway's curmin 10 both ways);
        # only the plot-region margin, a share of the span, moves it.
        assert 10 < f.y_range.start <= float(tp._DF["mpg"].min())
        assert _yticks(f) == _yticks(f0)
        assert not [n for n in notes if "base" in n], notes

    def test_the_dots_do_not_move(self, tmp_path):
        f0, _ = _yfig("saved", tmp_path)
        f, _ = _yfig("saved", tmp_path, base="50")
        [s0] = bg._glyphs([f0], "Scatter")
        [s] = bg._glyphs([f], "Scatter")
        y0 = s0.data_source.data[s0.glyph.y if isinstance(s0.glyph.y, str)
                                 else s0.glyph.y.field]
        y = s.data_source.data[s.glyph.y if isinstance(s.glyph.y, str)
                               else s.glyph.y.field]
        assert list(y) == list(y0)

    def test_a_horizontal_dot_widens_x(self):
        rs = _map({"base": "50"})
        dr._dash_transpose_layer(None, rs, [], "dot")
        assert all(r._dash_axis_include == {"x": 50.0} for r in rs)


class TestDotRecast:

    def test_the_branch_is_the_fixtures(self):
        p = _T["probes"]
        none = _T["dot"]["base_none"]["svg"]
        for k in ("dot_recast_line", "dot_recast_scatter"):
            assert p[k]["rc"] == 0, k
            assert p[k]["svg"] == none, k          # branch (iii)
        with open(os.path.join(_ROOT, "dash.ado"), encoding="utf-8") as fh:
            ado = fh.read()
        assert '"dot" exit' not in ado
        body = ado[ado.index("program define _dash_recast_opt"):]
        body = body[:body.index("\nend\n")]
        assert re.search(r'if "`ptype\'" == "dot" \{\s*\n\s*'
                         r'_dash_recast_named `_rc_word\'\s*\n\s*exit', body)


class TestTheSavedPlan:

    def test_the_page_reads_base_as_a_base(self):
        """The saved page's re-finish (bconsts) holds base(), so a filter
        move keeps the widened axis."""
        import test_saved_filter_layers as tsfl
        r = tsfl._render(tp._spec([_dot(base="50")],
                                  {"filter": bg._DROPDOWN}))
        plan, _models = dr._dash_axis_plan(r.figures, {})
        plan = json.loads(plan) if isinstance(plan, str) else plan
        bcs = [L["bconsts"] for g in plan for p in g.get("panels", [g])
               for a in p["axes"] if a["letter"] == "y"
               for L in a["layers"]]
        assert [50.0] in bcs, bcs
