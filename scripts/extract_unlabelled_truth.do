*! extract_unlabelled_truth.do
*! WP-29 section 03 (P0.3): ground truth for how twoway names an
*! UNLABELLED variable, for test/fixtures/unlabelled_truth.json, in
*! scripts/extract_text_truth.do's shape.
*!
*! WHY THIS EXISTS
*!
*! Stata's exporter writes an unlabelled variable's label as "" (jsonio
*! layout, dash_render._dash_write_stata_data).  twoway then draws the
*! variable's NAME as its axis title, legend key and colour-key title; a
*! label of blanks is not empty and is drawn as given.  This script runs
*! each probe through real Stata (scheme s2color, 12 generated
*! observations) and records what twoway's own SVG export drew, through the
*! shared reader scripts/svg_truth.py (test/cert_svg.do).
*!
*! Output: test/fixtures/unlabelled_truth.json
*!
*! Run with (the script sets its own directories, so it is handed to the
*! wrapper directly -- CLAUDE.md rule 10):
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_unlabelled_truth.do
*!
*! METHOD
*!
*! Every probe is registered by `zu id setup command option control` (five
*! arguments).  Before each probe `_zu_data` regenerates the data, then
*! `setup` (one Stata command, or empty) is run -- `label variable y1
*! "First"`, or the script's own `_zu_label_xy`.  The probe is run as
*! `command'[, option'] name(zqu, replace)` (`_zu_has_top_comma` decides
*! whether the option joins a top-level comma list already present) and
*! exported to SVG.  `control` names the probe's legend(off) twin, whose
*! texts are subtracted (by multiset) to give the legend keys.
*!
*! Per probe the fixture records "command", "setup", "rc", "labels" (each
*! variable's label as Stata holds it), "texts" ([text, size, fill, rotate,
*! x, y] of every <text> that is not a number, in document order),
*! "rotated" ([text, x] of the rotate(-90) texts, sorted by x), "flat" (the
*! non-rotated texts) and, with a control, "keys_in_drawn_order" (the
*! probe's entries minus the control's, sorted by y then x).
*!
*! Never calls back into Stata from the trailing python: block; a backtick
*! inside it is spelled \x60.
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
    display as error "extract_unlabelled_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_unlabelled_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZU_REPO "`repo'"
global ZU_OUT  "${ZU_REPO}/test/fixtures/unlabelled_truth.json"

local scratch "`c(tmpdir)'dash_unlabelled_probe"
capture mkdir "`scratch'"
global ZU_WORK "`scratch'"
global ZU_REC  "`scratch'/unlabelled_records.txt"
display as text "probe scratch dir: ${ZU_WORK}"

set scheme s2color

global ZU_SVER   = c(stata_version)
global ZU_BORN   = c(born_date)
global ZU_DATE   = c(current_date)
global ZU_SCHEME = c(scheme)

// ---------------------------------------------------------------------------
// Provenance stamp (D12): `shell' writes the commit into a file, the
// do-file reads the file back, never a Stata call from Python.
// ---------------------------------------------------------------------------
tempfile zugitrev
quietly shell git -C "${ZU_REPO}" rev-parse HEAD > "`zugitrev'"
tempname zugfh
file open `zugfh' using "`zugitrev'", read text
file read `zugfh' zugitline
file close `zugfh'
local dash_commit = trim(`"`zugitline'"')
capture assert ustrregexm(`"`dash_commit'"', "^[0-9a-f]{40}$")
if _rc {
    display as error "extract_unlabelled_truth.do: git rev-parse HEAD did not print a 40-character commit: `dash_commit'"
    exit 498
}

// Load cert_svg.do: it computes its scripts/ directory from c(pwd), so cd
// into test/, load it, and cd straight back.
local zu_cwd `"`c(pwd)'"'
cd "${ZU_REPO}/test"
quietly do "cert_svg.do"
cd `"`zu_cwd'"'

