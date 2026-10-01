*! extract_colorvar_qualifier_truth.do -- WP-29 S07 (P0.16): measure which
*! observations set twoway's colorvar() key -- a plot's own if, a graph's
*! if, by() panels and observations whose y or x is missing -- and twoway's
*! refusals, so dash's key is proved against a live twoway export.
*!
*! Output: test/fixtures/colorvar_qualifier_truth.json
*!
*! A command with no options of its own is registered with a trailing comma,
*! so name() can be appended to every command alike.
*!
*! Run through the slot wrapper (CLAUDE.md rule 10):
*!
*!   DASH_REPO=<tree> scripts/stata_slot.sh <scratch> \
*!     <tree>/scripts/extract_colorvar_qualifier_truth.do
*!
*! METHOD.  scripts/svg_truth.py is the one SVG reader.  Per probe this
*! records the twoway command, its rc, the observations its qualifier
*! selects (qual_obs, 1-based), the in-plot-region circle fills in document
*! order (fills), the fill counts over every circle (fill_counts, key
*! swatches included), the texts right of the plot region (key_texts), how
*! many texts equal the colour variable's label (key_title_count) and
*! summarize's r(min)/r(max) of the colour variable over the qualifier.
*! The trailing python: block never calls back into Stata, and git
*! rev-parse is read from a file `shell` wrote, never `shell=True`.

clear all
set more off
set linesize 200

global ZQ_REPO "/Users/billy/Desktop/Programs/StataPrograms/d/dash"
* DASH_REPO in the environment points the run at another tree (a worktree).
local zq_env : env DASH_REPO
if `"`zq_env'"' != "" global ZQ_REPO `"`zq_env'"'
global ZQ_OUT  "${ZQ_REPO}/test/fixtures/colorvar_qualifier_truth.json"

adopath ++ "${ZQ_REPO}"
quietly do "${ZQ_REPO}/dash_parse.mata"
quietly do "${ZQ_REPO}/dash.ado"
global dash_nobrowser 1

local scratch "`c(tmpdir)'dash_colorvar_qualifier_probe"
capture mkdir "`scratch'"
global ZQ_WORK "`scratch'"

