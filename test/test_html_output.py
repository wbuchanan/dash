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
import base64
import gzip
import json
import tempfile
import re
from html import unescape as _unescape
from html.parser import HTMLParser
import numpy as np
import pandas as pd
import pytest
import bokeh
from bokeh import models as bkm

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import warnings  # noqa: E402
import dash_render  # noqa: E402
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


def _extract_model_json(html: str) -> str:
    """Extract the Bokeh model JSON block from rendered HTML.

    With INLINE resources, the full Bokeh JS bundle is embedded in the HTML
    alongside the model JSON.  This helper extracts only the
    ``<script type="application/json">`` block that contains the serialized
    Bokeh document, so tests can search the model data without matching
    strings that appear inside the JS library itself.

    Fails when the page has no such block.  It returned "" then, and an
    absence check run on "" passed whatever the page drew: measured
    24sep2026, a page with its document cut out passed the "LogScale",
    "output_backend" and "webgl" absence checks alike.
    """
    _tag, start, end = _document_span(html)
    return html[start:end]


def _document_span(html: str) -> tuple:
    """``(tag start, content start, content end)`` of the page's
    ``<script type="application/json">`` block, the one Bokeh writes its
    document into; fails when the page has none."""
    m = re.search(r'<script[^>]+type=["\']application/json["\'][^>]*>', html)
    assert m, "the page embeds no Bokeh document (no application/json block)"
    end = html.find("</script>", m.end())
    assert end != -1, "the page's Bokeh document block is never closed"
    return m.start(), m.end(), end


def _outside_document(html: str) -> str:
    """The page with its embedded document cut out: the markup the browser
    parses as HTML, and BokehJS's code.  Text the document carries is
    escaped there as a whole, so it is never markup; text found here is."""
    tag, _start, end = _document_span(html)
    return html[:tag] + html[end:]


def _figure_colors(html: str, prop: str) -> list:
    """The value each Figure in the page's Bokeh document gives *prop*.

    Read from the document itself -- unescaped and parsed, as BokehJS reads
    it -- so a colour is found on the property it was meant for and not
    anywhere in the page.  None where the property is left at Bokeh's
    default, which the document does not write.
    """
    doc = json.loads(_unescape(_extract_model_json(html)))
    out = []

    def walk(node):
        if isinstance(node, dict):
            attrs = node.get("attributes")
            if node.get("name") == "Figure" and isinstance(attrs, dict):
                out.append(attrs.get(prop))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(doc)
    return out


def _page_models(html: str) -> dict:
    """``{model name: [attributes, ...]}`` for every model in the page's
    embedded Bokeh document.

    A model's name searched in the page's text cannot fail: the page embeds
    BokehJS whole, and its code names every model -- "Scatter", "Quad",
    "Segment", "VArea", "Span" and "LogScale" are on the page of a graph
    that draws none of them (measured 24sep2026).  The document is read
    instead, unescaped and parsed as BokehJS reads it.
    """
    doc = json.loads(_unescape(_extract_model_json(html)))
    out = {}

    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "object" and "name" in node:
                out.setdefault(node["name"], []).append(
                    node.get("attributes", {}))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(doc)
    return out


def _doc_models(html: str) -> dict:
    """``{id: model}`` for every model in the page's embedded document.

    A model is written out once and referred to by ``{"id": ...}`` after
    that, so every reader resolves its references through this table.
    """
    doc = json.loads(_unescape(_extract_model_json(html)))
    byid = {}

    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "object" and "name" in node:
                byid[node.get("id")] = node
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(doc)
    return byid


def _column(col) -> list:
    """One ColumnDataSource column as a list.  Bokeh writes a column as a
    list, or as an ndarray: base64 bytes, gzipped when that is smaller,
    with its dtype, byte order and shape."""
    if isinstance(col, list):
        return col
    if isinstance(col, dict) and col.get("type") == "ndarray":
        arr = col.get("array")
        if isinstance(arr, list):
            return arr
        if isinstance(arr, dict) and arr.get("type") == "bytes":
            raw = base64.b64decode(arr["data"])
            if raw[:2] == b"\x1f\x8b":
                raw = gzip.decompress(raw)
            dt = np.dtype(col["dtype"]).newbyteorder(
                "<" if col.get("order", "little") == "little" else ">")
            return np.frombuffer(raw, dtype=dt).reshape(
                col.get("shape") or [-1]).tolist()
    raise AssertionError("a column the reader cannot decode: %r" % (col,))


def _figure_layers(html: str) -> list:
    """For each figure in the page's document, in order, each layer it
    draws: ``{"glyph": model name, "props": the glyph's attributes,
    "data": {column: list}, "shown": the source rows its view keeps,
    "rows": how many}`` for every visible GlyphRenderer on the figure that
    draws at least one row.

    A renderer anywhere in the document is not enough: one a legend item or
    a hover tool still refers to is written into the document though no
    figure draws it.  Measured 24sep2026: a scatter taken off its figure
    left "Plot has no renderers" and its red Scatter glyph in the document,
    through the legend.  Nor is a renderer with no rows: a refused function
    expression leaves its Line on the figure, drawing nothing.  Nor is its
    source's size: linked by() panels share one source of every row, and
    each panel's view keeps its own group's.
    """
    byid = _doc_models(html)

    def resolve(ref):
        return byid.get(ref.get("id"), {}) if isinstance(ref, dict) else {}

    def kept(view, n):
        flt = resolve(resolve(view).get("attributes", {}).get("filter"))
        name, fa = flt.get("name", "AllIndices"), flt.get("attributes", {})
        if name == "AllIndices":
            return list(range(n))
        if name == "BooleanFilter":
            return [i for i, b in enumerate(_column(fa.get("booleans", [])))
                    if b]
        if name == "IndexFilter":
            return [int(i) for i in _column(fa.get("indices", []))]
        raise AssertionError("a view filter the reader cannot apply: %s"
                             % name)

    out = []
    for fig in [m for m in byid.values() if m["name"] == "Figure"]:
        layers = []
        for ref in fig.get("attributes", {}).get("renderers", []):
            r = resolve(ref)
            attrs = r.get("attributes", {})
            if r.get("name") != "GlyphRenderer" \
                    or not attrs.get("visible", True):
                continue
            src = resolve(attrs.get("data_source")).get(
                "attributes", {}).get("data", {})
            data = {k: _column(v) for k, v in
                    (src.get("entries", []) if isinstance(src, dict) else [])}
            shown = kept(attrs.get("view"),
                         max((len(v) for v in data.values()), default=0))
            if shown:
                glyph = resolve(attrs.get("glyph"))
                layers.append({"glyph": glyph.get("name"),
                               "props": glyph.get("attributes", {}),
                               "data": data, "shown": shown,
                               "rows": len(shown)})
        out.append(layers)
    return out


def _figure_glyphs(html: str) -> list:
    """For each figure in the page's document, in order, the glyph type of
    each layer it draws (``_figure_layers``) -- what the page draws, panel
    by panel."""
    return [[layer["glyph"] for layer in fig] for fig in _figure_layers(html)]


def _only_layer(html: str, glyph: str) -> dict:
    """The one layer the page draws, on its one figure: a *glyph*."""
    drawn = _figure_glyphs(html)
    assert drawn == [[glyph]], drawn
    return _figure_layers(html)[0][0]


#: A glyph property the document does not write (see ``_values``).
_ABSENT = object()


def _values(layer: dict, prop: str, default=None) -> list:
    """The value a layer's glyph gives *prop* at each row it draws.

    Bokeh writes a glyph property as a column (``{"type": "field",
    "field": name}``), a constant (``{"type": "value", "value": v}``, or
    the bare value), or not at all when it keeps Bokeh's own default --
    *default*, which the caller takes from Bokeh (``bkm.VBar().bottom``).
    """
    spec = layer["props"].get(prop, _ABSENT)
    if spec is _ABSENT:
        return [default] * layer["rows"]
    if isinstance(spec, dict) and spec.get("type") == "field":
        column = layer["data"][spec["field"]]
        return [column[i] for i in layer["shown"]]
    if isinstance(spec, dict) and spec.get("type") == "value":
        return [spec["value"]] * layer["rows"]
    return [spec] * layer["rows"]


def _figure_models(html: str, attr: str) -> list:
    """For each figure in the page's document, in order, the model its
    *attr* refers to -- ``x_range``, ``y_range``, ``title`` -- as
    ``(name, attributes)``; ``(None, {})`` where it refers to none."""
    byid = _doc_models(html)
    out = []
    for fig in [m for m in byid.values() if m["name"] == "Figure"]:
        ref = fig.get("attributes", {}).get(attr)
        mod = byid.get(ref.get("id"), {}) if isinstance(ref, dict) else {}
        out.append((mod.get("name"), mod.get("attributes", {})))
    return out


def _figure_titles(html: str) -> list:
    """Each figure's title text, in order; None where it has none."""
    return [attrs.get("text") for _name, attrs
            in _figure_models(html, "title")]


def _grid_cells(html: str) -> list:
    """``(title, row, column)`` of each figure a GridPlot in the page's
    document places, in order: where each panel is drawn."""
    byid = _doc_models(html)
    out = []
    for grid in [m for m in byid.values() if m["name"] == "GridPlot"]:
        for child in grid.get("attributes", {}).get("children", []):
            fig = byid.get(child[0].get("id"), {})
            if fig.get("name") == "Figure":
                title = byid.get(fig.get("attributes", {}).get(
                    "title", {}).get("id"), {}).get("attributes", {})
                out.append((title.get("text"), child[1], child[2]))
    return out


def _text_homes(html: str, needle: str) -> list:
    """Every string in the page's document that holds *needle*, in document
    order, as ``(model, attribute, string)``: the model the string belongs
    to and the attribute it is the value of."""
    doc = json.loads(_unescape(_extract_model_json(html)))
    out = []

    def walk(node, model, attr):
        if isinstance(node, dict):
            if node.get("type") == "object" and "name" in node:
                model = node["name"]
            for k, v in node.items():
                walk(v, model, attr if k == "attributes" else k)
        elif isinstance(node, list):
            for v in node:
                walk(v, model, attr)
        elif isinstance(node, str) and needle in node:
            out.append((model, attr, node))

    walk(doc, None, None)
    return out


class _TagsAndText(HTMLParser):
    """The elements an HTML fragment opens and the text it shows."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags, self.text = [], []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)

    def handle_data(self, data):
        self.text.append(data)


def _markup(fragment: str) -> tuple:
    """``(elements, text)`` of an HTML fragment as a browser parses it: the
    tags it opens, in order, and its text with entities decoded.  A Div's
    text is HTML to BokehJS, so this is what a Div shows."""
    p = _TagsAndText()
    p.feed(fragment)
    p.close()
    return p.tags, "".join(p.text)


def _header_divs(html: str) -> list:
    """Each Div in the page's document, in order, read by ``_markup``."""
    return [_markup(div.get("text", ""))
            for div in _page_models(html).get("Div", [])]


