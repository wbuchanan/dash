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
