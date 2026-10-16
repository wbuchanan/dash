*! extract_smcl_text_truth.do
*! WP-31 section 42 (E9): twoway's drawing of the SMCL directives that
*! graph_text.sthlp does not document, of a style tag on part of a text
*! and of a raised run with no Unicode form, for
*! test/fixtures/smcl_text_truth.json.
*!
*! WHY THIS EXISTS
*!
*! dash drew {hline}, {space}, {dup}, {cmd:}, {hi:}, {ccl}, {center:} and
*! the link directives as typed.  This script draws each as the title of
*! a twoway graph with no axes, exports the SVG and reads the title's text
*! through scripts/svg_text_runs.py, so dash_render.py's expansions and
*! test/test_graph_text.py are written against what twoway draws.  It
*! also records where a graph set font face lives (fonts.home) and what
*! the SVG writes for {stSans:} after one is set (fonts.svg); both
*! settings are put back to the values they had before the probe.
*!
*! Output: test/fixtures/smcl_text_truth.json
*!
*! Run with:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_smcl_text_truth.do
*!
*! Each key records the typed title, the title's text (its runs joined),
*! its runs, the return code, and for some keys variants: further typed
*! forms of the same directive.  The trailing python: block never calls
*! back into Stata; a backtick in it would be spelled \x60.
*! ---------------------------------------------------------------------------

clear all
set graphics off
set more off

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_smcl_text_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_smcl_text_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZS_REPO "`repo'"
global ZS_OUT  "${ZS_REPO}/test/fixtures/smcl_text_truth.json"

local scratch "`c(tmpdir)'dash_smcl_text_probe"
capture mkdir "`scratch'"
global ZS_WORK "`scratch'"
global ZS_REC  "`scratch'/smcl_manifest.txt"
global ZS_FLOG "`scratch'/fonts_home.log"

global ZS_SVER = c(stata_version)
global ZS_BORN = c(born_date)
global ZS_DATE = c(current_date)

