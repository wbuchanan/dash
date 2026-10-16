*! extract_axis2_move_truth.do -- WP-31 section 35 (GAPS3 D9): measure
*! twoway's second axes under the rows a filter move keeps (the graph drawn
*! with and without `if foreign == 1', each axis's scale and labels), the
*! side of each axis when no layer uses axis 1, and the axis titles of a
*! horizontal layer on yaxis(2).  twoway only: the output is the same
*! before and after dash changes.
*!
*! Output: test/fixtures/axis2_move_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_axis2_move_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200
set scheme s2color

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_am_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_am_bad' {
    display as error "extract_axis2_move_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _am_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_am_rc' | _rc {
    local _am_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_axis2_move_truth.do: `_am_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global AM_REPO "`repo'"
global AM_OUT "${AM_REPO}/test/fixtures/axis2_move_truth.json"

local work "`c(tmpdir)'dash_axis2_move_probe"
capture mkdir "`work'"
global AM_WORK "`work'"

if `"`c(python_exec)'"' == "" {
    display as error "extract_axis2_move_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

quietly shell git -C "${AM_REPO}" rev-parse HEAD > "${AM_WORK}/git_head.txt"
global AM_VERSION "`c(stata_version)'"
global AM_BORN "`c(born_date)'"
global AM_WHEN "`c(current_date)' `c(current_time)'"
global AM_KEYS ""

* _am_probe key twoway-command: as extract_axes_n_truth.do's _an_probe:
* rc, log, SVG, each axis's scale (AM_SY<n>_<key>, AM_SX<n>_<key>) and its
* title text (AM_TY<n>_<key>, AM_TX<n>_<key>).
capture program drop _am_probe
program define _am_probe
    gettoken key cmd : 0
    quietly sysuse auto, clear
    capture graph drop _all
    quietly log using "${AM_WORK}/`key'.log", text replace name(amp) nomsg
    capture noisily twoway `cmd' name(g, replace)
    local rc = _rc
    quietly log close amp
    global AM_RC_`key' `rc'
    global AM_KEYS "${AM_KEYS} `key'"
    forvalues n = 1/9 {
        global AM_SY`n'_`key' ""
        global AM_SX`n'_`key' ""
    }
    if !`rc' {
        quietly graph export "${AM_WORK}/`key'.svg", replace
        forvalues n = 1/9 {
            if "`.g.yaxis`n'.isa'" != "" {
                global AM_SY`n'_`key' "`.g.yaxis`n'.plotregion.yscale.curmin' `.g.yaxis`n'.plotregion.yscale.curmax'"
            }
            if "`.g.xaxis`n'.isa'" != "" {
                global AM_SX`n'_`key' "`.g.xaxis`n'.plotregion.xscale.curmin' `.g.xaxis`n'.plotregion.xscale.curmax'"
            }
        }
    }
    display as text "AM `key': rc `rc' y1 ${AM_SY1_`key'} y2 ${AM_SY2_`key'} x1 ${AM_SX1_`key'} x2 ${AM_SX2_`key'}"
end

* A move: the graph under the rows the dropdown at Foreign keeps.
_am_probe move_full (scatter mpg weight) (line price weight, yaxis(2) sort),
_am_probe move_foreign (scatter mpg weight) (line price weight, yaxis(2) sort) if foreign == 1,
_am_probe move_x2full (scatter mpg weight) (scatter mpg price, xaxis(2)),
_am_probe move_x2foreign (scatter mpg weight) (scatter mpg price, xaxis(2)) if foreign == 1,
_am_probe move_x2range (scatter mpg weight) (scatter mpg price, xaxis(2)) if weight >= 2000 & weight <= 3000,

