#!/usr/bin/env python3
"""regen_comprehensive.py
Regenerate comprehensive_demo.html without Stata.

Uses a 30-observation sample matching the sysuse auto dataset structure,
with all variables needed by every plot type in the demo.

Run from the dash/ directory:
    /Users/billy/anaconda3/bin/python3 regen_comprehensive.py
"""

import json
import math
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from dash_render import DashRenderer

# ---------------------------------------------------------------------------
# 30-observation sample data — all auto dataset variables + derived columns
# ---------------------------------------------------------------------------

_VALS = [
    # mpg  weight  price   rep78  foreign  length  displacement  headroom  turn  trunk  mpg_lo  mpg_hi  pc_y1  pc_x1  pc_y2   pc_x2
    (22,   2930,   4099,   5,     0,       186,    121,          2.5,      43,   11,    20,     24,     22,    2930,  20,     2780),
    (17,   3350,   4749,   3,     0,       173,    258,          2.5,      40,   11,    15,     19,     17,    3350,  15,     3200),
    (22,   2640,   3799,   4,     0,       168,    121,          3.0,      35,   13,    20,     24,     22,    2640,  20,     2490),
    (20,   3250,   4816,   3,     0,       196,    196,          4.0,      40,   16,    18,     22,     20,    3250,  18,     3100),
    (15,   4080,   7827,   4,     0,       222,    305,          4.0,      43,   21,    13,     17,     15,    4080,  13,     3930),
    (18,   3670,   5788,   3,     0,       218,    231,          4.0,      41,   15,    16,     20,     18,    3670,  16,     3520),
    (26,   2230,   4453,   3,     0,       170,    151,          3.5,      40,   10,    24,     28,     26,    2230,  24,     2080),
    (20,   3280,   6900,   2,     0,       200,    250,          3.5,      42,   16,    18,     22,     20,    3280,  18,     3130),
    (16,   3609,   4890,   3,     0,       219,    307,          3.5,      44,   17,    14,     18,     16,    3609,  14,     3459),
    (19,   3302,   6295,   3,     0,       197,    250,          3.5,      43,   18,    17,     21,     19,    3302,  17,     3152),
    (14,   3900,   5705,   4,     0,       204,    350,          4.0,      43,   21,    12,     16,     14,    3900,  12,     3750),
    (14,   4330,   5172,   2,     0,       221,    304,          3.5,      48,   16,    12,     16,     14,    4330,  12,     4180),
    (29,   1800,   3895,   2,     0,       147,    97,           3.0,      33,   11,    27,     31,     29,    1800,  27,     1650),
    (16,   3820,   6165,   3,     0,       212,    307,          3.0,      43,   13,    14,     18,     16,    3820,  14,     3670),
    (17,   3850,   5898,   3,     0,       218,    302,          4.0,      43,   19,    15,     19,     17,    3850,  15,     3700),
    (21,   2750,   4425,   4,     1,       193,    146,          2.5,      40,   12,    19,     23,     21,    2750,  25,     3050),
    (30,   2120,   5079,   4,     1,       172,    107,          2.5,      36,   8,     28,     32,     30,    2120,  34,     2420),
    (35,   2020,   4296,   5,     1,       165,    90,           2.0,      32,   8,     33,     37,     35,    2020,  39,     2320),
    (22,   2280,   5798,   4,     1,       170,    120,          3.0,      37,   8,     20,     24,     22,    2280,  26,     2580),
    (31,   2050,   6479,   5,     1,       164,    91,           3.5,      36,   8,     29,     33,     31,    2050,  35,     2350),
    (35,   1800,   3748,   5,     1,       157,    61,           2.0,      30,   8,     33,     37,     35,    1800,  39,     2100),
    (32,   1760,   3995,   5,     1,       154,    61,           2.5,      32,   6,     30,     34,     32,    1760,  36,     2060),
    (24,   2040,   4697,   5,     1,       165,    98,           3.0,      34,   8,     22,     26,     24,    2040,  28,     2340),
    (28,   1985,   5886,   5,     1,       163,    91,           3.5,      36,   8,     26,     30,     28,    1985,  32,     2285),
    (25,   1975,   4099,   4,     1,       166,    97,           2.5,      35,   8,     23,     27,     25,    1975,  29,     2275),
    (26,   1990,   8129,   4,     1,       163,    97,           2.5,      34,   8,     24,     28,     26,    1990,  30,     2290),
    (24,   2025,   7140,   5,     1,       165,    97,           3.0,      35,   8,     22,     26,     24,    2025,  28,     2325),
    (23,   2200,   9690,   5,     1,       172,    120,          2.5,      36,   8,     21,     25,     23,    2200,  27,     2500),
    (17,   2750,   6295,   3,     1,       180,    134,          4.0,      40,   10,    15,     19,     17,    2750,  21,     3050),
    (21,   2650,   5189,   4,     1,       176,    120,          3.5,      38,   8,     19,     23,     21,    2650,  25,     2950),
]

