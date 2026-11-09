* extract_recast_truth.do -- twoway's own recast(), recastas() and type()
* (WP-30 P1.8b, section 45), written to test/fixtures/recast_truth.json for
* test/test_recast.py, the RC cases of test/test_twoway_option_parity.cscript
* and the S45 block of test/test_wp30_truth.cscript.
*
* Records:
*   probes[<id>]  cmd, rc, lines (the log's "(note:" and error lines) and,
*                 for rc 0, counts: the SVG's circle, path, line, rect and
*                 polygon elements, and equal_to: the base probe whose SVG
*                 equals this one's (apart from <desc>), or "";
*                 the RH9- rows (WP-46 46-01) also bar_strokes: the
*                 stroke-width of each outlined rect in a plot colour
*                 (not the white frames), distinct, in SVG units.
*                 RH11-06..08: a repeated name on a range source.
*                 The RB-, RH5- and RH8- rows (WP-46 46-02) also yrange
*                 and xrange (.Graph's plot-region scale, curmin and
*                 curmax), ylabels and xlabels (svg_truth's axis
*                 reading), texts (every <text>, in order), marks (each
*                 plot rect, path and circle: fill, stroke and stroke
*                 width, distinct) and bar_w (the first plot rect's
*                 width in x units).
*   classes       Stata's four type classes, read from
*                 the style files *type-*.style of c(sysdir_base).
*
* Run (never the GUI; the slot wrapper of scripts/stata_slot.sh):
*   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_recast_truth.do
* SVGs and logs go to c(tmpdir).

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_recast_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zr_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zr_rc' | _rc {
    local _zr_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_recast_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1

clear all
set more off
version 19
set scheme stcolor

local stata_version = c(stata_version)
local born_date "`c(born_date)'"
tempfile gh
shell git -C "`repo'" rev-parse HEAD > "`gh'"
tempname fh
file open `fh' using "`gh'", read text
file read `fh' dash_commit
file close `fh'
local extracted "`c(current_date)'"
local tmp "`c(tmpdir)'"

local sysbase "`c(sysdir_base)'"

capture program drop _rc_data
program _rc_data
    clear
    quietly set obs 8
    generate double x  = _n
    generate double y  = .
    local ys  3 5 2 6 4 7 1 8
    forvalues i = 1/8 {
        quietly replace y = `: word `i' of `ys'' in `i'
    }
    generate double y2 = y + 3
    generate double t  = 9 - _n
    quietly tsset t
end

capture program drop _rc_probe
program _rc_probe
    args id cmd
    local tmp "`c(tmpdir)'"
    global RC_SEQ = $RC_SEQ + 1
    local f "rc_$RC_SEQ"
    capture log close rcp
    capture graph drop _all
    log using "`tmp'/`f'.log", text replace name(rcp)
    capture noisily `cmd'
    local rc = _rc
    log close rcp
    local svg ""
    if `rc' == 0 {
        quietly graph export "`tmp'/`f'.svg", replace
        local svg "svg"
        if inlist(substr("`id'", 1, 3), "RB-", "RH5", "RH8") {
            file write $RC_AH `"`id'|`.Graph.plotregion1.yscale.curmin'|`.Graph.plotregion1.yscale.curmax'|`.Graph.plotregion1.xscale.curmin'|`.Graph.plotregion1.xscale.curmax'"' _n
        }
    }
    file write $RC_RH `"`id'|`rc'|`svg'`f'|`cmd'"' _n
end

