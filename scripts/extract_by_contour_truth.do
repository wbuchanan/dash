*! extract_by_contour_truth.do
*! WP-41 section 41-01 (BY-28): the cuts twoway draws for each panel of a
*! contour or contourline graph under by(), for
*! test/fixtures/by_contour_truth.json.
*!
*! WHY THIS EXISTS
*!
*! dash cut each by() panel at the z ticks of its own rows, so one colour
*! meant a different z range in each panel.  twoway reads one z axis: every
*! panel, the Total panel too, is cut at the first panel's cuts.
*!
*! Output: test/fixtures/by_contour_truth.json
*!
*! Run with:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_by_contour_truth.do
*!
*! METHOD
*!
*! Every probe is `bc id "plot" "if" "options" "by" "alone-if"': the
*! command `twoway <plot> <if>, <options> by(<by>) name(G, replace)' is
*! run, exported to SVG (the cuts are empty until the graph is drawn) and
*! each panel's `.G.graphs[i].plotregion1.plot1.lastcuts' is written to a
*! record file; then the first panel is drawn alone
*! (`twoway <plot> if <alone-if>, <options>') and its lastcuts written.
*! The trailing python: block reads the record file and auto's rows (the
*! probes' variables) and writes the fixture.
*! ---------------------------------------------------------------------------

clear all
set graphics off
set more off
set linesize 255
version 19

* Root: DASH_REPO, else the current directory when it is a dash tree.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_by_contour_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zr_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zr_rc' | _rc {
    local _zr_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_by_contour_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1
global BC_REPO "`repo'"
global BC_OUT  "`repo'/test/fixtures/by_contour_truth.json"
local scratch "`c(tmpdir)'dash_by_contour_probe"
capture mkdir "`scratch'"
global BC_WORK "`scratch'"
global BC_REC  "`scratch'/by_contour_records.txt"

set scheme stcolor

global BC_SVER = c(stata_version)
global BC_BORN = c(born_date)
global BC_DATE = c(current_date) + " " + c(current_time)

// Provenance stamp: `shell' writes the commit into a file, read back.
tempfile bcgitrev
quietly shell git -C "${BC_REPO}" rev-parse HEAD > "`bcgitrev'"
tempname bcgfh
file open `bcgfh' using "`bcgitrev'", read text
file read `bcgfh' bcgitline
file close `bcgfh'
global BC_COMMIT = trim(`"`bcgitline'"')
capture assert ustrregexm(`"${BC_COMMIT}"', "^[0-9a-f]{40}$")
if _rc {
    display as error "extract_by_contour_truth.do: git rev-parse HEAD did not print a 40-character commit: ${BC_COMMIT}"
    exit 498
}

sysuse auto, clear
generate byte nf = 1 - foreign
quietly save "${BC_WORK}/bc.dta", replace

// ---------------------------------------------------------------------------
// bc id "plot" "if" "options" "by" "alone-if": one probe.
// ---------------------------------------------------------------------------
capture program drop bc
program define bc
    version 19
    args id plot ifq opts byo alone
    use "${BC_WORK}/bc.dta", clear
    capture noisily twoway `plot' `ifq', `opts' by(`byo') name(G, replace)
    local rc = _rc
    file write bcrec "R|`id'|`rc'|`plot' `ifq', `opts' by(`byo')" _n
    if `rc' exit
    capture erase "${BC_WORK}/`id'.svg"
    quietly graph export "${BC_WORK}/`id'.svg", name(G) replace
    local np = `.G.graphs.arrnels'
    forvalues k = 1/`np' {
        file write bcrec "P|`id'|`k'|`.G.graphs[`k'].plotregion1.plot1.lastcuts'" _n
    }
    capture noisily twoway `plot' if `alone', `opts' name(A, replace)
    if _rc exit
    capture erase "${BC_WORK}/`id'_alone.svg"
    quietly graph export "${BC_WORK}/`id'_alone.svg", name(A) replace
    file write bcrec "A|`id'|`.A.plotregion1.plot1.lastcuts'" _n
end

file open bcrec using "${BC_REC}", write text replace
bc C01 "contour price mpg weight" "" "" "foreign" "foreign == 0"
bc C02 "contour price mpg weight" "" "" "nf" "nf == 0"
bc C03 "contour price mpg weight" "" "" "rep78, total" "rep78 == 1"
bc C04 "contourline price mpg weight" "" "" "nf" "nf == 0"
bc C05 "contour price mpg weight" "" "levels(4)" "nf" "nf == 0"
bc C06 "contour price mpg weight" "" "ccuts(5000 9000)" "nf" "nf == 0"
bc C07 "contour price mpg weight" "" "" "nf, total" "nf == 0"
bc C08 "contour price mpg weight" "" "" "nf, rescale" "nf == 0"
bc C09 "contour price mpg weight" "" "" "nf, clegend(on)" "nf == 0"
bc C10 "contour price mpg weight" "if rep78 > 2" "" "rep78" "rep78 == 3"
file close bcrec
use "${BC_WORK}/bc.dta", clear

python:
import json, os
from sfi import Data, Macro

VARS = ["price", "mpg", "weight", "foreign", "rep78"]
_vals = Data.get(" ".join(VARS), missingval=None)
rows = {v: [None if r[i] is None else float(r[i]) for r in _vals]
        for i, v in enumerate(VARS)}


def cuts_of(text):
    return [float(t) for t in text.split()]


probes, order = {}, []
with open(Macro.getGlobal("BC_REC"), encoding="utf-8", errors="replace") as fh:
    for line in fh:
        f = line.rstrip("\n").split("|")
        if f[0] == "R":
            probes[f[1]] = {"cmd": "twoway " + "|".join(f[3:]),
                            "rc": int(f[2]), "panels": 0, "cuts": [],
                            "first_alone": None}
            order.append(f[1])
        elif f[0] == "P":
            p = probes[f[1]]
            p["panels"] += 1
            p["cuts"].append(cuts_of(f[3]))
        elif f[0] == "A":
            probes[f[1]]["first_alone"] = cuts_of(f[2])

out = {
    "_meta": {
        "stata_version": Macro.getGlobal("BC_SVER"),
        "born_date": Macro.getGlobal("BC_BORN"),
        "dash_commit": Macro.getGlobal("BC_COMMIT"),
        "extracted": Macro.getGlobal("BC_DATE"),
        "source": "scripts/extract_by_contour_truth.do",
    },
    "probes": {k: probes[k] for k in order},
    # auto's rows the probes draw, in the data's order (missing as null),
    # for the renderer tests (nf is 1 - foreign).
    "rows": rows,
}
with open(Macro.getGlobal("BC_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1)
    fh.write("\n")
print("wrote", Macro.getGlobal("BC_OUT"), len(order), "probes")
end