_COLS = ["mpg","weight","price","rep78","foreign","length","displacement",
         "headroom","turn","trunk","mpg_lo","mpg_hi","pc_y1","pc_x1","pc_y2","pc_x2"]

SAMPLE_DATA = {
    "StataJSON": {
        "variableNames": _COLS,
        "variableLabels": {
            "mpg":          "Mileage (mpg)",
            "weight":       "Weight (lbs.)",
            "price":        "Price",
            "rep78":        "Repair record 1978",
            "foreign":      "Car type",
            "length":       "Length (in.)",
            "displacement": "Displacement (cu. in.)",
            "headroom":     "Headroom (in.)",
            "turn":         "Turn circle (ft.)",
            "trunk":        "Trunk space (cu. ft.)",
            "mpg_lo":       "MPG lower bound",
            "mpg_hi":       "MPG upper bound",
            "pc_y1":        "Arrow start Y",
            "pc_x1":        "Arrow start X",
            "pc_y2":        "Arrow end Y",
            "pc_x2":        "Arrow end X",
        },
        "valueLabels":    {"foreign": {"0": "Domestic", "1": "Foreign"}},
        "valueLabelNames": {"foreign": "origin"},
        "variableTypeIsString": {c: False for c in _COLS},
        "values": [dict(zip(_COLS, row)) for row in _VALS],
    }
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def render(spec: dict, out_name: str) -> None:
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
        print(f"  {out_name}  ({os.path.getsize(dest):,} bytes)")
    finally:
        for p in (spec_path, data_path, out_path):
            try:
                os.unlink(p)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Graph spec helpers
# ---------------------------------------------------------------------------

def _g(name, plots, **gopts):
    return {"plots": plots, "graph_options": {"name": name, **gopts},
            "if_expr": "", "in_expr": ""}

def _p(ptype, **kw):
    _TOP_KEYS = ("yvar","xvar","yvar1","yvar2","var",
                 "y1var","x1var","y2var","x2var")
    opts = {k: v for k, v in kw.items() if k not in _TOP_KEYS}
    base = {k: v for k, v in kw.items() if k in _TOP_KEYS}
    return {"type": ptype, **base, "options": opts}

def _s(yvar, xvar, **o):  return _p("scatter",  yvar=yvar, xvar=xvar, **o)
def _lf(yvar, xvar, **o): return _p("lfit",     yvar=yvar, xvar=xvar, **o)
def _qf(yvar, xvar, **o): return _p("qfit",     yvar=yvar, xvar=xvar, **o)
def _lw(yvar, xvar, **o): return _p("lowess",   yvar=yvar, xvar=xvar, **o)
def _lp(yvar, xvar, **o): return _p("lpoly",    yvar=yvar, xvar=xvar, **o)
def _ms(yvar, xvar, **o): return _p("mspline",  yvar=yvar, xvar=xvar, **o)
def _mb(yvar, xvar, **o): return _p("mband",    yvar=yvar, xvar=xvar, **o)
def _hi(yvar, **o):       return _p("histogram",yvar=yvar, **o)
def _kd(yvar, **o):       return _p("kdensity", yvar=yvar, **o)
def _li(yvar, xvar, **o): return _p("line",     yvar=yvar, xvar=xvar, **o)
def _co(yvar, xvar, **o): return _p("connected",yvar=yvar, xvar=xvar, **o)
def _ar(yvar, xvar, **o): return _p("area",     yvar=yvar, xvar=xvar, **o)
def _ba(yvar, xvar, **o): return _p("bar",      yvar=yvar, xvar=xvar, **o)
def _sp(yvar, xvar, **o): return _p("spike",    yvar=yvar, xvar=xvar, **o)
def _dl(yvar, xvar, **o): return _p("dropline", yvar=yvar, xvar=xvar, **o)
def _do(yvar, xvar, **o): return _p("dot",      yvar=yvar, xvar=xvar, **o)

def _lfc(yvar, xvar, **o):  return _p("lfitci",   yvar=yvar, xvar=xvar, **o)
def _qfc(yvar, xvar, **o):  return _p("qfitci",   yvar=yvar, xvar=xvar, **o)
def _lpc(yvar, xvar, **o):  return _p("lpolyci",  yvar=yvar, xvar=xvar, **o)
def _fpc(yvar, xvar, **o):  return _p("fpfitci",  yvar=yvar, xvar=xvar, **o)

def _ra(y1,y2,xvar,**o):  return _p("rarea",      yvar1=y1, yvar2=y2, xvar=xvar, **o)
def _rb(y1,y2,xvar,**o):  return _p("rbar",       yvar1=y1, yvar2=y2, xvar=xvar, **o)
def _rc(y1,y2,xvar,**o):  return _p("rcap",       yvar1=y1, yvar2=y2, xvar=xvar, **o)
def _rsp(y1,y2,xvar,**o): return _p("rspike",     yvar1=y1, yvar2=y2, xvar=xvar, **o)
def _rl(y1,y2,xvar,**o):  return _p("rline",      yvar1=y1, yvar2=y2, xvar=xvar, **o)
def _rco(y1,y2,xvar,**o): return _p("rconnected", yvar1=y1, yvar2=y2, xvar=xvar, **o)
def _rcs(y1,y2,xvar,**o): return _p("rcapsym",    yvar1=y1, yvar2=y2, xvar=xvar, **o)
def _rs(y1,y2,xvar,**o):  return _p("rscatter",   yvar1=y1, yvar2=y2, xvar=xvar, **o)

def _pc_arrow(**o): return _p("pcarrow",
                               y1var="pc_y1", x1var="pc_x1",
                               y2var="pc_y2", x2var="pc_x2", **o)

def _kpi(name, stat, var, title, fmt="%9.1f", subtitle="", update="filter"):
    return {"name":name,"stat":stat,"var":var,"title":title,
            "fmt":fmt,"subtitle":subtitle,"update":update}

FILTER_JSON = json.dumps([
    {"varname": "foreign", "type": "dropdown", "label": "Car Origin",  "exclude": []},
    {"varname": "mpg",     "type": "range",    "label": "MPG Range",   "exclude": []},
    {"varname": "weight",  "type": "slider",   "label": "Weight >=",   "exclude": []},
])

TABS_STR = (
    "univariate: u1 u2 u3 u4 u5"
    " / bivariate: b1 b2 b3 b4 b5 b6 b7 b8 b9 b10 b11 b12 b13 b14 b15 b16 b17"
    " / multivariate: m1 m2 m3 m4 m5 m6 m7 m8 m9 m10 m11 m12 m13"
)

# ---- Univariate graphs ----
U_GRAPHS = [
    _g("u1", [_hi("mpg")],
       title="MPG Distribution", xtitle="Mileage (mpg)"),
    _g("u2", [_kd("mpg")],
       title="MPG Kernel Density", xtitle="Mileage (mpg)"),
    _g("u3", [_hi("mpg", fcolor="ltblue", falpha="0.4"),
              _kd("mpg", lcolor="maroon", lwidth="2")],
       title="MPG: Histogram + Density Overlay", xtitle="Mileage (mpg)"),
    _g("u4", [_hi("price")],
       title="Price Distribution", xtitle="Price (USD)"),
    _g("u5", [_hi("mpg")],
       title="MPG by Car Origin (by)", xtitle="Mileage (mpg)",
       **{"by": "foreign"}),
]

# ---- Bivariate graphs ----
B_GRAPHS = [
    _g("b1",  [_s("mpg","weight",mcolor="navy",   msize="5"),
               _lf("mpg","weight",lcolor="maroon",lwidth="2")],
       title="Scatter + OLS", xtitle="Weight", ytitle="MPG"),
    _g("b2",  [_s("mpg","weight",mcolor="forest_green",msize="5"),
               _lw("mpg","weight",lcolor="orange",lwidth="2")],
       title="Scatter + Lowess", xtitle="Weight", ytitle="MPG"),
    _g("b3",  [_s("mpg","weight",mcolor="purple",msize="5"),
               _qf("mpg","weight",lcolor="teal",lwidth="2")],
       title="Quadratic Fit", xtitle="Weight", ytitle="MPG"),
    _g("b4",  [_s("mpg","weight",mcolor="maroon",msize="5"),
               _lp("mpg","weight",lcolor="forest_green",lwidth="2")],
       title="Local Polynomial", xtitle="Weight", ytitle="MPG"),
    _g("b5",  [_s("mpg","weight",mcolor="orange",msize="5"),
               _ms("mpg","weight",lcolor="navy",lwidth="2")],
       title="Mean Spline", xtitle="Weight", ytitle="MPG"),
    _g("b6",  [_s("mpg","weight",mcolor="navy",msize="5"),
               _mb("mpg","weight",fcolor="ltblue",falpha="0.3")],
       title="Mean Band", xtitle="Weight", ytitle="MPG"),
    _g("b7",  [_li("mpg","weight",lcolor="navy",lwidth="2")],
       title="Line", xtitle="Weight", ytitle="MPG"),
    _g("b8",  [_co("mpg","rep78",mcolor="maroon",lcolor="maroon")],
       title="Connected", xtitle="Repair Record", ytitle="MPG"),
    _g("b9",  [_ar("mpg","weight",fcolor="ltblue",falpha="0.5")],
       title="Area", xtitle="Weight", ytitle="MPG"),
    _g("b10", [_ba("mpg","rep78")],
       title="Bar", xtitle="Repair Record", ytitle="MPG"),
    _g("b11", [_sp("mpg","weight",lcolor="navy")],
       title="Spike", xtitle="Weight", ytitle="MPG"),
    _g("b12", [_dl("mpg","weight",mcolor="maroon",lcolor="maroon")],
       title="Dropline", xtitle="Weight", ytitle="MPG"),
    _g("b13", [_do("mpg","rep78",mcolor="navy")],
       title="Dot", xtitle="Repair Record", ytitle="MPG"),
    _g("b14", [_ra("mpg_lo","mpg_hi","weight",fcolor="ltblue",falpha="0.4",lwidth="0")],
       title="rarea", xtitle="Weight", ytitle="MPG +/- 2"),
    _g("b15", [_rb("mpg_lo","mpg_hi","weight",fcolor="maroon")],
       title="rbar", xtitle="Weight", ytitle="MPG +/- 2"),
    _g("b16", [_rc("mpg_lo","mpg_hi","weight",lcolor="navy")],
       title="rcap", xtitle="Weight", ytitle="MPG +/- 2"),
    _g("b17", [_rsp("mpg_lo","mpg_hi","weight",lcolor="forest_green")],
       title="rspike", xtitle="Weight", ytitle="MPG +/- 2"),
]

# ---- Multivariate graphs ----
M_GRAPHS = [
    _g("m1",  [_s("mpg","weight",mcolor="navy",msize="5")],
       title="MPG vs Weight by Origin (by)", xtitle="Weight", ytitle="MPG",
       **{"by": "foreign"}),
    _g("m2",  [_s("mpg","weight",mcolor="navy",msize="5"),
               _lfc("mpg","weight",fcolor="ltblue",falpha="0.3")],
       title="OLS + 95% CI (lfitci)", xtitle="Weight", ytitle="MPG"),
    _g("m3",  [_s("mpg","weight",mcolor="purple",msize="5"),
               _qfc("mpg","weight",fcolor="lavender",falpha="0.3")],
       title="Quadratic + 95% CI (qfitci)", xtitle="Weight", ytitle="MPG"),
    _g("m4",  [_s("mpg","weight",mcolor="forest_green",msize="5"),
               _lpc("mpg","weight",fcolor="lime",falpha="0.3")],
       title="Local Poly + 95% CI (lpolyci)", xtitle="Weight", ytitle="MPG"),
    _g("m5",  [_s("mpg","weight",mcolor="orange",msize="5"),
               _fpc("mpg","weight",fcolor="gold",falpha="0.3")],
       title="Frac Poly + CI (fpfitci)", xtitle="Weight", ytitle="MPG"),
    _g("m6",  [
        {"type":"scatter","yvar":"mpg","xvar":"weight",
         "if_expr":"rep78==1","options":{"mcolor":"navy","msymbol":"circle","msize":"5"}},
        {"type":"scatter","yvar":"mpg","xvar":"weight",
         "if_expr":"rep78==2","options":{"mcolor":"maroon","msymbol":"square","msize":"5"}},
        {"type":"scatter","yvar":"mpg","xvar":"weight",
         "if_expr":"rep78==3","options":{"mcolor":"forest_green","msymbol":"triangle","msize":"5"}},
        {"type":"scatter","yvar":"mpg","xvar":"weight",
         "if_expr":"rep78==4","options":{"mcolor":"orange","msymbol":"diamond","msize":"5"}},
        {"type":"scatter","yvar":"mpg","xvar":"weight",
         "if_expr":"rep78==5","options":{"mcolor":"purple","msymbol":"inverted_triangle","msize":"5"}},
       ],
       title="5 Repair Record Groups", xtitle="Weight", ytitle="MPG"),
    _g("m7",  [_rco("mpg_lo","mpg_hi","weight",mcolor="maroon",lcolor="maroon")],
       title="rconnected", xtitle="Weight", ytitle="MPG +/- 2"),
    _g("m8",  [_rl("mpg_lo","mpg_hi","weight",lcolor="navy")],
       title="rline", xtitle="Weight", ytitle="MPG +/- 2"),
    _g("m9",  [_rcs("mpg_lo","mpg_hi","weight",mcolor="maroon",lcolor="maroon")],
       title="rcapsym", xtitle="Weight", ytitle="MPG +/- 2"),
    _g("m10", [_rs("mpg_lo","mpg_hi","weight",mcolor="navy")],
       title="rscatter", xtitle="Weight", ytitle="MPG +/- 2"),
    _g("m11", [_pc_arrow()],
       title="Paired Coord. Arrows (pcarrow)", xtitle="Weight", ytitle="MPG"),
    _g("m12", [{"type":"scatteri",
                "options":{"coords":"35 1800 28 2100 22 2800 18 3500 15 4200",
                           "msymbol":"diamond","mcolor":"red","msize":"8"}}],
       title="Scatter Immediate (scatteri)"),
    _g("m13", [{"type":"function",
                "options":{"expr":"50 - 0.009 * x","xmin":"1500","xmax":"5000",
                           "lcolor":"red","lwidth":"2"}}],
       title="Function: MPG ~ 50 - 0.009*Weight"),
]

# ---- Full spec ----
SPEC = {
    "graphs": U_GRAPHS + B_GRAPHS + M_GRAPHS,
    "kpis": [
        _kpi("k1","mean",  "mpg",          "Avg MPG",    "%9.1f",  "miles / gallon"),
        _kpi("k2","count", "mpg",           "# Cars",     "%9.0f",  "in current filter"),
        _kpi("k3","mean",  "price",         "Avg Price",  "%9.0fc", "USD"),
        _kpi("k4","mean",  "weight",        "Avg Weight", "%9.0fc", "lbs"),
        _kpi("k5","mean",  "rep78",         "Avg Repair", "%9.2f",  "scale 1-5"),
        _kpi("k6","mean",  "displacement",  "Avg Displ.", "%9.0f",  "cubic inches"),
    ],
    "build_options": {
        "layout":          "bs",
        "link":            "b1 b2 b3 m6",
        "filter":          FILTER_JSON,
        "theme":           "default",
        "title":           "Stata dash — Comprehensive Feature Demo",
        "subtitle":        "Auto Dataset · All Plot Types · Filters · Linked Brushing · Tabs",
        "registry":        "",
        "tabs":            TABS_STR,
        "filter_position": "left",
    },
}

if __name__ == "__main__":
    print("Generating comprehensive demo dashboard...")
    render(SPEC, "comprehensive_demo.html")
    print("Done.")
