*! extract_by_text_truth.do
*! WP-30 section 28 (P1.15a): ground truth for the text twoway draws on a
*! by() graph -- each panel's label, the graph's own title() on every
*! panel, by()'s overall title(), subtitle(), note() and caption(), the
*! default "Graphs by" note -- and which panels exist when a by() value is
*! missing, for test/fixtures/by_text_truth.json.
*!
*! WHY THIS EXISTS
*!
*! dash appended the panel label to the graph's title ("T — Domestic"),
*! joined labels " / ", titled a missing panel "Missing", drew a string
*! by() value "" as its own panel, and named by()'s text sub-options as
*! ignored.  twoway gives each panel its label as the panel's subtitle(),
*! joins labels ", ", writes "(missing)", marks out "" (markout, strok)
*! and draws the overall text once (bygraph_g.class).
*!
*! Output: test/fixtures/by_text_truth.json
*!
*! Run with:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_by_text_truth.do
*!
*! METHOD
*!
*! Every probe is `bt id "if" "options"': the data are reloaded, the
*! command `twoway scatter mpg weight <if>, <options> name(Graph, replace)'
*! is run under a text log, and, when it succeeds, the `.Graph' members
*! (the overall title, subtitle, note lines, caption and note size; each
*! panel's subtitle lines, title, note and caption) and each panel's
*! observations (its serset's r(N)) are written to a record file, and the
*! graph is exported to SVG.  The trailing python: block reads files only
*! (never calls Stata; a backtick is spelled \x60) and writes the fixture,
*! the SVG texts read by scripts/svg_truth.py.
*! ---------------------------------------------------------------------------

clear all
set graphics off
set more off
set linesize 255
version 19

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_by_text_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_by_text_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1
global BT_REPO "`repo'"
global BT_OUT  "`repo'/test/fixtures/by_text_truth.json"
local scratch "`c(tmpdir)'dash_by_text_probe"
capture mkdir "`scratch'"
global BT_WORK "`scratch'"
global BT_REC  "`scratch'/by_text_records.txt"

set scheme stcolor

global BT_SVER = c(stata_version)
global BT_BORN = c(born_date)
global BT_DATE = c(current_date) + " " + c(current_time)

