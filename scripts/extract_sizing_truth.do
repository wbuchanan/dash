*! extract_sizing_truth.do -- WP-31 section 32 (D5, E11): measure what
*! twoway draws for scale(), fxsize()/fysize(), aspectratio(#[,
*! placement()]), xoverhangs/yoverhangs and the size reference, and the
*! return codes and words of their refusals, from twoway's own SVG export
*! (the plot region and graph region are marked by sentinel outline
*! colours) and its printed lines.  twoway only: the output is the same
*! before and after dash changes.  S33's lwidth() bound (lw_*) and the
*! aspectratio() abbreviations (A3c, abbrev_*) are recorded beside them.
*!
*! Output: test/fixtures/sizing_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_sizing_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zs_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zs_bad' {
    display as error "extract_sizing_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zs_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zs_rc' | _rc {
    local _zs_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_sizing_truth.do: `_zs_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZS_REPO "`repo'"
global ZS_OUT "${ZS_REPO}/test/fixtures/sizing_truth.json"

local work "`c(tmpdir)'dash_sizing_probe"
capture mkdir "`work'"
global ZS_WORK "`work'"


quietly shell git -C "${ZS_REPO}" rev-parse HEAD > "${ZS_WORK}/git_head.txt"
global ZS_VERSION "`c(stata_version)'"
global ZS_BORN "`c(born_date)'"
global ZS_WHEN "`c(current_date)' `c(current_time)'"

* _zs_run key cmd: run `cmd' with its printed lines in a log; the rc in
* ZS_RC_<key>; the graph exported to <key>.svg when it drew.
capture program drop _zs_run
program define _zs_run
    gettoken key 0 : 0
    quietly log using "${ZS_WORK}/`key'.log", text replace name(zsref)
    capture noisily `0'
    local rc = _rc
    display as text "{p_end}"
    quietly log close zsref
    global ZS_RC_`key' "`rc'"
    if `rc' == 0 {
        capture graph describe zs1
        if _rc == 0 {
            quietly graph export "${ZS_WORK}/`key'.svg", replace
            graph drop zs1
        }
    }
    global ZS_KEYS "${ZS_KEYS} `key'"
end
global ZS_KEYS ""

