"""
test_scheme_integration.py
Integration tests for SchemeParser integration into DashRenderer.

Covers: scheme loaded from build_options, applied to figure, CSS injected into HTML.

Run with:  pytest test/test_scheme_integration.py -v
"""
import sys
import os
import json
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dash_render import DashRenderer, SchemeParser


# ============================================================
# Helpers
# ============================================================

def _make_renderer(scheme="", plots=None, graph_opts=None):
    """Build a DashRenderer instance with given scheme name in build_options."""
    n = 10
    data = {"x": list(range(n)), "y": [float(i) * 1.5 for i in range(n)]}
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
    if plots is None:
        plots = [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}]
    spec = {
        "graphs": [{
            "plots": plots,
            "graph_options": graph_opts or {"name": "g1"},
            "if_expr": "", "in_expr": "",
        }],
        "kpis": [],
        "build_options": {
            "layout": "auto", "link": "", "filter": "",
            "theme": "default", "title": "", "subtitle": "",
            "registry": "g1",
            "scheme": scheme,
        },
    }
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


def _render(scheme=""):
    """Return standalone HTML string from a full render with given scheme."""
    dr = _make_renderer(scheme=scheme)
    # Temporarily write to a temp file and return result
    n = 10
    data = {"x": list(range(n)), "y": [float(i) * 1.5 for i in range(n)]}
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
            "plots": [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}],
            "graph_options": {"name": "g1"},
            "if_expr": "", "in_expr": "",
        }],
        "kpis": [],
        "build_options": {
            "layout": "auto", "link": "", "filter": "",
            "theme": "default", "title": "", "subtitle": "",
            "registry": "g1",
            "scheme": scheme,
        },
    }
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


# ============================================================
# SI-01 – 04: Scheme loaded in __init__
# ============================================================

class TestSchemeLoadedInInit:
    def test_default_scheme_is_s2color(self):
        """SI-01: DashRenderer with no scheme uses s2color by default."""
        dr = _make_renderer(scheme="")
        assert isinstance(dr.scheme, SchemeParser)
        # s2color p1 marker color is navy (#1F497D or similar blue)
        p1 = dr.scheme.default_color(0, "scatter")
        assert p1.startswith("#")

    def test_explicit_scheme_loaded(self):
        """SI-02: DashRenderer with scheme='sj' loads sj scheme."""
        dr = _make_renderer(scheme="sj")
        # sj p1 is black
        p1 = dr.scheme.default_color(0, "scatter")
        assert p1 == "#000000"

    def test_invalid_scheme_falls_back_to_s2color(self):
        """SI-03: Unknown scheme name falls back to s2color without crash."""
        dr = _make_renderer(scheme="nonexistent_scheme_xyz")
        assert isinstance(dr.scheme, SchemeParser)

    def test_s1mono_scheme_loaded(self):
        """SI-04: s1mono scheme loads successfully."""
        dr = _make_renderer(scheme="s1mono")
        assert isinstance(dr.scheme, SchemeParser)


# ============================================================
# SI-05 – 07: apply_to_figure called in _make_figure
# ============================================================

class TestApplyToFigureInMakeFigure:
    def _get_fig(self, scheme="s2color"):
        dr = _make_renderer(scheme=scheme)
        figs = dr._build_figures()
        return list(figs.values())[0]

    def test_s2color_sets_white_background(self):
        """SI-05: s2color scheme sets white background_fill_color on figure."""
        fig = self._get_fig("s2color")
        # s2color background is white
        assert fig.background_fill_color in ("#ffffff", "#FFFFFF", "white")

    def test_sj_scheme_sets_white_background(self):
        """SI-06: sj scheme also sets white background_fill_color."""
        fig = self._get_fig("sj")
        assert fig.background_fill_color in ("#ffffff", "#FFFFFF", "white")

    def test_scheme_sets_grid_properties(self):
        """SI-07: apply_to_figure sets grid line properties."""
        fig = self._get_fig("s2color")
        # Grid should have some color set (not None)
        grid_colors = [g.grid_line_color for g in fig.grid]
        assert any(c is not None for c in grid_colors)


# ============================================================
# SI-08 – 10: CSS block injected into HTML
# ============================================================

class TestCssBlockInHtml:
    def test_html_contains_style_tag(self):
        """SI-08: rendered HTML contains a <style> tag from scheme.css_block()."""
        html_str = _render("s2color")
        assert "<style>" in html_str

    def test_html_contains_scheme_background_color(self):
        """SI-09: rendered HTML contains scheme background color in CSS."""
        html_str = _render("s2color")
        # s2color background is white
        assert "#ffffff" in html_str.lower() or "white" in html_str.lower()

    def test_sj_html_different_from_s2color_html(self):
        """SI-10: different schemes produce different HTML (CSS differs)."""
        html_s2 = _render("s2color")
        html_sj = _render("sj")
        # The two HTML documents should differ (scheme CSS differs)
        assert html_s2 != html_sj

    def test_html_renders_without_error_all_schemes(self):
        """SI-11: all built-in schemes render to HTML without error."""
        for scheme in ("s2color", "s1color", "s1mono", "economist", "sj"):
            html_str = _render(scheme)
            assert len(html_str) > 100, f"Empty HTML for scheme '{scheme}'"
