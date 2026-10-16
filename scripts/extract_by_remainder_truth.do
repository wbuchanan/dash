*! extract_by_remainder_truth.do
*! WP-31 section 36 (D10, D3b): ground truth for the rest of by() --
*! by()'s own graphregion()/plotregion(), legend(ring(0)), the
*! by_alternate scheme stubs, the panel margin under f(k) x iscale(),
*! subtitleformat(), subtitle(, fcolor() lcolor() nobox position() ring()),
*! the shrink words, a one-panel by() with an empty value label and the
*! bystyles -- for test/fixtures/by_remainder_truth.json.
*!
*! Output: test/fixtures/by_remainder_truth.json
*!
*! Run with:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_by_remainder_truth.do
*!
*! METHOD
*!
*! `br id scheme "command"' reloads the data, runs `twoway <command>
*! name(Graph, replace)' under a text log and exports the graph to SVG.
*! The graph object's panel count, rows, cols, panel labels, the panel
*! margin (.Graph.style.indiv_margin) and the shrink switches go to a
*! record file.  The trailing python: block reads files only (never calls
*! Stata; a backtick is spelled \x60) and keeps, per probe, the SVG's
*! canvas, every rect at least 3 units on a side, every text and the
*! first marker's radius.
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
    display as error "extract_by_remainder_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_by_remainder_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global BR_REPO "`repo'"
global BR_OUT  "`repo'/test/fixtures/by_remainder_truth.json"
local scratch "`c(tmpdir)'dash_by_remainder_probe"
capture mkdir "`scratch'"
global BR_WORK "`scratch'"
global BR_REC  "`scratch'/by_remainder_records.txt"
global BR_BASE "`c(sysdir_base)'"

global BR_SVER = c(stata_version)
global BR_BORN = c(born_date)
global BR_DATE = c(current_date) + " " + c(current_time)

tempfile brgitrev
quietly shell git -C "${BR_REPO}" rev-parse HEAD > "`brgitrev'"
tempname brgfh
file open `brgfh' using "`brgitrev'", read text
file read `brgfh' brgitline
file close `brgfh'
global BR_COMMIT = trim(`"`brgitline'"')
capture assert ustrregexm(`"${BR_COMMIT}"', "^[0-9a-f]{40}$")
if _rc {
    display as error "extract_by_remainder_truth.do: git rev-parse HEAD did not print a 40-character commit: ${BR_COMMIT}"
    exit 498
}

// A copy of s2color with the by_alternate stubs set yes (D-36.d).
tempname sch
file open `sch' using "${BR_WORK}/scheme-dashbyalt.scheme", write text replace
file write `sch' "#include s2color" _n
file write `sch' "yesno by_alternate_xaxes yes" _n
file write `sch' "yesno by_alternate_yaxes yes" _n
file close `sch'
adopath + "${BR_WORK}"

sysuse auto, clear
egen g2 = cut(price), group(2)
egen g4 = cut(price), group(4)
egen g10 = cut(price), group(10)
format g4 %9.1f
generate byte one = 1
label define brempty 1 ""
generate byte onee = 1
label values onee brempty
keep mpg weight price foreign rep78 g2 g4 g10 one onee
quietly save "${BR_WORK}/br.dta", replace

// ---------------------------------------------------------------------------
// br id scheme "command": one probe, exported to SVG.
// ---------------------------------------------------------------------------
capture program drop br
program define br
    version 19
    args id scheme cmd
    use "${BR_WORK}/br.dta", clear
    set scheme `scheme'
    quietly log using "${BR_WORK}/`id'.log", text replace name(brlog)
    capture noisily twoway `cmd' name(Graph, replace)
    local rc = _rc
    local xrc = 0
    if !`rc' {
        capture noisily graph export "${BR_WORK}/`id'.svg", name(Graph) replace
        local xrc = _rc
    }
    quietly log close brlog
    file write brrec "R|`id'|`scheme'|`rc'|`xrc'|" `"`cmd'"' _n
    if `rc' | `xrc' exit
    capture local np = `.Graph.graphs.arrnels'
    if _rc | "`np'" == "" local np 0
    file write brrec "G|`id'|`np'|`.Graph.rows'|`.Graph.cols'|" ///
        "`.Graph.style.indiv_margin.left'|`.Graph.style.indiv_margin.right'|" ///
        "`.Graph.style.indiv_margin.bottom'|`.Graph.style.indiv_margin.top'|" ///
        "`.Graph.style.shrink_indiv.istrue'|`.Graph.style.shrink_plotregion.istrue'|" ///
        "`.Graph.style.alternate_xaxes.istrue'|`.Graph.style.alternate_yaxes.istrue'|" ///
        `"`.Graph.note.text[1]'"' _n
    forvalues k = 1/`np' {
        file write brrec "P|`id'|`k'|" `"`.Graph.graphs[`k'].subtitle.text[1]'"' ///
            "|`.Graph.graphs[`k'].subtitle.draw_view.istrue'" _n
    }
