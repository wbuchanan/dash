*! extract_kde_hist_fn_truth.do -- WP-31 section 12 (GAPS3 C5): measure
*! what twoway draws for histogram gap() and baroffset(), kdensity area()
*! and boundary, function droplines() and base(), area nodropbase and bar
*! baroffset(): each probe's return code and first error line, plot 1's
*! serset (every variable, every row) and the class values the drawing
*! reads (bar_size, bar_offset, base, droplines, drop_base, the y scale);
*! the generator's r(dropxy); and on which of the forty plot types twoway
*! takes each of the six options (applicability probes).  twoway only:
*! the output is the same before and after dash changes.
*!
*! Output: test/fixtures/kde_hist_fn_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_kde_hist_fn_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zk_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zk_bad' {
    display as error "extract_kde_hist_fn_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zk_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zk_rc' | _rc {
    local _zk_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_kde_hist_fn_truth.do: `_zk_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZK_REPO "`repo'"
global ZK_OUT "${ZK_REPO}/test/fixtures/kde_hist_fn_truth.json"

local work "`c(tmpdir)'dash_kde_hist_fn_probe"
capture mkdir "`work'"
global ZK_WORK "`work'"

if `"`c(python_exec)'"' == "" {
    display as error "extract_kde_hist_fn_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

quietly shell git -C "${ZK_REPO}" rev-parse HEAD > "${ZK_WORK}/git_head.txt"
global ZK_VERSION "`c(stata_version)'"
global ZK_BORN "`c(born_date)'"
global ZK_WHEN "`c(current_date)' `c(current_time)'"
global ZK_KEYS ""

* _zk_probe key twoway-command: run the command on a fresh auto (in 1/5
* where the command says so), record its rc in ZK_RC_<key>, its output
* in <work>/<key>.log and, when it drew, plot 1's serset as a CSV
* <work>/<key>.csv (every variable at %21.0g) and the class values the
* drawing reads in ZK_M_<key>_<member>.  The command always holds a comma.
capture program drop _zk_probe
program define _zk_probe
    gettoken key cmd : 0
    quietly sysuse auto, clear
    serset clear
    capture graph drop _all
    quietly log using "${ZK_WORK}/`key'.log", text replace name(zkp) nomsg
    capture noisily twoway `cmd' nodraw name(g, replace)
    local rc = _rc
    quietly log close zkp
    global ZK_RC_`key' `rc'
    global ZK_KEYS "${ZK_KEYS} `key'"
    foreach m in bar_size bar_offset base droplines {
        global ZK_M_`key'_`m' ""
    }
    global ZK_M_`key'_drop_base ""
    global ZK_M_`key'_ymin ""
    global ZK_M_`key'_ymax ""
    if !`rc' {
        foreach m in bar_size bar_offset base {
            capture local v = `.g.plotregion1.plot1.`m''
            if !_rc global ZK_M_`key'_`m' = strofreal(`v', "%21.0g")
        }
        capture local v `"`.g.plotregion1.plot1.droplines'"'
        if !_rc global ZK_M_`key'_droplines `"`v'"'
        capture local v "`.g.plotregion1.plot1.drop_base.stylename'"
        if !_rc global ZK_M_`key'_drop_base "`v'"
        capture local v = `.g.plotregion1.yscale.curmin'
        if !_rc global ZK_M_`key'_ymin = strofreal(`v', "%21.0g")
        capture local v = `.g.plotregion1.yscale.curmax'
        if !_rc global ZK_M_`key'_ymax = strofreal(`v', "%21.0g")
        local id "`.g.plotregion1.plot1.serset.id'"
        preserve
        quietly serset set `id'
        quietly serset use, clear
        format _all %21.0g
        quietly export delimited using "${ZK_WORK}/`key'.csv", replace
        restore
    }
    display as text "ZK `key': rc `rc'"
end

