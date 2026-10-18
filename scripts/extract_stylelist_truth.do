* extract_stylelist_truth.do -- twoway's reading of a stylelist across an
* expanded varlist (WP-30 P1.1a, section 11), written to
* test/fixtures/stylelist_truth.json for test/test_stylelists.py.
*
* Each case runs `twoway <cmd>' under s2color; the record keeps its rc, its
* first error line and its notes from a text log, and, when it drew, the
* marker fills (circle, path and polygon; a triangle is a polygon), the
* stroke colours of its lines and paths and the circle radii of its SVG, in
* document order.
*
* Run (never the GUI; the slot wrapper of scripts/stata_slot.sh):
*   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_stylelist_truth.do
* The SVG and log files are written to the current directory (the slot
* wrapper's scratch directory).

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_stylelist_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_stylelist_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1

clear all
set more off
set linesize 255
version 19
local entry_scheme "`c(scheme)'"
set scheme s2color

local stata_version = c(stata_version)
local born_date "`c(born_date)'"
tempfile gh
shell git -C "`repo'" rev-parse HEAD > "`gh'"
tempname fh
file open `fh' using "`gh'", read text
file read `fh' dash_commit
file close `fh'
local extracted "`c(current_date)'"
local svgdir "`c(pwd)'"

tempfile records
tempname rf
file open `rf' using "`records'", write text replace

capture program drop _sl_case
program _sl_case
    // _sl_case id data cmd: run twoway cmd on auto or sp500, logging it,
    // and append id|rc|svg|log to the record file.
    args id data cmd
    if "`data'" == "sp500" {
        quietly sysuse sp500, clear
        quietly tsset date
    }
    else quietly sysuse auto, clear
    local log "`c(pwd)'/sl_`id'.log"
    local svg ""
    capture graph drop g
    quietly log using "`log'", text replace name(sltruth)
    capture noisily twoway `macval(cmd)'
    local rc = _rc
    quietly log close sltruth
    if !`rc' {
        local svg "`c(pwd)'/sl_`id'.svg"
        quietly graph export "`svg'", replace name(g)
    }
    file write $SL_RF "`id'|`rc'|`svg'|`log'" _n
    mata: st_global("SL_CMD_`id'", st_local("cmd"))
