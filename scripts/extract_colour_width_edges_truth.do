*! extract_colour_width_edges_truth.do
*! WP-31 S41 (E4, E5, E7, E8, E13, C4b, C17b): twoway's colour, width and
*! outline edges.
*!
*! Per probe: the return code, the log's error or note text, and a
*! summary of the exported SVG's drawn elements -- each distinct
*! (tag, fill, stroke, stroke-width, stroke-dasharray, fill-opacity,
*! stroke-opacity, clip) with its count, in document order of first use.
*! The trailing python: block reads the records into
*! test/fixtures/colour_width_edges_truth.json, never calls Stata and
*! starts no subprocess.
*!
*! Run (Stata only through the slot wrapper, never the GUI):
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> \
*!       <repo>/scripts/extract_colour_width_edges_truth.do

* Root: DASH_REPO, else the current directory when it is a dash tree.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_colour_width_edges_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_colour_width_edges_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1

clear all
set more off
set linesize 255
version 19
set graphics off
set scheme s2color

global CW_REPO "`repo'"
local work "`c(tmpdir)'dash_colour_width_probe"
capture mkdir "`work'"
global CW_PDIR "`work'"
global CW_SEQ 0

local stata_version = c(stata_version)
local born_date "`c(born_date)'"
local extracted "`c(current_date)'"
tempfile cwgit
quietly shell git -C "${CW_REPO}" rev-parse HEAD > "`cwgit'"
tempname cwgh
file open `cwgh' using "`cwgit'", read text
file read `cwgh' cwline
file close `cwgh'
local dash_commit = trim(`"`cwline'"')

tempname reg
file open `reg' using "${CW_PDIR}/registry.txt", write text replace
global CW_REG `reg'

* ---- _cw_probe key command ---------------------------------------------
capture program drop _cw_probe
program define _cw_probe
    version 19
    gettoken key 0 : 0
    local command = strtrim(`"`macval(0)'"')
    graph drop _all
    global CW_SEQ = ${CW_SEQ} + 1
    local id "p${CW_SEQ}"
    capture log close cw_probe
    log using "${CW_PDIR}/`id'.log", text replace name(cw_probe)
    capture noisily `command'
    local rc = _rc
    log close cw_probe
    if `rc' == 0 {
        graph export "${CW_PDIR}/`id'.svg", as(svg) replace
    }
    file write ${CW_REG} `"`id'"' _tab `"`key'"' _tab `"`rc'"' _n
    file write ${CW_REG} "cmd" _tab `"`key'"' _tab `"`macval(command)'"' _n
end

