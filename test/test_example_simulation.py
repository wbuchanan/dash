"""
test_example_simulation.py
End-to-end simulation tests for the two example scripts.

These tests faithfully reproduce the exact JSON that Stata's ``dash.ado`` would
emit for:

  - ``examples/basic_scatter.do``   — single scatter, no KPIs/filters/linking
  - ``examples/full_dashboard.do``  — 4 graphs, 4 KPI cards, 2 filters, linked
                                      brushing, theme(clean)

The simulation approach:
  1. Build ``master_spec`` and ``data_json`` dicts matching Stata's output.
  2. Write them to temp files and construct a ``DashRenderer``.
  3. Call ``renderer.render()`` and assert the HTML is returned without error.
  4. Assert structural properties (figure count, KPI div count, filter widgets,
     linked source sharing, scheme background colour, KPI title text).

Each example is run twice in sequence to satisfy the loop condition
("two consecutive runs without error").

Run with:  pytest test/test_example_simulation.py -v
"""

import sys
import os
import json
import math
import tempfile

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dash_render import DashRenderer

# ---------------------------------------------------------------------------
# Helpers shared across both simulations
# ---------------------------------------------------------------------------

def _make_data_json(columns: dict, value_labels: dict | None = None,
                    value_label_names: dict | None = None) -> dict:
    """Build a jsonio-format data JSON dict.

    Args:
        columns:          mapping of varname → list of values.
        value_labels:     ``{label_set_name: {code_str: label_str}}``
        value_label_names: ``{varname: label_set_name}``
    """
    if value_labels is None:
        value_labels = {}
    if value_label_names is None:
        value_label_names = {}

    col_names = list(columns.keys())
    n_rows = len(next(iter(columns.values())))
    rows = []
    for i in range(n_rows):
        row = {}
        for c in col_names:
            v = columns[c][i]
            row[c] = None if (isinstance(v, float) and np.isnan(v)) else v
        rows.append(row)
    return {
        "StataJSON": {
            "variableNames": col_names,
            "variableLabels": {c: c for c in col_names},
            "valueLabels": value_labels,
            "valueLabelNames": value_label_names,
            "variableTypeIsString": {c: False for c in col_names},
            "values": rows,
        }
    }


def _build_renderer(master_spec: dict, data_json: dict) -> DashRenderer:
    """Construct a DashRenderer from spec and data dicts via temp files."""
    spec_fd, spec_path = tempfile.mkstemp(suffix=".json")
    data_fd, data_path = tempfile.mkstemp(suffix=".json")
    out_fd, out_path   = tempfile.mkstemp(suffix=".html")

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


# ---------------------------------------------------------------------------
# Realistic auto.dta sample data (74 obs subset)
# Columns: mpg, weight, price, length, rep78, foreign
# foreign: 0=Domestic, 1=Foreign  (value-label "origin")
# ---------------------------------------------------------------------------

# Use 30 observations to keep tests fast while being realistic
_N = 30
_MPG     = [22, 17, 22, 20, 15, 18, 26, 20, 16, 19,
             24, 21, 23, 30, 15, 19, 22, 16, 29, 14,
             35, 18, 26, 20, 16, 20, 22, 18, 24, 12]
_WEIGHT  = [2930, 3350, 2640, 3250, 4080, 3670, 2110, 3180, 3600, 3420,
             2750, 3280, 3020, 2430, 3900, 3370, 2650, 3900, 1830, 3420,
             1760, 3460, 2070, 3070, 4060, 3040, 2760, 3720, 2580, 4840]
_PRICE   = [4099, 4749, 3799, 4816, 7827, 5788, 4453, 5379, 8814, 6342,
             5172, 4890, 6165, 5169, 8895, 5799, 3995, 6486, 4723, 5397,
             4187, 5528, 3748, 4082, 5895, 4296, 3980, 6303, 5172, 6165]
_LENGTH  = [186, 173, 168, 196, 222, 218, 170, 200, 207, 200,
             186, 188, 189, 175, 208, 196, 176, 222, 157, 206,
             142, 198, 154, 183, 203, 179, 172, 218, 173, 233]
