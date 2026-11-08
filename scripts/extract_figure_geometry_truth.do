*! extract_figure_geometry_truth.do
*! WP-45 section 45-04 (VF-4, GW-6): twoway's figure geometry -- the page
*! size, plot regions, tick-label size, marker radius and line widths per
*! scheme, by() graphs included; the xsize()/ysize()/aspectratio()/
*! fxsize()/fysize() boxes; the units of xsize(); the graph region's
*! outline and margin; the inner box -- for
*! test/fixtures/figure_geometry_truth.json.
*!
*! Output: test/fixtures/figure_geometry_truth.json
*!
*! Run with:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_figure_geometry_truth.do
*!
*! METHOD
*!
*! `fg id scheme "command"' reloads auto, runs `twoway <command>
*! name(Graph, replace)' under a text log and exports the graph to SVG.
*! The return code goes to a record file.  The trailing python: block
*! reads files only (never calls Stata; a backtick is spelled \x60) and
*! keeps, per probe, the rc, the first log line after the command (the
*! error text when it fails), the SVG's canvas, every rect at least 3
*! units on a side (fill, stroke, stroke width), every text, the page in
*! inches, the marker radii and the line widths.
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
    display as error "extract_figure_geometry_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_figure_geometry_truth.do: `_zl_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global FG_REPO "`repo'"
global FG_OUT  "`repo'/test/fixtures/figure_geometry_truth.json"
local scratch "`c(tmpdir)'dash_figure_geometry_probe"
capture mkdir "`scratch'"
global FG_WORK "`scratch'"
global FG_REC  "`scratch'/figure_geometry_records.txt"
global FG_BASE "`c(sysdir_base)'"

global FG_SVER = c(stata_version)
global FG_BORN = c(born_date)
global FG_DATE = c(current_date) + " " + c(current_time)

tempfile fggitrev
quietly shell git -C "${FG_REPO}" rev-parse HEAD > "`fggitrev'"
tempname fggfh
file open `fggfh' using "`fggitrev'", read text
file read `fggfh' fggitline
file close `fggfh'
global FG_COMMIT = trim(`"`fggitline'"')
capture assert ustrregexm(`"${FG_COMMIT}"', "^[0-9a-f]{40}$")
if _rc {
    display as error "extract_figure_geometry_truth.do: git rev-parse HEAD did not print a 40-character commit: ${FG_COMMIT}"
    exit 498
}


sysuse auto, clear
keep mpg weight price foreign rep78
quietly save "${FG_WORK}/fg.dta", replace

// ---------------------------------------------------------------------------
// fg id scheme "command": one probe, exported to SVG.
// ---------------------------------------------------------------------------
capture program drop fg
program define fg
    version 19
    args id scheme cmd
    use "${FG_WORK}/fg.dta", clear
    set scheme `scheme'
    quietly log using "${FG_WORK}/`id'.log", text replace name(fglog)
    capture noisily twoway `cmd' name(Graph, replace)
    local rc = _rc
    local xrc = 0
    if !`rc' {
        capture erase "${FG_WORK}/`id'.svg"
        capture noisily graph export "${FG_WORK}/`id'.svg", name(Graph) replace
        local xrc = _rc
    }
    quietly log close fglog
    file write fgrec "R|`id'|`scheme'|`rc'|`xrc'|" `"`cmd'"' _n
end

file open fgrec using "${FG_REC}", write text replace

local one "scatter mpg weight"

