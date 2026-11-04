"""
test_title_boxes.py -- the boxes of title(), subtitle(), note() and
caption() and the edge titles (WP-43 section 43-05: LT-8, LT-9, LT-14,
LT-16, LT-18, LT-19).

twoway's rule, measured in test/fixtures/title_box_truth.json by
scripts/extract_title_box_truth.do:

* LT-8: a framed title-family box is filled and lined in its text box
  style (textboxstyle-heading.style: ``set fillcolor scheme textbox``,
  ``set linestyle scheme textbox``): white under stcolor (``color textbox
  white``), bluishgray under s2color, the line the foreground's, black
  and thin.  stcolor's subtitle is drawn in subheading_gs, whose fill is
  ``color bylabel_outline`` (dash's ``color by_label_fill``).  text()
  keeps its own text_option box.
"""
import json
import os
import sys
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402

MODES = ("saved", "served")
_FIXTURE = os.path.join(_HERE, "fixtures", "title_box_truth.json")

with open(_FIXTURE, encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)


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


def _model(fig, key):
    """The model drawing *key*'s text: the figure's own Title for an
    unmoved title, else its one dash_textbox model, else the edge title."""
    if key == "title" and fig.title is not None:
        return fig.title
    b = _box(fig, key)
    if b:
        assert len(b) == 1, b
        return b[0][2]
    for side in ("above", "below", "left", "right"):
        for m in getattr(fig, side):
            if key in list(getattr(m, "tags", None) or []):
                return m
    raise AssertionError("no model for %s" % key)


def _svg_box(case, text):
    """(fill, stroke, stroke width) of the frame twoway draws round
    *text*'s box: the smallest filled rect holding the text's anchor and
    the stroked rect inside it."""
    row = TRUTH[case]
    t = [x for x in row["texts"] if x["text"] == text][0]
    holds = [r for r in row["rects"]
             if r["x"] <= t["x"] <= r["x"] + r["w"]
             and r["y"] - 1 <= t["y"] <= r["y"] + r["h"] + 1
             and r["w"] < row["viewbox"][2] / 2]
    # A box is a filled rect and a stroked one, or one rect doing both
    # (stcolor's subtitle, textboxstyle-subheading_gs.style).
    fills = [r for r in holds if "fill:none" not in r["style"]]
    strokes = [r for r in holds if "stroke:#" in r["style"]]
    assert fills and strokes, (case, holds)
    f = min(fills, key=lambda r: r["w"])
    s = min(strokes, key=lambda r: r["w"])

    def part(style, name):
        for kv in style.split(";"):
            if kv.startswith(name + ":"):
                return kv.split(":", 1)[1]
        return None
    return (part(f["style"], "fill").lower(), part(s["style"], "stroke").lower(),
            float(part(s["style"], "stroke-width")))


_BOX_KEYS = {"title": "T", "subtitle": "S", "note": "N", "caption": "C"}

with open(os.path.join(_HERE, "fixtures", "quote_truth.json"),
          encoding="utf-8") as _fh:
    QUOTES = json.load(_fh)


# ============================================================
# The fixture
# ============================================================
class TestTheFixture:

    def test_meta_is_stamped(self):
        m = TRUTH["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted",
                  "source"):
            assert m.get(k), k
        assert m["source"] == "scripts/extract_title_box_truth.do"

    @pytest.mark.parametrize("scheme", ["stcolor", "s2color"])
    @pytest.mark.parametrize("key", sorted(_BOX_KEYS))
    def test_boxes_as_measured(self, scheme, key):
        """stcolor fills the box white, s2color bluishgray; both line it
        black (the foreground).  stcolor's subtitle is drawn in
        textboxstyle subheading_gs, whose fill is `color bylabel_outline'
        (gs15): the fill is the box's own text box style's."""
        case = "box_%s_%s" % (key, scheme)
        assert TRUTH[case]["rc"] == 0 and TRUTH[case]["lines"] == []
        fill, stroke, _w = _svg_box(case, _BOX_KEYS[key])
        want = {"stcolor": "#ffffff", "s2color": "#d9e6eb"}[scheme]
        if (scheme, key) == ("stcolor", "subtitle"):
            want = "#f0f0f0"
        assert fill == want
        assert stroke == "#000000"


