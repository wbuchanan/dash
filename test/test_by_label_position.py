"""
test_by_label_position.py -- the graph's subtitle(, position() ring())
places every by() panel label as twoway places it (WP-31 D3b).

dash named position() and ring() on a by() graph's subtitle() and drew
each panel label above its panel.  twoway gives each panel its label as
the panel's subtitle(), so the graph's subtitle(, position()) moves it
(test/fixtures/by_remainder_truth.json, probes ``sub_pos*`` and
``sub_ring*``): 12, 11 and 1 o'clock above the plot region (centred, left,
right), 6, 7 and 5 below it, 9 and 3 at its bottom left and right corner;
ring(0) fills the plot region with the label's box and writes the label at
its bottom, at the clock's horizontal; a ring above 0 changes nothing.
by()'s own subtitle() is the overall subtitle and leaves the labels alone
(``byin_pos5_ring0``).
"""

import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import test_by_axes_keys as tk  # noqa: E402
import test_by_remainder as tr  # noqa: E402
from by_panel_probe import panel_label_title  # noqa: E402

from conftest import group_by_params  # noqa: E402

_MODES = ("saved", "served")
_BUILT = {}
#: Every test of one mode reads that mode's one build (``_build``): on one
#: worker it is built once.
xdist_group_of = group_by_params("by_label_position", "mode")

#: graph name -> the graph's subtitle() (by(foreign)).
_SUBS = {
    "p12": ", position(12)", "p11": ", position(11)", "p1": ", position(1)",
    "p6": ", position(6)", "p7": ", position(7)", "p5": ", position(5)",
    "p9": ", position(9)", "p3": ", position(3)",
    "r1p12": ", ring(1) position(12)", "r2p6": ", ring(2) position(6)",
    "r0p5": ", position(5) ring(0)", "r0p12": ", position(12) ring(0)",
    "r0nobox": ", position(5) ring(0) nobox",
    "r0p1": ", position(1) ring(0)", "r0p9": ", position(9) ring(0)",
    "r0p6": ", position(6) ring(0)", "r0p0": ", position(0)",
    "r0p1nob": ", position(1) ring(0) nobexpand",
}

#: ring(0) probe -> the Label anchor twoway's text takes (all at the
#: region's bottom, the clock's horizontal; nobexpand at the compass).
_RING0 = {"r0p5": "bottom_right", "r0p12": "bottom_center",
          "r0p1": "bottom_right", "r0p9": "bottom_left",
          "r0p6": "bottom_center", "r0p0": "bottom_center"}

#: probe -> (side, align) of the label, read from the fixture below.
_WANT = {"p12": ("above", "center"), "p11": ("above", "left"),
         "p1": ("above", "right"), "p6": ("below", "center"),
         "p7": ("below", "left"), "p5": ("below", "right"),
         # Flipped (WP-41 BY-18): ("below", "left") and ("below",
         # "right") were wrong because twoway draws 9 and 3 o'clock in a
         # narrow box beside the plot region, the label centred on it
         # (by_layout_truth.json Y11, Y12; by_remainder_truth sub_pos3/9).
         "p9": ("left", "center"), "p3": ("right", "center"),
         "r1p12": ("above", "center"), "r2p6": ("below", "center")}


def _build(mode):
    if mode not in _BUILT:
        graphs = [tk._graph(n, tk._ONE, {"by": "foreign", "subtitle": s})
                  for n, s in _SUBS.items()]
        graphs.append(tk._graph("byin", tk._ONE, {
            "by": "foreign, subtitle(, position(5) ring(0))"}))
        spec = tk._spec(graphs, scheme="s2color")
        _BUILT[mode] = tk._build(mode, spec, data=tr._data())
    return _BUILT[mode]


def _panels(mode, name):
    roots, _n, _o = _build(mode)
    grid = tk._grids(roots)[name]
    return [c[0] for c in grid.children
            if getattr(c[0], "_dash_by_panel", False)]


def _side_of(fig):
    for side in ("above", "below", "left", "right"):
        if panel_label_title(fig) in list(getattr(fig, side)):
            return side
    return None


