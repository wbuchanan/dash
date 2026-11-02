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
import test_by_text as tbt  # noqa: E402

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
        let b = rv.bbox;
        if (t === 'Title') {
          // A Title's bbox is its panel; its text box is what it paints,
          // computed as the next paint computes it (virtual time paints
          // no frames).
          rv.compute_geometry();
          const r = rv._rect;
          if (!r) continue;
          const x0 = r.sx - r.anchor.x * r.width;
          const y0 = r.sy - r.anchor.y * r.height;
          b = {x0, y0, x1: x0 + r.width, y1: y0 + r.height, width: r.width};
        }
        if (!b || !(b.width > 0)) continue;
        boxes.push({type: t, text: t === 'Title' ? m.text : '',
                    box: [b.x0, b.y0, b.x1, b.y1]});
      }
      // The graph: its graph region box (GW-6's margin round the figure)
      // in canvas px, else the canvas.
      let graph = [0, 0, c.width, c.height];
      for (let q = v.parent; q != null; q = q.parent) {
        if (q.model && q.model.type === 'GridBox') break;
        if (q.model && q.el && (q.model.tags || []).includes(
            'dash_graph_region')) {
          const g = q.el.getBoundingClientRect();
          const k = v.canvas_view.el.getBoundingClientRect();
          graph = [g.left - k.left, g.top - k.top, g.right - k.left,
                   g.bottom - k.top];
          break;
        }
      }
      out.push({canvas: [c.width, c.height], graph,
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


#: The legend's margin at the 4-inch unit and 96 px an inch.
_LM = 5


def _k(width, scheme="stcolor"):
    """The width scale of a graph drawn *width* px wide (DECISIONS D66,
    the maintainer's ruling of 01nov2026: the graph is one picture):
    width over its inch width at 96 px, times twoway's unit for the
    scheme's reference side.  Flipped: every size in px was the 4-inch,
    96-px value at any width."""
    import dash_render as _dr
    sp = _dr.SchemeParser(scheme)
    return float(width) / (sp.graphsize_x * 96.0) * sp.size_ref_in / 4.0


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
            # The graph region's edge (s2color's margin graph, 3.5% of
            # min(W, H)) plus the gap the box keeps from the plot region
            # without span (its own margin, 5 px), as twoway places it.
            # Flipped (BUGS.md "A graph's canvas ended before its own x
            # axis, x title and colour key labels"): the graph is its graph
            # region box, the canvas inside its margin.
            g = fig["graph"]
            edge = g[0] + 0.035 * min(g[2] - g[0], g[3] - g[1])
            # Flipped (D66): the margin is 5 px times the width scale.
            assert abs(lg["box"][0] - (edge + 5 * _k(g[2] - g[0],
                                                     "s2color"))) <= 1.5, fig

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


def _title(fig, text):
    (b,) = [x for x in fig["boxes"] if x["type"] == "Title"
            and x["text"] == text]
    return b["box"]


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestTheTitlesSpan:

    def test_each_box_is_placed_on_the_graph(self, mode):
        go = {"title": '"A spanned title", span',
              "subtitle": '"A plain subtitle"',
              "note": '"A spanned note", span',
              "caption": '"A spanned caption", span position(5)'}
        # The gap each end box keeps from the plot region without span.
        (plain,) = _figs(mode, {"note": '"A spanned note"',
                                "caption": '"A spanned caption", '
                                           'position(5)'})[0]
        gap = (_title(plain, "A spanned note")[0] - plain["frame"][0],
               plain["frame"][2] - _title(plain, "A spanned caption")[2])
        for figs in _figs(mode, go):
            (fig,) = figs
            W, f = fig["canvas"][0], fig["frame"]
            assert abs((f[0] + f[2]) / 2.0 - W / 2.0) > 30
            t = _title(fig, "A spanned title")
            assert abs(_centre(t)[0] - W / 2.0) <= 1.5, fig
            # Without span: centred on the plot region.
            s = _title(fig, "A plain subtitle")
            assert abs(_centre(s)[0] - (f[0] + f[2]) / 2.0) <= 1.5, fig
            # The note at the graph's left, the caption at its right.
            # Against the graph region's edges, as twoway places them
            # (measured: a spanned note at the region's left plus the gap
            # it keeps from the plot region without span).
            # Flipped (BUGS.md "A graph's canvas ended before its own x
            # axis, x title and colour key labels"): the graph is its graph
            # region box, the canvas inside its margin.
            g = fig["graph"]
            edge = 0.035 * min(g[2] - g[0], g[3] - g[1])
            n, c = _title(fig, "A spanned note"), _title(
                fig, "A spanned caption")
            assert n[0] < f[0] - 30, fig
            assert abs(n[0] - (g[0] + edge + gap[0])) <= 1.5, fig
            assert abs(c[2] - (g[2] - edge - gap[1])) <= 1.5, fig


#: by(): every legend and titled box (page px) and the by() grid's own box:
#: the GridBox nearest above the by() legend cell (inside the GridPlot,
#: without its toolbar).
_BY_JS = r"""
<script>
function rect(el){const r=el.getBoundingClientRect();return [r.left,r.top,r.right,r.bottom];}
// Flipped (WP-45 GW-6): the graph is the grid's graph region box, the
// scheme's graph margin (its CSS padding) included, where it was the grid.
function gbox(v){for(let q=v;q!=null;q=q.parent){if(q.model&&q.el&&(q.model.tags||[]).includes('dash_graph_region'))return q.el;}return v.el;}
function state() {
  const boxes = [], pframes = [], prows = [], pcells = [];
  let grid = null, pgrid = null;
  const visit = (v, box) => {
    if (!v) return;
    if (v.model && v.model.type === 'GridBox') box = v;
    if (v.model && (v.model.name === 'dash_by_legend'
        || v.model.name === 'dash_by_clegend'
        || v.model.name === 'dash_by_plegend') && box) grid = rect(gbox(box));
    if (v.frame && v.model && !v.model.name && box && !pgrid) {
      pgrid = rect(gbox(box));
    }
    if (v.frame && v.model && !v.model.name && box) {
      pframes.push(v.frame.bbox.width);
      const cr0 = v.canvas_view.el.getBoundingClientRect();
      prows.push([cr0.top + v.frame.bbox.y0, cr0.top + v.frame.bbox.y1]);
      // WP-41 41-04: each panel's frame's top left corner (page px).
      pcells.push([cr0.left + v.frame.bbox.x0, cr0.top + v.frame.bbox.y0]);
    }
    if (v.frame && v.renderer_views) {
      const cr = v.canvas_view.el.getBoundingClientRect();
      for (const [m, rv] of v.renderer_views) {
        const t = m.type || '';
        if (!m.visible) continue;
        if ((t === 'Legend' || t === 'ColorBar') && rv.bbox
            && rv.bbox.width > 0
            && (t === 'Legend' || m.name !== 'dash_by_label_box')) {
          const b = rv.bbox;
          boxes.push({type: t, cell: v.model.name || '', text: '',
                      box: t === 'Legend' ? rect(rv.el)
                        : [cr.left + b.x0, cr.top + b.y0, cr.left + b.x1,
                           cr.top + b.y1],
                      canvas: [cr.left, cr.top, cr.left + v.bbox.width,
                               cr.top + v.bbox.height],
                      frame: [cr.left + v.frame.bbox.x0,
                              cr.left + v.frame.bbox.x1],
                      len: t === 'ColorBar' ? m.height : null,
                      // A colour key's box and its colour strip.
                      key: (t === 'ColorBar' && rv._inner_layout) ? (() => {
                        const b = rv._inner_layout.bbox;
                        return [cr.left + b.x0, cr.top + b.y0, cr.left + b.x1,
                                cr.top + b.y1]; })() : null,
                      bar: (t === 'ColorBar' && rv._frame_view) ? (() => {
                        const b = rv._frame_view.bbox;
                        return [cr.left + b.x0, cr.top + b.y0, cr.left + b.x1,
                                cr.top + b.y1]; })() : null,
                      orient: t === 'ColorBar' ? m.orientation : null});
        } else if (t === 'Title' && m.text) {
          rv.compute_geometry();
          const r = rv._rect; if (!r) continue;
          // The text's box about its anchor, turned by its angle (a y
          // title is turned a quarter).
          const a = r.angle || 0, ca = Math.cos(a), sa = Math.sin(a);
          const xs = [], ys = [];
          for (const lx of [-r.anchor.x * r.width, (1 - r.anchor.x) * r.width])
            for (const ly of [-r.anchor.y * r.height, (1 - r.anchor.y) * r.height]) {
              xs.push(r.sx + lx * ca - ly * sa + cr.left);
              ys.push(r.sy + lx * sa + ly * ca + cr.top);
            }
          boxes.push({type: t, cell: v.model.name || '', text: m.text,
                      box: [Math.min(...xs), Math.min(...ys),
                            Math.max(...xs), Math.max(...ys)],
                      canvas: [cr.left, cr.top, cr.right, cr.bottom],
                      frame: [cr.left + v.frame.bbox.x0,
                              cr.left + v.frame.bbox.x1],
                      // The outer edge of the panel's visible left axes.
                      yaxis: (() => { let x = null;
                        for (const [am, av] of v.renderer_views) {
                          if (!am.visible || !(v.model.left || []).includes(am)
                              || !(am.type || '').endsWith('Axis')) continue;
                          const b = av.bbox; if (!b || !(b.width > 0)) continue;
                          x = x == null ? b.x0 : Math.min(x, b.x0);
                        }
                        return x == null ? null : cr.left + x; })()});
        }
      }
    }
    for (const c of (v.child_views || [])) visit(c, box);
  };
  for (const v of Object.values(Bokeh.index)) visit(v, null);
  if (!grid) grid = pgrid;
  // The panels plus their axes: the union of the grid's panel figures
  // (every child not named dash_by_*).
  let panels = null, pright = null;
  const gv = (() => { let f = null; const look = (v) => { if (!v || f) return;
    if (v.model && v.model.type === 'GridBox' && (v.child_views || []).some(
      (k) => k.model && (k.model.name === 'dash_by_legend'
        || k.model.name === 'dash_by_clegend'
        || k.model.name === 'dash_by_plegend'))) { f = v; return; }
    for (const c of (v.child_views || [])) look(c); };
    for (const v of Object.values(Bokeh.index)) look(v); return f; })();
  if (gv) {
    let yt = null;
    for (const k of gv.child_views || []) {
      const nm = (k.model && k.model.name) || '';
      if (nm === 'dash_by_ytitle') { yt = k; continue; }
      // WP-41 VF-6: a row's outer y axis cell is the panels' own axis.
      // Flipped (WP-45 GW-6): the stacking ruler closes the panels on the
      // right, as twoway's panels reach the graph region's edge.
      if (nm.startsWith('dash_by_') && !nm.startsWith('dash_by_yaxis_')
          && nm !== 'dash_by_ruler') continue;
      const r = rect(k.el);
      if (!(r[2] > r[0])) continue;
      if (nm !== 'dash_by_ruler') pright = pright == null ? r[2] : Math.max(pright, r[2]);
      panels = panels == null ? r : [Math.min(panels[0], r[0]),
        Math.min(panels[1], r[1]), Math.max(panels[2], r[2]),
        Math.max(panels[3], r[3])];
    }
    // Flipped (WP-45 GW-6): twoway's panels start one y-title size right
    // of the y title's cell (by_text_truth.json bp40: 113.4 + 112.56 of
    // 5400), not at dash's y labels.
    const tm = yt && (yt.model.left || []).find((t) => t && t.type === 'Title' && t.text);
    if (panels && tm) {
      const fs = String(tm.text_font_size || ''), fn = parseFloat(fs);
      panels[0] = Math.min(panels[0], rect(yt.el)[0] + (/pt$/.test(fs) ? fn * 4 / 3 : fn));
    }
  }
  return {grid, boxes, panels, pright, pframes, prows, pcells};
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


def _by(mode, go):
    spec = bk._spec([bk._graph("g1", bk._TWO, dict(go, ytitle='"Price"'),
                               title=False)], scheme="stcolor")
    got = kb._measure(mode, spec, _BY_JS)[1400]
    return got["wide"], got["narrow"]


def _by_legend(state):
    (lg,) = [b for b in state["boxes"] if b["type"] == "Legend"
             and b["cell"] == "dash_by_legend"]
    return lg["box"]


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestByLegendSpans:
    """Measured 19oct2026 (StataNow 19.5, stcolor, SVG of ``twoway (scatter
    price weight) (scatter mpg weight), ylabel(, format(%15.2fc))
    by(foreign, legend(pos(#) [span]))``): span places by()'s legend on the
    whole graph -- pos(6) centred at x 2700 of 5400 (2756.3 without), pos(3)
    at y 1620 of 3240 (1499.3 without), pos(7) at 152.2 (264.8 without),
    the graph region's edge 113.4 plus 38.8, as without by()."""

    def test_6_oclock_is_centred_on_the_graph(self, mode):
        for st in _by(mode, {"by": "foreign, legend(pos(6) span)"}):
            g, lg = st["grid"], _by_legend(st)
            assert abs(_centre(lg)[0] - (g[0] + g[2]) / 2.0) <= 1.5, st

    def test_3_oclock_is_centred_on_the_graphs_height(self, mode):
        for st in _by(mode, {"by": "foreign, legend(pos(3) span)"}):
            g, lg = st["grid"], _by_legend(st)
            assert abs(_centre(lg)[1] - (g[1] + g[3]) / 2.0) <= 1.5, st

    def test_7_oclock_is_at_the_graph_regions_edge(self, mode):
        for st in _by(mode, {"by": "foreign, legend(pos(7) span)"}):
            g, lg = st["grid"], _by_legend(st)
            edge = 0.035 * min(g[2] - g[0], g[3] - g[1])
            # Flipped (D66): the margin is 5 px times the width scale.
            assert abs(lg[0] - (g[0] + edge + _LM * _k(g[2] - g[0]))) <= 1.5, st


def _by_titles(state, text):
    return [b for b in state["boxes"] if b["type"] == "Title"
            and b["text"] == text]


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestByTitlesSpan:
    """Measured 19oct2026 (StataNow 19.5, stcolor, the same graph with
    by(foreign)): by()'s own spanned title, note and caption are placed on
    the whole graph (title 2700 of 5400, 2251.3 without; note 132.8, 245.4
    without; caption(, pos(5)) ending 5267.2, 4257.4 without), and a
    title() or note() given outside by() is drawn on every panel, spanned
    on that panel's graph (panel 1's title 1431.2, 1646.2 without; its
    note 355.9, its y labels' edge, 899.3 without)."""

    def test_bys_own_boxes_are_placed_on_the_graph(self, mode):
        by = ('foreign, title("A by title", span) note("A by note", span) '
              'caption("A by caption", span pos(5))')
        # Flipped (WP-32, BUGS.md "A by() legend, key or text row was
        # added under panels that kept their proportion, where twoway
        # shortens the panels"): the gap each end box keeps is its text
        # box's margin (stcolor 0.6 units, BUGS.md "A by() note or caption
        # sat at the panels' end without its margin"), read directly, as
        # the plain graph's grid is no longer the spanned graph's size.
        for st in _by(mode, {"by": by}):
            g = st["grid"]
            edge = 0.035 * min(g[2] - g[0], g[3] - g[1])
            m6 = 0.006 * min(g[2] - g[0], g[3] - g[1])
            gap = (m6, m6)
            (t,) = _by_titles(st, "A by title")
            assert abs(_centre(t["box"])[0] - (g[0] + g[2]) / 2.0) <= 1.5
            (n,) = _by_titles(st, "A by note")
            assert abs(n["box"][0] - (g[0] + edge + gap[0])) <= 1.5, st
            (c,) = _by_titles(st, "A by caption")
            assert abs(c["box"][2] - (g[2] - edge - gap[1])) <= 1.5, st

    def test_a_title_outside_by_is_spanned_on_each_panel(self, mode):
        for i, st in enumerate(_by(mode, {"by": "foreign",
                                          "title": '"A panel title", span'})):
            ts = _by_titles(st, "A panel title")
            assert len(ts) == 2, st
            g = st["grid"]
            e = 0.035 * min(g[2] - g[0], g[3] - g[1])
            for t in ts:
                # Flipped (WP-32, BUGS.md "A spanned panel title sat left
                # of twoway's: dash's panel ended at its frame"): twoway's
                # panel graph runs from its axis labels to the graph
                # margin past its plot region on the right (measured
                # 19oct2026: panel 1's title at 1346.8 of 5400, centred
                # on 226.8 .. 2353.4 + 113.4; panel 2's at 3428.5 on
                # 2580.2 .. 4163.4 + 113.4).
                # Flipped again (WP-32, BUGS.md "A spanned panel title's
                # box started at the panel's canvas, not left of its y
                # labels"): twoway's panel graph starts 1.5 units of the
                # graph's smaller side left of the y labels (measured
                # 19oct2026: 48.2 of 3240 and 42.9 of 2880, whatever the
                # labels' width), and at the plot region on a panel with
                # no y axis.
                f = t["frame"]
                left = f[0] if t["yaxis"] is None else \
                    t["yaxis"] - 0.015 * min(g[2] - g[0], g[3] - g[1])
                assert abs(_centre(t["box"])[0]
                           - (left + f[1] + e) / 2.0) <= 1.5, t
            # Flipped (WP-32): panel 1's y labels and the margin past its
            # frame nearly cancel here, so the move is read on panel 2,
            # which has no y axis: at full width its title moves right of
            # its frame's centre, as twoway's does (3428.5 against 3371.8).
            second = max(ts, key=lambda t: t["canvas"][0])
            if i == 0:
                assert _centre(second["box"])[0] - (
                    second["frame"][0] + second["frame"][1]) / 2.0 > 5, \
                    second


#: by()'s title, subtitle, note and caption at the corner clocks 11, 1, 5
#: and 7 (by_text_truth.json bp40-bp63, scripts/extract_by_text_truth.do).
_CORNER_PROBES = ("bp40", "bp42", "bp43", "bp45", "bp46", "bp48", "bp49",
                  "bp51", "bp52", "bp54", "bp55", "bp57", "bp58", "bp60",
                  "bp61", "bp63")


def _anchored_edge(box, anchor):
    """The x of *box*'s edge an SVG text-anchor names (start: left, end:
    right, middle: its centre)."""
    return {"end": box[2], "middle": (box[0] + box[2]) / 2.0}.get(
        anchor, box[0])


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestByTitlesAtPosition:
    """WP-33 BY-24 (D-33-12.g): by(foreign, <text>("X", position(c))) at
    the corner clocks puts the text's anchored edge where twoway's SVG
    does, as a fraction of the graph's width (twoway: its x over the
    canvas width; dash: the text's box edge over the figure root's), within
    0.02; a difference is a BY_POSITION_KNOWN "<probe>:offset" row."""

    def test_the_corner_clocks(self, mode):
        res = {}
        for pid in _CORNER_PROBES:
            p = tbt._truth()["probes"][pid]
            (x,) = [t for t in p["svg"] if t["text"] == "X"]
            want = x["x"] / p["canvas"]
            spec = tbt._probe_spec(p)
            spec["build_options"]["scheme"] = \
                spec["build_options"]["scheme"] or "stcolor"
            st = kb._measure(mode, spec, _BY_JS)[1400]["wide"]
            g = st["grid"]
            boxes = _by_titles(st, "X")
            if len(boxes) != 1:
                res[pid + ":offset"] = "dash draws %d texts X" % len(boxes)
                continue
            got = (_anchored_edge(boxes[0]["box"], x["anchor"]) - g[0]) / \
                (g[2] - g[0])
            res[pid + ":offset"] = None if abs(got - want) <= 0.02 else \
                "anchored (%s) edge at %.3f of the width, twoway %.3f" % (
                    x["anchor"], got, want)
        assert tbt.known_problems(
            res, tbt._known("offset"), "by_position",
            deliberate=tbt.BY_POSITION_DELIBERATE) == []


def _panels(st):
    """The panels plus their axes, within the graph region: the panels'
    union less nothing past the grid's margin graph sides (stcolor 3.5% of
    min(width, height))."""
    g, p = st["grid"], st["panels"]
    e = 0.035 * min(g[2] - g[0], g[3] - g[1])
    return [max(p[0], g[0] + e), max(p[1], g[1] + e),
            min(p[2], g[2] - e), min(p[3], g[3] - e)]


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestByLegendWithoutSpan:
    """BUGS.md "Without span by()'s legend was placed on its cell, not on
    the panels".  Measured 19oct2026 (StataNow 19.5, stcolor, SVG of
    ``twoway (scatter price weight) (scatter mpg weight), ylabel(,
    format(%15.2fc)) ytitle("Price") by(foreign, legend(pos(#)))``):
    without span twoway places by()'s legend on the panels plus their axes
    -- pos(6) centred at x 2756.3 of 5400, the shared x title's centre
    (2700 without the y title), pos(3) at y 1499.3, the shared y title's
    centre, pos(7) at 264.8, the panels' left (226.0) plus 38.8, pos(2)
    and pos(4) at their top and bottom less 38.8."""

    def test_6_oclock_is_centred_on_the_panels(self, mode):
        for st in _by(mode, {"by": "foreign, legend(pos(6))"}):
            p, lg = _panels(st), _by_legend(st)
            assert abs(_centre(lg)[0] - (p[0] + p[2]) / 2.0) <= 1.5, st

    def test_3_oclock_is_centred_on_the_panels_height(self, mode):
        for st in _by(mode, {"by": "foreign, legend(pos(3))"}):
            p, lg = _panels(st), _by_legend(st)
            assert abs(_centre(lg)[1] - (p[1] + p[3]) / 2.0) <= 1.5, st
            assert lg[0] >= p[2], st

    def test_a_corner_is_at_the_panels_end(self, mode):
        for st in _by(mode, {"by": "foreign, legend(pos(7))"}):
            p, lg = _panels(st), _by_legend(st)
            # Flipped (D66): the margin is 5 px times the width scale.
            k = _k(st["grid"][2] - st["grid"][0])
            assert abs(lg[0] - (p[0] + _LM * k)) <= 1.5, st
        for st in _by(mode, {"by": "foreign, legend(pos(4))"}):
            p, lg = _panels(st), _by_legend(st)
            k = _k(st["grid"][2] - st["grid"][0])
            assert abs(lg[3] - (p[3] - _LM * k)) <= 1.5, st


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestByTitlesWithoutSpan:
    """BUGS.md "Without span by()'s title, note and caption were placed on
    their cell, not on the panels".  Measured 19oct2026 (StataNow 19.5,
    stcolor, the same graph with ``ytitle("Price") by(foreign,
    legend(pos(3)) title("Title T") subtitle("Sub S") note("Note N")
    caption("Cap C", pos(5)))``): without span by()'s own boxes are placed
    on the panels plus their axes -- the title and subtitle centred at
    2251.3 of 5400, the x title's centre, the note at 245.4, the panels'
    left 226.0 plus 19.4, the caption ending at 4257.4, their right 4276.8
    less 19.4, where the graph region runs from 113.4 to 5286.6."""

    def test_each_box_is_placed_on_the_panels(self, mode):
        by = ('foreign, legend(pos(3)) title("A by title") '
              'note("A by note") caption("A by caption", pos(5))')
        for st in _by(mode, {"by": by}):
            p = _panels(st)
            g = st["grid"]
            # The panels are off the grid's centre: placing on the cell
            # would show here.
            assert abs((p[0] + p[2]) / 2.0 - (g[0] + g[2]) / 2.0) > 30
            (t,) = _by_titles(st, "A by title")
            assert abs(_centre(t["box"])[0] - (p[0] + p[2]) / 2.0) <= 1.5
            # Flipped (WP-32, BUGS.md "A by() note or caption sat at the
            # panels' end without its margin"): the note and caption keep
            # their text box's margin (stcolor's vsmall, 0.6 of the
            # graph's smaller side: twoway's 19.4 of 3240) inside the
            # panels' ends, as twoway places them.
            mg = 0.006 * min(g[2] - g[0], g[3] - g[1])
            (n,) = _by_titles(st, "A by note")
            assert abs(n["box"][0] - (p[0] + mg)) <= 1.0, st
            (c,) = _by_titles(st, "A by caption")
            assert abs(c["box"][2] - (p[2] - mg)) <= 1.0, st


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestByPanelsFillTheirRow:
    """BUGS.md "A by() panel row was taller than its panels".  twoway
    centres the shared y title on the panels (measured 19oct2026, stcolor,
    ``ytitle("Price") by(foreign, legend(pos(3)))``: the y title at y
    1499.34 of 3240, the panels' box 113.4 .. 2885.3), the x title right
    under them.  dash's panel kept its proportion's height in the grid's
    row (1.2 times its width, 807 px at 1400) while the panel itself was
    held to 560 px, so the row ran 247 px past the panels; and the title
    cells' frames were aligned with the panels' frames, so each title was
    centred on the panels' plot regions, not on the panels."""

    @pytest.mark.parametrize("width", (1400, 1000, 760))
    def test_the_y_title_is_centred_on_the_panels(self, mode, width):
        spec = bk._spec([bk._graph("g1", bk._TWO, {
            "by": "foreign, legend(pos(3))", "ytitle": '"Price"'},
            title=False)], scheme="stcolor")
        got = kb._measure(mode, spec, _BY_JS, (width,))[width]
        st = got["wide"]
        p = st["panels"]
        (yt,) = [b for b in st["boxes"] if b["type"] == "Title"
                 and b["cell"] == "dash_by_ytitle"]
        assert abs(_centre(yt["box"])[1] - (p[1] + p[3]) / 2.0) <= 1.5, st
        (xt,) = [b for b in st["boxes"] if b["type"] == "Title"
                 and b["cell"] == "dash_by_xtitle"]
        # The x title's row starts right under the panels (the grid's
        # spacing apart), its text centred on them as twoway's is (2251.29
        # of 5400, the panels' box 226.0 .. 4276.8).
        assert 0 <= xt["canvas"][1] - p[3] <= 30, st
        assert abs(_centre(xt["box"])[0] - (p[0] + p[2]) / 2.0) <= 1.5, st


def _by_spec(mode, go, plots=None):
    spec = bk._spec([bk._graph("g1", plots or bk._TWO, go, title=False)],
                    scheme="stcolor")
    got = kb._measure(mode, spec, _BY_JS)[1400]
    return got["wide"], got["narrow"]


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestByLegendInAHole:
    """BUGS.md "by()'s legend in an at() hole sat at its cell's top left
    and squeezed the panel above it".  Measured 19oct2026 (StataNow 19.5,
    stcolor, SVG of ``twoway (scatter price weight) (scatter mpg weight),
    ylabel(, format(%15.2fc)) by(rep78, legend(at(6) [pos(#)]))``): twoway
    places the legend in the hole's cell at its position's compass --
    pos(0) centred (x 4509.7, the column's plot region centre, on the cell
    3732.8 .. 5286.6; y 2192.2 on 1499.4 .. 2885.3), the default pos(3) at
    the cell's right less its margin (5255.6) and centred on its height,
    pos(2) at its top right (1530.4) -- and the panel above the hole is as
    wide as the others (1327.0 of 5400 each)."""

    @pytest.mark.parametrize("pos,where", (("pos(0)", "c"), ("", "r"),
                                           ("pos(2)", "tr")))
    def test_the_legend_sits_at_its_compass_in_the_hole(self, mode, pos,
                                                        where):
        for st in _by_spec(mode, {"by": "rep78, legend(at(6) %s)" % pos}):
            (lg,) = [b for b in st["boxes"] if b["type"] == "Legend"
                     and b["cell"] == "dash_by_legend"]
            box, c = lg["box"], lg["canvas"]
            # Flipped (D66): the margin is 5 px times the width scale.
            # A key in an at() hole is at by()'s size multiplier too
            # (0.8 for five panels and a hole, _dash_by_size_mult).
            mg = _LM * _k(st["grid"][2] - st["grid"][0]) * 0.8
            cx = (c[0] + c[2]) / 2.0
            cy = (c[1] + c[3]) / 2.0
            if where == "c":
                assert abs(_centre(box)[0] - cx) <= 1.5, st
                assert abs(_centre(box)[1] - cy) <= 1.5, st
            if where == "r":
                assert abs(box[2] - (c[2] - mg)) <= 1.5, st
                assert abs(_centre(box)[1] - cy) <= 1.5, st
            if where == "tr":
                assert abs(box[2] - (c[2] - mg)) <= 1.5, st
                assert abs(box[1] - (c[1] + mg)) <= 1.5, st
            # The hole's cell is its column's width, and the panel above
            # it keeps its frame.  Flipped (WP-41 VF-6): "<= 20" let the
            # first column's frames be narrower by their y axis, which was
            # wrong because twoway draws every panel's plot region equally
            # wide (by_layout_truth.json Y17); the y labels are a cell of
            # their own now.
            # Flipped (WP-45 GW-6): against the panel columns' right, as
            # the panels' box now reaches the stacking ruler past them.
            assert abs(c[2] - st["pright"]) <= 1.5, st
            assert c[2] - c[0] > 300, st
            f = st["pframes"]
            assert max(f) - min(f) <= 2, st


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestByLegendRing0:
    """BUGS.md "by()'s legend(ring(0)) was placed on its cell, not on the
    panels".  Measured 19oct2026 (StataNow 19.5, stcolor, SVG of the same
    graph with ``by(foreign, legend(ring(0) pos(#)))``): ring(0) puts the
    legend between the panels and the x title (5, 6, 1) or beside them
    (9, 3), along its side exactly where it sits without ring(0) -- pos(6)
    centred at 2700 of 5400, pos(5) ending at 5247.8 (the panels' right
    5286.6 less 38.8), pos(9) at y 1499.3 of 3240, the panels' middle."""

    def test_6_oclock_is_centred_on_the_panels(self, mode):
        for st in _by_spec(mode, {"by": "foreign, legend(ring(0) pos(6))"}):
            p, lg = _panels(st), _by_legend(st)
            assert abs(_centre(lg)[0] - (p[0] + p[2]) / 2.0) <= 1.5, st

    def test_5_oclock_ends_at_the_panels_right(self, mode):
        for st in _by_spec(mode, {"by": "foreign, legend(ring(0) pos(5))"}):
            p, lg = _panels(st), _by_legend(st)
            # Flipped (D66): the margin is 5 px times the width scale.
            k = _k(st["grid"][2] - st["grid"][0])
            assert abs(lg[2] - (p[2] - _LM * k)) <= 1.5, st

    def test_9_oclock_is_centred_on_the_panels_height(self, mode):
        for st in _by_spec(mode, {"by": "foreign, legend(ring(0) pos(9))"}):
            p, lg = _panels(st), _by_legend(st)
            assert abs(_centre(lg)[1] - (p[1] + p[3]) / 2.0) <= 1.5, st


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestByColourKey:
    """BUGS.md "by()'s colour key ran past the panels' foot".  Measured
    19oct2026 (StataNow 19.5, stcolor, SVG of ``twoway scatter price
    weight, colorvar(mpg) by(foreign, clegend(on))``): at its default 3
    o'clock the key is centred on the panels' height, its title at y
    1499.34 of 3240 as the y title.  dash's key cell aligned its frame
    with the panels' frames, so the key started at their plot regions'
    top and ran 17 px past the panels' foot."""

    def test_the_key_is_centred_on_the_panels_height(self, mode):
        for st in _by_spec(mode, {"by": "foreign, clegend(on)",
                                  "ytitle": '"Price"'},
                           plots=[bk._p("scatter", colorvar="mpg")]):
            p = st["panels"]
            (key,) = [b for b in st["boxes"] if b["type"] == "ColorBar"
                      and b["cell"] == "dash_by_clegend"]
            k = key["box"]
            assert abs(_centre(k)[1] - (p[1] + p[3]) / 2.0) <= 1.5, st
            assert k[3] <= p[3] + 0.5, st

    @pytest.mark.parametrize("go", ({}, {"xsize": "5", "ysize": "5"},
                                    {"xsize": "4", "ysize": "6"}))
    def test_the_key_is_the_panels_box_less_its_gap(self, mode, go):
        """BUGS.md "by()'s colour key at 3 o'clock ran the panels' whole
        height".  Measured 19oct2026 (StataNow 19.5, stcolor, SVG of the
        same graph with ytitle("Price") at 7.5x4.5, 5x5, 8x4 and 4x6): at
        3 o'clock twoway's key is the panels' box less 0.094 of the
        graph's smaller side (2467.3 of a 2771.9 box at 3240; 2741.4 of
        3079.8 at 3600; 2193.1 of 2463.8 and 3633.2 of 3904.0 at 2880),
        centred on it."""
        for st in _by_spec(mode, dict(go, by="foreign, clegend(on)",
                                      ytitle='"Price"'),
                           plots=[bk._p("scatter", colorvar="mpg")]):
            p, g = st["panels"], st["grid"]
            u = min(g[2] - g[0], g[3] - g[1]) / 100.0
            bar = _key(st)["bar"]
            assert abs((bar[3] - bar[1]) - (p[3] - p[1] - 9.4 * u)) <= 1.5, \
                (bar, p, u)
            assert abs(_centre(bar)[1] - (p[1] + p[3]) / 2.0) <= 1.5, \
                (bar, p)



def _key(st):
    (k,) = [b for b in st["boxes"] if b["type"] == "ColorBar"
            and b["cell"] == "dash_by_clegend"]
    return k


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestByColourKeyUpright:
    """BUGS.md "by(, clegend(pos(6))) drew the colour key across the graph,
    where twoway draws it upright".  Measured 19oct2026 (StataNow 19.5,
    stcolor, SVG of ``twoway scatter price weight, colorvar(mpg)
    by(foreign|rep78, clegend(on pos(6|12)))`` at xsize x ysize 7.5x4.5,
    5x5, 8x4 and 4x6): twoway draws the key upright at 6 and 12 o'clock,
    its axis 1081.4 of 3240 long (1201.5 of 3600, 961.2 of 2880, 1681.2 of
    4320): half the graph's height less 0.1662 of its smaller side, the
    same for two and five panels."""

    @pytest.mark.parametrize("go,k", (
        ({}, (0.5 - 0.1662) * 4.5 / 7.5),
        ({"xsize": "5", "ysize": "5"}, 0.5 - 0.1662),
        ({"xsize": "4", "ysize": "6"}, 0.5 * 6 / 4 - 0.1662)))
    def test_the_key_is_upright_at_twoways_length(self, mode, go, k):
        for st in _by_spec(mode, dict(go, by="foreign, clegend(on pos(6))"),
                           plots=[bk._p("scatter", colorvar="mpg")]):
            key = _key(st)
            assert key["orient"] == "vertical", st
            gw = st["grid"][2] - st["grid"][0]
            assert abs(key["len"] - k * gw) <= 1.5, (key, k * gw)
            bar = key["bar"]
            assert abs(bar[3] - bar[1] - k * gw) <= 1.5, (key, k * gw)
            b, c = key["key"], key["canvas"]
            # Upright, inside its cell, centred on it.
            assert b[3] - b[1] > b[2] - b[0], st
            assert c[1] - 0.5 <= b[1] and b[3] <= c[3] + 0.5, st
            assert abs(_centre(b)[0] - (c[0] + c[2]) / 2.0) <= 1.5, st


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestByColourKeyInAHole:
    """BUGS.md "by()'s colour key in an at() hole filled its cell's left
    edge".  Measured 19oct2026 (StataNow 19.5, stcolor, SVG of
    ``twoway scatter price weight, colorvar(mpg) by(rep78, clegend(on
    at(6) [pos(#)]))`` at 7.5x4.5, 5x5, 8x4, 4x6 and cols(2)): twoway draws
    the key upright in the hole, from 1.455 units (of the graph's smaller
    side) above its row's plot regions to 2.44 below them (default 1621.2
    .. 2763.4 for plot regions 1668.3 .. 2684.3), centred across the hole
    at pos(0), at its left at pos(9), at its right at the default pos(3)
    and at pos(2), whose height is the same."""

    @pytest.mark.parametrize("pos,where", (("pos(0)", "c"), ("", "r"),
                                           ("pos(2)", "r"), ("pos(9)", "l")))
    def test_the_key_spans_its_rows_plot_regions(self, mode, pos, where):
        wide, narrow = _by_spec(mode,
                                {"by": "rep78, clegend(on at(6) %s)" % pos},
                                plots=[bk._p("scatter", colorvar="mpg")])
        # Stacked (one column at 700 px), the key keeps a cell of its own
        # and stays inside it.
        key = _key(narrow)
        assert key["canvas"][3] - key["canvas"][1] >= 150, narrow
        assert key["canvas"][1] - 0.5 <= key["bar"][1] \
            and key["bar"][3] <= key["canvas"][3] + 0.5, narrow
        for st in (wide,):
            key = _key(st)
            b, c, bar = key["key"], key["canvas"], key["bar"]
            g = st["grid"]
            u = min(g[2] - g[0], g[3] - g[1]) / 100.0
            (row,) = {tuple(r) for r in st["prows"]
                      if c[1] - 1 <= r[0] <= c[3]}
            assert key["orient"] == "vertical", st
            assert abs(key["len"] - (row[1] - row[0] + 3.895 * u)) <= 1.5, \
                (key, row, u)
            assert abs(bar[1] - (row[0] - 1.455 * u)) <= 1.5, (bar, row, u)
            assert abs(bar[3] - (row[1] + 2.44 * u)) <= 1.5, (bar, row, u)
            if where == "c":
                assert abs(_centre(b)[0] - (c[0] + c[2]) / 2.0) <= 1.5, st
            elif where == "r":
                assert abs(b[2] - (c[2] - 5)) <= 1.5, st
            else:
                assert abs(b[0] - (c[0] + 5)) <= 1.5, st


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestByPanelBoxMargin:
    """BUGS.md "A spanned note or caption on a by() panel sat at the panel
    box's end without its margin".  Measured 19oct2026 (StataNow 19.5,
    stcolor, SVG of ``twoway (scatter price weight) (scatter mpg weight),
    by(foreign|rep78, legend(off)) note("Panel N", span) caption("Panel C",
    span pos(5))``): each panel's spanned note starts, and its caption
    ends, its text box's margin inside the panel's box -- 16.5 of 3240 with
    two panels, 15.5 with five: stcolor's 0.6 units at by()'s size
    multiplier (.85, .8)."""

    def test_the_note_and_caption_keep_their_margin(self, mode):
        for st in _by_spec(mode, {"by": "foreign, legend(off)",
                                  "note": '"Panel N", span',
                                  "caption": '"Panel C", span pos(5)'}):
            g = st["grid"]
            u = min(g[2] - g[0], g[3] - g[1]) / 100.0
            mg = 0.6 * 0.85 * u
            notes = _by_titles(st, "Panel N")
            caps = _by_titles(st, "Panel C")
            assert len(notes) == 2 and len(caps) == 2, st
            for n in notes:
                f = n["frame"]
                left = f[0] if n["yaxis"] is None else n["yaxis"] - 1.5 * u
                # Flipped (WP-32, BUGS.md "A first panel's spanned note
                # started at its canvas's edge, not 1 unit left of its y
                # labels"): 1.49 units left of the labels plus its margin,
                # the panel making room for it inside its canvas.
                assert abs(n["box"][0] - (left + mg)) <= 1.0, (n, mg)
                assert n["box"][0] >= n["canvas"][0] - 0.5, n
            for c in caps:
                f = c["frame"]
                assert abs(c["box"][2] - (f[1] + 3.5 * u - mg)) <= 1.0, \
                    (c, mg)


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestByPanelBoxUnderOtherSchemes:
    """BUGS.md "A spanned panel title's box reached the graph margin past
    the panel, where twoway reaches by()'s panel margin".  Measured
    19oct2026 (StataNow 19.5, SVG of the panel-title graph with y labels
    "0" and "00000000" under s2color, s1color, s1mono and economist):
    twoway's panel box reaches its plot region's right plus the scheme's
    ``margin by_indiv`` (s2 and s1 families small, 1.2 units: 34.6 of 2880;
    stcolor's allsides-ms 3.5 on the right: 113.4 of 3240), and starts 1.49
    units left of the y labels in every family (42.9 of 2880, 48.2 of
    3240); economist, with no y labels left of the plot, starts at it."""

    @pytest.mark.parametrize("scheme,right", (("s2color", 1.2),
                                              ("s1mono", 1.2),
                                              ("stcolor", 3.5)))
    def test_the_box_reaches_bys_panel_margin(self, mode, scheme, right):
        spec = bk._spec([bk._graph("g1", bk._TWO, {
            "by": "foreign, legend(off)", "title": '"A panel title", span'},
            title=False)], scheme=scheme)
        got = kb._measure(mode, spec, _BY_JS)[1400]
        for st in (got["wide"], got["narrow"]):
            g = st["grid"]
            u = min(g[2] - g[0], g[3] - g[1]) / 100.0
            ts = _by_titles(st, "A panel title")
            assert len(ts) == 2, st
            for t in ts:
                f = t["frame"]
                left = f[0] if t["yaxis"] is None else t["yaxis"] - 1.5 * u
                assert abs(_centre(t["box"])[0]
                           - (left + f[1] + right * u) / 2.0) <= 1.5, \
                    (scheme, t, u)


def _dkey(st):
    (k,) = [b for b in st["boxes"] if b["type"] == "Legend"
            and b["cell"] == "dash_by_clegend"]
    return k


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestByDiscreteColourKey:
    """BUGS.md "by()'s discrete colour key was as long as its keys, not
    twoway's key".  Measured 19oct2026 (StataNow 19.5, stcolor, SVG of
    ``twoway scatter price weight, colorvar(rep78) colordiscrete
    ytitle("Price") by(foreign|rep78, clegend(on [pos(6)|at(6) pos(0)]))``
    at 7.5x4.5 and 5x5): twoway draws the discrete key as the continuous
    one -- the same upright strip, its levels' labels spaced along it --
    2467.3 of 3240 beside the panels, 1081.4 at 6 o'clock (1201.5 at 5x5),
    1142.2 in the hole, centred."""

    def test_beside_the_panels(self, mode):
        for st in _by_spec(mode, {"by": "foreign, clegend(on)",
                                  "ytitle": '"Price"'},
                           plots=[bk._p("scatter", colorvar="rep78",
                                        colordiscrete="yes")]):
            p, g = st["panels"], st["grid"]
            u = min(g[2] - g[0], g[3] - g[1]) / 100.0
            b = _dkey(st)["box"]
            assert abs((b[3] - b[1]) - (p[3] - p[1] - 9.4 * u)) <= 2.5, \
                (b, p, u)
            assert abs(_centre(b)[1] - (p[1] + p[3]) / 2.0) <= 1.5, (b, p)

    def test_under_the_panels(self, mode):
        wide, narrow = _by_spec(mode, {"by": "foreign, clegend(on pos(6))",
                                       "ytitle": '"Price"'},
                                plots=[bk._p("scatter", colorvar="rep78",
                                             colordiscrete="yes")])
        k = (0.5 - 0.1662) * 4.5 / 7.5
        g, b = wide["grid"], _dkey(wide)["box"]
        # Whole px of spacing between five keys: within 2.5 px.
        assert abs((b[3] - b[1]) - k * (g[2] - g[0])) <= 2.5, (b, g)
        # Narrowed, the keys cannot close up further than touching.
        g, b = narrow["grid"], _dkey(narrow)["box"]
        assert b[3] - b[1] >= k * (g[2] - g[0]) - 2.5, (b, g)

    def test_in_a_hole(self, mode):
        # Panel 1 (rep78 1) holds one level: its key takes the length up
        # in its padding.
        st = _by_spec(mode, {"by": "rep78, clegend(on at(6) pos(0))"},
                      plots=[bk._p("scatter", colorvar="rep78",
                                   colordiscrete="yes")])[0]
        lg = _dkey(st)
        b, c, g = lg["box"], lg["canvas"], st["grid"]
        u = min(g[2] - g[0], g[3] - g[1]) / 100.0
        (row,) = {tuple(r) for r in st["prows"] if c[1] - 1 <= r[0] <= c[3]}
        assert abs((b[3] - b[1]) - (row[1] - row[0] + 3.895 * u)) <= 2.5, \
            (b, row, u)
        assert abs(_centre(b)[0] - (c[0] + c[2]) / 2.0) <= 1.5, (b, c)
        f = st["pframes"]
        assert max(f) - min(f) <= 20, st


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestByGraphKeepsItsSize:
    """BUGS.md "A by() legend, key or text row was added under panels that
    kept their proportion, where twoway shortens the panels".  Measured
    19oct2026 (StataNow 19.5, stcolor, SVG of ``twoway (scatter price
    weight) (scatter mpg weight), ylabel(, format(%15.2fc)) by(foreign,
    ...)`` and ``twoway scatter price weight, colorvar(mpg) by(foreign,
    clegend(on ...))``, 5400 x 3240 throughout): the graph keeps its size
    and the panels give up what a row takes -- plot regions 2383.6 tall
    with no row (legend(off), or a legend or key at 3), 1938.8 with the
    legend at 6 or 12 (ring(0) too), 2036.0 with a title, note and
    caption, 1591.2 with both, 997.8 with the colour key at 6 or 12."""

    @pytest.mark.parametrize("width", (1000, 760))
    @pytest.mark.parametrize("go,plots", (
        ({"by": "foreign, legend(off)"}, None),
        ({"by": "foreign, legend(pos(6))"}, None),
        ({"by": 'foreign, legend(pos(6)) title("T") note("N") '
                'caption("C", pos(5))'}, None),
        ({"by": "foreign, clegend(on pos(6))"}, "key")))
    def test_the_grid_keeps_the_graphs_ratio(self, mode, width, go, plots):
        plots = [bk._p("scatter", colorvar="mpg")] if plots else bk._TWO
        spec = bk._spec([bk._graph("g1", plots, go, title=False)],
                        scheme="stcolor")
        st = kb._measure(mode, spec, _BY_JS, (width,))[width]["wide"]
        g = st["grid"]
        assert abs((g[3] - g[1]) - (g[2] - g[0]) * 4.5 / 7.5) <= 2.5, \
            (go, g, st["panels"])


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestByHoleReserved:
    """WP-41 BY-3 (by_chrome_truth.json K02): ``twoway (scatter mpg
    weight) (lfit mpg weight), by(foreign, legend(off at(1)))`` keeps
    cell 1 empty: Domestic top right, Foreign bottom left of a 2 x 2
    grid."""

    def test_grid_cells(self, mode):
        st = _by_spec(mode, {"by": "foreign, legend(off at(1))"})[0]
        cells = st["pcells"]
        assert len(cells) == 2, st
        (tx, ty), (bx, by) = sorted(cells, key=lambda c: c[1])
        # One panel top right (cell 2), the other bottom left (cell 3).
        assert by > ty + 100 and tx > bx + 100, cells


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestByPlegend:
    """WP-41 BY-14 (by_chrome_truth.json K08): ``twoway scatter mpg
    weight, colorvar(rep78) colordiscrete coloruseplegend by(foreign,
    plegend(on))`` draws one plot legend of the colour keys right of the
    panels."""

    def test_drawn_right(self, mode):
        st = _by_spec(mode, {"by": "foreign, plegend(on)"},
                      plots=[bk._p("scatter", colorvar="rep78",
                                   colordiscrete="yes",
                                   coloruseplegend="coloruseplegend")])[0]
        (lg,) = [b for b in st["boxes"] if b["type"] == "Legend"
                 and b["cell"] == "dash_by_plegend"]
        assert lg["box"][0] >= st["panels"][2] - 1.5, (lg, st["panels"])
