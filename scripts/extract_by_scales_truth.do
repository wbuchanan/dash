*! extract_by_scales_truth.do
*! twoway's by() scales, measured from Stata itself (WP-29 P0.2, section
*! 10): which axes a by() graph's panels share, which yrescale, xrescale,
*! rescale (and their spellings and style()) give each panel its own, and
*! what range() does on a rescaled axis.
*!
*! Output: ${W29_REPO}/test/fixtures/by_scales_truth.json
*!
*! Run (Stata only through the slot wrapper, never the GUI), with a two-line
*! driver that sets the repository root:
*!
*!   printf 'global W29_REPO "%s"\ndo "%s/scripts/extract_by_scales_truth.do"\n' \
*!       <repo> <repo> > <scratch>/run_extract_by_scales_truth.do
*!   <repo>/scripts/stata_slot.sh <scratch> <scratch>/run_extract_by_scales_truth.do
*!
*! METHOD (bygraph_g.class set_rescaled, axis_allrange).  Each probe runs
*! under capture noisily; for an rc-0 probe, per panel k of .Graph.graphs:
*!   subtitle.text[1]                               the panel's title
*!   plotregion1.{y,x}scale.{min,max,curmin,curmax,reverse.istrue,
*!       transform.stylename}                       the panel's scales
*!   {y,x}axis1.major.{min,max,delta}, {y,x}axis1.draw_view.istrue
*!   yaxis2.plotregion.yscale.{min,max}, yaxis2.major.{min,max,delta}
*!   xaxis2.plotregion.xscale.{min,max}, xaxis2.major.{min,max,delta}
*! (a member that does not exist is recorded as null).  The python block
*! reads Stata only through sfi (Macro, Data) and never calls Stata; it
*! writes the probes, the data they were measured on, and rescale_rule:
*! each spelling of the "rule" probes mapped to the letters whose panel
*! scale min/max differ between panels.  A backtick in it is spelled \x60.

* make truth (no driver): DASH_REPO stands in for the global.
if "${W29_REPO}" == "" {
    local _w29_env : environment DASH_REPO
    if `"`_w29_env'"' != "" global W29_REPO `"`_w29_env'"'
}
if "${W29_REPO}" == "" {
    display as error "extract_by_scales_truth.do: set global W29_REPO to the repository root"
    exit 198
}
adopath ++ "${W29_REPO}/"
global dash_nobrowser 1

clear all
set graphics off
set more off
set linesize 255
version 19

local stata_version = c(stata_version)
local born_date "`c(born_date)'"
local extracted "`c(current_date)'"
tempfile gh
capture shell cd "${W29_REPO}" && git rev-parse HEAD > "`gh'"
local dash_commit ""
capture confirm file "`gh'"
if !_rc {
    tempname fh
    file open `fh' using "`gh'", read text
    file read `fh' dash_commit
    file close `fh'
}

local work "`c(tmpdir)'/dash_by_scales_probe"
capture mkdir "`work'"
global BSC_REC "`work'/by_scales_records.txt"
capture erase "${BSC_REC}"

capture program drop _bsc_data
program _bsc_data
    // the %td set of probe c23
    args which
    if "`which'" == "td" {
        clear
        quietly set obs 20
        generate t = td(01jan2000) + cond(_n > 10, 400 + _n * 30, _n)
        format t %td
        generate g = _n > 10
        generate y = _n + cond(_n > 10, 100, 0)
    }
    else sysuse auto, clear
end

capture program drop _bsc_rec
program _bsc_rec
    // one record line per panel
    local n "`.Graph.graphs.arrnels'"
    if "`n'" == "" local n 0
    file write bscrec "N|`n'" _n
    forvalues k = 1/`n' {
        local p ".Graph.graphs[`k']"
        local r "K|`k'|``p'.subtitle.text[1]'"
        foreach d in y x {
            local s "`p'.plotregion1.`d'scale"
            local r "`r'|``s'.min'|``s'.max'|``s'.curmin'|``s'.curmax'|``s'.reverse.istrue'|``s'.transform.stylename'"
            local a "`p'.`d'axis1"
            local r "`r'|``a'.major.min'|``a'.major.max'|``a'.major.delta'|``a'.draw_view.istrue'"
        }
        foreach d in y x {
            local s "`p'.`d'axis2.plotregion.`d'scale"
            local a "`p'.`d'axis2"
            local r "`r'|``s'.min'|``s'.max'|``a'.major.min'|``a'.major.max'|``a'.major.delta'"
        }
        file write bscrec `"`r'"' _n
    }
