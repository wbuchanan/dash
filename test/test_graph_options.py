"""
test_graph_options.py
Tests for graph-level options applied by _make_figure():
xtitle, ytitle, aspectratio, legend, note, caption.

Tests: P6-01 through P6-12

Run with:  pytest test/test_graph_options.py -v
"""
import sys
import os
import json
import tempfile
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dash_render import DashRenderer


# ================================================================
# Helpers
# ================================================================

def _make_graph_spec(name: str, ptype: str = "scatter",
                     yvar: str = "mpg", xvar: str = "weight",
                     graph_options: dict | None = None) -> dict:
    return {
        "plots": [{"type": ptype, "yvar": yvar, "xvar": xvar, "options": {}}],
        "graph_options": {"name": name, **(graph_options or {})},
        "if_expr": "",
        "in_expr": "",
    }


def _make_renderer(graph_options: dict | None = None) -> DashRenderer:
    """Create a minimal DashRenderer with one scatter graph."""
    graphs = [_make_graph_spec("g1", graph_options=graph_options)]
    master_spec = {
        "graphs": graphs,
        "kpis": [],
        "build_options": {
            "layout": "auto",
            "link": "",
            "filter": "",
            "theme": "default",
            "title": "",
            "subtitle": "",
            "registry": "g1",
        },
    }
    data_json = {
        "StataJSON": {
            "variableNames": ["mpg", "weight"],
            "variableLabels": {"mpg": "Mileage (mpg)", "weight": "Weight (lbs.)"},
            "valueLabels": {},
            "valueLabelNames": {},
            "variableTypeIsString": {"mpg": False, "weight": False},
            "values": [{"mpg": float(i), "weight": float(i * 50)} for i in range(1, 21)],
        }
    }
    spec_fd, spec_path = tempfile.mkstemp(suffix=".json")
    data_fd, data_path = tempfile.mkstemp(suffix=".json")
    out_fd,  out_path  = tempfile.mkstemp(suffix=".html")
    try:
        with os.fdopen(spec_fd, "w") as f:
            json.dump(master_spec, f)
        with os.fdopen(data_fd, "w") as f:
            json.dump(data_json, f)
        os.close(out_fd)
        r = DashRenderer(spec_path, data_path, out_path)
    finally:
        for p in (spec_path, data_path, out_path):
            try:
                os.unlink(p)
            except OSError:
                pass
    return r


def _get_figure(graph_options: dict | None = None):
    """Return the Bokeh figure produced for one scatter graph."""
    r = _make_renderer(graph_options)
    figs = r._build_figures()
    return figs["g1"]


# ================================================================
# P6-01 — xtitle applied to x_axis_label
# ================================================================
class TestXtitle:
    def test_xtitle_sets_x_axis_label(self):
        """P6-01: xtitle option overrides auto x-axis label."""
        fig = _get_figure({"xtitle": "Custom X Axis"})
        assert fig.xaxis.axis_label == "Custom X Axis", (
            f"Expected 'Custom X Axis', got '{fig.xaxis.axis_label}'"
        )

    def test_xtitle_xss_escaped(self):
        """P6-01: XSS in xtitle is HTML-escaped."""
        fig = _get_figure({"xtitle": "<script>alert(1)</script>"})
        assert "<script>" not in fig.xaxis.axis_label

    def test_no_xtitle_uses_variable_label(self):
        """P6-01: when xtitle absent, axis label falls back to variable label."""
        fig = _get_figure({})
        # Variable label for 'weight' is 'Weight (lbs.)'
        assert "weight" in fig.xaxis.axis_label.lower() or "weight" in fig.xaxis.axis_label


# ================================================================
# P6-02 — ytitle applied to y_axis_label
# ================================================================
class TestYtitle:
    def test_ytitle_sets_y_axis_label(self):
        """P6-02: ytitle option overrides auto y-axis label."""
        fig = _get_figure({"ytitle": "Custom Y Axis"})
        assert fig.yaxis.axis_label == "Custom Y Axis", (
            f"Expected 'Custom Y Axis', got '{fig.yaxis.axis_label}'"
        )

    def test_ytitle_xss_escaped(self):
        """P6-02: XSS in ytitle is HTML-escaped."""
        fig = _get_figure({"ytitle": "<script>evil()</script>"})
        assert "<script>" not in fig.yaxis.axis_label

    def test_no_ytitle_uses_variable_label(self):
        """P6-02: when ytitle absent, axis label falls back to variable label."""
        fig = _get_figure({})
        assert "mpg" in fig.yaxis.axis_label.lower() or "mileage" in fig.yaxis.axis_label.lower()


