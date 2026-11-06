*! extract_axis_title_truth.do
*! WP-44 section 44-01 (AX-13, PIC-12, MS-13, MS-11): ground truth for how
*! twoway draws an axis title's textbox sub-options, which way a right-hand
*! y title reads, how repeated suffix/prefix axis-title copies are laid
*! out, and the default axis title over several plot regions, for
*! test/fixtures/axis_title_truth.json.
*!
*! WHY THIS EXISTS
*!
*! dash named orientation(), justification(), box and the rest on
*! xtitle()/ytitle(), turned a right-hand y title to read downward, joined
*! ytitle(A) ytitle(B, suffix) on one line and left an x title out where
*! layers sit on different y axes.  This script records what twoway draws
*! for each, so the tests compare with twoway and never with a guess.
*!
*! Output: test/fixtures/axis_title_truth.json
*!
*! Run with:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_axis_title_truth.do
*!
*! METHOD
*!
*! `_at_run key data cmd' loads the data (auto or sp500), runs cmd under a
*! text log and exports the drawn graph to SVG.  The trailing python:
*! block reads files only (never calls Stata; a backtick is spelled \x60):
*! each key's rc, its log lines, and the SVG's texts, rects and plot
*! region through scripts/svg_truth.py.
*! ---------------------------------------------------------------------------

clear all
set graphics off
set more off
set linesize 255
version 19

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_at_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_at_bad' {
    display as error "extract_axis_title_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _at_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_at_rc' | _rc {
    local _at_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_axis_title_truth.do: `_at_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global AT_REPO "`repo'"
global AT_OUT "${AT_REPO}/test/fixtures/axis_title_truth.json"


local work "`c(tmpdir)'dash_axis_title_probe"
capture mkdir "`work'"
global AT_WORK "`work'"
global AT_BASE "`c(sysdir_base)'"

quietly shell git -C "${AT_REPO}" rev-parse HEAD > "${AT_WORK}/git_head.txt"
global AT_VERSION "`c(stata_version)'"
global AT_BORN "`c(born_date)'"
global AT_WHEN "`c(current_date)' `c(current_time)'"


capture program drop _at_run
program define _at_run
    args key data cmd
    sysuse `data', clear
    set scheme s2color
    capture graph drop u44k
    capture log close atr
    quietly log using "${AT_WORK}/r_`key'.log", text replace name(atr)
    capture noisily `macval(cmd)'
    local rc = _rc
    quietly log close atr
    global AT_R_`key' "`rc'"
    global AT_C_`key' `"`macval(cmd)'"'
    global AT_KEYS "${AT_KEYS} `key'"
    if !`rc' {
        quietly graph export "${AT_WORK}/`key'.svg", replace
    }
end

global AT_KEYS ""
local S "twoway scatter mpg weight"
local Y2 "twoway (scatter mpg weight) (scatter price weight, yaxis(2))"
local N "name(u44k, replace)"

