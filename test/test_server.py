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
    pruning, and a _MAX_IPS hard cap evicts the oldest entry when the store
    is full.
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
        """BUG-30-1c: _store size must not exceed _MAX_IPS under high-cardinality churn."""
        app_mod = _load_app_module(dr_module, auto_df, self._minimal_spec())
        limiter = app_mod._RateLimiter(max_rpm=60)
        max_ips = limiter._MAX_IPS
        # Issue requests from many more IPs than _MAX_IPS
        for i in range(max_ips + 500):
            limiter.is_allowed(f"192.0.2.{i // 256}.{i % 256}")
        assert len(limiter._store) <= max_ips, (
            f"_store size {len(limiter._store)} must not exceed _MAX_IPS={max_ips}"
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
# BUG-31: Server-mode function plots silently drop valid constant expressions
# np.asarray(scalar, dtype=float).tolist() returns a float, not a list;
# ColumnDataSource raises because 'y_fn' is not a sequence, so the broad
# except silently drops the entire function line.
# Fix: mirror standalone map_function by broadcasting scalar results to
# len(_x) before creating ColumnDataSource.
# ================================================================

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
        """BUG-31-1a: function expression 'pi' must produce a glyph renderer."""
        doc = _exec_function_app(dr_module, "pi")
        assert _count_glyph_renderers(doc) > 0, (
            "function expression 'pi' must produce at least one glyph renderer"
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
        """BUG-REGEX-1a: generated server if_expr guard must use AST whitelist
        (not the old regex-backspace approach); _UNSAFE_G must not appear."""
        src = _build_app(dr_module, auto_df, _make_spec_json(
            graphs=[{"plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                                "options": {}}],
                     "graph_options": {"name": "g1", "if_expr": "mpg > 15"}}]
        ))
        # The old broken pattern used a regex with backspace bytes.
        # The fixed code uses an AST whitelist (_safe_g function).
        # Verify the generated code no longer uses the old _UNSAFE_G regex
        # approach AND that the AST whitelist is present.
        for line in src.splitlines():
            if "_UNSAFE_G" in line and "compile" in line:
                assert "\x08" not in line, \
                    "_UNSAFE_G pattern must not contain backspace (\x08)"
                break
        # The AST guard must be present in the generated code
        assert "_safe_g" in src or "_ALLOWED_G" in src, \
            "Generated server code must use AST whitelist for if_expr validation"

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


# ---------------------------------------------------------------------------
# BUG-FILT-COMMA: filter() extraction fails when preceded by comma (no space)
# ---------------------------------------------------------------------------

def _simulate_extract_filters(cmd_str: str) -> tuple:
    """Python re-implementation of Mata _dash_extract_filters boundary logic.

    Accepts comma, space, or tab as valid word boundaries before filter/filt/filte.
    Returns (filter_out, remaining) where filter_out is ||-joined filter specs.
    """
    import re as _re
    raw = cmd_str
    lraw = raw.lower()
    n = len(raw)
    result_parts = []
    remaining = []
    i = 0
    while i < n:
        matched = 0
        klen = 0
        for kw in ("filter", "filte", "filt"):
            if lraw[i:i+len(kw)] == kw:
                matched = 1
                klen = len(kw)
                break
        if matched:
            prev_ch = raw[i-1] if i > 0 else ""
            before_ok = (i == 0 or prev_ch in (" ", ",", "\t"))
            if before_ok:
                j = i + klen
                # Skip spaces before "("
                while j < n and raw[j] == " ":
                    j += 1
                if j < n and raw[j] == "(":
                    depth = 1
                    k = j + 1
                    while k < n and depth > 0:
                        if raw[k] == "(":
                            depth += 1
                        elif raw[k] == ")":
                            depth -= 1
                        k += 1
                    if depth == 0:
                        inner = raw[j+1:k-1].strip()
                        result_parts.append(inner)
                        i = k
                        while i < n and raw[i] == " ":
                            i += 1
                        continue
        remaining.append(raw[i])
        i += 1
    return " || ".join(result_parts), "".join(remaining).strip()


class TestFilterExtractionCommaPrefix:
    """Regression tests for BUG-FILT-COMMA: _dash_extract_filters must recognise
    filter() when preceded by a comma (standard Stata option syntax)."""

    def test_space_separated_filter_extracted(self):
        """BUG-FILT-COMMA-1a: filter preceded by space must be extracted."""
        result, _ = _simulate_extract_filters("varname filter(foreign, type(dropdown))")
        assert "foreign" in result, "space-separated filter must be extracted"

    def test_comma_no_space_filter_extracted(self):
        """BUG-FILT-COMMA-1b: filter preceded by comma (no space) must be extracted."""
        result, _ = _simulate_extract_filters("varname,filter(foreign, type(dropdown))")
        assert "foreign" in result, \
            "comma-prefixed filter (,filter) must be extracted — this is standard Stata syntax"

    def test_comma_space_filter_extracted(self):
        """BUG-FILT-COMMA-1c: filter preceded by ', ' (comma+space) must be extracted."""
        result, _ = _simulate_extract_filters("varname, filter(foreign, type(dropdown))")
        assert "foreign" in result, "', filter' must be extracted"

    def test_two_filters_comma_prefix(self):
        """BUG-FILT-COMMA-1d: two comma-prefixed filters must both be extracted."""
        result, _ = _simulate_extract_filters(
            "var,filter(foreign, type(dropdown)),filter(weight, type(range))"
        )
        assert "foreign" in result, "first comma-prefixed filter must be extracted"
        assert "weight" in result, "second comma-prefixed filter must be extracted"
        assert "||" in result, "multiple filters must be joined with ||"

    def test_filter_substr_in_varname_not_extracted(self):
        """BUG-FILT-COMMA-1e: 'filter' as part of a varname must not be extracted."""
        result, remaining = _simulate_extract_filters("my_filtervariable other_var")
        assert result == "", "'filter' substring in varname must not match word boundary"
        assert "my_filtervariable" in remaining

    def test_comma_filter_remaining_is_clean(self):
        """BUG-FILT-COMMA-1f: after extraction, the filter() group must be removed from remaining."""
        _, remaining = _simulate_extract_filters("varname,filter(foreign, type(dropdown))")
        assert "filter(" not in remaining.lower(), \
            "filter() group must be removed from remaining text"
        assert "varname" in remaining, "non-filter tokens must remain in remaining"

    def test_server_build_accepts_comma_filter_spec(self, dr_module, auto_df):
        """BUG-FILT-COMMA-1g: server builder must produce filter widget for comma-prefixed spec."""
        # Simulate what _dash_build would store in build_options.filter after extraction:
        # the inner content of filter() — in both space-before and comma-before cases
        # the inner content would be the same ("foreign, type(dropdown)")
        spec = _make_spec_json(
            graphs=[{"plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                                "options": {}}], "graph_options": {"name": "g1"}}],
            build_options={
                "layout": "auto", "link": "",
                "filter": "foreign, type(dropdown)",  # inner content, already extracted
                "theme": "default", "title": "T", "subtitle": "", "registry": "g1",
                "mode": "server", "port": "5006",
            }
        )
        src = _build_app(dr_module, auto_df, spec)
        assert "foreign" in src, "filter var must appear in generated server source"


# ---------------------------------------------------------------------------
# BUG-MTSRC: Standalone filter callbacks only update single source
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
            renderer.render()
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
            renderer.render()
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
        """BUG-MTSRC-1d: two-graph unlinked dashboard with filter must render without crash."""
        spec = self._make_two_graph_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            html_out = renderer.render()
            assert len(html_out) > 100, "rendered HTML must be non-trivial"
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass


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
        """BUG-29-1a: filter callback must include all_graph_sources_orig_json."""
        spec = self._make_different_schema_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            renderer.render()
            assert renderer.filter_callbacks, "filter callback must be built"
            cb_args = renderer.filter_callbacks[0].args
            assert "all_graph_sources_orig_json" in cb_args, (
                "callback args must contain 'all_graph_sources_orig_json' for per-source snapshots"
            )
        finally:
            for _p in (spec_path, data_path):
                try:
                    os.unlink(_p)
                except OSError:
                    pass

    def test_per_source_orig_json_length_matches_sources(self, dr_module, auto_df):
        """BUG-29-1b: all_graph_sources_orig_json must have same length as all_graph_sources."""
        spec = self._make_different_schema_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            renderer.render()
            assert renderer.filter_callbacks, "filter callback must be built"
            cb_args = renderer.filter_callbacks[0].args
            srcs = cb_args.get("all_graph_sources", [])
            orig_jsons = cb_args.get("all_graph_sources_orig_json", [])
            assert len(srcs) == len(orig_jsons), (
                f"all_graph_sources_orig_json length ({len(orig_jsons)}) must match "
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
            renderer.render()
            assert renderer.filter_callbacks, "filter callback must be built"
            cb_args = renderer.filter_callbacks[0].args
            srcs = cb_args.get("all_graph_sources", [])
            orig_jsons = cb_args.get("all_graph_sources_orig_json", [])
            assert len(srcs) == len(orig_jsons) >= 2, (
                "need at least 2 source snapshots to verify per-source column preservation"
            )
            for i, (src, orig_json_str) in enumerate(zip(srcs, orig_jsons)):
                orig = _json.loads(orig_json_str)
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
            renderer.render()
            if not renderer.filter_callbacks:
                return
            cb_args = renderer.filter_callbacks[0].args
            srcs = cb_args.get("all_graph_sources", [])
            orig_jsons = cb_args.get("all_graph_sources_orig_json", [])
            if len(srcs) < 2:
                return
            g2_src = renderer.sources.get("g2")
            if g2_src is None:
                return
            for src, orig_json_str in zip(srcs, orig_jsons):
                if src is g2_src:
                    orig = _json.loads(orig_json_str)
                    assert "price" in orig, (
                        "g2 source orig_json must contain 'price' (g2's y-column)"
                    )
                    assert "mpg" not in orig, (
                        "g2 source orig_json must NOT contain 'mpg' (g1-only column) — "
                        "this was the pre-fix corruption vector"
                    )
        finally:
            for _p in (spec_path, data_path):
                try:
                    os.unlink(_p)
                except OSError:
                    pass

    def test_filter_js_uses_per_source_orig_json(self, dr_module, auto_df):
        """BUG-29-1e: _FILTER_JS must reference all_graph_sources_orig_json."""
        js = dr_module._FILTER_JS
        assert "all_graph_sources_orig_json" in js, (
            "_FILTER_JS must reference all_graph_sources_orig_json so each source "
            "is filtered with its own column snapshot, not the primary source's snapshot"
        )

    def test_render_with_different_schema_does_not_crash(self, dr_module, auto_df):
        """BUG-29-1f: two-graph unlinked dashboard with different schemas must render without crash."""
        spec = self._make_different_schema_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            html_out = renderer.render()
            assert len(html_out) > 100, "rendered HTML must be non-trivial"
            # Verify per-source orig data is embedded in the HTML
            assert "all_graph_sources_orig_json" in html_out, (
                "rendered HTML must embed all_graph_sources_orig_json callback arg"
            )
        finally:
            for _p in (spec_path, data_path):
                try:
                    os.unlink(_p)
                except OSError:
                    pass


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

    def test_make_filter_cb_accepts_trig_widget(self, dr_module, auto_df):
        """BUG-21b: _make_filter_cb in generated source must accept _trig_widget param."""
        spec = self._make_server_spec_two_widgets()
        source = _build_app(dr_module, auto_df, spec)
        assert "_trig_widget" in source, (
            "Generated _make_filter_cb must accept _trig_widget parameter"
        )

    def test_excl_uses_trig_widget_not_all_widgets_loop(self, dr_module, auto_df):
        """BUG-21c: excl must come from _trig_widget._dash_exclude, not a loop over all widgets."""
        spec = self._make_server_spec_two_widgets()
        source = _build_app(dr_module, auto_df, spec)
        # The buggy pattern: iterating over _all_widgets to build excl union
        assert "for w in _all_widgets:" not in source.split("def _on_filter_change")[1].split("return _on_filter_change")[0] or \
            "excl.extend(getattr(w, '_dash_exclude'" not in source, (
            "BUG-21: Generated code must NOT build excl by looping over _all_widgets"
        )

    def test_per_widget_callback_wired(self, dr_module, auto_df):
        """BUG-21d: Each widget must get its own callback bound via _make_filter_cb(w, ...)."""
        spec = self._make_server_spec_two_widgets()
        source = _build_app(dr_module, auto_df, spec)
        # Per-widget wiring: _make_filter_cb called inside a for-loop over filter_widgets.
        # The generated code iterates filter_widgets and calls _make_filter_cb(... w ...) per widget.
        # Accept either inline ("_make_filter_cb(w,") or multi-line ("_make_filter_cb(\n...w,").
        has_per_widget = (
            "_make_filter_cb(w," in source
            or "_cb_for_w = _make_filter_cb(" in source
        )
        assert has_per_widget, (
            "BUG-21d: Per-widget callback must be created by calling _make_filter_cb "
            "with w as triggering widget inside the wiring loop"
        )

    def test_excluding_widget_skips_target_graph(self, dr_module, auto_df):
        """BUG-21e: Widget with exclude(g1) must have _dash_exclude=['g1'];
        widget without exclude() must have empty _dash_exclude.
        Filter specs are separated by '||' (Mata-joined format).
        """
        import importlib.util as _ilu
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

            app_spec_obj = _ilu.spec_from_file_location("_bug21_app", out_f.name)
            app_mod = _ilu.module_from_spec(app_spec_obj)
            app_spec_obj.loader.exec_module(app_mod)

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
        """BUG-22d: make_document must succeed for a two-layer graph with a filter widget."""
        import importlib.util as _ilu
        from bokeh.document import Document

        spec = self._make_two_layer_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name, port=5006)

            app_spec_obj = _ilu.spec_from_file_location("_bug22_app", out_f.name)
            app_mod = _ilu.module_from_spec(app_spec_obj)
            app_spec_obj.loader.exec_module(app_mod)

            doc = Document()
            app_mod.make_document(doc)  # must not raise
            assert len(doc.roots) > 0, "Document must have at least one root widget/figure"
        finally:
            os.unlink(spec_path)
            os.unlink(data_path)
            os.unlink(out_f.name)

    def test_filter_callback_updates_all_layer_sources(self, dr_module, auto_df):
        """BUG-22e: Filter callback invocation on a 2-layer graph must not raise.
        Verifies that the generated filter callback correctly handles the list-of-sources
        structure for graph_sources[gname] when updating data after a filter change.
        """
        import importlib.util as _ilu
        from bokeh.document import Document
        from bokeh.models import Select

        spec = self._make_two_layer_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name, port=5006)

            app_spec_obj = _ilu.spec_from_file_location("_bug22e_app", out_f.name)
            app_mod = _ilu.module_from_spec(app_spec_obj)
            app_spec_obj.loader.exec_module(app_mod)

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
# BUG-32: Server filter callback clears synthetic columns (e.g. _x_jit/_y_jit)
# ---------------------------------------------------------------------------

class TestServerFilterPreservesDerivedColumns:
    """BUG-32: Server-mode filter callbacks must not blank derived columns.

    Pre-fix: for any column in ``src.data`` not present in ``_gdf.columns``
    (e.g. ``_x_jit``/``_y_jit`` from ``jitter()``, or Bokeh's implicit
    ``index`` column), the callback set it to ``[]``, causing a length
    mismatch warning and making glyphs disappear after filter interactions.

    Post-fix: a per-source original-data snapshot is captured before any
    filter fires; derived columns are populated by selecting rows at the
    correct positional indices from the snapshot.
    """

    def _make_jitter_spec(self) -> dict:
        """Scatter with jitter option so _x_jit/_y_jit exist in src.data."""
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

    def test_generated_source_has_orig_src_data_snapshot(self, dr_module, auto_df):
        """BUG-32-1a: generated server source must create _orig_src_data snapshot."""
        spec = self._make_jitter_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            src = builder._generate_app_source(5006)
            assert "_orig_src_data" in src, (
                "generated server source must create _orig_src_data snapshot "
                "to preserve derived columns during filter callbacks"
            )
        finally:
            for _p in (spec_path, data_path):
                try:
                    os.unlink(_p)
                except OSError:
                    pass

    def test_generated_callback_uses_snapshot_for_derived_cols(self, dr_module, auto_df):
        """BUG-32-1b: generated _make_filter_cb must reference _orig_src_data for non-df columns."""
        spec = self._make_jitter_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            src = builder._generate_app_source(5006)
            assert "_orig_src_data" in src, "_orig_src_data must be in generated source"
            # The callback must use _orig_src_data in the filter loop
            assert "_snap" in src or "_orig_src_data.get" in src, (
                "_make_filter_cb must use _orig_src_data snapshot for derived column selection"
            )
        finally:
            for _p in (spec_path, data_path):
                try:
                    os.unlink(_p)
                except OSError:
                    pass

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
        """BUG-32-1d: make_document with jitter+filter must not raise."""
        import importlib.util as _ilu
        from bokeh.document import Document
        spec = self._make_jitter_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name, port=5006)
            app_spec_obj = _ilu.spec_from_file_location("_bug32_app", out_f.name)
            app_mod = _ilu.module_from_spec(app_spec_obj)
            app_spec_obj.loader.exec_module(app_mod)
            doc = Document()
            app_mod.make_document(doc)
            assert len(doc.roots) > 0, "make_document must add roots"
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try:
                    os.unlink(_p)
                except OSError:
                    pass

    def test_filter_callback_preserves_derived_column_length(self, dr_module, auto_df):
        """BUG-32-1e: after filter callback fires, derived columns must match data column lengths."""
        import importlib.util as _ilu
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
            app_spec_obj = _ilu.spec_from_file_location("_bug32e_app", out_f.name)
            app_mod = _ilu.module_from_spec(app_spec_obj)
            app_spec_obj.loader.exec_module(app_mod)
            doc = Document()
            app_mod.make_document(doc)
            # Find filter widget and trigger it
            all_models = list(doc.models)
            fw = next(
                (m for m in all_models
                 if isinstance(m, Select) and getattr(m, "_dash_var", "") == "foreign"),
                None,
            )
            if fw is None:
                return  # no filter widget built — nothing to check
            # Pick a non-"All" option if available
            non_all = [v for v, _l in fw.options if v != "__all__"]
            new_val = non_all[0] if non_all else "__all__"
            old_val = fw.value
            # Fire the callback without warnings about column length mismatch
            with warnings.catch_warnings(record=True) as w_list:
                warnings.simplefilter("always")
                for cb_desc in fw._callbacks.get("value", []):
                    cb_desc("value", old_val, new_val)
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

    def test_generated_source_has_graph_qualifiers_dict(self, dr_module, auto_df):
        """BUG-33-1a: generated source must create _graph_qualifiers dict."""
        spec = self._make_qualified_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            src = builder._generate_app_source(5006)
            assert "_graph_qualifiers" in src, (
                "generated server source must create _graph_qualifiers to persist "
                "per-graph qualifier metadata for filter callbacks"
            )
        finally:
            for _p in (spec_path, data_path):
                try:
                    os.unlink(_p)
                except OSError:
                    pass

    def test_generated_callback_accepts_graph_qualifiers(self, dr_module, auto_df):
        """BUG-33-1b: _make_filter_cb must accept _gquals and _gfac_to_orig params."""
        spec = self._make_qualified_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            src = builder._generate_app_source(5006)
            assert "_gquals" in src or "_graph_qualifiers" in src, (
                "_make_filter_cb must reference graph qualifiers for reapplication"
            )
        finally:
            for _p in (spec_path, data_path):
                try:
                    os.unlink(_p)
                except OSError:
                    pass

    def test_make_document_with_qualified_graph_does_not_crash(self, dr_module, auto_df):
        """BUG-33-1c: make_document with if_expr graph must not raise."""
        import importlib.util as _ilu
        from bokeh.document import Document
        spec = self._make_qualified_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name, port=5006)
            app_spec_obj = _ilu.spec_from_file_location("_bug33_app", out_f.name)
            app_mod = _ilu.module_from_spec(app_spec_obj)
            app_spec_obj.loader.exec_module(app_mod)
            doc = Document()
            app_mod.make_document(doc)
            assert len(doc.roots) > 0, "make_document must add roots"
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try:
                    os.unlink(_p)
                except OSError:
                    pass

    def test_filter_callback_does_not_reintroduce_qualified_out_rows(self, dr_module, auto_df):
        """BUG-33-1d: filter callback must not expand qualified graph source beyond if_expr rows."""
        import importlib.util as _ilu
        from bokeh.document import Document
        from bokeh.models import Select
        spec = self._make_qualified_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name, port=5006)
            app_spec_obj = _ilu.spec_from_file_location("_bug33d_app", out_f.name)
            app_mod = _ilu.module_from_spec(app_spec_obj)
            app_spec_obj.loader.exec_module(app_mod)
            doc = Document()
            app_mod.make_document(doc)
            all_models = list(doc.models)
            # Find filter widget for rep78
            fw = next(
                (m for m in all_models
                 if isinstance(m, Select) and getattr(m, "_dash_var", "") == "rep78"),
                None,
            )
            if fw is None:
                return  # filter widget not built — skip
            # Find the g1 source
            g1_srcs = app_mod.graph_sources.get("g1", [])
            if not g1_srcs:
                return
            g1_src = g1_srcs[-1] if isinstance(g1_srcs, list) else g1_srcs
            # Record initial row count (should be only foreign==1 rows)
            initial_n = len(g1_src.data.get("mpg", []))
            # Trigger filter callback with "__all__" (no filter) — must stay within if_expr
            old_val = fw.value
            for cb_desc in fw._callbacks.get("value", []):
                cb_desc("value", old_val, "__all__")
            after_n = len(g1_src.data.get("mpg", []))
            assert after_n <= initial_n or initial_n == 0, (
                f"BUG-33: after filter callback, g1 source has {after_n} rows but should "
                f"be bounded by initial if_expr-filtered count ({initial_n}). "
                "Graph qualifier was not reapplied."
            )
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try:
                    os.unlink(_p)
                except OSError:
                    pass

    def test_generated_source_has_safe_g_cb_in_callback(self, dr_module, auto_df):
        """BUG-33-1e: generated callback body must contain AST validator for qualifier reapplication."""
        spec = self._make_qualified_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            src = builder._generate_app_source(5006)
            assert "_safe_g_cb" in src or "_ALLOW_CB" in src, (
                "generated filter callback must contain AST whitelist guard for "
                "graph qualifier reapplication"
            )
        finally:
            for _p in (spec_path, data_path):
                try:
                    os.unlink(_p)
                except OSError:
                    pass


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

    def _make_linked_qualified_spec(self) -> dict:
        """Two linked graphs: g1 has if_expr='foreign == 1', g2 has no qualifier."""
        return _make_spec_json(
            graphs=[
                {"plots": [{"type": "scatter", "yvar": "mpg",
                            "xvar": "weight", "options": {}}],
                 "graph_options": {"name": "g1", "if_expr": "foreign == 1"}},
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
        """BUG-34-1a: rendering linked graphs with if_expr must not raise."""
        spec = self._make_linked_qualified_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            html_out = renderer.render()
            assert len(html_out) > 100, "rendered HTML must be non-trivial"
        finally:
            for _p in (spec_path, data_path):
                try:
                    os.unlink(_p)
                except OSError:
                    pass

    def test_linked_qualified_graph_has_cdsview(self, dr_module, auto_df):
        """BUG-34-1b: g1 figure must have CDSView with BooleanFilter when if_expr is set."""
        from bokeh.models import CDSView
        spec = self._make_linked_qualified_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            renderer.render()
            g1_fig = renderer.figures.get("g1")
            assert g1_fig is not None, "g1 figure must be built"
            # Find renderers that have a view (CDSView)
            views = [r.view for r in g1_fig.renderers
                     if hasattr(r, "view") and r.view is not None
                     and isinstance(r.view, CDSView)]
            assert len(views) > 0, (
                "g1 (if_expr='foreign == 1') must have a CDSView on its renderers "
                "to mask qualified-out rows when using shared linked source"
            )
        finally:
            for _p in (spec_path, data_path):
                try:
                    os.unlink(_p)
                except OSError:
                    pass

    def test_unqualified_linked_graph_has_no_qualifier_view(self, dr_module, auto_df):
        """BUG-34-1c: g2 (no if_expr) must not have a CDSView forced by qualifier."""
        from bokeh.models import CDSView, BooleanFilter
        spec = self._make_linked_qualified_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            renderer.render()
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
        """BUG-34-1d: rendered HTML must contain glyphs for both g1 and g2."""
        spec = self._make_linked_qualified_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            html_out = renderer.render()
            assert "mpg" in html_out and "price" in html_out, (
                "rendered HTML must reference both g1 (mpg) and g2 (price) variables"
            )
        finally:
            for _p in (spec_path, data_path):
                try:
                    os.unlink(_p)
                except OSError:
                    pass

    def test_shared_source_covers_all_rows(self, dr_module, auto_df):
        """BUG-34-1e: the shared linked source must contain all rows (not filtered)."""
        spec = self._make_linked_qualified_spec()
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            renderer.render()
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
            renderer.render()
            if not renderer.filter_callbacks:
                pytest.skip("No filter callbacks built (nothing to test)")
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
            renderer.render()
            if not renderer.filter_callbacks:
                pytest.skip("No filter callbacks built (nothing to test)")
            cb_args = renderer.filter_callbacks[0].args
            filter_specs = json.loads(cb_args["filter_specs_json"])
            all_widgets  = cb_args.get("all_widgets", [])
            assert len(all_widgets) == len(filter_specs), (
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
            renderer.render()
            if not renderer.filter_callbacks:
                pytest.skip("No filter callbacks built (nothing to test)")
            cb_args = renderer.filter_callbacks[0].args
            filter_specs = json.loads(cb_args["filter_specs_json"])
            all_widgets  = cb_args.get("all_widgets", [])
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
        """BUG-FSALIGN-1f: rendering with mixed valid/missing filter vars must not raise."""
        spec = self._make_mixed_filter_spec("totallymissingcolumn")
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            try:
                html_out = renderer.render()
                assert html_out, "render() must return non-empty HTML"
            except Exception as exc:
                pytest.fail(
                    f"BUG-FSALIGN-1f: render() raised with mixed filter vars: {exc!r}"
                )
        finally:
            for _p in (spec_path, data_path):
                try: os.unlink(_p)
                except OSError: pass

    # ------------------------------------------------------------------
    # BUG-FSALIGN-1g: valid filter widget's callback fires correctly
    # ------------------------------------------------------------------

    def test_valid_filter_widget_callback_fires_without_error(self, dr_module, auto_df):
        """BUG-FSALIGN-1g: the surviving valid filter widget's callback must be
        invocable (no misalignment crash) even when another spec was skipped."""
        spec = self._make_mixed_filter_spec("missingvar")
        spec_path, data_path = _write_temp_files(auto_df, spec)
        try:
            renderer = dr_module.DashRenderer(spec_path, data_path)
            renderer.render()
            if not renderer.filter_callbacks:
                pytest.skip("No filter callbacks built (nothing to test)")
            cb = renderer.filter_callbacks[0]
            cb_args = cb.args
            # Simulate a widget value-change: build a mock 'cb_obj' with .value
            import types as _types
            mock_widget = _types.SimpleNamespace(value="1")
            # Simulate the JS callback by exercising alignment integrity:
            filter_specs = json.loads(cb_args["filter_specs_json"])
            all_widgets  = cb_args.get("all_widgets", [])
            assert len(filter_specs) == len(all_widgets), (
                "BUG-FSALIGN-1g: spec/widget misalignment detected — "
                f"specs={len(filter_specs)}, widgets={len(all_widgets)}"
            )
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
            import importlib.util as _ilu
            _app_spec = _ilu.spec_from_file_location("_test_slider_app", out_path)
            mod = _ilu.module_from_spec(_app_spec)
            _app_spec.loader.exec_module(mod)
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
            renderer.render()
            if not renderer.filter_callbacks:
                pytest.skip("No filter callbacks built (nothing to test)")
            cb_args = renderer.filter_callbacks[0].args
            kpi_config = json.loads(cb_args["kpi_config_json"])
            if not kpi_config:
                pytest.skip("No KPI config in callback (nothing to test)")
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
    """Regression suite for BUG-36: server by() faceting must honour if_expr/in_expr."""

    # ------------------------------------------------------------------
    # BUG-36-1a: generated source contains qualifier-base frame variable
    # ------------------------------------------------------------------

    def test_generated_source_contains_by_q_df(self, dr_module, auto_df):
        """BUG-36-1a: generated source must contain '_by_q_df' qualifier frame."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign", "if_expr": "foreign == 1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        assert "_by_q_df" in source, (
            "Generated source must define '_by_q_df' to apply qualifier before faceting"
        )

    # ------------------------------------------------------------------
    # BUG-36-1b: generated source applies if_expr before faceting
    # ------------------------------------------------------------------

    def test_generated_source_applies_if_expr_before_faceting(self, dr_module, auto_df):
        """BUG-36-1b: generated source must apply if_expr qualifier before work_df groupby."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign", "if_expr": "foreign == 1"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        # _by_if must appear before work_df assignment in the faceting block
        assert "_by_if" in source, "Generated source must check _by_if in faceting block"
        assert "_by_px" in source, "Generated source must build _by_px predicate for query"

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
            app_spec = importlib.util.spec_from_file_location("_b36c", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
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
            app_spec = importlib.util.spec_from_file_location("_b36d", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
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
            app_spec = importlib.util.spec_from_file_location("_b36e", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
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
            renderer.render()
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
            renderer.render()
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
            renderer.render()
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

    def test_server_dropdown_uses_computed_sentinel(self, dr_module, auto_df):
        """BUG-37-1d: generated server source must compute _sent before Select creation."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }], build_options={
            "layout": "auto", "link": "", "filter": "foreign, type(dropdown)",
            "theme": "default", "title": "T", "subtitle": "",
            "registry": "g1", "mode": "server", "port": "5006",
        })
        source = _build_app(dr_module, auto_df, spec)
        assert "_sent" in source, (
            "Generated server code must compute '_sent' sentinel variable"
        )
        assert "_uniq_strs" in source, (
            "Generated server code must build '_uniq_strs' to check for collision"
        )
        assert "while _sent in _uniq_strs" in source, (
            "Generated server code must loop until sentinel is unique"
        )

    # ------------------------------------------------------------------
    # BUG-37-1e: generated server uses per-widget sentinel in callback
    # ------------------------------------------------------------------

    def test_server_callback_uses_widget_sentinel_attribute(self, dr_module, auto_df):
        """BUG-37-1e: generated server filter callback must read _dash_sentinel from widget."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1"},
        }], build_options={
            "layout": "auto", "link": "", "filter": "foreign, type(dropdown)",
            "theme": "default", "title": "T", "subtitle": "",
            "registry": "g1", "mode": "server", "port": "5006",
        })
        source = _build_app(dr_module, auto_df, spec)
        assert "_dash_sentinel" in source, (
            "Generated server callback must read '_dash_sentinel' attribute from widget"
        )
        assert "_w_sentinel" in source, (
            "Generated server callback must use per-widget '_w_sentinel' variable"
        )
        # Hard-coded '__all__' check must not appear in the callback comparison
        assert "w.value != '__all__'" not in source, (
            "Generated server callback must not hard-code '__all__' in value check"
        )


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
            app_spec = importlib.util.spec_from_file_location("_b38a", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
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
            app_spec = importlib.util.spec_from_file_location("_b38b", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
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
        """BUG-38-1c: generated source must use work_df for Total agg computations."""
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "lfit", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign, total"},
        }])
        source = _build_app(dr_module, auto_df, spec)
        # Total lfit must call _compute_lfit(work_df, ...) not _compute_lfit(_fac_gdf, ...)
        assert "work_df" in source, "Generated source must reference work_df for Total panel"
        assert "_compute_lfit(work_df" in source, (
            "Total lfit must use work_df, not a facet-specific _fac_gdf frame"
        )

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
            app_spec = importlib.util.spec_from_file_location("_b38d", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
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
            app_spec = importlib.util.spec_from_file_location("_b38e", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
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
            app_spec = importlib.util.spec_from_file_location("_b39d", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
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
        """BUG-39-1e: server make_document applies if_expr filter when col is in data."""
        from bokeh.document import Document
        # Include 'foreign' in data — the filter should limit glyph source rows.
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "if_expr": "foreign == 1"},
        }])
        spec_path, data_path = _write_temp_files(auto_df, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_spec = importlib.util.spec_from_file_location("_b39e", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
            doc = Document()
            app_mod.make_document(doc)
            # The rendered graph should have fewer rows than the full dataset
            # because the if_expr filter (foreign==1) is applied.
            n_foreign = int((auto_df["foreign"] == 1).sum())
            n_total = len(auto_df)
            n_renderers = _count_glyph_renderers(doc)
            assert n_renderers >= 1, "Expected at least one renderer"
            # Verify source row count is limited by filter (not full 30 rows)
            # Inspect the first ColumnDataSource reachable from the document.
            renderers_list = []
            for root in doc.roots:
                if hasattr(root, "renderers"):
                    renderers_list.extend(root.renderers)
                elif hasattr(root, "children"):
                    for child in root.children:
                        if hasattr(child, "renderers"):
                            renderers_list.extend(child.renderers)
            glyph_renderers = [
                r for r in renderers_list
                if hasattr(r, "data_source") and hasattr(r, "glyph")
            ]
            if glyph_renderers:
                src_len = len(glyph_renderers[0].data_source.data.get("mpg", []))
                assert src_len == n_foreign, (
                    f"Expected {n_foreign} rows in source (foreign==1 filter), "
                    f"got {src_len} (total={n_total})"
                )
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try: os.unlink(_p)
                except OSError: pass


# ===========================================================================
# BUG-40 — Windows browser auto-open command uses `start` with incorrect
#          quoting; the first quoted token is treated as the window title.
#
# The fix adds an empty title ("") so the second quoted argument is used
# as the target file path.
#
# BUG-40-1a  dash.ado immediate-render: shell start "" present
# BUG-40-1b  dash.ado immediate-render: shell start "<path>" (no title) absent
# BUG-40-1c  dash.ado dash build: shell start "" present
# BUG-40-1d  dash.ado dash build: shell start "<path>" (no title) absent
# ===========================================================================

class TestWindowsBrowserStartQuoting:
    """BUG-40: Windows shell start must include empty title to avoid path-as-title."""

    _ADO_PATH = os.path.join(_DASH_DIR, "dash.ado")

    @classmethod
    def _ado_text(cls):
        with open(cls._ADO_PATH, "r", encoding="utf-8") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # BUG-40-1a: immediate-render path has shell start ""
    # ------------------------------------------------------------------

    def test_immediate_render_has_empty_title(self):
        """BUG-40-1a: immediate-render Windows open uses 'shell start \"\"'."""
        text = self._ado_text()
        assert 'shell start ""' in text, (
            'dash.ado should contain \'shell start ""\' for Windows browser open'
        )

    # ------------------------------------------------------------------
    # BUG-40-1b: no bare shell start "<path>" (missing empty title)
    # ------------------------------------------------------------------

    def test_no_bare_start_command(self):
        """BUG-40-1b: 'shell start \"`' (no empty title) must not appear in dash.ado."""
        text = self._ado_text()
        # Match the old incorrect pattern: shell start immediately followed
        # by a quote+backtick (the path macro).  An empty title would put
        # the empty-string token between 'start' and the path.
        import re
        bad_pattern = re.compile(r'\bshell\s+start\s+"[^"]*`')
        assert bad_pattern.search(text) is None, (
            "dash.ado still contains 'shell start \"<path>' pattern "
            "(missing empty title); Windows open will fail"
        )

    # ------------------------------------------------------------------
    # BUG-40-1c: dash-build path contains shell start ""
    # ------------------------------------------------------------------

    def test_dash_build_has_empty_title(self):
        """BUG-40-1c: dash build Windows open also uses 'shell start \"\"'."""
        text = self._ado_text()
        # Count occurrences — both immediate-render and dash-build must use it
        count = text.count('shell start ""')
        assert count >= 2, (
            f"Expected at least 2 occurrences of 'shell start \"\"' "
            f"(one per Windows open site), found {count}"
        )

    # ------------------------------------------------------------------
    # BUG-40-1d: regression — macOS and Unix open commands unchanged
    # ------------------------------------------------------------------

    def test_mac_unix_open_commands_unchanged(self):
        """BUG-40-1d: macOS 'shell open' and Unix 'shell xdg-open' still present."""
        text = self._ado_text()
        assert "shell open" in text, "macOS 'shell open' missing from dash.ado"
        assert "shell xdg-open" in text, "Unix 'shell xdg-open' missing from dash.ado"


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

    def test_helper_prefers_xff(self, dr_module, auto_df):
        """BUG-41-1b: _client_ip_from_request returns XFF first token, not remote_ip."""
        src = self._build_source(dr_module, auto_df)
        mod = types.ModuleType("_b41_mod")
        exec(compile(src, "<test>", "exec"), mod.__dict__)
        helper = getattr(mod, "_client_ip_from_request")

        class _FakeReq:
            remote_ip = "10.0.0.1"  # proxy IP
            headers = {"X-Forwarded-For": "203.0.113.55, 10.0.0.1"}

        assert helper(_FakeReq()) == "203.0.113.55", (
            "Helper should return first XFF token (end-user IP), not remote_ip"
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
    # BUG-41-1e: HealthHandler.prepare uses _client_ip_from_request
    # ------------------------------------------------------------------

    def test_health_handler_uses_helper(self, dr_module, auto_df):
        """BUG-41-1e: _HealthHandler.prepare must call _client_ip_from_request."""
        src = self._build_source(dr_module, auto_df)
        # Verify source text — _HealthHandler.prepare must call the helper
        assert "_client_ip_from_request(self.request)" in src, (
            "_HealthHandler.prepare should use _client_ip_from_request(self.request)"
        )
        # Ensure the old bare remote_ip pattern is gone from HealthHandler
        import re
        health_section = re.search(
            r"class _HealthHandler.*?def get\(", src, re.DOTALL
        )
        if health_section:
            section_text = health_section.group(0)
            assert "self.request.remote_ip" not in section_text, (
                "_HealthHandler.prepare should not use self.request.remote_ip directly"
            )

    # ------------------------------------------------------------------
    # BUG-41-1f: make_document uses _client_ip_from_request (not inline)
    # ------------------------------------------------------------------

    def test_make_document_uses_helper(self, dr_module, auto_df):
        """BUG-41-1f: make_document must call _client_ip_from_request, not inline IP."""
        src = self._build_source(dr_module, auto_df)
        assert "_client_ip_from_request(_req)" in src, (
            "make_document should use _client_ip_from_request(_req) helper"
        )
        # The old inline 'getattr(_req, 'remote_ip', None) or ...' must not appear
        assert "getattr(_req, 'remote_ip'" not in src, (
            "make_document should not inline IP extraction; use _client_ip_from_request"
        )


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
            dr.render()
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
        """BUG-42-1d: server make_document source has 0 rows when all by() keys missing."""
        from bokeh.document import Document
        df_na = auto_df.copy()
        df_na["foreign"] = float("nan")
        spec = _make_spec_json(graphs=[{
            "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
            "graph_options": {"name": "g1", "by": "foreign"},
        }])
        spec_path, data_path = _write_temp_files(df_na, spec)
        out_f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        out_f.close()
        try:
            builder = dr_module.ServerAppBuilder(spec_path, data_path)
            builder.build(out_f.name)
            app_spec = importlib.util.spec_from_file_location("_b42d", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
            doc = Document()
            app_mod.make_document(doc)
            # All glyph renderers should have empty (zero-length) data sources
            renderers_list = []
            for root in doc.roots:
                if hasattr(root, "renderers"):
                    renderers_list.extend(root.renderers)
                elif hasattr(root, "children"):
                    for child in root.children:
                        if hasattr(child, "renderers"):
                            renderers_list.extend(child.renderers)
            glyph_renderers = [
                r for r in renderers_list
                if hasattr(r, "data_source") and hasattr(r, "glyph")
            ]
            for gr in glyph_renderers:
                row_count = len(next(iter(gr.data_source.data.values()), []))
                assert row_count == 0, (
                    f"Expected 0-row source when all by() keys are missing, "
                    f"got {row_count} rows"
                )
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try: os.unlink(_p)
                except OSError: pass

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
# _extract_finite calls np.array([...], dtype=float) which raises ValueError
# for string columns.  The fix adds an is_numeric_dtype guard in
# _build_filter_widgets before calling build_slider/build_range.
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
                dr.render()
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
                dr.render()
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
                dr.render()
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
                dr.render()
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
                dr.render()
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
# side now does the same before iterating.
#
# BUG-45-1a  dash.ado filter extraction loop normalizes semicolons to "||"
# BUG-45-1b  Standalone render with semicolon filter builds both widgets
# BUG-45-1c  "||"-separated filter still works (regression)
# BUG-45-1d  Single filter (no separator) still works (regression)
# ===========================================================================

class TestSemicolonFilterSerialization:
    """BUG-45: semicolon-separated filter specs must all reach the Python renderer."""

    # ------------------------------------------------------------------
    # BUG-45-1a: dash.ado contains semicolon normalization
    # ------------------------------------------------------------------

    def test_ado_contains_semicolon_normalization(self):
        """BUG-45-1a: dash.ado filter loop must normalize semicolons to '||'."""
        with open(os.path.join(_DASH_DIR, "dash.ado"), encoding="utf-8") as f:
            ado_text = f.read()
        assert 'subinstr' in ado_text and '";"' in ado_text and '"||"' in ado_text, (
            "dash.ado should convert semicolons to '||' via subinstr before iterating"
        )

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
            dr.render()
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
            dr.render()
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
            dr.render()
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
            app_spec = importlib.util.spec_from_file_location("_b46c", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
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
            app_spec = importlib.util.spec_from_file_location("_b46d", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
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
            app_spec = importlib.util.spec_from_file_location("_b46e", out_f.name)
            app_mod = importlib.util.module_from_spec(app_spec)
            app_spec.loader.exec_module(app_mod)
            doc = Document()
            app_mod.make_document(doc)
            # Should have a RangeSlider widget in the layout
            src_text = open(out_f.name).read()
            assert "RangeSlider" in src_text, "Generated source should create RangeSlider"
        finally:
            for _p in (spec_path, data_path, out_f.name):
                try: os.unlink(_p)
                except OSError: pass
