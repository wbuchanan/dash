"""
test_sizing_browser.py -- the figure geometry BokehJS draws, in headless
Chrome (WP-34 VF-3; the base WP-45's 45-04 extends, DECISIONS A-1).

test_sizing.py reads the models; here Chrome lays both modes' pages out.
aspectratio() with xsize()/ysize() draws the figure at the xsize()/ysize()
box (96 px an inch) with a plot region of ratio # inside it.  Before WP-34
the figure kept Bokeh's default height, clamped by max_height, and
aspectratio(2) xsize(8) ysize(4) drew a 0 px wide frame.  Each probe is
read at 1400 px and at 375 px, alone and in a two-cell layout(): the host
is the box (a narrow cell scrolls sideways rather than shrinking it), the
frame is above 0 px and at ratio #, and placement(e) puts the frame
against the host's right edge less the right axis's room.

:func:`_frame_probe` is the reusable reader: it returns, per width, each
named figure's ``[host_w, host_h, frame_w, frame_h, frame_x0, frame_y0]``.
Without Chrome these tests skip, as test_by_axes_keys_browser.py's do.
"""
import json
import os
import sys
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import responsive_probe  # noqa: E402
import test_sizing as ts  # noqa: E402

if responsive_probe.find_chrome() is None:
    pytest.skip("headless Chrome is not installed (set DASH_CHROME); "
                "the browser check is skipped", allow_module_level=True)

# Headless Chrome: the release tier (WP-30 D), never the batch gate.
pytestmark = pytest.mark.release

#: Every Plot view whose model's name or id is in NAMES: its host element's
#: size and its frame's box, posted once the page has laid out.
_FRAME_JS = r"""
<script>
addEventListener('load', () => setTimeout(() => {
  const names = %s;
  const out = {};
  const visit = (v) => {
    if (!v) return;
    if (v.frame && v.model) {
      const key = names.includes(v.model.name) ? v.model.name
                : (names.includes(v.model.id) ? v.model.id : null);
      if (key !== null) {
        const f = v.frame.bbox;
        out[key] = [v.el.offsetWidth, v.el.offsetHeight, f.width, f.height,
                    f.x0, f.y0];
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


def _frame_probe(page, name, widths=(1400, 375)):
    """``{width: [host_w, host_h, frame_w, frame_h, frame_x0, frame_y0]}``
    of the figure named *name* (its model name or id) on *page*, laid out
    by headless Chrome at each of *widths*; *name* a list or tuple gives
    ``{width: [one such list per name]}``."""
    names = list(name) if isinstance(name, (list, tuple)) else [name]
    mp = pytest.MonkeyPatch()
    mp.setattr(responsive_probe, "PROBE_JS", _FRAME_JS % json.dumps(names))
    try:
        got = responsive_probe.measure_many(page, widths)
    finally:
        mp.undo()
    out = {}
    for w, rec in got.items():
        rows = [rec["out"].get(n) for n in names]
        assert all(rows), (w, names, rec)
        out[w] = rows if isinstance(name, (list, tuple)) else rows[0]
    return out


def _page(mode, wd, gos, layout="auto"):
    """``(html, figures)``: *mode*'s page, written under *wd*, of one
    scatter per graph option dict in *gos* (named g1, g2, ...), and its
    figures."""
    from bokeh.plotting import figure as _fcls
    tag = next(ts._SEQ)
    spec = ts._spec([ts._sc()], gos[0])
    graphs = []
    for i, go in enumerate(gos):
        # No title unless the probe gives one, as the twoway commands
        # measured ([B] section 4.6); the titled probes are D55's.
        go = dict({"title": ""}, **go)
        g = json.loads(json.dumps(spec["graphs"][0]))
        g["graph_options"] = dict(g["graph_options"], name="g%d" % (i + 1),
                                  **go)
        graphs.append(g)
    spec["graphs"] = graphs
    spec["build_options"]["registry"] = " ".join(
        "g%d" % (i + 1) for i in range(len(gos)))
    spec["build_options"]["layout"] = layout
    sp = os.path.join(wd, "s%d.json" % tag)
    dp = os.path.join(wd, "d%d.json" % tag)
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    with open(dp, "w", encoding="utf-8") as fh:
        json.dump(ts.make_data_json(ts._DF), fh)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if mode == "saved":
            r = ts.dr.DashRenderer(sp, dp)
            html = r.render()
            models = r._last_layout_root.references()
        else:
            from bokeh.document import Document
            from bokeh.embed import file_html
            from bokeh.resources import INLINE
            ap = os.path.join(wd, "a%d.py" % tag)
            ts.dr.ServerAppBuilder(sp, dp).build(ap)
            mod = ts.load_app(ap, "_szb_app_%d" % tag, draw=False)
            doc = Document()
            mod.make_document(doc)
            html = file_html(doc, INLINE, "served")
            models = [m for root in doc.roots for m in root.references()]
    figs = [m for m in models if isinstance(m, _fcls)]
    assert len(figs) == len(gos), figs
    return html, figs


def _check(fig, rec, ar):
    hw, hh, fw, fh = rec[:4]
    w, h = fig._dash_frame_box
    assert abs(hw - w) <= 2 and abs(hh - h) <= 2, (rec, fig._dash_frame_box)
    assert fw > 0 and fh > 0, rec
    assert fh / fw == pytest.approx(ar, rel=0.01), rec


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestFixedFrameInChrome:
    def test_frame(self, mode, tmp_path):
        """Each probe, untitled and titled (D55), alone and, the same probe
        twice, in a two-cell layout(1 2), at 1400 and 375 px: host = box,
        frame above 0 px, at ratio #."""
        for go in ts._FIXED + ts._FIXED_TITLED:
            ar = float(go["aspectratio"])
            html, figs = _page(mode, tmp_path, [go])
            for w, rec in _frame_probe(html, figs[0].id).items():
                _check(figs[0], rec, ar)
            html, figs = _page(mode, tmp_path, [go, go], layout="1 2")
            got = _frame_probe(html, [f.id for f in figs])
            for w, recs in got.items():
                for fig, rec in zip(figs, recs):
                    _check(fig, rec, ar)

    def test_placement_e(self, mode, tmp_path):
        """placement(e): the frame's right edge is the host's right edge
        less the room estimated for the right axis."""
        html, figs = _page(mode, tmp_path, [{
            "aspectratio": "1", "aspectplacement": "e", "xsize": "8",
            "ysize": "4"}])
        f = figs[0]
        for w, rec in _frame_probe(html, f.id).items():
            _check(f, rec, 1.0)
            hw, _hh, fw, _fh, fx0, _fy0 = rec
            assert abs((fx0 + fw) - (hw - f._dash_frame_est["right"])) <= 2, \
                (w, rec, f._dash_frame_est)


