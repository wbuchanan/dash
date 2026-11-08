*! extract_colour_edges_truth.do -- WP-45 section 45-05 (ST-22, GW-10):
*! what twoway draws for a colour's intensity above 1 near Stata's clamp,
*! how it refuses a blank style-list element, and what the svg
*! translator's font faces are.
*!
*! Output: test/fixtures/colour_edges_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_colour_edges_truth.do
*!
*! ROWS.
*!   I_<colour>_<k>  the marker fill of scatter mpg weight, mcolor(<c>*<k>)
*!                   under s2color for seven colours and seventeen k (a
*!                   "." in k is written p, a blank in a colour _).
*!   H_<c>           mcolor("<c> 255 255*<2c>"), c = 1..255: the smallest
*!                   channel at an exact half, where Stata's clamp is
*!                   decided by its own arithmetic.
*!   N_<c>           mcolor("1 <c> 255*2"), odd c: a channel other than the
*!                   smallest at an exact half.
*!   M_<c>           mcolor("2 <c> 255*10"), odd c: the clamp divides by 2,
*!                   so the channel lands at an exact half.
*!   B_<option>      a blank first element, <option>(" " p1), on a type with
*!                   two y that takes the option: rc and the first line.
*!   F_query         the values translator query gph2svg returns (read
*!                   only; nothing is set).
*!
*! The marker fill is the dominant fill of the largest circles of the
*! exported SVG (scripts/svg_truth.py).  twoway only: dash is never run.
*! No graph preference is changed.  Every SVG and log is erased.

clear all
set more off
set linesize 255

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_colour_edges_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_colour_edges_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the dash repository"'
    exit 601
}
global CE_REPO "`repo'"
global CE_OUT "${CE_REPO}/test/fixtures/colour_edges_truth.json"
global dash_nobrowser 1

version 19
set graphics off

tempfile _ce_name
mata: st_global("CE_WORK", pathjoin(st_global("c(tmpdir)"), "dash_ce_" + pathbasename(st_local("_ce_name"))))
mata: st_global("CE_WORK", subinstr(subinstr(st_global("CE_WORK"), ".tmp", ""), ".", "_"))
capture mkdir "${CE_WORK}"

quietly shell git -C "${CE_REPO}" rev-parse HEAD > "${CE_WORK}/git_head.txt"
global CE_VERSION "`c(stata_version)'"
global CE_BORN "`c(born_date)'"
global CE_WHEN "`c(current_date)' `c(current_time)'"

sysuse auto, clear
generate lo = mpg - 3
generate hi = mpg + 3

global CE_IDS ""
global CE_SEQ = 0

capture program drop _ce_fill
program define _ce_fill
    * _ce_fill id `"colour"': the marker fill of mcolor(colour)
    args id colour
    global CE_SEQ = ${CE_SEQ} + 1
    local f "${CE_WORK}/c${CE_SEQ}"
    capture twoway scatter mpg weight, mcolor(`colour') scheme(s2color) name(ce, replace)
    global CER_`id' = _rc
    global CEF_`id' "c${CE_SEQ}"
    global CEV_`id' `"`colour'"'
    global CEK_`id' "fill"
    if !_rc quietly graph export "`f'.svg", replace name(ce)
    capture graph drop ce
    global CE_IDS "${CE_IDS} `id'"
end

capture program drop _ce_refusal
program define _ce_refusal
    * _ce_refusal id ptype yvars option: option(" " p1) on ptype
    args id ptype yvars option
    global CE_SEQ = ${CE_SEQ} + 1
    local f "${CE_WORK}/c${CE_SEQ}"
    quietly log using "`f'.log", text replace name(cel)
    capture noisily twoway `ptype' `yvars' weight, `option'(" " p1) scheme(s2color) name(ce, replace)
    local rc = _rc
    quietly log close cel
    capture graph drop ce
    global CER_`id' = `rc'
    global CEF_`id' "c${CE_SEQ}"
    global CEV_`id' `"twoway `ptype' `yvars' weight, `option'(" " p1)"'
    global CEK_`id' "refusal"
    global CE_IDS "${CE_IDS} `id'"
end

