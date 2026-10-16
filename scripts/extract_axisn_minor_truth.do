*! extract_axisn_minor_truth.do -- WP-31 section 35 (GAPS3 D1b): measure
*! twoway's minor labels and ticks on a far-side axis 2 with and without
*! the rows a filter move keeps (if foreign == 1), and on axis 3 -- which
*! labels each column holds, and the scale of each axis.  twoway only:
*! the output is the same before and after dash changes.
*!
*! Output: test/fixtures/axisn_minor_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_axisn_minor_truth.do
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
    display as error "extract_axisn_minor_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_axisn_minor_truth.do: `_an_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global AN_REPO "`repo'"
global AN_OUT "${AN_REPO}/test/fixtures/axisn_minor_truth.json"

local work "`c(tmpdir)'dash_axisn_minor_probe"
capture mkdir "`work'"
global AN_WORK "`work'"

if `"`c(python_exec)'"' == "" {
    display as error "extract_axisn_minor_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

quietly shell git -C "${AN_REPO}" rev-parse HEAD > "${AN_WORK}/git_head.txt"
global AN_VERSION "`c(stata_version)'"
global AN_BORN "`c(born_date)'"
global AN_WHEN "`c(current_date)' `c(current_time)'"
global AN_KEYS ""

* _an_probe key twoway-command: as extract_axes_n_truth.do's _an_probe:
* rc, log, SVG, each axis's scale (AN_SY<n>_<key>, AN_SX<n>_<key>) and its
* title text (AN_TY<n>_<key>, AN_TX<n>_<key>).
capture program drop _an_probe
program define _an_probe
    gettoken key cmd : 0
    quietly sysuse auto, clear
    capture graph drop _all
    quietly log using "${AN_WORK}/`key'.log", text replace name(amp) nomsg
    capture noisily twoway `cmd' name(g, replace)
    local rc = _rc
    quietly log close amp
    global AN_RC_`key' `rc'
    global AN_KEYS "${AN_KEYS} `key'"
    forvalues n = 1/9 {
        global AN_SY`n'_`key' ""
        global AN_SX`n'_`key' ""
    }
    if !`rc' {
        quietly graph export "${AN_WORK}/`key'.svg", replace
        forvalues n = 1/9 {
            if "`.g.yaxis`n'.isa'" != "" {
                global AN_SY`n'_`key' "`.g.yaxis`n'.plotregion.yscale.curmin' `.g.yaxis`n'.plotregion.yscale.curmax'"
            }
            if "`.g.xaxis`n'.isa'" != "" {
                global AN_SX`n'_`key' "`.g.xaxis`n'.plotregion.xscale.curmin' `.g.xaxis`n'.plotregion.xscale.curmax'"
            }
        }
    }
    display as text "AM `key': rc `rc' y1 ${AN_SY1_`key'} y2 ${AN_SY2_`key'} x1 ${AN_SX1_`key'} x2 ${AN_SX2_`key'}"
end

* Minor labels on the far-side axis 2, all rows and under the move's if.
_an_probe m2_full (scatter mpg weight) (scatter price weight, yaxis(2)), ymlabel(##2, axis(2)) legend(off)
_an_probe m2_foreign (scatter mpg weight) (scatter price weight, yaxis(2)) if foreign == 1, ymlabel(##2, axis(2)) legend(off)
_an_probe m2_x2full (scatter mpg weight) (scatter mpg price, xaxis(2)), xmlabel(##2, axis(2)) legend(off)
_an_probe m2_x2foreign (scatter mpg weight) (scatter mpg price, xaxis(2)) if foreign == 1, xmlabel(##2, axis(2)) legend(off)

* Axis 3: minor labels and ticks.
_an_probe m3_mlabel (scatter mpg weight) (scatter price weight, yaxis(2)) (scatter length weight, yaxis(3)), ymlabel(##2, axis(3)) legend(off)
_an_probe m3_mlist (scatter mpg weight) (scatter price weight, yaxis(2)) (scatter length weight, yaxis(3)), ymlabel(165 215, axis(3)) legend(off)
_an_probe m3_mtick (scatter mpg weight) (scatter price weight, yaxis(2)) (scatter length weight, yaxis(3)), ymtick(##2, axis(3)) legend(off)
_an_probe m3_x3 (scatter mpg weight) (scatter mpg price, xaxis(2)) (scatter mpg length, xaxis(3)), xmlabel(##2, axis(3)) legend(off)
_an_probe m3_tmlabel (scatter mpg weight) (scatter mpg price, xaxis(2)), tmlabel(##2, axis(2)) legend(off)
_an_probe m3_unused scatter mpg weight, ymlabel(##2, axis(3))

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


out = {"m2": {}, "m3": {}}
keys = G("AN_KEYS").split()
for key in keys:
    group, name = key.split("_", 1)
    rc = int(G("AN_RC_" + key))
    r = {"rc": rc, "message": message(key) if rc else ""}
    if not rc:
        r["yscales"] = {str(n): pair(G("AN_SY%d_%s" % (n, key)))
                        for n in range(1, 10) if pair(G("AN_SY%d_%s" % (n, key)))}
        r["xscales"] = {str(n): pair(G("AN_SX%d_%s" % (n, key)))
                        for n in range(1, 10) if pair(G("AN_SX%d_%s" % (n, key)))}
        _doc = svg_document(os.path.join(work, key + ".svg"))
        r["axes"] = axes(_doc)
        r["columns"] = {sd: [[c, t] for c, t in cols] for sd, cols in columns(_doc).items()}
    out[group][name] = r
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("AN_VERSION"), "born_date": G("AN_BORN"),
                "dash_commit": commit, "extracted": G("AN_WHEN"),
                "source": "scripts/extract_axisn_minor_truth.do"}
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
