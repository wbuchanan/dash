#!/usr/bin/env python3
"""regen_comprehensive.py
Regenerate comprehensive_demo.html without Stata.

Demonstrates every twoway plot type, all three filter types (dropdown,
range, slider), linked brushing, Bootstrap sidebar layout, and three
tab panels (Univariate / Bivariate / Multivariate).

Design principles
-----------------
* No hardcoded statistics — all derived columns (OLS prediction intervals)
  are computed programmatically from the raw data in this script.
* Filters always use human-readable value labels for categorical variables.
* Every graph has a proper xtitle and ytitle reflecting the displayed data.
* Univariate: per-variable histograms + KDE overlays.
* Bivariate: meaningful (x, y) pairs with scatter, fits, line, connected,
  dot, spike, dropline, area, and range plot types.
* Multivariate: every graph encodes ≥ 3 variables using multiple color/shape
  series, or scatter data overlaid on range/CI bands.
* All graphs carry a "hover" option listing tooltip variables.
* All scatter/line/dot/spike/dropline/histogram graphs are linked so the
  dropdown filter updates them consistently.

Run from the dash/ directory:
    /Users/billy/anaconda3/bin/python3 regen_comprehensive.py
"""

import json
import math
import os
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from dash_render import DashRenderer

# ---------------------------------------------------------------------------
# Raw 30-observation sample — 1978 auto dataset variables
# Sorted ascending by weight so area/line/range plots render cleanly.
# ---------------------------------------------------------------------------

_RAW = [
    # mpg  weight  price   rep78  foreign  length  displacement  headroom  turn  trunk
    (32,   1760,   3995,   5,     1,       154,    61,           2.5,      32,   6),
    (35,   1800,   3748,   5,     1,       157,    61,           2.0,      30,   8),
    (35,   1800,   3895,   2,     0,       147,    97,           3.0,      33,   11),
    (28,   1985,   5886,   5,     1,       163,    91,           3.5,      36,   8),
    (25,   1975,   4099,   4,     1,       166,    97,           2.5,      35,   8),
    (26,   1990,   8129,   4,     1,       163,    97,           2.5,      34,   8),
    (24,   2025,   7140,   5,     1,       165,    97,           3.0,      35,   8),
    (24,   2040,   4697,   5,     1,       165,    98,           3.0,      34,   8),
    (31,   2050,   6479,   5,     1,       164,    91,           3.5,      36,   8),
    (30,   2120,   5079,   4,     1,       172,    107,          2.5,      36,   8),
    (23,   2200,   9690,   5,     1,       172,    120,          2.5,      36,   8),
    (22,   2280,   5798,   4,     1,       170,    120,          3.0,      37,   8),
    (26,   2230,   4453,   3,     0,       170,    151,          3.5,      40,   10),
    (22,   2640,   3799,   4,     0,       168,    121,          3.0,      35,   13),
    (17,   2650,   5189,   4,     1,       176,    120,          3.5,      38,   8),
    (21,   2750,   4425,   4,     1,       193,    146,          2.5,      40,   12),
    (17,   2750,   6295,   3,     1,       180,    134,          4.0,      40,   10),
    (22,   2930,   4099,   5,     0,       186,    121,          2.5,      43,   11),
    (20,   3250,   4816,   3,     0,       196,    196,          4.0,      40,   16),
    (20,   3280,   6900,   2,     0,       200,    250,          3.5,      42,   16),
    (19,   3302,   6295,   3,     0,       197,    250,          3.5,      43,   18),
    (17,   3350,   4749,   3,     0,       173,    258,          2.5,      40,   11),
    (16,   3609,   4890,   3,     0,       219,    307,          3.5,      44,   17),
    (18,   3670,   5788,   3,     0,       218,    231,          4.0,      41,   15),
    (16,   3820,   6165,   3,     0,       212,    307,          3.0,      43,   13),
    (17,   3850,   5898,   3,     0,       218,    302,          4.0,      43,   19),
    (15,   4080,   7827,   4,     0,       222,    305,          4.0,      43,   21),
    (14,   4330,   5172,   2,     0,       221,    304,          3.5,      48,   16),
    (14,   3900,   5705,   4,     0,       204,    350,          4.0,      43,   21),
    (16,   3820,   6165,   3,     0,       212,    307,          3.0,      43,   13),
]

