*! extract_scheme_layer_truth.do -- WP-30 section 24 (P1.4a): measure the
*! opacity, histogram style, marker symbols and marker colours twoway draws
*! on every layer type, so dash's scheme reach is proved against twoway.
*!
*! Output: test/fixtures/scheme_layer_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_scheme_layer_truth.do
*!
*! METHOD.  sysuse auto, lo = mpg - 3, hi = mpg + 3, y1..y15 = mpg + i,
*! sorted by weight.  Each probe (_sk_probe) runs one twoway command with
*! its axes, plot-region frame and legend off, so the SVG holds only the
*! layers, records the rc and exports the graph to SVG.  One python block
*! reads every SVG through scripts/svg_layer.py and records each probe's
*! distinct element styles and, for the symbol probes, each layer's first
*! marker (shape, hollow, stroked extent, colours).  It is twoway-only:
*! dash is never run.  The user schemes are written into a
*! tempfile-named directory under c(tmpdir), never into the repository.
*! The git commit is read from a file `shell' wrote, never with
*! shell=True.  Every SVG is erased.

clear all
set more off
set linesize 200

* Root: DASH_REPO, else the current directory when it is a dash tree.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_scheme_layer_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zr_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zr_rc' | _rc {
    local _zr_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_scheme_layer_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the dash repository"'
    exit 601
}
global OB_REPO "`repo'"
global OB_OUT "${OB_REPO}/test/fixtures/scheme_layer_truth.json"

adopath ++ "${OB_REPO}/"
global dash_nobrowser 1

version 19
set graphics off