#: Every Plot view's host size and frame box, and the innermost GridBox's
#: drawn size (a by() graph's array of panels), posted once the page has laid out.
_SHAPE_JS = r"""
<script>
addEventListener('load', () => setTimeout(() => {
  const plots = [];
  let grid = null, deep = -1, outer = null;
  const visit = (v, d) => {
    if (!v) return;
    if (v.frame && v.model) {
      const f = v.frame.bbox;
      plots.push([v.el.offsetWidth, v.el.offsetHeight, f.width, f.height]);
    }
    if (outer === null && v.model && v.model.type === "GridBox" && v.el) {
      const q = v.el.getBoundingClientRect();
      outer = [q.width, q.height];
    }
    if (d > deep && v.model && v.model.type === "GridBox" && v.el) {
      const r = v.el.getBoundingClientRect();
      grid = [r.width, r.height];
      deep = d;
    }
    for (const c of (v.child_views || [])) visit(c, d + 1);
  };
  for (const v of Object.values(Bokeh.index)) { if (!v.parent) visit(v, 0); }
  parent.postMessage('DASHPROBE' + JSON.stringify({W: innerWidth, plots,
                                                   grid, outer}), '*');
}, 3000));
</script>
"""


def _shape_probe(page, widths):
    mp = pytest.MonkeyPatch()
    mp.setattr(responsive_probe, "PROBE_JS", _SHAPE_JS)
    try:
        return responsive_probe.measure_many(page, widths)
    finally:
        mp.undo()


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestTheThreeCasesInChrome:
    """WP-45 VF-4 (DECISIONS A-1): a graph keeps twoway's shape at any
    width with no height band -- 7.5:4.5 under stcolor at 600, 1200 and
    1920 px, a by() graph's array too; aspectratio(1) alone draws a square
    plot region; by(foreign) xsize(8) ysize(4) is 768 x 384."""

    @staticmethod
    def _page(mode, go, tmp_path):
        """*mode*'s page of ``scatter mpg weight, <go>`` under stcolor."""
        import test_by_axes_keys as tbk
        from bokeh.document import Document
        from bokeh.embed import file_html
        from bokeh.resources import INLINE
        spec = tbk._spec([tbk._graph("g1", tbk._ONE, go, title=False)],
                         scheme="stcolor")
        tag = next(ts._SEQ)
        sp = os.path.join(str(tmp_path), "s%d.json" % tag)
        dp = os.path.join(str(tmp_path), "d%d.json" % tag)
        with open(sp, "w", encoding="utf-8") as fh:
            json.dump(spec, fh)
        with open(dp, "w", encoding="utf-8") as fh:
            json.dump(tbk.tg._data(), fh)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if mode == "saved":
                return ts.dr.DashRenderer(sp, dp).render()
            ap = os.path.join(str(tmp_path), "a%d.py" % tag)
            ts.dr.ServerAppBuilder(sp, dp).build(ap)
            mod = ts.load_app(ap, "_szs_app_%d" % tag, draw=False)
            doc = Document()
            mod.make_document(doc)
            return file_html(doc, INLINE, "served")

    def test_shape(self, mode, tmp_path):
        r = 7.5 / 4.5
        # The whole graph, its graph region's margin (WP-45 GW-6)
        # included: the page's grid.
        for go in ({}, {"by": "foreign"}):
            html = self._page(mode, go, tmp_path)
            for w, rec in _shape_probe(html, (600, 1200, 1920)).items():
                gw, gh = rec["outer"]
                assert gw / gh == pytest.approx(r, rel=0.01), (w, go, rec)

    def test_aspectratio_alone(self, mode, tmp_path):
        html = self._page(mode, {"aspectratio": "1"}, tmp_path)
        for w, rec in _shape_probe(html, (600, 1200)).items():
            hw, hh, fw, fh = rec["plots"][0]
            gw, gh = rec["outer"]
            assert gw / gh == pytest.approx(7.5 / 4.5, rel=0.01), (w, rec)
            assert abs(fw - fh) <= 2, (w, rec)

    def test_by_box(self, mode, tmp_path):
        html = self._page(mode, {"by": "foreign", "xsize": "8",
                                 "ysize": "4"}, tmp_path)
        for w, rec in _shape_probe(html, (1200,)).items():
            gw, gh = rec["grid"]
            assert gw == pytest.approx(768, rel=0.01), (w, rec)
            assert gh == pytest.approx(384, rel=0.01), (w, rec)



