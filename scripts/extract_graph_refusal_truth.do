*! extract_graph_refusal_truth.do -- WP-35 section 35-06: what twoway
*! answers to the graph-wide combinations dash took (two omit options in
*! one plot, aspectratio() with xoverhangs or yoverhangs, maxaxes(),
*! fxsiz()/fysiz(), a title with notitling, factor-variable notation in
*! by()/colorvar()/mlabel()) and contour's leniency under levels()
*! (syn:SD-22): its return code and printed lines, and for the fxsize()
*! spellings the plot region it draws (sentinel outline colours, as in
*! extract_sizing_truth.do).  twoway only: the output is the same before
*! and after dash changes.
*!
*! Output: test/fixtures/graph_refusal_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_graph_refusal_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zg_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zg_bad' {
    display as error "extract_graph_refusal_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zg_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zg_rc' | _rc {
    local _zg_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_graph_refusal_truth.do: `_zg_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZG_REPO "`repo'"
global ZG_OUT "${ZG_REPO}/test/fixtures/graph_refusal_truth.json"

local work "`c(tmpdir)'dash_graph_refusal_probe"
capture mkdir "`work'"
global ZG_WORK "`work'"

if `"`c(python_exec)'"' == "" {
    display as error "extract_graph_refusal_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

quietly shell git -C "${ZG_REPO}" rev-parse HEAD > "${ZG_WORK}/git_head.txt"
global ZG_VERSION "`c(stata_version)'"
global ZG_BORN "`c(born_date)'"
global ZG_WHEN "`c(current_date)' `c(current_time)'"

* _zg_run key cmd: run `cmd' with its printed lines in a log; probe n's
* key, command and rc in ZG_KEY_<n>, ZG_CMD_<n> and ZG_RC_<n>; the graph
* exported to p<n>.svg when it drew one named zg1.
capture program drop _zg_run
program define _zg_run
    gettoken key 0 : 0
    global ZG_N = ${ZG_N} + 1
    local n ${ZG_N}
    global ZG_KEY_`n' "`key'"
    global ZG_CMD_`n' `"`macval(0)'"'
    quietly log using "${ZG_WORK}/p`n'.log", text replace name(zgref)
    capture noisily `0'
    local rc = _rc
    display as text "{p_end}"
    quietly log close zgref
    global ZG_RC_`n' "`rc'"
    if `rc' == 0 {
        capture graph describe zg1
        if _rc == 0 {
            quietly graph export "${ZG_WORK}/p`n'.svg", replace
        }
    }
    capture graph drop _all
end
global ZG_N 0

sysuse auto, clear
set scheme s2color
local nm "name(zg1, replace)"
local sc "twoway scatter mpg weight"

* basic:PT-8 (syn:SD-10): two omit options in one plot.  The six pairs of
* the four words, full and at twoway's minimum (omitanym, omitallm,
* omitdup, omitn), drawn; one pair nodraw; three words; one word twice;
* across two lists; after the comma of the groups.
local w1 omitanymiss
local w2 omitallmiss
local w3 omitdupmiss
local w4 omitnothing
local m1 omitanym
local m2 omitallm
local m3 omitdup
local m4 omitn
forvalues i = 1/3 {
    forvalues j = `=`i'+1'/4 {
        _zg_run omit.`w`i''_`w`j'' `sc', `w`i'' `w`j'' `nm'
        _zg_run omit.min_`m`i''_`m`j'' `sc', `m`i'' `m`j'' `nm'
    }
}
_zg_run omit.alone `sc', omitanymiss `nm'
_zg_run omit.nodraw `sc', omitanymiss omitdupmiss nodraw
_zg_run omit.three `sc', omitanymiss omitallmiss omitdupmiss `nm'
_zg_run omit.twice `sc', omitanymiss omitanymiss `nm'
_zg_run omit.mixed `sc', omitanym omitallmiss `nm'
_zg_run omit.between `sc', omitanymiss msymbol(O) omitallmiss `nm'
_zg_run omit.two_lists twoway (scatter mpg weight, omitanymiss) (line mpg weight, omitallmiss), `nm'
_zg_run omit.after_comma twoway (scatter mpg weight), omitanymiss omitallmiss `nm'
_zg_run omit.bars twoway scatter mpg weight || line mpg weight, omitanymiss omitallmiss `nm'
_zg_run omit.line twoway line mpg weight, omitanymiss omitallmiss `nm'
_zg_run omit.reversed `sc', omitallmiss omitanymiss `nm'
_zg_run omit.two_lists_same twoway (scatter mpg weight, omitanymiss) (line mpg weight, omitanymiss), `nm'
_zg_run omit.two_lists_reversed twoway (scatter mpg weight, omitallmiss) (line mpg weight, omitanymiss), `nm'
_zg_run omit.list_and_comma twoway (scatter mpg weight, omitanymiss), omitallmiss `nm'
_zg_run omit.lfit twoway lfit mpg weight, omitanymiss omitallmiss `nm'
_zg_run omit.histogram twoway histogram mpg, omitanymiss omitallmiss `nm'
_zg_run omit.lfit_scatter twoway (lfit mpg weight, omitanymiss) (scatter mpg weight, omitallmiss), `nm'
_zg_run omit.scatter_lfit twoway (scatter mpg weight, omitallmiss) (lfit mpg weight, omitanymiss), `nm'
_zg_run omit.bars_two_lists twoway scatter mpg weight, omitanymiss || line mpg weight, omitallmiss `nm'

