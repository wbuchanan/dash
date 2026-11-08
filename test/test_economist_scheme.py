"""
test_economist_scheme.py -- economist's shipped look as twoway draws it
(WP-45 section 45-01).

PIC-4: twoway draws economist's note() in its reverse_big box (white text
on #7b92a8) at the top right of the title's band
(test/fixtures/economist_truth.json ``note``: the box's top at the graph
margin, its right edge at the plot region's, the band no taller than the
title's alone).  dash's Label sat in ``fig.center`` on Nodes of the
Title, and BokehJS clips every annotation of the centre to the frame
(``AnnotationView.needs_clip`` is ``layout == null``): nothing was
painted.  The Label is now a row of the ``above`` panel, pinned to the
canvas's top and the frame's right edge.

The pixel test runs the saved and served pages in headless Chrome
(``responsive_probe``), the release tier, as test_title_boxes.py's do.
"""
import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402

MODES = ("saved", "served")

with open(os.path.join(_HERE, "fixtures", "economist_truth.json"),
          encoding="utf-8") as _fh:
    _TRUTH = json.load(_fh)

_HELP = os.path.join(_HERE, "..", "dash.sthlp")

_GO = {"title": '"T"', "note": '"The note"'}


def _spec(go=None):
    return tp._spec([tp._sc()], {"scheme": "economist"}, dict(go or _GO))


def _fig(mode, go=None):
    figs, _caught = tp._figures_in(mode, _spec(go))
    assert len(figs) == 1, len(figs)
    return figs[0]


def _note(fig):
    """The figure's note Labels, wherever they are."""
    from bokeh.models import Label
    out = []
    for side in ("center", "above", "below", "left", "right"):
        out += [(side, m) for m in getattr(fig, side)
                if isinstance(m, Label) and "note" in (m.tags or [])]
    return out


def _between(text, start, end):
    i = text.index(start)
    j = text.index(end, i + len(start))
    return text[i:j]


class TestTheNoteIsMeasured:

    def test_twoways_box(self):
        """The fixture: the box filled #7b92a8 with white text, its top at
        the graph margin (3.5% of 1584), its right edge at the plot
        region's, and the title's band no taller with the note than
        without it."""
        n, pr, t = (_TRUTH["note"][k] for k in
                    ("N_note_pr", "N_note_pr", "N_title_pr"))
        x, y, w, _h = n["note_box"]
        assert n["note_box_fill"] == "#7b92a8"
        assert n["note_text"]["fill"] == "#ffffff"
        assert y == pytest.approx(3.5 / 100 * 1584, abs=0.1)
        px, py, pw, _ph = pr["plotregion"]
        assert x + w == pytest.approx(px + pw, abs=0.05)
        assert py == pytest.approx(t["plotregion"][1], abs=0.05)


