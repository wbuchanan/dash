*! extract_contour_outlines_truth.do -- WP-37 TR-13a (ruling D64): what
*! twoway contour draws under its outlines and heatmap options, and what
*! twoway contourline draws under them.
*!
*! WHY THIS EXISTS
*!
*! WP-32 drew outlines as black boundary lines at the cuts inside the plot
*! region.  37-03 found twoway's SVG under outlines has no black stroke in
*! the plot region.  This script exports each probe's graph as SVG and
*! records, per probe: its rc; the colour key's boxes (the filled shapes
*! right of the plot region, in document order: fill, stroke and stroke
*! width); the filled shapes inside the plot region, how many are
*! axis-aligned rectangles, and an MD5 of their geometry and styles
*! (path ids aside); the black strokes inside the plot region; and, for
*! contourline, an MD5 of its lines; and "malformed", the paths whose d
*! attribute holds markup (see the alpattern() probes).  The "same_plot_as" field names the
*! plain probe whose plot region it draws identically.
*!
*! Output: test/fixtures/contour_outlines_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_contour_outlines_truth.do
*!
*! CO_KEEP=1 in the environment keeps the work folder's SVGs.
*! The git commit is read from a file shell wrote, never with shell=True;
*! the trailing python: block never calls back into Stata.
*! ---------------------------------------------------------------------------

clear all
set more off
set linesize 200

* Root: DASH_REPO, else the current directory when it is a dash tree;
* never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_co_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_co_bad' {
    display as error "extract_contour_outlines_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _co_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_co_rc' | _rc {
    local _co_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_contour_outlines_truth.do: `_co_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global CO_REPO "`repo'"
global CO_OUT "${CO_REPO}/test/fixtures/contour_outlines_truth.json"

local work "`c(tmpdir)'dash_contour_outlines_probe"
capture mkdir "`work'"
global CO_WORK "`work'"

quietly shell git -C "${CO_REPO}" rev-parse HEAD > "${CO_WORK}/git_head.txt"
global CO_VERSION "`c(stata_version)'"
global CO_BORN "`c(born_date)'"
global CO_WHEN "`c(current_date)' `c(current_time)'"
set scheme stcolor

capture file close cof
file open cof using "${CO_WORK}/records.txt", write text replace

* _co_probe key type z y x [, options] : draw, export, record rc and command.
capture program drop _co_probe
program define _co_probe
    gettoken key 0 : 0
    gettoken tw 0 : 0
    gettoken z 0 : 0
    gettoken y 0 : 0
    gettoken x 0 : 0, parse(" ,")
    gettoken comma 0 : 0, parse(",")
    local opts `0'
    capture graph drop co
    capture noisily twoway `tw' `z' `y' `x', `opts' name(co)
    local rc = _rc
    file write cof "`key'" _tab "rc" _tab "`rc'" _n
    file write cof "`key'" _tab "command" _tab "twoway `tw' `z' `y' `x'`=cond(`"`opts'"' != "", ", ", "")'`opts'" _n
    if !`rc' {
        file write cof "`key'" _tab "cuts" _tab "`.co.plotregion1.plot1.lastcuts'" _n
        capture erase "${CO_WORK}/`key'.svg"
        quietly graph export "${CO_WORK}/`key'.svg", as(svg) replace
    }
    capture graph drop co
end

