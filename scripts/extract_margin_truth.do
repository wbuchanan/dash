*! extract_margin_truth.do
*! WP-30 S47 (P1.20b): twoway's plot-region margin and inner box --
*! plotregion(margin()) in every form the help documents, copies that
*! add, the named margin styles, by() panels, and the plotregion inner
*! sub-options (istyle icolor ifcolor ilstyle ilcolor ilwidth ilpattern)
*! -- measured from Stata.
*!
*! Output: test/fixtures/margin_truth.json
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_margin_truth.do
*!
*! Per probe: rc, the notes of its own log, .Graph.plotregion1.{x,y}scale
*! .{curmin,curmax} (per by() panel .Graph.graphs[k], with gmetric_mult),
*! and from the exported SVG (scripts/svg_truth.py) margin_rel on both
*! sides of each axis in visual order (lo = left or bottom, hi = right or
*! top): the distance from the plot-region edge to the scale's end over
*! min(canvas W, H).  An I* probe records the inner rect, the rect its
*! SVG draws that DEF's does not, in pixels and in data units through the
*! axis reading.  _meta carries the 28 margin-*.style files' four sides
*! and the margin ladder of s2color, stcolor and economist, read as text.
*! The python block reads files and locals only and calls no Stata; a
*! backtick in it is spelled \x60.

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_margin_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_margin_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1

clear all
set more off
set linesize 255
version 19
set graphics off

global MT_REPO "`repo'"
global MT_OUT "${MT_REPO}/test/fixtures/margin_truth.json"
global MT_BASE "`c(sysdir_base)'"
local work "`c(tmpdir)'dash_margin_probe"
capture mkdir "`work'"
global MT_WORK "`work'"
global MT_REC "`work'/mt_records.txt"

local stata_version = c(stata_version)
local born_date "`c(born_date)'"
local extracted "`c(current_date)'"
tempfile mtgit
quietly shell git -C "${MT_REPO}" rev-parse HEAD > "`mtgit'"
tempname mtgh
file open `mtgh' using "`mtgit'", read text
file read `mtgh' mtline
file close `mtgh'
local dash_commit = trim(`"`mtline'"')

capture program drop _mt_scales
program _mt_scales
    args id tag p
    local r "S|`id'|`tag'"
    foreach d in y x {
        local s "`p'.plotregion1.`d'scale"
        local a "`p'.`d'axis1"
        local r "`r'|``s'.curmin'|``s'.curmax'|``a'.major.min'|``a'.major.delta'|``a'.major.max'"
    }
    file write mtrec `"`r'"' _n
end

capture program drop _mt_rec
program _mt_rec
    // _mt_rec <id> <scheme> <data> `"<command>"'
    args id scheme data cmd
    sysuse auto, clear
    if "`data'" == "td" {
        quietly generate d = mdy(1, 1, 2000) + _n * 30
        format d %td
    }
    capture graph drop _all
    capture log close mt_probe
    quietly log using "${MT_WORK}/`id'.log", text replace name(mt_probe)
    capture noisily `cmd' scheme(`scheme')
    local rc = _rc
    capture log close mt_probe
    file write mtrec `"P|`id'|`scheme'|`data'|`rc'|`cmd'"' _n
    if `rc' == 0 {
        local n "`.Graph.graphs.arrnels'"
        if "`n'" == "" | "`n'" == "." local n 0
        if `n' > 0 {
            file write mtrec `"G|`id'|`.Graph.plotregion1.gmetric_mult'|`n'"' _n
            forvalues k = 1/`n' {
                _mt_scales `id' `k' ".Graph.graphs[`k']"
            }
        }
        else _mt_scales `id' 0 ".Graph"
        capture graph export "${MT_WORK}/`id'.svg", replace
    }
    capture graph drop _all
end

file open mtrec using "${MT_REC}", write text replace

