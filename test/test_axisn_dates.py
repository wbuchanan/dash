"""Axes 3 to 9 on a date variable, and the t options with axis(3) to
axis(9) (WP-31 section 35, GAPS3 C10e).

twoway's truth is test/fixtures/axisn_date_truth.json
(scripts/extract_axisn_date_truth.do, sysuse sp500):

* a %td variable on yaxis(3) or xaxis(3) labels that axis in dates
  (01jan2001 01apr2001 ... 01jan2002), as on axes 1 and 2;
* tlabel(), ttick(), ttitle(), tscale() and tline() with axis(3) are drawn
  on axis 3, their dates read in the axis's unit (tlabel 01feb2001
  01jun2001 01oct2001; tscale(range(01jan2000 31dec2002)) runs the axis
  from 14,610 to 15,705), and refused on an unused axis 3, r(198);
* tmlabel() and tmtick() with axis(2) read their dates too (01apr2001
  01oct2001 as minor labels on the date axis 2).

dash.ado folds the t options' dates into Stata numbers (_dash_taxis_fold,
the cscript block); here the renderers are given what it writes -- the
axisn object's x entries in the variable's units -- and must draw the
axes 3-9 as date axes in both modes.
"""

import json
import os
import sys
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_FIX = os.path.join(_HERE, "fixtures", "axisn_date_truth.json")
with open(_FIX, encoding="utf-8") as _fh:
    _T = json.load(_fh)

MODES = ("saved", "served")
_W = {"formats": {"when": "%td"}}
_Y3 = [plot_for("scatter"), plot_for("scatter", {"yaxis": "2"},
                                     yvar="price"),
       plot_for("scatter", {"yaxis": "3"}, yvar="when")]
_X3 = [plot_for("scatter"), plot_for("scatter", {"xaxis": "2"},
                                     xvar="price"),
       plot_for("scatter", {"xaxis": "3"}, xvar="when")]
_DAY_MS = 86400000.0
_EPOCH = -3653.0          # 01jan1960 in days from 01jan1970


def _ms(day):
    return (float(day) + _EPOCH) * _DAY_MS


def _fig(mode, plots, go=None):
    from bokeh.models import GlyphRenderer, Plot
    spec = tp._spec(plots, _W, go)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        if mode == "saved":
            r, _w = tp._standalone(spec)
            models = list(r._last_layout_root.references())
        else:
            doc, _w = tp._served(spec)
            models = [m for root in doc.roots for m in root.references()]
    figs = [m for m in models if isinstance(m, Plot)
            and any(isinstance(x, GlyphRenderer) for x in m.renderers)]
    assert len(figs) == 1
    return figs[0], list(_w) + [str(w.message) for w in caught]


def _axis(fig, letter, name):
    from bokeh.models.axes import ContinuousAxis
    kw = letter + "_range_name"
    for side in (("left", "right") if letter == "y" else ("below", "above")):
        for a in getattr(fig, side):
            if isinstance(a, ContinuousAxis) and getattr(a, kw) == name \
                    and "dash_alt_axis" not in (a.tags or ()):
                return a
    return None


class TestTheFixture:
    def test_meta(self):
        assert _T["_meta"]["source"] == "scripts/extract_axisn_date_truth.do"
        assert sorted(_T["_meta"]) == ["born_date", "dash_commit",
                                       "extracted", "source",
                                       "stata_version"]

    def test_twoway(self):
        def col(rec, side, first):
            return [c[1] for c in rec["columns"][side]
                    if c[1] and c[1][0] == first][0]
        assert _T["y3"]["date"]["yscales"]["3"] == [14976.0, 15341.0]
        assert _T["x3"]["tscale"]["xscales"]["3"] == [14610.0, 15705.0]
        assert col(_T["x3"]["tlabel"], "below", "01feb2001") == [
            "01feb2001", "01jun2001", "01oct2001"]
        assert col(_T["x3"]["tmlabel2"], "above", "01apr2001") == [
            "01apr2001", "01oct2001"]
        assert _T["x3"]["tunused"]["rc"] == 198


@pytest.mark.parametrize("mode", MODES)
class TestADateOnAxisThree:
    def test_y3_is_a_date_axis(self, mode):
        from bokeh.models import DatetimeAxis
        fig, _n = _fig(mode, _Y3)
        ax = _axis(fig, "y", "y3")
        assert isinstance(ax, DatetimeAxis)
        rng = fig.extra_y_ranges["y3"]
        lo, hi = _ms(15340), _ms(15349)
        assert rng.start <= lo and rng.end >= hi
        assert rng.end - rng.start < 3 * (hi - lo)

    def test_x3_is_a_date_axis(self, mode):
        from bokeh.models import DatetimeAxis
        fig, _n = _fig(mode, _X3)
        assert isinstance(_axis(fig, "x", "x3"), DatetimeAxis)

    def test_the_axis_options_read_dates(self, mode):
        """What dash.ado writes for tlabel(), tline() and tscale() with
        axis(3): Stata days, read in the axis's unit."""
        go = {"axisn": {"x3": {"label": "15342 15346",
                               "scale": "range(15330 15360)",
                               "title": "TT3"}}}
        fig, notes = _fig(mode, _X3, go)
        ax = _axis(fig, "x", "x3")
        ticks = sorted(float(t) for t in dr._dash_axis_majors(ax))
        assert ticks == [_ms(15342), _ms(15346)]
        rng = fig.extra_x_ranges["x3"]
        assert rng.start <= _ms(15330) and rng.end >= _ms(15360)
        assert ax.axis_label == "TT3"
        assert not [n for n in notes if "not a date" in n.lower()
                    or "axis(3)" in n], notes

    def test_a_number_axis_three_is_unchanged(self, mode):
        """Guard: axis 3 of numbers stays a linear axis."""
        from bokeh.models import DatetimeAxis
        fig, _n = _fig(mode, _Y3[:2] + [plot_for(
            "scatter", {"yaxis": "3"}, yvar="rep")])
        assert not isinstance(_axis(fig, "y", "y3"), DatetimeAxis)


class TestTheHelper:
    def test_extra_date_axes(self):
        got = dr._dash_extra_date_axes(_X3, {"when": "td"},
                                       {"when": "%td"})
        assert got == {"x3": ("when", "%td", "td")}
        assert dr._dash_extra_date_axes(_X3, {}, {}) == {}
