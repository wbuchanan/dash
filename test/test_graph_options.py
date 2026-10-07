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
# The parsers both render modes call: DashRenderer's _parse_axis_label_opt
# and _parse_by_raw only delegated to them (the latter dropping the list
# of unimplemented sub-options), only tests called them, and WP-26
# deleted them (24sep2026).
from dash_render import _dash_parse_axis_label_opt, _dash_parse_by


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
        # Bokeh draws an axis label as a CANVAS GLYPH, not as HTML, and
        # escapes it again on its way into the embedded JSON document.
        # Escaping it here made xtitle("R&D spend") read "R&amp;D spend"
        # on screen.  The model keeps the literal text; the guarantee
        # that matters -- nothing executable reaches the document -- is
        # asserted in test_axis_options.py.
        assert fig.xaxis.axis_label == "<script>alert(1)</script>"

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

    def test_ytitle_is_canvas_text_not_html(self):
        """P6-02: canvas glyph, not HTML -- see test_xtitle_xss_escaped."""
        fig = _get_figure({"ytitle": "<script>evil()</script>"})
        assert fig.yaxis.axis_label == "<script>evil()</script>"

    def test_no_ytitle_uses_variable_label(self):
        """P6-02: when ytitle absent, axis label falls back to variable label."""
        fig = _get_figure({})
        assert "mpg" in fig.yaxis.axis_label.lower() or "mileage" in fig.yaxis.axis_label.lower()


# ================================================================
# P6-03 — aspectratio applied to figure
# ================================================================
class TestAspectRatio:
    def test_aspectratio_is_inverted_for_bokeh(self):
        """P6-03: Stata's aspectratio is height/width; Bokeh's is width/height.

        dash forwarded the value unchanged, so every request came out upside
        down.  Measured in Stata on a 600x600 export: aspectratio(0.25)
        yields a plot region 542x152, i.e. height/width = 0.28.
        """
        fig = _get_figure({"aspectratio": "1.5"})
        assert fig.aspect_ratio == pytest.approx(1.0 / 1.5), (
            f"Expected aspect_ratio=1/1.5, got {fig.aspect_ratio}"
        )

    def test_aspectratio_invalid_ignored(self):
        """P6-03: invalid aspectratio does not raise; figure still created."""
        import warnings as _w
        with _w.catch_warnings(record=True):
            _w.simplefilter("always")
            fig = _get_figure({"aspectratio": "not_a_number"})
        assert fig is not None

    def test_no_aspectratio_falls_back_to_the_scheme(self):
        """P6-03: with no option, proportions come from the scheme's graphsize.

        This used to be None -- there was no way at all, by option, scheme or
        data, to influence a figure's proportions.
        """
        fig = _get_figure({})
        assert fig.aspect_ratio is not None
        assert fig.aspect_ratio == pytest.approx(5.5 / 4.0, rel=1e-6), (
            "s2color records graphsize x 5.5, graphsize y 4"
        )


# ================================================================
# P6-04 — note annotation added to figure
# ================================================================
class TestNote:
    def test_note_creates_label(self):
        """P6-04: note option creates a Label annotation on the figure."""
        # Flipped (WP-30 P1.2a): a Label was wrong because twoway places
        # the box by the scheme's clock, which S15 draws as a side-panel Title.
        from bokeh.models import Title
        fig = _get_figure({"note": "This is a note"})
        labels = [r for r in fig.below if isinstance(r, Title) and r is not fig.title]
        assert len(labels) >= 1, "Expected at least one Label in fig.below"
        assert any("This is a note" in lbl.text for lbl in labels)

    def test_note_is_canvas_text_not_html(self):
        """P6-04: a Label is drawn on the canvas, so its text stays literal.
        Flipped (WP-30 P1.2a): a Label was wrong because twoway places
        the box by the scheme's clock, which S15 draws as a side-panel Title.


        Escaping it turned note("R&D") into "R&amp;D" on screen.  Nothing
        executable reaches the document -- Bokeh escapes the model text again
        when it serialises it -- and that is asserted in test_axis_options.py.
        """
        from bokeh.models import Title
        fig = _get_figure({"note": "<script>bad()</script>"})
        labels = [r for r in fig.below if isinstance(r, Title) and r is not fig.title]
        assert labels, "note() drew no label"
        assert any(lbl.text == "<script>bad()</script>" for lbl in labels)


# ================================================================
# P6-05 — caption annotation added to figure
# ================================================================
class TestCaption:
    def test_caption_creates_label(self):
        """P6-05: caption option creates a Label annotation on the figure."""
        # Flipped (WP-30 P1.2a): a Label was wrong because twoway places
        # the box by the scheme's clock, which S15 draws as a side-panel Title.
        from bokeh.models import Title
        fig = _get_figure({"caption": "Figure 1: Scatter"})
        labels = [r for r in fig.below if isinstance(r, Title) and r is not fig.title]
        assert any("Figure 1: Scatter" in lbl.text for lbl in labels)

    def test_both_note_and_caption(self):
        """P6-05: both note and caption can coexist."""
        # Flipped (WP-30 P1.2a): a Label was wrong because twoway places
        # the box by the scheme's clock, which S15 draws as a side-panel Title.
        from bokeh.models import Title
        fig = _get_figure({"note": "Note text", "caption": "Caption text"})
        labels = [r for r in fig.below if isinstance(r, Title) and r is not fig.title]
        assert len(labels) >= 2
        # Two labels of any text passed: a caption drawn with the note's
        # text, say.  Measured 24sep2026: exactly these two, below.
        assert sorted(lbl.text for lbl in labels) == ["Caption text",
                                                      "Note text"]