local T "twoway scatter mpg weight,"
local P "plotregion"
_mt_rec DEF    s2color auto `"`T'"'
_mt_rec ZERO   s2color auto `"`T' `P'(margin(zero))"'
_mt_rec BOGUS  s2color auto `"`T' `P'(margin(bogus))"'
_mt_rec L10    s2color auto `"`T' `P'(margin(l+10))"'
_mt_rec LM5    s2color auto `"`T' `P'(margin(l-5))"'
_mt_rec LEQ0   s2color auto `"`T' `P'(margin(l=0))"'
_mt_rec LEQ10  s2color auto `"`T' `P'(margin(l=10))"'
_mt_rec L5     s2color auto `"`T' `P'(margin(l5))"'
_mt_rec L5L5   s2color auto `"`T' `P'(margin(l+5 l+5))"'
_mt_rec LSP    s2color auto `"`T' `P'(margin(l +10))"'
_mt_rec Q4     s2color auto `"`T' `P'(margin(1 2 3 4))"'
foreach n in 10-pt 2-pt 3-pt 4-pt allsides-ms bargraph bottom ebargraph esubhead horiz_bargraph large left medium medlarge medsmall right side-2-pt side-3-pt side-4-pt sides small tiny top top_bottom vlarge vside-2-pt vsmall zero {
    local id = "NM_" + subinstr("`n'", "-", "_", .)
    _mt_rec `id' s2color auto `"`T' `P'(margin(`n'))"'
}
_mt_rec COPY   s2color auto `"`T' `P'(margin(zero)) `P'(margin(l+10))"'
_mt_rec COPYR  s2color auto `"`T' `P'(margin(l+10)) `P'(margin(zero))"'
_mt_rec MIX    s2color auto `"`T' `P'(margin(zero) color(red)) `P'(mar(t+5))"'
_mt_rec XS     s2color auto `"`T' xsize(10) ysize(3) `P'(margin(l+10))"'
_mt_rec REV    s2color auto `"`T' xscale(reverse) `P'(margin(l+10))"'
_mt_rec LOG    s2color auto `"`T' yscale(log) `P'(margin(b+10))"'
_mt_rec TD     s2color td   `"twoway scatter mpg d, `P'(margin(r+10))"'
_mt_rec Y2     s2color auto `"twoway (scatter mpg weight) (scatter price weight, yaxis(2)), `P'(margin(t+10))"'
_mt_rec BY_DEF  s2color auto `"`T' by(foreign)"'
_mt_rec BY_L10  s2color auto `"`T' by(foreign) `P'(margin(l+10))"'
_mt_rec BY_ZERO s2color auto `"`T' by(foreign) `P'(margin(zero))"'
_mt_rec BY_B10  s2color auto `"`T' by(foreign) `P'(margin(b+10))"'
_mt_rec ECON_DEF economist auto `"`T'"'
_mt_rec ECON_L10 economist auto `"`T' `P'(margin(l+10))"'
_mt_rec ST_L10 stcolor auto `"`T' `P'(margin(l+10))"'
_mt_rec CAPL   s2color auto `"`T' `P'(margin(L+10))"'
_mt_rec Q3     s2color auto `"`T' `P'(margin(1 2 3))"'
_mt_rec Q5     s2color auto `"`T' `P'(margin(1 2 3 4 5))"'
_mt_rec I1     s2color auto `"`T' `P'(ifcolor(red))"'
_mt_rec I2     s2color auto `"`T' `P'(icolor(red))"'
_mt_rec I3     s2color auto `"`T' `P'(ilcolor(red) ilwidth(thick))"'
_mt_rec I4     s2color auto `"`T' `P'(ifcolor(red%50) ilpattern(dash))"'
_mt_rec I5     s2color auto `"`T' `P'(istyle(none) ifcolor(red))"'
_mt_rec I6     s2color auto `"`T' `P'(ifcolor(red) margin(zero))"'
_mt_rec I7     s2color auto `"`T' `P'(ifc(red) ilc(blue))"'
_mt_rec G1     s2color auto `"`T' graphregion(margin(l+10))"'
_mt_rec G2     s2color auto `"`T' graphregion(ifcolor(red))"'
file close mtrec

python:
import json, os, re, sys
from sfi import Macro

REPO = Macro.getGlobal("MT_REPO")
WORK = Macro.getGlobal("MT_WORK")
BASE = Macro.getGlobal("MT_BASE")
sys.path.insert(0, os.path.join(REPO, "scripts"))
import svg_truth


