"""
test_phase5.py
Tests for Phase 5: missing abbreviations and per-graph if/in filtering (Bug 5).

Run with:  pytest test/test_phase5.py -v
"""
import sys
import os
import json
import tempfile
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dash_render import DashRenderer


# ================================================================
# Helpers (from test_pipeline_integration.py)
# ================================================================

def _make_data_json(columns: dict) -> dict:
    col_names = list(columns.keys())
    n_rows = len(next(iter(columns.values())))
    rows = []
    for i in range(n_rows):
        row = {c: columns[c][i] for c in col_names}
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


DATA_20 = _make_data_json({
    "y": [float(i) for i in range(1, 21)],
    "x": [float(i) for i in range(1, 21)],
})


# ================================================================
# Bug 5 — per-graph in_expr filtering
# ================================================================

class TestPerGraphInFilter:
    """P5-01 through P5-04: in_expr restricts rows per graph."""

    def _spec_with_in(self, in_expr: str, name: str = "g1") -> dict:
        graph = {
            "plots": [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}],
            "graph_options": {"name": name},
            "if_expr": "",
            "in_expr": in_expr,
        }
        return _make_master_spec([graph])

    def test_in_expr_ten_rows(self):
        """P5-01: in_expr '1/10' → source has exactly 10 rows."""
        renderer = _build_renderer(self._spec_with_in("1/10"), DATA_20)
        sources = renderer._setup_sources()
        src = sources["g1"]
        n = len(src.data["y"])
        assert n == 10, f"Expected 10 rows, got {n}"

    def test_in_expr_five_rows(self):
        """P5-02: in_expr '1/5' → source has exactly 5 rows."""
        renderer = _build_renderer(self._spec_with_in("1/5"), DATA_20)
        sources = renderer._setup_sources()
        n = len(sources["g1"].data["y"])
        assert n == 5, f"Expected 5 rows, got {n}"

    def test_in_expr_all_rows(self):
        """P5-03: in_expr '1/20' → all 20 rows."""
        renderer = _build_renderer(self._spec_with_in("1/20"), DATA_20)
        sources = renderer._setup_sources()
        n = len(sources["g1"].data["y"])
        assert n == 20, f"Expected 20 rows, got {n}"

    def test_in_expr_missing_returns_full(self):
        """P5-04: empty in_expr → source has all rows."""
        renderer = _build_renderer(self._spec_with_in(""), DATA_20)
        sources = renderer._setup_sources()
        n = len(sources["g1"].data["y"])
        assert n == 20, f"Expected 20 rows, got {n}"


# ================================================================
# Bug 5 — per-graph if_expr filtering
# ================================================================

class TestPerGraphIfFilter:
    """P5-05 through P5-08: if_expr restricts rows per graph."""

    def _spec_with_if(self, if_expr: str, name: str = "g1") -> dict:
        graph = {
            "plots": [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}],
            "graph_options": {"name": name},
            "if_expr": if_expr,
            "in_expr": "",
        }
        return _make_master_spec([graph])

    def test_if_expr_filters_rows(self):
        """P5-05: if_expr 'y > 10' → only rows where y > 10 (10 rows)."""
        renderer = _build_renderer(self._spec_with_if("y > 10"), DATA_20)
        sources = renderer._setup_sources()
        y_vals = sources["g1"].data["y"]
        assert all(v > 10 for v in y_vals), "Not all values satisfy y > 10"
        # The rows themselves: all() of no rows is true, so a qualifier that
        # kept nothing passed.  y is 1..20, so y > 10 keeps 11..20.
        assert sorted(y_vals) == [float(i) for i in range(11, 21)], y_vals

    def test_if_expr_empty_returns_all(self):
        """P5-06: empty if_expr → source has all rows."""
        renderer = _build_renderer(self._spec_with_if(""), DATA_20)
        sources = renderer._setup_sources()
        n = len(sources["g1"].data["y"])
        assert n == 20

    def test_if_expr_invalid_no_crash(self):
        """P5-07: invalid if_expr → no crash, source has full or partial data."""
        renderer = _build_renderer(self._spec_with_if("INVALID %%% EXPR"), DATA_20)
        sources = renderer._setup_sources()
        # Must not raise; row count could be 0 or 20 (depending on pandas behaviour)
        assert "g1" in sources

    def test_if_expr_injection_blocked(self):
        """P5-08: if_expr with shell injection chars → blocked, source has data."""
        renderer = _build_renderer(
            self._spec_with_if("; import os; os.system('id')"), DATA_20
        )
        sources = renderer._setup_sources()
        assert "g1" in sources

    def test_if_expr_getattr_blocked(self):
        """P5-sec01: if_expr with getattr() call must be blocked."""
        renderer = _build_renderer(
            self._spec_with_if("getattr(x, '__class__')"), DATA_20
        )
        sources = renderer._setup_sources()
        # Must not raise; full data or empty (not partial)
        assert "g1" in sources

    def test_if_expr_setattr_blocked(self):
        """P5-sec02: if_expr with setattr() call must be blocked."""
        renderer = _build_renderer(
            self._spec_with_if("setattr(x, 'foo', 1)"), DATA_20
        )
        sources = renderer._setup_sources()
        assert "g1" in sources

    def test_two_graphs_different_if_expr(self):
        """P5-09: two graphs with different if_expr → disjoint CDS data."""
        g1 = {
            "plots": [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}],
            "graph_options": {"name": "g1"},
            "if_expr": "y <= 10", "in_expr": "",
        }
        g2 = {
            "plots": [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}],
            "graph_options": {"name": "g2"},
            "if_expr": "y > 10", "in_expr": "",
        }
        spec = _make_master_spec([g1, g2])
        renderer = _build_renderer(spec, DATA_20)
        sources = renderer._setup_sources()
        y1 = set(sources["g1"].data["y"])
        y2 = set(sources["g2"].data["y"])
        assert y1.isdisjoint(y2), "Graphs with opposite if_expr should have disjoint data"
        # Disjoint is true of an empty set too: each graph holds its ten.
        assert sorted(y1) == [float(i) for i in range(1, 11)], sorted(y1)
        assert sorted(y2) == [float(i) for i in range(11, 21)], sorted(y2)


