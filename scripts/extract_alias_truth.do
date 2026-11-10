*! extract_alias_truth.do -- WP-47 basic:PT-10 (section 47-04): how twoway
*! reads its older spellings of options dash draws: symbol(), msymangle(),
*! mlabels(), bcolor(), bfintensity(), blwidth(), blpattern(), afcolor(),
*! afintensity(), bsymbol() and bmsize().  twoway_yxview_parse.class
*! factors each onto the marker, label or area edit its target is factored
*! onto; this script measures, from graph export SVG (ids normalised):
*!
*!   P1  <type> ..., A(v) against <type> ..., T(v): the same picture?
*!   P2  T(v) A(w) and A(w) T(v) (and the pairs of PAIRS below): which
*!       value is drawn, by order
*!   P4  every spelling of A, from one letter to its full name: rc, first
*!       line, and whether it draws A's picture
*!   P5  A(<bad value>) and T(<bad value>): rc and the lines twoway prints
*!
*! Output: test/fixtures/alias_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_alias_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 255

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_za_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_za_bad' {
    display as error "extract_alias_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _za_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_za_rc' | _rc {
    local _za_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_alias_truth.do: `_za_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZA_REPO "`repo'"
global ZA_OUT "${ZA_REPO}/test/fixtures/alias_truth.json"

local work "`c(tmpdir)'dash_alias_probe"
capture mkdir "`work'"
global ZA_WORK "`work'"

quietly shell git -C "${ZA_REPO}" rev-parse HEAD > "${ZA_WORK}/git_head.txt"
global ZA_VERSION "`c(stata_version)'"
global ZA_BORN "`c(born_date)'"
global ZA_WHEN "`c(current_date)' `c(current_time)'"

