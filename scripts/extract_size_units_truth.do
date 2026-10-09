* extract_size_units_truth.do -- twoway's drawn marker, text and label-gap
* sizes and Stata's symbolsize/gsize ladders for WP-30 S08 (P1.12a, size
* units), written to test/fixtures/size_units_truth.json for
* test/test_size_units.py.
*
* Run (never the GUI; the slot wrapper of scripts/stata_slot.sh):
*   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_size_units_truth.do
* The tree is DASH_REPO, else the current directory when it is a dash tree.
*
* Each probe is one call of _su_probe: it runs the twoway command under
* capture noisily inside a named text log (so the "(note: ...)" lines are
* kept), records _rc and the marker class setting, and exports the graph
* as SVG under c(tmpdir).  One python block at the end reads every SVG
* through scripts/svg_truth.py's svg_document (it never calls Stata) and
* writes the fixture.  SVG: 10 units = 1 pt; 1 rs = min(viewBox w, h)/100.

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_size_units_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_size_units_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the dash repository"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1
global ZS_REPO "`repo'"

version 19
clear all
set graphics off
set more off
set linesize 255
local _su_scheme0 "`c(scheme)'"

local stata_version = c(stata_version)
local born_date "`c(born_date)'"
tempfile gh
shell git -C "${ZS_REPO}" rev-parse HEAD > "`gh'"
tempname fh
file open `fh' using "`gh'", read text
file read `fh' dash_commit
file close `fh'
local extracted "`c(current_date)'"

* ---- the probe directory (never in the repository) and its registry -------
local pdir "`c(tmpdir)'"
while strlen(`"`pdir'"') > 1 & inlist(substr(`"`pdir'"', -1, 1), "/", char(92)) {
    local pdir = substr(`"`pdir'"', 1, strlen(`"`pdir'"') - 1)
}
local pdir "`pdir'/su_probes"
capture mkdir "`pdir'"
local _sf : dir "`pdir'" files "*"
foreach f of local _sf {
    erase "`pdir'/`f'"
}
global ZS_PDIR "`pdir'"
tempname reg
file open `reg' using "`pdir'/registry.txt", write text replace
global ZS_REG "`reg'"

* ---- the ladders: Stata's own style files ----------------------------------
local ladders ""
foreach cls in symbolsize gsize {
    local files : dir "`c(sysdir_base)'style" files "`cls'-*.style"
    foreach f of local files {
        local nm = substr("`f'", strlen("`cls'") + 2, strlen("`f'") - strlen("`cls'") - 7)
        local val ""
        local szt ""
        tempname sh
        file open `sh' using "`c(sysdir_base)'style/`f'", read text
        file read `sh' line
        while r(eof) == 0 {
            local w1 : word 1 of `macval(line)'
            local w2 : word 2 of `macval(line)'
            local w3 : word 3 of `macval(line)'
            if "`w1'" == "set" & "`w2'" == "val" local val "`w3'"
            if "`w1'" == "set" & "`w2'" == "sztype" local szt "`w3'"
            file read `sh' line
        }
        file close `sh'
        local ladders "`ladders'|`cls'=`nm'=`val'=`szt'"
    }
}
global ZS_LADDERS "`ladders'"

* ---- _su_probe id scheme site "value" command ------------------------------
capture program drop _su_probe
program define _su_probe
    gettoken id 0 : 0
    gettoken scheme 0 : 0
    gettoken site 0 : 0
    gettoken value 0 : 0
    local command = strtrim(`"`macval(0)'"')
    set scheme `scheme'
    graph drop _all
    capture log close su_probe
    log using "${ZS_PDIR}/`id'.log", text replace name(su_probe)
    capture noisily `command'
    local rc = _rc
    log close su_probe
    local setting ""
    if `rc' == 0 {
        capture local setting "`.Graph.plotregion1.plot1.style.marker.size.setting'"
        graph export "${ZS_PDIR}/`id'.svg", as(svg) replace
    }
    file write ${ZS_REG} `"`id'"' _tab `"`scheme'"' _tab `"`site'"' _tab `"`macval(value)'"' _tab `"`macval(command)'"' _tab `"`rc'"' _tab `"`setting'"' _n
end

* ---- the 3-row probes -------------------------------------------------------
sysuse auto, clear
keep in 1/3
generate y2 = mpg + 5
generate x2 = weight + 300

