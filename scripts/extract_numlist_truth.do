*! extract_numlist_truth.do
*! WP-34 section 34-08 (DG-3): ground truth for the values Stata's numlist
*! makes, for test/fixtures/numlist_truth.json.
*!
*! WHY THIS EXISTS
*!
*! ylabel(-.3(.1).3) labels -.3 -.2 -.1 0 .1 .2 .3 in twoway; dash built
*! each value as a + b*k in plain floats, so the middle tick sat at
*! 5.551e-17 and was labelled so.  This script asks Stata's numlist each
*! rule and records r(numlist) and each of its values as %21x (converted
*! to a JSON double exactly in the python block).  For three rules that
*! cross zero it also draws twoway scatter y x, ylabel(<rule>) and records
*! the ticks twoway placed (.Graph.yaxis1.major.dlg_tickpos, as text and
*! as %21x) and the y-axis label texts of the exported SVG.
*!
*! Output: test/fixtures/numlist_truth.json
*!
*! Run with (the script sets its own directories, so it is handed to the
*! wrapper directly):
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_numlist_truth.do
*!
*! Never calls back into Stata from the trailing python: block; a backtick
*! inside it is spelled \x60.
*! ---------------------------------------------------------------------------

clear all
set graphics off
set more off
set linesize 255

* Root: DASH_REPO, else the current directory when it is a dash tree;
* never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_numlist_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_numlist_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1
global ZN_REPO "`repo'"
global ZN_OUT  "`repo'/test/fixtures/numlist_truth.json"

local work "`c(tmpdir)'dash_numlist_probe"
capture mkdir "`work'"
global ZN_WORK "`work'"
display as text "probe work dir: ${ZN_WORK}"

set scheme stcolor

global ZN_SVER = c(stata_version)
global ZN_BORN = c(born_date)
global ZN_DATE = "`c(current_date)' `c(current_time)'"

