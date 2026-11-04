"""test_legend_place.py -- the legend's place, its holes and legend(all),
draw and nodraw, as twoway draws them (WP-43 section 43-02: LT-4, LT-17,
LT-5).

LT-4: twoway puts ``legend(ring(0) bplacement(nw))`` at the plot region's
top-left; position(0) with bplacement() follows bplacement(); every
compass spelling twoway reads (compass2dir.class ``_unabbrev``:
abbreviations of the lower-case names, the capitals N .. SW and T B R L,
a clock number 0-12) is read, and a name it does not know is noted and
drawn east (its default attributes).

Ground truth: test/fixtures/legend_place_truth.json, written by
scripts/extract_legend_place_truth.do from twoway's class values and SVG
export (SVG px, 720 per inch; s2color).
"""
import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402
import test_legend_geometry as G  # noqa: E402

MODES = ("saved", "served")
with open(os.path.join(_HERE, "fixtures", "legend_place_truth.json"),
          encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)

COMPASS = ("n", "ne", "e", "se", "s", "sw", "w", "nw", "c")
#: compass2dir's full names of the short ones the fixture's keys use.
FULL = {"n": "north", "ne": "neast", "e": "east", "se": "seast",
        "s": "south", "sw": "swest", "w": "west", "nw": "nwest",
        "c": "center"}
SPELLINGS = TRUTH["_meta"]["spellings"]


def _inside_location(rec):
    """The Bokeh inside location of twoway's legend box in *rec*: each
    edge within 5% of the plot region's edge is that side."""
    r = rec["box_rel"]
    v = ("top" if r["top"] < 0.05 else "bottom" if r["bottom"] > 0.95
         else "center")
    h = ("left" if r["left"] < 0.05 else "right" if r["right"] > 0.95
         else "center")
    if (v, h) == ("center", "center"):
        return "center"
    return "%s_%s" % (v, h)


def _notes(msgs, word="bplacement"):
    return [m for m in msgs if word in m]


class TestTheFixture:

    def test_complete(self):
        meta = TRUTH["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted",
                  "source", "spellings"):
            assert meta.get(k), k
        assert meta["source"] == "scripts/extract_legend_place_truth.do"
        for k in (["r0_default", "r0_pos1", "r0_pos1_bp_sw", "pos0",
                   "pos0_bp_nw"] + ["r0_bp_" + x for x in COMPASS]
                  + ["out_bp_" + x for x in COMPASS]):
            assert TRUTH[k]["rc"] == 0 and TRUTH[k]["drawn"] == 1, k
        for i in range(1, len(SPELLINGS) + 1):
            for side in ("in", "out"):
                assert TRUTH["bp_%s_%d" % (side, i)]["rc"] == 0

    def test_the_measured_outcomes(self):
        # ring(0) bplacement(ne) is ring(0) position(1); bplacement wins
        # over position(0) and over ring(0) pos(1).
        assert TRUTH["r0_bp_ne"]["box"] == TRUTH["r0_pos1"]["box"]
        assert TRUTH["pos0_bp_nw"]["box"] == TRUTH["r0_bp_nw"]["box"]
        assert TRUTH["r0_pos1_bp_sw"]["box"] == TRUTH["r0_bp_sw"]["box"]
        # A name compass2dir does not know: noted, drawn east.
        for i, s in enumerate(SPELLINGS, 1):
            rec = TRUTH["bp_in_%d" % i]
            if s in ("NOR", "3.0", "bogus"):
                assert rec["same_as"] == ["e"] and rec["log"], s
            else:
                assert rec["log"] == [] and len(rec["same_as"]) == 1, s


