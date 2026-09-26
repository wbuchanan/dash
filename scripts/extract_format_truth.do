*! extract_format_truth.do
*! WP-28 S04: Stata's own display-format truth for the shared writer
*! (E1, E3, G6 foundation).  Nothing here is guessed: every numeric and
*! date string is what THIS run's `display' actually printed, captured
*! between "<" and ">" sentinels so leading/trailing blanks -- part of
*! what a display format means -- survive macro assignment.
*!
*! Output: test/fixtures/format_truth.json
*!
*! Run with (the script sets its own directories, so it is handed to the
*! wrapper directly -- CLAUDE.md rule 10, sections/BRIEF.md "Stata
*! invocation"):
*!
*!   scripts/stata_slot.sh /tmp/dash-s04 \
*!     /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/extract_format_truth.do
*!
*! ---------------------------------------------------------------------------
*! Two traps, restated from scripts/extract_date_truth.do and
*! scripts/extract_svg_truth_smoke.do because this script has its own
*! python: block:
*!
*!   1. A python: block inside a .do file must never call back into Stata
*!      (SFIToolkit.stata()/stata()) -- it desynchronises the interpreter.
*!      This script's trailing python: block only reads a file and Stata
*!      locals already computed; it issues no Stata command.
*!
*!   2. Stata expands a backtick/apostrophe pair as a local-macro reference
*!      even INSIDE a python: block, so a literal backtick in that block's
*!      own text is spelled \x60.
*! ---------------------------------------------------------------------------

clear all
set more off
set linesize 250

* <repo> is the root of the tree under test (sections/index.md step 1): the
* main checkout, or the section's own worktree while it runs there.
global ZF_REPO "/Users/billy/Desktop/Programs/StataPrograms/d/dash"
global ZF_OUT  "${ZF_REPO}/test/fixtures/format_truth.json"

local scratch "`c(tmpdir)'dash_format_probe"
capture mkdir "`scratch'"
global ZF_WORK "`scratch'"
global ZF_REC  "`scratch'/format_records.txt"
display as text "probe scratch dir: ${ZF_WORK}"

global ZF_SVER = c(stata_version)
global ZF_BORN = c(born_date)
global ZF_DATE = c(current_date)

* ---------------------------------------------------------------------------
* Provenance stamp (D12): the dash commit this fixture was measured
* against.  `shell' redirects git's stdout to a tempfile; the do-file reads
* it back with `file open'/`file read', never with a Stata call from
* Python.
* ---------------------------------------------------------------------------
tempfile zfgitrev
quietly shell git -C "${ZF_REPO}" rev-parse HEAD > "`zfgitrev'"
tempname zfgfh
file open `zfgfh' using "`zfgitrev'", read text
file read `zfgfh' zfgitline
file close `zfgfh'
local dash_commit = trim(`"`zfgitline'"')
capture assert ustrregexm(`"`dash_commit'"', "^[0-9a-f]{40}$")
if _rc {
    display as error "extract_format_truth.do: git rev-parse HEAD did not print a 40-character commit: `dash_commit'"
    exit 498
}

tempname rec
file open `rec' using "${ZF_REC}", write text replace
file write `rec' "META|stata_version|${ZF_SVER}" _n
file write `rec' "META|born_date|${ZF_BORN}" _n
file write `rec' "META|extracted|${ZF_DATE}" _n

* ===========================================================================
* A. Numeric display formats: f, g, e families, comma decimal, the 0 and -
*    flags, and the narrow widths 1-7 (F-24), each value as a double and as
*    a float.
* ===========================================================================
local nfmts `""%9.0g" "%10.0g" "%8.0g" "%20.15g" "%10.0gc" "%12.0gc" "%-12.0gc" "%9.0f" "%9.0fc" "%9.2f" "%9.2fc" "%-9.2f" "%12.2fc" "%9.3e" "%9.4f" "%9,2f" "%9,2fc" "%8.0gc" "%09.2f" "%-9.0g" "%9.2g" "%20.0g" "%12,2gc" "%10.3e" "%9.0e" "%9.4g" "%16.0g" "%12.0g" "%1.0f" "%2.0f" "%3.0g" "%4.0g" "%5.0g" "%6.0g" "%7.0g""'

local nvals "6165.2567 3.14159 1e7 -0.5 0.1 1234567.5 52313712223 0.000123456 1e21 . .a 0 123456789 -12345678 12345678 1e-7 1.2e-6 5e-7 1e100 1e-100 1000.03 31415.9265 0.0000029394 20.5 -1234567.891"

foreach f of local nfmts {
    foreach v of local nvals {
        capture local d : display "<" `f' (`v') ">"
        local rc = _rc
        if `rc' != 0 local d "<>"
        file write `rec' `"NVAL|`f'|`v'|double|`rc'|`d'|display `f' (`v')"' _n

        capture local fd : display "<" `f' (float(`v')) ">"
        local rc2 = _rc
        if `rc2' != 0 local fd "<>"
        file write `rec' `"NVAL|`f'|`v'|float|`rc2'|`fd'|display `f' (float(`v'))"' _n
    }
}
display as text "probed numeric display formats"

