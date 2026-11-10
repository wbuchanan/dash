*! extract_noted_drawn_truth.do -- WP-47 basic:PT-11 (section 47-05):
*! what twoway draws for the options dash named in its note as not drawn
*! and now draws -- back markers (bmsymbol() .. bmlalign()), alalign() and
*! blalign() beside lalign(), mlabalignment() and mlabjustification(),
*! bartype(spanning) and its edge cases (one bar, one distinct x, a
*! missing x), dropto(), numkeys(), the omit rules on a multi-y line,
*! dlpattern() on dot and zvarlabel() on contour.
*!
*! Each probe is one twoway command, run under capture noisily with its
*! own log and exported with graph export, as(svg); the record holds its
*! rc, the lines it printed, and the drawn elements of its SVG read by
*! scripts/svg_layer.py (gridlines and the background aside): each
*! circle and polygon's kind, fill, stroke, stroke width, extent and
*! centre; each filled rect's fill and edges; each stroked path's colour
*! and points; each <text>'s x, y, anchor and words.  Coordinates are the
*! SVG's (y down).
*!
*! Output: test/fixtures/noted_drawn_truth.json
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_noted_drawn_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 255
set graphics off

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zd_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zd_bad' {
    display as error "extract_noted_drawn_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zd_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zd_rc' | _rc {
    local _zd_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_noted_drawn_truth.do: `_zd_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZD_REPO "`repo'"
global ZD_OUT "${ZD_REPO}/test/fixtures/noted_drawn_truth.json"

adopath ++ "${ZD_REPO}"
quietly do "${ZD_REPO}/dash_parse.mata"
quietly do "${ZD_REPO}/dash.ado"
global dash_nobrowser 1

local work "`c(tmpdir)'dash_noted_drawn"
capture mkdir "`work'"
global ZD_WORK "`work'"
quietly shell git -C "${ZD_REPO}" rev-parse HEAD > "${ZD_WORK}/git_head.txt"
global ZD_VERSION "`c(stata_version)'"
global ZD_BORN "`c(born_date)'"
global ZD_WHEN "`c(current_date)' `c(current_time)'"

* The probes: key, then the command.  Data: auto's first rows; y1/y2 a
* multi-y pair with missing values (y1 in 3/5 and 10, y2 in 4 and 10);
* gx/gy/gz contour's 9-by-8 grid.
sysuse auto, clear
gen y1 = mpg
gen y2 = price / 1000
replace y1 = . in 3/5
replace y2 = . in 4
replace y1 = . in 10
replace y2 = . in 10
gen gx = mod(_n - 1, 9) + 1 if _n <= 72
gen gy = floor((_n - 1) / 9) + 1 if _n <= 72
gen gz = gx * gy + gy
gen w1 = weight
replace w1 = . in 4
gen one = 1
gen pv = cond(_n == 1, 9, cond(_n == 2, 12, 3))

