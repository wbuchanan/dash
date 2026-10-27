*! extract_geometry_truth.do -- measure twoway's graph size and plot
*! region geometry (S10): xsize()/ysize() in inches (the EPS bounding box,
*! the saved .gph header, a PNG export's pixel size), graph describe's
*! r(xsize)/r(ysize) under each scheme and option, the r(198) of an unusable
*! size, aspectratio()'s plot region from .Graph.plotregion1.xsize_ren and
*! .ysize_ren, and a scheme's bare and x/y graphsize entries.  On sysuse
*! auto, twoway scatter mpg weight.  twoway only: the output is the same
*! before and after dash changes.  Probe files are written to c(tmpdir) and
*! named in the fixture by basename only.
*!
*! Output: test/fixtures/geometry_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_geometry_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.
clear all
set more off
set linesize 200

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zg_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zg_bad' {
    display as error "extract_geometry_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zg_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zg_rc' | _rc {
    local _zg_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_geometry_truth.do: `_zg_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZG_REPO "`repo'"
global ZG_OUT "${ZG_REPO}/test/fixtures/geometry_truth.json"

adopath ++ "${ZG_REPO}"
global dash_nobrowser 1

local work "`c(tmpdir)'dash_geometry_probe"
capture mkdir "`work'"
global ZG_WORK "`work'"


quietly shell git -C "${ZG_REPO}" rev-parse HEAD > "${ZG_WORK}/git_head.txt"
global ZG_VERSION "`c(stata_version)'"
global ZG_BORN "`c(born_date)'"
global ZG_WHEN "`c(current_date)' `c(current_time)'"
global ZG_DEFAULT "`c(scheme)'"

sysuse auto, clear

* _zg_size key opts: draw twoway scatter mpg weight, <opts> as graph zg and
* leave graph describe's "xsize ysize" in global ZG_S_<key>.
capture program drop _zg_size
program define _zg_size
    gettoken key 0 : 0
    capture graph drop zg
    quietly twoway scatter mpg weight, `0' name(zg)
    quietly graph describe zg
    global ZG_S_`key' "`r(xsize)' `r(ysize)'"
    display as text "ZG `key': `r(xsize)' x `r(ysize)'"
end

* Scheme defaults.
local schemes "stcolor stcolor_alt stgcolor stmono1 stmono2 stsj s1color s1mono s1rcolor s2color s2mono s2gcolor sj economist"
global ZG_SCHEMES "`schemes'"
foreach s of local schemes {
    _zg_size sch_`s' scheme(`s')
}

* The fixture cases (under the installation's default scheme).
set scheme stcolor
_zg_size c1 xsize(6) ysize(4)
_zg_size c2 xsize(10) ysize(2)
_zg_size c3 xsize(9)
_zg_size c4
_zg_size c5 aspectratio(0.5)
_zg_size y9 ysize(9)

* An unusable size.
foreach v in 0 -3 {
    capture graph drop zg
    capture twoway scatter mpg weight, xsize(`v') name(zg)
    global ZG_RC_`=cond(`v' < 0, "m3", "0")' = _rc
}

* Units: a 6 x 4 graph exported to EPS and PNG width(600), saved as .gph,
* and graph describe's size line.
capture graph drop zg
quietly twoway scatter mpg weight, xsize(6) ysize(4) name(zg)
quietly graph export "${ZG_WORK}/geometry_6x4.eps", name(zg) replace
quietly graph export "${ZG_WORK}/geometry_6x4.png", name(zg) width(600) replace
quietly graph save zg "${ZG_WORK}/geometry_6x4.gph", replace
quietly log using "${ZG_WORK}/geometry_describe.log", text replace name(zglog)
graph describe zg
quietly log close zglog
capture graph drop zg
quietly twoway scatter mpg weight, aspectratio(0.5) name(zg)
quietly graph save zg "${ZG_WORK}/geometry_ar05.gph", replace

* aspectratio(): the plot region of a 6 x 6 graph.
foreach a in 0.25 1 4 {
    capture graph drop zg
    quietly twoway scatter mpg weight, xsize(6) ysize(6) aspectratio(`a') name(zg)
    global ZG_AR_`=subinstr("`a'", ".", "_", .)' "`.zg.plotregion1.xsize_ren' `.zg.plotregion1.ysize_ren'"
    display as text "ZG ar `a': `.zg.plotregion1.xsize_ren' x `.zg.plotregion1.ysize_ren'"
}

* A scheme's bare graphsize, and graphsize y alone.
tempname fh
file open `fh' using "${ZG_WORK}/scheme-zgbare.scheme", write text replace
file write `fh' "#include s2color" _n "graphsize 3" _n
file close `fh'
file open `fh' using "${ZG_WORK}/scheme-zgy.scheme", write text replace
file write `fh' "#include s2color" _n "graphsize y 2" _n
file close `fh'
adopath ++ "${ZG_WORK}"
_zg_size bare scheme(zgbare)
_zg_size gy scheme(zgy)
graph drop _all

* Stata's own aspect convention (matrixgraph_g.class).
quietly findfile matrixgraph_g.class
global ZG_MGCLASS "`r(fn)'"

python:
import json, os, re, struct
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


def size(key):
    x, y = (float(v) for v in G("ZG_S_" + key).split())
    return x, y


def num(v):
    return int(v) if v == int(v) else v


work = G("ZG_WORK")
with open(os.path.join(work, "geometry_6x4.eps"), encoding="latin-1") as fh:
    bbox = next(l.strip() for l in fh if l.startswith("%%BoundingBox:"))
bb = [float(v) for v in bbox.split()[1:]]
with open(os.path.join(work, "geometry_6x4.png"), "rb") as fh:
    head = fh.read(24)
pw, ph = struct.unpack(">II", head[16:24])
with open(os.path.join(work, "geometry_6x4.gph"), encoding="latin-1") as fh:
    gph = fh.read()
gx = re.search(r"^\*! xsize: (\S+)", gph, re.M).group(1)
gy = re.search(r"^\*! ysize: (\S+)", gph, re.M).group(1)
with open(os.path.join(work, "geometry_describe.log"), encoding="latin-1") as fh:
    sline = next(l.strip() for l in fh if l.strip().startswith("size:"))
with open(os.path.join(work, "geometry_ar05.gph"), encoding="latin-1") as fh:
    ar05 = fh.read()
ar_edit = ".style.editstyle aspect_ratio(.5)" in ar05
mg = G("ZG_MGCLASS")
with open(mg, encoding="latin-1") as fh:
    mgline = next(i for i, l in enumerate(fh, 1)
                  if "local aspect" in l and "graphsize.x" in l and "graphsize.y" in l)
mgrel = "/".join(mg.replace("\\", "/").split("/")[-4:])

c1, c2, c3, c4, c5, y9 = (size(k) for k in ("c1", "c2", "c3", "c4", "c5", "y9"))
bare, gyy = size("bare"), size("gy")
s2 = size("sch_s2color")
ar = {}
for a, k in (("0.25", "0_25"), ("1", "1"), ("4", "4")):
    w, h = (float(v) for v in G("ZG_AR_" + k).split())
    ar[a] = {"plotregion_ren": [w, h], "height_over_width": round(h / w, 4)}
ar["note"] = ("A 6x6in graph; .Graph.plotregion1.xsize_ren and .ysize_ren, the "
              "plot region's drawn width and height in graph units. Confirms "
              "Stata aspectratio = height/width.")

defaults = {}
for s in G("ZG_SCHEMES").split():
    x, y = size("sch_" + s)
    defaults[s] = {"xsize": num(x), "ysize": num(y),
                   "aspect_w_over_h": round(x / y, 4), "verified_in_stata": True}

out = {
    "_source": ("Measured in " + G("ZG_VERSION") + " (console, batch) via twoway "
                "scatter mpg weight (sysuse auto) + graph describe + graph save "
                "+ graph export, by scripts/extract_geometry_truth.do."),
    "_probes": ["extract_geometry_truth.do", "geometry_6x4.eps", "geometry_6x4.png",
                "geometry_6x4.gph", "geometry_ar05.gph", "geometry_describe.log",
                "scheme-zgbare.scheme", "scheme-zgy.scheme"],
    "units": {
        "xsize": "inches",
        "ysize": "inches",
        "evidence_eps_bounding_box": "xsize(6) ysize(4) -> %s (%g/72=%gin, %g/72=%gin)" % (
            bbox, bb[2], bb[2] / 72, bb[3], bb[3] / 72),
        "evidence_gph_header": "xsize(6) ysize(4) -> '*! xsize: %s' and '*! ysize: %s' in the saved .gph" % (gx, gy),
        "evidence_png": "graph export width(600) of a 6x4in graph -> %dx%d px (ratio %g = 6/4)" % (pw, ph, round(pw / ph, 4)),
        "graph_describe_order": "graph describe prints '%s' for xsize(6) ysize(4): 'size: <ysize> x <xsize>' (height x width) -- NOT x-then-y" % sline,
    },
    "semantics": {
        "xsize_ysize": ("Overall GRAPH (canvas) dimensions in inches. Each is "
                        "independent; supplying only xsize() leaves ysize at the "
                        "scheme default (xsize(9) under stcolor -> %g x %g)." % (c3[1], c3[0])),
        "xsize_ysize_validation": "xsize(0) returns r(%s) and xsize(-3) r(%s)." % (G("ZG_RC_0"), G("ZG_RC_m3")),
        "aspectratio": ("Stata aspectratio(#) = PLOT REGION height / width. It "
                        "does NOT change xsize/ysize: aspectratio(0.5) under "
                        "stcolor still reports size %g x %g%s." % (
                            c5[1], c5[0],
                            " and the .gph records '.style.editstyle aspect_ratio(.5)' on the graph object only" if ar_edit else "")),
        "aspectratio_measured": ar,
        "bokeh_aspect_ratio": ("Bokeh's Figure.aspect_ratio is width/height -- the "
                               "RECIPROCAL of Stata's aspectratio(). Passing Stata's "
                               "value straight through inverts the meaning."),
        "scheme_graphsize_bare": ("A bare 'graphsize <n>' scheme entry does not "
                                  "affect graph dimensions when 'graphsize x'/'graphsize y' "
                                  "are also set. Probed with '#include s2color' + "
                                  "'graphsize 3' -> %g x %g (s2color: %g x %g)." % (
                                      bare[1], bare[0], s2[1], s2[0])),
        "scheme_graphsize_xy": ("'graphsize x' is the default xsize (width, inches); "
                                "'graphsize y' is the default ysize (height, inches). "
                                "Each is independent: '#include s2color' + "
                                "'graphsize y 2' -> %g x %g." % (gyy[1], gyy[0])),
        "override_precedence": ("An explicit xsize()/ysize() overrides the scheme's "
                                "graphsize for that dimension only; the unspecified "
                                "dimension keeps the scheme default (ysize(9) under "
                                "stcolor -> %g x %g)." % (y9[1], y9[0])),
        "stata_own_aspect_convention": ("%s:%d computes 'local aspect = graphsize.x / "
                                        "graphsize.y' -- i.e. Stata itself treats x/y "
                                        "(width/height) as the aspect when converting "
                                        "graphsize to a ratio. This is the "
                                        "Bokeh-compatible direction." % (mgrel, mgline)),
    },
    "default_scheme_of_this_installation": G("ZG_DEFAULT"),
    "scheme_defaults": defaults,
    "fixture_cases_for_tests": [
        {"opts": "xsize(6) ysize(4)", "xsize": c1[0], "ysize": c1[1], "w_over_h": round(c1[0] / c1[1], 4)},
        {"opts": "xsize(10) ysize(2)", "xsize": c2[0], "ysize": c2[1], "w_over_h": round(c2[0] / c2[1], 4)},
        {"opts": "xsize(9)", "xsize": c3[0], "ysize": c3[1], "w_over_h": round(c3[0] / c3[1], 4), "scheme": "stcolor"},
        {"opts": "(none)", "xsize": c4[0], "ysize": c4[1], "w_over_h": round(c4[0] / c4[1], 4), "scheme": "stcolor"},
        {"opts": "aspectratio(0.5)", "xsize": c5[0], "ysize": c5[1],
         "note": "graph size unchanged; plot region h/w = 0.5"},
    ],
}
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZG_VERSION"), "born_date": G("ZG_BORN"),
                "dash_commit": commit, "extracted": G("ZG_WHEN"),
                "source": "scripts/extract_geometry_truth.do"}
with open(G("ZG_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1)
    fh.write("\n")
for f in ("git_head.txt", "geometry_6x4.eps", "geometry_6x4.png", "geometry_6x4.gph",
          "geometry_ar05.gph", "geometry_describe.log", "scheme-zgbare.scheme",
          "scheme-zgy.scheme"):
    try:
        os.remove(os.path.join(work, f))
    except OSError:
        pass
print("wrote", G("ZG_OUT"))
end