* ===========================================================================
* B. Date display formats: the eight kinds, one left-aligned variant, and
*    thirteen custom pictures exercising every code family, every value.
* ===========================================================================
local dfmts `""%td" "%tc" "%tC" "%tw" "%tm" "%tq" "%th" "%ty" "%-td" "%tdCCYY-NN-DD" "%tdDD/NN/CCYY" "%tdMonth_DD,_CCYY" "%tcHH:MM:SS.sss" "%tdJJJ" "%tdDayname_Day_Da_day_da" "%tdDAYNAME" "%tdyy!/nn" "%tcHh:MM_am" "%tcHH:MM:SS.ss" "%twCCYY!www" "%tdq!Qh!H" "%tdCCYY!c!!x""'

local dvals "15000 480 160 2000 -120 0 1 -1 2936549 ."

foreach f of local dfmts {
    foreach v of local dvals {
        capture local d : display "<" `f' (`v') ">"
        local rc = _rc
        if `rc' != 0 local d "<>"
        file write `rec' `"DVAL|`f'|`v'|`rc'|`d'|display `f' (`v')"' _n
    }
}
display as text "probed date display formats"

* ===========================================================================
* C. What `confirm numeric format' says about a format the writer must
*    refuse (%x, %H, %L) or that is simply invalid.
* ===========================================================================
local cfmts `""%21x" "%16H" "%16L" "%8H" "%8L" "%8s" "%9,2f" "%09.0g" "%9.2ec" "%tg" "%tdXYZ" "%tbsimple" "%9.2" "%""'

foreach f of local cfmts {
    capture confirm numeric format `f'
    file write `rec' `"CONF|`f'|`=_rc'"' _n
}
display as text "probed confirm numeric format"

* ===========================================================================
* D. dash.ado's own kpi_display rule (:6364-6421), replicated verbatim for
*    twelve stat/var combinations against fourteen formats (thirteen named
*    plus "no format", the macro's own text).
* ===========================================================================
capture program drop _zf_kpi_display
program define _zf_kpi_display, rclass
    args stat kpivar ifexpr fmt
    local kpi_value ""
    local is_pctile = 0
    local pct_num = .
    if regexm("`stat'", "^p([0-9]+(\.[0-9]+)?)$") {
        local is_pctile = 1
        local pct_num = real(regexs(1))
    }
    if inlist("`stat'", "mean", "sum", "min", "max", "sd") {
        quietly summarize `kpivar' `ifexpr'
        if      "`stat'" == "mean"  local kpi_value = r(mean)
        else if "`stat'" == "sum"   local kpi_value = r(sum)
        else if "`stat'" == "min"   local kpi_value = r(min)
        else if "`stat'" == "max"   local kpi_value = r(max)
        else if "`stat'" == "sd"    local kpi_value = r(sd)
    }
    else if "`stat'" == "count" {
        tempvar _nm
        quietly generate byte `_nm' = !missing(`kpivar') `ifexpr'
        quietly count if `_nm' == 1
        local kpi_value = r(N)
    }
    else if "`stat'" == "median" {
        quietly _pctile `kpivar' `ifexpr', p(50)
        local kpi_value = r(r1)
    }
    else if `is_pctile' {
        quietly _pctile `kpivar' `ifexpr', p(`pct_num')
        local kpi_value = r(r1)
    }
    local kpi_display = "`kpi_value'"
    if `"`fmt'"' != "" {
        capture local kpi_display : display `fmt' `kpi_value'
        if _rc == 0 local kpi_display = strtrim("`kpi_display'")
    }
    return local kpi_display `"`kpi_display'"'
    return local kpi_value `"`kpi_value'"'
end

sysuse auto, clear
quietly generate when = mdy(1,1,2000) + _n
format when %td
quietly generate whenm = mofd(when)
format whenm %tm

local kpi_fmts `""%9.0g" "%10.0g" "%9.2f" "%9,2fc" "%12.0fc" "%8.0gc" "%9.2e" "%9.3gc" "%-9.2f" "%09.2f" "%td" "%tdCCYY-NN-DD" "%tm" "%tdMonth_DD,_CCYY" """'

foreach kd in "mean price" "min mpg" "max weight" "sum price" "count rep78" "median price" "p97.5 price" "min when" "max whenm" "mean when" "median whenm" {
    local stat : word 1 of `kd'
    local kvar : word 2 of `kd'
    foreach fmt of local kpi_fmts {
        _zf_kpi_display `stat' `kvar' "" `"`fmt'"'
        file write `rec' `"KPI|`stat'|`kvar'||`fmt'|`r(kpi_display)'|`r(kpi_value)'"' _n
    }
}
* The no-observations case: mean(price) if price > 1e9.
foreach fmt of local kpi_fmts {
    _zf_kpi_display mean price "if price > 1e9" `"`fmt'"'
    file write `rec' `"KPI|mean|price|if price > 1e9|`fmt'|`r(kpi_display)'|`r(kpi_value)'"' _n
}
display as text "probed kpi_display"

