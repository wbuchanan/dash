#!/usr/bin/env python3
"""
regen_dashboards.py
Regenerate all four example dashboard HTML files from the current dash_render.py.

Usage:  python3 scripts/regen_dashboards.py
"""

import sys, os, json, math, tempfile
# The package root: dash_render.py is imported from it, and the example
# pages are written there, as they were before this script moved to
# scripts/ (WP-26, 24sep2026; the root's *.html are ignored by .gitignore).
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import numpy as np
import pandas as pd
from dash_render import DashRenderer

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_data_json(columns, value_labels=None, value_label_names=None,
                    variable_labels=None):
    if value_labels is None:       value_labels = {}
    if value_label_names is None:  value_label_names = {}
    if variable_labels is None:    variable_labels = {}

    col_names = list(columns.keys())
    n_rows = len(next(iter(columns.values())))
    rows = []
    for i in range(n_rows):
        row = {}
        for c in col_names:
            v = columns[c][i]
            row[c] = None if (isinstance(v, float) and (math.isnan(v) or math.isinf(v))) else v
        rows.append(row)
    vlabs = {c: variable_labels.get(c, c) for c in col_names}
    return {
        "StataJSON": {
            "variableNames":       col_names,
            "variableLabels":      vlabs,
            "valueLabels":         value_labels,
            "valueLabelNames":     value_label_names,
            "variableTypeIsString": {c: False for c in col_names},
            "values":              rows,
        }
    }


def _render(master_spec, data_json, out_path):
    spec_fd, spec_path = tempfile.mkstemp(suffix=".json")
    data_fd, data_path = tempfile.mkstemp(suffix=".json")
    try:
        with os.fdopen(spec_fd, "w") as f:
            json.dump(master_spec, f)
        with os.fdopen(data_fd, "w") as f:
            json.dump(data_json, f)
        r = DashRenderer(spec_path, data_path, out_path)
        html = r.render()
    finally:
        for p in (spec_path, data_path):
            try: os.unlink(p)
            except OSError: pass
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(html)
    return html


# ---------------------------------------------------------------------------
# Auto dataset (30 obs — verified sample matching test_example_simulation.py)
# ---------------------------------------------------------------------------

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

assert all(len(a) == _N for a in [_MPG, _WEIGHT, _PRICE, _LENGTH, _REP78, _FOREIGN])

_VAR_LABELS = {
    'mpg': 'Mileage (mpg)', 'weight': 'Weight (lbs.)', 'price': 'Price',
    'length': 'Length (in.)', 'rep78': 'Repair Record 1978',
    'foreign': 'Car type',
}
_VALUE_LABELS = {"origin": {"0": "Domestic", "1": "Foreign"},
                 "rep78lbl": {"1":"Poor","2":"Fair","3":"Average","4":"Good","5":"Excellent"}}
_VALUE_LABEL_NAMES = {"foreign": "origin", "rep78": "rep78lbl"}

_FULL_DATA_JSON = _make_data_json(
    {"mpg":     [float(v) for v in _MPG],
     "weight":  [float(v) for v in _WEIGHT],
     "price":   [float(v) for v in _PRICE],
     "length":  [float(v) for v in _LENGTH],
     "rep78":   list(_REP78),
     "foreign": [float(v) for v in _FOREIGN]},
    value_labels=_VALUE_LABELS,
    value_label_names=_VALUE_LABEL_NAMES,
    variable_labels=_VAR_LABELS,
)

# ---------------------------------------------------------------------------
# 1. scatter.html  — basic_scatter.do
# ---------------------------------------------------------------------------

def regen_scatter(out_path):
    master_spec = {
        "graphs": [{
            "plots": [{
                "type": "scatter", "yvar": "mpg", "xvar": "weight",
                "options": {"mcolor": "navy", "msymbol": "circle", "msize": "medium"},
                "if_expr": "", "in_expr": "",
            }],
            "graph_options": {
                "title": "Fuel Efficiency vs. Weight",
                "xtitle": "Weight (lbs.)", "ytitle": "Mileage (mpg)",
            },
            "if_expr": "", "in_expr": "",
        }],
        "build_options": {"layout": "1 1", "theme": "default"},
    }
    data_json = _make_data_json(
        {"mpg":    [float(v) for v in _MPG],
         "weight": [float(v) for v in _WEIGHT]},
        variable_labels=_VAR_LABELS,
    )
    _render(master_spec, data_json, out_path)
    print(f"  scatter.html  ({os.path.getsize(out_path):,} bytes)")


