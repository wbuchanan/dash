*! extract_default_axes_truth.do
*! WP-30 S21 (P1.3a): twoway's default axes -- natscale ticks for the
*! scheme's tick count, the scale's hull over every drawn layer, the
*! plot-region margin and by()'s size multiplier -- measured from Stata.
*!
*! Output: test/fixtures/default_axes_truth.json
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_default_axes_truth.do
*!
*! Per probe: .Graph.plotregion1.{y,x}scale.{min,max,curmin,curmax},
*! .Graph.{y,x}axis1.major.{min,delta,max}, the axis-2 majors and scales
*! when present, and .Graph.plotregion1.gmetric_mult for a by() graph
*! (with each panel's scales, .Graph.graphs[k]).  A probe marked svg is
*! exported, and the trailing python: block reads the SVG through
*! scripts/svg_truth.py: margin_rel is the distance from the plot-region
*! edge to curmin's pixel over min(canvas W, H), frame_frac that distance
*! over the plot-region's extent.  The python block reads files and
*! locals only and calls no Stata; a backtick in it is spelled \x60.

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_default_axes_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_default_axes_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1

clear all
set more off
set linesize 255
version 19
set graphics off
set scheme stcolor

global NS_REPO "`repo'"
global NS_OUT "${NS_REPO}/test/fixtures/default_axes_truth.json"
local work "`c(tmpdir)'dash_default_axes_probe"
capture mkdir "`work'"
global NS_WORK "`work'"
global NS_REC "`work'/ns_records.txt"

local stata_version = c(stata_version)
local born_date "`c(born_date)'"
local extracted "`c(current_date)'"
tempfile nsgit
quietly shell git -C "${NS_REPO}" rev-parse HEAD > "`nsgit'"
tempname nsgh
file open `nsgh' using "`nsgit'", read text
file read `nsgh' nsline
file close `nsgh'
local dash_commit = trim(`"`nsline'"')

capture program drop _ns_data
program _ns_data
    args which
    sysuse auto, clear
    if "`which'" == "tc" {
        quietly generate double t = clock("2001-01-01 00:00:00", "YMDhms") + _n * 7 * 3600000
        format t %tc
    }
    else if substr("`which'", 1, 1) == "g" {
        local G = substr("`which'", 2, .)
        quietly generate g = mod(_n, `G')
    }
end

capture program drop _ns_scales
program _ns_scales
    // one line: the scales and majors of graph object `1'
    args id tag p
    local r "S|`id'|`tag'"
    foreach d in y x {
        local s "`p'.plotregion1.`d'scale"
        local a "`p'.`d'axis1"
        local r "`r'|``s'.min'|``s'.max'|``s'.curmin'|``s'.curmax'|``a'.major.min'|``a'.major.delta'|``a'.major.max'"
    }
    foreach d in y x {
        local s "`p'.`d'axis2.plotregion.`d'scale"
        local a "`p'.`d'axis2"
        local r "`r'|``s'.curmin'|``s'.curmax'|``a'.major.min'|``a'.major.delta'|``a'.major.max'"
    }
    file write nsrec `"`r'"' _n
end

capture program drop _ns_rec
program _ns_rec
    // _ns_rec <id> <scheme> <data> <svg 0/1> `"<command>"'
    args id scheme data svg cmd
    _ns_data `data'
    capture graph drop _all
    capture noisily `cmd' scheme(`scheme')
    local rc = _rc
    file write nsrec `"P|`id'|`scheme'|`data'|`rc'|`svg'|`cmd'"' _n
    if `rc' == 0 {
        local n "`.Graph.graphs.arrnels'"
        if "`n'" == "" | "`n'" == "." local n 0
        if `n' > 0 {
            file write nsrec `"G|`id'|`.Graph.plotregion1.gmetric_mult'|`n'"' _n
            forvalues k = 1/`n' {
                _ns_scales `id' `k' ".Graph.graphs[`k']"
            }
        }
        else _ns_scales `id' 0 ".Graph"
        if `svg' {
            capture graph export "${NS_WORK}/`id'.svg", replace
        }
    }
    capture graph drop _all
end

file open nsrec using "${NS_REC}", write text replace

