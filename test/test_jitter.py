"""
test_jitter.py
Unit and integration tests for jitter() and jseed() options.

Run with:  pytest test/test_jitter.py -v
"""
import sys
import os
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dash_render import GlyphMapper, OptionTranslator, DashRenderer

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def auto_df():
    np.random.seed(42)
    n = 30
    return pd.DataFrame({
        "mpg":    np.random.randint(12, 40, n).astype(float),
        "weight": np.random.randint(1760, 4840, n).astype(float),
        "price":  np.random.randint(3291, 15906, n).astype(float),
        "make":   [f"car{i}" for i in range(n)],
    })


@pytest.fixture
def gm():
    return GlyphMapper()


def _make_source(df, xcol, ycol):
    return ColumnDataSource({xcol: df[xcol].tolist(), ycol: df[ycol].tolist()})


# ============================================================
# JIT-01 through JIT-06  map_scatter with jitter
# ============================================================

class TestMapScatterJitter:
    def test_jitter_uses_jit_columns_as_xy(self, auto_df, gm):
        """JIT-01: renderer x/y fields reference jittered columns when jitter is set."""
        fig = figure()
        src = _make_source(auto_df, "weight", "mpg")
        r = gm.map_scatter(fig, src, "mpg", "weight", {"jitter": "5", "jseed": "42"})
        assert r.glyph.x == "_x_jit"
        assert r.glyph.y == "_y_jit"

    def test_no_jitter_uses_original_columns(self, auto_df, gm):
        """JIT-02: renderer x/y use original column names when jitter absent."""
        fig = figure()
        src = _make_source(auto_df, "weight", "mpg")
        r = gm.map_scatter(fig, src, "mpg", "weight", {})
        assert r.glyph.x == "weight"
        assert r.glyph.y == "mpg"

    def test_jitter_cds_retains_original_columns(self, auto_df, gm):
        """JIT-03: original variable columns present in jittered CDS for hover."""
        fig = figure()
        src = _make_source(auto_df, "weight", "mpg")
        r = gm.map_scatter(fig, src, "mpg", "weight", {"jitter": "5", "jseed": "0"})
        cds_data = r.data_source.data
        assert "weight" in cds_data
        assert "mpg" in cds_data
        assert "_x_jit" in cds_data
        assert "_y_jit" in cds_data

    def test_deterministic_with_jseed(self, auto_df, gm):
        """JIT-04: two renders with same jseed produce identical jitter arrays."""
        fig1, fig2 = figure(), figure()
        src1 = _make_source(auto_df, "weight", "mpg")
        src2 = _make_source(auto_df, "weight", "mpg")
        r1 = gm.map_scatter(fig1, src1, "mpg", "weight", {"jitter": "5", "jseed": "42"})
        r2 = gm.map_scatter(fig2, src2, "mpg", "weight", {"jitter": "5", "jseed": "42"})
        np.testing.assert_array_equal(
            r1.data_source.data["_x_jit"],
            r2.data_source.data["_x_jit"],
        )

    def test_different_jseed_produces_different_jitter(self, auto_df, gm):
        """JIT-05: different jseed values produce different jitter."""
        fig1, fig2 = figure(), figure()
        src1 = _make_source(auto_df, "weight", "mpg")
        src2 = _make_source(auto_df, "weight", "mpg")
        r1 = gm.map_scatter(fig1, src1, "mpg", "weight", {"jitter": "5", "jseed": "1"})
        r2 = gm.map_scatter(fig2, src2, "mpg", "weight", {"jitter": "5", "jseed": "999"})
        assert not np.allclose(
            r1.data_source.data["_x_jit"],
            r2.data_source.data["_x_jit"],
        )

    def test_jitter_zero_no_jit_columns(self, auto_df, gm):
        """jitter(0) should not add jit columns (treated as no jitter)."""
        fig = figure()
        src = _make_source(auto_df, "weight", "mpg")
        r = gm.map_scatter(fig, src, "mpg", "weight", {"jitter": "0"})
        assert r.glyph.x == "weight"
        assert r.glyph.y == "mpg"

    def test_nonnumeric_jitter_ignored(self, auto_df, gm):
        """jitter with non-numeric value is silently ignored."""
        fig = figure()
        src = _make_source(auto_df, "weight", "mpg")
        r = gm.map_scatter(fig, src, "mpg", "weight", {"jitter": "abc"})
        assert r.glyph.x == "weight"
        assert r.glyph.y == "mpg"

    def test_injection_attempt_in_jitter_ignored(self, auto_df, gm):
        """jitter with injection attempt value is silently ignored."""
        fig = figure()
        src = _make_source(auto_df, "weight", "mpg")
        r = gm.map_scatter(fig, src, "mpg", "weight",
                           {"jitter": "5); import os"})
        # float() will raise ValueError → treated as 0 → no jitter
        assert r.glyph.x == "weight"

    def test_extreme_jitter_value_no_crash(self, auto_df, gm):
        """jitter(999999) is clamped to 100, no crash."""
        fig = figure()
        src = _make_source(auto_df, "weight", "mpg")
        r = gm.map_scatter(fig, src, "mpg", "weight", {"jitter": "999999"})
        assert "_x_jit" in r.data_source.data


