*! extract_abbrev_truth.do
*! Derive the ground-truth minimum abbreviation of every twoway option and
*! plottype that dash cares about, BY PROBING STATA ITSELF, and record what
*! dash does with the same abbreviation today.
*!
*! Output: test/fixtures/abbrev_truth.json
*!
*! Run with (Stata must be forced to its arm64 slice, and must be launched
*! from a scratch directory because batch mode writes its .log to the process
*! working directory):
*!
*!   mkdir -p /tmp/dash-wf/abbrev && cd /tmp/dash-wf/abbrev && \
*!   arch -arm64 /usr/local/bin/stata-mp -b do \
*!     /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/extract_abbrev_truth.do
*!
*! ---------------------------------------------------------------------------
*! METHOD
*!
*! Taking "the shortest prefix with _rc==0" is NOT sufficient.  twoway happily
*! accepts  xl(3000)  and  t(abc), but those resolve to xlabel() and t1title(),
*! not to xline() and title().  So every accepted prefix is checked against a
*! RESOLUTION ORACLE:
*!
*!   the graph is written to a live-format .gph -- which is a plain-text
*!   graph-object script -- the echoed command line and the per-run object ids
*!   are normalised away, and the text is compared byte for byte against the
*!   .gph produced by the FULL option name.  Identical => the prefix really did
*!   resolve to that option.
*!
*! Structure: Stata runs every probe and records (command, _rc, .gph path) into
*! a plain-text record file; a single trailing python: block reads that record
*! file, does the .gph comparisons, and writes the JSON fixture.  The python
*! block deliberately never calls back into Stata: SFIToolkit.stata() issued
*! from a do-file python block desynchronises the interpreter's input stream
*! after a few thousand calls (reproduced; it ends in r(7102)).
*! ---------------------------------------------------------------------------

clear all
adopath ++ "/Users/billy/Desktop/Programs/Java/StataJSON"
adopath ++ "/Users/billy/Desktop/Programs/StataPrograms/d/dash"
set graphics off
set more off
sysuse auto, clear

global ZQ_REPO "/Users/billy/Desktop/Programs/StataPrograms/d/dash"
global ZQ_OUT  "${ZQ_REPO}/test/fixtures/abbrev_truth.json"

* scratch area for the ~1500 probe .gph files and the record file
local scratch "`c(tmpdir)'/dash_abbrev_probe"
capture mkdir "`scratch'"
global ZQ_WORK "`scratch'"
global ZQ_REC  "`scratch'/probe_records.txt"
display as text "probe scratch dir: ${ZQ_WORK}"

global ZQ_SVER = c(stata_version)
global ZQ_FLAV = c(flavor)
global ZQ_EDIT = c(edition_real)
global ZQ_BORN = c(born_date)
global ZQ_DATE = c(current_date)

* ===========================================================================
* Registration helpers
* ===========================================================================
program define zq_ctx
    syntax, NAMe(string) CMD(string asis)
    global ZQ_NCTX = ${ZQ_NCTX} + 1
    global ZQ_CTXN_${ZQ_NCTX} "`name'"
    global ZQ_CTXC_${ZQ_NCTX} `"`cmd'"'
end

program define zq_opt
    syntax, OPT(string) [VALue(string asis) CTXs(string) ORAcle(string)]
    global ZQ_NOPT = ${ZQ_NOPT} + 1
    global ZQ_OPTN_${ZQ_NOPT} "`opt'"
    global ZQ_OPTV_${ZQ_NOPT} `"`value'"'
    global ZQ_OPTC_${ZQ_NOPT} "`ctxs'"
    global ZQ_OPTO_${ZQ_NOPT} "`oracle'"
end

program define zq_pt
    syntax, PT(string) VARs(string)
    global ZQ_NPT = ${ZQ_NPT} + 1
    global ZQ_PTN_${ZQ_NPT} "`pt'"
    global ZQ_PTV_${ZQ_NPT} "`vars'"
end

global ZQ_NCTX = 0
global ZQ_NOPT = 0
global ZQ_NPT  = 0

* ===========================================================================
* Plot-type contexts: the varlist that makes each a legal twoway plot
* ===========================================================================
zq_ctx, name(scatter)   cmd(scatter mpg weight)
zq_ctx, name(line)      cmd(line mpg weight)
zq_ctx, name(connected) cmd(connected mpg weight)
zq_ctx, name(bar)       cmd(bar mpg weight)
zq_ctx, name(area)      cmd(area mpg weight)
zq_ctx, name(spike)     cmd(spike mpg weight)
zq_ctx, name(dropline)  cmd(dropline mpg weight)
zq_ctx, name(dot)       cmd(dot mpg weight)
zq_ctx, name(histogram) cmd(histogram mpg)
zq_ctx, name(kdensity)  cmd(kdensity mpg)
zq_ctx, name(lowess)    cmd(lowess mpg weight)
zq_ctx, name(lpoly)     cmd(lpoly mpg weight)
zq_ctx, name(lfit)      cmd(lfit mpg weight)
zq_ctx, name(lfitci)    cmd(lfitci mpg weight)
zq_ctx, name(lpolyci)   cmd(lpolyci mpg weight)
zq_ctx, name(mband)     cmd(mband mpg weight)
zq_ctx, name(mspline)   cmd(mspline mpg weight)
zq_ctx, name(rarea)     cmd(rarea turn mpg weight)
zq_ctx, name(rbar)      cmd(rbar turn mpg weight)
zq_ctx, name(rcap)      cmd(rcap turn mpg weight)
zq_ctx, name(function)  cmd(function y=x)

