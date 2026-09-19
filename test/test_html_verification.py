"""
test_html_verification.py
Comprehensive verification tests that parse Bokeh's embedded JSON model in
rendered HTML to:

  * Count the number of glyphs / data points produced by each plot type
  * Verify that alpha transparency options are applied correctly
  * Verify colorvar() variable-color mapping embeds a ColorMapper
  * Verify jitter columns are embedded in the JSON model
  * Verify dual-axis ranges appear in the JSON model
  * Verify scheme CSS appears in the HTML
  * Verify mcolor / fcolor hex values appear in the JSON

All assertions are made against the raw JSON structure that Bokeh serialises
into the ``<script type="application/json">`` block in the standalone HTML,
so no headless browser is required.

Run with:  pytest test/test_html_verification.py -v
"""
import sys
import os
import json
import re
import tempfile

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dash_render import DashRenderer, GlyphMapper, OptionTranslator

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource


# ============================================================
# Helpers
# ============================================================

_N = 20  # default row count for test datasets


def _make_data(cols: dict) -> dict:
    """Build a StataJSON data blob from a column dict."""
    names = list(cols.keys())
    n = len(next(iter(cols.values())))
    return {
        "StataJSON": {
            "variableNames": names,
            "variableLabels": {k: k for k in names},
            "valueLabels": {},
            "valueLabelNames": {},
            "variableTypeIsString": {k: False for k in names},
            "values": [{k: cols[k][i] for k in names} for i in range(n)],
        }
    }


