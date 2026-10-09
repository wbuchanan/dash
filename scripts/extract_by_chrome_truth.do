*! extract_by_chrome_truth.do
*! WP-30 section 53 (P1.15c): ground truth for the chrome twoway shares
*! across a by() graph's panels -- which panels draw which axes, axis
*! titles and legends, the one overall legend and colour key and where
*! they go, how the i*/noi* words, edgelabel, individual and ilegends are
*! read -- and for the filled box each panel label is drawn in, for
*! test/fixtures/by_chrome_truth.json.
*!
*! WHY THIS EXISTS
*!
*! dash drew both axes, both axis titles, a legend and a colour key on
*! every by() panel and named legend(), clegend() and the i* words as
*! ignored.  bygraph_g.class decides them: parse_settings (the words),
*! set_axes_shown/titles/labels/ticks and set_outer_axes (the axes),
*! SetLegend and SetClegend (the keys); bygraphstyle-default.style draws
*! each panel's label as a boxed textbox.
*!
*! Output: test/fixtures/by_chrome_truth.json
*!
*! Run with:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_by_chrome_truth.do
*!
*! METHOD
*!
*! `bc id scheme "command"' reloads auto and runs `twoway <command>
*! name(Graph, replace)' under the scheme.  The record file gets the
*! graph object's members: its rows, cols, holes and key holes; its
*! style's edgelabel, outer_*, indiv_* switches; the overall l1title,
*! b1title and r1title text, the overall legend's and colour key's
*! draw_view and relative_position; and per panel the draw_view of its
*! y, x and second y axes, of their titles, and of its legend and colour
*! key.  `bb id scheme "command"' exports the graph to SVG for the label
*! boxes.  The trailing python: block reads files only (never calls
*! Stata; a backtick is spelled \x60): for each panel label in the SVG,
*! the rects drawn just before its text (fill, stroke, width), the
*! panel's plot-region rect under it, and the label's font.
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
    display as error "extract_by_chrome_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_by_chrome_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1
global BC_REPO "`repo'"
global BC_OUT  "`repo'/test/fixtures/by_chrome_truth.json"
local scratch "`c(tmpdir)'dash_by_chrome_probe"
capture mkdir "`scratch'"
global BC_WORK "`scratch'"
global BC_REC  "`scratch'/by_chrome_records.txt"

global BC_SVER = c(stata_version)
global BC_BORN = c(born_date)
global BC_DATE = c(current_date) + " " + c(current_time)