class TestTheQuoteFixture:
    """quote_truth.json (scripts/extract_quote_truth.do, LT-24): every
    probe a literal command line; twoway refuses a stray double quote
    followed by an apostrophe in option text and draws the compound and
    apostrophe controls."""

    def test_meta_is_stamped(self):
        m = QUOTES["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted",
                  "source"):
            assert m.get(k), k
        assert m["source"] == "scripts/extract_quote_truth.do"

    def test_controls_draw_and_strays_refuse(self):
        rows = {k: v for k, v in QUOTES.items() if k != "_meta"}
        assert len(rows) >= 50
        for k in ("compound", "compound_blank", "apostrophe"):
            assert rows[k]["twoway"]["rc"] == 0, k
        assert rows["title"]["twoway"]["rc"] == 100
        assert rows["title"]["twoway"]["first"] == ") required"
        assert rows["title_blank"]["twoway"]["rc"] == 109
        for k, v in rows.items():
            assert v["command"].startswith("twoway "), k
            assert v["twoway"]["rc"] in (0, 100, 109, 132, 198), k


# ============================================================
# LT-8: the scheme's text box fill and line
# ============================================================
class TestBoxDefaults:

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("scheme", ["stcolor", "s2color"])
    @pytest.mark.parametrize("key", sorted(_BOX_KEYS))
    def test_fill_and_line(self, mode, scheme, key):
        text = _BOX_KEYS[key]
        f, caught = _fig(mode, {key: '"%s", box' % text}, scheme=scheme)
        m = _model(f, key)
        fill, stroke, _w = _svg_box("box_%s_%s" % (key, scheme), text)
        assert str(m.background_fill_color).lower() == fill
        assert str(m.border_line_color).lower() == stroke
        sch = dr.SchemeParser.resolve_or_fallback(scheme, "x")
        assert m.border_line_width == pytest.approx(
            dr.OptionTranslator.translate_lwidth("thin"))
        assert m.border_line_width == pytest.approx(sch.textbox_line_width)
        assert not [w for w in caught if "box" in w]

    @pytest.mark.parametrize("scheme", ["stcolor", "s2color", "s1color",
                                        "economist"])
    def test_scheme_keys(self, scheme):
        """The parser reads `color textbox' and dash's two derived keys
        the generator writes from `linestyle textbox'."""
        sch = dr.SchemeParser.resolve_or_fallback(scheme, "x")
        assert sch._props.get("color textbox"), scheme
        assert sch.textbox_fill_color == sch._color("color textbox")
        assert sch.textbox_line_color == sch._color("color textbox_line")

    @pytest.mark.parametrize("mode", MODES)
    def test_text_keeps_its_own_box(self, mode):
        """text() keeps the text_option fill under stcolor."""
        rec = {"at_kind": "text", "at_y": 30, "at_x": 3000, "at_yaxis": 1,
               "at_xaxis": 1, "at_lines": ["P"], "at_opts": "box"}
        f, _c = _fig(mode, {"added_text": [rec]}, scheme="stcolor")
        lab = [m for m in f.center if type(m).__name__ == "Label"
               and "dash_added_text" in (m.tags or [])]
        assert lab
        sch = dr.SchemeParser.resolve_or_fallback("stcolor", "x")
        assert str(lab[0].background_fill_color).lower() == \
            sch.text_option_fill_color.lower()


# ============================================================
# LT-9: real-valued rings, ordered by value
# ============================================================
def _y(case, text):
    return [t for t in TRUTH[case]["texts"] if t["text"] == text][0]["y"]


def _x(case, text):
    return [t for t in TRUTH[case]["texts"] if t["text"] == text][0]["x"]


def _tagged(panel, key):
    hit = [i for i, m in enumerate(panel)
           if key in list(getattr(m, "tags", None) or [])]
    assert len(hit) == 1, (key, panel)
    return hit[0]


