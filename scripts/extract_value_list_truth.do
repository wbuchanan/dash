* extract_value_list_truth.do -- twoway's reading of the value lists
* mlabel(), jitter(), base() and barwidth() across an expanded varlist
* (WP-30 P1.1b, section 20), written to test/fixtures/value_list_truth.json
* for test/test_value_lists.py.
*
* Each case runs `twoway <cmd>' under s2color; the record keeps its rc and
* its first error line from a text log and, when it drew: the marker-label
* groups (M cases: text fill, count, first three texts, in document order),
* the bars of each fill in data units (G cases: width, bottom, top) and the
* distinct marker positions of each fill (J cases).
*
* Run (never the GUI; the slot wrapper of scripts/stata_slot.sh):
*   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_value_list_truth.do
* The SVG and log files are written to the current directory (the slot
* wrapper's scratch directory).

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_value_list_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_value_list_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
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

tempfile records
tempname rf
file open `rf' using "`records'", write text replace

capture program drop _vl_case
program _vl_case
    // _vl_case id data cmd: run twoway cmd on auto, the G bars or the J
    // points, logging it, and append id|rc|svg|log to the record file.
    args id data cmd
    if "`data'" == "G" {
        quietly {
            clear
            set obs 5
            gen x = _n
            gen y1 = 30 + _n
            gen y2 = 40 + _n
        }
    }
    else if "`data'" == "J" {
        quietly {
            clear
            set obs 30
            gen x = mod(_n, 3)
            gen y1 = mod(_n, 2)
            gen y2 = 2 + mod(_n, 2)
        }
    }
    else quietly sysuse auto, clear
    local log "`c(pwd)'/vl_`id'.log"
    local svg ""
    capture graph drop g
    local sep = cond(strpos(`"`macval(cmd)'"', ","), " ", ", ")
    quietly log using "`log'", text replace name(vltruth)
    capture noisily twoway `macval(cmd)'`sep'name(g, replace)
    local rc = _rc
    quietly log close vltruth
    if !`rc' {
        local svg "`c(pwd)'/vl_`id'.svg"
        quietly graph export "`svg'", replace name(g)
    }
    file write $VL_RF "`id'|`rc'|`svg'|`log'" _n
    mata: st_global("VL_CMD_`id'", st_local("cmd"))
