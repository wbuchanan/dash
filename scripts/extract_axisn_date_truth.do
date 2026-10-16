*! extract_axisn_date_truth.do -- WP-31 section 35 (GAPS3 C10e): measure
*! twoway's axes three to nine on a date variable -- each axis's labels and
*! scale when a %td variable is on yaxis(3) or xaxis(3) -- and where the
*! t-options tlabel(), ttick(), ttitle(), tscale() and tline() with axis(3)
*! land, and tmlabel()/tmtick() with axis(2) on a date axis 2.  twoway only: the output is the same before and after dash
*! changes.
*!
*! Output: test/fixtures/axisn_date_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_axisn_date_truth.do
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
mata: st_local("_ad_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_ad_bad' {
    display as error "extract_axisn_date_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _ad_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_ad_rc' | _rc {
    local _ad_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_axisn_date_truth.do: `_ad_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global AD_REPO "`repo'"
global AD_OUT "${AD_REPO}/test/fixtures/axisn_date_truth.json"

local work "`c(tmpdir)'dash_axisn_date_probe"
capture mkdir "`work'"
global AD_WORK "`work'"

if `"`c(python_exec)'"' == "" {
    display as error "extract_axisn_date_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

quietly shell git -C "${AD_REPO}" rev-parse HEAD > "${AD_WORK}/git_head.txt"
global AD_VERSION "`c(stata_version)'"
global AD_BORN "`c(born_date)'"
global AD_WHEN "`c(current_date)' `c(current_time)'"
global AD_KEYS ""

* _ad_probe key twoway-command: as extract_axes_n_truth.do's _an_probe:
* rc, log, SVG, each axis's scale (AD_SY<n>_<key>, AD_SX<n>_<key>) and its
* title text (AD_TY<n>_<key>, AD_TX<n>_<key>).
capture program drop _ad_probe
program define _ad_probe
    gettoken key cmd : 0
    quietly sysuse sp500, clear
    capture graph drop _all
    quietly log using "${AD_WORK}/`key'.log", text replace name(amp) nomsg
    capture noisily twoway `cmd' name(g, replace)
    local rc = _rc
    quietly log close amp
    global AD_RC_`key' `rc'
    global AD_KEYS "${AD_KEYS} `key'"
    forvalues n = 1/9 {
        global AD_SY`n'_`key' ""
        global AD_SX`n'_`key' ""
    }
    if !`rc' {
        quietly graph export "${AD_WORK}/`key'.svg", replace
        forvalues n = 1/9 {
            if "`.g.yaxis`n'.isa'" != "" {
                global AD_SY`n'_`key' "`.g.yaxis`n'.plotregion.yscale.curmin' `.g.yaxis`n'.plotregion.yscale.curmax'"
            }
            if "`.g.xaxis`n'.isa'" != "" {
                global AD_SX`n'_`key' "`.g.xaxis`n'.plotregion.xscale.curmin' `.g.xaxis`n'.plotregion.xscale.curmax'"
            }
        }
    }
    display as text "AM `key': rc `rc' y1 ${AD_SY1_`key'} y2 ${AD_SY2_`key'} x1 ${AD_SX1_`key'} x2 ${AD_SX2_`key'}"
end

* A %td variable on axis 3 (sp500: date is %td).
_ad_probe y3_date (scatter close open) (scatter volume open, yaxis(2)) (scatter date open, yaxis(3)), ytitle(AX3, axis(3))
_ad_probe x3_date (scatter close open) (scatter close volume, xaxis(2)) (scatter close date, xaxis(3)), xtitle(BX3, axis(3))
_ad_probe x3_tlabel (scatter close open) (scatter close volume, xaxis(2)) (scatter close date, xaxis(3)), tlabel(01feb2001 01jun2001 01oct2001, axis(3)) xtitle(BX3, axis(3))
_ad_probe x3_ttick (scatter close open) (scatter close volume, xaxis(2)) (scatter close date, xaxis(3)), ttick(01apr2001, axis(3)) xtitle(BX3, axis(3))
_ad_probe x3_ttitle (scatter close open) (scatter close volume, xaxis(2)) (scatter close date, xaxis(3)), ttitle(TT3, axis(3))
_ad_probe x3_tscale (scatter close open) (scatter close volume, xaxis(2)) (scatter close date, xaxis(3)), tscale(range(01jan2000 31dec2002) axis(3)) xtitle(BX3, axis(3))
_ad_probe x3_tline (scatter close open) (scatter close volume, xaxis(2)) (scatter close date, xaxis(3)), tline(01mar2001, axis(3)) xtitle(BX3, axis(3))
* tmlabel()/tmtick() with axis(2) on a date axis 2 (the D1b residual).
_ad_probe x3_tmlabel2 (scatter close open) (scatter close date, xaxis(2)), tmlabel(01apr2001 01oct2001, axis(2)) xtitle(BX2, axis(2))
_ad_probe x3_tmtick2 (scatter close open) (scatter close date, xaxis(2)), tmtick(01apr2001 01oct2001, axis(2)) xtitle(BX2, axis(2))
_ad_probe x3_tunused (scatter close open) (scatter close volume, xaxis(2)), tlabel(01feb2001, axis(3))

python:
import json, math, os, sys
from sfi import Macro

G = Macro.getGlobal
sys.path.insert(0, os.path.join(G("AD_REPO"), "scripts"))
from svg_truth import svg_document, label_value  # noqa: E402

work = G("AD_WORK")
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


out = {"y3": {}, "x3": {}}
keys = G("AD_KEYS").split()
for key in keys:
    group, name = key.split("_", 1)
    rc = int(G("AD_RC_" + key))
    r = {"rc": rc, "message": message(key) if rc else ""}
    if not rc:
        r["yscales"] = {str(n): pair(G("AD_SY%d_%s" % (n, key)))
                        for n in range(1, 10) if pair(G("AD_SY%d_%s" % (n, key)))}
        r["xscales"] = {str(n): pair(G("AD_SX%d_%s" % (n, key)))
                        for n in range(1, 10) if pair(G("AD_SX%d_%s" % (n, key)))}
        _doc = svg_document(os.path.join(work, key + ".svg"))
        r["axes"] = axes(_doc)
        r["columns"] = {sd: [[c, t] for c, t in cols] for sd, cols in columns(_doc).items()}
    out[group][name] = r
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("AD_VERSION"), "born_date": G("AD_BORN"),
                "dash_commit": commit, "extracted": G("AD_WHEN"),
                "source": "scripts/extract_axisn_date_truth.do"}
with open(G("AD_OUT"), "w", encoding="utf-8") as fh:
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
print("wrote", G("AD_OUT"))
end
