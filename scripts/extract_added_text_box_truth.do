* extract_added_text_box_truth.do -- twoway's own text() alignment(), box
* and line options, and the =exp of a global in a text() line (WP-43
* section 43-06, LT-11 and LT-20), written to
* test/fixtures/added_text_box_truth.json for test/test_added_text_box.py
* and block S06 of test/test_wp43_truth.cscript.
*
* Records, per probe id (probes[<id>]):
*   cmd, rc, notes (every "(note: ...)" line of the probes run through
*   _bx_probe), control (the probe whose texts and boxes are the
*   baseline), texts (every <text> the probe adds over its control: text,
*   x_px, y_px, size, fill, anchor, rotate) and boxes (every filled or
*   outlined <path> drawn through <use> that the control does not draw:
*   left, right, top, bottom, fill, stroke, stroke_width, dasharray).
*   Eval probes (x_eval_<k>, x_eval_out_<k>) record expr (the global's
*   value without its backtick and quote) and drawn (the text twoway drew).
* _meta.viewbox: the SVG's viewBox width and height; _meta.same_as_box:
*   x_bexpand and x_bmargin drew exactly x_box's texts and boxes;
*   _meta.al_equal: each alignment() spelling -> the full word whose
*   drawing it equals, or null.
*
* Every global probe is two straight lines (section 43-06 D-43-06.f): the
* global set by a string expression nothing expands, then twoway naming
* it as \$G, so twoway reads the global itself and evaluates its =exp.
* No probe runs a file function.
*
* Run (never the GUI; the slot wrapper of scripts/stata_slot.sh):
*   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_added_text_box_truth.do
* SVGs and logs go to c(tmpdir).  The trailing python: block never calls
* back into Stata and holds no backtick.

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zb_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zb_bad' {
    display as error "extract_added_text_box_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zb_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zb_rc' | _rc {
    local _zb_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_added_text_box_truth.do: `_zb_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}

clear all
set more off
set linesize 255
version 19
set scheme stcolor

local stata_version = c(stata_version)
local born_date "`c(born_date)'"
tempfile gh
shell git -C "`repo'" rev-parse HEAD > "`gh'"
tempname fh
file open `fh' using "`gh'", read text
file read `fh' dash_commit
file close `fh'
local extracted "`c(current_date)'"
local tmp "`c(tmpdir)'"

capture program drop _bx_probe
program _bx_probe
    version 19
    args id ctl cmd
    local tmp "`c(tmpdir)'"
    capture log close bxp
    capture graph drop _all
    log using "`tmp'/bx_`id'.log", text replace name(bxp)
    capture noisily `cmd' name(zqb, replace)
    local rc = _rc
    log close bxp
    capture erase "`tmp'/bx_`id'.svg"
    if `rc' == 0 {
        quietly graph export "`tmp'/bx_`id'.svg", name(zqb) replace
    }
    file write $BX_RH `"`id'|`ctl'|`rc'|`cmd'"' _n
end

* _bx_after <id> <rc>: export the eval probe just drawn as zqe and record it.
capture program drop _bx_after
program _bx_after
    version 19
    args id rc
    local tmp "`c(tmpdir)'"
    capture erase "`tmp'/bx_`id'.svg"
    if `rc' == 0 {
        quietly graph export "`tmp'/bx_`id'.svg", name(zqe) replace
    }
    capture graph drop zqe
    file write $BX_RH `"`id'|ctl0|`rc'|eval"' _n
end

