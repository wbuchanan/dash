*! extract_graph_export_truth.do -- WP-30 section 22 (P1.28a): measure what
*! graph export and twoway do in the states dash's r(filename), its
*! stale-graph note and its saving() image-suffix rule are written against,
*! so they are proved against Stata, not modelled.
*!
*! Output: test/fixtures/graph_export_truth.json
*!
*! Run through the slot wrapper only (CLAUDE.md rule 10):
*!
*!   DASH_REPO=<tree> <tree>/scripts/stata_slot.sh <scratch> <tree>/scripts/extract_graph_export_truth.do
*!
*! METHOD.  After sysuse auto, each case runs under capture noisily inside
*! _gx_run, with its output in a text log of its own: graph export with no
*! graph (no_graph), with a name not in memory (no_such_name), with only a
*! nodraw graph (nodraw_only), after the drawn graph was dropped (dropped);
*! the r() twoway leaves (return_after_twoway); graph export to every
*! suffix spelling of gr_export.ado's VerifySuffix list and some it does
*! not recognise (sfx_<s>); and twoway's own saving() of a .png name
*! (saving_png); twoway's nodraw with saving(, asis) before any graph is
*! drawn (nodraw_asis) and after a drawn graph was dropped
*! (nodraw_asis_dropped; WP-38 GW-15).  A trailing python: block (stdlib only, never calling back
*! into Stata) takes each log's first line (not replace's "(file ... not
*! found)"), puts <work> for the work
*! folder and writes the fixture.  The git commit is read from a file
*! shell wrote, never with shell=True.  Every log and exported file is
*! erased.

clear all
set more off
set linesize 255

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_graph_export_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_graph_export_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global GX_REPO "`repo'"
global GX_OUT "${GX_REPO}/test/fixtures/graph_export_truth.json"
adopath ++ "`repo'/"
global dash_nobrowser 1

local work "`c(tmpdir)'dash_gx_probe"
capture mkdir "`work'"
global GX_WORK "`work'"


quietly shell git -C "${GX_REPO}" rev-parse HEAD > "${GX_WORK}/git_head.txt"
global GX_VERSION "`c(stata_version)'"
global GX_BORN "`c(born_date)'"
global GX_WHEN "`c(current_date)' `c(current_time)'"
global GX_OS "`c(os)'"
global GX_MODE "`c(mode)'"

* _gx_run name : command -- run command under capture noisily with its
* output alone in gx_<name>.log; its rc in GX_rc_<name>.
capture program drop _gx_run
program define _gx_run
    gettoken name 0 : 0
    gettoken colon 0 : 0
    quietly log using "${GX_WORK}/gx_`name'.log", text replace name(gx) nomsg
    capture noisily `0'
    global GX_rc_`name' = _rc
    quietly log close gx
end

* _gx_mem name -- graph dir, memory's list into GX_mem_<name>.
capture program drop _gx_mem
program define _gx_mem
    quietly graph dir, memory
    global GX_mem_`1' `"`r(list)'"'
end

sysuse auto, clear

* WP-38 GW-15: nodraw with saving(, asis) before anything is drawn.
graph drop _all
_gx_run nodraw_asis : twoway scatter price weight, saving("${GX_WORK}/gx7.gph", asis) nodraw
capture confirm file "${GX_WORK}/gx7.gph"
global GX_s7_written = (_rc == 0)

graph drop _all
_gx_run no_graph : graph export "${GX_WORK}/gx1.png", replace

* nodraw_only before anything is drawn: in batch a dropped graph is
* still the one graph export writes (dropped, below).
quietly twoway scatter price weight, nodraw
_gx_mem nodraw
_gx_run nodraw_only : graph export "${GX_WORK}/gx3.svg", replace

quietly twoway scatter price weight
_gx_run no_such_name : graph export "${GX_WORK}/gx2.svg", name(nosuch) replace