# ================================================================
# P6-06 — legend off hides legend
# ================================================================
class TestLegend:
    def test_legend_off_hides(self):
        """P6-06: legend(off) sets legend.visible=False."""
        fig = _get_figure({"legend": "off"})
        # The figure keeps its one legend, hidden (measured 24sep2026); an
        # `if fig.legend:' passed a figure whose legend was dropped, which
        # hides nothing and leaves legend(on) nothing to show.
        assert len(fig.legend) == 1, len(fig.legend)
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
        # Three spans anywhere passed; one at each position asked for
        # (measured 24sep2026: 2, 7, 12, in order).
        assert [s.location for s in spans] == [2.0, 7.0, 12.0], (
            [s.location for s in spans])

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
        # At the two positions given, and no more (measured 24sep2026).
        assert [s.location for s in spans] == [3.0, 6.0], (
            [s.location for s in spans])


# ================================================================
# P6-08 — subtitle annotation added above figure
# ================================================================
class TestSubtitle:
    def test_subtitle_creates_label_above(self):
        """P6-08: subtitle option creates a Label annotation in fig.above."""
        # Flipped (WP-30 P1.2a): a Label was wrong because twoway places
        # the box by the scheme's clock, which S15 draws as a side-panel Title.
        from bokeh.models import Title
        fig = _get_figure({"subtitle": "My subtitle"})
        labels = [r for r in fig.above if isinstance(r, Title) and r is not fig.title]
        assert len(labels) >= 1
        assert any("My subtitle" in lbl.text for lbl in labels)

    def test_subtitle_is_canvas_text_not_html(self):
        """P6-08: canvas text stays literal -- see test_note_is_canvas_text."""
        # Flipped (WP-30 P1.2a): a Label was wrong because twoway places
        # the box by the scheme's clock, which S15 draws as a side-panel Title.
        from bokeh.models import Title
        fig = _get_figure({"subtitle": "<script>xss()</script>"})
        labels = [r for r in fig.above if isinstance(r, Title) and r is not fig.title]
        assert labels, "subtitle() drew no label"
        assert any(lbl.text == "<script>xss()</script>" for lbl in labels)

    def test_no_subtitle_no_label(self):
        """P6-08: without subtitle option, no Label appears in fig.above."""
        # Flipped (WP-30 P1.2a): a Label was wrong because twoway places
        # the box by the scheme's clock, which S15 draws as a side-panel Title.
        from bokeh.models import Title
        fig = _get_figure({})
        labels = [r for r in fig.above if isinstance(r, Title) and r is not fig.title]
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
# TestParseAxisLabelOpt -- unit tests for _dash_parse_axis_label_opt()
# ================================================================

