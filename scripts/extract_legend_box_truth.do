*! extract_legend_box_truth.do -- WP-43 section 43-03: measure how twoway
*! draws the legend's box and key texts -- nobox and box (LT-2), the key
*! texts' textbox options (LT-3), the layout and region style sub-options
*! (LT-6), bexpand on the legend and the title boxes (LT-7) and every
*! marginstyle form on text boxes and the legend, bmargin() per side
*! (LT-10).  twoway only: the output is the same before and after dash
*! changes.
*!
*! Output: test/fixtures/legend_box_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_legend_box_truth.do
*!
*! (Built on scripts/extract_title_box_truth.do's probe and reader.)
*! The git commit is read from a file `shell' wrote, never with shell=True.
*! Each row records the command twoway ran, its rc, every line it printed,
*! and (when it drew) every text and rect of its SVG export and the plot
*! region's box.


clear all
set more off
set linesize 200

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_lb_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_lb_bad' {
    display as error "extract_legend_box_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _lb_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_lb_rc' | _rc {
    local _lb_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_legend_box_truth.do: `_lb_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global LB_REPO "`repo'"
global LB_OUT "${LB_REPO}/test/fixtures/legend_box_truth.json"

local work "`c(tmpdir)'dash_legend_box_probe"
capture mkdir "`work'"
global LB_WORK "`work'"

quietly shell git -C "${LB_REPO}" rev-parse HEAD > "${LB_WORK}/git_head.txt"
global LB_VERSION "`c(stata_version)'"
global LB_BORN "`c(born_date)'"
global LB_WHEN "`c(current_date)' `c(current_time)'"

sysuse auto, clear
global LB_KEYS ""
global LB_N 0

* _lb_run key scheme cmd: run cmd under scheme, logging what it prints,
* and export the SVG when it draws.
capture program drop _lb_run
program define _lb_run
    args key scheme cmd
    * Files are numbered: the file system may fold case (ring(inside)
    * and ring(Inside) are two probes).
    global LB_N = ${LB_N} + 1
    local f "f${LB_N}"
    global LB_F_`key' "`f'"
    set scheme `scheme'
    capture graph drop u43b
    capture log close lbr
    quietly log using "${LB_WORK}/r_`f'.log", text replace name(lbr)
    capture noisily `macval(cmd)'
    local rc = _rc
    quietly log close lbr
    global LB_R_`key' "`rc'"
    global LB_S_`key' "`scheme'"
    global LB_C_`key' `"`macval(cmd)'"'
    global LB_KEYS "${LB_KEYS} `key'"
    capture erase "${LB_WORK}/`f'.svg"
    if !`rc' {
        quietly graph export "${LB_WORK}/`f'.svg", replace
    }
end

local B "twoway (scatter mpg weight) (scatter price weight) (scatter turn weight)"
local N "name(u43b, replace)"

* LT-2: nobox and box.
_lb_run ctl s2color `"`B', `N'"'
_lb_run nobox s2color `"`B', legend(nobox) `N'"'
_lb_run box s2color `"`B', legend(box) `N'"'
_lb_run box_nobox s2color `"`B', legend(box nobox) `N'"'
_lb_run ctl_st stcolor `"`B', `N'"'
_lb_run nobox_st stcolor `"`B', legend(nobox) `N'"'
_lb_run box_st stcolor `"`B', legend(box) `N'"'

* LT-3: the key texts' textbox options.
_lb_run box_bcolor s2color `"`B', legend(box bcolor(gs14)) `N'"'
_lb_run box_fcolor s2color `"`B', legend(box fcolor(red)) `N'"'
_lb_run box_lcolor s2color `"`B', legend(box lcolor(red) lwidth(thick)) `N'"'
_lb_run bcolor_only s2color `"`B', legend(bcolor(gs14)) `N'"'
_lb_run cols1 s2color `"`B', legend(cols(1)) `N'"'
_lb_run just_right s2color `"`B', legend(cols(1) justification(right)) `N'"'
_lb_run just_center s2color `"`B', legend(cols(1) justification(center)) `N'"'
_lb_run align_top s2color `"`B', legend(alignment(top)) `N'"'
_lb_run align_bottom s2color `"`B', legend(alignment(bottom)) `N'"'
_lb_run margin_large s2color `"`B', legend(margin(large)) `N'"'
_lb_run box_margin_large s2color `"`B', legend(box margin(large)) `N'"'
_lb_run box_margin_small s2color `"`B', legend(box margin(small)) `N'"'
_lb_run two_line s2color `"`B', legend(label(1 "Mileage" "(mpg)")) `N'"'
_lb_run linegap5 s2color `"`B', legend(label(1 "Mileage" "(mpg)") linegap(5)) `N'"'
_lb_run tstyle s2color `"`B', legend(tstyle(heading)) `N'"'
_lb_run holes_box s2color `"`B', legend(holes(1) cols(1) box) `N'"'
_lb_run box_msmall_scale s2color `"`B', legend(box margin(small)) scale(1.5) `N'"'

