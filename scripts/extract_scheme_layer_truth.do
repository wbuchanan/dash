*! extract_scheme_layer_truth.do -- WP-30 section 24 (P1.4a): measure the
*! opacity, histogram style, marker symbols and marker colours twoway draws
*! on every layer type, so dash's scheme reach is proved against twoway.
*!
*! Output: test/fixtures/scheme_layer_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_scheme_layer_truth.do
*!
*! METHOD.  sysuse auto, lo = mpg - 3, hi = mpg + 3, y1..y15 = mpg + i,
*! sorted by weight.  Each probe (_sk_probe) runs one twoway command with
*! its axes, plot-region frame and legend off, so the SVG holds only the
*! layers, records the rc and exports the graph to SVG.  One python block
*! reads every SVG through scripts/svg_layer.py and records each probe's
*! distinct element styles and, for the symbol probes, each layer's first
*! marker (shape, hollow, stroked extent, colours).  It is twoway-only:
*! dash is never run.  The user schemes are written into a
*! tempfile-named directory under c(tmpdir), never into the repository.
*! The git commit is read from a file `shell' wrote, never with
*! shell=True.  Every SVG is erased.

clear all
set more off
set linesize 200

* Root: DASH_REPO, else the current directory when it is a dash tree.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_scheme_layer_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_scheme_layer_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the dash repository"'
    exit 601
}
global OB_REPO "`repo'"
global OB_OUT "${OB_REPO}/test/fixtures/scheme_layer_truth.json"

adopath ++ "${OB_REPO}/"
global dash_nobrowser 1

version 19
set graphics off


* The work directory: tempfile-named, under c(tmpdir).
tempfile _sk_name
mata: st_global("OB_WORK", pathjoin(st_global("c(tmpdir)"), "dash_sk_" + pathbasename(st_local("_sk_name"))))
mata: st_global("OB_WORK", subinstr(subinstr(st_global("OB_WORK"), ".tmp", ""), ".", "_"))
capture mkdir "${OB_WORK}"

* The four user schemes of plan section 24's Stata truth.
tempname fh
file open `fh' using "${OB_WORK}/scheme-w24g.scheme", write text replace
file write `fh' "#include s2color" _n "color pmarkfill green" _n "color pmarkline blue" _n
file close `fh'
file open `fh' using "${OB_WORK}/scheme-w24m.scheme", write text replace
file write `fh' "#include s2color" _n "color p1mark green" _n "color pmark red" _n
file close `fh'
file open `fh' using "${OB_WORK}/scheme-w24f.scheme", write text replace
file write `fh' "#include s2color" _n "color p1markfill green" _n "color p1markline blue" _n
file close `fh'
file open `fh' using "${OB_WORK}/scheme-w24h.scheme", write text replace
file write `fh' "#include s2color" _n "color histogram red" _n "intensity histogram inten50" _n "color histogram_line blue" _n "linewidth histogram vthick" _n
file close `fh'
* Section 33's six user schemes (P1.4b): the marker-label chain and the
* colour key's text and tick keys.
file open `fh' using "${OB_WORK}/scheme-w33a.scheme", write text replace
file write `fh' "#include s2color" _n "color plabel green" _n "gsize plabel large" _n
file close `fh'
file open `fh' using "${OB_WORK}/scheme-w33b.scheme", write text replace
file write `fh' "#include s2color" _n "color p1label blue" _n "gsize p1label vlarge" _n "color plabel green" _n
file close `fh'
file open `fh' using "${OB_WORK}/scheme-w33c.scheme", write text replace
file write `fh' "#include s2color" _n "color label white" _n "gsize label huge" _n
file close `fh'
file open `fh' using "${OB_WORK}/scheme-w33d.scheme", write text replace
file write `fh' "#include s2color" _n "color p1 red" _n
file close `fh'
file open `fh' using "${OB_WORK}/scheme-w33k.scheme", write text replace
file write `fh' "#include s2color" _n "gsize axis_title vlarge" _n "color axis_title red" _n "gsize tick_label small" _n "color tick_label blue" _n
file close `fh'
file open `fh' using "${OB_WORK}/scheme-w33t.scheme", write text replace
file write `fh' "#include s2color" _n "color axisline orange" _n "color tick purple" _n "color clegend_line green" _n "color clegend blue" _n
file close `fh'
adopath ++ "${OB_WORK}/"

quietly shell git -C "${OB_REPO}" rev-parse HEAD > "${OB_WORK}/git_head.txt"
global OB_VERSION "`c(stata_version)'"
global OB_BORN "`c(born_date)'"
global OB_WHEN "`c(current_date)' `c(current_time)'"