* I_*: the plan's grid.
local ks "1.5 2 3 5 10 20 40 45 50 51 52 53 60 100 255 256 1000"
foreach c in navy red gs8 "26 71 111" "200 100 50" "1 2 255" white {
    local cn : subinstr local c " " "_", all
    foreach k of local ks {
        local kn : subinstr local k "." "p", all
        if strpos("`c'", " ") _ce_fill I_`cn'_`kn' `""`c'*`k'""'
        else _ce_fill I_`cn'_`kn' `"`c'*`k'"'
    }
}
* H_*: the smallest channel at an exact half.
forvalues c = 1/255 {
    local k = 2 * `c'
    _ce_fill H_`c' `""`c' 255 255*`k'""'
}
* N_*: another channel at an exact half (k = 2).
forvalues c = 3(2)253 {
    _ce_fill N_`c' `""1 `c' 255*2""'
}
* M_*: the clamp's division at an exact half (2 / 10 rounds to 0).
forvalues c = 3(2)253 {
    _ce_fill M_`c' `""2 `c' 255*10""'
}

* B_*: a blank first element.
foreach o in mcolor msymbol msize msangle mfcolor mlcolor mlwidth mlpattern ///
    mlabcolor mlabsize mlabposition mlabgap mlabangle mlabformat ///
    clcolor clpattern clwidth color fcolor ///
    fintensity bfcolor blcolor acolor alcolor alwidth alpattern ///
    mlabel jitter pstyle lstyle mstyle mlstyle mlabtextstyle {
    _ce_refusal B_`o' scatter "mpg turn" `o'
}
foreach o in lcolor lwidth lpattern {
    _ce_refusal B_`o' line "mpg turn" `o'
}
foreach o in base barwidth bstyle blstyle {
    _ce_refusal B_`o' bar "mpg turn" `o'
}
foreach o in astyle alstyle {
    _ce_refusal B_`o' area "mpg turn" `o'
}
foreach o in clstyle connect cmissing {
    _ce_refusal B_`o' connected "mpg turn" `o'
}
foreach o in dstyle dlstyle {
    _ce_refusal B_`o' dropline "mpg turn" `o'
}
_ce_refusal B_bmlinestyle rcap "lo hi" bmlinestyle

* F_query: read only.
quietly translator query gph2svg
foreach k in fontface fontfacesans fontfaceserif fontfacemono fontfacesymbol {
    global CEQ_`k' `"`r(`k')'"'
}

python:
import json, os, sys
from collections import Counter
from sfi import Macro

G = Macro.getGlobal
sys.path.insert(0, os.path.join(G("CE_REPO"), "scripts"))
from svg_truth import svg_document  # noqa: E402

work = G("CE_WORK")
written = [os.path.join(work, "git_head.txt")]
rows = {}
for rid in G("CE_IDS").split():
    stem = G("CEF_" + rid)
    rec = {"value": G("CEV_" + rid), "rc": int(float(G("CER_" + rid)))}
    if G("CEK_" + rid) == "fill":
        svg = os.path.join(work, stem + ".svg")
        rec["fill"] = None
        if os.path.exists(svg):
            written.append(svg)
            circ = [c for c in svg_document(svg)["circles"]
                    if c.get("fill") and c["fill"] != "none" and c.get("r")]
            if circ:
                rmax = max(c["r"] for c in circ)
                fills = Counter(c["fill"].lower() for c in circ
                                if c["r"] == rmax)
                rec["fill"] = fills.most_common(1)[0][0]
    else:
        logp = os.path.join(work, stem + ".log")
        rec["first_line"] = ""
        if os.path.exists(logp):
            written.append(logp)
            with open(logp, encoding="utf-8", errors="replace") as fh:
                lines = [ln.rstrip("\n") for ln in fh]
            body = [ln for ln in lines
                    if ln.strip() and not ln.lstrip().startswith(
                        ("log:", "log type:", "opened on:", "closed on:",
                         "name:", "-----", ". "))]
            rec["first_line"] = body[0].strip() if body else ""
    rows[rid] = rec
rows["F_query"] = {k: G("CEQ_" + k) for k in
                   ("fontface", "fontfacesans", "fontfaceserif",
                    "fontfacemono", "fontfacesymbol")}
try:
    with open(os.path.join(work, "git_head.txt"), encoding="utf-8") as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out = {"_meta": {"stata_version": G("CE_VERSION"), "born_date": G("CE_BORN"),
                 "source": "scripts/extract_colour_edges_truth.do",
                 "dash_commit": commit, "extracted": G("CE_WHEN"),
                 "scheme": "s2color"},
       "rows": rows}
with open(G("CE_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
for p in written:
    try:
        os.remove(p)
    except OSError:
        pass
try:
    os.rmdir(work)
except OSError:
    pass
print("colour_edges_truth: wrote %d rows" % len(rows))
end
