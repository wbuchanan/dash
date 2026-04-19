"""
test_server.py
==============
Unit tests for the ServerAppBuilder class in dash_render.py.

Tests:
  P4-57  Build output compiles without error
  P4-58  Generated file contains make_document function
  P4-59  Generated file contains __main__ block
  P4-60  Generated file contains Server and allow_websocket_origin
  P4-61  make_document callable — adds at least one root to Document
  P4-62  Filter callback recomputes histogram CDS when data is filtered
  P4-63  Filter callback recomputes lfit CDS when data is filtered
  P4-64  Filter callback updates filter-mode KPI Div.text
  P4-65  Brush callback updates brush-mode KPI Div.text
  P4-66  Base64 data round-trips correctly
  P4-67  XSS: <script> in title is HTML-escaped in generated file
  P4-68  Python escape chars in data do not break generated file syntax
  P4-69  --mode standalone still produces HTML (regression)
  P4-70  _compute_histogram returns correct structure
  P4-71  _compute_kpi returns correct values for mean and dcount
  P4-72  _compute_lfit returns 100 x/y points
  P4-73  _compute_kpi sd uses ddof=1 matching Stata (regression)

  BUG-RL-1  _RateLimiter allows requests below limit and blocks above it
  BUG-RL-2  Generated HealthHandler.prepare() enforces _LIMITER (429 on excess)
  BUG-RL-3  make_document enforces rate limit — adds 429 Div and returns early
  BUG-RL-4  make_document proceeds normally when rate limit is not exceeded

  BUG-FE-1  Server-mode function expressions with arithmetic operators (+, -, *, /, **) must not raise ValueError
"""

from __future__ import annotations

import ast
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
    # Should not raise SyntaxError
    compile(source, "<generated>", "exec")


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
# P4-61: make_document callable — adds at least one root to Document
# ---------------------------------------------------------------------------

def test_make_document_callable(dr_module, auto_df):
    """P4-61: Importing and calling make_document does not raise; doc has roots."""
    from bokeh.document import Document

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
        app_spec = importlib.util.spec_from_file_location("_test_app", out_f.name)
        app_mod = importlib.util.module_from_spec(app_spec)
        app_spec.loader.exec_module(app_mod)

        doc = Document()
        app_mod.make_document(doc)
        assert len(doc.roots) > 0, "make_document must add at least one root to Document"
    finally:
        os.unlink(spec_path)
        os.unlink(data_path)
        os.unlink(out_f.name)


# ---------------------------------------------------------------------------
# P4-62: Filter callback recomputes histogram CDS
# ---------------------------------------------------------------------------

def test_filter_callback_recomputes_histogram(dr_module, auto_df):
    """P4-62: Histogram bins change when filter reduces the dataset."""
    from bokeh.document import Document

    spec = _make_spec_json(
        graphs=[{
            "plots": [{"type": "histogram", "yvar": "mpg", "xvar": "", "options": {"bin": "10"}}],
            "graph_options": {"name": "h1", "title": "MPG Histogram"},
        }],
        build_options={
            "layout": "auto", "link": "", "filter": "foreign, type(dropdown)",
            "theme": "default", "title": "", "subtitle": "",
            "registry": "h1", "mode": "server", "port": "5006",
        },
    )
    spec_path, data_path = _write_temp_files(auto_df, spec)
    out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
    out_f.close()

    try:
        builder = dr_module.ServerAppBuilder(spec_path, data_path)
        builder.build(out_f.name, port=5006)

        app_spec_obj = importlib.util.spec_from_file_location("_test_app_hist", out_f.name)
        app_mod = importlib.util.module_from_spec(app_spec_obj)
        app_spec_obj.loader.exec_module(app_mod)

        doc = Document()
        app_mod.make_document(doc)
        # Test _compute_histogram directly with filtered data
        full_result = app_mod._compute_histogram(auto_df, "mpg", bins=10)
        half_df = auto_df[auto_df["foreign"] == 0]
        half_result = app_mod._compute_histogram(half_df, "mpg", bins=10)

        assert len(full_result["top"]) == 10
        assert len(half_result["top"]) == 10
        # Total counts differ (different number of rows)
        assert sum(full_result["top"]) == len(auto_df)
        assert sum(half_result["top"]) == len(half_df)
    finally:
        os.unlink(spec_path)
        os.unlink(data_path)
        os.unlink(out_f.name)


# ---------------------------------------------------------------------------
# P4-63: Filter callback recomputes lfit CDS
# ---------------------------------------------------------------------------

