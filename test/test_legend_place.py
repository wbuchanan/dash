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
import re
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


# ---------------------------------------------------------------------------
# LT-17: a hole in a one-column or one-row legend is one row (column) gap.
# twoway's legend_g PlaceKeyTextAdjRow advances the row for a hole, so
# holes(k) cols(1) grows the box by one legend_row_gap (40 SVG px under
# s2color) at the hole's place; holes(2) rows(1) by one legend_col_gap
# (140); in a grid of rows and columns a hole is a full cell.  dash draws
# the gap as an empty track of the legend's own CSS grid (the Legend's
# ``dash_legend_holes`` stylesheet, ruling D69): the grid's gap -- the
# legend's spacing, which scale() and the width scale carry -- is laid
# once more there, and the keys stay the original LegendItems.
# ---------------------------------------------------------------------------

_ROW_GAP_SVG = 1.3888 * 28.8     # s2color legend_row_gap, SVG px
_COL_GAP_SVG = 4.8611 * 28.8     # s2color legend_col_gap


def _hole_sheet(lg):
    sheets = [ss for ss in lg.stylesheets
              if "dash_legend_holes" in (ss.tags or [])]
    assert len(sheets) <= 1, sheets
    return sheets[0].css if sheets else None


def _twoway_tracks(key, base, axis="y"):
    """The track of each key in twoway's drawing of *key*: a key the hole
    moved (by the gap, against *base*) sits after the hole."""
    rec, ref = TRUTH[key], TRUTH[base]
    moved = []
    for a, b in zip(rec["key_texts"], ref["key_texts"]):
        d = a[axis] - b[axis]
        moved.append(abs(d) > 10)
    n = len(moved)
    if axis == "y":
        # The box is bottom-anchored: keys BEFORE the hole moved up.
        before = sum(moved)
    else:
        # Centred: keys before the hole moved left, after it right.
        before = sum(1 for a, b in zip(rec["key_texts"], ref["key_texts"])
                     if a[axis] - b[axis] < -10)
    return [i + 1 if i < before else i + 2 for i in range(n)], n + 1


def _expected_css(tracks, total, axis):
    prop = "rows" if axis == "y" else "columns"
    one = "row" if axis == "y" else "column"
    return (".bk-grid{grid-template-%s:repeat(%d,max-content);}" % (
        prop, total) + "".join(".bk-item:nth-child(%d){grid-%s:%d;}" % (
            i + 1, one, t) for i, t in enumerate(tracks)))


class TestHolesTruth:

    @pytest.mark.parametrize("key,base,gap", [
        ("holes_1col_1", "holes_1col_0", _ROW_GAP_SVG),
        ("holes_1col_2", "holes_1col_0", _ROW_GAP_SVG),
        ("holes_1col_4", "holes_1col_0", _ROW_GAP_SVG),
        ("holes_1col_1key", "holes_1col_1key_0", _ROW_GAP_SVG),
        ("holes_1col_scale", "holes_1col_scale_0", _ROW_GAP_SVG)])
    def test_one_row_gap(self, key, base, gap):
        """twoway: the box is one row gap taller (under scale(1.5) too:
        its row gap is the same 40 SVG px there)."""
        h = TRUTH[key]["box"]["bottom"] - TRUTH[key]["box"]["top"]
        h0 = TRUTH[base]["box"]["bottom"] - TRUTH[base]["box"]["top"]
        assert abs((h - h0) - gap) < 1.0, (h, h0)

    def test_one_column_gap(self):
        rec, ref = TRUTH["holes_1row"], TRUTH["holes_1row_0"]
        w = rec["box"]["right"] - rec["box"]["left"]
        w0 = ref["box"]["right"] - ref["box"]["left"]
        assert abs((w - w0) - _COL_GAP_SVG) < 1.0

    def test_two_columns_full_cell(self):
        xs = {round(t["x"]) for t in TRUTH["holes_2col"]["key_texts"]}
        ys = [round(t["y"]) for t in TRUTH["holes_2col"]["key_texts"]]
        assert len(xs) == 2 and ys[0] < ys[1] == ys[2]


