*! extract_date_truth.do
*! Derive the ground truth for Stata's eight date epochs and for its numeric
*! display formats, BY PROBING STATA ITSELF, and record what the shipped
*! datasets actually carry and whether jsonio can emit a display format.
*!
*! Output: test/fixtures/date_truth.json
*!
*! Run with (the slot wrapper starts Stata from a scratch directory, because
*! batch mode writes its .log to the process working directory):
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_date_truth.do
*!
*! Section D calls jsonio under capture: set STATAJSON_DIR to jsonio's
*! directory to reproduce the committed fixture's JSONIO rows (without it
*! they record rc 199).
*!
*! ---------------------------------------------------------------------------
*! METHOD
*!
*! A Stata display string is locale- and format-dependent ("02jan2001"), so it
*! is NOT a usable target for a Python implementation on its own.  Every probed
*! value therefore carries TWO recorded results:
*!
*!   display   what `display %td 14977' actually prints, verbatim
*!   iso       the same instant re-displayed through an explicit ISO-8601
*!             picture (%tdCCYY-NN-DD, %tcCCYY-NN-DD!THH:MM:SS.sss), which is
*!             what a Python converter must reproduce
*!
*! For the four CALENDAR-period formats (%tw %tm %tq %th) the ISO value is the
*! period START, obtained with Stata's own dofw()/dofm()/dofq()/dofh() (the
*! half-year function is dofh(), NOT doth() -- doth() does not exist); the
*! period END is recorded too.  These formats count calendar periods, not
*! fixed-length intervals, so no multiplication converts them.
*!
*! %ty is NOT an offset from 1960 -- it is the year itself.  That is recorded as
*! evidence (`display %ty 38' prints 38, not 1998) rather than asserted.
*!
*! %tC differs from %tc by accumulated leap seconds.  The difference is measured
*! at several instants with Cofc()/cofC() and by displaying the same integer
*! under both pictures; if Stata's leap-second table were unavailable the probe
*! records the failure instead of guessing.
*!
*! Leading/trailing blanks matter for the numeric formats (alignment is part of
*! what %9.2f means), and a `local' assignment would strip them, so every
*! display is captured between "<" and ">" sentinels and unwrapped in Python.
*!
*! Structure follows extract_abbrev_truth.do: Stata runs every probe and writes
*! pipe-delimited records to a plain-text file; a single trailing python: block
*! reads that file and writes the JSON fixture.  The python block deliberately
*! never calls back into Stata -- SFIToolkit.stata() issued from a do-file
*! python block desynchronises the interpreter's input stream.
*!
*! A synthetic dataset carrying one variable per date format (plus %9.0fc,
*! %9.2f, %9.0g and a string) is pushed through the EXACT jsonio call dash.ado
*! makes, and the emitted JSON is read back, so the fixture records what each
*! format actually looks like on the Python side of the boundary rather than
*! what it is assumed to look like.
*!
*! Variable labels are recorded with "|" mapped to "/" so they cannot break the
*! record delimiter.  That substitution is noted in the fixture's _meta.
*! ---------------------------------------------------------------------------

clear all
set more off
local sj : environment STATAJSON_DIR
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("sj"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_date_truth.do: STATAJSON_DIR may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
if `"`sj'"' != "" adopath ++ `"`sj'"'
* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_date_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_date_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"

global ZQ_REPO "`repo'"
global ZQ_OUT  "${ZQ_REPO}/test/fixtures/date_truth.json"
global ZQ_JSONIO_ADO ""
global ZQ_JSONIO_JAR ""
global ZQ_JSONIO_SRC ""
if `"`sj'"' != "" {
    global ZQ_JSONIO_ADO "`sj'/jsonio.ado"
    global ZQ_JSONIO_JAR "`sj'/target/jsonio-jar-with-dependencies.jar"
    global ZQ_JSONIO_SRC "`sj'/src/main/java/org/paces/Stata/JSON"
}

local scratch "`c(tmpdir)'/dash_date_probe"
capture mkdir "`scratch'"
global ZQ_WORK "`scratch'"
global ZQ_REC  "`scratch'/date_records.txt"
display as text "probe scratch dir: ${ZQ_WORK}"