class TestParseAxisLabelOpt:
    """Unit tests for _dash_parse_axis_label_opt(), the numlist reader of
    xlabel() and ylabel() both render modes run."""

    def test_pure_numeric(self):
        """Space-separated numbers parse to ticks with empty labels dict."""
        ticks, labels = _dash_parse_axis_label_opt("0 2 4 6 8")
        assert ticks == [0.0, 2.0, 4.0, 6.0, 8.0]
        assert labels == {}

    def test_comma_separated(self):
        """Comma-separated values parse correctly."""
        ticks, labels = _dash_parse_axis_label_opt("1,3,5")
        assert ticks == [1.0, 3.0, 5.0]

    def test_labeled_ticks(self):
        """'value \"label\"' pairs parse to ticks with labels dict."""
        ticks, labels = _dash_parse_axis_label_opt('0 "Zero" 5 "Five"')
        assert ticks == [0.0, 5.0]
        assert labels["0.0"] == "Zero"
        assert labels["5.0"] == "Five"

    def test_empty_string(self):
        """Empty string returns empty ticks and labels."""
        ticks, labels = _dash_parse_axis_label_opt("")
        assert ticks == []
        assert labels == {}

    def test_mixed_valid_invalid(self):
        """Non-numeric bare tokens are silently skipped."""
        ticks, labels = _dash_parse_axis_label_opt("0 foo 5")
        assert 0.0 in ticks
        assert 5.0 in ticks
        # 'foo' should not appear as a tick
        assert len(ticks) == 2

    def test_negative_values(self):
        """Negative tick values are parsed correctly."""
        ticks, labels = _dash_parse_axis_label_opt("-5 0 5")
        assert ticks == [-5.0, 0.0, 5.0]

    def test_float_values(self):
        """Floating-point tick values are parsed correctly."""
        ticks, labels = _dash_parse_axis_label_opt("0.5 1.5 2.5")
        assert ticks == pytest.approx([0.5, 1.5, 2.5])

    def test_single_value(self):
        """Single tick value is parsed into a list with one element."""
        ticks, labels = _dash_parse_axis_label_opt("42")
        assert ticks == [42.0]
        assert labels == {}

    def test_single_quoted_label(self):
        """A single quote is a character in Stata, not a string delimiter
        (WP-28 S14, GAPS2 B1; twoway refuses xlabel(2000 'a' 4000) with
        r(198), probe a1_single_quote): 'One' is a bare word, never a
        label."""
        bad = []
        ticks, labels = _dash_parse_axis_label_opt("1 'One' 2 'Two'", bad)
        assert ticks == [1.0, 2.0]
        assert labels == {}
        assert bad == ["'One'", "'Two'"]

    def test_output_ticks_sorted(self):
        """Output ticks are always sorted ascending regardless of input order."""
        ticks, labels = _dash_parse_axis_label_opt("10 2 5")
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

    def test_legend_top_is_not_a_placement(self):
        """P6-14 read legend(top) as top_center, INSIDE the plot.  twoway
        refuses legend(top) -- "option top not allowed", r(198) -- and
        dash.ado refuses it too (WP-23); a spec that carries it is named
        and not placed."""
        base = _get_figure({})
        fig = _get_figure({"legend": "top"})
        assert fig.legend
        assert fig.legend[0].location != "top_center"
        assert fig.legend[0].location == base.legend[0].location

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

    def test_label_names_the_key_number_not_the_position(self):
        """WP-28 B5: label(1) names plot 1 wherever order() puts it; it
        relabelled whatever order() had moved into the first row."""
        r = self._make_two_plot_renderer(
            {"legend": 'order(2 1) label(1 "Data")'})
        fig = r._build_figures()["g1"]
        items = fig.legend[0].items
        assert [self._item_label(i) for i in items] == [
            "Weight (lbs.)", "Data"]
        first_layer = [x for x in fig.renderers
                       if type(x.glyph).__name__ == "Scatter"][0]
        assert list(items[1].renderers) == [first_layer]

    def test_legend_label_override_with_position(self):
        """P6-14: label() and a placement can coexist -- position(12), the
        twoway spelling of the legend(top) this test used to write."""
        r = self._make_two_plot_renderer(
            {"legend": 'position(12) label(1 "Top First")'}
        )
        fig = r._build_figures()["g1"]
        assert fig.legend
        assert fig.legend[0] in fig.above
        first_label = self._item_label(fig.legend[0].items[0])
        assert first_label == "Top First", f"Expected 'Top First', got {first_label!r}"

    def test_legend_label_xss_is_carried_as_text(self):
        """P6-14, restated by WP-20: an XSS payload in a legend label reaches
        the LegendItem as the text the user wrote, never as markup.

        This used to assert the label was html-escaped.  BokehJS renders a
        LegendItem label as a DOM text node -- legend.js builds it as
        ``div({class: label}, `${label}`)'' and core/dom appends a string
        child with ``document.createTextNode'' (bokeh 3.8.0 and 3.9.0) -- so
        the escaping only put the entities on screen (``&lt;script&gt;'').
        The label is now raw; test_label_sinks.py pins that text rendering
        to the Bokeh versions where it was verified.
        """
        r = self._make_two_plot_renderer(
            {"legend": 'label(1 "<script>alert(1)</script>")'}
        )
        fig = r._build_figures()["g1"]
        assert fig.legend
        first_label = self._item_label(fig.legend[0].items[0])
        assert first_label == "<script>alert(1)</script>"
        assert "&lt;" not in first_label, "the label was escaped twice"


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
        # The line above held for any figure at all -- a facet included.
        # No faceting is the one figure under the graph's own name
        # (measured 24sep2026: ["g1"]; by(foreign) gives g1__by__0, 1).
        assert sorted(figs) == ["g1"], sorted(figs)

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

    def test_by_link_uses_shared_cds(self):
        """by() + link() now works: facet panels share a single CDS via CDSView."""
        import tempfile
        from bokeh.models import CDSView, BooleanFilter
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
            figs = r._build_figures()
        finally:
            for p in (spec_path, data_path, out_path):
                try:
                    os.unlink(p)
                except OSError:
                    pass
        # Should produce two facet figures (one per foreign value)
        facet_keys = [k for k in figs if "__by__" in k]
        assert len(facet_keys) == 2, f"Expected 2 facet panels, got {facet_keys}"
        # All panels must share the same ColumnDataSource
        sources = [figs[k].renderers[0].data_source for k in facet_keys
                   if figs[k].renderers]
        assert len(sources) == 2
        assert sources[0] is sources[1], "Facet panels must share a single CDS when linked"
        # Each panel's renderers should have a CDSView with BooleanFilter
        for fkey in facet_keys:
            fig = figs[fkey]
            for renderer in fig.renderers:
                assert hasattr(renderer, "view"), "Renderer must have a view"
                view = renderer.view
                assert isinstance(view, CDSView), f"Expected CDSView, got {type(view)}"
                assert isinstance(view.filter, BooleanFilter), (
                    f"Expected BooleanFilter on CDSView, got {type(view.filter)}"
                )

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
# P6-22: by() parser unit tests (_dash_parse_by)
# ================================================================

