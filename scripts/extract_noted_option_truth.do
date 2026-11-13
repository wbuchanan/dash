*! extract_noted_option_truth.do -- WP-32: what twoway does with each
*! option dash declares and names in its note as not drawn ("ignoring
*! unsupported option(s): ..."), on every one of the forty-four plot types
*! dash draws (BUGS.md "dash names in its note, as not drawn, options
*! twoway refuses on that plot type").
*!
*! For each probe: twoway's rc and first error line for the option alone on
*! each type, and -- where twoway takes it -- whether the graph twoway
*! draws differs from the one it draws without it (graph export SVG, its
*! <desc> lines and per-export ids aside): false for the same picture,
*! "order" for the same marks drawn in another order, true for another
*! picture, null where twoway refuses it or two exports of the plain graph
*! already differ in what they draw); dash's rc, first error line and note on each type.
*! Then twoway's and dash's answer to each graph-level probe after the plot
*! groups' comma, and to bare replace in each position.
*!
*! Output: test/fixtures/noted_option_truth.json
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_noted_option_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 255
set graphics off

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zn_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zn_bad' {
    display as error "extract_noted_option_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zn_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zn_rc' | _rc {
    local _zn_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_noted_option_truth.do: `_zn_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZN_REPO "`repo'"
global ZN_OUT "${ZN_REPO}/test/fixtures/noted_option_truth.json"

adopath ++ "${ZN_REPO}"
quietly do "${ZN_REPO}/dash_parse.mata"
quietly do "${ZN_REPO}/dash.ado"
global dash_nobrowser 1

local work "`c(tmpdir)'dash_noted_probe"
capture mkdir "`work'"
global ZN_WORK "`work'"


quietly shell git -C "${ZN_REPO}" rev-parse HEAD > "${ZN_WORK}/git_head.txt"
global ZN_VERSION "`c(stata_version)'"
global ZN_BORN "`c(born_date)'"
global ZN_WHEN "`c(current_date)' `c(current_time)'"


sysuse auto, clear
gen yl = mpg - 1
gen yh = mpg + 1
gen t = _n
tsset t
* contour and contourline on a grid (9 by 8, z = x*y + y): on auto's
* scattered points twoway interpolates, and two exports of the same
* contour differ in their band vertices; on a grid, with the seed set
* before each graph, two exports are the same (measured 19oct2026).
gen gx = mod(_n - 1, 9) + 1 if _n <= 72
gen gy = floor((_n - 1) / 9) + 1 if _n <= 72
gen gz = gx * gy + gy

* The forty-four types and the command each is asked with
* (extract_unknown_option_truth.do's).
local types scatter line connected area bar spike dropline dot tsline tsrline ///
    rarea rbar rspike rcap rline rconnected rcapsym rscatter rpcap rpspike ///
    contour contourline ///
    pcspike pccapsym pcarrow pcbarrow pcscatter pci pcarrowi scatteri ///
    lfit qfit lfitci qfitci fpfit fpfitci lowess lpoly lpolyci mspline mband ///
    kdensity histogram function
global ZN_TYPES "`types'"
local k 0
foreach t of local types {
    local ++k
    if inlist("`t'", "scatter", "line", "connected", "area", "bar", "spike", "dropline", "dot") local a "`t' mpg weight,"
    else if "`t'" == "tsline" local a "tsline mpg,"
    else if "`t'" == "tsrline" local a "tsrline yl yh,"
    else if inlist("`t'", "rarea", "rbar", "rspike", "rcap", "rline", "rconnected", "rcapsym", "rscatter") local a "`t' yl yh weight,"
    else if inlist("`t'", "rpcap", "rpspike") local a "`t' yl yh mpg weight,"
    else if inlist("`t'", "contour", "contourline") local a "`t' gz gy gx,"
    else if inlist("`t'", "pcspike", "pccapsym", "pcarrow", "pcbarrow", "pcscatter") local a "`t' mpg weight trunk turn,"
    else if inlist("`t'", "pci", "pcarrowi") local a "`t' 20 2000 30 4000,"
    else if "`t'" == "scatteri" local a "scatteri 20 2000,"
    else if inlist("`t'", "kdensity", "histogram") local a "`t' mpg,"
    else if "`t'" == "function" local a "function y = x, range(0 1)"
    else local a "`t' mpg weight,"
    local base_`t' "`a'"
    * The picture without the option, once per type.
    capture graph drop _all
    set seed 12345
    capture twoway `a' name(zo, replace)
    if !_rc capture graph export "${ZN_WORK}/b`k'.svg", name(zo) replace as(svg)
    capture graph drop _all
    * The same picture again: a type whose two exports differ (an id
    * numbered per session) is one where "draws" is not read.
    set seed 12345
    capture twoway `a' name(zo, replace)
    if !_rc capture graph export "${ZN_WORK}/c`k'.svg", name(zo) replace as(svg)
    capture graph drop _all
}

* The options on dash.ado's pending lists (_dash_parse_plot_opts,
* _dash_parse_graph_opts, _dash_fold_typed, _dash_recast_named) and bare
* replace (_dash_render's note).
local probes at(mpg) blabel(total) ciopts(lcolor(red)) fitopts(lcolor(red)) ///
    lineopts(lcolor(red)) mlabwidth(thick) bmlinestyle(p3) dlalign(inside) ///
    acolor(red) alcolor(red) alwidth(thick) alpattern(dash) sort sort(price) ///
    outlines lstyle(p3) alstyle(p3) blstyle(p3) mstyle(p3) mlstyle(p3) ///
    mangle(30) barbsize(2) headlabel mwidth baroffset(1) msize(small) ///
    recast(line) filter(foreign) link(g1) play(zn_no_such_recording) replace
* WP-47 basic:PT-11 (section 47-05): the catch-all list
* (catchall_options_truth.json's options), two non-default values each
* where the option takes one, on every type: the plain picture compared.
local probes `"`probes' alalign(outside) alalign(center) blalign(outside) blalign(center)"'
local probes `"`probes' bmsymbol(T) "bmsymbol(O) bmcolor(red) bmsize(large)" bmcolor(red) bmsize(large)"'
local probes `"`probes' "bmlcolor(red) bmlwidth(thick)" bmlwidth(thick) bmlpattern(dash) bmlalign(outside)"'
local probes `"`probes' mlabalignment(top) mlabjustification(right)"'
local probes `"`probes' bartype(spanning) bartype(fixed) dropto(y) dropto(10) numkeys(3) numkeys(1)"'
local probes `"`probes' omitanymiss omitallmiss omitdupmiss omitnothing"'
local probes `"`probes' dlpattern(dot) "dlpattern(dash) dlwidth(thick)" xtransform(ln(X)) xlog"'
local probes `"`probes' zvarlabel(Z) zvarformat(%9.1f) heatlabel dropbase nodropbase"'
local probes `"`probes' back noback bargap(50) below clalign(outside) copyscheme"'
local probes `"`probes' logging nologging refscheme norefscheme rescaling norescaling"'
local probes `"`probes' titling notitling onepanel"'
* WP-49 basic:PT-12 (section 49-02): a second non-default value for each
* catch-all option above probed at one value only, so a type is silent
* only when both values draw twoway's picture unchanged (D-49-02.a).
local probes `"`probes' clalign(center) bargap(-20) zvarformat(%4.0f) bmsize(small) bmcolor(blue)"'
local probes `"`probes' bmlalign(inside) bmlpattern(dot) bmlwidth(vthin)"'
local k 0
foreach one of local probes {
    local ++k
    global ZN_O_`k' `"`one'"'
    local tr ""
    local dr ""
    local j 0
    foreach t of local types {
        local ++j
        quietly log using "${ZN_WORK}/t`k'_`j'.log", replace text name(zn)
        set seed 12345
        capture noisily twoway `base_`t'' `one' name(zo, replace)
        local rc = _rc
        quietly log close zn
        local tr "`tr' `rc'"
        if !`rc' capture graph export "${ZN_WORK}/o`k'_`j'.svg", name(zo) replace as(svg)
        capture graph drop _all
        quietly log using "${ZN_WORK}/d`k'_`j'.log", replace text name(zn)
        capture noisily dash `base_`t'' `one' name(zq)
        local dr "`dr' `=_rc'"
        quietly log close zn
        capture dash clear
    }
    global ZN_TR_`k' "`tr'"
    global ZN_DR_`k' "`dr'"
}
global ZN_K "`k'"

* WP-47 basic:PT-1: headlabel again, on the types that take it, each
* asked WITH marker labels -- mlabel(make), or the immediate types' own
* labels -- since the base commands above draw none for it to move.
* Stored as the probe "headlabel+mlabel" (gen_twoway_takes_table.py
* folds it into headlabel's row); its base pictures are bl<j>/cl<j>.
local labtypes pcspike pccapsym pcarrow pcbarrow pcscatter pci pcarrowi rpcap rpspike
global ZN_LTYPES "`labtypes'"
local tr ""
local dr ""
local j 0
foreach t of local labtypes {
    local ++j
    if inlist("`t'", "pci", "pcarrowi") local a `"`t' 20 2000 30 4000 "A" 25 3000 35 4000 (9) "B","'
    else if inlist("`t'", "rpcap", "rpspike") local a "`t' yl yh mpg weight in 1/5, mlabel(make)"
    else local a "`t' mpg weight trunk turn in 1/5, mlabel(make)"
    foreach v in bl cl {
        capture graph drop _all
        set seed 12345
        capture twoway `macval(a)' name(zo, replace)
        if !_rc capture graph export "${ZN_WORK}/`v'`j'.svg", name(zo) replace as(svg)
    }
    capture graph drop _all
    quietly log using "${ZN_WORK}/tl_`j'.log", replace text name(zn)
    set seed 12345
    capture noisily twoway `macval(a)' headlabel name(zo, replace)
    local rc = _rc
    quietly log close zn
    local tr "`tr' `rc'"
    if !`rc' capture graph export "${ZN_WORK}/ol_`j'.svg", name(zo) replace as(svg)
    capture graph drop _all
    quietly log using "${ZN_WORK}/dl_`j'.log", replace text name(zn)
    capture noisily dash `macval(a)' headlabel name(zq)
    local dr "`dr' `=_rc'"
    quietly log close zn
    capture dash clear
}
global ZN_LTR "`tr'"
global ZN_LDR "`dr'"

* WP-47 basic:PT-11 (section 47-05): probes that need another base
* command, each keyed "<option>+<context>" (gen_twoway_takes_table.py
* folds a context key into its option's row).  mlabel: the label types
* with marker labels, mlabel(make) on rows 1-10.  multiy: two y
* variables with missing values (y1 missing in 3/5 and 10, y2 in 4 and
* 10) and three rows doubled, where the omit rules decide which rows a
* line joins.  Base pictures x<c><j>/y<c><j>.
local ctx_mlabel_types scatter line connected rline rconnected rcapsym rscatter dropline spike rspike rcap pcscatter pccapsym lfit
local ctx_mlabel_probes mlabalignment(top) mlabalignment(bottom) mlabjustification(right) mlabjustification(left) "bmsymbol(O) bmcolor(red)"
local ctx_multiy_types scatter line connected area bar spike dropline dot tsline
local ctx_multiy_probes omitanymiss omitallmiss omitdupmiss omitnothing numkeys(1) numkeys(3)
global ZN_CTX "mlabel multiy"
foreach c in mlabel multiy {
    if "`c'" == "multiy" {
        preserve
        gen y1 = mpg
        gen y2 = price / 1000
        replace y1 = . in 3/5
        replace y2 = . in 4
        replace y1 = . in 10
        replace y2 = . in 10
        expand 2 in 1/3
        sort weight, stable
        replace t = _n
        tsset t
    }
    global ZN_CT_`c' "`ctx_`c'_types'"
    local j 0
    foreach t of local ctx_`c'_types {
        local ++j
        if "`c'" == "mlabel" {
            if inlist("`t'", "rline", "rconnected", "rcapsym", "rscatter", "rspike", "rcap") local a "`t' yl yh weight in 1/10, mlabel(make)"
            else if inlist("`t'", "pcscatter", "pccapsym") local a "`t' mpg weight trunk turn in 1/10, mlabel(make)"
            else local a "`t' mpg weight in 1/10, mlabel(make)"
        }
        else {
            if "`t'" == "tsline" local a "tsline y1 y2,"
            else if inlist("`t'", "line", "connected") local a "`t' y1 y2 weight, sort"
            else local a "`t' y1 y2 weight,"
        }
        local cb_`c'_`j' "`a'"
        foreach v in x y {
            capture graph drop _all
            set seed 12345
            capture twoway `a' name(zo, replace)
            if !_rc capture graph export "${ZN_WORK}/`v'`c'`j'.svg", name(zo) replace as(svg)
        }
        capture graph drop _all
    }
    local k 0
    foreach one of local ctx_`c'_probes {
        local ++k
        global ZN_CO_`c'_`k' `"`one'"'
        local tr ""
        local dr ""
        local j 0
        foreach t of local ctx_`c'_types {
            local ++j
            quietly log using "${ZN_WORK}/tc`c'`k'_`j'.log", replace text name(zn)
            set seed 12345
            capture noisily twoway `cb_`c'_`j'' `one' name(zo, replace)
            local rc = _rc
            quietly log close zn
            local tr "`tr' `rc'"
            if !`rc' capture graph export "${ZN_WORK}/oc`c'`k'_`j'.svg", name(zo) replace as(svg)
            capture graph drop _all
            quietly log using "${ZN_WORK}/dc`c'`k'_`j'.log", replace text name(zn)
            capture noisily dash `cb_`c'_`j'' `one' name(zq)
            local dr "`dr' `=_rc'"
            quietly log close zn
            capture dash clear
        }
        global ZN_CTR_`c'_`k' "`tr'"
        global ZN_CDR_`c'_`k' "`dr'"
    }
    global ZN_CK_`c' "`k'"
    if "`c'" == "multiy" restore
}

* Graph level, and bare replace in each position.
local gl `" "(scatter mpg weight), filter(foreign)" "(scatter mpg weight), link(g1)" "(scatter mpg weight), play(zn_no_such_recording)" "(scatter mpg weight), replace" "scatter mpg weight, replace" "scatter mpg weight, saving(zn_f1) replace" "(scatter mpg weight), saving(zn_f2) replace" "scatter mpg weight, name(zq) replace" "(scatter mpg weight), name(zq) replace" "scatter mpg weight, name(zq) saving(zn_f3) replace" "scatter mpg weight, saving(zn_f4, replace)" "scatter mpg weight || line mpg weight, replace" "'
local j 0
foreach c of local gl {
    local ++j
    global ZN_GC_`j' `"`c'"'
    capture erase "${ZN_WORK}/zn_f`j'.gph"
    quietly log using "${ZN_WORK}/gt`j'.log", replace text name(zn)
    capture noisily twoway `c' nodraw
    global ZN_GT_`j' = _rc
    quietly log close zn
    capture graph drop _all
    quietly log using "${ZN_WORK}/gd`j'.log", replace text name(zn)
    capture noisily dash `c'
    global ZN_GD_`j' = _rc
    quietly log close zn
    capture dash clear
}
global ZN_J "`j'"
foreach f in zn_f1 zn_f2 zn_f3 zn_f4 {
    capture erase "`f'.gph"
    capture erase "`f'.html"
}

* WP-49 basic:PT-12 (section 49-02, D-49-02.a (2)): sub-options of graph
* options, each against its base command without it -- twoway's rc, its
* notes, whether its SVG differs from the base's (two base exports), and
* dash's notes.  Spec "<option>|<sub-option>|<base>|<command>"; the key
* is the command after its comma.  u is mpg / 50 (0 to 1).
gen u = mpg / 50
local s 0
foreach spec in ///
    `"legend|nostack|scatter mpg weight,|scatter mpg weight, legend(nostack)"' ///
    `"legend|angle|scatter mpg weight,|scatter mpg weight, legend(angle(45))"' ///
    `"legend|angle|scatter mpg weight,|scatter mpg weight, legend(angle(90))"' ///
    `"legend|orientation|scatter mpg weight,|scatter mpg weight, legend(orientation(vertical))"' ///
    `"legend|nodrawview|scatter mpg weight,|scatter mpg weight, legend(nodrawview)"' ///
    `"legend|styleonly|scatter mpg weight,|scatter mpg weight, legend(styleonly)"' ///
    `"title|angle|scatter mpg weight, title("T")|scatter mpg weight, title("T", angle(45))"' ///
    `"title|angle|scatter mpg weight, title("T")|scatter mpg weight, title("T", angle(90))"' ///
    `"title|astextbox|scatter mpg weight, title("T")|scatter mpg weight, title("T", astextbox)"' ///
    `"text|angle|scatter mpg weight, text(30 3000 "x")|scatter mpg weight, text(30 3000 "x", angle(45))"' ///
    `"text|angle|scatter mpg weight, text(30 3000 "x")|scatter mpg weight, text(30 3000 "x", angle(90))"' ///
    `"xscale|nolog|scatter mpg weight,|scatter mpg weight, xscale(nolog)"' ///
    `"yscale|noreverse|scatter mpg weight,|scatter mpg weight, yscale(noreverse)"' ///
    `"yscale|ring|scatter mpg weight,|scatter mpg weight, yscale(ring(3))"' ///
    `"yscale|ring|scatter mpg weight,|scatter mpg weight, yscale(ring(1))"' ///
    `"ylabel|labelkeepleadingzero|scatter u weight, ylabel(.1(.1).5)|scatter u weight, ylabel(.1(.1).5, labelkeepleadingzero)"' ///
    `"by|spacers|scatter mpg weight, by(foreign)|scatter mpg weight, by(foreign, spacers(ring(2)))"' ///
    `"subtitle|width|scatter mpg weight, by(foreign)|scatter mpg weight, by(foreign) subtitle(, width(20))"' {
    local ++s
    gettoken so rest : spec, parse("|")
    gettoken bar rest : rest, parse("|")
    gettoken ss rest : rest, parse("|")
    gettoken bar rest : rest, parse("|")
    gettoken sb rest : rest, parse("|")
    gettoken bar sc : rest, parse("|")
    global ZN_SO_`s' "`so'"
    global ZN_SS_`s' "`ss'"
    global ZN_SB_`s' `"`sb'"'
    global ZN_SC_`s' `"`sc'"'
    foreach v in sb sc {
        capture graph drop _all
        set seed 12345
        capture twoway `sb' name(zo, replace)
        if !_rc capture graph export "${ZN_WORK}/`v'`s'.svg", name(zo) replace as(svg)
    }
    capture graph drop _all
    quietly log using "${ZN_WORK}/ts`s'.log", replace text name(zn)
    set seed 12345
    capture noisily twoway `sc' name(zo, replace)
    global ZN_STR_`s' = _rc
    quietly log close zn
    if !${ZN_STR_`s'} capture graph export "${ZN_WORK}/os`s'.svg", name(zo) replace as(svg)
    capture graph drop _all
    * dash on its one-line route (no name()): the page is built, so the
    * renderer's notes are printed too.
    quietly log using "${ZN_WORK}/ds`s'.log", replace text name(zn)
    capture noisily dash `sc'
    global ZN_SDR_`s' = _rc
    quietly log close zn
    capture dash clear
}
global ZN_S "`s'"

* WP-49 LT-25 (section 49-02, the lt25 keys): the named-style probes --
* each command's notes as twoway prints them (every line, in order, a
* note twoway prints twice held twice) and as dash prints them.
local l 0
foreach spec in ///
    `"R_tpos|scatter mpg weight, title("T", position(13))"' ///
    `"R_e1pos|scatter mpg weight, t1title("T", position(13))"' ///
    `"R_tjust|scatter mpg weight, title("T", justification(bogus))"' ///
    `"tj_l|scatter mpg weight, title("T", justification(l))"' ///
    `"C_pbog|contour gz gy gx, clegend(position(13))"' ///
    `"R_tsz|scatter mpg weight, title("T", size(bogus))"' ///
    `"R_lsz|scatter mpg weight, legend(size(bogus))"' ///
    `"mlabgap_abc|scatter mpg weight, mlabel(make) mlabgap(abc)"' ///
    `"L_posfr|scatter mpg weight, legend(pos(4.5))"' ///
    `"R_tcol|scatter mpg weight, title("T", color(bogus))"' ///
    `"R_lcol|scatter mpg weight, legend(color(bogus))"' ///
    `"by_style_foo|scatter mpg weight, by(foreign, style(foo))"' ///
    `"by_scale_abc|scatter mpg weight, by(foreign, scale(abc))"' ///
    `"by_iscale_abc|scatter mpg weight, by(foreign, iscale(abc))"' ///
    `"scale_abc|scatter mpg weight, scale(abc)"' ///
    `"xsize_abc|scatter mpg weight, xsize(abc)"' ///
    `"ysize_abc|scatter mpg weight, ysize(abc)"' ///
    `"st11_legend_bottom|scatter mpg weight, legend(position(bottom))"' ///
    `"st11_legend_ring_i|scatter mpg weight, legend(ring(i))"' ///
    `"st11_connect_di|scatter mpg weight, connect(di)"' ///
    `"st11_text_nor|scatter mpg weight, text(30 3000 "x", placement(nor))"' ///
    `"st11_text_hor|scatter mpg weight, text(30 3000 "x", orientation(hor))"' ///
    `"st11_title_hor|scatter mpg weight, title("T", orientation(hor))"' {
    local ++l
    gettoken lk rest : spec, parse("|")
    gettoken bar lc : rest, parse("|")
    global ZN_LK_`l' "`lk'"
    global ZN_LC_`l' `"`lc'"'
    capture graph drop _all
    quietly log using "${ZN_WORK}/tq`l'.log", replace text name(zn)
    capture noisily twoway `lc' name(zo, replace)
    global ZN_LQT_`l' = _rc
    quietly log close zn
    capture graph drop _all
    quietly log using "${ZN_WORK}/dq`l'.log", replace text name(zn)
    capture noisily dash `lc'
    global ZN_LQD_`l' = _rc
    quietly log close zn
    capture dash clear
}
global ZN_L "`l'"

python:
import json, os, re
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


NOTE = "ignoring unsupported option(s):"


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def note(text):
    """The note's names as printed, its closing parenthesis aside."""
    for ln in text.replace("\n> ", "").splitlines():
        i = ln.find(NOTE)
        if i >= 0:
            s = ln[i + len(NOTE):].strip()
            if ln.lstrip().startswith("(note:") and s.endswith(")"):
                s = s[:-1]
            return s.split()
    return []


def notes(text):
    """Every "(note: ...)" line of the log, in order, its continuation
    lines joined and its blanks after "(note:" made one (WP-49 49-02)."""
    out = []
    for ln in text.replace("\n> ", "").splitlines():
        s = ln.strip()
        if s.startswith("(note:"):
            out.append("(note: " + s[len("(note:"):].strip())
    return out


def first_error(text):
    for s in (ln.strip() for ln in text.replace("\n> ", "").splitlines()):
        if not s or s.startswith(". ") or s.startswith("(note:") or s.startswith("dash: graph"):
            continue
        if (s.startswith("option") or "not allowed" in s or "invalid" in s
                or "not found" in s or "may not" in s or "not" in s):
            return s
    return ""


work = G("ZN_WORK")
types = G("ZN_TYPES").split()

_ID = re.compile(r"\b(path|clipPath|pattern|linearGradient|mask)_[A-Za-z]{8}\b")
_D = re.compile(r'd="([^"]*)"')


def svg_lines(path):
    """The SVG's lines, its <desc> lines aside and the ids Stata draws at
    random per export (path_XXXXXXXX, clipPath_XXXXXXXX) made one."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return None
    return [_ID.sub("ID", ln) for ln in text.splitlines()
            if not ln.strip().startswith("<desc>")]


def unordered(lines):
    """The same lines as a multiset, each path's points sorted: what is
    left when only the order things are drawn in is set aside."""
    def one(ln):
        return _D.sub(lambda m: 'd="%s"' % " ".join(sorted(
            re.findall(r"[ML][^ML]*", m.group(1)))), ln)
    return sorted(one(ln) for ln in lines)


def draws(j, opath, base=("b", "c")):
    """What twoway draws with the option against without it: False for the
    same picture, "order" for the same marks drawn in another order, True
    for a different picture, None where the plain graph's two exports
    already differ in what they draw.  *base* names the plain pictures'
    files (the headlabel+mlabel set's are bl<j>, cl<j>)."""
    b = svg_lines(os.path.join(work, "%s%d.svg" % (base[0], j)))
    c = svg_lines(os.path.join(work, "%s%d.svg" % (base[1], j)))
    o = svg_lines(opath)
    if b is None or c is None or o is None:
        return None
    if unordered(b) != unordered(c):
        return None
    if o == b:
        return False
    if unordered(o) == unordered(b):
        return "order" if b == c else False
    return True
probes = {}
for k in range(1, int(G("ZN_K")) + 1):
    opt = G("ZN_O_%d" % k)
    tr = [int(v) for v in G("ZN_TR_%d" % k).split()]
    dr = [int(v) for v in G("ZN_DR_%d" % k).split()]
    rows = {}
    for j, t in enumerate(types, 1):
        tl = os.path.join(work, "t%d_%d.log" % (k, j))
        dl = os.path.join(work, "d%d_%d.log" % (k, j))
        tt, dt = read(tl), read(dl)
        rows[t] = {"twoway_rc": tr[j - 1],
                   "twoway_message": first_error(tt) if tr[j - 1] else "",
                   "twoway_notes": notes(tt),
                   "twoway_draws": draws(j, os.path.join(work, "o%d_%d.svg" % (k, j))) if tr[j - 1] == 0 else None,
                   "dash_rc": dr[j - 1],
                   "dash_message": first_error(dt) if dr[j - 1] else "",
                   "dash_note": note(dt)}
        for f in (tl, dl):
            try:
                os.remove(f)
            except OSError:
                pass
    probes[opt] = rows
# headlabel with marker labels, on the types that take it only.
ltypes = G("ZN_LTYPES").split()
ltr = [int(v) for v in G("ZN_LTR").split()]
ldr = [int(v) for v in G("ZN_LDR").split()]
rows = {}
for j, t in enumerate(ltypes, 1):
    tl = os.path.join(work, "tl_%d.log" % j)
    dl = os.path.join(work, "dl_%d.log" % j)
    tt, dt = read(tl), read(dl)
    rows[t] = {"twoway_rc": ltr[j - 1],
               "twoway_message": first_error(tt) if ltr[j - 1] else "",
               "twoway_notes": notes(tt),
               "twoway_draws": draws(j, os.path.join(work, "ol_%d.svg" % j),
                                     ("bl", "cl")) if ltr[j - 1] == 0 else None,
               "dash_rc": ldr[j - 1],
               "dash_message": first_error(dt) if ldr[j - 1] else "",
               "dash_note": note(dt)}
    for f in (tl, dl):
        try:
            os.remove(f)
        except OSError:
            pass
probes["headlabel+mlabel"] = rows
# WP-47 basic:PT-11: the context probes, "<option>+<context>".
ctx_files = []
for c in G("ZN_CTX").split():
    ctypes = G("ZN_CT_%s" % c).split()
    for k in range(1, int(G("ZN_CK_%s" % c)) + 1):
        opt = G("ZN_CO_%s_%d" % (c, k))
        tr = [int(v) for v in G("ZN_CTR_%s_%d" % (c, k)).split()]
        dr = [int(v) for v in G("ZN_CDR_%s_%d" % (c, k)).split()]
        rows = {}
        for j, t in enumerate(ctypes, 1):
            tl = os.path.join(work, "tc%s%d_%d.log" % (c, k, j))
            dl = os.path.join(work, "dc%s%d_%d.log" % (c, k, j))
            tt, dt = read(tl), read(dl)
            op = os.path.join(work, "oc%s%d_%d.svg" % (c, k, j))
            ctx_files.append(op)
            rows[t] = {"twoway_rc": tr[j - 1],
                       "twoway_message": first_error(tt) if tr[j - 1] else "",
                       "twoway_notes": notes(tt),
                       "twoway_draws": draws(j, op, ("x" + c, "y" + c)) if tr[j - 1] == 0 else None,
                       "dash_rc": dr[j - 1],
                       "dash_message": first_error(dt) if dr[j - 1] else "",
                       "dash_note": note(dt)}
            for f in (tl, dl):
                try:
                    os.remove(f)
                except OSError:
                    pass
        probes["%s+%s" % (opt, c)] = rows
    ctx_files += [os.path.join(work, "%s%s%d.svg" % (v, c, j)) for v in "xy" for j in range(1, len(ctypes) + 1)]
graph = []
for j in range(1, int(G("ZN_J")) + 1):
    tl = os.path.join(work, "gt%d.log" % j)
    dl = os.path.join(work, "gd%d.log" % j)
    tt, dt = read(tl), read(dl)
    trc, drc = int(G("ZN_GT_%d" % j)), int(G("ZN_GD_%d" % j))
    graph.append({"cmd": G("ZN_GC_%d" % j), "twoway_rc": trc,
                  "twoway_message": first_error(tt) if trc else "",
                  "dash_rc": drc, "dash_message": first_error(dt) if drc else "",
                  "dash_note": note(dt)})
    for f in (tl, dl):
        try:
            os.remove(f)
        except OSError:
            pass
# WP-49 basic:PT-12: the sub-option probes, keyed "<option>(<typed>)".
sub = {}
sub_files = []
for s in range(1, int(G("ZN_S")) + 1):
    tl = os.path.join(work, "ts%d.log" % s)
    dl = os.path.join(work, "ds%d.log" % s)
    tt, dt = read(tl), read(dl)
    trc, drc = int(G("ZN_STR_%d" % s)), int(G("ZN_SDR_%d" % s))
    op = os.path.join(work, "os%d.svg" % s)
    b, c, o = (svg_lines(os.path.join(work, "%s%d.svg" % (v, s)))
               for v in ("sb", "sc", "os"))
    if trc or b is None or c is None or o is None or unordered(b) != unordered(c):
        dr_ = None
    elif o == b or unordered(o) == unordered(b):
        dr_ = False
    else:
        dr_ = True
    sub[G("ZN_SC_%d" % s).split(",", 1)[1].strip()] = {
        "option": G("ZN_SO_%d" % s), "suboption": G("ZN_SS_%d" % s),
        "base": G("ZN_SB_%d" % s), "cmd": G("ZN_SC_%d" % s),
        "twoway_rc": trc, "twoway_message": first_error(tt) if trc else "",
        "twoway_notes": notes(tt), "twoway_draws": dr_,
        "dash_rc": drc, "dash_message": first_error(dt) if drc else "",
        "dash_notes": notes(dt)}
    sub_files += [op] + [os.path.join(work, "%s%d.svg" % (v, s)) for v in ("sb", "sc")]
    for f in (tl, dl):
        try:
            os.remove(f)
        except OSError:
            pass
# WP-49 LT-25: the named-style probes.
lt25 = {}
for q in range(1, int(G("ZN_L")) + 1):
    tl = os.path.join(work, "tq%d.log" % q)
    dl = os.path.join(work, "dq%d.log" % q)
    tt, dt = read(tl), read(dl)
    trc, drc = int(G("ZN_LQT_%d" % q)), int(G("ZN_LQD_%d" % q))
    lt25[G("ZN_LK_%d" % q)] = {
        "cmd": G("ZN_LC_%d" % q), "twoway_rc": trc,
        "twoway_message": first_error(tt) if trc else "",
        "twoway_notes": notes(tt), "dash_rc": drc,
        "dash_message": first_error(dt) if drc else "",
        "dash_notes": notes(dt)}
    for f in (tl, dl):
        try:
            os.remove(f)
        except OSError:
            pass
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out = {"_meta": {"stata_version": G("ZN_VERSION"), "born_date": G("ZN_BORN"),
                 "dash_commit": commit, "extracted": G("ZN_WHEN"),
                 "source": "scripts/extract_noted_option_truth.do"},
       "types": types, "probes": probes, "graph_level": graph,
       "sub_probes": sub, "lt25": lt25}
with open(G("ZN_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
# ZN_KEEP=1 in the environment keeps the SVGs in c(tmpdir)dash_noted_probe
# for reading what twoway draws.
for f in ["git_head.txt"] + ([] if os.environ.get("ZN_KEEP") else ctx_files + sub_files + ["%s%d.svg" % (c, i) for c in "bc" for i in range(1, len(types) + 1)] + ["o%d_%d.svg" % (k, j) for k in range(1, int(G("ZN_K")) + 1) for j in range(1, len(types) + 1)] + ["%s%d.svg" % (c, i) for c in ("bl", "cl", "ol_") for i in range(1, len(ltypes) + 1)]):
    try:
        os.remove(os.path.join(work, f))
    except OSError:
        pass
print("wrote", G("ZN_OUT"), len(probes), "probes,", len(graph), "graph-level,",
      len(sub), "sub-option,", len(lt25), "lt25")
end
