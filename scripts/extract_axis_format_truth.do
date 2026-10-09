*! extract_axis_format_truth.do
*! WP-30 S18 (P1.5): twoway's tick-label text, refusals and acceptances for
*! the display format each axis is labelled in.  Every label is what THIS
*! run's twoway wrote into its own SVG; nothing is guessed.
*!
*! Output: test/fixtures/axis_format_truth.json
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_axis_format_truth.do
*!
*! The trailing python: block reads files and locals only and calls no
*! Stata; a backtick in it is spelled \x60.

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_axis_format_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_axis_format_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1

clear all
version 19
set graphics off
set more off
set linesize 255
set scheme stcolor

global AF_REPO "`repo'"
global AF_OUT "${AF_REPO}/test/fixtures/axis_format_truth.json"
local work "`c(tmpdir)'dash_axis_format_probe"
capture mkdir "`work'"
global AF_WORK "`work'"
global AF_REC "`work'/af_records.txt"

global AF_SVER = c(stata_version)
global AF_BORN = c(born_date)
global AF_DATE = c(current_date)

tempfile afgit
quietly shell git -C "${AF_REPO}" rev-parse HEAD > "`afgit'"
tempname afgh
file open `afgh' using "`afgit'", read text
file read `afgh' afgline
file close `afgh'
local dash_commit = trim(`"`afgline'"')

capture program drop _af_load
program _af_load
    args data
    if "`data'" == "sp500" {
        sysuse sp500, clear
        quietly tsset date
        quietly generate m = mofd(date)
        format m %tm
    }
    else sysuse auto, clear
end

capture program drop _af_probe
program _af_probe
    // _af_probe <id> <group> <data> "<setup>" `"<command>"'
    args id group data setup cmd
    _af_load `data'
    if `"`setup'"' != "" {
        quietly `setup'
    }
    capture graph drop _all
    capture log close aflog
    quietly log using "${AF_WORK}/`id'.log", text replace name(aflog)
    capture noisily `cmd'
    local rc = _rc
    quietly log close aflog
    file write afrec `"P|`id'|`group'|`data'|`rc'|`setup'|`cmd'"' _n
    if `rc' == 0 {
        capture graph export "${AF_WORK}/`id'.svg", replace
        if _rc file write afrec `"X|`id'|`=_rc'"' _n
    }
    capture graph drop _all
end

file open afrec using "${AF_REC}", write text replace

