*! extract_weighted_markers_truth.do -- WP-31 section 20 (C9, A5b):
*! measure how twoway draws the markers of a weighted plot -- each
*! marker's radius in twoway's own SVG export, beside the radii of
*! unweighted markers at known msize() values -- with msize(), the
*! max_wted_symsize cap, zero, missing and negative weights, on every
*! marker type, and what twoway says (return code and the lines it
*! prints) for weights that are zero on every row, on the marker types
*! and on the statistical types.  twoway only: the output is the same
*! before and after dash changes.
*!
*! Output: test/fixtures/weighted_markers_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_weighted_markers_truth.do
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
    display as error "extract_weighted_markers_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_weighted_markers_truth.do: `_zm_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZM_REPO "`repo'"
global ZM_OUT "${ZM_REPO}/test/fixtures/weighted_markers_truth.json"

local work "`c(tmpdir)'dash_weighted_markers_probe"
capture mkdir "`work'"
global ZM_WORK "`work'"

if `"`c(python_exec)'"' == "" {
    display as error "extract_weighted_markers_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

quietly shell git -C "${ZM_REPO}" rev-parse HEAD > "${ZM_WORK}/git_head.txt"
global ZM_VERSION "`c(stata_version)'"
global ZM_BORN "`c(born_date)'"
global ZM_WHEN "`c(current_date)' `c(current_time)'"
global ZM_KEYS ""

* _zm_data: auto's first eight cars (readable SVGs), with the weights the
* probes use.
capture program drop _zm_data
program define _zm_data
    sysuse auto, clear
    quietly keep in 1/8
    quietly generate t = _n
    quietly tsset t
    quietly generate double lo = mpg - 2
    quietly generate double hi = mpg + 2
    quietly generate double x2 = weight + 100
    quietly generate double wbig = cond(_n == 1, 10000, 1)
    quietly generate double wz = cond(_n == 1, 0, price)
    quietly generate double wmis = cond(_n == 1, ., price)
    quietly generate double wneg = cond(_n == 1, -1, price)
    quietly generate double zero = 0
    quietly generate double allmis = .
    quietly generate double allneg = -price
    set scheme s2color
end

* _zm_run <key> : <twoway command>  -- run the command under a log, record
* its rc and the log (the lines twoway printed) in globals ZM_RC_<key> and
* ZM_LOG_<key>; with rc 0 the graph is exported to <work>/<key>.svg.
capture program drop _zm_run
program define _zm_run
    gettoken key 0 : 0
    gettoken colon 0 : 0, parse(":")
    local cmd `"`0'"'
    local lf "${ZM_WORK}/`key'.log"
    capture graph drop _all
    quietly log using "`lf'", text replace name(zmlog)
    capture noisily `cmd' name(zm, replace)
    local rc = _rc
    quietly log close zmlog
    global ZM_RC_`key' "`rc'"
    global ZM_LOG_`key' "`lf'"
    global ZM_CMD_`key' `"`cmd'"'
    global ZM_KEYS "${ZM_KEYS} `key'"
    if `rc' == 0 {
        quietly graph export "${ZM_WORK}/`key'.svg", name(zm) replace
    }
    display as text "ZM `key': rc `rc'"
end

_zm_data
* The probe data, for the renderer's side of the comparison.
preserve
keep mpg weight price rep78
format mpg weight price rep78 %21.0g
quietly export delimited using "${ZM_WORK}/data.csv", replace datafmt
restore