* ---- sandstone: 6,400 points on an 80 x 80 grid (37-03 draws it from
* twoway's generator).
sysuse sandstone, clear
local s "depth northing easting"
_co_probe ss.default contour `s'
_co_probe ss.outlines contour `s', outlines
_co_probe ss.heatmap contour `s', heatmap
_co_probe ss.outlines_heatmap contour `s', outlines heatmap
_co_probe ss.ccuts contour `s', ccuts(7600(100)8000)
_co_probe ss.outlines_ccuts contour `s', outlines ccuts(7600(100)8000)
_co_probe ss.heatmap_ccuts contour `s', heatmap ccuts(7600(100)8000)
_co_probe ss.none contour `s', interp(none)
_co_probe ss.outlines_none contour `s', outlines interp(none)
_co_probe ss.line contourline `s'
_co_probe ss.line_outlines contourline `s', outlines
_co_probe ss.line_heatmap contourline `s', heatmap

* ---- auto: 74 scattered points (dash fits these itself).
sysuse auto, clear
local a "price mpg weight"
_co_probe au.default contour `a'
_co_probe au.outlines contour `a', outlines
_co_probe au.heatmap contour `a', heatmap
_co_probe au.none contour `a', interp(none)
_co_probe au.outlines_none contour `a', outlines interp(none)
_co_probe au.heatmap_none contour `a', heatmap interp(none)
_co_probe au.line contourline `a'
_co_probe au.line_outlines contourline `a', outlines
_co_probe au.line_heatmap contourline `a', heatmap

* ---- grid5: a 5 x 5 grid, z = x + y.
clear
set obs 25
generate double x = mod(_n - 1, 5)
generate double y = floor((_n - 1) / 5)
generate double z = x + y
_co_probe g5.default contour z y x
_co_probe g5.outlines contour z y x, outlines
_co_probe g5.heatmap contour z y x, heatmap

* ---- s2color: the key boxes' outline is twice s2color's medium line.
set scheme s2color
sysuse auto, clear
_co_probe s2.default contour `a'
_co_probe s2.outlines contour `a', outlines
set scheme stcolor

* ---- alpattern() last: Stata 19.5's SVG writer, after exporting a
* contour with alpattern(), writes each later polygon's boundary <line>
* inside its path's d attribute (measured 29oct2026: every later export
* of the session).  The records count such paths as "malformed".
sysuse sandstone, clear
_co_probe ss.alpattern contour `s', alpattern(dash)
_co_probe ss.outlines_alpattern contour `s', outlines alpattern(dash)
file close cof

python:
import hashlib, json, os, re, sys
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


work = G("CO_WORK")
repo = G("CO_REPO")
sys.path.insert(0, os.path.join(repo, "scripts"))
import svg_truth  # noqa: E402

rec = {}
order = []
with open(os.path.join(work, "records.txt"), encoding="utf-8") as fh:
    for ln in fh:
        ln = ln.rstrip("\n")
        if not ln:
            continue
        k, f, v = (ln.split("\t") + ["", ""])[:3]
        if k not in rec:
            order.append(k)
        rec.setdefault(k, {})[f] = v

_NUM = r"(-?[0-9.]+)"
_PT = re.compile(r"[ML]\s*" + _NUM + r"[ ,]+" + _NUM)


def style(s):
    out = {}
    for part in (s or "").split(";"):
        if ":" in part:
            a, b = part.split(":", 1)
            out[a.strip()] = b.strip().lower()
    return out


def shapes(txt):
    """[(points, d, style)] of every <use> of a defined path, in order."""
    defs = dict(re.findall(r'<path id="([^"]+)" d="([^"]*)"', txt))
    out = []
    for pid, st in re.findall(
            r'<use xlink:href="#([^"]+)"[^>]*? style="([^"]*)"', txt):
        d = defs.get(pid, "")
        pts = [(float(a), float(b)) for a, b in _PT.findall(d)]
        out.append((pts, d, style(st)))
    return out


def is_rect(pts):
    if len(pts) < 4:
        return False
    pts = pts[-5:]
    xs = sorted({round(p[0], 2) for p in pts})
    ys = sorted({round(p[1], 2) for p in pts})
    return len(xs) == 2 and len(ys) == 2


def read(key):
    path = os.path.join(work, key + ".svg")
    txt = open(path, encoding="utf-8").read()
    pr = svg_truth.svg_document(path)["plotregion"]

    def inside(x, y):
        return (pr["left"] + 0.5 < x < pr["right"] - 0.5
                and pr["top"] + 0.5 < y < pr["bottom"] - 0.5)

    key_boxes, plot = [], []
    for pts, d, st in shapes(txt):
        if not pts:
            continue
        if all(p[0] > pr["right"] for p in pts):
            if st.get("fill", "none") != "none":
                key_boxes.append({"fill": st["fill"], "rect": int(is_rect(pts)),
                                  "stroke": None, "stroke_width": None})
            elif key_boxes and st.get("stroke", "none") != "none":
                key_boxes[-1]["stroke"] = st["stroke"]
                key_boxes[-1]["stroke_width"] = float(st.get("stroke-width", "0"))
        elif any(p[0] <= pr["right"] for p in pts):
            # The plot region's shapes (a heatmap cell's path may open with
            # a move to the region's corner).
            plot.append((pts, d, st))
    filled = [s for s in plot if s[2].get("fill", "none") != "none"]
    strokes = [s for s in plot if s[2].get("stroke", "none") != "none"]
    black = sum(1 for s in strokes if s[2]["stroke"] == "#000000")
    for ln in re.findall(r"<line ([^>]*)/>", txt):
        a = dict(re.findall(r'(\w[\w-]*)="([^"]*)"', ln))
        st = style(a.get("style"))
        try:
            x1, y1, x2, y2 = (float(a[k]) for k in ("x1", "y1", "x2", "y2"))
        except (KeyError, ValueError):
            continue
        if st.get("stroke") == "#000000" and inside(x1, y1) and inside(x2, y2):
            black += 1
    stroke_kinds = {}
    for s in strokes:
        k = "%s %s" % (s[2]["stroke"], s[2].get("stroke-width", ""))
        stroke_kinds[k] = stroke_kinds.get(k, 0) + 1
    geo = hashlib.md5("\n".join(sorted(
        "%s|%s|%s|%s" % (d, s.get("fill", ""), s.get("stroke", ""),
                         s.get("stroke-width", ""))
        for _p, d, s in plot)).encode()).hexdigest()
    lines = [ln for ln in re.findall(r"<line ([^>]*)/>", txt)]
    plines = []
    for ln in lines:
        a = dict(re.findall(r'(\w[\w-]*)="([^"]*)"', ln))
        try:
            x1, y1, x2, y2 = (float(a[k]) for k in ("x1", "y1", "x2", "y2"))
        except (KeyError, ValueError):
            continue
        if inside(x1, y1) and inside(x2, y2):
            plines.append(ln)
    return {
        "malformed": len(re.findall(r'd="[^"]*<', txt)),
        "key_boxes": key_boxes,
        "plot_filled": len(filled),
        "plot_filled_rects": sum(1 for s in filled if is_rect(s[0])),
        "plot_black_strokes": black,
        "plot_stroke_kinds": stroke_kinds,
        "plot_md5": geo,
        "plot_lines": len(plines),
        "plot_lines_md5": hashlib.md5("\n".join(sorted(plines)).encode()).hexdigest(),
    }


out = {}
for k in order:
    r = rec[k]
    o = {"rc": int(r["rc"]), "command": r["command"]}
    if o["rc"] == 0:
        o["cuts"] = [float(t) for t in r.get("cuts", "").split()]
        o.update(read(k))
    out[k] = o

# The plain probe each draws its plot region as.
for k, o in out.items():
    if "plot_md5" not in o:
        continue
    same = [p for p in order if p != k and out[p].get("plot_md5") == o["plot_md5"]
            and out[p].get("plot_lines_md5") == o["plot_lines_md5"]]
    o["same_plot_as"] = sorted(same)

try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("CO_VERSION"), "born_date": G("CO_BORN"),
                "dash_commit": commit, "extracted": G("CO_WHEN"),
                "scheme": "stcolor (s2.*: s2color)",
                "source": "scripts/extract_contour_outlines_truth.do"}
with open(G("CO_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
for f in ([] if os.environ.get("CO_KEEP") else os.listdir(work)):
    try:
        os.remove(os.path.join(work, f))
    except OSError:
        pass
print("wrote", G("CO_OUT"))
for k in order:
    o = out[k]
    print(k, {f: o.get(f) for f in ("rc", "plot_filled", "plot_filled_rects",
                                     "plot_black_strokes", "plot_lines",
                                     "same_plot_as")},
          [(b["fill"], b["stroke"], b["stroke_width"]) for b in o.get("key_boxes", [])])
end