class TestRings:

    @pytest.mark.parametrize("text,want", [
        ("7.5", 7.5), (".5", 0.5), ("100", 100.0), ("101", 101.0),
        ("-1", -1.0), (" 4 ", 4.0), ("inside", 0.0), ("outside", 1.0),
        ("x", None), ("in", None), ("o", None), ("Inside", None),
        ("OUTSIDE", None), ("", None), ("7.5.1", None), ("1e2", 100.0)])
    def test_grammar(self, text, want):
        """title()'s ring(): any real (twoway draws ring(-1) and ring(101)
        with no note: ring_neg, ring_101) and the two words inside and
        outside (ring_w_inside, ring_w_outside); every other word twoway
        refuses on title() (ring_w_<w>, rc 198) is None."""
        assert dr._dash_ring_value(text) == want
        assert dr._DASH_RING_WORDS == {"inside": 0.0, "outside": 1.0}

    @pytest.mark.parametrize("ring,tag", [(7, "ring=7"), (7.5, "ring=7.5"),
                                          (100.0, "ring=100"),
                                          (-1, "ring=-1")])
    def test_tags(self, ring, tag):
        """A side-panel model's ring tag is the ring's shortest form, and
        every reader takes it back as a number (a float tag must not
        break an isdigit() reader)."""
        assert dr._dash_ring_tag(ring) == tag
        assert dr._dash_ring_of_tag(tag) == float(ring)
        for bad in ("ring=", "ring=x", "ring=nan", "rings=3", "dash"):
            assert dr._dash_ring_of_tag(bad) is None

    def test_the_mata_twin(self):
        """dash_parse.mata's _dash_ring_ok holds the same two words."""
        import re
        with open(os.path.join(_HERE, "..", "dash_parse.mata"),
                  encoding="utf-8") as fh:
            src = fh.read()
        body = src[src.index("real scalar _dash_ring_ok("):]
        body = body[:body.index("\n}\n")]
        m = re.search(r"words = \(([^)]*)\)", body)
        assert m
        assert set(re.findall(r'"([^"]+)"', m.group(1))) == \
            set(dr._DASH_RING_WORDS)

    def test_the_fixture_words(self):
        for w, v in dr._DASH_RING_WORDS.items():
            assert TRUTH["ring_w_" + w]["rc"] == 0
            assert TRUTH["ring_w_" + w]["lines"] == []
        for w in ("in", "out", "o", "i", "Inside", "OUTSIDE", "ins",
                  "insid", "ou", "outs", "outsid"):
            assert TRUTH["ring_w_" + w]["rc"] == 198, w
            assert dr._dash_ring_value(w) is None

    @pytest.mark.parametrize("text,want", [
        ("inside", 0.0), ("in", 0.0), ("i", 0.0), ("insid", 0.0),
        ("outside", 1.0), ("o", 1.0), ("ou", 1.0), ("outsid", 1.0),
        ("4.5", 4.5), ("-1", 0.0), ("101", 101.0), ("Inside", None),
        ("OUTSIDE", None), ("x", None), ("insidex", None)])
    def test_legend_grammar(self, text, want):
        """legend(ring()): a lowercase abbreviation of inside or outside
        (leg_ring_w_<w>, drawn with no note), any real, ring(-1) drawn
        inside the plot region (leg_ring_neg)."""
        assert dr._dash_legend_ring(text) == want

    def test_legend_fixture(self):
        inside = _y("leg_ring_0", "Trunk space (cu. ft.)")
        outside = _y("leg_ring_1", "Trunk space (cu. ft.)")
        for w in ("inside", "in", "i", "ins", "insid"):
            assert _y("leg_ring_w_" + w, "Trunk space (cu. ft.)") == inside
            assert TRUTH["leg_ring_w_" + w]["lines"] == []
        for w in ("outside", "out", "o", "ou", "outs", "outsid"):
            assert _y("leg_ring_w_" + w, "Trunk space (cu. ft.)") == outside
            assert TRUTH["leg_ring_w_" + w]["lines"] == []
        assert _y("leg_ring_neg", "Trunk space (cu. ft.)") == inside

    def test_fixture_order(self):
        assert _y("ring_75", "S") < _y("ring_75", "T")
        assert _y("ring_100", "S") < _y("ring_100", "T")
        assert _y("ring_101", "S") < _y("ring_101", "T")
        assert _y("ring_ctrl", "S") > _y("ring_ctrl", "T")
        assert _y("leg_45", "Trunk space (cu. ft.)") > _y("leg_45", "N")
        assert _y("leg_ctrl", "Trunk space (cu. ft.)") < _y("leg_ctrl", "N")
        assert _x("e_r1_ring75", "E") > _x("e_r1_ring75", "T")

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("ring", ["7.5", "100", "101"])
    def test_fractional_order(self, mode, ring):
        f, caught = _fig(mode, {"title": '"T"',
                                "subtitle": '"S", ring(%s)' % ring})
        above = list(f.above)
        assert _tagged(above, "subtitle") > _tagged(above, "title")
        s = above[_tagged(above, "subtitle")]
        assert "ring=%s" % format(float(ring), "g") in s.tags
        assert not [w for w in caught if "ring" in w]

    @pytest.mark.parametrize("mode", MODES)
    def test_point_five_stays_inside(self, mode):
        f, _c = _fig(mode, {"title": '"T"', "subtitle": '"S", ring(.5)',
                            "t1title": '"E"'})
        above = list(f.above)
        assert _tagged(above, "subtitle") < _tagged(above, "t1title")
        assert f.title is not None

    @pytest.mark.parametrize("mode", MODES)
    def test_legend_fraction(self, mode):
        plots = [tp._sc(), tp.plot_for("scatter", yvar="trunk",
                                       xvar="weight")]
        f, _c = _fig(mode, {"note": '"N"',
                            "legend": "position(6) ring(4.5)"}, plots)
        below = list(f.below)
        leg = [i for i, m in enumerate(below) if type(m).__name__ == "Legend"]
        assert len(leg) == 1
        assert leg[0] > _tagged(below, "note")

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("word,inside", [("in", True), ("i", True),
                                             ("o", False), ("-1", True),
                                             ("outs", False)])
    def test_legend_words(self, mode, word, inside):
        plots = [tp._sc(), tp.plot_for("scatter", yvar="trunk",
                                       xvar="weight")]
        f, caught = _fig(mode, {"legend": "ring(%s)" % word}, plots)
        legs = [m for m in f.center if type(m).__name__ == "Legend"]
        assert bool(legs) == inside
        assert not [w for w in caught if "gridringstyle" in w]

    @pytest.mark.parametrize("mode", MODES)
    def test_edge_title_fraction(self, mode):
        f, _c = _fig(mode, {"title": '"T"', "t1title": '"E", ring(7.5)'})
        above = list(f.above)
        assert _tagged(above, "t1title") > _tagged(above, "title")