// VF-4/VF-5: the default graph per scheme, by() included
fg G_stcolor stcolor `"`one',"'
fg G_s2color s2color `"`one',"'
fg G_economist economist `"`one',"'
fg G_by_stcolor stcolor `"`one', by(foreign)"'
fg G_by_s2color s2color `"`one', by(foreign)"'
// VF-4: the size options
fg G_xs44 stcolor `"`one', xsize(4) ysize(4)"'
fg G_xs9 stcolor `"`one', xsize(9)"'
fg G_ar1 stcolor `"`one', aspectratio(1)"'
fg G_by_xs84 stcolor `"`one', by(foreign) xsize(8) ysize(4)"'
// VF-11/GW-20: fxsize()/fysize()
fg G_fx50 stcolor `"`one', fxsize(50)"'
fg G_fy50 stcolor `"`one', fysize(50)"'
fg G_fx50_by stcolor `"`one', by(foreign) fxsize(50)"'
fg G_fy50_by stcolor `"`one', by(foreign) fysize(50)"'
// GW-1: xsize()/ysize() units
fg U_10cm stcolor `"`one', xsize(10cm)"'
fg U_3in stcolor `"`one', xsize(3in)"'
fg U_200pt stcolor `"`one', xsize(200pt)"'
fg U_254cm stcolor `"`one', xsize(2.54cm)"'
fg U_72pt stcolor `"`one', xsize(72pt)"'
fg U_05in stcolor `"`one', xsize(0.5in)"'
fg U_300cm stcolor `"`one', xsize(300cm)"'
fg U_200 stcolor `"`one', xsize(200)"'
fg U_05 stcolor `"`one', xsize(0.5)"'
// U_10CMup, not U_10CM: the probe files are named by id, and on a
// case-blind file system U_10CM.log is U_10cm.log (the 10cm row read
// 10CM's log and picture).
fg U_10CMup stcolor `"`one', xsize(10CM)"'
fg U_10_cm stcolor `"`one', xsize(10 cm)"'
fg U_abc stcolor `"`one', xsize(abc)"'
fg U_y200pt stcolor `"`one', ysize(200pt)"'
fg U_y05in stcolor `"`one', ysize(0.5in)"'
fg U_y200 stcolor `"`one', ysize(200)"'
fg U_3_in stcolor `"`one', xsize(3 in)"'
// GW-6/VF-7: the graph region's outline and margin
foreach s in s2color stcolor s1color {
    fg M_`s' `s' `"`one',"'
    fg M_`s'_red `s' `"`one', graphregion(fcolor(red))"'
    fg M_by_`s' `s' `"`one', by(foreign)"'
}
// ST-21/GW-19: the inner box, lalign() and the plot-region margin
fg I_ilc stcolor `"`one', graphregion(ilcolor(red))"'
fg I_ifc stcolor `"`one', graphregion(ifcolor(red))"'
fg I_gla stcolor `"`one', graphregion(lalign(inside) lcolor(red) lwidth(thick))"'
fg I_pla stcolor `"`one', plotregion(lalign(outside) lcolor(red) lwidth(thick))"'
fg I_pm84 stcolor `"`one', plotregion(margin(10)) xsize(8) ysize(4)"'
fg I_pm48 stcolor `"`one', plotregion(margin(10)) xsize(4) ysize(8)"'
fg I_by stcolor `"`one', by(foreign) graphregion(ifcolor(red) ilcolor(blue))"'
// The 41-05 checkpoint pairs (by() layout screenshots)
fg P1 s2color `"`one', by(foreign, compact)"'
fg P2 stcolor `"(scatter mpg weight) (lfit mpg weight), by(rep78, style(combine))"'
fg P3 stcolor `"`one', subtitle(, position(3)) by(foreign)"'
fg P4 stcolor `"`one', by(foreign, title("T", position(3)))"'
fg P5 stcolor `"`one', aspectratio(1) by(foreign)"'
fg P6 stcolor `"`one', by(foreign, graphregion(margin(small)))"'
fg P7 stcolor `"scatter price weight, ylabel(, format(%15.2fc)) by(rep78)"'
file close fgrec

python:
import json, os, re, sys
from sfi import Macro

REPO = Macro.getGlobal("FG_REPO")
WORK = Macro.getGlobal("FG_WORK")
sys.path.insert(0, os.path.join(REPO, "scripts"))
import svg_truth

_HEAD = re.compile(r"^\s*(name|log|log type|opened on|closed on):")
_SIZE = re.compile(r'<svg[^>]*\swidth="([\d.]+)in"[^>]*\sheight="([\d.]+)in"')


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
with open(Macro.getGlobal("FG_REC"), encoding="utf-8", errors="replace") as fh:
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
    with open(path, encoding="utf-8", errors="replace") as fh:
        m = _SIZE.search(fh.read(4000))
    p["inches"] = [float(m.group(1)), float(m.group(2))] if m else None
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
    p["marker_r"] = sorted({r2(c.get("r")) for c in doc["circles"]
                            if c.get("r")})
    p["line_widths"] = sorted({r2(d.get("width")) for d in
                               doc["hlines"] + doc["vlines"]
                               if d.get("width")})

out = {"probes": {pid: probes[pid] for pid in order}}
out["_meta"] = {"stata_version": Macro.getGlobal("FG_SVER"),
                "born_date": Macro.getGlobal("FG_BORN"),
                "dash_commit": Macro.getGlobal("FG_COMMIT"),
                "extracted": Macro.getGlobal("FG_DATE"),
                "source": "scripts/extract_figure_geometry_truth.do"}
with open(Macro.getGlobal("FG_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=0, sort_keys=True)
    fh.write("\n")
print("WROTE %s probes=%d" % (Macro.getGlobal("FG_OUT"), len(order)))
end

display as text "extract_figure_geometry_truth.do: done"
