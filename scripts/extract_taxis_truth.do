* extract_taxis_truth.do -- twoway's time-axis options tlabel(), ttick(),
* tmlabel(), tmtick(), ttitle(), tscale() and tline() (WP-30 P1.6, section
* 51), written to test/fixtures/taxis_truth.json for
* test/test_taxis_options.py, the TA cases of
* test/test_twoway_option_parity.cscript and the S51 block of
* test/test_wp30_truth.cscript.
*
* Data (kind ts): 60 months, t = tm(2000m1)+_n-1 (%tm, tsset), y = 100+_n,
* y2 = y+5, n = _n, d = dofm(t) (%td), and the same dates as w (%tw),
* q (%tq), h (%th), yr (%ty), tc (%tc), tmon (%tmMon_CCYY) and t2 (%-tm).
* Kind auto: sysuse auto.
*
* Each probe runs `capture noisily twoway ...' inside a named log and
* records rc, the first line of the error (the first non-empty line that
* is no note), every `(note:' line and, for rc 0, x axis 1's major
* dlg_tickpos, the scale's curmin/curmax, the x title's lines and the
* vertical reference lines read from the exported SVG
* (scripts/svg_truth.py), placed in data units through the plot region's
* edges and curmin/curmax.  A literal probe (kind lit) records the value
* of `scalar s = <fn>(<token>)' and its rc.
*
* Run (never the GUI; the slot wrapper of scripts/stata_slot.sh):
*   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_taxis_truth.do

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_ta_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_ta_bad' {
    display as error "extract_taxis_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _ta_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_ta_rc' | _rc {
    local _ta_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_taxis_truth.do: `_ta_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1

clear all
set more off
set linesize 255
set graphics off
version 19

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
global TA_RF `rf'

capture program drop _ta_data
program _ta_data
    args kind
    if "`kind'" == "auto" {
        quietly sysuse auto, clear
        exit
    }
    clear
    quietly set obs 60
    quietly generate t = tm(2000m1) + _n - 1
    format t %tm
    quietly tsset t
    quietly generate y = 100 + _n
    quietly generate y2 = y + 5
    quietly generate n = _n
    quietly generate d = dofm(t)
    format d %td
    quietly generate w = wofd(d)
    format w %tw
    quietly generate q = qofd(d)
    format q %tq
    quietly generate h = hofd(d)
    format h %th
    quietly generate yr = yofd(d) + _n
    format yr %ty
    quietly generate double tc = cofd(d)
    format tc %tc
    quietly generate tmon = t
    format tmon %tmMon_CCYY
    quietly generate t2 = t
    format t2 %-tm
end

capture program drop _ta
program _ta
    // _ta id kind `"<twoway arguments>"': one probe, appended to the records
    // as id<TAB>kind<TAB>rc<TAB>log<TAB>svg<TAB>ticks<TAB>min<TAB>max<TAB>title.
    args id kind cmd
    _ta_data `kind'
    local log "`c(pwd)'/ta_`id'.log"
    capture graph drop _all
    quietly log using "`log'", text replace name(tatruth)
    capture noisily twoway `macval(cmd)'
    local rc = _rc
    quietly log close tatruth
    local svg ""
    local v ""
    local lo ""
    local hi ""
    local tt ""
    if !`rc' {
        local svg "`c(pwd)'/ta_`id'.svg"
        quietly graph export "`svg'", replace
        local n "`.Graph.xaxis1.major.dlg_tickpos.arrnels'"
        if "`n'" == "" | "`n'" == "." local n 0
        forvalues i = 1/`n' {
            local v "`v' `.Graph.xaxis1.major.dlg_tickpos[`i']'"
        }
        local lo "`.Graph.plotregion1.xscale.curmin'"
        local hi "`.Graph.plotregion1.xscale.curmax'"
        local m "`.Graph.xaxis1.title.text.arrnels'"
        if "`m'" == "" | "`m'" == "." local m 0
        forvalues i = 1/`m' {
            local tt `"`tt'`=cond(`i' > 1, char(31), "")'`.Graph.xaxis1.title.text[`i']'"'
        }
    }
    capture graph drop _all
    mata: st_global("TA_CMD_`id'", st_local("cmd"))
    file write $TA_RF "`id'" _tab "`kind'" _tab "`rc'" _tab "`log'" _tab "`svg'" _tab "`v'" _tab "`lo'" _tab "`hi'" _tab `"`tt'"' _n