end

capture program drop _bsc_run
program _bsc_run
    // _bsc_run <id> <data> `"<command>"'
    args id data o
    _bsc_data `data'
    capture graph drop _all
    capture noisily `o'
    local rc = _rc
    file write bscrec `"P|`id'|`rc'|`data'|`o'"' _n
    if `rc' == 0 _bsc_rec
    capture graph drop _all
end

file open bscrec using "${BSC_REC}", write text replace

local S "twoway scatter mpg weight"
local D "twoway (scatter mpg weight) (scatter price weight, yaxis(2))"
local X "twoway (scatter mpg weight) (scatter mpg length, xaxis(2))"

* ---- shared by default ----
_bsc_run c01 auto `"`S', by(foreign)"'
_bsc_run c13 auto `"`S', by(foreign, total)"'
_bsc_run c14 auto `"`S', by(rep78, missing)"'
_bsc_run c15 auto `"twoway (scatter mpg weight) (lfit mpg weight), by(foreign)"'
_bsc_run c16 auto `"`D', by(foreign)"'
_bsc_run c18 auto `"`S', by(foreign) yscale(log)"'
_bsc_run c22 auto `"twoway histogram mpg, by(foreign)"'
_bsc_run c23 td   `"twoway scatter y t, by(g)"'
_bsc_run c25 auto `"twoway bar mpg weight, by(foreign)"'
_bsc_run c26 auto `"twoway kdensity mpg, by(foreign)"'
_bsc_run c27 auto `"`S', by(foreign rep78)"'
_bsc_run c33 auto `"`S', by(foreign) yscale(range(0))"'
_bsc_run d47 auto `"twoway scatter mpg weight if price>6000, by(foreign)"'
_bsc_run d50 auto `"twoway scatter mpg weight in 1/60, by(foreign)"'
_bsc_run d52 auto `"twoway rarea mpg turn weight, sort by(foreign)"'
_bsc_run f02 auto `"`X', by(foreign)"'
_bsc_run k07 auto `"`D', by(foreign) yscale(range(0) axis(2))"'