end
global VL_RF `rf'

local two "scatter mpg turn weight,"
_vl_case M01 auto `"`two' mlabel(make rep78)"'
_vl_case M02 auto `"scatter mpg weight, mlabel(make foreign)"'
_vl_case M03 auto `"`two' mlabel(. rep78)"'
_vl_case M04 auto `"`two' mlabel(make .)"'
_vl_case M05 auto `"`two' mlabel(make)"'
_vl_case M06 auto `"`two' mlabel(make rep78 foreign)"'
_vl_case M07 auto `"`two' mlabel(mak rep7)"'
_vl_case M08 auto `"`two' mlabel(make "")"'
_vl_case M09 auto `"`two' mlabel(rep*)"'
_vl_case M10 auto `"`two' mlabel(t*)"'
_vl_case M11 auto `"`two' mlabel(make) mlabel(rep78 foreign)"'
_vl_case M35 auto `"connected mpg turn weight, mlabel(make rep78) mlabposition(3 9)"'
_vl_case M12 auto `"`two' mlabel(make ..)"'
_vl_case M13 auto `"`two' mlabel(make ...)"'
_vl_case M14 auto `"`two' mlabel(make .. rep78)"'
_vl_case M15 auto `"`two' mlabel(make =)"'
_vl_case M16 auto `"`two' mlabel(= make)"'
_vl_case M17 auto `"`two' mlabel(.)"'
_vl_case M18 auto `"`two' mlabel(. ..)"'
_vl_case M19 auto `"`two' mlabel(make rep78 nosuch)"'
_vl_case M20 auto `"scatter mpg weight, mlabel(rep78 nosuch)"'
_vl_case M21 auto `"`two' mlabel(nosuch ..)"'
_vl_case M22 auto `"`two' mlabel(make .. nosuch)"'
_vl_case M23 auto `"`two' mlabel(nosuch =)"'
_vl_case M24 auto `"`two' mlabel(= nosuch)"'
_vl_case M25 auto `"histogram mpg, mlabel(nosuch ..)"'
_vl_case M26 auto `"histogram mpg, mlabel(= make)"'
_vl_case M27 auto `"histogram mpg, mlabel(nosuch)"'
_vl_case M28 auto `"function y=x, mlabel(make ..)"'
_vl_case M29 auto `"function y=x, mlabel(nosuch =)"'
_vl_case M30 auto `"mspline mpg weight, mlabel(make rep78)"'
_vl_case M31 auto `"mspline mpg weight, mlabel(make ..)"'
_vl_case M32 auto `"mband mpg weight, mlabel(nosuch rep78)"'
_vl_case M33 auto `"`two' mlabel(make..)"'
_vl_case M34 auto `"`two' mlabel(L.mpg)"'
_vl_case V01 auto `"`two' jitter(2 3)"'
_vl_case V02 auto `"`two' jitter(2 ..)"'
_vl_case V03 auto `"`two' jitter(. 3)"'
_vl_case V04 auto `"`two' jitter(2 =)"'
_vl_case V05 auto `"`two' jitter(2 .. 5)"'
_vl_case V06 auto `"`two' jitter(2 200)"'
_vl_case V07 auto `"scatter mpg weight, jitter(2 200)"'
_vl_case V08 auto `"`two' jitter(.)"'
_vl_case V09 auto `"`two' jitter(2 abc)"'
_vl_case V10 auto `"scatter mpg weight, jitter(2 abc)"'
_vl_case B01 auto `"bar mpg turn weight, base(10 20)"'
_vl_case B02 auto `"bar mpg turn weight, base(10 ..)"'
_vl_case B03 auto `"bar mpg turn weight, base(10 =)"'
_vl_case B04 auto `"bar mpg turn weight, base(10 .. 20)"'
_vl_case B05 auto `"bar mpg turn weight, barwidth(1 2)"'
_vl_case B06 auto `"bar mpg turn weight, barwidth(. 200)"'
_vl_case B07 auto `"bar mpg turn weight, barwidth(1 ..)"'
_vl_case B08 auto `"bar mpg turn weight, barwidth(.)"'
_vl_case B09 auto `"dropline mpg turn weight, base(10 20)"'
_vl_case B10 auto `"spike mpg turn weight, base(10 20)"'
_vl_case B11 auto `"area mpg turn weight, sort base(10 20)"'
_vl_case B12 auto `"bar mpg weight, barwidth(1 2)"'
_vl_case B13 auto `"bar mpg weight, base(10 20)"'
_vl_case B14 auto `"rbar mpg turn weight, barwidth(50 100)"'
_vl_case B15 auto `"rbar mpg turn weight, barwidth(50 ..)"'
_vl_case B16 auto `"rbar mpg turn weight, barwidth(50) barwidth(10 20)"'
_vl_case B17 auto `"histogram mpg, barwidth(1 2)"'
_vl_case B18 auto `"rcap mpg turn weight, barwidth(1 2)"'
_vl_case B19 auto `"rspike mpg turn weight, barwidth(1 2)"'
_vl_case B20 auto `"rbar mpg turn weight, base(10 20)"'
_vl_case B21 auto `"histogram mpg, base(10 20)"'
_vl_case B22 auto `"lowess mpg weight, bwidth(.5 .8)"'
_vl_case B23 auto `"bar mpg turn weight, base(10 abc)"'
_vl_case B24 auto `"rbar mpg turn weight, barwidth(.)"'
_vl_case G01 G `"bar y1 y2 x, barwidth(0.4 0.8) base(10 20)"'
_vl_case G02 G `"bar y1 y2 x, barwidth(0.4 ..) base(10 =)"'
_vl_case G03 G `"bar y1 y2 x, base(50)"'
_vl_case G04 G `"bar y1 y2 x, base(. 50)"'
_vl_case J01 J `"scatter y1 y2 x, jitter(5) jitterseed(1)"'
_vl_case J02 J `"scatter y1 y2 x, jitter(. 5) jitterseed(1)"'
_vl_case J03 J `"scatter y1 y2 x, jitter(5 ..) jitterseed(1)"'

