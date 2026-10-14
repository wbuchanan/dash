*! extract_axes_n_truth.do -- WP-31 section 09 (GAPS3 C10c): measure how
*! twoway draws axes three to nine -- the side and stacking order of every
*! y and x axis when a graph uses two, three or four of them, which axes
*! share one scale when a layer names several (the plot regions and their
*! axis numbers, each axis's scale), where axis(3) sub-options land, the
*! bounds of yaxis()/xaxis() and the refusal of an option for an axis no
*! layer uses.  twoway only: the output is the same before and after dash
*! changes.
*!
*! Output: test/fixtures/axes_n_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_axes_n_truth.do
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
mata: st_local("_an_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_an_bad' {
    display as error "extract_axes_n_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _an_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_an_rc' | _rc {
    local _an_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_axes_n_truth.do: `_an_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global AN_REPO "`repo'"
global AN_OUT "${AN_REPO}/test/fixtures/axes_n_truth.json"

local work "`c(tmpdir)'dash_axes_n_probe"
capture mkdir "`work'"
global AN_WORK "`work'"

if `"`c(python_exec)'"' == "" {
    display as error "extract_axes_n_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

quietly shell git -C "${AN_REPO}" rev-parse HEAD > "${AN_WORK}/git_head.txt"
global AN_VERSION "`c(stata_version)'"
global AN_BORN "`c(born_date)'"
global AN_WHEN "`c(current_date)' `c(current_time)'"
global AN_KEYS ""

* _an_probe key twoway-command: draw the command on a fresh auto, record
* its rc (AN_RC_<key>) and output (<work>/<key>.log, for the error line)
* and, when it drew, export <work>/<key>.svg and record each plot region's
* y and x axis numbers (AN_YD_<key>, AN_XD_<key>, "|"-separated) and each
* axis's scale (AN_SY<n>_<key>, AN_SX<n>_<key>: "curmin curmax").  The
* command always holds a comma.
capture program drop _an_probe
program define _an_probe
    gettoken key cmd : 0
    quietly sysuse auto, clear
    capture graph drop _all
    quietly log using "${AN_WORK}/`key'.log", text replace name(anp) nomsg
    capture noisily twoway `cmd' name(g, replace)
    local rc = _rc
    quietly log close anp
    global AN_RC_`key' `rc'
    global AN_KEYS "${AN_KEYS} `key'"
    global AN_YD_`key' ""
    global AN_XD_`key' ""
    forvalues n = 1/9 {
        global AN_SY`n'_`key' ""
        global AN_SX`n'_`key' ""
    }
    if !`rc' {
        quietly graph export "${AN_WORK}/`key'.svg", replace
        local yd ""
        local xd ""
        forvalues i = 1/9 {
            if "`.g.plotregion`i'.isa'" != "" {
                local yd `"`yd' `.g.plotregion`i'.yaxis_dexes'|"'
                local xd `"`xd' `.g.plotregion`i'.xaxis_dexes'|"'
            }
        }
        global AN_YD_`key' `"`yd'"'
        global AN_XD_`key' `"`xd'"'
        forvalues n = 1/9 {
            if "`.g.yaxis`n'.isa'" != "" {
                global AN_SY`n'_`key' "`.g.yaxis`n'.plotregion.yscale.curmin' `.g.yaxis`n'.plotregion.yscale.curmax'"
            }
            if "`.g.xaxis`n'.isa'" != "" {
                global AN_SX`n'_`key' "`.g.xaxis`n'.plotregion.xscale.curmin' `.g.xaxis`n'.plotregion.xscale.curmax'"
            }
        }
    }
    display as text "AN `key': rc `rc' y ${AN_YD_`key'} x ${AN_XD_`key'}"
end

* Bounds of yaxis()/xaxis().
_an_probe bounds_yaxis0 scatter mpg weight, yaxis(0)
_an_probe bounds_yaxis9 scatter mpg weight, yaxis(9)
_an_probe bounds_yaxis10 scatter mpg weight, yaxis(10)
_an_probe bounds_yaxis_frac scatter mpg weight, yaxis(2.5)
_an_probe bounds_xaxis10 scatter mpg weight, xaxis(10)

* Sides: every axis titled AX<n> (y) or BX<n> (x) so its column is found
* in the SVG by its title.
_an_probe sides_y2 (scatter mpg weight, yaxis(1)) (scatter price weight, yaxis(2)), ytitle(AX1, axis(1)) ytitle(AX2, axis(2))
_an_probe sides_y3 (scatter mpg weight, yaxis(1)) (scatter price weight, yaxis(2)) (scatter length weight, yaxis(3)), ytitle(AX1, axis(1)) ytitle(AX2, axis(2)) ytitle(AX3, axis(3))
_an_probe sides_y4 (scatter mpg weight, yaxis(1)) (scatter price weight, yaxis(2)) (scatter length weight, yaxis(3)) (scatter gear_ratio weight, yaxis(4)), ytitle(AX1, axis(1)) ytitle(AX2, axis(2)) ytitle(AX3, axis(3)) ytitle(AX4, axis(4))
_an_probe sides_y13 (scatter mpg weight, yaxis(1)) (scatter length weight, yaxis(3)), ytitle(AX1, axis(1)) ytitle(AX3, axis(3))
_an_probe sides_y23_no1 (scatter mpg weight, yaxis(2)) (scatter price weight, yaxis(3)), ytitle(AX2, axis(2)) ytitle(AX3, axis(3))
_an_probe sides_y3_lone scatter mpg weight, yaxis(3) ytitle(AX3, axis(3))
_an_probe sides_x3 (scatter mpg weight, xaxis(1)) (scatter mpg price, xaxis(2)) (scatter mpg length, xaxis(3)), xtitle(BX1, axis(1)) xtitle(BX2, axis(2)) xtitle(BX3, axis(3))

* Scales shared when a layer names several axes.
_an_probe ties_13 (scatter mpg weight, yaxis(1 3)) (scatter price weight, yaxis(3)) (scatter length weight, yaxis(2)),
_an_probe ties_23 (scatter mpg weight) (scatter price weight, yaxis(2 3)) (scatter length weight, yaxis(4)),
_an_probe ties_x13 (scatter mpg weight, xaxis(1 3)) (scatter mpg price, xaxis(3)) (scatter mpg length, xaxis(2)),

* axis(3) sub-options on the three-axis graph.
local three (scatter mpg weight, yaxis(1)) (scatter price weight, yaxis(2)) (scatter length weight, yaxis(3))
_an_probe routed_base `three', ytitle(AX3, axis(3))
_an_probe routed_label3 `three', ylabel(150(20)230, axis(3)) ytitle(AX3, axis(3))
_an_probe routed_title3 `three', ytitle("Len", axis(3))
_an_probe routed_scale3 `three', yscale(log axis(3)) ylabel(150(20)230, axis(3)) ytitle(AX3, axis(3))
_an_probe routed_line3 `three', yline(200, axis(3)) ytitle(AX3, axis(3))
_an_probe routed_tick3 `three', ytick(165 215, axis(3)) ytitle(AX3, axis(3))

* An option for an axis no layer uses.
_an_probe refusals_axis3_unused scatter mpg weight, ylabel(1 2, axis(3))

python:
import json, math, os, sys
from sfi import Macro

G = Macro.getGlobal
sys.path.insert(0, os.path.join(G("AN_REPO"), "scripts"))
from svg_truth import svg_document, label_value  # noqa: E402

work = G("AN_WORK")
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


def axes_of(doc, letter, keep_at=False):
    """[{axis, side, order, title, labels: [[text, px]]}] for every titled
    axis (AX<n> for y, BX<n> for x) or, for a graph without such titles,
    every label column: the column of tick labels next to each title, on
    the side of the plot region it sits, ordered from the region outward
    (order 1 is innermost)."""
    pr = doc["plotregion"]
    rot = ((lambda t: t.get("rotate") is not None) if letter == "y"
           else (lambda t: t.get("rotate") is None))
    pos = "x" if letter == "y" else "y"
    along = "y" if letter == "y" else "x"
    texts = [t for t in doc["texts"] if rot(t)]
    if letter == "y":
        texts = [t for t in texts if t["x"] < pr["left"] or t["x"] > pr["right"]]
    else:
        texts = [t for t in texts if (t["y"] > pr["bottom"] or t["y"] < pr["top"])
                 and pr["left"] - 5 <= t["x"] <= pr["right"] + 5]
    cols = {}
    for t in texts:
        cols.setdefault(round(t[pos], 1), []).append(t)
    out = []
    tag = "AX" if letter == "y" else "BX"
    for c, ts in cols.items():
        titles = [t["text"] for t in ts if t["text"].startswith(tag)]
        if not titles:
            continue
        n = int(titles[0][2:])
        if letter == "y":
            side = "left" if c < pr["left"] else "right"
        else:
            side = "below" if c > pr["bottom"] else "above"
        out.append({"axis": n, "side": side, "title_at": c})
    for a in out:
        # The label column of an axis is the nearest column between its
        # title and the plot region.
        edge = {"left": pr["left"], "right": pr["right"],
                "below": pr["bottom"], "above": pr["top"]}[a["side"]]
        lo, hi = sorted((a["title_at"], edge))
        cand = [c for c, ts in cols.items() if lo < c < hi
                and not any(t["text"].startswith(tag) for t in ts)]
        if cand:
            col = min(cand, key=lambda c: abs(c - a["title_at"]))
            a["labels"] = [[t["text"], t[along]] for t in
                           sorted(cols[col], key=lambda t: t[along])]
            a["label_at"] = col
        else:
            a["labels"] = []
            a["label_at"] = None
        a["distance"] = abs(a["title_at"] - edge)
    for side in ("left", "right", "below", "above"):
        on = sorted([a for a in out if a["side"] == side],
                    key=lambda a: a["distance"])
        for i, a in enumerate(on, 1):
            a["order"] = i
    for a in out:
        a.pop("title_at")
        a.pop("distance")
        if not keep_at:
            a.pop("label_at")
    return sorted(out, key=lambda a: a["axis"])


def value_at(labels, px, log=False):
    """The value at pixel *px* of an axis whose labels are [[text, px]]."""
    pts = [(p, label_value(t)) for t, p in labels if label_value(t) is not None]
    if len(pts) < 2:
        return None
    (p0, v0), (p1, v1) = pts[0], pts[-1]
    f = (lambda v: math.log(v)) if log else (lambda v: v)
    g = (lambda v: math.exp(v)) if log else (lambda v: v)
    return round(g(f(v0) + (px - p0) * (f(v1) - f(v0)) / (p1 - p0)), 3)


def rec(key):
    rc = int(G("AN_RC_" + key))
    r = {"rc": rc, "message": message(key) if rc else ""}
    if rc:
        return r, None
    r["yaxis_dexes"] = [x.strip() for x in G("AN_YD_" + key).split("|") if x.strip()]
    r["xaxis_dexes"] = [x.strip() for x in G("AN_XD_" + key).split("|") if x.strip()]
    r["yscales"] = {str(n): pair(G("AN_SY%d_%s" % (n, key))) for n in range(1, 10)
                    if pair(G("AN_SY%d_%s" % (n, key)))}
    r["xscales"] = {str(n): pair(G("AN_SX%d_%s" % (n, key))) for n in range(1, 10)
                    if pair(G("AN_SX%d_%s" % (n, key)))}
    doc = svg_document(os.path.join(work, key + ".svg"))
    return r, doc


out = {"bounds": {}, "sides": {}, "ties": {}, "routed": {}, "refusals": {}}
full = {}
keys = G("AN_KEYS").split()
for key in keys:
    group, name = key.split("_", 1)
    r, doc = rec(key)
    if doc is not None:
        if group == "sides":
            r["axes"] = axes_of(doc, "x" if name.startswith("x") else "y")
        elif group == "routed":
            axes = axes_of(doc, "y", keep_at=True)
            ax3 = [a for a in axes if a["axis"] == 3]
            r["axis3_labels"] = [t for t, _ in ax3[0]["labels"]] if ax3 else []
            r["axis3_side"] = ax3[0]["side"] if ax3 else ""
            if ax3 and len(ax3[0]["labels"]) > 2:
                px = [p for _, p in ax3[0]["labels"]]
                gaps = [b - a for a, b in zip(px, px[1:])]
                r["axis3_labels_evenly_spaced"] = max(gaps) - min(gaps) < 1.0
            if name == "title3":
                # No AX3 title: the title column outermost on the left.
                pr = doc["plotregion"]
                left = [t for t in doc["texts"] if t.get("rotate") is not None
                        and t["x"] < pr["left"]]
                r["axis3_title"] = min(left, key=lambda t: t["x"])["text"] if left else ""
            if name in ("base", "line3") and ax3:
                # Full-width lines inside the plot region; the line's are
                # those the base graph (no yline) does not draw.
                pr = doc["plotregion"]
                ys = sorted({round(h["y1"], 1) for h in doc["hlines"]
                             if h["x1"] <= pr["left"] + 5 and h["x2"] >= pr["right"] - 5
                             and pr["top"] + 2 < h["y1"] < pr["bottom"] - 2})
                full[name] = (ys, ax3[0]["labels"])
            if name == "tick3" and ax3:
                # Short tick marks in axis 3's band (between its title and
                # axis 2's title), read on axis 3's label scale.
                ax2 = [a for a in axes if a["axis"] == 2]
                lo = ax3[0]["label_at"]
                hi = (lo + ax2[0]["label_at"]) / 2 if ax2 else lo + 150
                ys = sorted({round(h["y1"], 1) for h in doc["hlines"]
                             if abs(h["x2"] - h["x1"]) < 100
                             and lo < min(h["x1"], h["x2"]) and max(h["x1"], h["x2"]) < hi})
                r["axis3_tick_values"] = [value_at(ax3[0]["labels"], y) for y in ys]
            for a in axes:
                a.pop("label_at", None)
    out[group][name] = r
if "base" in full and "line3" in full:
    extra = [y for y in full["line3"][0] if y not in full["base"][0]]
    out["routed"]["line3"]["line_values"] = [value_at(full["line3"][1], y) for y in extra]
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("AN_VERSION"), "born_date": G("AN_BORN"),
                "dash_commit": commit, "extracted": G("AN_WHEN"),
                "source": "scripts/extract_axes_n_truth.do"}
with open(G("AN_OUT"), "w", encoding="utf-8") as fh:
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
print("wrote", G("AN_OUT"))
end
