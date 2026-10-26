*! extract_stat_accept_truth.do -- WP-35 section 35-03: what twoway does
*! with the statistical types' option spellings and edge values dash
*! refused or read otherwise: lowess m, bwi(), contour's documented
*! abbreviations, function subchar(), the edge n() and bands() values,
*! ty() and type() on the ci types (stat:PT-7, syn:SD-5, stat:PT-13,
*! stat:PT-6, stat:PT-9, syn:SD-7), and the five spellings ruling D42
*! registered (syn:SD-20a..e: dot dsi(), fpfit est(), lpolyci s(), colorvar
*! zl() and zt(), scatter's cl*() options).  For each probe: the return
*! code, the first error line, every log line after the command line, plot
*! 1's serset (every variable, every row), and the SVG twoway exports (its
*! <desc> lines and per-export ids aside) as an md5, so two probes are
*! compared by their pictures.  twoway only: the output is the same before
*! and after dash changes.
*!
*! Output: test/fixtures/stat_accept_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_stat_accept_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200
set graphics off

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zs_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zs_bad' {
    display as error "extract_stat_accept_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_stat_accept_truth.do: `_zs_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZS_REPO "`repo'"
global ZS_OUT "${ZS_REPO}/test/fixtures/stat_accept_truth.json"

local work "`c(tmpdir)'dash_stat_accept_probe"
capture mkdir "`work'"
global ZS_WORK "`work'"

if `"`c(python_exec)'"' == "" {
    display as error "extract_stat_accept_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

quietly shell git -C "${ZS_REPO}" rev-parse HEAD > "${ZS_WORK}/git_head.txt"
global ZS_VERSION "`c(stata_version)'"
global ZS_BORN "`c(born_date)'"
global ZS_WHEN "`c(current_date)' `c(current_time)'"
global ZS_N 0

* _zs_probe key data twoway-command: run the command on a fresh copy of
* the data (auto or sandstone; twoway lfit n(0) leaves the data changed),
* record its rc, its log, plot 1's serset as a CSV and its SVG.
capture program drop _zs_probe
program define _zs_probe
    gettoken key 0 : 0
    gettoken data cmd : 0
    global ZS_N = ${ZS_N} + 1
    local k ${ZS_N}
    global ZS_K_`k' "`key'"
    global ZS_C_`k' `"`cmd'"'
    quietly sysuse `data', clear
    serset clear
    capture graph drop _all
    capture erase "${ZS_WORK}/p`k'.svg"
    set seed 12345
    quietly log using "${ZS_WORK}/p`k'.log", text replace name(zsp) nomsg
    capture noisily twoway `cmd' name(g, replace)
    local rc = _rc
    quietly log close zsp
    global ZS_RC_`k' `rc'
    if !`rc' {
        capture graph export "${ZS_WORK}/p`k'.svg", name(g) replace as(svg)
        capture local id "`.g.plotregion1.plot1.serset.id'"
        if !_rc & "`id'" != "" {
            preserve
            capture {
                serset set `id'
                serset use, clear
                format _all %21.0g
                export delimited using "${ZS_WORK}/p`k'.csv", replace
            }
            restore
        }
    }
    capture graph drop _all
    display as text "ZS `key': rc `rc'"
end

* stat:PT-7 lowess m (twoway_lowess_parse.class Mean)
_zs_probe lowess_m auto lowess mpg weight, m
_zs_probe lowess_mean auto lowess mpg weight, mean
_zs_probe lowess_none auto lowess mpg weight,

* syn:SD-5 bwi() against bwidth() on the four bandwidth types
_zs_probe bwi.lowess auto lowess mpg weight, bwi(.5)
_zs_probe bwidth.lowess auto lowess mpg weight, bwidth(.5)
_zs_probe bwi.kdensity auto kdensity mpg, bwi(2)
_zs_probe bwidth.kdensity auto kdensity mpg, bwidth(2)
_zs_probe bwi.lpoly auto lpoly mpg weight, bwi(500)
_zs_probe bwidth.lpoly auto lpoly mpg weight, bwidth(500)
_zs_probe bwi.lpolyci auto lpolyci mpg weight, bwi(500)
_zs_probe bwidth.lpolyci auto lpolyci mpg weight, bwidth(500)

