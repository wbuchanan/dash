"""
test_dual_axis.py
Unit and integration tests for yaxis(#)/xaxis(#) dual-axis support.

Run with:  pytest test/test_dual_axis.py -v
"""
import sys
import os
import json
import tempfile
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dash_render import DashRenderer


# ============================================================
# Helpers
# ============================================================

def _make_spec_and_data(plots, graph_opts=None):
    """Return (spec_dict, data_json_dict) for a single-graph dashboard."""
    n = 20
    np.random.seed(0)
    data = {
        "x":    list(range(1, n + 1)),
        "y1":   np.random.uniform(0, 100, n).tolist(),
        "y2":   np.random.uniform(1000, 5000, n).tolist(),
        "y3":   np.random.uniform(-1, 1, n).tolist(),
    }
    data_json = {
        "StataJSON": {
            "variableNames": list(data.keys()),
            "variableLabels": {k: k for k in data},
            "valueLabels": {},
            "valueLabelNames": {},
            "variableTypeIsString": {k: False for k in data},
            "values": [{k: data[k][i] for k in data} for i in range(n)],
        }
    }
    spec = {
        "graphs": [{
            "plots": plots,
            "graph_options": graph_opts or {"name": "fig1"},
            "if_expr": "",
            "in_expr": "",
        }],
        "kpis": [],
        "build_options": {
            "layout": "auto", "link": "", "filter": "",
            "theme": "default", "title": "", "subtitle": "",
            "registry": "fig1",
        },
    }
    return spec, data_json


def _render(plots, graph_opts=None):
    """Full HTML render; returns html string."""
    spec, data_json = _make_spec_and_data(plots, graph_opts)
    sp, dp, op = [tempfile.mkstemp(s)[1] for s in (".json", ".json", ".html")]
    try:
        with open(sp, "w") as f:
            json.dump(spec, f)
        with open(dp, "w") as f:
            json.dump(data_json, f)
        return DashRenderer(sp, dp, op).render()
    finally:
        for p in (sp, dp, op):
            try:
                os.unlink(p)
            except OSError:
                pass


def _make_renderer(plots, graph_opts=None):
    """Instantiate a DashRenderer and return it (don't call render())."""
    spec, data_json = _make_spec_and_data(plots, graph_opts)
    sp, dp, op = [tempfile.mkstemp(s)[1] for s in (".json", ".json", ".html")]
    try:
        with open(sp, "w") as f:
            json.dump(spec, f)
        with open(dp, "w") as f:
            json.dump(data_json, f)
        return DashRenderer(sp, dp, op)
    finally:
        for p in (sp, dp, op):
            try:
                os.unlink(p)
            except OSError:
                pass


# ============================================================
# DAX-01 – 06: Figure-level secondary axis setup
# ============================================================

class TestSecondaryAxisSetup:
    def _get_fig(self, plots, graph_opts=None):
        dr = _make_renderer(plots, graph_opts)
        figs = dr._build_figures()
        return list(figs.values())[0]

    def test_no_secondary_axis_by_default(self):
        """DAX-01: figure has no extra_y_ranges when no yaxis(2) plot."""
        plots = [{"type": "scatter", "yvar": "y1", "xvar": "x", "options": {}}]
        fig = self._get_fig(plots)
        assert "y2" not in fig.extra_y_ranges

    def test_secondary_y_axis_added(self):
        """DAX-02: extra_y_ranges['y2'] created when yaxis(2) plot present."""
        plots = [
            {"type": "scatter", "yvar": "y1", "xvar": "x", "options": {}},
            {"type": "line",    "yvar": "y2", "xvar": "x", "options": {"yaxis": "2"}},
        ]
        fig = self._get_fig(plots)
        assert "y2" in fig.extra_y_ranges

    def test_secondary_y_axis_renderer_assigned(self):
        """DAX-03: renderers for yaxis(2) plot have y_range_name='y2'."""
        plots = [
            {"type": "scatter", "yvar": "y1", "xvar": "x", "options": {}},
            {"type": "line",    "yvar": "y2", "xvar": "x", "options": {"yaxis": "2"}},
        ]
        fig = self._get_fig(plots)
        # At least one renderer should have y_range_name == "y2"
        y2_renderers = [r for r in drawn_renderers(fig)
                        if getattr(r, "y_range_name", None) == "y2"]
        assert len(y2_renderers) >= 1

    def test_primary_y_axis_renderer_unchanged(self):
        """DAX-04: renderers for primary axis keep default y_range_name."""
        plots = [
            {"type": "scatter", "yvar": "y1", "xvar": "x", "options": {}},
            {"type": "line",    "yvar": "y2", "xvar": "x", "options": {"yaxis": "2"}},
        ]
        fig = self._get_fig(plots)
        primary_renderers = [r for r in drawn_renderers(fig)
                             if getattr(r, "y_range_name", None) != "y2"]
        assert len(primary_renderers) >= 1

    def test_secondary_x_axis_added(self):
        """DAX-05: extra_x_ranges['x2'] created when xaxis(2) plot present."""
        plots = [
            {"type": "scatter", "yvar": "y1", "xvar": "x", "options": {}},
            {"type": "scatter", "yvar": "y3", "xvar": "y2",
             "options": {"xaxis": "2"}},
        ]
        fig = self._get_fig(plots)
        assert "x2" in fig.extra_x_ranges

    def test_secondary_y_axis_range_covers_data(self):
        """DAX-06: extra_y_ranges['y2'] start < end and covers the y2 data."""
        plots = [
            {"type": "scatter", "yvar": "y1", "xvar": "x", "options": {}},
            {"type": "line",    "yvar": "y2", "xvar": "x", "options": {"yaxis": "2"}},
        ]
        fig = self._get_fig(plots)
        rng = fig.extra_y_ranges["y2"]
        assert rng.start < rng.end
        # y2 data in fixture is in range [1000, 5000] with padding
        assert rng.start < 1000
        assert rng.end > 5000