local P ""
local P `"`P' "BM00|scatter mpg weight in 1/3," "BM01|scatter mpg weight in 1/3, bmsymbol(O)""'
local P `"`P' "BM02|scatter mpg weight in 1/3, bmsymbol(T)" "BM03|scatter mpg weight in 1/3, bmsymbol(O) bmcolor(red)""'
local P `"`P' "BM04|scatter mpg weight in 1/3, bmsymbol(O) bmsize(large)" "BM05|scatter mpg weight in 1/3, bmsymbol(O) bmlcolor(red) bmlwidth(thick)""'
local P `"`P' "BM06|scatter mpg weight in 1/3, bmlcolor(red) bmlwidth(thick)" "BM07|scatter mpg weight in 1/3, bmsymbol(O) bmlcolor(red) bmlwidth(thick) bmlalign(outside)""'
local P `"`P' "BM08|scatter mpg weight in 1/3, bmsymbol(O) bmlcolor(red) bmlwidth(thick) bmlpattern(dash)" "BM09|scatter mpg weight in 1/3, bmsymbol(O) msize(large) mcolor(blue)""'
local P `"`P' "BM10|scatter mpg weight in 1/3, bmsymbol(Oh) bmsize(large)" "BM11|scatter mpg weight in 1/3, bmsymbol(O) mlabel(make)""'
local P `"`P' "BM12|scatter mpg weight in 1/3 [aw=price], bmsymbol(O)" "BM13|scatter mpg weight in 1/3, bmsymbol(O) colorvar(price)""'
local P `"`P' "BM14|connected mpg weight in 1/3, bmsymbol(O) bmsize(large)" "BM15|line mpg weight in 1/3, bmsymbol(O) bmsize(large)""'
local P `"`P' "BM16|scatter mpg weight in 1/3, bmsymbol(O) bmsize(large) scheme(s2color)" "BM17|scatter mpg weight in 1/3, bmcolor(red) bmsize(large)""'
local P `"`P' "BM18|scatter mpg weight in 1/3, bmsymbol(D) bmsize(large) bmcolor(red)" "BM19|scatter mpg weight in 1/3, bsymbol(O) bmsize(large)""'
local P `"`P' "BM20|scatter mpg turn weight in 1/3, bmsymbol(O) bmsize(large)" "BM21|scatter mpg weight in 1/3, bmsymbol(O) bmsize(large) bmcolor(red%50)""'
local P `"`P' "AL00|bar mpg weight in 1/3, barwidth(100) lwidth(vthick) lalign(inside)" "AL01|bar mpg weight in 1/3, barwidth(100) lwidth(vthick) alalign(outside)""'
local P `"`P' "AL02|bar mpg weight in 1/3, barwidth(100) lwidth(vthick) blalign(outside)" "AL03|bar mpg weight in 1/3, barwidth(100) lwidth(vthick) alalign(outside) lalign(inside)""'
local P `"`P' "AL04|bar mpg weight in 1/3, barwidth(100) lwidth(vthick) blalign(inside) alalign(outside)" "AL05|bar mpg weight in 1/3, barwidth(100) lwidth(vthick) lalign(outside)""'
local P `"`P' "AL06|area mpg weight in 1/3, lwidth(vthick) alalign(outside)" "AL07|bar mpg weight in 1/3, barwidth(100) lwidth(vthick) alalign(center)""'
local P `"`P' "ML00|scatter mpg weight in 1/3, mlabel(make)" "ML01|scatter mpg weight in 1/3, mlabel(make) mlabalignment(top)""'
local P `"`P' "ML02|scatter mpg weight in 1/3, mlabel(make) mlabalignment(bottom)" "ML03|scatter mpg weight in 1/3, mlabel(make) mlabalignment(middle)""'
local P `"`P' "ML04|scatter mpg weight in 1/3, mlabel(make) mlabalignment(baseline)" "ML05|scatter mpg weight in 1/3, mlabel(make) mlabjustification(right)""'
local P `"`P' "ML06|scatter mpg weight in 1/3, mlabel(make) mlabjustification(left)" "ML07|scatter mpg weight in 1/3, mlabel(make) mlabjustification(center)""'
local P `"`P' "ML08|scatter mpg weight in 1/3, mlabel(make) mlabposition(9) mlabjustification(left)" "ML09|scatter mpg weight in 1/3, mlabel(make) mlabposition(12) mlabalignment(top)""'
local P `"`P' "ML10|scatter mpg weight in 1/3, mlabel(make) mlabalignment(nosuch)" "ML11|scatter mpg weight in 1/3, mlabel(make) mlabjustification(nosuch)""'
local P `"`P' "BT00|bar mpg weight in 1/5," "BT01|bar mpg weight in 1/5, bartype(spanning)""'
local P `"`P' "BT02|bar mpg weight in 1/5, bartype(fixed)" "BT03|bar mpg weight in 1/1, bartype(spanning)""'
local P `"`P' "BT04|bar mpg one in 1/10, bartype(spanning)" "BT05|bar mpg w1 in 1/10, bartype(spanning)""'
local P `"`P' "BT06|bar mpg weight in 1/5, bartype(spanning) horizontal" "BT07|bar mpg weight in 1/5, bartype(nosuch)""'
local P `"`P' "BT08|spike mpg weight in 1/5, bartype(spanning)" "BT09|dropline mpg weight in 1/5, bartype(spanning)""'
local P `"`P' "BT10|area mpg weight in 1/5, bartype(spanning)" "BT11|dot mpg weight in 1/5, bartype(spanning)""'
local P `"`P' "DT00|bar mpg weight in 1/5, dropto(y)" "DT01|bar mpg weight in 1/5, dropto(x)""'
local P `"`P' "DT02|bar mpg weight in 1/5, dropto(10)" "DT03|bar mpg weight in 1/5, dropto(y) horizontal""'
local P `"`P' "DT04|spike mpg weight in 1/5, dropto(y)" "DT05|dropline mpg weight in 1/5, dropto(y)""'
local P `"`P' "DT06|area mpg weight in 1/5, dropto(y)" "DT07|dot mpg weight in 1/5, dropto(y)""'
local P `"`P' "DT08|bar mpg weight in 1/5, dropto(y) base(20)" "DT09|bar mpg weight in 1/5, dropto(nosuch)""'
local P `"`P' "NK00|scatter mpg weight || scatter turn weight ||," "NK01|scatter mpg weight, numkeys(3) || scatter turn weight ||,""'
local P `"`P' "NK02|scatter mpg weight, numkeys(3) || scatter turn weight ||, legend(order(1 2 3 4))" "NK03|scatter mpg weight, numkeys(0) || scatter turn weight ||,""'
local P `"`P' "NK04|scatter mpg weight || scatter turn weight, numkeys(2)" "NK05|scatter mpg turn weight, numkeys(1)""'
local P `"`P' "NK06|scatter mpg weight, numkeys(3) legend(on)" "NK07|scatter mpg weight, numkeys(2) || scatter turn weight ||, legend(label(2 Two) label(3 Three))""'
local P `"`P' "NK08|scatter mpg weight, numkeys(abc) || scatter turn weight ||," "NK09|scatter mpg weight, numkeys(-1) || scatter turn weight ||,""'
local P `"`P' "NK10|scatter mpg weight, numkeys(1.5) || scatter turn weight ||," "NK11|scatter mpg turn weight, numkeys(3)""'
local P `"`P' "OM00|line y1 y2 weight in 1/12, sort" "OM01|line y1 y2 weight in 1/12, sort omitanymiss""'
local P `"`P' "OM02|line y1 y2 weight in 1/12, sort omitallmiss" "OM03|line y1 y2 weight in 1/12, sort omitdupmiss""'
local P `"`P' "OM04|line y1 y2 weight in 1/12, sort omitnothing" "OM05|line y1 y2 weight in 1/12, sort omitanymiss omitallmiss""'
local P `"`P' "OM06|line y1 weight in 1/12, sort omitanymiss" "OM07|scatter y1 y2 weight in 1/12, omitanymiss""'
local P `"`P' "OM08|line y1 weight in 1/12, sort || line y2 weight in 1/12, sort omitanymiss" "OM09|connected y1 y2 weight in 1/12, sort omitanymiss""'
local P `"`P' "DL00|dot mpg weight in 1/5, dlwidth(thick)" "DL01|dot mpg weight in 1/5, dlwidth(thick) dlpattern(dash)""'
local P `"`P' "DL02|dot mpg weight in 1/5, dlpattern(dash)" "ZV00|contour gz gy gx,""'
local P `"`P' "ZV01|contour gz gy gx, zvarlabel(Z)" "ZV02|contourline gz gy gx, zvarlabel(Z)""'
local P `"`P' "ZV03|scatter mpg weight, colorvar(price) zvarlabel(Z)" "ZV04|contour gz gy gx, zvarlabel(A b)""'
* Edge cases and the routed words (the coordinator's second pass).
local P `"`P' "BT12|bar y1 weight in 1/10, bartype(spanning)" "BT13|bar mpg weight in 1/5, bartype(obs)""'
local P `"`P' "BT14|bar mpg weight in 1/5, bartype(spanning) barwidth(50)" "BT15|bar mpg weight in 1/5, bartype(Spanning)""'
local P `"`P' "DT10|bar mpg weight in 1/5, horizontal" "DT11|bar mpg weight in 1/5, horizontal dropto(x)""'
local P `"`P' "DT12|bar mpg weight in 1/5, vertical dropto(y)" "DT13|bar mpg weight in 1/5, dropto(Y)""'
local P `"`P' "DT14|dot mpg weight in 1/5, horizontal" "DT15|spike mpg weight in 1/5, horizontal""'
local P `"`P' "DT16|dropline mpg weight in 1/5, horizontal" "DT17|area mpg weight in 1/5, horizontal""'
local P `"`P' "MV00|scatter mpg weight in 1/3, mlabel(make) mlabvposition(pv)" "MV01|scatter mpg weight in 1/3, mlabel(make) mlabvposition(pv) mlabalignment(top)""'
local P `"`P' "MV02|scatter mpg weight in 1/3, mlabel(make) mlabvposition(pv) mlabjustification(right)" "MV03|scatter mpg weight in 1/3, mlabel(make) mlabposition(9)""'
local P `"`P' "MV04|scatter mpg weight in 1/3, mlabel(make) mlabposition(12)" "MV05|scatter mpg weight in 1/3, mlabel(make) mlabposition(12) mlabjustification(left)""'
local P `"`P' "MV06|scatter mpg weight in 1/3, mlabel(make) mlabposition(9) mlabalignment(bottom)""'
local P `"`P' "NB00|mspline mpg weight," "NB01|mspline mpg weight, noback" "NB02|mband mpg weight, noback" "NB03|mband mpg weight," "NB04|mspline mpg weight, back""'
local P `"`P' "NB05|mspline mpg weight, noback ytitle(T)" "NB06|mspline mpg weight, noback yvarlabel(V)""'
local P `"`P' "BL00|lfitci mpg weight," "BL01|lfitci mpg weight, below" "BL02|qfitci mpg weight, below" "BL03|lpolyci mpg weight, below" "BL04|fpfitci mpg weight, below""'
local P `"`P' "BL05|lfitci mpg weight, below || scatter mpg weight" "BL06|scatter mpg weight || lfitci mpg weight, below""'
local P `"`P' "NK12|scatter mpg weight, numkeys(3) || scatter turn weight ||, legend(order(2 4))" "NK13|line mpg weight, sort numkeys(2) || scatter turn weight ||,""'
local P `"`P' "NK14|scatter mpg weight, numkeys(2) || scatter turn weight, numkeys(2) ||," "NK15|scatter mpg weight, numkeys(3) legend(off)""'
local P `"`P' "KD00|kdensity mpg," "KD01|kdensity mpg, omitanymiss" "KD02|kdensity mpg, n(50) omitanymiss" "KD03|kdensity mpg in 1/30, omitanymiss""'
local P `"`P' "KD04|kdensity mpg, n(500) omitanymiss" "LP00|lpolyci mpg weight," "LP01|lpolyci mpg weight, omitanymiss""'
local P `"`P' "LP02|lpoly mpg weight, omitanymiss" "LP03|lpoly mpg weight,""'
local P `"`P' "OM10|scatter y1 y2 weight in 1/12, omitanymiss" "OM11|scatter y1 y2 weight in 1/12,""'
local P `"`P' "OM12|line y1 y2 weight in 1/12 if foreign == 0, sort omitanymiss" "OM13|area y1 y2 weight in 1/12, sort omitanymiss""'
local P `"`P' "DB00|area mpg weight in 1/10," "DB01|area mpg weight in 1/10, nodropbase""'
local P `"`P' "CQ00|contour gz gy gx," "CQ01|contour gz gy gx, logging""'
* The minimum spellings of the folded words: each word at every length
* (AB_<word>_<L>), its full name and the context alone, twoway and dash.
local AB ""
local AB `"`AB' "alalign|bar mpg weight in 1/3, barwidth(100) lwidth(vthick)|(outside)""'
local AB `"`AB' "blalign|bar mpg weight in 1/3, barwidth(100) lwidth(vthick)|(outside)""'
local AB `"`AB' "bmsymbol|scatter mpg weight in 1/3, bmsize(large)|(T)""'
local AB `"`AB' "bmcolor|scatter mpg weight in 1/3, bmsymbol(O) bmsize(large)|(red)""'
local AB `"`AB' "bmsize|scatter mpg weight in 1/3, bmsymbol(O)|(large)""'
local AB `"`AB' "bmlcolor|scatter mpg weight in 1/3, bmsymbol(O) bmsize(large) bmlwidth(thick)|(red)""'
local AB `"`AB' "bmlwidth|scatter mpg weight in 1/3, bmsymbol(O) bmsize(large) bmlcolor(red)|(thick)""'
local AB `"`AB' "bmlalign|scatter mpg weight in 1/3, bmsymbol(O) bmsize(large) bmlcolor(red) bmlwidth(thick)|(outside)""'
local AB `"`AB' "bmlpattern|scatter mpg weight in 1/3, bmsymbol(O)|(nosuch)""'
local AB `"`AB' "mlabalignment|scatter mpg weight in 1/3, mlabel(make)|(top)""'
local AB `"`AB' "mlabjustification|scatter mpg weight in 1/3, mlabel(make)|(right)""'
local AB `"`AB' "zvarlabel|contour gz gy gx,|(Z)""'
local AB `"`AB' "bartype|bar mpg weight in 1/5,|(spanning)""'
local AB `"`AB' "dropto|bar mpg weight in 1/5,|(y)""'
local AB `"`AB' "numkeys|scatter mpg weight in 1/5,|(3) || scatter turn weight in 1/5 ||,""'
local AB `"`AB' "omitanymiss|line y1 y2 weight in 1/12, sort|""'
local AB `"`AB' "noback|mspline mpg weight,|""'
local AB `"`AB' "below|lfitci mpg weight,|""'
foreach one of local AB {
    gettoken w rest : one, parse("|")
    gettoken bar rest : rest, parse("|")
    gettoken ctx rest : rest, parse("|")
    gettoken bar val : rest, parse("|")
    local L = strlen("`w'")
    forvalues j = 1/`L' {
        local P `"`P' "AB_`w'_`j'|`ctx' `=substr("`w'", 1, `j')'`val'""'
    }
    local P `"`P' "AB_`w'_plain|`ctx'""'
}

local k 0
foreach one of local P {
    local ++k
    gettoken key cmd : one, parse("|")
    gettoken bar cmd : cmd, parse("|")
    global ZD_K_`k' "`key'"
    global ZD_C_`k' `"`cmd'"'
    capture graph drop _all
    quietly log using "${ZD_WORK}/`key'.log", replace text name(zd)
    set seed 12345
    capture noisily twoway `cmd' name(zo, replace)
    global ZD_R_`k' = _rc
    quietly log close zd
    capture erase "${ZD_WORK}/`key'.svg"
    if !${ZD_R_`k'} capture graph export "${ZD_WORK}/`key'.svg", name(zo) replace as(svg)
    capture graph drop _all
    if substr("`key'", 1, 3) == "AB_" {
        quietly log using "${ZD_WORK}/D`key'.log", replace text name(zd)
        capture noisily dash `cmd' name(zq)
        global ZD_D_`k' = _rc
        quietly log close zd
        capture dash clear
    }
}
global ZD_N "`k'"

