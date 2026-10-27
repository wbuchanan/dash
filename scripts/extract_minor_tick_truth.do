*! extract_minor_tick_truth.do -- WP-31 section 24 (GAPS3 D1): measure the
*! minor ticks and minor labels twoway draws for xmtick(), xmlabel() and
*! ymtick(, axis(2)), from twoway's own class values: each axis's labelled
*! minor tickset .minor (xmlabel) and unlabelled one .minornl (xmtick) --
*! their rule (.min, .max, .delta, ._between_ticks, .use_rule), their
*! listed ticks (.ticks[i][1] and [2]) and label format -- and the scale
*! they widen (.plotregion1.xscale.curmin/curmax).  The rule's positions
*! are min(delta)max up to max + .48*delta, as tickset_g.class's draw
*! walks them.  twoway only: the output is the same before and after dash
*! changes.
*!
*! Output: test/fixtures/minor_tick_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_minor_tick_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zm_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zm_bad' {
    display as error "extract_minor_tick_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zm_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zm_rc' | _rc {
    local _zm_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_minor_tick_truth.do: `_zm_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZM_REPO "`repo'"
global ZM_OUT "${ZM_REPO}/test/fixtures/minor_tick_truth.json"

adopath ++ "${ZM_REPO}"
quietly do "${ZM_REPO}/dash_parse.mata"
quietly do "${ZM_REPO}/dash.ado"
global dash_nobrowser 1

local work "`c(tmpdir)'dash_minor_tick_probe"
capture mkdir "`work'"
global ZM_WORK "`work'"


quietly shell git -C "${ZM_REPO}" rev-parse HEAD > "${ZM_WORK}/git_head.txt"
global ZM_VERSION "`c(stata_version)'"
global ZM_BORN "`c(born_date)'"
global ZM_WHEN "`c(current_date)' `c(current_time)'"

