*! extract_textbox_truth.do -- WP-31 section 30 (D3, D13, D2b): measure how
*! twoway draws the textbox sub-options of title(), subtitle(), note() and
*! caption() -- position(), ring(), span, box and its colours, margin(),
*! linegap(), tstyle() -- of the edge titles t1title() .. r2title()
*! (position(), ring(), span, orientation()), and of added text: tstyle()
*! and a global named in the text.  twoway only: the output is the same
*! before and after dash changes.
*!
*! Output: test/fixtures/textbox_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_textbox_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.
*! The global probes escape their dollar signs and every command runs
*! through macval(), so the do-file's own macro expansion leaves `$u30x'
*! for twoway to read; each row records the command twoway ran.  twoway
*! expands the global itself, and a global holding `=1+1' is evaluated
*! (global_eval).

clear all
set more off
set linesize 200

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_tb_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_tb_bad' {
    display as error "extract_textbox_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _tb_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_tb_rc' | _rc {
    local _tb_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_textbox_truth.do: `_tb_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global TB_REPO "`repo'"
global TB_OUT "${TB_REPO}/test/fixtures/textbox_truth.json"


local work "`c(tmpdir)'dash_textbox_probe"
capture mkdir "`work'"
global TB_WORK "`work'"

quietly shell git -C "${TB_REPO}" rev-parse HEAD > "${TB_WORK}/git_head.txt"
global TB_VERSION "`c(stata_version)'"
global TB_BORN "`c(born_date)'"
global TB_WHEN "`c(current_date)' `c(current_time)'"

set scheme s2color
sysuse auto, clear

* The members of a graph's title box, for the record.
quietly twoway scatter mpg weight, title("T", position(3)) name(u30k, replace)
log using "${TB_WORK}/members.log", text replace name(tbm)
classutil describe .u30k.title
log close tbm

* _tb_run key cmd: run cmd, logging what it prints, and export the SVG.
capture program drop _tb_run
program define _tb_run
    args key cmd
    capture graph drop u30k
    capture log close tbr
    quietly log using "${TB_WORK}/r_`key'.log", text replace name(tbr)
    capture noisily `macval(cmd)'
    local rc = _rc
    quietly log close tbr
    global TB_R_`key' "`rc'"
    if !`rc' {
        quietly graph export "${TB_WORK}/`key'.svg", replace
    }
end

forvalues k = 0/12 {
    _tb_run pos_`k' `"twoway scatter mpg weight, title("T", position(`k')) name(u30k, replace)"'
}
foreach k in 1 3 6 9 12 {
    _tb_run ring0_`k' `"twoway scatter mpg weight, note("N", ring(0) position(`k')) name(u30k, replace)"'
}
_tb_run plain `"twoway scatter mpg weight, name(u30k, replace)"'
_tb_run span_pos0 `"twoway scatter mpg weight, title("T", position(0) span) name(u30k, replace)"'
_tb_run box `"twoway scatter mpg weight, caption("C", box bcolor(gs14) lcolor(red) lwidth(thick) margin(medium)) name(u30k, replace)"'
_tb_run note_plain `"twoway scatter mpg weight, note("N") name(u30k, replace)"'
_tb_run tstyle_heading `"twoway scatter mpg weight, note("N", tstyle(heading)) name(u30k, replace)"'
_tb_run tstyle_size `"twoway scatter mpg weight, note("N", tstyle(heading) size(small)) name(u30k, replace)"'
_tb_run tstyle_bad `"twoway scatter mpg weight, note("N", tstyle(nosuch)) name(u30k, replace)"'
_tb_run just_left `"twoway scatter mpg weight, title("T", justification(left)) name(u30k, replace)"'
_tb_run order `"twoway (scatter mpg weight) (scatter trunk weight), title("T") subtitle("S") t1title("T1") t2title("T2") note("N") caption("C") legend(position(12)) name(u30k, replace)"'
_tb_run user_ring `"twoway scatter mpg weight, title("T") subtitle("S", ring(2)) t1title("T1") t2title("T2") t2title("T2") note("N", position(12)) name(u30k, replace)"'
_tb_run linegap_0 `"twoway scatter mpg weight, note("N1" "N2") name(u30k, replace)"'
_tb_run linegap_3 `"twoway scatter mpg weight, note("N1" "N2", linegap(3)) name(u30k, replace)"'
_tb_run at_plain `"twoway scatter mpg weight, text(30 2000 "P") name(u30k, replace)"'
_tb_run at_tstyle `"twoway scatter mpg weight, text(30 2000 "P", tstyle(heading)) name(u30k, replace)"'
global u30x "hello"
global u30f "F"
_tb_run global_plain `"twoway scatter mpg weight, text(30 2000 "\$u30x") name(u30k, replace)"'
_tb_run global_dollars `"twoway scatter mpg weight, text(30 2000 "\$\$u30f\$\$") name(u30k, replace)"'
_tb_run global_braces `"twoway scatter mpg weight, text(30 2000 "\${u30x}!") name(u30k, replace)"'
mata: st_global("u30e", char(96) + "=1+1" + char(39) + "!")
_tb_run global_eval `"twoway scatter mpg weight, text(30 2000 "\$u30e") name(u30k, replace)"'
global TB_C_global_eval `"twoway scatter mpg weight, text(30 2000 "\$u30e")"'
global TB_C_global_plain `"twoway scatter mpg weight, text(30 2000 "\$u30x")"'
global TB_C_global_dollars `"twoway scatter mpg weight, text(30 2000 "\$\$u30f\$\$")"'
global TB_C_global_braces `"twoway scatter mpg weight, text(30 2000 "\${u30x}!")"'

