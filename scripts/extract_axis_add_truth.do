*! extract_axis_add_truth.do
*! twoway's add sub-option on the axis label options, measured from Stata
*! itself (WP-30 P1.18b, section 52): add after values and after a rule,
*! repeated copies, norescale, the tick options, the second axis, by()
*! panels and a monthly date axis.
*!
*! Output: test/fixtures/axis_add_truth.json
*!
*! Run (Stata only through the slot wrapper, never the GUI):
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_axis_add_truth.do
*!
*! METHOD.  Every probe runs under capture noisily.  For an rc-0 probe one
*! record line per axis (yaxis1, xaxis1, yaxis2; under by() each panel's
*! .Graph.graphs[k].yaxis1) holds .major.dlg_tickpos[i] (the labelled
*! ticks), .majornl.dlg_tickpos[i] (the unlabelled ones),
*! .style.majorstyle.tickstyle.show_labels.istrue and, for yaxis1 and
*! xaxis1, .Graph.plotregion1.{y,x}scale.{curmin,curmax}.  The trailing
*! python: block reads the record file and writes the JSON; it never calls
*! Stata and spells a backtick \x60.

clear all
* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_axis_add_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_axis_add_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1
set graphics off
set more off
set linesize 255
version 19

global ADD_REPO "`repo'"
global ADD_META_VERSION = c(stata_version)
global ADD_META_BORN "`c(born_date)'"
global ADD_META_DATE "`c(current_date)'"
tempfile gh
capture shell cd "`repo'" && git rev-parse HEAD > "`gh'"
global ADD_META_COMMIT ""
capture confirm file "`gh'"
if !_rc {
    tempname fh
    file open `fh' using "`gh'", read text
    file read `fh' line
    file close `fh'
    global ADD_META_COMMIT "`line'"
}

local work "`c(tmpdir)'/dash_add_probe"
capture mkdir "`work'"
global ADD_REC "`work'/add_records.txt"
capture erase "${ADD_REC}"

capture program drop _add_axis
program _add_axis
    version 19
    // _add_axis <id> <name> <object> <scale>: one record of one axis
    args id name o scale
    local dv "``o'.draw_view.istrue'"
    if "`dv'" == "" exit
    local r "A|`id'|`name'"
    foreach set in major majornl {
        local n "``o'.`set'.dlg_tickpos.arrnels'"
        if "`n'" == "" | "`n'" == "." local n 0
        local v ""
        forvalues i = 1/`n' {
            local v "`v' ``o'.`set'.dlg_tickpos[`i']'"
        }
        local r "`r'|`v'"
    }
    local r "`r'|``o'.style.majorstyle.tickstyle.show_labels.istrue'"
    local lo ""
    local hi ""
    if "`scale'" != "" {
        local lo "``scale'.curmin'"
        local hi "``scale'.curmax'"
    }
    local r "`r'|`lo'|`hi'"
    file write addrec `"`r'"' _n
end

capture program drop _add_probe
program _add_probe
    version 19
    // _add_probe <id> <data> `"<command>"'
    args id data cmd
    if "`data'" == "auto" {
        sysuse auto, clear
    }
    else {
        clear
        quietly set obs 60
        quietly generate t = tm(2000m1) + _n - 1
        format t %tm
        quietly tsset t
        quietly generate y = 100 + _n
    }
    capture graph drop _all
    capture noisily `cmd'
    local rc = _rc
    file write addrec `"P|`id'|`rc'|`cmd'"' _n
    if `rc' == 0 {
        local g ".Graph"
        local npan "`.Graph.graphs.arrnels'"
        if strpos(`"`cmd'"', "by(") & "`npan'" != "" & "`npan'" != "." {
            forvalues k = 1/`npan' {
                _add_axis `id' "panel`k'" "`g'.graphs[`k'].yaxis1" ""
            }
        }
        else {
            _add_axis `id' yaxis1 "`g'.yaxis1" "`g'.plotregion1.yscale"
            _add_axis `id' xaxis1 "`g'.xaxis1" "`g'.plotregion1.xscale"
            _add_axis `id' yaxis2 "`g'.yaxis2" ""
        }
    }
    capture graph drop _all
end