* stat:PT-13 contour's documented abbreviations against the full spellings
_zs_probe contour.i sandstone contour depth northing easting, i(none)
_zs_probe contour.int sandstone contour depth northing easting, int(none)
_zs_probe contour.interp sandstone contour depth northing easting, interp(none)
_zs_probe contour.none sandstone contour depth northing easting,
_zs_probe contour.colorl sandstone contourline depth northing easting, colorl
_zs_probe contour.colorlines sandstone contourline depth northing easting, colorlines
_zs_probe contour.clp sandstone contourline depth northing easting, clp(dash)
_zs_probe contour.clpatterns sandstone contourline depth northing easting, clpatterns(dash)
_zs_probe contour.clpattern sandstone contourline depth northing easting, clpattern(dash)
_zs_probe contour.clw sandstone contourline depth northing easting, clw(thick)
_zs_probe contour.clwidths sandstone contourline depth northing easting, clwidths(thick)
_zs_probe contour.clwidth sandstone contourline depth northing easting, clwidth(thick)
_zs_probe contour.line sandstone contourline depth northing easting,

* stat:PT-6 function subchar()
_zs_probe subchar.ok auto function y = t^2, subchar(t) range(0 2) n(5)
_zs_probe subchar.bad auto function y = t^2, subchar(1t) range(0 2) n(5)
_zs_probe subchar.scatter auto scatter mpg weight, subchar(t)
_zs_probe subchar.subc auto function y = t^2, subc(t) range(0 2) n(5)
_zs_probe subchar.sub auto function y = t^2, sub(t) range(0 2) n(5)
_zs_probe subchar.twice auto function y = t^2, subchar(s) subchar(t) range(0 2) n(5)
_zs_probe subchar.order auto scatter mpg weight, bogus subchar(t)
_zs_probe subchar.two auto function y = t^2, subchar(t t) range(0 2) n(5)
_zs_probe subchar.x auto function y = x^2, subchar(t) range(0 2) n(5)

