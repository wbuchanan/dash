*! extract_area_outline_truth.do
*! WP-34 section 34-05 (PIC-1, RH-14): ground truth for the outline twoway
*! strokes round an area plot, for test/fixtures/area_outline_truth.json.
*!
*! WHY THIS EXISTS
*!
*! dash drew an area with no outline unless lcolor(), lwidth(), lpattern()
*! or a named line style asked for one, and then along the top only.
*! twoway strokes the polygon it fills in the p#area line style.  This
*! script records, per scheme, the outline colour and width and the fill
*! colour of plots 1-3 of `twoway (area le_wm year) (area le_bm year)
*! (area le_wf year)' (sysuse uslifeexp), and under stcolor the shape of
*! the stroked path of three probes (plain, nodropbase, cmissing(n) with a
*! gap), read from each probe's exported SVG.
*!
*! Output: test/fixtures/area_outline_truth.json
*!
*! Run with (the script sets its own directories):
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_area_outline_truth.do
*!
*! Never calls back into Stata from the trailing python: block; a backtick
*! inside it is spelled \x60.
*! ---------------------------------------------------------------------------

clear all
set graphics off
set more off
set linesize 255

* Root: DASH_REPO, else the current directory when it is a dash tree.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_area_outline_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_area_outline_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZA_REPO "`repo'"
global ZA_OUT  "`repo'/test/fixtures/area_outline_truth.json"

local work "`c(tmpdir)'dash_area_outline_probe"
capture mkdir "`work'"
global ZA_WORK "`work'"
display as text "probe work dir: ${ZA_WORK}"

global ZA_SVER = c(stata_version)
global ZA_BORN = c(born_date)
global ZA_DATE = "`c(current_date)' `c(current_time)'"

