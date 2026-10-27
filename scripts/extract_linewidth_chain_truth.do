*! extract_linewidth_chain_truth.do -- WP-31 S60 (GAPS3 K3): measure the
*! width of each plot's line, area outline and marker outline under ten
*! schemes written here, read from twoway's own class values
*! (.Graph.plotregion1.plot<k>.style.line.width.setting,
*! .style.area.linestyle.width.setting and
*! .style.marker.linestyle.width.setting), so the chain linewidth
*! p#<kind> -> p<kind> -> p# -> p that dash follows is proved against live
*! twoway; and the ten linewidth names' units, read from lwidth(<name>).
*! twoway only: the output is the same before and after dash changes.
*!
*! Output: test/fixtures/linewidth_chain_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_linewidth_chain_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zc_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zc_bad' {
    display as error "extract_linewidth_chain_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zc_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zc_rc' | _rc {
    local _zc_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_linewidth_chain_truth.do: `_zc_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZC_REPO "`repo'"
global ZC_OUT "${ZC_REPO}/test/fixtures/linewidth_chain_truth.json"

adopath ++ "${ZC_REPO}"
quietly do "${ZC_REPO}/dash_parse.mata"
quietly do "${ZC_REPO}/dash.ado"
global dash_nobrowser 1

local work "`c(tmpdir)'dash_linewidth_chain_probe"
capture mkdir "`work'"
global ZC_WORK "`work'"


quietly shell git -C "${ZC_REPO}" rev-parse HEAD > "${ZC_WORK}/git_head.txt"
global ZC_VERSION "`c(stata_version)'"
global ZC_BORN "`c(born_date)'"
global ZC_WHEN "`c(current_date)' `c(current_time)'"

* The ten schemes (session only: files in the probe directory, which
* joins the adopath; no `set scheme, permanently').
global ZC_S_lwt0 "#include s2color"
global ZC_S_lwt1 "#include s2color|linewidth p1 vthick|linewidth p2 thick"
global ZC_S_lwt2 "#include s2color|linewidth p1 vthick|linewidth p2 thick|linewidth p3 vvthick|linewidth p4 vvvthick"
global ZC_S_lwt3 "#include s2color|linewidth p1line vthick"
global ZC_S_lwt4 "#include s2color|linewidth p1lineplot vthick|linewidth p1area thick|linewidth p1arrow vvthick|linewidth p1other vvvthick"
global ZC_S_lwt5 "#include s2color|linewidth p vthick"
global ZC_S_lwt6 "#include s1manual|linewidth p1 vthick"
global ZC_S_lwt7 "#include economist|linewidth p1 vthick"
global ZC_S_lwt8 "#include s2color|linewidth p1 vthick|linewidth pline thick|linewidth plineplot vvthick"
global ZC_S_lwt9 "#include s2color|linewidth plineplot vvthick|linewidth p1arrowline vthick|linewidth p1bar thick|linewidth parea medthick"
forvalues i = 0/9 {
    tempname fh
    file open `fh' using "${ZC_WORK}/scheme-lwt`i'.scheme", write text replace
    local rest "${ZC_S_lwt`i'}"
    while `"`rest'"' != "" {
        gettoken line rest : rest, parse("|")
        if `"`line'"' != "|" file write `fh' `"`line'"' _n
    }
    file close `fh'
}
adopath ++ "${ZC_WORK}"

* The commands each scheme draws.
global ZC_L32 "area bar connected dropline fpfit fpfitci function histogram kdensity lfit lfitci line lowess lpoly lpolyci mspline pcarrow pcarrowi pcbarrow pccapsym pcspike qfit qfitci rarea rbar rcap rcapsym rconnected rline rspike scatter spike"
global ZC_L14 "area bar connected dropline lfit_lfitci lfitci lfitci_lfit line pcarrow rarea rcap scatter_lfitci scatterc spike"
global ZC_L34 "area bar connected dropline fpfit fpfitci function histogram kdensity lfit lfitci line lowess lpoly lpolyci mband mspline pcarrow pcbarrow pccapsym pcscatter pcspike qfit qfitci rarea rbar rcap rcapsym rconnected rline rscatter rspike scatter spike"
global ZC_C_lwt0 "L32"
global ZC_C_lwt1 "L32"
forvalues i = 2/8 {
    global ZC_C_lwt`i' "L14"
}
global ZC_C_lwt9 "L34"

* _zc_rec key n: plots 1..n of the current graph into global
* ZC_R_<key>_<k> as "line area_line marker_line".
capture program drop _zc_rec
program define _zc_rec
    args key n
    forvalues k = 1/`n' {
        local a "`.Graph.plotregion1.plot`k'.style.line.width.setting'"
        local b "`.Graph.plotregion1.plot`k'.style.area.linestyle.width.setting'"
        local c "`.Graph.plotregion1.plot`k'.style.marker.linestyle.width.setting'"
        foreach v in a b c {
            if "``v''" == "" local `v' "."
        }
        global ZC_R_`key'_`k' "`a' `b' `c'"
        display as text "ZC `key' `k': `a' `b' `c'"
    }
    global ZC_N_`key' "`n'"
