*! extract_by_label_truth.do
*! WP-41 section 41-06 (BY-10, BY-16): ground truth for a by() graph's
*! panel label row -- the label box and text under each subtitle()
*! sub-option twoway draws on it (justification(), nobexpand, lwidth(),
*! lpattern(), span, alignment() with height(), linegap(), bmargin(),
*! placement(), orientation(), width(), height()) and the label text of a
*! date by() variable and of a value label holding quoted parts, for
*! test/fixtures/by_label_truth.json.
*!
*! WHY THIS EXISTS
*!
*! dash named every one of those sub-options as ignored and drew the label
*! centred in a full-width box; it titled a date by() variable's panels
*! with formatted dates, where twoway writes the number (14610), and drew
*! a value label of quoted parts on one line.
*!
*! Output: test/fixtures/by_label_truth.json
*!
*! Run with:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_by_label_truth.do
*!
*! METHOD
*!
*! Every probe is `bl id "options"': the probe's data are reloaded, the
*! command `twoway scatter mpg weight, <options> name(Graph, replace)' is
*! run, each panel's subtitle lines are written to a record file from the
*! `.Graph' members and the graph is exported to SVG.  The trailing
*! python: block reads files only (never calls Stata; a backtick is
*! spelled \x60) and writes, per probe, every rect and non-numeric text of
*! the SVG in document order (scripts/svg_truth.py), each label's box (the
*! filled rect written before the label's first line) and the canvas.
*! ---------------------------------------------------------------------------

clear all
set graphics off
set more off
set linesize 255
version 19

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_by_label_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_by_label_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1
global BL_REPO "`repo'"
global BL_OUT  "`repo'/test/fixtures/by_label_truth.json"
local scratch "`c(tmpdir)'dash_by_label_probe"
capture mkdir "`scratch'"
global BL_WORK "`scratch'"
global BL_REC  "`scratch'/by_label_records.txt"

set scheme stcolor

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
    display as error "extract_by_label_truth.do: git rev-parse HEAD did not print a 40-character commit: ${BL_COMMIT}"
    exit 498
}

// The data: auto; d = 1jan2000 + foreign, shown %td; bl_q.dta gives
// foreign the value label ql, whose 0 holds two quoted parts.
sysuse auto, clear
keep mpg weight foreign
generate d = mdy(1, 1, 2000) + foreign
format d %td
quietly save "${BL_WORK}/bl.dta", replace
label define ql 0 `""Dom" "estic""' 1 "Foreign"
label values foreign ql
quietly save "${BL_WORK}/bl_q.dta", replace

capture program drop bl
program define bl
    version 19
    args id data opts
    use "${BL_WORK}/`data'.dta", clear
    capture noisily twoway scatter mpg weight, `opts' name(Graph, replace)
    local rc = _rc
    file write blrec "R|`id'|`rc'|`data'|" `"`opts'"' _n
    if `rc' exit
    local np = `.Graph.graphs.arrnels'
    forvalues k = 1/`np' {
        file write blrec "P|`id'|`k'|" `"`.Graph.graphs[`k'].subtitle.text[1]'"' "|" ///
            `"`.Graph.graphs[`k'].subtitle.text[2]'"' "|" ///
            `"`.Graph.graphs[`k'].subtitle.text[3]'"' _n
    }
    quietly graph export "${BL_WORK}/`id'.svg", name(Graph) replace
end