if `"`c(python_exec)'"' == "" {
    display as error "extract_colorvar_qualifier_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

program define zq_data
    sysuse auto, clear
    quietly gen y2 = mpg if price < 15000
    quietly gen x2 = weight if price < 15000
    quietly gen lo = mpg - 2
    quietly gen dom = 1 - foreign
    label define zq_dom 0 "Foreign" 1 "Domestic", replace
    label values dom zq_dom
end

* ===========================================================================
* Registration: (id, command, qualifier the colour rows obey, colorvar).
* ===========================================================================
global ZQ_N = 0
program define zqp
    global ZQ_N = ${ZQ_N} + 1
    global ZQ_ID_${ZQ_N}   `"`1'"'
    global ZQ_CMD_${ZQ_N}  `"`2'"'
    global ZQ_QUAL_${ZQ_N} `"`3'"'
    global ZQ_CV_${ZQ_N}   `"`4'"'
end

zqp "q_if_cont"  "twoway (scatter mpg weight if foreign==1, colorvar(price)) (scatter mpg weight if foreign==0)," "foreign==1" "price"
zqp "q_cmd_if"   "twoway scatter mpg weight if foreign==1, colorvar(price)" "foreign==1" "price"
zqp "q_unqual"   "twoway scatter mpg weight, colorvar(price)" "1" "price"
zqp "q_if_disc"  "twoway (scatter mpg weight if foreign==1, colorvar(rep78) colordiscrete) (scatter mpg weight if foreign==0)," "foreign==1" "rep78"
zqp "q_if_lv3"   "twoway (scatter mpg weight if foreign==1, colorvar(price) colorlevels(3)) (scatter mpg weight if foreign==0)," "foreign==1" "price"
zqp "q_if_cuts"  "twoway (scatter mpg weight if foreign==1, colorvar(price) colorcuts(5000 10000)) (scatter mpg weight if foreign==0)," "foreign==1" "price"
zqp "by_lv4"     "twoway scatter mpg weight, colorvar(price) colorlevels(4) by(foreign)" "1" "price"
zqp "by_lv4_p0"  "twoway scatter mpg weight if foreign==0, colorvar(price) colorlevels(4)" "foreign==0" "price"
zqp "by_lv4_p1"  "twoway scatter mpg weight if foreign==1, colorvar(price) colorlevels(4)" "foreign==1" "price"
zqp "by_cont"    "twoway scatter mpg weight, colorvar(price) by(foreign)" "1" "price"
zqp "by_if_lv4"    "twoway scatter mpg weight if price<6000, colorvar(price) colorlevels(4) by(foreign)" "price<6000" "price"
zqp "by_if_lv4_p0" "twoway scatter mpg weight if price<6000 & foreign==0, colorvar(price) colorlevels(4)" "price<6000 & foreign==0" "price"
zqp "by_if_lv4_p1" "twoway scatter mpg weight if price<6000 & foreign==1, colorvar(price) colorlevels(4)" "price<6000 & foreign==1" "price"
zqp "by_total"   "twoway scatter mpg weight, colorvar(price) by(foreign, total)" "1" "price"
zqp "by_clegend_cont" "twoway scatter mpg weight, colorvar(price) by(dom, clegend(on))" "1" "price"
zqp "by_clegend_lv4"  "twoway scatter mpg weight, colorvar(price) colorlevels(4) by(dom, clegend(on))" "1" "price"
zqp "by_clegend_disc" "twoway scatter mpg weight, colorvar(rep78) colordiscrete by(dom, clegend(on))" "1" "rep78"
zqp "missing_y_lv2"       "twoway scatter y2 weight, colorvar(price) colorlevels(2)" "1" "price"
zqp "missing_x_lv2"       "twoway scatter mpg x2, colorvar(price) colorlevels(2)" "1" "price"
zqp "missing_y_connected" "twoway connected y2 weight, colorvar(price) colorlevels(2)" "1" "price"
zqp "rconnected_key" "twoway rconnected lo mpg weight, colorvar(price)" "1" "price"
zqp "all_missing"    "twoway (scatter mpg weight if missing(rep78), colorvar(rep78))," "missing(rep78)" "rep78"
zqp "empty_layer"    "twoway (scatter mpg weight if price>20000, colorvar(price)) (scatter mpg weight)," "price>20000" "price"
zqp "multi_colorvar" "twoway (scatter mpg weight, colorvar(price)) (scatter mpg weight, colorvar(rep78))," "1" "price"

tempname rec
local recfile "${ZQ_WORK}/records.txt"
capture erase "`recfile'"
file open `rec' using "`recfile'", write replace text

zq_data
local zq_n = ${ZQ_N}
forvalues i = 1/`zq_n' {
    local id   "${ZQ_ID_`i'}"
    local cmd  `"${ZQ_CMD_`i'}"'
    local qual `"${ZQ_QUAL_`i'}"'
    local cv   "${ZQ_CV_`i'}"

    * The observations the qualifier selects, 1-based.
    tempname qf
    local qfile "${ZQ_WORK}/`id'_qual.txt"
    file open `qf' using "`qfile'", write replace text
    capture drop _zq_sel
    quietly gen byte _zq_sel = (`qual')
    forvalues o = 1/`=_N' {
        if _zq_sel[`o'] file write `qf' "`o'" _n
    }
    file close `qf'
    drop _zq_sel

    quietly summarize `cv' if `qual'
    local smin = r(min)
    local smax = r(max)
    local cvlab : variable label `cv'

    local svg "${ZQ_WORK}/`id'.svg"
    local logf "${ZQ_WORK}/`id'.log"
    capture erase "`svg'"
    capture graph drop zqg
    capture log close _zq
    log using "`logf'", name(_zq) text replace
    capture noisily `cmd' name(zqg, replace)
    local rc = _rc
    log close _zq
    local rcx = .
    if `rc' == 0 {
        capture graph export "`svg'", name(zqg) replace
        local rcx = _rc
    }
    capture graph drop zqg
    file write `rec' `"PROBE|`id'|`rc'|`cv'|`cvlab'|`smin'|`smax'|`svg'|`logf'|`qfile'|`cmd'"' _n
    display as text "probe `id' rc=`rc' svg_rc=`rcx'"
}
file close `rec'

* ---- The data, in observation order (missing as .) -----------------------
zq_data
tempname dcol
file open `dcol' using "${ZQ_WORK}/data_auto.txt", write replace text
forvalues o = 1/`=_N' {
    file write `dcol' "`=mpg[`o']'|`=weight[`o']'|`=foreign[`o']'|`=price[`o']'|`=rep78[`o']'" _n
}
file close `dcol'

* ---- Provenance (D12) ----------------------------------------------------
global ZQ_STATA_VERSION = c(stata_version)
global ZQ_BORN_DATE     "`c(born_date)'"
global ZQ_GHFILE "${ZQ_WORK}/git_head.txt"
capture erase "${ZQ_GHFILE}"
quietly shell git -C "${ZQ_REPO}" rev-parse HEAD > "${ZQ_GHFILE}"

* ===========================================================================
* Analysis + JSON emission.  No callback into Stata from here.
* ===========================================================================
python:
import datetime
import json
import os
import sys
from sfi import Macro

REPO = Macro.getGlobal("ZQ_REPO")
OUT = Macro.getGlobal("ZQ_OUT")
WORK = Macro.getGlobal("ZQ_WORK")

sys.path.insert(0, os.path.join(REPO, "scripts"))
from svg_truth import svg_document, svg_texts


def _num(s):
    s = s.strip()
    return None if s in ("", ".") else float(s)