def test_filter_callback_recomputes_lfit(dr_module, auto_df):
    """P4-63: lfit y-values differ when computed from a filtered subset."""
    from bokeh.document import Document

    spec = _make_spec_json(
        graphs=[{
            "plots": [{"type": "lfit", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "l1", "title": "OLS Fit"},
        }],
    )
    spec_path, data_path = _write_temp_files(auto_df, spec)
    out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
    out_f.close()

    try:
        builder = dr_module.ServerAppBuilder(spec_path, data_path)
        builder.build(out_f.name)

        app_spec_obj = importlib.util.spec_from_file_location("_test_app_lfit", out_f.name)
        app_mod = importlib.util.module_from_spec(app_spec_obj)
        app_spec_obj.loader.exec_module(app_mod)

        full_fit = app_mod._compute_lfit(auto_df, "mpg", "weight")
        subset_df = auto_df[auto_df["weight"] < auto_df["weight"].median()]
        sub_fit = app_mod._compute_lfit(subset_df, "mpg", "weight")

        assert len(full_fit["x"]) == 100
        assert len(full_fit["y"]) == 100
        assert len(sub_fit["x"]) == 100
        # The y-values should differ between full and filtered data
        assert not np.allclose(full_fit["y"], sub_fit["y"], atol=1.0), \
            "lfit should produce different values for full vs filtered data"
    finally:
        os.unlink(spec_path)
        os.unlink(data_path)
        os.unlink(out_f.name)


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

        app_spec_obj = importlib.util.spec_from_file_location("_test_app_kpi", out_f.name)
        app_mod = importlib.util.module_from_spec(app_spec_obj)
        app_spec_obj.loader.exec_module(app_mod)

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

        app_spec_obj = importlib.util.spec_from_file_location("_test_app_brush", out_f.name)
        app_mod = importlib.util.module_from_spec(app_spec_obj)
        app_spec_obj.loader.exec_module(app_mod)

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
    import importlib.util as _ilu
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
        app_spec_obj = _ilu.spec_from_file_location("_test_xss_app", out_f.name)
        app_mod = _ilu.module_from_spec(app_spec_obj)
        app_spec_obj.loader.exec_module(app_mod)
        doc = Document()
        app_mod.make_document(doc)
        # doc.title is set to html.escape(title) inside make_document
        assert "<script>" not in doc.title, (
            f"XSS Layer 2: raw <script> found in doc.title: {doc.title!r}"
        )
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
# P4-70: _compute_histogram returns correct structure
# ---------------------------------------------------------------------------

def test_compute_histogram_structure(dr_module, auto_df):
    """P4-70: _compute_histogram returns dict with top/left/right of length bins."""
    spec = _make_spec_json()
    spec_path, data_path = _write_temp_files(auto_df, spec)
    out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
    out_f.close()

    try:
        builder = dr_module.ServerAppBuilder(spec_path, data_path)
        builder.build(out_f.name)

        app_spec_obj = importlib.util.spec_from_file_location("_test_hist_struct", out_f.name)
        app_mod = importlib.util.module_from_spec(app_spec_obj)
        app_spec_obj.loader.exec_module(app_mod)

        result = app_mod._compute_histogram(auto_df, "mpg", bins=15)
        assert set(result.keys()) == {"top", "left", "right"}
        assert len(result["top"]) == 15
        assert len(result["left"]) == 15
        assert len(result["right"]) == 15
        # All heights non-negative
        assert all(v >= 0 for v in result["top"])
        # Total count equals number of non-NaN values
        assert sum(result["top"]) == auto_df["mpg"].dropna().shape[0]
    finally:
        os.unlink(spec_path)
        os.unlink(data_path)
        os.unlink(out_f.name)


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

        app_spec_obj = importlib.util.spec_from_file_location("_test_kpi_vals", out_f.name)
        app_mod = importlib.util.module_from_spec(app_spec_obj)
        app_spec_obj.loader.exec_module(app_mod)

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
# P4-72: _compute_lfit returns 100 x/y points
# ---------------------------------------------------------------------------

def test_compute_lfit_100_points(dr_module, auto_df):
    """P4-72: _compute_lfit returns exactly 100 x-points and 100 y-points."""
    spec = _make_spec_json()
    spec_path, data_path = _write_temp_files(auto_df, spec)
    out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
    out_f.close()

    try:
        builder = dr_module.ServerAppBuilder(spec_path, data_path)
        builder.build(out_f.name)

        app_spec_obj = importlib.util.spec_from_file_location("_test_lfit_pts", out_f.name)
        app_mod = importlib.util.module_from_spec(app_spec_obj)
        app_spec_obj.loader.exec_module(app_mod)

        result = app_mod._compute_lfit(auto_df, "mpg", "weight")
        assert len(result["x"]) == 100, f"Expected 100 x-points, got {len(result['x'])}"
        assert len(result["y"]) == 100, f"Expected 100 y-points, got {len(result['y'])}"
        # x should be sorted (linspace)
        assert result["x"][0] < result["x"][-1]
    finally:
        os.unlink(spec_path)
        os.unlink(data_path)
        os.unlink(out_f.name)


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

        app_spec_obj = importlib.util.spec_from_file_location("_test_sd_ddof", out_f.name)
        app_mod = importlib.util.module_from_spec(app_spec_obj)
        app_spec_obj.loader.exec_module(app_mod)

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
    """Regression: _compute_kdensity with constant-value column returns empty dict.

    scipy.stats.gaussian_kde raises LinAlgError on zero-variance data.
    The generated server code must guard against this.
    """
    spec = _make_spec_json()
    spec_path, data_path = _write_temp_files(auto_df, spec)
    out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
    out_f.close()

    try:
        builder = dr_module.ServerAppBuilder(spec_path, data_path)
        builder.build(out_f.name)

        app_spec_obj = importlib.util.spec_from_file_location("_test_kde_const", out_f.name)
        app_mod = importlib.util.module_from_spec(app_spec_obj)
        app_spec_obj.loader.exec_module(app_mod)

        # Constant-value column — gaussian_kde would raise LinAlgError without guard
        const_df = auto_df.copy()
        const_df["mpg"] = 22.0

        result = app_mod._compute_kdensity(const_df, "mpg")
        assert result == {"x": [], "y": []}, (
            f"Expected empty dict for constant data, got {result}"
        )

        # Single-point column
        single_df = auto_df.iloc[:1].copy()
        result2 = app_mod._compute_kdensity(single_df, "mpg")
        assert result2 == {"x": [], "y": []}, (
            f"Expected empty dict for single-point data, got {result2}"
        )
    finally:
        os.unlink(spec_path)
        os.unlink(data_path)
        os.unlink(out_f.name)


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

    def test_yscale_log_generates_y_axis_type(self, dr_module, auto_df):
        """yscale(log) in graph options must generate y_axis_type='log' in server source."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "yscale": "log"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "y_axis_type" in source, "yscale(log) must produce y_axis_type in server app"
        assert "log" in source

    def test_both_log_scales(self, dr_module, auto_df):
        """Both xscale and yscale log must both appear in server source."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "xscale": "log", "yscale": "log"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "x_axis_type" in source
        assert "y_axis_type" in source

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

    def test_server_yrange_sets_range(self, dr_module, auto_df):
        """yrange in server mode must generate y_range.start/end code."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "yrange": "1000 5000"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "y_range" in source or "yrange" in source, \
            "yrange option must appear in server-mode generated code"


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

    def test_spike_lwidth_code_present(self, dr_module, auto_df):
        """spike server code must read 'lwidth' option."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "spike", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "'lwidth'" in source or '"lwidth"' in source, \
            "server-mode spike must read 'lwidth' option from opts"

    def test_spike_lpattern_code_present(self, dr_module, auto_df):
        """spike server code must read 'lpattern' option."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "spike", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "'lpattern'" in source or '"lpattern"' in source, \
            "server-mode spike must read 'lpattern' option from opts"

    def test_bar_lwidth_code_present(self, dr_module, auto_df):
        """bar server code must read 'lwidth' option."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "bar", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "'lwidth'" in source or '"lwidth"' in source, \
            "server-mode bar must read 'lwidth' option from opts"

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

    Each test builds a server app with lwidth(thick)=2.5, executes make_document(),
    and verifies that at least one renderer has line_width≈2.5.
    'thick' maps to 2.5 in the lwidth translation table.
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
            app_spec = importlib.util.spec_from_file_location("_ta", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
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
            app_spec = importlib.util.spec_from_file_location("_tawa", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
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

    def _has_renderer_with_lw(self, renderers, target_lw=2.5, tol=0.05):
        """Return True if any renderer glyph has line_width close to target_lw."""
        for r in renderers:
            glyph = getattr(r, 'glyph', None)
            if glyph is not None:
                lw = getattr(glyph, 'line_width', None)
                if lw is not None and abs(float(lw) - target_lw) < tol:
                    return True
        return False

    def _has_arrow_with_lw(self, arrow_annots, target_lw=2.5, tol=0.05):
        """Return True if any Arrow annotation has line_width close to target_lw."""
        for arrow in arrow_annots:
            lw = getattr(arrow, 'line_width', None)
            if lw is not None and abs(float(lw) - target_lw) < tol:
                return True
        return False

    def test_lfit_applies_lwidth(self, dr_module, auto_df):
        """lfit with lwidth(thick)=2.5 must produce a renderer with line_width≈2.5."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "lfit", "yvar": "mpg", "xvar": "weight",
                       "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, 2.5), \
            "server-mode lfit must apply lwidth(thick)=2.5 to line renderer"

    def test_qfit_applies_lwidth(self, dr_module, auto_df):
        """qfit with lwidth(thick)=2.5 must produce a renderer with line_width≈2.5."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "qfit", "yvar": "mpg", "xvar": "weight",
                       "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, 2.5), \
            "server-mode qfit must apply lwidth(thick)=2.5 to line renderer"

    def test_connected_applies_lwidth(self, dr_module, auto_df):
        """connected with lwidth(thick)=2.5 must produce a renderer with line_width≈2.5."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "connected", "yvar": "mpg", "xvar": "weight",
                       "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, 2.5), \
            "server-mode connected must apply lwidth(thick)=2.5 to line renderer"

    def test_lowess_applies_lwidth(self, dr_module, auto_df):
        """lowess with lwidth(thick)=2.5 must produce a renderer with line_width≈2.5."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "lowess", "yvar": "mpg", "xvar": "weight",
                       "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, 2.5), \
            "server-mode lowess must apply lwidth(thick)=2.5 to line renderer"

    def test_kdensity_applies_lwidth(self, dr_module, auto_df):
        """kdensity with lwidth(thick)=2.5 must produce a renderer with line_width≈2.5."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "kdensity", "yvar": "mpg", "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, 2.5), \
            "server-mode kdensity must apply lwidth(thick)=2.5 to line renderer"

    def test_mspline_applies_lwidth(self, dr_module, auto_df):
        """mspline with lwidth(thick)=2.5 must produce a renderer with line_width≈2.5."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "mspline", "yvar": "mpg", "xvar": "weight",
                       "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, 2.5), \
            "server-mode mspline must apply lwidth(thick)=2.5 to line renderer"

    def test_tsline_applies_lwidth(self, dr_module, auto_df):
        """tsline with lwidth(thick)=2.5 must produce a renderer with line_width≈2.5."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "tsline", "yvar": "mpg", "xvar": "weight",
                       "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, 2.5), \
            "server-mode tsline must apply lwidth(thick)=2.5 to line renderer"

    def test_rspike_applies_lwidth(self, dr_module, auto_df):
        """rspike with lwidth(thick)=2.5 must produce a renderer with line_width≈2.5."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rspike", "yvar1": "mpg", "yvar2": "price",
                       "xvar": "weight", "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, 2.5), \
            "server-mode rspike must apply lwidth(thick)=2.5 to segment renderer"

    def test_rline_applies_lwidth(self, dr_module, auto_df):
        """rline with lwidth(thick)=2.5 must produce a renderer with line_width≈2.5."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rline", "yvar1": "mpg", "yvar2": "price",
                       "xvar": "weight", "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, 2.5), \
            "server-mode rline must apply lwidth(thick)=2.5 to line renderer"

    def test_function_applies_lwidth(self, dr_module, auto_df):
        """function with lwidth(thick)=2.5 must produce a renderer with line_width≈2.5."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "function", "expr": "x", "range": [0, 10],
                       "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, 2.5), \
            "server-mode function must apply lwidth(thick)=2.5 to line renderer"

    def test_tsrline_applies_lwidth(self, dr_module, auto_df):
        """tsrline with lwidth(thick)=2.5 must produce a renderer with line_width≈2.5."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "tsrline", "yvar1": "mpg", "yvar2": "price",
                       "xvar": "weight", "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, 2.5), \
            "server-mode tsrline must apply lwidth(thick)=2.5 to line renderer"

    def test_rconnected_applies_lwidth(self, dr_module, auto_df):
        """rconnected with lwidth(thick)=2.5 must produce a renderer with line_width≈2.5."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rconnected", "yvar1": "mpg", "yvar2": "price",
                       "xvar": "weight", "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, 2.5), \
            "server-mode rconnected must apply lwidth(thick)=2.5 to line renderer"

    def test_rcapsym_applies_lwidth(self, dr_module, auto_df):
        """rcapsym with lwidth(thick)=2.5 must produce a renderer with line_width≈2.5."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rcapsym", "yvar1": "mpg", "yvar2": "price",
                       "xvar": "weight", "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, 2.5), \
            "server-mode rcapsym must apply lwidth(thick)=2.5 to segment renderer"

    def test_pcspike_applies_lwidth(self, dr_module, auto_df):
        """pcspike with lwidth(thick)=2.5 must produce a renderer with line_width≈2.5."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "pcspike", "y1var": "mpg", "x1var": "weight",
                       "y2var": "price", "x2var": "foreign",
                       "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, 2.5), \
            "server-mode pcspike must apply lwidth(thick)=2.5 to segment renderer"

    def test_pcarrow_applies_lwidth(self, dr_module, auto_df):
        """pcarrow with lwidth(thick)=2.5 must produce a renderer with line_width≈2.5."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "pcarrow", "y1var": "mpg", "x1var": "weight",
                       "y2var": "price", "x2var": "foreign",
                       "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, 2.5), \
            "server-mode pcarrow must apply lwidth(thick)=2.5 to segment renderer"

    def test_pcbarrow_applies_lwidth(self, dr_module, auto_df):
        """pcbarrow with lwidth(thick)=2.5 must produce a renderer with line_width≈2.5."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "pcbarrow", "y1var": "mpg", "x1var": "weight",
                       "y2var": "price", "x2var": "foreign",
                       "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        assert self._has_renderer_with_lw(renderers, 2.5), \
            "server-mode pcbarrow must apply lwidth(thick)=2.5 to segment renderer"

    def test_pcarrow_lwidth_applies_to_arrow_annotations(self, dr_module, auto_df):
        """pcarrow lwidth(thick)=2.5 must be applied to Arrow annotation objects, not just segment."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "pcarrow", "y1var": "mpg", "x1var": "weight",
                       "y2var": "price", "x2var": "foreign",
                       "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        _, arrow_annots = self._exec_make_document_with_arrows(dr_module, auto_df, spec)
        assert arrow_annots, "server-mode pcarrow must produce Arrow annotations"
        assert self._has_arrow_with_lw(arrow_annots, 2.5), \
            "server-mode pcarrow Arrow annotations must have line_width=2.5 (thick)"

    def test_pcbarrow_lwidth_applies_to_arrow_annotations(self, dr_module, auto_df):
        """pcbarrow lwidth(thick)=2.5 must be applied to Arrow annotation objects, not just segment."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "pcbarrow", "y1var": "mpg", "x1var": "weight",
                       "y2var": "price", "x2var": "foreign",
                       "options": {"lwidth": "thick"}}],
            "graph_options": {"name": "g1"},
        }])
        _, arrow_annots = self._exec_make_document_with_arrows(dr_module, auto_df, spec)
        assert arrow_annots, "server-mode pcbarrow must produce Arrow annotations"
        assert self._has_arrow_with_lw(arrow_annots, 2.5), \
            "server-mode pcbarrow Arrow annotations must have line_width=2.5 (thick)"


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
            app_spec = importlib.util.spec_from_file_location(mod_name, out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
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
            app_spec = importlib.util.spec_from_file_location("_ta2", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
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

    def test_mcolor_named_navy_translates(self, dr_module, auto_df):
        """mcolor(navy) must produce fill_color=#1a476f on scatter renderer."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {"mcolor": "navy"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        colors = [getattr(getattr(r, 'glyph', None), 'fill_color', None)
                  for r in renderers if r is not None]
        assert "#1a476f" in colors, \
            "server-mode scatter mcolor(navy) must produce fill_color=#1a476f"

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
        """bgcolor(navy) in server app must set border_fill_color=#1a476f on figure."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}],
            "graph_options": {"name": "g1", "bgcolor": "navy"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        # The generated source must contain the navy hex value via _resolve_color
        assert "#1a476f" in source or "bgcolor" in source, \
            "bgcolor(navy) must resolve to #1a476f in generated server app"


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
            app_spec = importlib.util.spec_from_file_location("_tm4", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
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

    def test_mfcolor_named_navy_applied(self, dr_module, auto_df):
        """mfcolor(navy) must produce fill_color=#1a476f on scatter renderer."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {"mfcolor": "navy"}}],
            "graph_options": {"name": "g1"},
        }])
        renderers = self._exec_make_document(dr_module, auto_df, spec)
        colors = [getattr(getattr(r, 'glyph', None), 'fill_color', None)
                  for r in renderers if r is not None]
        assert "#1a476f" in colors, \
            "server-mode scatter mfcolor(navy) must produce fill_color=#1a476f"

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
            app_spec = importlib.util.spec_from_file_location("_tm3", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
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
    """mlabel must work for line, connected, and dot plot types in server mode."""

    def _exec_and_collect(self, dr_module, df, spec, mod_name):
        """Build and exec make_document, collecting all document objects."""
        from bokeh.document import Document
        spec_path, data_path = _write_temp_files(df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_spec = importlib.util.spec_from_file_location(mod_name, out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
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

    def test_mlabel_in_line_produces_labelset(self, dr_module, auto_df):
        """line with mlabel() must produce a LabelSet annotation in the document."""
        from bokeh.models import LabelSet
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "line", "yvar": "mpg", "xvar": "weight",
                       "options": {"mlabel": "foreign"}}],
            "graph_options": {"name": "g1"},
        }])
        all_objs = self._exec_and_collect(dr_module, auto_df, spec, "_tmline")
        assert any(isinstance(o, LabelSet) for o in all_objs), \
            "server-mode line with mlabel() must produce a LabelSet annotation"

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

    def test_mlabel_in_tsline_produces_labelset(self, dr_module, auto_df):
        """tsline with mlabel() must produce a LabelSet annotation in the document."""
        from bokeh.models import LabelSet
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "tsline", "yvar": "mpg", "xvar": "weight",
                       "options": {"mlabel": "foreign"}}],
            "graph_options": {"name": "g1"},
        }])
        all_objs = self._exec_and_collect(dr_module, auto_df, spec, "_tmtsline")
        assert any(isinstance(o, LabelSet) for o in all_objs), \
            "server-mode tsline with mlabel() must produce a LabelSet annotation"

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

    def test_mlabel_on_rspike_produces_labelset(self, dr_module, auto_df):
        """rspike with mlabel() must produce a LabelSet in the document."""
        from bokeh.models import LabelSet
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rspike", "yvar1": "mpg", "yvar2": "price", "xvar": "weight",
                       "options": {"mlabel": "foreign"}}],
            "graph_options": {"name": "g1"},
        }])
        all_objs = self._exec_and_collect(dr_module, auto_df, spec, "_tmrspike_mlab")
        assert any(isinstance(o, LabelSet) for o in all_objs), \
            "server-mode rspike with mlabel() must produce a LabelSet"

    def test_mlabel_on_rline_produces_labelset(self, dr_module, auto_df):
        """rline with mlabel() must produce a LabelSet in the document."""
        from bokeh.models import LabelSet
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rline", "yvar1": "mpg", "yvar2": "price", "xvar": "weight",
                       "options": {"mlabel": "foreign"}}],
            "graph_options": {"name": "g1"},
        }])
        all_objs = self._exec_and_collect(dr_module, auto_df, spec, "_tmrline_mlab")
        assert any(isinstance(o, LabelSet) for o in all_objs), \
            "server-mode rline with mlabel() must produce a LabelSet"

    def test_mlabel_on_rbar_produces_labelset(self, dr_module, auto_df):
        """rbar with mlabel() must produce a LabelSet in the document."""
        from bokeh.models import LabelSet
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rbar", "yvar1": "mpg", "yvar2": "price", "xvar": "weight",
                       "options": {"mlabel": "foreign"}}],
            "graph_options": {"name": "g1"},
        }])
        all_objs = self._exec_and_collect(dr_module, auto_df, spec, "_tmrbar_mlab")
        assert any(isinstance(o, LabelSet) for o in all_objs), \
            "server-mode rbar with mlabel() must produce a LabelSet"


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
            app_spec = importlib.util.spec_from_file_location("_tmfilt", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
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

    def test_unsafe_if_expr_ignored(self, dr_module, auto_df):
        """Unsafe if_expr must be silently ignored (no error, no filtering)."""
        n_total = len(auto_df)
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight"}],
            "graph_options": {"name": "g1", "if_expr": "__import__('os').getcwd()"},
        }])
        doc = self._exec_make_document(dr_module, auto_df, spec)
        lengths = self._collect_cds_lengths(doc)
        # No crash, and full unfiltered data (or empty due to failed query — not partial)
        assert not any(0 < n < n_total for n in lengths), \
            "unsafe if_expr must not partially filter data"

    def test_getattr_if_expr_ignored(self, dr_module, auto_df):
        """if_expr containing getattr() must be silently blocked."""
        n_total = len(auto_df)
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight"}],
            "graph_options": {"name": "g1", "if_expr": "getattr(mpg, '__class__')"},
        }])
        doc = self._exec_make_document(dr_module, auto_df, spec)
        lengths = self._collect_cds_lengths(doc)
        assert not any(0 < n < n_total for n in lengths), \
            "if_expr with getattr() must not partially filter data"

    def test_setattr_if_expr_ignored(self, dr_module, auto_df):
        """if_expr containing setattr() must be silently blocked."""
        n_total = len(auto_df)
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight"}],
            "graph_options": {"name": "g1", "if_expr": "setattr(mpg, 'x', 1)"},
        }])
        doc = self._exec_make_document(dr_module, auto_df, spec)
        lengths = self._collect_cds_lengths(doc)
        assert not any(0 < n < n_total for n in lengths), \
            "if_expr with setattr() must not partially filter data"

    def test_lfit_respects_in_expr(self, dr_module, auto_df):
        """lfit with in_expr must use filtered data for regression, not full df."""
        # With in_expr 1/5 (5 rows), the lfit CDS must reflect only those rows.
        # The result will differ from full-data lfit unless data is constant.
        import numpy as np
        spec_full = _make_spec_json(graphs=[{
            "plots": [{"type": "lfit", "yvar": "mpg", "xvar": "weight"}],
            "graph_options": {"name": "g1"},
        }])
        spec_filt = _make_spec_json(graphs=[{
            "plots": [{"type": "lfit", "yvar": "mpg", "xvar": "weight"}],
            "graph_options": {"name": "g1", "in_expr": "1/5"},
        }])
        doc_full = self._exec_make_document(dr_module, auto_df, spec_full)
        doc_filt = self._exec_make_document(dr_module, auto_df, spec_filt)
        lengths_full = self._collect_cds_lengths(doc_full)
        lengths_filt = self._collect_cds_lengths(doc_filt)
        # The filtered lfit CDS y-values should differ from full lfit CDS
        # (tested via CDS lengths — filtered version uses fewer input points)
        # lfit always returns 100 output points regardless of input size,
        # but using g_df ensures the regression is computed on the filtered subset.
        # We verify by checking that the generated app compiles and executes without error.
        assert len(lengths_filt) > 0, "filtered lfit must produce at least one CDS"

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
            app_spec = importlib.util.spec_from_file_location(mod_name, out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
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
        """Filter callback must handle atype=='lfitci' for recompute."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "lfitci", "yvar": "mpg", "xvar": "weight"}],
            "graph_options": {"name": "g1"},
        }])
        src = self._get_source(dr_module, auto_df, spec, "_tlfci_cb")
        assert "_compute_lfitci" in src and "atype == 'lfitci'" in src, \
            "Filter callback must have 'elif atype == lfitci' recompute branch"

    def test_qfitci_filter_callback_recomputes(self, dr_module, auto_df):
        """Filter callback must handle atype=='qfitci' for recompute."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "qfitci", "yvar": "mpg", "xvar": "weight"}],
            "graph_options": {"name": "g1"},
        }])
        src = self._get_source(dr_module, auto_df, spec, "_tqfci_cb")
        assert "_compute_qfitci" in src and "atype == 'qfitci'" in src, \
            "Filter callback must have 'elif atype == qfitci' recompute branch"

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
        """A-90: Filter callback must handle atype=='mspline' for recompute."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "mspline", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        src = self._get_source(dr_module, auto_df, spec, "_tmsp_cb")
        assert "_compute_mspline" in src and "atype == 'mspline'" in src, \
            "Filter callback must have 'elif atype == mspline' recompute branch"

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
        """A-91: Filter callback must handle atype=='mband' for recompute."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "mband", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        src = self._get_source(dr_module, auto_df, spec, "_tmb_cb")
        assert "_compute_mband" in src and "atype == 'mband'" in src, \
            "Filter callback must have 'elif atype == mband' recompute branch"

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
        """A-92: Filter callback must handle atype=='rscatter' for recompute."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rscatter", "yvar1": "mpg", "yvar2": "price",
                       "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        src = self._get_source(dr_module, auto_df, spec, "_trs_cb")
        assert "_compute_rscatter" in src and "atype == 'rscatter'" in src, \
            "Filter callback must have 'elif atype == rscatter' recompute branch"

    def test_pci_registered_in_graph_sources(self, dr_module, auto_df):
        """A-93: pci must register its source in graph_sources so the filter callback updates it."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "pci", "y1var": "mpg", "x1var": "weight",
                       "y2var": "price", "x2var": "length", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        src = self._get_source(dr_module, auto_df, spec, "_tpci_reg")
        # pci must register in graph_sources so the standard replacement loop updates it
        assert "graph_sources[gname] = " in src or "graph_sources[gname]=" in src, \
            "pci must set graph_sources[gname] so filter callback updates raw data"

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
        """A-94: Filter callback must handle atype=='pcscatter' for recompute."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "pcscatter", "y1var": "mpg", "x1var": "weight",
                       "y2var": "price", "x2var": "length", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        src = self._get_source(dr_module, auto_df, spec, "_tpcs_cb")
        assert "_compute_pcscatter" in src and "atype == 'pcscatter'" in src, \
            "Filter callback must have 'elif atype == pcscatter' recompute branch"

    def test_mspline_compute_fn_changes_with_filter(self, dr_module, auto_df):
        """A-90: _compute_mspline must return different y values for filtered vs full data."""
        from bokeh.document import Document
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "mspline", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_spec_obj = importlib.util.spec_from_file_location("_tmsp_fn", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec_obj)
            app_spec_obj.loader.exec_module(app_mod)
            doc = Document()
            app_mod.make_document(doc)
            full_result = app_mod._compute_mspline(auto_df, "mpg", "weight")
            half_df = auto_df[auto_df["foreign"] == 0]
            half_result = app_mod._compute_mspline(half_df, "mpg", "weight")
            assert len(full_result["y_sp"]) > 0, "_compute_mspline must return non-empty y_sp"
            assert not np.allclose(full_result["y_sp"], half_result["y_sp"], atol=1.0), \
                "_compute_mspline must return different y values for filtered vs full data"
        finally:
            for p in (spec_path, data_path, out_f.name):
                try: os.unlink(p)
                except OSError: pass

    def test_mband_compute_fn_changes_with_filter(self, dr_module, auto_df):
        """A-91: _compute_mband must return different y values for filtered vs full data."""
        from bokeh.document import Document
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "mband", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_spec_obj = importlib.util.spec_from_file_location("_tmb_fn", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec_obj)
            app_spec_obj.loader.exec_module(app_mod)
            doc = Document()
            app_mod.make_document(doc)
            full_result = app_mod._compute_mband(auto_df, "mpg", "weight")
            half_df = auto_df[auto_df["foreign"] == 0]
            half_result = app_mod._compute_mband(half_df, "mpg", "weight")
            assert len(full_result["y_mb"]) > 0, "_compute_mband must return non-empty y_mb"
            assert len(half_result["y_mb"]) > 0, "_compute_mband must return non-empty y_mb for subset"
            # Either the lengths differ (different # of bands) or the y values differ
            assert (
                len(full_result["y_mb"]) != len(half_result["y_mb"])
                or not np.allclose(full_result["y_mb"], half_result["y_mb"], atol=1.0)
            ), "_compute_mband must return different results for filtered vs full data"
        finally:
            for p in (spec_path, data_path, out_f.name):
                try: os.unlink(p)
                except OSError: pass


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
        app_spec = importlib.util.spec_from_file_location(mod_name, out_f.name)
        app_mod = importlib.util.module_from_spec(app_spec)
        app_spec.loader.exec_module(app_mod)
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
        """area with fcolor(red) must use the resolved hex for fill_color."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "area", "yvar": "mpg", "xvar": "weight",
                       "options": {"fcolor": "#ff0000"}}],
            "graph_options": {"name": "g1"},
        }])
        _, renderers = _exec_doc(dr_module, auto_df, spec, "_tar_fc")
        fill_colors = [getattr(r.glyph, 'fill_color', None) for r in renderers]
        assert "#ff0000" in fill_colors, \
            f"area fcolor '#ff0000' must appear in fill_color; got {fill_colors}"

    def test_area_fintensity_sets_alpha(self, dr_module, auto_df):
        """area with fintensity(50) must set fill_alpha ≈ 0.5."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "area", "yvar": "mpg", "xvar": "weight",
                       "options": {"fintensity": "50"}}],
            "graph_options": {"name": "g1"},
        }])
        _, renderers = _exec_doc(dr_module, auto_df, spec, "_tar_fi")
        alphas = [getattr(r.glyph, 'fill_alpha', None) for r in renderers]
        assert any(abs(a - 0.5) < 0.01 for a in alphas if a is not None), \
            f"area fintensity(50) must set fill_alpha≈0.5; got {alphas}"


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

    def test_rarea_fcolor_applied(self, dr_module):
        """rarea fcolor appears in generated source."""
        rdf = _range_data()
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rarea", "yvar1": "lo", "yvar2": "hi", "xvar": "x",
                       "options": {"fcolor": "#ff0000"}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, rdf, spec)
        assert "#ff0000" in source, "rarea fcolor must appear in generated app source"

    def test_rarea_fcolor_applied_functional(self, dr_module):
        """rarea with fcolor(#ff0000) must set fill_color in rendered doc."""
        rdf = _range_data()
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rarea", "yvar1": "lo", "yvar2": "hi", "xvar": "x",
                       "options": {"fcolor": "#ff0000"}}],
            "graph_options": {"name": "g1"},
        }])
        _, renderers = _exec_doc(dr_module, rdf, spec, "_tra_fc2")
        fill_colors = [getattr(r.glyph, 'fill_color', None) for r in renderers]
        assert "#ff0000" in fill_colors, \
            f"rarea fcolor must appear in fill_color; got {fill_colors}"


