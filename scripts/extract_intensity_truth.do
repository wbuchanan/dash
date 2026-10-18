*! extract_intensity_truth.do -- WP-30 section 16 (P1.2b): measure the fill
*! colour and opacity twoway draws for markers, bars, areas, range plots,
*! histograms and confidence bands, with and without fintensity(), under
*! the shipped schemes and two user schemes, so dash's opaque intensity
*! blend is proved against twoway itself.
*!
*! Output: test/fixtures/intensity_truth.json
*!
*! Run through the slot wrapper only (CLAUDE.md rule 10):
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_intensity_truth.do
*!
*! METHOD.  sysuse auto, lo = mpg - 3, hi = mpg + 3, sorted by weight.
*! Each probe (_ob_probe) runs one twoway command under `capture noisily'
*! inside its own text log (twoway's notes are kept), records the rc and
*! exports the graph to SVG.  One python block then reads every SVG
*! through scripts/svg_truth.py and records the commonest fill of the
*! probe's kind (markers: circles and paths; bars and histograms: the
*! narrow rects; areas, range areas and bands: the filled paths) with its
*! fill-opacity (absent = 1).  It is twoway-only: dash is never run.  The
*! user schemes are written into a tempfile-named directory under
*! c(tmpdir), never into the repository.  The git commit is read from a
*! file `shell' wrote, never with shell=True.  Every SVG and log is erased.

clear all
set more off
set linesize 200

* Root: DASH_REPO, else the current directory when it is a dash tree.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_intensity_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_intensity_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the dash repository"'
    exit 601
}
global OB_REPO "`repo'"
global OB_OUT "${OB_REPO}/test/fixtures/intensity_truth.json"

adopath ++ "${OB_REPO}/"
global dash_nobrowser 1

version 19
set graphics off

if `"`c(python_exec)'"' == "" {
    display as error "extract_intensity_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

* The work directory: tempfile-named, under c(tmpdir).
tempfile _ob_name
mata: st_global("OB_WORK", pathjoin(st_global("c(tmpdir)"), "dash_ob_" + pathbasename(st_local("_ob_name"))))
mata: st_global("OB_WORK", subinstr(subinstr(st_global("OB_WORK"), ".tmp", ""), ".", "_"))
capture mkdir "${OB_WORK}"

* The two user schemes of plan section 16 Evidence E3.
tempname fh
file open `fh' using "${OB_WORK}/scheme-s16up.scheme", write text replace
file write `fh' "#include s2color" _n "intensity p1bar inten200" _n "intensity p1area 150" _n
file close `fh'
file open `fh' using "${OB_WORK}/scheme-s16dn.scheme", write text replace
file write `fh' "#include s2color" _n "intensity p1bar inten40" _n "intensity p1area inten40" _n
file close `fh'
adopath ++ "${OB_WORK}/"

quietly shell git -C "${OB_REPO}" rev-parse HEAD > "${OB_WORK}/git_head.txt"
global OB_VERSION "`c(stata_version)'"
global OB_BORN "`c(born_date)'"
global OB_WHEN "`c(current_date)' `c(current_time)'"

sysuse auto, clear
generate lo = mpg - 3
generate hi = mpg + 3
sort weight

global OB_IDS ""
global OB_SEQ = 0
capture program drop _ob_probe
program define _ob_probe
    * _ob_probe id kind scheme owner command
    gettoken id 0 : 0
    gettoken kind 0 : 0
    gettoken scheme 0 : 0
    gettoken owner 0 : 0
    local cmd = strtrim(`"`0'"')
    local opt = cond(strpos(`"`cmd'"', ",") & substr(`"`cmd'"', 1, 1) != "(", " ", ", ")
    * Files are numbered, not named by id: the file system may fold case
    * (fi_full and fi_Full would share one file).
    global OB_SEQ = ${OB_SEQ} + 1
    local f "${OB_WORK}/p${OB_SEQ}"
    global OBF_`id' "p${OB_SEQ}"
    quietly log using "`f'.log", text replace name(obp)
    capture noisily twoway `cmd' `opt' scheme(`scheme') name(ob, replace)
    local rc = _rc
    quietly log close obp
    global OBR_`id' = `rc'
    global OBK_`id' "`kind'"
    global OBS_`id' "`scheme'"
    global OBO_`id' "`owner'"
    global OBC_`id' `"`cmd'"'
    if `rc' == 0 {
        quietly graph export "`f'.svg", replace
    }
    global OB_IDS "${OB_IDS} `id'"
    capture graph drop ob
end

local B "bar mpg rep78 if rep78<."
local N "lcolor(none)"

* marker
foreach s in s2color stcolor s1rcolor economist sttrans {
    local sid = cond("`s'" == "s2color", "", "_`s'")
    _ob_probe marker`sid'_1 marker `s' - scatter mpg weight
    _ob_probe marker`sid'_2 marker `s' - connected mpg weight
    _ob_probe marker`sid'_3 marker `s' - dot mpg rep78 if rep78<.
    _ob_probe marker`sid'_4 marker `s' - rconnected lo hi weight
}
_ob_probe marker_pct marker s2color - scatter mpg weight, mcolor(navy%50)
_ob_probe marker_pct_s1rcolor marker s1rcolor - scatter mpg weight, mcolor(navy%50)