_REP78   = [3.0, 3.0, float("nan"), 3.0, 4.0, 3.0, 3.0, 3.0, 3.0, 3.0,
             3.0, 3.0, float("nan"), 3.0, 2.0, 3.0, 3.0, 2.0, 4.0, 2.0,
             5.0, 3.0, 4.0, 3.0, 3.0, 3.0, 3.0, 4.0, 3.0, 2.0]
_FOREIGN = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

assert len(_MPG) == _N
assert len(_WEIGHT) == _N
assert len(_PRICE) == _N
assert len(_LENGTH) == _N
assert len(_REP78) == _N
assert len(_FOREIGN) == _N


# ============================================================================
# Simulation 1 — basic_scatter.do
# ============================================================================
#
# Stata commands:
#   sysuse auto, clear
#   dash scatter mpg weight, ///
#       mc(navy) ms(circle) msi(medium)     ///
#       title("Fuel Efficiency vs. Weight") ///
#       xtitle("Weight (lbs.)")             ///
#       ytitle("Mileage (mpg)")             ///
#       saving("scatter.html")
#
# Because no name() is given, dash.ado routes through _dash_render_immediate
# which creates a graph JSON WITHOUT a "name" key in graph_options.
# The master_spec emitted to Python is:
#   {"graphs": [<json_spec>], "build_options": {"layout": "1 1", "theme": "default"}}
# where json_spec.graph_options = {
#   "title": "Fuel Efficiency vs. Weight",
#   "xtitle": "Weight (lbs.)",
#   "ytitle": "Mileage (mpg)",
#   "saving": "scatter.html"
# }
# Note: no "name" key, no "kpis" array, and build_options only has layout+theme.
# ============================================================================

def _basic_scatter_spec() -> tuple[dict, dict]:
    """Return (master_spec, data_json) for basic_scatter.do simulation.

    Faithfully reproduces what _dash_render_immediate emits:
    - No "name" in graph_options (immediate mode has no name())
    - "saving" IS in graph_options (but Python uses --output arg, not this)
    - build_options has only "layout" and "theme" (no kpis, link, filter, etc.)
    - No "kpis" key at the top level
    """
    graph = {
        "plots": [{
            "type": "scatter",
            "yvar": "mpg",
            "xvar": "weight",
            "options": {
                "mcolor": "navy",
                "msymbol": "circle",
                "msize": "medium",
            },
            "if_expr": "",
            "in_expr": "",
        }],
        "graph_options": {
            # No "name" key — this is exactly what _dash_render_immediate produces
            "title": "Fuel Efficiency vs. Weight",
            "xtitle": "Weight (lbs.)",
            "ytitle": "Mileage (mpg)",
            "saving": "scatter.html",   # included by Stata parser, ignored by Python
        },
        "if_expr": "",
        "in_expr": "",
    }

    # _dash_render_immediate builds exactly this master spec:
    # {"graphs": [<json_spec>], "build_options": {"layout": "1 1", "theme": "default"}}
    master_spec = {
        "graphs": [graph],
        # No "kpis" key — _dash_render_immediate does not include it
        "build_options": {
            "layout": "1 1",      # _dash_render_immediate always uses "1 1"
            "theme": "default",   # _dash_render_immediate always uses "default"
            # No link, filter, title, subtitle, registry
        },
    }

    data_json = _make_data_json({
        "mpg":    [float(v) for v in _MPG],
        "weight": [float(v) for v in _WEIGHT],
    })

    return master_spec, data_json


