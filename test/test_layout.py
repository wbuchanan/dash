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
import re
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dash_render import DashRenderer
# The bs-layout rules, called directly: DashRenderer's static methods of
# the same job only delegated to these, only tests called them, and WP-26
# deleted them (24sep2026).
from dash_render import (_dash_auto_bs_layout, _dash_is_bs_layout,
                         _dash_parse_bs_layout)


# ================================================================
# Helpers
# ================================================================

from conftest import render_models  # noqa: E402


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
        # The grid itself, not only a floor under it (measured 24sep2026).
        assert (rows, cols) == (2, 2)

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
        assert (rows, cols) == (2, 3)

    def test_auto_9_graphs(self):
        renderer = _make_renderer(9)
        rows, cols = renderer._compute_grid(9, "auto")
        assert rows == 3 and cols == 3


# ================================================================
# P1B-34 — fewer graphs than grid cells → empty cells (None) in gridplot
# ================================================================
class TestEmptyCells:
    """A 2x2 layout given fewer than four graphs leaves the rest empty.

    These used to call `_pad_grid_children', a helper the renderer never
    called: the live path pads inline, with

        while len(cells) < rows_n * cols_n: cells.append(None)

    so the three tests certified a duplicate implementation and would have
    stayed green if the live padding had been deleted. They now read the
    GridPlot the renderer actually built, the way test_layout_placement.py
    does.
    """

    @staticmethod
    def _occupied(r):
        """How many cells of the assembled grid hold a figure."""
        from bokeh.models import GridPlot
        root = getattr(r, "_last_layout_root", None)
        assert root is not None, "the renderer kept no layout root to inspect"
        figs = {id(f) for f in r.figures.values()}
        seen, found = set(), 0

        def walk(m):
            nonlocal found
            if isinstance(m, (list, tuple)):
                for x in m:
                    if x is not None and not isinstance(x, (int, float, str)):
                        walk(x)
                return
            if m is None or id(m) in seen:
                return
            seen.add(id(m))
            if isinstance(m, GridPlot):
                for child in m.children:
                    if id(child[0]) in figs:
                        found += 1
            for attr in ("children", "tabs", "child"):
                k = getattr(m, attr, None)
                if k is not None:
                    walk(k)

        walk(root)
        return found

    @pytest.mark.parametrize("n_graphs", [1, 2, 3, 4])
    def test_a_two_by_two_grid_holds_exactly_the_graphs_given(self, n_graphs):
        r = _make_renderer(n_graphs, layout="2 2")
        render_models(r)
        assert self._occupied(r) == n_graphs, (
            f"{n_graphs} graph(s) in a 2x2 layout should occupy {n_graphs} "
            f"cells; the rest of the grid is empty"
        )

    def test_no_graph_is_dropped_when_the_grid_is_too_small(self):
        """The guard S12 added: a graph must never vanish."""
        r = _make_renderer(5, layout="2 2")
        render_models(r)
        assert self._occupied(r) == 5, (
            "a 2x2 layout given five graphs dropped one instead of growing"
        )


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
        render_models(r)
        for kname in ("k1", "k2", "k3", "k4"):
            assert kname in r.kpi_divs, f"KPI div '{kname}' not created"

    def test_layout_with_exact_fit_unchanged(self):
        """layout(2 2) with exactly 4 items still produces 2×2 grid (no change)."""
        from bokeh.models import GridPlot
        renderer = _make_renderer(4, layout="2 2")
        html = renderer.render()
        # All 4 figures should be in the HTML.  This asked for "g<i>" in
        # the page OR four figures built -- the second is true of any
        # render that built them, placed or not -- so it is asked of each
        # figure's own id, and of the grid it sits in: row by row, a 2x2.
        assert sorted(renderer.figures) == ["g1", "g2", "g3", "g4"]
        for name, fig in renderer.figures.items():
            assert fig.id in html, (
                f"Figure {name} missing from HTML with layout(2 2)"
            )
        grids = list(renderer._last_layout_root.select({"type": GridPlot}))
        assert len(grids) == 1, grids
        at = {id(f): n for n, f in renderer.figures.items()}
        cells = sorted((c[1], c[2], at.get(id(c[0]))) for c in
                       grids[0].children)
        assert cells == [(0, 0, "g1"), (0, 1, "g2"), (1, 0, "g3"),
                         (1, 1, "g4")], cells

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

    # ---- BS-01: _dash_is_bs_layout detects bs prefix ----
    def test_is_bootstrap_layout_bs(self):
        assert _dash_is_bs_layout("bs") is True

    def test_is_bootstrap_layout_bs_colon(self):
        assert _dash_is_bs_layout("bs: k1=3 k2=3") is True

    def test_is_bootstrap_layout_BS_upper(self):
        assert _dash_is_bs_layout("BS") is True

    def test_is_bootstrap_layout_auto_is_false(self):
        assert _dash_is_bs_layout("auto") is False

    def test_is_bootstrap_layout_grid_is_false(self):
        assert _dash_is_bs_layout("2 2") is False

    def test_is_bootstrap_layout_empty_is_false(self):
        assert _dash_is_bs_layout("") is False

    # ---- BS-02: _dash_auto_bs_layout generates rows ----
    def test_auto_bs_layout_single_item(self):
        rows = _dash_auto_bs_layout(["g1"], [])
        assert len(rows) >= 1
        assert rows[0][0][0] == "g1"
        # One graph fills its row.
        assert rows == [[("g1", 12)]], rows

    def test_auto_bs_layout_kpis_first_row(self):
        rows = _dash_auto_bs_layout(["k1", "k2", "g1", "g2"], ["k1", "k2"])
        # First row should contain KPIs
        first_row_names = [name for name, _ in rows[0]]
        assert "k1" in first_row_names
        assert "k2" in first_row_names

    def test_auto_bs_layout_spans_sum_le_12_per_row(self):
        names = ["k1", "k2", "k3", "k4", "g1", "g2", "g3", "g4"]
        rows = _dash_auto_bs_layout(names, ["k1", "k2", "k3", "k4"])
        # Every item placed once, so the loop below has a layout to read:
        # an empty one passed it.
        assert sorted(n for row in rows for n, _ in row) == sorted(names)
        for row in rows:
            total_span = sum(span for _, span in row)
            assert total_span <= 12, f"Row spans {total_span} exceed 12: {row}"

    def test_auto_bs_layout_spans_are_valid(self):
        rows = _dash_auto_bs_layout(["g1", "g2", "g3"], [])
        assert sorted(n for row in rows for n, _ in row) == ["g1", "g2", "g3"]
        for row in rows:
            for name, span in row:
                assert 1 <= span <= 12, f"Invalid span {span} for {name}"

    # ---- BS-03: _dash_parse_bs_layout explicit spec ----
    def test_parse_bs_layout_explicit(self):
        all_names = ["k1", "k2", "s1", "s2"]
        rows = _dash_parse_bs_layout(
            "bs: k1=3 k2=3 / s1=6 s2=6",
            all_names,
            ["k1", "k2"],
        )
        assert len(rows) == 2
        assert rows[0] == [("k1", 3), ("k2", 3)]
        assert rows[1] == [("s1", 6), ("s2", 6)]

    def test_parse_bs_layout_auto_fallback(self):
        all_names = ["k1", "s1"]
        rows = _dash_parse_bs_layout("bs", all_names, ["k1"])
        assert len(rows) >= 1
        assert all(isinstance(r, list) for r in rows)
        # Bare `bs' is the automatic layout: the card's row, then the
        # graph's, each item a full row (measured 24sep2026).
        assert rows == [[("k1", 12)], [("s1", 12)]], rows

    def test_parse_bs_layout_unknown_names_dropped(self):
        all_names = ["s1", "s2"]
        rows = _dash_parse_bs_layout(
            "bs: s1=6 __evil__=6 / s2=12",
            all_names,
            [],
        )
        flat_names = [name for row in rows for name, _ in row]
        assert "__evil__" not in flat_names
        # ...and the rest of the spec is drawn as written.
        assert rows == [[("s1", 6)], [("s2", 12)]], rows

    def test_parse_bs_layout_spans_clamped(self):
        all_names = ["s1", "s2"]
        rows = _dash_parse_bs_layout(
            "bs: s1=99 / s2=0",
            all_names,
            [],
        )
        flat = {name: span for row in rows for name, span in row}
        assert flat.get("s1", 6) <= 12
        assert flat.get("s2", 6) >= 1
        # The spans the clamp gives, both there: the defaults of 6 above
        # passed for a name the parse had dropped.
        assert flat == {"s1": 12, "s2": 1}, flat

    def test_parse_bs_layout_unplaced_names_appended(self):
        all_names = ["k1", "s1", "s2"]
        rows = _dash_parse_bs_layout(
            "bs: k1=6",
            all_names,
            ["k1"],
        )
        flat_names = [name for row in rows for name, _ in row]
        assert "s1" in flat_names
        assert "s2" in flat_names

    # ---- BS-04: render() with layout(bs) returns HTML ----
    # "db-container", "db-row" and "db-col-md-6" are all in _DASH_GRID_CSS,
    # which every bs page embeds, so a search for the bare word is answered
    # by the stylesheet whether the grid's markup is there or not.  The
    # markup is read as markup (a div's class), the stylesheet as rules.
    _CELL = re.compile(r'<div class="(db-col-12 [^"]*)"')

    def test_render_bs_auto_returns_html(self):
        r = _make_renderer(2, layout="bs")
        html = r.render()
        assert "<!DOCTYPE html>" in html
        assert "db-container" in html
        assert "db-row" in html
        assert html.count('<div class="db-container">') == 1
        assert html.count('<div class="db-row db-section">') == 1
        assert len(self._CELL.findall(html)) == 2, self._CELL.findall(html)

    def test_render_bs_explicit_returns_html(self):
        r = _make_renderer(2, layout="bs: g1=6 g2=6")
        html = r.render()
        assert "<!DOCTYPE html>" in html
        assert "db-col-md-6" in html
        cells = self._CELL.findall(html)
        assert len(cells) == 2 and all(
            "db-col-md-6" in c.split() for c in cells), cells

    def test_render_bs_contains_bokeh_script(self):
        r = _make_renderer(2, layout="bs")
        html = r.render()
        # Bokeh inlines its JS; script tag should be present
        assert "<script" in html

    def test_render_bs_contains_grid_css(self):
        r = _make_renderer(2, layout="bs")
        html = r.render()
        assert "db-col-md-" in html or "db-col-12" in html
        # The words are the cells' classes as well; a RULE is the
        # stylesheet's alone.
        assert re.search(r"\.db-col-md-6\s*\{", html)
        assert re.search(r"\.db-row\s*\{", html)

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
