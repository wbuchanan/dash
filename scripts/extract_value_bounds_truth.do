*! extract_value_bounds_truth.do -- WP-31 section 05 (GAPS3 C10a): measure
*! which range(), n(), bwidth() and level() values twoway accepts, resets
*! or refuses, with its return code and first error line, and for each
*! drawn probe the plot's serset (per variable: N, min, max, sum), so
*! dash's bounds are proved against live twoway, not modelled.  twoway
*! only: the output is the same before and after dash changes.
*!
*! Output: test/fixtures/value_bounds_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_value_bounds_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zv_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zv_bad' {
    display as error "extract_value_bounds_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zv_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zv_rc' | _rc {
    local _zv_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_value_bounds_truth.do: `_zv_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZV_REPO "`repo'"
global ZV_OUT "${ZV_REPO}/test/fixtures/value_bounds_truth.json"

local work "`c(tmpdir)'dash_value_bounds_probe"
capture mkdir "`work'"
global ZV_WORK "`work'"

if `"`c(python_exec)'"' == "" {
    display as error "extract_value_bounds_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

quietly shell git -C "${ZV_REPO}" rev-parse HEAD > "${ZV_WORK}/git_head.txt"
global ZV_VERSION "`c(stata_version)'"
global ZV_BORN "`c(born_date)'"
global ZV_WHEN "`c(current_date)' `c(current_time)'"
global ZV_KEYS ""

* _zv_probe key twoway-command: run the command on a fresh auto, record
* its rc in ZV_RC_<key>, its output (the error line) in <work>/<key>.log
* and, when it drew, plot 1's serset as "N min max sum" per variable in
* ZV_S_<key>.  The command always holds a comma.
capture program drop _zv_probe
program define _zv_probe
    gettoken key cmd : 0
    quietly sysuse auto, clear
    serset clear
    capture graph drop _all
    quietly log using "${ZV_WORK}/`key'.log", text replace name(zvp) nomsg
    capture noisily twoway `cmd' nodraw name(g, replace)
    local rc = _rc
    quietly log close zvp
    global ZV_RC_`key' `rc'
    global ZV_KEYS "${ZV_KEYS} `key'"
    global ZV_S_`key' ""
    if !`rc' {
        local id "`.g.plotregion1.plot1.serset.id'"
        preserve
        quietly serset set `id'
        quietly serset use, clear
        local s ""
        foreach v of varlist _all {
            quietly summarize `v'
            local s "`s' `r(N)' `=strofreal(r(min), "%21.0g")' `=strofreal(r(max), "%21.0g")' `=strofreal(r(sum), "%21.0g")'"
        }
        global ZV_S_`key' "`s'"
        restore
    }
    display as text "ZV `key': rc `rc' serset ${ZV_S_`key'}"
end

* range()
_zv_probe range_dot_hi lfit mpg weight, range(. 4000)
_zv_probe range_dot_lo lfit mpg weight, range(1000 .)
_zv_probe range_dots lfit mpg weight, range(. .)
_zv_probe range_reversed lfit mpg weight, range(4000 1000)
_zv_probe range_qfit_dot qfit mpg weight, range(. 4000)
_zv_probe range_lfitci_dot lfitci mpg weight, range(. 4000)
_zv_probe range_qfitci_dot qfitci mpg weight, range(1000 .)
_zv_probe range_var_lfit lfit mpg weight, range(weight)
_zv_probe range_var_kdensity kdensity mpg, range(weight)
_zv_probe range_var_function function y=x, range(weight)
_zv_probe range_var_missing lfit mpg weight, range(nosuch)
_zv_probe range_var_string lfit mpg weight, range(make)
_zv_probe range_one_number lfit mpg weight, range(10)
_zv_probe range_three lfit mpg weight, range(1 2 3)
_zv_probe range_function_one function y=x, range(10)
_zv_probe range_function_three function y=x, range(1 2 3)
_zv_probe range_function_dot function y=x, range(. 3)
_zv_probe range_function_var_missing function y=x, range(nosuch)
_zv_probe range_function_var_string function y=x, range(make)
_zv_probe range_kdensity_one kdensity mpg, range(10)
_zv_probe range_kdensity_three kdensity mpg, range(1 2 3)
_zv_probe range_kdensity_dot kdensity mpg, range(. 30)
_zv_probe range_kdensity_var_missing kdensity mpg, range(nosuch)
_zv_probe range_kdensity_var_string kdensity mpg, range(make)
_zv_probe range_kdensity_nums kdensity mpg, range(1760 4840)
_zv_probe range_function_nums function y=x, range(1760 4840)

* n()
_zv_probe n_one lfit mpg weight, n(1)
_zv_probe n_zero lfit mpg weight, n(0)
_zv_probe n_kdensity_one kdensity mpg, n(1)
_zv_probe n_function_one function y=x, n(1)

