*! extract_legend_geometry_truth.do -- WP-31 section 31 (D4, C13): measure
*! how twoway lays out its legend -- the scheme's key geometry, where each
*! clock position and ring(0) put the box, the columns kept with position(),
*! holes(), colfirst, rows()/cols(), label(#) with no text, two keys with
*! the same text, region(), the key sizes, bplacement(), title(), and
*! whether a histogram-only graph draws a legend, and which keys twoway
*! merges into one (same plot type and look, no style option given; the
*! texts joined by "/") -- from twoway's own class
*! values and SVG export.  twoway only: the output is the same before and
*! after dash changes.
*!
*! Output: test/fixtures/legend_geometry_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_legend_geometry_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_lg_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_lg_bad' {
    display as error "extract_legend_geometry_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _lg_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_lg_rc' | _rc {
    local _lg_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_legend_geometry_truth.do: `_lg_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global LG_REPO "`repo'"
global LG_OUT "${LG_REPO}/test/fixtures/legend_geometry_truth.json"


local work "`c(tmpdir)'dash_legend_geometry_probe"
capture mkdir "`work'"
global LG_WORK "`work'"

quietly shell git -C "${LG_REPO}" rev-parse HEAD > "${LG_WORK}/git_head.txt"
global LG_VERSION "`c(stata_version)'"
global LG_BORN "`c(born_date)'"
global LG_WHEN "`c(current_date)' `c(current_time)'"

set scheme s2color
sysuse auto, clear
sort weight
generate double trunk100 = trunk * 100
generate double turn100 = turn * 100

* The members of the legend and its style, for the record.
quietly twoway scatter mpg weight || scatter price weight, name(u31k, replace)
log using "${LG_WORK}/members.log", text replace name(lgm)
classutil describe .u31k.legend
classutil describe .u31k.legend.style
log close lgm

* _lg_run key cmd: draw, export the SVG, record _rc, the drawn flag, the
* key count and the class values the rows read.
capture program drop _lg_run
program define _lg_run
    args key cmd
    capture graph drop u31k
    capture noisily `cmd' name(u31k, replace)
    local rc = _rc
    local out "rc `rc'"
    if !`rc' {
        quietly graph export "${LG_WORK}/`key'.svg", replace
        local dv "`.u31k.legend.draw_view.istrue'"
        if "`dv'" == "" local dv "-"
        local nk "`.u31k.legend.keys.arrnels'"
        if "`nk'" == "" local nk 0
        local out "`out' drawn `dv' keys `nk'"
        foreach s in key_xsize key_ysize key_gap row_gap col_gap {
            local v "`.u31k.legend.style.`s'.val'"
            if "`v'" == "" local v "-"
            local out "`out' `s' `v'"
        }
        foreach s in cols rows {
            local v "`.u31k.legend.style.`s'.val'"
            if "`v'" == "" local v "-"
            local out "`out' `s' `v'"
        }
        local v "`.u31k.legend.holes'"
        if "`v'" == "" local v "-"
        local out "`out' holes `v'"
        local v "`.u31k.legend.style.box_alignment.snm'"
        if "`v'" == "" local v "-"
        local out "`out' box_alignment `v'"
    }
    global LG_R_`key' "`out'"
end

local two "twoway scatter mpg weight || scatter price weight,"
local three "twoway scatter mpg weight || scatter price weight || scatter trunk100 weight,"
local four "twoway scatter mpg weight || scatter price weight || scatter trunk100 weight || scatter turn100 weight,"
local lines "twoway line mpg weight || line price weight,"