sysuse auto, clear
* t has no ties: a type that joins its points in x order draws one picture
* each run (a sort over weight's ties does not).
gen t = _n

* One probe: id ; command after "twoway " (no name()).  Its picture goes
* to <id>.svg and what twoway prints to <id>.log.
capture program drop _za_probe
program define _za_probe
    args id cmd
    capture graph drop _all
    quietly log using "${ZA_WORK}/`id'.log", replace text name(za)
    capture noisily twoway `cmd' name(za, replace)
    local rc = _rc
    quietly log close za
    if !`rc' capture graph export "${ZA_WORK}/`id'.svg", name(za) replace as(svg)
    capture graph drop _all
    global ZA_RC_`id' "`rc'"
    global ZA_CMD_`id' `"`cmd'"'
    global ZA_IDS "${ZA_IDS} `id'"
end
global ZA_IDS ""

* A ";"-separated spec, split into the caller's locals f1, f2, ...
capture program drop _za_split
program define _za_split
    args spec
    mata: _za_s = st_local("spec")
    mata: _za_k = 0
    mata: while (strpos(_za_s, ";")) { _za_k++; st_local("f" + strofreal(_za_k), substr(_za_s, 1, strpos(_za_s, ";") - 1)); _za_s = substr(_za_s, strpos(_za_s, ";") + 1, .); }
    mata: _za_k++
    mata: st_local("f" + strofreal(_za_k), _za_s)
    forvalues j = 1/6 {
        c_local f`j' `"`f`j''"'
    }
end

* The aliases: alias ; target ; command ; v ; w ; bad value.
local aliases ""
local aliases `"`aliases' "symbol;msymbol;scatter mpg weight,;Oh;T;bogus""'
local aliases `"`aliases' "msymangle;msangle;scatter mpg weight, msymbol(T);45;10;abc""'
local aliases `"`aliases' "mlabels;mlabel;scatter mpg weight,;make;foreign;nosuchvar""'
local aliases `"`aliases' "bcolor;acolor;bar mpg weight,;red;blue;bogus""'
local aliases `"`aliases' "bfintensity;fintensity;bar mpg weight,;30;80;abc""'
local aliases `"`aliases' "blwidth;alwidth;bar mpg weight,;thick;vthin;bogus""'
local aliases `"`aliases' "blpattern;alpattern;bar mpg weight,;dash;dot;bogus""'
local aliases `"`aliases' "afcolor;fcolor;bar mpg weight,;red;blue;bogus""'
local aliases `"`aliases' "afintensity;fintensity;bar mpg weight,;30;80;abc""'
local aliases `"`aliases' "bsymbol;bmsymbol;scatter mpg weight,;O;T;bogus""'
local aliases `"`aliases' "bmsize;barbsize;pcarrow mpg weight trunk turn,;3;1;abc""'
* The same aliases on the other types the plan names (P1 only).
local others ""
local others `"`others' "bcolor;acolor;area mpg t,;red""'
local others `"`others' "afcolor;fcolor;area mpg t,;red""'
local others `"`others' "blwidth;alwidth;area mpg t,;thick""'
local others `"`others' "bcolor;acolor;scatter mpg weight,;red""'
local others `"`others' "bmsize;barbsize;scatter mpg weight,;3""'
local others `"`others' "bmsize;barbsize;pcbarrow mpg weight trunk turn,;3""'
local others `"`others' "bmsize;barbsize;pcarrowi 20 2000 30 4000,;3""'
local others `"`others' "bmsize;barbsize;rcapsym mpg trunk weight,;3""'
local others `"`others' "bsymbol;bmsymbol;pcbarrow mpg weight trunk turn,;O""'
local others `"`others' "bsymbol;bmsymbol;pcarrow mpg weight trunk turn,;O""'
local others `"`others' "symbol;msymbol;line mpg t,;Oh""'
local others `"`others' "symbol;msymbol;connected mpg t,;Oh""'
local others `"`others' "bcolor;color;area mpg t,;red""'
local others `"`others' "bcolor;acolor;rarea mpg trunk t,;red""'
local others `"`others' "bcolor;acolor;rbar mpg trunk weight,;red""'
local others `"`others' "bcolor;acolor;histogram mpg,;red""'
local others `"`others' "bcolor;acolor;rspike mpg trunk weight,;red""'
local others `"`others' "bcolor;acolor;lfitci mpg weight,;red""'
local others `"`others' "blwidth;alwidth;rbar mpg trunk weight,;thick""'
local others `"`others' "afcolor;fcolor;rbar mpg trunk weight,;red""'
local others `"`others' "msymangle;msangle;connected mpg t, msymbol(T);45""'
local others `"`others' "mlabels;mlabel;line mpg t,;make""'
* Pairs measured both ways: id ; command ; first option ; second option.
local pairs ""
local pairs `"`pairs' "msymbol_symbol;scatter mpg weight,;msymbol(Oh);symbol(T)""'
local pairs `"`pairs' "msangle_msymangle;scatter mpg weight, msymbol(T);msangle(10);msymangle(45)""'
local pairs `"`pairs' "mlabel_mlabels;scatter mpg weight,;mlabel(make);mlabels(foreign)""'
local pairs `"`pairs' "acolor_bcolor;bar mpg weight,;acolor(red);bcolor(blue)""'
local pairs `"`pairs' "color_bcolor;bar mpg weight,;color(red);bcolor(blue)""'
local pairs `"`pairs' "fcolor_bcolor;bar mpg weight,;fcolor(red);bcolor(blue)""'
local pairs `"`pairs' "bfcolor_bcolor;bar mpg weight,;bfcolor(red);bcolor(blue)""'
local pairs `"`pairs' "lcolor_bcolor;bar mpg weight,;lcolor(red);bcolor(blue)""'
local pairs `"`pairs' "alcolor_bcolor;bar mpg weight,;alcolor(red);bcolor(blue)""'
local pairs `"`pairs' "blcolor_bcolor;bar mpg weight,;blcolor(red);bcolor(blue)""'
local pairs `"`pairs' "fcolor_afcolor;bar mpg weight,;fcolor(red);afcolor(blue)""'
local pairs `"`pairs' "bfcolor_afcolor;bar mpg weight,;bfcolor(red);afcolor(blue)""'
local pairs `"`pairs' "acolor_afcolor;bar mpg weight,;acolor(red);afcolor(blue)""'
local pairs `"`pairs' "color_afcolor;bar mpg weight,;color(red);afcolor(blue)""'
local pairs `"`pairs' "bcolor_afcolor;bar mpg weight,;bcolor(red);afcolor(blue)""'
local pairs `"`pairs' "fintensity_bfintensity;bar mpg weight,;fintensity(30);bfintensity(80)""'
local pairs `"`pairs' "fintensity_afintensity;bar mpg weight,;fintensity(30);afintensity(80)""'
local pairs `"`pairs' "afintensity_bfintensity;bar mpg weight,;afintensity(30);bfintensity(80)""'
local pairs `"`pairs' "alwidth_blwidth;bar mpg weight,;alwidth(thick);blwidth(vthin)""'
local pairs `"`pairs' "lwidth_blwidth;bar mpg weight,;lwidth(thick);blwidth(vthin)""'
local pairs `"`pairs' "alpattern_blpattern;bar mpg weight,;alpattern(dash);blpattern(dot)""'
local pairs `"`pairs' "lpattern_blpattern;bar mpg weight,;lpattern(dash);blpattern(dot)""'
local pairs `"`pairs' "barbsize_bmsize;pcarrow mpg weight trunk turn,;barbsize(1);bmsize(3)""'
local pairs `"`pairs' "bmsymbol_bsymbol;scatter mpg weight,;bmsymbol(O);bsymbol(T)""'

local i 0
foreach a of local aliases {
    local ++i
    _za_split `"`a'"'
    local al "`f1'"
    local tg "`f2'"
    local cmd "`f3'"
    local v "`f4'"
    local w "`f5'"
    local bad "`f6'"
    global ZA_A_`i' "`al';`tg';`v';`w';`bad'"
    _za_probe `al'_base `"`cmd'"'
    _za_probe `al'_T_v `"`cmd' `tg'(`v')"'
    _za_probe `al'_T_w `"`cmd' `tg'(`w')"'
    _za_probe `al'_A_v `"`cmd' `al'(`v')"'
    _za_probe `al'_A_w `"`cmd' `al'(`w')"'
    _za_probe `al'_TA `"`cmd' `tg'(`v') `al'(`w')"'
    _za_probe `al'_AT `"`cmd' `al'(`w') `tg'(`v')"'
    _za_probe `al'_AA `"`cmd' `al'(`v') `al'(`w')"'
    _za_probe `al'_bad `"`cmd' `al'(`bad')"'
    _za_probe `al'_Tbad `"`cmd' `tg'(`bad')"'
    local L = strlen("`al'")
    forvalues j = 1/`L' {
        local pre = substr("`al'", 1, `j')
        _za_probe `al'_ab`j' `"`cmd' `pre'(`v')"'
    }
}
global ZA_NA "`i'"
local i 0
foreach o of local others {
    local ++i
    _za_split `"`o'"'
    global ZA_O_`i' "`f1';`f2';`f4'"
    _za_probe o`i'_base `"`f3'"'
    _za_probe o`i'_A `"`f3' `f1'(`f4')"'
    _za_probe o`i'_T `"`f3' `f2'(`f4')"'
}
global ZA_NO "`i'"
local i 0
foreach p of local pairs {
    local ++i
    _za_split `"`p'"'
    global ZA_P_`i' "`f1';`f3';`f4'"
    _za_probe p`i'_x `"`f2' `f3'"'
    _za_probe p`i'_y `"`f2' `f4'"'
    _za_probe p`i'_xy `"`f2' `f3' `f4'"'
    _za_probe p`i'_yx `"`f2' `f4' `f3'"'
}
global ZA_NP "`i'"