_RAW_COLS = ["mpg", "weight", "price", "rep78", "foreign", "length",
             "displacement", "headroom", "turn", "trunk"]

# ---------------------------------------------------------------------------
# Compute OLS prediction intervals for mpg ~ weight (no hardcoding)
# These give semantically meaningful range plots: for a car of a given
# weight, the 95% prediction interval spans the likely range of MPG values.
# ---------------------------------------------------------------------------

_x = np.array([r[1] for r in _RAW], dtype=float)   # weight
_y = np.array([r[0] for r in _RAW], dtype=float)   # mpg
_n = len(_x)
_x_mean = _x.mean()
_y_mean = _y.mean()
_b1 = np.sum((_x - _x_mean) * (_y - _y_mean)) / np.sum((_x - _x_mean) ** 2)
_b0 = _y_mean - _b1 * _x_mean
_y_hat = _b0 + _b1 * _x
_sse = np.sum((_y - _y_hat) ** 2)
_se = math.sqrt(_sse / (_n - 2))
_sx2 = np.sum((_x - _x_mean) ** 2)
# t critical value: 95% PI, df = n-2 = 28  ≈ 2.048
_T_CRIT = 2.048
_pi_margin = _T_CRIT * _se * np.sqrt(1.0 + 1.0 / _n + (_x - _x_mean) ** 2 / _sx2)
_pred_lo = np.round(_y_hat - _pi_margin, 1)
_pred_hi = np.round(_y_hat + _pi_margin, 1)

# ---------------------------------------------------------------------------
# pcarrow columns — shifts in (mpg, weight) space for each observation
# Start = actual (mpg, weight); End = (ŷ, weight) showing actual vs predicted
# ---------------------------------------------------------------------------
_pc_y1 = _y.tolist()                # actual mpg (arrow tail)
_pc_x1 = _x.tolist()               # actual weight (arrow tail)
_pc_y2 = np.round(_y_hat, 1).tolist()  # predicted mpg (arrow head)
_pc_x2 = _x.tolist()               # same weight (vertical arrow)

# ---------------------------------------------------------------------------
# Build full row list with derived columns appended
# ---------------------------------------------------------------------------
_ALL_COLS = _RAW_COLS + ["pred_lo", "pred_hi", "pc_y1", "pc_x1", "pc_y2", "pc_x2"]

_VALS = [
    tuple(raw) + (float(_pred_lo[i]), float(_pred_hi[i]),
                  float(_pc_y1[i]),   float(_pc_x1[i]),
                  float(_pc_y2[i]),   float(_pc_x2[i]))
    for i, raw in enumerate(_RAW)
]

# ---------------------------------------------------------------------------
# SAMPLE_DATA structure expected by DashRenderer
# ---------------------------------------------------------------------------
SAMPLE_DATA = {
    "StataJSON": {
        "variableNames": _ALL_COLS,
        "variableLabels": {
            "mpg":          "Mileage (mpg)",
            "weight":       "Weight (lbs.)",
            "price":        "Price (USD)",
            "rep78":        "Repair record 1978",
            "foreign":      "Car type",
            "length":       "Length (in.)",
            "displacement": "Displacement (cu. in.)",
            "headroom":     "Headroom (in.)",
            "turn":         "Turn circle (ft.)",
            "trunk":        "Trunk space (cu. ft.)",
            "pred_lo":      "OLS 95% Prediction Lower",
            "pred_hi":      "OLS 95% Prediction Upper",
            "pc_y1":        "Actual MPG (arrow start)",
            "pc_x1":        "Actual Weight (arrow start)",
            "pc_y2":        "Predicted MPG (arrow end)",
            "pc_x2":        "Predicted Weight (arrow end)",
        },
        "valueLabels":    {"foreign": {"0": "Domestic", "1": "Foreign"}},
        "valueLabelNames": {"foreign": "origin"},
        "variableTypeIsString": {c: False for c in _ALL_COLS},
        "values": [dict(zip(_ALL_COLS, row)) for row in _VALS],
    }
}


# ---------------------------------------------------------------------------
# Render helper
# ---------------------------------------------------------------------------

