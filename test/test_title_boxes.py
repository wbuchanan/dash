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
