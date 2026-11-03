"""
test_by_cells_browser.py -- a by() graph's side cells are painted at the
height of their track in headless Chrome (WP-34 VF-2, section 34-02).

The shared y title of a by() graph was never painted: the
``dash_by_ytitle`` cell held its Title and laid out 28x560, but its
canvas was 28x1 with nothing drawn, in both modes, because
``_dash_by_text_cell`` builds every cell with ``frame_height=1`` and
``_dash_by_cell`` never cleared it on a cell that fills its track.  The
browser tests before this one read bboxes and visibility only.

Here each cell's own canvas is read after a forced layout (virtual time
renders no frames, test_by_axes_keys_browser.py's docstring): its CSS
size and how many of its pixels are darker than its background.  The y
title is painted; a vertical legend is taller than 1 px; the default
colour key at 3 o'clock fills the panels' track as the y title does and
its ColorBar is drawn; at 6 o'clock the key keeps the fixed height its
branch sets (200 px at build, reset by the span hook to the upright
key's length).  Without Chrome these tests skip.
"""
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import responsive_probe  # noqa: E402
import test_by_axes_keys as bk  # noqa: E402
import test_by_axes_keys_browser as bkb  # noqa: E402

if responsive_probe.find_chrome() is None:
    pytest.skip("headless Chrome is not installed (set DASH_CHROME); "
                "the browser check is skipped", allow_module_level=True)

# Headless Chrome: the release tier (WP-30 D), never the batch gate.
pytestmark = pytest.mark.release

#: Every by() side cell's canvas: its CSS size, the pixels darker than its
#: top-left pixel (the cell's fill), and the height of any ColorBar it
#: draws.  The layout is forced first.
_CELLS_JS = r"""
<script>
addEventListener('load', () => setTimeout(() => {
  for (const v of Object.values(Bokeh.index)) {
    if (v.resize_layout) v.resize_layout();
    else if (v.after_resize) v.after_resize();
  }
  const out = [];
  const visit = (v) => {
    if (!v) return;
    const name = v.model && v.model.name;
    if (name && /^dash_by_(y|x)?(title|legend|clegend)$/.test(name)
        && v.canvas_view) {
      const layer = v.canvas_view.primary;
      const cv = layer.canvas, ctx = layer.ctx;
      const r = window.devicePixelRatio || 1;
      let dark = 0;
      if (cv.width > 0 && cv.height > 0) {
        const d = ctx.getImageData(0, 0, cv.width, cv.height).data;
        // WP-42 CV-3: a key cell's canvas is transparent; its corner is
        // read as white, so its swatches and labels count.
        const bg = d[3] === 0 ? 765 : d[0] + d[1] + d[2];
        for (let i = 0; i < d.length; i += 4) {
          if (d[i + 3] > 0 && d[i] + d[i + 1] + d[i + 2] < bg - 150) dark++;
        }
      }
      const bars = [], axes = [];
      for (const [m, rv] of (v.renderer_views || [])) {
        if (m.type === 'ColorBar' && rv.bbox) bars.push(rv.bbox.height);
        // WP-42 CV-3: a key cell's z axis.
        if ((m.type || '').endsWith('Axis') && rv.bbox) axes.push(rv.bbox.height);
      }
      out.push({name, w: cv.width / r, h: cv.height / r, dark, bars, axes,
                mh: v.model.height});
    }
    for (const c of (v.child_views || [])) visit(c);
  };
  for (const v of Object.values(Bokeh.index)) visit(v);
  parent.postMessage('DASHPROBE' + JSON.stringify({W: innerWidth, out}),
                     '*');
}, 3000));
</script>
"""

#: A colorvar() layer and a fit: with legend(on) the legend is a vertical
#: cell at 3 o'clock, and by(, clegend(on)) draws the colour key at its
#: default 3 o'clock, also vertical (a by() graph draws no key without
#: clegend(on), as twoway draws none: by_chrome_truth q06, q07).
_KEYED = [bk._p("scatter", colorvar="headroom"), bk._p("lfit")]


def _cells(mode, plots, go):
    spec = bk._spec([bk._graph("g1", plots, go, title=False)])
    got = bkb._measure(mode, spec, _CELLS_JS, (1200,))[1200]["out"]
    return {c["name"]: c for c in got}


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestTheTitleIsPainted:
    def test_ytitle(self, mode):
        """At 1200 px: the y title's canvas is at least 100 px tall and
        painted; a vertical legend's canvas is taller than 1 px; the
        default colour key's canvas is the y title's height (both fill
        the panels' track) with its z axis drawn (a ColorBar before WP-42
        CV-3); under clegend(on
        pos(6)) the key's canvas is the fixed height its branch and the
        span hook set."""
        go = {"by": "foreign", "ytitle": '"Price"'}
        c = _cells(mode, bk._ONE, go)
        yt = c["dash_by_ytitle"]
        assert yt["h"] >= 100 and yt["dark"] >= 50, yt

        c = _cells(mode, _KEYED, {"by": "foreign, clegend(on)",
                                  "ytitle": '"Price"', "legend": "on"})
        yt, leg, key = (c["dash_by_ytitle"], c["dash_by_legend"],
                        c["dash_by_clegend"])
        assert yt["h"] >= 100 and yt["dark"] >= 50, yt
        assert leg["h"] > 1, leg
        assert abs(key["h"] - yt["h"]) <= 2, (key, yt)
        # Flipped (WP-42 CV-3): the key drew a ColorBar; twoway draws
        # swatches beside a z axis, a key cell with its axis drawn.
        assert not key["bars"] and key["axes"] and max(key["axes"]) > 1, key
        assert key["dark"] >= 50, key

        c = _cells(mode, _KEYED[:1], {"by": "foreign, clegend(on pos(6))",
                                  "ytitle": '"Price"'})
        # The branch sets a fixed height (200 px at build), which the span
        # hook (_DASH_SPAN_JS, mode "row") resets to the upright key's
        # length plus its labels: the canvas is that height, neither the
        # 1-px frame nor Plot's default 600 px (measured 24oct2026: 293 px
        # at 1200 px).
        key = c["dash_by_clegend"]
        assert abs(key["h"] - key["mh"]) <= 1, key
        assert 160 <= key["h"] < 600 and key["dark"] >= 50, key
