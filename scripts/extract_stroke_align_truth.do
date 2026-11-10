*! extract_stroke_align_truth.do
*! WP-47 section 47-03 (basic:PT-4, basic:PT-6, basic:PT-5): where twoway
*! lays the outline of a bar, histogram bin, rbar, area, rarea, marker and
*! dot under lalign(), mlalign() and dlalign() (inside, center, outside and
*! the scheme's default), the line caps of rcap, and what twoway prints for
*! an alignment word it does not know.
*!
*! Each probe is exported as SVG and read back: for a rectangle the fill
*! rect and the outline rect (x, y, w, h, stroke width); for a marker or a
*! dot the fill circle's r, the outline circle's r and its stroke width;
*! for an area or rarea the stroked path's width and its clip (the shape,
*! the shape's outside by evenodd, or none); for rcap every line's
*! stroke-linecap.  Probes are run under scheme(stcolor) (keys _st) and
*! scheme(s2color) (keys _s2); the schemes' alignstroke entries are read
*! from their files with findfile.
*!
*! Output: test/fixtures/stroke_align_truth.json
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_stroke_align_truth.do
*!
*! Never calls back into Stata from the trailing python: block; a backtick
*! inside it is spelled \x60.
*! ---------------------------------------------------------------------------

clear all
set graphics off
set more off
set linesize 255

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zs_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zs_bad' {
    display as error "extract_stroke_align_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zs_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zs_rc' | _rc {
    local _zs_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_stroke_align_truth.do: `_zs_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZS_REPO "`repo'"
global ZS_OUT  "`repo'/test/fixtures/stroke_align_truth.json"

local work "`c(tmpdir)'dash_stroke_align_probe"
capture mkdir "`work'"
global ZS_WORK "`work'"

global ZS_SVER = c(stata_version)
global ZS_BORN = c(born_date)
global ZS_DATE = "`c(current_date)' `c(current_time)'"

tempfile zsgitrev
quietly shell git -C "${ZS_REPO}" rev-parse HEAD > "`zsgitrev'"
tempname zsgfh
file open `zsgfh' using "`zsgitrev'", read text
file read `zsgfh' zsgitline
file close `zsgfh'
global ZS_COMMIT = trim(`"`zsgitline'"')
capture assert ustrregexm(`"${ZS_COMMIT}"', "^[0-9a-f]{40}$")
if _rc {
    display as error "extract_stroke_align_truth.do: git rev-parse HEAD did not print a 40-character commit"
    exit 498
}

* The schemes' files, for their alignstroke entries.
quietly findfile scheme-stcolor.scheme
global ZS_SCH_st "`r(fn)'"
quietly findfile scheme-s2color.scheme
global ZS_SCH_s2 "`r(fn)'"

* One probe: its key, the plot command (before the scheme), the export.
capture program drop _zs_probe
program define _zs_probe
    gettoken key 0 : 0
    gettoken sch 0 : 0
    `0' scheme(`sch')
    graph export "${ZS_WORK}/`key'.svg", as(svg) replace
end

local schemes "stcolor s2color"
foreach sch of local schemes {
    local k = cond("`sch'" == "stcolor", "st", "s2")
    sysuse auto, clear
    sort weight
    gen yl = mpg - 3
    gen yh = mpg + 3
    local n 0
    foreach a in inside center outside "" {
        local ++n
        local la = cond("`a'" == "", "", "lalign(`a')")
        local ma = cond("`a'" == "", "", "mlalign(`a')")
        local da = cond("`a'" == "", "", "dlalign(`a')")
        _zs_probe A0`n'_`k' `sch' twoway bar mpg weight in 1/5, lwidth(vthick) barwidth(100) `la'
        local m = `n' + 4
        local m : display %02.0f `m'
        _zs_probe A`m'_`k' `sch' histogram mpg, lwidth(vthick) `la'
        local m = `n' + 8
        local m : display %02.0f `m'
        _zs_probe A`m'_`k' `sch' twoway rbar yl yh weight in 1/5, lwidth(vthick) barwidth(100) `la'
        local m = `n' + 12
        _zs_probe A`m'_`k' `sch' twoway area mpg weight in 1/5, lwidth(vthick) `la'
        local m = `n' + 16
        _zs_probe A`m'_`k' `sch' twoway rarea yl yh weight in 1/5, lwidth(vthick) `la'
        _zs_probe M0`n'_`k' `sch' twoway scatter mpg weight in 1/5, mlwidth(vthick) `ma'
        _zs_probe D0`n'_`k' `sch' twoway dot mpg weight in 1/5, `da'
    }
    _zs_probe A22_`k' `sch' twoway bar mpg weight in 1/5, lwidth(vthick) barwidth(100) base(1) yscale(log)
    _zs_probe A23_`k' `sch' twoway bar mpg weight in 1/5, horizontal lwidth(vthick) barwidth(100) base(1) xscale(log)
    _zs_probe A24_`k' `sch' twoway bar mpg weight in 1/5, lwidth(vthick) barwidth(1)
    _zs_probe C01_`k' `sch' twoway rcap yl yh weight in 1/5, lwidth(vthick)
    sysuse uslifeexp, clear
    _zs_probe A21_`k' `sch' twoway area le_wm year, lwidth(vthick)
}

* The unknown words: rc and every line twoway prints.
sysuse auto, clear
local u 0
foreach c in "scatter mpg weight, lalign(bogus)" "scatter mpg weight, mlalign(bogus)" "dot mpg weight in 1/5, dlalign(bogus)" {
    local ++u
    capture log close _zsu
    quietly log using "${ZS_WORK}/U0`u'.txt", text replace name(_zsu)
    capture noisily twoway `c'
    local rc = _rc
    quietly log close _zsu
    tempname zfh
    file open `zfh' using "${ZS_WORK}/U0`u'.rc", write text replace
    file write `zfh' "`rc'" _n
    file close `zfh'
}
graph drop _all

python:
import json
import re
from sfi import Macro

W = Macro.getGlobal("ZS_WORK")
OUT = Macro.getGlobal("ZS_OUT")
_ATTR = re.compile(r'([\w:-]+)="([^"]*)"')
_NUM = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")


def _style(a):
    out = {}
    for part in a.get("style", "").split(";"):
        k, _, v = part.partition(":")
        if k.strip():
            out[k.strip()] = v.strip()
    return out


def _tags(txt, tag):
    for m in re.finditer(r"<" + tag + r"\b([^>]*)>", txt):
        a = dict(_ATTR.findall(m.group(1)))
        yield a, _style(a)


def _sw(st):
    try:
        return float(st.get("stroke-width", ""))
    except ValueError:
        return None


def _rects(txt):
    rs = []
    for a, st in _tags(txt, "rect"):
        rs.append({"x": float(a.get("x", 0)), "y": float(a.get("y", 0)),
                   "w": float(a.get("width", 0)),
                   "h": float(a.get("height", 0)),
                   "fill": st.get("fill"), "stroke_width": _sw(st)})
    return rs


def _rect_probe(txt):
    """The first plot rect: the first rect stroked at the file's widest
    rect stroke; its fill rect is itself (centred) or the rect before."""
    rs = _rects(txt)
    w = max(r["stroke_width"] or 0 for r in rs)
    for i, r in enumerate(rs):
        if r["stroke_width"] == w:
            if r["fill"] not in (None, "none"):
                fill, out = r, r
            else:
                fill, out = rs[i - 1], r
            keep = ("x", "y", "w", "h")
            return {"fill": {k: fill[k] for k in keep},
                    "outline": {k: out[k] for k in keep},
                    "stroke_width": w}
    return None


def _circle_probe(txt):
    cs = [(float(a["cx"]), float(a["cy"]), float(a["r"]), st)
          for a, st in _tags(txt, "circle")]
    if not cs:
        return None
    cx, cy, r, st = cs[0]
    if _sw(st):
        return {"fill_r": r, "ring_r": r, "stroke_width": _sw(st)}
    nxt = cs[1]
    return {"fill_r": r, "ring_r": nxt[2], "stroke_width": _sw(nxt[3])}


def _path_probe(txt):
    defs = {m.group(1): m.group(2) for m in re.finditer(
        r'<path[^>]*\bid="([^"]+)"[^>]*\bd="([^"]+)"', txt)}
    for a, st in _tags(txt, "use"):
        if st.get("fill") == "none" and _sw(st):
            ref = a.get("xlink:href", "").lstrip("#")
            clip = a.get("clip-path", "")
            kind = "none"
            if clip:
                cid = re.search(r"#([^)]+)\)", clip).group(1)
                blk = re.search(r'<clipPath id="' + re.escape(cid)
                                + r'">(.*?)</clipPath>', txt, re.S).group(1)
                kind = "evenodd" if "evenodd" in blk else "shape"
            return {"stroke_width": _sw(st), "clip": kind,
                    "d": defs.get(ref, "")}
    for a, st in _tags(txt, "use"):
        if _sw(st):
            ref = a.get("xlink:href", "").lstrip("#")
            return {"stroke_width": _sw(st), "clip": "none",
                    "d": defs.get(ref, "")}
    return None


def _caps(txt):
    caps = set()
    for tag in ("line", "path"):
        for a, st in _tags(txt, tag):
            if _sw(st):
                caps.add(st.get("stroke-linecap",
                                a.get("stroke-linecap", "butt")))
    return sorted(caps)


def _read(key):
    with open(W + "/" + key + ".svg", encoding="utf-8") as fh:
        return fh.read()


def _scheme(path):
    out = {}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            p = line.split()
            if len(p) >= 3 and p[0] == "alignstroke":
                out[p[1]] = p[2]
    return out


d = {"_meta": {
    "stata_version": Macro.getGlobal("ZS_SVER"),
    "born_date": Macro.getGlobal("ZS_BORN"),
    "dash_commit": Macro.getGlobal("ZS_COMMIT"),
    "extracted": Macro.getGlobal("ZS_DATE"),
    "source": "scripts/extract_stroke_align_truth.do",
    "aligns": ["inside", "center", "outside", "default"],
    "svg_px_per_pt": "SVG units: 5400 per 7.5in graph, 10 per pt",
}}
d["schemes"] = {"st": _scheme(Macro.getGlobal("ZS_SCH_st")),
                "s2": _scheme(Macro.getGlobal("ZS_SCH_s2"))}
for k in ("st", "s2"):
    for n in range(1, 25):
        key = "A%02d_%s" % (n, k)
        txt = _read(key)
        if 13 <= n <= 21:
            d[key] = _path_probe(txt)
        else:
            d[key] = _rect_probe(txt)
    for n in range(1, 5):
        d["M%02d_%s" % (n, k)] = _circle_probe(_read("M%02d_%s" % (n, k)))
        d["D%02d_%s" % (n, k)] = _circle_probe(_read("D%02d_%s" % (n, k)))
    d["C01_" + k] = {"linecaps": _caps(_read("C01_" + k))}
for u in (1, 2, 3):
    with open(W + "/U%02d.rc" % u) as fh:
        rc = int(fh.read().strip())
    with open(W + "/U%02d.txt" % u, encoding="utf-8") as fh:
        body = fh.read()
    lines, cur = [], None
    for ln in body.splitlines():
        s = ln.strip()
        if s.startswith("(note:") or s.startswith("named style"):
            cur = s
            lines.append(cur)
        elif cur is not None and s and not s.startswith(".") and not s.startswith("name:") and not s.startswith("log"):
            lines[-1] = lines[-1] + " " + s
        else:
            cur = None
    d["U%02d" % u] = {"rc": rc, "lines": lines}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(d, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote " + OUT)
end
