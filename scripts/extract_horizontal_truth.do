* extract_horizontal_truth.do -- twoway's own horizontal and vertical
* (WP-30 P1.9a, section 49), written to test/fixtures/horizontal_truth.json
* for test/test_horizontal.py, the HZ cases of
* test/test_option_validation.cscript and the S49 block of
* test/test_wp30_truth.cscript.
*
* Records:
*   accept[<type>][<form>]  rc and first error line of the type given
*                           horizontal, vertical, "horizontal vertical" and
*                           "vertical horizontal" (forms h, v, hv, vh).
*   recast[<id>]            cmd, rc, line: the recast() rows (HZ- and R-
*                           on sysuse auto; RH1- and RH9-, WP-46 46-01, on
*                           the data below).
*   draw[<id>]              cmd, rc and, for rc 0, xlabels, ylabels (the
*                           tick labels svg_truth reads on each axis),
*                           ytitle, y2title (rotated texts left and right of
*                           the plot region) and xtitle (a flat text below
*                           it), each "" when absent.
*
* Run (never the GUI; the slot wrapper of scripts/stata_slot.sh):
*   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_horizontal_truth.do
* SVGs and logs go to c(tmpdir).

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zh_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zh_bad' {
    display as error "extract_horizontal_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zh_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zh_rc' | _rc {
    local _zh_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_horizontal_truth.do: `_zh_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}

clear all
set more off
version 19
set scheme stcolor

local stata_version = c(stata_version)
local born_date "`c(born_date)'"
tempfile gh
shell git -C "`repo'" rev-parse HEAD > "`gh'"
tempname fh
file open `fh' using "`gh'", read text
file read `fh' dash_commit
file close `fh'
local extracted "`c(current_date)'"
local tmp "`c(tmpdir)'"

capture program drop _hz_data
program _hz_data
    clear
    quietly set obs 5
    generate double x = _n
    generate double y = .
    local ys 10 30 20 50 40
    forvalues i = 1/5 {
        quietly replace y = `: word `i' of `ys'' in `i'
    }
    generate double lo = y - 5
    generate double hi = y + 5
    generate double d = td(08jan2020) + 25 * (_n - 1)
    format d %td
    generate double t = _n
    quietly tsset t
    label variable x "Xvar"
    label variable y "Yvar"
    label variable lo "Lovar"
    label variable hi "Hivar"
    label variable d "Day"
    label variable t "Tvar"
end

capture program drop _hz_probe
program _hz_probe
    args kind id cmd
    local tmp "`c(tmpdir)'"
    global HZ_SEQ = $HZ_SEQ + 1
    local f "hz_$HZ_SEQ"
    capture log close hzp
    capture graph drop _all
    log using "`tmp'/`f'.log", text replace name(hzp)
    capture noisily `cmd'
    local rc = _rc
    log close hzp
    if `rc' == 0 & "`kind'" == "draw" {
        quietly graph export "`tmp'/`f'.svg", replace
    }
    file write $HZ_RH `"`kind'|`id'|`rc'|`f'|`cmd'"' _n
end