* ---- the rule: radii of weighted markers beside unweighted references ----
_zm_run W01 : twoway scatter mpg weight [aw=price],
_zm_run R_med : twoway scatter mpg weight,
_zm_run R_1 : twoway scatter mpg weight, msize(1)
_zm_run R_15 : twoway scatter mpg weight, msize(1.5)
_zm_run R_10 : twoway scatter mpg weight, msize(10)
_zm_run W02_fw : twoway scatter mpg weight [fw=rep78],
_zm_run W02_pw : twoway scatter mpg weight [pw=price],
_zm_run W03_huge : twoway scatter mpg weight [aw=price], msize(huge)
_zm_run R_huge : twoway scatter mpg weight, msize(huge)
_zm_run W03_2 : twoway scatter mpg weight [aw=price], msize(2)
_zm_run W04_cap : twoway scatter mpg weight [aw=wbig],
* ---- zero, missing and negative weights ----
_zm_run W05_neg : twoway scatter mpg weight [aw=wneg],
_zm_run W06_zero : twoway scatter mpg weight [aw=wz],
_zm_run W06_mis : twoway scatter mpg weight [aw=wmis],
_zm_run W06_allzero : twoway scatter mpg weight [aw=zero],
_zm_run W06_allmis : twoway scatter mpg weight [aw=allmis],
_zm_run W06_allneg : twoway scatter mpg weight [aw=allneg],
_zm_run W06_twolayers : twoway (scatter mpg weight [aw=zero]) (line mpg weight),
_zm_run W06_none : twoway scatter mpg weight [aw=zero], msymbol(none)
_zm_run W06_mlab : twoway scatter mpg weight [aw=zero], mlabel(make)
* ---- markerless types: accepted, nothing said ----
_zm_run W07_line : twoway line mpg weight [aw=price],
_zm_run W07_bar : twoway bar mpg weight [fw=rep78],
_zm_run W07_area : twoway area mpg weight [aw=price],
_zm_run W07_spike : twoway spike mpg weight [aw=price],
_zm_run W07_rspike : twoway rspike lo hi weight [aw=price],
_zm_run W07_rcap : twoway rcap lo hi weight [aw=price],
_zm_run W07_pcspike : twoway pcspike mpg weight hi x2 [aw=price],
_zm_run W07_tsline : twoway tsline mpg [aw=price],
* ---- every marker type ----
_zm_run W08_dot : twoway dot mpg weight [aw=price],
_zm_run W09_rscatter : twoway rscatter lo hi weight [aw=price],
_zm_run W10_connected : twoway connected mpg weight [aw=price],
_zm_run W10_dropline : twoway dropline mpg weight [aw=price],
_zm_run W10_rcapsym : twoway rcapsym lo hi weight [aw=price],
_zm_run W10_rconnected : twoway rconnected lo hi weight [aw=price],
_zm_run W10_pcscatter : twoway pcscatter mpg weight hi x2 [aw=price],
_zm_run W10_pccapsym : twoway pccapsym mpg weight hi x2 [aw=price],
* ---- what else changes the weighted path ----
_zm_run W11_mlabel : twoway scatter mpg weight [aw=price], mlabel(make)
_zm_run W11_hollow : twoway scatter mpg weight [aw=price], msymbol(Oh)
_zm_run W11_point : twoway scatter mpg weight [aw=price], msymbol(p)
_zm_run R_point : twoway scatter mpg weight, msymbol(p)
_zm_run W11_jitter : twoway scatter mpg weight [aw=price], jitter(2)
_zm_run W11_colorvar : twoway scatter mpg weight [aw=price], colorvar(rep78)
_zm_run W11_expr : twoway scatter mpg weight [aw=price+1],
_zm_run W11_ts : twoway scatter mpg weight [aw=L.price],
* ---- A5b: a weight that is zero on every row, on the statistical types ----
foreach t in lfit qfit lfitci qfitci fpfit fpfitci lpoly lpolyci kdensity mspline mband lowess {
    local v = cond("`t'" == "kdensity", "mpg", "mpg weight")
    _zm_run A5b_`t'_expr : twoway `t' `v' [aw=price-price],
    _zm_run A5b_`t'_var : twoway `t' `v' [aw=zero],
}
_zm_run A5b_histogram_expr : twoway histogram mpg [fw=rep78-rep78],
_zm_run A5b_histogram_var : twoway histogram mpg [fw=zero],
* ---- A5b: the weight text each type's parser takes (serset.class new,
* _genwt; series.class new): a text -syntax varlist(min=1 max=1)- reads as
* one variable is used as typed, token by token ----
foreach t in scatter line mspline mband rscatter pcscatter bar tsline function lfit {
    local v "mpg weight"
    if "`t'" == "rscatter" local v "lo hi weight"
    if "`t'" == "pcscatter" local v "mpg weight hi x2"
    if "`t'" == "tsline" local v "mpg"
    if "`t'" == "function" local v "y = x"
    local k 0
    foreach f in "price-price" "price - price" "(price)" "( price )" "pri-pri" "price+1" "price-mpg" "((price))" "pri" {
        local ++k
        _zm_run X_`t'_`k' : twoway `t' `v' [aw=`f'],
    }
}
* An all-zero text the parser refuses: the parser's answer comes first.
_zm_run X_zero_order : twoway scatter mpg weight [aw=zero-zero],
* An option twoway refuses comes before the weight text.
_zm_run X_option_order : twoway scatter mpg weight [aw=price-price], bwidth(2)
* mspline and mband take a weight and say nothing.
_zm_run I_mspline : twoway mspline mpg weight [aw=price],
_zm_run I_mband : twoway mband mpg weight [aw=price],

