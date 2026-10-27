*! extract_axis_look_truth.do
*! WP-31 section 33 (D6, D7, E6, D1c): ground truth for how twoway draws the
*! axis label, tick and grid sub-options, the axis-scale look and the
*! line-width edges, for test/fixtures/axis_look_truth.json.
*!
*! WHY THIS EXISTS
*!
*! dash named labgap(), alternate, the tick and grid line looks,
*! outergap(), noextend and lstyle() in a note where twoway draws them,
*! read two yscale(alt) as one, and multiplied a line width after the
*! 0.3 pt floor.  This script records what twoway draws and prints for
*! each, so the tests compare with twoway and never with a guess.
*!
*! Output: test/fixtures/axis_look_truth.json
*!
*! Run with:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_axis_look_truth.do
*!
*! METHOD
*!
*! `_al_run key cmd' reloads auto, runs cmd under a text log and exports
*! the drawn graph to SVG.  The trailing python: block reads files only
*! (never calls Stata; a backtick is spelled \x60): each key's rc, its
*! log lines, and the SVG's texts, lines and plot region through
*! scripts/svg_truth.py.  A scheme whose xyline width is vvthin is
*! written to the work directory for the lw.* keys.
*! ---------------------------------------------------------------------------

clear all
set graphics off
set more off
set linesize 255
version 19

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_al_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_al_bad' {
    display as error "extract_axis_look_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _al_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_al_rc' | _rc {
    local _al_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_axis_look_truth.do: `_al_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global AL_REPO "`repo'"
global AL_OUT "${AL_REPO}/test/fixtures/axis_look_truth.json"


local work "`c(tmpdir)'dash_axis_look_probe"
capture mkdir "`work'"
global AL_WORK "`work'"
global AL_BASE "`c(sysdir_base)'"

quietly shell git -C "${AL_REPO}" rev-parse HEAD > "${AL_WORK}/git_head.txt"
global AL_VERSION "`c(stata_version)'"
global AL_BORN "`c(born_date)'"
global AL_WHEN "`c(current_date)' `c(current_time)'"

* The vvthin scheme: s2color with linewidth xyline vvthin and no #include.
python:
import os
from sfi import Macro
src = os.path.join(Macro.getGlobal("AL_BASE"), "s", "scheme-s2color.scheme")
with open(src, encoding="latin-1") as fh:
    lines = fh.read().splitlines()
out = []
for ln in lines:
    if ln.lstrip().startswith("#include"):
        continue
    if ln.split()[:2] == ["linewidth", "xyline"]:
        ln = "linewidth xyline       vvthin"
    out.append(ln)
with open(os.path.join(Macro.getGlobal("AL_WORK"), "scheme-alvvthin.scheme"),
          "w", encoding="latin-1") as fh:
    fh.write("\n".join(out) + "\n")
end
adopath ++ "${AL_WORK}"

capture program drop _al_run
program define _al_run
    args key cmd
    sysuse auto, clear
    set scheme s2color
    capture graph drop u33k
    capture log close alr
    quietly log using "${AL_WORK}/r_`key'.log", text replace name(alr)
    capture noisily `macval(cmd)'
    local rc = _rc
    quietly log close alr
    global AL_R_`key' "`rc'"
    global AL_C_`key' `"`macval(cmd)'"'
    global AL_KEYS "${AL_KEYS} `key'"
    if !`rc' {
        quietly graph export "${AL_WORK}/`key'.svg", replace
    }
end

global AL_KEYS ""
local S "twoway scatter mpg weight"
local N "name(u33k, replace)"