* AX-13: the axis title's textbox sub-options.
_at_run ax13_plain auto `"`S', ytitle("Y") xtitle("X") `N'"'
foreach w in horizontal vertical rhorizontal rvertical hor vert bogus {
    _at_run ax13_or_`w' auto `"`S', ytitle("Y", orientation(`w')) `N'"'
}
_at_run ax13_xor_vertical auto `"`S', xtitle("X", orientation(vertical)) `N'"'
foreach j in left center right {
    _at_run ax13_yjust_`j' auto `"`S', ytitle("Y", justification(`j')) `N'"'
}
foreach j in left right {
    _at_run ax13_xjust_`j' auto `"`S', xtitle("X", justification(`j')) `N'"'
}
foreach p in n s e w ne sw {
    _at_run ax13_place_`p' auto `"`S', ytitle("Y", placement(`p')) `N'"'
}
foreach p in e w n {
    _at_run ax13_xplace_`p' auto `"`S', xtitle("X", placement(`p')) `N'"'
}
foreach a in top bottom {
    _at_run ax13_align_`a' auto `"`S', ytitle("Y", alignment(`a')) `N'"'
}
_at_run ax13_margin_large auto `"`S', ytitle("Y", margin(large)) `N'"'
_at_run ax13_margin_l5 auto `"`S', ytitle("Y", margin(l+5)) `N'"'
_at_run ax13_bmargin_large auto `"`S', ytitle("Y", bmargin(large)) `N'"'
_at_run ax13_two_lines auto `"`S', ytitle(`"A"' `"B"') `N'"'
_at_run ax13_linegap_5 auto `"`S', ytitle(`"A"' `"B"', linegap(5)) `N'"'
_at_run ax13_box auto `"`S', ytitle("Y", box) `N'"'
_at_run ax13_box_colours auto `"`S', ytitle("Y", box fcolor(red) lcolor(blue) lwidth(thick)) `N'"'
_at_run ax13_box_bexpand auto `"`S', ytitle("Y", box bexpand) `N'"'
_at_run ax13_box_wh auto `"`S', ytitle("Y", box width(20) height(10)) `N'"'
_at_run ax13_xbox auto `"`S', xtitle("X", box) `N'"'
_at_run ax13_tstyle_heading auto `"`S', ytitle("Y", tstyle(heading)) `N'"'
_at_run ax13_box_ax2 auto `"`Y2', ytitle("Y", box axis(2)) `N'"'
* PIC-12: which way a right-hand y title reads.
_at_run pic12_y2 auto `"`Y2', `N'"'
_at_run pic12_econ auto `"`S', scheme(economist) `N'"'
_at_run pic12_alt auto `"`S', yscale(alt) `N'"'
_at_run pic12_y3 auto `"twoway (scatter mpg weight) (scatter price weight, yaxis(3)), `N'"'
_at_run pic12_y2orient auto `"`Y2', ytitle("P", axis(2) orientation(horizontal)) `N'"'
* MS-13: suffix and prefix copies of a title option.
foreach k in xtitle ytitle ztitle l1title l2title r1title r2title b1title b2title t1title t2title title {
    _at_run ms13_`k'_suf auto `"`S', `k'(A) `k'(B, suffix) `N'"'
    _at_run ms13_`k'_pre auto `"`S', `k'(A) `k'(B, prefix) `N'"'
}
_at_run ms13_ttitle_suf sp500 `"twoway line close date, ttitle(A) ttitle(B, suffix) `N'"'
_at_run ms13_ttitle_pre sp500 `"twoway line close date, ttitle(A) ttitle(B, prefix) `N'"'
_at_run ms13_ytitle_ax2_suf auto `"`Y2', ytitle(A, axis(2)) ytitle(B, suffix axis(2)) `N'"'
_at_run ms13_ytitle_ax2_pre auto `"`Y2', ytitle(A, axis(2)) ytitle(B, prefix axis(2)) `N'"'
_at_run ms13_xtitle_ax2_suf auto `"twoway (scatter mpg weight) (scatter mpg length, xaxis(2)), xtitle(A, axis(2)) xtitle(B, suffix axis(2)) `N'"'
_at_run ms13_xtitle_ax2_pre auto `"twoway (scatter mpg weight) (scatter mpg length, xaxis(2)), xtitle(A, axis(2)) xtitle(B, prefix axis(2)) `N'"'
_at_run ms13_ttitle_ax2_suf sp500 `"twoway line close date, xaxis(1 2) ttitle(A, axis(2)) ttitle(B, suffix axis(2)) `N'"'
_at_run ms13_ttitle_ax2_pre sp500 `"twoway line close date, xaxis(1 2) ttitle(A, axis(2)) ttitle(B, prefix axis(2)) `N'"'
* MS-11: the default title over plot regions.
_at_run ms11_e12 auto `"twoway (scatter mpg weight) (scatter price length, yaxis(2)), `N'"'
_at_run ms11_e13 auto `"twoway (scatter mpg weight) (scatteri 20 3000 25 4000, yaxis(2)), `N'"'
_at_run ms11_c04 auto `"twoway (scatter mpg weight) (scatter mpg length, yaxis(2)) (scatter price weight, yaxis(2)), `N'"'
_at_run ms11_same auto `"`Y2', `N'"'
_at_run ms11_empty1 auto `"twoway (scatter mpg weight) (scatter mpg length) (scatter price weight, yaxis(2)), `N'"'
_at_run ms11_three auto `"twoway (scatter mpg weight) (scatter price length, yaxis(2)) (scatter turn weight, yaxis(3)), `N'"'
_at_run ms11_x2 auto `"twoway (scatter mpg weight) (scatter mpg length, xaxis(2)), `N'"'
_at_run ms11_hz28 auto `"twoway (scatter mpg weight) (rcap mpg turn weight, horizontal yaxis(2)), `N'"'
_at_run ms11_both auto `"twoway (scatter mpg weight) (scatter price length, yaxis(2) xaxis(2)), `N'"'

python:
import json, os, re, sys
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


sys.path.insert(0, os.path.join(G("AT_REPO"), "scripts"))
import svg_truth

work = G("AT_WORK")


def logged(key):
    with open(os.path.join(work, "r_" + key + ".log"), encoding="utf-8") as fh:
        lines = [ln.rstrip() for ln in fh]
    keep = [" ".join(ln.split()) for ln in lines
            if ln.strip() and not ln.startswith(".")
            and not ln.startswith(">")
            and not ln.lstrip().startswith(("name:", "log:", "log type:",
                                             "opened on:", "closed on:"))
            and not set(ln.strip()) <= set("-")]
    return keep


def svg(key):
    doc = svg_truth.svg_document(os.path.join(work, key + ".svg"))
    return {
        "texts": [{k: t[k] for k in ("x", "y", "anchor", "rotate", "size",
                                     "text")} for t in doc["texts"]],
        "rects": [{k: r[k] for k in ("x", "y", "w", "h", "fill", "stroke")}
                  for r in doc["rects"]],
        "plotregion": doc["plotregion"], "canvas": doc["canvas"],
    }


out = {}
for key in G("AT_KEYS").split():
    rc = int(G("AT_R_" + key))
    row = {"rc": rc, "log": logged(key), "command": G("AT_C_" + key)}
    if rc == 0:
        row.update(svg(key))
    out[key] = row
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("AT_VERSION"), "born_date": G("AT_BORN"),
                "dash_commit": commit, "extracted": G("AT_WHEN"),
                "scheme": "s2color",
                "source": "scripts/extract_axis_title_truth.do"}
with open(G("AT_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
for key in G("AT_KEYS").split():
    p = os.path.join(work, key + ".svg")
    if os.path.exists(p):
        os.remove(p)
print("wrote", G("AT_OUT"))
end
