*! extract_axis_misc_truth.do
*! WP-44 section 44-05 (MS-12, DG-9): ground truth for a lone second axis's
*! gridlines and for the words twoway takes or refuses in an axis label or
*! tick list, for test/fixtures/axis_misc_truth.json.
*!
*! WHY THIS EXISTS
*!
*! dash drew a graph whose every layer is on yaxis(2) with the first axis's
*! gridlines, and drew a label list holding a bare word or .a with a note
*! where twoway refuses it.  This script records what twoway draws and
*! prints for each, so the tests compare with twoway and never with a guess.
*!
*! Output: test/fixtures/axis_misc_truth.json
*!
*! Run with:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_axis_misc_truth.do
*!
*! METHOD
*!
*! `_am_run key scheme data cmd' (globals named with the key's dot as an
*! underscore) loads data (auto or sp500), sets the
*! session scheme (never permanently), runs cmd under a text log and
*! exports the drawn graph to SVG.  The trailing python: block reads files
*! only (never calls Stata; a backtick is spelled \x60): each key's rc, its
*! log lines, and the SVG's lines and plot region through
*! scripts/svg_truth.py.  Keys: ms12.* (MS-12, the lone axis's gridlines)
*! and dg9.* (DG-9, label-list words; an accept_* key is a candidate form,
*! drawn or refused as its rc says).  Key names differ by more than case:
*! the work directory may be on a case-blind file system.
*! ---------------------------------------------------------------------------

clear all
set graphics off
set more off
set linesize 255
version 19

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_am_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_am_bad' {
    display as error "extract_axis_misc_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _am_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_am_rc' | _rc {
    local _am_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_axis_misc_truth.do: `_am_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global AM_REPO "`repo'"
global AM_OUT "${AM_REPO}/test/fixtures/axis_misc_truth.json"

local work "`c(tmpdir)'dash_axis_misc_probe"
capture mkdir "`work'"
global AM_WORK "`work'"

quietly shell git -C "${AM_REPO}" rev-parse HEAD > "${AM_WORK}/git_head.txt"
global AM_VERSION "`c(stata_version)'"
global AM_BORN "`c(born_date)'"
global AM_WHEN "`c(current_date)' `c(current_time)'"

capture program drop _am_run
program define _am_run
    args key scheme data cmd
    local g = subinstr("`key'", ".", "_", .)
    sysuse `data', clear
    set scheme `scheme'
    capture graph drop u44k
    capture log close amr
    quietly log using "${AM_WORK}/r_`g'.log", text replace name(amr)
    capture noisily `macval(cmd)'
    local rc = _rc
    quietly log close amr
    global AM_R_`g' "`rc'"
    global AM_C_`g' `"`macval(cmd)'"'
    global AM_S_`g' "`scheme'"
    global AM_KEYS "${AM_KEYS} `key'"
    if !`rc' {
        quietly graph export "${AM_WORK}/`g'.svg", replace
    }
end

global AM_KEYS ""
local S "twoway scatter mpg weight"
local N "name(u44k, replace)"

* MS-12: a lone second axis's gridlines.
_am_run ms12.control s2color auto `"`S', `N'"'
_am_run ms12.y2 s2color auto `"`S', yaxis(2) `N'"'
_am_run ms12.pci_y2 s2color auto `"twoway pci 20 3000 30 4000, yaxis(2) `N'"'
_am_run ms12.y2_grid s2color auto `"`S', yaxis(2) ylabel(, grid axis(2)) `N'"'
_am_run ms12.y3 s2color auto `"`S', yaxis(3) `N'"'
_am_run ms12.x2 s2color auto `"`S', xaxis(2) `N'"'
_am_run ms12.y2_s2color s2color auto `"`S', yaxis(2) `N'"'
_am_run ms12.y2_stcolor stcolor auto `"`S', yaxis(2) `N'"'
_am_run ms12.control_stcolor stcolor auto `"`S', `N'"'
_am_run ms12.x2_stcolor stcolor auto `"`S', xaxis(2) `N'"'
_am_run ms12.y2_y3 s2color auto `"twoway (scatter mpg weight, yaxis(2)) (scatter price weight, yaxis(3)), `N'"'
_am_run ms12.swap s2color auto `"twoway (scatter price weight, yaxis(2)) (scatter mpg weight), `N'"'