* stat:PT-9 the edge n() values on the fit types, bands(-1)
foreach t in lfit qfit lfitci qfitci fpfit fpfitci {
    foreach v in -1 0 abc {
        _zs_probe n.`t'.`v' auto `t' mpg weight, n(`v')
    }
}
* The whole n() rule on the fit types that take it (WP-35 stat:PT-9
* follow-up): negative, 0, 1, large, non-integer and missing values.
foreach t in lfit qfit lfitci qfitci fpfitci {
    foreach v in -1000000 -100 -5 -2 -1.5 1 2 3 2.5 1e3 10000 10001 100000 . {
        _zs_probe nr.`t'.`v' auto `t' mpg weight, n(`v')
    }
}
_zs_probe lfit_nm1.legend auto (scatter mpg weight) (lfit mpg weight, n(-1)),
_zs_probe lfit_n1.legend auto (scatter mpg weight) (lfit mpg weight),
foreach t in mspline mband {
    _zs_probe bands.`t'.-1 auto `t' mpg weight, bands(-1)
    _zs_probe bands.`t'.0 auto `t' mpg weight, bands(0)
    _zs_probe bands.`t'.none auto `t' mpg weight,
}

* syn:SD-7 ty() and type() on the ci types
foreach t in lfitci qfitci fpfitci lpolyci {
    _zs_probe ty.`t' auto `t' mpg weight, ty(line)
    _zs_probe ciplot.`t' auto `t' mpg weight, ciplot(line)
    _zs_probe none.`t' auto `t' mpg weight,
    _zs_probe type.`t' auto `t' mpg weight, type(line)
}

* syn:SD-20a..e (ruling D42)
_zs_probe sd20a.dsi auto dot mpg weight, dsi(small)
_zs_probe sd20a.dsize auto dot mpg weight, dsize(small)
_zs_probe sd20a.none auto dot mpg weight,
_zs_probe sd20b.est auto fpfit mpg weight, est(glm)
_zs_probe sd20b.estcmd auto fpfit mpg weight, estcmd(glm)
_zs_probe sd20b.estopts auto fpfit mpg weight, estopts(glm)
_zs_probe sd20b.none auto fpfit mpg weight,
_zs_probe sd20c.s auto lpolyci mpg weight, s(line)
_zs_probe sd20c.msymbol auto lpolyci mpg weight, msymbol(line)
_zs_probe sd20c.smoothplot auto lpolyci mpg weight, smoothplot(line)
_zs_probe sd20c.none auto lpolyci mpg weight,
_zs_probe sd20c.scatter_s auto scatter mpg weight, s(Oh)
_zs_probe sd20c.scatter_msymbol auto scatter mpg weight, msymbol(Oh)
_zs_probe sd20d.zl auto scatter mpg weight, colorvar(turn) zl(30(5)50)
_zs_probe sd20d.zlabel auto scatter mpg weight, colorvar(turn) zlabel(30(5)50)
_zs_probe sd20d.zt auto scatter mpg weight, colorvar(turn) zt(Z)
_zs_probe sd20d.ztitle auto scatter mpg weight, colorvar(turn) ztitle(Z)
_zs_probe sd20d.none auto scatter mpg weight, colorvar(turn)
_zs_probe sd20e.clc auto scatter mpg weight, clc(red)
_zs_probe sd20e.none auto scatter mpg weight,
_zs_probe sd20e.c_clc auto scatter mpg weight, connect(l) sort clc(red)
_zs_probe sd20e.c_lcolor auto scatter mpg weight, connect(l) sort lcolor(red)
_zs_probe sd20e.c_none auto scatter mpg weight, connect(l) sort
_zs_probe sd20e.c_clp auto scatter mpg weight, connect(l) sort clp(dash)
_zs_probe sd20e.c_lpattern auto scatter mpg weight, connect(l) sort lpattern(dash)
_zs_probe sd20e.c_clw auto scatter mpg weight, connect(l) sort clw(thick)
_zs_probe sd20e.c_lwidth auto scatter mpg weight, connect(l) sort lwidth(thick)
_zs_probe sd20e.c_cls auto scatter mpg weight, connect(l) sort cls(p2)
_zs_probe sd20e.c_lstyle auto scatter mpg weight, connect(l) sort lstyle(p2)

python:
import csv, hashlib, json, os, re
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


work = G("ZS_WORK")
_ID = re.compile(r"\b(path|clipPath|pattern|linearGradient|mask)_[A-Za-z]{8}\b")


def lines(key_k):
    """Every line the command printed, in order."""
    try:
        with open(os.path.join(work, "p%d.log" % key_k), encoding="utf-8",
                  errors="replace") as fh:
            text = fh.read()
    except OSError:
        return []
    # A program's commands are not echoed: the log holds the command's
    # output alone.
    return [ln.rstrip() for ln in text.replace("\n> ", "").splitlines()
            if ln.strip() and not ln.startswith(". ")]


def num(v):
    v = (v or "").strip()
    if v in ("", "."):
        return None
    try:
        return float(v)
    except ValueError:
        return v


def serset(key_k):
    try:
        with open(os.path.join(work, "p%d.csv" % key_k), newline="",
                  encoding="utf-8") as fh:
            rows = list(csv.reader(fh))
    except OSError:
        return None
    if not rows:
        return None
    head, body = rows[0], rows[1:]
    return {h: [num(r[i]) for r in body] for i, h in enumerate(head)}


def svg(key_k):
    """md5 of the exported SVG, its <desc> lines aside and its per-export
    ids made one; and the text of its <text> elements, in order."""
    try:
        with open(os.path.join(work, "p%d.svg" % key_k), encoding="utf-8",
                  errors="replace") as fh:
            text = fh.read()
    except OSError:
        return None, None
    body = "\n".join(_ID.sub("ID", ln) for ln in text.splitlines()
                     if not ln.strip().startswith("<desc>"))
    texts = re.findall(r"<text[^>]*>([^<]*)</text>", text)
    return hashlib.md5(body.encode("utf-8")).hexdigest(), texts


out = {}
for k in range(1, int(G("ZS_N")) + 1):
    key = G("ZS_K_%d" % k)
    rc = int(G("ZS_RC_%d" % k))
    notes = lines(k)
    r = {"cmd": "twoway " + G("ZS_C_%d" % k).strip(), "rc": rc,
         "message": (notes[0].strip() if notes else "") if rc else "",
         "notes": notes}
    if rc == 0:
        r["serset"] = serset(k)
        r["svg_md5"], r["svg_texts"] = svg(k)
    out[key] = r
    for ext in (".log", ".csv", ".svg"):
        try:
            os.remove(os.path.join(work, "p%d%s" % (k, ext)))
        except OSError:
            pass
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZS_VERSION"), "born_date": G("ZS_BORN"),
                "dash_commit": commit, "extracted": G("ZS_WHEN"),
                "source": "scripts/extract_stat_accept_truth.do"}
with open(G("ZS_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZS_OUT"), len(out) - 1, "probes")
end