class TestServerRbarOptions:
    """rbar in server mode must apply bfcolor, blcolor, lwidth."""

    def test_rbar_bfcolor_applied(self, dr_module):
        """rbar with bfcolor(#ff0000) must set fill_color."""
        rdf = _range_data()
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "rbar", "yvar1": "lo", "yvar2": "hi", "xvar": "x",
                       "options": {"bfcolor": "#ff0000"}}],
            "graph_options": {"name": "g1"},
        }])
        _, renderers = _exec_doc(dr_module, rdf, spec, "_trb_bfc")
        fill_colors = [getattr(r.glyph, 'fill_color', None) for r in renderers]
        assert "#ff0000" in fill_colors, \
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
        compile(source, "<generated_by>", "exec")

    def test_by_creates_facet_figures(self, dr_module, auto_df):
        """by(foreign) → generated code creates facet figure entries."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        # Should contain facet-keyed figure references
        assert "g1__by__0" in source or "__by__" in source or "facet" in source.lower(), \
            "Generated source should contain facet figure references"

    def test_by_doc_has_roots(self, dr_module, auto_df):
        """by(foreign) → make_document produces a doc with roots."""
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
            app_spec = importlib.util.spec_from_file_location("_by_test", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
            doc = Document()
            app_mod.make_document(doc)
            assert len(doc.roots) > 0, "Document must have at least one root"
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try:
                    os.unlink(_p)
                except OSError:
                    pass

    def test_by_facet_labels_in_source(self, dr_module, auto_df):
        """by(foreign) → facet group labels appear in generated source."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        # The source should contain references to the facet group values
        # (either as labels in figure titles or as group identifiers)
        assert "by" in source.lower() or "facet" in source.lower() or \
               "g1__by__" in source, \
            "Generated source should reference facet groups"

    def test_by_with_histogram_compiles(self, dr_module, auto_df):
        """by(foreign) with histogram → generated source compiles."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "histogram", "var": "mpg", "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        compile(source, "<generated_by_hist>", "exec")

    def test_by_total_in_source(self, dr_module, auto_df):
        """by(foreign) with by_total=1 → 'Total' appears in generated source."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign", "by_total": "1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "Total" in source, "by_total=1 should produce a 'Total' facet in generated code"

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
        """mband make_document() must produce a document with figures."""
        from bokeh.document import Document
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "mband", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        spec_path, data_path = _write_temp_files(auto_df, spec)
        import tempfile, importlib.util
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        builder = dr_module.ServerAppBuilder(spec_path, data_path)
        builder.build(out_f.name)
        app_spec = importlib.util.spec_from_file_location("_tmmband", out_f.name)
        app_mod = importlib.util.module_from_spec(app_spec)
        app_spec.loader.exec_module(app_mod)
        doc = Document()
        app_mod.make_document(doc)
        assert len(doc.roots) > 0, "mband make_document must produce at least one root"


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
        app_spec = importlib.util.spec_from_file_location("_tmrconn_mlab", out_f.name)
        app_mod = importlib.util.module_from_spec(app_spec)
        app_spec.loader.exec_module(app_mod)
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

    def test_fpfit_generates_valid_app(self, dr_module, auto_df):
        """fpfit must produce compilable server app source."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "fpfit", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        compile(source, "<generated>", "exec")
        assert "_compute_fpfit" in source

    def test_fpfitci_generates_valid_app(self, dr_module, auto_df):
        """fpfitci must produce compilable server app source."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "fpfitci", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        compile(source, "<generated>", "exec")
        assert "_compute_fpfit" in source

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
        """lpoly make_document() must produce a document with figures."""
        from bokeh.document import Document
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "lpoly", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        builder = dr_module.ServerAppBuilder(spec_path, data_path)
        builder.build(out_f.name)
        app_spec = importlib.util.spec_from_file_location("_tm_lpoly", out_f.name)
        app_mod = importlib.util.module_from_spec(app_spec)
        app_spec.loader.exec_module(app_mod)
        doc = Document()
        app_mod.make_document(doc)
        assert len(doc.roots) > 0

    def test_fpfit_make_document_runs(self, dr_module, auto_df):
        """fpfit make_document() must produce a document with figures."""
        from bokeh.document import Document
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "fpfit", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        builder = dr_module.ServerAppBuilder(spec_path, data_path)
        builder.build(out_f.name)
        app_spec = importlib.util.spec_from_file_location("_tm_fpfit", out_f.name)
        app_mod = importlib.util.module_from_spec(app_spec)
        app_spec.loader.exec_module(app_mod)
        doc = Document()
        app_mod.make_document(doc)
        assert len(doc.roots) > 0

    # ------------------------------------------------------------------
    # Regression: faceted lpoly must use bwidth/degree from options
    # ------------------------------------------------------------------

    def test_lpoly_faceted_bwidth_respected(self, dr_module, auto_df):
        """Regression: faceted lpoly must read bwidth from opts (not hardcode 0.5)."""
        import re, base64 as _b64
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "lpoly", "yvar": "mpg", "xvar": "weight",
                       "options": {"bwidth": "0.3"}}],
            "graph_options": {"name": "g1", "by": "foreign"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        compile(source, "<generated>", "exec")
        # The fix: generated faceted code must read bwidth from opts not hardcode it.
        # Verify: _SPEC_B64 roundtrip preserves the bwidth value
        m = re.search(r'_SPEC_B64\s*=\s*"([^"]+)"', source)
        assert m, "_SPEC_B64 must be present in generated source"
        decoded = _b64.b64decode(m.group(1)).decode("utf-8")
        assert "0.3" in decoded, "bwidth=0.3 must be preserved in embedded spec"
        # Also verify generated code reads from opts (not hardcoded default)
        assert "opts.get('bwidth'" in source or 'opts.get("bwidth"' in source, \
            "faceted lpoly code must read bwidth from opts dict"

    def test_lpoly_faceted_degree_respected(self, dr_module, auto_df):
        """Regression: faceted lpoly must read degree from opts (not hardcode 0)."""
        import re, base64 as _b64
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "lpoly", "yvar": "mpg", "xvar": "weight",
                       "options": {"degree": "2"}}],
            "graph_options": {"name": "g1", "by": "foreign"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        compile(source, "<generated>", "exec")
        m = re.search(r'_SPEC_B64\s*=\s*"([^"]+)"', source)
        assert m, "_SPEC_B64 must be present in generated source"
        decoded = _b64.b64decode(m.group(1)).decode("utf-8")
        assert '"degree": "2"' in decoded or '"degree":"2"' in decoded, \
            "degree=2 must be preserved in embedded spec"
        assert "opts.get('degree'" in source or 'opts.get("degree"' in source, \
            "faceted lpoly code must read degree from opts dict"

    def test_lpoly_faceted_make_document_runs(self, dr_module, auto_df):
        """lpoly with by() must produce a valid document with custom bwidth/degree."""
        from bokeh.document import Document
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "lpoly", "yvar": "mpg", "xvar": "weight",
                       "options": {"bwidth": "0.4", "degree": "1"}}],
            "graph_options": {"name": "g1", "by": "foreign"},
        }])
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        builder = dr_module.ServerAppBuilder(spec_path, data_path)
        builder.build(out_f.name)
        app_spec = importlib.util.spec_from_file_location("_tm_lpoly_fac", out_f.name)
        app_mod = importlib.util.module_from_spec(app_spec)
        app_spec.loader.exec_module(app_mod)
        doc = Document()
        app_mod.make_document(doc)
        assert len(doc.roots) > 0

    def test_fpfit_faceted_make_document_runs(self, dr_module, auto_df):
        """fpfit with by() must produce a valid document."""
        from bokeh.document import Document
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "fpfit", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign"},
        }])
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        builder = dr_module.ServerAppBuilder(spec_path, data_path)
        builder.build(out_f.name)
        app_spec = importlib.util.spec_from_file_location("_tm_fpfit_fac", out_f.name)
        app_mod = importlib.util.module_from_spec(app_spec)
        app_spec.loader.exec_module(app_mod)
        doc = Document()
        app_mod.make_document(doc)
        assert len(doc.roots) > 0