// ---------------------------------------------------------------------------
// _zu_has_top_comma: whether *s* has a comma outside every parenthesis.
// ---------------------------------------------------------------------------
capture program drop _zu_has_top_comma
program define _zu_has_top_comma, rclass
    version 16.0
    args s
    local depth = 0
    local found = 0
    local n = length(`"`s'"')
    forvalues i = 1/`n' {
        local ch = substr(`"`s'"', `i', 1)
        if `"`ch'"' == "(" local depth = `depth' + 1
        else if `"`ch'"' == ")" local depth = max(`depth' - 1, 0)
        else if `"`ch'"' == "," & `depth' == 0 local found = 1
    }
    return scalar found = `found'
end

// ---------------------------------------------------------------------------
// The data: deterministic, so pytest mirrors them exactly.  No variable is
// labelled.
// ---------------------------------------------------------------------------
capture program drop _zu_data
program define _zu_data
    clear
    quietly set obs 12
    gen double y = _n + 0.5
    gen double y1 = _n
    gen double y2 = _n + 3
    gen double x = _n*2
    gen double z = mod(_n,4)
    gen g = mod(_n,2)
    gen double w = _n*1.5
    gen t = mdy(1,1,2000)+_n
    format t %td
end

capture program drop _zu_label_xy
program define _zu_label_xy
    label variable x "Horizontal"
    label variable y "Vertical"
end

// ===========================================================================
// Registration
// ===========================================================================
global ZU_N = 0
capture program drop zu
program define zu
    global ZU_N = ${ZU_N} + 1
    global ZU_ID_${ZU_N}  `"`1'"'
    global ZU_SET_${ZU_N} `"`2'"'
    global ZU_CMD_${ZU_N} `"`3'"'
    global ZU_OPT_${ZU_N} `"`4'"'
    global ZU_CTL_${ZU_N} `"`5'"'
end