def num(s):
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None
    return v if v == v and abs(v) < 8.98e307 else None


probes, order = {}, []
with open(Macro.getGlobal("MT_REC"), encoding="utf-8", errors="replace") as fh:
    for line in fh:
        f = line.rstrip("\n").split("|")
        if f[0] == "P":
            pid = f[1]
            probes[pid] = {"scheme": f[2], "data": f[3], "rc": int(f[4]),
                           "cmd": "|".join(f[5:])}
            order.append(pid)
        elif f[0] == "G":
            probes[f[1]]["gmetric"] = num(f[2])
            probes[f[1]]["panels"] = []
        elif f[0] == "S":
            sc = {"y": {"cur": [num(f[3]), num(f[4])],
                        "major": [num(v) for v in f[5:8]]},
                  "x": {"cur": [num(f[8]), num(f[9])],
                        "major": [num(v) for v in f[10:13]]}}
            if f[2] == "0":
                probes[f[1]].update(sc)
            else:
                probes[f[1]]["panels"].append(sc)


def notes(pid):
    path = os.path.join(WORK, pid + ".log")
    out = []
    if os.path.exists(path):
        with open(path, encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                s = ln.strip()
                if s.startswith("(note:"):
                    out.append(s)
    return out


def tr(v, space):
    return __import__("math").log10(v) if space == "log10" else v


def with_majors(path, ax, major):
    if not major or None in major or not major[1] or major[1] <= 0:
        return None
    a, d, b = major
    k = int(round((b - a) / d))
    if k < 1 or k > 50:
        return None
    vals = [a + i * d for i in range(k + 1)]
    if ax == "y":
        vals = vals[::-1]
    try:
        return svg_truth.svg_axis_extent(path, ax, tick_values=vals)
    except ValueError:
        return None


def axes(pid, p):
    path = os.path.join(WORK, pid + ".svg")
    if not os.path.exists(path):
        return None
    doc = svg_truth.svg_document(path)
    cv = doc["canvas"]
    short = min(cv["w"], cv["h"])
    sc = p if "panels" not in p else p["panels"][0]
    out = {"canvas": [cv["w"], cv["h"]]}
    for ax in ("x", "y"):
        ext = svg_truth.svg_axis_extent(path, ax)
        if ext is None:
            # Labels that do not parse (dates, economist's commas): the
            # tick values are the axis's own majors, in pixel order.
            ext = with_majors(path, ax, sc[ax].get("major"))
        if ext is None:
            continue
        pr = ext["plotregion"]
        span_px = ((pr["right"] - pr["left"]) if ax == "x"
                   else (pr["bottom"] - pr["top"]))
        cmin, cmax = sc[ax]["cur"]
        if cmin is None or cmax is None:
            continue
        sp = ext["space"]
        lo, hi = tr(ext["low"], sp), tr(ext["high"], sp)
        a, b = tr(cmin, sp), tr(cmax, sp)
        if hi == lo:
            continue
        # low/high are the data values at the low and high edges; on a
        # reversed axis the left (x) or bottom (y) edge holds the high value.
        d_low = (a - lo) / (hi - lo) * span_px
        d_high = (hi - b) / (hi - lo) * span_px
        if ext["reversed"]:
            d_low, d_high = d_high, d_low
        out[ax] = {"margin_rel": {"lo": d_low / short, "hi": d_high / short},
                   "frame_frac": {"lo": d_low / span_px,
                                  "hi": d_high / span_px},
                   "edges": [ext["low"], ext["high"]],
                   "reversed": bool(ext["reversed"]), "space": sp,
                   "plotregion": [pr["left"], pr["top"], pr["right"],
                                  pr["bottom"]]}
    return out


for pid in order:
    p = probes[pid]
    p["notes"] = notes(pid)
    if p["rc"] == 0:
        a = axes(pid, p)
        if a:
            for k, v in a.items():
                if k == "canvas":
                    p["canvas"] = v
                else:
                    p.setdefault(k, {}).update(v)


def geom(r):
    return (r["x"], r["y"], r["w"], r["h"])


def base_rects(pid):
    path = os.path.join(WORK, pid + ".svg")
    if not os.path.exists(path):
        return set()
    return {(geom(r), r["fill"], r["stroke"]) for r in svg_truth.svg_rects(path)}


bases = {"DEF": base_rects("DEF"), "ZERO": base_rects("ZERO")}
for pid in order:
    if not pid.startswith("I") or probes[pid]["rc"] != 0:
        continue
    path = os.path.join(WORK, pid + ".svg")
    if not os.path.exists(path):
        continue
    base = bases["ZERO" if "margin(zero)" in probes[pid]["cmd"] else "DEF"]
    new = [r for r in svg_truth.svg_rects(path)
           if (geom(r), r["fill"], r["stroke"]) not in base]
    p = probes[pid]
    rects = []
    for r in new:
        if None in geom(r):
            continue
        d = dict(r)
        ok = all(k in p and "edges" in p[k] for k in ("x", "y"))
        if ok:
            xl, xr = p["x"]["edges"]
            yb, yt = p["y"]["edges"]
            pl, pt_, pr_, pb = p["x"]["plotregion"]
            ql, qt, qr, qb = p["y"]["plotregion"]

            def xd(px):
                return xl + (px - pl) / (pr_ - pl) * (xr - xl)

            def yd(py):
                return yb + (qb - py) / (qb - qt) * (yt - yb)
            d["data"] = {"left": xd(r["x"]), "right": xd(r["x"] + r["w"]),
                         "bottom": yd(r["y"] + r["h"]), "top": yd(r["y"])}
        rects.append(d)
    p["inner"] = rects

# The 28 margin styles, as text.
styles = {}
sdir = os.path.join(BASE, "style")
for fn in sorted(os.listdir(sdir)):
    m = re.match(r"^margin-(.+)\.style$", fn)
    if not m:
        continue
    sides = {}
    with open(os.path.join(sdir, fn), encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            t = ln.split()
            if len(t) >= 3 and t[0] == "set" and t[1] in ("gleft", "gright", "gtop", "gbottom"):
                sides[t[1][1:]] = t[-1]
    styles[m.group(1)] = [sides.get(k) for k in ("left", "right", "bottom", "top")]

# The margin ladder of three schemes, through their include chains.
LADDER = ("sidemargin", "medmargin", "medsmmargin", "medlgmargin",
          "largemargin", "vlargemargin", "smallmargin", "vsmallmargin",
          "tinymargin", "emargin", "esubmargin")


def scheme_lines(name, seen=None):
    seen = seen or set()
    if name in seen:
        return []
    seen.add(name)
    for sub in ("s", "."):
        path = os.path.join(BASE, sub, "scheme-%s.scheme" % name)
        if os.path.exists(path):
            break
    else:
        return []
    out = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            t = ln.split()
            if len(t) >= 2 and t[0] == "#include":
                out.extend(scheme_lines(t[1], seen))
            else:
                out.append(t)
    return out


ladders = {}
for sch in ("s2color", "stcolor", "economist"):
    lad = {}
    for t in scheme_lines(sch):
        if len(t) >= 3 and t[0] == "gsize" and t[1] in LADDER:
            v = t[2]
            if v.startswith("relative"):
                lad[t[1]] = float(v[len("relative"):].replace("p", "."))
    ladders[sch] = lad

doc = {"_meta": {"stata_version": Macro.getLocal("stata_version"),
                 "born_date": Macro.getLocal("born_date"),
                 "dash_commit": Macro.getLocal("dash_commit"),
                 "extracted": Macro.getLocal("extracted"),
                 "units": ("margin_rel = plot-region edge to curmin (or "
                           "curmax) distance / min(canvas W, H); lo is the "
                           "left or bottom side, hi the right or top"),
                 "source": "scripts/extract_margin_truth.do",
                 "marginstyles": styles, "ladders": ladders},
       "probes": probes}
with open(Macro.getGlobal("MT_OUT"), "w") as fh:
    json.dump(doc, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("margin_truth: wrote %d probes" % len(probes))
end

display as text "extract_margin_truth.do: done"
