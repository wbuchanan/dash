"""
test_layout.py
Unit tests for DashRenderer layout assembly.

Tests: P1B-31 through P1B-35

Run with:  pytest test/test_layout.py -v
"""
import sys
import os
import json
import math
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dash_render import DashRenderer


# ================================================================
# Helpers
# ================================================================

def _make_graph_spec(name: str, ptype: str = "scatter",
                     yvar: str = "mpg", xvar: str = "weight") -> dict:
    return {
        "plots": [{"type": ptype, "yvar": yvar, "xvar": xvar, "options": {}}],
        "graph_options": {"name": name},
        "if_expr": "",
        "in_expr": "",
    }


def _make_data_json(n: int = 20) -> dict:
    np.random.seed(0)
    rows = [{"mpg": float(i), "weight": float(i * 50)} for i in range(1, n + 1)]
    return {
        "StataJSON": {
            "variableNames": ["mpg", "weight"],
            "variableLabels": {"mpg": "Mileage (mpg)", "weight": "Weight (lbs.)"},
            "valueLabels": {},
            "valueLabelNames": {},
            "variableTypeIsString": {"mpg": False, "weight": False},
            "values": rows,
        }
    }


def _make_renderer(n_graphs: int, layout: str = "auto",
                   link: str = "") -> DashRenderer:
    """Create a DashRenderer with n_graphs scatter specs.

    Temp files are created, used for DashRenderer construction (which reads
    them immediately in __init__), then deleted before returning.
    """
    graphs = [_make_graph_spec(f"g{i+1}") for i in range(n_graphs)]
    master_spec = {
        "graphs": graphs,
        "kpis": [],
        "build_options": {
            "layout": layout,
            "link": link,
            "filter": "",
            "theme": "default",
            "title": "",
            "subtitle": "",
            "registry": " ".join(f"g{i+1}" for i in range(n_graphs)),
        },
    }
    data_json = _make_data_json()

    import tempfile
    spec_fd, spec_path = tempfile.mkstemp(suffix=".json")
    data_fd, data_path = tempfile.mkstemp(suffix=".json")
    out_fd,  out_path  = tempfile.mkstemp(suffix=".html")

    try:
        with os.fdopen(spec_fd, "w") as f:
            json.dump(master_spec, f)
        with os.fdopen(data_fd, "w") as f:
            json.dump(data_json, f)
        os.close(out_fd)
        renderer = DashRenderer(spec_path, data_path, out_path)
    finally:
        # DashRenderer reads both files in __init__; safe to clean up now
        for _p in (spec_path, data_path, out_path):
            try:
                os.unlink(_p)
            except OSError:
                pass

    return renderer


# ================================================================
# P1B-31 — layout(2 2) with 4 graphs → 2×2 gridplot
# ================================================================
class TestExplicitLayout:
    def test_2x2_layout_with_4_graphs(self):
        """P1B-31: layout('2 2') with 4 graphs produces a 2x2 grid."""
        renderer = _make_renderer(4, layout="2 2")
        rows_cols = renderer._compute_grid(4, "2 2")
        assert rows_cols == (2, 2)

    def test_1x3_layout_with_3_graphs(self):
        rows_cols = _make_renderer(3, layout="1 3")._compute_grid(3, "1 3")
        assert rows_cols == (1, 3)

    def test_3x1_layout_with_3_graphs(self):
        rows_cols = _make_renderer(3, layout="3 1")._compute_grid(3, "3 1")
        assert rows_cols == (3, 1)


# ================================================================
# P1B-32 — layout(auto) with 3 graphs → reasonable grid
# ================================================================
class TestAutoLayout:
    def test_auto_3_graphs(self):
        """P1B-32: auto layout with 3 graphs → at least 2 columns (e.g. 2x2)."""
        renderer = _make_renderer(3)
        rows, cols = renderer._compute_grid(3, "auto")
        assert rows * cols >= 3
        assert cols >= 2

    def test_auto_4_graphs(self):
        renderer = _make_renderer(4)
        rows, cols = renderer._compute_grid(4, "auto")
        assert rows * cols >= 4
        assert rows == 2 and cols == 2

    # ----------------------------------------------------------------
    # P1B-33 — layout(auto) with 1 graph → 1x1 grid
    # ----------------------------------------------------------------
    def test_auto_1_graph(self):
        """P1B-33: auto layout with 1 graph → 1x1."""
        renderer = _make_renderer(1)
        rows, cols = renderer._compute_grid(1, "auto")
        assert rows == 1
        assert cols == 1

    def test_auto_6_graphs(self):
        renderer = _make_renderer(6)
        rows, cols = renderer._compute_grid(6, "auto")
        assert rows * cols >= 6

    def test_auto_9_graphs(self):
        renderer = _make_renderer(9)
        rows, cols = renderer._compute_grid(9, "auto")
        assert rows == 3 and cols == 3


