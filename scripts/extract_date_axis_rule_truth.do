*! extract_date_axis_rule_truth.do
*! WP-44 section 44-04 (AX-18, DG-6, DG-4): ground truth for how twoway
*! labels an axis whose first layer is a fit, an estimate or an immediate
*! type on a date variable, how it draws a log scale on a date axis, how
*! it ticks and labels a %tC axis, and which parenthesised dates holding
*! blanks it reads in tlabel(), tline(), tscale(range()) and ttext(), for
*! test/fixtures/date_axis_rule_truth.json.
*!
*! WHY THIS EXISTS
*!
*! dash kept a date axis where twoway labels the variable's numbers,
*! dropped xscale(log) on a date axis, placed %tC ticks in leap-second
*! corrected time and refused (1 jan 2001).  This script records what
*! twoway draws for each, so the tests compare with twoway and never
*! with a guess.
*!
*! Output: test/fixtures/date_axis_rule_truth.json
*!
*! Run with:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_date_axis_rule_truth.do
*!
*! METHOD
*!
*! `_dr_run key cmd' runs cmd (on the data in memory) under a text log,
*! records the plot region's x and y scale (curmin, curmax; and the
*! second plot region's where there is one) and exports the drawn graph
*! to SVG.  The trailing python: block reads files only (never calls
*! Stata): each key's rc, its log lines, and per axis the tick pixels and
*! label texts through scripts/svg_truth.py's svg_axis_reading, the
*! vertical lines and every text.
*! ---------------------------------------------------------------------------

clear all
set graphics off
set more off
set linesize 255
version 19

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_dr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_dr_bad' {
    display as error "extract_date_axis_rule_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _dr_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_dr_rc' | _rc {
    local _dr_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_date_axis_rule_truth.do: `_dr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global DR_REPO "`repo'"
global DR_OUT "${DR_REPO}/test/fixtures/date_axis_rule_truth.json"

* A work directory of this run's own: a tempfile's name plus a suffix.
tempfile drwork
local work "`drwork'_dr"
capture mkdir "`work'"
if _rc {
    display as error "extract_date_axis_rule_truth.do: cannot make the work directory `work'"
    exit 9
}
global DR_WORK "`work'"

quietly shell git -C "${DR_REPO}" rev-parse HEAD > "${DR_WORK}/git_head.txt"
global DR_VERSION "`c(stata_version)'"
global DR_BORN "`c(born_date)'"
global DR_WHEN "`c(current_date)' `c(current_time)'"

capture program drop _dr_run
program define _dr_run
    args key cmd
    global DR_N = ${DR_N} + 1
    local i ${DR_N}
    set scheme s2color
    capture graph drop g
    capture log close drl
    quietly log using "${DR_WORK}/r_`i'.log", text replace name(drl)
    capture noisily `macval(cmd)' name(g, replace)
    local rc = _rc
    quietly log close drl
    global DR_K`i' "`key'"
    global DR_R`i' "`rc'"
    global DR_C`i' `"`macval(cmd)'"'
    global DR_S`i' ""
    if !`rc' {
        local s "`.g.plotregion1.xscale.curmin' `.g.plotregion1.xscale.curmax'"
        local s "`s' `.g.plotregion1.yscale.curmin' `.g.plotregion1.yscale.curmax'"
        local x2 ""
        local y2 ""
        capture local x2 "`.g.plotregion2.xscale.curmin' `.g.plotregion2.xscale.curmax'"
        capture local y2 "`.g.plotregion2.yscale.curmin' `.g.plotregion2.yscale.curmax'"
        global DR_S`i' "`s'|`x2'|`y2'"
        quietly graph export "${DR_WORK}/g`i'.svg", replace name(g)
    }
    capture graph drop g
end

global DR_N 0