tempfile recs
tempname rh
file open `rh' using "`recs'", write text replace
global HZ_RH `rh'
global HZ_SEQ 0

_hz_data
* accept: every dash type, four forms.
local yx     scatter line connected area bar spike dropline dot
local rng    rarea rbar rspike rcap rcapsym rline rconnected rscatter
local pc     pcspike pccapsym pcarrow pcbarrow pcscatter
local fits   lfit qfit lfitci qfitci fpfit fpfitci lowess lpoly lpolyci mband mspline
foreach form in h v hv vh {
    if "`form'" == "h"  local o "horizontal"
    if "`form'" == "v"  local o "vertical"
    if "`form'" == "hv" local o "horizontal vertical"
    if "`form'" == "vh" local o "vertical horizontal"
    foreach tt of local yx {
        _hz_probe accept `tt'/`form' "twoway `tt' y x, `o' nodraw"
    }
    foreach tt of local rng {
        _hz_probe accept `tt'/`form' "twoway `tt' lo hi x, `o' nodraw"
    }
    foreach tt of local pc {
        _hz_probe accept `tt'/`form' "twoway `tt' lo x hi x, `o' nodraw"
    }
    foreach tt of local fits {
        _hz_probe accept `tt'/`form' "twoway `tt' y x, `o' nodraw"
    }
    _hz_probe accept pci/`form'       "twoway pci 1 1 2 2, `o' nodraw"
    _hz_probe accept pcarrowi/`form'  "twoway pcarrowi 1 1 2 2, `o' nodraw"
    _hz_probe accept scatteri/`form'  "twoway scatteri 1 1 2 2, `o' nodraw"
    _hz_probe accept function/`form'  "twoway function y=x^2, range(0 2) `o' nodraw"
    _hz_probe accept histogram/`form' "twoway histogram y, `o' nodraw"
    _hz_probe accept kdensity/`form'  "twoway kdensity y, `o' nodraw"
    _hz_probe accept tsline/`form'    "twoway tsline y, `o' nodraw"
    _hz_probe accept tsrline/`form'   "twoway tsrline lo hi, `o' nodraw"
}

* recast: E4's rows (auto, as measured).
sysuse auto, clear
_hz_probe recast HZ-06 "twoway bar mpg weight, recast(scatter) horizontal nodraw"
_hz_probe recast HZ-07 "twoway kdensity mpg, recast(area) vertical nodraw"
_hz_probe recast HZ-08 "twoway lfit mpg weight, recast(bar) horizontal nodraw"
_hz_probe recast HZ-09 "twoway lfit mpg weight, recast(scatter) horizontal nodraw"
_hz_probe recast HZ-10 "twoway histogram mpg, recast(line) vertical nodraw"
_hz_probe recast HZ-11 "twoway scatter mpg weight, recast(bar) horizontal nodraw"
_hz_probe recast HZ-12 "twoway area mpg weight, recast(line) vertical nodraw"
_hz_probe recast HZ-13 "twoway rcap mpg price weight, recast(rscatter) horizontal vertical nodraw"
_hz_probe recast R-lfit-line   "twoway lfit mpg weight, recast(line) horizontal nodraw"
_hz_probe recast R-lowess-line "twoway lowess mpg weight, recast(line) horizontal nodraw"
_hz_probe recast R-lowess-bar  "twoway lowess mpg weight, recast(bar) horizontal nodraw"
_hz_probe recast R-kd-line-h   "twoway kdensity mpg, recast(line) horizontal nodraw"
_hz_probe recast R-kd-line-v   "twoway kdensity mpg, recast(line) vertical nodraw"
_hz_probe recast R-kd-line-hv  "twoway kdensity mpg, recast(line) horizontal vertical nodraw"
_hz_probe recast R-fn-area-v   "twoway function y=x, range(0 1) recast(area) vertical nodraw"
_hz_probe recast R-fn-line-v   "twoway function y=x, range(0 1) recast(line) vertical nodraw"
_hz_probe recast R-hist-sc-h   "twoway histogram mpg, recast(scatter) horizontal nodraw"
_hz_probe recast R-line-area-h "twoway line mpg weight, recast(area) horizontal nodraw"