@pytest.mark.parametrize("mode", MODES)
class TestHolesOneColumn:

    @pytest.mark.parametrize("k", [1, 2, 4])
    def test_track_sheet(self, mode, k):
        """holes(k) cols(1): the three keys, no hole item, each in the
        track twoway draws it in, one track more than keys."""
        tracks, total = _twoway_tracks("holes_1col_%d" % k, "holes_1col_0")
        _f, lg, _ = G._fig_legend(mode, G.THREE, "holes(%d) cols(1)" % k)
        assert len(lg.items) == 3
        assert all(list(it.renderers) for it in lg.items)
        assert (lg.ncols, lg.orientation) == (1, "vertical")
        assert _hole_sheet(lg) == _expected_css(tracks, total, "y")

    def test_one_key(self, mode):
        """legend(on holes(1) cols(1)) on one key: the key in track 2."""
        tracks, total = _twoway_tracks("holes_1col_1key",
                                       "holes_1col_1key_0")
        assert (tracks, total) == ([2], 2)
        _f, lg, _ = G._fig_legend(mode, [G._sc()], "on holes(1) cols(1)")
        assert len(lg.items) == 1 and lg.visible
        assert _hole_sheet(lg) == _expected_css(tracks, total, "y")

    def test_one_row(self, mode):
        """holes(2) rows(1): a column gap, keys spaced by colgap()."""
        tracks, total = _twoway_tracks("holes_1row", "holes_1row_0", "x")
        assert (tracks, total) == ([1, 3, 4], 4)
        _f, lg, _ = G._fig_legend(mode, G.THREE, "holes(2) rows(1)")
        assert len(lg.items) == 3 and lg.nrows == 1
        assert lg.spacing == G._px(dr.SchemeParser("s2color").legend_col_gap)
        assert _hole_sheet(lg) == _expected_css(tracks, total, "x")

    def test_keys_are_the_originals(self, mode):
        """The keys keep their renderers and their own text, so the stale
        cue and a click reach them as without holes."""
        _f, base, _ = G._fig_legend(mode, G.THREE, "cols(1)")
        _f, lg, _ = G._fig_legend(mode, G.THREE, "holes(2) cols(1)")
        assert [G._text(i) for i in lg.items] == [
            G._text(i) for i in base.items]
        assert [len(i.renderers) for i in lg.items] == [
            len(i.renderers) for i in base.items]

    def test_scale(self, mode):
        """scale(1.5): the same tracks; the gap is the legend's own
        spacing, which scale() carries (twoway: the hole is one row gap
        at either scale, holes_1col_scale)."""
        _f, lg, _ = G._fig_legend(mode, G.THREE, "holes(1) cols(1)",
                                  go={"scale": "1.5"})
        _f, lg0, _ = G._fig_legend(mode, G.THREE, "holes(1) cols(1)")
        assert _hole_sheet(lg) == _hole_sheet(lg0)
        # Only integers: no length of its own that scale() would miss.
        assert not re.search(r"\d(px|em|pt|%)", _hole_sheet(lg))

    def test_by_cell(self, mode):
        """by(): the overall legend's cell keeps the tracks and hides a
        series on a click in every panel."""
        from bokeh.models import Legend
        import test_mode_parity as tp
        spec = tp._spec(G.THREE, {"scheme": "s2color"},
                        {"by": "foreign", "legend": "holes(1) cols(1)"})
        if mode == "saved":
            r, _ = tp._standalone(spec)
            models = r._last_layout_root.references()
        else:
            doc, _ = tp._served(spec)
            models = [m for root in doc.roots for m in root.references()]
        cells = [m for m in models if isinstance(m, Legend)
                 and str(m.name or "").endswith("_key")]
        assert len(cells) == 1, cells
        lg = cells[0]
        assert lg.click_policy == "hide" and len(lg.items) == 3
        assert all(len(it.renderers) > 1 for it in lg.items)
        assert _hole_sheet(lg) == _expected_css([2, 3, 4], 4, "y")


@pytest.mark.parametrize("mode", MODES)
class TestHolesTwoColumns:

    def test_full_cell(self, mode):
        """holes(2) cols(2): the hole is a full cell, an empty item, and
        no track sheet (guard)."""
        _f, lg, _ = G._fig_legend(mode, G.THREE, "holes(2) cols(2)")
        assert len(lg.items) == 4 and list(lg.items[1].renderers) == []
        assert _hole_sheet(lg) is None


# ---------------------------------------------------------------------------
# LT-5: legend(all) keys every plot, draw is on and nodraw is off.
# twoway's _fr_legend_parse_and_log.ado: all sets .legend._all (legend_g
# rebuild adds every view's key, no merge); nodraw/off force no legend,
# draw/on force one, applied after, so on/draw win in either order
# (legend_place_truth.json all_p1, draw_1, nodraw_2, on_nodraw, nodraw_on,
# off_draw, draw_off, all_nodraw).
# ---------------------------------------------------------------------------

_P1 = [G._sc(pstyle="p1"), G._sc("price", pstyle="p1")]

#: probe -> (plots, legend(), the fixture key).
_LT5 = {
    "all": (_P1, "all", "all_p1"),
    "no_all": (_P1, "", "all_p1_0"),
    "draw": ([G._sc()], "draw", "draw_1"),
    "nodraw": (G.TWO, "nodraw", "nodraw_2"),
    "on_nodraw": (G.TWO, "on nodraw", "on_nodraw"),
    "nodraw_on": ([G._sc()], "nodraw on", "nodraw_on"),
    "off_draw": ([G._sc()], "off draw", "off_draw"),
    "draw_off": ([G._sc()], "draw off", "draw_off"),
    "all_nodraw": (_P1, "all nodraw", "all_nodraw"),
}


@pytest.mark.parametrize("mode", MODES)
class TestAllDrawNodraw:

    @pytest.mark.parametrize("probe", sorted(_LT5))
    def test_as_twoway(self, mode, probe):
        """The legend is drawn exactly when twoway draws it, with
        twoway's key count, and nothing is noted for the words."""
        plots, opt, key = _LT5[probe]
        rec = TRUTH[key]
        fig, lg, msgs = G._fig_legend(mode, plots, opt)
        assert bool(lg.visible) == bool(rec["drawn"]), (probe, rec)
        assert len(lg.items) == rec["keys"], (probe, rec)
        for word in ("all", "draw", "nodraw"):
            assert not [m for m in msgs if "legend" in m
                        and re.search(r"\b%s\b" % word, m)], msgs

    def test_all_keeps_both_texts(self, mode):
        _f, lg, _ = G._fig_legend(mode, _P1, "all")
        assert [G._text(i) for i in lg.items] == [
            G._text(i) for i in G._fig_legend(mode, G.TWO, "")[1].items]