* histogram gap() and baroffset()
_zk_probe H00 histogram mpg,
_zk_probe H01 histogram mpg, gap(20)
_zk_probe H02 histogram mpg, gap(100)
_zk_probe H03 histogram mpg, gap(-1)
_zk_probe H04 histogram mpg, baroffset(.5)
_zk_probe H05 histogram mpg, gap(20) gap(30)
_zk_probe H06 histogram mpg, baroffset(.5) baroffset(.2)
_zk_probe H07 histogram mpg, gap(99.5)
_zk_probe H08 histogram mpg, gap(20) baroffset(.5)
_zk_probe H09 histogram mpg, gap(20) barwidth(2)
_zk_probe H10 histogram mpg, gap(0)

* kdensity area() and boundary
_zk_probe K00 kdensity mpg,
_zk_probe K01 kdensity mpg, area(74)
_zk_probe K02 kdensity mpg, area(0)
_zk_probe K03 kdensity mpg, boundary
_zk_probe K04 kdensity mpg, boundary range(10 30)
_zk_probe K05 kdensity mpg, boundary bwidth(2)
_zk_probe K06 kdensity mpg, area(-1)
_zk_probe K07 kdensity mpg, area(2) area(3)
_zk_probe K08 kdensity mpg, boundary boundary
_zk_probe K09 kdensity mpg, range(10 30) boundary
_zk_probe K10 kdensity mpg, boundary width(2)
_zk_probe K11 kdensity mpg, area(74) boundary

* function droplines() and base()
_zk_probe F01 function y = x^2, range(-2 2) droplines(-1 1) base(1)
_zk_probe F02 function y = x^2, droplines(5)
_zk_probe F03 function y = x^2, range(1 3) droplines(2)
_zk_probe F04 function y = x^2, base(abc)
_zk_probe F05 function y = x^2, droplines(.5) droplines(.2)
_zk_probe F06 function y = x^2, range(-2 2) droplines(1 -1)
_zk_probe F07 function y = x^2, range(-2 2) droplines(-1 1) horizontal
_zk_probe F08 function y = x, range(0 1) droplines(2)
_zk_probe F09 function y = x^2, range(-2 2) droplines(-1 1)
_zk_probe F10 function y = x^2, range(-2 2) droplines(-1 1) base(1) base(2)

* area nodropbase
_zk_probe A00 area mpg weight,
_zk_probe A01 area mpg weight, nodropbase
_zk_probe A02 area mpg weight, nodropbase nodropbase
_zk_probe A03 area mpg weight, dropbase nodropbase

* bar baroffset()
_zk_probe B00 bar mpg weight in 1/5,
_zk_probe B01 bar mpg weight in 1/5, baroffset(.5)
_zk_probe B02 bar mpg weight in 1/5, baroffset(.5) baroffset(-.5)

