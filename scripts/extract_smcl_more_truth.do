*! extract_smcl_more_truth.do
*! WP-31 section 42 (E9, follow-up): twoway's drawing of {rcenter:},
*! {right:} and {col #}, of {ccl version}, and of {ccl} in a variable
*! label, a value label and an axis 3-9 title, for
*! test/fixtures/smcl_more_truth.json.
*!
*! Each probe draws one twoway graph and records every text of its SVG
*! (runs joined) that holds the probe's marker Q; nothing here changes a
*! graph set or any other persistent setting.
*!
*! Run with:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_smcl_more_truth.do
*!
*! The trailing python: block never calls back into Stata; a backtick in
*! it would be spelled \x60.
*! ---------------------------------------------------------------------------

clear all
set graphics off
set more off

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_smcl_more_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_smcl_more_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZM_REPO "`repo'"
global ZM_OUT  "${ZM_REPO}/test/fixtures/smcl_more_truth.json"

local scratch "`c(tmpdir)'dash_smcl_more_probe"
capture mkdir "`scratch'"
global ZM_WORK "`scratch'"
global ZM_REC  "`scratch'/smcl_more_manifest.txt"

global ZM_SVER = c(stata_version)
global ZM_BORN = c(born_date)
global ZM_DATE = c(current_date)

tempfile zsgitrev
quietly shell git -C "${ZM_REPO}" rev-parse HEAD > "`zsgitrev'"
tempname zsgfh
file open `zsgfh' using "`zsgitrev'", read text
file read `zsgfh' zsgitline
file close `zsgfh'
global ZM_COMMIT = trim(`"`zsgitline'"')
capture assert ustrregexm(`"${ZM_COMMIT}"', "^[0-9a-f]{40}$")
if _rc {
    display as error "extract_smcl_more_truth.do: git rev-parse HEAD did not print a 40-character commit"
    exit 498
}

// ---------------------------------------------------------------------------
// One graph per probe.  zm_done <key> exports the SVG and writes the
// manifest line: key, graph number, return code.  The commands are typed
// on their own lines.
// ---------------------------------------------------------------------------
tempname zmm
file open `zmm' using "${ZM_REC}", write text replace
global ZM_FH `zmm'
global ZM_G = 0
global ZM_T = char(9)

capture program drop zm_done
program define zm_done
    args key
    local rc = _rc
    global ZM_G = ${ZM_G} + 1
    if `rc' == 0 {
        quietly graph export "${ZM_WORK}/sm_${ZM_G}.svg", name(zmg) replace as(svg)
        graph drop zmg
    }
    file write ${ZM_FH} "`key'${ZM_T}${ZM_G}${ZM_T}`rc'" _n
end

capture program drop zm_title
program define zm_title
    args key inp
    capture graph drop zmg
    capture noisily twoway scatteri 0 0, xscale(off) yscale(off) title(`"Q`inp'"') name(zmg, replace)
    zm_done `key'
end

zm_title rcenter.even      "{rcenter:xy}"
zm_title rcenter.odd       "{rcenter:xyz}"
zm_title rcenter.after     "ab{rcenter:x}"
zm_title rcenter.width     "{rcenter 9:xy}"
zm_title rcenter.text      "{rcenter:xy}cd"
zm_title right.main        "{right:xy}"
zm_title right.after       "ab{right:x}"
zm_title right.text        "{right:x}cd"
zm_title right.width       "{right 9:xy}"
zm_title col.main          "{col 10}xy"
zm_title col.after         "abc{col 2}x"
zm_title col.one           "{col 1}x"
zm_title col.zero          "{col 0}x"
zm_title col.big           "{col 254}x"
zm_title col.over          "{col 255}x"
zm_title col.colon         "{col 5:x}"
zm_title ccl.version       "{ccl version}"
zm_title ccl.stata_version "{ccl stata_version}"
capture graph drop zmg
capture noisily version 16: twoway scatteri 0 0, xscale(off) yscale(off) title("Q{ccl version}") name(zmg, replace)
zm_done ccl.version16
capture program drop zm_v19
program define zm_v19
    version 19
    capture graph drop zmg
    capture noisily twoway scatteri 0 0, xscale(off) yscale(off) title("Q{ccl version}") name(zmg, replace)
    zm_done ccl.version19prog
end
zm_v19

sysuse auto, clear
label variable mpg "Qa {ccl pi} b"
capture graph drop zmg
capture noisily twoway scatter mpg weight, name(zmg, replace)
zm_done varlabel.ytitle
capture graph drop zmg
capture noisily twoway scatter mpg weight, legend(on) name(zmg, replace)
zm_done varlabel.legend
label define zmo 0 "Qd {ccl N}" 1 "Qf {hline 2}"
label values foreign zmo
capture graph drop zmg
capture noisily twoway scatter mpg foreign, xlabel(0 1, valuelabel) name(zmg, replace)
zm_done valuelabel.xlabel
label variable mpg "Mileage (mpg)"
capture graph drop zmg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(3)), ytitle("Qa {ccl pi} b", axis(3)) name(zmg, replace)
zm_done axis3.ytitle
capture graph drop zmg
capture noisily twoway (scatter mpg weight) (scatter price weight, yaxis(3)), ylabel(5000 "Qe {ccl N}", axis(3)) name(zmg, replace)
zm_done axis3.ylabel

file close `zmm'

python:
import json
import os
import sys
from sfi import Macro

REPO = Macro.getGlobal("ZM_REPO")
sys.path.insert(0, os.path.join(REPO, "scripts"))
import svg_text_runs

WORK = Macro.getGlobal("ZM_WORK")
out = {
    "_meta": {
        "stata_version": Macro.getGlobal("ZM_SVER"),
        "born_date": Macro.getGlobal("ZM_BORN"),
        "dash_commit": Macro.getGlobal("ZM_COMMIT"),
        "extracted": Macro.getGlobal("ZM_DATE"),
        "source": "scripts/extract_smcl_more_truth.do",
    },
}
with open(Macro.getGlobal("ZM_REC"), encoding="utf-8") as fh:
    rows = [l.rstrip("\n").split("\t", 2) for l in fh if l.strip()]
for key, g, rc in rows:
    rec = {"rc": int(rc)}
    if int(rc) == 0:
        texts = svg_text_runs.svg_text_runs(os.path.join(WORK, "sm_%s.svg" % g))
        joined = ["".join(r["text"] for r in t["runs"]) for t in texts]
        rec["texts"] = [t for t in joined if "Q" in t]
    out[key] = rec
with open(Macro.getGlobal("ZM_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2, sort_keys=True, ensure_ascii=True)
    fh.write("\n")
print("wrote", Macro.getGlobal("ZM_OUT"), len(out) - 1)
end
