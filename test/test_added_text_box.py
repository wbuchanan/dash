"""
test_added_text_box.py -- text()'s alignment() typed through dash, its box
and line options, and a global's =exp in a graph's text (WP-43 section
43-06, LT-11 and LT-20).

The defects: dash.ado named ``text(..., alignment())`` in a note and never
handed it to the drawing (LT-11), though the renderer could draw it; and
text()'s width(), height(), linegap(), lstyle(), lpattern() and lalign()
(and their bl forms) were named and not drawn, and a global holding
```=1+1'`` was drawn as written where twoway draws 2 (LT-20).

twoway's rule: test/fixtures/added_text_box_truth.json, written by
scripts/extract_added_text_box_truth.do (stcolor, auto, ``twoway scatter
mpg weight, text(30 3000 "Peak" "two", <opts>)``).
"""
import json
import os
import re
import sys
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_added_text as tat  # noqa: E402

MODES = ("saved", "served")

with open(os.path.join(_HERE, "fixtures", "added_text_box_truth.json"),
          encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)
P = TRUTH["probes"]


def _read(name):
    with open(os.path.join(_ROOT, name), encoding="utf-8") as fh:
        return fh.read()


def _program(src, head, end):
    """The text of one ado program or Mata function: from *head* to the
    first *end* after it."""
    a = src.index(head)
    return src[a:src.index(end, a)]


def _block(text, opts, mode, caught=None):
    """The Labels one text(30 3000 "Peak" "two", <opts>) record draws."""
    spec = tat._spec([tat._at(30, 3000, ["Peak", "two"], opts)])
    return [lab for f in tat._figs(spec, mode, None, caught)
            for lab in tat._labels(f)]


def _size_px(lab):
    return tat._pt(lab.text_font_size) * dr.OptionTranslator.PX_PER_PT


class TestTheFixture:

    def test_meta(self):
        m = TRUTH["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted",
                  "source"):
            assert m[k], k
        assert m["source"] == "scripts/extract_added_text_box_truth.do"
        assert m["viewbox"] == [5400.0, 3240.0]

    def test_alignment_spellings(self):
        """twoway draws only the four full words; an abbreviation is
        named (class vertical_text) and drawn as bottom is drawn."""
        eq = TRUTH["_meta"]["al_equal"]
        assert {k: v for k, v in eq.items() if v} == {
            w: w for w in ("top", "middle", "bottom", "baseline")}
        for ab in ("t", "to", "mid", "bot", "base"):
            assert P["al_" + ab]["notes"] == [
                "(note:  named style %s not found in class vertical_text, "
                "default attributes used)" % ab]
            assert [t["y_px"] for t in P["al_" + ab]["texts"]] == \
                [t["y_px"] for t in P["al_bottom"]["texts"]]

    def test_alignment_shifts(self):
        """top and bottom raise the block 0.15 of its size above middle,
        baseline lowers it 0.15 (_DASH_ADDED_TEXT_VSHIFT)."""
        mid = P["al_middle"]["texts"][0]
        for w, k in dr._DASH_ADDED_TEXT_VSHIFT.items():
            got = P["al_" + w]["texts"][0]
            assert (mid["y_px"] - got["y_px"]) / mid["size"] == \
                pytest.approx(k, abs=0.003), w


class TestAlignmentRoute:

    def test_ado_and_mata(self):
        """alignment() leaves dash.ado's noted list and _dash_at_canon
        writes it for the drawing."""
        ado = _program(_read("dash.ado"), "program define _dash_at_opts",
                       "\nend")
        noted = ado[ado.index("foreach _n in"):]
        noted = noted[:noted.index("{")]
        assert "alignment" not in noted.split()
        canon = _program(_read("dash_parse.mata"),
                         "string scalar _dash_at_canon()", "\n}")
        assert '" alignment("' in canon

    @pytest.mark.parametrize("mode", MODES)
    def test_unknown_name_is_drawn_as_bottom(self, mode):
        """An alignment twoway does not know is named in its words and
        drawn where bottom is drawn (al_t, al_bot: the fixture)."""
        caught = []
        (lab,) = _block("", "alignment(bot)", mode, caught)
        want = dr._DASH_ADDED_TEXT_VSHIFT["bottom"] * _size_px(lab)
        assert lab.y_offset == pytest.approx(want, abs=0.01)
        hits = [w for w in caught if "named style bot not found in class "
                "vertical_text, default attributes used" in w]
        assert len(hits) == 1, caught


# ---------------------------------------------------------------------------
# LT-20: the box and line options
# ---------------------------------------------------------------------------