# ================================================================
# P6-03 — aspectratio applied to figure
# ================================================================
class TestAspectRatio:
    def test_aspectratio_applied(self):
        """P6-03: aspectratio option is forwarded to Bokeh figure."""
        fig = _get_figure({"aspectratio": "1.5"})
        assert fig.aspect_ratio == pytest.approx(1.5), (
            f"Expected aspect_ratio=1.5, got {fig.aspect_ratio}"
        )

    def test_aspectratio_invalid_ignored(self):
        """P6-03: invalid aspectratio does not raise; figure still created."""
        fig = _get_figure({"aspectratio": "not_a_number"})
        assert fig is not None

    def test_no_aspectratio_is_none(self):
        """P6-03: without aspectratio option, figure.aspect_ratio is None."""
        fig = _get_figure({})
        assert fig.aspect_ratio is None


# ================================================================
# P6-04 — note annotation added to figure
# ================================================================
class TestNote:
    def test_note_creates_label(self):
        """P6-04: note option creates a Label annotation on the figure."""
        from bokeh.models import Label
        fig = _get_figure({"note": "This is a note"})
        labels = [r for r in fig.below if isinstance(r, Label)]
        assert len(labels) >= 1, "Expected at least one Label in fig.below"
        assert any("This is a note" in lbl.text for lbl in labels)

    def test_note_xss_escaped(self):
        """P6-04: XSS in note is HTML-escaped."""
        from bokeh.models import Label
        fig = _get_figure({"note": "<script>bad()</script>"})
        labels = [r for r in fig.below if isinstance(r, Label)]
        if labels:
            for lbl in labels:
                assert "<script>" not in lbl.text


# ================================================================
# P6-05 — caption annotation added to figure
# ================================================================
class TestCaption:
    def test_caption_creates_label(self):
        """P6-05: caption option creates a Label annotation on the figure."""
        from bokeh.models import Label
        fig = _get_figure({"caption": "Figure 1: Scatter"})
        labels = [r for r in fig.below if isinstance(r, Label)]
        assert any("Figure 1: Scatter" in lbl.text for lbl in labels)

    def test_both_note_and_caption(self):
        """P6-05: both note and caption can coexist."""
        from bokeh.models import Label
        fig = _get_figure({"note": "Note text", "caption": "Caption text"})
        labels = [r for r in fig.below if isinstance(r, Label)]
        assert len(labels) >= 2


# ================================================================
# P6-06 — legend off hides legend
# ================================================================
class TestLegend:
    def test_legend_off_hides(self):
        """P6-06: legend(off) sets legend.visible=False."""
        fig = _get_figure({"legend": "off"})
        # If there is a legend, it should be hidden
        if fig.legend:
            assert fig.legend[0].visible is False

    def test_no_legend_opt_does_not_crash(self):
        """P6-06: omitting legend option does not raise."""
        fig = _get_figure({})
        assert fig is not None


# ================================================================
# P6-07 — xline / yline reference lines
# ================================================================
def _get_spans(fig, dimension: str):
    """Return all Span objects in a figure (Bokeh adds them to fig.center)."""
    from bokeh.models import Span
    return [r for r in fig.center if isinstance(r, Span) and r.dimension == dimension]


class TestXlineYline:
    def test_xline_adds_span(self):
        """P6-07: xline option (string from parser) adds a vertical Span to the figure."""
        fig = _get_figure({"xline": "5"})
        spans = _get_spans(fig, "height")
        assert len(spans) >= 1, "xline should add at least one vertical Span"
        assert any(abs(s.location - 5.0) < 1e-9 for s in spans), (
            f"Expected vertical Span at 5.0, got: {[s.location for s in spans]}"
        )

    def test_xline_multi_values(self):
        """P6-07: xline with multiple space-separated values adds multiple Spans."""
        fig = _get_figure({"xline": "2 7 12"})
        spans = _get_spans(fig, "height")
        assert len(spans) >= 3, f"Expected >=3 xline Spans, got {len(spans)}"

    def test_yline_adds_span(self):
        """P6-07: yline option (string from parser) adds a horizontal Span to the figure."""
        fig = _get_figure({"yline": "10"})
        spans = _get_spans(fig, "width")
        assert len(spans) >= 1, "yline should add at least one horizontal Span"
        assert any(abs(s.location - 10.0) < 1e-9 for s in spans), (
            f"Expected horizontal Span at 10.0, got: {[s.location for s in spans]}"
        )

    def test_xline_invalid_value_no_crash(self):
        """P6-07: non-numeric xline value is silently ignored (no crash)."""
        fig = _get_figure({"xline": "notanumber"})
        assert fig is not None

    def test_xline_values_array_form(self):
        """P6-07: xline_values as list (legacy form) still works."""
        fig = _get_figure({"xline_values": [3.0, 6.0]})
        spans = _get_spans(fig, "height")
        assert len(spans) >= 2


