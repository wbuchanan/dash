*! extract_title_box_truth.do -- WP-43 section 43-05: measure how twoway
*! draws the boxes of title(), subtitle(), note() and caption() -- the
*! textbox fill and line under stcolor and s2color (LT-8), real-valued
*! rings and ring words on titles, edge titles and the legend (LT-9,
*! LT-14), placement() at ring(0) (LT-16), the further sub-options and
*! the side clocks (LT-18), and the edge titles' box, justification(),
*! margin(), tstyle() and direction (LT-19).  twoway only: the output is
*! the same before and after dash changes.
*!
*! Output: test/fixtures/title_box_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_title_box_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.
*! Each row records the command twoway ran, its rc, every line it printed,
*! and (when it drew) every text and rect of its SVG export.

clear all
set more off
set linesize 200

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_tb_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_tb_bad' {
    display as error "extract_title_box_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _tb_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_tb_rc' | _rc {
    local _tb_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_title_box_truth.do: `_tb_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global TB_REPO "`repo'"
global TB_OUT "${TB_REPO}/test/fixtures/title_box_truth.json"

local work "`c(tmpdir)'dash_title_box_probe"
capture mkdir "`work'"
global TB_WORK "`work'"

quietly shell git -C "${TB_REPO}" rev-parse HEAD > "${TB_WORK}/git_head.txt"
global TB_VERSION "`c(stata_version)'"
global TB_BORN "`c(born_date)'"
global TB_WHEN "`c(current_date)' `c(current_time)'"

sysuse auto, clear
global TB_KEYS ""
global TB_N 0

* _tb_run key scheme cmd: run cmd under scheme, logging what it prints,
* and export the SVG when it draws.
capture program drop _tb_run
program define _tb_run
    args key scheme cmd
    * Files are numbered: the file system may fold case (ring(inside)
    * and ring(Inside) are two probes).
    global TB_N = ${TB_N} + 1
    local f "f${TB_N}"
    global TB_F_`key' "`f'"
    set scheme `scheme'
    capture graph drop u43t
    capture log close tbr
    quietly log using "${TB_WORK}/r_`f'.log", text replace name(tbr)
    capture noisily `macval(cmd)'
    local rc = _rc
    quietly log close tbr
    global TB_R_`key' "`rc'"
    global TB_S_`key' "`scheme'"
    global TB_C_`key' `"`macval(cmd)'"'
    global TB_KEYS "${TB_KEYS} `key'"
    capture erase "${TB_WORK}/`f'.svg"
    if !`rc' {
        quietly graph export "${TB_WORK}/`f'.svg", replace
    }
end

local B "twoway scatter mpg weight"
local N "name(u43t, replace)"

* LT-8: the boxes' fill and line under each scheme.
foreach s in stcolor s2color {
    _tb_run box_title_`s' `s' `"`B', title("T", box) `N'"'
    _tb_run box_subtitle_`s' `s' `"`B', subtitle("S", box) `N'"'
    _tb_run box_note_`s' `s' `"`B', note("N", box) `N'"'
    _tb_run box_caption_`s' `s' `"`B', caption("C", box) `N'"'
    _tb_run box_t1title_`s' `s' `"`B', t1title("E", box) `N'"'
    _tb_run plain_`s' `s' `"`B', title("T") `N'"'
}

* LT-9: real-valued rings.
_tb_run ring_ctrl s2color `"`B', title("T") subtitle("S") `N'"'
_tb_run ring_75 s2color `"`B', title("T") subtitle("S", ring(7.5)) `N'"'
_tb_run ring_65 s2color `"`B', title("T") subtitle("S", ring(6.5)) note("N", position(12)) `N'"'
_tb_run ring_p5 s2color `"`B', title("T") subtitle("S", ring(.5)) `N'"'
_tb_run ring_100 s2color `"`B', title("T") subtitle("S", ring(100)) `N'"'
_tb_run ring_neg s2color `"`B', title("T") subtitle("S", ring(-1)) `N'"'
_tb_run ring_101 s2color `"`B', title("T") subtitle("S", ring(101)) `N'"'
_tb_run leg_45 s2color `"twoway (scatter mpg weight) (scatter trunk weight), note("N") legend(position(6) ring(4.5)) `N'"'
_tb_run leg_ctrl s2color `"twoway (scatter mpg weight) (scatter trunk weight), note("N") legend(position(6)) `N'"'
_tb_run e_r1_ring75 s2color `"`B', title("T", position(3)) r1title("E", ring(7.5)) `N'"'
_tb_run e_r1_ringctrl s2color `"`B', title("T", position(3)) r1title("E") `N'"'

* LT-14 and the ring words.
_tb_run ring_x s2color `"`B', title("T", ring(x)) `N'"'
_tb_run e_ring_x s2color `"`B', t1title("E", ring(x)) `N'"'
_tb_run leg_ring_x s2color `"twoway (scatter mpg weight) (scatter trunk weight), legend(ring(x)) `N'"'
_tb_run ring_0 s2color `"`B', title("T", ring(0)) `N'"'
_tb_run ring_1 s2color `"`B', title("T", ring(1)) `N'"'
_tb_run leg_ring_0 s2color `"twoway (scatter mpg weight) (scatter trunk weight), legend(ring(0)) `N'"'
_tb_run leg_ring_1 s2color `"twoway (scatter mpg weight) (scatter trunk weight), legend(ring(1)) `N'"'
foreach w in inside outside in out o i Inside OUTSIDE ins insid ou outs outsid {
    _tb_run ring_w_`w' s2color `"`B', title("T", ring(`w')) `N'"'
    _tb_run leg_ring_w_`w' s2color `"twoway (scatter mpg weight) (scatter trunk weight), legend(ring(`w')) `N'"'
    _tb_run e_ring_w_`w' s2color `"`B', t1title("E", ring(`w')) `N'"'
}
_tb_run e_ring_neg s2color `"`B', t1title("E", ring(-1)) `N'"'
_tb_run note_ring_x s2color `"`B', note("N", ring(x)) `N'"'
_tb_run sub_ring_x s2color `"`B', subtitle("S", ring(x)) `N'"'
_tb_run cap_ring_x s2color `"`B', caption("C", ring(x)) `N'"'
_tb_run leg_ring_neg s2color `"twoway (scatter mpg weight) (scatter trunk weight), legend(ring(-1)) `N'"'
_tb_run leg_ring_101 s2color `"twoway (scatter mpg weight) (scatter trunk weight), legend(ring(101)) `N'"'