sysuse auto, clear
generate lo = mpg - 3
generate hi = mpg + 3
forvalues i = 1/15 {
    generate y`i' = mpg + `i'
}
sort weight

global OB_IDS ""
global OB_SEQ = 0
capture program drop _sk_probe
program define _sk_probe
    * _sk_probe id group scheme command
    gettoken id 0 : 0
    gettoken group 0 : 0
    gettoken scheme 0 : 0
    local cmd = strtrim(`"`0'"')
    local opt = cond(strpos(`"`cmd'"', ",") & substr(`"`cmd'"', 1, 1) != "(", " ", ", ")
    global OB_SEQ = ${OB_SEQ} + 1
    local f "${OB_WORK}/p${OB_SEQ}"
    global OBF_`id' "p${OB_SEQ}"
    capture noisily twoway `cmd' `opt' scheme(`scheme') legend(off) xscale(off) yscale(off) plotregion(style(none)) name(sk, replace)
    local rc = _rc
    global OBR_`id' = `rc'
    global OBG_`id' "`group'"
    global OBS_`id' "`scheme'"
    global OBC_`id' `"`cmd'"'
    if `rc' == 0 {
        quietly graph export "`f'.svg", replace
    }
    global OB_IDS "${OB_IDS} `id'"
    capture graph drop sk
end

* opacity: every layer type under sttrans
local i = 0
foreach c in "lfit mpg weight" "qfit mpg weight" "lowess mpg weight" "lpoly mpg weight" "fpfit mpg weight" "mspline mpg weight" "mband mpg weight" "kdensity mpg" "function y=x/1000, range(1760 4840)" "lfitci mpg weight" "qfitci mpg weight" "lpolyci mpg weight" "fpfitci mpg weight" "spike mpg weight" "rspike lo hi weight" "rcap lo hi weight" "rcapsym lo hi weight" "dropline mpg weight" "rline lo hi weight" "rscatter lo hi weight" "rbar lo hi rep78 if rep78<." "rarea lo hi weight" "area mpg weight" "scatteri 20 3000 30 4000" "pci 20 3000 30 4000" "pcspike mpg weight price length" "pcarrow mpg weight price length in 1/5" "pcarrowi 20 3000 30 4000" "pcbarrow mpg weight price length in 1/5" "pccapsym mpg weight price length in 1/5" "pcscatter mpg weight price length" "histogram mpg" {
    local ++i
    gettoken t : c
    _sk_probe op_`t' opacity sttrans `c'
}
_sk_probe op_rarea_s2color opacity s2color rarea lo hi weight
_sk_probe op_area_s2color opacity s2color area mpg weight

* opacity_user
_sk_probe ou_rspike_red opacity_user sttrans rspike lo hi weight, lcolor(red)
_sk_probe ou_lfit_red70 opacity_user sttrans lfit mpg weight, lcolor(red%70)
_sk_probe ou_rarea_red opacity_user sttrans rarea lo hi weight, fcolor(red)
_sk_probe ou_hist_red opacity_user sttrans histogram mpg, color(red)
_sk_probe ou_lfitci_ci opacity_user sttrans lfitci mpg weight, pstyle(ci)
_sk_probe ou_lfitci_p3 opacity_user sttrans lfitci mpg weight, pstyle(p3)

* histogram
foreach s in s2color stcolor s1mono s2mono economist s1rcolor sttrans stmono1 {
    _sk_probe hi_`s' histogram `s' histogram mpg
    _sk_probe hi2_`s' histogram `s' (histogram mpg) (histogram trunk)
}
_sk_probe ho_fcolor histogram_opt s2color histogram mpg, fcolor(red)
_sk_probe ho_color histogram_opt s2color histogram mpg, color(red)
_sk_probe ho_lcolor histogram_opt s2color histogram mpg, lcolor(blue)
_sk_probe ho_navy_stcolor histogram_opt stcolor histogram mpg, fcolor(navy)
_sk_probe ho_w24h histogram_opt w24h histogram mpg

* symbol (s1mono)
_sk_probe sy_cycle symbol s1mono scatter y1-y15 weight in 1/3
_sk_probe sy_large symbol s1mono scatter y1-y11 weight in 1/3, msize(large large large large large large large large large large large)
_sk_probe sy_smh_red symbol s1mono (scatter mpg weight in 1/3) (scatter mpg weight in 4/6, msymbol(smcircle_hollow) mfcolor(red))
_sk_probe sy_p7_red symbol s1mono (scatter mpg weight in 1/3) (scatter mpg weight in 4/6, pstyle(p7) mfcolor(red))