foreach d in auto sp500 {
    _af_load `d'
    foreach v of varlist _all {
        local f : format `v'
        file write afrec `"D|`d'|`v'|`f'"' _n
    }
}

local T "twoway"
* ---- d: default ticks ----
_af_probe d01 d auto "" `"`T' scatter mpg weight"'
_af_probe d02 d auto "format weight %9.0fc" `"`T' scatter mpg weight"'
_af_probe d03 d auto "format weight %9.2f" `"`T' scatter mpg weight"'
_af_probe d04 d auto "" `"`T' scatter gear_ratio weight"'
_af_probe d05 d auto "generate r = gear_ratio/10" `"`T' scatter r weight"'
_af_probe d06 d auto "format price %9.2e" `"`T' scatter price weight"'
_af_probe d07 d auto "format gear_ratio %9,2f" `"`T' scatter gear_ratio weight"'
_af_probe d08 d auto "format price %9.0g" `"`T' scatter price weight"'
_af_probe d09 d auto "format weight %-9.0fc" `"`T' scatter mpg weight"'
_af_probe d10 d auto "format mpg %9.2f" `"`T' scatter mpg weight, by(foreign)"'
* ---- k: a rule kept ----
_af_probe k01 k auto "" `"`T' scatter price weight, ylabel(#5)"'
_af_probe k02 k auto "" `"`T' scatter mpg weight, xlabel(2000(1000)5000)"'
_af_probe k03 k auto "" `"`T' scatter mpg weight, xlabel(minmax)"'
_af_probe k04 k auto "" `"`T' scatter price weight, yscale(log) ylabel(#5)"'
_af_probe k05 k auto "" `"`T' scatter price weight, yscale(log)"'
_af_probe k06 k auto "" `"`T' scatter mpg weight, xlabel(2000 "two" 3000 4000)"'
_af_probe k07 k auto "" `"`T' scatter mpg weight, xlabel(2000 "two" 3000 4000, format(%9.1f))"'
* ---- l: layer types ----
_af_probe l01 l auto "" `"`T' rarea price mpg weight"'
_af_probe l02 l auto "" `"`T' rarea mpg price weight"'
_af_probe l03 l auto "" `"`T' pcspike mpg weight price length"'
_af_probe l04 l auto "" `"`T' scatteri 20 3000 30 4000"'
_af_probe l05 l auto "" `"`T' lfit price weight"'
_af_probe l06 l auto "" `"`T' lpoly price weight"'
_af_probe l07 l auto "" `"`T' kdensity price"'
_af_probe l08 l auto "" `"`T' lowess price weight"'
_af_probe l09 l auto "" `"`T' mspline price weight"'
_af_probe l10 l auto "" `"`T' histogram price"'
_af_probe l11 l auto "" `"`T' histogram price, frequency"'
_af_probe l12 l auto "" `"`T' histogram price, fraction"'
_af_probe l13 l auto "" `"`T' histogram price, percent"'
_af_probe l14 l auto "" `"`T' function y = x, range(0 1)"'
_af_probe l15 l sp500 "" `"`T' tsline close"'
_af_probe l16 l auto "" `"`T' fpfit price weight"'
_af_probe l17 l auto "" `"`T' mband price weight"'
* ---- m: several layers and axis 2 ----
_af_probe m01 m auto "" `"`T' scatter mpg price weight"'
_af_probe m02 m auto "" `"`T' scatter price mpg weight"'
_af_probe m03 m auto "" `"`T' (scatter mpg length) (scatter mpg weight)"'
_af_probe m04 m auto "" `"`T' (lfit price weight) (scatter price weight)"'
_af_probe m05 m auto "" `"`T' (scatter price weight) (lfit price weight)"'
_af_probe m06 m auto "" `"`T' (kdensity weight) (scatter mpg weight)"'
_af_probe m07 m auto "" `"`T' (scatter mpg weight) (scatter price weight, yaxis(2))"'
_af_probe m08 m auto "" `"`T' (scatter mpg weight) (scatter price weight, yaxis(2)), ylabel(, axis(2) format(%9.1f))"'
_af_probe m09 m auto "" `"`T' (scatter mpg length) (scatter mpg weight, yaxis(2))"'
_af_probe m10 m auto "" `"`T' (scatter mpg weight, yaxis(2)) (scatter mpg length)"'
_af_probe m11 m auto "" `"`T' (scatter mpg weight) (scatter mpg length, yaxis(2)) (scatter price weight, yaxis(2))"'
_af_probe m12 m auto "" `"`T' (scatter mpg weight, yaxis(2)) (scatter mpg weight, yaxis(2)) (scatter mpg length)"'
_af_probe m13 m auto "" `"`T' (scatter mpg weight, yaxis(2)) (scatter mpg length, yaxis(2))"'
_af_probe m14 m auto "" `"`T' (scatter mpg weight) (scatter price weight, xaxis(2))"'
_af_probe m15 m auto "" `"`T' (scatter price weight, xaxis(2)) (scatter mpg weight)"'
* ---- e: explicit format ----
_af_probe e01 e sp500 "" `"`T' line close date, xlabel(, format(%9.0fc))"'
_af_probe e02 e sp500 "" `"`T' line close date, xlabel(, format(%9.0f))"'
_af_probe e03 e sp500 "" `"`T' line close date, xlabel(, format(%tdDD/NN/CCYY))"'
_af_probe e04 e sp500 "" `"`T' line close date, xlabel(, format(%tm))"'
_af_probe e05 e sp500 "" `"`T' line close date, xlabel(15000(100)15300, format(%tdDD/NN/CCYY))"'
_af_probe e06 e sp500 "" `"`T' line date close, ylabel(, format(%9.0g))"'
_af_probe e07 e sp500 "" `"`T' line close m, xlabel(, format(%td))"'
_af_probe e08 e sp500 "" `"`T' line close m, xlabel(, format(%9.0fc))"'
_af_probe e09 e auto "" `"`T' scatter mpg weight, xlabel(, format(%td))"'
_af_probe e10 e auto "" `"`T' scatter mpg weight, xlabel(, format(%12s))"'
_af_probe e11 e auto "" `"`T' scatteri 123456789 1 223456789 2, ylabel(, format(%12s))"'
_af_probe e12 e auto "" `"`T' scatter mpg weight, xlabel(, format(%21x))"'
_af_probe e13 e auto "" `"`T' scatter mpg weight, xlabel(, format(%9.2f %9.1f))"'
_af_probe e14 e auto "" `"`T' scatter mpg weight, xlabel(, format("%9.2f"))"'
_af_probe e15 e auto "" `"`T' scatter mpg weight, xlabel(, format())"'
_af_probe e16 e auto "" `"`T' scatter mpg weight, xlabel(, for(%9.1f))"'
* ---- v: varformat ----
_af_probe v01 v auto "" `"`T' scatter mpg weight, xvarformat(%9.2f) yvarformat(%9.1f)"'
_af_probe v02 v auto "" `"`T' (scatter mpg weight) (scatter price weight, yaxis(2) yvarformat(%9.1f)),"'
_af_probe v03 v auto "" `"`T' (lfit mpg weight, xvarformat(%9.2f) yvarformat(%9.1f)) (scatter mpg weight),"'
_af_probe v04 v auto "" `"`T' (scatter mpg weight) (lfit mpg weight, xvarformat(%9.2f) yvarformat(%9.1f)),"'
_af_probe v05 v auto "" `"`T' (scatter mpg weight) (scatter price weight, yvarformat(%9.1f)),"'
_af_probe v06 v auto "" `"`T' histogram price, yvarformat(%9.3f)"'
_af_probe v07 v auto "" `"`T' histogram price, xvarformat(%9.1f)"'
_af_probe v08 v auto "" `"`T' rarea price mpg weight, yvarformat(%9.1f)"'
_af_probe v09 v auto "" `"`T' pcspike mpg weight price length, yvarformat(%9.1f) xvarformat(%9.2f)"'
_af_probe v10 v auto "" `"`T' scatter mpg weight, xvarformat(%td)"'
_af_probe v11 v auto "" `"`T' scatter mpg weight, xvarformat(%9.2f) xvarformat(%9.1f)"'
_af_probe v12 v auto "" `"`T' (scatter mpg weight) (scatter mpg weight, xvarformat(%9.1f)), xlabel(, format(%9.3f))"'
_af_probe v13 v auto "" `"`T' scatter mpg weight, xvarformat(%9.1f) xlabel(2000 "two" 3000)"'
_af_probe v14 v auto "" `"`T' scatter mpg weight, xvarformat(%9.2f bogus)"'
_af_probe v15 v auto "" `"`T' scatter mpg weight, xvarformat(bogus)"'
_af_probe v16 v auto "" `"`T' scatter mpg weight, xvarformat()"'
* ---- r: refusals ----
local i = 0
foreach f in "bogus" "%9.999999999f" "%2046.0f" "%0.0f" "%9.2" "9.2f" "%c" "%" "%9.2f_n" "%9.2fcc" "%9.9f" "%tdbogus" "%9.2f bogus" "bogus %9.2f" "%9.1f," {
    local ++i
    local id = "r" + string(`i', "%02.0f")
    _af_probe `id' r auto "" `"`T' scatter mpg weight, xlabel(, format(`f'))"'
}
_af_probe r16 r auto "" `"`T' scatter mpg weight, xtick(, format(bogus))"'
_af_probe r17 r auto "" `"`T' scatter mpg weight, xmlabel(, format(bogus))"'
_af_probe r18 r auto "" `"`T' scatter mpg weight, by(foreign) xlabel(, format(bogus))"'
_af_probe r19 r auto "" `"`T' (scatter mpg weight) (scatter price weight, yaxis(2)), ylabel(, axis(2) format(bogus))"'
_af_probe r20 r auto "" `"`T' (scatter mpg weight) (scatter mpg length), xvarformat(%9.2f)"'
_af_probe r21 r auto "" `"`T' scatter mpg weight, xvar(%9.2f)"'
* ---- a: accepted words ----
local i = 0
foreach f in "%300.0f" "%12s" "%-12s" "%21x" "%16H" "%16L" "%tdDD/NN/CCYY" "%tbxyz" "%tq" "%d" "%-9.0g" "%09.0f" "%5.4f" "%9,2f" "%253.0f" "%254.0f" "%9.0gc" "%9.2f %9.1f" `""%9.2f""' "" {
    local ++i
    local id = "a" + string(`i', "%02.0f")
    _af_probe `id' a auto "" `"`T' scatter mpg weight, xlabel(, format(`f'))"'
}
file close afrec

python:
import json, os, re, sys
from sfi import Macro

REPO = Macro.getGlobal("AF_REPO")
WORK = Macro.getGlobal("AF_WORK")
sys.path.insert(0, os.path.join(REPO, "scripts"))
import svg_truth

datasets, cases = {}, {}
order = []
with open(Macro.getGlobal("AF_REC"), encoding="utf-8", errors="replace") as fh:
    for line in fh:
        f = line.rstrip("\n").split("|")
        if f[0] == "D":
            datasets.setdefault(f[1], {})[f[2]] = f[3]
        elif f[0] == "P":
            cid, group, data, rc, setup = f[1], f[2], f[3], int(f[4]), f[5]
            cmd = "|".join(f[6:])
            cases[cid] = {"group": group, "data": data,
                          "setup": [setup] if setup else [], "command": cmd,
                          "rc": rc, "errors": [], "x": [], "y": [],
                          "x2": [], "y2": [], "values_from": ""}
            order.append(cid)


def errors_of(cid, rc):
    # The probe's log holds only what the refused command printed.
    try:
        with open(os.path.join(WORK, cid + ".log"), encoding="utf-8",
                  errors="replace") as fh:
            return [l.strip() for l in fh if l.strip()]
    except OSError:
        return []


def side_labels(doc, side):
    pr = doc["plotregion"]
    if pr is None:
        return []
    if side == "y2":
        cand = [t for t in doc["texts"] if t["x"] is not None
                and t["x"] > pr["right"] and t.get("anchor") != "middle"]
        key, order_key = "x", lambda t: -t["y"]
    else:
        cand = [t for t in doc["texts"] if t["y"] is not None
                and t["y"] < pr["top"] and t.get("anchor") == "middle"]
        key, order_key = "y", lambda t: t["x"]
    if not cand:
        return []
    near = (min(c[key] for c in cand) if side == "y2"
            else max(c[key] for c in cand))
    row = [c for c in cand if abs(c[key] - near) < 2.5]
    return [c["text"] for c in sorted(row, key=order_key)]


for cid in order:
    c = cases[cid]
    if c["rc"]:
        c["errors"] = errors_of(cid, c["rc"])
        continue
    svg = os.path.join(WORK, cid + ".svg")
    if not os.path.exists(svg):
        continue
    doc = svg_truth.svg_document(svg)
    for ax in ("x", "y"):
        try:
            c[ax] = list(svg_truth.svg_axis_reading(svg, ax, doc=doc)
                         .get("labels") or [])
        except Exception:
            c[ax] = []
    if "yaxis(2)" in c["command"]:
        c["y2"] = side_labels(doc, "y2")
    if "xaxis(2)" in c["command"]:
        c["x2"] = side_labels(doc, "x2")

for cid, frm in (("e03", "e02"), ("e04", "e02"), ("e05", "e02"),
                 ("e07", "e08"), ("e09", "d01")):
    if cid in cases:
        cases[cid]["values_from"] = frm

doc = {
    "_meta": {"stata_version": Macro.getGlobal("AF_SVER"),
              "born_date": Macro.getGlobal("AF_BORN"),
              "dash_commit": Macro.getLocal("dash_commit"),
              "extracted": Macro.getGlobal("AF_DATE"),
              "scheme": "stcolor",
              "script": "scripts/extract_axis_format_truth.do"},
    "datasets": datasets,
    "cases": cases,
}
with open(Macro.getGlobal("AF_OUT"), "w") as fh:
    json.dump(doc, fh, indent=2, sort_keys=True)
    fh.write("\n")
print("WROTE %s cases=%d" % (Macro.getGlobal("AF_OUT"), len(cases)))
end

display as text "extract_axis_format_truth.do: done"