end

file open brrec using "${BR_REC}", write text replace

local one "scatter mpg weight"
local two "(scatter mpg weight)(lfit mpg weight)"

br plain s2color `"`one',"'
br by_foreign s2color `"`one', by(foreign)"'
// by()'s own regions and the outer ones
br regions_graph_red s2color `"`one', by(foreign, graphregion(fcolor(red)))"'
br regions_plot_blue s2color `"`one', by(foreign, plotregion(fcolor(blue)))"'
br regions_both s2color `"`one', by(foreign, graphregion(fcolor(red)) plotregion(fcolor(blue)))"'
br regions_outer_vs_by s2color `"`one', graphregion(fcolor(green)) by(foreign, graphregion(fcolor(red)))"'
br regions_outer_only s2color `"`one', graphregion(fcolor(green)) plotregion(fcolor(yellow)) by(foreign)"'
br regions_plot_lcolor s2color `"`one', by(foreign, plotregion(lcolor(black)))"'
br regions_margin s2color `"`one', by(foreign, graphregion(margin(large)))"'
br regions_plot_margin s2color `"`one', by(foreign, plotregion(margin(large)))"'
br regions_comma s2color `"`one', by(foreign, graphregion(fcolor(red), x))"'
// legend(ring(0))
br legend_beside s2color `"`two', by(rep78)"'
br legend_ring0_hole s2color `"`two', by(rep78, legend(ring(0)))"'
br legend_ring0_full s2color `"`two', by(foreign, legend(ring(0)))"'
br legend_ring0_pos5 s2color `"`two', by(rep78, legend(ring(0) pos(5)))"'
br legend_ring0_pos1 s2color `"`two', by(rep78, legend(ring(0) pos(1)))"'
br legend_pos1 s2color `"`two', by(rep78, legend(pos(1)))"'
br legend_pos12 s2color `"`two', by(foreign, legend(pos(12)))"'
br legend_ring0_pos12 s2color `"`two', by(foreign, legend(ring(0) pos(12)))"'
br legend_ring0_full_pos1 s2color `"`two', by(foreign, legend(ring(0) pos(1)))"'
// the by_alternate stubs
br alt_no s2color `"`one', by(rep78)"'
br alt_yes dashbyalt `"`one', by(rep78)"'
// the panel margin over the panel count and iscale()
br margin_2 s2color `"`one', by(g2)"'
br margin_4 s2color `"`one', by(g4)"'
br margin_10 s2color `"`one', by(g10)"'
br margin_iscale_half s2color `"`one', by(g4, iscale(.5))"'
// subtitleformat()
br stf_fmt s2color `"`one', by(g2, subtitleformat(%9.2f))"'
br stf_var s2color `"`one', by(g4, subtitleformat(var))"'
br stf_label s2color `"`one', by(foreign, subtitleformat(%9.2f))"'
br stf_textbox s2color `"`one', by(foreign, subtitleformat(size(large) color(red)))"'
br stf_none s2color `"`one', by(g4)"'
// the label box words: by()'s own subtitle() is the overall subtitle
// (stage 3), so its textbox words leave the panel labels alone; the
// graph's own subtitle() restyles every panel label (bygraph_g.class:497).
br byin_fcolor_lcolor s2color `"`one', by(foreign, subtitle(, fcolor(yellow) lcolor(blue)))"'
br byin_nobox s2color `"`one', by(foreign, subtitle(, nobox))"'
br byin_pos5_ring0 s2color `"`one', by(foreign, subtitle(, position(5) ring(0)))"'
br sub_fcolor_lcolor s2color `"`one', by(foreign) subtitle(, fcolor(yellow) lcolor(blue))"'
br sub_nobox s2color `"`one', by(foreign) subtitle(, nobox)"'
br sub_size_color s2color `"`one', by(foreign) subtitle(, size(large) color(red))"'
// D3b: the graph's subtitle(, position() ring()) on the panel labels
br sub_pos12 s2color `"`one', by(foreign) subtitle(, position(12))"'
br sub_pos5_ring0 s2color `"`one', by(foreign) subtitle(, position(5) ring(0))"'
foreach c in 1 3 6 7 9 11 0 {
    br sub_pos`c'_ring0 s2color `"`one', by(foreign) subtitle(, position(`c') ring(0))"'
}
br sub_pos1_ring0_nobexpand s2color `"`one', by(foreign) subtitle(, position(1) ring(0) nobexpand)"'
br sub_pos12_ring0 s2color `"`one', by(foreign) subtitle(, position(12) ring(0))"'
br sub_pos6 s2color `"`one', by(foreign) subtitle(, position(6))"'
br sub_pos9 s2color `"`one', by(foreign) subtitle(, position(9))"'
br sub_pos3 s2color `"`one', by(foreign) subtitle(, position(3))"'
br sub_pos11 s2color `"`one', by(foreign) subtitle(, position(11))"'
br sub_pos1 s2color `"`one', by(foreign) subtitle(, position(1))"'
br sub_pos7 s2color `"`one', by(foreign) subtitle(, position(7))"'
br sub_ring1_pos12 s2color `"`one', by(foreign) subtitle(, ring(1) position(12))"'
br sub_ring2_pos6 s2color `"`one', by(foreign) subtitle(, ring(2) position(6))"'
// the shrink words
foreach g in g2 g10 {
    br shrink_base_`g' s2color `"`one', by(`g')"'
    foreach w in noshrink noishrink nooverallshrink shrink ishrink overallshrink {
        br shrink_`w'_`g' s2color `"`one', by(`g', `w' title("T"))"'
    }
    br shrink_title_`g' s2color `"`one', by(`g', title("T"))"'
}
// a one-panel by() with an empty value label
br one_panel_empty s2color `"`one', by(onee)"'
br one_panel_plain s2color `"`one', by(one)"'
// the bystyles
foreach s in default compact altleg combine econ rescale stata7 {
    br bystyle_`s' s2color `"`two', by(rep78, style(`s'))"'
}
file close brrec

python:
import json, os, re, sys
from sfi import Macro

REPO = Macro.getGlobal("BR_REPO")
WORK = Macro.getGlobal("BR_WORK")
BASE = Macro.getGlobal("BR_BASE").rstrip("/")
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
            and not l.strip().startswith("file ")
            and not l.strip().startswith("(file ")]


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def r2(v):
    return None if v is None else round(v, 2)


