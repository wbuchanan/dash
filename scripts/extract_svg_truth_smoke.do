*! extract_svg_truth_smoke.do
*! WP-28 S02: prove scripts/svg_truth.py and test/cert_svg.do against ONE
*! real Stata drawing.  Nothing here is guessed: the fixture records what
*! this run's `graph export' actually wrote and what the module and the
*! six Stata programs actually read back from it, plus the .Graph scale
*! members' own verdict (drawn and nodraw) beside the SVG-fitted extent --
*! a fact, not something later code is allowed to assume.
*!
*! Output: test/fixtures/svg_truth_smoke.json
*!         test/fixtures/svg_truth_smoke.svg  (the exported drawing itself)
*!
*! Run with (the script sets its own directories, so it is handed to the
*! wrapper directly -- CLAUDE.md rule 10, sections/BRIEF.md "Stata
*! invocation"):
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_svg_truth_smoke.do
*!
*! ---------------------------------------------------------------------------
*! TWO TRAPS, found the hard way and worth keeping (scripts/extract_axis_
*! truth.do's header explains both at length; restated here because this
*! script has its own python: block):
*!
*!   1. A python: block inside a .do file must never call back into Stata
*!      (SFIToolkit.stata()/stata()) -- it desynchronises the interpreter.
*!      This script's trailing python: block only reads files and Stata
*!      locals already computed; it issues no Stata command.
*!
*!   2. Stata expands a backtick/apostrophe pair as a local-macro reference
*!      even INSIDE a python: block.  A regex literal that needs a
*!      backtick spells it \x60.  scripts/svg_truth.py is a plain .py file,
*!      never a python: block, so ITS regexes may hold backticks freely;
*!      this file's own python: block holds none.
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
    display as error "extract_svg_truth_smoke.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_svg_truth_smoke.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZS_REPO "`repo'"
global ZS_OUT  "${ZS_REPO}/test/fixtures/svg_truth_smoke.json"
global ZS_SVG  "${ZS_REPO}/test/fixtures/svg_truth_smoke.svg"

local scratch "`c(tmpdir)'dash_svg_smoke"
capture mkdir "`scratch'"
global ZS_WORK "`scratch'"
global ZS_REC  "`scratch'/svg_smoke_records.txt"
display as text "probe scratch dir: ${ZS_WORK}"

global ZS_SVER   = c(stata_version)
global ZS_FLAV   = c(flavor)
global ZS_EDIT   = c(edition_real)
global ZS_BORN   = c(born_date)
global ZS_DATE   = c(current_date)
global ZS_SCHEME = c(scheme)

* ---------------------------------------------------------------------------
* Provenance stamp (D12): the dash commit this fixture was measured
* against.  A tempfile, never a Stata call from Python: `shell' runs the
* git command and redirects its stdout to the file; the do-file reads the
* file back with `file open'/`file read', never with `SFIToolkit.stata()'.
* ---------------------------------------------------------------------------
tempfile zsgitrev
quietly shell git -C "${ZS_REPO}" rev-parse HEAD > "`zsgitrev'"
tempname zsgfh
file open `zsgfh' using "`zsgitrev'", read text
file read `zsgfh' zsgitline
file close `zsgfh'
local dash_commit = trim(`"`zsgitline'"')
capture assert ustrregexm(`"`dash_commit'"', "^[0-9a-f]{40}$")
if _rc {
    display as error "extract_svg_truth_smoke.do: git rev-parse HEAD did not print a 40-character commit: `dash_commit'"
    exit 498
}

* ---------------------------------------------------------------------------
* Load cert_svg.do.  It computes its scripts/ directory from c(pwd)
* (test/cert_svg.do's header says so), so this script cd's into test/,
* loads it, and cd's straight back.
* ---------------------------------------------------------------------------
local zs_cwd `"`c(pwd)'"'
cd "${ZS_REPO}/test"
quietly do "cert_svg.do"
cd `"`zs_cwd'"'

tempname zsrfh
file open `zsrfh' using "${ZS_REC}", write text replace

* ---------------------------------------------------------------------------
* The smoke drawing (TR-02.3 step 3): two spaces in the title on purpose
* (the U+00A0 case).
* ---------------------------------------------------------------------------
sysuse auto, clear
twoway (scatter mpg weight if foreign == 0) (scatter mpg weight if foreign == 1), ///
    title("Smoke  title") ytitle("Miles per gallon") ///
    legend(order(1 "Domestic cars" 2 "Foreign cars")) ///
    yscale(range(0 60)) name(zsvg, replace)
local zs_command `"twoway (scatter mpg weight if foreign == 0) (scatter mpg weight if foreign == 1), title("Smoke  title") ytitle("Miles per gallon") legend(order(1 "Domestic cars" 2 "Foreign cars")) yscale(range(0 60))"'

cert_svg_export, name(zsvg) file("${ZS_WORK}/smoke.svg")
assert r(rc) == 0
local zs_exported `"`r(file)'"'
copy `"`zs_exported'"' "${ZS_SVG}", replace

* ---------------------------------------------------------------------------
* .Graph scale/tick members, drawn and nodraw (TR-02.3 step 5).  No Python.
* ---------------------------------------------------------------------------
foreach zs_ax in y x {
    cert_graph_scale, axis(`zs_ax') name(zsvg)
    file write `zsrfh' "PROBE drawn `zs_ax' min " "`=string(r(min), "%21.15g")'" _n
    file write `zsrfh' "PROBE drawn `zs_ax' max " "`=string(r(max), "%21.15g")'" _n
    file write `zsrfh' "PROBE drawn `zs_ax' curmin " "`=string(r(curmin), "%21.15g")'" _n
    file write `zsrfh' "PROBE drawn `zs_ax' curmax " "`=string(r(curmax), "%21.15g")'" _n
    file write `zsrfh' "PROBE drawn `zs_ax' major_min " "`=string(r(major_min), "%21.15g")'" _n
    file write `zsrfh' "PROBE drawn `zs_ax' major_max " "`=string(r(major_max), "%21.15g")'" _n
    file write `zsrfh' "PROBE drawn `zs_ax' major_delta " "`=string(r(major_delta), "%21.15g")'" _n
}

twoway (scatter mpg weight if foreign == 0) (scatter mpg weight if foreign == 1), ///
    title("Smoke  title") ytitle("Miles per gallon") ///
    legend(order(1 "Domestic cars" 2 "Foreign cars")) ///
    yscale(range(0 60)) nodraw name(zsvgn, replace)
foreach zs_ax in y x {
    cert_graph_scale, axis(`zs_ax') name(zsvgn)
    file write `zsrfh' "PROBE nodraw `zs_ax' min " "`=string(r(min), "%21.15g")'" _n
    file write `zsrfh' "PROBE nodraw `zs_ax' max " "`=string(r(max), "%21.15g")'" _n
    file write `zsrfh' "PROBE nodraw `zs_ax' curmin " "`=string(r(curmin), "%21.15g")'" _n
    file write `zsrfh' "PROBE nodraw `zs_ax' curmax " "`=string(r(curmax), "%21.15g")'" _n
    file write `zsrfh' "PROBE nodraw `zs_ax' major_min " "`=string(r(major_min), "%21.15g")'" _n
    file write `zsrfh' "PROBE nodraw `zs_ax' major_max " "`=string(r(major_max), "%21.15g")'" _n
    file write `zsrfh' "PROBE nodraw `zs_ax' major_delta " "`=string(r(major_delta), "%21.15g")'" _n
}
graph drop zsvgn

* ---------------------------------------------------------------------------
* cert_svg_* on the exported SVG (TR-02.3 step 6): what the PROGRAMS
* returned, so the fixture pins them beside what the module returns.
* ---------------------------------------------------------------------------
cert_svg_texts, file("${ZS_SVG}") list("${ZS_WORK}/smoke.texts.jsonl")
file write `zsrfh' "CERT cert_svg_texts n " "`=string(r(n))'" _n

cert_svg_has_text, file("${ZS_SVG}") text("Smoke  title")
file write `zsrfh' "CERT cert_svg_has_text title found " "`=string(r(found))'" _n
file write `zsrfh' "CERT cert_svg_has_text title count " "`=string(r(count))'" _n

cert_svg_has_text, file("${ZS_SVG}") text("Miles per gallon")
file write `zsrfh' "CERT cert_svg_has_text ytitle found " "`=string(r(found))'" _n

cert_svg_has_text, file("${ZS_SVG}") text("Domestic cars")
file write `zsrfh' "CERT cert_svg_has_text legend1 found " "`=string(r(found))'" _n

cert_svg_has_text, file("${ZS_SVG}") text("Foreign cars")
file write `zsrfh' "CERT cert_svg_has_text legend2 found " "`=string(r(found))'" _n

cert_svg_fills, file("${ZS_SVG}") markers list("${ZS_WORK}/smoke.fills.tsv")
file write `zsrfh' "CERT cert_svg_fills n " "`=string(r(n))'" _n
file write `zsrfh' "CERT cert_svg_fills colours " `"`r(colours)'"' _n

cert_svg_extent, file("${ZS_SVG}") axis(y)
file write `zsrfh' "CERT cert_svg_extent y low " "`=string(r(low), "%21.15g")'" _n
file write `zsrfh' "CERT cert_svg_extent y high " "`=string(r(high), "%21.15g")'" _n
file write `zsrfh' "CERT cert_svg_extent y space " `"`r(space)'"' _n

cert_svg_extent, file("${ZS_SVG}") axis(x)
file write `zsrfh' "CERT cert_svg_extent x low " "`=string(r(low), "%21.15g")'" _n
file write `zsrfh' "CERT cert_svg_extent x high " "`=string(r(high), "%21.15g")'" _n
file write `zsrfh' "CERT cert_svg_extent x space " `"`r(space)'"' _n

file close `zsrfh'
graph drop _all

* ===========================================================================
* Analysis + JSON emission.  This block reads files and Stata globals/
* locals only; it issues no Stata command (trap 1 above).
* ===========================================================================
python:
import json
import os
import sys
from sfi import Macro

ZS_REPO = Macro.getGlobal("ZS_REPO")
sys.path.insert(0, os.path.join(ZS_REPO, "scripts"))
import svg_truth

OUT = Macro.getGlobal("ZS_OUT")
SVG = Macro.getGlobal("ZS_SVG")
REC = Macro.getGlobal("ZS_REC")
COMMAND = Macro.getLocal("zs_command")
DASH_COMMIT = Macro.getLocal("dash_commit")

# ---- the record file: "KIND ...tokens... VALUE-is-the-rest-of-the-line" --
records = []
with open(REC, encoding="utf-8") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if not line:
            continue
        parts = line.split(" ")
        records.append(parts)

def _num(s):
    if s is None or s == ".":
        return None
    try:
        return float(s)
    except ValueError:
        return None

probes = {"drawn": {"y": {}, "x": {}}, "nodraw": {"y": {}, "x": {}}}
cert = []
for parts in records:
    kind = parts[0]
    if kind == "PROBE":
        _, state, axis, member, value = parts
        probes[state][axis][member] = _num(value)
    elif kind == "CERT":
        cert.append(parts[1:])

# ---- the module's own reading of the same SVG ----------------------------
texts = svg_truth.svg_texts(SVG)
title = {"text": "Smoke  title", "found": svg_truth.svg_has_text(SVG, "Smoke  title")}
ytitle = {"text": "Miles per gallon",
          "found": svg_truth.svg_has_text(SVG, "Miles per gallon")}
legend = {
    "texts": ["Domestic cars", "Foreign cars"],
    "found": [svg_truth.svg_has_text(SVG, "Domestic cars"),
              svg_truth.svg_has_text(SVG, "Foreign cars")],
}
marker_fills = svg_truth.svg_marker_fills(SVG)
y_extent = svg_truth.svg_axis_extent(SVG, "y")
x_extent = svg_truth.svg_axis_extent(SVG, "x")

# ---- which .Graph member (if any) agrees with the SVG-fitted extent ------
tol = 0.005 * (y_extent["high"] - y_extent["low"]) if y_extent else None
candidates = [
    ("plotregion1.yscale.min_max", "min", "max"),
    ("plotregion1.yscale.curmin_curmax", "curmin", "curmax"),
    ("yaxis1.major.min_max", "major_min", "major_max"),
]
matches_svg = {}
drawn_member = "none"
if y_extent is not None:
    for name, lo_key, hi_key in candidates:
        lo, hi = probes["drawn"]["y"].get(lo_key), probes["drawn"]["y"].get(hi_key)
        ok = (lo is not None and hi is not None
              and abs(min(lo, hi) - y_extent["low"]) <= tol
              and abs(max(lo, hi) - y_extent["high"]) <= tol)
        matches_svg[name] = ok
        if ok and drawn_member == "none":
            drawn_member = name
matches_svg["drawn_extent_member"] = drawn_member

cert_programs = []
for parts in cert:
    program = parts[0]
    rest = parts[1:]
    if program == "cert_svg_texts":
        cert_programs.append({"program": program, "n": int(rest[-1])})
    elif program == "cert_svg_has_text":
        which, field, value = rest
        cert_programs.append({"program": program, "which": which,
                              "field": field, "value": _num(value)})
    elif program == "cert_svg_fills":
        field = rest[0]
        value = " ".join(rest[1:])
        if field == "n":
            cert_programs.append({"program": program, "n": int(value)})
        else:
            cert_programs.append({"program": program, "colours": value.split()})
    elif program == "cert_svg_extent":
        axis, field, value = rest
        cert_programs.append({"program": program, "axis": axis, "field": field,
                              "value": value if field == "space" else _num(value)})

doc = {
    "_meta": {
        "stata_version": Macro.getGlobal("ZS_SVER"),
        "flavor": Macro.getGlobal("ZS_FLAV"),
        "edition": Macro.getGlobal("ZS_EDIT"),
        "born_date": Macro.getGlobal("ZS_BORN"),
        "extracted": Macro.getGlobal("ZS_DATE"),
        "source": "scripts/extract_svg_truth_smoke.do",
        "dash_commit": DASH_COMMIT,
        "scheme": Macro.getGlobal("ZS_SCHEME"),
        "command": COMMAND,
        "script": "scripts/extract_svg_truth_smoke.do",
        "svg": "test/fixtures/svg_truth_smoke.svg",
    },
    "texts": texts,
    "title": title,
    "ytitle": ytitle,
    "legend": legend,
    "marker_fills": marker_fills,
    "y_extent": y_extent,
    "x_extent": x_extent,
    "graph_probe": probes,
    "matches_svg": matches_svg,
    "cert_programs": cert_programs,
    "unverified": [],
}

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2, sort_keys=True)
end

display as text "WROTE ${ZS_OUT}"
