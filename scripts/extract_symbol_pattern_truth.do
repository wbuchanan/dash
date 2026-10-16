*! extract_symbol_pattern_truth.do
*! WP-31 S40 (E1, E2, E12): twoway's marker symbols and line patterns.
*!
*! Per probe: the return code, the log's "named style ... not found" note,
*! and the magenta elements of the exported SVG.  A symbol probe records
*! the first marker's elements (tag, fill, stroke, vertex count, bounding
*! box, apex direction); a pattern probe records the on/off lengths of the
*! dashed series in Stata relative units (1 rs = min(width, height)/100 of
*! the graph), read from the line segments twoway's SVG writer emits.
*! The trailing python: block reads the records into
*! test/fixtures/symbol_pattern_truth.json, never calls Stata and starts
*! no subprocess.
*!
*! Run (Stata only through the slot wrapper, never the GUI):
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> \
*!       <repo>/scripts/extract_symbol_pattern_truth.do

* Root: DASH_REPO, else the current directory when it is a dash tree.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_symbol_pattern_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_symbol_pattern_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1

clear all
set more off
set linesize 255
version 19
set graphics off
set scheme s2color

global SP_REPO "`repo'"
local work "`c(tmpdir)'dash_symbol_pattern_probe"
capture mkdir "`work'"
global SP_PDIR "`work'"
global SP_SEQ 0

local stata_version = c(stata_version)
local born_date "`c(born_date)'"
local extracted "`c(current_date)'"
tempfile spgit
quietly shell git -C "${SP_REPO}" rev-parse HEAD > "`spgit'"
tempname spgh
file open `spgh' using "`spgit'", read text
file read `spgh' spline
file close `spgh'
local dash_commit = trim(`"`spline'"')

tempname reg
file open `reg' using "${SP_PDIR}/registry.txt", write text replace
global SP_REG `reg'

* ---- _sp_probe key command ---------------------------------------------
* A numbered file id: keys differ only in case (V, v; O, o) and a
* case-insensitive file system would merge them.
capture program drop _sp_probe
program define _sp_probe
    version 19
    gettoken key 0 : 0
    local command = strtrim(`"`macval(0)'"')
    graph drop _all
    global SP_SEQ = ${SP_SEQ} + 1
    local id "p${SP_SEQ}"
    capture log close sp_probe
    log using "${SP_PDIR}/`id'.log", text replace name(sp_probe)
    capture noisily `command'
    local rc = _rc
    log close sp_probe
    if `rc' == 0 {
        graph export "${SP_PDIR}/`id'.svg", as(svg) replace
    }
    file write ${SP_REG} `"`id'"' _tab `"`key'"' _tab `"`rc'"' _n
end

