*! extract_range_ticks_truth.do
*! WP-34 section 34-03 (AX-1): ground truth for range() beyond the data.
*! On an axis with no label rule twoway's range() widens only the scale;
*! the ticks stay natscale over the data.  Under #N, or in a by() graph,
*! the ticks are placed over the data and the range together.
*!
*! R1-R11 are section 34-03's probes; R12 widens the second axis past its
*! data (range(20000) over price's 3291-15906); R13 is R1 over the rows a
*! price range filter at 3291-7075.5 keeps (the after-move tests' move).
*!
*! Per probe and axis (x1, y1, y2; each panel of a by() graph through
*! .Graph.graphs[k]): the tick list .major.dlg_tickpos[i], .major.{min,
*! max,delta} and the scale's curmin/curmax.  Records go to a file under
*! c(tmpdir); the trailing python: block reads it into
*! test/fixtures/range_ticks_truth.json, never calls Stata and starts no
*! subprocess.
*!
*! Run (Stata only through the slot wrapper, never the GUI):
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> \
*!       <repo>/scripts/extract_range_ticks_truth.do

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_range_ticks_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_range_ticks_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
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

global RT_REPO "`repo'"
global RT_OUT "${RT_REPO}/test/fixtures/range_ticks_truth.json"
local work "`c(tmpdir)'dash_range_ticks_probe"
capture mkdir "`work'"
global RT_WORK "`work'"
global RT_REC "`work'/rt_records.txt"

local stata_version = c(stata_version)
local born_date "`c(born_date)'"
local extracted "`c(current_date)'"
tempfile rtgit
quietly shell git -C "${RT_REPO}" rev-parse HEAD > "`rtgit'"
tempname rtgh
file open `rtgh' using "`rtgit'", read text
file read `rtgh' rtline
file close `rtgh'
local dash_commit = trim(`"`rtline'"')
capture assert ustrregexm(`"`dash_commit'"', "^[0-9a-f]{40}$")
if _rc {
    display as error "extract_range_ticks_truth.do: git rev-parse HEAD did not print a 40-character commit"
    exit 498
}

capture program drop _rt_axis
program _rt_axis
    // one line: the major ticks and scale of axis `ax' (x1, y1, y2) of `p'
    args id tag p ax
    local d = substr("`ax'", 1, 1)
    local k = substr("`ax'", 2, 1)
    local a "`p'.`d'axis`k'"
    if "`k'" == "1" local s "`p'.plotregion1.`d'scale"
    else local s "`p'.`d'axis`k'.plotregion.`d'scale"
    local n "`.`a'.major.dlg_tickpos.arrnels'"
    if "`n'" == "" | "`n'" == "." local n 0
    local v ""
    forvalues i = 1/`n' {
        local v "`v' `.`a'.major.dlg_tickpos[`i']'"
    }
    file write rtrec `"A|`id'|`tag'|`ax'|``a'.major.min'|``a'.major.max'|``a'.major.delta'|``s'.curmin'|``s'.curmax'|`v'"' _n
end

capture program drop _rt_rec
program _rt_rec
    // _rt_rec <id> <axes> `"<command>"'
    args id axes cmd
    sysuse auto, clear
    capture graph drop _all
    file write rtrec `"P|`id'|`cmd'"' _n
    capture noisily `cmd'
    local rc = _rc
    file write rtrec `"R|`id'|`rc'"' _n
    if `rc' == 0 {
        local n "`.Graph.graphs.arrnels'"
        if "`n'" == "" | "`n'" == "." local n 0
        if `n' > 0 {
            forvalues k = 1/`n' {
                foreach ax of local axes {
                    _rt_axis `id' `k' ".Graph.graphs[`k']" `ax'
                }
            }
        }
        else {
            foreach ax of local axes {
                _rt_axis `id' 0 ".Graph" `ax'
            }
        }
    }
    capture graph drop _all
end

file open rtrec using "${RT_REC}", write text replace
_rt_rec R1  "x1 y1"    `"twoway scatter mpg weight, yscale(range(0))"'
_rt_rec R2  "x1 y1"    `"twoway scatter mpg weight, yscale(range(100))"'
_rt_rec R3  "x1 y1"    `"twoway scatter mpg weight, xscale(range(0 6000))"'
_rt_rec R4  "x1 y1"    `"twoway scatter mpg weight, xscale(range(1000 6100))"'
_rt_rec R5  "x1 y1"    `"twoway scatter mpg weight, ylabel(#5) yscale(range(100))"'
_rt_rec R6  "x1 y1"    `"twoway scatter mpg weight, by(foreign) yscale(range(0))"'
_rt_rec R7  "x1 y1"    `"twoway scatter mpg weight, yscale(log range(5))"'
_rt_rec R8  "x1 y1"    `"twoway bar mpg weight, yscale(range(0))"'
_rt_rec R9  "x1 y1"    `"twoway (scatter mpg weight) (lfit mpg weight), yscale(range(0))"'
_rt_rec R10 "x1 y1 y2" `"twoway (scatter mpg weight) (scatter price weight, yaxis(2)), yscale(range(0) axis(2))"'
_rt_rec R11 "x1 y1"    `"twoway scatter mpg weight, ylabel(, angle(0)) yscale(range(0))"'
_rt_rec R12 "x1 y1 y2" `"twoway (scatter mpg weight) (scatter price weight, yaxis(2)), yscale(range(20000) axis(2))"'
_rt_rec R13 "x1 y1"    `"twoway scatter mpg weight if price >= 3291 & price <= 7075.5, yscale(range(0))"'
file close rtrec

python:
import json
from sfi import Macro


def num(s):
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None
    return v if v == v and abs(v) < 8.98e307 else None


probes = {}
with open(Macro.getGlobal("RT_REC"), encoding="utf-8", errors="replace") as fh:
    for line in fh:
        f = line.rstrip("\n").split("|")
        if f[0] == "P":
            probes[f[1]] = {"cmd": "|".join(f[2:]).strip(), "axes": {}}
        elif f[0] == "R":
            probes[f[1]]["rc"] = int(f[2])
        elif f[0] == "A":
            pid, tag, ax = f[1], f[2], f[3]
            rec = {"ticks": [num(v) for v in f[9].split()],
                   "major": [num(f[4]), num(f[5]), num(f[6])],
                   "cur": [num(f[7]), num(f[8])]}
            if tag == "0":
                probes[pid]["axes"][ax] = rec
            else:
                panels = probes[pid].setdefault("panels", [])
                while len(panels) < int(tag):
                    panels.append({})
                panels[int(tag) - 1][ax] = rec

doc = {"_meta": {"stata_version": Macro.getLocal("stata_version"),
                 "born_date": Macro.getLocal("born_date"),
                 "dash_commit": Macro.getLocal("dash_commit"),
                 "extracted": Macro.getLocal("extracted"),
                 "data": "sysuse auto",
                 "source": "scripts/extract_range_ticks_truth.do"},
       "probes": probes}
with open(Macro.getGlobal("RT_OUT"), "w") as fh:
    json.dump(doc, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("range_ticks_truth: wrote %d probes" % len(probes))
end
