*! extract_legend_keys_truth.do -- WP-43 section 43-04: measure how twoway
*! draws the legend's keys -- a marker key's size, angle and width per
*! scheme, textfirst, stacked, symplacement(), the legend's note() and
*! caption() and a wide economist legend (LT-21); the key shapes of rcap,
*! rcapsym, pccapsym, dropline, pcarrow, pcbarrow and rarea (PIC-11); which
*! keys twoway merges (MS-10); and a turned kdensity's and function's key
*! text (RH-13).  twoway only: the output is the same before and after
*! dash changes.
*!
*! Output: test/fixtures/legend_keys_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_legend_keys_truth.do
*!
*! (Built on scripts/extract_legend_box_truth.do's probe and reader.)
*! The git commit is read from a file `shell' wrote, never with shell=True.
*! Each row records the command twoway ran, its rc, every line it printed,
*! and (when it drew) every text, rect, line, circle, path and polygon of
*! its SVG export, the SVG's viewBox and the plot region's box.  The
*! marker and shape probes draw the first five rows of auto, so each SVG
*! is small; the legend does not depend on the data.


clear all
set more off
set linesize 200

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_lk_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_lk_bad' {
    display as error "extract_legend_keys_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _lk_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_lk_rc' | _rc {
    local _lk_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_legend_keys_truth.do: `_lk_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global LK_REPO "`repo'"
global LK_OUT "${LK_REPO}/test/fixtures/legend_keys_truth.json"

local work "`c(tmpdir)'dash_legend_keys_probe"
capture mkdir "`work'"
global LK_WORK "`work'"

quietly shell git -C "${LK_REPO}" rev-parse HEAD > "${LK_WORK}/git_head.txt"
global LK_VERSION "`c(stata_version)'"
global LK_BORN "`c(born_date)'"
global LK_WHEN "`c(current_date)' `c(current_time)'"

global LK_KEYS ""
global LK_N 0

* _lk_run key scheme cmd: run cmd under scheme, logging what it prints,
* and export the SVG when it draws.
capture program drop _lk_run
program define _lk_run
    args key scheme cmd
    global LK_N = ${LK_N} + 1
    local f "f${LK_N}"
    global LK_F_`key' "`f'"
    set scheme `scheme'
    capture graph drop u43k
    capture log close lkr
    quietly log using "${LK_WORK}/r_`f'.log", text replace name(lkr)
    capture noisily `macval(cmd)'
    local rc = _rc
    quietly log close lkr
    global LK_R_`key' "`rc'"
    global LK_S_`key' "`scheme'"
    global LK_C_`key' `"`macval(cmd)'"'
    global LK_KEYS "${LK_KEYS} `key'"
    capture erase "${LK_WORK}/`f'.svg"
    if !`rc' {
        quietly graph export "${LK_WORK}/`f'.svg", replace
    }
end

local N "name(u43k, replace)"

