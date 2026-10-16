*! extract_estimator_edges_truth.do
*! WP-31 S46 (C11, C10d): Stata's own lpoly grids for the weight-threshold
*! probes (gaussian bwidth 1, 0.5, 2 and biweight bwidth 1 on auto's mpg
*! and weight, n(50)), lpoly's ci path on the gaussian probe, the round-off
*! cases D1-D3, the five domestic rows of the parity frame, the return
*! codes and words of twoway's lpoly/lpolyci refusals (D6-D8), and
*! twoway kdensity's range() naming a string or an all-missing variable
*! (C10d).
*!
*! Each refusal is run with capture noisily inside its own log, and the
*! trailing python: block reads the logs and the generated variables into
*! test/fixtures/estimator_edges_truth.json; it never calls a shell.
*!
*! Run (Stata only through the slot wrapper, never the GUI):
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> \
*!       <repo>/scripts/extract_estimator_edges_truth.do

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_estimator_edges_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
if _rc {
    display as error "extract_estimator_edges_truth.do: not a dash tree; set DASH_REPO"
    exit 601
}

clear all
set more off
set linesize 255
version 19
set graphics off

global EE_REPO "`repo'"
global EE_OUT "${EE_REPO}/test/fixtures/estimator_edges_truth.json"
local work "`c(tmpdir)'dash_estimator_edges_probe"
capture mkdir "`work'"
global EE_WORK "`work'"

local stata_version = c(stata_version)
local born_date "`c(born_date)'"
local extracted "`c(current_date)'"
tempfile eegit
quietly shell git -C "${EE_REPO}" rev-parse HEAD > "`eegit'"
tempname eegh
file open `eegh' using "`eegit'", read text
file read `eegh' eeline
file close `eegh'
local dash_commit = trim(`"`eeline'"')

python:
import json
EE = {}
end

