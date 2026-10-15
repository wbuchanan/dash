"""
test_edge_title_placement.py -- position() and ring() on the edge titles
t1title() .. r2title() (WP-31 D2b, section 30).

The defect: S27 drew the eight edge titles at their default places and
named position(), ring(), span and orientation() given inside them.

twoway's rule (_fr_title_parse_and_log.ado, numbered titles; measured in
test/fixtures/textbox_truth.json e_*, s2color):

* position(k) moves an edge title to clock k and drops the vertical turn
  of an l or r title: t1title("E", position(6)) is below the plot,
  l1title("E", position(12)) above it and level, t1title("E",
  position(3)) right of it (dash: the nearer horizontal side, as for
  title(), :func:`_dash_textbox_place`);
* ring(k) orders it on its side: t1title("E", ring(8)) is outside the
  title (ring 7); ring(0) is not the plot region for an edge title -- it
  stays where ring 1 is (e_t1_ring0);
* span and nospan are refused, "option(s) t1title_span(yes) not allowed",
  r(198) (dash.ado; test_option_validation.cscript U30-14);
* orientation() turns the text, which a Bokeh Title cannot: named, as on
  title() (test_edge_titles.py::TestNamedSubOptions).
"""
import json
import os
import sys
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

from bokeh.models import Axis, Title  # noqa: E402

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402

MODES = ("saved", "served")

with open(os.path.join(_HERE, "fixtures", "textbox_truth.json"),
          encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)


def _fig(mode, go):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        figs, _c = tp._figures_in(mode, tp._spec(
            [tp._sc()], {"scheme": "s2color"}, go))
    assert len(figs) == 1
    return figs[0], [str(w.message) for w in caught] + list(_c or [])


def _where(fig, key):
    out = []
    for side in ("center", "above", "below", "left", "right"):
        for i, m in enumerate(getattr(fig, side)):
            if key in list(getattr(m, "tags", None) or []):
                out.append((side, i, m))
    assert len(out) == 1, out
    return out[0]


def _svg(case, text="E"):
    return [t for t in TRUTH[case]["texts"] if t["text"] == text][0]


class TestTheFixture:

    def test_twoway_as_measured(self):
        p = TRUTH["e_t1_pos6"]["plot"]
        assert _svg("e_t1_pos6")["y"] > p["y"] + p["h"]
        p = TRUTH["e_l1_pos12"]["plot"]
        e = _svg("e_l1_pos12")
        assert e["y"] < p["y"] and e["rotate"] == 0.0
        p = TRUTH["e_t1_pos3"]["plot"]
        assert _svg("e_t1_pos3")["x"] > p["x"] + p["w"]
        assert _svg("e_t1_ring8")["y"] < _svg("e_t1_ring8", "T")["y"]
        assert _svg("e_t1_ring0") == _svg("e_t1_plain")
        assert TRUTH["e_t1_span"] == {
            "rc": 198, "note": "option(s) t1title_span(yes) not allowed"}


@pytest.mark.parametrize("mode", MODES)
class TestPosition:

    @pytest.mark.parametrize("key,k", [("t1title", 6), ("t1title", 3),
                                       ("l1title", 12), ("r2title", 9),
                                       ("b1title", 11)])
    def test_clock(self, mode, key, k):
        f, caught = _fig(mode, {key: '"E", position(%d)' % k})
        side, _i, m = _where(f, key)
        assert isinstance(m, Title) and m.text == "E"
        assert (side, m.align) == dr._dash_textbox_place(k, "center")
        assert not [w for w in caught if key + "()" in w], caught

    def test_position0_is_inside(self, mode):
        f, _c = _fig(mode, {"t2title": '"E", position(0)'})
        side, i, m = _where(f, "t2title")
        assert (side, i, type(m).__name__) == ("center", 0, "Label")


@pytest.mark.parametrize("mode", MODES)
class TestRing:

    def test_outside_the_title(self, mode):
        f, caught = _fig(mode, {"title": '"T"', "t1title": '"E", ring(8)'})
        above = list(f.above)
        t = [i for i, m in enumerate(above) if "title" in (m.tags or [])]
        e = [i for i, m in enumerate(above) if "t1title" in (m.tags or [])]
        assert f.title is None and len(t) == len(e) == 1
        assert e[0] > t[0], above
        assert not [w for w in caught if "t1title()" in w], caught

    def test_ring0_stays_on_its_side(self, mode):
        f, _c = _fig(mode, {"t1title": '"E", ring(0)', "t2title": '"F"'})
        side, i, _m = _where(f, "t1title")
        assert side == "above"
        assert all(isinstance(m, Axis) for m in f.above[:i])
        assert _where(f, "t2title")[1] > i

    def test_a_left_title_by_ring(self, mode):
        f, _c = _fig(mode, {"l1title": '"E", ring(3)', "l2title": '"F"'})
        side, i, _m = _where(f, "l1title")
        assert side == "left" and _where(f, "l2title")[1] < i
