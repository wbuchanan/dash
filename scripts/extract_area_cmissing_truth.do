* extract_area_cmissing_truth.do -- twoway's own cmissing(n) on area, rarea
* and the estimators, connect() on rarea, and recast() of histogram to a
* range type and of pci/pcarrowi to a pc type (WP-31 C6, C7; section 14),
* written to test/fixtures/area_cmissing_truth.json for
* test/test_area_cmissing.py, test/test_recast_range_pc.py and the S14
* blocks of test/test_wp31_truth.cscript.
*
* Data: sysuse auto with mpg missing in 10/12, lo = mpg - 2, hi = mpg + 2.
* Records, per probe id:
*   cmd, rc, lines   the command, its return code and the log's "(note:"
*                    lines;
*   type             .<name>.plotregion1.plot1.type.setting (the type
*                    drawn) and class (its classname);
*   paths            every <path d> of the exported SVG split at M into
*                    subpaths of [x, y] in data units (1e-6), with filled,
*                    closed and stroke;
*   polys            the closed subpaths' [xmin, xmax] in data units (an
*                    area's or rarea's polygons: Stata writes them closed,
*                    with no fill attribute of their own);
*   rects, segs      every <rect> and every <line> but the gridlines and
*                    the black axis lines, in data units.
*
* Run (never the GUI; the slot wrapper):
*   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_area_cmissing_truth.do
* SVGs and logs go to c(tmpdir).

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_area_cmissing_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_area_cmissing_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
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

capture program drop _ac_data
program _ac_data
    sysuse auto, clear
    quietly replace mpg = . in 10/12
    quietly generate lo = mpg - 2
    quietly generate hi = mpg + 2
end

* One probe: the command under a named log, the drawn type, the SVG.
capture program drop _ac_probe
program _ac_probe
    args id cmd
    local tmp "`c(tmpdir)'"
    global AC_SEQ = $AC_SEQ + 1
    local f "ac_$AC_SEQ"
    capture log close acp
    capture graph drop _all
    log using "`tmp'/`f'.log", text replace name(acp)
    capture noisily `cmd' name(acg, replace)
    local rc = _rc
    log close acp
    local ty ""
    local cl ""
    if `rc' == 0 {
        local ty "`.acg.plotregion1.plot1.type.setting'"
        local cl "`.acg.plotregion1.plot1.classname'"
        quietly graph export "`tmp'/`f'.svg", replace
    }
    file write $AC_RH `"`id'|`rc'|`f'|`ty'|`cl'|`cmd'"' _n
end

tempfile recs
tempname rh
file open `rh' using "`recs'", write text replace
global AC_RH `rh'
global AC_SEQ 0

_ac_data
_ac_probe A00 "twoway area mpg weight in 1/20, sort"
_ac_probe A01 "twoway area mpg weight in 1/20, cmissing(n) sort"
_ac_probe A02 "twoway area mpg weight in 1/20, cmissing(y) sort"
_ac_probe A03 "twoway area mpg weight in 1/20, connect(stairstep) sort"
_ac_probe A04 "twoway area mpg weight in 1/20, cmissing(n) connect(stairstep) sort"
_ac_probe R00 "twoway rarea lo hi weight in 1/20, sort"
_ac_probe R01 "twoway rarea lo hi weight in 1/20, connect(stairstep) sort"
_ac_probe R02 "twoway rarea lo hi weight in 1/20, cmissing(n) sort"
_ac_probe R03 "twoway rarea lo hi weight in 1/20, connect(stepstair) cmissing(n) sort"
_ac_probe R04 "twoway rarea lo hi weight in 1/20, connect(none) sort"
_ac_probe E00 "twoway lowess mpg weight,"
_ac_probe E01 "twoway lowess mpg weight, cmissing(n)"
_ac_probe E02 "twoway lpolyci mpg weight, cmissing(n)"
_ac_probe E03 "twoway lpoly mpg weight, cmissing(n)"
_ac_probe E04 "twoway mband mpg weight, cmissing(n)"
_ac_probe E05 "twoway mspline mpg weight, cmissing(n)"
_ac_probe E06 "twoway fpfit mpg weight, cmissing(n)"
_ac_probe E07 "twoway fpfitci mpg weight, cmissing(n)"
_ac_probe E08 "twoway lfitci mpg weight, cmissing(n)"
_ac_probe E09 "twoway qfitci mpg weight, cmissing(n)"
_ac_probe E10 "twoway lowess mpg weight if foreign, cmissing(n)"
_ac_probe E11 "twoway lpoly mpg weight,"
_ac_probe E12 "twoway lfitci mpg weight,"
_ac_probe E13 "twoway fpfit mpg weight,"
_ac_probe H00 "twoway histogram mpg,"
_ac_probe H01 "twoway histogram mpg, recast(rarea)"
_ac_probe H02 "twoway histogram mpg, recast(bogus)"
_ac_probe H03 "twoway histogram mpg, recast(rbar)"
_ac_probe H04 "twoway histogram mpg, recast(rbar) gap(50)"
_ac_probe H05 "twoway histogram mpg, recast(rspike) gap(50) baroffset(1)"
_ac_probe H06 "twoway histogram mpg, recast(rcap)"
_ac_probe H07 "twoway histogram mpg, recast(rline)"
_ac_probe H08 "twoway histogram mpg, recast(rscatter)"
_ac_probe H09 "twoway histogram mpg, recast(rbar) gap(50) baroffset(1)"
_ac_probe H10 "twoway histogram mpg, recast(rcapsym)"
_ac_probe H11 "twoway histogram mpg, recast(rconnected)"
_ac_probe H12 "twoway histogram mpg, recast(rarea) gap(50) baroffset(1)"
_ac_probe P01 "twoway pci 20 2000 30 4000, recast(pcarrow)"
_ac_probe P02 "twoway pcarrowi 20 2000 30 4000, recast(pcscatter)"
_ac_probe P03 "twoway pci 20 2000 30 4000, recast(bogus)"
_ac_probe P04 "twoway pcarrowi 20 2000 30 4000, recast(pcspike)"
_ac_probe P05 "twoway pci 20 2000 30 4000, recast(pccapsym)"
_ac_probe P00 "twoway pci 20 2000 30 4000,"
file close `rh'