end

sysuse auto, clear
generate p2 = price * 0.8
generate lo = price - 1000
generate hi = price + 1000
generate w2 = weight + 100

forvalues i = 0/9 {
    set scheme lwt`i'
    local list "${ZC_C_lwt`i'}"
    foreach t of global ZC_`list' {
        local n 2
        if inlist("`t'", "lfitci", "qfitci", "lpolyci", "fpfitci") {
            local cmd "`t' price weight || `t' p2 weight"
            local n 4
        }
        else if "`t'" == "lfit_lfitci" {
            local cmd "lfit price weight || lfitci p2 weight"
            local n 3
        }
        else if "`t'" == "lfitci_lfit" {
            local cmd "lfitci price weight || lfit p2 weight"
            local n 3
        }
        else if "`t'" == "scatter_lfitci" {
            local cmd "scatter price weight || lfitci p2 weight"
            local n 3
        }
        else if "`t'" == "scatterc" {
            local cmd "scatter price weight, connect(l) || scatter p2 weight, connect(l)"
        }
        else if inlist("`t'", "histogram", "kdensity") {
            local cmd "`t' price || `t' p2"
        }
        else if "`t'" == "function" {
            local cmd "function y = x, range(0 1) || function y = 2*x, range(0 1)"
        }
        else if "`t'" == "pcarrowi" {
            local cmd "pcarrowi 1 1 2 2 || pcarrowi 2 2 3 3"
        }
        else if inlist("`t'", "rarea", "rbar", "rcap", "rcapsym", "rconnected", "rline", "rspike", "rscatter") {
            local cmd "`t' lo hi weight || `t' lo p2 weight"
        }
        else if inlist("`t'", "pcarrow", "pcbarrow", "pccapsym", "pcspike", "pcscatter") {
            local cmd "`t' lo weight hi w2 || `t' lo weight p2 w2"
        }
        else {
            local cmd "`t' price weight || `t' p2 weight"
        }
        quietly twoway `cmd'
        _zc_rec lwt`i'_`t' `n'
        graph drop _all
    }
}

* The units: each name's width as twoway reads lwidth(<name>).
set scheme s2color
global ZC_UNITS "vvthin vthin thin medthin medium medthick thick vthick vvthick vvvthick"
foreach u of global ZC_UNITS {
    quietly twoway line price weight, lwidth(`u')
    global ZC_U_`u' "`.Graph.plotregion1.plot1.style.line.width.setting'"
    display as text "ZC unit `u': ${ZC_U_`u'}"
    graph drop _all
}

python:
import json, os
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


def num(w):
    return None if w == "." else float(w)


cases, schemes = {}, {}
for i in range(10):
    s = "lwt%d" % i
    schemes[s] = "".join(l + "\n" for l in G("ZC_S_" + s).split("|"))
    cases[s] = {}
    for t in G("ZC_" + G("ZC_C_" + s)).split():
        key = "%s_%s" % (s, t)
        plots = {}
        for k in range(1, int(G("ZC_N_" + key)) + 1):
            a, b, c = G("ZC_R_%s_%d" % (key, k)).split()
            plots[str(k)] = {"line": num(a), "area_line": num(b),
                             "marker_line": num(c)}
        cases[s][t] = plots
units = {u: float(G("ZC_U_" + u)) for u in G("ZC_UNITS").split()}
out = {"cases": cases, "schemes": schemes, "units": units,
       "_about": ("Each scheme is a file in the probe directory; each "
                  "command is 'twoway <cmd> price weight || <cmd> p2 "
                  "weight' (range plots '<cmd> lo hi weight', pc plots "
                  "'<cmd> lo weight hi w2', ci fits draw two plots each) on "
                  "sysuse auto; the values are Stata linewidth units read "
                  "from '.Graph.plotregion1.plot<k>.style.line.width"
                  ".setting' (line), '.style.area.linestyle.width.setting' "
                  "(area_line) and '.style.marker.linestyle.width.setting' "
                  "(marker_line); units are each name's lwidth(<name>) "
                  "width.")}
work = G("ZC_WORK")
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZC_VERSION"), "born_date": G("ZC_BORN"),
                "dash_commit": commit, "extracted": G("ZC_WHEN"),
                "source": "scripts/extract_linewidth_chain_truth.do"}
with open(G("ZC_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
for f in ["git_head.txt"] + ["scheme-lwt%d.scheme" % i for i in range(10)]:
    try:
        os.remove(os.path.join(work, f))
    except OSError:
        pass
print("wrote", G("ZC_OUT"))
end
