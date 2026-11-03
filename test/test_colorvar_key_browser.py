"""
test_colorvar_key_browser.py -- clegend()'s bmargin(), subtitle(), note()
and caption() drawn where twoway draws them, read in headless Chrome
(WP-42 CV-15).

Only BokehJS knows where a key cell's frame and texts land once the row is
laid out, so both modes' pages are drawn 1100 px wide and the key is read
in page px against twoway's SVG (test/fixtures/colorvar_key_truth.json,
scripts/extract_colorvar_key_truth.do), whose units are the graph's: 2880
to its smaller side, the drawn graph's height here.  Read: the key cell's
frame against the figure's (the same top and foot), the axis line's ends
from the frame, the swatches' centre from the axis line, and each text's
baseline from the frame.  Without Chrome these tests skip, as
test_legend_span_browser.py's do.
"""
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import responsive_probe  # noqa: E402
import test_colorvar_key as tck  # noqa: E402
import test_colorvar_truth as tct  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_mode_parity import plot_for  # noqa: E402

if responsive_probe.find_chrome() is None:
    pytest.skip("headless Chrome is not installed (set DASH_CHROME); "
                "the browser check is skipped", allow_module_level=True)

# Headless Chrome: the release tier (WP-30 D), never the batch gate.
pytestmark = pytest.mark.release

#: The key cell and its figure: frames, the axis line's ends, the
#: swatches' centre and each Text glyph's baseline, in page px.
_KEY_JS = r"""
<script>
function state() {
  const out = {figs: [], cells: []};
  const visit = (v) => {
    if (!v) return;
    if (v.frame && v.canvas_view && v.model) {
      const cr = v.canvas_view.el.getBoundingClientRect();
      const f = v.frame.bbox;
      const rec = {frame: [cr.left + f.x0, cr.top + f.y0, cr.left + f.x1,
                           cr.top + f.y1],
                   canvas: [cr.left, cr.top, cr.left + v.bbox.width,
                            cr.top + v.bbox.height]};
      if ((v.model.tags || []).includes('dash_key_cell')) {
        const xr = v.model.x_range, yr = v.model.y_range;
        const xx = (x) => cr.left + f.x0 + (x - xr.start) / (xr.end - xr.start) * f.width;
        const yy = (y) => cr.top + f.y0 + (yr.end - y) / (yr.end - yr.start) * f.height;
        rec.texts = {}; rec.swatch = null; rec.line = null;
        for (const [m, rv] of v.renderer_views) {
          if ((m.type || '').endsWith('Axis') && m.bounds) {
            rec.line = [yy(Math.max(m.bounds[0], m.bounds[1])),
                        yy(Math.min(m.bounds[0], m.bounds[1])),
                        cr.left + f.x1];
          }
          if (m.type === 'GlyphRenderer' && m.data_source) {
            const d = m.data_source.data;
            if (m.name === 'dash_key_title_box') {
              rec.box = [xx(d.left[0]), yy(d.top[0]), xx(d.right[0]),
                         yy(d.bottom[0])];
            } else if (m.glyph.type === 'Text' && d.text) {
              rec.texts[d.text[0]] = [xx(d.x[0]), yy(d.y[0]), m.level];
            } else if (d.x && d.x.length && rec.swatch === null) {
              rec.swatch = [xx(d.x[0]), m.level];
            }
          }
        }
        out.cells.push(rec);
      } else if (v.renderer_views) {
        out.figs.push(rec);
      }
    }
    for (const c of (v.child_views || [])) visit(c);
  };
  for (const v of Object.values(Bokeh.index)) visit(v);
  // The graph region's height: twoway's 2880 units.
  const reg = (v) => {
    if (!v) return;
    if (v.model && (v.model.tags || []).includes('dash_graph_region')) {
      out.H = v.el.getBoundingClientRect().height;
    }
    for (const c of (v.child_views || [])) reg(c);
  };
  for (const v of Object.values(Bokeh.index)) reg(v);
  return out;
}
addEventListener('load', () => setTimeout(() => {
  parent.postMessage('DASHPROBE' + JSON.stringify({W: innerWidth, wide: state()}), '*');
}, 3000));
</script>
"""

_OPTS = dict(tck._P_OPTS, P_bm_m="bmargin(medium)", P_bm_v="bmargin(vlarge)")


