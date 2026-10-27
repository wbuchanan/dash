*! extract_rangept_truth.do -- WP-31 section 21 (B1, B2, B3): measure what
*! twoway rpcap and rpspike draw (the spike, the caps, the marker at y3, the
*! y range, the axis title, the key, horizontal, msize(), a weight), the
*! words and return codes twoway gives for a wrong variable count, and the
*! manual's words for sunflower and matamatrix(), so dash draws the two
*! range-point types as twoway does and refuses the other two by name.
*!
*! Output: test/fixtures/rangept_truth.json
*!
*! Run through the slot wrapper only (CLAUDE.md rule 10):
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_rangept_truth.do
*!
*! METHOD.  sysuse auto, scheme s2color; lo = turn - 5, hi = turn + 5, the
*! marker variable turn, x = weight.  twoway only: dash is never run.  Per
*! graph: the plot's class values (marker size, serset N, the four
*! variables' names, bar_drop_to), the y axis's major min/max and title,
*! the legend's key count, and from the SVG the circles (the y3 markers)
*! and the lines.  Refusals: rc and the error line, from a log at linesize
*! 255.  The git commit is read from a file `shell' wrote, never with
*! shell=True.  Every SVG is erased.

clear all
set more off
set linesize 255

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_rangept_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_rangept_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZR_REPO "`repo'"
global ZR_OUT "${ZR_REPO}/test/fixtures/rangept_truth.json"
global dash_nobrowser 1

local work "`c(tmpdir)'dash_rangept_probe"
capture mkdir "`work'"
global ZR_WORK "`work'"


quietly shell git -C "${ZR_REPO}" rev-parse HEAD > "${ZR_WORK}/git_head.txt"
global ZR_VERSION "`c(stata_version)'"
global ZR_BORN "`c(born_date)'"
global ZR_WHEN "`c(current_date)' `c(current_time)'"

* The manual's lines the refusals paraphrase (twoway_sunflower.sthlp,
* twoway_mata.sthlp), read as written.
foreach f in twoway_sunflower twoway_mata {
    global ZR_HELP_`f' ""
    capture findfile `f'.sthlp
    if !_rc global ZR_HELP_`f' "`r(fn)'"
}

sysuse auto, clear
set scheme s2color
generate lo = turn - 5
generate hi = turn + 5
generate zero = 0

* Graphs: key | command.  Class values and the SVG of each.
global ZR_GRAPHS ""
local G1 "rpcap|twoway rpcap lo hi turn weight"
local G2 "rpcap_msize|twoway rpcap lo hi turn weight, msize(large)"
local G3 "rpcap_hz|twoway rpcap lo hi turn weight, horizontal"
local G4 "rpcap_weight|twoway rpcap lo hi turn weight [aw=price]"
local G5 "rpspike|twoway rpspike lo hi turn weight"
local G6 "rpspike_hz|twoway rpspike lo hi turn weight, horizontal"
local G7 "rcap_scatter|twoway rcap lo hi weight || scatter turn weight"
local G8 "rpspike_weight|twoway rpspike lo hi turn weight [aw=price]"
local G9 "rpcap_colorvar|twoway rpcap lo hi turn weight, colorvar(rep78)"
local G10 "rpspike_colorvar|twoway rpspike lo hi turn weight, colorvar(rep78)"
forvalues k = 1/10 {
    gettoken key rest : G`k', parse("|")
    gettoken bar cmd : rest, parse("|")
    local opt = cond(strpos(`"`cmd'"', ","), " ", ", ")
    quietly `cmd' `opt' name(zr, replace)
    local p ".zr.plotregion1.plot1"
    local ss "`p'.serset.sers"
    global ZRG_`key'_cls "`.zr.plotregion1.plot1.style.marker.size.gmval'|`.zr.plotregion1.plot1.serset.N'|`.zr.plotregion1.plot1.bar_drop_to.stylename'|`.zr.legend.keys.arrnels'|`.zr.yaxis1.major.min'|`.zr.yaxis1.major.max'|`.zr.xaxis1.major.min'|`.zr.xaxis1.major.max'"
    global ZRG_`key'_vars ""
    foreach v in yvar y2var y3var xvar wvar {
        local id "`.zr.plotregion1.plot1.`v''"
        local nm ""
        if "`id'" != "" & "`id'" != "." capture local nm "`.zr.plotregion1.plot1.serset.sers[`id'].name'"
        global ZRG_`key'_vars "${ZRG_`key'_vars}`v'=`nm'|"
    }
    global ZRG_`key'_yt `"`.zr.yaxis1.title.text[1]'"'
    global ZRG_`key'_xt `"`.zr.xaxis1.title.text[1]'"'
    quietly graph export "${ZR_WORK}/g_`key'.svg", replace
    global ZR_GRAPHS "${ZR_GRAPHS} `key'"
}
graph drop _all

