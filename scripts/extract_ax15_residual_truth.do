*! extract_ax15_residual_truth.do
*! WP-44 AX-15 residual: ground truth for an axis whose layers reach past
*! Stata's dates and for the hexadecimal and IEEE-byte formats that reach
*! an axis or a colour key by another route than an axis's format(): a
*! variable's own display format, xvarformat()/yvarformat(), and
*! zlabel(, format()), for test/fixtures/ax15_residual_truth.json.
*!
*! WHY THIS EXISTS
*!
*! dash ticked a date axis past Stata's dates by natscale over its
*! numbers and wrote these formats in %9.0g.  This script records what
*! twoway draws, and what Stata's own _tsnatscale answers past its dates,
*! so the tests compare with twoway and never with a guess.
*!
*! Output: test/fixtures/ax15_residual_truth.json
*!
*! Run with:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_ax15_residual_truth.do
*!
*! METHOD
*!
*! `_ar_ts key lo hi n unit' records _tsnatscale's r(min), r(max),
*! r(delta) and r(list).  `_ar_run key data prep cmd' loads the data set,
*! runs prep (a format or generate), runs cmd under the stcolor scheme
*! for the session only and exports the graph to SVG.  The trailing
*! python: block reads files only: each key's rc and, through
*! scripts/svg_truth.py, the texts below the plot region (x labels), left
*! of it (y labels) and right of it (a colour key's labels and title),
*! in drawing order.  scatteri literals are stored as floats, so the
*! probes use values a float holds exactly (100000000, not 99999999).
*! ---------------------------------------------------------------------------

clear all
set graphics off
set more off
set linesize 255
version 19

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_ar_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_ar_bad' {
    display as error "extract_ax15_residual_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _ar_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_ar_rc' | _rc {
    local _ar_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_ax15_residual_truth.do: `_ar_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global AR_REPO "`repo'"
global AR_OUT "${AR_REPO}/test/fixtures/ax15_residual_truth.json"

local work "`c(tmpdir)'dash_ax15_residual_probe"
capture mkdir "`work'"
global AR_WORK "`work'"

quietly shell git -C "${AR_REPO}" rev-parse HEAD > "${AR_WORK}/git_head.txt"
global AR_VERSION "`c(stata_version)'"
global AR_BORN "`c(born_date)'"
global AR_WHEN "`c(current_date)' `c(current_time)'"

capture program drop _ar_ts
program define _ar_ts
    args key lo hi n unit
    capture _tsnatscale `lo' `hi' `n', `unit'
    global AR_TR_`key' "`=_rc'"
    global AR_TA_`key' "`lo' `hi' `n' `unit'"
    global AR_TV_`key' "`=r(min)' `=r(max)' `=r(delta)'"
    global AR_TL_`key' "`r(list)'"
    global AR_TKEYS "${AR_TKEYS} `key'"
end

capture program drop _ar_run
program define _ar_run
    args key data prep cmd
    sysuse `data', clear
    `prep'
    set scheme stcolor
    capture graph drop u15r
    capture noisily `macval(cmd)' name(u15r, replace)
    local rc = _rc
    global AR_R_`key' "`rc'"
    global AR_C_`key' `"`macval(cmd)'"'
    global AR_P_`key' `"`prep'"'
    global AR_D_`key' "`data'"
    global AR_KEYS "${AR_KEYS} `key'"
    if !`rc' {
        quietly graph export "${AR_WORK}/`key'.svg", replace
    }
end

global AR_TKEYS ""
global AR_KEYS ""

* _tsnatscale past Stata's dates (and one range inside them).
_ar_ts d_hi8      14977 100000000 5 daily
_ar_ts d_hi8_n8   14977 100000000 8 daily
_ar_ts d_hi9      14977 1000000000 5 daily
_ar_ts d_lo       -1500000 15340 5 daily
_ar_ts d_hi10000  14977 2936550 5 daily
_ar_ts d_inside   14977 15340 5 daily
_ar_ts m_lo       -6000 503 5 monthly
_ar_ts y_lo       -500 2005 5 yearly
_ar_ts y_lo_da    -500 2001 5 yearly
_ar_ts q_hi       164 40000 5 quarterly

