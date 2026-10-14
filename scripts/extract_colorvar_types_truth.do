*! extract_colorvar_types_truth.do -- WP-31 section 15 (GAPS3 C8a): measure
*! which plot types twoway colours by colorvar(), which it drops it on
*! without a word, the multi-y refusal, how a line is coloured, and how
*! jitter() moves the markers of rscatter, rcapsym, pcscatter and pccapsym.
*! twoway only: the output is the same before and after dash changes.
*!
*! Output: test/fixtures/colorvar_types_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_colorvar_types_truth.do
*!
*! PROBES
*!   C_<type>  every type of test_twoway_option_parity.cscript's m6 list,
*!             `twoway <cmd>, colorvar(z)': rc, and per plot the view's
*!             .cvar (the serset column of the colour variable, . when
*!             none) and .hascolorvar; the distinct colours of the SVG with
*!             and without colorvar(); colorvar(nosuchvar) and
*!             colorvar(make) (a string) rc.
*!   T_<type>  `twoway <type> y1 y2 x, colorvar(z)' on the eight types
*!             twoway_yxview_parse.class:231-236 names, plus area (silent)
*!             and tsline: rc and the lines printed.
*!   L01       `twoway line mpg weight, colorvar(z) sort': distinct stroke
*!             colours of the plotted path segments.
*!   J_<type>  rscatter, rcapsym, pcscatter, pccapsym with jitter(5)
*!             jitterseed(1) against the same command without: marker
*!             count, how many moved, the largest move as a fraction of the
*!             unjittered markers' x and y spans, and whether the spines
*!             (lines) moved.
*!   PC_<type> pcspike, pcarrow, pcbarrow, pccapsym, rcap, rcapsym,
*!             dropline with colorvar(z): distinct stroke colours of the
*!             plot's lines (shafts, spines, caps, arrowhead strokes) and
*!             fill colours of its markers/head polygons.
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zc_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zc_bad' {
    display as error "extract_colorvar_types_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zc_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zc_rc' | _rc {
    local _zc_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_colorvar_types_truth.do: `_zc_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZC_REPO "`repo'"
global ZC_OUT "${ZC_REPO}/test/fixtures/colorvar_types_truth.json"

local work "`c(tmpdir)'dash_colorvar_types_probe"
capture mkdir "`work'"
global ZC_WORK "`work'"

if `"`c(python_exec)'"' == "" {
    display as error "extract_colorvar_types_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

quietly shell git -C "${ZC_REPO}" rev-parse HEAD > "${ZC_WORK}/git_head.txt"
global ZC_VERSION "`c(stata_version)'"
global ZC_BORN "`c(born_date)'"
global ZC_WHEN "`c(current_date)' `c(current_time)'"

* _zc_rec key: per plot 1..3 of graph c1, "cvar hascolorvar" into global
* ZC_V_<key> as "p1cvar p1has p2cvar p2has p3cvar p3has" (. when absent).
capture program drop _zc_rec
program define _zc_rec
    args key
    local out ""
    forvalues k = 1/3 {
        local isa "`.c1.plotregion1.plot`k'.isa'"
        if "`isa'" == "" {
            local out "`out' . ."
            continue
        }
        local c "`.c1.plotregion1.plot`k'.cvar'"
        local h "`.c1.plotregion1.plot`k'.hascolorvar.istrue'"
        if "`c'" == "" local c "."
        if "`h'" == "" local h "."
        local out "`out' `c' `h'"
    }
    global ZC_V_`key' "`out'"
    display as text "ZC `key':`out'"
end

sysuse auto, clear
keep if rep78 < .
sort weight
generate t = _n
tsset t
generate y = mpg
generate y2 = mpg + 5
generate y3 = mpg + 10
generate z = rep78
generate lo = mpg - 2
generate hi = mpg + 2
generate x2 = weight + 500
set scheme s2color

* C_<type>: the m6 list (test/test_twoway_option_parity.cscript).
local m6 `"scatter "scatter y t" line "line y t" connected "connected y t" scatteri "scatteri 100 480" area "area y t" bar "bar y t" spike "spike y t" dropline "dropline y t" dot "dot y t" rarea "rarea y y2 t" rbar "rbar y y2 t" rspike "rspike y y2 t" rcap "rcap y y2 t" rcapsym "rcapsym y y2 t" rscatter "rscatter y y2 t" rline "rline y y2 t" rconnected "rconnected y y2 t" pcspike "pcspike y t y2 t" pccapsym "pccapsym y t y2 t" pcarrow "pcarrow y t y2 t" pcbarrow "pcbarrow y t y2 t" pcscatter "pcscatter y t y2 t" pci "pci 100 480 110 490" pcarrowi "pcarrowi 100 480 110 490" tsline "tsline y" tsrline "tsrline y y2" mband "mband y t" mspline "mspline y t" lowess "lowess y t" lfit "lfit y t" qfit "qfit y t" fpfit "fpfit y t" lfitci "lfitci y t" qfitci "qfitci y t" fpfitci "fpfitci y t" lpoly "lpoly y t" lpolyci "lpolyci y t" kdensity "kdensity y" histogram "histogram t" function "function y = x, range(480 539)""'
local ckeys ""
while `"`m6'"' != "" {
    gettoken ty m6 : m6
    gettoken cmd m6 : m6
    local sep = cond(strpos(`"`cmd'"', ","), " ", ", ")
    capture noisily twoway `cmd' `sep' colorvar(z) name(c1, replace)
    global ZC_RC_`ty' = _rc
    if _rc == 0 {
        _zc_rec `ty'
        quietly graph export "${ZC_WORK}/cv_`ty'.svg", replace
        graph drop c1
    }
    else global ZC_V_`ty' ". . . . . ."
    capture noisily twoway `cmd' `sep' name(c1, replace)
    if _rc == 0 {
        quietly graph export "${ZC_WORK}/plain_`ty'.svg", replace
        graph drop c1
    }
    capture noisily twoway `cmd' `sep' colorvar(nosuchvar) name(c1, replace)
    global ZC_BAD_`ty' = _rc
    capture graph drop c1
    capture noisily twoway `cmd' `sep' colorvar(make) name(c1, replace)
    global ZC_STR_`ty' = _rc
    capture graph drop c1
    local ckeys "`ckeys' `ty'"
}
global ZC_CKEYS "`ckeys'"