* Edge titles (D2b): position(), ring(), span and orientation().
_tb_run e_t1_plain `"twoway scatter mpg weight, t1title("E") name(u30k, replace)"'
_tb_run e_t1_pos3 `"twoway scatter mpg weight, t1title("E", position(3)) name(u30k, replace)"'
_tb_run e_t1_pos6 `"twoway scatter mpg weight, t1title("E", position(6)) name(u30k, replace)"'
_tb_run e_l1_pos12 `"twoway scatter mpg weight, l1title("E", position(12)) name(u30k, replace)"'
_tb_run e_t1_ring0 `"twoway scatter mpg weight, t1title("E", ring(0)) name(u30k, replace)"'
_tb_run e_t1_ring8 `"twoway scatter mpg weight, title("T") t1title("E", ring(8)) name(u30k, replace)"'
_tb_run e_t1_span `"twoway scatter mpg weight, t1title("E", span) name(u30k, replace)"'
_tb_run e_l1_horiz `"twoway scatter mpg weight, l1title("E", orientation(horizontal)) name(u30k, replace)"'
_tb_run e_t1_vert `"twoway scatter mpg weight, t1title("E", orientation(vertical)) name(u30k, replace)"'

python:
import json, os, re
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


work = G("TB_WORK")
_TEXT = re.compile(r"<text\b([^>]*)>([^<]*)</text>")
_RECT = re.compile(r"<rect\b([^>]*)/?>")


def attrs(s):
    return dict(re.findall(r'([a-z-]+)="([^"]*)"', s))


def svg(key):
    """Every non-numeric text (x, y, font size, rotation, anchor) and every
    rect (x, y, width, height, style) of the SVG; ``plot`` is the plot
    region (s2color's first white rect)."""
    with open(os.path.join(work, key + ".svg"), encoding="utf-8") as fh:
        src = fh.read()
    texts = []
    for a, body in _TEXT.findall(src):
        body = body.replace("&#36;", "$").replace("&amp;", "&").strip()
        if not body or re.fullmatch(r"[-0-9.,]+", body):
            continue
        a = attrs(a)
        fs = re.search(r"font-size:([0-9.]+)px", a.get("style", ""))
        rot = re.search(r"rotate\((-?[0-9.]+)", a.get("transform", ""))
        texts.append({"text": body, "x": float(a["x"]), "y": float(a["y"]),
                      "size": float(fs.group(1)) if fs else None,
                      "rotate": float(rot.group(1)) if rot else 0.0,
                      "anchor": a.get("text-anchor", "start")})
    rects = []
    for a in _RECT.findall(src):
        a = attrs(a)
        rects.append({"x": float(a.get("x", 0)), "y": float(a.get("y", 0)),
                      "w": float(a.get("width", 0)),
                      "h": float(a.get("height", 0)),
                      "style": a.get("style", "")})
    plot = next((r for r in rects
                 if r["style"].startswith("fill:#FFFFFF")), None)
    return {"texts": texts, "rects": rects, "plot": plot}


def logged(key):
    with open(os.path.join(work, "r_" + key + ".log"), encoding="utf-8") as fh:
        lines = [ln.rstrip() for ln in fh]
    keep = [ln for ln in lines if ln.strip() and not ln.startswith(".")
            and not ln.startswith(">") and not ln.lstrip().startswith("name:")
            and not ln.lstrip().startswith("log:")
            and not ln.lstrip().startswith("log type:")
            and not ln.lstrip().startswith("opened on:")
            and not ln.lstrip().startswith("closed on:")
            and not set(ln.strip()) <= set("-")]
    # A long note wraps at the line size; join the wrapped lines.
    return " ".join(" ".join(ln.split()) for ln in keep)


def row(key):
    rc = int(G("TB_R_" + key))
    out = {"rc": rc, "note": logged(key)}
    if rc == 0:
        out.update(svg(key))
    return out


keys = ["pos_%d" % k for k in range(13)] + \
    ["ring0_%d" % k for k in (1, 3, 6, 9, 12)] + \
    ["plain", "span_pos0", "box", "note_plain", "tstyle_heading",
     "tstyle_size", "tstyle_bad", "just_left", "order", "user_ring",
     "linegap_0", "linegap_3", "at_plain", "at_tstyle", "global_plain",
     "global_dollars", "global_braces", "global_eval", "e_t1_plain", "e_t1_pos3",
     "e_t1_pos6", "e_l1_pos12", "e_t1_ring0", "e_t1_ring8", "e_t1_span",
     "e_l1_horiz", "e_t1_vert"]
out = {k: row(k) for k in keys}
for k in ("global_plain", "global_dollars", "global_braces", "global_eval"):
    out[k]["command"] = G("TB_C_" + k)
    out[k]["text"] = next((t["text"] for t in out[k]["texts"]
                           if t["text"] not in ("Mileage (mpg)",
                                                "Weight (lbs.)")), None)
with open(os.path.join(work, "members.log"), encoding="utf-8") as fh:
    members = [ln.rstrip() for ln in fh if re.match(r"^\s+\S+\s+\.\S+", ln)]
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("TB_VERSION"), "born_date": G("TB_BORN"),
                "dash_commit": commit, "extracted": G("TB_WHEN"),
                "members": members, "scheme": "s2color",
                "globals": {"u30x": "hello", "u30f": "F",
                            "u30e": G("u30e")},
                "source": "scripts/extract_textbox_truth.do"}
with open(G("TB_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote", G("TB_OUT"))
end