# ============================================================
# LT-16: placement() at ring(0) is the plot region's compass point
# ============================================================
def _plot_rect(case):
    row = TRUTH[case]
    return [r for r in row["rects"] if r["style"] == "fill:#FFFFFF"
            and r["w"] < row["viewbox"][2] * 0.95][0]


def _third(v, lo, size):
    f = (v - lo) / size
    return 0 if f < 1 / 3 else 2 if f > 2 / 3 else 1


def _measured_place(case, text="TT"):
    """(sx, sy) of the frame symbols where twoway draws *text* in the
    plot region of *case*: the third of the region its anchor lies in."""
    p = _plot_rect(case)
    t = [x for x in TRUTH[case]["texts"] if x["text"] == text][0]
    return (("left", "center", "right")[_third(t["x"], p["x"], p["w"])],
            ("top", "center", "bottom")[_third(t["y"], p["y"], p["h"])])


_PLACEMENTS = ["n", "north", "12", "top", "t", "nor", "N", "ne", "neast",
               "1", "sw", "c", "center", "s", "se", "w", "e", "nw"]


class TestPlacementInside:

    @pytest.mark.parametrize("x", _PLACEMENTS)
    def test_fixture(self, x):
        assert TRUTH["pl_" + x]["rc"] == 0 and TRUTH["pl_" + x]["lines"] == []

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("x", _PLACEMENTS)
    def test_compass(self, mode, x):
        f, caught = _fig(mode, {"title": '"TT", ring(0) placement(%s)' % x})
        [(side, _i, m)] = _box(f, "title")
        assert side == "center"
        sx, sy = _measured_place("pl_" + x)
        assert (m.x.symbol, m.y.symbol) == (sx, sy), x
        want = "center" if (sx, sy) == ("center", "center") else (
            "%s_%s" % (sy, sx))
        assert m.anchor == want
        assert not [w for w in caught if "placement" in w]

    @pytest.mark.parametrize("mode", MODES)
    def test_placement_beats_clock(self, mode):
        f, _c = _fig(mode, {"title": '"TT", ring(0) position(1) '
                                     'placement(sw)'})
        [(_s, _i, m)] = _box(f, "title")
        assert _measured_place("pl_pos1_sw") == ("left", "bottom")
        assert (m.x.symbol, m.y.symbol, m.anchor) == \
            ("left", "bottom", "bottom_left")

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("x,align", [("w", "left"), ("e", "right")])
    def test_outside_aligns(self, mode, x, align):
        """Outside the plot region placement() moves the title box along
        its band (pl_side_w at the plot region's left, pl_side_e at its
        right, as placement(w) and placement(e) inside)."""
        assert _x("pl_side_" + x, "TT") == _x("pl_" + x, "TT")
        f, caught = _fig(mode, {"title": '"TT", placement(%s)' % x})
        assert _model(f, "title").align == align
        assert not [w for w in caught if "placement" in w]

    @pytest.mark.parametrize("mode", MODES)
    def test_outside_north_unchanged(self, mode):
        f, _c = _fig(mode, {"title": '"TT", placement(n)'})
        assert _model(f, "title").align == "center"


# ============================================================
# LT-18: orientation(), width(), height(), the frame styles, style()
# and the side clocks
# ============================================================
def _lw0():
    return dr.SchemeParser.resolve_or_fallback("s2color", "x") \
        .textbox_line_width


def _stroke(case):
    """(colour, width, opacity) of the stroked rect of *case*'s T box."""
    row = TRUTH[case]
    for r in row["rects"]:
        st = dict(kv.split(":", 1) for kv in r["style"].split(";") if kv)
        if st.get("fill") == "none" and r["w"] < 1000:
            return (st.get("stroke", "").lower(),
                    float(st.get("stroke-width", 0)),
                    float(st.get("stroke-opacity", 1)))
    raise AssertionError(case)


