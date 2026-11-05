"""
test_by_row_frames_browser.py -- every plot region in one by() row is as
tall as the others, and every one in a column as wide, in a browser.

BUGS.md "Plot regions in one by() row can differ by 1 px in height; twoway
draws them equal" (filed 05nov2026).  twoway lays a by() row's plot
regions out equal.  Since WP-41 41-05 (d536b03e) the grid's row heights
follow the width scale and are fractional, so Bokeh's whole-pixel frames
in one row could end 1 px apart (Bokeh 3.8: the middle column of a row;
3.9: a panel in row 1).  Here headless Chrome draws both modes' pages of a
2 x 2 by() graph (by(foreign, total): three panels and a hole) and a
3-column one (by(rep78): five panels in two rows, with and without
aspectratio(1)) at four widths, and
every panel's plot region (page px) is read: the frames in one row share
their top and foot, and those in one column their left and right edges,
to 0.01 px.  Without Chrome these tests skip, as
test_by_axes_keys_browser.py's do.
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

#: Every by() panel's plot region (an unnamed figure in a GridBox), page
#: px, once the page has laid out.
_FRAMES_JS = r"""
<script>
function frames() {
  const out = [];
  const visit = (v, box) => {
    if (!v) return;
    if (v.model && v.model.type === 'GridBox') box = v;
    if (v.frame && v.model && !v.model.name && box) {
      const c = v.canvas_view.el.getBoundingClientRect(), f = v.frame.bbox;
      out.push([c.left + f.x0, c.top + f.y0, c.left + f.x1, c.top + f.y1]);
    }
    for (const c of (v.child_views || [])) visit(c, box);
  };
  for (const v of Object.values(Bokeh.index)) visit(v, null);
  return out;
}
addEventListener('load', () => setTimeout(() => {
  parent.postMessage('DASHPROBE' + JSON.stringify(
    {W: innerWidth, frames: frames()}), '*');
}, 3000));
</script>
"""

#: (graph options, panels, columns, widths): a 2 x 2 grid with a hole
#: and a 3-column one, its panels shaped by the graph's size or by
#: aspectratio(1) (WP-41 BY-18), at the 1400 px reference, two widths
#: between and the stcolor graph's own 5.5-inch 528 px -- where the
#: 3-column grid's cells no longer fit and it stacks into one column
#: (_dash_reflow; at 640 px too), so it is read at 900 px instead.
_GRAPHS = (({"by": "foreign, total"}, 3, 2, (1400, 1000, 768, 528)),
           ({"by": "rep78"}, 5, 3, (1400, 1000, 900, 768)),
           ({"by": "rep78", "aspectratio": "1"}, 5, 3,
            (1400, 1000, 900, 768)))


def _lines(frames, i, tol=8.0):
    """*frames* grouped by edge *i* (1: top, a row; 0: left, a column):
    frames whose edge is within *tol* px of the group's first share it."""
    groups = []
    for f in sorted(frames, key=lambda q: q[i]):
        if groups and abs(f[i] - groups[-1][0][i]) <= tol:
            groups[-1].append(f)
        else:
            groups.append([f])
    return groups


@pytest.mark.parametrize("mode", ("saved", "served"))
@pytest.mark.parametrize("go,n,cols,widths", _GRAPHS,
                         ids=("2x2", "3col", "3col_ar1"))
def test_a_rows_plot_regions_are_equal(mode, go, n, cols, widths):
    """In every row the panels' frames share their top and foot, and in
    every column their left and right, to 0.01 px, at each width."""
    spec = bk._spec([bk._graph("g1", bk._ONE, go, title=False)])
    got = kb._measure(mode, spec, _FRAMES_JS, widths)
    bad = []
    for w in widths:
        fr = got[w]["frames"]
        assert len(fr) == n, (w, fr)
        rows, columns = _lines(fr, 1), _lines(fr, 0)
        # The grid is laid out, not stacked into one column.
        assert len(columns) == cols, (w, fr)
        for grp, edges in ((rows, (1, 3)), (columns, (0, 2))):
            for line in grp:
                for e in edges:
                    vals = [f[e] for f in line]
                    if max(vals) - min(vals) > 0.01:
                        bad.append((w, e, vals))
    assert not bad, bad