* ===========================================================================
* Options to probe.  ctxs() restricts the search order; empty = try them all
* in registration order.  oracle() selects a dedicated side-effect oracle for
* options that leave no trace in the .gph.
* ===========================================================================
* ---- graph-level options dash already declares ----
zq_opt, opt(title)        value(ZQSENTINEL)
zq_opt, opt(subtitle)     value(ZQSENTINEL)
zq_opt, opt(note)         value(ZQSENTINEL)
zq_opt, opt(caption)      value(ZQSENTINEL)
zq_opt, opt(name)         oracle(graph_exists)
zq_opt, opt(saving)       oracle(file_exists)
zq_opt, opt(xtitle)       value(ZQSENTINEL)
zq_opt, opt(ytitle)       value(ZQSENTINEL)
zq_opt, opt(xlabel)       value(2000 3000)
zq_opt, opt(ylabel)       value(20 30)
zq_opt, opt(xline)        value(3000)
zq_opt, opt(yline)        value(20)
zq_opt, opt(legend)       value(off)
zq_opt, opt(by)           value(foreign)
zq_opt, opt(xscale)       value(log)
zq_opt, opt(yscale)       value(log)
zq_opt, opt(aspectratio)  value(1)
zq_opt, opt(scheme)       value(s2color)
zq_opt, opt(plotregion)   value(margin(zero))
zq_opt, opt(graphregion)  value(margin(zero))
* ---- plot-level options dash already declares ----
zq_opt, opt(mcolor)       value(red)
zq_opt, opt(msymbol)      value(oh)
zq_opt, opt(msize)        value(large)
zq_opt, opt(msangle)      value(45)
zq_opt, opt(mfcolor)      value(red)
zq_opt, opt(mlcolor)      value(red)
zq_opt, opt(mlabel)       value(make)
zq_opt, opt(mlabcolor)    value(red)
zq_opt, opt(mlabsize)     value(large)
zq_opt, opt(mlabposition) value(12)
zq_opt, opt(mlabgap)      value(2)
zq_opt, opt(mlabwidth)    value(thick)
zq_opt, opt(malpha)       value(50)
zq_opt, opt(marker)       value(1)
zq_opt, opt(lcolor)       value(red)
zq_opt, opt(lwidth)       value(thick)
zq_opt, opt(lpattern)     value(dash)
zq_opt, opt(lalpha)       value(50)
zq_opt, opt(fcolor)       value(red)
zq_opt, opt(fintensity)   value(50)
zq_opt, opt(falpha)       value(50)
zq_opt, opt(barwidth)     value(100)
zq_opt, opt(base)         value(0)
zq_opt, opt(blcolor)      value(red)
zq_opt, opt(bfcolor)      value(red)
zq_opt, opt(jitter)       value(5)
zq_opt, opt(jseed)        value(123)
zq_opt, opt(jitterseed)   value(123)
zq_opt, opt(colorlist)    value(red blue)
zq_opt, opt(yaxis)        value(1)
zq_opt, opt(xaxis)        value(1)
zq_opt, opt(colorvar)     value(turn)
zq_opt, opt(colpalette)   value(viridis)
zq_opt, opt(colordiscrete)
zq_opt, opt(coloruseplegend)
zq_opt, opt(colornlevels)  value(4)
zq_opt, opt(colorcuts)     value(20 30)
zq_opt, opt(colormissing)  value(gray)
zq_opt, opt(bwidth)        value(0.5) ctxs(lowess lpoly lpolyci)
zq_opt, opt(degree)        value(1)   ctxs(lpoly lpolyci)
zq_opt, opt(pstyle)        value(p2)
zq_opt, opt(cmissing)      value(n)
zq_opt, opt(recast)        value(line)
zq_opt, opt(connect)       value(l)
* ---- options the plan intends to add ----
zq_opt, opt(xsize)        value(4)
zq_opt, opt(ysize)        value(4)
zq_opt, opt(text)         value(20 3000 "ZQSENTINEL")
zq_opt, opt(xtick)        value(2000 3000)
zq_opt, opt(ytick)        value(20 30)
zq_opt, opt(xmtick)       value(2500)
zq_opt, opt(ymtick)       value(25)
zq_opt, opt(xmlabel)      value(2500)
zq_opt, opt(ymlabel)      value(25)
zq_opt, opt(sort)
zq_opt, opt(horizontal)
zq_opt, opt(vertical)
zq_opt, opt(mlwidth)      value(thick)
zq_opt, opt(mstyle)       value(p2)
zq_opt, opt(lstyle)       value(p2)
zq_opt, opt(mlstyle)      value(p2)
zq_opt, opt(mlpattern)    value(dash)
zq_opt, opt(color)        value(red)
zq_opt, opt(blabel)       value(total)
zq_opt, opt(bin)          value(10) ctxs(histogram)
zq_opt, opt(width)        value(2)  ctxs(histogram)
zq_opt, opt(start)        value(10) ctxs(histogram)
zq_opt, opt(percent)      ctxs(histogram kdensity)
zq_opt, opt(frequency)    ctxs(histogram kdensity)
zq_opt, opt(density)      ctxs(histogram kdensity)
zq_opt, opt(fraction)     ctxs(histogram kdensity)
zq_opt, opt(kernel)       value(epanechnikov) ctxs(kdensity lpoly lpolyci lowess)
zq_opt, opt(n)            value(50) ctxs(kdensity lpoly lpolyci function)
zq_opt, opt(level)        value(90) ctxs(lfitci lpolyci)
zq_opt, opt(bands)        value(20) ctxs(mband mspline lowess)
zq_opt, opt(at)           value(weight) ctxs(lpoly lpolyci kdensity)
zq_opt, opt(ciopts)       value(lcolor(red)) ctxs(lfitci lpolyci)
zq_opt, opt(lineopts)     value(lcolor(red)) ctxs(lfitci lpolyci)
zq_opt, opt(fitopts)      value(lcolor(red)) ctxs(lfitci lpolyci lowess)
zq_opt, opt(range)        value(1 10) ctxs(function)
zq_opt, opt(nodraw)       oracle(rc_flag)
zq_opt, opt(t1title)      value(ZQSENTINEL)
zq_opt, opt(t2title)      value(ZQSENTINEL)
zq_opt, opt(b1title)      value(ZQSENTINEL)
zq_opt, opt(b2title)      value(ZQSENTINEL)
zq_opt, opt(l1title)      value(ZQSENTINEL)
zq_opt, opt(l2title)      value(ZQSENTINEL)
zq_opt, opt(r1title)      value(ZQSENTINEL)
zq_opt, opt(r2title)      value(ZQSENTINEL)

