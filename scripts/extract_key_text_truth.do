*! extract_key_text_truth.do -- WP-30 S17 (P1.23b): twoway's colour-key
*! texts (a date or number colorvar(), colorlevels(), colorcuts(),
*! zlabel() ticks and format(), zscale(range())), its refusals of a
*! zlabel() format, its histogram y titles and Stata's %7.0gc/%8.0gc/
*! %9.0gc display records, so dash's key and computed tooltips are proved
*! against a live twoway export.
*!
*! Output: test/fixtures/key_text_truth.json
*!
*! Run through the slot wrapper (CLAUDE.md rule 10):
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_key_text_truth.do
*!
*! METHOD.  scripts/svg_truth.py is the one SVG reader, used as
*! extract_colorvar_qualifier_truth.do uses it.  Per probe this records the
*! twoway command, its rc, the first line Stata printed when it refused
*! (err), the texts right of the plot region less the last one, the key's
*! title (key_texts), a histogram's y title (ytitle) and the colour
*! variable's values (data), so a test can rebuild the same key.  The
*! trailing python: block never calls back into Stata, and git rev-parse
*! is read from a file `shell` wrote, never `shell=True`.

clear all
set more off
set linesize 200

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_key_text_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_key_text_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global KT_REPO "`repo'"
global KT_OUT  "${KT_REPO}/test/fixtures/key_text_truth.json"

adopath ++ "${KT_REPO}/"
global dash_nobrowser 1

