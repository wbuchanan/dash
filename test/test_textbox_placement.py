"""
test_textbox_placement.py -- the textbox sub-options of title(),
subtitle(), note() and caption() (WP-31 D3, section 30).

The defect: ``_dash_textbox`` honoured size(), color(), prefix and suffix
and named every other textbox sub-option, so ``title("T", position(6))``
drew T above the plot and printed "title() sub-option(s) not implemented
and ignored: position(6)"; ``_dash_textbox_place`` was called with the
scheme's clocks only.

twoway's rule (_fr_title_parse_and_log.ado, _fr_tbstyle_parse_and_log.ado;
measured in test/fixtures/textbox_truth.json by
scripts/extract_textbox_truth.do, s2color):

* position(k) puts the box at clock k: 11, 12 and 1 above the plot region,
  5, 6 and 7 below it, 2-4 to its right and 8-10 to its left (horizontal
  text); dash draws a box twoway puts beside the plot on the nearer
  horizontal side (a Bokeh Title in a left or right panel is turned on its
  side), the documented difference;
* ring(0) or position(0) draws the box inside the plot region at the
  clock's compass point; span at position(0) prints "(option span ignored
  for position(0))";
* rings order the boxes on one side: title 7, subtitle 6, caption 5,
  note 4 (`gridringstyle <box>_ring'), legend 3, the edge titles 1-2;
* box draws the frame (bcolor() fill and line, fcolor() fill, lcolor(),
  lwidth()), margin() pads it, linegap() spaces the lines (the line step
  is the font size plus the gap), justification() aligns the text inside
  its box (the box itself stays at the clock), tstyle() is the base style
  and size()/color() still win; an unknown tstyle() draws the default
  attributes with "named style nosuch not found in class textboxstyle,
  default attributes used".

orientation(), width() and height() are what a Bokeh Title cannot draw and
stay named.
"""
import json
import os
import re
import sys
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

from bokeh.models import Label, Legend, Node, Title  # noqa: E402

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402

MODES = ("saved", "served")
_FIXTURE = os.path.join(_HERE, "fixtures", "textbox_truth.json")

with open(_FIXTURE, encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)

_INSIDE = {
    12: ("center", "top", "top_center"), 1: ("right", "top", "top_right"),
    2: ("right", "top", "top_right"), 3: ("right", "center", "center_right"),
    4: ("right", "bottom", "bottom_right"),
    5: ("right", "bottom", "bottom_right"),
    6: ("center", "bottom", "bottom_center"),
    7: ("left", "bottom", "bottom_left"), 8: ("left", "bottom", "bottom_left"),
    9: ("left", "center", "center_left"), 10: ("left", "top", "top_left"),
    11: ("left", "top", "top_left"), 0: ("center", "center", "center"),
}


def _figs(mode, go, plots=None, scheme="s2color"):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        figs, _c = tp._figures_in(mode, tp._spec(
            plots or [tp._sc()], {"scheme": scheme}, go))
    return figs, [str(w.message) for w in caught] + list(_c or [])


def _fig(mode, go, plots=None, scheme="s2color"):
    figs, caught = _figs(mode, go, plots, scheme)
    assert len(figs) == 1, len(figs)
    return figs[0], caught


def _box(fig, key):
    """[(panel, index, model)] of the dash_textbox models of *key*."""
    out = []
    for side in ("center", "above", "below", "left", "right"):
        for i, m in enumerate(getattr(fig, side)):
            tags = list(getattr(m, "tags", None) or [])
            if "dash_textbox" in tags and key in tags:
                out.append((side, i, m))
    return out


def _one(fig, key):
    b = _box(fig, key)
    assert len(b) == 1, b
    return b[0]


def _ring_tag(m):
    return [t for t in m.tags if str(t).startswith("ring=")]


def _named(caught, word):
    return [w for w in caught if "not implemented and ignored" in w
            and word in w]


def _svg(case, text):
    return [t for t in TRUTH[case]["texts"] if t["text"] == text][0]