python:
import html, json, os, re, sys
from sfi import Macro

G = Macro.getGlobal
repo, work = G("ZD_REPO"), G("ZD_WORK")
sys.path.insert(0, os.path.join(repo, "scripts"))
import svg_layer

GRID = "#f0f0f0"


def printed(key):
    """The lines the command printed: the log less its header, footer,
    echoed command and blank lines."""
    keep = []
    try:
        fh = open(os.path.join(work, key + ".log"), encoding="utf-8",
                  errors="replace")
    except OSError:
        return keep
    with fh:
        for ln in fh:
            t = ln.strip()
            if not t or t.startswith((".", ">", "name:", "log:", "log type:",
                                      "opened on:", "closed on:", "---")):
                continue
            keep.append(t)
    return keep


_TEXT = re.compile(r"<text\b([^>]*)>(.*?)</text>", re.S)
_A = re.compile(r'([\w:-]+)="([^"]*)"')


def texts(path):
    with open(path, encoding="utf-8") as fh:
        svg = fh.read()
    out = []
    for attrs, body in _TEXT.findall(svg):
        a = dict(_A.findall(attrs))
        out.append({"x": float(a.get("x", "nan")), "y": float(a.get("y", "nan")),
                    "anchor": a.get("text-anchor", "start"),
                    "text": html.unescape(re.sub(r"<[^>]+>", "", body)).strip()})
    return out


