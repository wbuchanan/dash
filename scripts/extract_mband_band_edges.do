*! extract_mband_band_edges.do -- measure twoway mband's knots (the cross
*! medians _mbandgen computes) for bands(20) and bands(7) on 200 draws of
*! x = round(runiform(), .01) and y = round(rnormal(), .001) after set seed
*! 12345 (the WP-18 review): each graph is drawn with nodraw and its
*! plotted serset read back with serset use (float32), [x, y] per knot.
*! twoway only: the output is the same before and after dash changes.
*!
*! Output: test/fixtures/mband_band_edges.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_mband_band_edges.do
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
    display as error "extract_mband_band_edges.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_mband_band_edges.do: `_zm_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZM_REPO "`repo'"
global ZM_OUT "${ZM_REPO}/test/fixtures/mband_band_edges.json"

adopath ++ "${ZM_REPO}"
global dash_nobrowser 1

local work "`c(tmpdir)'dash_mband_probe"
capture mkdir "`work'"
global ZM_WORK "`work'"


quietly shell git -C "${ZM_REPO}" rev-parse HEAD > "${ZM_WORK}/git_head.txt"
global ZM_VERSION "`c(stata_version)'"
global ZM_BORN "`c(born_date)'"
global ZM_WHEN "`c(current_date)' `c(current_time)'"

clear
set seed 12345
set obs 200
generate double x = round(runiform(), .01)
generate double y = round(rnormal(), .001)

python:
from sfi import Data
ZM = {"x": [float(v) for v in Data.get("x")],
      "y": [float(v) for v in Data.get("y")]}


def grab(key):
    """The serset in memory (mband's y then x) as [x, y] knots."""
    names = [Data.getVarName(i) for i in range(Data.getVarCount())]
    iy, ix = names.index("y"), names.index("x")
    rows = Data.get(None, missingval=None)
    ZM[key] = [[float(r[ix]), float(r[iy])] for r in rows
               if r[ix] is not None and r[iy] is not None]
    print("ZM", key, names, len(ZM[key]))


end

foreach b in 20 7 {
    preserve
    capture graph drop _all
    serset clear
    quietly twoway mband y x, bands(`b') nodraw
    local id "`.Graph.plotregion1.plot1.serset.id'"
    serset set `id'
    serset use, clear
    python: grab("knots_bands`b'")
    restore
}

python:
import json, os
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


out = {
    "_about": ("twoway mband y x, bands(20) and bands(7) on 200 draws of x = "
               "round(runiform(), .01) and y = round(rnormal(), .001) after "
               "set seed 12345 (" + G("ZM_VERSION") + ", the WP-18 review). "
               "knots_* are the plotted serset of each graph (float32), read "
               "back with serset use: [x, y] per knot."),
    "x": ZM["x"],
    "y": ZM["y"],
    "knots_bands20": ZM["knots_bands20"],
    "knots_bands7": ZM["knots_bands7"],
}
work = G("ZM_WORK")
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZM_VERSION"), "born_date": G("ZM_BORN"),
                "dash_commit": commit, "extracted": G("ZM_WHEN"),
                "source": "scripts/extract_mband_band_edges.do"}
with open(G("ZM_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZM_OUT"))
end
