*! extract_pnum_truth.do -- WP-35 syn:SD-3: what twoway does with p1() ..
*! p20() after the plot groups' comma (twowaygraph_g.class hands p<k>() to
*! the k-th plot, each y of a varlist counted) and with p<j>() inside one
*! plot's options (twoway_yxview_parse.class gives it to the j-th y).
*!
*! For each probe: twoway's rc, its error lines (first line kept), and when
*! it draws, the number of marker fills equal to red (#ff0000) and blue
*! (#0000ff) in its graph export SVG (scripts/svg_truth.py's
*! svg_marker_fills; a legend key's marker is counted with the plot's).
*! twoway only: the output is the same before and after dash changes.
*!
*! Output: test/fixtures/pnum_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_pnum_truth.do
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
    display as error "extract_pnum_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_pnum_truth.do: `_zp_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZP_REPO "`repo'"
global ZP_OUT "${ZP_REPO}/test/fixtures/pnum_truth.json"

local work "`c(tmpdir)'dash_pnum_probe"
capture mkdir "`work'"
global ZP_WORK "`work'"


quietly shell git -C "${ZP_REPO}" rev-parse HEAD > "${ZP_WORK}/git_head.txt"
global ZP_VERSION "`c(stata_version)'"
global ZP_BORN "`c(born_date)'"
global ZP_WHEN "`c(current_date)' `c(current_time)'"
global ZP_SCHEME "`c(scheme)'"

* One probe: twoway <cmd>, its log (inside a program, so the command is
* not echoed into it) and, when it draws, its SVG.
capture program drop _zp_probe
program define _zp_probe
    args id cmd
    capture erase "${ZP_WORK}/`id'.svg"
    capture graph drop _all
    quietly log using "${ZP_WORK}/`id'.log", replace text name(zp)
    capture noisily twoway `cmd'
    local rc = _rc
    quietly log close zp
    if !`rc' quietly graph export "${ZP_WORK}/`id'.svg", replace as(svg)
    capture graph drop _all
    global ZP_RC_`id' `rc'
    global ZP_CMD_`id' `"`cmd'"'
end

sysuse auto, clear

local ids ""
foreach p in ///
    "g_p1|scatter mpg weight, p1(mcolor(red))" ///
    "g_p3|(scatter mpg weight) (scatter price weight) (scatter trunk weight), p3(mcolor(red))" ///
    "g_p19|scatter mpg weight, p19(mcolor(red))" ///
    "g_p20|scatter mpg weight, p20(mcolor(red))" ///
    "g_p21|scatter mpg weight, p21(mcolor(red))" ///
    "multi_y|scatter mpg trunk weight, p2(mcolor(red))" ///
    "multi_own|scatter mpg trunk weight, mcolor(blue green) p2(mcolor(red))" ///
    "plot_level|(scatter mpg trunk weight, p2(mcolor(red)))" ///
    "prec_own|scatter mpg weight, mcolor(blue) p1(mcolor(red))" ///
    "prec_grp|(scatter mpg weight, mcolor(blue)), p1(mcolor(red))" ///
    "twice|scatter mpg weight, p1(mcolor(red)) p1(mcolor(blue))" ///
    "bad_inner|scatter mpg weight, p1(nosuch(1))" ///
    "ci_after|(lfitci mpg weight) (scatter mpg weight), p3(mcolor(red))" ///
    "ci_nofit_after|(lfitci mpg weight, nofit) (scatter mpg weight), p2(mcolor(red))" ///
    "plot_n1|(scatter mpg weight, p2(mcolor(red)))" ///
    "plot_over|(scatter mpg weight, p3(mcolor(red)))" ///
    "order_p21|(scatter mpg weight, bogus), p21(mcolor(red))" ///
    "ci_p2|(lfitci mpg weight) (scatter mpg weight), p2(mcolor(red))" ///
    "ci_p1_band|(lfitci mpg weight), p1(fcolor(red))" ///
    "ci_p2_band|(lfitci mpg weight), p2(fcolor(red))" ///
    "own_prec|(scatter mpg weight, mcolor(blue) p1(mcolor(red)))" ///
    "own_vs_grp|(scatter mpg weight, p1(mcolor(blue))), p1(mcolor(red))" ///
    "own_twice|(scatter mpg weight, p1(mcolor(red)) p1(mcolor(blue)))" ///
    "own_p21|(scatter mpg weight, p21(mcolor(red)))" ///
    "g_p100|scatter mpg weight, p100(mcolor(red))" ///
    "g_empty|scatter mpg weight, p1()" ///
    "multi_short|scatter mpg trunk weight, mcolor(blue) p2(mcolor(red))" ///
    "bars_p2|scatter mpg weight || scatter price weight, p2(mcolor(red))" ///
    "bars_p1|scatter mpg weight, p2(mcolor(red)) || scatter price weight" {
    gettoken id rest : p, parse("|")
    gettoken bar cmd : rest, parse("|")
    _zp_probe `id' `"`cmd'"'
    local ids "`ids' `id'"
    display as text "ZP `id': rc ${ZP_RC_`id'}"
}
global ZP_IDS "`ids'"

python:
import json, os, sys
from sfi import Macro

sys.path.insert(0, os.path.join(Macro.getGlobal("ZP_REPO"), "scripts"))
import svg_truth


def G(k):
    return Macro.getGlobal(k)


W = G("ZP_WORK")


def lines(path):
    """The log's message lines: blank lines, the log's own header and the
    r(#); line aside."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return []
    out = []
    for s in (ln.strip() for ln in text.replace("\n> ", "").splitlines()):
        if not s or s.startswith("r(") or s.startswith("name:") \
                or s.startswith("log:") or s.startswith("log type:") \
                or s.startswith("opened on:") or s.startswith("closed on:") \
                or set(s) <= set("-"):
            continue
        out.append(s)
    return out


probes = {}
for pid in G("ZP_IDS").split():
    rc = int(G("ZP_RC_" + pid))
    msg = lines(os.path.join(W, pid + ".log"))
    rec = {"cmd": "twoway " + G("ZP_CMD_" + pid), "rc": rc,
           "first_line": (msg[0] if (rc and msg) else ""),
           "lines": (msg if rc else [])}
    if rc == 0:
        f = svg_truth.svg_marker_fills(os.path.join(W, pid + ".svg"))
        rec["red"] = f.get("#ff0000", {}).get("n", 0)
        rec["blue"] = f.get("#0000ff", {}).get("n", 0)
    else:
        rec["red"] = None
        rec["blue"] = None
    probes[pid] = rec

out = {
    "_about": ("Measured with " + G("ZP_VERSION") + " (console, batch, "
               "scheme " + G("ZP_SCHEME") + ") on sysuse auto: each probe is "
               "'capture noisily twoway <cmd>'; rc and its error lines "
               "(first_line the first) are recorded, and when it draws, "
               "'red' and 'blue' count the marker fills equal to #ff0000 "
               "and #0000ff in its graph export SVG "
               "(scripts/svg_truth.py svg_marker_fills: circles, paths and "
               "polygons, so a legend key's marker counts with its plot's). "
               "p<k>() after the comma goes to the k-th plot, each y of a "
               "varlist counted (twowaygraph_g.class); p<j>() inside a plot "
               "goes to its j-th y (twoway_yxview_parse.class)."),
    "probes": probes,
}
try:
    with open(os.path.join(W, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZP_VERSION"), "born_date": G("ZP_BORN"),
                "dash_commit": commit, "extracted": G("ZP_WHEN"),
                "source": "scripts/extract_pnum_truth.do"}
with open(G("ZP_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1)
    fh.write("\n")
for pid in G("ZP_IDS").split():
    for ext in (".log", ".svg"):
        try:
            os.remove(os.path.join(W, pid + ext))
        except OSError:
            pass
try:
    os.remove(os.path.join(W, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZP_OUT"))
end