file close `rf'
global VL_RF

python:
import json, os, re, sys
from sfi import Macro
repo = Macro.getLocal("repo")
sys.path.insert(0, os.path.join(repo, "scripts"))
import svg_truth


def _log(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = [ln.rstrip("\n").replace(" ", " ") for ln in fh]
    for ln in lines:
        s = ln.strip()
        if (not s or s.startswith("(note:") or re.match(r"^r\(\d+\);$", s)
                or s.startswith("name:") or s.startswith("log:")
                or s.startswith("log type:") or s.startswith("opened on:")
                or s.startswith("closed on:") or s.startswith("---")):
            continue
        return s
    return ""


def _labels(path):
    out = []
    for t in svg_truth.svg_texts(path):
        fill = t.get("fill") or ""
        if not fill or fill == "#000000":
            continue
        if out and out[-1][0] == fill:
            out[-1][1] += 1
            if len(out[-1][2]) < 3:
                out[-1][2].append(t["text"])
        else:
            out.append([fill, 1, [t["text"]]])
    return out


def _bars(path):
    doc = svg_truth.svg_document(path)
    pr = doc["plotregion"]
    fx = svg_truth.svg_axis_reading(path, "x", doc=doc)["fit"]
    fy = svg_truth.svg_axis_reading(path, "y", doc=doc)["fit"]
    ux, uy = abs(fx["units_per_px"]), abs(fy["units_per_px"])
    out = {}
    for r in doc["rects"]:
        if None in (r["x"], r["y"], r["w"], r["h"]) or not r["fill"]:
            continue
        if r["fill"] in ("#ffffff", "#eaf2f3", "none", pr.get("fill")):
            continue
        if (r["x"] < pr["left"] - 0.5 or r["x"] + r["w"] > pr["right"] + 0.5
                or r["y"] < pr["top"] - 0.5 or r["y"] + r["h"] > pr["bottom"] + 0.5):
            continue
        lo = fy["low"] + (pr["bottom"] - (r["y"] + r["h"])) * uy
        hi = fy["low"] + (pr["bottom"] - r["y"]) * uy
        pair = [round(r["w"] * ux, 2), round(lo, 2), round(hi, 2)]
        lst = out.setdefault(r["fill"], [])
        if pair not in lst:
            lst.append(pair)
    return out


def _jitter(path):
    out = {}
    for c in svg_truth.svg_document(path)["circles"]:
        if not c["fill"] or c["fill"] in ("none", "#ffffff"):
            continue
        out.setdefault(c["fill"], set()).add((round(c["cx"], 1), round(c["cy"], 1)))
    return {k: len(v) for k, v in out.items()}


cases = {}
with open(Macro.getLocal("records"), encoding="utf-8") as fh:
    for ln in fh:
        cid, rc, svg, log = ln.rstrip("\n").split("|")
        rec = {"cmd": Macro.getGlobal("VL_CMD_" + cid), "rc": int(rc),
               "message": _log(log)}
        if svg:
            if cid.startswith("M"):
                rec["labels"] = _labels(svg)
            elif cid.startswith("G"):
                rec["bars"] = _bars(svg)
            elif cid.startswith("J"):
                rec["jitter"] = _jitter(svg)
        cases[cid] = rec
meta = {"stata_version": Macro.getLocal("stata_version"),
        "born_date": Macro.getLocal("born_date"),
        "dash_commit": Macro.getLocal("dash_commit"),
        "extracted": Macro.getLocal("extracted")}
out = os.path.join(repo, "test", "fixtures", "value_list_truth.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump({"cases": cases, "scheme": "s2color", "_meta": meta}, fh,
              indent=2, sort_keys=True)
    fh.write("\n")
print("wrote " + out)
end

set scheme `entry_scheme'
