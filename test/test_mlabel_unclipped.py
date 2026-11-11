"""Marker labels run past the plot region, as twoway draws them (WP-47 MS-15).

Measured 11nov2026 (StataNow 19.5, stcolor, each picture exported to SVG;
test/fixtures/mlabel_clip_truth.json, scripts/extract_mlabel_clip_truth.do):
twoway clips no marker label.  The calibration example
``scatter lexp gnppc if region==2, mlabel(country) mlabv(pos)
xsca(range(35000))`` draws Honduras (9 o'clock) from x 262.5 to 652.4 where
the plot region starts at 522.8, over the y axis's labels; a long label at
9, 3, 12 or 6 runs over the left, right, top or bottom edge and off the
graph's own edge; under by() a label runs on over the next panel.  The SVG
holds no clip at all.

dash drew each layer's labels with a Bokeh LabelSet in the figure's centre,
and BokehJS clips a centre annotation to the frame
(``AnnotationView.needs_clip`` is ``layout == null``, bokeh.js 3.8 and 3.9).
A GlyphRenderer is clipped only at the image, underlay and glyph levels
(``PlotView._paint_levels(ctx, level, frame_box, global_clip)``: the guide,
annotation and overlay levels pass ``global_clip`` false, and
``RendererView.needs_clip`` is false), so the labels are now a Text glyph
drawn at the annotation level: over the axes, to the figure's edge.
"""
import json
import os
import sys

import pytest
from bokeh.models import GlyphRenderer, LabelSet, Text

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

from test_marker_label_parity import _both  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "mlabel_clip_truth.json")
#: The levels BokehJS clips to the frame whatever the renderer.
_CLIPPED_LEVELS = ("image", "underlay", "glyph")


def _truth():
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _label(probe, text):
    (one,) = [lab for lab in probe["labels"] if lab["text"] == text]
    return one


class TestTwowayDrawsPastTheRegion:
    """The measurement the fix is held to."""

    def test_twoway_clips_nothing(self):
        for pid, probe in _truth()["probes"].items():
            assert probe["rc"] == 0, pid
            assert probe["clips"] == 0, (pid, probe["clips"])

    def test_honduras_runs_over_the_y_axis_labels(self):
        cal = _truth()["probes"]["CAL"]
        (region,) = cal["regions"]
        hon = _label(cal, "Honduras")
        assert hon["anchor"] == "end"
        assert 0 < hon["left"] < region["left"] < hon["right"], hon

    def test_each_edge_is_crossed_and_the_graph_edge_too(self):
        edge = _truth()["probes"]["EDGE"]
        (region,) = edge["regions"]
        w = edge["canvas"]["w"]
        left = _label(edge, "Label1_runs_well_past_the_region")
        right = _label(edge, "Label2_runs_well_past_the_region")
        top = _label(edge, "Label3_runs_well_past_the_region")
        bottom = _label(edge, "Label4_runs_well_past_the_region")
        assert left["left"] < 0 < region["left"] < left["right"], left
        assert right["left"] < region["right"] < w < right["right"], right
        # A cap height (0.718 em in Helvetica) above the baseline.
        assert top["y"] - 0.718 * top["size"] < region["top"] < top["y"], top
        assert bottom["y"] > region["bottom"], bottom

    def test_under_by_a_label_runs_over_the_next_panel(self):
        by = _truth()["probes"]["BY"]
        first, second = sorted(by["regions"], key=lambda r: r["left"])
        right = _label(by, "Label2_runs_well_past_the_region")
        left = _label(by, "Label1_runs_well_past_the_region")
        assert right["left"] < first["right"] < second["left"] \
            < right["right"], right
        assert left["left"] < first["right"] < second["left"] \
            < left["right"], left


def _label_models(fig):
    """Every model that draws *fig*'s marker labels: (LabelSets in the
    centre, Text glyph renderers)."""
    sets = [m for m in fig.center if isinstance(m, LabelSet)]
    texts = [r for r in fig.renderers if isinstance(r, GlyphRenderer)
             and isinstance(r.glyph, Text)]
    return sets, texts


@pytest.mark.parametrize("mode", ["saved", "served"])
@pytest.mark.parametrize("ptype,ends", [("scatter", 1), ("connected", 1),
                                         ("rcapsym", 2), ("pcscatter", 1)])
