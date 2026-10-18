* extract_named_style_truth.do -- twoway's named styles p1-p15 (WP-30
* P1.14a, section 32), written to test/fixtures/named_style_truth.json for
* test/test_named_styles.py.
*
* Each case runs `twoway <cmd>, name(g, replace)'; the record keeps
* its rc, its first error line and its notes from a text log, and, when it
* drew, plots 1-3's resolved style read from the graph object
* (.g.plotregion1.plot<k>.style: marker, line and area) and, for the grids
* R, F, P and N, the stroke and fill colours of its SVG with their counts.
* Grids: B the seriesstyle p1-p15 under every shipped scheme; R each plot
* type under each of the ten style options at p3 (stcolor, s1mono); F the
* factor order; P p(); N the plot numbering and per-y lists; A twoway's
* abbreviations; U other names (for section 36 and the interim note).
*
* Run (never the GUI; the slot wrapper of scripts/stata_slot.sh):
*   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_named_style_truth.do
* The SVG and log files are written to the current directory (the slot
* wrapper's scratch directory).

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_named_style_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_named_style_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1

clear all
set more off
set linesize 255
version 19
local entry_scheme "`c(scheme)'"

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
global NP_RF `rf'
global NP_SEQ 0

capture program drop _np_read
program _np_read
    // _np_read k: plot k's resolved style, one |-separated record of
    // name=value fields, in s(rec) ("" when the plot does not exist).
    args k
    local rec ""
    capture local t "`.g.plotregion1.plot`k'.style.marker.fillcolor.rgb'"
    if _rc | `"`t'"' == "" {
        c_local _np_rec ""
        exit
    }
    foreach f in mf:marker.fillcolor.rgb mfop:marker.fillcolor.opacity ///
        ml:marker.linestyle.color.rgb mlop:marker.linestyle.color.opacity ///
        mlw:marker.linestyle.width.val ms:marker.symbol.stylename ///
        msz:marker.size.val lc:line.color.rgb lop:line.color.opacity ///
        lw:line.width.val lp:line.pattern.stylename ///
        af:area.shadestyle.color.rgb afop:area.shadestyle.color.opacity ///
        ai:area.shadestyle.intensity.val al:area.linestyle.color.rgb ///
        alop:area.linestyle.color.opacity alw:area.linestyle.width.val ///
        alp:area.linestyle.pattern.stylename labc:label.textstyle.color.rgb {
        gettoken nm path : f, parse(":")
        local path = substr("`path'", 2, .)
        local v ""
        capture local v "`.g.plotregion1.plot`k'.style.`path''"
        local v = strtrim(stritrim(`"`v'"'))
        local rec `"`rec'`nm'=`v';"'
    }
    c_local _np_rec `"`rec'"'
end

capture program drop _np_case
program _np_case
    // _np_case id scheme data svg cmd: run twoway cmd under scheme on auto
    // or sp500, logging it, and append the record line.
    args id scheme data svg cmd
    if "`data'" == "sp500" {
        quietly sysuse sp500, clear
        quietly tsset date
    }
    else quietly sysuse auto, clear
    set scheme `scheme'
    local log "`c(pwd)'/np_`id'.log"
    local svgf ""
    capture graph drop g
    quietly log using "`log'", text replace name(nptruth)
    // graph export needs a drawn graph; the other rows are not drawn.
    local nd = cond("`svg'" == "1", "", "nodraw")
    capture noisily twoway `macval(cmd)' name(g, replace) `nd'
    local rc = _rc
    quietly log close nptruth
    local recs ""
    if !`rc' {
        forvalues k = 1/3 {
            _np_read `k'
            local recs `"`recs'`_np_rec'#"'
        }
        if "`svg'" == "1" {
            local svgf "`c(pwd)'/np_`id'.svg"
            quietly graph export "`svgf'", replace name(g)
        }
    }
    // The command by value, under a numbered global (an id holds "-").
    global NP_SEQ = ${NP_SEQ} + 1
    file write $NP_RF `"`id'|${NP_SEQ}|`scheme'|`rc'|`svgf'|`log'|`recs'"' _n
    mata: st_global("NP_CMD_" + st_global("NP_SEQ"), st_local("cmd"))
end

* ---- B: the seriesstyle p1-p15 under every shipped scheme ----
foreach s in economist meta s1color s1manual s1mono s1rcolor s2color s2color8 s2gcolor s2gmanual s2manual s2mono sj stcolor stcolor_alt stcolor_meta stcolor_mv stcoloralias stgcolor stgcolor_alt stgcolor_meta stgcolor_mv stmono1 stmono2 stsj sttrans {
    forvalues k = 1/15 {
        _np_case B-`s'-p`k' `s' auto 0 `"scatter mpg weight in 1/5, pstyle(p`k')"'
    }
}

