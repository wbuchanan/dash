*! extract_tick_style_truth.do
*! WP-44 section 44-02 (AX-5, AX-6, AX-8, AX-14, AX-15): ground truth for
*! how twoway draws custom ticks, tick-option gridlines, the label words
*! labelminlen()/showlabels/pgmgrid/style(), the tick, tickset, grid,
*! text and line style names, nogextend, two tick lengths, reference
*! lines outside the scale, string and hex axis formats, an axis past
*! Stata's dates and the plot-region margin, for
*! test/fixtures/tick_style_truth.json.
*!
*! WHY THIS EXISTS
*!
*! dash took these sub-options without drawing them, or drew them in
*! another look.  This script records what twoway draws and prints for
*! each, so the tests compare with twoway and never with a guess.
*!
*! Output: test/fixtures/tick_style_truth.json
*!
*! Run with:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_tick_style_truth.do
*!
*! METHOD
*!
*! `_ts_run key data scheme cmd' loads the data set, sets the scheme for
*! the session only, runs cmd under a text log and exports the drawn
*! graph to SVG.  The trailing python: block reads files only (never
*! calls Stata): each key's rc, its log lines, and the SVG's texts (with
*! fill, size and the text as written, so U+00A0 padding is kept), lines,
*! circles and plot region through scripts/svg_truth.py.  Keys differ in
*! more than case: their log and SVG files share one folder, and the
*! file system may not tell %16H's from %16h's.
*! ---------------------------------------------------------------------------

clear all
set graphics off
set more off
set linesize 255
version 19

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_ts_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_ts_bad' {
    display as error "extract_tick_style_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _ts_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_ts_rc' | _rc {
    local _ts_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_tick_style_truth.do: `_ts_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global TS_REPO "`repo'"
global TS_OUT "${TS_REPO}/test/fixtures/tick_style_truth.json"

local work "`c(tmpdir)'dash_tick_style_probe"
capture mkdir "`work'"
global TS_WORK "`work'"

quietly shell git -C "${TS_REPO}" rev-parse HEAD > "${TS_WORK}/git_head.txt"
global TS_VERSION "`c(stata_version)'"
global TS_BORN "`c(born_date)'"
global TS_WHEN "`c(current_date)' `c(current_time)'"

capture program drop _ts_run
program define _ts_run
    args key data scheme cmd
    sysuse `data', clear
    set scheme `scheme'
    capture graph drop u442k
    capture log close tsr
    quietly log using "${TS_WORK}/r_`key'.log", text replace name(tsr)
    capture noisily `macval(cmd)'
    local rc = _rc
    quietly log close tsr
    global TS_R_`key' "`rc'"
    global TS_C_`key' `"`macval(cmd)'"'
    global TS_D_`key' "`data'"
    global TS_S_`key' "`scheme'"
    global TS_KEYS "${TS_KEYS} `key'"
    if !`rc' {
        quietly graph export "${TS_WORK}/`key'.svg", replace
    }
end

global TS_KEYS ""
local S "twoway scatter mpg weight"
local N "name(u442k, replace)"