# ================================================================
# Phase 5 — _apply_graph_filter unit tests
# ================================================================

class TestApplyGraphFilter:
    @pytest.fixture
    def renderer(self):
        graph = {
            "plots": [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}],
            "graph_options": {"name": "g1"},
            "if_expr": "", "in_expr": "",
        }
        r = _build_renderer(_make_master_spec([graph]), DATA_20)
        return r

    def test_no_filter_returns_full_df(self, renderer):
        """P5-10: no filters → full DataFrame."""
        g = {"if_expr": "", "in_expr": ""}
        df = renderer._apply_graph_filter(g)
        assert len(df) == 20

    def test_in_expr_slices_correctly(self, renderer):
        """P5-11: in_expr '3/7' → 5 rows (rows 3–7 inclusive, 1-based)."""
        g = {"if_expr": "", "in_expr": "3/7"}
        df = renderer._apply_graph_filter(g)
        assert len(df) == 5

    def test_if_expr_equality(self, renderer):
        """P5-12: if_expr 'x == 5' → 1 row."""
        g = {"if_expr": "x == 5", "in_expr": ""}
        df = renderer._apply_graph_filter(g)
        assert len(df) == 1 and list(df["x"])[0] == 5.0


# ================================================================
# P6-20: by() security and edge case tests
# ================================================================