* No layer on axis 1: which axis is drawn on which side (titled AX<n> /
* BX<n> so the columns are found by their titles).
_am_probe first_y23 (scatter mpg weight, yaxis(2)) (scatter price weight, yaxis(3)), ytitle(AX2, axis(2)) ytitle(AX3, axis(3))
_am_probe first_y32 (scatter price weight, yaxis(3)) (scatter mpg weight, yaxis(2)), ytitle(AX3, axis(3)) ytitle(AX2, axis(2))
_am_probe first_y2opts (scatter mpg weight, yaxis(2)) (scatter price weight, yaxis(3)), ylabel(0(10)50, axis(2)) ytitle(AX2, axis(2)) ytitle(AX3, axis(3))
_am_probe first_x23 (scatter mpg weight, xaxis(2)) (scatter mpg price, xaxis(3)), xtitle(BX2, axis(2)) xtitle(BX3, axis(3))
_am_probe first_y2lone scatter mpg weight, yaxis(2) ytitle(AX2, axis(2))
_am_probe first_y12 (scatter price weight, yaxis(2)) (scatter mpg weight, yaxis(1)), ytitle(AX1, axis(1)) ytitle(AX2, axis(2))

* WP-31 D9b: three or four y axes with the first layer on axis 1 -- which
* axis is drawn where, by its title.
_am_probe first_y123 (scatter mpg weight) (scatter price weight, yaxis(2)) (scatter trunk weight, yaxis(3)), ytitle(AX1) ytitle(AX2, axis(2)) ytitle(AX3, axis(3))
_am_probe first_y132 (scatter mpg weight) (scatter price weight, yaxis(3)) (scatter trunk weight, yaxis(2)), ytitle(AX1) ytitle(AX3, axis(3)) ytitle(AX2, axis(2))
_am_probe first_y1432 (scatter mpg weight) (scatter price weight, yaxis(4)) (scatter trunk weight, yaxis(3)) (scatter turn weight, yaxis(2)), ytitle(AX1) ytitle(AX4, axis(4)) ytitle(AX3, axis(3)) ytitle(AX2, axis(2))
_am_probe first_y1342 (scatter mpg weight) (scatter price weight, yaxis(3)) (scatter trunk weight, yaxis(4)) (scatter turn weight, yaxis(2)), ytitle(AX1) ytitle(AX3, axis(3)) ytitle(AX4, axis(4)) ytitle(AX2, axis(2))
_am_probe first_y213 (scatter price weight, yaxis(2)) (scatter mpg weight) (scatter trunk weight, yaxis(3)), ytitle(AX2, axis(2)) ytitle(AX1) ytitle(AX3, axis(3))
_am_probe first_y243 (scatter mpg weight, yaxis(2)) (scatter price weight, yaxis(4)) (scatter trunk weight, yaxis(3)), ytitle(AX2, axis(2)) ytitle(AX4, axis(4)) ytitle(AX3, axis(3))

