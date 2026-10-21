*! extract_by_types_truth.do
*! WP-33 section 33-12 (BY-23): ground truth for every plot type's
*! per-panel data under by(), for test/fixtures/by_types_truth.json.
*!
*! WHY THIS EXISTS
*!
*! Per-type by() drawing was pinned against twoway only for function
*! (default range) and lpoly; histogram, kdensity, scatter, line and bar
*! were checked only for their panel count and saved/served agreement, and
*! no fixture held twoway's per-panel data for the fits, ci bands,
*! smooths, bins, range, pc or immediate types.  This script records, for
*! each of the 44 plot types under by(foreign) and by(foreign, total),
*! every serset twoway builds -- one per plot per panel, panel-major, the
*! Total panel last -- so test/test_by_types.py can compare dash's panels
*! with them in both modes.
*!
*! Output: test/fixtures/by_types_truth.json
*!
*! Run with:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_by_types_truth.do
*!
*! METHOD
*!
*! Every probe is `zbt id "cmd" "byopts"': the data are reloaded, every
*! serset and graph dropped, and `twoway (<cmd>), by(foreign<byopts>)
*! nodraw' is run under a text log.  On rc 0 the panel count
*! (.Graph.graphs.arrnels), the serset each panel's plot draws (its
*! .plotregion1.plot1.serset id, yvar and xvar) and every serset are
*! written to a record file (for contour and contourline, drawn once more,
*! each panel's .lastcuts too):
*! its variable names, N, the rows with no missing value, the drawn rows
*! (first two columns not missing), each column's minimum and maximum
*! over every row and over the drawn rows, and either every row
*! (N <= 41) or the 11 rows of extract_stat_truth.do's zq_curve rule
*! (1-based index round(1 + (k-1)*(N-1)/10), k = 1..11).  The trailing python: block
*! reads files only (never calls Stata; a backtick is spelled \x60) and
*! writes the fixture.
*! ---------------------------------------------------------------------------

clear all
set graphics off
set more off
set linesize 255
version 19

* Root: DASH_REPO, else the current directory when it is a dash tree;
* never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_by_types_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_by_types_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1
global ZBT_REPO "`repo'"
global ZBT_OUT  "`repo'/test/fixtures/by_types_truth.json"
local scratch "`c(tmpdir)'dash_by_types_probe"
capture mkdir "`scratch'"
global ZBT_WORK "`scratch'"
global ZBT_REC  "`scratch'/by_types_records.txt"

global ZBT_SVER = c(stata_version)
global ZBT_BORN = c(born_date)
global ZBT_DATE = c(current_date) + " " + c(current_time)

// Provenance stamp: `shell' writes the commit into a file, read back.
tempfile zbtgitrev
quietly shell git -C "${ZBT_REPO}" rev-parse HEAD > "`zbtgitrev'"
tempname zbtgfh
file open `zbtgfh' using "`zbtgitrev'", read text
file read `zbtgfh' zbtgitline
file close `zbtgfh'
global ZBT_COMMIT = trim(`"`zbtgitline'"')
capture assert ustrregexm(`"${ZBT_COMMIT}"', "^[0-9a-f]{40}$")
if _rc {
    display as error "extract_by_types_truth.do: git rev-parse HEAD did not print a 40-character commit: ${ZBT_COMMIT}"
    exit 498
}

// ---------------------------------------------------------------------------
// The data: auto's mpg weight price foreign, with t = _n, tsset t (for
// tsline and tsrline).  Every probe reloads this file.
// ---------------------------------------------------------------------------
sysuse auto, clear
generate double t = _n
keep mpg weight price foreign t
quietly tsset t
quietly save "${ZBT_WORK}/zbt.dta", replace

python:
import sys
from sfi import Macro
sys.path.insert(0, Macro.getGlobal("ZBT_REPO"))
import dash_render
dash_render._dash_write_stata_data(
    Macro.getGlobal("ZBT_WORK") + "/data.json", "mpg weight price foreign t")
end

// ---------------------------------------------------------------------------
// zbt_serset s id j: serset id s of the graph just drawn (the j-th,
// 0-based), loaded and written.
// `serset use' may name columns __00000k, which Stata drops as temporaries
// when the program that loaded them returns (extract_stat_truth.do's
// zq_serset), so everything is read here, under names c1..ck.
// ---------------------------------------------------------------------------
capture program drop zbt_serset
program define zbt_serset
    version 19
    args s id j0
    quietly serset set `s'
    quietly serset use, clear
    quietly ds
    local vl `r(varlist)'
    local k : word count `vl'
    local names ""
    forvalues j = 1/`k' {
        local old : word `j' of `vl'
        if substr("`old'", 1, 2) == "__" local names "`names' _"
        else local names "`names' `old'"
        quietly rename `old' zc`j'
    }
    local names = trim("`names'")
    quietly count
    local n = r(N)
    local cond "1"
    forvalues j = 1/`k' {
        local cond "`cond' & !missing(zc`j')"
    }
    quietly count if `cond'
    local nc = r(N)
    * The drawn rows: those whose first two columns are not missing (a
    * later column can be padding, as kdensity's raw variable is).
    local dcond "!missing(zc1)"
    if `k' > 1 local dcond "`dcond' & !missing(zc2)"
    quietly count if `dcond'
    local nd = r(N)
    file write zbtrec "S|`id'|`j0'|`n'|`k'|`names'|`nc'|`s'|`nd'" _n
    forvalues j = 1/`k' {
        quietly summarize zc`j', meanonly
        local lo = cond(missing(r(min)), "null", trim(string(r(min), "%20.17g")))
        local hi = cond(missing(r(max)), "null", trim(string(r(max), "%20.17g")))
        quietly summarize zc`j' if `dcond', meanonly
        local dlo = cond(missing(r(min)), "null", trim(string(r(min), "%20.17g")))
        local dhi = cond(missing(r(max)), "null", trim(string(r(max), "%20.17g")))
        file write zbtrec "M|`id'|`j0'|`j'|`lo'|`hi'|`dlo'|`dhi'" _n
    }
    if `n' == 0 exit
    if `n' <= 41 local K = `n'
    else         local K = 11
    forvalues r = 1/`K' {
        if `n' <= 41 local i = `r'
        else         local i = round(1 + (`r' - 1) * (`n' - 1) / 10)
        local row ""
        forvalues j = 1/`k' {
            local z = zc`j'[`i']
            if missing(`z') local v "null"
            else            local v = trim(string(`z', "%20.17g"))
            if `j' == 1 local row "`v'"
            else        local row "`row';`v'"
        }
        file write zbtrec "W|`id'|`j0'|`i'|`row'" _n
    }