def _rs_of(probe, side):
    """A probe's box side in relative units (percent of min(W, H))."""
    b = P[probe]["boxes"][0]
    lo, hi = ("left", "right") if side == "w" else ("top", "bottom")
    return (b[hi] - b[lo]) / min(TRUTH["_meta"]["viewbox"]) * 100.0


def _hook(fig):
    cbs = [c for v in fig.js_property_callbacks.values() for c in v
           if getattr(c, "code", None) == dr._DASH_TEXT_BOX_JS]
    return list({id(c): c for c in cbs}.values())


def _figs_with(opts, mode, go=None, kind="text", caught=None):
    spec = tat._spec([tat._at(30, 3000, ["Peak", "two"], opts, kind=kind)],
                     go=go)
    return tat._figs(spec, mode, None, caught)


class TestFixedBox:

    @pytest.mark.parametrize("mode", MODES)
    def test_hook_items(self, mode):
        """width(20) height(8): one callback, the Label's box in em of its
        font -- 20 and 8 relative units, twoway's 648-unit box (x_w) being
        20 of them."""
        assert _rs_of("x_w", "w") == pytest.approx(20.0, abs=0.01)
        assert _rs_of("x_h", "h") == pytest.approx(20.0, abs=0.01)
        (fig,) = _figs_with("box width(20) height(8)", mode)
        (lab,) = tat._labels(fig)
        (cb,) = _hook(fig)
        (item,) = cb.args["items"]
        assert item[0] is lab
        o = item[1]
        # In em of the text: twoway's x_w box is 648 / 112.56 = 5.76 of its
        # text's size wide; whole px at build round the em by < 1 px.
        size = P["x_w"]["texts"][0]["size"]
        b = P["x_w"]["boxes"][0]
        tol = 1.0 / _size_px(lab)
        assert o["w"] == pytest.approx((b["right"] - b["left"]) / size,
                                       abs=tol)
        assert o["h"] == pytest.approx(
            8 * min(TRUTH["_meta"]["viewbox"]) / 100.0 / size, abs=tol)
        assert len(o["pad"]) == 4 and o["valign"] == "middle"
        assert o["edge"] == 0
        assert lab.y_offset == 0

    @pytest.mark.parametrize("mode", MODES)
    def test_scale(self, mode):
        """Under scale(1.5) the box keeps its em: it grows with the font,
        as twoway's does (x_w_scale is 1.5 times x_w)."""
        ratio = _rs_of("x_w_scale", "w") / _rs_of("x_w", "w")
        assert ratio == pytest.approx(1.5, abs=0.001)
        (f1,) = _figs_with("box width(20)", mode)
        (f2,) = _figs_with("box width(20)", mode, go={"scale": "1.5"})
        (l1,), (l2,) = tat._labels(f1), tat._labels(f2)
        w1 = _hook(f1)[0].args["items"][0][1]["w"] * _size_px(l1)
        w2 = _hook(f2)[0].args["items"][0][1]["w"] * _size_px(l2)
        assert w2 / w1 == pytest.approx(ratio, rel=0.02)

    @pytest.mark.parametrize("mode", MODES)
    def test_ttext(self, mode):
        """ttext() takes the same options."""
        (fig,) = _figs_with("box width(20)", mode, kind="ttext")
        (lab,) = tat._labels(fig)
        assert _hook(fig)[0].args["items"][0][0] is lab

    @pytest.mark.parametrize("mode", MODES)
    def test_height_keeps_the_box_in_place(self, mode):
        """With height(), alignment() moves the text inside the box and
        not the box (x_h_top, x_h_bot: the box of x_h_mid)."""
        for p in ("x_h_top", "x_h_bot", "x_h_base"):
            assert P[p]["boxes"] == P["x_h_mid"]["boxes"], p
        (fig,) = _figs_with("box height(40) alignment(top)", mode)
        (lab,) = tat._labels(fig)
        assert lab.y_offset == 0
        assert _hook(fig)[0].args["items"][0][1]["valign"] == "top"

    def test_justification_in_the_box(self):
        """width(40) justification(left/right) puts the lines at the box's
        left or right edge (x_wj_l, x_wj_r), which the hook's split of the
        spare width by text_align does."""
        b = P["x_wj_l"]["boxes"][0]
        assert P["x_wj_l"]["texts"][0]["x_px"] == pytest.approx(b["left"])
        assert P["x_wj_r"]["texts"][0]["x_px"] == pytest.approx(b["right"])
        js = dr._DASH_TEXT_BOX_JS
        assert "{left: 0, center: 0.5, right: 1}[lab.text_align]" in js