* recast: WP-46 46-01's rows (RH-1, RH-9), on this script's data.
_hz_data
_hz_probe recast RH1-01 "twoway rarea lo hi x, recast(line) horizontal nodraw"
_hz_probe recast RH1-02 "twoway rcap lo hi x, recast(scatter) vertical nodraw"
_hz_probe recast RH1-03 "twoway rarea lo hi x, recast(connected) horizontal nodraw"
_hz_probe recast RH1-04 "twoway rspike lo hi x, recast(bar) horizontal nodraw"
_hz_probe recast RH1-05 "twoway rarea lo hi x, recast(area) horizontal nodraw"
_hz_probe recast RH1-06 "twoway rspike lo hi x, recast(spike) horizontal nodraw"
_hz_probe recast RH1-07 "twoway rcap lo hi x, recast(dropline) horizontal nodraw"
_hz_probe recast RH1-08 "twoway rbar lo hi x, recast(dot) horizontal nodraw"
_hz_probe recast RH1-09 "twoway rarea lo hi x, recast(line) horizontal vertical nodraw"
_hz_probe recast RH1-10 "twoway tsrline lo hi, recast(line) horizontal nodraw"
_hz_probe recast RH9-01 "twoway dot y x, recast(line) horizontal nodraw"
_hz_probe recast RH9-02 "twoway dot y x, recast(scatter) vertical nodraw"
_hz_probe recast RH9-03 "twoway dot y x, recast(bar) horizontal nodraw"
_hz_probe recast RH9-04 "twoway dot y x, recast(b) horizontal nodraw"
_hz_probe recast RH9-05 "twoway scatteri 1 1 2 2 3 1, recast(bar) horizontal nodraw"
_hz_probe recast RH9-06 "twoway scatteri 1 1 2 2 3 1, recast(area) vertical nodraw"
_hz_probe recast RH9-07 "twoway scatter y x, recast(b) horizontal nodraw"
_hz_probe recast RH9-08 "twoway scatter y x, recast(ba) horizontal nodraw"
_hz_probe recast RH9-09 "twoway scatter y x, recast(bar) horizontal nodraw"
_hz_probe recast RH9-12 "twoway bar y x, recast(b) horizontal nodraw"
_hz_probe recast RH9-13 "twoway lfit y x, recast(b) horizontal nodraw"
_hz_probe recast RH9-14 "twoway dot y x, recast(dot dot) horizontal nodraw"
_hz_probe recast RH9-15 "twoway scatter y x, recast(bar bar) horizontal nodraw"
_hz_probe recast RH9-16 "twoway kdensity y, recast(b) horizontal nodraw"
_hz_probe recast RH9-17 "twoway tsline y, recast(b) horizontal nodraw"