* marker, title, mlabgap and reference: every scheme; the rest s2color only
local marker_vals `""" medium large small vtiny tiny vhuge ehuge 1.52778 4pt .1in .2cm 1.52778rs *2 *.5 0 -1 *-1 -1pt abc HUGE Large 4PT 1d3"'
local title_vals `""" medium large 12pt 5 *2 vhuge huge minuscule half_tiny tenth relative3 10-pt 5rs .25in "4 pt" "4 in" abc LARGE 4PT ehuge vtiny -1 *-1"'
local gap_vals `""" 0 5 10pt medium *2 -2 abc"'

foreach sch in s2color stcolor economist {
    local n 0
    foreach v of local marker_vals {
        local ++n
        local o ""
        if `"`v'"' != "" local o "msize(`v')"
        _su_probe `sch'_marker_`n' `sch' marker `"`v'"' twoway scatter mpg weight in 1, `o'
    }
    local n 0
    foreach v of local title_vals {
        local ++n
        local o ""
        if `"`v'"' != "" local o ", size(`v')"
        _su_probe `sch'_title_`n' `sch' title `"`v'"' twoway scatter mpg weight in 1, title("TTT"`o')
    }
    local n 0
    foreach p in 12 2 3 4 6 9 0 {
        foreach v of local gap_vals {
            local ++n
            local o ""
            if `"`v'"' != "" local o "mlabgap(`v')"
            _su_probe `sch'_mlabgap_`n' `sch' mlabgap `"`p'|`v'"' twoway scatter mpg weight in 1, mlabel(make) mlabposition(`p') `o'
        }
    }
    _su_probe `sch'_reference_1 `sch' reference `"|"' twoway scatter mpg weight in 1, title("TTT")
    _su_probe `sch'_reference_2 `sch' reference `"14pt|4pt"' twoway scatter mpg weight in 1, title("TTT", size(14pt)) msize(4pt)
}