#: Flipped (BUGS.md "A graph's canvas ended before its own x axis, x title
#: and colour key labels"): the graph's top is its graph region box's
#: (GW-6's margin is a box round the figure now, not the figure's own
#: padding).
_PICTURE_JS = r"""
<script>
addEventListener('load', () => setTimeout(() => {
  const plots = [];
  const gbox = (v) => {
    for (let q = v; q != null; q = q.parent) {
      if (q.model && q.el && (q.model.tags || []).includes(
          'dash_graph_region')) return q.el;
    }
    return v.el;
  };
  const visit = (v) => {
    if (!v) return;
    if (v.frame && v.model) {
      const ax = (v.model.below || []).filter(
        (a) => a.major_label_text_font_size);
      plots.push([gbox(v).getBoundingClientRect().top,
                  ax.length ? ax[0].major_label_text_font_size : null]);
    }
    for (const c of (v.child_views || [])) visit(c);
  };
  for (const v of Object.values(Bokeh.index)) { if (!v.parent) visit(v); }
  parent.postMessage('DASHPROBE' + JSON.stringify({W: innerWidth, plots}),
                     '*');
}, 3000));
</script>
"""


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestOnePictureInChrome:
    """DECISIONS D66 (the maintainer's ruling of 01nov2026): at 1400 px a
    7.5-inch stcolor graph draws its 10-point tick labels at 10 x 1400 /
    720 x 4.5 / 4 pt (about 29 px, twoway's stcolor tick labels 11.26 pt
    on its 7.5 x 4.5 picture), and no toolbar pushes the graph down."""

    def test_tick_labels_and_top(self, mode, tmp_path):
        html = TestTheThreeCasesInChrome._page(mode, {}, tmp_path)
        mp = pytest.MonkeyPatch()
        mp.setattr(responsive_probe, "PROBE_JS", _PICTURE_JS)
        try:
            got = responsive_probe.measure_many(html, (1400, 720))
        finally:
            mp.undo()
        for w, rec in got.items():
            top, font = rec["plots"][0]
            assert top <= 1, (w, rec)
            assert float(font[:-2]) == pytest.approx(
                10.0 * w / 720.0 * 4.5 / 4.0, abs=0.02), (w, rec)


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestTheGraphMarginInChrome:
    """WP-45 GW-6: at 1400 x 840 a stcolor scatter's plot region starts
    3.5% of the 840 px side below the page's top (twoway: 113.4 of 3240
    SVG units, 29.4 px), and the graph is 840 px tall with its margin."""

    def test_top_and_height(self, mode, tmp_path):
        for go in ({}, {"by": "foreign"}):
            html = TestTheThreeCasesInChrome._page(mode, go, tmp_path)
            mp = pytest.MonkeyPatch()
            mp.setattr(responsive_probe, "PROBE_JS", _CANVAS_JS)
            try:
                rec = responsive_probe.measure_many(html, (1400,))[1400]
            finally:
                mp.undo()
            left = min(r[0] for r in rec["rows"])
            top = min(r[1] for r in rec["rows"])
            bottom = max(r[1] + r[3] for r in rec["rows"])
            m = 0.035 * 840
            # Flipped (WP-41 41-05): a by() array's first row starts its
            # by_indiv top margin (1.2 units, 10.1 px) under the graph
            # margin, as twoway's strips do (G_by_stcolor: 39.5 px).
            t = m + (0.012 * 840 if go else 0.0)
            assert abs(left - m) <= 2 and abs(top - t) <= 2, (go, rec)
            assert abs(bottom - (840 - m)) <= 3, (go, rec)
            assert rec["sh"] <= 841 or rec["sh"] == 1100, (go, rec)


