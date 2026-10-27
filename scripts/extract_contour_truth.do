*! extract_contour_truth.do -- WP-31 section 23 (B4a): measure the surface
*! twoway contour draws from scattered (x, y, z): the grid, the duplicate
*! rule, the thin-plate spline and Shepard interpolation, interp(none) and
*! the interp() words, from twoway's own generator (the compiled Mata
*! functions _contour_heatmap, _contour_filled and _contour_line that
*! twoway__contour_gen calls), so dash's interpolation is proved against
*! live twoway, not modelled.  twoway only: the output is the same before
*! and after dash changes.
*!
*! The generator's Mata matrices are written as doubles (twoway__contour_gen
*! itself stores z as a float through getmata; the matrix it reads is the
*! same).  Columns are (x, y, z, level), missing rows separating pieces.
*!
*! WP-31 section 26 (B4b) appends the ZD_ block: how twoway draws the
*! two types (cuts, colours, key, lines, abbreviations, refusals).
*!
*! Output: test/fixtures/contour_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_contour_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zc_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zc_bad' {
    display as error "extract_contour_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zc_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zc_rc' | _rc {
    local _zc_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_contour_truth.do: `_zc_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZC_REPO "`repo'"
global ZC_OUT "${ZC_REPO}/test/fixtures/contour_truth.json"
adopath ++ "${ZC_REPO}"
global dash_nobrowser 1

local work "`c(tmpdir)'dash_contour_probe"
capture mkdir "`work'"
global ZC_WORK "`work'"