tempfile recs
tempname rh
file open `rh' using "`recs'", write text replace
global BX_RH `rh'

sysuse auto, clear
local sc "twoway scatter mpg weight,"
local tx `"text(30 3000 "Peak" "two""'
_bx_probe ctl0 "" `"`sc'"'
_bx_probe x_ctl ctl0 `"`sc' `tx')"'
_bx_probe x_box ctl0 `"`sc' `tx', box)"'
foreach a in top middle bottom baseline t to mid bot base {
    _bx_probe al_`a' ctl0 `"`sc' `tx', alignment(`a'))"'
}
_bx_probe x_w ctl0 `"`sc' `tx', box width(20))"'
_bx_probe x_h ctl0 `"`sc' `tx', box height(20))"'
_bx_probe x_wh ctl0 `"`sc' `tx', box width(20) height(20))"'
_bx_probe x_w_small ctl0 `"`sc' `tx', box width(2))"'
_bx_probe x_h_small ctl0 `"`sc' `tx', box height(2))"'
_bx_probe ctl0_scale "" `"`sc' scale(1.5)"'
_bx_probe x_box_scale ctl0_scale `"`sc' `tx', box) scale(1.5)"'
_bx_probe x_w_scale ctl0_scale `"`sc' `tx', box width(20)) scale(1.5)"'
_bx_probe x_wj_l ctl0 `"`sc' `tx', box width(40) justification(left))"'
_bx_probe x_wj_r ctl0 `"`sc' `tx', box width(40) justification(right))"'
_bx_probe x_wj_c ctl0 `"`sc' `tx', box width(40))"'
_bx_probe x_h_top ctl0 `"`sc' `tx', box height(40) alignment(top))"'
_bx_probe x_h_mid ctl0 `"`sc' `tx', box height(40))"'
_bx_probe x_h_bot ctl0 `"`sc' `tx', box height(40) alignment(bottom))"'
_bx_probe x_h_base ctl0 `"`sc' `tx', box height(40) alignment(baseline))"'
_bx_probe x_lg ctl0 `"`sc' `tx', linegap(3))"'
_bx_probe x_lg_box ctl0 `"`sc' `tx', box linegap(3))"'
_bx_probe x_lst ctl0 `"`sc' `tx', box lstyle(p1))"'
_bx_probe x_blst ctl0 `"`sc' `tx', box blstyle(p1))"'
_bx_probe x_lst_bad ctl0 `"`sc' `tx', box lstyle(bogus))"'
_bx_probe x_lst_lc ctl0 `"`sc' `tx', box lstyle(p1) lcolor(red))"'
_bx_probe x_lc_lst ctl0 `"`sc' `tx', box lcolor(red) lstyle(p1))"'
_bx_probe x_lst_nobox ctl0 `"`sc' `tx', lstyle(p1))"'
_bx_probe x_lp ctl0 `"`sc' `tx', box lpattern(dash))"'
_bx_probe x_blp ctl0 `"`sc' `tx', box blpattern(dash))"'
_bx_probe x_lw ctl0 `"`sc' `tx', box lwidth(thick))"'
_bx_probe x_la_o ctl0 `"`sc' `tx', box lwidth(thick) lalign(outside))"'
_bx_probe x_la_i ctl0 `"`sc' `tx', box lwidth(thick) lalign(inside))"'
_bx_probe x_la_c ctl0 `"`sc' `tx', box lwidth(thick) lalign(center))"'
_bx_probe x_bla_o ctl0 `"`sc' `tx', box lwidth(thick) blalign(outside))"'
_bx_probe x_bexpand ctl0 `"`sc' `tx', box bexpand)"'
_bx_probe x_bmargin ctl0 `"`sc' `tx', box bmargin(large))"'

