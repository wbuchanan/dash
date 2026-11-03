*! extract_colorvar_key_truth.do -- WP-42 section 42-03 (CV-3, CV-15,
*! LT-12, AX-12, LT-22, CV-8a): measure the colour key twoway draws --
*! its swatches (element kind, colour, place), its z axis (the axis line,
*! the ticks, the labels and their places), its title and every text --
*! for the key forms, the plot types, the z options and the clegend()
*! sub-options the section draws.  twoway only: the output is the same
*! before and after dash changes.
*!
*! Output: test/fixtures/colorvar_key_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_colorvar_key_truth.do
*!
*! PROBES (scheme s2color; each a `twoway' command, exported as SVG)
*!   K*        the key forms on scatter mpg weight (auto): colordiscrete
*!             rep78 and foreign, colorlevels(3), colorcuts(2 4), zlabel(,
*!             valuelabel), colorotherlabel(), colorvar(price), an
*!             all-missing colorvar.
*!   T*, S_*   the swatch each plot type keys with: rep78 colordiscrete on
*!             every type twoway colours.
*!   C24, C26  zlabel(1 3 5) and zscale(reverse) on a discrete key.
*!   P_*       clegend()'s sub-options: altaxis, region(), ring(0)
*!             position() bplacement() (and its controls), bmargin() at
*!             three sizes, subtitle() note()
*!             caption(), width() height().
*!   Z*        the z tick family: ztick(), zticks(), zmlabel(), zmtick(),
*!             zmticks(), zlabels(), zlabel() on colorvar(price).
*!   C_*, CL_* contour and contourline on sandstone: the key, title(),
*!             title(, box), colorlines, plegend(position(6)).
*!   B_*       contour on surface under by(date): no key, clegend(on),
*!             clegend(on pos(6)).
*! Each probe records rc (and twoway's first error line), the canvas, the
*! plot region(s), every text (x, y, rotation, size, anchor, fill), the
*! filled regions, and the key: every circle, rect, line and path whose
*! centre is right of the rightmost plot region or below the lowest one
*! by more than the x labels' band (more than 200 SVG units).
*!
*! The git commit is read from a file `shell' wrote, never with
*! shell=True.

clear all
set more off
set linesize 200

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zk_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zk_bad' {
    display as error "extract_colorvar_key_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_colorvar_key_truth.do: `_zk_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZK_REPO "`repo'"
global ZK_OUT "${ZK_REPO}/test/fixtures/colorvar_key_truth.json"

local work "`c(tmpdir)'dash_colorvar_key_probe"
capture mkdir "`work'"
global ZK_WORK "`work'"

quietly shell git -C "${ZK_REPO}" rev-parse HEAD > "${ZK_WORK}/git_head.txt"
global ZK_VERSION "`c(stata_version)'"
global ZK_BORN "`c(born_date)'"
global ZK_WHEN "`c(current_date)' `c(current_time)'"

capture program drop _zk_probe
program define _zk_probe
    // _zk_probe <id> <twoway command ...>: run it, export its SVG, keep
    // its rc and first error line.
    gettoken id 0 : 0
    capture erase "${ZK_WORK}/`id'.svg"
    capture erase "${ZK_WORK}/`id'.log"
    capture log close zkl
    quietly log using "${ZK_WORK}/`id'.log", text replace name(zkl)
    local zsch "s2color"
    if `"${ZK_SCHEME}"' != "" local zsch "${ZK_SCHEME}"
    capture noisily twoway `0' scheme(`zsch') name(zk1, replace)
    local rc = _rc
    quietly log close zkl
    global ZK_RC_`id' = `rc'
    global ZK_CMD_`id' `"twoway `0'"'
    if `rc' == 0 {
        quietly graph export "${ZK_WORK}/`id'.svg", replace
        graph drop zk1
    }
    global ZK_IDS "${ZK_IDS} `id'"
end

