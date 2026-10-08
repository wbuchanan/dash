*! extract_mlabvpos_truth.do
*! WP-30 section 37 (P1.24): ground truth for mlabvposition(varname), for
*! test/fixtures/mlabvpos_truth.json.
*!
*! WHY THIS EXISTS
*!
*! dash drew every label of a layer at one clock position and named
*! mlabvposition() in its note.  twoway reads the variable row by row: a
*! whole number 0-12 is that clock, a missing value or a string variable
*! takes mlabposition() (else 3), anything else is drawn at 12 with a
*! note.  This script draws 18 labelled points under stcolor, once per
*! clock with mlabposition(k) (the references, per type) and once per
*! probe with mlabvposition(), and records the clock each label of each
*! probe sits at: the k whose reference puts the same label at the same
*! place (0.05 units) with the same text-anchor.
*!
*! Output: test/fixtures/mlabvpos_truth.json
*!
*! Run with:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_mlabvpos_truth.do
*!
*! Never calls back into Stata from the trailing python: block; a backtick
*! inside it is spelled \x60.
*! ---------------------------------------------------------------------------

clear all
set graphics off
set more off
set linesize 255

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_mlabvpos_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_mlabvpos_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1
global ZK_REPO "`repo'"
global ZK_OUT  "`repo'/test/fixtures/mlabvpos_truth.json"

local work "`c(tmpdir)'dash_mlabvpos_probe"
capture mkdir "`work'"
global ZK_WORK "`work'"
display as text "probe work dir: ${ZK_WORK}"


global ZK_SVER = c(stata_version)
global ZK_BORN = c(born_date)
global ZK_DATE = "`c(current_date)' `c(current_time)'"

