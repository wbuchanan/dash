"""
test_legend_place_browser.py -- a hole in a one-column or one-row legend
drawn in a browser as twoway draws it (WP-43 LT-17, ruling D69).

The legend's keys are DOM items in a CSS grid in the Legend's shadow root;
dash draws a hole as an empty track of that grid (the Legend's
``dash_legend_holes`` stylesheet), so only the browser lays it out.
Headless Chrome draws both modes' pages and reads, against the same graph
without the hole: the gap at the hole is one more grid gap (the legend's
own spacing), the legend's box grows by it and the plot region gives way
by it, as twoway's does (legend_place_truth.json holes_1col_<k>: the box
one legend_row_gap taller; holes_1row: one legend_col_gap wider).
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

#: Each series legend's box, grid gaps and key items, and its plot's
#: frame (page px), per figure in page order.
_HOLES_JS = r"""
<script>
addEventListener('load', () => setTimeout(() => {
  const out = [];
  const visit = (v) => {
    if (!v) return;
    if (v.frame && v.renderer_views) {
      for (const [m, rv] of v.renderer_views) {
        if (m.type !== 'Legend' || !m.visible || !rv.grid_el) continue;
        const h = rv.el.getBoundingClientRect();
        const cs = getComputedStyle(rv.grid_el);
        const f = v.frame.bbox;
        out.push({name: m.name || '',
                  host: [h.left, h.top, h.right, h.bottom],
                  rowgap: parseFloat(cs.rowGap), colgap: parseFloat(cs.columnGap),
                  items: [...rv.grid_el.children].map(e => {
                    const r = e.getBoundingClientRect();
                    return [r.left, r.top, r.right, r.bottom]; }),
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
    out = kb._measure(mode, spec, _HOLES_JS)[1400]["out"]
    return out


def _h(r):
    return r[3] - r[1]


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestHoleInChrome:

    def test_one_column(self, mode):
        """holes(2) cols(1): key 2 is one more row gap below key 1, the
        box one row gap taller and the frame one row gap shorter."""
        base, hole = _legends(mode, "cols(1)", "holes(2) cols(1)")
        g = hole["rowgap"]
        assert g > 0 and abs(g - base["rowgap"]) < 0.01
        i0, i1 = base["items"], hole["items"]
        assert len(i1) == 3
        pitch0 = i0[1][1] - i0[0][1]
        assert abs((i1[1][1] - i1[0][1]) - (pitch0 + g)) <= 1.0, (i0, i1)
        assert abs((i1[2][1] - i1[1][1]) - pitch0) <= 1.0, (i0, i1)
        assert abs(_h(hole["host"]) - _h(base["host"]) - g) <= 1.0
        # The plot region gives way, as twoway's does.
        assert abs(_h(base["frame"]) - _h(hole["frame"]) - g) <= 1.5, (
            base["frame"], hole["frame"])

    def test_before_and_after(self, mode):
        """holes(1) and holes(4): the gap above the first key and below
        the last; the keys' pitch unchanged."""
        base, first, last = _legends(mode, "cols(1)", "holes(1) cols(1)",
                                     "holes(4) cols(1)")
        g = base["rowgap"]
        for rec in (first, last):
            assert abs(_h(rec["host"]) - _h(base["host"]) - g) <= 1.0
            p = [b[1] - a[1] for a, b in zip(rec["items"], rec["items"][1:])]
            p0 = [b[1] - a[1] for a, b in zip(base["items"],
                                              base["items"][1:])]
            assert all(abs(x - y) <= 1.0 for x, y in zip(p, p0))
        assert (first["items"][0][1] - first["host"][1]) - (
            base["items"][0][1] - base["host"][1]) == pytest.approx(g, abs=1)
        assert (last["host"][3] - last["items"][-1][3]) - (
            base["host"][3] - base["items"][-1][3]) == pytest.approx(g, abs=1)

    def test_one_row(self, mode):
        """holes(2) rows(1): one more column gap between keys 1 and 2."""
        base, hole = _legends(mode, "rows(1)", "holes(2) rows(1)")
        g = hole["colgap"]
        assert g > 0
        i0, i1 = base["items"], hole["items"]
        assert abs((i1[1][0] - i1[0][2]) - (i0[1][0] - i0[0][2] + g)) <= 1.0
        w0 = base["host"][2] - base["host"][0]
        w1 = hole["host"][2] - hole["host"][0]
        assert abs(w1 - w0 - g) <= 1.0

    def test_by_cell(self, mode):
        """by(foreign): the overall legend's cell draws the gap too."""
        (cell,) = [r for r in _legends(mode, "holes(2) cols(1)",
                                       by="foreign")
                   if r["name"].endswith("_key")]
        i = cell["items"]
        assert len(i) == 3
        g = cell["rowgap"]
        assert abs((i[1][1] - i[0][1]) - (i[2][1] - i[1][1]) - g) <= 1.0
