"""
test_legend_title_browser.py -- legend(title()) and legend(subtitle())
drawn in a browser as twoway draws them (WP-43 LT-15, ruling D69).

The legend's title is a DOM text in the Legend's shadow root; dash draws
the title beside a subtitle, its place and its box with the legend's own
stylesheet (``.bk-title`` and ``.bk-title::first-line``).  Only the browser
lays that out, so headless Chrome draws both modes' pages and the title's
box, its first line's size and its frame are read against the legend's
keys.  Measured truth: test/fixtures/legend_title_truth.json (sub_under,
title_pos_5, title_box).  Without Chrome these tests skip.
"""
import json
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

with open(os.path.join(_HERE, "fixtures", "legend_title_truth.json"),
          encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)

#: Each legend's title box, keys box and title fonts (page px).
_TITLE_JS = r"""
<script>
addEventListener('load', () => setTimeout(() => {
  const out = [];
  const visit = (v) => {
    if (!v) return;
    if (v.frame && v.renderer_views) {
      for (const [m, rv] of v.renderer_views) {
        if (m.type !== 'Legend' || !m.visible || !m.title || !rv.title_el)
          continue;
        const t = rv.title_el.getBoundingClientRect();
        const g = rv.grid_el.getBoundingClientRect();
        const cs = getComputedStyle(rv.title_el);
        out.push({title: [t.left, t.top, t.right, t.bottom],
                  grid: [g.left, g.top, g.right, g.bottom],
                  font: parseFloat(cs.fontSize),
                  first: parseFloat(getComputedStyle(rv.title_el,
                                                     '::first-line').fontSize),
                  border: parseFloat(cs.borderTopWidth),
                  fill: cs.backgroundColor});
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


def _legends(mode, legend):
    spec = bk._spec([bk._graph("g1", bk._TWO, {"legend": legend},
                               title=False)], scheme="s2color")
    return kb._measure(mode, spec, _TITLE_JS)[1400]["out"]


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestTitleInChrome:

    def test_title_over_subtitle(self, mode):
        """T in the title's size above S, the block centred over the keys
        (sub_under: T and S on the keys' centre line)."""
        rec = TRUTH["sub_under"]
        (lg,) = _legends(mode, 'title("T") subtitle("S")')
        assert abs(lg["first"] / lg["font"]
                   - rec["T"]["size"] / rec["S"]["size"]) < 0.02
        cx = (lg["title"][0] + lg["title"][2]) / 2.0
        gx = (lg["grid"][0] + lg["grid"][2]) / 2.0
        assert abs(cx - gx) <= 1.5, lg
        assert lg["title"][3] <= lg["grid"][1] + 0.5

    def test_position_5(self, mode):
        """position(5): below the keys at their right end."""
        (lg,) = _legends(mode, 'title("T", position(5))')
        assert lg["title"][1] >= lg["grid"][3] - 0.5, lg
        assert abs(lg["title"][2] - lg["grid"][2]) <= 1.5, lg

    def test_box(self, mode):
        """box: the scheme's text box frame round the title."""
        (lg,) = _legends(mode, 'title("T", box)')
        assert lg["border"] > 0
        assert lg["fill"] == "rgb(217, 230, 235)", lg