probes, order = {}, []
with open(Macro.getGlobal("BR_REC"), encoding="utf-8", errors="replace") as fh:
    for line in fh:
        f = line.rstrip("\n").split("|")
        if f[0] == "R":
            pid = f[1]
            probes[pid] = {"scheme": f[2], "rc": int(f[3]) or int(f[4]),
                           "command": "|".join(f[5:]), "log": log_of(pid)}
            order.append(pid)
        elif f[0] == "G":
            p = probes[f[1]]
            p["n"] = int(f[2])
            p["rows"] = int(num(f[3]) or 0)
            p["cols"] = int(num(f[4]) or 0)
            p["indiv_margin"] = [num(v) for v in f[5:9]]
            p["shrink_indiv"] = f[9] == "1"
            p["shrink_plotregion"] = f[10] == "1"
            p["alternate_xaxes"] = f[11] == "1"
            p["alternate_yaxes"] = f[12] == "1"
            p["note"] = "|".join(f[13:])
            p["labels"] = []
        elif f[0] == "P":
            probes[f[1]]["labels"].append({"text": f[3],
                                           "drawn": f[4] == "1"})

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
    p["marker_r"] = r2(doc["circles"][0]["r"]) if doc["circles"] else None

stubs = []
with open(os.path.join(BASE, "s", "scheme-s2color.scheme"),
          encoding="utf-8", errors="replace") as fh:
    for line in fh:
        if re.match(r"\s*yesno\s+by_(alternate|skip_)", line):
            stubs.append(" ".join(line.split()))

out = {"probes": {pid: probes[pid] for pid in order}}
out["_meta"] = {"stata_version": Macro.getGlobal("BR_SVER"),
                "born_date": Macro.getGlobal("BR_BORN"),
                "dash_commit": Macro.getGlobal("BR_COMMIT"),
                "extracted": Macro.getGlobal("BR_DATE"),
                "source": "scripts/extract_by_remainder_truth.do",
                "by_alt_stubs": stubs}
with open(Macro.getGlobal("BR_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=0, sort_keys=True)
    fh.write("\n")
print("WROTE %s probes=%d" % (Macro.getGlobal("BR_OUT"), len(order)))
end

display as text "extract_by_remainder_truth.do: done"
