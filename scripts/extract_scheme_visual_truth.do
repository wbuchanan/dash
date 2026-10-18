*! extract_scheme_visual_truth.do -- what twoway draws under every shipped
*! scheme, for test/fixtures/scheme_visual/truth.json and its PNG renders
*! (read by test/test_scheme_visual_truth.py).
*!
*! For each of Stata's 26 shipped schemes four graphs are drawn from one
*! synthetic dataset (x = 1..20; y1 a zigzag near 1, y2 = y1 + 4,
*! y3 = y1 + 8, so every data segment is diagonal and each series has a
*! band of its own; the variables are labelled LK1..LK3, the legend keys):
*!   sc  twoway (scatter y1 x) (scatter y2 x) (scatter y3 x), title("TTL")
*!       subtitle("SUB") note("NTE") xtitle("XTL") ytitle("YTL")
*!   ln  twoway (line y1 x) (line y2 x) (line y3 x)
*!   cn  twoway (connected y1 x) (connected y2 x) (connected y3 x)
*!   hi  twoway histogram mpg (sysuse auto)
*! each exported to SVG (measured by scripts/svg_scheme_visual.py: the
*! graph size, the graph and plot regions, the legend box, the text sizes
*! and colours, the p1-p3 markers and lines, the histogram's bars) and the
*! sc, ln and hi graphs to PNG at width(400) (<s>.png, <s>_line.png,
*! <s>_hist.png).  The symbol-size ladder the markers are named by is
*! measured too: one scatter under s2color per msize() name.
*!
*! Settings are session-only (scheme() on each command); nothing is set
*! permanently and graph set is never called.
*!
*! Run (never the GUI; the slot wrapper of scripts/stata_slot.sh):
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_scheme_visual_truth.do
*! The trailing python: block reads files and macros only; it never calls
*! Stata, and spells a backtick \x60.
*! ---------------------------------------------------------------------------
clear all
set graphics off
set more off
set linesize 200
* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zv_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zv_bad' {
    display as error "extract_scheme_visual_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
if _rc {
    local _zv_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_scheme_visual_truth.do: `_zv_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZV_REPO "`repo'"
global ZV_OUT  "`repo'/test/fixtures/scheme_visual"
tempfile zvwork
local work "`zvwork'_d"
capture mkdir "`work'"
global ZV_WORK "`work'"
global ZV_SVER = c(stata_version)
global ZV_BORN "`c(born_date)'"
global ZV_DATE "`c(current_date)'"

tempfile zvgitrev
quietly shell git -C "${ZV_REPO}" rev-parse HEAD > "`zvgitrev'"
tempname zvgfh
file open `zvgfh' using "`zvgitrev'", read text
file read `zvgfh' zvgitline
file close `zvgfh'
local dash_commit = trim(`"`zvgitline'"')
capture assert ustrregexm(`"`dash_commit'"', "^[0-9a-f]{40}$")
if _rc {
    display as error "extract_scheme_visual_truth.do: git rev-parse HEAD did not print a 40-character commit"
    exit 498
}
global ZV_COMMIT "`dash_commit'"

local schemes stcolor stcolor_alt stgcolor stmono1 stmono2 stsj s2color s2mono s2gcolor s1color s1mono s1rcolor economist sj s2manual s1manual s2gmanual s2color8 sttrans stgcolor_alt meta stcolor_meta stcolor_mv stcoloralias stgcolor_meta stgcolor_mv
global ZV_SCHEMES "`schemes'"
local ladder vtiny tiny vsmall small medsmall medium medlarge large vlarge huge vhuge ehuge
global ZV_LADDER "`ladder'"

* The histogram's data first: its PNG and SVG are drawn from auto.
sysuse auto, clear
foreach s of local schemes {
    twoway histogram mpg, scheme(`s')
    graph export "`work'/hi_`s'.svg", replace
    graph export "${ZV_OUT}/`s'_hist.png", width(400) replace
}

clear
quietly set obs 20
generate double x = _n
generate double y1 = 1 + 0.5*mod(_n, 2) + 0.02*_n
generate double y2 = y1 + 4
generate double y3 = y1 + 8
label variable y1 "LK1"
label variable y2 "LK2"
label variable y3 "LK3"
foreach s of local schemes {
    twoway (scatter y1 x) (scatter y2 x) (scatter y3 x), title("TTL") subtitle("SUB") note("NTE") xtitle("XTL") ytitle("YTL") scheme(`s')
    graph export "`work'/sc_`s'.svg", replace
    graph export "${ZV_OUT}/`s'.png", width(400) replace
    twoway (line y1 x) (line y2 x) (line y3 x), scheme(`s')
    graph export "`work'/ln_`s'.svg", replace
    graph export "${ZV_OUT}/`s'_line.png", width(400) replace
    twoway (connected y1 x) (connected y2 x) (connected y3 x), scheme(`s')
    graph export "`work'/cn_`s'.svg", replace
}
foreach z of local ladder {
    twoway scatter y1 x, msize(`z') scheme(s2color)
    graph export "`work'/ms_`z'.svg", replace
}

python:
import json, os, sys
from sfi import Macro
REPO = Macro.getGlobal("ZV_REPO")
sys.path.insert(0, os.path.join(REPO, "scripts"))
import svg_scheme_visual as sv

doc = sv.measure_all(Macro.getGlobal("ZV_WORK"),
                     Macro.getGlobal("ZV_SCHEMES").split(),
                     Macro.getGlobal("ZV_LADDER").split())
doc = dict({"_meta": {
    "stata_version": Macro.getGlobal("ZV_SVER"),
    "born_date": Macro.getGlobal("ZV_BORN"),
    "extracted": Macro.getGlobal("ZV_DATE"),
    "source": "scripts/extract_scheme_visual_truth.do",
    "dash_commit": Macro.getGlobal("ZV_COMMIT"),
    "units": "SVG user units, 720 per inch; pct_of_min_dim = units / min(viewBox W, H) * 100",
    "method": ("x = 1..20, y1 = 1 + 0.5*mod(_n,2) + 0.02*_n, y2 = y1 + 4, "
               "y3 = y1 + 8; scatter, line and connected of y1-y3 on x and "
               "twoway histogram mpg of auto, under each scheme, exported "
               "to SVG and read by scripts/svg_scheme_visual.py"),
}}, **doc)
with open(os.path.join(Macro.getGlobal("ZV_OUT"), "truth.json"), "w",
          encoding="utf-8") as fh:
    json.dump(doc, fh, indent=1)
    fh.write("\n")
print("wrote %d schemes" % len(doc["schemes"]))
end

local svgs : dir "`work'" files "*.svg"
foreach f of local svgs {
    erase "`work'/`f'"
}
display as text "extract_scheme_visual_truth: done"