* ===========================================================================
* Plot types to probe
* ===========================================================================
zq_pt, pt(scatter)    vars(mpg weight)
zq_pt, pt(line)       vars(mpg weight)
zq_pt, pt(connected)  vars(mpg weight)
zq_pt, pt(area)       vars(mpg weight)
zq_pt, pt(bar)        vars(mpg weight)
zq_pt, pt(spike)      vars(mpg weight)
zq_pt, pt(dot)        vars(mpg weight)
zq_pt, pt(dropline)   vars(mpg weight)
zq_pt, pt(histogram)  vars(mpg)
zq_pt, pt(kdensity)   vars(mpg)
zq_pt, pt(lfit)       vars(mpg weight)
zq_pt, pt(qfit)       vars(mpg weight)
zq_pt, pt(lfitci)     vars(mpg weight)
zq_pt, pt(qfitci)     vars(mpg weight)
zq_pt, pt(lowess)     vars(mpg weight)
zq_pt, pt(lpoly)      vars(mpg weight)
zq_pt, pt(lpolyci)    vars(mpg weight)
zq_pt, pt(fpfit)      vars(mpg weight)
zq_pt, pt(fpfitci)    vars(mpg weight)
zq_pt, pt(mspline)    vars(mpg weight)
zq_pt, pt(mband)      vars(mpg weight)
zq_pt, pt(tsline)     vars(mpg)
zq_pt, pt(rarea)      vars(turn mpg weight)
zq_pt, pt(rbar)       vars(turn mpg weight)
zq_pt, pt(rspike)     vars(turn mpg weight)
zq_pt, pt(rcap)       vars(turn mpg weight)
zq_pt, pt(rline)      vars(turn mpg weight)
zq_pt, pt(rconnected) vars(turn mpg weight)
zq_pt, pt(rscatter)   vars(turn mpg weight)
zq_pt, pt(pcarrow)    vars(mpg weight turn length)
zq_pt, pt(pcspike)    vars(mpg weight turn length)
zq_pt, pt(scatteri)   vars(20 3000)
zq_pt, pt(function)   vars(y=x)

* ===========================================================================
* Probe loop
* ===========================================================================
tempname rec
file open `rec' using "${ZQ_REC}", write text replace

file write `rec' "META|stata_version|${ZQ_SVER}" _n
file write `rec' "META|stata_flavor|${ZQ_FLAV}" _n
file write `rec' "META|stata_edition|${ZQ_EDIT}" _n
file write `rec' "META|stata_born_date|${ZQ_BORN}" _n
file write `rec' "META|run_date|${ZQ_DATE}" _n
file write `rec' "META|workdir|${ZQ_WORK}" _n

* ---- baselines: same context with no options at all --------------------
* NOTE: a loop header must not contain ${...}: the closing brace of the macro
* reference confuses Stata's block-brace scanner ("code follows on the same
* line as open brace").  Loop bounds are therefore always held in locals.
local NCTX = $ZQ_NCTX
local NOPT = $ZQ_NOPT
local NPT  = $ZQ_NPT
* Each baseline is produced TWICE: some plottypes (the smoothers) do not write
* a reproducible serset, and in those contexts the identity oracle is invalid.
forvalues j = 1/`NCTX' {
    local cn "${ZQ_CTXN_`j'}"
    local cc "${ZQ_CTXC_`j'}"
    local pa "${ZQ_WORK}/base_`cn'_a.gph"
    local pb "${ZQ_WORK}/base_`cn'_b.gph"
    set seed 12345
    capture twoway `cc', nodraw saving("`pa'", replace)
    local rca = _rc
    set seed 12345
    capture twoway `cc', nodraw saving("`pb'", replace)
    file write `rec' "BASE|`cn'|`rca'|`pa'|`pb'" _n
}