# ============================================================
# DAX-07 – 09: Secondary axis options (title, ticks, log scale)
# ============================================================

class TestSecondaryAxisOptions:
    def _get_fig(self, plots, graph_opts=None):
        dr = _make_renderer(plots, graph_opts)
        figs = dr._build_figures()
        return list(figs.values())[0]

    def test_ytitle2_on_right_axis(self):
        """DAX-07: ytitle2 option sets axis_label on the right axis (beside
        a first-axis layer: a lone yaxis(2) graph draws one axis, on the
        left -- TestALoneSecondAxisIsDrawnAsTwowayDrawsIt).  WP-28 B7: the
        label is exactly the text, not a substring of something wider."""
        plots = [
            {"type": "scatter", "yvar": "y1", "xvar": "x", "options": {}},
            {"type": "line", "yvar": "y2", "xvar": "x", "options": {"yaxis": "2"}},
        ]
        graph_opts = {"name": "fig1", "ytitle2": "Secondary Y"}
        fig = self._get_fig(plots, graph_opts)
        right_axes = [ax for ax in fig.right
                      if hasattr(ax, "axis_label")]
        assert [ax.axis_label for ax in right_axes] == ["Secondary Y"]

    def test_ytitle2_lines_size_and_colour(self):
        """WP-28 B7: ytitle2() is read as a textbox, like every other text
        option -- quoted lines joined with a newline, size() and color()
        applied, in pixels and CSS, the same properties
        _dash_style_axis_titles sets on the first axis."""
        plots = [
            {"type": "scatter", "yvar": "y1", "xvar": "x", "options": {}},
            {"type": "line", "yvar": "y2", "xvar": "x", "options": {"yaxis": "2"}},
        ]
        graph_opts = {"name": "fig1",
                      "ytitle2": '"a" "b", size(large) color(red)'}
        fig = self._get_fig(plots, graph_opts)
        (ax,) = [ax for ax in fig.right if hasattr(ax, "axis_label")]
        assert ax.axis_label == "a\nb"
        assert ax.axis_label_text_font_size is not None
        assert str(ax.axis_label_text_color).lower() in ("red", "#ff0000")

    def test_ylabel2_custom_ticks(self):
        """DAX-08: ylabel2 option applies FixedTicker to secondary y-axis."""
        from bokeh.models.tickers import FixedTicker
        plots = [
            {"type": "scatter", "yvar": "y1", "xvar": "x", "options": {}},
            {"type": "line", "yvar": "y2", "xvar": "x", "options": {"yaxis": "2"}},
        ]
        graph_opts = {"name": "fig1", "ylabel2": "1000 2000 3000 4000 5000"}
        fig = self._get_fig(plots, graph_opts)
        right_axes = [ax for ax in fig.right if hasattr(ax, "ticker")]
        assert any(isinstance(ax.ticker, FixedTicker) for ax in right_axes)

    def test_dual_axis_html_renders(self):
        """DAX-09: full HTML render with yaxis(2) completes without error."""
        plots = [
            {"type": "scatter", "yvar": "y1", "xvar": "x", "options": {}},
            {"type": "line",    "yvar": "y2", "xvar": "x", "options": {"yaxis": "2"}},
        ]
        html_str = _render(plots)
        assert len(html_str) > 100


