"""test_legend_title_style.py -- legend(title()) and legend(subtitle()) are
drawn as twoway draws them (WP-43 section 43-01: LT-1, LT-15).

LT-1: twoway draws the legend's title and subtitle in the scheme's
``textboxstyle leg_title`` / ``leg_subtitle`` text boxes (heading and
subheading under s2color; stcolor's leg_title is legend_title, heading's
size in black), not in the key text's size and colour.

Ground truth: test/fixtures/legend_title_truth.json, written by
scripts/extract_legend_title_truth.do from twoway's SVG export (SVG px,
720 per inch).  ``style_<scheme>`` holds T's and S's size and fill and the
key text's size for ``legend(title("T") subtitle("S"))``.
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
_FIXTURE = os.path.join(_HERE, "fixtures", "legend_title_truth.json")
with open(_FIXTURE, encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)
with open(os.path.join(_HERE, "fixtures", "scheme_truth.json"),
          encoding="utf-8") as _fh:
    SCHEMES = {k: v for k, v in json.load(_fh).items() if k != "_meta"}

STYLE_SCHEMES = ("stcolor", "s2color", "s1mono", "economist", "meta")
EDGES = ("t1", "t2", "b1", "b2", "l1", "l2", "r1", "r2")


def _legend(mode, opt, scheme="s2color"):
    """``(legend, messages)`` of the two-scatter graph with legend(*opt*)."""
    fig, caught = G._build(mode, G.TWO, opt, scheme=scheme)
    return G._legend(fig), caught


def _pt(size):
    m = re.fullmatch(r"\s*([0-9.]+)\s*(pt|px)\s*", str(size))
    assert m, size
    v = float(m.group(1))
    return v if m.group(2) == "pt" else v * 0.75


class TestTheFixture:

    def test_complete(self):
        meta = TRUTH["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted",
                  "source"):
            assert meta.get(k), k
        assert meta["source"] == "scripts/extract_legend_title_truth.do"
        keys = (["style_" + s for s in STYLE_SCHEMES]
                + ["control", "title_box", "title_box_margin", "title_just",
                   "title_tstyle", "sub_style", "sub_under", "block_box",
                   "scale_block", "title_multi"]
                + ["title_pos_%d" % k for k in (0, 3, 5, 6, 9, 12)])
        for k in keys:
            assert TRUTH[k]["rc"] == 0, k
        for e in EDGES:
            assert TRUTH["edge_" + e]["rc"] == 198, e
            assert TRUTH["edge_" + e]["first_line"] == (
                "option %stitle() not allowed" % e)


class TestSchemeStyles:

    @pytest.mark.parametrize("scheme", sorted(SCHEMES))
    def test_each_scheme(self, scheme):
        sc = dr.SchemeParser(scheme)
        truth = SCHEMES[scheme]
        for box, dflt in (("title", "heading"), ("subtitle", "subheading"),
                          ("note", "small_body"), ("caption", "body")):
            want = truth.get("textboxstyle_leg_" + box) or dflt
            assert sc.legend_text_styles[box] == want, (scheme, box)
        assert sc._legend_text_style("bogus_box", "body") == "body"


class TestTitleStyle:

    @pytest.mark.parametrize("scheme", STYLE_SCHEMES)
    @pytest.mark.parametrize("mode", MODES)
    def test_scheme_style(self, mode, scheme):
        rec = TRUTH["style_" + scheme]
        lg, _ = _legend(mode, 'title("T")', scheme)
        sc = dr.SchemeParser(scheme)
        size, colour = sc.textbox_style(sc.legend_text_styles["title"])
        assert lg.title == "T"
        assert lg.title_text_font_size == size
        assert str(lg.title_text_color).lower() == str(colour).lower()
        assert str(lg.title_text_color).lower() == rec["T"]["fill"]
        want = rec["T"]["size"] / rec["key_size"]
        got = _pt(lg.title_text_font_size) / _pt(lg.label_text_font_size)
        assert abs(got / want - 1) < 0.02, (got, want)

    @pytest.mark.parametrize("scheme", STYLE_SCHEMES)
    @pytest.mark.parametrize("mode", MODES)
    def test_subtitle_alone(self, mode, scheme):
        rec = TRUTH["style_" + scheme]
        lg, msgs = _legend(mode, 'subtitle("S")', scheme)
        assert lg.title == "S"
        assert str(lg.title_text_color).lower() == rec["S"]["fill"]
        want = rec["S"]["size"] / rec["key_size"]
        got = _pt(lg.title_text_font_size) / _pt(lg.label_text_font_size)
        assert abs(got / want - 1) < 0.02, (got, want)
        assert not [m for m in msgs if "subtitle" in m], msgs

    @pytest.mark.parametrize("mode", MODES)
    def test_tstyle(self, mode):
        rec = TRUTH["title_tstyle"]
        lg, msgs = _legend(mode, 'title("T", tstyle(body))')
        assert abs(_pt(lg.title_text_font_size) / _pt(lg.label_text_font_size)
                   - rec["T"]["size"] / rec["key_size"]) < 0.02
        assert str(lg.title_text_color).lower() == rec["T"]["fill"]
        assert not [m for m in msgs if "tstyle" in m], msgs

    @pytest.mark.parametrize("mode", MODES)
    def test_tstyle_unknown_noted(self, mode):
        _lg, msgs = _legend(mode, 'title("T", tstyle(bogus))')
        hits = [m for m in msgs if "named style bogus not found in class "
                "textboxstyle, default attributes used" in m]
        assert len(hits) == 1, msgs


# ---------------------------------------------------------------------------
# LT-15 (D69): the title block's place, box and the title beside a
# subtitle, drawn by the legend's own stylesheet.
# ---------------------------------------------------------------------------

def _css(lg):
    """The legend title block's CSS (the dash_legend_title stylesheet)."""
    got = [ss.css for ss in lg.stylesheets
           if "dash_legend_title" in (ss.tags or [])]
    assert len(got) == 1, lg.stylesheets
    return got[0]


