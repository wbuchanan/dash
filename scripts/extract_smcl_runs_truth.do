*! extract_smcl_runs_truth.do
*! WP-43 section 43-07 (ST-14): twoway's drawing of markup on part of a
*! text -- each run's text, weight, slant, font, size and baseline shift --
*! in titles, axis titles, tick labels, legend keys and titles, added text,
*! by() titles and marker labels, for test/fixtures/smcl_runs_truth.json.
*!
*! Each probe draws one twoway graph and records every text of its SVG
*! drawn in more than one run (scripts/svg_text_runs.py).  twoway's SVG
*! writes one <tspan> per run with no x of its own: a run is placed at the
*! advance of the runs before it in the font's own metrics.  A raised or
*! lowered run carries dy; size and shift are recorded as ratios to the
*! text's own size (the first run's size at no shift).  Nothing here
*! changes a graph set or any other persistent setting.
*!
*! Run with:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_smcl_runs_truth.do
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
    display as error "extract_smcl_runs_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_smcl_runs_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZR_REPO "`repo'"
global ZR_OUT  "${ZR_REPO}/test/fixtures/smcl_runs_truth.json"

local scratch "`c(tmpdir)'dash_smcl_runs_probe"
capture mkdir "`scratch'"
global ZR_WORK "`scratch'"
global ZR_REC  "`scratch'/smcl_runs_manifest.txt"

global ZR_SVER = c(stata_version)
global ZR_BORN = c(born_date)
global ZR_DATE = c(current_date)

tempfile zrgitrev
quietly shell git -C "${ZR_REPO}" rev-parse HEAD > "`zrgitrev'"
tempname zrgfh
file open `zrgfh' using "`zrgitrev'", read text
file read `zrgfh' zrgitline
file close `zrgfh'
global ZR_COMMIT = trim(`"`zrgitline'"')
capture assert ustrregexm(`"${ZR_COMMIT}"', "^[0-9a-f]{40}$")
if _rc {
    display as error "extract_smcl_runs_truth.do: git rev-parse HEAD did not print a 40-character commit"
    exit 498
}

// ---------------------------------------------------------------------------
// One graph per probe.  zr_done <key> exports the SVG and writes the
// manifest line: key, graph number, return code.  The commands are typed
// on their own lines.
// ---------------------------------------------------------------------------
tempname zrm
file open `zrm' using "${ZR_REC}", write text replace
global ZR_FH `zrm'
global ZR_G = 0
global ZR_T = char(9)

capture program drop zr_done
program define zr_done
    args key
    local rc = _rc
    global ZR_G = ${ZR_G} + 1
    if `rc' == 0 {
        quietly graph export "${ZR_WORK}/sr_${ZR_G}.svg", name(zrg) replace as(svg)
        graph drop zrg
    }
    file write ${ZR_FH} "`key'${ZR_T}${ZR_G}${ZR_T}`rc'" _n
end

sysuse auto, clear

capture graph drop zrg
capture noisily twoway scatteri 0 0, xscale(off) yscale(off) title("a {bf:b} c") name(zrg, replace)
zr_done title.bold
capture graph drop zrg
capture noisily twoway scatteri 0 0, xscale(off) yscale(off) title("{it:p}-value") name(zrg, replace)
zr_done title.italic
capture graph drop zrg
capture noisily twoway scatteri 0 0, xscale(off) yscale(off) title("a{sup:q} b{sub:k}") name(zrg, replace)
zr_done title.supsub
capture graph drop zrg
capture noisily twoway scatter mpg weight, ytitle("m{sup:2}") name(zrg, replace)
zr_done ytitle.unicode
capture graph drop zrg
capture noisily twoway scatter mpg weight, xtitle("{stSerif:serif} sans") name(zrg, replace)
zr_done xtitle.font
capture graph drop zrg
capture noisily twoway scatter mpg weight, note("{bf:Source}: {it:Consumer Reports}") name(zrg, replace)
zr_done note.mixed
capture graph drop zrg
capture noisily twoway scatter mpg weight, t1title("x {it:y}") name(zrg, replace)
zr_done t1title.italic
capture graph drop zrg
capture noisily twoway scatter mpg weight, r1title("x {it:y}") name(zrg, replace)
zr_done r1title.italic
capture graph drop zrg
capture noisily twoway scatter mpg weight, title("{it:p} q", orientation(vertical)) name(zrg, replace)
zr_done title.vertical
capture graph drop zrg
capture noisily twoway scatter mpg weight, xlabel(3000 "{it:italic} text" 4000 "{bf:bold}" 5000 "a{sup:q}") name(zrg, replace)
zr_done xlabel.runs
capture graph drop zrg
capture noisily twoway (scatter mpg weight) (scatter turn weight), legend(label(1 "{it:Mileage} (mpg)") title("{bf:T} t")) name(zrg, replace)
zr_done legend.runs
capture graph drop zrg
capture noisily twoway scatter mpg weight, text(30 3000 "a {bf:b}") name(zrg, replace)
zr_done text.bold
capture graph drop zrg
capture noisily twoway scatter mpg weight, by(foreign, title("{it:t} u")) name(zrg, replace)
zr_done by.title
capture graph drop zrg
capture noisily twoway scatteri 0 0, xscale(off) yscale(off) title("a {bf:b} c") scale(1.5) name(zrg, replace)
zr_done title.scale15

