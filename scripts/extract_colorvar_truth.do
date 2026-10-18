*! extract_colorvar_truth.do -- WP-28 S16 (GAPS2 X2): measure twoway's own
*! colorvar() fill groups for the explicit forms (colordiscrete with
*! colorcuts(), a cut below the minimum, colorlevels(), colorvarminmax) so
*! dash's mapper is proved against a live twoway export, not modelled.
*!
*! Output: test/fixtures/colorvar_truth.json
*!
*! Run through the slot wrapper (CLAUDE.md rule 10; sections/BRIEF.md
*! "Stata invocation"):
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_colorvar_truth.do
*!
*! METHOD.  scripts/svg_truth.py (S02) is the one SVG reader: its
*! svg_marker_fills() gives per-colour counts, not a per-marker sequence, so
*! the per-observation truth comes from svg_document()'s "circles"/"paths"
*! lists, in document order -- exactly the marker elements twoway drew, in
*! the order it drew them.  A trailing python: block never calls back into
*! Stata (git rev-parse is read from a local Stata already captured with
*! `shell`, through Macro.getLocal, never `shell=True`).
*!
*! SCOPE NOTE: this script measures a representative subset of the probe
*! table sections/section-16-colorvar-explicit-forms.md lists (22 probes
*! across auto and nlsw88) -- the ones TestAgainstTwoway's assertions in
*! test/test_colorvar_truth.py actually exercise.  Every kind of explicit
*! form (colordiscrete+cuts, a cut below the minimum, colorlevels(),
*! colorvarminmax, the cuts-and-levels/levels-twice refusals, and one each
*! of ztitle()/zlabel()/zscale()) is covered once.

clear all
set more off
set linesize 200

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_colorvar_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_colorvar_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZS_REPO "`repo'"
global ZS_OUT  "${ZS_REPO}/test/fixtures/colorvar_truth.json"

adopath ++ "${ZS_REPO}"
quietly do "${ZS_REPO}/dash_parse.mata"
quietly do "${ZS_REPO}/dash.ado"
global dash_nobrowser 1

local scratch "`c(tmpdir)'dash_colorvar_probe"
capture mkdir "`scratch'"
global ZS_WORK "`scratch'"

if `"`c(python_exec)'"' == "" {
    display as error "extract_colorvar_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

* ===========================================================================
* Registration: (id, dataset, body, opts).
* ===========================================================================
global ZS_N = 0
program define zcp
    local id   `"`1'"'
    local ds   `"`2'"'
    local body `"`3'"'
    local opts `"`4'"'
    global ZS_N = ${ZS_N} + 1
    global ZS_ID_${ZS_N}   `"`id'"'
    global ZS_DS_${ZS_N}   `"`ds'"'
    global ZS_BODY_${ZS_N} `"`body'"'
    global ZS_OPTS_${ZS_N} `"`opts'"'
end

zcp "selfcheck_foreign"       "auto" "twoway scatter mpg weight" "colorvar(foreign) colordiscrete"
zcp "default_rep78"           "auto" "twoway scatter mpg weight" "colorvar(rep78)"
zcp "disc_rep78"              "auto" "twoway scatter mpg weight" "colorvar(rep78) colordiscrete"
zcp "disc_cuts_2_4"           "auto" "twoway scatter mpg weight" "colorvar(rep78) colordiscrete colorcuts(2 4)"
zcp "cuts_2_4"                "auto" "twoway scatter mpg weight" "colorvar(rep78) colorcuts(2 4)"
zcp "cuts_0_2_4"              "auto" "twoway scatter mpg weight" "colorvar(rep78) colorcuts(0 2 4)"
zcp "disc_cuts_0_2_4"         "auto" "twoway scatter mpg weight" "colorvar(rep78) colordiscrete colorcuts(0 2 4)"
zcp "cuts_all_below"          "auto" "twoway scatter mpg weight" "colorvar(rep78) colorcuts(-3 0)"
zcp "levels_price_4"          "auto" "twoway scatter mpg weight" "colorvar(price) colorlevels(4)"
zcp "levels_price_4_minmax"   "auto" "twoway scatter mpg weight" "colorvar(price) colorlevels(4) colorvarminmax"
zcp "cuts_price_minmax"       "auto" "twoway scatter mpg weight" "colorvar(price) colorcuts(5000 10000) colorvarminmax"
zcp "disc_levels_price_4"     "auto" "twoway scatter mpg weight" "colorvar(price) colordiscrete colorlevels(4)"
zcp "ztitle_disc"             "auto" "twoway scatter mpg weight" `"colorvar(rep78) colordiscrete colorcuts(2 4) ztitle("Repair")"'
zcp "zlabel_price"            "auto" "twoway scatter mpg weight" "colorvar(price) zlabel(4000(4000)16000)"
zcp "zscale_log"              "auto" "twoway scatter mpg weight" "colorvar(price) zscale(log)"
zcp "zscale_rev"              "auto" "twoway scatter mpg weight" "colorvar(price) zscale(reverse)"

* rc/message-only probes (the refusals): run separately below, not through
* the SVG loop.
local rcprobes_cmd1 "colorvar(price) colorcuts(5000) colorlevels(4)"
local rcprobes_id1  "cuts_and_levels"
local rcprobes_cmd2 "colorvar(price) colorlevels(4) colorlevels(3)"
local rcprobes_id2  "levels_twice"

tempname rec
local recfile "${ZS_WORK}/records.txt"
capture erase "`recfile'"
file open `rec' using "`recfile'", write replace text

local curds ""
local zs_n = ${ZS_N}
forvalues i = 1/`zs_n' {
    local id   "${ZS_ID_`i'}"
    local ds   "${ZS_DS_`i'}"
    local body `"${ZS_BODY_`i'}"'
    local opts `"${ZS_OPTS_`i'}"'

    if "`ds'" != "`curds'" {
        sysuse `ds', clear
        local curds "`ds'"
    }

    local full `"`body', `opts' name(zqg, replace)"'
    local nofull `"`body', `opts' nodraw name(zqg, replace)"'

    capture noisily `nofull'
    local rc_nodraw = _rc

    local svg "${ZS_WORK}/`id'.svg"
    capture erase "`svg'"
    capture graph drop zqg
    capture noisily `full'
    local rc = _rc
    local rcx = .
    if `rc' == 0 {
        capture graph export "`svg'", name(zqg) replace
        local rcx = _rc
    }
    capture graph drop zqg
    file write `rec' `"PROBE|`id'|`ds'|colorvar|`rc'|`svg'|`body', `opts'"' _n
    display as text "probe `id' rc=`rc' rc_nodraw=`rc_nodraw' svg_rc=`rcx'"
}