local S "twoway scatter mpg weight"
local Y2 "twoway (scatter mpg weight) (scatter price weight, yaxis(2))"
file open addrec using "${ADD_REC}", write text replace
_add_probe base      auto `"`S'"'
_add_probe add25     auto `"`S', ylabel(25, add)"'
_add_probe add5      auto `"`S', ylabel(5, add)"'
_add_probe add50     auto `"`S', ylabel(50, add)"'
_add_probe addto     auto `"`S', ylabel(15 25 to 35, add)"'
_add_probe addslash  auto `"`S', ylabel(15/17, add)"'
_add_probe addmixed  auto `"`S', ylabel(15 "a" 25(10)45, add)"'
_add_probe addlab    auto `"`S', ylabel(25 "x", add)"'
_add_probe rule      auto `"`S', ylabel(15(10)35, add)"'
_add_probe rule50    auto `"`S', ylabel(15(10)35 50, add)"'
_add_probe n2        auto `"`S', ylabel(#2, add)"'
_add_probe n2_25     auto `"`S', ylabel(#2 25, add)"'
_add_probe minmax    auto `"`S', ylabel(minmax, add)"'
_add_probe none      auto `"`S', ylabel(none, add)"'
_add_probe empty     auto `"`S', ylabel(, add)"'
_add_probe m_plain   auto `"`S', ylabel(25) ylabel(35, add)"'
_add_probe m_both    auto `"`S', ylabel(25, add) ylabel(35, add)"'
_add_probe m_second  auto `"`S', ylabel(25, add) ylabel(35)"'
_add_probe m_nolab   auto `"`S', ylabel(25, nolabels) ylabel(35, add)"'
_add_probe a01       auto `"`S', ylabel(25, add) ylabel(, nolabels)"'
_add_probe a02       auto `"`S', ylabel(25, add) ylabel(, labsize(small))"'
_add_probe a03       auto `"`S', ytick(25)"'
_add_probe a04       auto `"`S', ytick(25, add)"'
_add_probe a05       auto `"`S', ylabel(#3 25, add)"'
_add_probe a06       auto `"`S', ylabel(25, add norescale)"'
_add_probe a07       auto `"`S', ylabel(50, add norescale)"'
_add_probe a08       auto `"`S', xlabel(5000, add) xlabel(1500, add)"'
_add_probe nr_rule   auto `"`S', ylabel(0(10)100, norescale)"'
_add_probe nr_list   auto `"`S', ylabel(0 10 20, norescale)"'
_add_probe noticks   auto `"`S', ylabel(, noticks) ylabel(25, add)"'
_add_probe b00       auto `"`Y2'"'
_add_probe b01       auto `"`Y2', ylabel(6000, axis(2) add)"'
_add_probe b02       auto `"`Y2', ylabel(6000, axis(2) add) ylabel(9000, axis(2) add)"'
_add_probe by        auto `"`S', ylabel(25, add) by(foreign)"'
_add_probe by_base   auto `"`S', by(foreign)"'
_add_probe ts_base   ts   `"tsline y"'
_add_probe ts_x492   ts   `"tsline y, xlabel(492, add)"'
_add_probe ts_tlabel ts   `"tsline y, tlabel(2001m1, add)"'
file close addrec

python:
import json, os
from sfi import Macro

REPO = Macro.getGlobal("ADD_REPO")


def _nums(text):
    out = []
    for w in text.split():
        try:
            out.append(float(w))
        except ValueError:
            pass
    return out


def _num(text):
    try:
        return float(text)
    except ValueError:
        return None


probes, order = {}, []
with open(Macro.getGlobal("ADD_REC"), encoding="utf-8",
          errors="replace") as fh:
    for line in fh:
        f = line.rstrip("\n").split("|")
        if f[0] == "P":
            probes[f[1]] = {"cmd": "|".join(f[3:]), "rc": int(f[2])}
            order.append(f[1])
        elif f[0] == "A" and f[1] in probes and len(f) >= 8:
            rec = {"ticks": _nums(f[3]), "unlabelled": _nums(f[4]),
                   "labels_shown": f[5] == "1"}
            lo, hi = _num(f[6]), _num(f[7])
            if lo is not None and hi is not None:
                rec["range"] = [lo, hi]
            probes[f[1]][f[2]] = rec

meta = {"stata_version": Macro.getGlobal("ADD_META_VERSION"),
        "born_date": Macro.getGlobal("ADD_META_BORN"),
        "source": "scripts/extract_axis_add_truth.do",
        "dash_commit": Macro.getGlobal("ADD_META_COMMIT"),
        "extracted": Macro.getGlobal("ADD_META_DATE")}
out = os.path.join(REPO, "test", "fixtures", "axis_add_truth.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump({"_meta": meta, "probes": {k: probes[k] for k in order}}, fh,
              indent=1, sort_keys=False)
    fh.write("\n")
print("axis_add_truth.json: %d probes" % len(order))
end