# ============================================================
# DAX-10 – 11: Multi-layer secondary axis
# ============================================================

class TestMultiLayerSecondaryAxis:
    def _get_fig(self, plots, graph_opts=None):
        dr = _make_renderer(plots, graph_opts)
        figs = dr._build_figures()
        return list(figs.values())[0]

    def test_multiple_secondary_layers_all_assigned(self):
        """DAX-10: all plot layers with yaxis(2) get y_range_name='y2'."""
        plots = [
            {"type": "scatter", "yvar": "y1", "xvar": "x", "options": {}},
            {"type": "line",    "yvar": "y2", "xvar": "x", "options": {"yaxis": "2"}},
            {"type": "scatter", "yvar": "y3", "xvar": "x", "options": {"yaxis": "2"}},
        ]
        fig = self._get_fig(plots)
        y2_renderers = [r for r in drawn_renderers(fig)
                        if getattr(r, "y_range_name", None) == "y2"]
        assert len(y2_renderers) >= 2
        # Layer by layer, not by count: ">= 2" held just as well with the
        # primary layer moved to y2 too (three).  One renderer per layer
        # here, measured 24sep2026: the y1 scatter stays on the default
        # range, the y2 line and the y3 scatter are on y2.
        placed = sorted((r.glyph.y, r.y_range_name) for r in drawn_renderers(fig))
        assert placed == [("y1", "default"), ("y2", "y2"), ("y3", "y2")], (
            placed
        )

    def test_single_right_axis_with_multiple_secondary_layers(self):
        """DAX-11: only one right-side axis added, not one per layer."""
        plots = [
            {"type": "scatter", "yvar": "y1", "xvar": "x", "options": {}},
            {"type": "line",    "yvar": "y2", "xvar": "x", "options": {"yaxis": "2"}},
            {"type": "scatter", "yvar": "y3", "xvar": "x", "options": {"yaxis": "2"}},
        ]
        fig = self._get_fig(plots)
        assert len(fig.right) == 1


# ============================================================
# DAX-12: Security — injection in yaxis option value
# ============================================================

class TestSecondaryAxisSecurity:
    def _get_fig(self, plots, graph_opts=None):
        dr = _make_renderer(plots, graph_opts)
        figs = dr._build_figures()
        return list(figs.values())[0]

    def test_non_numeric_yaxis_treated_as_primary(self):
        """DAX-12: non-numeric yaxis value doesn't crash and uses primary axis."""
        plots = [
            {"type": "scatter", "yvar": "y1", "xvar": "x",
             "options": {"yaxis": "2; import os"}},
        ]
        # Should not raise; the string "2; import os" != "2", so no secondary axis
        fig = self._get_fig(plots)
        assert "y2" not in fig.extra_y_ranges


# ============================================================
# A graph whose every layer is on yaxis(2) (BUGS.md, S3)
# ============================================================
#
# Measured 24sep2026, StataNow 19.5, `sysuse auto', from graph export svg:
#
#   twoway scatter mpg weight, yaxis(2)
#       one y axis, on the LEFT (its labels 10 20 30 40 at x = 455 of the
#       graph, where a first y axis's are), titled with the variable's
#       label "Mileage (mpg)";
#   ... yaxis(2) ytitle(TITLETWO, axis(2)) ylabel(#3, axis(2))
#       the same left axis, titled TITLETWO -- the second axis's options
#       style the one axis drawn;
#   ... yaxis(2) ytitle(TITLEONE)
#       refused, r(198): there is no first axis to title;
#   ... yaxis(2) yscale(log axis(2))
#       the left axis on a log scale;
#   (scatter mpg weight, yaxis(2)) (line price weight, yaxis(2) sort)
#       one left axis, 0 5000 10000 15000;
#   twoway scatter mpg weight, xaxis(2)
#       one x axis, at the BOTTOM.
#
# dash drew a left axis over nothing and a right axis for the layers.
# dash's second-axis options are ytitle2(), ylabel2() and yscale2() (twoway
# writes them with axis(2)); on a lone second axis they style the one axis.

import importlib.util as _ilu
import itertools as _it
from conftest import drawn_renderers  # noqa: E402

_LONE_SEQ = _it.count()
_LONE_MODES = ("saved", "served")


