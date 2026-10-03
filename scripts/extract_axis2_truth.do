*! extract_axis2_truth.do
*! twoway's axis(#) routing, measured from Stata itself (WP-29 P0.5,
*! section 10): which axis each axis(#) sub-option lands on, the extents it
*! gives, the spellings twoway accepts and the forms it refuses, in order.
*!
*! Output: ${W29_REPO}/test/fixtures/axis2_truth.json
*!
*! Run (Stata only through the slot wrapper, never the GUI), with a two-line
*! driver that sets the repository root:
*!
*!   printf 'global W29_REPO "%s"\ndo "%s/scripts/extract_axis2_truth.do"\n' \
*!       <repo> <repo> > <scratch>/run_extract_axis2_truth.do
*!   <repo>/scripts/stata_slot.sh <scratch> <scratch>/run_extract_axis2_truth.do
*!
*! METHOD (graph_g.class ParseAndLogAxes).  Every probe runs under
*! capture noisily inside its own text log, so the first error line is read
*! back from that log.  For an rc-0 probe, these .Graph members are recorded:
*!   .Graph.<yaxis1|yaxis2|xaxis1|xaxis2>.<major|majornl|minor|minornl>
*!        .dlg_tickpos[i]          (arrnels first)
*!   .Graph.plotregion<j>.{yaxis_dexes, xaxis_dexes}
*!   .Graph.plotregion<j>.{y,x}scale.{curmin, curmax, transform.stylename,
*!        reverse.istrue}
*!   .Graph.plotregion<j>._xylines[l].z, with orientation from
*!        gdi_y0 == gdi_y1 (a horizontal line is a y line)
*! and for the by() probe gb, per panel k, .Graph.graphs[k].yaxis2.major.
*! Stata writes one record file; the trailing python: block reads it and the
*! per-probe logs (never calling Stata) and writes the JSON.  A backtick in
*! that block is spelled \x60.

if "${W29_REPO}" == "" {
    display as error "extract_axis2_truth.do: set global W29_REPO to the repository root"
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

local work "`c(tmpdir)'/dash_axis2_probe"
capture mkdir "`work'"
global AX2_WORK "`work'"
global AX2_REC "`work'/axis2_records.txt"
capture erase "${AX2_REC}"
global AX2_N = 0

capture program drop _ax2_ticks
program _ax2_ticks
    // _ax2_ticks <obj> <name> : one record of an axis tick set
    args obj name
    foreach set in major majornl minor minornl {
        local n "`.Graph.`obj'.`set'.dlg_tickpos.arrnels'"
        if "`n'" == "" continue
        local v ""
        forvalues i = 1/`n' {
            local v `v' `.Graph.`obj'.`set'.dlg_tickpos[`i']'
        }
        file write ax2rec "A|`name'|`set'|`v'" _n
    }
end

capture program drop _ax2_members
program _ax2_members
    foreach ax in yaxis1 yaxis2 xaxis1 xaxis2 {
        _ax2_ticks `ax' `ax'
    }
    forvalues j = 1/4 {
        local ydx "`.Graph.plotregion`j'.yaxis_dexes'"
        local xdx "`.Graph.plotregion`j'.xaxis_dexes'"
        local ymin "`.Graph.plotregion`j'.yscale.curmin'"
        if "`ymin'`ydx'" == "" continue
        local r "R|`j'|`ydx'|`xdx'"
        foreach d in y x {
            local r "`r'|`.Graph.plotregion`j'.`d'scale.curmin'|`.Graph.plotregion`j'.`d'scale.curmax'"
            local r "`r'|`.Graph.plotregion`j'.`d'scale.transform.stylename'|`.Graph.plotregion`j'.`d'scale.reverse.istrue'"
        }
        file write ax2rec "`r'" _n
        local nl "`.Graph.plotregion`j'._xylines.arrnels'"
        if "`nl'" == "" continue
        forvalues l = 1/`nl' {
            local z "`.Graph.plotregion`j'._xylines[`l'].z'"
            local y0 "`.Graph.plotregion`j'._xylines[`l'].gdi_y0'"
            local y1 "`.Graph.plotregion`j'._xylines[`l'].gdi_y1'"
            local o "x"
            if "`y0'" == "`y1'" local o "y"
            file write ax2rec "L|`j'|`z'|`o'" _n
        }
    }
end

