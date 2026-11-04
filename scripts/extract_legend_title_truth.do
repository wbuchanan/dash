*! extract_legend_title_truth.do -- WP-43 section 43-01 (LT-1, LT-15,
*! LT-13): measure how twoway draws legend(title()) and legend(subtitle())
*! -- their size and colour under five schemes beside the key texts, the
*! title's position(), justification(), box, margin() and tstyle(), the
*! subtitle's size() and color(), the block under scale(1.5) -- whether
*! each other textbox sub-option of the title changes the SVG at all, and
*! twoway's answer to the edge titles t1title() .. r2title() inside
*! legend().
*!
*! Output: test/fixtures/legend_title_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_legend_title_truth.do
*!
*! (Built on scripts/extract_legend_remainder_truth.do's probe and reader.)

clear all
set more off
set linesize 200

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_lt_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_lt_bad' {
    display as error "extract_legend_title_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _lt_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_lt_rc' | _rc {
    local _lt_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_legend_title_truth.do: `_lt_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global LT_REPO "`repo'"
global LT_OUT "${LT_REPO}/test/fixtures/legend_title_truth.json"

local work "`c(tmpdir)'dash_legend_title_probe"
capture mkdir "`work'"
global LT_WORK "`work'"

quietly shell git -C "${LT_REPO}" rev-parse HEAD > "${LT_WORK}/git_head.txt"
global LT_VERSION "`c(stata_version)'"
global LT_BORN "`c(born_date)'"
global LT_WHEN "`c(current_date)' `c(current_time)'"

sysuse auto, clear
sort weight

* _lt_run key cmd: draw under the session scheme, export the SVG and log
* the command's own lines (a refusal's first line is read from it).
capture program drop _lt_run
program define _lt_run
    args key cmd
    capture graph drop u43t
    capture log close ltr
    quietly log using "${LT_WORK}/r_`key'.log", text replace name(ltr)
    capture noisily `cmd' name(u43t, replace)
    local rc = _rc
    quietly log close ltr
    capture erase "${LT_WORK}/`key'.svg"
    if !`rc' {
        quietly graph export "${LT_WORK}/`key'.svg", as(svg) replace
    }
    global LT_R_`key' "`rc'"
end

local two "twoway (scatter mpg weight) (scatter price weight),"

set scheme s2color
foreach s in stcolor s2color s1mono economist meta {
    _lt_run style_`s' `"`two' scheme(`s') legend(title("T") subtitle("S"))"'
}
_lt_run control `"`two' legend(title("T"))"'
foreach k in 0 3 5 6 9 12 {
    _lt_run title_pos_`k' `"`two' legend(title("T", position(`k')))"'
}
_lt_run title_box `"`two' legend(title("T", box))"'
_lt_run title_box_margin `"`two' legend(title("T", box margin(large)))"'
_lt_run title_just `"`two' legend(title("T", justification(right)))"'
_lt_run title_tstyle `"`two' legend(title("T", tstyle(body)))"'
_lt_run sub_style `"`two' legend(subtitle("S", size(large) color(red)))"'
_lt_run sub_under `"`two' legend(title("T") subtitle("S"))"'
_lt_run block_box `"`two' legend(title("T", box) subtitle("S"))"'
_lt_run scale_block `"`two' legend(title("T", box) subtitle("S")) scale(1.5)"'
_lt_run title_orientation `"`two' legend(title("T", orientation(vertical)))"'
_lt_run title_width `"`two' legend(title("T", width(40)))"'
_lt_run title_height `"`two' legend(title("T", height(20)))"'
_lt_run title_angle `"`two' legend(title("T", angle(45)))"'
_lt_run title_alignment `"`two' legend(title("T", alignment(top)))"'
_lt_run title_linegap `"`two' legend(title("T", linegap(5)))"'
_lt_run title_bmargin `"`two' legend(title("T", bmargin(large)))"'
_lt_run title_bexpand `"`two' legend(title("T", bexpand))"'
_lt_run title_placement `"`two' legend(title("T", placement(east)))"'
_lt_run title_ring `"`two' legend(title("T", ring(0)))"'
_lt_run title_span `"`two' legend(title("T", span))"'
_lt_run title_lstyle `"`two' legend(title("T", lstyle(foreground)))"'
_lt_run title_blcolor `"`two' legend(title("T", blcolor(red)))"'
_lt_run title_blwidth `"`two' legend(title("T", blwidth(thick)))"'
_lt_run title_lalign `"`two' legend(title("T", lalign(outside)))"'
_lt_run title_prefix `"`two' legend(title("T", prefix))"'
_lt_run title_suffix `"`two' legend(title("T", suffix))"'
foreach e in t1 t2 b1 b2 l1 l2 r1 r2 {
    _lt_run edge_`e' `"`two' legend(`e'title("E"))"'
}

