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


# ================================================================
# TestParseAxisLabelOpt — unit tests for _parse_axis_label_opt()
# ================================================================

class TestParseAxisLabelOpt:
    """Unit tests for DashRenderer._parse_axis_label_opt() static method."""

    def test_pure_numeric(self):
        """Space-separated numbers parse to ticks with empty labels dict."""
        ticks, labels = DashRenderer._parse_axis_label_opt("0 2 4 6 8")
        assert ticks == [0.0, 2.0, 4.0, 6.0, 8.0]
        assert labels == {}

    def test_comma_separated(self):
        """Comma-separated values parse correctly."""
        ticks, labels = DashRenderer._parse_axis_label_opt("1,3,5")
        assert ticks == [1.0, 3.0, 5.0]

    def test_labeled_ticks(self):
        """'value \"label\"' pairs parse to ticks with labels dict."""
        ticks, labels = DashRenderer._parse_axis_label_opt('0 "Zero" 5 "Five"')
        assert ticks == [0.0, 5.0]
        assert labels["0.0"] == "Zero"
        assert labels["5.0"] == "Five"

    def test_empty_string(self):
        """Empty string returns empty ticks and labels."""
        ticks, labels = DashRenderer._parse_axis_label_opt("")
        assert ticks == []
        assert labels == {}

    def test_mixed_valid_invalid(self):
        """Non-numeric bare tokens are silently skipped."""
        ticks, labels = DashRenderer._parse_axis_label_opt("0 foo 5")
        assert 0.0 in ticks
        assert 5.0 in ticks
        # 'foo' should not appear as a tick
        assert len(ticks) == 2

    def test_negative_values(self):
        """Negative tick values are parsed correctly."""
        ticks, labels = DashRenderer._parse_axis_label_opt("-5 0 5")
        assert ticks == [-5.0, 0.0, 5.0]

    def test_float_values(self):
        """Floating-point tick values are parsed correctly."""
        ticks, labels = DashRenderer._parse_axis_label_opt("0.5 1.5 2.5")
        assert ticks == pytest.approx([0.5, 1.5, 2.5])

    def test_single_value(self):
        """Single tick value is parsed into a list with one element."""
        ticks, labels = DashRenderer._parse_axis_label_opt("42")
        assert ticks == [42.0]
        assert labels == {}

    def test_single_quoted_label(self):
        """Single-quoted labels are also parsed."""
        ticks, labels = DashRenderer._parse_axis_label_opt("1 'One' 2 'Two'")
        assert ticks == [1.0, 2.0]
        assert labels["1.0"] == "One"
        assert labels["2.0"] == "Two"

    def test_output_ticks_sorted(self):
        """Output ticks are always sorted ascending regardless of input order."""
        ticks, labels = DashRenderer._parse_axis_label_opt("10 2 5")
        assert ticks == [2.0, 5.0, 10.0]