file open blrec using "${BL_REC}", write text replace
bl L00 bl "by(foreign)"
bl L01 bl "subtitle(, justification(left)) by(foreign)"
bl L02 bl "subtitle(, justification(right)) by(foreign)"
bl L03 bl "subtitle(, nobexpand) by(foreign)"
bl L04 bl "subtitle(, lwidth(vthick) lcolor(black)) by(foreign)"
bl L05 bl "subtitle(, lpattern(dash) lcolor(black)) by(foreign)"
bl L06 bl "subtitle(, span) by(foreign)"
bl L07 bl "subtitle(, alignment(top) height(15)) by(foreign)"
bl L08 bl "subtitle(, alignment(bottom) height(15)) by(foreign)"
bl L09 bl "subtitle(, height(15)) by(foreign)"
bl L10 bl_q "subtitle(, linegap(3)) by(foreign)"
bl L11 bl "subtitle(, bmargin(medium)) by(foreign)"
bl L12 bl "subtitle(, nobexpand placement(e)) by(foreign)"
bl L13 bl "subtitle(, placement(e)) by(foreign)"
bl L14 bl "subtitle(, orientation(vertical)) by(foreign)"
bl L15 bl "subtitle(, width(30)) by(foreign)"
* Beyond the section's list: alignment() without height(), baseline, and
* a turned label of another length (the box height's rule).
bl L16 bl "subtitle(, alignment(top)) by(foreign)"
bl L17 bl "subtitle(, alignment(baseline) height(15)) by(foreign)"
bl L18 bl "subtitle(, orientation(vertical)) by(d)"
bl L19 bl "subtitle(, alignment(top) height(4)) by(foreign)"
bl L20 bl "subtitle(, justification(left) nobexpand) by(foreign)"
bl L21 bl "subtitle(, bmargin(medium) span) by(foreign)"
bl D01 bl "by(d)"
bl D02 bl "by(d, subtitleformat(var))"
bl Q01 bl_q "by(foreign)"
file close blrec

python:
import json, os, re, sys
from sfi import Macro

REPO = Macro.getGlobal("BL_REPO")
WORK = Macro.getGlobal("BL_WORK")
sys.path.insert(0, os.path.join(REPO, "scripts"))
import svg_truth

_NUM = re.compile(r"^[-+]?[0-9.,]+$")
_TAG = re.compile(r"<(rect|text)\b([^>]*?)/?>(?:([^<]*)</text>)?", re.S)

probes, order = {}, []
with open(Macro.getGlobal("BL_REC"), encoding="utf-8", errors="replace") as fh:
    for line in fh:
        f = line.rstrip("\n").split("|")
        if f[0] == "R":
            probes[f[1]] = {"rc": int(f[2]), "data": f[3],
                            "options": "|".join(f[4:]), "labels": []}
            order.append(f[1])
        elif f[0] == "P":
            probes[f[1]]["labels"].append([t for t in f[3:6] if t])


def elements(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        txt = fh.read()
    out = []
    for m in _TAG.finditer(txt):
        a = svg_truth._attrs(m.group(2))
        st = svg_truth._style_of(a)
        e = {"tag": m.group(1)}
        for key in ("x", "y", "width", "height"):
            e[key] = svg_truth._fnum(a.get(key))
        e["fill"] = (st.get("fill") or a.get("fill") or "").lower() or None
        e["stroke"] = ((st.get("stroke") or a.get("stroke") or "").lower()
                       or None)
        e["stroke_width"] = svg_truth._fnum(st.get("stroke-width",
                                                   a.get("stroke-width")))
        e["dasharray"] = st.get("stroke-dasharray",
                                a.get("stroke-dasharray"))
        if m.group(1) == "text":
            e["text"] = svg_truth.normalise_text(m.group(3) or "")
            e["size"] = svg_truth._fnum(
                (st.get("font-size") or "").replace("px", ""))
            e["anchor"] = a.get("text-anchor")
            mr = re.search(r"rotate\((-?[\d.]+)", a.get("transform", ""))
            e["angle"] = float(mr.group(1)) if mr else 0.0
        out.append(e)
    return out


for pid in order:
    p = probes[pid]
    if p["rc"]:
        continue
    path = os.path.join(WORK, pid + ".svg")
    els = elements(path)
    canvas = svg_truth.svg_document(path).get("canvas") or {}
    p["canvas"] = {"w": canvas.get("w"), "h": canvas.get("h")}
    p["texts"] = [t for lab in p["labels"] for t in lab]
    p["svg_texts"] = [{k: e[k] for k in ("text", "x", "y", "anchor",
                                          "angle", "size")}
                      for e in els if e["tag"] == "text" and e["text"]
                      and not _NUM.match(e["text"])]
    p["rects"] = [{k: e[k] for k in ("x", "y", "width", "height", "fill",
                                      "stroke", "stroke_width", "dasharray")}
                  for e in els if e["tag"] == "rect"]
    boxes = []
    for lab in p["labels"]:
        if not lab:
            continue
        idx = [i for i, e in enumerate(els)
               if e["tag"] == "text" and e["text"] == lab[0]]
        if not idx:
            boxes.append(None)
            continue
        i = idx[0]
        j = i - 1
        while j >= 0 and els[j]["tag"] != "rect":
            j -= 1
        before = []
        while j >= 0 and els[j]["tag"] == "rect" and len(before) < 2:
            before.insert(0, els[j])
            j -= 1
        fills = [r for r in before if r["fill"] not in (None, "none")]
        strokes = [r for r in before if r["stroke"] not in (None, "none")]
        b = fills[0] if fills else (before[0] if before else None)
        rec = {"label": lab, "text_x": els[i]["x"], "text_y": els[i]["y"],
               "anchor": els[i]["anchor"], "angle": els[i]["angle"],
               "size": els[i]["size"]}
        if b is not None:
            rec.update({"x": b["x"], "y": b["y"], "w": b["width"],
                        "h": b["height"], "fill": b["fill"],
                        "stroke": strokes[0]["stroke"] if strokes else None,
                        "stroke_width": (strokes[0]["stroke_width"]
                                         if strokes else None),
                        "dasharray": (strokes[0]["dasharray"]
                                      if strokes else None)})
            under = [r for r in els if r["tag"] == "rect" and r["width"]
                     and r["y"] is not None
                     and r["y"] > b["y"] + b["height"] - 1.0
                     and r["fill"] not in (None, "none")
                     and r["width"] < (canvas.get("w") or 1e9) * 0.9]
            rec["plotregion"] = ({k: under[0][k] for k in
                                  ("x", "y", "width", "height")}
                                 if under else None)
        boxes.append(rec)
    p["boxes"] = boxes

out = {
    "_meta": {"stata_version": Macro.getGlobal("BL_SVER"),
              "born_date": Macro.getGlobal("BL_BORN"),
              "source": "scripts/extract_by_label_truth.do",
              "dash_commit": Macro.getGlobal("BL_COMMIT"),
              "extracted": Macro.getGlobal("BL_DATE"),
              "scheme": "stcolor", "probes": len(order),
              "script": "scripts/extract_by_label_truth.do",
              "method": "each panel's subtitle lines from the .Graph "
                        "members; rects and texts from the SVG in document "
                        "order; a label's box is the filled rect written "
                        "before its first line"},
    "probes": probes,
}
with open(Macro.getGlobal("BL_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1, sort_keys=True)
    fh.write("\n")
print("WROTE %s probes=%d" % (Macro.getGlobal("BL_OUT"), len(order)))
end

display as text "extract_by_label_truth.do: done"