* ---- oracle self-check: the same command run twice must normalise to the
*      same text, otherwise every comparison below is meaningless -----------
set seed 12345
capture twoway scatter mpg weight, title(ZQSENTINEL) nodraw saving("${ZQ_WORK}/selfchk_a.gph", replace)
sleep 1100
set seed 12345
capture twoway scatter mpg weight, title(ZQSENTINEL) nodraw saving("${ZQ_WORK}/selfchk_b.gph", replace)
file write `rec' "SELFCHK|${ZQ_WORK}/selfchk_a.gph|${ZQ_WORK}/selfchk_b.gph" _n

* ---- options ------------------------------------------------------------
forvalues i = 1/`NOPT' {
    local nm  "${ZQ_OPTN_`i'}"
    local vl  `"${ZQ_OPTV_`i'}"'
    local cl  "${ZQ_OPTC_`i'}"
    local ora "${ZQ_OPTO_`i'}"
    local L   = strlen("`nm'")

    if "`ora'" == "graph_exists" {
        local found ""
        forvalues k = 1/`L' {
            local pre = substr("`nm'", 1, `k')
            capture graph drop _all
            capture twoway scatter mpg weight, `pre'(zqnm`k') nodraw
            local rc1 = _rc
            capture graph describe zqnm`k'
            local rc2 = _rc
            file write `rec' "DIRECTTRY|`nm'|`k'|`pre'|`rc1'|`rc2'" _n
            if `rc1' == 0 & `rc2' == 0 & "`found'" == "" local found "`pre'"
        }
        capture graph drop _all
        file write `rec' "DIRECT|`nm'|`found'|graph-created-under-name|twoway scatter mpg weight, `found'(zqname) nodraw" _n
        capture dash clear
        capture dash scatter mpg weight, `found'(zqdash)
        file write `rec' `"DASHNAME|`nm'|`found'|`=_rc'|${dash_graph_registry}"' _n
        capture dash clear
        continue
    }
    if "`ora'" == "file_exists" {
        local found ""
        forvalues k = 1/`L' {
            local pre = substr("`nm'", 1, `k')
            local p "${ZQ_WORK}/zqsav`k'.gph"
            capture erase "`p'"
            capture twoway scatter mpg weight, `pre'("`p'", replace) nodraw
            local rc1 = _rc
            capture confirm file "`p'"
            local rc2 = _rc
            file write `rec' "DIRECTTRY|`nm'|`k'|`pre'|`rc1'|`rc2'" _n
            if `rc1' == 0 & `rc2' == 0 & "`found'" == "" local found "`pre'"
        }
        file write `rec' "DIRECT|`nm'|`found'|file-written|twoway scatter mpg weight, `found'(<path>.gph, replace) nodraw" _n
        capture dash clear
        capture dash scatter mpg weight, `found'("${ZQ_WORK}/zqdashsav.gph") name(zqdash)
        file write `rec' `"DASH|`nm'|0|`found'|`=_rc'|${dash_json_zqdash}"' _n
        capture dash clear
        continue
    }
    if "`ora'" == "rc_flag" {
        local found ""
        forvalues k = 1/`L' {
            local pre = substr("`nm'", 1, `k')
            capture graph drop _all
            capture twoway scatter mpg weight, `pre'
            local rc1 = _rc
            capture graph drop _all
            file write `rec' "DIRECTTRY|`nm'|`k'|`pre'|`rc1'|0" _n
            if `rc1' == 0 & "`found'" == "" local found "`pre'"
        }
        file write `rec' "DIRECT|`nm'|`found'|return-code-only (bare flag leaves no trace in the .gph)|twoway scatter mpg weight, `found'" _n
        capture dash clear
        capture dash scatter mpg weight, `found' name(zqdash)
        file write `rec' `"DASH|`nm'|0|`found'|`=_rc'|${dash_json_zqdash}"' _n
        capture dash clear
        continue
    }

    * ---- choose the first context in which the FULL name is accepted ----
    local ctxname ""
    local lastrc  .
    local jlist ""
    if "`cl'" == "" {
        forvalues j = 1/`NCTX' {
            local jlist "`jlist' `j'"
        }
    }
    else {
        foreach want of local cl {
            forvalues j = 1/`NCTX' {
                if "${ZQ_CTXN_`j'}" == "`want'" local jlist "`jlist' `j'"
            }
        }
    }
    foreach j of local jlist {
        local cn "${ZQ_CTXN_`j'}"
        local cc "${ZQ_CTXC_`j'}"
        local p  "${ZQ_WORK}/ref_`nm'_`cn'.gph"
        if `"`vl'"' == "" local ostr "`nm'"
        else              local ostr `"`nm'(`vl')"'
        set seed 12345
        capture twoway `cc', `ostr' nodraw saving("`p'", replace)
        local lastrc = _rc
        if `lastrc' == 0 {
            local ctxname "`cn'"
            local ctxcmd  "`cc'"
            local refpath "`p'"
            continue, break
        }
    }
    if "`ctxname'" == "" {
        file write `rec' `"NOCTX|`nm'|`lastrc'|`vl'"' _n
        continue
    }
    file write `rec' `"OPT|`nm'|`ctxname'|`vl'|`ctxcmd'|`refpath'"' _n

    * ---- every proper prefix, in that context ----
    forvalues k = 1/`=`L'-1' {
        local pre = substr("`nm'", 1, `k')
        local p "${ZQ_WORK}/cand_`nm'_`k'.gph"
        if `"`vl'"' == "" local ostr "`pre'"
        else              local ostr `"`pre'(`vl')"'
        capture erase "`p'"
        set seed 12345
        capture twoway `ctxcmd', `ostr' nodraw saving("`p'", replace)
        file write `rec' "CAND|`nm'|`k'|`pre'|`=_rc'|`p'" _n
    }

    * ---- what dash does with each prefix (and with the full name) ----
    forvalues k = 1/`L' {
        local pre = substr("`nm'", 1, `k')
        if `"`vl'"' == "" local ostr "`pre'"
        else              local ostr `"`pre'(`vl')"'
        capture dash clear
        capture dash scatter mpg weight, `ostr' name(zqdash)
        file write `rec' `"DASH|`nm'|`k'|`pre'|`=_rc'|${dash_json_zqdash}"' _n
        capture dash clear
    }
    display as text "probed option `nm' (context `ctxname')"
}

* ---- plot types ---------------------------------------------------------
capture drop zqtime
quietly generate zqtime = _n
quietly tsset zqtime