def _tbox(case, text="T"):
    """The filled rect of *case* holding *text*'s anchor (its box)."""
    row = TRUTH[case]
    t = [x for x in row["texts"] if x["text"] == text][0]
    return [r for r in row["rects"] if "fill:none" not in r["style"]
            and r["x"] - 1 <= t["x"] <= r["x"] + r["w"] + 1
            and r["y"] - 1 <= t["y"] <= r["y"] + r["h"] + 1
            and r["w"] < row["viewbox"][2] / 2][0]


def _pad(m):
    p = m.padding
    if isinstance(p, dict):
        return [p.get(k, 0) for k in ("left", "right", "top", "bottom")]
    return [int(p or 0)] * 4


_LT18_CASES = ["t_angle", "t_angle_box", "t_blalign", "t_blcolor",
               "t_blpattern", "t_blpattern_solid", "t_blpattern_dot",
               "t_lpattern", "t_blstyle", "t_lstyle_lcolor", "t_blwidth",
               "t_height", "t_lalign", "t_lalign_in", "t_lstyle",
               "t_or_rhorizontal", "t_or_rvertical", "t_or_scale",
               "t_or_vertical", "t_or_vertical_nobox", "t_or_vertical_sub",
               "t_pos2", "t_pos3", "t_pos4", "t_pos8", "t_pos9", "t_pos10",
               "t_pos3_vertical", "t_style", "t_tstyle", "t_width"]

#: orientation() -> the probe and the counter-clockwise angle twoway's
#: SVG rotation shows (rotate(-90) reads upward: +90 degrees).
_ORIENT = {"vertical": "t_or_vertical", "rvertical": "t_or_rvertical",
           "rhorizontal": "t_or_rhorizontal"}


