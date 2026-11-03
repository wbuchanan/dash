*! extract_colorvar_plegend_truth.do -- WP-42 section 42-04 (CV-4, CV-5,
*! CV-11/CV-12): measure how twoway draws the coloruseplegend key, what
*! legend()'s off, rows() and size() do to a colour key, colorkeysreverse on
*! a discrete key, and colorlevels() over a one-value colour variable.
*! twoway only: the output is the same before and after dash changes.
*!
*! Output: test/fixtures/colorvar_plegend_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_colorvar_plegend_truth.do
*!
*! PROBES (sysuse auto, scheme s2color unless named).  Each drawn probe's
*! exported SVG is read for: the plot region; every text (position, size,
*! rotation); every rect with a fill or stroke; the circles outside the
*! plot region (key swatches) and the marker fills inside it (counts).
*! `key' summarises the texts right of the plot region, top to bottom, the
*! swatches there (marker or bar) and the rect that encloses them.
*!   K5   coloruseplegend over rep78         K6   ... over foreign
*!   X1   K5 + colorotherlabel("rest")       C28  K5 + colorkeysrange
*!   M3   K5 + legend(off)                   M4   K5 + legend(rows(1))
*!   Q0   colorvar(price) with an lfit layer Q1   Q0 + legend(size(huge))
*!   Q3   K5 + lfit + legend(size(huge))     P12  Q0 + legend(rows(1))
*!   ST   K5 under scheme(stcolor)
*!   K1   colordiscrete over rep78 (the axis key, for R1)
*!   R1   K1 + colorkeysreverse              D13r K5 + colorkeysreverse
*!   I5   if rep78==3, colorlevels(3)        I5m  I5 + colorvarminmax
*!   I3   if rep78==3, colordiscrete colorlevels(2)
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zp_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zp_bad' {
    display as error "extract_colorvar_plegend_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zp_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zp_rc' | _rc {
    local _zp_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_colorvar_plegend_truth.do: `_zp_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZP_REPO "`repo'"
global ZP_OUT "${ZP_REPO}/test/fixtures/colorvar_plegend_truth.json"

local work "`c(tmpdir)'dash_colorvar_plegend_probe"
capture mkdir "`work'"
global ZP_WORK "`work'"

quietly shell git -C "${ZP_REPO}" rev-parse HEAD > "${ZP_WORK}/git_head.txt"
global ZP_VERSION "`c(stata_version)'"
global ZP_BORN "`c(born_date)'"
global ZP_WHEN "`c(current_date)' `c(current_time)'"

* _zp_run key cmd: run `cmd' with its printed lines in a log; the rc in
* ZP_RC_<key>, the command in ZP_CMD_<key>; the graph exported to
* <key>.svg when it drew.
capture program drop _zp_run
program define _zp_run
    gettoken key 0 : 0
    quietly log using "${ZP_WORK}/`key'.log", text replace name(zpref)
    capture noisily `0'
    local rc = _rc
    display as text "{p_end}"
    quietly log close zpref
    global ZP_RC_`key' "`rc'"
    global ZP_CMD_`key' `"`0'"'
    if `rc' == 0 {
        capture graph describe zp1
        if _rc == 0 {
            quietly graph export "${ZP_WORK}/`key'.svg", replace
            graph drop zp1
        }
    }
    global ZP_KEYS "${ZP_KEYS} `key'"
end
global ZP_KEYS ""

sysuse auto, clear
set scheme s2color
local sc "twoway scatter mpg weight"
local nm "name(zp1, replace)"
local k5 "colorvar(rep78) colordiscrete coloruseplegend"

