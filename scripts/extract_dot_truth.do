*! extract_dot_truth.do -- WP-31 section 18 (B5b): measure the rows of dots
*! twoway dot draws -- how many per observation, along which axis, from
*! which base, how far, in which style -- and what it does with ndots(),
*! dotextend(), horizontal, the d-options, dstyle(), colorvar() and the
*! spellings it refuses, so dash's dot rows are proved against twoway.
*!
*! Output: test/fixtures/dot_truth.json
*!
*! Run through the slot wrapper only (CLAUDE.md rule 10):
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_dot_truth.do
*!
*! METHOD.  sysuse auto, scheme s2color unless a probe names another.
*! twoway only: dash is never run.  Per graph: the plot's class values
*! (.num_dots, .dots_extend.istrue, .bar_drop_to.stylename), both scales'
*! curmin/curmax, and from the SVG every circle (centre, radius, fill,
*! stroke, stroke width).  The dots are the circles of the smallest radius;
*! they are grouped into runs by the coordinate they share (cx for a
*! vertical plot, cy under horizontal).  Refusals: rc and the error line,
*! from a log.  The git commit is read from a file `shell' wrote, never
*! with shell=True.  Every SVG is erased.

clear all
set more off
set linesize 200

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zd_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zd_bad' {
    display as error "extract_dot_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zd_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zd_rc' | _rc {
    local _zd_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_dot_truth.do: `_zd_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZD_REPO "`repo'"
global ZD_OUT "${ZD_REPO}/test/fixtures/dot_truth.json"
global dash_nobrowser 1

local work "`c(tmpdir)'dash_dot_probe"
capture mkdir "`work'"
global ZD_WORK "`work'"