class TestTheNoteIsPainted:

    @pytest.mark.parametrize("mode", MODES)
    def test_model(self, mode):
        """A Label of the above panel (not the centre, which BokehJS clips
        to the frame), anchored top right on the frame's right edge and
        the canvas's top less the graph margin (3.5 relative units, 13 px
        at dash's 4-inch reference), in twoway's text and fill, its
        offsets tagged as a margin gap."""
        from bokeh.models import Node
        f = _fig(mode)
        [(side, lab)] = _note(f)
        assert side == "above"
        assert lab.text == _TRUTH["note"]["N_note"]["note_text"]["text"]
        assert isinstance(lab.x, Node) and isinstance(lab.y, Node)
        assert (lab.x.target, lab.x.symbol) == ("frame", "right")
        assert (lab.y.target, lab.y.symbol) == ("canvas", "top")
        assert lab.anchor == "top_right"
        assert lab.background_fill_color == \
            _TRUTH["note"]["N_note"]["note_box_fill"]
        assert lab.text_color == _TRUTH["note"]["N_note"]["note_text"]["fill"]
        gm = dr.SchemeParser("economist").graph_margin_sides[3]
        # The 4-inch px of the model: 3.84 a relative unit.
        assert lab.y_offset == -round(gm * 3.84)
        assert lab.x_offset == 0
        assert "dash_margin_offset" in lab.tags

    @pytest.mark.release
    @pytest.mark.parametrize("mode", MODES)
    def test_pixels(self, mode):
        """In Chrome at 384, 600 and 1000 px: #7b92a8 pixels fill a box
        above the frame whose right edge is the frame's and whose top is
        the Label's offset, with the note's white text inside it."""
        got = _chrome(mode)
        for w in _WIDTHS:
            p = got[w]
            box, white, fr = p["box"], p["white"], p["frame"]
            assert box is not None, (w, p)
            x0, y0, bw, bh, n = box
            assert y0 + bh <= fr[1] + 1, (w, p)
            assert x0 + bw == pytest.approx(fr[0] + fr[2], abs=2), (w, p)
            assert y0 == pytest.approx(p["offset"], abs=2), (w, p)
            assert n >= 0.6 * bw * bh, (w, p)
            assert white is not None, (w, p)
            assert x0 <= white[0] and white[0] + white[2] <= x0 + bw, (w, p)
            assert y0 <= white[1] and white[1] + white[3] <= y0 + bh, (w, p)
            assert p["errors"] == [], (w, p)


class TestTheHelpSaysSo:

    def test_hr15(self):
        """dash.sthlp's economist sentence (Appendix B HR-15), true now
        that the box is painted."""
        with open(_HELP, encoding="utf-8") as fh:
            text = fh.read()
        para = " ".join(_between(text, "under {cmd:economist} the title, "
                                       "subtitle and caption",
                                 "Clock positions 2 to 4").split())
        assert "the note sits in its box in the title's band, at the top " \
            "right" in para


_WIDTHS = (384, 600, 1000)

#: In Chrome: each figure's picture as its save tool exports it, the
#: bounding box and count of its #7b92a8 pixels above the frame, the
#: bounding box of the white pixels above the frame, the frame, and the
#: note Label's y offset in canvas px.
_CHROME_JS = r"""
<script>
const E = [];
addEventListener('error', e => E.push(String(e.message)));
window.addEventListener('load', () => setTimeout(() => {
  const out = {plots: []};
  const seen = new Set();
  const visit = (v) => {
    if (v == null || seen.has(v)) return;
    seen.add(v);
    if (v.frame && v.export) {
      const c = v.export("png", false).canvas;
      const W = c.width, H = c.height;
      const r = W / v.canvas.bbox.width;
      const d = c.getContext('2d').getImageData(0, 0, W, H).data;
      const top = Math.floor(v.frame.bbox.top * r);
      const box = (f) => { let x0 = 1e9, y0 = 1e9, x1 = -1, y1 = -1, n = 0;
        for (let y = 0; y < top; y++) for (let x = 0; x < W; x++) {
          const i = (y * W + x) * 4;
          if (f(d[i], d[i + 1], d[i + 2], d[i + 3])) { n++;
            if (x < x0) x0 = x; if (y < y0) y0 = y;
            if (x > x1) x1 = x; if (y > y1) y1 = y; } }
        return x1 < 0 ? null
          : [x0 / r, y0 / r, (x1 - x0 + 1) / r, (y1 - y0 + 1) / r,
             n / (r * r)]; };
      const near = (a, b) => Math.abs(a - b) <= 3;
      const b = v.frame.bbox;
      const lab = [...v.model.above].find(
        m => (m.tags || []).includes("note"));
      out.plots.push({
        box: box((R, G, B, A) => near(R, 0x7b) && near(G, 0x92)
                 && near(B, 0xa8) && A > 200),
        white: box((R, G, B, A) => R > 245 && G > 245 && B > 245 && A > 200),
        frame: [b.left, b.top, b.width, b.height],
        offset: lab ? -lab.y_offset : null});
    }
    for (const c of (v.child_views || [])) visit(c);
  };
  for (const v of Object.values(Bokeh.index)) visit(v);
  parent.postMessage('DASHPROBE' + JSON.stringify(
    Object.assign(out, {E, W: innerWidth})), '*');
}, 3000));
</script>
"""


