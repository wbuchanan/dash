*! extract_marker_fidelity_truth.do
*! WP-47 47-06 (PIC-2, PIC-9, PIC-10): twoway's invisible symbol, empty
*! histogram bins and dot rows with a missing value.
*!
*! The marker shapes themselves (D, V, +, the arrows) are measured by
*! scripts/extract_symbol_pattern_truth.do (symbol_pattern_truth.json
*! sym.*); this script adds what that one does not hold:
*!   S17  msymbol(invisible): rc, the note, and whether the SVG's magenta
*!        elements equal the default symbol's;
*!   B01  histogram mpg, bin(30): bars drawn, zero-count bins;
*!   B02  histogram rep78, discrete: the same;
*!   R01  dot close date in 1/45 (sp500, close missing in row 3): dots;
*!   R02  the same with dotextend(no).
*! The trailing python: block writes test/fixtures/marker_fidelity_truth.json,
*! never calls Stata and starts no subprocess.
*!
*! Run (Stata only through the slot wrapper, never the GUI):
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> \
*!       <repo>/scripts/extract_marker_fidelity_truth.do

* Root: DASH_REPO, else the current directory when it is a dash tree.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_marker_fidelity_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_marker_fidelity_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
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

global MF_REPO "`repo'"
local work "`c(tmpdir)'dash_marker_fidelity_probe"
capture mkdir "`work'"
global MF_PDIR "`work'"

local stata_version = c(stata_version)
local born_date "`c(born_date)'"
local extracted "`c(current_date)' `c(current_time)'"
tempfile mfgit
quietly shell git -C "${MF_REPO}" rev-parse HEAD > "`mfgit'"
tempname mfgh
file open `mfgh' using "`mfgit'", read text
file read `mfgh' mfline
file close `mfgh'
local dash_commit = trim(`"`mfline'"')

tempname reg
file open `reg' using "${MF_PDIR}/registry.txt", write text replace
global MF_REG `reg'

capture program drop _mf_probe
program define _mf_probe
    version 19
    gettoken key 0 : 0
    local command = strtrim(`"`macval(0)'"')
    graph drop _all
    capture log close mf_probe
    log using "${MF_PDIR}/`key'.log", text replace name(mf_probe)
    capture noisily `command'
    local rc = _rc
    log close mf_probe
    capture erase "${MF_PDIR}/`key'.svg"
    if `rc' == 0 {
        graph export "${MF_PDIR}/`key'.svg", as(svg) replace
    }
    file write ${MF_REG} `"`key'"' _tab `"`rc'"' _n
end

local M `""255 0 255""'
sysuse auto, clear
keep in 1/3
_mf_probe S17 twoway scatter mpg weight, msymbol(invisible) mcolor(`M') legend(off)
_mf_probe S17ref twoway scatter mpg weight, mcolor(`M') legend(off)

sysuse auto, clear
_mf_probe B01 twoway histogram mpg, bin(30) fcolor(`M') lcolor(`M')
_mf_probe B02 twoway histogram rep78, discrete fcolor(`M') lcolor(`M')

sysuse sp500, clear
keep in 1/45
replace close = . in 3
_mf_probe R01 twoway dot close date, mcolor(blue) dcolor(`M') ndots(75)
_mf_probe R02 twoway dot close date, mcolor(blue) dcolor(`M') ndots(75) dotextend(no)

file close ${MF_REG}

python:
import json, os, sys
from sfi import Macro

repo = Macro.getGlobal("MF_REPO")
pdir = Macro.getGlobal("MF_PDIR")
sys.path.insert(0, os.path.join(repo, "scripts"))
import svg_layer

MAG = "#ff00ff"

def mag(key):
    p = os.path.join(pdir, key + ".svg")
    if not os.path.exists(p):
        return []
    return [e for e in svg_layer.svg_elements(p)
            if e["fill"] == MAG or e["stroke"] == MAG]

def log_text(key):
    p = os.path.join(pdir, key + ".log")
    with open(p, encoding="utf-8", errors="replace") as fh:
        return " ".join(ln.strip() for ln in fh)

rcs = {}
with open(os.path.join(pdir, "registry.txt"), encoding="utf-8") as fh:
    for ln in fh:
        k, rc = ln.rstrip("\n").split("\t")
        rcs[k] = int(rc)

out = {"_meta": {
    "stata_version": Macro.getLocal("stata_version"),
    "born_date": Macro.getLocal("born_date"),
    "dash_commit": Macro.getLocal("dash_commit"),
    "extracted": Macro.getLocal("extracted"),
    "source": "scripts/extract_marker_fidelity_truth.do",
}}

import re
txt = log_text("S17")
m = re.search(r"\(note:\s+(named style .*? not found in class \w+[^)]*)\)", txt)
strip = lambda els: [(e["kind"], e["fill"], e["stroke"], e["extent"],
                      e["center"]) for e in els]
out["S17"] = {"rc": rcs["S17"], "note": m.group(1).strip() if m else "",
              "markers": len(svg_layer.markers(mag("S17"))),
              "equals_default": strip(mag("S17")) == strip(mag("S17ref"))}

def bars(key):
    """Bars of a histogram: magenta rects (or 4-point paths/polygons)."""
    els = [e for e in mag(key) if e["kind"] in ("rect", "polygon", "path")]
    hs = []
    for e in els:
        ys = [p[1] for p in e["points"]]
        hs.append(round(max(ys) - min(ys), 2))
    filled = [e for e in els if e["fill"] == MAG]
    return {"rc": rcs[key], "elements": len(els), "bars": len(filled),
            "zero_height": sum(1 for h in hs if h <= 0.01)}

out["B01"] = bars("B01")
out["B02"] = bars("B02")
for k in ("R01", "R02"):
    # A dot is a magenta fill circle (its ring is a second, stroked one);
    # dot y x draws each observation's row of dots up its x.
    circ = [e for e in mag(k) if e["kind"] == "circle" and e["fill"] == MAG]
    out[k] = {"rc": rcs[k], "dots": len(circ),
              "rows": len({e["center"][0] for e in circ})}

dest = os.path.join(repo, "test", "fixtures", "marker_fidelity_truth.json")
with open(dest, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote", dest)
end
