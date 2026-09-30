*! release_gate.do -- WP-27's release gate, run against an INSTALLED dash.
*!
*! Usage (through scripts/run_release_gate.sh, which stages the source and
*! judges this run's log with scripts/release_verdict.py):
*!
*!     do release_gate.do <source dir> <work dir> <examples dir>
*!
*! <source dir> holds exactly what dash.pkg ships plus stata.toc; <work dir>
*! is an empty scratch directory; <examples dir> is the repository's
*! examples/.  The gate:
*!
*!   1. net installs dash from <source dir> into a PLUS made for the run, with
*!      only Stata's own directories and that PLUS on the ado-path (dash
*!      needs no other Stata package), and confirms dash, dash_setup and the renderer are the
*!      installed copies (BR-27.1);
*!   2. runs every .do file in <examples dir> from <work dir>/out, each in a fresh
*!      session state and under its own log, recording each one's rc
*!      (TR-27.1); the verdict script reads those logs for fallback warnings,
*!      ignored-option notes and Python or Bokeh diagnostics;
*!   3. builds one page per shipped scheme through the installed renderer
*!      and records each rc and log (AC-27.2, "correct schemes");
*!   4. has adoupdate compare the installed dash with its source, then with
*!      a copy of that source one day newer (TR-27.5).
*!
*! Every result is one line starting "GATE ", which is all the verdict
*! reads.  PLUS and the ado-path are put back before the run ends.

version 18
args src work exdir
global dash_nobrowser 1
set more off
// A GATE line holds paths; Stata wraps a log line at the line size.
set linesize 255

if `"`src'"' == "" | `"`work'"' == "" | `"`exdir'"' == "" {
    display "GATE usage rc=198"
    exit 198
}

local plus0 "`c(sysdir_plus)'"
local sado0 `"$S_ADO"'
local plus "`work'/plus/"
local out "`work'/out"
local logs "`work'/logs"
mata: mkdir(st_local("plus")); mkdir(st_local("out")); mkdir(st_local("logs"))

// ---- 1. net install into a clean PLUS -----------------------------------
sysdir set PLUS "`plus'"
local moved = ("`c(sysdir_plus)'" == "`plus'")
display "GATE plus-moved ok=`moved'"
if !`moved' exit 459
capture noisily net from "`src'"
local rc = _rc
if `rc' == 0 {
    capture noisily net install dash, replace
    local rc = _rc
}
display "GATE install rc=`rc'"
mata: st_global("S_ADO", "BASE;SITE;PLUS")

// Each of these must resolve inside the scratch PLUS.
foreach f in dash.ado dash_setup.ado dash_parse.mata dash_render.py {
    capture findfile `f'
    local frc = _rc
    local ffn `"`r(fn)'"'
    mata: st_local("inside", strofreal(`frc' == 0 & strpos(pathresolve(pwd(), st_local("ffn")), pathresolve(pwd(), st_local("plus"))) == 1))
    display `"GATE installed file=`f' rc=`frc' inplus=`inside' path=`ffn'"'
}
// The locator is a subroutine of dash.ado, private to it when Stata
// autoloads the file; running the INSTALLED file defines it here.
capture findfile dash.ado
if _rc == 0 quietly run `"`r(fn)'"'
capture noisily _dash_find_render
local frc = _rc
local ffn `"`r(fn)'"'
mata: st_local("inside", strofreal(`frc' == 0 & strpos(pathresolve(pwd(), st_local("ffn")), pathresolve(pwd(), st_local("plus"))) == 1))
display `"GATE installed file=locator rc=`frc' inplus=`inside' path=`ffn'"'

// ---- 2. every example, from the installed tree --------------------------
local files : dir "`exdir'" files "*.do"
local files : list sort files
local nfiles : word count `files'
display "GATE examples n=`nfiles'"
quietly cd "`out'"
foreach f of local files {
    capture dash clear
    clear all
    global dash_nobrowser 1
    set more off
    capture log close _gate
    quietly log using "`logs'/example_`f'.log", text replace name(_gate)
    capture noisily do "`exdir'/`f'"
    local erc = _rc
    capture log close _gate
    display `"GATE example file=`f' rc=`erc' log=`logs'/example_`f'.log"'
}

// ---- 3. one page per shipped scheme -------------------------------------
local schemes : dir "`src'" files "dash-*.scheme"
local schemes : list sort schemes
local nsch : word count `schemes'
display "GATE schemes n=`nsch'"
foreach s of local schemes {
    local nm = subinstr(subinstr("`s'", ".scheme", "", 1), "dash-", "", 1)
    capture dash clear
    quietly sysuse auto, clear
    capture log close _gate
    quietly log using "`logs'/scheme_`nm'.log", text replace name(_gate)
    capture noisily {
        dash scatter mpg weight, name(g1) scheme(`nm') title("`nm'")
        dash line price weight, name(g2)
        dash build, saving("`out'/scheme_`nm'.html") replace nobrowser scheme(`nm')
    }
    local sch_rc = _rc
    capture log close _gate
    display `"GATE scheme name=`nm' rc=`sch_rc' log=`logs'/scheme_`nm'.log"'
}
capture dash clear

// ---- 4. adoupdate sees the release ---------------------------------------
quietly cd "`work'"
capture noisily adoupdate dash
local arc = _rc
local alist `"`r(pkglist)'"'
display `"GATE adoupdate-same rc=`arc' pkglist=[`alist']"'
// A source one day newer: only dash.pkg's Distribution-Date differs.
local newer "`work'/newer"
mata: mkdir(st_local("newer"))
python:
import os, re, shutil
from sfi import Macro
src, newer = Macro.getLocal("src"), Macro.getLocal("newer")
for name in os.listdir(src):
    p = os.path.join(src, name)
    if os.path.isfile(p):
        shutil.copy2(p, newer)
    elif os.path.isdir(p):
        shutil.copytree(p, os.path.join(newer, name))
pkg = os.path.join(newer, "dash.pkg")
text = open(pkg, encoding="utf-8").read()
m = re.search(r"^d Distribution-Date: (\d{8})\s*$", text, re.M)
if m:
    import datetime
    d = datetime.datetime.strptime(m.group(1), "%Y%m%d") + datetime.timedelta(days=1)
    text = text[:m.start(1)] + d.strftime("%Y%m%d") + text[m.end(1):]
    open(pkg, "w", encoding="utf-8").write(text)
Macro.setLocal("bumped", "1" if m else "0")
end
display "GATE newer-source bumped=`bumped'"
// adoupdate compares an installed package with the source its stata.trk
// entry records on the entry's S line, so point that line at the newer
// copy: the installed files stay the ones from step 1.
python:
import os
from sfi import Macro
trk = os.path.join(Macro.getLocal("plus"), "stata.trk")
text = open(trk, encoding="utf-8").read()
src, newer = Macro.getLocal("src"), Macro.getLocal("newer")
n = text.count("S " + src)
text = text.replace("S " + src, "S " + newer)
open(trk, "w", encoding="utf-8").write(text)
Macro.setLocal("trk_moved", str(n))
end
display "GATE trk-source moved=`trk_moved'"
capture noisily adoupdate dash
local arc = _rc
local alist `"`r(pkglist)'"'
display `"GATE adoupdate-newer rc=`arc' pkglist=[`alist']"'

// ---- put the session back -------------------------------------------------
sysdir set PLUS "`plus0'"
global S_ADO `"`sado0'"'
local back = ("`c(sysdir_plus)'" == "`plus0'")
display "GATE restored ok=`back'"
display "GATE done"
