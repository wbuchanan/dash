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
from html import unescape as _html_unescape

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import dash_render as dr
from dash_render import DashRenderer, GlyphMapper, OptionTranslator

from bokeh.document import Document
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, GlyphRenderer
from conftest import drawn_renderers, drawn_page_models  # noqa: E402


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


def _page_document(html_str: str) -> Document:
    """The page's one embedded Bokeh document, read back as models.

    A needle searched in the page text cannot fail here: the saved page
    inlines BokehJS, and a page with no colorvar() and no yaxis(2) holds
    "LinearColorMapper" 7 times, "ColorBar" 22, "extra_y_ranges" 9,
    "Range1d" 47 and "LinearAxis" 14 (measured 24sep2026).  The models
    the page embeds are what it draws.  Bokeh HTML-escapes the block, so
    it is unescaped before it is read, as test_layout_tabs.py does.
    """
    blocks = re.findall(r'<script type="application/json" id="[^"]+">'
                        r'\s*(.*?)\s*</script>', html_str, re.DOTALL)
    docs = [d for b in blocks for d in json.loads(_html_unescape(b)).values()]
    assert len(docs) == 1, f"{len(docs)} embedded Bokeh documents, not 1"
    return Document.from_json(docs[0])


def _page_figure(html_str: str):
    """The one figure the page's document holds (its .document is the doc)."""
    figs = [m for m in _page_document(html_str).models
            if type(m).__name__ == "figure"]
    assert len(figs) == 1, f"{len(figs)} figures in the page, not 1"
    return figs[0]


def _layers(fig) -> list:
    """The figure's drawn layers, its GlyphRenderers, in drawing order.

    Not a count of glyph models: each fig.scatter() writes three Scatter
    models (its glyph, nonselection and muted glyphs), so one scatter
    layer is three "Scatter" objects in the JSON (measured 24sep2026).
    """
    # WP-42 CV-7: legend-only proxies draw nothing
    return [r for r in drawn_renderers(fig) if isinstance(r, GlyphRenderer)]