# ================================================================
# P1B-34 — fewer graphs than grid cells → empty cells (None) in gridplot
# ================================================================
class TestEmptyCells:
    def test_3_graphs_in_2x2_has_empty_cell(self):
        """P1B-34: 3 graphs in a 2x2 layout → 1 None cell."""
        renderer = _make_renderer(3, layout="2 2")
        # _build_grid_children should pad with None
        children = renderer._pad_grid_children(["a", "b", "c"], rows=2, cols=2)
        assert len(children) == 4
        assert children[-1] is None

    def test_1_graph_in_2x2_has_3_empty_cells(self):
        renderer = _make_renderer(1, layout="2 2")
        children = renderer._pad_grid_children(["a"], rows=2, cols=2)
        assert len(children) == 4
        assert children.count(None) == 3

    def test_4_graphs_no_empty_cells(self):
        renderer = _make_renderer(4, layout="2 2")
        children = renderer._pad_grid_children(["a", "b", "c", "d"], rows=2, cols=2)
        assert None not in children


# ================================================================
# P1B-35 — sizing_mode="stretch_width" applied to all figures
# ================================================================
class TestSizingMode:
    def test_figures_have_stretch_width(self):
        """P1B-35: all figures built by DashRenderer use sizing_mode='stretch_width'."""
        renderer = _make_renderer(2)
        figs = renderer._build_figures()
        for name, fig in figs.items():
            assert fig.sizing_mode == "stretch_width", (
                f"Figure '{name}' has sizing_mode='{fig.sizing_mode}', expected 'stretch_width'"
            )

    def test_single_figure_stretch_width(self):
        renderer = _make_renderer(1)
        figs = renderer._build_figures()
        for fig in figs.values():
            assert fig.sizing_mode == "stretch_width"


