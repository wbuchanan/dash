"""
test_legend_box_browser.py -- the legend's key-text frames, margins and
alignment drawn in a browser as twoway draws them (WP-43 LT-3, ruling
D69).

Bokeh 3.8 and 3.9 draw each key text as a ``.bk-label`` DOM element in
the Legend's shadow root; dash frames, pads and moves it with the
Legend's own stylesheet (``dash_legend_keytext``), so only the browser
lays it out.  Headless Chrome draws both modes' pages and reads each key
text's line box, its frame (the label's ``::before``) and its baseline
(from the font's metrics) against twoway's measured facts
(legend_box_truth.json): the frame is the text's extent, one text size
high with the baseline 0.85 of it from the top, the keys where they were
without box; margin(large) pads 8 units (2.304 text sizes) a side;
alignment(top) raises the text 0.151 of its size and leaves the frame.
Without Chrome these tests skip.
"""
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import responsive_probe  # noqa: E402
import test_by_axes_keys as bk  # noqa: E402
import test_by_axes_keys_browser as kb  # noqa: E402

if responsive_probe.find_chrome() is None:
    pytest.skip("headless Chrome is not installed (set DASH_CHROME); "
                "the browser check is skipped", allow_module_level=True)

# Headless Chrome: the release tier (WP-30 D), never the batch gate.
pytestmark = pytest.mark.release

#: Each series legend's items: the item, its label, the text's line box,
#: the frame (the label's ::before, null without one), the baseline and
#: the font size (page px), per legend in page order.
_KEYS_JS = r"""
<script>
addEventListener('load', () => setTimeout(() => {
  const out = [];
  const R = (r) => [r.left, r.top, r.right, r.bottom];
  const visit = (v) => {
    if (!v) return;
    if (v.frame && v.renderer_views) {
      for (const [m, rv] of v.renderer_views) {
        if (m.type !== 'Legend' || !m.visible || !rv.grid_el) continue;
        const items = [...rv.grid_el.children].map(e => {
          const lab = e.querySelector('.bk-label');
          const rg = document.createRange(); rg.selectNodeContents(lab);
          const cs = getComputedStyle(lab);
          const bs = getComputedStyle(lab, '::before');
          const lr = lab.getBoundingClientRect();
          const tr = rg.getBoundingClientRect();
          const cv = document.createElement('canvas').getContext('2d');
          cv.font = cs.font;
          const mt = cv.measureText(lab.textContent);
          const a = mt.fontBoundingBoxAscent, d = mt.fontBoundingBoxDescent;
          const lh = cs.lineHeight === 'normal' ? a + d
                                                : parseFloat(cs.lineHeight);
          return {item: R(e.getBoundingClientRect()), text: R(tr),
                  fs: parseFloat(cs.fontSize),
                  base: tr.top + (lh - a - d) / 2 + a,
                  frame: bs.content === 'none' ? null :
                    [lr.left, lr.top + parseFloat(bs.top), lr.right,
                     lr.bottom - parseFloat(bs.bottom)],
                  pad: parseFloat(cs.paddingLeft)};
        });
        const h = rv.el.getBoundingClientRect();
        const f = v.frame.bbox;
        const c = v.el.getBoundingClientRect();
        out.push({name: m.name || '', items, canvas: [c.left, c.top],
                  host: [h.left, h.top, h.right, h.bottom],
                  frame: [f.x0, f.y0, f.x1, f.y1]});
      }
    }
    for (const c of (v.child_views || [])) visit(c);
  };
  const roots = (typeof Bokeh.index[Symbol.iterator] === 'function')
    ? [...Bokeh.index] : Object.values(Bokeh.index);
  roots.forEach(visit);
  parent.postMessage('DASHPROBE' + JSON.stringify({W: innerWidth, out}),
                     '*');
}, 3000));
</script>
"""

_THREE = [bk._p("scatter"), bk._p("scatter", y="headroom"),
          bk._p("scatter", y="rep78")]