python:
import json, os, re
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


work = G("ZA_WORK")
_ID = re.compile(r"\b(path|clipPath|pattern|linearGradient|mask)_[A-Za-z]{8}\b")


def svg(id_):
    try:
        with open(os.path.join(work, id_ + ".svg"), encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return None
    return [_ID.sub("ID", ln) for ln in text.splitlines()
            if not ln.strip().startswith("<desc>")]


def lines(id_):
    """What twoway printed, the command's echo and the log's frame aside."""
    try:
        with open(os.path.join(work, id_ + ".log"), encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return []
    out = []
    for ln in text.replace("\n> ", "").splitlines():
        s = ln.rstrip()
        if not s.strip() or s.lstrip().startswith(". ") or s.startswith("      name:") \
                or s.startswith("       log:") or s.startswith("  log type:") \
                or s.startswith(" opened on:") or s.startswith(" closed on:") \
                or set(s.strip()) <= set("-"):
            continue
        out.append(s.strip())
    return [s for s in out if not s.startswith("r(")]


def rc(id_):
    return int(G("ZA_RC_" + id_))


def same(a, b):
    x, y = svg(a), svg(b)
    if x is None or y is None:
        return None
    return x == y


def which(id_, x, y):
    """"first" or "second" for the probe's picture equal to x's or y's,
    "neither", or None when a picture is missing."""
    if same(id_, x):
        return "first"
    if same(id_, y):
        return "second"
    return None if svg(id_) is None else "neither"


out = {}
for i in range(1, int(G("ZA_NA")) + 1):
    al, tg, v, w, bad = G("ZA_A_%d" % i).split(";")
    e = {"target": tg, "command": G("ZA_CMD_%s_base" % al), "v": v, "w": w,
         "P1": {"rc": rc(al + "_A_v"),
                "same_as_target": same(al + "_A_v", al + "_T_v"),
                "same_as_target_w": same(al + "_A_w", al + "_T_w"),
                "differs_from_base": (same(al + "_A_v", al + "_base") is False)},
         "P2": {"cmd": G("ZA_CMD_%s_TA" % al), "rc": rc(al + "_TA"),
                "draws": which(al + "_TA", al + "_T_v", al + "_A_w")},
         "P3": {"cmd": G("ZA_CMD_%s_AT" % al), "rc": rc(al + "_AT"),
                "draws": which(al + "_AT", al + "_A_w", al + "_T_v")},
         "repeat": {"cmd": G("ZA_CMD_%s_AA" % al), "rc": rc(al + "_AA"),
                    "draws": which(al + "_AA", al + "_A_v", al + "_A_w")},
         "P5": {"alias": {"cmd": G("ZA_CMD_%s_bad" % al), "rc": rc(al + "_bad"),
                          "lines": lines(al + "_bad")},
                "target": {"cmd": G("ZA_CMD_%s_Tbad" % al), "rc": rc(al + "_Tbad"),
                           "lines": lines(al + "_Tbad")}},
         "P4": {}}
    for j in range(1, len(al) + 1):
        pid = "%s_ab%d" % (al, j)
        r = rc(pid)
        e["P4"][al[:j]] = {"rc": r, "first_line": (lines(pid) or [""])[0] if r else "",
                           "draws_alias": same(pid, al + "_A_v") if r == 0 else None}
    ab = [s for s, x in sorted(e["P4"].items(), key=lambda t: len(t[0]))
          if x["rc"] == 0 and x["draws_alias"]]
    # The shortest spelling from which every longer one draws the alias.
    m = al
    for j in range(len(al), 0, -1):
        x = e["P4"][al[:j]]
        if x["rc"] == 0 and x["draws_alias"]:
            m = al[:j]
        else:
            break
    e["min_abbrev"] = m
    out[al] = e
others = []
for i in range(1, int(G("ZA_NO")) + 1):
    al, tg, v = G("ZA_O_%d" % i).split(";")
    others.append({"alias": al, "target": tg, "command": G("ZA_CMD_o%d_A" % i),
                   "rc": rc("o%d_A" % i),
                   "same_as_target": same("o%d_A" % i, "o%d_T" % i),
                   "alias_differs_from_base": (same("o%d_A" % i, "o%d_base" % i) is False),
                   "target_differs_from_base": (same("o%d_T" % i, "o%d_base" % i) is False)})
pairs = {}
for i in range(1, int(G("ZA_NP")) + 1):
    pid, x, y = G("ZA_P_%d" % i).split(";")
    pairs[pid] = {"first": x, "second": y,
                  "xy": {"cmd": G("ZA_CMD_p%d_xy" % i), "rc": rc("p%d_xy" % i),
                         "draws": which("p%d_xy" % i, "p%d_x" % i, "p%d_y" % i)},
                  "yx": {"cmd": G("ZA_CMD_p%d_yx" % i), "rc": rc("p%d_yx" % i),
                         "draws": which("p%d_yx" % i, "p%d_x" % i, "p%d_y" % i)}}
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
res = {"_meta": {"stata_version": G("ZA_VERSION"), "born_date": G("ZA_BORN"),
                 "dash_commit": commit, "extracted": G("ZA_WHEN"),
                 "source": "scripts/extract_alias_truth.do",
                 "method": "graph export SVG, its <desc> lines aside and the per-export ids made one; "
                           "draws names the single-option picture a two-option probe equals "
                           "(first/second as listed), or neither"},
       "others": others, "pairs": pairs}
res.update(out)
with open(G("ZA_OUT"), "w", encoding="utf-8") as fh:
    json.dump(res, fh, indent=1, sort_keys=True)
    fh.write("\n")
if not os.environ.get("ZA_KEEP"):
    for f in os.listdir(work):
        if f.endswith((".svg", ".log")) or f == "git_head.txt":
            try:
                os.remove(os.path.join(work, f))
            except OSError:
                pass
print("wrote", G("ZA_OUT"), len(out), "aliases,", len(pairs), "pairs")
end