global ZK_IDS ""
sysuse auto, clear
generate zmiss = .
local sc "scatter mpg weight,"
_zk_probe K1 `sc' colorvar(rep78) colordiscrete
_zk_probe K2 `sc' colorvar(foreign) colordiscrete
_zk_probe K3 `sc' colorvar(rep78) colorlevels(3)
_zk_probe K4 `sc' colorvar(rep78) colorcuts(2 4)
_zk_probe K7 `sc' colorvar(foreign) colordiscrete zlabel(, valuelabel)
_zk_probe K8 `sc' colorvar(rep78) colordiscrete colorcuts(3 4) colorotherlabel("rest")
_zk_probe K_cont `sc' colorvar(price)
_zk_probe K_box `sc' colorvar(rep78) colordiscrete xsize(6) ysize(4)
// WP-42 CV-3: the key's place under other schemes (K1 under stcolor,
// s1color and economist), for the gaps per scheme.
foreach sch in stcolor s1color economist {
    global ZK_SCHEME "`sch'"
    _zk_probe K1_`sch' `sc' colorvar(rep78) colordiscrete
}
global ZK_SCHEME ""
_zk_probe E_allmiss `sc' colorvar(zmiss)
_zk_probe T1 bar mpg weight, colorvar(rep78) colordiscrete
_zk_probe T5 rconnected mpg turn weight, colorvar(rep78) colordiscrete
_zk_probe T_line line mpg weight, sort colorvar(rep78) colordiscrete
foreach ty in scatter connected line area bar spike dropline dot {
    _zk_probe S_`ty' `ty' mpg weight, sort colorvar(rep78) colordiscrete
}
foreach ty in rarea rbar rspike rcap rcapsym rscatter rline rconnected {
    _zk_probe S_`ty' `ty' mpg turn weight, sort colorvar(rep78) colordiscrete
}
foreach ty in pcspike pccapsym pcarrow pcbarrow pcscatter {
    _zk_probe S_`ty' `ty' mpg weight turn length, colorvar(rep78) colordiscrete
}
_zk_probe C24 `sc' colorvar(rep78) colordiscrete zlabel(1 3 5)
_zk_probe C26 `sc' colorvar(rep78) colordiscrete zscale(reverse)
_zk_probe P_alt `sc' colorvar(rep78) colordiscrete clegend(altaxis)
_zk_probe P_reg `sc' colorvar(rep78) colordiscrete clegend(region(fcolor(gs14) lcolor(red)))
_zk_probe P_bp_1 `sc' colorvar(rep78) colordiscrete clegend(ring(0) position(1))
_zk_probe P_bp_7 `sc' colorvar(rep78) colordiscrete clegend(ring(0) position(7) bplacement(sw))
_zk_probe P_bm `sc' colorvar(rep78) colordiscrete clegend(bmargin(large))
// WP-42 CV-15: bplacement() against its control (P_bp_7c), on a side
// key (P_bp_n, P_bp_s), and bmargin() at two more sizes (P_bm_m, P_bm_v).
_zk_probe P_bp_7c `sc' colorvar(rep78) colordiscrete clegend(ring(0) position(7))
_zk_probe P_bp_n `sc' colorvar(rep78) colordiscrete clegend(bplacement(north))
_zk_probe P_bp_s `sc' colorvar(rep78) colordiscrete clegend(bplacement(south))
_zk_probe P_bm_m `sc' colorvar(rep78) colordiscrete clegend(bmargin(medium))
_zk_probe P_bm_v `sc' colorvar(rep78) colordiscrete clegend(bmargin(vlarge))
_zk_probe P_sub `sc' colorvar(rep78) colordiscrete clegend(subtitle("S") note("N") caption("C"))
_zk_probe P_w `sc' colorvar(rep78) colordiscrete clegend(width(5) height(40))
_zk_probe Z1 `sc' colorvar(price) ztick(5000 10000)
_zk_probe Z1p `sc' colorvar(price) zticks(5000 10000)
_zk_probe Z2 `sc' colorvar(price) zmlabel(7500)
_zk_probe Z3 `sc' colorvar(price) zmtick(2500(5000)17500)
_zk_probe Z3p `sc' colorvar(price) zmticks(2500(5000)17500)
_zk_probe Z4 `sc' colorvar(price) zlabels(4000 8000 12000)
_zk_probe Z4s `sc' colorvar(price) zlabel(4000 8000 12000)
sysuse sandstone, clear
_zk_probe C_plain contour depth northing easting,
_zk_probe C_ti contour depth northing easting, clegend(title("Z"))
_zk_probe C_cbx contour depth northing easting, clegend(title("Z", box))
_zk_probe CL_ctl contourline depth northing easting,
_zk_probe CL_cl contourline depth northing easting, colorlines
_zk_probe CL_clp contourline depth northing easting, colorlines plegend(position(6))
sysuse surface, clear
_zk_probe B_none contour temperature latitude longitude, levels(10) by(date)
_zk_probe B_on contour temperature latitude longitude, levels(10) by(date, clegend(on))
_zk_probe B_on6 contour temperature latitude longitude, levels(10) by(date, clegend(on pos(6)))

python:
import json, os, re, sys
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


work = G("ZK_WORK")
sys.path.insert(0, os.path.join(G("ZK_REPO"), "scripts"))
from svg_truth import svg_document  # noqa: E402

_NUM = re.compile(r"-?\d+(?:\.\d+)?")


def r2(v):
    return round(v, 2) if isinstance(v, float) else v


def centre(e):
    if "cx" in e:
        return e["cx"], e["cy"]
    if "x1" in e:
        return (e["x1"] + e["x2"]) / 2.0, (e["y1"] + e["y2"]) / 2.0
    if "w" in e:
        return e["x"] + (e["w"] or 0) / 2.0, e["y"] + (e["h"] or 0) / 2.0
    n = [float(v) for v in _NUM.findall(e.get("d") or "")]
    if len(n) < 2:
        return None, None
    xs, ys = n[0::2], n[1::2]
    return (min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0


def first_line(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                s = ln.strip()
                if (s and not s.startswith((". ", "> ", "("))
                        and not s.startswith("r(")):
                    return s
    except OSError:
        pass
    return ""


def record(pid):
    rc = int(G("ZK_RC_" + pid))
    rec = {"rc": rc, "command": G("ZK_CMD_" + pid)}
    lg = os.path.join(work, pid + ".log")
    if rc:
        rec["message"] = first_line(lg)
    if os.path.exists(lg):
        os.remove(lg)
    path = os.path.join(work, pid + ".svg")
    if rc or not os.path.exists(path):
        return rec
    doc = svg_document(path)
    os.remove(path)
    pans = ([g for g in doc["regions"] if g.get("fill") == "#ffffff"]
            or [doc["plotregion"]])
    right = max(g["right"] for g in pans)
    bottom = max(g["bottom"] for g in pans)
    rec["canvas"] = doc["canvas"]
    rec["plot"] = {k: r2(doc["plotregion"][k])
                   for k in ("left", "top", "right", "bottom")}
    rec["panels"] = [{k: r2(g[k]) for k in ("left", "top", "right",
                                             "bottom")} for g in pans]
    rec["regions"] = [{k: r2(v) for k, v in g.items()}
                      for g in doc["regions"]]
    rec["texts"] = [{"text": t["text"], "x": r2(t["x"]), "y": r2(t["y"]),
                     "rotate": t["rotate"], "size": r2(t["size"]),
                     "anchor": t["anchor"], "fill": t["fill"]}
                    for t in doc["texts"]]
    key = {}
    for kind in ("circles", "rects", "hlines", "vlines", "diaglines",
                 "paths"):
        rows = []
        for e in doc[kind]:
            x, y = centre(e)
            if x is None or not (x > right + 1 or y > bottom + 200):
                continue
            row = {k: r2(v) for k, v in e.items() if k != "d"}
            row["cx"], row["cy"] = r2(x), r2(y)
            rows.append(row)
        key[kind] = rows
    rec["key"] = key
    return rec


out = {}
for pid in G("ZK_IDS").split():
    out[pid] = record(pid)
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZK_VERSION"), "born_date": G("ZK_BORN"),
                "dash_commit": commit, "extracted": G("ZK_WHEN"),
                "source": "scripts/extract_colorvar_key_truth.do",
                "scheme": "s2color",
                "units": "SVG units of graph export, 720 a graph inch"}
with open(G("ZK_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZK_OUT"))
end
