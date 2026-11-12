*! extract_catchall_options_truth.do -- WP-31 section 56 (J1): measure which
*! twoway option names dash accepts once and names in its "ignoring
*! unsupported option(s)" note without a pending declaration -- the names
*! that reach the catch-all.  WP-48 syn:SD-15: the candidates are read from
*! twoway's own tables in dash_parse.mata -- every row's full name of
*! _dash_tw_takes_tab() (the words twoway takes, measured in
*! unknown_option_truth.json) and every row's full spelling of
*! _dash_rep_und_tab() -- not typed by hand, so a word twoway takes cannot
*! reach dash's note unprobed.  The typed form of each candidate (the plot
*! and the option as typed) is the table below; a candidate with no typed
*! form, or one typed on a plot type its row does not name, stops the run.
*! Every probe runs the same command
*! under twoway (nodraw) and under dash, each under capture noisily with its
*! own log; the return codes and the names dash's note gives are recorded.
*! The output changes when dash starts drawing or refusing one of them.
*!
*! Output: test/fixtures/catchall_options_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_catchall_options_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 255

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zk_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zk_bad' {
    display as error "extract_catchall_options_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zk_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zk_rc' | _rc {
    local _zk_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_catchall_options_truth.do: `_zk_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZK_REPO "`repo'"
global ZK_OUT "${ZK_REPO}/test/fixtures/catchall_options_truth.json"

adopath ++ "${ZK_REPO}"
quietly do "${ZK_REPO}/dash_parse.mata"
quietly do "${ZK_REPO}/dash.ado"
global dash_nobrowser 1

local work "`c(tmpdir)'dash_catchall_probe"
capture mkdir "`work'"
global ZK_WORK "`work'"


quietly shell git -C "${ZK_REPO}" rev-parse HEAD > "${ZK_WORK}/git_head.txt"
global ZK_VERSION "`c(stata_version)'"
global ZK_BORN "`c(born_date)'"
global ZK_WHEN "`c(current_date)' `c(current_time)'"

sysuse auto, clear
gen yl = mpg - 1
gen yh = mpg + 1
gen t = _n
tsset t

* The typed form of each candidate: name ; plot ; option as typed
* (appended one at a time in compound quotes, so each keeps its own
* quotes).  The plot is one of the types the candidate's table row names
* (checked below): the type the option is drawn on where twoway draws it
* on some types only (the bar-derived ones on bar or dot, the line
* alignments on line), else scatter.  WP-48 syn:SD-15 keeps the plots the
* hand list chose, so the 110 earlier measurements do not move, and puts
* each new row on the first type it names ("*", every type, is scatter;
* play(), taken only after the comma, on scatter).
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
* WP-48 syn:SD-15: the rows of the two tables the hand list did not hold.
local probes `"`probes' "aspect;scatter mpg weight;aspect(1)""'
local probes `"`probes' "aspectratio;scatter mpg weight;aspectratio(1)""'
local probes `"`probes' "bgcolor;scatter mpg weight;bgcolor(white)""'
local probes `"`probes' "fxsize;scatter mpg weight;fxsize(50)""'
local probes `"`probes' "fysize;scatter mpg weight;fysize(50)""'
local probes `"`probes' "graphregion;scatter mpg weight;graphregion(color(white))""'
local probes `"`probes' "play;scatter mpg weight;play(dash_no_such_recording)""'
local probes `"`probes' "plotregion;scatter mpg weight;plotregion(color(white))""'
local probes `"`probes' "scale;scatter mpg weight;scale(1.2)""'
local probes `"`probes' "scheme;scatter mpg weight;scheme(s2color)""'
local probes `"`probes' "tlabel;scatter mpg weight;tlabel(#3)""'
local probes `"`probes' "tline;scatter mpg weight;tline(3000)""'
local probes `"`probes' "tmlabel;scatter mpg weight;tmlabel(#3)""'
local probes `"`probes' "tmtick;scatter mpg weight;tmtick(#3)""'
local probes `"`probes' "tscale;scatter mpg weight;tscale(range(1000 5000))""'
local probes `"`probes' "ttick;scatter mpg weight;ttick(#3)""'
local probes `"`probes' "ttitle;scatter mpg weight;ttitle(t)""'
local probes `"`probes' "xaxis;scatter mpg weight;xaxis(1)""'
local probes `"`probes' "xoverhangs;scatter mpg weight;xoverhangs""'
local probes `"`probes' "xsize;scatter mpg weight;xsize(5)""'
local probes `"`probes' "yaxis;scatter mpg weight;yaxis(1)""'
local probes `"`probes' "yoverhangs;scatter mpg weight;yoverhangs""'
local probes `"`probes' "ysize;scatter mpg weight;ysize(4)""'
local probes `"`probes' "zlabel;scatter mpg weight;zlabel(#3)""'
local probes `"`probes' "zmlabel;scatter mpg weight;zmlabel(#3)""'
local probes `"`probes' "zmtick;scatter mpg weight;zmtick(#3)""'
local probes `"`probes' "zscale;scatter mpg weight;zscale(range(0 10))""'
local probes `"`probes' "ztick;scatter mpg weight;ztick(#3)""'
local probes `"`probes' "ztitle;scatter mpg weight;ztitle(z)""'
local probes `"`probes' "smoothplot;lpolyci mpg weight;smoothplot(lcolor(red))""'
local probes `"`probes' "logit;lowess foreign weight;logit""'
local probes `"`probes' "nologit;lowess foreign weight;nologit""'

