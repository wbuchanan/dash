*! extract_ci_plot_index_truth.do -- measure the p# each twoway layer is
*! drawn in when ci fits (lfitci, qfitci, lpolyci, fpfitci) take two plots,
*! from twoway's own class values: every graph is drawn with nodraw and
*! each layer's p#-styled plot (a ci layer's line, the plot after its band)
*! is read from .Graph.plotregion1.plot<k>.style.stylename (p<n>, p<n>line,
*! ...).  Also the s2color p1-p15 colours (marker.fillcolor.rgb of fifteen
*! scatters).  twoway only: the output is the same before and after dash
*! changes.
*!
*! Output: test/fixtures/ci_plot_index_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_ci_plot_index_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zc_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zc_bad' {
    display as error "extract_ci_plot_index_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zc_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zc_rc' | _rc {
    local _zc_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_ci_plot_index_truth.do: `_zc_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZC_REPO "`repo'"
global ZC_OUT "${ZC_REPO}/test/fixtures/ci_plot_index_truth.json"

adopath ++ "${ZC_REPO}"
global dash_nobrowser 1

local work "`c(tmpdir)'dash_ci_plot_index_probe"
capture mkdir "`work'"
global ZC_WORK "`work'"

if `"`c(python_exec)'"' == "" {
    display as error "extract_ci_plot_index_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

quietly shell git -C "${ZC_REPO}" rev-parse HEAD > "${ZC_WORK}/git_head.txt"
global ZC_VERSION "`c(stata_version)'"
global ZC_BORN "`c(born_date)'"
global ZC_WHEN "`c(current_date)' `c(current_time)'"

* The custom scheme z1 (test/test_ci_plot_index.py _Z1): s2color with p1
* vthick, p14 thick and p15 vvthick lines.
tempname fh
file open `fh' using "${ZC_WORK}/scheme-z1.scheme", write text replace
file write `fh' "#include s2color" _n "linewidth p1 vthick" _n ///
    "linewidth p15 vvthick" _n "linewidth p14 thick" _n
file close `fh'
adopath ++ "${ZC_WORK}"

sysuse auto, clear
quietly generate lo = price - 1000
quietly generate hi = price + 1000
sort weight

* The twoway plot of each layer type.
local cmd_scatter   "scatter mpg weight"
local cmd_line      "line mpg weight"
local cmd_connected "connected mpg weight"
local cmd_lfit      "lfit mpg weight"
local cmd_lfitci    "lfitci mpg weight"
local cmd_qfitci    "qfitci mpg weight"
local cmd_lpolyci   "lpolyci mpg weight"
local cmd_fpfitci   "fpfitci mpg weight"
local cmd_rarea     "rarea lo hi weight"
local cmd_rcap      "rcap lo hi weight"
local cmd_rcapsym   "rcapsym lo hi weight"
local cmd_pcarrow   "pcarrow lo weight hi weight"
local cmd_histogram "histogram price"
local cmd_kdensity  "kdensity price"
local ci_types "lfitci qfitci lpolyci fpfitci"

* Each case: id|scheme|layers ("N*scatter" is N scatter layers).
local ncase 0
foreach c in ///
    "lfitci_lfitci_lfit|s2color|lfitci lfitci lfit" ///
    "scatter_lfitci_scatter|s2color|scatter lfitci scatter" ///
    "qfitci_scatter|s2color|qfitci scatter" ///
    "lpolyci_line|s2color|lpolyci line" ///
    "fpfitci_connected|s2color|fpfitci connected" ///
    "rarea_rcap_scatter|s2color|rarea rcap scatter" ///
    "two_y_scatter_lfit|s2color|scatter scatter lfit" ///
    "lfitci_rcapsym_pcarrow_scatter|s2color|lfitci rcapsym pcarrow scatter" ///
    "histogram_lfitci_kdensity|s2color|histogram lfitci kdensity" ///
    "eight_lfitci_scatter|s2color|lfitci lfitci lfitci lfitci lfitci lfitci lfitci lfitci scatter" ///
    "seven_lfitci_qfitci_line|z1|lfitci lfitci lfitci lfitci lfitci lfitci lfitci qfitci line" ///
    "s1mono_lfitci_lfitci_line|s1mono|lfitci lfitci line" ///
    "s1mono_scatter_lpolyci_scatter|s1mono|scatter lpolyci scatter" ///
    "z1_12_scatters_lfitci_scatter|z1|12*scatter lfitci scatter" ///
    "z1_13_scatters_lfitci_scatter|z1|13*scatter lfitci scatter" ///
    "z1_14_scatters_lfitci_scatter|z1|14*scatter lfitci scatter" ///
    "z1_15_scatters_lfitci_scatter|z1|15*scatter lfitci scatter" ///
    "z1_28_scatters_lfitci_scatter|z1|28*scatter lfitci scatter" ///
    "z1_29_scatters_lfitci_scatter|z1|29*scatter lfitci scatter" {
    local ++ncase
    gettoken id rest : c, parse("|")
    gettoken bar rest : rest, parse("|")
    gettoken scheme rest : rest, parse("|")
    gettoken bar layers : rest, parse("|")
    * Spell the layers out; each layer's p#-styled plot number.
    local types ""
    foreach t of local layers {
        if strpos("`t'", "*") {
            local n = real(substr("`t'", 1, strpos("`t'", "*") - 1))
            local typ = substr("`t'", strpos("`t'", "*") + 1, .)
            forvalues j = 1/`n' {
                local types "`types' `typ'"
            }
        }
        else local types "`types' `t'"
    }
    local cmd ""
    local plot 0
    local which ""
    foreach t of local types {
        local cmd `"`cmd' (`cmd_`t'')"'
        if `: list t in ci_types' local plot = `plot' + 2
        else local plot = `plot' + 1
        local which "`which' `plot'"
    }
    set scheme `scheme'
    quietly twoway `cmd', nodraw legend(off)
    local got ""
    foreach k of local which {
        local s "`.Graph.plotregion1.plot`k'.style.stylename'"
        if "`s'" == "" local s "."
        local got "`got' `s'"
    }
    global ZC_C`ncase' "`id'|`scheme'|`layers'|`got'|`which'"
    display as text "ZC `id': `got'"
}
global ZC_NCASE `ncase'

* The s2color p1-p15 colours.
set scheme s2color
local cmd ""
forvalues j = 1/15 {
    local cmd `"`cmd' (scatter mpg weight)"'
}
quietly twoway `cmd', nodraw legend(off)
local rgb ""
forvalues j = 1/15 {
    local r "`.Graph.plotregion1.plot`j'.style.marker.fillcolor.rgb'"
    local rgb "`rgb'|`r'"
}
global ZC_RGB "`rgb'"

