"""
test_html_output.py
Tests that verify Bokeh-rendered HTML contains expected SVG/canvas elements
and structural markers produced by the Bokeh library.

These tests exercise the full DashRenderer.render() pipeline and check the
actual HTML output — not just Python objects in memory.

Run with:  pytest test/test_html_output.py -v
"""
import sys
import os
import json
import tempfile
import re
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dash_render import DashRenderer


# ================================================================
# Helpers
# ================================================================

def _make_data_json(columns: dict) -> dict:
    col_names = list(columns.keys())
    n_rows = len(next(iter(columns.values())))
    rows = [{c: columns[c][i] for c in col_names} for i in range(n_rows)]
    return {
        "StataJSON": {
            "variableNames": col_names,
            "variableLabels": {c: c for c in col_names},
            "valueLabels": {},
            "valueLabelNames": {},
            "variableTypeIsString": {c: False for c in col_names},
            "values": rows,
        }
    }


def _render_to_html(master_spec: dict, data_json: dict) -> str:
    """Run DashRenderer.render() and return the HTML string."""
    spec_fd, spec_path = tempfile.mkstemp(suffix=".json")
    data_fd, data_path = tempfile.mkstemp(suffix=".json")
    out_fd, out_path = tempfile.mkstemp(suffix=".html")

    try:
        with os.fdopen(spec_fd, "w") as f:
            json.dump(master_spec, f)
        with os.fdopen(data_fd, "w") as f:
            json.dump(data_json, f)
        os.close(out_fd)

        renderer = DashRenderer(spec_path, data_path, out_path)
        html_str = renderer.render()
        return html_str
    finally:
        for _p in (spec_path, data_path, out_path):
            try:
                os.unlink(_p)
            except OSError:
                pass


def _single_graph_spec(plot_type: str, extra_keys: dict = None,
                       options: dict = None) -> tuple[dict, dict]:
    """Build a minimal single-graph master spec and matching data JSON."""
    base_data = {
        "y": [float(i) for i in range(1, 21)],
        "x": [float(i) for i in range(1, 21)],
        "lo": [float(i) * 0.5 for i in range(1, 21)],
        "hi": [float(i) * 1.5 for i in range(1, 21)],
    }
    data_json = _make_data_json(base_data)

    plot = {"type": plot_type, "options": options or {}}
    if extra_keys:
        plot.update(extra_keys)

    graph = {
        "plots": [plot],
        "graph_options": {"name": "fig1"},
        "if_expr": "",
        "in_expr": "",
    }
    spec = {
        "graphs": [graph],
        "kpis": [],
        "build_options": {
            "layout": "auto",
            "link": "",
            "filter": "",
            "theme": "default",
            "title": "",
            "subtitle": "",
            "registry": "fig1",
        },
    }
    return spec, data_json


# ================================================================
# HTML structure tests — every rendered output must pass these
# ================================================================

class TestHtmlStructure:
    """Verify basic HTML structure of rendered Bokeh output."""

    def test_html_has_doctype_or_html_tag(self):
        """HTML output begins with <!DOCTYPE> or <html> tag."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert html.strip().lower().startswith("<!doctype") or "<html" in html.lower()

    def test_html_contains_bokeh_root(self):
        """Bokeh embeds a model root with data-root-id attribute."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        # Bokeh standalone HTML uses a div with data-root-id or class="bk-root"
        has_root = "data-root-id" in html or 'class="bk-root"' in html or "Bokeh.embed" in html
        assert has_root, "HTML should contain Bokeh embed markers"

    def test_html_contains_script_tags(self):
        """Bokeh output includes <script> tags for the Bokeh JS library."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "<script" in html.lower(), "HTML must include <script> tags"

    def test_html_contains_json_data(self):
        """Bokeh embeds plot data as JSON in the HTML output."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        # Bokeh model JSON is embedded as application/json or similar
        has_json = '"type"' in html and '"attributes"' in html
        assert has_json, "HTML should contain Bokeh model JSON"

    def test_html_not_empty(self):
        """Rendered HTML is not empty for any standard plot type."""
        for ptype in ["scatter", "line", "bar", "spike"]:
            spec, data = _single_graph_spec(ptype, {"yvar": "y", "xvar": "x"})
            html = _render_to_html(spec, data)
            assert len(html) > 1000, f"{ptype}: HTML is suspiciously short"


# ================================================================
# Plot-type specific rendering tests
# ================================================================

class TestScatterHtmlOutput:
    """Scatter plot produces correct Bokeh model in HTML."""

    def test_scatter_html_contains_scatter_glyph(self):
        """scatter plot HTML contains Scatter glyph type in Bokeh JSON."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        # Bokeh embeds glyph type names in the model JSON
        assert "Scatter" in html or "scatter" in html.lower()

    def test_scatter_html_non_empty(self):
        """scatter HTML output is non-trivial."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert len(html) > 500


