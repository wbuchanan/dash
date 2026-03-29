#!/usr/bin/env python3
"""regen_bootstrap_examples.py
Regenerate all four Bootstrap-layout example HTML files.

Uses the same 30-observation sample data as test_example_simulation.py.
Run from the dash/ directory:
    /Users/billy/anaconda3/bin/python3 regen_bootstrap_examples.py
"""

import json
import os
import tempfile
import sys

sys.path.insert(0, os.path.dirname(__file__))
from dash_render import DashRenderer

# ---------------------------------------------------------------------------
# 30-observation sample data (matches test_example_simulation.py)
# ---------------------------------------------------------------------------

SAMPLE_DATA = {
    "StataJSON": {
        "variableNames": ["mpg", "weight", "length", "foreign", "price", "rep78"],
        "variableLabels": {
            "mpg": "Mileage (mpg)",
            "weight": "Weight (lbs.)",
            "length": "Length (in.)",
            "foreign": "Car type",
            "price": "Price",
            "rep78": "Repair record 1978",
        },
        "valueLabels": {
            "foreign": {"0": "Domestic", "1": "Foreign"},
        },
        "valueLabelNames": {"foreign": "origin"},
        "variableTypeIsString": {
            "mpg": False,
            "weight": False,
            "length": False,
            "foreign": False,
            "price": False,
            "rep78": False,
        },
        "values": [
            {"mpg": 22, "weight": 2930, "length": 186, "foreign": 0, "price": 4099, "rep78": 5},
            {"mpg": 17, "weight": 3350, "length": 173, "foreign": 0, "price": 4749, "rep78": 3},
            {"mpg": 22, "weight": 2640, "length": 168, "foreign": 0, "price": 3799, "rep78": 4},
            {"mpg": 20, "weight": 3250, "length": 196, "foreign": 0, "price": 4816, "rep78": 3},
            {"mpg": 15, "weight": 4080, "length": 222, "foreign": 0, "price": 7827, "rep78": 4},
            {"mpg": 18, "weight": 3670, "length": 218, "foreign": 0, "price": 5788, "rep78": 3},
            {"mpg": 26, "weight": 2230, "length": 170, "foreign": 0, "price": 4453, "rep78": 3},
            {"mpg": 20, "weight": 3280, "length": 200, "foreign": 0, "price": 6900, "rep78": 2},
            {"mpg": 16, "weight": 3609, "length": 219, "foreign": 0, "price": 4890, "rep78": 3},
            {"mpg": 19, "weight": 3302, "length": 197, "foreign": 0, "price": 6295, "rep78": 3},
            {"mpg": 14, "weight": 3900, "length": 204, "foreign": 0, "price": 5705, "rep78": 4},
            {"mpg": 14, "weight": 4330, "length": 221, "foreign": 0, "price": 5172, "rep78": 2},
            {"mpg": 29, "weight": 1800, "length": 147, "foreign": 0, "price": 3895, "rep78": 2},
            {"mpg": 16, "weight": 3820, "length": 212, "foreign": 0, "price": 6165, "rep78": 3},
            {"mpg": 17, "weight": 3850, "length": 218, "foreign": 0, "price": 5898, "rep78": 3},
            {"mpg": 21, "weight": 2750, "length": 193, "foreign": 1, "price": 4425, "rep78": 4},
            {"mpg": 30, "weight": 2120, "length": 172, "foreign": 1, "price": 5079, "rep78": 4},
            {"mpg": 35, "weight": 2020, "length": 165, "foreign": 1, "price": 4296, "rep78": 5},
            {"mpg": 22, "weight": 2280, "length": 170, "foreign": 1, "price": 5798, "rep78": 4},
            {"mpg": 31, "weight": 2050, "length": 164, "foreign": 1, "price": 6479, "rep78": 5},
            {"mpg": 35, "weight": 1800, "length": 157, "foreign": 1, "price": 3748, "rep78": 5},
            {"mpg": 32, "weight": 1760, "length": 154, "foreign": 1, "price": 3995, "rep78": 5},
            {"mpg": 24, "weight": 2040, "length": 165, "foreign": 1, "price": 4697, "rep78": 5},
            {"mpg": 28, "weight": 1985, "length": 163, "foreign": 1, "price": 5886, "rep78": 5},
            {"mpg": 25, "weight": 1975, "length": 166, "foreign": 1, "price": 4099, "rep78": 4},
            {"mpg": 26, "weight": 1990, "length": 163, "foreign": 1, "price": 8129, "rep78": 4},
            {"mpg": 24, "weight": 2025, "length": 165, "foreign": 1, "price": 7140, "rep78": 5},
            {"mpg": 23, "weight": 2200, "length": 172, "foreign": 1, "price": 9690, "rep78": 5},
            {"mpg": 17, "weight": 2750, "length": 180, "foreign": 1, "price": 6295, "rep78": 3},
            {"mpg": 21, "weight": 2650, "length": 176, "foreign": 1, "price": 5189, "rep78": 4},
        ],
    }
}