capture program drop _ax2_panels
program _ax2_panels
    // by(): each panel's second-axis major ticks
    forvalues k = 1/12 {
        local n "`.Graph.graphs[`k'].yaxis2.major.dlg_tickpos.arrnels'"
        if "`n'" == "" continue
        local v ""
        forvalues i = 1/`n' {
            local v `v' `.Graph.graphs[`k'].yaxis2.major.dlg_tickpos[`i']'
        }
        file write ax2rec "G|`k'|`v'" _n
    }
end

capture program drop _ax2_run
program _ax2_run
    // _ax2_run <id> `"<command>"' : run one probe under its own log
    args id o
    global AX2_N = ${AX2_N} + 1
    sysuse auto, clear
    capture graph drop _all
    capture log close ax2log
    quietly log using "${AX2_WORK}/`id'.log", text replace name(ax2log)
    timer clear 9
    timer on 9
    capture noisily `o'
    local rc = _rc
    timer off 9
    quietly log close ax2log
    quietly timer list 9
    local secs = r(t9)
    file write ax2rec `"P|`id'|`rc'|`secs'|`o'"' _n
    if `rc' == 0 {
        if "`id'" == "gb" _ax2_panels
        else _ax2_members
    }
    capture graph drop _all
end

file open ax2rec using "${AX2_REC}", write text replace

local B "twoway (scatter mpg weight) (line price weight, yaxis(2) sort)"
local X "twoway (scatter mpg weight) (scatter mpg length, xaxis(2))"
local S "twoway scatter mpg weight"
local L "twoway line price weight, yaxis(2) sort"