def _lone_figure(mode, plots, graph_opts=None):
    """The one figure the saved renderer or the served app draws."""
    from bokeh.document import Document
    from bokeh.plotting import figure as _fig_cls
    import dash_render as _dr
    spec, data_json = _make_spec_and_data(plots, graph_opts)
    d = tempfile.mkdtemp(prefix="dash_lone_y2_")
    sp, dp = os.path.join(d, "spec.json"), os.path.join(d, "data.json")
    with open(sp, "w") as f:
        json.dump(spec, f)
    with open(dp, "w") as f:
        json.dump(data_json, f)
    if mode == "saved":
        r = DashRenderer(sp, dp)
        return list(r._build_figures().values())[0]
    ap = os.path.join(d, "app.py")
    _dr.ServerAppBuilder(sp, dp).build(ap)
    ms = _ilu.spec_from_file_location("_lone_y2_app_%d" % next(_LONE_SEQ), ap)
    mod = _ilu.module_from_spec(ms)
    ms.loader.exec_module(mod)
    doc = Document()
    mod.make_document(doc)
    figs = [m for root in doc.roots for m in root.references()
            if isinstance(m, _fig_cls)]
    assert len(figs) == 1, figs
    return figs[0]


def _axes(side):
    from bokeh.models import ContinuousAxis
    return [a for a in side if isinstance(a, ContinuousAxis)]


def _layers(fig):
    from bokeh.models import GlyphRenderer
    return [r for r in drawn_renderers(fig) if isinstance(r, GlyphRenderer)]


_LONE = [{"type": "scatter", "yvar": "y2", "xvar": "x",
          "options": {"yaxis": "2"}}]


@pytest.mark.parametrize("mode", _LONE_MODES)
class TestALoneSecondAxisIsDrawnAsTwowayDrawsIt:
    def test_one_y_axis_on_the_left(self, mode):
        fig = _lone_figure(mode, _LONE)
        assert len(_axes(fig.left)) == 1
        assert _axes(fig.right) == []
        assert "y2" not in fig.extra_y_ranges
        assert [r.y_range_name for r in _layers(fig)] == ["default"]

    def test_titled_with_the_variables_label(self, mode):
        fig = _lone_figure(mode, _LONE)
        assert [a.axis_label for a in _axes(fig.left)] == ["y2"]

    def test_ytitle2_titles_it(self, mode):
        fig = _lone_figure(mode, _LONE,
                           {"name": "fig1", "ytitle2": "TITLETWO"})
        assert [a.axis_label for a in _axes(fig.left)] == ["TITLETWO"]

    def test_ylabel2_labels_it(self, mode):
        from bokeh.models.tickers import FixedTicker
        fig = _lone_figure(mode, _LONE,
                           {"name": "fig1", "ylabel2": "1000(2000)5000"})
        (ax,) = _axes(fig.left)
        assert isinstance(ax.ticker, FixedTicker)
        assert list(ax.ticker.ticks) == [1000.0, 3000.0, 5000.0]

    def test_yscale2_log_makes_it_a_log_axis(self, mode):
        from bokeh.models import LogAxis
        fig = _lone_figure(mode, _LONE, {"name": "fig1", "yscale2": "log"})
        (ax,) = _axes(fig.left)
        assert isinstance(ax, LogAxis)

    def test_two_layers_on_the_second_axis_share_the_one_axis(self, mode):
        plots = [{"type": "scatter", "yvar": "y1", "xvar": "x",
                  "options": {"yaxis": "2"}},
                 {"type": "line", "yvar": "y2", "xvar": "x",
                  "options": {"yaxis": "2"}}]
        fig = _lone_figure(mode, plots)
        assert len(_axes(fig.left)) == 1 and _axes(fig.right) == []
        assert {r.y_range_name for r in _layers(fig)} == {"default"}

    def test_a_lone_xaxis2_is_drawn_at_the_bottom(self, mode):
        plots = [{"type": "scatter", "yvar": "y1", "xvar": "x",
                  "options": {"xaxis": "2"}}]
        fig = _lone_figure(mode, plots)
        assert len(_axes(fig.below)) == 1
        assert _axes(fig.above) == []
        assert "x2" not in fig.extra_x_ranges

    def test_a_first_axis_layer_keeps_both_axes(self, mode):
        """Control: with a layer on the first axis, the second is drawn on
        the right, as twoway draws it."""
        plots = [{"type": "scatter", "yvar": "y1", "xvar": "x",
                  "options": {}}] + _LONE
        fig = _lone_figure(mode, plots)
        assert len(_axes(fig.left)) == 1 and len(_axes(fig.right)) == 1
        assert [r.y_range_name for r in _layers(fig)] == ["default", "y2"]

    def test_a_hostile_title_is_canvas_text(self, mode):
        """Adversarial: ytitle2() text reaches the axis title verbatim, as
        text Bokeh draws on the canvas -- never markup, and never read as
        another option (a title naming ylabel2() is only text)."""
        hostile = '<script>alert(1)</script>" ylabel2(#9999999)'
        fig = _lone_figure(mode, _LONE, {"name": "fig1", "ytitle2": hostile})
        (ax,) = _axes(fig.left)
        assert ax.axis_label == hostile
        # The default axis's ticks (WP-30 P1.3a), not #9999999.
        assert "dash_default" in ax.ticker.tags
        assert "dash_count:9999999" not in ax.ticker.tags