* T_<type>: two y variables with colorvar().
local tkeys ""
foreach c in "scatter|scatter y y3 t" "line|line y y3 t" "connected|connected y y3 t" ///
    "bar|bar y y3 t" "spike|spike y y3 t" "dropline|dropline y y3 t" ///
    "dot|dot y y3 t" "tsline|tsline y y3" "area|area y y3 t" "scatter_one|scatter y t" {
    gettoken key cmd : c, parse("|")
    local cmd = substr(`"`cmd'"', 2, .)
    quietly log using "${ZC_WORK}/t_`key'.log", text replace name(zcref)
    capture noisily twoway `cmd', colorvar(z) name(c1, replace)
    local rc = _rc
    quietly log close zcref
    capture graph drop c1
    global ZC_TRC_`key' "`rc'"
    local tkeys "`tkeys' `key'"
}
global ZC_TKEYS "`tkeys'"

* L01: a line coloured along its length.
sysuse auto, clear
generate z = rep78
quietly twoway line mpg weight, colorvar(z) sort name(c1, replace)
quietly graph export "${ZC_WORK}/l01.svg", replace
graph drop c1

* J_<type>: jitter on the four range and pc marker types.
sysuse auto, clear
keep if rep78 < .
generate lo = mpg - 2
generate hi = mpg + 2
generate y2 = mpg + 5
generate x2 = weight + 500
local jkeys ""
foreach c in "rscatter|rscatter lo hi weight" "rcapsym|rcapsym lo hi weight" ///
    "pcscatter|pcscatter mpg weight y2 x2" "pccapsym|pccapsym mpg weight y2 x2" {
    gettoken key cmd : c, parse("|")
    local cmd = substr(`"`cmd'"', 2, .)
    quietly twoway `cmd', name(c1, replace)
    quietly graph export "${ZC_WORK}/j0_`key'.svg", replace
    graph drop c1
    quietly twoway `cmd', jitter(5) jitterseed(1) name(c1, replace)
    quietly graph export "${ZC_WORK}/j1_`key'.svg", replace
    graph drop c1
    local jkeys "`jkeys' `key'"
}
global ZC_JKEYS "`jkeys'"

python:
import json, math, os, re
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


work = G("ZC_WORK")
_HEX = re.compile(r"(?:stroke|fill):(#[0-9A-Fa-f]{6})")
_CIRCLE = re.compile(r"<circle\b([^>]*)/?>")
_LINE = re.compile(r"<line\b([^>]*)/?>")
_PATHUSE = re.compile(r"<(?:path|use)\b([^>]*)/?>")
_ATTR = re.compile(r'([\w:-]+)="([^"]*)"')
# Colours of the s2color chrome: canvas, regions, axes, grid, text.
_CHROME = {"#eaf2f3", "#ffffff", "#000000", "#dce7eb"}


def read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        txt = fh.read()
    os.remove(path)
    return txt


def style(a):
    out = {}
    for part in a.get("style", "").split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip()] = v.strip().lower()
    return out


def colours(txt):
    return sorted({h.lower() for h in _HEX.findall(txt)} - _CHROME)


def plot_lines(txt):
    out = []
    for m in _LINE.finditer(txt):
        a = dict(_ATTR.findall(m.group(1)))
        st = style(a)
        if st.get("stroke") in _CHROME or "stroke-dasharray" in st:
            continue
        out.append({"x1": float(a["x1"]), "y1": float(a["y1"]),
                    "x2": float(a["x2"]), "y2": float(a["y2"]),
                    "stroke": st.get("stroke"),
                    "round": a.get("stroke-linecap") == "round"})
    return out