def _inside(fig):
    return [m for m in fig.center if "dash_by_label_inside"
            in (getattr(m, "tags", None) or [])]


class TestTheFixture:
    def test_clock_sides(self):
        """The label's text sits above the plot region at 12, 11, 1 and
        below it at 6, 7, 5; at 9 and 3 at the region's bottom; with
        ring(0) inside the region at its bottom."""
        p = tr._fix()["probes"]
        top = 258.27      # the plain panel's plot region top
        for pid, where in (("sub_pos12", "above"), ("sub_pos11", "above"),
                           ("sub_pos1", "above"), ("sub_pos6", "below"),
                           ("sub_pos7", "below"), ("sub_ring1_pos12", "above"),
                           ("sub_ring2_pos6", "below")):
            (t,) = [x for x in p[pid]["texts"] if x["t"] == "Domestic"]
            assert (t["y"] < top) == (where == "above"), pid
        anchors = {pid: [x for x in p[pid]["texts"]
                         if x["t"] == "Domestic"][0]["anchor"]
                   for pid in ("sub_pos11", "sub_pos1", "sub_pos5_ring0",
                               "sub_pos12_ring0")}
        assert anchors == {"sub_pos11": None, "sub_pos1": "end",
                           "sub_pos5_ring0": "end",
                           "sub_pos12_ring0": "middle"}
        reg_bottom = 135.39 + 2241.68
        for c, anchor in (("1", "end"), ("3", "end"), ("5", "end"),
                          ("7", None), ("9", None), ("11", None),
                          ("0", "middle"), ("6", "middle"), ("12", "middle")):
            q = p["sub_pos%s_ring0" % c]
            (t,) = [x for x in q["texts"] if x["t"] == "Domestic"]
            assert t["anchor"] == anchor and reg_bottom - 60 < t["y"] < \
                reg_bottom, c
            fill = [r for r in q["rects"] if r["fill"] == "#d9e6eb"]
            assert fill and fill[0]["h"] > 2000, c
        q = p["sub_pos1_ring0_nobexpand"]
        (t,) = [x for x in q["texts"] if x["t"] == "Domestic"]
        assert t["y"] < 300 and t["anchor"] == "end"
        b = [r for r in q["rects"] if r["fill"] == "#d9e6eb"][0]
        assert b["h"] < 200 and abs(b["x"] + b["w"] - (388.33 + 1683.5)) < 1

    def test_by_subtitle_leaves_the_labels(self):
        p = tr._fix()["probes"]
        assert p["byin_pos5_ring0"]["texts"] == p["by_foreign"]["texts"]


@pytest.mark.parametrize("mode", _MODES)
class TestThePlace:
    def test_sides(self, mode):
        bad = []
        for name, (side, align) in _WANT.items():
            for f in _panels(mode, name):
                t = panel_label_title(f)
                if (_side_of(f), t.align) != (side, align):
                    bad.append((name, _side_of(f), t.align))
                box = tr._box(f)
                if box is None or box not in list(getattr(f, side)):
                    bad.append((name, "box"))
        assert bad == []

    def test_ring0(self, mode):
        for name, anchor in _RING0.items():
            for f in _panels(mode, name):
                (lab,) = _inside(f)
                assert lab.anchor == anchor, name
                assert lab.text in ("Domestic", "Foreign")
                assert str(f.background_fill_color).lower() == "#d9e6eb"
                assert panel_label_title(f).visible is False
                assert tr._box(f) is None
        for f in _panels(mode, "r0nobox"):
            (lab,) = _inside(f)
            assert str(f.background_fill_color).lower() == "#ffffff"
        for f in _panels(mode, "r0p1nob"):
            (lab,) = _inside(f)
            assert lab.anchor == "top_right"
            assert str(lab.background_fill_color).lower() == "#d9e6eb"
            assert str(f.background_fill_color).lower() == "#ffffff"

    def test_silent(self, mode):
        _r, notes, _o = _build(mode)
        assert not [n for n in notes if "subtitle()" in n
                    and ("position" in n or "ring" in n)], notes

    def test_by_subtitle_leaves_the_labels(self, mode):
        for f in _panels(mode, "byin"):
            assert _side_of(f) == "above" and not _inside(f)
