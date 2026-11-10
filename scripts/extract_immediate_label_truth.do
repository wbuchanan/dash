*! extract_immediate_label_truth.do -- WP-47 section 47-01 (basic:PT-1,
*! MS-7): where twoway draws the marker labels of the paired-coordinate
*! and immediate types under headlabel and under recast(), and what it
*! does with mlabel() on the immediate types.
*!
*! For each probe: twoway's rc and first error line; where it draws, every
*! <text> element of its SVG export (scripts/svg_truth.py svg_texts) with
*! its pixel position, the axis mapping of each axis (pixel -> data, from
*! svg_axis_reading's tick pairs) and each label text's position in data
*! units.
*!
*!   H01-H07  headlabel on pcscatter, pccapsym, pcarrowi (and pcarrowi
*!            recast(pcbarrow))
*!   R01-R06  pci's labels under recast() to the pc types, and plain pci
*!   S01-S08  scatteri's labels under recast() to the yxview types
*!   M01-M07  mlabel() on scatteri, pci and pcarrowi
*!
*! Output: test/fixtures/immediate_label_truth.json
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_immediate_label_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 255
set graphics off

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_il_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_il_bad' {
    display as error "extract_immediate_label_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _il_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_il_rc' | _rc {
    local _il_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_immediate_label_truth.do: `_il_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global IL_REPO "`repo'"
global IL_OUT "${IL_REPO}/test/fixtures/immediate_label_truth.json"

local work "`c(tmpdir)'dash_immlab_probe"
capture mkdir "`work'"
global IL_WORK "`work'"

quietly shell git -C "${IL_REPO}" rev-parse HEAD > "${IL_WORK}/git_head.txt"
global IL_VERSION "`c(stata_version)'"
global IL_BORN "`c(born_date)'"
global IL_WHEN "`c(current_date)' `c(current_time)'"

sysuse auto, clear

local pcl `"20 2000 30 4000 "A" 25 3000 35 4000 (9) "B""'
local sil `"20 3000 "A" 25 4000 "B""'
local n 0
foreach c in ///
    `"H01|pcscatter mpg weight trunk turn in 1/5, mlabel(make)"' ///
    `"H02|pcscatter mpg weight trunk turn in 1/5, mlabel(make) headlabel"' ///
    `"H03|pccapsym mpg weight trunk turn in 1/5, mlabel(make)"' ///
    `"H04|pccapsym mpg weight trunk turn in 1/5, mlabel(make) headlabel"' ///
    `"H05|pcarrowi `pcl',"' ///
    `"H06|pcarrowi `pcl', headlabel"' ///
    `"H07|pcarrowi `pcl', recast(pcbarrow) headlabel"' ///
    `"R01|pci `pcl', recast(pccapsym)"' ///
    `"R02|pci `pcl', recast(pcarrow)"' ///
    `"R03|pci `pcl', recast(pcbarrow)"' ///
    `"R04|pci `pcl', recast(pcscatter)"' ///
    `"R05|pci `pcl', recast(pccapsym) headlabel"' ///
    `"R06|pci `pcl',"' ///
    `"S01|scatteri `sil', recast(scatter)"' ///
    `"S02|scatteri `sil', recast(line)"' ///
    `"S03|scatteri `sil', recast(connected)"' ///
    `"S04|scatteri `sil', recast(area)"' ///
    `"S05|scatteri `sil', recast(bar)"' ///
    `"S06|scatteri `sil', recast(spike)"' ///
    `"S07|scatteri `sil', recast(dropline)"' ///
    `"S08|scatteri `sil', recast(dot)"' ///
    `"M01|scatteri 20 3000, mlabel(nosuch)"' ///
    `"M02|scatteri `sil', mlabel(nosuch)"' ///
    `"M03|pci 20 2000 30 4000, mlabel(nosuch)"' ///
    `"M04|pcarrowi 20 2000 30 4000, mlabel(nosuch)"' ///
    `"M05|scatteri 20 3000, mlabel(..)"' ///
    `"M06|scatteri 20 3000, mlabel(=)"' ///
    `"M07|scatteri 20 3000, mlabel(make)"' {
    local ++n
    mata: st_local("pid", substr(st_local("c"), 1, 3))
    mata: st_local("cmd", substr(st_local("c"), 5, .))
    global IL_ID_`n' "`pid'"
    global IL_CMD_`n' `"`macval(cmd)'"'
    capture graph drop _all
    quietly log using "${IL_WORK}/`pid'.log", replace text name(il)
    capture noisily twoway `macval(cmd)' name(il, replace)
    local rc = _rc
    quietly log close il
    global IL_RC_`n' = `rc'
    capture erase "${IL_WORK}/`pid'.svg"
    if !`rc' capture graph export "${IL_WORK}/`pid'.svg", name(il) replace as(svg)
    capture graph drop _all
}
global IL_N "`n'"