* ---- rescaled ----
_bsc_run c02 auto `"`S', by(foreign, yrescale)"'
_bsc_run c03 auto `"`S', by(foreign, xrescale)"'
_bsc_run c04 auto `"`S', by(foreign, rescale)"'
_bsc_run c05 auto `"`S', by(foreign, r)"'
_bsc_run c06 auto `"`S', by(foreign, yr)"'
_bsc_run c07 auto `"`S', by(foreign, xr)"'
_bsc_run c08 auto `"`S', by(foreign, norescale)"'
_bsc_run c09 auto `"`S', by(foreign, rescale noyrescale)"'
_bsc_run c10 auto `"`S', by(foreign, yrescale noyrescale)"'
_bsc_run c11 auto `"`S', by(foreign, style(rescale))"'
_bsc_run c12 auto `"`S', by(foreign, style(compact) yrescale)"'
_bsc_run c17 auto `"`D', by(foreign, yrescale)"'
_bsc_run c20 auto `"`S', by(foreign, yrescale) ylabel(0(10)50)"'
_bsc_run c28 auto `"`S', by(foreign, yrescale) ylabel(#5)"'
_bsc_run c29 auto `"`S', by(foreign, noyrescale)"'
_bsc_run c30 auto `"`S', by(foreign, rescale) ylabel(#5) xlabel(#4)"'
_bsc_run c31 auto `"`S', by(foreign, resc)"'
_bsc_run c32 auto `"`S', by(foreign, yresc)"'
_bsc_run c36 auto `"`S', by(foreign, r(1))"'
_bsc_run c38 auto `"`S', by(foreign, total yrescale)"'
_bsc_run d19 auto `"`S', by(foreign, yrescale) yscale(range(0))"'
_bsc_run d40 auto `"`S', by(foreign, yrescale) xscale(range(0))"'
_bsc_run d41 auto `"`S', by(foreign, xrescale) yscale(range(0))"'
_bsc_run d44 auto `"`S', by(foreign, xrescale) xscale(range(0))"'
_bsc_run d46 auto `"`S', by(foreign, rescale) yscale(range(0)) xscale(range(0))"'
_bsc_run d48 auto `"`S', by(foreign, yrescale) ytick(0 60)"'
_bsc_run d49 auto `"`D', by(foreign, yrescale) yscale(range(0) axis(2))"'
_bsc_run d53 auto `"`S', by(foreign, yrescale norescale)"'
_bsc_run d54 auto `"`S', by(foreign, norescale yrescale)"'
_bsc_run d55 auto `"`S', by(foreign, yrescale) yscale(range(0 50))"'
_bsc_run e01 auto `"`S', by(foreign, style(rescale) noyrescale)"'
_bsc_run e02 auto `"`S', by(foreign, style(combine))"'
_bsc_run e03 auto `"`S', by(foreign, yrescale) yscale(reverse)"'
_bsc_run e04 auto `"`S', by(foreign, yrescale) yscale(log)"'
_bsc_run e06 auto `"`S', by(foreign, Yrescale)"'
_bsc_run e07 auto `"`S', by(foreign, YRESCALE)"'
_bsc_run e08 auto `"`S', by(foreign, rescal)"'
_bsc_run e09 auto `"`S', by(foreign, yrescal)"'
_bsc_run e10 auto `"`S', by(foreign, yrescale) yscale(range(5))"'
_bsc_run e12 auto `"`D', by(foreign, yrescale) yscale(range(0) axis(2))"'
_bsc_run f01 auto `"twoway scatter mpg weight if foreign == 1, by(foreign, yrescale) yscale(range(0))"'
_bsc_run f03 auto `"`X', by(foreign, xrescale)"'
_bsc_run f04 auto `"`S', by(foreign, total rescale)"'
_bsc_run f05 auto `"`S', by(foreign, xrescale) xlabel(#4)"'
_bsc_run k02 auto `"`S', by(foreign, yrescale) yscale(range(0))"'
_bsc_run k03 auto `"`S', by(foreign, YRESCALE)"'
_bsc_run k06 auto `"`S', by(foreign, yrescale) ylabel(#5)"'
_bsc_run k09 auto `"`S', by(foreign, re)"'
_bsc_run k11 auto `"`S', by(foreign, res noyr)"'
_bsc_run k16 auto `"`S', by(foreign, rescale(1))"'
_bsc_run m01 auto `"`S', by(foreign, style(rescale) style(combine))"'
_bsc_run m02 auto `"`S', by(foreign, style(compact) style(rescale))"'
_bsc_run m03 auto `"`S', by(foreign, style(resc))"'
_bsc_run m04 auto `"`S', by(foreign, compact style(rescale))"'
_bsc_run m06 auto `"`S', by(foreign, style(rescale) nor)"'
_bsc_run m07 auto `"`S', by(foreign, yrescale) ylabel(#5) yscale(range(0))"'

* ---- the rescale rule, one probe per spelling (rule ids) ----
local k = 0
foreach s in ///
    `"(none)"' `"norescale"' `"nor"' `"noyrescale"' `"r(1)"' ///
    `"style(compact)"' `"style(resc)"' `"style(rescale) nor"' ///
    `"rescale"' `"r"' `"re"' `"resc"' `"rescal"' `"rescale noyrescale"' ///
    `"res noyr"' `"style(rescale)"' `"style(combine)"' ///
    `"compact style(rescale)"' `"yrescale"' `"yr"' `"yresc"' `"yrescal"' ///
    `"yrescale noyrescale"' `"yrescale norescale"' `"norescale yrescale"' ///
    `"nor yr"' `"style(compact) yrescale"' `"compact yrescale"' ///
    `"rows(1) yrescale"' `"total yrescale"' `"xrescale"' `"xr"' `"xresc"' ///
    `"style(rescale) noyrescale"' {
    local ++k
    local sub `"`s'"'
    if `"`s'"' == "(none)" local sub ""
    file write bscrec `"R|rule`k'|`s'"' _n
    _bsc_run rule`k' auto `"`S', by(foreign, `sub')"'
}