def _rule(css, sel, prop):
    """The value *css* gives *prop* in the rule for *sel*, or None."""
    m = re.search(re.escape(sel) + r"\{([^}]*)\}", css)
    if not m:
        return None
    for part in m.group(1).split(";"):
        k, _, v = part.partition(":")
        if k.strip() == prop:
            return v.strip()
    return None


def _named(msgs, box):
    return [m for m in msgs if "legend(%s)" % box in m
            and "not implemented" in m]


class TestSubtitleStyle:

    @pytest.mark.parametrize("mode", MODES)
    def test_two_styles(self, mode):
        """title("T") subtitle("S"): T above S, both centred on one x, T
        in the title's text box and S in the subtitle's (sub_under)."""
        rec = TRUTH["sub_under"]
        assert rec["T"]["y"] < rec["S"]["y"]
        assert rec["T"]["x"] == rec["S"]["x"]
        lg, msgs = _legend(mode, 'title("T") subtitle("S")')
        sc = dr.SchemeParser("s2color")
        assert lg.title == "T\nS"
        assert lg.title_text_font_size == sc.textbox_style("subheading")[0]
        css = _css(lg)
        ratio = rec["T"]["size"] / rec["S"]["size"]
        fs = _rule(css, ".bk-title::first-line", "font-size")
        assert fs.endswith("em") and abs(float(fs[:-2]) / ratio - 1) < 0.01
        assert _rule(css, ".bk-title::first-line", "color") == \
            rec["T"]["fill"]
        assert _rule(css, ".bk-title", "text-align") == "center"
        assert not [m for m in msgs if "legend(" in m and "title" in m]

    @pytest.mark.parametrize("mode", MODES)
    def test_size_color(self, mode):
        rec = TRUTH["sub_style"]
        lg, msgs = _legend(mode, 'subtitle("S", size(large) color(red))')
        assert lg.title == "S"
        assert abs(_pt(lg.title_text_font_size) / _pt(lg.label_text_font_size)
                   - rec["S"]["size"] / rec["key_size"]) < 0.02
        assert str(lg.title_text_color).lower() == rec["S"]["fill"]
        assert not _named(msgs, "subtitle"), msgs

    @pytest.mark.parametrize("mode", MODES)
    def test_scale_rides_the_title_size(self, mode):
        """The CSS is in em of the title text, so scale() (and the width
        scale, which multiplies title_text_font_size) carries it."""
        a, _ = _legend(mode, 'title("T", box) subtitle("S")')
        fig, _ = G._build(mode, G.TWO, 'title("T", box) subtitle("S")',
                          go={"scale": "1.5"})
        b = G._legend(fig)
        assert _css(a) == _css(b)
        assert abs(_pt(b.title_text_font_size)
                   / _pt(a.title_text_font_size) - 1.5) < 0.01


