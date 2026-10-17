*! extract_kpi_weights_truth.do -- WP-31 section 50 (H2k): measure what
*! Stata's summarize, _pctile and tabstat answer for a KPI statistic under
*! each weight class dash kpi takes -- aweight, fweight and iweight -- and
*! unweighted, on the auto data, so the KPI card's weighted arithmetic in
*! both renderers is proved against Stata, not modelled.  Also the words
*! Stata uses to refuse a pweight, an iweight under summarize, detail, a
*! string, negative or noninteger weight.  Stata only: the output is the
*! same before and after dash changes.
*!
*! Output: test/fixtures/kpi_weights_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_kpi_weights_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_kw_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_kw_bad' {
    display as error "extract_kpi_weights_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _kw_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_kw_rc' | _rc {
    local _kw_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_kpi_weights_truth.do: `_kw_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global KW_REPO "`repo'"
global KW_OUT "${KW_REPO}/test/fixtures/kpi_weights_truth.json"

adopath ++ "${KW_REPO}"
global dash_nobrowser 1

local work "`c(tmpdir)'dash_kpi_weights_probe"
capture mkdir "`work'"
global KW_WORK "`work'"

if `"`c(python_exec)'"' == "" {
    display as error "extract_kpi_weights_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

quietly shell git -C "${KW_REPO}" rev-parse HEAD > "${KW_WORK}/git_head.txt"
global KW_VERSION "`c(stata_version)'"
global KW_BORN "`c(born_date)'"
global KW_WHEN "`c(current_date)' `c(current_time)'"

* The percentiles measured beside p25, p50 and p75.
global KW_PCT "1 2.5 5 10 33.3 66.7 90 95 97.5 99"

* _kw_scope key var wt if: one scope's statistics into global KW_S_<key>
* as "name=value" words; "." for a statistic Stata gives as missing or
* refuses.  wt is "" or a weight clause such as aw=weight.
capture program drop _kw_scope
program define _kw_scope
    args key var wt cond
    local w = cond("`wt'" == "", "", "[`wt']")
    local out ""
    quietly summarize `var' `w' `cond'
    foreach s in N sum_w mean Var sd min max sum {
        local out = "`out' `s'=" + strofreal(r(`s'), "%21.17g")
    }
    local out = "`out' range=" + strofreal(r(max) - r(min), "%21.17g")
    local out = "`out' semean=" + strofreal(r(sd) / sqrt(r(N)), "%21.17g")
    capture summarize `var' `w' `cond', detail
    local drc = _rc
    local out "`out' detail_rc=`drc'"
    if `drc' == 0 {
        foreach s in skewness kurtosis p25 p50 p75 {
            local out = "`out' `s'=" + strofreal(r(`s'), "%21.17g")
        }
    }
    else {
        foreach s in skewness kurtosis p25 p50 p75 {
            local out "`out' `s'=."
        }
    }
    * tabstat's semean, the statistic dash names after it.
    capture tabstat `var' `w' `cond', statistics(semean) save
    local trc = _rc
    local out "`out' tabstat_rc=`trc'"
    if `trc' == 0 {
        matrix _kwT = r(StatTotal)
        local out = "`out' tabstat_semean=" + strofreal(_kwT[1, 1], "%21.17g")
    }
    * _pctile's answers, which dash kpi's median, iqr and p# take.
    if `drc' == 0 {
        quietly _pctile `var' `w' `cond', p(${KW_PCT})
        local i 0
        foreach p of global KW_PCT {
            local ++i
            local out = "`out' pct`p'=" + strofreal(r(r`i'), "%21.17g")
        }
    }
    * dcount takes no weight: the distinct values among the observations
    * the weight keeps (a missing or zero weight drops its observation).
    local wv = cond("`wt'" == "", "", substr("`wt'", strpos("`wt'", "=") + 1, .))
    local wk = cond("`wv'" == "", "1", "!missing(`wv') & `wv' != 0")
    local wc = cond(`"`cond'"' == "", "if `wk'", `"`cond' & `wk'"')
    tempvar grp
    quietly egen `grp' = group(`var') `wc'
    quietly summarize `grp', meanonly
    local out = "`out' dcount=" + strofreal(cond(r(N) == 0, 0, r(max)), "%21.17g")
    global KW_S_`key' "`out'"
    display as text "KW `key': `out'"
end

sysuse auto, clear
* An aweight with zero weights: summarize leaves those observations out.
generate double wz = cond(_n <= 5, 0, weight)

foreach scope in all foreign1 {
    local cond = cond("`scope'" == "all", "", "if foreign == 1")
    _kw_scope unweighted_`scope' mpg "" "`cond'"
    _kw_scope aweight_`scope' mpg "aw=weight" "`cond'"
    _kw_scope fweight_`scope' mpg "fw=rep78" "`cond'"
    _kw_scope iweight_`scope' mpg "iw=weight" "`cond'"
}
_kw_scope aweight_zero mpg "aw=wz" ""
* price, for the percentile rule on a variable with no ties.
_kw_scope aweight_price price "aw=weight" ""
_kw_scope fweight_price price "fw=rep78" ""

* mean's standard error under an aweight (the plan's semean_aw).
quietly mean mpg [aw=weight]
global KW_SEMEAN_AW = strofreal(_se[mpg], "%21.17g")

