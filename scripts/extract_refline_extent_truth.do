* extract_refline_extent_truth.do -- twoway's reference-line extent
* (WP-30 P1.21b, section 50), written to
* test/fixtures/refline_extent_truth.json for test/test_refline_extent.py
* and the S50 block of test/test_wp30_truth.cscript.
*
* Probes E01-E26, `twoway scatter mpg weight, <opts>' on sysuse auto, each
* with xline(3000<, sub>) and yline(25<, sub>) (25 is no ylabel position,
* so no gridline lies under the line), exported to SVG with a baseline run
* of the same command without the lines.  A reference line is a line group
* (one position, stroke, width) the probe draws and its baseline does not.
* Per line: its SVG ends and the inset of each end from the plot region
* it lies in, as a fraction of that region along the line (`low' is the
* bottom of an xline and the left of a yline); 0 when the end reaches the
* frame.  Also rc and every `(note:' line.
* Two scratch user schemes, dashxlow and dashxhigh (#include s2color, one
* `yesno xyline_extend_*' key set to no), are written to the current
* directory, which is put on the ado-path.
*
* Run (never the GUI; the slot wrapper of scripts/stata_slot.sh):
*   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_refline_extent_truth.do

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_xe_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_xe_bad' {
    display as error "extract_refline_extent_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _xe_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_xe_rc' | _rc {
    local _xe_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_refline_extent_truth.do: `_xe_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1

clear all
set more off
set linesize 255
version 19
local entry_scheme "`c(scheme)'"

local stata_version = c(stata_version)
local born_date "`c(born_date)'"
tempfile gh
shell git -C "`repo'" rev-parse HEAD > "`gh'"
tempname fh
file open `fh' using "`gh'", read text
file read `fh' dash_commit
file close `fh'
local extracted "`c(current_date)'"

* The scratch user schemes.
foreach s in low high {
    tempname sf
    file open `sf' using "`c(pwd)'/scheme-dashx`s'.scheme", write text replace
    file write `sf' "#include s2color" _n "yesno xyline_extend_`s' no" _n
    file close `sf'
}
adopath ++ "`c(pwd)'/"

tempfile records
tempname rf
file open `rf' using "`records'", write text replace
global XE_RF `rf'

capture program drop _xe_case
program _xe_case
    // _xe_case id scheme kind lines rest: kind "auto", "two" (a second y
    // axis) or "date" (a %td x); lines the xline()/yline() options, rest
    // the others.  Runs the probe and its baseline, exports both, and
    // appends id|scheme|rc|svg|base|log.
    args id scheme kind lines rest
    if "`kind'" == "date" {
        quietly sysuse auto, clear
        quietly gen d = mdy(1, 1, 2000) + 5 * _n
        format d %td
        local cmd "twoway scatter mpg d"
    }
    else {
        quietly sysuse auto, clear
        local cmd "twoway scatter mpg weight"
        if "`kind'" == "two" {
            local cmd "twoway (scatter mpg weight) (scatter price weight, yaxis(2))"
        }
    }
    set scheme `scheme'
    local log "`c(pwd)'/xe_`id'.log"
    capture graph drop _all
    quietly log using "`log'", text replace name(xetruth)
    capture noisily `cmd', `macval(lines)' `macval(rest)' name(g, replace)
    local rc = _rc
    quietly log close xetruth
    local out ""
    local bout ""
    if !`rc' {
        local out "`c(pwd)'/xe_`id'.svg"
        quietly graph export "`out'", replace name(g)
        capture graph drop _all
        capture `cmd', `macval(rest)' name(b, replace)
        local bout "`c(pwd)'/xe_`id'_base.svg"
        quietly graph export "`bout'", replace name(b)
    }
    capture graph drop _all
    file write $XE_RF "`id'|`scheme'|`rc'|`out'|`bout'|`log'" _n
    mata: st_global("XE_OPT_`id'", st_local("lines") + " " + st_local("rest"))
end

capture program drop _xe_run
program _xe_run
    // _xe_run id scheme kind sub rest: xline(3000<, sub>) yline(25<, sub>).
    args id scheme kind sub rest
    local c = cond(`"`sub'"' == "", "", ", ")
    if "`kind'" == "date" {
        local lines `"xline(14700`c'`sub') yline(25`c'`sub')"'
    }
    else if "`kind'" == "two" {
        local lines `"xline(3000`c'`sub') yline(5000, axis(2) `sub')"'
    }
    else {
        local lines `"xline(3000`c'`sub') yline(25`c'`sub')"'
    }
    _xe_case `id' `scheme' `kind' `"`macval(lines)'"' `"`macval(rest)'"'
end

_xe_run E01 s2color auto "" ""
_xe_run E02 s2color auto "noextend" ""
_xe_run E03 s2color auto "extend" ""
_xe_run E04 s2color auto "style(unextended)" ""
_xe_run E05 s2color auto "style(extended)" ""
_xe_run E06 s2color auto "style(default)" ""
_xe_run E07 s2color auto "style(nosuch)" ""
_xe_run E08 s2color auto "style(Unextended)" ""
_xe_run E09 s2color auto "style()" ""
_xe_run E10 s2color auto "noextend extend" ""
_xe_run E11 s2color auto "style(unextended) extend" ""
_xe_run E12 dashxlow auto "" ""
_xe_run E13 dashxhigh auto "" ""
_xe_run E14 dashxlow auto "extend" ""
_xe_run E15 s2color auto "noextend" "yscale(log)"
_xe_run E16 s2color auto "noextend" "plotregion(margin(zero))"
_xe_run E17 s2color auto "noextend" "plotregion(margin(large))"
_xe_run E18 s2color auto "noextend" "plotregion(margin(l=10 b=0))"
_xe_run E19 dashxlow auto "" "xscale(reverse) yscale(reverse)"
_xe_run E20 s2color two "noextend" ""
_xe_run E21 s2color auto "noextend" "by(foreign)"
_xe_run E22 stcolor auto "noextend" ""
_xe_run E23 economist auto "noextend" ""
_xe_run E24 s2color auto "noextend" "xscale(range(1000 6000))"
_xe_run E25 s2color date "noextend" ""
_xe_run E26 s2color auto "noextend lstyle(p1)" ""

