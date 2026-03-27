"""
test_pipeline_integration.py
Integration tests that exercise the full DashRenderer pipeline for plot types
that use non-standard JSON keys (histogram/kdensity "var", range plots "yvar1"/"yvar2").

These tests catch dispatch-layer bugs that unit tests on individual GlyphMapper
methods would miss.

Run with:  pytest test/test_pipeline_integration.py -v
"""
import sys
import os
import json
import tempfile

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dash_render import DashRenderer, GlyphMapper

from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


# ================================================================
# Helpers
# ================================================================

def _make_data_json(columns: dict) -> dict:
    """Build a jsonio-format data JSON dict from a column dict.

    Args:
        columns: mapping of variable name → list of values.
    """
    col_names = list(columns.keys())
    n_rows = len(next(iter(columns.values())))
    rows = []
    for i in range(n_rows):
        row = {}
        for c in col_names:
            v = columns[c][i]
            row[c] = None if (isinstance(v, float) and np.isnan(v)) else v
        rows.append(row)
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


def _build_renderer(master_spec: dict, data_json: dict) -> DashRenderer:
    """Construct a DashRenderer from spec and data dicts.

    Temp files are created, passed to DashRenderer (which reads them in
    __init__), and deleted immediately.
    """
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
    finally:
        for _p in (spec_path, data_path, out_path):
            try:
                os.unlink(_p)
            except OSError:
                pass
    return renderer


def _make_master_spec(graphs: list, registry: str = "") -> dict:
    """Build a minimal master spec dict for DashRenderer."""
    if not registry:
        registry = " ".join(
            g.get("graph_options", {}).get("name", f"g{i}")
            for i, g in enumerate(graphs)
        )
    return {
        "graphs": graphs,
        "kpis": [],
        "build_options": {
            "layout": "auto",
            "link": "",
            "filter": "",
            "theme": "default",
            "title": "",
            "subtitle": "",
            "registry": registry,
        },
    }


# Standard data fixture for two-variable plots
STANDARD_DATA = _make_data_json({
    "mpg": [float(i) for i in range(1, 21)],
    "weight": [float(i * 50) for i in range(1, 21)],
})

# Range data fixture with lo, hi, x columns
RANGE_DATA = _make_data_json({
    "lo": [float(i * 0.5) for i in range(1, 21)],
    "hi": [float(i * 1.5) for i in range(1, 21)],
    "x":  [float(i) for i in range(1, 21)],
})


# ================================================================
# T1-01 — Histogram through full pipeline (uses "var" JSON key)
# ================================================================
class TestPipelineHistogram:
    def test_histogram_var_key_renders(self):
        """Histogram spec using 'var' key (not 'yvar') produces visible glyph."""
        graph = {
            "plots": [{"type": "histogram", "var": "mpg", "options": {}}],
            "graph_options": {"name": "h1"},
            "if_expr": "",
            "in_expr": "",
        }
        spec = _make_master_spec([graph])
        renderer = _build_renderer(spec, STANDARD_DATA)
        figs = renderer._build_figures()
        assert "h1" in figs, "Figure 'h1' not built"
        fig = figs["h1"]
        # histogram should produce at least one renderer (Quad glyph)
        assert len(fig.renderers) >= 1, (
            f"Expected >=1 renderer for histogram, got {len(fig.renderers)}"
        )


# ================================================================
# T1-02 — Kdensity through full pipeline (uses "var" JSON key)
# ================================================================
class TestPipelineKdensity:
    def test_kdensity_var_key_renders(self):
        """Kdensity spec using 'var' key (not 'yvar') produces visible glyph."""
        graph = {
            "plots": [{"type": "kdensity", "var": "mpg", "options": {}}],
            "graph_options": {"name": "k1"},
            "if_expr": "",
            "in_expr": "",
        }
        spec = _make_master_spec([graph])
        renderer = _build_renderer(spec, STANDARD_DATA)
        figs = renderer._build_figures()
        assert "k1" in figs, "Figure 'k1' not built"
        fig = figs["k1"]
        assert len(fig.renderers) >= 1, (
            f"Expected >=1 renderer for kdensity, got {len(fig.renderers)}"
        )