def _render(plots, graph_opts=None, build_opts=None, data=None,
            if_expr="", in_expr=""):
    """Full render; returns HTML string."""
    np.random.seed(42)
    if data is None:
        data = _make_data({
            "x":   list(range(1, _N + 1)),
            "y":   np.random.uniform(10, 100, _N).tolist(),
            "y2":  np.random.uniform(1000, 9000, _N).tolist(),
            "cat": ["A" if i < _N // 2 else "B" for i in range(_N)],
            "grp": [float(i % 3) for i in range(_N)],
        })
    g_opts = dict(graph_opts or {"name": "g1"})
    gname = g_opts.get("name", "g1")
    spec = {
        "graphs": [{
            "plots": plots,
            "graph_options": g_opts,
            "if_expr": if_expr,
            "in_expr": in_expr,
        }],
        "kpis": [],
        "build_options": {
            "layout": "auto", "link": "", "filter": "",
            "theme": "default", "title": "", "subtitle": "",
            "registry": gname,
            **(build_opts or {}),
        },
    }
    sp, dp, op = [tempfile.mkstemp(s)[1] for s in (".json", ".json", ".html")]
    try:
        with open(sp, "w") as f:
            json.dump(spec, f)
        with open(dp, "w") as f:
            json.dump(data, f)
        return DashRenderer(sp, dp, op).render()
    finally:
        for p in (sp, dp, op):
            try:
                os.unlink(p)
            except OSError:
                pass


def _bokeh_model_json(html_str: str) -> dict:
    """Extract the first Bokeh application/json model block from the HTML."""
    m = re.search(
        r'<script type="application/json"[^>]*>(.*?)</script>',
        html_str, re.DOTALL
    )
    if m is None:
        raise AssertionError("No Bokeh JSON model block found in HTML")
    return json.loads(m.group(1))


def _walk_json(obj, matches=None):
    """Recursively walk a JSON structure; yield all dicts."""
    if matches is None:
        matches = []
    if isinstance(obj, dict):
        matches.append(obj)
        for v in obj.values():
            _walk_json(v, matches)
    elif isinstance(obj, list):
        for item in obj:
            _walk_json(item, matches)
    return matches


def _find_type(model_json: dict, type_str: str) -> list[dict]:
    """Return all model dicts whose 'type' or 'name' field contains *type_str*.

    Handles both Bokeh 2.x (``"type": "Scatter"``) and Bokeh 3.x
    (``"type": "object", "name": "scatter"``) serialisation formats.
    """
    needle = type_str.lower()
    result = []
    for d in _walk_json(model_json):
        type_val = d.get("type", "")
        name_val = d.get("name", "")
        if (isinstance(type_val, str) and needle in type_val.lower()) or \
           (isinstance(name_val, str) and needle in name_val.lower()):
            result.append(d)
    return result


def _cds_data_as_dict(raw_data: "dict | list") -> "dict[str, list]":
    """Normalise a Bokeh CDS ``data`` attribute to a plain column dict.

    Bokeh 3.x serialises CDS data as ``{"type": "map", "entries": [[k,v], ...]}``.
    Bokeh 2.x serialises as a plain ``{col: [values], ...}`` dict.
    Returns a ``{col_name: list_of_values}`` dict either way.
    """
    if isinstance(raw_data, dict):
        # Bokeh 3.x map format
        if raw_data.get("type") == "map" and "entries" in raw_data:
            return {str(k): v for k, v in raw_data["entries"]}
        # Bokeh 2.x plain dict format
        return raw_data
    return {}


def _count_data_points(model_json: dict, col_name: str) -> int:
    """Return the length of the first CDS column named *col_name*.

    Works with both Bokeh 2.x and Bokeh 3.x serialisation formats.
    """
    for d in _walk_json(model_json):
        combined = (d.get("type", "") + " " + d.get("name", "")).lower()
        if "columndatasource" in combined:
            raw = d.get("attributes", {}).get("data", {})
            cols = _cds_data_as_dict(raw)
            if col_name in cols:
                col = cols[col_name]
                if isinstance(col, list):
                    return len(col)
                # ndarray blob: {"__ndarray__": ..., "shape": [N], ...}
                if isinstance(col, dict) and "shape" in col:
                    shape = col["shape"]
                    return shape[0] if isinstance(shape, list) else int(shape)
    return 0


def _find_color_value(model_json: dict, hex_lower: str) -> bool:
    """Return True if *hex_lower* appears anywhere as a string value in the model."""
    raw = json.dumps(model_json).lower()
    return hex_lower.lower() in raw


def _find_alpha_value(model_json: dict, attr_name: str, approx: float,
                      tol: float = 0.02) -> bool:
    """Return True if any glyph has *attr_name* within *tol* of *approx*."""
    raw_str = json.dumps(model_json)
    raw = json.loads(raw_str)
    for d in _walk_json(raw):
        attrs = d.get("attributes", {})
        if attr_name in attrs:
            val = attrs[attr_name]
            if isinstance(val, (int, float)):
                if abs(float(val) - approx) <= tol:
                    return True
    return False


# ============================================================
# GV-01 – 06: Glyph count verification
# ============================================================

class TestGlyphCount:
    def test_scatter_data_points_match_n(self):
        """GV-01: scatter plot embeds exactly N x-values in the CDS."""
        html = _render([{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}])
        model = _bokeh_model_json(html)
        n = _count_data_points(model, "x")
        assert n == _N, f"Expected {_N} data points, got {n}"

    def test_line_data_points_match_n(self):
        """GV-02: line plot embeds exactly N x-values."""
        html = _render([{"type": "line", "yvar": "y", "xvar": "x", "options": {}}])
        model = _bokeh_model_json(html)
        n = _count_data_points(model, "x")
        assert n == _N

    def test_bar_data_points_match_n(self):
        """GV-03: bar plot embeds exactly N x-values."""
        html = _render([{"type": "bar", "yvar": "y", "xvar": "x", "options": {}}])
        model = _bokeh_model_json(html)
        n = _count_data_points(model, "x")
        assert n == _N

    def test_scatter_with_jitter_has_jit_column(self):
        """GV-04: scatter with jitter(5) embeds _x_jit column of length N."""
        html = _render([{"type": "scatter", "yvar": "y", "xvar": "x",
                         "options": {"jitter": "5", "jseed": "1"}}])
        model = _bokeh_model_json(html)
        n = _count_data_points(model, "_x_jit")
        assert n == _N, f"_x_jit column has {n} entries, expected {_N}"

    def test_scatter_no_jitter_has_no_jit_column(self):
        """GV-05: scatter without jitter does NOT embed _x_jit column."""
        html = _render([{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}])
        assert "_x_jit" not in html

    def test_jit_column_differs_from_original(self):
        """GV-06: _x_jit values differ from original x values (noise was added)."""
        html = _render([{"type": "scatter", "yvar": "y", "xvar": "x",
                         "options": {"jitter": "10", "jseed": "99"}}])
        model = _bokeh_model_json(html)
        # Retrieve both columns from any CDS that has both (Bokeh 2.x and 3.x)
        for d in _walk_json(model):
            combined = (d.get("type", "") + " " + d.get("name", "")).lower()
            if "columndatasource" in combined:
                raw = d.get("attributes", {}).get("data", {})
                cols = _cds_data_as_dict(raw)
                if "x" in cols and "_x_jit" in cols:
                    def _to_list(val):
                        if isinstance(val, list):
                            return val
                        if isinstance(val, dict) and "__ndarray__" in val:
                            import base64, struct
                            b = base64.b64decode(val["__ndarray__"])
                            dtype = val.get("dtype", "float64")
                            fmt = {"float64": "d", "float32": "f", "int32": "i",
                                   "int64": "q"}.get(dtype, "d")
                            n = len(b) // struct.calcsize(fmt)
                            return list(struct.unpack(f"{n}{fmt}", b))
                        return []
                    orig = np.array(_to_list(cols["x"]), dtype=float)
                    jit = np.array(_to_list(cols["_x_jit"]), dtype=float)
                    if len(orig) > 0 and len(jit) > 0:
                        assert not np.allclose(orig, jit), \
                            "Jittered x values identical to originals"
                        return
        pytest.fail("Could not find x and _x_jit in any CDS")


# ============================================================
# ALP-01 – 10: Alpha transparency verification
# ============================================================

class TestAlphaTransparency:
    """Verify that mcolor%alpha, malpha, fcolor%alpha, lcolor%alpha are applied."""

    # -- Unit: parse_color_alpha --

    def test_parse_color_alpha_named_with_pct(self):
        """ALP-01: 'red%50' → ('#ff0000', 0.5)."""
        color, alpha = OptionTranslator.parse_color_alpha("red%50")
        assert color == "#ff0000"
        assert alpha == pytest.approx(0.5)

    def test_parse_color_alpha_bare_pct(self):
        """ALP-02: '%30' → (None, 0.3)."""
        color, alpha = OptionTranslator.parse_color_alpha("%30")
        assert color is None
        assert alpha == pytest.approx(0.3)

    def test_parse_color_alpha_no_pct(self):
        """ALP-03: 'navy' → ('#1a476f', None)."""
        color, alpha = OptionTranslator.parse_color_alpha("navy")
        assert color is not None
        assert alpha is None

    def test_parse_color_alpha_hex_with_pct(self):
        """ALP-04: '#ff0000%75' → ('#ff0000', 0.75)."""
        color, alpha = OptionTranslator.parse_color_alpha("#ff0000%75")
        assert color == "#ff0000"
        assert alpha == pytest.approx(0.75)

    def test_parse_color_alpha_zero(self):
        """ALP-05: 'blue%0' → alpha==0.0 (fully transparent)."""
        _, alpha = OptionTranslator.parse_color_alpha("blue%0")
        assert alpha == pytest.approx(0.0)

    def test_parse_color_alpha_100(self):
        """ALP-06: 'blue%100' → alpha==1.0 (fully opaque)."""
        _, alpha = OptionTranslator.parse_color_alpha("blue%100")
        assert alpha == pytest.approx(1.0)

    def test_translate_mcolor_strips_alpha(self):
        """ALP-07: translate_mcolor('red%50') returns the color hex, not an error."""
        color = OptionTranslator.translate_mcolor("red%50")
        assert color == "#ff0000"

    # -- Integration: mcolor%alpha applied to scatter --

    def test_mcolor_alpha_sets_fill_alpha(self):
        """ALP-08: mcolor(navy%60) → fill_alpha≈0.6 on scatter glyph."""
        fig = figure()
        src = ColumnDataSource({"x": [1.0, 2.0, 3.0], "y": [1.0, 2.0, 3.0]})
        gm = GlyphMapper()
        r = gm.map_scatter(fig, src, "y", "x", {"mcolor": "navy%60"})
        assert abs(r.glyph.fill_alpha - 0.6) < 0.02

    def test_malpha_sets_fill_and_line_alpha(self):
        """ALP-09: malpha(40) → fill_alpha≈0.4 and line_alpha≈0.4."""
        fig = figure()
        src = ColumnDataSource({"x": [1.0, 2.0, 3.0], "y": [1.0, 2.0, 3.0]})
        gm = GlyphMapper()
        r = gm.map_scatter(fig, src, "y", "x", {"malpha": "40"})
        assert abs(r.glyph.fill_alpha - 0.4) < 0.02
        assert abs(r.glyph.line_alpha - 0.4) < 0.02

    def test_mcolor_alpha_in_html(self):
        """ALP-10: full render with mcolor(navy%50) → fill_alpha≈0.5 in JSON model."""
        html = _render([{"type": "scatter", "yvar": "y", "xvar": "x",
                         "options": {"mcolor": "navy%50"}}])
        model = _bokeh_model_json(html)
        found = _find_alpha_value(model, "fill_alpha", 0.5)
        assert found, "fill_alpha≈0.5 not found in Bokeh JSON model"

    def test_fcolor_alpha_applied_to_bar(self):
        """ALP-11: fcolor(red%70) → fill_alpha≈0.7 on bar glyph."""
        fig = figure()
        src = ColumnDataSource({"x": [1.0, 2.0, 3.0], "y": [10.0, 20.0, 30.0]})
        gm = GlyphMapper()
        rs = gm.map_bar(fig, src, "y", "x", {"fcolor": "red%70"})
        renderer = rs[0] if isinstance(rs, list) else rs
        assert abs(renderer.glyph.fill_alpha - 0.7) < 0.02

    def test_lcolor_alpha_applied_to_line(self):
        """ALP-12: lcolor(black%30) → line_alpha≈0.3 on line glyph."""
        fig = figure()
        src = ColumnDataSource({"x": [1.0, 2.0, 3.0], "y": [1.0, 2.0, 3.0]})
        gm = GlyphMapper()
        r = gm.map_line(fig, src, "y", "x", {"lcolor": "black%30"})
        assert abs(r.glyph.line_alpha - 0.3) < 0.02

    def test_malpha_overrides_mcolor_alpha(self):
        """ALP-13: malpha(20) overrides alpha set by mcolor%alpha."""
        fig = figure()
        src = ColumnDataSource({"x": [1.0, 2.0, 3.0], "y": [1.0, 2.0, 3.0]})
        gm = GlyphMapper()
        # mcolor sets alpha=0.9, then malpha overrides to 0.2
        r = gm.map_scatter(fig, src, "y", "x",
                           {"mcolor": "navy%90", "malpha": "20"})
        assert abs(r.glyph.fill_alpha - 0.2) < 0.02

    def test_lalpha_sets_line_alpha_only(self):
        """ALP-14: lalpha(10) sets line_alpha without changing fill_alpha."""
        fig = figure()
        src = ColumnDataSource({"x": [1.0, 2.0, 3.0], "y": [1.0, 2.0, 3.0]})
        gm = GlyphMapper()
        r = gm.map_scatter(fig, src, "y", "x", {"lalpha": "10"})
        assert abs(r.glyph.line_alpha - 0.1) < 0.02
        # fill_alpha should be the default (≈0.7, set by alpha=0.7 in map_scatter)
        assert r.glyph.fill_alpha > 0.5, \
            "fill_alpha should be near default, not affected by lalpha"

    def test_invalid_alpha_value_ignored(self):
        """ALP-15: malpha with non-numeric value does not crash."""
        fig = figure()
        src = ColumnDataSource({"x": [1.0], "y": [1.0]})
        gm = GlyphMapper()
        r = gm.map_scatter(fig, src, "y", "x", {"malpha": "not_a_number"})
        assert r is not None  # no crash

    def test_alpha_out_of_range_ignored(self):
        """ALP-16: malpha(200) (>100%) is ignored (not applied)."""
        fig = figure()
        src = ColumnDataSource({"x": [1.0], "y": [1.0]})
        gm = GlyphMapper()
        # Default fill_alpha after map_scatter is 0.7; if malpha=200 were applied
        # it would be 2.0 which Bokeh would clamp/reject. Since we validate range,
        # it should stay at the default ≈0.7.
        r = gm.map_scatter(fig, src, "y", "x", {"malpha": "200"})
        assert r.glyph.fill_alpha <= 1.0


# ============================================================
# CV-01 – 08: colorvar() variable color mapping
# ============================================================

class TestColorvar:
    def _src(self, n=10):
        np.random.seed(0)
        return ColumnDataSource({
            "x":   list(range(1, n + 1)),
            "y":   np.random.uniform(0, 100, n).tolist(),
            "grp": [float(i % 3) for i in range(n)],
            "cat": ["A" if i < n // 2 else "B" for i in range(n)],
        })

    def test_colorvar_linear_mapper_added(self):
        """CV-01: colorvar(grp) on numeric variable creates a LinearColorMapper."""
        from bokeh.models import LinearColorMapper, ColorBar
        fig = figure()
        src = self._src()
        gm = GlyphMapper()
        gm.map_scatter(fig, src, "y", "x", {"colorvar": "grp"})
        # A ColorBar backed by a LinearColorMapper must be on the right
        right_bars = [r for r in fig.right if isinstance(r, ColorBar)]
        assert len(right_bars) == 1
        assert isinstance(right_bars[0].color_mapper, LinearColorMapper)

    def test_colorvar_colorbar_added_to_figure(self):
        """CV-02: colorvar adds a ColorBar on the right of the figure."""
        from bokeh.models import ColorBar
        fig = figure()
        src = self._src()
        gm = GlyphMapper()
        gm.map_scatter(fig, src, "y", "x", {"colorvar": "grp"})
        right_bars = [r for r in fig.right if isinstance(r, ColorBar)]
        assert len(right_bars) == 1

    def test_colorvar_categorical_mapper(self):
        """CV-03: colorvar(cat) on string variable creates CategoricalColorMapper.

        Discrete colorvar mappings now render a Bokeh Legend (not a ColorBar)
        by default — matches Stata 18 colordiscrete behavior and the user
        expectation of one labeled legend entry per category.
        """
        from bokeh.models import CategoricalColorMapper, Legend
        fig = figure()
        src = self._src()
        gm = GlyphMapper()
        r = gm.map_scatter(fig, src, "y", "x", {"colorvar": "cat"})
        mapper = r.glyph.fill_color["transform"]
        assert isinstance(mapper, CategoricalColorMapper)
        # Discrete data → Legend on the right (no ColorBar)
        legends = [lay for lay in fig.right if isinstance(lay, Legend)]
        assert len(legends) == 1

    def test_colorvar_categorical_has_both_factors(self):
        """CV-04: CategoricalColorMapper for 'cat' has factors ['A', 'B']."""
        from bokeh.models import CategoricalColorMapper
        fig = figure()
        src = self._src()
        gm = GlyphMapper()
        r = gm.map_scatter(fig, src, "y", "x", {"colorvar": "cat"})
        mapper = r.glyph.fill_color["transform"]
        assert isinstance(mapper, CategoricalColorMapper)
        assert set(mapper.factors) == {"A", "B"}

    def test_colorvar_nonexistent_column_ignored(self):
        """CV-05: colorvar pointing to a missing column is silently ignored."""
        fig = figure()
        src = self._src()
        gm = GlyphMapper()
        gm.map_scatter(fig, src, "y", "x", {"colorvar": "nonexistent"})
        # No ColorBar should be added when column is missing
        from bokeh.models import ColorBar
        assert len([r for r in fig.right if isinstance(r, ColorBar)]) == 0

    def test_colorvar_injection_attempt_ignored(self):
        """CV-06: colorvar value with injection chars is ignored."""
        fig = figure()
        src = self._src()
        gm = GlyphMapper()
        gm.map_scatter(fig, src, "y", "x",
                       {"colorvar": "__import__('os')"})
        from bokeh.models import ColorBar
        assert len([r for r in fig.right if isinstance(r, ColorBar)]) == 0

    def test_colorvar_html_contains_linearcolormapper(self):
        """CV-07: full render with colorvar(grp) embeds LinearColorMapper in JSON."""
        html = _render([{"type": "scatter", "yvar": "y", "xvar": "x",
                         "options": {"colorvar": "grp"}}])
        # Bokeh 3.x uses lowercase "name" in JSON, 2.x uses PascalCase "type"
        assert "linearcolormapper" in html.lower() or "LinearColorMapper" in html

    def test_colorvar_html_contains_colorbar(self):
        """CV-08: full render with colorvar(grp) embeds ColorBar in JSON."""
        html = _render([{"type": "scatter", "yvar": "y", "xvar": "x",
                         "options": {"colorvar": "grp"}}])
        assert "colorbar" in html.lower() or "ColorBar" in html

    def test_colorvar_palette_viridis_default(self):
        """CV-09: LinearColorMapper uses Viridis palette by default."""
        from bokeh.models import LinearColorMapper
        from bokeh import palettes
        fig = figure()
        src = self._src()
        gm = GlyphMapper()
        gm.map_scatter(fig, src, "y", "x", {"colorvar": "grp"})
        bar = fig.right[0]
        mapper = bar.color_mapper
        assert isinstance(mapper, LinearColorMapper)
        # Viridis256 starts with a dark purple (#440154)
        assert "#440154" in list(mapper.palette)[:10]

    def test_colorvar_palette_magma_option(self):
        """CV-10: colpalette(magma) selects Magma256 palette."""
        from bokeh.models import LinearColorMapper
        from bokeh import palettes
        fig = figure()
        src = self._src()
        gm = GlyphMapper()
        gm.map_scatter(fig, src, "y", "x",
                       {"colorvar": "grp", "colpalette": "magma"})
        bar = fig.right[0]
        mapper = bar.color_mapper
        # Magma256[0] is a dark color different from Viridis256[0]
        assert list(mapper.palette)[0] != list(palettes.Viridis256)[0]


# ============================================================
# DAX-V: Dual-axis JSON verification
# ============================================================

class TestDualAxisJsonVerification:
    def test_extra_y_range_in_html(self):
        """DAX-V1: yaxis(2) → extra_y_ranges entry appears in Bokeh JSON."""
        html = _render([
            {"type": "scatter", "yvar": "y", "xvar": "x", "options": {}},
            {"type": "line", "yvar": "y2", "xvar": "x", "options": {"yaxis": "2"}},
        ])
        assert "extra_y_ranges" in html or "Range1d" in html

    def test_secondary_y_renderer_count(self):
        """DAX-V2: figure with primary + secondary scatter → at least 2 Scatter models."""
        html = _render([
            {"type": "scatter", "yvar": "y", "xvar": "x", "options": {}},
            {"type": "scatter", "yvar": "y2", "xvar": "x",
             "options": {"yaxis": "2"}},
        ])
        model = _bokeh_model_json(html)
        scatters = _find_type(model, "Scatter")
        assert len(scatters) >= 2, f"Expected ≥2 Scatter models, found {len(scatters)}"

    def test_linear_axis_on_right(self):
        """DAX-V3: yaxis(2) → a LinearAxis model exists in the JSON."""
        html = _render([
            {"type": "line", "yvar": "y2", "xvar": "x",
             "options": {"yaxis": "2"}},
        ])
        assert "LinearAxis" in html


# ============================================================
# SCH-V: Scheme CSS verification
# ============================================================

class TestSchemeHtmlVerification:
    def test_s2color_css_in_html(self):
        """SCH-V1: s2color scheme injects a <style> block into output HTML."""
        html = _render(
            [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}],
            build_opts={"scheme": "s2color"},
        )
        assert "<style>" in html

    def test_sj_css_differs_from_s2color(self):
        """SCH-V2: sj and s2color produce different CSS blocks."""
        html_s2 = _render(
            [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}],
            build_opts={"scheme": "s2color"},
        )
        html_sj = _render(
            [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}],
            build_opts={"scheme": "sj"},
        )
        # Extract just the style blocks and compare
        def _styles(h):
            return re.findall(r"<style>(.*?)</style>", h, re.DOTALL)
        assert _styles(html_s2) != _styles(html_sj)

    def test_s2color_background_white_in_json(self):
        """SCH-V3: s2color sets white background → 'white' or '#ffffff' in JSON."""
        html = _render(
            [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}],
            build_opts={"scheme": "s2color"},
        )
        model = _bokeh_model_json(html)
        raw = json.dumps(model).lower()
        assert "#ffffff" in raw or "white" in raw