* DG-9: words in a label or tick list.
_am_run dg9.T11 s2color auto `"twoway scatter mpg rep78, xlabel(1/5 .a, valuelabel) `N'"'
foreach o in xlabel ylabel xtick ytick xmlabel ymlabel xmtick ymtick {
    _am_run dg9.abc_`o' s2color auto `"`S', `o'(abc) `N'"'
}
_am_run dg9.mid_word s2color auto `"`S', ylabel(10 abc 20) `N'"'
_am_run dg9.fn_word s2color auto `"`S', ylabel(abc(1)) `N'"'
_am_run dg9.dot_a s2color auto `"`S', ylabel(10 .a 20) `N'"'
_am_run dg9.word_label s2color auto `"`S', ylabel(10 abc "x") `N'"'
_am_run dg9.rule_word s2color auto `"`S', ylabel(10(10)40 abc) `N'"'
_am_run dg9.count_word s2color auto `"`S', ylabel(#3 abc) `N'"'
_am_run dg9.y2_abc s2color auto `"`S', yaxis(1 2) ylabel(abc, axis(2)) `N'"'
_am_run dg9.ymlabel_y2_abc s2color auto `"`S', yaxis(1 2) ymlabel(abc, axis(2)) `N'"'
_am_run dg9.accept_dot s2color auto `"`S', ylabel(10 . 30) `N'"'
_am_run dg9.accept_neg s2color auto `"`S', ylabel(-5 10) `N'"'
_am_run dg9.accept_exp s2color auto `"`S', xlabel(1e3 3000) `N'"'
_am_run dg9.accept_plus s2color auto `"`S', ylabel(+2 20) `N'"'
_am_run dg9.accept_paren s2color auto `"`S', ylabel(5 10(10)40) `N'"'
_am_run dg9.accept_bracket s2color auto `"`S', ylabel(5 10[10]40) `N'"'
_am_run dg9.accept_range s2color auto `"`S', ylabel(10/12 20) `N'"'
_am_run dg9.accept_negrange s2color auto `"`S', ylabel(-1/1 20) `N'"'
_am_run dg9.accept_label s2color auto `"`S', ylabel(10 "a" 20 "b") `N'"'
_am_run dg9.accept_lead_dot s2color auto `"`S', ylabel(.5 20) `N'"'
_am_run dg9.accept_neg_dot s2color auto `"`S', ylabel(-.5 20) `N'"'
_am_run dg9.rule_label s2color auto `"`S', ylabel(10(10)40 "a") `N'"'
_am_run dg9.desc_rule_word s2color auto `"`S', ylabel(40(-10)10 abc) `N'"'
_am_run dg9.missing_dot_word s2color auto `"`S', ylabel(. abc) `N'"'
_am_run dg9.unfinished_range s2color auto `"`S', ylabel(10/ 20) `N'"'
_am_run dg9.to_open s2color auto `"`S', ylabel(10 "a" to 40) `N'"'
_am_run dg9.accept_lead_dot_rule s2color auto `"`S', ylabel(. 10 20) `N'"'
_am_run dg9.accept_to s2color auto `"`S', ylabel(10 20 to 40) `N'"'
_am_run dg9.accept_colon s2color auto `"`S', ylabel(10 20 : 40) `N'"'
_am_run dg9.accept_spaced_rule s2color auto `"`S', ylabel(10 (10) 40) `N'"'
_am_run dg9.accept_desc_rule s2color auto `"`S', ylabel(40(-10)10) `N'"'
_am_run dg9.accept_rule_tail s2color auto `"`S', ylabel(10(10)30 35) `N'"'
_am_run dg9.accept_label_tail s2color auto `"`S', ylabel(10 "a" 20/30) `N'"'
local L "twoway line close date"
_am_run dg9.accept_td s2color sp500 `"`L', xlabel(td(1jan2001) td(1jul2001)) `N'"'
_am_run dg9.accept_tc s2color sp500 `"`L', xlabel(tc(1jan2001 00:00:00)) `N'"'
_am_run dg9.accept_tc_big s2color sp500 `"`L', xlabel(tC(1jan2001 00:00:00)) `N'"'
_am_run dg9.accept_tw s2color sp500 `"`L', xlabel(tw(2001w10)) `N'"'
_am_run dg9.accept_tm s2color sp500 `"`L', xlabel(tm(2001m6)) `N'"'
_am_run dg9.accept_tq s2color sp500 `"`L', xlabel(tq(2001q2)) `N'"'
_am_run dg9.accept_th s2color sp500 `"`L', xlabel(th(2001h2)) `N'"'
_am_run dg9.accept_ty s2color sp500 `"`L', xlabel(ty(2001)) `N'"'
_am_run dg9.accept_td_y s2color auto `"`S', ylabel(td(1jan1960)) `N'"'
_am_run dg9.fn_d s2color sp500 `"`L', xlabel(d(1jan2001)) `N'"'
_am_run dg9.fn_ts s2color sp500 `"`L', xlabel(ts(1jan2001)) `N'"'
_am_run dg9.fn_upper s2color sp500 `"`L', xlabel(TD(1jan2001)) `N'"'
_am_run dg9.tlabel_abc s2color sp500 `"`L', tlabel(abc) `N'"'