* The generator's own (x, f(x)) pairs, as twoway_function_parse reads them.
quietly sysuse auto, clear
tempvar fy fx
quietly twoway__function_gen y = x^2, range(-2 2) x(x) n(300) generate(`fy' `fx') droplines(-1 1)
global ZK_DROPXY `"`r(dropxy)'"'

* Applicability: each option once on each of the forty types.
quietly sysuse auto, clear
local types scatter line connected area bar spike dropline dot tsline tsrline ///
    rarea rbar rspike rcap rline rconnected rcapsym rscatter ///
    pcspike pccapsym pcarrow pcbarrow pcscatter pci pcarrowi scatteri ///
    lfit qfit lfitci qfitci fpfit fpfitci lowess lpoly lpolyci mspline mband ///
    kdensity histogram function
local options gap baroffset area boundary droplines nodropbase
local v_gap "gap(20)"
local v_baroffset "baroffset(.5)"
local v_area "area(2)"
local v_boundary "boundary"
local v_droplines "droplines(.5)"
local v_nodropbase "nodropbase"
global ZK_ATYPES "`types'"
global ZK_AOPTIONS "`options'"
local k 0
foreach o of local options {
    foreach t of local types {
        quietly sysuse auto, clear
        quietly gen yl = mpg - 1
        quietly gen yh = mpg + 1
        quietly gen t = _n
        quietly tsset t
        if inlist("`t'", "scatter", "line", "connected", "area", "bar", "spike", "dropline", "dot") {
            local a "`t' mpg weight"
        }
        else if "`t'" == "tsline" local a "tsline mpg"
        else if "`t'" == "tsrline" local a "tsrline yl yh"
        else if inlist("`t'", "rarea", "rbar", "rspike", "rcap", "rline", "rconnected", "rcapsym", "rscatter") {
            local a "`t' yl yh weight"
        }
        else if inlist("`t'", "pcspike", "pccapsym", "pcarrow", "pcbarrow", "pcscatter") {
            local a "`t' mpg weight trunk turn"
        }
        else if inlist("`t'", "pci", "pcarrowi") local a "`t' 20 2000 30 4000"
        else if "`t'" == "scatteri" local a "scatteri 20 2000"
        else if inlist("`t'", "kdensity", "histogram") local a "`t' mpg"
        else if "`t'" == "function" local a "function y = x"
        else local a "`t' mpg weight"
        local cmd "twoway `a', `v_`o'' nodraw"
        local ++k
        quietly log using "${ZK_WORK}/a`k'.log", replace text name(zka) nomsg
        capture noisily `cmd'
        local rc = _rc
        quietly log close zka
        global ZK_AK_`k' "`o'@`t'"
        global ZK_AC_`k' "`cmd'"
        global ZK_AR_`k' "`rc'"
        capture graph drop Graph
    }
}
global ZK_AN "`k'"

python:
import csv, json, os
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


work = G("ZK_WORK")
_HEAD = ("name:", "log:", "log type:", "opened on:", "closed on:")


def message(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = [ln.strip() for ln in fh.read().splitlines()]
    except OSError:
        return ""
    for ln in lines:
        if not ln or ln.startswith(_HEAD) or set(ln) <= set("-"):
            continue
        if ln.startswith(". "):
            continue
        return ln
    return ""


def num(v):
    v = (v or "").strip()
    if v in ("", "."):
        return None
    try:
        return float(v)
    except ValueError:
        return v


def serset(key):
    path = os.path.join(work, key + ".csv")
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.reader(fh))
    except OSError:
        return None
    if not rows:
        return None
    head, body = rows[0], rows[1:]
    return {h: [num(r[i]) for r in body] for i, h in enumerate(head)}


def rec(key):
    rc = int(G("ZK_RC_" + key))
    r = {"rc": rc,
         "message": message(os.path.join(work, key + ".log")) if rc else ""}
    if rc == 0:
        r["serset"] = serset(key)
        for m in ("bar_size", "bar_offset", "base", "ymin", "ymax"):
            r[m] = num(G("ZK_M_%s_%s" % (key, m)))
        r["droplines"] = G("ZK_M_%s_droplines" % key)
        r["drop_base"] = G("ZK_M_%s_drop_base" % key)
    return r


keys = G("ZK_KEYS").split()
out = {k: rec(k) for k in keys}
out["dropxy"] = G("ZK_DROPXY")
app = {}
for k in range(1, int(G("ZK_AN")) + 1):
    rc = int(G("ZK_AR_%d" % k))
    p = os.path.join(work, "a%d.log" % k)
    app[G("ZK_AK_%d" % k)] = {"cmd": G("ZK_AC_%d" % k), "rc": rc,
                              "message": message(p) if rc else ""}
    try:
        os.remove(p)
    except OSError:
        pass
out["applies"] = {"options": G("ZK_AOPTIONS").split(),
                  "types": G("ZK_ATYPES").split(), "pairs": app}
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZK_VERSION"), "born_date": G("ZK_BORN"),
                "dash_commit": commit, "extracted": G("ZK_WHEN"),
                "source": "scripts/extract_kde_hist_fn_truth.do"}
with open(G("ZK_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
for k in keys:
    for ext in (".log", ".csv"):
        try:
            os.remove(os.path.join(work, k + ext))
        except OSError:
            pass
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZK_OUT"), len(keys), len(app))
end