def render(spec: dict, out_name: str) -> None:
    """Write spec + sample data to temp files, render, save HTML."""
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
# Graph-spec helpers
# ---------------------------------------------------------------------------

def _g(name: str, plots: list, **gopts) -> dict:
    """Build a graph spec dict."""
    return {"plots": plots,
            "graph_options": {"name": name, **gopts},
            "if_expr": "", "in_expr": ""}


# Plot keys recognised as top-level (not placed in options)
_TOP_KEYS = ("yvar", "xvar", "yvar1", "yvar2", "var",
             "y1var", "x1var", "y2var", "x2var")


def _p(ptype: str, **kw) -> dict:
    opts = {k: v for k, v in kw.items() if k not in _TOP_KEYS}
    base = {k: v for k, v in kw.items() if k in _TOP_KEYS}
    return {"type": ptype, **base, "options": opts}


# ---- Bivariate helpers ----
def _s(y, x, **o):   return _p("scatter",   yvar=y, xvar=x, **o)
def _lf(y, x, **o):  return _p("lfit",      yvar=y, xvar=x, **o)
def _qf(y, x, **o):  return _p("qfit",      yvar=y, xvar=x, **o)
def _lw(y, x, **o):  return _p("lowess",    yvar=y, xvar=x, **o)
def _lp(y, x, **o):  return _p("lpoly",     yvar=y, xvar=x, **o)
def _ms(y, x, **o):  return _p("mspline",   yvar=y, xvar=x, **o)
def _mb(y, x, **o):  return _p("mband",     yvar=y, xvar=x, **o)
def _li(y, x, **o):  return _p("line",      yvar=y, xvar=x, **o)
def _co(y, x, **o):  return _p("connected", yvar=y, xvar=x, **o)
def _ar(y, x, **o):  return _p("area",      yvar=y, xvar=x, **o)
def _ba(y, x, **o):  return _p("bar",       yvar=y, xvar=x, **o)
def _sp(y, x, **o):  return _p("spike",     yvar=y, xvar=x, **o)
def _dl(y, x, **o):  return _p("dropline",  yvar=y, xvar=x, **o)
def _do(y, x, **o):  return _p("dot",       yvar=y, xvar=x, **o)

# ---- Univariate helpers ----
def _hi(y, **o):     return _p("histogram", yvar=y, **o)
def _kd(y, **o):     return _p("kdensity",  yvar=y, **o)

# ---- Range-plot helpers (yvar1=lower, yvar2=upper, xvar=x) ----
def _ra(y1, y2, x, **o):  return _p("rarea",      yvar1=y1, yvar2=y2, xvar=x, **o)
def _rb(y1, y2, x, **o):  return _p("rbar",       yvar1=y1, yvar2=y2, xvar=x, **o)
def _rc(y1, y2, x, **o):  return _p("rcap",       yvar1=y1, yvar2=y2, xvar=x, **o)
def _rsp(y1, y2, x, **o): return _p("rspike",     yvar1=y1, yvar2=y2, xvar=x, **o)
def _rl(y1, y2, x, **o):  return _p("rline",      yvar1=y1, yvar2=y2, xvar=x, **o)
def _rco(y1, y2, x, **o): return _p("rconnected", yvar1=y1, yvar2=y2, xvar=x, **o)
def _rcs(y1, y2, x, **o): return _p("rcapsym",    yvar1=y1, yvar2=y2, xvar=x, **o)
def _rs(y1, y2, x, **o):  return _p("rscatter",   yvar1=y1, yvar2=y2, xvar=x, **o)

# ---- Paired-coordinate helper (pcarrow uses actual→predicted positions) ----
def _pca(**o):
    return _p("pcarrow",
              y1var="pc_y1", x1var="pc_x1",
              y2var="pc_y2", x2var="pc_x2", **o)

# ---- If-filtered scatter (for multi-group encoding) ----
def _si(y, x, if_expr, **o):
    """Scatter with an if_expr for group subsetting."""
    base = {"type": "scatter", "yvar": y, "xvar": x,
            "if_expr": if_expr, "options": o}
    return base

def _lfi(y, x, if_expr, **o):
    """lfit with an if_expr for per-group OLS line."""
    return {"type": "lfit", "yvar": y, "xvar": x,
            "if_expr": if_expr, "options": o}

