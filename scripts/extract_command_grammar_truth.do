*! extract_command_grammar_truth.do -- WP-35 section 35-09: what twoway
*! does with the command grammar dash reads before any option.
*!
*!   case.<Word>   a plot-type word written with a capital letter
*!                 (twoway <Word> <its variables>): rc and first error
*!                 line, and the rc of the same word in lower case
*!                 (lc_rc).
*!   empty.svg.*   twoway with no plot (bare, and with title(T)): the
*!                 exported SVG's <line> count and its texts.
*!   empty.<opt>   twoway, <opt> -- the axis, scale, line, tick and title
*!                 options and by() on a graph with no plot -- with
*!                 empty.order (two at once), empty.if and empty.bars.
*!   group.<form>  a bare plot after a parenthesised group, and the forms
*!                 around it: rc, first line, the plots drawn (count and
*!                 style names, p<n> or p<n>line).
*!   inner.<form>  || inside one parenthesised group.
*!   generic.nosuchtype  twoway nosuchtype mpg weight.
*!
*! Output: test/fixtures/command_grammar_truth.json
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_command_grammar_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 255
set graphics off

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zg_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zg_bad' {
    display as error "extract_command_grammar_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zg_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zg_rc' | _rc {
    local _zg_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_command_grammar_truth.do: `_zg_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZG_REPO "`repo'"
global ZG_OUT "${ZG_REPO}/test/fixtures/command_grammar_truth.json"

if `"`c(python_exec)'"' == "" {
    display as error "extract_command_grammar_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

local work "`c(tmpdir)'dash_grammar_probe"
capture mkdir "`work'"
global ZG_WORK "`work'"

quietly shell git -C "${ZG_REPO}" rev-parse HEAD > "${ZG_WORK}/git_head.txt"
global ZG_VERSION "`c(stata_version)'"
global ZG_BORN "`c(born_date)'"
global ZG_WHEN "`c(current_date)' `c(current_time)'"

sysuse auto, clear
gen yl = mpg - 1
gen yh = mpg + 1
gen gx = mod(_n - 1, 9) + 1 if _n <= 72
gen gy = floor((_n - 1) / 9) + 1 if _n <= 72
gen gz = gx * gy + gy

* One probe: twoway <text> under the default graph name, so .Graph reads
* it.  Writes <work>/<id>.log (the output), <id>.svg when svg is 1, and
* the globals ZG_RC_<id> and ZG_PLOTS_<id> (the plots' style names).
capture program drop _zg_probe
program define _zg_probe
    args id text svg
    capture graph drop _all
    quietly log using "${ZG_WORK}/`id'.log", replace text name(zg)
    capture noisily twoway `text'
    local rc = _rc
    quietly log close zg
    global ZG_RC_`id' = `rc'
    local pl ""
    if !`rc' {
        local k 1
        while "`.Graph.plotregion1.plot`k'.isa'" == "class" {
            local pl "`pl' `.Graph.plotregion1.plot`k'.style.stylename'"
            local ++k
        }
        if "`svg'" == "1" {
            capture graph export "${ZG_WORK}/`id'.svg", name(Graph) replace as(svg)
        }
    }
    global ZG_PLOTS_`id' "`pl'"
    capture graph drop _all
end

* ---- case.<Word> ----
local words Sc Li Con Hist Rsc Rl Rcon Fun Fn Mband Histogram Contour ///
    Scatter SCATTER Line Bar BAR LFIT Area Rcap Function Scatteri Mbands ///
    Connected Kdensity Pcarrowi Lowess
global ZG_WORDS "`words'"
foreach w of local words {
    local lw = strlower("`w'")
    if inlist("`lw'", "hist", "histogram", "kdensity") local v "mpg"
    else if inlist("`lw'", "rsc", "rl", "rcon", "rcap") local v "yl yh weight"
    else if inlist("`lw'", "fun", "fn", "function") local v "y = x, range(0 1)"
    else if "`lw'" == "contour" local v "gz gy gx"
    else if "`lw'" == "scatteri" local v "20 2000"
    else if "`lw'" == "pcarrowi" local v "20 2000 30 4000"
    else local v "mpg weight"
    global ZG_CV_`w' "`v'"
    _zg_probe c_`w' "`w' `v'" 0
    _zg_probe l_`w' "`lw' `v'" 0
}

