*! extract_marker_linewidth_truth.do -- WP-31 S60 (GAPS3 K3): measure the
*! width of each plot's marker outline under four schemes (three written
*! here, one Stata's own economist), read from twoway's own class values
*! (.Graph.plotregion1.plot<k>.style.marker.linestyle.width.setting), so the
*! chain linewidth p#mark -> pmark -> p# -> p that dash follows is proved
*! against live twoway.  twoway only: the output is the same before and
*! after dash changes.
*!
*! Output: test/fixtures/marker_linewidth_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_marker_linewidth_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zm_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zm_bad' {
    display as error "extract_marker_linewidth_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zm_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zm_rc' | _rc {
    local _zm_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_marker_linewidth_truth.do: `_zm_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZM_REPO "`repo'"
global ZM_OUT "${ZM_REPO}/test/fixtures/marker_linewidth_truth.json"

adopath ++ "${ZM_REPO}"
quietly do "${ZM_REPO}/dash_parse.mata"
quietly do "${ZM_REPO}/dash.ado"
global dash_nobrowser 1

local work "`c(tmpdir)'dash_marker_linewidth_probe"
capture mkdir "`work'"
global ZM_WORK "`work'"

if `"`c(python_exec)'"' == "" {
    display as error "extract_marker_linewidth_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

quietly shell git -C "${ZM_REPO}" rev-parse HEAD > "${ZM_WORK}/git_head.txt"
global ZM_VERSION "`c(stata_version)'"
global ZM_BORN "`c(born_date)'"
global ZM_WHEN "`c(current_date)' `c(current_time)'"

* The three written schemes (session only: files in the probe directory,
* which joins the adopath; no `set scheme, permanently').
global ZM_S_mk1 "#include s2color|linewidth p1 vthick|linewidth p2mark thick"
global ZM_S_mk2 "#include s2color|linewidth pmark vvthick|linewidth p1mark thin|linewidth p3 vthick"
global ZM_S_mk3 "#include s2color|linewidth p1dotmark vvthick|linewidth p1mark thick|linewidth p2 vthick"
global ZM_S_economist "#include economist"
foreach s in mk1 mk2 mk3 {
    tempname fh
    file open `fh' using "${ZM_WORK}/scheme-`s'.scheme", write text replace
    local rest "${ZM_S_`s'}"
    while `"`rest'"' != "" {
        gettoken line rest : rest, parse("|")
        if `"`line'"' != "|" file write `fh' `"`line'"' _n
    }
    file close `fh'
}
adopath ++ "${ZM_WORK}"

* _zm_rec key n: the marker outline widths of plots 1..n of the current
* graph into global ZM_R_<key>.
capture program drop _zm_rec
program define _zm_rec
    args key n
    local out ""
    forvalues k = 1/`n' {
        local w "`.Graph.plotregion1.plot`k'.style.marker.linestyle.width.setting'"
        if "`w'" == "" local w "."
        local out "`out' `w'"
    }
    global ZM_R_`key' "`out'"
    display as text "ZM `key':`out'"
end

sysuse auto, clear
generate p2 = price * 0.8
generate lo = price - 1000
generate hi = price + 1000
generate w2 = weight + 100

global ZM_CMDS "scatter connected scatteri dot dropline rcapsym rscatter rconnected pcscatter pccapsym ciscatter"
foreach s in economist mk1 mk2 mk3 {
    set scheme `s'
    foreach t of global ZM_CMDS {
        local n 3
        if inlist("`t'", "scatter", "connected", "dropline") {
            local cmd "`t' price weight || `t' p2 weight || `t' price weight"
        }
        else if "`t'" == "dot" {
            local cmd "dot price weight in 1/10 || dot p2 weight in 1/10 || dot price weight in 1/10"
        }
        else if "`t'" == "scatteri" {
            local cmd "scatteri 1 2 || scatteri 2 3 || scatteri 3 4"
        }
        else if inlist("`t'", "rcapsym", "rscatter", "rconnected") {
            local cmd "`t' lo hi weight || `t' lo p2 weight || `t' lo hi weight"
        }
        else if inlist("`t'", "pcscatter", "pccapsym") {
            local cmd "`t' lo weight hi w2 || `t' lo weight p2 w2 || `t' lo weight hi w2"
        }
        else {
            local cmd "lfitci price weight || scatter price weight || scatter p2 weight"
            local n 4
        }
        quietly twoway `cmd'
        _zm_rec `s'_`t' `n'
        graph drop _all
    }
}
set scheme mk1
quietly twoway scatter price weight, mlwidth(vthin) || scatter p2 weight
_zm_rec mk1_mlwidth 2
graph drop _all
set scheme s2color

python:
import json, os
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


def rec(key):
    return [None if w == "." else float(w) for w in G("ZM_R_" + key).split()]


cmds = G("ZM_CMDS").split()
cases = {}
for s in ("economist", "mk1", "mk2", "mk3"):
    cases[s] = {t: rec("%s_%s" % (s, t)) for t in cmds}
cases["mk1"]["mlwidth"] = rec("mk1_mlwidth")
schemes = {s: "".join(l + "\n" for l in G("ZM_S_" + s).split("|"))
           for s in ("economist", "mk1", "mk2", "mk3")}
out = {"cases": cases, "schemes": schemes,
       "_about": ("twoway <type> ... || <type> ... || <type> ... (three "
                  "plots; dot on in 1/10; 'ciscatter' is lfitci || scatter "
                  "|| scatter, whose band is plot 1 and line plot 2) on "
                  "sysuse auto under each scheme (a file in the probe "
                  "directory; for 'economist', Stata's own economist); each "
                  "value is the plot's marker outline width in Stata "
                  "linewidth units, read from .Graph.plotregion1.plot<k>"
                  ".style.marker.linestyle.width.setting.  'mlwidth' is "
                  "'scatter, mlwidth(vthin) || scatter' under mk1.")}
work = G("ZM_WORK")
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZM_VERSION"), "born_date": G("ZM_BORN"),
                "dash_commit": commit, "extracted": G("ZM_WHEN"),
                "source": "scripts/extract_marker_linewidth_truth.do"}
with open(G("ZM_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
for f in ["git_head.txt"] + ["scheme-%s.scheme" % s for s in ("mk1", "mk2", "mk3")]:
    try:
        os.remove(os.path.join(work, f))
    except OSError:
        pass
print("wrote", G("ZM_OUT"))
end