sysuse auto, clear
keep in 1/2
local M `""255 0 255""'

* sym.<name>: Stata's symbols and synonyms, and names twoway does not know
foreach s in O circle Oh D Dh S Sh T Th + plus X V arrow arrowf A a pipe | point p ///
        o d s t oh dh sh th x v smcircle smcircle_hollow smdiamond smdiamond_hollow smsquare ///
        smsquare_hollow smtriangle smtriangle_hollow smplus smx smv lgx i none ///
        star asterisk hexagon hexagon_hollow dot CIRCLE Circle {
    _sp_probe sym.`s' twoway scatter mpg weight, msymbol(`s') mcolor(`M') legend(off)
}
_sp_probe sym.point_large twoway scatter mpg weight, msymbol(point) msize(large) mcolor(`M') legend(off)
_sp_probe sym.O_large twoway scatter mpg weight, msymbol(O) msize(large) mcolor(`M') legend(off)
_sp_probe sym.pipe_angle45 twoway scatter mpg weight, msymbol(pipe) msangle(45) mcolor(`M') legend(off)
_sp_probe sym.T_angle45 twoway scatter mpg weight, msymbol(T) msangle(45) mcolor(`M') legend(off)

* pat.<name>: the 17 style files, solid and two names that are not files
foreach p in blank dash dash_3dot dash_dot dash_dot_dot dot longdash longdash_3dot longdash_dot ///
        longdash_dot_dot longdash_shortdash shortdash shortdash_dot shortdash_dot_dot solid ///
        tight_dot vshortdash shortdot l {
    _sp_probe pat.`p' twoway line mpg weight, lpattern(`p') lcolor(`M') legend(off)
}

* pat.dash_w.<w>: does the pattern scale with the pen width?
foreach w in vvthin medium thick vthick {
    _sp_probe pat.dash_w.`w' twoway line mpg weight, lpattern(dash) lwidth(`w') lcolor(`M') legend(off)
}
_sp_probe pat.dot_w.vthick twoway line mpg weight, lpattern(dot) lwidth(vthick) lcolor(`M') legend(off)

* pat.dash_size.<id>: does it scale with the graph's size (rs)?
_sp_probe pat.dash_size.x8y8 twoway line mpg weight, lpattern(dash) lcolor(`M') legend(off) xsize(8) ysize(8)
_sp_probe pat.dash_size.x8y2 twoway line mpg weight, lpattern(dash) lcolor(`M') legend(off) xsize(8) ysize(2)

* pat.formula.<i>
local i 0
foreach f in "-." "--.." "_" "#" "-_-" "_--_#" "l" "ll" "-x" "Dash" "DASH" {
    local ++i
    _sp_probe pat.formula.f`i' twoway line mpg weight, lpattern("`f'") lcolor(`M') legend(off)
    file write ${SP_REG} "text" _tab "pat.formula.f`i'" _tab `"`f'"' _n
}

* pat.scheme.<i>: a scheme's linepattern p1 (the p1 line's key) holding a
* name, a quoted or bare formula, a name twoway does not know
local i 0
foreach body in `"linepattern p1 dash"' `"linepattern p1 "--..""' `"linepattern p1 --.."' `"linepattern p1 "-x""' `"linepattern p1 Dash"' {
    local ++i
    tempname us
    file open `us' using "scheme-u40s`i'.scheme", write text replace
    file write `us' "#include s2color" _n `"`body'"' _n
    file close `us'
    _sp_probe pat.scheme.s`i' twoway line mpg weight, scheme(u40s`i') lcolor(`M') legend(off)
    file write ${SP_REG} "text" _tab "pat.scheme.s`i'" _tab `"`body'"' _n
    capture erase "scheme-u40s`i'.scheme"
}

* mlp.<p>: the marker outline's pattern
* The Graph window's renderer writes the PNG: a dashed outline there
* differs from the solid one's pixels.
foreach p in dash dot solid {
    _sp_probe mlp.`p' twoway scatter mpg weight, msymbol(Oh) mlpattern(`p') msize(huge) mlwidth(thick) mcolor(`M') legend(off)
    file write ${SP_REG} "setting" _tab "mlp.`p'" _tab "`.Graph.plotregion1.plot1.style.marker.linestyle.pattern.setting'" _n
    graph export "${SP_PDIR}/mlp_`p'.png", as(png) replace width(800)
}

file close ${SP_REG}

python:
import json, math, os, re, sys
import xml.etree.ElementTree as ET
from sfi import Macro

def L(n):
    return Macro.getLocal(n)

repo = Macro.getGlobal("SP_REPO")
pdir = Macro.getGlobal("SP_PDIR")
MAG = "#ff00ff"
_NUM = re.compile(r"-?\d+(?:\.\d+)?")

def style_of(el):
    out = {}
    for part in (el.get("style") or "").split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip().lower()] = v.strip().lower()
    for k in ("fill", "stroke", "stroke-width", "stroke-dasharray"):
        if el.get(k) is not None and k not in out:
            out[k] = el.get(k).strip().lower()
    return out