def _chrome(mode):
    """{width: the one figure's probe result, with the page's errors}."""
    import responsive_probe
    if responsive_probe.find_chrome() is None:
        pytest.skip("headless Chrome is not installed (set DASH_CHROME)")
    spec = _spec()
    if mode == "saved":
        page = tp._standalone_page(spec)[2]
    else:
        from bokeh.embed import file_html
        from bokeh.resources import INLINE
        page = file_html(tp._served(spec)[0], INLINE, "served")
    mp = pytest.MonkeyPatch()
    mp.setattr(responsive_probe, "PROBE_JS", _CHROME_JS)
    try:
        got = responsive_probe.measure_many(page, _WIDTHS)
    finally:
        mp.undo()
    out = {}
    for w in _WIDTHS:
        assert len(got[w]["plots"]) == 1, got[w]
        out[w] = dict(got[w]["plots"][0], errors=got[w]["E"])
    return out


# ---------------------------------------------------------------------------
# PIC-7 (PIC-8): the range, spike, drop-line and paired-coordinate lines
# take linestyle p#other; rarea's outline takes p#area
# ---------------------------------------------------------------------------

#: The types whose shaft twoway strokes at linestyle p#other (measured:
#: economist_truth.json widths -- 0.8 under economist's pother thick, 2.6
#: under wt45's pother vvthick, 0.3 under s2color, for every one).
_OTHER = ("rspike", "rcap", "rcapsym", "rline", "rconnected", "pcspike",
          "pccapsym", "pcarrow", "pcbarrow", "spike", "dropline")

_TW = _TRUTH["widths"]


def _tw_parts(scheme, ptype):
    """(shaft, heads, markers): sets of twoway's drawn widths in relative
    units -- the shaft the line, path or area outline drawn fewest times
    (a clipped, inside-aligned outline draws half its SVG width), the
    heads the other lines, the markers the circles."""
    st = _TW[scheme][ptype]["strokes"]
    n_min = min(s[2] for s in st if s[0] in ("line", "path", "use"))
    shaft, heads, marks = set(), set(), set()
    for tag, rs, n, clipped in st:
        rs = round(rs / 2.0 if clipped else rs, 3)
        if tag == "circle":
            marks.add(rs)
        elif n == n_min:
            shaft.add(rs)
        else:
            heads.add(rs)
    return shaft, heads, marks


def _dash_parts(fig):
    """(shaft, heads, markers): sets of dash's drawn widths in relative
    units (px / 3.84) of the layer's glyphs."""
    import test_scheme_linewidth as tsl
    shaft, heads, marks = set(), set(), set()
    for r in tsl.drawn_renderers(fig):
        g = getattr(r, "glyph", None)
        w = getattr(g, "line_width", None)
        if isinstance(w, bool) or not isinstance(w, (int, float)):
            continue
        rs = round(float(w) / 3.84, 3)
        if "dash-arrowhead" in (r.tags or []):
            heads.add(rs)
        elif type(g).__name__ in ("Line", "Segment", "MultiLine"):
            shaft.add(rs)
        elif type(g).__name__ == "Scatter":
            marks.add(rs)
    return shaft, heads, marks


def _one_layer(ptype):
    import test_scheme_linewidth as tsl
    return tsl._layers(ptype)[:1]


@pytest.fixture
def wd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "wt45.scheme").write_text(_TRUTH["schemes"]["wt45"],
                                          encoding="utf-8")
    return tmp_path


