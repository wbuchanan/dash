*! extract_series_label_truth.do
*! WP-30 section 19 (P1.16): ground truth for the legend keys and default
*! axis titles twoway gives each plot type, for
*! test/fixtures/series_label_truth.json.
*!
*! WHY THIS EXISTS
*!
*! dash keyed every fit "Fitted values", range layers by their first
*! boundary, pc and immediate layers by their type name, and titled each
*! axis from its first layer.  twoway keys each series in its own text and
*! titles an axis with its first series' label only when its last series'
*! label is the same.  This script runs 150 probes through real Stata
*! (scheme stcolor, sysuse auto and sp500) and records, per probe, twoway's
*! keys (the drawn texts minus the legend(off) twin's, by multiset), its
*! axis objects' titles, the titles its SVG draws, and the spec dash
*! registers for the same command.
*!
*! Output: test/fixtures/series_label_truth.json
*!
*! Run with (the script sets its own directories, so it is handed to the
*! wrapper directly -- CLAUDE.md rule 10):
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_series_label_truth.do
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
    display as error "extract_series_label_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_series_label_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1
global ZK_REPO "`repo'"
global ZK_OUT  "`repo'/test/fixtures/series_label_truth.json"

local work "`c(tmpdir)'dash_series_label_probe"
capture mkdir "`work'"
global ZK_WORK "`work'"
display as text "probe work dir: ${ZK_WORK}"

set scheme stcolor

global ZK_SVER = c(stata_version)
global ZK_BORN = c(born_date)
global ZK_DATE = "`c(current_date)' `c(current_time)'"

// Provenance stamp (D12): shell writes the commit into a file, read back.
tempfile zkgitrev
quietly shell git -C "${ZK_REPO}" rev-parse HEAD > "`zkgitrev'"
tempname zkgfh
file open `zkgfh' using "`zkgitrev'", read text
file read `zkgfh' zkgitline
file close `zkgfh'
global ZK_COMMIT = trim(`"`zkgitline'"')
capture assert ustrregexm(`"${ZK_COMMIT}"', "^[0-9a-f]{40}$")
if _rc {
    display as error "extract_series_label_truth.do: git rev-parse HEAD did not print a 40-character commit"
    exit 498
}

// ---------------------------------------------------------------------------
// The data sets
// ---------------------------------------------------------------------------
capture program drop _zk_auto
program define _zk_auto
    sysuse auto, clear
    gen m2 = mpg
    gen p2 = price
    gen p3 = price
    label variable p3 "Price"
    gen t2 = turn
    label variable t2 "Turn circle (ft.)"
    gen p4 = price
    label variable p4 "Mileage (mpg)"
end

capture program drop _zk_sp
program define _zk_sp
    sysuse sp500, clear
    quietly tsset date
end

// Each data set is exported once, through dash's own writer, with each
// variable's display format.
capture program drop _zk_export
program define _zk_export
    args ds vars
    global ZK_DPATH "${ZK_WORK}/data_`ds'.json"
    global ZK_DVARS "`vars'"
    python: import sys; sys.path.insert(0, __import__("sfi").Macro.getGlobal("ZK_REPO")); import dash_render as _zkdr; _zkm = __import__("sfi").Macro; _zke = _zkdr._dash_write_stata_data(_zkm.getGlobal("ZK_DPATH"), _zkm.getGlobal("ZK_DVARS")); assert _zke == "", _zke
    tempname fh
    file open `fh' using "${ZK_WORK}/formats_`ds'.txt", write text replace
    foreach v of local vars {
        local f : format `v'
        file write `fh' "`v'|`f'" _n
    }
    file close `fh'
end

_zk_auto
_zk_export auto "mpg weight turn length price trunk foreign m2 p2 p3 t2 p4"
_zk_sp
_zk_export sp500 "date close open high low"

// ---------------------------------------------------------------------------
// Registration
// ---------------------------------------------------------------------------
global ZK_N = 0
capture program drop zk
program define zk
    global ZK_N = ${ZK_N} + 1
    global ZK_ID_${ZK_N}   `"`1'"'
    global ZK_DS_${ZK_N}   `"`2'"'
    global ZK_BODY_${ZK_N} `"`3'"'
    global ZK_OPTS_${ZK_N} `"`4'"'
end

zk F01 auto "(scatter mpg weight) (lowess mpg weight)" ""
zk F02 auto "(lowess mpg weight)" "legend(on)"
zk F03 auto "(scatter mpg weight) (lpoly mpg weight)" ""
zk F04 auto "(lpoly mpg weight)" "legend(on)"
zk F05 auto "(scatter mpg weight) (mband mpg weight)" ""
zk F06 auto "(mband mpg weight)" "legend(on)"
zk F07 auto "(scatter mpg weight) (mspline mpg weight)" ""
zk F08 auto "(mspline mpg weight)" "legend(on)"
zk F09 auto "(scatter mpg weight) (function y=20+0.001*x, range(2000 5000))" ""
zk F10 auto "(function y=x^2, range(0 2))" "legend(on)"
zk F11 auto "(scatter mpg weight) (lfit mpg weight)" ""
zk F12 auto "(lfit mpg weight)" "legend(on)"
zk F13 auto "(scatter mpg weight) (qfit mpg weight)" ""
zk F14 auto "(qfit mpg weight)" "legend(on)"
zk F15 auto "(scatter mpg weight) (fpfit mpg weight)" ""
zk F16 auto "(fpfit mpg weight)" "legend(on)"
zk F17 auto "(scatter mpg weight) (lfitci mpg weight)" ""
zk F18 auto "(lfitci mpg weight)" ""
zk F19 auto "(qfitci mpg weight)" ""
zk F20 auto "(fpfitci mpg weight)" ""
zk F21 auto "(scatter mpg weight) (lpolyci mpg weight)" ""
zk F22 auto "(lpolyci mpg weight)" ""
zk F23 auto "(lfit mpg weight) (qfit mpg weight)" ""
zk F24 auto "(lowess mpg weight) (lpoly mpg weight)" ""
zk F25 auto "(scatter m2 weight) (lowess m2 weight)" ""
zk F26 auto "(scatter m2 weight) (lpoly m2 weight)" ""
zk F27 auto "(scatter mpg weight) (function sin(x), range(2000 5000))" ""
zk F28 auto "(scatter mpg weight) (function z=x/100, range(2000 5000))" ""
zk F29 auto "(scatter mpg weight) (lowess mpg weight) (lowess mpg weight, bwidth(0.3))" ""
zk F30 auto "(mband mpg weight) (mspline mpg weight)" ""
zk F31 auto "(scatter mpg weight) (lpolyci mpg weight) (lfitci mpg weight)" ""
zk F32 auto "(scatter mpg weight) (lpoly mpg weight, kernel(biweight) degree(2))" ""
zk U01 auto "(histogram mpg)" "legend(on)"
zk U02 auto "(kdensity mpg)" "legend(on)"
zk U03 auto "(histogram mpg) (kdensity mpg)" ""
zk R01 auto "(rarea mpg turn weight)" "legend(on)"
zk R02 auto "(rbar mpg turn weight)" "legend(on)"
zk R03 auto "(rspike mpg turn weight)" "legend(on)"
zk R04 auto "(rcap mpg turn weight)" "legend(on)"
zk R05 auto "(rcapsym mpg turn weight)" "legend(on)"
zk R06 auto "(rscatter mpg turn weight)" "legend(on)"
zk R07 auto "(rline mpg turn weight)" "legend(on)"
zk R08 auto "(rconnected mpg turn weight)" "legend(on)"
zk R09 auto "(rarea mpg turn weight) (scatter mpg weight)" ""
zk R10 auto "(rcap mpg turn weight) (scatter price weight)" ""
zk R11 auto "(rcap m2 p2 weight)" "legend(on)"
zk R12 auto "(rcap mpg mpg weight)" "legend(on)"
zk R13 auto "(rcap mpg turn weight) (rcap turn mpg weight)" ""
zk P01 auto "(pcspike mpg weight turn length)" "legend(on)"
zk P02 auto "(pccapsym mpg weight turn length)" "legend(on)"
zk P03 auto "(pcarrow mpg weight turn length)" "legend(on)"
zk P04 auto "(pcbarrow mpg weight turn length)" "legend(on)"
zk P05 auto "(pcscatter mpg weight turn length)" "legend(on)"
zk P06 auto "(scatter mpg weight) (pcspike mpg weight turn length)" ""
zk P07 auto "(pcspike m2 weight p2 length)" "legend(on)"
zk I01 auto "(scatteri 20 3000 25 3500)" "legend(on)"
zk I02 auto "(pci 20 3000 25 3500)" "legend(on)"
zk I03 auto "(pcarrowi 20 3000 25 3500)" "legend(on)"
zk I04 auto "(scatter mpg weight) (scatteri 20 3000 25 3500)" ""
zk I05 auto "(scatter mpg weight) (pci 20 3000 25 3500)" ""
zk I06 auto "(scatter mpg weight) (pcarrowi 20 3000 25 3500)" ""
zk D01 auto "(line mpg weight, sort)" "legend(on)"
zk D02 auto "(bar mpg weight)" "legend(on)"
zk D03 auto "(spike mpg weight)" "legend(on)"
zk D04 auto "(dropline mpg weight)" "legend(on)"
zk D05 auto "(dot mpg weight)" "legend(on)"
zk D06 auto "(area mpg weight, sort)" "legend(on)"
zk D07 auto "(connected mpg weight, sort)" "legend(on)"
zk M01 auto "(scatter mpg weight) (scatter price weight)" ""
zk M02 auto "(scatter mpg weight) (line mpg weight, sort)" ""
zk M03 auto "(scatter mpg turn weight)" ""
zk M04 auto "(scatter mpg weight) (scatter mpg length)" ""
zk M05 auto "(scatter mpg weight) (scatter price weight, yaxis(2))" ""
zk M06 auto "(scatter mpg weight) (scatter price weight, yaxis(2)) (scatter trunk weight, yaxis(2))" ""
zk M07 auto "(scatter mpg weight) (lfit price weight, yaxis(2))" ""
zk M08 auto "(scatter m2 weight) (scatter p2 weight)" ""
zk M09 auto "(scatter m2 weight) (scatter p2 weight, yaxis(2))" ""
zk M10 auto "(lfit mpg weight) (scatter mpg weight)" ""
zk M11 auto "(scatter mpg weight) (scatter mpg weight)" ""
zk M12 auto "(scatter mpg weight) (scatter mpg weight, yaxis(2)) (scatter price weight, yaxis(2))" ""
zk M13 auto "(histogram mpg) (scatter mpg weight)" ""
zk M14 auto "(scatter mpg weight) (function y=20+0*x, range(2000 5000))" ""
zk M15 auto "(scatter mpg weight) (scatter mpg weight, xaxis(2))" ""
zk M16 auto "(scatter mpg weight) (scatter mpg length, xaxis(2))" ""
zk T01 sp "(tsline close)" "legend(on)"
zk T02 sp "(tsrline high low)" "legend(on)"
zk T03 sp "(tsrline high low) (tsline close)" ""
zk K01 auto "(scatter mpg weight) (scatter mpg length) (scatter mpg weight)" ""
zk K02 auto "(scatter mpg weight) (scatter mpg length) (scatter mpg length)" ""
zk K03 auto "(scatter mpg weight) (scatter price weight) (scatter trunk weight) (scatter mpg weight)" ""
zk K04 auto "(scatter mpg weight) (scatter price weight) (scatter price weight) (scatter mpg weight)" ""
zk K05 auto "(lfit mpg weight) (lfitci mpg weight)" ""
zk K06 auto "(lfitci mpg weight) (lfit mpg weight)" ""
zk K07 auto "(rcap mpg turn weight) (scatter mpg weight) (rcap mpg turn weight)" ""
zk K08 auto "(scatter mpg turn mpg weight)" ""
zk K09 auto "(scatter mpg weight) (lpoly mpg weight) (lfit mpg weight)" ""
zk K10 auto "(scatter mpg weight) (scatter price weight) (scatter mpg weight)" "by(foreign)"
zk K11 auto "(scatter mpg weight) (scatter price weight, yaxis(2)) (scatter trunk weight, yaxis(2)) (scatter price weight, yaxis(2))" ""
zk G01 auto "(scatter m2 weight) (fpfit m2 weight)" ""
zk G02 auto "(fpfitci m2 weight)" ""
zk G03 auto "(scatter price weight) (scatter p3 weight)" ""
zk G04 auto "(rcap turn t2 weight)" "legend(on)"
zk G05 auto "(scatter mpg weight) (scatter price weight)" "by(foreign)"
zk G06 auto "(scatter mpg weight) (lfit mpg weight)" "by(foreign)"
zk G07 auto "(lfitci mpg weight, level(90)) (scatter mpg weight)" ""
zk G08 auto "(lpolyci mpg weight, level(90))" ""
zk G09 auto "(function y=x, range(0 1)) (function y=2*x, range(0 1))" ""
zk G10 auto "(line mpg turn weight, sort)" ""
zk G11 auto "(kdensity mpg) (kdensity mpg, bwidth(5))" ""
zk G12 auto "(scatteri 20 3000) (scatteri 25 3500)" ""
zk G13 auto "(pci 1 1 2 2) (pci 3 3 4 4)" ""
zk G14 auto "(rarea mpg turn weight) (rarea mpg turn weight)" ""
zk G15 auto "(pcspike mpg weight mpg weight)" "legend(on)"
zk G16 auto "(pcspike mpg weight turn weight)" "legend(on)"
zk G17 auto "(kdensity mpg) (scatter mpg weight)" ""
zk G18 auto "(lowess mpg weight) (lowess mpg weight)" ""
zk G19 auto "(scatter mpg weight) (lowess mpg weight)" "by(foreign)"
zk G20 auto "(rcap mpg turn weight)" "by(foreign)"
zk G21 auto "(scatter mpg weight) (scatter p4 weight)" ""
zk G22 auto "(scatter mpg weight) (lfit mpg weight, yaxis(2)) (qfit mpg weight, yaxis(2))" ""
zk G23 auto "(scatter mpg weight) (rcap mpg turn weight, yaxis(2))" ""
zk G24 auto `"(scatteri 20 3000 "pt")"' "legend(on)"
zk G25 auto "(histogram mpg) (histogram mpg)" ""
zk G26 auto "(scatter mpg weight) (mband mpg weight, bands(5))" "ytitle(, size(large))"
zk G27 auto "(scatter mpg weight) (scatter mpg weight)" "by(foreign)"
zk H01 auto "(scatter price weight, yaxis(2)) (scatter mpg weight)" ""
zk H02 auto "(scatter mpg weight, xaxis(2)) (scatter mpg length)" ""
zk H05 auto "(scatter mpg weight) (lfitci mpg weight, yaxis(2))" ""
zk H07 sp "(tsline close open)" ""
zk H11 auto "(function  yy = x, range(0 1))" "legend(on)"
zk H14 auto "(lfit mpg weight) (lfit price weight)" ""
zk H15 auto "(mband mpg weight) (mband price weight)" ""
zk H16 auto "(lowess mpg weight) (lowess price weight)" ""
zk H17 auto "(kdensity mpg) (kdensity price)" ""
zk H20 auto "(scatter mpg weight) (scatter price weight)" "ytitle(, size(large))"
zk H21 auto "(scatter mpg weight) (lpoly price weight)" "xtitle(, size(large))"
zk L01 auto "(lfitci mpg weight) (lfitci price weight)" ""
zk L02 auto "(lfitci mpg weight) (qfitci mpg weight)" ""
zk L03 auto "(histogram mpg) (histogram price)" ""
zk L04 auto "(histogram mpg) (histogram mpg)" "legend(on)"
zk L05 auto "(scatter mpg weight, pstyle(p1)) (scatter mpg weight, pstyle(p1))" ""
zk L06 auto "(histogram mpg) (scatter mpg weight)" ""
zk L07 auto "(scatter mpg weight) (histogram mpg)" ""
zk L08 auto "(rcap mpg turn weight) (scatter mpg weight)" "by(foreign)"
zk L09 auto "(histogram mpg, freq) (histogram mpg, percent)" ""
zk N01 auto "(function _y = x, range(0 1))" "legend(on)"
zk N02 auto "(function ü = x, range(0 1))" "legend(on)"
zk N03 auto "(scatter mpg weight) (function 日本 = x/100, range(2000 5000))" ""
zk N04 auto "(scatter mpg weight) (lowess mp wei)" ""
zk N05 auto "(scatter mpg weight) (fpfit mp wei)" ""

// ---------------------------------------------------------------------------
// _zk_put(): write a text (by value, never expanded) as one file.
// ---------------------------------------------------------------------------
capture mata: mata drop _zk_put()
mata:
void _zk_put(string scalar file, string scalar text)
{
    real scalar fh
    if (fileexists(file)) unlink(file)
    fh = fopen(file, "w")
    fput(fh, text)
    fclose(fh)
}
end

// ---------------------------------------------------------------------------
// The probes
// ---------------------------------------------------------------------------
local N = ${ZK_N}
forvalues i = 1/`N' {
    local id   "${ZK_ID_`i'}"
    local ds   "${ZK_DS_`i'}"
    local body `"${ZK_BODY_`i'}"'
    local opts `"${ZK_OPTS_`i'}"'
    if "`ds'" == "sp" _zk_sp
    else _zk_auto

    // 1. twoway, and its axis objects' titles
    capture graph drop Graph
    capture noisily twoway `body', `opts' name(Graph, replace)
    local rc = _rc
    local y1 ""
    local y2 ""
    local x1 ""
    local x2 ""
    if `rc' == 0 {
        capture graph export "${ZK_WORK}/`id'_tw.svg", name(Graph) replace
        capture local y1 `"`.Graph.yaxis1.title.text[1]'"'
        capture local y2 `"`.Graph.yaxis2.title.text[1]'"'
        capture local x1 `"`.Graph.xaxis1.title.text[1]'"'
        capture local x2 `"`.Graph.xaxis2.title.text[1]'"'
        // A by() graph draws its shared axis titles as its l1title and
        // b1title; its panels' axis objects hold none.
        if strpos(`"`opts'"', "by(") {
            capture local y1 `"`.Graph.l1title.text[1]'"'
            capture local x1 `"`.Graph.b1title.text[1]'"'
        }
        // 2. its legend(off) twin
        capture graph drop Graph
        // (under by() the legend is by()'s own: legend(off) goes inside it)
        local offopts `"`opts' legend(off)"'
        if strpos(`"`opts'"', "by(foreign)") {
            local offopts : subinstr local opts "by(foreign)" "by(foreign, legend(off))"
        }
        capture noisily twoway `body', `offopts' name(Graph, replace)
        if _rc == 0 {
            capture graph export "${ZK_WORK}/`id'_off.svg", name(Graph) replace
        }
    }
    capture graph drop Graph
    local twrec "`rc'"
    mata: _zk_put(st_global("ZK_WORK") + "/" + st_local("id") + "_twrc.txt", st_local("twrec"))
    mata: _zk_put(st_global("ZK_WORK") + "/" + st_local("id") + "_y1.txt", st_local("y1"))
    mata: _zk_put(st_global("ZK_WORK") + "/" + st_local("id") + "_y2.txt", st_local("y2"))
    mata: _zk_put(st_global("ZK_WORK") + "/" + st_local("id") + "_x1.txt", st_local("x1"))
    mata: _zk_put(st_global("ZK_WORK") + "/" + st_local("id") + "_x2.txt", st_local("x2"))

    // 3. dash
    capture dash clear
    capture noisily dash `body', `opts' name(zk`i')
    local drc "`=_rc'"
    mata: _zk_put(st_global("ZK_WORK") + "/" + st_local("id") + "_dashrc.txt", st_local("drc"))
    mata: _zk_put(st_global("ZK_WORK") + "/" + st_local("id") + "_dash.txt", st_global("dash_json_zk" + st_local("i")))
    // WP-36 plat:PT-4: a named graph's points are its point file.
    mata: _zk_put(st_global("ZK_WORK") + "/" + st_local("id") + "_fpts.txt", _dash_fpts_get("zk" + st_local("i")))
    capture dash clear
    display as text "probe `id' twoway rc=`rc' dash rc=`drc'"
}