def magenta(path):
    """(tag, style, points, el) of every element stroked or filled magenta,
    in document order."""
    root = ET.parse(path).getroot()
    vb = [float(v) for v in root.get("viewBox").split()]
    out = []
    parent = {c: pa for pa in root.iter() for c in pa}
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        st = style_of(el)
        if st.get("stroke") != MAG and st.get("fill") != MAG:
            continue
        if tag == "line":
            pts = [(float(el.get("x1")), float(el.get("y1"))),
                   (float(el.get("x2")), float(el.get("y2")))]
        elif tag == "circle":
            cx, cy, r = (float(el.get(k)) for k in ("cx", "cy", "r"))
            pts = [(cx - r, cy - r), (cx + r, cy + r)]
        elif tag == "path":
            nums = [float(v) for v in _NUM.findall(el.get("d") or "")]
            pts = list(zip(nums[0::2], nums[1::2]))
        elif tag == "polyline" or tag == "polygon":
            nums = [float(v) for v in _NUM.findall(el.get("points") or "")]
            pts = list(zip(nums[0::2], nums[1::2]))
        elif tag == "rect":
            x, y, w, h = (float(el.get(k)) for k in ("x", "y", "width", "height"))
            pts = [(x, y), (x + w, y + h)]
        else:
            continue
        tf = []
        node = el
        while node is not None:
            if node.get("transform"):
                tf.append(node.get("transform"))
            node = parent.get(node)
        el.set("_dash_tf", " ".join(tf))
        out.append((tag, st, pts, el))
    return out, vb

def note(pid):
    p = os.path.join(pdir, pid + ".log")
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8", errors="replace") as fh:
        txt = " ".join(ln.strip() for ln in fh)
    m = re.search(r"\(note:\s+(named style .*? not found in class \w+)", txt)
    if m:
        return m.group(1)
    m = re.search(r"([^.]*invalid line pattern[^.]*)", txt)
    return m.group(1).strip() if m else ""

def bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)

def first_marker(els):
    """The elements of the first marker: those whose box centre lies
    within 80 SVG units of the first element's."""
    if not els:
        return []
    x0, y0, x1, y1 = bbox(els[0][2])
    c = ((x0 + x1) / 2, (y0 + y1) / 2)
    keep = []
    for e in els:
        a, b, cc, d = bbox(e[2])
        if abs((a + cc) / 2 - c[0]) < 80 and abs((b + d) / 2 - c[1]) < 80:
            keep.append(e)
    return keep

def symbol_record(els):
    """The first marker: its elements, fill, and the bounding box of its
    stroked geometry (the filled copy twoway writes under an outline is
    half a pen wider), so a factor compares shapes, not pens."""
    m = first_marker(els)
    if not m:
        return {}
    stroked_els = [e for e in m if e[1].get("stroke") not in (None, "none")]
    geo = stroked_els or m
    x0, y0, x1, y1 = bbox([p for e in geo for p in e[2]])
    filled = any(e[1].get("fill") not in (None, "none") for e in m)
    rec = {"tags": [e[0] for e in m],
           "filled": filled, "stroked": bool(stroked_els),
           "vertices": sum(len(e[2]) for e in m if e[0] == "path"),
           "closed": any("z" in (e[3].get("d") or "").lower() for e in m),
           "d": [e[3].get("d") for e in m if e[0] == "path"],
           "bbox_w": round(x1 - x0, 3), "bbox_h": round(y1 - y0, 3),
           "stroke_width": max([float(e[1].get("stroke-width", "0") or 0)
                                for e in m] or [0.0])}
    rec["transform"] = " ".join(t for t in sorted({e[3].get("_dash_tf") for e in m}) if t)
    circles = [float(e[3].get("r")) for e in geo if e[0] == "circle"]
    if circles:
        rec["r"] = max(circles)
    path = [e for e in m if e[0] in ("path", "polygon")]
    if path:
        p = [(round(a, 2), round(b, 2)) for a, b in path[0][2]]
        # The apex: the vertex the path visits most (an arrow's head and
        # shaft meet there), else the middle of three; up when it lies
        # above the box's centre (SVG y grows downward).
        if max(p.count(q) for q in p) > 1:
            top = max(set(p), key=p.count)
        else:
            top = p[1] if len(p) == 3 else min(p, key=lambda q: q[1])
        rec["apex"] = "up" if top[1] < (y0 + y1) / 2 else "down"
    return rec

