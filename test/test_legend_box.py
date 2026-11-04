"""test_legend_box.py -- the legend's box and its key texts' text boxes,
as twoway draws them (WP-43 section 43-03: LT-2, LT-3, LT-6, LT-7,
LT-10).

LT-2: twoway's ``legend(nobox)`` and ``legend(box)`` are the key texts'
textbox options (legend_options.sthlp): nobox leaves the legend as the
default draws it, box frames each key's text; neither touches the region
box, which only the scheme and region() draw.

Ground truth: test/fixtures/legend_box_truth.json, written by
scripts/extract_legend_box_truth.do from twoway's SVG export (SVG user
units, 720 per inch; three scatters; s2color unless the row says).
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
with open(os.path.join(_HERE, "fixtures", "legend_box_truth.json"),
          encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)

#: The key texts of the fixture's three scatters.
KEYS = ("Mileage (mpg)", "Price", "Turn circle (ft.)")


def _rects(key):
    """The fixture row *key*'s rects smaller than the canvas, as
    ``(x0, y0, x1, y1, style)``."""
    row = TRUTH[key]
    return [(r["x"], r["y"], r["x"] + r["w"], r["y"] + r["h"], r["style"])
            for r in row["rects"] if r["w"] < row["viewbox"][2] - 1]


def _key_frames(key):
    """The rects of row *key* that hold one key text's anchor and no
    other: twoway's frame round each key text (fill and line)."""
    texts = [t for t in TRUTH[key]["texts"] if t["text"] in KEYS]
    out = []
    for r in _rects(key):
        # A line is drawn inside the fill: up to half its width in.
        inside = [t for t in texts if r[0] - 15 <= t["x"] <= r[2] + 1
                  and r[1] <= t["y"] <= r[3] + 1]
        if len(inside) == 1:
            out.append(r)
    return out


def _legend_region(key):
    """The legend's region box (fill and line) of row *key*: the rects
    holding every key text."""
    texts = [t for t in TRUTH[key]["texts"] if t["text"] in KEYS]
    return [r for r in _rects(key)
            if all(r[0] <= t["x"] <= r[2] and r[1] <= t["y"] <= r[3]
                   for t in texts)]


class TestTheFixture:

    def test_complete(self):
        meta = TRUTH["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted",
                  "source", "base", "units"):
            assert meta.get(k), k
        assert meta["source"] == "scripts/extract_legend_box_truth.do"
        for k, row in TRUTH.items():
            if k != "_meta":
                assert row["rc"] == 0, (k, row["lines"])

    def test_nobox_is_the_default(self):
        """nobox draws the default; box and box nobox frame each key text
        and leave the region box (s2color and stcolor)."""
        for sfx in ("", "_st"):
            ctl = TRUTH["ctl" + sfx]
            assert TRUTH["nobox" + sfx]["rects"] == ctl["rects"]
            assert TRUTH["nobox" + sfx]["texts"] == ctl["texts"]
            assert _legend_region("box" + sfx) == _legend_region("ctl" + sfx)
            assert len(_key_frames("box" + sfx)) == 2 * len(KEYS)
        assert _key_frames("box_nobox") == _key_frames("box")


@pytest.mark.parametrize("mode", MODES)
class TestNobox:

    @pytest.mark.parametrize("scheme", ["s2color", "stcolor"])
    def test_changes_nothing(self, mode, scheme):
        """legend(nobox) and legend(box): the region box's line and fill
        are the default's (legend_box_truth.json nobox, box)."""
        _f, ref, _ = G._fig_legend(mode, G.THREE, "", scheme=scheme)
        for opt in ("nobox", "box"):
            _f, lg, caught = G._fig_legend(mode, G.THREE, opt,
                                           scheme=scheme)
            assert lg.border_line_color == ref.border_line_color, opt
            assert lg.background_fill_color == ref.background_fill_color, \
                opt
            assert lg.padding == ref.padding, opt
            assert not [w for w in caught if opt in w], caught


# ---------------------------------------------------------------------------
# LT-3: the key texts' textbox options
# ---------------------------------------------------------------------------

def _frame_of(key, text):
    """``(fill rect, line rect, text)`` of twoway's frame round the key
    text *text* in row *key*."""
    t = [x for x in TRUTH[key]["texts"] if x["text"] == text][0]
    fr = [r for r in _key_frames(key) if r[0] - 15 <= t["x"] <= r[2]
          and r[1] <= t["y"] <= r[3] + 1]
    fill = [r for r in fr if "fill:none" not in r[4]]
    line = [r for r in fr if "fill:none" in r[4]]
    return (fill[0] if fill else None), (line[0] if line else None), t