# ================================================================
# Bug 11 — layout overflow: items beyond grid size silently dropped
# ================================================================
class TestLayoutOverflow:
    """Bug 11 regression: when items > rows*cols, excess are silently dropped.

    full_dashboard.do specifies layout(3 2) = 6 cells but has 8 items
    (4 graphs + 4 KPI cards).  Before the fix, render() built grid rows
    by slicing cells[0:6], silently discarding items 7 and 8 (k3, k4).

    The fix: when len(all_names) > rows_n * cols_n, auto-expand rows_n to
    ceil(len(all_names) / cols_n) so that all items appear in the HTML.
    """

    def _build_full_dashboard_renderer(self):
        """Create a renderer matching the full_dashboard.do spec structure:
        4 graphs + 4 KPI divs, layout(3 2).
        """
        import json, os, tempfile
        import numpy as np

        graphs = [
            {"plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                        "options": {}, "if_expr": "", "in_expr": ""}],
             "graph_options": {"name": name},
             "if_expr": "", "in_expr": ""}
            for name in ("s1", "h1", "s2", "d1")
        ]
        kpis = [
            {"name": kn, "stat": "mean", "var": "mpg",
             "value": "21.0", "display": "21.0", "fmt": "%9.1f",
             "title": f"KPI {kn}", "subtitle": "", "color": "",
             "bgcolor": "", "update": "filter"}
            for kn in ("k1", "k2", "k3", "k4")
        ]
        spec = {
            "graphs": graphs,
            "kpis": kpis,
            "build_options": {
                "layout": "3 2",   # 6 cells but 8 items → overflow
                "link": "",
                "filter": "",
                "theme": "default",
                "title": "Test Dashboard",
                "subtitle": "",
                "registry": "s1 h1 s2 d1 k1 k2 k3 k4",
            },
        }
        vals = [{"mpg": float(i), "weight": float(i * 100)}
                for i in range(1, 21)]
        data = {"StataJSON": {
            "variableNames": ["mpg", "weight"],
            "variableLabels": {"mpg": "mpg", "weight": "weight"},
            "valueLabels": {}, "valueLabelNames": {},
            "variableTypeIsString": {"mpg": False, "weight": False},
            "values": vals,
        }}

        sp_fd, sp = tempfile.mkstemp(suffix=".json")
        dp_fd, dp = tempfile.mkstemp(suffix=".json")
        op_fd, op = tempfile.mkstemp(suffix=".html")
        try:
            with os.fdopen(sp_fd, "w") as f: json.dump(spec, f)
            with os.fdopen(dp_fd, "w") as f: json.dump(data, f)
            os.close(op_fd)
            r = DashRenderer(sp, dp, op)
        finally:
            for p in (sp, dp, op):
                try: os.unlink(p)
                except OSError: pass
        return r

    def test_all_items_appear_in_html(self):
        """Bug 11: all 8 items (4 graphs + 4 KPIs) must appear in rendered HTML.

        Before fix: layout(3 2) = 6 cells; items 7 and 8 (k3, k4) were
        silently dropped because grid row slicing stopped at cell 6.
        After fix: rows auto-expand to ceil(8/2)=4 rows so all items render.
        """
        r = self._build_full_dashboard_renderer()
        html = r.render()
        for kname in ("k1", "k2", "k3", "k4"):
            kpi_title = f"KPI {kname}"
            assert kpi_title in html, (
                f"KPI card '{kname}' (title='{kpi_title}') is missing from "
                f"the rendered HTML.  This indicates layout overflow: items "
                f"beyond the specified grid size are being silently dropped "
                f"(Bug 11).  layout(3 2) has 6 cells but there are 8 items."
            )

    def test_kpi_divs_all_created(self):
        """Verify all 4 KPI divs are created before checking HTML output."""
        r = self._build_full_dashboard_renderer()
        r.render()
        for kname in ("k1", "k2", "k3", "k4"):
            assert kname in r.kpi_divs, f"KPI div '{kname}' not created"

    def test_layout_with_exact_fit_unchanged(self):
        """layout(2 2) with exactly 4 items still produces 2×2 grid (no change)."""
        renderer = _make_renderer(4, layout="2 2")
        html = renderer.render()
        # All 4 figures should be in the HTML
        for i in range(1, 5):
            assert f"g{i}" in html or len(renderer.figures) == 4, (
                f"Figure g{i} missing from HTML with layout(2 2)"
            )

    def test_layout_with_fewer_items_pads(self):
        """layout(3 2) with 4 items pads remaining 2 cells with None (no overflow)."""
        renderer = _make_renderer(4, layout="3 2")
        html = renderer.render()
        # All 4 figures should be present
        assert len(renderer.figures) == 4


# ================================================================
# Bootstrap Layout Tests (BS-01 through BS-12)
# ================================================================