if `"`c(python_exec)'"' == "" {
    display as error "extract_key_text_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

local scratch "`c(tmpdir)'dash_key_text_probe"
capture mkdir "`scratch'"
global KT_WORK "`scratch'"

* ---- Data setups ----------------------------------------------------------
program define kt_sp500
    sysuse sp500, clear
    quietly gen m = mofd(date)
    format m %tm
    quietly gen double tc = cofd(date)
    format tc %tc
    quietly gen double dn = date
end

program define kt_auto
    sysuse auto, clear
end

program define kt_auto_g
    sysuse auto, clear
    format price %9.0g
end

program define kt_gen
    clear
    quietly set obs 50
    quietly gen x = _n
    quietly gen y = _n
    quietly gen double big = 1000000 + _n*80000
    quietly gen double tiny = .0012 + _n*.00001
    quietly gen double mid = 12345.6 + _n*.008
    quietly gen double six = 123456 + _n*.01
end

* ---- Registration: (id, data setup, colour variable, kind, command) ------
* kind: bar (continuous key), bins (colorcuts()/colorlevels()), labels
* (zlabel() labels), discrete, hist, refuse.
global KT_N = 0
program define ktp
    global KT_N = ${KT_N} + 1
    global KT_ID_${KT_N}   `"`1'"'
    global KT_DATA_${KT_N} `"`2'"'
    global KT_CV_${KT_N}   `"`3'"'
    global KT_KIND_${KT_N} `"`4'"'
    global KT_CMD_${KT_N}  `"`5'"'
end

local sc "twoway scatter close open, colorvar(date)"
ktp k_date        kt_sp500 date bar    "`sc'"
ktp k_date_lev3   kt_sp500 date bins   "`sc' colorlevels(3)"
ktp k_date_cuts   kt_sp500 date bins   "`sc' colorcuts(15100 15200)"
ktp k_date_td     kt_sp500 date bar    "`sc' zlabel(, format(%td))"
ktp k_date_n3     kt_sp500 date bar    "`sc' zlabel(#3)"
ktp k_date_minmax kt_sp500 date bar    "`sc' zlabel(minmax)"
ktp k_date_lbl    kt_sp500 date labels `"`sc' zlabel(15000 "start" 15300 "end")"'
ktp k_date_f91    kt_sp500 date bar    "`sc' zlabel(, format(%9.1fc))"
ktp k_date_lev_td kt_sp500 date bins   "`sc' colorlevels(3) zlabel(, format(%td))"
ktp k_date_zrange kt_sp500 date bar    "`sc' zscale(range(14600 15700))"
ktp k_date_tm     kt_sp500 date bar    "`sc' zlabel(, format(%tm))"
ktp k_tm          kt_sp500 m    bar    "twoway scatter close open, colorvar(m)"
ktp k_tc          kt_sp500 tc   bar    "twoway scatter close open, colorvar(tc)"
ktp k_dn          kt_sp500 dn   bar    "twoway scatter close open, colorvar(dn)"
ktp h_density     kt_sp500 date hist   "twoway histogram date,"
ktp h_frequency   kt_sp500 date hist   "twoway histogram date, frequency"
ktp h_fraction    kt_sp500 date hist   "twoway histogram date, fraction"
ktp h_percent     kt_sp500 date hist   "twoway histogram date, percent"
local ac "twoway scatter mpg weight, colorvar(price)"
ktp k_price_gc     kt_auto   price bar    "`ac'"
ktp k_price_g      kt_auto_g price bar    "`ac'"
ktp k_price_cuts   kt_auto_g price bins   "`ac' colorcuts(5000 9000)"
ktp k_price_lev3   kt_auto_g price bins   "`ac' colorlevels(3)"
ktp k_price_f92    kt_auto_g price bar    "`ac' zlabel(, format(%9.2f))"
ktp k_price_quoted kt_auto_g price bar    `"`ac' zlabel(, format("%9.2f"))"'
ktp f_bogus        kt_auto_g price refuse "`ac' zlabel(, format(bogus))"
ktp f_92x          kt_auto_g price refuse "`ac' zlabel(, format(%9.2x))"
ktp f_tdbogus      kt_auto_g price refuse "`ac' zlabel(, format(%tdbogus))"
ktp f_12s          kt_auto_g price bar    "`ac' zlabel(, format(%12s))"
ktp f_21x          kt_auto_g price bar    "`ac' zlabel(, format(%21x))"
ktp k_big          kt_gen big  bar "twoway scatter y x, colorvar(big)"
ktp k_tiny         kt_gen tiny bar "twoway scatter y x, colorvar(tiny)"
ktp k_mid          kt_gen mid  bar "twoway scatter y x, colorvar(mid)"
ktp k_six          kt_gen six  bar "twoway scatter y x, colorvar(six)"

tempname rec
local recfile "${KT_WORK}/records.txt"
capture erase "`recfile'"
file open `rec' using "`recfile'", write replace text

local kt_n = ${KT_N}
forvalues i = 1/`kt_n' {
    local id   "${KT_ID_`i'}"
    local data "${KT_DATA_`i'}"
    local cv   "${KT_CV_`i'}"
    local kind "${KT_KIND_`i'}"
    local cmd  `"${KT_CMD_`i'}"'
    `data'

    * The colour variable's values, in observation order (%21.0g).
    tempname dv
    local dfile "${KT_WORK}/`id'_data.txt"
    file open `dv' using "`dfile'", write replace text
    forvalues o = 1/`=_N' {
        file write `dv' %21.0g (`cv'[`o']) _n
    }
    file close `dv'
    local fmt : format `cv'

    local svg "${KT_WORK}/`id'.svg"
    local logf "${KT_WORK}/`id'.log"
    capture erase "`svg'"
    capture graph drop ktg
    capture log close _kt
    log using "`logf'", name(_kt) text replace
    capture noisily `cmd' name(ktg, replace)
    local rc = _rc
    log close _kt
    if `rc' == 0 {
        capture graph export "`svg'", name(ktg) replace
    }
    capture graph drop ktg
    file write `rec' `"PROBE|`id'|`rc'|`cv'|`kind'|`fmt'|`svg'|`logf'|`dfile'|`cmd'"' _n
    display as text "probe `id' rc=`rc'"
}
file close `rec'

* ---- display records --------------------------------------------------------
tempname dr
file open `dr' using "${KT_WORK}/display.txt", write replace text
foreach v in 15000 15098.333 1296000000000 1000000 1234567 .00123456 -5000 12345.75 123456.25 {
    local t7 : display %7.0gc `v'
    local t8 : display %8.0gc `v'
    local t9 : display %9.0gc `v'
    file write `dr' `"`v'|`t7'|`t8'|`t9'"' _n
}
file close `dr'

* ---- Provenance (D12) ----------------------------------------------------
global KT_STATA_VERSION = c(stata_version)
global KT_BORN_DATE     "`c(born_date)'"
global KT_EXTRACTED     "`c(current_date)'"
global KT_GHFILE "${KT_WORK}/sha.txt"
capture erase "${KT_GHFILE}"
quietly shell git -C "${KT_REPO}" rev-parse HEAD > "${KT_GHFILE}"

