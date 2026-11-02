*! extract_colorvar_refusal_truth.do -- WP-42 section 42-05 (CV-2, CV-9,
*! CV-10, CV-14): measure twoway's colordiscrete colorlevels() cuts, its
*! refusals of colorcuts(), colorlevels() and colorvar() values, of
*! malformed clegend(), plegend(), zlabel() and zscale() texts, of the
*! colorvar spellings it does not take, and its answer to a colorvar()
*! layer whose qualifiers keep no observation.  twoway only: the output
*! is the same before and after dash changes.
*!
*! Output: test/fixtures/colorvar_refusal_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_colorvar_refusal_truth.do
*!
*! PROBES (sysuse auto, scheme s2color, unless named).  Every probe is run
*! drawn (not nodraw) under -capture noisily- with its printed lines in a
*! log; the rc and every non-blank printed line are recorded, and a drawn
*! graph is exported to SVG, from which the key's texts (right of the
*! plot region, top to bottom) and the in-region marker fills (circle) or
*! line strokes (path) are read through scripts/svg_truth.py.
*!   L*   colordiscrete colorlevels(4) cuts (L2-L5 on z = 0, 10, ..., 100).
*!   R*   colorcuts(), colorlevels() and colorvar() value refusals.
*!   K*   clegend() sub-options (each word with a legal value) and the
*!        malformed clegend(), plegend(), zlabel() and zscale() texts.
*!   W*   cv(), colv(), colornlevels(), colormissing(), colpalette().
*!   E*   a colorvar() layer with no observation, and the all-missing ones.
*!
*! The git commit is read from a file -shell- wrote, never with shell=True.

clear all
set more off
set linesize 200

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zo_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zo_bad' {
    display as error "extract_colorvar_refusal_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zo_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zo_rc' | _rc {
    local _zo_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_colorvar_refusal_truth.do: `_zo_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZR_REPO "`repo'"
global ZR_OUT "${ZR_REPO}/test/fixtures/colorvar_refusal_truth.json"

tempfile _zr_base
local work "`_zr_base'_cvref"
capture mkdir "`work'"
global ZR_WORK "`work'"

quietly shell git -C "${ZR_REPO}" rev-parse HEAD > "${ZR_WORK}/git_head.txt"
global ZR_VERSION "`c(stata_version)'"
global ZR_BORN "`c(born_date)'"

* _zr_run key cmd: run `cmd' drawn with its printed lines in <key>.log;
* the rc in ZR_RC_<key>, the command in ZR_CMD_<key>; the graph exported
* to <key>.svg when it drew.
capture program drop _zr_run
program define _zr_run
    gettoken key 0 : 0
    capture erase "${ZR_WORK}/`key'.log"
    capture erase "${ZR_WORK}/`key'.svg"
    quietly log using "${ZR_WORK}/`key'.log", text replace name(zrref)
    capture noisily `0' name(zr1, replace)
    local rc = _rc
    display as text "{p_end}"
    quietly log close zrref
    global ZR_RC_`key' "`rc'"
    global ZR_CMD_`key' `"`0'"'
    if `rc' == 0 {
        capture graph describe zr1
        if _rc == 0 {
            quietly graph export "${ZR_WORK}/`key'.svg", replace
            graph drop zr1
        }
    }
    global ZR_KEYS "${ZR_KEYS} `key'"
end
global ZR_KEYS ""
set scheme s2color

* ---- L: colordiscrete colorlevels(k) ------------------------------------
sysuse auto, clear
_zr_run L1 twoway scatter mpg weight, colorvar(rep78) colordiscrete colorlevels(4)
clear
set obs 11
gen z = (_n - 1) * 10
gen y = _n
gen x = _n
_zr_run L2 twoway scatter y x, colorvar(z) colordiscrete colorlevels(4)
_zr_run L3 twoway scatter y x, colorvar(z) colordiscrete colorlevels(4) colorvarminmax
_zr_run L4 twoway scatter y x, colorvar(z) colorlevels(4)
_zr_run L5 twoway line y x, colorvar(z) colordiscrete colorlevels(4)

