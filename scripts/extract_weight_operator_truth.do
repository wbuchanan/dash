*! extract_weight_operator_truth.do -- WP-31 section 07 (A5, A6, A8):
*! measure what twoway does with a weight expression ([aw=price+1],
*! [aw=L.price]), with a time-series operator in an option's variable
*! (mlabel(L.make), colorvar(L.mpg), mlabvposition(L.pos), by(L.foreign))
*! and with a date literal in a y label, tick or scale option
*! (ylabel(2000m1)): each command's return code and the lines twoway
*! prints, and for a drawn weighted fit the values of the serset twoway
*! plots, so dash's answers are proved against live twoway, not modelled.
*! twoway only: the output is the same before and after dash changes.
*!
*! Output: test/fixtures/weight_operator_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_weight_operator_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zw_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zw_bad' {
    display as error "extract_weight_operator_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zw_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zw_rc' | _rc {
    local _zw_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_weight_operator_truth.do: `_zw_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZW_REPO "`repo'"
global ZW_OUT "${ZW_REPO}/test/fixtures/weight_operator_truth.json"

adopath ++ "${ZW_REPO}"
global dash_nobrowser 1

local work "`c(tmpdir)'dash_weight_operator_probe"
capture mkdir "`work'"
global ZW_WORK "`work'"

if `"`c(python_exec)'"' == "" {
    display as error "extract_weight_operator_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

quietly shell git -C "${ZW_REPO}" rev-parse HEAD > "${ZW_WORK}/git_head.txt"
global ZW_VERSION "`c(stata_version)'"
global ZW_BORN "`c(born_date)'"
global ZW_WHEN "`c(current_date)' `c(current_time)'"
global ZW_KEYS ""

* _zw_data: the probe data -- auto, tsset on t = _n, the generated twins
* of the weight expressions, a clock position and a monthly date.
capture program drop _zw_data
program define _zw_data
    sysuse auto, clear
    quietly generate t = _n
    quietly tsset t
    quietly generate double w1 = price + 1
    quietly generate double w2 = L.price
    quietly generate double w3 = rep78 + 1
    quietly generate int pos = mod(_n, 12)
    quietly generate ym = ym(2000, mod(_n, 12) + 1)
    format ym %tm
end

* _zw_run <sec> <key> <serset 0|1> : <twoway command>  -- run the command
* under a log, record its rc and the log (the lines twoway printed) in
* globals ZW_RC_<sec>_<key> and ZW_LOG_<sec>_<key>; with serset 1 and rc 0
* the plot's serset 0 is written to <work>/<sec>_<key>.csv.
capture program drop _zw_run
program define _zw_run
    gettoken sec 0 : 0
    gettoken key 0 : 0
    gettoken ser 0 : 0
    gettoken colon 0 : 0, parse(":")
    local cmd `"`0'"'
    local lf "${ZW_WORK}/`sec'_`key'.log"
    local gp "${ZW_WORK}/`sec'_`key'.gph"
    capture graph drop _all
    quietly log using "`lf'", text replace name(zwlog)
    capture noisily `cmd' nodraw
    local rc = _rc
    quietly log close zwlog
    global ZW_RC_`sec'_`key' "`rc'"
    global ZW_LOG_`sec'_`key' "`lf'"
    global ZW_CMD_`sec'_`key' `"`cmd'"'
    global ZW_KEYS "${ZW_KEYS} `sec':`key'"
    if `rc' == 0 & `ser' {
        quietly `cmd' nodraw saving("`gp'", replace)
        preserve
        capture graph drop _all
        capture serset drop _all
        quietly graph use "`gp'"
        serset set 0
        serset use, clear
        quietly ds
        local i 0
        foreach v in `r(varlist)' {
            local ++i
            quietly rename `v' c`i'
            capture confirm numeric variable c`i'
            if !_rc format c`i' %21.0g
        }
        quietly export delimited using "${ZW_WORK}/`sec'_`key'.csv", replace datafmt
        restore
    }
    capture erase "`gp'"
    display as text "ZW `sec' `key': rc `rc'"
end

_zw_data
* The probe data the weighted fits were drawn from, for the renderer's
* side of the comparison (test/test_weight_expressions.py).
preserve
keep mpg weight price rep78 t
format mpg weight price rep78 t %21.0g
quietly export delimited using "${ZW_WORK}/data.csv", replace datafmt
restore