// Provenance stamp: shell writes the commit into a file, read back.
tempfile zagitrev
quietly shell git -C "${ZA_REPO}" rev-parse HEAD > "`zagitrev'"
tempname zagfh
file open `zagfh' using "`zagitrev'", read text
file read `zagfh' zagitline
file close `zagfh'
global ZA_COMMIT = trim(`"`zagitline'"')
capture assert ustrregexm(`"${ZA_COMMIT}"', "^[0-9a-f]{40}$")
if _rc {
    display as error "extract_area_outline_truth.do: git rev-parse HEAD did not print a 40-character commit"
    exit 498
}

// ---------------------------------------------------------------------------
// (a) The style of plots 1-3 per scheme: outline colour and width, fill
//     colour (shadestyle, before intensity); and plot 1 under lcolor(red).
// ---------------------------------------------------------------------------
global ZA_SCHEMES "s1mono s1color s2mono s2color sj economist meta stmono1 stgcolor stcolor"
global ZA_REC "${ZA_WORK}/styles.txt"
tempname rec
file open `rec' using "${ZA_REC}", write text replace
sysuse uslifeexp, clear
foreach s of global ZA_SCHEMES {
    twoway (area le_wm year) (area le_bm year) (area le_wf year), scheme(`s') nodraw
    forvalues k = 1/3 {
        local A ".Graph.plotregion1.plot`k'.style.area"
        local lc "``A'.linestyle.color.rgb'"
        local lw "``A'.linestyle.width.val'"
        local fc "``A'.shadestyle.color.rgb'"
        file write `rec' "`s'|`k'|`lc'|`lw'|`fc'" _n
    }
    twoway (area le_wm year, lcolor(red)) (area le_bm year), scheme(`s') nodraw
    local A ".Graph.plotregion1.plot1.style.area"
    local lc "``A'.linestyle.color.rgb'"
    local lw "``A'.linestyle.width.val'"
    local fc "``A'.shadestyle.color.rgb'"
    file write `rec' "`s'|red|`lc'|`lw'|`fc'" _n
}
file close `rec'

// ---------------------------------------------------------------------------
// (b) The stroked path, scheme stcolor: plain, nodropbase, cmissing(n) gap.
// ---------------------------------------------------------------------------
sysuse uslifeexp, clear
twoway area le_wm year, scheme(stcolor)
graph export "${ZA_WORK}/a_plain.svg", as(svg) replace
twoway area le_wm year, nodropbase scheme(stcolor)
graph export "${ZA_WORK}/a_nodrop.svg", as(svg) replace
// (c) the data (le_wm abbreviates le_wmale), before the gap probe
global ZA_DATA "${ZA_WORK}/data.csv"
export delimited year le_wm using "${ZA_DATA}", replace
replace le_wm = . in 40/45
twoway area le_wm year, cmissing(n) scheme(stcolor)
graph export "${ZA_WORK}/a_gap.svg", as(svg) replace
graph drop _all

python:
import csv
import json
import re
from sfi import Macro

W = Macro.getGlobal("ZA_WORK")
OUT = Macro.getGlobal("ZA_OUT")


def _hex(rgb):
    p = [int(float(v)) for v in str(rgb).split()]
    return "#%02x%02x%02x" % tuple(p[:3])


schemes = {}
red = {}
with open(Macro.getGlobal("ZA_REC")) as fh:
    for line in fh:
        s, k, lc, lw, fc = line.rstrip("\n").split("|")
        rec = {"line": _hex(lc), "fill": _hex(fc), "width": float(lw)}
        if k == "red":
            red[s] = rec
        else:
            schemes.setdefault(s, []).append(rec)

_NUM = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


def _subpaths(d):
    """Absolute M/L/Z subpaths of an SVG path *d* (twoway writes M, L, Z
    and their lower-case forms only)."""
    out, cur, closed = [], None, False
    pos = (0.0, 0.0)
    for cmd, args in re.findall(r"([MmLlHhVvZz])([^MmLlHhVvZz]*)", d):
        nums = [float(v) for v in _NUM.findall(args)]
        if cmd in "Mm":
            if cur:
                out.append((cur, closed))
            cur, closed = [], False
            pts = list(zip(nums[0::2], nums[1::2]))
            for i, (a, b) in enumerate(pts):
                pos = (pos[0] + a, pos[1] + b) if cmd == "m" else (a, b)
                cur.append(pos)
        elif cmd in "Ll":
            for a, b in zip(nums[0::2], nums[1::2]):
                pos = (pos[0] + a, pos[1] + b) if cmd == "l" else (a, b)
                cur.append(pos)
        elif cmd in "Hh":
            for a in nums:
                pos = (pos[0] + a if cmd == "h" else a, pos[1])
                cur.append(pos)
        elif cmd in "Vv":
            for b in nums:
                pos = (pos[0], pos[1] + b if cmd == "v" else b)
                cur.append(pos)
        else:
            closed = True
    if cur:
        out.append((cur, closed))
    return out


def _shape(pts, closed):
    ys = [p[1] for p in pts]
    xs = [p[0] for p in pts]
    ymax, xmin, xmax = max(ys), min(xs), max(xs)
    first, last = pts[0], pts[-1]
    closed = bool(closed or (abs(first[0] - last[0]) <= 0.01
                             and abs(first[1] - last[1]) <= 0.01))
    at = lambda x: any(abs(p[0] - x) <= 0.5 and abs(p[1] - ymax) <= 0.5
                       for p in pts)
    return {"closed": closed, "base_corners": bool(at(xmin) and at(xmax))}


def _stroked(svg, colour):
    ids = {m.group(1): m.group(2) for m in re.finditer(
        r'<path[^>]*\bid="([^"]+)"[^>]*\bd="([^"]+)"', svg)}
    ids.update({m.group(2): m.group(1) for m in re.finditer(
        r'<path[^>]*\bd="([^"]+)"[^>]*\bid="([^"]+)"', svg)})
    found = []
    for m in re.finditer(r"<(use|path)\b([^>]*)>", svg):
        attrs = m.group(2)
        st = re.search(r'style="([^"]*)"', attrs)
        st = st.group(1).lower() if st else ""
        if "stroke:" + colour.lower() not in st:
            continue
        if m.group(1) == "use":
            h = re.search(r'(?:xlink:)?href="#([^"]+)"', attrs)
            d = ids.get(h.group(1)) if h else None
        else:
            d = re.search(r'\bd="([^"]+)"', attrs)
            d = d.group(1) if d else None
        if d:
            found.extend(_shape(p, c) for p, c in _subpaths(d))
    return found


line1 = schemes["stcolor"][0]["line"]
paths = {}
for probe in ("plain", "nodrop", "gap"):
    with open("%s/a_%s.svg" % (W, probe)) as fh:
        paths[probe] = _stroked(fh.read(), line1)

year, le_wm = [], []
with open(Macro.getGlobal("ZA_DATA")) as fh:
    for row in csv.DictReader(fh):
        year.append(float(row["year"]))
        le_wm.append(float(row["le_wmale"]))

doc = {
    "_meta": {
        "stata_version": Macro.getGlobal("ZA_SVER"),
        "born_date": Macro.getGlobal("ZA_BORN"),
        "dash_commit": Macro.getGlobal("ZA_COMMIT"),
        "extracted": Macro.getGlobal("ZA_DATE"),
        "source": "scripts/extract_area_outline_truth.do",
        "read_from": (".Graph.plotregion1.plot<k>.style.area: "
                      "linestyle.color.rgb (line), linestyle.width.val "
                      "(width), shadestyle.color.rgb (fill, before "
                      "intensity); paths: the stroked subpaths of the "
                      "elements of each probe's exported SVG (scheme "
                      "stcolor) whose style strokes plot 1's line colour, "
                      "a <use> resolved to the <path> it names"),
        "probes": {"plain": "twoway area le_wm year",
                   "nodrop": "twoway area le_wm year, nodropbase",
                   "gap": "replace le_wm = . in 40/45; "
                          "twoway area le_wm year, cmissing(n)"},
    },
    "schemes": schemes,
    "lcolor_red": red,
    "paths": paths,
    "data": {"year": year, "le_wm": le_wm},
}
with open(OUT, "w") as fh:
    json.dump(doc, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote", OUT, {k: len(v) for k, v in paths.items()})
end