class TestLineOptions:

    @pytest.mark.parametrize("mode", MODES)
    def test_linegap(self, mode):
        """linegap(3): the line step is the size plus the gap (x_lg)."""
        t = P["x_lg"]["texts"]
        step = (t[1]["y_px"] - t[0]["y_px"]) / t[0]["size"]
        (lab,) = _block("", "linegap(3)", mode)
        assert lab.text_line_height == pytest.approx(step, rel=0.02)

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("case", ["p1", "red_then_p1", "p1_then_red",
                                      "bogus"])
    def test_lstyle(self, mode, case):
        """lstyle(p1)'s colour (x_lst); an explicit lcolor() wins in either
        order (x_lst_lc, x_lc_lst); an unknown style is named in twoway's
        words and the scheme's frame drawn (x_lst_bad)."""
        opts = {"p1": "box lstyle(p1)",
                "red_then_p1": "box lcolor(red) lstyle(p1)",
                "p1_then_red": "box lstyle(p1) lcolor(red)",
                "bogus": "box lstyle(bogus)"}[case]
        caught = []
        (lab,) = _block("", opts, mode, caught)
        sch = dr.SchemeParser.resolve_or_fallback("stcolor", "x")
        if case == "p1":
            assert P["x_lst"]["boxes"][0]["stroke"] == "#1a85ff"
            assert lab.border_line_color.lower() == "#1a85ff"
        elif case == "bogus":
            assert lab.border_line_color == sch.text_option_line_color
            assert len([w for w in caught if "named style bogus not found "
                        "in class linestyle" in w]) == 1, caught
        else:
            assert P["x_lst_lc"]["boxes"][0]["stroke"] == "#ff0000"
            assert P["x_lc_lst"]["boxes"][0]["stroke"] == "#ff0000"
            assert lab.border_line_color.lower() in ("#ff0000", "red")

    @pytest.mark.parametrize("mode", MODES)
    def test_lpattern(self, mode):
        """lpattern(dash) dashes the frame (x_lp, x_blp: twoway draws the
        frame as dashes)."""
        (lab,) = _block("", "box lpattern(dash)", mode)
        assert list(lab.border_line_dash) == list(
            dr.OptionTranslator.translate_lpattern("dash"))
        assert list(lab.border_line_dash)

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("side", ["outside", "inside"])
    def test_lalign(self, mode, side):
        """lalign(outside) moves every side of the box out by half the
        line, inside in by half (x_la_o: the stroke clipped outside the
        box's edge, x_la_i inside it)."""
        (base,) = _block("", "box lwidth(thick)", mode)
        (lab,) = _block("", "box lwidth(thick) lalign(%s)" % side, mode)
        half = 0.5 * float(lab.border_line_width)
        p0 = base.padding if isinstance(base.padding, dict) else \
            dict.fromkeys(("left", "right", "top", "bottom"), base.padding)
        for k in ("left", "right", "top", "bottom"):
            want = p0[k] + (half if side == "outside" else -half)
            assert lab.padding[k] == max(0, round(want)), k

    def test_the_bl_forms(self):
        """_dash_at_canon writes blpattern(), blstyle() and blalign() as
        the plain names when those are absent (x_blp = x_lp, x_blst =
        x_lst, x_bla_o = x_la_o in the fixture)."""
        for a, b in (("x_blp", "x_lp"), ("x_blst", "x_lst"),
                     ("x_bla_o", "x_la_o")):
            assert P[a]["boxes"] == P[b]["boxes"], a
        canon = _program(_read("dash_parse.mata"),
                         "string scalar _dash_at_canon()", "\n}")
        for nm in ("lpattern", "lstyle", "lalign"):
            assert 'st_local("b%s")' % nm in canon
            assert '" %s("' % nm in canon
        for nm in ("linegap", "width", "height"):
            assert '" %s("' % nm in canon


class TestSilent:

    @pytest.mark.parametrize("sub", ["bexpand", "bmargin"])
    def test_no_note(self, sub):
        """bexpand and bmargin() draw an added text's box as without them
        (x_bexpand, x_bmargin), so dash takes them in silence; the box and
        line options leave the noted list too."""
        assert TRUTH["_meta"]["same_as_box"]["x_" + sub] is True
        ado = _program(_read("dash.ado"), "program define _dash_at_opts",
                       "\nend")
        noted = ado[ado.index("foreach _n in"):]
        noted = noted[:noted.index("{")].split()
        assert sub not in noted
        for nm in ("width", "height", "linegap", "lstyle", "lpattern",
                   "lalign", "blstyle", "blpattern", "blalign", "nobexpand"):
            assert nm not in noted, nm