_zp_run K5   `sc', `k5' `nm'
_zp_run K6   `sc', colorvar(foreign) colordiscrete coloruseplegend `nm'
_zp_run X1   `sc', `k5' colorotherlabel("rest") `nm'
_zp_run C28  `sc', `k5' colorkeysrange `nm'
_zp_run M3   `sc', `k5' legend(off) `nm'
_zp_run M4   `sc', `k5' legend(rows(1)) `nm'
_zp_run Q0   twoway (scatter mpg weight, colorvar(price)) (lfit mpg weight), `nm'
_zp_run Q1   twoway (scatter mpg weight, colorvar(price)) (lfit mpg weight), legend(size(huge)) `nm'
_zp_run Q3   twoway (scatter mpg weight, `k5') (lfit mpg weight), legend(size(huge)) `nm'
_zp_run P12  twoway (scatter mpg weight, colorvar(price)) (lfit mpg weight), legend(rows(1)) `nm'
_zp_run ST   `sc', `k5' scheme(stcolor) `nm'
_zp_run K1   `sc', colorvar(rep78) colordiscrete `nm'
_zp_run R1   `sc', colorvar(rep78) colordiscrete colorkeysreverse `nm'
_zp_run D13r `sc', `k5' colorkeysreverse `nm'
_zp_run I5   `sc' if rep78==3, colorvar(rep78) colorlevels(3) `nm'
_zp_run I5m  `sc' if rep78==3, colorvar(rep78) colorlevels(3) colorvarminmax `nm'
_zp_run I3   `sc' if rep78==3, colorvar(rep78) colordiscrete colorlevels(2) `nm'

python:
import json, os, sys
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


work = G("ZP_WORK")
sys.path.insert(0, os.path.join(G("ZP_REPO"), "scripts"))
from svg_truth import svg_document  # noqa: E402

r3 = lambda v: None if v is None else round(v, 2)


def log_lines(key):
    p = os.path.join(work, key + ".log")
    with open(p, encoding="utf-8", errors="replace") as fh:
        lines = [ln.rstrip() for ln in fh
                 if ln.strip() and not ln.lstrip().startswith((".", "> "))
                 and "log:" not in ln and "log type:" not in ln
                 and "opened on:" not in ln and "closed on:" not in ln
                 and "name:" not in ln and not ln.startswith("---")
                 and ln.strip() != "{p_end}"]
    os.remove(p)
    return lines


def summary(doc):
    pr = doc["plotregion"] or {}
    left, top = pr.get("left", 0), pr.get("top", 0)
    right, bottom = pr.get("right", 0), pr.get("bottom", 0)

    def inside(x, y):
        return left - 0.5 <= x <= right + 0.5 and top - 0.5 <= y <= bottom + 0.5

    texts = [{"text": t["text"], "x": r3(t["x"]), "y": r3(t["y"]),
              "size": r3(t["size"]), "rotate": t["rotate"],
              "anchor": t["anchor"]} for t in doc["texts"]]
    rects = [{"x": r3(r["x"]), "y": r3(r["y"]), "w": r3(r["w"]),
              "h": r3(r["h"]), "fill": r["fill"], "stroke": r["stroke"]}
             for r in doc["rects"] if r["x"] is not None]
    outer = [{"cx": r3(c["cx"]), "cy": r3(c["cy"]), "r": r3(c["r"]),
              "fill": c["fill"]} for c in doc["circles"]
             if c["cx"] is not None and not inside(c["cx"], c["cy"])]
    fills = {}
    for c in doc["circles"]:
        if c["cx"] is not None and inside(c["cx"], c["cy"]) \
                and c["fill"] not in (None, "none"):
            fills[c["fill"]] = fills.get(c["fill"], 0) + 1
    # The key: what is drawn right of the plot region, top to bottom.
    ktexts = sorted((t for t in texts if t["x"] is not None
                     and t["x"] > right + 1 and not t["rotate"]),
                    key=lambda t: (t["y"], t["x"]))
    ksw = []
    for c in outer:
        if c["cx"] > right + 1:
            ksw.append({"kind": "marker", "fill": c["fill"],
                        "x": c["cx"], "y": c["cy"]})
    for r in rects:
        if r["x"] > right + 1 and r["fill"] not in (None, "none") \
                and r["w"] and r["h"] and r["w"] < 200 and r["h"] < 200:
            ksw.append({"kind": "bar", "fill": r["fill"],
                        "x": r["x"] + r["w"] / 2, "y": r["y"] + r["h"] / 2})
    ksw.sort(key=lambda s: (s["y"], s["x"]))
    box = None
    if ktexts:
        for r in rects:
            if r["w"] and r["h"] and r["x"] > right and all(
                    r["x"] <= t["x"] <= r["x"] + r["w"]
                    and r["y"] <= t["y"] <= r["y"] + r["h"] for t in ktexts):
                box = r
    key = {"texts": [t["text"] for t in ktexts],
           "sizes": [t["size"] for t in ktexts],
           "text_pos": [[t["x"], t["y"]] for t in ktexts],
           "swatches": [s["kind"] for s in ksw],
           "fills": [s["fill"] for s in ksw],
           "box": box}
    return {"plot": {"left": r3(left), "top": r3(top), "right": r3(right),
                     "bottom": r3(bottom)},
            "texts": texts, "rects": rects, "outer_circles": outer,
            "marker_fills": fills, "key": key}


out = {"probes": {}}
for key in G("ZP_KEYS").split():
    rec = {"rc": int(G("ZP_RC_" + key)), "lines": log_lines(key),
           "command": G("ZP_CMD_" + key).replace(", name(zp1, replace)", "")
                                        .replace(" name(zp1, replace)", "")}
    svg = os.path.join(work, key + ".svg")
    if os.path.exists(svg):
        rec.update(summary(svg_document(svg)))
        os.remove(svg)
    out["probes"][key] = rec
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZP_VERSION"), "born_date": G("ZP_BORN"),
                "dash_commit": commit, "extracted": G("ZP_WHEN"),
                "source": "scripts/extract_colorvar_plegend_truth.do"}
with open(G("ZP_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZP_OUT"))
end