_lg_run default_geometry `"`two'"'
_lg_run default_lines `"`lines'"'
global LG_KEYS ""
foreach k of numlist 0/12 {
    _lg_run clock_`k' `"`two' legend(pos(`k'))"'
}
_lg_run ring0_default `"`two' legend(ring(0))"'
_lg_run cols_with_pos `"`two' legend(pos(3))"'
_lg_run holes `"`three' legend(holes(2) cols(2))"'
_lg_run colfirst `"`four' legend(colfirst cols(2))"'
_lg_run rows3 `"`four' legend(rows(3))"'
_lg_run cols3 `"`four' legend(cols(3))"'
_lg_run label_blank `"`two' legend(label(1))"'
_lg_run merge `"twoway scatter mpg weight || scatter mpg weight,"'
_lg_run merge_pstyle `"twoway scatter mpg weight, pstyle(p1) || scatter mpg weight, pstyle(p1)"'
_lg_run merge_style `"twoway scatter mpg weight, pstyle(p1) || scatter mpg weight, pstyle(p1) mcolor(red)"'
_lg_run hist_only `"twoway histogram mpg || histogram price,"'
_lg_run hist_on `"twoway histogram mpg || histogram price, legend(on)"'
_lg_run hist_mixed `"twoway histogram mpg || scatter mpg mpg,"'
_lg_run hist_color `"twoway histogram mpg || histogram price, color(red)"'
_lg_run merge_on `"twoway scatter mpg weight, pstyle(p1) || scatter mpg weight, pstyle(p1) legend(on)"'
_lg_run merge_lab2 `"twoway scatter mpg weight, pstyle(p1) || scatter mpg weight, pstyle(p1) legend(label(2 "B"))"'
_lg_run merge_order `"twoway scatter mpg weight, pstyle(p1) || scatter mpg weight, pstyle(p1) legend(on order(2 1))"'
_lg_run merge_lab2_on `"twoway scatter mpg weight, pstyle(p1) || scatter mpg weight, pstyle(p1) legend(on label(2 "B"))"'
_lg_run merge_lab1_on `"twoway scatter mpg weight, pstyle(p1) || scatter mpg weight, pstyle(p1) legend(on label(1 "A"))"'
_lg_run merge_order2 `"twoway scatter mpg weight, pstyle(p1) || scatter mpg weight, pstyle(p1) legend(on order(2))"'
_lg_run merge_text `"twoway scatter mpg weight, pstyle(p1) || scatter price weight, pstyle(p1) legend(on)"'
global LG_MERGE_TEXT "`.u31k.legend.labels[1]'"
_lg_run merge_override `"twoway scatter mpg weight, pstyle(p1) mcolor(red) || scatter mpg weight, pstyle(p1) mcolor(red)"'
_lg_run merge_default_value `"twoway scatter mpg weight, pstyle(p1) msize(medium) || scatter mpg weight, pstyle(p1)"'
_lg_run merge_mlabel `"twoway scatter mpg weight, pstyle(p1) mlabel(make) || scatter mpg weight, pstyle(p1) mlabel(make)"'
_lg_run hist_scales `"twoway histogram mpg, freq || histogram mpg, percent"'
_lg_run merge_glyph `"twoway scatter mpg weight, pstyle(p1) || line mpg weight, pstyle(p1)"'
_lg_run merge_three `"twoway scatter mpg weight, pstyle(p1) || scatter price weight || scatter mpg weight, pstyle(p1)"'
_lg_run region `"`two' legend(region(lcolor(red) fcolor(gs14) lwidth(thick)))"'
_lg_run nobox `"`two' legend(nobox)"'
_lg_run sizes `"`lines' legend(symxsize(5) symysize(2) keygap(1) rowgap(3))"'
_lg_run sizes_rows `"`lines' legend(cols(1) rowgap(3))"'
_lg_run bplacement `"`two' legend(pos(6) bplacement(w))"'
_lg_run title `"`two' legend(title("Keys"))"'
global LG_TITLE "`.u31k.legend.title.text[1]'"
_lg_run silent `"`two' legend(span forcesize bexpand nospan)"'
_lg_run holes_zero `"`three' legend(holes(0))"'
_lg_run holes_frac `"`three' legend(holes(2.5))"'
_lg_run holes_big `"`three' legend(holes(9))"'
_lg_run symx_bogus `"`two' legend(symxsize(bogus))"'
set scheme stcolor
_lg_run st_default `"`two'"'
_lg_run st_ring0 `"`two' legend(ring(0))"'
set scheme s2color

* Each probe's log: the refusal or note lines.
capture program drop _lg_log
program define _lg_log
    args key cmd
    capture log close lgr
    quietly log using "${LG_WORK}/r_`key'.log", text replace name(lgr)
    capture noisily `cmd' name(u31k, replace)
    quietly log close lgr
end
_lg_log holes_zero `"`three' legend(holes(0))"'
_lg_log holes_frac `"`three' legend(holes(2.5))"'
_lg_log symx_bogus `"`two' legend(symxsize(bogus))"'

