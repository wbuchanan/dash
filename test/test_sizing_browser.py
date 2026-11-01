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
            mod = ts.load_app(ap, "_szb_app_%d" % tag)
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
            mod = ts.load_app(ap, "_szs_app_%d" % tag)
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



_PICTURE_JS = r"""
<script>
addEventListener('load', () => setTimeout(() => {
  const plots = [];
  const visit = (v) => {
    if (!v) return;
    if (v.frame && v.model) {
      const ax = (v.model.below || []).filter(
        (a) => a.major_label_text_font_size);
      plots.push([v.el.getBoundingClientRect().top,
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
            assert abs(left - m) <= 2 and abs(top - m) <= 2, (go, rec)
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