tempfile recs axr
tempname rh ah
file open `rh' using "`recs'", write text replace
global RC_RH `rh'
file open `ah' using "`axr'", write text replace
global RC_AH `ah'
global RC_SEQ 0

_rc_data
* The bases each recast is compared with.
_rc_probe B-line      "twoway line y x"
_rc_probe B-scatter   "twoway scatter y x"
_rc_probe B-connected "twoway connected y x"
_rc_probe B-bar       "twoway bar y x"
_rc_probe B-rspike    "twoway rspike y y2 x"
_rc_probe B-rscatter  "twoway rscatter y y2 x"
_rc_probe B-rbar      "twoway rbar y y2 x"
_rc_probe B-pcspike   "twoway pcspike y x y2 x"
_rc_probe B-pcbarrow  "twoway pcbarrow y x y2 x"
_rc_probe B-pccapsym  "twoway pccapsym y x y2 x"
_rc_probe B-tsconn    "twoway connected y t, sort"
_rc_probe B-2line     "twoway line y y2 x"
_rc_probe B-2scatter  "twoway scatter y y2 x"
_rc_probe B-dot       "twoway dot y x"
_rc_probe B-function  "twoway function y=x, range(1 5)"
* Within a class: the target's drawing.
_rc_probe W-sc-line     "twoway scatter y x, recast(line)"
_rc_probe W-li-scatter  "twoway line y x, recast(scatter)"
_rc_probe W-sc-co       "twoway scatter y x, recast(co)"
_rc_probe W-sc-b        "twoway scatter y x, recast(b)"
_rc_probe W-sc-li       "twoway scatter y x, recast(li)"
_rc_probe W-rl-line     "twoway rline y y2 x, recast(line)"
_rc_probe W-rl-rsc      "twoway rline y y2 x, recast(rsc)"
_rc_probe W-rl-rbarm    "twoway rline y y2 x, recast(rbarm)"
_rc_probe W-pc-pcbar    "twoway pcspike y x y2 x, recast(pcbar)"
_rc_probe W-pc-pccaps   "twoway pcspike y x y2 x, recast(pccaps)"
_rc_probe W-ts-conn     "twoway tsline y, recast(connected)"
_rc_probe W-2-line      "twoway scatter y y2 x, recast(line)"
_rc_probe W-2-lineline  "twoway scatter y y2 x, recast(line line)"
_rc_probe W-dot-line    "twoway dot y x, recast(line)"
_rc_probe W-fn-scatter  "twoway function y=x, range(1 5) recast(scatter)"
* Precedence and spellings.
_rc_probe PR-1 "twoway scatter y x, recast(line) type(bar)"
_rc_probe PR-2 "twoway scatter y x, type(bar) recast(line)"
_rc_probe PR-3 "twoway scatter y x, recastas(bar) recast(line)"
_rc_probe PR-4 "twoway scatter y x, recast(line) recast(bar)"
_rc_probe PR-5 "twoway scatter y x, type(line) type(bar)"
_rc_probe PR-6 "twoway scatter y x, recasta(line)"
_rc_probe PR-7 "twoway scatter y x, ty(line)"
_rc_probe SP-l    "twoway scatter y x, recast(l)"
_rc_probe SP-LINE "twoway scatter y x, recast(LINE)"
_rc_probe SP-rsc  "twoway scatter y x, recast(rsc)"
_rc_probe SP-pcl  "twoway pcspike y x y2 x, recast(pcl)"
_rc_probe SP-ls   "twoway scatter y y2 x, recast(line scatter)"
* Fallbacks.
_rc_probe FB-line    "twoway line y x, recast(rline)"
_rc_probe FB-rline   "twoway rline y y2 x, recast(pcspike)"
_rc_probe FB-pcspike "twoway pcspike y x y2 x, recast(line)"
_rc_probe FB-func    "twoway function y=x, range(1 5) recast(rline)"
_rc_probe FB-rbogus  "twoway rline y y2 x, recast(bogus)"
* Refusals.
_rc_probe RF-rec     "twoway scatter y x, rec(line)"
foreach tt in lfitci qfitci lpolyci fpfitci {
    _rc_probe RF-`tt'-recast   "twoway `tt' y x, recast(line)"
    _rc_probe RF-`tt'-recastas "twoway `tt' y x, recastas(line)"
    _rc_probe RF-`tt'-type     "twoway `tt' y x, type(line)"
}
* Literals.
_rc_probe L-scatteri "twoway scatteri 1 1 2 2 3 1, recast(line)"
_rc_probe L-pci      "twoway pci 1 1 2 2, recast(pcarrow)"
* Derived types on auto.
sysuse auto, clear
_rc_probe D-kdensity-area   "twoway kdensity mpg, recast(area)"
_rc_probe D-kdensity-base   "twoway kdensity mpg"
_rc_probe D-lfit-scatter    "twoway lfit mpg weight, recast(scatter)"
_rc_probe D-lfit-base       "twoway lfit mpg weight"
_rc_probe D-lfit-rline      "twoway lfit mpg weight, recast(rline)"
_rc_probe D-histogram-line  "twoway histogram mpg, recast(line)"
_rc_probe D-histogram-base  "twoway histogram mpg"
_rc_probe D-histogram-rline "twoway histogram mpg, recast(rline)"
_rc_probe D-function-scatter "twoway function y=x^2, range(0 3) recast(scatter)"
* WP-46 46-01: yx names on a y2xtype source (RH-11), and the generic
* style of an abbreviated bar (RH-9).
_rc_data
_rc_probe RH11-01 "twoway rline y y2 x, recast(sc)"
_rc_probe RH11-03 "twoway rline y y2 x, recast(co)"
_rc_probe RH11-04 "twoway rbar y y2 x, recast(b)"
_rc_probe RH11-05 "twoway tsrline y y2, recast(li)"
* A repeated yx name is one unknown y2xtype name; a repeated range name
* is that name (measured 09nov2026).
_rc_probe RH11-06 "twoway rline y y2 x, recast(line line)"
_rc_probe RH11-07 "twoway rline y y2 x, recast(rline rline)"
_rc_probe RH9-10  "twoway scatter y x, recast(b)"
_rc_probe RH9-11  "twoway scatter y x, recast(bar)"
_rc_probe RH9-12  "twoway bar y x, recast(b)"
sysuse auto, clear
_rc_probe RH11-02 "twoway histogram mpg, recast(li)"
_rc_probe RH11-08 "twoway histogram mpg, recast(line line)"
* WP-46 46-02: a range source drawn as a yx type keeps both bounds
* (RH-3), ciplot() as a yx type (RH-4), a recast histogram's style, bar
* width and zero (RH-5..7), and recast() with horizontal (RH-8).
_rc_data
_rc_probe RB-01 "twoway rline y y2 x, recast(line)"
_rc_probe RB-02 "twoway (rcap y y2 x, recast(scatter)) (scatter y x)"
_rc_probe RB-03 "twoway rbar y y2 x, recast(bar)"
_rc_probe RB-07 "twoway rline y y2 x"
_rc_probe RH8-02 "twoway rbar y y2 x, recast(rcap) horizontal"
sysuse auto, clear
_rc_probe RB-04 "twoway lfitci mpg weight, ciplot(area)"
_rc_probe RB-05 "twoway lfitci mpg weight, ciplot(bar)"
_rc_probe RB-06 "twoway lfitci mpg weight, ciplot(scatter)"
_rc_probe RB-08 "twoway lfitci mpg weight"
_rc_probe RH5-00 "twoway histogram mpg"
_rc_probe RH5-01 "twoway histogram mpg, recast(bar)"
_rc_probe RH5-02 "twoway histogram mpg, recast(area)"
_rc_probe RH5-03 "twoway histogram mpg, recast(spike)"
_rc_probe RH5-04 "twoway histogram mpg, recast(scatter)"
_rc_probe RH5-05 "twoway histogram mpg, recast(bar) gap(50)"
_rc_probe RH5-08 "twoway histogram mpg, gap(50)"
_rc_probe RH5-09 "twoway histogram mpg, recast(line)"
_rc_probe RH5-10 "twoway histogram mpg, recast(bar) color(red)"
_rc_probe RH8-01 "twoway histogram mpg, recast(bar) horizontal"
clear
quietly set obs 3
generate y = _n
_rc_probe RH5-06 "twoway histogram y, recast(area)"
_rc_probe RH5-07 "twoway histogram y, recast(dropline)"
file close `rh'
file close `ah'