# ============================================================
# The fixture
# ============================================================
class TestTheFixture:

    def test_meta_is_stamped(self):
        m = TRUTH["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted",
                  "source", "members"):
            assert m.get(k), k
        assert m["source"] == "scripts/extract_textbox_truth.do"

    def test_every_case_was_measured(self):
        keys = ["pos_%d" % k for k in range(13)] + \
            ["ring0_%d" % k for k in (1, 3, 6, 9, 12)] + \
            ["span_pos0", "box", "tstyle_heading", "tstyle_bad",
             "linegap_0", "linegap_3", "order", "user_ring", "just_left"]
        for k in keys:
            assert TRUTH[k]["rc"] == 0, k
        assert TRUTH["span_pos0"]["note"] == \
            "(option span ignored for position(0))"
        assert TRUTH["tstyle_bad"]["note"] == (
            "(note: named style nosuch not found in class textboxstyle, "
            "default attributes used)")

    def test_twoways_clock_as_measured(self):
        """11, 12, 1 above the plot region; 5, 6, 7 below; 2-4 right of
        it and 8-10 left of it; 0 inside, at its centre."""
        for k in range(13):
            t, p = _svg("pos_%d" % k, "T"), TRUTH["pos_%d" % k]["plot"]
            top, bot = p["y"], p["y"] + p["h"]
            left, right = p["x"], p["x"] + p["w"]
            if k in (11, 12, 1):
                assert t["y"] < top, k
            elif k in (5, 6, 7):
                assert t["y"] > bot, k
            elif k in (2, 3, 4):
                assert t["x"] > right, k
            elif k in (8, 9, 10):
                assert t["x"] < left, k
            else:
                assert left < t["x"] < right and top < t["y"] < bot

    def test_ring0_is_inside(self):
        for k in (1, 3, 6, 9, 12):
            t, p = _svg("ring0_%d" % k, "N"), TRUTH["ring0_%d" % k]["plot"]
            assert p["x"] < t["x"] < p["x"] + p["w"], k
            assert p["y"] < t["y"] < p["y"] + p["h"], k

    def test_rings_as_measured(self):
        y = {t["text"]: t["y"] for t in TRUTH["order"]["texts"]}
        assert y["T"] < y["S"] < y["Trunk space (cu. ft.)"] < y["T2"] \
            < y["T1"]
        u = {t["text"]: t["y"] for t in TRUTH["user_ring"]["texts"]}
        # subtitle ring(2) shares t2title's ring, inside the note's 4.
        assert u["T"] < u["N"] < u["S"] < u["T1"]


# ============================================================
# position(): the clock
# ============================================================
class TestPlacement:

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("k", list(range(1, 13)))
    def test_clock_table(self, mode, k):
        f, caught = _fig(mode, {"title": '"T", position(%d)' % k})
        side, _i, m = _one(f, "title")
        want = dr._dash_textbox_place(k, "center")
        assert isinstance(m, Title) and m.text == "T"
        assert (side, m.align) == want
        assert _ring_tag(m) == ["ring=7"]
        assert f.title is None
        assert not _named(caught, "position")

    @pytest.mark.parametrize("mode", MODES)
    def test_note_below_moves_above(self, mode):
        f, _c = _fig(mode, {"note": '"N", position(12)'})
        side, _i, m = _one(f, "note")
        assert side == "above" and m.align == "center"

    def test_a_bad_clock_is_the_default(self):
        f, _c = _fig("saved", {"note": '"N", position(13)'})
        side, _i, m = _one(f, "note")
        assert side == "below" and m.align == "left"


