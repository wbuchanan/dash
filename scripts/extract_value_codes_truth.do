*! extract_value_codes_truth.do -- twoway's return codes and words for the
*! option values dash refused in its own words, and twoway's drawing of the
*! values dash's own bounds refused; written to
*! test/fixtures/value_codes_truth.json (WP-35 section 35-05: basic:PT-9,
*! basic:PT-13).  Read by scripts/gen_value_refusal_table.py, which writes
*! dash_parse.mata's _dash_tw_value_tab() from it and from
*! test/fixtures/value_truth.json, and by test_option_validation.cscript
*! Q3505-1 and test_wp35_truth.cscript's S05 blocks.
*!
*! probes: one `capture noisily twoway ...' per key (sysuse auto, set
*! graphics off, drawn): its rc, its first line (the first non-blank line
*! of its output) and its non-blank lines joined by a blank.  A probe with
*! a reference command is drawn under `set seed 1' and exported as SVG, as
*! is its reference, and both files' md5 recorded: equal means twoway draws
*! the value as it draws the reference.
*! per_type: lwidth(-1), mlwidth(-1) and msangle(400) on each of the
*! forty-four plot types: rc, first line, and (rc 0) whether the picture
*! equals the same command without the option.
*! vt_first: the first line of each probe test/fixtures/value_truth.json
*! records as refused (that fixture holds the joined message only).
*!
*! Run (never the GUI; the slot wrapper of scripts/stata_slot.sh):
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_value_codes_truth.do
*! Probe logs and SVGs go to c(tmpdir).

clear all
set more off
set linesize 255

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zc_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zc_bad' {
    display as error "extract_value_codes_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_value_codes_truth.do: `_zc_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZC_REPO "`repo'"
global ZC_SVER = c(stata_version)
global ZC_BORN "`c(born_date)'"
global ZC_DATE "`c(current_date)'"
tempfile gh
shell git -C "`repo'" rev-parse HEAD > "`gh'"
tempname fh
file open `fh' using "`gh'", read text
file read `fh' zc_commit
file close `fh'
global ZC_COMMIT "`zc_commit'"
local work "`c(tmpdir)'dash_value_codes_truth"
capture mkdir "`work'"
global ZC_WORK "`work'"
global ZC_IDS ""

set graphics off
capture log close _all

* The data, made again before every probe and reference: twoway rbar's
* barwidth(.) refusal leaves the data in memory changed (measured: every
* probe after it found no variable weight).
capture program drop _zc_data
program define _zc_data
    quietly sysuse auto, clear
    quietly gen yl = mpg - 1
    quietly gen yh = mpg + 1
    quietly gen t = _n
    quietly tsset t
end

* _zc_probe id "command" ["reference command"]: rc and log; with a
* reference, both drawn under set seed 1 and exported as SVG.
capture program drop _zc_probe
program define _zc_probe
    args id cmd ref
    capture graph drop _all
    _zc_data
    set seed 1
    quietly log using `"${ZC_WORK}/p_`id'.log"', text replace name(zc)
    capture noisily `cmd'
    local rc = _rc
    quietly log close zc
    local svg 0
    if `rc' == 0 & `"`ref'"' != "" {
        quietly graph export `"${ZC_WORK}/p_`id'.svg"', replace
        capture graph drop _all
        _zc_data
        set seed 1
        quietly `ref'
        quietly graph export `"${ZC_WORK}/r_`id'.svg"', replace
        local svg 1
    }
    capture graph drop _all
    tempname fh
    file open `fh' using `"${ZC_WORK}/p_`id'.rc"', write text replace
    file write `fh' "`rc'" _n "`svg'" _n `"`cmd'"' _n `"`ref'"' _n
    file close `fh'
    global ZC_IDS "${ZC_IDS} `id'"
end