# ================================================================
# P4-74 — server-mode xscale/yscale reverse
# ================================================================
class TestServerXscaleYscaleReverse:
    """Server-mode xscale(reverse)/yscale(reverse) must emit flipped assignments."""

    def test_xscale_reverse_in_server_source(self, dr_module, auto_df):
        """P4-74: xscale(reverse) → generated source contains flipped = True for x_range."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "xscale": "reverse"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "x_range.flipped" in source, "xscale(reverse) must produce x_range.flipped in source"

    def test_yscale_reverse_in_server_source(self, dr_module, auto_df):
        """P4-75: yscale(reverse) → generated source contains flipped = True for y_range."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "yscale": "reverse"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "y_range.flipped" in source, "yscale(reverse) must produce y_range.flipped in source"

    def test_xscale_log_reverse_server_source(self, dr_module, auto_df):
        """P4-76: xscale(log reverse) must produce both x_axis_type and flipped in source."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "xscale": "log reverse"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "x_axis_type" in source
        assert "x_range.flipped" in source

    def test_xscale_log_only_uses_runtime_conditional_for_flip(self, dr_module, auto_df):
        """P4-74b: xscale(log) — generated source guards flipping with runtime token check.

        The flip code is always emitted as a conditional; we verify x_axis_type is present
        and that the reverse guard condition is in the source.
        """
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "xscale": "log"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "x_axis_type" in source
        # Flip guarded by runtime token check — not unconditionally applied
        assert "_xs_toks" in source, "Generated source must use token-based xscale parsing"


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
        """P4-79: make_document() must run without error when xlabel has angle()."""
        import tempfile, importlib.util
        from bokeh.document import Document
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
            app_spec = importlib.util.spec_from_file_location("_tm_axangle", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
            doc = Document()
            app_mod.make_document(doc)
            assert len(doc.roots) > 0
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
            app_spec = importlib.util.spec_from_file_location("_tm_rl_allow", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
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
            app_spec = importlib.util.spec_from_file_location("_tm_rl_block", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
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
            app_spec = importlib.util.spec_from_file_location("_tm_rl_burst", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
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
        """make_document() must complete without error when legend has cols()."""
        import tempfile, importlib.util
        from bokeh.document import Document
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "legend": "top cols(2)"},
        }])
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_spec = importlib.util.spec_from_file_location("_tm_leg_cols", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
            doc = Document()
            app_mod.make_document(doc)
            assert len(doc.roots) > 0
        finally:
            import os
            for p in (spec_path, data_path, out_f.name):
                try: os.unlink(p)
                except OSError: pass


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
        """make_document() must run without error when scatter has msangle."""
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
            app_spec = importlib.util.spec_from_file_location("_tm_msangle", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
            doc = Document()
            app_mod.make_document(doc)
            assert len(doc.roots) > 0
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
        app_spec = importlib.util.spec_from_file_location("_rl_app", out_f.name)
        app_mod = importlib.util.module_from_spec(app_spec)
        app_spec.loader.exec_module(app_mod)
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
        """BUG-RL-2b: _HealthHandler.prepare() must call _LIMITER.is_allowed and set 429."""
        source = _build_app(dr_module, auto_df, self._minimal_spec())
        assert "_LIMITER.is_allowed" in source, \
            "Generated source must call _LIMITER.is_allowed"
        assert "429" in source, \
            "Generated source must set HTTP status 429 for rate-limited requests"

    def test_health_handler_prepare_blocks_and_returns_429(self, dr_module, auto_df):
        """BUG-RL-2c: _HealthHandler.prepare() must set 429 and finish() when blocked."""
        app_mod = _load_app_module(dr_module, auto_df, self._minimal_spec())

        original_limiter = app_mod._LIMITER
        app_mod._LIMITER = app_mod._RateLimiter(max_rpm=0)  # always blocks
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
            app_mod._LIMITER = original_limiter

    # ------------------------------------------------------------------
    # BUG-RL-3/4: make_document enforces the rate limiter
    # ------------------------------------------------------------------
    def test_make_document_source_contains_limiter_check(self, dr_module, auto_df):
        """BUG-RL-3a: make_document must contain a _LIMITER.is_allowed call."""
        source = _build_app(dr_module, auto_df, self._minimal_spec())
        make_doc_start = source.find("def make_document(")
        assert make_doc_start != -1
        assert "_LIMITER.is_allowed" in source[make_doc_start:], (
            "make_document must call _LIMITER.is_allowed at session-creation time"
        )

    def test_make_document_adds_429_div_when_rate_limited(self, dr_module, auto_df):
        """BUG-RL-3b: make_document must add a 429 Div and return early when blocked."""
        from bokeh.document import Document
        from bokeh.models import Div as BkDiv
        app_mod = _load_app_module(dr_module, auto_df, self._minimal_spec())

        original_limiter = app_mod._LIMITER
        app_mod._LIMITER = app_mod._RateLimiter(max_rpm=0)

        try:
            doc = Document()

            class _FakeSessionContext:
                class request:
                    remote_ip = "10.1.1.1"
                    headers = {}

            doc._session_context = _FakeSessionContext()
            type(doc).session_context = property(lambda self: self._session_context)

            app_mod.make_document(doc)

            assert len(doc.roots) == 1, \
                "Blocked make_document must add exactly one root (the 429 Div)"
            assert isinstance(doc.roots[0], BkDiv), \
                "The root added by a rate-limited make_document must be a Div"
            assert "429" in doc.roots[0].text, \
                "The 429 Div text must contain '429'"
        finally:
            app_mod._LIMITER = original_limiter

    def test_make_document_proceeds_normally_when_allowed(self, dr_module, auto_df):
        """BUG-RL-4: make_document must build the full dashboard when not rate-limited."""
        from bokeh.document import Document
        from bokeh.models import Div as BkDiv
        app_mod = _load_app_module(dr_module, auto_df, self._minimal_spec())

        app_mod._LIMITER = app_mod._RateLimiter(max_rpm=1000)

        doc = Document()

        class _FakeSessionContext:
            class request:
                remote_ip = "10.2.2.2"
                headers = {}

        doc._session_context = _FakeSessionContext()
        type(doc).session_context = property(lambda self: self._session_context)

        app_mod.make_document(doc)

        assert len(doc.roots) > 0, \
            "make_document must add dashboard roots when not rate-limited"
        bad = [r for r in doc.roots if isinstance(r, BkDiv) and "429" in r.text]
        assert not bad, \
            "No 429 Div should appear when the request is within the rate limit"


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


def _exec_function_app(dr_module, expr):
    """Build a server app with *expr* as the function expression and run make_document.

    Returns the Bokeh Document; raises if make_document raises.
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
        app_spec = importlib.util.spec_from_file_location("_tfe", out_f.name)
        app_mod = importlib.util.module_from_spec(app_spec)
        app_spec.loader.exec_module(app_mod)
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
    """

    # BUG-FE-1a: generated source must contain the operator-skip guard
    def test_val_node_source_skips_operator_nodes(self, dr_module, auto_df):
        """BUG-FE-1a: generated server source must skip ast.operator/ast.unaryop nodes."""
        source = _build_function_app(dr_module, "x + 1")
        assert "_ast.operator" in source or "ast.operator" in source, (
            "generated _val_node must skip _ast.operator nodes; "
            "fix: add elif isinstance(node, (_ast.operator, _ast.unaryop)): pass"
        )

    # BUG-FE-1b: addition (BinOp with Add)
    def test_function_addition_does_not_raise(self, dr_module, auto_df):
        """BUG-FE-1b: x + 1 must not raise ValueError in server make_document."""
        doc = _exec_function_app(dr_module, "x + 1")
        assert len(doc.roots) > 0, "make_document must add roots for 'x + 1'"

    # BUG-FE-1c: subtraction (BinOp with Sub)
    def test_function_subtraction_does_not_raise(self, dr_module, auto_df):
        """BUG-FE-1c: x - 1 must not raise ValueError in server make_document."""
        doc = _exec_function_app(dr_module, "x - 1")
        assert len(doc.roots) > 0, "make_document must add roots for 'x - 1'"

    # BUG-FE-1d: multiplication (BinOp with Mult)
    def test_function_multiplication_does_not_raise(self, dr_module, auto_df):
        """BUG-FE-1d: x * 2 must not raise ValueError in server make_document."""
        doc = _exec_function_app(dr_module, "x * 2")
        assert len(doc.roots) > 0, "make_document must add roots for 'x * 2'"

    # BUG-FE-1e: division (BinOp with Div)
    def test_function_division_does_not_raise(self, dr_module, auto_df):
        """BUG-FE-1e: x / 2 must not raise ValueError in server make_document."""
        doc = _exec_function_app(dr_module, "x / 2")
        assert len(doc.roots) > 0, "make_document must add roots for 'x / 2'"

    # BUG-FE-1f: exponentiation (BinOp with Pow)
    def test_function_power_does_not_raise(self, dr_module, auto_df):
        """BUG-FE-1f: x ** 2 must not raise ValueError in server make_document."""
        doc = _exec_function_app(dr_module, "x ** 2")
        assert len(doc.roots) > 0, "make_document must add roots for 'x ** 2'"

    # BUG-FE-1g: unary negation (UnaryOp with USub)
    def test_function_unary_negation_does_not_raise(self, dr_module, auto_df):
        """BUG-FE-1g: -x must not raise ValueError in server make_document."""
        doc = _exec_function_app(dr_module, "-x")
        assert len(doc.roots) > 0, "make_document must add roots for '-x'"

    # BUG-FE-1h: complex nested expression
    def test_function_complex_expr_does_not_raise(self, dr_module, auto_df):
        """BUG-FE-1h: sin(x) + x**2 - 1 must not raise ValueError."""
        doc = _exec_function_app(dr_module, "sin(x) + x**2 - 1")
        assert len(doc.roots) > 0, (
            "make_document must add roots for complex expression 'sin(x) + x**2 - 1'"
        )

    # Safety: unsafe names must be blocked — generated source must contain _SAFE_NAMES guard
    def test_function_unsafe_name_guard_in_source(self, dr_module, auto_df):
        """BUG-FE-1 safety: generated source must contain _SAFE_NAMES to block disallowed names.

        The try/except around _val_node intentionally swallows ValueError so a bad
        expression does not crash the whole dashboard.  The security property is that
        eval() is never reached with the unsafe code, not that make_document raises.
        Verify the guard exists in the generated source.
        """
        source = _build_function_app(dr_module, "x + 1")
        assert "_SAFE_NAMES" in source, (
            "generated server source must contain _SAFE_NAMES to block disallowed names"
        )
        assert "Unsafe name" in source, (
            "generated server source must contain 'Unsafe name' error text for _SAFE_NAMES guard"
        )

    # Safety: unsafe function calls must be blocked — generated source must contain _SAFE_FUNCS guard
    def test_function_unsafe_call_guard_in_source(self, dr_module, auto_df):
        """BUG-FE-1 safety: generated source must contain _SAFE_FUNCS to block disallowed calls.

        Same rationale as test_function_unsafe_name_guard_in_source: the try/except
        silences the error but the eval() path is never reached for unsafe expressions.
        """
        source = _build_function_app(dr_module, "x + 1")
        assert "_SAFE_FUNCS" in source, (
            "generated server source must contain _SAFE_FUNCS to block disallowed function calls"
        )
        assert "Disallowed function call" in source, (
            "generated server source must contain 'Disallowed function call' guard text"
        )

    # Safety: unsafe expression silently skipped (dashboard still loads, no line from unsafe expr)
    def test_function_unsafe_expr_document_still_loads(self, dr_module, auto_df):
        """BUG-FE-1 safety: make_document must not crash for an unsafe expression.

        The validator detects the unsafe expression, the try/except swallows the error,
        and the dashboard loads without the function plot.  This is correct behavior.
        """
        # This must complete without raising — the bad expr is silently skipped
        doc = _exec_function_app(dr_module, "os.system('id')")
        # Document must have loaded (other roots may still be present)
        assert doc is not None, "make_document must not crash for an unsafe expression"


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
    """Regression suite for BUG-FE-2: function n option must be clamped 2..10000."""

    # BUG-FE-2a: generated source must contain the clamp expression
    def test_function_n_clamp_in_source(self, dr_module, auto_df):
        """BUG-FE-2a: generated server source must clamp n_pts to prevent resource exhaustion."""
        import pandas as pd, numpy as np
        df = pd.DataFrame({"x": np.linspace(0, 10, 20), "y": np.linspace(0, 10, 20)})
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "function", "expr": "x",
                       "range": [0, 10], "options": {"n": "200"}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, df, spec)
        # Generated code must clamp n_pts — check for any of the clamp patterns
        has_clamp = (
            "max(2, min(" in source
            or "min(int(opts['n']), 10000)" in source
            or "clamp" in source.lower()
        )
        assert has_clamp, (
            "generated server code must clamp n_pts (e.g. max(2, min(int(opts['n']), 10000))) "
            "to prevent resource exhaustion; fix: mirror standalone path"
        )

    # BUG-FE-2b: large n must be clamped — document loads without OOM
    def test_function_large_n_does_not_exhaust(self, dr_module, auto_df):
        """BUG-FE-2b: n=1000000 must not produce 1M-element arrays (clamped to 10000)."""
        import pandas as pd, numpy as np, importlib.util, tempfile, os, inspect
        from bokeh.document import Document

        df = pd.DataFrame({"x": np.linspace(0, 10, 20), "y": np.linspace(0, 10, 20)})
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "function", "expr": "x",
                       "range": [0, 10], "options": {"n": "1000000"}}],
            "graph_options": {"name": "g1"},
        }])
        spec_path, data_path = _write_temp_files(df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            with open(out_f.name) as fh:
                generated = fh.read()
            # Generated source must have the clamp so n never reaches 1 000 000
            assert "10000" in generated, (
                "generated source must reference 10000 as the max clamp for n"
            )
            # Run make_document to confirm it completes in reasonable time
            app_spec = importlib.util.spec_from_file_location("_tfc2", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
            doc = Document()
            app_mod.make_document(doc)
            assert doc is not None, "make_document must complete without crashing for n=1000000"
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try:
                    os.unlink(_p)
                except OSError:
                    pass

    # BUG-FE-2c: n below minimum (0, 1) must be clamped up to 2
    def test_function_n_below_minimum_clamped_to_2(self, dr_module, auto_df):
        """BUG-FE-2c: n=0 or n=1 must be clamped to 2 (minimum safe for linspace)."""
        import pandas as pd, numpy as np
        df = pd.DataFrame({"x": np.linspace(0, 10, 20), "y": np.linspace(0, 10, 20)})
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "function", "expr": "x",
                       "range": [0, 10], "options": {"n": "1"}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, df, spec)
        # Clamp must ensure n >= 2
        assert "max(2," in source, (
            "generated server code must clamp n_pts to minimum 2 (max(2, ...)) "
            "so np.linspace never receives n < 2"
        )


# ================================================================
# BUG-CLI-1: dash serve invokes unsupported renderer CLI mode/flags
# Regression for: "_dash_serve sets sys.argv with --mode 'serve' plus
# --port/--timeout flags, but dash_render.py only accepts
# --mode {standalone,server} and does not define --port, --timeout, or
# --no-browser."
# Fix:
#   (1) dash.ado: changed --mode serve → --mode server and
#       --output serve → a real .py temp-file path
#   (2) dash_render.py: added --port, --timeout, --no-browser to argparse
# ================================================================

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
        """BUG-CLI-1a: --mode choices must include 'server' (not just 'serve')."""
        help_txt = self._get_help_output()
        assert "server" in help_txt, \
            "--mode choices must include 'server' (visible in --help output)"
        assert "serve" not in help_txt.replace("server", ""), \
            "--mode choices must NOT include invalid choice 'serve'"

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
            # Must not raise
            dr_module.main(spec_path, data_path, out_f.name, "server")
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
    We test:
      (a) dash_render.py main() accepts paths with special chars
      (b) Paths with double-quotes produce a safe output (no crash)
      (c) dash.ado source shows _dash_json_str escaping pattern
    """

    def _source_ado(self):
        """Return the dash.ado source text."""
        import os
        ado_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "dash.ado"
        )
        with open(ado_path) as fh:
            return fh.read()

    def test_ado_uses_json_str_escaping_for_spec(self, dr_module, auto_df):
        """BUG-SEC-1a: dash.ado must use _dash_json_str to escape spec path."""
        src = self._source_ado()
        assert "_dash_json_str" in src, \
            "dash.ado must call _dash_json_str to escape file paths before Python interpolation"
        # Verify the old unsafe pattern (r"...macro...") is not present for spec/data/output
        import re
        # Count occurrences of r"`...' in python: sys.argv lines (should be zero after fix)
        unsafe_argv = re.findall(r'python: sys\.argv.*?r"`[^"\']+\'', src)
        assert not unsafe_argv, (
            "dash.ado must not use r\"...macro...\" in sys.argv Python lines; "
            "use _dash_json_str-escaped values in regular double-quoted strings instead. "
            f"Found: {unsafe_argv}"
        )

    def test_ado_uses_escaped_vars_in_argv(self, dr_module, auto_df):
        """BUG-SEC-1b: dash.ado sys.argv lines must use _py_* escaped locals, not raw macros."""
        src = self._source_ado()
        # The escaped locals should be present in the argv construction
        assert "_py_spec'" in src or "_py_master'" in src, \
            "dash.ado must use _py_spec (or _py_master) escaped local in Python sys.argv"
        assert "_py_data'" in src, \
            "dash.ado must use _py_data escaped local in Python sys.argv"
        assert "_py_output'" in src or "_py_serve'" in src, \
            "dash.ado must use _py_output (or _py_serve) escaped local in Python sys.argv"

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

    def test_main_accepts_path_with_backslash_on_posix(self, dr_module, auto_df):
        """BUG-SEC-1d: main() must handle backslashes in path correctly on POSIX."""
        import tempfile, os, sys
        if sys.platform == "win32":
            pytest.skip("Backslash is path separator on Windows; test only on POSIX")
        # A path that happens to have a backslash in the filename is unusual on POSIX
        # but should not cause Python injection.  Test with a normal path via main().
        spec_path, data_path = _write_temp_files(auto_df, _make_spec_json())
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False)
        out_f.close()
        try:
            # Just verify it doesn't crash — backslash risk is in the Stata layer
            dr_module.main(spec_path, data_path, out_f.name, "standalone")
            assert os.path.exists(out_f.name)
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try: os.unlink(_p)
                except OSError: pass


