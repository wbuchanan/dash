"""
test_by_axes_keys_browser.py -- by()'s shared axes and the panel label's
box in a browser (WP-30 P1.15c).

test_by_axes_keys.py reads the models; here headless Chrome draws both
modes' pages under their own Content Security Policy.  The stacked view:
at 1400 px the right panel's y axis is hidden and the axis titles are in
their cells; when the grid narrows to one column (the page body is set to
375 px and a resize is dispatched) every panel's axes and titles show and
the cells hide; widened again, twoway's layout returns -- with no CSP
violation.  The label box: each panel's ``dash_by_label_box`` spans its
frame and ends on its top edge, drawn in the scheme's fill (s2color), and
under s1color its outline is black.  The save button writes one file.
Without Chrome these tests skip, as test_by_scales_chrome.py's do.
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

if responsive_probe.find_chrome() is None:
    pytest.skip("headless Chrome is not installed (set DASH_CHROME); "
                "the browser check is skipped", allow_module_level=True)

#: Wide, narrowed and widened again: the panels' axes and the title
#: cells, read from the document's models; CSP violations collected.
_STACK_JS = r"""
<script>
const V = [];
addEventListener('securitypolicyviolation', e => V.push(e.violatedDirective));
function state() {
  const doc = Bokeh.documents[0];
  const ms = [...(doc._all_models ? doc._all_models.values()
                                  : doc.all_models)];
  const ax = ms.filter(m => m.type && m.type.endsWith('Axis'));
  const cells = ms.filter(m => m.name === 'dash_by_ytitle'
                               || m.name === 'dash_by_xtitle');
  return {axes: ax.length, vis: ax.filter(a => a.visible).length,
          titled: ax.filter(a => a.visible && a.axis_label).length,
          cells: cells.map(c => c.visible)};
}
// Each step waits for the layout to settle: up to 2.5 s for the axes'
// state to change, polled every 250 ms.
function settle(from, then, left) {
  const now = state();
  if (now.vis !== from.vis || left <= 0) { then(now); return; }
  setTimeout(() => settle(from, then, left - 250), 250);
}
addEventListener('load', () => setTimeout(() => {
  const wide = state();
  document.body.style.width = '375px';
  dispatchEvent(new Event('resize'));
  settle(wide, (narrow) => {
    document.body.style.width = '';
    dispatchEvent(new Event('resize'));
    settle(narrow, (again) => {
      parent.postMessage('DASHPROBE' + JSON.stringify(
        {W: innerWidth, wide, narrow, again, V}), '*');
    }, 2500);
  }, 2500);
}, 3000));
</script>
"""

#: Each panel's frame and its label box, and the canvas pixels inside the
#: box (left of the label) and on its top edge.
_BOX_JS = r"""
<script>
addEventListener('load', () => setTimeout(() => {
  const out = [];
  const rgb = (ctx, x, y) => {
    const r = window.devicePixelRatio || 1;
    return [...ctx.getImageData(Math.round(x * r), Math.round(y * r),
                                1, 1).data].slice(0, 3);
  };
  const visit = (v) => {
    if (!v) return;
    if (v.frame && v.renderer_views) {
      for (const [m, rv] of v.renderer_views) {
        if (m.name !== 'dash_by_label_box') continue;
        const f = v.frame.bbox, b = rv.bbox;
        const ctx = v.canvas_view.primary.ctx;
        out.push({frame: [f.x0, f.y0, f.x1, f.y1],
                  box: [b.x0, b.y0, b.x1, b.y1],
                  fill: rgb(ctx, b.x0 + 4, b.y0 + b.height / 2),
                  edges: [[rgb(ctx, b.x0 - 0.5, b.y0 + b.height / 2),
                           rgb(ctx, b.x0 + 0.5, b.y0 + b.height / 2)],
                          [rgb(ctx, b.x1 - 0.5, b.y0 + b.height / 2),
                           rgb(ctx, b.x1 + 0.5, b.y0 + b.height / 2)],
                          [rgb(ctx, b.x0 + 4, b.y0 - 0.5),
                           rgb(ctx, b.x0 + 4, b.y0 + 0.5)],
                          [rgb(ctx, b.x0 + 4, b.y1 - 0.5),
                           rgb(ctx, b.x0 + 4, b.y1 + 0.5)]]});
      }
    }
    for (const c of (v.child_views || [])) visit(c);
  };
  for (const v of Object.values(Bokeh.index)) visit(v);
  parent.postMessage('DASHPROBE' + JSON.stringify({W: innerWidth, out}),
                     '*');
}, 3000));
</script>
"""


def _page(mode, spec):
    if mode == "saved":
        tag = next(bk._SEQ)
        a = os.path.join(bk._TMP, "b_%d.json" % tag)
        b = os.path.join(bk._TMP, "bd_%d.json" % tag)
        with open(a, "w") as fh:
            json.dump(spec, fh)
        with open(b, "w") as fh:
            json.dump(bk.tg._data(), fh)
        return bk.dr.DashRenderer(a, b).render()
    from bokeh.embed import file_html
    from bokeh.resources import INLINE
    _roots, _n, owner = bk._build(mode, spec)
    return file_html(owner, INLINE, "served")


def _measure(mode, spec, js, widths=(1400,)):
    mp = pytest.MonkeyPatch()
    mp.setattr(responsive_probe, "PROBE_JS", js)
    try:
        return responsive_probe.measure_many(_page(mode, spec), widths)
    finally:
        mp.undo()


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestInChrome:
    def test_stacking(self, mode):
        """1400 px: the right panel's y axis hidden, no panel axis titled,
        the title cells shown; one column: every axis and title shown and
        the cells hidden; wide again: restored; no CSP violation."""
        spec = bk._spec([bk._graph("g1", bk._ONE, {"by": "foreign"},
                                   title=False)], scheme="s2color")
        both = _measure(mode, spec, _STACK_JS, (1400, 375))
        got = both[1400]
        # A phone-width page loads stacked.
        assert both[375]["wide"]["vis"] == 4 and both[375]["V"] == []
        assert both[375]["wide"]["cells"] == [False, False]
        assert got["V"] == []
        wide, narrow, again = got["wide"], got["narrow"], got["again"]
        assert wide["axes"] == 4 and wide["vis"] == 3
        assert wide["titled"] == 0 and wide["cells"] == [True, True]
        assert narrow["vis"] == 4 and narrow["titled"] == 4
        assert narrow["cells"] == [False, False]
        assert again == wide

    def test_label_box(self, mode):
        """Each box spans its panel's frame and ends on its top edge, in
        s2color's fill; under s1color its outline is black all round."""
        spec = bk._spec([bk._graph("g1", bk._ONE, {"by": "foreign"},
                                   title=False),
                         bk._graph("g2", bk._ONE, {"by": "foreign",
                                                   "scheme": "s1color"},
                                   title=False)], scheme="s2color")
        out = _measure(mode, spec, _BOX_JS)[1400]["out"]
        assert len(out) == 4
        fills = set()
        for rec in out:
            f, b = rec["frame"], rec["box"]
            assert abs(b[0] - f[0]) <= 1 and abs(b[2] - f[2]) <= 1, rec
            assert abs(b[3] - f[1]) <= 1, rec
            fills.add(tuple(rec["fill"]))
        assert (217, 230, 235) in fills          # s2color #D9E6EB
        assert (229, 218, 165) in fills          # s1color #E5DAA5
        s1 = [r for r in out if tuple(r["fill"]) == (229, 218, 165)]
        for rec in s1:
            # Each edge, sampled either side of its line, is drawn darker
            # than the fill: the outline is there all round.
            for pair in rec["edges"]:
                assert min(sum(px) for px in pair) < sum(rec["fill"]) - 150, \
                    rec

    def test_save_button(self, mode):
        """The grid's one save button writes one named file."""
        from bokeh.models import GridPlot, SaveTool
        spec = bk._spec([bk._graph("g1", bk._TWO, {"by": "foreign"})])
        roots, _n, _o = bk._build(mode, spec)
        grids = [m for r in roots for m in r.references()
                 if isinstance(m, GridPlot)
                 and any(getattr(c[0], "name", "") == "dash_by_legend"
                         for c in m.children)]
        assert len(grids) == 1
        saves = [t for t in grids[0].toolbar.tools
                 if isinstance(t, SaveTool)]
        assert len(saves) == 1 and saves[0].filename