* LT-6: layout and region style sub-options.
_lb_run style_column s2color `"`B', legend(style(column)) `N'"'
_lb_run style_zyx2 s2color `"`B', legend(style(zyx2)) `N'"'
_lb_run style_bogus s2color `"`B', legend(style(bogus)) `N'"'
_lb_run width60 s2color `"`B', legend(width(60)) `N'"'
_lb_run height30 s2color `"`B', legend(height(30)) `N'"'
_lb_run xoff5 s2color `"`B', legend(xoffset(5)) `N'"'
_lb_run yoff5 s2color `"`B', legend(yoffset(5)) `N'"'
_lb_run showindex s2color `"`B', legend(showindex) `N'"'
_lb_run reg_style_none s2color `"`B', legend(region(style(none))) `N'"'
_lb_run reg_lstyle_p1 s2color `"`B', legend(region(lstyle(p1))) `N'"'
_lb_run reg_thick s2color `"`B', legend(region(lwidth(thick))) `N'"'
_lb_run reg_thick_out s2color `"`B', legend(region(lwidth(thick) lalign(outside))) `N'"'
_lb_run reg_thick_in s2color `"`B', legend(region(lwidth(thick) lalign(inside))) `N'"'

* LT-7: bexpand.
_lb_run bexpand s2color `"`B', legend(bexpand) `N'"'
_lb_run bexpand_st stcolor `"`B', legend(bexpand) `N'"'
_lb_run t_box s2color `"`B', title("T", box) `N'"'
_lb_run t_bexpand s2color `"`B', title("T", box bexpand) `N'"'
_lb_run n_box s2color `"`B', note("N", box) `N'"'
_lb_run n_bexpand s2color `"`B', note("N", box bexpand) `N'"'

* LT-10: marginstyle forms and bmargin() per side.
_lb_run rm_l20 s2color `"`B', legend(region(margin(l=20))) `N'"'
_lb_run rm_1_20 s2color `"`B', legend(region(margin(1 20 1 1))) `N'"'
_lb_run bm_t20 s2color `"`B', legend(bmargin(t=20)) `N'"'
_lb_run p3 s2color `"`B', legend(pos(3)) `N'"'
_lb_run p3_bm_l20 s2color `"`B', legend(pos(3) bmargin(l=20)) `N'"'
_lb_run p2 s2color `"`B', legend(pos(2) cols(1)) `N'"'
_lb_run p2_bm_l20 s2color `"`B', legend(pos(2) cols(1) bmargin(l=20)) `N'"'
_lb_run p5 s2color `"`B', legend(pos(5) cols(1)) `N'"'
_lb_run p5_bm_t20 s2color `"`B', legend(pos(5) cols(1) bmargin(t=20)) `N'"'
_lb_run r0 s2color `"`B', legend(ring(0)) `N'"'
_lb_run r0_bm s2color `"`B', legend(ring(0) bmargin(l=20 t=10)) `N'"'
_lb_run t_plain s2color `"`B', title("T") `N'"'
_lb_run t_margin_l20 s2color `"`B', title("T", box margin(l=20)) `N'"'
_lb_run t_margin_4 s2color `"`B', title("T", box margin(1 2 3 4)) `N'"'
_lb_run t_margin_lplus s2color `"`B', title("T", box margin(l+5)) `N'"'
_lb_run c_plain s2color `"`B', caption("C") `N'"'
_lb_run c_bm_t20 s2color `"`B', caption("C", bmargin(t=20)) `N'"'
_lb_run ts_plain s2color `"`B', title("T") subtitle("S") `N'"'
_lb_run ts_bm_t20 s2color `"`B', title("T", bmargin(t=20)) subtitle("S") `N'"'
_lb_run t_bm_l40 s2color `"`B', title("T", bmargin(l=40)) `N'"'
_lb_run x_box s2color `"`B', text(30 3000 "X", box) `N'"'
_lb_run x_box_ml10 s2color `"`B', text(30 3000 "X", box margin(l=10)) `N'"'