def pattern_record(els, vb):
    """The on/off run lengths of the dashed series, in rs, from the
    collinear line segments the writer emits (first 24 runs)."""
    rs = min(vb[2], vb[3]) / 100.0
    segs = [e for e in els if e[0] == "line"]
    paths = [e for e in els if e[0] in ("path", "polyline")]
    rec = {"segments": len(segs), "paths": len(paths), "rs_units": rs,
           "stroke_width": max([float(e[1].get("stroke-width", "0") or 0)
                                for e in els] or [0.0]),
           "dasharray": sorted({e[1].get("stroke-dasharray") for e in els
                                if e[1].get("stroke-dasharray")})}
    runs = []
    prev_end = None
    for e in segs[:40]:
        (ax, ay), (bx, by) = e[2]
        if prev_end is not None:
            runs.append(round(math.hypot(ax - prev_end[0],
                                         ay - prev_end[1]) / rs, 4))
        runs.append(round(math.hypot(bx - ax, by - ay) / rs, 4))
        prev_end = (bx, by)
    rec["runs_rs"] = runs[:24]
    return rec

with open(os.path.join(pdir, "registry.txt"), encoding="utf-8") as fh:
    rows = [ln.rstrip("\n").split("\t") for ln in fh if ln.strip()]
texts = {r[1]: r[2] for r in rows if r[0] == "text"}
settings = {r[1]: r[2] for r in rows if r[0] == "setting"}
out = {}
o_h = None
for pid, key, rc in [r for r in rows if r[0] not in ("text", "setting")]:
    rc = int(rc)
    svg = os.path.join(pdir, pid + ".svg")
    els, vb = magenta(svg) if rc == 0 and os.path.exists(svg) else ([], [0, 0, 1, 1])
    rec = {"rc": rc, "note": note(pid)}
    if key.startswith("sym."):
        rec.update(symbol_record(els))
        if key == "sym.O":
            o_h = rec["bbox_h"]
    elif key.startswith("mlp."):
        rec.update(symbol_record(els))
        rec["elements"] = len(first_marker(els))
        rec["dasharray"] = sorted({e[1].get("stroke-dasharray") for e in els
                                   if e[1].get("stroke-dasharray")})
        rec["setting"] = settings.get(key, "")
    else:
        rec.update(pattern_record(els, vb))
    if key in texts:
        rec["text"] = texts[key]
    out[key] = rec
# PNG pixels: does a dashed marker outline differ from the solid one?
try:
    from PIL import Image, ImageChops
    _solid = Image.open(os.path.join(pdir, "mlp_solid.png")).convert("RGB")
    for p in ("dash", "dot"):
        _im = Image.open(os.path.join(pdir, "mlp_%s.png" % p)).convert("RGB")
        _bb = ImageChops.difference(_im, _solid).getbbox()
        out["mlp." + p]["png_differs_from_solid"] = _bb is not None
except ImportError:
    pass
for k, rec in out.items():
    if k.startswith("sym.") and rec.get("bbox_h") and o_h:
        rec["factor"] = round(rec["bbox_h"] / o_h, 3)

# The unit of a pattern number: the dash's first run over the style
# file's 2, per width; constant across widths means the pen width is not
# the unit.
ratios = {}
for w in ("vvthin", "medium", "thick", "vthick"):
    r = out["pat.dash_w." + w]["runs_rs"]
    ratios[w] = round(r[0] / 2.0, 4) if r else None
out["unit_rs_per_number"] = ratios
out["unit_per_width"] = {
    w: round(ratios[w] * out["pat.dash_w." + w]["rs_units"]
             / out["pat.dash_w." + w]["stroke_width"], 4)
    for w in ratios if ratios[w] and out["pat.dash_w." + w]["stroke_width"]}

for f in os.listdir(pdir):
    os.remove(os.path.join(pdir, f))
os.rmdir(pdir)

out["_meta"] = {"stata_version": L("stata_version"),
                "born_date": L("born_date"),
                "dash_commit": L("dash_commit").strip(),
                "extracted": L("extracted"),
                "units": "SVG 720 units per inch; runs_rs in Stata relative units, 1 rs = min(width, height)/100 of the graph",
                "source": "scripts/extract_symbol_pattern_truth.do"}
path = os.path.join(repo, "test", "fixtures", "symbol_pattern_truth.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
Macro.setGlobal("SP_N", str(len(out) - 1))
end
display as text "symbol_pattern_truth: wrote ${SP_N} records"
