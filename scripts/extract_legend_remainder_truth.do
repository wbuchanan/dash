*! extract_legend_remainder_truth.do -- WP-31 section 39 (D4b): measure
*! how twoway draws the legend sub-options section 31 left named --
*! stacked, symplacement(), colgap() and the legend's own subtitle(),
*! note() and caption() -- beside the default and title(), from the SVG:
*! every text with its place and size, the key marks and the box.
*!
*! Output: test/fixtures/legend_remainder_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_legend_remainder_truth.do
*!
*! (Built on scripts/extract_legend_geometry_truth.do's probe and reader.)

clear all
set more off
set linesize 200

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_lg_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_lg_bad' {
    display as error "extract_legend_remainder_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_legend_remainder_truth.do: `_lg_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global LG_REPO "`repo'"
global LG_OUT "${LG_REPO}/test/fixtures/legend_remainder_truth.json"

if `"`c(python_exec)'"' == "" {
    display as error "extract_legend_remainder_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

local work "`c(tmpdir)'dash_legend_remainder_probe"
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

_lg_run base `"`two'"'
_lg_run stacked `"`two' legend(stacked)"'
_lg_run stacked_cols1 `"`two' legend(stacked cols(1))"'
foreach d in w e n s c nw se {
    _lg_run symp_`d' `"`two' legend(symplacement(`d'))"'
}
_lg_run symp_bogus `"`two' legend(symplacement(bogus))"'
_lg_run colgap_large `"`two' legend(colgap(large))"'
_lg_run colgap_zero `"`two' legend(colgap(0))"'
_lg_run colgap_rows `"`four' legend(cols(2) colgap(large))"'
_lg_run colgap_cols1 `"`two' legend(cols(1) colgap(large))"'
_lg_run colgap_bogus `"`two' legend(colgap(bogus))"'
_lg_run lsubtitle `"`two' legend(subtitle("Sub"))"'
_lg_run lnote `"`two' legend(note("Nt"))"'
_lg_run lcaption `"`two' legend(caption("Cap"))"'
_lg_run lall `"`two' legend(title("Ttl") subtitle("Sub") note("Nt") caption("Cap"))"'
_lg_run ltitle `"`two' legend(title("Ttl"))"'

* Each probe's log: the refusal or note lines.
capture program drop _lg_log
program define _lg_log
    args key cmd
    capture log close lgr
    quietly log using "${LG_WORK}/r_`key'.log", text replace name(lgr)
    capture noisily `cmd' name(u31k, replace)
    quietly log close lgr
end
_lg_log symp_bogus `"`two' legend(symplacement(bogus))"'
_lg_log colgap_bogus `"`two' legend(colgap(bogus))"'

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
    rec["texts"] = [{"text": t["text"], "x": t["x"], "y": t["y"],
                     "anchor": t["anchor"], "size": t.get("size")}
                    for t in doc["texts"]]
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

keys = ["base", "stacked", "stacked_cols1"] + [
    "symp_" + d for d in ("w", "e", "n", "s", "c", "nw", "se")] + [
    "symp_bogus", "colgap_large", "colgap_zero", "colgap_rows",
    "colgap_cols1", "colgap_bogus", "lsubtitle", "lnote", "lcaption",
    "lall", "ltitle"]
out = {k: record(k) for k in keys}
for k in ("symp_bogus", "colgap_bogus"):
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
                "source": "scripts/extract_legend_remainder_truth.do"}
with open(G("LG_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote", G("LG_OUT"))
end