* Axis titles: the three labels differ; the three labels are equal.
label variable lo "Low"
label variable hi "High"
label variable turn "Turn"
quietly twoway rpcap lo hi turn weight, name(zr, replace)
global ZR_title_differs `"`.zr.yaxis1.title.text[1]'"'
label variable lo "Turn"
label variable hi "Turn"
quietly twoway rpcap lo hi turn weight, name(zr, replace)
global ZR_title_same `"`.zr.yaxis1.title.text[1]'"'
quietly twoway rpcap lo hi turn weight, horizontal name(zr, replace)
global ZR_title_same_hz `"`.zr.xaxis1.title.text[1]'"'
graph drop _all
label variable lo ""
label variable hi ""
label variable turn "Turn Circle (ft.)"

mata: M = (1, 2 \ 3, 4)

* The rc and error line of each probe.
global ZR_PROBES ""
quietly log using "${ZR_WORK}/probes.log", text replace name(zrlog)
local P1 "counts.rpcap_1|twoway rpcap turn"
local P2 "counts.rpcap_2|twoway rpcap turn weight"
local P3 "counts.rpcap_3|twoway rpcap lo hi weight"
local P4 "counts.rpcap_4|twoway rpcap lo hi turn weight"
local P5 "counts.rpcap_5|twoway rpcap lo hi turn weight price"
local P6 "counts.rpspike_1|twoway rpspike turn"
local P7 "counts.rpspike_2|twoway rpspike turn weight"
local P8 "counts.rpspike_3|twoway rpspike lo hi weight"
local P9 "counts.rpspike_4|twoway rpspike lo hi turn weight"
local P10 "counts.rpspike_5|twoway rpspike lo hi turn weight price"
local P11 "abbrev.rpca|twoway rpca lo hi turn weight"
local P12 "abbrev.rpspik|twoway rpspik lo hi turn weight"
local P13 "abbrev.sunflow|twoway sunflow mpg weight"
local P14 "draw.sunflower|twoway sunflower mpg weight"
local P15 "barwidth.rpcap|twoway rpcap lo hi turn weight, barwidth(.5)"
local P16 "barwidth.rpspike|twoway rpspike lo hi turn weight, barwidth(.5)"
local P17 "advice.matamatrix|twoway scatter matamatrix(nosuch)"
local P18 "matamatrix.defined|twoway scatter matamatrix(M)"
local P19 "matamatrix.upper|twoway scatter MATAMATRIX(M)"
local P20 "matamatrix.line|twoway line matamatrix(M)"
local P21 "jitter.rpcap|twoway rpcap lo hi turn weight, jitter(5) jitterseed(1)"
local P22 "hzvt.rpcap|twoway rpcap lo hi turn weight, horizontal vertical"
local P23 "headlabel.rpcap|twoway rpcap lo hi turn weight, headlabel"
local P24 "mlabel.rpcap|twoway rpcap lo hi turn weight, mlabel(make)"
local P25 "fw.rpcap|twoway rpcap lo hi turn weight [fw=rep78]"
local P26 "pw.rpcap|twoway rpcap lo hi turn weight [pw=price]"
local P27 "iw.rpcap|twoway rpcap lo hi turn weight [iw=price]"
local P28 "string.rpcap|twoway rpcap lo hi make weight"
local P29 "recast.rpcap_rspike|twoway rpcap lo hi turn weight, recast(rspike)"
local P30 "recast.rpcap_scatter|twoway rpcap lo hi turn weight, recast(scatter)"
local P31 "recast.rpcap_rpspike|twoway rpcap lo hi turn weight, recast(rpspike)"
local P32 "recast.rcap_rpcap|twoway rcap lo hi weight, recast(rpcap)"
local P33 "sort.rpcap|twoway rpcap lo hi turn weight, sort"
local P34 "plain.rpcap|twoway rpcap lo hi turn weight"
local P35 "mlabvpos.rpcap|twoway rpcap lo hi turn weight, mlabel(make) mlabvposition(rep78)"
local P36 "recast.rpcap_rcap|twoway rpcap lo hi turn weight, recast(rcap)"
local P37 "vertical.rpcap|twoway rpcap lo hi turn weight, vertical"
local P38 "vertical.rpspike|twoway rpspike lo hi turn weight, vertical"
local P39 "horizontal.rpspike|twoway rpspike lo hi turn weight, horizontal"
local P40 "horizontal.rpcap|twoway rpcap lo hi turn weight, horizontal"
* The weight text as the y3 view reads it, and when the weight sizes
* nothing (WP-31 B1, beside section 20's weighted_markers_truth.json).
local P41 "wexp.rpcap_minus|twoway rpcap lo hi turn weight [aw=price-price]"
local P42 "wexp.rpcap_paren|twoway rpcap lo hi turn weight [aw=(price)]"
local P43 "wexp.rpcap_plus|twoway rpcap lo hi turn weight [aw=price+1]"
local P44 "wzero.rpcap|twoway rpcap lo hi turn weight [aw=zero]"
local P45 "wmlabel.rpcap|twoway rpcap lo hi turn weight [aw=price], mlabel(make)"
local P46 "wpoint.rpcap|twoway rpcap lo hi turn weight [aw=price], msymbol(p)"
local P47 "wexp.rpspike_minus|twoway rpspike lo hi turn weight [aw=price-price]"
local P48 "wzero.rpspike|twoway rpspike lo hi turn weight [aw=zero]"
local P49 "wfw.rpspike|twoway rpspike lo hi turn weight [fw=rep78]"
forvalues k = 1/49 {
    gettoken key rest : P`k', parse("|")
    gettoken bar cmd : rest, parse("|")
    local opt = cond(strpos(`"`cmd'"', ","), " ", ", ")
    display "ZR-MARK `key'"
    capture noisily `cmd' `opt' name(zr, replace)
    global ZRP_`k'_rc = _rc
    if _rc == 0 {
        quietly graph export "${ZR_WORK}/p_`k'.svg", replace
    }
    display "ZR-END `key'"
    capture graph drop zr
    global ZR_PROBES "${ZR_PROBES} `key'"
}
quietly log close zrlog

