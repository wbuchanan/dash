*! extract_region_remainder_truth.do
*! WP-31 section 37 (D11): ground truth for graphregion(margin()), the
*! regions' intensity() and shadestyle(), the graph region's inner-box
*! options and marginonly, the schemes' `shadestyle plotregion' stub and
*! the margin style names twoway refuses, for
*! test/fixtures/region_remainder_truth.json.
*!
*! WHY THIS EXISTS
*!
*! dash named graphregion(margin()), intensity(), shadestyle(), the inner
*! options and marginonly as ignored, and filled s1color's plot region
*! white, where Stata's scheme-s1color.scheme says `shadestyle plotregion
*! none'.  This script records what twoway (StataNow 19.5) draws:
*!   gmargin   graphregion(margin(<form>)): every rect, the plot box gaps
*!   refusals  plotregion(margin(<name>)) for allsides-ms and every
*!             style/margin-*.style basename: rc and first error line
*!   intensity plotregion()/graphregion() intensity(): the region fills
*!   shade     shadestyle(<word>) on either region: the fills, rc, line
*!   inner     graphregion()'s inner-box options and marginonly: every rect
*!   s1        the s1 family and s2color: every rect, and the stub text
*! Every rect is recorded in document order through scripts/svg_truth.py
*! (svg_rects); the canvas is the first.
*!
*! Run (never the GUI; the slot wrapper):
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_region_remainder_truth.do
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
    display as error "extract_region_remainder_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_region_remainder_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1
global ZR_REPO "`repo'"
global ZR_BASE "`c(sysdir_base)'"

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
local pdir "`pdir'/region_remainder_probes"
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

* ---- _rr_probe id svg scheme : options -------------------------------------
* Runs twoway scatter mpg weight, <options> scheme(<scheme>) under capture
* noisily inside a named log; exports the SVG when svg is 1 and rc is 0.
capture program drop _rr_probe
program define _rr_probe
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
    capture log close rr_probe
    quietly log using "${ZR_PDIR}/`f'.log", text replace name(rr_probe)
    capture noisily twoway scatter mpg weight, `macval(opts)' scheme(`sch') `nd'
    local rc = _rc
    quietly log close rr_probe
    if `rc' == 0 & `svg' {
        quietly graph export "${ZR_PDIR}/`f'.svg", as(svg) replace
    }
    file write ${ZR_REG} `"`f'"' _tab `"`id'"' _tab `"`sch'"' _tab `"`svg'"' _tab `"`rc'"' _tab `"`macval(opts)'"' _n
end

sysuse auto, clear

* ---- gmargin: graphregion(margin()) ----------------------------------------
_rr_probe gmargin.stub 1 s2color :
foreach m in zero small medium large vlarge sides top_bottom left tiny 10-pt {
    _rr_probe gmargin.`m' 1 s2color : graphregion(margin(`m'))
}
_rr_probe gmargin.l+5 1 s2color : graphregion(margin(l+5))
_rr_probe gmargin.l+5_r+5 1 s2color : graphregion(margin(l+5 r+5))
_rr_probe gmargin.t=0 1 s2color : graphregion(margin(t=0))
_rr_probe gmargin.1_2_3 1 s2color : graphregion(margin(1 2 3))
_rr_probe gmargin.1_2_3_4_5 1 s2color : graphregion(margin(1 2 3 4 5))
_rr_probe gmargin.L+10 1 s2color : graphregion(margin(L+10))
_rr_probe gmargin.large_xsize 1 s2color : graphregion(margin(large)) xsize(8) ysize(4)
_rr_probe gmargin.twice 1 s2color : graphregion(margin(l+5)) graphregion(margin(l+5))

* ---- refusals: plotregion(margin(<name>)) ----------------------------------
local _sty : dir "`c(sysdir_base)'style" files "margin-*.style"
foreach f of local _sty {
    local nm = substr("`f'", 8, strlen("`f'") - 13)
    _rr_probe refusals.`nm' 0 s2color : plotregion(margin(`nm'))
    _rr_probe grefusals.`nm' 0 s2color : graphregion(margin(`nm'))
}