* _zm_rec key axis set region: one tickset of graph u24k -- axis xaxis1,
* yaxis2 ..., set minor or minornl -- into globals ZM_<key>_rule ("min max
* delta between use_rule"), ZM_<key>_n, ZM_<key>_v<i> (value) and
* ZM_<key>_t<i> (its text, "" when none), ZM_<key>_fmt (label format) and
* ZM_<key>_scale ("curmin curmax" of the region's scale on that axis).
capture program drop _zm_rec
program define _zm_rec
    args key axis set region
    local p ".u24k.`axis'.`set'"
    local s "``p'.min' ``p'.max' ``p'.delta' ``p'._between_ticks' ``p'.use_rule.istrue'"
    global ZM_`key'_rule "`s'"
    local n = 0``p'.ticks.arrnels'
    global ZM_`key'_n "`n'"
    forvalues i = 1/`n' {
        global ZM_`key'_v`i' "``p'.ticks[`i'][1]'"
        global ZM_`key'_t`i' `"``p'.ticks[`i'][2]'"'
    }
    global ZM_`key'_fmt "``p'.label_format'"
    local sc = cond(substr("`axis'", 1, 1) == "x", "xscale", "yscale")
    global ZM_`key'_scale "`.u24k.`region'.`sc'.curmin' `.u24k.`region'.`sc'.curmax'"
    display as text "ZM `key': rule `s' n `n' scale ${ZM_`key'_scale}"
end

sysuse auto, clear
set scheme s2color

* key | set | twoway options (scatter mpg weight)
foreach c in ///
    "m_between5|minornl|xlabel(0(1000)5000) xmtick(##5)" ///
    "m_between_default|minornl|xmtick(##5)" ///
    "m_between_uneven|minornl|xlabel(1000 2000 4000) xmtick(##5)" ///
    "m_between_even_list|minornl|xlabel(1000 2000 3000) xmtick(##5)" ///
    "m_between_label|minor|xmlabel(##4)" ///
    "m_between_count|minornl|xlabel(#3) xmtick(##2)" ///
    "m_explicit|minornl|xmtick(1500 2500)" ///
    "m_count|minornl|xmtick(#3)" ///
    "m_minmax|minornl|xmtick(minmax)" ///
    "m_widen|minornl|xmtick(6000)" ///
    "m_log|minornl|xscale(log) xmtick(##5)" {
    gettoken key rest : c, parse("|")
    gettoken bar rest : rest, parse("|")
    gettoken set rest : rest, parse("|")
    gettoken bar opts : rest, parse("|")
    quietly twoway scatter mpg weight, `opts' name(u24k, replace)
    _zm_rec `key' xaxis1 `set' plotregion1
    graph drop u24k
}
* The rows a filter move to foreign == 1 keeps: ##5 follows their majors.
quietly twoway scatter mpg weight if foreign == 1, xmtick(##5) name(u24k, replace)
_zm_rec m_between_foreign xaxis1 minornl plotregion1
graph drop u24k
quietly twoway scatter mpg weight, xmlabel(1500 "a" 2500) name(u24k, replace)
_zm_rec m_labels xaxis1 minor plotregion1
graph drop u24k
quietly twoway scatter mpg weight, ymlabel(##2) ylabel(10(10)40) name(u24k, replace)
_zm_rec m_y_between yaxis1 minor plotregion1
graph drop u24k
quietly twoway scatter mpg weight || scatter price weight, yaxis(2) ymtick(5000 10000, axis(2)) name(u24k, replace)
_zm_rec m_axis2 yaxis2 minornl plotregion2
graph drop u24k
* A %td axis: tsnatscale's default majors are uneven, so ##2 draws nothing.
preserve
generate d = mdy(1, 1, 2000) + _n * 30
format d %td
quietly twoway scatter mpg d, xmtick(##2) name(u24k, replace)
_zm_rec m_date_between xaxis1 minornl plotregion1
graph drop u24k
restore
* ##N on a major option: twoway notes it and draws the default ticks.
capture noisily twoway scatter mpg weight, xlabel(##5) name(u24k, replace)
global ZM_refusal_rc "`=_rc'"
capture graph drop u24k

python:
import json, os
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


def num(w):
    try:
        return float(w)
    except ValueError:
        return None


def rec(key):
    r = [num(w) for w in G("ZM_%s_rule" % key).split()]
    n = int(G("ZM_%s_n" % key) or 0)
    vals = [num(G("ZM_%s_v%d" % (key, i))) for i in range(1, n + 1)]
    texts = [G("ZM_%s_t%d" % (key, i)) for i in range(1, n + 1)]
    sc = [num(w) for w in G("ZM_%s_scale" % key).split()]
    out = {"min": r[0], "max": r[1], "delta": r[2], "between": r[3],
           "use_rule": bool(r[4]), "ticks": vals, "texts": texts,
           "format": G("ZM_%s_fmt" % key), "scale": sc}
    # tickset_g.class draw: forvalues x = min(delta)(max + .48*delta),
    # a value within delta*1e-6 of 0 drawn at 0.
    pos = []
    lo, hi, d = r[0], r[1], r[2]
    if out["use_rule"] and None not in (lo, hi, d) and d != 0 \
            and abs(lo) < 1e299 and abs(hi) < 1e299:
        i = 0
        while lo + i * d <= hi + 0.48 * d and i <= 10000:
            x = lo + i * d
            pos.append(0.0 if abs(x) < d * 1e-6 else x)
            i += 1
    out["positions"] = pos
    return out


keys = ["m_between5", "m_between_default", "m_between_uneven",
        "m_between_even_list", "m_between_label", "m_between_count",
        "m_explicit", "m_count", "m_minmax", "m_widen", "m_log",
        "m_labels", "m_between_foreign", "m_y_between", "m_axis2", "m_date_between"]
out = {k: rec(k) for k in keys}
out["m_refusal"] = {"rc": int(G("ZM_refusal_rc") or 0),
                    "note": "##5 ignored, only allowed for minor ticks"}
work = G("ZM_WORK")
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZM_VERSION"), "born_date": G("ZM_BORN"),
                "dash_commit": commit, "extracted": G("ZM_WHEN"),
                "source": "scripts/extract_minor_tick_truth.do",
                "members": ["min", "max", "delta", "_between_ticks",
                            "use_rule", "ticks", "label_format"]}
with open(G("ZM_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZM_OUT"))
end