* The refusals, as Stata words them: rc and the one line of text, read
* back from a log of the one command.
capture program drop _kw_refusal
program define _kw_refusal
    args key cmd
    local lf "${KW_WORK}/refusal_`key'.log"
    capture log close _kwl
    quietly log using "`lf'", text replace name(_kwl)
    capture noisily `cmd'
    local rc = _rc
    quietly log close _kwl
    tempname fh
    local text ""
    file open `fh' using "`lf'", read text
    file read `fh' line
    while r(eof) == 0 {
        local t = strtrim(`"`macval(line)'"')
        if `"`macval(t)'"' != "" & substr(`"`macval(t)'"', 1, 1) != "." ///
            & !strpos(`"`macval(t)'"', "log:") & !strpos(`"`macval(t)'"', "log type:") ///
            & !strpos(`"`macval(t)'"', "opened on:") & !strpos(`"`macval(t)'"', "name:") ///
            & !strpos(`"`macval(t)'"', "closed on:") & !strpos(`"`macval(t)'"', "----") {
            local text `"`macval(t)'"'
        }
        file read `fh' line
    }
    file close `fh'
    global KW_RC_`key' "`rc'"
    global KW_TX_`key' `"`macval(text)'"'
    display as text "KW refusal `key': rc `rc' text `macval(text)'"
end
_kw_refusal pweight "summarize mpg [pw=weight]"
_kw_refusal iweight_detail "summarize mpg [iw=weight], detail"
_kw_refusal string "summarize mpg [aw=make]"
generate double wneg = weight - 3000
_kw_refusal negative "summarize mpg [aw=wneg]"
_kw_refusal noninteger "summarize mpg [fw=gear_ratio]"

python:
import json, os
from sfi import Data, Macro


def G(k):
    return Macro.getGlobal(k)


def scope(key):
    out = {}
    pct = {}
    for word in G("KW_S_" + key).split():
        name, _, val = word.partition("=")
        v = None if val == "." else float(val)
        if name.endswith("_rc"):
            v = int(v)
        if name.startswith("pct"):
            pct[name[3:]] = v
        else:
            out[name] = v
    if pct:
        out["pctiles"] = pct
    return out


out = {"variable": "mpg", "dataset": "auto",
       "weights": {"aweight": "weight", "fweight": "rep78",
                   "iweight": "weight", "aweight_zero": "wz",
                   "wz": "weight with observations 1-5 set to 0"},
       "unweighted": {s: scope("unweighted_" + s) for s in ("all", "foreign1")},
       "aweight": {s: scope("aweight_" + s) for s in ("all", "foreign1")},
       "fweight": {s: scope("fweight_" + s) for s in ("all", "foreign1")},
       "iweight": {s: scope("iweight_" + s) for s in ("all", "foreign1")}}
# The data itself, so the tests compute on exactly what Stata summarized:
# Stata's missing value is written as null.
cols = {}
for v in ("mpg", "weight", "rep78", "foreign", "price", "wz"):
    vals = Data.get(v)
    cols[v] = [None if (x is None or x >= 8.988e307) else float(x)
               for x in vals]
out["data"] = cols
out["aweight"]["zero"] = scope("aweight_zero")
out["aweight"]["price"] = scope("aweight_price")
out["fweight"]["price"] = scope("fweight_price")
out["aweight"]["semean_aw"] = float(G("KW_SEMEAN_AW"))
for key in ("pweight", "iweight_detail", "string", "negative", "noninteger"):
    out[key + "_refusal"] = {"rc": int(G("KW_RC_" + key)),
                             "text": G("KW_TX_" + key)}
work = G("KW_WORK")
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("KW_VERSION"), "born_date": G("KW_BORN"),
                "dash_commit": commit, "extracted": G("KW_WHEN"),
                "source": "scripts/extract_kpi_weights_truth.do"}
with open(G("KW_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("KW_OUT"))
end