def _spec_value(v):
    """A decoded glyph property's plain value.

    Bokeh 3.9 writes a glyph's fixed colour or alpha as {"type": "value",
    "value": ...}, which reads back as a Value; an overlay's alpha is a
    plain number, and a mapped colour is a Field, returned as it is.
    """
    if isinstance(v, dict):
        return v.get("value")
    return getattr(v, "value", v)


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
    """Return True if any glyph has *attr_name* within *tol* of *approx*.

    A glyph is what a GlyphRenderer draws.  This read the plain numbers of
    every model in the JSON and never saw one: Bokeh 3.9 writes a glyph's
    alpha as {"type": "value", "value": 0.5}.  What it found was the 0.5
    fill_alpha of the box-zoom and box-select BoxAnnotations and the
    lasso's PolyAnnotation, which every page carries, so a page with no
    alpha option at all passed ALP-10 (measured 24sep2026).  It now reads
    the document back and looks at the renderers' glyphs only -- not
    their nonselection or muted glyphs, whose alphas are 0.1 and 0.2.
    """
    for doc_json in model_json.values():
        for r in Document.from_json(doc_json).models:
            glyph = getattr(r, "glyph", None) \
                if isinstance(r, GlyphRenderer) else None
            if glyph is None or attr_name not in glyph.properties():
                continue
            val = _spec_value(getattr(glyph, attr_name))
            if isinstance(val, (int, float)) and not isinstance(val, bool) \
                    and abs(float(val) - approx) <= tol:
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
        """GV-04: scatter with jitter(5) embeds the __dash_xjit column of
        length N (G1, WP-28: named under the __dash prefix)."""
        html = _render([{"type": "scatter", "yvar": "y", "xvar": "x",
                         "options": {"jitter": "5", "jseed": "1"}}])
        model = _bokeh_model_json(html)
        n = _count_data_points(model, dr._DASH_JITTER_X)
        assert n == _N, f"{dr._DASH_JITTER_X} column has {n} entries, expected {_N}"

    def test_scatter_no_jitter_has_no_jit_column(self):
        """GV-05: scatter without jitter does NOT embed the jitter column."""
        html = _render([{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}])
        assert dr._DASH_JITTER_X not in html

    def test_jit_column_differs_from_original(self):
        """GV-06: the jitter column's values differ from the original x
        values (noise was added)."""
        html = _render([{"type": "scatter", "yvar": "y", "xvar": "x",
                         "options": {"jitter": "10", "jseed": "99"}}])
        model = _bokeh_model_json(html)
        # Retrieve both columns from any CDS that has both (Bokeh 2.x and 3.x)
        for d in _walk_json(model):
            combined = (d.get("type", "") + " " + d.get("name", "")).lower()
            if "columndatasource" in combined:
                raw = d.get("attributes", {}).get("data", {})
                cols = _cds_data_as_dict(raw)
                if "x" in cols and dr._DASH_JITTER_X in cols:
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
                    jit = np.array(_to_list(cols[dr._DASH_JITTER_X]), dtype=float)
                    if len(orig) > 0 and len(jit) > 0:
                        assert not np.allclose(orig, jit), \
                            "Jittered x values identical to originals"
                        return
        pytest.fail(f"Could not find x and {dr._DASH_JITTER_X} in any CDS")


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
        # The pair the docstring names -- `color is not None' held for any
        # colour at all.  #1a476f is Stata's color-navy.style.
        assert (color, alpha) == ("#1a476f", None)

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
        # The same page without the %50 draws the scheme's own 0.8, and the
        # helper must not find 0.5 there.  It did (the overlays' 0.5) until
        # it read the glyphs alone, 24sep2026.
        ctl = _bokeh_model_json(_render([{"type": "scatter", "yvar": "y",
                                          "xvar": "x",
                                          "options": {"mcolor": "navy"}}]))
        assert not _find_alpha_value(ctl, "fill_alpha", 0.5), \
            "fill_alpha 0.5 found in a page drawn without %50"

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
        """ALP-14: lalpha(10) sets a LINE's alpha, and leaves the markers.

        lalpha() is dash's own "opacity of the lines" (dash.sthlp); it was
        read onto a scatter marker's outline here, as lcolor() and lwidth()
        were, where twoway's line options never reach a marker (measured
        23sep2026; test_marker_label_parity.py).
        """
        fig = figure()
        src = ColumnDataSource({"x": [1.0, 2.0, 3.0], "y": [1.0, 2.0, 3.0]})
        gm = GlyphMapper()
        line = gm.map_line(fig, src, "y", "x", {"lalpha": "10"})
        assert abs(line.glyph.line_alpha - 0.1) < 0.02
        base = gm.map_scatter(figure(), src, "y", "x", {})
        r = gm.map_scatter(fig, src, "y", "x", {"lalpha": "10"})
        assert r.glyph.line_alpha == base.glyph.line_alpha
        assert r.glyph.fill_alpha == base.glyph.fill_alpha

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
        # Drawn under sttrans, whose declared opacity is 0.2: markers are
        # opaque by default since WP-30 P1.2b (twoway draws them so), and a
        # default of 1.0 would hide a clamp to 1.0.
        from dash_render import SchemeParser
        gm = GlyphMapper(scheme=SchemeParser("sttrans"))
        # Ignored means the scheme's default stays, on the fill and the
        # outline alike.  `<= 1.0' alone let an out-of-range malpha be
        # applied in any in-range form: clamped to 1.0 (fully opaque) it
        # passed.  Bokeh 3.9 neither clamps nor rejects an alpha of 2.0,
        # so the ceiling does catch the raw 2.0 and is kept.
        base = gm.map_scatter(figure(), src, "y", "x", {})
        r = gm.map_scatter(fig, src, "y", "x", {"malpha": "200"})
        assert r.glyph.fill_alpha <= 1.0
        # A default of 1.0 would hide a clamp from the checks below.
        assert base.glyph.fill_alpha < 1.0 and base.glyph.line_alpha < 1.0
        assert r.glyph.fill_alpha == base.glyph.fill_alpha
        assert r.glyph.line_alpha == base.glyph.line_alpha


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
        r = gm.map_scatter(fig, src, "y", "x", {"colorvar": "grp"})
        # Flipped (WP-42 CV-3): a ColorBar on the right was the key; twoway
        # draws swatches beside a z axis, a key cell, and the layer's own
        # mapper is the LinearColorMapper.
        assert fig._dash_key_cell is not None
        assert not [m for m in fig.right if isinstance(m, ColorBar)]
        assert isinstance(r.glyph.fill_color["transform"], LinearColorMapper)

    def test_colorvar_colorbar_added_to_figure(self):
        """CV-02: colorvar adds a ColorBar on the right of the figure."""
        from bokeh.models import ColorBar
        fig = figure()
        src = self._src()
        gm = GlyphMapper()
        gm.map_scatter(fig, src, "y", "x", {"colorvar": "grp"})
        # Flipped (WP-42 CV-3): the key is a key cell beside the figure, on
        # its right, not a ColorBar on it.
        assert fig._dash_key_cell is not None
        assert fig._dash_key_cell._dash_key_side == "right"
        assert not [m for m in fig.right if isinstance(m, ColorBar)]

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
        # Flipped (WP-42 CV-3): a Legend on the right; a key cell labelling
        # each value on its z axis.
        assert not [lay for lay in fig.right if isinstance(lay, Legend)]
        ovr = fig._dash_key_cell._dash_key_axis.major_label_overrides
        assert sorted(ovr.values()) == ["A", "B"]

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
        from bokeh.models import LinearColorMapper
        html = _render([{"type": "scatter", "yvar": "y", "xvar": "x",
                         "options": {"colorvar": "grp"}}])
        # Read from the page's document.  The text search this was
        # ("linearcolormapper" in the page, any case) could not fail: the
        # inlined BokehJS holds the name 7 times in a page with no
        # colorvar() (measured 24sep2026).  One mapper, spanning grp's own
        # range, 0 to 2, and colouring the layer, fill and outline, by grp
        # -- not merely present.
        fig = _page_figure(html)
        mappers = [m for m in fig.document.models
                   if isinstance(m, LinearColorMapper)]
        # Flipped (WP-42 CV-8): the continuous key was a 256-step gradient; twoway bins at its z ticks (CV-8); two mappers, the layer's levels and
        # the key's bar, each holding grp's range 0 to 2.
        # Flipped (WP-42 CV-3): the key is a key cell of swatches, no bar,
        # so one mapper, the layer's levels.
        assert len(mappers) == 1, f"{len(mappers)} LinearColorMappers"
        assert all(m.low <= 0.0 and m.high >= 2.0 for m in mappers)
        layers = _layers(fig)
        assert len(layers) == 1, f"{len(layers)} layers, not 1"
        ids = set()
        for prop in ("fill_color", "line_color"):
            spec = getattr(layers[0].glyph, prop)
            assert getattr(spec, "field", None) == "grp", (prop, spec)
            ids.add(getattr(spec.transform, "id", None))
        assert len(ids) == 1 and ids <= {m.id for m in mappers}


    def test_colorvar_html_contains_colorbar(self):
        """CV-08: full render with colorvar(grp) embeds ColorBar in JSON."""
        from bokeh.models import ColorBar
        html = _render([{"type": "scatter", "yvar": "y", "xvar": "x",
                         "options": {"colorvar": "grp"}}])
        # Read from the page's document: "ColorBar" is in the inlined
        # BokehJS 22 times in a page with no colorvar() (measured
        # 24sep2026).  One bar, on the right, keyed to the layer's mapper.
        fig = _page_figure(html)
        # Flipped (WP-42 CV-3): one ColorBar on the right was the key;
        # twoway draws swatches beside a z axis, a key cell in the page,
        # its swatches the layer's level colours.
        assert not [m for m in fig.document.models if isinstance(m, ColorBar)]
        cells = [m for m in fig.document.models
                 if "dash_key_cell" in (getattr(m, "tags", None) or [])]
        assert len(cells) == 1, f"{len(cells)} key cells"
        mapped = _layers(fig)[0].glyph.fill_color
        tr = getattr(mapped, "transform", None)
        [sw] = [r for r in drawn_renderers(cells[0])
                if "c" in getattr(r.data_source, "data", {})]
        cols = list(sw.data_source.data["c"])
        assert cols and cols == list(tr.palette)[:len(cols)]


    def test_colorvar_palette_viridis_default(self):
        """CV-09: LinearColorMapper uses twoway's hue rule by default."""
        from bokeh.models import LinearColorMapper
        from bokeh import palettes
        fig = figure()
        src = self._src()
        gm = GlyphMapper()
        r = gm.map_scatter(fig, src, "y", "x", {"colorvar": "grp"})
        # Flipped (WP-42 CV-3): the key's ColorBar mapper; the layer's own
        # mapper, its cuts the key cell's ticks.
        kc = fig._dash_key_cell._dash_keycell
        mapper = r.glyph.fill_color["transform"]
        assert isinstance(mapper, LinearColorMapper)
        # Flipped (WP-31 C8b): Viridis256 by default was wrong because
        # twoway draws the key in its colour rule, hue from blue to red
        # (colorvar_options_truth.json D01).
        pal = list(mapper.palette)
        # Flipped (WP-42 CV-8): the continuous key was a 256-step gradient; twoway bins at its z ticks (CV-8); one step of the rule a level.
        cuts = [t for t in kc["ticker"].ticks if t >= min(src.data["grp"])]
        assert len(pal) == len(cuts) + 1
        assert pal[0] == "#0000ff" and pal[-1] == "#ff0000"

    def test_colorvar_palette_magma_option(self):
        """CV-10: colpalette(magma) selects Magma256 palette."""
        from bokeh.models import LinearColorMapper
        from bokeh import palettes
        fig = figure()
        src = self._src()
        gm = GlyphMapper()
        gm.map_scatter(fig, src, "y", "x",
                       {"colorvar": "grp", "colpalette": "magma"})
        # Flipped (WP-42 CV-3): the key's ColorBar; the key cell's swatches.
        cols = fig._dash_key_cell._dash_keycell["src"].data["c"]
        # Magma256[0] is a dark color different from Viridis256[0]
        assert list(cols)[0] != list(palettes.Viridis256)[0]
        assert list(cols)[0].lower() == palettes.Magma256[0].lower()