tempfile bcgitrev
quietly shell git -C "${BC_REPO}" rev-parse HEAD > "`bcgitrev'"
tempname bcgfh
file open `bcgfh' using "`bcgitrev'", read text
file read `bcgfh' bcgitline
file close `bcgfh'
global BC_COMMIT = trim(`"`bcgitline'"')
capture assert ustrregexm(`"${BC_COMMIT}"', "^[0-9a-f]{40}$")
if _rc {
    display as error "extract_by_chrome_truth.do: git rev-parse HEAD did not print a 40-character commit: ${BC_COMMIT}"
    exit 498
}

sysuse auto, clear
quietly save "${BC_WORK}/bc.dta", replace

// ---------------------------------------------------------------------------
// bc id scheme "command": one chrome probe.
// ---------------------------------------------------------------------------
capture program drop bc
program define bc
    version 19
    args id scheme cmd
    use "${BC_WORK}/bc.dta", clear
    set scheme `scheme'
    capture noisily twoway `cmd' name(Graph, replace)
    local rc = _rc
    file write bcrec "R|`id'|`scheme'|`rc'|" `"`cmd'"' _n
    if `rc' exit
    local np `.Graph.graphs.arrnels'
    file write bcrec "G|`id'|`np'|`.Graph.rows'|`.Graph.cols'|`.Graph.holes'|" ///
        "`.Graph.legend_hole'|`.Graph.clegend_hole'" _n
    local fl ""
    foreach f in edgelabel outer_xaxes outer_yaxes outer_xtitles outer_ytitles ///
        indiv_xaxes indiv_yaxes indiv_xlabels indiv_ylabels indiv_xticks ///
        indiv_yticks indiv_xtitles indiv_ytitles indiv_as_whole indiv_legends ///
        indiv_xrescale indiv_yrescale {
        local fl `"`fl'|`f'=`.Graph.style.`f'.istrue'"'
    }
    file write bcrec `"F|`id'`fl'"' _n
    file write bcrec "O|`id'|" `"`.Graph.l1title.text[1]'|`.Graph.b1title.text[1]'|`.Graph.r1title.text[1]'|"' ///
        "`.Graph.legend.draw_view.istrue'|`.Graph.style.legend_position.relative_position'|" ///
        "`.Graph.clegend.draw_view.istrue'|`.Graph.style.zyx2legend_position.relative_position'|" ///
        "`.Graph.at_legend.draw_view.istrue'|`.Graph.at_clegend.draw_view.istrue'|" ///
        "`.Graph.graphs[1].legend.keys.arrnels'" _n
    forvalues k = 1/`np' {
        local g ".Graph.graphs[`k']"
        file write bcrec "P|`id'|`k'|" `"`.Graph.graphs[`k'].subtitle.text[1]'"' "|" ///
            "`.Graph.graphs[`k'].yaxis1.draw_view.istrue'|`.Graph.graphs[`k'].xaxis1.draw_view.istrue'|" ///
            "`.Graph.graphs[`k'].yaxis2.draw_view.istrue'|" ///
            "`.Graph.graphs[`k'].yaxis1.title.draw_view.istrue'|`.Graph.graphs[`k'].xaxis1.title.draw_view.istrue'|" ///
            "`.Graph.graphs[`k'].yaxis2.title.draw_view.istrue'|" ///
            "`.Graph.graphs[`k'].legend.draw_view.istrue'|`.Graph.graphs[`k'].clegend.draw_view.istrue'" _n
    }
end

// bb id scheme "command": one label-box probe, exported to SVG.
capture program drop bb
program define bb
    version 19
    args id scheme cmd
    use "${BC_WORK}/bc.dta", clear
    set scheme `scheme'
    capture noisily twoway `cmd' name(Graph, replace)
    local rc = _rc
    local xrc = 0
    if !`rc' {
        capture noisily graph export "${BC_WORK}/`id'.svg", name(Graph) replace
        local xrc = _rc
    }
    file write bcrec "B|`id'|`scheme'|`=`rc' + `xrc''|" `"`cmd'"' _n
    if `rc' | `xrc' exit
    local np `.Graph.graphs.arrnels'
    forvalues k = 1/`np' {
        file write bcrec "L|`id'|`k'|" `"`.Graph.graphs[`k'].subtitle.text[1]'"' _n
    }
end

file open bcrec using "${BC_REC}", write text replace

local two "(scatter mpg weight)(lfit mpg weight)"
local one "scatter mpg weight"
local dual "(scatter mpg weight)(scatter price weight, yaxis(2))"

// The chrome probes, under stcolor unless named.
bc p01 stcolor `"`one', by(foreign)"'
bc p02 stcolor `"`two', by(foreign)"'
bc p02_s2 s2color `"`two', by(foreign)"'
bc p02_ec economist `"`two', by(foreign)"'
bc p03 stcolor `"`two', by(foreign, legend(off))"'
bc p04 stcolor `"`two', by(foreign) legend(off)"'
bc p05 stcolor `"`two', by(foreign, total legend(at(4) pos(0)))"'
bc p06 stcolor `"`two', by(foreign, total)"'
bc p08 stcolor `"`one', by(rep78, holes(2))"'
bc p09 stcolor `"`one', by(rep78, colfirst)"'
bc p18 stcolor `"`one', by(rep78, iylabels)"'
bc p19 stcolor `"`one', by(foreign, iyaxes noiylabels)"'
bc p20 stcolor `"`one', by(foreign, iyaxes noiyticks)"'
bc p21 stcolor `"`one', by(rep78, iyaxes ixaxes)"'
bc p22 stcolor `"`one', by(rep78, iytitles ixtitles iyaxes ixaxes)"'
bc p23 stcolor `"`one', by(foreign, total noedgelabel)"'
bc p24 stcolor `"`one', by(foreign, total compact)"'
bc p25 stcolor `"`one', by(foreign, noytitles noxtitles)"'
bc p26 stcolor `"`one', by(foreign, individual)"'
bc p27 stcolor `"`dual', by(foreign) ytitle("Price", axis(2))"'
bc p28 stcolor `"`dual', by(foreign, iytitles iyaxes) ytitle("Price", axis(2))"'
bc p32 stcolor `"`two', by(foreign, ilegends)"'
bc p33 stcolor `"`one', by(foreign, legend(on))"'
bc p34 stcolor `"`two', by(foreign) legend(on)"'
bc p40 stcolor `"`one', by(rep78, holes(1 5))"'
bc p41 stcolor `"`one', by(rep78, colfirst holes(3))"'
bc p43 stcolor `"`one', by(foreign, total ixaxes)"'
bc p44 stcolor `"`one', by(foreign, iyticks)"'
bc p46 stcolor `"`two', by(foreign, legend(at(3) pos(0)))"'
bc p47 stcolor `"`one', by(foreign rep78, compact)"'
bc p48 stcolor `"`one', by(foreign, yrescale)"'
bc p49 stcolor `"`one', by(foreign, iyaxes noiyaxes)"'
bc p50 stcolor `"`one', by(foreign, noiyaxes iyaxes)"'
bc p51 stcolor `"`one', by(foreign, style(compact) total)"'
bc q06 stcolor `"scatter mpg weight, colorvar(price) by(foreign)"'
bc q07 stcolor `"scatter mpg weight, colorvar(price) by(foreign, clegend(on))"'
bc q08 stcolor `"scatter mpg weight, colorvar(rep78) colordiscrete by(foreign, clegend(on))"'
bc q09 stcolor `"scatter mpg weight, colorvar(price) by(foreign, clegend(on pos(6)))"'
bc r04 stcolor `"`two', by(foreign, legend(pos(6))) legend(order(2 1))"'
bc r05 stcolor `"`two', by(foreign, legend(pos(9)))"'
bc r06 stcolor `"`two', by(foreign, legend(pos(12) ring(0)))"'

// The abbreviation probes (E4): the style switch each spelling sets.
local i 0
foreach a in ix iy ixl ixt ixti ixtit noixt noedge ileg ind iyt iyti iytit {
    local ++i
    bc a`i' stcolor `"`one', by(foreign, `a')"'
}

// The label-box probes, every scheme dash ships.
foreach s in economist meta s1color s1manual s1mono s1rcolor s2color ///
    s2color8 s2gcolor s2gmanual s2manual s2mono sj stcolor stcolor_alt ///
    stcolor_meta stcolor_mv stcoloralias stgcolor stgcolor_alt ///
    stgcolor_meta stgcolor_mv stmono1 stmono2 stsj sttrans {
    bb box_`s' `s' `"`one', by(foreign)"'
}
bb box_two s2color `"`one', by(foreign rep78)"'
bb box_total s2color `"`one', by(foreign, total)"'
bb box_fcolor s2color `"`one', by(foreign) subtitle(, fcolor(red) lcolor(blue))"'
bb box_nobox s2color `"`one', by(foreign) subtitle(, nobox)"'
file close bcrec

python:
import json, os, re, sys
from sfi import Macro

REPO = Macro.getGlobal("BC_REPO")
WORK = Macro.getGlobal("BC_WORK")
sys.path.insert(0, os.path.join(REPO, "scripts"))
import svg_truth

_TAG = re.compile(r"<(rect|text)\b([^>]*?)/?>(?:([^<]*)</text>)?", re.S)


def flag(v):
    v = (v or "").strip()
    return None if v == "" else v == "1"


probes, boxes, order = {}, {}, []
with open(Macro.getGlobal("BC_REC"), encoding="utf-8", errors="replace") as fh:
    for line in fh:
        f = line.rstrip("\n").split("|")
        k = f[0]
        if k == "R":
            probes[f[1]] = {"scheme": f[2], "rc": int(f[3]),
                            "command": "|".join(f[4:]), "panels": []}
            order.append(f[1])
        elif k == "G":
            p = probes[f[1]]
            p["n"] = int(f[2])
            p["rows"], p["cols"] = int(f[3]), int(f[4])
            p["holes"] = [int(v) for v in f[5].split()]
            p["legend_hole"] = int(f[6] or 0)
            p["clegend_hole"] = int(f[7] or 0)
        elif k == "F":
            p = probes[f[1]]
            p["style"] = {kv.split("=")[0]: flag(kv.split("=")[1])
                          for kv in f[2:]}
        elif k == "O":
            p = probes[f[1]]
            p["l1title"], p["b1title"], p["r1title"] = f[2], f[3], f[4]
            p["legend"] = {"drawn": flag(f[5]), "side": f[6],
                           "at_drawn": flag(f[9])}
            p["clegend"] = {"drawn": flag(f[7]), "side": f[8],
                            "at_drawn": flag(f[10])}
            p["panel1_keys"] = int(f[11] or 0)
        elif k == "P":
            p = probes[f[1]]
            names = ("y", "x", "y2", "ytitle", "xtitle", "y2title",
                     "legend", "clegend")
            rec = {"label": f[3]}
            rec.update({n: flag(v) for n, v in zip(names, f[4:12])})
            p["panels"].append(rec)
        elif k == "B":
            boxes[f[1]] = {"scheme": f[2], "rc": int(f[3]),
                           "command": "|".join(f[4:]), "labels": []}
        elif k == "L":
            boxes[f[1]]["labels"].append(f[3])


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
        if m.group(1) == "text":
            e["text"] = svg_truth.normalise_text(m.group(3) or "")
            e["size"] = svg_truth._fnum(
                (st.get("font-size") or "").replace("px", ""))
            e["anchor"] = a.get("text-anchor")
        out.append(e)
    return out, svg_truth.svg_document(path).get("canvas")


def label_boxes(pid, labels):
    els, canvas = elements(os.path.join(WORK, pid + ".svg"))
    rects = [e for e in els if e["tag"] == "rect"]
    res = []
    for lab in labels:
        idx = [i for i, e in enumerate(els)
               if e["tag"] == "text" and e["text"] == lab]
        if not idx:
            res.append({"label": lab, "box": None})
            continue
        i = max(idx, key=lambda j: els[j]["size"] or 0)
        before = []
        j = i - 1
        while j >= 0 and els[j]["tag"] == "rect" and len(before) < 2:
            before.insert(0, els[j])
            j -= 1
        rec = {"label": lab, "font_size": els[i]["size"],
               "anchor": els[i]["anchor"], "text_x": els[i]["x"],
               "rects": [{k: r[k] for k in ("x", "y", "width", "height",
                                            "fill", "stroke",
                                            "stroke_width")}
                         for r in before]}
        fills = [r for r in before if r["fill"] not in (None, "none")]
        strokes = [r for r in before if r["stroke"] not in (None, "none")]
        if fills:
            b = fills[0]
            rec["box"] = {"fill": b["fill"], "x": b["x"], "y": b["y"],
                          "width": b["width"], "height": b["height"],
                          "outline": strokes[0]["stroke"] if strokes else None,
                          "stroke_width": (strokes[0]["stroke_width"]
                                           if strokes else None)}
            under = [r for r in rects if r["width"] and r["x"] is not None
                     and abs(r["x"] - b["x"]) < 1.0
                     and abs(r["width"] - b["width"]) < 1.0
                     and r["y"] > b["y"] + b["height"] - 1.0]
            rec["plotregion"] = ({k: under[0][k] for k in
                                  ("x", "y", "width", "height")}
                                 if under else None)
        else:
            rec["box"] = None
            rec["plotregion"] = None
        res.append(rec)
    return {"panels": res,
            "units_per_rs": (min(canvas["w"], canvas["h"]) / 100.0
                             if canvas else None)}


box_out = {}
for pid, b in boxes.items():
    rec = {"scheme": b["scheme"], "rc": b["rc"], "command": b["command"]}
    if not b["rc"]:
        rec.update(label_boxes(pid, b["labels"]))
    box_out[pid] = rec

out = {"probes": {pid: probes[pid] for pid in order}, "label_box": box_out}
out["_meta"] = {"stata_version": Macro.getGlobal("BC_SVER"),
                "born_date": Macro.getGlobal("BC_BORN"),
                "dash_commit": Macro.getGlobal("BC_COMMIT"),
                "extracted": Macro.getGlobal("BC_DATE"),
                "script": "scripts/extract_by_chrome_truth.do",
                "method": "twoway per probe under the named scheme; the "
                          "graph object's rows, cols, holes, key holes, "
                          "style switches, l1/b1/r1 title text, overall "
                          "legend and colour key draw_view and "
                          "relative_position, and per panel the draw_view "
                          "of its y, x and y2 axes, their titles, its "
                          "legend and colour key; label boxes from the "
                          "rects written just before each panel label's "
                          "text in the SVG export"}
with open(Macro.getGlobal("BC_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1, sort_keys=True)
    fh.write("\n")
print("WROTE %s probes=%d boxes=%d" % (Macro.getGlobal("BC_OUT"),
                                        len(order), len(box_out)))
end

display as text "extract_by_chrome_truth.do: done"
