*! extract_noted_option_truth.do -- WP-32: what twoway does with each
*! option dash declares and names in its note as not drawn ("ignoring
*! unsupported option(s): ..."), on every one of the forty-four plot types
*! dash draws (BUGS.md "dash names in its note, as not drawn, options
*! twoway refuses on that plot type").
*!
*! For each probe: twoway's rc and first error line for the option alone on
*! each type, and -- where twoway takes it -- whether the graph twoway
*! draws differs from the one it draws without it (graph export SVG, its
*! <desc> lines aside; null where two exports of the plain graph already
*! differ, or twoway refuses it); dash's rc, first error line and note on each type.
*! Then twoway's and dash's answer to each graph-level probe after the plot
*! groups' comma, and to bare replace in each position.
*!
*! Output: test/fixtures/noted_option_truth.json
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_noted_option_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 255
set graphics off

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zn_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zn_bad' {
    display as error "extract_noted_option_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zn_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zn_rc' | _rc {
    local _zn_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_noted_option_truth.do: `_zn_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZN_REPO "`repo'"
global ZN_OUT "${ZN_REPO}/test/fixtures/noted_option_truth.json"

adopath ++ "${ZN_REPO}"
quietly do "${ZN_REPO}/dash_parse.mata"
quietly do "${ZN_REPO}/dash.ado"
global dash_nobrowser 1

local work "`c(tmpdir)'dash_noted_probe"
capture mkdir "`work'"
global ZN_WORK "`work'"

if `"`c(python_exec)'"' == "" {
    display as error "extract_noted_option_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

quietly shell git -C "${ZN_REPO}" rev-parse HEAD > "${ZN_WORK}/git_head.txt"
global ZN_VERSION "`c(stata_version)'"
global ZN_BORN "`c(born_date)'"
global ZN_WHEN "`c(current_date)' `c(current_time)'"

* 1 when two SVG files differ, their <desc> lines aside.
capture mata: mata drop _zn_differs()
mata:
real scalar _zn_differs(string scalar a, string scalar b)
{
    string colvector A, B
    A = cat(a)
    B = cat(b)
    A = select(A, !strmatch(strtrim(A), "<desc>*"))
    B = select(B, !strmatch(strtrim(B), "<desc>*"))
    if (rows(A) != rows(B)) return(1)
    return(!all(A :== B))
}
end

sysuse auto, clear
gen yl = mpg - 1
gen yh = mpg + 1
gen t = _n
tsset t

* The forty-four types and the command each is asked with
* (extract_unknown_option_truth.do's).
local types scatter line connected area bar spike dropline dot tsline tsrline ///
    rarea rbar rspike rcap rline rconnected rcapsym rscatter rpcap rpspike ///
    contour contourline ///
    pcspike pccapsym pcarrow pcbarrow pcscatter pci pcarrowi scatteri ///
    lfit qfit lfitci qfitci fpfit fpfitci lowess lpoly lpolyci mspline mband ///
    kdensity histogram function
global ZN_TYPES "`types'"
local k 0
foreach t of local types {
    local ++k
    if inlist("`t'", "scatter", "line", "connected", "area", "bar", "spike", "dropline", "dot") local a "`t' mpg weight,"
    else if "`t'" == "tsline" local a "tsline mpg,"
    else if "`t'" == "tsrline" local a "tsrline yl yh,"
    else if inlist("`t'", "rarea", "rbar", "rspike", "rcap", "rline", "rconnected", "rcapsym", "rscatter") local a "`t' yl yh weight,"
    else if inlist("`t'", "rpcap", "rpspike") local a "`t' yl yh mpg weight,"
    else if inlist("`t'", "contour", "contourline") local a "`t' mpg weight length,"
    else if inlist("`t'", "pcspike", "pccapsym", "pcarrow", "pcbarrow", "pcscatter") local a "`t' mpg weight trunk turn,"
    else if inlist("`t'", "pci", "pcarrowi") local a "`t' 20 2000 30 4000,"
    else if "`t'" == "scatteri" local a "scatteri 20 2000,"
    else if inlist("`t'", "kdensity", "histogram") local a "`t' mpg,"
    else if "`t'" == "function" local a "function y = x, range(0 1)"
    else local a "`t' mpg weight,"
    local base_`t' "`a'"
    * The picture without the option, once per type.
    capture graph drop _all
    capture twoway `a' name(zo, replace)
    if !_rc capture graph export "${ZN_WORK}/b`k'.svg", name(zo) replace as(svg)
    capture graph drop _all
    * The same picture again: a type whose two exports differ (an id
    * numbered per session) is one where "draws" is not read.
    capture twoway `a' name(zo, replace)
    if !_rc capture graph export "${ZN_WORK}/c`k'.svg", name(zo) replace as(svg)
    capture graph drop _all
    local stable_`t' 0
    capture confirm file "${ZN_WORK}/c`k'.svg"
    if !_rc {
        mata: st_local("stable_`t'", strofreal(!_zn_differs("${ZN_WORK}/b`k'.svg", "${ZN_WORK}/c`k'.svg")))
    }
}

* The options on dash.ado's pending lists (_dash_parse_plot_opts,
* _dash_parse_graph_opts, _dash_fold_typed, _dash_recast_named) and bare
* replace (_dash_render's note).
local probes at(mpg) blabel(total) ciopts(lcolor(red)) fitopts(lcolor(red)) ///
    lineopts(lcolor(red)) mlabwidth(thick) bmlinestyle(p3) dlalign(inside) ///
    acolor(red) alcolor(red) alwidth(thick) alpattern(dash) sort sort(price) ///
    heatmap outlines lstyle(p3) alstyle(p3) blstyle(p3) mstyle(p3) mlstyle(p3) ///
    mangle(30) barbsize(2) headlabel mwidth baroffset(1) msize(small) ///
    recast(line) filter(foreign) link(g1) play(zn_no_such_recording) replace
local k 0
foreach one of local probes {
    local ++k
    global ZN_O_`k' `"`one'"'
    local tr ""
    local dr ""
    local df ""
    local j 0
    foreach t of local types {
        local ++j
        quietly log using "${ZN_WORK}/t`k'_`j'.log", replace text name(zn)
        capture noisily twoway `base_`t'' `one' name(zo, replace)
        local rc = _rc
        quietly log close zn
        local tr "`tr' `rc'"
        local d = -1
        if !`rc' & `stable_`t'' {
            capture graph export "${ZN_WORK}/o.svg", name(zo) replace as(svg)
            if !_rc {
                mata: st_local("d", strofreal(_zn_differs("${ZN_WORK}/b`j'.svg", "${ZN_WORK}/o.svg")))
            }
        }
        local df "`df' `d'"
        capture graph drop _all
        quietly log using "${ZN_WORK}/d`k'_`j'.log", replace text name(zn)
        capture noisily dash `base_`t'' `one' name(zq)
        local dr "`dr' `=_rc'"
        quietly log close zn
        capture dash clear
    }
    global ZN_TR_`k' "`tr'"
    global ZN_DR_`k' "`dr'"
    global ZN_DF_`k' "`df'"
}
global ZN_K "`k'"

* Graph level, and bare replace in each position.
local gl `" "(scatter mpg weight), filter(foreign)" "(scatter mpg weight), link(g1)" "(scatter mpg weight), play(zn_no_such_recording)" "(scatter mpg weight), replace" "scatter mpg weight, replace" "scatter mpg weight, saving(zn_f1) replace" "(scatter mpg weight), saving(zn_f2) replace" "scatter mpg weight, name(zq) replace" "(scatter mpg weight), name(zq) replace" "scatter mpg weight, name(zq) saving(zn_f3) replace" "scatter mpg weight, saving(zn_f4, replace)" "scatter mpg weight || line mpg weight, replace" "'
local j 0
foreach c of local gl {
    local ++j
    global ZN_GC_`j' `"`c'"'
    capture erase "${ZN_WORK}/zn_f`j'.gph"
    quietly log using "${ZN_WORK}/gt`j'.log", replace text name(zn)
    capture noisily twoway `c' nodraw
    global ZN_GT_`j' = _rc
    quietly log close zn
    capture graph drop _all
    quietly log using "${ZN_WORK}/gd`j'.log", replace text name(zn)
    capture noisily dash `c'
    global ZN_GD_`j' = _rc
    quietly log close zn
    capture dash clear
}
global ZN_J "`j'"
foreach f in zn_f1 zn_f2 zn_f3 zn_f4 {
    capture erase "`f'.gph"
    capture erase "`f'.html"
}

python:
import json, os, re
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


NOTE = "ignoring unsupported option(s):"


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def note(text):
    """The note's names as printed, its closing parenthesis aside."""
    for ln in text.replace("\n> ", "").splitlines():
        i = ln.find(NOTE)
        if i >= 0:
            s = ln[i + len(NOTE):].strip()
            if ln.lstrip().startswith("(note:") and s.endswith(")"):
                s = s[:-1]
            return s.split()
    return []


def first_error(text):
    for s in (ln.strip() for ln in text.replace("\n> ", "").splitlines()):
        if not s or s.startswith(". ") or s.startswith("(note:") or s.startswith("dash: graph"):
            continue
        if (s.startswith("option") or "not allowed" in s or "invalid" in s
                or "not found" in s or "may not" in s or "not" in s):
            return s
    return ""


work = G("ZN_WORK")
types = G("ZN_TYPES").split()
probes = {}
for k in range(1, int(G("ZN_K")) + 1):
    opt = G("ZN_O_%d" % k)
    tr = [int(v) for v in G("ZN_TR_%d" % k).split()]
    dr = [int(v) for v in G("ZN_DR_%d" % k).split()]
    df = [int(v) for v in G("ZN_DF_%d" % k).split()]
    rows = {}
    for j, t in enumerate(types, 1):
        tl = os.path.join(work, "t%d_%d.log" % (k, j))
        dl = os.path.join(work, "d%d_%d.log" % (k, j))
        tt, dt = read(tl), read(dl)
        rows[t] = {"twoway_rc": tr[j - 1],
                   "twoway_message": first_error(tt) if tr[j - 1] else "",
                   "twoway_draws": None if df[j - 1] < 0 else bool(df[j - 1]),
                   "dash_rc": dr[j - 1],
                   "dash_message": first_error(dt) if dr[j - 1] else "",
                   "dash_note": note(dt)}
        for f in (tl, dl):
            try:
                os.remove(f)
            except OSError:
                pass
    probes[opt] = rows
graph = []
for j in range(1, int(G("ZN_J")) + 1):
    tl = os.path.join(work, "gt%d.log" % j)
    dl = os.path.join(work, "gd%d.log" % j)
    tt, dt = read(tl), read(dl)
    trc, drc = int(G("ZN_GT_%d" % j)), int(G("ZN_GD_%d" % j))
    graph.append({"cmd": G("ZN_GC_%d" % j), "twoway_rc": trc,
                  "twoway_message": first_error(tt) if trc else "",
                  "dash_rc": drc, "dash_message": first_error(dt) if drc else "",
                  "dash_note": note(dt)})
    for f in (tl, dl):
        try:
            os.remove(f)
        except OSError:
            pass
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out = {"_meta": {"stata_version": G("ZN_VERSION"), "born_date": G("ZN_BORN"),
                 "dash_commit": commit, "extracted": G("ZN_WHEN"),
                 "source": "scripts/extract_noted_option_truth.do"},
       "types": types, "probes": probes, "graph_level": graph}
with open(G("ZN_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
for f in ["git_head.txt", "o.svg"] + ["%s%d.svg" % (c, i) for c in "bc" for i in range(1, len(types) + 1)]:
    try:
        os.remove(os.path.join(work, f))
    except OSError:
        pass
print("wrote", G("ZN_OUT"), len(probes), "probes,", len(graph), "graph-level")
end