capture program drop _ee_grid
program _ee_grid
    // _ee_grid <key> <lpoly command ...>: xg, yg (and sg when asked).
    gettoken key 0 : 0
    foreach v in xg yg sg {
        capture drop `v'
    }
    quietly `0'
    capture confirm variable sg
    local hasse = (_rc == 0)
    python: __import__("__main__")._ee_take("`key'", `hasse', "`r(bwidth)'")
end

capture program drop _ee_rc
program _ee_rc
    // _ee_rc <key> <command ...>: the rc and the error text twoway prints.
    gettoken key 0 : 0
    local lg "${EE_WORK}/`key'.log"
    capture log close _ee
    quietly log using "`lg'", text replace name(_ee)
    capture noisily `0'
    local rc = _rc
    quietly log close _ee
    python: __import__("__main__")._ee_words("`key'", `rc', "`lg'")
end

python:
def _ee_take(key, hasse, bw):
    from sfi import Data
    def col(name):
        out = []
        for v in Data.get(var=name):
            out.append(None if v is None or v >= 8.98e307 else float(v))
        return out
    n = 0
    xg = col("xg")
    while n < len(xg) and xg[n] is not None:
        n += 1
    rec = {"xg": xg[:n], "yg": col("yg")[:n]}
    if hasse:
        rec["sg"] = col("sg")[:n]
    try:
        rec["bwidth"] = float(bw)
    except ValueError:
        rec["bwidth"] = None
    EE[key] = rec


def _ee_words(key, rc, path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = [l.rstrip("\n") for l in fh]
    body = [l for l in lines
            if l.strip() and not l.startswith(("  name:", "       log:",
                                                 "  log type:", " opened on:",
                                                 "      name:", "      log:",
                                                 " closed on:"))
            and not l.startswith(". ") and not l.startswith("-" * 10)]
    EE[key] = {"rc": int(rc), "text": [l.strip() for l in body
                                         if not l.strip().startswith("r(")]}
end

* ---- auto: the probes' data (mpg, weight) ----
sysuse auto, clear
python: from sfi import Data as _eeD; EE["auto"] = {"mpg": [float(v) for v in _eeD.get(var="mpg")], "weight": [float(v) for v in _eeD.get(var="weight")]}

* ---- lp.*: the weight threshold probes (D-46a) ----
sysuse auto, clear
_ee_grid lp.gauss_bw1 lpoly mpg weight, kernel(gaussian) bwidth(1) n(50) generate(xg yg) nograph
_ee_grid lp.gauss_bw05 lpoly mpg weight, kernel(gaussian) bwidth(0.5) n(50) generate(xg yg) nograph
_ee_grid lp.gauss_bw2 lpoly mpg weight, kernel(gaussian) bwidth(2) n(50) generate(xg yg) nograph
_ee_grid lp.biweight_bw1 lpoly mpg weight, kernel(biweight) bwidth(1) n(50) generate(xg yg) nograph
_ee_grid lp.gauss_bw1_ci lpoly mpg weight, kernel(gaussian) bwidth(1) n(50) ci generate(xg yg) se(sg) nograph
_ee_grid lp.gauss_bw50 lpoly mpg weight, kernel(gaussian) bwidth(50) n(50) generate(xg yg) nograph
_ee_grid lp.gauss_bw50_ci lpoly mpg weight, kernel(gaussian) bwidth(50) n(50) ci generate(xg yg) se(sg) nograph

* ---- lp.D1-D3: Stata's round-off decides ----
sysuse auto, clear
quietly generate ylin = 2*weight + 1
quietly generate yw = weight
quietly generate ys = mpg*1e-150
_ee_grid lp.D1 lpoly ylin weight, degree(0) n(50) generate(xg yg) nograph
_ee_grid lp.D2_0 lpoly yw weight, degree(0) n(50) generate(xg yg) nograph
_ee_grid lp.D2_1 lpoly yw weight, degree(1) n(50) generate(xg yg) nograph
_ee_grid lp.D3 lpoly ys weight, degree(2) n(50) generate(xg yg) nograph

* ---- lp.D6-D8: refusals, as twoway gives them ----
sysuse auto, clear
_ee_rc lp.D6 twoway lpolyci mpg weight if _n == 1, pwidth(0)
_ee_rc lp.D6_lpoly twoway lpoly mpg weight if _n == 1
_ee_rc lp.D6_pw0 twoway lpolyci mpg weight, pwidth(0)
_ee_rc lp.D7.bwidth twoway lpoly mpg weight, bwidth(abc)
_ee_rc lp.D7.degree twoway lpoly mpg weight, degree(9)
_ee_rc lp.D7.n twoway lpoly mpg weight, n(0)
_ee_rc lp.D7.kernel twoway lpoly mpg weight, kernel(x)
_ee_rc lp.D8 twoway lpolyci mpg weight, pwidth(+800)
_ee_rc lp.D8_bw twoway lpoly mpg weight, bwidth(+800)
_ee_rc lp.D6_n2 twoway lpoly mpg weight if _n <= 2
_ee_rc lp.D6_n3 twoway lpoly mpg weight if _n <= 3
_ee_rc lp.D6_ci_n2 twoway lpolyci mpg weight if _n <= 2
_ee_rc lp.D6_ci_n3 twoway lpolyci mpg weight if _n <= 3
_ee_rc lp.D6_bw twoway lpoly mpg weight if _n == 1, bwidth(abc)
_ee_rc lp.D7.degree8 twoway lpoly mpg weight, degree(8)
_ee_rc lp.D7.degree_ci twoway lpolyci mpg weight, degree(9)
_ee_rc lp.D7.degree_neg twoway lpoly mpg weight, degree(-1)
_ee_rc lp.D7.bwidth_neg twoway lpoly mpg weight, bwidth(-1)
_ee_rc lp.D7.n_abc twoway lpoly mpg weight, n(abc)
_ee_rc lp.D8_pw_abc twoway lpolyci mpg weight, pwidth(abc)
_ee_rc lp.D8_pw_neg twoway lpolyci mpg weight, pwidth(-5)

* ---- lp.five_rows: the parity frame's five domestic rows ----
clear
quietly input mpg weight
22 2930
25 2200
21 3000
14 4080
16 3600
end
_ee_grid lp.five_rows lpoly mpg weight, generate(xg yg) nograph

* ---- kd.*: kdensity range() on a string or an all-missing variable ----
sysuse auto, clear
quietly generate allmiss = .
foreach k in string missing {
    local v = cond("`k'" == "string", "make", "allmiss")
    _ee_rc kd.range_`k' twoway kdensity mpg, range(`v') nodraw name(ee_kd2, replace)
    capture graph drop _all
    capture serset drop _all
    local gph "${EE_WORK}/kd_`k'.gph"
    capture erase "`gph'"
    quietly twoway kdensity mpg, range(`v') nodraw saving("`gph'", replace)
    capture graph drop _all
    capture serset drop _all
    preserve
    quietly graph use "`gph'", nodraw
    quietly serset set 0
    quietly serset use, clear
    python: from sfi import Data as _eeD; __import__("__main__").EE["kd.range_`k'"]["serset"] = {_eeD.getVarName(i): [None if v is None or v >= 8.98e307 else float(v) for v in _eeD.get(var=i)] for i in range(_eeD.getVarCount())}
    restore
    capture graph drop _all
}

python:
from sfi import Macro
EE["_meta"] = {
    "stata_version": Macro.getLocal("stata_version"),
    "born_date": Macro.getLocal("born_date"),
    "dash_commit": Macro.getLocal("dash_commit"),
    "extracted": Macro.getLocal("extracted"),
    "source": "scripts/extract_estimator_edges_truth.do",
}
with open(Macro.getGlobal("EE_OUT"), "w", encoding="utf-8") as fh:
    json.dump(EE, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote", Macro.getGlobal("EE_OUT"), len(EE), "keys")
end