* ===========================================================================
* Analysis + JSON emission.  No callback into Stata from here.
* ===========================================================================
python:
import json
import os
import sys
from sfi import Macro

REPO = Macro.getGlobal("KT_REPO")
OUT = Macro.getGlobal("KT_OUT")
WORK = Macro.getGlobal("KT_WORK")

sys.path.insert(0, os.path.join(REPO, "scripts"))
from svg_truth import svg_plotregion, svg_texts

_YTITLES = ("Density", "Frequency", "Fraction", "Percent")


def _num(s):
    s = s.strip()
    return None if s in ("", ".") else float(s)


def _message(logpath):
    """The first line Stata printed for the refused command: the log
    holds only that command (run under capture noisily), between the
    log's "opened on" header and its closing "name:" line."""
    if not os.path.exists(logpath):
        return ""
    with open(logpath, "r", encoding="utf-8", errors="replace") as fh:
        lines = [ln.strip() for ln in fh if ln.strip()]
    body = False
    for ln in lines:
        if ln.startswith("opened on:"):
            body = True
            continue
        if body:
            if ln.startswith("name:"):
                break
            return " ".join(ln.split())
    return ""


probes = {}
with open(os.path.join(WORK, "records.txt"), encoding="utf-8") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if not line:
            continue
        (_t, pid, rc, cv, kind, fmt, svgpath, logpath, dfile,
         cmd) = line.split("|", 9)
        rc = int(rc)
        with open(dfile, encoding="utf-8") as dh:
            data = [_num(x) for x in dh.read().split("\n") if x.strip()]
        p = {"cmd": cmd.replace("`", "\\x60"), "rc": rc,
             "err": _message(logpath) if rc else "", "var": cv,
             "format": fmt, "kind": kind, "key_texts": [], "ytitle": "",
             "data": data}
        if rc == 0 and os.path.exists(svgpath):
            pr = svg_plotregion(svgpath) or {}
            texts = svg_texts(svgpath)
            if kind != "hist":
                right = [t["text"] for t in texts
                         if pr and t.get("x") is not None
                         and t["x"] > pr["right"]]
                p["key_texts"] = right[:-1]
            else:
                hits = [t["text"] for t in texts if t["text"] in _YTITLES]
                p["ytitle"] = hits[0] if hits else ""
        probes[pid] = p

display = {}
with open(os.path.join(WORK, "display.txt"), encoding="utf-8") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if not line:
            continue
        v, t7, t8, t9 = line.split("|")
        display[v] = {"%7.0gc": t7, "%8.0gc": t8, "%9.0gc": t9}

dash_commit = ""
ghfile = Macro.getGlobal("KT_GHFILE")
if os.path.exists(ghfile):
    with open(ghfile, encoding="utf-8") as fh:
        dash_commit = fh.read().strip()

meta = {
    "stata_version": Macro.getGlobal("KT_STATA_VERSION"),
    "born_date": Macro.getGlobal("KT_BORN_DATE"),
    "source": "scripts/extract_key_text_truth.do",
    "dash_commit": dash_commit,
    "extracted": Macro.getGlobal("KT_EXTRACTED"),
    "script": "scripts/extract_key_text_truth.do",
}
out = {"_meta": meta, "display": display, "probes": probes}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
print("wrote", OUT, "with", len(probes), "probes")
end