def markers(txt):
    out = []
    for m in _CIRCLE.finditer(txt):
        a = dict(_ATTR.findall(m.group(1)))
        st = style(a)
        if "cx" not in a:
            continue
        out.append((float(a["cx"]), float(a["cy"]), st.get("fill"),
                    st.get("stroke")))
    return out


def plot_fills(txt):
    out = set()
    for m in list(_CIRCLE.finditer(txt)) + list(_PATHUSE.finditer(txt)):
        st = style(dict(_ATTR.findall(m.group(1))))
        f = st.get("fill")
        if f and f != "none" and f not in _CHROME:
            out.add(f)
    return sorted(out)


def nums(s):
    return [None if w == "." else float(w) for w in s.split()]


types = {}
for t in G("ZC_CKEYS").split():
    rc = int(G("ZC_RC_" + t))
    v = nums(G("ZC_V_" + t))
    plots = []
    for k in range(3):
        c, h = v[2 * k], v[2 * k + 1]
        if c is None and h is None:
            continue
        plots.append({"cvar": c, "hascolorvar": h})
    rec = {"rc": rc, "plots": plots,
           "bad_var_rc": int(G("ZC_BAD_" + t)),
           "string_var_rc": int(G("ZC_STR_" + t))}
    rec["coloured"] = bool(rc == 0 and any(p["cvar"] is not None
                                           for p in plots))
    pc = os.path.join(work, "cv_%s.svg" % t)
    pp = os.path.join(work, "plain_%s.svg" % t)
    if os.path.exists(pc):
        cv_txt = read(pc)
        rec["colours_with"] = colours(cv_txt)
        rec["line_strokes_with"] = sorted({d["stroke"] for d in plot_lines(cv_txt)})
        rec["head_strokes_with"] = sorted({d["stroke"] for d in plot_lines(cv_txt) if d["round"]})
        rec["marker_fills_with"] = plot_fills(cv_txt)
    if os.path.exists(pp):
        pl_txt = read(pp)
        rec["colours_without"] = colours(pl_txt)
        rec["line_strokes_without"] = sorted({d["stroke"] for d in plot_lines(pl_txt)})
    types[t] = rec

multi_y = {}
for k in G("ZC_TKEYS").split():
    p = os.path.join(work, "t_%s.log" % k)
    with open(p, encoding="utf-8", errors="replace") as fh:
        lines = [ln.rstrip() for ln in fh
                 if ln.strip() and not ln.lstrip().startswith((".", "> "))
                 and "log:" not in ln and "log type:" not in ln
                 and "opened on:" not in ln and "closed on:" not in ln
                 and "name:" not in ln and not ln.startswith("---")]
    os.remove(p)
    multi_y[k] = {"rc": int(G("ZC_TRC_" + k)), "lines": lines}

l01_txt = read(os.path.join(work, "l01.svg"))
l01_lines = plot_lines(l01_txt)
l01 = {"command": "twoway line mpg weight, colorvar(z) sort",
       "segments": len(l01_lines),
       "distinct_strokes": len({d["stroke"] for d in l01_lines}),
       "strokes": sorted({d["stroke"] for d in l01_lines})}

jitter = {}
for t in G("ZC_JKEYS").split():
    t0 = read(os.path.join(work, "j0_%s.svg" % t))
    t1 = read(os.path.join(work, "j1_%s.svg" % t))
    m0, m1 = markers(t0), markers(t1)
    xs = [m[0] for m in m0]
    ys = [m[1] for m in m0]
    xspan = max(xs) - min(xs)
    yspan = max(ys) - min(ys)
    n = min(len(m0), len(m1))
    dx = [abs(m1[i][0] - m0[i][0]) for i in range(n)]
    dy = [abs(m1[i][1] - m0[i][1]) for i in range(n)]
    moved = sum(1 for i in range(n) if dx[i] > 0.01 or dy[i] > 0.01)
    l0, l1 = plot_lines(t0), plot_lines(t1)
    same_lines = (len(l0) == len(l1) and all(
        abs(a["x1"] - b["x1"]) < 0.01 and abs(a["y1"] - b["y1"]) < 0.01
        and abs(a["x2"] - b["x2"]) < 0.01 and abs(a["y2"] - b["y2"]) < 0.01
        for a, b in zip(l0, l1)))
    jitter[t] = {"markers_without": len(m0), "markers_with": len(m1),
                 "moved": moved,
                 "max_dx_frac": round(max(dx) / xspan, 4) if xspan else None,
                 "max_dy_frac": round(max(dy) / yspan, 4) if yspan else None,
                 "lines": len(l0), "lines_unmoved": same_lines}

cv_silent = sorted(t for t, r in types.items()
                   if r["rc"] == 0 and not r["coloured"])
coloured = sorted(t for t, r in types.items() if r["coloured"])
out = {"types": types, "cv_silent": cv_silent, "coloured": coloured,
       "multi_y": multi_y, "line_L01": l01, "jitter": jitter}
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZC_VERSION"), "born_date": G("ZC_BORN"),
                "dash_commit": commit, "extracted": G("ZC_WHEN"),
                "source": "scripts/extract_colorvar_types_truth.do"}
with open(G("ZC_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZC_OUT"))
end