def _page_scripts(html: str) -> list:
    """``(attributes, body)`` of each <script> element in the page, in
    order; an element ends at the first ``</script>``, as HTML parsing
    ends it."""
    return re.findall(r"<script\b([^>]*)>(.*?)</script>", html, re.S)


def _inlined_bokehjs(html: str) -> list:
    """The bodies of the page's inline copies of BokehJS itself: a <script>
    with no src that holds Bokeh's bundle and declares the version of the
    bokeh that wrote the page."""
    stamp = re.compile(r'\bversion\s*=\s*"%s"' % re.escape(bokeh.__version__))
    return [body for attrs, body in _page_scripts(html)
            if "src=" not in attrs
            and body.lstrip().startswith("/* BEGIN bokeh.min.js */")
            and len(stamp.findall(body)) == 1]


def _assert_drawn_as_text(html: str, payload: str, model: str) -> None:
    """*payload* reaches the page as the text of exactly one *model* -- a
    Title or a Label, which BokehJS draws on the canvas, where text is
    never markup -- and nowhere else: in no Div, HTMLTitle or HTMLLabel,
    whose text BokehJS renders as HTML, and not in the page's own markup.

    The page text cannot show this.  The document is escaped as a whole on
    its way into the page, so the payload is never in the page text,
    whether dash draws it as text or as live markup: measured 24sep2026, a
    graph title also drawn as an HTMLTitle, and a note drawn as an
    HTMLLabel, both passed ``payload not in html``.
    """
    homes = _text_homes(html, payload)
    assert homes == [(model, "text", payload)], homes
    markup = _outside_document(html)
    # What is read is the page's own markup: its Bokeh root element is here.
    assert re.search(r'<div id="[^"]+" data-root-id="[^"]+"', markup), \
        "the page's own markup has no Bokeh root element"
    assert payload not in markup, "the payload is live in the page's markup"