python:
import json, os, sys
from sfi import Macro

sys.path.insert(0, Macro.getGlobal("LT_REPO") + "/scripts")
import svg_truth


def G(k):
    return Macro.getGlobal(k)


work = G("LT_WORK")


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


def shape(path):
    doc = svg_truth.svg_document(path)
    texts = [{"text": t["text"], "x": t["x"], "y": t["y"],
              "anchor": t["anchor"], "size": t.get("size"),
              "fill": t.get("fill"), "rotate": t.get("rotate")}
             for t in doc["texts"]]
    rects = [{k: r.get(k) for k in ("x", "y", "w", "h", "fill", "stroke",
                                    "stroke_width", "dasharray")}
             for r in svg_truth.svg_rects(path)]
    return texts, rects


def record(key):
    rc = int(G("LT_R_" + key) or "0")
    rec = {"rc": rc}
    if rc:
        lines = log_lines(key)
        rec["first_line"] = lines[0] if lines else ""
        return rec
    path = os.path.join(work, key + ".svg")
    texts, rects = shape(path)
    rec["texts"] = texts
    rec["rects"] = rects
    rec["log"] = log_lines(key)
    keys = [t for t in texts if not t["anchor"]]
    rec["key_size"] = keys[0]["size"] if keys else None
    rec["key_fill"] = keys[0]["fill"] if keys else None
    for t in texts:
        if t["text"] in ("T", "S"):
            rec[t["text"]] = t
    return rec


keys = (["style_" + s for s in ("stcolor", "s2color", "s1mono", "economist",
                                "meta")]
        + ["control"] + ["title_pos_%s" % k for k in (0, 3, 5, 6, 9, 12)]
        + ["title_box", "title_box_margin", "title_just", "title_tstyle",
           "sub_style", "sub_under", "block_box", "scale_block"])
subs = ("orientation", "width", "height", "angle", "alignment", "linegap",
        "bmargin", "bexpand", "placement", "ring", "span", "lstyle",
        "blcolor", "blwidth", "lalign", "prefix", "suffix")
out = {k: record(k) for k in keys}
ctl = shape(os.path.join(work, "control.svg"))
for s in subs:
    k = "title_" + s
    rec = record(k)
    if rec["rc"] == 0:
        rec["same_as_control"] = shape(os.path.join(work, k + ".svg")) == ctl
        rec.pop("rects", None)
    out[k] = rec
for e in ("t1", "t2", "b1", "b2", "l1", "l2", "r1", "r2"):
    rec = record("edge_" + e)
    rec.pop("rects", None)
    rec.pop("texts", None)
    out["edge_" + e] = rec
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("LT_VERSION"), "born_date": G("LT_BORN"),
                "dash_commit": commit, "extracted": G("LT_WHEN"),
                "scheme": "s2color unless the key says otherwise",
                "units": "SVG px, 720 per inch; Stata size unit = 28.8 SVG px",
                "source": "scripts/extract_legend_title_truth.do"}
with open(G("LT_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote", G("LT_OUT"))
end