* twoway's axes past Stata's dates.
_ar_run past_hi8 sp500 "" "twoway (line close date) (scatteri 1300 100000000),"
_ar_run past_hi8_n8 sp500 "" "twoway (line close date) (scatteri 1300 100000000), xlabel(#8)"
_ar_run past_lo sp500 "" "twoway (line close date) (scatteri 1300 -1500000),"
_ar_run past_hi10000 sp500 "" "twoway (line close date) (scatteri 1300 2936550),"
_ar_run past_y sp500 "" "twoway (line date close) (scatteri 100000000 1300),"
_ar_run past_m sp500 "generate m = mofd(date) + mod(_n, 3)" "twoway (line close m, xvarformat(%tm)) (scatteri 1300 -6000),"
_ar_run past_ty sp500 "generate yr = 2001 + mod(_n, 5)" "twoway (line close yr, xvarformat(%ty)) (scatteri 1300 -500),"

* The dump formats by the other routes.
_ar_run fmt_var21x auto "format weight %21x" "scatter mpg weight,"
_ar_run fmt_xvar21x auto "" "scatter mpg weight, xvarformat(%21x)"
_ar_run fmt_yvar16H auto "" "scatter mpg weight, yvarformat(%16H)"
_ar_run fmt_var8H auto "format mpg %8H" "scatter mpg weight,"
_ar_run fmt_var16L auto "format mpg %16L" "scatter mpg weight,"
_ar_run fmt_xvarl21x auto "" "scatter mpg weight, xvarformat(%-21x)"
_ar_run fmt_xvar12s auto "" "scatter mpg weight, xvarformat(%12s)"
_ar_run key_cv12s auto "" "scatter mpg weight, colorvar(price) zlabel(, format(%12s))"
_ar_run key_cv8L auto "" "scatter mpg weight, colorvar(price) zlabel(, format(%8L))"
_ar_run key_z21x sandstone "" "twoway contour depth northing easting, zlabel(, format(%21x))"
_ar_run key_z16H sandstone "" "twoway contour depth northing easting, zlabel(, format(%16H))"
_ar_run key_var21x sandstone "format depth %21x" "twoway contour depth northing easting,"
_ar_run key_cv21x auto "" "scatter mpg weight, colorvar(price) zlabel(, format(%21x))"
_ar_run key_cvvar21x auto "format price %21x" "scatter mpg weight, colorvar(price)"


python:
import json, os, sys
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


sys.path.insert(0, os.path.join(G("AR_REPO"), "scripts"))
import svg_truth

work = G("AR_WORK")


def num(s):
    try:
        v = float(s)
    except ValueError:
        return None
    return v if abs(v) < 8.9e307 else None


def texts(key):
    doc = svg_truth.svg_document(os.path.join(work, key + ".svg"))
    pr = doc["plotregion"]
    t = [x for x in doc["texts"] if x["x"] is not None and x["y"] is not None]
    return {
        "x": [x["text"] for x in t if x["y"] > pr["bottom"]
              and x["rotate"] is None],
        "y": [x["text"] for x in t if x["x"] < pr["left"]],
        "right": [x["text"] for x in t if x["x"] > pr["right"]],
    }


out = {"tsnatscale": {}, "graphs": {}}
for key in G("AR_TKEYS").split():
    lo, hi, n, unit = G("AR_TA_" + key).split()
    mn, mx, de = G("AR_TV_" + key).split()
    out["tsnatscale"][key] = {
        "lo": float(lo), "hi": float(hi), "n": int(n), "unit": unit,
        "rc": int(G("AR_TR_" + key)), "min": num(mn), "max": num(mx),
        "delta": num(de),
        "list": [float(v) for v in G("AR_TL_" + key).split()]}
for key in G("AR_KEYS").split():
    rc = int(G("AR_R_" + key))
    row = {"rc": rc, "command": G("AR_C_" + key), "prep": G("AR_P_" + key),
           "data": G("AR_D_" + key)}
    if rc == 0:
        row.update(texts(key))
        os.remove(os.path.join(work, key + ".svg"))
    out["graphs"][key] = row

try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("AR_VERSION"), "born_date": G("AR_BORN"),
                "dash_commit": commit, "extracted": G("AR_WHEN"),
                "scheme": "stcolor",
                "source": "scripts/extract_ax15_residual_truth.do"}
with open(G("AR_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True, ensure_ascii=False)
    fh.write("\n")
print("wrote", G("AR_OUT"))
end