def _drawn_glyphs(html: str) -> list:
    """Every glyph type the page draws, figure after figure, in order."""
    return [g for fig in _figure_glyphs(html) for g in fig]


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
        # The scatter's twenty rows, read from the page's embedded document.
        # This looked for '"type"' and '"attributes"' in the page text:
        # BokehJS spells '"type"' itself and every document -- its toolbar
        # alone -- spells both, so a page whose sources carried no rows at
        # all passed (measured 24sep2026).
        pts = _only_layer(html, "Scatter")
        assert _values(pts, "x") == [float(i) for i in range(1, 21)]
        assert _values(pts, "y") == [float(i) for i in range(1, 21)]

    def test_html_not_empty(self):
        """Rendered HTML is not empty for any standard plot type."""
        # Not empty is a page that draws its plot, all twenty rows.  This
        # was len(html) > 1000, which a page inlining 1.6 MB of BokehJS
        # passes drawing nothing (measured 24sep2026).
        for ptype, glyph in (("scatter", "Scatter"), ("line", "Line"),
                             ("bar", "VBar"), ("spike", "Segment")):
            spec, data = _single_graph_spec(ptype, {"yvar": "y", "xvar": "x"})
            drawn = [[(layer["glyph"], layer["rows"]) for layer in fig]
                     for fig in _figure_layers(_render_to_html(spec, data))]
            assert drawn == [[(glyph, 20)]], (ptype, drawn)


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
        assert "Scatter" in _drawn_glyphs(html)

    def test_scatter_html_non_empty(self):
        """scatter HTML output is non-trivial."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        # One figure drawing all twenty points.  len(html) > 500 passed on
        # a page drawing nothing: the inlined BokehJS is 1.6 MB.
        drawn = [[(layer["glyph"], layer["rows"]) for layer in fig]
                 for fig in _figure_layers(html)]
        assert drawn == [[("Scatter", 20)]], drawn


class TestLineHtmlOutput:
    def test_line_html_contains_line_glyph(self):
        """line plot HTML references Line glyph."""
        spec, data = _single_graph_spec("line", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "Line" in _drawn_glyphs(html)


class TestHistogramHtmlOutput:
    def test_histogram_html_contains_quad_glyph(self):
        """histogram HTML contains Quad glyph (used for bars)."""
        spec, data = _single_graph_spec("histogram", {"var": "y"})
        html = _render_to_html(spec, data)
        assert "Quad" in _drawn_glyphs(html)


class TestBarHtmlOutput:
    def test_bar_html_contains_vbar_glyph(self):
        """bar plot HTML contains VBar glyph."""
        spec, data = _single_graph_spec("bar", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "VBar" in _drawn_glyphs(html)


class TestSpikeHtmlOutput:
    def test_spike_html_contains_segment_glyph(self):
        """spike plot HTML contains Segment glyph."""
        spec, data = _single_graph_spec("spike", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "Segment" in _drawn_glyphs(html)


class TestLfitHtmlOutput:
    def test_lfit_html_contains_line_glyph(self):
        """lfit plot HTML contains a Line glyph (fitted line)."""
        spec, data = _single_graph_spec("lfit", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "Line" in _drawn_glyphs(html)


class TestRareaHtmlOutput:
    def test_rarea_html_contains_varea_glyph(self):
        """rarea HTML contains VArea glyph."""
        spec, data = _single_graph_spec(
            "rarea", {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}
        )
        html = _render_to_html(spec, data)
        assert "VArea" in _drawn_glyphs(html)


class TestDroplineHtmlOutput:
    def test_dropline_html_contains_segment_glyph(self):
        """dropline HTML contains Segment glyph."""
        spec, data = _single_graph_spec("dropline", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "Segment" in _drawn_glyphs(html)


class TestMsplineHtmlOutput:
    def test_mspline_html_contains_line_glyph(self):
        """mspline HTML contains a Line glyph."""
        spec, data = _single_graph_spec("mspline", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "Line" in _drawn_glyphs(html)


class TestFunctionHtmlOutput:
    def test_function_html_contains_line_glyph(self):
        """function plot HTML contains a Line glyph."""
        spec, data = _single_graph_spec(
            "function",
            {"expr": "sin(x)"},
            options={"range": "0 6.28"},
        )
        html = _render_to_html(spec, data)
        assert "Line" in _drawn_glyphs(html)


# ================================================================
# XSS safety in HTML output
# ================================================================

class TestConnectedHtmlOutput:
    def test_connected_html_contains_line_and_scatter(self):
        """connected plot HTML references both Line and Scatter glyphs."""
        spec, data = _single_graph_spec("connected", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "Line" in _drawn_glyphs(html), "connected must have Line glyph"
        assert "Scatter" in _drawn_glyphs(html), "connected must have Scatter glyph"


class TestAreaHtmlOutput:
    def test_area_html_contains_varea_glyph(self):
        """area plot HTML contains VArea glyph."""
        spec, data = _single_graph_spec("area", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "VArea" in _drawn_glyphs(html)


class TestQfitHtmlOutput:
    def test_qfit_html_contains_line_glyph(self):
        """qfit plot HTML contains Line glyph (quadratic fitted line)."""
        spec, data = _single_graph_spec("qfit", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "Line" in _drawn_glyphs(html)


class TestLfitciHtmlOutput:
    def test_lfitci_html_contains_varea_and_line(self):
        """lfitci plot HTML contains both VArea (CI band) and Line glyphs."""
        spec, data = _single_graph_spec("lfitci", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "VArea" in _drawn_glyphs(html), "lfitci must have VArea CI band"
        assert "Line" in _drawn_glyphs(html), "lfitci must have Line glyph"


class TestQfitciHtmlOutput:
    def test_qfitci_html_contains_varea_and_line(self):
        """qfitci plot HTML contains both VArea (CI band) and Line glyphs."""
        spec, data = _single_graph_spec("qfitci", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "VArea" in _drawn_glyphs(html), "qfitci must have VArea CI band"
        assert "Line" in _drawn_glyphs(html), "qfitci must have Line glyph"


class TestLowessHtmlOutput:
    def test_lowess_html_contains_line_glyph(self):
        """lowess plot HTML contains Line glyph (smoothed line)."""
        spec, data = _single_graph_spec("lowess", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "Line" in _drawn_glyphs(html)


class TestKdensityHtmlOutput:
    def test_kdensity_html_contains_line_glyph(self):
        """kdensity plot HTML contains Line glyph (density curve)."""
        spec, data = _single_graph_spec("kdensity", {"var": "y"})
        html = _render_to_html(spec, data)
        assert "Line" in _drawn_glyphs(html)


class TestRbarHtmlOutput:
    def test_rbar_html_contains_vbar_glyph(self):
        """rbar plot HTML contains VBar glyph."""
        spec, data = _single_graph_spec(
            "rbar", {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}
        )
        html = _render_to_html(spec, data)
        assert "VBar" in _drawn_glyphs(html)


class TestRspikeHtmlOutput:
    def test_rspike_html_contains_segment_glyph(self):
        """rspike plot HTML contains Segment glyph."""
        spec, data = _single_graph_spec(
            "rspike", {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}
        )
        html = _render_to_html(spec, data)
        assert "Segment" in _drawn_glyphs(html)


class TestRcapHtmlOutput:
    def test_rcap_html_contains_segment_glyph(self):
        """rcap plot HTML contains Segment glyph (spines and caps)."""
        spec, data = _single_graph_spec(
            "rcap", {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}
        )
        html = _render_to_html(spec, data)
        assert "Segment" in _drawn_glyphs(html)


class TestRlineHtmlOutput:
    def test_rline_html_contains_line_glyph(self):
        """rline plot HTML contains Line glyph (two range boundary lines)."""
        spec, data = _single_graph_spec(
            "rline", {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}
        )
        html = _render_to_html(spec, data)
        assert "Line" in _drawn_glyphs(html)


class TestRconnectedHtmlOutput:
    def test_rconnected_html_contains_line_and_scatter(self):
        """rconnected plot HTML contains both Line and Scatter glyphs."""
        spec, data = _single_graph_spec(
            "rconnected", {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}
        )
        html = _render_to_html(spec, data)
        assert "Line" in _drawn_glyphs(html), "rconnected must have Line glyph"
        assert "Scatter" in _drawn_glyphs(html), "rconnected must have Scatter glyph"


class TestDotHtmlOutput:
    def test_dot_html_contains_scatter_glyph(self):
        """dot plot HTML contains Scatter glyph."""
        spec, data = _single_graph_spec("dot", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "Scatter" in _drawn_glyphs(html)


class TestRcapsymHtmlOutput:
    def test_rcapsym_html_contains_segment_and_scatter(self):
        """rcapsym plot HTML contains Segment and Scatter glyphs."""
        spec, data = _single_graph_spec(
            "rcapsym", {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}
        )
        html = _render_to_html(spec, data)
        assert "Segment" in _drawn_glyphs(html), "rcapsym must have Segment glyph"
        assert "Scatter" in _drawn_glyphs(html), "rcapsym must have Scatter glyph"


class TestScatteriHtmlOutput:
    def test_scatteri_html_contains_scatter_glyph(self):
        """scatteri plot HTML contains Scatter glyph from inline coordinate pairs."""
        spec, data = _single_graph_spec(
            "scatteri",
            {"values": [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]},
        )
        html = _render_to_html(spec, data)
        assert "Scatter" in _drawn_glyphs(html)

    def test_scatteri_coordinates_embedded_in_json(self):
        """scatteri literal coordinate values must appear in the Bokeh JSON model."""
        spec, data = _single_graph_spec(
            "scatteri",
            {"values": [[7.0, 13.0], [42.0, 99.0]]},
        )
        html = _render_to_html(spec, data)
        # Each (y, x) pair is a point of the drawn scatter, read from the
        # document.  "7.0" and "42.0" were looked for in the page text,
        # where BokehJS carries both (18 and 1 copies, measured 24sep2026),
        # so a scatteri that drew no point, or swapped x and y, passed.
        pts = _only_layer(html, "Scatter")
        assert _values(pts, "y") == [7.0, 42.0]
        assert _values(pts, "x") == [13.0, 99.0]


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
        assert "Segment" in _drawn_glyphs(html)


class TestTslineHtmlOutput:
    def test_tsline_html_contains_line_glyph(self):
        """tsline plot HTML contains Line glyph."""
        spec, data = _single_graph_spec("tsline", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "Line" in _drawn_glyphs(html)


class TestTsrlineHtmlOutput:
    def test_tsrline_html_contains_line_glyph(self):
        """tsrline plot HTML contains Line glyph (two time-series boundary lines)."""
        spec, data = _single_graph_spec(
            "tsrline", {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}
        )
        html = _render_to_html(spec, data)
        assert "Line" in _drawn_glyphs(html)


class TestXssInHtmlOutput:
    def test_script_tag_in_title_is_escaped(self):
        """XSS: <script> in title must not appear unescaped in output HTML."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["title"] = "<script>alert(1)</script>"
        html = _render_to_html(spec, data)
        # The title is the figure's Title -- canvas text -- and live markup
        # nowhere.  "not in html" alone could not fail on the document.
        _assert_drawn_as_text(html, "<script>alert(1)</script>", "Title")

    def test_html_contains_csp_meta(self):
        """HTML output includes Content-Security-Policy meta tag."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "content-security-policy" in html.lower() or \
               "Content-Security-Policy" in html, \
               "HTML must include a CSP meta tag"


def _heads_on_page(html: str) -> int:
    """The arrowheads the page draws: its one Arrow annotation's source
    rows, the source being the one a Segment renderer draws from."""
    byid = _doc_models(html)
    arrows = [m for m in byid.values() if m["name"] == "Arrow"]
    assert len(arrows) == 1, f"{len(arrows)} Arrow annotations"
    attrs = arrows[0].get("attributes", {})
    assert attrs.get("x_start", {}).get("field") == "x1", attrs.get("x_start")
    src = byid[attrs["source"]["id"]]
    seg_srcs = {r["attributes"]["data_source"]["id"] for r in byid.values()
                if r["name"] == "GlyphRenderer"
                and byid.get(r["attributes"]["glyph"]["id"], {}).get("name")
                == "Segment"}
    assert src["id"] in seg_srcs, "the heads are not on the shaft's source"
    return len(_column(src["attributes"]["data"]["entries"][0][1]))


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
        # Both: the shaft is a Segment glyph and the heads ONE Arrow
        # annotation over the shaft's source, a head for each of its 10
        # rows (one fixed annotation per row did not follow a filter move,
        # BUGS.md 24sep2026).
        assert "Segment" in _drawn_glyphs(html)
        heads = _heads_on_page(html)
        assert heads == 10, f"{heads} arrowheads for 10 arrows"


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
        assert "Segment" in _drawn_glyphs(html)
        heads = _heads_on_page(html)
        assert heads == 10, f"{heads} two-headed arrows for 10 arrows"


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
        # FixedTicker tick values should be embedded in the model JSON --
        # read from the document: "FixedTicker" and "ticks" are words the
        # page's BokehJS carries whatever the axes do.
        assert [t.get("ticks") for t in _page_models(html).get("FixedTicker", [])] \
            == [[2.0, 6.0, 10.0, 14.0, 18.0]], \
            "xlabel() must embed FixedTicker (with ticks) in model JSON"

    def test_ylabel_tick_values_in_html(self):
        """ylabel() tick values must appear in the Bokeh model JSON in rendered HTML."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["ylabel"] = "5 10 15 20"
        html = _render_to_html(spec, data)
        assert [t.get("ticks") for t in _page_models(html).get("FixedTicker", [])] \
            == [[5.0, 10.0, 15.0, 20.0]], \
            "ylabel() must embed FixedTicker (with ticks) in model JSON"

    def test_xlabel_labeled_ticks_in_html(self):
        """xlabel() with labeled ticks must embed CustomJSTickFormatter in model JSON.

        Flipped (WP-30 P1.5): "exactly one CustomJSTickFormatter" was wrong
        once every numeric axis carries Stata's writer, because the y axis
        now has one too; the x axis's is the one holding the labels."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["xlabel"] = '1 "Low" 10 "Mid" 20 "High"'
        html = _render_to_html(spec, data)
        models = _page_models(html)
        fmts = [f for f in models.get("CustomJSTickFormatter", [])
                if "labels" in dict(f["args"]["entries"])]
        assert len(fmts) == 1, \
            "xlabel labeled ticks must produce CustomJSTickFormatter in model JSON"
        labels = json.loads(dict(fmts[0]["args"]["entries"])["labels"])
        assert labels == {"1.0": "Low", "10.0": "Mid", "20.0": "High"}, labels
        assert [t.get("ticks") for t in models.get("FixedTicker", [])] == \
            [[1.0, 10.0, 20.0]]

    def test_title_xss_not_in_html_unescaped(self):
        """XSS payload in title does not appear as a raw <script> tag in output."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["title"] = "<script>alert(2)</script>"
        html = _render_to_html(spec, data)
        # Bokeh escapes the whole document on its way into the page, so the
        # literal tag is never in the page text whatever model carries it;
        # the document is read instead (see _assert_drawn_as_text).
        _assert_drawn_as_text(html, "<script>alert(2)</script>", "Title")


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

    def test_mcolor_named_colour_appears_in_scatter_html(self):
        """mcolor(magenta) produces #ff00ff in scatter HTML Bokeh JSON.

        This was mcolor(navy) and #1a476f -- s2color's first series colour,
        in the page whether or not the option was read.  Magenta is in no
        s2color slot (see TestTheColoursUnderTestAreNotDrawnByDefault).
        """
        spec, data = _single_graph_spec(
            "scatter", {"yvar": "y", "xvar": "x"}, options={"mcolor": "magenta"}
        )
        html = _render_to_html(spec, data)
        assert "#ff00ff" in html, "mcolor(magenta) should produce #ff00ff in Bokeh JSON"

    def test_mcolor_rgb_triplet_in_scatter_html(self):
        """mcolor with RGB triplet produces correct hex in HTML."""
        spec, data = _single_graph_spec(
            "scatter", {"yvar": "y", "xvar": "x"}, options={"mcolor": "0 0 255"}
        )
        html = _render_to_html(spec, data)
        assert "#0000ff" in html, "mcolor(0 0 255) should produce #0000ff"

    def test_lcolor_named_colour_appears_in_line_html(self):
        """lcolor(magenta) produces #ff00ff in line HTML Bokeh JSON (it was
        navy, the default, which passed with the option ignored)."""
        spec, data = _single_graph_spec(
            "line", {"yvar": "y", "xvar": "x"}, options={"lcolor": "magenta"}
        )
        html = _render_to_html(spec, data)
        assert "#ff00ff" in html, "lcolor(magenta) should produce #ff00ff in Bokeh JSON"

    def test_fcolor_maroon_appears_in_area_html(self):
        """fcolor(maroon) is filled at the area's intensity: #a65d62 in the
        area HTML Bokeh JSON (WP-30 P1.2b; twoway's SVG, plan section 16 Evidence E3)."""
        spec, data = _single_graph_spec(
            "area", {"yvar": "y", "xvar": "x"}, options={"fcolor": "maroon"}
        )
        html = _render_to_html(spec, data)
        assert "#a65d62" in html, "fcolor(maroon) should produce #a65d62 in Bokeh JSON"

    def test_fcolor_in_bar_html(self):
        """fcolor(forest_green) in bar produces Stata's #55752f in HTML.

        This asserted #538d22, which is not a colour Stata has.  Stata's
        own style/color-forest_green.style sets rgb "85 117 47" = #55752f;
        52 of the 92 named colours disagreed with their style files the same
        way.  See test_color_fidelity.py.  The bar fills it at its intensity,
        inten80: #779159 (WP-30 P1.2b; twoway's SVG, plan section 16 Evidence E3).
        """
        spec, data = _single_graph_spec(
            "bar", {"yvar": "y", "xvar": "x"}, options={"fcolor": "forest_green"}
        )
        html = _render_to_html(spec, data)
        assert "#779159" in html, "fcolor(forest_green) should fill #779159"

    def test_combined_mcolor_and_lcolor_in_scatter_html(self):
        """mcolor() and lcolor() together on a scatter: the markers are
        mcolor()'s, fill and outline, and lcolor() leaves them alone.

        This said both options "appear", set lcolor(navy) -- s2color's
        first series colour, which the page carries with the option ignored
        -- and checked only the red.  lcolor() colours a layer's lines and
        a scatter draws none: twoway leaves every marker as drawn without
        it (twoway's SVG, 23sep2026, as recorded in dash_render.py
        _apply_marker_opts).  So lcolor() is magenta, which no s2color slot
        uses, and it must reach no model at all.
        """
        spec, data = _single_graph_spec(
            "scatter", {"yvar": "y", "xvar": "x"},
            options={"mcolor": "red", "lcolor": "magenta"},
        )
        html = _render_to_html(spec, data)
        pts = _only_layer(html, "Scatter")
        assert _values(pts, "fill_color") == ["#ff0000"] * 20
        assert _values(pts, "line_color") == ["#ff0000"] * 20
        # The reader finds a colour where one is: red, on the markers only.
        assert {m for m, _a, _s in _text_homes(html, "#ff0000")} \
            == {"Scatter"}
        assert _text_homes(html, "#ff00ff") == []


# ================================================================
# The colours the tests look for are not drawn without the option
# ================================================================
_ONE_Y = {"yvar": "y", "xvar": "x"}
_RANGE_Y = {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}