* ---- R: each type under each of the ten options at p3 ----
local T_scatter    "mpg weight in 1/10|"
local T_line       "mpg weight in 1/10|sort"
local T_connected  "mpg weight in 1/10|sort"
local T_area       "mpg weight in 1/10|sort"
local T_rarea      "mpg turn weight in 1/10|sort"
local T_bar        "mpg weight in 1/10|"
local T_rbar       "mpg turn weight in 1/10|"
local T_histogram  "mpg|"
local T_spike      "mpg weight in 1/10|"
local T_rspike     "mpg turn weight in 1/10|"
local T_rcap       "mpg turn weight in 1/10|"
local T_rcapsym    "mpg turn weight in 1/10|"
local T_rline      "mpg turn weight in 1/10|sort"
local T_rconnected "mpg turn weight in 1/10|sort"
local T_rscatter   "mpg turn weight in 1/10|"
local T_dropline   "mpg weight in 1/10|"
local T_dot        "mpg weight in 1/10|"
local T_lfit       "mpg weight|"
local T_qfit       "mpg weight|"
local T_lowess     "mpg weight|"
local T_lpoly      "mpg weight|"
local T_fpfit      "mpg weight|"
local T_kdensity   "mpg|"
local T_mspline    "mpg weight|"
local T_mband      "mpg weight|"
local T_function   "y=x|range(0 1)"
local T_lfitci     "mpg weight|"
local T_lpolyci    "mpg weight|"
local T_pcspike    "mpg weight turn length in 1/10|"
local T_pccapsym   "mpg weight turn length in 1/10|"
local T_pcscatter  "mpg weight turn length in 1/10|"
local T_pcarrow    "mpg weight turn length in 1/10|"
local T_pcbarrow   "mpg weight turn length in 1/10|"
local T_scatteri   "20 3000 25 4000|"
local T_pci        "20 2000 30 4000|"
local T_pcarrowi   "15 2000 25 4000|"
local T_tsline     "close in 1/30|"
local types "scatter line connected area rarea bar rbar histogram spike rspike rcap rcapsym rline rconnected rscatter dropline dot lfit qfit lowess lpoly fpfit kdensity mspline mband function lfitci lpolyci pcspike pccapsym pcscatter pcarrow pcbarrow scatteri pci pcarrowi tsline"
foreach s in stcolor s1mono {
    foreach t of local types {
        gettoken vars extra : T_`t', parse("|")
        local extra = substr(`"`extra'"', 2, .)
        local data = cond("`t'" == "tsline", "sp500", "auto")
        _np_case R-`s'-`t'-none `s' `data' 1 `"`t' `vars', `extra'"'
        foreach o in pstyle p lstyle clstyle mstyle mlstyle astyle alstyle bstyle blstyle {
            _np_case R-`s'-`t'-`o' `s' `data' 1 `"`t' `vars', `extra' `o'(p3)"'
        }
    }
}

