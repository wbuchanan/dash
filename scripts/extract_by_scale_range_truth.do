*! extract_by_scale_range_truth.do
*! WP-41 section 41-03: ground truth for three per-panel rules of a by()
*! graph -- scale() beside and inside by(), function and kdensity
*! range(varname) per panel, and a weighted marker layer with a panel whose
*! weights are all zero -- for test/fixtures/by_scale_range_truth.json.
*!
*! WHY THIS EXISTS
*!
*! dash scaled every by() panel by a scale() written beside by() (twoway
*! ignores it there) and named by(, scale()) as ignored (twoway applies
*! it, BY-2); it spanned function and kdensity range(varname) over the
*! whole data in every panel (twoway uses each panel's own rows, BY-27);
*! and it drew a weighted layer whose panel holds only zero weights
*! (twoway stops with r(198), sil:SD-7).
*!
*! Output: test/fixtures/by_scale_range_truth.json
*!
*! Run with:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_by_scale_range_truth.do
*!
*! METHOD
*!
*! Every probe is `bsr id "command"': the data are reloaded and the twoway
*! command is drawn (graphics off, never nodraw) under `capture noisily'.
*! Its rc is recorded; when it succeeds the graph is exported to SVG (S
*! probes: every text's string and font size, the first circle's r) and,
*! for the R probes, each panel's second plot's serset is loaded and the
*! minimum and maximum of its x variable recorded beside
*! `summarize weight' over the panel's rows.  The trailing python: block
*! reads files only (never calls Stata; a backtick is spelled \x60) and
*! writes the fixture through scripts/svg_truth.py.
*! ---------------------------------------------------------------------------

clear all
set graphics off
set more off
set linesize 255
version 19

* Root: DASH_REPO, else the current directory when it is a dash tree.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_by_scale_range_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_by_scale_range_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1
global BSR_REPO "`repo'"
global BSR_OUT  "`repo'/test/fixtures/by_scale_range_truth.json"
local scratch "`c(tmpdir)'dash_by_scale_range_probe"
capture mkdir "`scratch'"
global BSR_WORK "`scratch'"
global BSR_REC  "`scratch'/by_scale_range_records.txt"

set scheme stcolor

global BSR_SVER = c(stata_version)
global BSR_BORN = c(born_date)
global BSR_DATE = c(current_date) + " " + c(current_time)

// Provenance stamp: `shell' writes the commit into a file, read back.
tempfile bsrgitrev
quietly shell git -C "${BSR_REPO}" rev-parse HEAD > "`bsrgitrev'"
tempname bsrgfh
file open `bsrgfh' using "`bsrgitrev'", read text
file read `bsrgfh' bsrgitline
file close `bsrgfh'
global BSR_COMMIT = trim(`"`bsrgitline'"')
capture assert ustrregexm(`"${BSR_COMMIT}"', "^[0-9a-f]{40}$")
if _rc {
    display as error "extract_by_scale_range_truth.do: git rev-parse HEAD did not print a 40-character commit: ${BSR_COMMIT}"
    exit 498
}

// ---------------------------------------------------------------------------
// The data: auto with w = 0 for every foreign car (W01, W02, W05, W06),
// w3 = 0 when rep78 == 3 (W03, W04), wm missing for every foreign car
// (W07) and wd = 0 when rep78 is missing (W08: that panel is not drawn
// without by()'s missing).
// ---------------------------------------------------------------------------
sysuse auto, clear
generate double w = cond(foreign, 0, 1 + mod(_n, 3))
generate double w3 = cond(rep78 == 3, 0, 1 + mod(_n, 3))
generate double wm = cond(foreign, ., 1 + mod(_n, 3))
generate double wd = cond(missing(rep78), 0, 1 + mod(_n, 3))
keep mpg weight foreign rep78 w w3 wm wd
quietly save "${BSR_WORK}/bsr.dta", replace

// ---------------------------------------------------------------------------
// bsr id "command" [rangevar]: one probe.  With rangevar, each panel's
// second plot's serset x extent and the panel's summarize are recorded.
// ---------------------------------------------------------------------------
capture program drop bsr
program define bsr
    version 19
    args id cmd byvar total
    use "${BSR_WORK}/bsr.dta", clear
    serset clear
    quietly log using "${BSR_WORK}/`id'.log", text replace name(bsrlog)
    capture noisily twoway `cmd' name(Graph, replace)
    local rc = _rc
    quietly log close bsrlog
    file write bsrrec "R|`id'|`rc'|" `"`cmd'"' _n
    if `rc' exit
    quietly graph export "${BSR_WORK}/`id'.svg", name(Graph) replace
    if "`byvar'" == "" exit
    local np = `.Graph.graphs.arrnels'
    * The panels' groups in sort order (rep78's missing panel is not drawn
    * here: no probe passes missing), the Total panel last.
    quietly levelsof `byvar', local(levs)
    forvalues k = 1/`np' {
        local sid `.Graph.graphs[`k'].plotregion1.plot2.serset.id'
        local lev : word `k' of `levs'
        if "`lev'" != "" {
            quietly summarize weight if `byvar' == `lev', meanonly
        }
        else {
            quietly summarize weight if !missing(`byvar'), meanonly
        }
        local slo = r(min)
        local shi = r(max)
        preserve
        quietly serset set `sid'
        quietly serset use, clear
        * The x variable is the serset's second variable for function and
        * kdensity (y first).
        unab sv : _all
        local xv : word 2 of `sv'
        quietly summarize `xv', meanonly
        local flo = r(min)
        local fhi = r(max)
        restore
        file write bsrrec "P|`id'|`k'|`lev'|" %21.0g (`slo') "|" %21.0g (`shi') ///
            "|" %21.0g (`flo') "|" %21.0g (`fhi') _n
    }
end

file open bsrrec using "${BSR_REC}", write text replace
bsr S01 "scatter mpg weight, by(foreign)"
bsr S02 "scatter mpg weight, scale(1.5) by(foreign)"
bsr S03 "scatter mpg weight, by(foreign, scale(1.5))"
bsr S04 "scatter mpg weight, by(foreign, scale(1.5) iscale(1))"
bsr S05 `"(scatter mpg weight) (lfit mpg weight), legend(on) by(foreign, scale(1.5) title("T"))"'
bsr S06 `"(scatter mpg weight) (lfit mpg weight), legend(on) by(foreign, title("T"))"'
bsr S07 "scatter mpg weight, by(foreign, iscale(1))"
bsr R01 "(scatter mpg weight) (function y=40-x/200, range(weight)), by(foreign)" foreign
bsr R02 "(scatter mpg weight) (function y=40-x/200, range(weight)), by(rep78, total)" rep78 total
bsr R03 "(scatter mpg weight) (kdensity weight, range(weight)), by(foreign)" foreign
bsr W01 "scatter mpg weight [aw=w], by(foreign)"
bsr W02 "scatter mpg weight [aw=w], by(foreign, total)"
bsr W03 "scatter mpg weight [aw=w3], by(rep78)"
bsr W04 "scatter mpg weight [aw=w3], by(rep78, missing)"
bsr W05 "(scatter mpg weight [aw=w]) (scatter mpg weight), by(foreign)"
bsr W06 "scatter mpg weight [aw=w], by(foreign) msymbol(none)"
bsr W07 "scatter mpg weight [aw=wm], by(foreign)"
bsr W08 "scatter mpg weight [aw=wd], by(rep78)"
bsr W09 "scatter mpg weight [aw=wd], by(rep78, missing)"
file close bsrrec

python:
import json, os, re, sys
from sfi import Macro

REPO = Macro.getGlobal("BSR_REPO")
WORK = Macro.getGlobal("BSR_WORK")
sys.path.insert(0, os.path.join(REPO, "scripts"))
import svg_truth

_HEAD = re.compile(r"^\s*(name|log|log type|opened on|closed on):")


def message_of(pid):
    try:
        with open(os.path.join(WORK, pid + ".log"), encoding="utf-8",
                  errors="replace") as fh:
            lines = [l.rstrip() for l in fh]
    except OSError:
        return ""
    keep = [l for l in lines if l.strip() and not _HEAD.match(l)
            and not set(l.strip()) <= set("-")
            and not re.match(r"^r\(\d+\);$", l.strip())]
    return keep[-1].strip() if keep else ""


def num(s):
    s = s.strip()
    return None if s in ("", ".") else float(s)


probes, order = {}, []
with open(Macro.getGlobal("BSR_REC"), encoding="utf-8", errors="replace") as fh:
    for line in fh:
        f = line.rstrip("\n").split("|")
        if f[0] == "R":
            pid, rc = f[1], int(f[2])
            probes[pid] = {"command": "twoway " + "|".join(f[3:]), "rc": rc,
                           "message": message_of(pid) if rc else ""}
            order.append(pid)
        elif f[0] == "P":
            p = probes[f[1]]
            p.setdefault("panels", []).append({
                "level": f[3] if f[3] else "Total",
                "summarize": [num(f[4]), num(f[5])],
                "drawn": [num(f[6]), num(f[7])]})

for pid in order:
    p = probes[pid]
    if p["rc"] or not pid.startswith("S"):
        continue
    doc = svg_truth.svg_document(os.path.join(WORK, pid + ".svg"))
    p["texts"] = [{"text": t["text"], "size": t["size"]}
                  for t in doc["texts"] if t["text"]]
    p["marker_r"] = doc["circles"][0]["r"] if doc["circles"] else None
    p["canvas"] = (doc.get("canvas") or {}).get("w")

out = {
    "_meta": {"stata_version": Macro.getGlobal("BSR_SVER"),
              "born_date": Macro.getGlobal("BSR_BORN"),
              "source": "scripts/extract_by_scale_range_truth.do",
              "dash_commit": Macro.getGlobal("BSR_COMMIT"),
              "extracted": Macro.getGlobal("BSR_DATE"),
              "scheme": "stcolor", "probes": len(order),
              "method": "drawn twoway graphs (graphics off); S: SVG texts "
                        "and the first circle's r through "
                        "scripts/svg_truth.py; R: each panel's second "
                        "plot's serset x extent beside summarize weight "
                        "over the panel's rows; W: rc"},
    "probes": probes,
}
with open(Macro.getGlobal("BSR_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1, sort_keys=True)
    fh.write("\n")
print("WROTE %s probes=%d" % (Macro.getGlobal("BSR_OUT"), len(order)))
end

display as text "extract_by_scale_range_truth.do: done"