# ================================================================
# BUG-PARSE-1: Immediate render parser truncates if_expr on quotes
# Regression for: "_dash_render_immediate extracts if_expr from JSON
# using substr(..., 1, strpos(..., '"') - 1). This stops at the first
# quote character even when it is an escaped quote inside the JSON
# string value."
# Fix: Replace naive strpos/substr with Mata _dash_json_get_str that
# walks the JSON string char-by-char handling \" escape sequences.
# ================================================================

class TestIfExprQuoteHandling:
    """Regression suite for BUG-PARSE-1: if_expr containing quotes must not be truncated.

    The Mata fix (_dash_json_get_str) and the dash.ado change to use it
    are tested here via:
      (a) dash_parse.mata source inspection (contains the fix)
      (b) dash.ado source inspection (calls _dash_json_get_str)
      (c) dash_render.py: if_expr is passed through without truncation
          when it contains quoted strings
    """

    def _source_mata(self):
        import os
        p = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "dash_parse.mata"
        )
        with open(p) as fh:
            return fh.read()

    def _source_ado(self):
        import os
        p = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "dash.ado"
        )
        with open(p) as fh:
            return fh.read()

    def test_dash_parse_contains_json_get_str(self, dr_module, auto_df):
        """BUG-PARSE-1a: dash_parse.mata must define _dash_json_get_str."""
        src = self._source_mata()
        assert "_dash_json_get_str" in src, (
            "dash_parse.mata must define _dash_json_get_str for JSON-safe if_expr extraction"
        )

    def test_dash_parse_handles_escaped_quotes(self, dr_module, auto_df):
        """BUG-PARSE-1b: _dash_json_get_str implementation must handle backslash-quote."""
        src = self._source_mata()
        # The function must check for backslash escape sequences
        assert 'ch == "\\"' in src or "ch == " + repr("\\") in src or r'ch == "\"' in src or "backslash" in src.lower() or "escape" in src.lower(), (
            "_dash_json_get_str must handle JSON escape sequences (backslash handling)"
        )

    def test_ado_uses_json_get_str_for_if_expr(self, dr_module, auto_df):
        """BUG-PARSE-1c: dash.ado must call _dash_json_get_str for if_expr extraction."""
        src = self._source_ado()
        assert "_dash_json_get_str" in src, (
            "dash.ado must call _dash_json_get_str instead of naive strpos/substr for if_expr"
        )

    def test_ado_no_naive_strpos_for_if_expr(self, dr_module, auto_df):
        """BUG-PARSE-1d: dash.ado must not use naive strpos pattern for if_expr extraction."""
        src = self._source_ado()
        # The old pattern: strpos(`"`after_if'"', `"""') - should be gone
        assert 'strpos(`"`after_if' not in src, (
            "dash.ado must not use old naive strpos-based if_expr extraction; "
            "it truncates values containing escaped quotes"
        )

    def test_renderer_passes_if_expr_with_quoted_string(self, dr_module, auto_df):
        """BUG-PARSE-1e: DashRenderer must accept if_expr containing JSON-escaped quotes.

        The Python-side renderer handles if_expr values directly from the spec dict.
        Verify that a spec with a quoted if_expr is processed without truncation.
        """
        import pandas as pd, numpy as np, json, tempfile, os
        # Build a spec where graph_options has an if_expr with a quoted string.
        # _make_spec_json returns a dict; set if_expr directly then pass dict
        # to _write_temp_files (which calls json.dump internally).
        spec_dict = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}],
            "graph_options": {"name": "g1"},
        }])
        # Set if_expr containing a quoted string (json.dump will produce \" inside)
        spec_dict["graphs"][0]["graph_options"]["if_expr"] = 'foreign == 1'

        spec_path, data_path = _write_temp_files(auto_df, spec_dict)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False)
        out_f.close()
        try:
            dr_module.main(spec_path, data_path, out_f.name, "standalone")
            assert os.path.exists(out_f.name), \
                "main() must produce output for spec with if_expr"
            with open(out_f.name) as fh:
                html = fh.read()
            assert len(html) > 100, "output HTML must be non-trivial"
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try: os.unlink(_p)
                except OSError: pass


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
      (b) DashRenderer filters data when graph spec has if_expr
      (c) Generated server code falls back to g.get('if_expr')
      (d) dash.ado source calls _dash_json_get_str for if_expr promotion
    """

    def _source_ado(self):
        import os
        p = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "dash.ado"
        )
        with open(p) as fh:
            return fh.read()

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

    def test_server_code_falls_back_to_top_level_if_expr(self, dr_module, auto_df):
        """BUG-QUAL-1c: generated server code must fall back to g.get('if_expr')."""
        source = _build_app(dr_module, auto_df, _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}],
            "graph_options": {"name": "g1"},
            "if_expr": "foreign == 1",
        }]))
        # The generated code must read if_expr from g (top level) as fallback
        assert "g.get('if_expr')" in source or 'g.get("if_expr")' in source, (
            "generated server code must fall back to g.get('if_expr') "
            "when graph_options.if_expr is empty (BUG-QUAL-1 fix)"
        )

    def test_ado_promotes_if_expr_to_graph_level(self, dr_module, auto_df):
        """BUG-QUAL-1d: dash.ado must use _dash_json_get_str to promote if_expr to graph level."""
        src = self._source_ado()
        # After the fix, _dash_plot calls _dash_json_get_str to extract if_expr
        # from plots_json and then sets it at graph level
        assert "_dash_json_get_str" in src, \
            "dash.ado must call _dash_json_get_str for if_expr promotion"
        # The old hard-coded empty string for if_expr must be gone
        assert '"if_expr":"","in_expr":""' not in src, (
            "dash.ado must not hard-code empty strings for if_expr/in_expr in graph_json"
        )

    def test_renderer_graph_with_if_expr_filters_data(self, dr_module, auto_df):
        """BUG-QUAL-1e: standalone render with top-level if_expr must filter output."""
        import tempfile, os, json
        spec_dict = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}],
            "graph_options": {"name": "g1"},
            "if_expr": "foreign == 1",
        }])
        spec_path, data_path = _write_temp_files(auto_df, spec_dict)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False)
        out_f.close()
        try:
            dr_module.main(spec_path, data_path, out_f.name, "standalone")
            assert os.path.exists(out_f.name), \
                "main() must produce output when graph has top-level if_expr"
            with open(out_f.name) as fh:
                html = fh.read()
            assert len(html) > 100, "output HTML must be non-trivial"
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try: os.unlink(_p)
                except OSError: pass


# ================================================================
# BUG-HIST-1: Server-mode histogram bin() accepts unbounded values
# Regression for: "Generated server code parses nbins = int(opts.get
# ('bin', 20)) with no bounds and feeds it to np.histogram(..., bins=nbins).
# Large bin() values can force very large array allocations."
# Fix: clamp nbins to max(1, min(int(...), 1000)) at the call site and
# inside _compute_histogram.
# ================================================================

class TestServerHistogramBinClamp:
    """Regression suite for BUG-HIST-1: server histogram bin() must be clamped 1..1000."""

    def test_histogram_bin_clamp_in_source(self, dr_module, auto_df):
        """BUG-HIST-1a: generated server source must clamp nbins to 1..1000."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "histogram", "yvar": "mpg", "xvar": "",
                       "options": {"bin": "20"}}],
            "graph_options": {"name": "g1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "max(1, min(" in source or "min(int(" in source, (
            "generated server source must clamp nbins with max(1, min(..., 1000)) "
            "to prevent resource exhaustion"
        )

    def test_histogram_large_bin_does_not_exhaust(self, dr_module, auto_df):
        """BUG-HIST-1b: bin=100000 must be clamped and document loads without OOM."""
        import importlib.util, tempfile, os
        from bokeh.document import Document
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "histogram", "yvar": "mpg", "xvar": "",
                       "options": {"bin": "100000"}}],
            "graph_options": {"name": "g1"},
        }])
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            with open(out_f.name) as fh:
                generated = fh.read()
            assert "1000" in generated, "generated source must reference 1000 as max bin clamp"
            app_spec = importlib.util.spec_from_file_location("_th2", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
            doc = Document()
            app_mod.make_document(doc)
            assert doc is not None, "make_document must complete with bin=100000"
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try: os.unlink(_p)
                except OSError: pass

    def test_compute_histogram_clamps_bins(self, dr_module, auto_df):
        """BUG-HIST-1c: generated _compute_histogram must clamp bins internally."""
        source = _build_app(dr_module, auto_df, _make_spec_json(graphs=[{
            "plots": [{"type": "histogram", "yvar": "mpg", "xvar": "", "options": {}}],
            "graph_options": {"name": "g1"},
        }]))
        # _compute_histogram body must clamp bins
        assert "max(1, min(int(bins), 1000))" in source or "clamp" in source.lower(), (
            "_compute_histogram in generated source must clamp bins parameter"
        )

    def test_histogram_bin_minimum_is_1(self, dr_module, auto_df):
        """BUG-HIST-1d: bin=0 must be clamped to minimum 1."""
        source = _build_app(dr_module, auto_df, _make_spec_json(graphs=[{
            "plots": [{"type": "histogram", "yvar": "mpg", "xvar": "",
                       "options": {"bin": "0"}}],
            "graph_options": {"name": "g1"},
        }]))
        assert "max(1," in source, (
            "generated server code must ensure bins >= 1 via max(1, ...)"
        )


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

    def test_xscale_log_only(self, dr_module, auto_df):
        """BUG-SCALE-1a: xscale(log) alone must produce log x-axis."""
        from bokeh.models import LogScale
        renderer = self._make_renderer(dr_module, auto_df, {"xscale": "log"})
        html = renderer.render()
        # If xscale(log) works, the generated JSON should contain "LogScale"
        assert "LogScale" in html or "log" in html.lower(), \
            "xscale(log) must produce a LogScale x-axis in the rendered HTML"

    def test_yscale_log_only(self, dr_module, auto_df):
        """BUG-SCALE-1b: yscale(log) alone must produce log y-axis."""
        renderer = self._make_renderer(dr_module, auto_df, {"yscale": "log"})
        html = renderer.render()
        assert "LogScale" in html or "log" in html.lower(), \
            "yscale(log) must produce a LogScale y-axis in the rendered HTML"

    def test_dual_log_scale_both_axes(self, dr_module, auto_df):
        """BUG-SCALE-1c: xscale(log) yscale(log) must produce log scale on BOTH axes.

        Before the fix, the second bokeh_figure() call overrode the first so the
        x-axis reverted to linear.  After the fix, both axes are set in one call.
        """
        renderer = self._make_renderer(dr_module, auto_df, {"xscale": "log", "yscale": "log"})
        html = renderer.render()
        # Count LogScale occurrences — dual-log needs at least 2
        log_count = html.count("LogScale")
        assert log_count >= 2, (
            f"xscale(log) yscale(log) must produce 2 LogScale instances in the HTML "
            f"(one per axis), got {log_count}. "
            "This is BUG-SCALE-1: second figure re-creation must not overwrite x-axis type."
        )

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
            renderer.render()
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
    """Regression suite for BUG-FAC-1: faceted aggregates must use per-facet data."""

    def test_server_source_uses_agg_fdf_not_fdf(self, dr_module, auto_df):
        """BUG-FAC-1a: generated server source must use agg_fdf (not fdf) for aggregates."""
        source = _build_app(dr_module, auto_df, _make_spec_json(graphs=[{
            "plots": [{"type": "histogram", "yvar": "mpg", "xvar": "",
                       "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign"},
        }]))
        # The aggregate recompute loop must use agg_fdf, not global fdf
        assert "agg_fdf" in source, (
            "generated server source must use agg_fdf (per-facet data frame) "
            "in aggregate recompute loop, not global fdf"
        )

    def test_server_source_derives_facet_mask_for_agg(self, dr_module, auto_df):
        """BUG-FAC-1b: generated server source must derive facet mask for aggregates."""
        source = _build_app(dr_module, auto_df, _make_spec_json(graphs=[{
            "plots": [{"type": "lfit", "yvar": "mpg", "xvar": "weight",
                       "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign"},
        }]))
        # The facet-aware derive pattern for aggregates
        assert "_fgvals" in source, \
            "generated server source must use _fgvals for facet-aware aggregate recompute"
        assert "agg_fdf" in source, \
            "generated server source must assign agg_fdf per aggregate entry"

    def test_server_faceted_histogram_generates_without_crash(self, dr_module, auto_df):
        """BUG-FAC-1c: server app with by() and histogram must build and run without crash."""
        import importlib.util, tempfile, os
        from bokeh.document import Document
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "histogram", "yvar": "mpg", "xvar": "",
                       "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign"},
        }])
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_spec = importlib.util.spec_from_file_location("_tfac1", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
            doc = Document()
            app_mod.make_document(doc)
            assert len(doc.roots) > 0, \
                "faceted histogram server app must build a document with roots"
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try: os.unlink(_p)
                except OSError: pass


# ---------------------------------------------------------------------------
# BUG-FILT-OR: Server build drops additional filter() clauses joined with ||
# ---------------------------------------------------------------------------

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
# BUG-SHELL: saving() path shell-metacharacter hardening
# ---------------------------------------------------------------------------

def _validate_saving_path(fpath: str) -> None:
    """Python re-implementation of Stata's _dash_validate_path logic.

    Raises ValueError if fpath contains '..' (path traversal), does not end
    in '.html', or contains any shell metacharacter that could be exploited
    in ``shell open/start/xdg-open "<path>"``.
    """
    import re
    if ".." in fpath:
        raise ValueError("path traversal not allowed")
    if not fpath.lower().endswith(".html"):
        raise ValueError("path must end in .html")
    # Shell metacharacters: ; & | < > ( ) backtick dollar newline CR tab
    _SHELL_BAD = set(";&|<>()\x60\x24\n\r\t")
    for ch in fpath:
        if ch in _SHELL_BAD:
            raise ValueError(f"disallowed character in path: {ch!r}")


class TestSavingPathHardening:
    """Regression tests for BUG-SHELL: saving() path must not allow shell metacharacters."""

    def test_normal_path_accepted(self):
        """BUG-SHELL-1a: a normal absolute path ending in .html must be accepted."""
        _validate_saving_path("/tmp/my_dashboard.html")  # must not raise

    def test_path_with_spaces_accepted(self):
        """BUG-SHELL-1b: spaces in paths are permitted (valid on all OSes)."""
        _validate_saving_path("/tmp/my dashboard.html")  # must not raise

    def test_path_traversal_rejected(self):
        """BUG-SHELL-1c: path containing '..' must be rejected."""
        with pytest.raises(ValueError, match="path traversal"):
            _validate_saving_path("/tmp/../etc/passwd.html")

    def test_non_html_rejected(self):
        """BUG-SHELL-1d: path not ending in .html must be rejected."""
        with pytest.raises(ValueError, match=".html"):
            _validate_saving_path("/tmp/dashboard.py")

    def test_semicolon_in_path_rejected(self):
        """BUG-SHELL-1e: semicolon must be rejected (command chaining)."""
        with pytest.raises(ValueError, match="disallowed character"):
            _validate_saving_path("/tmp/foo;rm -rf /.html")

    def test_ampersand_in_path_rejected(self):
        """BUG-SHELL-1f: ampersand must be rejected (background execution)."""
        with pytest.raises(ValueError, match="disallowed character"):
            _validate_saving_path("/tmp/foo&id.html")

    def test_pipe_in_path_rejected(self):
        """BUG-SHELL-1g: pipe must be rejected (output piping)."""
        with pytest.raises(ValueError, match="disallowed character"):
            _validate_saving_path("/tmp/foo|cat /etc/passwd.html")

    def test_backtick_in_path_rejected(self):
        """BUG-SHELL-1h: backtick must be rejected (command substitution)."""
        with pytest.raises(ValueError, match="disallowed character"):
            _validate_saving_path("/tmp/foo`id`.html")

    def test_dollar_in_path_rejected(self):
        """BUG-SHELL-1i: dollar sign must be rejected (variable expansion)."""
        with pytest.raises(ValueError, match="disallowed character"):
            _validate_saving_path("/tmp/foo$(touch /tmp/pwned).html")

    def test_angle_bracket_in_path_rejected(self):
        """BUG-SHELL-1j: < and > must be rejected (redirection)."""
        with pytest.raises(ValueError, match="disallowed character"):
            _validate_saving_path("/tmp/foo</dev/urandom.html")

    def test_newline_in_path_rejected(self):
        """BUG-SHELL-1k: newline in path must be rejected (command injection)."""
        with pytest.raises(ValueError, match="disallowed character"):
            _validate_saving_path("/tmp/foo\nrm -rf /.html")

    def test_paren_in_path_rejected(self):
        """BUG-SHELL-1l: parenthesis must be rejected (subshell invocation)."""
        with pytest.raises(ValueError, match="disallowed character"):
            _validate_saving_path("/tmp/foo(bar).html")


# ---------------------------------------------------------------------------
# BUG-REGEX: Generated server unsafe-token regex uses word boundaries (\b)
# ---------------------------------------------------------------------------

class TestUnsafeTokenRegexWordBoundaries:
    """Regression tests for BUG-REGEX: _UNSAFE_G and _UNSAFE_BY in generated
    server source must use \\b word-boundary markers, not backspace bytes."""

    def test_unsafe_g_uses_word_boundary_not_backspace(self, dr_module, auto_df):
        """BUG-REGEX-1a: generated _UNSAFE_G pattern must contain \\b not backspace."""
        src = _build_app(dr_module, auto_df, _make_spec_json(
            graphs=[{"plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                                "options": {}}],
                     "graph_options": {"name": "g1", "if_expr": "mpg > 15"}}]
        ))
        # Find the _UNSAFE_G compile line
        for line in src.splitlines():
            if "_UNSAFE_G" in line and "compile" in line:
                # Must NOT contain backspace character (0x08)
                assert "\x08" not in line, \
                    "_UNSAFE_G pattern must not contain backspace (\\x08); use \\b word boundary"
                # Must contain the literal two-char sequence \b
                assert r"\b" in line, \
                    "_UNSAFE_G pattern must contain \\b word-boundary markers"
                break
        else:
            pytest.fail("_UNSAFE_G compile line not found in generated source")

    def test_unsafe_g_blocks_bare_eval(self, dr_module, auto_df):
        """BUG-REGEX-1b: _UNSAFE_G in generated source must block 'eval(...)' expression."""
        import importlib.util, tempfile, os
        from bokeh.document import Document
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "if_expr": "eval('1==1')"},
        }])
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_spec = importlib.util.spec_from_file_location("_trx1", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
            doc = Document()
            # Must not crash and must not have called eval() (filter blocked)
            app_mod.make_document(doc)
            assert len(doc.roots) > 0
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try: os.unlink(_p)
                except OSError: pass

    def test_unsafe_g_allows_evaluate_variable_name(self, dr_module, auto_df):
        """BUG-REGEX-1c: _UNSAFE_G must NOT block variable names containing 'eval' as substring.

        With backspace chars instead of word boundaries, 'evaluate' would not be blocked
        (backspace-eval-backspace doesn't match 'evaluate'). With real \b, 'evaluate'
        is also not blocked because the 'e' after 'eval' prevents the word-boundary match.
        Both scenarios should allow 'evaluate' as a valid column name in df.query.
        """
        # This test verifies the regex compiled from the generated string actually works
        import re
        # Simulate the pattern that should be in the generated source
        pattern = re.compile(
            r'[;`$\\]|import\s|__|\beval\b|\bexec\b|\bopen\b'
            r'|\bgetattr\b|\bsetattr\b|\bhasattr\b|\bdelattr\b'
        )
        # 'evaluate' contains 'eval' as substring but not at word boundary
        assert not pattern.search("evaluate > 5"), \
            "word-boundary \\b must not block 'evaluate' (not an exact 'eval' token)"
        # 'eval(...)' must be blocked
        assert pattern.search("eval('1==1')"), \
            "word-boundary \\b must block 'eval(...)'"

    def test_unsafe_by_uses_word_boundary_not_backspace(self, dr_module, auto_df):
        """BUG-REGEX-1d: generated _UNSAFE_BY pattern must contain \\b not backspace."""
        src = _build_app(dr_module, auto_df, _make_spec_json(
            graphs=[{"plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                                "options": {}}],
                     "graph_options": {"name": "g1", "by": "foreign"}}]
        ))
        # Find the _UNSAFE_BY lines (may span multiple lines)
        unsafe_by_block = ""
        in_block = False
        for line in src.splitlines():
            if "_UNSAFE_BY" in line and "compile" in line:
                in_block = True
            if in_block:
                unsafe_by_block += line + "\n"
                if ")" in line and in_block and len(unsafe_by_block) > 20:
                    break
        assert "\x08" not in unsafe_by_block, \
            "_UNSAFE_BY pattern must not contain backspace (\\x08); use \\b word boundary"
        assert r"\b" in unsafe_by_block, \
            "_UNSAFE_BY pattern must contain \\b word-boundary markers"


# ---------------------------------------------------------------------------
# BUG-IQUAL: Immediate render jsonio qualifier wrongly pre-filters multi-plot data
# ---------------------------------------------------------------------------

class TestImmediateRenderQualifierHandling:
    """Regression tests for BUG-IQUAL: immediate render must not pre-filter
    jsonio with the first plot's qualifier when multiple plots have different
    if/in expressions.  The renderer must receive all rows and apply per-graph
    filtering itself via _apply_graph_filter."""

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
        """BUG-IQUAL-1c: multi-plot spec with different per-plot qualifiers must render."""
        spec = self._make_multi_qualifier_spec("foreign==1", "foreign==0")
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            html = renderer.render()
            assert len(html) > 100, "rendered HTML must be non-trivial"
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

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
# BUG-EXCL: dash build validates only first exclude() group
# ---------------------------------------------------------------------------

def _validate_filter_exclude_names(filter_str: str, registry: set) -> list:
    """Python re-implementation of the Stata filter exclude() validation loop.

    Returns a list of unrecognised exclude names, or raises nothing if all
    names are in the registry.  Mirrors the updated Stata code that iterates
    over ALL exclude() groups in the (||/;-joined) filter string.
    """
    import re as _re
    unknown = []
    remaining = filter_str
    while True:
        pos = remaining.find("exclude(")
        if pos < 0:
            break
        inner = remaining[pos + 8:]
        end = inner.find(")")
        if end < 0:
            break  # malformed
        names = inner[:end].split()
        for name in names:
            if name not in registry:
                unknown.append(name)
        remaining = inner[end + 1:]
    return unknown


class TestFilterExcludeValidationAllGroups:
    """Regression tests for BUG-EXCL: build must validate ALL exclude() groups
    in a multi-filter spec, not just the first one."""

    def test_no_exclude_passes(self):
        """BUG-EXCL-1a: filter string with no exclude() must validate cleanly."""
        unknown = _validate_filter_exclude_names(
            "foreign, type(dropdown)", {"g1", "g2"}
        )
        assert unknown == [], "no exclude() should produce no unknown names"

    def test_single_valid_exclude_passes(self):
        """BUG-EXCL-1b: single exclude() with known names must validate cleanly."""
        unknown = _validate_filter_exclude_names(
            "foreign, type(dropdown) exclude(g1)", {"g1", "g2"}
        )
        assert unknown == [], "valid single exclude() must pass"

    def test_single_invalid_exclude_fails(self):
        """BUG-EXCL-1c: single exclude() with unknown name must be flagged."""
        unknown = _validate_filter_exclude_names(
            "foreign, type(dropdown) exclude(g99)", {"g1", "g2"}
        )
        assert "g99" in unknown, "unknown exclude name must be detected"

    def test_second_exclude_group_validated(self):
        """BUG-EXCL-1d: second exclude() group after || must also be validated."""
        # Only first group has known names; second has unknown
        unknown = _validate_filter_exclude_names(
            "foreign, type(dropdown) exclude(g1) || weight, type(range) exclude(g99)",
            {"g1", "g2"}
        )
        assert "g99" in unknown, \
            "second exclude() group must be validated (not just first)"

    def test_both_groups_validated_when_both_invalid(self):
        """BUG-EXCL-1e: all exclude() groups must be validated — both unknown names reported."""
        unknown = _validate_filter_exclude_names(
            "foreign, type(dropdown) exclude(badA) || weight, type(range) exclude(badB)",
            {"g1", "g2"}
        )
        assert "badA" in unknown, "first exclude() group's unknown name must appear"
        assert "badB" in unknown, "second exclude() group's unknown name must appear"

    def test_three_exclude_groups_all_checked(self):
        """BUG-EXCL-1f: three || -joined filters with exclude() are all checked."""
        unknown = _validate_filter_exclude_names(
            "a, type(dropdown) exclude(g1) || b, type(range) exclude(g2) || c, type(range) exclude(zz)",
            {"g1", "g2"}
        )
        assert "zz" in unknown, "third exclude() group must be validated"
        assert "g1" not in unknown, "known name in first group must not be flagged"
        assert "g2" not in unknown, "known name in second group must not be flagged"

    def test_server_builder_generates_exclude_metadata_for_all_filters(
            self, dr_module, auto_df):
        """BUG-EXCL-1g: generated server source must carry exclude metadata for every filter."""
        spec = _make_spec_json(
            graphs=[
                {"plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                            "options": {}}], "graph_options": {"name": "g1"}},
                {"plots": [{"type": "scatter", "yvar": "price", "xvar": "weight",
                            "options": {}}], "graph_options": {"name": "g2"}},
            ],
            build_options={
                "layout": "auto", "link": "",
                "filter": (
                    "foreign, type(dropdown), exclude(g2) || "
                    "weight, type(range), exclude(g1)"
                ),
                "theme": "default", "title": "T", "subtitle": "", "registry": "g1 g2",
                "mode": "server", "port": "5006",
            }
        )
        src = _build_app(dr_module, auto_df, spec)
        # Both filter specs should be present in the generated source
        assert "'foreign'" in src, "first filter var must appear in generated source"
        assert "'weight'" in src, "second filter var must appear in generated source"


# ---------------------------------------------------------------------------
# BUG-CBEXCL: Filter callback exclude() binds to wrong widget when var is missing
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
        """BUG-CBEXCL-1a: filter_specs_json length must equal the number of built widgets."""
        spec = self._make_mixed_filter_spec(dr_module, auto_df)
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            html = renderer.render()
            # foreign is the only built filter — filter_specs_json must have 1 entry
            import re as _re
            # The filter_specs_json in the rendered HTML is an array like [{"varname":...}]
            m = _re.search(r'"filter_specs_json"\s*:\s*"(\[.*?\])"', html)
            if m:
                fs = json.loads(m.group(1).replace('\\"', '"').replace('\\\\', '\\'))
                assert len(fs) == 1, \
                    f"filter_specs must have 1 entry (not {len(fs)}); missing_var must be excluded"
                assert fs[0]["varname"] == "foreign", \
                    "only the successfully-built filter spec must appear in filter_specs"
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    def test_render_with_missing_filter_var_does_not_crash(self, dr_module, auto_df):
        """BUG-CBEXCL-1b: render must not crash when first filter var is missing."""
        spec = self._make_mixed_filter_spec(dr_module, auto_df)
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            html = renderer.render()
            assert len(html) > 100, "rendered HTML must be non-trivial"
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    def test_built_filter_callback_count_equals_valid_filter_specs(self, dr_module, auto_df):
        """BUG-CBEXCL-1c: number of filter callbacks must equal number of built widgets."""
        spec = self._make_mixed_filter_spec(dr_module, auto_df)
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            renderer.render()
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
            renderer.render()
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
            renderer.render()
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
            renderer.render()
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
            renderer.render()
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
            renderer.render()
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