* The eval probes: two straight lines each, never in a loop (D-43-06.f).
global G = char(96) + "=1+1" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_1 `=_rc'
global G = char(96) + "=1/3" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_2 `=_rc'
global G = char(96) + "=2/3*3" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_3 `=_rc'
global G = char(96) + "=10^20" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_4 `=_rc'
global G = char(96) + "=-1.5" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_5 `=_rc'
global G = char(96) + "=1/0" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_6 `=_rc'
global G = char(96) + "=1e-7" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_7 `=_rc'
global G = char(96) + "=123456789" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_8 `=_rc'
global G = char(96) + "=.1+.2" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_9 `=_rc'
global G = char(96) + "=-2^2" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_10 `=_rc'
global G = char(96) + "=2^3^2" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_11 `=_rc'
global G = char(96) + "=2*3+4" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_12 `=_rc'
global G = char(96) + "=2+3*4" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_13 `=_rc'
global G = char(96) + "=(2+3)*4" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_14 `=_rc'
global G = char(96) + "=!0" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_15 `=_rc'
global G = char(96) + "=!1+1" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_16 `=_rc'
global G = char(96) + "=1<2&2<1|1" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_17 `=_rc'
global G = char(96) + "=.>5" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_18 `=_rc'
global G = char(96) + "=1==1" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_19 `=_rc'
global G = char(96) + "=abs(-3)" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_20 `=_rc'
global G = char(96) + "=round(2.567,.01)" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_21 `=_rc'
global G = char(96) + "=round(2.5)" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_22 `=_rc'
global G = char(96) + "=mod(7,3)" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_23 `=_rc'
global G = char(96) + "=min(3,.,1)" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_24 `=_rc'
global G = char(96) + "=max(1,2)" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_25 `=_rc'
global G = char(96) + "=sqrt(2)" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_26 `=_rc'
global G = char(96) + "=ln(1)" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_27 `=_rc'
global G = char(96) + "=log10(1000)" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_28 `=_rc'
global G = char(96) + "=int(-2.5)" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_29 `=_rc'
global G = char(96) + "=ceil(1.2)" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_30 `=_rc'
global G = char(96) + "=floor(-1.2)" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_31 `=_rc'
global G = char(96) + "=exp(1)" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_32 `=_rc'
global G = char(96) + "=sign(-4)" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_33 `=_rc'
global G = char(96) + "=string(1/3)" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_34 `=_rc'
global G = char(96) + `"=string(1/3,"%5.2f")"' + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_35 `=_rc'
global G = char(96) + "=strofreal(2)" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_36 `=_rc'
global G = char(96) + `"=real("3")+1"' + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_37 `=_rc'
global G = char(96) + `"=strlen("abc")"' + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_38 `=_rc'
global G = char(96) + `"=ustrlen("ab")"' + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_39 `=_rc'
global G = char(96) + `"=substr("abcdef",2,3)"' + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_40 `=_rc'
global G = char(96) + `"=usubstr("abc",1,1)"' + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_41 `=_rc'
global G = char(96) + `"=upper("ab")"' + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_42 `=_rc'
global G = char(96) + `"=strupper("ab")"' + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_43 `=_rc'
global G = char(96) + `"=lower("AB")"' + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_44 `=_rc'
global G = char(96) + `"=strlower("AB")"' + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_45 `=_rc'
global G = char(96) + `"=trim("  a ")"' + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_46 `=_rc'
global G = char(96) + `"=strtrim(" a ")"' + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_47 `=_rc'
global G = char(96) + `"="a"+"b""' + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_48 `=_rc'
global G = char(96) + "=_N" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_out_1 `=_rc'
global G = char(96) + "=mpg[1]" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_out_2 `=_rc'
global G = char(96) + "=c(N)" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_out_3 `=_rc'
global G = char(96) + "c(N)" + char(39)
capture noisily twoway scatter mpg weight, text(30 3000 "\$G") name(zqe, replace)
_bx_after x_eval_out_4 `=_rc'
macro drop G
file close `rh'

python:
import collections, json, os, re, sys
from sfi import Macro
repo = Macro.getLocal("repo")
tmp = Macro.getLocal("tmp")
sys.path.insert(0, os.path.join(repo, "scripts"))
import svg_truth

_HDR = re.compile(r"^\s*(name|log|log type|opened on|closed on):")
EVAL = {
 "x_eval_1": "1+1",
 "x_eval_2": "1/3",
 "x_eval_3": "2/3*3",
 "x_eval_4": "10^20",
 "x_eval_5": "-1.5",
 "x_eval_6": "1/0",
 "x_eval_7": "1e-7",
 "x_eval_8": "123456789",
 "x_eval_9": ".1+.2",
 "x_eval_10": "-2^2",
 "x_eval_11": "2^3^2",
 "x_eval_12": "2*3+4",
 "x_eval_13": "2+3*4",
 "x_eval_14": "(2+3)*4",
 "x_eval_15": "!0",
 "x_eval_16": "!1+1",
 "x_eval_17": "1<2&2<1|1",
 "x_eval_18": ".>5",
 "x_eval_19": "1==1",
 "x_eval_20": "abs(-3)",
 "x_eval_21": "round(2.567,.01)",
 "x_eval_22": "round(2.5)",
 "x_eval_23": "mod(7,3)",
 "x_eval_24": "min(3,.,1)",
 "x_eval_25": "max(1,2)",
 "x_eval_26": "sqrt(2)",
 "x_eval_27": "ln(1)",
 "x_eval_28": "log10(1000)",
 "x_eval_29": "int(-2.5)",
 "x_eval_30": "ceil(1.2)",
 "x_eval_31": "floor(-1.2)",
 "x_eval_32": "exp(1)",
 "x_eval_33": "sign(-4)",
 "x_eval_34": "string(1/3)",
 "x_eval_35": "string(1/3,\"%5.2f\")",
 "x_eval_36": "strofreal(2)",
 "x_eval_37": "real(\"3\")+1",
 "x_eval_38": "strlen(\"abc\")",
 "x_eval_39": "ustrlen(\"ab\")",
 "x_eval_40": "substr(\"abcdef\",2,3)",
 "x_eval_41": "usubstr(\"abc\",1,1)",
 "x_eval_42": "upper(\"ab\")",
 "x_eval_43": "strupper(\"ab\")",
 "x_eval_44": "lower(\"AB\")",
 "x_eval_45": "strlower(\"AB\")",
 "x_eval_46": "trim(\"  a \")",
 "x_eval_47": "strtrim(\" a \")",
 "x_eval_48": "\"a\"+\"b\"",
 "x_eval_out_1": "=_N",
 "x_eval_out_2": "=mpg[1]",
 "x_eval_out_3": "=c(N)",
 "x_eval_out_4": "c(N)"
}


def _notes(pid):
    try:
        with open(os.path.join(tmp, "bx_" + pid + ".log"),
                  encoding="utf-8", errors="replace") as fh:
            rows = fh.read().splitlines()
    except OSError:
        return []
    return [r.strip() for r in rows
            if not _HDR.match(r) and r.strip().startswith("(note:")]


_USE = re.compile(r"<use ([^>]*?)/>")
_PATHD = re.compile(r'<path id="([^"]+)" d="([^"]+)"')
_VB = re.compile(r'viewBox="([0-9.\- ]+)"')


def _read(p):
    with open(p, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _boxes(svg):
    txt = _read(svg)
    paths = {}
    for pid, d in _PATHD.findall(txt):
        nums = [float(v) for v in re.findall(r"-?[0-9.]+", d)]
        xs, ys = nums[0::2], nums[1::2]
        if xs and ys:
            paths[pid] = (min(xs), max(xs), min(ys), max(ys))
    out = collections.OrderedDict()
    for m in _USE.finditer(txt):
        a = dict(re.findall(r'([\w:-]+)="([^"]*)"', m.group(1)))
        ref = a.get("xlink:href", "").lstrip("#")
        if ref not in paths:
            continue
        st = {}
        for part in a.get("style", "").split(";"):
            if ":" in part:
                k, v = part.split(":", 1)
                st[k.strip()] = v.strip()
        l, r, t, b = paths[ref]
        rec = out.setdefault(ref, {"left": l, "right": r, "top": t,
                                   "bottom": b, "fill": None, "stroke": None,
                                   "stroke_width": None, "dasharray": None})
        if st.get("fill", "none") != "none":
            rec["fill"] = st["fill"].lower()
        if st.get("stroke", "none") != "none":
            rec["stroke"] = st["stroke"].lower()
            try:
                rec["stroke_width"] = float(st.get("stroke-width"))
            except (TypeError, ValueError):
                pass
            if st.get("stroke-dasharray"):
                rec["dasharray"] = st["stroke-dasharray"]
    return [v for v in out.values() if v["fill"] or v["stroke"]]


recs = []
with open(Macro.getLocal("recs"), encoding="utf-8") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if line:
            pid, ctl, rc, cmd = line.split("|", 3)
            recs.append((pid, ctl, int(rc), cmd.rstrip(",").strip()))

texts, boxes = {}, {}
viewbox = None
for pid, ctl, rc, cmd in recs:
    p = os.path.join(tmp, "bx_" + pid + ".svg")
    if rc == 0 and os.path.exists(p):
        texts[pid] = svg_truth.svg_document(p)["texts"]
        boxes[pid] = _boxes(p)
        if viewbox is None:
            m = _VB.search(_read(p))
            if m:
                viewbox = [float(v) for v in m.group(1).split()][2:]

probes = {}
for pid, ctl, rc, cmd in recs:
    rec = {"cmd": cmd, "rc": rc, "control": ctl, "notes": _notes(pid)}
    if pid in texts:
        base = collections.Counter(t["text"] for t in texts.get(ctl, []))
        added = []
        for t in texts[pid]:
            if base[t["text"]] > 0:
                base[t["text"]] -= 1
                continue
            added.append({"text": t["text"], "x_px": t["x"], "y_px": t["y"],
                          "size": t["size"], "fill": t["fill"],
                          "anchor": t["anchor"], "rotate": t["rotate"]})
        rec["texts"] = added if ctl else []
        cb = [(b["left"], b["top"], b["right"], b["bottom"])
              for b in boxes.get(ctl, [])]
        rec["boxes"] = [b for b in boxes[pid]
                        if (b["left"], b["top"], b["right"], b["bottom"])
                        not in cb] if ctl else []
    if pid in EVAL:
        rec["cmd"] = ("global G = \x60" + EVAL[pid] + "'; twoway scatter "
                      "mpg weight, text(30 3000 \"" + chr(36) + "G\")")
        rec["expr"] = EVAL[pid]
        rec["drawn"] = " ".join(t["text"] for t in rec.get("texts", []))
    probes[pid] = rec


def _same(a, b):
    pa, pb = probes.get(a, {}), probes.get(b, {})
    return (pa.get("texts") == pb.get("texts")
            and pa.get("boxes") == pb.get("boxes")
            and not pa.get("notes"))


al_equal = {}
for spell in ("top", "middle", "bottom", "baseline", "t", "to", "mid",
              "bot", "base"):
    hit = None
    for full in ("top", "middle", "bottom", "baseline"):
        if _same("al_" + spell, "al_" + full):
            hit = full
            break
    al_equal[spell] = hit

out = {"probes": probes,
       "_meta": {"stata_version": Macro.getLocal("stata_version"),
                 "born_date": Macro.getLocal("born_date"),
                 "source": "scripts/extract_added_text_box_truth.do",
                 "dash_commit": Macro.getLocal("dash_commit").strip(),
                 "extracted": Macro.getLocal("extracted"),
                 "scheme": "stcolor", "data": "auto",
                 "viewbox": viewbox,
                 "al_equal": al_equal,
                 "same_as_box": {"x_bexpand": _same("x_bexpand", "x_box"),
                                 "x_bmargin": _same("x_bmargin", "x_box")}}}
path = os.path.join(repo, "test", "fixtures", "added_text_box_truth.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote " + path)
end