graph drop _all
quietly twoway scatter price weight
graph drop _all
_gx_mem dropped
_gx_run dropped : graph export "${GX_WORK}/gx4.svg", replace
_gx_run nodraw_asis_dropped : twoway scatter price weight, saving("${GX_WORK}/gx8.gph", asis) nodraw
capture confirm file "${GX_WORK}/gx8.gph"
global GX_s8_written = (_rc == 0)

quietly summarize price
twoway scatter price weight
mata: st_global("GX_rmac", strofreal(rows(st_dir("r()", "macro", "*"))))
mata: st_global("GX_rsca", strofreal(rows(st_dir("r()", "numscalar", "*"))))

global GX_SFX "png svg pdf eps ps jpg jpeg tif gif emf wmf PNG tiff pict gph html xyz"
* Numbered, not named by suffix: png and PNG are one file name on a Mac.
local i 0
foreach s of global GX_SFX {
    local ++i
    _gx_run sfx_`i' : graph export "${GX_WORK}/gx5_`i'.`s'", replace
}

_gx_run saving_png : twoway scatter price weight, saving("${GX_WORK}/gx6.png", replace)
capture confirm file "${GX_WORK}/gx6.png"
global GX_s6_named = (_rc == 0)
capture confirm file "${GX_WORK}/gx6.png.gph"
global GX_s6_appended = (_rc == 0)
graph drop _all

python:
import glob, json, os
from sfi import Macro

G = Macro.getGlobal
work = G("GX_WORK")
works = {work, work.rstrip("/"), os.path.realpath(work)}


def first(name):
    path = os.path.join(work, "gx_%s.log" % name)
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = [ln.rstrip() for ln in fh]
    os.remove(path)
    for ln in lines:
        # replace's "(file ... not found)" for a file not there yet says
        # nothing about the case.
        if not ln.strip() or ln.startswith("> ") or (
                ln.startswith("(file ") and ln.endswith(" not found)")):
            continue
        for w in sorted(works, key=len, reverse=True):
            ln = ln.replace(w.rstrip("/"), "<work>")
        return ln.strip()
    return ""


def case(name, **extra):
    d = {"rc": int(G("GX_rc_" + name)), "first": first(name)}
    d.update(extra)
    return d


with open(os.path.join(work, "git_head.txt"), encoding="utf-8") as fh:
    commit = fh.read().strip()
out = {
    "_meta": {
        "stata_version": G("GX_VERSION"),
        "born_date": G("GX_BORN"),
        "dash_commit": commit,
        "extracted": G("GX_WHEN"),
        "source": "scripts/extract_graph_export_truth.do",
        "os": G("GX_OS"),
        "mode": G("GX_MODE"),
    },
    "cases": {
        "no_graph": case("no_graph"),
        "no_such_name": case("no_such_name"),
        "nodraw_only": case("nodraw_only", memory=G("GX_mem_nodraw").strip()),
        "dropped": case("dropped", memory=G("GX_mem_dropped").strip()),
        "nodraw_asis": case("nodraw_asis",
                            written=int(float(G("GX_s7_written")))),
        "nodraw_asis_dropped": case("nodraw_asis_dropped",
                                    written=int(float(G("GX_s8_written")))),
        "saving_png": case("saving_png",
                           named_as_typed=int(float(G("GX_s6_named"))),
                           gph_appended=int(float(G("GX_s6_appended")))),
    },
    "suffixes": {s: case("sfx_%d" % (i + 1))
                 for i, s in enumerate(G("GX_SFX").split())},
    "return_after_twoway": {"macros": int(float(G("GX_rmac"))),
                            "scalars": int(float(G("GX_rsca")))},
}
with open(G("GX_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
for p in glob.glob(os.path.join(work, "gx*")) + [os.path.join(work, "git_head.txt")]:
    if os.path.isfile(p):
        os.remove(p)
end

display as text "extract_graph_export_truth.do: wrote ${GX_OUT}"