file close `rec'

* ===========================================================================
* Analysis + JSON emission.  This block reads a file and Stata globals/
* locals only; it issues no Stata command (trap 1 above).
* ===========================================================================
python:
import json
from sfi import Macro

REC = Macro.getGlobal("ZF_REC")
OUT = Macro.getGlobal("ZF_OUT")
DASH_COMMIT = Macro.getLocal("dash_commit")


def unwrap(s):
    """Strip the "<...>" sentinels that protect leading/trailing blanks;
    "<>" (written when `capture' caught a nonzero rc) becomes ""."""
    if s is None:
        return ""
    if len(s) >= 2 and s[0] == "<" and s[-1] == ">":
        return s[1:-1]
    return s


meta = {}
numeric_formats, date_formats, confirm, kpi = {}, {}, {}, []

with open(REC, encoding="utf-8", errors="replace") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if not line:
            continue
        f = line.split("|")
        t = f[0]
        if t == "META":
            meta[f[1]] = "|".join(f[2:])
        elif t == "NVAL":
            fmt, value, storage, rc, disp = f[1], f[2], f[3], int(f[4]), f[5]
            cmd = "|".join(f[6:])
            numeric_formats.setdefault(fmt, {"values": []})
            numeric_formats[fmt]["values"].append({
                "value": value, "storage": storage, "rc": rc,
                "display": unwrap(disp), "display_cmd": cmd,
            })
        elif t == "DVAL":
            fmt, value, rc, disp = f[1], f[2], int(f[3]), f[4]
            cmd = "|".join(f[5:])
            date_formats.setdefault(fmt, {"values": []})
            date_formats[fmt]["values"].append({
                "value": value, "rc": rc,
                "display": unwrap(disp), "display_cmd": cmd,
            })
        elif t == "CONF":
            confirm[f[1]] = int(f[2])
        elif t == "KPI":
            stat, kvar, ifexpr, fmt, disp, val = (
                f[1], f[2], f[3], f[4], f[5], "|".join(f[6:]))
            kpi.append({
                "stat": stat, "var": kvar, "if": ifexpr, "fmt": fmt,
                "display": disp, "value": val,
            })

for k in numeric_formats:
    numeric_formats[k]["value_count"] = len(numeric_formats[k]["values"])
for k in date_formats:
    date_formats[k]["value_count"] = len(date_formats[k]["values"])

doc = {
    "_meta": {
        "stata_version": meta.get("stata_version", ""),
        "born_date": meta.get("born_date", ""),
        "dash_commit": DASH_COMMIT,
        "extracted": meta.get("extracted", ""),
        "script": "scripts/extract_format_truth.do",
    },
    "numeric_formats": numeric_formats,
    "date_formats": date_formats,
    "confirm": confirm,
    "kpi": kpi,
}

with open(OUT, "w") as fh:
    json.dump(doc, fh, indent=2, sort_keys=True)
    fh.write("\n")

print("WROTE " + OUT)
print("numeric_rows=%d date_rows=%d confirm=%d kpi=%d" % (
    sum(v["value_count"] for v in numeric_formats.values()),
    sum(v["value_count"] for v in date_formats.values()),
    len(confirm), len(kpi)))
end

display as text "extract_format_truth.do: done"