* ---- _cw_scheme name body... : a scheme file in the current directory
capture program drop _cw_scheme
program define _cw_scheme
    version 19
    gettoken name 0 : 0
    tempname us
    file open `us' using "scheme-`name'.scheme", write text replace
    file write `us' "#include s2color" _n
    while `"`macval(0)'"' != "" {
        gettoken line 0 : 0
        file write `us' `"`macval(line)'"' _n
    }
    file close `us'
end

sysuse auto, clear

* sl.*: stylelist edge forms (E4)
_cw_probe sl.eq_glued     twoway scatter mpg weight turn, mcolor(red=blue)
_cw_probe sl.eq_trail     twoway scatter mpg weight turn, mcolor(red=)
_cw_probe sl.paren        twoway scatter mpg weight turn, mcolor((red))
_cw_probe sl.msym_unknown twoway scatter mpg weight turn, msymbol(bogus circle)
_cw_probe sl.msym_unknown2 twoway scatter mpg weight turn, msymbol(circle bogus)
_cw_probe sl.quoted_comma twoway scatter mpg weight, mcolor("red",blue)

* sc.<host>.<subopt>: a comma colour inside a structured option (E5)
_cw_probe sc.title.color         twoway scatter mpg weight, title("T", color("1,2,3"))
_cw_probe sc.subtitle.color      twoway scatter mpg weight, subtitle("T", color("1,2,3"))
_cw_probe sc.note.color          twoway scatter mpg weight, note("T", color("1,2,3"))
_cw_probe sc.caption.color       twoway scatter mpg weight, caption("T", color("1,2,3"))
_cw_probe sc.xline.lcolor        twoway scatter mpg weight, xline(3000, lcolor("1,2,3"))
_cw_probe sc.yline.lcolor        twoway scatter mpg weight, yline(20, lcolor("1,2,3"))
_cw_probe sc.xlabel.labcolor     twoway scatter mpg weight, xlabel(, labcolor("1,2,3"))
_cw_probe sc.ylabel.labcolor     twoway scatter mpg weight, ylabel(, labcolor("1,2,3"))
_cw_probe sc.plotregion.color    twoway scatter mpg weight, plotregion(color("1,2,3"))
_cw_probe sc.plotregion.lcolor   twoway scatter mpg weight, plotregion(lcolor("1,2,3"))
_cw_probe sc.graphregion.color   twoway scatter mpg weight, graphregion(color("1,2,3"))
_cw_probe sc.graphregion.lcolor  twoway scatter mpg weight, graphregion(lcolor("1,2,3"))
_cw_probe sc.legend.color        twoway scatter mpg weight turn, legend(color("1,2,3"))
* the same colours written without the comma, for the drawn colour
_cw_probe sp.title.color         twoway scatter mpg weight, title("T", color("1 2 3"))
_cw_probe sp.plotregion.color    twoway scatter mpg weight, plotregion(color("1 2 3"))

* lw.*: the width multiplier against the 0.3 pt floor (E5, D-41d)
_cw_scheme u41w "linewidth p vvthin" "linewidth p1 vvthin" "linewidth p1line vvthin" "linewidth plineplot vvthin" "linewidth p1lineplot vvthin"
_cw_probe lw.vvthin          twoway line mpg weight, sort lwidth(vvthin)
_cw_probe lw.scheme_vvthin   twoway line mpg weight, sort scheme(u41w)
_cw_probe lw.vvthin_x10      twoway line mpg weight, sort scheme(u41w) lwidth(*10)
_cw_probe lw.vvthin_x2       twoway line mpg weight, sort scheme(u41w) lwidth(*2)
_cw_probe lw.medium          twoway line mpg weight, sort lwidth(medium)
_cw_probe lw.medium_x2       twoway line mpg weight, sort lwidth(*2)
_cw_probe lw.medium_x0_5     twoway line mpg weight, sort lwidth(*.5)
_cw_probe lw.medium_x10      twoway line mpg weight, sort lwidth(*10)
capture erase "scheme-u41w.scheme"

* ol.*: rarea and rbar outlines (E8)
_cw_probe ol.rarea        twoway rarea mpg trunk weight, sort
_cw_probe ol.rbar         twoway rbar mpg trunk weight
_cw_probe ol.line_medium  twoway line mpg weight, sort lwidth(medium)
_cw_probe ol.rarea_p2     twoway rarea mpg trunk weight, sort pstyle(p2)
_cw_probe ol.rbar_p2      twoway rbar mpg trunk weight, pstyle(p2)
_cw_probe ol.rarea_stcolor twoway rarea mpg trunk weight, sort scheme(stcolor)
_cw_probe ol.rbar_stcolor  twoway rbar mpg trunk weight, scheme(stcolor)

* ci.*: a CI band's intensity above full (E7)
_cw_scheme u41i "intensity p1bar inten200"
_cw_probe ci.base     twoway lfitci mpg weight, pstyle(p1)
_cw_probe ci.inten200 twoway lfitci mpg weight, pstyle(p1) scheme(u41i)
_cw_probe ci.inten200_default twoway lfitci mpg weight, scheme(u41i)
capture erase "scheme-u41i.scheme"
* the band's intensity is shadestyle p#'s chain, p#shade -> pshade -> p# -> p
_cw_scheme u41j "intensity p1shade inten200"
_cw_probe ci.p1shade_inten200 twoway lfitci mpg weight, pstyle(p1) scheme(u41j)
_cw_probe ci.astyle_p1shade_inten200 twoway lfitci mpg weight, astyle(p1) scheme(u41j)
_cw_probe ci.rarea_p1shade_inten200 twoway rarea mpg trunk weight, sort pstyle(p1) scheme(u41j)
capture erase "scheme-u41j.scheme"
_cw_scheme u41k "intensity pshade inten50"
_cw_probe ci.pshade_inten50 twoway lfitci mpg weight, pstyle(p1) scheme(u41k)
capture erase "scheme-u41k.scheme"
_cw_scheme u41l "intensity p1 inten50" "intensity p1shade inten200"
_cw_probe ci.p1_inten50_p1shade_inten200 twoway lfitci mpg weight, pstyle(p1) scheme(u41l)
capture erase "scheme-u41l.scheme"
_cw_scheme u41m "intensity p inten200"
_cw_probe ci.p_inten200 twoway lfitci mpg weight, pstyle(p1) scheme(u41m)
capture erase "scheme-u41m.scheme"
* the band's colour: color p#other or color p#shade (recorded)
_cw_scheme u41n "color p1shade red"
_cw_probe ci.color_p1shade twoway lfitci mpg weight, pstyle(p1) scheme(u41n)
capture erase "scheme-u41n.scheme"
_cw_scheme u41o "color p1other red"
_cw_probe ci.color_p1other twoway lfitci mpg weight, pstyle(p1) scheme(u41o)
capture erase "scheme-u41o.scheme"

* hist.*: a scheme's %NN on color histogram (E13)
_cw_scheme u41h `"color histogram "202 194 126%40""'
_cw_probe hist.pct  twoway histogram mpg, scheme(u41h)
_cw_probe hist.base twoway histogram mpg
capture erase "scheme-u41h.scheme"

* unclear.*: recorded only (D-41c)
_cw_probe unclear.navy52 twoway scatter mpg weight, mcolor(navy*52)
_cw_probe unclear.fgbg   twoway scatter mpg weight turn, mcolor(bg fg)

