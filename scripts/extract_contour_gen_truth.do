*! extract_contour_gen_truth.do -- WP-37 section 37-03 (TR-13): what
*! twoway__contour_gen gives for the data twoway contour and contourline
*! draw, so dash can run it at export and draw twoway's own polygons.
*!
*! WHY THIS EXISTS
*!
*! dash fitted every contour above 1,000 distinct points on a seeded
*! subsample (every sandstone help example).  twoway runs its generator,
*! twoway__contour_gen, on the plot's rows at the cuts it draws (the z
*! axis's interior ticks, levels() or ccuts()).  This script records, per
*! probe: the cuts twoway drew (.plot1.lastcuts after a drawn graph), the
*! generator's output at those cuts (rc, rows, seconds, whether the
*! polygon runs come in non-decreasing levels, polygons and vertices per
*! band or polylines per cut, the first 200 rows, an MD5 of every row in
*! %21x), and whether those cuts equal dash's own rule
*! (_dash_contour_cuts) on the same z range.  grid40 and grid40.line keep
*! every row, for the renderer tests.  sandstone.outlines reads the black
*! strokes twoway's SVG draws under outlines (cut lines or band rings);
*! sandstone.by draws contour and contourline under by(half) and reads
*! each panel's derived serset (its cuts and polygons per band) beside the
*! generator run on that panel's rows.
*!
*! Output: test/fixtures/contour_gen_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_contour_gen_truth.do
*!
*! The git commit is read from a file shell wrote, never with shell=True;
*! the trailing python: block never calls back into Stata.
*! ---------------------------------------------------------------------------

clear all
set more off
set linesize 200

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_cg_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_cg_bad' {
    display as error "extract_contour_gen_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _cg_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_cg_rc' | _rc {
    local _cg_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_contour_gen_truth.do: `_cg_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global CG_REPO "`repo'"
global CG_OUT "${CG_REPO}/test/fixtures/contour_gen_truth.json"
global dash_nobrowser 1

local work "`c(tmpdir)'dash_contour_gen_probe"
capture mkdir "`work'"
global CG_WORK "`work'"

quietly shell git -C "${CG_REPO}" rev-parse HEAD > "${CG_WORK}/git_head.txt"
global CG_VERSION "`c(stata_version)'"
global CG_BORN "`c(born_date)'"
global CG_WHEN "`c(current_date)' `c(current_time)'"
set scheme stcolor
global CG_KEYS ""

* ---- One record file: "key<TAB>field<TAB>value" lines; the generator's
* rows go to <key>.rows.txt (%21.17g, "." for missing) and
* <key>.hex.txt (%21x, the MD5's input).
capture file close cgf
file open cgf using "${CG_WORK}/records.txt", write text replace

mata:
void cg_rows(string scalar key, string scalar vars)
{
    real matrix M
    real scalar fh, fx, r, c
    string scalar a, b
    M = st_data(., tokens(vars))
    if (fileexists(key + ".rows.txt")) unlink(key + ".rows.txt")
    if (fileexists(key + ".hex.txt")) unlink(key + ".hex.txt")
    fh = fopen(key + ".rows.txt", "w")
    fx = fopen(key + ".hex.txt", "w")
    for (r = 1; r <= rows(M); r++) {
        a = ""
        b = ""
        for (c = 1; c <= cols(M); c++) {
            a = a + (c > 1 ? " " : "") +
                (M[r, c] >= . ? "." : strtrim(sprintf("%21.17g", M[r, c])))
            b = b + (c > 1 ? " " : "") + strtrim(sprintf("%21x", M[r, c]))
        }
        fput(fh, a)
        fput(fx, b)
    }
    fclose(fh)
    fclose(fx)
}
end

* _cg_gen key isline interp cuts : run the generator on the data in memory
* (under preserve) at the cuts, record rc, rows, seconds and the rows.
capture program drop _cg_gen
program define _cg_gen
    args key isline interp cuts z y x
    local line = cond(`isline', "line", "")
    preserve
    timer clear 37
    timer on 37
    capture noisily twoway__contour_gen `z' `y' `x', cuts(`cuts') gen(__z __y __x __l) interp(`interp') `line'
    local rc = _rc
    timer off 37
    quietly timer list 37
    local secs = r(t37)
    file write cgf "`key'" _tab "gen_rc" _tab "`rc'" _n
    file write cgf "`key'" _tab "seconds" _tab "`secs'" _n
    if !`rc' {
        file write cgf "`key'" _tab "rows" _tab "`=_N'" _n
        mata: cg_rows("${CG_WORK}/`key'", "__x __y __z __l")
    }
    restore
end

