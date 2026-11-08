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
