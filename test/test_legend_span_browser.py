"""
test_legend_span_browser.py -- legend(span) and title(, span) placed on the
whole graph in a browser (WP-32, BUGS.md "Five scheme keys are parsed and
read by nothing").

Measured 19oct2026 (StataNow 19.5, SVG): span centres a legend at 6 or 12
o'clock on the graph's width and one at 3 or 9 on its height, where twoway
otherwise centres it on the plot region; a spanned title(), subtitle(),
note() or caption() takes the same place on the graph.  Only BokehJS knows
where the frame sits in the canvas once the axes are laid out, so the
figure carries _DASH_SPAN_JS on its laid-out size; here headless Chrome
draws both modes' pages and the box's centre is read against the canvas's
centre, at load and after the page is narrowed.  Without Chrome these
tests skip, as test_by_axes_keys_browser.py's do.
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

#: Each figure's canvas, frame and every visible legend's and titled
#: annotation's box (canvas px), at load and after the body is narrowed to
#: 700 px (BokehJS's resize handler called, as virtual time renders no
#: frames).
_SPAN_JS = r"""
<script>
function state() {
  const out = [];
  const visit = (v) => {
    if (!v) return;
    if (v.frame && v.renderer_views) {
      const f = v.frame.bbox, c = v.bbox;
      const boxes = [];
      for (const [m, rv] of v.renderer_views) {
        const t = m.type || '';
        if (!(t === 'Legend' || t === 'Title') || !m.visible) continue;
        if (t === 'Title' && !m.text) continue;
        const b = rv.bbox;
        if (!b || !(b.width > 0)) continue;
        boxes.push({type: t, text: t === 'Title' ? m.text : '',
                    box: [b.x0, b.y0, b.x1, b.y1]});
      }
      out.push({canvas: [c.width, c.height],
                frame: [f.x0, f.y0, f.x1, f.y1], boxes});
    }
    for (const c of (v.child_views || [])) visit(c);
  };
  for (const v of Object.values(Bokeh.index)) visit(v);
  return out;
}
addEventListener('load', () => setTimeout(() => {
  const wide = state();
  document.body.style.width = '700px';
  for (const v of Object.values(Bokeh.index)) v.after_resize();
  dispatchEvent(new Event('resize'));
  setTimeout(() => {
    parent.postMessage('DASHPROBE' + JSON.stringify(
      {W: innerWidth, wide, narrow: state()}), '*');
  }, 2500);
}, 3000));
</script>
"""

#: A long left side: the y axis and two edge titles push the frame right,
#: so the plot region's centre is well off the canvas's.
_LEFT = {"l1title": '"A left edge title"', "l2title": '"And another"',
         "ytitle": '"A y title"'}


def _figs(mode, go):
    spec = bk._spec([bk._graph("g1", bk._TWO, dict(_LEFT, **go),
                               title=False)], scheme="s2color")
    got = kb._measure(mode, spec, _SPAN_JS)[1400]
    return got["wide"], got["narrow"]


def _centre(box):
    return (box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestTheLegendSpans:

    def test_6_oclock_is_centred_on_the_graph(self, mode):
        for figs in _figs(mode, {"legend": "pos(6) span"}):
            (fig,) = figs
            (lg,) = [b for b in fig["boxes"] if b["type"] == "Legend"]
            f = fig["frame"]
            # The plot region is off centre: a span that did nothing would
            # show here.
            assert abs((f[0] + f[2]) / 2.0 - fig["canvas"][0] / 2.0) > 30
            assert abs(_centre(lg["box"])[0]
                       - fig["canvas"][0] / 2.0) <= 1.5, fig
            # Still under the plot.
            assert lg["box"][1] >= f[3], fig

    def test_without_span_it_is_centred_on_the_plot_region(self, mode):
        for figs in _figs(mode, {"legend": "pos(6)"}):
            (fig,) = figs
            (lg,) = [b for b in fig["boxes"] if b["type"] == "Legend"]
            f = fig["frame"]
            assert abs(_centre(lg["box"])[0] - (f[0] + f[2]) / 2.0) <= 1.5

    def test_3_oclock_is_centred_on_the_graphs_height(self, mode):
        for figs in _figs(mode, {"legend": "pos(3) span",
                                 "title": '"A title"',
                                 "note": '"A note"'}):
            (fig,) = figs
            (lg,) = [b for b in fig["boxes"] if b["type"] == "Legend"]
            f = fig["frame"]
            assert abs((f[1] + f[3]) / 2.0 - fig["canvas"][1] / 2.0) > 10
            assert abs(_centre(lg["box"])[1]
                       - fig["canvas"][1] / 2.0) <= 1.5, fig
            assert lg["box"][0] >= f[2], fig

    def test_7_oclock_is_at_the_graphs_left_end(self, mode):
        for figs in _figs(mode, {"legend": "pos(7) span"}):
            (fig,) = figs
            (lg,) = [b for b in fig["boxes"] if b["type"] == "Legend"]
            assert lg["box"][0] < fig["frame"][0] - 30, fig
            assert 0 <= lg["box"][0] <= 15, fig

    @pytest.mark.parametrize("pos", ("6", "12", "9"))
    def test_across_its_side_it_stays_where_it_was(self, mode, pos):
        """span moves the box along its side only: under the plot it keeps
        its height, beside it its distance from the plot, whatever its
        margin."""
        for extra in ("", " bmargin(large)"):
            plain = _figs(mode, {"legend": "pos(%s)%s" % (pos, extra)})
            span = _figs(mode, {"legend": "pos(%s) span%s" % (pos, extra)})
            for a, b in zip(plain, span):
                (la,) = [x for x in a[0]["boxes"] if x["type"] == "Legend"]
                (lb,) = [x for x in b[0]["boxes"] if x["type"] == "Legend"]
                i = 0 if pos == "9" else 1
                assert abs(la["box"][i] - lb["box"][i]) <= 1, (la, lb)