def _lwi(y, x, if_expr, **o):
    """lowess with an if_expr for per-group smoothed line."""
    return {"type": "lowess", "yvar": y, "xvar": x,
            "if_expr": if_expr, "options": o}

# ---- KPI helper ----
def _kpi(name, stat, var, title, fmt="%9.1f", subtitle="", update="filter"):
    return {"name": name, "stat": stat, "var": var, "title": title,
            "fmt": fmt, "subtitle": subtitle, "update": update}


# ---------------------------------------------------------------------------
# Filter spec — "filters" key (structured list) so the renderer reads it
# directly.  Labels must match what users see for categorical variables.
# ---------------------------------------------------------------------------

FILTERS = [
    {"varname": "foreign",  "type": "dropdown", "label": "Car Origin",    "exclude": []},
    {"varname": "mpg",      "type": "range",    "label": "MPG Range",     "exclude": []},
    {"varname": "weight",   "type": "slider",   "label": "Min Weight",    "exclude": []},
]

# ---------------------------------------------------------------------------
# Tabs string
# ---------------------------------------------------------------------------

TABS_STR = (
    "univariate: u1 u2 u4 u5 u6 u7 u8"
    " / bivariate: b1 b2 b3 b4 b5 b6 b7 b8 b9 b10 b11 b12 b13 b14 b15 b16 b17"
    " / multivariate: m1 m2 m3 m4 m5 m6 m7 m8 m9 m10 m11 m12 m13"
)

# ---------------------------------------------------------------------------
# UNIVARIATE tab (u1–u8)
# One graph per key numeric variable; histogram for distribution shape,
# kdensity for smooth density, and a combined overlay.
# ---------------------------------------------------------------------------

U_GRAPHS = [
    # u1 — MPG histogram
    _g("u1", [_hi("mpg", fcolor="navy", falpha="0.7")],
       title="MPG Distribution",
       xtitle="Mileage (mpg)", ytitle="Frequency",
       hover="mpg"),

    # u2 — MPG kernel density
    _g("u2", [_kd("mpg", lcolor="maroon", lwidth="2")],
       title="MPG Kernel Density",
       xtitle="Mileage (mpg)", ytitle="Density",
       hover="mpg"),

    # u4 — Price histogram
    _g("u4", [_hi("price", fcolor="forest_green", falpha="0.7")],
       title="Price Distribution",
       xtitle="Price (USD)", ytitle="Frequency",
       hover="price"),

    # u5 — Weight histogram
    _g("u5", [_hi("weight", fcolor="maroon", falpha="0.7")],
       title="Vehicle Weight Distribution",
       xtitle="Weight (lbs.)", ytitle="Frequency",
       hover="weight"),

    # u6 — Engine displacement histogram
    _g("u6", [_hi("displacement", fcolor="orange", falpha="0.7")],
       title="Engine Displacement Distribution",
       xtitle="Displacement (cu. in.)", ytitle="Frequency",
       hover="displacement"),

    # u7 — Length histogram
    _g("u7", [_hi("length", fcolor="purple", falpha="0.7")],
       title="Vehicle Length Distribution",
       xtitle="Length (in.)", ytitle="Frequency",
       hover="length"),

    # u8 — MPG by origin faceted via by()
    #      Note: by() graphs are NOT included in the link list.
    _g("u8", [_hi("mpg", fcolor="navy", falpha="0.7")],
       title="MPG Distribution by Car Origin",
       xtitle="Mileage (mpg)", ytitle="Frequency",
       hover="mpg foreign",
       **{"by": "foreign"}),
]

# ---------------------------------------------------------------------------
# BIVARIATE tab (b1–b17)
# Pairs of numeric variables, numeric × categorical, and range plots.
# Range plots (b14–b17) use OLS 95% prediction intervals computed above.
# ---------------------------------------------------------------------------