def _style(r, name):
    for kv in r[4].split(";"):
        if kv.startswith(name + ":"):
            return kv.split(":", 1)[1].lower()
    return None


def _sheet(lg, tag="dash_legend_keytext"):
    return "".join(ss.css for ss in lg.stylesheets
                   if tag in (getattr(ss, "tags", None) or []))


def _font_pt(lg):
    return dr.OptionTranslator.css_to_pt(lg.label_text_font_size)


def _em(css, prop, rule="label"):
    """The em value of *prop* in the key-text sheet's label rule (or
    its ::before rule), or None."""
    import re
    sel = ".bk-label::before{" if rule == "before" else ".bk-label{"
    i = css.find(sel)
    if i < 0:
        return None
    body = css[i + len(sel):css.index("}", i)]
    for decl in body.split(";"):
        if decl.startswith(prop + ":"):
            return decl.split(":", 1)[1]
    return None


class TestKeyTextFixture:

    def test_measured(self):
        """The fixture's facts the drawing follows: the frame is the
        text's extent, one text size high (baseline - 0.85 size to + 0.15),
        no margin by default, the line inside, in the scheme's text box
        fill; justification() moves no text; alignment() moves the text,
        not its frame; margin(large) is 8 units each side; linegap(5)
        adds 5 units to the line pitch; a dashed lpattern() draws no
        line."""
        f, line, t = _frame_of("box", "Mileage (mpg)")
        assert abs(f[0] - t["x"]) < 0.01
        assert abs((f[3] - f[1]) - t["size"]) < 0.05
        assert abs((t["y"] - f[1]) / t["size"] - 0.85) < 0.01
        assert _style(f, "fill") == "#d9e6eb"
        assert _style(line, "stroke") == "#000000"
        f, _l, _t = _frame_of("box_st", "Mileage (mpg)")
        assert _style(f, "fill") == "#ffffff"
        for k in ("just_right", "just_center"):
            for a, b in zip(TRUTH[k]["texts"], TRUTH["cols1"]["texts"]):
                if a["text"] in KEYS:
                    w = {"start": 0, "middle": 0.5, "end": 1}[a["anchor"]]
                    assert a["y"] == b["y"]
        ctl_y = [t["y"] for t in TRUTH["ctl"]["texts"] if t["text"] in KEYS]
        for k, d in (("align_top", -15.09), ("align_bottom", -15.09),
                     ("align_middle", 0.0), ("align_baseline", 14.97)):
            ys = [t["y"] for t in TRUTH[k]["texts"] if t["text"] in KEYS]
            assert all(abs(y - c - d) < 0.05 for y, c in zip(ys, ctl_y)), k
        assert _frame_of("box_align_top", "Price")[0] == \
            _frame_of("box", "Price")[0]
        f, _l, t = _frame_of("box_margin_large", "Price")
        assert abs((t["x"] - f[0]) - 8 * 28.8) < 0.2
        assert abs((f[3] - f[1]) - t["size"] - 16 * 28.8) < 0.2
        two = [t["y"] for t in TRUTH["linegap5"]["texts"]
               if t["text"] in ("Mileage", "(mpg)")]
        assert abs((two[1] - two[0]) - 99.99 - 5 * 28.8) < 0.2
        _f, line, _t = _frame_of("box_lpattern", "Price")
        assert _style(line, "stroke-opacity") == "0.00"