# ============================================================
# JIT-06 through JIT-08  other plot types
# ============================================================

class TestJitterOnOtherPlots:
    def test_jitter_on_dot_plot(self, auto_df, gm):
        """JIT-06: jitter option works on map_dot (delegates to map_scatter)."""
        fig = figure()
        src = _make_source(auto_df, "weight", "mpg")
        r = gm.map_dot(fig, src, "mpg", "weight", {"jitter": "5", "jseed": "0"})
        # map_dot returns a list with one renderer
        renderer = r if hasattr(r, "glyph") else r[0]
        assert renderer.glyph.x == "_x_jit"

    def test_jitter_on_dropline(self, auto_df, gm):
        """JIT-07: jitter option on dropline adds offset columns to CDS."""
        fig = figure()
        src = _make_source(auto_df, "weight", "mpg")
        renderers = gm.map_dropline(fig, src, "mpg", "weight",
                                    {"jitter": "5", "jseed": "0"})
        # The dot renderer's source should have jittered "x" column != original
        dot = renderers[1]
        xs = np.array(dot.data_source.data["x"])
        orig = np.array(dot.data_source.data["weight"])
        # At least some values should differ
        assert not np.allclose(xs, orig)

    def test_jitter_on_scatteri(self, gm):
        """JIT-08: jitter option on scatteri produces jittered literal coords."""
        fig = figure()
        values = [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]
        r_no_jit = gm.map_scatteri(figure(), values, {})[0]
        r_jit = gm.map_scatteri(fig, values, {"jitter": "20", "jseed": "7"})[0]
        xs_orig = np.array(r_no_jit.data_source.data["x"])
        xs_jit  = np.array(r_jit.data_source.data["x"])
        assert not np.allclose(xs_orig, xs_jit)


# ============================================================
# JIT-09  Line plot ignores jitter
# ============================================================

class TestJitterNotOnLinePlot:
    def test_line_plot_ignores_jitter(self, auto_df, gm):
        """JIT-09: map_line silently ignores jitter option."""
        fig = figure()
        src = _make_source(auto_df, "weight", "mpg")
        r = gm.map_line(fig, src, "mpg", "weight", {"jitter": "5"})
        assert r.glyph.x == "weight"
        assert r.glyph.y == "mpg"
        assert "_x_jit" not in r.data_source.data


# ============================================================
# JIT-10  HTML integration test
# ============================================================

class TestJitterHtmlIntegration:
    def _render(self, options):
        import json as _json
        import tempfile
        data = {
            "mpg":    [20.0, 25.0, 30.0, 22.0, 28.0],
            "weight": [2000.0, 3000.0, 2500.0, 2800.0, 3200.0],
        }
        n = 5
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
                "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                           "options": options}],
                "graph_options": {"name": "fig1"},
                "if_expr": "", "in_expr": "",
            }],
            "kpis": [],
            "build_options": {
                "layout": "auto", "link": "", "filter": "",
                "theme": "default", "title": "", "subtitle": "", "registry": "fig1",
            },
        }
        sp, dp, op = [tempfile.mkstemp(s)[1] for s in (".json", ".json", ".html")]
        try:
            with open(sp, "w") as f: _json.dump(spec, f)
            with open(dp, "w") as f: _json.dump(data_json, f)
            from dash_render import DashRenderer as DR
            return DR(sp, dp, op).render()
        finally:
            for p in (sp, dp, op):
                try: os.unlink(p)
                except OSError: pass

    def test_html_contains_jit_column(self):
        """JIT-I1: full render with jitter(5) embeds _x_jit column in Bokeh JSON."""
        html_str = self._render({"jitter": "5", "jseed": "42"})
        assert "_x_jit" in html_str

    def test_html_no_jit_column_without_jitter(self):
        """No jitter → no _x_jit column in output."""
        html_str = self._render({})
        assert "_x_jit" not in html_str