* bar
foreach s in s2color stcolor economist s1mono sj s1rcolor sttrans {
    local sid = cond("`s'" == "s2color", "", "_`s'")
    _ob_probe bar`sid' bar `s' - `B', `N'
}
_ob_probe bar_p2 bar s2color - (`B', `N') (bar price rep78 if rep78<., yaxis(2) `N')
_ob_probe bar_user_1 bar s2color - `B', fcolor(yellow) `N'
_ob_probe bar_user_2 bar s2color - `B', color(yellow) `N'
_ob_probe bar_user_3 bar s2color - `B', fcolor(navy%50) `N'
_ob_probe bar_user_sttrans bar sttrans - `B', fcolor(navy) `N'
_ob_probe bar_user_stcolor bar stcolor - `B', fcolor(navy) `N'

* fi: fcolor(navy) fintensity(V) under s2color
foreach v in 50 150 1000 0 -5 5000 6000 9999 inten200 max full inten50 . abc inten150 INTEN50 Full .a {
    local vid = cond("`v'" == ".", "dot", cond("`v'" == ".a", "dota", subinstr("`v'", "-", "m", 1)))
    _ob_probe fi_`vid' fi s2color - `B', fcolor(navy) fintensity(`v') `N'
}
foreach v in 50 150 0 1 {
    _ob_probe fi_s1rcolor_`v' fi s1rcolor - `B', fcolor(navy) fintensity(`v') `N'
}
_ob_probe fi_s1rcolor_red0 fi s1rcolor - `B', fcolor(red) fintensity(0) `N'
_ob_probe fi_s1rcolor_rgb1 fi s1rcolor - `B', fcolor("200 100 3") fintensity(1) `N'
_ob_probe fi_s1rcolor_yellow10000 fi s1rcolor - `B', fcolor(yellow) fintensity(10000) `N'

* area
_ob_probe area_1 area s2color - area mpg weight, `N'
_ob_probe area_2 area s2color - area mpg weight, fcolor(yellow) `N'
_ob_probe area_3 area s2color - area mpg weight, fcolor(navy) fintensity(50) `N'
_ob_probe area_s1rcolor_3 area s1rcolor - area mpg weight, fcolor(navy) fintensity(50) `N'

* range
_ob_probe range_1 range s2color - rbar lo hi rep78 if rep78<., `N'
_ob_probe range_2 range s2color - rarea lo hi weight, `N'
_ob_probe range_3 range s2color - rbar lo hi rep78 if rep78<., color(red)
_ob_probe range_4 range s2color - rarea lo hi weight, color(red) `N'
_ob_probe range_s1rcolor_1 range s1rcolor - rbar lo hi rep78 if rep78<., `N'

* hist (the default histogram's colour is section 24's)
foreach s in s2color stcolor s1rcolor {
    local sid = cond("`s'" == "s2color", "", "_`s'")
    * stcolor's `intensity histogram inten90' is section 24's (D-16a).
    local own = cond("`s'" == "stcolor", "S24", "-")
    _ob_probe hist`sid'_1 hist `s' `own' histogram mpg, fcolor(navy) `N'
    _ob_probe hist`sid'_2 hist `s' - histogram mpg, fcolor(navy) fintensity(50) `N'
    _ob_probe hist`sid'_3 hist `s' S24 histogram mpg, `N'
}

* band
_ob_probe band_1 band s2color - lfitci mpg weight
_ob_probe band_150 band s2color - lfitci mpg weight, fintensity(150)
_ob_probe band_m5 band s2color - lfitci mpg weight, fintensity(-5)
_ob_probe band_s1rcolor_50 band s1rcolor - lfitci mpg weight, fintensity(50)

* userscheme
foreach s in s16up s16dn {
    _ob_probe userscheme_`s'_1 userscheme `s' - `B', `N'
    _ob_probe userscheme_`s'_2 userscheme `s' - area mpg weight, `N'
}

python:
import json, os, re, sys
from collections import Counter
from sfi import Macro

G = Macro.getGlobal
sys.path.insert(0, os.path.join(G("OB_REPO"), "scripts"))
from svg_truth import svg_document, svg_marker_fills  # noqa: E402

work = G("OB_WORK")
written = [os.path.join(work, n) for n in
           ("scheme-s16up.scheme", "scheme-s16dn.scheme", "git_head.txt")]
_RECT = re.compile(r"<rect\b([^>]*)>")
_ATTR = re.compile(r'([\w:-]+)="([^"]*)"')


def _style(a):
    out = {}
    for part in a.get("style", "").split(";"):
        k, _, v = part.partition(":")
        if k.strip():
            out[k.strip().lower()] = v.strip()
    return out


def _rect_strokes(path, canvas_w):
    """The strokes of the narrow rects: Stata draws a bar's outline as a
    second rect, fill none."""
    with open(path, encoding="utf-8") as fh:
        txt = fh.read()
    out = []
    for m in _RECT.finditer(txt):
        a = dict(_ATTR.findall(m.group(1)))
        st = _style(a)
        try:
            w = float(a.get("width", "0"))
        except ValueError:
            w = 0.0
        stroke = (st.get("stroke") or a.get("stroke") or "").upper()
        if 0 < w < canvas_w / 3.0 and stroke and stroke != "NONE":
            out.append(stroke)
    return out


def _rects(path, canvas_w):
    """The narrow rects (bars, bins) as (fill, opacity, stroke): svg_truth's
    rect record carries no fill-opacity, so the opacity is read here."""
    with open(path, encoding="utf-8") as fh:
        txt = fh.read()
    out = []
    for m in _RECT.finditer(txt):
        a = dict(_ATTR.findall(m.group(1)))
        st = _style(a)
        try:
            w = float(a.get("width", "0"))
        except ValueError:
            w = 0.0
        if not (0 < w < canvas_w / 3.0):
            continue
        fill = (st.get("fill") or a.get("fill") or "").upper()
        if not fill or fill == "NONE":
            continue
        op = st.get("fill-opacity") or a.get("fill-opacity")
        out.append((fill, float(op) if op else None,
                    (st.get("stroke") or a.get("stroke") or "").upper()))
    return out


_USE = re.compile(r"<use\b([^>]*)>")


def _uses(path):
    """The filled <use> elements (a confidence band is drawn as one) as
    (fill, opacity)."""
    with open(path, encoding="utf-8") as fh:
        txt = fh.read()
    out = []
    for m in _USE.finditer(txt):
        st = _style(dict(_ATTR.findall(m.group(1))))
        fill = (st.get("fill") or "").upper()
        if fill and fill != "NONE":
            op = st.get("fill-opacity")
            out.append((fill, float(op) if op else None))
    return out


def _dominant(items):
    c = Counter((f, o) for f, o, *_ in items)
    if not c:
        return None, None, []
    (f, o), _ = c.most_common(1)[0]
    order = []
    for it in items:
        if it[0] not in order:
            order.append(it[0])
    return f, o, order


probes = {}
for pid in G("OB_IDS").split():
    kind = G("OBK_" + pid)
    rec = {"kind": kind, "scheme": G("OBS_" + pid),
           "command": G("OBC_" + pid), "rc": int(float(G("OBR_" + pid))),
           "notes": [], "fill": None, "opacity": None, "fills": [],
           "stroke": None, "owner": None if G("OBO_" + pid) == "-"
           else G("OBO_" + pid)}
    stem = G("OBF_" + pid)
    logp = os.path.join(work, stem + ".log")
    if os.path.exists(logp):
        with open(logp, encoding="utf-8", errors="replace") as fh:
            rec["notes"] = [ln.strip() for ln in fh
                            if ln.strip().startswith("(note:")]
        written.append(logp)
    svg = os.path.join(work, stem + ".svg")
    if os.path.exists(svg):
        written.append(svg)
        doc = svg_document(svg)
        if kind == "marker":
            # The plot's markers are the largest filled circles: dot's
            # guide dots are small black ones.
            circ = [c for c in doc["circles"]
                    if c.get("fill") and c["fill"] != "none" and c.get("r")]
            if circ:
                rmax = max(c["r"] for c in circ)
                items = [(c["fill"].upper(), c.get("fill_opacity"))
                         for c in circ if c["r"] == rmax]
            else:
                mf = svg_marker_fills(svg)
                items = [(c.upper(), (e["opacity"] or [None])[0])
                         for c, e in mf.items() for _ in range(e["n"])]
        elif kind in ("bar", "fi", "hist") or (
                kind in ("range", "userscheme")
                and re.match(r"\(?\s*r?bar\b", rec["command"])):
            items = _rects(svg, doc["canvas"]["w"])
        else:
            items = [((p["fill"] or "").upper(), p.get("fill_opacity"))
                     for p in doc["paths"]
                     if p.get("fill") and p["fill"] != "none"]
            items += _uses(svg)
        f, o, order = _dominant(items)
        rec["fill"], rec["opacity"] = f, o
        if pid == "bar_p2":
            rec["fills"] = order
        if kind == "range" and "color(red)" in rec["command"] and \
                rec["command"].startswith("rbar"):
            strokes = Counter(_rect_strokes(svg, doc["canvas"]["w"]))
            rec["stroke"] = strokes.most_common(1)[0][0] if strokes else None
    probes[pid] = rec

try:
    with open(os.path.join(work, "git_head.txt"), encoding="utf-8") as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out = {"_meta": {"stata_version": G("OB_VERSION"), "born_date": G("OB_BORN"),
                 "source": "scripts/extract_intensity_truth.do",
                 "dash_commit": commit, "extracted": G("OB_WHEN"),
                 "rule": "E4",
                 "excluded": {"navy_fi_5200":
                              "P1.13 UNCLEAR, research p1-13 section 3"}},
       "probes": probes}
with open(G("OB_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
for p in written:
    try:
        os.remove(p)
    except OSError:
        pass
try:
    os.rmdir(work)
except OSError:
    pass
print("intensity_truth: wrote %d probes" % len(probes))
end