@pytest.mark.parametrize("mode", MODES)
class TestKeyText:

    @pytest.mark.parametrize("opt", [
        "box", "bcolor(gs14)", "box bcolor(gs14)", "box fcolor(red)",
        "box bfcolor(red)", "box lcolor(red) lwidth(thick)",
        "box lpattern(dash)", "justification(right)", "alignment(top)",
        "margin(large)", "linegap(5)", "tstyle(heading)"])
    def test_no_note(self, mode, opt):
        """Every key-text textbox option is drawn: no note names it."""
        _f, _lg, caught = G._fig_legend(mode, G.THREE, opt)
        assert not [w for w in caught if "not implemented" in w
                    or "legend(" in w], caught

    def test_native(self, mode):
        """tstyle(heading) sizes and colours the key texts in the
        scheme's heading style, size() and color() winning; justification()
        changes nothing (twoway's key text box is its text's width)."""
        sch = dr.SchemeParser.resolve_or_fallback("s2color", "test")
        size, colour = sch.textbox_style("heading")
        _f, lg, _ = G._fig_legend(mode, G.THREE, "tstyle(heading)")
        assert _font_pt(lg) == pytest.approx(
            dr.OptionTranslator.css_to_pt(size), abs=0.01)
        assert lg.label_text_color == colour
        _f, small, _ = G._fig_legend(mode, G.THREE,
                                     "tstyle(heading) size(small)")
        _f, ref, _ = G._fig_legend(mode, G.THREE, "size(small)")
        assert small.label_text_font_size == ref.label_text_font_size
        _f, j, _ = G._fig_legend(mode, G.THREE, "cols(1) justification(right)")
        assert _sheet(j) == ""

    @pytest.mark.parametrize("opt,fill,line", [
        ("box", "#d9e6eb", "#000000"),
        ("box bcolor(gs14)", "#e0e0e0", "#e0e0e0"),
        ("box fcolor(red)", "#ff0000", "#000000"),
        ("box lcolor(red)", "#d9e6eb", "#ff0000"),
        ("holes(1) cols(1) box", "#d9e6eb", "#000000")])
    def test_frames(self, mode, opt, fill, line):
        """box frames every key text behind it, in the scheme's text box
        fill and line or bcolor()/fcolor()/lcolor() (legend_box_truth.json
        box, box_bcolor, box_fcolor, holes_box)."""
        _f, lg, _ = G._fig_legend(mode, G.THREE, opt)
        css = _sheet(lg)
        assert _em(css, "background-color", "before") == fill
        assert line in (_em(css, "outline", "before") or "")
        assert _em(css, "z-index", "before") == "-1"

    def test_frame_line(self, mode):
        """lwidth(thick) lines the frame inside at thick's width; a
        dashed lpattern() draws no line (box_lcolor, box_lpattern)."""
        T = dr.OptionTranslator
        _f, lg, _ = G._fig_legend(mode, G.THREE, "box lwidth(thick)")
        css = _sheet(lg)
        w = float(_em(css, "outline", "before").split()[0][:-2])
        want = T.translate_lwidth("thick", None, 4.0) / (
            _font_pt(lg) * T.PX_PER_PT)
        assert w == pytest.approx(want, rel=0.01)
        assert _em(css, "outline-offset", "before") == "-%s" % \
            _em(css, "outline", "before").split()[0]
        _f, lg, _ = G._fig_legend(mode, G.THREE, "box lpattern(dash)")
        assert _em(_sheet(lg), "outline", "before") is None

    @pytest.mark.parametrize("scheme,fill", [("stcolor", "#ffffff")])
    def test_scheme_fill(self, mode, scheme, fill):
        _f, lg, _ = G._fig_legend(mode, G.THREE, "box", scheme=scheme)
        assert _em(_sheet(lg), "background-color", "before") == fill

    def test_no_frame_without_box(self, mode):
        """bcolor() without box draws nothing (bcolor_only)."""
        _f, lg, _ = G._fig_legend(mode, G.THREE, "bcolor(gs14)")
        assert "::before" not in _sheet(lg)

    def test_margin_reserved(self, mode):
        """margin(large) pads every key text 8 units a side, in em of
        the key text, so the keys and the box grow as twoway's do
        (box_margin_large); without box too (margin_large)."""
        T = dr.OptionTranslator
        for opt in ("margin(large)", "box margin(large)"):
            _f, lg, _ = G._fig_legend(mode, G.THREE, opt)
            em = 8 * T.PT_PER_RS / _font_pt(lg)
            pad = _em(_sheet(lg), "padding").split()
            assert [float(p[:-2]) for p in pad] == pytest.approx([em] * 4,
                                                                 rel=0.01)

    @pytest.mark.parametrize("opt,shift", [
        ("alignment(top)", -0.151), ("alignment(bottom)", -0.151),
        ("alignment(baseline)", 0.1497), ("alignment(middle)", None)])
    def test_alignment(self, mode, opt, shift):
        """alignment() moves the text by its measured share of the text
        size (align_top/_bottom up, align_baseline down, middle the
        default); with box the frame stays (box_align_top)."""
        _f, lg, _ = G._fig_legend(mode, G.THREE, opt)
        css = _sheet(lg)
        if shift is None:
            assert _em(css, "top") is None
        else:
            assert float(_em(css, "top")[:-2]) == pytest.approx(shift,
                                                                abs=0.002)
        _f, lg, _ = G._fig_legend(mode, G.THREE, "box " + opt)
        if shift is not None:
            css = _sheet(lg)
            assert "%.4gem" % (-shift) in _em(css, "top", "before")

    def test_linegap(self, mode):
        """linegap(5) spreads a key text's lines 5 units further than
        the text size (linegap5)."""
        T = dr.OptionTranslator
        _f, lg, _ = G._fig_legend(mode, G.THREE, "linegap(5)")
        want = 1.0 + 5 * T.PT_PER_RS / _font_pt(lg)
        assert float(_em(_sheet(lg), "line-height")) == pytest.approx(
            want, rel=0.001)

    def test_by_cell(self, mode):
        """by()'s legend cell carries the key-text sheet."""
        figs = G.tp._figures_in(mode, G.tp._spec(
            G.THREE, {"scheme": "s2color"},
            {"by": "foreign", "legend": "box"}))[0]
        from bokeh.models import Legend
        cells = [m for f in figs for m in f.select({"type": Legend})
                 if str(m.name or "").endswith("_key")]
        assert cells and all("::before" in _sheet(c) for c in cells)


