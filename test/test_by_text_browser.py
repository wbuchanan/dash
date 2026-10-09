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
_RECTS_JS = r"""
<script>
window.addEventListener('load', () => setTimeout(() => {
  const c = [];
  const walk = (root) => { for (const el of root.querySelectorAll('*')) {
    if (el.shadowRoot) walk(el.shadowRoot);
    if (el.tagName === 'CANVAS') { const r = el.getBoundingClientRect();
      if (r.width >= 20 && r.height >= 20 &&
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