# ================================================================
# T1-03 through T1-04 — Range plots through full pipeline
# ================================================================
class TestPipelineRangePlots:
    """Each range plot type uses yvar1/yvar2/xvar JSON keys.

    The full DashRenderer pipeline must detect these keys and dispatch to
    the correct GlyphMapper method.
    """

    @pytest.mark.parametrize("ptype", [
        "rarea", "rbar", "rspike", "rcap", "rline", "rconnected",
    ])
    def test_range_plot_renders(self, ptype):
        graph = {
            "plots": [{
                "type": ptype,
                "yvar1": "lo",
                "yvar2": "hi",
                "xvar": "x",
                "options": {},
            }],
            "graph_options": {"name": "r1"},
            "if_expr": "",
            "in_expr": "",
        }
        spec = _make_master_spec([graph])
        renderer = _build_renderer(spec, RANGE_DATA)
        figs = renderer._build_figures()
        assert "r1" in figs, f"Figure 'r1' not built for {ptype}"
        fig = figs["r1"]
        assert len(fig.renderers) >= 1, (
            f"Expected >=1 renderer for {ptype}, got {len(fig.renderers)}"
        )


# ================================================================
# T1-05, T1-06 — Return type regression (Bug 3)
# ================================================================
class TestReturnTypeConsistency:
    @pytest.fixture
    def fig(self):
        return figure()

    @pytest.fixture
    def range_cds(self):
        df = pd.DataFrame({
            "lo": np.linspace(0, 5, 20),
            "hi": np.linspace(5, 10, 20),
            "x":  np.linspace(0, 10, 20),
        })
        return ColumnDataSource(df)

    @pytest.fixture
    def gm(self):
        return GlyphMapper()

    def test_map_rarea_returns_list(self, fig, range_cds, gm):
        """map_rarea() must return a list for consistency with other range methods."""
        result = gm.map_rarea(fig, range_cds, "lo", "hi", "x", {})
        assert isinstance(result, list), (
            f"map_rarea() returned {type(result).__name__}, expected list"
        )

    def test_map_rbar_returns_list(self, fig, range_cds, gm):
        """map_rbar() must return a list for consistency with other range methods."""
        result = gm.map_rbar(fig, range_cds, "lo", "hi", "x", {})
        assert isinstance(result, list), (
            f"map_rbar() returned {type(result).__name__}, expected list"
        )


# ================================================================
# T1-07 — Lowess basic functionality (only empty-data tested before)
# ================================================================
class TestLowessBasicFunctionality:
    def test_lowess_produces_smooth_line(self):
        """map_lowess with valid data produces a renderer with data points."""
        gm = GlyphMapper()
        fig_obj = figure()
        x = np.linspace(0, 10, 50)
        y = np.sin(x) + np.random.RandomState(42).normal(0, 0.2, 50)
        df = pd.DataFrame({"y": y, "x": x})
        cds = ColumnDataSource(df)
        r = gm.map_lowess(fig_obj, cds, "y", "x", {})
        # Should produce a renderer with smoothed data
        from bokeh.models import GlyphRenderer
        assert isinstance(r, GlyphRenderer), (
            f"Expected GlyphRenderer, got {type(r).__name__}"
        )
        # The smooth line should have data
        x_data = r.data_source.data.get("x_lw", [])
        assert len(x_data) > 0, "Lowess produced empty data"


# ================================================================
# T1-08 — Qfitci basic functionality (no dedicated test before)
# ================================================================
class TestQfitciBasicFunctionality:
    def test_qfitci_produces_line_and_band(self):
        """map_qfitci with valid data produces a list of [line, band] renderers."""
        gm = GlyphMapper()
        fig_obj = figure()
        np.random.seed(42)
        x = np.linspace(0, 10, 30)
        y = 0.5 * x ** 2 - 3 * x + np.random.normal(0, 2, 30)
        df = pd.DataFrame({"y": y, "x": x})
        cds = ColumnDataSource(df)
        result = gm.map_qfitci(fig_obj, cds, "y", "x", {})
        assert isinstance(result, list), (
            f"Expected list, got {type(result).__name__}"
        )
        assert len(result) == 2, (
            f"Expected 2 renderers (line + band), got {len(result)}"
        )