// graph_text.sthlp's own examples (the six commands it runs with
// gr_example and gr_example2), keyed by the help topic.
capture graph drop zrg
capture noisily scatter mpg weight, title("This is {it:italics} in a graph title") name(zrg, replace)
zr_done help.italics
capture graph drop zrg
capture noisily scatter mpg weight, caption("{bf:Source}: {it:Consumer Reports}, used with permission") name(zrg, replace)
zr_done help.caption
capture graph drop zrg
capture noisily twoway function y = 2*exp(-2*x), range(0 2) title("{&function}(x)=2e{superscript:-2x}") name(zrg, replace)
zr_done help.funcsup1
capture graph drop zrg
capture noisily twoway function y = gammaden(1.5,2,0,x), range(0 10) title("{&chi}{sup:2}(3) distribution") name(zrg, replace)
zr_done help.funcsup2
capture graph drop zrg
capture noisily scatter mpg weight, title("Here are {stSerif:serif}, {stSans:sans serif}, and {stMono:monospace}") name(zrg, replace)
zr_done help.fonts
capture graph drop zrg
capture noisily scatter mpg weight, title(`"Text in {fontface "Century Schoolbook":a different font}"') name(zrg, replace)
zr_done help.fontface

// D-43-07.e's measured example: markup on part of a marker label.
generate lab = "a {bf:b}"
capture graph drop zrg
capture noisily twoway scatter mpg weight in 1, mlabel(lab) name(zrg, replace)
zr_done mlabel_part

file close `zrm'

python:
import json
import os
import sys
from sfi import Macro

REPO = Macro.getGlobal("ZR_REPO")
sys.path.insert(0, os.path.join(REPO, "scripts"))
import svg_text_runs

WORK = Macro.getGlobal("ZR_WORK")


def shifts(path):
    """The running dy of each tspan of each multi-run text, in order."""
    import re
    doc = open(path, encoding="utf-8").read()
    out = []
    for m in re.finditer(r"<text\b[^>]*>(.*?)</text>", doc, re.S):
        spans = re.findall(r"<tspan\b([^>]*)>", m.group(1))
        if len(spans) < 2:
            continue
        acc, row = 0.0, []
        for a in spans:
            d = re.search(r'\bdy="([-0-9.]+)px"', a)
            if d:
                acc += float(d.group(1))
            row.append(acc)
        out.append(row)
    return out


out = {
    "_meta": {
        "stata_version": Macro.getGlobal("ZR_SVER"),
        "born_date": Macro.getGlobal("ZR_BORN"),
        "dash_commit": Macro.getGlobal("ZR_COMMIT"),
        "extracted": Macro.getGlobal("ZR_DATE"),
        "source": "scripts/extract_smcl_runs_truth.do",
    },
}
sup_s, sup_v, sub_s, sub_v = [], [], [], []
with open(Macro.getGlobal("ZR_REC"), encoding="utf-8") as fh:
    rows = [l.rstrip("\n").split("\t", 2) for l in fh if l.strip()]
for key, g, rc in rows:
    rec = {"rc": int(rc)}
    if int(rc) == 0:
        path = os.path.join(WORK, "sr_%s.svg" % g)
        texts = [t for t in svg_text_runs.svg_text_runs(path)
                 if len(t["runs"]) > 1]
        dys = shifts(path)
        recs = []
        for t, dy in zip(texts, dys):
            base = t["runs"][0]["size"]
            for r, d in zip(t["runs"], dy):
                if d == 0:
                    base = r["size"]
                    break
            runs = []
            for r, d in zip(t["runs"], dy):
                s = round(r["size"] / base, 4)
                v = round(-d / base, 4) + 0.0
                runs.append({"t": r["text"], "b": r["weight"] == "bold",
                             "i": r["style"] == "italic",
                             "f": r["family"], "s": s, "v": v,
                             "level": r["level"]})
                if r["level"] == "sup":
                    sup_s.append(s)
                    sup_v.append(v)
                elif r["level"] == "sub":
                    sub_s.append(s)
                    sub_v.append(v)
            recs.append({"text": "".join(r["text"] for r in t["runs"]),
                         "size": base, "runs": runs})
        rec["texts"] = recs
    out[key] = rec


def mean(v):
    return round(sum(v) / len(v), 4) if v else None


out["ratios"] = {"sup_scale": mean(sup_s), "sup_shift": mean(sup_v),
                 "sub_scale": mean(sub_s), "sub_shift": mean(sub_v)}
with open(Macro.getGlobal("ZR_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2, sort_keys=True, ensure_ascii=True)
    fh.write("\n")
print("wrote", Macro.getGlobal("ZR_OUT"), len(out) - 2)
end
