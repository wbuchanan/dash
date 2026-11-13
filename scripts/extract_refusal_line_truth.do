*! extract_refusal_line_truth.do -- WP-49 (section 49-01, plot:PT-7 and
*! plot:PT-6): the lines twoway and dash print when each refuses a command.
*!
*! For each probe: the command (asked as "twoway <command>" and as
*! "dash <command>"), twoway's rc and every line it prints, and dash's rc
*! and every line it prints, read from a text log of a `capture noisily'
*! run.  Keys:
*!   pt7.typed.<site>  an option spelled short at each refusal site that
*!                     printed the table's name (option bands() for ba())
*!   pt7.kept.<name>   refusals whose first line was already twoway's: the
*!                     lines dash adds after it are kept (PD-11)
*!   sd12.<name>       first lines dash wrote in its own words
*!   pt6.<type>        tsline and tsrline without tsset
*!   pt8.<name>        a weight glued to the type, and one after the varlist
*!   dg10.<name>       tline() on a business-calendar (%tb) axis
*!
*! Output: test/fixtures/refusal_line_truth.json
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_refusal_line_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 255
set graphics off

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_rl_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_rl_bad' {
    display as error "extract_refusal_line_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _rl_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_rl_rc' | _rc {
    local _rl_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_refusal_line_truth.do: `_rl_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global RL_REPO "`repo'"
global RL_OUT "${RL_REPO}/test/fixtures/refusal_line_truth.json"

adopath ++ "${RL_REPO}"
quietly do "${RL_REPO}/dash_parse.mata"
quietly do "${RL_REPO}/dash.ado"
global dash_nobrowser 1

local work "`c(tmpdir)'dash_refusal_line_probe"
capture mkdir "`work'"
global RL_WORK "`work'"
adopath + "`work'"

quietly shell git -C "${RL_REPO}" rev-parse HEAD > "${RL_WORK}/git_head.txt"
global RL_VERSION "`c(stata_version)'"
global RL_BORN "`c(born_date)'"
global RL_WHEN "`c(current_date)' `c(current_time)'"

* The business calendar of the dg10 probes (as test_wp31_truth.cscript
* makes one): sp500's trading days.
sysuse sp500, clear
quietly bcal create "${RL_WORK}/u49", from(date) replace

