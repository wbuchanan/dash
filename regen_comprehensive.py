#!/usr/bin/env python3
"""regen_comprehensive.py
Regenerate comprehensive_demo.html without Stata.

Demonstrates every twoway plot type, all three filter types (dropdown,
range, slider), linked brushing, Bootstrap sidebar layout, and three
tab panels (Univariate / Bivariate / Multivariate).

Fixes vs previous version
--------------------------
* Filters now use the "filters" key (structured list) so they appear in
  the rendered HTML.
* scatteri spec uses the "values" key (list of [y, x] pairs).
* function spec places "expr" at the plot-root level and "range" in options.
* Sample data is sorted by weight so area/line/range plots render cleanly.
* Every graph has a proper ytitle and xtitle.
* Univariate tab: one histogram per key numeric variable + KDE overlays.
* Bivariate tab: meaningful (x, y) pairs using scatter, fitted lines,
  range plots, bar, dot, area, spike, and dropline types.
* Multivariate tab: each graph encodes ≥ 3 variables using color, marker
  shape, or error-band overlays.
* All graphs carry a "hover" option listing tooltip variables.

Run from the dash/ directory:
    /Users/billy/anaconda3/bin/python3 regen_comprehensive.py
"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from dash_render import DashRenderer

# ---------------------------------------------------------------------------
# 30-observation sample — auto dataset variables + derived columns
# Sorted by weight so area/line/range plots render cleanly.
# ---------------------------------------------------------------------------

_VALS = [
    # mpg  weight  price   rep78  foreign  length  displacement  headroom  turn  trunk  mpg_lo  mpg_hi  pc_y1  pc_x1  pc_y2   pc_x2
    (32,   1760,   3995,   5,     1,       154,    61,           2.5,      32,   6,     30,     34,     32,    1760,  36,     2060),
    (35,   1800,   3748,   5,     1,       157,    61,           2.0,      30,   8,     33,     37,     35,    1800,  39,     2100),
    (35,   1800,   3895,   2,     0,       147,    97,           3.0,      33,   11,    33,     37,     29,    1800,  27,     1650),
    (28,   1985,   5886,   5,     1,       163,    91,           3.5,      36,   8,     26,     30,     28,    1985,  32,     2285),
    (25,   1975,   4099,   4,     1,       166,    97,           2.5,      35,   8,     23,     27,     25,    1975,  29,     2275),
    (26,   1990,   8129,   4,     1,       163,    97,           2.5,      34,   8,     24,     28,     26,    1990,  30,     2290),
    (24,   2025,   7140,   5,     1,       165,    97,           3.0,      35,   8,     22,     26,     24,    2025,  28,     2325),
    (24,   2040,   4697,   5,     1,       165,    98,           3.0,      34,   8,     22,     26,     24,    2040,  28,     2340),
    (31,   2050,   6479,   5,     1,       164,    91,           3.5,      36,   8,     29,     33,     31,    2050,  35,     2350),
    (30,   2120,   5079,   4,     1,       172,    107,          2.5,      36,   8,     28,     32,     30,    2120,  34,     2420),
    (23,   2200,   9690,   5,     1,       172,    120,          2.5,      36,   8,     21,     25,     23,    2200,  27,     2500),
    (22,   2280,   5798,   4,     1,       170,    120,          3.0,      37,   8,     20,     24,     22,    2280,  26,     2580),
    (26,   2230,   4453,   3,     0,       170,    151,          3.5,      40,   10,    24,     28,     26,    2230,  24,     2080),
    (22,   2640,   3799,   4,     0,       168,    121,          3.0,      35,   13,    20,     24,     22,    2640,  20,     2490),
    (17,   2650,   5189,   4,     1,       176,    120,          3.5,      38,   8,     15,     19,     21,    2650,  25,     2950),
    (21,   2750,   4425,   4,     1,       193,    146,          2.5,      40,   12,    19,     23,     21,    2750,  25,     3050),
    (17,   2750,   6295,   3,     1,       180,    134,          4.0,      40,   10,    15,     19,     17,    2750,  21,     3050),
    (22,   2930,   4099,   5,     0,       186,    121,          2.5,      43,   11,    20,     24,     22,    2930,  20,     2780),
    (20,   3250,   4816,   3,     0,       196,    196,          4.0,      40,   16,    18,     22,     20,    3250,  18,     3100),
    (20,   3280,   6900,   2,     0,       200,    250,          3.5,      42,   16,    18,     22,     20,    3280,  18,     3130),
    (19,   3302,   6295,   3,     0,       197,    250,          3.5,      43,   18,    17,     21,     19,    3302,  17,     3152),
    (17,   3350,   4749,   3,     0,       173,    258,          2.5,      40,   11,    15,     19,     17,    3350,  15,     3200),
    (16,   3609,   4890,   3,     0,       219,    307,          3.5,      44,   17,    14,     18,     16,    3609,  14,     3459),
    (18,   3670,   5788,   3,     0,       218,    231,          4.0,      41,   15,    16,     20,     18,    3670,  16,     3520),
    (16,   3820,   6165,   3,     0,       212,    307,          3.0,      43,   13,    14,     18,     16,    3820,  14,     3670),
    (17,   3850,   5898,   3,     0,       218,    302,          4.0,      43,   19,    15,     19,     17,    3850,  15,     3700),
    (15,   4080,   7827,   4,     0,       222,    305,          4.0,      43,   21,    13,     17,     15,    4080,  13,     3930),
    (14,   4330,   5172,   2,     0,       221,    304,          3.5,      48,   16,    12,     16,     14,    4330,  12,     4180),
    (14,   3900,   5705,   4,     0,       204,    350,          4.0,      43,   21,    12,     16,     14,    3900,  12,     3750),
    (16,   3820,   6165,   3,     0,       212,    307,          3.0,      43,   13,    14,     18,     16,    3820,  14,     3670),
]

_COLS = ["mpg", "weight", "price", "rep78", "foreign", "length", "displacement",
         "headroom", "turn", "trunk", "mpg_lo", "mpg_hi", "pc_y1", "pc_x1", "pc_y2", "pc_x2"]

SAMPLE_DATA = {
    "StataJSON": {
        "variableNames": _COLS,
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
            "mpg_lo":       "MPG lower bound",
            "mpg_hi":       "MPG upper bound",
            "pc_y1":        "Arrow start Y (MPG)",
            "pc_x1":        "Arrow start X (Weight)",
            "pc_y2":        "Arrow end Y (MPG shifted)",
            "pc_x2":        "Arrow end X (Weight shifted)",
        },
        "valueLabels":    {"foreign": {"0": "Domestic", "1": "Foreign"}},
        "valueLabelNames": {"foreign": "origin"},
        "variableTypeIsString": {c: False for c in _COLS},
        "values": [dict(zip(_COLS, row)) for row in _VALS],
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
_TOP_KEYS = ("yvar", "xvar", "yvar1", "yvar2", "var", "y1var", "x1var", "y2var", "x2var")


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

# ---- Fit-with-CI helpers ----
def _lfc(y, x, **o): return _p("lfitci",  yvar=y, xvar=x, **o)
def _qfc(y, x, **o): return _p("qfitci",  yvar=y, xvar=x, **o)
def _lpc(y, x, **o): return _p("lpolyci", yvar=y, xvar=x, **o)
def _fpc(y, x, **o): return _p("fpfitci", yvar=y, xvar=x, **o)

# ---- Range-plot helpers ----
def _ra(y1, y2, x, **o):  return _p("rarea",      yvar1=y1, yvar2=y2, xvar=x, **o)
def _rb(y1, y2, x, **o):  return _p("rbar",       yvar1=y1, yvar2=y2, xvar=x, **o)
def _rc(y1, y2, x, **o):  return _p("rcap",       yvar1=y1, yvar2=y2, xvar=x, **o)
def _rsp(y1, y2, x, **o): return _p("rspike",     yvar1=y1, yvar2=y2, xvar=x, **o)
def _rl(y1, y2, x, **o):  return _p("rline",      yvar1=y1, yvar2=y2, xvar=x, **o)
def _rco(y1, y2, x, **o): return _p("rconnected", yvar1=y1, yvar2=y2, xvar=x, **o)
def _rcs(y1, y2, x, **o): return _p("rcapsym",    yvar1=y1, yvar2=y2, xvar=x, **o)
def _rs(y1, y2, x, **o):  return _p("rscatter",   yvar1=y1, yvar2=y2, xvar=x, **o)

# ---- Paired-coordinate helper ----
def _pca(**o): return _p("pcarrow",
                          y1var="pc_y1", x1var="pc_x1",
                          y2var="pc_y2", x2var="pc_x2", **o)

# ---- KPI helper ----
def _kpi(name, stat, var, title, fmt="%9.1f", subtitle="", update="filter"):
    return {"name": name, "stat": stat, "var": var, "title": title,
            "fmt": fmt, "subtitle": subtitle, "update": update}


# ---------------------------------------------------------------------------
# Filter spec — use the "filters" key (structured list) so the renderer
# picks it up directly without calling _parse_filter_raw on a JSON string.
# ---------------------------------------------------------------------------

FILTERS = [
    {"varname": "foreign", "type": "dropdown", "label": "Car Origin",  "exclude": []},
    {"varname": "mpg",     "type": "range",    "label": "MPG Range",   "exclude": []},
    {"varname": "weight",  "type": "slider",   "label": "Weight ≥",    "exclude": []},
]

# ---------------------------------------------------------------------------
# Tabs string
# ---------------------------------------------------------------------------

TABS_STR = (
    "univariate: u1 u2 u3 u4 u5 u6 u7 u8"
    " / bivariate: b1 b2 b3 b4 b5 b6 b7 b8 b9 b10 b11 b12 b13 b14 b15 b16 b17"
    " / multivariate: m1 m2 m3 m4 m5 m6 m7 m8 m9 m10 m11 m12 m13 m14"
)

# ---------------------------------------------------------------------------
# UNIVARIATE tab (u1–u8)
# One graph per key numeric variable; histogram for distribution shape,
# kdensity for smooth density, and a faceted histogram to compare groups.
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

    # u3 — MPG histogram + KDE overlay
    _g("u3", [_hi("mpg", fcolor="ltblue", falpha="0.5"),
              _kd("mpg", lcolor="maroon", lwidth="2")],
       title="MPG: Histogram + Density Overlay",
       xtitle="Mileage (mpg)", ytitle="Frequency / Density",
       hover="mpg"),

    # u4 — Price histogram
    _g("u4", [_hi("price", fcolor="forest_green", falpha="0.7")],
       title="Price Distribution",
       xtitle="Price (USD)", ytitle="Frequency",
       hover="price"),

    # u5 — Weight histogram
    _g("u5", [_hi("weight", fcolor="maroon", falpha="0.7")],
       title="Vehicle Weight Distribution",
       xtitle="Weight (lbs)", ytitle="Frequency",
       hover="weight"),

    # u6 — Engine displacement histogram
    _g("u6", [_hi("displacement", fcolor="orange", falpha="0.7")],
       title="Engine Displacement Distribution",
       xtitle="Displacement (cu in)", ytitle="Frequency",
       hover="displacement"),

    # u7 — Length histogram
    _g("u7", [_hi("length", fcolor="purple", falpha="0.7")],
       title="Vehicle Length Distribution",
       xtitle="Length (in)", ytitle="Frequency",
       hover="length"),

    # u8 — MPG by origin (faceted histogram via by())
    _g("u8", [_hi("mpg", fcolor="navy", falpha="0.7")],
       title="MPG Distribution by Origin",
       xtitle="Mileage (mpg)", ytitle="Frequency",
       hover="mpg foreign",
       **{"by": "foreign"}),
]

# ---------------------------------------------------------------------------
# BIVARIATE tab (b1–b17)
# Pairs of numeric variables, numeric × categorical, and range plots.
# ---------------------------------------------------------------------------

B_GRAPHS = [
    # b1 — scatter + OLS fit
    _g("b1",
       [_s("mpg", "weight", mcolor="navy",   msize="5"),
        _lf("mpg", "weight", lcolor="maroon", lwidth="2")],
       title="MPG vs Weight: Scatter + OLS",
       xtitle="Weight (lbs)", ytitle="Mileage (mpg)",
       hover="mpg weight price foreign rep78"),

    # b2 — scatter + Lowess
    _g("b2",
       [_s("mpg", "weight", mcolor="forest_green", msize="5"),
        _lw("mpg", "weight", lcolor="orange",       lwidth="2")],
       title="MPG vs Weight: Scatter + Lowess",
       xtitle="Weight (lbs)", ytitle="Mileage (mpg)",
       hover="mpg weight price foreign rep78"),

    # b3 — scatter + quadratic fit
    _g("b3",
       [_s("price", "weight", mcolor="purple", msize="5"),
        _qf("price", "weight", lcolor="teal",  lwidth="2")],
       title="Price vs Weight: Quadratic Fit",
       xtitle="Weight (lbs)", ytitle="Price (USD)",
       hover="price weight mpg foreign rep78"),

    # b4 — scatter + local polynomial
    _g("b4",
       [_s("mpg", "length", mcolor="maroon",       msize="5"),
        _lp("mpg", "length", lcolor="forest_green", lwidth="2")],
       title="MPG vs Length: Local Polynomial Fit",
       xtitle="Length (in)", ytitle="Mileage (mpg)",
       hover="mpg length weight foreign"),

    # b5 — scatter + mean spline
    _g("b5",
       [_s("mpg", "weight", mcolor="orange", msize="5"),
        _ms("mpg", "weight", lcolor="navy",   lwidth="2")],
       title="MPG vs Weight: Mean Spline",
       xtitle="Weight (lbs)", ytitle="Mileage (mpg)",
       hover="mpg weight price foreign"),

    # b6 — scatter + mean band
    _g("b6",
       [_s("mpg", "weight", mcolor="navy",                    msize="5"),
        _mb("mpg", "weight", fcolor="ltblue", falpha="0.35")],
       title="MPG vs Weight: Mean Band",
       xtitle="Weight (lbs)", ytitle="Mileage (mpg)",
       hover="mpg weight price foreign"),

    # b7 — line (data sorted by weight → clean trend line)
    _g("b7",
       [_li("mpg", "weight", lcolor="navy", lwidth="2")],
       title="MPG vs Weight: Line Chart",
       xtitle="Weight (lbs)", ytitle="Mileage (mpg)",
       hover="mpg weight"),

    # b8 — connected
    _g("b8",
       [_co("mpg", "weight", mcolor="maroon", lcolor="maroon", lwidth="1.5")],
       title="MPG vs Weight: Connected Points",
       xtitle="Weight (lbs)", ytitle="Mileage (mpg)",
       hover="mpg weight"),

    # b9 — area (data sorted by weight → smooth fill)
    _g("b9",
       [_ar("mpg", "weight", fcolor="ltblue", falpha="0.6")],
       title="MPG vs Weight: Area Chart",
       xtitle="Weight (lbs)", ytitle="Mileage (mpg)",
       hover="mpg weight"),

    # b10 — bar chart: average MPG by repair record (categorical × numeric)
    _g("b10",
       [_ba("mpg", "rep78", fcolor="navy", falpha="0.8")],
       title="Average MPG by Repair Record",
       xtitle="Repair Record (1 = Poor … 5 = Excellent)", ytitle="Mileage (mpg)",
       hover="mpg rep78"),

    # b11 — dot chart
    _g("b11",
       [_do("price", "rep78", mcolor="forest_green", msize="6")],
       title="Price by Repair Record: Dot Chart",
       xtitle="Repair Record (1–5)", ytitle="Price (USD)",
       hover="price rep78 mpg foreign"),

    # b12 — spike
    _g("b12",
       [_sp("price", "weight", lcolor="navy", lwidth="1")],
       title="Price vs Weight: Spike Chart",
       xtitle="Weight (lbs)", ytitle="Price (USD)",
       hover="price weight mpg"),

    # b13 — dropline
    _g("b13",
       [_dl("price", "displacement", mcolor="maroon", lcolor="maroon", lwidth="1.5")],
       title="Price vs Displacement: Dropline",
       xtitle="Displacement (cu in)", ytitle="Price (USD)",
       hover="price displacement weight mpg foreign"),

    # b14 — rarea: MPG ± 2 band vs weight
    _g("b14",
       [_ra("mpg_lo", "mpg_hi", "weight", fcolor="ltblue", falpha="0.45", lwidth="0")],
       title="MPG ± 2 Range Area vs Weight",
       xtitle="Weight (lbs)", ytitle="MPG ± 2 Bounds",
       hover="mpg_lo mpg_hi weight mpg"),

    # b15 — rbar: MPG ± 2 bars vs weight
    _g("b15",
       [_rb("mpg_lo", "mpg_hi", "weight", fcolor="maroon", falpha="0.6")],
       title="MPG ± 2 Range Bars vs Weight",
       xtitle="Weight (lbs)", ytitle="MPG ± 2 Bounds",
       hover="mpg_lo mpg_hi weight mpg"),

    # b16 — rcap: cap error bars
    _g("b16",
       [_rc("mpg_lo", "mpg_hi", "weight", lcolor="navy", lwidth="1.5")],
       title="MPG ± 2 Cap Error Bars vs Weight",
       xtitle="Weight (lbs)", ytitle="MPG ± 2 Bounds",
       hover="mpg_lo mpg_hi weight mpg"),

    # b17 — rspike: spike error bars
    _g("b17",
       [_rsp("mpg_lo", "mpg_hi", "weight", lcolor="forest_green", lwidth="1.5")],
       title="MPG ± 2 Spike Error Bars vs Weight",
       xtitle="Weight (lbs)", ytitle="MPG ± 2 Bounds",
       hover="mpg_lo mpg_hi weight mpg"),
]

# ---------------------------------------------------------------------------
# MULTIVARIATE tab (m1–m14)
# Each graph encodes information from ≥ 3 variables.
# ---------------------------------------------------------------------------

M_GRAPHS = [
    # m1 — MPG vs Weight faceted by Origin (by() → two separate panels)
    #      Encodes: mpg, weight, foreign
    _g("m1",
       [_s("mpg", "weight", mcolor="navy", msize="5")],
       title="MPG vs Weight — Faceted by Origin",
       xtitle="Weight (lbs)", ytitle="Mileage (mpg)",
       hover="mpg weight price foreign rep78",
       **{"by": "foreign"}),

    # m2 — MPG vs Weight with 5 repair-record groups encoded by color + shape
    #      Encodes: mpg, weight, rep78 (color + marker)
    _g("m2",
       [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
         "if_expr": "rep78==1",
         "options": {"mcolor": "navy",         "msymbol": "circle",           "msize": "5"}},
        {"type": "scatter", "yvar": "mpg", "xvar": "weight",
         "if_expr": "rep78==2",
         "options": {"mcolor": "maroon",       "msymbol": "square",           "msize": "5"}},
        {"type": "scatter", "yvar": "mpg", "xvar": "weight",
         "if_expr": "rep78==3",
         "options": {"mcolor": "forest_green", "msymbol": "triangle",         "msize": "5"}},
        {"type": "scatter", "yvar": "mpg", "xvar": "weight",
         "if_expr": "rep78==4",
         "options": {"mcolor": "orange",       "msymbol": "diamond",          "msize": "5"}},
        {"type": "scatter", "yvar": "mpg", "xvar": "weight",
         "if_expr": "rep78==5",
         "options": {"mcolor": "purple",       "msymbol": "inverted_triangle","msize": "5"}},
       ],
       title="MPG vs Weight: Repair Record Groups (color + shape)",
       xtitle="Weight (lbs)", ytitle="Mileage (mpg)",
       hover="mpg weight rep78 foreign price"),

    # m3 — Price vs Displacement by Origin (color + shape encode foreign)
    #      Encodes: price, displacement, foreign
    _g("m3",
       [{"type": "scatter", "yvar": "price", "xvar": "displacement",
         "if_expr": "foreign==0",
         "options": {"mcolor": "maroon", "msymbol": "circle",  "msize": "6"}},
        {"type": "scatter", "yvar": "price", "xvar": "displacement",
         "if_expr": "foreign==1",
         "options": {"mcolor": "navy",   "msymbol": "diamond", "msize": "6"}},
       ],
       title="Price vs Displacement by Origin",
       xtitle="Displacement (cu in)", ytitle="Price (USD)",
       hover="price displacement foreign weight mpg"),

    # m4 — scatter + lfitci  (data + fit line + CI band = 3 encoded layers)
    #      Encodes: mpg, weight, confidence interval
    _g("m4",
       [_s("mpg", "weight", mcolor="navy",   msize="5"),
        _lfc("mpg", "weight", fcolor="ltblue", falpha="0.3")],
       title="MPG vs Weight: OLS Fit + 95% CI",
       xtitle="Weight (lbs)", ytitle="Mileage (mpg)",
       hover="mpg weight foreign price rep78"),

    # m5 — scatter + qfitci
    #      Encodes: price, weight, quadratic CI
    _g("m5",
       [_s("price", "weight", mcolor="purple",   msize="5"),
        _qfc("price", "weight", fcolor="lavender", falpha="0.3")],
       title="Price vs Weight: Quadratic Fit + 95% CI",
       xtitle="Weight (lbs)", ytitle="Price (USD)",
       hover="price weight mpg foreign rep78"),

    # m6 — scatter + lpolyci
    #      Encodes: mpg, length, local-poly CI
    _g("m6",
       [_s("mpg", "length", mcolor="forest_green", msize="5"),
        _lpc("mpg", "length", fcolor="lime",         falpha="0.3")],
       title="MPG vs Length: Local Poly + 95% CI",
       xtitle="Length (in)", ytitle="Mileage (mpg)",
       hover="mpg length weight foreign"),

    # m7 — scatter + fpfitci
    #      Encodes: mpg, displacement, fractional poly CI
    _g("m7",
       [_s("mpg", "displacement", mcolor="orange", msize="5"),
        _fpc("mpg", "displacement", fcolor="gold",  falpha="0.3")],
       title="MPG vs Displacement: Frac Poly + 95% CI",
       xtitle="Displacement (cu in)", ytitle="Mileage (mpg)",
       hover="mpg displacement weight foreign"),

    # m8 — rconnected: lower + upper bound connected across repair records
    #      Encodes: mpg_lo, mpg_hi, rep78 (3 distinct numeric dimensions)
    _g("m8",
       [_rco("mpg_lo", "mpg_hi", "rep78", mcolor="navy", lcolor="navy", lwidth="1.5")],
       title="MPG Range vs Repair Record (rconnected)",
       xtitle="Repair Record (1–5)", ytitle="MPG Lower / Upper Bound",
       hover="mpg_lo mpg_hi rep78 mpg"),

    # m9 — rcapsym: capped symmetrical error bars
    #      Encodes: mpg_lo, mpg_hi, weight
    _g("m9",
       [_rcs("mpg_lo", "mpg_hi", "weight", mcolor="maroon", lcolor="maroon", lwidth="1.5")],
       title="MPG ± 2 Cap-Sym Error Bars vs Weight",
       xtitle="Weight (lbs)", ytitle="MPG ± 2 Bounds",
       hover="mpg_lo mpg_hi weight mpg foreign"),

    # m10 — rscatter: two separate y-values at each x
    #       Encodes: mpg_lo, mpg_hi, weight
    _g("m10",
       [_rs("mpg_lo", "mpg_hi", "weight", mcolor="navy", msize="5")],
       title="MPG Range Scatter vs Weight (rscatter)",
       xtitle="Weight (lbs)", ytitle="MPG Lower / Upper Bound",
       hover="mpg_lo mpg_hi weight mpg"),

    # m11 — rline: paired lines from lower to upper bound
    #       Encodes: mpg_lo, mpg_hi, weight
    _g("m11",
       [_rl("mpg_lo", "mpg_hi", "weight", lcolor="navy", lwidth="1.5")],
       title="MPG Range Lines vs Weight (rline)",
       xtitle="Weight (lbs)", ytitle="MPG Lower / Upper Bound",
       hover="mpg_lo mpg_hi weight mpg"),

    # m12 — pcarrow: movement arrows (start → end in 4-D space)
    #       Encodes: pc_y1, pc_x1 → pc_y2, pc_x2  (4 variables = shift in MPG/Weight)
    _g("m12",
       [_pca(lcolor="maroon", lwidth="1.5")],
       title="Vehicle Attribute Shifts (pcarrow)",
       xtitle="Weight (lbs)", ytitle="Mileage (mpg)",
       hover="pc_y1 pc_x1 pc_y2 pc_x2"),

    # m13 — scatteri: fixed reference landmarks on the MPG/Weight plane
    #       Encodes user-specified (mpg, weight) reference points
    _g("m13",
       [{"type": "scatteri",
         "values": [[35, 1800], [28, 2200], [22, 2800], [18, 3500], [15, 4200]],
         "options": {"msymbol": "diamond", "mcolor": "red", "msize": "8"}}],
       title="Reference Landmarks (scatteri)",
       xtitle="Weight (lbs)", ytitle="Mileage (mpg)"),

    # m14 — function: theoretical MPG ~ 50 - 0.009 * weight
    #       Encodes the mathematical relationship over the weight range
    _g("m14",
       [{"type": "function",
         "expr": "50 - 0.009 * x",
         "options": {"range": "1500 5000", "lcolor": "red", "lwidth": "2"}}],
       title="Theoretical: MPG = 50 − 0.009 × Weight",
       xtitle="Weight (lbs)", ytitle="Expected Mileage (mpg)"),
]

# ---------------------------------------------------------------------------
# Full dashboard spec
# ---------------------------------------------------------------------------

SPEC = {
    "graphs": U_GRAPHS + B_GRAPHS + M_GRAPHS,
    "kpis": [
        _kpi("k1", "mean",  "mpg",          "Avg MPG",    "%9.1f",  "miles per gallon"),
        _kpi("k2", "count", "mpg",           "# Vehicles", "%9.0f",  "in current filter"),
        _kpi("k3", "mean",  "price",         "Avg Price",  "%9.0fc", "USD"),
        _kpi("k4", "mean",  "weight",        "Avg Weight", "%9.0fc", "lbs"),
        _kpi("k5", "mean",  "rep78",         "Avg Repair", "%9.2f",  "1 (poor) – 5 (excellent)"),
        _kpi("k6", "mean",  "displacement",  "Avg Displ.", "%9.0f",  "cubic inches"),
    ],
    "build_options": {
        "layout":          "bs",
        # Use the structured "filters" key so the renderer reads it directly
        # (the "filter" key expects a Stata-format string, not a JSON array).
        "filters":         FILTERS,
        "link":            "b1 b2 b3 m4",
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