* bwidth()
_zv_probe bwidth_kdensity_default kdensity mpg,
_zv_probe bwidth_kdensity_0 kdensity mpg, bwidth(0)
_zv_probe bwidth_lpoly_0 lpoly mpg weight, bwidth(0)
_zv_probe bwidth_lpolyci_0 lpolyci mpg weight, bwidth(0)

* lowess bwidth(): ids for the values 1 1.5 5 0 -1 .3 .8
_zv_probe lowess_1 lowess mpg weight, bwidth(1)
_zv_probe lowess_1p5 lowess mpg weight, bwidth(1.5)
_zv_probe lowess_5 lowess mpg weight, bwidth(5)
_zv_probe lowess_0 lowess mpg weight, bwidth(0)
_zv_probe lowess_m1 lowess mpg weight, bwidth(-1)
_zv_probe lowess_p3 lowess mpg weight, bwidth(.3)
_zv_probe lowess_p8 lowess mpg weight, bwidth(.8)

* level(): ids for the values 5 9.99 10 99.99 100 50 on lfitci
_zv_probe level_5 lfitci mpg weight, level(5)
_zv_probe level_9p99 lfitci mpg weight, level(9.99)
_zv_probe level_10 lfitci mpg weight, level(10)
_zv_probe level_99p99 lfitci mpg weight, level(99.99)
_zv_probe level_100 lfitci mpg weight, level(100)
_zv_probe level_50 lfitci mpg weight, level(50)
_zv_probe level_qfitci_5 qfitci mpg weight, level(5)
_zv_probe level_fpfitci_5 fpfitci mpg weight, level(5)
_zv_probe level_lpolyci_5 lpolyci mpg weight, level(5)

* summarize weight, the variable range(weight) names
quietly sysuse auto, clear
quietly summarize weight
global ZV_WMIN = strofreal(r(min), "%21.0g")
global ZV_WMAX = strofreal(r(max), "%21.0g")

python:
import json, os
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


work = G("ZV_WORK")
_HEAD = ("name:", "log:", "log type:", "opened on:", "closed on:")


def message(key):
    try:
        with open(os.path.join(work, key + ".log"), encoding="utf-8") as fh:
            lines = [ln.strip() for ln in fh.read().splitlines()]
    except OSError:
        return ""
    for ln in lines:
        if not ln or ln.startswith(_HEAD) or set(ln) <= set("-"):
            continue
        return ln
    return ""


def serset(key):
    w = G("ZV_S_" + key).split()
    out = []
    for i in range(0, len(w), 4):
        n, lo, hi, s = w[i:i + 4]
        f = [None if v == "." else float(v) for v in (lo, hi, s)]
        out.append({"n": int(n), "min": f[0], "max": f[1], "sum": f[2]})
    return out


def rec(key):
    rc = int(G("ZV_RC_" + key))
    r = {"rc": rc, "message": message(key) if rc else ""}
    if rc == 0:
        r["serset"] = serset(key)
    return r


keys = G("ZV_KEYS").split()
recs = {k: rec(k) for k in keys}
out = {"range": {}, "n": {}, "bwidth": {}, "lowess_bwidth": {}, "level": {}}
for k, r in recs.items():
    for grp in ("range", "n", "bwidth"):
        if k.startswith(grp + "_"):
            out[grp][k[len(grp) + 1:]] = r
lowess_ids = {"1": "1", "1p5": "1.5", "5": "5", "0": "0", "m1": "-1",
              "p3": ".3", "p8": ".8"}
lo8 = recs["lowess_p8"]["serset"][0]["sum"]
lo3 = recs["lowess_p3"]["serset"][0]["sum"]
for i, v in lowess_ids.items():
    r = dict(recs["lowess_" + i])
    if r["rc"] == 0:
        ys = r["serset"][0]["sum"]
        r["reset"] = int(ys == lo8 and ys != lo3 and v != ".8")
    else:
        r["reset"] = 0
    out["lowess_bwidth"][v] = r
level_ids = {"5": "5", "9p99": "9.99", "10": "10", "99p99": "99.99",
             "100": "100", "50": "50", "qfitci_5": "qfitci_5",
             "fpfitci_5": "fpfitci_5", "lpolyci_5": "lpolyci_5"}
for i, v in level_ids.items():
    out["level"][v] = recs["level_" + i]
out["summarize_weight"] = {"min": float(G("ZV_WMIN")), "max": float(G("ZV_WMAX"))}
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZV_VERSION"), "born_date": G("ZV_BORN"),
                "dash_commit": commit, "extracted": G("ZV_WHEN"),
                "source": "scripts/extract_value_bounds_truth.do"}
with open(G("ZV_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
for k in keys + ["git_head"]:
    try:
        os.remove(os.path.join(work, k + (".txt" if k == "git_head" else ".log")))
    except OSError:
        pass
print("wrote", G("ZV_OUT"))
end