class TestTitleSubopts:

    @pytest.mark.parametrize("case", _LT18_CASES)
    def test_fixture(self, case):
        assert TRUTH[case]["rc"] == 0 and TRUTH[case]["lines"] == [], case

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("orient", sorted(_ORIENT))
    def test_orientation(self, mode, orient):
        """The text and its box turn by the angle twoway's SVG shows, in
        the title's band above the plot: a Label in the panel, at the
        frame's centre, its turned box's bottom on the band's floor."""
        import math
        case = _ORIENT[orient]
        rot = [t for t in TRUTH[case]["texts"] if t["text"] == "T"][0][
            "rotate"]
        f, caught = _fig(mode, {"title": '"T", orientation(%s) box'
                                % orient})
        [(side, _i, m)] = _box(f, "title")
        assert (side, type(m).__name__) == ("above", "Label")
        want = math.radians(-rot) % (2 * math.pi)
        assert m.angle % (2 * math.pi) == pytest.approx(want)
        assert (m.x.target, m.x.symbol) == ("frame", "center")
        assert (m.y, m.x_units, m.y_units) == (0, "screen", "screen")
        assert m.anchor == {"vertical": "center_left",
                            "rvertical": "center_right",
                            "rhorizontal": "top_center"}[orient]
        assert str(m.background_fill_color).lower() == "#d9e6eb"
        assert not [w for w in caught if "title()" in w], caught

    def test_turned_box_as_measured(self):
        """vertical and rvertical turn the box (174 x 127 for 127 x 174);
        rhorizontal keeps it."""
        b, v, r, h = (_tbox(c) for c in ("t_box", "t_or_vertical",
                                         "t_or_rvertical",
                                         "t_or_rhorizontal"))
        assert (v["w"], v["h"]) == pytest.approx((b["h"], b["w"]), abs=0.2)
        assert (r["w"], r["h"]) == pytest.approx((b["h"], b["w"]), abs=0.2)
        assert (h["w"], h["h"]) == pytest.approx((b["w"], b["h"]), abs=0.2)

    @pytest.mark.parametrize("mode", MODES)
    def test_orientation_without_box(self, mode):
        f, caught = _fig(mode, {"title": '"T", orientation(vertical)'})
        [(_s, _i, m)] = _box(f, "title")
        assert type(m).__name__ == "Label" and m.background_fill_color is None
        assert not [w for w in caught if "title()" in w], caught

    @pytest.mark.parametrize("mode", MODES)
    def test_orientation_on_subtitle(self, mode):
        assert [t for t in TRUTH["t_or_vertical_sub"]["texts"]
                if t["text"] == "S"][0]["rotate"] == -90.0
        f, caught = _fig(mode, {"title": '"T"',
                                "subtitle": '"S", orientation(vertical) box'})
        [(side, _i, m)] = _box(f, "subtitle")
        assert (side, type(m).__name__) == ("above", "Label")
        assert m.angle == pytest.approx(__import__("math").pi / 2)
        assert not [w for w in caught if "subtitle()" in w], caught

    @pytest.mark.parametrize("mode", MODES)
    def test_style_is_tstyle(self, mode):
        """style(subheading) draws exactly as tstyle(subheading)."""
        assert TRUTH["t_style"]["texts"] == TRUTH["t_tstyle"]["texts"]
        a, ca = _fig(mode, {"title": '"T", style(subheading)'})
        b, _cb = _fig(mode, {"title": '"T", tstyle(subheading)'})
        ma, mb = _model(a, "title"), _model(b, "title")
        assert (ma.text_font_size, ma.text_color) == \
            (mb.text_font_size, mb.text_color)
        assert ma.text_font_size != _fig(mode, {"title": '"T"'})[0] \
            .title.text_font_size
        assert not [w for w in ca if "title()" in w], ca

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("case,sub", [
        ("t_lstyle", "lstyle(p1)"), ("t_blstyle", "blstyle(p1)"),
        ("t_blcolor", "blcolor(red)"), ("t_blwidth", "blwidth(vthick)"),
        ("t_lstyle_lcolor", "lstyle(p1) lcolor(red)"),
        ("t_blpattern_solid", "blpattern(solid)")])
    def test_frame_line(self, mode, case, sub):
        """The frame's colour and width as measured, explicit options over
        the line style's; a solid pattern is drawn."""
        colour, width, opacity = _stroke(case)
        _c0, width0, _o0 = _stroke("t_box")
        f, caught = _fig(mode, {"title": '"T", %s box' % sub})
        m = _model(f, "title")
        assert str(m.border_line_color).lower() == colour
        assert m.border_line_width == pytest.approx(
            _lw0() * width / width0)
        assert opacity == 1.0 and m.border_line_alpha == 1.0
        assert not [w for w in caught if "title()" in w], caught

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("case,sub", [
        ("t_blpattern", "blpattern(dash)"), ("t_blpattern_dot",
                                             "blpattern(dot)"),
        ("t_lpattern", "lpattern(dash)")])
    def test_patterned_frame_not_drawn(self, mode, case, sub):
        """twoway draws a dashed or dotted title frame with no stroke
        (stroke-opacity 0): only the fill shows."""
        assert _stroke(case)[2] == 0.0
        f, caught = _fig(mode, {"title": '"T", %s box' % sub})
        m = _model(f, "title")
        assert m.border_line_alpha == 0.0
        assert str(m.background_fill_color).lower() == "#d9e6eb"
        assert not [w for w in caught if "title()" in w], caught

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("sub", ["lalign(outside)", "blalign(outside)",
                                     "lalign(inside)"])
    def test_line_alignment(self, mode, sub):
        """outside moves the line out by half its width (t_lalign,
        t_blalign: the stroked rect 2.88 units outside the fill, its width
        5.76); inside is the default (t_lalign_in)."""
        case = {"lalign(outside)": "t_lalign", "blalign(outside)":
                "t_blalign", "lalign(inside)": "t_lalign_in"}[sub]
        s0 = [r for r in TRUTH["t_box"]["rects"] if "fill:none" in
              r["style"] and r["w"] < 1000][0]
        s1 = [r for r in TRUTH[case]["rects"] if "fill:none" in
              r["style"] and r["w"] < 1000][0]
        shift = (s0["x"] - s1["x"]) / _stroke("t_box")[1]
        assert shift == pytest.approx(0.0 if "inside" in sub else 1.0,
                                      abs=0.01)
        for lw in ("", " lwidth(vthick)"):
            base = _model(_fig(mode, {"title": '"T", box%s' % lw})[0],
                          "title")
            f, caught = _fig(mode, {"title": '"T", %s box%s' % (sub, lw)})
            m = _model(f, "title")
            got = [a - b for a, b in zip(_pad(m), _pad(base))]
            want = 0 if "inside" in sub else int(round(
                base.border_line_width / 2))
            assert got == [want] * 4, (sub, lw, got)
            assert not [w for w in caught if "title()" in w], caught

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("sub,case,slot", [
        ("width(50)", "t_width", "w"), ("height(20)", "t_height", "h")])
    def test_fixed_box(self, mode, sub, case, slot):
        """width() and height() fix the box -- the size plus the box's
        margins, centred where the box was -- through the fixed-box fit
        43-06 made for text(), in em of the font."""
        b = _tbox(case)
        size = [t for t in TRUTH[case]["texts"] if t["text"] == "T"][0][
            "size"]
        want_em = b["w" if slot == "w" else "h"] / size
        f, caught = _fig(mode, {"title": '"T", %s box' % sub})
        [(side, _i, m)] = _box(f, "title")
        assert (side, type(m).__name__) == ("above", "Label")
        cbs = [c for cs in f.js_property_callbacks.values() for c in cs
               if getattr(c, "code", None) == dr._DASH_TEXT_BOX_JS]
        assert cbs
        [item] = [it for it in cbs[0].args["items"] if it[0] is m]
        assert item[1][slot] == pytest.approx(want_em, rel=0.03)
        assert item[1]["h" if slot == "w" else "w"] is None
        assert not [w for w in caught if "title()" in w], caught

    @pytest.mark.parametrize("mode", MODES)
    def test_angle_without_box_changes_nothing(self, mode):
        assert TRUTH["t_angle"]["texts"] == TRUTH["t_ctrl"]["texts"]
        f, caught = _fig(mode, {"title": '"T", angle(45)'})
        assert f.title is not None and f.title.text == "T"
        assert not [w for w in caught if "title()" in w], caught

    @pytest.mark.parametrize("mode", MODES)
    def test_angle_with_box_stays_level(self, mode):
        """angle(45) with box: twoway turns the text -45 degrees inside
        its unturned box (t_angle_box); a Bokeh Label turns its box with
        its text, so the title stays level and nothing is named (BUGS.md
        "title(..., angle() box) turns twoway's text inside its box ...",
        open for a ruling)."""
        t = [x for x in TRUTH["t_angle_box"]["texts"] if x["text"] == "T"][0]
        assert t["rotate"] == -45.0
        assert _tbox("t_angle_box")["w"] == _tbox("t_box")["w"]
        f, caught = _fig(mode, {"title": '"T", angle(45) box'})
        assert f.title is not None and f.title.text == "T"
        assert not [w for w in caught if "title()" in w], caught

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("k", [2, 3, 4, 8, 9, 10])
    def test_side_clock(self, mode, k):
        """A box at 2, 3 or 4 o'clock is drawn right of the plot region,
        8, 9 or 10 left of it, level, its top, centre or bottom on the
        plot region's (t_pos<k>)."""
        case = "t_pos%d" % k
        p = _plot_rect(case)
        b = _tbox(case)
        right = k in (2, 3, 4)
        assert (b["x"] >= p["x"] + p["w"] - 0.5) if right else \
            (b["x"] + b["w"] <= p["x"] + 0.5)
        v = {2: "top", 10: "top", 3: "center", 9: "center", 4: "bottom",
             8: "bottom"}[k]
        edge = {"top": (b["y"], p["y"]),
                "center": (b["y"] + b["h"] / 2, p["y"] + p["h"] / 2),
                "bottom": (b["y"] + b["h"], p["y"] + p["h"])}[v]
        assert edge[0] == pytest.approx(edge[1], abs=0.5)
        f, caught = _fig(mode, {"title": '"T", position(%d) box' % k})
        [(side, _i, m)] = _box(f, "title")
        assert (side, type(m).__name__) == \
            ("right" if right else "left", "Label")
        assert (m.y.target, m.y.symbol) == ("frame", v)
        assert (m.x, m.angle) == (0, 0)
        assert m.anchor == ("center_left" if v == "center"
                            else "%s_left" % v)
        assert not [w for w in caught if "title()" in w], caught

    @pytest.mark.parametrize("mode", MODES)
    def test_side_clock_turned(self, mode):
        """position(3) orientation(vertical): the turned box right of the
        plot region, centred on it (t_pos3_vertical)."""
        b, p = _tbox("t_pos3_vertical"), _plot_rect("t_pos3_vertical")
        assert b["y"] + b["h"] / 2 == pytest.approx(p["y"] + p["h"] / 2,
                                                    abs=0.5)
        f, _c = _fig(mode, {"title": '"T", position(3) orientation(vertical)'
                                     ' box'})
        [(side, _i, m)] = _box(f, "title")
        assert side == "right" and m.anchor == "top_center"
        assert m.angle == pytest.approx(__import__("math").pi / 2)

    @pytest.mark.parametrize("mode", MODES)
    def test_scale(self, mode):
        """scale(1.5): the turned box's text and line 1.5 times
        (t_or_scale: the box 1.5 times t_or_vertical's)."""
        a, b = _tbox("t_or_vertical"), _tbox("t_or_scale")
        assert (b["w"] / a["w"], b["h"] / a["h"]) == pytest.approx(
            (1.5, 1.5), abs=0.01)
        f0, _c = _fig(mode, {"title": '"T", orientation(vertical) box'})
        f, _c = _fig(mode, {"title": '"T", orientation(vertical) box',
                            "scale": "1.5"})
        [(_s, _i, m0)] = _box(f0, "title")
        [(_s, _i, m)] = _box(f, "title")
        assert dr.OptionTranslator.css_to_pt(m.text_font_size) == \
            pytest.approx(1.5 * dr.OptionTranslator.css_to_pt(
                m0.text_font_size))
        assert m.border_line_width == pytest.approx(
            1.5 * m0.border_line_width)
        assert m.angle == m0.angle