# ---------------------------------------------------------------------------
# Helper: render a spec to a named HTML file
# ---------------------------------------------------------------------------

def render(spec: dict, out_name: str) -> None:
    """Write master spec + sample data to temp files, render, save HTML."""
    spec_fd, spec_path = tempfile.mkstemp(suffix=".json")
    data_fd, data_path = tempfile.mkstemp(suffix=".json")
    out_fd,  out_path  = tempfile.mkstemp(suffix=".html")

    try:
        with os.fdopen(spec_fd, "w") as f:
            json.dump(spec, f)
        with os.fdopen(data_fd, "w") as f:
            json.dump(SAMPLE_DATA, f)
        os.close(out_fd)

        renderer = DashRenderer(spec_path, data_path, out_path)
        html = renderer.render()

        dest = os.path.join(os.path.dirname(__file__), out_name)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(html)

        size = os.path.getsize(dest)
        print(f"  {out_name}  ({size:,} bytes)")

    finally:
        for p in (spec_path, data_path, out_path):
            try:
                os.unlink(p)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Dashboard specs
# ---------------------------------------------------------------------------

def _graph(name, plots, gopts=None):
    return {
        "plots": plots,
        "graph_options": {"name": name, **(gopts or {})},
        "if_expr": "",
        "in_expr": "",
    }


def _scatter(yvar, xvar, **opts):
    return {"type": "scatter", "yvar": yvar, "xvar": xvar, "options": opts}


def _lfit(yvar, xvar, **opts):
    return {"type": "lfit", "yvar": yvar, "xvar": xvar, "options": opts}


def _hist(yvar, **opts):
    return {"type": "histogram", "yvar": yvar, "options": opts}


def _kpi(name, stat, varname, title, fmt="%9.1f", subtitle="", update="filter"):
    return {
        "name": name,
        "stat": stat,
        "var": varname,
        "title": title,
        "fmt": fmt,
        "subtitle": subtitle,
        "update": update,
    }


def _build_opts(layout, title="", subtitle="", link="", filter_json="",
                theme="default"):
    return {
        "layout": layout,
        "link": link,
        "filter": filter_json,
        "theme": theme,
        "title": title,
        "subtitle": subtitle,
        "registry": "",
    }


# ---------------------------------------------------------------------------
# Example 1 — Equal columns (auto Bootstrap)
# ---------------------------------------------------------------------------

EQUAL_COLS_SPEC = {
    "graphs": [
        _graph("s1", [_scatter("mpg", "weight", mcolor="navy",
                               msize="6")],
               {"title": "MPG vs Weight", "xtitle": "Weight (lbs.)",
                "ytitle": "Mileage (mpg)"}),
        _graph("s2", [_scatter("mpg", "length", mcolor="forest_green",
                               msize="6")],
               {"title": "MPG vs Length", "xtitle": "Length (in.)",
                "ytitle": "Mileage (mpg)"}),
        _graph("h1", [_hist("mpg")],
               {"title": "MPG Distribution", "xtitle": "Mileage (mpg)"}),
    ],
    "kpis": [
        _kpi("k1", "mean", "mpg",    "Avg MPG",    "%9.1f",  "All vehicles"),
        _kpi("k2", "count", "mpg",   "Sample Size", "%9.0f"),
        _kpi("k3", "mean", "price",  "Avg Price",   "%9.0f",  "USD"),
        _kpi("k4", "mean", "weight", "Avg Weight",  "%9.0f",  "lbs"),
    ],
    "build_options": _build_opts(
        layout="bs",
        title="Auto Dataset — Equal Columns",
        subtitle="Auto Bootstrap layout: 4 KPI cards + 3 graphs",
    ),
}

# ---------------------------------------------------------------------------
# Example 2 — Hero layout (featured 8-col scatter + 4-col histogram)
# ---------------------------------------------------------------------------