class TestEconomistWidths:

    def test_twoway_draws_p_other(self):
        """The fixture: every listed type's shaft at pother, under
        economist (thick, 0.8), wt45 (vvthick, 2.6) and s2color (p, 0.3);
        rarea's outline at parea (0.2, wt45's vthin 0.15, s2color's p)."""
        want = {"economist": 0.8, "wt45": 2.6, "s2color": 0.3}
        for s, w in want.items():
            for t in _OTHER:
                assert _tw_parts(s, t)[0] == {w}, (s, t)
        assert {s: _tw_parts(s, "rarea")[0] for s in want} == {
            "economist": {0.2}, "wt45": {0.15}, "s2color": {0.3}}

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("ptype", _OTHER + ("rarea",))
    @pytest.mark.parametrize("scheme", ("economist", "wt45", "s2color"))
    def test_type(self, wd, mode, ptype, scheme):
        """dash's shaft (rarea's bound lines) at twoway's drawn width,
        within 0.05 relative units, saved and served."""
        import test_scheme_linewidth as tsl
        fig = tsl._figure(mode, wd, _one_layer(ptype), scheme)
        [want] = _tw_parts(scheme, ptype)[0]
        got = _dash_parts(fig)[0]
        assert got and all(abs(g - want) <= 0.05 for g in got), (got, want)

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("ptype", ("rcapsym", "rconnected", "pccapsym",
                                       "pcarrow", "pcbarrow", "dropline"))
    def test_heads_and_markers(self, wd, mode, ptype):
        """The heads and marker outlines keep p# (1.2 under economist),
        as twoway draws them."""
        import test_scheme_linewidth as tsl
        fig = tsl._figure(mode, wd, _one_layer(ptype), "economist")
        _s, heads, marks = _dash_parts(fig)
        _t, tw_heads, tw_marks = _tw_parts("economist", ptype)
        if tw_heads:
            assert heads and all(abs(h - 1.2) <= 0.05 for h in heads), heads
        if tw_marks:
            assert marks and all(abs(m - 1.2) <= 0.05 for m in marks), marks


class TestTheOtherChain:

    def test_chain(self, wd):
        """`linewidth p#other' -> `pother' -> `p#' -> `p': a user scheme
        with only `linewidth pother vthick' draws every plot's other line
        vthick, and `linewidth p2other' beats it on plot 2 alone;
        `linewidth p#area' -> `parea' -> `p#' for rarea's outline."""
        tr = dr.OptionTranslator.translate_lwidth
        (wd / "oc1.scheme").write_text(
            "#include s2color\nlinewidth pother vthick\n", encoding="utf-8")
        sp = dr.SchemeParser("oc1")
        assert [sp.plot_line_width(i, "other") for i in range(15)] == \
            [tr("vthick")] * 15
        assert sp.plot_line_width(0, "") == sp.default_line_width
        (wd / "oc2.scheme").write_text(
            "#include s2color\nlinewidth p1 thick\nlinewidth p2other thin\n"
            "linewidth p3area vvthick\nlinewidth parea vthin\n",
            encoding="utf-8")
        sp = dr.SchemeParser("oc2")
        assert sp.plot_line_width(0, "other") == tr("thick")
        assert sp.plot_line_width(1, "other") == tr("thin")
        assert sp.plot_line_width(2, "other") == sp.default_line_width
        assert sp.p_area_line_widths[0] == tr("vthin")
        assert sp.p_area_line_widths[2] == tr("vvthick")
        assert len(sp.p_area_line_widths) == 15
        econ = dr.SchemeParser("economist")
        assert econ.plot_line_width(0, "other") == tr("thick")
        assert econ.p_area_line_widths[0] == tr("thin")

    def test_help(self):
        """dash.sthlp's scheme-file width sentence names the other stub
        and the types that take it."""
        with open(_HELP, encoding="utf-8") as fh:
            text = fh.read()
        para = " ".join(_between(text, "whose stub is the plot type's",
                                 "a bar's outline stops at").split())
        assert "{cmd:other} for the range, spike, drop-line and " \
            "paired-coordinate lines" in para
        assert "{cmd:area} for an area outline and {cmd:rarea}'s" in para