* _cg_probe key isline z y x interp [, twoway options] : draw the graph,
* read the cuts it drew, run the generator at them.
capture program drop _cg_probe
program define _cg_probe
    gettoken key 0 : 0
    gettoken isline 0 : 0
    gettoken z 0 : 0
    gettoken y 0 : 0
    gettoken x 0 : 0
    gettoken interp 0 : 0, parse(" ,")
    gettoken comma 0 : 0, parse(",")
    local opts `0'
    local tw = cond(`isline', "contourline", "contour")
    local io = cond("`interp'" == "default", "", "interp(`interp')")
    capture graph drop cg
    twoway `tw' `z' `y' `x', `opts' `io' name(cg)
    local cuts `.cg.plotregion1.plot1.lastcuts'
    file write cgf "`key'" _tab "cuts" _tab "`cuts'" _n
    file write cgf "`key'" _tab "command" _tab "twoway `tw' `z' `y' `x', `opts' `io'" _n
    file write cgf "`key'" _tab "opts" _tab "`opts' `io'" _n
    quietly summarize `z'
    file write cgf "`key'" _tab "zmin" _tab "`=strofreal(r(min), "%21.17g")'" _n
    file write cgf "`key'" _tab "zmax" _tab "`=strofreal(r(max), "%21.17g")'" _n
    file write cgf "`key'" _tab "n" _tab "`=r(N)'" _n
    file write cgf "`key'" _tab "line" _tab "`isline'" _n
    local gi = cond("`interp'" == "default", "thinplatespline", "`interp'")
    _cg_gen `key' `isline' `gi' "`cuts'" `z' `y' `x'
    global CG_KEYS "${CG_KEYS} `key'"
    capture graph drop cg
end

* ---- sandstone: 6,400 points on an 80 x 80 grid.
sysuse sandstone, clear
local s "depth northing easting"
_cg_probe sandstone.default 0 `s' default
_cg_probe sandstone.default.line 1 `s' default
_cg_probe sandstone.levels10 0 `s' default, levels(10)
_cg_probe sandstone.levels10.line 1 `s' default, levels(10)
_cg_probe sandstone.ccuts 0 `s' default, ccuts(7600(100)8000)
_cg_probe sandstone.ccuts.line 1 `s' default, ccuts(7600(100)8000)
_cg_probe sandstone.none 0 `s' none
_cg_probe sandstone.none.line 1 `s' none

* ---- sandstone.outlines: twoway's boundaries under outlines, from its SVG.
capture graph drop cg
twoway contour depth northing easting, outlines name(cg)
quietly graph export "${CG_WORK}/outlines.svg", as(svg) replace
capture graph drop cg

* ---- sandstone.by: two 80 x 40 grids under by(half).
summarize northing, detail
generate byte half = northing > r(p50)
foreach tw in contour contourline {
    capture graph drop cg
    twoway `tw' depth northing easting, by(half) name(cg)
    * Each panel's cuts: its own plot's lastcuts (.graphs[p], p = 1 for
    * half == 0).
    forvalues p = 1/2 {
        file write cgf "by.`tw'.`=`p'-1'" _tab "cuts" _tab "`.cg.graphs[`p'].plotregion1.plot1.lastcuts'" _n
    }
    * Each derived serset (z y x levels) is one panel's; its northing
    * range names the panel.
    serset dir
    local nser = 0
    forvalues k = 0/40 {
        capture serset set `k'
        if _rc continue
        preserve
        quietly serset use, clear
        quietly ds
        if "`r(varlist)'" != "z y x levels" {
            restore
            continue
        }
        quietly summarize y
        local v = (r(min) > 73770)
        file write cgf "by.`tw'.`v'" _tab "rows" _tab "`=_N'" _n
        mata: cg_rows("${CG_WORK}/by.`tw'.`v'", "x y z levels")
        restore
        local ++nser
    }
    file write cgf "by.`tw'" _tab "sersets" _tab "`nser'" _n
    if "`tw'" == "contour" {
        forvalues p = 1/2 {
            global CG_BYCUTS_`=`p'-1' "`.cg.graphs[`p'].plotregion1.plot1.lastcuts'"
        }
    }
    capture graph drop cg
}

* The generator on each panel's own rows at the cuts that panel drew.
forvalues v = 0/1 {
    preserve
    quietly keep if half == `v'
    _cg_gen by.gen.`v' 0 thinplatespline "${CG_BYCUTS_`v'}" depth northing easting
    file write cgf "by.gen.`v'" _tab "cuts" _tab "${CG_BYCUTS_`v'}" _n
    file write cgf "by.gen.`v'" _tab "n" _tab "`=_N'" _n
    restore
}

* ---- grid40: a 40 x 40 grid.
clear
set obs 1600
generate double x = mod(_n - 1, 40)
generate double y = floor((_n - 1) / 40)
generate double z = sin(x / 6) + cos(y / 7)
_cg_probe grid40 0 z y x default
_cg_probe grid40.line 1 z y x default