#: Every canvas's box on the page (the graph drawn inside its margin).
_CANVAS_JS = r"""
<script>
addEventListener('load', () => setTimeout(() => {
  const rows = [];
  const walk = (root) => { for (const el of root.querySelectorAll('*')) {
    if (el.shadowRoot) walk(el.shadowRoot);
    if (el.tagName === 'CANVAS') { const r = el.getBoundingClientRect();
      if (r.width > 20 && r.height > 20) rows.push([r.left, r.top, r.width,
                                                   r.height]); } } };
  walk(document);
  parent.postMessage('DASHPROBE' + JSON.stringify({W: innerWidth, rows,
    sh: document.documentElement.scrollHeight}), '*');
}, 3500));
</script>
"""


#: Each plot's canvas size and the laid-out box of every visible axis and
#: colour key on it (tick labels and title included), in the plot's own
#: canvas px: BokehJS draws nothing of a part past its canvas.
_INSIDE_JS = r"""
<script>
addEventListener('load', () => setTimeout(() => {
  const plots = [];
  const visit = (v) => {
    if (!v) return;
    if (v.frame && v.renderer_views && v.canvas_view) {
      const c = v.canvas_view.bbox;
      const parts = [];
      for (const [m, rv] of v.renderer_views) {
        if (!m.visible || !rv.bbox) continue;
        if (!(String(m.type).endsWith('Axis') || m.type === 'ColorBar'))
          continue;
        const b = rv.bbox;
        if (!(b.width > 0) || !(b.height > 0)) continue;
        parts.push([m.type, m.axis_label || m.title || '',
                    b.x0, b.y0, b.x1, b.y1]);
      }
      plots.push({canvas: [c.width, c.height], parts});
    }
    for (const k of (v.child_views || [])) visit(k);
  };
  for (const v of Object.values(Bokeh.index)) { if (!v.parent) visit(v); }
  parent.postMessage('DASHPROBE' + JSON.stringify({W: innerWidth, plots}),
                     '*');
}, 3500));
</script>
"""


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestEveryLabelInsideInChrome:
    """BUGS.md "A graph's canvas ended before its own x axis, x title and
    colour key labels" (f74ea1b, WP-41 41.4): BokehJS laid a figure out in
    its whole box, GW-6's graph margin (its CSS padding) included, while
    its canvas is only what the padding leaves, so at 1100 px the bottom
    and right 47 px -- the x tick labels, the x title and the colour key's
    labels -- were cut.  Every axis's and colour key's box, titles
    included, lies inside its own canvas, as twoway draws them: a plain
    scatter, a colorvar() scatter and a by() graph."""

    @pytest.mark.parametrize("plots,go", [
        ("one", {}), ("colour", {}), ("one", {"by": "foreign"})],
        ids=["plain", "colorvar", "by"])
    def test_inside_the_canvas(self, plots, go, mode, tmp_path):
        import test_by_axes_keys as tbk
        p = tbk._ONE if plots == "one" else [
            tbk._p("scatter", colorvar="weight")]
        spec = tbk._spec([tbk._graph("g1", p, go, title=False)],
                         scheme="stcolor")
        tag = next(ts._SEQ)
        sp = os.path.join(str(tmp_path), "s%d.json" % tag)
        dp = os.path.join(str(tmp_path), "d%d.json" % tag)
        with open(sp, "w", encoding="utf-8") as fh:
            json.dump(spec, fh)
        with open(dp, "w", encoding="utf-8") as fh:
            json.dump(tbk.tg._data(), fh)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if mode == "saved":
                html = ts.dr.DashRenderer(sp, dp).render()
            else:
                from bokeh.document import Document
                from bokeh.embed import file_html
                from bokeh.resources import INLINE
                ap = os.path.join(str(tmp_path), "a%d.py" % tag)
                ts.dr.ServerAppBuilder(sp, dp).build(ap)
                mod = ts.load_app(ap, "_szi_app_%d" % tag, draw=False)
                doc = Document()
                mod.make_document(doc)
                html = file_html(doc, INLINE, "served")
        mp = pytest.MonkeyPatch()
        mp.setattr(responsive_probe, "PROBE_JS", _INSIDE_JS)
        try:
            rec = responsive_probe.measure_many(html, (1100,))[1100]
        finally:
            mp.undo()
        parts = [q for pl in rec["plots"] for q in pl["parts"]]
        kinds = {q[0] for q in parts}
        assert "LinearAxis" in kinds, rec
        if plots == "colour":
            # Flipped (WP-42 CV-3): dash's colour key was a ColorBar;
            # twoway draws swatches beside a z axis (CV-3): a key cell of
            # its own with its z axis (its title a Label beside it).
            assert len(rec["plots"]) == 2, rec
            assert [q for q in rec["plots"][1]["parts"]
                    if q[0] == "LinearAxis"], rec
        titles = {q[1] for q in parts if q[0] == "LinearAxis"}
        if not go:
            # The axis titles are the figure's own (by() draws them in
            # cells of their own).
            assert {"Weight (lbs.)", "Mileage (mpg)"} <= titles, rec
        for pl in rec["plots"]:
            cw, ch = pl["canvas"]
            for q in pl["parts"]:
                x0, y0, x1, y1 = q[2:]
                assert x0 >= -0.5 and y0 >= -0.5, (q, pl)
                assert x1 <= cw + 0.5 and y1 <= ch + 0.5, (q, pl)


