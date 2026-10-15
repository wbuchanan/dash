*! extract_varlabel_mlabel_truth.do -- WP-31 section 34 (D8 C17 E3 C14
*! C15): measure what twoway does with yvarlabel()/xvarlabel(),
*! mlabprefix()/mlabsuffix(), lalign()/mlalign(), mlabstyle(), msangle()
*! names, the default marker-label clock of bar/rbar/scatter, and a range
*! plot labelled by one of its own variables.  twoway only: the output is
*! the same before and after dash changes.
*!
*! Output: test/fixtures/varlabel_mlabel_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_varlabel_mlabel_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_vl_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_vl_bad' {
    display as error "extract_varlabel_mlabel_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _vl_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_vl_rc' | _rc {
    local _vl_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_varlabel_mlabel_truth.do: `_vl_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global VL_REPO "`repo'"
global VL_OUT "${VL_REPO}/test/fixtures/varlabel_mlabel_truth.json"

local work "`c(tmpdir)'dash_varlabel_probe"
capture mkdir "`work'"
global VL_WORK "`work'"

if `"`c(python_exec)'"' == "" {
    display as error "extract_varlabel_mlabel_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

quietly shell git -C "${VL_REPO}" rev-parse HEAD > "${VL_WORK}/git_head.txt"
global VL_VERSION "`c(stata_version)'"
global VL_BORN "`c(born_date)'"
global VL_WHEN "`c(current_date)' `c(current_time)'"
global VL_KEYS ""

sysuse auto, clear
generate lo = mpg - 2
generate hi = mpg + 2
set scheme s2color

* _vl_run key : command -- run the twoway command under a log, keep its rc,
* the log (for its note and error lines), its SVG export, the y and x axis
* titles and the first plot's marker-label clock, under key.
capture program drop _vl_run
program define _vl_run
    gettoken key 0 : 0
    gettoken colon 0 : 0
    local lg "${VL_WORK}/`key'.log"
    capture erase "`lg'"
    capture erase "${VL_WORK}/`key'.svg"
    quietly log using "`lg'", name(_vl) text replace
    capture noisily twoway `0' name(g, replace)
    local rc = _rc
    quietly log close _vl
    local yt ""
    local xt ""
    local pos ""
    local ytn 0
    local xtn 0
    if `rc' == 0 {
        quietly graph export "${VL_WORK}/`key'.svg", name(g) replace
        local ytn "`.g.yaxis1.title.text.arrnels'"
        local xtn "`.g.xaxis1.title.text.arrnels'"
        if 0`ytn' > 0 local yt `"`.g.yaxis1.title.text[1]'"'
        if 0`xtn' > 0 local xt `"`.g.xaxis1.title.text[1]'"'
        local pos "`.g.plotregion1.plot1.style.label.position.setting'"
        capture graph drop g
    }
    global VL_R_`key' "`rc'"
    global VL_Y_`key' `"`yt'"'
    global VL_X_`key' `"`xt'"'
    global VL_YN_`key' "`ytn'"
    global VL_XN_`key' "`xtn'"
    global VL_P_`key' "`pos'"
    global VL_KEYS "${VL_KEYS} `key'"
    display as text "VL `key': rc `rc' y[`yt'] x[`xt'] pos[`pos']"
end

