*! extract_stat_refusal_truth.do -- WP-35 section 35-04: what twoway does,
*! drawn, with the statistical options dash accepted and twoway refuses:
*! histogram's bins() with width() and its scale words together
*! (stat:PT-1), density, fraction, frequency and percent off histogram
*! (stat:PT-2), contour's levels() and ccuts() bound (stat:PT-5), lowess
*! weight and noweight weight (stat:PT-8) and bw() off the bandwidth types
*! (stat:PT-14).  For each probe: the return code, the first error line,
*! every log line after the command line, plot 1's serset (every variable,
*! every row), and the SVG twoway exports (its <desc> lines and per-export
*! ids aside) as an md5, so two probes are compared by their pictures.
*! twoway only: the output is the same before and after dash changes.
*!
*! Output: test/fixtures/stat_refusal_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_stat_refusal_truth.do
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
    display as error "extract_stat_refusal_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_stat_refusal_truth.do: `_zs_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZS_REPO "`repo'"
global ZS_OUT "${ZS_REPO}/test/fixtures/stat_refusal_truth.json"

local work "`c(tmpdir)'dash_stat_refusal_probe"
capture mkdir "`work'"
global ZS_WORK "`work'"

if `"`c(python_exec)'"' == "" {
    display as error "extract_stat_refusal_truth.do needs Python (c(python_exec) is empty)"
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

* contour's ccuts() lists, 499 and 500 values spanning depth's range
* (built once, before the probes, from the data's own minimum and maximum)
quietly sysuse sandstone, clear
quietly summarize depth
local _zs_lo = r(min)
local _zs_hi = r(max)
foreach n in 499 500 {
    local _zs_step = (`_zs_hi' - `_zs_lo') / (`n' + 1)
    mata: st_local("_zs_cuts`n'", invtokens(strofreal(`_zs_lo' :+ (1..`n') :* `_zs_step', "%21.0g")))
}

* stat:PT-1 histogram's exclusive options (twoway__histogram_gen.ado)
_zs_probe hist.bins_width auto histogram mpg, bin(10) width(2)
_zs_probe hist.bin0_width auto histogram mpg, bin(0) width(2)
_zs_probe hist.density_fraction auto histogram mpg, density fraction
_zs_probe hist.fraction_percent auto histogram mpg, fraction percent
_zs_probe hist.frequency_density auto histogram mpg, frequency density
_zs_probe hist.percent_frequency auto histogram mpg, percent frequency
_zs_probe hist.density_fraction_frequency auto histogram mpg, density fraction frequency
_zs_probe hist.discrete_bin_width auto histogram rep78, discrete bin(3) width(2)

* stat:PT-2 the scale words off histogram
foreach f in density fraction frequency percent {
    _zs_probe flag.scatter.`f' auto scatter mpg weight, `f'
    _zs_probe flag.line.`f' auto line mpg weight, `f'
    _zs_probe flag.lfit.`f' auto lfit mpg weight, `f'
    _zs_probe flag.kdensity.`f' auto kdensity mpg, `f'
    _zs_probe flag.function.`f' auto function y=x, `f'
    _zs_probe flag.bar.`f' auto bar mpg rep78, `f'
    _zs_probe flag.histogram.`f' auto histogram mpg, `f'
}

* stat:PT-5 contour's bound, drawn
foreach n in 500 501 1000 {
    _zs_probe contour.levels_`n' sandstone contour depth northing easting, levels(`n')
}
foreach n in 499 500 {
    _zs_probe contour.ccuts_`n' sandstone contour depth northing easting, ccuts(`_zs_cuts`n'')
}

* stat:PT-8 lowess weight and noweight
_zs_probe lowess.weight auto lowess mpg weight, weight
_zs_probe lowess.none auto lowess mpg weight,
_zs_probe lowess.noweight auto lowess mpg weight, noweight
_zs_probe lowess.noweight_weight auto lowess mpg weight, noweight weight
_zs_probe lowess.weight_noweight auto lowess mpg weight, weight noweight
_zs_probe lowess.bogus_noweight_weight auto lowess mpg weight, bogus noweight weight

* stat:PT-14 bw() off the bandwidth types (and on them)
_zs_probe bw.scatter auto scatter mpg weight, bw(2)
_zs_probe bw.line auto line mpg weight, bw(2)
_zs_probe bw.lfit auto lfit mpg weight, bw(2)
_zs_probe bw.fpfit auto fpfit mpg weight, bw(2)
_zs_probe bw.bar auto bar mpg rep78, bw(2)
_zs_probe bw.rbar auto rbar mpg turn weight, bw(2)
_zs_probe bw.histogram auto histogram mpg, bw(2)
_zs_probe bw.dot auto dot mpg rep78, bw(2)
_zs_probe bw.spike auto spike mpg weight, bw(2)
_zs_probe bw.lowess auto lowess mpg weight, bw(.5)
_zs_probe bw.kdensity auto kdensity mpg, bw(2)
_zs_probe bw.lpoly auto lpoly mpg weight, bw(500)
_zs_probe bw.lpolyci auto lpolyci mpg weight, bw(500)

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
                "source": "scripts/extract_stat_refusal_truth.do"}
with open(G("ZS_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZS_OUT"), len(out) - 1, "probes")
end