#: The graph region box, the by() array (the deepest GridBox) and every
#: plot frame, in page px.
_FXY_JS = r"""
<script>
addEventListener('load', () => setTimeout(() => {
  const frames = []; let region = null, grid = null, deep = -1;
  const visit = (v, d) => {
    if (!v) return;
    if (v.model && v.el && region === null
        && (v.model.tags || []).includes('dash_graph_region')) {
      const q = v.el.getBoundingClientRect();
      region = [q.left, q.top, q.width, q.height];
    }
    if (v.model && v.el && v.model.type === 'GridBox' && d > deep) {
      const q = v.el.getBoundingClientRect();
      grid = [q.left, q.top, q.width, q.height]; deep = d;
    }
    if (v.frame && v.model && v.el) {
      const r = v.el.getBoundingClientRect(), f = v.frame.bbox;
      if (f.width > 20 && f.height > 20)
        frames.push([r.left + f.x0, r.top + f.y0, f.width, f.height]);
    }
    for (const c of (v.child_views || [])) visit(c, d + 1);
  };
  for (const v of Object.values(Bokeh.index)) { if (!v.parent) visit(v, 0); }
  parent.postMessage('DASHPROBE' + JSON.stringify({W: innerWidth, region,
                                                   grid, frames}), '*');
}, 3000));
</script>
"""


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestFxFyInChrome:
    """WP-45 VF-4 (VF-11, GW-20): at 1400 px a stcolor graph with
    fxsize(50) or fysize(50) keeps its 1400 x 840 size and draws the plot
    -- a by() graph's array -- in 50% of the 4.5-inch reference side, 420
    px, centred (figure_geometry_truth.json G_fx50, G_fy50, G_fx50_by,
    G_fy50_by: 1890..3510 of 5400 and 810..2430 of 3240 SVG units).
    Before: the box was 192 px at any width, and under by() fysize()
    shortened the whole graph with its array at the top."""

    @pytest.mark.parametrize("opt", ["fxsize", "fysize"])
    def test_by_array(self, opt, mode, tmp_path):
        html = TestTheThreeCasesInChrome._page(
            mode, {"by": "foreign", opt: "50"}, tmp_path)
        mp = pytest.MonkeyPatch()
        mp.setattr(responsive_probe, "PROBE_JS", _FXY_JS)
        try:
            rec = responsive_probe.measure_many(html, (1400,))[1400]
        finally:
            mp.undo()
        rl, rt, rw, rh = rec["region"]
        assert abs(rw - 1400) <= 2 and abs(rh - 840) <= 3, rec
        gl, gt, gw, gh = rec["grid"]
        panels = sorted(rec["frames"], key=lambda q: -q[2] * q[3])[:2]
        # The two panels side by side, as twoway's (a narrowed array does
        # not stack).
        assert abs(panels[0][1] - panels[1][1]) <= 1, rec
        if opt == "fxsize":
            assert abs(gw - 420) <= 4 and abs(gl - 490) <= 4, rec
        else:
            # The array's top holds its first row's by_indiv margin (1.2
            # units of 4.5 in, 10.1 px) above the strips, as twoway's.
            assert abs(gt - (210 + 10.1)) <= 4, rec
            assert abs(gt + gh - 630) <= 4, rec

    @pytest.mark.parametrize("opt", ["fxsize", "fysize"])
    def test_lone(self, opt, mode, tmp_path):
        """The plot region at twoway's: G_fx50's 2299.39 + 1210.61 of
        5400 SVG units (596.1 + 313.9 px at 1400), G_fy50's 810 + 1260.06
        of 3240 (210 + 326.7 px)."""
        html = TestTheThreeCasesInChrome._page(mode, {opt: "50"}, tmp_path)
        mp = pytest.MonkeyPatch()
        mp.setattr(responsive_probe, "PROBE_JS", _FXY_JS)
        try:
            rec = responsive_probe.measure_many(html, (1400,))[1400]
        finally:
            mp.undo()
        rl, rt, rw, rh = rec["region"]
        assert abs(rw - 1400) <= 2 and abs(rh - 840) <= 3, rec
        fl, ft, fw, fh = rec["frames"][0]
        if opt == "fxsize":
            assert abs(fl - 596.1) <= 10 and abs(fw - 313.9) <= 10, rec
        else:
            # Measured 08nov2026: 220.4 + 311 px.  dash's top border keeps
            # Bokeh's 5 px minimum (11 px drawn at this width) where
            # twoway's plot region starts at the box's top, and its x axis
            # is 6 px taller than twoway's 93.
            assert abs(ft - 210) <= 12 and abs(fh - 326.7) <= 18, rec