* ---- routing, repeats, extents and spellings on the dual-y graph B ----
local o `"`B'"'
_ax2_run c1 `"`o'"'
local o `"`B', ylabel(5000 10000 15000, axis(2))"'
_ax2_run c2 `"`o'"'
local o `"`B', yscale(log axis(2))"'
_ax2_run c3 `"`o'"'
local o `"`B', yline(5000, axis(2))"'
_ax2_run c4 `"`o'"'
local o `"`B', ytick(5000 7500, axis(2))"'
_ax2_run c5 `"`o'"'
local o `"`B', ymlabel(6000 9000, axis(2))"'
_ax2_run c6 `"`o'"'
local o `"`B', ymtick(6000 9000, axis(2))"'
_ax2_run c7 `"`o'"'
local o `"`B', ylabel(10 20) ylabel(5000 10000, axis(2))"'
_ax2_run c8 `"`o'"'
local o `"`B', ylabel(5000 10000, axis(2)) ylabel(10 20)"'
_ax2_run c9 `"`o'"'
local o `"`B', ylabel(5000 10000, axis(2)) ylabel(6000, axis(2))"'
_ax2_run c10 `"`o'"'
local o `"`B', yline(5000 10000, axis(2)) yline(20)"'
_ax2_run c11 `"`o'"'
local o `"`B', yscale(log axis(2)) yscale(reverse)"'
_ax2_run c12 `"`o'"'
local o `"`B', ylabel(20000, axis(2))"'
_ax2_run c13 `"`o'"'
local o `"`B', ytick(20000, axis(2))"'
_ax2_run c14 `"`o'"'
local o `"`B', yline(30000, axis(2))"'
_ax2_run c15 `"`o'"'
local o `"`B', ylabel(5000 10000, axis(2) norescale) ytick(20000, axis(2) norescale)"'
_ax2_run c16 `"`o'"'
local o `"`B', ylabel(5000, ax(2))"'
_ax2_run c17 `"`o'"'
local o `"`B', ylabel(5000, axi(2))"'
_ax2_run c18 `"`o'"'
local o `"`B', ytic(5000, ax(2))"'
_ax2_run c19 `"`o'"'
local o `"`B', yli(5000, ax(2))"'
_ax2_run c20 `"`o'"'
local o `"`B', ysc(log ax(2))"'
_ax2_run c21 `"`o'"'
local o `"`B', yml(6000, ax(2))"'
_ax2_run c22 `"`o'"'
local o `"`B', ymt(6000, ax(2))"'
_ax2_run c23 `"`o'"'
local o `"`B', ytitle(T, ax(2))"'
_ax2_run c24 `"`o'"'
local o `"`B', ylabel(5000, axis( 2 ))"'
_ax2_run c25 `"`o'"'
local o `"`B', ylabel(5000, axis(02))"'
_ax2_run c26 `"`o'"'
local o `"`B', ylabel(5000, axis(2.0))"'
_ax2_run c27 `"`o'"'
local o `"`B', ylabel(5000, axis(+2))"'
_ax2_run c28 `"`o'"'
local o `"`B', ylabel(5000, axis(2e0))"'
_ax2_run c29 `"`o'"'
local o `"`B', ylabel(5000, axis(1.0x+1))"'
_ax2_run c30 `"`o'"'
local o `"`B', ylabel(5000, axis(2.5))"'
_ax2_run c31 `"`o'"'
local o `"`B', ylabel(5000, axis(a))"'
_ax2_run c32 `"`o'"'
* c33: axis-1 options on a graph whose only layer is on yaxis(2) (SD-1)
local o `"`L' ylabel(5000 10000)"'
_ax2_run c33 `"`o'"'
local o `"`B', ylabel(5000, axis())"'
_ax2_run c34 `"`o'"'
local o `"`B', ylabel(5000, axis(1.5))"'
_ax2_run c35 `"`o'"'
local o `"`B', ylabel(5000, axis(2 1))"'
_ax2_run c36 `"`o'"'
local o `"`B', ylabel(5000, axis(#2))"'
_ax2_run c37 `"`o'"'
local o `"`B', ylabel(5000, axis(.))"'
_ax2_run c38 `"`o'"'
local o `"`B', ylabel(5000, axis(1e300))"'
_ax2_run c39 `"`o'"'
local o `"`B', ylabel(5000, axis(2147483648))"'
_ax2_run c40 `"`o'"'
local o `"`B', ylabel(5000, axis(-2147483649))"'
_ax2_run c41 `"`o'"'
local o `"`B', ylabel(5000, axis(-9999999999))"'
_ax2_run c42 `"`o'"'
local o `"`B', ylabels(5000 10000, axis(2))"'
_ax2_run c43 `"`o'"'
local o `"`B', yticks(5000, axis(2))"'
_ax2_run c44 `"`o'"'
local o `"`B', ylines(5000, axis(2))"'
_ax2_run c45 `"`o'"'
local o `"`B', ymticks(5000, axis(2))"'
_ax2_run c46 `"`o'"'
local o `"`B', ymlabels(5000, axis(2))"'
_ax2_run c47 `"`o'"'
local o `"`B', ytitle(TT, size(small),)"'
_ax2_run c48 `"`o'"'
local o `"`B', ytick(5000, axis(2),)"'
_ax2_run c49 `"`o'"'
local o `"`B', ylabel(5000 10000, axis(2) add)"'
_ax2_run c50 `"`o'"'
local o `"`L' ylabel(5000 10000, axis(2)) yscale(log axis(2))"'
_ax2_run c51 `"`o'"'
local o `"twoway (scatter mpg weight, ylabel(5000, axis(2))) (line price weight, yaxis(2) sort)"'
_ax2_run c52 `"`o'"'
local o `"`B', ylabel(5000, axis(2)) ylabel(6000, axis(a))"'
_ax2_run c53 `"`o'"'
local o `"`B', ylabel(5000, axis(1))"'
_ax2_run c54 `"`o'"'

* ---- the x family on the dual-x graph X ----
local o `"`X'"'
_ax2_run x1 `"`o'"'
local o `"`X', xlabel(150 200, axis(2))"'
_ax2_run x2 `"`o'"'
local o `"`X', xscale(log axis(2))"'
_ax2_run x3 `"`o'"'
local o `"`X', xline(200, axis(2))"'
_ax2_run x4 `"`o'"'
local o `"`X', xtick(160 180, axis(2))"'
_ax2_run x5 `"`o'"'
local o `"`X', xmlabel(170, axis(2))"'
_ax2_run x6 `"`o'"'
local o `"`X', xmtick(170, axis(2))"'
_ax2_run x7 `"`o'"'
local o `"`X', xtitle(V, axis(2))"'
_ax2_run x8 `"`o'"'
local o `"`X', xt(V, ax(2))"'
_ax2_run x9 `"`o'"'
local o `"`X', xlabel(2000 3000) xlabel(150 200, axis(2))"'
_ax2_run x10 `"`o'"'
local o `"`X', xlabels(150 200, axis(2))"'
_ax2_run x11 `"`o'"'
local o `"`X', xline(200, axis(2)) xline(3000)"'
_ax2_run x12 `"`o'"'