file close `rf'
global XE_RF

python:
import json, os, re, sys
from sfi import Macro
repo = Macro.getLocal("repo")
sys.path.insert(0, os.path.join(repo, "scripts"))
import svg_truth


def _notes(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = [ln.rstrip("\n").replace(" ", " ") for ln in fh]
    notes, cur = [], None
    for ln in lines:
        s = ln.strip()
        if cur is not None:
            if s and not s.startswith(".") and not s.startswith("(note"):
                cur += " " + s
                continue
            notes.append(cur)
            cur = None
        if s.startswith("(note:"):
            cur = s
    if cur is not None:
        notes.append(cur)
    return [re.sub(r"\s+", " ", n) for n in notes]


def _region(doc, d, dim):
    """The smallest region holding segment *d*, else the plot region."""
    best = None
    lo, hi = ((min(d["y1"], d["y2"]), max(d["y1"], d["y2"])) if dim == "v"
              else (min(d["x1"], d["x2"]), max(d["x1"], d["x2"])))
    for r in doc["regions"]:
        if dim == "v":
            ok = (r["left"] - 0.5 <= d["x1"] <= r["right"] + 0.5
                  and r["top"] - 0.5 <= lo and hi <= r["bottom"] + 0.5)
        else:
            ok = (r["top"] - 0.5 <= d["y1"] <= r["bottom"] + 0.5
                  and r["left"] - 0.5 <= lo and hi <= r["right"] + 0.5)
        area = (r["right"] - r["left"]) * (r["bottom"] - r["top"])
        if ok and (best is None or area < best[0]):
            best = (area, r)
    r = best[1] if best else doc["plotregion"]
    return tuple(round(r[k], 2) for k in ("left", "top", "right", "bottom"))


def _groups(doc):
    """One group per drawn line: its segments share an orientation, a
    position, a stroke, a width and a region (a by() yline is one segment
    per panel)."""
    g = {}
    for dim, lines, coord in (("v", doc["vlines"], "x1"),
                              ("h", doc["hlines"], "y1")):
        for d in lines:
            key = (dim, round(d[coord], 1), d["stroke"], d["width"],
                   _region(doc, d, dim))
            g.setdefault(key, []).append(d)
    out = []
    for key, segs in g.items():
        a, b = ("y1", "y2") if key[0] == "v" else ("x1", "x2")
        out.append({"dim": key[0], "px": key[1], "stroke": key[2],
                    "width": key[3], "region": key[4],
                    "n_segments": len(segs),
                    "span_from": min(min(d[a], d[b]) for d in segs),
                    "span_to": max(max(d[a], d[b]) for d in segs)})
    return out


def _key(g):
    return (g["dim"], g["px"], g["stroke"], g["width"], g["region"])


recs = []
with open(Macro.getLocal("records"), encoding="utf-8") as fh:
    for ln in fh:
        recs.append(ln.rstrip("\n").split("|"))
probes = {}
for cid, scheme, rc, svg, bsvg, log in recs:
    rec = {"opt": Macro.getGlobal("XE_OPT_" + cid).strip(),
           "scheme": scheme, "rc": int(rc), "notes": _notes(log)}
    if svg:
        doc = svg_truth.svg_document(svg)
        bdoc = svg_truth.svg_document(bsvg)
        base = {_key(g) for g in _groups(bdoc)}
        xl, yl = [], []
        for g in _groups(doc):
            if _key(g) in base:
                continue
            r = dict(zip(("left", "top", "right", "bottom"), g["region"]))
            if g["dim"] == "v":
                ext = r["bottom"] - r["top"]
                low = (r["bottom"] - g["span_to"]) / ext
                high = (g["span_from"] - r["top"]) / ext
            else:
                ext = r["right"] - r["left"]
                low = (g["span_from"] - r["left"]) / ext
                high = (r["right"] - g["span_to"]) / ext
            ent = {"colour": g["stroke"], "px": g["px"],
                   "ends": [g["span_from"], g["span_to"]],
                   "region": list(g["region"]),
                   "dashed": g["n_segments"] > 1,
                   "low_inset": round(max(low, 0.0), 6),
                   "high_inset": round(max(high, 0.0), 6)}
            (xl if g["dim"] == "v" else yl).append(ent)
        rec["xline"] = sorted(xl, key=lambda e: e["px"])
        rec["yline"] = sorted(yl, key=lambda e: e["px"])
        rec["region"] = [doc["plotregion"][k] for k in
                         ("left", "top", "right", "bottom")]
    probes[cid] = rec
meta = {"stata_version": Macro.getLocal("stata_version"),
        "born_date": Macro.getLocal("born_date"),
        "source": "scripts/extract_refline_extent_truth.do",
        "dash_commit": Macro.getLocal("dash_commit"),
        "extracted": Macro.getLocal("extracted"),
        "scheme": {k: v["scheme"] for k, v in probes.items()}}
out = os.path.join(repo, "test", "fixtures", "refline_extent_truth.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump({"probes": probes, "_meta": meta}, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote " + out)
end

set scheme `entry_scheme'