B_GRAPHS = [
    # b1 — scatter + OLS fit
    _g("b1",
       [_s("mpg", "weight", mcolor="navy",   msize="5"),
        _lf("mpg", "weight", lcolor="maroon", lwidth="2")],
       title="MPG vs Weight: Scatter + OLS Fit",
       xtitle="Weight (lbs.)", ytitle="Mileage (mpg)",
       hover="mpg weight price foreign rep78"),

    # b2 — scatter + Lowess
    _g("b2",
       [_s("mpg", "weight", mcolor="forest_green", msize="5"),
        _lw("mpg", "weight", lcolor="orange",       lwidth="2")],
       title="MPG vs Weight: Scatter + Lowess Smooth",
       xtitle="Weight (lbs.)", ytitle="Mileage (mpg)",
       hover="mpg weight price foreign rep78"),

    # b3 — scatter + quadratic fit
    _g("b3",
       [_s("price", "weight", mcolor="purple", msize="5"),
        _qf("price", "weight", lcolor="teal",  lwidth="2")],
       title="Price vs Weight: Quadratic Fit",
       xtitle="Weight (lbs.)", ytitle="Price (USD)",
       hover="price weight mpg foreign rep78"),

    # b4 — scatter + local polynomial
    _g("b4",
       [_s("mpg", "length", mcolor="maroon",       msize="5"),
        _lp("mpg", "length", lcolor="forest_green", lwidth="2")],
       title="MPG vs Length: Local Polynomial Fit",
       xtitle="Length (in.)", ytitle="Mileage (mpg)",
       hover="mpg length weight foreign"),

    # b5 — scatter + mean spline
    _g("b5",
       [_s("mpg", "weight", mcolor="orange", msize="5"),
        _ms("mpg", "weight", lcolor="navy",   lwidth="2")],
       title="MPG vs Weight: Mean Spline",
       xtitle="Weight (lbs.)", ytitle="Mileage (mpg)",
       hover="mpg weight price foreign"),

    # b6 — scatter + mean band
    _g("b6",
       [_s("mpg", "weight", mcolor="navy",                    msize="5"),
        _mb("mpg", "weight", fcolor="ltblue", falpha="0.35")],
       title="MPG vs Weight: Mean Band",
       xtitle="Weight (lbs.)", ytitle="Mileage (mpg)",
       hover="mpg weight price foreign"),

    # b7 — line (data sorted by weight → clean trend line)
    _g("b7",
       [_li("mpg", "weight", lcolor="navy", lwidth="2")],
       title="MPG vs Weight: Line Chart",
       xtitle="Weight (lbs.)", ytitle="Mileage (mpg)",
       hover="mpg weight"),

    # b8 — connected
    _g("b8",
       [_co("mpg", "weight", mcolor="maroon", lcolor="maroon", lwidth="1.5")],
       title="MPG vs Weight: Connected Points",
       xtitle="Weight (lbs.)", ytitle="Mileage (mpg)",
       hover="mpg weight"),

    # b9 — area: engine displacement vs vehicle weight
    #      Heavier cars have larger engines — the rising fill makes physical sense.
    _g("b9",
       [_ar("displacement", "weight", fcolor="ltblue", falpha="0.6")],
       title="Engine Displacement vs Weight: Area Chart",
       xtitle="Weight (lbs.)", ytitle="Displacement (cu. in.)",
       hover="displacement weight mpg foreign"),

    # b10 — dot chart: individual MPG values by repair record category
    #       Shows the full distribution within each repair category, not means.
    _g("b10",
       [_do("mpg", "rep78", mcolor="forest_green", msize="6")],
       title="Mileage by Repair Record: Individual Values",
       xtitle="Repair Record (1 = poor … 5 = excellent)", ytitle="Mileage (mpg)",
       hover="mpg rep78 price foreign weight"),

    # b11 — dot chart: price by repair record
    _g("b11",
       [_do("price", "rep78", mcolor="navy", msize="6")],
       title="Price by Repair Record: Dot Chart",
       xtitle="Repair Record (1–5)", ytitle="Price (USD)",
       hover="price rep78 mpg foreign"),

    # b12 — spike
    _g("b12",
       [_sp("price", "weight", lcolor="navy", lwidth="1")],
       title="Price vs Weight: Spike Chart",
       xtitle="Weight (lbs.)", ytitle="Price (USD)",
       hover="price weight mpg"),

    # b13 — dropline
    _g("b13",
       [_dl("price", "displacement", mcolor="maroon", lcolor="maroon", lwidth="1.5")],
       title="Price vs Displacement: Dropline",
       xtitle="Displacement (cu. in.)", ytitle="Price (USD)",
       hover="price displacement weight mpg foreign"),

    # b14 — rarea: OLS 95% prediction interval band for mpg ~ weight
    #       Shaded region = plausible MPG range for each vehicle weight.
    _g("b14",
       [_ra("pred_lo", "pred_hi", "weight", fcolor="ltblue", falpha="0.5")],
       title="MPG ~ Weight: OLS 95% Prediction Interval (rarea)",
       xtitle="Weight (lbs.)", ytitle="MPG Prediction Interval"),

    # b15 — rbar: same prediction interval shown as range bars
    _g("b15",
       [_rb("pred_lo", "pred_hi", "weight", fcolor="maroon", falpha="0.6")],
       title="MPG ~ Weight: OLS 95% Prediction Interval (rbar)",
       xtitle="Weight (lbs.)", ytitle="MPG Prediction Interval"),

    # b16 — rcap: capped error-bar style prediction interval
    _g("b16",
       [_rc("pred_lo", "pred_hi", "weight", lcolor="navy", lwidth="1.5")],
       title="MPG ~ Weight: OLS 95% Prediction Interval (rcap)",
       xtitle="Weight (lbs.)", ytitle="MPG Prediction Interval"),

    # b17 — rspike: spike error-bar style prediction interval
    _g("b17",
       [_rsp("pred_lo", "pred_hi", "weight", lcolor="forest_green", lwidth="1.5")],
       title="MPG ~ Weight: OLS 95% Prediction Interval (rspike)",
       xtitle="Weight (lbs.)", ytitle="MPG Prediction Interval"),
]