# ---------------------------------------------------------------------------
# LT-6: the legend's layout and region style sub-options
# ---------------------------------------------------------------------------

def _region_box(key):
    """The legend's fill rect in row *key* (the smallest filled rect
    holding every key text), as (x0, y0, x1, y1)."""
    rs = [r for r in _legend_region(key) if "fill:none" not in r[4]]
    return min(rs, key=lambda r: (r[2] - r[0]) * (r[3] - r[1]))[:4] \
        if rs else None


def _layout_decl(lg, prop):
    css = _sheet(lg, "dash_legend_layout")
    i = css.find(":host{")
    if i < 0:
        return None
    for d in css[i + 6:css.index("}", i)].split(";"):
        if d.startswith(prop + ":"):
            return d.split(":", 1)[1]
    return None


class TestLayoutFixture:

    def test_measured(self):
        """style(column) is cols(1); style(bogus) is noted and drawn as
        the default; width(60) and height(30) make the box 60 and 30
        units plus its margins (1.2 units a side), the keys centred in
        it; xoffset(5) moves the box 5 units right, yoffset(5) 5 up, the
        plot region unmoved; showindex writes "n:" before each key text;
        region(style(none)) draws no box; region(lstyle(p1)) lines it
        #1A476F at medium; lalign(outside) draws the line outside the
        fill, inside is the default."""
        assert TRUTH["style_column"]["rects"] == TRUTH["cols1"]["rects"]
        assert TRUTH["style_bogus"]["rects"] == TRUTH["ctl"]["rects"]
        assert any("legendstyle" in ln for ln in TRUTH["style_bogus"]["lines"])
        b0 = _region_box("ctl")
        bw = _region_box("width60")
        bh = _region_box("height30")
        assert abs((bw[2] - bw[0]) - (60 + 2.4) * 28.8) < 0.5
        assert abs((bh[3] - bh[1]) - (30 + 2.4) * 28.8) < 0.5
        assert abs((bw[0] + bw[2]) / 2 - (b0[0] + b0[2]) / 2) < 0.5
        bx, by = _region_box("xoff5"), _region_box("yoff5")
        assert abs((bx[0] - b0[0]) - 5 * 28.8) < 0.1
        assert abs((b0[1] - by[1]) - 5 * 28.8) < 0.2
        for k in ("xoff5", "yoff5"):
            assert TRUTH[k]["plot"] == TRUTH["ctl"]["plot"]
        texts = [t["text"] for t in TRUTH["showindex"]["texts"]
                 if ":" in t["text"]]
        assert texts == ["1:Mileage (mpg)", "2:Price",
                         "3:Turn circle (ft.)"]
        # Only the graph region's outline holds the keys.
        assert [r for r in _legend_region("reg_style_none")
                if r[2] - r[0] < 3900] == []
        line = [r for r in _legend_region("reg_lstyle_p1")
                if "fill:none" in r[4] and r[2] - r[0] < 3900][0]
        assert _style(line, "stroke") == "#1a476f"
        assert _style(line, "stroke-width") == "8.64"
        out = [r for r in _rects("reg_thick_out") if "fill:none" in r[4]
               and "23.04" in r[4]][0]
        inn = [r for r in _rects("reg_thick_in") if "fill:none" in r[4]
               and "23.04" in r[4]][0]
        assert abs((inn[0] - out[0]) - 23.04) < 0.05
        assert _rects("reg_thick_in") == _rects("reg_thick")