* ---- R: value refusals -----------------------------------------------------
sysuse auto, clear
local sc "twoway scatter mpg weight"
_zr_run R_cuts_abc     `sc', colorvar(rep78) colorcuts(abc)
_zr_run R_levels_abc   `sc', colorvar(rep78) colorlevels(abc)
_zr_run R_levels_frac  `sc', colorvar(rep78) colorlevels(2.5)
_zr_run R_var_two      `sc', colorvar(rep78 foreign)
_zr_run R_var_wild     `sc', colorvar(pri*)
_zr_run R_var_range    `sc', colorvar(price-length)
_zr_run R_var_nosuch   `sc', colorvar(nosuch)
_zr_run R_var_abbrev   `sc', colorvar(pri)
_zr_run R_var_string   `sc', colorvar(make)
gen t = _n
quietly tsset t
_zr_run R_var_ts       `sc', colorvar(L.price)
quietly tsset, clear
drop t

* ---- K: colour-key options -------------------------------------------------
local cv "`sc', colorvar(price)"
_zr_run K_cleg_width      `cv' clegend(width(5))
_zr_run K_cleg_height     `cv' clegend(height(20))
_zr_run K_cleg_altaxis    `cv' clegend(altaxis)
_zr_run K_cleg_bmargin    `cv' clegend(bmargin(small))
_zr_run K_cleg_region     `cv' clegend(region(fcolor(white)))
_zr_run K_cleg_off        `cv' clegend(off)
_zr_run K_cleg_on         `cv' clegend(on)
_zr_run K_cleg_position   `cv' clegend(position(6))
_zr_run K_cleg_ring       `cv' clegend(ring(1))
_zr_run K_cleg_bplacement `cv' clegend(bplacement(e))
_zr_run K_cleg_at         twoway scatter mpg weight, colorvar(price) by(foreign) clegend(at(3))
_zr_run K_cleg_title      `cv' clegend(title("T"))
_zr_run K_cleg_subtitle   `cv' clegend(subtitle("S"))
_zr_run K_cleg_note       `cv' clegend(note("N"))
_zr_run K_cleg_caption    `cv' clegend(caption("C"))
foreach w in t1title t2title b1title b2title l1title l2title r1title r2title {
    _zr_run K_cleg_`w'    `cv' clegend(`w'("A"))
}
_zr_run K_cleg_bogus      `cv' clegend(bogus)
_zr_run K_cleg_bogusp     `cv' clegend(bogus(1))
_zr_run K_pleg_position   `sc', colorvar(rep78) colordiscrete coloruseplegend plegend(position(6))
_zr_run K_pleg_bogus      `sc', colorvar(rep78) colordiscrete coloruseplegend plegend(bogus)
_zr_run K_pleg_bogus_nopl `cv' plegend(bogus)
_zr_run K_zlab_bogus      `cv' zlabel(bogus)
_zr_run K_zlab_bogus_disc `sc', colorvar(rep78) colordiscrete zlabel(bogus)
_zr_run K_zsc_log         `cv' zscale(log)
_zr_run K_zsc_range       `cv' zscale(range(0 20000))
_zr_run K_zsc_bogus       `cv' zscale(bogus)
* The same words where no colour key is drawn: no colorvar(), and a
* plot legend without coloruseplegend.
_zr_run K_cleg_bogus_nocv `sc', clegend(bogus)
_zr_run K_pleg_bogus_nocv `sc', plegend(bogus)
_zr_run K_zlab_bogus_nocv `sc', zlabel(bogus)
_zr_run K_zsc_bogus_nocv  `sc', zscale(bogus)
_zr_run K_cleg_bogus_disc `sc', colorvar(rep78) colordiscrete clegend(bogus)
_zr_run K_pleg_bogus_disc `sc', colorvar(rep78) colordiscrete plegend(bogus)
_zr_run K_cleg_bogus_upl  `sc', colorvar(rep78) colordiscrete coloruseplegend clegend(bogus)
_zr_run K_cleg_abbrev     `cv' cleg(off)
_zr_run K_pleg_abbrev     `sc', colorvar(rep78) colordiscrete coloruseplegend pleg(off)

* ---- W: the spellings twoway does not take ---------------------------------
_zr_run W_cv           `sc', cv(price)
_zr_run W_colv         `sc', colv(price)
_zr_run W_colornlevels `sc', colorvar(price) colornlevels(5)
_zr_run W_colormissing `sc', colorvar(price) colormissing(red)
_zr_run W_colpalette   `sc', colorvar(price) colpalette(viridis)