python:
import json, os, re, sys
from sfi import Macro

G = Macro.getGlobal
sys.path.insert(0, os.path.join(G("ZR_REPO"), "scripts"))
from svg_truth import svg_document  # noqa: E402

work = G("ZR_WORK")
written = []


def _num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


graphs = {}
for key in G("ZR_GRAPHS").split():
    sp = os.path.join(work, "g_%s.svg" % key)
    written.append(sp)
    doc = svg_document(sp)
    cls = (G("ZRG_%s_cls" % key) or "").split("|")
    cls += [""] * (8 - len(cls))
    roles = {}
    for part in (G("ZRG_%s_vars" % key) or "").split("|"):
        if "=" in part:
            k, v = part.split("=", 1)
            roles[k] = v
    circ = [c for c in doc["circles"] if c.get("r") is not None]
    radii = sorted(set(round(c["r"], 3) for c in circ))
    graphs[key] = {
        "marker_size_gmval": _num(cls[0]),
        "N": _num(cls[1]),
        "bar_drop_to": cls[2],
        "legend_keys": _num(cls[3]),
        "yaxis_major": [_num(cls[4]), _num(cls[5])],
        "xaxis_major": [_num(cls[6]), _num(cls[7])],
        "roles": roles,
        "ytitle": G("ZRG_%s_yt" % key),
        "xtitle": G("ZRG_%s_xt" % key),
        "n_circles": len(circ),
        "n_radii": len(radii),
        "radii": radii if len(radii) <= 4 else radii[:1] + radii[-1:],
        "n_hlines": len(doc["hlines"]),
        "n_vlines": len(doc["vlines"]),
        "n_paths": len(doc["paths"]),
    }