* ---- refusals, in twoway's order ----
local o `"`S', ylabel(20 30, axis(2))"'
_ax2_run x101 `"`o'"'
local o `"`S', yscale(log axis(2))"'
_ax2_run x102 `"`o'"'
local o `"`B', ylabel(1, axis(3)) xscale(log axis(3))"'
_ax2_run x103 `"`o'"'
local o `"`B', yline(1, axis(3)) ylabel(1, axis(4))"'
_ax2_run x104 `"`o'"'
local o `"`B', ylabel(5000, axis(3) axis(1))"'
_ax2_run x105 `"`o'"'
local o `"`B', ylabel(5000, axis(1) axis(3))"'
_ax2_run x106 `"`o'"'
local o `"`B', ylabel(5000, AXIS(3))"'
_ax2_run x107 `"`o'"'
local o `"`B', ytitle(T, AXIS(2))"'
_ax2_run x108 `"`o'"'
local o `"`B', ylabel(5000, Axis(2))"'
_ax2_run x109 `"`o'"'
local o `"`L' ylabel(5000, AXIS(2))"'
_ax2_run x110 `"`o'"'
local o `"`B', ylabel(5000, AXIS(2) axis(3))"'
_ax2_run x111 `"`o'"'
local o `"`B', ylabel(5000, axis(2)) yscale(axis(3))"'
_ax2_run x112 `"`o'"'
local o `"twoway (scatter mpg weight, ylabel(1, axis(3))) (line price weight, yaxis(2) sort), yscale(log axis(4))"'
_ax2_run x113 `"`o'"'
local o `"`B', ytitle(T, axis(3)) ylabel(1, AXIS(2))"'
_ax2_run x114 `"`o'"'
local o `"twoway (scatter mpg weight, ylabel(1, axis(3))) (line price weight, yaxis(2) sort), ylabel(1, axis(4))"'
_ax2_run x115 `"`o'"'
local o `"twoway scatter mpg weight || line price weight, yaxis(2) sort ylabel(1, axis(5)) || , ylabel(1, axis(4))"'
_ax2_run x116 `"`o'"'
local o `"`S', yline(20, axis(2))"'
_ax2_run x117 `"`o'"'
local o `"`S', ytick(20 30, axis(2))"'
_ax2_run x118 `"`o'"'
local o `"`S', ymlabel(20 30, axis(2))"'
_ax2_run x119 `"`o'"'
local o `"`S', ymtick(20 30, axis(2))"'
_ax2_run x120 `"`o'"'
local o `"`S', ytitle(T, axis(2))"'
_ax2_run x121 `"`o'"'
local o `"`B', ylabel(5000, axis(0))"'
_ax2_run x122 `"`o'"'
local o `"`B', ylabel(5000, axis(-1))"'
_ax2_run x123 `"`o'"'
local o `"`B', ylabel(5000, axis(10))"'
_ax2_run x124 `"`o'"'
local o `"`B', xlabel(2000, axis(2))"'
_ax2_run x125 `"`o'"'
local o `"`L' ytitle(T)"'
_ax2_run x126 `"`o'"'
local o `"`S', ytitle("T", axis(2))"'
_ax2_run x127 `"`o'"'

* ---- integer bounds and double commas ----
local o `"`B', ylabel(5000, axis(2147483647))"'
_ax2_run x201 `"`o'"'
local o `"`B', ylabel(5000, axis(-2147483648))"'
_ax2_run x202 `"`o'"'
local o `"`B', ylabel(5000, axis(1e9))"'
_ax2_run x203 `"`o'"'
local o `"`B', ylabel(5000, axis(-0))"'
_ax2_run x204 `"`o'"'
local o `"`B', ylabel(5000, axis(1e1))"'
_ax2_run x205 `"`o'"'
local o `"`B', yscale(log, axis(2))"'
_ax2_run x206 `"`o'"'
local o `"`B', ytitle(TT, size(small), axis(2))"'
_ax2_run x207 `"`o'"'
local o `"`B', yline(5000, lcolor(red), axis(2))"'
_ax2_run x208 `"`o'"'
local o `"`B', ylabel(5000, angle(0), axis(2))"'
_ax2_run x209 `"`o'"'
local o `"`B', ytick(20 30, grid, axis(1))"'
_ax2_run x210 `"`o'"'
local o `"`B', ytitle(TT, size(small), color(red))"'
_ax2_run x211 `"`o'"'
local o `"`B', yscale(log, range(1 50))"'
_ax2_run x212 `"`o'"'
local o `"`B', yscale(, log)"'
_ax2_run x213 `"`o'"'
local o `"`B', yline(20, lcolor(red), lwidth(thick))"'
_ax2_run x214 `"`o'"'