class TestTheLoneAxisRewrite:
    """_dash_lone_second_axes, the one place both modes read it from."""

    def test_the_callers_spec_is_not_modified(self):
        import dash_render as _dr
        spec = {"graphs": [{"plots": [{"type": "scatter", "yvar": "y",
                                       "xvar": "x",
                                       "options": {"yaxis": "2"}}],
                            "graph_options": {"ytitle2": "T"}}]}
        before = json.dumps(spec, sort_keys=True)
        out = _dr._dash_lone_second_axes(spec)
        assert json.dumps(spec, sort_keys=True) == before
        g = out["graphs"][0]
        assert "yaxis" not in g["plots"][0]["options"]
        assert g["graph_options"]["ytitle"] == "T"
        assert "ytitle2" not in g["graph_options"]

    def test_an_empty_second_title_is_moved_and_removes_the_title(self):
        """WP-28 B6: ytitle2("") on a lone yaxis(2) graph is moved (a raw
        "" is not blank) and removes the one axis's title, both modes."""
        for mode in _LONE_MODES:
            fig = _lone_figure(mode, _LONE, {"name": "fig1", "ytitle2": '""'})
            assert [a.axis_label or "" for a in _axes(fig.left)] == [""]

    def test_a_mixed_graph_is_left_alone(self):
        import dash_render as _dr
        spec = {"graphs": [{"plots": [
            {"type": "scatter", "yvar": "y", "xvar": "x", "options": {}},
            {"type": "scatter", "yvar": "z", "xvar": "x",
             "options": {"yaxis": "2"}}],
            "graph_options": {"ytitle2": "T"}}]}
        assert _dr._dash_lone_second_axes(spec) == spec

    @pytest.mark.parametrize("bad", [None, [], "x", {"graphs": "x"},
                                     {"graphs": [None, 3, {"plots": "x"}]},
                                     {"graphs": [{"plots": [None, 1]}]},
                                     {"graphs": [{"plots": [
                                         {"options": "yaxis(2)"}]}]}])
    def test_malformed_specs_pass_through(self, bad):
        """Adversarial: a hand-written spec of the wrong shape is returned
        as it came, for the loaders' own checks to refuse."""
        import dash_render as _dr
        assert _dr._dash_lone_second_axes(bad) == bad

    def test_many_graphs_cost_one_pass(self):
        """Resource: the rewrite is linear in the spec.  Flipped
        (22oct2026): a two-second bound for 2,000 graphs of 50 layers failed
        on a loaded machine (2.9 s); linear is measured as a ratio instead --
        2,000 graphs take under 8 times what 500 take (linear is about 4,
        quadratic about 16), with 50 ms of slack and a 20-second ceiling.
        Each size keeps its best of three runs (30oct2026: one pause on a
        loaded gate made 2,000 graphs take 28 times what 500 took)."""
        import time
        import dash_render as _dr
        g = {"plots": [{"type": "scatter", "yvar": "y", "xvar": "x",
                        "options": {"yaxis": "2"}}] * 50,
             "graph_options": {}}
        secs = {}
        for n in (500, 2000):
            runs = []
            for _ in range(3):
                t0 = time.perf_counter()
                out = _dr._dash_lone_second_axes({"graphs": [g] * n})
                runs.append(time.perf_counter() - t0)
            secs[n] = min(runs)
        assert secs[2000] < 8 * secs[500] + 0.05, secs
        assert secs[2000] < 20, secs
        assert all("yaxis" not in p["options"]
                   for gg in out["graphs"] for p in gg["plots"])
