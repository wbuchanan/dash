* extract_style_leaf_truth.do -- leaf, color and textbox style files, the
* shipped-name scheme order, five scheme directives and an unknown scheme()
* as twoway draws them (WP-45 section 45-03: ST-7, ST-15, ST-10, ST-17,
* ST-16), written to test/fixtures/style_leaf_truth.json for
* test/test_style_files_more.py.
*
* Records (each draw is exported as SVG and compared, whole, with its
* reference draw; the notes the call printed are kept):
*   L_<class>   a <class>-zq*.style file in a directory put on the ado-path
*               for this session (adopath ++), drawn at its option against
*               the same draw with the file's value typed;
*   S_order     scheme-economist.scheme (#include s2color, color p1 red) in
*               a directory before BASE (adopath ++) and after it (adopath +);
*   D_<name>    a user scheme w45<x>.scheme (#include s2color) with one
*               directive, against s2color with the option it stands for;
*   U_unknown   scheme(nosuchscheme): rc, notes, and whether it is s2color;
*   U_path      scheme(../nosuch): the same.
*
* No persistent preference is changed: no graph set, no set ..., permanently;
* the scheme is set for the session and restored, the directories leave the
* ado-path at the end.
*
* Run (never the GUI):
*   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_style_leaf_truth.do

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zl_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zl_bad' {
    display as error "extract_style_leaf_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
if _rc {
    display as error "extract_style_leaf_truth.do: set DASH_REPO to the dash repository"
    exit 601
}
global dash_nobrowser 1

clear all
set more off
set linesize 255
version 19
set graphics off
local entry_scheme "`c(scheme)'"
local stata_version = c(stata_version)
local born_date "`c(born_date)'"
tempfile gh
shell git -C "`repo'" rev-parse HEAD > "`gh'"
tempname fh
file open `fh' using "`gh'", read text
file read `fh' dash_commit
file close `fh'
local extracted "`c(current_date)'"

* ---- the probe directory and the user directories ----
local pdir "`c(pwd)'/leaf_probes"
capture mkdir "`pdir'"
local _old : dir "`pdir'" files "*"
foreach f of local _old {
    erase "`pdir'/`f'"
}
local ud "`c(pwd)'/leaf_user"
local od "`c(pwd)'/leaf_order"
capture mkdir "`ud'"
capture mkdir "`od'"
python:
import os
from sfi import Macro
_ud, _od = Macro.getLocal("ud"), Macro.getLocal("od")
_heading_rest = ("set horizontal scheme heading\nset vertical   scheme heading\n"
                 "set margin     scheme heading\nset drawbox    scheme textbox\n"
                 "set fillcolor  scheme textbox\nset linestyle  scheme textbox\n"
                 "set boxmargin  scheme textbox\n")
_files = {
    "linepattern-zqpat.style": 'set pattern "4 1 1 1"\n',
    "linepattern-zqpb.style": 'set pattern "4 1 .1 1"\n',
    "linewidth-zqw.style": "set val 2\n",
    "symbolsize-zqs.style": "set val     5\nset sztype  relative\n",
    "gsize-zqg.style": "set val     10\nset sztype  relative\n",
    "gsize-zqp.style": "set val     18\nset sztype  points\n",
    "intensity-zqi.style": "set val 30\n",
    "anglestyle-zqa.style": "set val 30\n",
    "margin-zqm.style": ("set gleft   5\nset gright  5\nset gtop    5\n"
                         "set gbottom 5\n"),
    "margin-zqn.style": ("set gleft   2\nset gright  4\nset gtop    6\n"
                         "set gbottom 8\n"),
    "color-zqc.style": 'set rgb "200 30 40"\n',
    "textboxstyle-zqt.style": ("set angle      default\nset size       huge\n"
                               "set color      red\n" + _heading_rest),
    "scheme-w45p.scheme": "#include s2color\nclockdir p 9\n",
    "scheme-w45q.scheme": "#include s2color\nclockdir p2 9\n",
    "scheme-w45t.scheme": "#include s2color\ntextboxstyle title subheading\n",
    "scheme-w45g.scheme": "#include s2color\ngsize legend_col_gap huge\n",
    "scheme-w45c.scheme": "#include s2color\nclockdir title_position 3\n",
    "scheme-w45b.scheme": "#include s2color\nyesno plabelboxed yes\n",
}
for _f, _t in _files.items():
    with open(os.path.join(_ud, _f), "w", encoding="utf-8") as _fh:
        _fh.write(_t)
with open(os.path.join(_od, "scheme-economist.scheme"), "w",
          encoding="utf-8") as _fh:
    _fh.write("#include s2color\ncolor p1 red\n")
end
adopath ++ "`ud'"

* ---- the registry ----
tempname reg
file open `reg' using "`pdir'/registry.txt", write text replace
global ZL_REG `reg'
global ZL_PDIR "`pdir'"
global ZL_SEQ 0

capture program drop _zl_probe
program define _zl_probe
    // _zl_probe id scheme : command -- run command under scheme, export SVG
    version 19
    gettoken id 0 : 0
    gettoken sch 0 : 0
    gettoken colon 0 : 0
    local cmd = strtrim(`"`macval(0)'"')
    quietly sysuse auto, clear
    // a stable order: line draws ties of weight in data order
    quietly sort weight mpg make
    graph drop _all
    if strpos(`"`macval(cmd)'"', ",") == 0 local cmd `"`macval(cmd)',"'
    global ZL_SEQ = ${ZL_SEQ} + 1
    local f "p${ZL_SEQ}"
    capture log close zl_probe
    quietly log using "${ZL_PDIR}/`f'.log", text replace name(zl_probe)
    capture noisily `macval(cmd)' scheme(`sch')
    local rc = _rc
    quietly log close zl_probe
    if `rc' == 0 {
        quietly graph export "${ZL_PDIR}/`f'.svg", as(svg) replace
    }
    file write ${ZL_REG} `"`f'"' _tab `"`id'"' _tab `"`sch'"' _tab `"`rc'"' _tab `"`macval(cmd)'"' _n
end

* ---- L: leaf, color and textbox files (ST-7, ST-15) ----
local LN "line mpg weight,"
local SC "scatter mpg weight"
_zl_probe L_linepattern.probe s2color : `LN' lpattern(zqpat)
_zl_probe L_linepattern.solid s2color : `LN' lpattern(solid)
_zl_probe L_linepattern_b.probe s2color : `LN' lpattern(zqpb)
_zl_probe L_linepattern_b.ref s2color : `LN' lpattern(longdash_dot)
_zl_probe L_linewidth.probe s2color : `LN' lwidth(zqw)
_zl_probe L_linewidth.ref s2color : `LN' lwidth(2)
_zl_probe L_symbolsize.probe s2color : `SC', msize(zqs)
_zl_probe L_symbolsize.ref s2color : `SC', msize(5)
_zl_probe L_gsize.probe s2color : `SC', title("T", size(zqg))
_zl_probe L_gsize.ref s2color : `SC', title("T", size(10))
_zl_probe L_gsize_pt.probe s2color : `SC', title("T", size(zqp))
_zl_probe L_gsize_pt.ref s2color : `SC', title("T", size(18pt))
_zl_probe L_mlabsize.probe s2color : `SC' in 1/5, mlabel(make) mlabsize(zqg)
_zl_probe L_mlabsize.ref s2color : `SC' in 1/5, mlabel(make) mlabsize(10)
_zl_probe L_intensity.probe s2color : twoway bar mpg rep78, fintensity(zqi)
_zl_probe L_intensity.ref s2color : twoway bar mpg rep78, fintensity(30)
_zl_probe L_anglestyle.probe s2color : `SC' in 1/5, mlabel(make) mlabangle(zqa)
_zl_probe L_anglestyle.ref s2color : `SC' in 1/5, mlabel(make) mlabangle(30)
_zl_probe L_msangle.probe s2color : `SC', msymbol(T) msangle(zqa)
_zl_probe L_msangle.ref s2color : `SC', msymbol(T) msangle(30)
_zl_probe L_margin.probe s2color : `SC', plotregion(margin(zqm))
_zl_probe L_margin.ref s2color : `SC', plotregion(margin(5 5 5 5))
_zl_probe L_margin_n.probe s2color : `SC', plotregion(margin(zqn))
_zl_probe L_margin_n.ref s2color : `SC', plotregion(margin(2 4 8 6))
_zl_probe L_color.probe s2color : `SC', mcolor(zqc)
_zl_probe L_color.ref s2color : `SC', mcolor("200 30 40")
_zl_probe L_lcolor.probe s2color : `LN' lcolor(zqc)
_zl_probe L_lcolor.ref s2color : `LN' lcolor("200 30 40")
_zl_probe L_textboxstyle.probe s2color : `SC', title("T", tstyle(zqt))
_zl_probe L_textboxstyle.ref s2color : `SC', title("T", size(huge) color(red))
_zl_probe L_mlabtextstyle.probe s2color : `SC' in 1/5, mlabel(make) mlabtextstyle(zqt)
_zl_probe L_mlabtextstyle.ref s2color : `SC' in 1/5, mlabel(make) mlabsize(huge) mlabcolor(red)
_zl_probe L_unknown.probe s2color : `SC', mcolor(zqnone)

* ---- S: the shipped-name order (ST-10) ----
adopath ++ "`od'"
capture findfile scheme-economist.scheme
local find_before ""
if !_rc local find_before "`r(fn)'"
_zl_probe S_order.before economist : `SC'
_zl_probe S_order.s2red s2color : `SC', mcolor(red)
adopath - "`od'"
adopath + "`od'"
capture findfile scheme-economist.scheme
local find_after ""
if !_rc local find_after "`r(fn)'"
_zl_probe S_order.after economist : `SC'
_zl_probe S_order.native economist : `SC'
adopath - "`od'"

* ---- D: scheme directives (ST-17) ----
_zl_probe D_clockdir_p.probe w45p : `SC' in 1/5, mlabel(make)
_zl_probe D_clockdir_p.ref s2color : `SC' in 1/5, mlabel(make) mlabposition(9)
_zl_probe D_clockdir_p2.probe w45q : twoway (scatter mpg weight in 1/5, mlabel(make)) (scatter price weight in 1/5, mlabel(make) yaxis(2)),
_zl_probe D_clockdir_p2.ref s2color : twoway (scatter mpg weight in 1/5, mlabel(make)) (scatter price weight in 1/5, mlabel(make) yaxis(2) mlabposition(9)),
_zl_probe D_textboxstyle.probe w45t : `SC', title("T")
_zl_probe D_textboxstyle.ref s2color : `SC', title("T", size(medium) color(black))
_zl_probe D_textboxstyle.base s2color : `SC', title("T")
_zl_probe D_legend_col_gap.probe w45g : twoway (scatter mpg weight) (scatter price weight), legend(cols(2))
_zl_probe D_legend_col_gap.base s2color : twoway (scatter mpg weight) (scatter price weight), legend(cols(2))
_zl_probe D_legend_col_gap.ref s2color : twoway (scatter mpg weight) (scatter price weight), legend(cols(2) colgap(huge))
_zl_probe D_title_position.probe w45c : `SC', title("T")
_zl_probe D_title_position.ref s2color : `SC', title("T", position(3))
_zl_probe D_plabelboxed.probe w45b : `SC' in 1/5, mlabel(make)
_zl_probe D_plabelboxed.base s2color : `SC' in 1/5, mlabel(make)

* ---- U: an unknown scheme() (ST-16) ----
_zl_probe U_unknown.probe nosuchscheme : `SC'
_zl_probe U_unknown.s2color s2color : `SC'
_zl_probe U_path.probe ../nosuch : `SC'
file close `reg'
global ZL_REG

python:
import hashlib, json, os, re
from sfi import Macro
repo = Macro.getLocal("repo")
pdir = Macro.getLocal("pdir")
recs = {}
with open(os.path.join(pdir, "registry.txt"), encoding="utf-8") as fh:
    for ln in fh:
        f, rid, sch, rc, cmd = ln.rstrip("\n").split("\t", 4)
        svg = os.path.join(pdir, f + ".svg")
        text = ""
        if os.path.exists(svg):
            with open(svg, encoding="utf-8", errors="replace") as s:
                text = s.read()
        with open(os.path.join(pdir, f + ".log"), encoding="utf-8",
                  errors="replace") as lg:
            lines = [" ".join(x.split()) for x in lg]
        notes = [x for x in lines if x.startswith("(note:")]
        out = [x for x in lines if x and not x.startswith(("(note:", ". "))
               and not x.startswith("> ")]
        recs[rid] = {"rc": int(rc), "scheme": sch, "cmd": cmd,
                     "notes": notes,
                     "sha": hashlib.sha256(text.encode()).hexdigest()
                     if text else None, "svg": text}
def _dash(text):
    return sorted(set(re.findall(r'stroke-dasharray="([^"]+)"', text)))
def _texts(text, word):
    # (x, y, font-size, fill) of every <text> drawing *word*
    got = []
    for m in re.finditer(r"<text ([^>]*)>([^<]*)</text>", text):
        if m.group(2).strip() != word:
            continue
        a = dict(re.findall(r'([a-z-]+)="([^"]*)"', m.group(1)))
        st = dict(kv.split(":", 1) for kv in a.get("style", "").split(";")
                  if ":" in kv)
        got.append({"x": a.get("x"), "y": a.get("y"),
                    "font_size": st.get("font-size"), "fill": st.get("fill"),
                    "transform": a.get("transform")})
    return got
def _count(text, s):
    return text.upper().count(s.upper())
res = {}
def _pair(key, probe, ref):
    p, r = recs[probe], recs[ref]
    res[key] = {"cmd": p["cmd"], "ref_cmd": r["cmd"], "rc": p["rc"],
                "notes": p["notes"],
                "same_as_reference": int(p["sha"] is not None
                                         and p["sha"] == r["sha"])}
for k in ("linepattern", "linepattern_b", "linewidth", "symbolsize", "gsize",
          "gsize_pt", "mlabsize", "intensity", "anglestyle", "msangle",
          "margin", "margin_n", "color", "lcolor", "textboxstyle",
          "mlabtextstyle"):
    ref = "L_%s.%s" % (k, "solid" if k == "linepattern" else "ref")
    _pair("L_" + k, "L_%s.probe" % k, ref)
res["L_linepattern"]["same_as_solid"] = res["L_linepattern"].pop(
    "same_as_reference")
res["L_linepattern"]["dasharray"] = _dash(recs["L_linepattern.probe"]["svg"])
res["L_linepattern"]["solid_dasharray"] = _dash(
    recs["L_linepattern.solid"]["svg"])
res["L_linepattern_b"]["dasharray"] = _dash(
    recs["L_linepattern_b.probe"]["svg"])
res["L_unknown"] = {"cmd": recs["L_unknown.probe"]["cmd"],
                    "rc": recs["L_unknown.probe"]["rc"],
                    "notes": recs["L_unknown.probe"]["notes"]}
res["L_textboxstyle"]["title"] = _texts(recs["L_textboxstyle.probe"]["svg"],
                                        "T")
ud = Macro.getLocal("ud")
od = Macro.getLocal("od")
def _rel(p):
    if not p:
        return None
    for root, tag in ((od, "ORDER"), (ud, "USER")):
        if p.startswith(root + "/"):
            return tag + "/" + p[len(root) + 1:]
    return "BASE/" + os.path.basename(p) if "/base/" in p else p
sb, sa = recs["S_order.before"], recs["S_order.after"]
res["S_order"] = {
    "find_before": _rel(Macro.getLocal("find_before")),
    "find_after": _rel(Macro.getLocal("find_after")),
    "before": {"rc": sb["rc"], "notes": sb["notes"],
               "red_fills": _count(sb["svg"], "#FF0000"),
               "same_as_s2color_mcolor_red": int(
                   sb["sha"] == recs["S_order.s2red"]["sha"])},
    "after": {"rc": sa["rc"], "notes": sa["notes"],
              "red_fills": _count(sa["svg"], "#FF0000"),
              "same_as_native": int(sa["sha"] == recs["S_order.native"]["sha"])},
}
for k in ("clockdir_p", "clockdir_p2", "textboxstyle", "legend_col_gap",
          "title_position"):
    _pair("D_" + k, "D_%s.probe" % k, "D_%s.ref" % k)
res["D_textboxstyle"]["same_as_base"] = int(
    recs["D_textboxstyle.probe"]["sha"] == recs["D_textboxstyle.base"]["sha"])
res["D_textboxstyle"]["title"] = _texts(recs["D_textboxstyle.probe"]["svg"],
                                        "T")
res["D_textboxstyle"]["base_title"] = _texts(
    recs["D_textboxstyle.base"]["svg"], "T")
res["D_title_position"]["title"] = _texts(
    recs["D_title_position.probe"]["svg"], "T")
res["D_title_position"]["base_title"] = _texts(
    recs["D_textboxstyle.base"]["svg"], "T")
res["D_legend_col_gap"]["same_as_base"] = int(
    recs["D_legend_col_gap.probe"]["sha"]
    == recs["D_legend_col_gap.base"]["sha"])
for tag in ("probe", "base"):
    t = recs["D_legend_col_gap." + tag]["svg"]
    res["D_legend_col_gap"][tag + "_keys"] = [
        _texts(t, "Mileage (mpg)"), _texts(t, "Price")]
_pair("D_plabelboxed", "D_plabelboxed.probe", "D_plabelboxed.base")
res["D_plabelboxed"]["same_as_base"] = res["D_plabelboxed"].pop(
    "same_as_reference")
up, us = recs["U_unknown.probe"], recs["U_unknown.s2color"]
res["U_unknown"] = {"cmd": up["cmd"], "rc": up["rc"], "notes": up["notes"],
                    "same_as_s2color": int(up["sha"] == us["sha"])}
pp = recs["U_path.probe"]
res["U_path"] = {"cmd": pp["cmd"], "rc": pp["rc"], "notes": pp["notes"],
                 "same_as_s2color": int(pp["sha"] == us["sha"])}
res["files"] = {}
for f in sorted(os.listdir(ud)):
    with open(os.path.join(ud, f), encoding="utf-8") as fh:
        res["files"][f] = fh.read()
with open(os.path.join(od, "scheme-economist.scheme"), encoding="utf-8") as fh:
    res["files"]["ORDER/scheme-economist.scheme"] = fh.read()
res["_meta"] = {"stata_version": Macro.getLocal("stata_version"),
                "born_date": Macro.getLocal("born_date"),
                "dash_commit": Macro.getLocal("dash_commit"),
                "extracted": Macro.getLocal("extracted"),
                "source": "scripts/extract_style_leaf_truth.do"}
dst = os.path.join(repo, "test", "fixtures", "style_leaf_truth.json")
with open(dst, "w", encoding="utf-8") as fh:
    json.dump(res, fh, indent=2, sort_keys=True)
    fh.write("\n")
for k in sorted(res):
    v = res[k]
    if isinstance(v, dict) and k[:2] in ("L_", "D_", "U_", "S_"):
        print(k, {a: b for a, b in v.items()
                  if a in ("rc", "notes", "same_as_reference", "same_as_solid",
                           "same_as_base", "same_as_s2color", "dasharray")})
print("S_order", res["S_order"])
end
adopath - "`ud'"
set scheme `entry_scheme'