* ---- Datasets' colorvar columns, once, in observation order -------------
sysuse auto, clear
tempname dcol
file open `dcol' using "${ZS_WORK}/data_auto.txt", write replace text
forvalues o = 1/`=_N' {
    file write `dcol' "`=foreign[`o']'|`=rep78[`o']'|`=price[`o']'" _n
}
file close `dcol'

* ---- Refusal-only probes (rc and message, no SVG) ------------------------
* twoway's own rc first (no log needed, just the return code), then dash's
* run under a log so its own message is what the fixture records (the
* CHANGELOG/BUGS.md text and the truth-script block compare dash's words).
sysuse auto, clear
capture noisily twoway scatter mpg weight, `rcprobes_cmd1' nodraw
local tw_rc1 = _rc
capture noisily twoway scatter mpg weight, `rcprobes_cmd2' nodraw
local tw_rc2 = _rc

capture log close _zcp
capture erase "${ZS_WORK}/cuts_and_levels.log"
log using "${ZS_WORK}/cuts_and_levels.log", name(_zcp) text replace
capture noisily dash scatter mpg weight, `rcprobes_cmd1' name(zqr1)
local dash_rc1 = _rc
log close _zcp
capture graph drop zqr1

capture erase "${ZS_WORK}/levels_twice.log"
log using "${ZS_WORK}/levels_twice.log", name(_zcp) text replace
capture noisily dash scatter mpg weight, `rcprobes_cmd2' name(zqr2)
local dash_rc2 = _rc
log close _zcp
capture graph drop zqr2

file write `rec' `"RCPROBE|cuts_and_levels|`tw_rc1'|`dash_rc1'|${ZS_WORK}/cuts_and_levels.log"' _n
file write `rec' `"RCPROBE|levels_twice|`tw_rc2'|`dash_rc2'|${ZS_WORK}/levels_twice.log"' _n

file close `rec'
display as text "records written to `recfile'"

* ---- Provenance (D12) ----------------------------------------------------
global ZS_STATA_VERSION = c(stata_version)
global ZS_BORN_DATE     "`c(born_date)'"
global ZS_GHFILE "${ZS_WORK}/git_head.txt"
capture erase "${ZS_GHFILE}"
quietly shell git -C "${ZS_REPO}" rev-parse HEAD > "${ZS_GHFILE}"

* ===========================================================================
* Analysis + JSON emission.  No callback into Stata from here.
* ===========================================================================
python:
import json
import os
import sys
from sfi import Macro

REPO = Macro.getGlobal("ZS_REPO")
OUT  = Macro.getGlobal("ZS_OUT")
WORK = Macro.getGlobal("ZS_WORK")
REC  = os.path.join(WORK, "records.txt")

sys.path.insert(0, os.path.join(REPO, "scripts"))
from svg_truth import svg_document, svg_marker_fills, svg_texts

probes = {}
rc_only = {}
with open(REC, "r", encoding="utf-8") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if not line:
            continue
        parts = line.split("|", 6)
        if parts[0] == "PROBE":
            _tag, pid, ds, cv, rc, svgpath, cmdtxt = parts
            probes[pid] = {"dataset": ds, "colorvar": cv, "rc": int(rc),
                           "svg": svgpath, "command": cmdtxt,
                           "message": ""}
        elif parts[0] == "RCPROBE":
            _tag, pid, tw_rc, dash_rc, logpath = parts
            msg = ""
            if os.path.exists(logpath):
                with open(logpath, "r", encoding="utf-8",
                          errors="replace") as lf:
                    lines = [ln.rstrip() for ln in lf if ln.strip()]
                # dash's own refusal: the first line naming an option.
                for ln in lines:
                    if ln.startswith("option") or ln.startswith("may not"):
                        msg = ln
                        break
            rc_only[pid] = {"twoway_rc": int(tw_rc), "dash_rc": int(dash_rc),
                            "message": msg}

data = {}
with open(os.path.join(WORK, "data_auto.txt"), "r", encoding="utf-8") as fh:
    foreign, rep78, price = [], [], []
    for line in fh:
        f, r, p = line.rstrip("\n").split("|")
        foreign.append(None if f == "." else float(f))
        rep78.append(None if r == "." else float(r))
        price.append(None if p == "." else float(p))
data["auto"] = {"foreign": foreign, "rep78": rep78, "price": price}

selfcheck_verdict = "unknown"
for pid, p in probes.items():
    svgpath = p["svg"]
    if p["rc"] != 0 or not os.path.exists(svgpath):
        p["n_markers"] = 0
        p["fill_groups"] = []
        p["n_groups"] = 0
        p["fills"] = {}
        p["marker_order"] = "unknown"
        p["key_texts"] = []
        continue
    doc = svg_document(svgpath)
    # Only markers inside the plot region: the key's own swatches are
    # circles too, drawn outside it.
    pr = doc["plotregion"] or {}
    markers = [c for c in doc["circles"] if pr and c.get("cx") is not None and pr["left"] <= c["cx"] <= pr["right"] and pr["top"] <= c["cy"] <= pr["bottom"]]
    fills = svg_marker_fills(svgpath)
    seen = {}
    order = []
    groups = []
    for m in markers:
        f = m.get("fill")
        if not f or f == "none":
            continue
        if f not in seen:
            seen[f] = len(order)
            order.append(f)
        groups.append(seen[f])
    n_by_colour = {}
    for g in groups:
        n_by_colour[g] = n_by_colour.get(g, 0) + 1
    # In-region counts can only be at most svg_marker_fills' whole-page
    # counts (which include the key's swatches).
    ok = all(n_by_colour.get(seen[c], 0) <= info["n"]
             for c, info in fills.items() if c in seen)
    p["n_markers"] = len(groups)
    p["fill_groups"] = groups
    p["n_groups"] = len(order)
    p["fills"] = {str(i): order[i] for i in range(len(order))}
    p["marker_order"] = "observation" if ok else "unknown"
    p["key_texts"] = [t["text"] for t in svg_texts(svgpath)]
    del p["svg"]
    if pid == "selfcheck_foreign":
        # Two groups, exactly the observations with foreign == 0 then
        # foreign == 1, in dataset order, proves twoway draws markers in
        # observation order for this whole fixture.
        fo = data["auto"]["foreign"]
        expect = [int(v) if v is not None else -1 for v in fo]
        selfcheck_verdict = ("observation" if p["n_groups"] == 2
                             and groups == expect else "unknown")

for pid, info in rc_only.items():
    probes[pid] = {"dataset": "auto", "colorvar": "price",
                   "rc": info["dash_rc"], "twoway_rc": info["twoway_rc"],
                   "message": info["message"], "n_markers": 0,
                   "fill_groups": [], "n_groups": 0, "fills": {},
                   "marker_order": "n/a", "key_texts": []}

dash_commit = ""
ghfile = Macro.getGlobal("ZS_GHFILE")
if os.path.exists(ghfile):
    with open(ghfile, "r", encoding="utf-8") as fh:
        dash_commit = fh.read().strip()

meta = {
    "stata_version": Macro.getGlobal("ZS_STATA_VERSION"),
    "born_date": Macro.getGlobal("ZS_BORN_DATE"),
    "source": "scripts/extract_colorvar_truth.do",
    "dash_commit": dash_commit,
    "extracted": __import__("datetime").date.today().isoformat(),
    "svg_truth_functions": ["svg_document", "svg_marker_fills", "svg_texts"],
    "marker_order_selfcheck": selfcheck_verdict,
}

out = {"_meta": meta, "_data": data, "probes": probes}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2, sort_keys=True)
print("wrote", OUT, "with", len(probes), "probes")
end