forvalues i = 1/`NPT' {
    local pt "${ZQ_PTN_`i'}"
    local vr "${ZQ_PTV_`i'}"
    local L  = strlen("`pt'")
    local p  "${ZQ_WORK}/ptref_`pt'.gph"
    set seed 12345
    capture twoway `pt' `vr', nodraw saving("`p'", replace)
    local rc = _rc
    file write `rec' "PT|`pt'|`vr'|`rc'|`p'" _n
    if `rc' != 0 continue
    forvalues k = 1/`=`L'-1' {
        local pre = substr("`pt'", 1, `k')
        local pc "${ZQ_WORK}/ptcand_`pt'_`k'.gph"
        capture erase "`pc'"
        set seed 12345
        capture twoway `pre' `vr', nodraw saving("`pc'", replace)
        file write `rec' "PTCAND|`pt'|`k'|`pre'|`=_rc'|`pc'" _n
    }
    forvalues k = 1/`L' {
        local pre = substr("`pt'", 1, `k')
        capture dash clear
        capture dash `pre' `vr', name(zqdash)
        file write `rec' `"PTDASH|`pt'|`k'|`pre'|`=_rc'|${dash_json_zqdash}"' _n
        capture dash clear
    }
    display as text "probed plottype `pt'"
}
capture tsset, clear
capture drop zqtime

file close `rec'
display as text "records written to ${ZQ_REC}"

* ===========================================================================
* Analysis + JSON emission.  No callbacks into Stata from here on.
* ===========================================================================
python:
import json, os, re, collections
from sfi import Macro

REC  = Macro.getGlobal("ZQ_REC")
OUT  = Macro.getGlobal("ZQ_OUT")

# dash's hard-coded abbreviation table (dash_parse.mata, _expand_optkey).
DASH_TABLE = {
    "mc": "mcolor", "ms": "msymbol", "msi": "msize", "msa": "msangle",
    "mla": "mlabel", "mlc": "mlabcolor", "mls": "mlabsize",
    "mlp": "mlabposition", "mlg": "mlabgap", "mlw": "mlabwidth",
    "mfc": "mfcolor", "mal": "malpha", "m": "marker",
    "fc": "fcolor", "fi": "fintensity", "fa": "falpha",
    "blc": "blcolor", "bfc": "bfcolor", "bw": "barwidth",
    "lc": "lcolor", "lw": "lwidth", "lp": "lpattern", "lal": "lalpha",
    "fal": "falpha", "ti": "title", "sub": "subtitle", "xti": "xtitle",
    "yti": "ytitle", "xla": "xlabel", "yla": "ylabel", "note": "note",
    "cap": "caption", "leg": "legend", "sav": "saving", "nam": "name",
    "by": "by", "xsc": "xscale", "ysc": "yscale", "xl": "xline", "yl": "yline",
    "asp": "aspectratio", "plotr": "plotregion", "graphr": "graphregion",
    "jit": "jitter", "jse": "jseed", "yax": "yaxis", "xax": "xaxis",
    "sch": "scheme", "bwid": "bwidth", "deg": "degree",
    "cv": "colorvar", "colv": "colorvar", "colpal": "colpalette",
    "pbgc": "plotbgcolor", "bgc": "bgcolor",
    "yti2": "ytitle2", "xti2": "xtitle2", "yla2": "ylabel2",
    "xla2": "xlabel2", "ysc2": "yscale2", "xsc2": "xscale2",
}

# dash-only / unprobeable options, with the reason.  Never guessed.
SKIP = {
    "bgcolor":     "dash-only option; twoway has no bgcolor() (background colour is graphregion(fcolor()))",
    "plotbgcolor": "dash-only option; twoway has no plotbgcolor() (use plotregion(fcolor()))",
    "link":        "dash-only option (cross-filter link target); no twoway counterpart",
    "filter":      "dash-only option (interactive filter widget); no twoway counterpart",
    "ytitle2":     "dash-only secondary-axis option; twoway spells this ytitle(..., axis(2))",
    "xtitle2":     "dash-only secondary-axis option; twoway spells this xtitle(..., axis(2))",
    "ylabel2":     "dash-only secondary-axis option; twoway spells this ylabel(..., axis(2))",
    "xlabel2":     "dash-only secondary-axis option; twoway spells this xlabel(..., axis(2))",
    "yscale2":     "dash-only secondary-axis option; twoway spells this yscale(..., axis(2))",
    "xscale2":     "dash-only secondary-axis option; twoway spells this xscale(..., axis(2))",
    "title2":      "not a twoway option; Stata graphics has no title2()",
    "subtitle2":   "not a twoway option; Stata graphics has no subtitle2()",
    "play":        "play() needs an existing .grec recording file; not probeable without fabricating one",
}

# Volatile parts of a live .gph that must be normalised away before two probes
# can be compared:
#   *! ...            header comments: echo the command, the wall-clock time and
#                     the saving() path
#   .command = `"..."'  the same command echoed inside the graph object
#   .date / .time     wall-clock stamps -- these DO tick over between two
#                     consecutive probes and silently corrupt the comparison
#   K<hex>            per-run object ids for sersets and graph objects
_K    = re.compile(r"K[0-9a-fA-F]{6,}")
_BANG = re.compile(r"(?m)^\*!.*$")
_CMD  = re.compile(r"(?m)^\.(command|date|time) = .*$")

_cache = {}
def gph(path):
    if path in _cache:
        return _cache[path]
    txt = None
    if path and os.path.exists(path):
        with open(path, "r", errors="replace") as fh:
            txt = fh.read()
        txt = _BANG.sub("", txt)
        txt = _CMD.sub("", txt)
        txt = _K.sub("K#", txt)
    _cache[path] = txt
    return txt