@pytest.mark.parametrize("mode", MODES)
class TestLayout:

    def test_style(self, mode):
        """style(column) lays the keys in one column; style(default) is
        the default; style(bogus) is noted with twoway's words."""
        _f, lg, _ = G._fig_legend(mode, G.THREE, "style(column)")
        assert lg.ncols == 1 and lg.nrows == 3
        _f, lg, caught = G._fig_legend(mode, G.THREE, "style(default)")
        assert lg.ncols == 2 and not caught
        _f, lg, caught = G._fig_legend(mode, G.THREE, "style(bogus)")
        assert lg.ncols == 2
        assert any("named style bogus not found in class legendstyle"
                   in w for w in caught), caught

    def test_width_height(self, mode):
        """width(60) and height(30): the box's least size is the size
        plus its margins, the keys centred, in px at the 4-inch reference
        times the width scale's factor."""
        T = dr.OptionTranslator
        _f, lg, caught = G._fig_legend(mode, G.THREE, "width(60) height(30)")
        assert not [w for w in caught if "legend(" in w], caught
        pad = lg.padding
        w = 60 * T.PT_PER_RS * T.PX_PER_PT + 2 * pad
        h = 30 * T.PT_PER_RS * T.PX_PER_PT + 2 * pad
        assert _layout_decl(lg, "min-width") == \
            "calc(%.4gpx * var(--dash-k, 1))" % w
        assert _layout_decl(lg, "min-height") == \
            "calc(%.4gpx * var(--dash-k, 1))" % h
        assert _layout_decl(lg, "justify-content") == "center"
        assert _layout_decl(lg, "box-sizing") == "border-box"

    def test_offset(self, mode):
        """xoffset(5) moves the box 5 units right, yoffset(5) 5 up."""
        T = dr.OptionTranslator
        u = 5 * T.PT_PER_RS * T.PX_PER_PT
        _f, lg, _ = G._fig_legend(mode, G.THREE, "xoffset(5) yoffset(5)")
        assert _layout_decl(lg, "translate") == (
            "calc(%.4gpx * var(--dash-k, 1)) calc(%.4gpx * var(--dash-k, 1))"
            % (u, -u))

    def test_showindex(self, mode):
        _f, lg, _ = G._fig_legend(mode, G.THREE, "showindex")
        assert [G._text(i) for i in lg.items][:2] == ["1:mpg", "2:price"]

    @pytest.mark.parametrize("case", ["none", "lstyle", "outside", "inside"])
    def test_region_styles(self, mode, case):
        T = dr.OptionTranslator
        _f, ref, _ = G._fig_legend(mode, G.THREE, "region(lwidth(thick))")
        opt = {"none": "region(style(none))",
               "lstyle": "region(lstyle(p1))",
               "outside": "region(lwidth(thick) lalign(outside))",
               "inside": "region(lwidth(thick) lalign(inside))"}[case]
        _f, lg, caught = G._fig_legend(mode, G.THREE, opt)
        assert not [w for w in caught if "legend(" in w], caught
        if case == "none":
            assert lg.border_line_color is None
            assert lg.background_fill_color is None
        elif case == "lstyle":
            assert lg.border_line_color == "#1a476f"
            assert lg.border_line_width == pytest.approx(
                T.translate_lwidth("medium", None, 4.0))
        elif case == "outside":
            assert lg.padding == ref.padding + round(lg.border_line_width)
        else:
            assert lg.padding == ref.padding

    def test_by_cell(self, mode):
        """by()'s legend cell carries the layout sheet."""
        figs = G.tp._figures_in(mode, G.tp._spec(
            G.THREE, {"scheme": "s2color"},
            {"by": "foreign", "legend": "xoffset(5)"}))[0]
        from bokeh.models import Legend
        cells = [m for f in figs for m in f.select({"type": Legend})
                 if str(m.name or "").endswith("_key")]
        assert cells and all("translate" in _sheet(c, "dash_legend_layout")
                             for c in cells)