# ---------------------------------------------------------------------------
# MULTIVARIATE tab (m1–m14)
# Every graph encodes information from ≥ 3 variables simultaneously using
# multiple colored/shaped series, per-group fitted curves, or range overlays.
# ---------------------------------------------------------------------------

M_GRAPHS = [
    # m1 — MPG vs Weight faceted by Origin (by() → 2 separate panels)
    #      3 variables: mpg, weight, foreign  |  cannot be in link list
    _g("m1",
       [_s("mpg", "weight", mcolor="navy", msize="5")],
       title="MPG vs Weight — Faceted by Car Origin",
       xtitle="Weight (lbs.)", ytitle="Mileage (mpg)",
       hover="mpg weight price foreign rep78",
       **{"by": "foreign"}),

    # m2 — MPG vs Weight: 5 repair-record groups (color + marker shape)
    #      3 variables: mpg, weight, rep78 (encoded via color + symbol)
    _g("m2",
       [_si("mpg", "weight", "rep78==1", mcolor="navy",         msymbol="circle",           msize="6"),
        _si("mpg", "weight", "rep78==2", mcolor="maroon",       msymbol="square",           msize="6"),
        _si("mpg", "weight", "rep78==3", mcolor="forest_green", msymbol="triangle",         msize="6"),
        _si("mpg", "weight", "rep78==4", mcolor="orange",       msymbol="diamond",          msize="6"),
        _si("mpg", "weight", "rep78==5", mcolor="purple",       msymbol="inverted_triangle",msize="6"),
       ],
       title="MPG vs Weight by Repair Record (color + shape encode rep78)",
       xtitle="Weight (lbs.)", ytitle="Mileage (mpg)",
       hover="mpg weight rep78 foreign price"),

    # m3 — Price vs Displacement by Origin (color + shape encode foreign)
    #      3 variables: price, displacement, foreign
    _g("m3",
       [_si("price", "displacement", "foreign==0",
            mcolor="maroon", msymbol="circle",  msize="6"),
        _si("price", "displacement", "foreign==1",
            mcolor="navy",   msymbol="diamond", msize="6"),
       ],
       title="Price vs Displacement by Car Origin",
       xtitle="Displacement (cu. in.)", ytitle="Price (USD)",
       hover="price displacement foreign weight mpg"),

    # m4 — MPG vs Weight: two origin groups + per-group OLS line
    #      4 variables: mpg, weight, foreign (color), OLS slope per group
    _g("m4",
       [_si("mpg",  "weight", "foreign==0", mcolor="maroon", msymbol="circle",  msize="5"),
        _si("mpg",  "weight", "foreign==1", mcolor="navy",   msymbol="diamond", msize="5"),
        _lfi("mpg", "weight", "foreign==0", lcolor="maroon", lwidth="2"),
        _lfi("mpg", "weight", "foreign==1", lcolor="navy",   lwidth="2"),
       ],
       title="MPG vs Weight by Origin with Per-Group OLS Fit",
       xtitle="Weight (lbs.)", ytitle="Mileage (mpg)",
       hover="mpg weight foreign price rep78"),

    # m5 — MPG vs Length: two origin groups + per-group Lowess
    #      4 variables: mpg, length, foreign (color), Lowess per group
    _g("m5",
       [_si("mpg",  "length", "foreign==0", mcolor="maroon",       msymbol="circle",  msize="5"),
        _si("mpg",  "length", "foreign==1", mcolor="forest_green", msymbol="diamond", msize="5"),
        _lwi("mpg", "length", "foreign==0", lcolor="maroon",       lwidth="2"),
        _lwi("mpg", "length", "foreign==1", lcolor="forest_green", lwidth="2"),
       ],
       title="MPG vs Length by Origin with Per-Group Lowess",
       xtitle="Length (in.)", ytitle="Mileage (mpg)",
       hover="mpg length foreign weight"),

    # m6 — Price vs Weight: two origin groups + per-group OLS
    #      4 variables: price, weight, foreign (color), OLS slope per group
    _g("m6",
       [_si("price", "weight", "foreign==0", mcolor="orange", msymbol="circle",  msize="5"),
        _si("price", "weight", "foreign==1", mcolor="purple", msymbol="diamond", msize="5"),
        _lfi("price", "weight", "foreign==0", lcolor="orange", lwidth="2"),
        _lfi("price", "weight", "foreign==1", lcolor="purple", lwidth="2"),
       ],
       title="Price vs Weight by Origin with Per-Group OLS Fit",
       xtitle="Weight (lbs.)", ytitle="Price (USD)",
       hover="price weight foreign mpg rep78"),

    # m7 — MPG vs Displacement: 5 repair-record groups
    #      3 variables: mpg, displacement, rep78 (encoded via color + shape)
    _g("m7",
       [_si("mpg", "displacement", "rep78==1", mcolor="navy",         msymbol="circle",           msize="6"),
        _si("mpg", "displacement", "rep78==2", mcolor="maroon",       msymbol="square",           msize="6"),
        _si("mpg", "displacement", "rep78==3", mcolor="forest_green", msymbol="triangle",         msize="6"),
        _si("mpg", "displacement", "rep78==4", mcolor="orange",       msymbol="diamond",          msize="6"),
        _si("mpg", "displacement", "rep78==5", mcolor="purple",       msymbol="inverted_triangle",msize="6"),
       ],
       title="MPG vs Displacement by Repair Record",
       xtitle="Displacement (cu. in.)", ytitle="Mileage (mpg)",
       hover="mpg displacement rep78 weight foreign"),

    # m8 — Scatter + OLS prediction band (rarea)
    #      4 variables: actual mpg (dots), weight, pred_lo, pred_hi (band)
    _g("m8",
       [_ra("pred_lo", "pred_hi", "weight", fcolor="ltblue", falpha="0.35"),
        _s("mpg", "weight", mcolor="navy", msize="5"),
       ],
       title="MPG vs Weight: Data Points Inside 95% Prediction Band",
       xtitle="Weight (lbs.)", ytitle="Mileage (mpg)",
       hover="mpg weight pred_lo pred_hi foreign"),

    # m9 — Scatter + rcap prediction interval
    #      4 variables: mpg (dots), weight, pred_lo, pred_hi (error bars)
    _g("m9",
       [_rc("pred_lo", "pred_hi", "weight", lcolor="navy", lwidth="1.5"),
        _s("mpg", "weight", mcolor="maroon", msize="5"),
       ],
       title="MPG vs Weight: Data Points + 95% PI Cap Error Bars",
       xtitle="Weight (lbs.)", ytitle="Mileage (mpg)",
       hover="mpg weight pred_lo pred_hi foreign"),

    # m10 — Scatter + rspike prediction interval
    _g("m10",
       [_rsp("pred_lo", "pred_hi", "weight", lcolor="forest_green", lwidth="1.5"),
        _s("mpg", "weight", mcolor="maroon", msize="5"),
       ],
       title="MPG vs Weight: Data Points + 95% PI Spike Error Bars",
       xtitle="Weight (lbs.)", ytitle="Mileage (mpg)",
       hover="mpg weight pred_lo pred_hi foreign"),

    # m11 — rconnected: lower and upper PI lines connected across weight
    #       3 variables: pred_lo (lower line), pred_hi (upper line), weight
    _g("m11",
       [_rl("pred_lo", "pred_hi", "weight", lcolor="navy", lwidth="1.5")],
       title="MPG ~ Weight: OLS 95% PI Upper + Lower Lines (rline)",
       xtitle="Weight (lbs.)", ytitle="MPG Prediction Interval",
       hover="pred_lo pred_hi weight"),

    # m12 — rscatter: two y-values at each x — both PI bounds as dots
    #       3 variables: pred_lo, pred_hi, weight
    _g("m12",
       [_rs("pred_lo", "pred_hi", "weight", mcolor="purple", msize="5")],
       title="MPG ~ Weight: PI Lower and Upper Bound Points (rscatter)",
       xtitle="Weight (lbs.)", ytitle="MPG Prediction Interval",
       hover="pred_lo pred_hi weight mpg"),

    # m13 — pcarrow: arrows from actual MPG to OLS-predicted MPG at same weight
    #       4 variables: pc_y1 (actual mpg), pc_x1 (weight), pc_y2 (predicted),
    #                    pc_x2 (weight, same) — vertical arrows show residuals
    _g("m13",
       [_pca(lcolor="maroon", lwidth="1.5")],
       title="Residual Arrows: Actual MPG → OLS Predicted MPG",
       xtitle="Weight (lbs.)", ytitle="Mileage (mpg)",
       hover="pc_y1 pc_x1 pc_y2 pc_x2"),

]