* ---- F: the factor order (stcolor) ----
local i = 0
foreach c in "scatter mpg weight, color(red) mstyle(p4)" ///
    "scatter mpg weight, mstyle(p4) color(red)" ///
    "scatter mpg weight, mlcolor(red) mstyle(p4)" ///
    "scatter mpg weight, mstyle(p4) mlcolor(red)" ///
    "scatter mpg weight, mstyle(p4) mlstyle(p3)" ///
    "scatter mpg weight, mlstyle(p3) mstyle(p4)" ///
    "connected mpg weight, sort lstyle(p3) clstyle(p4)" ///
    "connected mpg weight, sort clstyle(p4) lstyle(p3)" ///
    "line mpg weight, sort lwidth(thick) lstyle(p3)" ///
    "line mpg weight, sort lstyle(p3) lwidth(thick)" ///
    "area mpg weight, sort color(red) astyle(p4)" ///
    "area mpg weight, sort color(red) pstyle(p4)" ///
    "area mpg weight, sort fintensity(30) astyle(p4)" ///
    "bar mpg weight, blcolor(red) bstyle(p4)" ///
    "bar mpg weight, bfcolor(red) bstyle(p4)" ///
    "lfitci mpg weight, pstyle(p3) astyle(p4)" ///
    "scatter mpg weight, msymbol(T) mstyle(p4)" ///
    "scatter mpg weight, mstyle(p4) msymbol(T)" ///
    "scatter mpg weight, msize(huge) pstyle(p3)" ///
    "line mpg weight, sort lcolor(red) lstyle(p4)" ///
    "line mpg weight, sort lstyle(p4) lcolor(red)" ///
    "connected mpg weight, sort mcolor(red) mlstyle(p3)" ///
    "rcap mpg turn weight, lcolor(red) alstyle(p4)" ///
    "lfitci mpg weight, acolor(red) astyle(p4)" ///
    "lfitci mpg weight, lstyle(p4) lcolor(red)" ///
    "scatter mpg weight, mcolor(red) pstyle(p3)" ///
    "line mpg weight, sort lcolor(red) pstyle(p3)" ///
    "area mpg weight, sort fcolor(red) pstyle(p3)" ///
    "bar mpg weight, color(red) blstyle(p4)" ///
    "spike mpg weight, lcolor(red) alstyle(p4)" ///
    "spike mpg weight, alstyle(p4) lcolor(red)" ///
    "dropline mpg weight, mcolor(red) mstyle(p4)" ///
    "dropline mpg weight, mstyle(p4) mcolor(red)" ///
    "dropline mpg weight, lstyle(p3) mcolor(red)" {
    local ++i
    local id = "F" + string(`i', "%02.0f")
    _np_case `id' stcolor auto 1 `"`c'"'
}

* ---- P: p() (stcolor) ----
local i = 0
foreach c in "scatter mpg weight, mcolor(red) msize(huge) p(p3)" ///
    "scatter mpg weight, mlabel(make) mlabcolor(red) p(p3)" ///
    "scatter mpg weight, mlabel(make) mlabposition(9) p(p3)" ///
    "scatter mpg weight, mlabel(make) mlabformat(%9.1f) p(p3)" ///
    "scatter mpg weight, mlabel(make) mlabgap(5) p(p3)" ///
    "scatter mpg weight, mfcolor(red) p(p3)" ///
    "scatter mpg weight, mlwidth(thick) p(p3)" ///
    "scatter mpg weight, cmissing(n) p(p3)" ///
    "scatter mpg weight, connect(l) sort p(p3)" ///
    "line mpg weight, sort lstyle(p4) p(p3)" ///
    "area mpg weight, sort fcolor(red) p(p3)" ///
    "scatter mpg weight, p(p3) pstyle(p4)" ///
    "scatter mpg weight, pstyle(p4) p(p3)" ///
    "scatter mpg weight, p(p3) p(p4)" ///
    "scatter mpg weight, mcolor(red) p(p3) p(bogus)" ///
    "scatter mpg weight, mcolor(red) p(bogus)" ///
    "scatter mpg weight, msymbol(T) p(p3 p4)" ///
    "scatter mpg weight, p(p3) mcolor(red%50)" ///
    "line mpg weight, sort p(p3)" ///
    "lfitci mpg weight, p(p3)" {
    local ++i
    local id = "P" + string(`i', "%02.0f")
    local sch = cond(`i' == 19, "s1mono", "stcolor")
    _np_case `id' `sch' auto 1 `"`c'"'
}

* ---- N: the plot numbering and per-y lists (stcolor) ----
local i = 0
foreach c in "(scatter mpg weight, pstyle(p3)) (scatter mpg turn)," ///
    "scatter mpg turn weight, pstyle(p3 p4)" ///
    "line mpg turn weight, sort lstyle(p3 p4)" ///
    "area mpg turn weight, sort astyle(p3 p4)" ///
    "scatter mpg weight, pstyle(p3 p4)" ///
    "scatter mpg turn weight, p(p3 p4)" ///
    "(scatteri 20 3000, pstyle(p3)) (function y=20, range(2000 4000) pstyle(p4))," ///
    "(pci 20 2000 30 4000, pstyle(p5)) (pcarrowi 15 2000 25 4000, pstyle(p6))," {
    local ++i
    local id = "N" + string(`i', "%02.0f")
    _np_case `id' stcolor auto 1 `"`c'"'
}

* ---- A: abbreviations (stcolor) ----
local i = 0
foreach c in "scatter mpg weight, psty(p3)" "scatter mpg weight, p(p3)" ///
    "line mpg weight, ls(p3)" "line mpg weight, cls(p3)" ///
    "scatter mpg weight, mst(p3)" "scatter mpg weight, mls(p3)" ///
    "area mpg weight, ast(p3)" "spike mpg weight, al(p3)" ///
    "bar mpg weight, bst(p3)" "bar mpg weight, bl(p3)" ///
    "scatter mpg weight, pst(p3)" "scatter mpg weight, ps(p3)" ///
    "area mpg weight, as(p3)" {
    local ++i
    local id = "A" + string(`i', "%02.0f")
    _np_case `id' stcolor auto 0 `"`c'"'
}

* ---- U: other names (stcolor) ----
foreach t in scatter line area {
    foreach o in pstyle lstyle mstyle astyle {
        foreach n in bogus P3 p16 p03 ci ci2 foreground refline p3line p3bar none {
            _np_case U-`t'-`o'-`n' stcolor auto 0 `"`t' mpg weight, sort `o'(`n')"'
        }
    }
}

file close `rf'
global NP_RF

python:
import json, os, re, sys
from sfi import Macro
repo = Macro.getLocal("repo")
sys.path.insert(0, os.path.join(repo, "scripts"))
import svg_truth

_EL = re.compile(r"<(circle|path|polygon|line|rect|polyline|ellipse|use)\b([^>]*)>")


def _paint(a, prop):
    st = svg_truth._style_of(a)
    v = st.get(prop, a.get(prop))
    return v.lower() if isinstance(v, str) else v


def _svg(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        txt = fh.read()
    strokes, fills = {}, {}
    for m in _EL.finditer(txt):
        a = svg_truth._attrs(m.group(2))
        for prop, out in (("stroke", strokes), ("fill", fills)):
            v = _paint(a, prop)
            if v and v != "none" and v.startswith("#"):
                out[v] = out.get(v, 0) + 1
    return {"strokes": sorted([k, n] for k, n in strokes.items()),
            "fills": sorted([k, n] for k, n in fills.items())}


def _log(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = [ln.rstrip("\n") for ln in fh]
    notes = [ln.strip() for ln in lines if ln.strip().startswith("(note:")]
    message = ""
    for ln in lines:
        s = ln.strip()
        if (not s or s.startswith("(note:") or re.match(r"^r\(\d+\);$", s)
                or s.startswith("name:") or s.startswith("log:")
                or s.startswith("log type:") or s.startswith("opened on:")
                or s.startswith("closed on:") or s.startswith("---")):
            continue
        message = s
        break
    return message, notes


def _plots(recs):
    out = {}
    for k, rec in enumerate(recs.split("#")[:3], start=1):
        if not rec:
            continue
        out[str(k)] = dict(f.split("=", 1) for f in rec.split(";") if "=" in f)
    return out


cases = {}
with open(Macro.getLocal("records"), encoding="utf-8") as fh:
    for ln in fh:
        cid, seq, scheme, rc, svg, log, recs = ln.rstrip("\n").split("|", 6)
        rec = {"cmd": Macro.getGlobal("NP_CMD_" + seq), "scheme": scheme,
               "rc": int(rc)}
        rec["message"], rec["notes"] = _log(log)
        rec["plots"] = _plots(recs)
        if svg:
            rec["svg"] = _svg(svg)
        cases[cid] = rec
schemes = sorted({c[2:].rsplit("-", 1)[0] for c in cases if c.startswith("B-")})
meta = {"stata_version": Macro.getLocal("stata_version"),
        "born_date": Macro.getLocal("born_date"),
        "source": "scripts/extract_named_style_truth.do",
        "dash_commit": Macro.getLocal("dash_commit"),
        "extracted": Macro.getLocal("extracted")}
out = os.path.join(repo, "test", "fixtures", "named_style_truth.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump({"cases": cases, "schemes": schemes, "_meta": meta}, fh,
              indent=2, sort_keys=True)
    fh.write("\n")
print("named_style_truth: wrote %d cases" % len(cases))
end

set scheme `entry_scheme'