python:
import json, os, re
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


def pnum(s, plot):
    """The p# of style s drawn as plot number plot.  A plot whose style is
    not a p# (histogram draws in its own style, 'histogram', wherever it
    stands) takes the p# of its place in the fifteen-plot cycle."""
    m = re.match(r"^p(\d+)", s)
    if not m:
        return (plot - 1) % 15 + 1
    # A seriesid of 0 is drawn as p1.
    return max(int(m.group(1)), 1)


cases = []
for i in range(1, int(G("ZC_NCASE")) + 1):
    cid, scheme, layers, got, plots = G("ZC_C%d" % i).split("|")
    layers = layers.split()
    styles = got.split()
    ps = [pnum(s, int(k)) for s, k in zip(styles, plots.split())]
    lead = 0
    if "*" in layers[0]:
        lead = int(layers[0].split("*")[0])
        # The leading scatters cycle p1..p15; the case lists only the rest.
        if ps[:lead] != [k % 15 + 1 for k in range(lead)]:
            raise SystemExit("extract_ci_plot_index_truth.do: %s leading scatters %r" % (cid, ps[:lead]))
    cases.append({"id": cid, "scheme": scheme, "layers": layers,
                  "pstyle": ps[lead:], "styles": styles[lead:]})

cols = []
for r in G("ZC_RGB").strip("|").split("|"):
    cols.append("".join("%02x" % int(v) for v in r.split()[:3]))

out = {
    "_about": ("Measured with " + G("ZC_VERSION") + " (console, batch) on "
               "sysuse auto (lo = price - 1000, hi = price + 1000): each graph "
               "is drawn with nodraw and each layer's p#-styled plot -- for a "
               "ci fit (lfitci, qfitci, lpolyci, fpfitci), which draws two "
               "plots, its band (pstyle ci) then its line, the line -- is read "
               "from .Graph.plotregion1.plot<k>.style.stylename (p<n> or "
               "p<n>line; p0 is drawn as p1).  twoway_lfitci_parse.class gives "
               "the line seriesid(`seriesid'-1), so a layer that is plot n of "
               "the graph draws in p((n-1) mod 15 + 1), and a ci layer whose "
               "line is plot n in p(((n-1) mod 15 + 1) - 1), p1 where that is "
               "0.  'layers' are dash's plot entries; 'pstyle' is the 1-based "
               "p# of each layer.  z1 is #include s2color, linewidth p1 "
               "vthick, p14 thick, p15 vvthick.  'styles' is each listed "
               "layer's stylename; a layer whose style is not a p# "
               "(histogram's own 'histogram') is given the p# of its plot "
               "number in the fifteen-plot cycle."),
    "p_colors": {"s2color": cols},
    "cases": cases,
    "_cases_note": ("An 'N*scatter' entry is N scatter layers whose pstyles "
                    "are 1..N cycling through 15 (measured, checked by the "
                    "generator, not listed); 'pstyle' then lists only the "
                    "layers after them."),
}
work = G("ZC_WORK")
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZC_VERSION"), "born_date": G("ZC_BORN"),
                "dash_commit": commit, "extracted": G("ZC_WHEN"),
                "source": "scripts/extract_ci_plot_index_truth.do"}
with open(G("ZC_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1)
    fh.write("\n")
for f in ("git_head.txt", "scheme-z1.scheme"):
    try:
        os.remove(os.path.join(work, f))
    except OSError:
        pass
print("wrote", G("ZC_OUT"))
end