class TestBasicScatterSimulation:
    """Full pipeline simulation of basic_scatter.do — run twice consecutively."""

    def _run_once(self, tmp_path):
        """Execute a complete render cycle; return the HTML string."""
        master_spec, data_json = _basic_scatter_spec()
        renderer = _build_renderer(master_spec, data_json)
        html = renderer.render()
        return html, renderer

    def test_basic_scatter_run_1(self, tmp_path):
        """First consecutive run of basic_scatter simulation — must not error.

        basic_scatter.do uses saving() without name(), so _dash_render_immediate
        is called. The graph JSON has no "name" key — graph is keyed by "" in
        renderer.figures (empty-string name is valid).
        """
        html, renderer = self._run_once(tmp_path)

        # HTML must be a non-empty string
        assert isinstance(html, str), "render() must return a string"
        assert len(html) > 500, f"HTML too short ({len(html)} chars) — render probably failed"

        # Exactly one figure must be built (keyed by "" since there's no name())
        assert len(renderer.figures) == 1, (
            f"Expected 1 figure for basic_scatter, got {len(renderer.figures)}"
        )
        # The figure key is "" (empty string) when no name() is given
        fig_key = list(renderer.figures.keys())[0]
        assert fig_key == "", (
            f"Expected empty-string figure key for immediate-mode graph, got {fig_key!r}"
        )

        # Figure must have at least one renderer (scatter glyph)
        fig = renderer.figures[""]
        assert len(fig.renderers) >= 1, (
            "scatter figure has no renderers — glyph was not added"
        )

        # No KPI cards, no filter widgets
        assert len(renderer.kpi_divs) == 0, (
            f"Expected 0 KPI divs for basic_scatter, got {len(renderer.kpi_divs)}"
        )
        assert len(renderer.filter_widgets) == 0, (
            f"Expected 0 filter widgets for basic_scatter, got {len(renderer.filter_widgets)}"
        )

        # HTML must contain key Bokeh elements
        assert "Bokeh" in html or "bokeh" in html, (
            "HTML does not appear to be a Bokeh document"
        )
        # Title must appear in HTML
        assert "Fuel Efficiency vs. Weight" in html, (
            "Graph title not found in HTML output"
        )

    def test_basic_scatter_run_2(self, tmp_path):
        """Second consecutive run of basic_scatter simulation — must not error.

        Verifies identical results on a fresh render cycle (no state leakage).
        """
        html, renderer = self._run_once(tmp_path)

        assert isinstance(html, str)
        assert len(html) > 500
        assert len(renderer.figures) == 1
        # Empty-string key for unnamed immediate-mode graph
        assert "" in renderer.figures
        fig = renderer.figures[""]
        assert len(fig.renderers) >= 1
        assert len(renderer.kpi_divs) == 0
        assert len(renderer.filter_widgets) == 0
        assert "Fuel Efficiency vs. Weight" in html


# ============================================================================
# Simulation 2 — full_dashboard.do
# ============================================================================
#
# Stata commands (abridged):
#   sysuse auto, clear
#   dash clear
#
#   dash (scatter mpg weight, mc(navy) msi(small) ms(circle))      ///
#        (lfit    mpg weight, lc(maroon) lw(medthick)),             ///
#        name(s1) title("Fuel Efficiency vs. Weight") ...
#
#   dash histogram price, name(h1) title("Price Distribution") ...
#   dash scatter mpg length, mc(forest_green) msi(small), name(s2) ...
#   dash kdensity mpg, name(d1) title("MPG Kernel Density") ...
#
#   dash kpi mean(mpg),   name(k1) title("Avg MPG") ...      update(filter)
#   dash kpi median(price), name(k2) title("Median Price") ... update(filter)
#   dash kpi count(mpg),  name(k3) title("Sample Size") ...  update(both)
#   dash kpi dcount(rep78), name(k4) title("Repair Ratings") ... update(filter)
#
#   dash build,                                                         ///
#        saving("full_dashboard.html")                                  ///
#        title("Automobile Data — Interactive Dashboard")               ///
#        subtitle("Explore fuel efficiency, pricing, and more")         ///
#        layout(3 2)                                                     ///
#        link(s1 s2)                                                     ///
#        filter(foreign, type(dropdown))                                 ///
#        filter(weight, type(range) exclude(h1 d1 k1 k2))               ///
#        theme(clean)                                                    ///
#        replace
# ============================================================================