end

capture program drop _ta_lit
program _ta_lit
    // _ta_lit id fn token: the value twoway's pseudo-function gives token.
    args id fn tok
    capture scalar s = `fn'(`tok')
    local rc = _rc
    local v ""
    if !`rc' local v = strofreal(scalar(s), "%21.0g")
    mata: st_global("TA_CMD_`id'", st_local("fn") + "|" + st_local("tok"))
    file write $TA_RF "`id'" _tab "lit" _tab "`rc'" _tab "" _tab "" _tab "`v'" _tab "" _tab "" _tab "" _n
end

* ---- 3.1 what each option does; 3.2 order (all on the 60 months) ----
_ta c00  ts `"tsline y"'
_ta c01  ts `"tsline y, tlabel(2000m1(12)2004m1)"'
_ta c02  ts `"tsline y, ttick(2000m7(12)2004m7)"'
_ta c03  ts `"tsline y, tmlabel(2000m7(12)2004m7)"'
_ta c04  ts `"tsline y, tmtick(2000m4(3)2004m10)"'
_ta c05  ts `"tsline y, ttitle("Month")"'
_ta c06  ts `"tsline y, tscale(range(1999m1 2006m1))"'
_ta c07  ts `"tsline y, tline(2002m1)"'
_ta c08  ts `"tsline y, tline(2001m1 2003m1)"'
_ta c09  ts `"tsline y, tline(2001m1(12)2003m1)"'
_ta c10  ts `"tsline y, tlabel(2000m1 "Start" 2002m6 "Mid")"'
_ta c11  ts `"tsline y, xlabel(2000m1(12)2004m1)"'
_ta c12  ts `"tsline y, xline(2002m1)"'
_ta c13  ts `"tsline y, xscale(range(1999m1 2006m1))"'
_ta c14  ts `"tsline y, xlabel(480(12)528) tlabel(2001m1 2003m1)"'
_ta c15  ts `"tsline y, tlabel(2001m1 2003m1) xlabel(480(12)528)"'
_ta c16  ts `"tsline y, tlabel(2001m1, add)"'
_ta c17  ts `"tsline y, tlabel(#3)"'
_ta c18  ts `"tsline y, tlabel(minmax)"'
_ta c20  ts `"line y t, tlabel(2000m1(12)2004m1)"'
_ta c21  auto `"scatter mpg weight, tlabel(2000 3000 4000)"'
_ta c22  auto `"scatter mpg weight, tlabel(2000m1)"'
_ta c23  ts `"tsline y, tlabel(2000x1)"'
_ta c25  ts `"line y d, tlabel(01jan2000 01apr2000 01jul2000)"'
_ta c25b ts `"line y d, tline(15feb2000)"'
_ta c25c ts `"line y d, tlabel(01jan2000(30)01jul2000)"'
_ta c25d ts `"line y d, tline(2000m3)"'
_ta c26  ts `"line y q, tline(2001q1)"'
_ta c27  ts `"line y tc, tline(01jan2000 12:00:00)"'
_ta c27b ts `"line y tc, tline(1300000000000)"'
_ta c27c ts `"line y tc, tlabel(2000m1)"'
_ta c28  ts `"line y yr, tline(2020)"'
_ta c30  ts `"tsline y, tline(2002m1, lcolor(red) lpattern(dash))"'
_ta c33  ts `"tsline y, ttitle("")"'
_ta c34  ts `"tsline y, tlabel(2001m1) tlabel(2003m1)"'
_ta c35  ts `"tsline y, xtitle("X") ttitle("T")"'
_ta c35b ts `"tsline y, ttitle("T") xtitle("X")"'
_ta c36  ts `"tsline y, tline(2002m1) xline(490)"'
_ta c37  ts `"line y w, tline(2000w20)"'
_ta c38  ts `"line y h, tline(2002h1)"'
_ta c42  ts `"tsline y, tline(2010m1)"'
_ta c43  ts `"tsline y, tlabel(2010m1)"'
_ta c44  ts `"(tsline y, tlabel(2001m1 2003m1)) (line y2 t)"'
_ta c45  ts `"tsline y || line y2 t, tlabel(2001m1 2003m1)"'
_ta c46  ts `"tsline y, tline(2002m1) tline(2003m1)"'
_ta c47  ts `"tsline y, tscale(range(2002m1 2003m1))"'
_ta c48  ts `"tsline y, tscale(range(1999m1)) tscale(range(2006m1))"'
_ta c49  ts `"tsline y, ttick(2000m7(12)2004m7, grid)"'
_ta c51  ts `"tsline y, tscale(log)"'
_ta c52  ts `"tsline y, tscale(reverse)"'
_ta c55  ts `"tsline y, tlabel((2000m1)(12)(2004m1))"'
_ta c57  ts `"tsline y, tlabel(2001m1(6)2002m1 2004m1)"'
_ta c60  ts `"line y n, tlabel(2000m1)"'
_ta c63  auto `"scatter mpg weight, ttitle("W")"'
_ta c64  auto `"scatter mpg weight, tline(3000)"'
_ta c65  auto `"scatter mpg weight, tscale(range(0 6000))"'