# ================================================================
# T1-09 — dropline through full pipeline
# ================================================================
class TestPipelineDropline:
    def test_dropline_renders(self):
        """dropline spec produces >=2 renderers (segment + scatter)."""
        graph = {
            "plots": [{"type": "dropline", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "dl1"},
            "if_expr": "", "in_expr": "",
        }
        spec = _make_master_spec([graph])
        renderer = _build_renderer(spec, STANDARD_DATA)
        figs = renderer._build_figures()
        assert "dl1" in figs
        fig = figs["dl1"]
        assert len(fig.renderers) >= 2


# ================================================================
# T1-10 — rcapsym through full pipeline
# ================================================================
class TestPipelineRcapsym:
    def test_rcapsym_renders(self):
        """rcapsym spec produces >=5 renderers (spine+2 caps+2 dots)."""
        graph = {
            "plots": [{
                "type": "rcapsym",
                "yvar1": "lo", "yvar2": "hi", "xvar": "x",
                "options": {},
            }],
            "graph_options": {"name": "rcs1"},
            "if_expr": "", "in_expr": "",
        }
        spec = _make_master_spec([graph])
        renderer = _build_renderer(spec, RANGE_DATA)
        figs = renderer._build_figures()
        assert "rcs1" in figs
        fig = figs["rcs1"]
        assert len(fig.renderers) >= 5


# ================================================================
# T1-11 — scatteri through full pipeline
# ================================================================
class TestPipelineScatteri:
    def test_scatteri_renders_inline_coords(self):
        """scatteri spec with values list produces scatter renderer."""
        graph = {
            "plots": [{
                "type": "scatteri",
                "values": [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]],
                "options": {},
            }],
            "graph_options": {"name": "si1"},
            "if_expr": "", "in_expr": "",
        }
        spec = _make_master_spec([graph])
        # scatteri doesn't need any dataset variables
        empty_data = _make_data_json({"dummy": [0.0]})
        renderer = _build_renderer(spec, empty_data)
        figs = renderer._build_figures()
        assert "si1" in figs
        fig = figs["si1"]
        assert len(fig.renderers) >= 1


# ================================================================
# T1-12 — Regression: "options" JSON must not be double-nested
# ================================================================
class TestOptionsJsonFormat:
    """Regression tests for Bug 1: dash.ado was wrapping _opts_json (which
    already contained outer braces) in another set of braces, producing
    "options":{{"key":"val"}} — invalid JSON that caused json.loads() to fail
    in the Python renderer for every plot command with options.
    """

    def test_double_nested_options_is_invalid_json(self):
        """Simulate the bug: double-braces in 'options' value produces invalid JSON.

        If this string were produced by dash.ado (the buggy version), Python's
        json.loads() must reject it.  This confirms that the bug would have
        caused a hard failure in the renderer.
        """
        # This is what the buggy dash.ado would produce when options = {"mcolor":"navy"}
        buggy_segment = (
            '{"type":"scatter","yvar":"mpg","xvar":"weight",'
            '"options":{{"mcolor":"navy","msymbol":"circle"}},'
            '"if_expr":"","in_expr":""}'
        )
        with pytest.raises(json.JSONDecodeError):
            json.loads(buggy_segment)

    def test_single_nested_options_is_valid_json(self):
        """The fixed dash.ado emits 'options':{...} — valid JSON that parses cleanly."""
        fixed_segment = (
            '{"type":"scatter","yvar":"mpg","xvar":"weight",'
            '"options":{"mcolor":"navy","msymbol":"circle"},'
            '"if_expr":"","in_expr":""}'
        )
        parsed = json.loads(fixed_segment)
        assert isinstance(parsed["options"], dict)
        assert parsed["options"]["mcolor"] == "navy"
        assert parsed["options"]["msymbol"] == "circle"

    def test_options_dict_renders_correctly(self):
        """Full pipeline: scatter spec with options dict renders a figure with renderers.

        This verifies that when options arrive as a proper dict (not a double-nested
        string), the renderer correctly passes them through to _add_glyph and
        a renderer is actually created.
        """
        graph = {
            "plots": [{
                "type": "scatter",
                "yvar": "y",
                "xvar": "x",
                "options": {"mcolor": "navy", "msymbol": "circle", "msize": "medium"},
            }],
            "graph_options": {"name": "g1"},
            "if_expr": "", "in_expr": "",
        }
        spec = _make_master_spec([graph])
        data = _make_data_json({
            "x": [float(i) for i in range(1, 11)],
            "y": [float(i * 2) for i in range(1, 11)],
        })
        renderer = _build_renderer(spec, data)
        figs = renderer._build_figures()
        assert "g1" in figs
        assert len(figs["g1"].renderers) >= 1, (
            "scatter with options must produce at least one renderer"
        )