class TestTitleSubopts:

    @pytest.mark.parametrize("mode", MODES)
    def test_centred_by_default(self, mode):
        rec = TRUTH["control"]
        box = [r for r in rec["rects"] if r["fill"] == "#ffffff"
               and r["y"] > 2000][0]
        assert abs(rec["T"]["x"] - (box["x"] + box["w"] / 2)) < 1
        lg, _ = _legend(mode, 'title("T")')
        css = _css(lg)
        assert _rule(css, ".bk-title", "margin-left") == "auto"
        assert _rule(css, ".bk-title", "margin-right") == "auto"
        assert _rule(css, ".bk-title", "width") == "fit-content"

    @pytest.mark.parametrize("k,loc,side", [
        (12, "above", "center"), (6, "below", "center"),
        (5, "below", "right")])
    @pytest.mark.parametrize("mode", MODES)
    def test_position(self, mode, k, loc, side):
        rec = TRUTH["title_pos_%d" % k]
        key_y = min(t["y"] for t in rec["texts"] if not t["anchor"])
        assert (rec["T"]["y"] < key_y) == (loc == "above")
        assert (rec["T"]["anchor"] == "end") == (side == "right")
        lg, msgs = _legend(mode, 'title("T", position(%d))' % k)
        assert lg.title_location == loc
        css = _css(lg)
        want = {"center": ("auto", "auto"), "right": ("auto", "0")}[side]
        assert (_rule(css, ".bk-title", "margin-left"),
                _rule(css, ".bk-title", "margin-right")) == want
        assert not _named(msgs, "title"), msgs

    @pytest.mark.parametrize("k,side", [(0, ("auto", "auto")),
                                        (3, ("auto", "0")),
                                        (9, ("0", "auto"))])
    @pytest.mark.parametrize("mode", MODES)
    def test_key_row_clocks_drawn_above(self, mode, k, side):
        """twoway puts the title in the key row at 0, 3 and 9 (title_pos_k:
        T's y is the keys' row); Bokeh's legend draws a title beside its
        keys only turned on its side, so dash draws it above at that end
        (a documented difference)."""
        rec = TRUTH["title_pos_%d" % k]
        key_y = min(t["y"] for t in rec["texts"] if not t["anchor"])
        assert abs(rec["T"]["y"] - key_y) < 20
        lg, _ = _legend(mode, 'title("T", position(%d))' % k)
        assert lg.title_location == "above"
        css = _css(lg)
        assert (_rule(css, ".bk-title", "margin-left"),
                _rule(css, ".bk-title", "margin-right")) == side

    @pytest.mark.parametrize("mode", MODES)
    def test_justification(self, mode):
        """justification(right) aligns the text inside its own box, the
        block staying centred (title_just: T moves 46 of 1320 SVG px)."""
        rec, ctl = TRUTH["title_just"], TRUTH["control"]
        assert rec["T"]["anchor"] == "end"
        assert 0 < rec["T"]["x"] - ctl["T"]["x"] < 100
        lg, _ = _legend(mode, 'title("T", justification(right))')
        css = _css(lg)
        assert _rule(css, ".bk-title", "text-align") == "right"
        assert _rule(css, ".bk-title", "margin-left") == "auto"
        assert lg.title_text_align == "right"

    @pytest.mark.parametrize("mode", MODES)
    def test_box(self, mode):
        rec = TRUTH["title_box"]
        frame = [r for r in rec["rects"] if r["fill"] == "#d9e6eb"]
        line = [r for r in rec["rects"] if r["stroke"] == "#000000"
                and r["w"] < 200]
        assert frame and line
        lg, msgs = _legend(mode, 'title("T", box)')
        css = _css(lg)
        assert _rule(css, ".bk-title", "background-color") == "#d9e6eb"
        border = _rule(css, ".bk-title", "border").split()
        assert border[1:] == ["solid", "#000000"]
        # 5.76 SVG px at 139.96 px text: the line in em of the title.
        assert abs(float(border[0][:-2])
                   - line[0]["stroke_width"] / rec["T"]["size"]) < 0.005
        assert _rule(css, ".bk-title", "padding").endswith("em")
        assert not _named(msgs, "title"), msgs

    @pytest.mark.parametrize("mode", MODES)
    def test_box_options(self, mode):
        lg, msgs = _legend(mode, 'title("T", box fcolor(red) lcolor(blue) '
                                 'lpattern(dash) lwidth(thick) '
                                 'margin(large))')
        css = _css(lg)
        assert _rule(css, ".bk-title", "background-color") == "#ff0000"
        assert _rule(css, ".bk-title", "border").split()[1:] == [
            "dashed", "#0000ff"]
        small, _ = _legend(mode, 'title("T", box)')
        pad = lambda c: float(_rule(c, ".bk-title", "padding").split()[0][:-2])  # noqa: E731
        assert pad(css) > 5 * pad(_css(small))
        assert not _named(msgs, "title"), msgs
        lg, _ = _legend(mode, 'title("T", box nobox)')
        assert _rule(_css(lg), ".bk-title", "border") is None

    @pytest.mark.parametrize("sub", sorted(
        k[6:] for k, v in TRUTH.items()
        if k.startswith("title_") and v.get("same_as_control") is False))
    @pytest.mark.parametrize("mode", MODES)
    def test_named(self, mode, sub):
        arg = {"orientation": "orientation(vertical)",
               "height": "height(20)", "alignment": "alignment(top)",
               "placement": "placement(east)", "ring": "ring(0)"}[sub]
        _lg, msgs = _legend(mode, 'title("T", %s)' % arg)
        hits = _named(msgs, "title")
        assert len(hits) == 1 and sub in hits[0], msgs

    def test_the_silent_names_are_the_fixtures(self):
        assert dr._DASH_LEGEND_TITLE_SILENT == {
            k[6:] for k, v in TRUTH.items()
            if k.startswith("title_") and v.get("same_as_control") is True}

    @pytest.mark.parametrize("sub", sorted(
        k[6:] for k, v in TRUTH.items()
        if k.startswith("title_") and v.get("same_as_control") is True))
    @pytest.mark.parametrize("mode", MODES)
    def test_silent(self, mode, sub):
        arg = sub if sub in ("bexpand", "span", "prefix", "suffix") else \
            {"width": "width(40)", "angle": "angle(45)",
             "linegap": "linegap(5)", "bmargin": "bmargin(large)",
             "lstyle": "lstyle(foreground)", "blcolor": "blcolor(red)",
             "blwidth": "blwidth(thick)", "lalign": "lalign(outside)"}[sub]
        _lg, msgs = _legend(mode, 'title("T", %s)' % arg)
        assert not _named(msgs, "title"), msgs

    @pytest.mark.parametrize("mode", MODES)
    def test_no_user_text_in_the_css(self, mode):
        lg, _ = _legend(mode, 'title("a}b{</style>", box fcolor(bogus) '
                              'lcolor("1 2 3;x")) subtitle("q}")')
        css = _css(lg)
        for bad in ("}b{", "</style>", "bogus", ";x", "q}"):
            assert bad not in css
        assert re.fullmatch(r"[A-Za-z0-9#.:;{}() \-]*", css), css