# ============================================================
# ring(0) and position(0): inside the plot region
# ============================================================
class TestInside:

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("k", [1, 3, 6, 9, 12])
    def test_ring0_anchor(self, mode, k):
        f, _c = _fig(mode, {"note": '"N", ring(0) position(%d)' % k})
        side, i, m = _one(f, "note")
        sx, sy, a = _INSIDE[k]
        assert (side, i) == ("center", 0)
        assert isinstance(m, Label) and m.text == "N"
        assert isinstance(m.x, Node) and isinstance(m.y, Node)
        assert (m.x.target, m.x.symbol) == ("frame", sx)
        assert (m.y.target, m.y.symbol) == ("frame", sy)
        assert m.anchor == a

    @pytest.mark.parametrize("mode", MODES)
    def test_position0_is_centre(self, mode):
        f, _c = _fig(mode, {"title": '"T", position(0)'})
        side, _i, m = _one(f, "title")
        assert side == "center" and isinstance(m, Label)
        assert (m.x.symbol, m.y.symbol, m.anchor) == \
            ("center", "center", "center")
        assert f.title is None

    @pytest.mark.parametrize("mode", MODES)
    def test_span_at_zero_notes(self, mode):
        _f, caught = _fig(mode, {"title": '"T", position(0) span'})
        hits = [w for w in caught
                if "option span ignored for position(0)" in w]
        assert len(hits) == 1, caught
        assert not _named(caught, "span")


# ============================================================
# ring(): the order of the boxes on one side
# ============================================================
class TestRingOrder:

    @pytest.mark.parametrize("mode", MODES)
    def test_rings_on_one_side(self, mode):
        plots = [tp._sc(), tp.plot_for("scatter", yvar="price",
                                       xvar="weight")]
        f, _c = _fig(mode, {"title": '"T", ring(7)', "subtitle": '"S"',
                            "t1title": '"T1"', "t2title": '"T2"',
                            "legend": "position(12)"}, plots)
        above = list(f.above)

        def at(pred):
            hit = [i for i, m in enumerate(above) if pred(m)]
            assert len(hit) == 1, (above, hit)
            return hit[0]

        t1 = at(lambda m: "t1title" in (m.tags or []))
        t2 = at(lambda m: "t2title" in (m.tags or []))
        leg = at(lambda m: isinstance(m, Legend))
        s = at(lambda m: "subtitle" in (m.tags or []))
        t = at(lambda m: "title" in (m.tags or []))
        assert t1 < t2 < leg < s < t, above

    @pytest.mark.parametrize("mode", MODES)
    def test_user_ring_moves_inside(self, mode):
        f, _c = _fig(mode, {"title": '"T", ring(7)',
                            "subtitle": '"S", ring(2)',
                            "note": '"N", position(12)',
                            "t1title": '"T1"', "t2title": '"T2"'})
        order = [k for m in f.above for k in ("t1title", "t2title",
                                              "subtitle", "note", "title")
                 if k in (m.tags or [])]
        assert order == ["t1title", "t2title", "subtitle", "note", "title"]

    def test_the_scheme_rings(self):
        s = dr.SchemeParser.resolve_or_fallback("s2color", "x")
        assert s.text_ring == {"title": 7, "subtitle": 6, "caption": 5,
                               "note": 4}