class TestParseByRaw:
    """Unit tests for _dash_parse_by(): varlist, cols(), total, missing."""

    def test_simple_varname(self):
        """P6-22a: 'foreign' → varlist='foreign', defaults."""
        varlist, by_cols, by_total, by_missing = _dash_parse_by("foreign")[:4]
        assert varlist == "foreign"
        assert by_cols == 0
        assert by_total is False
        assert by_missing is False

    def test_varname_with_cols(self):
        """P6-22b: 'foreign, cols(3)' → by_cols=3."""
        varlist, by_cols, by_total, by_missing = _dash_parse_by("foreign, cols(3)")[:4]
        assert varlist == "foreign"
        assert by_cols == 3

    def test_varname_with_total(self):
        """P6-22c: 'foreign, total' → by_total=True."""
        varlist, by_cols, by_total, by_missing = _dash_parse_by("foreign, total")[:4]
        assert varlist == "foreign"
        assert by_total is True
        assert by_missing is False

    def test_varname_with_missing(self):
        """P6-22d: 'foreign, missing' → by_missing=True."""
        varlist, by_cols, by_total, by_missing = _dash_parse_by("foreign, missing")[:4]
        assert varlist == "foreign"
        assert by_missing is True

    def test_all_suboptions(self):
        """P6-22e: 'rep78, cols(2) total missing' → all flags set."""
        varlist, by_cols, by_total, by_missing = _dash_parse_by(
            "rep78, cols(2) total missing"
        )[:4]
        assert varlist == "rep78"
        assert by_cols == 2
        assert by_total is True
        assert by_missing is True

    def test_multi_var(self):
        """P6-22f: 'foreign rep78' (no comma) → multi-var varlist, no subopts."""
        varlist, by_cols, by_total, by_missing = _dash_parse_by("foreign rep78")[:4]
        assert varlist == "foreign rep78"
        assert by_cols == 0
        assert by_total is False

    def test_empty_string(self):
        """P6-22g: empty string → empty varlist, all defaults."""
        varlist, by_cols, by_total, by_missing = _dash_parse_by("")[:4]
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
    """A KPI whose update() names a by() graph is still ONE card.

    These tests used to pin a card per panel (k1__by__0, k1__by__1) on the
    saved page -- the renderer read update(), whose values are filter,
    brush and both, as a graph's name.  The served app never built such
    cards, dash.ado never wrote such a spec, and a by() graph named
    ``filter`` split every default KPI on the saved page alone (measured
    23sep2026; test_keyword_names.py).  Restated to the one-card rule.
    """

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
        """P6-24a, restated: one card, under the KPI's own name."""
        kpi = {
            "name": "k1", "title": "Avg MPG",
            "stat": "mean", "var": "mpg",
            "fmt": "%9.1f", "update": "g1",
            "value": "", "subtitle": "", "color": "", "bgcolor": "",
        }
        r = self._build_renderer_with_kpi(kpi)
        r.render()
        assert list(r.kpi_divs) == ["k1"]

    def test_facet_kpi_titles_include_label(self):
        """P6-24b, restated: the card keeps its own title and shows the
        statistic over every row, as the served card does."""
        kpi = {
            "name": "k1", "title": "Avg MPG",
            "stat": "mean", "var": "mpg",
            "fmt": "%9.1f", "update": "g1",
            "value": "", "subtitle": "", "color": "", "bgcolor": "",
        }
        r = self._build_renderer_with_kpi(kpi)
        r.render()
        text = r.kpi_divs["k1"].text
        assert "Avg MPG" in text and "Avg MPG (" not in text
        assert ">14.5<" in text   # the mean of mpg 10, 11, ..., 19

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


# ================================================================
# P6-25 — xscale(reverse) / yscale(reverse) axis flipping
# ================================================================
class TestXscaleYscaleReverse:
    """xscale(reverse) and yscale(reverse) must flip the axis direction."""

    def test_xscale_reverse_flips_x_range(self):
        """P6-25a: xscale(reverse) must set fig.x_range.flipped = True."""
        fig = _get_figure({"xscale": "reverse"})
        assert getattr(fig.x_range, "flipped", False) is True

    def test_reverse_with_a_range_is_start_above_end(self):
        """WP-28 B2: reverse beside range() was dropped (a Range1d has no
        flipped); the hull is drawn high end first."""
        from bokeh.models import Range1d
        import dash_render as _dr
        fig = _get_figure({"yscale": "reverse range(0 50)"})
        assert isinstance(fig.y_range, Range1d)
        assert fig.y_range.start > fig.y_range.end
        assert _dr._dash_range_reversed(fig.y_range) is True

    def test_yscale_reverse_flips_y_range(self):
        """P6-25b: yscale(reverse) must set fig.y_range.flipped = True."""
        fig = _get_figure({"yscale": "reverse"})
        assert getattr(fig.y_range, "flipped", False) is True

    def test_xscale_log_reverse_both_applied(self):
        """P6-25c: xscale(log reverse) must produce log axis AND flipped = True."""
        fig = _get_figure({"xscale": "log reverse"})
        # Log axis is set via x_axis_type; verify the axis type name
        assert fig.xaxis[0].__class__.__name__ == "LogAxis"
        assert getattr(fig.x_range, "flipped", False) is True

    def test_xscale_reverse_order_independent(self):
        """P6-25d: xscale(reverse log) (reversed word order) must still flip the axis."""
        fig = _get_figure({"xscale": "reverse log"})
        assert getattr(fig.x_range, "flipped", False) is True

    def test_xscale_log_only_does_not_flip(self):
        """P6-25e: xscale(log) alone must NOT set flipped (regression guard)."""
        fig = _get_figure({"xscale": "log"})
        assert getattr(fig.x_range, "flipped", False) is False

    def test_yscale_log_only_does_not_flip(self):
        """P6-25e2: yscale(log) alone must NOT set flipped."""
        fig = _get_figure({"yscale": "log"})
        assert getattr(fig.y_range, "flipped", False) is False

    def test_no_scale_opts_no_flip(self):
        """P6-25f: No xscale/yscale options must leave flipped at default (False)."""
        fig = _get_figure({})
        assert getattr(fig.x_range, "flipped", False) is False
        assert getattr(fig.y_range, "flipped", False) is False