// Provenance stamp: shell writes the commit into a file, read back.
tempfile zngitrev
quietly shell git -C "${ZN_REPO}" rev-parse HEAD > "`zngitrev'"
tempname zngfh
file open `zngfh' using "`zngitrev'", read text
file read `zngfh' zngitline
file close `zngfh'
global ZN_COMMIT = trim(`"`zngitline'"')
capture assert ustrregexm(`"${ZN_COMMIT}"', "^[0-9a-f]{40}$")
if _rc {
    display as error "extract_numlist_truth.do: git rev-parse HEAD did not print a 40-character commit"
    exit 498
}

// ---------------------------------------------------------------------------
// The rules (section 34-08 TR-34-08.4), separated by |.
// ---------------------------------------------------------------------------
local rules "-.3(.1).3|-.7(.1).7|-.6(.2).6|1(-.1)-1|-.05(.01).05|-3(.3)3"
local rules "`rules'|-.3[.1].3|-.3 -.2 to .3|-.3 -.2:.3|0(.1)1|-2/2"
local rules "`rules'|-1e-5(1e-6)1e-5|0(.3333333333333333)1"
local rules "`rules'|123456.123456789(1)123458|0(1.234567890123456)3"
local rules "`rules'|-1(0.0000001234567891)-0.9999995|1e6(.25)1000001"
local rules "`rules'|-.000123456789012345(.0001)0|12345678.123456(1)12345680"
local rules "`rules'|100000.1(.1)100000.5|1e13(1e12)1.2e13|1e14(1e13)1.2e14"
local rules "`rules'|1e-100(1e-101)1.2e-100|0.30000000000000004|0(.333333333334)1"
local rules "`rules'|-1(1.00000000000002)2|-2(1.00000000000003)0"
local rules "`rules'|-1(1.000000000000025)1|-1(.250000000000002)1"
local rules "`rules'|-4(4.00000000000006)4|-4(4.00000000000012)4"
local rules "`rules'|-1(.99999999999999)1|1e150(1e149)1.2e150"

tempname fh
file open `fh' using "${ZN_WORK}/rules.tsv", write text replace
local nrule 0
local rest "`rules'"
while `"`rest'"' != "" {
    gettoken r rest : rest, parse("|")
    if `"`r'"' == "|" continue
    local ++nrule
    numlist "`r'"
    local txt "`r(numlist)'"
    local hx ""
    foreach w of local txt {
        local h : display %21x `w'
        local hx "`hx' `=trim("`h'")'"
    }
    file write `fh' "`r'" _tab "`txt'" _tab "`=trim("`hx'")'" _n
}
file close `fh'
display as text "rules measured: `nrule'"

// ---------------------------------------------------------------------------
// The drawn rules: twoway scatter y x, ylabel(<rule>).
// ---------------------------------------------------------------------------
file open `fh' using "${ZN_WORK}/drawn.tsv", write text replace
local k 0
foreach r in "-.3(.1).3" "-.7(.1).7" "-.6(.2).6" {
    local ++k
    clear
    quietly set obs 11
    quietly gen x = _n
    quietly gen y = (_n - 6) / 10 * 7
    capture graph drop _all
    quietly twoway scatter y x, ylabel(`r')
    local nt "`.Graph.yaxis1.major.dlg_tickpos.arrnels'"
    if "`nt'" == "" | "`nt'" == "." local nt 0
    local tt ""
    local hx ""
    forvalues i = 1/`nt' {
        local t "`.Graph.yaxis1.major.dlg_tickpos[`i']'"
        local tt "`tt' `t'"
        local h : display %21x `t'
        local hx "`hx' `=trim("`h'")'"
    }
    capture erase "${ZN_WORK}/d`k'.svg"
    quietly graph export "${ZN_WORK}/d`k'.svg", name(Graph) replace
    file write `fh' "`r'" _tab "`=trim("`tt'")'" _tab "`=trim("`hx'")'" _tab "d`k'.svg" _n
}
file close `fh'
capture graph drop _all

// ===========================================================================
// JSON emission.  No callbacks into Stata from here on.
// REMINDER: no backtick may appear literally in this block.
// ===========================================================================
python:
import json
import os
import sys
from sfi import Macro

ZN_REPO = Macro.getGlobal("ZN_REPO")
sys.path.insert(0, os.path.join(ZN_REPO, "scripts"))
import svg_truth

W = Macro.getGlobal("ZN_WORK")
OUT = Macro.getGlobal("ZN_OUT")


def _hex(h):
    """Stata's %21x text (e.g. -1.999999999999aX-003) as the double."""
    h = h.strip()
    sign = -1.0 if h.startswith("-") else 1.0
    body = h.lstrip("+-")
    mant, exp = body.split("X")
    if mant.startswith("0."):
        return 0.0
    return sign * float.fromhex("0x" + mant + "p" + str(int(exp, 16)))


def _rows(name):
    with open(os.path.join(W, name), encoding="utf-8") as fh:
        return [ln.rstrip("\n").split("\t") for ln in fh if ln.strip()]


rules = {}
for rule, text, hx in _rows("rules.tsv"):
    rules[rule] = {"text": text, "values": [_hex(h) for h in hx.split()]}

drawn = {}
for rule, ticks_text, hx, svg in _rows("drawn.tsv"):
    doc = svg_truth.svg_document(os.path.join(W, svg))
    left = doc["plotregion"]["left"]
    labs = [e for e in doc["texts"]
            if e["x"] is not None and e["x"] < left
            and svg_truth.label_value(e["text"]) is not None]
    labs.sort(key=lambda e: -float(e["y"]))
    drawn[rule] = {"ticks": [_hex(h) for h in hx.split()],
                   "ticks_text": ticks_text,
                   "labels": [e["text"] for e in labs]}

doc = {
    "_meta": {
        "stata_version": Macro.getGlobal("ZN_SVER"),
        "born_date": Macro.getGlobal("ZN_BORN"),
        "dash_commit": Macro.getGlobal("ZN_COMMIT"),
        "extracted": Macro.getGlobal("ZN_DATE"),
        "scheme": "stcolor",
        "source": "scripts/extract_numlist_truth.do",
        "rules": len(rules),
        "method": ("rules: numlist \"<rule>\"; text is r(numlist), values "
                   "each of its words as %21x, read exactly. drawn: twoway "
                   "scatter y x, ylabel(<rule>) on set obs 11, x = _n, "
                   "y = (_n-6)/10*7; ticks are "
                   ".Graph.yaxis1.major.dlg_tickpos as %21x (ticks_text as "
                   "the class wrote them), labels the exported SVG's "
                   "numeric texts left of the plot region, bottom to top."),
    },
    "rules": rules,
    "drawn": drawn,
}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, ensure_ascii=False, indent=1, sort_keys=True)
    fh.write("\n")
print("WROTE %s rules=%d drawn=%d" % (OUT, len(rules), len(drawn)))
end