python:
import json, os, re, sys
from sfi import Macro

sys.path.insert(0, Macro.getGlobal("LG_REPO") + "/scripts")
import svg_truth


def G(k):
    return Macro.getGlobal(k)


work = G("LG_WORK")


def record(key):
    w = G("LG_R_" + key).split()
    rec = {}
    for i in range(0, len(w) - 1, 2):
        v = w[i + 1]
        try:
            v = float(v)
            v = int(v) if v == int(v) else v
        except ValueError:
            pass
        rec[w[i]] = v
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
        rec["box"] = {"left": box["x"], "top": box["y"],
                      "right": box["x"] + box["w"],
                      "bottom": box["y"] + box["h"], "fill": box["fill"]}
        x0, y0 = box["x"], box["y"]
        x1, y1 = x0 + box["w"], y0 + box["h"]
        # The box's outline: the unfilled rect just inside it.
        for r in rects:
            if (r.get("fill") == "none" and r["x"] is not None
                    and x0 <= r["x"] <= x0 + 40 and y0 <= r["y"] <= y0 + 40
                    and r["x"] + r["w"] <= x1 + 1):
                rec["outline"] = {"stroke": r["stroke"],
                                  "width": r["stroke_width"]}
                break
        rec["key_marks"] = [
            {"cx": c.get("cx"), "cy": c.get("cy"), "r": c.get("r"),
             "fill": c.get("fill"), "stroke": c.get("stroke")}
            for c in doc["circles"]
            if c.get("cx") is not None and x0 <= c["cx"] <= x1
            and y0 <= c["cy"] <= y1]
        rec["key_lines"] = [
            {"x1": d["x1"], "x2": d["x2"], "y1": d["y1"], "stroke": d["stroke"]}
            for d in doc["hlines"]
            if x0 <= d["x1"] <= x1 and y0 <= d["y1"] <= y1]
        if pr:
            rec["box_centre_rel"] = [
                round(((x0 + x1) / 2 - pr["left"])
                      / (pr["right"] - pr["left"]), 4),
                round(((y0 + y1) / 2 - pr["top"])
                      / (pr["bottom"] - pr["top"]), 4)]
    return rec


def log_lines(key):
    with open(os.path.join(work, "r_" + key + ".log"), encoding="utf-8") as fh:
        lines = [ln.rstrip() for ln in fh]
    return [ln for ln in lines if ln.strip() and not ln.startswith(".")
            and not ln.startswith(">")
            and not ln.lstrip().startswith(("name:", "log:", "log type:",
                                            "opened on:", "closed on:"))
            and not set(ln.strip()) <= set("-")]


with open(os.path.join(work, "members.log"), encoding="utf-8") as fh:
    members = [ln.rstrip() for ln in fh
               if re.match(r"^\s+\S+\s+\.\S+", ln)]

keys = ["default_geometry", "default_lines"] + [
    "clock_%d" % k for k in range(13)] + [
    "ring0_default", "cols_with_pos", "holes", "colfirst", "rows3", "cols3",
    "label_blank", "merge", "merge_pstyle", "merge_style", "hist_only",
    "hist_on", "hist_mixed", "hist_color", "merge_on", "merge_lab2",
    "merge_order", "merge_lab2_on", "merge_lab1_on", "merge_order2",
    "merge_text", "merge_override", "merge_default_value", "merge_mlabel",
    "hist_scales", "merge_glyph", "merge_three", "region", "nobox", "sizes", "sizes_rows",
    "bplacement", "title", "silent", "holes_zero", "holes_frac", "holes_big",
    "symx_bogus", "st_default", "st_ring0"]
out = {k: record(k) for k in keys}
out["title"]["title_text"] = G("LG_TITLE")
out["merge_text"]["label_1"] = G("LG_MERGE_TEXT")
for k in ("holes_zero", "holes_frac", "symx_bogus"):
    out[k]["log"] = log_lines(k)
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("LG_VERSION"), "born_date": G("LG_BORN"),
                "dash_commit": commit, "extracted": G("LG_WHEN"),
                "members": members, "scheme": "s2color",
                "units": "SVG px, 720 per inch; Stata size unit = 28.8 SVG px",
                "source": "scripts/extract_legend_geometry_truth.do"}
with open(G("LG_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote", G("LG_OUT"))
end