* ---- ax18.first_<type>: which first layers label a date axis with numbers.
sysuse sp500, clear
foreach t in lfit qfit lfitci qfitci lpoly lpolyci fpfit fpfitci lowess mspline mband {
    _dr_run ax18.first_`t' `"twoway (`t' close date) (scatter close date),"'
}
foreach t in kdensity histogram {
    _dr_run ax18.first_`t' `"twoway (`t' date) (scatter close date),"'
}
_dr_run ax18.first_scatteri `"twoway (scatteri 1300 15400) (scatter close date),"'
_dr_run ax18.first_pci `"twoway (pci 1300 15200 1400 15300) (scatter close date),"'
_dr_run ax18.first_pcarrowi `"twoway (pcarrowi 1300 15200 1400 15300) (scatter close date),"'
_dr_run ax18.first_function `"twoway (function y = 1300, range(15000 15400)) (scatter close date),"'
_dr_run ax18.first_function_rangevar `"twoway (function y = 1300, range(date)) (scatter close date),"'
_dr_run ax18.scatter_first `"twoway (scatter close date) (lfit close date),"'
_dr_run ax18.line_first `"twoway (line close date) (lfit close date),"'
_dr_run ax18.lfit_range `"twoway (lfit close date, range(14900 15400)) (scatter close date),"'
_dr_run ax18.kdensity_alone `"twoway kdensity date,"'
_dr_run ax18.lfit_alone `"twoway lfit close date,"'
_dr_run ax18.y2_first `"twoway (scatter close date) (lfit open date, xaxis(2)),"'
_dr_run ax18.ygrp_lfit_second `"twoway (scatter close date) (lfit open date, yaxis(2)),"'
_dr_run ax18.ygrp_lfit_first `"twoway (lfit close date) (scatter open date, yaxis(2)),"'
_dr_run ax18.mixed_lfit_first `"twoway (lfit close date) (scatter close change),"'
_dr_run ax18.hz `"twoway kdensity date, horizontal"'
_dr_run ax18.y_lfit `"twoway (lfit date close) (scatter date close),"'
_dr_run ax18.y_scatter `"twoway (scatter date close) (lfit date close),"'

* ---- ax18.log_<k>: log scales on date axes.
_dr_run ax18.log_x_td `"twoway line close date, xscale(log)"'
_dr_run ax18.log_y_td `"twoway scatter date close, yscale(log)"'
_dr_run ax18.log_x4_td `"twoway line close date, xscale(log) xlabel(#4)"'
gen int m = mofd(date)
format m %tm
_dr_run ax18.log_x_tm `"twoway line close m, xscale(log)"'
_dr_run ax18.log_y_tm `"twoway scatter m close, yscale(log)"'
_dr_run ax18.log_x4_tm `"twoway line close m, xscale(log) xlabel(#4)"'

* ---- dg4.*: parenthesised dates holding blanks, on line close date.
_dr_run dg4.DT04 `"twoway line close date, tlabel((1 jan 2001) (1 jul 2001))"'
_dr_run dg4.DT05 `"twoway line close date, tlabel(01jan2001 (1 jul 2001))"'
_dr_run dg4.DT09 `"twoway line close date, tline((15 jun 2001))"'
_dr_run dg4.DT20 `"twoway line close date, tscale(range((1 dec 2000) (31 jan 2002)))"'
_dr_run dg4.DT06 `"twoway line close date, tlabel((july 1, 2001))"'
_dr_run dg4.ttext `"twoway line close date, ttext(1300 (15 jun 2001) "x")"'
_dr_run dg4.plain `"twoway line close date,"'

* ---- dg6.*: %tc against %tC.
clear
set obs 30
gen double t = tc(01jan2001 00:00:00) + (_n - 1) * 86400000
gen double tC = Cofc(t)
format t %tc
format tC %tC
gen y = _n
_dr_run dg6.T04 `"twoway scatter y t,"'
_dr_run dg6.T05 `"twoway scatter y tC,"'
clear
set obs 30
gen double t = tc(31dec2016 23:58:00) + (_n - 1) * 10000
gen double tC = Cofc(t)
format t %tc
format tC %tC
gen y = _n
_dr_run dg6.tc_2016 `"twoway scatter y t,"'
_dr_run dg6.tC_2016 `"twoway scatter y tC,"'

python:
import json, os, sys
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


sys.path.insert(0, os.path.join(G("DR_REPO"), "scripts"))
import svg_truth

work = G("DR_WORK")


def logged(key):
    with open(os.path.join(work, "r_" + key + ".log"), encoding="utf-8") as fh:
        lines = [ln.rstrip() for ln in fh]
    return [" ".join(ln.split()) for ln in lines
            if ln.strip() and not ln.startswith(".")
            and not ln.startswith(">")
            and not ln.lstrip().startswith(("name:", "log:", "log type:",
                                             "opened on:", "closed on:"))
            and not set(ln.strip()) <= set("-")]


def num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def scales(s):
    parts = (s or "").split("|")
    out = {}
    first = parts[0].split() if parts else []
    if len(first) == 4:
        out["x"] = [num(first[0]), num(first[1])]
        out["y"] = [num(first[2]), num(first[3])]
    for name, part in zip(("x2", "y2"), parts[1:3]):
        p = part.split()
        if len(p) == 2 and num(p[0]) is not None:
            out[name] = [num(p[0]), num(p[1])]
    return out


def svg(key):
    path = os.path.join(work, key + ".svg")
    doc = svg_truth.svg_document(path)
    row = {"plotregion": doc["plotregion"],
           "texts": [{k: t[k] for k in ("x", "y", "anchor", "rotate", "text")}
                     for t in doc["texts"]],
           "vlines": [{k: d[k] for k in ("x1", "y1", "x2", "y2", "stroke")}
                      for d in doc["vlines"]]}
    for ax in ("x", "y"):
        r = svg_truth.svg_axis_reading(path, ax, doc=doc)
        row[ax + "axis"] = {"tick_px": r.get("tick_px"),
                            "labels": r.get("labels"),
                            "tick_side": r.get("tick_side")}
    return row


out = {}
n = int(G("DR_N"))
for i in range(1, n + 1):
    i = str(i)
    rc = int(G("DR_R" + i))
    row = {"rc": rc, "log": logged(i), "command": G("DR_C" + i)}
    if rc == 0:
        row["scale"] = scales(G("DR_S" + i))
        row.update(svg("g" + i))
    out[G("DR_K" + i)] = row
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("DR_VERSION"), "born_date": G("DR_BORN"),
                "dash_commit": commit, "extracted": G("DR_WHEN"),
                "scheme": "s2color",
                "source": "scripts/extract_date_axis_rule_truth.do"}
with open(G("DR_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
for i in range(1, n + 1):
    p = os.path.join(work, "g%d.svg" % i)
    if os.path.exists(p):
        os.remove(p)
print("wrote", G("DR_OUT"))
end
