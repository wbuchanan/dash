*! extract_mlabel_clip_truth.do
*! WP-47 MS-15: ground truth for where twoway draws a marker label that
*! runs past the plot region, for test/fixtures/mlabel_clip_truth.json.
*!
*! WHY THIS EXISTS
*!
*! dash clipped every marker label at the plot region's edge; twoway lets
*! it run on over the axis area (WP-33 33-05's calibration example,
*! help-marker_label_options-9b377083: Honduras at 9 o'clock runs left
*! over the y-axis labels).  This script draws that example, one long
*! label at each edge (9 at the left, 3 at the right, 12 at the top, 6 at
*! the bottom) and the same under by(), exports each to SVG and records
*! the plot regions, the canvas, every label's anchor and its extent (the
*! text's Helvetica advance widths at its font size), and whether the SVG
*! clips anything (clipPath or clip-path).
*!
*! Output: test/fixtures/mlabel_clip_truth.json
*!
*! Run with:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_mlabel_clip_truth.do
*!
*! Never calls back into Stata from the trailing python: block; a backtick
*! inside it is spelled \x60.
*! ---------------------------------------------------------------------------

clear all
set graphics off
set more off
set linesize 255

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_mlabel_clip_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_mlabel_clip_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1
global ZK_REPO "`repo'"
global ZK_OUT  "`repo'/test/fixtures/mlabel_clip_truth.json"

local work "`c(tmpdir)'dash_mlabel_clip_probe"
capture mkdir "`work'"
global ZK_WORK "`work'"
display as text "probe work dir: ${ZK_WORK}"


global ZK_SVER = c(stata_version)
global ZK_BORN = c(born_date)
global ZK_DATE = "`c(current_date)' `c(current_time)'"