# ================================================================
# P6-08 — subtitle annotation added above figure
# ================================================================
class TestSubtitle:
    def test_subtitle_creates_label_above(self):
        """P6-08: subtitle option creates a Label annotation in fig.above."""
        from bokeh.models import Label
        fig = _get_figure({"subtitle": "My subtitle"})
        labels = [r for r in fig.above if isinstance(r, Label)]
        assert len(labels) >= 1
        assert any("My subtitle" in lbl.text for lbl in labels)

    def test_subtitle_xss_escaped(self):
        """P6-08: XSS in subtitle is HTML-escaped."""
        from bokeh.models import Label
        fig = _get_figure({"subtitle": "<script>xss()</script>"})
        labels = [r for r in fig.above if isinstance(r, Label)]
        if labels:
            for lbl in labels:
                assert "<script>" not in lbl.text

    def test_no_subtitle_no_label(self):
        """P6-08: without subtitle option, no Label appears in fig.above."""
        from bokeh.models import Label
        fig = _get_figure({})
        labels = [r for r in fig.above if isinstance(r, Label)]
        assert len(labels) == 0


# ================================================================
# P6-13 — xlabel/ylabel custom axis tick values
# ================================================================
class TestXlabelYlabel:
    def test_xlabel_sets_fixed_ticks(self):
        """P6-13: xlabel option sets FixedTicker on x-axis."""
        from bokeh.models.tickers import FixedTicker
        fig = _get_figure({"xlabel": "0 2 4 6 8"})
        assert isinstance(fig.xaxis.ticker, FixedTicker), (
            f"Expected FixedTicker, got {type(fig.xaxis.ticker).__name__}"
        )
        assert sorted(fig.xaxis.ticker.ticks) == [0.0, 2.0, 4.0, 6.0, 8.0]

    def test_ylabel_sets_fixed_ticks(self):
        """P6-13: ylabel option sets FixedTicker on y-axis."""
        from bokeh.models.tickers import FixedTicker
        fig = _get_figure({"ylabel": "10 20 30"})
        assert isinstance(fig.yaxis.ticker, FixedTicker)
        assert sorted(fig.yaxis.ticker.ticks) == [10.0, 20.0, 30.0]

    def test_xlabel_comma_separated(self):
        """P6-13: xlabel with comma-separated values parses correctly."""
        from bokeh.models.tickers import FixedTicker
        fig = _get_figure({"xlabel": "1,3,5,7"})
        assert isinstance(fig.xaxis.ticker, FixedTicker)
        assert sorted(fig.xaxis.ticker.ticks) == [1.0, 3.0, 5.0, 7.0]

    def test_xlabel_invalid_no_crash(self):
        """P6-13: invalid xlabel value is silently ignored; no crash."""
        fig = _get_figure({"xlabel": "not_a_number"})
        assert fig is not None

    def test_no_xlabel_default_ticker(self):
        """P6-13: without xlabel, axis uses default (non-Fixed) ticker."""
        from bokeh.models.tickers import FixedTicker
        fig = _get_figure({})
        assert not isinstance(fig.xaxis.ticker, FixedTicker)

    def test_xlabel_with_labels(self):
        """P6-13: xlabel with 'value label' pairs sets tick labels via CustomJSTickFormatter."""
        from bokeh.models.tickers import FixedTicker
        from bokeh.models.formatters import CustomJSTickFormatter
        fig = _get_figure({"xlabel": '0 "Zero" 5 "Five" 10 "Ten"'})
        assert isinstance(fig.xaxis.ticker, FixedTicker)
        assert isinstance(fig.xaxis.formatter, CustomJSTickFormatter)
        # The formatter code or args must reference the label strings
        assert "Zero" in fig.xaxis.formatter.code or "Zero" in str(fig.xaxis.formatter.args)