class TestByFacetingSecurity:
    """Security hardening tests for by() faceting."""

    @pytest.fixture
    def renderer(self):
        """Renderer with a simple dataset for security tests."""
        data = {
            "y": [float(i) for i in range(1, 21)],
            "x": [float(i) for i in range(1, 21)],
            "grp": [float(i % 2) for i in range(20)],
        }
        data_json = _make_data_json(data)
        graph = {
            "plots": [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}],
            "graph_options": {"name": "g1", "by": "grp"},
            "if_expr": "", "in_expr": "",
        }
        spec = {
            "graphs": [graph], "kpis": [],
            "build_options": {"layout": "auto", "link": "", "filter": "",
                              "theme": "default", "title": "", "subtitle": "",
                              "registry": "g1"},
        }
        spec_fd, spec_path = tempfile.mkstemp(suffix=".json")
        data_fd, data_path = tempfile.mkstemp(suffix=".json")
        out_fd, out_path = tempfile.mkstemp(suffix=".html")
        try:
            with os.fdopen(spec_fd, "w") as f:
                json.dump(spec, f)
            with os.fdopen(data_fd, "w") as f:
                json.dump(data_json, f)
            os.close(out_fd)
            r = DashRenderer(spec_path, data_path, out_path)
        finally:
            for p in (spec_path, data_path, out_path):
                try:
                    os.unlink(p)
                except OSError:
                    pass
        return r

    def test_by_import_injection_blocked(self, renderer):
        """by('__import__(\"os\")') → falls back to no faceting."""
        g = {
            "plots": [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}],
            "graph_options": {"name": "g1", "by": '__import__("os")'},
            "if_expr": "", "in_expr": "",
        }
        groups = renderer._expand_by_groups(g)
        # Should return single unfaceted group (injection blocked)
        assert len(groups) == 1 and groups[0][0] == ""

    def test_by_eval_injection_blocked(self, renderer):
        """by('eval(\"1+1\")') → falls back to no faceting."""
        g = {
            "plots": [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}],
            "graph_options": {"name": "g1", "by": 'eval("1+1")'},
            "if_expr": "", "in_expr": "",
        }
        groups = renderer._expand_by_groups(g)
        assert len(groups) == 1 and groups[0][0] == ""

    def test_by_getattr_injection_blocked(self, renderer):
        """by('getattr(x, \"y\")') → falls back to no faceting."""
        g = {
            "plots": [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}],
            "graph_options": {"name": "g1", "by": 'getattr(x, "y")'},
            "if_expr": "", "in_expr": "",
        }
        groups = renderer._expand_by_groups(g)
        assert len(groups) == 1 and groups[0][0] == ""

    def test_by_shell_injection_blocked(self, renderer):
        """by('grp; rm -rf /') → falls back to no faceting."""
        g = {
            "plots": [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}],
            "graph_options": {"name": "g1", "by": "grp; rm -rf /"},
            "if_expr": "", "in_expr": "",
        }
        groups = renderer._expand_by_groups(g)
        assert len(groups) == 1 and groups[0][0] == ""

    def test_by_dunder_blocked(self, renderer):
        """by('__class__') → blocked by __ pattern."""
        g = {
            "plots": [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}],
            "graph_options": {"name": "g1", "by": "__class__"},
            "if_expr": "", "in_expr": "",
        }
        groups = renderer._expand_by_groups(g)
        assert len(groups) == 1 and groups[0][0] == ""

    def test_by_xss_in_facet_label_is_canvas_text(self):
        """An XSS payload in a by-variable's value label reaches the facet
        title as the text it is -- restated by WP-20.

        This used to assert the title was html-escaped.  A facet title is
        ``fig.title.text'', which Bokeh draws on the canvas; it is never
        parsed as HTML, so the escaping only put the entities on screen,
        and the per-facet KPI card, which is HTML, escaped it a second
        time.  The title is now raw (the KPI card escapes it once);
        test_label_sinks.py pins the canvas rendering.
        """
        data = {
            "y": [1.0, 2.0, 3.0, 4.0],
            "x": [1.0, 2.0, 3.0, 4.0],
            "grp": [0.0, 0.0, 1.0, 1.0],
        }
        data_json = _make_data_json(data)
        # Inject XSS in value labels
        data_json["StataJSON"]["valueLabels"] = {
            "grp_lbl": {"0": '<script>alert(1)</script>', "1": "Normal"}
        }
        data_json["StataJSON"]["valueLabelNames"] = {"grp": "grp_lbl"}
        graph = {
            "plots": [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}],
            "graph_options": {"name": "g1", "by": "grp"},
            "if_expr": "", "in_expr": "",
        }
        spec = {
            "graphs": [graph], "kpis": [],
            "build_options": {"layout": "auto", "link": "", "filter": "",
                              "theme": "default", "title": "", "subtitle": "",
                              "registry": "g1"},
        }
        spec_fd, spec_path = tempfile.mkstemp(suffix=".json")
        data_fd, data_path = tempfile.mkstemp(suffix=".json")
        out_fd, out_path = tempfile.mkstemp(suffix=".html")
        try:
            with os.fdopen(spec_fd, "w") as f:
                json.dump(spec, f)
            with os.fdopen(data_fd, "w") as f:
                json.dump(data_json, f)
            os.close(out_fd)
            r = DashRenderer(spec_path, data_path, out_path)
        finally:
            for p in (spec_path, data_path, out_path):
                try:
                    os.unlink(p)
                except OSError:
                    pass
        figs = r._build_figures()
        titles = [figs[k].title.text for k in figs if "__by__" in k]
        assert any("<script>alert(1)</script>" in t for t in titles), titles
        assert not any("&lt;" in t for t in titles), "escaped: " + repr(titles)


# ================================================================
# BUG-28: if_expr RCE via pandas.query() @-variable references
# ================================================================