class TestCompassReader:

    @pytest.mark.parametrize("spelling", SPELLINGS)
    def test_each_spelling(self, spelling):
        """Every spelling the fixture probed reads as the name twoway drew
        it by; one twoway noted is no name (None)."""
        rec = TRUTH["bp_in_%d" % (SPELLINGS.index(spelling) + 1)]
        got = dr._dash_compass_dir(spelling)
        if rec["log"]:
            assert got is None
        else:
            assert got == FULL[rec["same_as"][0]]
            assert got in dr._DASH_BPLACEMENT_LOCATION

    @pytest.mark.parametrize("text,want", [
        ("n", "north"), ("no", "north"), ("north", "north"),
        ("nw", "nwest"), ("nwe", "nwest"), ("c", "center"),
        ("cent", "center"), ("b", "south"), ("bottom", "south"),
        ("l", "west"), ("lef", "west"), ("SE", "seast"), ("T", "north"),
        ("B", "south"), ("L", "west"), ("0", "center"), ("1", "neast"),
        ("6", "south"), ("9", "west"), ("11", "nwest"), (" ne ", "neast"),
        ("Nw", None), ("north1", None), ("13", None), ("06", "south"),
        ("", None), ("x", None), ("-1", None)])
    def test_the_port(self, text, want):
        """compass2dir.class _unabbrev: lower-case abbreviations first,
        then (two characters at most) the capitals and a clock number."""
        assert dr._dash_compass_dir(text) == want


@pytest.mark.parametrize("mode", MODES)
class TestInsideBplacement:

    @pytest.mark.parametrize("x", COMPASS)
    def test_ring0(self, mode, x):
        want = _inside_location(TRUTH["r0_bp_" + x])
        fig, lg, msgs = G._fig_legend(mode, G.THREE,
                                      "ring(0) bplacement(%s)" % x)
        assert G._panel_of(fig, lg) == "center"
        assert lg.location == want
        assert not _notes(msgs)

    def test_ring0_pos1_sw(self, mode):
        want = _inside_location(TRUTH["r0_pos1_bp_sw"])
        assert want == "bottom_left"
        fig, lg, _ = G._fig_legend(mode, G.THREE,
                                   "ring(0) pos(1) bplacement(sw)")
        assert G._panel_of(fig, lg) == "center"
        assert lg.location == want

    def test_pos0_bplacement(self, mode):
        want = _inside_location(TRUTH["pos0_bp_nw"])
        fig, lg, _ = G._fig_legend(mode, G.THREE, "pos(0) bplacement(nw)")
        assert G._panel_of(fig, lg) == "center"
        assert lg.location == want == "top_left"

    def test_without_bplacement(self, mode):
        """ring(0) alone keeps the clock's inside place (guard)."""
        assert _inside_location(TRUTH["r0_default"]) == "bottom_center"
        assert _inside_location(TRUTH["r0_pos1"]) == "top_right"
        _f, lg, _ = G._fig_legend(mode, G.THREE, "ring(0)")
        assert lg.location == "bottom_center"
        _f, lg, _ = G._fig_legend(mode, G.THREE, "ring(0) pos(1)")
        assert lg.location == "top_right"

    @pytest.mark.parametrize("spelling", SPELLINGS)
    def test_spelling_inside(self, mode, spelling):
        """ring(0) bplacement(<spelling>): where twoway drew it, the
        unknown ones east with their note."""
        rec = TRUTH["bp_in_%d" % (SPELLINGS.index(spelling) + 1)]
        want = _inside_location(TRUTH["r0_bp_" + rec["same_as"][0]])
        _f, lg, msgs = G._fig_legend(mode, G.THREE,
                                     "ring(0) bplacement(%s)" % spelling)
        assert lg.location == want
        assert bool(_notes(msgs)) == bool(rec["log"])

    @pytest.mark.parametrize("spelling", ["nor", "top", "t", "nea", "bot",
                                          "rig", "3", "bogus"])
    def test_abbreviation_outside(self, mode, spelling):
        """pos(6) bplacement(<spelling>) reads the spelling (top_center
        for nor, as for n) and notes only a name twoway notes."""
        rec = TRUTH["bp_out_%d" % (SPELLINGS.index(spelling) + 1)]
        canon = {"nor": "n", "top": "n", "t": "n", "nea": "ne", "bot": "s",
                 "rig": "e", "3": "e", "bogus": "e"}[spelling]
        assert canon in rec["same_as"]
        _f, ref, _ = G._fig_legend(mode, G.THREE,
                                   "pos(6) bplacement(%s)" % canon)
        fig, lg, msgs = G._fig_legend(mode, G.THREE,
                                      "pos(6) bplacement(%s)" % spelling)
        assert G._panel_of(fig, lg) == "below"
        assert lg.location == ref.location
        assert bool(_notes(msgs)) == bool(rec["log"])
