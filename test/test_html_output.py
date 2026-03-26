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
