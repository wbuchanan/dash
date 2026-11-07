*! extract_axis_scale_truth.do
*! WP-44 section 44-03: ground truth for the axis scale items -- off fill
*! (AX-7), the transform words twoway's graph fails on and scale style()
*! (AX-9), contradictory transforms in one copy (AX-10), log axes over
*! non-positive data (AX-11), range() on a log axis (MS-14), minmax on an
*! empty scale (DG-13) and spans that overflow (DG-11), for
*! test/fixtures/axis_scale_truth.json.
*!
*! WHY THIS EXISTS
*!
*! The tests compare dash with what twoway does, never with a guess.
*! This script records it: each key's rc and error line, and for a drawn
*! graph its plot region, axis texts and grid lines.
*!
*! Output: test/fixtures/axis_scale_truth.json
*!
*! Run with:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_axis_scale_truth.do
*!
*! METHOD
*!
*! `_as_run key data prep cmd' loads the data set (none when data is "-"),
*! runs prep, runs cmd under the stcolor scheme for the session only with
*! its output in a text log of its own, and exports a drawn graph to SVG.
*! `_as_dg11 a b' builds the two-row data set the overflow keys draw.  The
*! trailing python: block reads files only: each key's rc and the last
*! line of its log that is not an r() line, and through
*! scripts/svg_truth.py the plot region, the texts below it (x labels),
*! left of it (y labels), the number of grid rows and columns inside it
*! (a grid line is written as dashed segments) and the lines on its edges.
*! ---------------------------------------------------------------------------

clear all
set graphics off
set more off
set linesize 255
version 19

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_as_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_as_bad' {
    display as error "extract_axis_scale_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _as_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_as_rc' | _rc {
    local _as_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_axis_scale_truth.do: `_as_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global AS_REPO "`repo'"
global AS_OUT "${AS_REPO}/test/fixtures/axis_scale_truth.json"

local work "`c(tmpdir)'dash_axis_scale_probe"
capture mkdir "`work'"
global AS_WORK "`work'"

quietly shell git -C "${AS_REPO}" rev-parse HEAD > "${AS_WORK}/git_head.txt"
global AS_VERSION "`c(stata_version)'"
global AS_BORN "`c(born_date)'"
global AS_WHEN "`c(current_date)' `c(current_time)'"