# ============================================================
# box, colours, width, margin
# ============================================================
class TestBox:

    @pytest.mark.parametrize("mode", MODES)
    def test_box_props(self, mode):
        f, caught = _fig(mode, {"caption": '"C", box bcolor(gs14) lcolor(red)'
                                           ' lwidth(thick) margin(medium)'})
        _s, _i, m = _one(f, "caption")
        rects = TRUTH["box"]["rects"]
        fill = [r for r in rects if r["style"].startswith("fill:#E0E0E0")]
        line = [r for r in rects if "stroke:#FF0000" in r["style"]]
        assert fill and line
        assert m.background_fill_color.lower() == "#e0e0e0"
        assert m.border_line_color.lower() == "#ff0000"
        assert m.border_line_width == pytest.approx(
            dr.OptionTranslator.translate_lwidth("thick", None, 4.0))
        sides = dr.SchemeParser.resolve_or_fallback(
            "s2color", "x").margin_sides("medium")
        T = dr.OptionTranslator
        px = [int(round(float(v) * T.PT_PER_RS * T.PX_PER_PT))
              for v in sides]
        assert m.padding == {"left": px[0], "right": px[1],
                             "bottom": px[2], "top": px[3]}
        assert not _named(caught, "box")

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("key", ["title", "subtitle", "note",
                                     "caption"])
    def test_an_unspanned_box_is_its_text_and_margin(self, mode, key):
        """D39 D-30.c: a box drawn without span is sized to its text plus
        the text box style's margin, as twoway draws it.  Measured 18oct2026
        (StataNow 19.5, s2color, SVG at 720 px an inch, 28.8 px a unit):
        title("Hello world", box justification(left)), subtitle("Sub", box
        justification(left)), note("A note here", box) and caption("Cap",
        box) each start their text 17.2-17.3 px, 0.6 units, inside the box
        (s2color's ``margin heading/subheading/body/small_body vsmall``,
        ``gsize vsmallmargin relative0p6``); span moves the box (centred on
        the graph, not the plot region) and leaves its width; margin(medium)
        pads 3.5 units.  A Bokeh Title draws its box round the text and its
        padding, so the padding is the margin."""
        f, _c = _fig(mode, {key: '"T", box'})
        m = f.title if key == "title" else _one(f, key)[2]
        T = dr.OptionTranslator
        px = int(round(0.6 * T.PT_PER_RS * T.PX_PER_PT))
        assert px == 2
        assert m.padding == {"left": px, "right": px, "bottom": px,
                             "top": px}

    @pytest.mark.parametrize("mode", MODES)
    def test_no_box_keeps_no_padding(self, mode):
        """Without box nothing is framed and the text keeps its place."""
        f, _c = _fig(mode, {"note": '"N"'})
        _s, _i, m = _one(f, "note")
        assert m.padding in (0, None, {"left": 0, "right": 0, "bottom": 0,
                                       "top": 0})

    @pytest.mark.parametrize("mode", MODES)
    def test_nobox(self, mode):
        f, _c = _fig(mode, {"note": '"N", nobox', "title": '"T"'},
                     scheme="economist")
        found = [m for side in ("center", "above", "below")
                 for m in getattr(f, side)
                 if "note" in (getattr(m, "tags", None) or [])]
        assert len(found) == 1
        assert found[0].background_fill_color is None
        assert found[0].border_line_color is None

    def test_box_colours_need_box(self):
        """twoway draws bcolor()/lcolor() only with box: without it the
        colours are read and nothing is framed."""
        f, caught = _fig("saved", {"caption": '"C", lcolor(red)'})
        _s, _i, m = _one(f, "caption")
        assert m.border_line_color is None
        assert not _named(caught, "lcolor")


# ============================================================
# justification(), alignment(), linegap()
# ============================================================
class TestTextProps:

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("sub", ["justification", "alignment_title",
                                     "alignment_label", "linegap"])
    def test_each(self, mode, sub):
        if sub == "justification":
            f, _c = _fig(mode, {"title": '"T", justification(left)'})
            m = f.title
            if m is None:
                m = _one(f, "title")[2]
            assert m.text_align == "left"
            # The box stays at the clock: twoway's text moved 46 of 3960
            # units (just_left), the box did not.
            assert m.align == "center"
        elif sub == "alignment_title":
            f, _c = _fig(mode, {"note": '"N", alignment(top)'})
            assert _one(f, "note")[2].vertical_align == "top"
        elif sub == "alignment_label":
            f, _c = _fig(mode, {"note": '"N", ring(0) position(3) '
                                        'alignment(top)'})
            m = _one(f, "note")[2]
            assert isinstance(m, Label) and m.anchor.startswith("top_")
        else:
            f, _c = _fig(mode, {"note": '"N1" "N2", linegap(3)'})
            m = _one(f, "note")[2]
            a, b = _svg("linegap_3", "N1"), _svg("linegap_3", "N2")
            measured = (b["y"] - a["y"]) / a["size"]
            assert m.text_line_height == pytest.approx(measured, abs=0.05)