* D6: label, tick and grid sub-options.
_al_run plain `"`S', `N'"'
foreach g in small large 3 {
    _al_run labgap_`g' `"`S', ylabel(, labgap(`g')) `N'"'
}
foreach j in left center right {
    _al_run labjust_`j' `"`S', ylabel(, labjustification(`j')) `N'"'
}
foreach a in top middle bottom baseline {
    _al_run labalign_`a' `"`S', ylabel(, labalignment(`a')) `N'"'
}
_al_run alt_default `"`S', xlabel(1500(500)5000, alternate) `N'"'
_al_run alt_altgap_large `"`S', xlabel(1500(500)5000, alternate altgap(large)) `N'"'
_al_run tl_width_thick `"`S', ylabel(, tlwidth(thick)) `N'"'
_al_run tl_color_red `"`S', ylabel(, tlcolor(red)) `N'"'
_al_run tl_pattern_dash `"`S', ylabel(, tlpattern(dash)) `N'"'
_al_run tick_tlwidth_thick `"`S', ytick(15 25 35, tlwidth(thick) tlcolor(red)) `N'"'
_al_run gl_width_thick `"`S', ylabel(, grid glwidth(thick)) `N'"'
_al_run gl_color_red `"`S', ylabel(, grid glcolor(red)) `N'"'
_al_run gl_pattern_dash `"`S', ylabel(, grid glpattern(dash)) `N'"'
_al_run gl_color_nogrid `"`S', xlabel(, glcolor(red)) `N'"'
_al_run ge_default `"`S', ylabel(10 20 30 40, grid) `N'"'
_al_run ge_nogmin_nogmax `"`S', ylabel(10 20 30 40, grid nogmin nogmax) `N'"'
_al_run ge_gmin_gmax `"`S', ylabel(10 20 30 40, grid gmin gmax) `N'"'
_al_run ge_range `"`S', ylabel(10(10)40, grid) yscale(range(10 40)) `N'"'
_al_run ge_range_nogmin `"`S', ylabel(10(10)40, grid nogmin nogmax) yscale(range(10 40)) `N'"'
_al_run ge_range_gmin `"`S', ylabel(10(10)40, grid gmin gmax) yscale(range(10 40)) `N'"'
_al_run ge_list_nogmin `"`S', ylabel(10 20 30 40, grid nogmin) `N'"'
_al_run ge_list_nogmax `"`S', ylabel(10 20 30 40, grid nogmax) `N'"'
_al_run ge_auto_nogmin `"`S', ylabel(, grid nogmin) `N'"'
_al_run ge_auto_nogmax `"`S', ylabel(, grid nogmax) `N'"'
_al_run ge_count_nogmin `"`S', ylabel(#3, grid nogmin nogmax) `N'"'
_al_run gx_default `"`S', ylabel(, grid) `N'"'
_al_run gx_gextend `"`S', ylabel(, grid gextend) `N'"'
_al_run gx_nogextend `"`S', ylabel(, grid nogextend) `N'"'
_al_run custom_with `"`S', ylabel(10 20 30, custom) `N'"'
_al_run custom_without `"`S', ylabel(10 20 30) `N'"'
_al_run dh_ylabel `"`S', ylabel(##5) `N'"'
_al_run dh_ytick `"`S', ytick(##5) `N'"'
_al_run dh_xlabel `"`S', xlabel(##5) `N'"'
_al_run dh_ylabel_list `"`S', ylabel(##5 20 30) `N'"'
_al_run minmax_two `"twoway scatter mpg weight || scatter trunk weight, ylabel(minmax) `N'"'
local i 0
foreach f in `"`"a"'"' `"1 "a" "b""' `"none 1 2"' `"minmax 1"' `"#3 #4"' `"1(1)"' `","' `"1 "a" 2"' `"#3 20"' `"none"' {
    local ++i
    _al_run ref_`i' `"`S', ylabel(`f') `N'"'
}
* D7: the axis-scale look.
_al_run sc_outergap_5 `"`S', yscale(outergap(5)) `N'"'
_al_run sc_xoutergap_5 `"`S', xscale(outergap(5)) `N'"'
_al_run sc_noextend `"`S', yscale(noextend) `N'"'
_al_run sc_extend `"`S', yscale(extend) `N'"'
_al_run sc_fextend `"`S', yscale(fextend) `N'"'
_al_run sc_fill `"`S', yscale(fill) `N'"'
_al_run sc_lstyle_grid `"`S', yscale(lstyle(grid)) `N'"'
_al_run sc_alt1 `"`S', yscale(alt) `N'"'
_al_run sc_alt2 `"`S', yscale(alt) yscale(alt) `N'"'
_al_run sc_alt2one `"`S', yscale(alt alt) `N'"'
_al_run z_zlabel `"`S', zlabel(, labsize(small)) `N'"'
_al_run z_zscale `"`S', zscale(alt) `N'"'
* E6: line widths.
_al_run lw_star2_medium `"`S', xline(3000, lwidth(*2)) `N'"'
_al_run lw_medium `"`S', xline(3000) `N'"'
_al_run lw_bound_10000 `"`S', xline(3000, lwidth(10000)) `N'"'
_al_run lw_bound_20000 `"`S', xline(3000, lwidth(20000)) `N'"'
_al_run lw_star2_vvthin `"`S', xline(3000, lwidth(*2)) scheme(alvvthin) `N'"'
_al_run lw_vvthin `"`S', xline(3000) scheme(alvvthin) `N'"'
_al_run lw_star10_vvthin `"`S', xline(3000, lwidth(*10)) scheme(alvvthin) `N'"'
* D1c: axis-2 minor-label angle().
_al_run m2_angle_y `"twoway scatter mpg weight, yaxis(1 2) ymlabel(##2, axis(2) angle(400)) `N'"'
_al_run m2_angle_x `"twoway scatter mpg weight, xaxis(1 2) xmlabel(##2, axis(2) angle(400)) `N'"'
_al_run m2_tick_y `"twoway scatter mpg weight, yaxis(1 2) ymtick(##2, axis(2) angle(400)) `N'"'
_al_run m1_angle_y `"`S', ymlabel(##2, angle(400)) `N'"'

python:
import json, os, re, sys
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


sys.path.insert(0, os.path.join(G("AL_REPO"), "scripts"))
import svg_truth

work = G("AL_WORK")


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
                                     "text")} for t in doc["texts"]],
        "hlines": [{k: d[k] for k in keep_l} for d in doc["hlines"]],
        "vlines": [{k: d[k] for k in keep_l} for d in doc["vlines"]],
        "plotregion": doc["plotregion"], "canvas": doc["canvas"],
    }


out = {}
for key in G("AL_KEYS").split():
    rc = int(G("AL_R_" + key))
    row = {"rc": rc, "log": logged(key), "command": G("AL_C_" + key)}
    if rc == 0:
        row.update(svg(key))
    out[key] = row
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("AL_VERSION"), "born_date": G("AL_BORN"),
                "dash_commit": commit, "extracted": G("AL_WHEN"),
                "scheme": "s2color",
                "source": "scripts/extract_axis_look_truth.do"}
with open(G("AL_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
for key in G("AL_KEYS").split():
    p = os.path.join(work, key + ".svg")
    if os.path.exists(p):
        os.remove(p)
print("wrote", G("AL_OUT"))
end
