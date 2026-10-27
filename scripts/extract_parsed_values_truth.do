*! extract_parsed_values_truth.do -- WP-31 section 06 (GAPS3 C10b, C18,
*! F4): measure the values twoway accepts that dash refused for want of
*! parsing -- lpoly degree() above 3 (r(bwidth) of the lpoly command for
*! each degree and kernel), an mlabel() element naming several
*! variables, a scatteri or pci coordinate p/q, and yaxis()/xaxis() lists -- with
*! each probe's return code, first error line, serset and, for the axis
*! lists, the plot regions, plots, axes and legend keys twoway builds.
*! twoway only: the output is the same before and after dash changes.
*!
*! Output: test/fixtures/parsed_values_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_parsed_values_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zp_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zp_bad' {
    display as error "extract_parsed_values_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zp_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zp_rc' | _rc {
    local _zp_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_parsed_values_truth.do: `_zp_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZP_REPO "`repo'"
global ZP_OUT "${ZP_REPO}/test/fixtures/parsed_values_truth.json"

local work "`c(tmpdir)'dash_parsed_values_probe"
capture mkdir "`work'"
global ZP_WORK "`work'"


quietly shell git -C "${ZP_REPO}" rev-parse HEAD > "${ZP_WORK}/git_head.txt"
global ZP_VERSION "`c(stata_version)'"
global ZP_BORN "`c(born_date)'"
global ZP_WHEN "`c(current_date)' `c(current_time)'"
global ZP_KEYS ""

* _zp_probe key twoway-command: run the command on a fresh auto, record
* its rc in ZP_RC_<key>, its output (the error line) in <work>/<key>.log
* and, when it drew: plot 1's serset variable names (ZP_V_<key>) and
* values row by row (ZP_S_<key>, "." for missing), the plot regions and
* the plots in plot region 1 (ZP_PR_, ZP_NP_), each region's axis
* numbers (ZP_YD_, ZP_XD_), axis 1's and 2's y scale (ZP_Y1_, ZP_Y2_) and
* the legend's key count (ZP_LK_).  The command always holds a comma.
capture program drop _zp_probe
program define _zp_probe
    gettoken key cmd : 0
    quietly sysuse auto, clear
    serset clear
    capture graph drop _all
    quietly log using "${ZP_WORK}/`key'.log", text replace name(zpp) nomsg
    capture noisily twoway `cmd' nodraw name(g, replace)
    local rc = _rc
    quietly log close zpp
    global ZP_RC_`key' `rc'
    global ZP_KEYS "${ZP_KEYS} `key'"
    foreach g in V S PR NP YD XD Y1 Y2 LK {
        global ZP_`g'_`key' ""
    }
    if !`rc' {
        local np 0
        forvalues i = 1/9 {
            if "`.g.plotregion1.plot`i'.isa'" != "" local np `i'
        }
        local pr 0
        local yd ""
        local xd ""
        forvalues i = 1/9 {
            if "`.g.plotregion`i'.isa'" != "" {
                local pr `i'
                local yd `"`yd' `.g.plotregion`i'.yaxis_dexes'|"'
                local xd `"`xd' `.g.plotregion`i'.xaxis_dexes'|"'
            }
        }
        global ZP_NP_`key' `np'
        global ZP_PR_`key' `pr'
        global ZP_YD_`key' `"`yd'"'
        global ZP_XD_`key' `"`xd'"'
        global ZP_Y1_`key' "`.g.yaxis1.plotregion.yscale.curmin' `.g.yaxis1.plotregion.yscale.curmax'"
        if "`.g.yaxis2.isa'" != "" {
            global ZP_Y2_`key' "`.g.yaxis2.plotregion.yscale.curmin' `.g.yaxis2.plotregion.yscale.curmax'"
        }
        global ZP_LK_`key' "`.g.legend.keys.arrnels'"
        local id "`.g.plotregion1.plot1.serset.id'"
        preserve
        quietly serset set `id'
        quietly serset use, clear
        local names ""
        foreach v of varlist _all {
            local names `names' `v'
        }
        global ZP_V_`key' "`names'"
        local s ""
        local nr = min(_N, 3)
        forvalues r = 1/`nr' {
            foreach v of varlist _all {
                capture confirm numeric variable `v'
                if _rc local s "`s' str"
                else   local s "`s' `=strofreal(`v'[`r'], "%21.0g")'"
            }
            local s "`s' |"
        }
        global ZP_S_`key' "`s'"
        restore
    }
    display as text "ZP `key': rc `rc' vars ${ZP_V_`key'} plots ${ZP_NP_`key'} regions ${ZP_PR_`key'}"