selfchk = None
meta_rows, base, opt_rows, cand_rows, dash_rows = {}, {}, {}, [], []
direct_rows, directtry, dashname_rows, noctx = {}, [], {}, {}
pt_rows, ptcand_rows, ptdash_rows = {}, [], []

with open(REC, "r", errors="replace") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if not line:
            continue
        f = line.split("|")
        t = f[0]
        if   t == "META":      meta_rows[f[1]] = f[2]
        elif t == "SELFCHK":   selfchk = (f[1], f[2])
        elif t == "BASE":      base[f[1]] = (int(f[2]), f[3], f[4])
        elif t == "OPT":       opt_rows[f[1]] = {"ctx": f[2], "value": f[3], "ctxcmd": f[4], "ref": f[5]}
        elif t == "CAND":      cand_rows.append({"name": f[1], "k": int(f[2]), "pre": f[3], "rc": int(f[4]), "path": f[5]})
        elif t == "DASH":      dash_rows.append({"name": f[1], "k": int(f[2]), "pre": f[3], "rc": int(f[4]), "json": "|".join(f[5:])})
        elif t == "DIRECT":    direct_rows[f[1]] = {"abbrev": f[2], "oracle": f[3], "cmd": "|".join(f[4:])}
        elif t == "DIRECTTRY": directtry.append({"name": f[1], "k": int(f[2]), "pre": f[3], "rc1": int(f[4]), "rc2": int(f[5])})
        elif t == "DASHNAME":  dashname_rows[f[1]] = {"pre": f[2], "rc": int(f[3]), "registry": "|".join(f[4:])}
        elif t == "NOCTX":     noctx[f[1]] = {"rc": f[2], "value": "|".join(f[3:])}
        elif t == "PT":        pt_rows[f[1]] = {"vars": f[2], "rc": int(f[3]), "ref": f[4]}
        elif t == "PTCAND":    ptcand_rows.append({"name": f[1], "k": int(f[2]), "pre": f[3], "rc": int(f[4]), "path": f[5]})
        elif t == "PTDASH":    ptdash_rows.append({"name": f[1], "k": int(f[2]), "pre": f[3], "rc": int(f[4]), "json": "|".join(f[5:])})

# A context is usable for the identity oracle only if the very same command run
# twice normalises to the same text.  lowess/lpoly/lfitci and friends do not.
ctx_stable = {}
for cn, (rc, pa, pb) in base.items():
    ta, tb = gph(pa), gph(pb)
    ctx_stable[cn] = bool(ta is not None and tb is not None and ta == tb)

directtry_by = collections.defaultdict(dict)
for r in directtry:
    directtry_by[r["name"]][r["k"]] = r

cand_by = collections.defaultdict(dict)
for r in cand_rows:
    cand_by[r["name"]][r["k"]] = r
dash_by = collections.defaultdict(dict)
for r in dash_rows:
    dash_by[r["name"]][r["k"]] = r
ptcand_by = collections.defaultdict(dict)
for r in ptcand_rows:
    ptcand_by[r["name"]][r["k"]] = r
ptdash_by = collections.defaultdict(dict)
for r in ptdash_rows:
    ptdash_by[r["name"]][r["k"]] = r

def dash_keys(raw):
    """Full option keys dash recorded in its serialized spec."""
    try:
        spec = json.loads(raw)
    except Exception:
        return None
    keys = []
    for p in spec.get("plots", []):
        keys += [k for k in p.get("options", {}).keys()]
    keys += [k for k in spec.get("graph_options", {}).keys() if k != "name"]
    return keys

def dash_entry(name, k, abbrev):
    r = dash_by.get(name, {}).get(k)
    if r is None:
        return {"accepts": None, "rc": None, "key": None,
                "note": "no dash probe recorded"}
    if r["rc"] != 0:
        return {"accepts": False, "rc": r["rc"], "key": None,
                "probe_cmd": "dash scatter mpg weight, " + abbrev + "(...) name(zqdash)"}
    keys = dash_keys(r["json"])
    if keys is None:
        return {"accepts": True, "rc": 0, "key": None,
                "note": "dash spec JSON could not be parsed: " + r["json"][:120]}
    return {"accepts": True, "rc": 0,
            "key": keys[0] if len(keys) == 1 else None,
            "keys": None if len(keys) == 1 else keys}

# ------------------------------------------------------------------ options
options_out = {}
unprobeable = {}

for name, meta in sorted(opt_rows.items()):
    ctx  = meta["ctx"]
    val  = meta["value"]
    ref  = gph(meta["ref"])
    baserc, basepath, basepath2 = base.get(ctx, (1, None, None))
    basetxt = gph(basepath)

    if not ctx_stable.get(ctx, False):
        accepted = [cand_by[name][k]["pre"] for k in sorted(cand_by[name])
                    if cand_by[name][k]["rc"] == 0]
        unprobeable[name] = (
            "the only twoway context in which this option is legal (" + ctx + ") does not "
            "produce a reproducible .gph -- the same command run twice writes the same "
            "serset values in a different order -- so the resolution oracle cannot be "
            "applied and no minimum abbreviation is claimed.  twoway returned _rc==0 for "
            "these prefixes, but which option each one resolved to was NOT verified: " +
            (", ".join(accepted) if accepted else "(none)"))
        continue
    ostr = name if val == "" else name + "(" + val + ")"
    full_cmd = "twoway " + meta["ctxcmd"] + ", " + ostr + " nodraw"

    if ref is None:
        unprobeable[name] = "reference .gph was not produced in context " + ctx
        continue

    degenerate = (basetxt is not None and ref == basetxt)
    minab, probe_cmd, oracle = name, full_cmd, "gph-identity"
    if degenerate:
        oracle = "return-code-only (option leaves no trace in the .gph)"
        for k in sorted(cand_by[name]):
            r = cand_by[name][k]
            if r["rc"] == 0:
                minab = r["pre"]
                pstr = r["pre"] if val == "" else r["pre"] + "(" + val + ")"
                probe_cmd = "twoway " + meta["ctxcmd"] + ", " + pstr + " nodraw"
                break
    else:
        for k in sorted(cand_by[name]):
            r = cand_by[name][k]
            if r["rc"] == 0 and gph(r["path"]) is not None and gph(r["path"]) == ref:
                minab = r["pre"]
                pstr = r["pre"] if val == "" else r["pre"] + "(" + val + ")"
                probe_cmd = "twoway " + meta["ctxcmd"] + ", " + pstr + " nodraw"
                break

    options_out[name] = {
        "min_abbrev": minab,
        "probe_cmd": probe_cmd,
        "full_name_cmd": full_cmd,
        "plottype_context": ctx,
        "probe_value": val if val != "" else None,
        "oracle": oracle,
        "dash": dash_entry(name, len(minab), minab),
    }

