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
*! WP-47 basic:PT-15 (47-06-07) adds, selected alone with the environment
*! variable MF_ONLY=PT15 (the other probes' records are then kept from the
*! committed fixture):
*!   E01  rarea yl yh weight (sorted, in 1/10): the outline's paths;
*!   E02  the same under cmissing(n) with yl missing in row 5;
*!   H01  pcscatter mpg weight trunk turn in 1/5, mlabel(make), turn
*!        missing in row 2: markers and label texts; H02 the same on
*!        pccapsym;
*!   A01  pcarrow ... mlabangle(400): rc, lines printed, labels;
*!   L01  scatter mpg weight in 1/5, mlabel(d), d %td with a value label
*!        on two of its values: the label texts;
*!   I01  scatteri 1 1 2 2 3 and I02 pci 0 0 0 1 1 1 2: lines printed;
*!   K01  a scheme file holding only "color p1 navy" (written to
*!        c(tmpdir), on the ado-path for this session only, erased after):
*!        scatter mpg weight, yline(20): the refline's stroke, lines;
*!   X01  title("{stSymbol:a} {col 5:x}"): the title's text.
*! The zero- and missing-weight dot (DG-12) is weighted_markers_truth.json
*! W06_zero/W06_mis: no probe here.
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
local mf_only : environment MF_ONLY
global MF_ONLY `"`mf_only'"'
if `"`mf_only'"' == "" {
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
}