end

* _zp_lpoly d k: the lpoly command's r(bwidth) and r(degree) for degree d
* and kernel k (no graph), in ZP_BW_<d>_<k>, ZP_DG_<d>_<k>.
capture program drop _zp_lpoly
program define _zp_lpoly
    args d k
    quietly sysuse auto, clear
    capture lpoly mpg weight, degree(`d') kernel(`k') nograph
    global ZP_LRC_`d'_`k' = _rc
    global ZP_BW_`d'_`k' = cond(_rc, ".", strofreal(r(bwidth), "%21.0g"))
    global ZP_DG_`d'_`k' = cond(_rc, ".", strofreal(r(degree), "%21.0g"))
end

* degree(): the command for degrees 4-8 under each kernel, and twoway's
* acceptance of each degree.
global ZP_KERNELS "epanechnikov epan2 biweight cosine gaussian parzen rectangle triangle"
foreach d in 4 5 6 7 8 {
    foreach k of global ZP_KERNELS {
        _zp_lpoly `d' `k'
    }
    _zp_probe degree_`d' lpoly mpg weight, degree(`d')
}

* mlabel(): one element naming several variables.
_zp_probe mlabel_pattern scatter mpg price weight, mlabel(t*)
_zp_probe mlabel_extra_names scatter mpg weight, mlabel(t*)
_zp_probe mlabel_range scatter mpg price weight, mlabel(make-foreign)
_zp_probe mlabel_bad_pattern scatter mpg weight, mlabel(zz*)

* scatteri p/q.  Ids for the forms "2/2 1", "-1/-1 1", "0/0 1", "1/2 1",
* "1 2 (1/1)", "2/2 1/1".
_zp_probe scatteri_a scatteri 2/2 1,
_zp_probe scatteri_b scatteri -1/-1 1,
_zp_probe scatteri_c scatteri 0/0 1,
_zp_probe scatteri_d scatteri 1/2 1,
_zp_probe scatteri_e scatteri 1 2 (1/1),
_zp_probe scatteri_f scatteri 2/2 1/1,
* pci reads its coordinates as scatteri does.
_zp_probe pci_a pci 2/2 0 0 1,
_zp_probe pci_b pci 1/2 0 0 1,

* yaxis() and xaxis() lists.
_zp_probe yaxis_both line mpg weight, yaxis(1 2)
_zp_probe yaxis_order line mpg weight, yaxis(2 1)
_zp_probe yaxis_dupe line mpg weight, yaxis(1 1)
_zp_probe yaxis_three line mpg weight, yaxis(1 2 3)
_zp_probe yaxis_zero line mpg weight, yaxis(0)
_zp_probe yaxis_ten line mpg weight, yaxis(10)
_zp_probe yaxis_frac line mpg weight, yaxis(1.5)
_zp_probe yaxis_word line mpg weight, yaxis(abc)
_zp_probe yaxis_tied (line mpg weight, yaxis(1 2)) (line price weight, yaxis(2)),
_zp_probe yaxis_untied (line mpg weight) (line price weight, yaxis(2)),
_zp_probe xaxis_both line mpg weight, xaxis(1 2)

python:
import json, os
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


work = G("ZP_WORK")
_HEAD = ("name:", "log:", "log type:", "opened on:", "closed on:")


def message(key):
    try:
        with open(os.path.join(work, key + ".log"), encoding="utf-8") as fh:
            lines = [ln.strip() for ln in fh.read().splitlines()]
    except OSError:
        return ""
    for ln in lines:
        if not ln or ln.startswith(_HEAD) or set(ln) <= set("-"):
            continue
        return ln
    return ""


def num(v):
    return None if v in (".", "", "str") else float(v)


def pair(v):
    w = (v or "").split()
    return [num(x) for x in w] if len(w) == 2 else None


def rec(key):
    rc = int(G("ZP_RC_" + key))
    r = {"rc": rc, "message": message(key) if rc else ""}
    if rc == 0:
        r["vars"] = G("ZP_V_" + key).split()
        rows = [x.split() for x in G("ZP_S_" + key).split("|")]
        r["rows"] = [[num(v) for v in row] for row in rows if row]
        r["plots"] = int(G("ZP_NP_" + key))
        r["regions"] = int(G("ZP_PR_" + key))
        r["yaxis_dexes"] = [x.strip() for x in G("ZP_YD_" + key).split("|") if x.strip()]
        r["xaxis_dexes"] = [x.strip() for x in G("ZP_XD_" + key).split("|") if x.strip()]
        r["yscale1"] = pair(G("ZP_Y1_" + key))
        r["yscale2"] = pair(G("ZP_Y2_" + key))
        lk = G("ZP_LK_" + key)
        r["legend_keys"] = int(lk) if lk.strip() else None
    return r


keys = G("ZP_KEYS").split()
recs = {k: rec(k) for k in keys}
out = {"degree": {}, "mlabel": {}, "scatteri": {}, "yaxis": {}, "xaxis": {}}
for d in ("4", "5", "6", "7", "8"):
    r = dict(recs["degree_" + d])
    r["twoway_rc"] = r.pop("rc")
    r["twoway_message"] = r.pop("message")
    for drop in ("vars", "rows", "plots", "regions", "yaxis_dexes",
                 "xaxis_dexes", "yscale1", "yscale2", "legend_keys"):
        r.pop(drop, None)
    r["kernels"] = {}
    for k in G("ZP_KERNELS").split():
        r["kernels"][k] = {"rc": int(G("ZP_LRC_%s_%s" % (d, k))),
                           "r_bwidth": num(G("ZP_BW_%s_%s" % (d, k))),
                           "r_degree": num(G("ZP_DG_%s_%s" % (d, k)))}
    r["r_bwidth"] = r["kernels"]["epanechnikov"]["r_bwidth"]
    r["r_degree"] = r["kernels"]["epanechnikov"]["r_degree"]
    out["degree"][d] = r
for k in ("pattern", "extra_names", "range", "bad_pattern"):
    out["mlabel"][k] = recs["mlabel_" + k]
forms = {"a": "2/2 1", "b": "-1/-1 1", "c": "0/0 1", "d": "1/2 1",
         "e": "1 2 (1/1)", "f": "2/2 1/1"}
for i, f in forms.items():
    out["scatteri"][f] = recs["scatteri_" + i]
out["pci"] = {"2/2 0 0 1": recs["pci_a"], "1/2 0 0 1": recs["pci_b"]}
for k in ("both", "order", "dupe", "three", "zero", "ten", "frac", "word",
          "tied", "untied"):
    out["yaxis"][k] = recs["yaxis_" + k]
out["xaxis"]["both"] = recs["xaxis_both"]
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZP_VERSION"), "born_date": G("ZP_BORN"),
                "dash_commit": commit, "extracted": G("ZP_WHEN"),
                "source": "scripts/extract_parsed_values_truth.do"}
with open(G("ZP_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
for k in keys + ["git_head"]:
    try:
        os.remove(os.path.join(work, k + (".txt" if k == "git_head" else ".log")))
    except OSError:
        pass
print("wrote", G("ZP_OUT"))
end