// Provenance stamp (D12): `shell' writes the commit into a file, read back.
tempfile btgitrev
quietly shell git -C "${BT_REPO}" rev-parse HEAD > "`btgitrev'"
tempname btgfh
file open `btgfh' using "`btgitrev'", read text
file read `btgfh' btgitline
file close `btgfh'
global BT_COMMIT = trim(`"`btgitline'"')
capture assert ustrregexm(`"${BT_COMMIT}"', "^[0-9a-f]{40}$")
if _rc {
    display as error "extract_by_text_truth.do: git rev-parse HEAD did not print a 40-character commit: ${BT_COMMIT}"
    exit 498
}

// ---------------------------------------------------------------------------
// The data: auto, with a string by() variable s (D rows 1-40, F the other
// foreign cars, "" the rest), an all-empty string e, an unlabelled numeric
// u and a copy of foreign, fb, whose variable label is blanks.
// ---------------------------------------------------------------------------
sysuse auto, clear
generate str4 s = cond(foreign, "F", "")
replace s = "D" in 1/40
generate str1 e = ""
generate double u = foreign
label variable u ""
generate double fb = foreign
label values fb origin
label variable fb "   "
keep mpg weight foreign rep78 headroom s e u fb
quietly save "${BT_WORK}/bt.dta", replace

python:
import sys
from sfi import Macro
sys.path.insert(0, Macro.getGlobal("BT_REPO"))
import dash_render
dash_render._dash_write_stata_data(
    Macro.getGlobal("BT_WORK") + "/data.json",
    "mpg weight foreign rep78 headroom s e u fb")
end

// ---------------------------------------------------------------------------
// bt id "if" "options": one probe.
// ---------------------------------------------------------------------------
capture program drop bt
program define bt
    version 19
    args id ifq opts
    use "${BT_WORK}/bt.dta", clear
    serset clear
    quietly log using "${BT_WORK}/`id'.log", text replace name(btlog)
    capture noisily twoway scatter mpg weight `ifq', `opts' name(Graph, replace)
    local rc = _rc
    quietly log close btlog
    file write btrec "R|`id'|`rc'|`ifq'|" `"`opts'"' _n
    if `rc' exit
    local np = `.Graph.graphs.arrnels'
    file write btrec "O|`id'|`np'|" `"`.Graph.title.text[1]'"' "|" ///
        `"`.Graph.subtitle.text[1]'"' "|" `"`.Graph.note.text[1]'"' "|" ///
        `"`.Graph.note.text[2]'"' "|" `"`.Graph.caption.text[1]'"' "|" ///
        `"`.Graph.note.style.size.val'"' _n
    forvalues k = 1/`np' {
        local n = .
        capture quietly serset set `=`k' - 1'
        if !_rc {
            capture quietly serset
            if !_rc local n = r(N)
        }
        file write btrec "P|`id'|`k'|" `"`.Graph.graphs[`k'].subtitle.text[1]'"' "|" ///
            `"`.Graph.graphs[`k'].subtitle.text[2]'"' "|" ///
            `"`.Graph.graphs[`k'].title.text[1]'"' "|" ///
            `"`.Graph.graphs[`k'].note.text[1]'"' "|" ///
            `"`.Graph.graphs[`k'].caption.text[1]'"' "|`n'" _n
    }
    quietly graph export "${BT_WORK}/`id'.svg", name(Graph) replace
end

file open btrec using "${BT_REC}", write text replace
bt bp01 "" "by(foreign)"
bt bp02 "" `"title("T") by(foreign)"'
bt bp03 "" `"subtitle("S") by(foreign)"'
bt bp04 "" `"subtitle("S", prefix) by(foreign)"'
bt bp05 "" `"subtitle("Extra", suffix) by(foreign)"'
bt bp06 "" `"subtitle("") by(foreign)"'
bt bp07 "" "subtitle(, ring(0) pos(1) nobexpand) by(foreign)"
bt bp08 "" "by(foreign rep78)"
bt bp09 "" "by(rep78, missing)"
bt bp10 "" "by(foreign rep78 headroom)"
bt bp11 "" `"by(foreign, title("X") subtitle("S") note("N") caption("C"))"'
bt bp12 "" `"by(foreign, note(""))"'
bt bp13 "" `"by(foreign, note("My", suffix))"'
bt bp14 "" `"by(foreign, note("My", prefix))"'
bt bp15 "" "by(foreign, note(, size(large)))"
bt bp16 "" `"by(foreign, note("", suffix))"'
bt bp17 "" `"by(foreign, ti("X") sub("S") cap("C"))"'
bt bp18 "" `"by(foreign, note("A") note("B"))"'
bt bp19 "" `"by(foreign, note("A") note(, size(large)))"'
bt bp20 "" `"by(foreign, title("X") title("Y"))"'
bt bp21 "" `"note("N") caption("C") by(foreign)"'
bt bp22 "" `"subtitle("S") by(foreign, subtitle("O"))"'
bt bp23 "" `"title("T") by(foreign, title("X"))"'
bt bp24 "" "by(foreign, total)"
bt bp25 "if foreign == 1" "by(foreign)"
bt bp26 "" "by(foreign rep78, missing)"
bt bp27 "" "by(s)"
bt bp28 "" "by(s, total)"
bt bp29 "" "by(s, missing)"
bt bp30 "" "by(s, missing total)"
bt bp31 "" "by(e, missing)"
bt bp32 "" "by(e)"
bt bp33 "" "by(u)"
bt bp34 "" "by(fb)"
bt bp35 "" `"by(foreign, TITLE("X"))"'
bt bp36 "" `"by(foreign, title("X", ring(0)))"'
bt bp37 "" "by(foreign) scheme(economist)"
bt bp38 "" `"by(foreign, title("X") note("N")) scheme(economist)"'
bt bp39 "" `"by(foreign, title("X") subtitle("S") note("N") caption("C")) scheme(s2color)"'
file close btrec

python:
import json, os, re, sys
from sfi import Macro

REPO = Macro.getGlobal("BT_REPO")
WORK = Macro.getGlobal("BT_WORK")
sys.path.insert(0, os.path.join(REPO, "scripts"))
import svg_truth

_NUM = re.compile(r"^[-+]?[0-9.,]+$")
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


probes, order = {}, []
with open(Macro.getGlobal("BT_REC"), encoding="utf-8", errors="replace") as fh:
    for line in fh:
        f = line.rstrip("\n").split("|")
        if f[0] == "R":
            pid, rc = f[1], int(f[2])
            probes[pid] = {"if": f[3], "options": "|".join(f[4:]), "rc": rc,
                           "message": message_of(pid) if rc else ""}
            order.append(pid)
        elif f[0] == "O":
            p = probes[f[1]]
            p["n"] = int(f[2])
            p["overall"] = {"title": f[3], "subtitle": f[4],
                            "note": [t for t in (f[5], f[6]) if t],
                            "caption": f[7],
                            "note_size": float(f[8]) if f[8] else None}
            p["panels"] = []
        elif f[0] == "P":
            n = f[8]
            probes[f[1]]["panels"].append({
                "sub": [t for t in (f[3], f[4]) if t], "title": f[5],
                "note": f[6], "caption": f[7],
                "n": int(n) if n not in ("", ".") else None})

for pid in order:
    p = probes[pid]
    if p["rc"]:
        continue
    svg = os.path.join(WORK, pid + ".svg")
    doc = svg_truth.svg_document(svg)
    p["svg"] = [{"text": t["text"], "x": t["x"], "y": t["y"],
                 "anchor": t["anchor"], "size": t["size"]}
                for t in doc["texts"] if t["text"]
                and not _NUM.match(t["text"])]
    p["canvas"] = (doc.get("canvas") or {}).get("width")

with open(os.path.join(WORK, "data.json"), encoding="utf-8") as fh:
    data = json.load(fh)

out = {
    "_meta": {"stata_version": Macro.getGlobal("BT_SVER"),
              "born_date": Macro.getGlobal("BT_BORN"),
              "dash_commit": Macro.getGlobal("BT_COMMIT"),
              "extracted": Macro.getGlobal("BT_DATE"),
              "scheme": "stcolor", "probes": len(order),
              "script": "scripts/extract_by_text_truth.do",
              "method": ".Graph members per probe; panel observations from "
                        "the sersets; texts from the SVG through "
                        "scripts/svg_truth.py"},
    "data": data,
    "probes": probes,
}
with open(Macro.getGlobal("BT_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1, sort_keys=True)
    fh.write("\n")
print("WROTE %s probes=%d" % (Macro.getGlobal("BT_OUT"), len(order)))
end

display as text "extract_by_text_truth.do: done"
