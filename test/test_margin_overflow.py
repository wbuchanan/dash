"""A margin() term past double precision, and a unit after the operator
(WP-31 D11b, section 39).

Measured (test/fixtures/region_remainder_truth.json gmargin.*, s2color,
28.8 SVG units per relative unit): graphregion(margin(l+1e400)) draws
the left side at gsize medium, 3.8194 units, whatever it was (stub 393.68
-> 402.84; zero 292.83 -> 402.84), with "(note:  named style . not found
in class gsize, default attributes used)", the other sides untouched;
r+1e400 the same on the right; l=1e400 draws the left side zero, with no
note.  dash drew all four sides zero and named the text.  A unit after
the operator makes the side's sum points (l+3pt: 3.5 + 3 = 6.5 pt, left
gap 357.92; l+5pt: 8.5 pt, 377.84), which dash already drew (guarded).
"""
import json
import os
import sys
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr

_FIX = os.path.join(_HERE, "fixtures", "region_remainder_truth.json")
_P = json.load(open(_FIX))["probes"]
_MED = 3.8194444444444446


def _sides(text, start):
    dr._dash_reset_notes()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        sides, noted = dr._dash_margin_sides(text, list(start))
    return sides, noted, [str(x.message) for x in w]


def _left_units(pid, base="gmargin.zero"):
    return (_P[pid]["gaps"]["left"] - _P[base]["gaps"]["left"]) / 28.8


class TestTheFixture:
    def test_overflow_is_medium(self):
        assert abs(_left_units("gmargin.l+1e400") - _MED) < 0.01
        assert abs(_left_units("gmargin.zero_l+1e400") - _MED) < 0.01
        assert _P["gmargin.l+1e400"]["notes"] == [
            "(note:  named style . not found in class gsize, default "
            "attributes used)"]
        assert _P["gmargin.l+1e400"]["gaps"]["right"] == \
            _P["gmargin.stub"]["gaps"]["right"]

    def test_assign_overflow_is_zero(self):
        assert abs(_left_units("gmargin.l=1e400")) < 0.01
        assert _P["gmargin.l=1e400"]["notes"] == []
        assert _P["gmargin.1e400_1_1_1"]["gaps"]["left"] == \
            _P["gmargin.zero"]["gaps"]["left"]
        assert _P["gmargin.1e400_1_1_1"]["notes"] == []

    def test_points(self):
        assert abs(_left_units("gmargin.l+3pt") - 6.5 / 2.88) < 0.01
        assert abs(_left_units("gmargin.l+5pt") - 8.5 / 2.88) < 0.01


class TestTheReading:
    @pytest.mark.parametrize("text,start,want", [
        ("l+1e400", [3.5] * 4, [_MED, 3.5, 3.5, 3.5]),
        ("r+1e400", [3.5] * 4, [3.5, _MED, 3.5, 3.5]),
        ("l+1e400", [0.0] * 4, [_MED, 0.0, 0.0, 0.0]),
        ("l+1e400 r+5", [3.5] * 4, [_MED, 8.5, 3.5, 3.5]),
    ])
    def test_overflow_is_medium_with_the_note(self, text, start, want):
        sides, noted, msgs = _sides(text, start)
        assert noted is None
        assert [round(v, 6) for v in sides] == [round(v, 6) for v in want]
        assert any("named style . not found in class gsize" in m
                   for m in msgs), msgs

    def test_assign_overflow_is_zero_silently(self):
        sides, noted, msgs = _sides("l=1e400", [3.5] * 4)
        assert noted is None and sides == [0.0, 3.5, 3.5, 3.5]
        sides, noted, msgs2 = _sides("1e400 1 1 1", [3.5] * 4)
        assert noted is None and sides == [0.0, 1.0, 1.0, 1.0]
        msgs = msgs + msgs2
        assert not [m for m in msgs if "gsize" in m], msgs

    @pytest.mark.parametrize("text,pt", [("l+3pt", 6.5), ("l+5pt", 8.5)])
    def test_points_guard(self, text, pt):
        sides, _n, _m = _sides(text, [3.5] * 4)
        assert abs(sides[0] - pt / 2.88) < 1e-9


class TestBothModes:
    """graphregion(margin(l+1e400)) moves the left border as
    margin(l+0.3194) does from medium, in both modes."""

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_left_border(self, mode):
        import test_tabs_layout_edges as T

        def border(go):
            sp = T._spec(["g1"])
            sp["graphs"][0]["graph_options"].update(go)
            roots, msgs = T._root(mode, sp)
            from bokeh.models import Plot
            f = [m for r in roots for m in r.select({"type": Plot})][0]
            return (f.min_border_left, f.min_border_right), msgs

        got, msgs = border({"graphregion": "margin(l+1e400)"})
        want, _ = border({"graphregion": "margin(l=%r)" % _MED})
        assert got == want, (got, want)
        assert not [m for m in msgs if "l+1e400" in m], msgs