def elements(path):
    out = []
    for e in svg_layer.svg_elements(path):
        if e["stroke"] == GRID or e["fill"] == GRID:
            continue
        xs = [p[0] for p in e["points"]]
        ys = [p[1] for p in e["points"]]
        rec = {"kind": e["kind"], "fill": e["fill"], "stroke": e["stroke"],
               "stroke_width": e["stroke_width"],
               "fill_opacity": e["fill_opacity"],
               "extent": e["extent"], "center": list(e["center"]),
               "x0": round(min(xs), 2), "x1": round(max(xs), 2),
               "y0": round(min(ys), 2), "y1": round(max(ys), 2)}
        if e["kind"] in ("path", "line") and e["fill"] in (None, "none"):
            rec["points"] = [list(p) for p in e["points"]]
        out.append(rec)
    return out


_ID = re.compile(r"\b(path|clipPath|pattern|linearGradient|mask)_[A-Za-z]{8}\b")


def picture(key):
    """The SVG's lines, <desc> lines aside and per-export ids made one."""
    try:
        with open(os.path.join(work, key + ".svg"), encoding="utf-8") as fh:
            return [_ID.sub("ID", ln) for ln in fh.read().splitlines()
                    if not ln.strip().startswith("<desc>")]
    except OSError:
        return None