#: In Chrome: each figure's picture as its save tool exports it, the
#: bounding boxes of its yellow (the box's fill), red (the text) and blue
#: (the frame) pixels, and its frame; CSP violations collected.
_CHROME_JS = r"""
<script>
const V = [];
addEventListener('securitypolicyviolation', e => V.push(e.violatedDirective));
window.addEventListener('load', () => setTimeout(() => {
  const out = {V, plots: []};
  const seen = new Set();
  const visit = (v) => {
    if (v == null || seen.has(v)) return;
    seen.add(v);
    if (v.frame && v.export) {
      const c = v.export("png", false).canvas;
      const W = c.width, H = c.height;
      const d = c.getContext('2d').getImageData(0, 0, W, H).data;
      const box = (f) => { let x0 = 1e9, y0 = 1e9, x1 = -1, y1 = -1;
        for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
          const i = (y * W + x) * 4;
          if (f(d[i], d[i + 1], d[i + 2], d[i + 3])) {
            if (x < x0) x0 = x; if (y < y0) y0 = y;
            if (x > x1) x1 = x; if (y > y1) y1 = y; } }
        return x1 < 0 ? null : [x0, y0, x1 - x0 + 1, y1 - y0 + 1]; };
      const b = v.frame.bbox;
      out.plots.push({
        yellow: box((r, g, b2, a) => r > 230 && g > 230 && b2 < 60 && a > 200),
        red: box((r, g, b2, a) => r > 200 && g < 80 && b2 < 80 && a > 200),
        frame: [b.left, b.top, b.width, b.height]});
    }
    for (const c of (v.child_views || [])) visit(c);
  };
  for (const v of Object.values(Bokeh.index)) visit(v);
  parent.postMessage('DASHPROBE' + JSON.stringify(
    Object.assign(out, {W: innerWidth})), '*');
}, 3000));
</script>
"""