* basic:PT-9: codes and words not in value_truth.json.
_zc_probe mlabel_dotdot `"twoway scatter mpg weight, mlabel(make..)"'
_zc_probe rbar_barwidth_missing `"twoway rbar mpg turn weight, barwidth(.)"'
_zc_probe lfit_n_0 `"twoway lfit mpg weight, n(0)"'
_zc_probe lfit_n_abc `"twoway lfit mpg weight, n(abc)"'
_zc_probe lfit_n_2_5 `"twoway lfit mpg weight, n(2.5)"'
_zc_probe lpoly_n_100 `"twoway lpoly mpg weight, n(100)"'
* n() on the types whose words value_truth.json does not hold.
_zc_probe kdensity_n_0 `"twoway kdensity mpg, n(0)"'
_zc_probe kdensity_n_abc `"twoway kdensity mpg, n(abc)"'
_zc_probe kdensity_n_2_5 `"twoway kdensity mpg, n(2.5)"'
_zc_probe mspline_n_0 `"twoway mspline mpg weight, n(0)"'
_zc_probe mspline_n_301 `"twoway mspline mpg weight, n(301)"'
_zc_probe mspline_n_abc `"twoway mspline mpg weight, n(abc)"'
_zc_probe mspline_n_2_5 `"twoway mspline mpg weight, n(2.5)"'
_zc_probe mband_n_0 `"twoway mband mpg weight, n(0)"'
_zc_probe lwidth_mult_line `"twoway line mpg weight, lwidth(*40000)"'
* Where the multiplier's bound lies, and barwidth() below -1.
_zc_probe lwidth_mult_line_20000 `"twoway line mpg weight, lwidth(*20000)"'
_zc_probe lwidth_mult_line_10001 `"twoway line mpg weight, lwidth(*10001)"'
_zc_probe lwidth_mult_line_5000 `"twoway line mpg weight, lwidth(*5000)"'
_zc_probe barwidth_m2_ref `"twoway bar mpg foreign, barwidth(-2)"' `"twoway bar mpg foreign"'
_zc_probe jitterseed_abc `"twoway scatter mpg weight, jitter(5) jitterseed(abc)"' `"twoway scatter mpg weight, jitter(5)"'
* basic:PT-13: the values dash's own bounds refused, against a reference.
_zc_probe jitter_150 `"twoway scatter mpg weight, jitter(150)"' `"twoway scatter mpg weight"'
_zc_probe jitter_m3_ref `"twoway scatter mpg weight, jitter(-3)"' `"twoway scatter mpg weight"'
_zc_probe jitter_abc_ref `"twoway scatter mpg weight, jitter(abc)"' `"twoway scatter mpg weight"'
_zc_probe jitterseed_m1 `"twoway scatter mpg weight, jitter(5) jitterseed(-1)"'
_zc_probe barwidth_m1_ref `"twoway bar mpg foreign, barwidth(-1)"' `"twoway bar mpg foreign"'
_zc_probe barwidth_0 `"twoway bar mpg foreign, barwidth(0)"' `"twoway bar mpg foreign"'
_zc_probe aspectratio_m1_ref `"twoway scatter mpg weight, aspectratio(-1)"' `"twoway scatter mpg weight"'
_zc_probe msize_1e400_ref `"twoway scatter mpg weight, msize(1e400)"' `"twoway scatter mpg weight"'
* Where a value does not draw its reference, the value it draws as.
_zc_probe msize_1e400_vs0 `"twoway scatter mpg weight, msize(1e400)"' `"twoway scatter mpg weight, msize(0)"'
_zc_probe aspectratio_m1_vs1 `"twoway scatter mpg weight, aspectratio(-1)"' `"twoway scatter mpg weight, aspectratio(1)"'
* A picture twoway draws differently each time cannot be compared.
_zc_probe contourline_self `"twoway contourline mpg weight length"' `"twoway contourline mpg weight length"'