sysuse auto, clear
set scheme s2color
local nm "name(zs1, replace)"
* Sentinels: the plot region's outline #010203, the graph region's #040506.
local sn `"plotregion(lcolor("1 2 3")) graphregion(lcolor("4 5 6"))"'
local sc "twoway scatter mpg weight"

_zs_run base      `sc', title("T") `sn' `nm'
_zs_run scale_15  `sc', title("T") scale(1.5) `sn' `nm'
_zs_run scale_05  `sc', title("T") scale(0.5) `sn' `nm'
_zs_run scale_bad_0   `sc', scale(0)
_zs_run scale_bad_neg `sc', scale(-1)
_zs_run scale_bad_x   `sc', scale(x)
_zs_run fysize_50 `sc', fysize(50) `sn' `nm'
_zs_run fxsize_50 `sc', fxsize(50) `sn' `nm'
_zs_run fx_100    `sc', fxsize(100) `sn' `nm'
_zs_run fx_bad_0   `sc', fxsize(0)
_zs_run fx_bad_150 `sc', fxsize(150)
_zs_run fx_bad_x   `sc', fxsize(x)
_zs_run fy_bad_0   `sc', fysize(0)
_zs_run fy_bad_150 `sc', fysize(150)
_zs_run fy_bad_x   `sc', fysize(x)
_zs_run ar_1       `sc', aspectratio(1) `sn' `nm'
_zs_run ar_sizes   `sc', aspectratio(1) xsize(8) ysize(4) `sn' `nm'
foreach p in c e w ne sw {
    _zs_run ar_place_`p' `sc', aspectratio(1, placement(`p')) xsize(8) ysize(4) `sn' `nm'
}
foreach p in c n s {
    _zs_run ar_vplace_`p' `sc', aspectratio(0.25, placement(`p')) xsize(4) ysize(4) `sn' `nm'
}
_zs_run aspect_bad_sub   `sc', aspectratio(1, foo)
_zs_run aspect_bad_place `sc', aspectratio(1, placement(xx))
_zs_run aspect_bad_num   `sc', aspectratio(x)
_zs_run overhang_x0 `sc', xlabel(1760 "a very long first label" 4840) `sn' `nm'
_zs_run overhang_x1 `sc', xlabel(1760 "a very long first label" 4840) xoverhangs `sn' `nm'
_zs_run overhang_y0 `sc', ylabel(12 41, labsize(huge) angle(0)) `sn' `nm'
_zs_run overhang_y1 `sc', ylabel(12 41, labsize(huge) angle(0)) yoverhangs `sn' `nm'
_zs_run ref_def `sc', title("T", size(5)) `sn' `nm'
_zs_run ref_84  `sc', title("T", size(5)) xsize(8) ysize(4) `sn' `nm'
_zs_run ref_48  `sc', title("T", size(5)) xsize(4) ysize(8) `sn' `nm'
_zs_run ref_88  `sc', title("T", size(5)) xsize(8) ysize(8) `sn' `nm'
* S33's lwidth() bound (TR-33.10).
_zs_run lw_10000 twoway line mpg weight, sort lwidth(10000) `nm'
_zs_run lw_20000 twoway line mpg weight, sort lwidth(20000)
* A3c: twoway's minimum abbreviation of aspectratio().
foreach a in as asp aspe aspec aspect aspectr aspectra aspectrat aspectrati {
    _zs_run abbrev_`a' `sc', `a'(1) `nm'
}

python:
import json, os, sys
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


sys.path.insert(0, os.path.join(G("ZS_REPO"), "scripts"))
import svg_truth  # noqa: E402
import svg_chrome  # noqa: E402

work = G("ZS_WORK")


def log_lines(key):
    p = os.path.join(work, key + ".log")
    with open(p, encoding="utf-8", errors="replace") as fh:
        lines = [ln.rstrip() for ln in fh
                 if ln.strip() and not ln.lstrip().startswith((".", "> "))
                 and "log:" not in ln and "log type:" not in ln
                 and "opened on:" not in ln and "closed on:" not in ln
                 and "name:" not in ln and not ln.startswith("---")
                 and ln.strip() != "{p_end}"]
    os.remove(p)
    return lines


def box(r):
    if not r:
        return None
    return {k: round(r[k], 3) for k in ("left", "top", "right", "bottom")}


def facts(path):
    doc = svg_truth.svg_document(path)
    rec = {"canvas": doc["canvas"],
           "plot": box(svg_chrome.svg_region(path, "#010203")),
           "graph": box(svg_chrome.svg_region(path, "#040506"))}
    t = [d for d in doc["texts"] if d["text"] == "T"]
    rec["title_size"] = t[0]["size"] if t else None
    ticks = [d for d in doc["texts"] if d["text"] in ("2,000", "3,000", "4,000", "5,000")]
    rec["xlabel_size"] = ticks[0]["size"] if ticks else None
    rs = sorted({c["r"] for c in doc["circles"] if c["r"]})
    rec["marker_r"] = rs[0] if rs else None
    widths = sorted({d["width"] for d in doc["hlines"] + doc["vlines"]
                     if d["width"]})
    rec["line_widths"] = widths
    return rec


out = {}
for key in G("ZS_KEYS").split():
    rec = {"rc": int(G("ZS_RC_" + key)), "lines": log_lines(key)}
    svg = os.path.join(work, key + ".svg")
    if os.path.exists(svg):
        rec.update(facts(svg))
        os.remove(svg)
    out[key] = rec
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZS_VERSION"), "born_date": G("ZS_BORN"),
                "dash_commit": commit, "extracted": G("ZS_WHEN"),
                "source": "scripts/extract_sizing_truth.do"}
with open(G("ZS_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZS_OUT"))
end
