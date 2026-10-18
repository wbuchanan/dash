*! extract_chrome_truth.do
*! WP-30 section 15 (P1.2a): twoway's chrome for every shipped scheme, for
*! test/fixtures/chrome_truth.json.
*!
*! Each probe draws a scatter of auto under one scheme, with the plot-region
*! sentinel plotregion(lcolor("1 2 3") lstyle(foreground)) that
*! scripts/svg_chrome.py finds the plot region by, exports it to SVG, and
*! records where the title, subtitle, note, caption and axis titles sit,
*! the tick labels' rotation and side, the ticks, the axis lines and the
*! grids (scripts/svg_chrome.py; lengths in Stata units, rs = min(viewBox
*! W, H)/100).
*!
*! Run with:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_chrome_truth.do
*!
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
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_chrome_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
if _rc {
    local _zr_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_chrome_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1
global ZC_REPO "`repo'"
global ZC_OUT  "${ZC_REPO}/test/fixtures/chrome_truth.json"
tempfile zcwork
local work "`zcwork'_d"
capture mkdir "`work'"
global ZC_WORK "`work'"

global ZC_SVER   = c(stata_version)
global ZC_BORN   = c(born_date)
global ZC_DATE   = c(current_date)

* Provenance stamp (D12), as extract_text_truth.do captures it.
tempfile zcgitrev
quietly shell git -C "${ZC_REPO}" rev-parse HEAD > "`zcgitrev'"
tempname zcgfh
file open `zcgfh' using "`zcgitrev'", read text
file read `zcgfh' zcgitline
file close `zcgfh'
local dash_commit = trim(`"`zcgitline'"')
capture assert ustrregexm(`"`dash_commit'"', "^[0-9a-f]{40}$")
if _rc {
    display as error "extract_chrome_truth.do: git rev-parse HEAD did not print a 40-character commit"
    exit 498
}
global ZC_COMMIT "`dash_commit'"

local sent `"plotregion(lcolor("1 2 3") lstyle(foreground))"'
local schemes stcolor stcolor_alt stgcolor stmono1 stmono2 stsj s2color s2mono s2gcolor s1color s1mono s1rcolor economist sj s2manual s1manual s2gmanual s2color8 sttrans stgcolor_alt meta stcolor_meta stcolor_mv stcoloralias stgcolor_meta stgcolor_mv
global ZC_SCHEMES "`schemes'"

sysuse auto, clear
foreach s of local schemes {
    twoway scatter mpg weight, title("TTL") subtitle("SUB") note("NTE") caption("CAP") xtitle("XTL") ytitle("YTL") `sent' scheme(`s')
    graph export "`work'/ck_`s'.svg", replace
}
foreach s in economist s2color {
    twoway (scatter mpg weight) (scatter price weight, yaxis(2)), title("TTL") `sent' scheme(`s')
    graph export "`work'/ck_`s'_y2.svg", replace
}
twoway scatter mpg weight, ylabel(, angle(horizontal)) `sent' scheme(s2color)
graph export "`work'/ck_s2color_yh.svg", replace
foreach s in stcolor s2color {
    twoway scatter mpg weight, xlabel(, grid) `sent' scheme(`s')
    graph export "`work'/ck_`s'_xgrid.svg", replace
}
global ZC_EXTRA "economist_y2 s2color_y2 s2color_yh stcolor_xgrid s2color_xgrid"

python:
import json, os, sys
from sfi import Macro
REPO = Macro.getGlobal("ZC_REPO")
sys.path.insert(0, os.path.join(REPO, "scripts"))
import svg_chrome as sc

WORK = Macro.getGlobal("ZC_WORK")
names = Macro.getGlobal("ZC_SCHEMES").split()
extra = Macro.getGlobal("ZC_EXTRA").split()

def record(path):
    reg = sc.svg_region(path)
    if reg is None:
        raise RuntimeError("no sentinel in " + path)
    texts = {}
    for t in ("TTL", "SUB", "NTE", "CAP", "XTL", "YTL"):
        p = sc.svg_text_place(path, t, reg)
        if p is not None:
            texts[t] = p
    y_sides = sc.svg_label_side(path, "y", reg)
    rec = {"texts": texts,
           "label_rotation": {"x": sc.svg_label_rotation(path, "x", reg)},
           "label_side": {}, "ticks": {}, "axis_line": {}, "grid": {},
           "minor_ticks": {}}
    rec["ticks"]["x"] = sc.svg_ticks(path, "bottom", reg)
    rec["axis_line"]["x"] = sc.svg_axis_line(path, "bottom", reg)
    two = len(y_sides) == 2
    if two:
        # Axis 1's labels sit on the scheme's side; axis 2 opposite.  The
        # probe's y2 is price (thousands), axis 1 mpg (tens).
        for side in y_sides:
            labs = [t for t in sc._labels(path, "y", reg)
                    if sc._label_side_of(t, "y", reg) == side]
            big = max(abs(float(t["text"].replace(",", "").replace("−", "-")))
                      for t in labs)
            role = "y2" if big >= 1000 else "y"
            edge = side
            rec["label_side"][role] = side
            rec["label_rotation"][role] = sc.svg_label_rotation(path, "y", reg, side)
            rec["ticks"][role] = sc.svg_ticks(path, edge, reg)
            rec["axis_line"][role] = sc.svg_axis_line(path, edge, reg)
    else:
        side = y_sides[0] if y_sides else "left"
        rec["label_side"]["y"] = side
        rec["label_rotation"]["y"] = sc.svg_label_rotation(path, "y", reg)
        rec["ticks"]["y"] = sc.svg_ticks(path, side, reg)
        rec["axis_line"]["y"] = (sc.svg_axis_line(path, side, reg))
    for ax in ("x", "y"):
        rec["grid"][ax] = sc.svg_grid(path, ax, reg)
        rec["minor_ticks"][ax] = (rec["ticks"].get(ax) or {}).get("minor", 0)
    return rec

out = {"_meta": {
    "stata_version": Macro.getGlobal("ZC_SVER"),
    "born_date": Macro.getGlobal("ZC_BORN"),
    "extracted": Macro.getGlobal("ZC_DATE"),
    "source": "scripts/extract_chrome_truth.do",
    "dash_commit": Macro.getGlobal("ZC_COMMIT"),
    "units": "rs = min(viewBox W, H)/100",
    "method": ("twoway scatter mpg weight of auto with the plot-region "
               "sentinel plotregion(lcolor(\"1 2 3\") lstyle(foreground)), "
               "exported to SVG and read by scripts/svg_chrome.py"),
}}
for n in names:
    out[n] = record(os.path.join(WORK, "ck_" + n + ".svg"))
for n in extra:
    out[n] = record(os.path.join(WORK, "ck_" + n + ".svg"))
with open(Macro.getGlobal("ZC_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=False)
    fh.write("\n")
print("wrote %d records" % (len(out) - 1))
end

local svgs : dir "`work'" files "*.svg"
foreach f of local svgs {
    erase "`work'/`f'"
}
display as text "extract_chrome_truth: done"