# ---------------------------------------------------------------------------
# 2. dashboard.html  — multi_graph_dashboard.do
# ---------------------------------------------------------------------------

def regen_dashboard(out_path):
    _mpg_arr   = np.array(_MPG, dtype=float)
    _price_arr = np.array(_PRICE, dtype=float)
    _rep78_arr = np.array([v for v in _REP78 if not math.isnan(v)], dtype=float)

    s1 = {
        "plots": [
            {"type": "scatter", "yvar": "mpg", "xvar": "weight",
             "options": {"mcolor": "navy", "msize": "small"}, "if_expr": "", "in_expr": ""},
            {"type": "lfit", "yvar": "mpg", "xvar": "weight",
             "options": {"lcolor": "maroon", "lwidth": "medthick"}, "if_expr": "", "in_expr": ""},
        ],
        "graph_options": {"name": "s1", "title": "MPG vs Weight",
                          "xtitle": "Weight (lbs.)", "ytitle": "Mileage (mpg)"},
        "if_expr": "", "in_expr": "",
    }
    s2 = {
        "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "length",
                   "options": {"mcolor": "forest_green", "msize": "small"},
                   "if_expr": "", "in_expr": ""}],
        "graph_options": {"name": "s2", "title": "MPG vs Length",
                          "xtitle": "Length (in.)", "ytitle": "Mileage (mpg)"},
        "if_expr": "", "in_expr": "",
    }
    s3 = {
        "plots": [
            {"type": "scatter", "yvar": "mpg", "xvar": "weight",
             "options": {"mcolor": "navy", "msymbol": "circle", "msize": "small"},
             "if_expr": "rep78==1", "in_expr": ""},
            {"type": "scatter", "yvar": "mpg", "xvar": "weight",
             "options": {"mcolor": "maroon", "msymbol": "square", "msize": "small"},
             "if_expr": "rep78==2", "in_expr": ""},
            {"type": "scatter", "yvar": "mpg", "xvar": "weight",
             "options": {"mcolor": "forest_green", "msymbol": "triangle", "msize": "small"},
             "if_expr": "rep78==3", "in_expr": ""},
            {"type": "scatter", "yvar": "mpg", "xvar": "weight",
             "options": {"mcolor": "orange", "msymbol": "diamond", "msize": "small"},
             "if_expr": "rep78==4", "in_expr": ""},
            {"type": "scatter", "yvar": "mpg", "xvar": "weight",
             "options": {"mcolor": "purple", "msymbol": "inverted_triangle", "msize": "small"},
             "if_expr": "rep78==5", "in_expr": ""},
        ],
        "graph_options": {"name": "s3", "title": "MPG vs Weight by Repair Record",
                          "xtitle": "Weight (lbs.)", "ytitle": "Mileage (mpg)"},
        "if_expr": "", "in_expr": "",
    }
    h1 = {
        "plots": [{"type": "histogram", "var": "mpg", "options": {},
                   "if_expr": "", "in_expr": ""}],
        "graph_options": {"name": "h1", "title": "MPG Distribution",
                          "xtitle": "Mileage (mpg)"},
        "if_expr": "", "in_expr": "",
    }
    kpis = [
        {"name": "k1", "stat": "mean",  "var": "mpg",   "value": f"{_mpg_arr.mean():.1f}",
         "display": f"{_mpg_arr.mean():.1f}", "fmt": "%9.1f",
         "title": "Average MPG", "subtitle": "All vehicles", "color": "", "bgcolor": "",
         "update": "filter"},
        {"name": "k2", "stat": "count", "var": "mpg",   "value": str(_N),
         "display": str(_N), "fmt": "%9.0fc",
         "title": "Sample Size", "subtitle": "", "color": "", "bgcolor": "",
         "update": "filter"},
    ]
    master_spec = {
        "graphs": [s1, s2, s3, h1],
        "kpis": kpis,
        "build_options": {
            "layout": "3 2",
            "link": "s1 s2 s3",
            "filter": "foreign, type(dropdown)",
            "theme": "clean",
            "title": "Auto Dataset Dashboard",
            "subtitle": "1978 Automobile Data",
            "registry": "s1 s2 s3 h1 k1 k2",
        },
    }
    _render(master_spec, _FULL_DATA_JSON, out_path)
    print(f"  dashboard.html  ({os.path.getsize(out_path):,} bytes)")