# ============================================================
# DAX-V: Dual-axis JSON verification
# ============================================================

class TestDualAxisJsonVerification:
    def test_extra_y_range_in_html(self):
        """DAX-V1: yaxis(2) → extra_y_ranges entry appears in Bokeh JSON."""
        from bokeh.models import Range1d
        html = _render([
            {"type": "scatter", "yvar": "y", "xvar": "x", "options": {}},
            {"type": "line", "yvar": "y2", "xvar": "x", "options": {"yaxis": "2"}},
        ])
        # Read from the page's document: "extra_y_ranges" (9 times) and
        # "Range1d" (47) are in the inlined BokehJS of a page with no
        # yaxis(2) (measured 24sep2026), so the text search this was could
        # not fail.  The one extra range, and the yaxis(2) layer on it.
        fig = _page_figure(html)
        assert list(fig.extra_y_ranges) == ["y2"], dict(fig.extra_y_ranges)
        assert isinstance(fig.extra_y_ranges["y2"], Range1d)
        assert [(type(r.glyph).__name__, r.y_range_name)
                for r in _layers(fig)] == [("Scatter", "default"),
                                           ("Line", "y2")]


    def test_secondary_y_renderer_count(self):
        """DAX-V2: figure with primary + secondary scatter -> both layers drawn.

        Two scatter layers, the second on the y2 range: 6 Scatter models.
        """
        html = _render([
            {"type": "scatter", "yvar": "y", "xvar": "x", "options": {}},
            {"type": "scatter", "yvar": "y2", "xvar": "x",
             "options": {"yaxis": "2"}},
        ])
        model = _bokeh_model_json(html)
        # Not the legend-only key proxies' own Scatter models (WP-43
        # LT-21): they draw the legend's keys, not a layer.
        drawn = {id(d) for d in drawn_page_models(_walk_json(model))}
        scatters = [d for d in _find_type(model, "Scatter") if id(d) in drawn]
        # Exactly three per layer (glyph, nonselection, muted): the floor
        # of 2 this was is met by ONE scatter layer, which writes three,
        # so the secondary layer could be missing (measured 24sep2026:
        # 3 models for one layer, 6 for these two).
        assert len(scatters) == 6, f"Expected 6 Scatter models, found {len(scatters)}"
        # The layers themselves: both drawn, the second on the y2 range.
        assert [(type(r.glyph).__name__, r.y_range_name)
                for r in _layers(_page_figure(html))] == [
                    ("Scatter", "default"), ("Scatter", "y2")]


    def test_linear_axis_on_right(self):
        """DAX-V3: yaxis(2) beside a first-axis layer → a LinearAxis on the
        right, reading the y2 range, in the page's document."""
        from bokeh.models import LinearAxis
        html = _render([
            {"type": "scatter", "yvar": "y", "xvar": "x", "options": {}},
            {"type": "line", "yvar": "y2", "xvar": "x",
             "options": {"yaxis": "2"}},
        ])
        # Read from the page's document: "LinearAxis" is in the inlined
        # BokehJS 14 times in a page with no yaxis(2), whose own figure
        # has a LinearAxis on its left (measured 24sep2026).  The one this
        # test names is on the RIGHT, reading the y2 range the layer draws.
        fig = _page_figure(html)
        assert [a.y_range_name for a in fig.right
                if isinstance(a, LinearAxis)] == ["y2"]
        assert "y2" in fig.extra_y_ranges
        assert [(type(r.glyph).__name__, r.y_range_name)
                for r in _layers(fig)] == [("Scatter", "default"),
                                           ("Line", "y2")]

    def test_a_lone_second_axis_is_drawn_on_the_left(self):
        """DAX-V3b: a LONE yaxis(2) layer gets twoway's one axis, on the
        left (measured 24sep2026 from the SVG export of `twoway scatter
        mpg weight, yaxis(2)'): no right axis and no second range in the
        page's document (BUGS.md, S3)."""
        from bokeh.models import LinearAxis
        html = _render([
            {"type": "line", "yvar": "y2", "xvar": "x",
             "options": {"yaxis": "2"}},
        ])
        fig = _page_figure(html)
        assert [a for a in fig.right if isinstance(a, LinearAxis)] == []
        assert len([a for a in fig.left if isinstance(a, LinearAxis)]) == 1
        assert "y2" not in fig.extra_y_ranges
        assert [(type(r.glyph).__name__, r.y_range_name)
                for r in _layers(fig)] == [("Line", "default")]



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
        # `"<style>" in html' could not fail: Bokeh's own page template
        # writes a <style> (its `html, body' rule) into every page, with the
        # scheme's block or without it (measured 24sep2026).  The scheme's
        # block is the one carrying s2color's rules: `color background
        # ltbluishgray' (rgb 234 242 243) on the body and `color heading
        # dknavy' (rgb 30 45 83) on the title, from Stata's own style files.
        bg = re.compile(r"body\s*\{\s*background-color:\s*#eaf2f3\s*;")
        head = re.compile(r"\.db-title\s*\{\s*color:\s*#1e2d53\s*;")

        def _styles(h):
            return re.findall(r"<style>(.*?)</style>", h, re.DOTALL)
        assert any(bg.search(s) and head.search(s) for s in _styles(html)), \
            "s2color's rules are in no <style> element"
        # stcolor's page, background white, has neither rule: they are the
        # scheme's, not text every page carries.
        ctl = _render(
            [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}],
            build_opts={"scheme": "stcolor"},
        )
        assert not any(bg.search(s) or head.search(s) for s in _styles(ctl))

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
        # The search above cannot fail: every page's JSON holds "white"
        # twice, the box-zoom and box-select overlays' handle fill, and an
        # s2color page holds "#ffffff" not once -- Bokeh leaves out a value
        # equal to its default, and white is the default plot background
        # (measured 24sep2026).  So the colours are read back from the
        # page's document: s2color's white `color plotregion' inside its
        # ltbluishgray `color background', #eaf2f3 -- a page with no scheme
        # applied is white on white.  s1rcolor's page, black on black, is
        # the control that the reading sees a scheme's colours.
        fig = _page_figure(html)
        assert (fig.background_fill_color, fig.border_fill_color) == (
            "#ffffff", "#eaf2f3"), (fig.background_fill_color,
                                    fig.border_fill_color)
        ctl = _page_figure(_render(
            [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}],
            build_opts={"scheme": "s1rcolor"},
        ))
        assert (ctl.background_fill_color, ctl.border_fill_color) == (
            "#000000", "#000000")