* ---- 3.6 refusals and the edges of the grammar ----
_ta e01  ts `"tsline y, tlabel(foo)"'
_ta e02  ts `"tsline y, tline(foo)"'
_ta e03  ts `"tsline y, tscale(range(foo))"'
_ta e04  ts `"tsline y, tlabel(2000m13)"'
_ta e05  ts `"tsline y, tline(2000m13)"'
_ta e06  ts `"tsline y, tlabel(2000m1(0)2004m1)"'
_ta e07  ts `"tsline y, tlabel(2004m1(12)2000m1)"'
_ta e08  ts `"tsline y, tline(2002m1 foo)"'
_ta e10  ts `"tsline y, tlabel(2000m1(12)2004m1 "x")"'
_ta e11  ts `"tsline y, ttitle("a" "b")"'
_ta e12  ts `"tsline y, tscale(range(2006m1))"'
_ta e13  ts `"tsline y, tline(2002m1(6)2003m1)"'
_ta e18  ts `"tsline y, tline(2000m6.5)"'
_ta e19  ts `"tsline y, tlabel(2000.5m1)"'
_ta e20  ts `"tsline y, tlabel(480 2002m1)"'
_ta e21  ts `"tsline y, tline(480 2002m1)"'
_ta e22  ts `"tsline y, tscale(range(480 2006m1))"'
_ta e27  ts `"tsline y, tlabel(2000m1;2001m1)"'
_ta e28  ts `"tsline y, tlabel(2000m1,2001m1)"'
_ta e31  ts `"line y tmon, tlabel(2001m1 2003m1)"'
_ta e34  ts `"(line y t) (line y d), tline(2002m1)"'
_ta e35  ts `"(line y d) (line y t), tline(2002m1)"'
_ta e36  ts `"(line y d) (line y t), tline(01jan2002)"'
_ta f01  ts `"line y n, tline(2002m1)"'
_ta f07  ts `"(tsline y) (line y2 d, xaxis(2)), tline(2002m1)"'
_ta f08  ts `"(tsline y) (line y2 d, xaxis(2)), tline(2002m1, axis(2))"'
_ta f08b ts `"(tsline y) (line y2 d, xaxis(2)), tline(01jan2002, axis(2))"'
_ta f08c ts `"(tsline y) (line y2 d, xaxis(2)), tlabel(01jan2001 01jan2003, axis(2))"'
_ta f09  ts `"tsline y, tlabel(2001m1, axis(3))"'
_ta f10  ts `"tsline y, tline(2002m1, axis(2))"'
_ta f11  ts `"tsline y, ttitle("A", axis(2))"'
_ta f12  ts `"tsline y, xlabel(2001m1, axis(3)) tlabel(2001m1, axis(3))"'
_ta f13  ts `"tsline y, tlabel(2001m1, axis(3)) ylabel(100, axis(3))"'
_ta f14  ts `"tsline y, tlabel(2001m1, , foo)"'
_ta g01  ts `"line y t2, tlabel(2001m1 2003m1)"'
_ta g02  ts `"line y t2, tline(2002m1)"'
_ta g03  ts `"line y t2, tscale(range(2006m1))"'
_ta g04  ts `"line y t2, ttick(2001m1) tline(2002m1)"'
_ta h05  ts `"tsline y, tmtick(##4)"'
_ta h06  ts `"tsline y, ttick(#10)"'
_ta k01  ts `"line y n, xlabel(, format(%tm)) tline(2002m1)"'
_ta k02  ts `"line y n, xlabel(, format(%tm)) tlabel(2001m1 2003m1)"'
_ta k03  ts `"line y n, tlabel(2001m1 2003m1, format(%tm))"'
_ta k04  ts `"line y n, tlabel(, format(%tm)) tline(2002m1)"'
_ta k05  ts `"tsline y, xlabel(, format(%td)) tline(2002m1)"'
_ta k06  ts `"tsline y, xlabel(, format(%td)) tlabel(2002m1)"'
_ta k07  ts `"line y n, xmlabel(, format(%tm)) tline(2002m1)"'
_ta k08  ts `"tsline y, xtitle("A", axis(2))"'
_ta m8   ts `"tsline y, tline(2000m1(1)2400m1)"'
_ta m8b  ts `"tsline y, tline(2000m1(1)2100m1)"'