* ---- LT-21: marker keys --------------------------------------------------
sysuse auto, clear
local M "twoway (scatter mpg weight in 1/5) (scatter price weight in 1/5)"
foreach s in s2color economist meta stcolor s1mono {
    _lk_run mk_`s' `s' `"`M', `N'"'
}
_lk_run mk_large s2color `"twoway (scatter mpg weight in 1/5, msize(large)) (scatter price weight in 1/5), `N'"'
_lk_run mk_angle s2color `"twoway (scatter mpg weight in 1/5, msymbol(S) msangle(45)) (scatter price weight in 1/5), `N'"'
_lk_run mk_syms s2color `"twoway (scatter mpg weight in 1/5, msymbol(T)) (scatter price weight in 1/5, msymbol(D)) (scatter turn weight in 1/5, msymbol(S)) (scatter trunk weight in 1/5, msymbol(X)) (scatter length weight in 1/5, msymbol(+)), `N'"'
_lk_run mk_scale s2color `"`M', scale(1.5) `N'"'
_lk_run mk_line s2color `"twoway (scatter mpg weight in 1/5) (line price weight in 1/5), `N'"'
_lk_run mk_symx s2color `"`M', legend(symxsize(30)) `N'"'

* textfirst, stacked, symplacement(), note() and caption().
local L "twoway (scatter mpg weight in 1/5) (line price weight in 1/5)"
_lk_run cell_ctl s2color `"`L', `N'"'
_lk_run textfirst s2color `"`L', legend(textfirst) `N'"'
_lk_run stacked s2color `"`L', legend(stacked) `N'"'
_lk_run symp_left s2color `"`L', legend(symplacement(left)) `N'"'
_lk_run symp_n s2color `"`L', legend(symplacement(n)) `N'"'
_lk_run symp_sw s2color `"`L', legend(symplacement(sw)) `N'"'
_lk_run note s2color `"`L', legend(note("N")) `N'"'
_lk_run caption s2color `"`L', legend(caption("C")) `N'"'
_lk_run note_caption s2color `"`L', legend(note("N") caption("C")) `N'"'
_lk_run textfirst_stacked s2color `"`L', legend(textfirst stacked) `N'"'
_lk_run textfirst_cols1 s2color `"twoway (scatter mpg weight in 1/5) (line price weight in 1/5) (scatter turn weight in 1/5), legend(textfirst cols(1)) `N'"'
_lk_run textfirst_box s2color `"`L', legend(textfirst box) `N'"'
_lk_run textfirst_note s2color `"`L', legend(textfirst note("N")) `N'"'
_lk_run econ3 economist `"twoway (scatter mpg weight in 1/5) (scatter price weight in 1/5) (scatter turn weight in 1/5), legend(cols(3)) `N'"'
_lk_run by_textfirst s2color `"twoway (scatter mpg weight) (lfit mpg weight), by(foreign) legend(textfirst) `N'"'

* ---- PIC-11: key shapes ----------------------------------------------------
local S "(scatter mpg weight in 1/5)"
_lk_run sh_rcap s2color `"twoway (rcap mpg turn weight in 1/5) `S', `N'"'
_lk_run sh_rcapsym s2color `"twoway (rcapsym mpg turn weight in 1/5) `S', `N'"'
_lk_run sh_pccapsym s2color `"twoway (pccapsym mpg weight turn length in 1/5) `S', `N'"'
_lk_run sh_dropline s2color `"twoway (dropline mpg weight in 1/5) `S', `N'"'
_lk_run sh_pcarrow s2color `"twoway (pcarrow mpg weight turn length in 1/5) `S', `N'"'
_lk_run sh_pcbarrow s2color `"twoway (pcbarrow mpg weight turn length in 1/5) `S', `N'"'
_lk_run sh_rarea s2color `"twoway (rarea mpg turn weight in 1/5) `S', `N'"'
_lk_run sh_rcap_scale s2color `"twoway (rcap mpg turn weight in 1/5) `S', scale(1.5) `N'"'
_lk_run sh_rcap_st stcolor `"twoway (rcap mpg turn weight in 1/5) `S', `N'"'

* ---- RH-13: a turned kdensity or function ----------------------------------
_lk_run hz_kdensity s2color `"twoway (scatter mpg weight) (kdensity mpg, horizontal xaxis(2)), `N'"'
_lk_run hz_kd_area s2color `"twoway (scatter mpg weight) (kdensity mpg, horizontal xaxis(2) recast(area)), `N'"'
_lk_run hz_kd_bar s2color `"twoway (scatter mpg weight) (kdensity mpg, horizontal xaxis(2) recast(bar)), `N'"'
_lk_run hz_function s2color `"twoway (scatter mpg weight) (function y=x^2, range(0 2) horizontal xaxis(2)), `N'"'
_lk_run vt_kdensity s2color `"twoway (scatter mpg weight) (kdensity mpg, xaxis(2)), `N'"'
_lk_run vt_function s2color `"twoway (scatter mpg weight) (function y=x^2, range(0 2) xaxis(2)), `N'"'

* ---- MS-10: which keys merge -----------------------------------------------
_lk_run merge_lfitci s2color `"twoway (lfitci mpg weight) (lfitci price weight), `N'"'
_lk_run merge_hist s2color `"twoway (histogram mpg) (histogram turn), `N'"'
_lk_run merge_p1p2 s2color `"twoway (scatter mpg weight, pstyle(p1)) (scatter price weight, pstyle(p2)), `N'"'
_lk_run merge_p1p1 s2color `"twoway (scatter mpg weight, pstyle(p1)) (scatter price weight, pstyle(p1)), `N'"'
_lk_run merge_cross s2color `"twoway (kdensity mpg, pstyle(p1)) (line mpg weight, sort pstyle(p1)), `N'"'
_lk_run merge_cross_lfit s2color `"twoway (lfit mpg weight, pstyle(p1)) (line mpg weight, sort pstyle(p1)), `N'"'
_lk_run merge_cross_sc s2color `"twoway (scatter mpg weight, pstyle(p1)) (line mpg weight, sort pstyle(p1)), `N'"'
_lk_run merge_recast s2color `"twoway (scatter mpg weight, pstyle(p1) recast(line) sort) (line price weight, sort pstyle(p1)), `N'"'
* ---- LT-21 residual (batch 43.6): a key column, symplacement()'s
* compass values, the legend's note() beside its title() and a weighted
* marker layer's key.
sysuse auto, clear
local L "twoway (scatter mpg weight in 1/5) (line price weight in 1/5)"
local L3 "twoway (scatter mpg weight in 1/5) (line price weight in 1/5) (scatter turn weight in 1/5)"
_lk_run cols1 s2color `"`L3', legend(cols(1)) `N'"'
_lk_run cols1_symp_w s2color `"`L3', legend(cols(1) symplacement(w)) `N'"'
_lk_run cols1_symp_e s2color `"`L3', legend(cols(1) symplacement(e)) `N'"'
_lk_run cols1_symp_ne s2color `"`L3', legend(cols(1) symplacement(ne)) `N'"'
foreach d in c ne e se s w nw 12 6 top bottom right NE bogus {
    _lk_run symp_x`d' s2color `"`L', legend(symplacement(`d')) `N'"'
}
_lk_run symp_n_symy s2color `"`L', legend(symplacement(n) symysize(6)) `N'"'
_lk_run symp_n_size s2color `"`L', legend(symplacement(n) size(large)) `N'"'
_lk_run symp_n_scale s2color `"`L', legend(symplacement(n)) scale(1.5) `N'"'
_lk_run title_note s2color `"`L', legend(title("T") note("N")) `N'"'
_lk_run subtitle_note s2color `"`L', legend(subtitle("S") note("N")) `N'"'
_lk_run note_size s2color `"`L', legend(note("N", size(large))) `N'"'
_lk_run note_two s2color `"`L', legend(note("N1" "N2")) `N'"'
_lk_run note_cols1 s2color `"`L3', legend(cols(1) note("Note")) `N'"'
_lk_run wt_marker s2color `"twoway (scatter mpg weight in 1/5 [aw=turn]) (scatter price weight in 1/5), `N'"'
_lk_run wt_line s2color `"twoway (scatter mpg weight in 1/5 [aw=turn]) (line price weight in 1/5), `N'"'
_lk_run wt_trunk s2color `"twoway (scatter mpg weight in 1/5 [aw=trunk]) (line price weight in 1/5), `N'"'
_lk_run wt_large s2color `"twoway (scatter mpg weight in 1/5 [aw=turn], msize(large)) (line price weight in 1/5), `N'"'
_lk_run wt_all s2color `"twoway (scatter mpg weight [aw=turn]) (line price weight in 1/5), `N'"'
_lk_run sh_rcapsym_cols1 s2color `"twoway (rcapsym mpg turn weight in 1/5) (scatter mpg weight in 1/5), legend(cols(1)) `N'"'
clear
set obs 10
generate x = _n
forvalues i = 1/16 {
    generate v`i' = x + `i'
}
_lk_run merge_s1mono14 s1mono `"line v1-v14 x, sort `N'"'
_lk_run merge_s1mono15 s1mono `"line v1-v15 x, sort `N'"'
_lk_run merge_s1mono16 s1mono `"line v1-v16 x, sort `N'"'
_lk_run merge_s2color16 s2color `"line v1-v16 x, sort `N'"'

python:
import json, os, re, sys
from sfi import Macro
def G(k):
    return Macro.getGlobal(k)


work = G("LK_WORK")
_EL = re.compile(r"<(text|rect|line|circle|path|polygon|polyline|ellipse)\b"
                 r"([^>]*?)(/?)>(?:([^<]*)</text>)?")


def attrs(s):
    return dict(re.findall(r'([a-zA-Z0-9_:-]+)="([^"]*)"', s))


def svg(f):
    """Every drawn element of the SVG in document order: its tag, its
    attributes and, for a text, its body; and the SVG's viewBox."""
    with open(os.path.join(work, f + ".svg"), encoding="utf-8") as fh:
        src = fh.read()
    els = []
    for tag, a, _slash, body in _EL.findall(src):
        e = {"tag": tag, "a": attrs(a)}
        if tag == "text":
            e["text"] = (body or "").replace("&amp;", "&").strip()
        els.append(e)
    vb = re.search(r'viewBox="([-0-9. ]+)"', src)
    return {"els": els,
            "viewbox": [float(v) for v in vb.group(1).split()] if vb else None}


def logged(f):
    with open(os.path.join(work, "r_" + f + ".log"), encoding="utf-8") as fh:
        lines = [ln.rstrip() for ln in fh]
    return [ln.strip() for ln in lines if ln.strip()
            and not ln.startswith(".") and not ln.startswith(">")
            and not ln.lstrip().startswith(("name:", "log:", "log type:",
                                            "opened on:", "closed on:"))
            and not set(ln.strip()) <= set("-")]


def plot_box(f):
    sys.path.insert(0, os.path.join(G("LK_REPO"), "scripts"))
    import svg_truth
    pr = svg_truth.svg_plotregion(os.path.join(work, f + ".svg")) or {}
    return {k: pr.get(k) for k in ("left", "top", "right", "bottom")}


def row(key):
    rc = int(G("LK_R_" + key))
    f = G("LK_F_" + key)
    out = {"rc": rc, "lines": logged(f), "scheme": G("LK_S_" + key),
           "command": G("LK_C_" + key).replace(", name(u43k, replace)", "")
                                       .replace(" name(u43k, replace)", "")}
    if rc == 0:
        out.update(svg(f))
        out["plot"] = plot_box(f)
    return out


keys = G("LK_KEYS").split()
out = {k: row(k) for k in keys}
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("LK_VERSION"), "born_date": G("LK_BORN"),
                "dash_commit": commit, "extracted": G("LK_WHEN"),
                "data": "sysuse auto (the marker and shape probes its first"
                        " five rows); the merge_s* probes 10 rows of x and"
                        " v1-v16 = x + i",
                "source": "scripts/extract_legend_keys_truth.do",
                "units": "SVG user units of graph export, as(svg)"}
with open(G("LK_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote", G("LK_OUT"), len(keys), "probes")
end