if `"`c(python_exec)'"' == "" {
    display as error "extract_dot_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

quietly shell git -C "${ZD_REPO}" rev-parse HEAD > "${ZD_WORK}/git_head.txt"
global ZD_VERSION "`c(stata_version)'"
global ZD_BORN "`c(born_date)'"
global ZD_WHEN "`c(current_date)' `c(current_time)'"

sysuse auto, clear
set scheme s2color

* Graphs: key | command.  Class values and the SVG of each.
global ZD_GRAPHS ""
local G1 "D01|twoway dot mpg weight in 1/5"
local G2 "D02|twoway dot mpg weight in 1/5, dotextend(no)"
local G3 "D03|twoway dot mpg weight in 1/5, ndots(10)"
local G4 "D06|twoway dot mpg weight in 1/5, horizontal"
local G5 "D07|twoway dot mpg weight in 1/5, dcolor(red) dsize(medium) dlcolor(blue) dlwidth(thick) dsymbol(square)"
local G6 "D08|twoway dot mpg weight in 1/5, dstyle(p3)"
local G7 "D08b|twoway dot mpg weight in 1/5, dstyle(p7)"
local G8 "D09|twoway dot mpg weight in 1/5, colorvar(rep78) colordiscrete"
local G9 "D10|twoway dot mpg weight in 1/5, base(50)"
local G10 "D12|twoway dot mpg weight in 1/5, dsize(medium)"
local G11 "D13|twoway scatter mpg weight in 1/5"
local G12 "D14|twoway dot mpg weight in 1/5, dcolor(red)"
local G13 "D15|twoway dot mpg weight in 1/5, dfcolor(red)"
local G14 "D16|twoway dot mpg weight in 1/5, dotextend(no) horizontal"
local G15 "D17|twoway dot mpg weight in 1/5, ndots(2)"
local G16 "D18|twoway dot mpg weight in 1/5, scheme(s1rcolor)"
local G17 "D19|twoway dot mpg weight in 1/5, dlwidth(thin)"
local G18 "D20|twoway dot mpg weight in 1/5, dlwidth(none) dsize(large)"
local G19 "D21|twoway dot price mpg in 1/5"
local G20 "D22|twoway dot mpg weight in 1/5, ndots(10) dotextend(no)"
local G21 "D23|twoway dot mpg weight in 1/5, color(red)"
local G22 "D24|twoway dot mpg weight in 1/5, mcolor(red) msymbol(diamond) mlwidth(thick) msize(large)"
local G23 "D25|twoway dot mpg weight in 1/5, pstyle(p3)"
local G24 "D26|twoway dot mpg weight in 1/5, mstyle(p3) mlstyle(p3)"
local G25 "D27|twoway dot mpg weight in 1/5, p(p3) dcolor(red)"
local G26 "D28|twoway dot mpg weight in 1/5, baroffset(.5)"
local G27 "D29|twoway dot mpg weight in 1/5, baroffset(5)"
local G28 "D30|twoway dot mpg weight in 1/5, dlalign(outside)"
forvalues k = 1/28 {
    gettoken key rest : G`k', parse("|")
    gettoken bar cmd : rest, parse("|")
    local opt = cond(strpos(`"`cmd'"', ","), " ", ", ")
    quietly `cmd' `opt' name(zd, replace)
    global ZDG_`key'_cls "`.zd.plotregion1.plot1.num_dots' `.zd.plotregion1.plot1.dots_extend.istrue' `.zd.plotregion1.plot1.bar_drop_to.stylename'"
    global ZDG_`key'_sc "`.zd.plotregion1.yscale.curmin' `.zd.plotregion1.yscale.curmax' `.zd.plotregion1.xscale.curmin' `.zd.plotregion1.xscale.curmax'"
    quietly graph export "${ZD_WORK}/g_`key'.svg", replace
    global ZD_GRAPHS "${ZD_GRAPHS} `key'"
}
graph drop _all
set scheme s2color

* The rc and error line of each probe.
global ZD_PROBES ""
quietly log using "${ZD_WORK}/probes.log", text replace name(zdlog)
local P1 "D04|twoway dot mpg weight in 1/5, ndots(1)"
local P2 "D04b|twoway dot mpg weight in 1/5, ndots(0)"
local P3 "D04c|twoway dot mpg weight in 1/5, ndots(2.5)"
local P4 "D04d|twoway dot mpg weight in 1/5, ndots(-3)"
local P5 "D04e|twoway dot mpg weight in 1/5, ndots(20000)"
local P6 "D05|twoway dot mpg weight in 1/5, dotextend(0)"
local P7 "D05b|twoway dot mpg weight in 1/5, dotextend(y)"
local P8 "D05c|twoway dot mpg weight in 1/5, dotextend(maybe)"
local P9 "D05d|twoway dot mpg weight in 1/5, dotextend(n)"
local P10 "D05e|twoway dot mpg weight in 1/5, dotextend(1)"
local P11 "D05f|twoway dot mpg weight in 1/5, dotextend(YES)"
local P12 "D11|twoway dot mpg weight in 1/5, dlalign(outside)"
local P13 "D11b|twoway dot mpg weight in 1/5, dlalign(x)"
local P14 "D11c|twoway scatter mpg weight in 1/5, dlalign(outside)"
local P15 "D11d|twoway scatter mpg weight in 1/5, ndots(10)"
local P16 "D11e|twoway dot mpg weight in 1/5, dsize(bogus)"
local P17 "D11f|twoway dot mpg weight in 1/5, dcolor(bogus)"
local P18 "D11g|twoway dot mpg weight in 1/5, ndots(x)"
local P19 "D11h|twoway dot mpg weight in 1/5, dsymbol(bogus)"
local P20 "D11i|twoway dot mpg weight in 1/5, dotextend()"
local P21 "D11j|twoway dot mpg weight in 1/5, dlwidth(bogus)"
local P22 "D11k|twoway scatter mpg weight in 1/5, dstyle(p3)"
local P23 "D11l|twoway line mpg weight in 1/5, dotextend(no)"
local P24 "D11m|twoway dot mpg weight in 1/5, dotex(no) ndot(4) d(square) dc(red) dfc(blue) dsiz(small) dlc(green) dlw(thin) dla(inside) dsty(p2) dlsty(p3)"
local P25 "D05g|twoway dot mpg weight in 1/5, dotextend(NO)"
local P26 "D05h|twoway dot mpg weight in 1/5, dotextend(N)"
local P27 "D05i|twoway dot mpg weight in 1/5, dotextend(off)"
local P28 "D05j|twoway dot mpg weight in 1/5, dotextend(false)"
local P29 "D11n|twoway line mpg weight in 1/5, dstyle(p3) dlstyle(p3) dsymbol(square) dcolor(red) dfcolor(red) dsize(small) dlcolor(red) dlwidth(thin) dlalign(inside)"
local P30 "D11o|twoway bar mpg weight in 1/5, dstyle(p3) dlstyle(p3) dsymbol(square) dcolor(red) dfcolor(red) dsize(small) dlcolor(red) dlwidth(thin) dlalign(inside)"
local P31 "D11p|twoway rcap mpg turn weight in 1/5, dstyle(p3) dlstyle(p3) dsymbol(square) dcolor(red) dfcolor(red) dsize(small) dlcolor(red) dlwidth(thin) dlalign(inside)"
local P32 "D11q|twoway lfit mpg weight in 1/5, dstyle(p3) dlstyle(p3) dsymbol(square) dcolor(red) dfcolor(red) dsize(small) dlcolor(red) dlwidth(thin) dlalign(inside)"
local P33 "D11r|twoway histogram mpg in 1/5, dstyle(p3) dlstyle(p3) dsymbol(square) dcolor(red) dfcolor(red) dsize(small) dlcolor(red) dlwidth(thin) dlalign(inside)"
local P34 "D11s|twoway pci 1 1 2 2, dstyle(p3) dlstyle(p3) dsymbol(square) dcolor(red) dfcolor(red) dsize(small) dlcolor(red) dlwidth(thin) dlalign(inside)"
local P35 "D11t|twoway function y=x, dstyle(p3) dlstyle(p3) dsymbol(square) dcolor(red) dfcolor(red) dsize(small) dlcolor(red) dlwidth(thin) dlalign(inside)"
local P36 "D11u|twoway scatter mpg weight in 1/5, dotextend(no)"
local P37 "D11v|twoway dot mpg weight in 1/5, ndots(1e3)"
local P38 "D11w|twoway dot mpg weight in 1/5, ndots(10 20)"
local P39 "D11x|twoway dot mpg weight in 1/5, dotextend(yes no)"
forvalues k = 1/39 {
    gettoken key rest : P`k', parse("|")
    gettoken bar cmd : rest, parse("|")
    display "ZD-MARK `key'"
    capture noisily `cmd' name(zd, replace)
    global ZDP_`key'_rc = _rc
    if _rc == 0 {
        global ZDP_`key'_cls "`.zd.plotregion1.plot1.num_dots' `.zd.plotregion1.plot1.dots_extend.istrue'"
        quietly graph export "${ZD_WORK}/p_`key'.svg", replace
        graph drop zd
    }
    display "ZD-END `key'"
    global ZD_PROBES "${ZD_PROBES} `key'"
}
quietly log close zdlog

python:
import json, os, re, sys
from sfi import Macro

G = Macro.getGlobal
sys.path.insert(0, os.path.join(G("ZD_REPO"), "scripts"))
from svg_truth import svg_document  # noqa: E402

work = G("ZD_WORK")
written = []
_RE_C = re.compile(r'<circle ([^/>]*)/>')
_RE_SW = re.compile(r'stroke-width:([0-9.]+)')


def _num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def _shapes(path):
    """Every circle with its stroke width; the rects and paths that are
    small markers (a square dot is a rect or path, a triangle a path)."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        txt = fh.read()
    doc = svg_document(path)
    widths = []
    for m in _RE_C.finditer(txt):
        sw = _RE_SW.search(m.group(1))
        widths.append(float(sw.group(1)) if sw else None)
    circ = []
    for c, w in zip(doc["circles"], widths):
        d = dict(c)
        d["stroke_width"] = w
        circ.append(d)
    return doc, circ


def _runs(points, along):
    """Group *points* into runs by the coordinate they share (the other
    one varies): ``{shared: sorted positions}``."""
    key = "cx" if along == "y" else "cy"
    other = "cy" if along == "y" else "cx"
    runs = {}
    for p in points:
        runs.setdefault(round(p[key], 2), []).append(round(p[other], 3))
    return {str(k): sorted(v) for k, v in sorted(runs.items())}


graphs = {}
for key in G("ZD_GRAPHS").split():
    sp = os.path.join(work, "g_%s.svg" % key)
    written.append(sp)
    doc, circ = _shapes(sp)
    cls = (G("ZDG_%s_cls" % key) or "").split()
    cls += [None] * (3 - len(cls))
    sc = [_num(w) for w in (G("ZDG_%s_sc" % key) or "").split()]
    sc += [None] * (4 - len(sc))
    radii = sorted(set(round(c["r"], 3) for c in circ if c["r"] is not None))
    entry = {"num_dots": _num(cls[0]), "dots_extend": cls[1],
             "bar_drop_to": cls[2],
             "yscale": sc[0:2], "xscale": sc[2:4],
             "n_circles": len(circ), "radii": radii,
             "canvas": [doc["canvas"]["w"], doc["canvas"]["h"]],
             "plotregion": doc["plotregion"],
             "n_rects": len(doc["rects"]), "n_paths": len(doc["paths"])}
    along = "x" if cls[2] == "y" else "y"
    entry["along"] = along
    if radii:
        rmin = radii[0]
        dots = [c for c in circ if c["r"] is not None and round(c["r"], 3) == rmin]
        others = [c for c in circ if c["r"] is not None and round(c["r"], 3) != rmin]
        entry["dot_r"] = rmin
        entry["dot_fill"] = sorted(set(str(c["fill"]) for c in dots))
        entry["dot_stroke"] = sorted(set(str(c["stroke"]) for c in dots))
        entry["dot_stroke_width"] = sorted(set(c["stroke_width"] for c in dots if c["stroke_width"] is not None))
        entry["n_dots"] = len(dots)
        entry["dot_runs"] = _runs(dots, along)
        entry["marker_r"] = sorted(set(round(c["r"], 3) for c in others))
        entry["marker_fill"] = sorted(set(str(c["fill"]) for c in others))
        entry["marker_centres"] = sorted([round(c["cx"], 3), round(c["cy"], 3)] for c in others)
    # Small rects and paths (a square or triangle dsymbol()).
    smalls = [r for r in doc["rects"] if r.get("w") and r["w"] < 10]
    entry["small_rects"] = len(smalls)
    if smalls:
        entry["small_rect_w"] = sorted(set(round(r["w"], 3) for r in smalls))
        entry["small_rect_fill"] = sorted(set(str(r["fill"]) for r in smalls))
        entry["small_rect_stroke"] = sorted(set(str(r["stroke"]) for r in smalls))
    if doc["paths"]:
        entry["path_fill"] = sorted(set(str(q["fill"]) for q in doc["paths"]))
        entry["path_stroke"] = sorted(set(str(q["stroke"]) for q in doc["paths"]))
    graphs[key] = entry

with open(os.path.join(work, "probes.log"), encoding="utf-8",
          errors="replace") as fh:
    plog = fh.read().splitlines()
written.append(os.path.join(work, "probes.log"))
msgs, cur = {}, None
for ln in plog:
    s = ln.strip()
    m = re.match(r"^ZD-MARK (\S+)$", s)
    if m:
        cur = m.group(1)
        continue
    if re.match(r"^ZD-END ", s):
        cur = None
        continue
    if cur and cur not in msgs and s and not s.startswith(".") \
            and not s.startswith("r(") and not s.startswith("(note"):
        msgs[cur] = s
probes = {}
for key in G("ZD_PROBES").split():
    rc = int(G("ZDP_%s_rc" % key))
    entry = {"rc": rc, "message": msgs.get(key) if rc else None}
    sp = os.path.join(work, "p_%s.svg" % key)
    if rc == 0 and os.path.exists(sp):
        written.append(sp)
        cls = (G("ZDP_%s_cls" % key) or "").split()
        entry["class"] = cls
        doc, circ = _shapes(sp)
        entry["n_circles"] = len(circ)
    probes[key] = entry

try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
written.append(os.path.join(work, "git_head.txt"))
out = dict(graphs)
out["probes"] = probes
out["_meta"] = {"stata_version": G("ZD_VERSION"), "born_date": G("ZD_BORN"),
                "dash_commit": commit, "extracted": G("ZD_WHEN"),
                "source": "scripts/extract_dot_truth.do"}
with open(G("ZD_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
for p in written:
    try:
        os.remove(p)
    except OSError:
        pass
print("wrote", G("ZD_OUT"))
end