* ---- 3.3 abbreviations ----
_ta ab_tl      ts `"tsline y, tl(2001m1 2003m1)"'
_ta ab_tlab    ts `"tsline y, tlab(2001m1 2003m1)"'
_ta ab_tlabels ts `"tsline y, tlabels(2001m1 2003m1)"'
_ta ab_tt      ts `"tsline y, tt("M")"'
_ta ab_tti     ts `"tsline y, tti("M")"'
_ta ab_ttit    ts `"tsline y, ttit("M")"'
_ta ab_tli     ts `"tsline y, tli(2002m1)"'
_ta ab_tlin    ts `"tsline y, tlin(2002m1)"'
_ta ab_tlines  ts `"tsline y, tlines(2002m1)"'
_ta ab_ttic    ts `"tsline y, ttic(2001m1 2003m1)"'
_ta ab_ttick   ts `"tsline y, ttick(2001m1 2003m1)"'
_ta ab_tticks  ts `"tsline y, tticks(2001m1 2003m1)"'
_ta ab_tsc     ts `"tsline y, tsc(range(1999m1))"'
_ta ab_tsca    ts `"tsline y, tsca(range(1999m1))"'
_ta ab_tml     ts `"tsline y, tml(2001m1)"'
_ta ab_tmt     ts `"tsline y, tmt(2001m1)"'
_ta ab_tm      ts `"tsline y, tm(2001m1)"'
_ta ab_ts      ts `"tsline y, ts(range(1999m1))"'

* ---- critic C2 (number first), C4 (pc types read x1) and operators ----
_ta c2_d1 ts `"line y d, tlabel(15000 01012001)"'
_ta c2_e1 ts `"line y d, tline(01012001 01jul2001)"'
_ta c2_e3 ts `"line y d, tline(1012001 01jul2001)"'
_ta pc1   ts `"pcspike y t y2 d, tline(2002m1)"'
_ta pc2   ts `"pcspike y d y2 t, tline(2002m1)"'
_ta op1   ts `"line y L.t, tline(2002m1)"'
_ta op2   ts `"line y L.t, tlabel(2001m1 2003m1)"'
_ta op3   ts `"line y D.t, tlabel(2001m1)"'

