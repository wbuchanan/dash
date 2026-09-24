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
        y2_renderers = [r for r in fig.renderers
                        if getattr(r, "y_range_name", None) == "y2"]
        assert len(y2_renderers) >= 1

    def test_primary_y_axis_renderer_unchanged(self):
        """DAX-04: renderers for primary axis keep default y_range_name."""
        plots = [
            {"type": "scatter", "yvar": "y1", "xvar": "x", "options": {}},
            {"type": "line",    "yvar": "y2", "xvar": "x", "options": {"yaxis": "2"}},
        ]
        fig = self._get_fig(plots)
        primary_renderers = [r for r in fig.renderers
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
        """DAX-07: ytitle2 option sets axis_label on the right axis."""
        plots = [
            {"type": "line", "yvar": "y2", "xvar": "x", "options": {"yaxis": "2"}},
        ]
        graph_opts = {"name": "fig1", "ytitle2": "Secondary Y"}
        fig = self._get_fig(plots, graph_opts)
        # The right-side axis should have the label
        right_axes = [ax for ax in fig.right
                      if hasattr(ax, "axis_label")]
        assert any("Secondary Y" in ax.axis_label for ax in right_axes)

    def test_ylabel2_custom_ticks(self):
        """DAX-08: ylabel2 option applies FixedTicker to secondary y-axis."""
        from bokeh.models.tickers import FixedTicker
        plots = [
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
        y2_renderers = [r for r in fig.renderers
                        if getattr(r, "y_range_name", None) == "y2"]
        assert len(y2_renderers) >= 2
        # Layer by layer, not by count: ">= 2" held just as well with the
        # primary layer moved to y2 too (three).  One renderer per layer
        # here, measured 24sep2026: the y1 scatter stays on the default
        # range, the y2 line and the y3 scatter are on y2.
        placed = sorted((r.glyph.y, r.y_range_name) for r in fig.renderers)
        assert placed == [("y1", "default"), ("y2", "y2"), ("y3", "y2")], (
            placed
        )

    def test_single_right_axis_with_multiple_secondary_layers(self):
        """DAX-11: only one right-side axis added, not one per layer."""
        plots = [
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