capture program drop _as_dg11
program define _as_dg11
    args a b
    clear
    quietly set obs 2
    quietly generate double y = cond(_n == 1, `a', `b')
    quietly generate double y1 = cond(_n == 1, `a', .)
    quietly generate double y2 = cond(_n == 2, `b', .)
    quietly generate x = _n
end

capture program drop _as_run
program define _as_run
    args key data prep cmd
    if "`data'" != "-" {
        sysuse `data', clear
    }
    `prep'
    set scheme stcolor
    capture graph drop u43s
    capture erase "${AS_WORK}/`key'.txt"
    quietly log using "${AS_WORK}/`key'.txt", text replace name(_as_k)
    capture noisily `macval(cmd)' name(u43s, replace)
    local rc = _rc
    quietly log close _as_k
    global AS_R_`key' "`rc'"
    global AS_C_`key' `"`macval(cmd)'"'
    global AS_P_`key' `"`prep'"'
    global AS_D_`key' "`data'"
    global AS_KEYS "${AS_KEYS} `key'"
    if !`rc' {
        quietly graph export "${AS_WORK}/`key'.svg", replace
    }
end

global AS_KEYS ""

* AX-7: off fill keeps the axis's space.
_as_run ax7_plain auto "" "scatter mpg weight,"
_as_run ax7_off auto "" "scatter mpg weight, yscale(off)"
_as_run ax7_off_fill auto "" "scatter mpg weight, yscale(off fill)"
_as_run ax7_fill auto "" "scatter mpg weight, yscale(fill)"
_as_run ax7_x_off auto "" "scatter mpg weight, xscale(off)"
_as_run ax7_x_off_fill auto "" "scatter mpg weight, xscale(off fill)"

* AX-9: the transform words twoway's graph fails on; scale style().
_as_run ax9_atanh_y auto "" "scatter mpg weight, yscale(atanh)"
_as_run ax9_logit_y auto "" "scatter mpg weight, yscale(logit)"
_as_run ax9_log1m_y auto "" "scatter mpg weight, yscale(log1m)"
_as_run ax9_log1_y auto "" "scatter mpg weight, yscale(log1)"
_as_run ax9_atanh_x auto "" "scatter mpg weight, xscale(atanh)"
_as_run ax9_alt_atanh auto "" "scatter mpg weight, yscale(alt atanh)"
_as_run ax9_t_atanh sp500 "tsset date" "tsline close, tscale(atanh)"
_as_run ax9_z_contour sandstone "" "twoway contour depth northing easting, zscale(atanh)"
_as_run ax9_z_colorvar auto "" "scatter mpg weight, colorvar(price) zscale(logit)"
_as_run ax9_axis2 auto "" "twoway (scatter mpg weight) (scatter price weight, yaxis(2)), yscale(axis(2) logit)"
_as_run ax9_log_then_logit auto "" "scatter mpg weight, yscale(log) yscale(logit)"
_as_run ax9_logit_then_log auto "" "scatter mpg weight, yscale(logit) yscale(log)"
_as_run ax9_log1m_then_no auto "" "scatter mpg weight, yscale(log1m) yscale(nolog1m)"
_as_run ax9_atanh_then_no auto "" "scatter mpg weight, yscale(atanh) yscale(noatanh)"
_as_run ax9_logit_then_nolog auto "" "scatter mpg weight, yscale(logit) yscale(nolog)"
_as_run ax9_logit_then_alt auto "" "scatter mpg weight, yscale(logit) yscale(alt)"
_as_run ax9_no_forms auto "" "scatter mpg weight, yscale(noatanh nologit nolog1m)"
_as_run ax9_noatanh auto "" "scatter mpg weight, yscale(noatanh)"
_as_run ax9_nolog1m_x auto "" "scatter mpg weight, xscale(nolog1m)"
_as_run ax9_style_nogrid auto "" "scatter mpg weight, yscale(style(vertical_nogrid))"
_as_run ax9_style_noline auto "" "scatter mpg weight, xscale(style(horizontal_noline))"
_as_run ax9_style_bogus auto "" "scatter mpg weight, yscale(style(bogus_style))"

* AX-10: contradictory transforms in one copy.
_as_run ax10_log_nolog auto "" "scatter mpg weight, yscale(log nolog)"
_as_run ax10_atanh_log auto "" "scatter mpg weight, yscale(atanh log)"
_as_run ax10_three auto "" "scatter mpg weight, yscale(log logit atanh)"
_as_run ax10_noatanh_atanh auto "" "scatter mpg weight, yscale(noatanh atanh)"
_as_run ax10_across auto "" "scatter mpg weight, yscale(log) yscale(nolog)"
_as_run ax10_log_log auto "" "scatter mpg weight, yscale(log log)"
_as_run ax10_logit_logit auto "" "scatter mpg weight, yscale(logit logit)"
_as_run ax10_nolog_nolog auto "" "scatter mpg weight, yscale(nolog nolog)"
_as_run ax10_x_log_nolog auto "" "scatter mpg weight, xscale(nolog log)"

* AX-11: a log axis over non-positive data.
_as_run ax11_c20 auto "generate z = mpg - 25" "scatter z weight, yscale(log)"
_as_run ax11_with_n auto "generate z = mpg - 25" "scatter z weight, yscale(log) ylabel(#5)"
_as_run ax11_positive auto "" "scatter mpg weight, yscale(log)"

* MS-14: range() on a log axis.
_as_run ms14_b04 auto "" "scatter mpg weight, xscale(range(1000)) xscale(log)"
_as_run ms14_b2 auto "" "scatter weight mpg, yscale(log range(1000 20000))"
_as_run ms14_with_n auto "" "scatter weight mpg, yscale(log range(1000 20000)) ylabel(#5)"

* DG-13: minmax on an empty scale.
_as_run dg13_s07 auto "" "scatter mpg weight if price < 0, xlabel(#5) ylabel(minmax)"
_as_run dg13_log_empty auto "" "scatter mpg weight if price < 0, xlabel(#5) ylabel(minmax) yscale(log)"

* DG-11: spans that overflow.
_as_run dg11_pm8e307 - "_as_dg11 8e307 -8e307" "scatter y x,"
_as_run dg11_pm4_5e307 - "_as_dg11 4.5e307 -4.5e307" "scatter y x,"
_as_run dg11_pm4_4e307 - "_as_dg11 4.4e307 -4.4e307" "scatter y x,"
_as_run dg11_one_signed - "_as_dg11 0 8e307" "scatter y x,"
_as_run dg11_two_plots - "_as_dg11 8e307 -8e307" "twoway (scatter y1 x) (scatter y2 x),"
_as_run dg11_x_axis - "_as_dg11 8e307 -8e307" "scatter x y,"


python:
import json, os, re, sys
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


sys.path.insert(0, os.path.join(G("AS_REPO"), "scripts"))
import svg_truth

work = G("AS_WORK")


def error_line(key):
    try:
        with open(os.path.join(work, key + ".txt"), encoding="utf-8",
                  errors="replace") as fh:
            lines = [ln.rstrip() for ln in fh]
    except OSError:
        return None
    keep = [ln for ln in lines if ln.strip()
            and not re.match(r"^\s*r\(\d+\);?$", ln)
            and not ln.lstrip().startswith(("name:", "log:", "log type:",
                                            "opened on:", "closed on:"))
            and not set(ln.strip()) <= set("-")]
    return keep[-1].strip() if keep else None


def note_lines(key):
    try:
        with open(os.path.join(work, key + ".txt"), encoding="utf-8",
                  errors="replace") as fh:
            return [ln.strip() for ln in fh if "note:" in ln.lower()
                    or "not found" in ln.lower()]
    except OSError:
        return []


def drawn(key):
    doc = svg_truth.svg_document(os.path.join(work, key + ".svg"))
    pr = doc["plotregion"]
    t = [x for x in doc["texts"] if x["x"] is not None and x["y"] is not None]
    w = pr["right"] - pr["left"]
    h = pr["bottom"] - pr["top"]
    def grid(lines, a, b, lo, hi):
        return len({round(ln[a], 1) for ln in lines
                    if lo + 0.5 < ln[a] < hi - 0.5
                    and ln["stroke"] not in (None, "#000000", "none")})
    hgrid = grid(doc["hlines"], "y1", "y1", pr["top"], pr["bottom"])
    vgrid = grid(doc["vlines"], "x1", "x1", pr["left"], pr["right"])
    bottom_line = [ln["stroke"] for ln in doc["hlines"]
                   if abs(ln["y1"] - pr["bottom"]) < 0.5
                   and abs(ln["x2"] - ln["x1"]) > 0.5 * w]
    left_line = [ln["stroke"] for ln in doc["vlines"]
                 if abs(ln["x1"] - pr["left"]) < 0.5
                 and abs(ln["y2"] - ln["y1"]) > 0.5 * h]
    return {
        "plotregion": {k: pr[k] for k in ("left", "top", "right", "bottom")},
        "canvas": doc["canvas"],
        "x": [x["text"] for x in t if x["y"] > pr["bottom"]
              and x["rotate"] is None],
        "y": [x["text"] for x in t if x["x"] < pr["left"]],
        "y_pos": [[x["text"], x["y"]] for x in t if x["x"] < pr["left"]
                  and x["rotate"] is None],
        "hgrid": hgrid,
        "vgrid": vgrid,
        "bottom_line": bottom_line,
        "left_line": left_line,
    }


out = {"graphs": {}}
for key in G("AS_KEYS").split():
    rc = int(G("AS_R_" + key))
    row = {"rc": rc, "command": G("AS_C_" + key), "prep": G("AS_P_" + key),
           "data": G("AS_D_" + key), "notes": note_lines(key)}
    if rc:
        row["error"] = error_line(key)
    else:
        row.update(drawn(key))
        os.remove(os.path.join(work, key + ".svg"))
    try:
        os.remove(os.path.join(work, key + ".txt"))
    except OSError:
        pass
    out["graphs"][key] = row

try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("AS_VERSION"), "born_date": G("AS_BORN"),
                "dash_commit": commit, "extracted": G("AS_WHEN"),
                "scheme": "stcolor",
                "source": "scripts/extract_axis_scale_truth.do"}
with open(G("AS_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True, ensure_ascii=False)
    fh.write("\n")
print("wrote", G("AS_OUT"))
end