* sm: each small symbol and its full symbol, at the default size and large
foreach n in smcircle smcircle_hollow smdiamond smdiamond_hollow smsquare smsquare_hollow smtriangle smtriangle_hollow smplus smx smv {
    local full = substr("`n'", 3, .)
    _sk_probe sm_`n' sm s2color scatter mpg weight in 1, msymbol(`n')
    _sk_probe sm_`n'_L sm s2color scatter mpg weight in 1, msymbol(`n') msize(large)
    _sk_probe sm_`full' sm s2color scatter mpg weight in 1, msymbol(`full')
    _sk_probe sm_`full'_L sm s2color scatter mpg weight in 1, msymbol(`full') msize(large)
}

* cycle (s1mono): the second layer of each marker type
_sk_probe cy_scatteri cycle s1mono (scatter mpg weight in 1/3) (scatteri 20 3000)
_sk_probe cy_rscatter cycle s1mono (scatter mpg weight in 1/3) (rscatter lo hi weight in 1/3)
_sk_probe cy_pcscatter cycle s1mono (scatter mpg weight in 1/3) (pcscatter mpg weight price length in 1/3)
_sk_probe cy_dropline cycle s1mono (scatter mpg weight in 1/3) (dropline mpg weight in 1/3)
_sk_probe cy_rcapsym cycle s1mono (scatter mpg weight in 1/3) (rcapsym lo hi weight in 1/3)

* mark: the marker colour keys
foreach s in w24g w24m w24f {
    _sk_probe mk_`s'_1 mark `s' scatter mpg weight in 1/3
    _sk_probe mk_`s'_2 mark `s' (scatter mpg weight in 1/3) (scatter price weight in 1/3, yaxis(2))
}

* Section 33 (P1.4b): marker labels and the colour key.
capture program drop _s33_probe
program define _s33_probe
    * _s33_probe id group scheme command: as _sk_probe, with the axes and
    * plot region left on, so the colour key's place is measurable.
    gettoken id 0 : 0
    gettoken group 0 : 0
    gettoken scheme 0 : 0
    local cmd = strtrim(`"`0'"')
    global OB_SEQ = ${OB_SEQ} + 1
    local f "${OB_WORK}/p${OB_SEQ}"
    global OBF_`id' "p${OB_SEQ}"
    capture noisily twoway `cmd' scheme(`scheme') name(sk, replace)
    local rc = _rc
    global OBR_`id' = `rc'
    global OBG_`id' "`group'"
    global OBS_`id' "`scheme'"
    global OBC_`id' `"`cmd'"'
    if `rc' == 0 {
        quietly graph export "`f'.svg", replace
    }
    global OB_IDS "${OB_IDS} `id'"
    capture graph drop sk
end
foreach s in s2color s1rcolor stcolor s1mono economist sttrans s2mono stmono1 {
    _sk_probe s33_mlabel_`s' mlabel `s' scatter mpg weight in 1/3, mlabel(make)
}
foreach s in w33a w33c w33d {
    _sk_probe s33_mlabel_chain_`s' mlabel_chain `s' scatter mpg weight in 1/3, mlabel(make)
}
_sk_probe s33_mlabel_chain_w33b mlabel_chain w33b (scatter mpg weight in 1/3, mlabel(make)) (scatter price weight in 1/3, mlabel(make) yaxis(2))
_sk_probe s33_mlabel_chain_mcolor mlabel_chain s2color scatter mpg weight in 1/3, mlabel(make) mcolor(red)
_sk_probe s33_mlabel_chain_mlabsize2 mlabel_chain s2color scatter mpg weight in 1/3, mlabel(make) mlabsize(*2)
_sk_probe s33_mlabel_chain_mlabcolor mlabel_chain s2color scatter mpg weight in 1/3, mlabel(make) mlabcolor(red)
_sk_probe s33_mlabel_chain_trmlabcolor mlabel_chain sttrans scatter mpg weight in 1/3, mlabel(make) mlabcolor(red)
_sk_probe s33_mlabel_chain_trmcolor mlabel_chain sttrans scatter mpg weight in 1/3, mlabel(make) mcolor(red)
foreach c in "bar mpg weight in 1/3" "dropline mpg weight in 1/3" "rcapsym lo hi weight in 1/3" "rscatter lo hi weight in 1/3" "pcscatter mpg weight price length in 1/3" "pcarrow mpg weight price length in 1/3" "pcbarrow mpg weight price length in 1/3" "pccapsym mpg weight price length in 1/3" "connected mpg weight in 1/3" {
    gettoken t : c
    _sk_probe s33_mlabel_types_`t' mlabel_types s2color (scatter mpg weight in 1/3) (`c', mlabel(make))
}
_sk_probe s33_mlabel_types_scatteri mlabel_types s2color (scatter mpg weight in 1/3) (scatteri 20 3000 "lab")
_sk_probe s33_mlabel_types_pcarrowi mlabel_types s2color (scatter mpg weight in 1/3) (pcarrowi 20 3000 30 4000 "lab")
foreach s in s2color s1manual s1rcolor economist w33k w33t {
    _s33_probe s33_colorkey_`s' colorkey `s' scatter mpg weight, colorvar(price)
}