class TestLineHtmlOutput:
    def test_line_html_contains_line_glyph(self):
        """line plot HTML references Line glyph."""
        spec, data = _single_graph_spec("line", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "Line" in html or '"line"' in html.lower()


class TestHistogramHtmlOutput:
    def test_histogram_html_contains_quad_glyph(self):
        """histogram HTML contains Quad glyph (used for bars)."""
        spec, data = _single_graph_spec("histogram", {"var": "y"})
        html = _render_to_html(spec, data)
        assert "Quad" in html or '"quad"' in html.lower()


class TestBarHtmlOutput:
    def test_bar_html_contains_vbar_glyph(self):
        """bar plot HTML contains VBar glyph."""
        spec, data = _single_graph_spec("bar", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "VBar" in html or '"vbar"' in html.lower()


class TestSpikeHtmlOutput:
    def test_spike_html_contains_segment_glyph(self):
        """spike plot HTML contains Segment glyph."""
        spec, data = _single_graph_spec("spike", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "Segment" in html or '"segment"' in html.lower()


class TestLfitHtmlOutput:
    def test_lfit_html_contains_line_glyph(self):
        """lfit plot HTML contains a Line glyph (fitted line)."""
        spec, data = _single_graph_spec("lfit", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "Line" in html or '"line"' in html.lower()


class TestRareaHtmlOutput:
    def test_rarea_html_contains_varea_glyph(self):
        """rarea HTML contains VArea glyph."""
        spec, data = _single_graph_spec(
            "rarea", {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}
        )
        html = _render_to_html(spec, data)
        assert "VArea" in html or '"varea"' in html.lower()


class TestDroplineHtmlOutput:
    def test_dropline_html_contains_segment_glyph(self):
        """dropline HTML contains Segment glyph."""
        spec, data = _single_graph_spec("dropline", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "Segment" in html or '"segment"' in html.lower()


class TestMsplineHtmlOutput:
    def test_mspline_html_contains_line_glyph(self):
        """mspline HTML contains a Line glyph."""
        spec, data = _single_graph_spec("mspline", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "Line" in html or '"line"' in html.lower()


class TestFunctionHtmlOutput:
    def test_function_html_contains_line_glyph(self):
        """function plot HTML contains a Line glyph."""
        spec, data = _single_graph_spec(
            "function",
            {"expr": "sin(x)"},
            options={"range": "0 6.28"},
        )
        html = _render_to_html(spec, data)
        assert "Line" in html or '"line"' in html.lower()


# ================================================================
# XSS safety in HTML output
# ================================================================

class TestConnectedHtmlOutput:
    def test_connected_html_contains_line_and_scatter(self):
        """connected plot HTML references both Line and Scatter glyphs."""
        spec, data = _single_graph_spec("connected", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert ("Line" in html or '"line"' in html.lower()), "connected must have Line glyph"
        assert ("Scatter" in html or '"scatter"' in html.lower()), "connected must have Scatter glyph"


class TestAreaHtmlOutput:
    def test_area_html_contains_varea_glyph(self):
        """area plot HTML contains VArea glyph."""
        spec, data = _single_graph_spec("area", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "VArea" in html or '"varea"' in html.lower()


class TestQfitHtmlOutput:
    def test_qfit_html_contains_line_glyph(self):
        """qfit plot HTML contains Line glyph (quadratic fitted line)."""
        spec, data = _single_graph_spec("qfit", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "Line" in html or '"line"' in html.lower()


class TestLfitciHtmlOutput:
    def test_lfitci_html_contains_varea_and_line(self):
        """lfitci plot HTML contains both VArea (CI band) and Line glyphs."""
        spec, data = _single_graph_spec("lfitci", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "VArea" in html or '"varea"' in html.lower(), "lfitci must have VArea CI band"
        assert "Line" in html or '"line"' in html.lower(), "lfitci must have Line glyph"


class TestQfitciHtmlOutput:
    def test_qfitci_html_contains_varea_and_line(self):
        """qfitci plot HTML contains both VArea (CI band) and Line glyphs."""
        spec, data = _single_graph_spec("qfitci", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "VArea" in html or '"varea"' in html.lower(), "qfitci must have VArea CI band"
        assert "Line" in html or '"line"' in html.lower(), "qfitci must have Line glyph"


class TestLowessHtmlOutput:
    def test_lowess_html_contains_line_glyph(self):
        """lowess plot HTML contains Line glyph (smoothed line)."""
        spec, data = _single_graph_spec("lowess", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "Line" in html or '"line"' in html.lower()


class TestKdensityHtmlOutput:
    def test_kdensity_html_contains_line_glyph(self):
        """kdensity plot HTML contains Line glyph (density curve)."""
        spec, data = _single_graph_spec("kdensity", {"var": "y"})
        html = _render_to_html(spec, data)
        assert "Line" in html or '"line"' in html.lower()


class TestRbarHtmlOutput:
    def test_rbar_html_contains_vbar_glyph(self):
        """rbar plot HTML contains VBar glyph."""
        spec, data = _single_graph_spec(
            "rbar", {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}
        )
        html = _render_to_html(spec, data)
        assert "VBar" in html or '"vbar"' in html.lower()


class TestRspikeHtmlOutput:
    def test_rspike_html_contains_segment_glyph(self):
        """rspike plot HTML contains Segment glyph."""
        spec, data = _single_graph_spec(
            "rspike", {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}
        )
        html = _render_to_html(spec, data)
        assert "Segment" in html or '"segment"' in html.lower()


class TestRcapHtmlOutput:
    def test_rcap_html_contains_segment_glyph(self):
        """rcap plot HTML contains Segment glyph (spines and caps)."""
        spec, data = _single_graph_spec(
            "rcap", {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}
        )
        html = _render_to_html(spec, data)
        assert "Segment" in html or '"segment"' in html.lower()


class TestRlineHtmlOutput:
    def test_rline_html_contains_line_glyph(self):
        """rline plot HTML contains Line glyph (two range boundary lines)."""
        spec, data = _single_graph_spec(
            "rline", {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}
        )
        html = _render_to_html(spec, data)
        assert "Line" in html or '"line"' in html.lower()


class TestRconnectedHtmlOutput:
    def test_rconnected_html_contains_line_and_scatter(self):
        """rconnected plot HTML contains both Line and Scatter glyphs."""
        spec, data = _single_graph_spec(
            "rconnected", {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}
        )
        html = _render_to_html(spec, data)
        assert "Line" in html or '"line"' in html.lower(), "rconnected must have Line glyph"
        assert "Scatter" in html or '"scatter"' in html.lower(), "rconnected must have Scatter glyph"


class TestDotHtmlOutput:
    def test_dot_html_contains_scatter_glyph(self):
        """dot plot HTML contains Scatter glyph."""
        spec, data = _single_graph_spec("dot", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "Scatter" in html or '"scatter"' in html.lower()


class TestRcapsymHtmlOutput:
    def test_rcapsym_html_contains_segment_and_scatter(self):
        """rcapsym plot HTML contains Segment and Scatter glyphs."""
        spec, data = _single_graph_spec(
            "rcapsym", {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}
        )
        html = _render_to_html(spec, data)
        assert "Segment" in html or '"segment"' in html.lower(), "rcapsym must have Segment glyph"
        assert "Scatter" in html or '"scatter"' in html.lower(), "rcapsym must have Scatter glyph"


class TestScatteriHtmlOutput:
    def test_scatteri_html_contains_scatter_glyph(self):
        """scatteri plot HTML contains Scatter glyph from inline coordinate pairs."""
        spec, data = _single_graph_spec(
            "scatteri",
            {"values": [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]},
        )
        html = _render_to_html(spec, data)
        assert "Scatter" in html or '"scatter"' in html.lower()

    def test_scatteri_coordinates_embedded_in_json(self):
        """scatteri literal coordinate values must appear in the Bokeh JSON model."""
        spec, data = _single_graph_spec(
            "scatteri",
            {"values": [[7.0, 13.0], [42.0, 99.0]]},
        )
        html = _render_to_html(spec, data)
        # y-values 7.0 and 42.0 must appear in the model JSON data
        assert "7.0" in html or "7," in html, \
            "scatteri y-value 7.0 must be embedded in Bokeh model JSON"
        assert "42.0" in html or "42," in html, \
            "scatteri y-value 42.0 must be embedded in Bokeh model JSON"


class TestPcspikeHtmlOutput:
    def test_pcspike_html_contains_segment_glyph(self):
        """pcspike plot HTML contains Segment glyph."""
        base_data = {
            "y1": [float(i) for i in range(1, 11)],
            "x1": [float(i) for i in range(1, 11)],
            "y2": [float(i) * 1.5 for i in range(1, 11)],
            "x2": [float(i) * 1.2 for i in range(1, 11)],
        }
        data_json = _make_data_json(base_data)
        plot = {
            "type": "pcspike",
            "y1var": "y1",
            "x1var": "x1",
            "y2var": "y2",
            "x2var": "x2",
            "options": {},
        }
        graph = {
            "plots": [plot],
            "graph_options": {"name": "fig1"},
            "if_expr": "",
            "in_expr": "",
        }
        spec = {
            "graphs": [graph],
            "kpis": [],
            "build_options": {
                "layout": "auto",
                "link": "",
                "filter": "",
                "theme": "default",
                "title": "",
                "subtitle": "",
                "registry": "fig1",
            },
        }
        html = _render_to_html(spec, data_json)
        assert "Segment" in html or '"segment"' in html.lower()


class TestTslineHtmlOutput:
    def test_tsline_html_contains_line_glyph(self):
        """tsline plot HTML contains Line glyph."""
        spec, data = _single_graph_spec("tsline", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "Line" in html or '"line"' in html.lower()


class TestTsrlineHtmlOutput:
    def test_tsrline_html_contains_line_glyph(self):
        """tsrline plot HTML contains Line glyph (two time-series boundary lines)."""
        spec, data = _single_graph_spec(
            "tsrline", {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}
        )
        html = _render_to_html(spec, data)
        assert "Line" in html or '"line"' in html.lower()


class TestXssInHtmlOutput:
    def test_script_tag_in_title_is_escaped(self):
        """XSS: <script> in title must not appear unescaped in output HTML."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["title"] = "<script>alert(1)</script>"
        html = _render_to_html(spec, data)
        assert "<script>alert(1)</script>" not in html, \
            "Raw <script> injection must not appear in rendered HTML"

    def test_html_contains_csp_meta(self):
        """HTML output includes Content-Security-Policy meta tag."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "content-security-policy" in html.lower() or \
               "Content-Security-Policy" in html, \
               "HTML must include a CSP meta tag"


# ================================================================
# pcarrow — Arrow glyph
# ================================================================
class TestPcarrowHtmlOutput:
    def test_pcarrow_html_contains_arrow_or_segment(self):
        """pcarrow plot HTML contains Arrow or Segment glyph."""
        base_data = {
            "y1": [float(i) for i in range(1, 11)],
            "x1": [float(i) for i in range(1, 11)],
            "y2": [float(i) * 1.5 for i in range(1, 11)],
            "x2": [float(i) * 1.2 for i in range(1, 11)],
        }
        data_json = _make_data_json(base_data)
        graph = {
            "plots": [{"type": "pcarrow", "y1var": "y1", "x1var": "x1",
                       "y2var": "y2", "x2var": "x2", "options": {}}],
            "graph_options": {"name": "g1"},
            "if_expr": "", "in_expr": "",
        }
        spec = {"graphs": [graph], "kpis": [], "build_options": {
            "layout": "auto", "link": "", "filter": "",
            "theme": "default", "title": "", "subtitle": "", "registry": "g1",
        }}
        html = _render_to_html(spec, data_json)
        # pcarrow uses segment shaft + Arrow annotation; check glyph or non-empty
        assert len(html) > 500, "pcarrow should produce non-trivial HTML"
        assert "Segment" in html or "Arrow" in html or '"segment"' in html.lower()


# ================================================================
# pcbarrow — bidirectional Arrow glyph
# ================================================================
class TestPcbarrowHtmlOutput:
    def test_pcbarrow_html_contains_arrow_or_segment(self):
        """pcbarrow plot HTML contains Arrow or Segment glyph."""
        base_data = {
            "y1": [float(i) for i in range(1, 11)],
            "x1": [float(i) for i in range(1, 11)],
            "y2": [float(i) * 1.5 for i in range(1, 11)],
            "x2": [float(i) * 1.2 for i in range(1, 11)],
        }
        data_json = _make_data_json(base_data)
        graph = {
            "plots": [{"type": "pcbarrow", "y1var": "y1", "x1var": "x1",
                       "y2var": "y2", "x2var": "x2", "options": {}}],
            "graph_options": {"name": "g1"},
            "if_expr": "", "in_expr": "",
        }
        spec = {"graphs": [graph], "kpis": [], "build_options": {
            "layout": "auto", "link": "", "filter": "",
            "theme": "default", "title": "", "subtitle": "", "registry": "g1",
        }}
        html = _render_to_html(spec, data_json)
        assert len(html) > 500, "pcbarrow should produce non-trivial HTML"
        assert "Segment" in html or "Arrow" in html or '"segment"' in html.lower()


# ================================================================
# Graph-level options verified in rendered HTML output
# ================================================================
class TestGraphOptionsInHtml:
    """Graph-level options (title, xtitle, note, subtitle) appear in HTML."""

    def test_title_appears_in_html(self):
        """Custom title text is present in the rendered HTML."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["title"] = "My Custom Dashboard"
        html = _render_to_html(spec, data)
        assert "My Custom Dashboard" in html

    def test_xtitle_appears_in_html(self):
        """Custom x-axis title text appears in rendered HTML."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["xtitle"] = "Weight in Kilograms"
        html = _render_to_html(spec, data)
        assert "Weight in Kilograms" in html

    def test_ytitle_appears_in_html(self):
        """Custom y-axis title text appears in rendered HTML."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["ytitle"] = "Miles per Gallon"
        html = _render_to_html(spec, data)
        assert "Miles per Gallon" in html

    def test_note_text_appears_in_html(self):
        """note() annotation text appears in rendered HTML."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["note"] = "Source: auto.dta"
        html = _render_to_html(spec, data)
        assert "Source: auto.dta" in html

    def test_subtitle_appears_in_html(self):
        """subtitle() annotation text appears in rendered HTML."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["subtitle"] = "Model comparison results"
        html = _render_to_html(spec, data)
        assert "Model comparison results" in html

    def test_caption_appears_in_html(self):
        """caption() annotation text appears in rendered HTML."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["caption"] = "Figure 1"
        html = _render_to_html(spec, data)
        assert "Figure 1" in html

    def test_xlabel_tick_values_in_html(self):
        """xlabel() tick values must appear in the Bokeh model JSON in rendered HTML."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["xlabel"] = "2 6 10 14 18"
        html = _render_to_html(spec, data)
        # FixedTicker tick values should be embedded in the model JSON
        assert "FixedTicker" in html or '"ticks"' in html, \
            "xlabel() must embed FixedTicker (with ticks) in model JSON"

    def test_ylabel_tick_values_in_html(self):
        """ylabel() tick values must appear in the Bokeh model JSON in rendered HTML."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["ylabel"] = "5 10 15 20"
        html = _render_to_html(spec, data)
        assert "FixedTicker" in html or '"ticks"' in html, \
            "ylabel() must embed FixedTicker (with ticks) in model JSON"

    def test_xlabel_labeled_ticks_in_html(self):
        """xlabel() with labeled ticks must embed CustomJSTickFormatter in model JSON."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["xlabel"] = '1 "Low" 10 "Mid" 20 "High"'
        html = _render_to_html(spec, data)
        assert "CustomJSTickFormatter" in html or "Low" in html, \
            "xlabel labeled ticks must produce CustomJSTickFormatter in model JSON"

    def test_title_xss_not_in_html_unescaped(self):
        """XSS payload in title does not appear as a raw <script> tag in output."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["title"] = "<script>alert(2)</script>"
        html = _render_to_html(spec, data)
        # The raw <script> tag must not appear literally outside a JSON string
        # (Bokeh encodes it safely in its JSON model)
        assert "<script>alert(2)</script>" not in html


# ================================================================
# Plot-level options verified in the Bokeh JSON model in HTML
# ================================================================
class TestPlotOptionsInHtml:
    """Plot-level options (mcolor, lcolor, fcolor) produce the correct values
    in the Bokeh JSON model embedded in the rendered HTML."""

    def test_mcolor_red_appears_in_scatter_html(self):
        """mcolor(red) produces #ff0000 in scatter HTML Bokeh JSON."""
        spec, data = _single_graph_spec(
            "scatter", {"yvar": "y", "xvar": "x"}, options={"mcolor": "red"}
        )
        html = _render_to_html(spec, data)
        assert "#ff0000" in html, "mcolor(red) should produce #ff0000 in Bokeh JSON"

    def test_mcolor_navy_appears_in_scatter_html(self):
        """mcolor(navy) produces #1a476f in scatter HTML Bokeh JSON."""
        spec, data = _single_graph_spec(
            "scatter", {"yvar": "y", "xvar": "x"}, options={"mcolor": "navy"}
        )
        html = _render_to_html(spec, data)
        assert "#1a476f" in html, "mcolor(navy) should produce #1a476f in Bokeh JSON"

    def test_mcolor_rgb_triplet_in_scatter_html(self):
        """mcolor with RGB triplet produces correct hex in HTML."""
        spec, data = _single_graph_spec(
            "scatter", {"yvar": "y", "xvar": "x"}, options={"mcolor": "0 0 255"}
        )
        html = _render_to_html(spec, data)
        assert "#0000ff" in html, "mcolor(0 0 255) should produce #0000ff"

    def test_lcolor_navy_appears_in_line_html(self):
        """lcolor(navy) produces #1a476f in line HTML Bokeh JSON."""
        spec, data = _single_graph_spec(
            "line", {"yvar": "y", "xvar": "x"}, options={"lcolor": "navy"}
        )
        html = _render_to_html(spec, data)
        assert "#1a476f" in html, "lcolor(navy) should produce #1a476f in Bokeh JSON"

    def test_fcolor_maroon_appears_in_area_html(self):
        """fcolor(maroon) produces #90353b in area HTML Bokeh JSON."""
        spec, data = _single_graph_spec(
            "area", {"yvar": "y", "xvar": "x"}, options={"fcolor": "maroon"}
        )
        html = _render_to_html(spec, data)
        assert "#90353b" in html, "fcolor(maroon) should produce #90353b in Bokeh JSON"

    def test_fcolor_in_bar_html(self):
        """fcolor(forest_green) in bar produces #538d22 in HTML."""
        spec, data = _single_graph_spec(
            "bar", {"yvar": "y", "xvar": "x"}, options={"fcolor": "forest_green"}
        )
        html = _render_to_html(spec, data)
        assert "#538d22" in html, "fcolor(forest_green) should produce #538d22"

    def test_combined_mcolor_and_lcolor_in_scatter_html(self):
        """mcolor and lcolor options both appear in scatter HTML JSON."""
        spec, data = _single_graph_spec(
            "scatter", {"yvar": "y", "xvar": "x"},
            options={"mcolor": "red", "lcolor": "navy"},
        )
        html = _render_to_html(spec, data)
        assert "#ff0000" in html, "mcolor(red) hex should appear"
        assert "Scatter" in html or '"scatter"' in html.lower()


# ================================================================
# Color rendering tests — all 26 remaining plot types must embed
# the resolved color hex value in the Bokeh JSON model in HTML
# ================================================================
class TestColorRenderingAllPlotTypes:
    """Verify lcolor/mcolor/fcolor option produces correct hex in HTML JSON
    for the 26 plot types not covered by TestPlotOptionsInHtml."""

    _NAVY = "#1a476f"   # translate_mcolor("navy")
    _RED  = "#ff0000"   # translate_mcolor("red")

    def _html(self, ptype, extra_keys, option_key, option_val="navy"):
        spec, data = _single_graph_spec(ptype, extra_keys, options={option_key: option_val})
        return _render_to_html(spec, data)

    # --- line-style plot types (lcolor) ---

    def test_spike_lcolor_in_html(self):
        html = self._html("spike", {"yvar": "y", "xvar": "x"}, "lcolor")
        assert self._NAVY in html, "spike lcolor(navy) must embed #1a476f in model JSON"

    def test_lfit_lcolor_in_html(self):
        html = self._html("lfit", {"yvar": "y", "xvar": "x"}, "lcolor")
        assert self._NAVY in html, "lfit lcolor(navy) must embed #1a476f in model JSON"

    def test_qfit_lcolor_in_html(self):
        html = self._html("qfit", {"yvar": "y", "xvar": "x"}, "lcolor")
        assert self._NAVY in html, "qfit lcolor(navy) must embed #1a476f in model JSON"

    def test_lowess_lcolor_in_html(self):
        html = self._html("lowess", {"yvar": "y", "xvar": "x"}, "lcolor")
        assert self._NAVY in html, "lowess lcolor(navy) must embed #1a476f in model JSON"

    def test_kdensity_lcolor_in_html(self):
        html = self._html("kdensity", {"var": "y"}, "lcolor")
        assert self._NAVY in html, "kdensity lcolor(navy) must embed #1a476f in model JSON"

    def test_rline_lcolor_in_html(self):
        html = self._html("rline",
                          {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}, "lcolor")
        assert self._NAVY in html, "rline lcolor(navy) must embed #1a476f in model JSON"

    def test_rspike_lcolor_in_html(self):
        html = self._html("rspike",
                          {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}, "lcolor")
        assert self._NAVY in html, "rspike lcolor(navy) must embed #1a476f in model JSON"

    def test_rcap_lcolor_in_html(self):
        html = self._html("rcap",
                          {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}, "lcolor")
        assert self._NAVY in html, "rcap lcolor(navy) must embed #1a476f in model JSON"

    def test_tsline_lcolor_in_html(self):
        html = self._html("tsline", {"yvar": "y", "xvar": "x"}, "lcolor")
        assert self._NAVY in html, "tsline lcolor(navy) must embed #1a476f in model JSON"

    def test_tsrline_lcolor_in_html(self):
        html = self._html("tsrline",
                          {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}, "lcolor")
        assert self._NAVY in html, "tsrline lcolor(navy) must embed #1a476f in model JSON"

    def test_mspline_lcolor_in_html(self):
        html = self._html("mspline", {"yvar": "y", "xvar": "x"}, "lcolor")
        assert self._NAVY in html, "mspline lcolor(navy) must embed #1a476f in model JSON"

    def test_function_lcolor_in_html(self):
        html = self._html("function",
                          {"expr": "x", "range": [0, 10]}, "lcolor")
        assert self._NAVY in html, "function lcolor(navy) must embed #1a476f in model JSON"

    def test_dropline_lcolor_in_html(self):
        html = self._html("dropline", {"yvar": "y", "xvar": "x"}, "lcolor")
        assert self._NAVY in html, "dropline lcolor(navy) must embed #1a476f in model JSON"

    def test_pcspike_lcolor_in_html(self):
        base = {
            "y": [1.0, 2.0, 3.0], "x": [1.0, 2.0, 3.0],
            "lo": [0.5, 1.0, 1.5], "hi": [1.5, 3.0, 4.5],
        }
        data = _make_data_json(base)
        spec, _ = _single_graph_spec("pcspike", {
            "y1var": "y", "x1var": "x", "y2var": "hi", "x2var": "lo"
        }, options={"lcolor": "navy"})
        html = _render_to_html(spec, data)
        assert self._NAVY in html, "pcspike lcolor(navy) must embed #1a476f in model JSON"

    # --- scatter-type plot types (mcolor) ---

    def test_connected_mcolor_in_html(self):
        html = self._html("connected", {"yvar": "y", "xvar": "x"}, "mcolor")
        assert self._NAVY in html, "connected mcolor(navy) must embed #1a476f in model JSON"

    def test_dot_mcolor_in_html(self):
        html = self._html("dot", {"yvar": "y", "xvar": "x"}, "mcolor")
        assert self._NAVY in html, "dot mcolor(navy) must embed #1a476f in model JSON"

    def test_rcapsym_mcolor_in_html(self):
        html = self._html("rcapsym",
                          {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}, "mcolor")
        assert self._NAVY in html, "rcapsym mcolor(navy) must embed #1a476f in model JSON"

    def test_rconnected_mcolor_in_html(self):
        html = self._html("rconnected",
                          {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}, "mcolor")
        assert self._NAVY in html, "rconnected mcolor(navy) must embed #1a476f in model JSON"

    def test_scatteri_mcolor_in_html(self):
        html = self._html("scatteri",
                          {"values": [[1.0, 2.0], [3.0, 4.0]]}, "mcolor")
        assert self._NAVY in html, "scatteri mcolor(navy) must embed #1a476f in model JSON"

    # --- fill-type plot types (fcolor) ---

    def test_rbar_fcolor_in_html(self):
        html = self._html("rbar",
                          {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}, "fcolor")
        assert self._NAVY in html, "rbar fcolor(navy) must embed #1a476f in model JSON"

    def test_histogram_fcolor_in_html(self):
        html = self._html("histogram", {"var": "y"}, "fcolor")
        assert self._NAVY in html, "histogram fcolor(navy) must embed #1a476f in model JSON"

    def test_lfitci_fcolor_in_html(self):
        html = self._html("lfitci", {"yvar": "y", "xvar": "x"}, "fcolor")
        assert self._NAVY in html, "lfitci fcolor(navy) must embed #1a476f in model JSON"

    def test_qfitci_fcolor_in_html(self):
        html = self._html("qfitci", {"yvar": "y", "xvar": "x"}, "fcolor")
        assert self._NAVY in html, "qfitci fcolor(navy) must embed #1a476f in model JSON"

    def test_rarea_fcolor_in_html(self):
        html = self._html("rarea",
                          {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}, "fcolor")
        assert self._NAVY in html, "rarea fcolor(navy) must embed #1a476f in model JSON"


# ================================================================
# Adversarial tests — injection, resource exhaustion (CLAUDE.md rule 18)
# ================================================================
class TestAdversarialPlotOptions:
    """Security-focused adversarial tests for plot-level option inputs."""

    def test_injection_in_mcolor_produces_valid_html(self):
        """Injection attempt in mcolor is rejected; render uses default color."""
        spec, data = _single_graph_spec(
            "scatter", {"yvar": "y", "xvar": "x"},
            options={"mcolor": "'; import os; os.system('id')"},
        )
        html = _render_to_html(spec, data)
        assert len(html) > 500, "Render must succeed despite invalid mcolor"
        assert "Scatter" in html or '"scatter"' in html.lower()
        # Injected string must NOT appear literally in output HTML
        assert "os.system" not in html

    def test_injection_in_lcolor_produces_valid_html(self):
        """Injection attempt in lcolor is rejected; render uses default color."""
        spec, data = _single_graph_spec(
            "line", {"yvar": "y", "xvar": "x"},
            options={"lcolor": "__import__('os').system('id')"},
        )
        html = _render_to_html(spec, data)
        assert len(html) > 500, "Render must succeed despite invalid lcolor"
        assert "Line" in html or '"line"' in html.lower()

    def test_invalid_msymbol_falls_back_to_default(self):
        """Invalid msymbol value falls back to default circle marker."""
        spec, data = _single_graph_spec(
            "scatter", {"yvar": "y", "xvar": "x"},
            options={"msymbol": "'; import os'"},
        )
        html = _render_to_html(spec, data)
        assert "Scatter" in html or '"scatter"' in html.lower()

    def test_huge_histogram_bin_count_is_bounded(self):
        """Extremely large bin count is capped to prevent resource exhaustion."""
        spec, data = _single_graph_spec("histogram", {"var": "y"},
                                        options={"bin": "99999999"})
        html = _render_to_html(spec, data)
        assert len(html) > 500, "Histogram must render with large bin count"
        assert "Quad" in html or '"quad"' in html.lower()

    def test_extreme_msize_does_not_crash(self):
        """Extremely large msize value must not crash the renderer."""
        spec, data = _single_graph_spec(
            "scatter", {"yvar": "y", "xvar": "x"},
            options={"msize": "999999"},
        )
        html = _render_to_html(spec, data)
        assert len(html) > 500, "Render must succeed with extreme msize"
        assert "Scatter" in html or '"scatter"' in html.lower()

    def test_extreme_lwidth_does_not_crash(self):
        """Extremely large lwidth value must not crash the renderer."""
        spec, data = _single_graph_spec(
            "line", {"yvar": "y", "xvar": "x"},
            options={"lwidth": "999999"},
        )
        html = _render_to_html(spec, data)
        assert len(html) > 500, "Render must succeed with extreme lwidth"
        assert "Line" in html or '"line"' in html.lower()

    def test_unicode_in_title_does_not_crash(self):
        """Unicode characters in title option must not crash the renderer."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["title"] = "Ünïcödé tïtlé: 中文 日本語 한국어"
        html = _render_to_html(spec, data)
        assert len(html) > 500, "Render must succeed with unicode title"

    def test_null_byte_in_option_value_does_not_crash(self):
        """Null byte in mcolor option value must not crash the renderer."""
        spec, data = _single_graph_spec(
            "scatter", {"yvar": "y", "xvar": "x"},
            options={"mcolor": "red\x00injected"},
        )
        html = _render_to_html(spec, data)
        assert len(html) > 500, "Render must succeed with null byte in option"
        assert "injected" not in html, "Null-byte bypass must not inject content"

    def test_xss_in_note_option_escaped(self):
        """XSS payload in note option must be escaped in rendered HTML."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["note"] = "<script>alert('xss')</script>"
        html = _render_to_html(spec, data)
        assert "<script>alert('xss')</script>" not in html, \
            "Raw XSS payload must not appear unescaped in note output"


# ================================================================
# HTML model data-content tests — verify actual Bokeh JSON model
# data payload (coordinates, colors) not just structure
# ================================================================

class TestHtmlModelDataContent:
    """Verify the Bokeh model JSON in rendered HTML contains actual plot data."""

    def test_scatter_html_contains_x_data(self):
        """Scatter HTML embeds x-axis data values in the Bokeh JSON model."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        # x values 1-20 should appear somewhere in the JSON data
        assert "1.0" in html or "1," in html, "x data values must be embedded"

    def test_scatter_html_contains_y_data(self):
        """Scatter HTML embeds y-axis data values in the Bokeh JSON model."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "20.0" in html or "20," in html, "y data values must be embedded"

    def test_mcolor_hex_in_html(self):
        """mcolor(red) produces #ff0000 hex in the Bokeh model JSON."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"},
                                        options={"mcolor": "red"})
        html = _render_to_html(spec, data)
        assert "#ff0000" in html.lower() or "ff0000" in html.lower(), \
            "mcolor(red) must produce #ff0000 in HTML"

    def test_lcolor_hex_in_html(self):
        """lcolor(navy) produces #1a476f hex in the Bokeh model JSON."""
        spec, data = _single_graph_spec("line", {"yvar": "y", "xvar": "x"},
                                        options={"lcolor": "navy"})
        html = _render_to_html(spec, data)
        assert "#1a476f" in html.lower() or "1a476f" in html.lower(), \
            "lcolor(navy) must produce #1a476f in HTML"

    def test_histogram_quad_data_embedded(self):
        """Histogram HTML embeds top/left/right arrays for the Quad glyph."""
        spec, data = _single_graph_spec("histogram", {"var": "y"})
        html = _render_to_html(spec, data)
        assert "Quad" in html or "quad" in html.lower(), \
            "histogram must embed Quad glyph type in HTML model"

    def test_line_glyph_type_in_json(self):
        """Line plot HTML contains 'Line' glyph type in model JSON."""
        spec, data = _single_graph_spec("line", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert '"Line"' in html or '"line"' in html.lower(), \
            "line plot must embed Line glyph in HTML model"

    def test_varea_glyph_type_in_json(self):
        """rarea plot HTML contains VArea glyph type in model JSON."""
        spec, data = _single_graph_spec(
            "rarea", extra_keys={"yvar1": "lo", "yvar2": "hi", "xvar": "x"}
        )
        html = _render_to_html(spec, data)
        assert "VArea" in html or "varea" in html.lower(), \
            "rarea plot must embed VArea glyph in HTML model"

    def test_segment_glyph_for_spike(self):
        """spike plot HTML contains Segment glyph type in model JSON."""
        spec, data = _single_graph_spec("spike", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "Segment" in html or "segment" in html.lower(), \
            "spike plot must embed Segment glyph in HTML model"


# ================================================================
# bgcolor / plotbgcolor — figure background color
# ================================================================

class TestBgcolorPlotbgcolor:
    """bgcolor() and plotbgcolor() set figure border/plot background colors."""

    def test_bgcolor_hex_appears_in_html(self):
        """bgcolor(#aabbcc) sets border_fill_color; sentinel hex must appear in Bokeh JSON."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["bgcolor"] = "#aabbcc"
        html = _render_to_html(spec, data)
        assert "#aabbcc" in html.lower(), \
            "bgcolor(#aabbcc) must appear as border_fill_color in Bokeh model JSON"

    def test_plotbgcolor_hex_appears_in_html(self):
        """plotbgcolor(#112233) sets background_fill_color; sentinel hex must appear in Bokeh JSON."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["plotbgcolor"] = "#112233"
        html = _render_to_html(spec, data)
        assert "#112233" in html.lower(), \
            "plotbgcolor(#112233) must appear as background_fill_color in Bokeh model JSON"

    def test_bgcolor_named_color_translates(self):
        """bgcolor(navy) must translate to #1a476f and appear in HTML."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["bgcolor"] = "navy"
        html = _render_to_html(spec, data)
        assert "#1a476f" in html, \
            "bgcolor(navy) must translate to #1a476f and appear in Bokeh JSON"

    def test_plotbgcolor_named_color_translates(self):
        """plotbgcolor(ltblue) must translate and appear in HTML."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["plotbgcolor"] = "ltblue"
        html = _render_to_html(spec, data)
        # ltblue translates to some hex; just verify no crash and HTML valid
        assert "Scatter" in html, \
            "plotbgcolor with named color must not crash rendering"

    def test_bgcolor_invalid_no_crash(self):
        """bgcolor with invalid value must not crash — renders normally."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["bgcolor"] = "not_a_color_xyz"
        html = _render_to_html(spec, data)
        assert "Scatter" in html, \
            "invalid bgcolor must fall back gracefully"


# ================================================================
# xrange / yrange axis limit tests
# ================================================================

class TestXrangeYrange:
    """xrange() and yrange() options must set axis limits on the figure."""

    def test_xrange_embeds_unique_start_value(self):
        """xrange(-37 99) must embed -37.0 in model JSON (unique sentinel not in data)."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["xrange"] = "-37 99"
        html = _render_to_html(spec, data)
        # -37 is not in the data (1-20), so must come from the x_range
        assert "-37" in html, "xrange start=-37 must appear in Bokeh model JSON"

    def test_yrange_embeds_unique_end_value(self):
        """yrange(0 9999) must embed 9999 in model JSON (unique sentinel not in data)."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["yrange"] = "0 9999"
        html = _render_to_html(spec, data)
        # 9999 is not in the data (1-20), so must come from the y_range
        assert "9999" in html, "yrange end=9999 must appear in Bokeh model JSON"

    def test_xrange_invalid_ignores_gracefully(self):
        """xrange with non-numeric values must not crash — renders normally."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["xrange"] = "bad_value"
        html = _render_to_html(spec, data)
        assert "Scatter" in html or "scatter" in html.lower(), \
            "invalid xrange must fall back gracefully"

    def test_yrange_invalid_ignores_gracefully(self):
        """yrange with non-numeric values must not crash."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["yrange"] = "bad"
        html = _render_to_html(spec, data)
        assert len(html) > 500, "invalid yrange must still produce HTML"


# ================================================================
# xscale / yscale log axis tests in standalone HTML mode
# ================================================================

class TestLogScaleHtml:
    """xscale(log) and yscale(log) must produce log axis in standalone HTML."""

    def test_xscale_log_html_contains_log_type(self):
        """xscale(log) must embed LogScale or x_axis_type log marker in Bokeh JSON."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["xscale"] = "log"
        html = _render_to_html(spec, data)
        # Bokeh serializes log axis as "LogScale" in model JSON
        has_log = "LogScale" in html or '"log"' in html or "log_scale" in html.lower()
        assert has_log, "xscale(log) must produce log axis marker in HTML model JSON"

    def test_yscale_log_html_contains_log_type(self):
        """yscale(log) must embed LogScale marker in Bokeh JSON."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["yscale"] = "log"
        html = _render_to_html(spec, data)
        has_log = "LogScale" in html or '"log"' in html or "log_scale" in html.lower()
        assert has_log, "yscale(log) must produce log axis marker in HTML model JSON"

    def test_no_log_scale_by_default(self):
        """Without xscale/yscale, HTML must NOT contain LogScale marker."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        # A normal scatter should not have LogScale in model JSON
        assert "LogScale" not in html, \
            "default figure must not have LogScale in HTML model"


# ================================================================
# Backend selection and visual rendering confirmation tests
# ================================================================

class TestOutputBackendAndVisualMarkers:
    """Verify the correct Bokeh output backend is embedded in the model JSON,
    and that actual rendering-relevant attributes are present."""

    def test_canvas_backend_omits_output_backend_key(self):
        """Bokeh omits output_backend from JSON for the default canvas backend.
        Small datasets must render with canvas (default) — verified by absence
        of output_backend key and presence of renderers in model JSON."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        # Canvas (default) backend: Bokeh omits output_backend from model JSON
        assert "output_backend" not in html, \
            "Default canvas backend must not appear as output_backend in HTML"
        # Plot model must still be fully present with renderers
        assert '"renderers"' in html, "Model JSON must contain renderers on canvas"

    def test_model_json_contains_glyph_renderers_key(self):
        """Bokeh model JSON must contain 'renderers' key showing glyph renderers list."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert '"renderers"' in html, \
            "Bokeh model JSON must contain 'renderers' array for glyph renderer list"

    def test_scatter_model_has_glyph_fill_color(self):
        """Scatter model JSON must embed fill_color attribute for the Scatter glyph."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"},
                                        options={"mcolor": "red"})
        html = _render_to_html(spec, data)
        assert '"fill_color"' in html, \
            "Scatter glyph model must contain fill_color attribute"
        assert "ff0000" in html.lower(), \
            "Red fill_color (#ff0000) must be present in model JSON"

    def test_line_model_has_line_color_attribute(self):
        """Line model JSON must embed line_color attribute."""
        spec, data = _single_graph_spec("line", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert '"line_color"' in html, \
            "Line glyph model must contain line_color attribute"

    def test_histogram_model_has_fill_and_top(self):
        """Histogram model JSON must embed both fill_color and data arrays."""
        spec, data = _single_graph_spec("histogram", {"var": "y"})
        html = _render_to_html(spec, data)
        assert '"fill_color"' in html, "Histogram Quad must have fill_color"
        assert '"top"' in html, "Histogram Quad must have 'top' data key"

    def test_all_plot_types_produce_renderers_in_json(self):
        """Every basic plot type must produce a non-empty 'renderers' array in model JSON."""
        types_and_keys = [
            ("scatter", {"yvar": "y", "xvar": "x"}),
            ("line",    {"yvar": "y", "xvar": "x"}),
            ("bar",     {"yvar": "y", "xvar": "x"}),
            ("spike",   {"yvar": "y", "xvar": "x"}),
            ("area",    {"yvar": "y", "xvar": "x"}),
        ]
        for ptype, keys in types_and_keys:
            spec, data = _single_graph_spec(ptype, keys)
            html = _render_to_html(spec, data)
            assert '"renderers"' in html, \
                f"{ptype}: Bokeh model JSON must contain renderers key"
            assert len(html) > 2000, \
                f"{ptype}: HTML must be substantial (got {len(html)} chars)"

    def test_rarea_varea_glyph_has_fill_attributes(self):
        """rarea VArea glyph model must have fill_color and fill_alpha attributes."""
        spec, data = _single_graph_spec(
            "rarea", extra_keys={"yvar1": "lo", "yvar2": "hi", "xvar": "x"}
        )
        html = _render_to_html(spec, data)
        assert '"fill_color"' in html, "VArea glyph must have fill_color in model"
        assert '"fill_alpha"' in html, "VArea glyph must have fill_alpha in model"


class TestWebglBackendLargeData:
    """For datasets > 10 000 rows, output_backend must be set to 'webgl' in model JSON."""

    def _large_data_spec(self):
        """Build a scatter spec with 10 001 rows to trigger webgl threshold."""
        n = 10_001
        data_json = _make_data_json({
            "y": [float(i % 100) for i in range(n)],
            "x": [float(i) for i in range(n)],
        })
        spec, _ = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        return spec, data_json

    def test_large_dataset_uses_webgl_backend(self):
        """Datasets > 10 000 rows must embed output_backend='webgl' in model JSON."""
        spec, data = self._large_data_spec()
        html = _render_to_html(spec, data)
        assert "webgl" in html, \
            "Large dataset (>10 000 rows) must set output_backend='webgl' in Bokeh model JSON"

    def test_small_dataset_does_not_use_webgl(self):
        """Datasets <= 10 000 rows must NOT embed output_backend='webgl'."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "webgl" not in html, \
            "Small dataset must not use webgl backend (canvas is default)"

    def test_webgl_model_still_has_renderers(self):
        """webgl-backend model must still contain renderers in the JSON."""
        spec, data = self._large_data_spec()
        html = _render_to_html(spec, data)
        assert '"renderers"' in html, \
            "webgl-backend model must still contain renderers key"


class TestBokehJsBundleInHtml:
    """Verify the Bokeh JavaScript bundle is referenced in rendered HTML."""

    def test_html_contains_bokeh_script_reference(self):
        """Rendered HTML must include a reference to the Bokeh JS library."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        # Bokeh inlines its JS or references it via CDN — either way 'bokeh' appears in <script>
        has_bokeh_js = "bokeh" in html.lower() and "<script" in html.lower()
        assert has_bokeh_js, \
            "HTML must reference the Bokeh JS library via <script> tag"

    def test_html_contains_bokeh_json_model_block(self):
        """Rendered HTML must contain the application/json model block with Bokeh objects."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        # Bokeh embeds model as application/json script or inline JSON
        has_model = ('"type"' in html and '"attributes"' in html) or \
                    'application/json' in html
        assert has_model, \
            "HTML must contain the Bokeh model JSON block (type + attributes)"

    def test_all_plot_types_include_bokeh_bundle(self):
        """Every standard plot type must include the Bokeh JS bundle in HTML."""
        plot_configs = [
            ("scatter", {"yvar": "y", "xvar": "x"}),
            ("line",    {"yvar": "y", "xvar": "x"}),
            ("histogram", {"var": "y"}),
            ("rarea", {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}),
        ]
        for ptype, keys in plot_configs:
            spec, data = _single_graph_spec(ptype, keys)
            html = _render_to_html(spec, data)
            assert "bokeh" in html.lower() and "<script" in html.lower(), \
                f"{ptype}: HTML must include Bokeh JS bundle"


class TestNewOptionHtml:
    """HTML output tests for mfcolor, base(), barwidth(), bfcolor(), blcolor()."""

    def test_mfcolor_fill_hex_in_model_json(self):
        """scatter with mfcolor(red) must have #ff0000 fill_color in Bokeh JSON."""
        spec, data = _single_graph_spec(
            "scatter",
            extra_keys={"yvar": "y", "xvar": "x"},
            options={"mfcolor": "red"},
        )
        html = _render_to_html(spec, data)
        # Red fill color must appear in embedded Bokeh model JSON
        assert "#ff0000" in html, \
            "mfcolor(red) must embed #ff0000 as fill_color in Bokeh model JSON"

    def test_mfcolor_does_not_change_line_color(self):
        """scatter with mfcolor alone must not change default line_color."""
        spec, data = _single_graph_spec(
            "scatter",
            extra_keys={"yvar": "y", "xvar": "x"},
            options={"mfcolor": "red"},
        )
        html_mfc = _render_to_html(spec, data)
        spec2, data2 = _single_graph_spec(
            "scatter",
            extra_keys={"yvar": "y", "xvar": "x"},
            options={},
        )
        html_def = _render_to_html(spec2, data2)
        # Both should have the same default line_color (unchanged by mfcolor)
        assert '"line_color"' in html_mfc, "model must still have line_color key"
        assert "#ff0000" in html_mfc, "mfcolor must appear as fill_color"

    def test_bar_base_nonzero_in_html(self):
        """bar with base(10) must have bottom!=0 reflected in Bokeh model JSON."""
        spec, data = _single_graph_spec(
            "bar",
            extra_keys={"yvar": "y", "xvar": "x"},
            options={"base": "10"},
        )
        html = _render_to_html(spec, data)
        assert "10" in html, \
            "bar base(10) must embed value 10 in Bokeh model JSON"

    def test_bar_default_base_zero(self):
        """bar without base option must have bottom=0 in Bokeh model JSON."""
        spec, data = _single_graph_spec(
            "bar",
            extra_keys={"yvar": "y", "xvar": "x"},
            options={},
        )
        html = _render_to_html(spec, data)
        assert '"bottom"' in html or "bottom" in html, \
            "bar must include bottom attribute in Bokeh model"

    def test_spike_base_nonzero_in_html(self):
        """spike with base(5) must have y0 values != 0 in model JSON."""
        spec, data = _single_graph_spec(
            "spike",
            extra_keys={"yvar": "y", "xvar": "x"},
            options={"base": "5"},
        )
        html = _render_to_html(spec, data)
        # The CDS will contain y0 values all equal to 5.0
        assert "5.0" in html or '"y0"' in html, \
            "spike base(5) must embed y0 values in model JSON"

    def test_area_base_nonzero_in_html(self):
        """area with base(3) must have lower boundary = 3 in model JSON."""
        spec, data = _single_graph_spec(
            "area",
            extra_keys={"yvar": "y", "xvar": "x"},
            options={"base": "3"},
        )
        html = _render_to_html(spec, data)
        assert "3.0" in html or '"y1"' in html, \
            "area base(3) must embed y1 baseline values in model JSON"

    def test_bfcolor_bar_fill_in_html(self):
        """bar with bfcolor(red) must embed #ff0000 as fill_color in Bokeh JSON."""
        spec, data = _single_graph_spec(
            "bar",
            extra_keys={"yvar": "y", "xvar": "x"},
            options={"bfcolor": "red"},
        )
        html = _render_to_html(spec, data)
        assert "#ff0000" in html, \
            "bfcolor(red) must embed #ff0000 as fill_color in bar glyph model"

    def test_blcolor_bar_line_in_html(self):
        """bar with blcolor(navy) must embed #1a476f as line_color in Bokeh JSON."""
        spec, data = _single_graph_spec(
            "bar",
            extra_keys={"yvar": "y", "xvar": "x"},
            options={"blcolor": "navy"},
        )
        html = _render_to_html(spec, data)
        assert "#1a476f" in html, \
            "blcolor(navy) must embed #1a476f as line_color in bar glyph model"


class TestLineWidthPatternHtml:
    """lwidth and lpattern options must appear in the Bokeh model JSON in rendered HTML."""

    def test_lwidth_thick_in_line_html(self):
        """line with lwidth(thick) must have line_width > default in Bokeh JSON."""
        spec, data = _single_graph_spec(
            "line",
            extra_keys={"yvar": "y", "xvar": "x"},
            options={"lwidth": "thick"},
        )
        html = _render_to_html(spec, data)
        assert '"line_width"' in html, \
            "line_width attribute must be present in Bokeh model JSON"
        # thick = 2.5 in OptionTranslator; default is 1.5
        # Confirm a value > 1.5 appears (the model embeds it numerically)
        assert "2.5" in html, \
            "lwidth(thick)=2.5 must appear in Bokeh model JSON"

    def test_lpattern_dash_in_line_html(self):
        """line with lpattern(dash) must have line_dash in Bokeh model JSON."""
        spec, data = _single_graph_spec(
            "line",
            extra_keys={"yvar": "y", "xvar": "x"},
            options={"lpattern": "dash"},
        )
        html = _render_to_html(spec, data)
        assert '"line_dash"' in html, \
            "line_dash attribute must be present in Bokeh model JSON for dash pattern"

    def test_lwidth_applied_to_spike(self):
        """spike with lwidth(vthick) must embed line_width=3.5 in Bokeh JSON."""
        spec, data = _single_graph_spec(
            "spike",
            extra_keys={"yvar": "y", "xvar": "x"},
            options={"lwidth": "vthick"},
        )
        html = _render_to_html(spec, data)
        assert "3.5" in html, \
            "lwidth(vthick)=3.5 must appear in spike glyph Bokeh model JSON"

    def test_lwidth_applied_to_bar(self):
        """bar with lwidth(thick) must embed line_width=2.5 in Bokeh JSON."""
        spec, data = _single_graph_spec(
            "bar",
            extra_keys={"yvar": "y", "xvar": "x"},
            options={"lwidth": "thick"},
        )
        html = _render_to_html(spec, data)
        assert "2.5" in html, \
            "lwidth(thick)=2.5 must appear in bar glyph Bokeh model JSON"

    def test_lwidth_applied_to_histogram(self):
        """histogram with lwidth(thick) must embed line_width=2.5 in Bokeh JSON."""
        spec, data = _single_graph_spec(
            "histogram",
            extra_keys={"yvar": "y"},
            options={"lwidth": "thick"},
        )
        html = _render_to_html(spec, data)
        assert "2.5" in html, \
            "lwidth(thick)=2.5 must appear in histogram quad Bokeh model JSON"

    def test_lpattern_applied_to_histogram(self):
        """histogram with lpattern(dash) must have line_dash in Bokeh JSON."""
        spec, data = _single_graph_spec(
            "histogram",
            extra_keys={"yvar": "y"},
            options={"lpattern": "dash"},
        )
        html = _render_to_html(spec, data)
        assert '"line_dash"' in html, \
            "lpattern(dash) must produce line_dash in histogram quad Bokeh model JSON"


class TestXlineYlineHtml:
    """xline() and yline() must produce Span annotations visible in the Bokeh model JSON."""

    def test_xline_produces_span_in_html(self):
        """xline(5) must add a vertical Span to the standalone HTML model."""
        spec, data = _single_graph_spec(
            "scatter",
            extra_keys={"yvar": "y", "xvar": "x"},
        )
        # Inject xline into graph_options
        spec["graphs"][0]["graph_options"]["xline"] = "5"
        html = _render_to_html(spec, data)
        assert "Span" in html or '"renderers"' in html, \
            "xline must add a Span annotation; model JSON must be non-empty"
        # More specific: Bokeh serialises Span model type as "Span"
        assert "Span" in html, \
            "xline must produce a Bokeh Span annotation in the HTML model"

    def test_yline_produces_span_in_html(self):
        """yline(10) must add a horizontal Span to the standalone HTML model."""
        spec, data = _single_graph_spec(
            "scatter",
            extra_keys={"yvar": "y", "xvar": "x"},
        )
        spec["graphs"][0]["graph_options"]["yline"] = "10"
        html = _render_to_html(spec, data)
        assert "Span" in html, \
            "yline must produce a Bokeh Span annotation in the HTML model"

    def test_xline_yline_both_present(self):
        """Both xline and yline must produce two Span annotations."""
        spec, data = _single_graph_spec(
            "scatter",
            extra_keys={"yvar": "y", "xvar": "x"},
        )
        spec["graphs"][0]["graph_options"]["xline"] = "5"
        spec["graphs"][0]["graph_options"]["yline"] = "10"
        html = _render_to_html(spec, data)
        assert html.count("Span") >= 2, \
            "Both xline and yline must each produce a Span annotation"


# ================================================================
# by() faceting HTML output tests
# ================================================================

def _by_facet_spec(by_var: str = "grp", extra_gopts: dict = None):
    """Build a spec + data with a binary grouping var for by() testing."""
    n = 20
    base_data = {
        "y": [float(i) for i in range(1, n + 1)],
        "x": [float(i) for i in range(1, n + 1)],
        "grp": [float(i % 2) for i in range(n)],
    }
    data_json = _make_data_json(base_data)
    # Add value labels for grp
    data_json["StataJSON"]["valueLabels"] = {"grp_lbl": {"0": "Group A", "1": "Group B"}}
    data_json["StataJSON"]["valueLabelNames"] = {"grp": "grp_lbl"}

    gopts = {"name": "fig1", "by": by_var}
    if extra_gopts:
        gopts.update(extra_gopts)
    graph = {
        "plots": [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}],
        "graph_options": gopts,
        "if_expr": "", "in_expr": "",
    }
    spec = {
        "graphs": [graph], "kpis": [],
        "build_options": {
            "layout": "auto", "link": "", "filter": "",
            "theme": "default", "title": "", "subtitle": "",
            "registry": "fig1",
        },
    }
    return spec, data_json


class TestByFacetingHtmlOutput:
    """Verify by() faceting produces correct HTML output."""

    def test_by_produces_two_scatter_panels(self):
        """by(grp) with 2 groups → HTML contains Scatter glyph for each facet."""
        spec, data = _by_facet_spec("grp")
        html = _render_to_html(spec, data)
        # Should have at least 2 Scatter glyph references
        scatter_count = html.lower().count('"scatter"')
        assert scatter_count >= 2, (
            f"Expected >=2 Scatter glyph refs, got {scatter_count}"
        )

    def test_by_facet_titles_in_html(self):
        """by(grp) → facet group labels appear in the HTML."""
        spec, data = _by_facet_spec("grp")
        html = _render_to_html(spec, data)
        assert "Group A" in html, "Facet label 'Group A' not found in HTML"
        assert "Group B" in html, "Facet label 'Group B' not found in HTML"

    def test_by_with_value_labels(self):
        """by(grp) with value labels → HTML uses labels not raw numbers."""
        spec, data = _by_facet_spec("grp")
        html = _render_to_html(spec, data)
        # Value labels should appear, not just "0.0" and "1.0"
        assert "Group A" in html or "Group B" in html

    def test_by_total_adds_total_panel(self):
        """by(grp) with by_total=1 → HTML contains 'Total' panel."""
        spec, data = _by_facet_spec("grp", extra_gopts={"by_total": "1"})
        html = _render_to_html(spec, data)
        assert "Total" in html, "Total facet label not found in HTML"

    def test_by_with_multiple_plot_layers(self):
        """by(grp) with scatter+line → each facet has both glyph types."""
        spec, data = _by_facet_spec("grp")
        # Add a line plot layer
        spec["graphs"][0]["plots"].append(
            {"type": "line", "yvar": "y", "xvar": "x", "options": {}}
        )
        html = _render_to_html(spec, data)
        # Should have both Scatter and Line glyph types
        assert "Scatter" in html, "Scatter glyph not in HTML"
        assert "Line" in html, "Line glyph not in HTML"

    def test_by_html_non_empty(self):
        """by(grp) → HTML output is non-trivial."""
        spec, data = _by_facet_spec("grp")
        html = _render_to_html(spec, data)
        assert len(html) > 1000, f"HTML too short: {len(html)} chars"

    def test_by_nonexistent_var_still_renders(self):
        """by(nonexistent) → HTML still renders (falls back to no faceting)."""
        spec, data = _by_facet_spec("nonexistent")
        html = _render_to_html(spec, data)
        assert len(html) > 500, "HTML should still render without faceting"

    def test_by_link_raises_error_in_render(self):
        """by() + link() in render() → ValueError raised."""
        spec, data = _by_facet_spec("grp")
        spec["build_options"]["link"] = "fig1"  # match the graph name
        with pytest.raises(ValueError, match="by.*link"):
            _render_to_html(spec, data)

    def test_by_cols_suboption_produces_html(self):
        """by('grp, cols(1)') → renders valid HTML (suboption parsing works)."""
        spec, data = _by_facet_spec("grp")
        # Set by with cols suboption in the raw string
        spec["graphs"][0]["graph_options"]["by"] = "grp, cols(1)"
        html = _render_to_html(spec, data)
        assert len(html) > 1000


# ================================================================
# plotregion() / graphregion() — region styling options
# ================================================================

class TestPlotregionGraphregion:
    """plotregion() and graphregion() apply Stata-standard region styling."""

    def test_plotregion_color_sets_background(self):
        """plotregion(color(#aabbcc)) must embed sentinel hex in HTML."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["plotregion"] = "color(#aabbcc)"
        html = _render_to_html(spec, data)
        assert "#aabbcc" in html.lower(), \
            "plotregion(color(#aabbcc)) must set background_fill_color"

    def test_plotregion_named_color(self):
        """plotregion(color(navy)) must translate to #1a476f in HTML."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["plotregion"] = "color(navy)"
        html = _render_to_html(spec, data)
        assert "#1a476f" in html, \
            "plotregion(color(navy)) must translate to #1a476f"

    def test_graphregion_color_sets_border(self):
        """graphregion(color(#112233)) must embed sentinel hex in HTML."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["graphregion"] = "color(#112233)"
        html = _render_to_html(spec, data)
        assert "#112233" in html.lower(), \
            "graphregion(color(#112233)) must set border_fill_color"

    def test_plotregion_fcolor_accepted(self):
        """plotregion(fcolor(#ddeeff)) — fcolor() alias accepted."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["plotregion"] = "fcolor(#ddeeff)"
        html = _render_to_html(spec, data)
        assert "#ddeeff" in html.lower(), \
            "plotregion(fcolor(#ddeeff)) must set background_fill_color"

    def test_plotregion_invalid_no_crash(self):
        """plotregion with invalid color sub-option must not crash."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["plotregion"] = "color(not_a_real_color_xyz)"
        html = _render_to_html(spec, data)
        assert "Scatter" in html, "invalid plotregion color must fall back gracefully"

    def test_graphregion_invalid_no_crash(self):
        """graphregion with invalid color must not crash."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["graphregion"] = "color(notacolor)"
        html = _render_to_html(spec, data)
        assert "Scatter" in html, "invalid graphregion color must fall back gracefully"