HERO_SPEC = {
    "graphs": [
        _graph("s1",
               [_scatter("mpg", "weight", mcolor="navy", msize="6"),
                _lfit("mpg", "weight", lcolor="maroon", lwidth="2")],
               {"title": "MPG vs Weight (OLS fit)", "xtitle": "Weight (lbs.)",
                "ytitle": "Mileage (mpg)"}),
        _graph("h1", [_hist("mpg")],
               {"title": "MPG Distribution", "xtitle": "Mileage (mpg)"}),
        _graph("s2", [_scatter("mpg", "length", mcolor="forest_green", msize="6")],
               {"title": "MPG vs Length"}),
        _graph("s3", [_scatter("price", "weight", mcolor="orange", msize="6")],
               {"title": "Price vs Weight"}),
    ],
    "kpis": [
        _kpi("k1", "mean",  "mpg",    "Avg MPG",    "%9.1f", "All vehicles"),
        _kpi("k2", "count", "mpg",    "Sample Size", "%9.0f"),
        _kpi("k3", "mean",  "price",  "Avg Price",   "%9.0f", "USD"),
        _kpi("k4", "mean",  "weight", "Avg Weight",  "%9.0f", "lbs"),
    ],
    "build_options": _build_opts(
        layout="bs: k1=3 k2=3 k3=3 k4=3 / s1=8 h1=4 / s2=6 s3=6",
        title="Auto Dataset — Hero Layout",
        subtitle="Featured: MPG vs Weight spans 8 of 12 columns",
    ),
}

# ---------------------------------------------------------------------------
# Example 3 — Stacked narrative (full-width panels)
# ---------------------------------------------------------------------------

STACKED_SPEC = {
    "graphs": [
        _graph("s1", [_scatter("mpg", "weight", mcolor="navy", msize="6")],
               {"title": "MPG vs Weight — All Vehicles",
                "xtitle": "Weight (lbs.)", "ytitle": "Mileage (mpg)"}),
        _graph("h1", [_hist("mpg")],
               {"title": "Distribution of Fuel Economy",
                "xtitle": "Mileage (mpg)"}),
        _graph("s2", [_scatter("mpg", "price", mcolor="maroon", msize="6")],
               {"title": "MPG vs Price",
                "xtitle": "Price (USD)", "ytitle": "Mileage (mpg)"}),
    ],
    "kpis": [
        _kpi("k1", "mean",  "mpg",    "Avg MPG",    "%9.1f"),
        _kpi("k2", "count", "mpg",    "N Cars",      "%9.0f"),
        _kpi("k3", "mean",  "price",  "Avg Price",   "%9.0f", "USD"),
        _kpi("k4", "mean",  "weight", "Avg Weight",  "%9.0f", "lbs"),
    ],
    "build_options": _build_opts(
        layout="bs: k1=3 k2=3 k3=3 k4=3 / s1=12 / h1=12 / s2=12",
        title="Auto Dataset — Stacked Layout",
        subtitle="Narrative dashboard: each chart occupies the full row width",
    ),
}

# ---------------------------------------------------------------------------
# Example 4 — Responsive asymmetric with filter + linked brushing
# ---------------------------------------------------------------------------

FILTER_JSON = json.dumps([{
    "varname": "foreign",
    "type": "dropdown",
    "label": "Car Origin",
    "exclude": [],
}])

RESPONSIVE_SPEC = {
    "graphs": [
        _graph("s1",
               [_scatter("mpg", "weight", mcolor="navy", msize="6"),
                _lfit("mpg", "weight", lcolor="maroon", lwidth="2")],
               {"title": "MPG vs Weight",
                "xtitle": "Weight (lbs.)", "ytitle": "Mileage (mpg)"}),
        _graph("h1", [_hist("mpg")],
               {"title": "MPG Distribution", "xtitle": "Mileage (mpg)"}),
        _graph("s2", [_scatter("mpg", "length", mcolor="forest_green", msize="6")],
               {"title": "MPG vs Length",
                "xtitle": "Length (in.)", "ytitle": "Mileage (mpg)"}),
        _graph("s3", [_scatter("mpg", "price", mcolor="purple", msize="6")],
               {"title": "MPG vs Price",
                "xtitle": "Price (USD)", "ytitle": "Mileage (mpg)"}),
    ],
    "kpis": [
        _kpi("k1", "mean",  "mpg",   "Avg MPG",    "%9.1f", "All vehicles", "filter"),
        _kpi("k2", "count", "mpg",   "Sample Size", "%9.0f", "",             "filter"),
        _kpi("k3", "mean",  "price", "Avg Price",   "%9.0f", "USD",          "filter"),
    ],
    "build_options": _build_opts(
        layout="bs: k1=4 k2=4 k3=4 / s1=8 h1=4 / s2=6 s3=6",
        title="Auto Dataset — Responsive Layout",
        subtitle="Filter by origin  ·  Brush s1 to highlight s2 and s3",
        link="s1 s2 s3",
        filter_json=FILTER_JSON,
    ),
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Generating Bootstrap example dashboards...")
    render(EQUAL_COLS_SPEC,  "bs_equal_cols.html")
    render(HERO_SPEC,         "bs_kpi_hero.html")
    render(STACKED_SPEC,      "bs_stacked.html")
    render(RESPONSIVE_SPEC,   "bs_responsive.html")
    print("Done.")