// Provenance stamp (D12): shell writes the commit into a file, read back.
tempfile zkgitrev
quietly shell git -C "${ZK_REPO}" rev-parse HEAD > "`zkgitrev'"
tempname zkgfh
file open `zkgfh' using "`zkgitrev'", read text
file read `zkgfh' zkgitline
file close `zkgfh'
global ZK_COMMIT = trim(`"`zkgitline'"')
capture assert ustrregexm(`"${ZK_COMMIT}"', "^[0-9a-f]{40}$")
if _rc {
    display as error "extract_mlabvpos_truth.do: git rev-parse HEAD did not print a 40-character commit"
    exit 498
}

set scheme stcolor

// ---------------------------------------------------------------------------
// The data: 18 points on a diagonal, positions 0..12 then ., 3.5, 13, -1, .a
// ---------------------------------------------------------------------------
clear
set obs 18
gen double x = _n
gen double y = _n
gen str3 lab = "R" + string(_n)
gen double pos = _n - 1 in 1/13
replace pos = 3.5 in 15
replace pos = 13 in 16
replace pos = -1 in 17
replace pos = .a in 18
gen byte bpos = pos
gen str4 spos = string(pos)
gen double dpos = pos
format dpos %td
gen double p9 = 9
gen byte g = mod(_n, 2)
gen double y2 = y + 20
gen double x2 = x + 0.5
gen double y3 = y + 0.5
tempfile mvdata
save "`mvdata'"

// ---------------------------------------------------------------------------
// Registration: id, then the twoway command (no name(), no export)
// ---------------------------------------------------------------------------
global ZK_N = 0
capture program drop zk
program define zk
    global ZK_N = ${ZK_N} + 1
    global ZK_ID_${ZK_N}  `"`1'"'
    global ZK_CMD_${ZK_N} `"`2'"'
end

foreach t in scatter connected bar dot dropline {
    forvalues k = 0/12 {
        zk REF_`t'_`k' "`t' y x, mlabel(lab) mlabposition(`k')"
    }
}
foreach t in pcscatter pccapsym pcarrow pcbarrow {
    forvalues k = 0/12 {
        zk REF_`t'_`k' "`t' y x y3 x2, mlabel(lab) mlabposition(`k')"
    }
}
forvalues k = 0/12 {
    zk REFG_scatter_`k' "scatter y x, mlabel(lab) mlabposition(`k') mlabgap(5)"
    zk REFB_scatter_`k' "scatter y x, mlabel(lab) mlabposition(`k') by(g)"
}
zk A   "scatter y x, mlabel(lab) mlabvposition(pos)"
zk C   "scatter y x, mlabel(lab) mlabvposition(pos) mlabposition(9)"
zk G   "scatter y x, mlabel(lab) mlabvposition(pos) mlabgap(5)"
zk K3  "scatter y x, mlabel(lab) mlabvposition(bpos)"
zk E2  "scatter y x, mlabel(lab) mlabvposition(spos) mlabposition(6)"
zk DT  "scatter y x, mlabel(lab) mlabvposition(dpos)"
zk BY  "scatter y x, mlabel(lab) mlabvposition(pos) by(g)"
zk MY2 "scatter y y2 x, mlabel(lab lab) mlabvposition(p9)"
zk MY2_REF "scatter y y2 x, mlabel(lab lab) mlabposition(9 9)"
foreach t in connected bar dot dropline {
    zk T_`t' "`t' y x, mlabel(lab) mlabvposition(pos)"
}
foreach t in pcscatter pccapsym pcarrow pcbarrow {
    zk T_`t' "`t' y x y3 x2, mlabel(lab) mlabvposition(pos)"
}
zk RSQ "rscatter y y2 x, mlabel(y) mlabvposition(p9)"
zk SI  `"scatteri 1 1 "a" 2 2 "b", mlabvposition(p9)"'
zk RSQ_REF "rscatter y y2 x,"
zk SI_REF `"scatteri 1 1 "a" 2 2 "b","'

capture mata: mata drop _zk_put()
mata:
void _zk_put(string scalar file, string scalar text)
{
    real scalar fh
    if (fileexists(file)) unlink(file)
    fh = fopen(file, "w")
    fput(fh, text)
    fclose(fh)
}
end

// ---------------------------------------------------------------------------
// The probes: each in a named log, so its notes are recorded
// ---------------------------------------------------------------------------
local N = ${ZK_N}
forvalues i = 1/`N' {
    local id "${ZK_ID_`i'}"
    use "`mvdata'", clear
    capture graph drop Graph
    capture log close mvp
    log using "${ZK_WORK}/mv_`id'.log", text replace name(mvp)
    capture noisily twoway ${ZK_CMD_`i'} name(Graph, replace)
    local rc = _rc
    log close mvp
    if `rc' == 0 {
        capture graph export "${ZK_WORK}/mv_`id'.svg", name(Graph) replace
    }
    capture graph drop Graph
    mata: _zk_put(st_global("ZK_WORK") + "/mv_" + st_local("id") + "_rc.txt", st_local("rc"))
    display as text "probe `id' rc=`rc'"
}
tempname tfh
file open `tfh' using "${ZK_WORK}/probes.txt", write text replace
file close `tfh'
forvalues i = 1/`N' {
    mata: _zkfh = fopen(st_global("ZK_WORK") + "/probes.txt", "a"); fput(_zkfh, st_global("ZK_ID_" + st_local("i")) + char(9) + st_global("ZK_CMD_" + st_local("i"))); fclose(_zkfh)
}
use "`mvdata'", clear

// ===========================================================================
// Analysis + JSON emission.  No callbacks into Stata from here on.
// REMINDER: no backtick may appear literally in this block.
// ===========================================================================
python:
import json
import os
import re
import sys
from sfi import Data, Macro, Missing

ZK_REPO = Macro.getGlobal("ZK_REPO")
sys.path.insert(0, os.path.join(ZK_REPO, "scripts"))
import svg_truth

W = Macro.getGlobal("ZK_WORK")
OUT = Macro.getGlobal("ZK_OUT")
_LAB = re.compile(r"^R([0-9]+)$")


def _read(name):
    p = os.path.join(W, name)
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8") as fh:
        return fh.read().rstrip("\n")


def _labels(pid):
    """{"R<n>": [(x, y, anchor), ...]} of a probe's SVG, in document order."""
    p = os.path.join(W, "mv_" + pid + ".svg")
    out = {}
    if not os.path.exists(p):
        return out
    for t in svg_truth.svg_texts(p):
        m = _LAB.match(t["text"].strip())
        if m:
            out.setdefault(t["text"].strip(), []).append(
                (t["x"], t["y"], t["anchor"] or "start"))
    return out


def _all_texts(pid):
    p = os.path.join(W, "mv_" + pid + ".svg")
    if not os.path.exists(p):
        return None
    return sorted((t["text"], round(t["x"], 2), round(t["y"], 2),
                   t["anchor"] or "start") for t in svg_truth.svg_texts(p))


def _notes(pid):
    return [ln.strip() for ln in _read("mv_" + pid + ".log").splitlines()
            if ln.strip().startswith("(note:")]


probes = []
for ln in _read("probes.txt").splitlines():
    pid, cmd = ln.split("\t", 1)
    probes.append((pid, cmd))
refs = {pid: _labels(pid) for pid, _ in probes if pid.startswith("REF")}


def _clock(fam, lab, at):
    hits = []
    for k in range(13):
        r = refs.get(fam + "_" + str(k), {}).get(lab)
        if not r:
            continue
        rx, ry, ra = r[0]
        if ra == at[2] and abs(rx - at[0]) <= 0.05 and abs(ry - at[1]) <= 0.05:
            hits.append(k)
    return hits[0] if len(hits) == 1 else None


fams = {"A": "REF_scatter", "C": "REF_scatter", "G": "REFG_scatter",
        "K3": "REF_scatter", "E2": "REF_scatter", "DT": "REF_scatter",
        "BY": "REFB_scatter"}
for t in ("connected", "bar", "dot", "dropline", "pcscatter", "pccapsym",
          "pcarrow", "pcbarrow"):
    fams["T_" + t] = "REF_" + t

rec = {}
cmds = dict(probes)
for pid, cmd in probes:
    if pid.startswith("REF") or pid.endswith("_REF"):
        continue
    r = {"cmd": "twoway " + cmd, "rc": int(_read("mv_" + pid + "_rc.txt") or -1),
         "notes": _notes(pid)}
    labs = _labels(pid)
    if pid in fams:
        fam = fams[pid]
        anchor, dx, dy, clock = {}, {}, {}, {}
        for lab, ats in sorted(labs.items(), key=lambda kv: int(kv[0][1:])):
            at = ats[0]
            z = refs.get(fam + "_0", {}).get(lab)
            anchor[lab] = at[2]
            dx[lab] = round(at[0] - z[0][0], 3) if z else None
            dy[lab] = round(at[1] - z[0][1], 3) if z else None
            clock[lab] = _clock(fam, lab, at)
        r.update(anchor=anchor, dx=dx, dy=dy, clock=clock, ref=fam)
    elif pid == "RSQ":
        # The labels are the texts the unlabelled twin does not draw (the
        # y values beside the points; twoway refuses mlabposition() there).
        base = list(_all_texts("RSQ_REF") or [])
        extra = []
        for t in (_all_texts("RSQ") or []):
            if t in base:
                base.remove(t)
            else:
                extra.append(t)
        r["labels"] = len(extra)
        r["anchors"] = sorted({t[3] for t in extra})
    elif pid in ("MY2", "SI"):
        r["equal_to_ref"] = (_all_texts(pid) is not None
                             and _all_texts(pid) == _all_texts(pid + "_REF"))
        if pid == "MY2":
            r["anchors"] = sorted({a[2] for v in labs.values() for a in v})
    rec[pid] = r

rows = []
names = ["x", "y", "lab", "pos", "bpos", "spos", "dpos", "p9", "g", "y2", "x2", "y3"]
for i in range(Data.getObsTotal()):
    row = {}
    for n in names:
        v = Data.get(n, i)[0][0] if Data.isVarTypeStr(Data.getVarIndex(n)) else Data.get(n, i, missingval=None)[0][0]
        row[n] = v
    rows.append(row)

meta = {
    "stata_version": Macro.getGlobal("ZK_SVER"),
    "born_date": Macro.getGlobal("ZK_BORN"),
    "dash_commit": Macro.getGlobal("ZK_COMMIT"),
    "extracted": Macro.getGlobal("ZK_DATE"),
    "scheme": "stcolor",
    "probes": len(rec),
    "references": len(refs),
    "data": rows,
    "generator": "scripts/extract_mlabvpos_truth.do",
}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump({"_meta": meta, "probes": rec}, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote", OUT, len(rec), "probes", len(refs), "references")
end