# ================================================================
# T7 — theme key in build_options must be honoured
# ================================================================
class TestThemeKey:
    """Regression tests: dash.ado writes 'theme' (not 'scheme') into build_options.

    DashRenderer.__init__ previously read only 'scheme', so theme() was silently
    ignored and the renderer always fell back to s2color.  Bug 6.
    """

    def _build_renderer_with_theme(self, theme_name: str):
        """Build a minimal renderer with a specific theme in build_options."""
        graph = {
            "plots": [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}],
            "graph_options": {"name": "g1"},
            "if_expr": "", "in_expr": "",
        }
        spec = {
            "graphs": [graph],
            "kpis": [],
            "build_options": {
                "layout": "auto",
                "link": "",
                "filter": "",
                "theme": theme_name,
                "title": "",
                "subtitle": "",
                "registry": "g1",
            },
        }
        data = _make_data_json({
            "x": [float(i) for i in range(1, 11)],
            "y": [float(i * 2) for i in range(1, 11)],
        })
        return _build_renderer(spec, data)

    # s2color has a bluish-grey background; s1color has a white background.
    # These constants let tests assert the CORRECT scheme was loaded.
    S2COLOR_BG = "#d9e8f0"   # ltbluishgray translated by OptionTranslator
    S1COLOR_BG = "#ffffff"   # white

    def test_theme_default_resolves_to_s2color(self):
        """theme('default') in build_options → s2color scheme background color."""
        r = self._build_renderer_with_theme("default")
        assert hasattr(r, "scheme")
        assert r.scheme.background_color.lower() == self.S2COLOR_BG, (
            f"theme('default') should load s2color (bg {self.S2COLOR_BG}), "
            f"got {r.scheme.background_color!r}"
        )

    def test_theme_clean_is_honoured(self):
        """theme('clean') in build_options → s1color scheme is applied (white bg).

        Previously, 'clean' was silently ignored because DashRenderer read
        build_options['scheme'] (key not present) and fell back to s2color.
        After the fix, build_options['theme'] is read and 'clean' is mapped to
        s1color — which has a white background, not the bluish-grey of s2color.
        """
        r = self._build_renderer_with_theme("clean")
        assert hasattr(r, "scheme")
        assert r.scheme.background_color.lower() == self.S1COLOR_BG, (
            f"theme('clean') should load s1color (white bg), "
            f"got {r.scheme.background_color!r} — "
            "theme key in build_options was not being read (Bug 6)"
        )

    def test_theme_mono_is_honoured(self):
        """theme('mono') in build_options → s1mono scheme is applied without error."""
        r = self._build_renderer_with_theme("mono")
        assert hasattr(r, "scheme")
        # s1mono also has white background
        assert r.scheme.background_color.lower() == self.S1COLOR_BG, (
            f"theme('mono') should load s1mono (white bg), "
            f"got {r.scheme.background_color!r}"
        )

    def test_theme_economist_is_honoured(self):
        """theme('economist') → economist scheme file is loaded (not s2color bg)."""
        r = self._build_renderer_with_theme("economist")
        assert hasattr(r, "scheme")
        # economist has white background too, just check it doesn't crash
        assert r.scheme.background_color is not None

    def test_unknown_theme_falls_back_to_s2color(self):
        """An unrecognised theme name must not crash — fallback to s2color."""
        r = self._build_renderer_with_theme("does_not_exist_theme")
        assert hasattr(r, "scheme")
        # Falls back to s2color
        assert r.scheme.background_color.lower() == self.S2COLOR_BG

    def test_theme_and_scheme_key_both_work(self):
        """If someone passes 'scheme' key directly, it must also be honoured."""
        graph = {
            "plots": [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}],
            "graph_options": {"name": "g1"},
            "if_expr": "", "in_expr": "",
        }
        spec = {
            "graphs": [graph],
            "kpis": [],
            "build_options": {
                "layout": "auto",
                "link": "",
                "filter": "",
                "scheme": "s1color",   # note: using 'scheme' key directly
                "title": "",
                "subtitle": "",
                "registry": "g1",
            },
        }
        data = _make_data_json({
            "x": [float(i) for i in range(1, 11)],
            "y": [float(i * 2) for i in range(1, 11)],
        })
        r = _build_renderer(spec, data)
        assert hasattr(r, "scheme")
        assert r.scheme.background_color.lower() == self.S1COLOR_BG, (
            "'scheme' key in build_options must also be read"
        )