* ---- date literals in the x-options, axis 1 and axis 2 ----
_ta xl1  ts `"tsline y, xlabel(2000m1)"'
_ta xt1  ts `"tsline y, xtick(2000m1)"'
_ta xml1 ts `"tsline y, xmlabel(2000m1)"'
_ta xmt1 ts `"tsline y, xmtick(2000m1)"'
_ta xli1 ts `"tsline y, xline(2002m1)"'
_ta xsc1 ts `"tsline y, xscale(range(1999m1 2006m1))"'
_ta xl2  ts `"(tsline y) (line y2 t, xaxis(2)), xlabel(2000m1, axis(2))"'
_ta xt2  ts `"(tsline y) (line y2 t, xaxis(2)), xtick(2000m1, axis(2))"'
_ta xli2 ts `"(tsline y) (line y2 t, xaxis(2)), xline(2002m1, axis(2))"'
_ta xsc2 ts `"(tsline y) (line y2 t, xaxis(2)), xscale(range(1999m1) axis(2))"'
_ta xl2b ts `"(tsline y) (line y2 t, xaxis(2)), tlabel(2001m1 2003m1, axis(2))"'
_ta xli2b ts `"(tsline y) (line y2 t, xaxis(2)), tline(2002m1, axis(2))"'

* ---- the first-plot rule (m6.do): every type first, then (tsline y) ----
local m6 `"scatter "scatter y t" line "line y t" connected "connected y t" scatteri "scatteri 100 480" area "area y t" bar "bar y t" spike "spike y t" dropline "dropline y t" dot "dot y t" rarea "rarea y y2 t" rbar "rbar y y2 t" rspike "rspike y y2 t" rcap "rcap y y2 t" rcapsym "rcapsym y y2 t" rscatter "rscatter y y2 t" rline "rline y y2 t" rconnected "rconnected y y2 t" pcspike "pcspike y t y2 t" pccapsym "pccapsym y t y2 t" pcarrow "pcarrow y t y2 t" pcbarrow "pcbarrow y t y2 t" pcscatter "pcscatter y t y2 t" pci "pci 100 480 110 490" pcarrowi "pcarrowi 100 480 110 490" tsline "tsline y" tsrline "tsrline y y2" mband "mband y t" mspline "mspline y t" lowess "lowess y t" lfit "lfit y t" qfit "qfit y t" fpfit "fpfit y t" lfitci "lfitci y t" qfitci "qfitci y t" fpfitci "fpfitci y t" lpoly "lpoly y t" lpolyci "lpolyci y t" kdensity "kdensity y" histogram "histogram t" function "function y = x, range(480 539)""'
local i 0
local nm ""
foreach w of local m6 {
    local ++i
    if mod(`i', 2) local nm `"`w'"'
    else {
        _ta m6_`nm'_l ts `"(`w') (tsline y), tline(2002m1)"'
        _ta m6_`nm'_t ts `"(`w') (tsline y), tlabel(2001m1 2003m1)"'
    }
}

* ---- 3.5 literal leniency: the value twoway's own pseudo-function gives ----
local i 0
foreach tok in 2000x1 2000/1 2000-1 2000+1 2000*1 2000@1 2000=1 2000M1 2000m1 2000m13 2000m0 99m1 2000m1x -2000m1 10000m1 2000.5m1 {
    local ++i
    _ta_lit lit_m`i' m `tok'
}
local i 0
foreach tok in 1+jan+2000 1january2000 01JAN2000 01jan2000 2000-01-01 15feb2000 {
    local ++i
    _ta_lit lit_d`i' d `tok'
}
_ta_lit lit_w1 w 2000w20
_ta_lit lit_w2 w 2000w53
_ta_lit lit_q1 q 2001q1
_ta_lit lit_q2 q 2001q5
_ta_lit lit_h1 h 2002h1
_ta_lit lit_h2 h 2002h3

