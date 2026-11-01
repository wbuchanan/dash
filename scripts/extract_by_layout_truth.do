*! extract_by_layout_truth.do
*! WP-41 section 41-05: ground truth for by()'s layout -- compact beside
*! style() and its outlines (BY-4), aspectratio() with the shrink words
*! (BY-5), by(, total) with no variables (BY-6), style(combine)'s regions,
*! labels and titles beside the panels, aspectratio() and a smaller graph
*! margin under by() (BY-18), equal plot regions across a row (VF-6) and
*! xoverhangs under by() and on the end labels (GW-5) -- for
*! test/fixtures/by_layout_truth.json.
*!
*! Output: test/fixtures/by_layout_truth.json
*!
*! Run with:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_by_layout_truth.do
*!
*! METHOD
*!
*! `bl id scheme "command"' reloads auto, runs `twoway <command>
*! name(Graph, replace)' under a text log and exports the graph to SVG.
*! The return code goes to a record file.  The trailing python: block
*! reads files only (never calls Stata; a backtick is spelled \x60) and
*! keeps, per probe, the rc, the first log line after the command (the
*! error text when it fails), the SVG's canvas, every rect at least 3
*! units on a side (fill, stroke, stroke width) and every text.
*! ---------------------------------------------------------------------------

clear all
set graphics off
set more off
set linesize 255
version 19

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zl_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zl_bad' {
    display as error "extract_by_layout_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zl_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zl_rc' | _rc {
    local _zl_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_by_layout_truth.do: `_zl_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global BL_REPO "`repo'"
global BL_OUT  "`repo'/test/fixtures/by_layout_truth.json"
local scratch "`c(tmpdir)'dash_by_layout_probe"
capture mkdir "`scratch'"
global BL_WORK "`scratch'"
global BL_REC  "`scratch'/by_layout_records.txt"
global BL_BASE "`c(sysdir_base)'"

global BL_SVER = c(stata_version)
global BL_BORN = c(born_date)
global BL_DATE = c(current_date) + " " + c(current_time)

tempfile blgitrev
quietly shell git -C "${BL_REPO}" rev-parse HEAD > "`blgitrev'"
tempname blgfh
file open `blgfh' using "`blgitrev'", read text
file read `blgfh' blgitline
file close `blgfh'
global BL_COMMIT = trim(`"`blgitline'"')
capture assert ustrregexm(`"${BL_COMMIT}"', "^[0-9a-f]{40}$")
if _rc {
    display as error "extract_by_layout_truth.do: git rev-parse HEAD did not print a 40-character commit: ${BL_COMMIT}"
    exit 498
}


sysuse auto, clear
keep mpg weight price foreign rep78
quietly save "${BL_WORK}/bl.dta", replace

// ---------------------------------------------------------------------------
// bl id scheme "command": one probe, exported to SVG.
// ---------------------------------------------------------------------------
capture program drop bl
program define bl
    version 19
    args id scheme cmd
    use "${BL_WORK}/bl.dta", clear
    set scheme `scheme'
    quietly log using "${BL_WORK}/`id'.log", text replace name(bllog)
    capture noisily twoway `cmd' name(Graph, replace)
    local rc = _rc
    local xrc = 0
    if !`rc' {
        capture noisily graph export "${BL_WORK}/`id'.svg", name(Graph) replace
        local xrc = _rc
    }
    quietly log close bllog
    file write blrec "R|`id'|`scheme'|`rc'|`xrc'|" `"`cmd'"' _n
end

file open blrec using "${BL_REC}", write text replace

local one "scatter mpg weight"
local two "(scatter mpg weight)(lfit mpg weight)"