class TestDashDrawsPastTheRegion:

    def test_no_label_is_clipped_to_the_frame(self, mode, ptype, ends):
        saved, served, _sw, _vw = _both(
            [plot_for(ptype, {"mlabel": "make"})], served=mode == "served")
        fig = saved if mode == "saved" else served
        sets, texts = _label_models(fig)
        assert sets == [], (
            f"{mode} {ptype}: marker labels drawn by a LabelSet, which "
            f"BokehJS clips to the plot frame")
        assert len(texts) == ends, (mode, ptype, texts)
        for r in texts:
            assert r.level not in _CLIPPED_LEVELS, (mode, ptype, r.level)
            assert r.level == "annotation", (mode, ptype, r.level)

    def test_a_selection_does_not_dim_the_labels(self, mode, ptype, ends):
        """A LabelSet ignores the source's selection; the Text renderer's
        selected and brushed-away copies draw as its glyph does, each a
        model of its own (the scale passes size each once)."""
        saved, served, _sw, _vw = _both(
            [plot_for(ptype, {"mlabel": "make"})], served=mode == "served")
        fig = saved if mode == "saved" else served
        _sets, texts = _label_models(fig)
        assert texts, (mode, ptype)
        props = ("text_alpha", "text_color", "text_font_size", "x_offset",
                 "y_offset", "text_align", "text_baseline", "tags")
        for r in texts:
            for copy in (r.selection_glyph, r.nonselection_glyph):
                assert isinstance(copy, Text) and copy is not r.glyph, (
                    mode, ptype, copy)
                for n in props:
                    assert getattr(copy, n) == getattr(r.glyph, n), (
                        mode, ptype, n)


# ---------------------------------------------------------------------------
# The in-frame filter under node (WP-47 MS-15, the maintainer's condition)
# ---------------------------------------------------------------------------

from js_runner import requires_node, run_js  # noqa: E402

import dash_render as dr  # noqa: E402

_HARNESS = r"""
class Signal { constructor() { this.slots = []; }
  connect(f) { this.slots.push(f); } emit() { for (const f of this.slots) f(); } }
const pending = [];
globalThis.setTimeout = (f, ms) => { pending.push(ms); };
globalThis.Bokeh = {index: {}};
const mk = (start, end) => ({start, end, change: new Signal()});
const set = (rg, start, end) => { rg.start = start; rg.end = end; rg.change.emit(); };
const fn = new Function("source", %(code)s);
const xs = [1, 5, 10, null, 3], ys = [1, 5, 10, 4, 99];
const source = {get_length: () => xs.length,
                get_column: (c) => ({x: xs, y: ys, d: xs})[c]};
const me = {change: new Signal()};
const x2 = mk(0, 100);
const r = {view: {filter: me}, x_range_name: "default", y_range_name: "y2",
           glyph: {x: {field: "x"}, y: {field: "y"}}};
const other = {view: {filter: {}}};
const fig = {x_range: mk(0, 10), y_range: mk(0, 10), extra_x_ranges: {},
             extra_y_ranges: new Map([["y2", x2]])};
const pv = {model: fig, renderer_views: new Map([[1, {model: other}], [2, {model: r}]]),
            child_views: []};
const out = {};
let runs = 0;
me.change.connect(() => { runs++; });
out.unbuilt = fn.call(me, source);
out.retry = pending.slice();
Bokeh.index = {root: {child_views: [{child_views: [pv]}]}};
out.first = fn.call(me, source);
set(fig.x_range, 2, 10);
out.panned = fn.call(me, source);
set(x2, 10, 0);
out.reversed = fn.call(me, source);
set(fig.x_range, NaN, NaN);
out.unset = fn.call(me, source);
out.runs = runs;
r.glyph.x = {field: "d", transform: {v_compute: (v) => v.map(t => t == null ? null : t * 2)}};
set(fig.x_range, 0, 10);
out.transformed = fn.call(me, source);
console.log(JSON.stringify(out));
"""


@requires_node
class TestTheInFrameFilter:

    def test_a_label_is_kept_while_its_point_is_in_the_ranges(self):
        out = run_js(_HARNESS % {"code": json.dumps(
            dr._DASH_MLABEL_IN_FRAME_JS)})
        # Each row's x and y on the renderer's own ranges: x on the
        # default, y on the extra "y2" (0..100); a missing x keeps its
        # label (it draws none).
        assert out["first"] == [True, True, True, True, True]
        # A pan to 2..10 takes x = 1 out; the edge x = 10 stays.
        assert out["panned"] == [False, True, True, True, True]
        # A reversed range (y2 10..0) is read by its ends: y 99 is out.
        assert out["reversed"] == [False, True, True, True, False]
        # A range not yet computed (x NaN) keeps every label on it.
        assert out["unset"] == [True, True, True, True, False]
        # Each range is hooked once: three changes, three recomputes.
        assert out["runs"] == 3
        # The coordinate is read through its transform (x 1 5 10 3 ->
        # 2 10 20 6 on 0..10).
        assert out["transformed"] == [True, True, False, True, False]
        # Before the views exist it keeps every label and looks again.
        assert out["unbuilt"] is None and out["retry"] == [100]


def test_the_help_says_where_a_label_runs_and_when_it_goes():
    """dash.sthlp's Marker Label Options states MS-15's rule and its
    by() residual."""
    with open(os.path.join(_HERE, "..", "dash.sthlp"), encoding="utf-8") as fh:
        text = " ".join(fh.read().split())
    for claim in ("A label runs past the plot region, over the axes and "
                  "their labels, to the edge of the graph, as {cmd:twoway} "
                  "draws it;",
                  "under {cmd:by()} it stops at its panel's edge, where "
                  "{cmd:twoway}'s runs on over the next panel.",
                  "When a pan, a zoom or a range move takes a point out of "
                  "the plot region, its label goes with it"):
        assert claim in text, claim