for name, d in sorted(direct_rows.items()):
    minab = d["abbrev"] or name
    if name in dashname_rows:
        dn = dashname_rows[name]
        dash = {"accepts": dn["rc"] == 0 and "zqdash" in dn["registry"].split(),
                "rc": dn["rc"],
                "key": "name" if "zqdash" in dn["registry"].split() else None}
    else:
        dash = dash_entry(name, 0, minab)
    options_out[name] = {
        "min_abbrev": minab,
        "probe_cmd": d["cmd"],
        "full_name_cmd": None,
        "plottype_context": "scatter",
        "probe_value": None,
        "oracle": d["oracle"],
        "dash": dash,
    }

for name, d in sorted(noctx.items()):
    unprobeable[name] = ("twoway rejected the full option name in every context tried "
                         "(last _rc=" + d["rc"] + "; probe value " + repr(d["value"]) + ")")
for name, why in SKIP.items():
    unprobeable[name] = why

# --------------------------------------------------------------- plottypes
plottypes_out = {}
for name, meta in sorted(pt_rows.items()):
    if meta["rc"] != 0:
        unprobeable[name + " (plottype)"] = ("twoway rejected the full plottype name with varlist '" +
                                             meta["vars"] + "' (_rc=" + str(meta["rc"]) + ")")
        continue
    ref = gph(meta["ref"])
    if ref is None:
        unprobeable[name + " (plottype)"] = "reference .gph was not produced"
        continue
    minab = name
    cmd = "twoway " + name + " " + meta["vars"] + ", nodraw"
    for k in sorted(ptcand_by[name]):
        r = ptcand_by[name][k]
        if r["rc"] == 0 and gph(r["path"]) is not None and gph(r["path"]) == ref:
            minab = r["pre"]
            cmd = "twoway " + r["pre"] + " " + meta["vars"] + ", nodraw"
            break
    dr = ptdash_by.get(name, {}).get(len(minab))
    if dr is None:
        dash = {"accepts": None, "rc": None, "type": None}
    elif dr["rc"] != 0:
        dash = {"accepts": False, "rc": dr["rc"], "type": None}
    else:
        try:
            dash = {"accepts": True, "rc": 0,
                    "type": json.loads(dr["json"])["plots"][0]["type"]}
        except Exception:
            dash = {"accepts": True, "rc": 0, "type": None,
                    "note": "could not read plot type out of dash spec"}
    plottypes_out[name] = {"min_abbrev": minab, "probe_cmd": cmd,
                           "varlist": meta["vars"], "oracle": "gph-identity",
                           "dash": dash}

# ------------------------------------------------------- abbrev resolution
# What does Stata actually resolve each of dash's hard-coded abbreviations to?
# Derived from the SAME candidate .gph files: abbreviation A resolves to option
# O iff the graph produced by A(value-of-O) is identical to the one produced by
# O(value-of-O).
resolution = {}
mismaps = []
stata_rejects_dash_abbrev = []
unresolved = []
for ab, dash_target in sorted(DASH_TABLE.items()):
    hits, accepted, skipped_unstable = [], [], []
    for cand, meta in sorted(opt_rows.items()):
        if not cand.startswith(ab) or cand == ab:
            continue
        if not ctx_stable.get(meta["ctx"], False):
            skipped_unstable.append(cand)
            continue
        r = cand_by[cand].get(len(ab))
        if r is None or r["rc"] != 0:
            continue
        accepted.append(cand)
        ref = gph(meta["ref"])
        txt = gph(r["path"])
        if ref is not None and txt is not None and txt == ref:
            hits.append(cand)
    for cand, d in sorted(direct_rows.items()):
        if not cand.startswith(ab) or cand == ab:
            continue
        r = directtry_by[cand].get(len(ab))
        if r is None:
            continue
        if r["rc1"] == 0:
            accepted.append(cand)
            if r["rc2"] == 0:
                hits.append(cand)
    exact = [c for c in opt_rows if c == ab]
    stata_target = (exact[0] if exact else (hits[0] if len(hits) == 1 else None))
    resolution[ab] = {
        "dash_maps_to": dash_target,
        "stata_resolves_to": stata_target,
        "stata_accepted_prefix_in_context_of": accepted or None,
        "stata_identity_matches": hits if len(hits) != 1 else None,
    }
    resolution[ab]["candidates_in_non_reproducible_context"] = skipped_unstable or None
    if stata_target is None:
        if skipped_unstable and not accepted:
            unresolved.append(ab)
            resolution[ab]["status"] = (
                "not determined: the only candidate option(s) (" + ", ".join(skipped_unstable) +
                ") live in a twoway context whose .gph is not reproducible, so the oracle "
                "could not be applied")
        elif accepted:
            unresolved.append(ab)
            resolution[ab]["status"] = ("twoway accepted this prefix but the identity oracle "
                                        "matched no option in the probed universe")
        else:
            stata_rejects_dash_abbrev.append(
                ab + ": dash->" + dash_target + ", stata rejects the abbreviation")
            resolution[ab]["status"] = "twoway rejects this abbreviation"
        continue
    if stata_target != dash_target:
        mismaps.append(ab + ": dash->" + dash_target + ", stata->" + stata_target)
        resolution[ab]["status"] = "MIS-MAP"
    else:
        resolution[ab]["status"] = "agrees"