* ---- intensity ---------------------------------------------------------------
foreach i in inten0 inten50 inten80 full *.5 50 bogus {
    local k = subinstr(subinstr("`i'", "*", "star", .), ".", "", .)
    _rr_probe intensity.`k'.plot 1 s2color : plotregion(fcolor(navy) intensity(`i'))
    _rr_probe intensity.`k'.graph 1 s2color : graphregion(fcolor(navy) intensity(`i'))
}
_rr_probe intensity.inten50.plot_scheme 1 s2color : plotregion(intensity(inten50))
_rr_probe intensity.inten80.graph_scheme 1 s2color : graphregion(intensity(inten80))
_rr_probe intensity.both 1 s2color : plotregion(intensity(inten50)) graphregion(intensity(inten80))

* ---- shadestyle ----------------------------------------------------------------
foreach w in none foreground background plotregion ci pattern10 solid bogus {
    _rr_probe shade.`w'.plot 1 s2color : plotregion(shadestyle(`w'))
    _rr_probe shade.`w'.graph 1 s2color : graphregion(shadestyle(`w'))
}
_rr_probe shade.none_fcolor.plot 1 s2color : plotregion(shadestyle(none) fcolor(red))
_rr_probe shade.fg_inten50.plot 1 s2color : plotregion(shadestyle(foreground) intensity(inten50))
_rr_probe shade.plotregion.s1color 1 s1color : plotregion(shadestyle(plotregion))
_rr_probe shade.background.s1color 1 s1color : plotregion(shadestyle(background))

* ---- inner: graphregion's inner box --------------------------------------------
_rr_probe inner.ifcolor 1 s2color : graphregion(ifcolor(red))
_rr_probe inner.icolor 1 s2color : graphregion(icolor(red))
_rr_probe inner.ilcolor 1 s2color : graphregion(ilcolor(blue))
_rr_probe inner.ilwidth 1 s2color : graphregion(ilwidth(thick))
_rr_probe inner.istyle_none 1 s2color : graphregion(istyle(none))
_rr_probe inner.marginonly 1 s2color : graphregion(fcolor(red) marginonly)
_rr_probe inner.marginonly_m 1 s2color : graphregion(fcolor(red) margin(large) marginonly)
_rr_probe inner.iintensity 1 s2color : graphregion(ifcolor(red) iintensity(inten50))
_rr_probe inner.ishade_none 1 s2color : graphregion(ifcolor(red) ishadestyle(none))
_rr_probe inner.ifcolor_ilcolor 1 s2color : graphregion(ifcolor(red) ilcolor(blue))
_rr_probe inner.lalign 1 s2color : graphregion(lalign(inside) lwidth(vthick) lcolor(red))
_rr_probe inner.p_marginonly 1 s2color : plotregion(fcolor(red) marginonly)

* ---- s1: the schemes' plot region ------------------------------------------------
foreach s in s1color s1mono s1rcolor s1manual stmono1 s2color {
    _rr_probe s1.`s' 1 `s' :
}
_rr_probe s1.override 1 s1color : plotregion(fcolor(yellow))
_rr_probe s1.red_graph 1 s1color : graphregion(fcolor(red))
_rr_probe s1.red_graph_s1mono 1 s1mono : graphregion(fcolor(red))
_rr_probe s1.red_graph_s2color 1 s2color : graphregion(fcolor(red))

file close ${ZR_REG}

python:
import json, os, re, sys
from sfi import Macro

def L(n):
    return Macro.getLocal(n)

repo = Macro.getGlobal("ZR_REPO")
pdir = Macro.getGlobal("ZR_PDIR")
base = Macro.getGlobal("ZR_BASE")
sys.path.insert(0, os.path.join(repo, "scripts"))
import svg_truth