def _legends(mode, *legends, by=None):
    graphs = []
    for i, lg in enumerate(legends):
        go = {"legend": lg}
        if by:
            go["by"] = by
        graphs.append(bk._graph("g%d" % i, _THREE, go, title=False))
    spec = bk._spec(graphs, scheme="s2color")
    return kb._measure(mode, spec, _KEYS_JS)[1400]["out"]


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestKeyTextInChrome:

    def test_frames(self, mode):
        """box and holes(1) cols(1) box: each frame is its text's extent,
        one text size high, the baseline 0.85 of it below the top; the
        keys stay where the same legend without box puts them."""
        base, box, hbase, hbox = _legends(
            mode, "", "box", "holes(1) cols(1)", "holes(1) cols(1) box")
        def rel(rec, it):
            o = rec["items"][0]["item"]
            return [it["item"][i] - o[i % 2] for i in range(4)]
        for plain, framed in ((base, box), (hbase, hbox)):
            assert len(framed["items"]) == 3
            for p, it in zip(plain["items"], framed["items"]):
                f, t, fs = it["frame"], it["text"], it["fs"]
                assert f is not None
                assert abs(f[0] - t[0]) <= 1 and abs(f[2] - t[2]) <= 1
                assert abs((f[3] - f[1]) - fs) <= 1, it
                assert abs((it["base"] - f[1]) / fs - 0.85) < 0.05, it
                assert all(abs(a - b) <= 0.5 for a, b in zip(
                    rel(plain, p), rel(framed, it))), (p, it)

    def test_margin_and_alignment(self, mode):
        """box margin(large): 2.304 text sizes a side round the text;
        box alignment(top): the text 0.151 of its size up, the frame
        where box alone draws it."""
        box, marg, top = _legends(mode, "box", "box margin(large)",
                                  "box alignment(top)")
        for it in marg["items"]:
            f, t, fs = it["frame"], it["text"], it["fs"]
            assert abs((t[0] - f[0]) - 2.304 * fs) <= 1, it
            assert abs((f[3] - f[1]) - 5.608 * fs) <= 1, it
        for b, it in zip(box["items"], top["items"]):
            # The two legends sit side by side: compare each against its
            # own item.
            fb = [b["frame"][i] - b["item"][i % 2] for i in range(4)]
            ft = [it["frame"][i] - it["item"][i % 2] for i in range(4)]
            assert all(abs(x - y) <= 0.5 for x, y in zip(fb, ft)), (b, it)
            assert abs(((b["base"] - b["item"][1])
                        - (it["base"] - it["item"][1])) / it["fs"]
                       - 0.151) < 0.01

    def test_by_cell(self, mode):
        """by(foreign): the overall legend's cell frames its key texts."""
        (cell,) = [r for r in _legends(mode, "box", by="foreign")
                   if r["name"].endswith("_key")]
        assert len(cell["items"]) == 3
        for it in cell["items"]:
            f, t = it["frame"], it["text"]
            assert f is not None and abs(f[0] - t[0]) <= 1
            assert abs((f[3] - f[1]) - it["fs"]) <= 1


#: twoway's SVG units of a text size (legend_box_truth.json: 99.99).
_SIZE = 99.99


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestLayoutInChrome:

    def test_width_height(self, mode):
        """cols(1) width(60) and height(30): the box 60 (30) units plus
        its margins (legend_box_truth.json width60, height30: 62.4 and
        32.4 units), the keys centred in it, and the plot region gives
        way to the taller box."""
        base, wide, b2, tall = _legends(mode, "cols(1)", "cols(1) width(60)",
                                        "", "height(30)")
        u = 28.8 * wide["items"][0]["fs"] / _SIZE
        w = wide["host"][2] - wide["host"][0]
        assert abs(w - 62.4 * u) <= 2, (w, 62.4 * u)
        mid = (wide["host"][0] + wide["host"][2]) / 2
        its = wide["items"]
        span = (min(i["item"][0] for i in its), max(i["item"][2] for i in its))
        assert abs((span[0] + span[1]) / 2 - mid) <= 1
        h = tall["host"][3] - tall["host"][1]
        assert abs(h - 32.4 * u) <= 2, (h, 32.4 * u)
        assert (tall["frame"][3] - tall["frame"][1]) < \
            (b2["frame"][3] - b2["frame"][1]) - 50

    def test_offset(self, mode):
        """xoffset(5) yoffset(5): the box 5 units right and 5 up of where
        it is without them, the plot region unmoved (xoff5, yoff5)."""
        base, moved = _legends(mode, "", "xoffset(5) yoffset(5)")
        u = 28.8 * moved["items"][0]["fs"] / _SIZE
        bx, by = [base["host"][i] - base["canvas"][i] for i in (0, 1)]
        mx, my = [moved["host"][i] - moved["canvas"][i] for i in (0, 1)]
        assert abs((mx - bx) - 5 * u) <= 1, (mx - bx, 5 * u)
        assert abs((by - my) - 5 * u) <= 1, (by - my, 5 * u)
        assert [round(a - b, 1) for a, b in zip(base["frame"][1:],
                                                moved["frame"][1:])] == \
            [0.0, 0.0, 0.0]