// Provenance stamp (D12): shell writes the commit into a file, read back.
tempfile zkgitrev
quietly shell git -C "${ZK_REPO}" rev-parse HEAD > "`zkgitrev'"
tempname zkgfh
file open `zkgfh' using "`zkgitrev'", read text
file read `zkgfh' zkgitline
file close `zkgfh'
global ZK_COMMIT = trim(`"`zkgitline'"')
capture assert ustrregexm(`"${ZK_COMMIT}"', "^[0-9a-f]{40}$")
if _rc {
    display as error "extract_mlabel_clip_truth.do: git rev-parse HEAD did not print a 40-character commit"
    exit 498
}

set scheme stcolor

capture mata: mata drop _zk_put()
mata:
void _zk_put(string scalar file, string scalar text)
{
    real scalar fh
    if (fileexists(file)) unlink(file)
    fh = fopen(file, "w")
    fput(fh, text)
    fclose(fh)
}
end

// The calibration example (marker_label_options.sthlp, markerlabel1).
sysuse lifeexp, clear
generate pos = 3
replace pos = 9 if country == "Honduras"
capture graph drop Graph
capture noisily scatter lexp gnppc if region==2, mlabel(country) mlabv(pos) xsca(range(35000)) name(Graph, replace)
local rc = _rc
mata: _zk_put(st_global("ZK_WORK") + "/CAL_rc.txt", st_local("rc"))
capture graph export "${ZK_WORK}/CAL.svg", name(Graph) replace
capture graph drop Graph

// One long label at each edge, then the same under by().
clear
set obs 4
gen double x = cond(_n == 1, 0, cond(_n == 2, 10, 5))
gen double y = cond(_n == 3, 10, cond(_n == 4, 0, 5))
gen str40 lab = "Label" + string(_n) + "_runs_well_past_the_region"
gen double p = cond(_n == 1, 9, cond(_n == 2, 3, cond(_n == 3, 12, 6)))
gen byte g = mod(_n, 2)
capture noisily scatter y x, mlabel(lab) mlabvposition(p) name(Graph, replace)
local rc = _rc
mata: _zk_put(st_global("ZK_WORK") + "/EDGE_rc.txt", st_local("rc"))
capture graph export "${ZK_WORK}/EDGE.svg", name(Graph) replace
capture graph drop Graph
capture noisily scatter y x, mlabel(lab) mlabvposition(p) by(g) name(Graph, replace)
local rc = _rc
mata: _zk_put(st_global("ZK_WORK") + "/BY_rc.txt", st_local("rc"))
capture graph export "${ZK_WORK}/BY.svg", name(Graph) replace
capture graph drop Graph

// ===========================================================================
// Analysis + JSON emission.  No callbacks into Stata from here on.
// REMINDER: no backtick may appear literally in this block.
// ===========================================================================
python:
import json
import os
import re
import sys
from sfi import Macro

ZK_REPO = Macro.getGlobal("ZK_REPO")
sys.path.insert(0, os.path.join(ZK_REPO, "scripts"))
import svg_truth

W = Macro.getGlobal("ZK_WORK")
OUT = Macro.getGlobal("ZK_OUT")

# Helvetica's advance widths (Adobe AFM, per 1000 em), for the characters
# the probes' labels use; the SVG names Helvetica.
_AFM = dict(zip("abcdefghijklmnopqrstuvwxyz",
                (556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222,
                 833, 556, 556, 556, 556, 333, 500, 278, 556, 500, 722, 500,
                 500, 500)))
_AFM.update(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                (667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556,
                 833, 722, 778, 667, 778, 722, 667, 611, 722, 667, 944, 667,
                 667, 611)))
_AFM.update({c: 556 for c in "0123456789"})
_AFM.update({"_": 556, " ": 278, ".": 278, ",": 278, "-": 333,
             "(": 333, ")": 333, "&": 667, "'": 222})


def _width(text, size):
    return round(sum(_AFM.get(c, 556) for c in text) * size / 1000.0, 2)


def _read(name):
    p = os.path.join(W, name)
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8") as fh:
        return fh.read().strip()


def _probe(pid, cmd, wanted):
    p = os.path.join(W, pid + ".svg")
    rec = {"cmd": cmd, "rc": int(_read(pid + "_rc.txt") or -1)}
    if not os.path.exists(p):
        return rec
    with open(p, encoding="utf-8", errors="replace") as fh:
        txt = fh.read()
    doc = svg_truth.svg_document(p)
    rec["clips"] = len(re.findall(r"clip", txt, flags=re.I))
    cw, ch = doc["canvas"]["w"], doc["canvas"]["h"]
    rec["canvas"] = {"w": cw, "h": ch}
    regions = []
    for r in svg_truth.svg_rects(p):
        if r["fill"] in (None, "none") or r["w"] is None:
            continue
        if r["w"] >= 0.95 * cw and r["h"] >= 0.95 * ch:
            continue
        if r["h"] < 0.3 * ch:
            continue
        regions.append({"left": r["x"], "top": r["y"],
                        "right": round(r["x"] + r["w"], 2),
                        "bottom": round(r["y"] + r["h"], 2)})
    rec["regions"] = regions
    labels = []
    for t in doc["texts"]:
        if not wanted(t["text"]):
            continue
        a = t["anchor"] or "start"
        w = _width(t["text"], t["size"])
        left = t["x"] - (w if a == "end" else w / 2.0 if a == "middle" else 0)
        labels.append({"text": t["text"], "x": t["x"], "y": t["y"],
                       "anchor": a, "size": t["size"], "width": w,
                       "left": round(left, 2), "right": round(left + w, 2)})
    rec["labels"] = labels
    return rec


rec = {}
rec["CAL"] = _probe("CAL", "scatter lexp gnppc if region==2, mlabel(country) "
                    "mlabv(pos) xsca(range(35000))",
                    lambda s: s == "Honduras")
_long = re.compile(r"^Label[0-9]_runs_well_past_the_region$")
rec["EDGE"] = _probe("EDGE", "scatter y x, mlabel(lab) mlabvposition(p)",
                     lambda s: bool(_long.match(s)))
rec["BY"] = _probe("BY", "scatter y x, mlabel(lab) mlabvposition(p) by(g)",
                   lambda s: bool(_long.match(s)))

meta = {
    "stata_version": Macro.getGlobal("ZK_SVER"),
    "born_date": Macro.getGlobal("ZK_BORN"),
    "source": "scripts/extract_mlabel_clip_truth.do",
    "dash_commit": Macro.getGlobal("ZK_COMMIT"),
    "extracted": Macro.getGlobal("ZK_DATE"),
    "scheme": "stcolor",
    "probes": len(rec),
    "data": "sysuse lifeexp (CAL: pos = 3, 9 for Honduras); EDGE and BY: "
            "four rows, x = 0 10 5 5, y = 5 5 10 0, p = 9 3 12 6, "
            "g = mod(_n, 2), lab = Label<n>_runs_well_past_the_region",
    "widths": "Helvetica AFM advance widths at the text's font size",
    "generator": "scripts/extract_mlabel_clip_truth.do",
}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump({"_meta": meta, "probes": rec}, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote", OUT, len(rec), "probes")
end
