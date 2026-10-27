*! extract_bystyle_truth.do -- WP-31 section 44 (GAPS3 D10c): whether
*! twoway draws by(rep78, style(<s>)) exactly as by() words plus graph
*! options read from bygraphstyle-<s>.style (econ, stata7, rescale,
*! combine; s2color).  twoway only.
*!
*! Output: test/fixtures/bystyle_truth.json
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_bystyle_truth.do
*!
*! Each record: the style, the expansion's by() words and graph options,
*! the number of SVG lines that differ between the two exports (0 =
*! identical), and the (note: ...) lines each printed.

clear all
set more off
set linesize 250
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zb_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zb_bad' {
    display as error "extract_bystyle_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
capture confirm file `"`repo'/dash.ado"'
if _rc {
    display as error "extract_bystyle_truth.do: set DASH_REPO to the dash repository"
    exit 601
}
tempfile wb
local work "`wb'_zb"
capture mkdir "`work'"
quietly shell git -C "`repo'" rev-parse HEAD > "`work'/git_head.txt"
local entry_scheme "`c(scheme)'"
local stata_version = c(stata_version)
local born_date "`c(born_date)'"
local extracted "`c(current_date)'"
sysuse auto, clear
set scheme s2color
local c "(scatter mpg weight)(lfit mpg weight)"
local k 0
foreach row in ///
    "econ||subtitle(, margin(small)) plotregion(color(edkbg) margin(t=5))" ///
    "stata7|edgelabel ixaxes iyaxes imargin(small)|ylabels(#2, labsize(small)) xlabels(#2, labsize(small)) xmticks(##4, style(major_horiz_nolabel)) ymticks(##4, style(major_vert_nolabel)) subtitle(, nobox size(small) position(11)) plotregion(style(none))" ///
    "rescale|rescale individual imargin(medsmall)|subtitle(, box astextbox blstyle(foreground)) ylabels(#3) xlabels(#3)" ///
    "combine|rescale individual ixtitle iytitle imargin(medsmall)|subtitle(, nobox)" {
    local ++k
    gettoken s rest : row, parse("|")
    gettoken bar rest : rest, parse("|")
    gettoken w rest : rest, parse("|")
    if "`w'" == "|" {
        local w ""
    }
    else gettoken bar rest : rest, parse("|")
    local o `"`rest'"'
    global ZB_S_`k' "`s'"
    global ZB_W_`k' "`w'"
    global ZB_O_`k' `"`o'"'
    capture graph drop _all
    quietly log using "`work'/a`k'.log", text replace name(zb)
    capture noisily twoway `c', by(rep78, style(`s')) name(ga, replace)
    quietly log close zb
    quietly graph export "`work'/a`k'.svg", replace name(ga)
    capture graph drop _all
    quietly log using "`work'/b`k'.log", text replace name(zb)
    capture noisily twoway `c', by(rep78, `w') `o' name(gb, replace)
    quietly log close zb
    quietly graph export "`work'/b`k'.svg", replace name(gb)
}
global ZB_N `k'
set scheme `entry_scheme'
python:
import difflib, json, os, re
from sfi import Macro
work = Macro.getLocal("work")
def lines(p):
    with open(p, encoding="utf-8", errors="replace") as fh:
        return [re.sub(r"Graph - g[ab]", "G", ln) for ln in fh]
def notes(p):
    with open(p, encoding="utf-8", errors="replace") as fh:
        return [" ".join(ln.split()) for ln in fh if ln.strip().startswith("(note:")]
out = {"styles": {}}
for k in range(1, int(Macro.getGlobal("ZB_N")) + 1):
    a, b = lines(os.path.join(work, "a%d.svg" % k)), lines(os.path.join(work, "b%d.svg" % k))
    d = sum(1 for x in difflib.unified_diff(a, b, n=0) if x[:1] in "+-" and x[:3] not in ("+++", "---"))
    s = Macro.getGlobal("ZB_S_%d" % k)
    out["styles"][s] = {"by_words": Macro.getGlobal("ZB_W_%d" % k),
                        "options": Macro.getGlobal("ZB_O_%d" % k),
                        "diff_lines": d,
                        "notes_style": notes(os.path.join(work, "a%d.log" % k)),
                        "notes_expanded": notes(os.path.join(work, "b%d.log" % k))}
with open(os.path.join(work, "git_head.txt")) as fh:
    commit = fh.read().strip()
out["_meta"] = {"stata_version": Macro.getLocal("stata_version"),
                "born_date": Macro.getLocal("born_date"),
                "dash_commit": commit, "extracted": Macro.getLocal("extracted"),
                "source": "scripts/extract_bystyle_truth.do"}
dst = os.path.join(Macro.getLocal("repo"), "test", "fixtures", "bystyle_truth.json")
with open(dst, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote", dst)
end