* c4b.<scheme>.<view>: fitplot() and ciplot() colours (C4b)
foreach s in s2color stcolor {
    _cw_probe c4b.`s'.default  twoway lfitci mpg weight, scheme(`s')
    _cw_probe c4b.`s'.fitplot_scatter twoway lfitci mpg weight, fitplot(scatter) scheme(`s')
    _cw_probe c4b.`s'.ciplot_rline twoway lfitci mpg weight, ciplot(rline) scheme(`s')
    _cw_probe c4b.`s'.ciplot_rcap  twoway lfitci mpg weight, ciplot(rcap) scheme(`s')
    _cw_probe c4b.`s'.ciplot_rarea twoway lfitci mpg weight, ciplot(rarea) scheme(`s')
    foreach t in rbar rspike rcapsym rscatter rconnected scatter line connected area bar spike dropline dot {
        _cw_probe c4b.`s'.ciplot_`t' twoway lfitci mpg weight, ciplot(`t') scheme(`s')
    }
}

* lal.*: which abbreviations of lalign() twoway reads (C17b); outside,
* because inside is a line's default
foreach ab in l la lal lali lalig lalign lalp lalpha {
    _cw_probe lal.`ab' twoway line mpg weight, sort `ab'(outside)
    file write ${CW_REG} "setting" _tab "lal.`ab'" _tab "`.Graph.plotregion1.plot1.style.line.align.setting'" _n
}
foreach ab in la lal lali {
    _cw_probe lal.rarea_`ab' twoway rarea mpg trunk weight, sort `ab'(outside)
}

file close ${CW_REG}

python:
import json, os, re
import xml.etree.ElementTree as ET
from sfi import Macro

def L(n):
    return Macro.getLocal(n)

repo = Macro.getGlobal("CW_REPO")
pdir = Macro.getGlobal("CW_PDIR")
KEYS = ("fill", "stroke", "stroke-width", "stroke-dasharray",
        "fill-opacity", "stroke-opacity")

def style_of(el):
    out = {}
    for part in (el.get("style") or "").split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip().lower()] = v.strip().lower()
    for k in KEYS:
        if el.get(k) is not None and k not in out:
            out[k] = el.get(k).strip().lower()
    return out

def elements(path):
    """[tag, fill, stroke, stroke-width, dasharray, fill-opacity,
    stroke-opacity, clip, count] for each distinct drawn style, in order
    of first use; a polygon twoway writes once in <defs> is drawn by
    <use> elements, and "clip" marks a stroke clipped to its own shape
    (only its inner half shows)."""
    root = ET.parse(path).getroot()
    seen = {}
    order = []
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag not in ("line", "circle", "path", "polyline", "polygon",
                       "rect", "text", "ellipse", "use"):
            continue
        st = style_of(el)
        if not any(st.get(k) for k in KEYS):
            continue
        key = (tag,) + tuple(st.get(k, "") for k in KEYS) + (
            "clip" if el.get("clip-path") else "",)
        if key not in seen:
            seen[key] = 0
            order.append(key)
        seen[key] += 1
    return [list(k) + [seen[k]] for k in order]

def log_text(pid):
    p = os.path.join(pdir, pid + ".log")
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8", errors="replace") as fh:
        lines = [ln.rstrip() for ln in fh]
    keep = []
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith(". ") or s.startswith("> ") or \
                s.startswith("name:") or s.startswith("log:") or \
                s.startswith("log type:") or s.startswith("opened on:") or \
                s.startswith("closed on:") or set(s) <= set("-"):
            continue
        if s.startswith("r(") and s.endswith(");"):
            continue
        keep.append(s)
    return " ".join(keep)[:600]

with open(os.path.join(pdir, "registry.txt"), encoding="utf-8") as fh:
    rows = [ln.rstrip("\n").split("\t", 2) for ln in fh if ln.strip()]
cmds = {r[1]: r[2] for r in rows if r[0] == "cmd"}
settings = {r[1]: r[2] for r in rows if r[0] == "setting"}
out = {}
for pid, key, rc in [r for r in rows if r[0] not in ("cmd", "setting")]:
    rc = int(rc)
    svg = os.path.join(pdir, pid + ".svg")
    rec = {"rc": rc, "text": log_text(pid), "cmd": cmds.get(key, "")}
    if rc == 0 and os.path.exists(svg):
        rec["elements"] = elements(svg)
    if key in settings:
        rec["setting"] = settings[key]
    out[key] = rec

for f in os.listdir(pdir):
    os.remove(os.path.join(pdir, f))
os.rmdir(pdir)

out["_meta"] = {"stata_version": L("stata_version"),
                "born_date": L("born_date"),
                "dash_commit": L("dash_commit").strip(),
                "extracted": L("extracted"),
                "units": "stroke-width in the units of twoway's exported SVG (its viewBox); elements: [tag, fill, stroke, stroke-width, stroke-dasharray, fill-opacity, stroke-opacity, clip, count]; a clipped stroke shows only its inner half",
                "source": "scripts/extract_colour_width_edges_truth.do"}
path = os.path.join(repo, "test", "fixtures", "colour_width_edges_truth.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
Macro.setGlobal("CW_N", str(len(out) - 1))
end
display as text "colour_width_edges_truth: wrote ${CW_N} records"