NOTE = "ignoring unsupported option(s):"


def noted(key):
    for ln in printed("D" + key):
        i = ln.find(NOTE)
        if i >= 0:
            return ln[i + len(NOTE):].strip().rstrip(")").split()
    return []


probes = {}
for k in range(1, int(G("ZD_N")) + 1):
    key = G("ZD_K_%d" % k)
    rc = int(G("ZD_R_%d" % k))
    svg = os.path.join(work, key + ".svg")
    rec = {"cmd": G("ZD_C_%d" % k).strip(), "rc": rc, "printed": printed(key)}
    if key.startswith("AB_"):
        # A spelling's record: twoway's rc and first lines, whether its
        # picture is the full name's and the context's alone, and dash's
        # rc and note.
        w = key.split("_")[1]
        L = len(w)
        rec["dash_rc"] = int(G("ZD_D_%d" % k))
        rec["dash_note"] = noted(key)
        pic = picture(key) if rc == 0 else None
        rec["same_as_full"] = (pic is not None and pic == picture("AB_%s_%d" % (w, L)))
        rec["same_as_plain"] = (pic is not None and pic == picture("AB_%s_plain" % w))
        probes[key] = rec
        continue
    if rc == 0 and os.path.exists(svg):
        rec["elements"] = elements(svg)
        rec["texts"] = texts(svg)
    probes[key] = rec
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out = {"_meta": {"stata_version": G("ZD_VERSION"), "born_date": G("ZD_BORN"),
                 "dash_commit": commit, "extracted": G("ZD_WHEN"),
                 "source": "scripts/extract_noted_drawn_truth.do"},
       "probes": probes}
with open(G("ZD_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
if not os.environ.get("ZD_KEEP"):
    for f in os.listdir(work):
        if f.endswith((".svg", ".log", ".txt")):
            try:
                os.remove(os.path.join(work, f))
            except OSError:
                pass
print("wrote", G("ZD_OUT"), len(probes), "probes")
end
