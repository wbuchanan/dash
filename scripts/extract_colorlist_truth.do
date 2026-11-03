*! extract_colorlist_truth.do -- WP-42 CV-17: measure how twoway draws a
*! colorlist() of quoted RGB colours under colorvar(), a list mixing named
*! and quoted colours, and contour's ccolors() of quoted RGB colours.
*! twoway only: the output is the same before and after dash changes.
*!
*! Output: test/fixtures/colorlist_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_colorlist_truth.do
*!
*! PROBES (scheme s2color).  Each drawn probe's exported SVG is read for
*! the fills of its circles, paths and rects (svg_fills: fill -> count),
*! every `fill:#rrggbb' style it writes, lower-cased (style_fills: a
*! contour's bands are polygons styled so, which svg_fills does not read),
*! and its printed lines.
*!   L8   sysuse auto: the corpus example ex-feature_tour-eaf70b99,
*!        colorvar(price) colorlevels(8) colorlist(eight quoted RGB)
*!   LM   sysuse auto: colorvar(rep78) colordiscrete
*!        colorlist("255 0 0" green "0 0 255")
*!   C3   sysuse sandstone: contour depth northing easting, levels(3)
*!        ccolors("255 0 0" "0 255 0" "0 0 255")
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zp_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zp_bad' {
    display as error "extract_colorlist_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_colorlist_truth.do: `_zp_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZP_REPO "`repo'"
global ZP_OUT "${ZP_REPO}/test/fixtures/colorlist_truth.json"

local work "`c(tmpdir)'dash_colorlist_probe"
capture mkdir "`work'"
global ZP_WORK "`work'"

quietly shell git -C "${ZP_REPO}" rev-parse HEAD > "${ZP_WORK}/git_head.txt"
global ZP_VERSION "`c(stata_version)'"
global ZP_BORN "`c(born_date)'"
global ZP_WHEN "`c(current_date)' `c(current_time)'"

* _zp_run key cmd: run `cmd' with its printed lines in a log; the rc in
* ZP_RC_<key>, the command in ZP_CMD_<key>; the graph exported to
* <key>.svg when it drew.
capture program drop _zp_run
program define _zp_run
    gettoken key 0 : 0
    quietly log using "${ZP_WORK}/`key'.log", text replace name(zpref)
    capture noisily `0'
    local rc = _rc
    display as text "{p_end}"
    quietly log close zpref
    global ZP_RC_`key' "`rc'"
    global ZP_CMD_`key' `"`0'"'
    if `rc' == 0 {
        capture graph describe zp1
        if _rc == 0 {
            quietly graph export "${ZP_WORK}/`key'.svg", replace
            graph drop zp1
        }
    }
    global ZP_KEYS "${ZP_KEYS} `key'"
end
global ZP_KEYS ""

set scheme s2color
local nm "name(zp1, replace)"

sysuse auto, clear
_zp_run L8 twoway scatter mpg weight, colorvar(price) colorlevels(8) colorlist("68 1 84" "70 50 126" "54 92 141" "39 127 142" "31 161 135" "74 193 109" "160 218 57" "253 231 37") `nm'
_zp_run LM twoway scatter mpg weight, colorvar(rep78) colordiscrete colorlist("255 0 0" green "0 0 255") `nm'

sysuse sandstone, clear
_zp_run C3 twoway contour depth northing easting, levels(3) ccolors("255 0 0" "0 255 0" "0 0 255") `nm'

python:
import json, os, re, sys
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


work = G("ZP_WORK")
sys.path.insert(0, os.path.join(G("ZP_REPO"), "scripts"))
from svg_truth import svg_fills  # noqa: E402


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


out = {"probes": {}}
for key in G("ZP_KEYS").split():
    rec = {"rc": int(G("ZP_RC_" + key)), "lines": log_lines(key),
           "command": G("ZP_CMD_" + key).replace(" name(zp1, replace)", "")}
    svg = os.path.join(work, key + ".svg")
    if os.path.exists(svg):
        rec["fills"] = {k: v["n"] for k, v in svg_fills(svg).items()}
        with open(svg, encoding="utf-8", errors="replace") as fh:
            sf = {}
            for m in re.findall(r"fill:(#[0-9A-Fa-f]{6})", fh.read()):
                sf[m.lower()] = sf.get(m.lower(), 0) + 1
        rec["style_fills"] = sf
        os.remove(svg)
    out["probes"][key] = rec
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZP_VERSION"), "born_date": G("ZP_BORN"),
                "dash_commit": commit, "extracted": G("ZP_WHEN"),
                "source": "scripts/extract_colorlist_truth.do"}
with open(G("ZP_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZP_OUT"))
end
