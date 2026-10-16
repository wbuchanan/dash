*! extract_stata_ticks_truth.do
*! WP-31 S45 (D15): the ticks Stata's own _natscale and _tsnatscale give over
*! an axis's data, beside the ticks twoway draws on that axis.
*!
*! Per probe: the axis variable's range over the drawn rows (summarize), the
*! routine's answer over that range (r(min) r(max) r(delta) r(n), and
*! _tsnatscale's r(list)), the ticks that answer gives (_natscale: r(min) in
*! steps of r(delta) while at most r(max); _tsnatscale: r(list), else r(min)
*! + k*r(delta) for k below r(n)) and the drawn graph's
*! .<axis>.major.dlg_tickpos list.  Plus the cost of the work dash adds per
*! axis (a marker, summarize and _natscale) over 1,000,000 rows.  Records
*! go to a file under c(tmpdir); the trailing python: block reads it into
*! test/fixtures/stata_ticks_truth.json, never calls Stata and starts no
*! subprocess.
*!
*! Run (Stata only through the slot wrapper, never the GUI):
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> \
*!       <repo>/scripts/extract_stata_ticks_truth.do

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_stata_ticks_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
if _rc {
    display as error "extract_stata_ticks_truth.do: set DASH_REPO to the repository root"
    exit 601
}

clear all
set more off
set linesize 255
version 19
set graphics off
set scheme stcolor

global ST_REPO "`repo'"
global ST_OUT "${ST_REPO}/test/fixtures/stata_ticks_truth.json"
local work "`c(tmpdir)'dash_stata_ticks_probe"
capture mkdir "`work'"
global ST_REC "`work'/st_records.txt"

local stata_version = c(stata_version)
local born_date "`c(born_date)'"
local extracted "`c(current_date)'"
tempfile stgit
quietly shell git -C "${ST_REPO}" rev-parse HEAD > "`stgit'"
tempname stgh
file open `stgh' using "`stgit'", read text
file read `stgh' stline
file close `stgh'
local dash_commit = trim(`"`stline'"')

capture program drop _st_data
program _st_data
    args which
    if "`which'" == "auto" {
        sysuse auto, clear
        exit
    }
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
    quietly generate double tc = cofd(date) + 3600000 * mod(_n, 7)
    format tc %tc
end

