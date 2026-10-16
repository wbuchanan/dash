* extract_refline_frame_truth.do -- twoway's reference lines at positions
* outside the axis's range (WP-31 D12, section 38), written to
* test/fixtures/refline_frame_truth.json for test/test_refline_frame.py and
* the S38 block of test/test_wp31_truth.cscript.
*
* Each probe is `twoway scatter mpg weight, <lines>' on sysuse auto,
* exported to SVG beside a baseline run without the lines.  A reference
* line is a line group (one position, stroke, width) the probe draws and
* its baseline does not.  Recorded per probe: rc, the canvas and the plot
* region (px), each axis's first and last labelled tick and the fitted
* px<->value map (svg_truth.svg_axis_reading), whether the axes equal the
* baseline's, and per line its px, its ends and whether it lies outside
* the plot region.  zoom.asym runs under dashxlow, a scratch user scheme
* (#include s2color, `yesno xyline_extend_low no') written to the
* current directory, the scheme test_refline_extent.py's E12 uses.
* _meta.arrow_unclipped is the D-38.a headless-Chrome probe's result, read
* from the file named by the environment variable DASH_PROBE (a line
* `arrow_unclipped: true|false'); absent, null.
*
* Run (never the GUI; the slot wrapper of scripts/stata_slot.sh):
*   DASH_REPO=<repo> DASH_PROBE=<file> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_refline_frame_truth.do

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_xf_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_xf_bad' {
    display as error "extract_refline_frame_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _xf_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_xf_rc' | _rc {
    local _xf_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_refline_frame_truth.do: `_xf_show' is not a dash tree; set DASH_REPO to the repository root"'
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
local probe : environment DASH_PROBE

tempname sf
file open `sf' using "`c(pwd)'/scheme-dashxlow.scheme", write text replace
file write `sf' "#include s2color" _n "yesno xyline_extend_low no" _n
file close `sf'
adopath ++ "`c(pwd)'/"

tempfile records
tempname rf
file open `rf' using "`records'", write text replace
global XF_RF `rf'

capture program drop _xf_case
program _xf_case
    // _xf_case key scheme lines: runs the probe and its baseline, exports
    // both, appends key|scheme|rc|svg|base.
    args key scheme lines
    quietly sysuse auto, clear
    set scheme `scheme'
    capture graph drop _all
    capture noisily twoway scatter mpg weight, `macval(lines)' name(g, replace)
    local rc = _rc
    local out ""
    local bout ""
    local id = subinstr("`key'", ".", "_", .)
    if !`rc' {
        local out "`c(pwd)'/xf_`id'.svg"
        quietly graph export "`out'", replace name(g)
        capture graph drop _all
        twoway scatter mpg weight, name(b, replace)
        local bout "`c(pwd)'/xf_`id'_base.svg"
        quietly graph export "`bout'", replace name(b)
    }
    capture graph drop _all
    file write $XF_RF "`key'|`scheme'|`rc'|`out'|`bout'" _n
    mata: st_global("XF_OPT_`id'", st_local("lines"))
end

_xf_case outside.x_5100 s2color "xline(5100)"
_xf_case outside.x_5200 s2color "xline(5200)"
_xf_case outside.x_10000 s2color "xline(10000)"
_xf_case outside.x_neg s2color "xline(-500)"
_xf_case outside.y_60 s2color "yline(60)"
_xf_case outside.mixed s2color "xline(3000 10000)"
_xf_case outside.noextend s2color "xline(10000, noextend)"
_xf_case inside.control s2color "xline(3000)"
_xf_case zoom.asym dashxlow "xline(3000)"

