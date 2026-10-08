*! extract_date_axes_truth.do
*! WP-30 S44 (P1.3b): twoway's default date axes -- the ticks _tsnatscale
*! gives a %td, %tw, %tm, %tq, %th and %ty axis with no label rule, a second
*! date axis, a date beside a number, a by() date graph and the if()
*! subsets the tests' filter moves keep.
*!
*! Per probe: .Graph.{x,y}axis{1,2}.major.{min,max,delta}, the tick list
*! .major.dlg_tickpos[i] (delta is 0 on a date axis), the scale's
*! curmin/curmax, and the axis variable's range over the drawn rows
*! (summarize).  Records go to a file under c(tmpdir); the trailing python:
*! block reads it into test/fixtures/date_axes_truth.json, never calls
*! Stata and starts no subprocess.
*!
*! Run (Stata only through the slot wrapper, never the GUI):
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> \
*!       <repo>/scripts/extract_date_axes_truth.do

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_date_axes_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_date_axes_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
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

global DT_REPO "`repo'"
global DT_OUT "${DT_REPO}/test/fixtures/date_axes_truth.json"
local work "`c(tmpdir)'dash_date_axes_probe"
capture mkdir "`work'"
global DT_WORK "`work'"
global DT_REC "`work'/dt_records.txt"

local stata_version = c(stata_version)
local born_date "`c(born_date)'"
local extracted "`c(current_date)'"
tempfile dtgit
quietly shell git -C "${DT_REPO}" rev-parse HEAD > "`dtgit'"
tempname dtgh
file open `dtgh' using "`dtgit'", read text
file read `dtgh' dtline
file close `dtgh'
local dash_commit = trim(`"`dtline'"')

capture program drop _dt_data
program _dt_data
    args which
    if "`which'" == "yearly" {
        clear
        quietly set obs 40
        quietly generate y = 1960 + _n
        format y %ty
        quietly generate val = mod(_n * 7, 23)
        exit
    }
    sysuse sp500, clear
    quietly generate w = wofd(date)
    format w %tw
    quietly generate m = mofd(date)
    format m %tm
    quietly generate q = qofd(date)
    format q %tq
    quietly generate h = hofd(date)
    format h %th
    quietly generate g = mod(_n, 2)
    quietly generate obs = _n
end

capture program drop _dt_axis
program _dt_axis
    // one line: the major ticks and scale of axis `ax' (x1, x2, y1) of `p'
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
    file write dtrec `"A|`id'|`tag'|`ax'|``a'.major.min'|``a'.major.max'|``a'.major.delta'|``s'.curmin'|``s'.curmax'|`v'"' _n
end

capture program drop _dt_rec
program _dt_rec
    // _dt_rec <id> <data> <axes> <var> `"<if>"' `"<command>"'
    args id data axes var cond cmd
    _dt_data `data'
    capture graph drop _all
    quietly summarize `var' `cond'
    file write dtrec `"P|`id'|`data'|`r(min)'|`r(max)'|`cmd' `cond'"' _n
    capture noisily `cmd' `cond'
    local rc = _rc
    file write dtrec `"R|`id'|`rc'"' _n
    if `rc' == 0 {
        capture graph export "${DT_WORK}/`id'.svg", replace
        local n "`.Graph.graphs.arrnels'"
        if "`n'" == "" | "`n'" == "." local n 0
        if `n' > 0 {
            forvalues k = 1/`n' {
                foreach ax of local axes {
                    _dt_axis `id' `k' ".Graph.graphs[`k']" `ax'
                }
            }
        }
        else {
            foreach ax of local axes {
                _dt_axis `id' 0 ".Graph" `ax'
            }
        }
    }
    capture graph drop _all
end

file open dtrec using "${DT_REC}", write text replace
_dt_rec TD   sp500  "x1"    date  `""'                      `"twoway line close date"'
_dt_rec N5   sp500  "x1"    date  `""'                      `"twoway line close date, xlabel(#5)"'
_dt_rec TW   sp500  "x1"    w     `""'                      `"twoway scatter close w"'
_dt_rec TM   sp500  "x1"    m     `""'                      `"twoway scatter close m"'
_dt_rec TQ   sp500  "x1"    q     `""'                      `"twoway scatter close q"'
_dt_rec TH   sp500  "x1"    h     `""'                      `"twoway scatter close h"'
_dt_rec TY   yearly "x1"    y     `""'                      `"twoway line val y"'
_dt_rec Y2   sp500  "x1 x2" date  `""'                      `"twoway (line close date) (line volume date, xaxis(2))"'
_dt_rec MIX  sp500  "x1"    obs   `""'                      `"twoway (scatter close date) (scatter close obs)"'
_dt_rec MIXN sp500  "x1"    obs   `""'                      `"twoway (scatter close date) (scatter close obs), xlabel(#5)"'
_dt_rec BY   sp500  "x1"    date  `""'                      `"twoway line close date, by(g)"'
_dt_rec IF1  sp500  "x1"    date  `"if date <= 15100"'      `"twoway line close date"'
_dt_rec IF2  sp500  "x1"    date  `"if close > 1200"'       `"twoway line close date"'
_dt_rec IF3  sp500  "x1"    m     `"if m >= 492 & m <= 497"' `"twoway scatter close m"'
file close dtrec

python:
import json
from sfi import Macro


def num(s):
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None
    return v if v == v and abs(v) < 8.98e307 else None


probes, order = {}, []
with open(Macro.getGlobal("DT_REC"), encoding="utf-8", errors="replace") as fh:
    for line in fh:
        f = line.rstrip("\n").split("|")
        if f[0] == "P":
            probes[f[1]] = {"data": f[2], "data_lo": num(f[3]),
                            "data_hi": num(f[4]), "cmd": "|".join(f[5:]).strip()}
            order.append(f[1])
        elif f[0] == "R":
            probes[f[1]]["rc"] = int(f[2])
        elif f[0] == "A":
            pid, tag, ax = f[1], f[2], f[3]
            name = {"x1": "x", "x2": "x2", "y1": "y"}[ax]
            rec = {"major": [num(f[4]), num(f[5]), num(f[6])],
                   "cur": [num(f[7]), num(f[8])],
                   "list": [num(v) for v in f[9].split()]}
            if tag == "0":
                probes[pid][name] = rec
            else:
                probes[pid].setdefault("panels", []).append({name: rec})

doc = {"_meta": {"stata_version": Macro.getLocal("stata_version"),
                 "born_date": Macro.getLocal("born_date"),
                 "dash_commit": Macro.getLocal("dash_commit"),
                 "extracted": Macro.getLocal("extracted"),
                 "units": "Stata units of the axis variable",
                 "source": "scripts/extract_date_axes_truth.do"},
       "probes": probes}
with open(Macro.getGlobal("DT_OUT"), "w") as fh:
    json.dump(doc, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("date_axes_truth: wrote %d probes" % len(probes))
end

display as text "extract_date_axes_truth.do: done"