python:
import json, os, sys
from collections import Counter
from sfi import Macro

G = Macro.getGlobal
sys.path.insert(0, os.path.join(G("OB_REPO"), "scripts"))
import svg_layer as sl  # noqa: E402

work = G("OB_WORK")
written = [os.path.join(work, n) for n in
           ("scheme-w24g.scheme", "scheme-w24m.scheme", "scheme-w24f.scheme",
            "scheme-w24h.scheme", "git_head.txt")]
written += [os.path.join(work, "scheme-%s.scheme" % n) for n in
           ("w33a", "w33b", "w33c", "w33d", "w33k", "w33t")]
_KEYS = ("kind", "fill", "fill_opacity", "stroke", "stroke_opacity",
         "stroke_width")


def styles(els):
    """The distinct element styles, in first-drawn order, with counts."""
    c = Counter(tuple(e[k] for k in _KEYS) for e in els)
    seen, out = set(), []
    for e in els:
        key = tuple(e[k] for k in _KEYS)
        if key not in seen:
            seen.add(key)
            out.append(dict(zip(_KEYS, key), n=c[key]))
    return out


def layer(marker):
    return {"shape": sl.marker_shape(marker), "hollow": sl.hollow(marker),
            "extent": sl.stroke_extent(marker),
            "fill": next((e["fill"] for e in marker
                          if e["fill"] not in (None, "none")), None),
            "stroke": next((e["stroke"] for e in marker
                            if e["stroke"] not in (None, "none")), None)}


probes = {}
for pid in G("OB_IDS").split():
    grp = G("OBG_" + pid)
    rec = {"group": grp, "scheme": G("OBS_" + pid),
           "command": G("OBC_" + pid), "rc": int(float(G("OBR_" + pid))),
           "elements": [], "layers": []}
    svg = os.path.join(work, G("OBF_" + pid) + ".svg")
    if os.path.exists(svg):
        written.append(svg)
        els = sl.svg_elements(svg)
        rec["elements"] = styles(els)
        if grp in ("symbol", "sm", "cycle", "mark"):
            ms = [m for m in sl.markers(els) if sl.marker_shape(m)]
            if grp == "cycle":
                # The second layer's marker: the last one drawn.
                rec["layers"] = [layer(ms[0]), layer(ms[-1])] if ms else []
            elif grp == "sm":
                rec["layers"] = [layer(ms[0])] if ms else []
            else:
                per = 3
                rec["layers"] = [layer(ms[i]) for i in range(0, len(ms), per)]
    probes[pid] = rec


def ext(pid):
    ls = probes.get(pid, {}).get("layers") or []
    return ls[0]["extent"] if ls else None


sm = {}
for n in ("smcircle", "smcircle_hollow", "smdiamond", "smdiamond_hollow",
          "smsquare", "smsquare_hollow", "smtriangle", "smtriangle_hollow",
          "smplus", "smx", "smv"):
    full = n[2:]
    r = {}
    for size, suf in (("default", ""), ("large", "_L")):
        a, b = ext("sm_" + n + suf), ext("sm_" + full + suf)
        r[size] = round(a / b, 4) if a and b else None
    sm[n] = r
cyc = probes.get("sy_cycle", {}).get("layers") or []
derived = {"sm_factor": sm,
           "s1mono_hollow": [l["hollow"] for l in cyc],
           "s1mono_extent": [l["extent"] for l in cyc]}

# Section 33 (P1.4b): every text of a probe's SVG with its fill, opacity,
# size in Stata's relative units (font-size over a hundredth of the
# canvas's smaller side), rotation, anchor and x; and, for the colour key,
# the lines right of the plot region.
import re  # noqa: E402
import svg_truth as st  # noqa: E402

_S33_OPACITY = re.compile(r"(?:^|;)\s*opacity:([0-9.]{1,8})")