* The points the label probes draw: the five cars' coordinates.
forvalues i = 1/5 {
    global IL_MAKE_`i' = make[`i']
    global IL_P_`i' = "`=mpg[`i']' `=weight[`i']' `=trunk[`i']' `=turn[`i']'"
}

python:
import json, os, sys
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


repo, work = G("IL_REPO"), G("IL_WORK")
sys.path.insert(0, os.path.join(repo, "scripts"))
import svg_truth


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def first_error(text):
    for s in (ln.strip() for ln in text.replace("\n> ", "").splitlines()):
        if not s or s.startswith(". ") or s.startswith("(note:"):
            continue
        if s.startswith("name:") or s.startswith("log:") or s.startswith("log type:") \
                or s.startswith("opened on:") or s.startswith("closed on:") \
                or set(s) <= set("-"):
            continue
        return s
    return ""


def mapping(reading):
    """(value of pixel p) as a line through the first and last tick pair."""
    pairs = reading.get("pairs") or []
    if reading.get("fit") is None or len(pairs) < 2:
        return None
    (p0, v0), (p1, v1) = pairs[0], pairs[-1]
    if p1 == p0:
        return None
    slope = (v1 - v0) / (p1 - p0)
    return {"p0": p0, "v0": v0, "units_per_px": slope}


LABELS = {"A", "B"} | {G("IL_MAKE_%d" % i) for i in range(1, 6)}
probes = {}
for k in range(1, int(G("IL_N")) + 1):
    pid = G("IL_ID_%d" % k)
    rc = int(G("IL_RC_%d" % k))
    log = read(os.path.join(work, pid + ".log"))
    rec = {"cmd": G("IL_CMD_%d" % k), "twoway_rc": rc,
           "twoway_message": first_error(log) if rc else "",
           "texts": [], "labels": [], "x_axis": None, "y_axis": None}
    svg = os.path.join(work, pid + ".svg")
    if rc == 0 and os.path.exists(svg):
        doc = svg_truth.svg_document(svg)
        rec["texts"] = [{"text": t["text"], "x_px": t["x"], "y_px": t["y"]}
                        for t in doc["texts"]]
        mx = mapping(svg_truth.svg_axis_reading(svg, "x", doc=doc))
        my = mapping(svg_truth.svg_axis_reading(svg, "y", doc=doc))
        rec["x_axis"], rec["y_axis"] = mx, my
        for t in rec["texts"]:
            if t["text"] not in LABELS:
                continue
            lab = {"text": t["text"], "x_px": t["x_px"], "y_px": t["y_px"],
                   "x": None, "y": None}
            if mx and my and t["x_px"] is not None and t["y_px"] is not None:
                lab["x"] = mx["v0"] + mx["units_per_px"] * (t["x_px"] - mx["p0"])
                lab["y"] = my["v0"] + my["units_per_px"] * (t["y_px"] - my["p0"])
            rec["labels"].append(lab)
    probes[pid] = rec
    for f in (pid + ".log", pid + ".svg"):
        try:
            if not os.environ.get("IL_KEEP"):
                os.remove(os.path.join(work, f))
        except OSError:
            pass
points = {}
for i in range(1, 6):
    y1, x1, y2, x2 = (float(v) for v in G("IL_P_%d" % i).split())
    points[G("IL_MAKE_%d" % i)] = {"y1": y1, "x1": x1, "y2": y2, "x2": x2}
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out = {"_meta": {"stata_version": G("IL_VERSION"), "born_date": G("IL_BORN"),
                 "dash_commit": commit, "extracted": G("IL_WHEN"),
                 "source": "scripts/extract_immediate_label_truth.do"},
       "points": points}
out.update(probes)
with open(G("IL_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("IL_OUT"), len(probes), "probes")
end
