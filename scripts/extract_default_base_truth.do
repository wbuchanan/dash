*! extract_default_base_truth.do -- WP-30 section 27 (P1.17b): measure
*! where twoway draws the base of bar, spike, dropline and area with and
*! without base(), and the y scale it draws them on, from twoway's own class
*! values (.plot#.drawn_base, .plotregion#.yscale.curmin/curmax,
*! .yaxis1.major.min/delta/max), so dash's default base is proved against
*! live twoway, not modelled.  twoway only: the output is the same before
*! and after dash changes.
*!
*! Output: test/fixtures/default_base_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_default_base_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zb_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zb_bad' {
    display as error "extract_default_base_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zb_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zb_rc' | _rc {
    local _zb_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_default_base_truth.do: `_zb_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZB_REPO "`repo'"
global ZB_OUT "${ZB_REPO}/test/fixtures/default_base_truth.json"

adopath ++ "${ZB_REPO}"
quietly do "${ZB_REPO}/dash_parse.mata"
quietly do "${ZB_REPO}/dash.ado"
global dash_nobrowser 1

local work "`c(tmpdir)'dash_default_base_probe"
capture mkdir "`work'"
global ZB_WORK "`work'"


quietly shell git -C "${ZB_REPO}" rev-parse HEAD > "${ZB_WORK}/git_head.txt"
global ZB_VERSION "`c(stata_version)'"
global ZB_BORN "`c(born_date)'"
global ZB_WHEN "`c(current_date)' `c(current_time)'"

* _zb_rec key prefix region plot: one record of the graph named g -- the
* plot's drawn_base, the region's curmin and curmax, and the major ticks
* of the y axis -- into global ZB_R_<key> as "base lo hi tmin tdelta tmax".
capture program drop _zb_rec
program define _zb_rec
    args key prefix region plot
    local b "`.g`prefix'.`region'.plot`plot'.drawn_base'"
    local lo "`.g`prefix'.`region'.yscale.curmin'"
    local hi "`.g`prefix'.`region'.yscale.curmax'"
    local ax = cond("`region'" == "plotregion2", "yaxis2", "yaxis1")
    local t0 "`.g`prefix'.`ax'.major.min'"
    local td "`.g`prefix'.`ax'.major.delta'"
    local t1 "`.g`prefix'.`ax'.major.max'"
    foreach v in b lo hi t0 td t1 {
        if "``v''" == "" local `v' "."
    }
    global ZB_R_`key' "`b' `lo' `hi' `t0' `td' `t1'"
    display as text "ZB `key': `b' [`lo', `hi'] ticks `t0'(`td')`t1'"
end

clear
input x1 ypos y12 yneg ys g d ymix ydown
1 10 12 -10 1 1 15000 -3 14
2 11 25 -11 2 1 15007 5 13
3 12 33 -12 3 2 15014 8 12
4 13 41 -13 4 2 15021 2 11
5 14 18 -14 5 2 15028 -1 10
end
format d %td
set scheme s2color

* One plot, plotregion1.
foreach c in "bar_ypos|bar ypos x1" "bar_y12|bar y12 x1" "spike_y12|spike y12 x1" ///
    "dropline_y12|dropline y12 x1" "area_y12|area y12 x1" "bar_yneg|bar yneg x1" ///
    "bar_ymix|bar ymix x1" "bar_scatter|(bar y12 x1) (scatter ys x1)" ///
    "bar_base5|bar ypos x1, base(5)" "spike_base5|spike ypos x1, base(5)" ///
    "area_base5|area y12 x1, base(5)" "bar_base20|bar ypos x1, base(20)" ///
    "auto_explicit0|(bar ypos x1) (bar y12 x1, base(0))" ///
    "bar_log|bar ypos x1, yscale(log)" "area_log|area ypos x1, yscale(log)" ///
    "bar_range0|bar ypos x1, yscale(range(0))" "bar_ylabel5|bar ypos x1, ylabel(5(5)15)" ///
    "bar_reverse|bar ypos x1, yscale(reverse)" "bar_if|bar ypos x1 if x1>=3" ///
    "bar_ydown|bar ydown x1" "bar_ydown_if|bar ydown x1 if x1<=3" ///
    "bar_td|bar d x1" "dropline_td|dropline d x1" {
    gettoken key cmd : c, parse("|")
    local cmd = substr(`"`cmd'"', 2, .)
    local sep = cond(strpos(`"`cmd'"', ",") & substr(`"`cmd'"', 1, 1) != "(", " ", ", ")
    quietly twoway `cmd' `sep' name(g, replace)
    _zb_rec `key' "" plotregion1 1
    graph drop g
}
quietly twoway (bar y12 x1) (bar ypos x1, base(30)), name(g, replace)
_zb_rec two_bars "" plotregion1 1
_zb_rec two_bars_2 "" plotregion1 2
graph drop g
quietly twoway (scatter y12 x1) (bar ypos x1, yaxis(2)), name(g, replace)
_zb_rec bar_y2 "" plotregion2 2
_zb_rec bar_y2_y "" plotregion1 1
graph drop g
quietly twoway bar y12 x1, by(g) name(g, replace)
forvalues i = 1/2 {
    _zb_rec bar_by_`i' ".graphs[`i']" plotregion1 1
}
graph drop g
quietly twoway bar y12 x1, by(g, yrescale) name(g, replace)
forvalues i = 1/2 {
    _zb_rec bar_by_yrescale_`i' ".graphs[`i']" plotregion1 1
}
graph drop g
quietly twoway (scatter y12 x1) (bar ypos x1, yaxis(2)), by(g) name(g, replace)
forvalues i = 1/2 {
    _zb_rec bar_by_y2_`i' ".graphs[`i']" plotregion2 2
}
graph drop g