* ---- by(): each panel's second axis ----
local o `"`B', by(foreign) ylabel(5000 10000, axis(2))"'
_ax2_run gb `"`o'"'

* ---- r1: 10,000 copies (too many options) ----
local many ""
forvalues i = 1/10000 {
    local many "`many' ylabel(1, axis(2))"
}
local o `"`B',`many'"'
_ax2_run r1 `"`o'"'

file close ax2rec

* ---- the data the probes were measured on, for the pytest twins ----
sysuse auto, clear
keep mpg weight price length foreign
global AX2_DATA "${AX2_WORK}/axis2_data.csv"
quietly export delimited using "${AX2_DATA}", replace nolabel

python:
import json, os, re
from sfi import Macro

repo = Macro.getGlobal("W29_REPO")
work = Macro.getGlobal("AX2_WORK")
rec = Macro.getGlobal("AX2_REC")

def _num(s):
    s = s.strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return s

def _first_error(pid):
    path = os.path.join(work, pid + ".log")
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = [ln.rstrip("\n") for ln in fh]
    except OSError:
        return ""
    # The command runs inside a program, so nothing is echoed: under
    # capture noisily the log holds only what the command printed, and a
    # refusal's message is its first non-blank line.
    for ln in lines:
        if ln.strip():
            return ln.strip()
    return ""

probes = []
cur = None
with open(rec, encoding="utf-8", errors="replace") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if not line:
            continue
        kind, rest = line.split("|", 1)
        if kind == "P":
            pid, rc, secs, cmd = rest.split("|", 3)
            if len(cmd) > 2000:
                cmd = cmd[:200] + " ... (%d characters)" % len(cmd)
            cur = {"id": pid, "command": cmd, "rc": int(rc),
                   "seconds": float(secs) if secs.strip() else None,
                   "error": _first_error(pid) if int(rc) else "",
                   "axes": {}, "plotregions": [], "panels": []}
            probes.append(cur)
        elif kind == "A":
            ax, st, vals = rest.split("|", 2)
            cur["axes"].setdefault(ax, {})[st] = [float(v) for v in vals.split()]
        elif kind == "R":
            f = rest.split("|")
            cur["plotregions"].append({
                "index": int(f[0]),
                "yaxis_dexes": f[1].split(), "xaxis_dexes": f[2].split(),
                "y": {"curmin": _num(f[3]), "curmax": _num(f[4]),
                      "transform": f[5], "reverse": _num(f[6])},
                "x": {"curmin": _num(f[7]), "curmax": _num(f[8]),
                      "transform": f[9], "reverse": _num(f[10])},
                "lines": []})
        elif kind == "L":
            j, z, o = rest.split("|")
            for pr in cur["plotregions"]:
                if pr["index"] == int(j):
                    pr["lines"].append({"z": float(z), "orientation": o})
        elif kind == "G":
            k, vals = rest.split("|", 1)
            cur["panels"].append({"panel": int(k),
                                  "yaxis2_major": [float(v) for v in vals.split()]})

import csv
data = {}
with open(Macro.getGlobal("AX2_DATA"), encoding="utf-8") as fh:
    for row in csv.DictReader(fh):
        for k, v in row.items():
            data.setdefault(k, []).append(float(v) if v.strip() else None)

out = {
    "data": data,
    "_meta": {
        "stata_version": Macro.getLocal("stata_version"),
        "born_date": Macro.getLocal("born_date"),
        "dash_commit": Macro.getLocal("dash_commit").strip(),
        "extracted": Macro.getLocal("extracted"),
        "method": ".Graph members via graph_g.class ParseAndLogAxes "
                  "(scripts/extract_axis2_truth.do)",
        "caveats": ["twoway prints a broken message and r(133) for a refused "
                    "value holding a double quote"],
    },
    "probes": probes,
}
path = os.path.join(repo, "test", "fixtures", "axis2_truth.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote %s (%d probes)" % (path, len(probes)))
end
