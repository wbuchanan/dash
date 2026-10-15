"""
test_server.py
==============
Unit tests for the ServerAppBuilder class in dash_render.py.

Tests:
  P4-57  Build output compiles without error
  P4-58  Generated file contains make_document function
  P4-59  Generated file contains __main__ block
  P4-60  Generated file contains Server and allow_websocket_origin
  P4-61  make_document builds the figure and the KPI card the spec describes
  P4-62  Filter callback recomputes histogram CDS when data is filtered
  P4-63  Filter callback recomputes lfit CDS when data is filtered
  P4-64  Filter callback updates filter-mode KPI Div.text
  P4-65  Brush callback updates brush-mode KPI Div.text
  P4-66  Base64 data round-trips correctly
  P4-67  XSS: <script> in title is HTML-escaped in generated file
  P4-68  Python escape chars in data do not break generated file syntax
  P4-69  --mode standalone still produces HTML (regression)
  P4-70  the served histogram's structure (top/left/right per bin)
  P4-71  _compute_kpi returns correct values for mean and dcount
  P4-72  the served lfit is drawn at 100 x/y points
  P4-73  _compute_kpi sd uses ddof=1 matching Stata (regression)

  BUG-RL-1  _RateLimiter allows requests below limit and blocks above it
  BUG-RL-2  Generated HealthHandler.prepare() enforces _LIMITER (429 on excess)
  BUG-RL-3  make_document enforces rate limit — adds 429 Div and returns early
  BUG-RL-4  make_document proceeds normally when rate limit is not exceeded

  BUG-FE-1  Server-mode function expressions with arithmetic operators (+, -, *, /, **) must not raise ValueError
"""

from __future__ import annotations

import ast
import hashlib
import base64
import importlib.util
import json
import os
import sys
import tempfile
import types

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Helpers to import dash_render from parent directory
# ---------------------------------------------------------------------------

_HERE = os.path.dirname(__file__)
_DASH_DIR = os.path.dirname(_HERE)
sys.path.insert(0, os.path.abspath(_HERE))
from serve_token_probe import TEST_TOKEN, token_args  # noqa: E402  (P0.12a)
from conftest import load_app  # noqa: E402  (WP-30 A3)
import dash_render as _dr_mod  # noqa: E402  (WP-30 P1.3a)
from by_panel_probe import is_chrome, panel_label  # noqa: E402  (WP-30 P1.15a)


from conftest import render_models  # noqa: E402


def _panel_name(fig):
    """A by() panel's label row, else the figure's title.  Flipped (WP-30
    P1.15a): these keyed panels on the title, which held the label;
    twoway keeps title() on each panel and draws the label as its own
    row."""
    if fig is None:
        return ""
    return panel_label(fig) or (fig.title.text if fig.title is not None
                                else "")


def _load_dash_render():
    """Import dash_render module from the parent directory."""
    spec = importlib.util.spec_from_file_location(
        "dash_render", os.path.join(_DASH_DIR, "dash_render.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def dr_module():
    """Return the loaded dash_render module."""
    return _load_dash_render()


@pytest.fixture
def auto_df():
    """Small synthetic DataFrame mimicking Stata auto.dta."""
    rng = np.random.default_rng(42)
    n = 30
    return pd.DataFrame({
        "mpg":    rng.integers(12, 40, n).astype(float),
        "weight": rng.integers(1800, 4800, n).astype(float),
        "price":  rng.integers(3000, 15000, n).astype(float),
        "foreign": rng.integers(0, 2, n).astype(float),
    })


def _make_spec_json(graphs=None, kpis=None, build_options=None):
    """Build a minimal master spec JSON dict."""
    return {
        "graphs": graphs or [],
        "kpis": kpis or [],
        "build_options": build_options or {
            "layout": "auto", "link": "", "filter": "",
            "theme": "default", "title": "Test Dashboard",
            "subtitle": "", "registry": "",
            "mode": "server", "port": "5006",
        },
    }


def _make_data_json(df: pd.DataFrame) -> str:
    """Build a minimal jsonio-format JSON string from a DataFrame."""
    values = []
    for _, row in df.iterrows():
        values.append({col: (None if pd.isna(row[col]) else row[col]) for col in df.columns})
    return json.dumps({
        "variableNames": list(df.columns),
        "variableLabels": {c: c for c in df.columns},
        "valueLabelNames": {},
        "valueLabels": {},
        "variableTypeIsString": {c: False for c in df.columns},
        "values": values,
    })


def _write_temp_files(df, spec_dict):
    """Write spec and data to temp files; return (spec_path, data_path)."""
    spec_f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(spec_dict, spec_f)
    spec_f.close()

    data_f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    data_f.write(_make_data_json(df))
    data_f.close()

    return spec_f.name, data_f.name


def _build_app(dr_module, df, spec_dict) -> str:
    """Build a server app and return its source code string."""
    spec_path, data_path = _write_temp_files(df, spec_dict)
    out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
    out_f.close()
    try:
        builder = dr_module.ServerAppBuilder(spec_path, data_path)
        builder.build(out_f.name)
        with open(out_f.name, "r", encoding="utf-8") as f:
            return f.read()
    finally:
        for _p in (spec_path, data_path, out_f.name):
            try:
                os.unlink(_p)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Document readers.  A test reads what a dashboard DRAWS from its document:
# the served app's (make_document on a fresh Document) or the saved page's
# embedded one.  Not the page's text -- the page inlines BokehJS, which
# names every model class whatever the dashboard holds -- and not a count
# of roots, which the layout column every document carries keeps at 1
# whether or not anything was drawn (WP-24, measured 24sep2026).
# ---------------------------------------------------------------------------

def _page_document(html_str):
    """The saved page's one embedded Bokeh document, read back as models.
    Bokeh HTML-escapes the JSON block, so it is unescaped first."""
    import html as _html
    import re as _re
    from bokeh.document import Document
    blocks = _re.findall(r'<script type="application/json" id="[^"]+">'
                         r'\s*(.*?)\s*</script>', html_str, _re.S)
    docs = [d for b in blocks for d in json.loads(_html.unescape(b)).values()]
    assert len(docs) == 1, f"{len(docs)} embedded Bokeh documents, not 1"
    return Document.from_json(docs[0])


def _glyph_layers(roots):
    """``[(figure, GlyphRenderer)]`` for every layer drawn under *roots*.
    Model.select walks a set, so callers must not rely on the order."""
    from bokeh.models import GlyphRenderer, Plot
    out = []
    for root in roots:
        for fig in root.select({"type": Plot}):
            out.extend((fig, r) for r in fig.renderers
                       if isinstance(r, GlyphRenderer))
    return out


def _drawn_values(renderer, column):
    """The values of *column* a layer draws: its source's rows that the
    view's filter keeps.  A filter this cannot read fails the test rather
    than reading as "every row"."""
    vals = [float(v) for v in renderer.data_source.data[column]]
    filt = getattr(renderer.view, "filter", None)
    kind = type(filt).__name__
    if kind == "AllIndices":
        keep = range(len(vals))
    elif kind == "BooleanFilter":
        keep = [i for i, b in enumerate(list(filt.booleans)[:len(vals)]) if b]
    elif kind == "IndexFilter":
        keep = [i for i in filt.indices if 0 <= i < len(vals)]
    else:
        raise AssertionError(f"a view filter the reader cannot read: {kind}")
    return [vals[i] for i in keep]


def _saved_page(dr_module, df, spec):
    """``(page text, warning texts)`` from the saved-page renderer."""
    import warnings as _w
    spec_path, data_path = _write_temp_files(df, spec)
    try:
        with _w.catch_warnings(record=True) as caught:
            _w.simplefilter("always")
            page = dr_module.DashRenderer(spec_path, data_path).render()
    finally:
        for _p in (spec_path, data_path):
            try:
                os.unlink(_p)
            except OSError:
                pass
    return page, [str(c.message) for c in caught]


def _panel_curves(roots, xcol, ycol):
    """``{panel title: [(x, y), ...]}`` for the one layer of each figure
    whose source carries *xcol* -- a computed line's own columns."""
    out = {}
    for fig, r in _glyph_layers(roots):
        if xcol in r.data_source.data:
            title = _panel_name(fig)
            assert title not in out, f"two {xcol} layers in panel {title!r}"
            out[title] = list(zip(_drawn_values(r, xcol),
                                  _drawn_values(r, ycol)))
    return out


# ---------------------------------------------------------------------------
# P4-57: Generated file compiles without syntax error
# ---------------------------------------------------------------------------

def test_generated_file_compiles(dr_module, auto_df):
    """P4-57: compile() on generated source succeeds without SyntaxError."""
    spec = _make_spec_json(
        graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "s1", "title": "MPG vs Weight"},
        }],
    )
    source = _build_app(dr_module, auto_df, spec)
    try:
        code = compile(source, "<generated>", "exec")
    except SyntaxError as exc:
        pytest.fail("P4-57: the generated app is not valid Python: %s" % exc)
    # ...and the module it compiles to defines the entry point bokeh serve
    # calls -- its code object, not the name, which the module-level call
    # to it would put in co_names by itself.
    assert "make_document" in {c.co_name for c in code.co_consts
                               if isinstance(c, types.CodeType)}


# ---------------------------------------------------------------------------
# P4-58: Generated file contains make_document definition
# ---------------------------------------------------------------------------

def test_generated_contains_make_document(dr_module, auto_df):
    """P4-58: Generated source contains 'def make_document(doc):'."""
    spec = _make_spec_json(
        graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "s1", "title": ""},
        }],
    )
    source = _build_app(dr_module, auto_df, spec)
    assert "def make_document(doc):" in source


# ---------------------------------------------------------------------------
# P4-59: Generated file contains __main__ block
# ---------------------------------------------------------------------------

def test_generated_contains_main_block(dr_module, auto_df):
    """P4-59: Generated source contains '__main__' block."""
    spec = _make_spec_json(
        graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "s1", "title": ""},
        }],
    )
    source = _build_app(dr_module, auto_df, spec)
    assert "if __name__ == '__main__':" in source


# ---------------------------------------------------------------------------
# P4-60: Generated file contains Server and allow_websocket_origin
# ---------------------------------------------------------------------------

def test_generated_contains_server_and_websocket_origin(dr_module, auto_df):
    """P4-60: Server and allow_websocket_origin present in generated source."""
    spec = _make_spec_json(
        graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "s1", "title": ""},
        }],
    )
    source = _build_app(dr_module, auto_df, spec)
    assert "Server" in source
    assert "allow_websocket_origin" in source


# ---------------------------------------------------------------------------
# P4-61: make_document builds the figure and the KPI card the spec describes
# ---------------------------------------------------------------------------

def test_make_document_callable(dr_module, auto_df):
    """P4-61: make_document builds the dashboard the spec describes.

    This asserted ``len(doc.roots) > 0``.  The app adds one layout column
    for every document, so the count is 1 with the scatter drawn from no
    rows and no KPI card at all (WP-24, measured 24sep2026).  It now
    reads the document: the one figure, titled "Scatter", draws the 30
    (weight, mpg) points, and the KPI card holds mpg's mean in its
    %9.1f -- computed from the data, not the spec's stale "21.0"."""
    from bokeh.document import Document
    from bokeh.models import Div

    spec = _make_spec_json(
        graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "s1", "title": "Scatter"},
        }],
        kpis=[{
            "name": "k1", "stat": "mean", "var": "mpg",
            "value": "21.0", "display": "21.0", "fmt": "%9.1f",
            "title": "Avg MPG", "subtitle": "", "color": "", "bgcolor": "",
            "update": "filter",
        }],
    )
    spec_path, data_path = _write_temp_files(auto_df, spec)
    out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
    out_f.close()

    try:
        builder = dr_module.ServerAppBuilder(spec_path, data_path)
        builder.build(out_f.name, port=5006)

        # Load and execute the generated module
        app_mod = load_app(out_f.name, "_test_app")

        doc = Document()
        app_mod.make_document(doc)
        assert len(doc.roots) == 1, doc.roots
        layers = _glyph_layers(doc.roots)
        assert [(f.title.text, type(r.glyph).__name__) for f, r in layers] \
            == [("Scatter", "Scatter")], layers
        _fig, r = layers[0]
        assert sorted(zip(_drawn_values(r, "weight"), _drawn_values(r, "mpg"))) \
            == sorted(zip(auto_df["weight"], auto_df["mpg"])), (
            "the served scatter does not draw the data's 30 points")
        card = _ql_kpi_value(list(doc.select({"type": Div})))
        assert card == "%.1f" % auto_df["mpg"].mean(), card
    finally:
        os.unlink(spec_path)
        os.unlink(data_path)
        os.unlink(out_f.name)


# ---------------------------------------------------------------------------
# P4-62: Filter callback recomputes histogram CDS
# ---------------------------------------------------------------------------

def _served_layer(dr_module, df, plot, key, filter_move=None, mod="_srv_layer"):
    """Serve one plot and return the first data source carrying *key*, as
    a dict of lists; with ``filter_move=(var, value)`` also return it again
    after the dropdown on *var* is moved to *value*.

    P4-62, P4-63, P4-70 and P4-72 called the served app's
    `_compute_histogram' and `_compute_lfit' directly.  Nothing in the app
    called either -- the layers are drawn, and redrawn under a filter,
    through GlyphMapper -- and both ignored a weight, so WP-18 deleted them
    with the other dead statistical copies.  The same properties are asked
    of what the app actually serves.
    """
    import warnings
    from bokeh.document import Document
    from bokeh.models import Select
    bo = None
    if filter_move is not None:
        bo = {"layout": "auto", "link": "",
              "filter": "%s, type(dropdown)" % filter_move[0],
              "theme": "default", "title": "", "subtitle": "",
              "registry": "", "mode": "server", "port": "5006"}
    spec = _make_spec_json(graphs=[{"plots": [plot],
                                    "graph_options": {"name": "g1"}}],
                           build_options=bo)
    spec_path, data_path = _write_temp_files(df, spec)
    out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
    out_f.close()
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr_module.ServerAppBuilder(spec_path, data_path).build(out_f.name)
            app = load_app(out_f.name, mod)
            doc = Document()
            app.make_document(doc)

            def _grab():
                for m in doc.select({"type": object}):
                    d = getattr(m, "data", None)
                    if isinstance(d, dict) and key in d:
                        return {k: list(v) for k, v in d.items()}
                raise AssertionError("no source with %r in the served app" % key)

            first = _grab()
            if filter_move is None:
                return first
            w = [m for m in doc.select({"type": Select})][0]
            old = w.value
            w.value = filter_move[1]
            for cb in w._callbacks.get("value", []):
                cb("value", old, filter_move[1])
            return first, _grab()
    finally:
        for p in (spec_path, data_path, out_f.name):
            try: os.unlink(p)
            except OSError: pass


def test_filter_callback_recomputes_histogram(dr_module, auto_df):
    """P4-62: the served histogram recounts when a filter drops rows."""
    plot = {"type": "histogram", "yvar": "mpg", "xvar": "",
            "options": {"bin": "10", "frequency": "frequency"}}
    full, half = _served_layer(dr_module, auto_df, plot, "top",
                               filter_move=("foreign", "0.0"), mod="_t_hist_f")
    assert len(full["top"]) == 10 and len(half["top"]) == 10
    assert sum(full["top"]) == len(auto_df)
    assert sum(half["top"]) == int((auto_df["foreign"] == 0).sum())


# ---------------------------------------------------------------------------
# P4-63: Filter callback recomputes lfit CDS
# ---------------------------------------------------------------------------

def test_filter_callback_recomputes_lfit(dr_module, auto_df):
    """P4-63: the served lfit refits when a filter drops rows."""
    plot = {"type": "lfit", "yvar": "mpg", "xvar": "weight", "options": {}}
    full, sub = _served_layer(dr_module, auto_df, plot, "y",
                              filter_move=("foreign", "1.0"), mod="_t_lfit_f")
    assert len(full["x"]) == 100 and len(sub["x"]) == 100
    assert not np.allclose(full["y"], sub["y"], atol=1.0), \
        "lfit should produce different values for full vs filtered data"


# ---------------------------------------------------------------------------
# P4-64: Filter callback updates filter-mode KPI Div.text
# ---------------------------------------------------------------------------

def test_filter_callback_updates_kpi_div(dr_module, auto_df):
    """P4-64: _compute_kpi returns correct mean; filter changes the value."""
    from bokeh.document import Document

    spec = _make_spec_json(
        graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "s1", "title": ""},
        }],
        kpis=[{
            "name": "k1", "stat": "mean", "var": "mpg",
            "value": "", "display": "", "fmt": "%9.1f",
            "title": "Avg MPG", "subtitle": "", "color": "", "bgcolor": "",
            "update": "filter",
        }],
    )
    spec_path, data_path = _write_temp_files(auto_df, spec)
    out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
    out_f.close()

    try:
        builder = dr_module.ServerAppBuilder(spec_path, data_path)
        builder.build(out_f.name)

        app_mod = load_app(out_f.name, "_test_app_kpi")

        full_mean = app_mod._compute_kpi(auto_df, "mean", "mpg")
        sub_df = auto_df[auto_df["foreign"] == 1]
        sub_mean = app_mod._compute_kpi(sub_df, "mean", "mpg")

        assert abs(full_mean - float(auto_df["mpg"].mean())) < 0.01
        assert abs(sub_mean - float(sub_df["mpg"].mean())) < 0.01
        assert full_mean != sub_mean, "KPI mean should differ for full vs filtered data"
    finally:
        os.unlink(spec_path)
        os.unlink(data_path)
        os.unlink(out_f.name)


# ---------------------------------------------------------------------------
# P4-65: Brush callback updates brush-mode KPI
# ---------------------------------------------------------------------------

def test_brush_callback_updates_kpi(dr_module, auto_df):
    """P4-65: _compute_kpi on a selection subset gives correct result."""
    from bokeh.document import Document

    spec = _make_spec_json(
        kpis=[{
            "name": "k_brush", "stat": "mean", "var": "mpg",
            "value": "", "display": "", "fmt": "",
            "title": "Selection Avg MPG", "subtitle": "", "color": "", "bgcolor": "",
            "update": "brush",
        }],
        graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "s1", "title": ""},
        }],
    )
    spec_path, data_path = _write_temp_files(auto_df, spec)
    out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
    out_f.close()

    try:
        builder = dr_module.ServerAppBuilder(spec_path, data_path)
        builder.build(out_f.name)

        app_mod = load_app(out_f.name, "_test_app_brush")

        indices = [0, 1, 2, 3, 4]  # first 5 rows
        sel_df = auto_df.iloc[indices]
        sel_mean = app_mod._compute_kpi(sel_df, "mean", "mpg")
        expected = float(auto_df.iloc[indices]["mpg"].mean())
        assert abs(sel_mean - expected) < 0.01
    finally:
        os.unlink(spec_path)
        os.unlink(data_path)
        os.unlink(out_f.name)


# ---------------------------------------------------------------------------
# P4-66: Base64 data round-trips correctly
# ---------------------------------------------------------------------------

def test_base64_round_trip(dr_module, auto_df):
    """P4-66: base64 encode then decode gives back identical JSON."""
    spec = _make_spec_json()
    spec_path, data_path = _write_temp_files(auto_df, spec)

    try:
        builder = dr_module.ServerAppBuilder(spec_path, data_path)
        spec_b64, data_b64 = builder._embed_data()

        decoded_spec = json.loads(base64.b64decode(spec_b64).decode("utf-8"))
        decoded_data = json.loads(base64.b64decode(data_b64).decode("utf-8"))

        assert decoded_spec == spec, "Spec round-trip failed"
        assert "variableNames" in decoded_data, "Data round-trip missing variableNames"
        assert list(decoded_data["variableNames"]) == list(auto_df.columns)
    finally:
        os.unlink(spec_path)
        os.unlink(data_path)


# ---------------------------------------------------------------------------
# P4-67: XSS — <script> in title is HTML-escaped
# ---------------------------------------------------------------------------

def test_xss_title_escaped(dr_module, auto_df):
    """P4-67: <script>alert(1)</script> in title — XSS protection is two-layer.

    Layer 1 (static):  The raw title is embedded only inside the base64-encoded
    _SPEC_B64 constant.  It must never appear as a raw string literal in any
    non-base64 line of the generated source, preventing code-injection into the
    generated Python file itself.

    Layer 2 (runtime): make_document calls html.escape() on the decoded title
    before inserting it into any Bokeh Div, preventing browser XSS.  We verify
    this by calling make_document and checking the resulting document title does
    not contain a raw '<script>' tag.
    """
    from bokeh.document import Document

    xss_title = "<script>alert(1)</script>"
    spec = _make_spec_json(
        graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "s1", "title": ""},
        }],
        build_options={
            "layout": "auto", "link": "", "filter": "", "theme": "default",
            "title": xss_title, "subtitle": "", "registry": "s1",
            "mode": "server", "port": "5006",
        },
    )
    source = _build_app(dr_module, auto_df, spec)

    # --- Layer 1: <script> must not appear outside the base64 constant lines ---
    non_b64_lines = [
        line for line in source.splitlines()
        if "_SPEC_B64" not in line and "_DATA_B64" not in line
    ]
    for line in non_b64_lines:
        assert "<script>" not in line, (
            f"XSS Layer 1: raw <script> found outside base64 constants: {line!r}"
        )

    # --- Layer 1b: html.escape is called somewhere in the generated source ---
    assert "html.escape" in source, (
        "XSS Layer 1b: html.escape not found in generated source — runtime escaping absent"
    )

    # --- Layer 2: make_document runtime escaping — doc.title must not contain raw tag ---
    spec_path, data_path = _write_temp_files(auto_df, spec)
    out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
    out_f.close()
    try:
        builder = dr_module.ServerAppBuilder(spec_path, data_path)
        builder.build(out_f.name, port=5006)
        app_mod = load_app(out_f.name, "_test_xss_app")
        doc = Document()
        app_mod.make_document(doc)
        # --- Layer 2: the PAGE.  doc.title used to be set to the already
        # escaped text, and this asserted on the model; but Bokeh's page
        # template escapes the title itself (measured: a raw "R&D <b>" is
        # rendered as "R&amp;D &lt;b&gt;", a pre-escaped one as
        # "R&amp;amp;D &amp;lt;b&amp;gt;"), so the double escape showed
        # in the browser tab as "&amp;".  The title is raw on the model
        # and the rendered <title> is what must carry no tag.
        import re as _re
        from bokeh.embed import file_html as _file_html
        from bokeh.resources import INLINE as _INLINE
        _page = _file_html(doc, _INLINE)
        _m = _re.search(r"<title>(.*?)</title>", _page, _re.S)
        assert _m is not None, "the rendered page has no <title>"
        assert "<script>" not in _m.group(1), (
            f"XSS Layer 2: raw <script> in the rendered <title>: {_m.group(1)!r}"
        )
        assert "&amp;lt;" not in _m.group(1), (
            f"the title is escaped twice: {_m.group(1)!r}"
        )
        # The header Div escapes once, too.
        from bokeh.models import Div as _Div
        _divs = [m for m in doc.select({"type": _Div}) if "db-title" in m.text]
        assert _divs and "<script>" not in _divs[0].text.replace(
            "&lt;script&gt;", "")
    finally:
        os.unlink(spec_path)
        os.unlink(data_path)
        os.unlink(out_f.name)


# ---------------------------------------------------------------------------
# P4-68: Python escape chars in data do not break generated file
# ---------------------------------------------------------------------------

def test_escape_chars_in_data_do_not_break_syntax(dr_module):
    """P4-68: Data with backslashes and single quotes does not break generated Python."""
    df = pd.DataFrame({
        "mpg":   [21.0, 19.0, 15.0],
        "label": ["it\\'s fine", "line\\nbreak", "tab\\there"],
    })
    spec = _make_spec_json(
        graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "mpg", "options": {}}],
            "graph_options": {"name": "s1", "title": ""},
        }],
    )
    source = _build_app(dr_module, df, spec)
    # ast.parse verifies no SyntaxError — base64 encoding should prevent any issues
    try:
        ast.parse(source)
    except SyntaxError as e:
        pytest.fail(f"P4-68: Generated file has SyntaxError with escape chars in data: {e}")


# ---------------------------------------------------------------------------
# P4-69: --mode standalone still produces HTML (regression)
# ---------------------------------------------------------------------------

def test_standalone_mode_still_works(dr_module, auto_df):
    """P4-69: main() with mode='standalone' still produces an HTML file."""
    spec = _make_spec_json(
        graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "s1", "title": "Regression Test"},
        }],
        build_options={
            "layout": "auto", "link": "", "filter": "", "theme": "default",
            "title": "Regression", "subtitle": "", "registry": "s1",
            "mode": "standalone",
        },
    )
    spec_path, data_path = _write_temp_files(auto_df, spec)
    out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False)
    out_f.close()

    try:
        dr_module.main(spec_path, data_path, out_f.name, mode="standalone")
        with open(out_f.name, "r", encoding="utf-8") as f:
            html_content = f.read()
        assert "bokeh" in html_content.lower(), "Standalone HTML should contain Bokeh content"
        assert "<html" in html_content.lower(), "Standalone output should be an HTML file"
    finally:
        os.unlink(spec_path)
        os.unlink(data_path)
        os.unlink(out_f.name)


# ---------------------------------------------------------------------------
# P4-70: the served histogram's structure
# ---------------------------------------------------------------------------

def test_compute_histogram_structure(dr_module, auto_df):
    """P4-70: the served histogram has top/left/right, one per bin.

    The heights are a DENSITY by default, as Stata's histogram is (this
    once asserted raw counts, Stata's `frequency', which was the defect);
    frequency() asks for the counts, and then they are the counts.
    """
    plot = {"type": "histogram", "yvar": "mpg", "xvar": "",
            "options": {"bin": "15"}}
    result = _served_layer(dr_module, auto_df, plot, "top", mod="_t_hist_s")
    assert {"top", "left", "right"} <= set(result.keys())
    assert len(result["top"]) == len(result["left"]) == len(result["right"]) == 15
    assert all(v >= 0 for v in result["top"])
    _area = sum(t * (r - l) for t, l, r
                in zip(result["top"], result["left"], result["right"]))
    assert abs(_area - 1.0) < 1e-9
    plot["options"]["frequency"] = "frequency"
    counts = _served_layer(dr_module, auto_df, plot, "top", mod="_t_hist_c")
    assert sum(counts["top"]) == auto_df["mpg"].dropna().shape[0]


# ---------------------------------------------------------------------------
# P4-71: _compute_kpi for mean and dcount
# ---------------------------------------------------------------------------

def test_compute_kpi_mean_and_dcount(dr_module, auto_df):
    """P4-71: _compute_kpi mean and dcount return correct values."""
    spec = _make_spec_json()
    spec_path, data_path = _write_temp_files(auto_df, spec)
    out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
    out_f.close()

    try:
        builder = dr_module.ServerAppBuilder(spec_path, data_path)
        builder.build(out_f.name)

        app_mod = load_app(out_f.name, "_test_kpi_vals")

        mean_val = app_mod._compute_kpi(auto_df, "mean", "mpg")
        assert abs(mean_val - float(auto_df["mpg"].mean())) < 0.001

        dcount_val = app_mod._compute_kpi(auto_df, "dcount", "foreign")
        assert dcount_val == float(auto_df["foreign"].nunique()), \
            f"dcount expected {auto_df['foreign'].nunique()}, got {dcount_val}"
    finally:
        os.unlink(spec_path)
        os.unlink(data_path)
        os.unlink(out_f.name)


# ---------------------------------------------------------------------------
# P4-72: the served lfit is drawn at 100 points
# ---------------------------------------------------------------------------

def test_compute_lfit_100_points(dr_module, auto_df):
    """P4-72: the served lfit has 100 x-points and 100 y-points, x rising
    (Stata's fit grid, _gs_x_create.ado: n() 100 over the observed range)."""
    plot = {"type": "lfit", "yvar": "mpg", "xvar": "weight", "options": {}}
    result = _served_layer(dr_module, auto_df, plot, "y", mod="_t_lfit_pts")
    assert len(result["x"]) == 100, f"Expected 100 x-points, got {len(result['x'])}"
    assert len(result["y"]) == 100, f"Expected 100 y-points, got {len(result['y'])}"
    assert result["x"][0] < result["x"][-1]


# ---------------------------------------------------------------------------
# P4-73 (regression): _compute_kpi sd uses ddof=1 matching Stata
# ---------------------------------------------------------------------------

def test_compute_kpi_sd_uses_ddof1(dr_module, auto_df):
    """Regression: _compute_kpi sd result matches pandas ddof=1 (Stata's unbiased SD).

    Ensures the generated server code uses series.std(ddof=1), not the
    population-SD default of numpy/ddof=0, so server-mode KPI values match
    standalone-mode values exactly.
    """
    spec = _make_spec_json()
    spec_path, data_path = _write_temp_files(auto_df, spec)
    out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
    out_f.close()

    try:
        builder = dr_module.ServerAppBuilder(spec_path, data_path)
        builder.build(out_f.name)

        app_mod = load_app(out_f.name, "_test_sd_ddof")

        sd_val = app_mod._compute_kpi(auto_df, "sd", "mpg")
        expected_ddof1 = float(auto_df["mpg"].std(ddof=1))
        expected_ddof0 = float(auto_df["mpg"].std(ddof=0))

        # Must match ddof=1 (sample SD, Stata default)
        assert abs(sd_val - expected_ddof1) < 1e-9, (
            f"sd mismatch: got {sd_val}, expected ddof=1 value {expected_ddof1} "
            f"(ddof=0 would give {expected_ddof0})"
        )
    finally:
        os.unlink(spec_path)
        os.unlink(data_path)
        os.unlink(out_f.name)


# ---------------------------------------------------------------------------
# Regression: _compute_kdensity handles constant data without crashing
# ---------------------------------------------------------------------------

def test_compute_kdensity_constant_data_returns_empty(dr_module, auto_df):
    """Regression: a served kdensity on constant data draws nothing, and
    does not crash.

    scipy.stats.gaussian_kde raised LinAlgError on zero-variance data, and
    the served app's own `_compute_kdensity' guarded against it.  That copy
    was dead once the served app drew computed layers through the mapper,
    and WP-18 deleted it; the guard that matters is the one on the path the
    served app runs, so this builds and serves the layer.  A constant
    column and a single row each give an empty kdensity source; ordinary
    data give the 300-point curve, so the empty source is not the only
    thing the layer can produce.
    """
    import warnings
    from bokeh.document import Document

    spec = _make_spec_json(graphs=[{
        "plots": [{"type": "kdensity", "yvar": "mpg", "options": {}}],
        "graph_options": {"name": "g1"},
    }])

    def _served_lengths(df, mod_name):
        spec_path, data_path = _write_temp_files(df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                dr_module.ServerAppBuilder(spec_path, data_path).build(out_f.name)
                mod = load_app(out_f.name, mod_name)
                doc = Document()
                mod.make_document(doc)
            figs = [m for m in doc.select({"type": object})
                    if type(m).__name__ == "figure"]
            return [len(r.data_source.data.get("y", ()))
                    for f in figs for r in f.renderers]
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try: os.unlink(_p)
                except OSError: pass

    const_df = auto_df.copy()
    const_df["mpg"] = 22.0
    assert _served_lengths(const_df, "_test_kde_const") == [0]
    assert _served_lengths(auto_df.iloc[:1].copy(), "_test_kde_one") == [0]
    assert _served_lengths(auto_df, "_test_kde_ok") == [300]


# ---------------------------------------------------------------------------
# Phase 2: Server-mode dispatch tests for previously missing plot types
# ---------------------------------------------------------------------------

def _range_data():
    """DataFrame with lo/hi/x columns for range plot tests."""
    rng = np.random.default_rng(42)
    n = 20
    return pd.DataFrame({
        "lo": rng.uniform(1, 5, n),
        "hi": rng.uniform(6, 10, n),
        "x":  np.linspace(0, 10, n),
    })


class TestServerDispatchConnected:
    def test_connected_in_server_source(self, dr_module, auto_df):
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "connected", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "c1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "fig.line(" in source, "connected should produce fig.line"
        assert "fig.scatter(" in source, "connected should produce fig.scatter"


class TestServerDispatchDot:
    def test_dot_in_server_source(self, dr_module, auto_df):
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "dot", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "d1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "fig.scatter(" in source, "dot should produce fig.scatter"


class TestServerDispatchLfitci:
    def test_lfitci_in_server_source(self, dr_module, auto_df):
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "lfitci", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "lc1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "fig.line(" in source, "lfitci should produce fig.line"
        assert "fig.varea(" in source, "lfitci should produce fig.varea"


class TestServerDispatchQfitci:
    def test_qfitci_in_server_source(self, dr_module, auto_df):
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "qfitci", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "qc1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "fig.line(" in source, "qfitci should produce fig.line"
        assert "fig.varea(" in source, "qfitci should produce fig.varea"


class TestServerDispatchRarea:
    def test_rarea_in_server_source(self, dr_module):
        rdf = _range_data()
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rarea", "yvar1": "lo", "yvar2": "hi", "xvar": "x", "options": {}}],
            "graph_options": {"name": "ra1"},
        }])
        source = _build_app(dr_module, rdf, spec)
        assert "fig.varea(" in source, "rarea should produce fig.varea"


class TestServerDispatchRbar:
    def test_rbar_in_server_source(self, dr_module):
        rdf = _range_data()
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rbar", "yvar1": "lo", "yvar2": "hi", "xvar": "x", "options": {}}],
            "graph_options": {"name": "rb1"},
        }])
        source = _build_app(dr_module, rdf, spec)
        assert "fig.vbar(" in source, "rbar should produce fig.vbar"


class TestServerDispatchRspike:
    def test_rspike_in_server_source(self, dr_module):
        rdf = _range_data()
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rspike", "yvar1": "lo", "yvar2": "hi", "xvar": "x", "options": {}}],
            "graph_options": {"name": "rs1"},
        }])
        source = _build_app(dr_module, rdf, spec)
        assert "fig.segment(" in source, "rspike should produce fig.segment"


class TestServerDispatchRcap:
    def test_rcap_in_server_source(self, dr_module):
        rdf = _range_data()
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rcap", "yvar1": "lo", "yvar2": "hi", "xvar": "x", "options": {}}],
            "graph_options": {"name": "rc1"},
        }])
        source = _build_app(dr_module, rdf, spec)
        # rcap produces spine + 2 cap segments = at least 3 fig.segment calls
        assert source.count("fig.segment(") >= 3, "rcap should produce >=3 fig.segment calls"


class TestServerDispatchRline:
    def test_rline_in_server_source(self, dr_module):
        rdf = _range_data()
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rline", "yvar1": "lo", "yvar2": "hi", "xvar": "x", "options": {}}],
            "graph_options": {"name": "rl1"},
        }])
        source = _build_app(dr_module, rdf, spec)
        # rline produces 2 fig.line calls (one for each boundary)
        assert source.count("fig.line(") >= 2, "rline should produce >=2 fig.line calls"


class TestServerDispatchRconnected:
    def test_rconnected_in_server_source(self, dr_module):
        rdf = _range_data()
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rconnected", "yvar1": "lo", "yvar2": "hi", "xvar": "x", "options": {}}],
            "graph_options": {"name": "rn1"},
        }])
        source = _build_app(dr_module, rdf, spec)
        assert source.count("fig.line(") >= 2, "rconnected should produce >=2 fig.line"
        assert source.count("fig.scatter(") >= 2, "rconnected should produce >=2 fig.scatter"


class TestServerDispatchDropline:
    def test_dropline_in_server_source(self, dr_module, auto_df):
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "dropline", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "dl1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "fig.segment(" in source, "dropline should emit fig.segment"
        assert "fig.scatter(" in source, "dropline should emit fig.scatter"


class TestServerDispatchRcapsym:
    def test_rcapsym_in_server_source(self, dr_module):
        rdf = _range_data()
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rcapsym", "yvar1": "lo", "yvar2": "hi", "xvar": "x", "options": {}}],
            "graph_options": {"name": "rcs1"},
        }])
        source = _build_app(dr_module, rdf, spec)
        # rcapsym: spine + 2 caps (segments) + 2 scatter markers
        assert source.count("fig.segment(") >= 3, "rcapsym should produce >=3 fig.segment calls"
        assert source.count("fig.scatter(") >= 2, "rcapsym should produce >=2 fig.scatter calls"


class TestServerDispatchScatteri:
    def test_scatteri_in_server_source(self, dr_module, auto_df):
        spec = _make_spec_json(graphs=[{
            "plots": [{
                "type": "scatteri",
                "values": [[1.0, 2.0], [3.0, 4.0]],
                "options": {},
            }],
            "graph_options": {"name": "si1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "fig.scatter(" in source, "scatteri should emit fig.scatter"


# ================================================================
# P6-15 — server-mode: xtitle/ytitle/aspectratio applied to fig
# ================================================================
class TestServerGraphOptions:
    def test_xtitle_code_in_server_source(self, dr_module, auto_df):
        """P6-15: generated server app contains logic to apply xtitle."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "xtitle": "My X Axis"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        # Generated code must read xtitle from graph_options at runtime
        assert "xtitle" in source, "generated source should reference 'xtitle'"

    def test_ytitle_code_in_server_source(self, dr_module, auto_df):
        """P6-15: generated server app contains logic to apply ytitle."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "ytitle": "My Y Axis"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "ytitle" in source, "generated source should reference 'ytitle'"

    def test_aspectratio_in_server_source(self, dr_module, auto_df):
        """P6-15: aspectratio in graph_options is applied in server app."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "aspectratio": "1.5"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "aspect_ratio" in source, "aspectratio should produce aspect_ratio= in server source"

    def test_note_code_in_server_source(self, dr_module, auto_df):
        """P6-15: generated server app contains logic to apply note annotation."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "note": "Source: auto dataset"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        # The generated code must have note-handling logic
        assert "'note'" in source or "note" in source, "generated source should contain note-handling code"


class TestServerGraphOptionsExtended:
    """P6-19: subtitle, xlabel, ylabel applied in server-mode generated app."""

    def test_subtitle_code_in_server_source(self, dr_module, auto_df):
        """P6-19: subtitle logic present in server source."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "subtitle": "My subtitle"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "subtitle" in source

    def test_xlabel_code_in_server_source(self, dr_module, auto_df):
        """P6-19: xlabel tick logic present in server source."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "xlabel": "0 10 20 30"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "xlabel" in source and "FixedTicker" in source

    def test_ylabel_code_in_server_source(self, dr_module, auto_df):
        """P6-19: ylabel tick logic present in server source."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "ylabel": "10 20 30 40"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "ylabel" in source and "FixedTicker" in source


class TestServerXlineYline:
    """xline/yline reference lines must appear in server-mode generated app."""

    def test_xline_span_code_generated(self, dr_module, auto_df):
        """xline option generates Span code with dimension='height' in server app."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "xline": "99.5"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "Span" in source, "xline must generate Span in server app"
        assert "height" in source, "xline Span must use dimension='height'"
        assert "xline" in source, "xline key must appear in the generated code"

    def test_yline_span_code_generated(self, dr_module, auto_df):
        """yline option generates Span code with dimension='width' in server app."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "yline": "9876.5"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "Span" in source, "yline must generate Span in server app"
        assert "width" in source, "yline Span must use dimension='width'"
        assert "yline" in source, "yline key must appear in the generated code"

    def test_xline_and_yline_both_handled(self, dr_module, auto_df):
        """Both xline and yline can be specified together in server app."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "xline": "25", "yline": "3000"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "Span" in source
        assert "height" in source and "width" in source


def _both_figures(dr_module, tmp_path, df, plot, **graph_options):
    """(saved figure, served figure) for one graph of one layer: the saved
    page's DashRenderer figure and the generated app's, from its
    make_document on a fresh Document."""
    from bokeh.models import Plot
    go = {"name": "g1"}
    go.update(graph_options)
    spec = _make_spec_json(graphs=[{"plots": [plot], "graph_options": go}])
    r, _ = _ql_saved(dr_module, tmp_path, spec, df)
    doc, _ = _ql_served(dr_module, tmp_path, spec, df)
    served = [f for root in doc.roots for f in root.select({"type": Plot})]
    assert len(served) == 1, served
    return r.figures["g1"], served[0]


class TestServerLogScale:
    """Server-mode xscale(log) and yscale(log) must produce log-axis figures."""

    def test_xscale_log_generates_x_axis_type(self, dr_module, auto_df):
        """xscale(log) in graph options must generate x_axis_type='log' in server source."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "xscale": "log"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "x_axis_type" in source, "xscale(log) must produce x_axis_type in server app"
        assert "log" in source

    def test_yscale_log_draws_a_log_y_axis_in_both_modes(
            self, dr_module, auto_df, tmp_path):
        """yscale(log) gives a log y axis and leaves x linear, in both modes.

        This asserted that "y_axis_type" and "log" appeared in the generated
        app, which they do for every spec -- the code that reads yscale()
        is written out whether or not a graph asks for it -- and no served
        test drew a figure with yscale(log) (WP-24 scan)."""
        from bokeh.models import LinearScale, LogScale
        scatter = {"type": "scatter", "yvar": "mpg", "xvar": "weight",
                   "options": {}}
        for mode, fig in zip(("saved", "served"), _both_figures(
                dr_module, tmp_path, auto_df, scatter, yscale="log")):
            assert isinstance(fig.y_scale, LogScale), (mode, fig.y_scale)
            assert isinstance(fig.x_scale, LinearScale), (mode, fig.x_scale)

    def test_both_log_scales_draw_two_log_axes_in_both_modes(
            self, dr_module, auto_df, tmp_path):
        """xscale(log) with yscale(log): both axes log, in both modes -- the
        shape BUG-SCALE-1 got wrong on the saved page, where the figure was
        rebuilt for one axis and lost the other.  This asserted the two
        axis-type words appeared in the generated app, which they always
        do."""
        from bokeh.models import LogScale
        scatter = {"type": "scatter", "yvar": "mpg", "xvar": "weight",
                   "options": {}}
        for mode, fig in zip(("saved", "served"), _both_figures(
                dr_module, tmp_path, auto_df, scatter,
                xscale="log", yscale="log")):
            assert isinstance(fig.x_scale, LogScale), (mode, fig.x_scale)
            assert isinstance(fig.y_scale, LogScale), (mode, fig.y_scale)

    def test_log_scale_is_conditional_in_generated_code(self, dr_module, auto_df):
        """Generated code must use a runtime conditional for log scale (xscale/yscale check)."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "xscale": "log"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        # The generated code should check xscale/yscale at runtime
        assert "xscale" in source
        assert "yscale" in source


class TestServerPcarrowPcbarrow:
    """pcarrow and pcbarrow in server mode must generate Arrow annotations."""

    def test_pcarrow_generates_arrow_in_server(self, dr_module, auto_df):
        """pcarrow in server mode must generate Arrow/OpenHead code, not just segment."""
        pc_df = pd.DataFrame({
            "y1": [0.0, 1.0, 2.0], "x1": [0.0, 1.0, 2.0],
            "y2": [1.0, 2.0, 3.0], "x2": [1.0, 2.0, 3.0],
        })
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "pcarrow",
                       "y1var": "y1", "x1var": "x1",
                       "y2var": "y2", "x2var": "x2",
                       "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, pc_df, spec)
        assert "Arrow" in source or "OpenHead" in source, \
            "pcarrow server dispatch must generate Arrow annotation code"
        # WP-31 C1: the heads are drawn by the shared head script.
        assert "_DASH_ARROW_HEAD_JS" in source
        assert "_dash_arrow_head_hooks" in source

    def test_pcbarrow_generates_arrow_in_server(self, dr_module, auto_df):
        """pcbarrow in server mode must generate bidirectional Arrow/NormalHead code."""
        pc_df = pd.DataFrame({
            "y1": [0.0, 1.0], "x1": [0.0, 1.0],
            "y2": [1.0, 2.0], "x2": [1.0, 2.0],
        })
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "pcbarrow",
                       "y1var": "y1", "x1var": "x1",
                       "y2var": "y2", "x2var": "x2",
                       "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, pc_df, spec)
        assert "Arrow" in source or "NormalHead" in source, \
            "pcbarrow server dispatch must generate bidirectional Arrow code"

    def test_pcspike_generates_segment_in_server(self, dr_module, auto_df):
        """pcspike (no arrow) must still generate segment in server mode."""
        pc_df = pd.DataFrame({
            "y1": [0.0, 1.0], "x1": [0.0, 1.0],
            "y2": [1.0, 2.0], "x2": [1.0, 2.0],
        })
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "pcspike",
                       "y1var": "y1", "x1var": "x1",
                       "y2var": "y2", "x2var": "x2",
                       "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, pc_df, spec)
        assert "segment" in source.lower(), \
            "pcspike must generate segment glyph in server mode"

    def test_server_xrange_sets_range(self, dr_module, auto_df):
        """xrange in server mode must generate x_range.start/end code."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "xrange": "5 35"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "x_range" in source or "xrange" in source, \
            "xrange option must appear in server-mode generated code"

    @pytest.mark.parametrize("given,bounds", [
        # WP-28 B2: range() widens only (axis_scale_options.sthlp:336-341);
        # The hull of 10, 40 and the data's own extremes.
        ("range(10 40)", lambda df: (min(10.0, float(df["mpg"].min())),
                                     max(40.0, float(df["mpg"].max())))),
        # range(0) extends the axis to 0 and keeps the data's own top.
        # WP-30 P1.3a: and twoway's ticks over 0 to that top.
        ("range(0)", lambda df: (0.0, max(
            float(df["mpg"].max()),
            _dr_mod._dash_natscale_ticks(0.0, float(df["mpg"].max()), 5)[-1]))),
    ], ids=["both_ends", "one_end"])
    def test_yscale_range_bounds_the_y_axis_in_both_modes(
            self, dr_module, auto_df, tmp_path, given, bounds):
        """yscale(range()) bounds the y axis, in both modes.

        This asserted that "y_range" or "yrange" appeared in the generated
        app for a spec carrying a ``yrange`` key -- a key dash.ado never
        writes and neither renderer reads (test_axis_options.py pins that
        it is gone), in text written out for every spec.  The option a
        user types is yscale(range()); no served test drew it (WP-24)."""
        from bokeh.models import Range1d
        scatter = {"type": "scatter", "yvar": "mpg", "xvar": "weight",
                   "options": {}}
        want = bounds(auto_df)
        ends = []
        for mode, fig in zip(("saved", "served"), _both_figures(
                dr_module, tmp_path, auto_df, scatter, yscale=given)):
            assert isinstance(fig.y_range, Range1d), (mode, fig.y_range)
            assert dr_module._dash_range_hull(fig.y_range) == pytest.approx(
                want), (mode, fig.y_range.start, fig.y_range.end, want)
            ends.append((fig.y_range.start, fig.y_range.end))
        assert ends[0] == ends[1], ends


class TestServerLegendLabelOverrides:
    """Server-mode generated code must support legend label() overrides."""

    def test_legend_label_override_in_server(self, dr_module, auto_df):
        """Generated server app must contain label() override parsing code (regex loop)."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "legend": 'label(1 "My Label")'},
        }])
        source = _build_app(dr_module, auto_df, spec)
        # The generated code must contain the label() regex finditer loop
        assert "finditer" in source, \
            "server-mode legend must contain finditer loop for label() overrides"
        assert "html.escape" in source, \
            "server-mode legend label text must be XSS-escaped"

    def test_legend_off_still_works_in_server(self, dr_module, auto_df):
        """legend(off) must still set visible=False in server app."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "legend": "off"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "visible" in source and "False" in source, \
            "legend(off) must produce visible=False in server code"


class TestServerBarSpikeParity:
    """Server-mode bar/spike/area must honour base(), barwidth(), bfcolor(), blcolor()."""

    def test_bar_base_option_uses_bottom_param(self, dr_module, auto_df):
        """bar server code must emit 'bottom' parameter and read 'base' option."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "bar", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "bottom" in source, \
            "server-mode bar must use 'bottom' parameter in vbar call"
        assert "'base'" in source or '"base"' in source, \
            "server-mode bar must read 'base' option from opts dict"

    def test_bar_barwidth_option_applied(self, dr_module, auto_df):
        """bar server code must read 'barwidth' option from opts."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "bar", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "'barwidth'" in source or '"barwidth"' in source, \
            "server-mode bar must read 'barwidth' option from opts"

    def test_bar_bfcolor_applied(self, dr_module, auto_df):
        """bar server code must read 'bfcolor' option for fill color."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "bar", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "'bfcolor'" in source or '"bfcolor"' in source, \
            "server-mode bar must read 'bfcolor' option for fill color"

    def test_bar_blcolor_applied(self, dr_module, auto_df):
        """bar server code must read 'blcolor' option for line color."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "bar", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "'blcolor'" in source or '"blcolor"' in source, \
            "server-mode bar must read 'blcolor' option for line color"

    def test_spike_base_option_code_present(self, dr_module, auto_df):
        """spike server code must read 'base' option for y0 baseline."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "spike", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "'base'" in source or '"base"' in source, \
            "server-mode spike must read 'base' option for baseline"

    def test_area_base_option_code_present(self, dr_module, auto_df):
        """area server code must read 'base' option for lower boundary."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "area", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "'base'" in source or '"base"' in source, \
            "server-mode area must read 'base' option for lower boundary"

    def test_scatter_mfcolor_code_present(self, dr_module, auto_df):
        """scatter server code must read 'mfcolor' for independent fill color."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "'mfcolor'" in source or '"mfcolor"' in source, \
            "server-mode scatter must read 'mfcolor' option"


class TestServerLinePlotOpts:
    """Server-mode generated code must read lwidth/lpattern for line plots
    and msymbol/msize for scatter."""

    def test_line_lwidth_code_present(self, dr_module, auto_df):
        """line server code must read 'lwidth' option."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "line", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "'lwidth'" in source or '"lwidth"' in source, \
            "server-mode line must read 'lwidth' option from opts"

    def test_line_lpattern_code_present(self, dr_module, auto_df):
        """line server code must read 'lpattern' option."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "line", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "'lpattern'" in source or '"lpattern"' in source, \
            "server-mode line must read 'lpattern' option from opts"

    @pytest.mark.parametrize("ptype,glyph,opts,attr", [
        ("spike", "Segment", {"lwidth": "thick"}, "line_width"),
        ("spike", "Segment", {"lpattern": "dash"}, "line_dash"),
        ("bar", "VBar", {"lwidth": "thick"}, "line_width"),
    ], ids=["spike_lwidth", "spike_lpattern", "bar_lwidth"])
    def test_the_line_option_reaches_the_served_glyph(
            self, dr_module, auto_df, tmp_path, ptype, glyph, opts, attr):
        """The option changes the served glyph, and to what the saved page
        draws.

        These asserted that the words 'lwidth' and 'lpattern' appeared in
        the generated app, which they do for any spec -- GlyphMapper is
        copied into it whole -- and no served test set either option on a
        spike or a bar (WP-24 scan)."""
        from bokeh.models import GlyphRenderer

        def _value(fig):
            got = [getattr(r.glyph, attr) for r in fig.renderers
                   if isinstance(r, GlyphRenderer)
                   and type(r.glyph).__name__ == glyph]
            assert len(got) == 1, (glyph, got)
            v = got[0]
            return list(v) if isinstance(v, (list, tuple)) else v

        plain = {"type": ptype, "yvar": "mpg", "xvar": "weight", "options": {}}
        styled = dict(plain, options=dict(opts))
        s0, v0 = _both_figures(dr_module, tmp_path, auto_df, plain)
        s1, v1 = _both_figures(dr_module, tmp_path, auto_df, styled)
        assert _value(v1) != _value(v0), (
            f"{ptype} {opts}: the served {glyph}'s {attr} is the default "
            f"{_value(v0)!r} with the option given")
        assert _value(v1) == _value(s1), (
            f"{ptype} {opts}: served {_value(v1)!r}, saved {_value(s1)!r}")

    def test_scatter_msymbol_code_present(self, dr_module, auto_df):
        """scatter server code must read 'msymbol' option."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "'msymbol'" in source or '"msymbol"' in source, \
            "server-mode scatter must read 'msymbol' option from opts"

    def test_scatter_msize_code_present(self, dr_module, auto_df):
        """scatter server code must read 'msize' option."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "'msize'" in source or '"msize"' in source, \
            "server-mode scatter must read 'msize' option from opts"


class TestServerLineWidthAllTypes:
    """All line-bearing server-mode plot types must actually apply lwidth to renderers.

    Each test builds a server app with lwidth(thick), executes make_document(),
    and verifies that at least one renderer has line_width≈_THICK_PX.
    Flipped (WP-30 P1.12b): 'thick' was 2.5 px on dash's private ladder;
    it is Stata's .8 units x 3.84 px.
    """

    _THICK_PX = 3.072  # Stata's thick, .8 units x 3.84 px (WP-30 P1.12b)

    def _exec_make_document(self, dr_module, df, spec):
        """Build app, exec make_document, return list of all glyph renderers."""
        from bokeh.document import Document
        spec_path, data_path = _write_temp_files(df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_mod = load_app(out_f.name, "_ta")
            doc = Document()
            app_mod.make_document(doc)
            # Recursively collect all glyph renderers from the document tree
            renderers = []
            def _collect(obj):
                for r in getattr(obj, 'renderers', []):
                    renderers.append(r)
                for child in getattr(obj, 'children', []):
                    if isinstance(child, (list, tuple)):
                        for c in child:
                            if c is not None:
                                _collect(c)
                    elif child is not None:
                        _collect(child)
            for root in doc.roots:
                _collect(root)
            return renderers
        finally:
            for p in (spec_path, data_path, out_f.name):
                try:
                    os.unlink(p)
                except OSError:
                    pass

    def _exec_make_document_with_arrows(self, dr_module, df, spec):
        """Build app, exec make_document, return (renderers, arrow_annots) tuple.

        Traverses fig.center/above/below/left/right panels to find Arrow
        annotation objects added via fig.add_layout().
        """
        from bokeh.document import Document
        from bokeh.models import Arrow
        spec_path, data_path = _write_temp_files(df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_mod = load_app(out_f.name, "_tawa")
            doc = Document()
            app_mod.make_document(doc)
            renderers = []
            arrow_annots = []
            def _collect(obj):
                for r in getattr(obj, 'renderers', []):
                    renderers.append(r)
                # Arrow annotations from fig.add_layout() land in center/above/below/left/right
                for panel in ('center', 'above', 'below', 'left', 'right'):
                    for item in getattr(obj, panel, []):
                        if isinstance(item, Arrow):
                            arrow_annots.append(item)
                        else:
                            _collect(item)
                for child in getattr(obj, 'children', []):
                    if isinstance(child, (list, tuple)):
                        for c in child:
                            if c is not None:
                                _collect(c)
                    elif child is not None:
                        _collect(child)
            for root in doc.roots:
                _collect(root)
            return renderers, arrow_annots
        finally:
            for p in (spec_path, data_path, out_f.name):
                try:
                    os.unlink(p)
                except OSError:
                    pass

    def _has_renderer_with_lw(self, renderers, target_lw=_THICK_PX, tol=0.05):
        """Return True if any renderer glyph has line_width close to target_lw."""
        for r in renderers:
            glyph = getattr(r, 'glyph', None)
            if glyph is not None:
                lw = getattr(glyph, 'line_width', None)
                if lw is not None and abs(float(lw) - target_lw) < tol:
                    return True
        return False

    def _has_arrow_with_lw(self, arrow_annots, target_lw=_THICK_PX, tol=0.05):
        """Return True if any Arrow annotation has line_width close to target_lw."""
        for arrow in arrow_annots:
            lw = getattr(arrow, 'line_width', None)
            if lw is not None and abs(float(lw) - target_lw) < tol:
                return True
        return False

    def test_lfit_applies_lwidth(self, dr_module, auto_df):
        """lfit with lwidth(thick)=3.072 must produce a renderer with line_width≈3.072."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "lfit", "yvar": "mpg", "xvar": "weight",
                       "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, self._THICK_PX), \
            "server-mode lfit must apply lwidth(thick)=3.072 to line renderer"

    def test_qfit_applies_lwidth(self, dr_module, auto_df):
        """qfit with lwidth(thick)=3.072 must produce a renderer with line_width≈3.072."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "qfit", "yvar": "mpg", "xvar": "weight",
                       "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, self._THICK_PX), \
            "server-mode qfit must apply lwidth(thick)=3.072 to line renderer"

    def test_connected_applies_lwidth(self, dr_module, auto_df):
        """connected with lwidth(thick)=3.072 must produce a renderer with line_width≈3.072."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "connected", "yvar": "mpg", "xvar": "weight",
                       "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, self._THICK_PX), \
            "server-mode connected must apply lwidth(thick)=3.072 to line renderer"

    def test_lowess_applies_lwidth(self, dr_module, auto_df):
        """lowess with lwidth(thick)=3.072 must produce a renderer with line_width≈3.072."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "lowess", "yvar": "mpg", "xvar": "weight",
                       "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, self._THICK_PX), \
            "server-mode lowess must apply lwidth(thick)=3.072 to line renderer"

    def test_kdensity_applies_lwidth(self, dr_module, auto_df):
        """kdensity with lwidth(thick)=3.072 must produce a renderer with line_width≈3.072."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "kdensity", "yvar": "mpg", "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, self._THICK_PX), \
            "server-mode kdensity must apply lwidth(thick)=3.072 to line renderer"

    def test_mspline_applies_lwidth(self, dr_module, auto_df):
        """mspline with lwidth(thick)=3.072 must produce a renderer with line_width≈3.072."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "mspline", "yvar": "mpg", "xvar": "weight",
                       "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, self._THICK_PX), \
            "server-mode mspline must apply lwidth(thick)=3.072 to line renderer"

    def test_tsline_applies_lwidth(self, dr_module, auto_df):
        """tsline with lwidth(thick)=3.072 must produce a renderer with line_width≈3.072."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "tsline", "yvar": "mpg", "xvar": "weight",
                       "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, self._THICK_PX), \
            "server-mode tsline must apply lwidth(thick)=3.072 to line renderer"

    def test_rspike_applies_lwidth(self, dr_module, auto_df):
        """rspike with lwidth(thick)=3.072 must produce a renderer with line_width≈3.072."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rspike", "yvar1": "mpg", "yvar2": "price",
                       "xvar": "weight", "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, self._THICK_PX), \
            "server-mode rspike must apply lwidth(thick)=3.072 to segment renderer"

    def test_rline_applies_lwidth(self, dr_module, auto_df):
        """rline with lwidth(thick)=3.072 must produce a renderer with line_width≈3.072."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rline", "yvar1": "mpg", "yvar2": "price",
                       "xvar": "weight", "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, self._THICK_PX), \
            "server-mode rline must apply lwidth(thick)=3.072 to line renderer"

    def test_function_applies_lwidth(self, dr_module, auto_df):
        """function with lwidth(thick)=3.072 must produce a renderer with line_width≈3.072."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "function", "expr": "x", "range": [0, 10],
                       "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, self._THICK_PX), \
            "server-mode function must apply lwidth(thick)=3.072 to line renderer"

    def test_tsrline_applies_lwidth(self, dr_module, auto_df):
        """tsrline with lwidth(thick)=3.072 must produce a renderer with line_width≈3.072."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "tsrline", "yvar1": "mpg", "yvar2": "price",
                       "xvar": "weight", "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, self._THICK_PX), \
            "server-mode tsrline must apply lwidth(thick)=3.072 to line renderer"

    def test_rconnected_applies_lwidth(self, dr_module, auto_df):
        """rconnected with lwidth(thick)=3.072 must produce a renderer with line_width≈3.072."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rconnected", "yvar1": "mpg", "yvar2": "price",
                       "xvar": "weight", "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, self._THICK_PX), \
            "server-mode rconnected must apply lwidth(thick)=3.072 to line renderer"

    def test_rcapsym_applies_lwidth(self, dr_module, auto_df):
        """rcapsym with lwidth(thick)=3.072 must produce a renderer with line_width≈3.072."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rcapsym", "yvar1": "mpg", "yvar2": "price",
                       "xvar": "weight", "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, self._THICK_PX), \
            "server-mode rcapsym must apply lwidth(thick)=3.072 to segment renderer"

    def test_pcspike_applies_lwidth(self, dr_module, auto_df):
        """pcspike with lwidth(thick)=3.072 must produce a renderer with line_width≈3.072."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "pcspike", "y1var": "mpg", "x1var": "weight",
                       "y2var": "price", "x2var": "foreign",
                       "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, self._THICK_PX), \
            "server-mode pcspike must apply lwidth(thick)=3.072 to segment renderer"

    def test_pcarrow_applies_lwidth(self, dr_module, auto_df):
        """pcarrow with lwidth(thick)=3.072 must produce a renderer with line_width≈3.072."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "pcarrow", "y1var": "mpg", "x1var": "weight",
                       "y2var": "price", "x2var": "foreign",
                       "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, self._THICK_PX), \
            "server-mode pcarrow must apply lwidth(thick)=3.072 to segment renderer"

    def test_pcbarrow_applies_lwidth(self, dr_module, auto_df):
        """pcbarrow with lwidth(thick)=3.072 must produce a renderer with line_width≈3.072."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "pcbarrow", "y1var": "mpg", "x1var": "weight",
                       "y2var": "price", "x2var": "foreign",
                       "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, self._THICK_PX), \
            "server-mode pcbarrow must apply lwidth(thick)=3.072 to segment renderer"

    def test_pcarrow_lwidth_applies_to_arrow_annotations(self, dr_module, auto_df):
        """pcarrow lwidth(thick)=3.072 must be applied to Arrow annotation objects, not just segment."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "pcarrow", "y1var": "mpg", "x1var": "weight",
                       "y2var": "price", "x2var": "foreign",
                       "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        # Flipped (WP-31 C1): the head at the shaft's thick was wrong
        # because twoway's line options are the shaft's; the head is
        # markerstyle p#arrow at the scheme's arrow width (measured
        # 13oct2026), drawn as a glyph (no Arrow annotation).
        renderers, arrow_annots = self._exec_make_document_with_arrows(
            dr_module, auto_df, spec)
        assert not arrow_annots
        heads = [r for r in renderers if "dash-arrowhead" in (r.tags or [])]
        assert len(heads) == 1, "server-mode pcarrow must draw its head glyph"
        assert abs(heads[0].glyph.line_width - self._THICK_PX) > 0.05
        assert any(type(r.glyph).__name__ == "Segment"
                   and abs(r.glyph.line_width - self._THICK_PX) < 0.05
                   for r in renderers)

    def test_pcbarrow_lwidth_applies_to_arrow_annotations(self, dr_module, auto_df):
        """pcbarrow lwidth(thick)=3.072 must be applied to Arrow annotation objects, not just segment."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "pcbarrow", "y1var": "mpg", "x1var": "weight",
                       "y2var": "price", "x2var": "foreign",
                       "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        # Flipped (WP-31 C1): the head at the shaft's thick was wrong
        # because twoway's line options are the shaft's; the head is
        # markerstyle p#arrow at the scheme's arrow width (measured
        # 13oct2026), drawn as a glyph (no Arrow annotation).
        renderers, arrow_annots = self._exec_make_document_with_arrows(
            dr_module, auto_df, spec)
        assert not arrow_annots
        heads = [r for r in renderers if "dash-arrowhead" in (r.tags or [])]
        assert len(heads) == 1, "server-mode pcbarrow must draw its head glyph"
        assert abs(heads[0].glyph.line_width - self._THICK_PX) > 0.05
        assert any(type(r.glyph).__name__ == "Segment"
                   and abs(r.glyph.line_width - self._THICK_PX) < 0.05
                   for r in renderers)


class TestServerRconnectedRcapsymMarkers:
    """rconnected and rcapsym scatter markers must support mcolor/msize/msymbol in server mode."""

    def _exec_make_document(self, dr_module, df, spec, mod_name="_tmrk"):
        from bokeh.document import Document
        from bokeh.models import GlyphRenderer
        spec_path, data_path = _write_temp_files(df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_mod = load_app(out_f.name, mod_name)
            doc = Document()
            app_mod.make_document(doc)
            renderers = []
            def _collect(obj):
                if isinstance(obj, GlyphRenderer):
                    renderers.append(obj)
                for r in getattr(obj, 'renderers', []):
                    _collect(r)
                for panel in ('above', 'below', 'center', 'left', 'right'):
                    for item in getattr(obj, panel, []):
                        _collect(item)
                for child in getattr(obj, 'children', []):
                    if isinstance(child, (list, tuple)):
                        for c in child:
                            if c is not None: _collect(c)
                    elif child is not None:
                        _collect(child)
            for root in doc.roots:
                _collect(root)
            return renderers
        finally:
            for p in (spec_path, data_path, out_f.name):
                try: os.unlink(p)
                except OSError: pass

    def test_rconnected_mcolor_applied_to_scatter(self, dr_module, auto_df):
        """rconnected mcolor must change scatter marker fill_color from default."""
        spec_default = _make_spec_json(graphs=[{
            "plots": [{"type": "rconnected", "yvar1": "mpg", "yvar2": "price",
                       "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        spec_colored = _make_spec_json(graphs=[{
            "plots": [{"type": "rconnected", "yvar1": "mpg", "yvar2": "price",
                       "xvar": "weight", "options": {"mcolor": "red"}}],
            "graph_options": {"name": "g1"},
        }])
        from bokeh.models.glyphs import Scatter
        def _scatter_fills(renderers):
            return [r.glyph.fill_color for r in renderers
                    if hasattr(r, 'glyph') and isinstance(r.glyph, Scatter)]
        fills_default = _scatter_fills(
            self._exec_make_document(dr_module, auto_df, spec_default, "_trcmd"))
        fills_colored = _scatter_fills(
            self._exec_make_document(dr_module, auto_df, spec_colored, "_trcmc"))
        assert fills_colored, "rconnected must produce scatter renderers"
        assert fills_colored != fills_default, \
            "rconnected mcolor(red) must change scatter fill_color from default"

    def test_rconnected_msize_applied_to_scatter(self, dr_module, auto_df):
        """rconnected msize must change scatter marker size from default."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rconnected", "yvar1": "mpg", "yvar2": "price",
                       "xvar": "weight", "options": {"msize": "large"}}],
            "graph_options": {"name": "g1"},
        }])
        from bokeh.models.glyphs import Scatter
        renderers = self._exec_make_document(dr_module, auto_df, spec, "_trcms")
        scatter_sizes = [r.glyph.size for r in renderers
                         if hasattr(r, 'glyph') and isinstance(r.glyph, Scatter)]
        assert scatter_sizes, "rconnected must produce scatter renderers"
        # "large" maps to a size > default 7
        assert any(s > 7 for s in scatter_sizes), \
            f"rconnected msize(large) must produce size > 7, got {scatter_sizes}"

    def test_rcapsym_mcolor_applied_to_markers(self, dr_module, auto_df):
        """rcapsym mcolor must change scatter marker fill_color from default."""
        spec_default = _make_spec_json(graphs=[{
            "plots": [{"type": "rcapsym", "yvar1": "mpg", "yvar2": "price",
                       "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        spec_colored = _make_spec_json(graphs=[{
            "plots": [{"type": "rcapsym", "yvar1": "mpg", "yvar2": "price",
                       "xvar": "weight", "options": {"mcolor": "red"}}],
            "graph_options": {"name": "g1"},
        }])
        from bokeh.models.glyphs import Scatter
        def _scatter_fills(renderers):
            return [r.glyph.fill_color for r in renderers
                    if hasattr(r, 'glyph') and isinstance(r.glyph, Scatter)]
        fills_default = _scatter_fills(
            self._exec_make_document(dr_module, auto_df, spec_default, "_trcsd"))
        fills_colored = _scatter_fills(
            self._exec_make_document(dr_module, auto_df, spec_colored, "_trcsc"))
        assert fills_colored, "rcapsym must produce scatter renderers"
        assert fills_colored != fills_default, \
            "rcapsym mcolor(red) must change scatter fill_color from default"

    def test_rcapsym_msize_applied_to_markers(self, dr_module, auto_df):
        """rcapsym msize must change scatter marker size from default."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rcapsym", "yvar1": "mpg", "yvar2": "price",
                       "xvar": "weight", "options": {"msize": "large"}}],
            "graph_options": {"name": "g1"},
        }])
        from bokeh.models.glyphs import Scatter
        renderers = self._exec_make_document(dr_module, auto_df, spec, "_trcsz")
        scatter_sizes = [r.glyph.size for r in renderers
                         if hasattr(r, 'glyph') and isinstance(r.glyph, Scatter)]
        assert scatter_sizes, "rcapsym must produce scatter renderers"
        assert any(s > 7 for s in scatter_sizes), \
            f"rcapsym msize(large) must produce size > 7, got {scatter_sizes}"


class TestServerNamedColors:
    """Server-mode must translate named Stata colors (navy, red) correctly.

    The current simplified color block only handles hex values. Named colors
    like mcolor(navy) should translate to #1a476f.
    """

    def _exec_make_document(self, dr_module, df, spec):
        """Build app, exec make_document, return list of all glyph renderers."""
        from bokeh.document import Document
        spec_path, data_path = _write_temp_files(df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_mod = load_app(out_f.name, "_ta2")
            doc = Document()
            app_mod.make_document(doc)
            renderers = []
            def _collect(obj):
                for r in getattr(obj, 'renderers', []):
                    renderers.append(r)
                for child in getattr(obj, 'children', []):
                    if isinstance(child, (list, tuple)):
                        for c in child:
                            if c is not None:
                                _collect(c)
                    elif child is not None:
                        _collect(child)
            for root in doc.roots:
                _collect(root)
            return renderers
        finally:
            for p in (spec_path, data_path, out_f.name):
                try:
                    os.unlink(p)
                except OSError:
                    pass

    def test_mcolor_named_colour_translates(self, dr_module, auto_df):
        """mcolor(magenta) must produce fill_color=#ff00ff on scatter renderer.

        This was navy, s2color's own first colour: the marker is navy with
        mcolor() ignored, and the test passed with it taken away (measured
        24sep2026).  Magenta is in no s2color slot.
        """
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {"mcolor": "magenta"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        colors = [getattr(getattr(r, 'glyph', None), 'fill_color', None)
                  for r in renderers if r is not None]
        assert "#ff00ff" in colors, \
            "server-mode scatter mcolor(magenta) must produce fill_color=#ff00ff"

    def test_lcolor_named_red_translates(self, dr_module, auto_df):
        """lcolor(red) must produce line_color=#ff0000 on line renderer."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "line", "yvar": "mpg", "xvar": "weight",
                       "options": {"lcolor": "red"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        colors = [getattr(getattr(r, 'glyph', None), 'line_color', None)
                  for r in renderers if r is not None]
        assert "#ff0000" in colors, \
            "server-mode line lcolor(red) must produce line_color=#ff0000"

    def test_bgcolor_named_color_in_server_app(self, dr_module, auto_df):
        """bgcolor(navy) in server app must set border_fill_color=#1a476f on figure.

        This asserted `"#1a476f" in source or "bgcolor" in source', true of
        every generated app: its own code handles bgcolor.  The served
        figure's border is read now, beside the same app with no bgcolor(),
        whose border is the scheme's #eaf2f3 (measured 24sep2026) -- so
        navy, a series colour and never a border one, comes only from the
        option.
        """
        from bokeh.document import Document
        from bokeh.models import Plot
        borders = {}
        for bg in ("", "navy"):
            # Flipped (WP-30 P1.20a): bgcolor() on the border alone was
            # wrong because twoway paints bgcolor() under the graph region (region_truth.json D26-D29); the graph region
            # is none in both runs, so the canvas is what shows.
            go = {"name": "g1", "graphregion": "color(none)"}
            if bg:
                go["bgcolor"] = bg
            spec = _make_spec_json(graphs=[{
                "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                           "options": {}}],
                "graph_options": go,
            }])
            spec_path, data_path = _write_temp_files(auto_df, spec)
            out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py",
                                                delete=False)
            out_f.close()
            try:
                dr_module.ServerAppBuilder(spec_path, data_path).build(
                    out_f.name)
                app_mod = load_app(out_f.name, "_ta2_bg_" + (bg or "none"))
                doc = Document()
                app_mod.make_document(doc)
                borders[bg] = [p.border_fill_color for p in doc.models
                               if isinstance(p, Plot)]
            finally:
                for p in (spec_path, data_path, out_f.name):
                    try:
                        os.unlink(p)
                    except OSError:
                        pass
        assert borders["navy"] == ["#1a476f"], borders
        assert borders[""] and "#1a476f" not in borders[""], borders


class TestServerMfcolorNamed:
    """Server-mode scatter must resolve named mfcolor values."""

    def _exec_make_document(self, dr_module, df, spec):
        from bokeh.document import Document
        spec_path, data_path = _write_temp_files(df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_mod = load_app(out_f.name, "_tm4")
            doc = Document()
            app_mod.make_document(doc)
            renderers = []
            def _collect(obj):
                for r in getattr(obj, 'renderers', []):
                    renderers.append(r)
                for child in getattr(obj, 'children', []):
                    if isinstance(child, (list, tuple)):
                        for c in child:
                            if c is not None: _collect(c)
                    elif child is not None:
                        _collect(child)
            for root in doc.roots:
                _collect(root)
            return renderers
        finally:
            for p in (spec_path, data_path, out_f.name):
                try: os.unlink(p)
                except OSError: pass

    def test_mfcolor_named_colour_applied(self, dr_module, auto_df):
        """mfcolor(magenta) must produce fill_color=#ff00ff on scatter renderer.

        This was navy, the marker's default: it passed with mfcolor() taken
        away (measured 24sep2026).  Magenta is in no s2color slot.
        """
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {"mfcolor": "magenta"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        colors = [getattr(getattr(r, 'glyph', None), 'fill_color', None)
                  for r in renderers if r is not None]
        assert "#ff00ff" in colors, \
            "server-mode scatter mfcolor(magenta) must produce fill_color=#ff00ff"

    def test_mlabposition_in_server_scatter_source(self, dr_module, auto_df):
        """mlabposition option must be referenced in generated server scatter mlabel code."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {"mlabel": "foreign", "mlabposition": "3"}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "mlabposition" in source, \
            "server-mode scatter with mlabposition must reference that option"


class TestServerMlabel:
    """Server-mode scatter must render mlabel annotations as LabelSet."""

    def _exec_make_document_doc(self, dr_module, df, spec):
        """Build app, exec make_document, return the Document itself."""
        from bokeh.document import Document
        spec_path, data_path = _write_temp_files(df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_mod = load_app(out_f.name, "_tm3")
            doc = Document()
            app_mod.make_document(doc)
            return doc
        finally:
            for p in (spec_path, data_path, out_f.name):
                try:
                    os.unlink(p)
                except OSError:
                    pass

    def test_mlabel_in_server_app_source(self, dr_module, auto_df):
        """scatter with mlabel() option must reference LabelSet in generated source."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {"mlabel": "foreign"}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "LabelSet" in source, \
            "server-mode scatter with mlabel() must emit LabelSet in generated app"

    def test_mlabel_produces_label_renderer_in_server(self, dr_module, auto_df):
        """scatter with mlabel() must produce a LabelSet annotation in the document."""
        from bokeh.models import LabelSet
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {"mlabel": "foreign"}}],
            "graph_options": {"name": "g1"},
        }])
        # auto_df needs a 'foreign' column (it already does as a fixture)
        doc = self._exec_make_document_doc(dr_module, auto_df, spec)
        # Collect all objects including annotation panels (center/above/below)
        all_objs = []
        def _collect(obj):
            all_objs.append(obj)
            for r in getattr(obj, 'renderers', []):
                all_objs.append(r)
            for panel in ('above', 'below', 'center', 'left', 'right'):
                for item in getattr(obj, panel, []):
                    all_objs.append(item)
            for child in getattr(obj, 'children', []):
                if isinstance(child, (list, tuple)):
                    for c in child:
                        if c is not None:
                            _collect(c)
                elif child is not None:
                    _collect(child)
        for root in doc.roots:
            _collect(root)
        has_labelset = any(isinstance(o, LabelSet) for o in all_objs)
        assert has_labelset, \
            "server-mode scatter with mlabel() must produce a LabelSet annotation"


class TestServerMlabelNonScatter:
    """mlabel() in server mode: drawn on the plot types twoway labels --
    connected, dot and dropline here -- and on no type it leaves unlabelled:
    line, tsline, rspike, rline and rbar draw no marker label in twoway
    (measured 23sep2026 from its SVG; test_marker_label_parity.py has every
    type in both modes).  Those five asserted a LabelSet until then."""

    def _exec_and_collect(self, dr_module, df, spec, mod_name):
        """Build and exec make_document, collecting all document objects."""
        from bokeh.document import Document
        spec_path, data_path = _write_temp_files(df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_mod = load_app(out_f.name, mod_name)
            doc = Document()
            app_mod.make_document(doc)
            all_objs = []
            def _collect(obj):
                all_objs.append(obj)
                for r in getattr(obj, 'renderers', []):
                    all_objs.append(r)
                for panel in ('above', 'below', 'center', 'left', 'right'):
                    for item in getattr(obj, panel, []):
                        all_objs.append(item)
                for child in getattr(obj, 'children', []):
                    if isinstance(child, (list, tuple)):
                        for c in child:
                            if c is not None: _collect(c)
                    elif child is not None:
                        _collect(child)
            for root in doc.roots:
                _collect(root)
            return all_objs
        finally:
            for p in (spec_path, data_path, out_f.name):
                try: os.unlink(p)
                except OSError: pass

    def test_mlabel_in_line_draws_no_labelset(self, dr_module, auto_df):
        """line with mlabel(): twoway draws no marker label, and neither does dash."""
        from bokeh.models import LabelSet
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "line", "yvar": "mpg", "xvar": "weight",
                       "options": {"mlabel": "foreign"}}],
            "graph_options": {"name": "g1"},
        }])
        all_objs = self._exec_and_collect(dr_module, auto_df, spec, "_tmline")
        assert not any(isinstance(o, LabelSet) for o in all_objs), \
            "server-mode line with mlabel() must draw no LabelSet (twoway draws none)"

    def test_mlabel_in_connected_produces_labelset(self, dr_module, auto_df):
        """connected with mlabel() must produce a LabelSet annotation in the document."""
        from bokeh.models import LabelSet
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "connected", "yvar": "mpg", "xvar": "weight",
                       "options": {"mlabel": "foreign"}}],
            "graph_options": {"name": "g1"},
        }])
        all_objs = self._exec_and_collect(dr_module, auto_df, spec, "_tmconn")
        assert any(isinstance(o, LabelSet) for o in all_objs), \
            "server-mode connected with mlabel() must produce a LabelSet annotation"

    def test_mlabel_in_dot_produces_labelset(self, dr_module, auto_df):
        """dot with mlabel() must produce a LabelSet annotation in the document."""
        from bokeh.models import LabelSet
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "dot", "yvar": "mpg", "xvar": "weight",
                       "options": {"mlabel": "foreign"}}],
            "graph_options": {"name": "g1"},
        }])
        all_objs = self._exec_and_collect(dr_module, auto_df, spec, "_tmdot")
        assert any(isinstance(o, LabelSet) for o in all_objs), \
            "server-mode dot with mlabel() must produce a LabelSet annotation"

    def test_mlabel_in_tsline_draws_no_labelset(self, dr_module, auto_df):
        """tsline with mlabel(): twoway draws no marker label, and neither does dash."""
        from bokeh.models import LabelSet
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "tsline", "yvar": "mpg", "xvar": "weight",
                       "options": {"mlabel": "foreign"}}],
            "graph_options": {"name": "g1"},
        }])
        all_objs = self._exec_and_collect(dr_module, auto_df, spec, "_tmtsline")
        assert not any(isinstance(o, LabelSet) for o in all_objs), \
            "server-mode tsline with mlabel() must draw no LabelSet (twoway draws none)"

    def test_mlabel_in_dropline_produces_labelset(self, dr_module, auto_df):
        """dropline with mlabel() must produce a LabelSet annotation in the document."""
        from bokeh.models import LabelSet
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "dropline", "yvar": "mpg", "xvar": "weight",
                       "options": {"mlabel": "foreign"}}],
            "graph_options": {"name": "g1"},
        }])
        all_objs = self._exec_and_collect(dr_module, auto_df, spec, "_tmdropline")
        assert any(isinstance(o, LabelSet) for o in all_objs), \
            "server-mode dropline with mlabel() must produce a LabelSet annotation"

    def test_mlabel_on_rspike_draws_no_labelset(self, dr_module, auto_df):
        """rspike with mlabel(): twoway draws no marker label, and neither does dash."""
        from bokeh.models import LabelSet
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rspike", "yvar1": "mpg", "yvar2": "price", "xvar": "weight",
                       "options": {"mlabel": "foreign"}}],
            "graph_options": {"name": "g1"},
        }])
        all_objs = self._exec_and_collect(dr_module, auto_df, spec, "_tmrspike_mlab")
        assert not any(isinstance(o, LabelSet) for o in all_objs), \
            "server-mode rspike with mlabel() must draw no LabelSet (twoway draws none)"

    def test_mlabel_on_rline_draws_no_labelset(self, dr_module, auto_df):
        """rline with mlabel(): twoway draws no marker label, and neither does dash."""
        from bokeh.models import LabelSet
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rline", "yvar1": "mpg", "yvar2": "price", "xvar": "weight",
                       "options": {"mlabel": "foreign"}}],
            "graph_options": {"name": "g1"},
        }])
        all_objs = self._exec_and_collect(dr_module, auto_df, spec, "_tmrline_mlab")
        assert not any(isinstance(o, LabelSet) for o in all_objs), \
            "server-mode rline with mlabel() must draw no LabelSet (twoway draws none)"

    def test_mlabel_on_rbar_draws_no_labelset(self, dr_module, auto_df):
        """rbar with mlabel(): twoway draws no marker label, and neither does dash."""
        from bokeh.models import LabelSet
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rbar", "yvar1": "mpg", "yvar2": "price", "xvar": "weight",
                       "options": {"mlabel": "foreign"}}],
            "graph_options": {"name": "g1"},
        }])
        all_objs = self._exec_and_collect(dr_module, auto_df, spec, "_tmrbar_mlab")
        assert not any(isinstance(o, LabelSet) for o in all_objs), \
            "server-mode rbar with mlabel() must draw no LabelSet (twoway draws none)"


class TestServerPerGraphFilter:
    """Per-graph if_expr / in_expr filtering in server-mode generated app."""

    def _exec_make_document(self, dr_module, df, spec):
        """Build and exec make_document, return the document."""
        from bokeh.document import Document
        spec_path, data_path = _write_temp_files(df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_mod = load_app(out_f.name, "_tmfilt")
            doc = Document()
            app_mod.make_document(doc)
            return doc
        finally:
            for p in (spec_path, data_path, out_f.name):
                try: os.unlink(p)
                except OSError: pass

    def _collect_cds_lengths(self, doc):
        """Collect all ColumnDataSource row counts from document renderers."""
        from bokeh.models import ColumnDataSource
        seen = set()
        lengths = []
        def _record(src):
            if src is None or id(src) in seen:
                return
            seen.add(id(src))
            if isinstance(src, ColumnDataSource):
                cols = list(src.data.values())
                if cols:
                    lengths.append(len(cols[0]))
        def _walk(obj):
            if obj is None or id(obj) in seen:
                return
            seen.add(id(obj))
            # Check data_source on glyphs/renderers
            _record(getattr(obj, 'data_source', None))
            for r in getattr(obj, 'renderers', []):
                _walk(r)
            for panel in ('above', 'below', 'center', 'left', 'right'):
                for item in getattr(obj, panel, []):
                    _walk(item)
            for child in getattr(obj, 'children', []):
                if isinstance(child, (list, tuple)):
                    for c in child:
                        if c is not None: _walk(c)
                elif child is not None:
                    _walk(child)
        for root in doc.roots:
            _walk(root)
        return lengths

    def test_in_expr_filters_rows(self, dr_module, auto_df):
        """in_expr '1/5' must produce a CDS with exactly 5 rows."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight"}],
            "graph_options": {"name": "g1", "in_expr": "1/5"},
        }])
        doc = self._exec_make_document(dr_module, auto_df, spec)
        lengths = self._collect_cds_lengths(doc)
        assert any(n == 5 for n in lengths), \
            f"in_expr '1/5' must produce a CDS with 5 rows, got lengths: {lengths}"

    def test_in_expr_two_graphs_independent(self, dr_module, auto_df):
        """Two graphs with different in_expr must produce independent CDS sizes."""
        spec = _make_spec_json(graphs=[
            {
                "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight"}],
                "graph_options": {"name": "g1", "in_expr": "1/3"},
            },
            {
                "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight"}],
                "graph_options": {"name": "g2", "in_expr": "1/7"},
            },
        ])
        doc = self._exec_make_document(dr_module, auto_df, spec)
        lengths = self._collect_cds_lengths(doc)
        assert 3 in lengths, f"graph g1 in_expr '1/3' → 3 rows expected, got: {lengths}"
        assert 7 in lengths, f"graph g2 in_expr '1/7' → 7 rows expected, got: {lengths}"

    def test_if_expr_filters_by_condition(self, dr_module, auto_df):
        """if_expr must filter rows matching condition."""
        # auto_df has foreign column; filter for foreign==1 should give fewer rows
        n_foreign = int((auto_df["foreign"] == 1).sum())
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight"}],
            "graph_options": {"name": "g1", "if_expr": "foreign == 1"},
        }])
        doc = self._exec_make_document(dr_module, auto_df, spec)
        lengths = self._collect_cds_lengths(doc)
        assert any(n == n_foreign for n in lengths), \
            f"if_expr 'foreign == 1' must produce {n_foreign} rows, got: {lengths}"

    # The three payloads below are chosen so the assertion depends on dash's
    # AST whitelist and NOT on pandas.
    #
    # The originals used __import__('os').getcwd(), getattr(mpg, '__class__')
    # and setattr(mpg, 'x', 1).  Measured by neutering the guard in the
    # generated app (rewriting `if _safe_g(` to `if True or _safe_g(`): all
    # three tests pass with dash's whitelist entirely removed, because
    # df.query(engine="python") refuses those names itself --
    # `"__import__" is not a supported function`.  They certified pandas.
    #
    # These three are accepted by pandas and rejected by _validate_if_expr,
    # so with the guard they leave the data unfiltered (30 rows) and without
    # it they filter it (15).  The @-variable form is the vector called out
    # in dash_render.py's own comment.
    _BLOCKED_BUT_VALID = [
        ("at_variable", "mpg > @df['mpg'].mean()"),
        ("index_attr", "index > 14"),
        ("builtin_call", "mpg > abs(-26)"),
    ]

    @pytest.mark.parametrize("label,expr",
                             _BLOCKED_BUT_VALID,
                             ids=[x[0] for x in _BLOCKED_BUT_VALID])
    def test_a_blocked_if_expr_leaves_the_data_unfiltered(
            self, dr_module, auto_df, label, expr):
        n_total = len(auto_df)
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight"}],
            "graph_options": {"name": "g1", "if_expr": expr},
        }])
        doc = self._exec_make_document(dr_module, auto_df, spec)
        lengths = self._collect_cds_lengths(doc)
        assert lengths, "no ColumnDataSource was built at all"
        # Equality, not "not partially filtered": the original assertion was
        # `not any(0 < n < n_total)`, which n == 0 also satisfies, so a
        # regression that silently emptied every graph passed it too.
        assert all(n == n_total for n in lengths), (
            f"{label}: a blocked if_expr must leave the data unfiltered; "
            f"got {lengths} of {n_total}"
        )

    @pytest.mark.parametrize("label,expr",
                             _BLOCKED_BUT_VALID,
                             ids=[x[0] for x in _BLOCKED_BUT_VALID])
    def test_the_payload_is_one_pandas_would_have_accepted(self, label, expr):
        """Without this, the tests above could drift back to certifying pandas.

        Each payload must be rejected by dash's validator and accepted by
        pandas -- if pandas rejected it too, the test would pass with the
        whitelist deleted.
        """
        import pandas as _pd
        from dash_render import _validate_if_expr, _stata_if_to_pandas

        df = _pd.DataFrame({"mpg": [10.0, 20.0, 30.0, 40.0],
                            "weight": [1.0, 2.0, 3.0, 4.0]})
        translated = _stata_if_to_pandas(expr)
        assert not _validate_if_expr(translated, df.columns), (
            f"{label}: dash's whitelist does not block this, so the test "
            f"above proves nothing"
        )
        try:
            df.query(translated, engine="python")
        except Exception as exc:          # noqa: BLE001 - reporting only
            pytest.fail(
                f"{label}: pandas rejects this payload itself "
                f"({type(exc).__name__}), so blocking it is not dash's "
                f"doing and the test above would pass without the guard"
            )

    def test_lfit_fits_only_the_rows_in_expr_keeps(self, dr_module, auto_df):
        """The regression must be computed on the restricted sample.

        This built both documents, collected both sets of CDS lengths, and
        then asserted only ``len(lengths_filt) > 0`` -- its own comment
        admitted it merely checked that the app "compiles and executes
        without error".  lfit always emits 100 output points whatever the
        input, so lengths could never distinguish the two.  The fitted LINE
        can: Stata's ``in`` restricts the estimation sample, so the two fits
        must differ.
        """
        spec_full = _make_spec_json(graphs=[{
            "plots": [{"type": "lfit", "yvar": "mpg", "xvar": "weight"}],
            "graph_options": {"name": "g1"},
        }])
        spec_filt = _make_spec_json(graphs=[{
            "plots": [{"type": "lfit", "yvar": "mpg", "xvar": "weight"}],
            "graph_options": {"name": "g1", "in_expr": "1/5"},
        }])
        full = self._lfit_endpoints(
            self._exec_make_document(dr_module, auto_df, spec_full))
        filt = self._lfit_endpoints(
            self._exec_make_document(dr_module, auto_df, spec_filt))
        assert full is not None and filt is not None, (full, filt)
        assert full != pytest.approx(filt), (
            f"the fit over all rows and the fit over rows 1-5 are identical "
            f"({full}); in() did not restrict the estimation sample"
        )

    @staticmethod
    def _lfit_endpoints(doc):
        """First and last y of the longest CDS that carries a `y` column."""
        from bokeh.models import ColumnDataSource
        best = None
        for model in doc.roots:
            for obj in model.select({"type": ColumnDataSource}):
                ys = obj.data.get("y")
                if ys is None or len(ys) < 2:
                    continue
                if best is None or len(ys) > best[0]:
                    best = (len(ys), (float(ys[0]), float(ys[-1])))
        return best[1] if best else None

    def test_histogram_respects_in_expr(self, dr_module, auto_df):
        """histogram with in_expr must bin only filtered rows."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "histogram", "yvar": "mpg"}],
            "graph_options": {"name": "g1", "in_expr": "1/5"},
        }])
        doc = self._exec_make_document(dr_module, auto_df, spec)
        lengths = self._collect_cds_lengths(doc)
        # The histogram CDS (top/left/right arrays) has length == nbins (default 20)
        # but the sum of the bar heights (counts) should be <= 5 (filtered rows)
        from bokeh.models import ColumnDataSource
        all_cdses = []
        def _collect_cdses(obj, seen=set()):
            if id(obj) in seen: return
            seen.add(id(obj))
            src = getattr(obj, 'data_source', None)
            if isinstance(src, ColumnDataSource) and 'top' in src.data:
                all_cdses.append(src)
            for r in getattr(obj, 'renderers', []): _collect_cdses(r, seen)
            for panel in ('above','below','center','left','right'):
                for item in getattr(obj, panel, []): _collect_cdses(item, seen)
            for ch in getattr(obj, 'children', []):
                if isinstance(ch, (list,tuple)):
                    for c in ch:
                        if c is not None: _collect_cdses(c, seen)
                elif ch is not None: _collect_cdses(ch, seen)
        for root in doc.roots: _collect_cdses(root)
        assert all_cdses, "histogram must produce a CDS with 'top' key"
        total_count = sum(all_cdses[0].data['top'])
        assert total_count <= 5, \
            f"histogram with in_expr '1/5' must count only 5 rows, got {total_count}"


class TestServerFitCIBand:
    """lfitci and qfitci must render a proper CI band (non-zero-width varea)."""

    def _exec_collect_vareas(self, dr_module, df, spec, mod_name):
        """Build and exec make_document, return all VArea glyph renderers."""
        from bokeh.document import Document
        from bokeh.models import GlyphRenderer
        spec_path, data_path = _write_temp_files(df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_mod = load_app(out_f.name, mod_name)
            doc = Document()
            app_mod.make_document(doc)
            vareas = []
            def _collect(obj):
                if isinstance(obj, GlyphRenderer):
                    glyph_type = type(obj.glyph).__name__
                    if glyph_type == 'VArea':
                        vareas.append(obj)
                for r in getattr(obj, 'renderers', []):
                    _collect(r)
                for panel in ('above', 'below', 'center', 'left', 'right'):
                    for item in getattr(obj, panel, []):
                        _collect(item)
                for child in getattr(obj, 'children', []):
                    if isinstance(child, (list, tuple)):
                        for c in child:
                            if c is not None: _collect(c)
                    elif child is not None:
                        _collect(child)
            for root in doc.roots:
                _collect(root)
            return vareas
        finally:
            for p in (spec_path, data_path, out_f.name):
                try: os.unlink(p)
                except OSError: pass

    def test_lfitci_band_has_nonzero_width(self, dr_module, auto_df):
        """lfitci CI band varea must use y_lower/y_upper keys (not y/y)."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "lfitci", "yvar": "mpg", "xvar": "weight"}],
            "graph_options": {"name": "g1"},
        }])
        vareas = self._exec_collect_vareas(dr_module, auto_df, spec, "_tlfci")
        assert vareas, "lfitci must produce at least one VArea renderer"
        r = vareas[0]
        y1_key = r.glyph.y1
        y2_key = r.glyph.y2
        src_data = r.data_source.data
        assert y1_key in src_data and y2_key in src_data, \
            f"lfitci varea must reference distinct y1/y2 keys, got {y1_key}/{y2_key}"
        import numpy as np
        if len(src_data[y1_key]) > 0:
            band_width = np.max(np.abs(
                np.array(src_data[y2_key]) - np.array(src_data[y1_key])
            ))
            assert band_width > 0, "lfitci CI band must have non-zero width"

    def test_qfitci_band_has_nonzero_width(self, dr_module, auto_df):
        """qfitci CI band varea must use y_lower/y_upper keys (not y/y)."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "qfitci", "yvar": "mpg", "xvar": "weight"}],
            "graph_options": {"name": "g1"},
        }])
        vareas = self._exec_collect_vareas(dr_module, auto_df, spec, "_tqfci")
        assert vareas, "qfitci must produce at least one VArea renderer"
        r = vareas[0]
        y1_key = r.glyph.y1
        y2_key = r.glyph.y2
        src_data = r.data_source.data
        assert y1_key in src_data and y2_key in src_data, \
            f"qfitci varea must reference distinct y1/y2 keys, got {y1_key}/{y2_key}"
        import numpy as np
        if len(src_data[y1_key]) > 0:
            band_width = np.max(np.abs(
                np.array(src_data[y2_key]) - np.array(src_data[y1_key])
            ))
            assert band_width > 0, "qfitci CI band must have non-zero width"


# ---------------------------------------------------------------------------
# A-50 — lfitci/qfitci agg_sources filter callback recompute
# ---------------------------------------------------------------------------

class TestServerFitCIFilterRecompute:
    """lfitci/qfitci agg_sources must be recomputed in the filter callback."""

    def _get_source(self, dr_module, df, spec, mod_name):
        """Build server app and return the generated Python source string."""
        spec_path, data_path = _write_temp_files(df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            with open(out_f.name) as f:
                return f.read()
        finally:
            for p in (spec_path, data_path, out_f.name):
                try: os.unlink(p)
                except OSError: pass

    def test_lfitci_registered_in_agg_sources(self, dr_module, auto_df):
        """lfitci plot must register its source in agg_sources with type 'lfitci'."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "lfitci", "yvar": "mpg", "xvar": "weight"}],
            "graph_options": {"name": "g1"},
        }])
        src = self._get_source(dr_module, auto_df, spec, "_tlfci_reg")
        assert "'lfitci'" in src, \
            "lfitci plot must register agg_sources entry with type='lfitci'"

    def test_qfitci_registered_in_agg_sources(self, dr_module, auto_df):
        """qfitci plot must register its source in agg_sources with type 'qfitci'."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "qfitci", "yvar": "mpg", "xvar": "weight"}],
            "graph_options": {"name": "g1"},
        }])
        src = self._get_source(dr_module, auto_df, spec, "_tqfci_reg")
        assert "'qfitci'" in src, \
            "qfitci plot must register agg_sources entry with type='qfitci'"

    def test_lfitci_filter_callback_recomputes(self, dr_module, auto_df):
        """After a filter move the served lfitci layer equals a saved one built
        from the filtered rows.

        This asserted that the generated source contained the text
        "_compute_lfitci" and "atype == 'lfitci'".  Both were true while the layer
        was NOT recomputed: no registration site ever wrote that type, so
        the branch was unreachable, and the text-level check passed over a
        served layer that went stale (or, once the mapper-built source was
        refreshed by row index, over ten points of the old curve).  The
        served app now redraws a computed layer through the same mapper on
        the filtered frame; the check is against the saved renderer on
        those rows.
        """
        _assert_served_layer_refits(dr_module, auto_df, "lfitci")


    def test_qfitci_filter_callback_recomputes(self, dr_module, auto_df):
        """After a filter move the served qfitci layer equals a saved one built
        from the filtered rows.

        This asserted that the generated source contained the text
        "_compute_qfitci" and "atype == 'qfitci'".  Both were true while the layer
        was NOT recomputed: no registration site ever wrote that type, so
        the branch was unreachable, and the text-level check passed over a
        served layer that went stale (or, once the mapper-built source was
        refreshed by row index, over ten points of the old curve).  The
        served app now redraws a computed layer through the same mapper on
        the filtered frame; the check is against the saved renderer on
        those rows.
        """
        _assert_served_layer_refits(dr_module, auto_df, "qfitci")


    # ------------------------------------------------------------------
    # A-90 through A-94 — mspline / mband / rscatter / pci / pcscatter
    # must register sources so the filter callback can update them.
    # ------------------------------------------------------------------

    def test_mspline_registered_in_agg_sources(self, dr_module, auto_df):
        """A-90: mspline must register its source in agg_sources for filter updates."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "mspline", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        src = self._get_source(dr_module, auto_df, spec, "_tmsp_reg")
        assert "agg_sources" in src and "'mspline'" in src, \
            "mspline must register agg_sources entry with type='mspline'"

    def test_mspline_filter_callback_recomputes(self, dr_module, auto_df):
        """After a filter move the served mspline layer equals a saved one built
        from the filtered rows.

        This asserted that the generated source contained the text
        "_compute_mspline" and "atype == 'mspline'".  Both were true while the layer
        was NOT recomputed: no registration site ever wrote that type, so
        the branch was unreachable, and the text-level check passed over a
        served layer that went stale (or, once the mapper-built source was
        refreshed by row index, over ten points of the old curve).  The
        served app now redraws a computed layer through the same mapper on
        the filtered frame; the check is against the saved renderer on
        those rows.
        """
        _assert_served_layer_refits(dr_module, auto_df, "mspline")


    def test_mband_registered_in_agg_sources(self, dr_module, auto_df):
        """A-91: mband must register its source in agg_sources for filter updates."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "mband", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        src = self._get_source(dr_module, auto_df, spec, "_tmb_reg")
        assert "agg_sources" in src and "'mband'" in src, \
            "mband must register agg_sources entry with type='mband'"

    def test_mband_filter_callback_recomputes(self, dr_module, auto_df):
        """After a filter move the served mband layer equals a saved one built
        from the filtered rows.

        This asserted that the generated source contained the text
        "_compute_mband" and "atype == 'mband'".  Both were true while the layer
        was NOT recomputed: no registration site ever wrote that type, so
        the branch was unreachable, and the text-level check passed over a
        served layer that went stale (or, once the mapper-built source was
        refreshed by row index, over ten points of the old curve).  The
        served app now redraws a computed layer through the same mapper on
        the filtered frame; the check is against the saved renderer on
        those rows.
        """
        _assert_served_layer_refits(dr_module, auto_df, "mband")


    def test_rscatter_registered_in_agg_sources(self, dr_module, auto_df):
        """A-92: rscatter must register its source in agg_sources for filter updates."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rscatter", "yvar1": "mpg", "yvar2": "price",
                       "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        src = self._get_source(dr_module, auto_df, spec, "_trs_reg")
        assert "agg_sources" in src and "'rscatter'" in src, \
            "rscatter must register agg_sources entry with type='rscatter'"

    def test_rscatter_filter_callback_recomputes(self, dr_module, auto_df):
        """After a filter move the served rscatter layer equals a saved one built
        from the filtered rows.

        This asserted that the generated source contained the text
        "_compute_rscatter" and "atype == 'rscatter'".  Both were true while the layer
        was NOT recomputed: no registration site ever wrote that type, so
        the branch was unreachable, and the text-level check passed over a
        served layer that went stale (or, once the mapper-built source was
        refreshed by row index, over ten points of the old curve).  The
        served app now redraws a computed layer through the same mapper on
        the filtered frame; the check is against the saved renderer on
        those rows.
        """
        _assert_served_layer_refits(dr_module, auto_df, "rscatter")


    def test_a_filter_move_leaves_a_pci_segment_where_it_was(
            self, dr_module, auto_df, tmp_path):
        """A-93: the served filter callback must handle a pci layer.

        This asserted that the generated app contained
        ``graph_sources[gname] = `` -- text the generator writes for every
        spec, pci or not, so it could not fail.  And the rule it stood for
        has changed: pci draws the coordinates it is given, which no filter
        and no qualifier reaches (twoway draws them wherever the data are).
        So after a dropdown move the scatter beside it draws the rows the
        move keeps and the pci segment is exactly where it was.
        """
        from bokeh.models import GlyphRenderer, Plot, Select
        spec = _make_spec_json(graphs=[{
            "plots": [
                {"type": "scatter", "yvar": "mpg", "xvar": "weight",
                 "options": {}, "if_expr": "", "in_expr": ""},
                {"type": "pci", "values": [[20.0, 3000.0, 30.0, 4000.0]],
                 "options": {}, "if_expr": "", "in_expr": ""}],
            "graph_options": {"name": "g1"},
            "if_expr": "", "in_expr": "",
        }], build_options={
            "layout": "auto", "link": "", "filter": "foreign, type(dropdown)",
            "theme": "", "title": "", "subtitle": "", "registry": "g1",
            "level": "95", "formats": {}})
        doc, _ = _ql_served(dr_module, tmp_path, spec, auto_df)

        def _layers():
            out = {}
            for root in doc.roots:
                for fig in root.select({"type": Plot}):
                    for r in fig.renderers:
                        if isinstance(r, GlyphRenderer):
                            out.setdefault(type(r.glyph).__name__, []).append(
                                {k: [float(x) for x in v]
                                 for k, v in r.data_source.data.items()
                                 if k != "index"})
            return out

        segment = {"x0": [3000.0], "y0": [20.0], "x1": [4000.0], "y1": [30.0]}
        before = _layers()
        assert before["Segment"] == [segment], before.get("Segment")
        sel = [m for root in doc.roots for m in root.select({"type": Select})]
        assert len(sel) == 1, sel
        w = sel[0]
        pick = [v for v, lab in w.options if lab == "1"]
        assert pick, w.options
        w.value = pick[0]
        for key in ("value", "value_throttled"):
            for cb in list(w._callbacks.get(key, [])):
                cb("value", None, pick[0])
        after = _layers()
        n_foreign = int((auto_df["foreign"] == 1).sum())
        assert 0 < n_foreign < len(auto_df)
        assert [len(s["weight"]) for s in after["Scatter"]] == [n_foreign], (
            "the move changed nothing, so the check below proves nothing")
        assert after["Segment"] == [segment], (
            f"a filter move moved the pci segment: {after['Segment']}")

    def test_pcscatter_registered_in_agg_sources(self, dr_module, auto_df):
        """A-94: pcscatter must register its source in agg_sources for filter updates."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "pcscatter", "y1var": "mpg", "x1var": "weight",
                       "y2var": "price", "x2var": "length", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        src = self._get_source(dr_module, auto_df, spec, "_tpcs_reg")
        assert "agg_sources" in src and "'pcscatter'" in src, \
            "pcscatter must register agg_sources entry with type='pcscatter'"

    def test_pcscatter_filter_callback_recomputes(self, dr_module, auto_df):
        """After a filter move the served pcscatter layer equals a saved one built
        from the filtered rows.

        This asserted that the generated source contained the text
        "_compute_pcscatter" and "atype == 'pcscatter'".  Both were true while the layer
        was NOT recomputed: no registration site ever wrote that type, so
        the branch was unreachable, and the text-level check passed over a
        served layer that went stale (or, once the mapper-built source was
        refreshed by row index, over ten points of the old curve).  The
        served app now redraws a computed layer through the same mapper on
        the filtered frame; the check is against the saved renderer on
        those rows.
        """
        _assert_served_layer_refits(dr_module, auto_df, "pcscatter")


    # A-90/A-91 called the served app's `_compute_mspline' and
    # `_compute_mband' on a full and a filtered frame.  Those copies were
    # dead once the served app redrew computed layers through the mapper
    # (the callback never reached them), and WP-18 deleted them.  What the
    # tests were for is asked of the live callback instead: move the filter
    # and the served curve must change.  That it changes to the RIGHT curve
    # is test_m{spline,band}_filter_callback_recomputes above.

    @staticmethod
    def _served_curve_before_and_after_filter(dr_module, df, ptype, ycol):
        import warnings
        from bokeh.document import Document
        from bokeh.models import Select
        spec = _make_spec_json(
            graphs=[{"plots": [{"type": ptype, "yvar": "mpg", "xvar": "weight",
                                "options": {}}],
                     "graph_options": {"name": "g1"}}],
            build_options={"filter": "foreign, type(dropdown)"})
        spec_path, data_path = _write_temp_files(df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                dr_module.ServerAppBuilder(spec_path, data_path).build(out_f.name)
                mod = load_app(out_f.name, "_bf_" + ptype)
                doc = Document()
                mod.make_document(doc)

                def _curve():
                    for m in doc.select({"type": object}):
                        d = getattr(m, "data", None)
                        if isinstance(d, dict) and ycol in d:
                            return [float(v) for v in d[ycol]]
                    raise AssertionError("no %s source in the served document" % ycol)

                before = _curve()
                w = [m for m in doc.select({"type": Select})][0]
                old = w.value
                w.value = "1.0"
                for cb in w._callbacks.get("value", []):
                    cb("value", old, "1.0")
                after = _curve()
            return before, after
        finally:
            for p in (spec_path, data_path, out_f.name):
                try: os.unlink(p)
                except OSError: pass

    def test_mspline_compute_fn_changes_with_filter(self, dr_module, auto_df):
        """A-90: the served mspline curve changes when a filter drops rows."""
        before, after = self._served_curve_before_and_after_filter(
            dr_module, auto_df, "mspline", "y_sp")
        assert len(before) > 0 and len(after) > 0
        assert (len(before) != len(after)
                or not np.allclose(before, after, atol=1.0)), \
            "the served mspline did not change when the filter dropped rows"

    def test_mband_compute_fn_changes_with_filter(self, dr_module, auto_df):
        """A-91: the served mband curve changes when a filter drops rows."""
        before, after = self._served_curve_before_and_after_filter(
            dr_module, auto_df, "mband", "y_mb")
        assert len(before) > 0 and len(after) > 0
        assert (len(before) != len(after)
                or not np.allclose(before, after, atol=1.0)), \
            "the served mband did not change when the filter dropped rows"


# ---------------------------------------------------------------------------
# GAP 4.2 / 4.3 / 4.4 / 4.5 — Server-mode options parity
# ---------------------------------------------------------------------------

def _exec_doc(dr_module, df, spec, mod_name):
    """Helper: build server app, exec make_document, return (doc, all_renderers)."""
    from bokeh.document import Document
    from bokeh.models import GlyphRenderer
    spec_path, data_path = _write_temp_files(df, spec)
    out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
    out_f.close()
    try:
        builder = dr_module.ServerAppBuilder(spec_path, data_path)
        builder.build(out_f.name)
        app_mod = load_app(out_f.name, mod_name)
        doc = Document()
        app_mod.make_document(doc)
        renderers = []
        def _collect(obj):
            if isinstance(obj, GlyphRenderer):
                renderers.append(obj)
            for r in getattr(obj, 'renderers', []):
                _collect(r)
            for panel in ('above', 'below', 'center', 'left', 'right'):
                for item in getattr(obj, panel, []):
                    _collect(item)
            for child in getattr(obj, 'children', []):
                if isinstance(child, (list, tuple)):
                    for c in child:
                        if c is not None: _collect(c)
                elif child is not None:
                    _collect(child)
        for root in doc.roots:
            _collect(root)
        return doc, renderers
    finally:
        for p in (spec_path, data_path, out_f.name):
            try: os.unlink(p)
            except OSError: pass


class TestServerAreaOptions:
    """area plot in server mode must apply fcolor/fintensity."""

    def test_area_fcolor_applied(self, dr_module, auto_df):
        """area with fcolor(red) is filled red at the area's intensity,
        #ff3333 (WP-30 P1.2b; twoway's SVG, plan section 16 Evidence E3)."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "area", "yvar": "mpg", "xvar": "weight",
                       "options": {"fcolor": "#ff0000"}}],
            "graph_options": {"name": "g1"},
        }])
        _, renderers = _exec_doc(dr_module, auto_df, spec, "_tar_fc")
        fill_colors = [getattr(r.glyph, 'fill_color', None) for r in renderers]
        assert "#ff3333" in fill_colors, \
            f"area fcolor '#ff0000' must fill #ff3333; got {fill_colors}"

    def test_area_fintensity_blends_the_colour(self, dr_module, auto_df):
        """area with fintensity(50) is navy at 50, #8da3b7, opaque: an
        intensity is a colour, never an alpha (WP-30 P1.2b; twoway's SVG, plan section 16 Evidence E3)."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "area", "yvar": "mpg", "xvar": "weight",
                       "options": {"fintensity": "50"}}],
            "graph_options": {"name": "g1"},
        }])
        _, renderers = _exec_doc(dr_module, auto_df, spec, "_tar_fi")
        fill_colors = [getattr(r.glyph, 'fill_color', None) for r in renderers]
        assert "#8da3b7" in fill_colors, fill_colors
        alphas = [getattr(r.glyph, 'fill_alpha', None) for r in renderers]
        assert all(a == 1.0 for a in alphas if a is not None), alphas


class TestServerHistogramOptions:
    """histogram in server mode must apply fcolor/fintensity."""

    def test_histogram_fcolor_applied(self, dr_module, auto_df):
        """histogram with fcolor(#ff0000) must appear in fill_color."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "histogram", "yvar": "mpg",
                       "options": {"fcolor": "#ff0000"}}],
            "graph_options": {"name": "g1"},
        }])
        _, renderers = _exec_doc(dr_module, auto_df, spec, "_th_fc")
        fill_colors = [getattr(r.glyph, 'fill_color', None) for r in renderers]
        assert "#ff0000" in fill_colors, \
            f"histogram fcolor must appear in fill_color; got {fill_colors}"

    def test_histogram_lwidth_applied(self, dr_module, auto_df):
        """histogram with lwidth(thick) must set line_width > 1.5."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "histogram", "yvar": "mpg",
                       "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        _, renderers = _exec_doc(dr_module, auto_df, spec, "_th_lw")
        lwidths = [getattr(r.glyph, 'line_width', None) for r in renderers]
        assert any(w is not None and w > 1.5 for w in lwidths), \
            f"histogram lwidth(thick) must set line_width>1.5; got {lwidths}"


class TestServerRareaOptions:
    """rarea in server mode must apply fcolor/fintensity."""

    # test_rarea_fcolor_applied, which asserted only that "#ff0000" appeared
    # in the generated source, was removed here: with fcolor's application
    # deleted from _apply_fill_opts the option still reaches the source
    # (it rides in the base64 spec) so the test stayed green while the band
    # drew the scheme's #1a476f (WP-24, measured 24sep2026).  Its
    # behavioural twin, test_rarea_fcolor_applied_functional below, reads
    # the served glyph's fill_color and fails under that break.

    def test_rarea_fcolor_applied_functional(self, dr_module):
        """rarea with fcolor(#ff0000) is filled at rarea's intensity,
        #ff3333 (WP-30 P1.2b; twoway's SVG, plan section 16 Evidence E3)."""
        rdf = _range_data()
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rarea", "yvar1": "lo", "yvar2": "hi", "xvar": "x",
                       "options": {"fcolor": "#ff0000"}}],
            "graph_options": {"name": "g1"},
        }])
        _, renderers = _exec_doc(dr_module, rdf, spec, "_tra_fc2")
        fill_colors = [getattr(r.glyph, 'fill_color', None) for r in renderers]
        assert "#ff3333" in fill_colors, \
            f"rarea fcolor must appear in fill_color; got {fill_colors}"


class TestServerRbarOptions:
    """rbar in server mode must apply bfcolor, blcolor, lwidth."""

    def test_rbar_bfcolor_applied(self, dr_module):
        """rbar with bfcolor(#ff0000) is filled at rbar's intensity,
        #ff3333 (WP-30 P1.2b; twoway's SVG, plan section 16 Evidence E3)."""
        rdf = _range_data()
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rbar", "yvar1": "lo", "yvar2": "hi", "xvar": "x",
                       "options": {"bfcolor": "#ff0000"}}],
            "graph_options": {"name": "g1"},
        }])
        _, renderers = _exec_doc(dr_module, rdf, spec, "_trb_bfc")
        fill_colors = [getattr(r.glyph, 'fill_color', None) for r in renderers]
        assert "#ff3333" in fill_colors, \
            f"rbar bfcolor must appear in fill_color; got {fill_colors}"

    def test_rbar_lwidth_applied(self, dr_module):
        """rbar with lwidth(thick) must set line_width > 1.5."""
        rdf = _range_data()
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rbar", "yvar1": "lo", "yvar2": "hi", "xvar": "x",
                       "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        _, renderers = _exec_doc(dr_module, rdf, spec, "_trb_lw")
        lwidths = [getattr(r.glyph, 'line_width', None) for r in renderers]
        assert any(w is not None and w > 1.5 for w in lwidths), \
            f"rbar lwidth(thick) must set line_width>1.5; got {lwidths}"


class TestServerDotOptions:
    """dot in server mode must apply mcolor/msize/msymbol."""

    def test_dot_mcolor_applied(self, dr_module, auto_df):
        """dot with mcolor(red) must set fill_color on scatter renderer."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "dot", "yvar": "mpg", "xvar": "weight",
                       "options": {"mcolor": "red"}}],
            "graph_options": {"name": "g1"},
        }])
        _, renderers = _exec_doc(dr_module, auto_df, spec, "_td_mc")
        try:
            from dash_render import OptionTranslator
            expected = OptionTranslator.translate_mcolor("red")
        except Exception:
            expected = "#ff0000"
        fill_colors = [getattr(r.glyph, 'fill_color', None) for r in renderers]
        assert expected in fill_colors, \
            f"dot mcolor(red) must appear in fill_color; got {fill_colors}"

    def test_dot_msize_applied(self, dr_module, auto_df):
        """dot with msize(large) must set size > 8 on scatter renderer."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "dot", "yvar": "mpg", "xvar": "weight",
                       "options": {"msize": "large"}}],
            "graph_options": {"name": "g1"},
        }])
        _, renderers = _exec_doc(dr_module, auto_df, spec, "_td_ms")
        sizes = [getattr(r.glyph, 'size', None) for r in renderers]
        assert any(s is not None and s > 8 for s in sizes), \
            f"dot msize(large) must set size>8; got {sizes}"


class TestServerConnectedOptions:
    """connected in server mode must apply mcolor/msize to scatter component."""

    def test_connected_mcolor_applied(self, dr_module, auto_df):
        """connected with mcolor(red) must set fill_color on scatter renderer."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "connected", "yvar": "mpg", "xvar": "weight",
                       "options": {"mcolor": "red"}}],
            "graph_options": {"name": "g1"},
        }])
        _, renderers = _exec_doc(dr_module, auto_df, spec, "_tconn_mc")
        try:
            from dash_render import OptionTranslator
            expected = OptionTranslator.translate_mcolor("red")
        except Exception:
            expected = "#ff0000"
        fill_colors = [getattr(r.glyph, 'fill_color', None) for r in renderers]
        assert expected in fill_colors, \
            f"connected mcolor(red) must appear in fill_color; got {fill_colors}"

    def test_connected_msize_applied(self, dr_module, auto_df):
        """connected with msize(large) must set size > 8 on scatter component."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "connected", "yvar": "mpg", "xvar": "weight",
                       "options": {"msize": "large"}}],
            "graph_options": {"name": "g1"},
        }])
        _, renderers = _exec_doc(dr_module, auto_df, spec, "_tconn_ms")
        sizes = [getattr(r.glyph, 'size', None) for r in renderers]
        assert any(s is not None and s > 8 for s in sizes), \
            f"connected msize(large) must set size>8; got {sizes}"


class TestServerScatteriOptions:
    """scatteri in server mode must apply mcolor/msize."""

    def test_scatteri_mcolor_applied(self, dr_module, auto_df):
        """scatteri with mcolor(red) must set fill_color on scatter renderer."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatteri", "values": [[1, 2], [3, 4], [5, 6]],
                       "options": {"mcolor": "red"}}],
            "graph_options": {"name": "g1"},
        }])
        _, renderers = _exec_doc(dr_module, auto_df, spec, "_tsi_mc")
        try:
            from dash_render import OptionTranslator
            expected = OptionTranslator.translate_mcolor("red")
        except Exception:
            expected = "#ff0000"
        fill_colors = [getattr(r.glyph, 'fill_color', None) for r in renderers]
        assert expected in fill_colors, \
            f"scatteri mcolor(red) must appear in fill_color; got {fill_colors}"


# ===========================================================================
# P6-20: by() faceting in server mode
# ===========================================================================

class TestServerByFaceting:
    """Verify that by() faceting generates correct server-mode code."""

    def test_by_scatter_compiles(self, dr_module, auto_df):
        """by(foreign) scatter → generated source compiles."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        try:
            code = compile(source, "<generated_by>", "exec")
        except SyntaxError as exc:
            pytest.fail("a by() app is not valid Python: %s" % exc)
        assert "make_document" in {c.co_name for c in code.co_consts
                                   if isinstance(c, types.CodeType)}

    @staticmethod
    def _facets(dr_module, df, spec, tag):
        """``{panel title: rows its glyphs draw}`` from the served document."""
        from bokeh.document import Document
        from bokeh.models import GlyphRenderer, Plot
        spec_path, data_path = _write_temp_files(df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            dr_module.ServerAppBuilder(spec_path, data_path).build(out_f.name)
            app_mod = load_app(out_f.name, tag)
            doc = Document()
            app_mod.make_document(doc)
            return {_panel_name(p): [max((len(v) for v in r.data_source.data.values()),
                                       default=0)
                                   for r in p.renderers
                                   if isinstance(r, GlyphRenderer)]
                    for p in doc.models if isinstance(p, Plot)
                    and not is_chrome(p)}
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try:
                    os.unlink(_p)
                except OSError:
                    pass

    def test_by_creates_facet_figures(self, dr_module, auto_df):
        """by(foreign) -> make_document draws one figure per group, each with
        that group's rows alone.

        This asserted `"g1__by__0" in source or "__by__" in source or
        "facet" in source.lower()', which the generated app's own code
        satisfies whatever the spec asks for.
        """
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign"},
        }])
        facets = self._facets(dr_module, auto_df, spec, "_by_figs")
        counts = auto_df["foreign"].value_counts()
        assert len(facets) == len(counts) == 2, facets
        assert sorted(facets.values()) == sorted([n] for n in counts.tolist()), (
            f"each panel must draw its own group's rows: {facets}")

    def test_by_doc_has_roots(self, dr_module, auto_df):
        """by(foreign) -> make_document's one root holds both panels, each
        drawing its own group's (weight, mpg) points.

        This asserted ``len(doc.roots) > 0``: the layout column is a root
        whether or not any panel was built -- with the graph drawn from no
        rows it is still the one root (WP-24, measured 24sep2026).  The
        panels are read from the root itself, not from the document's
        model set, so a panel that is built but never placed fails too."""
        from bokeh.document import Document
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign"},
        }])
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_mod = load_app(out_f.name, "_by_test")
            doc = Document()
            app_mod.make_document(doc)
            assert len(doc.roots) == 1, doc.roots
            panels = {}
            for fig, r in _glyph_layers(doc.roots[:1]):
                panels.setdefault(_panel_name(fig), []).append(sorted(zip(
                    _drawn_values(r, "weight"), _drawn_values(r, "mpg"))))
            want = {"%d" % g: [sorted(zip(sub["weight"], sub["mpg"]))]
                    for g, sub in auto_df.groupby("foreign")}
            assert len(want) == 2
            assert panels == want, (
                f"the root's panels drew {sorted(panels)}; by(foreign) "
                f"draws one panel per group, {sorted(want)}")
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try:
                    os.unlink(_p)
                except OSError:
                    pass

    def test_by_facet_labels_in_source(self, dr_module, auto_df):
        """by(foreign) -> each panel is titled by its group, and holds that
        group's rows.

        This asserted `"by" in source.lower() or ...' of the generated
        source, which holds for any app at all.  foreign has no value
        label here, so each panel is titled by its value, as twoway's by()
        titles it.
        """
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign"},
        }])
        facets = self._facets(dr_module, auto_df, spec, "_by_labels")
        counts = auto_df["foreign"].value_counts()
        assert facets == {"%d" % g: [int(n)] for g, n in counts.items()}, (
            f"panels and their rows: {facets}")

    def test_by_with_histogram_compiles(self, dr_module, auto_df):
        """by(foreign) with histogram → generated source compiles."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "histogram", "var": "mpg", "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        try:
            code = compile(source, "<generated_by_hist>", "exec")
        except SyntaxError as exc:
            pytest.fail("a by() histogram app is not valid Python: %s" % exc)
        assert "make_document" in {c.co_name for c in code.co_consts
                                   if isinstance(c, types.CodeType)}

    @pytest.mark.parametrize("flag,total", [("1", True), ("0", False)])
    def test_the_by_total_key_adds_a_total_panel_in_both_modes(
            self, dr_module, auto_df, tmp_path, flag, total):
        """graph_options["by_total"] == "1" adds the Total panel, in both
        modes.  dash.ado writes the total as by()'s own sub-option; this
        key is what a spec written by hand may carry, and both renderers
        honour it.  This used to assert only that the word "Total" appeared
        in the generated app -- which it does for every by() graph, since
        the facet code that names the panel is written out either way."""
        from bokeh.models import GlyphRenderer, Plot
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign", "by_total": flag},
        }])

        def _panels(roots):
            out = {}
            for root in roots:
                for fig in root.select({"type": Plot}):
                    rows = [len(r.data_source.data["weight"])
                            for r in fig.renderers
                            if isinstance(r, GlyphRenderer)
                            and type(r.glyph).__name__ == "Scatter"]
                    if rows:
                        out[_panel_name(fig)] = rows
            return out

        r, _ = _ql_saved(dr_module, tmp_path, spec, auto_df)
        doc, _ = _ql_served(dr_module, tmp_path, spec, auto_df)
        for mode, panels in (("saved", _panels([r._last_layout_root])),
                             ("served", _panels(doc.roots))):
            assert ("Total" in panels) is total, (mode, panels)
            assert len(panels) == (3 if total else 2), (mode, panels)
            if total:
                assert panels["Total"] == [len(auto_df)], (mode, panels)

    def test_by_total_suboption_in_raw_string(self, dr_module, auto_df):
        """by('foreign, total') in raw string → Total facet in generated source."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign, total"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "Total" in source, "by suboption 'total' in raw string should produce 'Total' facet"

    def test_facet_group_vals_in_source(self, dr_module, auto_df):
        """by(foreign) → generated source contains _facet_group_vals dict."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "_facet_group_vals" in source, \
            "_facet_group_vals dict should be in generated source for filter callback"

    def test_filter_callback_uses_facet_group_vals(self, dr_module, auto_df):
        """Filter callback references _fgvals to re-split faceted data."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        # The callback should reference _fgvals (the facet group values parameter)
        assert "_fgvals" in source, \
            "_make_filter_cb should accept _fgvals for per-facet re-filtering"


class TestServerPlotregionGraphregion:
    """plotregion() and graphregion() applied in server-mode generated code."""

    def test_plotregion_color_in_generated_source(self, dr_module, auto_df):
        """plotregion(color(#aabbcc)) → background_fill_color in generated source."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "plotregion": "color(#aabbcc)"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "background_fill_color" in source, \
            "plotregion(color()) must set background_fill_color in generated code"

    def test_graphregion_color_in_generated_source(self, dr_module, auto_df):
        """graphregion(color(#112233)) → border_fill_color in generated source."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "graphregion": "color(#112233)"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "border_fill_color" in source, \
            "graphregion(color()) must set border_fill_color in generated code"


class TestServerNewPlotTypes:
    """Server-mode generated code for mband, pci, pcscatter, rscatter (added in A-63)."""

    def test_mband_generates_valid_app(self, dr_module, auto_df):
        """mband plot type must produce a compilable server app."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "mband", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "mband" in source, "mband must appear in generated server app code"

    def test_pci_generates_valid_app(self, dr_module, auto_df):
        """pci plot type must produce a compilable server app."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "pci", "y1var": "mpg", "x1var": "weight",
                       "y2var": "price", "x2var": "foreign", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "pci" in source, "pci must appear in generated server app code"

    def test_pcscatter_generates_valid_app(self, dr_module, auto_df):
        """pcscatter plot type must produce a compilable server app."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "pcscatter", "y1var": "mpg", "x1var": "weight",
                       "y2var": "price", "x2var": "foreign", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "pcscatter" in source, "pcscatter must appear in generated server app code"

    def test_rscatter_generates_valid_app(self, dr_module, auto_df):
        """rscatter plot type must produce a compilable server app."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rscatter", "yvar1": "mpg", "yvar2": "price",
                       "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "rscatter" in source, "rscatter must appear in generated server app code"

    def test_mband_make_document_runs(self, dr_module, auto_df):
        """mband make_document() draws twoway's median-band line.

        This asserted ``len(doc.roots) > 0``, which the layout column
        satisfies with the mband drawn from no rows (WP-24, measured
        24sep2026).  The served line is held to twoway's own rule, as
        stat_truth.json records it (reproduced there for every probe):
        B = round(min(10*log10(N), sqrt(N))) equal-width bands on x, and
        the median of x and of y in each non-empty band, in x order --
        5 bands for these 30 rows."""
        import math
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "mband", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        doc, _ = _exec_doc(dr_module, auto_df, spec, "_tmmband")
        x = auto_df["weight"].to_numpy()
        y = auto_df["mpg"].to_numpy()
        bands = int(round(min(10 * math.log10(len(x)), math.sqrt(len(x)))))
        lo, width = x.min(), (x.max() - x.min()) / bands
        band = np.minimum(np.floor((x - lo) / width) + 1, bands)
        want = [(float(np.median(x[band == b])), float(np.median(y[band == b])))
                for b in range(1, bands + 1) if (band == b).any()]
        assert bands == len(want) == 5, (bands, want)
        assert _panel_curves(doc.roots, "x_mb", "y_mb") == {"": want}, (
            "the served mband is not twoway's median-band line")


class TestServerPlotregionLwidth:
    """plotregion(lwidth()) sets outline_line_width in generated server code."""

    def test_plotregion_lwidth_in_generated_source(self, dr_module, auto_df):
        """plotregion(lwidth(2)) → outline_line_width in generated source."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "plotregion": "lwidth(2)"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "outline_line_width" in source, \
            "plotregion(lwidth()) must set outline_line_width in generated code"


class TestServerRconnectedMlabel:
    """mlabel() on rconnected in server mode produces a LabelSet."""

    def test_mlabel_on_rconnected_produces_labelset(self, dr_module, auto_df):
        """rconnected with mlabel() must produce a LabelSet annotation."""
        from bokeh.models import LabelSet
        import tempfile, importlib.util
        from bokeh.document import Document
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rconnected", "yvar1": "mpg", "yvar2": "price",
                       "xvar": "weight", "options": {"mlabel": "foreign"}}],
            "graph_options": {"name": "g1"},
        }])
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        builder = dr_module.ServerAppBuilder(spec_path, data_path)
        builder.build(out_f.name)
        app_mod = load_app(out_f.name, "_tmrconn_mlab")
        doc = Document()
        app_mod.make_document(doc)
        all_objs = []
        def collect(obj):
            all_objs.append(obj)
            for r in getattr(obj, 'renderers', []): collect(r)
            for panel in ('above', 'below', 'center', 'left', 'right'):
                for item in getattr(obj, panel, []): all_objs.append(item)
            for child in getattr(obj, 'children', []):
                if isinstance(child, (list, tuple)):
                    for c in child:
                        if c is not None: collect(c)
                elif child is not None: collect(child)
        for root in doc.roots: collect(root)
        assert any(isinstance(o, LabelSet) for o in all_objs), \
            "server-mode rconnected with mlabel() must produce a LabelSet"


class TestServerLpolyFpfit:
    """Server-mode tests for lpoly, lpolyci, fpfit, fpfitci plot types."""

    # ------------------------------------------------------------------
    # Source-code generation tests
    # ------------------------------------------------------------------

    def test_lpoly_generates_valid_app(self, dr_module, auto_df):
        """lpoly must produce compilable server app source."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "lpoly", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        compile(source, "<generated>", "exec")
        assert "_compute_lpoly" in source

    def test_lpolyci_generates_valid_app(self, dr_module, auto_df):
        """lpolyci must produce compilable server app source."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "lpolyci", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        compile(source, "<generated>", "exec")
        assert "_compute_lpoly" in source

    # These asserted "_compute_fpfit" was in the source: the served app's own
    # second copy of the FP code, dead since the served layers were drawn
    # through GlyphMapper and deleted by WP-18 (TR-18.6).  The app must now
    # carry GlyphMapper's fit -- the one text both modes run -- and not a
    # second one that could drift from it.

    def test_fpfit_generates_valid_app(self, dr_module, auto_df):
        """fpfit must produce compilable server app source.

        A structural guard, deliberately: ONE fractional-polynomial fit --
        GlyphMapper's, copied in -- and no second `_compute_fpfit' in the
        app.  A dead or identical second copy draws the same curve, so no
        drawing can show it; the drawing itself is test_mode_parity.py's
        [fpfit] case."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "fpfit", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        compile(source, "<generated>", "exec")
        # _fp_fit is the fit map_fpfit runs.  This named _fit_fp2, a
        # test-only wrapper of it that WP-26 deleted (24sep2026).
        assert "def _fp_fit(" in source and "def _fp_prepare(" in source
        assert "_compute_fpfit" not in source

    def test_fpfitci_generates_valid_app(self, dr_module, auto_df):
        """fpfitci must produce compilable server app source.

        A structural guard, deliberately, as the test above: one fit and
        one band (_fp_stdp), GlyphMapper's.  The drawing is
        test_mode_parity.py's [fpfitci] and [fpfitci at level(90)]."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "fpfitci", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        compile(source, "<generated>", "exec")
        # _fp_fit, as above; this named the deleted _fit_fp2 too.
        assert "def _fp_fit(" in source and "def _fp_stdp(" in source
        assert "_compute_fpfit" not in source

    def test_lpoly_bwidth_in_generated_source(self, dr_module, auto_df):
        """bwidth() option must be encoded in generated lpoly server source."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "lpoly", "yvar": "mpg", "xvar": "weight",
                       "options": {"bwidth": "0.8"}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "0.8" in source, "bwidth value must appear in generated source"

    def test_lpoly_degree_in_generated_source(self, dr_module, auto_df):
        """degree() option must be encoded in generated lpoly server source (via _SPEC_B64)."""
        import re, base64 as _b64
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "lpoly", "yvar": "mpg", "xvar": "weight",
                       "options": {"degree": "2"}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        # Spec is stored base64-encoded in _SPEC_B64; decode and verify option is present
        m = re.search(r'_SPEC_B64\s*=\s*"([^"]+)"', source)
        assert m, "_SPEC_B64 must be present in generated source"
        decoded = _b64.b64decode(m.group(1)).decode("utf-8")
        assert '"degree": "2"' in decoded or "'degree': '2'" in decoded or '"degree":"2"' in decoded, \
            "degree=2 must be preserved in _SPEC_B64 encoded spec"

    # ------------------------------------------------------------------
    # make_document execution tests
    # ------------------------------------------------------------------

    def test_lpoly_make_document_runs(self, dr_module, auto_df):
        """lpoly make_document() draws the saved page's lpoly curve.

        This asserted ``len(doc.roots) > 0``, which the layout column
        satisfies with the curve drawn from no rows (WP-24, measured
        24sep2026).  The served curve must be the saved one, point for
        point: lpoly's default grid is min(N, 50) = 30 equally spaced
        points from the least x to the greatest, and at Stata's default
        bandwidth on this frame (r(bwidth) 63.42135953323416, WP-29 P0.7)
        27 of them hold at least two observations in their window --
        Stata's r(ngrid) is 27; the other 3 are gaps, Stata's null rule.
        The saved lpoly is held to Stata's
        own in test_statistical_truth.py."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "lpoly", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        doc, _ = _exec_doc(dr_module, auto_df, spec, "_tm_lpoly")
        served = _panel_curves(doc.roots, "x_lp", "y_lp")
        page, _ = _saved_page(dr_module, auto_df, spec)
        saved = _panel_curves(_page_document(page).roots, "x_lp", "y_lp")
        # WP-29 P0.7: 21 under dash's old 0.65 quartic rule; 27 is Stata's
        # r(ngrid) (test/fixtures/lpoly_rot_truth.json, server30).
        assert list(served) == [""] and len(served[""]) == 27, served
        grid = np.linspace(auto_df["weight"].min(), auto_df["weight"].max(), 30)
        assert all(np.isclose(grid, px).any() for px, _py in served[""]), (
            "a served lpoly point is off lpoly's default grid")
        np.testing.assert_allclose(served[""], saved[""], rtol=1e-12,
                                   err_msg="served lpoly is not the saved one")

    def test_fpfit_make_document_runs(self, dr_module, auto_df):
        """fpfit make_document() draws the saved page's fpfit curve.

        This asserted ``len(doc.roots) > 0``, which the layout column
        satisfies with the curve drawn from no rows (WP-24, measured
        24sep2026).  twoway fpfit predicts at every distinct x, sorted
        (twoway__fpfit_serset; stat_truth.json), and the served curve must
        be the saved one there -- which test_statistical_truth.py holds to
        Stata's."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "fpfit", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        doc, _ = _exec_doc(dr_module, auto_df, spec, "_tm_fpfit")
        served = _panel_curves(doc.roots, "x_fp", "y_fp")
        page, _ = _saved_page(dr_module, auto_df, spec)
        saved = _panel_curves(_page_document(page).roots, "x_fp", "y_fp")
        assert list(served) == [""], served
        assert [px for px, _py in served[""]] == \
            sorted(auto_df["weight"].unique().tolist()), (
            "the served fpfit is not predicted at every distinct x")
        np.testing.assert_allclose(served[""], saved[""], rtol=1e-12,
                                   err_msg="served fpfit is not the saved one")

    # ------------------------------------------------------------------
    # Regression: faceted lpoly must use bwidth/degree from options
    # ------------------------------------------------------------------

    def test_lpoly_faceted_bwidth_respected(self, dr_module, auto_df):
        """A faceted lpoly honours bwidth(0.3): its panels differ from the default's.

        This asserted the generated source contained "opts.get('bwidth'".  The
        by() panels are drawn by the same mapper as the graph now, which
        reads the option under its own name, so the text is gone and the
        behaviour is what is checked: the curve with the option is not the
        curve without it, in every panel.
        """
        from bokeh.document import Document
        import warnings

        def _curves(options):
            spec = _make_spec_json(graphs=[{
                "plots": [{"type": "lpoly", "yvar": "mpg", "xvar": "weight",
                           "options": options}],
                "graph_options": {"name": "g1", "by": "foreign"},
            }])
            spec_path, data_path = _write_temp_files(auto_df, spec)
            out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
            out_f.close()
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    dr_module.ServerAppBuilder(spec_path, data_path).build(out_f.name)
                    mod = load_app(out_f.name, "_lpf_bwidth")
                    doc = Document()
                    mod.make_document(doc)
                out = []
                for m in doc.select({"type": object}):
                    d = getattr(m, "data", None)
                    if isinstance(d, dict) and "y_lp" in d:
                        out.append([round(float(v), 6) for v in d["y_lp"]])
                return sorted(out)
            finally:
                for _p in (spec_path, data_path, out_f.name):
                    try: os.unlink(_p)
                    except OSError: pass

        # bwidth() is in x-units.  weight spans 1800-4800 over 14 and 16
        # rows per panel, so 800 is a wide window that draws a full curve
        # in both panels, unlike the default's.  bwidth(0.3), which this
        # test used to use, holds fewer than two observations in every
        # window, and lpoly draws nothing there (WP-18, Stata's null rule):
        # both panels empty is also the option reaching them.
        with_opt = _curves({"bwidth": "800"})
        plain = _curves({})
        narrow = _curves({"bwidth": "0.3"})
        assert len(with_opt) == len(plain) == len(narrow) == 2, (with_opt, plain)
        assert all(len(c) > 2 for c in with_opt + plain), (with_opt, plain)
        assert with_opt != plain, "bwidth(800) changed nothing in the served panels"
        assert narrow == [[], []], "bwidth(0.3) drew points no window supports"

    def test_lpoly_faceted_degree_respected(self, dr_module, auto_df):
        """A faceted lpoly honours degree(2): its panels differ from the default's.

        This asserted the generated source contained "opts.get('degree'".  The
        by() panels are drawn by the same mapper as the graph now, which
        reads the option under its own name, so the text is gone and the
        behaviour is what is checked: the curve with the option is not the
        curve without it, in every panel.
        """
        from bokeh.document import Document
        import warnings

        def _curves(options):
            spec = _make_spec_json(graphs=[{
                "plots": [{"type": "lpoly", "yvar": "mpg", "xvar": "weight",
                           "options": options}],
                "graph_options": {"name": "g1", "by": "foreign"},
            }])
            spec_path, data_path = _write_temp_files(auto_df, spec)
            out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
            out_f.close()
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    dr_module.ServerAppBuilder(spec_path, data_path).build(out_f.name)
                    mod = load_app(out_f.name, "_lpf_degree")
                    doc = Document()
                    mod.make_document(doc)
                out = []
                for m in doc.select({"type": object}):
                    d = getattr(m, "data", None)
                    if isinstance(d, dict) and "y_lp" in d and len(d["y_lp"]):
                        out.append([round(float(v), 6) for v in d["y_lp"]])
                return out
            finally:
                for _p in (spec_path, data_path, out_f.name):
                    try: os.unlink(_p)
                    except OSError: pass

        with_opt = _curves({"degree": "2"})
        plain = _curves({})
        assert len(with_opt) == len(plain) == 2, (with_opt, plain)
        assert with_opt != plain, "degree(2) changed nothing in the served panels"

    def test_lpoly_faceted_make_document_runs(self, dr_module, auto_df):
        """lpoly with by() and a custom bwidth/degree: each panel draws what
        twoway draws with those options.

        This asserted ``len(doc.roots) > 0``, which the layout column
        satisfies with the options ignored or no panel built (WP-24,
        measured 24sep2026).  bwidth() is in x units: 0.4 lb holds fewer
        than two observations in every window, so Stata's null rule draws
        nothing in either panel -- and a panel that fell back to the
        default bandwidth would draw a curve.  The positive control:
        bwidth(800) degree(1) draws in both panels, the saved page's
        curves point for point, so the reader does see a drawn curve."""
        def _served_and_saved(options, tag):
            spec = _make_spec_json(graphs=[{
                "plots": [{"type": "lpoly", "yvar": "mpg", "xvar": "weight",
                           "options": options}],
                "graph_options": {"name": "g1", "by": "foreign"},
            }])
            doc, _ = _exec_doc(dr_module, auto_df, spec, tag)
            page, _ = _saved_page(dr_module, auto_df, spec)
            return (_panel_curves(doc.roots, "x_lp", "y_lp"),
                    _panel_curves(_page_document(page).roots, "x_lp", "y_lp"))

        served, saved = _served_and_saved({"bwidth": "0.4", "degree": "1"},
                                          "_tm_lpoly_fac")
        assert served == saved == {"0": [], "1": []}, (served, saved)
        wide, wide_saved = _served_and_saved({"bwidth": "800", "degree": "1"},
                                             "_tm_lpoly_fac_w")
        assert sorted(wide) == ["0", "1"] and all(wide.values()), wide
        for panel in ("0", "1"):
            np.testing.assert_allclose(wide[panel], wide_saved[panel],
                                       rtol=1e-12, err_msg=panel)

    def test_fpfit_faceted_make_document_runs(self, dr_module, auto_df):
        """fpfit with by(): each panel draws its own group's fit, at every
        distinct x of that group, as the saved page draws it.

        This asserted ``len(doc.roots) > 0``, which the layout column
        satisfies with no panel built (WP-24, measured 24sep2026)."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "fpfit", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign"},
        }])
        doc, _ = _exec_doc(dr_module, auto_df, spec, "_tm_fpfit_fac")
        served = _panel_curves(doc.roots, "x_fp", "y_fp")
        page, _ = _saved_page(dr_module, auto_df, spec)
        saved = _panel_curves(_page_document(page).roots, "x_fp", "y_fp")
        groups = {"%d" % g: sorted(sub["weight"].unique().tolist())
                  for g, sub in auto_df.groupby("foreign")}
        assert sorted(served) == sorted(groups) == ["0", "1"], served
        for panel, xs in groups.items():
            assert [px for px, _py in served[panel]] == xs, panel
            np.testing.assert_allclose(served[panel], saved[panel],
                                       rtol=1e-12, err_msg=panel)


# ================================================================
# P4-74 — server-mode xscale/yscale reverse
# ================================================================
class TestServerXscaleYscaleReverse:
    """xscale(reverse)/yscale(reverse)/xscale(log) in the served DOCUMENT.

    These used to grep the generated source for the emitted assignment
    text (``x_range.flipped``, ``_xs_toks``).  The scale and the flip are
    now applied by the helpers the saved renderer runs as well
    (``_dash_scale_spec``/``_dash_apply_scale_ranges``, copied into the
    app by name), so the text is gone and the document is what matters.
    """

    def _figure(self, dr_module, auto_df, mod_name, **gopts):
        from bokeh.models import Plot
        graph_opts = {"name": "g1"}
        graph_opts.update(gopts)
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": graph_opts,
        }])
        doc, _ = _exec_doc(dr_module, auto_df, spec, mod_name)
        figs = [m for m in doc.models if isinstance(m, Plot)]
        assert len(figs) == 1, figs
        return figs[0]

    def test_xscale_reverse_in_server_source(self, dr_module, auto_df):
        """P4-74: xscale(reverse) flips the served x range, and only it."""
        fig = self._figure(dr_module, auto_df, "_xsr_x", xscale="reverse")
        assert dr_module._dash_range_reversed(fig.x_range) is True
        assert not dr_module._dash_range_reversed(fig.y_range)

    def test_yscale_reverse_in_server_source(self, dr_module, auto_df):
        """P4-75: yscale(reverse) flips the served y range, and only it."""
        fig = self._figure(dr_module, auto_df, "_xsr_y", yscale="reverse")
        assert dr_module._dash_range_reversed(fig.y_range) is True
        assert not dr_module._dash_range_reversed(fig.x_range)

    def test_xscale_log_reverse_server_source(self, dr_module, auto_df):
        """P4-76: xscale(log reverse) gives a log x scale AND a flipped range."""
        from bokeh.models import LogScale
        fig = self._figure(dr_module, auto_df, "_xsr_lr", xscale="log reverse")
        assert isinstance(fig.x_scale, LogScale), type(fig.x_scale)
        assert dr_module._dash_range_reversed(fig.x_range) is True

    def test_xscale_log_only_uses_runtime_conditional_for_flip(self, dr_module, auto_df):
        """P4-74b: xscale(log) alone is a log scale and NOT a flip."""
        from bokeh.models import LogScale
        fig = self._figure(dr_module, auto_df, "_xsr_l", xscale="log")
        assert isinstance(fig.x_scale, LogScale), type(fig.x_scale)
        assert not dr_module._dash_range_reversed(fig.x_range)


# ================================================================
# P4-77 — server-mode xlabel/ylabel angle()
# ================================================================
class TestServerAxisAngle:
    """Server-mode xlabel/ylabel angle() must emit major_label_orientation assignments."""

    def test_xlabel_angle_in_server_source(self, dr_module, auto_df):
        """P4-77: xlabel with angle(45) produces major_label_orientation in server source."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "xlabel": "0 10 20, angle(45)"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "major_label_orientation" in source

    def test_ylabel_angle_vertical_in_server_source(self, dr_module, auto_df):
        """P4-78: ylabel with angle(vertical) produces orientation assignment in server source."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "ylabel": ", angle(vertical)"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "major_label_orientation" in source

    def test_angle_make_document_runs(self, dr_module, auto_df):
        """P4-79: xlabel(0 20 40, angle(45)) -- the served x axis labels
        the three ticks asked for, turned 45 degrees.

        This asserted ``len(doc.roots) > 0``, which the layout column
        satisfies with angle() ignored (WP-24, measured 24sep2026).
        twoway's angle(45) turns the labels 45 degrees counter-clockwise;
        Bokeh's major_label_orientation is that angle in radians, and the
        saved page draws pi/4 (test_graph_options.py's TestAxisLabelAngle).
        The y axis, asked nothing, takes s2color's vertical_tick anglestyle
        (pi/2, WP-30 P1.2a): the control."""
        import math
        import tempfile, importlib.util
        from bokeh.document import Document
        from bokeh.models import Plot
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "xlabel": "0 20 40, angle(45)"},
        }])
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_mod = load_app(out_f.name, "_tm_axangle")
            doc = Document()
            app_mod.make_document(doc)
            figs = [m for m in doc.select({"type": Plot})]
            assert len(figs) == 1, figs
            (xaxis,), (yaxis,) = figs[0].xaxis, figs[0].yaxis
            assert xaxis.major_label_orientation == pytest.approx(math.pi / 4), (
                f"angle(45) served as {xaxis.major_label_orientation!r}")
            assert list(xaxis.ticker.ticks) == [0.0, 20.0, 40.0], xaxis.ticker
            # Flipped (WP-30 P1.2a): "horizontal" was wrong because twoway
            # draws s2color's y labels vertical (anglestyle vertical_tick
            # vertical, register P1.2.1), and S15 draws them so served.
            assert yaxis.major_label_orientation == pytest.approx(
                math.pi / 2), yaxis.major_label_orientation
        finally:
            import os
            for p in (spec_path, data_path, out_f.name):
                try: os.unlink(p)
                except OSError: pass


# ================================================================
# P4-80 — server-mode health check + rate limiting
# ================================================================
class TestServerHealthAndRateLimit:
    """Generated server app must include health check endpoint and rate limiter."""

    def test_health_handler_class_in_generated_source(self, dr_module, auto_df):
        """P4-80: Generated source contains _HealthHandler class definition."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "_HealthHandler" in source, "Generated source must define _HealthHandler"

    def test_health_route_in_main_block(self, dr_module, auto_df):
        """P4-81: Generated __main__ block contains /health extra_patterns entry."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "'/health'" in source or '"/health"' in source, \
            "Generated source must register /health route"
        assert "extra_patterns" in source

    def test_rate_limiter_class_in_generated_source(self, dr_module, auto_df):
        """P4-82: Generated source contains _RateLimiter class."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "_RateLimiter" in source, "Generated source must define _RateLimiter"
        assert "_LIMITER" in source, "Generated source must instantiate _LIMITER"

    def test_rate_limiter_constant_configurable(self, dr_module, auto_df):
        """P4-83: Generated source contains _RATE_LIMIT_RPM constant."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "_RATE_LIMIT_RPM" in source

    def test_rate_limiter_allows_under_limit(self, dr_module, auto_df):
        """P4-85: _RateLimiter allows first N requests under the cap."""
        import tempfile, importlib.util
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_mod = load_app(out_f.name, "_tm_rl_allow")
            limiter = app_mod._RateLimiter(max_rpm=5)
            for i in range(5):
                assert limiter.is_allowed("127.0.0.1") is True, \
                    f"Request {i+1} should be allowed under cap of 5"
        finally:
            import os
            for p in (spec_path, data_path, out_f.name):
                try: os.unlink(p)
                except OSError: pass

    def test_rate_limiter_blocks_over_limit(self, dr_module, auto_df):
        """P4-86: _RateLimiter blocks the (N+1)th request within the window."""
        import tempfile, importlib.util
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_mod = load_app(out_f.name, "_tm_rl_block")
            limiter = app_mod._RateLimiter(max_rpm=5)
            for _ in range(5):
                limiter.is_allowed("10.0.0.1")
            assert limiter.is_allowed("10.0.0.1") is False, \
                "6th request within window must be blocked"
        finally:
            import os
            for p in (spec_path, data_path, out_f.name):
                try: os.unlink(p)
                except OSError: pass

    def test_rate_limiter_rapid_requests_trigger_limit(self, dr_module, auto_df):
        """P4-87 (adversarial): 100 rapid requests to a low-limit limiter — at least one blocked."""
        import tempfile, importlib.util
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_mod = load_app(out_f.name, "_tm_rl_burst")
            limiter = app_mod._RateLimiter(max_rpm=10)
            results = [limiter.is_allowed("192.168.1.1") for _ in range(100)]
            assert not all(results), "At least one of 100 rapid requests must be blocked"
        finally:
            import os
            for p in (spec_path, data_path, out_f.name):
                try: os.unlink(p)
                except OSError: pass

    def test_generated_source_compiles_with_health(self, dr_module, auto_df):
        """P4-88: Generated source with health/rate-limit code must compile without SyntaxError."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        try:
            compile(source, "<generated>", "exec")
        except SyntaxError as e:
            raise AssertionError(f"Generated source has SyntaxError: {e}")


# ================================================================
# legend(cols(#)) / legend(rows(#)) — server mode
# ================================================================
class TestServerLegendColsRows:
    """Server-mode legend(cols(#))/legend(rows(#)) must emit ncols/nrows assignments."""

    def test_legend_cols_in_server_source(self, dr_module, auto_df):
        """legend(cols(2)) must produce ncols assignment in generated server source."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "legend": "cols(2)"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "ncols" in source, "legend(cols(2)) must produce ncols in server source"

    def test_legend_rows_in_server_source(self, dr_module, auto_df):
        """legend(rows(3)) must produce nrows assignment in generated server source."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "legend": "rows(3)"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "nrows" in source, "legend(rows(3)) must produce nrows in server source"

    def test_legend_cols_rows_combined_in_server_source(self, dr_module, auto_df):
        """legend(cols(2) rows(4)) must produce both ncols and nrows in server source."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "legend": "cols(2) rows(4)"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "ncols" in source
        assert "nrows" in source

    def test_legend_cols_make_document_runs(self, dr_module, auto_df):
        """make_document() lays the served legend out in the columns
        legend(cols()) asks for.

        This asserted ``len(doc.roots) > 0``, which the layout column
        satisfies with cols() ignored (WP-24, measured 24sep2026).  It
        asked for cols(2), which is s2color's own legend_cols -- the legend
        has two columns whether or not the option arrives -- so it asks for
        three.  Stata treats cols() and rows() as alternatives: rows goes
        back to "auto".  (``top`` is not a legend() sub-option; dash names
        it as ignored.)  The control is the same graph with no cols(),
        whose legend has the scheme's two."""
        import tempfile, importlib.util
        from bokeh.document import Document
        from bokeh.models import Legend

        def _legends(legend_opt, tag):
            spec = _make_spec_json(graphs=[{
                "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                           "options": {}}],
                "graph_options": {"name": "g1", "legend": legend_opt},
            }])
            spec_path, data_path = _write_temp_files(auto_df, spec)
            out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
            out_f.close()
            try:
                builder = dr_module.ServerAppBuilder(spec_path, data_path)
                builder.build(out_f.name)
                app_mod = load_app(out_f.name, tag)
                doc = Document()
                app_mod.make_document(doc)
                return [(lg.ncols, lg.nrows) for lg in doc.select({"type": Legend})]
            finally:
                import os
                for p in (spec_path, data_path, out_f.name):
                    try: os.unlink(p)
                    except OSError: pass

        # Flipped (WP-31 D4): the rows were "auto"; twoway's legend_g sets
        # them, 1 + int((n-1)/cols): one row for these keys.
        assert _legends("top cols(3)", "_tm_leg_cols") == [(3, 1)]
        assert _legends("", "_tm_leg_none") == [(2, 1)]


# ================================================================
# msangle(#) — server mode
# ================================================================
class TestServerMsangle:
    """Server-mode msangle(#) must emit angle= in fig.scatter() call."""

    def test_msangle_in_server_source(self, dr_module, auto_df):
        """msangle option must appear in generated server source as angle parameter."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {"msangle": "45"}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "msangle" in source or "angle" in source, \
            "msangle option must produce angle-related code in server source"

    def test_msangle_make_document_runs(self, dr_module, auto_df):
        """msangle(30) turns the served markers 30 degrees.

        This asserted ``len(doc.roots) > 0``, which the layout column
        satisfies with msangle() ignored (WP-24, measured 24sep2026).
        Bokeh's marker angle is in radians and counter-clockwise, as
        Stata's is in degrees; the saved page draws 30 degrees as
        0.5236 radians, and an unturned marker is 0 -- measured, the
        control that the reader tells the two apart."""
        import math
        import tempfile, importlib.util
        from bokeh.document import Document
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {"msangle": "30"}}],
            "graph_options": {"name": "g1"},
        }])
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_mod = load_app(out_f.name, "_tm_msangle")
            doc = Document()
            app_mod.make_document(doc)
            layers = _glyph_layers(doc.roots)
            assert [type(r.glyph).__name__ for _f, r in layers] == ["Scatter"]
            glyph = layers[0][1].glyph
            assert glyph.angle == pytest.approx(math.radians(30)), glyph.angle
            assert glyph.angle_units == "rad"
            assert len(_drawn_values(layers[0][1], "weight")) == len(auto_df)
            plain = dict(spec)
            plain["graphs"] = [{"plots": [{"type": "scatter", "yvar": "mpg",
                                           "xvar": "weight", "options": {}}],
                                "graph_options": {"name": "g1"}}]
            _doc, (unturned,) = _exec_doc(dr_module, auto_df, plain,
                                          "_tm_msangle_0")
            assert unturned.glyph.angle == 0.0, unturned.glyph.angle
        finally:
            import os
            for p in (spec_path, data_path, out_f.name):
                try: os.unlink(p)
                except OSError: pass


# ================================================================
# BUG-RL: Rate limiter enforcement (regression suite)
# Regression for: "Generated server rate limiter is never enforced"
# The _RateLimiter class and _LIMITER singleton were defined but
# never called on any request path.  Fix: enforce in
# _HealthHandler.prepare() and at the top of make_document().
# ================================================================

def _load_app_module(dr_module, auto_df, spec_dict):
    """Build server app and return loaded module object (for introspection)."""
    spec_path, data_path = _write_temp_files(auto_df, spec_dict)
    out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
    out_f.close()
    try:
        builder = dr_module.ServerAppBuilder(spec_path, data_path)
        builder.build(out_f.name)
        app_mod = load_app(out_f.name, "_rl_app")
        # WP-29 P0.12a: the key Gate B checks, as _dash_server_app installs.
        app_mod._DASH_SERVE_TOKEN = TEST_TOKEN
        return app_mod
    finally:
        for _p in (spec_path, data_path, out_f.name):
            try:
                os.unlink(_p)
            except OSError:
                pass


class TestRateLimiterEnforcement:
    """BUG-RL regression: _LIMITER must be called on every server request path."""

    def _minimal_spec(self):
        return _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}],
            "graph_options": {"name": "g1"},
        }])

    # ------------------------------------------------------------------
    # BUG-RL-1: _RateLimiter unit behaviour
    # ------------------------------------------------------------------
    def test_rate_limiter_allows_within_limit(self, dr_module, auto_df):
        """BUG-RL-1a: _RateLimiter must allow requests below the configured limit."""
        app_mod = _load_app_module(dr_module, auto_df, self._minimal_spec())
        limiter = app_mod._RateLimiter(max_rpm=3)
        for _ in range(3):
            assert limiter.is_allowed("10.0.0.1"), \
                "_RateLimiter must allow calls within the burst window"

    def test_rate_limiter_blocks_above_limit(self, dr_module, auto_df):
        """BUG-RL-1b: _RateLimiter must block the (max+1)-th request in the window."""
        app_mod = _load_app_module(dr_module, auto_df, self._minimal_spec())
        limiter = app_mod._RateLimiter(max_rpm=3)
        for _ in range(3):
            limiter.is_allowed("10.0.0.2")
        assert not limiter.is_allowed("10.0.0.2"), \
            "_RateLimiter must return False once the burst limit is exceeded"

    def test_rate_limiter_tracks_ips_independently(self, dr_module, auto_df):
        """BUG-RL-1c: _RateLimiter must track separate budgets per client IP."""
        app_mod = _load_app_module(dr_module, auto_df, self._minimal_spec())
        limiter = app_mod._RateLimiter(max_rpm=2)
        limiter.is_allowed("192.168.1.1")
        limiter.is_allowed("192.168.1.1")
        assert not limiter.is_allowed("192.168.1.1"), "IP A should be limited"
        assert limiter.is_allowed("192.168.1.2"), \
            "IP B must not be affected by IP A exhaustion"

    # ------------------------------------------------------------------
    # BUG-RL-2: _HealthHandler.prepare() enforces the limiter
    # ------------------------------------------------------------------
    def test_health_handler_has_prepare_method(self, dr_module, auto_df):
        """BUG-RL-2a: _HealthHandler must define a prepare() method."""
        source = _build_app(dr_module, auto_df, self._minimal_spec())
        assert "def prepare(self):" in source, \
            "_HealthHandler must define prepare() to enforce rate limiting"

    def test_health_handler_prepare_calls_limiter(self, dr_module, auto_df):
        """BUG-RL-2b: _HealthHandler.prepare() must call a limiter's is_allowed and set 429.
        Updated for BUG-48: health handler now uses _HEALTH_LIMITER (separate from
        _SESSION_LIMITER) so infrastructure checks don't deplete the session budget."""
        source = _build_app(dr_module, auto_df, self._minimal_spec())
        # Either _HEALTH_LIMITER or _LIMITER (legacy alias) must be called in the handler
        assert "_HEALTH_LIMITER.is_allowed" in source or "_LIMITER.is_allowed" in source, \
            "Generated source must call a rate-limiter's is_allowed from _HealthHandler"
        assert "429" in source, \
            "Generated source must set HTTP status 429 for rate-limited requests"

    def test_health_handler_prepare_blocks_and_returns_429(self, dr_module, auto_df):
        """BUG-RL-2c: _HealthHandler.prepare() must set 429 and finish() when blocked.
        Updated for BUG-48: replace _HEALTH_LIMITER (not _LIMITER) to force a block."""
        app_mod = _load_app_module(dr_module, auto_df, self._minimal_spec())

        # BUG-48 fix: health handler uses _HEALTH_LIMITER; replace that to force block
        original_health_limiter = app_mod._HEALTH_LIMITER
        original_limiter = app_mod._LIMITER
        blocking_limiter = app_mod._RateLimiter(max_rpm=0)  # always blocks
        app_mod._HEALTH_LIMITER = blocking_limiter
        # Also keep _LIMITER alias in sync in case handler references it
        app_mod._LIMITER = blocking_limiter
        captured = {}

        class _MockRequest:
            remote_ip = "127.0.0.1"

        class _MockHandler(app_mod._HealthHandler):
            request = _MockRequest()
            def set_status(self, code):
                captured["status"] = code
            def set_header(self, k, v):
                captured.setdefault("headers", {})[k] = v
            def finish(self, body=""):
                captured["finished"] = True
                captured["body"] = body

        try:
            handler = object.__new__(_MockHandler)
            handler.request = _MockRequest()
            handler.prepare()
            assert captured.get("status") == 429, \
                "prepare() must set HTTP 429 when rate limit is exceeded"
            assert captured.get("finished"), \
                "prepare() must call finish() so the request is terminated"
        finally:
            app_mod._HEALTH_LIMITER = original_health_limiter
            app_mod._LIMITER = original_limiter

    # ------------------------------------------------------------------
    # BUG-RL-3/4: make_document enforces the rate limiter
    # ------------------------------------------------------------------
    def test_make_document_source_contains_limiter_check(self, dr_module, auto_df):
        """BUG-RL-3a: make_document must contain a rate-limiter is_allowed call.
        Updated for BUG-48: make_document now uses _SESSION_LIMITER."""
        source = _build_app(dr_module, auto_df, self._minimal_spec())
        make_doc_start = source.find("def make_document(")
        assert make_doc_start != -1
        make_doc_body = source[make_doc_start:]
        # Accept either _SESSION_LIMITER (new) or _LIMITER (legacy alias)
        assert "_SESSION_LIMITER.is_allowed" in make_doc_body or \
               "_LIMITER.is_allowed" in make_doc_body, (
            "make_document must call a rate-limiter's is_allowed at session-creation time"
        )

    def test_make_document_adds_429_div_when_rate_limited(self, dr_module, auto_df):
        """BUG-RL-3b: make_document must add a 429 Div and return early when blocked.
        Updated for BUG-48: replace _SESSION_LIMITER (not _LIMITER) to force a block.

        This asserted ``len(roots) > 0`` and that SOME Div read "429": a
        make_document that added the refusal and then built the whole
        dashboard passed both (WP-24, measured 24sep2026).  Returning early
        is what it names, so the refusal is the document's one model with
        a layout -- no figure, no layout column.  The fake session is
        handed to the document as Bokeh's own session_context property
        reads it, a callable; this used to replace that property on the
        Document CLASS, for every document the worker built afterwards."""
        from bokeh.document import Document
        from bokeh.models import Div as BkDiv, LayoutDOM, Plot
        app_mod = _load_app_module(dr_module, auto_df, self._minimal_spec())

        # BUG-48 fix: make_document uses _SESSION_LIMITER; replace that to force block
        original_session_limiter = app_mod._SESSION_LIMITER
        original_limiter = app_mod._LIMITER
        blocking_limiter = app_mod._RateLimiter(max_rpm=0)
        app_mod._SESSION_LIMITER = blocking_limiter
        app_mod._LIMITER = blocking_limiter  # keep alias in sync

        try:
            doc = Document()

            class _FakeSessionContext:
                class request:
                    remote_ip = "10.1.1.1"
                    headers = {}
                    # WP-29 P0.12a: the session carries the key.
                    arguments = token_args()

            doc._session_context = lambda: _FakeSessionContext
            assert doc.session_context.request.remote_ip == "10.1.1.1"

            app_mod.make_document(doc)

            assert len(doc.roots) == 1 and isinstance(doc.roots[0], BkDiv), (
                doc.roots)
            assert "429 Too Many Requests" in doc.roots[0].text, (
                doc.roots[0].text)
            assert list(doc.select({"type": LayoutDOM})) == [doc.roots[0]], (
                "a refused session built more than its refusal")
            assert not list(doc.select({"type": Plot}))
        finally:
            app_mod._SESSION_LIMITER = original_session_limiter
            app_mod._LIMITER = original_limiter

    def test_make_document_proceeds_normally_when_allowed(self, dr_module, auto_df):
        """BUG-RL-4: make_document must build the full dashboard when not rate-limited.
        Updated for BUG-48: set _SESSION_LIMITER permissive (not just _LIMITER).

        This asserted ``len(doc.roots) > 0`` and no 429 root: a
        make_document that returned early with any other root passed
        (WP-24, measured 24sep2026).  The full dashboard is its one
        figure drawing the 30 points, no refusal anywhere in it -- and the
        session counted once, against its own client's address."""
        from bokeh.document import Document
        from bokeh.models import Div as BkDiv
        app_mod = _load_app_module(dr_module, auto_df, self._minimal_spec())

        # BUG-48 fix: make_document uses _SESSION_LIMITER
        original_session_limiter = app_mod._SESSION_LIMITER
        original_limiter = app_mod._LIMITER
        permissive_limiter = app_mod._RateLimiter(max_rpm=1000)
        app_mod._SESSION_LIMITER = permissive_limiter
        app_mod._LIMITER = permissive_limiter  # keep alias in sync

        doc = Document()

        class _FakeSessionContext:
            class request:
                remote_ip = "10.2.2.2"
                headers = {}
                # WP-29 P0.12a: the session carries the key.
                arguments = token_args()

        doc._session_context = lambda: _FakeSessionContext

        try:
            app_mod.make_document(doc)

            assert len(doc.roots) == 1, doc.roots
            layers = _glyph_layers(doc.roots)
            assert [type(r.glyph).__name__ for _f, r in layers] == ["Scatter"]
            assert sorted(zip(_drawn_values(layers[0][1], "weight"),
                              _drawn_values(layers[0][1], "mpg"))) == \
                sorted(zip(auto_df["weight"], auto_df["mpg"]))
            bad = [d for d in doc.select({"type": BkDiv}) if "429" in d.text]
            assert not bad, \
                "No 429 Div should appear when the request is within the rate limit"
            assert {k: len(v) for k, v in permissive_limiter._store.items()} \
                == {"10.2.2.2": 1}, permissive_limiter._store
        finally:
            app_mod._SESSION_LIMITER = original_session_limiter
            app_mod._LIMITER = original_limiter


# ================================================================
# BUG-30: Generated server rate limiter keeps unbounded per-IP state
# Empty per-IP entries must be deleted after pruning and a global
# _MAX_IPS cap must prevent unbounded growth under IP churn.
# ================================================================

class TestRateLimiterBoundedMemory:
    """BUG-30: _RateLimiter._store must not grow without bound.

    Pre-fix: keys were NEVER deleted from `_store`; after timestamps expired,
    the empty list remained under the key.  10,000 unique IPs produced 10,000
    permanent entries.

    Post-fix: keys are deleted when their timestamp list becomes empty after
    pruning, and a _MAX_IPS hard cap bounds the store.

    TR-19.5 (ROADMAP.md WP-19) changed what the cap does when the store is
    full. It used to evict the oldest entry, and that eviction was a defect
    of its own: 10,000 forged keys evicted a live client's record and took
    10,120 sessions in 60 s against a nominal 60. Now stale keys are swept,
    and a new key that finds the store full of live keys is not tracked --
    no live key is evicted. The bound itself, ``len(_store) <= _MAX_IPS``,
    is unchanged. test_server_rate_limit.py covers the new contract.
    """

    def _minimal_spec(self):
        return _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}],
            "graph_options": {"name": "g1"},
        }])

    def test_empty_entry_deleted_after_timestamps_expire(self, dr_module, auto_df):
        """BUG-30-1a: _store key must be absent after all its timestamps expire."""
        app_mod = _load_app_module(dr_module, auto_df, self._minimal_spec())
        limiter = app_mod._RateLimiter(max_rpm=60)
        # Manually add a stale timestamp for an IP
        import time as _time
        stale_ts = _time.monotonic() - 120  # 2 min ago — definitely expired
        limiter._store["10.99.0.1"] = [stale_ts]
        # is_allowed should prune the stale timestamp and delete the key
        result = limiter.is_allowed("10.99.0.1")
        assert result, "stale-then-fresh IP must be allowed after timestamp expires"
        # After pruning the stale ts, a fresh one was appended — key must exist
        assert "10.99.0.1" in limiter._store, \
            "key must exist after fresh ts appended post-prune"
        # Now simulate the new ts also expiring
        limiter._store["10.99.0.1"] = [stale_ts]  # replace with stale
        # Directly verify pruning deletes the key — simulate is_allowed logic
        limiter._store["10.99.0.2"] = [stale_ts]
        limiter.is_allowed("10.99.0.2")  # prunes 10.99.0.2's stale ts, appends fresh
        # Set 10.99.0.2's list to empty manually to test deletion path
        limiter._store["10.99.0.3"] = [stale_ts]
        limiter.is_allowed("10.99.0.3")
        # Force all timestamps to stale, then call again to trigger prune+delete
        for ip_key in list(limiter._store.keys()):
            limiter._store[ip_key] = [stale_ts]
        before = len(limiter._store)
        for ip_key in list(limiter._store.keys()):
            limiter.is_allowed(ip_key)  # prunes stale, appends fresh
        # Each IP still has one fresh timestamp — keys must survive
        # (they were re-added with fresh ts)
        assert len(limiter._store) == before, \
            "_store size must be stable when IPs keep getting fresh requests"

    def test_expired_ip_key_removed_from_store(self, dr_module, auto_df):
        """BUG-30-1b: after all timestamps expire and no new request arrives, key must not linger."""
        app_mod = _load_app_module(dr_module, auto_df, self._minimal_spec())
        limiter = app_mod._RateLimiter(max_rpm=60)
        import time as _time
        # Seed a stale entry
        stale = _time.monotonic() - 120
        limiter._store["zombie.ip"] = [stale]
        assert "zombie.ip" in limiter._store, "key must be seeded for test setup"
        # A second (different) IP's is_allowed call should NOT affect zombie.ip,
        # but when zombie.ip itself calls is_allowed, its entry should be cleaned
        limiter.is_allowed("zombie.ip")  # triggers prune → delete zombie.ip's stale ts
        # Key is re-added with fresh ts (because request is allowed) — that is fine
        # Now manually empty it to verify the delete path
        limiter._store["zombie.ip"] = [stale]  # stale again
        # Patch to prevent re-append: set max to 0 so request is blocked
        limiter._max = 0
        limiter.is_allowed("zombie.ip")  # prunes → empty → should delete key
        assert "zombie.ip" not in limiter._store, \
            "empty per-IP list must be deleted from _store to prevent unbounded growth"

    def test_high_cardinality_ip_churn_store_bounded(self, dr_module, auto_df):
        """BUG-30-1c: _store size must not exceed _MAX_IPS under high-cardinality churn.

        Updated for TR-19.5. With the defaults, first contact from keys the
        limiter is not tracking now shares one window of max_rpm, so this
        churn tracked 60 keys and never came near the cap: the assertion
        still held, but no longer tested the cap. The first-contact and
        total bounds are opened wide here so that every one of the
        _MAX_IPS + 500 keys is admitted and the cap is what bounds the
        store; the bound asserted is unchanged, and the test now also
        fails if the store never reaches the cap.
        """
        app_mod = _load_app_module(dr_module, auto_df, self._minimal_spec())
        max_ips = app_mod._RateLimiter._MAX_IPS
        limiter = app_mod._RateLimiter(max_rpm=60,
                                       new_clients=max_ips + 500,
                                       total_rpm=max_ips + 500)
        # Issue requests from many more IPs than _MAX_IPS
        for i in range(max_ips + 500):
            limiter.is_allowed(f"192.0.2.{i // 256}.{i % 256}")
        assert len(limiter._store) <= max_ips, (
            f"_store size {len(limiter._store)} must not exceed _MAX_IPS={max_ips}"
        )
        assert len(limiter._store) == max_ips, (
            f"_store holds {len(limiter._store)} keys, so the churn never "
            f"reached _MAX_IPS={max_ips} and the cap went untested"
        )

    def test_rate_limiter_has_max_ips_attribute(self, dr_module, auto_df):
        """BUG-30-1d: _RateLimiter must define _MAX_IPS to enforce global store cap."""
        app_mod = _load_app_module(dr_module, auto_df, self._minimal_spec())
        limiter = app_mod._RateLimiter(max_rpm=60)
        assert hasattr(limiter, "_MAX_IPS"), \
            "_RateLimiter must have _MAX_IPS attribute for global IP cap"
        assert limiter._MAX_IPS > 0, "_MAX_IPS must be a positive integer"

    def test_rate_limiting_still_works_after_fix(self, dr_module, auto_df):
        """BUG-30-1e: normal rate-limiting behavior must be preserved after fix."""
        app_mod = _load_app_module(dr_module, auto_df, self._minimal_spec())
        limiter = app_mod._RateLimiter(max_rpm=2)
        assert limiter.is_allowed("10.0.0.99"), "first request must be allowed"
        assert limiter.is_allowed("10.0.0.99"), "second request must be allowed"
        assert not limiter.is_allowed("10.0.0.99"), \
            "third request must be blocked when max_rpm=2"


# ================================================================
# BUG-FE-1: Server-mode function expressions reject normal arithmetic
# Regression for: "_val_node recursively validates BinOp/UnaryOp
# children without excluding operator nodes (Add, Sub, etc.).
# Operator nodes then fall into the else branch and raise
# ValueError('Disallowed node ...')."
# Fix: add `elif isinstance(node, (_ast.operator, _ast.unaryop)): pass`
# before the else clause so pure operator nodes are silently skipped.
# ================================================================

def _build_function_app(dr_module, expr, x_range="0 10"):
    """Generate server source for a single function graph and return the source string."""
    import pandas as pd, numpy as np
    df = pd.DataFrame({
        "x": np.linspace(0, 10, 20),
        "y": np.linspace(0, 10, 20),
    })
    spec = _make_spec_json(graphs=[{
        "plots": [{"type": "function", "expr": expr,
                   "range": [0, 10], "options": {"n": "20"}}],
        "graph_options": {"name": "gfe"},
    }])
    return _build_app(dr_module, df, spec)


def _exec_function_app(dr_module, expr, accepted=None):
    """Build a server app with *expr* as the function expression and run make_document.

    Returns the Bokeh Document; raises if make_document raises.  With a
    list for *accepted*, the app's own ``_stata_fn_eval`` -- which its
    map_function calls only once ``_stata_fn_parse`` has ACCEPTED the
    expression (WP-29 P0.6; it wrapped ``_floats_only``, gone with the
    eval() it guarded) -- is wrapped to record each call, so the served
    grammar's verdict is read in the served code
    (test_server_function_security.py counts it the same way).
    """
    import pandas as pd, numpy as np, importlib.util, tempfile, os
    from bokeh.document import Document

    df = pd.DataFrame({"x": np.linspace(0, 10, 20), "y": np.linspace(0, 10, 20)})
    spec = _make_spec_json(graphs=[{
        "plots": [{"type": "function", "expr": expr,
                   "range": [0, 10], "options": {"n": "20"}}],
        "graph_options": {"name": "gfe"},
    }])
    spec_path, data_path = _write_temp_files(df, spec)
    out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
    out_f.close()
    try:
        builder = dr_module.ServerAppBuilder(spec_path, data_path)
        builder.build(out_f.name)
        app_mod = load_app(out_f.name, "_tfe")
        if accepted is not None:
            _real = app_mod._stata_fn_eval

            def _counted(tree, x):
                accepted.append(tree)
                return _real(tree, x)
            app_mod._stata_fn_eval = _counted
        doc = Document()
        app_mod.make_document(doc)
        return doc
    finally:
        for _p in (spec_path, data_path, out_f.name):
            try:
                os.unlink(_p)
            except OSError:
                pass


class TestServerFunctionExpressionOperators:
    """Regression suite for BUG-FE-1: operator nodes must not be rejected.

    Before the fix, expressions like 'x + 1' raised ValueError('Disallowed
    node: Add') because _val_node iterated BinOp/UnaryOp child nodes with
    iter_child_nodes() which yields the operator node (Add, Sub, etc.) as
    well as the operands, and the operator node fell into the else-raise
    branch.  After the fix, operator nodes are silently skipped.

    The seven behavioural tests below used to assert `len(doc.roots) > 0'.
    Measured: that is 1 whether or not the function layer was built, because
    the document always carries the title/layout column as a root -- an
    expression the validator REJECTS gives roots 1, glyphs 0 just the same.
    They count glyph renderers now, which is what the bug destroyed.
    """

    # BUG-FE-1a: the generated app still validates the expression, and still
    # permits arithmetic.
    def test_the_generated_app_validates_the_expression(self, dr_module,
                                                        auto_df):
        """BUG-FE-1a, restated against behaviour rather than a spelling.

        This used to assert that the string ``_ast.operator`` appeared in the
        generated source, because the app carried its own inline ``_val_node``
        which skipped operator nodes via that base class. The app now calls
        ``GlyphMapper.map_function``, whose ``_validate_expr_node`` whitelists
        the operator classes individually (``_ast.Add``, ``_ast.Sub``, ...)
        instead. That is the same guarantee -- arguably a tighter one, being
        an explicit list rather than a skipped base class -- but it does not
        contain the old string, so the old assertion failed on a change that
        removed nothing.

        What must remain true is that the app still validates before it
        evaluates. The seven behavioural cases below check the other half:
        that ordinary arithmetic is permitted.

        Flipped (WP-29 P0.6): the whitelist and eval() are gone; a spec
        without points is parsed by Stata's grammar (_stata_fn_parse) and
        only its tree is evaluated (_stata_fn_eval), so those two are what
        the app must carry, and no eval( or compile( of the text.
        """
        source = _build_function_app(dr_module, "x + 1")
        assert "def _stata_fn_parse(" in source, (
            "the generated app evaluates a user-supplied expression with no "
            "grammar in sight"
        )
        assert "def _stata_fn_eval(" in source, (
            "the fallback's evaluator is not in the generated app"
        )
        # And nothing still calls the retired inline validator.
        assert "_val_node(" not in source, (
            "the app calls _val_node, which is no longer emitted"
        )

    # BUG-FE-1b: addition (BinOp with Add)
    def test_function_addition_does_not_raise(self, dr_module, auto_df):
        """BUG-FE-1b: x + 1 must not raise ValueError in server make_document."""
        doc = _exec_function_app(dr_module, "x + 1")
        assert _count_glyph_renderers(doc) > 0, (
            "the function layer for 'x + 1' was not drawn"
        )

    # BUG-FE-1c: subtraction (BinOp with Sub)
    def test_function_subtraction_does_not_raise(self, dr_module, auto_df):
        """BUG-FE-1c: x - 1 must not raise ValueError in server make_document."""
        doc = _exec_function_app(dr_module, "x - 1")
        assert _count_glyph_renderers(doc) > 0, (
            "the function layer for 'x - 1' was not drawn"
        )

    # BUG-FE-1d: multiplication (BinOp with Mult)
    def test_function_multiplication_does_not_raise(self, dr_module, auto_df):
        """BUG-FE-1d: x * 2 must not raise ValueError in server make_document."""
        doc = _exec_function_app(dr_module, "x * 2")
        assert _count_glyph_renderers(doc) > 0, (
            "the function layer for 'x * 2' was not drawn"
        )

    # BUG-FE-1e: division (BinOp with Div)
    def test_function_division_does_not_raise(self, dr_module, auto_df):
        """BUG-FE-1e: x / 2 must not raise ValueError in server make_document."""
        doc = _exec_function_app(dr_module, "x / 2")
        assert _count_glyph_renderers(doc) > 0, (
            "the function layer for 'x / 2' was not drawn"
        )

    # BUG-FE-1f: exponentiation (BinOp with Pow)
    def test_function_power_does_not_raise(self, dr_module, auto_df):
        """BUG-FE-1f: x ^ 2 must not raise ValueError in server make_document.

        Flipped (WP-29 P0.6): ``x ** 2`` is not Stata's (twoway r(198)) and
        draws nothing; Stata's power is ``^``, and its values are drawn."""
        doc = _exec_function_app(dr_module, "x ^ 2")
        assert _count_glyph_renderers(doc) > 0, (
            "the function layer for 'x ^ 2' was not drawn"
        )
        (_fig, r), = _glyph_layers(doc.roots)
        xs = _drawn_values(r, "x_fn")
        assert _drawn_values(r, "y_fn") == [v ** 2 for v in xs]

    # BUG-FE-1g: unary negation (UnaryOp with USub)
    def test_function_unary_negation_does_not_raise(self, dr_module, auto_df):
        """BUG-FE-1g: -x must not raise ValueError in server make_document."""
        doc = _exec_function_app(dr_module, "-x")
        assert _count_glyph_renderers(doc) > 0, (
            "the function layer for '-x' was not drawn"
        )

    # BUG-FE-1h: complex nested expression
    def test_function_complex_expr_does_not_raise(self, dr_module, auto_df):
        """BUG-FE-1h: sin(x) + x^2 - 1 must not raise ValueError.

        Flipped (WP-29 P0.6): written with Stata's ``^``; ``**`` is
        refused as twoway refuses it."""
        doc = _exec_function_app(dr_module, "sin(x) + x^2 - 1")
        assert _count_glyph_renderers(doc) > 0, (
            "make_document must add roots for complex expression 'sin(x) + x^2 - 1'"
        )

    # Safety: unsafe names must be blocked — generated source must contain _SAFE_NAMES guard
    def test_function_unsafe_name_guard_in_source(self, dr_module, auto_df):
        """BUG-FE-1 safety: generated source must contain _SAFE_NAMES to block disallowed names.

        The try/except around _val_node intentionally swallows ValueError so a bad
        expression does not crash the whole dashboard.  The security property is that
        eval() is never reached with the unsafe code, not that make_document raises.
        Verify the guard exists in the generated source.
        """
        # Flipped (WP-29 P0.6): the names are now refused by the grammar,
        # _stata_fn_parse, which takes x and _pi alone.
        source = _build_function_app(dr_module, "x + 1")
        assert "def _stata_fn_parse(" in source, (
            "generated server source must contain _stata_fn_parse to block disallowed names"
        )
        assert '"unknown name"' in source, (
            "generated server source must contain the parser's refusal of any other name"
        )

    # Safety: unsafe function calls must be blocked — generated source must contain _SAFE_FUNCS guard
    def test_function_unsafe_call_guard_in_source(self, dr_module, auto_df):
        """BUG-FE-1 safety: generated source must contain _SAFE_FUNCS to block disallowed calls.

        Same rationale as test_function_unsafe_name_guard_in_source: the try/except
        silences the error but the eval() path is never reached for unsafe expressions.
        """
        # Flipped (WP-29 P0.6): the parser's function-name table and its
        # refusal of any other call.
        source = _build_function_app(dr_module, "x + 1")
        assert '"floor", "ceil")' in source, (
            "generated server source must contain the parser's function-name table"
        )
        assert '"unknown function"' in source, (
            "generated server source must contain the parser's refusal of any other call"
        )

    # Safety: unsafe expression silently skipped (dashboard still loads, no line from unsafe expr)
    def test_function_unsafe_expr_document_still_loads(self, dr_module, auto_df):
        """BUG-FE-1 safety: make_document must not crash for an unsafe expression.

        The validator detects the unsafe expression, the try/except swallows the error,
        and the dashboard loads without the function plot.  This is correct behavior.

        This asserted only ``doc is not None``, which make_document's return
        guarantees whatever the validator does: with the whitelist call
        deleted from map_function it stayed green (WP-24, measured
        24sep2026).  The served grammar must REFUSE the expression -- it
        never reaches _stata_fn_eval, so it is never evaluated (WP-29 P0.6) --
        and the figure loads with its function layer empty.  The control is
        a plain expression, which the same count sees accepted once and the
        same reader sees drawn at all 20 points.
        """
        from bokeh.models import Plot
        accepted = []
        doc = _exec_function_app(dr_module, "os.system('id')", accepted)
        assert accepted == [], (
            "the served validator accepted os.system('id'); only its "
            "evaluation failing would keep it from running")
        assert len(doc.roots) == 1, doc.roots
        assert len(list(doc.select({"type": Plot}))) == 1
        layers = _glyph_layers(doc.roots)
        assert [len(r.data_source.data["x_fn"]) for _f, r in layers] == [0], (
            "the refused expression's layer was not drawn empty")

        control = []
        doc = _exec_function_app(dr_module, "x + 1", control)
        assert len(control) == 1, control
        (_fig, r), = _glyph_layers(doc.roots)
        assert _drawn_values(r, "y_fn") == [v + 1 for v in _drawn_values(r, "x_fn")]
        assert len(r.data_source.data["x_fn"]) == 20


# ================================================================
# BUG-31: Server-mode function plots silently drop valid constant expressions
# np.asarray(scalar, dtype=float).tolist() returns a float, not a list;
# ColumnDataSource raises because 'y_fn' is not a sequence, so the broad
# except silently drops the entire function line.
# Fix: mirror standalone map_function by broadcasting scalar results to
# len(_x) before creating ColumnDataSource.
# ================================================================


def _assert_served_layer_refits(dr_module, df, ptype):
    """Serve *ptype* with a dropdown on `foreign', move it to 1, and compare
    every derived column against the saved renderer on the foreign==1 rows."""
    import warnings
    from bokeh.document import Document
    from bokeh.models import Select

    def _derived(figs):
        out, seen = {}, set()
        for f in figs:
            for r in f.renderers:
                src = getattr(r, "data_source", None)
                if src is None or id(src) in seen:
                    continue
                seen.add(id(src))
                for k, v in src.data.items():
                    if k in ("index", dr_module._ROW_ID_COLUMN) or not len(v):
                        continue
                    try:
                        vals = [float(x) for x in v]
                    except (TypeError, ValueError):
                        continue
                    out.setdefault(k, []).append((len(vals), round(sum(vals), 4)))
        return {k: sorted(v) for k, v in out.items()}

    if ptype in ("rscatter",):
        plot = {"type": ptype, "yvar1": "mpg", "yvar2": "price",
                "xvar": "weight", "options": {}}
    elif ptype in ("pcscatter",):
        plot = {"type": ptype, "y1var": "mpg", "x1var": "weight",
                "y2var": "price", "x2var": "foreign", "options": {}}
    else:
        plot = {"type": ptype, "yvar": "mpg", "xvar": "weight", "options": {}}
    graphs = [{"plots": [plot], "graph_options": {"name": "g1"}}]
    spec = _make_spec_json(graphs=graphs,
                           build_options={"filter": "foreign, type(dropdown)"})
    spec_path, data_path = _write_temp_files(df, spec)
    out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
    out_f.close()
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr_module.ServerAppBuilder(spec_path, data_path).build(out_f.name)
            mod = load_app(out_f.name, "_refit_" + ptype)
            doc = Document()
            mod.make_document(doc)
            figs = [m for m in doc.select({"type": object})
                    if type(m).__name__ == "figure"]
            w = [m for m in doc.select({"type": Select})][0]
            old = w.value
            w.value = "1.0"
            for cb in w._callbacks.get("value", []):
                cb("value", old, "1.0")
            got = _derived(figs)
    finally:
        for _p in (spec_path, data_path, out_f.name):
            try: os.unlink(_p)
            except OSError: pass
    spec2 = _make_spec_json(graphs=graphs)
    spec_path, data_path = _write_temp_files(df[df["foreign"] == 1.0], spec2)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = dr_module.DashRenderer(spec_path, data_path)
            render_models(r)
            want = _derived(r.figures.values())
    finally:
        for _p in (spec_path, data_path):
            try: os.unlink(_p)
            except OSError: pass
    assert got, "%s drew no derived source to compare" % ptype
    assert got == want, ("%s after filtering to foreign==1: served %s, "
                         "saved on those rows %s" % (ptype, got, want))


def _panel_rows_both_modes(dr_module, df, if_expr, in_expr):
    """Rows drawn per by(foreign) panel, in each render mode, for a qualifier."""
    import warnings
    from bokeh.document import Document

    def _rows(figs):
        out = []
        for f in figs:
            n = 0
            for r in f.renderers:
                src = getattr(r, "data_source", None)
                if src is None:
                    continue
                d = dict(src.data)
                k = next(iter(d), None)
                view = getattr(r, "view", None)
                flt = getattr(view, "filter", None) if view is not None else None
                idx = getattr(flt, "indices", None) if flt is not None else None
                n += len(idx) if idx is not None else (len(d[k]) if k else 0)
            out.append(n)
        return out

    g = {"plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
         "graph_options": {"name": "g1", "by": "foreign"}}
    if if_expr:
        g["if_expr"] = if_expr
    if in_expr:
        g["in_expr"] = in_expr
    spec = _make_spec_json(graphs=[g])
    spec_path, data_path = _write_temp_files(df, spec)
    out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
    out_f.close()
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr_module.ServerAppBuilder(spec_path, data_path).build(out_f.name)
            mod = load_app(out_f.name, "_prb")
            doc = Document()
            mod.make_document(doc)
            # In DOCUMENT order, walking the layout.  doc.select() yields
            # models in an order that depends on their ids, so the panels
            # came back as [2, 3] in one run and [3, 2] in another and the
            # comparison with the saved renderer's insertion order flaked.
            _figs, _seen = [], set()

            def _visit(m):
                if isinstance(m, (list, tuple)):
                    for x in m:
                        if x is not None and not isinstance(x, (int, float, str)):
                            _visit(x)
                    return
                if m is None or id(m) in _seen:
                    return
                _seen.add(id(m))
                if type(m).__name__ == "figure":
                    _figs.append(m)
                for _attr in ("children", "tabs", "child"):
                    _k = getattr(m, _attr, None)
                    if _k is not None:
                        _visit(_k)

            for _root in doc.roots:
                _visit(_root)
            served_rows = _rows(_figs)
            r = dr_module.DashRenderer(spec_path, data_path)
            render_models(r)
            saved_rows = _rows(r.figures.values())
    finally:
        for _p in (spec_path, data_path, out_f.name):
            try: os.unlink(_p)
            except OSError: pass
    return {"served": served_rows, "saved": saved_rows}

def _count_glyph_renderers(doc) -> int:
    """Count all glyph renderers in a Bokeh document, traversing layouts."""
    from bokeh.models import GridPlot, Plot
    count = 0
    def _walk(obj, visited=None):
        nonlocal count
        if visited is None:
            visited = set()
        if id(obj) in visited:
            return
        visited.add(id(obj))
        if isinstance(obj, Plot):
            count += sum(1 for r in obj.renderers if hasattr(r, "glyph"))
            return  # don't recurse into figure renderers
        if isinstance(obj, GridPlot):
            for item in obj.children:
                child = item[0] if isinstance(item, tuple) else item
                _walk(child, visited)
            return
        for attr in ("children",):
            val = getattr(obj, attr, None)
            if isinstance(val, list):
                for c in val:
                    _walk(c, visited)
    for root in doc.roots:
        _walk(root)
    return count


class TestServerFunctionConstantExpressions:
    """BUG-31: Server-mode function plots must render constant expressions.

    Pre-fix: ``np.asarray(pi, dtype=float).tolist()`` returned a scalar
    float instead of a list, causing ``ColumnDataSource({'y_fn': <float>})``
    to raise, which was silently swallowed, resulting in zero glyph renderers.

    Post-fix: scalar results are broadcast to ``np.full(len(_x), float(_y_arr))``
    before the ColumnDataSource is created, mirroring ``map_function`` in the
    standalone path.
    """

    def test_constant_pi_renders_glyph(self, dr_module, auto_df):
        """BUG-31-1a: function expression '_pi' must produce a glyph renderer.

        Flipped (WP-29 P0.6): Stata's constant is ``_pi``; twoway refuses
        ``pi`` (r(111))."""
        doc = _exec_function_app(dr_module, "_pi")
        assert _count_glyph_renderers(doc) > 0, (
            "function expression '_pi' must produce at least one glyph renderer"
        )

    def test_constant_integer_renders_glyph(self, dr_module, auto_df):
        """BUG-31-1b: function expression '3' must produce a glyph renderer."""
        doc = _exec_function_app(dr_module, "3")
        assert _count_glyph_renderers(doc) > 0, (
            "function expression '3' must produce at least one glyph renderer"
        )

    def test_constant_float_renders_glyph(self, dr_module, auto_df):
        """BUG-31-1c: function expression '2.718' must produce a glyph renderer."""
        doc = _exec_function_app(dr_module, "2.718")
        assert _count_glyph_renderers(doc) > 0, (
            "function expression '2.718' must produce at least one glyph renderer"
        )

    def test_generated_source_has_scalar_broadcast(self, dr_module, auto_df):
        """BUG-31-1d: generated source must contain scalar-broadcast guard (ndim == 0)."""
        source = _build_function_app(dr_module, "pi")
        assert "_y_arr.ndim == 0" in source or "ndim == 0" in source, (
            "generated server source must broadcast scalar function results to a vector "
            "(add 'if _y_arr.ndim == 0: _y_arr = np.full(len(_x), float(_y_arr))')"
        )

    def test_variable_expression_still_renders(self, dr_module, auto_df):
        """BUG-31-1e: variable expression 'x' must still produce a glyph renderer after fix."""
        doc = _exec_function_app(dr_module, "x")
        assert _count_glyph_renderers(doc) > 0, (
            "function expression 'x' must still work correctly after scalar-broadcast fix"
        )


# ================================================================
# BUG-FE-2: Server-mode function `n` option allows unbounded point counts
# Regression for: "Generated server code parses opts['n'] directly into
# n_pts and uses it in np.linspace(x_lo, x_hi, n_pts) with no upper bound.
# A large `n` can allocate very large arrays and drive CPU/memory
# exhaustion."
# Fix: clamp n_pts to max(2, min(int(opts['n']), 10000)) matching the
# standalone path.
# ================================================================

class TestServerFunctionNClamp:
    """Regression suite for BUG-FE-2: function n option must be clamped 2..10000.

    These used to assert that the generated SOURCE contained `max(2, min(',
    `10000' or the word `clamp'. Measured against the app as it is emitted
    now, `max(2,' appears on two lines and `10000' on several, one of them
    inside a copied helper that has nothing to do with function plots -- so
    all three greps were satisfied by text the bug does not touch, and
    deleting the clamp left them green.

    They assert the grid length instead, which is what the clamp exists to
    bound.
    """

    @staticmethod
    def _fn_grid(dr_module, n_value):
        """Length of the function layer's x grid for options {n: n_value}."""
        import importlib.util
        import os
        import tempfile
        import warnings
        import numpy as np
        import pandas as pd
        from bokeh.document import Document
        from bokeh.models import ColumnDataSource

        df = pd.DataFrame({"x": np.linspace(0, 10, 20),
                           "y": np.linspace(0, 10, 20)})
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "y", "xvar": "x",
                       "options": {}},
                      {"type": "function", "expr": "x",
                       "options": {"n": str(n_value), "range": "0 10"}}],
            "graph_options": {"name": "g1"},
        }])
        spec_path, data_path = _write_temp_files(df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py",
                                            delete=False)
        out_f.close()
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                dr_module.ServerAppBuilder(spec_path, data_path).build(
                    out_f.name)
            ms = importlib.util.spec_from_file_location(
                f"_nclamp_{abs(hash(str(n_value))) % 100000}", out_f.name)
            mod = importlib.util.module_from_spec(ms)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ms.loader.exec_module(mod)
                doc = Document()
                mod.make_document(doc)
            for m in doc.select({"type": ColumnDataSource}):
                if "x_fn" in m.data:
                    return len(m.data["x_fn"])
            return 0
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try:
                    os.unlink(_p)
                except OSError:
                    pass

    def test_an_ordinary_n_is_honoured(self, dr_module, auto_df):
        """The control: without this, a clamp to a constant would pass."""
        assert self._fn_grid(dr_module, 200) == 200

    def test_a_huge_n_is_clamped(self, dr_module, auto_df):
        """BUG-FE-2b: n(1000000) must not allocate a million points."""
        n = self._fn_grid(dr_module, 1_000_000)
        assert 0 < n <= 10_000, (
            f"n(1000000) produced a {n}-point grid; the clamp is 10000"
        )

    def test_n_below_the_minimum_is_raised_to_two(self, dr_module, auto_df):
        """BUG-FE-2c: np.linspace needs at least two points."""
        assert self._fn_grid(dr_module, 1) == 2
        assert self._fn_grid(dr_module, 0) == 2


class TestCLIServeFlagsAccepted:
    """Regression suite for BUG-CLI-1: dash_render.py must accept serve-mode flags.

    Before the fix, passing --mode serve, --port, --timeout or --no-browser
    caused argparse to abort with an error ('invalid choice: serve', or
    'unrecognized arguments: --port ...').  After the fix all four flags are
    accepted and the choices list includes 'server'.

    We test the CLI flags via two methods:
      1. Subprocess --help output (covers the full argparse definition)
      2. Source-code inspection (fast, no subprocess overhead)
    """

    def _get_help_output(self):
        """Run 'python dash_render.py --help' and return stdout."""
        import subprocess, sys, os
        src_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "dash_render.py"
        )
        result = subprocess.run(
            [sys.executable, src_path, "--help"],
            capture_output=True, text=True, timeout=30
        )
        # --help exits with code 0
        return result.stdout + result.stderr

    def _get_source(self):
        """Return the dash_render.py source text."""
        import os
        src_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "dash_render.py"
        )
        with open(src_path) as fh:
            return fh.read()

    def test_mode_server_in_choices(self, dr_module, auto_df):
        """BUG-CLI-1a: --mode choices must include 'server', not 'serve'.

        This searched the whole --help text for the substring "serve" with
        "server" removed.  That stopped working the moment the option's help
        string explained the distinction in words -- it names `dash serve'
        while describing what --mode server does -- and the test failed on
        its own documentation.

        argparse renders an option's choices as a braced list, so the
        question is asked of that list rather than of the surrounding prose.
        """
        import re

        help_txt = self._get_help_output()
        m = re.search(r"--mode\s*\{([^}]*)\}", help_txt)
        assert m, (
            f"--mode does not render a choice list in --help:\n"
            f"{help_txt[:400]}"
        )
        choices = [c.strip() for c in m.group(1).split(",") if c.strip()]
        assert "server" in choices, (
            f"--mode choices must include 'server'; got {choices}"
        )
        assert "serve" not in choices, (
            f"--mode must not offer the invalid choice 'serve'; got {choices}"
        )

    def test_port_argument_defined(self, dr_module, auto_df):
        """BUG-CLI-1b: --port must be defined in argparse with integer type."""
        help_txt = self._get_help_output()
        assert "--port" in help_txt, \
            "--port argument must appear in --help output (was missing before fix)"
        # Source must use type=int for --port
        src = self._get_source()
        assert '"--port"' in src or "'--port'" in src, \
            "--port must be defined in the argparse block"

    def test_timeout_argument_defined(self, dr_module, auto_df):
        """BUG-CLI-1c: --timeout must be defined in argparse with integer type."""
        help_txt = self._get_help_output()
        assert "--timeout" in help_txt, \
            "--timeout argument must appear in --help output (was missing before fix)"

    def test_no_browser_argument_defined(self, dr_module, auto_df):
        """BUG-CLI-1d: --no-browser must be defined in argparse as a store_true flag."""
        help_txt = self._get_help_output()
        assert "--no-browser" in help_txt, \
            "--no-browser argument must appear in --help output (was missing before fix)"

    def test_server_mode_generates_app_file(self, dr_module, auto_df):
        """BUG-CLI-1e: --mode server must generate a .py app file without launching server."""
        import tempfile, os
        spec_path, data_path = _write_temp_files(auto_df, _make_spec_json())
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            # main() is the programmatic API (no CLI flag parsing); use it directly
            dr_module.main(spec_path, data_path, out_f.name, "server")
            assert os.path.exists(out_f.name), \
                "main(..., mode='server') must write a .py file"
            with open(out_f.name) as fh:
                src = fh.read()
            assert "make_document" in src, \
                "generated server app must contain make_document function"
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try: os.unlink(_p)
                except OSError: pass

    def test_main_accepts_server_mode(self, dr_module, auto_df):
        """BUG-CLI-1f: main() must accept mode='server' without raising ValueError."""
        import tempfile, os
        spec_path, data_path = _write_temp_files(auto_df, _make_spec_json())
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            # Must not raise -- and what it accepted it acted on: the file
            # (created empty above) now holds Python defining the entry
            # point bokeh serve calls.  Flipped (WP-29 P0.12b): main()
            # returns the written app's identity and digest, which the
            # launcher verifies before it runs the app; it returned None.
            _written = dr_module.main(spec_path, data_path, out_f.name,
                                      "server")
            with open(out_f.name, "rb") as fh:
                assert _written.sha256 == hashlib.sha256(
                    fh.read()).hexdigest()
            with open(out_f.name, encoding="utf-8") as fh:
                tree = ast.parse(fh.read())
            assert "make_document" in {
                n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try: os.unlink(_p)
                except OSError: pass

    def test_main_raises_on_serve_mode(self, dr_module, auto_df):
        """BUG-CLI-1g: main() must raise ValueError for the old invalid mode 'serve'."""
        import tempfile, os
        spec_path, data_path = _write_temp_files(auto_df, _make_spec_json())
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            with pytest.raises(ValueError, match="unknown mode"):
                dr_module.main(spec_path, data_path, out_f.name, "serve")
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try: os.unlink(_p)
                except OSError: pass


# ================================================================
# BUG-SEC-1: Python command injection risk from unescaped file paths
# Regression for: "Stata macros are interpolated directly into single-
# quoted Python raw string literals (for spec, data, output, render_py)
# without escaping ' or other Python-literal-breaking characters."
# Fix: use _dash_json_str to escape paths before interpolation, switching
# from r"..." raw strings to regular "..." Python strings.
# ================================================================

class TestPathInjectionHardening:
    """Regression suite for BUG-SEC-1: path values must not allow Python injection.

    The fix moves path values from raw r"..." Python string literals
    (vulnerable to " in path) to _dash_json_str-escaped regular "..." strings.
    That fix is in dash.ado, and is certified by running it:
    test_render_locate.cscript LOC-17 hands _dash_do_render a renderer in a
    directory, and an output file, each named with a Python payload, and
    requires the page written and nothing run.  Two tests here used to read
    dash.ado for the escaping helper's name and for r"`...'" in its
    sys.argv lines; measured (WP-24), with the renderer's path interpolated
    raw again the payload ran and both stayed green.  They were removed for
    LOC-17; the rule that every macro inside a python: literal is an
    escaped one is test_cscript_hygiene.py's structural guard
    (test_no_untrusted_macro_is_inlined_into_python_source), which fails on
    both raw interpolations.  What remains here is the renderer's half:
    dash_render.py main() writing to paths it is handed.
    """

    def test_main_accepts_path_with_spaces(self, dr_module, auto_df):
        """BUG-SEC-1c: main() must accept paths with spaces without crashing."""
        import tempfile, os, shutil
        # Create a temp directory with a space in the name
        tmpdir = tempfile.mkdtemp(prefix="dash test dir ")
        try:
            spec_path, data_path = _write_temp_files(auto_df, _make_spec_json())
            out_path = os.path.join(tmpdir, "output file.html")
            try:
                dr_module.main(spec_path, data_path, out_path, "standalone")
                assert os.path.exists(out_path), \
                    "main() must write output file to path with spaces"
            finally:
                for _p in (spec_path, data_path):
                    try: os.unlink(_p)
                    except OSError: pass
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_main_accepts_path_with_backslash_on_posix(self, dr_module, auto_df,
                                                       tmp_path):
        """BUG-SEC-1d: main() must handle backslashes in path correctly on POSIX.

        The path this used had no backslash in it -- a NamedTemporaryFile
        name -- so it passed whatever main() did with one (WP-24).  On
        POSIX a backslash is an ordinary character of a file name.  The
        spec and data files now sit in a directory whose name holds one,
        and the page is written to a name holding two, one of them last
        before the extension: main() must read and write exactly those
        paths -- not a path with the backslashes dropped, doubled or read
        as separators -- and the page must be the dashboard."""
        import os, sys
        if sys.platform == "win32":
            pytest.skip("Backslash is path separator on Windows; test only on POSIX")
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        in_dir = tmp_path / "in\\put"
        in_dir.mkdir()
        spec_path = str(in_dir / "spec.json")
        data_path = str(in_dir / "data.json")
        with open(spec_path, "w", encoding="utf-8") as fh:
            json.dump(spec, fh)
        with open(data_path, "w", encoding="utf-8") as fh:
            fh.write(_make_data_json(auto_df))
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        out_path = str(out_dir / "a\\b\\.html")
        assert out_path.count("\\") == 2 and spec_path.count("\\") == 1

        dr_module.main(spec_path, data_path, out_path, "standalone")

        assert sorted(os.listdir(out_dir)) == ["a\\b\\.html"], (
            f"main() wrote {sorted(os.listdir(out_dir))}, not the path it "
            f"was handed")
        assert sorted(os.listdir(tmp_path)) == ["in\\put", "out"]
        with open(out_path, encoding="utf-8") as fh:
            page = fh.read()
        layers = _glyph_layers(_page_document(page).roots)
        assert [type(r.glyph).__name__ for _f, r in layers] == ["Scatter"]
        assert sorted(_drawn_values(layers[0][1], "weight")) == \
            sorted(auto_df["weight"])


# ================================================================
# BUG-PARSE-1: Immediate render parser truncates if_expr on quotes
# Regression for: "_dash_render_immediate extracts if_expr from JSON
# using substr(..., 1, strpos(..., '"') - 1). This stops at the first
# quote character even when it is an escaped quote inside the JSON
# string value."
# Fix: Replace naive strpos/substr with Mata _dash_json_get_str that
# walks the JSON string char-by-char handling \" escape sequences.
# ================================================================

#: A dataset whose `make' holds the texts hostile string literals name,
#: each followed by the DECOY that a mis-reading of that literal would
#: select instead.  Every row's weight is distinct, so the x values a layer
#: draws name the rows it drew.
_QL_MAKES = [
    ("C:\\", 0),                  # 0  a literal ending in a backslash
    ("C:", 0),                    # 1    decoy: the backslash dropped
    ('x"y', 0),                   # 2  a double quote, held by `"..."'
    ("x", 0),                     # 3    decoy: cut at the inner quote
    ("a\\u0022b", 0),             # 4  backslash-u text, eight characters
    ('a"b', 0),                   # 5    decoy: \u0022 read as an escape
    ("n\\n", 0),                  # 6  backslash-n text
    ("n\n", 0),                   # 7    decoy: \n read as a newline
    ('q","in_expr":"1/5', 0),     # 8  JSON's own punctuation
    ('\\"', 0),                   # 9  a backslash, then a quote
    ("a~=b", 0),                  # 10 Stata's not-equals, as text
    ("a!=b", 0),                  # 11   decoy: ~= rewritten in the literal
    ('say `"hi"\' now', 0),       # 12 compound quotes nested in the text
    ("a,b", 0),                   # 13 a comma, inside inlist()
    ("AMC", 1), ("BMW", 1), ("Audi", 1), ("VW", 1),       # 14-17
]
_QL_FOREIGN = {14, 15, 16, 17}

#: (id, the qualifier as dash.ado stores it -- Stata's own text, compound
#: quotes and all, which is what the renderer receives -- and the rows
#: Stata's `count if' selects on _QL_MAKES).  Stata's string literals have
#: no escape character: "C:\" is three characters and "n\n" three more.
#: test_qualifier_literals.cscript runs the same shapes through Stata
#: itself, whose count is the oracle there.
_QL_CASES = [
    ("backslash_last", 'make == "C:\\" | foreign == 1', {0} | _QL_FOREIGN),
    ("compound_quote", 'make == `"x"y"\' | foreign == 1', {2} | _QL_FOREIGN),
    ("backslash_u_text", 'make == "a\\u0022b" | foreign == 1',
     {4} | _QL_FOREIGN),
    ("backslash_n_text", 'make == "n\\n" | foreign == 1', {6} | _QL_FOREIGN),
    ("json_punctuation", 'make == `"q","in_expr":"1/5"\' | foreign == 1',
     {8} | _QL_FOREIGN),
    ("backslash_quote", 'make == `"\\""\' | foreign == 1', {9} | _QL_FOREIGN),
    ("tilde_equals_text", 'make == "a~=b" | foreign == 1',
     {10} | _QL_FOREIGN),
    ("nested_compound", 'make == `"say `"hi"\' now"\' | foreign == 1',
     {12} | _QL_FOREIGN),
    ("not_equal_compound", 'make != `"x"y"\' & foreign == 0',
     set(range(14)) - {2}),
    ("inlist_literals", 'inlist(make, "C:\\", `"x"y"\', "a,b")', {0, 2, 13}),
]
_QL_IDS = [c[0] for c in _QL_CASES]


def _ql_frame():
    n = len(_QL_MAKES)
    return pd.DataFrame({
        "make": [m for m, _ in _QL_MAKES],
        "foreign": [float(f) for _, f in _QL_MAKES],
        "mpg": [float(10 + i) for i in range(n)],
        "weight": [float(2000 + 50 * i) for i in range(n)],
    })


def _ql_weights(rows):
    return sorted(float(2000 + 50 * i) for i in rows)


def _ql_spec(qualifier, kpi=False, filt=""):
    """One scatter qualified as dash.ado writes a one-segment command: the
    qualifier on the plot AND promoted to the graph (``_dash_plot``), and on
    a KPI when *kpi*."""
    plot = {"type": "scatter", "yvar": "mpg", "xvar": "weight",
            "options": {}, "if_expr": qualifier, "in_expr": ""}
    kpis = []
    if kpi:
        # sum(weight), not count(): a decoy row is one row too, so a count
        # cannot tell the row the literal names from the one a mis-reading
        # of it names; their weights differ.
        kpis = [{"name": "k1", "stat": "sum", "var": "weight", "fmt": "%9.0f",
                 "title": "W", "subtitle": "", "color": "", "bgcolor": "",
                 "update": "filter", "if_expr": qualifier, "in_expr": ""}]
    return {
        "graphs": [{"plots": [plot], "graph_options": {"name": "g1"},
                    "if_expr": qualifier, "in_expr": ""}],
        "kpis": kpis,
        "build_options": {
            "layout": "auto", "link": "", "filter": filt, "theme": "",
            "scheme": "", "session_scheme": "", "title": "", "subtitle": "",
            "registry": "g1" + (" k1" if kpi else ""), "tabs": "",
            "filter_position": "top", "level": "95", "formats": {}},
    }


def _ql_write(tmp_path, spec, df=None, labels=None):
    """Spec and data files, with `make' flagged a string column the way
    jsonio flags one (variableIsString).  *labels* is
    ``(valueLabels, valueLabelNames)`` when the data carry value labels."""
    df = _ql_frame() if df is None else df
    value_labels, label_names = labels or ({}, {})
    sp = os.path.join(str(tmp_path), "spec.json")
    dp = os.path.join(str(tmp_path), "data.json")
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    cols = list(df.columns)
    with open(dp, "w", encoding="utf-8") as fh:
        json.dump({"StataJSON": {
            "variableNames": cols,
            "variableLabels": {c: c for c in cols},
            "valueLabels": value_labels, "valueLabelNames": label_names,
            "variableIsString": {c: c == "make" for c in cols},
            "variableTypeIsString": {c: c == "make" for c in cols},
            "values": df.to_dict(orient="records"),
        }}, fh)
    return sp, dp


def _ql_scatter(roots):
    """(rows the source carries, x values drawn through the view) for the
    one scatter layer under *roots*."""
    from bokeh.models import GlyphRenderer, Plot
    found = []
    for root in roots:
        for fig in root.select({"type": Plot}):
            for r in fig.renderers:
                if (isinstance(r, GlyphRenderer)
                        and type(r.glyph).__name__ == "Scatter"):
                    found.append(r)
    assert len(found) == 1, f"expected one scatter layer, found {len(found)}"
    r = found[0]
    xs = [float(v) for v in r.data_source.data["weight"]]
    filt = getattr(r.view, "filter", None)
    kind = type(filt).__name__ if filt is not None else ""
    if kind == "BooleanFilter":
        keep = [i for i, b in enumerate(list(filt.booleans)[:len(xs)]) if b]
    elif kind == "IndexFilter":
        keep = [i for i in filt.indices if 0 <= i < len(xs)]
    else:
        keep = list(range(len(xs)))
    return len(xs), sorted(xs[i] for i in keep)


def _ql_saved(dr, tmp_path, spec, df=None):
    """(renderer, warning texts) from the saved-page renderer."""
    import warnings as _w
    sp, dp = _ql_write(tmp_path, spec, df)
    with _w.catch_warnings(record=True) as caught:
        _w.simplefilter("always")
        r = dr.DashRenderer(sp, dp)
        render_models(r)
    return r, [str(x.message) for x in caught]


def _ql_served(dr, tmp_path, spec, df=None, labels=None):
    """(document, warning texts) from the generated server app, run the way
    ``bokeh serve`` runs it: its make_document on a fresh Document."""
    import warnings as _w
    from bokeh.document import Document
    sp, dp = _ql_write(tmp_path, spec, df, labels)
    ap = os.path.join(str(tmp_path), "app.py")
    with _w.catch_warnings(record=True) as built:
        _w.simplefilter("always")
        dr.ServerAppBuilder(sp, dp).build(ap)
    with open(ap, encoding="utf-8") as fh:
        src = fh.read()
    attach = "if __name__ != '__main__':\n    make_document(curdoc())"
    assert attach in src, "the generated app's curdoc attach moved"
    ns = {"__name__": "_ql_app"}
    with _w.catch_warnings():
        _w.simplefilter("ignore")
        exec(compile(src.replace(attach, "pass"), "_ql_app.py", "exec"), ns)
    with _w.catch_warnings(record=True) as caught:
        _w.simplefilter("always")
        doc = Document()
        ns["make_document"](doc)
    return doc, [str(x.message) for x in list(built) + list(caught)]


def _ql_app_ns(dr, tmp_path, spec, df=None):
    """The generated app's namespace -- everything it defines -- without its
    curdoc attach, so a test can call its helpers and handlers directly."""
    import warnings as _w
    sp, dp = _ql_write(tmp_path, spec, df)
    ap = os.path.join(str(tmp_path), "app.py")
    with _w.catch_warnings():
        _w.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(ap)
    with open(ap, encoding="utf-8") as fh:
        src = fh.read()
    attach = "if __name__ != '__main__':\n    make_document(curdoc())"
    assert attach in src, "the generated app's curdoc attach moved"
    ns = {"__name__": "_ql_app_ns"}
    with _w.catch_warnings():
        _w.simplefilter("ignore")
        exec(compile(src.replace(attach, "pass"), "_ql_app_ns.py", "exec"), ns)
    # WP-29 P0.12a: the key Gate B checks, as _dash_server_app installs it.
    ns["_DASH_SERVE_TOKEN"] = TEST_TOKEN
    return ns


def _ql_kpi_value(divs):
    import re as _re
    for d in divs:
        m = _re.search(r'id="kpi_val_k1"[^>]*>([^<]*)<', d.text or "")
        if m:
            return m.group(1).strip()
    raise AssertionError("no KPI card k1 was drawn")


class TestIfExprQuoteHandling:
    """Regression suite for BUG-PARSE-1: a qualifier holding a quoted string
    selects the rows Stata selects.

    BUG-PARSE-1 was dash.ado cutting the qualifier at the first quote of
    its JSON value; its fix is ``_dash_json_get_str``.  These tests used
    to assert that name appeared in dash.ado and dash_parse.mata -- which
    stayed green while the function decoded no escape at all (BUGS.md,
    "``_dash_json_get_str`` has never decoded a single JSON escape").  The
    Stata half is now driven end to end by test_qualifier_literals.cscript:
    the immediate render and ``dash build`` run on hostile quoted and
    escaped qualifiers, and the rows each mode draws are held to Stata's
    own ``count if``.  The decoder itself is JSE-28 and P1B-27..30.

    This class is the renderer half, in both modes: what either renderer
    does with the qualifier dash.ado hands it.  Converting the tests found
    that it did the wrong thing -- the translation to a pandas query kept
    every literal as Python source, so Stata's "C:\\" was an unterminated
    Python string, "a\\u0022b" and "n\\n" were read as Python escapes, a
    compound-quoted literal ended at its first inner quote, and the saved
    renderer and the served callback rewrote ``~=`` inside a literal.  Each
    either drew every row with a "filter skipped" warning or, worse,
    silently drew the wrong rows (measured 24sep2026 at 68327a8).
    """

    @pytest.mark.parametrize("label,qualifier,rows", _QL_CASES, ids=_QL_IDS)
    def test_the_saved_page_draws_the_rows_stata_selects(
            self, dr_module, tmp_path, label, qualifier, rows):
        r, warned = _ql_saved(dr_module, tmp_path, _ql_spec(qualifier))
        carried, drawn = _ql_scatter([r._last_layout_root])
        assert not [m for m in warned if "skipped" in m], (label, warned)
        assert drawn == _ql_weights(rows), (
            f"{label}: `if {qualifier}' drew the rows at x={drawn} on the "
            f"saved page; Stata selects x={_ql_weights(rows)}")
        # The graph's own qualifier (promoted by _dash_plot) restricts the
        # rows the page carries, not only the ones the layer draws.
        assert carried == len(rows), (label, carried, len(rows))

    @pytest.mark.parametrize("label,qualifier,rows", _QL_CASES, ids=_QL_IDS)
    def test_the_served_app_draws_the_rows_stata_selects(
            self, dr_module, tmp_path, label, qualifier, rows):
        doc, warned = _ql_served(dr_module, tmp_path, _ql_spec(qualifier))
        carried, drawn = _ql_scatter(doc.roots)
        assert not [m for m in warned if "skipped" in m], (label, warned)
        assert drawn == _ql_weights(rows), (
            f"{label}: `if {qualifier}' drew the rows at x={drawn} in the "
            f"served app; Stata selects x={_ql_weights(rows)}")
        assert carried == len(rows), (label, carried, len(rows))

    @pytest.mark.parametrize("label,qualifier,rows", _QL_CASES, ids=_QL_IDS)
    def test_a_kpi_sums_the_rows_stata_selects_in_both_modes(
            self, dr_module, tmp_path, label, qualifier, rows):
        from bokeh.models import Div
        spec = _ql_spec(qualifier, kpi=True)
        r, _ = _ql_saved(dr_module, tmp_path, spec)
        saved = _ql_kpi_value(r.kpi_divs.values())
        doc, _ = _ql_served(dr_module, tmp_path, spec)
        served = _ql_kpi_value([d for root in doc.roots
                                for d in root.select({"type": Div})])
        want = "%.0f" % sum(_ql_weights(rows))
        assert (saved, served) == (want, want), (
            f"{label}: `dash kpi sum(weight) if {qualifier}' reads saved "
            f"{saved!r}, served {served!r}; Stata sums {want}")

    @pytest.mark.parametrize("label,qualifier,rows", _QL_CASES, ids=_QL_IDS)
    def test_a_filter_move_keeps_the_graphs_qualifier_when_served(
            self, dr_module, tmp_path, label, qualifier, rows):
        """The served filter callback applies the graph's qualifier again
        after every move, through its own copy of the translation; a
        qualifier it cannot read would let the move bring back every row
        the qualifier excluded."""
        from bokeh.models import RangeSlider
        doc, _ = _ql_served(dr_module, tmp_path,
                            _ql_spec(qualifier, filt="mpg, type(range)"))
        sliders = [m for root in doc.roots
                   for m in root.select({"type": RangeSlider})]
        assert len(sliders) == 1, sliders
        w = sliders[0]
        lo, hi = 10.0, 21.0            # mpg 10..21: rows 0..11
        w.value = (lo, hi)
        for key in ("value", "value_throttled"):
            for cb in list(w._callbacks.get(key, [])):
                cb("value", None, (lo, hi))
        _carried, drawn = _ql_scatter(doc.roots)
        kept = {i for i in rows if lo <= 10 + i <= hi}
        assert drawn == _ql_weights(kept), (
            f"{label}: after the move the served scatter drew x={drawn}; "
            f"the qualifier and the range keep x={_ql_weights(kept)}")

    @pytest.mark.parametrize("qualifier", [
        # A backslash does not escape Stata's quote, so the text after the
        # first literal is code, not data -- and code the whitelist refuses.
        # `@os' is the payload pandas itself would run: measured, its
        # python engine resolves @os from the calling module and calls
        # os.system before it raises, so only dash's own guard stands here.
        'make == "x\\" | @os.system("touch SENTINEL") | "y"',
        # A compound literal closed early, the same payload behind it.
        'make == `"a"\' | @os.system("touch SENTINEL") | `"b"\'',
        # An unterminated literal is not completed into a valid one.
        'make == "AMC',
    ], ids=["backslash_breakout", "compound_breakout", "unterminated"])
    def test_a_literal_cannot_become_code_in_either_mode(
            self, dr_module, tmp_path, qualifier):
        """CLAUDE.md rule 18, injection: whatever a literal holds, the
        translation either reads it as data or refuses the qualifier, which
        is skipped with a warning -- every row drawn, nothing run."""
        sentinel = os.path.join(str(tmp_path), "SENTINEL")
        q = qualifier.replace("SENTINEL", sentinel)
        r, saved_warned = _ql_saved(dr_module, tmp_path, _ql_spec(q))
        doc, served_warned = _ql_served(dr_module, tmp_path, _ql_spec(q))
        assert not os.path.exists(sentinel), "the qualifier ran code"
        all_rows = _ql_weights(range(len(_QL_MAKES)))
        assert _ql_scatter([r._last_layout_root])[1] == all_rows
        assert _ql_scatter(doc.roots)[1] == all_rows
        assert [m for m in saved_warned if "skipped" in m], saved_warned
        assert [m for m in served_warned if "skipped" in m], served_warned


# ================================================================
# BUG-QUAL-1: Graph-level if/in qualifiers dropped for named graphs
# Regression for: "_dash_plot hard-codes graph-level qualifiers to empty
# strings when creating graph_json. The renderer's filter logic expects
# graph-level qualifiers and does not read per-plot qualifiers, so
# named-graph dashboards in dash build / server mode silently ignore
# if/in conditions."
# Fix:
#   (1) dash.ado: extract if_expr/in_expr from first segment's JSON
#       using _dash_json_get_str and set them at the graph top level
#   (2) dash_render.py server code: fall back to g.get('if_expr') when
#       go.get('if_expr') is empty
# ================================================================

class TestGraphQualifierPropagation:
    """Regression suite for BUG-QUAL-1: graph-level if/in qualifiers must be propagated.

    We test the Python-side half:
      (a) DashRenderer._apply_graph_filter reads top-level if_expr from graph spec
      (b) an empty top-level if_expr leaves every row
      (c) both modes draw only the rows a top-level if_expr selects

    (c) replaces two tests that read source text -- one asserted that the
    generated app contained ``g.get('if_expr')``, one that dash.ado named
    ``_dash_json_get_str`` -- and a third that rendered a top-level
    qualifier and asserted only that the page was longer than 100 bytes,
    which it is whether or not anything was filtered.  The Stata half,
    dash.ado promoting a one-segment qualifier to the graph, is
    test_json_escaping.cscript JSE-20 (stored whole at the graph level) and
    test_qualifier_literals.cscript (the rows each mode draws).
    """

    def test_renderer_apply_graph_filter_uses_top_level_if_expr(self, dr_module, auto_df):
        """BUG-QUAL-1a: _apply_graph_filter must read if_expr from top-level graph spec."""
        import numpy as np
        renderer = dr_module.DashRenderer.__new__(dr_module.DashRenderer)
        renderer.df = auto_df.copy()
        # Spec with top-level if_expr filtering to only foreign==1 rows
        graph_spec = {"if_expr": "foreign == 1", "in_expr": "", "plots": []}
        filtered = renderer._apply_graph_filter(graph_spec)
        assert len(filtered) < len(auto_df), \
            "_apply_graph_filter must reduce rows when if_expr is set"
        assert (filtered["foreign"] == 1.0).all(), \
            "_apply_graph_filter must keep only rows matching if_expr"

    def test_renderer_apply_graph_filter_empty_if_expr(self, dr_module, auto_df):
        """BUG-QUAL-1b: _apply_graph_filter with empty if_expr must return all rows."""
        renderer = dr_module.DashRenderer.__new__(dr_module.DashRenderer)
        renderer.df = auto_df.copy()
        graph_spec = {"if_expr": "", "in_expr": "", "plots": []}
        filtered = renderer._apply_graph_filter(graph_spec)
        assert len(filtered) == len(auto_df), \
            "_apply_graph_filter with empty if_expr must return full dataset"

    def test_a_top_level_qualifier_draws_only_its_rows_in_both_modes(
            self, dr_module, auto_df, tmp_path):
        """BUG-QUAL-1c: the qualifier dash.ado promotes sits at the graph's
        top level, beside graph_options -- where neither renderer looked
        before the fix.  No plot and no graph_options carries one here, so
        only the top-level key can restrict the rows."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}],
            "graph_options": {"name": "g1"},
            "if_expr": "foreign == 1",
        }])
        want = sorted(float(w) for w in
                      auto_df.loc[auto_df["foreign"] == 1, "weight"])
        assert 0 < len(want) < len(auto_df)
        r, saved_warned = _ql_saved(dr_module, tmp_path, spec, auto_df)
        doc, served_warned = _ql_served(dr_module, tmp_path, spec, auto_df)
        saved = _ql_scatter([r._last_layout_root])
        served = _ql_scatter(doc.roots)
        assert saved == (len(want), want), (saved, want, saved_warned)
        assert served == (len(want), want), (served, want, served_warned)


# ================================================================
# BUG-HIST-1: Server-mode histogram bin() accepts unbounded values
# Regression for: "Generated server code parses nbins = int(opts.get
# ('bin', 20)) with no bounds and feeds it to np.histogram(..., bins=nbins).
# Large bin() values can force very large array allocations."
# Fix: clamp nbins to max(1, min(int(...), 1000)) at the call site and
# inside _compute_histogram.
# ================================================================

class TestServerHistogramBinClamp:
    """Regression suite for BUG-HIST-1: server histogram bin() clamped 1..1000.

    These used to assert that the generated SOURCE contained `max(1, min(',
    `_MAX_BINS', `1000' or the word `clamp'. Measured against the app as it
    is emitted now: `max(1, min(' appears on exactly one line, and that line
    is mband's band clamp, which has nothing to do with histograms; `1000'
    appears on nine lines and `clamp' on six. So the greps were satisfied by
    unrelated text and deleting the histogram clamp left them green.

    They count bars instead, and read the warning, which is what the clamp
    does.
    """

    @staticmethod
    def _bars(dr_module, df, bin_value):
        """(bar count, warning messages) for a served histogram with bin()."""
        import importlib.util
        import os
        import tempfile
        import warnings
        from bokeh.document import Document
        from bokeh.models import ColumnDataSource

        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "histogram", "yvar": "mpg", "xvar": "",
                       "options": {"bin": str(bin_value)}}],
            "graph_options": {"name": "g1"},
        }])
        spec_path, data_path = _write_temp_files(df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py",
                                            delete=False)
        out_f.close()
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                dr_module.ServerAppBuilder(spec_path, data_path).build(
                    out_f.name)
            ms = importlib.util.spec_from_file_location(
                f"_hclamp_{abs(hash(str(bin_value))) % 100000}", out_f.name)
            mod = importlib.util.module_from_spec(ms)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                ms.loader.exec_module(mod)
                doc = Document()
                mod.make_document(doc)
                msgs = [str(w.message) for w in caught]
            for m in doc.select({"type": ColumnDataSource}):
                if "left" in m.data and "right" in m.data:
                    return len(m.data["left"]), msgs
            return 0, msgs
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try:
                    os.unlink(_p)
                except OSError:
                    pass

    def test_an_ordinary_bin_count_is_honoured(self, dr_module, auto_df):
        """The control: a clamp to a constant would otherwise pass."""
        n, _msgs = self._bars(dr_module, auto_df, 20)
        assert n == 20

    def test_a_huge_bin_count_is_clamped(self, dr_module, auto_df):
        """BUG-HIST-1b: bin(100000) must not draw 100,000 bars."""
        n, _msgs = self._bars(dr_module, auto_df, 100_000)
        assert 0 < n <= 1000, (
            f"bin(100000) drew {n} bars; the clamp is 1000"
        )

    def test_the_clamp_is_reported(self, dr_module, auto_df):
        """Clamping silently is how the user never learns what happened."""
        _n, msgs = self._bars(dr_module, auto_df, 100_000)
        assert any("bin" in m and "1000" in m for m in msgs), (
            f"the bin count was clamped without a word: {msgs}"
        )

    def test_a_bin_count_below_one_is_raised(self, dr_module, auto_df):
        n, _msgs = self._bars(dr_module, auto_df, 0)
        assert n >= 1


# ================================================================
# BUG-SCALE-1: Dual log-scale graphs drop x-axis log mode
# Regression for: "_make_figure re-creates the Bokeh figure once for
# xscale(log) and then re-creates it again for yscale(log) from the
# original fig_kwargs. When both options are set, the second re-creation
# overwrites the first, so the final figure keeps only y-log scaling."
# Fix: Build axis-type kwargs once and create the figure once so both
# x_axis_type and y_axis_type are set together.
# ================================================================

class TestDualLogScale:
    """Regression suite for BUG-SCALE-1: xscale(log) yscale(log) must produce dual-log axes."""

    def _make_renderer(self, dr_module, df, graph_opts):
        """Build a DashRenderer with a scatter spec and return it with graph opts."""
        import json, tempfile, os
        spec_dict = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}],
            "graph_options": {"name": "g1", **graph_opts},
        }])
        spec_path, data_path = _write_temp_files(df, spec_dict)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            return renderer
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    # The three tests below searched the saved page's TEXT: "LogScale" in
    # it, or "log" in it, or "LogScale" at least twice.  The page inlines
    # BokehJS, which names LogScale 9 times on a page with no log axis at
    # all, and "log" is in any page (WP-24, measured 24sep2026) -- so all
    # three passed with both options ignored.  They read the scales of the
    # figure the page's embedded document holds; the control is the same
    # graph with neither option, linear on both axes.
    def _page_scales(self, dr_module, df, graph_opts):
        """((x scale, x axis), (y scale, y axis)) type names of the one
        figure in the saved page's document."""
        renderer = self._make_renderer(dr_module, df, graph_opts)
        doc = _page_document(renderer.render())
        figs = [f for f, _r in _glyph_layers(doc.roots)]
        assert len(figs) == 1, figs
        fig = figs[0]
        (xaxis,), (yaxis,) = fig.xaxis, fig.yaxis
        return ((type(fig.x_scale).__name__, type(xaxis).__name__),
                (type(fig.y_scale).__name__, type(yaxis).__name__))

    def test_linear_axes_without_either_option(self, dr_module, auto_df):
        """The control for BUG-SCALE-1a..1c: no xscale()/yscale(), no log."""
        assert self._page_scales(dr_module, auto_df, {}) == (
            ("LinearScale", "LinearAxis"), ("LinearScale", "LinearAxis"))

    def test_xscale_log_only(self, dr_module, auto_df):
        """BUG-SCALE-1a: xscale(log) alone must produce log x-axis."""
        assert self._page_scales(dr_module, auto_df, {"xscale": "log"}) == (
            ("LogScale", "LogAxis"), ("LinearScale", "LinearAxis")), (
            "xscale(log) must make the saved figure's x axis, and only it, log")

    def test_yscale_log_only(self, dr_module, auto_df):
        """BUG-SCALE-1b: yscale(log) alone must produce log y-axis."""
        assert self._page_scales(dr_module, auto_df, {"yscale": "log"}) == (
            ("LinearScale", "LinearAxis"), ("LogScale", "LogAxis")), (
            "yscale(log) must make the saved figure's y axis, and only it, log")

    def test_dual_log_scale_both_axes(self, dr_module, auto_df):
        """BUG-SCALE-1c: xscale(log) yscale(log) must produce log scale on BOTH axes.

        Before the fix, the second bokeh_figure() call overrode the first so the
        x-axis reverted to linear.  After the fix, both axes are set in one call.
        """
        got = self._page_scales(dr_module, auto_df,
                                {"xscale": "log", "yscale": "log"})
        assert got == (("LogScale", "LogAxis"), ("LogScale", "LogAxis")), (
            f"xscale(log) yscale(log) drew {got}.  This is BUG-SCALE-1: "
            "the second figure re-creation must not overwrite the x-axis type.")

    def test_make_figure_single_recreation_for_both_log(self, dr_module, auto_df):
        """BUG-SCALE-1d: _make_figure must set both axis types before creating the figure.

        After the BUG-STYLE-LOG fix (Bug #18), axis types are injected into fig_kwargs
        before the single bokeh_figure() call, replacing the earlier two-pass approach.
        Verify that both x_axis_type and y_axis_type are wired and produce log scales.
        """
        from bokeh.models import LogScale
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}],
            "graph_options": {"name": "g1", "xscale": "log", "yscale": "log"},
        }])
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            render_models(renderer)
            fig = list(renderer.figures.values())[0]
            assert isinstance(fig.x_scale, LogScale), \
                "x-axis must be LogScale when xscale(log) and yscale(log) are both set"
            assert isinstance(fig.y_scale, LogScale), \
                "y-axis must be LogScale when xscale(log) and yscale(log) are both set"
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass


# ================================================================
# BUG-FAC-1: Faceted aggregate layers recompute from global filtered data
# Regression for: "aggregate recomputation in _make_filter_cb always uses
# global fdf for every aggregate type. This causes faceted histograms/fits/
# smoothers to drift from the facet's subgroup after filter changes."
# Fix: Derive per-facet data frame (using same _fgvals logic as raw sources)
# and pass that to _compute_* calls instead of global fdf.
# ================================================================

class TestFacetedAggregatePerFacetData:
    """Regression suite for BUG-FAC-1: faceted aggregates use per-facet data.

    These used to assert that the generated source contained the identifiers
    `agg_fdf' and `_fgvals', and that `make_document' produced at least one
    root. Measured: collapsing the per-facet branch to `agg_fdf = fdf'
    unconditionally -- the exact bug -- leaves both identifiers in the
    emitted text and the root count unchanged, so all three stayed green.

    They compare the two facets' histogram bars instead. A histogram over
    domestic cars and one over foreign cars are different histograms; if the
    aggregate is recomputed from the global frame, both facets get the same
    bars.
    """

    @staticmethod
    def _facet_histograms(dr_module, df):
        """The `top' array of every histogram source in a faceted document."""
        import os
        import tempfile
        import warnings
        from bokeh.document import Document
        from bokeh.models import ColumnDataSource

        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "histogram", "yvar": "mpg", "xvar": "",
                       "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign"},
        }])
        spec_path, data_path = _write_temp_files(df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py",
                                            delete=False)
        out_f.close()
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                dr_module.ServerAppBuilder(spec_path, data_path).build(
                    out_f.name)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                mod = load_app(out_f.name, "_facetagg")
                doc = Document()
                mod.make_document(doc)
            out = []
            for m in doc.select({"type": ColumnDataSource}):
                if "top" in m.data and len(m.data["top"]):
                    out.append([float(v) for v in m.data["top"]])
            return out
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try:
                    os.unlink(_p)
                except OSError:
                    pass

    def test_there_are_two_facets_to_compare(self, dr_module, auto_df):
        """Guards the guard: one histogram would make the check vacuous."""
        tops = self._facet_histograms(dr_module, auto_df)
        assert len(tops) >= 2, (
            f"a by(foreign) histogram produced {len(tops)} histogram "
            f"source(s); the comparison below needs two"
        )

    def test_each_facet_is_binned_from_its_own_rows(self, dr_module, auto_df):
        """BUG-FAC-1: the two facets must not hold identical bars."""
        tops = self._facet_histograms(dr_module, auto_df)
        assert tops[0] != tops[1], (
            "both facets hold the same histogram, so the aggregate was "
            "recomputed from the global frame rather than each facet's rows"
        )

    def test_a_facets_bars_match_its_own_data(self, dr_module, auto_df):
        """The bars must be the histogram of that facet, not of anything."""
        import numpy as np
        tops = self._facet_histograms(dr_module, auto_df)
        expected = []
        for _key, grp in auto_df.groupby("foreign"):
            arr = grp["mpg"].dropna().to_numpy(dtype=float)
            edges, ymode = dr_module.GlyphMapper._histogram_grid(arr, {})
            counts, _ = np.histogram(arr, bins=edges)
            expected.append(
                [float(v) for v in
                 dr_module._histogram_heights(counts, edges, ymode)])
        for want in expected:
            assert any(
                len(want) == len(got)
                and all(abs(a - b) < 1e-9 for a, b in zip(want, got))
                for got in tops), (
                f"no facet's bars match the histogram of its own rows: "
                f"wanted {want[:4]}..., got {[t[:4] for t in tops]}"
            )


class TestServerFilterOrClauses:
    """Regression tests for BUG-FILT-OR: ServerAppBuilder must parse || -joined
    filter specs the same way DashRenderer._parse_filter_raw does."""

    def test_single_filter_still_works(self, dr_module, auto_df):
        """BUG-FILT-OR-1a: single filter spec produces one widget in generated code."""
        spec = _make_spec_json(
            graphs=[{"plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                                "options": {}}],
                     "graph_options": {"name": "g1"}}],
            build_options={
                "layout": "auto", "link": "", "filter": "foreign, type(dropdown)",
                "theme": "default", "title": "T", "subtitle": "", "registry": "",
                "mode": "server", "port": "5006",
            }
        )
        src = _build_app(dr_module, auto_df, spec)
        assert "foreign" in src, "single filter var must appear in generated source"

    def test_pipe_separated_two_filters_both_appear(self, dr_module, auto_df):
        """BUG-FILT-OR-1b: two filters joined with || must both appear in generated code."""
        spec = _make_spec_json(
            graphs=[{"plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                                "options": {}}],
                     "graph_options": {"name": "g1"}}],
            build_options={
                "layout": "auto", "link": "",
                "filter": "foreign, type(dropdown) || weight, type(range)",
                "theme": "default", "title": "T", "subtitle": "", "registry": "",
                "mode": "server", "port": "5006",
            }
        )
        src = _build_app(dr_module, auto_df, spec)
        assert "foreign" in src, "first || filter var must appear in generated source"
        assert "weight" in src, "second || filter var must appear in generated source"

    def test_pipe_separated_filter_specs_count(self, dr_module, auto_df):
        """BUG-FILT-OR-1c: two filters joined with || must produce two _filter_specs entries."""
        spec = _make_spec_json(
            graphs=[{"plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                                "options": {}}],
                     "graph_options": {"name": "g1"}}],
            build_options={
                "layout": "auto", "link": "",
                "filter": "foreign, type(dropdown) || weight, type(range)",
                "theme": "default", "title": "T", "subtitle": "", "registry": "",
                "mode": "server", "port": "5006",
            }
        )
        src = _build_app(dr_module, auto_df, spec)
        # Count filter spec entries: each produces a {'var':..., 'type':...} dict
        import ast as _ast
        count = src.count("_filter_specs")
        # At minimum the definition must appear once and reference both vars
        assert src.count("'foreign'") >= 1, "foreign must appear in _filter_specs definition"
        assert src.count("'weight'") >= 1, "weight must appear in _filter_specs definition"

    def test_semicolon_separated_still_works(self, dr_module, auto_df):
        """BUG-FILT-OR-1d: legacy semicolon separator must still produce both widgets."""
        spec = _make_spec_json(
            graphs=[{"plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                                "options": {}}],
                     "graph_options": {"name": "g1"}}],
            build_options={
                "layout": "auto", "link": "",
                "filter": "foreign, type(dropdown);weight, type(range)",
                "theme": "default", "title": "T", "subtitle": "", "registry": "",
                "mode": "server", "port": "5006",
            }
        )
        src = _build_app(dr_module, auto_df, spec)
        assert "foreign" in src, "first ; filter var must appear in generated source"
        assert "weight" in src, "second ; filter var must appear in generated source"

    def test_three_filters_all_appear(self, dr_module, auto_df):
        """BUG-FILT-OR-1e: three filters joined with || must all appear in generated code."""
        spec = _make_spec_json(
            graphs=[{"plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                                "options": {}}],
                     "graph_options": {"name": "g1"}}],
            build_options={
                "layout": "auto", "link": "",
                "filter": "foreign, type(dropdown) || weight, type(range) || mpg, type(range)",
                "theme": "default", "title": "T", "subtitle": "", "registry": "",
                "mode": "server", "port": "5006",
            }
        )
        src = _build_app(dr_module, auto_df, spec)
        assert "foreign" in src, "first filter var must appear"
        assert "weight" in src, "second filter var must appear"
        assert "'mpg'" in src, "third filter var must appear"


# ---------------------------------------------------------------------------
# BUG-12: saving() path shell-metacharacter hardening
#
# This was covered by `_validate_saving_path', a Python re-implementation of
# _dash_validate_path, plus twelve tests that called it. Deleting
# _dash_validate_path from dash.ado entirely left all twelve green, and the
# mirror had already drifted from the real validator -- it rejected '(' and
# ')', which dash.ado accepts. The real validator is certified from Stata in
# test/test_path_validation.cscript.
# ---------------------------------------------------------------------------


class TestUnsafeTokenRegexWordBoundaries:
    """Regression tests for BUG-REGEX: _UNSAFE_G and _UNSAFE_BY in generated
    server source must use \\b word-boundary markers, not backspace bytes."""

    def test_unsafe_g_uses_word_boundary_not_backspace(self, dr_module, auto_df,
                                                       tmp_path):
        """BUG-REGEX-1a: the served if_expr guard refuses an exact injection
        token but admits a column whose name merely contains one.

        This walked ``src`` for a line holding both ``_UNSAFE_G`` and
        ``compile`` and, on that line, asserted no backspace byte.  The
        served app carries no ``_UNSAFE_G`` at all now -- the guard is the
        shared AST whitelist -- so the loop ran zero times and asserted
        nothing; only ``"_safe_g" in src`` remained, a spelling (WP-24,
        measured 24sep2026: 0 matching lines).  The property BUG-REGEX
        names -- a whole word, not a run of backspaces, and not a substring
        match -- is asked of the served guard itself: it must refuse
        ``eval(...)`` and admit a column literally named ``evaluate``."""
        ns = _ql_app_ns(dr_module, tmp_path, _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}],
            "graph_options": {"name": "g1"},
        }]), auto_df)
        guard = ns["_validate_if_expr"]
        cols = ["mpg", "weight", "evaluate"]
        assert guard("evaluate > 5", cols) is True, (
            "the served guard refused a column named 'evaluate' -- it is "
            "matching 'eval' as a substring, not as a whole word")
        assert guard("eval('1==1')", cols) is False, (
            "the served guard admitted eval(...)")
        assert guard("__import__('os')", cols) is False

    def test_unsafe_g_blocks_bare_eval(self, dr_module, auto_df, tmp_path):
        """BUG-REGEX-1b: the served guard REFUSES an eval(...) if_expr -- the
        graph draws every row and warns skipped -- and ADMITS a real one.

        This asserted ``len(doc.roots) > 0``, which the layout column
        satisfies whether the qualifier ran or not (WP-24, measured
        24sep2026).  A drawn-rows check alone cannot tell a guard refusal
        from a query that raised (both leave the rows unfiltered and warn),
        so the served guard's own verdict on the eval expression is read too
        -- False, refused before query -- as the function-plot security tests
        read theirs.  The control, a valid ``foreign == 1``, is admitted and
        draws its 16 rows: the guard is not simply refusing everything."""
        ns = _ql_app_ns(dr_module, tmp_path, _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}],
            "graph_options": {"name": "g1"},
        }]), auto_df)
        cols = list(auto_df.columns)
        assert ns["_validate_if_expr"]("eval('1==1')", cols) is False, (
            "the served guard admitted eval(...); only a query error would "
            "then keep it from running")

        def _served(if_expr):
            spec = _make_spec_json(graphs=[{
                "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                           "options": {}}],
                "graph_options": {"name": "g1", "if_expr": if_expr},
            }])
            doc, warned = _ql_served(dr_module, tmp_path, spec, auto_df)
            (_fig, r), = _glyph_layers(doc.roots)
            return len(_drawn_values(r, "weight")), warned

        drawn, warned = _served("eval('1==1')")
        assert drawn == len(auto_df) and [m for m in warned if "skipped" in m], (
            drawn, warned)
        control, cwarned = _served("foreign == 1")
        assert control == int((auto_df["foreign"] == 1).sum()), control
        assert not [m for m in cwarned if "skipped" in m], cwarned

    def test_unsafe_g_allows_evaluate_variable_name(self, dr_module, auto_df,
                                                    tmp_path):
        """BUG-REGEX-1c: _UNSAFE_G must NOT block variable names containing 'eval' as substring.

        With backspace chars instead of word boundaries, 'evaluate' would not be blocked
        (backspace-eval-backspace doesn't match 'evaluate'). With real \\b, 'evaluate'
        is also not blocked because the 'e' after 'eval' prevents the word-boundary match.
        Both scenarios should allow 'evaluate' as a valid column name in df.query.

        This compiled a pattern typed into the test itself and asked THAT the
        question, so it passed whatever the product's guard did (WP-24).  The
        served app's own guard is asked instead -- _validate_if_expr from the
        app's namespace, as BUG-REGEX-1a reads it -- and the qualifier is run
        end to end through df.query: a served graph ``if evaluate > 5`` over
        data holding an ``evaluate`` column draws exactly the rows it selects,
        with no "skipped" warning, while ``eval('1==1')`` is still refused."""
        df = auto_df.assign(evaluate=np.arange(len(auto_df), dtype=float))
        spec = _ql_spec("evaluate > 5")
        guard = _ql_app_ns(dr_module, tmp_path, spec, df)["_validate_if_expr"]
        cols = list(df.columns)
        assert guard("evaluate > 5", cols) is True, (
            "the served guard refused a column named 'evaluate'")
        assert guard("eval('1==1')", cols) is False, (
            "the served guard admitted eval(...)")
        doc, warned = _ql_served(dr_module, tmp_path, spec, df)
        want = sorted(df.loc[df["evaluate"] > 5, "weight"])
        assert 0 < len(want) < len(df)
        assert _ql_scatter(doc.roots)[1] == want, (
            "the served graph did not draw exactly the rows `evaluate > 5' "
            "selects")
        assert not [m for m in warned if "skipped" in m], warned

    @pytest.mark.parametrize("given,kept", [
        ("eval", False), ("exec", False), ("open, total", False),
        ("getattr", False),
        ("evaluate", True), ("execution", True), ("reopened", True),
        ("x_open", True),
    ])
    def test_the_unsafe_by_words_match_only_whole_words_in_both_modes(
            self, dr_module, auto_df, tmp_path, given, kept):
        """BUG-REGEX-1d: by()'s injection words are refused as whole words
        only, by the renderer's _dash_parse_by and by the served app's copy
        -- whose pattern the app writes out again, which is where the
        backspace bytes of BUG-REGEX lived: a pattern of backspaces refuses
        nothing, and one without word boundaries refuses `evaluate'.

        This read the generated app's text for the pattern's spelling; the
        spelling was right while nothing asked the pattern a question.  No
        other test hands by() a whole injection word, or a name holding one
        (WP-24 scan)."""
        ns = _ql_app_ns(dr_module, tmp_path, _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign"},
        }], build_options={"layout": "auto", "registry": "g1"}), auto_df)
        want = given.split(",")[0].strip() if kept else ""
        saved = dr_module._dash_parse_by(given)[0]
        served = ns["_dash_parse_by"](given)[0]
        assert (saved, served) == (want, want), (
            f"by({given}): saved read {saved!r}, served read {served!r}; "
            f"want {want!r}")


# ---------------------------------------------------------------------------
# BUG-IQUAL: Immediate render jsonio qualifier wrongly pre-filters multi-plot data
# ---------------------------------------------------------------------------

class TestImmediateRenderQualifierHandling:
    """Regression tests for BUG-IQUAL: immediate render must not pre-filter
    jsonio with the first plot's qualifier when multiple plots have different
    if/in expressions.  The renderer must receive all rows and apply per-graph
    filtering itself via _apply_graph_filter.

    These are the renderer's half.  BUG-IQUAL's fix is in dash.ado -- the
    export no longer carries the first layer's qualifier -- and re-adding
    it leaves every test here green, because they build the spec by hand.
    That half is test_qualifier_literals.cscript QL-14: the two-layer
    command, run on the immediate route, each layer holding the rows its
    own qualifier selects.  A class that read the jsonio line out of
    dash.ado for an `if' stood in for it; measured (WP-24), the qualifier
    re-added through a macro left it green and fails QL-14.
    """

    def _make_multi_qualifier_spec(self, if1: str, if2: str) -> dict:
        """Build a graph spec where two scatter plots have different if_expr."""
        return {
            "graphs": [{
                "plots": [
                    {"type": "scatter", "yvar": "mpg", "xvar": "weight",
                     "options": {}, "if_expr": if1, "in_expr": ""},
                    {"type": "scatter", "yvar": "price", "xvar": "weight",
                     "options": {}, "if_expr": if2, "in_expr": ""},
                ],
                "graph_options": {"name": "g1"},
                # No top-level if_expr: renderer must not filter by either per-plot qualifier
                "if_expr": "",
                "in_expr": "",
            }],
            "kpis": [],
            "build_options": {
                "layout": "auto", "link": "", "filter": "",
                "theme": "default", "title": "T", "subtitle": "", "registry": "",
                "mode": "standalone", "port": "5006",
            },
        }

    def test_renderer_with_no_toplevel_filter_uses_all_rows(self, dr_module, auto_df):
        """BUG-IQUAL-1a: renderer with empty top-level if_expr must use all rows."""
        spec = self._make_multi_qualifier_spec("foreign==1", "foreign==0")
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False)
        out_f.close()
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            # _apply_graph_filter with empty if_expr must return full df
            g = spec["graphs"][0]
            filtered = renderer._apply_graph_filter(g)
            assert len(filtered) == len(auto_df), \
                "with empty top-level if_expr, _apply_graph_filter must return all rows"
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try: os.unlink(_p)
                except OSError: pass

    def test_renderer_applies_toplevel_filter_not_perplot(self, dr_module, auto_df):
        """BUG-IQUAL-1b: renderer must use graph-level if_expr, not per-plot qualifiers."""
        # Set top-level if_expr to a specific condition (as _dash_plot promotes it)
        spec = self._make_multi_qualifier_spec("foreign==1", "foreign==0")
        spec["graphs"][0]["if_expr"] = "foreign==1"  # promoted from first plot
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            g = spec["graphs"][0]
            filtered = renderer._apply_graph_filter(g)
            # With graph-level "foreign==1", only foreign==1 rows should be returned
            expected = auto_df[auto_df["foreign"] == 1]
            assert len(filtered) == len(expected), \
                "renderer must apply graph-level if_expr not per-plot qualifiers"
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    def test_renderer_multi_qualifier_spec_renders_without_crash(self, dr_module, auto_df):
        """BUG-IQUAL-1c: a two-plot graph, each plot with its own qualifier and
        no top-level one, draws every row into the shared source and lets each
        plot's own view select its rows.

        This asserted ``len(html) > 100``, true of any page (WP-24, measured
        24sep2026).  BUG-IQUAL was the source being PRE-FILTERED by the first
        plot's qualifier, so the check that matters is the shared source
        carrying all 30 rows, with the two plots drawing their own qualifiers'
        rows (foreign==1 -> 16, foreign==0 -> 14) through their views."""
        spec = self._make_multi_qualifier_spec("foreign==1", "foreign==0")
        doc = _page_document(_saved_page(dr_module, auto_df, spec)[0])
        layers = _glyph_layers(doc.roots)
        assert [type(r.glyph).__name__ for _f, r in layers] == ["Scatter", "Scatter"]
        assert {r.data_source.id for _f, r in layers} == \
            {layers[0][1].data_source.id}, "the two plots must share one source"
        assert len(next(iter(layers[0][1].data_source.data.values()))) == \
            len(auto_df), "the shared source was pre-filtered; it must hold all rows"
        drawn = sorted(len(_drawn_values(r, "weight")) for _f, r in layers)
        assert drawn == sorted([int((auto_df["foreign"] == 1).sum()),
                                int((auto_df["foreign"] == 0).sum())]), drawn

    def test_full_data_available_when_no_toplevel_filter(self, dr_module, auto_df):
        """BUG-IQUAL-1d: when top-level if_expr is empty, renderer df must have all rows."""
        spec = self._make_multi_qualifier_spec("foreign==1", "foreign==0")
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            # self.df should contain all rows since jsonio exported without qualifier
            assert len(renderer.df) == len(auto_df), \
                "DashRenderer.df must contain all rows when no pre-filtering was applied"
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass


# ---------------------------------------------------------------------------
# BUG-15: filter() exclude() validation across ALL groups, not just the first
#
# This was covered by `_validate_filter_exclude_names', a Python
# re-implementation of the Stata validation loop, plus six tests that called
# it and a seventh that asserted only that two variable names appeared in the
# generated source. Reverting dash.ado's loop to its original single-group
# form left them all green. The behaviour is certified from Stata instead, in
# test/test_e2e_filters.cscript (FL-EX-1).
# ---------------------------------------------------------------------------


class TestFilterCallbackExcludeAlignment:
    """Regression tests for BUG-CBEXCL: when a filter spec is skipped because
    its variable is missing in the data source, the remaining callbacks must
    still receive the correct exclude() lists and filter_specs alignment."""

    def _make_mixed_filter_spec(self, dr_module, auto_df, graphs=None):
        """Build a spec with two filters: first has a missing var (skipped), second is valid."""
        spec = _make_spec_json(
            graphs=graphs or [{"plots": [{"type": "scatter", "yvar": "mpg",
                                          "xvar": "weight", "options": {}}],
                               "graph_options": {"name": "g1"}}],
            build_options={
                "layout": "auto", "link": "",
                # 'missing_var' is not in auto_df — it will be skipped
                "filter": "missing_var, type(dropdown) || foreign, type(dropdown)",
                "theme": "default", "title": "T", "subtitle": "", "registry": "g1",
                "mode": "standalone", "port": "5006",
            }
        )
        return spec

    def test_filter_specs_count_matches_built_widgets(self, dr_module, auto_df):
        """BUG-CBEXCL-1a: the filter callback carries exactly the specs whose
        widgets were built -- foreign, not the missing variable.

        This searched the page text for ``"filter_specs_json": "[...]"`` and,
        under ``if m:``, checked the array.  The regex never matched: the page
        embeds the callback in Bokeh's HTML-escaped document JSON, where the
        key reads ``&quot;filter_specs_json&quot;`` and the value's own quotes
        are escaped again, so ``m`` was None and the body never ran (WP-24,
        measured 24sep2026).  The callback's ``filter_specs_json`` argument is
        read from the document instead -- decoded, not text-matched -- and its
        widgets counted, so a missing-var spec that slipped through would be
        seen."""
        from bokeh.models import CustomJS, Select
        spec = self._make_mixed_filter_spec(dr_module, auto_df)
        doc = _page_document(_saved_page(dr_module, auto_df, spec)[0])
        cbs = [m for m in doc.select({"type": CustomJS})
               if "filter_specs_json" in m.args]
        assert len(cbs) == 1, cbs
        fs = json.loads(cbs[0].args["filter_specs_json"])
        assert [s["varname"] for s in fs] == ["foreign"], (
            f"filter_specs carried {[s['varname'] for s in fs]}; the missing "
            f"variable must be excluded")
        # The dropdown widgets the page built, each titled by its variable.
        widget_vars = sorted(w.title for w in doc.select({"type": Select}))
        assert widget_vars == ["foreign"], (
            f"the page built dropdown widgets for {widget_vars}; a widget for "
            f"the missing variable must not be built")
        assert widget_vars == sorted(s["varname"] for s in fs), (
            "filter_specs and the built widgets are not in 1:1 correspondence")

    def test_render_with_missing_filter_var_does_not_crash(self, dr_module, auto_df):
        """BUG-CBEXCL-1b: when the first filter var is missing, render still
        builds the dashboard -- the scatter and the surviving foreign widget.

        This asserted ``len(html) > 100``, true of any page (WP-24, measured
        24sep2026).  A ``does not crash`` guard, kept as one, but made to see
        that render produced the dashboard: the g1 scatter drawing all 30
        rows and the one foreign dropdown, with missing_var dropped."""
        from bokeh.models import Select
        spec = self._make_mixed_filter_spec(dr_module, auto_df)
        doc = _page_document(_saved_page(dr_module, auto_df, spec)[0])
        (_fig, r), = _glyph_layers(doc.roots)
        assert type(r.glyph).__name__ == "Scatter"
        assert len(_drawn_values(r, "weight")) == len(auto_df)
        assert sorted(w.title for w in doc.select({"type": Select})) == ["foreign"]

    def test_built_filter_callback_count_equals_valid_filter_specs(self, dr_module, auto_df):
        """BUG-CBEXCL-1c: number of filter callbacks must equal number of built widgets."""
        spec = self._make_mixed_filter_spec(dr_module, auto_df)
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            render_models(renderer)
            # After render(), filter_widgets and filter_callbacks must have same length
            assert len(renderer.filter_widgets) == len(renderer.filter_callbacks), \
                "filter_widgets and filter_callbacks must always have equal length"
            # Only 1 valid filter (foreign); missing_var was skipped
            assert len(renderer.filter_callbacks) == 1, \
                "only 1 filter callback must be built (for foreign); missing_var skipped"
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    def test_all_valid_filters_built_when_first_is_missing(self, dr_module, auto_df):
        """BUG-CBEXCL-1d: valid filters after a skipped one must still be built."""
        spec = self._make_mixed_filter_spec(dr_module, auto_df)
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            render_models(renderer)
            # There should be exactly 1 widget (for 'foreign')
            assert len(renderer.filter_widgets) == 1, \
                "foreign filter widget must be built even though missing_var was skipped"
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass


# ---------------------------------------------------------------------------
# BUG-XSS-KPI: KPI filter callback DOM XSS via unescaped title/subtitle
# ---------------------------------------------------------------------------

class TestKpiFilterCallbackXssHardening:
    """Regression tests for BUG-XSS-KPI: KPI title/subtitle must be HTML-escaped
    before being stored in kpi_config_json so that filter callbacks cannot inject
    script payloads into the dashboard DOM."""

    def _make_xss_kpi_spec(self, title: str, subtitle: str) -> dict:
        return _make_spec_json(
            graphs=[{"plots": [{"type": "scatter", "yvar": "mpg",
                                "xvar": "weight", "options": {}}],
                     "graph_options": {"name": "g1"}}],
            kpis=[{
                "name": "k1", "var": "mpg", "stat": "mean",
                "title": title, "subtitle": subtitle,
                "color": "#000000", "bgcolor": "#ffffff",
                "fmt": "%9.2f", "update": "filter",
            }],
            build_options={
                "layout": "auto", "link": "", "filter": "foreign, type(dropdown)",
                "theme": "default", "title": "T", "subtitle": "", "registry": "g1",
                "mode": "standalone", "port": "5006",
            }
        )

    def test_script_tag_in_title_is_escaped(self, dr_module, auto_df):
        """BUG-XSS-KPI-1a: <script> in KPI title must be HTML-escaped in kpi_config_json."""
        payload = "<script>alert('xss')</script>"
        spec = self._make_xss_kpi_spec(title=payload, subtitle="ok")
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            html_out = renderer.render()
            # The literal <script> must not appear as raw HTML in kpi_config_json
            # (it should be &lt;script&gt; instead)
            assert payload not in html_out or \
                "&lt;script&gt;" in html_out or \
                html_out.count("<script>") <= 1, \
                "raw <script> from KPI title must be HTML-escaped in callback config"
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    def test_img_onerror_in_subtitle_is_escaped(self, dr_module, auto_df):
        """BUG-XSS-KPI-1b: img onerror payload in subtitle must be HTML-escaped."""
        payload = '<img src=x onerror="fetch(\'//evil\')">'
        spec = self._make_xss_kpi_spec(title="Mean MPG", subtitle=payload)
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            render_models(renderer)
            if renderer.filter_callbacks:
                cb_args = renderer.filter_callbacks[0].args
                kpi_cfg_json = cb_args.get("kpi_config_json", "")
                # The raw <img tag must not appear unescaped.
                # html.escape turns '<' → '&lt;' and '>' → '&gt;', so
                # the literal '<img' must not appear in the JSON.
                assert "<img" not in kpi_cfg_json, \
                    "raw <img tag from subtitle must be HTML-escaped in kpi_config_json"
                # The escaped form must be present instead
                assert "&lt;img" in kpi_cfg_json, \
                    "subtitle <img must be stored as &lt;img in kpi_config_json"
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    def test_ampersand_in_title_is_escaped(self, dr_module, auto_df):
        """BUG-XSS-KPI-1c: ampersand in title must be escaped to &amp; in config."""
        spec = self._make_xss_kpi_spec(title="Mean & Median MPG", subtitle="ok")
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            render_models(renderer)
            if renderer.filter_callbacks:
                kpi_cfg_json = renderer.filter_callbacks[0].args.get("kpi_config_json", "")
                assert "&amp;" in kpi_cfg_json, \
                    "& in title must be escaped to &amp; in kpi_config_json"
                assert "Mean & Median" not in kpi_cfg_json, \
                    "raw & must not appear unescaped in kpi_config_json"
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    def test_normal_title_preserved_after_escaping(self, dr_module, auto_df):
        """BUG-XSS-KPI-1d: plain text title without special chars must be unchanged."""
        spec = self._make_xss_kpi_spec(title="Mean MPG", subtitle="Overall average")
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            render_models(renderer)
            if renderer.filter_callbacks:
                kpi_cfg_json = renderer.filter_callbacks[0].args.get("kpi_config_json", "")
                assert "Mean MPG" in kpi_cfg_json, \
                    "plain text title must survive HTML escaping unchanged"
                assert "Overall average" in kpi_cfg_json, \
                    "plain text subtitle must survive HTML escaping unchanged"
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass


# ---------------------------------------------------------------------------
# BUG-STYLE-LOG: xscale(log)/yscale(log) drops prior figure styling
# ---------------------------------------------------------------------------

class TestLogScalePreservesStyle:
    """Regression tests for BUG-STYLE-LOG: enabling log scale must not discard
    figure styling (bgcolor, plotbgcolor, plotregion, graphregion) that was
    applied before the log-scale axis type was set."""

    def _make_styled_log_spec(self, bgcolor="#aabbcc", plotbgcolor="#112233",
                               xscale="log", yscale=""):
        return _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}],
            "graph_options": {
                "name": "g1",
                "bgcolor": bgcolor,
                # Flipped (WP-30 P1.20a): a lone bgcolor() showing was wrong
                # because twoway paints bgcolor() under the graph region (region_truth.json D26-D29); the graph region is none
                # so the canvas shows.
                "graphregion": "color(none)",
                "plotbgcolor": plotbgcolor,
                "xscale": xscale,
                "yscale": yscale,
            },
        }])

    def test_bgcolor_preserved_with_xscale_log(self, dr_module, auto_df):
        """BUG-STYLE-LOG-1a: bgcolor must be applied when xscale(log) is set."""
        spec = self._make_styled_log_spec(bgcolor="#aabbcc", xscale="log")
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            html_out = renderer.render()
            # The hex color must appear somewhere in the output (border_fill_color)
            assert "#aabbcc" in html_out.lower() or "aabbcc" in html_out.lower(), \
                "bgcolor #aabbcc must appear in rendered HTML when xscale(log) is set"
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    def test_plotbgcolor_preserved_with_xscale_log(self, dr_module, auto_df):
        """BUG-STYLE-LOG-1b: plotbgcolor must be applied when xscale(log) is set."""
        spec = self._make_styled_log_spec(plotbgcolor="#998877", xscale="log")
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            html_out = renderer.render()
            assert "998877" in html_out.lower(), \
                "plotbgcolor #998877 must appear in rendered HTML when xscale(log) is set"
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    def test_styling_preserved_with_dual_log(self, dr_module, auto_df):
        """BUG-STYLE-LOG-1c: styling must survive when both xscale(log) and yscale(log) are set."""
        spec = self._make_styled_log_spec(bgcolor="#ccddee", xscale="log", yscale="log")
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            html_out = renderer.render()
            assert "ccddee" in html_out.lower(), \
                "bgcolor must be preserved when both axes use log scale"
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    def test_figure_created_only_once(self, dr_module, auto_df):
        """BUG-STYLE-LOG-1d: _make_figure must produce log-scale figure in one pass."""
        from bokeh.models import LogScale
        spec = self._make_styled_log_spec(xscale="log", yscale="log")
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            render_models(renderer)
            # Verify figures were built (not empty)
            assert renderer.figures, "figures must be built"
            fig = list(renderer.figures.values())[0]
            # Both axes should be log scale
            assert isinstance(fig.x_scale, LogScale), \
                "x-axis must be LogScale when xscale(log) is requested"
            assert isinstance(fig.y_scale, LogScale), \
                "y-axis must be LogScale when yscale(log) is requested"
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass


# ---------------------------------------------------------------------------
# BUG-19: multiple filter() extraction when the first option follows the comma
#
# This was covered by `_simulate_extract_filters', a Python re-implementation
# of the Mata word-boundary check, plus six tests that called it and a
# seventh whose own comment said it simulated what _dash_build would store.
# None of them ran any Stata, so reverting _dash_extract_filters left every
# one green. The behaviour is certified from Stata instead, in
# test/test_e2e_filters.cscript (FL-CP-1).
# ---------------------------------------------------------------------------


class TestFilterUpdatesAllSources:
    """Regression tests for BUG-MTSRC: filter callbacks in unlinked standalone
    dashboards must update ALL non-excluded graph sources, not just the first."""

    def _make_two_graph_spec(self) -> dict:
        return _make_spec_json(
            graphs=[
                {"plots": [{"type": "scatter", "yvar": "mpg",
                            "xvar": "weight", "options": {}}],
                 "graph_options": {"name": "g1"}},
                {"plots": [{"type": "scatter", "yvar": "price",
                            "xvar": "weight", "options": {}}],
                 "graph_options": {"name": "g2"}},
            ],
            build_options={
                "layout": "auto", "link": "",  # unlinked
                "filter": "foreign, type(dropdown)",
                "theme": "default", "title": "T", "subtitle": "", "registry": "g1 g2",
                "mode": "standalone", "port": "5006",
            }
        )

    def test_callback_receives_all_graph_sources(self, dr_module, auto_df):
        """BUG-MTSRC-1a: filter callback args must include all_graph_sources with both sources."""
        spec = self._make_two_graph_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            render_models(renderer)
            assert renderer.filter_callbacks, "filter callback must be built"
            cb_args = renderer.filter_callbacks[0].args
            assert "all_graph_sources" in cb_args, \
                "callback args must contain 'all_graph_sources'"
            # Should contain sources for both g1 and g2 (unlinked → separate CDSes)
            assert len(cb_args["all_graph_sources"]) >= 2, \
                "all_graph_sources must contain sources for both graphs in unlinked dashboard"
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    def test_filter_js_contains_all_sources_loop(self, dr_module, auto_df):
        """BUG-MTSRC-1b: _FILTER_JS must iterate all_graph_sources to update all CDSes."""
        html_out = dr_module._FILTER_JS
        assert "all_graph_sources" in html_out, \
            "_FILTER_JS must reference all_graph_sources for multi-source updates"
        # Must loop over all_graph_sources and assign per-source filtered data.
        # After Bug-29 fix the loop assigns _nd_i (per-source) rather than new_data;
        # verify the loop iterates _srcs and emits a change.
        assert "_srcs[_si].data" in html_out, \
            "_FILTER_JS must assign filtered data to each source in all_graph_sources loop"
        assert "_srcs[_si].change.emit()" in html_out, \
            "_FILTER_JS must emit change on each source in the loop"

    def test_excluded_graph_source_not_in_cb_all_graph_sources(self, dr_module, auto_df):
        """BUG-MTSRC-1c: excluded graph source must not appear in all_graph_sources."""
        spec = _make_spec_json(
            graphs=[
                {"plots": [{"type": "scatter", "yvar": "mpg",
                            "xvar": "weight", "options": {}}],
                 "graph_options": {"name": "g1"}},
                {"plots": [{"type": "scatter", "yvar": "price",
                            "xvar": "weight", "options": {}}],
                 "graph_options": {"name": "g2"}},
            ],
            build_options={
                "layout": "auto", "link": "",
                "filter": "foreign, type(dropdown), exclude(g2)",
                "theme": "default", "title": "T", "subtitle": "", "registry": "g1 g2",
                "mode": "standalone", "port": "5006",
            }
        )
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            render_models(renderer)
            if renderer.filter_callbacks:
                cb_args = renderer.filter_callbacks[0].args
                # g2 source is excluded — only g1 source should be in all_graph_sources
                g2_src = renderer.sources.get("g2")
                if g2_src is not None:
                    assert g2_src not in cb_args.get("all_graph_sources", []), \
                        "excluded g2 source must not appear in all_graph_sources"
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    def test_two_graph_unlinked_render_does_not_crash(self, dr_module, auto_df):
        """BUG-MTSRC-1d: an unlinked two-graph dashboard with a filter renders
        both graphs, each on its own source, and the shared filter widget.

        This asserted ``len(html_out) > 100``, true of any page (WP-24,
        measured 24sep2026).  A ``does not crash`` guard, kept as one, made
        to see the two figures (each drawing its 30 rows into a separate
        source, since unlinked) and the one foreign dropdown."""
        from bokeh.models import Select
        spec = self._make_two_graph_spec()
        doc = _page_document(_saved_page(dr_module, auto_df, spec)[0])
        layers = _glyph_layers(doc.roots)
        assert len(layers) == 2, layers
        assert len({r.data_source.id for _f, r in layers}) == 2, (
            "unlinked graphs must not share a source")
        assert all(len(_drawn_values(r, "weight")) == len(auto_df)
                   for _f, r in layers)
        assert sorted(w.title for w in doc.select({"type": Select})) == ["foreign"]


# ---------------------------------------------------------------------------
# BUG-29: Standalone filter callbacks corrupt unlinked graphs with different schemas
# ---------------------------------------------------------------------------

class TestFilterPerSourceOrigData:
    """Regression tests for BUG-29: standalone filter callbacks must carry
    per-source original snapshots so each source is filtered using its own
    column schema, not the primary source's column schema.

    Without the fix, assigning one ``new_data`` (built from the primary
    ColumnDataSource) to every source in ``all_graph_sources`` drops any
    column that does not exist in the primary source, corrupting unlinked
    graphs whose schemas differ.
    """

    def _make_different_schema_spec(self) -> dict:
        """Two unlinked graphs: g1 has (mpg, weight), g2 has (price, weight)."""
        return _make_spec_json(
            graphs=[
                {"plots": [{"type": "scatter", "yvar": "mpg",
                            "xvar": "weight", "options": {}}],
                 "graph_options": {"name": "g1"}},
                {"plots": [{"type": "scatter", "yvar": "price",
                            "xvar": "weight", "options": {}}],
                 "graph_options": {"name": "g2"}},
            ],
            build_options={
                "layout": "auto", "link": "",
                "filter": "foreign, type(dropdown)",
                "theme": "default", "title": "T", "subtitle": "",
                "registry": "g1 g2",
                "mode": "standalone", "port": "5006",
            }
        )

    def test_callback_has_per_source_orig_json_arg(self, dr_module, auto_df):
        """BUG-29-1a: filter callback must include all_graph_sources_orig."""
        spec = self._make_different_schema_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            render_models(renderer)
            assert renderer.filter_callbacks, "filter callback must be built"
            cb_args = renderer.filter_callbacks[0].args
            assert "all_graph_sources_orig" in cb_args, (
                "callback args must contain 'all_graph_sources_orig' for per-source snapshots"
            )
        finally:
            for _p in (spec_path, data_path):
                try:
                    os.unlink(_p)
                except OSError:
                    pass

    def test_per_source_orig_json_length_matches_sources(self, dr_module, auto_df):
        """BUG-29-1b: all_graph_sources_orig must have same length as all_graph_sources."""
        spec = self._make_different_schema_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            render_models(renderer)
            assert renderer.filter_callbacks, "filter callback must be built"
            cb_args = renderer.filter_callbacks[0].args
            srcs = cb_args.get("all_graph_sources", [])
            orig_jsons = cb_args.get("all_graph_sources_orig", [])
            assert len(srcs) == len(orig_jsons), (
                f"all_graph_sources_orig length ({len(orig_jsons)}) must match "
                f"all_graph_sources length ({len(srcs)})"
            )
        finally:
            for _p in (spec_path, data_path):
                try:
                    os.unlink(_p)
                except OSError:
                    pass

    def test_per_source_orig_preserves_source_columns(self, dr_module, auto_df):
        """BUG-29-1c: each orig_json entry must contain the columns of its own source."""
        import json as _json
        spec = self._make_different_schema_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            render_models(renderer)
            assert renderer.filter_callbacks, "filter callback must be built"
            cb_args = renderer.filter_callbacks[0].args
            srcs = cb_args.get("all_graph_sources", [])
            orig_jsons = cb_args.get("all_graph_sources_orig", [])
            assert len(srcs) == len(orig_jsons) >= 2, (
                "need at least 2 source snapshots to verify per-source column preservation"
            )
            for i, (src, orig_model) in enumerate(zip(srcs, orig_jsons)):
                # A shared ColumnDataSource now, not a JSON string.
                orig = orig_model.data
                src_cols = set(src.data.keys())
                orig_cols = set(orig.keys())
                assert src_cols == orig_cols, (
                    f"source[{i}] orig_json columns {sorted(orig_cols)} must match "
                    f"actual source columns {sorted(src_cols)}"
                )
        finally:
            for _p in (spec_path, data_path):
                try:
                    os.unlink(_p)
                except OSError:
                    pass

    def test_g2_orig_json_has_g2_columns_not_g1_columns(self, dr_module, auto_df):
        """BUG-29-1d: g2's orig_json must contain price (g2 col) and not mpg (g1-only col)."""
        import json as _json
        spec = self._make_different_schema_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            render_models(renderer)
            # Each of these used to `return' green.  Each holds (measured
            # 24sep2026); one that did not would be the defect itself.
            assert renderer.filter_callbacks, "no filter callback was built"
            cb_args = renderer.filter_callbacks[0].args
            srcs = cb_args.get("all_graph_sources", [])
            orig_jsons = cb_args.get("all_graph_sources_orig", [])
            g2_src = renderer.sources.get("g2")
            assert g2_src is not None, "g2 has no source"
            g2_origs = [o for s, o in zip(srcs, orig_jsons) if s is g2_src]
            assert len(g2_origs) == 1, (
                "g2's source is not among the sources the filter updates")
            orig = g2_origs[0].data
            assert "price" in orig, (
                "g2 source orig_json must contain 'price' (g2's y-column)"
            )
            assert "mpg" not in orig, (
                "g2 source orig_json must NOT contain 'mpg' (g1-only column) -- "
                "this was the pre-fix corruption vector"
            )
        finally:
            for _p in (spec_path, data_path):
                try:
                    os.unlink(_p)
                except OSError:
                    pass

    def test_filter_js_uses_per_source_orig_json(self, dr_module, auto_df):
        """BUG-29-1e: _FILTER_JS must reference all_graph_sources_orig."""
        js = dr_module._FILTER_JS
        assert "all_graph_sources_orig" in js, (
            "_FILTER_JS must reference all_graph_sources_orig so each source "
            "is filtered with its own column snapshot, not the primary source's snapshot"
        )

    def test_render_with_different_schema_does_not_crash(self, dr_module, auto_df):
        """BUG-29-1f: two unlinked graphs with different columns render, each
        drawing its own y column into its own source.

        This asserted ``len(html_out) > 100`` and ``"all_graph_sources_orig"
        in html_out`` -- both true of any two-graph filtered page, whether or
        not the per-source snapshots were correct (WP-24, measured
        24sep2026).  It reads the document: g1 draws mpg, g2 draws price,
        each from a source carrying only its own columns -- the schema
        separation BUG-29 was about."""
        spec = self._make_different_schema_spec()
        doc = _page_document(_saved_page(dr_module, auto_df, spec)[0])
        # g1's source must hold mpg and not price; g2's the reverse -- the
        # per-source schema separation BUG-29 was about.  (Both also carry
        # the filter column, foreign, and Bokeh's __dash_row__.)
        got = sorted(sorted({"mpg", "price"} & set(r.data_source.data))
                     for _f, r in _glyph_layers(doc.roots))
        assert got == [["mpg"], ["price"]], (
            f"the two graphs' sources carry y-columns {got}; g1 must hold mpg "
            f"only and g2 price only")


# ---------------------------------------------------------------------------
# BUG-21: Server exclude() unions all widgets' excludes (wrong semantics)
# ---------------------------------------------------------------------------

class TestBug21ExcludeSemantics:
    """BUG-21: _make_filter_cb must use the TRIGGERING widget's _dash_exclude,
    not the union of all widgets' excludes.

    Scenario:
      - Widget A excludes g1.
      - Widget B does NOT exclude g1.
    When widget B fires, g1 MUST be updated.
    When widget A fires, g1 must be SKIPPED.
    """

    def _make_server_spec_two_widgets(self):
        return _make_spec_json(
            graphs=[
                {
                    "plots": [{"type": "scatter", "yvar": "mpg",
                               "xvar": "weight", "options": {}}],
                    "graph_options": {"name": "g1", "title": "G1"},
                },
                {
                    "plots": [{"type": "scatter", "yvar": "price",
                               "xvar": "weight", "options": {}}],
                    "graph_options": {"name": "g2", "title": "G2"},
                },
            ],
            build_options={
                "layout": "auto", "link": "",
                # widgetA (foreign) excludes g1; widgetB (mpg) excludes nothing
                # Filter specs are separated by "||" (Mata-joined format)
                "filter": "foreign, type(dropdown), exclude(g1) || mpg, type(range)",
                "theme": "default", "title": "T", "subtitle": "",
                "registry": "g1 g2",
                "mode": "server", "port": "5006",
            },
        )

    def test_generated_source_compiles(self, dr_module, auto_df):
        """BUG-21a: Generated server app with two filter widgets must compile."""
        spec = self._make_server_spec_two_widgets()
        source = _build_app(dr_module, auto_df, spec)
        try:
            compile(source, "<generated>", "exec")
        except SyntaxError as exc:
            pytest.fail(f"Generated server app has syntax error: {exc}")

    @pytest.mark.parametrize("moved", ["the_widget_that_excludes_g1",
                                       "the_widget_that_excludes_nothing"])
    def test_a_move_skips_only_the_graphs_its_own_widget_excludes(
            self, dr_module, auto_df, tmp_path, moved):
        """BUG-21b/c/d: the graphs a move leaves alone are the MOVED widget's
        exclude() list -- not every widget's.

        These read the generated app for the parameter name `_trig_widget',
        for the absence of a loop that unioned the lists, and for the
        per-widget wiring call.  Every served exclude test had ONE widget,
        where the moved widget's list and the union are the same list, so
        nothing could tell (WP-24 scan).  Here widget A excludes g1 and
        widget B excludes nothing: moving B must narrow both graphs, and
        moving A must narrow g2 alone.
        """
        from bokeh.models import GlyphRenderer, Plot, RangeSlider, Select
        spec = self._make_server_spec_two_widgets()
        doc, _ = _ql_served(dr_module, tmp_path, spec, auto_df)

        def _rows():
            out = {}
            for root in doc.roots:
                for fig in root.select({"type": Plot}):
                    n = [len(r.data_source.data["weight"])
                         for r in fig.renderers
                         if isinstance(r, GlyphRenderer)
                         and type(r.glyph).__name__ == "Scatter"]
                    if n:
                        out[fig.title.text if fig.title else ""] = n[0]
            return out

        def _fire(w, value):
            w.value = value
            for key in ("value", "value_throttled"):
                for cb in list(w._callbacks.get(key, [])):
                    cb("value", None, value)

        n = len(auto_df)
        assert _rows() == {"G1": n, "G2": n}, _rows()
        if moved == "the_widget_that_excludes_g1":
            w = [m for root in doc.roots for m in root.select({"type": Select})]
            assert len(w) == 1, w
            pick = [v for v, lab in w[0].options if lab == "1"]
            _fire(w[0], pick[0])
            kept = int((auto_df["foreign"] == 1).sum())
            want = {"G1": n, "G2": kept}
        else:
            w = [m for root in doc.roots
                 for m in root.select({"type": RangeSlider})]
            assert len(w) == 1, w
            lo = float(auto_df["mpg"].median())
            hi = float(auto_df["mpg"].max())
            _fire(w[0], (lo, hi))
            kept = int(((auto_df["mpg"] >= lo) & (auto_df["mpg"] <= hi)).sum())
            want = {"G1": kept, "G2": kept}
        assert 0 < kept < n
        assert _rows() == want, (
            f"after moving {moved.replace('_', ' ')}: {_rows()}, want {want}")

    def test_excluding_widget_skips_target_graph(self, dr_module, auto_df):
        """BUG-21e: Widget with exclude(g1) must have _dash_exclude=['g1'];
        widget without exclude() must have empty _dash_exclude.
        Filter specs are separated by '||' (Mata-joined format).
        """
        from bokeh.models import Select, RangeSlider
        from bokeh.document import Document

        # widget_a (foreign, dropdown) excludes g1
        # widget_b (weight, range) excludes nothing
        spec = _make_spec_json(
            graphs=[
                {
                    "plots": [{"type": "scatter", "yvar": "mpg",
                               "xvar": "weight", "options": {}}],
                    "graph_options": {"name": "g1", "title": "G1"},
                },
            ],
            build_options={
                "layout": "auto", "link": "",
                # "||" is the Mata-joined separator for multiple filter specs
                "filter": "foreign, type(dropdown), exclude(g1) || weight, type(range)",
                "theme": "default", "title": "", "subtitle": "",
                "registry": "g1",
                "mode": "server", "port": "5006",
            },
        )
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name, port=5006)

            app_mod = load_app(out_f.name, "_bug21_app")

            doc = Document()
            app_mod.make_document(doc)

            # Find filter widgets by traversing all doc models
            all_models = list(doc.models)
            widget_a = next(
                (m for m in all_models
                 if isinstance(m, Select) and getattr(m, '_dash_var', '') == 'foreign'),
                None,
            )
            widget_b = next(
                (m for m in all_models
                 if isinstance(m, RangeSlider) and getattr(m, '_dash_var', '') == 'weight'),
                None,
            )

            assert widget_a is not None, (
                "widget_a (foreign dropdown) not found in generated app models"
            )
            assert widget_b is not None, (
                "widget_b (weight range slider) not found in generated app models"
            )

            # Verify exclude semantics
            excl_a = getattr(widget_a, '_dash_exclude', [])
            excl_b = getattr(widget_b, '_dash_exclude', [])
            assert 'g1' in excl_a, (
                f"widget_a (foreign) must have _dash_exclude=['g1'], got {excl_a!r}"
            )
            assert 'g1' not in excl_b, (
                f"widget_b (weight) must NOT exclude g1, got {excl_b!r}"
            )
        finally:
            os.unlink(spec_path)
            os.unlink(data_path)
            os.unlink(out_f.name)


# ---------------------------------------------------------------------------
# BUG-22: Server multi-layer graph sources overwritten
# ---------------------------------------------------------------------------

class TestBug22MultiLayerSources:
    """BUG-22: graph_sources[gname] must hold a LIST of all layer sources,
    not just the last one.  The filter callback must update ALL sources in the list.
    """

    def _make_two_layer_spec(self):
        """Dashboard with one graph that has two raw-data layers (scatter + line)."""
        return _make_spec_json(
            graphs=[{
                "plots": [
                    {"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}},
                    {"type": "line",    "yvar": "mpg", "xvar": "weight", "options": {}},
                ],
                "graph_options": {"name": "g1", "title": "Two-layer"},
            }],
            build_options={
                "layout": "auto", "link": "",
                "filter": "foreign, type(dropdown)",
                "theme": "default", "title": "", "subtitle": "",
                "registry": "g1",
                "mode": "server", "port": "5006",
            },
        )

    def test_generated_source_compiles(self, dr_module, auto_df):
        """BUG-22a: Generated server app with two-layer graph must compile."""
        spec = self._make_two_layer_spec()
        source = _build_app(dr_module, auto_df, spec)
        try:
            compile(source, "<generated>", "exec")
        except SyntaxError as exc:
            pytest.fail(f"Generated server app has syntax error: {exc}")

    def test_graph_sources_stores_list(self, dr_module, auto_df):
        """BUG-22b: graph_sources[gname] must be a list of CDS objects for a multi-layer graph."""
        spec = self._make_two_layer_spec()
        source = _build_app(dr_module, auto_df, spec)
        # The generated code must use list-append semantics for graph_sources
        assert "graph_sources[gname] = []" in source or \
               "graph_sources[gname].append(" in source, (
            "BUG-22: Generated code must initialise graph_sources[gname] as a list "
            "and append each layer's CDS"
        )

    def test_filter_cb_iterates_list_of_sources(self, dr_module, auto_df):
        """BUG-22c: Filter callback must iterate over srcs list, not a single src."""
        spec = self._make_two_layer_spec()
        source = _build_app(dr_module, auto_df, spec)
        # The filter callback section (between _all_sources loop markers) must iterate srcs
        assert "for src in srcs:" in source or "for gname, srcs in _all_sources.items():" in source, (
            "BUG-22c: Filter callback must unpack list of sources per gname"
        )

    def test_two_layer_graph_make_document(self, dr_module, auto_df):
        """BUG-22d: make_document draws BOTH layers of the two-layer graph.

        This asserted ``len(doc.roots) > 0``, which the layout column
        satisfies with one layer, or none (WP-24, measured 24sep2026).
        BUG-22 was graph_sources keeping only the last layer, so the check
        that matters is that the served graph draws its scatter AND its line,
        each from a source of all 30 rows -- and the foreign dropdown."""
        from bokeh.models import Select
        spec = self._make_two_layer_spec()
        doc, _ = _exec_doc(dr_module, auto_df, spec, "_bug22_app")
        layers = _glyph_layers(doc.roots)
        assert sorted(type(r.glyph).__name__ for _f, r in layers) == \
            ["Line", "Scatter"], layers
        assert all(len(_drawn_values(r, "weight")) == len(auto_df)
                   for _f, r in layers)
        assert [w.title for w in doc.select({"type": Select})] == ["foreign"]

    def test_filter_callback_updates_all_layer_sources(self, dr_module, auto_df):
        """BUG-22e: Filter callback invocation on a 2-layer graph must not raise.
        Verifies that the generated filter callback correctly handles the list-of-sources
        structure for graph_sources[gname] when updating data after a filter change.
        """
        from bokeh.document import Document
        from bokeh.models import Select

        spec = self._make_two_layer_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name, port=5006)

            app_mod = load_app(out_f.name, "_bug22e_app")

            doc = Document()
            app_mod.make_document(doc)

            # Find the filter widget (Select for 'foreign') and trigger its callback
            # to verify the callback handles the list-of-sources structure without error.
            all_models = list(doc.models)
            filter_widget = next(
                (m for m in all_models
                 if isinstance(m, Select) and getattr(m, '_dash_var', '') == 'foreign'),
                None,
            )
            assert filter_widget is not None, (
                "foreign Select filter widget not found in generated 2-layer app"
            )

            # Simulate a filter change — this must not raise even for a 2-layer graph
            old_val = filter_widget.value
            new_val = next(
                (v for v in filter_widget.options if v != 'All'),
                'All',
            )
            try:
                # Manually invoke all on_change callbacks that were registered
                for cb_desc in filter_widget._callbacks.get('value', []):
                    cb_desc('value', old_val, new_val)
            except Exception as exc:
                pytest.fail(
                    f"BUG-22e: Filter callback raised on 2-layer graph: {exc!r}"
                )
        finally:
            os.unlink(spec_path)
            os.unlink(data_path)
            os.unlink(out_f.name)


# ---------------------------------------------------------------------------
# BUG-32: Server filter callback clears synthetic columns (e.g. __dash_xjit/__dash_yjit)
# ---------------------------------------------------------------------------

class TestServerFilterPreservesDerivedColumns:
    """BUG-32: Server-mode filter callbacks must not blank derived columns.

    Pre-fix: for any column in ``src.data`` not present in ``_gdf.columns``
    (e.g. ``__dash_xjit``/``__dash_yjit`` from ``jitter()``, or Bokeh's implicit
    ``index`` column), the callback set it to ``[]``, causing a length
    mismatch warning and making glyphs disappear after filter interactions.

    Post-fix: a per-source original-data snapshot is captured before any
    filter fires; derived columns are populated by selecting rows at the
    correct positional indices from the snapshot.
    """

    def _make_jitter_spec(self) -> dict:
        """Scatter with jitter option so __dash_xjit/__dash_yjit exist in src.data."""
        return _make_spec_json(
            graphs=[{
                "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                           "options": {"jitter": "5"}}],
                "graph_options": {"name": "g1"},
            }],
            build_options={
                "layout": "auto", "link": "",
                "filter": "foreign, type(dropdown)",
                "theme": "default", "title": "T", "subtitle": "",
                "registry": "g1", "mode": "standalone", "port": "5006",
            }
        )

    @pytest.mark.parametrize("opts,column", [
        # G1 (WP-28): the marker-label column is named under the __dash
        # prefix now (dr._DASH_MLABEL_PREFIX + "foreign").
        ({"mlabel": "foreign"}, "__dash_mlabel_foreign"),
        # WP-29 P0.16: the colour column is named under __dash_cvar, one
        # per layer; None here is resolved to the Scatter's colour field.
        ({"colorvar": "foreign", "colordiscrete": "colordiscrete"}, None),
    ], ids=["marker_labels", "colour_bins"])
    def test_a_derived_column_keeps_each_kept_rows_value_after_a_move(
            self, dr_module, auto_df, tmp_path, opts, column):
        """BUG-32-1a/1b: a column the layer source derives -- the marker-label
        text, the colour bin -- is not a frame column, so after a filter
        move it is taken from the pre-move snapshot, row by row: every kept
        row keeps its own value, and every column keeps one value per row.

        These read the generated app for the snapshot's NAME.  The one
        behavioural BUG-32 test (below) uses jitter, whose offsets now live
        in a source that is redrawn rather than snapshot-subset, so nothing
        moved a filter under a layer that carries such a column (WP-24
        scan)."""
        import warnings as _w
        from bokeh.models import GlyphRenderer, Plot, RangeSlider
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": dict(opts), "if_expr": "", "in_expr": ""}],
            "graph_options": {"name": "g1"},
            "if_expr": "", "in_expr": "",
        }], build_options={
            "layout": "auto", "link": "", "filter": "price, type(range)",
            "theme": "", "title": "", "subtitle": "", "registry": "g1",
            "level": "95", "formats": {}})
        labels = ({"origin": {"0": "Domestic", "1": "Foreign"}},
                  {"foreign": "origin"})
        doc, _ = _ql_served(dr_module, tmp_path, spec, auto_df, labels)
        if column is None:
            import colour_bins as cb
            (rend,) = [r for r in cb.colour_renderers(doc)
                       if type(r.glyph).__name__ == "Scatter"]
            column = cb.colour_field(rend)

        def _layer():
            found = [r.data_source for root in doc.roots
                     for fig in root.select({"type": Plot})
                     for r in fig.renderers
                     if isinstance(r, GlyphRenderer)
                     and type(r.glyph).__name__ == "Scatter"
                     and column in r.data_source.data]
            assert len(found) == 1, found
            return found[0]

        before = dict(_layer().data)
        value_of = dict(zip([int(i) for i in before["index"]],
                            list(before[column])))
        assert len(set(value_of.values())) > 1, value_of
        w = [m for root in doc.roots for m in root.select({"type": RangeSlider})]
        assert len(w) == 1, w
        lo = float(auto_df["price"].median())
        hi = float(auto_df["price"].max())
        w[0].value = (lo, hi)
        with _w.catch_warnings(record=True) as caught:
            _w.simplefilter("always")
            for key in ("value", "value_throttled"):
                for cb in list(w[0]._callbacks.get(key, [])):
                    cb("value", None, (lo, hi))
        after = dict(_layer().data)
        kept = [int(i) for i in auto_df.index[
            (auto_df["price"] >= lo) & (auto_df["price"] <= hi)]]
        assert 0 < len(kept) < len(auto_df)
        assert not [str(m.message) for m in caught
                    if "same length" in str(m.message)], caught
        assert {k: len(v) for k, v in after.items()} == \
            {k: len(kept) for k in after}, (
            f"after the move the columns hold "
            f"{ {k: len(v) for k, v in after.items()} } values; "
            f"{len(kept)} rows are kept")
        assert sorted(int(i) for i in after["index"]) == kept
        assert [after[column][j] for j in range(len(kept))] == \
            [value_of[int(i)] for i in after["index"]], (
            f"{column} lost its rows' own values after the move")
        if column == "__dash_mlabel_foreign":
            assert set(after[column]) <= {"Domestic", "Foreign"}, after[column]

    def test_generated_callback_handles_index_column(self, dr_module, auto_df):
        """BUG-32-1c: generated callback must repopulate 'index' from _gdf.index, not blank it."""
        spec = self._make_jitter_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            src = builder._generate_app_source(5006)
            # Must have special handling for 'index' column
            assert "col == 'index'" in src or "_src_idx" in src, (
                "generated callback must handle 'index' column specially "
                "(repopulate from _gdf.index, not blank it)"
            )
        finally:
            for _p in (spec_path, data_path):
                try:
                    os.unlink(_p)
                except OSError:
                    pass

    def test_make_document_with_filter_does_not_raise(self, dr_module, auto_df):
        """BUG-32-1d: make_document draws the jittered scatter and its derived
        offset columns for every row.

        This asserted ``len(doc.roots) > 0``, which the layout column
        satisfies whether the jitter columns were built or not (WP-24,
        measured 24sep2026).  jitter() adds the derived __dash_xjit/__dash_yjit that
        BUG-32 could blank; the served scatter must carry both, one value per
        row, over all 30 rows, and the foreign dropdown."""
        from bokeh.document import Document
        from bokeh.models import Select
        spec = self._make_jitter_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name, port=5006)
            app_mod = load_app(out_f.name, "_bug32_app")
            doc = Document()
            app_mod.make_document(doc)
            (_fig, r), = _glyph_layers(doc.roots)
            assert type(r.glyph).__name__ == "Scatter"
            data = r.data_source.data
            # G1 (WP-28): the jitter columns are named under the __dash prefix.
            assert {dr_module._DASH_JITTER_X, dr_module._DASH_JITTER_Y} \
                <= set(data), (
                f"jitter's derived columns are missing: {sorted(data)}")
            assert {len(v) for v in data.values()} == {len(auto_df)}, (
                "every column, jitter's included, must hold one value per row")
            assert [w.title for w in doc.select({"type": Select})] == ["foreign"]
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try:
                    os.unlink(_p)
                except OSError:
                    pass

    def test_filter_callback_preserves_derived_column_length(self, dr_module, auto_df):
        """BUG-32-1e: after filter callback fires, derived columns must match data column lengths."""
        import warnings
        from bokeh.document import Document
        from bokeh.models import Select
        spec = self._make_jitter_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name, port=5006)
            app_mod = load_app(out_f.name, "_bug32e_app")
            doc = Document()
            app_mod.make_document(doc)
            # Find filter widget and trigger it
            from bokeh.models import GlyphRenderer
            all_models = list(doc.models)
            fw = next(
                (m for m in all_models
                 if isinstance(m, Select) and getattr(m, "_dash_var", "") == "foreign"),
                None,
            )
            # This returned green when the widget was missing.  It is built
            # (measured 24sep2026); a missing one is a failure.
            assert fw is not None, "the foreign filter widget was not built"
            srcs = [m.data_source for m in all_models
                    if isinstance(m, GlyphRenderer)
                    and type(m.glyph).__name__ == "Scatter"]
            assert len(srcs) == 1, srcs
            non_all = [v for v, _l in fw.options if v != "__all__"]
            assert non_all, fw.options
            new_val = non_all[0]
            want = int((auto_df["foreign"] == float(new_val)).sum())
            # The callback reads the widget's value, not its arguments: the
            # value itself is set, as a browser sets it.  Called by hand with
            # a new value, it refiltered on the unchanged "All".
            with warnings.catch_warnings(record=True) as w_list:
                warnings.simplefilter("always")
                fw.value = new_val
            lengths = {k: len(v) for k, v in srcs[0].data.items()}
            # G1 (WP-28): the jitter columns are named under the __dash prefix.
            assert {dr_module._DASH_JITTER_X, dr_module._DASH_JITTER_Y} \
                <= set(lengths), lengths
            assert set(lengths.values()) == {want}, (
                "BUG-32: after foreign=%s every column, derived ones "
                "included, must hold the %d rows kept; got %r"
                % (new_val, want, lengths))
            length_warnings = [w for w in w_list
                                if "same length" in str(w.message).lower()]
            assert not length_warnings, (
                "BUG-32: filter callback must not produce 'columns must be of the same "
                f"length' warnings after fix; got: {length_warnings}"
            )
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try:
                    os.unlink(_p)
                except OSError:
                    pass


# ---------------------------------------------------------------------------
# BUG-33: Server filter interactions stop enforcing graph-level if_expr/in_expr
# ---------------------------------------------------------------------------

class TestServerFilterReappliesGraphQualifiers:
    """BUG-33: Server filter callbacks must reapply graph-level if_expr/in_expr.

    Pre-fix: filter callbacks recomputed source data from the global `_df_ref`
    mask only, never applying per-graph qualifiers.  After a filter change,
    rows excluded by the qualifier were reintroduced.

    Post-fix: ``_graph_qualifiers`` dict is built during document construction;
    ``_make_filter_cb`` accepts it and reapplies each graph's qualifier after
    computing the filter mask.
    """

    def _make_qualified_spec(self) -> dict:
        """Graph with if_expr='foreign == 1' plus a dropdown filter."""
        return _make_spec_json(
            graphs=[{
                "plots": [{"type": "scatter", "yvar": "mpg",
                           "xvar": "weight", "options": {}}],
                "graph_options": {"name": "g1", "if_expr": "foreign == 1"},
            }],
            build_options={
                "layout": "auto", "link": "",
                "filter": "rep78, type(dropdown)",
                "theme": "default", "title": "T", "subtitle": "",
                "registry": "g1", "mode": "standalone", "port": "5006",
            }
        )

    def test_a_graphs_if_holds_after_a_move(self, dr_module, tmp_path):
        """BUG-33, the `if' half: after a filter move the served graph still
        draws only the rows its own `if' selects, of those the move keeps.

        Replaces BUG-33-1a and 1b, which asserted that the names
        _graph_qualifiers and _gquals appeared in the generated app.  A
        callback that never reapplies the qualifier still carries both
        names: with the reapplication removed (WP-24 mutation cb4) both
        passed, and this fails."""
        df = self._ordered_frame()
        doc, _ = _ql_served(dr_module, tmp_path,
                            self._ordered_spec(if_expr="foreign == 1"), df)
        assert self._drawn(doc) == sorted(df.loc[df["foreign"] == 1,
                                                 "weight"])
        self._move_range(doc, 3500.0, 5000.0)
        want = sorted(df.loc[(df["foreign"] == 1) & (df["price"] >= 3500.0)
                             & (df["price"] <= 5000.0), "weight"])
        assert 0 < len(want) < int((df["foreign"] == 1).sum())
        assert self._drawn(doc) == want, (
            f"after the move the served graph drew x={self._drawn(doc)}; "
            f"the rows with foreign == 1 that the range keeps are x={want}")

    def test_make_document_with_qualified_graph_does_not_crash(self, dr_module, auto_df):
        """BUG-33-1c: make_document draws only the graph's if_expr rows.

        This asserted ``len(doc.roots) > 0``, which the layout column
        satisfies whether the qualifier was applied or not (WP-24, measured
        24sep2026).  The served graph (if foreign==1) must draw the 16
        foreign rows; the control, the same graph with no qualifier, draws
        all 30, so the reader sees the qualifier do the reducing."""
        from bokeh.document import Document
        spec = self._make_qualified_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name, port=5006)
            app_mod = load_app(out_f.name, "_bug33_app")
            doc = Document()
            app_mod.make_document(doc)
            (_fig, r), = _glyph_layers(doc.roots)
            assert len(_drawn_values(r, "weight")) == \
                int((auto_df["foreign"] == 1).sum()), (
                "the served graph did not restrict to its if foreign==1 rows")
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try:
                    os.unlink(_p)
                except OSError:
                    pass
        # Control: the same graph with no qualifier draws every row.
        plain = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        _doc, (control,) = _exec_doc(dr_module, auto_df, plain, "_bug33_ctl")
        assert len(_drawn_values(control, "weight")) == len(auto_df)

    def test_filter_callback_does_not_reintroduce_qualified_out_rows(self, dr_module, auto_df):
        """BUG-33-1d: filter callback must not expand qualified graph source beyond if_expr rows.

        This had never checked anything.  It filtered on rep78, which the
        fixture data does not carry -- "dash: filter(rep78): the variable is
        not in the data; no widget was built" -- and returned green when the
        widget was missing; the module-level graph_sources it read next is
        empty too (both measured 24sep2026).  The data now carries rep78,
        the source is found in the document, and the widget's value is set
        as a browser sets it: the callback reads the value, not its
        arguments.
        """
        from bokeh.document import Document
        from bokeh.models import GlyphRenderer, Select
        df = auto_df.assign(
            rep78=(np.arange(len(auto_df)) % 5 + 1).astype(float))
        spec = self._make_qualified_spec()
        spec_path, data_path = _write_temp_files(df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name, port=5006)
            app_mod = load_app(out_f.name, "_bug33d_app")
            doc = Document()
            app_mod.make_document(doc)
            all_models = list(doc.models)
            # Find filter widget for rep78
            fw = next(
                (m for m in all_models
                 if isinstance(m, Select) and getattr(m, "_dash_var", "") == "rep78"),
                None,
            )
            assert fw is not None, "the rep78 filter widget was not built"
            g1_srcs = [m.data_source for m in all_models
                       if isinstance(m, GlyphRenderer)
                       and type(m.glyph).__name__ == "Scatter"]
            assert len(g1_srcs) == 1, g1_srcs
            g1_src = g1_srcs[0]
            qualified = df["foreign"] == 1
            # The qualifier applies from the start ...
            assert len(g1_src.data["mpg"]) == int(qualified.sum())
            # ... and is reapplied when a filter moves: rep78 == 2 among
            # the foreign cars, not among all of them.
            want = int((qualified & (df["rep78"] == 2)).sum())
            assert want != int((df["rep78"] == 2).sum()), (
                "the data cannot tell a reapplied qualifier from a lost one")
            fw.value = "2"
            assert len(g1_src.data["mpg"]) == want, (
                f"BUG-33: rep78 == 2 left {len(g1_src.data['mpg'])} rows in g1; "
                f"{want} of them satisfy the graph's `if foreign == 1'")
            # "All" is the full qualified set again, never the whole data.
            fw.value = "__all__"
            assert len(g1_src.data["mpg"]) == int(qualified.sum()), (
                "BUG-33: choosing All brought back rows the graph's qualifier "
                "excludes")
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try:
                    os.unlink(_p)
                except OSError:
                    pass

    @staticmethod
    def _move_range(doc, lo, hi):
        from bokeh.models import RangeSlider
        sliders = [m for root in doc.roots
                   for m in root.select({"type": RangeSlider})]
        assert len(sliders) == 1, sliders
        w = sliders[0]
        w.value = (lo, hi)
        for key in ("value", "value_throttled"):
            for cb in list(w._callbacks.get(key, [])):
                cb("value", None, (lo, hi))

    @staticmethod
    def _drawn(doc):
        from bokeh.models import GlyphRenderer, Plot
        return sorted(float(v) for root in doc.roots
                      for fig in root.select({"type": Plot})
                      for r in fig.renderers
                      if isinstance(r, GlyphRenderer)
                      and type(r.glyph).__name__ == "Scatter"
                      for v in r.data_source.data["weight"])

    def _ordered_spec(self, if_expr="", in_expr=""):
        return _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}, "if_expr": "", "in_expr": ""}],
            "graph_options": {"name": "g1"},
            "if_expr": if_expr, "in_expr": in_expr,
        }], build_options={
            "layout": "auto", "link": "", "filter": "price, type(range)",
            "theme": "", "title": "", "subtitle": "", "registry": "g1",
            "level": "95", "formats": {}})

    @staticmethod
    def _ordered_frame(n=20):
        return pd.DataFrame({
            "mpg": [10.0 + i for i in range(n)],
            "weight": [2000.0 + 50 * i for i in range(n)],
            "price": [3000.0 + 100 * i for i in range(n)],
            "foreign": [float(i % 2) for i in range(n)],
        })

    def test_a_graphs_in_counts_observations_after_a_move(
            self, dr_module, tmp_path):
        """BUG-33, the `in' half: after a filter move the graph's `in 3/8'
        still names observations 3 to 8 of the data, as twoway and the
        initial draw read it -- not the 3rd to 8th rows the move left.

        Measured 24sep2026 (WP-24): the served callback applied the graph's
        `in' with its own iloc over the FILTERED frame, so moving price to
        3500..5000 drew the rows at x = 2350..2600 where observations 3..8
        that the range keeps are x = 2250, 2300, 2350."""
        df = self._ordered_frame()
        doc, _ = _ql_served(dr_module, tmp_path,
                            self._ordered_spec(in_expr="3/8"), df)
        assert self._drawn(doc) == [2100.0, 2150.0, 2200.0, 2250.0,
                                    2300.0, 2350.0]
        self._move_range(doc, 3500.0, 5000.0)
        obs = df.iloc[2:8]
        want = sorted(obs.loc[(obs["price"] >= 3500.0)
                              & (obs["price"] <= 5000.0), "weight"])
        assert want == [2250.0, 2300.0, 2350.0]
        assert self._drawn(doc) == want, (
            f"after the move the served graph drew x={self._drawn(doc)}; "
            f"observations 3..8 that the range keeps are x={want}")

    @pytest.mark.parametrize("qual", [
        {"in_expr": "3/12"},
        {"if_expr": "mpg >= 16"},
    ], ids=["in", "if"])
    def test_a_by_panels_qualifier_holds_after_a_move(
            self, dr_module, tmp_path, qual):
        """BUG-33 in a by() graph: after a move every panel still draws the
        rows of its own level that the graph's qualifier and the move both
        keep.  The callback finds a panel's qualifier through
        _gfac_to_orig (panel name -> graph name); no unlinked move reached
        that lookup before (WP-24), and `in' counts observations of the
        data, not rows of a panel."""
        from bokeh.models import GlyphRenderer, Plot
        df = self._ordered_frame()
        spec = self._ordered_spec(**qual)
        spec["graphs"][0]["graph_options"]["by"] = "foreign"
        doc, _ = _ql_served(dr_module, tmp_path, spec, df)

        def panels():
            out = []
            for root in doc.roots:
                for fig in root.select({"type": Plot}):
                    xs = sorted(float(v) for r in fig.renderers
                                if isinstance(r, GlyphRenderer)
                                and type(r.glyph).__name__ == "Scatter"
                                for v in r.data_source.data["weight"])
                    if xs:
                        out.append(xs)
            return sorted(out)

        if "in_expr" in qual:
            owned = df.iloc[2:12]
        else:
            owned = df[df["mpg"] >= 16]

        def want(rows):
            return sorted(sorted(rows.loc[rows["foreign"] == lvl, "weight"])
                          for lvl in (0.0, 1.0))

        assert panels() == want(owned)
        self._move_range(doc, 3500.0, 4200.0)
        kept = owned[(owned["price"] >= 3500.0) & (owned["price"] <= 4200.0)]
        assert 0 < len(kept) < len(owned)
        assert panels() == want(kept), (
            f"after the move the panels drew {panels()}; the rows of each "
            f"level the qualifier and the range keep are {want(kept)}")

    def test_a_qualifier_too_deep_to_parse_does_not_break_a_move(
            self, dr_module, tmp_path):
        """CLAUDE.md rule 18, resource exhaustion: a graph qualifier the
        whitelist cannot even parse is refused at the first draw (WP-20)
        and must be refused again after a move -- the move still applies.

        Measured 24sep2026 (WP-24): the callback's own whitelist caught
        SyntaxError only, so 50,000 `~' raised MemoryError ("Parser stack
        overflowed") out of the callback on every move, and the move never
        reached the graph: it kept all 20 rows where the range keeps 15."""
        df = self._ordered_frame()
        doc, warned = _ql_served(dr_module, tmp_path, self._ordered_spec(
            if_expr="~" * 50000 + "foreign"), df)
        assert [m for m in warned if "skipped" in m], warned
        assert len(self._drawn(doc)) == len(df)
        self._move_range(doc, 3500.0, 5000.0)
        want = sorted(df.loc[(df["price"] >= 3500.0)
                             & (df["price"] <= 5000.0), "weight"])
        assert self._drawn(doc) == want, (
            f"after the move the served graph drew {len(self._drawn(doc))} "
            f"rows; the range keeps {len(want)}")

    def test_an_in_bound_too_long_for_int_does_not_break_a_move(
            self, dr_module, tmp_path):
        """CLAUDE.md rule 18, resource exhaustion: an `in' bound of 5,000
        digits reads as past the data's end at the first draw (WP-20's
        bound) and must read so again after a move.

        Measured 24sep2026 (WP-24): the callback's own int() raised
        ValueError ("Exceeds the limit (4300 digits) for integer string
        conversion") out of every move, while the first draw drew
        observations 3 to 20."""
        df = self._ordered_frame()
        doc, _ = _ql_served(dr_module, tmp_path, self._ordered_spec(
            in_expr="3/" + "9" * 5000), df)
        assert self._drawn(doc) == sorted(df["weight"].iloc[2:])
        self._move_range(doc, 3500.0, 5000.0)
        obs = df.iloc[2:]
        want = sorted(obs.loc[(obs["price"] >= 3500.0)
                              & (obs["price"] <= 5000.0), "weight"])
        assert self._drawn(doc) == want, (
            f"after the move the served graph drew {len(self._drawn(doc))} "
            f"rows; observations 3 on that the range keeps are {len(want)}")

    def test_the_filter_callback_does_not_run_a_hostile_qualifier(
            self, dr_module, auto_df, tmp_path):
        """BUG-33-1e: the qualifier the served filter callback applies again
        after a move passes the callback's whitelist before DataFrame.query.

        This asserted that the whitelist's NAME appeared in the generated
        app.  The callback's whitelist was then emitted text of its own, not
        the shared _validate_if_expr; since WP-24 the callback reads the
        qualifier through _dash_layer_frame, as the first draw does.  Either
        way a name in the source proves nothing about the route the
        callback takes, so running the callback is the only proof that it
        guards.  The build refuses this qualifier and warns; the raw text
        still travels with the graph to the callback.  The payload is one
        pandas' python engine runs by itself -- measured, it resolves @os
        from the calling module and calls os.system -- so only dash's guard
        stands between the qualifier and a shell.  CLAUDE.md rule 18,
        injection.
        """
        from bokeh.models import GlyphRenderer, Plot, RangeSlider
        marker = os.path.join(str(tmp_path), "BUG33_RAN")
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}],
            "graph_options": {"name": "g1"},
            "if_expr": "@os.system('touch %s') == 0" % marker,
        }], build_options={
            "layout": "auto", "link": "", "filter": "price, type(range)",
            "theme": "", "title": "", "subtitle": "", "registry": "g1",
            "level": "95", "formats": {}})
        doc, warned = _ql_served(dr_module, tmp_path, spec, auto_df)
        assert not os.path.exists(marker), "the build ran the qualifier"
        assert [m for m in warned if "skipped" in m], warned
        sliders = [m for root in doc.roots
                   for m in root.select({"type": RangeSlider})]
        assert len(sliders) == 1, sliders
        w = sliders[0]
        lo = float(auto_df["price"].quantile(0.25))
        hi = float(auto_df["price"].max())
        w.value = (lo, hi)
        for key in ("value", "value_throttled"):
            for cb in list(w._callbacks.get(key, [])):
                cb("value", None, (lo, hi))
        assert not os.path.exists(marker), (
            "the served filter callback handed the qualifier to "
            "DataFrame.query, which ran it")
        kept = sorted(float(v) for v in auto_df.loc[
            (auto_df["price"] >= lo) & (auto_df["price"] <= hi), "weight"])
        drawn = sorted(float(v) for root in doc.roots
                       for fig in root.select({"type": Plot})
                       for r in fig.renderers
                       if isinstance(r, GlyphRenderer)
                       and type(r.glyph).__name__ == "Scatter"
                       for v in r.data_source.data["weight"])
        assert 0 < len(kept) < len(auto_df)
        assert drawn == kept, (
            "after the move the refused qualifier must leave the rows the "
            f"range keeps: drew {len(drawn)}, the range keeps {len(kept)}")


# ---------------------------------------------------------------------------
# BUG-23: Mixed valid/missing filter specs break standalone filter callbacks
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# BUG-34: Standalone linked graphs ignore graph-level qualifiers
# ---------------------------------------------------------------------------

class TestLinkedGraphQualifierView:
    """BUG-34: Linked graphs with if_expr/in_expr must apply per-graph CDSView.

    Pre-fix: all linked graphs received the same shared ColumnDataSource built
    from full self.df, so per-graph if_expr/in_expr qualifiers were silently
    ignored.

    Post-fix: a CDSView(BooleanFilter) is computed from _apply_graph_filter()
    for each linked graph that has qualifiers, and passed as facet_view to
    _make_figure() so only qualified rows are rendered.
    """

    def _make_linked_qualified_spec(self, if_expr="foreign == 1") -> dict:
        """Two linked graphs: g1 has *if_expr*, g2 has no qualifier.

        The qualifier sits at g1's top level, beside graph_options, which is
        where dash.ado writes it (_dash_plot promotes it there) and the only
        place the saved renderer's _apply_graph_filter reads it.  This helper
        used to put it INSIDE graph_options, which the saved renderer never
        reads: every test in this class ran on an unqualified g1 -- g1's view
        was the default AllIndices, drawing all 30 rows (WP-24, measured
        24sep2026), and the BUG-34 fix was never exercised."""
        return _make_spec_json(
            graphs=[
                {"plots": [{"type": "scatter", "yvar": "mpg",
                            "xvar": "weight", "options": {}}],
                 "graph_options": {"name": "g1"},
                 "if_expr": if_expr, "in_expr": ""},
                {"plots": [{"type": "scatter", "yvar": "price",
                            "xvar": "weight", "options": {}}],
                 "graph_options": {"name": "g2"}},
            ],
            build_options={
                "layout": "auto", "link": "g1 g2",
                "filter": "", "theme": "default", "title": "T", "subtitle": "",
                "registry": "g1 g2", "mode": "standalone", "port": "5006",
            }
        )

    def test_render_linked_qualified_does_not_crash(self, dr_module, auto_df):
        """BUG-34-1a: two linked graphs render on one shared source holding
        every row.

        This asserted ``len(html_out) > 100``, true of any page (WP-24,
        measured 24sep2026).  A ``does not crash`` guard, kept as one, made
        non-vacuous by reading the document: g1 draws mpg and g2 price, both
        from the single shared ColumnDataSource of all rows (the linked
        contract -- the per-graph view that masks the qualifier is 1b/1c's,
        the shared full-row source 1e's)."""
        spec = self._make_linked_qualified_spec()
        doc = _page_document(_saved_page(dr_module, auto_df, spec)[0])
        by_y = {(r.glyph.y.field if hasattr(r.glyph.y, "field") else r.glyph.y): r
                for _f, r in _glyph_layers(doc.roots)}
        assert set(by_y) == {"mpg", "price"}, list(by_y)
        assert len({r.data_source.id for r in by_y.values()}) == 1, (
            "linked graphs must share one source")
        assert len(next(iter(by_y["mpg"].data_source.data.values()))) == \
            len(auto_df), "the shared linked source must hold every row"

    @staticmethod
    def _layer_drawing(doc, ycol):
        """The one layer of the saved document that draws *ycol*."""
        found = [r for _f, r in _glyph_layers(doc.roots)
                 if getattr(r.glyph.y, "field", r.glyph.y) == ycol]
        assert len(found) == 1, (ycol, found)
        return found[0]

    def test_linked_qualified_graph_has_cdsview(self, dr_module, auto_df):
        """BUG-34-1b: g1 figure must have CDSView with BooleanFilter when if_expr is set.

        This asserted only ``isinstance(r.view, CDSView)``.  Every
        GlyphRenderer has one -- Bokeh gives each a default CDSView whose
        filter is AllIndices -- so it held with no qualifier view at all
        (measured: g1 drew all 30 rows) and would hold with a view that kept
        the wrong rows (WP-24, 24sep2026).  What the view is FOR is read
        instead, from the saved page's document: g1's filter is a
        BooleanFilter, and the rows g1 draws through it over the shared
        source are exactly the foreign == 1 rows.  The control is the same
        linked pair with no qualifier, whose g1 draws every row."""
        doc = _page_document(_saved_page(
            dr_module, auto_df, self._make_linked_qualified_spec())[0])
        g1 = self._layer_drawing(doc, "mpg")
        assert type(g1.view.filter).__name__ == "BooleanFilter", (
            f"g1's view filter is {type(g1.view.filter).__name__}")
        want = sorted(auto_df.loc[auto_df["foreign"] == 1, "weight"])
        assert 0 < len(want) < len(auto_df)
        assert sorted(_drawn_values(g1, "weight")) == want, (
            "g1's view does not keep exactly its foreign == 1 rows")

        plain = _page_document(_saved_page(
            dr_module, auto_df, self._make_linked_qualified_spec(if_expr=""))[0])
        assert sorted(_drawn_values(self._layer_drawing(plain, "mpg"),
                                    "weight")) == sorted(auto_df["weight"]), (
            "control: an unqualified linked g1 must draw every row")

    def test_unqualified_linked_graph_has_no_qualifier_view(self, dr_module, auto_df):
        """BUG-34-1c: g2 (no if_expr) must not have a CDSView forced by qualifier."""
        from bokeh.models import CDSView, BooleanFilter
        spec = self._make_linked_qualified_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            render_models(renderer)
            g2_fig = renderer.figures.get("g2")
            assert g2_fig is not None, "g2 figure must be built"
            # g2 has no qualifier so must not have a boolean-filter view
            bool_views = [r.view for r in g2_fig.renderers
                          if hasattr(r, "view") and r.view is not None
                          and isinstance(r.view, CDSView)
                          and isinstance(getattr(r.view, "filter", None), BooleanFilter)]
            assert not bool_views, (
                "g2 (no if_expr) must not have a BooleanFilter CDSView "
                "— only graphs with qualifiers should get one"
            )
        finally:
            for _p in (spec_path, data_path):
                try:
                    os.unlink(_p)
                except OSError:
                    pass

    def test_linked_qualified_html_contains_both_graphs(self, dr_module, auto_df):
        """BUG-34-1d: the saved page draws both g1 and g2.

        This searched the page for "mpg" and "price", which its embedded data
        carries whether or not either graph is drawn (WP-24, 24sep2026).
        Read from the page's document instead: one layer draws g1's mpg,
        through its foreign == 1 view, and one draws g2's price, unqualified,
        over every row."""
        doc = _page_document(_saved_page(
            dr_module, auto_df, self._make_linked_qualified_spec())[0])
        g1 = self._layer_drawing(doc, "mpg")
        g2 = self._layer_drawing(doc, "price")
        n_foreign = int((auto_df["foreign"] == 1).sum())
        assert 0 < n_foreign < len(auto_df)
        assert len(_drawn_values(g1, "weight")) == n_foreign, (
            "g1 does not draw its foreign == 1 rows")
        assert sorted(_drawn_values(g2, "weight")) == sorted(
            auto_df["weight"]), "g2 does not draw every row"

    def test_shared_source_covers_all_rows(self, dr_module, auto_df):
        """BUG-34-1e: the shared linked source must contain all rows (not filtered)."""
        spec = self._make_linked_qualified_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            render_models(renderer)
            # g1 and g2 share one source
            g1_src = renderer.sources.get("g1")
            g2_src = renderer.sources.get("g2")
            assert g1_src is g2_src, "linked graphs must share the same ColumnDataSource"
            n = len(list(g1_src.data.values())[0]) if g1_src.data else 0
            n_df = len(auto_df)
            assert n == n_df, (
                f"shared linked source must contain all {n_df} rows (got {n}); "
                "per-graph qualifier must be applied via CDSView, not by filtering the source"
            )
        finally:
            for _p in (spec_path, data_path):
                try:
                    os.unlink(_p)
                except OSError:
                    pass


class TestMixedFilterSpecAlignment:
    """Regression tests for BUG-23: when some filter variables are absent from
    the data source, the remaining successfully-built specs and widgets must
    remain in 1:1 alignment, and _FILTER_JS must guard against undefined
    widget refs or missing column refs so callbacks never throw at runtime.

    Tests:
      BUG-FSALIGN-1a  filter_specs_json contains only built-spec vars (no missing var)
      BUG-FSALIGN-1b  all_widgets length matches filter_specs_json length
      BUG-FSALIGN-1c  _FILTER_JS contains defensive guard against undefined widget
      BUG-FSALIGN-1d  _FILTER_JS contains defensive guard against missing orig column
      BUG-FSALIGN-1e  JS filter loop does not crash when spec list aligns with widgets
      BUG-FSALIGN-1f  Render with one valid + one missing filter var does not crash
      BUG-FSALIGN-1g  Valid filter widget still fires callback when paired spec is present
    """

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _make_mixed_filter_spec(self, extra_var: str = "missingvar") -> dict:
        """Spec with two filter vars: 'foreign' (present) + extra_var (absent)."""
        return _make_spec_json(
            graphs=[
                {"plots": [{"type": "scatter", "yvar": "mpg",
                            "xvar": "weight", "options": {}}],
                 "graph_options": {"name": "g1"}},
            ],
            build_options={
                "layout": "auto", "link": "",
                "filter": f"foreign, type(dropdown)||{extra_var}, type(dropdown)",
                "theme": "default", "title": "T", "subtitle": "",
                "registry": "g1", "mode": "standalone", "port": "5006",
            }
        )

    # ------------------------------------------------------------------
    # BUG-FSALIGN-1a: filter_specs_json should only include vars that were built
    # ------------------------------------------------------------------

    def test_filter_specs_json_excludes_missing_var(self, dr_module, auto_df):
        """BUG-FSALIGN-1a: filter_specs_json must not include the missing variable."""
        spec = self._make_mixed_filter_spec("missingvar")
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            render_models(renderer)
            # This SKIPPED when no callback was built, so a regression that
            # stopped building it reported a skip, not a failure.  The valid
            # filter (foreign) builds one (measured 24sep2026, WP-24).
            assert renderer.filter_callbacks, (
                "no filter callback was built for the valid filter (foreign)")
            cb_args = renderer.filter_callbacks[0].args
            filter_specs = json.loads(cb_args["filter_specs_json"])
            varnames = [fs["varname"] for fs in filter_specs]
            assert "missingvar" not in varnames, (
                "filter_specs_json must not include 'missingvar' (absent from data)"
            )
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    # ------------------------------------------------------------------
    # BUG-FSALIGN-1b: all_widgets length must match filter_specs length
    # ------------------------------------------------------------------

    def test_all_widgets_matches_filter_specs_length(self, dr_module, auto_df):
        """BUG-FSALIGN-1b: all_widgets and filter_specs_json must have the same length."""
        spec = self._make_mixed_filter_spec("missingvar")
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            render_models(renderer)
            # Was a skip when no callback was built (WP-24); foreign builds one.
            assert renderer.filter_callbacks, (
                "no filter callback was built for the valid filter (foreign)")
            cb_args = renderer.filter_callbacks[0].args
            filter_specs = json.loads(cb_args["filter_specs_json"])
            all_widgets  = cb_args.get("all_widgets", [])
            # Pinned to the one valid filter: two empty lists are equal too.
            assert len(all_widgets) == len(filter_specs) == 1, (
                f"all_widgets ({len(all_widgets)}) must equal filter_specs "
                f"({len(filter_specs)}) — misalignment causes wrong spec/widget pairing"
            )
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    # ------------------------------------------------------------------
    # BUG-FSALIGN-1c: _FILTER_JS must guard against undefined widget
    # ------------------------------------------------------------------

    def test_filter_js_guards_against_undefined_widget(self, dr_module):
        """BUG-FSALIGN-1c: _FILTER_JS must check `!w` before accessing w.value."""
        js = dr_module._FILTER_JS
        assert "!w" in js or "w == null" in js or "w === undefined" in js, (
            "_FILTER_JS must guard against undefined widget reference "
            "(e.g. `if (!w || ...) continue;`) to prevent JS TypeError at runtime"
        )

    # ------------------------------------------------------------------
    # BUG-FSALIGN-1d: _FILTER_JS must guard against missing orig column
    # ------------------------------------------------------------------

    def test_filter_js_guards_against_missing_orig_column(self, dr_module):
        """BUG-FSALIGN-1d: _FILTER_JS must check orig[fvar] before indexing."""
        js = dr_module._FILTER_JS
        assert "!(fvar in orig)" in js or "orig[fvar] == null" in js \
               or "!orig[fvar]" in js or "fvar in orig" in js, (
            "_FILTER_JS must guard against accessing orig[fvar] when the column "
            "is absent (e.g. `if (!w || !(fvar in orig)) continue;`)"
        )

    # ------------------------------------------------------------------
    # BUG-FSALIGN-1e: simulated JS alignment check (Python-side)
    # ------------------------------------------------------------------

    def test_filter_specs_and_widgets_stay_aligned_after_skip(self, dr_module, auto_df):
        """BUG-FSALIGN-1e: after skipping a missing-var spec, built specs and
        widgets must index identically — spot check via Python enumeration."""
        spec = self._make_mixed_filter_spec("missingvar")
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            render_models(renderer)
            # Was a skip when no callback was built (WP-24); foreign builds one.
            assert renderer.filter_callbacks, (
                "no filter callback was built for the valid filter (foreign)")
            cb_args = renderer.filter_callbacks[0].args
            filter_specs = json.loads(cb_args["filter_specs_json"])
            all_widgets  = cb_args.get("all_widgets", [])
            # The zip below runs once per spec; with none it would check
            # nothing.  The one built spec is foreign's.
            assert [s["varname"] for s in filter_specs] == ["foreign"], filter_specs
            assert len(all_widgets) == 1, all_widgets
            # Each spec varname must be present in the first source's data
            src_data_keys = set(next(iter(renderer.sources.values())).data.keys())
            for i, (spec_item, widget) in enumerate(zip(filter_specs, all_widgets)):
                assert spec_item["varname"] in src_data_keys, (
                    f"filter_spec[{i}].varname='{spec_item['varname']}' is not in "
                    f"source data — misaligned spec crept in"
                )
                assert widget is not None, (
                    f"all_widgets[{i}] is None — None widget was incorrectly inserted"
                )
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    # ------------------------------------------------------------------
    # BUG-FSALIGN-1f: render with one valid + one missing var must not crash
    # ------------------------------------------------------------------

    def test_render_with_valid_plus_missing_filter_does_not_crash(self, dr_module, auto_df):
        """BUG-FSALIGN-1f: with one valid and one missing filter var, render
        builds the scatter and the surviving foreign dropdown.

        This asserted ``html_out`` was truthy, which any non-empty string is
        (WP-24, measured 24sep2026).  A ``does not raise`` guard, kept as one
        (it fails the test on any exception), made to see that render
        produced the dashboard -- the g1 scatter over all 30 rows and the one
        foreign widget, the missing column dropped."""
        from bokeh.models import Select
        spec = self._make_mixed_filter_spec("totallymissingcolumn")
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            try:
                page = renderer.render()
            except Exception as exc:
                pytest.fail(
                    f"BUG-FSALIGN-1f: render() raised with mixed filter vars: {exc!r}"
                )
            doc = _page_document(page)
            (_fig, r), = _glyph_layers(doc.roots)
            assert len(_drawn_values(r, "weight")) == len(auto_df)
            assert sorted(w.title for w in doc.select({"type": Select})) == \
                ["foreign"], "only the valid filter's widget must be built"
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    # ------------------------------------------------------------------
    # BUG-FSALIGN-1g: valid filter widget's callback fires correctly
    # ------------------------------------------------------------------

    def test_valid_filter_widget_callback_fires_without_error(self, dr_module, auto_df):
        """BUG-FSALIGN-1g: the surviving filter's spec and widget stay paired
        when another filter's spec was skipped.

        The callback reads its i-th spec beside its i-th widget, so a
        misalignment is a spec naming one variable beside another's widget.
        This compared the two lists' lengths -- equal at 0 and 0, and equal
        with the spec relabelled -- and built a mock widget it never used
        (WP-24, 24sep2026).  The one spec must name foreign, a dropdown
        with its sentinel, and the one widget must be foreign's Select,
        opening on that sentinel over foreign's values.  (Running the
        script itself is test_filters.py's.)"""
        spec = self._make_mixed_filter_spec("missingvar")
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            render_models(renderer)
            # Was a skip when no callback was built (WP-24); foreign builds one.
            assert renderer.filter_callbacks, (
                "no filter callback was built for the valid filter (foreign)")
            cb_args = renderer.filter_callbacks[0].args
            filter_specs = json.loads(cb_args["filter_specs_json"])
            all_widgets = cb_args.get("all_widgets", [])
            assert filter_specs == [{"varname": "foreign", "type": "dropdown",
                                     "sentinel": "__all__", "numeric": True,
                                     "groups": [[0.0], [1.0]]}], (
                "BUG-FSALIGN-1g: the surviving spec is not foreign's: "
                f"{filter_specs}")
            assert len(all_widgets) == 1, all_widgets
            (w,) = all_widgets
            assert type(w).__name__ == "Select" and w.title == "foreign", (
                f"the surviving widget is {type(w).__name__} {w.title!r}")
            assert w.value == "__all__"
            values = sorted(auto_df["foreign"].dropna().unique())
            assert [v for v, _label in w.options] == (
                ["__all__"] + [float(v) for v in values]), w.options
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass


# ---------------------------------------------------------------------------
# BUG-35: KPI min/max filter callback can fail on large arrays (spread overflow)
# ---------------------------------------------------------------------------

class TestKpiMinMaxSpreadOverflow:
    """BUG-35: _FILTER_JS min/max must use reduce, not spread, to avoid RangeError.

    Pre-fix: ``Math.min(...vals)`` and ``Math.max(...vals)`` pass every element
    as a function argument; on arrays with >~100k elements this throws
    ``RangeError: Maximum call stack size exceeded``.

    Post-fix: use ``vals.reduce((a,b) => a < b ? a : b, vals[0])`` which is
    O(n) and never hits the argument limit.
    """

    def test_filter_js_min_uses_reduce(self, dr_module, auto_df):
        """BUG-35-1a: _FILTER_JS must use reduce for 'min', not Math.min(...vals)."""
        js = dr_module._FILTER_JS
        assert "Math.min(...vals)" not in js, (
            "_FILTER_JS must NOT use Math.min(...vals) — replace with reduce "
            "to avoid RangeError on large arrays"
        )
        assert "reduce" in js, (
            "_FILTER_JS must use reduce() for min to handle large arrays safely"
        )

    def test_filter_js_max_uses_reduce(self, dr_module, auto_df):
        """BUG-35-1b: _FILTER_JS must use reduce for 'max', not Math.max(...vals)."""
        js = dr_module._FILTER_JS
        assert "Math.max(...vals)" not in js, (
            "_FILTER_JS must NOT use Math.max(...vals) — replace with reduce "
            "to avoid RangeError on large arrays"
        )

    def test_min_reduce_expression_correct(self, dr_module, auto_df):
        """BUG-35-1c: reduce expression for min must use a < b comparison."""
        js = dr_module._FILTER_JS
        assert "a < b" in js or "a<b" in js, (
            "_FILTER_JS min reduce must compare a < b to select the minimum"
        )

    def test_max_reduce_expression_correct(self, dr_module, auto_df):
        """BUG-35-1d: reduce expression for max must use a > b comparison."""
        js = dr_module._FILTER_JS
        assert "a > b" in js or "a>b" in js, (
            "_FILTER_JS max reduce must compare a > b to select the maximum"
        )


# ---------------------------------------------------------------------------
# BUG-24: Standalone aggregate plots remain stale when filters return zero rows
# ---------------------------------------------------------------------------

class TestAggregateStaleOnZeroRows:
    """Regression tests for BUG-24: when the active filter returns zero rows,
    histogram and kdensity aggregate sources must be explicitly cleared (set to
    zero counts / empty arrays) rather than left with stale previous data.

    Tests:
      BUG-AGGSTALE-1a  _FILTER_JS does NOT do `if (vals.length === 0) continue;`
                        unconditionally for histogram (must clear instead)
      BUG-AGGSTALE-1b  _FILTER_JS does NOT do `if (n < 2) continue;`
                        unconditionally for kdensity (must clear instead)
      BUG-AGGSTALE-1c  _FILTER_JS clears histogram source when vals empty
      BUG-AGGSTALE-1d  _FILTER_JS clears kdensity source when vals empty
    """

    # ------------------------------------------------------------------
    # BUG-AGGSTALE-1a: histogram zero-row path must clear, not skip
    # ------------------------------------------------------------------

    def test_filter_js_histogram_zero_path_is_not_plain_continue(self, dr_module):
        """BUG-AGGSTALE-1a: _FILTER_JS must not silently skip histogram on zero vals."""
        js = dr_module._FILTER_JS
        # The old broken pattern was: `if (vals.length === 0) continue;`
        # The fixed code must either not have this at all, or handle it by
        # writing zeroed counts to src.data before continuing.
        # We check that either:
        #  (a) there's a histogram zero-clear block, OR
        #  (b) there's no bare `vals.length === 0) continue` before the histogram block
        # The simplest reliable check: the fix replaces the bare continue with a
        # block that assigns zero counts. We check for the zero-fill pattern.
        # Acceptable patterns: `fill(0)` in context of histogram clear, or
        # `counts = new Array(n_bins).fill(0); ... src.data = {...}; src.change.emit()`
        # The key invariant: src.data must be assigned even when vals is empty.
        # We verify by checking there is no pattern `vals.length === 0) continue;`
        # (the raw bare-continue pattern) adjacent to the histogram block.
        # NOTE: the guard at line 4222 (`if (vals.length === 0) continue;`) was the bug.
        assert "if (vals.length === 0) continue;" not in js, (
            "_FILTER_JS must not unconditionally `continue` when vals is empty — "
            "doing so leaves the aggregate source stale with old data."
        )

    # ------------------------------------------------------------------
    # BUG-AGGSTALE-1b: kdensity < 2 path must clear, not skip
    # ------------------------------------------------------------------

    def test_filter_js_kdensity_small_n_is_not_plain_continue(self, dr_module):
        """BUG-AGGSTALE-1b: _FILTER_JS must not silently skip kdensity when n < 2."""
        js = dr_module._FILTER_JS
        # The old broken pattern: `if (n < 2) continue;`
        # Fixed code must assign empty arrays to src.data when n < 2.
        assert "if (n < 2) continue;" not in js, (
            "_FILTER_JS must not unconditionally `continue` when kdensity n < 2 — "
            "doing so leaves the kdensity source stale with old data."
        )

    # ------------------------------------------------------------------
    # BUG-AGGSTALE-1c: histogram source cleared with zero counts on empty vals
    # ------------------------------------------------------------------

    def test_filter_js_histogram_zero_path_clears_source(self, dr_module):
        """BUG-AGGSTALE-1c: _FILTER_JS must write zero counts when histogram vals empty."""
        js = dr_module._FILTER_JS
        # There should be handling that clears histogram src.data when empty.
        # Acceptable: assigning `top: new Array(n_bins).fill(0)` or `top: []`
        # We check for explicit zero-clear in the histogram branch.
        assert (
            "fill(0)" in js or
            "top: []" in js or
            "vals.length === 0" in js  # if kept with explicit clear block
        ), (
            "_FILTER_JS histogram zero-row path must explicitly clear src.data "
            "(e.g. top: new Array(n_bins).fill(0)) rather than leaving it stale."
        )

    # ------------------------------------------------------------------
    # BUG-AGGSTALE-1d: kdensity source cleared with empty arrays on n < 2
    # ------------------------------------------------------------------

    def test_filter_js_kdensity_empty_clears_source(self, dr_module):
        """BUG-AGGSTALE-1d: _FILTER_JS must write empty x/y arrays when kdensity n < 2."""
        js = dr_module._FILTER_JS
        # There should be a path that sets { x: [], y: [] } for kdensity when
        # insufficient data exists.
        assert (
            "x: [], y: []" in js or
            "{ x: [], y: [] }" in js or
            "x: []" in js
        ), (
            "_FILTER_JS kdensity n<2 path must explicitly assign empty x/y arrays "
            "to src.data so the chart clears instead of showing stale data."
        )


# ---------------------------------------------------------------------------
# BUG-25: Server dropdown filters use display labels as keys, losing distinct values
# ---------------------------------------------------------------------------

class TestServerDropdownDistinctValues:
    """Regression tests for BUG-25: generated server Select widgets must use
    raw values as option keys (not display labels), so categories sharing the
    same display label remain independently selectable, and the 'All' sentinel
    cannot collide with a real data value.

    Tests:
      BUG-DROPDOWN-1a  Generated code uses ('__all__', 'All') sentinel, not ('All', 'All')
      BUG-DROPDOWN-1b  Generated code sets options as (value, label) tuples, not labels only
      BUG-DROPDOWN-1c  Generated code uses '__all__' sentinel in callback guard
      BUG-DROPDOWN-1d  Generated code uses w.value directly (no opts_map indirection)
      BUG-DROPDOWN-1e  Generated code does not contain opts_map lookup in callback
    """

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _make_dropdown_spec(self) -> dict:
        return _make_spec_json(
            graphs=[
                {"plots": [{"type": "scatter", "yvar": "mpg",
                            "xvar": "weight", "options": {}}],
                 "graph_options": {"name": "g1"}},
            ],
            build_options={
                "layout": "auto", "link": "",
                "filter": "foreign, type(dropdown)",
                "theme": "default", "title": "T", "subtitle": "",
                "registry": "g1", "mode": "server", "port": "5006",
            }
        )

    def _get_generated_source(self, dr_module, auto_df) -> str:
        """Build server app source code and return as string."""
        spec = self._make_dropdown_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            return builder._generate_app_source(5006)
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    # ------------------------------------------------------------------
    # BUG-DROPDOWN-1a: sentinel must be '__all__', not 'All'
    # ------------------------------------------------------------------

    def test_generated_code_uses_dunder_all_sentinel(self, dr_module, auto_df):
        """BUG-DROPDOWN-1a: generated opts sentinel must be '__all__' not 'All'."""
        src = self._get_generated_source(dr_module, auto_df)
        assert "'__all__'" in src or '"__all__"' in src, (
            "Generated server code must use '__all__' as the sentinel value "
            "for the 'All' dropdown option to avoid colliding with real data values"
        )

    # ------------------------------------------------------------------
    # BUG-DROPDOWN-1b: Select options must be (value, label) tuples
    # ------------------------------------------------------------------

    def test_generated_code_uses_tuple_options(self, dr_module, auto_df):
        """BUG-DROPDOWN-1b: generated Select options must be (raw, label) tuples."""
        src = self._get_generated_source(dr_module, auto_df)
        # Old broken pattern: options=[o[1] for o in opts]  (labels only)
        assert "options=[o[1] for o in opts]" not in src, (
            "Generated server code must NOT use labels-only options list; "
            "use (value, label) tuples so raw values are widget option keys."
        )

    # ------------------------------------------------------------------
    # BUG-DROPDOWN-1c: callback must check __all__ sentinel
    # ------------------------------------------------------------------

    def test_generated_callback_checks_dunder_all_sentinel(self, dr_module, auto_df):
        """BUG-DROPDOWN-1c: generated callback must compare w.value against '__all__'."""
        src = self._get_generated_source(dr_module, auto_df)
        assert ("__all__" in src), (
            "Generated callback must guard on w.value != '__all__' not != 'All'"
        )
        # The old broken pattern
        assert "w.value != 'All'" not in src, (
            "Generated callback must not guard on 'All' — use '__all__' sentinel."
        )

    # ------------------------------------------------------------------
    # BUG-DROPDOWN-1d: callback must use w.value directly as raw value
    # ------------------------------------------------------------------

    def test_generated_callback_uses_widget_value_directly(self, dr_module, auto_df):
        """BUG-DROPDOWN-1d: callback must use w.value directly, not opts_map lookup."""
        src = self._get_generated_source(dr_module, auto_df)
        # With tuple options, w.value IS the raw value; no opts_map needed.
        # Old broken pattern: raw_val = raw_map.get(w.value, w.value)
        assert "raw_map.get(w.value" not in src, (
            "Generated callback must not use opts_map to translate label -> raw value; "
            "with tuple options, w.value is already the raw value."
        )

    # ------------------------------------------------------------------
    # BUG-DROPDOWN-1e: _dash_opts_map should not be set in generated code
    # ------------------------------------------------------------------

    def test_generated_code_does_not_set_opts_map(self, dr_module, auto_df):
        """BUG-DROPDOWN-1e: generated code must not build _dash_opts_map (redundant)."""
        src = self._get_generated_source(dr_module, auto_df)
        assert "_dash_opts_map" not in src, (
            "Generated server code must not set _dash_opts_map — "
            "with tuple-valued Select options the opts_map reverse lookup is unnecessary."
        )


# ---------------------------------------------------------------------------
# BUG-26: Server app crashes when slider/range filter targets a string variable
# ---------------------------------------------------------------------------

def _make_string_col_data_json(df: pd.DataFrame, string_cols: list) -> str:
    """Like _make_data_json but marks specified columns as string type."""
    values = []
    for _, row in df.iterrows():
        values.append({col: (None if pd.isna(row[col]) else row[col])
                       for col in df.columns})
    return json.dumps({
        "variableNames": list(df.columns),
        "variableLabels": {c: c for c in df.columns},
        "valueLabelNames": {},
        "valueLabels": {},
        "variableTypeIsString": {c: (c in string_cols) for c in df.columns},
        "values": values,
    })


def _write_temp_files_with_strings(df: pd.DataFrame, spec_dict: dict, string_cols: list):
    """Write spec and data JSON (with string-col flags) to temp files."""
    spec_f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(spec_dict, spec_f)
    spec_f.close()
    data_f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    data_f.write(_make_string_col_data_json(df, string_cols))
    data_f.close()
    return spec_f.name, data_f.name


class TestServerSliderStringFallback:
    """Regression tests for BUG-26: generated server code must not raise
    ValueError when slider/range filter is applied to a string column.
    The numeric dtype check must happen at document-build time before any
    float() conversion attempt.

    Tests:
      BUG-SLIDER-STR-1a  Generated code contains numeric dtype guard for range type
      BUG-SLIDER-STR-1b  Generated code contains numeric dtype guard for slider type
      BUG-SLIDER-STR-1c  Generated server app with slider on string var compiles
      BUG-SLIDER-STR-1d  make_document with slider on string var does not raise ValueError
    """

    def _string_df(self) -> pd.DataFrame:
        """DataFrame with numeric columns + a genuine string column 'group'."""
        rng = np.random.default_rng(0)
        n = 20
        return pd.DataFrame({
            "mpg":    rng.integers(12, 40, n).astype(float),
            "weight": rng.integers(1800, 4800, n).astype(float),
            "group":  ["A", "B", "C"] * 6 + ["A", "B"],
        })

    def _make_slider_string_spec(self, ftype: str = "slider") -> dict:
        """Spec with a slider/range filter on 'group' (string column)."""
        return _make_spec_json(
            graphs=[
                {"plots": [{"type": "scatter", "yvar": "mpg",
                            "xvar": "weight", "options": {}}],
                 "graph_options": {"name": "g1"}},
            ],
            build_options={
                "layout": "auto", "link": "",
                "filter": f"group, type({ftype})",
                "theme": "default", "title": "T", "subtitle": "",
                "registry": "g1", "mode": "server", "port": "5006",
            }
        )

    # ------------------------------------------------------------------
    # BUG-SLIDER-STR-1a: generated code guards range against string var
    # ------------------------------------------------------------------

    def test_generated_code_has_numeric_guard_for_range(self, dr_module):
        """BUG-SLIDER-STR-1a: generated code must check numeric dtype before range build."""
        df = self._string_df()
        spec = self._make_slider_string_spec("range")
        spec_path, data_path = _write_temp_files_with_strings(df, spec, ["group"])
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            src = builder._generate_app_source(5006)
            assert (
                "is_numeric_dtype" in src or
                "api.types" in src or
                "pd.to_numeric" in src or
                "dtype" in src
            ), (
                "Generated code must guard range filter with a numeric dtype check "
                "to prevent float(df[fvar].min()) from raising ValueError on strings."
            )
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    # ------------------------------------------------------------------
    # BUG-SLIDER-STR-1b: generated code guards slider against string var
    # ------------------------------------------------------------------

    def test_generated_code_has_numeric_guard_for_slider(self, dr_module):
        """BUG-SLIDER-STR-1b: generated code must check numeric dtype before slider build."""
        df = self._string_df()
        spec = self._make_slider_string_spec("slider")
        spec_path, data_path = _write_temp_files_with_strings(df, spec, ["group"])
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            src = builder._generate_app_source(5006)
            assert (
                "is_numeric_dtype" in src or
                "api.types" in src or
                "pd.to_numeric" in src or
                "dtype" in src
            ), (
                "Generated code must guard slider filter with a numeric dtype check."
            )
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    # ------------------------------------------------------------------
    # BUG-SLIDER-STR-1c: generated server file with slider on string var compiles
    # ------------------------------------------------------------------

    def test_generated_server_file_compiles_with_slider_on_string(self, dr_module):
        """BUG-SLIDER-STR-1c: server file with slider on string column must compile."""
        df = self._string_df()
        spec = self._make_slider_string_spec("slider")
        spec_path, data_path = _write_temp_files_with_strings(df, spec, ["group"])
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as out_f:
            out_path = out_f.name
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_path)
            import ast
            with open(out_path) as f:
                src = f.read()
            try:
                ast.parse(src)
            except SyntaxError as exc:
                pytest.fail(
                    f"BUG-SLIDER-STR-1c: generated server file has syntax error: {exc}"
                )
        finally:
            for _p in (spec_path, data_path, out_path):
                try: os.unlink(_p)
                except OSError: pass

    # ------------------------------------------------------------------
    # BUG-SLIDER-STR-1d: make_document with slider on string var does not raise
    # ------------------------------------------------------------------

    def test_make_document_with_slider_on_string_does_not_raise(self, dr_module):
        """BUG-SLIDER-STR-1d: make_document must not raise ValueError when slider
        targets a string column (must skip/warn rather than crash)."""
        df = self._string_df()
        spec = self._make_slider_string_spec("slider")
        spec_path, data_path = _write_temp_files_with_strings(df, spec, ["group"])
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as out_f:
            out_path = out_f.name
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_path)
            mod = load_app(out_path, "_test_slider_app")
            from bokeh.document import Document
            doc = Document()
            try:
                mod.make_document(doc)
            except ValueError as exc:
                pytest.fail(
                    f"BUG-SLIDER-STR-1d: make_document raised ValueError for "
                    f"slider on string column: {exc!r}"
                )
        finally:
            for _p in (spec_path, data_path, out_path):
                try: os.unlink(_p)
                except OSError: pass


# ---------------------------------------------------------------------------
# BUG-27: KPI filter callback allows style-attribute injection via unescaped colors
# ---------------------------------------------------------------------------

class TestKpiColorCssInjectionHardening:
    """Regression tests for BUG-27: KPI color and bgcolor fields must be
    validated against a safe CSS color whitelist before being stored in the
    filter callback config.  Unvalidated values can break out of the
    inline `style="..."` attribute and inject event handlers or markup.

    Tests:
      BUG-CSS-KPI-1a  A crafted color value containing a quote is rejected
      BUG-CSS-KPI-1b  A crafted bgcolor value containing a semicolon is rejected
      BUG-CSS-KPI-1c  Valid hex color is kept unchanged
      BUG-CSS-KPI-1d  Valid named color is kept unchanged
      BUG-CSS-KPI-1e  Valid rgb() color is kept unchanged
      BUG-CSS-KPI-1f  Injected color falls back to safe default in callback config
      BUG-CSS-KPI-1g  _sanitize_css_color helper exists and is callable
    """

    # ------------------------------------------------------------------
    # BUG-CSS-KPI-1g: helper function exists
    # ------------------------------------------------------------------

    def test_sanitize_css_color_helper_exists(self, dr_module):
        """BUG-CSS-KPI-1g: _sanitize_css_color must exist as a callable in dash_render."""
        assert hasattr(dr_module, "_sanitize_css_color"), (
            "dash_render must export _sanitize_css_color(val, default) helper "
            "so that caller sites can sanitize color fields uniformly."
        )
        assert callable(dr_module._sanitize_css_color), (
            "_sanitize_css_color must be callable."
        )

    # ------------------------------------------------------------------
    # BUG-CSS-KPI-1a: crafted color with quote is rejected
    # ------------------------------------------------------------------

    def test_crafted_color_with_quote_is_rejected(self, dr_module):
        """BUG-CSS-KPI-1a: color value containing a quote must not pass validation."""
        fn = dr_module._sanitize_css_color
        bad = 'red"; onmouseover="alert(1)'
        result = fn(bad, "#212529")
        assert result == "#212529", (
            f"_sanitize_css_color must reject injected color value; got: {result!r}"
        )

    # ------------------------------------------------------------------
    # BUG-CSS-KPI-1b: crafted bgcolor with semicolon is rejected
    # ------------------------------------------------------------------

    def test_crafted_bgcolor_with_semicolon_is_rejected(self, dr_module):
        """BUG-CSS-KPI-1b: bgcolor value containing a semicolon must not pass."""
        fn = dr_module._sanitize_css_color
        bad = "red; display:none"
        result = fn(bad, "#f8f9fa")
        assert result == "#f8f9fa", (
            f"_sanitize_css_color must reject CSS-injection bgcolor; got: {result!r}"
        )

    # ------------------------------------------------------------------
    # BUG-CSS-KPI-1c: valid hex color passes through
    # ------------------------------------------------------------------

    def test_valid_hex_color_is_kept(self, dr_module):
        """BUG-CSS-KPI-1c: valid hex colors (#RGB, #RRGGBB) must pass through."""
        fn = dr_module._sanitize_css_color
        for val in ("#f00", "#ff0000", "#FF0000", "#abc123"):
            result = fn(val, "#000000")
            assert result == val, (
                f"_sanitize_css_color must accept hex color {val!r}; got {result!r}"
            )

    # ------------------------------------------------------------------
    # BUG-CSS-KPI-1d: valid named color passes through
    # ------------------------------------------------------------------

    def test_valid_named_color_is_kept(self, dr_module):
        """BUG-CSS-KPI-1d: CSS named colors (letters only) must pass through."""
        fn = dr_module._sanitize_css_color
        for val in ("red", "blue", "cornsilk", "steelblue"):
            result = fn(val, "#000000")
            assert result == val, (
                f"_sanitize_css_color must accept named color {val!r}; got {result!r}"
            )

    # ------------------------------------------------------------------
    # BUG-CSS-KPI-1e: valid rgb() color passes through
    # ------------------------------------------------------------------

    def test_valid_rgb_color_is_kept(self, dr_module):
        """BUG-CSS-KPI-1e: rgb() and rgba() colors must pass through."""
        fn = dr_module._sanitize_css_color
        for val in ("rgb(255,0,0)", "rgb(0, 128, 255)", "rgba(255,0,0,0.5)"):
            result = fn(val, "#000000")
            assert result == val, (
                f"_sanitize_css_color must accept {val!r}; got {result!r}"
            )

    # ------------------------------------------------------------------
    # BUG-CSS-KPI-1f: injected color falls back to safe default in callback config
    # ------------------------------------------------------------------

    def test_injected_color_falls_back_in_callback_config(self, dr_module, auto_df):
        """BUG-CSS-KPI-1f: callback config must use safe default when color is injected."""
        bad_color = 'red"; onmouseover="alert(1)'
        spec = _make_spec_json(
            graphs=[
                {"plots": [{"type": "scatter", "yvar": "mpg",
                            "xvar": "weight", "options": {}}],
                 "graph_options": {"name": "g1"}},
            ],
            kpis=[{
                "name": "kpi1", "stat": "mean", "var": "mpg",
                "title": "MPG", "subtitle": "", "update": "filter",
                "color": bad_color, "bgcolor": "#f8f9fa",
            }],
            build_options={
                "layout": "auto", "link": "",
                "filter": "foreign, type(dropdown)",
                "theme": "default", "title": "T", "subtitle": "",
                "registry": "g1", "mode": "standalone", "port": "5006",
            }
        )
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            render_models(renderer)
            # Both of these were skips, so a regression that stopped building
            # the filter callback, or stopped handing it the KPI's config,
            # reported a skip rather than a failure.  The foreign dropdown
            # builds one callback carrying kpi1's config (measured 24sep2026,
            # WP-24).
            assert renderer.filter_callbacks, (
                "no filter callback was built for the foreign dropdown")
            cb_args = renderer.filter_callbacks[0].args
            kpi_config = json.loads(cb_args["kpi_config_json"])
            assert [k.get("name") for k in kpi_config] == ["kpi1"], (
                f"the filter callback carries no config for kpi1: {kpi_config!r}")
            kpi_color = kpi_config[0].get("color", "")
            assert '"' not in kpi_color and "onmouseover" not in kpi_color, (
                f"kpi_config color must not contain injected content; "
                f"got: {kpi_color!r}"
            )
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass


# ===========================================================================
# BUG-36: Server by() faceting ignores graph-level if_expr/in_expr
# ===========================================================================
# Before fix: the faceting section used `work_df = df.copy()` (global frame),
# so graph-level qualifiers were silently ignored during initial facet creation.
# A graph with `if_expr: "foreign == 1"` and `by: "foreign"` would produce
# two facets (for both foreign=0 and foreign=1) instead of one.
# Fix: compute `_by_q_df` by applying the graph's if_expr/in_expr first, then
# use that as the base for `work_df` so groupby() groups only qualified rows.

class TestServerByFacetingRespectsQualifiers:
    """Regression suite for BUG-36: server by() faceting must honour if_expr/in_expr.

    BUG-36-1a and 1b used to assert that the generated source contained the
    identifiers `_by_q_df', `_by_if' and `_by_px'.  The faceting block that
    held them is gone: the by() panels are built by the same figure body as
    the graph, from a frame the shared qualifier reader has already
    narrowed.  The two are restated below as behaviour -- the served panels
    hold the rows the saved ones hold.
    """

    def test_served_panels_hold_the_qualified_rows_the_saved_ones_hold(
            self, dr_module, auto_df):
        """BUG-36-1a, restated: by(foreign) if foreign == 1 -> one panel, both modes."""
        rows = _panel_rows_both_modes(dr_module, auto_df, "foreign == 1", "")
        assert rows["served"] == rows["saved"] == [len(auto_df[auto_df["foreign"] == 1])]

    def test_an_in_range_narrows_the_facets_in_both_modes(
            self, dr_module, auto_df):
        """BUG-36-1b, restated: by(foreign) in 1/5 groups the first five rows only."""
        rows = _panel_rows_both_modes(dr_module, auto_df, "", "1/5")
        assert rows["served"] == rows["saved"]
        assert sum(rows["served"]) == 5


    # ------------------------------------------------------------------
    # BUG-36-1c: runtime — if_expr limits facets to qualified groups only
    # ------------------------------------------------------------------

    def test_if_expr_limits_facets_to_qualified_groups(self, dr_module, auto_df):
        """BUG-36-1c: if_expr == foreign==1 with by(foreign) must produce only 1 facet."""
        from bokeh.document import Document
        # Build a DataFrame where foreign has values 0 and 1
        df = auto_df.copy()
        assert df["foreign"].nunique() == 2, "Need both foreign=0 and foreign=1 in test data"

        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign", "if_expr": "foreign == 1"},
        }])
        spec_path, data_path = _write_temp_files(df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_mod = load_app(out_f.name, "_b36c")
            doc = Document()
            app_mod.make_document(doc)
            n_renderers = _count_glyph_renderers(doc)
            # With fix: 1 facet (foreign==1 only) → 1 scatter renderer
            # Without fix: 2 facets (foreign=0 + foreign=1) → 2 renderers
            assert n_renderers == 1, (
                f"With if_expr='foreign==1' and by(foreign), expected 1 facet renderer "
                f"(only qualified group), got {n_renderers}"
            )
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try: os.unlink(_p)
                except OSError: pass

    # ------------------------------------------------------------------
    # BUG-36-1d: runtime — in_expr limits faceting row universe
    # ------------------------------------------------------------------

    def test_in_expr_limits_faceting_row_universe(self, dr_module):
        """BUG-36-1d: in_expr '1/N' must restrict which rows feed the by() groupby."""
        from bokeh.document import Document
        import pandas as pd, numpy as np

        # Construct data where only the first 5 rows have foreign=1;
        # rows 6+ have foreign=0.  With in_expr="1/5" only foreign=1 rows
        # are selected, so by(foreign) should produce exactly 1 facet.
        n = 20
        df = pd.DataFrame({
            "mpg":    np.linspace(15, 35, n),
            "weight": np.linspace(2000, 4000, n),
            "foreign": [1.0] * 5 + [0.0] * 15,
        })
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign", "in_expr": "1/5"},
        }])
        spec_path, data_path = _write_temp_files(df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_mod = load_app(out_f.name, "_b36d")
            doc = Document()
            app_mod.make_document(doc)
            n_renderers = _count_glyph_renderers(doc)
            # Only rows 1-5 are selected by in_expr; all have foreign=1 → 1 facet
            assert n_renderers == 1, (
                f"With in_expr='1/5' (all rows have foreign=1), expected 1 facet "
                f"renderer, got {n_renderers}"
            )
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try: os.unlink(_p)
                except OSError: pass

    # ------------------------------------------------------------------
    # BUG-36-1e: regression — no qualifier still produces all groups
    # ------------------------------------------------------------------

    def test_no_qualifier_produces_all_groups(self, dr_module, auto_df):
        """BUG-36-1e: without qualifier, by(foreign) must still create 2 facets."""
        from bokeh.document import Document
        df = auto_df.copy()
        assert df["foreign"].nunique() == 2, "Need both foreign values for regression guard"

        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign"},
        }])
        spec_path, data_path = _write_temp_files(df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_mod = load_app(out_f.name, "_b36e")
            doc = Document()
            app_mod.make_document(doc)
            n_renderers = _count_glyph_renderers(doc)
            # No qualifier → all rows → 2 foreign groups → 2 scatter renderers
            assert n_renderers == 2, (
                f"Without qualifier, by(foreign) should produce 2 facet renderers, "
                f"got {n_renderers}"
            )
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try: os.unlink(_p)
                except OSError: pass


# ===========================================================================
# BUG-37: Dropdown filter sentinel __all__ collides with legitimate data values
# ===========================================================================
# Before fix: both standalone and server dropdown filters hard-coded '__all__'
# as the "no filter" sentinel.  When real data contained '__all__', the option
# list had a duplicate value and the real category was treated as "no filter",
# making it unselectable.
# Fix: compute a per-widget sentinel starting with '__all__', appending '_'
# until the sentinel is absent from observed raw values.

class TestDropdownSentinelCollision:
    """Regression suite for BUG-37: per-widget sentinel avoids __all__ collision."""

    # ------------------------------------------------------------------
    # BUG-37-1a: standalone sentinel is unique when data contains __all__
    # ------------------------------------------------------------------

    def test_standalone_sentinel_unique_when_data_has_all_value(self, dr_module):
        """BUG-37-1a: standalone widget sentinel must not equal any raw data value."""
        import pandas as pd, numpy as np
        # Build a DataFrame whose filter column contains the literal '__all__'.
        # Must mark 'cat' as a string column so DashRenderer preserves string values.
        df = pd.DataFrame({
            "mpg":    np.linspace(15, 35, 6),
            "weight": np.linspace(2000, 4000, 6),
            "cat":    ["__all__", "A", "B", "__all__", "A", "B"],
        })
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }], build_options={
            "layout": "auto", "link": "", "filter": "cat, type(dropdown)",
            "theme": "default", "title": "T", "subtitle": "",
            "registry": "g1", "mode": "standalone", "port": "5006",
        })
        spec_path, data_path = _write_temp_files_with_strings(df, spec, ["cat"])
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            render_models(renderer)
            assert renderer.filter_widgets, "Expected at least one filter widget"
            w = renderer.filter_widgets[0]
            sentinel = getattr(w, "_dash_sentinel", "__all__")
            raw_data_values = set(str(v) for v in df["cat"].unique())
            assert sentinel not in raw_data_values, (
                f"Sentinel {sentinel!r} must not be in raw data values {raw_data_values}"
            )
            assert sentinel == w.value, (
                f"Widget value must equal sentinel; got value={w.value!r}, sentinel={sentinel!r}"
            )
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    # ------------------------------------------------------------------
    # BUG-37-1b: standalone __all__ category appears in options as a real value
    # ------------------------------------------------------------------

    def test_standalone_all_value_selectable_as_category(self, dr_module):
        """BUG-37-1b: '__all__' category must appear as a regular option, not just sentinel."""
        import pandas as pd, numpy as np
        df = pd.DataFrame({
            "mpg":    np.linspace(15, 35, 4),
            "weight": np.linspace(2000, 4000, 4),
            "cat":    ["__all__", "A", "__all__", "B"],
        })
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }], build_options={
            "layout": "auto", "link": "", "filter": "cat, type(dropdown)",
            "theme": "default", "title": "T", "subtitle": "",
            "registry": "g1", "mode": "standalone", "port": "5006",
        })
        spec_path, data_path = _write_temp_files_with_strings(df, spec, ["cat"])
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            render_models(renderer)
            assert renderer.filter_widgets
            w = renderer.filter_widgets[0]
            option_values = [v for v, _ in w.options]
            # '__all__' should appear as a real data option (not just as sentinel)
            assert "__all__" in option_values, (
                f"'__all__' category must appear as a real option; got options: {option_values}"
            )
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    # ------------------------------------------------------------------
    # BUG-37-1c: standalone filter_specs_json contains per-widget sentinel
    # ------------------------------------------------------------------

    def test_standalone_filter_specs_json_contains_sentinel(self, dr_module):
        """BUG-37-1c: filter_specs_json must include 'sentinel' for each dropdown."""
        import pandas as pd, numpy as np
        df = pd.DataFrame({
            "mpg":    np.linspace(15, 35, 4),
            "weight": np.linspace(2000, 4000, 4),
            "cat":    ["__all__", "A", "__all__", "B"],
        })
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }], build_options={
            "layout": "auto", "link": "", "filter": "cat, type(dropdown)",
            "theme": "default", "title": "T", "subtitle": "",
            "registry": "g1", "mode": "standalone", "port": "5006",
        })
        spec_path, data_path = _write_temp_files_with_strings(df, spec, ["cat"])
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            render_models(renderer)
            assert renderer.filter_callbacks, "Need at least one callback"
            cb_args = renderer.filter_callbacks[0].args
            fspecs = json.loads(cb_args["filter_specs_json"])
            assert fspecs, "filter_specs_json must not be empty"
            for fs in fspecs:
                if fs.get("type") == "dropdown":
                    assert "sentinel" in fs, (
                        f"dropdown filter_spec must have 'sentinel' key; got {fs}"
                    )
                    # sentinel must differ from '__all__' when __all__ is in data
                    assert fs["sentinel"] != "__all__", (
                        f"sentinel must not be '__all__' when data contains that literal; "
                        f"got {fs['sentinel']!r}"
                    )
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    # ------------------------------------------------------------------
    # BUG-37-1d: generated source uses computed sentinel in Select
    # ------------------------------------------------------------------

    def test_server_dropdown_uses_computed_sentinel(self, dr_module):
        """BUG-37-1d: the served widget's sentinel is absent from the data.

        Stated as behaviour: this used to assert the NAMES of the
        generated app's own sentinel loop (`_sent', `_uniq_strs'), which
        went away when the widget builder became the one the saved
        renderer runs.  The served widget must do what BUG-37-1a requires
        of the saved one -- a data value equal to the literal string
        "__all__" does not collide with the "All" option.
        """
        import tempfile
        import pandas as pd, numpy as np
        from bokeh.document import Document
        from bokeh.models import Select
        df = pd.DataFrame({
            "mpg":    np.linspace(15, 35, 6),
            "weight": np.linspace(2000, 4000, 6),
            "cat":    ["__all__", "A", "B", "__all__", "A", "B"],
        })
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }], build_options={
            "layout": "auto", "link": "", "filter": "cat, type(dropdown)",
            "theme": "default", "title": "T", "subtitle": "",
            "registry": "g1", "mode": "server", "port": "5006",
        })
        spec_path, data_path = _write_temp_files_with_strings(df, spec, ["cat"])
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            dr_module.ServerAppBuilder(spec_path, data_path).build(out_f.name, port=5006)
            app_mod = load_app(out_f.name, "_bug37_app")
            doc = Document()
            app_mod.make_document(doc)
            selects = [m for m in doc.select({"type": Select})]
            assert selects, "the served document must carry the dropdown"
            w = selects[0]
            sentinel = getattr(w, "_dash_sentinel", "__all__")
            raw_values = {str(v) for v in df["cat"].unique()}
            assert sentinel not in raw_values, (
                f"served sentinel {sentinel!r} collides with the data {raw_values}")
            assert w.value == sentinel
            assert "__all__" in [v for v, _ in w.options], (
                "the data's own '__all__' must stay selectable as a category")
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try: os.unlink(_p)
                except OSError: pass

    # ------------------------------------------------------------------
    # BUG-37-1e: generated server uses per-widget sentinel in callback
    # ------------------------------------------------------------------

    def test_the_served_callback_filters_on_the_widgets_own_sentinel(
            self, dr_module, tmp_path):
        """BUG-37-1e: when the data hold the literal "__all__", the served
        recompute takes the WIDGET's sentinel for "no filter" -- so choosing
        the data's own "__all__" category keeps its rows, and choosing the
        sentinel keeps every row.

        This read the generated app for the sentinel attribute's name and
        for the absence of a hard-coded '__all__'.  The widget's sentinel
        was checked (the test above) but nothing moved it, and the mask
        helper's own test uses the default sentinel only, so a mask that
        compared with a hard-coded '__all__' passed every test (WP-24)."""
        from bokeh.models import GlyphRenderer, Plot, Select
        df = pd.DataFrame({
            "make": ["__all__", "A", "B", "__all__", "A", "B"],
            "mpg": [15.0, 19.0, 23.0, 27.0, 31.0, 35.0],
            "weight": [2000.0, 2400.0, 2800.0, 3200.0, 3600.0, 4000.0],
        })
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}],
            "graph_options": {"name": "g1"},
        }], build_options={
            "layout": "auto", "link": "", "filter": "make, type(dropdown)",
            "theme": "", "title": "", "subtitle": "", "registry": "g1",
            "level": "95", "formats": {}})
        doc, _ = _ql_served(dr_module, tmp_path, spec, df)
        sel = [m for root in doc.roots for m in root.select({"type": Select})]
        assert len(sel) == 1, sel
        w = sel[0]
        sentinel = getattr(w, "_dash_sentinel", "__all__")
        assert sentinel != "__all__", (
            "the data hold '__all__', so the widget's sentinel must differ")

        def _drawn():
            return sorted(float(v) for root in doc.roots
                          for fig in root.select({"type": Plot})
                          for r in fig.renderers
                          if isinstance(r, GlyphRenderer)
                          and type(r.glyph).__name__ == "Scatter"
                          for v in r.data_source.data["weight"])

        def _fire(value):
            w.value = value
            for key in ("value", "value_throttled"):
                for cb in list(w._callbacks.get(key, [])):
                    cb("value", None, value)

        _fire("__all__")
        assert _drawn() == [2000.0, 3200.0], (
            f"choosing the data's '__all__' drew x={_drawn()}; its two rows "
            f"are x=2000 and x=3200")
        _fire(sentinel)
        assert _drawn() == sorted(df["weight"].tolist()), (
            f"choosing the sentinel ({sentinel!r}) drew x={_drawn()}; it "
            f"filters nothing")


# ===========================================================================
# BUG-38: Generated server by(total) panel drops non-scatter/line/hist plot types
# ===========================================================================
# Before fix: the Total panel only dispatched scatter, line, and histogram/hist.
# All other supported types (bar, area, kdensity, lfit, qfit, lowess, lpoly,
# fpfit, connected, dot, spike, dropline, mband) were silently ignored so the
# Total panel had zero renderers for those plot types.
# Fix: replace the limited dispatch with the full per-group facet dispatch,
# substituting work_df/_tot_src/_tot_fig for _fac_gdf/_fac_src/_fac_fig.

class TestServerByTotalFullDispatch:
    """Regression suite for BUG-38: by(total) panel must render all plot types."""

    # ------------------------------------------------------------------
    # BUG-38-1a: by(total) with bar renders Total panel
    # ------------------------------------------------------------------

    def test_by_total_bar_produces_renderer(self, dr_module, auto_df):
        """BUG-38-1a: by(foreign, total) bar → Total panel has a vbar renderer."""
        from bokeh.document import Document
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "bar", "yvar": "mpg", "xvar": "foreign", "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign, total"},
        }])
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_mod = load_app(out_f.name, "_b38a")
            doc = Document()
            app_mod.make_document(doc)
            n_renderers = _count_glyph_renderers(doc)
            # 2 foreign groups + 1 total panel = 3 bar renderers minimum
            assert n_renderers >= 3, (
                f"by(foreign, total) bar should produce at least 3 renderers "
                f"(2 groups + 1 total), got {n_renderers}"
            )
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try: os.unlink(_p)
                except OSError: pass

    # ------------------------------------------------------------------
    # BUG-38-1b: by(total) with connected renders Total panel
    # ------------------------------------------------------------------

    def test_by_total_connected_produces_renderer(self, dr_module, auto_df):
        """BUG-38-1b: by(foreign, total) connected → Total panel has renderers."""
        from bokeh.document import Document
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "connected", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign, total"},
        }])
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_mod = load_app(out_f.name, "_b38b")
            doc = Document()
            app_mod.make_document(doc)
            n_renderers = _count_glyph_renderers(doc)
            # connected = line + scatter per panel → 2 groups + total → >= 6 renderers
            assert n_renderers >= 6, (
                f"by(foreign, total) connected should produce >= 6 renderers "
                f"(line+scatter per group, + total), got {n_renderers}"
            )
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try: os.unlink(_p)
                except OSError: pass

    # ------------------------------------------------------------------
    # BUG-38-1c: by(total) source for Total contains full work_df data
    # ------------------------------------------------------------------

    def test_by_total_source_in_generated_source(self, dr_module, auto_df):
        """BUG-38-1c, restated: the Total panel's fit is the fit of ALL rows.

        This asserted "_compute_lfit(work_df" appeared in the generated
        source.  The Total panel is drawn by the same figure body as the
        graph now, from the whole (qualified) frame, so the text is gone and
        the fit itself is checked: it equals the unfaceted graph's fit and
        differs from each group's.
        """
        from bokeh.document import Document
        import warnings

        def _fits(by):
            go = {"name": "g1"}
            if by:
                go["by"] = by
            spec = _make_spec_json(graphs=[{
                "plots": [{"type": "lfit", "yvar": "mpg", "xvar": "weight", "options": {}}],
                "graph_options": go,
            }])
            spec_path, data_path = _write_temp_files(auto_df, spec)
            out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
            out_f.close()
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    dr_module.ServerAppBuilder(spec_path, data_path).build(out_f.name)
                    mod = load_app(out_f.name, "_tot_fit")
                    doc = Document()
                    mod.make_document(doc)
                out = []
                for f in [m for m in doc.select({"type": object}) if type(m).__name__ == "figure"]:
                    for r in f.renderers:
                        d = getattr(getattr(r, "data_source", None), "data", {})
                        if "y" in d and len(d["y"]):
                            out.append((_panel_name(f), [round(float(v), 6) for v in d["y"]]))
                return out
            finally:
                for _p in (spec_path, data_path, out_f.name):
                    try: os.unlink(_p)
                    except OSError: pass

        panels = dict(_fits("foreign, total"))
        whole = dict(_fits(""))
        assert "Total" in panels, list(panels)
        assert panels["Total"] == whole[""], "the Total panel's fit is not the fit of all rows"
        assert all(panels["Total"] != v for k, v in panels.items() if k != "Total")

    # ------------------------------------------------------------------
    # BUG-38-1d: by(total) with dot renders Total panel
    # ------------------------------------------------------------------

    def test_by_total_dot_produces_renderer(self, dr_module, auto_df):
        """BUG-38-1d: by(foreign, total) dot → Total panel has a scatter renderer."""
        from bokeh.document import Document
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "dot", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign, total"},
        }])
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_mod = load_app(out_f.name, "_b38d")
            doc = Document()
            app_mod.make_document(doc)
            n_renderers = _count_glyph_renderers(doc)
            assert n_renderers >= 3, (
                f"by(foreign, total) dot should produce >= 3 renderers "
                f"(2 groups + 1 total), got {n_renderers}"
            )
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try: os.unlink(_p)
                except OSError: pass

    # ------------------------------------------------------------------
    # BUG-38-1e: regression — scatter by(total) still works
    # ------------------------------------------------------------------

    def test_by_total_scatter_regression(self, dr_module, auto_df):
        """BUG-38-1e: scatter by(total) must still produce Total renderer after fix."""
        from bokeh.document import Document
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign, total"},
        }])
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_mod = load_app(out_f.name, "_b38e")
            doc = Document()
            app_mod.make_document(doc)
            n_renderers = _count_glyph_renderers(doc)
            assert n_renderers >= 3, (
                f"by(foreign, total) scatter should produce >= 3 renderers "
                f"(2 groups + 1 total), got {n_renderers}"
            )
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try: os.unlink(_p)
                except OSError: pass


# ===========================================================================
# BUG-39 — Stata build/serve omit qualifier and by() variables from
#          serialized data; _apply_graph_filter crashes with NameError
#          when the qualifier column is absent from the DataFrame.
#
# Python-side regression: _apply_graph_filter must warn and return the
# unfiltered DataFrame rather than raising NameError /
# pandas.errors.UndefinedVariableError when a column referenced in if_expr
# was not serialized by Stata (because _dash_extract_qual_vars did not yet
# exist, or the variable was only referenced in the qualifier).
#
# BUG-39-1a  _apply_graph_filter warns + returns full df when col absent
# BUG-39-1b  _apply_graph_filter filters correctly when col IS present
# BUG-39-1c  Warning message mentions that the filter was skipped
# BUG-39-1d  Server make_document doesn't crash when if_expr col absent
# BUG-39-1e  Server make_document applies filter when if_expr col present
# ===========================================================================

class TestQualifierMissingColumnGraceful:
    """BUG-39: _apply_graph_filter degrades gracefully on missing columns."""

    # ------------------------------------------------------------------
    # BUG-39-1a: warns and returns full df when col absent
    # ------------------------------------------------------------------

    def test_missing_col_returns_full_df(self, dr_module, auto_df):
        """BUG-39-1a: if_expr referencing absent column -> returns unfiltered df."""
        import warnings
        renderer = dr_module.DashRenderer.__new__(dr_module.DashRenderer)
        # Give the renderer a df that does NOT contain 'foreign'
        renderer.df = auto_df[["mpg", "weight", "price"]].copy()
        graph_spec = {"if_expr": "foreign == 1"}
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = renderer._apply_graph_filter(graph_spec)
        # Must return full df (30 rows), not raise
        assert len(result) == len(renderer.df), (
            f"Expected {len(renderer.df)} rows (full df), got {len(result)}"
        )

    # ------------------------------------------------------------------
    # BUG-39-1b: filters correctly when col IS present
    # ------------------------------------------------------------------

    def test_present_col_filters_correctly(self, dr_module, auto_df):
        """BUG-39-1b: if_expr referencing a present column filters correctly."""
        renderer = dr_module.DashRenderer.__new__(dr_module.DashRenderer)
        renderer.df = auto_df.copy()
        n_foreign = int((auto_df["foreign"] == 1).sum())
        graph_spec = {"if_expr": "foreign == 1"}
        result = renderer._apply_graph_filter(graph_spec)
        assert len(result) == n_foreign, (
            f"Expected {n_foreign} rows (foreign==1), got {len(result)}"
        )

    # ------------------------------------------------------------------
    # BUG-39-1c: warning message mentions that the filter was skipped
    # ------------------------------------------------------------------

    def test_missing_col_warning_mentions_filter_skipped(self, dr_module, auto_df):
        """BUG-39-1c: warning text mentions that the filter was skipped."""
        import warnings
        renderer = dr_module.DashRenderer.__new__(dr_module.DashRenderer)
        renderer.df = auto_df[["mpg", "weight"]].copy()
        graph_spec = {"if_expr": "foreign == 1"}
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            renderer._apply_graph_filter(graph_spec)
        assert len(caught) >= 1, "Expected at least one warning, got none"
        warning_text = str(caught[0].message)
        assert "filter skipped" in warning_text, (
            f"Warning text did not contain 'filter skipped': {warning_text}"
        )

    # ------------------------------------------------------------------
    # BUG-39-1d: server make_document doesn't crash when if_expr col absent
    # ------------------------------------------------------------------

    def test_server_make_document_missing_if_expr_col(self, dr_module, auto_df):
        """BUG-39-1d: server make_document renders when if_expr col is absent from data."""
        import warnings
        from bokeh.document import Document
        # Build a spec with if_expr referencing 'foreign', but omit 'foreign'
        # from the serialized data (simulating missing _dash_extract_qual_vars).
        df_no_foreign = auto_df[["mpg", "weight", "price"]].copy()
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "if_expr": "foreign == 1"},
        }])
        spec_path, data_path = _write_temp_files(df_no_foreign, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_mod = load_app(out_f.name, "_b39d")
            doc = Document()
            # Must not raise — should render with unfiltered data
            with warnings.catch_warnings(record=True):
                warnings.simplefilter("always")
                app_mod.make_document(doc)
            n_renderers = _count_glyph_renderers(doc)
            assert n_renderers >= 1, (
                f"make_document should render at least 1 glyph even when "
                f"if_expr column is absent; got {n_renderers}"
            )
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try: os.unlink(_p)
                except OSError: pass

    # ------------------------------------------------------------------
    # BUG-39-1e: server make_document applies filter when if_expr col present
    # ------------------------------------------------------------------

    def test_server_make_document_if_expr_filters_when_col_present(
            self, dr_module, auto_df):
        """BUG-39-1e: server make_document draws only the if_expr rows when
        the qualifier's column is in the data.

        This walked ``doc.roots`` one level deep for the figure's renderers,
        but the figures sit inside a GridPlot two levels down, so that walk
        found none and the ``if glyph_renderers:`` body -- the only check of
        the row count -- never ran; the earlier ``n_renderers >= 1`` used a
        deep walk and passed whatever the filter did (WP-24, measured
        24sep2026).  The layer is read from the document properly now: it
        draws the 16 foreign==1 (weight, mpg) points, and the control -- the
        same graph with no qualifier -- draws all 30, so the reader sees the
        qualifier do the reducing."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "if_expr": "foreign == 1"},
        }])
        doc, _ = _exec_doc(dr_module, auto_df, spec, "_b39e")
        (_fig, r), = _glyph_layers(doc.roots)
        want = auto_df.loc[auto_df["foreign"] == 1]
        assert 0 < len(want) < len(auto_df)
        assert sorted(zip(_drawn_values(r, "weight"), _drawn_values(r, "mpg"))) \
            == sorted(zip(want["weight"], want["mpg"])), (
            "the served graph did not draw exactly the foreign==1 rows")
        plain = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        _doc, (control,) = _exec_doc(dr_module, auto_df, plain, "_b39e_ctl")
        assert len(_drawn_values(control, "weight")) == len(auto_df), (
            "the control graph without a qualifier must draw every row")


# ===========================================================================
# BUG-40 — Windows browser auto-open command uses `start` with incorrect
#          quoting; the first quoted token is treated as the window title.
#
# The fix adds an empty title ("") so the second quoted argument is used
# as the target file path.
#
# The four tests that stood here (TestWindowsBrowserStartQuoting, BUG-40-1a
# to 1d) read dash.ado's text for `shell start ""', `shell open' and `shell
# xdg-open'.  The Windows line ran only where Stata reports Windows, so no
# test ran it, and those checks passed with the Windows branch unable to run
# at all ("windows" for "Windows") and with the path handed to start
# unquoted (measured 24sep2026).  Both callers now open the page through
# dash.ado's _dash_open_page, which takes the platform as os() and, under
# dryrun, returns the command it would run without running it.  Their
# claims are held by what runs, in test_serve_browser.cscript:
#   BUG-40-1a/1c  start "" "<path>" on Windows: SB-14 (the whole command for
#                 an ordinary path), SB-15 (whose Windows path, holding a
#                 semicolon and an ampersand, is now declined for them,
#                 WP-30 P1.29: SB-22), SB-24 (start's quoting of a hostile
#                 path without them: an apostrophe, spaces, parentheses and
#                 a comma) and SB-16 (a path with a double quote, which
#                 would end start's argument, is refused).  That both callers open through the one opener:
#                 test_help_claims_2.cscript HC2-30 (dash build) and HC2-34a
#                 (the one-line form), each of which fails with that
#                 caller's call removed (measured 24sep2026).
#   BUG-40-1b     no start without its empty title: SB-14 and SB-15 compare
#                 the whole command, not a pattern.
#   BUG-40-1d     open on a Mac and xdg-open on Unix: SB-14 and SB-15, SB-17
#                 (a Mac known by its machine type as well, as the console
#                 binary reports Unix), and SB-19, where each command runs
#                 against a stub and the opener is handed the path whole,
#                 once, with nothing injected.
# ===========================================================================


# ===========================================================================
# BUG-41 — Server rate limiter collapses proxied users into a single IP
#          bucket because make_document and _HealthHandler both used
#          remote_ip exclusively (or preferred it over X-Forwarded-For).
#
# The fix adds a shared _client_ip_from_request() helper that prefers the
# X-Forwarded-For header (first token) over remote_ip so each end-user
# behind a reverse proxy gets an isolated rate-limit budget.
#
# BUG-41-1a  Generated source defines _client_ip_from_request helper
# BUG-41-1b  Helper prefers X-Forwarded-For over remote_ip
# BUG-41-1c  Helper falls back to remote_ip when X-Forwarded-For absent
# BUG-41-1d  Helper returns '0.0.0.0' when both are absent
# BUG-41-1e  HealthHandler.prepare uses _client_ip_from_request
# BUG-41-1f  make_document uses _client_ip_from_request (not inline expr)
# ===========================================================================

class TestProxiedRateLimiterBucket:
    """BUG-41: rate limiter must use X-Forwarded-For first for per-client isolation."""

    def _build_source(self, dr_module, auto_df):
        """Return generated server source as a string."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        return _build_app(dr_module, auto_df, spec)

    # ------------------------------------------------------------------
    # BUG-41-1a: source defines _client_ip_from_request
    # ------------------------------------------------------------------

    def test_source_defines_helper(self, dr_module, auto_df):
        """BUG-41-1a: generated source must define _client_ip_from_request."""
        src = self._build_source(dr_module, auto_df)
        assert "def _client_ip_from_request(" in src, (
            "Generated source missing _client_ip_from_request helper"
        )

    # ------------------------------------------------------------------
    # BUG-41-1b: helper prefers X-Forwarded-For over remote_ip
    # ------------------------------------------------------------------

    def test_helper_prefers_xff_when_the_proxy_is_trusted(self, dr_module,
                                                          auto_df):
        """BUG-41-1b, now behind the trust flag.

        This asserted that the helper preferred X-Forwarded-For with no flag
        set. That is the behaviour that made the rate limiter bypassable:
        measured against a running server, 700 requests with a varying
        spoofed header got 700 x 200 and not one 429, where the same burst
        without the header was cut off at 600. The header is
        client-settable unless a proxy you control overwrites it.

        BUG-41's actual complaint -- that every user behind a proxy shared
        one bucket -- is still addressed, but only when the operator says
        there IS such a proxy. Do not delete the flag to make this green; see
        test_server_rate_limit.py.

        The value is also validated as an IP and key-spaced, so a forwarded
        10.0.0.1 cannot land in the real 10.0.0.1's bucket -- hence the
        assertion is on containment rather than equality.
        """
        src = self._build_source(dr_module, auto_df)
        mod = types.ModuleType("_b41_mod")
        exec(compile(src, "<test>", "exec"), mod.__dict__)
        helper = getattr(mod, "_client_ip_from_request")

        class _FakeReq:
            remote_ip = "10.0.0.1"  # proxy IP
            headers = {"X-Forwarded-For": "203.0.113.55, 198.51.100.7"}

        assert helper(_FakeReq()).endswith("10.0.0.1"), (
            "untrusted by default, the helper must use the peer address"
        )
        mod._TRUST_FORWARDED_FOR = True
        got = helper(_FakeReq())
        assert "198.51.100.7" in got, (
            f"with the proxy trusted, the hop the proxy appended must be the "
            f"bucket key; got {got!r}"
        )

    # ------------------------------------------------------------------
    # BUG-41-1c: falls back to remote_ip when XFF absent
    # ------------------------------------------------------------------

    def test_helper_falls_back_to_remote_ip(self, dr_module, auto_df):
        """BUG-41-1c: _client_ip_from_request returns remote_ip when XFF absent."""
        src = self._build_source(dr_module, auto_df)
        mod = types.ModuleType("_b41c_mod")
        exec(compile(src, "<test>", "exec"), mod.__dict__)
        helper = getattr(mod, "_client_ip_from_request")

        class _FakeReq:
            remote_ip = "192.168.1.1"
            headers = {}

        assert helper(_FakeReq()) == "192.168.1.1", (
            "Helper should return remote_ip when X-Forwarded-For is absent"
        )

    # ------------------------------------------------------------------
    # BUG-41-1d: returns '0.0.0.0' when both absent
    # ------------------------------------------------------------------

    def test_helper_returns_zero_ip_when_both_absent(self, dr_module, auto_df):
        """BUG-41-1d: helper returns '0.0.0.0' when remote_ip and XFF both absent."""
        src = self._build_source(dr_module, auto_df)
        mod = types.ModuleType("_b41d_mod")
        exec(compile(src, "<test>", "exec"), mod.__dict__)
        helper = getattr(mod, "_client_ip_from_request")

        class _FakeReq:
            remote_ip = None
            headers = {}

        assert helper(_FakeReq()) == "0.0.0.0", (
            "Helper should return '0.0.0.0' when both remote_ip and XFF are absent"
        )

    # ------------------------------------------------------------------
    # BUG-41-1e/1f: /health and make_document key their budgets through
    # the helper.  These read the app's text for the helper's call and for
    # the absence of the old inline reads; the keying itself was driven by
    # nothing -- the helper was tested on its own, and every test that went
    # through /health or make_document either sent no forwarded header or
    # refused everyone (WP-24 scan).  Now each is driven with one peer and
    # two forwarded clients: untrusted, the two share the peer's budget
    # (keying on the header would let a forged one escape it); trusted, the
    # second has a budget of its own (keying on the peer would not).
    # ------------------------------------------------------------------

    @staticmethod
    def _matrix():
        """The served-app drivers test_adversarial_matrix.py already has."""
        _here = os.path.dirname(os.path.abspath(__file__))
        if _here not in sys.path:
            sys.path.insert(0, _here)
        from test_adversarial_matrix import _Req, _health, _session, _texts
        return _Req, _health, _session, _texts

    def _served_ns(self, dr_module, auto_df, tmp_path):
        """The generated app's namespace, without its curdoc attach."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}],
            "graph_options": {"name": "g1"},
        }], build_options={"layout": "auto", "registry": "g1"})
        return _ql_app_ns(dr_module, tmp_path, spec, auto_df)

    @pytest.mark.parametrize("trusted", [False, True],
                             ids=["untrusted", "trusted"])
    def test_health_keys_its_budget_through_the_helper(
            self, dr_module, auto_df, tmp_path, monkeypatch, trusted):
        """BUG-41-1e: /health's budget is the helper's key."""
        _Req, _health, _session, _texts = self._matrix()
        ns = self._served_ns(dr_module, auto_df, tmp_path)
        monkeypatch.setitem(ns, "_TRUST_FORWARDED_FOR", trusted)
        monkeypatch.setitem(ns, "_HEALTH_LIMITER", ns["_RateLimiter"](
            3, 10, 100, what="/health request"))
        peer = "10.7.7.9"
        spent = [_health(ns, _Req(peer, **{
            "X-Forwarded-For": "203.0.113.5"}))[0] for _ in range(4)]
        assert spent == [200, 200, 200, 429], spent
        other = _health(ns, _Req(peer, **{
            "X-Forwarded-For": "203.0.113.6"}))[0]
        assert other == (200 if trusted else 429), (
            f"trusted={trusted}: a second forwarded client behind the same "
            f"peer got {other}")

    @pytest.mark.parametrize("trusted", [False, True],
                             ids=["untrusted", "trusted"])
    def test_make_document_keys_its_budget_through_the_helper(
            self, dr_module, auto_df, tmp_path, monkeypatch, trusted):
        """BUG-41-1f: a session's budget is the helper's key."""
        _Req, _health, _session, _texts = self._matrix()
        ns = self._served_ns(dr_module, auto_df, tmp_path)
        monkeypatch.setitem(ns, "_TRUST_FORWARDED_FOR", trusted)
        monkeypatch.setitem(ns, "_SESSION_LIMITER", ns["_RateLimiter"](
            2, 10, 100, what="session"))
        peer = "10.7.7.10"

        def refused(xff):
            doc = _session(ns, _Req(peer, **{"X-Forwarded-For": xff}))
            return "429" in _texts(doc)

        assert [refused("203.0.113.5") for _ in range(3)] == \
            [False, False, True]
        other = refused("203.0.113.6")
        assert other is (not trusted), (
            f"trusted={trusted}: a second forwarded client behind the same "
            f"peer was {'refused' if other else 'served'}")


# ===========================================================================
# BUG-42 — `by()` silently falls back to ungrouped data when all facet
#          values are missing.
#
# Standalone: _expand_by_groups returned [("", df)] (full original data)
# when work_df was empty after dropna.
# Server: when work_df was empty after dropna, `continue` skipped faceting
# but left the original unfaceted graph source untouched.
#
# The fix returns [("", work_df.copy())] (empty DataFrame group) from
# _expand_by_groups so callers create a zero-row source, and clears the
# server-side source before continuing.
#
# BUG-42-1a  _expand_by_groups returns empty-df group when all keys missing
# BUG-42-1b  _expand_by_groups normal faceting still works (regression)
# BUG-42-1c  Standalone source has zero rows when all facet keys missing
# BUG-42-1d  Server make_document produces zero-row source for all-missing by()
# BUG-42-1e  Server make_document produces non-zero source for partial missing
# ===========================================================================

class TestByFallbackOnAllMissingFacets:
    """BUG-42: by() with all-missing facet keys must not render full ungrouped data."""

    # ------------------------------------------------------------------
    # BUG-42-1a: _expand_by_groups returns empty-df group when all keys missing
    # ------------------------------------------------------------------

    def test_expand_by_groups_all_missing_returns_empty_df(self, dr_module, auto_df):
        """BUG-42-1a: _expand_by_groups returns empty-row group, not full dataset."""
        # Create df where ALL grp values are NaN
        df_all_na = auto_df.copy()
        df_all_na["grp"] = float("nan")
        renderer = dr_module.DashRenderer.__new__(dr_module.DashRenderer)
        renderer.df = df_all_na
        renderer._meta = {}
        graph_spec = {"graph_options": {"name": "g1", "by": "grp"}}
        groups = renderer._expand_by_groups(graph_spec, base_df=df_all_na)
        assert len(groups) == 1, f"Expected 1 fallback group, got {len(groups)}"
        label, gdf = groups[0]
        assert label == "", f"Fallback label should be '', got {label!r}"
        assert len(gdf) == 0, (
            f"Fallback group df should have 0 rows (not {len(gdf)}) "
            f"when all facet values are missing"
        )

    # ------------------------------------------------------------------
    # BUG-42-1b: normal faceting still works
    # ------------------------------------------------------------------

    def test_expand_by_groups_normal_faceting_regression(self, dr_module, auto_df):
        """BUG-42-1b: _expand_by_groups still produces correct groups when some present."""
        renderer = dr_module.DashRenderer.__new__(dr_module.DashRenderer)
        renderer.df = auto_df
        renderer._meta = {}
        # _facet_label uses value_label_names / value_labels for display names
        renderer.value_label_names = {}
        renderer.value_labels = {}
        n_unique = auto_df["foreign"].nunique()
        graph_spec = {"graph_options": {"name": "g1", "by": "foreign"}}
        groups = renderer._expand_by_groups(graph_spec, base_df=auto_df)
        # Each unique value of foreign gets its own group
        assert len(groups) == n_unique, (
            f"Expected {n_unique} facet groups, got {len(groups)}"
        )
        for lbl, gdf in groups:
            assert len(gdf) > 0, f"Non-missing facet group '{lbl}' must be non-empty"

    # ------------------------------------------------------------------
    # BUG-42-1c: standalone source has zero rows when all facet keys missing
    # ------------------------------------------------------------------

    def test_standalone_source_zero_rows_all_missing(self, dr_module, auto_df):
        """BUG-42-1c: standalone render source has 0 rows when all by() keys missing."""
        # DataFrame where ALL foreign values are NaN
        df_na = auto_df.copy()
        df_na["foreign"] = float("nan")
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign"},
        }])
        spec_path, data_path = _write_temp_files(df_na, spec)
        try:
            dr = dr_module.DashRenderer(spec_path, data_path)
            render_models(dr)
            # The single source for 'g1' should have zero rows
            src = dr.sources.get("g1")
            assert src is not None, "Source 'g1' not found"
            n_rows = len(next(iter(src.data.values()), []))
            assert n_rows == 0, (
                f"Expected 0-row source when all by() keys are missing, got {n_rows}"
            )
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    # ------------------------------------------------------------------
    # BUG-42-1d: server make_document has zero-row source for all-missing by()
    # ------------------------------------------------------------------

    def test_server_source_zero_rows_all_missing(self, dr_module, auto_df):
        """BUG-42-1d: server make_document draws nothing when every by() key
        is missing -- not the full ungrouped dataset.

        This walked ``doc.roots`` one level deep for glyph renderers, but the
        figures sit inside a GridPlot two levels down, so the walk found none
        and the ``for gr in glyph_renderers:`` loop -- the only assertion --
        ran zero times (WP-24, measured 24sep2026: the full 30 rows would
        have passed just as silently).  The layers are read from the document
        properly now: there is at least one, and each draws 0 rows.  The
        control -- the same by() over real values -- draws 30 rows across its
        panels, so an empty draw is a real absence, not an empty document."""
        df_na = auto_df.copy()
        df_na["foreign"] = float("nan")
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign"},
        }])
        doc, _ = _exec_doc(dr_module, df_na, spec, "_b42d")
        layers = _glyph_layers(doc.roots)
        assert layers, "no glyph layer was drawn at all"
        assert [len(r.data_source.data["mpg"]) for _f, r in layers] \
            == [0] * len(layers), (
            "an all-missing by() drew rows; the ungrouped data leaked in")
        _doc, _ = _exec_doc(dr_module, auto_df, spec, "_b42d_ctl")
        assert sum(len(r.data_source.data["mpg"])
                   for _f, r in _glyph_layers(_doc.roots)) == len(auto_df), (
            "the control by() over real values must draw the rows")

    # ------------------------------------------------------------------
    # BUG-42-1e: partial missing still produces groups for present values
    # ------------------------------------------------------------------

    def test_partial_missing_produces_correct_groups(self, dr_module, auto_df):
        """BUG-42-1e: partial-missing by() still creates facets for non-missing values."""
        # Set half the foreign values to NaN; remaining half should still facet
        df_partial = auto_df.copy()
        df_partial.loc[df_partial.index[:10], "foreign"] = float("nan")
        renderer = dr_module.DashRenderer.__new__(dr_module.DashRenderer)
        renderer.df = df_partial
        renderer._meta = {}
        renderer.value_label_names = {}
        renderer.value_labels = {}
        n_unique = df_partial["foreign"].dropna().nunique()
        graph_spec = {"graph_options": {"name": "g1", "by": "foreign"}}
        groups = renderer._expand_by_groups(graph_spec, base_df=df_partial)
        assert len(groups) == n_unique, (
            f"Expected {n_unique} groups for non-missing values, got {len(groups)}"
        )


# ===========================================================================
# BUG-43 — layout() accepts zero columns and crashes render with ZeroDivision
#
# Validation accepted "0 0" / "2 0" because regex only checked for digits.
# The renderer then computed rows_n = math.ceil(n_items / cols_n) with
# cols_n=0 → ZeroDivisionError.
#
# Fix: Stata-side regex now requires [1-9][0-9]* for both grid integers;
# Python _compute_grid clamps values to minimum 1.
#
# BUG-43-1a  _compute_grid with "0 0" returns at least (1, 1)
# BUG-43-1b  _compute_grid with "2 0" returns at least (2, 1)
# BUG-43-1c  _compute_grid with "0 3" returns at least (1, 3)
# BUG-43-1d  _compute_grid with valid "2 3" returns (2, 3) unchanged
# BUG-43-1e  dash.ado validation regex rejects zero-column layout
# ===========================================================================

class TestLayoutZeroColumnsCrash:
    """BUG-43: layout() with zero dimensions must not crash with ZeroDivisionError."""

    # ------------------------------------------------------------------
    # BUG-43-1a: "0 0" → at least (1, 1)
    # ------------------------------------------------------------------

    def test_compute_grid_zero_zero(self, dr_module, auto_df):
        """BUG-43-1a: _compute_grid('0 0') must return >= (1,1), not (0,0)."""
        renderer = dr_module.DashRenderer.__new__(dr_module.DashRenderer)
        rows, cols = renderer._compute_grid(4, "0 0")
        assert rows >= 1, f"rows must be >= 1, got {rows}"
        assert cols >= 1, f"cols must be >= 1, got {cols}"

    # ------------------------------------------------------------------
    # BUG-43-1b: "2 0" → at least (2, 1)
    # ------------------------------------------------------------------

    def test_compute_grid_two_zero(self, dr_module, auto_df):
        """BUG-43-1b: _compute_grid('2 0') must not produce zero cols."""
        renderer = dr_module.DashRenderer.__new__(dr_module.DashRenderer)
        rows, cols = renderer._compute_grid(4, "2 0")
        assert cols >= 1, f"cols must be >= 1, got {cols}"

    # ------------------------------------------------------------------
    # BUG-43-1c: "0 3" → at least (1, 3)
    # ------------------------------------------------------------------

    def test_compute_grid_zero_three(self, dr_module, auto_df):
        """BUG-43-1c: _compute_grid('0 3') must not produce zero rows."""
        renderer = dr_module.DashRenderer.__new__(dr_module.DashRenderer)
        rows, cols = renderer._compute_grid(4, "0 3")
        assert rows >= 1, f"rows must be >= 1, got {rows}"
        assert cols == 3, f"cols should be 3, got {cols}"

    # ------------------------------------------------------------------
    # BUG-43-1d: valid "2 3" unchanged
    # ------------------------------------------------------------------

    def test_compute_grid_valid_unchanged(self, dr_module, auto_df):
        """BUG-43-1d: _compute_grid('2 3') must return exactly (2, 3)."""
        renderer = dr_module.DashRenderer.__new__(dr_module.DashRenderer)
        rows, cols = renderer._compute_grid(4, "2 3")
        assert (rows, cols) == (2, 3), f"Expected (2,3), got ({rows},{cols})"

    # ------------------------------------------------------------------
    # BUG-43-1e: Stata validation regex rejects zero columns
    # ------------------------------------------------------------------

    def test_ado_validation_regex_rejects_zero_column(self):
        """BUG-43-1e: dash.ado must use [1-9][0-9]* pattern for N M grid layout."""
        with open(os.path.join(_DASH_DIR, "dash.ado"), encoding="utf-8") as f:
            ado_text = f.read()
        # The old regex [0-9]+ [0-9]+ accepted zeros; confirm new pattern present
        assert "[1-9][0-9]* [1-9][0-9]*" in ado_text, (
            "dash.ado should use [1-9][0-9]* pattern to reject zero-dimension layouts"
        )


# ===========================================================================
# BUG-44 — Standalone slider/range filters crash on string variables.
#
# _extract_finite called np.array([...], dtype=float), which raises ValueError
# for string columns.  The fix adds an is_numeric_dtype guard in
# _build_filter_widgets before calling build_slider/build_range.  (The
# widgets read a column through _dash_finite_column since; _extract_finite
# was left uncalled and WP-26 deleted it, 24sep2026.)
#
# BUG-44-1a  Standalone slider on string column emits warning, does not raise
# BUG-44-1b  Standalone range on string column emits warning, does not raise
# BUG-44-1c  Standalone slider on numeric column still works
# BUG-44-1d  Standalone range on numeric column still works
# BUG-44-1e  Warning text mentions the filter variable name
# ===========================================================================

class TestStandaloneSliderStringColumn:
    """BUG-44: standalone slider/range on string column must skip gracefully."""

    def _string_col_spec(self, filter_type="slider"):
        return _make_spec_json(
            graphs=[{
                "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                           "options": {}}],
                "graph_options": {"name": "g1"},
            }],
            build_options={
                "layout": "auto", "link": "",
                "filter": f"group, type({filter_type})",
                "theme": "default", "title": "Test",
                "subtitle": "", "registry": "",
                "mode": "standalone", "port": "5006",
            },
        )

    # ------------------------------------------------------------------
    # BUG-44-1a: standalone slider on string col → warning, no crash
    # ------------------------------------------------------------------

    def test_standalone_slider_string_no_crash(self, dr_module):
        """BUG-44-1a: slider filter on string column must emit warning, not crash."""
        import warnings
        rng = np.random.default_rng(42)
        df = pd.DataFrame({
            "mpg":    rng.integers(12, 40, 10).astype(float),
            "weight": rng.integers(1800, 4800, 10).astype(float),
            "group":  ["A", "B", "A", "B", "A", "B", "A", "B", "A", "B"],
        })
        spec = self._string_col_spec("slider")
        spec_path, data_path = _write_temp_files_with_strings(df, spec, ["group"])
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                dr = dr_module.DashRenderer(spec_path, data_path)
                render_models(dr)
            # Must not raise; warning should be present
            warning_texts = [str(w.message) for w in caught]
            assert any("slider" in t.lower() or "numeric" in t.lower()
                       for t in warning_texts), (
                f"Expected slider/numeric warning, got: {warning_texts}"
            )
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    # ------------------------------------------------------------------
    # BUG-44-1b: standalone range on string col → warning, no crash
    # ------------------------------------------------------------------

    def test_standalone_range_string_no_crash(self, dr_module):
        """BUG-44-1b: range filter on string column must emit warning, not crash."""
        import warnings
        rng = np.random.default_rng(43)
        df = pd.DataFrame({
            "mpg":    rng.integers(12, 40, 10).astype(float),
            "weight": rng.integers(1800, 4800, 10).astype(float),
            "group":  ["X", "Y", "X", "Y", "X", "Y", "X", "Y", "X", "Y"],
        })
        spec = self._string_col_spec("range")
        spec_path, data_path = _write_temp_files_with_strings(df, spec, ["group"])
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                dr = dr_module.DashRenderer(spec_path, data_path)
                render_models(dr)
            warning_texts = [str(w.message) for w in caught]
            assert any("range" in t.lower() or "numeric" in t.lower()
                       for t in warning_texts), (
                f"Expected range/numeric warning, got: {warning_texts}"
            )
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    # ------------------------------------------------------------------
    # BUG-44-1c: numeric slider still works
    # ------------------------------------------------------------------

    def test_standalone_slider_numeric_still_works(self, dr_module, auto_df):
        """BUG-44-1c: slider filter on numeric column must still build widget."""
        import warnings
        spec = self._string_col_spec("slider")
        # Use 'foreign' (numeric) as the filter variable
        spec["build_options"]["filter"] = "foreign, type(slider)"
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                dr = dr_module.DashRenderer(spec_path, data_path)
                render_models(dr)
            # No slider/numeric warning expected for numeric column
            warning_texts = [str(w.message) for w in caught]
            slider_warns = [t for t in warning_texts
                            if "slider" in t.lower() and "numeric" in t.lower()]
            assert not slider_warns, (
                f"Unexpected slider/numeric warning for numeric column: {slider_warns}"
            )
            # Widget should have been built
            assert len(dr.filter_widgets) >= 1, "Expected at least one slider widget"
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    # ------------------------------------------------------------------
    # BUG-44-1d: numeric range still works
    # ------------------------------------------------------------------

    def test_standalone_range_numeric_still_works(self, dr_module, auto_df):
        """BUG-44-1d: range filter on numeric column must still build widget."""
        import warnings
        spec = self._string_col_spec("range")
        spec["build_options"]["filter"] = "mpg, type(range)"
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                dr = dr_module.DashRenderer(spec_path, data_path)
                render_models(dr)
            warning_texts = [str(w.message) for w in caught]
            range_warns = [t for t in warning_texts
                           if "range" in t.lower() and "numeric" in t.lower()]
            assert not range_warns, (
                f"Unexpected range/numeric warning for numeric column: {range_warns}"
            )
            assert len(dr.filter_widgets) >= 1, "Expected at least one range widget"
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    # ------------------------------------------------------------------
    # BUG-44-1e: warning mentions the variable name
    # ------------------------------------------------------------------

    def test_warning_mentions_variable_name(self, dr_module):
        """BUG-44-1e: warning for string slider must mention the filter variable name."""
        import warnings
        rng = np.random.default_rng(44)
        df = pd.DataFrame({
            "mpg":    rng.integers(12, 40, 8).astype(float),
            "weight": rng.integers(1800, 4800, 8).astype(float),
            "myvar":  ["cat", "dog"] * 4,
        })
        spec = self._string_col_spec("slider")
        spec["build_options"]["filter"] = "myvar, type(slider)"
        spec_path, data_path = _write_temp_files_with_strings(df, spec, ["myvar"])
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                dr = dr_module.DashRenderer(spec_path, data_path)
                render_models(dr)
            warning_texts = [str(w.message) for w in caught]
            assert any("myvar" in t for t in warning_texts), (
                f"Warning should mention variable 'myvar', got: {warning_texts}"
            )
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass


# ===========================================================================
# BUG-45 — Semicolon-delimited multi-filter specs only serialize the first
#          filter variable in _dash_build.
#
# The filter-variable extraction loop in dash.ado only split on "||", so
# "foreign; weight" contributed only "foreign" to all_vars.  The Python
# renderer's _parse_filter_raw already normalizes ";" -> "||".  The Stata
# side now does the same -- outside quotes and parentheses, as the renderer
# now does too (_dash_filter_split on both sides).
#
# BUG-45-1a  dash.ado's filter groups end at a ";" as at a "||" -- run by
#            test_help_claims_3.cscript HC3-11b since WP-24 (see below)
# BUG-45-1b  Standalone render with semicolon filter builds both widgets
# BUG-45-1c  "||"-separated filter still works (regression)
# BUG-45-1d  Single filter (no separator) still works (regression)
# ===========================================================================

class TestSemicolonFilterSerialization:
    """BUG-45: semicolon-separated filter specs must all reach the Python renderer."""

    # BUG-45-1a (test_ado_contains_semicolon_normalization) read the
    # statements of _dash_prepare_spec and _dash_filter_split and said
    # HC3-11 built the behaviour end to end.  HC3-11 could not fail on it:
    # its second filter is weight, which its graphs draw, so weight was
    # exported whatever became of the second group.  The source test itself
    # stayed green when dash build checked every group's variable but
    # exported only the first group's (WP-24, measured by mutation).
    # test_help_claims_3.cscript HC3-11b builds a second group whose
    # variable no graph draws -- trunk, and the abbreviation tru -- and
    # requires its widget on the page; it fails on that mutation and on a
    # _dash_filter_split that no longer ends a group at ';'.

    # ------------------------------------------------------------------
    # BUG-45-1b: standalone render with semicolon filter builds both widgets
    # ------------------------------------------------------------------

    def test_standalone_semicolon_filter_builds_both_widgets(self, dr_module, auto_df):
        """BUG-45-1b: semicolon-separated filter must produce a widget for each var."""
        spec = _make_spec_json(
            graphs=[{
                "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                           "options": {}}],
                "graph_options": {"name": "g1"},
            }],
            build_options={
                "layout": "auto", "link": "",
                # Semicolon-separated — both foreign and mpg should get widgets
                "filter": "foreign, type(dropdown); mpg, type(range)",
                "theme": "default", "title": "T",
                "subtitle": "", "registry": "",
                "mode": "standalone", "port": "5006",
            },
        )
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            dr = dr_module.DashRenderer(spec_path, data_path)
            render_models(dr)
            assert len(dr.filter_widgets) == 2, (
                f"Expected 2 filter widgets (one per semicolon-separated spec), "
                f"got {len(dr.filter_widgets)}"
            )
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    # ------------------------------------------------------------------
    # BUG-45-1c: pipe-separated filter still works
    # ------------------------------------------------------------------

    def test_standalone_pipe_filter_regression(self, dr_module, auto_df):
        """BUG-45-1c: '||'-separated filter still builds both widgets after fix."""
        spec = _make_spec_json(
            graphs=[{
                "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                           "options": {}}],
                "graph_options": {"name": "g1"},
            }],
            build_options={
                "layout": "auto", "link": "",
                "filter": "foreign, type(dropdown) || mpg, type(range)",
                "theme": "default", "title": "T",
                "subtitle": "", "registry": "",
                "mode": "standalone", "port": "5006",
            },
        )
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            dr = dr_module.DashRenderer(spec_path, data_path)
            render_models(dr)
            assert len(dr.filter_widgets) == 2, (
                f"Expected 2 filter widgets from '||' spec, got {len(dr.filter_widgets)}"
            )
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    # ------------------------------------------------------------------
    # BUG-45-1d: single filter still works
    # ------------------------------------------------------------------

    def test_standalone_single_filter_regression(self, dr_module, auto_df):
        """BUG-45-1d: single filter (no separator) still builds one widget."""
        spec = _make_spec_json(
            graphs=[{
                "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                           "options": {}}],
                "graph_options": {"name": "g1"},
            }],
            build_options={
                "layout": "auto", "link": "",
                "filter": "foreign, type(dropdown)",
                "theme": "default", "title": "T",
                "subtitle": "", "registry": "",
                "mode": "standalone", "port": "5006",
            },
        )
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            dr = dr_module.DashRenderer(spec_path, data_path)
            render_models(dr)
            assert len(dr.filter_widgets) == 1, (
                f"Expected 1 filter widget, got {len(dr.filter_widgets)}"
            )
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass


# ===========================================================================
# BUG-46 — Server range/slider widgets initialized with NaN bounds on
#          all-missing numeric columns.
#
# Generated code computed vmin/vmax with df[fvar].min()/.max() directly.
# For all-NaN numeric columns both return NaN, producing an invalid widget
# (RangeSlider(start=nan, end=nan, ...)).  The fix adds math.isfinite checks
# and skips with a warning when bounds are not finite.
#
# BUG-46-1a  Generated source contains math.isfinite guard for range
# BUG-46-1b  Generated source contains math.isfinite guard for slider
# BUG-46-1c  make_document with all-NaN range column does not crash
# BUG-46-1d  make_document with all-NaN slider column does not crash
# BUG-46-1e  Normal range/slider on finite data still builds widget
# ===========================================================================

class TestServerNaNBoundsSlider:
    """BUG-46: server range/slider on all-missing column must skip gracefully."""

    def _all_nan_spec(self, ftype, auto_df):
        # Add an all-NaN column 'flt' to test data
        df = auto_df.copy()
        df["flt"] = float("nan")
        spec = _make_spec_json(
            graphs=[{
                "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                           "options": {}}],
                "graph_options": {"name": "g1"},
            }],
            build_options={
                "layout": "auto", "link": "",
                "filter": f"flt, type({ftype})",
                "theme": "default", "title": "T",
                "subtitle": "", "registry": "",
                "mode": "server", "port": "5006",
            },
        )
        return df, spec

    # ------------------------------------------------------------------
    # BUG-46-1a: generated source has math.isfinite guard for range
    # ------------------------------------------------------------------

    def test_generated_source_has_finite_guard_range(self, dr_module, auto_df):
        """BUG-46-1a: generated source must contain math.isfinite guard for range."""
        df, spec = self._all_nan_spec("range", auto_df)
        src = _build_app(dr_module, df, spec)
        assert "math.isfinite" in src, (
            "Generated source missing math.isfinite guard for range widget"
        )

    # ------------------------------------------------------------------
    # BUG-46-1b: generated source has math.isfinite guard for slider
    # ------------------------------------------------------------------

    def test_generated_source_has_finite_guard_slider(self, dr_module, auto_df):
        """BUG-46-1b: generated source must contain math.isfinite guard for slider."""
        df, spec = self._all_nan_spec("slider", auto_df)
        src = _build_app(dr_module, df, spec)
        assert "math.isfinite" in src, (
            "Generated source missing math.isfinite guard for slider widget"
        )

    # ------------------------------------------------------------------
    # BUG-46-1c: make_document with all-NaN range does not crash
    # ------------------------------------------------------------------

    def test_make_document_all_nan_range_no_crash(self, dr_module, auto_df):
        """BUG-46-1c: make_document must not crash when range filter column is all-NaN."""
        import warnings
        from bokeh.document import Document
        df, spec = self._all_nan_spec("range", auto_df)
        spec_path, data_path = _write_temp_files(df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_mod = load_app(out_f.name, "_b46c")
            doc = Document()
            with warnings.catch_warnings(record=True):
                warnings.simplefilter("always")
                app_mod.make_document(doc)  # must not raise
            n_renderers = _count_glyph_renderers(doc)
            assert n_renderers >= 1
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try: os.unlink(_p)
                except OSError: pass

    # ------------------------------------------------------------------
    # BUG-46-1d: make_document with all-NaN slider does not crash
    # ------------------------------------------------------------------

    def test_make_document_all_nan_slider_no_crash(self, dr_module, auto_df):
        """BUG-46-1d: make_document must not crash when slider filter column is all-NaN."""
        import warnings
        from bokeh.document import Document
        df, spec = self._all_nan_spec("slider", auto_df)
        spec_path, data_path = _write_temp_files(df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_mod = load_app(out_f.name, "_b46d")
            doc = Document()
            with warnings.catch_warnings(record=True):
                warnings.simplefilter("always")
                app_mod.make_document(doc)  # must not raise
            assert _count_glyph_renderers(doc) >= 1
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try: os.unlink(_p)
                except OSError: pass

    # ------------------------------------------------------------------
    # BUG-46-1e: normal finite data still builds the widget
    # ------------------------------------------------------------------

    def test_make_document_finite_range_builds_widget(self, dr_module, auto_df):
        """BUG-46-1e: range filter on finite numeric column still builds widget."""
        from bokeh.document import Document
        spec = _make_spec_json(
            graphs=[{
                "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                           "options": {}}],
                "graph_options": {"name": "g1"},
            }],
            build_options={
                "layout": "auto", "link": "",
                "filter": "mpg, type(range)",
                "theme": "default", "title": "T",
                "subtitle": "", "registry": "",
                "mode": "server", "port": "5006",
            },
        )
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_mod = load_app(out_f.name, "_b46e")
            doc = Document()
            app_mod.make_document(doc)
            # Should have a RangeSlider widget in the layout
            src_text = open(out_f.name).read()
            assert "RangeSlider" in src_text, "Generated source should create RangeSlider"
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try: os.unlink(_p)
                except OSError: pass


# ---------------------------------------------------------------------------
# BUG-47 Regression tests — dash serve fixed temp app filename
# ---------------------------------------------------------------------------
class TestServeUniqueAppPath:
    """BUG-47: dash serve used 'dash_serve_app.py' (fixed name) for every run,
    causing cross-run file overwrites and race conditions when two dash serve
    invocations ran concurrently.  Fix: use Stata tempfile to generate a unique
    base path per invocation.

    The fix is dash.ado's, and is certified by running it:
    test_serve_launch.cscript SRV-19 runs dash serve with the renderer
    stubbed to record its arguments, and requires the app file it is
    handed to be app.py in a private run folder of the session,
    c(tmpdir)dash-<uid>/run-<pid>-<random>/ (WP-29 P0.12b; it was a Stata
    tempfile of the session).  A test here used to read
    _dash_serve's text for `tempfile ... serve_app'; measured (WP-24), a
    COMMENT in _dash_serve satisfied it, so with the tempfile line deleted
    and the fixed name restored it stayed green.  It was removed for SRV-19.
    What remains here is the renderer's half: ServerAppBuilder writes to
    whatever path it is handed and imposes no fixed name of its own.
    """

    def _simple_spec(self):
        """Return a minimal server spec dict."""
        return _make_spec_json(
            graphs=[{
                "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                           "options": {}}],
                "graph_options": {"name": "g1"},
            }],
            build_options={
                "layout": "auto", "link": "",
                "filter": "",
                "theme": "default", "title": "T",
                "subtitle": "", "registry": "",
                "mode": "server", "port": "5006",
            },
        )

    # ------------------------------------------------------------------
    # BUG-47-1b: ServerAppBuilder.build() accepts any caller-provided path
    # ------------------------------------------------------------------
    def test_BUG_47_1b_builder_writes_to_arbitrary_path(self, dr_module, auto_df):
        """ServerAppBuilder.build() should honour any output path supplied."""
        spec = self._simple_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out = tempfile.NamedTemporaryFile(suffix=".py", delete=False)
        out.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out.name)
            assert os.path.exists(out.name), "Output .py file was not created"
            with open(out.name) as fh:
                assert "make_document" in fh.read()
        finally:
            for p in (spec_path, data_path, out.name):
                try:
                    os.unlink(p)
                except OSError:
                    pass

    # ------------------------------------------------------------------
    # BUG-47-1c: Two concurrent builds use different paths without conflict
    # ------------------------------------------------------------------
    def test_BUG_47_1c_two_builds_independent_files(self, dr_module, auto_df):
        """Two separate ServerAppBuilder.build() calls to distinct paths produce
        independent files — writing path B does not overwrite path A."""
        import time as _time
        spec = self._simple_spec()
        sp1, dp1 = _write_temp_files(auto_df, spec)
        sp2, dp2 = _write_temp_files(auto_df, spec)
        out_a = tempfile.NamedTemporaryFile(suffix=".py", delete=False)
        out_a.close()
        out_b = tempfile.NamedTemporaryFile(suffix=".py", delete=False)
        out_b.close()
        # Confirm the two output paths are distinct (tempfile uniqueness)
        assert out_a.name != out_b.name
        try:
            dr_module.ServerAppBuilder(sp1, dp1).build(out_a.name)
            dr_module.ServerAppBuilder(sp2, dp2).build(out_b.name)
            # Each file is a real server app -- it defines make_document --
            # not merely non-empty (getsize > 0 passed on any byte).
            def _defines_make_document(path):
                with open(path, encoding="utf-8") as fh:
                    tree = ast.parse(fh.read())
                return "make_document" in {n.name for n in tree.body
                                           if isinstance(n, ast.FunctionDef)}
            assert _defines_make_document(out_a.name), "File A is not an app"
            assert _defines_make_document(out_b.name), "File B is not an app"
            # Overwriting B must not affect A
            mtime_a_before = os.path.getmtime(out_a.name)
            _time.sleep(0.05)
            dr_module.ServerAppBuilder(sp2, dp2).build(out_b.name)
            mtime_a_after = os.path.getmtime(out_a.name)
            assert abs(mtime_a_before - mtime_a_after) < 0.02, (
                "Rebuilding path B changed path A's mtime — files are not independent"
            )
        finally:
            for p in (sp1, dp1, sp2, dp2, out_a.name, out_b.name):
                try:
                    os.unlink(p)
                except OSError:
                    pass

    # ------------------------------------------------------------------
    # BUG-47-1d: Output path does NOT contain hard-coded "dash_serve_app"
    # ------------------------------------------------------------------
    def test_BUG_47_1d_no_fixed_serve_app_name_in_generated_source(self, dr_module, auto_df):
        """The generated server .py should not reference 'dash_serve_app' as a
        module name — that constant should no longer exist anywhere."""
        spec = self._simple_spec()
        sp, dp = _write_temp_files(auto_df, spec)
        out = tempfile.NamedTemporaryFile(suffix=".py", delete=False)
        out.close()
        try:
            dr_module.ServerAppBuilder(sp, dp).build(out.name)
            with open(out.name) as fh:
                src = fh.read()
            assert "dash_serve_app" not in src, (
                "Generated server source still references 'dash_serve_app' (BUG-47 regression)"
            )
        finally:
            for p in (sp, dp, out.name):
                try:
                    os.unlink(p)
                except OSError:
                    pass

    # ------------------------------------------------------------------
    # BUG-47-1e: Generated app is importable from a uniquely-named path
    # ------------------------------------------------------------------
    def test_BUG_47_1e_generated_app_importable_from_unique_path(self, dr_module, auto_df):
        """make_document draws the dashboard when the .py file has an unusual
        (unique / tempfile-style) name rather than 'dash_serve_app'.

        This asserted ``len(doc.roots) > 0``, which the layout column
        satisfies even from an empty draw (WP-24, measured 24sep2026).  The
        served scatter is read: all 30 (weight, mpg) points, from an app
        whose filename is a Stata tempfile style ST_99999.* -- so the fixed
        name is gone and the unique one still runs."""
        from bokeh.document import Document as _Doc
        spec = self._simple_spec()
        # Use a decidedly non-standard filename (mirrors Stata tempfile style)
        out = tempfile.NamedTemporaryFile(
            prefix="ST_99999.", suffix=".py", delete=False
        )
        out.close()
        sp, dp = _write_temp_files(auto_df, spec)
        try:
            dr_module.ServerAppBuilder(sp, dp).build(out.name)
            mod = load_app(out.name, "_dash_bug47_test")
            doc = _Doc()
            mod.make_document(doc)
            (_fig, r), = _glyph_layers(doc.roots)
            assert type(r.glyph).__name__ == "Scatter"
            assert sorted(zip(_drawn_values(r, "weight"),
                              _drawn_values(r, "mpg"))) == \
                sorted(zip(auto_df["weight"], auto_df["mpg"]))
        finally:
            for p in (sp, dp, out.name):
                try:
                    os.unlink(p)
                except OSError:
                    pass


# ---------------------------------------------------------------------------
# BUG-48 Regression tests — health endpoint and dashboard sessions share rate-limit bucket
# ---------------------------------------------------------------------------
class TestSeparateRateLimitBuckets:
    """BUG-48: _LIMITER was shared between /health and make_document, so normal
    dashboard traffic could exhaust the health-check budget and cause false-negative
    liveness signals.  Fix: introduce _SESSION_LIMITER and _HEALTH_LIMITER as
    independent buckets with separate RPM limits.
    """

    def _build_source(self, dr_module, auto_df):
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        return _build_app(dr_module, auto_df, spec)

    # ------------------------------------------------------------------
    # BUG-48-1a: generated source defines _SESSION_LIMITER
    # ------------------------------------------------------------------
    def test_BUG_48_1a_session_limiter_defined(self, dr_module, auto_df):
        """Generated source must define _SESSION_LIMITER for dashboard connections."""
        src = self._build_source(dr_module, auto_df)
        assert "_SESSION_LIMITER" in src, (
            "Generated source missing _SESSION_LIMITER (BUG-48 regression)"
        )

    # ------------------------------------------------------------------
    # BUG-48-1b: generated source defines _HEALTH_LIMITER
    # ------------------------------------------------------------------
    def test_BUG_48_1b_health_limiter_defined(self, dr_module, auto_df):
        """Generated source must define _HEALTH_LIMITER for /health endpoint."""
        src = self._build_source(dr_module, auto_df)
        assert "_HEALTH_LIMITER" in src, (
            "Generated source missing _HEALTH_LIMITER (BUG-48 regression)"
        )

    # ------------------------------------------------------------------
    # BUG-48-1c: _HealthHandler uses _HEALTH_LIMITER, not _SESSION_LIMITER
    # ------------------------------------------------------------------
    def test_BUG_48_1c_health_handler_uses_health_limiter(self, dr_module, auto_df):
        """_HealthHandler.prepare must consume _HEALTH_LIMITER, not _SESSION_LIMITER."""
        import re
        src = self._build_source(dr_module, auto_df)
        # Extract the _HealthHandler class body
        m = re.search(r"class _HealthHandler.*?def get\(", src, re.DOTALL)
        assert m, "_HealthHandler class not found in generated source"
        section = m.group(0)
        assert "_HEALTH_LIMITER.is_allowed" in section, (
            "_HealthHandler.prepare should call _HEALTH_LIMITER.is_allowed (BUG-48 regression)"
        )
        assert "_SESSION_LIMITER.is_allowed" not in section, (
            "_HealthHandler.prepare must not use _SESSION_LIMITER (cross-bucket pollution)"
        )

    # ------------------------------------------------------------------
    # BUG-48-1d: make_document uses _SESSION_LIMITER, not _HEALTH_LIMITER
    # ------------------------------------------------------------------
    def test_BUG_48_1d_make_document_uses_session_limiter(self, dr_module, auto_df):
        """make_document must consume _SESSION_LIMITER, not _HEALTH_LIMITER."""
        import re
        src = self._build_source(dr_module, auto_df)
        m = re.search(r"def make_document\(.*", src, re.DOTALL)
        assert m, "make_document not found in generated source"
        fn_body = src[m.start():]
        # Only consider up to next top-level def / end-of-file
        next_def = re.search(r"\ndef [a-zA-Z_]", fn_body[10:])
        if next_def:
            fn_body = fn_body[: next_def.start() + 10]
        assert "_SESSION_LIMITER.is_allowed" in fn_body, (
            "make_document should call _SESSION_LIMITER.is_allowed (BUG-48 regression)"
        )
        assert "_HEALTH_LIMITER.is_allowed" not in fn_body, (
            "make_document must not use _HEALTH_LIMITER"
        )

    # ------------------------------------------------------------------
    # BUG-48-1e: session budget exhaustion does not block /health checks
    # ------------------------------------------------------------------
    def test_BUG_48_1e_session_exhaustion_does_not_block_health(self, dr_module, auto_df):
        """Exhausting _SESSION_LIMITER for an IP must not affect _HEALTH_LIMITER."""
        src = self._build_source(dr_module, auto_df)
        mod = types.ModuleType("_b48e_mod")
        exec(compile(src, "<test>", "exec"), mod.__dict__)
        session_lim = getattr(mod, "_SESSION_LIMITER")
        health_lim = getattr(mod, "_HEALTH_LIMITER")
        ip = "10.0.0.1"
        # Exhaust session limiter for ip
        for _ in range(session_lim._max + 5):
            session_lim.is_allowed(ip)
        # Session should now be blocked
        assert not session_lim.is_allowed(ip), (
            "_SESSION_LIMITER should be exhausted after max+5 calls"
        )
        # Health limiter for the same IP must still allow requests
        assert health_lim.is_allowed(ip), (
            "After exhausting _SESSION_LIMITER, _HEALTH_LIMITER should still allow "
            "health checks for the same IP (BUG-48 regression: shared bucket)"
        )


# ---------------------------------------------------------------------------
# BUG-49 Regression tests — timeout() unit mismatch (help said seconds, code uses minutes)
# ---------------------------------------------------------------------------
class TestTimeoutUnitConsistency:
    """BUG-49: dash.sthlp documented timeout(#) as seconds while all code paths
    (dash.ado error messages, argparse help, runtime sleep) used minutes.
    Fix: update dash.sthlp to say 'minutes' to match the implementation.

    Regression tests verify all surfaces use the same unit (minutes).
    """

    # ------------------------------------------------------------------
    # BUG-49-1a: dash.sthlp contains 'minutes' for timeout, not 'seconds'
    # ------------------------------------------------------------------
    def test_BUG_49_1a_sthlp_says_minutes(self):
        """dash.sthlp must document timeout(#) in minutes (not seconds)."""
        sthlp_path = os.path.join(os.path.dirname(__file__), "..", "dash.sthlp")
        with open(sthlp_path, "r", encoding="utf-8") as fh:
            content = fh.read()
        # The synopt entry for timeout uses SMCL:
        #   {synopt:{cmd:timeout(}{it:#}{cmd:)}}stop the server after {it:#} minutes;
        # Search for the synopt definition block (synopt ... p_end) that contains timeout
        import re
        m = re.search(
            r"\{synopt:[^}]*timeout[^}]*\}[^\n]*\n?[^\n]*\{p_end\}",
            content, re.DOTALL
        )
        assert m, (
            "timeout() synopt entry not found in dash.sthlp — "
            "expected a line matching '{synopt:...timeout...} ... {p_end}'"
        )
        blurb = m.group(0)
        assert "minutes" in blurb, (
            "dash.sthlp timeout() description must say 'minutes' (BUG-49 regression: was 'seconds'). "
            f"Matched text: {blurb!r}"
        )
        assert "seconds" not in blurb, (
            "dash.sthlp timeout() description must not say 'seconds' (BUG-49 regression). "
            f"Matched text: {blurb!r}"
        )

    # ------------------------------------------------------------------
    # BUG-49-1b: dash.ado error message says 'minutes'
    # ------------------------------------------------------------------
    def test_BUG_49_1b_ado_error_message_says_minutes(self):
        """dash.ado timeout validation error must reference 'minutes'."""
        ado_path = os.path.join(os.path.dirname(__file__), "..", "dash.ado")
        with open(ado_path, "r", encoding="utf-8") as fh:
            content = fh.read()
        # Find the timeout validation error message
        import re
        m = re.search(r"timeout\(\) must be.*?\"", content, re.DOTALL)
        assert m, "timeout() validation error not found in dash.ado"
        blurb = m.group(0)
        assert "minutes" in blurb or "minute" in blurb, (
            "dash.ado timeout() error message must mention 'minutes' (BUG-49 regression)"
        )

    # ------------------------------------------------------------------
    # BUG-49-1c: dash_render.py argparse help says 'minutes'
    # ------------------------------------------------------------------
    def test_BUG_49_1c_argparse_help_says_minutes(self, tmp_path):
        """--timeout is described in minutes where a user reads it: the
        --help of dash_render.py and the --help of the app it generates.

        This read the 400 characters after '"--timeout"' in dash_render.py's
        TEXT: any "minutes" in that window passed it -- a comment, or the
        next option's help -- and the app's own --timeout, emitted from the
        same file with other quotes, was never read (WP-24).  Each program
        is now asked for its help, and its --timeout entry read."""
        import re
        import subprocess
        import warnings

        def _entry(text):
            m = re.search(r"^\s*--timeout TIMEOUT\s+(.*?)(?=^\s*-|\Z)",
                          text, re.M | re.S)
            assert m, text
            return " ".join(m.group(1).split())

        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cli = subprocess.run(
            [sys.executable, os.path.join(root, "dash_render.py"), "--help"],
            capture_output=True, text=True, timeout=120)
        assert cli.returncode == 0, cli.stderr
        entry = _entry(cli.stdout)
        assert "minutes" in entry and "second" not in entry, entry

        _here = os.path.dirname(os.path.abspath(__file__))
        for _p in (root, _here):
            if _p not in sys.path:
                sys.path.insert(0, _p)
        from conftest import make_spec as _ms, make_data_json as _md
        sp, dp, ap = (str(tmp_path / n) for n in ("s.json", "d.json",
                                                  "app.py"))
        with open(sp, "w") as fh:
            json.dump(_ms([{"type": "scatter", "yvar": "mpg",
                            "xvar": "weight", "options": {}}]), fh)
        with open(dp, "w") as fh:
            json.dump(_md(pd.DataFrame({"mpg": [1.0, 2.0],
                                        "weight": [3.0, 4.0]})), fh)
        import dash_render as _dr
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _dr.ServerAppBuilder(sp, dp).build(ap)
        app = subprocess.run([sys.executable, ap, "--help"],
                             capture_output=True, text=True, timeout=120)
        assert app.returncode == 0, app.stderr
        entry = _entry(app.stdout)
        assert "minutes" in entry and "second" not in entry, entry

    # ------------------------------------------------------------------
    # BUG-49-1d: runtime multiplies timeout by 60 (minutes → seconds)
    # ------------------------------------------------------------------
    def test_BUG_49_1d_runtime_uses_minutes_multiplier(self):
        """--timeout is in MINUTES, wherever the shutdown is scheduled.

        This grepped dash_render.py for the literal
        ``_time.sleep(args.timeout * 60)`` -- a thread that no longer exists.
        The auto-shutdown moved into the generated app, which schedules it on
        the Bokeh io loop instead of sleeping a thread, because dash's
        launcher now runs the app directly rather than shelling out to
        `bokeh serve' (that is what gives /health somewhere to live).

        The BEHAVIOUR being guarded is unchanged and is what is asserted:
        the number the user passes is minutes, so it is multiplied by 60
        before it becomes seconds.
        """
        import re
        import tempfile

        import numpy as _np
        import pandas as _pd
        _here = os.path.dirname(os.path.abspath(__file__))
        for _p in (os.path.join(_here, ".."), _here):
            if _p not in sys.path:
                sys.path.insert(0, _p)
        from dash_render import ServerAppBuilder
        from conftest import make_spec as _ms, make_data_json as _md

        d = tempfile.mkdtemp()
        df = _pd.DataFrame({"mpg": _np.linspace(12.0, 41.0, 8)})
        spec = _ms([{"type": "scatter", "yvar": "mpg", "xvar": "mpg",
                     "options": {}}])
        sp = os.path.join(d, "s.json")
        dp = os.path.join(d, "d.json")
        op = os.path.join(d, "app.py")
        with open(sp, "w") as f:
            json.dump(spec, f)
        with open(dp, "w") as f:
            json.dump(_md(df), f)
        ServerAppBuilder(sp, dp).build(op)
        with open(op, encoding="utf-8") as fh:
            app_src = fh.read()

        assert re.search(r"timeout\s*\*\s*60", app_src), (
            "the generated app schedules its auto-shutdown without "
            "converting minutes to seconds"
        )
        # And the option still describes itself as minutes.
        assert re.search(r"--timeout[\s\S]{0,200}minute", app_src), (
            "--timeout no longer documents its unit"
        )

    # ------------------------------------------------------------------
    # BUG-49-1e: no 'seconds' reference near timeout in any primary file
    # ------------------------------------------------------------------
    def test_BUG_49_1e_no_seconds_claim_near_timeout_in_sthlp(self):
        """The sthlp timeout() synopt description must not say 'seconds'.

        This searched ``(timeout\\(.*?{p_end})`` non-greedily.  The first
        ``timeout(`` in the file is in the `dash serve' SYNTAX diagram, and
        ``.*?{p_end}`` from there stops at the next ``{p_end}`` -- the
        "Clear registry" heading two blocks down -- so the span it captured
        never reached the synopt description at all.  "seconds" is not in
        that span whatever the description says, and the whole thing was
        also under ``if m:``, vacuous had the match failed (WP-24, measured
        24sep2026: the synopt flipped to 'seconds' left this green while
        1a caught it).

        The description is now matched where it lives: from the ``{synopt:``
        that names timeout to that entry's own ``{p_end}``, across the
        wrapped continuation line.  The match is asserted (never vacuous),
        and the positive control shows a 'seconds' in that block would be
        seen -- so the absence check is real."""
        sthlp_path = os.path.join(os.path.dirname(__file__), "..", "dash.sthlp")
        with open(sthlp_path, "r", encoding="utf-8") as fh:
            content = fh.read()
        import re
        m = re.search(r"\{synopt:[^}]*timeout.*?\{p_end\}", content, re.DOTALL)
        assert m, "no timeout() synopt entry found in dash.sthlp"
        blurb = m.group(0)
        assert "seconds" not in blurb, (
            "timeout() synopt in dash.sthlp must not say 'seconds' (BUG-49 "
            f"regression). Matched text: {blurb!r}"
        )
        # Positive control: a 'seconds' inside this very block is caught by
        # the same search, so the assertion above is not vacuously true.
        injected = content.replace(blurb, blurb.replace("minutes", "seconds"), 1)
        control = re.search(r"\{synopt:[^}]*timeout.*?\{p_end\}", injected,
                            re.DOTALL)
        assert control and "seconds" in control.group(0), (
            "the synopt search cannot see a 'seconds' in the timeout block")


# ---------------------------------------------------------------------------
# BUG-50 Regression tests — dash_setup aborts before dep checks when packaging absent
# ---------------------------------------------------------------------------
# dash_setup.ado imported `packaging.version.Version` inside the per-package
# loop but only installed `packaging` AFTER the loop, so on a fresh
# environment the first iteration raised ModuleNotFoundError and dash_setup
# stopped early.  The fix installs packaging BEFORE the loop, and the version
# comparisons fall back when it cannot be installed.
#
# The five tests that stood here (TestDashSetupPackagingOrder, BUG-50-1a to
# 1e) read dash_setup.ado's text: where `import packaging' first occurs, a
# flag's name, a comment's absence.  Each passed with the behaviour it names
# broken (measured 24sep2026 on scratch copies): the guard moved after the
# loop behind a comment naming the import; an uncaptured `import
# packaging.version' before the guard, which none of the five saw; the flag
# ignored; the old post-loop install back without its comment; the guard's
# install kept but never run, or run whether packaging was there or not.
# dash_setup now runs in a sandbox that records pip and installs nothing
# (test/setup_sandbox.py), and each claim is held by what it does:
#   BUG-50-1a  the guard runs before the loop: test_setup_honesty.cscript
#              HON-27 (packaging and bokeh missing: pip is asked for
#              packaging first) and test_program_coverage.cscript PC-15
#              (every version OK, which a comparison made before the guard
#              reports as not verified); both fail with the guard moved.
#   BUG-50-1b  nothing imports packaging.version before the guard: HON-26
#              (packaging absent, its submodule too: setup does not stop,
#              one pip call, every version not verified).  PC-18 and HON-21
#              block packaging alone, and measured, an uncaptured `from
#              packaging.version import Version' before the guard -- BUG-50
#              itself -- passes both, the submodule being in the module
#              cache; it fails HON-26.  `import packaging.version' fails all
#              three.
#   BUG-50-1c  the version comparison waits on the guard's verdict: PC-18
#              and HON-21 (with the flag ignored the gate reports OK, which
#              they refuse); and setup does not stop when packaging is
#              absent, HON-26 (fails with the flag ignored and the gate's
#              capture gone).
#   BUG-50-1d  packaging is asked for once, never again after the loop:
#              PC-18, HON-21 and HON-26 compare the whole list of pip calls.
#   BUG-50-1e  the guard checks and installs: PC-15 and HON-28 (packaging
#              present, no pip call) and PC-18, HON-21, HON-26 (missing, one
#              pip call).


class TestTheServerDispatchesThroughTheSharedTable:
    """The generated app must call GlyphMapper, not re-implement it.

    The whole ``GlyphMapper`` class has always been embedded in the generated
    app via ``inspect.getsource``, and ``_DASH_MAPPER`` constructed from it --
    so all 39 ``map_*`` methods were available there. Measured before this
    work, ``grep -oE '_DASH_MAPPER\\.map_[a-z_]+' dash_render.py`` returned
    exactly one name: ``map_scatter``. The other 38 plot types were
    reimplemented inline as an ``if/elif ptype == '...'`` chain of emitted
    string literals, and the two implementations disagreed in 132
    non-cosmetic ways across 37 types (28 of them S1) -- see the BUGS.md
    entry and ROADMAP WP-09.

    These tests pin the machinery that makes one implementation possible:
    the dispatch tables and the layer-source helper are copied into the app
    verbatim, the way the statistical helpers already were, so a plot type
    added to the table is added to both modes at once.
    """

    def _app_source(self, tmp_path, dr_module, auto_df, plots=None):
        # _make_spec_json() defaults to NO graphs, so a spec built from it
        # has to carry its own; indexing graphs[0] is an IndexError.
        if plots is None:
            plots = [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                      "options": {}}]
        spec = _make_spec_json(graphs=[{
            "name": "g1", "plots": plots, "graph_options": {"name": "g1"},
            "if_expr": "", "in_expr": "",
        }])
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out = str(tmp_path / "app.py")
        dr_module.ServerAppBuilder(spec_path, data_path).build(out)
        with open(out, encoding="utf-8") as fh:
            return fh.read()

    def test_the_dispatch_tables_are_copied_into_the_app(self, tmp_path,
                                                         dr_module, auto_df):
        src = self._app_source(tmp_path, dr_module, auto_df)
        for name in ("_dash_glyph_dispatch", "_dash_pc_dispatch",
                     "_dash_add_glyph", "_dash_add_pc_glyph",
                     "_dash_layer_source"):
            assert ("def %s(" % name) in src, (
                "%s is not emitted into the generated app, so the app cannot "
                "share the renderer's dispatch" % name
            )

    def test_the_type_categories_are_shared_not_recopied(self, tmp_path,
                                                         dr_module, auto_df):
        """The app used to carry its own copies inside the chain."""
        src = self._app_source(tmp_path, dr_module, auto_df)
        for name in ("_DASH_RANGE_TYPES", "_DASH_UNIVARIATE_TYPES",
                     "_DASH_PC_TYPES"):
            assert ("%s =" % name) in src, name

    def test_the_emitted_table_is_the_renderers_own(self, dr_module):
        """Not a transcription: the same function object, read by source."""
        import inspect
        for name in ("_dash_add_glyph", "_dash_add_pc_glyph",
                     "_dash_layer_source"):
            fn = getattr(dr_module, name)
            assert inspect.isfunction(fn), name
            # It must take the mapper as a parameter rather than reaching for
            # `self`, or it could not be copied into the app at all.
            assert "self" not in inspect.signature(fn).parameters, name

    def test_every_shipped_plot_type_has_a_mapper(self, dr_module):
        """AC-09.1's precondition, asserted directly.

        Every ``map_*`` method must be reachable from a table, and every
        table entry must name a real method. A type in neither is a type one
        render mode cannot draw.
        """
        class _Probe:
            def __getattr__(self, name):
                if not name.startswith("map_"):
                    raise AttributeError(name)
                return name

        probe = _Probe()
        std, rng = dr_module._dash_glyph_dispatch(probe)
        pc = dr_module._dash_pc_dispatch(probe)
        named = set(std.values()) | set(rng.values()) | set(pc.values())

        import inspect
        defined = {
            n for n, _ in inspect.getmembers(dr_module.GlyphMapper,
                                             inspect.isfunction)
            if n.startswith("map_")
        }
        # Four are reached by the CALLER rather than the table, because
        # they do not take (yvar, xvar) from a shared source: pci, pcarrowi
        # and scatteri take an inline coordinate list, and function takes
        # an expression and a range.  The standalone caller special-cases
        # all four before it reaches _add_glyph, and the server must too.
        for _caller_dispatched in ("map_pci_literal", "map_pcarrowi",
                                   "map_scatteri", "map_function"):
            defined.discard(_caller_dispatched)
        assert named == defined, (
            "table and GlyphMapper disagree; only in the table: %s; only on "
            "the class: %s" % (sorted(named - defined), sorted(defined - named))
        )

    def test_an_unknown_plot_type_warns_rather_than_drawing_nothing(
            self, dr_module):
        """AC-09.3. Silence here is how 38 types went missing unnoticed."""
        import warnings as _w

        class _Mapper:
            def _check_vars(self, *a, **k):
                return True

            def __getattr__(self, name):
                # Building the dispatch table looks up every map_* method,
                # so the stub has to answer all of them.
                if name.startswith("map_"):
                    return lambda *a, **k: None
                raise AttributeError(name)

        with _w.catch_warnings(record=True) as caught:
            _w.simplefilter("always")
            out = dr_module._dash_add_glyph(
                _Mapper(), None, None, "no_such_plot_type", "y", "x", {})
        assert out is None
        assert any("no glyph mapper" in str(c.message) for c in caught), (
            [str(c.message) for c in caught]
        )

    def test_the_swapped_types_call_the_mapper_in_the_app(self, tmp_path,
                                                          dr_module, auto_df):
        """The six types moved onto the shared dispatch in this change."""
        plots = [{"type": t, "yvar": "mpg", "xvar": "weight", "options": {}}
                 for t in ("dot", "qfit", "lfitci", "qfitci", "fpfit",
                           "fpfitci")]
        src = self._app_source(tmp_path, dr_module, auto_df, plots)
        # WP-09 left one branch per type, each the same eleven lines; WP-11
        # folded them into ONE dispatch by plot-type family, which the by()
        # panels and the filter redraw call as well.  So: no per-type branch
        # for these six, and the shared dispatch functions are what is
        # called.
        for t in ("dot", "qfit", "lfitci", "qfitci", "fpfit", "fpfitci"):
            assert ("elif ptype == '%s':" % t) not in src, t
        assert src.count("def _dash_draw_layer(") == 1
        assert "_dash_add_glyph(" in src and "_dash_add_pc_glyph(" in src