* ---- empty.* ----
local ek svg_bare svg_title xlabel_1_2 ylabel_1_2 xtitle_T ytitle_T ///
    xscale_range yscale_range xline_1 yline_1 xtick_1_2 xmlabel_1_2 ///
    ylabel_angle xlabel_n3 ytitle_blank yscale_off xscale_alt tlabel_1_2 ///
    ttitle_T by_foreign order if bars
global ZG_EK "`ek'"
global ZG_E_svg_bare ""
global ZG_E_svg_title ", title(T)"
global ZG_E_xlabel_1_2 ", xlabel(1 2)"
global ZG_E_ylabel_1_2 ", ylabel(1 2)"
global ZG_E_xtitle_T ", xtitle(T)"
global ZG_E_ytitle_T ", ytitle(T)"
global ZG_E_xscale_range ", xscale(range(1 2))"
global ZG_E_yscale_range ", yscale(range(1 2))"
global ZG_E_xline_1 ", xline(1)"
global ZG_E_yline_1 ", yline(1)"
global ZG_E_xtick_1_2 ", xtick(1 2)"
global ZG_E_xmlabel_1_2 ", xmlabel(1 2)"
global ZG_E_ylabel_angle ", ylabel(, angle(0))"
global ZG_E_xlabel_n3 ", xlabel(#3)"
global ZG_E_ytitle_blank `", ytitle("")"'
global ZG_E_yscale_off ", yscale(off)"
global ZG_E_xscale_alt ", xscale(alt)"
global ZG_E_tlabel_1_2 ", tlabel(1 2)"
global ZG_E_ttitle_T ", ttitle(T)"
global ZG_E_by_foreign ", by(foreign)"
global ZG_E_order ", ytitle(T) xlabel(1 2)"
global ZG_E_if "if foreign, xlabel(1 2)"
global ZG_E_bars "||, xlabel(1 2)"
foreach k of local ek {
    local svg = cond(substr("`k'", 1, 4) == "svg_", 1, 0)
    _zg_probe e_`k' `"${ZG_E_`k'}"' `svg'
}

* ---- empty.order_names: the order twoway refuses the option names in ----
* Every name at once (one representative option each); the name refused
* first is recorded and dropped, and the rest are asked again.
python:
import re
from sfi import Macro


def _zg_first_line(path, out):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read().replace("\n> ", "")
    except OSError:
        text = ""
    line = ""
    for ln in text.splitlines():
        s = ln.strip()
        if not s or s.startswith(". ") or re.match(r"^r\(\d+\);$", s):
            continue
        line = s
        break
    Macro.setLocal(out, line)
end
local left xlabel ylabel xtitle ytitle xscale yscale xline yline xtick xmlabel tlabel ttitle by
global ZG_N_xlabel "xlabel(1 2)"
global ZG_N_ylabel "ylabel(1 2)"
global ZG_N_xtitle "xtitle(T)"
global ZG_N_ytitle "ytitle(T)"
global ZG_N_xscale "xscale(range(1 2))"
global ZG_N_yscale "yscale(range(1 2))"
global ZG_N_xline "xline(1)"
global ZG_N_yline "yline(1)"
global ZG_N_xtick "xtick(1 2)"
global ZG_N_xmlabel "xmlabel(1 2)"
global ZG_N_tlabel "tlabel(1 2)"
global ZG_N_ttitle "ttitle(T)"
global ZG_N_by "by(foreign)"
local order ""
local lines ""
while "`left'" != "" {
    local o ""
    foreach n of local left {
        local o "`o' ${ZG_N_`n'}"
    }
    capture graph drop _all
    quietly log using "${ZG_WORK}/ord.log", replace text name(zg)
    capture noisily twoway, `o'
    quietly log close zg
    python: _zg_first_line(Macro.getGlobal("ZG_WORK") + "/ord.log", "fl")
    * The name: the word before "(", a plural's s dropped; by()'s own
    * line is xlabels(#4) with no x label given.
    local w = substr(`"`fl'"', 1, strpos(`"`fl'"', "(") - 1)
    if inlist("`w'", "xlabels", "ylabels", "xlines", "ylines", "xticks", "xmlabels", "tlabels") {
        local w = substr("`w'", 1, strlen("`w'") - 1)
    }
    if substr(`"`fl'"', 1, 11) == "xlabels(#4)" & !`: list posof "xlabel" in left' local w by
    if !`: list posof "`w'" in left' {
        display as error `"order probe: `fl' names no option left (`left')"'
        exit 9
    }
    local order "`order' `w'"
    local left : list left - w
}
global ZG_ORDER "`order'"