file close `rf'
global TA_RF

python:
import json, os, re, sys
from sfi import Macro
repo = Macro.getLocal("repo")
sys.path.insert(0, os.path.join(repo, "scripts"))
import svg_truth


def _log(path):
    """(first error line, notes) of a probe's log."""
    first, notes, cur = None, [], None
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = [ln.rstrip("\n").replace("\xa0", " ") for ln in fh]
    for ln in lines:
        s = ln.strip()
        if cur is not None:
            if s and not s.startswith("(note"):
                cur += " " + s
                continue
            notes.append(cur)
            cur = None
        if s.startswith("(note:"):
            cur = s
            continue
        if s and first is None and not s.startswith("(") \
                and not s.startswith("name:") and not s.startswith("log:") \
                and not s.startswith("log type:") \
                and not s.startswith("opened on:"):
            first = s
    if cur is not None:
        notes.append(cur)
    return first, [re.sub(r"\s+", " ", n) for n in notes]


def _num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def _lines(svg, ticks):
    """The vertical reference lines inside the plot region, in data units:
    each drawn line's segments grouped (svg_truth.line_groups), less the
    gridlines (the stroke of the horizontal gridlines), placed through the
    fit of the major ticks' pixels to their values."""
    if len(ticks) < 2:
        return None
    doc = svg_truth.svg_document(svg)
    try:
        rd = svg_truth.svg_axis_reading(svg, "x", tick_values=ticks, doc=doc)
    except ValueError:
        return None
    r, fit = doc["plotregion"], rd.get("fit")
    if r is None or fit is None or fit["space"] != "linear":
        return None
    p0, v0 = rd["tick_px"][0], ticks[0]
    left, right, top, bottom = r["left"], r["right"], r["top"], r["bottom"]
    tall = bottom - top
    grid = {g["stroke"] for g in svg_truth.line_groups(doc["hlines"], "y1")
            if g["span_to"] - g["span_from"] > 0.5 * (right - left)
            and top + 0.5 < g["px"] < bottom - 0.5}
    out = set()
    for g in svg_truth.line_groups(doc["vlines"], "x1"):
        if not (left + 0.5 < g["px"] < right - 0.5) or g["stroke"] in grid:
            continue
        if g["span_to"] - g["span_from"] < 0.5 * tall:
            continue
        out.add(round(v0 + (g["px"] - p0) * fit["units_per_px"], 1))
    return sorted(out)


probes = {}
with open(Macro.getLocal("records"), encoding="utf-8") as fh:
    for ln in fh:
        f = ln.rstrip("\n").split("\t")
        cid, kind, rc = f[0], f[1], int(f[2])
        cmd = Macro.getGlobal("TA_CMD_" + cid)
        if kind == "lit":
            fn, tok = cmd.split("|", 1)
            probes[cid] = {"kind": "lit", "fn": fn, "token": tok, "rc": rc,
                           "value": _num(f[5]) if f[5] else None}
            continue
        first, notes = _log(f[3])
        rec = {"kind": kind, "cmd": "twoway " + cmd, "rc": rc,
               "msg": first if rc else None, "notes": notes}
        if not rc:
            lo, hi = _num(f[6]), _num(f[7])
            rec["ticks"] = [float(v) for v in f[5].split()]
            rec["range"] = [lo, hi]
            rec["title"] = [t for t in f[8].split("\x1f")] if f[8] else []
            rec["lines"] = _lines(f[4], rec["ticks"])
        probes[cid] = rec
meta = {"stata_version": Macro.getLocal("stata_version"),
        "born_date": Macro.getLocal("born_date"),
        "source": "scripts/extract_taxis_truth.do",
        "dash_commit": Macro.getLocal("dash_commit"),
        "extracted": Macro.getLocal("extracted")}
out = os.path.join(repo, "test", "fixtures", "taxis_truth.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump({"probes": probes, "_meta": meta}, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote " + out + " (" + str(len(probes)) + " probes)")
end