#: The graph region box's laid-out size and its computed outline, and
#: every plot frame, in page px.
_OUTLINE_JS = r"""
<script>
addEventListener('load', () => setTimeout(() => {
  let region = null; const frames = [];
  const visit = (v) => {
    if (!v) return;
    if (v.model && v.el && region === null
        && (v.model.tags || []).includes('dash_graph_region')) {
      const q = v.el.getBoundingClientRect(), c = getComputedStyle(v.el);
      region = [q.left, q.top, q.width, q.height,
                parseFloat(c.outlineWidth), c.outlineColor,
                parseFloat(c.outlineOffset), c.outlineStyle];
    }
    if (v.frame && v.model && v.el) {
      const r = v.el.getBoundingClientRect(), f = v.frame.bbox;
      const c = getComputedStyle(v.el);
      if (f.width > 20) frames.push([r.left + f.x0, r.top + f.y0,
        parseFloat(c.outlineWidth), c.outlineColor,
        parseFloat(c.outlineOffset), c.outlineStyle]);
    }
    for (const c of (v.child_views || [])) visit(c);
  };
  for (const v of Object.values(Bokeh.index)) { if (!v.parent) visit(v); }
  parent.postMessage('DASHPROBE' + JSON.stringify({W: innerWidth, region,
                                                   frames}), '*');
}, 3000));
</script>
"""


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestGraphOutlineInChrome:
    """WP-45 GW-6 residual: at 1400 px a stcolor graph's region outline is
    drawn inside its edge in the scheme's white, also under
    graphregion(fcolor(red)) (figure_geometry_truth.json M_stcolor_red:
    6.48 of 3240 SVG units, 1.68 px at 840 px tall; Chrome draws an
    outline in whole px), red and thick under lcolor(red) lwidth(thick)
    (I_gla: 25.92 units, 6.72 px); a graph at xsize(4) ysize(4) is its
    384 px box with the scheme's 13.44 px margin inside it (G_xs44)."""

    def _probe(self, mode, go, tmp_path):
        html = TestTheThreeCasesInChrome._page(mode, go, tmp_path)
        mp = pytest.MonkeyPatch()
        mp.setattr(responsive_probe, "PROBE_JS", _OUTLINE_JS)
        try:
            return responsive_probe.measure_many(html, (1400,))[1400]
        finally:
            mp.undo()

    @pytest.mark.parametrize("go,colour,px", [
        ({"graphregion": "fcolor(red)"}, "rgb(255, 255, 255)", 1.68),
        ({"graphregion": "lcolor(red) lwidth(thick)"}, "rgb(255, 0, 0)",
         6.72)], ids=["fcolor", "lcolor"])
    def test_the_outline(self, go, colour, px, mode, tmp_path):
        rec = self._probe(mode, go, tmp_path)
        l, t, w, h, ow, oc, off, sty = rec["region"]
        assert abs(w - 1400) <= 2 and abs(h - 840) <= 3, rec
        assert oc == colour and sty == "solid", rec
        assert abs(ow - px) <= 1 and off == -ow, rec

    def test_the_box_margin(self, mode, tmp_path):
        rec = self._probe(mode, {"xsize": "4", "ysize": "4"}, tmp_path)
        l, t, w, h = rec["region"][:4]
        assert abs(w - 384) <= 1 and abs(h - 384) <= 1, rec
        # The plot region's top: the 13.44 px margin and the 1 px border
        # the plot region's thin outline needs (Flipped, WP-45 GW-6
        # residual: was Bokeh's own 5 px border).
        fl, ft = rec["frames"][0][:2]
        assert abs(ft - t - (13.44 + 1)) <= 1.5, rec

    def test_the_inner_line(self, mode, tmp_path):
        """WP-45 ST-21: graphregion(ilcolor(red) ilwidth(thick)) strokes
        the inner box -- the figure inside the margin -- red, inside its
        edge (I_ilc), and ilalign(outside) in the margin (I_ila)."""
        for al, inside in (("", True), (" ilalign(outside)", False)):
            rec = self._probe(mode, {"graphregion": "ilcolor(red) "
                                     "ilwidth(thick)" + al}, tmp_path)
            ow, oc, off, sty = rec["frames"][0][2:]
            assert oc == "rgb(255, 0, 0)" and sty == "solid", rec
            assert abs(ow - 6.72) <= 1, rec
            assert off == (-ow if inside else 0), rec


