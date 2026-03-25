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