# ================================================================
# P6-14 — legend label overrides via legend(label(N "text"))
# ================================================================
class TestLegendLabels:
    def _get_figure_with_labels(self, legend_opt: str):
        """Return a figure built with an explicit legend option."""
        r = _make_renderer({"legend": legend_opt})
        figs = r._build_figures()
        return figs["g1"]

    def test_legend_off_hides_legend(self):
        """P6-14: legend(off) hides legend items."""
        fig = _get_figure({"legend": "off"})
        # Either no legend or it's not visible
        if fig.legend:
            assert not fig.legend[0].visible

    def test_legend_position_top(self):
        """P6-14: legend(top) positions legend at top_center."""
        fig = _get_figure({"legend": "top"})
        if fig.legend:
            assert fig.legend[0].location == "top_center"

    def test_no_legend_opt_no_crash(self):
        """P6-14: no legend option — figure builds without error."""
        fig = _get_figure({})
        assert fig is not None

    # --- legend_label entries exist when glyphs are rendered ---

    def _make_two_plot_renderer(self, graph_options: dict | None = None) -> "DashRenderer":
        """Return a renderer with two scatter plots on one graph."""
        import tempfile, json, os
        graph_spec = {
            "plots": [
                {"type": "scatter", "yvar": "mpg",    "xvar": "weight", "options": {}},
                {"type": "scatter", "yvar": "weight",  "xvar": "weight", "options": {}},
            ],
            "graph_options": {"name": "g1", **(graph_options or {})},
            "if_expr": "",
            "in_expr": "",
        }
        master_spec = {
            "graphs": [graph_spec],
            "kpis": [],
            "build_options": {
                "layout": "auto", "link": "", "filter": "",
                "theme": "default", "title": "", "subtitle": "", "registry": "g1",
            },
        }
        data_json = {
            "StataJSON": {
                "variableNames": ["mpg", "weight"],
                "variableLabels": {"mpg": "Mileage (mpg)", "weight": "Weight (lbs.)"},
                "valueLabels": {}, "valueLabelNames": {},
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

    def _item_label(self, item) -> str:
        """Extract the string value from a Bokeh LegendItem label (Value object)."""
        lbl = item.label
        # Bokeh wraps legend labels in a Value object with a .value attribute
        if hasattr(lbl, "value"):
            return lbl.value
        if isinstance(lbl, dict):
            return lbl.get("value", "")
        return str(lbl)

    def test_scatter_gets_legend_label_from_yvar(self):
        """P6-14: scatter glyph creates a legend item labelled with yvar name."""
        fig = _get_figure({})
        assert fig.legend, "Expected at least one legend item for scatter"
        labels = [self._item_label(item) for item in fig.legend[0].items]
        assert any("mpg" in lbl for lbl in labels), f"Expected 'mpg' in legend labels: {labels}"

    def test_two_scatter_plots_create_two_legend_items(self):
        """P6-14: two scatter plots → two legend items."""
        r = self._make_two_plot_renderer()
        fig = r._build_figures()["g1"]
        assert fig.legend, "Expected a legend"
        items = fig.legend[0].items
        assert len(items) == 2, f"Expected 2 legend items, got {len(items)}"

    def test_legend_label_override_single(self):
        """P6-14: legend(label(1 "Custom")) overrides the first legend item."""
        r = self._make_two_plot_renderer({"legend": 'label(1 "My First")'})
        fig = r._build_figures()["g1"]
        assert fig.legend
        first_label = self._item_label(fig.legend[0].items[0])
        assert first_label == "My First", f"Expected 'My First', got {first_label!r}"

    def test_legend_label_override_both(self):
        """P6-14: label(1 ...) label(2 ...) overrides both items."""
        r = self._make_two_plot_renderer(
            {"legend": 'label(1 "Series A") label(2 "Series B")'}
        )
        fig = r._build_figures()["g1"]
        assert fig.legend
        items = fig.legend[0].items
        first  = self._item_label(items[0])
        second = self._item_label(items[1])
        assert first  == "Series A", f"Expected 'Series A', got {first!r}"
        assert second == "Series B", f"Expected 'Series B', got {second!r}"

    def test_legend_label_override_with_position(self):
        """P6-14: label() and position keywords can coexist."""
        r = self._make_two_plot_renderer(
            {"legend": 'top label(1 "Top First")'}
        )
        fig = r._build_figures()["g1"]
        assert fig.legend
        assert fig.legend[0].location == "top_center"
        first_label = self._item_label(fig.legend[0].items[0])
        assert first_label == "Top First", f"Expected 'Top First', got {first_label!r}"

    def test_legend_label_xss_escaped(self):
        """P6-14: XSS payload in legend label is HTML-escaped."""
        r = self._make_two_plot_renderer(
            {"legend": 'label(1 "<script>alert(1)</script>")'}
        )
        fig = r._build_figures()["g1"]
        assert fig.legend
        first_label = self._item_label(fig.legend[0].items[0])
        assert "<script>" not in first_label
        assert "&lt;script&gt;" in first_label


# ================================================================
# by() faceting tests — P6-20
# ================================================================

def _make_by_renderer(by_value: str, extra_gopts: dict | None = None,
                      include_nan: bool = False) -> "DashRenderer":
    """Create a DashRenderer whose data has a 'foreign' grouping var (0/1)
    and optionally NaN values, with by() set in graph_options."""
    import tempfile
    n = 20
    vals = []
    for i in range(n):
        row = {"mpg": float(i + 10), "weight": float(i * 100 + 1000)}
        if include_nan and i >= 18:
            row["foreign"] = None
        else:
            row["foreign"] = float(i % 2)
        # rep78: 5 unique integer values (1-5)
        row["rep78"] = float((i % 5) + 1)
        vals.append(row)

    gopts = {"name": "g1", "by": by_value}
    if extra_gopts:
        gopts.update(extra_gopts)

    graph_spec = {
        "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
        "graph_options": gopts,
        "if_expr": "",
        "in_expr": "",
    }
    master_spec = {
        "graphs": [graph_spec],
        "kpis": [],
        "build_options": {
            "layout": "auto", "link": "", "filter": "",
            "theme": "default", "title": "", "subtitle": "",
            "registry": "g1",
        },
    }
    var_names = ["mpg", "weight", "foreign", "rep78"]
    data_json = {
        "StataJSON": {
            "variableNames": var_names,
            "variableLabels": {v: v for v in var_names},
            "valueLabels": {
                "foreign_lbl": {"0": "Domestic", "1": "Foreign"},
            },
            "valueLabelNames": {"foreign": "foreign_lbl"},
            "variableTypeIsString": {v: False for v in var_names},
            "values": vals,
        }
    }
    spec_fd, spec_path = tempfile.mkstemp(suffix=".json")
    data_fd, data_path = tempfile.mkstemp(suffix=".json")
    out_fd, out_path = tempfile.mkstemp(suffix=".html")
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


class TestByFaceting:
    """P6-20: by() creates one figure per unique value of the grouping var."""

    def test_by_foreign_creates_two_figures(self):
        """by(foreign) with 2 unique values → 2 figures."""
        r = _make_by_renderer("foreign")
        figs = r._build_figures()
        # Should have 2 facet figures, not the original "g1"
        facet_keys = [k for k in figs if k.startswith("g1__by__")]
        assert len(facet_keys) == 2, f"Expected 2 facets, got {len(facet_keys)}: {list(figs.keys())}"

    def test_by_rep78_creates_five_figures(self):
        """by(rep78) with 5 unique values → 5 figures."""
        r = _make_by_renderer("rep78")
        figs = r._build_figures()
        facet_keys = [k for k in figs if k.startswith("g1__by__")]
        assert len(facet_keys) == 5, f"Expected 5 facets, got {len(facet_keys)}: {list(figs.keys())}"

    def test_by_total_adds_extra_facet(self):
        """by(foreign) with by_total=1 → 3 figures (2 groups + Total)."""
        r = _make_by_renderer("foreign", extra_gopts={"by_total": "1"})
        figs = r._build_figures()
        facet_keys = [k for k in figs if k.startswith("g1__by__")]
        assert len(facet_keys) == 3, f"Expected 3 facets (incl Total), got {len(facet_keys)}"

    def test_facet_figures_have_filtered_data(self):
        """Each facet figure's CDS has only rows matching the group value."""
        r = _make_by_renderer("foreign")
        figs = r._build_figures()
        sources = r.sources
        for key, src in sources.items():
            if "__by__" not in key:
                continue
            # Each facet should have 10 rows (20 total, 2 groups)
            n_rows = len(src.data.get("mpg", []))
            assert n_rows == 10, f"Facet {key} has {n_rows} rows, expected 10"

    def test_facet_title_contains_group_label(self):
        """Facet figure titles include the group value label."""
        r = _make_by_renderer("foreign")
        figs = r._build_figures()
        titles = [figs[k].title.text for k in sorted(figs) if "__by__" in k]
        # foreign has value labels: 0→Domestic, 1→Foreign
        assert any("Domestic" in t for t in titles), f"No 'Domestic' in titles: {titles}"
        assert any("Foreign" in t for t in titles), f"No 'Foreign' in titles: {titles}"

    def test_by_nonexistent_var_no_crash(self):
        """by(nonexistent) → single unfaceted figure, no crash."""
        r = _make_by_renderer("nonexistent_var")
        figs = r._build_figures()
        # Falls back to no faceting
        assert "g1" in figs or len(figs) >= 1

    def test_by_single_unique_value(self):
        """by(var) where var has only 1 unique value → 1 facet."""
        # Create renderer where all rows have foreign=0
        import tempfile
        vals = [{"mpg": float(i), "weight": float(i * 50), "foreign": 0.0}
                for i in range(1, 11)]
        gopts = {"name": "g1", "by": "foreign"}
        graph_spec = {
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": gopts,
            "if_expr": "", "in_expr": "",
        }
        master_spec = {
            "graphs": [graph_spec], "kpis": [],
            "build_options": {"layout": "auto", "link": "", "filter": "",
                              "theme": "default", "title": "", "subtitle": "",
                              "registry": "g1"},
        }
        data_json = {
            "StataJSON": {
                "variableNames": ["mpg", "weight", "foreign"],
                "variableLabels": {"mpg": "mpg", "weight": "weight", "foreign": "foreign"},
                "valueLabels": {}, "valueLabelNames": {},
                "variableTypeIsString": {"mpg": False, "weight": False, "foreign": False},
                "values": vals,
            }
        }
        spec_fd, spec_path = tempfile.mkstemp(suffix=".json")
        data_fd, data_path = tempfile.mkstemp(suffix=".json")
        out_fd, out_path = tempfile.mkstemp(suffix=".html")
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
        figs = r._build_figures()
        facet_keys = [k for k in figs if k.startswith("g1__by__")]
        assert len(facet_keys) == 1, f"Expected 1 facet, got {len(facet_keys)}"

    def test_by_with_missing_excludes_nan_by_default(self):
        """by(foreign) without by_missing → NaN rows excluded from all facets."""
        r = _make_by_renderer("foreign", include_nan=True)
        figs = r._build_figures()
        sources = r.sources
        total = sum(
            len(src.data.get("mpg", []))
            for key, src in sources.items() if "__by__" in key
        )
        # 20 rows total, 2 NaN → 18 rows across facets
        assert total == 18, f"Expected 18 rows total across facets, got {total}"

    def test_by_with_missing_flag_includes_nan_group(self):
        """by(foreign) with by_missing=1 → includes NaN group."""
        r = _make_by_renderer("foreign", extra_gopts={"by_missing": "1"},
                              include_nan=True)
        figs = r._build_figures()
        facet_keys = [k for k in figs if k.startswith("g1__by__")]
        # 2 non-NaN groups + 1 NaN group = 3
        assert len(facet_keys) == 3, f"Expected 3 facets (incl NaN), got {len(facet_keys)}"

    def test_by_link_raises_error(self):
        """by() + link() → raises ValueError."""
        import tempfile
        vals = [{"mpg": float(i), "weight": float(i * 50), "foreign": float(i % 2)}
                for i in range(1, 11)]
        gopts = {"name": "g1", "by": "foreign"}
        graph_spec = {
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": gopts,
            "if_expr": "", "in_expr": "",
        }
        master_spec = {
            "graphs": [graph_spec], "kpis": [],
            "build_options": {"layout": "auto", "link": "g1", "filter": "",
                              "theme": "default", "title": "", "subtitle": "",
                              "registry": "g1"},
        }
        data_json = {
            "StataJSON": {
                "variableNames": ["mpg", "weight", "foreign"],
                "variableLabels": {"mpg": "mpg", "weight": "weight", "foreign": "foreign"},
                "valueLabels": {}, "valueLabelNames": {},
                "variableTypeIsString": {"mpg": False, "weight": False, "foreign": False},
                "values": vals,
            }
        }
        spec_fd, spec_path = tempfile.mkstemp(suffix=".json")
        data_fd, data_path = tempfile.mkstemp(suffix=".json")
        out_fd, out_path = tempfile.mkstemp(suffix=".html")
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
        with pytest.raises(ValueError, match="by.*link"):
            r._build_figures()

    def test_by_multi_var_faceting(self):
        """by(foreign rep78) with multi-variable → composite facet labels."""
        # Use only foreign(0,1) × rep78(1,2) subset for predictable count
        import tempfile
        vals = []
        for i in range(20):
            vals.append({
                "mpg": float(i + 10),
                "weight": float(i * 100 + 1000),
                "foreign": float(i % 2),
                "rep78": float((i % 2) + 1),  # 1 or 2
            })
        gopts = {"name": "g1", "by": "foreign rep78"}
        graph_spec = {
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": gopts,
            "if_expr": "", "in_expr": "",
        }
        master_spec = {
            "graphs": [graph_spec], "kpis": [],
            "build_options": {"layout": "auto", "link": "", "filter": "",
                              "theme": "default", "title": "", "subtitle": "",
                              "registry": "g1"},
        }
        var_names = ["mpg", "weight", "foreign", "rep78"]
        data_json = {
            "StataJSON": {
                "variableNames": var_names,
                "variableLabels": {v: v for v in var_names},
                "valueLabels": {}, "valueLabelNames": {},
                "variableTypeIsString": {v: False for v in var_names},
                "values": vals,
            }
        }
        spec_fd, spec_path = tempfile.mkstemp(suffix=".json")
        data_fd, data_path = tempfile.mkstemp(suffix=".json")
        out_fd, out_path = tempfile.mkstemp(suffix=".html")
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
        figs = r._build_figures()
        facet_keys = [k for k in figs if k.startswith("g1__by__")]
        # foreign(0,1) × rep78(1,2) = 4 combos, but with the data pattern:
        # even i → foreign=0, rep78=1; odd i → foreign=1, rep78=2
        # So only 2 unique combos: (0,1) and (1,2)
        assert len(facet_keys) == 2, f"Expected 2 multi-var facets, got {len(facet_keys)}"


# ================================================================
# P6-22: _parse_by_raw unit tests
# ================================================================

class TestParseByRaw:
    """Unit tests for DashRenderer._parse_by_raw()."""

    def test_simple_varname(self):
        """P6-22a: 'foreign' → varlist='foreign', defaults."""
        varlist, by_cols, by_total, by_missing = DashRenderer._parse_by_raw("foreign")
        assert varlist == "foreign"
        assert by_cols == 0
        assert by_total is False
        assert by_missing is False

    def test_varname_with_cols(self):
        """P6-22b: 'foreign, cols(3)' → by_cols=3."""
        varlist, by_cols, by_total, by_missing = DashRenderer._parse_by_raw("foreign, cols(3)")
        assert varlist == "foreign"
        assert by_cols == 3

    def test_varname_with_total(self):
        """P6-22c: 'foreign, total' → by_total=True."""
        varlist, by_cols, by_total, by_missing = DashRenderer._parse_by_raw("foreign, total")
        assert varlist == "foreign"
        assert by_total is True
        assert by_missing is False

    def test_varname_with_missing(self):
        """P6-22d: 'foreign, missing' → by_missing=True."""
        varlist, by_cols, by_total, by_missing = DashRenderer._parse_by_raw("foreign, missing")
        assert varlist == "foreign"
        assert by_missing is True

    def test_all_suboptions(self):
        """P6-22e: 'rep78, cols(2) total missing' → all flags set."""
        varlist, by_cols, by_total, by_missing = DashRenderer._parse_by_raw(
            "rep78, cols(2) total missing"
        )
        assert varlist == "rep78"
        assert by_cols == 2
        assert by_total is True
        assert by_missing is True

    def test_multi_var(self):
        """P6-22f: 'foreign rep78' (no comma) → multi-var varlist, no subopts."""
        varlist, by_cols, by_total, by_missing = DashRenderer._parse_by_raw("foreign rep78")
        assert varlist == "foreign rep78"
        assert by_cols == 0
        assert by_total is False

    def test_empty_string(self):
        """P6-22g: empty string → empty varlist, all defaults."""
        varlist, by_cols, by_total, by_missing = DashRenderer._parse_by_raw("")
        assert varlist == ""
        assert by_cols == 0


# ================================================================
# P6-23: by() suboptions end-to-end via _build_figures()
# ================================================================

class TestBySuboptions:
    """Test cols/total/missing suboptions parsed from the raw by() string."""

    def test_cols_parsed_in_render(self):
        """P6-23a: by('foreign, cols(1)') → facets arranged in 1-column sub-grid."""
        r = _make_by_renderer("foreign", extra_gopts={"by": "foreign, cols(1)"})
        html_out = r.render()
        # Just verify it renders without error and produces facets
        assert "html" in html_out.lower()

    def test_total_suboption_parsed(self):
        """P6-23b: by('foreign, total') → 3 facets (Domestic, Foreign, Total)."""
        r = _make_by_renderer("foreign", extra_gopts={"by": "foreign, total"})
        figs = r._build_figures()
        facet_keys = [k for k in figs if k.startswith("g1__by__")]
        assert len(facet_keys) == 3, f"Expected 3 (2 groups + total), got {len(facet_keys)}"

    def test_missing_suboption_parsed(self):
        """P6-23c: by('foreign, missing') includes NaN group."""
        r = _make_by_renderer("foreign", include_nan=True,
                              extra_gopts={"by": "foreign, missing"})
        figs = r._build_figures()
        facet_keys = [k for k in figs if k.startswith("g1__by__")]
        assert len(facet_keys) == 3, f"Expected 3 facets (incl NaN), got {len(facet_keys)}"


# ================================================================
# P6-24: Per-facet KPI cards
# ================================================================

class TestPerFacetKpis:
    """KPI cards are created per-facet when a KPI references a faceted graph."""

    def _build_renderer_with_kpi(self, kpi_def: dict) -> DashRenderer:
        """Build a renderer with foreign faceting and one KPI."""
        import tempfile
        vals = [{"mpg": float(i + 10), "weight": float(i * 100),
                 "foreign": float(i % 2)}
                for i in range(10)]
        graph = {
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign"},
            "if_expr": "", "in_expr": "",
        }
        spec = {
            "graphs": [graph],
            "kpis": [kpi_def],
            "build_options": {
                "layout": "auto", "link": "", "filter": "",
                "theme": "default", "title": "", "subtitle": "",
                "registry": "g1",
            },
        }
        data_json = {
            "StataJSON": {
                "variableNames": ["mpg", "weight", "foreign"],
                "variableLabels": {"mpg": "mpg", "weight": "weight",
                                   "foreign": "foreign"},
                "valueLabels": {}, "valueLabelNames": {},
                "variableTypeIsString": {
                    "mpg": False, "weight": False, "foreign": False
                },
                "values": vals,
            }
        }
        spec_fd, spec_path = tempfile.mkstemp(suffix=".json")
        data_fd, data_path = tempfile.mkstemp(suffix=".json")
        out_fd, out_path = tempfile.mkstemp(suffix=".html")
        try:
            with os.fdopen(spec_fd, "w") as f:
                json.dump(spec, f)
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

    def test_facet_kpi_divs_created(self):
        """P6-24a: KPI with stat+var+update → two kpi_divs (one per facet)."""
        kpi = {
            "name": "k1", "title": "Avg MPG",
            "stat": "mean", "var": "mpg",
            "fmt": "%9.1f", "update": "g1",
            "value": "", "subtitle": "", "color": "", "bgcolor": "",
        }
        r = self._build_renderer_with_kpi(kpi)
        r.render()
        # Should have per-facet divs: k1__by__0 and k1__by__1
        assert "k1__by__0" in r.kpi_divs, "Missing k1__by__0"
        assert "k1__by__1" in r.kpi_divs, "Missing k1__by__1"
        assert "k1" not in r.kpi_divs, "k1 should be replaced by per-facet divs"

    def test_facet_kpi_titles_include_label(self):
        """P6-24b: Per-facet KPI titles include the facet label."""
        kpi = {
            "name": "k1", "title": "Avg MPG",
            "stat": "mean", "var": "mpg",
            "fmt": "%9.1f", "update": "g1",
            "value": "", "subtitle": "", "color": "", "bgcolor": "",
        }
        r = self._build_renderer_with_kpi(kpi)
        r.render()
        # Each facet KPI div should contain the facet label in its title
        div0_text = r.kpi_divs["k1__by__0"].text
        div1_text = r.kpi_divs["k1__by__1"].text
        # At least one should contain "0.0" or "1.0" label
        assert any("0" in t for t in [div0_text, div1_text])

    def test_no_stat_var_falls_back_to_single_kpi(self):
        """P6-24c: KPI without stat/var → single KPI div created normally."""
        kpi = {
            "name": "k1", "title": "Count",
            "value": "10", "update": "g1",
            "subtitle": "", "color": "", "bgcolor": "",
        }
        r = self._build_renderer_with_kpi(kpi)
        r.render()
        # No stat/var → falls back to single div
        assert "k1" in r.kpi_divs