zu "ul_scatter"          ""                            "twoway scatter y x" "" ""
zu "ul_multi_y"          ""                            "twoway scatter y1 y2 x" "" "ul_multi_y__off"
zu "ul_multi_y__off"     ""                            "twoway scatter y1 y2 x" "legend(off)" ""
zu "ul_two_layers"       ""                            "twoway (scatter y1 x) (scatter y2 x)" "" "ul_two_layers__off"
zu "ul_two_layers__off"  ""                            "twoway (scatter y1 x) (scatter y2 x)" "legend(off)" ""
zu "ul_mixed"            `"label variable y1 "First""' "twoway (scatter y1 x) (scatter y2 x)" "" "ul_mixed__off"
zu "ul_mixed__off"       `"label variable y1 "First""' "twoway (scatter y1 x) (scatter y2 x)" "legend(off)" ""
zu "ul_blank_title"      `"label variable w "   ""'     "twoway scatter w x" "" ""
zu "ul_blank_key"        `"label variable w "   ""'     "twoway (scatter w x) (scatter y2 x)" "" "ul_blank_key__off"
zu "ul_blank_key__off"   `"label variable w "   ""'     "twoway (scatter w x) (scatter y2 x)" "legend(off)" ""
zu "ul_fit"              ""                            "twoway (scatter y x) (lfit y x)" "" "ul_fit__off"
zu "ul_fit__off"         ""                            "twoway (scatter y x) (lfit y x)" "legend(off)" ""
zu "ul_hist"             ""                            "twoway histogram x" "" ""
zu "ul_kdensity"         ""                            "twoway kdensity x" "" ""
zu "ul_hist_kd"          ""                            "twoway (histogram x) (kdensity x)" "" "ul_hist_kd__off"
zu "ul_hist_kd__off"     ""                            "twoway (histogram x) (kdensity x)" "legend(off)" ""
zu "ul_histpct_kd"       ""                            "twoway (histogram x, percent) (kdensity x)" "" "ul_histpct_kd__off"
zu "ul_histpct_kd__off"  ""                            "twoway (histogram x, percent) (kdensity x)" "legend(off)" ""
zu "ul_histfreq_kd"      ""                            "twoway (histogram x, frequency) (kdensity x)" "" "ul_histfreq_kd__off"
zu "ul_histfreq_kd__off" ""                            "twoway (histogram x, frequency) (kdensity x)" "legend(off)" ""
zu "ul_histfrac_kd"      ""                            "twoway (histogram x, fraction) (kdensity x)" "" "ul_histfrac_kd__off"
zu "ul_histfrac_kd__off" ""                            "twoway (histogram x, fraction) (kdensity x)" "legend(off)" ""
zu "ul_kd2"              ""                            "twoway (kdensity x) (kdensity y)" "" "ul_kd2__off"
zu "ul_kd2__off"         ""                            "twoway (kdensity x) (kdensity y)" "legend(off)" ""
zu "ul_kd_labelled"      "_zu_label_xy"                "twoway (kdensity x) (kdensity y)" "" "ul_kd_labelled__off"
zu "ul_kd_labelled__off" "_zu_label_xy"                "twoway (kdensity x) (kdensity y)" "legend(off)" ""
zu "ul_by"               ""                            "twoway scatter y x" "by(g)" ""
zu "ul_by_labelled"      `"label variable g "Group""'  "twoway scatter y x" "by(g)" ""
zu "ul_colorvar"         ""                            "twoway scatter y x" "colorvar(z)" ""
zu "ul_legend_on"        ""                            "twoway scatter y x" "legend(on)" "ul_legend_on__off"
zu "ul_legend_on__off"   ""                            "twoway scatter y x" "legend(off)" ""
zu "ul_xlabelled"        `"label variable x "Horizontal""' "twoway scatter y x" "" ""
zu "ul_date"             ""                            "twoway line y t" "" ""
zu "ul_axis2"            ""                            "twoway (scatter y x) (scatter y1 x, yaxis(2))" "" ""
zu "ul_ytitle_size"      ""                            "twoway scatter y x" "ytitle(, size(large))" ""
zu "ul_rcap"             ""                            "twoway rcap y1 y2 x" "" ""
zu "ul_range_key"        ""                            "twoway (rarea y1 y2 x) (scatter y x)" "" "ul_range_key__off"
zu "ul_range_key__off"   ""                            "twoway (rarea y1 y2 x) (scatter y x)" "legend(off)" ""

// ===========================================================================
// Export loop
// ===========================================================================
tempname zurfh
file open `zurfh' using "${ZU_REC}", write text replace