# --------------- abbreviations twoway accepts but dash rejects -------------
# Every option name declared in dash.ado's _dash_parse_graph_opts and
# _dash_parse_plot_opts, so that "dash rejects the minimum abbreviation of an
# option it supports" can be told apart from "dash has no such option".
DASH_DECLARED = set("""
title subtitle note caption name saving xtitle ytitle xlabel ylabel xline yline
legend by xscale yscale aspectratio scheme plotregion graphregion bgcolor
plotbgcolor link filter ytitle2 xtitle2 ylabel2 xlabel2 yscale2 xscale2
mcolor msymbol msize msangle mfcolor mlcolor mlabel mlabcolor mlabsize
mlabposition mlabgap mlabwidth malpha marker lcolor lwidth lpattern lalpha
fcolor fintensity falpha barwidth base blcolor bfcolor jitter jseed yaxis xaxis
colorvar colpalette colordiscrete coloruseplegend colornlevels colorcuts
colormissing bwidth degree pstyle cmissing recast connect
""".split())

dash_rejects = sorted([n for n, e in options_out.items()
                       if e["dash"].get("accepts") is False])
dash_rejects_declared = sorted([n for n in dash_rejects if n in DASH_DECLARED])
dash_rejects_undeclared = sorted([n for n in dash_rejects if n not in DASH_DECLARED])

doc = {
    "_meta": {
        "generated_by": "scripts/extract_abbrev_truth.do",
        "record_file": REC,
        "run_date": meta_rows.get("run_date"),
        "stata_version": meta_rows.get("stata_version"),
        "stata_flavor": meta_rows.get("stata_flavor"),
        "stata_edition": meta_rows.get("stata_edition"),
        "stata_born_date": meta_rows.get("stata_born_date"),
        "dataset": "sysuse auto, clear",
        "context_reproducibility": ctx_stable,
        "oracle_selfcheck": (
            "the same twoway command run twice, more than a second apart, "
            "normalises to identical text: " +
            ("PASS" if (selfchk and gph(selfchk[0]) is not None and
                        gph(selfchk[0]) == gph(selfchk[1])) else "FAIL")
        ),
        "method": (
            "For each option/plottype the shortest prefix P is sought such that "
            "twoway accepts P AND P resolves to the intended option.  The second "
            "half is enforced with a resolution oracle: each probe is saved to a "
            "live-format .gph (a plain-text graph-object script), the echoed "
            "command line and the per-run object ids are normalised away, and the "
            "text is compared with the .gph produced by the full option name.  "
            "Return code alone is NOT sufficient: twoway accepts xl(3000) and "
            "t(ZQSENTINEL), but they resolve to xlabel() and t1title()."
        ),
        "oracle_caveat": (
            "Options whose .gph output is identical to the no-option baseline "
            "cannot use the identity oracle.  Those entries carry "
            "oracle=\"return-code-only ...\" or a dedicated side-effect oracle "
            "(graph-created-under-name, file-written) and are flagged as such."
        ),
        "dash_probe": (
            "Every prefix is also fed to dash as "
            "`dash scatter mpg weight, <prefix>(<value>) name(zqdash)`; the entry "
            "for the measured minimum abbreviation is reported under \"dash\", "
            "with the landing key read back out of ${dash_json_zqdash}."
        ),
        "counts": {
            "options": len(options_out),
            "plottypes": len(plottypes_out),
            "unprobeable": len(unprobeable),
            "dash_mismaps": len(mismaps),
            "dash_rejects_min_abbrev": len(dash_rejects),
            "dash_rejects_min_abbrev_option_declared_by_dash": len(dash_rejects_declared),
            "dash_rejects_min_abbrev_option_not_in_dash": len(dash_rejects_undeclared),
            "stata_rejects_dash_abbrev": len(stata_rejects_dash_abbrev),
            "dash_abbrev_unresolved": len(unresolved),
        },
    },
    "options": options_out,
    "plottypes": plottypes_out,
    "abbrev_resolution": resolution,
    "dash_mismaps": mismaps,
    "dash_abbrev_stata_rejects": stata_rejects_dash_abbrev,
    "dash_abbrev_unresolved": unresolved,
    "dash_rejects_min_abbrev": dash_rejects,
    "dash_rejects_min_abbrev_option_declared_by_dash": dash_rejects_declared,
    "dash_rejects_min_abbrev_option_not_in_dash": dash_rejects_undeclared,
    "unprobeable": unprobeable,
}

with open(OUT, "w") as fh:
    json.dump(doc, fh, indent=2, sort_keys=True)
    fh.write("\n")
print("WROTE " + OUT)
print("options=%d plottypes=%d mismaps=%d rejects=%d unprobeable=%d" %
      (len(options_out), len(plottypes_out), len(mismaps),
       len(dash_rejects), len(unprobeable)))
for m in mismaps:
    print("MISMAP " + m)
end

capture dash clear
display as text "extract_abbrev_truth.do: done"