python:
import json, os, re, glob, sys
from sfi import Macro
repo = Macro.getLocal("repo")
tmp = Macro.getLocal("tmp")
base = Macro.getLocal("sysbase")
sys.path.insert(0, os.path.join(repo, "scripts"))
import svg_truth

def _body(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    return re.sub(r"<desc>.*?</desc>", "", text, flags=re.S)

def _counts(path):
    b = _body(path)
    return {k: len(re.findall(r"<" + k + r"[\s>/]", b))
            for k in ("circle", "path", "line", "rect", "polygon")}

def _lines(log):
    out = []
    try:
        with open(log, encoding="utf-8", errors="replace") as fh:
            rows = fh.read().splitlines()
    except OSError:
        return out
    for r in rows:
        s = r.rstrip()
        if s.startswith("(note:") or "not allowed" in s:
            out.append(s)
    return out

def _bar_strokes(path):
    out = set()
    for m in re.finditer(r"<rect[^>]*style=\"([^\"]*)\"", _body(path)):
        st = m.group(1)
        if "fill:none" not in st or "stroke:#FFFFFF" in st:
            continue
        w = re.search(r"stroke-width:([0-9.]+)", st)
        if w:
            out.add(float(w.group(1)))
    return sorted(out)

def _num(s):
    try:
        return float(s)
    except ValueError:
        return None

_axr = {}
with open(Macro.getLocal("axr"), encoding="utf-8") as fh:
    for line in fh:
        parts = line.rstrip("\n").split("|")
        if len(parts) == 5:
            _axr[parts[0]] = [_num(v) for v in parts[1:]]

_STYLE = re.compile(r"<(rect|path|circle|use|line)[^>]*style=\"([^\"]*)\"")

def _marks(path):
    # Each plot mark's fill, stroke and stroke width, distinct: the
    # white region frames, the canvas, the axes (black) and the
    # gridlines (#f0f0f0) left out.  An area is a <use> of a path.
    out = set()
    for m in _STYLE.finditer(_body(path)):
        st = dict(kv.split(":", 1) for kv in m.group(2).split(";")
                  if ":" in kv)
        fill = st.get("fill", "").strip().lower()
        stroke = st.get("stroke", "").strip().lower()
        if fill in ("#ffffff", "", "none") and stroke in ("#ffffff", "none", "", "#000000", "#f0f0f0"):
            continue
        out.add((m.group(1), fill, stroke,
                 st.get("stroke-width", "").strip()))
    return [list(t) for t in sorted(out)]

def _axes(rec, pid, p):
    yr = _axr.get(pid)
    if yr:
        rec["yrange"] = yr[:2]
        rec["xrange"] = yr[2:]
    doc = svg_truth.svg_document(p)
    rec["texts"] = [t["text"] for t in doc["texts"]]
    rx = svg_truth.svg_axis_reading(p, "x", doc=doc)
    ry = svg_truth.svg_axis_reading(p, "y", doc=doc)
    rec["xlabels"] = list(rx.get("labels") or [])
    rec["ylabels"] = list(ry.get("labels") or [])
    rec["marks"] = _marks(p)
    rec["bar_w"] = None
    fit = rx.get("fit")
    pr = doc["plotregion"]
    plot = [r for r in svg_truth.svg_rects(p)
            if r["w"] and r["h"] and r["fill"] not in (None, "none", "#ffffff")
            and pr and r["x"] >= pr["left"] - 0.5
            and r["x"] + r["w"] <= pr["right"] + 0.5
            and r["w"] < 0.5 * (pr["right"] - pr["left"])]
    if fit and plot:
        rec["bar_w"] = round(abs(plot[0]["w"] * fit["units_per_px"]), 6)

probes = {}
with open(Macro.getLocal("recs"), encoding="utf-8") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if not line:
            continue
        pid, rc, svg, cmd = line.split("|", 3)
        f = svg[3:] if svg.startswith("svg") else svg
        rec = {"cmd": cmd, "rc": int(rc),
               "lines": _lines(os.path.join(tmp, f + ".log"))}
        p = os.path.join(tmp, f + ".svg")
        if svg.startswith("svg") and os.path.exists(p):
            rec["counts"] = _counts(p)
            if pid.startswith("RH9-"):
                rec["bar_strokes"] = _bar_strokes(p)
            if pid[:3] in ("RB-", "RH5", "RH8"):
                _axes(rec, pid, p)
            rec["_body"] = _body(p)
        probes[pid] = rec

bases = [k for k in probes if k.startswith("B-")]
for pid, rec in probes.items():
    rec["equal_to"] = ""
    if "_body" in rec and not pid.startswith("B-"):
        for b in bases:
            if probes[b].get("_body") == rec["_body"]:
                rec["equal_to"] = b
                break
for rec in probes.values():
    rec.pop("_body", None)

classes = {}
for path in sorted(glob.glob(os.path.join(base, "style", "*type-*.style"))):
    name = os.path.basename(path)[:-len(".style")]
    cls, _, member = name.partition("-")
    classes.setdefault(cls, []).append(member)
classes = {k: sorted(v) for k, v in classes.items()
           if k in ("yxtype", "y2xtype", "yxyxtype", "functiontype")}

out = {"probes": probes,
       "_meta": {"stata_version": Macro.getLocal("stata_version"),
                 "born_date": Macro.getLocal("born_date"),
                 "source": "scripts/extract_recast_truth.do",
                 "dash_commit": Macro.getLocal("dash_commit").strip(),
                 "extracted": Macro.getLocal("extracted"),
                 "scheme": "stcolor",
                 "classes": classes}}
path = os.path.join(repo, "test", "fixtures", "recast_truth.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote " + path)
end