capture program drop _st_rec
program _st_rec
    // _st_rec <id> <data> <axis> <var> <n> <unit> <panel> `"<rows>"' `"<command>"'
    // <rows> selects the rows the axis draws for summarize; the command
    // carries its own if.
    args id data ax var n unit panel rows cmd
    _st_data `data'
    capture graph drop _all
    quietly summarize `var' `rows', meanonly
    local lo = strofreal(r(min), "%21x")
    local hi = strofreal(r(max), "%21x")
    local olo = r(min)
    local ohi = r(max)
    if "`unit'" == "-" quietly _natscale `lo' `hi' `n'
    else {
        local word : word `=strpos("dwmqhy", "`unit'")' of daily weekly monthly quarterly halfyearly yearly
        quietly _tsnatscale `lo' `hi' `n', `word'
    }
    file write strec `"P|`id'|`data'|`ax'|`n'|`unit'|`panel'|`=strofreal(`olo', "%21.0g")'|`=strofreal(`ohi', "%21.0g")'|`=strofreal(r(min), "%21.0g")'|`=strofreal(r(max), "%21.0g")'|`=strofreal(r(delta), "%21.0g")'|`=strofreal(r(n), "%21.0g")'|`r(list)'|`cmd'"' _n
    capture noisily `cmd'
    local rc = _rc
    local d = substr("`ax'", 1, 1)
    local k = substr("`ax'", 2, 1)
    local p ".Graph"
    if "`panel'" != "-" local p ".Graph.graphs[`panel']"
    local a "`p'.`d'axis`k'"
    local nt "`.`a'.major.dlg_tickpos.arrnels'"
    if "`nt'" == "" | "`nt'" == "." local nt 0
    local v ""
    forvalues i = 1/`nt' {
        local v "`v' `.`a'.major.dlg_tickpos[`i']'"
    }
    file write strec `"D|`id'|`rc'|`v'"' _n
    capture graph drop _all
end

file open strec using "${ST_REC}", write text replace
_st_rec P4   auto   y1 price 4 - - `""'               `"twoway scatter price mpg, ylabel(#4)"'
_st_rec T2   auto   y1 trunk 2 - - `""'               `"twoway scatter trunk mpg, ylabel(#2)"'
_st_rec T3   auto   y1 trunk 3 - - `""'               `"twoway scatter trunk mpg, ylabel(#3)"'
_st_rec P5   auto   y1 price 5 - - `""'               `"twoway scatter price mpg"'
_st_rec MF   auto   y1 mpg   5 - - `"if foreign"'     `"twoway scatter mpg weight if foreign"'
_st_rec HZX  auto   x1 mpg   5 - - `""'               `"twoway rcap mpg mpg weight, horizontal"'
_st_rec HZY  auto   y1 weight 5 - - `""'              `"twoway rcap mpg mpg weight, horizontal"'
_st_rec BY1  auto   x1 weight 5 - 1 `"if foreign == 0"' `"twoway scatter price weight, by(foreign, xrescale)"'
_st_rec BY2  auto   x1 weight 5 - 2 `"if foreign == 1"' `"twoway scatter price weight, by(foreign, xrescale)"'
_st_rec TD   sp500  x1 date  5 d - `""'               `"twoway line close date"'
_st_rec IF2  sp500  x1 date  5 d - `"if close > 1200"' `"twoway line close date if close > 1200"'
_st_rec TW   sp500  x1 w     5 w - `""'               `"twoway scatter close w"'
_st_rec TM   sp500  x1 m     5 m - `""'               `"twoway scatter close m"'
_st_rec TQ   sp500  x1 q     5 q - `""'               `"twoway scatter close q"'
_st_rec TH   sp500  x1 h     5 h - `""'               `"twoway scatter close h"'
_st_rec TY   yearly x1 y     5 y - `""'               `"twoway line val y"'
_st_rec TC   sp500  x1 tc    5 - - `""'               `"twoway line close tc"'
file close strec

* The work dash adds per axis, over 1,000,000 rows of a %tc variable: a
* marker column, summarize over it, and _natscale.
clear
quietly set obs 1000000
quietly generate double tc = 1.6e12 + 60000 * _n
format tc %tc
quietly generate byte __m = mod(_n, 3) > 0
timer clear 1
timer on 1
tempvar lu
quietly generate byte `lu' = 1
quietly replace `lu' = 0 if __m != 1
quietly summarize tc if `lu', meanonly
local a = strofreal(r(min), "%21x")
local b = strofreal(r(max), "%21x")
quietly _natscale `a' `b' 5
timer off 1
quietly timer list 1
global ST_T1E6 = r(t1)

python:
import json, math
from sfi import Macro


def num(s):
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None
    return v if v == v and abs(v) < 8.98e307 else None


probes = {}
cur = None
with open(Macro.getGlobal("ST_REC"), encoding="utf-8", errors="replace") as fh:
    for line in fh:
        f = line.rstrip("\n").split("|")
        if f[0] == "P":
            pid = f[1]
            unit = "" if f[5] == "-" else f[5]
            mn, mx, de, rn = num(f[9]), num(f[10]), num(f[11]), num(f[12])
            lst = [num(v) for v in f[13].split()]
            if unit == "":
                t, k = [], 0
                while mn + k * de <= mx + 1e-9 * de and k <= 2000:
                    t.append(float("%.15g" % (mn + k * de)))
                    k += 1
            elif lst:
                t = lst
            else:
                t = [float("%.12g" % (mn + k * de)) for k in range(int(rn))]
            probes[pid] = {"data": f[2], "axis": f[3], "n": int(f[4]),
                           "unit": unit,
                           "panel": None if f[6] == "-" else int(f[6]),
                           "data_lo": num(f[7]), "data_hi": num(f[8]),
                           "routine": {"min": mn, "max": mx, "delta": de,
                                       "n": rn, "list": lst},
                           "stata_ticks": t,
                           "cmd": "|".join(f[14:]).strip()}
        elif f[0] == "D":
            probes[f[1]]["rc"] = int(f[2])
            probes[f[1]]["drawn_ticks"] = [num(v) for v in f[3].split()]

doc = {"_meta": {"stata_version": Macro.getLocal("stata_version"),
                 "born_date": Macro.getLocal("born_date"),
                 "dash_commit": Macro.getLocal("dash_commit"),
                 "extracted": Macro.getLocal("extracted"),
                 "source": "scripts/extract_stata_ticks_truth.do"},
       "probes": probes,
       "time": {"reg_1e6": num(Macro.getGlobal("ST_T1E6"))}}
with open(Macro.getGlobal("ST_OUT"), "w") as fh:
    json.dump(doc, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("stata_ticks_truth: wrote %d probes" % len(probes))
end

display as text "extract_stata_ticks_truth.do: done"