class TestIfExprRceHardening:
    """Regression tests for BUG-28: if_expr must not allow arbitrary code
    execution via @ variable references in df.query(engine='python').

    Tests:
      BUG-RCE-1a  @ reference blocked by _validate_if_expr
      BUG-RCE-1b  attribute access (col.attr) blocked
      BUG-RCE-1c  function call (func()) blocked
      BUG-RCE-1d  @ PoC payload blocked end-to-end (no file created)
      BUG-RCE-1e  valid comparison expression allowed
      BUG-RCE-1f  _validate_if_expr helper exists and is callable
      BUG-RCE-1g  __dunder__ access blocked
      BUG-RCE-1h  import statement blocked
    """

    def _renderer_with_if(self, if_expr: str):
        graph = {
            "plots": [{"type": "scatter", "yvar": "y", "xvar": "x", "options": {}}],
            "graph_options": {"name": "g1"},
            "if_expr": if_expr,
            "in_expr": "",
        }
        return _build_renderer(_make_master_spec([graph]), DATA_20)

    # ------------------------------------------------------------------
    # BUG-RCE-1f: helper exists
    # ------------------------------------------------------------------

    def test_validate_if_expr_helper_exists(self):
        """BUG-RCE-1f: _validate_if_expr must be importable from dash_render."""
        from dash_render import _validate_if_expr
        assert callable(_validate_if_expr), "_validate_if_expr must be callable"

    # ------------------------------------------------------------------
    # BUG-RCE-1a: @ reference rejected
    # ------------------------------------------------------------------

    def test_at_reference_rejected(self):
        """BUG-RCE-1a: @ variable reference must be rejected by _validate_if_expr."""
        from dash_render import _validate_if_expr
        cols = ["x", "y"]
        assert not _validate_if_expr("@pd.io.common.os.system('id')", cols), \
            "_validate_if_expr must reject @ references"
        assert not _validate_if_expr("@local_var == 1", cols), \
            "_validate_if_expr must reject any @ reference"

    # ------------------------------------------------------------------
    # BUG-RCE-1b: attribute access rejected
    # ------------------------------------------------------------------

    def test_attribute_access_rejected(self):
        """BUG-RCE-1b: attribute chains must be rejected."""
        from dash_render import _validate_if_expr
        cols = ["x", "y"]
        assert not _validate_if_expr("x.__class__.__name__ == 'int'", cols), \
            "_validate_if_expr must reject attribute access"

    # ------------------------------------------------------------------
    # BUG-RCE-1c: function call rejected
    # ------------------------------------------------------------------

    def test_function_call_rejected(self):
        """BUG-RCE-1c: function calls must be rejected."""
        from dash_render import _validate_if_expr
        cols = ["x", "y"]
        assert not _validate_if_expr("len(x) > 0", cols), \
            "_validate_if_expr must reject function calls"
        assert not _validate_if_expr("x.apply(lambda v: v) > 0", cols), \
            "_validate_if_expr must reject method calls"

    # ------------------------------------------------------------------
    # BUG-RCE-1d: @ PoC end-to-end blocked (no side effect)
    # ------------------------------------------------------------------

    def test_at_poc_payload_blocked_end_to_end(self):
        """BUG-RCE-1d: reported PoC @pd.io.common.os.system must not execute."""
        import os
        import tempfile
        poc_file = os.path.join(tempfile.gettempdir(), "dash_bug28_rce_poc.txt")
        # Clean up in case a prior run left it
        try:
            os.unlink(poc_file)
        except FileNotFoundError:
            pass

        renderer = self._renderer_with_if(
            f"@pd.io.common.os.system('touch {poc_file}') == 0"
        )
        renderer._setup_sources()  # trigger filter evaluation

        assert not os.path.exists(poc_file), (
            "BUG-28: RCE payload executed — poc file was created. "
            "if_expr must block @ references before calling df.query()."
        )

    # ------------------------------------------------------------------
    # BUG-RCE-1e: valid comparison still works
    # ------------------------------------------------------------------

    def test_valid_comparison_expression_allowed(self):
        """BUG-RCE-1e: simple column comparisons must still be accepted."""
        from dash_render import _validate_if_expr
        cols = ["x", "y"]
        assert _validate_if_expr("y > 10", cols), \
            "_validate_if_expr must allow simple numeric comparisons"
        assert _validate_if_expr("(x == 5) & (y < 20)", cols), \
            "_validate_if_expr must allow combined comparisons"

    # ------------------------------------------------------------------
    # BUG-RCE-1g: __dunder__ blocked
    # ------------------------------------------------------------------

    def test_dunder_access_blocked(self):
        """BUG-RCE-1g: __dunder__ expressions must be rejected."""
        from dash_render import _validate_if_expr
        cols = ["x", "y"]
        assert not _validate_if_expr("x.__class__ == int", cols), \
            "_validate_if_expr must reject __dunder__ references"

    # ------------------------------------------------------------------
    # BUG-RCE-1h: import blocked
    # ------------------------------------------------------------------

    def test_import_keyword_blocked(self):
        """BUG-RCE-1h: expressions containing 'import' must be rejected."""
        from dash_render import _validate_if_expr
        cols = ["x", "y"]
        assert not _validate_if_expr("__import__('os').system('id') == 0", cols), \
            "_validate_if_expr must block __import__ calls"