* ---- weights: rc and the plotted serset ----
_zw_run weights lfit_aw_expr 1 : twoway lfit mpg weight [aw=price+1],
_zw_run weights lfit_aw_var 1 : twoway lfit mpg weight [aw=w1],
_zw_run weights lfit_aw_ts 1 : twoway lfit mpg weight [aw=L.price],
_zw_run weights lfit_aw_ts_var 1 : twoway lfit mpg weight [aw=w2],
_zw_run weights hist_fw_expr 1 : twoway histogram mpg [fw=rep78+1],
_zw_run weights hist_fw_var 1 : twoway histogram mpg [fw=w3],
_zw_run weights kde_aw_expr 1 : twoway kdensity mpg [aw=price+1],
_zw_run weights kde_aw_var 1 : twoway kdensity mpg [aw=w1],
_zw_run weights lpoly_aw_expr 1 : twoway lpoly mpg weight [aw=price+1],
_zw_run weights lpoly_aw_var 1 : twoway lpoly mpg weight [aw=w1],
_zw_run weights bad_expr 0 : twoway lfit mpg weight [aw=nosuch+1],
_zw_run weights bad_var 0 : twoway lfit mpg weight [aw=nosuch],
_zw_run weights bad_syntax 0 : twoway lfit mpg weight [aw=price+],

* ---- operators in an option's variable ----
_zw_run operators mlabel_L 1 : twoway scatter mpg weight, mlabel(L.make)
_zw_run operators mlabel_Lnum 1 : twoway scatter mpg weight, mlabel(L.rep78)
_zw_run operators colorvar_L 1 : twoway scatter mpg weight, colorvar(L.mpg)
_zw_run operators mlabvpos_L 1 : twoway scatter mpg weight, mlabel(make) mlabvposition(L.pos)
_zw_run operators by_L 1 : twoway scatter mpg weight, by(L.foreign)

* ---- date literals in y options ----
_zw_run ydates ylabel 0 : twoway scatter mpg weight, ylabel(2000m1)
_zw_run ydates ytick 0 : twoway scatter mpg weight, ytick(2000m1)
_zw_run ydates ymlabel 0 : twoway scatter mpg weight, ymlabel(2000m1)
_zw_run ydates ymtick 0 : twoway scatter mpg weight, ymtick(2000m1)
_zw_run ydates ylabel2 0 : twoway (scatter mpg weight, yaxis(2)), ylabel(2000m1, axis(2))
_zw_run ydates ytick2 0 : twoway (scatter mpg weight, yaxis(2)), ytick(2000m1, axis(2))
_zw_run ydates yscale 0 : twoway scatter mpg weight, yscale(range(2000m1))
_zw_run ydates yscale2 0 : twoway (scatter mpg weight, yaxis(2)), yscale(range(2000m1) axis(2))
_zw_run ydates ylabel_tfmt 0 : twoway scatter ym weight, ylabel(2000m1)
_zw_run ydates ylabel_tfmt_lit 0 : twoway scatter ym weight, ylabel(480)
_zw_run ydates ylabel_num 0 : twoway scatter mpg weight, ylabel(480)

python:
import csv, json, os
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


def lines(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            got = [ln.rstrip("\n").rstrip() for ln in fh]
    except OSError:
        return []
    return [ln for ln in got if ln.strip()]


def serset(path):
    try:
        with open(path, encoding="utf-8") as fh:
            rows = list(csv.reader(fh))
    except OSError:
        return None
    if not rows:
        return None
    cols = {h: [] for h in rows[0]}
    for r in rows[1:]:
        for h, v in zip(rows[0], r):
            try:
                cols[h].append(float(v) if v not in ("", ".") else None)
            except ValueError:
                cols[h].append(v)
    return cols


work = G("ZW_WORK")
out = {"weights": {}, "operators": {}, "ydates": {}}
for sk in G("ZW_KEYS").split():
    sec, key = sk.split(":", 1)
    rc = int(G("ZW_RC_%s_%s" % (sec, key)))
    lf = G("ZW_LOG_%s_%s" % (sec, key))
    txt = lines(lf)
    rec = {"cmd": G("ZW_CMD_%s_%s" % (sec, key)).strip().rstrip(","),
           "rc": rc, "lines": txt, "text": txt[-1] if txt else ""}
    csvp = os.path.join(work, "%s_%s.csv" % (sec, key))
    if rc == 0 and os.path.exists(csvp):
        rec["serset"] = serset(csvp)
        os.remove(csvp)
    try:
        os.remove(lf)
    except OSError:
        pass
    out[sec][key] = rec
out["data"] = serset(os.path.join(work, "data.csv"))
os.remove(os.path.join(work, "data.csv"))
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZW_VERSION"), "born_date": G("ZW_BORN"),
                "dash_commit": commit, "extracted": G("ZW_WHEN"),
                "source": "scripts/extract_weight_operator_truth.do"}
with open(G("ZW_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZW_OUT"))
end