tempfile zsgitrev
quietly shell git -C "${ZS_REPO}" rev-parse HEAD > "`zsgitrev'"
tempname zsgfh
file open `zsgfh' using "`zsgitrev'", read text
file read `zsgfh' zsgitline
file close `zsgfh'
global ZS_COMMIT = trim(`"`zsgitline'"')
capture assert ustrregexm(`"${ZS_COMMIT}"', "^[0-9a-f]{40}$")
if _rc {
    display as error "extract_smcl_text_truth.do: git rev-parse HEAD did not print a 40-character commit"
    exit 498
}

// ---------------------------------------------------------------------------
// One graph per probe: a scatteri with no axes, the typed text its title.
// The manifest line: key, variant, graph number, return code, the typed
// text, c(linesize), c(current_date).
// ---------------------------------------------------------------------------
tempname zsm
file open `zsm' using "${ZS_REC}", write text replace
global ZS_FH `zsm'
global ZS_G = 0
global ZS_T = char(9)

capture program drop zs
program define zs
    args key variant inp
    global ZS_G = ${ZS_G} + 1
    capture graph drop zsg
    capture noisily twoway scatteri 0 0, xscale(off) yscale(off) ///
        title(`"`inp'"') name(zsg, replace)
    local rc = _rc
    if `rc' == 0 {
        quietly graph export "${ZS_WORK}/sm_${ZS_G}.svg", name(zsg) replace as(svg)
        graph drop zsg
    }
    file write ${ZS_FH} `"`key'${ZS_T}`variant'${ZS_T}${ZS_G}${ZS_T}`rc'${ZS_T}`c(linesize)'${ZS_T}`c(current_date)'${ZS_T}`inp'"' _n
end

zs smcl.hline     main     `"a {hline} b"'
zs smcl.hline     h0       `"a {hline 0} b"'
zs smcl.hline     h300     `"{hline 300}"'
zs smcl.hline     blanks   `"a {hline  2 } b"'
zs smcl.hline     colon    `"a {hline 2:x} b"'
zs smcl.hline     h254     `"{hline 254}"'
zs smcl.hline     h255     `"{hline 255}"'
zs smcl.hline     h256     `"{hline 256}"'
zs smcl.hline     bare     `"{hline}"'
zs smcl.hline     after    `"ab{hline}"'
zs smcl.hline     twice    `"a{hline}b{hline}c"'
zs smcl.hline5    main     `"a {hline 5} b"'
zs smcl.space3    main     `"a{space 3}b"'
zs smcl.space3    bare     `"a{space}b"'
zs smcl.space3    s300     `"a{space 300}b"'
zs smcl.space3    s255     `"a{space 255}b"'
zs smcl.space3    s256     `"a{space 256}b"'
zs smcl.dup3      main     `"a {dup 3:xy} b"'
zs smcl.dup3      styled   `"a {dup 2:{bf:x}y} b"'
zs smcl.dup3      bare     `"a {dup:xy} b"'
zs smcl.dup3      zero     `"a {dup 0:xy} b"'
zs smcl.dup3      unit     `"a {dup 3} b"'
zs smcl.cmd       main     `"a {cmd:xy} b"'
zs smcl.cmd       styled   `"a {cmd:{it:x}y} b"'
zs smcl.cmd       set      `"a {cmd}xy"'
zs smcl.hi        main     `"a {hi:xy} b"'
zs smcl.hi        bfin     `"{bf:a {hi:xy} b}"'
zs smcl.ccl       main     `"a {ccl current_date} b"'
zs smcl.ccl       pi       `"a {ccl pi} b"'
zs smcl.ccl       N        `"a {ccl N} b"'
zs smcl.ccl       nosuch   `"a {ccl nosuchname} b"'
zs smcl.ccl       colon    `"a {ccl pi:x} b"'
zs smcl.ccl       maxdouble `"{ccl maxdouble}"'
zs smcl.ccl       epsdouble `"{ccl epsdouble}"'
zs smcl.ccl       version  `"{ccl version}"'
zs smcl.ccl       blanks   `"a { ccl  pi } b"'
zs smcl.center    main     `"{center:xy}"'
zs smcl.center    inline   `"a {center:xy} b"'
zs smcl.center    width    `"{center 10:xy}"'
zs smcl.center    narrow   `"{center 3:xy}"'
zs smcl.center    over     `"{center 1:xyz}"'
zs smcl.center    twice    `"{center:xy}{center:ab}"'
zs smcl.center    w254     `"{center 254:xy}"'
zs smcl.center    w255     `"{center 255:xy}"'
zs smcl.center    w300     `"{center 300:xy}"'
set linesize 100
zs smcl.center    ls100    `"{center:xy}"'
set linesize 255
zs smcl.center    ls255    `"{center:xy}"'
set linesize 80
zs smcl.browse    main     `"a {browse "https://www.stata.com":xy} b"'
zs smcl.browse    bare     `"a {browse "https://www.stata.com"} b"'
zs smcl.browse    word     `"a {browse www.stata.com} b"'
zs smcl.help      main     `"a {help twoway} b"'
zs smcl.help      text     `"a {help twoway:xy} b"'
zs smcl.stata     main     `"a {stata sysuse auto:xy} b"'
zs smcl.stata     bare     `"a {stata sysuse auto} b"'
zs smcl.dup_big   main     `"{dup 1000:x}"'
zs smcl.dup_big   d300     `"{dup 300:x}"'
zs smcl.dup_big   d500     `"{dup 500:x}"'
zs smcl.dup_big   d999     `"{dup 999:x}"'
zs smcl.dup_big   plain300 `"`=300*"x"'"'
zs smcl.dup_big   bf301    `"{bf:a}`=300*"x"'"'
zs smcl.dup_big   tail     `"a{dup 600:x}b{bf:c}"'
zs inline.bf_part main     `"a {bf:b} c"'
zs inline.sup_q   main     `"a{sup:q}"'
zs inline.sup_2   main     `"a{sup:2}"'

// ---- fonts: where a graph set font face lives ------------------------------
// The settings are put back afterwards: svg fontface's value before the
// probe is read from the graph set listing below (Helvetica on the
// measuring machine), window fontface had none.
log using "${ZS_FLOG}", text replace name(zsfonts)
graph set svg fontface Courier
graph set window fontface Courier
graph set svg
return list
creturn list
macro list
char list
log close zsfonts
global ZS_G = ${ZS_G} + 1
capture graph drop zsg
twoway scatteri 0 0, xscale(off) yscale(off) title(`"{stSans:a} b"') name(zsg, replace)
quietly graph export "${ZS_WORK}/sm_${ZS_G}.svg", name(zsg) replace as(svg)
graph drop zsg
file write ${ZS_FH} `"fonts.svg${ZS_T}main${ZS_T}${ZS_G}${ZS_T}0${ZS_T}`c(linesize)'${ZS_T}`c(current_date)'${ZS_T}{stSans:a} b"' _n
graph set svg fontface Helvetica
graph set window fontface default
graph set svg
graph set window
file write ${ZS_FH} `"fonts.home${ZS_T}main${ZS_T}0${ZS_T}0${ZS_T}`c(linesize)'${ZS_T}`c(current_date)'${ZS_T}graph set svg fontface Courier; graph set window fontface Courier"' _n

file close `zsm'

python:
import json
import os
import re
import sys
from sfi import Macro

REPO = Macro.getGlobal("ZS_REPO")
sys.path.insert(0, os.path.join(REPO, "scripts"))
import svg_text_runs

WORK = Macro.getGlobal("ZS_WORK")
out = {
    "_meta": {
        "stata_version": Macro.getGlobal("ZS_SVER"),
        "born_date": Macro.getGlobal("ZS_BORN"),
        "dash_commit": Macro.getGlobal("ZS_COMMIT"),
        "extracted": Macro.getGlobal("ZS_DATE"),
        "source": "scripts/extract_smcl_text_truth.do",
    },
}


def record(g, rc, typed, ls, today):
    rec = {"typed": typed, "rc": int(rc), "linesize": int(ls),
           "current_date": today}
    if int(rc) or int(g) == 0:
        return rec
    texts = svg_text_runs.svg_text_runs(os.path.join(WORK, "sm_%s.svg" % g))
    runs = [r for t in texts for r in t["runs"] if r["text"]]
    rec["text"] = "".join(r["text"] for r in runs)
    rec["runs"] = [{"text": r["text"], "weight": r["weight"],
                    "style": r["style"], "family": r["family"],
                    "level": r["level"]} for r in runs]
    return rec


with open(Macro.getGlobal("ZS_REC"), encoding="utf-8") as fh:
    rows = [l.rstrip("\n").split("\t", 6) for l in fh if l.strip()]
for key, variant, g, rc, ls, today, typed in rows:
    rec = record(g, rc, typed, ls, today)
    if variant == "main":
        out.setdefault(key, {}).update(rec)
    else:
        out.setdefault(key, {}).setdefault("variants", {})[variant] = rec

with open(Macro.getGlobal("ZS_FLOG"), encoding="utf-8") as fh:
    flog = fh.read()
# Where Courier shows up after the two graph set lines: the graph set
# listing prints it; return list, creturn list, macro list and char list
# are read for a readable home.
cut = flog.find(". return list")
listing, rest = flog[:cut], flog[cut:]
out["fonts.home"]["listing_shows"] = bool(re.search(r"fontface\s+Courier", listing))
out["fonts.home"]["readable_home"] = "Courier" in rest
out["fonts.home"]["log_lines"] = [l for l in rest.splitlines() if "Courier" in l][:20]

with open(Macro.getGlobal("ZS_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2, sort_keys=True, ensure_ascii=True)
    fh.write("\n")
print("wrote", Macro.getGlobal("ZS_OUT"), len([k for k in out if k != "_meta"]))
end