* ---- scatter100.none: 100 scattered points with interp(none).
clear
set obs 100
set seed 20261020
generate double x = runiform()
generate double y = runiform()
generate double z = runiform()
_cg_probe scatter100.none 0 z y x none
file close cgf

python:
import hashlib, json, os, sys
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


work = G("CG_WORK")
repo = G("CG_REPO")
sys.path.insert(0, os.path.join(repo, "scripts"))
sys.path.insert(0, repo)
import svg_truth  # noqa: E402

rec = {}
with open(os.path.join(work, "records.txt"), encoding="utf-8") as fh:
    for ln in fh:
        ln = ln.rstrip("\n")
        if not ln:
            continue
        k, f, v = (ln.split("\t") + ["", ""])[:3]
        rec.setdefault(k, {})[f] = v


def num(s):
    return None if s == "." else float(s)


def rows_of(key):
    with open(os.path.join(work, key + ".rows.txt"), encoding="utf-8") as fh:
        return [[num(t) for t in ln.split()] for ln in fh if ln.strip()]


def md5_of(key):
    with open(os.path.join(work, key + ".hex.txt"), "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def runs(rows):
    """[(level, nvertices)] per run of rows ended by an all-missing row."""
    out, cur = [], []
    for r in rows:
        if all(v is None for v in r):
            if cur:
                out.append((cur[0][3], len(cur)))
            cur = []
        else:
            cur.append(r)
    if cur:
        out.append((cur[0][3], len(cur)))
    return out


def per_level(rs, n):
    polys = [0] * n
    verts = [0] * n
    for lev, nv in rs:
        i = int(lev) - 1
        if 0 <= i < n:
            polys[i] += 1
            verts[i] += nv
    return polys, verts


def cuts_of(s):
    return [float(t) for t in s.split()]


def dash_cuts(opts, zmin, zmax):
    """dash's own rule (_dash_contour_cuts) on the same z range."""
    try:
        import dash_render as dr
    except Exception as e:  # noqa: BLE001
        print("dash_render not importable:", e)
        return None
    o = {}
    zo = {}
    for tok in opts.split():
        if tok.startswith("levels("):
            o["levels"] = tok[7:-1]
        elif tok.startswith("ccuts("):
            o["ccuts"] = " ".join(repr(v) for v in _numlist(tok[6:-1]))
        elif tok == "minmax":
            o["minmax"] = "minmax"
    cuts, _t = dr._dash_contour_cuts(o, zmin, zmax, zo)
    return [float(c) for c in cuts]


def _numlist(s):
    # a(b)c only (the probes' one form)
    a, rest = s.split("(", 1)
    b, c = rest.split(")", 1)
    a, b, c = float(a), float(b), float(c)
    out, v = [], a
    while v <= c + 1e-9 * abs(c):
        out.append(v)
        v += b
    return out


def same(a, b):
    if a is None or b is None or len(a) != len(b):
        return False
    return all(abs(x - y) <= 1e-9 * max(1.0, abs(x), abs(y))
               for x, y in zip(a, b))


out = {}
for key in G("CG_KEYS").split():
    d = rec.get(key, {})
    line = d.get("line") == "1"
    cuts = cuts_of(d.get("cuts", ""))
    o = {"command": d.get("command", ""), "cuts": cuts,
         "gen_rc": int(d.get("gen_rc", "-1")),
         "seconds": float(d.get("seconds") or "nan"),
         "n": int(d.get("n", "0")), "line": int(line),
         "zmin": float(d["zmin"]), "zmax": float(d["zmax"])}
    if o["gen_rc"] == 0:
        rows = rows_of(key)
        rs = runs(rows)
        o["row_count"] = len(rows)
        o["runs"] = len(rs)
        levs = [lv for lv, _n in rs]
        o["levels_nondecreasing"] = int(all(levs[i] <= levs[i + 1]
                                            for i in range(len(levs) - 1)))
        if line:
            p, v = per_level(rs, len(cuts))
            o["lines_per_cut"] = p
            o["vertices_per_cut"] = v
        else:
            p, v = per_level(rs, len(cuts) + 1)
            o["polys_per_band"] = p
            o["vertices_per_band"] = v
        o["first_rows"] = rows[:200]
        o["md5"] = md5_of(key)
        if key.startswith("grid40"):
            o["rows"] = rows
    dc = dash_cuts(d.get("opts", ""), o["zmin"], o["zmax"])
    o["dash_cuts"] = dc
    o["cuts_equal_dash"] = int(same(cuts, dc))
    out[key] = o

# sandstone.outlines: black strokes inside the plot region.
doc = svg_truth.svg_document(os.path.join(work, "outlines.svg"))
pr = doc["plotregion"]
segs = []


def inside(x, y):
    return (pr["left"] + 0.5 < x < pr["right"] - 0.5
            and pr["top"] + 0.5 < y < pr["bottom"] - 0.5)


for d in doc["hlines"] + doc["vlines"] + doc["diaglines"]:
    if d.get("stroke") == "#000000" and inside(d["x1"], d["y1"]) \
            and inside(d["x2"], d["y2"]):
        segs.append((d["x1"], d["y1"], d["x2"], d["y2"]))
import re  # noqa: E402
for p in doc["paths"]:
    if p.get("stroke") != "#000000" or not p.get("d"):
        continue
    pts = [(float(a), float(b)) for a, b in
           re.findall(r"[ML]\s*(-?[0-9.]+)[ ,]+(-?[0-9.]+)", p["d"])]
    for (a, b), (c, e) in zip(pts, pts[1:]):
        if inside(a, b) and inside(c, e):
            segs.append((a, b, c, e))
# Stata writes a stroked shape as <use xlink:href="#id" style=...> over a
# <path id=...> in its defs.
_defs = dict(re.findall(r'<path id="([^"]+)" d="([^"]*)"', open(
    os.path.join(work, "outlines.svg"), encoding="utf-8").read()))
for pid, st in re.findall(r'<use xlink:href="#([^"]+)" style="([^"]*)"', open(
        os.path.join(work, "outlines.svg"), encoding="utf-8").read()):
    if "stroke:#000000" not in st.upper().replace("#000000", "#000000"):
        continue
    pts = [(float(a), float(b)) for a, b in
           re.findall(r"[ML]\s*(-?[0-9.]+)[ ,]+(-?[0-9.]+)", _defs.get(pid, ""))]
    for (a, b), (c, e) in zip(pts, pts[1:]):
        if inside(a, b) and inside(c, e):
            segs.append((a, b, c, e))
edge = 0
if segs:
    xs = [s[0] for s in segs] + [s[2] for s in segs]
    ys = [s[1] for s in segs] + [s[3] for s in segs]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    for a, b, c, e in segs:
        for side in ((0, x0), (0, x1), (1, y0), (1, y1)):
            u = (a, c) if side[0] == 0 else (b, e)
            if abs(u[0] - side[1]) <= 0.5 and abs(u[1] - side[1]) <= 0.5:
                edge += 1
                break
out["sandstone.outlines"] = {
    "command": "twoway contour depth northing easting, outlines",
    "segments": len(segs), "edge_segments": edge,
    "outlines_are_cut_lines": int(edge == 0)}

# sandstone.by: each panel's drawn polygons and cuts, and the generator on
# that panel's rows at those cuts.
panels = []
for v in (0, 1):
    cuts = cuts_of(rec.get("by.contour.%d" % v, {}).get("cuts", ""))
    lcuts = cuts_of(rec.get("by.contourline.%d" % v, {}).get("cuts", ""))
    lrows = rows_of("by.contourline.%d" % v)
    lp, _v = per_level(runs(lrows), len(lcuts))
    frows = rows_of("by.contour.%d" % v)
    p, _v = per_level(runs(frows), len(cuts) + 1)
    g = rec.get("by.gen.%d" % v, {})
    gp = None
    if g.get("gen_rc") == "0":
        gp, _v = per_level(runs(rows_of("by.gen.%d" % v)), len(cuts) + 1)
    panels.append({"half": v, "n": int(g.get("n", "0")), "cuts": cuts,
                   "line_cuts": lcuts, "lines_per_cut": lp,
                   "polys_per_band": p, "gen_polys_per_band": gp,
                   "gen_rc": int(g.get("gen_rc", "-1"))})
out["sandstone.by"] = {
    "command": "twoway contour depth northing easting, by(half) "
               "(half = northing > its median)",
    "sersets": [int(rec.get("by.contour", {}).get("sersets", "0")),
                int(rec.get("by.contourline", {}).get("sersets", "0"))],
    "panels": panels,
    "first_panel_rule": int(all(same(p["cuts"], panels[0]["cuts"])
                                and same(p["line_cuts"], panels[0]["cuts"])
                                for p in panels))}

try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("CG_VERSION"), "born_date": G("CG_BORN"),
                "dash_commit": commit, "extracted": G("CG_WHEN"),
                "source": "scripts/extract_contour_gen_truth.do"}
with open(G("CG_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, separators=(",", ":"), sort_keys=True)
    fh.write("\n")
for f in os.listdir(work):
    try:
        os.remove(os.path.join(work, f))
    except OSError:
        pass
print("wrote", G("CG_OUT"))
for k in sorted(out):
    if k == "_meta":
        continue
    o = out[k]
    print(k, {f: o.get(f) for f in ("cuts", "gen_rc", "seconds", "row_count",
                                     "levels_nondecreasing", "cuts_equal_dash",
                                     "polys_per_band", "lines_per_cut",
                                     "edge_segments", "first_panel_rule")
              if f in o})
end
