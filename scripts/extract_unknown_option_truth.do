*! extract_unknown_option_truth.do -- WP-32: which option words twoway
*! takes, on which plot types and from which spelling, among the names
*! dash leaves to its catch-all, and the order in which twoway names the
*! first word of a mixed list it refuses (BUGS.md "In a few mixed lists
*! dash names another word than twoway names first, and an unknown
*! lower-case word is noted where twoway refuses it").
*!
*! For each probe (the candidates of extract_catchall_options_truth.do and
*! the graph options twoway's parsers declare): twoway's rc for the option
*! alone on each of the forty-four plot types dash draws, for each shorter
*! spelling and for the other form (a value where it takes none, none
*! where it takes one) on the probe's plot, and dash's rc and note there.
*! twoway's rc for it alone after the plot groups' comma.  Then twoway's
*! rc and message for each mixed list of `orders'.
*!
*! Output: test/fixtures/unknown_option_truth.json
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_unknown_option_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 255

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zu_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zu_bad' {
    display as error "extract_unknown_option_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zu_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zu_rc' | _rc {
    local _zu_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_unknown_option_truth.do: `_zu_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZU_REPO "`repo'"
global ZU_OUT "${ZU_REPO}/test/fixtures/unknown_option_truth.json"

adopath ++ "${ZU_REPO}"
quietly do "${ZU_REPO}/dash_parse.mata"
quietly do "${ZU_REPO}/dash.ado"
global dash_nobrowser 1

local work "`c(tmpdir)'dash_unknown_probe"
capture mkdir "`work'"
global ZU_WORK "`work'"

if `"`c(python_exec)'"' == "" {
    display as error "extract_unknown_option_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

quietly shell git -C "${ZU_REPO}" rev-parse HEAD > "${ZU_WORK}/git_head.txt"
global ZU_VERSION "`c(stata_version)'"
global ZU_BORN "`c(born_date)'"
global ZU_WHEN "`c(current_date)' `c(current_time)'"

sysuse auto, clear
gen yl = mpg - 1
gen yh = mpg + 1
gen t = _n
tsset t

* The forty-four types and the command each is asked with
* (extract_applicability_truth.do's).
local types scatter line connected area bar spike dropline dot tsline tsrline ///
    rarea rbar rspike rcap rline rconnected rcapsym rscatter rpcap rpspike ///
    contour contourline ///
    pcspike pccapsym pcarrow pcbarrow pcscatter pci pcarrowi scatteri ///
    lfit qfit lfitci qfitci fpfit fpfitci lowess lpoly lpolyci mspline mband ///
    kdensity histogram function
global ZU_TYPES "`types'"
foreach t of local types {
    if inlist("`t'", "scatter", "line", "connected", "area", "bar", "spike", "dropline", "dot") local a "`t' mpg weight,"
    else if "`t'" == "tsline" local a "tsline mpg,"
    else if "`t'" == "tsrline" local a "tsrline yl yh,"
    else if inlist("`t'", "rarea", "rbar", "rspike", "rcap", "rline", "rconnected", "rcapsym", "rscatter") local a "`t' yl yh weight,"
    else if inlist("`t'", "rpcap", "rpspike") local a "`t' yl yh mpg weight,"
    else if inlist("`t'", "contour", "contourline") local a "`t' mpg weight length,"
    else if inlist("`t'", "pcspike", "pccapsym", "pcarrow", "pcbarrow", "pcscatter") local a "`t' mpg weight trunk turn,"
    else if inlist("`t'", "pci", "pcarrowi") local a "`t' 20 2000 30 4000,"
    else if "`t'" == "scatteri" local a "scatteri 20 2000,"
    else if inlist("`t'", "kdensity", "histogram") local a "`t' mpg,"
    else if "`t'" == "function" local a "function y = x, range(0 1)"
    else local a "`t' mpg weight,"
    local base_`t' "`a'"
}

local probes ""
local probes `"`probes' "afcolor;scatter mpg weight;afcolor(red)""'
local probes `"`probes' "afintensity;scatter mpg weight;afintensity(50)""'
local probes `"`probes' "alalign;scatter mpg weight;alalign(inside)""'
local probes `"`probes' "bcolor;scatter mpg weight;bcolor(red)""'
local probes `"`probes' "bfintensity;scatter mpg weight;bfintensity(50)""'
local probes `"`probes' "blalign;scatter mpg weight;blalign(inside)""'
local probes `"`probes' "blpattern;scatter mpg weight;blpattern(dash)""'
local probes `"`probes' "blwidth;scatter mpg weight;blwidth(thin)""'
local probes `"`probes' "bmcolor;scatter mpg weight;bmcolor(red)""'
local probes `"`probes' "bmlalign;scatter mpg weight;bmlalign(inside)""'
local probes `"`probes' "bmlcolor;scatter mpg weight;bmlcolor(red)""'
local probes `"`probes' "bmlpattern;scatter mpg weight;bmlpattern(dash)""'
local probes `"`probes' "bmlwidth;scatter mpg weight;bmlwidth(thin)""'
local probes `"`probes' "bmsize;scatter mpg weight;bmsize(small)""'
local probes `"`probes' "bmsymbol;scatter mpg weight;bmsymbol(O)""'
local probes `"`probes' "bsymbol;scatter mpg weight;bsymbol(O)""'
local probes `"`probes' "clalign;line mpg weight;clalign(inside)""'
local probes `"`probes' "dlpattern;dot mpg weight;dlpattern(dash)""'
local probes `"`probes' "mlabels;scatter mpg weight;mlabels(make)""'
local probes `"`probes' "mlabalignment;scatter mpg weight;mlabel(make) mlabalignment(top)""'
local probes `"`probes' "mlabfontface;scatter mpg weight;mlabel(make) mlabfontface(Courier)""'
local probes `"`probes' "mlabjustification;scatter mpg weight;mlabel(make) mlabjustification(left)""'
local probes `"`probes' "msymangle;scatter mpg weight;msymangle(45)""'
local probes `"`probes' "symbol;scatter mpg weight;symbol(O)""'
local probes `"`probes' "numkeys;scatter mpg weight;numkeys(1)""'
local probes `"`probes' "omitallmiss;scatter mpg weight;omitallmiss""'
local probes `"`probes' "omitanymiss;scatter mpg weight;omitanymiss""'
local probes `"`probes' "omitdupmiss;scatter mpg weight;omitdupmiss""'
local probes `"`probes' "omitnothing;scatter mpg weight;omitnothing""'
local probes `"`probes' "dropbase;scatter mpg weight;dropbase""'
local probes `"`probes' "bartype;bar mpg weight;bartype(spanning)""'
local probes `"`probes' "bargap;bar mpg weight;bargap(10)""'
local probes `"`probes' "dropto;bar mpg weight;dropto(0)""'
local probes `"`probes' "heatlabel;contour mpg weight length;heatlabel""'
local probes `"`probes' "zvarlabel;contour mpg weight length;zvarlabel(z)""'
local probes `"`probes' "zvarformat;contour mpg weight length;zvarformat(%9.2f)""'
local probes `"`probes' "xlog;lfit mpg weight;xlog""'
local probes `"`probes' "xtransform;lfit mpg weight;xtransform(ln(X))""'
local probes `"`probes' "fit;lfitci mpg weight;fit""'
local probes `"`probes' "pwidth;lpolyci mpg weight;pwidth(1)""'
local probes `"`probes' "var;lpolyci mpg weight;var(1)""'
local probes `"`probes' "weight;lowess mpg weight;weight""'
local probes `"`probes' "back;mspline mpg weight;back""'
local probes `"`probes' "noback;mspline mpg weight;noback""'
local probes `"`probes' "subchar;function y = x, range(0 1);subchar(x)""'
local probes `"`probes' "biweight;kdensity mpg;biweight""'
local probes `"`probes' "cosine;kdensity mpg;cosine""'
local probes `"`probes' "epan2;kdensity mpg;epan2""'
local probes `"`probes' "epanechnikov;kdensity mpg;epanechnikov""'
local probes `"`probes' "gaussian;kdensity mpg;gaussian""'
local probes `"`probes' "parzen;kdensity mpg;parzen""'
local probes `"`probes' "rectangle;kdensity mpg;rectangle""'
local probes `"`probes' "triangle;kdensity mpg;triangle""'
local probes `"`probes' "onepanel;tsline mpg;onepanel""'
local probes `"`probes' "below;scatter mpg weight;below""'
local probes `"`probes' "copyscheme;scatter mpg weight;copyscheme""'
local probes `"`probes' "maxaxes;scatter mpg weight;maxaxes(2)""'
local probes `"`probes' "logging;scatter mpg weight;logging""'
local probes `"`probes' "nologging;scatter mpg weight;nologging""'
local probes `"`probes' "refscheme;scatter mpg weight;refscheme""'
local probes `"`probes' "norefscheme;scatter mpg weight;norefscheme""'
local probes `"`probes' "rescaling;scatter mpg weight;rescaling""'
local probes `"`probes' "norescaling;scatter mpg weight;norescaling""'
local probes `"`probes' "titling;scatter mpg weight;titling""'
local probes `"`probes' "notitling;scatter mpg weight;notitling""'
* The names GAPS3 J1 listed as reaching the note, declared since: each
* recorded so the fixture shows what each does now.
local probes `"`probes' "atobs;lfit mpg weight;atobs""'
local probes `"`probes' "ciplot;lfitci mpg weight;ciplot(rline)""'
local probes `"`probes' "fitplot;lfitci mpg weight;fitplot(scatter)""'
local probes `"`probes' "nofit;lfitci mpg weight;nofit""'
local probes `"`probes' "boundary;kdensity mpg;boundary""'
local probes `"`probes' "headlabel;pcarrow mpg weight trunk turn;headlabel""'
local probes `"`probes' "mwidth;rbar yl yh weight;mwidth""'
local probes `"`probes' "baroffset;rbar yl yh weight;baroffset(1)""'
local probes `"`probes' "nodropbase;scatter mpg weight;nodropbase""'
local probes `"`probes' "clegend;contour mpg weight length;clegend(off)""'
local probes `"`probes' "plegend;scatter mpg weight;plegend(off)""'
local probes `"`probes' "pcycle;scatter mpg weight;pcycle(3)""'
local probes `"`probes' "colorstart;scatter mpg weight;colorvar(price) colorstart(red)""'
local probes `"`probes' "colorend;scatter mpg weight;colorvar(price) colorend(blue)""'
local probes `"`probes' "colorrule;scatter mpg weight;colorvar(price) colorrule(hue)""'
local probes `"`probes' "colorkeysreverse;scatter mpg weight;colorvar(price) colorkeysreverse""'
local probes `"`probes' "colorallowmultiple;scatter mpg weight;colorvar(price) colorallowmultiple""'
local probes `"`probes' "colorkeysrange;scatter mpg weight;colorvar(price) colorkeysrange""'
local probes `"`probes' "colorfillonly;scatter mpg weight;colorvar(price) colorfillonly""'
local probes `"`probes' "colorformissing;scatter mpg weight;colorvar(price) colorformissing(red)""'
local probes `"`probes' "colorotherlabel;scatter mpg weight;colorvar(price) colorotherlabel(other)""'
local probes `"`probes' "gap;histogram mpg;gap(10)""'
local probes `"`probes' "droplines;function y = x, range(0 1);droplines(0.5)""'
local probes `"`probes' "mangle;pcarrow mpg weight trunk turn;mangle(30)""'
local probes `"`probes' "barbsize;pcarrow mpg weight trunk turn;barbsize(2)""'
local probes `"`probes' "ndots;dot mpg weight;ndots(10)""'
local probes `"`probes' "dotextend;dot mpg weight;dotextend(no)""'
local probes `"`probes' "dcolor;dot mpg weight;dcolor(red)""'
local probes `"`probes' "dsymbol;dot mpg weight;dsymbol(O)""'
local probes `"`probes' "dsize;dot mpg weight;dsize(small)""'
local probes `"`probes' "dfcolor;dot mpg weight;dfcolor(red)""'
local probes `"`probes' "dlcolor;dot mpg weight;dlcolor(red)""'
local probes `"`probes' "dlwidth;dot mpg weight;dlwidth(thin)""'
local probes `"`probes' "dstyle;dot mpg weight;dstyle(p1)""'
local probes `"`probes' "dlstyle;dot mpg weight;dlstyle(p1)""'
local probes `"`probes' "estcmd;fpfit mpg weight;estcmd(fp)""'
local probes `"`probes' "estopts;lfit mpg weight;estopts(noconstant)""'
local probes `"`probes' "predopts;lfit mpg weight;predopts(xb)""'
local probes `"`probes' "mlabprefix;scatter mpg weight;mlabel(make) mlabprefix(a)""'
local probes `"`probes' "mlabsuffix;scatter mpg weight;mlabel(make) mlabsuffix(a)""'
local probes `"`probes' "mlalign;scatter mpg weight;mlalign(inside)""'
local probes `"`probes' "mlabstyle;scatter mpg weight;mlabel(make) mlabstyle(p1)""'
local probes `"`probes' "lalign;line mpg weight;lalign(inside)""'
local probes `"`probes' "yvarlabel;scatter mpg weight;yvarlabel(a)""'
local probes `"`probes' "xvarlabel;scatter mpg weight;xvarlabel(a)""'

* The graph options twoway's own parsers declare (twowaygraph_g.class
* parse's graph_g_opts and graph_opts, graph_g.class, graph.ado), asked
* on scatter: those dash leaves to the catch-all are taken here as twoway
* takes them.
foreach o in "tlabel(1)" "ttick(1)" "tmlabel(1)" "tmtick(1)" "tscale(off)" "ttitle(a)" "tline(1)" ///
    "zlabel(1)" "ztick(1)" "zmlabel(1)" "zmtick(1)" "zscale(off)" "ztitle(a)" ///
    "plotregion(margin(zero))" "graphregion(color(white))" "spacers(x)" "bgcolor(white)" ///
    "legloc(x)" "useplotregion(x)" "add" "aspectratio(1)" "xoverhangs" "yoverhangs" ///
    "scale(1)" "p1(mcolor(red))" "p20(mcolor(red))" "nodraw" "draw" "iscale(1)" "play(x)" ///
    "fxsize(50)" "fysize(50)" "commonscheme" "usescheme(s2color)" "labels" "readlog(x)" ///
    "xsize(3)" "ysize(3)" "scheme(s2color)" "xaxis(1)" "yaxis(1)" "nomaybedraw" "xcommon" ///
    "serset(x)" "ttext(20 3000 a)" "text(20 3000 a)" "aspect(1)" {
    local nm = "`o'"
    local pp = strpos("`o'", "(")
    if `pp' local nm = substr("`o'", 1, `pp' - 1)
    local probes `"`probes' "`nm';scatter mpg weight;`o'""'
}

* The mixed lists: twoway names the first word of a list it refuses.
local orders ""
foreach c in "kdensity mpg, gaussian epan2 bogus" "kdensity mpg, bogus gaussian epan2" ///
    "kdensity mpg, gaussian epan2 xsize(3) xsize(4)" "kdensity mpg, xsize(3) xsize(4) gaussian epan2" ///
    "kdensity mpg, bwidth(1) bwidth(2) bogus" "kdensity mpg, bogus bwidth(1) bwidth(2)" ///
    "kdensity mpg, gaussian kernel(epan2) bogus" "kdensity mpg, bogus gaussian kernel(epan2)" ///
    "kdensity mpg, gaussian gaussian bogus" "kdensity mpg, xsize(3) xsize(4) bogus" ///
    "kdensity mpg, gaussian epan2 mlabfontface(x)" "kdensity mpg, mlabfontface(x) gaussian epan2" ///
    "scatter mpg weight, bogus" "scatter mpg weight, bogus(1)" "scatter mpg weight, bogus zork" ///
    "scatter mpg weight, xsize(3) xsize(4) bogus" "scatter mpg weight, bogus xsize(3) xsize(4)" ///
    "scatter mpg weight, bogus ATOBS" "scatter mpg weight, ATOBS bogus" ///
    "scatter mpg weight, ATOBS jit(5)" "scatter mpg weight, jit(5) ATOBS" ///
    "scatter mpg weight, title2(a) jit(5)" "scatter mpg weight, jit(5) title2(a)" ///
    "scatter mpg weight, xsize(3) xsize(4) mlabfontface(x)" "scatter mpg weight, mlabfontface(x) xsize(3) xsize(4)" ///
    "scatter mpg weight, mlabfontface(x) bogus" "scatter mpg weight, bogus mlabfontface(x)" ///
    "scatter mpg weight, bogus jit(5)" "scatter mpg weight, bogus title2(a)" "scatter mpg weight, bogus nam(zz)" ///
    "scatter mpg weight, bogus asp(1)" "scatter mpg weight, bogus below below" ///
    "scatter mpg weight, bogus scheme(s1color) scheme(s2color)" "scatter mpg weight, bogus hover(make)" ///
    "scatter mpg weight, xreverse" "scatter mpg weight, bargap(10)" "scatter mpg weight, cl(red)" ///
    "lfit mpg weight, atobs atobs bogus" "lfit mpg weight, bogus atobs atobs" ///
    "lowess mpg weight, bogus lo nolo" "lowess mpg weight, lo nolo bogus" ///
    "kdensity mpg, epan2 bogus" "kdensity mpg, ep bogus" ///
    "(scatter mpg weight), bogus" "(scatter mpg weight), bogus xsize(3) xsize(4)" ///
    "(scatter mpg weight), xsize(3) xsize(4) bogus" "(scatter mpg weight), bogus atobs" ///
    "(scatter mpg weight), atobs bogus" "(scatter mpg weight), ATOBS bogus" "(scatter mpg weight, bogus)" ///
    "scatter mpg weight || line mpg weight, bogus" "scatter mpg weight, bogus || line mpg weight, zork" ///
    "scatter mpg weight, xsize(3) xsize(4) || line mpg weight, bogus" ///
    "scatter mpg weight, below || line mpg weight, below bogus" ///
    "kdensity mpg, gaussian epan2 || scatter mpg weight, bogus" ///
    "(scatter mpg weight, bogus), xsize(3) xsize(4)" "(scatter mpg weight, xsize(3) xsize(4)), bogus" ///
    "(kdensity mpg, gaussian epan2), bogus" "(scatter mpg weight, mlabfontface(x)), bogus" ///
    "(scatter mpg weight), bogus below below" "(scatter mpg weight), below below bogus" {
    local orders `"`orders' "`c'""'
}

local k 0
foreach p of local probes {
    local ++k
    gettoken nm rest : p, parse(";")
    gettoken semi rest : rest, parse(";")
    gettoken plot rest : rest, parse(";")
    gettoken semi opt : rest, parse(";")
    * The option itself is the last word of opt; mlabel(make) and
    * colorvar(price) before it are what it styles.
    local pre ""
    local one : copy local opt
    if strpos(`"`opt'"', " ") & !strpos(`"`opt'"', `"""') {
        local nw : word count `opt'
        local one : word `nw' of `opt'
        forvalues j = 1/`=`nw'-1' {
            local pre `"`pre' `: word `j' of `opt''"'
        }
    }
    if strpos(`"`plot'"', ",") local cmd `"`plot' `opt'"'
    else local cmd `"`plot', `opt'"'
    global ZU_N_`k' "`nm'"
    global ZU_C_`k' `"`cmd'"'
    global ZU_O_`k' `"`one'"'
    quietly log using "${ZU_WORK}/t`k'.log", replace text name(zu)
    capture noisily twoway `cmd' nodraw
    global ZU_T_`k' = _rc
    quietly log close zu
    capture graph drop _all
    quietly log using "${ZU_WORK}/d`k'.log", replace text name(zu)
    capture noisily dash `cmd' name(zuq)
    global ZU_D_`k' = _rc
    quietly log close zu
    capture dash clear
    * Each type, the option alone.
    local tr ""
    foreach t of local types {
        capture twoway `base_`t'' `one' nodraw
        local tr "`tr' `=_rc'"
        capture graph drop _all
    }
    global ZU_TY_`k' "`tr'"
    * Each shorter spelling, and the other form, on the probe's plot.
    local pp = strpos(`"`one'"', "(")
    local val ""
    local name : copy local one
    if `pp' {
        local name = substr(`"`one'"', 1, `pp' - 1)
        local val = substr(`"`one'"', `pp', .)
    }
    local ab ""
    forvalues L = 1/`=strlen("`name'") - 1' {
        local sp = substr("`name'", 1, `L')
        if strpos(`"`plot'"', ",") capture twoway `plot' `pre' `sp'`val' nodraw
        else capture twoway `plot', `pre' `sp'`val' nodraw
        local ab "`ab' `=_rc'"
        capture graph drop _all
    }
    global ZU_AB_`k' "`ab'"
    local other "`name'(1)"
    if `pp' local other "`name'"
    if strpos(`"`plot'"', ",") capture twoway `plot' `pre' `other' nodraw
    else capture twoway `plot', `pre' `other' nodraw
    global ZU_OF_`k' = _rc
    capture graph drop _all
    * After the plot groups' comma.
    capture twoway (scatter mpg weight), `one' nodraw
    global ZU_AC_`k' = _rc
    capture graph drop _all
}
global ZU_K "`k'"

local j 0
foreach c of local orders {
    local ++j
    local sep ","
    if strpos(`"`c'"', ",") local sep ""
    if substr(`"`c'"', 1, 1) == "(" & !strpos(`"`c'"', "),") local sep ","
    global ZU_OC_`j' `"`c'"'
    quietly log using "${ZU_WORK}/o`j'.log", replace text name(zu)
    capture noisily twoway `c'`sep' nodraw
    global ZU_OR_`j' = _rc
    quietly log close zu
    capture graph drop _all
}
global ZU_J "`j'"

python:
import json, os, re
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


NOTE = "ignoring unsupported option(s):"


def noted(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return []
    out = []
    for ln in text.splitlines():
        i = ln.find(NOTE)
        if i < 0:
            continue
        for w in ln[i + len(NOTE):].split():
            w = re.sub(r"\(\)?$", "", w.strip(")").rstrip("("))
            if w:
                out.append(w)
    return out


def first_error(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = [ln.strip() for ln in fh]
    except OSError:
        return ""
    for s in lines:
        if s.startswith(". ") or s.startswith("> "):
            continue
        if (s.startswith("option") or s.endswith("not allowed") or
                "kernel" in s or "invalid" in s or "not found" in s):
            return s
    return ""


work = G("ZU_WORK")
types = G("ZU_TYPES").split()
probes = {}
for k in range(1, int(G("ZU_K")) + 1):
    nm = G("ZU_N_%d" % k)
    dlog = os.path.join(work, "d%d.log" % k)
    tlog = os.path.join(work, "t%d.log" % k)
    trc, drc = int(G("ZU_T_%d" % k)), int(G("ZU_D_%d" % k))
    ty = [int(v) for v in G("ZU_TY_%d" % k).split()]
    probes[nm] = {
        "cmd": G("ZU_C_%d" % k), "option": G("ZU_O_%d" % k),
        "twoway_rc": trc, "twoway_message": first_error(tlog) if trc else "",
        "dash_rc": drc, "dash_message": first_error(dlog) if drc else "",
        "noted": noted(dlog),
        "types_taking": [t for t, rc in zip(types, ty) if rc == 0],
        "spellings_rc": [int(v) for v in G("ZU_AB_%d" % k).split()],
        "other_form_rc": int(G("ZU_OF_%d" % k)),
        "after_comma_rc": int(G("ZU_AC_%d" % k)),
    }
    for f in (dlog, tlog):
        try:
            os.remove(f)
        except OSError:
            pass
orders = []
for j in range(1, int(G("ZU_J")) + 1):
    olog = os.path.join(work, "o%d.log" % j)
    rc = int(G("ZU_OR_%d" % j))
    orders.append({"cmd": G("ZU_OC_%d" % j), "twoway_rc": rc,
                   "twoway_message": first_error(olog) if rc else ""})
    try:
        os.remove(olog)
    except OSError:
        pass
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out = {"_meta": {"stata_version": G("ZU_VERSION"), "born_date": G("ZU_BORN"),
                 "dash_commit": commit, "extracted": G("ZU_WHEN"),
                 "source": "scripts/extract_unknown_option_truth.do"},
       "types": types, "probes": probes, "orders": orders}
with open(G("ZU_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZU_OUT"), len(probes), "probes,", len(orders), "orders")
end