local N = $ZU_N
forvalues i = 1/`N' {
    local id  "${ZU_ID_`i'}"
    local setup `"${ZU_SET_`i'}"'
    local cmd `"${ZU_CMD_`i'}"'
    local opt `"${ZU_OPT_`i'}"'
    local ctl "${ZU_CTL_`i'}"

    _zu_data
    if `"`macval(setup)'"' != "" {
        `macval(setup)'
    }

    if `"`opt'"' == "" {
        local full  `"`cmd', name(zqu, replace)"'
        local shown `"`cmd'"'
    }
    else {
        _zu_has_top_comma `"`cmd'"'
        if r(found) {
            local full  `"`cmd' `opt' name(zqu, replace)"'
            local shown `"`cmd' `opt'"'
        }
        else {
            local full  `"`cmd', `opt' name(zqu, replace)"'
            local shown `"`cmd', `opt'"'
        }
    }

    local svg "${ZU_WORK}/`id'.svg"
    capture erase "`svg'"

    capture graph drop zqu
    capture noisily `full'
    local rc = _rc
    local rcx = .
    if `rc' == 0 {
        capture graph export "`svg'", name(zqu) replace
        local rcx = _rc
    }
    capture graph drop zqu
    file write `zurfh' `"P|`id'|`rc'|`rcx'|`svg'|`ctl'|`shown'|`macval(setup)'"' _n
    foreach v in x y y1 y2 z g t w {
        local lab : variable label `v'
        file write `zurfh' `"L|`id'|`v'|`macval(lab)'"' _n
    }
    display as text "probe `id' rc=`rc' svg_rc=`rcx'"
}
file close `zurfh'
display as text "records written to ${ZU_REC}"

// ===========================================================================
// Analysis + JSON emission.  No callbacks into Stata from here on.
//
// REMINDER: no backtick may appear literally in this block.
// ===========================================================================
python:
import collections
import json
import os
import sys
from sfi import Macro

ZU_REPO = Macro.getGlobal("ZU_REPO")
sys.path.insert(0, os.path.join(ZU_REPO, "scripts"))
import svg_truth

OUT = Macro.getGlobal("ZU_OUT")
REC = Macro.getGlobal("ZU_REC")
DASH_COMMIT = Macro.getLocal("dash_commit")

probes_raw, order = {}, []
with open(REC, encoding="utf-8") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if line.startswith("P|"):
            _, pid, rc, rcx, svgpath, ctl, shown, setup = line.split("|", 7)
            probes_raw[pid] = {
                "rc": int(rc), "rcx": (int(rcx) if rcx != "." else None),
                "svg": svgpath, "control": ctl, "command": shown,
                "setup": setup, "labels": {},
            }
            order.append(pid)
        elif line.startswith("L|"):
            _, pid, var, lab = line.split("|", 3)
            probes_raw[pid]["labels"][var] = lab

entries_cache = {}
for pid, info in probes_raw.items():
    ok = info["rc"] == 0 and info["rcx"] == 0
    ents = svg_truth.svg_texts(info["svg"]) if ok else []
    entries_cache[pid] = [e for e in ents
                          if svg_truth.label_value(e["text"]) is None]

probes_out = {}
for pid in order:
    info = probes_raw[pid]
    entries = entries_cache[pid]
    texts = [[e["text"], e["size"], e["fill"], e["rotate"], e["x"], e["y"]]
             for e in entries]
    rotated = sorted(([e["text"], e["x"]] for e in entries
                      if e["rotate"] == -90.0),
                     key=lambda r: float(r[1] or 0.0))
    flat = [e["text"] for e in entries if e["rotate"] != -90.0]
    rec = {
        "command": info["command"],
        "setup": info["setup"],
        "rc": info["rc"] if info["rc"] != 0 else (info["rcx"] or 0),
        "control": info["control"],
        "labels": info["labels"],
        "texts": texts,
        "rotated": rotated,
        "flat": flat,
    }
    ctl = info["control"]
    if ctl:
        ctl_counts = collections.Counter(
            e["text"] for e in entries_cache.get(ctl, []))
        added_counts = (collections.Counter(e["text"] for e in entries)
                        - ctl_counts)
        seen_e, added_e = collections.Counter(), []
        for e in entries:
            if seen_e[e["text"]] < added_counts.get(e["text"], 0):
                added_e.append(e)
                seen_e[e["text"]] += 1
        added_e.sort(key=lambda e: (float(e.get("y") or 0.0),
                                    float(e.get("x") or 0.0)))
        rec["keys_in_drawn_order"] = [e["text"] for e in added_e]
    probes_out[pid] = rec

doc = {
    "_meta": {
        "stata_version": Macro.getGlobal("ZU_SVER"),
        "born_date": Macro.getGlobal("ZU_BORN"),
        "extracted": Macro.getGlobal("ZU_DATE"),
        "source": "scripts/extract_unlabelled_truth.do",
        "dash_commit": DASH_COMMIT,
        "scheme_in_force": Macro.getGlobal("ZU_SCHEME"),
        "method": ("Each probe regenerates 12 unlabelled observations "
                   "(_zu_data), runs its setup, exports the twoway command "
                   "to SVG and reads it through scripts/svg_truth.py; "
                   "texts exclude numeric tick labels; keys_in_drawn_order "
                   "are the probe's <text> entries minus its legend(off) "
                   "twin's, by multiset, sorted by (y, x)."),
    },
    "probes": probes_out,
}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2, sort_keys=True)
    fh.write("\n")
print("WROTE %s" % OUT)
print("probes=%d" % len(probes_out))
end

display as text "extract_unlabelled_truth.do: done"