* ---- E: no observation, and all missing -----------------------------------
_zr_run E_empty       `sc' if price < 0, colorvar(price)
_zr_run E_empty_disc  `sc' if price < 0, colorvar(price) colordiscrete
_zr_run E_empty_line  twoway line mpg weight if price < 0, colorvar(price)
_zr_run E_empty_levels `sc' if price < 0, colorvar(price) colorlevels(4)
_zr_run E_empty_cuts  `sc' if price < 0, colorvar(price) colorcuts(5000)
_zr_run E_empty_ipre  `sc' if price < 0, colorvar(i.rep78)
_zr_run E_empty_in    `sc' in 1/1 if price < 0, colorvar(price)
gen ymiss = .
_zr_run E_allmiss_y   twoway scatter ymiss weight, colorvar(price)
drop ymiss
_zr_run E_by          `sc' if price < 0, colorvar(price) by(foreign)
_zr_run E_two         twoway (scatter mpg weight) (scatter mpg weight if price < 0, colorvar(price)),
gen m = .
_zr_run E_allmiss     `sc', colorvar(m)
drop m
preserve
quietly drop if 1
_zr_run E_nodata      `sc', colorvar(price)
_zr_run E_nodata_disc `sc', colorvar(price) colordiscrete
restore

* ---- data the pytest side redraws ------------------------------------------
sysuse auto, clear
quietly export delimited mpg weight rep78 using "${ZR_WORK}/auto.csv", replace nolabel

python:
import datetime, json, os, re, sys
from sfi import Macro

G = Macro.getGlobal
work = G("ZR_WORK")
repo = G("ZR_REPO")
sys.path.insert(0, os.path.join(repo, "scripts"))
from svg_truth import svg_document

_SKIP = ("name:", "log:", "log type:", "opened on:", "closed on:")


def lines_of(key):
    out = []
    with open(os.path.join(work, key + ".log"), encoding="utf-8",
              errors="replace") as fh:
        for ln in fh:
            s = ln.rstrip("\n").rstrip()
            if not s.strip() or s.strip().startswith(_SKIP) or \
                    s.strip() == "{p_end}":
                continue
            out.append(s)
    return out


def inside(pr, x, y):
    return bool(pr) and pr["left"] - 0.5 <= x <= pr["right"] + 0.5 and \
        pr["top"] - 0.5 <= y <= pr["bottom"] + 0.5


def drawn(path):
    doc = svg_document(path)
    pr = doc["plotregion"] or {}
    right = pr.get("right")
    texts = sorted((t for t in doc["texts"] if right is not None
                    and t["x"] is not None and t["x"] > right + 1
                    and not t["rotate"]), key=lambda t: (t["y"], t["x"]))
    circles, strokes = [], {}
    for c in doc["circles"]:
        if c.get("cx") is not None and inside(pr, c["cx"], c["cy"]) and \
                c["fill"] not in (None, "none"):
            circles.append(c["fill"])
    for q in doc["paths"]:
        if q["stroke"] not in (None, "none"):
            strokes[q["stroke"]] = strokes.get(q["stroke"], 0) + 1
    return {"key_texts": [t["text"] for t in texts],
            "marker_fills": circles, "path_strokes": strokes}


probes = {}
for key in G("ZR_KEYS").split():
    p = {"command": G("ZR_CMD_" + key), "rc": int(G("ZR_RC_" + key)),
         "lines": lines_of(key)}
    svg = os.path.join(work, key + ".svg")
    if p["rc"] == 0 and os.path.exists(svg):
        p.update(drawn(svg))
    probes[key] = p

data = {"z": [float(10 * i) for i in range(11)],
        "y": [float(i + 1) for i in range(11)],
        "x": [float(i + 1) for i in range(11)]}
auto = {"mpg": [], "weight": [], "rep78": []}
with open(os.path.join(work, "auto.csv"), encoding="utf-8") as fh:
    head = fh.readline().strip().split(",")
    for ln in fh:
        row = dict(zip(head, ln.strip().split(",")))
        for k in auto:
            v = row[k]
            auto[k].append(None if v in ("", ".") else float(v))

with open(os.path.join(work, "git_head.txt"), encoding="utf-8") as fh:
    head = fh.read().strip()
meta = {"stata_version": G("ZR_VERSION"), "born_date": G("ZR_BORN"),
        "dash_commit": head,
        "extracted": datetime.date.today().isoformat(),
        "source": "scripts/extract_colorvar_refusal_truth.do",
        "scheme": "s2color",
        "method": "each probe run drawn under capture noisily; rc and every "
                  "non-blank printed line; key_texts are the SVG texts right "
                  "of the plot region, top to bottom; marker_fills the "
                  "in-region circle fills in document order; path_strokes "
                  "the path strokes by colour"}
out = {"_meta": meta, "_data": {"steps": data, "auto": auto},
       "probes": probes}
with open(G("ZR_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote", G("ZR_OUT"), len(probes), "probes")
end
