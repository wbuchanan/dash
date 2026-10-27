*! extract_dash_only_truth.do -- WP-35 section 35-07 (DT-15): what twoway
*! answers for each spelling dash took and twoway does not (the second-axis
*! spellings ytitle2() .. ttitle2(), malpha(), lalpha(), falpha(),
*! marker(), jseed(), mlg(), cv(), colv(), colornlevels(), colormissing(),
*! plotbgcolor(), pbgc(), colpalette(), hover() and table), for the
*! non-word forms (kernel() with a capital, xsize(()), a string colorvar(),
*! an if keeping no row with colorvar(), title("'90s")), for each word
*! moved into p1() (the p.<word> keys) and for the order in which twoway
*! names a refused word when a command holds two (the order.* keys).
*! For each probe: the return code, the first error line and every log
*! line after the command line.  twoway only: the output is the same
*! before and after dash changes.
*!
*! Output: test/fixtures/dash_only_words_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_dash_only_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200
set graphics off

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zd_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zd_bad' {
    display as error "extract_dash_only_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zd_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zd_rc' | _rc {
    local _zd_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_dash_only_truth.do: `_zd_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZD_REPO "`repo'"
global ZD_OUT "${ZD_REPO}/test/fixtures/dash_only_words_truth.json"

local work "`c(tmpdir)'dash_dash_only_probe"
capture mkdir "`work'"
global ZD_WORK "`work'"