# ============================================================
# COLOR-V: Color hex values in JSON model
# ============================================================

class TestColorHexInJson:
    def test_mcolor_named_hex_in_scatter_json(self):
        """COL-V1: mcolor(magenta) -> its hex #ff00ff in Bokeh JSON.

        This set navy and found #1a476f, which s2color's own navy markers
        put in the model whatever mcolor() said (measured 24sep2026: it
        passed with the option taken away).  Magenta is in no s2color slot,
        and the control below shows it absent until the option asks.
        """
        base = _bokeh_model_json(_render([{"type": "scatter", "yvar": "y",
                                           "xvar": "x", "options": {}}]))
        assert not _find_color_value(base, "#ff00ff")
        html = _render([{"type": "scatter", "yvar": "y", "xvar": "x",
                         "options": {"mcolor": "magenta"}}])
        model = _bokeh_model_json(html)
        found = _find_color_value(model, "#ff00ff")
        assert found, "#ff00ff (magenta) not in Bokeh JSON model"
        # ...and it is the marker's colour, fill and outline.
        layers = _layers(_page_figure(html))
        assert len(layers) == 1, f"{len(layers)} layers, not 1"
        glyph = layers[0].glyph
        assert (_spec_value(glyph.fill_color),
                _spec_value(glyph.line_color)) == ("#ff00ff", "#ff00ff")

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
        test_color_fidelity.py for the other 51.  The bar fills it at its
        intensity, inten80: #cd375d (WP-30 P1.2b; twoway's SVG, plan section 16 Evidence E3).
        """
        html = _render([{"type": "bar", "yvar": "y", "xvar": "x",
                         "options": {"fcolor": "cranberry"}}])
        model = _bokeh_model_json(html)
        raw = json.dumps(model).lower()
        assert "#cd375d" in raw  # Stata cranberry at inten80

    def test_mcolor_alpha_hex_still_present(self):
        """COL-V4: mcolor(magenta%50) -> the marker is #ff00ff, and the 50%
        is its alpha, not part of its colour.

        This was navy%50 and looked for #1a476f anywhere in the model, where
        s2color's navy markers put it whatever mcolor() said (measured
        24sep2026).  The glyph carrying the colour is read instead, with the
        alpha beside it: the default marker is drawn at 0.8.
        """
        html = _render([{"type": "scatter", "yvar": "y", "xvar": "x",
                         "options": {"mcolor": "magenta%50"}}])
        model = _bokeh_model_json(html)
        marks = [d["attributes"] for d in _walk_json(model)
                 if d.get("name") == "Scatter"
                 and (d.get("attributes", {}).get("fill_color") or {})
                 .get("value") == "#ff00ff"]
        assert marks, "no marker is drawn in #ff00ff"
        # WP-30 P1.12a (ratification row 27): the brushed-away (0.1) and
        # muted (0.2) copies now carry the glyph's magenta too, dimmed and
        # never above the glyph's 0.5; they were drawn in the scheme's navy.
        assert sorted(a["fill_alpha"]["value"] for a in marks) == \
            [pytest.approx(0.1), pytest.approx(0.2), pytest.approx(0.5)], marks
        # The drawn layer itself: one, magenta fill and outline, at 0.5.
        layers = _layers(_page_figure(html))
        assert len(layers) == 1, f"{len(layers)} layers, not 1"
        glyph = layers[0].glyph
        assert (_spec_value(glyph.fill_color),
                _spec_value(glyph.line_color)) == ("#ff00ff", "#ff00ff")
        assert _spec_value(glyph.fill_alpha) == pytest.approx(0.5)

    def test_n_rows_match_filter(self):
        """COL-V5: in_expr='1/10' filter → exactly 10 data points in CDS."""
        html = _render(
            [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}],
            in_expr="1/10",
        )
        model = _bokeh_model_json(html)
        n = _count_data_points(model, "x")
        assert n == 10, f"Expected 10 data points after in(1/10), got {n}"