local sch s2color
local n 0
foreach v in "" large 5 "4 pt" {
    local ++n
    local o ""
    if `"`v'"' != "" local o ", size(`v')"
    _su_probe `sch'_subtitle_`n' `sch' subtitle `"`v'"' twoway scatter mpg weight in 1, subtitle("SSS"`o')
}
local n 0
foreach v in "" large *2 "4 pt" {
    local ++n
    local o ""
    if `"`v'"' != "" local o "ytitle(, size(`v'))"
    _su_probe `sch'_ytitle_`n' `sch' ytitle `"`v'"' twoway scatter mpg weight in 1, `o'
}
local n 0
foreach v in "" 5 medium 10pt *2 vhuge abc "4 pt" {
    local ++n
    local o ""
    if `"`v'"' != "" local o "ylabel(, labsize(`v'))"
    _su_probe `sch'_labsize_`n' `sch' labsize `"`v'"' twoway scatter mpg weight in 1, `o'
}
local n 0
foreach v in "" medium large 5 10pt *2 vhuge abc Large -1 {
    local ++n
    local o ""
    if `"`v'"' != "" local o "mlabsize(`v')"
    _su_probe `sch'_mlabsize_`n' `sch' mlabsize `"`v'"' twoway scatter mpg weight in 1, mlabel(make) `o'
}
local n 0
foreach v in "" 5 large 12pt *2 abc "4 pt" {
    local ++n
    local o ""
    if `"`v'"' != "" local o "legend(size(`v'))"
    _su_probe `sch'_legend_`n' `sch' legend `"`v'"' twoway (scatter mpg weight in 1) (scatter price weight in 1, yaxis(2)), `o'
}
local n 0
foreach m in small large -1 {
    local ++n
    _su_probe `sch'_mlabgap_msize_`n' `sch' mlabgap_msize `"`m'"' twoway scatter mpg weight in 1, mlabel(make) msize(`m') mlabgap(0)
}
local n 0
foreach k in bar pcarrow pcbarrow scatteri {
    if "`k'" == "bar" local base "twoway bar mpg weight in 1, mlabel(make) barwidth(100)"
    if "`k'" == "pcarrow" local base "twoway pcarrow mpg weight y2 x2 in 1, mlabel(make)"
    if "`k'" == "pcbarrow" local base "twoway pcbarrow mpg weight y2 x2 in 1, mlabel(make)"
    if "`k'" == "scatteri" local base `"twoway scatteri 20 3000 "lab","'
    foreach w in "mlabgap(0)" "" "msize(large) mlabgap(0)" {
        local ++n
        _su_probe `sch'_origin_`n' `sch' origin `"`k'|`w'"' `base' `w'
    }
}

* ---- the 74-row colour-key probes ------------------------------------------
sysuse auto, clear
local n 0
foreach v in "" large "4 pt" {
    local ++n
    local o ""
    if `"`v'"' != "" local o "zlabel(, labsize(`v'))"
    _su_probe `sch'_zlabel_`n' `sch' zlabel `"`v'"' twoway scatter mpg weight, colorvar(price) `o'
}
local n 0
foreach v in "" large {
    local ++n
    local o ""
    if `"`v'"' != "" local o ", size(`v')"
    _su_probe `sch'_ztitle_`n' `sch' ztitle `"`v'"' twoway scatter mpg weight, colorvar(price) ztitle("ZZ"`o')
}

file close `reg'
graph drop _all
set scheme `_su_scheme0'

python:
import json, os, re, sys
from sfi import Macro
repo = Macro.getGlobal("ZS_REPO")
pdir = Macro.getGlobal("ZS_PDIR")
sys.path.insert(0, os.path.join(repo, "scripts"))
import svg_truth


def L(name):
    return Macro.getLocal(name)


def num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def notes_of(path):
    out = []
    if not os.path.exists(path):
        return out
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        lines = fh.read().splitlines()
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if s.startswith("(note:"):
            # join a wrapped note until its closing parenthesis
            while not s.endswith(")") and i + 1 < len(lines):
                i += 1
                s = s + " " + lines[i].strip()
            out.append(s)
        i += 1
    return out


def inner_circle(doc):
    cs = [c for c in doc["circles"] if c["r"] is not None and c["cx"] is not None]
    if not cs:
        return None
    return min(cs, key=lambda c: c["r"])


def data_px(doc, path, axis, value):
    """The SVG coordinate of *value* on *axis*, from the labelled ticks."""
    try:
        rd = svg_truth.svg_axis_reading(path, axis, doc=doc)
    except Exception:
        return None
    pairs = rd.get("pairs") or []
    if len(pairs) < 2:
        return None
    (p0, v0), (p1, v1) = pairs[0], pairs[-1]
    if v1 == v0:
        return None
    return p0 + (value - v0) * (p1 - p0) / (v1 - v0)


def text_of(doc, s):
    for t in doc["texts"]:
        if t["text"] == s:
            return t
    return None


def pt(t):
    return None if t is None or t["size"] is None else t["size"] / 10.0


def rnd(x, k=5):
    return None if x is None else round(x, k)


ladders = {"symbolsize": {}, "gsize": {}}
for item in Macro.getGlobal("ZS_LADDERS").split("|"):
    if not item:
        continue
    cls, nm, val, szt = item.split("=")
    v = num(val)
    ladders[cls][nm] = [v if v is not None else val, szt]

# obs 1 of sysuse auto: AMC Concord, mpg 22, weight 2930
OBS_X, OBS_Y = 2930.0, 22.0
probes = {}
schemes = []
with open(os.path.join(pdir, "registry.txt"), "r", encoding="utf-8") as fh:
    rows = [r.rstrip("\n").split("\t") for r in fh if r.strip()]
for pid, scheme, site, value, command, rc, setting in rows:
    if scheme not in schemes:
        schemes.append(scheme)
    rec = {"scheme": scheme, "site": site, "value": value,
           "command": command, "rc": int(rc),
           "notes": notes_of(os.path.join(pdir, pid + ".log")),
           "setting": None, "units_per_rs": None, "drawn_rs": None,
           "drawn_pt": None, "dx_rs": None, "dy_rs": None, "font_pt": None}
    if site in ("mlabgap",):
        p, v = value.split("|", 1)
        rec["mlabposition"] = int(p)
        rec["value"] = v
    if site == "reference":
        v, w = value.split("|", 1)
        rec["value"] = v
        rec["msize"] = w
    if site == "origin":
        k, w = value.split("|", 1)
        rec["plottype"] = k
        rec["value"] = w
    svg = os.path.join(pdir, pid + ".svg")
    if int(rc) != 0 or not os.path.exists(svg):
        probes[pid] = rec
        continue
    if site in ("marker", "reference", "mlabgap", "mlabgap_msize"):
        rec["setting"] = num(setting) if setting not in ("", ".") else setting
        if setting == ".":
            rec["setting"] = "."
    doc = svg_truth.svg_document(svg)
    cv = doc["canvas"]
    upr = min(cv["w"], cv["h"]) / 100.0
    rec["units_per_rs"] = rnd(upr)
    c = inner_circle(doc)
    if site in ("marker", "reference") and c is not None:
        # the smaller of the concentric circles; no drawn size for a
        # setting <= 0 (Stata still writes a 0.25-unit outline circle)
        rec["marker_r_units"] = c["r"]
        sv = rec["setting"]
        if not (isinstance(sv, float) and sv <= 0):
            rec["drawn_rs"] = rnd(2 * c["r"] / upr)
            rec["drawn_pt"] = rnd(2 * c["r"] / 10.0)
    if site in ("title", "reference"):
        rec["font_pt"] = pt(text_of(doc, "TTT"))
    elif site == "subtitle":
        rec["font_pt"] = pt(text_of(doc, "SSS"))
    elif site == "ytitle":
        rec["font_pt"] = pt(text_of(doc, "Mileage (mpg)"))
    elif site == "ztitle":
        rec["font_pt"] = pt(text_of(doc, "ZZ"))
    elif site == "mlabsize":
        rec["font_pt"] = pt(text_of(doc, "AMC Concord"))
    elif site == "legend":
        keys = [t for t in doc["texts"] if t["anchor"] is None
                and t["text"] in ("Mileage (mpg)", "Price")]
        rec["font_pt_keys"] = [pt(t) for t in keys]
        rec["font_pt"] = rec["font_pt_keys"][0] if keys else None
    elif site == "labsize":
        rd = svg_truth.svg_axis_reading(svg, "y", doc=doc)
        labs = [t for t in (rd.get("label_objs") or []) if t is not None]
        sizes = sorted({pt(t) for t in labs if pt(t) is not None})
        rec["font_pt_labels"] = sizes
        rec["font_pt"] = sizes[0] if len(sizes) == 1 else None
    elif site == "zlabel":
        pr = doc["plotregion"]
        right = pr["right"] if pr else 0
        labs = [t for t in doc["texts"] if t["x"] is not None
                and t["x"] > right and svg_truth.label_value(t["text"]) is not None]
        rec["zlabel_texts"] = [t["text"] for t in labs]
        sizes = sorted({pt(t) for t in labs if pt(t) is not None})
        rec["font_pt_labels"] = sizes
        rec["font_pt"] = sizes[0] if len(sizes) == 1 else None
    if site in ("mlabgap", "mlabgap_msize", "origin"):
        lab = "lab" if rec.get("plottype") == "scatteri" else "AMC Concord"
        t = text_of(doc, lab)
        ox = oy = None
        src = None
        kind = rec.get("plottype", "scatter")
        if kind == "bar":
            cands = [r for r in doc["rects"] if r["w"] and t is not None
                     and r["x"] <= t["x"] <= r["x"] + r["w"]
                     and r["fill"] not in (None, "none")]
            prw = doc["plotregion"]["right"] - doc["plotregion"]["left"]
            cands = [r for r in cands if r["w"] < prw - 1]
            if cands:
                b = min(cands, key=lambda r: r["w"])
                ox, oy, src = b["x"] + b["w"] / 2.0, b["y"], "bar top rect"
        elif kind in ("pcarrow", "pcbarrow"):
            if doc["diaglines"]:
                d0 = doc["diaglines"][0]
                ox, oy, src = d0["x1"], d0["y1"], "first diagonal line x1/y1"
        elif c is not None:
            ox, oy, src = c["cx"], c["cy"], "inner circle centre"
        if ox is None and kind == "scatter":
            ox = data_px(doc, svg, "x", OBS_X)
            oy = data_px(doc, svg, "y", OBS_Y)
            src = "axis mapping of the point (no circle drawn)"
        rec["origin_source"] = src
        if t is not None:
            rec["font_pt"] = pt(t)
            rec["anchor"] = t["anchor"]
            if ox is not None:
                rec["dx_units"] = rnd(t["x"] - ox, 3)
                rec["dx_rs"] = rnd((t["x"] - ox) / upr)
            if oy is not None:
                rec["dy_units"] = rnd(t["y"] - oy, 3)
                rec["dy_rs"] = rnd((t["y"] - oy) / upr)
    probes[pid] = rec

for f in os.listdir(pdir):
    os.remove(os.path.join(pdir, f))
os.rmdir(pdir)

out = {"_meta": {"stata_version": L("stata_version"),
                 "born_date": L("born_date"),
                 "dash_commit": L("dash_commit").strip(),
                 "extracted": L("extracted"),
                 "schemes": schemes,
                 "units": "SVG 10 units = 1 pt; rs = min(viewBox w, h)/100 units",
                 "source": "scripts/extract_size_units_truth.do"},
       "ladders": ladders, "probes": probes}
path = os.path.join(repo, "test", "fixtures", "size_units_truth.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
Macro.setGlobal("ZS_N", str(len(probes)))
end
display as text "size_units_truth: wrote ${ZS_N} probes"