def _message(logpath, rc):
    """The first line Stata printed for the refused command: the log
    holds only that command (run under capture noisily), between the
    log's "opened on" header and its closing "name:" line."""
    if not os.path.exists(logpath):
        return ""
    with open(logpath, "r", encoding="utf-8", errors="replace") as fh:
        lines = [ln.strip() for ln in fh if ln.strip()]
    body = False
    for ln in lines:
        if ln.startswith("opened on:"):
            body = True
            continue
        if body:
            if ln.startswith("name:"):
                break
            return " ".join(ln.split())
    return ""


probes = {}
with open(os.path.join(WORK, "records.txt"), encoding="utf-8") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if not line:
            continue
        (_t, pid, rc, cv, cvlab, smin, smax, svgpath, logpath, qfile,
         cmd) = line.split("|", 10)
        rc = int(rc)
        with open(qfile, encoding="utf-8") as qh:
            qual_obs = [int(x) for x in qh.read().split()]
        p = {"command": cmd.rstrip(","), "rc": rc, "colorvar": cv,
             "message": _message(logpath, rc) if rc else "",
             "qual_obs": qual_obs, "summ_min": _num(smin),
             "summ_max": _num(smax), "fills": [], "fill_counts": {},
             "key_texts": [], "key_title_count": 0}
        if rc == 0 and os.path.exists(svgpath):
            doc = svg_document(svgpath)
            pr = doc["plotregion"] or {}
            circles = [c for c in doc["circles"]
                       if c.get("fill") and c.get("fill") != "none"]
            inside = [c for c in circles if pr and c.get("cx") is not None
                      and pr["left"] <= c["cx"] <= pr["right"]
                      and pr["top"] <= c["cy"] <= pr["bottom"]]
            p["fills"] = [c["fill"] for c in inside]
            counts = {}
            for c in circles:
                counts[c["fill"]] = counts.get(c["fill"], 0) + 1
            p["fill_counts"] = counts
            texts = svg_texts(svgpath)
            p["key_texts"] = [t["text"] for t in texts
                              if pr and t.get("x") is not None
                              and t["x"] > pr["right"]]
            p["key_title_count"] = sum(1 for t in texts
                                       if t["text"] == cvlab)
        probes[pid] = p

cols = {"mpg": [], "weight": [], "foreign": [], "price": [], "rep78": []}
with open(os.path.join(WORK, "data_auto.txt"), encoding="utf-8") as fh:
    for line in fh:
        vals = line.rstrip("\n").split("|")
        for k, v in zip(("mpg", "weight", "foreign", "price", "rep78"),
                        vals):
            cols[k].append(_num(v))


def _partition(seq):
    seen = {}
    return [seen.setdefault(v, len(seen)) for v in seq]


# Self-check 1: document order is observation order for a qualified first
# layer -- the first len(qual_obs) in-region fills of q_if_disc partition
# the qualifying cars as rep78 does (missing its own group).
why = ""
qd = probes.get("q_if_disc", {})
qo = qd.get("qual_obs", [])
fl = qd.get("fills", [])[:len(qo)]
rep = [cols["rep78"][o - 1] for o in qo]
if len(fl) != len(qo):
    why = "failed: %d fills for %d qualifying cars" % (len(fl), len(qo))
elif _partition(fl) != _partition(rep):
    why = "failed: the fills do not partition the cars as rep78 does"
qualified_order = why or "held"

# Self-check 2: by() maps each panel's own rows -- each colour's count on
# the by() graph equals the two single panels' counts less their one key
# swatch each.
why = ""
for by_id in ("by_lv4", "by_if_lv4"):
    b = probes.get(by_id, {}).get("fill_counts", {})
    p0 = probes.get(by_id + "_p0", {}).get("fill_counts", {})
    p1 = probes.get(by_id + "_p1", {}).get("fill_counts", {})
    if not b:
        why = "failed: %s drew no circle" % by_id
        break
    for col in set(b) | set(p0) | set(p1):
        want = max(p0.get(col, 0) - 1, 0) + max(p1.get(col, 0) - 1, 0)
        if b.get(col, 0) != want:
            why = "failed: %s colour %s has %d, panels give %d" % (
                by_id, col, b.get(col, 0), want)
            break
    if why:
        break
by_panel = why or "held"

dash_commit = ""
ghfile = Macro.getGlobal("ZQ_GHFILE")
if os.path.exists(ghfile):
    with open(ghfile, encoding="utf-8") as fh:
        dash_commit = fh.read().strip()

meta = {
    "stata_version": Macro.getGlobal("ZQ_STATA_VERSION"),
    "born_date": Macro.getGlobal("ZQ_BORN_DATE"),
    "dash_commit": dash_commit,
    "extracted": datetime.date.today().isoformat(),
    "script": "scripts/extract_colorvar_qualifier_truth.do",
    "qualified_order_selfcheck": qualified_order,
    "by_panel_selfcheck": by_panel,
}
out = {"_meta": meta, "_data": {"auto": cols}, "probes": probes}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
print("wrote", OUT, "with", len(probes), "probes;", qualified_order, by_panel)
end