#: The plot frame's box, each range's ends and the hull of the first
#: scatter's x and y columns, in page px and data units.
_MARGIN_JS = r"""
<script>
addEventListener('load', () => setTimeout(() => {
  let out = null;
  const visit = (v) => {
    if (!v || out) return;
    if (v.frame && v.model && v.model.x_range) {
      const f = v.frame.bbox, m = v.model;
      const r = m.renderers.find((g) => g.glyph && g.glyph.x
                                 && g.glyph.x.field && g.data_source);
      const col = (n) => Array.from(r.data_source.data[n] || [])
        .filter((z) => Number.isFinite(z));
      const xs = col(r.glyph.x.field), ys = col(r.glyph.y.field);
      out = [f.width, f.height, m.x_range.start, m.x_range.end,
             m.y_range.start, m.y_range.end, Math.min(...xs),
             Math.max(...xs), Math.min(...ys), Math.max(...ys)];
      return;
    }
    for (const c of (v.child_views || [])) visit(c);
  };
  for (const v of Object.values(Bokeh.index)) { if (!v.parent) visit(v); }
  parent.postMessage('DASHPROBE' + JSON.stringify({W: innerWidth, out}),
                     '*');
}, 3000));
</script>
"""


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestPlotMarginInChrome:
    """WP-45 ST-21 residual: plotregion(margin(10 10 10 10)) at xsize(4)
    ysize(8) leaves 288 of 2880 SVG units between the plot region's edge
    and its scale on each side (figure_geometry_truth.json I_pmn48 against
    I_pmz48), 10% of the graph's 4 in smaller side: 38.4 px of the 384 px
    box.  Before: 10% of the smaller side over the graph's own side as the
    frame's share, about 31 px across and 35 down."""

    def test_the_margin(self, mode, tmp_path):
        html = TestTheThreeCasesInChrome._page(
            mode, {"xsize": "4", "ysize": "8",
                   "plotregion": "margin(10 10 10 10)"}, tmp_path)
        mp = pytest.MonkeyPatch()
        mp.setattr(responsive_probe, "PROBE_JS", _MARGIN_JS)
        try:
            rec = responsive_probe.measure_many(html, (1400,))[1400]["out"]
        finally:
            mp.undo()
        fw, fh, x0, x1, y0, y1, xl, xh, yl, yh = rec
        # The left and top sides, where the data's hull ends the scale
        # (the right and bottom ones run on to the ticks 5,000 and 10).
        got = [fw * (xl - x0) / (x1 - x0), fh * (y1 - yh) / (y1 - y0)]
        for px in got:
            assert abs(px - 38.4) <= 2.5, (got, rec)