@pytest.fixture
def _auto(monkeypatch):
    monkeypatch.setattr(tp, "_DF", tct._auto_frame())


_SEEN = {}


def _drawn(mode, pid):
    """The key cell's and its figure's record at 1100 px (one Chrome run
    a page)."""
    if (mode, pid) not in _SEEN:
        _SEEN[(mode, pid)] = _draw(mode, pid)
    return _SEEN[(mode, pid)]


def _draw(mode, pid):
    spec = tp._spec([plot_for("scatter", tck._KEY_OPTS["K1"], yvar="mpg",
                              xvar="weight")], {"scheme": "s2color"},
                    {"clegend": _OPTS[pid]})
    if mode == "saved":
        page = tp._standalone_page(spec)[2]
    else:
        from bokeh.embed import file_html
        from bokeh.resources import INLINE
        doc, _w = tp._served(spec)
        page = file_html(doc, INLINE, "served")
    mp = pytest.MonkeyPatch()
    mp.setattr(responsive_probe, "PROBE_JS", _KEY_JS)
    try:
        got = responsive_probe.measure_many(page, (1100,))[1100]["wide"]
    finally:
        mp.undo()
    (cell,) = got["cells"]
    fig = max(got["figs"], key=lambda r: r["frame"][2] - r["frame"][0])
    return fig, cell, got["H"] / 2880.0


def _down(rec, y, frame):
    """twoway's *y* as page px below dash's frame top: its share of
    twoway's plot region times dash's frame (the plot region's own height
    is not this item's)."""
    pl = rec["plot"]
    return (y - pl["top"]) / (pl["bottom"] - pl["top"]) * (frame[3] - frame[1])


@pytest.mark.usefixtures("_auto")
@pytest.mark.parametrize("mode", ("saved", "served"))
class TestTheKeyAsDrawn:

    @pytest.mark.parametrize("pid", ("P_bm_m", "P_bm", "P_bm_v", "P_sub",
                                     "P_ti", "P_tbx"))
    def test_frame_line_and_swatches(self, mode, pid):
        rec = tck._key_truth()[pid]
        fig, cell, s = _drawn(mode, pid)
        # One frame: the key's top and foot are the plot region's.
        assert abs(cell["frame"][1] - fig["frame"][1]) <= 1.0, (fig, cell)
        assert abs(cell["frame"][3] - fig["frame"][3]) <= 1.0, (fig, cell)
        v = rec["key"]["vlines"][0]
        f = cell["frame"]
        top, foot = min(v["y1"], v["y2"]), max(v["y1"], v["y2"])
        assert cell["line"][0] - f[1] == pytest.approx(
            _down(rec, top, f), abs=2.0)
        assert cell["line"][1] - f[1] == pytest.approx(
            _down(rec, foot, f), abs=2.0)
        if pid.startswith("P_bm"):
            # The swatches' move toward the axis line from K1's (bmargin()
            # moves them toward it and, at vlarge, across it), drawn
            # whole; K1's own gap is CV-3's.
            k1 = tck._key_truth()["K1"]
            _f, c1, _s = _drawn(mode, "K1")
            moved = (c1["line"][2] - c1["swatch"][0]) \
                - (cell["line"][2] - cell["swatch"][0])
            gap = lambda r: r["key"]["vlines"][0]["x1"] \
                - r["key"]["circles"][0]["cx"]  # noqa: E731
            assert moved == pytest.approx((gap(k1) - gap(rec)) * s, abs=1.0)
            assert cell["swatch"][1] == "overlay"

    @pytest.mark.parametrize("pid,names", (("P_sub", "SNC"), ("P_ti", "Z"),
                                           ("P_tbx", "Z")))
    def test_texts(self, mode, pid, names):
        rec = tck._key_truth()[pid]
        fig, cell, s = _drawn(mode, pid)
        pl = rec["plot"]
        tw = {t["text"]: t for t in rec["texts"] if t["text"] in names
              and len(t["text"]) == 1}
        assert set(cell["texts"]) == set(names)
        for k, (x, y, level) in cell["texts"].items():
            # Baselines from the frame's top, drawn whole (over the frame).
            assert level == "overlay"
            assert y - cell["frame"][1] == pytest.approx(
                _down(rec, tw[k]["y"], cell["frame"]), abs=2.0), (k, cell)
            assert x - fig["frame"][2] == pytest.approx(
                (tw[k]["x"] - pl["right"]) * s, abs=2.0), (k, cell)


