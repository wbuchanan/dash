*! extract_applicability_truth.do -- WP-31 section 04 (C3): measure which
*! plot types twoway accepts each of fourteen value options on.  Every probe
*! is `twoway <type> ..., <opt>(<value>) nodraw' under capture noisily with
*! its own log, and the return code and the first message line are
*! recorded per pair.  twoway only: the output is the same before and after
*! dash changes.
*!
*! Output: test/fixtures/applicability_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_applicability_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_za_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_za_bad' {
    display as error "extract_applicability_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _za_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_za_rc' | _rc {
    local _za_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_applicability_truth.do: `_za_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZA_REPO "`repo'"
global ZA_OUT "${ZA_REPO}/test/fixtures/applicability_truth.json"

global dash_nobrowser 1

local work "`c(tmpdir)'dash_applicability_probe"
capture mkdir "`work'"
global ZA_WORK "`work'"

if `"`c(python_exec)'"' == "" {
    display as error "extract_applicability_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

quietly shell git -C "${ZA_REPO}" rev-parse HEAD > "${ZA_WORK}/git_head.txt"
global ZA_VERSION "`c(stata_version)'"
global ZA_BORN "`c(born_date)'"
global ZA_WHEN "`c(current_date)' `c(current_time)'"

sysuse auto, clear
gen yl = mpg - 1
gen yh = mpg + 1
gen t = _n
tsset t

* The forty-two types (the dash.ado "Supported:" set) and their commands;
* rpcap and rpspike since WP-31 B1.
local types scatter line connected area bar spike dropline dot tsline tsrline ///
    rarea rbar rspike rcap rline rconnected rcapsym rscatter rpcap rpspike ///
    pcspike pccapsym pcarrow pcbarrow pcscatter pci pcarrowi scatteri ///
    lfit qfit lfitci qfitci fpfit fpfitci lowess lpoly lpolyci mspline mband ///
    kdensity histogram function
local options kernel n level bwidth bands range base degree bin width start barwidth ndots dotextend
local v_kernel "gaussian"
local v_n "50"
local v_level "90"
local v_bwidth ".5"
local v_bands "5"
local v_range "1 10"
local v_base "0"
local v_degree "1"
local v_bin "5"
local v_width "1"
local v_start "0"
local v_barwidth ".5"
* WP-31 B5b: twoway dot's own two (dot_truth.json D11d, D11l).
local v_ndots "10"
local v_dotextend "no"

global ZA_TYPES "`types'"
global ZA_OPTIONS "`options'"
local k 0
foreach o of local options {
    foreach t of local types {
        if inlist("`t'", "scatter", "line", "connected", "area", "bar", "spike", "dropline", "dot") {
            local a "`t' mpg weight"
        }
        else if "`t'" == "tsline" local a "tsline mpg"
        else if "`t'" == "tsrline" local a "tsrline yl yh"
        else if inlist("`t'", "rarea", "rbar", "rspike", "rcap", "rline", "rconnected", "rcapsym", "rscatter") {
            local a "`t' yl yh weight"
        }
        else if inlist("`t'", "rpcap", "rpspike") {
            local a "`t' yl yh mpg weight"
        }
        else if inlist("`t'", "pcspike", "pccapsym", "pcarrow", "pcbarrow", "pcscatter") {
            local a "`t' mpg weight trunk turn"
        }
        else if inlist("`t'", "pci", "pcarrowi") local a "`t' 20 2000 30 4000"
        else if "`t'" == "scatteri" local a "scatteri 20 2000"
        else if inlist("`t'", "kdensity", "histogram") local a "`t' mpg"
        else if "`t'" == "function" local a "function y = x"
        else local a "`t' mpg weight"
        local cmd "twoway `a', `o'(`v_`o'') nodraw"
        local ++k
        quietly log using "${ZA_WORK}/p`k'.log", replace text name(za)
        capture noisily `cmd'
        local rc = _rc
        quietly log close za
        global ZA_K_`k' "`o'@`t'"
        global ZA_C_`k' "`cmd'"
        global ZA_R_`k' "`rc'"
        capture graph drop Graph
    }
}
global ZA_N "`k'"
display as text "probes: `k'"

python:
import json, os
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


SKIP = ("name:", "log:", "log type:", "opened on:", "closed on:")


def message(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = [ln.rstrip() for ln in fh]
    except OSError:
        return ""
    body = []
    for ln in lines:
        s = ln.strip()
        if not s or set(s) <= set("-") or s.startswith(SKIP):
            continue
        if s.startswith(". "):
            continue
        body.append(s)
    for s in body:
        if s.startswith("option "):
            return s
    return body[0] if body else ""


work = G("ZA_WORK")
pairs = {}
for k in range(1, int(G("ZA_N")) + 1):
    rc = int(G("ZA_R_%d" % k))
    msg = message(os.path.join(work, "p%d.log" % k)) if rc else ""
    pairs[G("ZA_K_%d" % k)] = {"cmd": G("ZA_C_%d" % k), "rc": rc,
                               "message": msg}
    try:
        os.remove(os.path.join(work, "p%d.log" % k))
    except OSError:
        pass
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out = {"_meta": {"stata_version": G("ZA_VERSION"), "born_date": G("ZA_BORN"),
                 "dash_commit": commit, "extracted": G("ZA_WHEN"),
                 "source": "scripts/extract_applicability_truth.do"},
       "options": G("ZA_OPTIONS").split(), "types": G("ZA_TYPES").split(),
       "pairs": pairs}
with open(G("ZA_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZA_OUT"), len(pairs))
end
