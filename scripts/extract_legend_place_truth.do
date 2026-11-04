*! extract_legend_place_truth.do -- WP-43 section 43-02 (LT-4, LT-17,
*! LT-5): measure where twoway puts an inside legend under bplacement(),
*! which compass spellings it reads (bplacement(nor), NE, top, a clock
*! number), how much room a hole takes in a one-column, one-row and
*! two-column legend (with scale(1.5) too), and what legend(all), draw and
*! nodraw do to the keys and to whether a legend is drawn -- from twoway's
*! own class values and SVG export.  twoway only: the output is the same
*! before and after dash changes.
*!
*! Output: test/fixtures/legend_place_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_legend_place_truth.do
*!
*! (Built on scripts/extract_legend_geometry_truth.do's probe and reader.)
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_lp_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_lp_bad' {
    display as error "extract_legend_place_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _lp_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_lp_rc' | _rc {
    local _lp_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_legend_place_truth.do: `_lp_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global LP_REPO "`repo'"
global LP_OUT "${LP_REPO}/test/fixtures/legend_place_truth.json"

local work "`c(tmpdir)'dash_legend_place_probe"
capture mkdir "`work'"
global LP_WORK "`work'"

quietly shell git -C "${LP_REPO}" rev-parse HEAD > "${LP_WORK}/git_head.txt"
global LP_VERSION "`c(stata_version)'"
global LP_BORN "`c(born_date)'"
global LP_WHEN "`c(current_date)' `c(current_time)'"

set scheme s2color
sysuse auto, clear
sort weight

* _lp_run key cmd: draw, log the command's own lines (a note is read from
* them), export the SVG, and record _rc, the drawn flag, the key count and
* the legend's box alignment, cols and rows.
capture program drop _lp_run
program define _lp_run
    args key cmd
    capture graph drop u43p
    capture log close lpr
    quietly log using "${LP_WORK}/r_`key'.log", text replace name(lpr)
    capture noisily `cmd' name(u43p, replace)
    local rc = _rc
    quietly log close lpr
    local out "rc `rc'"
    capture erase "${LP_WORK}/`key'.svg"
    if !`rc' {
        quietly graph export "${LP_WORK}/`key'.svg", as(svg) replace
        local dv "`.u43p.legend.draw_view.istrue'"
        if "`dv'" == "" local dv "-"
        local nk "`.u43p.legend.keys.arrnels'"
        if "`nk'" == "" local nk 0
        local out "`out' drawn `dv' keys `nk'"
        foreach s in cols rows {
            local v "`.u43p.legend.style.`s'.val'"
            if "`v'" == "" local v "-"
            local out "`out' `s' `v'"
        }
        local v "`.u43p.legend.style.box_alignment.snm'"
        if "`v'" == "" local v "-"
        local out "`out' box_alignment `v'"
    }
    global LP_R_`key' "`out'"
end

local three "twoway (scatter mpg weight) (scatter price weight) (scatter turn weight),"
local one "twoway (scatter mpg weight),"
local two "twoway (scatter mpg weight) (scatter price weight),"
local p1 "twoway (scatter mpg weight, pstyle(p1)) (scatter price weight, pstyle(p1)),"

* LT-4: an inside legend and bplacement().
_lp_run r0_default `"`three' legend(ring(0))"'
foreach x in n ne e se s sw w nw c {
    _lp_run r0_bp_`x' `"`three' legend(ring(0) bplacement(`x'))"'
    _lp_run out_bp_`x' `"`three' legend(pos(6) bplacement(`x'))"'
}
_lp_run r0_pos1 `"`three' legend(ring(0) pos(1))"'
_lp_run r0_pos1_bp_sw `"`three' legend(ring(0) pos(1) bplacement(sw))"'
_lp_run pos0 `"`three' legend(pos(0))"'
_lp_run pos0_bp_nw `"`three' legend(pos(0) bplacement(nw))"'
* The spellings, by index (the file system folds case: N and n).
local spellings "nor nea t top N NE R 3 12 rig bot NOR 3.0 bogus"
global LP_SPELLINGS "`spellings'"
local i 0
foreach s of local spellings {
    local ++i
    _lp_run bp_out_`i' `"`three' legend(pos(6) bplacement(`s'))"'
    _lp_run bp_in_`i' `"`three' legend(ring(0) bplacement(`s'))"'
}

* LT-17: holes.
_lp_run holes_1col_0 `"`three' legend(cols(1))"'
foreach k in 1 2 4 {
    _lp_run holes_1col_`k' `"`three' legend(holes(`k') cols(1))"'
}
_lp_run holes_1col_1key_0 `"`one' legend(on cols(1))"'
_lp_run holes_1col_1key `"`one' legend(on holes(1) cols(1))"'
_lp_run holes_1col_scale_0 `"`three' legend(cols(1)) scale(1.5)"'
_lp_run holes_1col_scale `"`three' legend(holes(1) cols(1)) scale(1.5)"'
_lp_run holes_1row_0 `"`three' legend(rows(1))"'
_lp_run holes_1row `"`three' legend(holes(2) rows(1))"'
_lp_run holes_2col_0 `"`three' legend(cols(2))"'
_lp_run holes_2col `"`three' legend(holes(2) cols(2))"'