def _full_dashboard_spec() -> tuple[dict, dict]:
    """Return (master_spec, data_json) for full_dashboard.do simulation."""

    # ---- Graphs ----
    s1 = {
        "plots": [
            {
                "type": "scatter",
                "yvar": "mpg",
                "xvar": "weight",
                "options": {
                    "mcolor": "navy",
                    "msize": "small",
                    "msymbol": "circle",
                },
                "if_expr": "",
                "in_expr": "",
            },
            {
                "type": "lfit",
                "yvar": "mpg",
                "xvar": "weight",
                "options": {
                    "lcolor": "maroon",
                    "lwidth": "medthick",
                },
                "if_expr": "",
                "in_expr": "",
            },
        ],
        "graph_options": {
            "name": "s1",
            "title": "Fuel Efficiency vs. Weight",
            "xtitle": "Weight (lbs.)",
            "ytitle": "Mileage (mpg)",
        },
        "if_expr": "",
        "in_expr": "",
    }

    h1 = {
        "plots": [{
            "type": "histogram",
            "var": "price",
            "options": {},
            "if_expr": "",
            "in_expr": "",
        }],
        "graph_options": {
            "name": "h1",
            "title": "Price Distribution",
            "xtitle": "Price ($)",
            "ytitle": "Count",
        },
        "if_expr": "",
        "in_expr": "",
    }

    s2 = {
        "plots": [{
            "type": "scatter",
            "yvar": "mpg",
            "xvar": "length",
            "options": {
                "mcolor": "forest_green",
                "msize": "small",
            },
            "if_expr": "",
            "in_expr": "",
        }],
        "graph_options": {
            "name": "s2",
            "title": "MPG vs Car Length",
            "xtitle": "Length (in.)",
            "ytitle": "Mileage (mpg)",
        },
        "if_expr": "",
        "in_expr": "",
    }

    d1 = {
        "plots": [{
            "type": "kdensity",
            "var": "mpg",
            "options": {},
            "if_expr": "",
            "in_expr": "",
        }],
        "graph_options": {
            "name": "d1",
            "title": "MPG Kernel Density",
            "xtitle": "Mileage (mpg)",
            "ytitle": "Density",
        },
        "if_expr": "",
        "in_expr": "",
    }

    # ---- KPIs ----
    # Values computed from the sample data
    _mpg_arr   = np.array(_MPG, dtype=float)
    _price_arr = np.array(_PRICE, dtype=float)
    _rep78_arr = np.array([v for v in _REP78 if not np.isnan(v)], dtype=float)

    kpis = [
        {
            "name": "k1",
            "stat": "mean",
            "var": "mpg",
            "value": str(round(float(_mpg_arr.mean()), 1)),
            "display": f"{_mpg_arr.mean():.1f}",
            "fmt": "%9.1f",
            "title": "Avg MPG",
            "subtitle": "Miles per gallon",
            "color": "#2c3e50",
            "bgcolor": "#ecf0f1",
            "update": "filter",
        },
        {
            "name": "k2",
            "stat": "median",
            "var": "price",
            "value": str(round(float(np.median(_price_arr)), 0)),
            "display": f"{np.median(_price_arr):,.0f}",
            "fmt": "%12.0fc",
            "title": "Median Price",
            "subtitle": "1978 USD",
            "color": "",
            "bgcolor": "",
            "update": "filter",
        },
        {
            "name": "k3",
            "stat": "count",
            "var": "mpg",
            "value": str(_N),
            "display": str(_N),
            "fmt": "%9.0fc",
            "title": "Sample Size",
            "subtitle": "Observations",
            "color": "",
            "bgcolor": "",
            "update": "both",
        },
        {
            "name": "k4",
            "stat": "dcount",
            "var": "rep78",
            "value": str(len(set(_rep78_arr.tolist()))),
            "display": str(len(set(_rep78_arr.tolist()))),
            "fmt": "%9.0f",
            "title": "Repair Ratings",
            "subtitle": "Distinct values",
            "color": "",
            "bgcolor": "",
            "update": "filter",
        },
    ]

    # ---- Master spec ----
    # filter: two filter() calls joined with " || " by _dash_extract_filters
    master_spec = {
        "graphs": [s1, h1, s2, d1],
        "kpis": kpis,
        "build_options": {
            "layout": "3 2",
            "link": "s1 s2",
            "filter": "foreign, type(dropdown) || weight, type(range) exclude(h1 d1 k1 k2)",
            "theme": "clean",
            "title": "Automobile Data \u2014 Interactive Dashboard",
            "subtitle": "Explore fuel efficiency, pricing, and more",
            "registry": "s1 h1 s2 d1 k1 k2 k3 k4",
        },
    }

    # ---- Data JSON ----
    value_labels = {
        "origin": {"0": "Domestic", "1": "Foreign"},
    }
    value_label_names = {
        "foreign": "origin",
    }
    data_json = _make_data_json(
        {
            "mpg":     [float(v) for v in _MPG],
            "weight":  [float(v) for v in _WEIGHT],
            "price":   [float(v) for v in _PRICE],
            "length":  [float(v) for v in _LENGTH],
            "rep78":   list(_REP78),   # includes NaN values
            "foreign": [float(v) for v in _FOREIGN],
        },
        value_labels=value_labels,
        value_label_names=value_label_names,
    )

    return master_spec, data_json