python:
import json, os, re, sys
from sfi import Macro
repo = Macro.getLocal("repo")
tmp = Macro.getLocal("tmp")
sys.path.insert(0, os.path.join(repo, "scripts"))
import svg_truth

def _fit(path, axis):
    pairs = svg_truth.svg_axis_reading(path, axis).get("pairs") or []
    if len(pairs) < 2:
        return None
    n = float(len(pairs))
    mx = sum(p for p, _ in pairs) / n
    mv = sum(v for _, v in pairs) / n
    b = (sum((p - mx) * (v - mv) for p, v in pairs)
         / sum((p - mx) ** 2 for p, _ in pairs))
    return (mv - b * mx, b)

def _read(path):
    fx = _fit(path, "x")
    fy = _fit(path, "y")
    if fx is None or fy is None:
        return None, None, None
    X = lambda a: round(fx[0] + fx[1] * float(a), 6)
    Y = lambda b: round(fy[0] + fy[1] * float(b), 6)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    paths = []
    for el in re.findall(r"<path[^>]*>", text):
        m = re.search(r'\sd="([^"]*)"', el)
        if not m:
            continue
        fill = re.search(r'fill="([^"]*)"', el)
        style = re.search(r'style="([^"]*)"', el)
        filled = bool(fill and fill.group(1) not in ("none",)) or bool(
            style and "fill:" in style.group(1)
            and "fill:none" not in style.group(1).replace(" ", ""))
        stroke = re.search(r'stroke="([^"]*)"', el) or re.search(
            r"stroke:\s*([^;\"]*)", el)
        for sub in re.split(r"(?=M)", m.group(1)):
            nums = re.findall(r"[ML]\s*(-?[0-9.]+)\s+(-?[0-9.]+)", sub)
            if not nums:
                continue
            paths.append({"pts": [[X(a), Y(b)] for a, b in nums],
                          "filled": filled,
                          "closed": "Z" in sub or "z" in sub,
                          "stroke": stroke.group(1) if stroke else ""})
    doc = svg_truth.svg_document(path)
    pr = doc.get("plotregion") or {}
    rects = []
    for r in doc.get("rects", []):
        if r is pr or r.get("w") is None:
            continue
        x0, y0 = r.get("x"), r.get("y")
        w, h = r.get("w"), r.get("h")
        if None in (x0, y0, w, h):
            continue
        rects.append([X(x0), X(x0 + w), Y(y0 + h), Y(y0), r.get("fill")])
    segs = []
    for k in ("vlines", "hlines", "diaglines"):
        for ln in doc.get(k, []):
            # Gridlines (#f0f0f0) and the black axis lines and ticks are
            # not the plot's.
            if ln.get("stroke") in ("#000000", "#f0f0f0"):
                continue
            segs.append([X(ln["x1"]), Y(ln["y1"]), X(ln["x2"]), Y(ln["y2"])])
    return paths, rects, segs

def _lines(log):
    out = []
    try:
        with open(log, encoding="utf-8", errors="replace") as fh:
            rows = fh.read().splitlines()
    except OSError:
        return out
    for s in rows:
        s = s.rstrip()
        if s.startswith("(note:") or "not allowed" in s:
            out.append(s)
    return out

probes = {}
with open(Macro.getLocal("recs"), encoding="utf-8") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if not line:
            continue
        pid, rc, f, ty, cl, cmd = line.split("|", 5)
        rec = {"cmd": cmd, "rc": int(rc), "type": ty, "class": cl,
               "lines": _lines(os.path.join(tmp, f + ".log"))}
        svgp = os.path.join(tmp, f + ".svg")
        if int(rc) == 0 and os.path.exists(svgp):
            paths, rects, segs = _read(svgp)
            rec["paths"] = paths
            rec["rects"] = rects
            rec["segs"] = segs
            rec["polys"] = [[min(p[0] for p in q["pts"]),
                             max(p[0] for p in q["pts"])]
                            for q in (paths or []) if q["closed"]]
        probes[pid] = rec

probes["_meta"] = {"stata_version": Macro.getLocal("stata_version"),
                   "born_date": Macro.getLocal("born_date"),
                   "dash_commit": Macro.getLocal("dash_commit").strip(),
                   "extracted": Macro.getLocal("extracted"),
                   "source": "scripts/extract_area_cmissing_truth.do",
                   "data": "sysuse auto; replace mpg = . in 10/12; lo = mpg - 2; hi = mpg + 2",
                   "scheme": "stcolor"}
path = os.path.join(repo, "test", "fixtures", "area_cmissing_truth.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(probes, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote " + path)
end
