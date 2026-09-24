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
        # ...and its bars.  A histogram with nothing to bin draws an empty
        # quad placeholder, which the count above cannot tell from one that
        # drew.  mpg is 1..20: Stata's default is min(sqrt(20),
        # 10*log10(20)) -> 4 bins of width 4.75 from 1, five cars in each,
        # density 5 / (20 * 4.75).
        [quad] = fig.renderers
        data = quad.data_source.data
        assert list(data["left"]) == [1.0, 5.75, 10.5, 15.25], data
        assert list(data["right"]) == [5.75, 10.5, 15.25, 20.0], data
        assert np.allclose(data["top"], [5 / (20 * 4.75)] * 4), data


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
        """map_lowess with valid data produces a renderer with data points.

        No statsmodels skip: lowess is Stata's smoother in numpy (WP-18).
        """
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
        # The three points, y then x as scatteri reads them: a renderer
        # holding fewer, or none, passed the count above.
        [pts] = fig.renderers
        assert list(pts.data_source.data["y"]) == [1.0, 3.0, 5.0]
        assert list(pts.data_source.data["x"]) == [2.0, 4.0, 6.0]


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
    # s2color's `color background ltbluishgray`, resolved from Stata's own
    # color-ltbluishgray.style ("234 242 243").  The former value #d9e8f0 came
    # from OptionTranslator._COLOR_MAP, which disagrees with Stata for 52 of
    # the 68 colour names they share -- see BASELINE.md finding F7.  The
    # translated schemes carry resolved hex and so are unaffected by that bug.
    S2COLOR_BG = "#eaf2f3"
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


# ================================================================
# Regression: BUG-5 — _collect_graph_vars promoted to static method;
# render() and _setup_sources must both include hover variables in sources
# ================================================================

class TestCollectGraphVarsConsistency:
    """BUG-5 regression: variable collection must be consistent between
    _setup_sources and render(), and must include hover-option variables."""

    def _build_dr(self, hover_var="price"):
        import json, tempfile, os
        vals = [{"mpg": float(20+i), "weight": float(2000+i*100),
                 "price": float(4000+i*200)}
                for i in range(15)]
        data = {"StataJSON": {
            "variableNames": ["mpg", "weight", "price"],
            "variableLabels": {"mpg": "mpg", "weight": "weight", "price": "price"},
            "valueLabels": {}, "valueLabelNames": {},
            "variableTypeIsString": {"mpg": False, "weight": False, "price": False},
            "values": vals,
        }}
        spec = {
            "graphs": [{"plots": [{"type": "scatter", "yvar": "mpg",
                                    "xvar": "weight", "options": {}}],
                         "graph_options": {"name": "g1", "hover": hover_var},
                         "if_expr": "", "in_expr": ""}],
            "kpis": [],
            "build_options": {
                "layout": "auto", "link": "g1", "theme": "default",
                "title": "", "subtitle": "", "registry": "g1",
            },
        }
        sp, dp, op = [tempfile.mkstemp(s)[1] for s in (".json", ".json", ".html")]
        try:
            with open(sp, "w") as f: json.dump(spec, f)
            with open(dp, "w") as f: json.dump(data, f)
            dr = DashRenderer(sp, dp, op)
            dr.render()
        finally:
            for p in (sp, dp, op):
                try: os.unlink(p)
                except OSError: pass
        return dr

    def test_collect_plot_vars_is_static_method(self):
        """BUG-5a: _collect_plot_vars must be a static method on DashRenderer."""
        assert hasattr(DashRenderer, "_collect_plot_vars"), (
            "DashRenderer must have _collect_plot_vars as a static method"
        )
        assert callable(DashRenderer._collect_plot_vars)

    def test_collect_graph_vars_is_static_method(self):
        """BUG-5b: _collect_graph_vars must be a static method on DashRenderer."""
        assert hasattr(DashRenderer, "_collect_graph_vars"), (
            "DashRenderer must have _collect_graph_vars as a static method"
        )
        assert callable(DashRenderer._collect_graph_vars)

    def test_hover_vars_included_in_source(self):
        """BUG-5c: shared CDS must contain hover-option variables."""
        dr = self._build_dr(hover_var="price")
        # The shared source for g1 should include 'price' (from hover option)
        shared_src = dr.sources.get("g1")
        assert shared_src is not None, "Expected a source named 'g1'"
        assert "price" in shared_src.data, (
            "Shared CDS must include 'price' (declared in hover option) "
            f"but only has: {list(shared_src.data.keys())}"
        )

    def test_collect_plot_vars_returns_correct_vars(self):
        """BUG-5d: _collect_plot_vars must extract all variable keys from plots."""
        plots = [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                  "options": {"colorvar": "price"}}]
        result = DashRenderer._collect_plot_vars(plots)
        assert "mpg" in result
        assert "weight" in result
        assert "price" in result  # from options.colorvar