#: The plot region's, the series legend's and the key cell's boxes across
#: the page (page px).
_RING_JS = r"""
<script>
function state() {
  const out = {legend: null, frame: null, cell: null};
  const visit = (v) => {
    if (!v) return;
    if (v.frame && v.canvas_view && v.model) {
      const cr = v.canvas_view.el.getBoundingClientRect();
      if ((v.model.tags || []).includes('dash_key_cell')) {
        out.cell = [cr.left, cr.left + cr.width];
      } else if (v.renderer_views) {
        out.frame = [cr.left + v.frame.bbox.x0, cr.left + v.frame.bbox.x1];
        for (const [m, rv] of v.renderer_views) {
          if (m.type === 'Legend' && rv.bbox && m.visible) {
            out.legend = [cr.left + rv.bbox.left, cr.left + rv.bbox.right];
          }
        }
      }
    }
    for (const c of (v.child_views || [])) visit(c);
  };
  for (const v of Object.values(Bokeh.index)) visit(v);
  return out;
}
addEventListener('load', () => setTimeout(() => {
  parent.postMessage('DASHPROBE' + JSON.stringify({W: innerWidth, wide: state()}), '*');
}, 3000));
</script>
"""


def _ring_boxes(mode, clegend):
    plots = [plot_for("scatter", {"colorvar": "price"}, yvar="mpg",
                      xvar="weight"),
             plot_for("scatter", {}, yvar="price", xvar="weight")]
    go = {"legend": "pos(3)"}
    if clegend:
        go["clegend"] = clegend
    spec = tp._spec(plots, {"scheme": "s2color"}, go)
    if mode == "saved":
        page = tp._standalone_page(spec)[2]
    else:
        from bokeh.embed import file_html
        from bokeh.resources import INLINE
        doc, _w = tp._served(spec)
        page = file_html(doc, INLINE, "served")
    mp = pytest.MonkeyPatch()
    mp.setattr(responsive_probe, "PROBE_JS", _RING_JS)
    try:
        return responsive_probe.measure_many(page, (1100,))[1100]["wide"]
    finally:
        mp.undo()


@pytest.mark.usefixtures("_auto")
@pytest.mark.parametrize("mode", ("saved", "served"))
class TestTheKeysRingBesideTheLegend:
    """scheme_key_readers' measurement: beside legend(pos(3)) (ring 3)
    twoway draws clegend(ring(2)) between the plot and the legend, and its
    default ring 4 outside the legend.  The key cell drew outside the
    legend at any ring (WP-42 CV-3)."""

    def test_ring_2_is_between_the_plot_and_the_legend(self, mode):
        b = _ring_boxes(mode, "ring(2)")
        assert b["frame"][1] <= b["cell"][0] + 1.0, b
        assert b["cell"][1] <= b["legend"][0] + 1.0, b

    def test_the_default_ring_is_outside_the_legend(self, mode):
        b = _ring_boxes(mode, "")
        assert b["legend"][1] <= b["cell"][0] + 1.0, b


@pytest.mark.usefixtures("_auto")
@pytest.mark.parametrize("mode", ("saved", "served"))
@pytest.mark.parametrize("pid", ("P_tbx", "P_tbx2", "P_tbx3", "P_tbx4"))
def test_the_title_box(mode, pid):
    """LT-12 (P_tbx .. P_tbx4: Z, "Price in dollars", "WWW", "iii"):
    title(, box)'s fill is the band from the line's ordinary top to its new
    one, twoway's width -- the drawn text's with its margins, at most 408
    -- centred on the title."""
    rec = tck._key_truth()[pid]
    fig, cell, s = _drawn(mode, pid)
    fill = [r for r in rec["key"]["rects"] if r["fill"] == "#d9e6eb"][0]
    f = cell["frame"]
    x0, y0, x1, y1 = cell["box"]
    assert x1 - x0 == pytest.approx(fill["w"] * s, abs=2.0)
    assert y0 - f[1] == pytest.approx(_down(rec, fill["y"], f), abs=2.0)
    assert y1 - f[1] == pytest.approx(
        _down(rec, fill["y"] + fill["h"], f), abs=2.0)
    (t,) = [v for k, v in cell["texts"].items()]
    assert (x0 + x1) / 2.0 == pytest.approx(t[0], abs=1.0)