// BY-4: compact beside style(); compact's outlines
bl Y01 stcolor `"`one', by(foreign, total)"'
bl Y02 stcolor `"`one', by(foreign, total style(default) compact)"'
bl Y03 stcolor `"`one', by(foreign, total compact style(default))"'
bl Y04 s2color `"`one', by(foreign, compact)"'
bl Y04b stcolor `"`one', by(foreign, compact)"'
bl Y04c s2color `"`one', by(foreign)"'
// BY-5: aspectratio() with the shrink words
bl Y05 stcolor `"`one', aspectratio(1) by(foreign, shrink)"'
bl Y06 stcolor `"`one', aspectratio(1) by(foreign, overallshrink)"'
bl Y07 stcolor `"`one', aspectratio(1) by(foreign, shr)"'
bl Y08 stcolor `"`one', aspectratio(1) by(foreign, ishrink)"'
bl Y08b stcolor `"`one', aspectratio(1) by(foreign, overallshr)"'
bl Y08c stcolor `"`one', aspectratio(1) by(foreign, total shrink)"'
bl Y08d stcolor `"`one', aspectratio(1) by(foreign, noshrink)"'
bl Y08e stcolor `"`one', by(foreign, shrink) aspectratio(1)"'
// BY-6: by(, total) with no variables
bl Y09 stcolor `"`one', by(, total)"'
// BY-18: combine's regions, beside labels and titles, aspect, margin
bl Y10 stcolor `"`two', by(rep78, style(combine))"'
bl Y10d stcolor `"`two', by(rep78)"'
bl Y11 stcolor `"`one', subtitle(, position(3)) by(foreign)"'
bl Y12 stcolor `"`one', subtitle(, position(9)) by(foreign)"'
bl Y11d stcolor `"`one', by(foreign)"'
bl Y13 stcolor `"`one', by(foreign, title("T", position(3)))"'
bl Y13b stcolor `"`one', by(foreign, title("T", position(9)))"'
bl Y14 stcolor `"`one', aspectratio(1) by(foreign)"'
bl Y15 stcolor `"`one', by(foreign, graphregion(margin(small)))"'
bl Y16 stcolor `"`one', by(foreign, graphregion(margin(zero)))"'
// VF-6: equal plot regions across a row
bl Y17 stcolor `"scatter price weight, ylabel(, format(%15.2fc)) by(rep78)"'
// GW-5: overhangs under by() and on the end labels
bl Y18 stcolor `"`one', xlabel(2000 "a very long label" 5000) by(foreign) xoverhangs"'
bl Y19 stcolor `"`one', xlabel(2000 "a very long label" 5000) by(foreign)"'
bl Y20 stcolor `"`one', xlabel(2000 "a very long label" 3000 "b" 5000 "c") xoverhangs"'
bl Y20b stcolor `"`one', xlabel(2000 "a very long label" 3000 "b" 5000 "c")"'
// BY-5: a shrink word inside a sub-option's text
bl Y21 stcolor `"`one', aspectratio(1) by(foreign, note("a shrink b"))"'
file close blrec

python:
import json, os, re, sys
from sfi import Macro

REPO = Macro.getGlobal("BL_REPO")
WORK = Macro.getGlobal("BL_WORK")
sys.path.insert(0, os.path.join(REPO, "scripts"))
import svg_truth

_HEAD = re.compile(r"^\s*(name|log|log type|opened on|closed on):")


def log_of(pid):
    try:
        with open(os.path.join(WORK, pid + ".log"), encoding="utf-8",
                  errors="replace") as fh:
            lines = [l.rstrip() for l in fh]
    except OSError:
        return []
    return [l.strip() for l in lines if l.strip() and not _HEAD.match(l)
            and not set(l.strip()) <= set("-")
            and not l.lstrip().startswith(". ")
            and not l.lstrip().startswith("> ")
            and not l.strip().startswith("file ")
            and not l.strip().startswith("(file ")]


def r2(v):
    return None if v is None else round(v, 2)


probes, order = {}, []
with open(Macro.getGlobal("BL_REC"), encoding="utf-8", errors="replace") as fh:
    for line in fh:
        f = line.rstrip("\n").split("|")
        if f[0] == "R":
            pid = f[1]
            rc = int(f[3]) or int(f[4])
            lg = log_of(pid)
            probes[pid] = {"scheme": f[2], "rc": rc,
                           "command": "|".join(f[5:]), "log": lg,
                           "line": (lg[0] if (rc and lg) else "")}
            order.append(pid)

for pid in order:
    p = probes[pid]
    path = os.path.join(WORK, pid + ".svg")
    if p["rc"] or not os.path.exists(path):
        continue
    doc = svg_truth.svg_document(path)
    p["canvas"] = doc.get("canvas")
    p["rects"] = [{"x": r2(r["x"]), "y": r2(r["y"]), "w": r2(r["w"]),
                   "h": r2(r["h"]), "fill": r["fill"], "stroke": r["stroke"],
                   "sw": r2(r["stroke_width"])}
                  for r in svg_truth.svg_rects(path)
                  if (r["w"] or 0) >= 3 and (r["h"] or 0) >= 3]
    p["texts"] = [{"t": t["text"], "x": r2(t["x"]), "y": r2(t["y"]),
                   "size": r2(t["size"]), "fill": t["fill"],
                   "anchor": t["anchor"], "rot": t["rotate"]}
                  for t in doc["texts"] if t["text"]]

out = {"probes": {pid: probes[pid] for pid in order}}
out["_meta"] = {"stata_version": Macro.getGlobal("BL_SVER"),
                "born_date": Macro.getGlobal("BL_BORN"),
                "dash_commit": Macro.getGlobal("BL_COMMIT"),
                "extracted": Macro.getGlobal("BL_DATE"),
                "source": "scripts/extract_by_layout_truth.do"}
with open(Macro.getGlobal("BL_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=0, sort_keys=True)
    fh.write("\n")
print("WROTE %s probes=%d" % (Macro.getGlobal("BL_OUT"), len(order)))
end

display as text "extract_by_layout_truth.do: done"