def log_lines(f):
    p = os.path.join(pdir, f + ".log")
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8", errors="replace") as fh:
        return [ln.rstrip("\n") for ln in fh]

def first_error(lines):
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

def rnd(v):
    return None if v is None else round(float(v), 2)

def rects(path):
    out = []
    for r in svg_truth.svg_rects(path):
        out.append({"x": rnd(r["x"]), "y": rnd(r["y"]), "w": rnd(r["w"]),
                    "h": rnd(r["h"]), "fill": r["fill"],
                    "fill_opacity": r["fill_opacity"], "stroke": r["stroke"],
                    "stroke_width": r["stroke_width"]})
    return out

def plot_box(path):
    """The plot region's box: the axis lines' hull is not used; the plot
    region is the last region rect drawn before the markers -- its outline
    rect inset by half its stroke -- read as the outline rect's centre
    line (x, y, w, h)."""
    rs = svg_truth.svg_rects(path)
    if len(rs) < 2:
        return None
    r = rs[-1]
    return {"x": rnd(r["x"]), "y": rnd(r["y"]), "w": rnd(r["w"]),
            "h": rnd(r["h"])}

def stub(scheme, key):
    """`<key>' as the scheme files' #include chain leaves it."""
    seen = set()
    def walk(name):
        if name in seen:
            return None
        seen.add(name)
        p = os.path.join(base, "s", "scheme-" + name + ".scheme")
        if not os.path.exists(p):
            return None
        val = None
        with open(p, encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                t = ln.split()
                if len(t) >= 2 and t[0] == "#include":
                    v = walk(t[1])
                    if v is not None:
                        val = v
                elif len(t) >= 3 and (t[0] + " " + t[1]) == key:
                    val = t[2]
        return val
    return walk(scheme)

probes = {}
with open(os.path.join(pdir, "registry.txt"), encoding="utf-8") as fh:
    rows = [ln.rstrip("\n").split("\t") for ln in fh if ln.strip()]
for f, pid, sch, svg, rc, opts in rows:
    lines = log_lines(f)
    rec = {"cmd": ("twoway scatter mpg weight, " + opts).strip(),
           "rc": int(rc), "err": first_error(lines) if int(rc) else "",
           "notes": notes(lines), "scheme": sch}
    if svg == "1":
        p = os.path.join(pdir, f + ".svg")
        if int(rc) == 0 and os.path.exists(p):
            rs = rects(p)
            rec["rects"] = rs
            rec["plot_box"] = plot_box(p)
            c = rs[0] if rs else None
            pb = rec["plot_box"]
            if c and pb:
                rec["canvas"] = {"w": c["w"], "h": c["h"]}
                rec["gaps"] = {"left": rnd(pb["x"] - c["x"]),
                               "right": rnd(c["x"] + c["w"] - pb["x"] - pb["w"]),
                               "top": rnd(pb["y"] - c["y"]),
                               "bottom": rnd(c["y"] + c["h"] - pb["y"] - pb["h"])}
    if pid.startswith("s1."):
        rec["stub_shadestyle_plotregion"] = stub(sch, "shadestyle plotregion")
    if pid == "gmargin.stub":
        rec["stub_margin_graph"] = stub(sch, "margin graph")
    probes[pid] = rec

for name in os.listdir(pdir):
    os.remove(os.path.join(pdir, name))
os.rmdir(pdir)

doc = {
    "_meta": {"stata_version": L("stata_version"),
              "born_date": L("born_date"),
              "dash_commit": L("dash_commit").strip(),
              "extracted": L("extracted"),
              "units": "SVG 720 units per inch; 3960 x 2880 at 5.5 x 4",
              "source": "scripts/extract_region_remainder_truth.do"},
    "probes": probes,
}
path = os.path.join(repo, "test", "fixtures", "region_remainder_truth.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=1, sort_keys=True)
    fh.write("\n")
Macro.setGlobal("ZR_N", str(len(probes)))
end
display as text "region_remainder_truth: wrote ${ZR_N} probes"