with open(os.path.join(work, "probes.log"), encoding="utf-8",
          errors="replace") as fh:
    plog = fh.read().splitlines()
written.append(os.path.join(work, "probes.log"))
msgs, cur = {}, None
for ln in plog:
    s = ln.strip()
    m = re.match(r"^ZR-MARK (\S+)$", s)
    if m:
        cur = m.group(1)
        continue
    if re.match(r"^ZR-END ", s):
        cur = None
        continue
    if cur and cur not in msgs and s and not s.startswith(".") \
            and not s.startswith("r(") and not s.startswith("(note"):
        msgs[cur] = s
# A weight sizes the y3 markers when the weighted graph draws more distinct
# radii than the unweighted one (the unweighted draws the marker and its
# key: two radii).
for wk, base in (("rpcap_weight", "rpcap"), ("rpspike_weight", "rpspike")):
    more = graphs[wk]["n_radii"] > graphs[base]["n_radii"]
    graphs[wk]["radii_vary_with_weight"] = more

probes = {}
for k, key in enumerate(G("ZR_PROBES").split(), 1):
    rc = int(G("ZRP_%d_rc" % k))
    probes[key] = {"rc": rc, "message": msgs.get(key) if rc else None}
    sp = os.path.join(work, "p_%d.svg" % k)
    if rc == 0 and os.path.exists(sp):
        # What the graph drew: its markers, vertical and horizontal
        # lines, and the texts that are no axis label or title.
        written.append(sp)
        doc = svg_document(sp)
        probes[key]["n_circles"] = len(doc["circles"])
        probes[key]["n_radii"] = len(set(round(c["r"], 3)
                                         for c in doc["circles"]
                                         if c.get("r") is not None))
        probes[key]["n_vlines"] = len(doc["vlines"])
        probes[key]["n_hlines"] = len(doc["hlines"])
        probes[key]["n_texts"] = len(doc["texts"])
        # The markers' centres and the vertical lines, rounded: a jitter
        # moves the one and leaves the other.
        probes[key]["centres"] = sorted(
            [round(c["cx"], 1), round(c["cy"], 1)] for c in doc["circles"]
            if c.get("cx") is not None)[:8]
        probes[key]["vline_x"] = sorted(
            round(v["x1"], 1) for v in doc["vlines"])[:8]


def _help_lines(path, lo, hi):
    if not path:
        return None
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().splitlines()
    return lines[lo - 1:hi]


advice = {
    "sunflower": _help_lines(G("ZR_HELP_twoway_sunflower"), 35, 39),
    "matamatrix_title": _help_lines(G("ZR_HELP_twoway_mata"), 13, 13),
    "matamatrix": probes.get("advice.matamatrix"),
}
titles = {"differs": G("ZR_title_differs"), "same": G("ZR_title_same"),
          "same_hz": G("ZR_title_same_hz")}

try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
written.append(os.path.join(work, "git_head.txt"))
out = {"draw": graphs, "probes": probes, "advice": advice, "title": titles}
out["_meta"] = {"stata_version": G("ZR_VERSION"), "born_date": G("ZR_BORN"),
                "dash_commit": commit, "extracted": G("ZR_WHEN"),
                "source": "scripts/extract_rangept_truth.do"}
with open(G("ZR_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
for p in written:
    try:
        os.remove(p)
    except OSError:
        pass
print("wrote", G("ZR_OUT"))
end