sysuse auto, clear
foreach t in bar spike dropline area {
    quietly twoway `t' mpg weight, name(g, replace)
    _zb_rec auto_`t' "" plotregion1 1
    graph drop g
    quietly twoway `t' mpg weight in 1/3, name(g, replace)
    _zb_rec auto3_`t' "" plotregion1 1
    graph drop g
}

python:
import json, os
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


def rec(key):
    f = [None if w == "." else float(w) for w in G("ZB_R_" + key).split()]
    return {"drawn_base": f[0], "curmin": f[1], "curmax": f[2],
            "ticks": f[3:6]}


one = ["bar_ypos", "bar_y12", "spike_y12", "dropline_y12", "area_y12",
       "bar_yneg", "bar_ymix", "bar_scatter", "bar_base5", "spike_base5",
       "area_base5", "bar_base20", "auto_explicit0", "bar_log", "area_log",
       "bar_range0", "bar_ylabel5", "bar_reverse", "bar_if", "bar_ydown",
       "bar_ydown_if", "bar_td", "dropline_td"]
bases = {k: rec(k) for k in one}
bases["two_bars"] = dict(rec("two_bars"),
                         drawn_base2=rec("two_bars_2")["drawn_base"])
bases["bar_y2"] = dict(rec("bar_y2"), y=rec("bar_y2_y"))
for k in ("bar_by", "bar_by_yrescale", "bar_by_y2"):
    bases[k] = {"panels": [rec("%s_%d" % (k, i)) for i in (1, 2)]}
out = {"bases": bases,
       "auto": {t: rec("auto_" + t) for t in ("bar", "spike", "dropline", "area")},
       "auto3": {t: rec("auto3_" + t) for t in ("bar", "spike", "dropline", "area")}}
work = G("ZB_WORK")
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZB_VERSION"), "born_date": G("ZB_BORN"),
                "dash_commit": commit, "extracted": G("ZB_WHEN"),
                "source": "scripts/extract_default_base_truth.do"}
with open(G("ZB_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZB_OUT"))
end
