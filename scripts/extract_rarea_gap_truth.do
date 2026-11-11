* extract_rarea_gap_truth.do -- twoway's rarea where a row misses one or
* both bounds inside the series and at its ends, under the default
* cmissing(y) and cmissing(n), sorted and unsorted, horizontal, on a
* subset (a filter move's rows: G11, G22, G23) and with stairs (WP-47
* PIC-17), written to
* test/fixtures/rarea_gap_truth.json for test/test_rarea_gap.py and the
* PIC-17 block of test/test_wp47_truth.cscript.
*
* Data (_rg_data): 8 rows, x = 1..8, lo = x, hi = 20 + 4*mod(x,2), so a
* straight edge across a missing upper bound (24 to 24) differs from the
* bound itself (20).  Each probe sets the rows it names missing.
* Records, per probe id: cmd, rc, type, and paths -- every <path d> of
* the exported SVG split at M into subpaths of [x, y] in data units (1e-6),
* with filled, closed and stroke; polys -- the closed subpaths' [xmin,
* xmax] (rarea's polygons, closed, stroked as drawn).
*
* Run (never the GUI; the slot wrapper):
*   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_rarea_gap_truth.do
* SVGs and logs go to c(tmpdir).

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_rarea_gap_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_rarea_gap_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
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

capture program drop _rg_data
program _rg_data
    args shuffle
    clear
    quietly set obs 8
    quietly generate double x = _n
    if "`shuffle'" != "" {
        * data order 1 3 2 5 4 7 6 8
        quietly replace x = cond(mod(_n, 2) == 0 & _n < 8, _n + 1, cond(mod(_n, 2) == 1 & _n > 1, _n - 1, _n))
    }
    quietly generate double lo = x
    quietly generate double hi = 20 + 4 * mod(x, 2)
end

* One probe: the data, the rows set missing (data-order row lists), the
* command under a named log, the drawn type and the SVG.
capture program drop _rg_probe
program _rg_probe
    args id shuffle mlo mhi cmd
    _rg_data `shuffle'
    foreach r of local mlo {
        quietly replace lo = . in `r'
    }
    foreach r of local mhi {
        quietly replace hi = . in `r'
    }
    local tmp "`c(tmpdir)'"
    global RG_SEQ = $RG_SEQ + 1
    local f "rg_$RG_SEQ"
    capture log close rgp
    capture graph drop _all
    log using "`tmp'/`f'.log", text replace name(rgp)
    capture noisily `cmd' name(rgg, replace)
    local rc = _rc
    log close rgp
    local ty ""
    local cl ""
    if `rc' == 0 {
        local ty "`.rgg.plotregion1.plot1.type.setting'"
        local cl "`.rgg.plotregion1.plot1.classname'"
        quietly graph export "`tmp'/`f'.svg", replace
    }
    file write $RG_RH `"`id'|`rc'|`f'|`ty'|`cl'|`shuffle'|`mlo'|`mhi'|`cmd'"' _n
end

tempfile recs
tempname rh
file open `rh' using "`recs'", write text replace
global RG_RH `rh'
global RG_SEQ 0

_rg_probe G00 "" "" "" "twoway rarea lo hi x, sort"
_rg_probe G01 "" "" "4" "twoway rarea lo hi x, sort"
_rg_probe G02 "" "4" "" "twoway rarea lo hi x, sort"
_rg_probe G03 "" "4" "4" "twoway rarea lo hi x, sort"
_rg_probe G04 "" "1" "8" "twoway rarea lo hi x, sort"
_rg_probe G05 "" "6" "3" "twoway rarea lo hi x, sort"
_rg_probe G06 "" "" "4 5" "twoway rarea lo hi x, sort"
_rg_probe G07 "" "" "4" "twoway rarea lo hi x,"
_rg_probe G08 "s" "" "4" "twoway rarea lo hi x,"
_rg_probe G09 "s" "" "4" "twoway rarea lo hi x, sort"
_rg_probe G10 "" "" "4" "twoway rarea lo hi x, sort horizontal"
_rg_probe G11 "" "" "4" "twoway rarea lo hi x if x != 2, sort"
_rg_probe G12 "" "" "4" "twoway rarea lo hi x, sort connect(stairstep)"
_rg_probe G13 "" "8" "1" "twoway rarea lo hi x, sort"
_rg_probe G14 "" "1 2" "" "twoway rarea lo hi x, sort"
_rg_probe G15 "" "" "7 8" "twoway rarea lo hi x, sort"
_rg_probe G16 "" "8" "" "twoway rarea lo hi x, sort"
_rg_probe G17 "" "" "1" "twoway rarea lo hi x, sort"
_rg_probe G18 "" "1" "8" "twoway rarea hi lo x, sort"
_rg_probe G19 "" "" "4 5" "twoway rarea lo hi x, sort connect(stairstep)"
_rg_probe G20 "" "" "1 8" "twoway rarea lo hi x, sort"
_rg_probe G21 "s" "" "1 8" "twoway rarea lo hi x,"
_rg_probe G22 "" "" "4" "twoway rarea lo hi x if x != 5, sort"
_rg_probe G23 "" "" "2" "twoway rarea lo hi x if x != 1, sort"
_rg_probe N01 "" "" "4" "twoway rarea lo hi x, sort cmissing(n)"
_rg_probe N02 "" "4" "" "twoway rarea lo hi x, sort cmissing(n)"
_rg_probe N03 "" "4" "4" "twoway rarea lo hi x, sort cmissing(n)"
_rg_probe N04 "" "1" "8" "twoway rarea lo hi x, sort cmissing(n)"
_rg_probe N05 "" "6" "3" "twoway rarea lo hi x, sort cmissing(n)"
_rg_probe N10 "" "" "4" "twoway rarea lo hi x, sort cmissing(n) horizontal"
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
        pid, rc, f, ty, cl, sh, mlo, mhi, cmd = line.split("|", 8)
        rec = {"cmd": cmd, "rc": int(rc), "type": ty, "class": cl,
               "shuffle": bool(sh), "lo_missing": mlo.split(),
               "hi_missing": mhi.split(),
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
                   "source": "scripts/extract_rarea_gap_truth.do",
                   "data": "8 rows: x = 1..8, lo = x, hi = 20 + 4*mod(x,2) (24 at odd x, 20 at even); each probe sets the named rows missing (in data order)",
                   "scheme": "stcolor"}
path = os.path.join(repo, "test", "fixtures", "rarea_gap_truth.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(probes, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote " + path)
end