class TestByLegend:

    @pytest.mark.parametrize("mode", MODES)
    def test_cell_carries_the_title_block(self, mode):
        from bokeh.models import Legend
        import test_mode_parity as tp
        spec = tp._spec(G.TWO, {"scheme": "s2color"},
                        {"by": "rep", "legend": 'title("T") subtitle("S")'})
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
        assert lg.title == "T\nS"
        css = _css(lg)
        assert _rule(css, ".bk-title::first-line", "color") == "#1e2d53"
        assert _rule(css, ".bk-title", "margin-left") == "auto"


# ---------------------------------------------------------------------------
# The differences ruling D69 keeps (WP-43 LT-15), each against a measured
# twoway example in legend_title_truth.json.
# ---------------------------------------------------------------------------

#: No open difference of the legend title block.
LEGEND_TITLE_KNOWN = {}

#: What ruling D69 keeps on purpose: Bokeh's legend draws its title only
#: above or below its keys (beside them turned on its side), and a CSS
#: first line is one line with no frame of its own.
LEGEND_TITLE_DELIBERATE = {
    "pos_0": "D69: position(0) draws the title above the keys, centred; "
             "twoway draws it in the key row",
    "pos_3": "D69: position(3) draws the title above the keys at the "
             "right; twoway draws it right of the keys, in their row",
    "pos_9": "D69: position(9) draws the title above the keys at the "
             "left; twoway draws it left of the keys, in their row",
    "box_with_subtitle": "D69: title(, box) beside subtitle() frames both "
                         "lines; twoway frames the title alone",
    "multiline_with_subtitle": "D69: a title of two lines above a "
                               "subtitle draws its second line in the "
                               "subtitle's style; twoway draws both in "
                               "the title's",
}


