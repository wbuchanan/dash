*! extract_region_truth.do
*! WP-30 section 38 (P1.20a): ground truth for plotregion() and
*! graphregion() styling and for bgcolor(), for
*! test/fixtures/region_truth.json.
*!
*! WHY THIS EXISTS
*!
*! dash read only color()/fcolor(), lcolor() and lwidth() of a region,
*! under their full names, drew none as black, dropped %NN, ignored
*! style(), lstyle() and lpattern(), and coloured the graph region with
*! bgcolor().  This script records what twoway (StataNow 19.5,
*! _fr_area_parse_and_log.ado) accepts, refuses and draws:
*!   S  every spelling of every region sub-option (rc), nodraw
*!   R  the refusals and their order (rc, first error line), nodraw
*!   D  the drawing probes, exported as SVG, under s2color, stcolor, s1color
*!   M  repeated copies, SVG, s2color
*!   B  by() with outer regions, SVG, s2color (the closeout's residual)
*! Roles come from scripts/svg_truth.py's svg_rects: the first rect is the
*! canvas, rects at x < 20 the graph region, the next ones the plot
*! region; a rect whose fill is none is an outline.  A dashed outline is
*! drawn as line segments over an invisible rect, so it is read from the
*! horizontal lines on the region's edge.
*!
*! Run (never the GUI; the slot wrapper):
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_region_truth.do
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
    display as error "extract_region_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_region_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1
global ZR_REPO "`repo'"

local stata_version = c(stata_version)
local born_date "`c(born_date)'"
local extracted "`c(current_date)'"
tempfile gh
quietly shell git -C "${ZR_REPO}" rev-parse HEAD > "`gh'"
tempname fh
file open `fh' using "`gh'", read text
file read `fh' dash_commit
file close `fh'

* ---- the probe directory (never in the repository) and its registry -------
local pdir "`c(tmpdir)'"
while strlen(`"`pdir'"') > 1 & inlist(substr(`"`pdir'"', -1, 1), "/", char(92)) {
    local pdir = substr(`"`pdir'"', 1, strlen(`"`pdir'"') - 1)
}
local pdir "`pdir'/region_probes"
capture mkdir "`pdir'"
local _sf : dir "`pdir'" files "*"
foreach f of local _sf {
    erase "`pdir'/`f'"
}
global ZR_PDIR "`pdir'"
tempname reg
file open `reg' using "`pdir'/registry.txt", write text replace
global ZR_REG "`reg'"
global ZR_SEQ 0

* ---- _rs_probe id svg scheme : options -------------------------------------
* Runs twoway scatter mpg weight, <options> scheme(<scheme>) under capture
* noisily inside a named log; exports the SVG when svg is 1 and rc is 0.
capture program drop _rs_probe
program define _rs_probe
    version 19
    gettoken id 0 : 0
    gettoken svg 0 : 0
    gettoken sch 0 : 0
    gettoken colon 0 : 0
    local opts = strtrim(`"`macval(0)'"')
    graph drop _all
    global ZR_SEQ = ${ZR_SEQ} + 1
    local f "p${ZR_SEQ}"
    local nd = cond(`svg', "", "nodraw")
    capture log close rs_probe
    quietly log using "${ZR_PDIR}/`f'.log", text replace name(rs_probe)
    capture noisily twoway scatter mpg weight, `macval(opts)' scheme(`sch') `nd'
    local rc = _rc
    quietly log close rs_probe
    if `rc' == 0 & `svg' {
        quietly graph export "${ZR_PDIR}/`f'.svg", as(svg) replace
    }
    file write ${ZR_REG} `"`f'"' _tab `"`id'"' _tab `"`sch'"' _tab `"`svg'"' _tab `"`rc'"' _tab `"`macval(opts)'"' _n
end

sysuse auto, clear

* ---- S: every spelling, from one letter to the full name, and the capital --
local rows "style:sty istyle:isty lstyle:ls ilstyle:ils lcolor:lc ilcolor:ilc lwidth:lw ilwidth:ilw lpattern:lp ilpattern:ilp lalign:la ilalign:ila shadestyle:shades ishadestyle:ishades fcolor:fc ifcolor:ifc color:c icolor:ic intensity:inten iintensity:iinten margin:m marginonly:marginonly"
foreach r of local rows {
    gettoken full rest : r, parse(":")
    local mn = substr("`rest'", 2, .)
    local arg "(red)"
    if inlist("`full'", "style", "istyle", "lstyle", "ilstyle", "shadestyle", "ishadestyle") local arg "(none)"
    if inlist("`full'", "lwidth", "ilwidth") local arg "(thick)"
    if inlist("`full'", "lpattern", "ilpattern") local arg "(dash)"
    if inlist("`full'", "lalign", "ilalign") local arg "(inside)"
    if inlist("`full'", "intensity", "iintensity") local arg "(50)"
    if inlist("`full'", "margin") local arg "(zero)"
    if "`full'" == "marginonly" local arg ""
    forvalues k = 1/`=strlen("`full'")' {
        local pre = substr("`full'", 1, `k')
        _rs_probe S|`full'|`pre' 0 s2color : plotregion(`pre'`arg')
    }
    local up = strupper("`full'")
    _rs_probe S|`full'|`up' 0 s2color : plotregion(`up'`arg')
}

* ---- R: refusals and their order -------------------------------------------
_rs_probe R01 0 s2color : plotregion(bogus(1))
_rs_probe R02 0 s2color : plotregion(st(none))
_rs_probe R03 0 s2color : plotregion(is(none))
_rs_probe R04 0 s2color : plotregion(COLOR(red))
_rs_probe R05 0 s2color : plotregion(none)
_rs_probe R06 0 s2color : plotregion(c(red) c(red))
_rs_probe R07 0 s2color : plotregion(fc(red) fcolor(blue))
_rs_probe R08 0 s2color : plotregion(margin(l+10) margin(r+10))
_rs_probe R09 0 s2color : plotregion(color(red) marginonly marginonly)
_rs_probe R10 0 s2color : plotregion(margino)
_rs_probe R11 0 s2color : plotregion(color(red), lcolor(blue))
_rs_probe R12 0 s2color : plotregion(, color(red))
_rs_probe R13 0 s2color : graphregion(color(red)) graphregion(c(blue) c(green))
_rs_probe R14 0 s2color : graphregion(bogus(1)) plotregion(foo(2))
_rs_probe R15 0 s2color : plotregion(foo(2)) graphregion(bogus(1))
_rs_probe R16 0 s2color : legend(bogus) plotregion(foo(1))
_rs_probe R17 0 s2color : xline(abc) plotregion(foo(1))
_rs_probe R18 0 s2color : plotregion(color(red),)
_rs_probe R19 0 s2color : plotregion(lalign(bogus))
_rs_probe R20 0 s2color : plotregion(lpattern(bogus))
_rs_probe R21 0 s2color : plotregion(margin(bogus))
_rs_probe R22 0 s2color : plotregion(lcolor(notacolour))
_rs_probe R23 0 s2color : plotregion(lwidth(abc))

* ---- D: drawing, under three schemes ---------------------------------------
foreach sch in s2color stcolor s1color {
    _rs_probe D01 1 `sch' :
    _rs_probe D02 1 `sch' : plotregion(color(red))
    _rs_probe D03 1 `sch' : plotregion(c(red))
    _rs_probe D04 1 `sch' : plotregion(fcolor(blue) color(red))
    _rs_probe D05 1 `sch' : plotregion(color(red) fcolor(blue))
    _rs_probe D06 1 `sch' : plotregion(color(red) lcolor(blue))
    _rs_probe D07 1 `sch' : plotregion(lcolor(blue) color(red))
    _rs_probe D08 1 `sch' : plotregion(style(none))
    _rs_probe D09 1 `sch' : graphregion(style(none))
    _rs_probe D10 1 `sch' : plotregion(style(none) fcolor(red))
    _rs_probe D11 1 `sch' : plotregion(lstyle(none))
    _rs_probe D12 1 `sch' : plotregion(lstyle(none) lcolor(red))
    _rs_probe D13 1 `sch' : plotregion(ls(none) lcolor(red))
    _rs_probe D14 1 `sch' : plotregion(lstyle(none) lwidth(thick))
    _rs_probe D15 1 `sch' : plotregion(lc(red) lw(thick) lp(dash))
    _rs_probe D16 1 `sch' : plotregion(fcolor(red%50))
    _rs_probe D17 1 `sch' : plotregion(lcolor(red%50) lwidth(thick))
    _rs_probe D18 1 `sch' : plotregion(fcolor(none))
    _rs_probe D19 1 `sch' : plotregion(color(none))
    _rs_probe D20 1 `sch' : plotregion(lcolor(none))
    _rs_probe D21 1 `sch' : graphregion(color(red))
    _rs_probe D22 1 `sch' : graphregion(fc(red))
    _rs_probe D23 1 `sch' : graphregion(lcolor(red) lwidth(thick))
    _rs_probe D24 1 `sch' : graphregion(lwidth(thick))
    _rs_probe D25 1 `sch' : graphregion(color(none))
    _rs_probe D26 1 `sch' : bgcolor(red)
    _rs_probe D27 1 `sch' : bgcolor(red) graphregion(color(none)) plotregion(fcolor(none))
    _rs_probe D28 1 `sch' : graphregion(fcolor(red%50)) bgcolor(blue)
    _rs_probe D29 1 `sch' : bgcolor(none)
    _rs_probe D30 1 `sch' : plotregion(style(foreground))
    _rs_probe D31 1 `sch' : plotregion(lstyle(foreground))
    _rs_probe D32 1 `sch' : plotregion(lstyle(p3))
    _rs_probe D33 1 `sch' : plotregion(style(bogus))
    _rs_probe D34 1 `sch' : plotregion(lpattern(bogus))
    _rs_probe D35 1 `sch' : plotregion(lcolor(notacolour))
    _rs_probe D36 1 `sch' : plotregion(lalign(inside) lwidth(vthick))
    _rs_probe D37 1 `sch' : plotregion(ifcolor(red))
    _rs_probe D38 1 `sch' : graphregion(ifcolor(red))
    _rs_probe D39 1 `sch' : plotregion(intensity(50) fcolor(red))
    _rs_probe D40 1 `sch' : bgcolor(none) graphregion(color(none))
    _rs_probe D41 1 `sch' : graphregion(lpattern(dash) lcolor(red))
    _rs_probe D42 1 `sch' : plotregion(lw(*2))
    _rs_probe D43 1 `sch' : graphregion(fcolor(red%50))
}

* ---- M: repeated copies, each editing the last ------------------------------
_rs_probe M01 1 s2color : plotregion(color(red)) plotregion(lcolor(blue))
_rs_probe M02 1 s2color : plotregion(lcolor(blue)) plotregion(color(red))
_rs_probe M03 1 s2color : plotregion(color(red)) plotregion(c(blue))
_rs_probe M04 1 s2color : plotregion(fcolor(red)) plotregion(style(none))
_rs_probe M05 1 s2color : plotregion(lcolor(red)) plotregion(lstyle(none))
_rs_probe M06 1 s2color : plotregion(fcolor(blue)) plotregion(color(red))
_rs_probe M07 1 s2color : plotregion(color(red)) plotregion(fcolor(blue))
_rs_probe M08 1 s2color : plotregion(style(none)) plotregion(fcolor(red))
_rs_probe M09 1 s2color : graphregion(color(red)) graphregion(lcolor(blue))

* ---- B: by() with the outer regions (closeout residual) --------------------
_rs_probe B01 1 s2color : by(foreign) plotregion(fcolor(red)) graphregion(fcolor(blue))

file close ${ZR_REG}

python:
import json, os, re, sys
from sfi import Macro

def L(n):
    return Macro.getLocal(n)

repo = Macro.getGlobal("ZR_REPO")
pdir = Macro.getGlobal("ZR_PDIR")
sys.path.insert(0, os.path.join(repo, "scripts"))
import svg_truth

def log_lines(f):
    p = os.path.join(pdir, f + ".log")
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8", errors="replace") as fh:
        return [ln.rstrip("\n") for ln in fh]

def first_error(lines):
    """The first line twoway printed: inside the probe program nothing is
    echoed, so after the log's header it is the error message (capture
    noisily prints no r(#) line)."""
    start = 0
    for i, ln in enumerate(lines):
        if "opened on:" in ln:
            start = i + 1
            break
    for ln in lines[start:]:
        t = ln.strip()
        if not t or t.startswith(("(note:", "-", ".", ">")):
            continue
        if t.startswith(("name:", "log:", "log type:", "closed on:")):
            return ""
        return t
    return ""

def notes(lines):
    return [ln.strip() for ln in lines if ln.strip().startswith("(note:")]

def role(r):
    if r is None:
        return None
    out = {"fill": r["fill"], "fill_opacity": r["fill_opacity"],
           "stroke": r["stroke"], "width": r["stroke_width"],
           "opacity": r["stroke_opacity"], "dasharray": r["dasharray"]}
    return out

def edge_dashes(path, box):
    """The stroke and width of a dashed outline drawn as line segments on
    the edges of *box* (x, y, w, h; the fill rect, or the outline rect
    inset by half its width), or None."""
    doc = svg_truth.svg_document(path)
    x, y, w, h = box
    segs = [d for d in doc["hlines"]
            if (abs(d["y1"] - y) < 3.5 or abs(d["y1"] - (y + h)) < 3.5)
            and min(d["x1"], d["x2"]) >= x - 3.5
            and max(d["x1"], d["x2"]) <= x + w + 3.5]
    if len(segs) < 3:
        return None
    return {"stroke": segs[0]["stroke"], "width": segs[0]["width"],
            "opacity": None, "fill": "none", "fill_opacity": None,
            "dasharray": "segments"}

def roles(path):
    rects = svg_truth.svg_rects(path)
    out = {"canvas": None, "graph_fill": None, "graph_line": None,
           "plot_fill": None, "plot_line": None}
    if not rects:
        return out
    out["canvas"] = role(rects[0])
    graph = [r for r in rects[1:] if (r["x"] or 0) < 20]
    plot = [r for r in rects[1:] if (r["x"] or 0) >= 20][:2]
    for kind, rs in (("graph", graph), ("plot", plot)):
        for r in rs:
            if r["fill"] == "none":
                if out[kind + "_line"] is None:
                    out[kind + "_line"] = role(r)
            elif out[kind + "_fill"] is None:
                out[kind + "_fill"] = role(r)
        box = None
        anyr = rs[0] if rs else None
        if anyr is not None:
            box = (anyr["x"], anyr["y"], anyr["w"], anyr["h"])
            ln = out[kind + "_line"]
            if ln is None or (ln.get("opacity") == 0.0):
                d = edge_dashes(path, box)
                if d is not None:
                    out[kind + "_line"] = d
    return out

probes = {}
with open(os.path.join(pdir, "registry.txt"), encoding="utf-8") as fh:
    rows = [ln.rstrip("\n").split("\t") for ln in fh if ln.strip()]
for f, pid, sch, svg, rc, opts in rows:
    lines = log_lines(f)
    rec = {"cmd": ("twoway scatter mpg weight, " + opts).strip(),
           "rc": int(rc), "err": first_error(lines) if int(rc) else "",
           "notes": notes(lines), "scheme": sch}
    key = pid
    if svg == "1":
        p = os.path.join(pdir, f + ".svg")
        if int(rc) == 0 and os.path.exists(p):
            rec.update(roles(p))
            if pid == "B01":
                rec["twoway_draws_outer_graphregion"] = any(
                    r["fill"] == "#0000ff" for r in svg_truth.svg_rects(p))
        key = pid if pid.startswith(("M", "B")) else sch + "|" + pid
    probes[key] = rec

for name in os.listdir(pdir):
    os.remove(os.path.join(pdir, name))
os.rmdir(pdir)

doc = {
    "_meta": {"stata_version": L("stata_version"),
              "born_date": L("born_date"),
              "dash_commit": L("dash_commit").strip(),
              "extracted": L("extracted"),
              "units": "SVG 720 units per inch; 3960 x 2880",
              "source": "scripts/extract_region_truth.do"},
    "probes": probes,
}
path = os.path.join(repo, "test", "fixtures", "region_truth.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=1, sort_keys=True)
    fh.write("\n")
Macro.setGlobal("ZR_N", str(len(probes)))
end
display as text "region_truth: wrote ${ZR_N} probes"