python:
import csv, json, os, re
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


def lines(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            got = [ln.rstrip("\n").rstrip() for ln in fh]
    except OSError:
        return []
    # The log holds the command echo and the lines twoway printed; only
    # the printed lines are kept.
    keep = []
    for ln in got:
        s = ln.strip()
        if not s or s.startswith(".") or s.startswith(">") \
                or s.startswith("name:") or s.startswith("log:") \
                or s.startswith("log type:") or s.startswith("opened on:") \
                or s.startswith("closed on:") or set(s) <= set("-"):
            continue
        keep.append(s)
    return keep


_CIRCLE = re.compile(r'<circle cx="([-\d.]+)" cy="([-\d.]+)" r="([\d.]+)" '
                     r'style="([^"]*)"')
_RECT = re.compile(r'<rect x="[-\d.]+" y="[-\d.]+" width="([\d.]+)" '
                   r'height="[\d.]+" style="([^"]*)"')


def markers(path):
    """The radius of every outlined marker circle, in document order (the
    data's order), and every fill-only circle's: twoway draws a marker as
    a filled circle and then its outline, and the outline's radius is the
    marker's (the fill's is it plus half the outline)."""
    try:
        with open(path, encoding="utf-8") as fh:
            s = fh.read()
    except OSError:
        return None
    out, fill = [], []
    for cx, cy, r, sty in _CIRCLE.findall(s):
        if "fill:none" in sty:
            out.append(float(r))
        else:
            fill.append(float(r))
    return {"radii": out, "fill_radii": fill}


def data(path):
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    cols = {h: [] for h in rows[0]}
    for r in rows[1:]:
        for h, v in zip(rows[0], r):
            cols[h].append(float(v) if v not in ("", ".") else None)
    return cols


work = G("ZM_WORK")
out = {}
for key in G("ZM_KEYS").split():
    rc = int(G("ZM_RC_%s" % key))
    lf = G("ZM_LOG_%s" % key)
    txt = lines(lf)
    rec = {"cmd": G("ZM_CMD_%s" % key).strip().rstrip(","), "rc": rc,
           "lines": txt}
    sp = os.path.join(work, "%s.svg" % key)
    if rc == 0 and os.path.exists(sp):
        rec.update(markers(sp))
        os.remove(sp)
    try:
        os.remove(lf)
    except OSError:
        pass
    out[key] = rec
out["data"] = data(os.path.join(work, "data.csv"))
os.remove(os.path.join(work, "data.csv"))
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZM_VERSION"), "born_date": G("ZM_BORN"),
                "dash_commit": commit, "extracted": G("ZM_WHEN"),
                "source": "scripts/extract_weighted_markers_truth.do"}
with open(G("ZM_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZM_OUT"))
end