# ================================================================
# TEST-1: Edge-case data — empty dataset, single row, all-NaN, constant
# ================================================================

class TestEdgeCaseData:
    """EC-01 through EC-06: mappers must degrade gracefully for unusual data."""

    def _render_spec(self, plots, values, varnames, extra_build=None):
        """Helper: build and render a DashRenderer from inline data."""
        import json, tempfile, os
        data = {"StataJSON": {
            "variableNames": varnames,
            "variableLabels": {v: v for v in varnames},
            "valueLabels": {}, "valueLabelNames": {},
            "variableTypeIsString": {v: False for v in varnames},
            "values": values,
        }}
        build = {"layout": "auto", "link": "", "theme": "default",
                 "title": "", "subtitle": "", "registry": "g1"}
        if extra_build:
            build.update(extra_build)
        spec = {
            "graphs": [{"plots": plots, "graph_options": {"name": "g1"},
                         "if_expr": "", "in_expr": ""}],
            "kpis": [],
            "build_options": build,
        }
        sp, dp, op = [tempfile.mkstemp(s)[1] for s in (".json", ".json", ".html")]
        try:
            with open(sp, "w") as f: json.dump(spec, f)
            with open(dp, "w") as f: json.dump(data, f)
            dr = DashRenderer(sp, dp, op)
            dr.render()
        finally:
            for p in (sp, dp, op):
                try: os.unlink(p)
                except OSError: pass
        return dr

    # The "does not crash" cases below assert what the render DID, measured
    # 24sep2026 at 68327a8, beside what twoway does with the same data
    # (StataNow 19.5 MP, `twoway <plot> ..., nodraw').  They asserted
    # nothing, so a render that drew garbage, or drew nothing and said
    # nothing, passed as long as it returned.

    def _render_noted(self, **kw):
        """``(renderer, dash's notes)`` for one render."""
        import warnings
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr = self._render_spec(**kw)
        return dr, [str(c.message) for c in caught
                    if str(c.message).startswith("dash")]

    @staticmethod
    def _drawn(dr):
        """``[(glyph type, rows)]`` for every renderer of the one graph."""
        assert list(dr.figures) == ["g1"], list(dr.figures)
        out = []
        for r in dr.figures["g1"].renderers:
            data = r.data_source.data
            out.append((type(r.glyph).__name__,
                        max((len(v) for v in data.values()), default=0)))
        return out

    @pytest.mark.parametrize("plot", [
        {"type": "scatter", "yvar": "mpg", "xvar": "weight"},
        {"type": "histogram", "yvar": "mpg"},
        {"type": "lfit", "yvar": "mpg", "xvar": "weight"},
    ], ids=["scatter", "histogram", "lfit"])
    def test_ec01_an_empty_dataset_builds_the_graph_and_draws_nothing(
            self, plot):
        """EC-01: n=0 renders the graph and draws no point.

        twoway on no observations: scatter draws nothing, rc 0, in silence;
        lfit notes "regress could not fit model", rc 0; histogram stops with
        r(198).  dash keeps the dashboard -- the one graph is built -- and
        draws nothing.  What it says is left unasserted on purpose: today
        it is "variable(s) [...] not found in data source", which is wrong
        about variables that are there (reported as a defect), and silence,
        twoway's answer for scatter, would be as right as a correct note.
        """
        dr, _notes = self._render_noted(
            plots=[dict(plot, options={})], values=[],
            varnames=[v for k, v in plot.items() if k != "type"])
        assert all(rows == 0 for _g, rows in self._drawn(dr))

    def test_ec02_single_row_scatter_draws_its_point(self):
        """EC-02: n=1 scatter draws the one point, as twoway does (rc 0)."""
        dr, notes = self._render_noted(
            plots=[{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            values=[{"mpg": 22.0, "weight": 2500.0}],
            varnames=["mpg", "weight"],
        )
        assert self._drawn(dr) == [("Scatter", 1)]
        r = dr.figures["g1"].renderers[0]
        data = r.data_source.data
        assert list(data[r.glyph.x]) == [2500.0]
        assert list(data[r.glyph.y]) == [22.0]
        assert notes == []

    def test_ec02_single_row_lfit_returns_empty(self):
        """EC-02: n=1 lfit returns empty (needs 2+ points), no crash.

        twoway lfit refuses one observation -- "insufficient observations",
        r(2001) -- and dash keeps the dashboard and names the empty layer.
        This asserted only ``fig is not None``, which any figure satisfies.
        """
        dr, notes = self._render_noted(
            plots=[{"type": "lfit", "yvar": "mpg", "xvar": "weight", "options": {}}],
            values=[{"mpg": 22.0, "weight": 2500.0}],
            varnames=["mpg", "weight"],
        )
        assert self._drawn(dr) == [("Line", 0)]
        assert notes == ["dash: graph 'g1' plot 1 (lfit) drew nothing from 1 "
                         "observations."]

    @pytest.mark.parametrize("ptype,glyph", [("scatter", "Scatter"),
                                             ("histogram", "Quad")])
    def test_ec03_an_all_missing_column_draws_nothing_and_says_so(
            self, ptype, glyph):
        """EC-03: all-NaN renders, draws nothing, and names the layer.

        twoway scatter and twoway histogram both draw nothing here (rc 0).
        """
        plot = {"type": ptype, "yvar": "mpg", "options": {}}
        values = [{"mpg": None} for _ in range(5)]
        varnames = ["mpg"]
        if ptype == "scatter":
            plot["xvar"] = "weight"
            values = [{"mpg": None, "weight": float("nan")} for _ in range(5)]
            varnames = ["mpg", "weight"]
        dr, notes = self._render_noted(plots=[plot], values=values,
                                       varnames=varnames)
        assert self._drawn(dr) == [(glyph, 0)]
        assert notes == ["dash: graph 'g1' plot 1 (%s) drew nothing from 5 "
                         "observations." % ptype]

    _CONST_X = [{"mpg": float(20 + i), "weight": 2500.0} for i in range(10)]

    def test_ec04_constant_x_lfit_passes_through_the_mean(self):
        """EC-04: constant-x lfit degrades gracefully (std==0).

        With no variation in x, Stata's regress omits x and predicts the
        mean of y: twoway lfit draws its points at (2500, 24.5).  dash's fit
        starts there too.  Where it goes after that is the next test.
        """
        dr, _notes = self._render_noted(
            plots=[{"type": "lfit", "yvar": "mpg", "xvar": "weight", "options": {}}],
            values=self._CONST_X, varnames=["mpg", "weight"])
        assert self._drawn(dr) == [("Line", 100)]
        data = dr.figures["g1"].renderers[0].data_source.data
        assert data["x"][0] == 2500.0
        assert data["y"][0] == pytest.approx(24.5, abs=1e-9)

    @pytest.mark.xfail(strict=True, reason=(
        "open defect, measured 24sep2026: _fit_grid widens a zero-width x "
        "range to [x, x+1] and np.polyfit's minimum-norm solution gives the "
        "segment a slope, so dash draws a sloped line from (2500, 24.5) to "
        "(2501, 24.505) where twoway lfit draws every point at (2500, 24.5); "
        "numpy's 'Polyfit may be poorly conditioned' reaches the user too"))
    def test_ec04_constant_x_lfit_draws_what_twoway_draws(self):
        """EC-04, against Stata: `twoway lfit mpg weight' on a constant
        weight -- serset points all (2500, 24.5), and no note."""
        import warnings
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr = self._render_spec(
                plots=[{"type": "lfit", "yvar": "mpg", "xvar": "weight",
                        "options": {}}],
                values=self._CONST_X, varnames=["mpg", "weight"])
        data = dr.figures["g1"].renderers[0].data_source.data
        assert set(np.round(np.asarray(data["x"], float), 9)) == {2500.0}
        assert np.allclose(np.asarray(data["y"], float), 24.5)
        assert not [str(c.message) for c in caught
                    if "poorly conditioned" in str(c.message)]

    def test_ec04_constant_x_lowess_draws_nothing_and_says_so(self):
        """EC-04: constant-x lowess draws nothing, as twoway lowess does
        (``lowess, generate()`` gives all missing and the serset is empty),
        and dash says so."""
        dr, notes = self._render_noted(
            plots=[{"type": "lowess", "yvar": "mpg", "xvar": "weight", "options": {}}],
            values=self._CONST_X, varnames=["mpg", "weight"])
        assert self._drawn(dr) == [("Line", 0)]
        assert notes == ["dash: graph 'g1' plot 1 (lowess) drew nothing from "
                         "10 observations."]

    def test_ec05_constant_y_kdensity_draws_nothing_and_says_so(self):
        """EC-05: constant y (std==0) kdensity draws nothing and says so.

        twoway kdensity puts all 300 of its points at (22, 0) -- a line of
        no length and no height, so nothing shows either way.
        """
        dr, notes = self._render_noted(
            plots=[{"type": "kdensity", "yvar": "mpg", "options": {}}],
            values=[{"mpg": 22.0} for _ in range(10)],
            varnames=["mpg"],
        )
        assert self._drawn(dr) == [("Line", 0)]
        assert notes == ["dash: graph 'g1' plot 1 (kdensity) drew nothing "
                         "from 10 observations."]

    def test_ec06_missing_yvar_column_warns_no_keyerror(self):
        """EC-06: missing yvar emits warning and does not raise KeyError."""
        import warnings
        import json, tempfile, os
        vals = [{"x": float(i)} for i in range(5)]
        data = {"StataJSON": {
            "variableNames": ["x"],
            "variableLabels": {"x": "x"},
            "valueLabels": {}, "valueLabelNames": {},
            "variableTypeIsString": {"x": False},
            "values": vals,
        }}
        spec = {
            "graphs": [{"plots": [{"type": "scatter", "yvar": "nonexistent",
                                    "xvar": "x", "options": {}}],
                         "graph_options": {"name": "g1"},
                         "if_expr": "", "in_expr": ""}],
            "kpis": [],
            "build_options": {"layout": "auto", "link": "", "theme": "default",
                              "title": "", "subtitle": "", "registry": "g1"},
        }
        sp, dp, op = [tempfile.mkstemp(s)[1] for s in (".json", ".json", ".html")]
        try:
            with open(sp, "w") as f: json.dump(spec, f)
            with open(dp, "w") as f: json.dump(data, f)
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                dr = DashRenderer(sp, dp, op)
                dr.render()  # must not raise KeyError
            msgs = [str(x.message) for x in w]
            assert any("nonexistent" in m for m in msgs), (
                f"Expected warning about 'nonexistent'. Got: {msgs}"
            )
        finally:
            for p in (sp, dp, op):
                try: os.unlink(p)
                except OSError: pass