file close `rf'
global XF_RF

python:
import json, os, sys
from sfi import Macro
repo = Macro.getLocal("repo")
sys.path.insert(0, os.path.join(repo, "scripts"))
import svg_truth


def _groups(doc):
    g = {}
    for dim, lines, coord in (("v", doc["vlines"], "x1"),
                              ("h", doc["hlines"], "y1")):
        for d in lines:
            key = (dim, round(d[coord], 1), d["stroke"], d["width"])
            g.setdefault(key, []).append(d)
    out = []
    for key, segs in g.items():
        a, b = ("y1", "y2") if key[0] == "v" else ("x1", "x2")
        out.append({"dim": key[0], "px": key[1], "stroke": key[2],
                    "width": key[3],
                    "ends": [round(min(min(d[a], d[b]) for d in segs), 3),
                             round(max(max(d[a], d[b]) for d in segs), 3)]})
    return out


def _axis(path, doc, letter):
    r = svg_truth.svg_axis_reading(path, letter, doc=doc)
    vals = [v for _, v in (r.get("pairs") or [])]
    fit = r.get("fit") or {}
    return {"first": min(vals) if vals else None,
            "last": max(vals) if vals else None,
            "labels": [l for l in (r.get("labels") or []) if l is not None],
            "fit": ({k: fit[k] for k in sorted(fit)
                     if isinstance(fit[k], (int, float, str))} or None)}


recs = []
with open(Macro.getLocal("records"), encoding="utf-8") as fh:
    for ln in fh:
        recs.append(ln.rstrip("\n").split("|"))
probes = {}
for key, scheme, rc, svg, bsvg in recs:
    rec = {"opt": Macro.getGlobal("XF_OPT_" + key.replace(".", "_")).strip(),
           "scheme": scheme, "rc": int(rc)}
    if svg:
        doc = svg_truth.svg_document(svg)
        bdoc = svg_truth.svg_document(bsvg)
        pr = doc["plotregion"]
        region = [round(pr[k], 3) for k in ("left", "top", "right", "bottom")]
        base = {(g["dim"], g["px"], g["stroke"], g["width"])
                for g in _groups(bdoc)}
        lines = []
        for g in _groups(doc):
            if (g["dim"], g["px"], g["stroke"], g["width"]) in base:
                continue
            lo_edge, hi_edge = ((region[0], region[2]) if g["dim"] == "v"
                                else (region[1], region[3]))
            g["outside"] = not (lo_edge - 0.5 <= g["px"] <= hi_edge + 0.5)
            g["on_canvas"] = (0 <= g["px"] <= (doc["canvas"]["w"] if
                                               g["dim"] == "v" else
                                               doc["canvas"]["h"]))
            lines.append(g)
        rec["lines"] = sorted(lines, key=lambda e: (e["dim"], e["px"]))
        rec["region"] = region
        rec["canvas"] = doc["canvas"]
        rec["x_axis"] = _axis(svg, doc, "x")
        rec["y_axis"] = _axis(svg, doc, "y")
        bx, by = _axis(bsvg, bdoc, "x"), _axis(bsvg, bdoc, "y")
        # Where each position falls on the axis's own px<->value map:
        # twoway writes a far position at a wrapped coordinate (measured:
        # xline(10000) at x px 842 inside the plot region, where the map
        # puts it at 8952, off the 3960-px canvas), so a line's "px" can
        # differ from its "axis_px".
        letter = "x" if rec["opt"].startswith("xline") else "y"
        fit = rec[letter + "_axis"]["fit"]
        pos = [float(t) for t in rec["opt"].split("(", 1)[1].split(",")[0]
               .rstrip(")").split()]
        rec["positions"] = pos
        if fit and fit.get("space") == "linear":
            if letter == "x":
                rec["axis_px"] = [round(region[0] + (v - fit["low"])
                                        / fit["units_per_px"], 2)
                                  for v in pos]
            else:
                rec["axis_px"] = [round(region[1] + (v - fit["high"])
                                        / fit["units_per_px"], 2)
                                  for v in pos]
        rec["axes_as_baseline"] = (bx["labels"] == rec["x_axis"]["labels"]
                                   and by["labels"] == rec["y_axis"]["labels"])
    probes[key] = rec
unclipped = None
probe = Macro.getLocal("probe")
if probe and os.path.isfile(probe):
    with open(probe, encoding="utf-8") as fh:
        for ln in fh:
            if ln.strip().startswith("arrow_unclipped:"):
                unclipped = ln.split(":", 1)[1].strip().lower() == "true"
                break
meta = {"stata_version": Macro.getLocal("stata_version"),
        "born_date": Macro.getLocal("born_date"),
        "dash_commit": Macro.getLocal("dash_commit"),
        "extracted": Macro.getLocal("extracted"),
        "source": "scripts/extract_refline_frame_truth.do",
        "arrow_unclipped": unclipped}
out = os.path.join(repo, "test", "fixtures", "refline_frame_truth.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump({"probes": probes, "_meta": meta}, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote " + out)
end

set scheme `entry_scheme'
