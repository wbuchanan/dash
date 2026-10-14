*! extract_fit_options_truth.do -- WP-31 section 11 (C4): measure twoway's
*! fit options atobs, nofit, fitplot(), ciplot(), smoothplot(), estopts(),
*! predopts() and estcmd(): which of the forty plot types take each (rc and
*! first message line per pair), the refusals of a pair or a repeat, the
*! notes of an unknown fitplot()/ciplot() name, and the points twoway's own
*! serset holds for a fit drawn with them (.plotregion1.plot1.serset, read
*! with serset use).  twoway only: the output is the same before and after
*! dash changes.
*!
*! Output: test/fixtures/fit_options_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_fit_options_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zf_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zf_bad' {
    display as error "extract_fit_options_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zf_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zf_rc' | _rc {
    local _zf_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_fit_options_truth.do: `_zf_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZF_REPO "`repo'"
global ZF_OUT "${ZF_REPO}/test/fixtures/fit_options_truth.json"

global dash_nobrowser 1

local work "`c(tmpdir)'dash_fit_options_probe"
capture mkdir "`work'"
global ZF_WORK "`work'"

if `"`c(python_exec)'"' == "" {
    display as error "extract_fit_options_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

quietly shell git -C "${ZF_REPO}" rev-parse HEAD > "${ZF_WORK}/git_head.txt"
global ZF_VERSION "`c(stata_version)'"
global ZF_BORN "`c(born_date)'"
global ZF_WHEN "`c(current_date)' `c(current_time)'"


* _zf_probe <group> <key> <command>: run it under capture noisily with its
* own log; record rc, command and the log for the python block.
capture program drop _zf_probe
program define _zf_probe
    args grp key cmd
    local k = ${ZF_K} + 1
    global ZF_K `k'
    quietly log using "${ZF_WORK}/p`k'.log", replace text name(zf)
    capture noisily `cmd'
    local rc = _rc
    * A message in paragraph mode ({p 0 8}, never closed) reaches the log
    * only when the paragraph ends.
    display as text "{p_end}"
    quietly log close zf
    global ZF_G_`k' "`grp'"
    global ZF_K_`k' "`key'"
    global ZF_C_`k' `"`cmd'"'
    global ZF_R_`k' "`rc'"
    capture graph drop Graph
    c_local zf_k `k'
end

* _zf_pts <key> <command>: twoway's serset of plot 1, its columns written
* to <work>/<key>.csv (y [lo hi] x, as the serset orders them).
capture program drop _zf_pts
program define _zf_pts
    args key cmd
    quietly twoway `cmd' name(zfg, replace) nodraw
    local id = `.zfg.plotregion1.plot1.serset.id'
    preserve
    serset set `id'
    serset use, clear
    mata: _zf_csv("${ZF_WORK}/`key'.csv")
    restore
    graph drop zfg
    global ZF_P_`key' `"`cmd'"'
    c_local zf_k ${ZF_K}
end
global ZF_K 0

* _zf_csv(path): the data in memory as comma-separated text, a header line
* first, every value at %21.17g, a missing one as ".".
mata:
void _zf_csv(string scalar path)
{
    real matrix D
    real scalar fh, i, j
    string scalar s

    D = st_data(., .)
    if (fileexists(path)) unlink(path)
    fh = fopen(path, "w")
    fput(fh, "h")
    for (i = 1; i <= rows(D); i++) {
        s = ""
        for (j = 1; j <= cols(D); j++) {
            s = s + (j > 1 ? "," : "") + (D[i, j] >= . ? "." : strofreal(D[i, j], "%21.17g"))
        }
        fput(fh, s)
    }
    fclose(fh)
}
end
sysuse auto, clear
gen yl = mpg - 1
gen yh = mpg + 1
gen t = _n
tsset t

* A. Which types take each option.
local types scatter line connected area bar spike dropline dot tsline tsrline ///
    rarea rbar rspike rcap rline rconnected rcapsym rscatter ///
    pcspike pccapsym pcarrow pcbarrow pcscatter pci pcarrowi scatteri ///
    lfit qfit lfitci qfitci fpfit fpfitci lowess lpoly lpolyci mspline mband ///
    kdensity histogram function
local options atobs nofit fitplot ciplot smoothplot estopts predopts estcmd
local w_atobs "atobs"
local w_nofit "nofit"
local w_fitplot "fitplot(line)"
local w_ciplot "ciplot(rarea)"
local w_smoothplot "smoothplot(line)"
local w_estopts "estopts(noconstant)"
local w_predopts "predopts(stdp)"
local w_estcmd "estcmd(regress)"
global ZF_TYPES "`types'"
global ZF_OPTIONS "`options'"
local k 0
foreach o of local options {
    foreach t of local types {
        if inlist("`t'", "scatter", "line", "connected", "area", "bar", "spike", "dropline", "dot") {
            local a "`t' mpg weight"
        }
        else if "`t'" == "tsline" local a "tsline mpg"
        else if "`t'" == "tsrline" local a "tsrline yl yh"
        else if inlist("`t'", "rarea", "rbar", "rspike", "rcap", "rline", "rconnected", "rcapsym", "rscatter") {
            local a "`t' yl yh weight"
        }
        else if inlist("`t'", "pcspike", "pccapsym", "pcarrow", "pcbarrow", "pcscatter") {
            local a "`t' mpg weight trunk turn"
        }
        else if inlist("`t'", "pci", "pcarrowi") local a "`t' 20 2000 30 4000"
        else if "`t'" == "scatteri" local a "scatteri 20 2000"
        else if inlist("`t'", "kdensity", "histogram") local a "`t' mpg"
        else if "`t'" == "function" local a "function y = x"
        else local a "`t' mpg weight"
        _zf_probe "A" "`o'@`t'" "twoway `a', `w_`o'' nodraw"
    }
}

* R. Refusals, repeats and notes.
_zf_probe "R" "atobs_range" "twoway lfit mpg weight, atobs range(1000 5000) nodraw"
_zf_probe "R" "predopts_resid_range" "twoway lfit mpg weight, predopts(residuals) range(1000 5000) nodraw"
_zf_probe "R" "predopts_stdp_range" "twoway lfit mpg weight, predopts(stdp) range(1000 5000) nodraw"
_zf_probe "R" "atobs_twice" "twoway lfit mpg weight, atobs atobs nodraw"
_zf_probe "R" "nofit_twice" "twoway lfitci mpg weight, nofit nofit nodraw"
_zf_probe "R" "fitplot_twice" "twoway lfitci mpg weight, fitplot(scatter) fitplot(line) nodraw"
_zf_probe "R" "ciplot_twice" "twoway lfitci mpg weight, ciplot(rcap) ciplot(rarea) nodraw"
_zf_probe "R" "estopts_twice" "twoway lfit mpg weight, estopts(noconstant) estopts(noconstant) nodraw"
_zf_probe "R" "fitplot_bogus" "twoway lfitci mpg weight, fitplot(bogus) nodraw"
_zf_probe "R" "ciplot_bogus" "twoway lfitci mpg weight, ciplot(bogus) nodraw"
_zf_probe "R" "ciplot_sc" "twoway lfitci mpg weight, ciplot(sc) nodraw"
_zf_probe "R" "estopts_bogus" "twoway lfit mpg weight, estopts(bogus) nodraw"
_zf_probe "R" "estcmd_bogus" "twoway fpfit mpg weight, estcmd(bogus) nodraw"

* F. The points twoway's serset holds.
_zf_pts F01 "lfit mpg weight, atobs"
_zf_pts F02 "lfit mpg weight, estopts(noconstant)"
_zf_pts F03 "fpfit mpg weight, estopts(degree(3))"
_zf_pts F04 "lfitci mpg weight, estopts(noconstant)"
_zf_pts F05 "lfit mpg weight, predopts(residuals)"
_zf_pts F06 "fpfitci mpg weight, estcmd(glm)"
_zf_pts F07 "qfitci mpg weight [aw=trunk], estopts(noconstant) level(90)"
_zf_pts F08 "lfit mpg weight if foreign, estopts(noconstant) n(5)"
global ZF_N "`zf_k'"
display as text "probes: ${ZF_N}"

python:
import csv, json, os
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


SKIP = ("name:", "log:", "log type:", "opened on:", "closed on:")


def lines_of(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            raw = [ln.rstrip() for ln in fh]
    except OSError:
        return []
    body = []
    for ln in raw:
        s = ln.strip()
        if not s or set(s) <= set("-") or s.startswith(SKIP):
            continue
        if s.startswith(". ") or s.startswith("> ") or s == "{p_end}":
            continue
        body.append(s)
    return body


def message(body):
    for s in body:
        if s.startswith("option "):
            return s
    return body[-1] if body else ""


work = G("ZF_WORK")
out = {"applies": {}, "refusals": {}, "points": {}}
for k in range(1, int(G("ZF_K")) + 1):
    path = os.path.join(work, "p%d.log" % k)
    body = lines_of(path)
    rc = int(G("ZF_R_%d" % k))
    rec = {"cmd": G("ZF_C_%d" % k), "rc": rc,
           "message": message(body) if rc else "",
           "notes": [s for s in body if s.startswith("(note:")]}
    grp = "applies" if G("ZF_G_%d" % k) == "A" else "refusals"
    out[grp][G("ZF_K_%d" % k)] = rec
    try:
        os.remove(path)
    except OSError:
        pass


def num(s):
    s = s.strip()
    return None if s in ("", ".") else float(s)


for key in ("F01", "F02", "F03", "F04", "F05", "F06", "F07", "F08"):
    path = os.path.join(work, key + ".csv")
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    os.remove(path)
    cols = list(zip(*rows[1:])) if len(rows) > 1 else [()] * len(rows[0])
    vals = [[num(v) for v in c] for c in cols]
    rec = {"cmd": G("ZF_P_" + key), "y": vals[0], "x": vals[-1]}
    if len(vals) == 4:
        rec["lo"], rec["hi"] = vals[1], vals[2]
    out["points"][key] = rec
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZF_VERSION"), "born_date": G("ZF_BORN"),
                "dash_commit": commit, "extracted": G("ZF_WHEN"),
                "source": "scripts/extract_fit_options_truth.do"}
out["options"] = G("ZF_OPTIONS").split()
out["types"] = G("ZF_TYPES").split()
with open(G("ZF_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZF_OUT"), len(out["applies"]), len(out["refusals"]))
end