# ================================================================
# P6-30 — xlabel/ylabel angle() sub-option for tick label rotation
# ================================================================
class TestParseAxisAngle:
    """Unit tests for the _parse_axis_angle() module-level helper."""

    def test_no_angle_returns_none(self):
        from dash_render import _parse_axis_angle
        assert _parse_axis_angle("0 10 20") is None

    def test_empty_returns_none(self):
        from dash_render import _parse_axis_angle
        assert _parse_axis_angle("") is None

    def test_numeric_angle(self):
        import math
        from dash_render import _parse_axis_angle
        assert abs(_parse_axis_angle("0 10, angle(45)") - math.radians(45)) < 1e-9

    def test_angle_horizontal(self):
        from dash_render import _parse_axis_angle
        assert _parse_axis_angle(", angle(horizontal)") == 0.0

    def test_angle_vertical(self):
        import math
        from dash_render import _parse_axis_angle
        assert abs(_parse_axis_angle(", angle(vertical)") - math.pi / 2) < 1e-9

    def test_angle_negative(self):
        import math
        from dash_render import _parse_axis_angle
        assert abs(_parse_axis_angle(", angle(-45)") - math.radians(-45)) < 1e-9

    def test_invalid_angle_returns_none(self):
        from dash_render import _parse_axis_angle
        assert _parse_axis_angle(", angle(notanumber)") is None


class TestAxisLabelAngle:
    """xlabel/ylabel angle() sub-option must rotate tick labels on Bokeh figures."""

    def test_xlabel_angle_numeric_applied(self):
        """P6-30a: xlabel(angle(45)) sets fig.xaxis major_label_orientation."""
        import math
        fig = _get_figure({"xlabel": "0 10 20, angle(45)"})
        ori = fig.xaxis[0].major_label_orientation
        assert abs(ori - math.radians(45)) < 1e-9

    def test_ylabel_angle_numeric_applied(self):
        """P6-30b: ylabel(angle(30)) sets fig.yaxis major_label_orientation."""
        import math
        fig = _get_figure({"ylabel": "0 5 10 15 20, angle(30)"})
        ori = fig.yaxis[0].major_label_orientation
        assert abs(ori - math.radians(30)) < 1e-9

    def test_xlabel_angle_vertical(self):
        """P6-30c: angle(vertical) sets orientation to pi/2."""
        import math
        fig = _get_figure({"xlabel": ", angle(vertical)"})
        assert abs(fig.xaxis[0].major_label_orientation - math.pi / 2) < 1e-9

    def test_xlabel_angle_horizontal(self):
        """P6-30d: angle(horizontal) sets orientation to 0.0."""
        fig = _get_figure({"xlabel": ", angle(horizontal)"})
        assert fig.xaxis[0].major_label_orientation == 0.0

    def test_xlabel_no_angle_orientation_unchanged(self):
        """P6-30e: xlabel without angle() must not set major_label_orientation to a float."""
        fig = _get_figure({"xlabel": "0 10 20"})
        # Bokeh default is "auto" (a string), not a float
        ori = fig.xaxis[0].major_label_orientation
        assert isinstance(ori, str), f"Expected string default, got {type(ori)}: {ori}"

    def test_xlabel_angle_negative(self):
        """P6-30f: angle(-45) must be accepted and produce negative radians."""
        import math
        fig = _get_figure({"xlabel": ", angle(-45)"})
        assert abs(fig.xaxis[0].major_label_orientation - math.radians(-45)) < 1e-9

    def test_angle_with_tick_values_combined(self):
        """P6-30g: angle() combined with tick values applies both correctly."""
        import math
        fig = _get_figure({"xlabel": "0 5 10, angle(90)"})
        from bokeh.models.tickers import FixedTicker
        assert isinstance(fig.xaxis[0].ticker, FixedTicker)
        assert abs(fig.xaxis[0].major_label_orientation - math.pi / 2) < 1e-9


