*! extract_axisn_alt_truth.do -- WP-31 section 35 (GAPS3 D6b): measure
*! twoway's alternate on a label option of axis 2 and axis 3 -- which
*! columns (rows, for x) the labels take, and in which order -- beside
*! axis 1's own.  twoway only: the output is the same before and after
*! dash changes.
*!
*! Output: test/fixtures/axisn_alt_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_axisn_alt_truth.do
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
mata: st_local("_aa_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_aa_bad' {
    display as error "extract_axisn_alt_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _aa_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_aa_rc' | _rc {
    local _aa_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_axisn_alt_truth.do: `_aa_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global AA_REPO "`repo'"
global AA_OUT "${AA_REPO}/test/fixtures/axisn_alt_truth.json"

local work "`c(tmpdir)'dash_axisn_alt_probe"
capture mkdir "`work'"
global AA_WORK "`work'"


quietly shell git -C "${AA_REPO}" rev-parse HEAD > "${AA_WORK}/git_head.txt"
global AA_VERSION "`c(stata_version)'"
global AA_BORN "`c(born_date)'"
global AA_WHEN "`c(current_date)' `c(current_time)'"
global AA_KEYS ""

* _aa_probe key twoway-command: as extract_axes_n_truth.do's _an_probe:
* rc, log, SVG, each axis's scale (AA_SY<n>_<key>, AA_SX<n>_<key>) and its
* title text (AA_TY<n>_<key>, AA_TX<n>_<key>).
capture program drop _aa_probe
program define _aa_probe
    gettoken key cmd : 0
    quietly sysuse auto, clear
    capture graph drop _all
    quietly log using "${AA_WORK}/`key'.log", text replace name(amp) nomsg
    capture noisily twoway `cmd' name(g, replace)
    local rc = _rc
    quietly log close amp
    global AA_RC_`key' `rc'
    global AA_KEYS "${AA_KEYS} `key'"
    forvalues n = 1/9 {
        global AA_SY`n'_`key' ""
        global AA_SX`n'_`key' ""
    }
    if !`rc' {
        quietly graph export "${AA_WORK}/`key'.svg", replace
        forvalues n = 1/9 {
            if "`.g.yaxis`n'.isa'" != "" {
                global AA_SY`n'_`key' "`.g.yaxis`n'.plotregion.yscale.curmin' `.g.yaxis`n'.plotregion.yscale.curmax'"
            }
            if "`.g.xaxis`n'.isa'" != "" {
                global AA_SX`n'_`key' "`.g.xaxis`n'.plotregion.xscale.curmin' `.g.xaxis`n'.plotregion.xscale.curmax'"
            }
        }
    }
    display as text "AM `key': rc `rc' y1 ${AA_SY1_`key'} y2 ${AA_SY2_`key'} x1 ${AA_SX1_`key'} x2 ${AA_SX2_`key'}"
end

* alternate on axis 2 and axis 3 (legend off: no text but the axes').
_aa_probe y_y2alt (scatter mpg weight) (scatter price weight, yaxis(2)), ylabel(, axis(2) alternate) legend(off)
_aa_probe y_y2gap (scatter mpg weight) (scatter price weight, yaxis(2)), ylabel(, axis(2) alternate altgap(large)) legend(off)
_aa_probe y_y3alt (scatter mpg weight) (scatter price weight, yaxis(2)) (scatter length weight, yaxis(3)), ylabel(, axis(3) alternate) legend(off)
_aa_probe x_x2alt (scatter mpg weight) (scatter mpg price, xaxis(2)), xlabel(, axis(2) alternate) legend(off)
_aa_probe y_y1alt (scatter mpg weight) (scatter price weight, yaxis(2)), ylabel(, alternate) legend(off)

python:
import json, math, os, sys
from sfi import Macro

G = Macro.getGlobal
sys.path.insert(0, os.path.join(G("AA_REPO"), "scripts"))
from svg_truth import svg_document, label_value  # noqa: E402

work = G("AA_WORK")
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


out = {"y": {}, "x": {}}
keys = G("AA_KEYS").split()
for key in keys:
    group, name = key.split("_", 1)
    rc = int(G("AA_RC_" + key))
    r = {"rc": rc, "message": message(key) if rc else ""}
    if not rc:
        r["yscales"] = {str(n): pair(G("AA_SY%d_%s" % (n, key)))
                        for n in range(1, 10) if pair(G("AA_SY%d_%s" % (n, key)))}
        r["xscales"] = {str(n): pair(G("AA_SX%d_%s" % (n, key)))
                        for n in range(1, 10) if pair(G("AA_SX%d_%s" % (n, key)))}
        _doc = svg_document(os.path.join(work, key + ".svg"))
        r["axes"] = axes(_doc)
        r["columns"] = {sd: [[c, t] for c, t in cols] for sd, cols in columns(_doc).items()}
    out[group][name] = r
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("AA_VERSION"), "born_date": G("AA_BORN"),
                "dash_commit": commit, "extracted": G("AA_WHEN"),
                "source": "scripts/extract_axisn_alt_truth.do"}
with open(G("AA_OUT"), "w", encoding="utf-8") as fh:
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
print("wrote", G("AA_OUT"))
end