* ---- WP-47 basic:PT-15 (47-06-07) ----
if inlist(`"`mf_only'"', "", "PT15") {
sysuse auto, clear
keep in 1/10
sort weight
generate yl = mpg - 5
generate yh = mpg + 5
_mf_probe E01 twoway rarea yl yh weight, fcolor(gs14) lcolor(`M') legend(off)
replace yl = . in 5
_mf_probe E02 twoway rarea yl yh weight, fcolor(gs14) lcolor(`M') cmissing(n) legend(off)

sysuse auto, clear
keep in 1/5
replace turn = . in 2
_mf_probe H01 twoway pcscatter mpg weight trunk turn, mcolor(`M') mlabel(make) legend(off)
_mf_probe H02 twoway pccapsym mpg weight trunk turn, mcolor(`M') lcolor(blue) mlabel(make) legend(off)
sysuse auto, clear
keep in 1/5
_mf_probe A01 twoway pcarrow mpg weight trunk turn, mlabel(make) mlabangle(400) lcolor(`M') mcolor(`M') legend(off)

sysuse auto, clear
keep in 1/5
generate d = mdy(1, _n, 2001)
format d %td
label define q4706d 14976 "first" 14978 "third"
label values d q4706d
_mf_probe L01 twoway scatter mpg weight, mlabel(d) legend(off)

clear
_mf_probe I01 twoway scatteri 1 1 2 2 3, mcolor(`M')
_mf_probe I02 twoway pci 0 0 0 1 1 1 2, lcolor(`M')

* A scheme of one key, on the session's ado-path only (never set scheme).
local sdir "`c(tmpdir)'dash_q4706_scheme"
capture mkdir "`sdir'"
tempname sch
file open `sch' using "`sdir'/scheme-q4706.scheme", write text replace
file write `sch' "color p1 navy" _n
file close `sch'
adopath ++ "`sdir'"
sysuse auto, clear
_mf_probe K01 twoway scatter mpg weight, yline(20) scheme(q4706)
_mf_probe K01ref twoway scatter mpg weight, yline(20) scheme(s2color)
adopath - "`sdir'"
capture erase "`sdir'/scheme-q4706.scheme"
capture rmdir "`sdir'"

sysuse auto, clear
_mf_probe X01 twoway scatter mpg weight, title("{stSymbol:a} {col 5:x}")
}

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
import html as _html
mf_only = Macro.getGlobal("MF_ONLY")
dest = os.path.join(repo, "test", "fixtures", "marker_fidelity_truth.json")
if mf_only:
    # One group re-run: the other probes' records stay as committed.
    with open(dest, encoding="utf-8") as fh:
        _old = json.load(fh)
    _old["_meta"] = out["_meta"]
    out = _old

strip = lambda els: [(e["kind"], e["fill"], e["stroke"], e["extent"],
                      e["center"]) for e in els]


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


if not mf_only:
    txt = log_text("S17")
    m = re.search(r"\(note:\s+(named style .*? not found in class \w+[^)]*)\)",
                  txt)
    out["S17"] = {"rc": rcs["S17"],
                  "note": m.group(1).strip() if m else "",
                  "markers": len(svg_layer.markers(mag("S17"))),
                  "equals_default": strip(mag("S17")) == strip(mag("S17ref"))}
    out["B01"] = bars("B01")
    out["B02"] = bars("B02")
    for k in ("R01", "R02"):
        # A dot is a magenta fill circle (its ring is a second, stroked
        # one); dot y x draws each observation's row of dots up its x.
        circ = [e for e in mag(k)
                if e["kind"] == "circle" and e["fill"] == MAG]
        out[k] = {"rc": rcs[k], "dots": len(circ),
                  "rows": len({e["center"][0] for e in circ})}


def lines_printed(key):
    """What the command printed: the log less its header, footer, echoed
    commands and blank lines."""
    p = os.path.join(pdir, key + ".log")
    keep = []
    with open(p, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            t = ln.strip()
            if not t or t.startswith((".", ">", "name:", "log:",
                                      "log type:", "opened on:",
                                      "closed on:", "---")):
                continue
            keep.append(t)
    return keep


def texts(key):
    """Every <text> element's text, tags stripped, in document order."""
    p = os.path.join(pdir, key + ".svg")
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as fh:
        svg = fh.read()
    return [_html.unescape(re.sub(r"<[^>]+>", "", t)).strip()
            for t in re.findall(r"<text\b[^>]*>(.*?)</text>", svg, re.S)]


def strokes(key, colour=MAG):
    """Every element stroked in *colour*: kind, points, width."""
    p = os.path.join(pdir, key + ".svg")
    if not os.path.exists(p):
        return []
    return [{"kind": e["kind"], "fill": e["fill"],
             "stroke_width": e["stroke_width"], "points": e["points"]}
            for e in svg_layer.svg_elements(p) if e["stroke"] == colour]


if mf_only in ("", "PT15"):
    makes = ["AMC Concord", "AMC Pacer", "AMC Spirit", "Buick Century",
             "Buick Electra"]
    for k in ("E01", "E02"):
        p = os.path.join(pdir, k + ".svg")
        fills = [{"kind": e["kind"], "points": e["points"]}
                 for e in svg_layer.svg_elements(p)
                 if e["fill"] not in (None, "none", MAG)
                 and e["kind"] == "path"]
        out[k] = {"rc": rcs[k], "outline": strokes(k), "fill": fills}
    for k in ("H01", "H02", "A01"):
        tx = texts(k)
        out[k] = {"rc": rcs[k], "lines": lines_printed(k),
                  "labels": [t for t in tx if t in makes],
                  "markers": len(svg_layer.markers(
                      [e for e in mag(k) if e["kind"] == "circle"])),
                  "segments": strokes(k, "#0000ff") + strokes(k)}
    out["L01"] = {"rc": rcs["L01"], "texts": texts("L01")}
    for k in ("I01", "I02"):
        out[k] = {"rc": rcs[k], "lines": lines_printed(k),
                  "marked": len(mag(k))}
    for k in ("K01", "K01ref"):
        p = os.path.join(pdir, k + ".svg")
        els = svg_layer.svg_elements(p) if os.path.exists(p) else []
        # The refline: a horizontal two-point stroke across the plot.
        flat = [{"stroke": e["stroke"], "stroke_width": e["stroke_width"],
                 "points": e["points"]} for e in els
                if e["kind"] in ("line", "path") and len(e["points"]) == 2
                and e["points"][0][1] == e["points"][1][1]]
        out[k] = {"rc": rcs[k], "lines": lines_printed(k), "flat": flat,
                  "marker_fill": sorted({e["fill"] for e in els
                                         if e["kind"] == "circle"})}
    out["X01"] = {"rc": rcs["X01"], "texts": texts("X01"),
                  "lines": lines_printed("X01")}

with open(dest, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote", dest)
end