* ---- group.* and inner.* ----
local gk bare_after bare_after_bars two_then_bare bars_group_bare junk ///
    bare_then_group number pipe bare_title
global ZG_GK "`gk'"
global ZG_G_bare_after "(scatter mpg weight) line mpg weight"
global ZG_G_bare_after_bars "(scatter mpg weight) line mpg weight || scatter price weight"
global ZG_G_two_then_bare "(scatter mpg weight) (line mpg weight) scatter price weight"
global ZG_G_bars_group_bare "scatter mpg weight || (line mpg weight) scatter price weight"
global ZG_G_junk "(scatter mpg weight) junk (line mpg weight)"
global ZG_G_bare_then_group "(scatter mpg weight) line mpg weight (line price weight)"
global ZG_G_number "(scatter mpg weight) 123"
global ZG_G_pipe "(scatter mpg weight) | (line mpg weight)"
global ZG_G_bare_title "(scatter mpg weight) line mpg weight, title(T)"
foreach k of local gk {
    _zg_probe g_`k' "${ZG_G_`k'}" 0
}
local ik bare comma title then_group piece_comma
global ZG_IK "`ik'"
global ZG_I_bare "(scatter mpg weight || line mpg weight)"
global ZG_I_comma "(scatter mpg weight || line mpg weight),"
global ZG_I_title "(scatter mpg weight || line mpg weight), title(T)"
global ZG_I_then_group "(scatter mpg weight || line mpg weight) (scatter price weight)"
global ZG_I_piece_comma "(scatter mpg weight, mcolor(red) || line mpg weight)"
foreach k of local ik {
    _zg_probe i_`k' "${ZG_I_`k'}" 0
}

* ---- generic.nosuchtype ----
_zg_probe n_nosuchtype "nosuchtype mpg weight" 0

python:
import json, os, re
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


work = G("ZG_WORK")


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def first_line(pid):
    """The first line twoway printed after the command's echo."""
    text = read(os.path.join(work, pid + ".log")).replace("\n> ", "")
    for ln in text.splitlines():
        s = ln.strip()
        if not s or s.startswith(". ") or re.match(r"^r\(\d+\);$", s):
            continue
        return s
    return ""


def row(pid, cmd):
    rc = int(float(G("ZG_RC_" + pid)))
    plots = G("ZG_PLOTS_" + pid).split()
    return {"cmd": cmd, "rc": rc, "message": first_line(pid) if rc else "",
            "plots": plots, "nplots": len(plots)}


def svg(pid):
    text = read(os.path.join(work, pid + ".svg"))
    texts = [re.sub(r"\s+", " ", t.replace(" ", " ")).strip()
             for t in re.findall(r"<text[^>]*>(.*?)</text>", text, re.S)]
    return {"lines": len(re.findall(r"<line\b", text)),
            "texts": [t for t in texts if t]}


out = {"_meta": {"stata_version": G("ZG_VERSION"), "born_date": G("ZG_BORN"),
                 "dash_commit": read(os.path.join(work, "git_head.txt")).strip(),
                 "extracted": G("ZG_WHEN"),
                 "source": "scripts/extract_command_grammar_truth.do"}}
for w in G("ZG_WORDS").split():
    r = row("c_" + w, "twoway %s %s" % (w, G("ZG_CV_" + w)))
    r["lc_rc"] = int(float(G("ZG_RC_l_" + w)))
    out["case." + w] = r
order = []
for k in G("ZG_EK").split():
    r = row("e_" + k, ("twoway " + G("ZG_E_" + k)).replace("twoway ,", "twoway,").strip())
    if k.startswith("svg_"):
        r.update(svg("e_" + k))
        out["empty.svg." + k[4:]] = r
    else:
        out["empty." + k] = r
        if k not in ("order", "if", "bars"):
            order.append(k)
out["empty.keys"] = order
out["empty.order_names"] = G("ZG_ORDER").split()
for k in G("ZG_GK").split():
    out["group." + k] = row("g_" + k, "twoway " + G("ZG_G_" + k))
for k in G("ZG_IK").split():
    out["inner." + k] = row("i_" + k, "twoway " + G("ZG_I_" + k))
out["generic.nosuchtype"] = row("n_nosuchtype", "twoway nosuchtype mpg weight")
with open(G("ZG_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
for f in os.listdir(work):
    if f.endswith((".log", ".svg")) or f == "git_head.txt":
        try:
            os.remove(os.path.join(work, f))
        except OSError:
            pass
print("wrote", G("ZG_OUT"), len(out) - 1, "keys")
end