* D8
_vl_run varlabel__y : scatter mpg weight, yvarlabel("Miles")
_vl_run varlabel__x : scatter mpg weight, xvarlabel("Pounds")
_vl_run varlabel__both : scatter mpg weight, yvarlabel("Miles") xvarlabel("Pounds")
_vl_run varlabel__x_empty : scatter mpg weight, xvarlabel("")
_vl_run varlabel__y_two : scatter mpg price weight, yvarlabel("A" "B")
_vl_run varlabel__plain : scatter mpg weight,
_vl_run varlabel__range : rscatter lo hi weight, yvarlabel("Band") xvarlabel("Pounds")
_vl_run varlabel__range_two : rscatter lo hi weight, yvarlabel("Band" "Top")
_vl_run varlabel__fit : lfit mpg weight, yvarlabel("Q") xvarlabel("Pounds")
_vl_run varlabel__fitci : lfitci mpg weight, yvarlabel("Q")
_vl_run varlabel__overlay : (scatter mpg weight) (lfit mpg weight, yvarlabel("Q")),
_vl_run varlabel__plain_two : scatter mpg price weight,
* C17
_vl_run prefix__both : scatter mpg weight in 1/3, mlabel(make) mlabprefix("[") mlabsuffix("]")
_vl_run prefix__none : scatter mpg weight in 1/3, mlabel(make)
foreach a in center inside outside bogus {
    _vl_run align__`a' : line mpg weight, lalign(`a')
    _vl_run malign__`a' : scatter mpg weight, mlalign(`a')
}
_vl_run align__la : line mpg weight, la(inside)
* E3
_vl_run mlabstyle__p2 : scatter mpg weight in 1/3, mlabel(make) mlabstyle(p2)
_vl_run mlabstyle__bogus : scatter mpg weight in 1/3, mlabel(make) mlabstyle(bogus)
_vl_run msangle__forty_five : scatter mpg weight, msymbol(T) msangle(forty_five)
_vl_run msangle__bogus : scatter mpg weight, msymbol(T) msangle(bogus)
_vl_run msangle__n45 : scatter mpg weight, msymbol(T) msangle(45)
_vl_run msangle__n0 : scatter mpg weight, msymbol(T) msangle(0)
* C15
_vl_run bardefault__bar : bar mpg weight in 1/3, mlabel(make)
_vl_run bardefault__rbar : rbar lo hi weight in 1/3, mlabel(make)
_vl_run bardefault__scatter : scatter mpg weight in 1/3, mlabel(make)
* C14
_vl_run c14__y : rscatter lo hi weight, mlabel(lo)
_vl_run c14__y2 : rscatter lo hi weight, mlabel(hi)
_vl_run c14__x : rscatter lo hi weight, mlabel(weight)
_vl_run c14__other : rscatter lo hi weight, mlabel(make)
_vl_run c14__y_other : rscatter lo hi weight, mlabel(lo make)
_vl_run c14__rcapsym_y : rcapsym lo hi weight, mlabel(lo)
_vl_run c14__rconnected_y : rconnected lo hi weight, mlabel(lo)
_vl_run c14__rbar_y : rbar lo hi weight, mlabel(lo)
_vl_run c14__rarea_y : rarea lo hi weight, mlabel(lo)
_vl_run c14__rcap_y : rcap lo hi weight, mlabel(lo)
_vl_run c14__rline_y : rline lo hi weight, mlabel(lo)
_vl_run c14__rspike_y : rspike lo hi weight, mlabel(lo)
_vl_run c14__rpcap_y : rpcap lo hi mpg weight, mlabel(lo)
_vl_run c14__rpspike_y : rpspike lo hi mpg weight, mlabel(lo)
* cross-checks for S03/S08
_vl_run mwidth__rbar : rbar lo hi weight, mwidth
_vl_run mlalign__declared : scatter mpg weight, mlal(center)
_vl_run mlalign__mla : scatter mpg weight, mla(center)

python:
import hashlib, json, os, re, sys
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


sys.path.insert(0, os.path.join(G("VL_REPO"), "scripts"))
from svg_truth import svg_texts

work = G("VL_WORK")


def lines_of(key):
    try:
        with open(os.path.join(work, key + ".log"), encoding="utf-8",
                  errors="replace") as fh:
            raw = fh.read().splitlines()
    except OSError:
        return [], []
    body = [ln.rstrip() for ln in raw
            if ln.strip() and not ln.startswith(("  name:", "       log:",
                                                 "  log type:", " opened on:",
                                                 "      name:", " closed on:"))
            and not ln.lstrip().startswith(". ")]
    notes = [ln for ln in body if ln.startswith("(note:")]
    errs = [ln for ln in body if not ln.startswith("(note:")
            and not ln.startswith("-----")]
    return notes, errs


def record(key):
    rc = int(G("VL_R_" + key))
    notes, errs = lines_of(key)
    rec = {"rc": rc, "notes": notes, "error": errs[-1] if (rc and errs) else ""}
    if rc == 0:
        svg = os.path.join(work, key + ".svg")
        with open(svg, "rb") as fh:
            rec["svg_sha"] = hashlib.sha256(fh.read()).hexdigest()
        rec["texts"] = [{"text": t["text"], "fill": t["fill"]}
                        for t in svg_texts(svg)]
        rec["ytitle"] = G("VL_Y_" + key) if int(G("VL_YN_" + key) or 0) else None
        rec["xtitle"] = G("VL_X_" + key) if int(G("VL_XN_" + key) or 0) else None
        rec["label_position"] = G("VL_P_" + key)
    return rec


out = {}
for key in G("VL_KEYS").split():
    group, case = key.split("__", 1)
    out.setdefault(group, {})[case] = record(key)
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("VL_VERSION"), "born_date": G("VL_BORN"),
                "dash_commit": commit, "extracted": G("VL_WHEN"),
                "source": "scripts/extract_varlabel_mlabel_truth.do"}
with open(G("VL_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("VL_OUT"))
end