# ============================================================
# tstyle()
# ============================================================
class TestTstyle:

    @pytest.mark.parametrize("mode", MODES)
    def test_base_style(self, mode):
        f, _c = _fig(mode, {"note": '"N", tstyle(heading)'})
        m = _one(f, "note")[2]
        s = dr.SchemeParser.resolve_or_fallback("s2color", "x")
        size, colour = s.textbox_style("heading")
        assert m.text_font_size == size and m.text_color == colour
        # twoway: heading's 139.96 SVG units, 14pt.
        assert _svg("tstyle_heading", "N")["size"] == pytest.approx(139.96)

    @pytest.mark.parametrize("mode", MODES)
    def test_size_wins(self, mode):
        f, _c = _fig(mode, {"note": '"N", tstyle(heading) size(small)'})
        assert _one(f, "note")[2].text_font_size == "8pt"

    @pytest.mark.parametrize("mode", MODES)
    def test_unknown_named_once(self, mode):
        f, caught = _fig(mode, {"note": '"N", tstyle(nosuch)'})
        m = _one(f, "note")[2]
        s = dr.SchemeParser.resolve_or_fallback("s2color", "x")
        assert m.text_font_size == s.textbox_style("body")[0]
        hits = [w for w in caught if "named style nosuch not found in class "
                "textboxstyle, default attributes used" in w]
        assert len(hits) == 1, caught


# ============================================================
# orientation(), width(), height(): still named, the box drawn
# ============================================================
class TestStillNamed:

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("sub", ["orientation(vertical)", "width(20)",
                                     "height(5)"])
    def test_named_once(self, mode, sub):
        f, caught = _fig(mode, {"note": '"N", %s' % sub})
        assert [m for m in f.below if isinstance(m, Title)
                and m.text == "N"]
        assert len(_named(caught, sub)) == 1, caught


# ============================================================
# Nothing printed for a drawn sub-option
# ============================================================
class TestSilentWhenHonoured:

    @pytest.mark.parametrize("sub", [
        "position(6)", "ring(5)", "span", "nospan", "justification(left)",
        "alignment(top)", "margin(small)", "linegap(2)", "box", "nobox",
        "bcolor(red)", "bfcolor(red)", "fcolor(red)", "lcolor(red)",
        "lwidth(thin)", "lpattern(dash)", "bmargin(small)", "bexpand",
        "nobexpand", "tstyle(body)", "placement(ne)"])
    def test_no_note(self, sub):
        _f, caught = _fig("saved", {"caption": '"C", %s' % sub})
        assert not [w for w in caught if "caption()" in w], caught


# ============================================================
# Guards
# ============================================================
class TestEconomistBandUnchanged:

    @pytest.mark.parametrize("mode", MODES)
    def test_band(self, mode):
        f, _c = _fig(mode, {"title": '"T"', "note": '"N"'},
                     scheme="economist")
        labs = [m for m in f.center if isinstance(m, Label)
                and m.text == "N"]
        assert len(labs) == 1
        assert labs[0].x.target is f.title and labs[0].y.symbol == "top"


class TestOnAByGraph:

    @pytest.mark.parametrize("mode", MODES)
    def test_once(self, mode):
        figs, _c = _figs(mode, {"by": "foreign",
                                "note": '"N", ring(0) position(1)'})
        assert len(figs) == 2
        for f in figs:
            labs = [m for m in f.center if isinstance(m, Label)
                    and "dash_textbox" in (m.tags or [])]
            assert len(labs) == 1 and labs[0].text == "N"


class TestHostile:

    def test_values_do_not_reach_html(self):
        spec = tp._spec([tp._sc()], {"scheme": "s2color"},
                        {"note": '"<b>N</b>", lcolor(</script>) box '
                                 'tstyle(<img src=x>)'})
        r, _caught, page = tp._standalone_page(spec)
        fig = list(r.figures.values())[0]
        m = _one(fig, "note")[2]
        assert m.text == "<b>N</b>"
        assert "<img src=x>" not in page
        assert "lcolor(</script>)" not in page
        assert re.search(r"</script>\s*\)", page) is None