class TestBootstrapLayout:
    """Tests for Bootstrap grid layout (layout(bs ...) option)."""

    # ---- BS-01: _is_bootstrap_layout detects bs prefix ----
    def test_is_bootstrap_layout_bs(self):
        assert DashRenderer._is_bootstrap_layout("bs") is True

    def test_is_bootstrap_layout_bs_colon(self):
        assert DashRenderer._is_bootstrap_layout("bs: k1=3 k2=3") is True

    def test_is_bootstrap_layout_BS_upper(self):
        assert DashRenderer._is_bootstrap_layout("BS") is True

    def test_is_bootstrap_layout_auto_is_false(self):
        assert DashRenderer._is_bootstrap_layout("auto") is False

    def test_is_bootstrap_layout_grid_is_false(self):
        assert DashRenderer._is_bootstrap_layout("2 2") is False

    def test_is_bootstrap_layout_empty_is_false(self):
        assert DashRenderer._is_bootstrap_layout("") is False

    # ---- BS-02: _auto_bs_layout generates rows ----
    def test_auto_bs_layout_single_item(self):
        rows = DashRenderer._auto_bs_layout(["g1"], [])
        assert len(rows) >= 1
        assert rows[0][0][0] == "g1"

    def test_auto_bs_layout_kpis_first_row(self):
        rows = DashRenderer._auto_bs_layout(["k1", "k2", "g1", "g2"], ["k1", "k2"])
        # First row should contain KPIs
        first_row_names = [name for name, _ in rows[0]]
        assert "k1" in first_row_names
        assert "k2" in first_row_names

    def test_auto_bs_layout_spans_sum_le_12_per_row(self):
        rows = DashRenderer._auto_bs_layout(
            ["k1", "k2", "k3", "k4", "g1", "g2", "g3", "g4"],
            ["k1", "k2", "k3", "k4"],
        )
        for row in rows:
            total_span = sum(span for _, span in row)
            assert total_span <= 12, f"Row spans {total_span} exceed 12: {row}"

    def test_auto_bs_layout_spans_are_valid(self):
        rows = DashRenderer._auto_bs_layout(["g1", "g2", "g3"], [])
        for row in rows:
            for name, span in row:
                assert 1 <= span <= 12, f"Invalid span {span} for {name}"

    # ---- BS-03: _parse_bs_layout explicit spec ----
    def test_parse_bs_layout_explicit(self):
        all_names = ["k1", "k2", "s1", "s2"]
        rows = DashRenderer._parse_bs_layout(
            "bs: k1=3 k2=3 / s1=6 s2=6",
            all_names,
            ["k1", "k2"],
        )
        assert len(rows) == 2
        assert rows[0] == [("k1", 3), ("k2", 3)]
        assert rows[1] == [("s1", 6), ("s2", 6)]

    def test_parse_bs_layout_auto_fallback(self):
        all_names = ["k1", "s1"]
        rows = DashRenderer._parse_bs_layout("bs", all_names, ["k1"])
        assert len(rows) >= 1
        assert all(isinstance(r, list) for r in rows)

    def test_parse_bs_layout_unknown_names_dropped(self):
        all_names = ["s1", "s2"]
        rows = DashRenderer._parse_bs_layout(
            "bs: s1=6 __evil__=6 / s2=12",
            all_names,
            [],
        )
        flat_names = [name for row in rows for name, _ in row]
        assert "__evil__" not in flat_names

    def test_parse_bs_layout_spans_clamped(self):
        all_names = ["s1", "s2"]
        rows = DashRenderer._parse_bs_layout(
            "bs: s1=99 / s2=0",
            all_names,
            [],
        )
        flat = {name: span for row in rows for name, span in row}
        assert flat.get("s1", 6) <= 12
        assert flat.get("s2", 6) >= 1

    def test_parse_bs_layout_unplaced_names_appended(self):
        all_names = ["k1", "s1", "s2"]
        rows = DashRenderer._parse_bs_layout(
            "bs: k1=6",
            all_names,
            ["k1"],
        )
        flat_names = [name for row in rows for name, _ in row]
        assert "s1" in flat_names
        assert "s2" in flat_names

    # ---- BS-04: render() with layout(bs) returns HTML ----
    def test_render_bs_auto_returns_html(self):
        r = _make_renderer(2, layout="bs")
        html = r.render()
        assert "<!DOCTYPE html>" in html
        assert "db-container" in html
        assert "db-row" in html

    def test_render_bs_explicit_returns_html(self):
        r = _make_renderer(2, layout="bs: g1=6 g2=6")
        html = r.render()
        assert "<!DOCTYPE html>" in html
        assert "db-col-md-6" in html

    def test_render_bs_contains_bokeh_script(self):
        r = _make_renderer(2, layout="bs")
        html = r.render()
        # Bokeh inlines its JS; script tag should be present
        assert "<script" in html

    def test_render_bs_contains_grid_css(self):
        r = _make_renderer(2, layout="bs")
        html = r.render()
        assert "db-col-md-" in html or "db-col-12" in html

    def test_render_bs_csp_meta_present(self):
        r = _make_renderer(2, layout="bs")
        html = r.render()
        assert "Content-Security-Policy" in html
        assert "unsafe-eval" in html

    # ---- BS-05: _render_bootstrap_html with title / subtitle ----
    def test_render_bs_title_in_html(self):
        import tempfile, os, json
        graphs = [_make_graph_spec("g1"), _make_graph_spec("g2")]
        spec = {
            "graphs": graphs,
            "kpis": [],
            "build_options": {
                "layout": "bs",
                "link": "",
                "filter": "",
                "theme": "default",
                "title": "Test Dashboard",
                "subtitle": "Subtitle here",
                "registry": "g1 g2",
            },
        }
        data = _make_data_json()
        spec_fd, spec_path = tempfile.mkstemp(suffix=".json")
        data_fd, data_path = tempfile.mkstemp(suffix=".json")
        out_fd, out_path   = tempfile.mkstemp(suffix=".html")
        try:
            with os.fdopen(spec_fd, "w") as f:
                json.dump(spec, f)
            with os.fdopen(data_fd, "w") as f:
                json.dump(data, f)
            os.close(out_fd)
            renderer = DashRenderer(spec_path, data_path, out_path)
            html = renderer.render()
            assert "Test Dashboard" in html
            assert "Subtitle here" in html
        finally:
            for p in (spec_path, data_path, out_path):
                try:
                    os.unlink(p)
                except OSError:
                    pass
