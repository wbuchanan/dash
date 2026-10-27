*! extract_bare_prefix_truth.do -- WP-31 section 08 (A1, A2, A4): measure
*! what twoway does with (1) the thirteen shorter plot-type spellings dash
*! took (ar ba sp lfi qfi low lpo fp kde dr tsl tsrl msp), (2) its own ten
*! spellings (sc li con hist rsc rl rcon fun mbands fn), (3) the prefix
*! with nothing after it (twoway, tw, graph twoway, twoway, title()) and
*! (4) the marker-label spellings ml() mla() mlab() mlabe() mlal()
*! mlalign(), each compared with the full option's saved .gph.  twoway
*! only: the output is the same before and after dash changes.
*!
*! Output: test/fixtures/bare_prefix_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_bare_prefix_truth.do
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
    display as error "extract_bare_prefix_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_bare_prefix_truth.do: `_zp_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZP_REPO "`repo'"
global ZP_OUT "${ZP_REPO}/test/fixtures/bare_prefix_truth.json"

local work "`c(tmpdir)'dash_bare_prefix_probe"
capture mkdir "`work'"
global ZP_WORK "`work'"


quietly shell git -C "${ZP_REPO}" rev-parse HEAD > "${ZP_WORK}/git_head.txt"
global ZP_VERSION "`c(stata_version)'"
global ZP_BORN "`c(born_date)'"
global ZP_WHEN "`c(current_date)' `c(current_time)'"

* _zp_run key cmd: run cmd under a log, record its rc in ZP_R_<key> and
* keep the log as <work>/<key>.log for the python block.
capture program drop _zp_run
program define _zp_run
    gettoken key 0 : 0
    quietly log using "${ZP_WORK}/`key'.log", replace text name(zp)
    capture noisily `0'
    local rc = _rc
    quietly log close zp
    global ZP_R_`key' "`rc'"
    global ZP_C_`key' `"`0'"'
    display as text "ZP `key': rc `rc'"
end

sysuse auto, clear
generate t = _n
tsset t
set scheme s2color

* (1) the thirteen spellings dash took and twoway does not
global ZP_EXTRAS "ar ba sp lfi qfi low lpo fp kde dr tsl tsrl msp"
foreach w of global ZP_EXTRAS {
    local v "mpg weight"
    if inlist("`w'", "kde", "tsl") local v "mpg"
    if "`w'" == "tsrl" local v "mpg turn"
    _zp_run x_`w' twoway `w' `v', nodraw
}

* (2) twoway's own spellings: the eight minimums and mbands/fn
global ZP_TWOWAYS "sc li con hist rsc rl rcon fun mbands fn"
foreach w of global ZP_TWOWAYS {
    local v "mpg weight"
    if "`w'" == "hist" local v "mpg"
    if inlist("`w'", "rsc", "rl", "rcon") local v "turn mpg weight"
    if inlist("`w'", "fun", "fn") local v "y = x"
    _zp_run w_`w' twoway `w' `v', nodraw
}

* (3) the bare prefix
_zp_run b_twoway twoway, name(zb1, replace)
global ZP_B1_PLOT1 "`.zb1.plotregion1.plot1.isa'"
_zp_run b_twoway_title twoway, title(T) name(zb2, replace)
global ZP_B2_TITLE "`.zb2.title.text[1]'"
global ZP_B2_PLOT1 "`.zb2.plotregion1.plot1.isa'"
_zp_run b_graph_twoway graph twoway, name(zb3, replace)
_zp_run b_tw tw, name(zb4, replace)
_zp_run b_gr_tw gr tw, name(zb5, replace)
_zp_run b_plain twoway
capture graph drop _all

* (4) marker-label spellings, each saved and compared with the full name
foreach c in "ml|ml(make)" "mla|mla(make)" "mla_center|mla(center)" ///
    "mlab|mlab(make)" "mlabe|mlabe(make)" "mlabel|mlabel(make)" ///
    "mlal|mlal(inside)" "mlali|mlali(inside)" "mlalign|mlalign(inside)" {
    gettoken key opt : c, parse("|")
    local opt = substr(`"`opt'"', 2, .)
    capture erase "${ZP_WORK}/m_`key'.gph"
    _zp_run m_`key' twoway scatter mpg weight, `opt' nodraw saving("${ZP_WORK}/m_`key'.gph", replace)
}

python:
import json, os, re
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


work = G("ZP_WORK")
SKIP = ("name:", "log:", "log type:", "opened on:", "closed on:")


def message(key):
    """The first line the command logged that is not the echoed command."""
    path = os.path.join(work, key + ".log")
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = [ln.rstrip() for ln in fh]
    except OSError:
        return ""
    for ln in lines:
        s = ln.strip()
        if not s or set(s) <= set("-") or s.startswith(SKIP):
            continue
        if s.startswith(". ") or s.startswith("> "):
            continue
        return s
    return ""


_K = re.compile(r"K[0-9a-fA-F]{6,}")
_BANG = re.compile(r"(?m)^\*!.*$")
_CMD = re.compile(r"(?m)^\.(command|date|time) = .*$")


def gph(key):
    """The saved .gph with its command echo, stamps and object ids
    normalised away (the oracle of scripts/extract_abbrev_truth.do)."""
    path = os.path.join(work, key + ".gph")
    if not os.path.exists(path):
        return None
    with open(path, errors="replace") as fh:
        txt = fh.read()
    return _K.sub("K#", _CMD.sub("", _BANG.sub("", txt)))


def rec(key):
    rc = int(G("ZP_R_" + key))
    # The saving() path is the probe's own temporary file: dropped, so the
    # record holds no path.
    cmd = re.sub(r"\s*saving\(.*\)\s*$", "", G("ZP_C_" + key).strip())
    return {"cmd": cmd, "rc": rc,
            "message": message(key) if rc else ""}


out = {"extras": {w: rec("x_" + w) for w in G("ZP_EXTRAS").split()},
       "twoways": {w: rec("w_" + w) for w in G("ZP_TWOWAYS").split()}}
bare = {k: rec("b_" + k) for k in ("twoway", "twoway_title",
                                   "graph_twoway", "tw", "gr_tw", "plain")}
bare["twoway"]["plot1_exists"] = G("ZP_B1_PLOT1") != ""
bare["twoway_title"]["plot1_exists"] = G("ZP_B2_PLOT1") != ""
bare["twoway_title"]["title"] = G("ZP_B2_TITLE")
out["bare"] = bare
full = {"label": gph("m_mlabel"), "align": gph("m_mlalign")}
mla = {}
for key in ("ml", "mla", "mla_center", "mlab", "mlabe", "mlabel", "mlal",
            "mlali", "mlalign"):
    r = rec("m_" + key)
    txt = gph("m_" + key) if r["rc"] == 0 else None
    r["resolves_to"] = ("mlabel" if txt is not None and txt == full["label"]
                        else "mlalign" if txt is not None and txt == full["align"]
                        else None)
    mla[key] = r
out["mla"] = mla
for name in os.listdir(work):
    if name.endswith((".log", ".gph")):
        try:
            os.remove(os.path.join(work, name))
        except OSError:
            pass
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZP_VERSION"), "born_date": G("ZP_BORN"),
                "dash_commit": commit, "extracted": G("ZP_WHEN"),
                "source": "scripts/extract_bare_prefix_truth.do"}
with open(G("ZP_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZP_OUT"))
end