* WP-31 D9b: an added text(..., yaxis(#)) on a renumbered axis -- where
* its marker text TXT lands beside the left axis's labels.
_am_probe text_y23 (scatter mpg weight, yaxis(2)) (scatter price weight, yaxis(3)), text(30 3000 "TXT", yaxis(2)) ytitle(AX2, axis(2)) ytitle(AX3, axis(3))
_am_probe text_y23b (scatter mpg weight, yaxis(2)) (scatter price weight, yaxis(3)), text(10000 3000 "TXT", yaxis(3)) ytitle(AX2, axis(2)) ytitle(AX3, axis(3))

* horizontal with yaxis(2): the default axis titles.
_am_probe horizontal_y2 bar mpg weight, horizontal yaxis(2)
_am_probe horizontal_ctrl bar mpg weight, horizontal
_am_probe horizontal_scatter scatter mpg weight, horizontal yaxis(2)
_am_probe horizontal_two (scatter weight mpg) (bar mpg weight, horizontal yaxis(2)),
_am_probe horizontal_spike (scatter weight mpg) (spike mpg weight, horizontal yaxis(2)),

python:
import json, math, os, sys
from sfi import Macro

G = Macro.getGlobal
sys.path.insert(0, os.path.join(G("AM_REPO"), "scripts"))
from svg_truth import svg_document, label_value  # noqa: E402

work = G("AM_WORK")
_HEAD = ("name:", "log:", "log type:", "opened on:", "closed on:")


def message(key):
    try:
        with open(os.path.join(work, key + ".log"), encoding="utf-8") as fh:
            lines = [ln.strip() for ln in fh.read().splitlines()]
    except OSError:
        return ""
    for ln in lines:
        if not ln or ln.startswith(_HEAD) or set(ln) <= set("-"):
            continue
        return ln
    return ""


def pair(v):
    w = (v or "").split()
    return [float(x) for x in w] if len(w) == 2 else None


def columns(doc):
    """{side: [[column position, [texts in order along the axis]]]} for the
    text outside the plot region, ordered from the region outward; y
    columns are rotated texts' x, x rows unrotated texts' y."""
    pr = doc["plotregion"]
    out = {"left": {}, "right": {}, "below": {}, "above": {}}
    for t in doc["texts"]:
        if t.get("rotate") is not None or label_value(t["text"]) is None:
            pass
        x, y = t["x"], t["y"]
        if pr["top"] - 2 <= y <= pr["bottom"] + 2 and x < pr["left"]:
            side, at, along = "left", x, y
        elif pr["top"] - 2 <= y <= pr["bottom"] + 2 and x > pr["right"]:
            side, at, along = "right", x, y
        elif pr["left"] - 40 <= x <= pr["right"] + 40 and y > pr["bottom"]:
            side, at, along = "below", y, x
        elif pr["left"] - 40 <= x <= pr["right"] + 40 and y < pr["top"]:
            side, at, along = "above", y, x
        else:
            continue
        out[side].setdefault(round(at), []).append((along, t["text"]))
    res = {}
    for side, cols in out.items():
        edge = {"left": pr["left"], "right": pr["right"],
                "below": pr["bottom"], "above": pr["top"]}[side]
        res[side] = [[c, [s for _, s in sorted(ts)]] for c, ts in
                     sorted(cols.items(), key=lambda kv: abs(kv[0] - edge))]
    return res


def axes(doc):
    """[{side, order, labels, title}]: each side's columns paired as
    (labels, title) from the region outward; a column of numbers is an
    axis's labels, the next column of words its title."""
    out = []
    for side, cols in columns(doc).items():
        order = 0
        pending = None
        for _, texts in cols:
            numeric = all(label_value(s) is not None for s in texts)
            if numeric:
                if pending is not None:
                    out.append(pending)
                order += 1
                pending = {"side": side, "order": order, "labels": texts,
                           "title": ""}
            else:
                if pending is None:
                    order += 1
                    pending = {"side": side, "order": order, "labels": [],
                               "title": ""}
                pending["title"] = " ".join(texts)
                out.append(pending)
                pending = None
        if pending is not None:
            out.append(pending)
    return out


out = {"move": {}, "first_used": {}, "horizontal": {}, "text": {}}
keys = G("AM_KEYS").split()
for key in keys:
    group, name = key.split("_", 1)
    group = {"first": "first_used"}.get(group, group)
    rc = int(G("AM_RC_" + key))
    r = {"rc": rc, "message": message(key) if rc else ""}
    if not rc:
        r["yscales"] = {str(n): pair(G("AM_SY%d_%s" % (n, key)))
                        for n in range(1, 10) if pair(G("AM_SY%d_%s" % (n, key)))}
        r["xscales"] = {str(n): pair(G("AM_SX%d_%s" % (n, key)))
                        for n in range(1, 10) if pair(G("AM_SX%d_%s" % (n, key)))}
        _doc = svg_document(os.path.join(work, key + ".svg"))
        r["axes"] = axes(_doc)
        if group == "text":
            # WP-31 D9b: the added text's place and every text's, so a test
            # reads which axis's scale placed it.
            r["texts"] = [{"text": t["text"], "x": t["x"], "y": t["y"]}
                          for t in _doc["texts"]]
            r["plotregion"] = dict(_doc["plotregion"])
    out[group][name] = r
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("AM_VERSION"), "born_date": G("AM_BORN"),
                "dash_commit": commit, "extracted": G("AM_WHEN"),
                "source": "scripts/extract_axis2_move_truth.do"}
with open(G("AM_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
for k in keys:
    for ext in (".log", ".svg"):
        try:
            os.remove(os.path.join(work, k + ext))
        except OSError:
            pass
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("AM_OUT"))
end