# ---------------------------------------------------------------------------
# Link list: all graphs that share raw columnar data and should respond
# consistently to the dropdown / slider / range filters.
# Excluded from link: by() graphs (u8, m1), pcarrow (m13),
# and range-only plots without a scatter overlay (b14-b17, m11, m12).
# ---------------------------------------------------------------------------

_LINK = (
    "u1 u2 u4 u5 u6 u7 "           # univariate histograms + kdensity
    "b1 b2 b3 b4 b5 b6 b7 b8 b9 "  # bivariate scatter / line / area
    "b10 b11 b12 b13 "              # dot / spike / dropline
    "m2 m3 m4 m5 m6 m7 "           # multivariate scatter groups
    "m8 m9 m10"                     # scatter + range-band overlays
)

# ---------------------------------------------------------------------------
# Full dashboard spec
# ---------------------------------------------------------------------------

SPEC = {
    "graphs": U_GRAPHS + B_GRAPHS + M_GRAPHS,
    "kpis": [
        _kpi("k1", "mean",  "mpg",         "Avg MPG",    "%9.1f",  "miles per gallon"),
        _kpi("k2", "count", "mpg",          "# Vehicles", "%9.0f",  "in current filter"),
        _kpi("k3", "mean",  "price",        "Avg Price",  "%9.0fc", "USD"),
        _kpi("k4", "mean",  "weight",       "Avg Weight", "%9.0fc", "lbs."),
        _kpi("k5", "mean",  "rep78",        "Avg Repair", "%9.2f",  "1 (poor) – 5 (excellent)"),
        _kpi("k6", "mean",  "displacement", "Avg Displ.", "%9.0f",  "cu. inches"),
    ],
    "build_options": {
        "layout":          "bs",
        # "filters" key (structured list) is read directly by the renderer.
        # The "filter" key expects a Stata-format string, not a JSON array.
        "filters":         FILTERS,
        "link":            _LINK,
        "theme":           "default",
        "title":           "Stata dash — Comprehensive Feature Demo",
        "subtitle":        "1978 Auto Data · All Plot Types · Filters · Linked Brushing · Tabs",
        "registry":        "",
        "tabs":            TABS_STR,
        "filter_position": "left",
    },
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Generating comprehensive demo dashboard...")
    render(SPEC, "comprehensive_demo.html")
    print("Done.")