* GW-2: aspectratio() with xoverhangs or yoverhangs.
_zg_run asp.comma `sc', aspectratio(1) xoverhangs `nm'
_zg_run asp.yoverhangs `sc', aspectratio(1) yoverhangs `nm'
_zg_run asp.group twoway (scatter mpg weight, aspectratio(1) xoverhangs), `nm'
_zg_run asp.split_groups twoway (scatter mpg weight, aspectratio(1)) (line mpg weight, xoverhangs), `nm'
_zg_run asp.bars twoway scatter mpg weight, aspectratio(1) || line mpg weight, xoverhangs `nm'
_zg_run asp.by `sc', by(foreign) aspectratio(1) xoverhangs `nm'
_zg_run asp.alone_x `sc', xoverhangs `nm'
_zg_run asp.alone_a `sc', aspectratio(1) `nm'
_zg_run asp.abbrev `sc', aspect(1) xoverhangs `nm'

* GW-3: maxaxes().
_zg_run maxaxes.x `sc', maxaxes(x) `nm'
_zg_run maxaxes.2_5 `sc', maxaxes(2.5) `nm'
_zg_run maxaxes.1_y2 twoway (scatter mpg weight) (scatter price weight, yaxis(2)), maxaxes(1) `nm'
_zg_run maxaxes.1_x2 twoway (scatter mpg weight) (scatter mpg price, xaxis(2)), maxaxes(1) `nm'
_zg_run maxaxes.1_y12 twoway (scatter mpg weight, yaxis(1 2)), maxaxes(1) `nm'
_zg_run maxaxes.2_y3 twoway (scatter mpg weight) (scatter price weight, yaxis(3)), maxaxes(2) `nm'
_zg_run maxaxes.2_y2 twoway (scatter mpg weight) (scatter price weight, yaxis(2)), maxaxes(2) `nm'
_zg_run maxaxes.1_y2_one `sc', yaxis(2) maxaxes(1) `nm'
_zg_run maxaxes.1_y1 `sc', maxaxes(1) `nm'
_zg_run maxaxes.9 `sc', maxaxes(9) `nm'
_zg_run maxaxes.10 `sc', maxaxes(10) `nm'
_zg_run maxaxes.0 `sc', maxaxes(0) `nm'
_zg_run maxaxes.neg `sc', maxaxes(-1) `nm'
_zg_run maxaxes.0_y1 twoway (scatter mpg weight, yaxis(1)), maxaxes(0) `nm'
_zg_run maxaxes.in_group twoway (scatter mpg weight, maxaxes(x)) (line mpg weight), `nm'
_zg_run maxaxes.group_1_y2 twoway (scatter mpg weight, maxaxes(1)) (scatter price weight, yaxis(2)), `nm'
_zg_run maxaxes.1_y2x2 twoway (scatter mpg weight, yaxis(2) xaxis(2)), maxaxes(1) `nm'
_zg_run maxaxes.1_x2y2 twoway (scatter price weight, xaxis(2)) (scatter mpg weight, yaxis(2)), maxaxes(1) `nm'
_zg_run maxaxes.1_y2_then_x2 twoway (scatter mpg weight, yaxis(2)) (scatter price weight, xaxis(2)), maxaxes(1) `nm'
_zg_run maxaxes.y10 `sc', yaxis(10) `nm'
_zg_run maxaxes.1_ytitle2 `sc', ytitle(T, axis(2)) maxaxes(1) `nm'
foreach a in maxa maxax maxaxe maxaxes {
    _zg_run maxaxes.spell_`a' `sc', `a'(1) `nm'
}

* GW-4: fxsize() and fysize() spellings; the plot region drawn.
local sn `"plotregion(lcolor("1 2 3")) graphregion(lcolor("4 5 6"))"'
_zg_run fx.base `sc', `sn' `nm'
foreach a in fxsize fxsiz fxsi fxs {
    _zg_run fx.`a' `sc', `a'(50) `sn' `nm'
}
foreach a in fysize fysiz fysi {
    _zg_run fx.`a' `sc', `a'(50) `sn' `nm'
}

* sil:SD-8: a title with notitling.
foreach k in title subtitle note caption {
    _zg_run notitling.`k' `sc', `k'("T") notitling `nm'
}
_zg_run notitling.two_strings `sc', title("A" "B") notitling `nm'
_zg_run notitling.alone `sc', notitling `nm'
_zg_run notitling.note_title `sc', note("N") title("T") notitling `nm'
_zg_run notitling.title_note `sc', title("T") note("N") notitling `nm'
_zg_run notitling.title_subtitle `sc', title("T") subtitle("S") notitling `nm'
_zg_run notitling.subtitle_title `sc', subtitle("S") title("T") notitling `nm'
_zg_run notitling.caption_note `sc', caption("C") note("N") notitling `nm'
_zg_run notitling.note_caption `sc', note("N") caption("C") notitling `nm'
_zg_run notitling.subtitle_note `sc', subtitle("S") note("N") notitling `nm'
_zg_run notitling.title_caption `sc', title("T") caption("C") notitling `nm'
_zg_run notitling.caption_subtitle `sc', caption("C") subtitle("S") notitling `nm'
_zg_run notitling.in_group twoway (scatter mpg weight, title("T") notitling), `nm'
_zg_run notitling.first `sc', notitling title("T") `nm'
_zg_run notitling.title_opts `sc', title("T", size(small)) notitling `nm'
_zg_run notitling.bare `sc', title(T x) notitling `nm'
_zg_run notitling.spell_notitl `sc', title("T") notitl `nm'

* syn:SD-8: factor-variable notation in by(), colorvar() and mlabel().
_zg_run fv.by_i_foreign `sc', by(i.foreign) `nm'
_zg_run fv.by_c_foreign `sc', by(c.foreign) `nm'
_zg_run fv.by_foreign_i_rep78 `sc', by(foreign i.rep78) `nm'
_zg_run fv.by_foreign_hash_rep78 `sc', by(foreign#rep78) `nm'
_zg_run fv.by_foreign_hh_rep78 `sc', by(foreign##rep78) `nm'
_zg_run fv.by_ib1_foreign `sc', by(ib1.foreign) `nm'
_zg_run fv.by_1_foreign `sc', by(1.foreign) `nm'
_zg_run fv.by_o_foreign `sc', by(o.foreign) `nm'
_zg_run fv.by_L_foreign `sc', by(L.foreign) `nm'
_zg_run fv.colorvar_c_price `sc', colorvar(c.price) `nm'
_zg_run fv.colorvar_i_foreign `sc', colorvar(i.foreign) `nm'
_zg_run fv.colorvar_price_hash_foreign `sc', colorvar(price#foreign) `nm'
_zg_run fv.mlabel_c_make `sc', mlabel(c.make) `nm'
_zg_run fv.mlabel_i_foreign `sc', mlabel(i.foreign) `nm'
_zg_run fv.mlabel_45 `sc', mlabel(45) `nm'
_zg_run fv.mlabel_fmt `sc', mlabel(%9.1f) `nm'
_zg_run fv.mlabel_hash `sc', mlabel(make#foreign) `nm'

* syn:SD-22 (D54): contour with levels() takes an option it does not know.
gen gx = mod(_n - 1, 9) + 1 if _n <= 72
gen gy = floor((_n - 1) / 9) + 1 if _n <= 72
gen gz = gx * gy + gy
* basic:PT-8: the pair alone on each of the forty-four types
* (extract_noted_option_truth.do's commands).
gen yl = mpg - 1
gen yh = mpg + 1
gen t = _n
tsset t
foreach t in scatter line connected area bar spike dropline dot tsline tsrline ///
    rarea rbar rspike rcap rline rconnected rcapsym rscatter rpcap rpspike ///
    contour contourline pcspike pccapsym pcarrow pcbarrow pcscatter pci ///
    pcarrowi scatteri lfit qfit lfitci qfitci fpfit fpfitci lowess lpoly ///
    lpolyci mspline mband kdensity histogram function {
    if inlist("`t'", "scatter", "line", "connected", "area", "bar", "spike", "dropline", "dot") local a "`t' mpg weight,"
    else if "`t'" == "tsline" local a "tsline mpg,"
    else if "`t'" == "tsrline" local a "tsrline yl yh,"
    else if inlist("`t'", "rarea", "rbar", "rspike", "rcap", "rline", "rconnected", "rcapsym", "rscatter") local a "`t' yl yh weight,"
    else if inlist("`t'", "rpcap", "rpspike") local a "`t' yl yh mpg weight,"
    else if inlist("`t'", "contour", "contourline") local a "`t' gz gy gx,"
    else if inlist("`t'", "pcspike", "pccapsym", "pcarrow", "pcbarrow", "pcscatter") local a "`t' mpg weight trunk turn,"
    else if inlist("`t'", "pci", "pcarrowi") local a "`t' 20 2000 30 4000,"
    else if "`t'" == "scatteri" local a "scatteri 20 2000,"
    else if inlist("`t'", "kdensity", "histogram") local a "`t' mpg,"
    else if "`t'" == "function" local a "function y = x, range(0 1)"
    else local a "`t' mpg weight,"
    _zg_run omit.type_`t' twoway `a' omitanymiss omitallmiss `nm'
}
_zg_run contour.levels_bogus twoway contour gz gy gx, levels(10) bogus(1) `nm'
_zg_run contour.bogus twoway contour gz gy gx, bogus(1) `nm'
_zg_run contour.levels_region twoway contour gz gy gx, levels(10) region(fcolor(red)) `nm'
_zg_run contourline.levels_bogus twoway contourline gz gy gx, levels(10) bogus(1) `nm'
_zg_run contourline.bogus twoway contourline gz gy gx, bogus(1) `nm'

python:
import json, os, sys
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


sys.path.insert(0, os.path.join(G("ZG_REPO"), "scripts"))
import svg_chrome  # noqa: E402

work = G("ZG_WORK")


def log_lines(n):
    p = os.path.join(work, "p%d.log" % n)
    with open(p, encoding="utf-8", errors="replace") as fh:
        lines = [ln.rstrip() for ln in fh
                 if ln.strip() and not ln.lstrip().startswith((".", "> "))
                 and "log:" not in ln and "log type:" not in ln
                 and "opened on:" not in ln and "closed on:" not in ln
                 and "name:" not in ln and not ln.startswith("---")
                 and ln.strip() != "{p_end}"]
    os.remove(p)
    return lines


def box(r):
    if not r:
        return None
    return {k: round(r[k], 3) for k in ("left", "top", "right", "bottom")}


out = {}
for n in range(1, int(G("ZG_N")) + 1):
    key = G("ZG_KEY_%d" % n)
    rc = int(G("ZG_RC_%d" % n))
    lines = log_lines(n)
    rec = {"cmd": G("ZG_CMD_%d" % n), "rc": rc, "lines": lines,
           "first": lines[0] if (rc and lines) else ""}
    svg = os.path.join(work, "p%d.svg" % n)
    if os.path.exists(svg):
        if key.startswith("fx."):
            rec["plot"] = box(svg_chrome.svg_region(svg, "#010203"))
            rec["graph"] = box(svg_chrome.svg_region(svg, "#040506"))
        os.remove(svg)
    out[key] = rec
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZG_VERSION"), "born_date": G("ZG_BORN"),
                "dash_commit": commit, "extracted": G("ZG_WHEN"),
                "source": "scripts/extract_graph_refusal_truth.do"}
with open(G("ZG_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZG_OUT"), len(out) - 1, "probes")
end
