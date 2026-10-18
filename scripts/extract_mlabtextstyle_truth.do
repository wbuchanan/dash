*! extract_mlabtextstyle_truth.do
*! WP-30 section 37 (P1.24, part 2): ground truth for mlabtextstyle(), for
*! test/fixtures/mlabtextstyle_truth.json.
*!
*! WHY THIS EXISTS
*!
*! dash named mlabtextstyle() in its note and drew the labels in the
*! marker-label default.  twoway draws them in the named text box style,
*! read from the scheme (style/textboxstyle-<name>.style: "set size scheme
*! <key>", "set color scheme <key>").  This script records Stata's table of
*! the 37 shipped textboxstyle files and, under stcolor, s2color, economist
*! and s1rcolor, the size and fill of each series' labels in the exported
*! SVG for every name and for the override, list and unknown-name cases.
*!
*! Output: test/fixtures/mlabtextstyle_truth.json
*!
*! Run with:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_mlabtextstyle_truth.do
*!
*! The python block reads the style files as data (a name regex and a 64 KiB
*! bound per file) and never calls back into Stata.
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
    display as error "extract_mlabtextstyle_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_mlabtextstyle_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1
global ZK_REPO "`repo'"
global ZK_OUT  "`repo'/test/fixtures/mlabtextstyle_truth.json"

local work "`c(tmpdir)'dash_mlabtextstyle_probe"
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
    display as error "extract_mlabtextstyle_truth.do: git rev-parse HEAD did not print a 40-character commit"
    exit 498
}

// ---------------------------------------------------------------------------
// The table: each shipped textboxstyle's size and colour scheme keys
// ---------------------------------------------------------------------------
global ZK_STYLEDIR "`c(sysdir_base)'style"
python:
import os, re, json
from sfi import Macro
d = Macro.getGlobal("ZK_STYLEDIR")
pat = re.compile(r"^textboxstyle-([A-Za-z0-9_#]+)\.style$")
table = {}
for f in sorted(os.listdir(d)):
    m = pat.match(f)
    if not m:
        continue
    p = os.path.join(d, f)
    if os.path.getsize(p) > 65536:
        continue
    size = color = None
    with open(p, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            t = ln.split()
            if len(t) >= 4 and t[0] == "set" and t[2] == "scheme":
                if t[1] == "size":
                    size = t[3]
                elif t[1] == "color":
                    color = t[3]
    table[m.group(1)] = [size, color]
with open(os.path.join(Macro.getGlobal("ZK_WORK"), "table.json"), "w") as fh:
    json.dump(table, fh)
Macro.setGlobal("ZK_NAMES", " ".join(n for n in sorted(table) if "#" not in n))
end

clear
set obs 3
gen double x = _n
gen double y = 2 * x
gen double y2 = y + 1
gen str2 lab = "Q" + string(_n)
gen str2 lab2 = "S" + string(_n)

global ZK_N = 0
capture program drop zk
program define zk
    global ZK_N = ${ZK_N} + 1
    global ZK_ID_${ZK_N}  `"`1'"'
    global ZK_CMD_${ZK_N} `"`2'"'
end
local S "scatter y x, mlabel(lab)"
local L "scatter y y2 x, mlabel(lab lab2)"
zk DEF "`S'"
foreach n in $ZK_NAMES p1 p3 p3barlabel p3boxlabel nosuch p0 p16 {
    zk `n' "`S' mlabtextstyle(`n')"
}
// Upper case is another name to twoway; its id differs from heading's in
// more than case, as the files are named by id.
zk UC_Heading "`S' mlabtextstyle(Heading)"
zk HV "`S' mlabtextstyle(heading) mlabsize(vsmall)"
zk VH "`S' mlabsize(vsmall) mlabtextstyle(heading)"
zk HR "`S' mlabtextstyle(heading) mlabcolor(red)"
zk RH "`S' mlabcolor(red) mlabtextstyle(heading)"
zk H2 "`S' mlabtextstyle(heading) mlabsize(*2)"
zk TW "`S' mlabtextstyle(heading) mlabtextstyle(body)"
zk QT `"`S' mlabtextstyle("heading")"'
zk L2 "`L' mlabtextstyle(heading body)"
zk L1 "`L' mlabtextstyle(heading)"
zk LD "`L' mlabtextstyle(. heading)"

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

local N = ${ZK_N}
foreach sch in stcolor s2color economist s1rcolor {
    set scheme `sch'
    forvalues i = 1/`N' {
        local id "${ZK_ID_`i'}"
        capture graph drop Graph
        capture log close mvp
        log using "${ZK_WORK}/`sch'_`id'.log", text replace name(mvp)
        capture noisily twoway ${ZK_CMD_`i'} name(Graph, replace)
        local rc = _rc
        log close mvp
        if `rc' == 0 {
            capture graph export "${ZK_WORK}/`sch'_`id'.svg", name(Graph) replace
        }
        capture graph drop Graph
        mata: _zk_put(st_global("ZK_WORK") + "/" + st_local("sch") + "_" + st_local("id") + "_rc.txt", st_local("rc"))
    }
}
tempname tfh
file open `tfh' using "${ZK_WORK}/probes.txt", write text replace
file close `tfh'
forvalues i = 1/`N' {
    mata: _zkfh = fopen(st_global("ZK_WORK") + "/probes.txt", "a"); fput(_zkfh, st_global("ZK_ID_" + st_local("i")) + char(9) + st_global("ZK_CMD_" + st_local("i"))); fclose(_zkfh)
}

// ===========================================================================
// Analysis + JSON emission.  No callbacks into Stata from here on.
// REMINDER: no backtick may appear literally in this block.
// ===========================================================================
python:
import json
import os
import re
import sys
from sfi import Macro

sys.path.insert(0, os.path.join(Macro.getGlobal("ZK_REPO"), "scripts"))
import svg_truth

W = Macro.getGlobal("ZK_WORK")


def _read(name):
    p = os.path.join(W, name)
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8") as fh:
        return fh.read().rstrip("\n")


probes = [ln.split("\t", 1) for ln in _read("probes.txt").splitlines()]
schemes = {}
for sch in ("stcolor", "s2color", "economist", "s1rcolor"):
    out = {}
    for pid, cmd in probes:
        rec = {"cmd": "twoway " + cmd,
               "rc": int(_read(sch + "_" + pid + "_rc.txt") or -1),
               "notes": [ln.strip() for ln in _read(sch + "_" + pid + ".log").splitlines()
                         if ln.strip().startswith("(note:")]}
        p = os.path.join(W, sch + "_" + pid + ".svg")
        if os.path.exists(p):
            for t in svg_truth.svg_texts(p):
                m = re.match(r"^([QS])[0-9]$", t["text"].strip())
                if m and m.group(1) not in rec:
                    rec[m.group(1)] = {"size": t["size"], "fill": (t["fill"] or "").lower()}
        out[pid] = rec
    schemes[sch] = out

with open(os.path.join(W, "table.json")) as fh:
    table = json.load(fh)
meta = {
    "stata_version": Macro.getGlobal("ZK_SVER"),
    "born_date": Macro.getGlobal("ZK_BORN"),
    "source": "scripts/extract_mlabtextstyle_truth.do",
    "dash_commit": Macro.getGlobal("ZK_COMMIT"),
    "extracted": Macro.getGlobal("ZK_DATE"),
    "table": table,
    "generator": "scripts/extract_mlabtextstyle_truth.do",
}
OUT = Macro.getGlobal("ZK_OUT")
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump({"_meta": meta, "schemes": schemes}, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote", OUT, len(table), "styles", len(probes), "probes")
end
