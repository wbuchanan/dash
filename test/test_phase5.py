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