class TestFullDashboardSimulation:
    """Full pipeline simulation of full_dashboard.do — run twice consecutively."""

    S1COLOR_BG = "#ffffff"   # s1color (mapped from theme 'clean') has white bg
    S2COLOR_BG = "#d9e8f0"   # s2color (default) has bluish-grey bg

    def _run_once(self, tmp_path):
        """Execute a complete render cycle; return (html, renderer)."""
        master_spec, data_json = _full_dashboard_spec()
        renderer = _build_renderer(master_spec, data_json)
        html = renderer.render()
        return html, renderer

    # ------------------------------------------------------------------
    # Run 1
    # ------------------------------------------------------------------

    def test_full_dashboard_run_1_no_error(self, tmp_path):
        """First consecutive run of full_dashboard simulation — must not error."""
        html, renderer = self._run_once(tmp_path)
        assert isinstance(html, str), "render() must return a string"
        assert len(html) > 1000, f"HTML too short ({len(html)} chars)"

    def test_full_dashboard_run_1_figures(self, tmp_path):
        """Run 1: all four graph figures are created."""
        _, renderer = self._run_once(tmp_path)
        for fname in ("s1", "h1", "s2", "d1"):
            assert fname in renderer.figures, (
                f"Figure '{fname}' not found in renderer.figures"
            )
        assert len(renderer.figures) == 4, (
            f"Expected 4 figures, got {len(renderer.figures)}: {list(renderer.figures)}"
        )

    def test_full_dashboard_run_1_s1_two_renderers(self, tmp_path):
        """Run 1: graph s1 has ≥2 renderers (scatter + lfit)."""
        _, renderer = self._run_once(tmp_path)
        s1_fig = renderer.figures["s1"]
        assert len(s1_fig.renderers) >= 2, (
            f"s1 must have >=2 renderers (scatter + lfit), got {len(s1_fig.renderers)}"
        )

    def test_full_dashboard_run_1_kpi_cards(self, tmp_path):
        """Run 1: four KPI divs created (k1, k2, k3, k4)."""
        _, renderer = self._run_once(tmp_path)
        for kname in ("k1", "k2", "k3", "k4"):
            assert kname in renderer.kpi_divs, (
                f"KPI div '{kname}' not found in renderer.kpi_divs"
            )
        assert len(renderer.kpi_divs) == 4, (
            f"Expected 4 KPI divs, got {len(renderer.kpi_divs)}"
        )

    def test_full_dashboard_run_1_kpi_multiword_title(self, tmp_path):
        """Run 1: k1 div contains full multi-word title 'Avg MPG'."""
        _, renderer = self._run_once(tmp_path)
        k1_html = renderer.kpi_divs["k1"].text
        assert "Avg MPG" in k1_html, (
            f"Multi-word title 'Avg MPG' not found in k1 div HTML:\n{k1_html[:300]}"
        )
        assert "Miles per gallon" in k1_html, (
            f"Subtitle 'Miles per gallon' not found in k1 div HTML:\n{k1_html[:300]}"
        )

    def test_full_dashboard_run_1_kpi_bgcolor(self, tmp_path):
        """Run 1: k1 div contains the custom bgcolor #ecf0f1."""
        _, renderer = self._run_once(tmp_path)
        k1_html = renderer.kpi_divs["k1"].text
        assert "#ecf0f1" in k1_html, (
            f"bgcolor '#ecf0f1' not found in k1 div HTML:\n{k1_html[:300]}"
        )

    def test_full_dashboard_run_1_filter_widgets(self, tmp_path):
        """Run 1: two filter widgets created (foreign dropdown + weight range)."""
        _, renderer = self._run_once(tmp_path)
        assert len(renderer.filter_widgets) >= 2, (
            f"Expected >=2 filter widgets, got {len(renderer.filter_widgets)}: "
            f"{[type(w).__name__ for w in renderer.filter_widgets]}"
        )

    def test_full_dashboard_run_1_linked_source_shared(self, tmp_path):
        """Run 1: s1 and s2 share the same ColumnDataSource (linked brushing)."""
        _, renderer = self._run_once(tmp_path)
        s1_src = renderer.sources.get("s1")
        s2_src = renderer.sources.get("s2")
        assert s1_src is not None, "Source for 's1' not found"
        assert s2_src is not None, "Source for 's2' not found"
        assert s1_src is s2_src, (
            "s1 and s2 must share the same ColumnDataSource for linked brushing"
        )

    def test_full_dashboard_run_1_theme_clean(self, tmp_path):
        """Run 1: theme('clean') is mapped to s1color — white background."""
        _, renderer = self._run_once(tmp_path)
        assert hasattr(renderer, "scheme"), "DashRenderer must have .scheme attribute"
        bg = renderer.scheme.background_color.lower()
        assert bg == self.S1COLOR_BG, (
            f"theme('clean') must resolve to s1color (bg={self.S1COLOR_BG}), "
            f"got bg={bg!r}"
        )

    def test_full_dashboard_run_1_layout_title_in_html(self, tmp_path):
        """Run 1: dashboard title appears in HTML."""
        html, _ = self._run_once(tmp_path)
        assert "Automobile Data" in html, (
            "Dashboard title 'Automobile Data...' not found in HTML"
        )

    # ------------------------------------------------------------------
    # Run 2 (identical assertions — both must pass for the loop condition)
    # ------------------------------------------------------------------

    def test_full_dashboard_run_2_no_error(self, tmp_path):
        """Second consecutive run — must not error."""
        html, renderer = self._run_once(tmp_path)
        assert isinstance(html, str)
        assert len(html) > 1000

    def test_full_dashboard_run_2_figures(self, tmp_path):
        """Run 2: all four graph figures are created."""
        _, renderer = self._run_once(tmp_path)
        for fname in ("s1", "h1", "s2", "d1"):
            assert fname in renderer.figures

    def test_full_dashboard_run_2_kpi_cards(self, tmp_path):
        """Run 2: four KPI divs created."""
        _, renderer = self._run_once(tmp_path)
        for kname in ("k1", "k2", "k3", "k4"):
            assert kname in renderer.kpi_divs

    def test_full_dashboard_run_2_filter_widgets(self, tmp_path):
        """Run 2: two filter widgets created."""
        _, renderer = self._run_once(tmp_path)
        assert len(renderer.filter_widgets) >= 2

    def test_full_dashboard_run_2_linked_source_shared(self, tmp_path):
        """Run 2: s1 and s2 share the same ColumnDataSource."""
        _, renderer = self._run_once(tmp_path)
        assert renderer.sources.get("s1") is renderer.sources.get("s2")

    def test_full_dashboard_run_2_theme_clean(self, tmp_path):
        """Run 2: theme('clean') maps to s1color — white background."""
        _, renderer = self._run_once(tmp_path)
        bg = renderer.scheme.background_color.lower()
        assert bg == self.S1COLOR_BG

    def test_full_dashboard_run_2_kpi_multiword_title(self, tmp_path):
        """Run 2: k1 div contains full multi-word title 'Avg MPG'."""
        _, renderer = self._run_once(tmp_path)
        k1_html = renderer.kpi_divs["k1"].text
        assert "Avg MPG" in k1_html
        assert "Miles per gallon" in k1_html