end
global SL_RF `rf'

_sl_case CTRL3 auto `"scatter mpg turn trunk weight, name(g, replace)"'
_sl_case T01 auto `"scatter mpg turn weight, mcolor(red blue) msymbol(O T) name(g, replace)"'
_sl_case T02 auto `"scatter mpg turn weight, mcolor(red) name(g, replace)"'
_sl_case T03 auto `"scatter mpg turn trunk weight, mcolor(red blue) name(g, replace)"'
_sl_case T04 auto `"scatter mpg turn weight, mcolor(red blue green) name(g, replace)"'
_sl_case T05 auto `"scatter mpg turn weight, mcolor(. blue) name(g, replace)"'
_sl_case T06 auto `"scatter mpg turn trunk weight, mcolor(red = blue) name(g, replace)"'
_sl_case T07 auto `"scatter mpg turn trunk weight, mcolor(red ..) name(g, replace)"'
_sl_case T08 auto `"scatter mpg turn trunk weight, mcolor(red ...) name(g, replace)"'
_sl_case T12 auto `"scatter mpg turn weight, mcolor(= blue) name(g, replace)"'
_sl_case T13 auto `"scatter mpg turn trunk weight, mcolor(red..) name(g, replace)"'
_sl_case T14 auto `"scatter mpg turn trunk weight, mcolor(red....) name(g, replace)"'
_sl_case T15 auto `"scatter mpg turn trunk weight, mcolor(. ..) name(g, replace)"'
_sl_case T16 auto `"scatter mpg turn trunk weight, mcolor(red . =) name(g, replace)"'
_sl_case T17 auto `"scatter mpg turn trunk weight, mcolor(red = = blue) name(g, replace)"'
_sl_case T18 auto `"scatter mpg turn trunk weight, mcolor(..) name(g, replace)"'
_sl_case T11 auto `"scatter mpg turn weight, mcolor("255 0 0" "0 0 255") name(g, replace)"'
_sl_case T20 auto `"scatter mpg turn weight, mcolor(`"red"' blue) name(g, replace)"'
_sl_case T21 auto `"scatter mpg turn weight, mcolor("" blue) name(g, replace)"'
_sl_case T22 auto `"scatter mpg turn weight, mcolor(red `""') name(g, replace)"'
_sl_case T23 auto `"scatter mpg turn weight, mcolor(red) mcolor("") name(g, replace)"'
_sl_case T24 auto `"scatter mpg turn weight, mcolor(red "..") name(g, replace)"'
_sl_case T25 auto `"scatter mpg turn weight, mcolor(navy*.5 red%50) name(g, replace)"'
_sl_case Y01 auto `"scatter mpg turn weight, mcolor(255 0 0) name(g, replace)"'
_sl_case U20 auto `"scatter mpg turn weight, mcolor(red blue) mfcolor(green) name(g, replace)"'
_sl_case U21 auto `"scatter mpg turn weight, msize(large) name(g, replace)"'
_sl_case U19 auto `"scatter mpg turn weight, mcolor(red) mcolor(blue green) name(g, replace)"'
_sl_case W21 auto `"scatter mpg turn weight, mcolor(red blue) mcolor(green) name(g, replace)"'
_sl_case P16 auto `"scatter mpg turn weight, mcolor(red .. blue) mcolor(green) name(g, replace)"'
_sl_case BY auto `"scatter mpg turn weight, mcolor(red blue) by(foreign) name(g, replace)"'
_sl_case PN auto `"(scatter mpg turn weight, mcolor(red blue)) (scatter price weight), name(g, replace)"'
_sl_case T10 auto `"line mpg turn weight, sort lpattern(solid dash) lcolor(red blue) name(g, replace)"'
_sl_case W30 auto `"connected mpg turn weight, sort lcolor(red) clcolor(. blue) name(g, replace)"'
_sl_case W36 auto `"line mpg turn trunk weight, sort lcolor(red) lpattern(. dash) name(g, replace)"'
_sl_case U40 sp500 `"tsline open close, lcolor(red blue) lpattern(solid dash) name(g, replace)"'
_sl_case T09 auto `"scatter mpg weight, mcolor(red blue) name(g, replace)"'
_sl_case T19 auto `"scatter mpg weight, msymbol(T O) name(g, replace)"'
_sl_case T26 auto `"lfit mpg weight, lcolor(red blue) name(g, replace)"'
_sl_case T27 auto `"area mpg weight, sort color(red blue) name(g, replace)"'
_sl_case T28 auto `"rcap mpg turn weight, lcolor(red blue) name(g, replace)"'
_sl_case T29 auto `"lfitci mpg weight, lcolor(red green) fcolor(green red) name(g, replace)"'
_sl_case T30 auto `"lfitci mpg weight, acolor(red blue) name(g, replace)"'
_sl_case T31 auto `"histogram mpg, color(red blue) name(g, replace)"'
_sl_case T32 auto `"scatteri 20 3000 25 4000, mcolor(red blue) name(g, replace)"'
_sl_case T33 auto `"function y=x, range(0 1) lcolor(red blue) name(g, replace)"'
_sl_case T34 auto `"bar mpg turn weight, bfcolor(red blue) name(g, replace)"'
_sl_case R01 auto `"scatter mpg turn weight, mcolor(red .. blue) name(g, replace)"'
_sl_case R02 auto `"scatter mpg turn weight, mc(red .. blue) name(g, replace)"'
_sl_case R03 auto `"scatter mpg weight, mcolor(red .. blue) name(g, replace)"'
_sl_case R04 auto `"scatter mpg turn weight, msymbol(O .. T) name(g, replace)"'
_sl_case R05 auto `"scatter mpg turn weight, mcolor(red .. ..) name(g, replace)"'
_sl_case R06 auto `"scatter mpg turn weight, mcolor(red.. ..) name(g, replace)"'
_sl_case R07 auto `"scatter mpg turn weight, mcolor(.. red) name(g, replace)"'
_sl_case R08 auto `"scatter mpg turn weight, mcolor("red" .. "blue") name(g, replace)"'
_sl_case R09 auto `"scatter mpg turn weight, mcolor(red ..) mcolor(blue .. green) name(g, replace)"'
_sl_case R10 auto `"line mpg turn weight, lwidth(thick 20000) name(g, replace)"'
_sl_case R11 auto `"line mpg weight, lwidth(thick 20000) name(g, replace)"'
_sl_case R12 auto `"scatter mpg turn weight, msangle(0 500) name(g, replace)"'
_sl_case R13 auto `"scatter mpg weight, msangle(0 500) name(g, replace)"'
_sl_case R14 auto `"scatter mpg turn weight, mcolor(red " ") name(g, replace)"'
_sl_case R15 auto `"scatter mpg weight, mcolor(red " ") name(g, replace)"'
_sl_case R16 auto `"scatter mpg turn weight, mcolor(  red   ..   blue  ) name(g, replace)"'
_sl_case G01 auto `"scatter mpg turn trunk weight, mcolor(red=blue) name(g, replace)"'
_sl_case G02 auto `"scatter mpg turn trunk weight, mcolor(red= blue) name(g, replace)"'
_sl_case G03 auto `"scatter mpg turn weight, mcolor((red) blue) name(g, replace)"'

file close `rf'
global SL_RF

