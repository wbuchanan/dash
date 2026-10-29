*! extract_zero_obs_truth.do -- WP-37 section 37-01 (DG-1): what twoway
*! answers when a plot has no observation, for test/fixtures/
*! zero_obs_truth.json.
*!
*! WHY THIS EXISTS
*!
*! dash's zero-observation check (_dash_zero_obs_check, the rule table
*! _dash_zero_obs_rule in dash_parse.mata) copies twoway's answer per plot
*! type and case.  This script asks twoway (StataNow, scheme stcolor) the
*! 400 probes of the research's zero-observation table: 48 data types (40
*! types and the eight horizontal variants) in eight cases, and function,
*! scatteri, pci and pcarrowi in four.  The cases:
*!   a   T V if 0
*!   b1  (T V if 0) (scatter mpg weight)
*!   b2  (scatter mpg weight) (T V if 0)
*!   c   T V || scatter mpg weight || if 0     (a graph-wide if)
*!   d   T V in 1 if foreign                    (in and if select nothing)
*!   f   T with its y variable all missing (ymiss for mpg)
*!   e1  T with ydom for mpg, by(foreign)      (one panel holds no row)
*!   e2  T V if 0, by(foreign)                 (every panel empty)
*! The literal types take a, b1, c and e2 only.  For each probe: the
*! return code and every message line; for contour and contourline probes
*! that draw, the texts of the SVG twoway exports.  twoway only: the
*! output does not depend on dash.
*!
*! Output: test/fixtures/zero_obs_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> sh <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_zero_obs_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200
set graphics off
global dash_nobrowser 1

* Root: DASH_REPO, else the current directory when it is a dash tree;
* never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zz_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zz_bad' {
    display as error "extract_zero_obs_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zz_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zz_rc' | _rc {
    local _zz_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_zero_obs_truth.do: `_zz_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZZ_REPO "`repo'"
global ZZ_OUT "${ZZ_REPO}/test/fixtures/zero_obs_truth.json"

local work "`c(tmpdir)'dash_zero_obs_probe"
capture mkdir "`work'"
global ZZ_WORK "`work'"

set scheme stcolor

quietly shell git -C "${ZZ_REPO}" rev-parse HEAD > "${ZZ_WORK}/git_head.txt"
global ZZ_VERSION "`c(stata_version)'"
global ZZ_BORN "`c(born_date)'"
global ZZ_WHEN "`c(current_date)' `c(current_time)'"
global ZZ_N 0

* The data every probe reads.
quietly sysuse auto, clear
quietly gen t = _n
quietly tsset t
quietly gen ymiss = .
quietly gen ydom = mpg if !foreign
tempfile zzdata
quietly save "`zzdata'"
global ZZ_DATA "`zzdata'"

* _zz_probe key svg twoway-command: run the command on a fresh copy of the
* data, record its rc and its log, and, when svg is 1 and it draws, its SVG.
capture program drop _zz_probe
program define _zz_probe
    gettoken key 0 : 0
    gettoken svg cmd : 0
    global ZZ_N = ${ZZ_N} + 1
    local k ${ZZ_N}
    global ZZ_K_`k' "`key'"
    global ZZ_C_`k' `"`cmd'"'
    quietly use "${ZZ_DATA}", clear
    capture graph drop _all
    capture erase "${ZZ_WORK}/p`k'.svg"
    quietly log using "${ZZ_WORK}/p`k'.log", text replace name(zzp) nomsg
    capture noisily twoway `cmd'
    local rc = _rc
    quietly log close zzp
    global ZZ_RC_`k' `rc'
    if !`rc' & `svg' {
        capture graph export "${ZZ_WORK}/p`k'.svg", replace as(svg)
    }
    capture graph drop _all
    display as text "ZZ `key': rc `rc'"
end

* The 40 data types and their variables; the eight horizontal variants.
local types scatter line connected area bar spike dropline dot lowess ///
    rarea rbar rspike rcap rcapsym rscatter rline rconnected rpcap rpspike ///
    pcspike pccapsym pcarrow pcbarrow pcscatter tsline tsrline kdensity ///
    histogram contour contourline lfit qfit lfitci qfitci fpfit fpfitci ///
    lpoly lpolyci mband mspline