# ============================================================
# COLOR-V: Color hex values in JSON model
# ============================================================

class TestColorHexInJson:
    def test_mcolor_navy_hex_in_scatter_json(self):
        """COL-V1: mcolor(navy) → navy hex #1a476f in Bokeh JSON."""
        html = _render([{"type": "scatter", "yvar": "y", "xvar": "x",
                         "options": {"mcolor": "navy"}}])
        model = _bokeh_model_json(html)
        found = _find_color_value(model, "#1a476f")
        assert found, "#1a476f (navy) not in Bokeh JSON model"

    def test_lcolor_red_hex_in_line_json(self):
        """COL-V2: lcolor(red) → red hex in Bokeh JSON."""
        html = _render([{"type": "line", "yvar": "y", "xvar": "x",
                         "options": {"lcolor": "red"}}])
        model = _bokeh_model_json(html)
        # 'red' maps to #ff0000
        raw = json.dumps(model).lower()
        assert "#ff0000" in raw or '"red"' in raw

    def test_fcolor_in_bar_json(self):
        """COL-V3: fcolor(cranberry) → Stata's #c10534 in bar JSON.

        This asserted #a00000, which is not Stata's cranberry.  Its own
        style/color-cranberry.style sets rgb "193 5 52" = #c10534.  See
        test_color_fidelity.py for the other 51.
        """
        html = _render([{"type": "bar", "yvar": "y", "xvar": "x",
                         "options": {"fcolor": "cranberry"}}])
        model = _bokeh_model_json(html)
        raw = json.dumps(model).lower()
        assert "#c10534" in raw  # Stata cranberry

    def test_mcolor_alpha_hex_still_present(self):
        """COL-V4: mcolor(navy%50) → navy hex in JSON (alpha separate from color)."""
        html = _render([{"type": "scatter", "yvar": "y", "xvar": "x",
                         "options": {"mcolor": "navy%50"}}])
        model = _bokeh_model_json(html)
        raw = json.dumps(model).lower()
        assert "#1a476f" in raw

    def test_n_rows_match_filter(self):
        """COL-V5: in_expr='1/10' filter → exactly 10 data points in CDS."""
        html = _render(
            [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}],
            in_expr="1/10",
        )
        model = _bokeh_model_json(html)
        n = _count_data_points(model, "x")
        assert n == 10, f"Expected 10 data points after in(1/10), got {n}"