# ================================================================
# legend(cols(#)) / legend(rows(#)) — multi-column/row legend layout
# ================================================================
class TestLegendColsRows:
    """legend(cols(#)) and legend(rows(#)) must set ncols/nrows on the Bokeh Legend."""

    # Each figure here has its one legend (measured 24sep2026, hidden: a
    # single scatter has one key).  `if fig.legend:' skipped the check on
    # a figure whose legend was dropped, so the legend is asserted first.

    def test_legend_cols_sets_ncols(self):
        """legend(cols(2)) must set fig.legend[0].ncols = 2."""
        fig = _get_figure({"legend": "cols(2)"})
        assert len(fig.legend) == 1, len(fig.legend)
        if fig.legend:
            assert fig.legend[0].ncols == 2

    def test_legend_rows_sets_nrows(self):
        """legend(rows(3)) must set fig.legend[0].nrows = 3."""
        fig = _get_figure({"legend": "rows(3)"})
        assert len(fig.legend) == 1, len(fig.legend)
        if fig.legend:
            assert fig.legend[0].nrows == 3

    def test_legend_cols_and_position_combined(self):
        """legend(position(12) cols(2)) must set both placement and ncols
        (it read legend(top cols(2)), which twoway refuses -- WP-23)."""
        fig = _get_figure({"legend": "position(12) cols(2)"})
        assert fig.legend
        assert fig.legend[0].ncols == 2
        assert fig.legend[0] in fig.above

    def test_legend_rows_and_cols_combined(self):
        """legend(cols(2) rows(4)): rows() wins, as twoway's does (WP-30
        P1.19, measured: every order of rows/cols draws the rows)."""
        fig = _get_figure({"legend": "cols(2) rows(4)"})
        assert len(fig.legend) == 1, len(fig.legend)
        assert fig.legend[0].nrows == 4
        assert fig.legend[0].ncols == "auto"

    def test_legend_cols_zero_ignored(self):
        """legend(cols(0)) — zero column count must not raise."""
        try:
            fig = _get_figure({"legend": "cols(0)"})
            assert fig is not None
        except Exception as e:
            raise AssertionError(f"legend(cols(0)) raised unexpectedly: {e}")

    def test_legend_without_cols_rows_unchanged(self):
        """Omitting cols()/rows() leaves ncols/nrows at Bokeh default ('auto')
        on a legend the user placed, where the scheme's columns do not
        apply -- position(3); this used legend(top), which twoway refuses
        and which is no placement (WP-23)."""
        fig = _get_figure({"legend": "position(3)"})
        assert fig.legend
        assert fig.legend[0].ncols == "auto"
        assert fig.legend[0].nrows == "auto"


# ================================================================
# msangle(#) — uniform marker rotation
# ================================================================
class TestMsangle:
    """msangle(#) must rotate all markers in scatter-type plots by the given degrees."""

    def test_msangle_sets_glyph_angle(self):
        """msangle(45) must set glyph.angle ≈ pi/4 radians on scatter renderer."""
        import math, json, os, tempfile
        from dash_render import DashRenderer
        graphs = [{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {"msangle": "45"}}],
            "graph_options": {"name": "g1"},
            "if_expr": "", "in_expr": "",
        }]
        master_spec = {
            "graphs": graphs, "kpis": [],
            "build_options": {"layout": "auto", "link": "", "filter": "",
                              "theme": "default", "title": "", "subtitle": "", "registry": "g1"},
        }
        data_json = {"StataJSON": {
            "variableNames": ["mpg", "weight"],
            "variableLabels": {"mpg": "", "weight": ""},
            "valueLabels": {}, "valueLabelNames": {},
            "variableTypeIsString": {"mpg": False, "weight": False},
            "values": [{"mpg": float(i), "weight": float(i * 50)} for i in range(1, 11)],
        }}
        sp, dp, op = [tempfile.mkstemp(suffix=s)[1] for s in (".json", ".json", ".html")]
        try:
            with open(sp, "w") as f: json.dump(master_spec, f)
            with open(dp, "w") as f: json.dump(data_json, f)
            renderer = DashRenderer(sp, dp, op)
            figs = renderer._build_figures()
            fig = figs["g1"]
            scatter_rs = [r for r in fig.renderers if hasattr(r, "glyph") and
                          hasattr(r.glyph, "angle")]
            assert scatter_rs, "scatter renderer with angle attribute expected"
            assert abs(scatter_rs[0].glyph.angle - math.radians(45)) < 1e-9
        finally:
            for p in (sp, dp, op):
                try: os.unlink(p)
                except OSError: pass

    def test_msangle_zero_allowed(self):
        """msangle(0) must set angle = 0.0 without error."""
        import math, json, os, tempfile
        from dash_render import DashRenderer
        graphs = [{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {"msangle": "0"}}],
            "graph_options": {"name": "g1"},
            "if_expr": "", "in_expr": "",
        }]
        master_spec = {
            "graphs": graphs, "kpis": [],
            "build_options": {"layout": "auto", "link": "", "filter": "",
                              "theme": "default", "title": "", "subtitle": "", "registry": "g1"},
        }
        data_json = {"StataJSON": {
            "variableNames": ["mpg", "weight"],
            "variableLabels": {"mpg": "", "weight": ""},
            "valueLabels": {}, "valueLabelNames": {},
            "variableTypeIsString": {"mpg": False, "weight": False},
            "values": [{"mpg": float(i), "weight": float(i * 50)} for i in range(1, 11)],
        }}
        sp, dp, op = [tempfile.mkstemp(suffix=s)[1] for s in (".json", ".json", ".html")]
        try:
            with open(sp, "w") as f: json.dump(master_spec, f)
            with open(dp, "w") as f: json.dump(data_json, f)
            renderer = DashRenderer(sp, dp, op)
            figs = renderer._build_figures()
            assert "g1" in figs
        finally:
            for p in (sp, dp, op):
                try: os.unlink(p)
                except OSError: pass

    def test_msangle_in_apply_marker_opts(self):
        """_apply_marker_opts with msangle sets glyph.angle in radians."""
        import math
        from bokeh.plotting import figure
        from bokeh.models import ColumnDataSource
        from dash_render import GlyphMapper
        fig = figure()
        src = ColumnDataSource({"x": [1.0, 2.0], "y": [3.0, 4.0]})
        r = fig.scatter(x="x", y="y", source=src)
        gm = GlyphMapper(None)
        gm._apply_marker_opts(r, {"msangle": "90"})
        assert abs(r.glyph.angle - math.pi / 2) < 1e-9

    def test_msangle_invalid_value_ignored(self):
        """msangle(notanumber) must not raise — silently ignored."""
        from bokeh.plotting import figure
        from bokeh.models import ColumnDataSource
        from dash_render import GlyphMapper
        fig = figure()
        src = ColumnDataSource({"x": [1.0], "y": [2.0]})
        r = fig.scatter(x="x", y="y", source=src)
        original_angle = r.glyph.angle
        gm = GlyphMapper(None)
        gm._apply_marker_opts(r, {"msangle": "notanumber"})
        assert r.glyph.angle == original_angle

    def test_msangle_negative_angle(self):
        """msangle(-45) must set negative radians without error."""
        import math
        from bokeh.plotting import figure
        from bokeh.models import ColumnDataSource
        from dash_render import GlyphMapper
        fig = figure()
        src = ColumnDataSource({"x": [1.0], "y": [2.0]})
        r = fig.scatter(x="x", y="y", source=src)
        gm = GlyphMapper(None)
        gm._apply_marker_opts(r, {"msangle": "-45"})
        assert abs(r.glyph.angle - math.radians(-45)) < 1e-9