class TestTheColoursUnderTestAreNotDrawnByDefault:
    """Guards the guards: a test that sets a colour and finds its hex in the
    page proves the option was read only if the hex is absent without it.

    Navy failed this for every plot type below -- #1a476f is s2color's first
    series colour -- so every navy test in this file passed with the option
    ignored.  Each hex another test here looks for is checked on the same
    plot drawn with no colour option at all.
    """

    @pytest.mark.parametrize("ptype,extra,hexes", [
        ("scatter", _ONE_Y, ["#ff00ff", "#ff0000", "#0000ff"]),
        ("line", _ONE_Y, ["#ff00ff"]),
        ("area", _ONE_Y, ["#90353b"]),
        ("bar", _ONE_Y, ["#ff00ff", "#55752f", "#ff0000"]),
        ("spike", _ONE_Y, ["#ff00ff"]),
        ("lfit", _ONE_Y, ["#ff00ff"]),
        ("qfit", _ONE_Y, ["#ff00ff"]),
        ("lowess", _ONE_Y, ["#ff00ff"]),
        ("kdensity", {"var": "y"}, ["#ff00ff"]),
        ("rline", _RANGE_Y, ["#ff00ff"]),
        ("rspike", _RANGE_Y, ["#ff00ff"]),
        ("rcap", _RANGE_Y, ["#ff00ff"]),
        ("tsline", _ONE_Y, ["#ff00ff"]),
        ("tsrline", _RANGE_Y, ["#ff00ff"]),
        ("mspline", _ONE_Y, ["#ff00ff"]),
        ("function", {"expr": "x", "range": [0, 10]}, ["#ff00ff"]),
        ("dropline", _ONE_Y, ["#ff00ff"]),
        ("pcspike", {"y1var": "y", "x1var": "x", "y2var": "hi",
                     "x2var": "lo"}, ["#ff00ff"]),
        ("connected", _ONE_Y, ["#ff00ff"]),
        ("dot", _ONE_Y, ["#ff00ff"]),
        ("rcapsym", _RANGE_Y, ["#ff00ff"]),
        ("rconnected", _RANGE_Y, ["#ff00ff"]),
        ("scatteri", {"values": [[1.0, 2.0], [3.0, 4.0]]}, ["#ff00ff"]),
        ("rbar", _RANGE_Y, ["#ff00ff"]),
        ("histogram", {"var": "y"}, ["#ff00ff"]),
        ("lfitci", _ONE_Y, ["#ff00ff"]),
        ("qfitci", _ONE_Y, ["#ff00ff"]),
        ("rarea", _RANGE_Y, ["#ff00ff"]),
    ])
    def test_the_colour_is_absent_without_the_option(self, ptype, extra,
                                                     hexes):
        spec, data = _single_graph_spec(ptype, extra)
        html = _render_to_html(spec, data).lower()
        drawn = [h for h in hexes if h in html]
        assert not drawn, (
            "%s draws %s with no colour option, so a test that sets it and "
            "finds it proves nothing" % (ptype, drawn))


# ================================================================
# Color rendering tests — all 26 remaining plot types must embed
# the resolved color hex value in the Bokeh JSON model in HTML
# ================================================================
class TestColorRenderingAllPlotTypes:
    """Verify lcolor/mcolor/fcolor option produces correct hex in HTML JSON
    for the 26 plot types not covered by TestPlotOptionsInHtml.

    These set navy and looked for #1a476f anywhere in the page.  Navy is
    s2color's first series colour, so every one of them passed with the
    option ignored: measured 24sep2026, #1a476f is in the page of every
    one of these plot types drawn with no colour option at all.  Magenta
    is in no slot of the s2color palette, and
    TestTheColoursUnderTestAreNotDrawnByDefault checks it is absent
    until the option asks for it.
    """

    _HEX = "#ff00ff"    # translate_mcolor("magenta")
    _RED  = "#ff0000"   # translate_mcolor("red")

    def _html(self, ptype, extra_keys, option_key, option_val="magenta"):
        spec, data = _single_graph_spec(ptype, extra_keys, options={option_key: option_val})
        return _render_to_html(spec, data)

    # --- line-style plot types (lcolor) ---

    def test_spike_lcolor_in_html(self):
        html = self._html("spike", {"yvar": "y", "xvar": "x"}, "lcolor")
        assert self._HEX in html, "spike lcolor(magenta) must embed #ff00ff in model JSON"

    def test_lfit_lcolor_in_html(self):
        html = self._html("lfit", {"yvar": "y", "xvar": "x"}, "lcolor")
        assert self._HEX in html, "lfit lcolor(magenta) must embed #ff00ff in model JSON"

    def test_qfit_lcolor_in_html(self):
        html = self._html("qfit", {"yvar": "y", "xvar": "x"}, "lcolor")
        assert self._HEX in html, "qfit lcolor(magenta) must embed #ff00ff in model JSON"

    def test_lowess_lcolor_in_html(self):
        # No statsmodels skip: lowess is Stata's smoother in numpy (WP-18).
        html = self._html("lowess", {"yvar": "y", "xvar": "x"}, "lcolor")
        assert self._HEX in html, "lowess lcolor(magenta) must embed #ff00ff in model JSON"

    def test_kdensity_lcolor_in_html(self):
        html = self._html("kdensity", {"var": "y"}, "lcolor")
        assert self._HEX in html, "kdensity lcolor(magenta) must embed #ff00ff in model JSON"

    def test_rline_lcolor_in_html(self):
        html = self._html("rline",
                          {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}, "lcolor")
        assert self._HEX in html, "rline lcolor(magenta) must embed #ff00ff in model JSON"

    def test_rspike_lcolor_in_html(self):
        html = self._html("rspike",
                          {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}, "lcolor")
        assert self._HEX in html, "rspike lcolor(magenta) must embed #ff00ff in model JSON"

    def test_rcap_lcolor_in_html(self):
        html = self._html("rcap",
                          {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}, "lcolor")
        assert self._HEX in html, "rcap lcolor(magenta) must embed #ff00ff in model JSON"

    def test_tsline_lcolor_in_html(self):
        html = self._html("tsline", {"yvar": "y", "xvar": "x"}, "lcolor")
        assert self._HEX in html, "tsline lcolor(magenta) must embed #ff00ff in model JSON"

    def test_tsrline_lcolor_in_html(self):
        html = self._html("tsrline",
                          {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}, "lcolor")
        assert self._HEX in html, "tsrline lcolor(magenta) must embed #ff00ff in model JSON"

    def test_mspline_lcolor_in_html(self):
        html = self._html("mspline", {"yvar": "y", "xvar": "x"}, "lcolor")
        assert self._HEX in html, "mspline lcolor(magenta) must embed #ff00ff in model JSON"

    def test_function_lcolor_in_html(self):
        html = self._html("function",
                          {"expr": "x", "range": [0, 10]}, "lcolor")
        assert self._HEX in html, "function lcolor(magenta) must embed #ff00ff in model JSON"

    def test_dropline_lcolor_in_html(self):
        html = self._html("dropline", {"yvar": "y", "xvar": "x"}, "lcolor")
        assert self._HEX in html, "dropline lcolor(magenta) must embed #ff00ff in model JSON"

    def test_pcspike_lcolor_in_html(self):
        base = {
            "y": [1.0, 2.0, 3.0], "x": [1.0, 2.0, 3.0],
            "lo": [0.5, 1.0, 1.5], "hi": [1.5, 3.0, 4.5],
        }
        data = _make_data_json(base)
        spec, _ = _single_graph_spec("pcspike", {
            "y1var": "y", "x1var": "x", "y2var": "hi", "x2var": "lo"
        }, options={"lcolor": "magenta"})
        html = _render_to_html(spec, data)
        assert self._HEX in html, "pcspike lcolor(magenta) must embed #ff00ff in model JSON"

    # --- scatter-type plot types (mcolor) ---

    def test_connected_mcolor_in_html(self):
        html = self._html("connected", {"yvar": "y", "xvar": "x"}, "mcolor")
        assert self._HEX in html, "connected mcolor(magenta) must embed #ff00ff in model JSON"

    def test_dot_mcolor_in_html(self):
        html = self._html("dot", {"yvar": "y", "xvar": "x"}, "mcolor")
        assert self._HEX in html, "dot mcolor(magenta) must embed #ff00ff in model JSON"

    def test_rcapsym_mcolor_in_html(self):
        html = self._html("rcapsym",
                          {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}, "mcolor")
        assert self._HEX in html, "rcapsym mcolor(magenta) must embed #ff00ff in model JSON"

    def test_rconnected_mcolor_in_html(self):
        html = self._html("rconnected",
                          {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}, "mcolor")
        assert self._HEX in html, "rconnected mcolor(magenta) must embed #ff00ff in model JSON"

    def test_scatteri_mcolor_in_html(self):
        html = self._html("scatteri",
                          {"values": [[1.0, 2.0], [3.0, 4.0]]}, "mcolor")
        assert self._HEX in html, "scatteri mcolor(magenta) must embed #ff00ff in model JSON"

    # --- fill-type plot types (fcolor) ---

    def test_rbar_fcolor_in_html(self):
        html = self._html("rbar",
                          {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}, "fcolor")
        # Filled at rbar's intensity, inten80 (WP-30 P1.2b; twoway's SVG, plan section 16 Evidence E3).
        assert "#ff33ff" in html, "rbar fcolor(magenta) must embed #ff33ff in model JSON"

    def test_histogram_fcolor_in_html(self):
        html = self._html("histogram", {"var": "y"}, "fcolor")
        assert self._HEX in html, "histogram fcolor(magenta) must embed #ff00ff in model JSON"

    def test_lfitci_fcolor_in_html(self):
        html = self._html("lfitci", {"yvar": "y", "xvar": "x"}, "fcolor")
        assert self._HEX in html, "lfitci fcolor(magenta) must embed #ff00ff in model JSON"

    def test_qfitci_fcolor_in_html(self):
        html = self._html("qfitci", {"yvar": "y", "xvar": "x"}, "fcolor")
        assert self._HEX in html, "qfitci fcolor(magenta) must embed #ff00ff in model JSON"

    def test_rarea_fcolor_in_html(self):
        html = self._html("rarea",
                          {"yvar1": "lo", "yvar2": "hi", "xvar": "x"}, "fcolor")
        # Filled at rarea's intensity, inten80 (WP-30 P1.2b; twoway's SVG, plan section 16 Evidence E3).
        assert "#ff33ff" in html, "rarea fcolor(magenta) must embed #ff33ff in model JSON"