local T "twoway"
_ns_rec P01  stcolor  auto 1 `"`T' scatter mpg weight,"'
_ns_rec P01b stcolor  auto 0 `"`T' scatter mpg weight, ylabel(#5) xlabel(#5)"'
_ns_rec P02  s2color  auto 1 `"`T' scatter mpg weight,"'
_ns_rec P10  economist auto 1 `"`T' scatter mpg weight,"'
_ns_rec P13  stcolor  auto 1 `"`T' scatter mpg weight, xsize(4) ysize(4)"'
_ns_rec B03  s2color  auto 1 `"`T' scatter mpg weight, xsize(10) ysize(3)"'
_ns_rec B02  stcolor  auto 1 `"`T' scatter mpg weight, title("t") legend(on) note("n")"'
_ns_rec P03  stcolor  auto 0 `"`T' (scatter price mpg) (lfit price mpg),"'
_ns_rec P05  stcolor  auto 0 `"`T' (scatter mpg weight) (scatteri 50 1000),"'
_ns_rec P06  stcolor  auto 0 `"`T' scatter price weight, yscale(log)"'
_ns_rec P08  stcolor  auto 0 `"`T' histogram mpg,"'
_ns_rec P09  stcolor  auto 0 `"`T' bar price rep78,"'
_ns_rec P12  stcolor  auto 0 `"`T' function y=x^2, range(0 3)"'
_ns_rec P14  stcolor  auto 0 `"`T' (scatter mpg weight) (lfit mpg weight),"'
_ns_rec P15  stcolor  auto 0 `"`T' kdensity mpg,"'
_ns_rec P16  stcolor  auto 0 `"`T' scatter mpg weight if foreign,"'
_ns_rec P17  stcolor  auto 0 `"`T' (scatter mpg weight) (scatter price weight, yaxis(2)),"'
_ns_rec X2   stcolor  auto 0 `"`T' (scatter mpg weight) (scatter mpg price, xaxis(2)),"'
_ns_rec P20  stcolor  auto 0 `"`T' (scatter mpg weight) (qfitci mpg weight),"'
_ns_rec Q01  stcolor  auto 0 `"`T' scatter mpg weight if price<=7075.5,"'
_ns_rec Q02  stcolor  auto 0 `"`T' (scatter price mpg) (lfit price mpg), by(foreign)"'
_ns_rec Q06  stcolor  auto 0 `"`T' (scatter mpg weight) (lfit mpg weight) if price<=7075.5,"'
_ns_rec Q08  stcolor  auto 0 `"`T' (scatter mpg weight) (scatter price weight, yaxis(2)) if foreign,"'
_ns_rec Q09  stcolor  auto 0 `"`T' rarea mpg turn weight,"'
_ns_rec Q10  stcolor  auto 0 `"`T' spike mpg weight,"'
_ns_rec Q11  stcolor  auto 0 `"`T' dropline mpg weight,"'
_ns_rec P22  stcolor  auto 0 `"`T' area mpg weight,"'
_ns_rec B01  stcolor  auto 0 `"`T' bar mpg weight,"'
_ns_rec B06  stcolor  auto 0 `"`T' bar mpg weight, base(5)"'
_ns_rec Q12  stcolor  auto 0 `"`T' scatter mpg weight, yscale(log) xscale(log)"'
_ns_rec L00  stcolor  auto 0 `"`T' scatter mpg weight,"'
_ns_rec L01  stcolor  auto 0 `"`T' scatter mpg weight, yline(50)"'
_ns_rec L02  stcolor  auto 0 `"`T' scatter mpg weight, xline(6000)"'
_ns_rec L03  stcolor  auto 0 `"`T' scatter mpg weight, text(50 6000 "hi")"'
_ns_rec L04  stcolor  auto 0 `"`T' scatter mpg weight, mlabel(make)"'
_ns_rec L05  stcolor  auto 0 `"`T' (scatter mpg weight) (scatteri 50 6000, msymbol(none)),"'
_ns_rec L07  stcolor  auto 0 `"`T' (scatter mpg weight) (pcarrowi 50 6000 45 5500),"'
_ns_rec TC   stcolor  tc   0 `"`T' scatter mpg t,"'
_ns_rec BY2  stcolor  auto 1 `"`T' scatter mpg weight, by(foreign)"'
_ns_rec BY3  stcolor  g3   0 `"`T' scatter mpg weight, by(g)"'
_ns_rec BY6  stcolor  g6   0 `"`T' scatter mpg weight, by(g)"'
_ns_rec BY10 stcolor  g10  0 `"`T' scatter mpg weight, by(g)"'