# ================================================================
# TestByLinkIntegration — by() + link() shared CDS via CDSView
# ================================================================

def _make_by_link_renderer(by_var="foreign", link_graph="g1", second_graph=True):
    """Create a DashRenderer with a by()-faceted linked graph."""
    vals = [
        {"mpg": float(i), "weight": float(i * 50), "price": float(i * 200),
         "foreign": float(i % 2)}
        for i in range(1, 21)
    ]
    graphs = [
        {
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "by": by_var},
            "if_expr": "", "in_expr": "",
        },
    ]
    if second_graph:
        graphs.append({
            "plots": [{"type": "scatter", "yvar": "price", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g2"},
            "if_expr": "", "in_expr": "",
        })
    master_spec = {
        "graphs": graphs, "kpis": [],
        "build_options": {
            "layout": "auto",
            "link": [link_graph, "g2"] if second_graph else link_graph,
            "filter": "", "theme": "default", "title": "", "subtitle": "",
            "registry": "g1 g2" if second_graph else "g1",
        },
    }
    data_json = {
        "StataJSON": {
            "variableNames": ["mpg", "weight", "price", "foreign"],
            "variableLabels": {"mpg": "mpg", "weight": "weight",
                               "price": "price", "foreign": "foreign"},
            "valueLabels": {}, "valueLabelNames": {},
            "variableTypeIsString": {
                "mpg": False, "weight": False, "price": False, "foreign": False
            },
            "values": vals,
        }
    }
    spec_fd, spec_path = tempfile.mkstemp(suffix=".json")
    data_fd, data_path = tempfile.mkstemp(suffix=".json")
    out_fd, out_path   = tempfile.mkstemp(suffix=".html")
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


class TestByLinkIntegration:
    """BL-01 through BL-10: by() + link() uses shared CDS with CDSView."""

    def test_bl_01_no_error_raised(self):
        """BL-01: by()+link() must not raise any exception."""
        r = _make_by_link_renderer()
        figs = r._build_figures()  # must not raise
        assert figs is not None

    def test_bl_02_facet_panels_created(self):
        """BL-02: by(foreign)+link() must produce 2 facet panels for g1."""
        r = _make_by_link_renderer()
        figs = r._build_figures()
        facet_keys = [k for k in figs if k.startswith("g1__by__")]
        assert len(facet_keys) == 2, f"Expected 2 panels, got {facet_keys}"

    def test_bl_03_panels_share_same_cds(self):
        """BL-03: All facet panels must share the same ColumnDataSource object."""
        r = _make_by_link_renderer()
        figs = r._build_figures()
        facet_keys = sorted(k for k in figs if k.startswith("g1__by__"))
        srcs = []
        for fkey in facet_keys:
            for renderer in figs[fkey].renderers:
                if hasattr(renderer, "data_source"):
                    srcs.append(renderer.data_source)
                    break
        assert len(srcs) == 2
        assert srcs[0] is srcs[1], "Facet panels must share the same CDS object"

    def test_bl_04_panels_share_cds_with_linked_graph(self):
        """BL-04: Facet panels and the linked non-by graph share the same CDS."""
        r = _make_by_link_renderer()
        figs = r._build_figures()
        facet_keys = sorted(k for k in figs if k.startswith("g1__by__"))
        g2_src = None
        for renderer in figs["g2"].renderers:
            if hasattr(renderer, "data_source"):
                g2_src = renderer.data_source
                break
        facet_src = None
        for renderer in figs[facet_keys[0]].renderers:
            if hasattr(renderer, "data_source"):
                facet_src = renderer.data_source
                break
        assert g2_src is not None
        assert facet_src is not None
        assert g2_src is facet_src, "Facet panel and linked graph must share the same CDS"

    def test_bl_05_each_panel_has_cdsview(self):
        """BL-05: Each facet renderer must have a CDSView with BooleanFilter."""
        from bokeh.models import CDSView, BooleanFilter
        r = _make_by_link_renderer()
        figs = r._build_figures()
        facet_keys = sorted(k for k in figs if k.startswith("g1__by__"))
        for fkey in facet_keys:
            for renderer in figs[fkey].renderers:
                assert isinstance(renderer.view, CDSView), (
                    f"{fkey}: renderer.view must be CDSView"
                )
                assert isinstance(renderer.view.filter, BooleanFilter), (
                    f"{fkey}: renderer.view.filter must be BooleanFilter"
                )

    def test_bl_06_masks_are_disjoint(self):
        """BL-06: The BooleanFilter masks across panels must be disjoint (no row in both)."""
        from bokeh.models import BooleanFilter
        r = _make_by_link_renderer()
        figs = r._build_figures()
        facet_keys = sorted(k for k in figs if k.startswith("g1__by__"))
        masks = []
        for fkey in facet_keys:
            for renderer in figs[fkey].renderers:
                if hasattr(renderer, "view") and isinstance(
                        renderer.view.filter, BooleanFilter):
                    masks.append(renderer.view.filter.booleans)
                    break
        assert len(masks) == 2
        # One entry a row of the shared source, in each mask (measured
        # 24sep2026: 20 and 20, ten true each): zip() stops at the shorter,
        # so an empty or short mask made no comparison at all.
        assert [len(m) for m in masks] == [20, 20], [len(m) for m in masks]
        for i, (a, b) in enumerate(zip(masks[0], masks[1])):
            assert not (a and b), f"Row {i} is in both facet masks — masks must be disjoint"

    def test_bl_07_masks_are_exhaustive(self):
        """BL-07: Every row is covered by exactly one facet mask."""
        from bokeh.models import BooleanFilter
        r = _make_by_link_renderer()
        figs = r._build_figures()
        facet_keys = sorted(k for k in figs if k.startswith("g1__by__"))
        masks = []
        for fkey in facet_keys:
            for renderer in figs[fkey].renderers:
                if hasattr(renderer, "view") and isinstance(
                        renderer.view.filter, BooleanFilter):
                    masks.append(list(renderer.view.filter.booleans))
                    break
        assert len(masks) == 2
        # Measured 24sep2026: 20 and 20.  An empty first mask made range(0)
        # and checked no row.
        assert [len(m) for m in masks] == [20, 20], [len(m) for m in masks]
        n = len(masks[0])
        for i in range(n):
            assert masks[0][i] or masks[1][i], (
                f"Row {i} is in neither facet mask — coverage is not exhaustive"
            )

    def test_bl_08_shared_cds_contains_all_rows(self):
        """BL-08: Shared CDS must contain all N rows (not a filtered subset)."""
        r = _make_by_link_renderer()
        figs = r._build_figures()
        facet_keys = sorted(k for k in figs if k.startswith("g1__by__"))
        shared_src = None
        for renderer in figs[facet_keys[0]].renderers:
            if hasattr(renderer, "data_source"):
                shared_src = renderer.data_source
                break
        assert shared_src is not None
        n_rows = len(next(iter(shared_src.data.values())))
        assert n_rows == 20, f"Shared CDS must have 20 rows, got {n_rows}"

    def test_bl_09_facet_titles_contain_group_label(self):
        """BL-09: Each facet figure title must contain the group value."""
        r = _make_by_link_renderer()
        figs = r._build_figures()
        facet_keys = sorted(k for k in figs if k.startswith("g1__by__"))
        for fkey in facet_keys:
            fig = figs[fkey]
            title = fig.title.text if fig.title else ""
            assert len(title) > 0, f"{fkey}: facet figure must have a non-empty title"
        # Non-empty is not the group value, and no facet at all checked
        # nothing.  Measured 24sep2026: two panels titled by foreign's
        # values, "0" and "1" (the data has no value labels).
        assert facet_keys == ["g1__by__0", "g1__by__1"], facet_keys
        assert [figs[k].title.text for k in facet_keys] == ["0", "1"], (
            [figs[k].title.text for k in facet_keys])

    def test_bl_10_render_produces_valid_html(self):
        """BL-10: render() with by()+link() must produce valid non-trivial HTML."""
        r = _make_by_link_renderer()
        html = r.render()
        assert len(html) > 2000, "by()+link() render() must produce non-trivial HTML"
        assert "bokeh" in html.lower(), "HTML must contain Bokeh references"