# ================================================================
# Adversarial tests — injection, resource exhaustion (CLAUDE.md rule 18)
# ================================================================
class TestAdversarialPlotOptions:
    """Security-focused adversarial tests for plot-level option inputs."""

    # The four below checked that something was drawn, and not the fallback
    # or the cap each names, so a refusal that drew any other colour or
    # marker, and a raised cap, passed.  Each refusal is also named.

    def test_injection_in_mcolor_produces_valid_html(self):
        """Injection attempt in mcolor is rejected; render uses default color."""
        spec, data = _single_graph_spec(
            "scatter", {"yvar": "y", "xvar": "x"},
            options={"mcolor": "'; import os; os.system('id')"},
        )
        with pytest.warns(UserWarning, match=re.escape(
                "mcolor('; import os; os.system('id')) is not a recognised "
                "colour; using the scheme's default")):
            html = _render_to_html(spec, data)
        # The scheme's first series colour, fill and outline.
        pts = _only_layer(html, "Scatter")
        assert _values(pts, "fill_color") == _values(pts, "line_color") \
            == ["#1a476f"] * 20
        # Injected string must NOT appear literally in output HTML
        assert "os.system" not in html

    def test_injection_in_lcolor_produces_valid_html(self):
        """Injection attempt in lcolor is rejected; render uses default color."""
        spec, data = _single_graph_spec(
            "line", {"yvar": "y", "xvar": "x"},
            options={"lcolor": "__import__('os').system('id')"},
        )
        with pytest.warns(UserWarning, match=re.escape(
                "lcolor(__import__('os').system('id')) is not a recognised "
                "colour; using the scheme's default")):
            html = _render_to_html(spec, data)
        assert _values(_only_layer(html, "Line"), "line_color") \
            == ["#1a476f"] * 20

    def test_invalid_msymbol_falls_back_to_default(self):
        """Invalid msymbol value falls back to default circle marker."""
        spec, data = _single_graph_spec(
            "scatter", {"yvar": "y", "xvar": "x"},
            options={"msymbol": "'; import os'"},
        )
        with pytest.warns(UserWarning, match=re.escape(
                "msymbol('; import os') is not a recognised marker symbol; "
                "using the scheme's default")):
            html = _render_to_html(spec, data)
        # The document leaves the marker out at Bokeh's default, a circle.
        assert _values(_only_layer(html, "Scatter"), "marker",
                       bkm.Scatter().marker) == ["circle"] * 20

    def test_huge_histogram_bin_count_is_bounded(self):
        """Extremely large bin count is capped to prevent resource exhaustion."""
        spec, data = _single_graph_spec("histogram", {"var": "y"},
                                        options={"bin": "99999999"})
        with pytest.warns(UserWarning, match=re.escape(
                "histogram bin count 99999999 exceeds the 1000 limit; "
                "using 1000 bins")):
            html = _render_to_html(spec, data)
        # The renderer's cap, 1000 bins (_histogram_grid's _MAX_BINS).
        assert _only_layer(html, "Quad")["rows"] == 1000, \
            "Histogram must render its large bin count capped at 1000"

    def test_extreme_msize_does_not_crash(self):
        """Extremely large msize value must not crash the renderer."""
        spec, data = _single_graph_spec(
            "scatter", {"yvar": "y", "xvar": "x"},
            options={"msize": "999999"},
        )
        html = _render_to_html(spec, data)
        assert len(html) > 500, "Render must succeed with extreme msize"
        assert "Scatter" in _drawn_glyphs(html)

    def test_extreme_lwidth_does_not_crash(self):
        """Extremely large lwidth value must not crash the renderer."""
        spec, data = _single_graph_spec(
            "line", {"yvar": "y", "xvar": "x"},
            options={"lwidth": "999999"},
        )
        html = _render_to_html(spec, data)
        assert len(html) > 500, "Render must succeed with extreme lwidth"
        assert "Line" in _drawn_glyphs(html)

    def test_unicode_in_title_does_not_crash(self):
        """Unicode characters in title option must not crash the renderer."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["title"] = "Ünïcödé tïtlé: 中文 日本語 한국어"
        html = _render_to_html(spec, data)
        # Drawn, and drawn as written: len(html) > 500 could not fail.
        assert _figure_titles(html) \
            == [spec["graphs"][0]["graph_options"]["title"]], \
            "Render must draw the unicode title as given"
        assert _figure_glyphs(html) == [["Scatter"]]

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
        # The note is a Title -- canvas text -- and live markup nowhere.
        # Flipped (WP-30 P1.2a): "Label" was wrong because twoway places
        # note() by the scheme's clock, which S15 draws as a side-panel Title.
        _assert_drawn_as_text(html, "<script>alert('xss')</script>", "Title")


# ================================================================
# HTML model data-content tests — verify actual Bokeh JSON model
# data payload (coordinates, colors) not just structure
# ================================================================

class TestHtmlModelDataContent:
    """Verify the Bokeh model JSON in rendered HTML contains actual plot data."""

    #: y is not x here, so a scatter drawn with the two swapped is seen.
    _X = [float(i) for i in range(1, 21)]
    _Y = [float(100 + i) for i in range(1, 21)]

    def _points(self):
        """The one layer a scatter of _Y on _X draws, read from the
        document.  "1.0" and "20.0" were looked for in the page text,
        where BokehJS carries each (37 and 14 copies, measured 24sep2026),
        so a scatter whose source held no rows at all passed."""
        spec, _ = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        return _only_layer(_render_to_html(spec, _make_data_json(
            {"y": self._Y, "x": self._X})), "Scatter")

    def test_scatter_html_contains_x_data(self):
        """Scatter HTML embeds x-axis data values in the Bokeh JSON model."""
        assert _values(self._points(), "x") == self._X

    def test_scatter_html_contains_y_data(self):
        """Scatter HTML embeds y-axis data values in the Bokeh JSON model."""
        assert _values(self._points(), "y") == self._Y

    def test_mcolor_hex_in_html(self):
        """mcolor(red) produces #ff0000 hex in the Bokeh model JSON."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"},
                                        options={"mcolor": "red"})
        html = _render_to_html(spec, data)
        assert "#ff0000" in html.lower() or "ff0000" in html.lower(), \
            "mcolor(red) must produce #ff0000 in HTML"

    def test_lcolor_hex_in_html(self):
        """lcolor(magenta) produces #ff00ff hex in the Bokeh model JSON (it
        was navy, the default, which passed with the option ignored)."""
        spec, data = _single_graph_spec("line", {"yvar": "y", "xvar": "x"},
                                        options={"lcolor": "magenta"})
        html = _render_to_html(spec, data)
        assert "#ff00ff" in html.lower(), \
            "lcolor(magenta) must produce #ff00ff in HTML"

    def test_histogram_quad_data_embedded(self):
        """Histogram HTML embeds top/left/right arrays for the Quad glyph."""
        spec, data = _single_graph_spec("histogram", {"var": "y"})
        html = _render_to_html(spec, data)
        assert "Quad" in _drawn_glyphs(html), \
            "histogram must embed Quad glyph type in HTML model"

    def test_line_glyph_type_in_json(self):
        """Line plot HTML contains 'Line' glyph type in model JSON."""
        spec, data = _single_graph_spec("line", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "Line" in _drawn_glyphs(html), \
            "line plot must embed Line glyph in HTML model"

    def test_varea_glyph_type_in_json(self):
        """rarea plot HTML contains VArea glyph type in model JSON."""
        spec, data = _single_graph_spec(
            "rarea", extra_keys={"yvar1": "lo", "yvar2": "hi", "xvar": "x"}
        )
        html = _render_to_html(spec, data)
        assert "VArea" in _drawn_glyphs(html), \
            "rarea plot must embed VArea glyph in HTML model"

    def test_segment_glyph_for_spike(self):
        """spike plot HTML contains Segment glyph type in model JSON."""
        spec, data = _single_graph_spec("spike", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        assert "Segment" in _drawn_glyphs(html), \
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
        """bgcolor(navy) must translate to #1a476f -- on the figure border.

        This looked for #1a476f anywhere in the page.  Navy is s2color's
        first series colour, so the markers alone passed it whatever the
        background was (measured 24sep2026: six copies with no bgcolor() at
        all).  The property is read now, and the control is that the
        border is not navy without the option.
        """
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        before = _figure_colors(_render_to_html(spec, data),
                                "border_fill_color")
        spec["graphs"][0]["graph_options"]["bgcolor"] = "navy"
        html = _render_to_html(spec, data)
        assert _figure_colors(html, "border_fill_color") == ["#1a476f"], \
            "bgcolor(navy) must set the figure's border_fill_color to #1a476f"
        assert before != ["#1a476f"], before

    def test_plotbgcolor_named_color_translates(self):
        """plotbgcolor(ltblue) must translate and appear in HTML.

        This checked only that a Scatter was drawn, so it passed with the
        colour ignored.  Stata's color-ltblue.style sets rgb "173 216 230"
        (read 24sep2026), and the plot region must be that colour -- which
        it is not without the option.
        """
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        before = _figure_colors(_render_to_html(spec, data),
                                "background_fill_color")
        spec["graphs"][0]["graph_options"]["plotbgcolor"] = "ltblue"
        html = _render_to_html(spec, data)
        assert _figure_colors(html, "background_fill_color") == ["#add8e6"], \
            "plotbgcolor(ltblue) must set background_fill_color #add8e6"
        assert before != ["#add8e6"], before
        assert _figure_glyphs(html) == [["Scatter"]]

    def test_bgcolor_invalid_no_crash(self):
        """bgcolor with invalid value must not crash — renders normally."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["bgcolor"] = "not_a_color_xyz"
        html = _render_to_html(spec, data)
        assert "Scatter" in _drawn_glyphs(html), \
            "invalid bgcolor must fall back gracefully"


# ================================================================
# xrange / yrange axis limit tests
# ================================================================

class TestXrangeYrange:
    """xrange() and yrange() options must set axis limits on the figure."""

    def test_xrange_embeds_unique_start_value(self):
        """xrange(-37 99) must embed -37.0 in model JSON (unique sentinel not in data)."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        # xscale(range()) is Stata's spelling.  The graph_options key
        # "xrange" was a DEAD read -- dash.ado has never emitted it -- and a
        # dead read is what made the axis range look implemented.
        spec["graphs"][0]["graph_options"]["xscale"] = "range(-37 99)"
        html = _render_to_html(spec, data)
        # The x axis's own range, read from the document, and the y axis
        # left to the data.  "-37" was looked for in the page text: it
        # passed with the range drawn on the y axis instead, and a page
        # carries "-37" whenever one of its UUIDs has a group beginning 37
        # -- 12 of 500 pages drawn with no range at all (measured 24sep2026).
        # WP-28 B2: range() widens to include -37 and 99 and never narrows;
        # the Range1d is that hull padded 5% a side (this pinned exactly
        # (-37, 99)).
        got = [(name, attrs.get("start", bkm.Range1d().start),
                attrs.get("end"))
               for name, attrs in _figure_models(html, "x_range")]
        assert [g[0] for g in got] == ["Range1d"]
        start, end = float(got[0][1]), float(got[0][2])
        assert start < -37.0 and end > 99.0
        assert dash_render._dash_range_hull(bkm.Range1d(start=start, end=end)) \
            == pytest.approx((-37.0, 99.0))
        assert [name for name, _a in _figure_models(html, "y_range")] \
            == ["DataRange1d"]

    def test_yrange_embeds_unique_end_value(self):
        """yrange(0 9999) must embed 9999 in model JSON (unique sentinel not in data)."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["yscale"] = "range(0 9999)"
        html = _render_to_html(spec, data)
        # Read from the document: "9999" is in the page's BokehJS (8
        # copies, measured 24sep2026), so the page text passed with the
        # range ignored.  The document leaves out a start of 0, Bokeh's
        # own default for Range1d.start.
        # WP-28 B2: the hull of 0, 9999 and the data, padded 5% a side
        # (this pinned exactly (0, 9999)); the padded start is never 0,
        # so the document writes it.
        got = [(name, attrs.get("start", bkm.Range1d().start),
                attrs.get("end"))
               for name, attrs in _figure_models(html, "y_range")]
        assert [g[0] for g in got] == ["Range1d"]
        start, end = float(got[0][1]), float(got[0][2])
        assert start < 0.0 and end > 9999.0
        assert dash_render._dash_range_hull(bkm.Range1d(start=start, end=end)) \
            == pytest.approx((0.0, 9999.0))
        assert [name for name, _a in _figure_models(html, "x_range")] \
            == ["DataRange1d"]

    def test_xrange_invalid_ignores_gracefully(self):
        """xrange with non-numeric values must not crash -- renders normally.

        This set the graph option "xrange", which nothing reads (the dead
        key above), so no change to the renderer could fail it.  The range
        is xscale(range()): one that is not numbers leaves the axis on the
        data, and the scatter drawn.
        """
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["xscale"] = "range(bad_value)"
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            html = _render_to_html(spec, data)
        assert [name for name, _a in _figure_models(html, "x_range")] \
            == ["DataRange1d"]
        # Named once (WP-28 B2): an unhonoured value is named, Q22.
        assert [str(w.message) for w in caught
                if "range()" in str(w.message)] == [
            "dash: xscale(range()) ignores bad_value, which is not a number"]
        assert _figure_glyphs(html) == [["Scatter"]]

    def test_yrange_invalid_ignores_gracefully(self):
        """yrange with non-numeric values must not crash.

        As above: "yrange" is a key nothing reads, and len(html) > 500
        could not fail on a page that inlines BokehJS.
        """
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["yscale"] = "range(bad)"
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            html = _render_to_html(spec, data)
        assert [name for name, _a in _figure_models(html, "y_range")] \
            == ["DataRange1d"]
        assert [str(w.message) for w in caught
                if "range()" in str(w.message)] == [
            "dash: yscale(range()) ignores bad, which is not a number"]
        assert _figure_glyphs(html) == [["Scatter"]]


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
        # The figure's own scales, read from the document: "LogScale" and
        # "log" are in the page's BokehJS whatever the axes are.
        scales = [(f["x_scale"]["name"], f["y_scale"]["name"])
                  for f in _page_models(html)["Figure"]]
        assert scales == [("LogScale", "LinearScale")], \
            "xscale(log) must produce log axis marker in HTML model JSON"

    def test_yscale_log_html_contains_log_type(self):
        """yscale(log) must embed LogScale marker in Bokeh JSON."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["yscale"] = "log"
        html = _render_to_html(spec, data)
        scales = [(f["x_scale"]["name"], f["y_scale"]["name"])
                  for f in _page_models(html)["Figure"]]
        assert scales == [("LinearScale", "LogScale")], \
            "yscale(log) must produce log axis marker in HTML model JSON"

    def test_no_log_scale_by_default(self):
        """Without xscale/yscale, HTML must NOT contain LogScale in model JSON."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        # The page's BokehJS defines "LogScale", so the page text cannot
        # say; this read the document block as a string, and a page with no
        # block read as "" and passed.  The figure's own scales, from the
        # parsed document, and no LogScale model anywhere in it...
        models = _page_models(html)
        assert [(f["x_scale"]["name"], f["y_scale"]["name"])
                for f in models["Figure"]] == [("LinearScale", "LinearScale")]
        assert "LogScale" not in models, \
            "default figure must not have LogScale in Bokeh model JSON"
        # ...by a reader that finds one where one is drawn.
        spec["graphs"][0]["graph_options"]["xscale"] = "log"
        assert len(_page_models(_render_to_html(spec, data))
                   .get("LogScale", [])) == 1


# ================================================================
# Backend selection and visual rendering confirmation tests
# ================================================================

def _large_scatter_spec() -> tuple:
    """A scatter of 10 001 rows, one past _WEBGL_THRESHOLD, which the
    renderer draws with WebGL."""
    n = 10_001
    data_json = _make_data_json({
        "y": [float(i % 100) for i in range(n)],
        "x": [float(i) for i in range(n)],
    })
    spec, _ = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
    return spec, data_json


def _figure_backends(html: str) -> list:
    """Each figure's output_backend as the document writes it; None where
    it writes none, which Bokeh does at its default, "canvas"."""
    return [f.get("output_backend") for f in _page_models(html)["Figure"]]


class TestOutputBackendAndVisualMarkers:
    """Verify the correct Bokeh output backend is embedded in the model JSON,
    and that actual rendering-relevant attributes are present.

    Every check here was a page-text search that could not fail: the
    page's BokehJS spells "output_backend" and '"top"', and every
    document's toolbar spells '"renderers"', '"fill_color"', '"line_color"'
    and '"fill_alpha"' (measured 24sep2026 on a page drawing nothing).  The
    figure and its glyphs are read from the parsed document instead.
    """

    def test_canvas_backend_omits_output_backend_key(self):
        """Bokeh omits output_backend from JSON for the default canvas backend.
        Small datasets must render with canvas (default) — verified by absence
        of output_backend key and presence of renderers in model JSON."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        # The figure writes no output_backend -- the key Bokeh leaves out at
        # its default, canvas -- and draws its scatter.  This searched the
        # document block as a string: a page with no block read as "" and
        # passed.
        assert ["output_backend" in f for f in _page_models(html)["Figure"]] \
            == [False]
        assert bkm.Plot().output_backend == "canvas"
        assert _figure_glyphs(html) == [["Scatter"]]
        # The reader sees the key where it is written: 10 001 rows.
        assert _figure_backends(_render_to_html(*_large_scatter_spec())) \
            == ["webgl"]

    def test_model_json_contains_glyph_renderers_key(self):
        """Bokeh model JSON must contain 'renderers' key showing glyph renderers list."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        # The figure's renderers: one GlyphRenderer, drawing the scatter.
        assert _figure_glyphs(html) == [["Scatter"]], \
            "Bokeh model JSON must contain 'renderers' array for glyph renderer list"

    def test_scatter_model_has_glyph_fill_color(self):
        """Scatter model JSON must embed fill_color attribute for the Scatter glyph."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"},
                                        options={"mcolor": "red"})
        html = _render_to_html(spec, data)
        # The markers' own fill, not "ff0000" anywhere: red on the outline
        # alone passed that.
        assert _values(_only_layer(html, "Scatter"), "fill_color") \
            == ["#ff0000"] * 20, "Scatter glyph fill_color must be #ff0000"

    def test_line_model_has_line_color_attribute(self):
        """Line model JSON must embed line_color attribute."""
        spec, data = _single_graph_spec("line", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        # The line's own colour: s2color's first series colour, navy
        # (Stata's color-navy.style, rgb "26 71 111").
        assert _values(_only_layer(html, "Line"), "line_color") \
            == ["#1a476f"] * 20, "Line glyph line_color must be the scheme's"

    def test_histogram_model_has_fill_and_top(self):
        """Histogram model JSON must embed both fill_color and data arrays."""
        spec, data = _single_graph_spec("histogram", {"var": "y"})
        html = _render_to_html(spec, data)
        bars = _only_layer(html, "Quad")
        # y is 1..20.  Stata's default bin count, min(sqrt(N), 10*log10(N))
        # truncated (dash_render.py _stata_bin_count, checked against Stata
        # there), is 4, and its default height is the density: numpy's
        # histogram of the same four bins.  '"top"' was looked for in the
        # page text, where BokehJS spells it 67 times.
        dens, edges = np.histogram(np.arange(1.0, 21.0), bins=4, density=True)
        assert _values(bars, "top") == pytest.approx(dens.tolist())
        assert _values(bars, "left") == pytest.approx(edges[:-1].tolist())
        assert _values(bars, "right") == pytest.approx(edges[1:].tolist())
        assert _values(bars, "fill_color") == ["#1a476f"] * 4

    def test_all_plot_types_produce_renderers_in_json(self):
        """Every basic plot type must produce a non-empty 'renderers' array in model JSON."""
        types_and_keys = [
            ("scatter", {"yvar": "y", "xvar": "x"}, "Scatter"),
            ("line",    {"yvar": "y", "xvar": "x"}, "Line"),
            ("bar",     {"yvar": "y", "xvar": "x"}, "VBar"),
            ("spike",   {"yvar": "y", "xvar": "x"}, "Segment"),
            ("area",    {"yvar": "y", "xvar": "x"}, "VArea"),
        ]
        for ptype, keys, glyph in types_and_keys:
            spec, data = _single_graph_spec(ptype, keys)
            drawn = [[(layer["glyph"], layer["rows"]) for layer in fig]
                     for fig in _figure_layers(_render_to_html(spec, data))]
            assert drawn == [[(glyph, 20)]], (ptype, drawn)

    def test_rarea_varea_glyph_has_fill_attributes(self):
        """rarea VArea glyph model must have fill_color and fill_alpha attributes."""
        spec, data = _single_graph_spec(
            "rarea", extra_keys={"yvar1": "lo", "yvar2": "hi", "xvar": "x"}
        )
        html = _render_to_html(spec, data)
        band = _only_layer(html, "VArea")
        # The band's own fill: the scheme's first series colour at its
        # p1area intensity, #486c8c (WP-30 P1.2b; twoway's SVG, plan section 16 Evidence E3), at the 0.5 alpha map_rarea gives
        # it (section 24's; the renderer's value, pinned here).
        assert _values(band, "fill_color") == ["#486c8c"] * 20
        assert _values(band, "fill_alpha") == [0.5] * 20


class TestWebglBackendLargeData:
    """For datasets > 10 000 rows, output_backend must be set to 'webgl' in model JSON."""

    def _large_data_spec(self):
        """Build a scatter spec with 10 001 rows to trigger webgl threshold."""
        return _large_scatter_spec()

    def test_large_dataset_uses_webgl_backend(self):
        """Datasets > 10 000 rows must embed output_backend='webgl' in model JSON."""
        spec, data = self._large_data_spec()
        html = _render_to_html(spec, data)
        # The figure's own backend.  "webgl" in the page text could not
        # fail: the page's BokehJS spells it 56 times (measured 24sep2026).
        assert _figure_backends(html) == ["webgl"], \
            "Large dataset (>10 000 rows) must set output_backend='webgl' in Bokeh model JSON"

    def test_small_dataset_does_not_use_webgl(self):
        """Datasets <= 10 000 rows must NOT embed output_backend='webgl'."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        # Nothing in the parsed document asks for webgl.  This searched the
        # block as a string, and a page with no block read as "" and passed.
        assert _figure_backends(html) == [None]
        assert _text_homes(html, "webgl") == [], \
            "Small dataset must not use webgl backend in Bokeh model JSON"
        # The reader finds it where it is written, on the figure alone.
        big = _render_to_html(*self._large_data_spec())
        assert _text_homes(big, "webgl") \
            == [("Figure", "output_backend", "webgl")]

    def test_webgl_model_still_has_renderers(self):
        """webgl-backend model must still contain renderers in the JSON."""
        spec, data = self._large_data_spec()
        html = _render_to_html(spec, data)
        # The figure draws its scatter, every row.  '"renderers"' is in
        # every document's toolbar, drawn or not.
        drawn = [[(layer["glyph"], layer["rows"]) for layer in fig]
                 for fig in _figure_layers(html)]
        assert drawn == [[("Scatter", 10_001)]], \
            "webgl-backend model must still draw its renderers"


class TestBokehJsBundleInHtml:
    """Verify the Bokeh JavaScript bundle is referenced in rendered HTML.

    "bokeh" and "<script" were looked for in the page text, where the
    page's own embed script spells both: a page that fetched BokehJS from
    Bokeh's CDN passed (measured 24sep2026) -- a script the page's own
    Content-Security-Policy does not allow: it names the page's own
    scripts by hash and no source (WP-30 P1.29), so a CDN script is not
    allowed.  And 'application/json' is a string BokehJS itself
    carries.
    """

    def test_html_contains_bokeh_script_reference(self):
        """Rendered HTML must include a reference to the Bokeh JS library."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        # BokehJS inlined whole, once, and no script fetched from elsewhere.
        assert len(_inlined_bokehjs(html)) == 1, \
            "HTML must inline the Bokeh JS library in a <script> tag"
        assert [attrs for attrs, _b in _page_scripts(html) if "src=" in attrs] \
            == []

    def test_html_contains_bokeh_json_model_block(self):
        """Rendered HTML must contain the application/json model block with Bokeh objects."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        html = _render_to_html(spec, data)
        # One block, holding one document of this bokeh; the page's root
        # element names that document's root, the embed script reads the
        # block by its id, and the document draws the scatter.
        blocks = re.findall(r'<script type="application/json" id="([^"]+)"',
                            html)
        assert len(blocks) == 1, blocks
        (body,) = json.loads(_unescape(_extract_model_json(html))).values()
        assert body["version"] == bokeh.__version__
        roots = [root["id"] for root in body["roots"]]
        assert re.findall(r'<div id="[^"]+" data-root-id="([^"]+)"', html) \
            == roots
        assert "document.getElementById('%s').textContent" % blocks[0] in html
        assert _figure_glyphs(html) == [["Scatter"]]

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
            assert len(_inlined_bokehjs(html)) == 1, \
                f"{ptype}: HTML must include Bokeh JS bundle"
            assert [a for a, _b in _page_scripts(html) if "src=" in a] == [], \
                ptype


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
        # Both outlines read from their pages' Scatter.  This built the
        # default page and never read it: it asserted '"line_color"', which
        # every document's toolbar spells, and red somewhere in the page.
        mfc = _only_layer(html_mfc, "Scatter")
        assert _values(mfc, "fill_color") == ["#ff0000"] * 20, \
            "mfcolor must appear as fill_color"
        assert _values(mfc, "line_color") \
            == _values(_only_layer(html_def, "Scatter"), "line_color") \
            == ["#1a476f"] * 20, "mfcolor must leave the outline alone"

    def test_bar_base_nonzero_in_html(self):
        """bar with base(10) must have bottom!=0 reflected in Bokeh model JSON."""
        spec, data = _single_graph_spec(
            "bar",
            extra_keys={"yvar": "y", "xvar": "x"},
            options={"base": "10"},
        )
        html = _render_to_html(spec, data)
        # The bars' own bottom.  "10" in the page text could not fail: the
        # page carries it hundreds of times (measured 24sep2026).
        assert _values(_only_layer(html, "VBar"), "bottom") == [10.0] * 20, \
            "bar base(10) must set the bars' bottom to 10"

    def test_bar_default_base_zero(self):
        """bar without base option must have bottom=0 in Bokeh model JSON."""
        spec, data = _single_graph_spec(
            "bar",
            extra_keys={"yvar": "y", "xvar": "x"},
            options={},
        )
        html = _render_to_html(spec, data)
        # The document leaves bottom out at Bokeh's own default, 0.  The
        # word "bottom" is in the page's BokehJS 587 times.
        assert _values(_only_layer(html, "VBar"), "bottom",
                       bkm.VBar().bottom) == [0] * 20, \
            "bar must stand on 0 without base()"

    def test_spike_base_nonzero_in_html(self):
        """spike with base(5) must have y0 values != 0 in model JSON."""
        spec, data = _single_graph_spec(
            "spike",
            extra_keys={"yvar": "y", "xvar": "x"},
            options={"base": "5"},
        )
        html = _render_to_html(spec, data)
        # Every spike runs from 5 to its y: the Segment's y0 and y1.  "5.0"
        # and '"y0"' are both in the page's BokehJS.
        spikes = _only_layer(html, "Segment")
        assert _values(spikes, "y0") == [5.0] * 20, \
            "spike base(5) must start every spike at 5"
        assert _values(spikes, "y1") == [float(i) for i in range(1, 21)]

    def test_area_base_nonzero_in_html(self):
        """area with base(3) must have lower boundary = 3 in model JSON."""
        spec, data = _single_graph_spec(
            "area",
            extra_keys={"yvar": "y", "xvar": "x"},
            options={"base": "3"},
        )
        html = _render_to_html(spec, data)
        # The area's lower edge is 3 all along: the VArea's y1.  "3.0" and
        # '"y1"' are both in the page's BokehJS.
        band = _only_layer(html, "VArea")
        assert _values(band, "y1") == [3.0] * 20, \
            "area base(3) must put the lower boundary at 3"
        assert _values(band, "y2") == [float(i) for i in range(1, 21)]

    def test_bfcolor_bar_fill_in_html(self):
        """bar with bfcolor(red) embeds red at the bar's intensity, #ff3333,
        as fill_color in Bokeh JSON (WP-30 P1.2b; twoway's SVG, plan section 16 Evidence E3)."""
        spec, data = _single_graph_spec(
            "bar",
            extra_keys={"yvar": "y", "xvar": "x"},
            options={"bfcolor": "red"},
        )
        html = _render_to_html(spec, data)
        assert "#ff3333" in html, \
            "bfcolor(red) must embed #ff3333 as fill_color in bar glyph model"

    def test_blcolor_bar_line_in_html(self):
        """bar with blcolor(magenta) must embed #ff00ff as line_color in
        Bokeh JSON (it was navy, the default, which passed with the option
        ignored)."""
        spec, data = _single_graph_spec(
            "bar",
            extra_keys={"yvar": "y", "xvar": "x"},
            options={"blcolor": "magenta"},
        )
        html = _render_to_html(spec, data)
        assert "#ff00ff" in html, \
            "blcolor(magenta) must embed #ff00ff as line_color in bar glyph model"


class TestLineWidthPatternHtml:
    """lwidth and lpattern options must appear in the Bokeh model JSON in rendered HTML.

    Each looked in the page text, where nothing could fail: every
    document's toolbar overlays spell '"line_width"' and '"line_dash"'
    (a dashed box-zoom outline), and the page's BokehJS carries "2.5" 31
    times and "3.5" 35 times (measured 24sep2026).  The glyph's own
    width and dash are read from the document.  The widths and the dash
    pattern are dash's translations, pinned.
    """

    def test_lwidth_thick_in_line_html(self):
        """line with lwidth(thick) must have line_width > default in Bokeh JSON."""
        spec, data = _single_graph_spec(
            "line",
            extra_keys={"yvar": "y", "xvar": "x"},
            options={"lwidth": "thick"},
        )
        html = _render_to_html(spec, data)
        # thick is .8 Stata units, 3.072 px, where the scheme draws the same
        # line at medium, 1.152 px (WP-30 P1.12b; dash's private ladder had
        # 2.5 and 1.5).
        assert _values(_only_layer(html, "Line"), "line_width") \
            == pytest.approx([3.072] * 20), "lwidth(thick) must be the line's width"
        spec["graphs"][0]["plots"][0]["options"] = {}
        assert _values(_only_layer(_render_to_html(spec, data), "Line"),
                       "line_width") == pytest.approx([1.152] * 20)

    def test_lpattern_dash_in_line_html(self):
        """line with lpattern(dash) must have line_dash in Bokeh model JSON."""
        spec, data = _single_graph_spec(
            "line",
            extra_keys={"yvar": "y", "xvar": "x"},
            options={"lpattern": "dash"},
        )
        html = _render_to_html(spec, data)
        assert _values(_only_layer(html, "Line"), "line_dash",
                       bkm.Line().line_dash) == [[8, 4]] * 20, \
            "lpattern(dash) must dash the line"

    def test_lwidth_applied_to_spike(self):
        """spike with lwidth(vthick) must embed line_width=5.376 in Bokeh JSON
        (1.4 Stata units; 3.5 on dash's private ladder, WP-30 P1.12b)."""
        spec, data = _single_graph_spec(
            "spike",
            extra_keys={"yvar": "y", "xvar": "x"},
            options={"lwidth": "vthick"},
        )
        html = _render_to_html(spec, data)
        assert _values(_only_layer(html, "Segment"), "line_width") \
            == pytest.approx([5.376] * 20), "lwidth(vthick) must be the spikes' width"

    def test_lwidth_applied_to_bar(self):
        """bar with lwidth(thick) must embed line_width=3.072 in Bokeh JSON
        (WP-30 P1.12b; 2.5 on dash's private ladder)."""
        spec, data = _single_graph_spec(
            "bar",
            extra_keys={"yvar": "y", "xvar": "x"},
            options={"lwidth": "thick"},
        )
        html = _render_to_html(spec, data)
        assert _values(_only_layer(html, "VBar"), "line_width") \
            == pytest.approx([3.072] * 20), "lwidth(thick) must be the bars' outline width"

    def test_lwidth_applied_to_histogram(self):
        """histogram with lwidth(thick) must embed line_width=3.072 in Bokeh
        JSON (WP-30 P1.12b; 2.5 on dash's private ladder)."""
        spec, data = _single_graph_spec(
            "histogram",
            extra_keys={"yvar": "y"},
            options={"lwidth": "thick"},
        )
        html = _render_to_html(spec, data)
        assert _values(_only_layer(html, "Quad"), "line_width") \
            == pytest.approx([3.072] * 4), "lwidth(thick) must be the bins' outline width"

    def test_lpattern_applied_to_histogram(self):
        """histogram with lpattern(dash) must have line_dash in Bokeh JSON."""
        spec, data = _single_graph_spec(
            "histogram",
            extra_keys={"yvar": "y"},
            options={"lpattern": "dash"},
        )
        html = _render_to_html(spec, data)
        assert _values(_only_layer(html, "Quad"), "line_dash",
                       bkm.Quad().line_dash) == [[8, 4]] * 4, \
            "lpattern(dash) must dash the bins' outlines"


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
        # Read from the document: "Span" is a word the page's BokehJS
        # carries whatever the figure holds.  A vertical line spans the
        # height, at x = 5 (a Span left at Bokeh's default is "width").
        spans = [(s.get("dimension", "width"), s.get("location"))
                 for s in _page_models(html).get("Span", [])]
        assert spans == [("height", 5.0)], \
            "xline must produce a Bokeh Span annotation in the HTML model"

    def test_yline_produces_span_in_html(self):
        """yline(10) must add a horizontal Span to the standalone HTML model."""
        spec, data = _single_graph_spec(
            "scatter",
            extra_keys={"yvar": "y", "xvar": "x"},
        )
        spec["graphs"][0]["graph_options"]["yline"] = "10"
        html = _render_to_html(spec, data)
        spans = [(s.get("dimension", "width"), s.get("location"))
                 for s in _page_models(html).get("Span", [])]
        assert spans == [("width", 10.0)], \
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
        # Counted in the document: the page's BokehJS names "Span" many
        # times over whatever the figure holds.
        spans = sorted((s.get("dimension", "width"), s.get("location"))
                       for s in _page_models(html).get("Span", []))
        assert spans == [("height", 5.0), ("width", 10.0)], \
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
        # One panel for each of grp's two groups, a Scatter drawn in each,
        # read from the document.  The page's BokehJS spells '"scatter"'
        # twice itself, so counting it in the page text passed ">= 2" on a
        # page with no scatter at all (measured 24sep2026).
        panels = _figure_glyphs(html)
        assert panels == [["Scatter"], ["Scatter"]], (
            f"Expected a Scatter in each of 2 panels, got {panels}"
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
        # A third panel, titled Total, drawing all twenty rows after each
        # group's ten -- read from the document.  "Total" in the page text
        # found the title alone (the one copy on the page, measured
        # 24sep2026), so a Total panel drawing one group's rows passed.
        assert _figure_titles(html) == ["Group A", "Group B", "Total"], \
            "Total facet label not found in HTML"
        layers = _figure_layers(html)
        assert [[(layer["glyph"], layer["rows"]) for layer in fig]
                for fig in layers] \
            == [[("Scatter", 10)], [("Scatter", 10)], [("Scatter", 20)]]
        assert _values(layers[2][0], "x") == [float(i) for i in range(1, 21)]

    def test_by_with_multiple_plot_layers(self):
        """by(grp) with scatter+line → each facet has both glyph types."""
        spec, data = _by_facet_spec("grp")
        # Add a line plot layer
        spec["graphs"][0]["plots"].append(
            {"type": "line", "yvar": "y", "xvar": "x", "options": {}}
        )
        html = _render_to_html(spec, data)
        # Both glyph types in each of grp's two panels, read from the
        # document rather than from page text BokehJS already names them in.
        panels = [sorted(p) for p in _figure_glyphs(html)]
        assert panels == [["Line", "Scatter"], ["Line", "Scatter"]], panels

    # The four below asserted a page length, which a page inlining 1.6 MB
    # of BokehJS passes drawing nothing.  Each now reads the panels it
    # names from the document.

    def test_by_html_non_empty(self):
        """by(grp) → HTML output is non-trivial."""
        spec, data = _by_facet_spec("grp")
        html = _render_to_html(spec, data)
        # Two panels, each drawing its group's ten rows.
        assert [[(layer["glyph"], layer["rows"]) for layer in fig]
                for fig in _figure_layers(html)] \
            == [[("Scatter", 10)], [("Scatter", 10)]]

    def test_by_nonexistent_var_still_renders(self):
        """by(nonexistent) → HTML still renders (falls back to no faceting)."""
        spec, data = _by_facet_spec("nonexistent")
        html = _render_to_html(spec, data)
        # No faceting: one untitled panel drawing all twenty rows.
        assert [[(layer["glyph"], layer["rows"]) for layer in fig]
                for fig in _figure_layers(html)] == [[("Scatter", 20)]], \
            "HTML should still render without faceting"
        assert _figure_titles(html) == [None]

    def test_by_link_renders_valid_html(self):
        """by() + link() in render() → produces valid HTML (no longer raises)."""
        spec, data = _by_facet_spec("grp")
        spec["build_options"]["link"] = "fig1"  # match the graph name
        html = _render_to_html(spec, data)
        # Both panels, each drawing its group.
        assert _figure_titles(html) == ["Group A", "Group B"]
        assert [[(layer["glyph"], layer["rows"]) for layer in fig]
                for fig in _figure_layers(html)] \
            == [[("Scatter", 10)], [("Scatter", 10)]], \
            "by()+link() must draw both panels"

    def test_by_cols_suboption_produces_html(self):
        """by('grp, cols(1)') → renders valid HTML (suboption parsing works)."""
        spec, data = _by_facet_spec("grp")
        # Set by with cols suboption in the raw string
        spec["graphs"][0]["graph_options"]["by"] = "grp, cols(1)"
        html = _render_to_html(spec, data)
        # cols(1) stacks the two panels in one column...
        assert _grid_cells(html) == [("Group A", 0, 0), ("Group B", 1, 0)]
        assert _figure_glyphs(html) == [["Scatter"], ["Scatter"]]
        # ...where by(grp) alone sets them side by side.
        spec["graphs"][0]["graph_options"]["by"] = "grp"
        assert _grid_cells(_render_to_html(spec, data)) \
            == [("Group A", 0, 0), ("Group B", 0, 1)]


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
        """plotregion(color(navy)) must translate to #1a476f -- on the plot
        region.

        This looked for #1a476f anywhere in the page, where s2color's navy
        markers put it with no plotregion() at all (measured 24sep2026), so
        it passed whatever the region colour was.  The property is read
        now, and the control is that the region is not navy without it.
        """
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        before = _figure_colors(_render_to_html(spec, data),
                                "background_fill_color")
        spec["graphs"][0]["graph_options"]["plotregion"] = "color(navy)"
        html = _render_to_html(spec, data)
        assert _figure_colors(html, "background_fill_color") == ["#1a476f"], \
            "plotregion(color(navy)) must set background_fill_color #1a476f"
        assert before != ["#1a476f"], before

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
        assert "Scatter" in _drawn_glyphs(html), "invalid plotregion color must fall back gracefully"

    def test_graphregion_invalid_no_crash(self):
        """graphregion with invalid color must not crash."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["graphs"][0]["graph_options"]["graphregion"] = "color(notacolor)"
        html = _render_to_html(spec, data)
        assert "Scatter" in _drawn_glyphs(html), "invalid graphregion color must fall back gracefully"


# ================================================================
# Bug 13 — Build-level subtitle silently ignored
# ================================================================
class TestBuildSubtitleInHtml:
    """build_options['subtitle'] must appear in rendered HTML.

    full_dashboard.do specifies subtitle("Explore fuel efficiency, pricing, and more")
    which is parsed by dash.ado and stored in build_options["subtitle"], but was
    silently dropped by render() — never extracted or displayed in the HTML.
    """

    def test_build_subtitle_appears_in_html(self):
        """Bug 13: subtitle from build_options must appear in rendered HTML."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["build_options"]["title"] = "My Dashboard"
        spec["build_options"]["subtitle"] = "Explore the data"
        html = _render_to_html(spec, data)
        assert "Explore the data" in html, (
            "Build-level subtitle must appear in dashboard HTML. "
            "build_options['subtitle'] is specified in full_dashboard.do but "
            "was silently dropped by render()."
        )

    def test_build_subtitle_without_title(self):
        """subtitle appears in HTML even when title is empty."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["build_options"]["title"] = ""
        spec["build_options"]["subtitle"] = "Just a subtitle"
        html = _render_to_html(spec, data)
        assert "Just a subtitle" in html, (
            "Build-level subtitle must appear in HTML even when title is empty."
        )

    def test_build_subtitle_escaped(self):
        """subtitle with HTML special characters is safely escaped (no raw injection).

        When the subtitle contains '<b>bold</b>', the text 'bold' must appear in
        the HTML (content is preserved) but the raw '<b>bold</b>' tag must NOT
        appear as an unescaped inline HTML element (XSS prevention via html.escape).
        """
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["build_options"]["title"] = "Safe Title"
        spec["build_options"]["subtitle"] = "<b>bold</b>"
        html = _render_to_html(spec, data)
        # The header is two Divs, whose text BokehJS renders as HTML, so
        # each is parsed as the browser parses it: the title an <h2>, the
        # subtitle a <p> whose text reads "<b>bold</b>" -- escaped once,
        # opening no <b>.  The page text could not show this: Bokeh escapes
        # the document as a whole, so "<b>bold</b>" was absent from the
        # page whether or not dash escaped the subtitle, and "bold" is a
        # word the page's BokehJS carries 20 times (measured 24sep2026).
        assert _header_divs(html) == [(["h2"], "Safe Title"),
                                      (["p"], "<b>bold</b>")], (
            "Subtitle '<b>bold</b>' must reach its Div escaped, as text "
            "(html.escape() must be applied to prevent XSS injection)."
        )

    def test_empty_subtitle_no_extra_element(self):
        """Empty subtitle does not add an extra empty element."""
        spec, data = _single_graph_spec("scatter", {"yvar": "y", "xvar": "x"})
        spec["build_options"]["title"] = "Title Only"
        spec["build_options"]["subtitle"] = ""
        html = _render_to_html(spec, data)
        # One header Div, the title's.  This checked only that the title
        # was on the page, so an empty subtitle element passed.
        assert _header_divs(html) == [(["h2"], "Title Only")], \
            "Title must appear alone when subtitle is empty."