local schemes "s2color stgcolor_mv stcolor s1rcolor economist s2manual stmono1 stgcolor stcolor_alt s2gmanual stgcolor_alt stcolor_meta s1manual stsj stcolor_mv sj meta s2color8 s1mono stmono2 stcoloralias s2mono sttrans stgcolor_meta s1color s2gcolor"
global NS_SCHEMES "`schemes'"
foreach s of local schemes {
    _ns_rec scheme_`s' `s' auto 0 `"`T' scatter mpg weight,"'
}
file close nsrec

python:
import json, os, sys
from sfi import Macro

REPO = Macro.getGlobal("NS_REPO")
WORK = Macro.getGlobal("NS_WORK")
sys.path.insert(0, os.path.join(REPO, "scripts"))
import svg_truth


def num(s):
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None
    return v if v == v and abs(v) < 8.98e307 else None


def scales(f):
    out = {}
    i = 0
    for d in ("y", "x"):
        mn, mx, cmn, cmx, a, dl, b = (num(v) for v in f[i:i + 7])
        i += 7
        out[d] = {"min": mn, "max": mx, "cur": [cmn, cmx],
                  "major": [a, dl, b]}
    for d in ("y2", "x2"):
        cmn, cmx, a, dl, b = (num(v) for v in f[i:i + 5])
        i += 5
        if a is not None:
            out[d] = {"cur": [cmn, cmx], "major": [a, dl, b]}
    return out


probes, order = {}, []
with open(Macro.getGlobal("NS_REC"), encoding="utf-8", errors="replace") as fh:
    for line in fh:
        f = line.rstrip("\n").split("|")
        if f[0] == "P":
            pid = f[1]
            probes[pid] = {"scheme": f[2], "data": f[3], "rc": int(f[4]),
                           "svg": f[5] == "1", "cmd": "|".join(f[6:])}
            order.append(pid)
        elif f[0] == "G":
            probes[f[1]]["gmetric"] = num(f[2])
            probes[f[1]]["panels"] = []
        elif f[0] == "S":
            sc = scales(f[3:])
            if f[2] == "0":
                probes[f[1]].update(sc)
            else:
                probes[f[1]]["panels"].append(sc)


def margins(pid, p):
    path = os.path.join(WORK, pid + ".svg")
    if not os.path.exists(path):
        return
    doc = svg_truth.svg_document(path)
    cv = doc["canvas"]
    short = min(cv["w"], cv["h"])
    sc = p if "panels" not in p else p["panels"][0]
    out = {}
    for ax in ("x", "y"):
        ext = svg_truth.svg_axis_extent(path, ax)
        if ext is None:
            continue
        pr = ext["plotregion"]
        span_px = ((pr["right"] - pr["left"]) if ax == "x"
                   else (pr["bottom"] - pr["top"]))
        lo, hi = ext["low"], ext["high"]
        cmin = sc[ax]["cur"][0]
        if cmin is None or hi == lo:
            continue
        dist = (cmin - lo) / (hi - lo) * span_px
        out[ax] = {"margin_rel": dist / short, "frame_frac": dist / span_px,
                   "canvas": [cv["w"], cv["h"]]}
    p["svg_margin"] = out


for pid in order:
    if probes[pid]["svg"] and probes[pid]["rc"] == 0:
        margins(pid, probes[pid])

schemes = {}
for pid in list(order):
    if pid.startswith("scheme_"):
        schemes[pid[len("scheme_"):]] = probes.pop(pid)

doc = {"_meta": {"stata_version": Macro.getLocal("stata_version"),
                 "born_date": Macro.getLocal("born_date"),
                 "dash_commit": Macro.getLocal("dash_commit"),
                 "extracted": Macro.getLocal("extracted"),
                 "units": ("SVG 720 units per inch; margin_rel = edge-to-"
                           "curmin distance / min(canvas W, H)"),
                 "source": "scripts/extract_default_axes_truth.do"},
       "probes": probes, "schemes": schemes}
with open(Macro.getGlobal("NS_OUT"), "w") as fh:
    json.dump(doc, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("default_axes_truth: wrote %d probes" % len(probes))
end

display as text "extract_default_axes_truth.do: done"