#: The plot frame's top edge, and the CSS px rows above and below it (a
#: quarter px apart, 12 px each way) where the canvas is red, read at 40%
#: of the frame's width (no axis, tick or title there).
_LINE_JS = r"""
<script>
addEventListener('load', () => setTimeout(() => {
  let out = null;
  const visit = (v) => {
    if (!v || out) return;
    if (v.frame && v.canvas_view && v.frame.bbox.width > 20) {
      const f = v.frame.bbox, ctx = v.canvas_view.primary.ctx;
      const r = window.devicePixelRatio || 1;
      const x = f.x0 + 0.4 * f.width, red = [];
      for (let d = -12; d <= 12; d += 0.25) {
        const p = ctx.getImageData(Math.floor(x * r),
                                   Math.floor((f.y0 + d) * r), 1, 1).data;
        if (p[0] > 200 && p[1] < 90 && p[2] < 90) red.push(d);
      }
      out = {red};
      return;
    }
    for (const c of (v.child_views || [])) visit(c);
  };
  for (const v of Object.values(Bokeh.index)) { if (!v.parent) visit(v); }
  parent.postMessage('DASHPROBE' + JSON.stringify({W: innerWidth, out}),
                     '*');
}, 3000));
</script>
"""


@pytest.mark.parametrize("mode", ("saved", "served"))
class TestPlotLineAlignInChrome:
    """WP-45 ST-21 residual: at 1400 px a stcolor graph's
    plotregion(lcolor(red) lwidth(thick) lalign()) line lies inside the
    plot region's top edge at inside, across it at center and outside it
    at outside, 6.72 px wide (figure_geometry_truth.json I_pli, I_plc,
    I_pla: the 25.92-unit line's centre 12.96 units inside, on and 12.96
    units outside the 113.4-unit edge of 3240, 840 px tall).  dash draws
    inside and center as twoway does and outside centred, a documented
    difference: the canvas ends at the frame on a side without an axis
    (5 px above it before GW-6's min_border 0), so an outside line is cut
    there (measured with the 5 px border: rows -5 to 1 drawn
    red where twoway's run -6.72 to 0).  Before: centred on the edge at
    every lalign()."""

    @pytest.mark.parametrize("al,probe", [("inside", "I_pli"),
                                          ("center", "I_plc"),
                                          ("outside", "I_plc")])
    def test_the_line(self, al, probe, mode, tmp_path):
        import test_figure_geometry as tfg
        line = [r for r in tfg._truth()[probe]["rects"]
                if r["stroke"] == "#ff0000"][0]
        k = 840.0 / 3240.0
        want = ((line["y"] - line["sw"] / 2 - 113.4) * k,
                (line["y"] + line["sw"] / 2 - 113.4) * k)
        html = TestTheThreeCasesInChrome._page(
            mode, {"plotregion": "lalign(%s) lcolor(red) lwidth(thick)"
                   % al}, tmp_path)
        mp = pytest.MonkeyPatch()
        mp.setattr(responsive_probe, "PROBE_JS", _LINE_JS)
        try:
            rec = responsive_probe.measure_many(html, (1400,))[1400]["out"]
        finally:
            mp.undo()
        red = rec["red"]
        assert red, rec
        got = (min(red), max(red) + 0.25)
        assert abs(got[0] - want[0]) <= 1.5 and \
            abs(got[1] - want[1]) <= 1.5, (got, want)