file close bscrec

* ---- the data the probes were measured on ----
sysuse auto, clear
keep mpg weight price turn rep78 foreign length
global BSC_AUTO "`work'/by_scales_auto.csv"
quietly export delimited using "${BSC_AUTO}", replace nolabel
_bsc_data td
global BSC_TD "`work'/by_scales_td.csv"
quietly export delimited using "${BSC_TD}", replace nolabel

python:
import csv, json, os
from sfi import Macro

repo = Macro.getGlobal("W29_REPO")


def _num(s):
    s = s.strip()
    if s == "" or s == ".":
        return None
    try:
        return float(s)
    except ValueError:
        return s


def _csv(path):
    out = {}
    with open(path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            for k, v in row.items():
                out.setdefault(k, []).append(_num(v))
    return out


_AX = ("min", "max", "curmin", "curmax", "reverse", "transform",
       "major_min", "major_max", "major_delta", "view")
_AX2 = ("min", "max", "major_min", "major_max", "major_delta")

probes, rules, cur, spelling = [], {}, None, None
with open(Macro.getGlobal("BSC_REC"), encoding="utf-8", errors="replace") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if not line:
            continue
        kind, rest = line.split("|", 1)
        if kind == "R":
            rid, spelling = rest.split("|", 1)
            rules[rid] = "" if spelling == "(none)" else spelling
        elif kind == "P":
            pid, rc, data, cmd = rest.split("|", 3)
            cur = {"id": pid, "command": cmd, "rc": int(rc), "data": data,
                   "n": 0, "panels": []}
            if pid in rules:
                cur["spelling"] = rules[pid]
            probes.append(cur)
        elif kind == "N":
            cur["n"] = int(rest)
        elif kind == "K":
            f = rest.split("|")
            p = {"panel": int(f[0]), "title": f[1]}
            i = 2
            for d in ("y", "x"):
                p[d] = {k: _num(v) for k, v in zip(_AX, f[i:i + 10])}
                p[d]["transform"] = f[i + 5]
                i += 10
            for d in ("y2", "x2"):
                p[d] = {k: _num(v) for k, v in zip(_AX2, f[i:i + 5])}
                i += 5
            cur["panels"].append(p)


def _rescaled(probe):
    out = []
    for d in ("x", "y"):
        spans = {(p[d]["min"], p[d]["max"]) for p in probe["panels"]}
        if len(spans) > 1:
            out.append(d)
    return sorted(out)


rescale_rule = {p["spelling"]: _rescaled(p) for p in probes
                if "spelling" in p and p["rc"] == 0}

out = {
    "_meta": {
        "stata_version": Macro.getLocal("stata_version"),
        "born_date": Macro.getLocal("born_date"),
        "source": "scripts/extract_by_scales_truth.do",
        "dash_commit": Macro.getLocal("dash_commit").strip(),
        "extracted": Macro.getLocal("extracted"),
        "method": ".Graph.graphs[k] members via bygraph_g.class "
                  "(scripts/extract_by_scales_truth.do)",
    },
    "data": {"auto": _csv(Macro.getGlobal("BSC_AUTO")),
             "auto_value_labels": {"origin": {"0": "Domestic",
                                              "1": "Foreign"}},
             "auto_value_label_names": {"foreign": "origin"},
             "td": _csv(Macro.getGlobal("BSC_TD")),
             "td_formats": {"t": "%td"}},
    "probes": probes,
    "rescale_rule": rescale_rule,
}
path = os.path.join(repo, "test", "fixtures", "by_scales_truth.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote %s (%d probes)" % (path, len(probes)))
end