end

// ---------------------------------------------------------------------------
// zbt id "cmd" "byopts": one probe.
// ---------------------------------------------------------------------------
capture program drop zbt
program define zbt
    version 19
    args id cmd byopts
    use "${ZBT_WORK}/zbt.dta", clear
    capture serset drop _all
    capture graph drop _all
    quietly log using "${ZBT_WORK}/`id'.log", text replace name(zbtlog)
    capture noisily twoway (`cmd'), by(foreign`byopts') nodraw
    local rc = _rc
    quietly log close zbtlog
    file write zbtrec "R|`id'|`rc'|foreign`byopts'|`cmd'" _n
    if `rc' exit
    local np = `.Graph.graphs.arrnels'
    * Serset ids can have gaps (a plot may free one it used while
    * building), so every id up to 199 is tried, in order.
    local ids ""
    forvalues s = 0/199 {
        capture quietly serset set `s'
        if !_rc local ids "`ids' `s'"
    }
    local ns : word count `ids'
    file write zbtrec "N|`id'|`np'|`ns'|`ids'" _n
    * The serset each panel's plot draws (measured: mspline frees an id
    * while it builds, so position alone does not say which is which).
    forvalues k = 1/`np' {
        local sid `.Graph.graphs[`k'].plotregion1.plot1.serset.id'
        local yv `.Graph.graphs[`k'].plotregion1.plot1.serset.yvar'
        local xv `.Graph.graphs[`k'].plotregion1.plot1.serset.xvar'
        file write zbtrec "P|`id'|`k'|`sid'|`yv'|`xv'" _n
    }
    local j 0
    foreach s of local ids {
        zbt_serset `s' `id' `j'
        local ++j
    }
    * A contour's cuts are set when it is drawn (.lastcuts is empty under
    * nodraw), so contour and contourline are drawn once more for them.
    if inlist(word(`"`cmd'"', 1), "contour", "contourline") {
        use "${ZBT_WORK}/zbt.dta", clear
        capture graph drop _all
        quietly twoway (`cmd'), by(foreign`byopts')
        forvalues k = 1/`np' {
            file write zbtrec "C|`id'|`k'|`.Graph.graphs[`k'].plotregion1.plot1.lastcuts'" _n
        }
    }
end

capture program drop zbt2
program define zbt2
    version 19
    args t cmd
    zbt bt_`t'_by `"`cmd'"' ""
    zbt bt_`t'_total `"`cmd'"' ", total"
end

file open zbtrec using "${ZBT_REC}", write text replace
* yx types (plot_for's default shape), sorted for line, connected, area.
foreach t in bar dot dropline fpfit fpfitci lfit lfitci lowess lpoly ///
        lpolyci mband mspline qfit qfitci scatter spike {
    zbt2 `t' "`t' mpg weight"
}
foreach t in area connected line {
    zbt2 `t' "`t' mpg weight, sort"
}
zbt2 histogram "histogram mpg"
zbt2 kdensity "kdensity mpg"
* range types: y1 y2 x; rline and rconnected sorted.
foreach t in rarea rbar rspike rcap rcapsym rscatter {
    zbt2 `t' "`t' mpg price weight"
}
foreach t in rline rconnected {
    zbt2 `t' "`t' mpg price weight, sort"
}
foreach t in rpcap rpspike {
    zbt2 `t' "`t' mpg price foreign weight"
}
foreach t in pcspike pcarrow pcbarrow pcscatter pccapsym {
    zbt2 `t' "`t' mpg weight price foreign"
}
zbt2 scatteri "scatteri 20 3000 30 4000"
zbt2 pci "pci 20 3000 30 4000"
zbt2 pcarrowi "pcarrowi 20 3000 30 4000 25 2000 22 3500"
zbt2 function "function y = x^2"
foreach t in contour contourline {
    zbt2 `t' "`t' price mpg weight"
}
zbt2 tsline "tsline mpg"
zbt2 tsrline "tsrline mpg price"
file close zbtrec

python:
import json, os, re
from sfi import Macro

WORK = Macro.getGlobal("ZBT_WORK")
_HEAD = re.compile(r"^\s*(name|log|log type|opened on|closed on):")


def first_line(pid):
    try:
        with open(os.path.join(WORK, pid + ".log"), encoding="utf-8",
                  errors="replace") as fh:
            lines = [l.rstrip() for l in fh]
    except OSError:
        return ""
    keep = [l.strip() for l in lines if l.strip() and not _HEAD.match(l)
            and not set(l.strip()) <= set("-")
            and not re.match(r"^r\(\d+\);$", l.strip())]
    return keep[0] if keep else ""


def num(s):
    return None if s == "null" else float(s)


probes, order = {}, []
with open(Macro.getGlobal("ZBT_REC"), encoding="utf-8", errors="replace") as fh:
    for line in fh:
        f = line.rstrip("\n").split("|")
        if f[0] == "R":
            pid, rc = f[1], int(f[2])
            probes[pid] = {"cmd": "|".join(f[4:]), "by": f[3], "rc": rc,
                           "first_line": first_line(pid) if rc else ""}
            order.append(pid)
        elif f[0] == "N":
            p = probes[f[1]]
            p["n_panels"] = int(f[2])
            p["sersets"] = [None] * int(f[3])
        elif f[0] == "P":
            probes[f[1]].setdefault("panels", []).append({
                "serset_id": int(f[3]) if f[3] not in ("", ".") else None,
                "yvar": int(f[4]) if f[4] not in ("", ".") else None,
                "xvar": int(f[5]) if f[5] not in ("", ".") else None})
        elif f[0] == "C":
            q = probes[f[1]]["panels"][int(f[2]) - 1]
            q["cuts"] = [float(v) for v in f[3].split()]
        elif f[0] == "S":
            n = int(f[3])
            probes[f[1]]["sersets"][int(f[2])] = {
                "vars": f[5].split(), "n": n, "n_complete": int(f[6]),
                "id": int(f[7]), "n_drawn": int(f[8]),
                "min": [], "max": [], "drawn_min": [], "drawn_max": [],
                "rows": [], "sample_index": []}
        elif f[0] == "M":
            s = probes[f[1]]["sersets"][int(f[2])]
            s["min"].append(num(f[4]))
            s["max"].append(num(f[5]))
            s["drawn_min"].append(num(f[6]))
            s["drawn_max"].append(num(f[7]))
        elif f[0] == "W":
            s = probes[f[1]]["sersets"][int(f[2])]
            s["sample_index"].append(int(f[3]))
            s["rows"].append([num(v) for v in f[4].split(";")])

for p in probes.values():
    ids = [s["id"] for s in p.get("sersets", [])]
    for q in p.get("panels", []):
        q["serset"] = (ids.index(q["serset_id"])
                       if q["serset_id"] in ids else None)
    for s in p.get("sersets", []):
        if s["n"] > 41:
            s["samples"] = s.pop("rows")
        else:
            s.pop("sample_index")

with open(os.path.join(WORK, "data.json"), encoding="utf-8") as fh:
    data = json.load(fh)

out = {
    "_meta": {"stata_version": Macro.getGlobal("ZBT_SVER"),
              "born_date": Macro.getGlobal("ZBT_BORN"),
              "source": "scripts/extract_by_types_truth.do",
              "dash_commit": Macro.getGlobal("ZBT_COMMIT"),
              "extracted": Macro.getGlobal("ZBT_DATE"),
              "probes": len(order),
              "method": "twoway (<cmd>), by(foreign[, total]) nodraw; every "
                        "serset in order (one per plot per panel, "
                        "panel-major, Total last; panels[k].serset is the index of "
                        "the one panel k's plot draws): vars ('_' for a "
                        "temporary column), n, n_complete (rows with no "
                        "missing value), n_drawn (rows whose first two "
                        "columns are not missing), per-column min and max "
                        "over every row and drawn_min/drawn_max over the "
                        "drawn rows, and every "
                        "row (n <= 41) or the 11 rows at sample_index "
                        "(1-based, round(1 + (k-1)*(n-1)/10))"},
    "data": data,
    "probes": probes,
}
with open(Macro.getGlobal("ZBT_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1, sort_keys=True)
    fh.write("\n")
print("WROTE %s probes=%d" % (Macro.getGlobal("ZBT_OUT"), len(order)))
end

display as text "extract_by_types_truth.do: done"