if `"`c(python_exec)'"' == "" {
    display as error "extract_dash_only_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

quietly shell git -C "${ZD_REPO}" rev-parse HEAD > "${ZD_WORK}/git_head.txt"
global ZD_VERSION "`c(stata_version)'"
global ZD_BORN "`c(born_date)'"
global ZD_WHEN "`c(current_date)' `c(current_time)'"
global ZD_N 0

* _zd_probe key twoway-command: run the command on a fresh copy of auto
* and record its rc and its log.
capture program drop _zd_probe
program define _zd_probe
    gettoken key cmd : 0
    global ZD_N = ${ZD_N} + 1
    local k ${ZD_N}
    global ZD_K_`k' "`key'"
    global ZD_C_`k' `"`macval(cmd)'"'
    quietly sysuse auto, clear
    capture graph drop _all
    quietly log using "${ZD_WORK}/p`k'.log", text replace name(zdp) nomsg
    capture noisily twoway `macval(cmd)' name(g, replace)
    local rc = _rc
    quietly log close zdp
    global ZD_RC_`k' `rc'
    capture graph drop _all
    display as text "ZD `key': rc `rc'"
end

* Rows 1-25: the second-axis spellings, then each inside p1()
foreach w in ytitle2 xtitle2 yti2 xti2 ttitle2 {
    _zd_probe `w' scatter mpg weight, `w'(T)
    _zd_probe p.`w' scatter mpg weight, p1(`w'(T))
}
foreach w in ylabel2 xlabel2 yla2 xla2 ytick2 xtick2 ymtick2 ymlabel2 xmtick2 xmlabel2 tlabel2 ttick2 {
    _zd_probe `w' scatter mpg weight, `w'(10 20)
    _zd_probe p.`w' scatter mpg weight, p1(`w'(10 20))
}
foreach w in yline2 xline2 tline2 {
    _zd_probe `w' scatter mpg weight, `w'(20)
    _zd_probe p.`w' scatter mpg weight, p1(`w'(20))
}
foreach w in yscale2 xscale2 ysc2 xsc2 tscale2 {
    _zd_probe `w' scatter mpg weight, `w'(range(0 50))
    _zd_probe p.`w' scatter mpg weight, p1(`w'(range(0 50)))
}

* Rows 26-37, 41: the other synonyms and extensions
_zd_probe marker scatter mpg weight, marker(O)
_zd_probe p.marker scatter mpg weight, p1(marker(O))
_zd_probe malpha scatter mpg weight, malpha(50)
_zd_probe p.malpha scatter mpg weight, p1(malpha(50))
_zd_probe lalpha line mpg weight, lalpha(50)
_zd_probe p.lalpha line mpg weight, p1(lalpha(50))
_zd_probe falpha area mpg weight, falpha(50)
_zd_probe p.falpha area mpg weight, p1(falpha(50))
_zd_probe jseed scatter mpg weight, jitter(5) jseed(3)
_zd_probe p.jseed scatter mpg weight, jitter(5) p1(jseed(3))
_zd_probe mlg scatter mpg weight, mlabel(make) mlg(2)
_zd_probe p.mlg scatter mpg weight, mlabel(make) p1(mlg(2))
_zd_probe cv scatter mpg weight, cv(price)
_zd_probe p.cv scatter mpg weight, p1(cv(price))
_zd_probe colv scatter mpg weight, colv(price)
_zd_probe p.colv scatter mpg weight, p1(colv(price))
_zd_probe colornlevels scatter mpg weight, colorvar(price) colornlevels(4)
_zd_probe p.colornlevels scatter mpg weight, colorvar(price) p1(colornlevels(4))
_zd_probe colormissing scatter mpg weight, colorvar(price) colormissing(gray)
_zd_probe p.colormissing scatter mpg weight, colorvar(price) p1(colormissing(gray))
_zd_probe plotbgcolor scatter mpg weight, plotbgcolor(red)
_zd_probe p.plotbgcolor scatter mpg weight, p1(plotbgcolor(red))
_zd_probe pbgc scatter mpg weight, pbgc(red)
_zd_probe p.pbgc scatter mpg weight, p1(pbgc(red))
_zd_probe colpalette scatter mpg weight, colorvar(price) colpalette(viridis)
_zd_probe p.colpalette scatter mpg weight, colorvar(price) p1(colpalette(viridis))

* Rows 39-40: the kept words
_zd_probe hover scatter mpg weight, hover(make)
_zd_probe table scatter mpg weight, table

* V1-V5: the non-word forms
_zd_probe V1 kdensity mpg, kernel(GAUSSIAN)
_zd_probe V2 scatter mpg weight, xsize(())
_zd_probe V3 scatter mpg weight, colorvar(make)
_zd_probe V4 scatter mpg weight if price < 0, colorvar(price)
_zd_probe V5 scatter mpg weight, title("'90s")

* The order in which twoway names a refused word
_zd_probe order.unknown_first scatter mpg weight, bogus ytitle2(T)
_zd_probe order.word_first scatter mpg weight, ytitle2(T) bogus
_zd_probe order.group_then_comma (scatter mpg weight, bogus), ytitle2(T)
_zd_probe order.p_own_first scatter mpg weight, p1(malpha(50)) bogus
_zd_probe order.p_own_word scatter mpg weight, p1(malpha(50)) ytitle2(T)
_zd_probe order.p_before_comma (scatter mpg weight), bogus p1(malpha(50))
_zd_probe order.p_after_groups (scatter mpg weight) (scatter price weight, bogus), p1(malpha(50))
_zd_probe order.p_plot_order (scatter mpg weight) (scatter price weight), p2(jseed(3)) p1(malpha(50))
_zd_probe order.p_list scatter mpg weight, p1(malpha(50) mcolor(red) jseed(3))
_zd_probe order.p_own_then_graph (scatter mpg weight, p1(jseed(3))) (scatter price weight), p1(malpha(50))

* How twoway's p# line writes the blanks of a refused token: a run of
* blanks inside its parentheses, and a blank inside quotes
_zd_probe space.run scatter mpg weight, p1(ytitle2(a   b)   mlg( 2 ))
_zd_probe space.quote scatter mpg weight, p1(ytitle2("a b" c))

python:
import json, os
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


work = G("ZD_WORK")


def lines(key_k):
    """Every line the command printed, in order."""
    try:
        with open(os.path.join(work, "p%d.log" % key_k), encoding="utf-8",
                  errors="replace") as fh:
            text = fh.read()
    except OSError:
        return []
    # A program's commands are not echoed: the log holds the command's
    # output alone.
    return [ln.rstrip() for ln in text.replace("\n> ", "").splitlines()
            if ln.strip() and not ln.startswith(". ")]


out = {}
for k in range(1, int(G("ZD_N")) + 1):
    key = G("ZD_K_%d" % k)
    rc = int(G("ZD_RC_%d" % k))
    notes = lines(k)
    out[key] = {"cmd": "twoway " + G("ZD_C_%d" % k).strip(), "rc": rc,
                "message": (notes[0].strip() if notes else "") if rc else "",
                "notes": notes}
    try:
        os.remove(os.path.join(work, "p%d.log" % k))
    except OSError:
        pass
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZD_VERSION"), "born_date": G("ZD_BORN"),
                "dash_commit": commit, "extracted": G("ZD_WHEN"),
                "source": "scripts/extract_dash_only_truth.do"}
with open(G("ZD_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZD_OUT"), len(out) - 1, "probes")
end