if `"`c(python_exec)'"' == "" {
    display as error "extract_contour_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

quietly shell git -C "${ZC_REPO}" rev-parse HEAD > "${ZC_WORK}/git_head.txt"
global ZC_VERSION "`c(stata_version)'"
global ZC_BORN "`c(born_date)'"
global ZC_WHEN "`c(current_date)' `c(current_time)'"
set scheme s2color
* twoway's thin-plate and Shepard paths pick among duplicate (y, x) rows
* in an order that follows the sort seed (measured below); fix it so the
* fixture is reproducible.
set sortseed 20261010

* ---- Mata: one record file, one "key<TAB>rows cols" header per matrix,
* then its rows, %21.17g, "." for missing.
mata:
void zc_open(string scalar path)
{
    external real scalar zc_fh
    if (fileexists(path)) unlink(path)
    zc_fh = fopen(path, "w")
}
void zc_close()
{
    external real scalar zc_fh
    fclose(zc_fh)
}
void zc_put(string scalar key, real matrix M)
{
    external real scalar zc_fh
    real scalar r, c
    string scalar line
    fput(zc_fh, sprintf("%s\t%g %g", key, rows(M), cols(M)))
    for (r = 1; r <= rows(M); r++) {
        line = ""
        for (c = 1; c <= cols(M); c++) {
            line = line + (c > 1 ? " " : "") +
                   (M[r, c] >= . ? "." : strtrim(sprintf("%21.17g", M[r, c])))
        }
        fput(zc_fh, line)
    }
}
void zc_data(real matrix D)
{
    stata("clear")
    st_addobs(rows(D))
    (void) st_addvar("double", ("y", "x", "z"))
    st_store(., ("y", "x", "z"), D)
}
end

mata: zc_open("${ZC_WORK}/records.txt")

* ---- One dataset: its rows, the de-duplicated input (smallest z per
* (y, x), the documented rule), the cuts and the three generators under
* each interp().
capture program drop _zc_case
program define _zc_case
    args ds
    mata: zc_put("`ds'.rows", st_data(., ("x", "y", "z")))
    quietly _pctile z, p(25 50 75)
    local cuts `r(r1)' `r(r2)' `r(r3)'
    mata: zc_ct = strtoreal(tokens(st_local("cuts")))'
    mata: zc_put("`ds'.cuts", zc_ct')
    preserve
    sort y x z
    quietly by y x: keep if _n == 1
    mata: zc_put("`ds'.input", st_data(., ("x", "y", "z")))
    restore
    foreach i in thinplatespline shepard none {
        foreach k in heatmap filled line {
            capture noisily mata: zc_M = _contour_`k'("z", "y", "x", zc_ct, "`i'")
            local rc = _rc
            mata: zc_put("`ds'.`i'.`k'.rc", `rc')
            if !`rc' mata: zc_put("`ds'.`i'.`k'", zc_M)
        }
        display as text "ZC `ds' `i' done"
    }
end

* (a) auto: z = mpg, y = weight, x = length.
sysuse auto, clear
keep mpg weight length
rename (mpg weight length) (z y x)
_zc_case auto

* (b) synthetic: 40 scattered points, no duplicates (40, not 60: the
* fixture's polygon rows stay small).
clear
set obs 40
set seed 20261010
gen x = runiform() * 10
gen y = runiform() * 5
gen z = sin(x) * cos(y) + rnormal(0, .05)
_zc_case synthetic

* (c) the duplicate-pair example: (y, x, z) rows (1,1,1) (1,2,2) (2,1,3)
* (2,2,4) (2,2,5).
mata: zc_data((1,1,1 \ 1,2,2 \ 2,1,3 \ 2,2,4 \ 2,2,5))
_zc_case manual5

* ---- The duplicate rule under the sort seed: the z each interp() gives
* the node (2, 2) of manual5 under sort seeds 1-5, rows in two orders.
mata:
real scalar zc_node(string scalar im, real scalar xx, real scalar yy)
{
    real matrix M, G
    real scalar r
    M = _contour_heatmap("z", "y", "x", (2 \ 3 \ 4), im)
    M = select(M, M[., 1] :< .)
    for (r = 1; r <= rows(M); r = r + 4) {
        G = M[r..r+3, .]
        if (min(G[., 1]) <= xx & xx <= max(G[., 1]) &
            min(G[., 2]) <= yy & yy <= max(G[., 2])) return(G[1, 3])
    }
    return(.)
}
end
foreach o in 1 2 {
    forvalues s = 1/5 {
        set sortseed `s'
        if `o' == 1 mata: zc_data((1,1,1 \ 1,2,2 \ 2,1,3 \ 2,2,4 \ 2,2,5))
        else        mata: zc_data((2,2,5 \ 1,1,1 \ 2,2,4 \ 1,2,2 \ 2,1,3))
        foreach i in thinplatespline shepard none {
            mata: zc_put("dupseed.`i'.order`o'.seed`s'", zc_node("`i'", 2, 2))
        }
    }
}
set sortseed 20261010

* ---- interp() words: what twoway contour returns, and which method the
* generator applies (its heatmap compared with the three canonical ones on
* five points whose 3x3 grid leaves four nodes to interpolate).
mata: zc_data((1,1,1 \ 1,3,2 \ 3,1,3 \ 2,2,10 \ 3,3,4))
mata: zc_put("words.rows", st_data(., ("x", "y", "z")))
local w 0
foreach word in thinplatespline shepard none thin thinp th t tps shep shepa sh s no n bogus THIN Shepard thinx EMPTY {
    local w = `w' + 1
    local arg = cond("`word'" == "EMPTY", "", "`word'")
    capture twoway contour z y x, interp(`arg') nodraw
    mata: zc_put("words.w`w'.rc", `=_rc')
    mata: zc_put("words.w`w'.heatmap", _contour_heatmap("z", "y", "x", (2 \ 3 \ 4), "`arg'"))
    global ZC_WORD_`w' "`word'"
}
global ZC_NWORDS `w'

* ---- Degenerate inputs: twoway contour's answer, with its message.
foreach d in two_points one_x {
    if "`d'" == "two_points" mata: zc_data((1,1,1 \ 2,2,2))
    else                     mata: zc_data((1,1,1 \ 2,1,2 \ 3,1,3 \ 4,1,4))
    capture log close zc_log
    quietly log using "${ZC_WORK}/deg_`d'.log", text replace name(zc_log)
    capture noisily twoway contour z y x, nodraw
    local rc = _rc
    quietly log close zc_log
    mata: zc_put("degenerate.`d'.rc", `rc')
    mata: zc_put("degenerate.`d'.rows", st_data(., ("x", "y", "z")))
    foreach k in heatmap filled {
        capture mata: zc_M = _contour_`k'("z", "y", "x", 1.5, "thinplatespline")
        local rc = _rc
        mata: zc_put("degenerate.`d'.`k'.rc", `rc')
        if !`rc' mata: zc_put("degenerate.`d'.`k'", zc_M)
    }
}

mata: zc_close()

* ==== ZD_ (WP-31 section 26, B4b): how twoway draws contour and
* contourline -- the cuts (ccuts(), levels(), minmax, the z axis's ticks),
* the level colours under each crule() and ccolors(), the labels, the key,
* horizontal, the contourline lines (exported SVG), the abbreviations
* twoway takes and every refusal with its rc and printed lines, on auto
* (z = mpg, y = weight, x = length).  Written under the new top-level keys
* draw, line, abbrev, refuse and scheme; S23's keys are untouched.
* Each probe runs with its printed lines in a log; a drawn graph's
* class values go to one record file, "key<TAB>value" a line.
global ZD_KEYS ""
capture file close zdf
file open zdf using "${ZC_WORK}/zd_records.txt", write text replace
capture program drop _zd_run
program define _zd_run
    gettoken key 0 : 0
    capture graph drop zd
    quietly log using "${ZC_WORK}/zd_`key'.log", text replace name(zdlog)
    capture noisily `0'
    local rc = _rc
    display as text "{p_end}"
    quietly log close zdlog
    file write zdf "`key'.rc" _tab "`rc'" _n
    global ZD_KEYS "${ZD_KEYS} `key'"
    if `rc' exit
    capture graph describe zd
    if _rc exit
    local v ".zd.plotregion1.plot1"
    capture confirm existence `.zd.contour_view'`.zd.contourline_view'
    local vv "`.zd.contour_view'"
    if "`vv'" == "" local vv "`.zd.contourline_view'"
    if "`vv'" == "" exit
    local v ".zd.`vv'"
    local L = 0`.`v'.style.levels.val'
    local za `.`v'.zaxis'
    file write zdf "`key'.view" _tab "`vv'" _n
    file write zdf "`key'.type" _tab "`.`v'.type.setting'" _n
    file write zdf "`key'.cuts" _tab "`.`v'.style.ccutsopt'" _n
    file write zdf "`key'.levels" _tab "`L'" _n
    file write zdf "`key'.rule" _tab "`.`v'.style.rule.stylename'" _n
    file write zdf "`key'.ticks" _tab "`.`za'.major.tick_values'" _n
    file write zdf "`key'.use_rule" _tab "`.`za'.major.use_rule.istrue'" _n
    file write zdf "`key'.legend_keys" _tab "`.zd.legend.keys.arrnels'" _n
    file write zdf "`key'.drop_to" _tab "`.`v'.drop_to.stylename'" _n
    local fmt "`.`v'.style.format'"
    if "`fmt'" == "" local fmt "`.`v'.serset.sers[`.`v'.zvar'].format'"
    file write zdf "`key'.format" _tab "`fmt'" _n
    forvalues i = 1/`L' {
        file write zdf "`key'.rgb`i'" _tab "`.`v'.style.cstyles[`i'].color.rgb'" _n
    }
    forvalues k = 1/`=`L'-1' {
        local lab `"`.`v'.style.clabels[`k']'"'
        if `"`lab'"' == "" local lab = string(`.`v'.style.ccuts[`k']', "`fmt'")
        file write zdf "`key'.label`k'" _tab `"`lab'"' _n
        file write zdf "`key'.lw`k'" _tab "`.`v'.style.lwstyles[`k'].stylename'" _n
        file write zdf "`key'.lp`k'" _tab "`.`v'.style.lpstyles[`k'].stylename'" _n
    }
    file write zdf "`key'.xmin" _tab "`.zd.plotregion1.xscale.curmin'" _n
    file write zdf "`key'.xmax" _tab "`.zd.plotregion1.xscale.curmax'" _n
    quietly graph export "${ZC_WORK}/zd_`key'.svg", as(svg) replace
end

sysuse auto, clear
set scheme s2color
local c "twoway contour mpg weight length"
local cl "twoway contourline mpg weight length"
local nm "name(zd)"
_zd_run draw.default `c', `nm'
_zd_run draw.ccuts `c', ccuts(15 20 25 30) `nm'
_zd_run draw.ccuts_unsorted `c', ccuts(30 15 25 20) `nm'
_zd_run draw.levels5 `c', levels(5) `nm'
_zd_run draw.levels5_minmax `c', levels(5) minmax `nm'
_zd_run draw.levels1 `c', levels(1) `nm'
_zd_run draw.levels2 `c', levels(2) `nm'
_zd_run draw.minmax_alone `c', minmax `nm'
_zd_run draw.zlabel5 `c', zlabel(#5) `nm'
_zd_run draw.zlabel_list `c', zlabel(15(5)35) `nm'
_zd_run draw.zlabel_plain `c', zlabel(15 20 25 30 35) `nm'
_zd_run draw.zlabel_minmax `c', zlabel(minmax) `nm'
foreach r in linear revlinear intensity hue chue phue {
    _zd_run draw.crule_`r' `c', crule(`r') scolor(navy) ecolor(gold) `nm'
}
_zd_run draw.crule_hue_default `c', crule(hue) `nm'
_zd_run draw.crule_linear_default `c', crule(linear) `nm'
_zd_run draw.crule_intensity_default `c', crule(intensity) `nm'
_zd_run draw.chue_default `c', crule(chue) `nm'
_zd_run draw.scolor_only `c', scolor(green) `nm'
_zd_run draw.ccolors `c', ccolors(red blue green) `nm'
_zd_run draw.clabels `c', ccuts(15 20 25 30) clabels(a b c d) `nm'
_zd_run draw.format `c', format(%4.1f) `nm'
_zd_run draw.hz `c', horizontal `nm'
_zd_run draw.vertical `c', vertical `nm'
_zd_run draw.interp_shepard `c', interp(shepard) `nm'
_zd_run draw.interp_none `c', interp(none) `nm'
_zd_run draw.reversekey `c', reversekey `nm'
_zd_run draw.scheme_s1mono `c', scheme(s1mono) `nm'
_zd_run draw.scheme_economist `c', scheme(economist) `nm'
_zd_run line.default `cl', `nm'
_zd_run line.ccuts `cl', ccuts(15 20 25 30) `nm'
_zd_run line.clwidths `cl', clwidths(thin medium thick) `nm'
_zd_run line.clpatterns `cl', clpatterns(solid dash dot) `nm'
_zd_run line.reversekey `cl', reversekey `nm'
_zd_run line.hz `cl', horizontal `nm'
_zd_run line.vertical `cl', vertical `nm'
_zd_run line.ccolors `cl', ccolors(red blue) `nm'
_zd_run line.colorlines `cl', colorlines `nm'
_zd_run line.colorlines_clwidths `cl', colorlines clwidths(vthick thin) `nm'
_zd_run line.clwidths_vthick `cl', clwidths(vthick vthick) `nm'
_zd_run line.clpatterns_dash `cl', clpatterns(dash dash) `nm'
* abbreviations twoway takes and dash declares in full
_zd_run abbrev.lev `c', lev(5) `nm'
_zd_run abbrev.l `c', l(5) `nm'
_zd_run abbrev.le `c', le(5) `nm'
_zd_run abbrev.leve `c', leve(5) `nm'
_zd_run abbrev.level `c', level(5) `nm'
_zd_run abbrev.le_line `cl', le(5) `nm'
_zd_run abbrev.i `c', i(shepard) `nm'
_zd_run abbrev.clw `cl', clw(thin) `nm'
_zd_run abbrev.clp `cl', clp(dash) `nm'
_zd_run abbrev.cc `c', cc(20 30) `nm'
_zd_run abbrev.sc `c', sc(navy) `nm'
_zd_run abbrev.ec `c', ec(gold) `nm'
_zd_run abbrev.ccol `c', ccol(red blue) `nm'
_zd_run abbrev.clab `c', ccuts(20 30) clab(a b) `nm'
_zd_run abbrev.rev `c', rev `nm'
_zd_run abbrev.out `c', out `nm'
_zd_run abbrev.colorl `cl', colorl `nm'
_zd_run abbrev.hor `c', hor `nm'
* refusals
_zd_run refuse.ccuts_levels `c', ccuts(15 20) levels(5)
_zd_run refuse.levels0 `c', levels(0)
_zd_run refuse.levelsneg `c', levels(-1)
_zd_run refuse.levelsbig `c', levels(1001)
_zd_run refuse.levels_text `c', levels(a)
_zd_run refuse.levels_real `c', levels(2.5)
_zd_run refuse.ccuts_text `c', ccuts(a b)
_zd_run refuse.crule_bogus `c', crule(bogus)
_zd_run refuse.crule_Hue `c', crule(Hue)
_zd_run refuse.scolor_bogus `c', scolor(notacolour)
_zd_run refuse.ccolors_bogus `c', ccolors(red notacolour)
_zd_run refuse.clwidths_bogus `cl', clwidths(notawidth)
_zd_run refuse.clpatterns_bogus `cl', clpatterns(notapattern)
_zd_run refuse.hz_vert `c', horizontal vertical
_zd_run refuse.two_contours twoway (contour mpg weight length) (contour price weight length)
_zd_run refuse.two_lines twoway (contourline mpg weight length) (contourline price weight length)
_zd_run refuse.contour_and_line twoway (contour mpg weight length) (contourline price weight length)
_zd_run refuse.contour_scatter twoway (contour mpg weight length) (scatter weight length), `nm'
_zd_run refuse.string_z twoway contour make weight length
_zd_run refuse.string_y twoway contour mpg make length
_zd_run refuse.weight twoway contour mpg weight length [aw=price]
_zd_run refuse.counts_1 twoway contour mpg
_zd_run refuse.counts_2 twoway contour mpg weight
_zd_run refuse.counts_4 twoway contour mpg weight length turn
_zd_run refuse.counts_5 twoway contour mpg weight length turn trunk
_zd_run refuse.line_counts_2 twoway contourline mpg weight
foreach o in ccuts(1) levels(5) crule(hue) scolor(red) ecolor(red) ccolors(red) clabels(a) interp(none) minmax reversekey clwidths(thin) clpatterns(dash) heatmap outlines colorlines {
    local k = subinstr(subinstr(subinstr("`o'", "(", "", .), ")", "", .), " ", "", .)
    _zd_run refuse.on_scatter_`k' twoway scatter mpg weight, `o'
}
_zd_run refuse.colorvar `c', colorvar(price) `nm'
file close zdf

python:
import json, os, re
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


work = G("ZC_WORK")
rec = {}
with open(os.path.join(work, "records.txt"), encoding="utf-8") as fh:
    lines = fh.read().split("\n")
i = 0
while i < len(lines):
    if not lines[i]:
        i += 1
        continue
    key, _, shape = lines[i].partition("\t")
    r, c = (int(v) for v in shape.split())
    rows = []
    for j in range(r):
        rows.append([None if v == "." else float(v)
                     for v in lines[i + 1 + j].split()])
    rec[key] = rows
    i += 1 + r


def cols(rows, names):
    return {n: [row[k] for row in rows] for k, n in enumerate(names)}


def scalar(key):
    return rec[key][0][0]


def gen(key):
    out = {"rc": int(scalar(key + ".rc"))}
    if key in rec:
        out.update(cols(rec[key], ("x", "y", "z", "lev")))
        out["n_rows"] = len(rec[key])
    return out


def heat(key):
    # A heatmap matrix is one rectangle per drawn grid node: four corner
    # rows, the node's z and level on each, missing rows between pieces.
    out = {"rc": int(scalar(key + ".rc"))}
    if key not in rec:
        return out
    rows = [row for row in rec[key] if row[0] is not None]
    rect = {"x0": [], "x1": [], "y0": [], "y1": [], "z": [], "lev": []}
    for s in range(0, len(rows), 4):
        g = rows[s:s + 4]
        rect["x0"].append(min(p[0] for p in g))
        rect["x1"].append(max(p[0] for p in g))
        rect["y0"].append(min(p[1] for p in g))
        rect["y1"].append(max(p[1] for p in g))
        rect["z"].append(g[0][2])
        rect["lev"].append(int(g[0][3]))
    out.update(rect)
    out["n_rows"] = len(rec[key])
    out["n_rects"] = len(rect["z"])
    return out


out = {"cases": {}, "grid": {}}
for ds in ("auto", "synthetic", "manual5"):
    inp = rec[ds + ".input"]
    base = {"input": dict(cols(inp, ("x", "y", "z")), n_rows=len(rec[ds + ".rows"]),
                          n_unique=len(inp)),
            "cuts": rec[ds + ".cuts"][0]}
    out["cases"][ds] = {}
    for it in ("thinplatespline", "shepard", "none"):
        k = "%s.%s" % (ds, it)
        out["cases"][ds][it] = dict(base, heatmap=heat(k + ".heatmap"),
                                    filled=gen(k + ".filled"),
                                    line=gen(k + ".line"),
                                    rc={g: int(scalar("%s.%s.rc" % (k, g)))
                                        for g in ("heatmap", "filled", "line")})
    hm = out["cases"][ds]["thinplatespline"]["heatmap"]
    out["grid"][ds] = {"x": sorted(set(hm["x0"]) | set(hm["x1"])),
                       "y": sorted(set(hm["y0"]) | set(hm["y1"]))}
    out["cases"][ds]["rows"] = cols(rec[ds + ".rows"], ("x", "y", "z"))

out["dupseed"] = {it: {"order%d" % o: [scalar("dupseed.%s.order%d.seed%d" % (it, o, s))
                                       for s in range(1, 6)] for o in (1, 2)}
                  for it in ("thinplatespline", "shepard", "none")}
out["dupseed"]["note"] = ("z twoway gives the node (2,2) of manual5 (duplicate z 4 and 5) "
                          "under set sortseed 1-5, rows in two orders")

canon = {}
words = {"rows": cols(rec["words.rows"], ("x", "y", "z"))}
n = int(G("ZC_NWORDS"))
for w in range(1, n + 1):
    word = G("ZC_WORD_%d" % w)
    m = rec["words.w%d.heatmap" % w]
    words[word] = {"rc": int(scalar("words.w%d.rc" % w)), "heatmap_rows": len(m)}
    if word in ("thinplatespline", "shepard", "none"):
        canon[word] = m
for w in range(1, n + 1):
    word = G("ZC_WORD_%d" % w)
    m = rec["words.w%d.heatmap" % w]
    same = [c for c, cm in canon.items() if cm == m]
    words[word]["method"] = same[0] if len(same) == 1 else None
out["interp_abbrev"] = words

deg = {}
for d in ("two_points", "one_x"):
    text = ""
    try:
        with open(os.path.join(work, "deg_%s.log" % d), encoding="utf-8") as fh:
            body = fh.read()
        keep = [l.strip() for l in body.splitlines()
                if l.strip() and not l.lstrip().startswith(("log:", "log type:", "opened on:",
                                                            "name:", "closed on:", "."))
                and not set(l.strip()) <= set("-")]
        text = "\n".join(keep)
    except OSError:
        pass
    deg[d] = {"rc": int(scalar("degenerate.%s.rc" % d)), "message": text,
              "rows": cols(rec["degenerate.%s.rows" % d], ("x", "y", "z")),
              "heatmap": heat("degenerate.%s.heatmap" % d),
              "filled": gen("degenerate.%s.filled" % d)}
out["degenerate"] = deg
out["cost"] = {"n3000": "not run: twoway did not finish n=3000 in ten minutes "
                        "(research/bokeh-web.md section 2)"}

# ---- ZD_ (WP-31 B4b): the drawing records, logs and SVGs.
zd = {}
with open(os.path.join(work, "zd_records.txt"), encoding="utf-8") as fh:
    for ln in fh.read().split("\n"):
        if "\t" not in ln:
            continue
        k, v = ln.split("\t", 1)
        key, field = k.rsplit(".", 1)
        zd.setdefault(key, {})[field] = v


def zd_lines(key):
    p = os.path.join(work, "zd_%s.log" % key)
    try:
        with open(p, encoding="utf-8", errors="replace") as fh:
            lines = [ln.strip() for ln in fh
                     if ln.strip() and not ln.lstrip().startswith((".", "> "))
                     and "log:" not in ln and "log type:" not in ln
                     and "opened on:" not in ln and "closed on:" not in ln
                     and "name:" not in ln and not ln.startswith("---")
                     and ln.strip() != "{p_end}"]
        os.remove(p)
    except OSError:
        lines = []
    return lines


_ZD_STROKE = re.compile(r'<line [^>]*style="stroke:(#[0-9A-Fa-f]{6});stroke-width:([\d.]+)"')
_ZD_KEYFILL = re.compile(r'style="stroke:none;fill:(#[0-9A-Fa-f]{6})"')


def zd_svg(key):
    p = os.path.join(work, "zd_%s.svg" % key)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8", errors="replace") as fh:
        txt = fh.read()
    os.remove(p)
    head, _, tail = txt.partition("Length (in.)</text>")
    strokes = {}
    for c, w in _ZD_STROKE.findall(head):
        strokes["%s %s" % (c.lower(), w)] = strokes.get("%s %s" % (c.lower(), w), 0) + 1
    return {"plot_strokes": strokes,
            "key_fills": [f.lower() for f in _ZD_KEYFILL.findall(tail)]}


def zd_num(v):
    return [float(t) for t in v.split()] if v.strip() else []


for key in G("ZD_KEYS").split():
    d = zd.get(key, {})
    rec = {"rc": int(d.get("rc", "-1")), "lines": zd_lines(key)}
    if "levels" in d:
        L = int(d["levels"] or 0)
        rec.update(type=d.get("type", ""), cuts=zd_num(d.get("cuts", "")),
                   levels=L, rule=d.get("rule", ""),
                   ticks=zd_num(d.get("ticks", "")),
                   use_rule=d.get("use_rule", ""),
                   legend_keys=int(d.get("legend_keys") or 0),
                   format=d.get("format", ""),
                   rgb=["#%02x%02x%02x" % tuple(int(c) for c in d["rgb%d" % i].split())
                        for i in range(1, L + 1) if d.get("rgb%d" % i, "").strip()],
                   labels=[d.get("label%d" % k, "") for k in range(1, L)],
                   lwstyles=[d.get("lw%d" % k, "") for k in range(1, L)],
                   lpstyles=[d.get("lp%d" % k, "") for k in range(1, L)],
                   xrange=[float(d.get("xmin") or "nan"), float(d.get("xmax") or "nan")])
        svg = zd_svg(key)
        if svg is not None:
            rec.update(svg)
    group, _, name = key.partition(".")
    if group == "draw" and name.startswith("scheme_"):
        out.setdefault("scheme", {})[name[len("scheme_"):]] = rec
    else:
        out.setdefault(group, {})[name] = rec
out.setdefault("scheme", {})["note"] = ("twoway contour mpg weight length, scheme(<s>): the "
                                        "scheme's zyx2rule contour and contour_begin/end colours")
for f in ("zd_records.txt",):
    try:
        os.remove(os.path.join(work, f))
    except OSError:
        pass

try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZC_VERSION"), "born_date": G("ZC_BORN"),
                "dash_commit": commit, "extracted": G("ZC_WHEN"),
                "source": "scripts/extract_contour_truth.do"}
with open(G("ZC_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, separators=(",", ":"), sort_keys=True)
    fh.write("\n")
for f in ("git_head.txt", "records.txt", "deg_two_points.log", "deg_one_x.log"):
    try:
        os.remove(os.path.join(work, f))
    except OSError:
        pass
print("wrote", G("ZC_OUT"))
end