def _chrome(mode, go):
    import responsive_probe
    if responsive_probe.find_chrome() is None:
        pytest.skip("headless Chrome is not installed (set DASH_CHROME)")
    spec = tp._spec([tp._sc()], {"scheme": "s2color"}, go)
    if mode == "saved":
        page = tp._standalone_page(spec)[2]
    else:
        from bokeh.embed import file_html
        from bokeh.resources import INLINE
        page = file_html(tp._served(spec)[0], INLINE, "served")
    mp = pytest.MonkeyPatch()
    mp.setattr(responsive_probe, "PROBE_JS", _CHROME_JS)
    try:
        got = responsive_probe.measure_many(page, (1000,))[1000]
    finally:
        mp.undo()
    assert got["V"] == []
    assert len(got["plots"]) == 1, got
    return got["plots"][0]


_LOUD = "fcolor(yellow) lcolor(blue) color(red)"


@pytest.mark.release
@pytest.mark.parametrize("mode", MODES)
class TestTitleSuboptsInChrome:

    def test_turned_title(self, mode):
        """orientation(vertical): the box above the frame, centred on it,
        turned (wider than tall, as t_or_vertical's 174 x 127), the text
        inside it taller than wide."""
        a = _chrome(mode, {"title": '"Tgxyz", box %s' % _LOUD})
        p = _chrome(mode, {"title": '"Tgxyz", orientation(vertical) box %s'
                                    % _LOUD})
        y, r, fr = p["yellow"], p["red"], p["frame"]
        assert y is not None and r is not None
        assert y[1] + y[3] <= fr[1] + 1
        assert y[0] + y[2] / 2 == pytest.approx(fr[0] + fr[2] / 2, abs=2)
        ya = a["yellow"]
        assert (y[2], y[3]) == pytest.approx((ya[3], ya[2]), abs=2)
        assert r[3] > r[2]
        assert y[0] <= r[0] and r[0] + r[2] <= y[0] + y[2]

    def test_side_clock(self, mode):
        """position(3): the box right of the frame, level with its
        centre (t_pos3); the text level (wider than tall)."""
        p = _chrome(mode, {"title": '"Tgx", position(3) box %s' % _LOUD})
        y, r, fr = p["yellow"], p["red"], p["frame"]
        assert y[0] >= fr[0] + fr[2]
        assert y[1] + y[3] / 2 == pytest.approx(fr[1] + fr[3] / 2, abs=2)
        assert r[2] > r[3]