foreach sch in stcolor s2color {
    _ts_run plain_`sch' auto `sch' `"`S', `N'"'
}

* AX-5: custom ticks.
_ts_run ax5_add_custom_lab auto stcolor `"`S', ylabel(25 "x", add custom labcolor(red) labsize(large)) `N'"'
_ts_run ax5_add_custom_grid auto stcolor `"`S', ylabel(25, add custom labcolor(red) grid glcolor(red)) `N'"'
_ts_run ax5_custom_full auto stcolor `"`S', ylabel(10 20 30 40, custom labcolor(red)) `N'"'
_ts_run ax5_empty_custom auto stcolor `"`S', ylabel(, custom labcolor(red)) `N'"'
_ts_run ax5_empty_plain auto stcolor `"`S', ylabel(, custom) `N'"'
_ts_run ax5_custom_tick auto stcolor `"`S', ylabel(25, add custom tlcolor(red) tlength(*3)) `N'"'
_ts_run ax5_xlabel_custom auto stcolor `"`S', xlabel(3000 "M", add custom angle(45)) `N'"'
_ts_run ax5_add_plain auto stcolor `"`S', ylabel(25 "x", add labcolor(red)) `N'"'
_ts_run ax5_rule_custom auto stcolor `"`S', ylabel(10(10)40, custom labcolor(red)) `N'"'
_ts_run ax5_count_custom auto stcolor `"`S', ylabel(#5, custom labcolor(red)) `N'"'
_ts_run ax5_minmax_custom auto stcolor `"`S', ylabel(minmax, custom labcolor(red)) `N'"'
_ts_run ax5_none_custom auto stcolor `"`S', ylabel(none, custom labcolor(red)) `N'"'
_ts_run ax5_empty_grid auto stcolor `"`S', ylabel(, custom grid glcolor(red)) `N'"'
_ts_run ax5_empty_angle auto stcolor `"`S', ylabel(, custom angle(45)) `N'"'
_ts_run ax5_empty_nolabels auto stcolor `"`S', ylabel(, custom nolabels) `N'"'
_ts_run ax5_empty_format auto stcolor `"`S', ylabel(, custom format(%9.1f)) `N'"'
_ts_run ax5_empty_tlcolor auto stcolor `"`S', ylabel(, custom tlcolor(red)) `N'"'
_ts_run ax5_ytick_custom auto stcolor `"`S', ytick(25, add custom tlcolor(red)) `N'"'
_ts_run ax5_ytick_empty auto stcolor `"`S', ytick(, custom tlcolor(red)) `N'"'
_ts_run ax5_xlabel_empty auto stcolor `"`S', xlabel(, custom labcolor(red)) `N'"'

* AX-6: tick-option gridlines.
foreach sch in stcolor s2color {
    _ts_run ax6_xtick_`sch' auto `sch' `"`S', xtick(2500 3500, grid) `N'"'
    _ts_run ax6_xmtick_`sch' auto `sch' `"`S', xmtick(2500 3500, grid) `N'"'
    _ts_run ax6_xlabel_`sch' auto `sch' `"`S', xlabel(, grid) `N'"'
}
_ts_run ax6_ytick_n auto stcolor `"`S', ytick(#10, grid) `N'"'

* AX-8: the label words.
_ts_run ax8_minlen_y auto stcolor `"`S', ylabel(, labelminlen(10)) `N'"'
_ts_run ax8_minlen_x auto stcolor `"`S', xlabel(, labelminlen(10)) `N'"'
_ts_run ax8_noshowlabels auto stcolor `"`S', ylabel(, noshowlabels) `N'"'
_ts_run ax8_showlabels auto stcolor `"`S', ylabel(, showlabels) `N'"'
_ts_run ax8_order_a auto stcolor `"`S', ylabel(, showlabels nolabels) `N'"'
_ts_run ax8_order_b auto stcolor `"`S', ylabel(, nolabels showlabels) `N'"'
_ts_run ax8_order_c auto stcolor `"`S', ylabel(, labels noshowlabels) `N'"'
_ts_run ax8_order_d auto stcolor `"`S', ylabel(, noshowlabels labels) `N'"'
_ts_run ax8_nopgmgrid auto stcolor `"`S', ylabel(, nopgmgrid) `N'"'
_ts_run ax8_pgmgrid auto stcolor `"`S', ylabel(, nogrid pgmgrid) `N'"'
_ts_run ax8_pgmgrid_x auto stcolor `"`S', xlabel(, pgmgrid) `N'"'
_ts_run ax8_grid_nopgmgrid auto stcolor `"`S', ylabel(, grid nopgmgrid) `N'"'
_ts_run ax8_style_nolabel auto stcolor `"`S', ylabel(, style(major_vert_nolabel)) `N'"'
_ts_run ax8_style_notick auto stcolor `"`S', ylabel(, style(major_vert_notick)) `N'"'
_ts_run ax8_style_bogus auto stcolor `"`S', ylabel(, style(bogus)) `N'"'

* AX-14: style names and nogextend.
_ts_run ax14_tstyle_notick auto stcolor `"`S', ylabel(, tstyle(major_notick)) `N'"'
_ts_run ax14_tstyle_nolabel auto stcolor `"`S', ylabel(, tstyle(major_nolabel)) `N'"'
_ts_run ax14_tstyle_bogus auto stcolor `"`S', ylabel(, tstyle(bogus)) `N'"'
_ts_run ax14_labstyle_heading auto stcolor `"`S', ylabel(, labstyle(heading)) `N'"'
_ts_run ax14_labstyle_small_body auto stcolor `"`S', ylabel(, labstyle(small_body)) `N'"'
_ts_run ax14_gstyle_dot auto stcolor `"`S', ylabel(, grid gstyle(dot)) `N'"'
_ts_run ax14_tlstyle_foreground auto stcolor `"`S', ylabel(, tlstyle(foreground)) `N'"'
_ts_run ax14_glstyle_refline auto stcolor `"`S', ylabel(, grid glstyle(refline)) `N'"'
_ts_run ax14_grid_nogextend auto stcolor `"`S', ylabel(, grid nogextend) `N'"'
_ts_run ax14_grid_gextend auto stcolor `"`S', ylabel(, grid) `N'"'

* AX-15: tick lengths, reference lines, formats, past dates, margins.
_ts_run ax15_ticklens auto stcolor `"`S', xtick(2000 4000) xmtick(3000) `N'"'
* Tick-only and minor positions away from the labels, on x and on y.
_ts_run ax15_ticklens_x auto stcolor `"`S', xtick(2500 4500) xmtick(3500) `N'"'
_ts_run ax15_ticklens_y auto stcolor `"`S', ytick(15 25) ymtick(35) `N'"'
_ts_run ax15_refl_out auto stcolor `"`S', xline(5100) yline(45) `N'"'
_ts_run ax15_refl_out_log auto stcolor `"`S', xscale(log) xline(5100) `N'"'
_ts_run ax15_refl_far auto stcolor `"`S', xline(10000) `N'"'
_ts_run ax15_fmt_x auto stcolor `"`S', ylabel(, format(%21x)) `N'"'
_ts_run ax15_fmt_hexhi auto stcolor `"`S', ylabel(, format(%16H)) `N'"'
_ts_run ax15_fmt_hexlo auto stcolor `"`S', ylabel(, format(%16h)) `N'"'
_ts_run ax15_fmt_s auto stcolor `"`S', ylabel(, format(%12s)) `N'"'
_ts_run ax15_past auto stcolor `"twoway scatteri 1300 99999999, xscale(range(0 99999999)) xlabel(, format(%td)) `N'"'
_ts_run ax15_margin_5 auto stcolor `"`S', xsize(5.5) ysize(4) `N'"'
_ts_run ax15_margin_11 auto stcolor `"`S', xsize(11) ysize(4) `N'"'
_ts_run ax15_past_browser sp500 stcolor `"twoway (line close date) (scatteri 1300 1000000000), `N'"'
* AX-15: the hexadecimal, IEEE and string formats over a list of values
* (zero, a fraction, negatives, a subnormal, large and small numbers),
* written in the list's order; %10x and %12H are refused.
local I "twoway scatteri 0 0 1 1"
local LX "0 0.1 -0.5 10 33.3333333 65536 1e-310 1e20 -2.5e-8"
local LS "0 0.1 -0.5 10 33.3333333 1234567.891 1234567890 -123456789 0.000012345 123456789012"
_ts_run ax15_fmtl_x21 auto stcolor `"`I', ylabel(`LX', format(%21x)) `N'"'
_ts_run ax15_fmtl_xl auto stcolor `"`I', ylabel(`LX', format(%-21x)) `N'"'
_ts_run ax15_fmtl_h16 auto stcolor `"`I', ylabel(`LX', format(%16H)) `N'"'
_ts_run ax15_fmtl_h8 auto stcolor `"`I', ylabel(`LX', format(%8H)) `N'"'
_ts_run ax15_fmtl_l16 auto stcolor `"`I', ylabel(`LX', format(%16L)) `N'"'
_ts_run ax15_fmtl_l8 auto stcolor `"`I', ylabel(`LX', format(%8L)) `N'"'
_ts_run ax15_fmtl_hl auto stcolor `"`I', ylabel(`LX', format(%-16H)) `N'"'
_ts_run ax15_fmtl_s auto stcolor `"`I', ylabel(`LS', format(%12s)) `N'"'
_ts_run ax15_fmtl_sl auto stcolor `"`I', ylabel(`LS', format(%-5s)) `N'"'
_ts_run ax15_fmtl_bad10x auto stcolor `"`I', ylabel(`LX', format(%10x)) `N'"'
_ts_run ax15_fmtl_bad12h auto stcolor `"`I', ylabel(`LX', format(%12H)) `N'"'

python:
import json, os, sys
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


sys.path.insert(0, os.path.join(G("TS_REPO"), "scripts"))
import svg_truth

work = G("TS_WORK")


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
    keep_l = ("x1", "y1", "x2", "y2", "stroke", "width", "dasharray")
    return {
        "texts": [{k: t[k] for k in ("x", "y", "anchor", "rotate", "size",
                                     "fill", "text", "raw")}
                  for t in doc["texts"]],
        "hlines": [{k: d[k] for k in keep_l} for d in doc["hlines"]],
        "vlines": [{k: d[k] for k in keep_l} for d in doc["vlines"]],
        "diaglines": [{k: d[k] for k in keep_l} for d in doc["diaglines"]],
        "circles": ([{k: c[k] for k in ("cx", "cy", "r")}
                     for c in doc["circles"]]
                    if key.startswith("ax15_past") else []),
        "plotregion": doc["plotregion"], "canvas": doc["canvas"],
    }


out = {}
for key in G("TS_KEYS").split():
    rc = int(G("TS_R_" + key))
    row = {"rc": rc, "log": logged(key), "command": G("TS_C_" + key),
           "data": G("TS_D_" + key), "scheme": G("TS_S_" + key)}
    if rc == 0:
        row.update(svg(key))
    out[key] = row

pb = out.get("ax15_past_browser", {})
drawn = 0
if pb.get("rc") == 0 and pb.get("plotregion"):
    pr = pb["plotregion"]
    left, right = pr["left"], pr["right"]
    for c in pb.get("circles", []):
        if c["cx"] is not None and c["cx"] >= left + 0.9 * (right - left):
            drawn = 1
pb["past_browser_drawn"] = drawn

try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("TS_VERSION"), "born_date": G("TS_BORN"),
                "dash_commit": commit, "extracted": G("TS_WHEN"),
                "source": "scripts/extract_tick_style_truth.do"}
with open(G("TS_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True, ensure_ascii=False)
    fh.write("\n")
for key in G("TS_KEYS").split():
    p = os.path.join(work, key + ".svg")
    if os.path.exists(p):
        os.remove(p)
print("wrote", G("TS_OUT"))
end