def _title_differences(mode):
    """``{key: None | difference}`` of the title block against twoway."""
    out = {}
    for k in (0, 3, 9):
        rec = TRUTH["title_pos_%d" % k]
        key_y = min(t["y"] for t in rec["texts"] if not t["anchor"])
        in_row = abs(rec["T"]["y"] - key_y) < 20
        lg, _ = _legend(mode, 'title("T", position(%d))' % k)
        out["pos_%d" % k] = (
            "twoway in the key row, dash %s" % lg.title_location
            if in_row and lg.title_location in ("above", "below") else None)
    rec = TRUTH["block_box"]
    frame = [r for r in rec["rects"] if r["fill"] == "#d9e6eb"][0]
    s_in = frame["y"] <= rec["S"]["y"] <= frame["y"] + frame["h"]
    lg, _ = _legend(mode, 'title("T", box) subtitle("S")')
    both = "\n" in lg.title and _rule(_css(lg), ".bk-title", "border")
    out["box_with_subtitle"] = (
        "twoway frames T only, dash both lines" if both and not s_in
        else None)
    rec = TRUTH["title_multi"]
    lg, _ = _legend(mode, 'title("T1" "T2") subtitle("S")')
    split = rec["T2"]["size"] == rec["T1"]["size"] != rec["S"]["size"]
    out["multiline_with_subtitle"] = (
        "twoway draws T2 at T1's size, dash at S's"
        if split and lg.title == "T1\nT2\nS" else None)
    return out


class TestKnownDifferences:

    @pytest.mark.parametrize("mode", MODES)
    def test_every_known_difference_is_open(self, mode):
        from known_differences import known_problems
        res = _title_differences(mode)
        assert known_problems(res, LEGEND_TITLE_KNOWN, "legend_title",
                              deliberate=LEGEND_TITLE_DELIBERATE) == []
        # Each kept difference is still one, and each names its ruling.
        for key, why in LEGEND_TITLE_DELIBERATE.items():
            assert res[key] is not None, key
            assert why.startswith("D69: ")