python:
import json, os, sys
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


sys.path.insert(0, os.path.join(G("AM_REPO"), "scripts"))
import svg_truth

work = G("AM_WORK")


def logged(key):
    with open(os.path.join(work, "r_" + key.replace(".", "_") + ".log"), encoding="utf-8") as fh:
        lines = [ln.rstrip() for ln in fh]
    keep = [" ".join(ln.split()) for ln in lines
            if ln.strip() and not ln.startswith(".")
            and not ln.startswith(">")
            and not ln.lstrip().startswith(("name:", "log:", "log type:",
                                             "opened on:", "closed on:"))
            and not set(ln.strip()) <= set("-")]
    raw = [ln for ln in lines if "invalid label specifier" in ln]
    return keep, raw


def svg(key):
    doc = svg_truth.svg_document(os.path.join(work, key.replace(".", "_") + ".svg"))
    keep_l = ("x1", "y1", "x2", "y2", "stroke", "width", "dasharray")
    return {
        "hlines": [{k: d[k] for k in keep_l} for d in doc["hlines"]],
        "vlines": [{k: d[k] for k in keep_l} for d in doc["vlines"]],
        "plotregion": doc["plotregion"],
    }


out = {}
for key in G("AM_KEYS").split():
    g = key.replace(".", "_")
    rc = int(G("AM_R_" + g))
    log, raw = logged(key)
    row = {"rc": rc, "log": log, "command": G("AM_C_" + g),
           "scheme": G("AM_S_" + g)}
    if raw:
        # The refusal line as twoway writes it, blanks kept.
        row["raw_message"] = raw[0]
    if rc == 0:
        row.update(svg(key))
    out[key] = row
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("AM_VERSION"), "born_date": G("AM_BORN"),
                "dash_commit": commit, "extracted": G("AM_WHEN"),
                "source": "scripts/extract_axis_misc_truth.do"}
with open(G("AM_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
for key in G("AM_KEYS").split():
    p = os.path.join(work, key.replace(".", "_") + ".svg")
    if os.path.exists(p):
        os.remove(p)
print("wrote", G("AM_OUT"))
end