* The candidates (WP-48 syn:SD-15): every full name of _dash_tw_takes_tab()
* and every full spelling of _dash_rep_und_tab(), first appearance kept,
* each with the plot types its row names; then the names the hand list
* probed that neither table holds (mlabfontface, which twoway refuses;
* subchar and symbol, which dash declares), kept so their records stay.
mata:
void _zk_candidates()
{
    string matrix a, b
    string colvector nm, ty
    string scalar out
    real scalar i
    transmorphic scalar seen

    a = _dash_tw_takes_tab()
    b = _dash_rep_und_tab()
    nm = a[., 1] \ b[., 2]
    ty = a[., 4] \ b[., 5]
    seen = asarray_create()
    out = ""
    for (i = 1; i <= rows(nm); i++) {
        if (asarray_contains(seen, nm[i])) continue
        asarray(seen, nm[i], 1)
        out = out + " " + nm[i]
        st_global("ZK_TY_" + nm[i], ty[i] == "" ? "after-comma" : ty[i])
    }
    st_local("cands", strtrim(out))
}
_zk_candidates()
end
local extra "mlabfontface subchar symbol"
foreach nm of local extra {
    global ZK_TY_`nm' "*"
}
local cands "`cands' `extra'"

* Each candidate's typed form, in candidate order; a missing form or a plot
* its row does not name stops the run.
local forms `"`probes'"'
local probes ""
foreach nm of local cands {
    local hit ""
    foreach p of local forms {
        gettoken pn : p, parse(";")
        if "`pn'" == "`nm'" local hit `"`p'"'
    }
    if `"`hit'"' == "" {
        display as error "extract_catchall_options_truth.do: no typed form for `nm'; add one to the table"
        exit 198
    }
    gettoken pn rest : hit, parse(";")
    gettoken semi rest : rest, parse(";")
    gettoken pt : rest, parse(" ;,")
    local types "${ZK_TY_`nm'}"
    if !inlist("`types'", "*", "after-comma") & !`: list pt in types' {
        display as error "extract_catchall_options_truth.do: `nm' is typed on `pt', not one of its row's types (`types')"
        exit 198
    }
    local probes `"`probes' `"`hit'"'"'
}

local k 0
foreach p of local probes {
    local ++k
    gettoken nm rest : p, parse(";")
    gettoken semi rest : rest, parse(";")
    gettoken plot rest : rest, parse(";")
    gettoken semi opt : rest, parse(";")
    * A plot that carries its own comma (function's range()) takes the
    * option after a space; every other plot after a comma.
    if strpos(`"`plot'"', ",") local cmd `"`plot' `opt'"'
    else local cmd `"`plot', `opt'"'
    quietly log using "${ZK_WORK}/t`k'.log", replace text name(zk)
    capture noisily twoway `cmd' nodraw
    local trc = _rc
    quietly log close zk
    capture graph drop Graph
    quietly log using "${ZK_WORK}/d`k'.log", replace text name(zk)
    capture noisily dash `cmd'
    local drc = _rc
    quietly log close zk
    global ZK_N_`k' "`nm'"
    global ZK_C_`k' `"`cmd'"'
    global ZK_T_`k' "`trc'"
    global ZK_D_`k' "`drc'"
}
global ZK_K "`k'"
display as text "probes: `k'"

python:
import json, os, re
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


NOTE = "ignoring unsupported option(s):"


def noted(path):
    """The names dash's note gives, without their "()"."""
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
            w = w.strip(")").rstrip("(")
            w = re.sub(r"\(\)?$", "", w)
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
        if s.startswith("option ") or s.endswith("not allowed") or \
                "invalid" in s or "not found" in s:
            return s
    return ""


work = G("ZK_WORK")
probes = {}
options = []
refused = []
for k in range(1, int(G("ZK_K")) + 1):
    nm = G("ZK_N_%d" % k)
    trc, drc = int(G("ZK_T_%d" % k)), int(G("ZK_D_%d" % k))
    dlog = os.path.join(work, "d%d.log" % k)
    tlog = os.path.join(work, "t%d.log" % k)
    names = noted(dlog)
    probes[nm] = {"cmd": G("ZK_C_%d" % k), "twoway_rc": trc,
                  "twoway_message": first_error(tlog) if trc else "",
                  "dash_rc": drc,
                  "dash_message": first_error(dlog) if drc else "",
                  "noted": names}
    # A name twoway refuses on that plot is no twoway option there: it is
    # kept apart, as one dash names that twoway would refuse.
    if drc == 0 and nm in names:
        (options if trc == 0 else refused).append(nm)
    for f in (dlog, tlog):
        try:
            os.remove(f)
        except OSError:
            pass
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out = {"_meta": {"stata_version": G("ZK_VERSION"), "born_date": G("ZK_BORN"),
                 "dash_commit": commit, "extracted": G("ZK_WHEN"),
                 "source": "scripts/extract_catchall_options_truth.do"},
       "options": sorted(options), "twoway_refuses": sorted(refused),
       "source_tables": ["_dash_tw_takes_tab", "_dash_rep_und_tab"],
       "probes": probes}
with open(G("ZK_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZK_OUT"), len(probes), "probes,", len(options), "noted")
end