# ---------------------------------------------------------------------------
# 3. full_dashboard.html  — full_dashboard.do
# ---------------------------------------------------------------------------

def regen_full_dashboard(out_path):
    _mpg_arr   = np.array(_MPG, dtype=float)
    _price_arr = np.array(_PRICE, dtype=float)
    _rep78_arr = np.array([v for v in _REP78 if not math.isnan(v)], dtype=float)

    s1 = {
        "plots": [
            {"type": "scatter", "yvar": "mpg", "xvar": "weight",
             "options": {"mcolor": "navy", "msize": "small", "msymbol": "circle"},
             "if_expr": "", "in_expr": ""},
            {"type": "lfit", "yvar": "mpg", "xvar": "weight",
             "options": {"lcolor": "maroon", "lwidth": "medthick"},
             "if_expr": "", "in_expr": ""},
        ],
        "graph_options": {"name": "s1", "title": "Fuel Efficiency vs. Weight",
                          "xtitle": "Weight (lbs.)", "ytitle": "Mileage (mpg)"},
        "if_expr": "", "in_expr": "",
    }
    h1 = {
        "plots": [{"type": "histogram", "var": "price", "options": {},
                   "if_expr": "", "in_expr": ""}],
        "graph_options": {"name": "h1", "title": "Price Distribution",
                          "xtitle": "Price ($)", "ytitle": "Count"},
        "if_expr": "", "in_expr": "",
    }
    s2 = {
        "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "length",
                   "options": {"mcolor": "forest_green", "msize": "small"},
                   "if_expr": "", "in_expr": ""}],
        "graph_options": {"name": "s2", "title": "MPG vs Car Length",
                          "xtitle": "Length (in.)", "ytitle": "Mileage (mpg)"},
        "if_expr": "", "in_expr": "",
    }
    d1 = {
        "plots": [{"type": "kdensity", "var": "mpg", "options": {},
                   "if_expr": "", "in_expr": ""}],
        "graph_options": {"name": "d1", "title": "MPG Kernel Density",
                          "xtitle": "Mileage (mpg)", "ytitle": "Density"},
        "if_expr": "", "in_expr": "",
    }

    kpis = [
        {"name": "k1", "stat": "mean",   "var": "mpg",
         "value": f"{_mpg_arr.mean():.1f}", "display": f"{_mpg_arr.mean():.1f}",
         "fmt": "%9.1f",  "title": "Avg MPG",      "subtitle": "Miles per gallon",
         "color": "#2c3e50", "bgcolor": "#ecf0f1",  "update": "filter"},
        {"name": "k2", "stat": "median", "var": "price",
         "value": str(int(np.median(_price_arr))),
         "display": f"{np.median(_price_arr):,.0f}",
         "fmt": "%12.0fc", "title": "Median Price", "subtitle": "1978 USD",
         "color": "", "bgcolor": "", "update": "filter"},
        {"name": "k3", "stat": "count",  "var": "mpg",
         "value": str(_N), "display": str(_N),
         "fmt": "%9.0fc",  "title": "Sample Size",  "subtitle": "Observations",
         "color": "", "bgcolor": "", "update": "both"},
        {"name": "k4", "stat": "dcount", "var": "rep78",
         "value": str(int(len(set(_rep78_arr.tolist())))),
         "display": str(int(len(set(_rep78_arr.tolist())))),
         "fmt": "%9.0f",   "title": "Repair Ratings", "subtitle": "Distinct values",
         "color": "", "bgcolor": "", "update": "filter"},
    ]
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
    _render(master_spec, _FULL_DATA_JSON, out_path)
    print(f"  full_dashboard.html  ({os.path.getsize(out_path):,} bytes)")


# ---------------------------------------------------------------------------
# 4. kelly22ex_dashboard.html  — kelly22ex_categorical.do
# ---------------------------------------------------------------------------