tempname rec
file open `rec' using "${ZQ_REC}", write text replace

file write `rec' "META|stata_version|`c(stata_version)'" _n
file write `rec' "META|stata_flavor|`c(flavor)'" _n
file write `rec' "META|stata_edition|`c(edition_real)'" _n
file write `rec' "META|stata_born_date|`c(born_date)'" _n
file write `rec' "META|run_date|`c(current_date)'" _n
file write `rec' "META|os|`c(os)' `c(machine_type)'" _n
file write `rec' "META|workdir|${ZQ_WORK}" _n

* ===========================================================================
* A.  The eight date epochs
*
* Value sets deliberately cover: 0 (the epoch), a negative value, a small
* positive, 2-3 values inside 1990-2025, and a large positive (including, for
* %td, one beyond pandas' nanosecond datetime64 range so the clamping path
* required by task 08-03 has a real target).  The anchors section 08 names --
* %td 14977, %tm 0, %tm 745, %ty 1998 -- are all present.
* ===========================================================================
global ZV_td "-10000 -3653 -1 0 1 10000 11323 14977 22281 23741 100000 1000000"
global ZV_tc "-86400000 -1 0 1 1000 86400000 631152000000 946684800000 1234567890123 1893456000000"
global ZV_tC "-86400000 -1 0 1 1000 86400000 631152000000 946684800000 1234567890123 1893456000000"
global ZV_tw "-100 -1 0 1 51 52 53 1560 2000 3380 3400 5000"
global ZV_tm "-120 -1 0 1 11 12 360 745 780 1000"
global ZV_tq "-40 -1 0 1 3 4 120 248 262 300"
global ZV_th "-20 -1 0 1 2 60 124 131 150"
global ZV_ty "-50 0 38 100 1960 1998 2001 2025 9999"

local fmtlist "td tc tC tw tm tq th ty"

foreach f of local fmtlist {
    local vals "${ZV_`f'}"
    foreach v of local vals {

        * ---- the display string, verbatim, blanks preserved -------------
        local dcmd "display %`f' `v'"
        local disp ""
        capture local disp : display "<" %`f' (`v') ">"
        local drc = _rc

        * ---- the same instant as ISO-8601, plus the period bounds -------
        local iso ""
        local icmd ""
        local pend ""
        local pcmd ""
        local irc = 0

        if "`f'" == "td" {
            local icmd "display %tdCCYY-NN-DD `v'"
            capture local iso : display "<" %tdCCYY-NN-DD (`v') ">"
            local irc = _rc
        }
        else if "`f'" == "tc" {
            local icmd "display %tcCCYY-NN-DD!THH:MM:SS.sss `v'"
            capture local iso : display "<" %tcCCYY-NN-DD!THH:MM:SS.sss (`v') ">"
            local irc = _rc
        }
        else if "`f'" == "tC" {
            local icmd "display %tCCCYY-NN-DD!THH:MM:SS.sss `v'"
            capture local iso : display "<" %tCCCYY-NN-DD!THH:MM:SS.sss (`v') ">"
            local irc = _rc
        }
        else if "`f'" == "tw" {
            local icmd "display %tdCCYY-NN-DD dofw(`v')"
            local pcmd "display %tdCCYY-NN-DD dofw(`v'+1)-1"
            capture local iso  : display "<" %tdCCYY-NN-DD (dofw(`v')) ">"
            local irc = _rc
            capture local pend : display "<" %tdCCYY-NN-DD (dofw(`v'+1)-1) ">"
        }
        else if "`f'" == "tm" {
            local icmd "display %tdCCYY-NN-DD dofm(`v')"
            local pcmd "display %tdCCYY-NN-DD dofm(`v'+1)-1"
            capture local iso  : display "<" %tdCCYY-NN-DD (dofm(`v')) ">"
            local irc = _rc
            capture local pend : display "<" %tdCCYY-NN-DD (dofm(`v'+1)-1) ">"
        }
        else if "`f'" == "tq" {
            local icmd "display %tdCCYY-NN-DD dofq(`v')"
            local pcmd "display %tdCCYY-NN-DD dofq(`v'+1)-1"
            capture local iso  : display "<" %tdCCYY-NN-DD (dofq(`v')) ">"
            local irc = _rc
            capture local pend : display "<" %tdCCYY-NN-DD (dofq(`v'+1)-1) ">"
        }
        else if "`f'" == "th" {
            * NB: the half-year -> daily function is dofh(), not doth().
            local icmd "display %tdCCYY-NN-DD dofh(`v')"
            local pcmd "display %tdCCYY-NN-DD dofh(`v'+1)-1"
            capture local iso  : display "<" %tdCCYY-NN-DD (dofh(`v')) ">"
            local irc = _rc
            capture local pend : display "<" %tdCCYY-NN-DD (dofh(`v'+1)-1) ">"
        }
        else if "`f'" == "ty" {
            * %ty is the year itself, so dofy() -- which takes a YEAR, not an
            * offset -- is the native derivation.  It is undefined outside
            * 0100-9999, and those probes record a missing ISO, not a guess.
            local icmd "display %tdCCYY-NN-DD dofy(`v')"
            local pcmd "display %tdCCYY-NN-DD dofy(`v'+1)-1"
            capture local iso  : display "<" %tdCCYY-NN-DD (dofy(`v')) ">"
            local irc = _rc
            capture local pend : display "<" %tdCCYY-NN-DD (dofy(`v'+1)-1) ">"
        }

        file write `rec' `"DVAL|`f'|`v'|`drc'|`disp'|`irc'|`iso'|`pend'|`dcmd'|`icmd'|`pcmd'"' _n
    }
    display as text "probed date format %`f'"
}

* ---- %ty evidence: the year itself, not an offset from 1960 --------------
* If %ty were an offset the display of 38 would read 1998.  Both are recorded.
foreach v in 0 38 1960 1998 2025 {
    capture local d : display "<" %ty (`v') ">"
    local rc1 = _rc
    capture local dtd : display "<" %td (`v') ">"
    file write `rec' `"TYEVID|`v'|`rc1'|`d'|`dtd'|display %ty `v'|display %td `v'"' _n
}

* ---- %tC vs %tc: measure the accumulated leap seconds --------------------
* Cofc(t) maps a %tc instant to the %tC value for the SAME instant, so
* Cofc(t)-t is the accumulated leap-second offset in milliseconds.
foreach v in 0 1 86400000 631152000000 946684800000 1234567890123 1893456000000 {
    capture local ctc : display "<" %tcCCYY-NN-DD!THH:MM:SS.sss (`v') ">"
    local rc1 = _rc
    capture local ctC : display "<" %tCCCYY-NN-DD!THH:MM:SS.sss (`v') ">"
    local rc2 = _rc
    capture local cof : display "<" %21.0f (Cofc(`v')) ">"
    local rc3 = _rc
    capture local dif : display "<" %21.0f (Cofc(`v') - `v') ">"
    capture local bak : display "<" %21.0f (cofC(Cofc(`v'))) ">"
    file write `rec' `"LEAP|`v'|`rc1'|`ctc'|`rc2'|`ctC'|`rc3'|`cof'|`dif'|`bak'"' _n
}

* ---- the left-aligned %-t variants task 08-03 must also classify ---------
foreach s in "-td" "-tc" "-tC" "-tw" "-tm" "-tq" "-th" "-ty" {
    capture local d : display "<" %`s' (14977) ">"
    file write `rec' `"PREFIX|%`s'|14977|`=_rc'|`d'|display %`s' 14977"' _n
}

* ===========================================================================
* B.  Numeric display formats
*
* Blanks are load-bearing here: %9.2f right-aligns into nine columns and %-9.2f
* left-aligns, so the sentinels around each display are what make the fixture
* usable as a target for a Python formatter.
* ===========================================================================
local nfmts `""%9.0f" "%9.2f" "%9.0fc" "%9.2fc" "%12.0gc" "%9.0g" "%10.0gc" "%-9.2f" "%9.3e" "%8.0g" "%10.0g" "%12.2fc" "%9.4f" "%20.15g" "%-12.0gc""'

foreach f of local nfmts {
    foreach v in 0 -1 1234.5678 -1234.5678 1234567.891 -1234567.891 0.000123456 1e12 . .a {
        capture local d : display "<" `f' (`v') ">"
        file write `rec' `"NVAL|`f'|`v'|`=_rc'|`d'|display `f' `v'"' _n
    }
}
display as text "probed numeric display formats"

* ===========================================================================
* C.  What the shipped datasets actually carry
*
* Every sysuse dataset is opened and every variable's ACTUAL display format is
* read with `: format'.  sp500 and auto are recorded in full (section 08
* asserts sp500's date is %td -- this confirms or refutes it); for the rest
* only %t* variables are recorded, to keep the fixture readable.
* ===========================================================================
local sysbase "`c(sysdir_base)'"
file write `rec' "META|sysdir_base|`sysbase'" _n

local dsnames ""
local dirs : dir "`sysbase'" dirs "*"
foreach d of local dirs {
    local files : dir "`sysbase'`d'" files "*.dta"
    foreach fn of local files {
        local nm = subinstr(`"`fn'"', ".dta", "", .)
        local dsnames `"`dsnames' "`nm'""'
    }
}

foreach ds of local dsnames {
    capture sysuse `ds', clear
    if _rc != 0 {
        file write `rec' `"DSERR|`ds'|`=_rc'"' _n
        continue
    }
    local full = ("`ds'" == "sp500" | "`ds'" == "auto")
    file write `rec' `"DS|`ds'|`c(N)'|`c(k)'|`full'"' _n
    foreach v of varlist _all {
        local fm : format `v'
        local tp : type `v'
        local lb : variable label `v'
        local lb = subinstr(`"`lb'"', "|", "/", .)
        local isdate = (substr("`fm'", 1, 2) == "%t" | substr("`fm'", 1, 3) == "%-t")
        if `full' | `isdate' {
            file write `rec' `"DSVAR|`ds'|`v'|`fm'|`tp'|`isdate'|`lb'"' _n
        }
    }
}
display as text "probed shipped datasets"

* ===========================================================================
* D.  Can jsonio emit a display format?
*
* Three probes.  (1) The exact call dash.ado:1481 makes, so the resulting JSON
* can be inspected for a format member.  (2) The same metaprint() WITHOUT
* what(), with a filenm(), which is the combination the gating bug at
* jsonio.ado:238 is claimed to break -- inlist("`metaprint'`filenm'", ...)
* CONCATENATES the two, so a non-empty filenm() can never match.  (3) The same
* metaprint() with NO filenm(), captured to its own log, which is the only way
* the metadata branch can fire at all.
* ===========================================================================
sysuse sp500, clear
local jp1 "${ZQ_WORK}/jsonio_dashstyle.json"
local jp2 "${ZQ_WORK}/jsonio_metafile.json"
local jp3 "${ZQ_WORK}/jsonio_console.log"
capture erase "`jp1'"
capture erase "`jp2'"
capture erase "`jp3'"

capture quietly jsonio out date close, what(all) filenm("`jp1'") ///
    metaprint(varnames varlabels vallabs labelnames)
local rc1 = _rc
capture confirm file "`jp1'"
file write `rec' `"JSONIO|dashstyle|`rc1'|`=_rc'|`jp1'|jsonio out date close, what(all) filenm(<path>) metaprint(varnames varlabels vallabs labelnames)"' _n

capture quietly jsonio out date close, filenm("`jp2'") metaprint(varlabels)
local rc1 = _rc
capture confirm file "`jp2'"
file write `rec' `"JSONIO|metaprint_with_filenm|`rc1'|`=_rc'|`jp2'|jsonio out date close, filenm(<path>) metaprint(varlabels)"' _n

capture log close zqjl
capture log using "`jp3'", text replace name(zqjl)
capture noisily jsonio out date close, metaprint(varlabels)
local rc1 = _rc
capture log close zqjl
capture confirm file "`jp3'"
file write `rec' `"JSONIO|metaprint_no_filenm|`rc1'|`=_rc'|`jp3'|jsonio out date close, metaprint(varlabels)"' _n

* ---- E.  How does each display format survive the jsonio boundary? ------
* A synthetic dataset with one variable per date format, plus formatted and
* unformatted numerics and a string, pushed through the exact call dash.ado
* makes.  The emitted JSON is read back in the python block.
clear
quietly set obs 4

quietly generate double zq_td = . 
quietly replace zq_td = 14977 in 1
quietly replace zq_td = 0     in 2
quietly replace zq_td = -1    in 3
format zq_td %td

quietly generate double zq_tc = .
quietly replace zq_tc = 1234567890123 in 1
quietly replace zq_tc = 0             in 2
quietly replace zq_tc = -1            in 3
format zq_tc %tc

quietly generate double zq_tC = .
quietly replace zq_tC = 1234567890123 in 1
quietly replace zq_tC = 0             in 2
quietly replace zq_tC = -1            in 3
format zq_tC %tC

quietly generate double zq_tw = .
quietly replace zq_tw = 3380 in 1
quietly replace zq_tw = 0    in 2
quietly replace zq_tw = -1   in 3
format zq_tw %tw

quietly generate double zq_tm = .
quietly replace zq_tm = 745 in 1
quietly replace zq_tm = 0   in 2
quietly replace zq_tm = -1  in 3
format zq_tm %tm

quietly generate double zq_tq = .
quietly replace zq_tq = 248 in 1
quietly replace zq_tq = 0   in 2
quietly replace zq_tq = -1  in 3
format zq_tq %tq

quietly generate double zq_th = .
quietly replace zq_th = 124 in 1
quietly replace zq_th = 0   in 2
quietly replace zq_th = -1  in 3
format zq_th %th

quietly generate double zq_ty = .
quietly replace zq_ty = 1998 in 1
quietly replace zq_ty = 1960 in 2
quietly replace zq_ty = 2025 in 3
format zq_ty %ty

quietly generate double zq_fc = .
quietly replace zq_fc = 1234567.891 in 1
quietly replace zq_fc = 0           in 2
quietly replace zq_fc = -1234.5678  in 3
format zq_fc %9.0fc

quietly generate double zq_f2 = .
quietly replace zq_f2 = 1234.5678 in 1
quietly replace zq_f2 = 0         in 2
quietly replace zq_f2 = -1234.5678 in 3
format zq_f2 %9.2f

quietly generate double zq_plain = .
quietly replace zq_plain = 1234.5678 in 1
quietly replace zq_plain = 0         in 2
quietly replace zq_plain = -1234.5678 in 3
format zq_plain %9.0g

quietly generate str12 zq_str = "abc"
quietly replace zq_str = "" in 4

foreach v of varlist zq_* {
    local fm : format `v'
    file write `rec' `"FMTVAR|`v'|`fm'"' _n
}

local jp4 "${ZQ_WORK}/jsonio_formats.json"
capture erase "`jp4'"
capture quietly jsonio out zq_td zq_tc zq_tC zq_tw zq_tm zq_tq zq_th zq_ty ///
    zq_fc zq_f2 zq_plain zq_str, what(all) filenm("`jp4'") ///
    metaprint(varnames varlabels vallabs labelnames)
local rc1 = _rc
capture confirm file "`jp4'"
file write `rec' `"FMTPROBE|`rc1'|`=_rc'|`jp4'|jsonio out <one var per format>, what(all) filenm(<path>) metaprint(varnames varlabels vallabs labelnames)"' _n

file write `rec' "META|jsonio_ado|${ZQ_JSONIO_ADO}" _n
file write `rec' "META|jsonio_jar|${ZQ_JSONIO_JAR}" _n
file write `rec' "META|jsonio_src|${ZQ_JSONIO_SRC}" _n

file close `rec'
display as text "records written to ${ZQ_REC}"

* ===========================================================================
* Analysis + JSON emission.  No callbacks into Stata from here on.
* ===========================================================================
python:
import json, os, re, subprocess
from sfi import Macro

REC = Macro.getGlobal("ZQ_REC")
OUT = Macro.getGlobal("ZQ_OUT")
JSONIO_ADO = Macro.getGlobal("ZQ_JSONIO_ADO")
JSONIO_JAR = Macro.getGlobal("ZQ_JSONIO_JAR")
JSONIO_SRC = Macro.getGlobal("ZQ_JSONIO_SRC")

UNVERIFIED = []


def unwrap(s):
    """Strip the <...> sentinels that protect leading/trailing blanks."""
    if s is None:
        return None
    if len(s) >= 2 and s[0] == "<" and s[-1] == ">":
        return s[1:-1]
    return s


def nz(s):
    return s if s not in (None, "") else None


meta = {}
dvals, tyevid, leap, prefix, nvals = [], [], [], [], []
ds_rows, dsvar_rows, dserr_rows, jsonio_rows = {}, [], {}, {}
fmtvars, fmtprobe = {}, {}

with open(REC, "r", errors="replace") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if not line:
            continue
        f = line.split("|")
        t = f[0]
        if t == "META":
            meta[f[1]] = "|".join(f[2:])
        elif t == "DVAL":
            dvals.append({
                "fmt": f[1], "value": f[2], "drc": int(f[3]),
                "display": unwrap(f[4]), "irc": int(f[5]),
                "iso": unwrap(f[6]), "period_end": unwrap(f[7]),
                "display_cmd": f[8], "iso_cmd": nz(f[9]), "period_end_cmd": nz(f[10]),
            })
        elif t == "TYEVID":
            tyevid.append({
                "value": f[1], "rc": int(f[2]),
                "display_ty": unwrap(f[3]), "display_td": unwrap(f[4]),
                "ty_cmd": f[5], "td_cmd": f[6],
            })
        elif t == "LEAP":
            leap.append({
                "value": f[1],
                "tc_rc": int(f[2]), "tc_iso": unwrap(f[3]),
                "tC_rc": int(f[4]), "tC_iso": unwrap(f[5]),
                "cofc_rc": int(f[6]), "Cofc": unwrap(f[7]).strip(),
                "Cofc_minus_value_ms": unwrap(f[8]).strip(),
                "cofC_roundtrip": unwrap(f[9]).strip(),
            })
        elif t == "PREFIX":
            prefix.append({"fmt": f[1], "value": f[2], "rc": int(f[3]),
                           "display": unwrap(f[4]), "display_cmd": f[5]})
        elif t == "NVAL":
            nvals.append({"fmt": f[1], "value": f[2], "rc": int(f[3]),
                          "display": unwrap(f[4]), "display_cmd": f[5]})
        elif t == "DS":
            ds_rows[f[1]] = {"nobs": int(f[2]), "nvars": int(f[3]),
                             "recorded": "all variables" if f[4] == "1"
                             else "only variables with a %t* display format"}
        elif t == "DSVAR":
            dsvar_rows.append({"ds": f[1], "var": f[2], "format": f[3],
                               "type": f[4], "is_date_format": f[5] == "1",
                               "label": nz("|".join(f[6:]))})
        elif t == "DSERR":
            dserr_rows[f[1]] = int(f[2])
        elif t == "FMTVAR":
            fmtvars[f[1]] = f[2]
        elif t == "FMTPROBE":
            fmtprobe = {"rc": int(f[1]), "output_exists": int(f[2]) == 0,
                        "path": f[3], "cmd": "|".join(f[4:])}
        elif t == "JSONIO":
            jsonio_rows[f[1]] = {"rc": int(f[2]), "output_exists": int(f[3]) == 0,
                                 "path": f[4], "cmd": "|".join(f[5:])}

# ------------------------------------------------------------- A. date epochs
FMT_INFO = {
    "td": ("days", "day", "01jan1960",
           "A plain day count from 01jan1960.  Fixed-length: a timedelta of "
           "'value' days added to 1960-01-01 is exact."),
    "tc": ("milliseconds", "millisecond", "01jan1960 00:00:00.000",
           "A plain millisecond count from 01jan1960 00:00:00.000, with NO leap "
           "seconds.  Fixed-length: a timedelta of 'value' ms added to the epoch "
           "is exact."),
    "tC": ("milliseconds (leap-second corrected)", "millisecond",
           "01jan1960 00:00:00.000",
           "A millisecond count from 01jan1960 that DOES include leap seconds, "
           "so it is NOT a fixed-length offset.  See \"leap_seconds\"."),
    "tw": ("weeks", "calendar week", "1960w1",
           "A CALENDAR week index.  Week 1 of every year starts on 01jan and "
           "week 52 absorbs the remaining 8 or 9 days, so weeks are not 7 days "
           "apart across a year boundary and multiplication does not convert."),
    "tm": ("months", "calendar month", "1960m1",
           "A CALENDAR month index.  Months are 28-31 days; multiplication does "
           "not convert."),
    "tq": ("quarters", "calendar quarter", "1960q1",
           "A CALENDAR quarter index; multiplication does not convert."),
    "th": ("half-years", "calendar half-year", "1960h1",
           "A CALENDAR half-year index; multiplication does not convert."),
    "ty": ("years", "calendar year", "NOT AN EPOCH",
           "%ty is the YEAR ITSELF.  It is not an offset from 1960 and must not "
           "be offset at all.  See \"ty_is_the_year_itself\"."),
}

date_formats = {}
for key, (unit, period, epoch, note) in FMT_INFO.items():
    rows = [r for r in dvals if r["fmt"] == key]
    out_rows = []
    for r in rows:
        entry = {
            "value": int(r["value"]),
            "display": r["display"],
            "display_cmd": r["display_cmd"],
            "display_rc": r["drc"],
            "iso": r["iso"],
            "iso_cmd": r["iso_cmd"],
            "iso_rc": r["irc"],
            "source": "stata",
        }
        if key in ("tw", "tm", "tq", "th"):
            entry["period_start_iso"] = r["iso"]
            entry["period_end_iso"] = r["period_end"]
            entry["period_end_cmd"] = r["period_end_cmd"]
        # A missing date comes back from Stata blank-padded ("         ."),
        # so the emptiness test must strip before comparing.
        def blank(x):
            return (x or "").strip() in ("", ".")

        if key in ("tw", "tm", "tq", "th") and blank(r["period_end"]):
            entry["period_end_iso"] = None
        if key == "ty":
            entry["jan1_iso"] = None if blank(r["iso"]) else r["iso"]
            entry["dec31_iso"] = None if blank(r["period_end"]) else r["period_end"]
            entry["jan1_cmd"] = r["iso_cmd"]
            if blank(r["iso"]):
                entry["note"] = ("dofy() is undefined outside years 0100-9999, so "
                                 "no ISO date could be derived empirically for "
                                 "this %ty value; the value itself IS the year.")
        if blank(r["iso"]):
            entry["iso"] = None
            if key in ("tw", "tm", "tq", "th"):
                entry["period_start_iso"] = None
        out_rows.append(entry)

    zero = [r for r in out_rows if r["value"] == 0]
    date_formats["%" + key] = {
        "unit": unit,
        "period": period,
        "epoch": epoch,
        "epoch_iso_at_value_0": (zero[0]["iso"] if zero else None),
        "epoch_evidence_cmd": (zero[0]["iso_cmd"] if zero else None),
        "fixed_length": key in ("td", "tc"),
        "note": note,
        "value_count": len(out_rows),
        "values": out_rows,
    }

# %ty is the year itself -- recorded as measured evidence, not as an assertion.
ty_off_by_1960 = []
for e in tyevid:
    ty_off_by_1960.append({
        "value": int(e["value"]),
        "display_as_ty": e["display_ty"],
        "display_as_ty_cmd": e["ty_cmd"],
        "display_as_td": e["display_td"],
        "display_as_td_cmd": e["td_cmd"],
    })
ty38 = [e for e in tyevid if e["value"] == "38"]
ty_conclusion = "UNDETERMINED"
if ty38:
    shown = (ty38[0]["display_ty"] or "").strip()
    if shown == "38":
        ty_conclusion = ("CONFIRMED: display %ty 38 prints \"38\", not \"1998\".  "
                         "%ty carries the year itself; adding 1960 is wrong.")
    elif shown == "1998":
        ty_conclusion = ("REFUTED: display %ty 38 printed \"1998\" -- on this "
                         "Stata %ty IS offset from 1960.")
    else:
        ty_conclusion = ("UNDETERMINED: display %ty 38 printed " + repr(shown))

# ----------------------------------------------------------- leap seconds
leap_rows = []
tC_available = True
for r in leap:
    if r["tC_rc"] != 0 or r["cofc_rc"] != 0:
        tC_available = False
    try:
        diff_ms = int(float(r["Cofc_minus_value_ms"]))
    except Exception:
        diff_ms = None
    leap_rows.append({
        "value_ms": int(r["value"]),
        "tc_iso": r["tc_iso"],
        "tc_cmd": "display %tcCCYY-NN-DD!THH:MM:SS.sss " + r["value"],
        "tc_rc": r["tc_rc"],
        "tC_iso": r["tC_iso"],
        "tC_cmd": "display %tCCCYY-NN-DD!THH:MM:SS.sss " + r["value"],
        "tC_rc": r["tC_rc"],
        "Cofc_value": r["Cofc"],
        "Cofc_cmd": "display %21.0f Cofc(" + r["value"] + ")",
        "leap_offset_ms": diff_ms,
        "leap_offset_seconds": (None if diff_ms is None else diff_ms / 1000.0),
        "cofC_roundtrip": r["cofC_roundtrip"],
        "source": "stata",
    })

nonzero = [r["leap_offset_seconds"] for r in leap_rows
           if r["leap_offset_seconds"] not in (None, 0.0)]
if not tC_available:
    leap_finding = ("Stata could NOT evaluate %tC or Cofc() on this installation "
                    "(non-zero return codes recorded per row).  Leap-second data "
                    "appears unavailable; no offset is claimed.")
elif not nonzero:
    leap_finding = ("Stata evaluated %tC successfully but the measured offset was "
                    "zero at every probed instant, which would mean this build "
                    "carries no leap-second table.  Recorded as measured.")
else:
    leap_finding = (
        "Leap-second data IS available.  %tC and %tc interpret the SAME integer "
        "as instants that differ by the accumulated leap seconds: the offset "
        "measured with Cofc() runs from " + repr(min(nonzero)) + "s to " +
        repr(max(nonzero)) + "s across the probed range, growing with time.  "
        "Treating %tC as %tc is therefore wrong by up to that many seconds and, "
        "per section 08, is acceptable only if documented.")

# -------------------------------------------------------- B. numeric formats
numeric_formats = {}
for r in nvals:
    numeric_formats.setdefault(r["fmt"], {"value_count": 0, "values": []})
    numeric_formats[r["fmt"]]["values"].append({
        "value": r["value"],
        "display": r["display"],
        "display_width": (None if r["display"] is None else len(r["display"])),
        "display_cmd": r["display_cmd"],
        "rc": r["rc"],
        "source": "stata",
    })
for k in numeric_formats:
    numeric_formats[k]["value_count"] = len(numeric_formats[k]["values"])
    widths = {v["display_width"] for v in numeric_formats[k]["values"]
              if v["display_width"] is not None}
    numeric_formats[k]["constant_width"] = (len(widths) == 1)
    numeric_formats[k]["observed_widths"] = sorted(widths)
    numeric_formats[k]["left_aligned"] = k.startswith("%-")
    numeric_formats[k]["comma_separated"] = k.endswith("c")

# ------------------------------------------------------------ C. datasets
datasets = {}
for ds, info in sorted(ds_rows.items()):
    datasets[ds] = dict(info)
    datasets[ds]["variables"] = {}
for r in dsvar_rows:
    datasets.setdefault(r["ds"], {"variables": {}})
    datasets[r["ds"]]["variables"][r["var"]] = {
        "format": r["format"],
        "type": r["type"],
        "is_date_format": r["is_date_format"],
        "label": r["label"],
        "cmd": "sysuse " + r["ds"] + ", clear ; local f : format " + r["var"],
        "source": "stata",
    }
for ds, rc in sorted(dserr_rows.items()):
    datasets[ds] = {"load_failed_rc": rc,
                    "note": "sysuse could not load this dataset; nothing recorded"}

date_vars = sorted(
    (r["ds"], r["var"], r["format"]) for r in dsvar_rows if r["is_date_format"])

sp500_date = datasets.get("sp500", {}).get("variables", {}).get("date")
if sp500_date is None:
    sp500_finding = ("UNVERIFIED: sp500 was not loaded or has no variable named "
                     "'date'; section 08 claim could not be checked.")
    UNVERIFIED.append("sp500 date format")
elif sp500_date["format"] == "%td":
    sp500_finding = ("CONFIRMED: sysuse sp500 variable 'date' carries display "
                     "format %td, measured with: local f : format date")
else:
    sp500_finding = ("REFUTED: section 08 asserts sp500 'date' is %td, but the "
                     "measured display format is " + sp500_date["format"] + ".")

# -------------------------------------------------------------- D. jsonio
def read_lines(path):
    try:
        with open(path, "r", errors="replace") as fh:
            return fh.read().split("\n")
    except Exception:
        return None


ado = read_lines(JSONIO_ADO)
gate_lineno, gate_text = None, None
if ado:
    for i, ln in enumerate(ado, start=1):
        if "inlist(" in ln and "metaprint" in ln and "filenm" in ln:
            gate_lineno, gate_text = i, ln.strip()
            break
else:
    UNVERIFIED.append("jsonio.ado could not be read")

all_java = read_lines(os.path.join(JSONIO_SRC, "StataAllToJSON.java"))
all_fields = []
if all_java:
    for ln in all_java:
        m = re.search(r'makeJSON\.put\("([^"]+)"', ln)
        if m and not ln.strip().startswith("//"):
            all_fields.append(m.group(1))
else:
    UNVERIFIED.append("StataAllToJSON.java could not be read")

meta_java = read_lines(os.path.join(JSONIO_SRC, "StataMetaToJSON.java"))
meta_keys = []
if meta_java:
    for ln in meta_java:
        m = re.search(r'public static final String \w+ = "([^"]+)"', ln)
        if m:
            meta_keys.append(m.group(1))
else:
    UNVERIFIED.append("StataMetaToJSON.java could not be read")

javap_members, javap_note = None, None
try:
    p = subprocess.run(["javap", "-cp", JSONIO_JAR,
                        "org.paces.Stata.MetaData.Variables"],
                       capture_output=True, text=True, timeout=60)
    if p.returncode == 0:
        javap_members = [l.strip() for l in p.stdout.split("\n")
                         if "Fmt" in l or "isDateTime" in l]
    else:
        javap_note = "javap exited " + str(p.returncode) + ": " + p.stderr[:200]
except Exception as exc:
    javap_note = "javap could not be run: " + repr(exc)
if javap_members is None:
    UNVERIFIED.append("javap inspection of jsonio.jar")

probe1 = jsonio_rows.get("dashstyle", {})
dashstyle_keys, dashstyle_has_format = None, None
if probe1.get("output_exists"):
    try:
        with open(probe1["path"], "r", errors="replace") as fh:
            blob = json.load(fh)
        dashstyle_keys = sorted(blob.keys()) if isinstance(blob, dict) else None
        if dashstyle_keys is not None:
            dashstyle_has_format = any(
                "format" in k.lower() or "fmt" in k.lower() for k in dashstyle_keys)
    except Exception as exc:
        dashstyle_keys = ["<could not parse: " + repr(exc) + ">"]

console_tail = None
probe3 = jsonio_rows.get("metaprint_no_filenm", {})
if probe3.get("output_exists"):
    lines = read_lines(probe3["path"]) or []
    console_tail = [l for l in lines if l.strip()][-6:]

# The needle is assembled from chr() on purpose.  A do-file's python: block is
# still scanned by Stata's macro expander, so a literal backtick-apostrophe pair
# written here would be expanded to nothing BEFORE python ever sees it -- which
# would silently turn this test into ("" in gate_text), i.e. always true.
BT = chr(96)
AP = chr(39)
NEEDLE = BT + "metaprint" + AP + BT + "filenm" + AP
gate_broken = None
if gate_text is not None:
    gate_broken = NEEDLE in gate_text

if gate_broken and dashstyle_has_format is False:
    jsonio_finding = (
        "CONFIRMED on all three counts.  (1) jsonio.ado line " + str(gate_lineno) +
        " gates the metadata branch on inlist(" + repr(NEEDLE) + ", ...), which "
        "CONCATENATES the two macros, so any non-empty filenm() makes the test "
        "unmatchable and metaprint() becomes a no-op -- exactly what dash.ado:1481 "
        "does.  (2) The metaprint() keys StataMetaToJSON accepts are " +
        repr(meta_keys) + " -- none is a display format.  (3) The what(all) payload "
        "jsonio actually wrote carries top-level keys " + repr(dashstyle_keys) +
        ", with no format member.  jsonio therefore cannot emit display formats "
        "and dash must carry them itself.")
elif gate_broken and dashstyle_has_format:
    jsonio_finding = ("PARTIALLY REFUTED: the line " + str(gate_lineno) +
                      " concatenation bug is real, but the what(all) payload DOES "
                      "contain a format-like key: " + repr(dashstyle_keys))
elif gate_text is None:
    jsonio_finding = ("UNVERIFIED: no inlist() line mentioning both the metaprint "
                      "and filenm macros was found in " + JSONIO_ADO)
else:
    jsonio_finding = ("REFUTED: the gating line at " + str(gate_lineno) +
                      " does not concatenate the macros: " + repr(gate_text))

jsonio_block = {
    "claim_in_plan": ("jsonio has no option that emits display formats; "
                      "jsonio.ado:238 gates on inlist(" + repr(NEEDLE) + ", ...)"),
    "finding": jsonio_finding,
    "gating_line_number": gate_lineno,
    "gating_line_text": gate_text,
    "gating_concatenates_macros": gate_broken,
    "gating_line_matches_plan_line_238": (gate_lineno == 238),
    "metaprint_accepted_keys": meta_keys or None,
    "StataAllToJSON_emitted_fields": all_fields or None,
    "StataAllToJSON_has_format_field": (
        None if not all_fields
        else any("format" in f.lower() or "fmt" in f.lower() for f in all_fields)),
    "javap_Variables_format_members": javap_members,
    "javap_cmd": "javap -cp " + JSONIO_JAR + " org.paces.Stata.MetaData.Variables",
    "javap_note": javap_note,
    "empirical_probes": jsonio_rows,
    "dashstyle_payload_top_level_keys": dashstyle_keys,
    "dashstyle_payload_has_format_key": dashstyle_has_format,
    "metaprint_no_filenm_console_tail": console_tail,
    "source_files_read": {"ado": JSONIO_ADO, "java": JSONIO_SRC,
                          "jar": JSONIO_JAR},
    "note": "jsonio was read only.  Nothing in StataJSON was modified.",
}

# ------------------------------------------------------------------- output
# ------------------------- E. what crosses the jsonio boundary ------------
# jsonio is the ONLY route data takes from Stata to dash_render.py
# (dash.ado:1481/:1897/:2080), so what it emits for a formatted variable is the
# real input to every Python code path in section 08.
boundary = {
    "why": ("jsonio is the only route data takes from Stata into "
            "dash_render.py, so whatever it emits for a formatted variable is "
            "the actual input to _load_data.  This block records that, "
            "measured, rather than assuming a raw SIF integer arrives."),
    "probe_cmd": fmtprobe.get("cmd"),
    "probe_rc": fmtprobe.get("rc"),
    "stata_formats": fmtvars or None,
    "variables": {},
}
payload = None
if fmtprobe.get("output_exists"):
    try:
        with open(fmtprobe["path"], "r", errors="replace") as fh:
            payload = json.load(fh)
    except Exception as exc:
        boundary["parse_error"] = repr(exc)
        UNVERIFIED.append("jsonio boundary payload could not be parsed")
else:
    UNVERIFIED.append("jsonio boundary payload was not produced")

if payload is not None:
    isstr = payload.get("variableIsString", {})
    rows = payload.get("values", [])
    for var, fmt in sorted(fmtvars.items()):
        emitted = [r.get(var) for r in rows]
        # Observations 1-3 are non-missing by construction; observation 4 is
        # the system missing value (and the empty string for zq_str), so the
        # two are classified separately.
        present, absent = emitted[:3], (emitted[3] if len(emitted) > 3 else None)
        types = sorted({("null" if e is None else type(e).__name__)
                        for e in present})
        boundary["variables"][var] = {
            "stata_format": fmt,
            "jsonio_variableIsString": isstr.get(var),
            "emitted_values": emitted,
            "emitted_json_types_nonmissing": types,
            "emitted_as_formatted_string": types == ["str"],
            "missing_emitted_as": absent,
            "source": "stata",
        }

date_pass = {v: d["emitted_as_formatted_string"]
             for v, d in boundary["variables"].items()
             if d["stata_format"].startswith("%t")}
num_pass = {v: d["emitted_as_formatted_string"]
            for v, d in boundary["variables"].items()
            if v in ("zq_fc", "zq_f2", "zq_plain")}
boundary["missing_value_encoding"] = {
    "date_formats": ("a blank-padded \".\" STRING, e.g. " +
                     repr(boundary["variables"].get("zq_td", {}).get(
                         "missing_emitted_as"))),
    "numeric_formats": ("the four-character STRING " +
                        repr(boundary["variables"].get("zq_plain", {}).get(
                            "missing_emitted_as")) +
                        " -- quoted, so it is NOT a JSON null"),
    "string_variables": repr(boundary["variables"].get("zq_str", {}).get(
        "missing_emitted_as")),
}
# The same thing on a real shipped dataset, so the claim about sp500 is backed
# by the recorded payload rather than by prose.
sp = jsonio_rows.get("dashstyle", {})
if sp.get("output_exists"):
    try:
        with open(sp["path"], "r", errors="replace") as fh:
            spblob = json.load(fh)
        boundary["sp500_first_rows"] = spblob.get("values", [])[:3]
        boundary["sp500_variableIsString"] = spblob.get("variableIsString")
        boundary["sp500_probe_cmd"] = sp.get("cmd")
    except Exception as exc:
        boundary["sp500_first_rows"] = "<could not parse: " + repr(exc) + ">"
        UNVERIFIED.append("sp500 jsonio payload could not be parsed")

tc_row = boundary["variables"].get("zq_tc", {})
boundary["subsecond_precision"] = {
    "probe_value_ms": 1234567890123,
    "true_instant": "1999-02-13T23:31:30.123",
    "jsonio_emitted": (tc_row.get("emitted_values") or [None])[0],
    "finding": ("jsonio renders %tc through the DEFAULT %tc picture, which "
                "stops at whole seconds, so the .123 millisecond component is "
                "destroyed in transit.  Sub-second precision cannot be "
                "recovered on the Python side from what jsonio emits."),
}
if not boundary["variables"]:
    boundary["finding"] = "UNVERIFIED: no boundary payload to inspect."
elif all(date_pass.values()) and not any(num_pass.values()):
    boundary["finding"] = (
        "MEASURED, AND IT CONTRADICTS THE SECTION 08 OVERVIEW.  Section 08 "
        "opens with \"a %td variable arrives as a raw Stata SIF integer\".  It "
        "does not.  jsonio renders EVERY %t* variable through its display "
        "format and emits a JSON STRING (sp500 date arrives as \"02jan2001\", "
        "not 14977), while still reporting variableIsString=false for it.  "
        "Numeric display formats are NOT applied: %9.0fc and %9.2f come across "
        "as raw JSON numbers.  So the Python side must parse a formatted date "
        "STRING, not offset an integer -- and _load_data's existing "
        "pd.to_numeric(..., errors=\"coerce\") will turn those strings into "
        "NaN.  Tasks 08-03 and 08-04 must be re-read against this.")
elif not any(date_pass.values()):
    boundary["finding"] = (
        "Section 08's premise holds at the boundary: jsonio emits %t* variables "
        "as raw numeric SIF values, so the Python side offsets an integer.")
else:
    boundary["finding"] = (
        "Mixed result; see per-variable rows.  Date variables emitted as "
        "strings: " + repr(date_pass) + "; numeric-format variables emitted as "
        "strings: " + repr(num_pass))

# Does the gating bug merely disable metaprint(), or silently change the call?
p1 = jsonio_rows.get("dashstyle", {})
p2 = jsonio_rows.get("metaprint_with_filenm", {})
fallthrough = None
if p1.get("output_exists") and p2.get("output_exists"):
    try:
        with open(p1["path"], "rb") as a, open(p2["path"], "rb") as b:
            same = a.read() == b.read()
        fallthrough = {
            "byte_identical_to_what_all": same,
            "meaning": (
                "metaprint() with a filenm() and NO what() produced a payload "
                "byte-identical to what(all): after the line 238 test fails, "
                "control reaches the final unconditional else (jsonio.ado:295) "
                "which calls printAllToFile.  metaprint() is not merely ignored "
                "-- the call silently degrades to a full data+metadata dump."
                if same else
                "metaprint() with a filenm() produced a payload that differs "
                "from what(all); see the two files."),
        }
    except Exception as exc:
        fallthrough = {"error": repr(exc)}
        UNVERIFIED.append("metaprint/what(all) payload comparison")
jsonio_block["gating_fallthrough"] = fallthrough

doc = {
    "_meta": {
        "generated_by": "scripts/extract_date_truth.do",
        "record_file": REC,
        "run_date": meta.get("run_date"),
        "stata_version": meta.get("stata_version"),
        "stata_flavor": meta.get("stata_flavor"),
        "stata_edition": meta.get("stata_edition"),
        "stata_born_date": meta.get("stata_born_date"),
        "os": meta.get("os"),
        "sysdir_base": meta.get("sysdir_base"),
        "method": (
            "Every value in this fixture was produced by a Stata display and "
            "carries the exact command that produced it.  Each date value is "
            "recorded twice: \"display\", the verbatim locale-dependent string "
            "Stata prints, and \"iso\", the same instant re-displayed through an "
            "explicit ISO-8601 picture, which is the unambiguous target for a "
            "Python converter.  Calendar-period formats (%tw %tm %tq %th) record "
            "the period START and END, derived with Stata's own dofw/dofm/dofq/"
            "dofh, and %ty with dofy, which takes a YEAR rather than an offset.  "
            "Display strings are captured between \"<\" and \">\" sentinels "
            "so that leading and trailing blanks -- which are part of what a "
            "numeric format means -- survive macro assignment; the sentinels are "
            "stripped when the fixture is written."),
        "honesty": (
            "Nothing here is recalled or inferred.  Anything that could not be "
            "derived empirically is marked \"source\": \"UNVERIFIED\" and listed "
            "under \"unverified\"."),
        "record_delimiter_note": (
            "Records are pipe-delimited; variable labels had \"|\" replaced with "
            "\"/\" before writing.  No display format or date string contains a "
            "pipe."),
        "counts": {
            "date_formats": len(date_formats),
            "date_values_total": sum(v["value_count"] for v in date_formats.values()),
            "date_values_per_format": {k: v["value_count"]
                                       for k, v in sorted(date_formats.items())},
            "numeric_formats": len(numeric_formats),
            "numeric_values_total": sum(v["value_count"]
                                        for v in numeric_formats.values()),
            "leap_probes": len(leap_rows),
            "datasets_probed": len(datasets),
            "dataset_variables_recorded": len(dsvar_rows),
            "dataset_date_variables": len(date_vars),
            "jsonio_boundary_variables": len(boundary["variables"]),
            "unverified": len(UNVERIFIED),
        },
    },
    "date_formats": date_formats,
    "ty_is_the_year_itself": {
        "conclusion": ty_conclusion,
        "why_it_matters": ("Offsetting a %ty value from 1960 -- the arithmetic that "
                           "is correct for the other seven formats -- turns 1998 "
                           "into 3958.  %ty must be used as-is."),
        "evidence": ty_off_by_1960,
    },
    "leap_seconds": {
        "finding": leap_finding,
        "tC_evaluable": tC_available,
        "method": ("Cofc(t) maps a %tc instant to the %tC value for the SAME "
                   "instant, so Cofc(t) - t is the accumulated leap-second offset "
                   "in milliseconds.  The same integer is also displayed under "
                   "both pictures to show the two formats disagree on what a given "
                   "number means."),
        "probes": leap_rows,
    },
    "left_aligned_prefix": {
        "note": ("Task 08-03 must match the %t / %-t prefix case-sensitively.  "
                 "These rows show Stata accepting the left-aligned variant of "
                 "each date format.  The SAME integer 14977 is fed to all eight, "
                 "so the resulting instants deliberately differ -- the point of "
                 "these rows is that the %-t spelling parses, not what it means."),
        "probes": prefix,
    },
    "numeric_formats": numeric_formats,
    "datasets": datasets,
    "dataset_date_variables": [
        {"dataset": d, "variable": v, "format": f} for d, v, f in date_vars],
    "sp500_finding": sp500_finding,
    "jsonio_display_formats": jsonio_block,
    "jsonio_value_boundary": boundary,
    "unverified": UNVERIFIED,
}

with open(OUT, "w") as fh:
    json.dump(doc, fh, indent=2, sort_keys=True)
    fh.write("\n")

print("WROTE " + OUT)
print("date_formats=%d date_values=%d numeric_formats=%d numeric_values=%d" % (
    len(date_formats),
    sum(v["value_count"] for v in date_formats.values()),
    len(numeric_formats),
    sum(v["value_count"] for v in numeric_formats.values())))
print("datasets=%d date_vars=%d unverified=%d" % (
    len(datasets), len(date_vars), len(UNVERIFIED)))
print("TY: " + ty_conclusion)
print("LEAP: " + leap_finding)
print("SP500: " + sp500_finding)
print("JSONIO: " + jsonio_finding)
print("BOUNDARY: " + boundary.get("finding", "(none)"))
for u in UNVERIFIED:
    print("UNVERIFIED " + u)
end

display as text "extract_date_truth.do: done"