* The forty-four types (applicability_truth.json's), their commands.
local types scatter line connected area bar spike dropline dot tsline tsrline ///
    rarea rbar rspike rcap rline rconnected rcapsym rscatter rpcap rpspike ///
    contour contourline ///
    pcspike pccapsym pcarrow pcbarrow pcscatter pci pcarrowi scatteri ///
    lfit qfit lfitci qfitci fpfit fpfitci lowess lpoly lpolyci mspline mband ///
    kdensity histogram function
global ZC_TYPES "`types'"
local pt_opts lwidth_neg mlwidth_neg msangle_400
local o_lwidth_neg "lwidth(-1)"
local o_mlwidth_neg "mlwidth(-1)"
local o_msangle_400 "msangle(400)"
foreach t of local types {
    local a "`t' mpg weight"
    if "`t'" == "tsline" local a "tsline mpg"
    else if "`t'" == "tsrline" local a "tsrline yl yh"
    else if inlist("`t'", "rarea", "rbar", "rspike", "rcap", "rline", "rconnected", "rcapsym", "rscatter") {
        local a "`t' yl yh weight"
    }
    else if inlist("`t'", "rpcap", "rpspike") local a "`t' yl yh mpg weight"
    else if inlist("`t'", "contour", "contourline") local a "`t' mpg weight length"
    else if inlist("`t'", "pcspike", "pccapsym", "pcarrow", "pcbarrow", "pcscatter") {
        local a "`t' mpg weight trunk turn"
    }
    else if inlist("`t'", "pci", "pcarrowi") local a "`t' 20 2000 30 4000"
    else if "`t'" == "scatteri" local a "scatteri 20 2000"
    else if inlist("`t'", "kdensity", "histogram") local a "`t' mpg"
    else if "`t'" == "function" local a "function y = x"
    foreach o of local pt_opts {
        _zc_probe `o'__`t' `"twoway `a', `o_`o''"' `"twoway `a'"'
    }
}

* vt_first: value_truth.json's refused probes, run again for their first line.
python:
import json, os
from sfi import Macro
with open(os.path.join(Macro.getGlobal("ZC_REPO"), "test", "fixtures", "value_truth.json"), encoding="utf-8") as fh:
    _zc_vt = json.load(fh)["twoway"]
with open(os.path.join(Macro.getGlobal("ZC_WORK"), "vt_list.txt"), "w", encoding="utf-8") as fh:
    for p in _zc_vt:
        if p["rc"]:
            assert "|" not in p["command"] and "\x60" not in p["command"], p["id"]
            fh.write("%s|%s\n" % (p["id"], p["command"]))
end
global ZC_VT ""
tempname vf
file open `vf' using `"${ZC_WORK}/vt_list.txt"', read text
file read `vf' line
while r(eof) == 0 {
    gettoken vid rest : line, parse("|")
    gettoken bar rest : rest, parse("|")
    _zc_probe vt__`vid' `"`rest'"'
    global ZC_VT "${ZC_VT} `vid'"
    file read `vf' line
}
file close `vf'

python:
import hashlib, json, os, re
from sfi import Macro
G = Macro.getGlobal
work = G("ZC_WORK")
SKIP = ("name:", "log:", "log type:", "opened on:", "closed on:")


def body(path):
    out = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for ln in fh.read().splitlines():
            s = " ".join(ln.split())
            if not s or s.startswith(SKIP) or s.startswith((". ", "> ")):
                continue
            out.append(s)
    return out


def md5(path):
    # Stata names each clip path and its path with eight random letters
    # (path_BBROytYk): those names are made one before hashing.
    with open(path, "rb") as fh:
        svg = fh.read()
    svg = re.sub(rb"\b(path|clipPath)_[A-Za-z]{8}\b", rb"\1_ID", svg)
    return hashlib.md5(svg).hexdigest()


def read(pid):
    with open(os.path.join(work, "p_%s.rc" % pid), encoding="utf-8") as fh:
        rc, svg, cmd, ref = fh.read().split("\n")[:4]
    ls = body(os.path.join(work, "p_%s.log" % pid))
    row = {"command": cmd, "rc": int(rc), "first": ls[0] if ls else "",
           "message": " ".join(ls)}
    if ref:
        row["reference"] = ref
    if svg == "1":
        a = md5(os.path.join(work, "p_%s.svg" % pid))
        b = md5(os.path.join(work, "r_%s.svg" % pid))
        row["svg_md5"] = a
        row["ref_md5"] = b
        row["equal"] = a == b
    return row


probes, per_type, vt_first = {}, {}, {}
vt = set(G("ZC_VT").split())
for pid in G("ZC_IDS").split():
    if pid.startswith("vt__"):
        vt_first[pid[4:]] = read(pid)["first"]
    elif "__" in pid:
        key, t = pid.split("__", 1)
        per_type.setdefault(key, {})[t] = read(pid)
    else:
        probes[pid] = read(pid)
out = {
    "_meta": {
        "stata_version": G("ZC_SVER"), "born_date": G("ZC_BORN"),
        "dash_commit": G("ZC_COMMIT").strip(), "extracted": G("ZC_DATE"),
        "source": "scripts/extract_value_codes_truth.do",
        "stata": "console binary (stata_slot.sh), set graphics off, sysuse auto, drawn",
        "purpose": "twoway's rc and first line for the option values dash refused in its own words (basic:PT-9), and twoway's drawing of the values dash's own bounds refused (basic:PT-13). Read by scripts/gen_value_refusal_table.py and the Q3505 cases.",
        "how": "one \x60capture noisily twoway ...\x60 per probe; first = the first non-blank output line; a probe with a reference is drawn under \x60set seed 1\x60, exported as SVG and its md5 (random clip-path names made one) compared with the reference's",
        "types": G("ZC_TYPES").split(),
    },
    "probes": probes, "per_type": per_type, "vt_first": vt_first,
}
path = os.path.join(G("ZC_REPO"), "test", "fixtures", "value_codes_truth.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True, ensure_ascii=False)
    fh.write("\n")
print("wrote %s: %d probes, %d per-type sets, %d first lines" % (path, len(probes), len(per_type), len(vt_first)))
end