* key ~ data ~ command.  Data: a = auto with yl, yh (no tsset);
* b = sp500 with tb, a %tbu49 date.
local k 0
foreach p in ///
    "pt7.typed.applies_function~a~function y = x, ba(3)" ///
    "pt7.typed.applies_dropline~a~dropline mpg weight, ba(3)" ///
    "pt7.typed.applies_degree~a~scatter mpg weight, deg(2)" ///
    "pt7.typed.applies_n~a~scatter mpg weight, n(5)" ///
    "pt7.typed.applies_kernel~a~scatter mpg weight, ker(gaussian)" ///
    "pt7.typed.lpoly_degree~a~lpoly mpg weight, deg(abc)" ///
    "pt7.typed.lpoly_n~a~lpoly mpg weight, n(2.5)" ///
    "pt7.typed.onevalue~a~rbar yl yh weight, barw(1 2)" ///
    "pt7.typed.atobs~a~scatter mpg weight, ato" ///
    "pt7.typed.nofit~a~scatter mpg weight, nof" ///
    "pt7.typed.fitplot~a~scatter mpg weight, fitp(line)" ///
    "pt7.typed.pcycle~a~scatter mpg weight, pcyc(abc)" ///
    "pt7.typed.seriesid~a~scatter mpg weight || scatter mpg turn || scatter mpg trunk, pcyc(0)" ///
    "pt7.typed.contour_ccuts~a~scatter mpg weight, ccut(1 2)" ///
    "pt7.typed.contour_minmax~a~scatter mpg weight, minm" ///
    "pt7.typed.horizontal~a~scatter mpg weight, hor" ///
    "pt7.typed.flag~a~scatter mpg weight, disc" ///
    "pt7.typed.baroffset~a~scatter mpg weight, baro(1)" ///
    "pt7.typed.boundary~a~scatter mpg weight, bound" ///
    "pt7.typed.mwidth~a~scatter mpg weight, mwid" ///
    "pt7.typed.noweight~a~scatter mpg weight, nowe" ///
    "pt7.typed.fxsize~a~scatter mpg weight, fxs(abc)" ///
    "pt7.typed.maxaxes~a~scatter mpg weight, maxa(abc)" ///
    "pt7.typed.gunique~a~(scatter mpg weight, xsiz(3)) (line mpg weight, xsiz(4))" ///
    "pt7.typed.gunique_mixed~a~(scatter mpg weight, xsize(3)) (line mpg weight, xsiz(4))" ///
    "pt7.kept.ytitle2~a~scatter mpg weight, ytitle2(Y)" ///
    "pt7.kept.unknown~a~scatter mpg weight, titel(x)" ///
    "pt7.kept.repeat~a~lfit mpg weight, atobs atobs" ///
    "pt7.kept.plottype~a~scatterx mpg weight" ///
    "sd12.E08~a~[aw=price] scatter mpg weight" ///
    "sd12.Q14~a~(scatter mpg weight" ///
    "sd12.by_nosuch~a~scatter mpg weight, by(nosuch)" ///
    "sd12.mlabel_nosuch~a~scatter mpg weight, mlabel(nosuch)" ///
    "sd12.colorvar_nosuch~a~scatter mpg weight, colorvar(nosuch)" ///
    "sd12.bar_word~a~scatter mpg weight | line mpg weight" ///
    "sd12.legloc~a~scatter mpg weight, legloc(6)" ///
    "sd12.legloc_by~a~scatter mpg weight, by(foreign, legloc(6))" ///
    "sd12.legloc_word~a~scatter mpg weight, legloc(abc)" ///
    "sd12.legloc_abbrev~a~scatter mpg weight, legl(6)" ///
    "sd12.legloc_graph~a~(scatter mpg weight), legloc(6)" ///
    "sd12.useplotregion~a~scatter mpg weight, useplotregion(1)" ///
    "sd12.useplotregion_word~a~scatter mpg weight, useplotregion(abc)" ///
    "sd12.useplotregion_abbrev~a~scatter mpg weight, useplot(1)" ///
    "sd12.useplotregion_graph~a~(scatter mpg weight), useplotregion(1)" ///
    "pt6.tsline~a~tsline mpg" ///
    "pt6.tsrline~a~tsrline yl yh" ///
    "pt8.scatter~a~scatter[aw=price] mpg weight" ///
    "pt8.hist~a~hist[fw=rep78] mpg" ///
    "pt8.after~a~scatter mpg weight [aw=price]" ///
    "dg10.tb~b~scatter close tb, tline(10nov2001)" ///
    "dg10.tb_number~b~scatter close tb, tline(100)" {
    local ++k
    mata: _rl_p = tokens(st_local("p"), "~"); st_global("RL_KEY_`k'", _rl_p[1]); st_local("d", _rl_p[3]); st_global("RL_CMD_`k'", _rl_p[5])
    local cmd `"${RL_CMD_`k'}"'
    foreach who in twoway dash {
        if "`d'" == "b" {
            quietly sysuse sp500, clear
            quietly generate tb = bofd("u49", date)
            format tb %tbu49
        }
        else {
            quietly sysuse auto, clear
            quietly generate yl = mpg - 1
            quietly generate yh = mpg + 1
        }
        capture graph drop _all
        quietly log using "${RL_WORK}/`who'`k'.log", replace text name(rl)
        capture noisily `who' `cmd'
        local rc = _rc
        quietly log close rl
        global RL_`who'_RC_`k' "`rc'"
        capture graph drop _all
        capture dash clear
    }
}
global RL_K "`k'"

python:
import json
import os
from sfi import Macro


def G(name):
    return Macro.getGlobal(name)


def lines(path):
    """Every line a run printed: the log's command echo (". " and its "> "
    continuation lines) and blank lines aside."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return []
    out = []
    echo = False
    for ln in text.splitlines():
        s = ln.rstrip()
        if s.startswith(". "):
            echo = True
            continue
        if echo and s.startswith("> "):
            continue
        echo = False
        if s.strip():
            out.append(s.strip())
    return out


work = G("RL_WORK")
probes = {}
for k in range(1, int(G("RL_K")) + 1):
    row = {"command": G("RL_CMD_%d" % k)}
    for who in ("twoway", "dash"):
        path = os.path.join(work, "%s%d.log" % (who, k))
        row[who + "_rc"] = int(G("RL_%s_RC_%d" % (who, k)))
        # A drawn graph's lines (the page's path) are not kept.
        row[who + "_lines"] = lines(path) if row[who + "_rc"] else []
        try:
            os.remove(path)
        except OSError:
            pass
    probes[G("RL_KEY_%d" % k)] = row
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out = {"_meta": {"stata_version": G("RL_VERSION"), "born_date": G("RL_BORN"),
                 "dash_commit": commit, "extracted": G("RL_WHEN"),
                 "source": "scripts/extract_refusal_line_truth.do"},
       "probes": probes}
with open(G("RL_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
for f in ("git_head.txt", "u49.stbcal"):
    try:
        os.remove(os.path.join(work, f))
    except OSError:
        pass
print("wrote", G("RL_OUT"), len(probes), "probes")
end