local hz bar area spike dropline rbar rarea rcap histogram
local rng rarea rbar rspike rcap rcapsym rscatter rline rconnected
local rp rpcap rpspike
local pc pcspike pccapsym pcarrow pcbarrow pcscatter
local uni kdensity histogram
local cont contour contourline

local keys ""
foreach T of local types {
    local keys `keys' `T'
}
foreach T of local hz {
    local keys `keys' `T'_h
}
foreach key of local keys {
    local T = subinstr("`key'", "_h", "", 1)
    local h ""
    if "`key'" != "`T'" local h "horizontal"
    local V "mpg weight"
    if `: list T in rng' local V "mpg turn weight"
    if `: list T in rp' local V "mpg turn trunk weight"
    if `: list T in pc' local V "mpg weight turn length"
    if "`T'" == "tsline" local V "mpg"
    if "`T'" == "tsrline" local V "mpg turn"
    if `: list T in uni' local V "mpg"
    if `: list T in cont' local V "mpg weight length"
    local Vf = subinstr("`V'", "mpg", "ymiss", 1)
    local Ve = subinstr("`V'", "mpg", "ydom", 1)
    local svg = `: list T in cont'
    local o ""
    if "`h'" != "" local o ", `h'"
    local ob ", by(foreign)"
    if "`h'" != "" local ob ", `h' by(foreign)"
    _zz_probe `key'.a `svg' `T' `V' if 0`o'
    _zz_probe `key'.b1 `svg' (`T' `V' if 0`o') (scatter mpg weight)
    _zz_probe `key'.b2 `svg' (scatter mpg weight) (`T' `V' if 0`o')
    _zz_probe `key'.c `svg' `T' `V'`o' || scatter mpg weight || if 0
    _zz_probe `key'.d `svg' `T' `V' in 1 if foreign`o'
    _zz_probe `key'.f `svg' `T' `Vf'`o'
    _zz_probe `key'.e1 `svg' `T' `Ve'`ob'
    _zz_probe `key'.e2 `svg' `T' `V' if 0`ob'
}
* The literal types: if 0 does not reach their values.
foreach L in function scatteri pci pcarrowi {
    local V "1 2 3 4"
    local o ""
    local ob ", by(foreign)"
    if "`L'" == "function" {
        local V "y = x"
        local o ", range(0 1)"
        local ob ", range(0 1) by(foreign)"
    }
    _zz_probe `L'.a 0 `L' `V' if 0`o'
    _zz_probe `L'.b1 0 (`L' `V' if 0`o') (scatter mpg weight)
    _zz_probe `L'.c 0 `L' `V'`o' || scatter mpg weight || if 0
    _zz_probe `L'.e2 0 `L' `V' if 0`ob'
}

python:
import json, os, re
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


work = G("ZZ_WORK")


def lines(k):
    """Every line the command printed, in order (commands are not echoed:
    the log is opened inside a program)."""
    try:
        with open(os.path.join(work, "p%d.log" % k), encoding="utf-8",
                  errors="replace") as fh:
            text = fh.read()
    except OSError:
        return []
    return [ln.rstrip() for ln in text.replace("\n> ", "").splitlines()
            if ln.strip() and not ln.startswith(". ")]


def svg_texts(k):
    try:
        with open(os.path.join(work, "p%d.svg" % k), encoding="utf-8",
                  errors="replace") as fh:
            text = fh.read()
    except OSError:
        return None
    return [t.strip() for t in re.findall(r"<text[^>]*>([^<]*)</text>", text)
            if t.strip()]


out = {}
for k in range(1, int(G("ZZ_N")) + 1):
    key = G("ZZ_K_%d" % k)
    r = {"cmd": G("ZZ_C_%d" % k).strip(), "rc": int(G("ZZ_RC_%d" % k)),
         "lines": lines(k)}
    t = svg_texts(k)
    if t is not None:
        r["svg_texts"] = t
    out[key] = r
    for ext in (".log", ".svg"):
        try:
            os.remove(os.path.join(work, "p%d%s" % (k, ext)))
        except OSError:
            pass
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZZ_VERSION"), "born_date": G("ZZ_BORN"),
                "dash_commit": commit, "extracted": G("ZZ_WHEN"),
                "source": "scripts/extract_zero_obs_truth.do"}
with open(G("ZZ_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZZ_OUT"), len(out) - 1, "probes")
end