def regen_kelly22ex(out_path):
    _mpg_arr   = np.array(_MPG, dtype=float)
    _price_arr = np.array(_PRICE, dtype=float)
    _rep78_arr = np.array([v for v in _REP78 if not math.isnan(v)], dtype=float)

    # Kelly22ex palette colors
    kelly_colors = ["#F3C300","#875692","#F38400","#A1CAF1","#BE0032"]
    markers      = ["circle","square","triangle","diamond","inverted_triangle"]

    # s1: categorical scatter by rep78 (5 layers) + lfit
    s1_plots = []
    for i, (col, mk) in enumerate(zip(kelly_colors, markers), start=1):
        s1_plots.append({
            "type": "scatter", "yvar": "mpg", "xvar": "weight",
            "options": {"mcolor": col, "msymbol": mk, "msize": "small"},
            "if_expr": f"rep78=={i}", "in_expr": "",
        })
    s1_plots.append({
        "type": "lfit", "yvar": "mpg", "xvar": "weight",
        "options": {"lcolor": "black", "lwidth": "medthick"},
        "if_expr": "", "in_expr": "",
    })
    s1 = {
        "plots": s1_plots,
        "graph_options": {"name": "s1", "title": "MPG vs Weight by Repair Record",
                          "xtitle": "Weight (lbs.)", "ytitle": "Mileage (mpg)"},
        "if_expr": "", "in_expr": "",
    }

    s2 = {
        "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "length",
                   "options": {"mcolor": "forest_green", "msize": "small"},
                   "if_expr": "", "in_expr": ""}],
        "graph_options": {"name": "s2", "title": "MPG vs Length",
                          "xtitle": "Length (in.)", "ytitle": "Mileage (mpg)"},
        "if_expr": "", "in_expr": "",
    }
    s3 = {
        "plots": [{"type": "scatter", "yvar": "price", "xvar": "weight",
                   "options": {"mcolor": "navy", "msize": "small"},
                   "if_expr": "", "in_expr": ""}],
        "graph_options": {"name": "s3", "title": "Price vs Weight",
                          "xtitle": "Weight (lbs.)", "ytitle": "Price ($)"},
        "if_expr": "", "in_expr": "",
    }
    h1 = {
        "plots": [{"type": "histogram", "var": "mpg", "options": {},
                   "if_expr": "", "in_expr": ""}],
        "graph_options": {"name": "h1", "title": "MPG Distribution",
                          "xtitle": "Mileage (mpg)"},
        "if_expr": "", "in_expr": "",
    }

    kpis = [
        {"name": "k1", "stat": "mean",   "var": "mpg",
         "value": f"{_mpg_arr.mean():.1f}", "display": f"{_mpg_arr.mean():.1f}",
         "fmt": "%9.1f",  "title": "Avg MPG",    "subtitle": "All vehicles",
         "color": "", "bgcolor": "", "update": "filter"},
        {"name": "k2", "stat": "median", "var": "price",
         "value": str(int(np.median(_price_arr))), "display": f"{np.median(_price_arr):,.0f}",
         "fmt": "%12.0fc", "title": "Median Price", "subtitle": "1978 USD",
         "color": "", "bgcolor": "", "update": "filter"},
        {"name": "k3", "stat": "count",  "var": "mpg",
         "value": str(_N), "display": str(_N),
         "fmt": "%9.0fc",  "title": "Sample Size", "subtitle": "Observations",
         "color": "", "bgcolor": "", "update": "filter"},
    ]
    master_spec = {
        "graphs": [s1, s2, s3, h1],
        "kpis": kpis,
        "build_options": {
            "layout": "3 2",
            "link": "s1 s2 s3",
            "filter": "foreign, type(dropdown)",
            "theme": "clean",
            "title": "Kelly22ex Categorical Colors Dashboard",
            "subtitle": "1978 Auto Data — Repair Record by Kelly Colors",
            "registry": "s1 s2 s3 h1 k1 k2 k3",
        },
    }
    _render(master_spec, _FULL_DATA_JSON, out_path)
    print(f"  kelly22ex_dashboard.html  ({os.path.getsize(out_path):,} bytes)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    base = _ROOT
    print("Regenerating dashboards...")
    regen_scatter(         os.path.join(base, "scatter.html"))
    regen_dashboard(       os.path.join(base, "dashboard.html"))
    regen_full_dashboard(  os.path.join(base, "full_dashboard.html"))
    regen_kelly22ex(       os.path.join(base, "kelly22ex_dashboard.html"))
    print("Done.")