* draw: the 24 turned types and E3's titles, dates and second axes.
_hz_data
foreach tt in area bar spike dropline dot {
    _hz_probe draw `tt' "twoway `tt' y x, horizontal"
}
foreach tt in rarea rbar rspike rcap rcapsym rline rconnected rscatter {
    _hz_probe draw `tt' "twoway `tt' lo hi x, horizontal"
}
foreach tt in pcspike pccapsym pcarrow pcbarrow pcscatter {
    _hz_probe draw `tt' "twoway `tt' lo x hi x, horizontal"
}
_hz_probe draw pci       "twoway pci 1 1 2 2, horizontal"
_hz_probe draw pcarrowi  "twoway pcarrowi 1 1 2 2, horizontal"
_hz_probe draw function  "twoway function y=x^2, range(0 2) horizontal"
_hz_probe draw histogram "twoway histogram y, horizontal"
_hz_probe draw kdensity  "twoway kdensity y, horizontal"
_hz_probe draw tsrline   "twoway tsrline lo hi, horizontal"
_hz_probe draw T-sc-barh       "twoway (scatter y x) (bar y x, horizontal)"
_hz_probe draw T-sc-barh-sc    "twoway (scatter y x) (bar y x, horizontal) (scatter y x)"
_hz_probe draw T-barh-barh     "twoway (bar y x, horizontal) (bar y x, horizontal)"
_hz_probe draw T-rcaph-sc      "twoway (rcap lo hi x, horizontal) (scatter x y)"
_hz_probe draw HZ-25 "twoway bar y d, horizontal"
_hz_probe draw HZ-26 "twoway (scatter y d) (bar y d, horizontal)"
_hz_probe draw HZ-27 "twoway (bar y d, horizontal) (scatter y d)"
_hz_probe draw HZ-28 "twoway (scatter y x) (bar y x, horizontal yaxis(2))"
_hz_probe draw hist-d "twoway histogram d, horizontal"
* WP-46 46-01: recast layers drawn under horizontal.
_hz_probe draw RH1-01 "twoway rarea lo hi x, recast(line) horizontal"
_hz_probe draw RH1-03 "twoway rarea lo hi x, recast(connected) horizontal"
_hz_probe draw RH1-04 "twoway rspike lo hi x, recast(bar) horizontal"
_hz_probe draw RH1-05 "twoway rarea lo hi x, recast(area) horizontal"
_hz_probe draw RH9-05 "twoway scatteri 1 1 2 2 3 1, recast(bar) horizontal"
file close `rh'

python:
import json, os, re, sys
from sfi import Macro
repo = Macro.getLocal("repo")
tmp = Macro.getLocal("tmp")
sys.path.insert(0, os.path.join(repo, "scripts"))
import svg_truth

def _first_error(log):
    try:
        with open(log, encoding="utf-8", errors="replace") as fh:
            rows = fh.read().splitlines()
    except OSError:
        return ""
    for r in rows:
        s = r.strip()
        if "not allowed" in s or s.startswith("may not combine"):
            return s
    return ""

def _draw(svg):
    doc = svg_truth.svg_document(svg)
    pr = doc["plotregion"]
    out = {"xlabels": [], "ylabels": [], "xtitle": "", "ytitle": "",
           "y2title": ""}
    for ax in ("x", "y"):
        rd = svg_truth.svg_axis_reading(svg, ax, doc=doc)
        out[ax + "labels"] = [str(v) for v in (rd.get("labels") or [])]
    if pr is None:
        return out
    labels = set(out["xlabels"]) | set(out["ylabels"])
    mid = (pr["left"] + pr["right"]) / 2.0
    for t in doc["texts"]:
        s = t.get("text", "")
        if not s or s in labels:
            continue
        if t.get("rotate") is not None:
            key = "ytitle" if t.get("x", 0) < mid else "y2title"
            out[key] = out[key] or s
        elif t.get("y", 0) > pr["bottom"] and t.get("x", 0) > pr["left"] \
                and t.get("x", 0) < pr["right"]:
            out["xtitle"] = out["xtitle"] or s
    return out

accept, recast, draw = {}, {}, {}
with open(Macro.getLocal("recs"), encoding="utf-8") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if not line:
            continue
        kind, pid, rc, f, cmd = line.split("|", 4)
        line1 = _first_error(os.path.join(tmp, f + ".log"))
        if kind == "accept":
            tt, form = pid.split("/")
            accept.setdefault(tt, {})[form] = {"rc": int(rc), "line": line1}
        elif kind == "recast":
            recast[pid] = {"cmd": cmd.replace(" nodraw", ""), "rc": int(rc),
                           "line": line1}
        else:
            rec = {"cmd": cmd, "rc": int(rc)}
            p = os.path.join(tmp, f + ".svg")
            if int(rc) == 0 and os.path.exists(p):
                rec.update(_draw(p))
            draw[pid] = rec

out = {"accept": accept, "recast": recast, "draw": draw,
       "_meta": {"stata_version": Macro.getLocal("stata_version"),
                 "born_date": Macro.getLocal("born_date"),
                 "source": "scripts/extract_horizontal_truth.do",
                 "dash_commit": Macro.getLocal("dash_commit").strip(),
                 "extracted": Macro.getLocal("extracted"),
                 "scheme": "stcolor",
                 "data": "x 1..5 (Xvar), y 10 30 20 50 40 (Yvar), lo = y-5 (Lovar), hi = y+5 (Hivar), d %td from 08jan2020 step 25 (Day), t = _n tsset; recast rows HZ- and R- on sysuse auto, RH1- and RH9- on these data"}}
path = os.path.join(repo, "test", "fixtures", "horizontal_truth.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote " + path)
end