* LT-16: placement() at ring(0) and outside.
foreach x in n north 12 top t nor N ne neast 1 sw c center s se w e nw {
    _tb_run pl_`x' s2color `"`B', title("TT", ring(0) placement(`x')) `N'"'
}
_tb_run pl_ring0 s2color `"`B', title("TT", ring(0)) `N'"'
_tb_run pl_pos1_sw s2color `"`B', title("TT", ring(0) position(1) placement(sw)) `N'"'
_tb_run pl_pos1 s2color `"`B', title("TT", ring(0) position(1)) `N'"'
_tb_run pl_side_w s2color `"`B', title("TT", placement(w)) `N'"'
_tb_run pl_side_e s2color `"`B', title("TT", placement(e)) `N'"'
_tb_run pl_side_ctrl s2color `"`B', title("TT") `N'"'

* LT-18: the further sub-options and the side clocks.
_tb_run t_ctrl s2color `"`B', title("T") `N'"'
_tb_run t_box s2color `"`B', title("T", box) `N'"'
_tb_run t_or_vertical s2color `"`B', title("T", orientation(vertical) box) `N'"'
_tb_run t_or_rvertical s2color `"`B', title("T", orientation(rvertical) box) `N'"'
_tb_run t_or_rhorizontal s2color `"`B', title("T", orientation(rhorizontal) box) `N'"'
_tb_run t_or_vertical_nobox s2color `"`B', title("T", orientation(vertical)) `N'"'
_tb_run t_width s2color `"`B', title("T", width(50) box) `N'"'
_tb_run t_height s2color `"`B', title("T", height(20) box) `N'"'
_tb_run t_angle s2color `"`B', title("T", angle(45)) `N'"'
_tb_run t_angle_box s2color `"`B', title("T", angle(45) box) `N'"'
_tb_run t_lstyle s2color `"`B', title("T", lstyle(p1) box) `N'"'
_tb_run t_blwidth s2color `"`B', title("T", blwidth(vthick) box) `N'"'
_tb_run t_blcolor s2color `"`B', title("T", blcolor(red) box) `N'"'
_tb_run t_blpattern s2color `"`B', title("T", blpattern(dash) box) `N'"'
_tb_run t_blalign s2color `"`B', title("T", blalign(outside) box) `N'"'
_tb_run t_lalign s2color `"`B', title("T", lalign(outside) box) `N'"'
_tb_run t_lalign_in s2color `"`B', title("T", lalign(inside) box) `N'"'
_tb_run t_style s2color `"`B', title("T", style(subheading)) `N'"'
_tb_run t_tstyle s2color `"`B', title("T", tstyle(subheading)) `N'"'
foreach k in 2 3 4 8 9 10 {
    _tb_run t_pos`k' s2color `"`B', title("T", position(`k') box) `N'"'
}
_tb_run t_or_scale s2color `"`B', title("T", orientation(vertical) box) scale(1.5) `N'"'

* LT-19: the edge titles.
_tb_run e_t1_box s2color `"`B', t1title("E", box) `N'"'
_tb_run e_t1_plain s2color `"`B', t1title("E") `N'"'
_tb_run e_t1_boxjl s2color `"`B', t1title("E", box justification(left)) `N'"'
_tb_run e_b1_mbox s2color `"`B', b1title("E", margin(large) box) `N'"'
_tb_run e_b1_box s2color `"`B', b1title("E", box) `N'"'
_tb_run e_t2_ts s2color `"`B', t2title("E", tstyle(heading)) `N'"'
_tb_run e_r1_dir s2color `"`B', r1title("Edge") `N'"'
_tb_run e_r2_dir s2color `"`B', r2title("Edge") `N'"'
_tb_run e_l1_dir s2color `"`B', l1title("Edge") `N'"'
_tb_run e_r1_box s2color `"`B', r1title("Edge", box) `N'"'
foreach j in left center right {
    _tb_run e_r1_just_`j' s2color `"`B', r1title("Edge", justification(`j')) `N'"'
}
_tb_run e_by_r_dir s2color `"`B', by(foreign, r1title("R1") r2title("R2")) `N'"'
_tb_run e_t1_placement s2color `"`B', t1title("E", placement(w)) `N'"'

python:
import json, os, re
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


work = G("TB_WORK")
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


def row(key):
    rc = int(G("TB_R_" + key))
    f = G("TB_F_" + key)
    out = {"rc": rc, "lines": logged(f), "scheme": G("TB_S_" + key),
           "command": G("TB_C_" + key).replace(" name(u43t, replace)", "")}
    if rc == 0:
        out.update(svg(f))
    return out


keys = G("TB_KEYS").split()
out = {k: row(k) for k in keys}
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("TB_VERSION"), "born_date": G("TB_BORN"),
                "dash_commit": commit, "extracted": G("TB_WHEN"),
                "source": "scripts/extract_title_box_truth.do",
                "units": "SVG user units of graph export, as(svg)"}
with open(G("TB_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote", G("TB_OUT"), len(keys), "probes")
end
