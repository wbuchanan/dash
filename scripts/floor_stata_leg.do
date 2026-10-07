*! floor_stata_leg.do -- the Stata leg of the Python floor matrix (WP-30 P1.33)
*!
*! Run it through the slot wrapper, from the venv directory, so that the log
*! is <work>/floor_stata_leg.log:
*!
*!   PIP_NO_INDEX=1 DASH_REPO=<repo> DASH_FLOOR_WORK=<work> <repo>/scripts/stata_slot.sh <work> <repo>/scripts/floor_stata_leg.do
*!
*! <work> holds gatevenv, a venv scripts/floor_matrix.sh made.  The session
*! runs scripts/release_gate_venv.do's venvuse phase: it links Stata to
*! gatevenv/bin/python for this session only, runs dash_setup, venv() on it,
*! builds a saved page and serves /health, one "GATE " line per result.
*! This file starts no Python itself, so that link is the session's first
*! Python act.
*!
*! Environment: DASH_REPO (the tree under test, else the current directory
*! when it is a dash tree), DASH_FLOOR_WORK (required), DASH_FLOOR_MODE (dev,
*! the default, or plus) and DASH_FLOOR_ADO (default <repo>/).  A value
*! holding a double quote, backquote, dollar sign or control character is
*! refused, r(198).

version 19
clear all
set more off
* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "floor_stata_leg.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"floor_stata_leg.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}

local _fl_work : environment DASH_FLOOR_WORK
local _fl_mode : environment DASH_FLOOR_MODE
local _fl_ado : environment DASH_FLOOR_ADO
foreach v in work mode ado {
    mata: st_local("_fl_bad", strofreal(any(strpos(st_local("_fl_`v'"), (char(34), char(36), char(96)))) | any(ascii(st_local("_fl_`v'")) :< 32)))
    if `_fl_bad' {
        local _fl_name = strupper("`v'")
        display as error "floor_stata_leg.do: DASH_FLOOR_`_fl_name' holds a quote, backquote, dollar sign or control character"
        exit 198
    }
}
if `"`macval(_fl_work)'"' == "" {
    display as error "floor_stata_leg.do: set DASH_FLOOR_WORK to the directory that holds gatevenv"
    exit 198
}
if `"`macval(_fl_mode)'"' == "" local _fl_mode "dev"
if !inlist(`"`_fl_mode'"', "dev", "plus") {
    display as error "floor_stata_leg.do: DASH_FLOOR_MODE must be dev or plus"
    exit 198
}
if `"`macval(_fl_ado)'"' == "" local _fl_ado `"`repo'/"'

adopath ++ "`repo'/"
global dash_nobrowser 1
do "`repo'/scripts/release_gate_venv.do" "`_fl_work'" "`_fl_ado'" `_fl_mode' venvuse
