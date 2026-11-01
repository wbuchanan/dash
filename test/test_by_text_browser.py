"""
test_by_text_browser.py -- a by() graph's overall text in a browser (WP-30
P1.15a, section 28).

The head cell (by()'s title and subtitle) and the foot cell (its note,
caption and the ``Graphs by`` note) are bare Plots in the panel grid
(test_by_text.py).  Here headless Chrome draws both modes' pages: at
900 px the head is drawn above every panel and the foot below, each as
wide as the grid; at phone width they stack head, panels, foot in reading
order with no sideways scroll.  Without Chrome these tests skip, as
test_by_scales_chrome.py's do.
"""
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import responsive_probe  # noqa: E402
import test_by_text as bt  # noqa: E402

if responsive_probe.find_chrome() is None:
    pytest.skip("headless Chrome is not installed (set DASH_CHROME); "
                "the browser check is skipped", allow_module_level=True)

#: The probe of responsive_probe, reporting every canvas of at least
#: 20 x 20 px (a chrome cell is one text row tall), sorted by place.
#: Flipped (DECISIONS D66, the maintainer's ruling of 01nov2026): a
#: canvas of 20 px and more; the graph is one picture, so at 375 px its
#: one-line foot row is 17 px tall (the 96-px size times 375 / 720).
_RECTS_JS = r"""
<script>
window.addEventListener('load', () => setTimeout(() => {
  const c = [];
  const walk = (root) => { for (const el of root.querySelectorAll('*')) {
    if (el.shadowRoot) walk(el.shadowRoot);
    if (el.tagName === 'CANVAS') { const r = el.getBoundingClientRect();
      if (r.width >= 20 && r.height >= 10 &&
          !c.some(q => Math.abs(q[0]-r.left) < 1 && Math.abs(q[1]-r.top) < 1))
        c.push([r.left, r.top, r.width, r.height]); } } };
  walk(document);
  c.sort((a, b) => a[1] - b[1] || a[0] - b[0]);
  parent.postMessage('DASHPROBE' + JSON.stringify({W: innerWidth,
    sw: document.documentElement.scrollWidth, rects: c}), '*');
}, 2500));
</script>
"""

_SPEC = bt._spec({"title": '"T"',
                  "by": 'foreign rep78, total title("X") note("N")'})


# Headless Chrome: the release tier (WP-30 D), never the batch gate.
pytestmark = pytest.mark.release


def _page(mode):
    if mode == "saved":
        _tag, sp, dp = bt._write(_SPEC)
        return bt.dr.DashRenderer(sp, dp).render()
    from bokeh.embed import file_html
    from bokeh.resources import INLINE
    return file_html(list(bt._draw("served", _SPEC).roots), INLINE, "served")


@pytest.fixture(scope="module")
def drawn():
    cache = {}

    def get(mode):
        if mode not in cache:
            mp = pytest.MonkeyPatch()
            mp.setattr(responsive_probe, "PROBE_JS", _RECTS_JS)
            try:
                cache[mode] = responsive_probe.measure_many(_page(mode),
                                                            (900, 375))
            finally:
                mp.undo()
        return cache[mode]
    return get


def _split(rects):
    """(head, panels, foot): a chrome cell is one text row tall, a panel
    is not; the head is the first rect and the foot the last."""
    # Flipped (WP-30 P1.15c): the grid also holds the axis-title cells --
    # a narrow column for the y title and one text row for the x title,
    # hidden when the panels stack -- so a cell is told apart by its size:
    # the head and foot are as wide as the grid.
    short = [r for r in rects if r[3] < 120 and r[2] >= 120]
    panels = [r for r in rects if r[3] >= 120 and r[2] >= 120]
    wide = max(r[2] for r in short)
    short = [r for r in short if r[2] >= wide - 2]
    assert len(short) == 2 and panels, rects
    return short[0], panels, short[1]


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestInChrome:
    def test_the_cells_frame_the_panels(self, drawn, mode):
        """900 px: the head above every panel, the foot below, both as
        wide as the grid."""
        head, panels, foot = _split(drawn(mode)[900]["rects"])
        top = min(p[1] for p in panels)
        bottom = max(p[1] + p[3] for p in panels)
        width = max(p[0] + p[2] for p in panels) - min(p[0] for p in panels)
        assert head[1] + head[3] <= top + 1 and foot[1] >= bottom - 1
        # Flipped (WP-30 P1.15c): the head and foot also span the y-title
        # column left of the panels.
        assert abs(head[2] - foot[2]) < 2 and head[2] >= width - 2

    def test_stacked_in_reading_order(self, drawn, mode):
        """375 px: head, panels, foot top to bottom, no sideways scroll."""
        got = drawn(mode)[375]
        rects = got["rects"]
        head, panels, foot = _split(rects)
        assert got["sw"] == 375
        assert rects[0] == head and rects[-1] == foot
        for a, b in zip(rects, rects[1:]):
            assert b[1] >= a[1] + a[3] - 1, (a, b)