python:
import json, os, re, sys
from sfi import Macro
def G(k):
    return Macro.getGlobal(k)


work = G("LB_WORK")
_TEXT = re.compile(r"<text\b([^>]*)>([^<]*)</text>")
_RECT = re.compile(r"<rect\b([^>]*)/?>")
_LINE = re.compile(r"<line\b([^>]*)/?>")


def attrs(s):
    return dict(re.findall(r'([a-z-]+)="([^"]*)"', s))


def svg(f):
    """Every non-numeric text (x, y, font size, rotation, anchor, style),
    every rect (x, y, w, h, style) and the SVG's width and height."""
    with open(os.path.join(work, f + ".svg"), encoding="utf-8") as fh:
        src = fh.read()
    texts = []
    for a, body in _TEXT.findall(src):
        body = body.replace("&amp;", "&").strip()
        if not body or re.fullmatch(r"[-0-9.,]+", body):
            continue
        a = attrs(a)
        fs = re.search(r"font-size:([0-9.]+)px", a.get("style", ""))
        rot = re.search(r"rotate\((-?[0-9.]+)", a.get("transform", ""))
        texts.append({"text": body, "x": float(a["x"]), "y": float(a["y"]),
                      "size": float(fs.group(1)) if fs else None,
                      "rotate": float(rot.group(1)) if rot else 0.0,
                      "anchor": a.get("text-anchor", "start"),
                      "style": a.get("style", "")})
    rects = []
    for a in _RECT.findall(src):
        a = attrs(a)
        rects.append({"x": float(a.get("x", 0)), "y": float(a.get("y", 0)),
                      "w": float(a.get("width", 0)),
                      "h": float(a.get("height", 0)),
                      "style": a.get("style", "")})
    vb = re.search(r'viewBox="([-0-9. ]+)"', src)
    return {"texts": texts, "rects": rects,
            "viewbox": [float(v) for v in vb.group(1).split()] if vb else None}


def logged(f):
    with open(os.path.join(work, "r_" + f + ".log"), encoding="utf-8") as fh:
        lines = [ln.rstrip() for ln in fh]
    return [ln.strip() for ln in lines if ln.strip()
            and not ln.startswith(".") and not ln.startswith(">")
            and not ln.lstrip().startswith(("name:", "log:", "log type:",
                                            "opened on:", "closed on:"))
            and not set(ln.strip()) <= set("-")]


def plot_box(f):
    sys.path.insert(0, os.path.join(G("LB_REPO"), "scripts"))
    import svg_truth
    pr = svg_truth.svg_plotregion(os.path.join(work, f + ".svg")) or {}
    return {k: pr.get(k) for k in ("left", "top", "right", "bottom")}


def row(key):
    rc = int(G("LB_R_" + key))
    f = G("LB_F_" + key)
    out = {"rc": rc, "lines": logged(f), "scheme": G("LB_S_" + key),
           "command": G("LB_C_" + key).replace(" name(u43b, replace)", "")}
    if rc == 0:
        out.update(svg(f))
        out["plot"] = plot_box(f)
    return out


keys = G("LB_KEYS").split()
out = {k: row(k) for k in keys}
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("LB_VERSION"), "born_date": G("LB_BORN"),
                "dash_commit": commit, "extracted": G("LB_WHEN"),
                "base": "twoway (scatter mpg weight) (scatter price weight)"
                        " (scatter turn weight)",
                "source": "scripts/extract_legend_box_truth.do",
                "units": "SVG user units of graph export, as(svg)"}
with open(G("LB_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote", G("LB_OUT"), len(keys), "probes")
end