def _s33_texts(path):
    doc = st.svg_document(path)
    with open(path, encoding="utf-8", errors="replace") as fh:
        raw = fh.read()
    ops = []
    for m in st._RE_TEXT.finditer(raw):
        o = _S33_OPACITY.search(st._attrs(m.group(1)).get("style", ""))
        ops.append(float(o.group(1)) if o else None)
    cv = doc["canvas"] or {"w": 100.0, "h": 100.0}
    rs = min(cv["w"], cv["h"]) / 100.0
    texts = []
    for t, o in zip(doc["texts"], ops):
        texts.append({"text": t["text"], "fill": t["fill"], "opacity": o,
                      "size_rs": round(t["size"] / rs, 3)
                      if t["size"] else None,
                      "rotate": t["rotate"], "anchor": t["anchor"],
                      "x": t["x"]})
    return doc, rs, texts


def _s33_key_lines(doc, rs):
    pr = doc["plotregion"]
    if not pr:
        return []
    out = []
    for vertical, ls in ((False, doc["hlines"]), (True, doc["vlines"])):
        for l in ls:
            if min(l["x1"], l["x2"]) >= pr["right"] + 1:
                length = (abs(l["y2"] - l["y1"]) if vertical
                          else abs(l["x2"] - l["x1"]))
                out.append({"stroke": l["stroke"],
                            "width_rs": round((l["width"] or 0) / rs, 3),
                            "length_rs": round(length / rs, 3),
                            "vertical": vertical,
                            "x1": l["x1"], "x2": l["x2"]})
    return out


s33 = {"label": {}, "chain": {}, "types": {}, "key": {}}
for pid in G("OB_IDS").split():
    if not pid.startswith("s33_"):
        continue
    rec = probes[pid]
    rec.pop("elements", None)
    rec.pop("layers", None)
    svg = os.path.join(work, G("OBF_" + pid) + ".svg")
    if not os.path.exists(svg):
        continue
    doc, rs, texts = _s33_texts(svg)
    grp = rec["group"]
    if grp == "colorkey":
        pr = doc["plotregion"]
        right = pr["right"] if pr else 0.0
        texts = [t for t in texts if t["x"] is not None and t["x"] > right]
        rec["key_lines"] = _s33_key_lines(doc, rs)
    else:
        # A marker label is a make or "lab"; a number is an axis's tick
        # label and a turned text its title (the second y axis of w33b is
        # not turned off).
        texts = [t for t in texts if st.label_value(t["text"]) is None
                 and t["rotate"] is None]
    rec["texts"] = texts
    tag = pid[len("s33_" + grp + "_"):]
    if grp == "mlabel" and texts:
        t = texts[0]
        s33["label"][tag] = {"fill": t["fill"], "opacity": t["opacity"],
                             "size_rs": t["size_rs"]}
    elif grp == "mlabel_chain":
        s33["chain"][tag] = [[texts[i]["fill"], texts[i]["size_rs"],
                              texts[i]["opacity"]]
                             for i in range(0, len(texts), 3)]
    elif grp == "mlabel_types" and texts:
        s33["types"][tag] = texts[0]["fill"]
    elif grp == "colorkey":
        title = next((t for t in texts if t["rotate"] is not None), None)
        labs = [t for t in texts if t["rotate"] is None]
        ticks = [l for l in rec["key_lines"] if not l["vertical"]]
        axis = [l for l in rec["key_lines"] if l["vertical"]]
        tick = ticks[0] if ticks else None
        s33["key"][tag] = {
            "label_fill": labs[0]["fill"] if labs else None,
            "label_rs": labs[0]["size_rs"] if labs else None,
            "title_fill": title["fill"] if title else None,
            "title_rs": title["size_rs"] if title else None,
            "title_rotate": title["rotate"] if title else None,
            "tick_stroke": tick["stroke"] if tick else None,
            "tick_len_rs": tick["length_rs"] if tick else None,
            "tick_side": ("outward" if tick and labs and
                          min(tick["x1"], tick["x2"]) < labs[0]["x"]
                          else "inward") if tick else None,
            "axis_stroke": axis[0]["stroke"] if axis else None}
derived["s33"] = s33

try:
    with open(os.path.join(work, "git_head.txt"), encoding="utf-8") as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out = {"_meta": {"stata_version": G("OB_VERSION"), "born_date": G("OB_BORN"),
                 "dash_commit": commit, "extracted": G("OB_WHEN"),
                 "source": "scripts/extract_scheme_layer_truth.do"},
       "probes": probes, "derived": derived}
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
print("scheme_layer_truth: wrote %d probes" % len(probes))
end