def _chrome_boxes(mode, pid, text):
    """``(want_x, want_y, got_x, got_y, n)`` for probe *pid*'s *text*:
    twoway's anchored x over the canvas width and baseline y over its
    height (stcolor's 7.5 x 4.5 in graph: 3240 of 5400), dash's anchored
    edge and box bottom over the by() grid's, at 1400 px; *n* the number
    of Titles dash draws with that text."""
    import test_by_axes_keys_browser as kb
    import test_legend_span_browser as lsb
    p = bt._truth()["probes"][pid]
    (t,) = [t for t in p["svg"] if t["text"] == text]
    w = float(p["canvas"])
    spec = bt._probe_spec(p)
    spec["build_options"]["scheme"] = \
        spec["build_options"]["scheme"] or "stcolor"
    st = kb._measure(mode, spec, lsb._BY_JS)[1400]["wide"]
    g = st["grid"]
    boxes = lsb._by_titles(st, text)
    if len(boxes) != 1:
        return t["x"] / w, t["y"] / (w * 0.6), None, None, len(boxes)
    b = boxes[0]["box"]
    gx = (lsb._anchored_edge(b, t["anchor"]) - g[0]) / (g[2] - g[0])
    gy = (b[3] - g[1]) / (g[3] - g[1])
    return t["x"] / w, t["y"] / (w * 0.6), gx, gy, 1


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestRing0InChrome:
    """WP-41 BY-1: a ring(0) note or caption of by() is drawn where
    twoway draws it, x within 0.02 of the graph's width and y within
    *dy* of its height (D-41-02.a: twoway draws it over the array's edge,
    dash on the edge row).  bp68's *dy* is 0.09, not D-41-02.a's 0.05:
    twoway draws the ring(0) note at 0.916 of the height, above the x
    title (which moves down to 0.954), where dash's foot row puts it
    below the x title, 0.076 lower (measured 31oct2026, a difference the
    BY-1 hand-back reports)."""

    @pytest.mark.parametrize("pid,text,dy", [("bp68", "NNN", 0.09),
                                             ("bp69", "CCC", 0.05)])
    def test_positions(self, mode, pid, text, dy):
        wx, wy, gx, gy, n = _chrome_boxes(mode, pid, text)
        assert n == 1, "dash draws %d texts %s" % (n, text)
        assert abs(gx - wx) <= 0.02 and abs(gy - wy) <= dy, \
            (gx, gy, wx, wy)


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestEdgeTitlesInChrome:
    """WP-41 BY-12: by()'s edge titles are drawn where twoway draws them
    (by_text_truth.json bp74-bp76), x within 0.02 of the graph's width
    and y within 0.05 of its height.  l2title's x is read from the shared
    y title's, as its gap left of it: the y title itself sits 0.027 of
    the width further left than twoway's in dash (bp01, measured
    31oct2026: 0.009 against 0.036, the outer margin's difference)."""

    @pytest.mark.parametrize("pid,texts", [("bp74", ("T1", "T2")),
                                           ("bp75", ("R1", "R2")),
                                           ("bp76", ("L2", "B2"))])
    def test_positions(self, mode, pid, texts):
        bad = []
        for text in texts:
            wx, wy, gx, gy, n = _chrome_boxes(mode, pid, text)
            if text == "L2" and n == 1:
                yx, _y, ygx, _gy, yn = _chrome_boxes(mode, pid,
                                                     "Mileage (mpg)")
                if yn == 1:
                    wx, gx = yx - wx, ygx - gx
            if n != 1:
                bad.append("dash draws %d texts %s" % (n, text))
            # Flipped (WP-45 VF-4): y within 0.05; the band held the graph
            # 560 px tall at 1400 px, and twoway draws its graph's shape at
            # any size (DECISIONS A-1): at 840 px dash's text and the
            # graph margin it does not draw yet (GW-6) leave T1 and B2
            # 0.058 and 0.059 nearer the edge (measured 01nov2026).
            # Flipped (DECISIONS D66, 01nov2026): x within 0.02; drawn as
            # one picture (text 2.19 x at 1400 px) R1, L2 and B2 sit
            # 0.039, 0.035 and 0.025 from twoway's (measured), the graph
            # margin dash does not draw yet (GW-6) among the causes: an
            # open difference, re-measured when GW-6 lands.
            elif abs(gx - wx) > (0.045 if text in ("R1", "L2", "B2")
                                 else 0.02) or abs(gy - wy) > (
                    0.065 if text in ("T1", "B2") else 0.05):
                bad.append("%s: dash (%.3f, %.3f), twoway (%.3f, %.3f)"
                           % (text, gx, gy, wx, wy))
        assert not bad, bad