python:
import json, os, re, sys
from sfi import Macro
repo = Macro.getLocal("repo")
sys.path.insert(0, os.path.join(repo, "scripts"))
import svg_truth

_EL = re.compile(r"<(circle|path|polygon|line)\b([^>]*)>")


def _paint(a, prop):
    st = svg_truth._style_of(a)
    v = st.get(prop, a.get(prop))
    return v.lower() if isinstance(v, str) else v


def _svg(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        txt = fh.read()
    markers, strokes, radii = [], [], {}
    for m in _EL.finditer(txt):
        kind = m.group(1)
        a = svg_truth._attrs(m.group(2))
        fill = _paint(a, "fill")
        stroke = _paint(a, "stroke")
        if kind in ("circle", "path", "polygon") and fill and fill != "none":
            if markers and markers[-1][0] == fill:
                markers[-1][1] += 1
                markers[-1][2][kind] = markers[-1][2].get(kind, 0) + 1
            else:
                markers.append([fill, 1, {kind: 1}])
            if kind == "circle":
                r = a.get("r")
                if r is not None:
                    radii.setdefault(fill, set()).add(r)
        if kind in ("line", "path") and stroke and stroke != "none" and not (kind == "path" and fill and fill != "none"):
            nl, np_ = (1, 0) if kind == "line" else (0, 1)
            if strokes and strokes[-1][0] == stroke:
                strokes[-1][1] += nl
                strokes[-1][2] += np_
            else:
                strokes.append([stroke, nl, np_])
    fills = [[c, d["n"]] for c, d in svg_truth.svg_fills(path, elements=("rect", "path")).items() if d["n"] < 1000]
    return dict(markers=markers, strokes=strokes, fills=fills,
                radii={c: sorted(v) for c, v in radii.items()})


def _log(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = [ln.rstrip("\n") for ln in fh]
    notes = [ln.strip() for ln in lines if ln.strip().startswith("(note:")]
    message = ""
    for ln in lines:
        s = ln.strip()
        if (not s or s.startswith("(note:") or re.match(r"^r\(\d+\);$", s)
                or s.startswith("name:") or s.startswith("log:")
                or s.startswith("log type:") or s.startswith("opened on:")
                or s.startswith("closed on:") or s.startswith("---")):
            continue
        message = s
        break
    return message, notes


cases = {}
with open(Macro.getLocal("records"), encoding="utf-8") as fh:
    for ln in fh:
        cid, rc, svg, log = ln.rstrip("\n").split("|")
        rec = {"cmd": Macro.getGlobal("SL_CMD_" + cid), "rc": int(rc)}
        rec["message"], rec["notes"] = _log(log)
        if svg:
            rec.update(_svg(svg))
        cases[cid] = rec
meta = {"stata_version": Macro.getLocal("stata_version"),
        "born_date": Macro.getLocal("born_date"),
        "source": "scripts/extract_stylelist_truth.do",
        "dash_commit": Macro.getLocal("dash_commit"),
        "extracted": Macro.getLocal("extracted")}
out = os.path.join(repo, "test", "fixtures", "stylelist_truth.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump({"cases": cases, "scheme": "s2color", "_meta": meta}, fh,
              indent=2, sort_keys=True)
    fh.write("\n")
print("wrote " + out)
end

set scheme `entry_scheme'