* LT-5: all, draw, nodraw.
_lp_run all_p1_0 `"`p1'"'
_lp_run all_p1 `"`p1' legend(all)"'
_lp_run draw_1 `"`one' legend(draw)"'
_lp_run nodraw_2 `"`two' legend(nodraw)"'
_lp_run on_nodraw `"`two' legend(on nodraw)"'
_lp_run nodraw_on `"`one' legend(nodraw on)"'
_lp_run off_draw `"`one' legend(off draw)"'
_lp_run draw_off `"`one' legend(draw off)"'
_lp_run all_nodraw `"`p1' legend(all nodraw)"'

python:
import json, os, sys
from sfi import Macro

sys.path.insert(0, Macro.getGlobal("LP_REPO") + "/scripts")
import svg_truth


def G(k):
    return Macro.getGlobal(k)


work = G("LP_WORK")


def log_lines(key):
    try:
        with open(os.path.join(work, "r_" + key + ".log"),
                  encoding="utf-8") as fh:
            lines = [ln.rstrip() for ln in fh]
    except OSError:
        return []
    return [ln for ln in lines if ln.strip() and not ln.startswith(".")
            and not ln.startswith(">")
            and not ln.lstrip().startswith(("name:", "log:", "log type:",
                                            "opened on:", "closed on:"))
            and not set(ln.strip()) <= set("-")]


def record(key):
    w = G("LP_R_" + key).split()
    rec = {}
    for i in range(0, len(w) - 1, 2):
        v = w[i + 1]
        try:
            v = float(v)
            v = int(v) if v == int(v) else v
        except ValueError:
            pass
        rec[w[i]] = v
    rec["log"] = log_lines(key)
    path = os.path.join(work, key + ".svg")
    if rec.get("rc") != 0 or not os.path.exists(path):
        return rec
    doc = svg_truth.svg_document(path)
    rects = svg_truth.svg_rects(path)
    pr = doc["plotregion"] or {}
    rec["plot"] = {k: pr.get(k) for k in ("left", "top", "right", "bottom")}
    # Legend keys are the <text> elements with no text-anchor.
    keys = [{"text": t["text"], "x": t["x"], "y": t["y"]}
            for t in doc["texts"] if not t["anchor"]]
    rec["key_texts"] = keys
    # The legend box: the smallest filled rect, other than the canvas and
    # the plot region, holding every key text's anchor point.
    box = None
    if keys:
        for r in rects:
            if r.get("fill") in (None, "none") or r["w"] is None:
                continue
            x0, y0, x1, y1 = r["x"], r["y"], r["x"] + r["w"], r["y"] + r["h"]
            if pr and abs(x0 - pr["left"]) < 1 and abs(y0 - pr["top"]) < 1:
                continue
            if r["w"] > 3900:
                continue
            if all(x0 <= k["x"] <= x1 and y0 <= k["y"] <= y1 for k in keys):
                if box is None or r["w"] * r["h"] < box["w"] * box["h"]:
                    box = r
    if box is not None:
        x0, y0 = box["x"], box["y"]
        x1, y1 = x0 + box["w"], y0 + box["h"]
        rec["box"] = {"left": x0, "top": y0, "right": x1, "bottom": y1}
        rec["key_marks"] = [
            {"cx": c.get("cx"), "cy": c.get("cy")}
            for c in doc["circles"]
            if c.get("cx") is not None and x0 <= c["cx"] <= x1
            and y0 <= c["cy"] <= y1]
        if pr:
            pw = pr["right"] - pr["left"]
            ph = pr["bottom"] - pr["top"]
            rec["box_rel"] = {
                "left": round((x0 - pr["left"]) / pw, 4),
                "right": round((x1 - pr["left"]) / pw, 4),
                "top": round((y0 - pr["top"]) / ph, 4),
                "bottom": round((y1 - pr["top"]) / ph, 4)}
    return rec


compass = ("n", "ne", "e", "se", "s", "sw", "w", "nw", "c")
keys = (["r0_default", "r0_pos1", "r0_pos1_bp_sw", "pos0", "pos0_bp_nw"]
        + ["r0_bp_" + x for x in compass] + ["out_bp_" + x for x in compass]
        + ["holes_1col_0", "holes_1col_1", "holes_1col_2", "holes_1col_4",
           "holes_1col_1key_0", "holes_1col_1key", "holes_1col_scale_0",
           "holes_1col_scale", "holes_1row_0", "holes_1row", "holes_2col_0",
           "holes_2col"]
        + ["all_p1_0", "all_p1", "draw_1", "nodraw_2", "on_nodraw",
           "nodraw_on", "off_draw", "draw_off", "all_nodraw"])
out = {k: record(k) for k in keys}


def where(rec):
    b = rec.get("box")
    return None if b is None else [round(b[k], 1) for k in
                                   ("left", "top", "right", "bottom")]


spellings = G("LP_SPELLINGS").split()
for i, s in enumerate(spellings, 1):
    for side, canon in (("out", "out_bp_"), ("in", "r0_bp_")):
        rec = record("bp_%s_%d" % (side, i))
        rec["spelling"] = s
        rec["same_as"] = [x for x in compass
                          if where(rec) is not None
                          and where(rec) == where(out[canon + x])]
        out["bp_%s_%d" % (side, i)] = rec
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("LP_VERSION"), "born_date": G("LP_BORN"),
                "dash_commit": commit, "extracted": G("LP_WHEN"),
                "scheme": "s2color",
                "spellings": spellings,
                "base": "twoway (scatter mpg weight) (scatter price weight)"
                        " (scatter turn weight)",
                "units": "SVG px, 720 per inch; Stata size unit = 28.8 SVG px",
                "source": "scripts/extract_legend_place_truth.do"}
with open(G("LP_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote", G("LP_OUT"))
end