if `"`c(python_exec)'"' == "" {
    display as error "extract_scheme_layer_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

* The work directory: tempfile-named, under c(tmpdir).
tempfile _sk_name
mata: st_global("OB_WORK", pathjoin(st_global("c(tmpdir)"), "dash_sk_" + pathbasename(st_local("_sk_name"))))
mata: st_global("OB_WORK", subinstr(subinstr(st_global("OB_WORK"), ".tmp", ""), ".", "_"))
capture mkdir "${OB_WORK}"

* The four user schemes of plan section 24's Stata truth.
tempname fh
file open `fh' using "${OB_WORK}/scheme-w24g.scheme", write text replace
file write `fh' "#include s2color" _n "color pmarkfill green" _n "color pmarkline blue" _n
file close `fh'
file open `fh' using "${OB_WORK}/scheme-w24m.scheme", write text replace
file write `fh' "#include s2color" _n "color p1mark green" _n "color pmark red" _n
file close `fh'
file open `fh' using "${OB_WORK}/scheme-w24f.scheme", write text replace
file write `fh' "#include s2color" _n "color p1markfill green" _n "color p1markline blue" _n
file close `fh'
file open `fh' using "${OB_WORK}/scheme-w24h.scheme", write text replace
file write `fh' "#include s2color" _n "color histogram red" _n "intensity histogram inten50" _n "color histogram_line blue" _n "linewidth histogram vthick" _n
file close `fh'
adopath ++ "${OB_WORK}/"

quietly shell git -C "${OB_REPO}" rev-parse HEAD > "${OB_WORK}/git_head.txt"
global OB_VERSION "`c(stata_version)'"
global OB_BORN "`c(born_date)'"
global OB_WHEN "`c(current_date)' `c(current_time)'"

sysuse auto, clear
generate lo = mpg - 3
generate hi = mpg + 3
forvalues i = 1/15 {
    generate y`i' = mpg + `i'
}
sort weight

global OB_IDS ""
global OB_SEQ = 0
capture program drop _sk_probe
program define _sk_probe
    * _sk_probe id group scheme command
    gettoken id 0 : 0
    gettoken group 0 : 0
    gettoken scheme 0 : 0
    local cmd = strtrim(`"`0'"')
    local opt = cond(strpos(`"`cmd'"', ",") & substr(`"`cmd'"', 1, 1) != "(", " ", ", ")
    global OB_SEQ = ${OB_SEQ} + 1
    local f "${OB_WORK}/p${OB_SEQ}"
    global OBF_`id' "p${OB_SEQ}"
    capture noisily twoway `cmd' `opt' scheme(`scheme') legend(off) xscale(off) yscale(off) plotregion(style(none)) name(sk, replace)
    local rc = _rc
    global OBR_`id' = `rc'
    global OBG_`id' "`group'"
    global OBS_`id' "`scheme'"
    global OBC_`id' `"`cmd'"'
    if `rc' == 0 {
        quietly graph export "`f'.svg", replace
    }
    global OB_IDS "${OB_IDS} `id'"
    capture graph drop sk
end

* opacity: every layer type under sttrans
local i = 0
foreach c in "lfit mpg weight" "qfit mpg weight" "lowess mpg weight" "lpoly mpg weight" "fpfit mpg weight" "mspline mpg weight" "mband mpg weight" "kdensity mpg" "function y=x/1000, range(1760 4840)" "lfitci mpg weight" "qfitci mpg weight" "lpolyci mpg weight" "fpfitci mpg weight" "spike mpg weight" "rspike lo hi weight" "rcap lo hi weight" "rcapsym lo hi weight" "dropline mpg weight" "rline lo hi weight" "rscatter lo hi weight" "rbar lo hi rep78 if rep78<." "rarea lo hi weight" "area mpg weight" "scatteri 20 3000 30 4000" "pci 20 3000 30 4000" "pcspike mpg weight price length" "pcarrow mpg weight price length in 1/5" "pcarrowi 20 3000 30 4000" "pcbarrow mpg weight price length in 1/5" "pccapsym mpg weight price length in 1/5" "pcscatter mpg weight price length" "histogram mpg" {
    local ++i
    gettoken t : c
    _sk_probe op_`t' opacity sttrans `c'
}
_sk_probe op_rarea_s2color opacity s2color rarea lo hi weight
_sk_probe op_area_s2color opacity s2color area mpg weight

* opacity_user
_sk_probe ou_rspike_red opacity_user sttrans rspike lo hi weight, lcolor(red)
_sk_probe ou_lfit_red70 opacity_user sttrans lfit mpg weight, lcolor(red%70)
_sk_probe ou_rarea_red opacity_user sttrans rarea lo hi weight, fcolor(red)
_sk_probe ou_hist_red opacity_user sttrans histogram mpg, color(red)
_sk_probe ou_lfitci_ci opacity_user sttrans lfitci mpg weight, pstyle(ci)
_sk_probe ou_lfitci_p3 opacity_user sttrans lfitci mpg weight, pstyle(p3)

* histogram
foreach s in s2color stcolor s1mono s2mono economist s1rcolor sttrans stmono1 {
    _sk_probe hi_`s' histogram `s' histogram mpg
    _sk_probe hi2_`s' histogram `s' (histogram mpg) (histogram trunk)
}
_sk_probe ho_fcolor histogram_opt s2color histogram mpg, fcolor(red)
_sk_probe ho_color histogram_opt s2color histogram mpg, color(red)
_sk_probe ho_lcolor histogram_opt s2color histogram mpg, lcolor(blue)
_sk_probe ho_navy_stcolor histogram_opt stcolor histogram mpg, fcolor(navy)
_sk_probe ho_w24h histogram_opt w24h histogram mpg

* symbol (s1mono)
_sk_probe sy_cycle symbol s1mono scatter y1-y15 weight in 1/3
_sk_probe sy_large symbol s1mono scatter y1-y11 weight in 1/3, msize(large large large large large large large large large large large)
_sk_probe sy_smh_red symbol s1mono (scatter mpg weight in 1/3) (scatter mpg weight in 4/6, msymbol(smcircle_hollow) mfcolor(red))
_sk_probe sy_p7_red symbol s1mono (scatter mpg weight in 1/3) (scatter mpg weight in 4/6, pstyle(p7) mfcolor(red))

* sm: each small symbol and its full symbol, at the default size and large
foreach n in smcircle smcircle_hollow smdiamond smdiamond_hollow smsquare smsquare_hollow smtriangle smtriangle_hollow smplus smx smv {
    local full = substr("`n'", 3, .)
    _sk_probe sm_`n' sm s2color scatter mpg weight in 1, msymbol(`n')
    _sk_probe sm_`n'_L sm s2color scatter mpg weight in 1, msymbol(`n') msize(large)
    _sk_probe sm_`full' sm s2color scatter mpg weight in 1, msymbol(`full')
    _sk_probe sm_`full'_L sm s2color scatter mpg weight in 1, msymbol(`full') msize(large)
}

* cycle (s1mono): the second layer of each marker type
_sk_probe cy_scatteri cycle s1mono (scatter mpg weight in 1/3) (scatteri 20 3000)
_sk_probe cy_rscatter cycle s1mono (scatter mpg weight in 1/3) (rscatter lo hi weight in 1/3)
_sk_probe cy_pcscatter cycle s1mono (scatter mpg weight in 1/3) (pcscatter mpg weight price length in 1/3)
_sk_probe cy_dropline cycle s1mono (scatter mpg weight in 1/3) (dropline mpg weight in 1/3)
_sk_probe cy_rcapsym cycle s1mono (scatter mpg weight in 1/3) (rcapsym lo hi weight in 1/3)

* mark: the marker colour keys
foreach s in w24g w24m w24f {
    _sk_probe mk_`s'_1 mark `s' scatter mpg weight in 1/3
    _sk_probe mk_`s'_2 mark `s' (scatter mpg weight in 1/3) (scatter price weight in 1/3, yaxis(2))
}

python:
import json, os, sys
from collections import Counter
from sfi import Macro

G = Macro.getGlobal
sys.path.insert(0, os.path.join(G("OB_REPO"), "scripts"))
import svg_layer as sl  # noqa: E402

work = G("OB_WORK")
written = [os.path.join(work, n) for n in
           ("scheme-w24g.scheme", "scheme-w24m.scheme", "scheme-w24f.scheme",
            "scheme-w24h.scheme", "git_head.txt")]
_KEYS = ("kind", "fill", "fill_opacity", "stroke", "stroke_opacity",
         "stroke_width")


def styles(els):
    """The distinct element styles, in first-drawn order, with counts."""
    c = Counter(tuple(e[k] for k in _KEYS) for e in els)
    seen, out = set(), []
    for e in els:
        key = tuple(e[k] for k in _KEYS)
        if key not in seen:
            seen.add(key)
            out.append(dict(zip(_KEYS, key), n=c[key]))
    return out


def layer(marker):
    return {"shape": sl.marker_shape(marker), "hollow": sl.hollow(marker),
            "extent": sl.stroke_extent(marker),
            "fill": next((e["fill"] for e in marker
                          if e["fill"] not in (None, "none")), None),
            "stroke": next((e["stroke"] for e in marker
                            if e["stroke"] not in (None, "none")), None)}


probes = {}
for pid in G("OB_IDS").split():
    grp = G("OBG_" + pid)
    rec = {"group": grp, "scheme": G("OBS_" + pid),
           "command": G("OBC_" + pid), "rc": int(float(G("OBR_" + pid))),
           "elements": [], "layers": []}
    svg = os.path.join(work, G("OBF_" + pid) + ".svg")
    if os.path.exists(svg):
        written.append(svg)
        els = sl.svg_elements(svg)
        rec["elements"] = styles(els)
        if grp in ("symbol", "sm", "cycle", "mark"):
            ms = [m for m in sl.markers(els) if sl.marker_shape(m)]
            if grp == "cycle":
                # The second layer's marker: the last one drawn.
                rec["layers"] = [layer(ms[0]), layer(ms[-1])] if ms else []
            elif grp == "sm":
                rec["layers"] = [layer(ms[0])] if ms else []
            else:
                per = 3
                rec["layers"] = [layer(ms[i]) for i in range(0, len(ms), per)]
    probes[pid] = rec


def ext(pid):
    ls = probes.get(pid, {}).get("layers") or []
    return ls[0]["extent"] if ls else None


sm = {}
for n in ("smcircle", "smcircle_hollow", "smdiamond", "smdiamond_hollow",
          "smsquare", "smsquare_hollow", "smtriangle", "smtriangle_hollow",
          "smplus", "smx", "smv"):
    full = n[2:]
    r = {}
    for size, suf in (("default", ""), ("large", "_L")):
        a, b = ext("sm_" + n + suf), ext("sm_" + full + suf)
        r[size] = round(a / b, 4) if a and b else None
    sm[n] = r
cyc = probes.get("sy_cycle", {}).get("layers") or []
derived = {"sm_factor": sm,
           "s1mono_hollow": [l["hollow"] for l in cyc],
           "s1mono_extent": [l["extent"] for l in cyc]}

try:
    with open(os.path.join(work, "git_head.txt"), encoding="utf-8") as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out = {"_meta": {"stata_version": G("OB_VERSION"), "born_date": G("OB_BORN"),
                 "dash_commit": commit, "extracted": G("OB_WHEN"),
                 "source": "scripts/extract_scheme_layer_truth.do"},
       "probes": probes, "derived": derived}
with open(G("OB_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
for p in written:
    try:
        os.remove(p)
    except OSError:
        pass
try:
    os.rmdir(work)
except OSError:
    pass
print("scheme_layer_truth: wrote %d probes" % len(probes))
end
