*! extract_graph_text_truth.do
*! WP-30 section 29 (P1.11b): twoway's drawing of Stata's graph-text
*! markup, for test/fixtures/graph_text_truth.json.
*!
*! WHY THIS EXISTS
*!
*! dash draws graph-text markup ({bf:}, {it:}, {sup:}, {&alpha}, {c 233},
*! the font tags ...) as twoway draws it.  The tables dash_render.py holds
*! (_DASH_GT_SYMBOLS, _DASH_GT_CNAMES, _DASH_GT_STSYMBOL) are transcribed
*! from this fixture, and test/test_graph_text.py compares the scanner
*! with every entry.  This script draws each directive as a tick label of
*! a twoway scatteri, exports the SVG and reads each label's styled runs
*! through scripts/svg_text_runs.py.
*!
*! Output: test/fixtures/graph_text_truth.json
*!
*! Run with (the script sets its own directories):
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_graph_text_truth.do
*!
*! METHOD
*!
*! Every tick label is "<i>_" + the directive, so the reader keys each label
*! by its index and never splits on a character the output may hold.  A
*! label whose directive draws nothing records no runs.  Families:
*! symbols (the {&name} list read from graph_text.sthlp, 148), chars ({c n},
*! n = 1..255), cnames (the {c name} table read from smcl.sthlp), stsymbol
*! ({stSymbol:ch} for printable ASCII except " $ backtick { } \), and cases
*! (edge cases, each with a category: graph_text, other_smcl or
*! difference).  Multi-line cases are titles of a graph with no axes.
*!
*! {c 0} (measured 08oct2026; scratch note 29-c0-truth.txt): twoway does
*! not empty the text -- it cuts off the rest of the {c 0}'s own styled
*! run on its own line; the text after the run's closing brace and other
*! lines are drawn.  The c0 cases below record it.
*!
*! The trailing python: block never calls back into Stata; a backtick in
*! it would be spelled \x60.
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
    display as error "extract_graph_text_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_graph_text_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZG_REPO "`repo'"
global ZG_OUT  "${ZG_REPO}/test/fixtures/graph_text_truth.json"

local scratch "`c(tmpdir)'dash_graph_text_probe"
capture mkdir "`scratch'"
global ZG_WORK "`scratch'"
global ZG_REC  "`scratch'/gt_manifest.txt"

global ZG_SVER = c(stata_version)
global ZG_BORN = c(born_date)
global ZG_DATE = c(current_date)

// Provenance stamp: the commit read through a file, never a Stata call
// from Python.
tempfile zggitrev
quietly shell git -C "${ZG_REPO}" rev-parse HEAD > "`zggitrev'"
tempname zggfh
file open `zggfh' using "`zggitrev'", read text
file read `zggfh' zggitline
file close `zggfh'
global ZG_COMMIT = trim(`"`zggitline'"')
capture assert ustrregexm(`"${ZG_COMMIT}"', "^[0-9a-f]{40}$")
if _rc {
    display as error "extract_graph_text_truth.do: git rev-parse HEAD did not print a 40-character commit"
    exit 498
}

// ---------------------------------------------------------------------------
// The manifest: one tab-separated line per label: kind, graph, index,
// family, key, category, input (a name such as S| holds a bar).
// ---------------------------------------------------------------------------
tempname zgm
file open `zgm' using "${ZG_REC}", write text replace
global ZG_G = 0
global ZG_I = 0
global ZG_XL ""
global ZG_T = char(9)

capture program drop _zg_flush
program define _zg_flush
    if ${ZG_I} == 0 exit
    local g = ${ZG_G}
    local n = ${ZG_I} + 1
    capture graph drop zgg
    quietly twoway scatteri 0 0 0 `n', xlabel(${ZG_XL}) ///
        xscale(range(0 `n')) yscale(off) xtitle("") name(zgg, replace)
    quietly graph export "${ZG_WORK}/gt_`g'.svg", name(zgg) replace as(svg)
    graph drop zgg
    global ZG_I = 0
    global ZG_XL ""
end

capture program drop _zg_add
program define _zg_add
    args fam key cat
    local inp `"${ZG_INP}"'
    if ${ZG_I} == 0 global ZG_G = ${ZG_G} + 1
    global ZG_I = ${ZG_I} + 1
    local i = ${ZG_I}
    global ZG_XL `"${ZG_XL} `i' `"`i'_`inp'"'"'
    file write ${ZG_FH} `"T${ZG_T}${ZG_G}${ZG_T}`i'${ZG_T}`fam'${ZG_T}`key'${ZG_T}`cat'${ZG_T}`inp'"' _n
    if ${ZG_I} >= 40 _zg_flush
end
global ZG_FH `zgm'

// ---- symbols: read from graph_text.sthlp ----------------------------------
findfile graph_text.sthlp
local gtf "`r(fn)'"
tempname zgh
local nsym = 0
file open `zgh' using "`gtf'", read text
file read `zgh' line
while r(eof) == 0 {
    local rest `"`macval(line)'"'
    while ustrregexm(`"`macval(rest)'"', "\{c -\(\}&([A-Za-z0-9]+)\{c \)-\}") {
        local nm = ustrregexs(1)
        local whole = ustrregexs(0)
        if !`: list nm in symlist' {
            local symlist `symlist' `nm'
            local ++nsym
        }
        local at = strpos(`"`macval(rest)'"', "`whole'") + strlen("`whole'")
        local rest = substr(`"`macval(rest)'"', `at', .)
    }
    file read `zgh' line
}
file close `zgh'
assert `nsym' == 148
foreach nm of local symlist {
    global ZG_INP "{&`nm'}"
    _zg_add symbols `nm' symbols
}
_zg_flush

// ---- chars: {c n}, n = 1..255 ---------------------------------------------
forvalues n = 1/255 {
    global ZG_INP "{c `n'}"
    _zg_add chars `n' chars
}
_zg_flush

// ---- cnames: the {c name} table of smcl.sthlp ------------------------------
findfile smcl.sthlp
local smf "`r(fn)'"
local ncn = 0
file open `zgh' using "`smf'", read text
file read `zgh' line
while r(eof) == 0 {
    if substr(`"`macval(line)'"', 1, 8) == "{center:" {
        local rest `"`macval(line)'"'
        while ustrregexm(`"`macval(rest)'"', "\{cmd:\{c -\(\}c (.+?)\{c \)-\}\}") {
            local nm = ustrregexs(1)
            local whole = ustrregexs(0)
            global ZG_INP `"{c `nm'}"'
            local ++ncn
            _zg_add cnames `"`nm'"' cnames
            local at = strpos(`"`macval(rest)'"', `"`whole'"') + strlen(`"`whole'"')
            local rest = substr(`"`macval(rest)'"', `at', .)
        }
    }
    file read `zgh' line
}
file close `zgh'
assert `ncn' >= 70
_zg_flush

// ---- stsymbol: {stSymbol:ch} -----------------------------------------------
forvalues n = 33/126 {
    if inlist(`n', 34, 36, 92, 96, 123, 125) continue
    local ch = char(`n')
    global ZG_INP `"{stSymbol:`ch'}"'
    _zg_add stsymbol `n' stsymbol
}
_zg_flush

// ---- cases: edge cases ------------------------------------------------------
capture program drop zc
program define zc
    args id cat inp
    global ZG_INP `"`inp'"'
    _zg_add cases `id' `cat'
end
zc it_bf          graph_text `"{it:{bf:x}}"'
zc bf_bf          graph_text `"{bf:a}{bf:b}"'
zc bf_unclosed    graph_text `"{bf:abc"'
zc bf_set         graph_text `"a {bf}b"'
zc it_bf_set      graph_text `"{it}a{bf}b"'
zc bf_it          graph_text `"{bf:{it:both}}"'
zc bf_it_mid      graph_text `"{bf:a{it:b}c}"'
zc sub_sup        graph_text `"{sub:{sup:x}}"'
zc sup_alpha      graph_text `"{sup:{&alpha}}"'
zc long_levels    graph_text `"{superscript:2}{subscript:x}"'
zc bf_empty       graph_text `"{bf:}"'
zc bf_bare        graph_text `"{bf}"'
zc bf_upper       graph_text `"{BF:x}"'
zc bf_blank1      graph_text `"{ bf:x}"'
zc bf_blank2      graph_text `"{bf :x}"'
zc cp1252         graph_text `"{c 128}{c 150}{c 169}{c 0x41}"'
zc c999           graph_text `"{c 999}"'
zc c256           graph_text `"{c 256}"'
zc c0XE9          graph_text `"{c 0XE9}"'
zc c_2blank       graph_text `"{c  233}"'
zc escaped        graph_text `"{c -(}bf:x{c )-}"'
zc amp_semi       graph_text `"{&alpha;}"'
zc amp_blank      graph_text `"{& alpha}"'
zc amp_colon      graph_text `"{&alpha:x}"'
zc c1             graph_text `"{c 1}|"'
zc c31            graph_text `"{c 31}|"'
zc c129           graph_text `"{c 129}|"'
zc fontface       graph_text `"{fontface "Courier New":fx}"'
zc fontface_set   graph_text `"{fontface "Courier"}all"'
zc foo_frame      graph_text `"{foo:{bf:x}}"'
zc bf_foo         graph_text `"{bf:a{foo}b}"'
zc bf_zz          graph_text `"{bf:a{zz:q}b}"'
zc it_bf_c        graph_text `"{it:a{bf}b}c"'
zc it_bf_cd       graph_text `"{it:a{bf:b}c}d"'
zc bf_sup         graph_text `"{bf:a{sup:2}}"'
zc amp_lblank     graph_text `"{ &alpha}"'
zc amp_rblank     graph_text `"{&alpha }"'
zc c233_rblank    graph_text `"{c 233 }"'
zc c233_lblank    graph_text `"{ c 233}"'
zc char_hex       graph_text `"{char 0xe9}"'
zc punct          graph_text `"{c 34}{c 36}{c 96}{c 123}{c 125}"'
zc del            graph_text `"a{c 127}b"'
zc serif2         graph_text `"{stSerif:a}{stSerif:b}"'
zc serif_part     graph_text `"{stSerif:a}b"'
zc sans           graph_text `"{stSans:s}"'
zc mono           graph_text `"{stMono:m}"'
zc it_unclosed_bf graph_text `"{it:{bf:a}"'
zc bf_extra_close graph_text `"{bf:a}}b"'
zc r_sup2         graph_text `"R{sup:2}"'
zc x_sub1         graph_text `"x{sub:1}"'
zc c0_first       graph_text `"{c 0}|"'
zc c0_mid         graph_text `"a{c 0}b"'
zc c0_after_bf    graph_text `"{bf:a}{c 0}"'
zc c0_after_c1    graph_text `"{c 1}a{c 0}"'
zc c0_in_bf       graph_text `"{bf:a{c 0}b}c"'
zc c0_qzq         graph_text `"s29qzq{c 0}x"'
zc c00            graph_text `"{c 00}x"'
zc char0          graph_text `"{char 0}x"'
zc c0x0           graph_text `"{c 0x0}x"'
zc c0_then_bf     graph_text `"a{c 0}b{bf:c}d"'
zc c0_nested      graph_text `"{bf:a{c 0}b{it:c}d}e"'
zc c0_symbol      graph_text `"a{c 0}{&alpha}b"'
zc c0_set         graph_text `"{bf}a{c 0}b{it}c"'
zc c0_plain_run   graph_text `"{bf:a}b{c 0}c{it:d}"'
zc c0_foo         graph_text `"{foo:a{c 0}b}c"'
zc c0_sup         graph_text `"a{c 0}b{sup:2}"'
zc c0_between     graph_text `"{it:x}{c 0}{bf:y}"'
zc c0_lead_bf     graph_text `"{c 0}{bf:y}"'
zc c0_in_bf_lead  graph_text `"{bf:{c 0}y}z"'
zc cmd            other_smcl `"{cmd:x}"'
zc hi             other_smcl `"{hi:x}"'
zc hline          other_smcl `"{hline 3}"'
zc ccl            other_smcl `"{ccl pi}"'
zc dup            other_smcl `"{dup 3:ab}"'
zc center         other_smcl `"{center:c}"'
zc stsym_alpha    difference `"{stSymbol:{&alpha}b}"'
_zg_flush

// ---- multi-line cases: the title lines of a graph with no axes -------------
capture program drop zl
program define zl
    args id opt
    global ZG_G = ${ZG_G} + 1
    capture graph drop zgg
    quietly twoway scatteri 0 0, xscale(off) yscale(off) `opt' name(zgg, replace)
    quietly graph export "${ZG_WORK}/gt_${ZG_G}.svg", name(zgg) replace as(svg)
    graph drop zgg
    file write ${ZG_FH} `"L${ZG_T}${ZG_G}${ZG_T}0${ZG_T}lines${ZG_T}`id'${ZG_T}graph_text${ZG_T}`opt'"' _n
end
zl ml_bf_line1   `"title("{bf:a}" "b")"'
zl ml_set_line1  `"title("{bf}a" "b")"'
zl ml_it_both    `"subtitle("{it:x}" "{it:y}")"'
zl ml_c0_line2   `"title("a" "b{c 0}c")"'
zl ml_c0_line1   `"title("a{c 0}b" "c")"'

file close `zgm'

// ===========================================================================
// JSON emission.  No callbacks into Stata from here on.
// ===========================================================================
python:
import json
import os
import re
import sys
from sfi import Macro

REPO = Macro.getGlobal("ZG_REPO")
sys.path.insert(0, os.path.join(REPO, "scripts"))
import svg_text_runs

WORK = Macro.getGlobal("ZG_WORK")
out = {
    "_meta": {
        "stata_version": Macro.getGlobal("ZG_SVER"),
        "born_date": Macro.getGlobal("ZG_BORN"),
        "dash_commit": Macro.getGlobal("ZG_COMMIT"),
        "extracted": Macro.getGlobal("ZG_DATE"),
        "c0_rule": ("{c 0} cuts off the rest of its own styled run on its "
                    "own line; text after the run's closing brace and other "
                    "lines are drawn (measured 08oct2026, scratch note "
                    "29-c0-truth.txt)"),
    },
    "symbols": {}, "chars": {}, "cnames": {}, "stsymbol": {}, "cases": [],
}
svgs = {}


def runs_of(g):
    if g not in svgs:
        svgs[g] = svg_text_runs.svg_text_runs(
            os.path.join(WORK, "gt_%s.svg" % g))
    return svgs[g]


def clean(runs):
    return [{"text": r["text"], "weight": r["weight"], "style": r["style"],
             "family": r["family"], "level": r["level"]}
            for r in runs if r["text"]]


with open(Macro.getGlobal("ZG_REC"), encoding="utf-8") as fh:
    rows = [l.rstrip("\n").split("\t", 6) for l in fh if l.strip()]
for kind, g, i, fam, key, cat, inp in rows:
    if kind == "L":
        lines = [clean(t["runs"]) for t in runs_of(g)]
        out["cases"].append({"id": key, "category": cat, "input": inp,
                             "lines": lines})
        continue
    pre = i + "_"
    found = None
    for t in runs_of(g):
        rs = t["runs"]
        if rs and rs[0]["text"].startswith(pre) and re.match(
                r"[0-9]+_", rs[0]["text"]).group(0) == pre:
            found = [dict(r) for r in rs]
            found[0]["text"] = found[0]["text"][len(pre):]
            break
    runs = clean(found or [])
    if fam == "cases":
        out["cases"].append({"id": key, "category": cat, "input": inp,
                             "lines": [runs]})
    elif fam == "stsymbol":
        out[fam][chr(int(key))] = "".join(r["text"] for r in runs)
    else:
        out[fam][key] = "".join(r["text"] for r in runs)

with open(Macro.getGlobal("ZG_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2, sort_keys=True, ensure_ascii=True)
    fh.write("\n")
print("wrote", Macro.getGlobal("ZG_OUT"), len(out["symbols"]),
      len(out["chars"]), len(out["cnames"]), len(out["stsymbol"]),
      len(out["cases"]))
end