// The probe table, for the reader.
tempname tfh
file open `tfh' using "${ZK_WORK}/probes.txt", write text replace
file close `tfh'
forvalues i = 1/`N' {
    mata: _zkfh = fopen(st_global("ZK_WORK") + "/probes.txt", "a"); fput(_zkfh, st_global("ZK_ID_" + st_local("i")) + char(9) + st_global("ZK_DS_" + st_local("i")) + char(9) + st_global("ZK_BODY_" + st_local("i")) + char(9) + st_global("ZK_OPTS_" + st_local("i"))); fclose(_zkfh)
}

// ===========================================================================
// Analysis + JSON emission.  No callbacks into Stata from here on.
// REMINDER: no backtick may appear literally in this block.
// ===========================================================================
python:
import collections
import json
import os
import re
import sys
from sfi import Macro

ZK_REPO = Macro.getGlobal("ZK_REPO")
sys.path.insert(0, os.path.join(ZK_REPO, "scripts"))
import svg_truth

W = Macro.getGlobal("ZK_WORK")
OUT = Macro.getGlobal("ZK_OUT")


def _read(name):
    p = os.path.join(W, name)
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8") as fh:
        return fh.read().rstrip("\n")


def _texts(path):
    if not os.path.exists(path):
        return [], None
    doc = svg_truth.svg_document(path)
    ents = [e for e in doc["texts"]
            if svg_truth.label_value(e["text"]) is None
            and e["text"].strip() != ""]
    return ents, doc.get("canvas")


_DATE = re.compile(r"^\d\d[a-z]{3}\d{4}$")
_BY_TEXTS = {"Domestic", "Foreign"}


def _keys(bare, off, by):
    cnt = collections.Counter(e["text"] for e in bare)
    cnt.subtract(collections.Counter(e["text"] for e in off))
    seen, out = collections.Counter(), []
    for e in sorted(bare, key=lambda e: (float(e.get("y") or 0.0),
                                         float(e.get("x") or 0.0))):
        t = e["text"]
        if seen[t] < cnt.get(t, 0):
            seen[t] += 1
            if by and (t in _BY_TEXTS or t.startswith("Graphs by")):
                continue
            out.append(t)
    return out


def _sides(off, canvas, by):
    out = {"left": [], "right": [], "bottom": [], "top": []}
    if not canvas:
        return out
    w, h = float(canvas["w"]), float(canvas["h"])
    for e in off:
        t = e["text"]
        if by and (t in _BY_TEXTS or t.startswith("Graphs by")):
            continue
        x, y = float(e.get("x") or 0.0), float(e.get("y") or 0.0)
        if e.get("rotate") == -90.0:
            out["left" if x < w / 2 else "right"].append(t)
        elif not _DATE.match(t):
            out["top" if y < h / 2 else "bottom"].append(t)
    return out


def _json_or_none(s):
    s = s.strip()
    if not s:
        return None
    return json.loads(s)


data, formats = {}, {}
for ds in ("auto", "sp500"):
    with open(os.path.join(W, "data_%s.json" % ds), encoding="utf-8") as fh:
        data[ds] = json.load(fh)
    formats[ds] = {}
    for line in _read("formats_%s.txt" % ds).splitlines():
        v, f = line.split("|", 1)
        formats[ds][v] = f

probes = {}
for line in _read("probes.txt").splitlines():
    pid, ds, body, opts = line.split("\t")
    ds = "sp500" if ds == "sp" else ds
    by = "by(" in opts
    bare, canvas = _texts(os.path.join(W, pid + "_tw.svg"))
    off, canvas_off = _texts(os.path.join(W, pid + "_off.svg"))
    tw = {
        "rc": int(_read(pid + "_twrc.txt") or 0),
        "keys": _keys(bare, off, by),
        "titles": dict((k, _read("%s_%s.txt" % (pid, k)))
                       for k in ("y1", "y2", "x1", "x2")),
        "svg_titles": _sides(off, canvas_off, by),
    }
    probes[pid] = {
        "ds": ds, "body": body, "opts": opts, "twoway": tw,
        "dash": {"rc": int(_read(pid + "_dashrc.txt") or 0),
                 "graph": _json_or_none(_read(pid + "_dash.txt")),
                 "points": _json_or_none(_read(pid + "_fpts.txt"))},
    }

doc = {
    "_meta": {
        "stata_version": Macro.getGlobal("ZK_SVER"),
        "born_date": Macro.getGlobal("ZK_BORN"),
        "source": "scripts/extract_series_label_truth.do",
        "dash_commit": Macro.getGlobal("ZK_COMMIT"),
        "extracted": Macro.getGlobal("ZK_DATE"),
        "scheme": "stcolor",
        "probes": len(probes),
        "method": ("keys are the bare SVG's non-numeric texts minus its "
                   "legend(off) twin's, by multiset, in (y, x) order; titles "
                   "are twoway's axis objects (.Graph.<axis>.title.text[1]; "
                   "under by() .Graph.l1title and .Graph.b1title); "
                   "svg_titles are the texts the legend(off) SVG draws on "
                   "each side."),
    },
    "data": data,
    "formats": formats,
    "probes": probes,
}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, ensure_ascii=False, indent=1, sort_keys=True)
    fh.write("\n")
print("WROTE %s probes=%d" % (OUT, len(probes)))
end

display as text "extract_series_label_truth.do: done"
