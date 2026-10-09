* extract_recast_truth.do -- twoway's own recast(), recastas() and type()
* (WP-30 P1.8b, section 45), written to test/fixtures/recast_truth.json for
* test/test_recast.py, the RC cases of test/test_twoway_option_parity.cscript
* and the S45 block of test/test_wp30_truth.cscript.
*
* Records:
*   probes[<id>]  cmd, rc, lines (the log's "(note:" and error lines) and,
*                 for rc 0, counts: the SVG's circle, path, line, rect and
*                 polygon elements, and equal_to: the base probe whose SVG
*                 equals this one's (apart from <desc>), or "".
*   classes       Stata's four type classes, read from
*                 the style files *type-*.style of c(sysdir_base).
*
* Run (never the GUI; the slot wrapper of scripts/stata_slot.sh):
*   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_recast_truth.do
* SVGs and logs go to c(tmpdir).

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_recast_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_recast_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1

clear all
set more off
version 19
set scheme stcolor

local stata_version = c(stata_version)
local born_date "`c(born_date)'"
tempfile gh
shell git -C "`repo'" rev-parse HEAD > "`gh'"
tempname fh
file open `fh' using "`gh'", read text
file read `fh' dash_commit
file close `fh'
local extracted "`c(current_date)'"
local tmp "`c(tmpdir)'"

local sysbase "`c(sysdir_base)'"

capture program drop _rc_data
program _rc_data
    clear
    quietly set obs 8
    generate double x  = _n
    generate double y  = .
    local ys  3 5 2 6 4 7 1 8
    forvalues i = 1/8 {
        quietly replace y = `: word `i' of `ys'' in `i'
    }
    generate double y2 = y + 3
    generate double t  = 9 - _n
    quietly tsset t
end

capture program drop _rc_probe
program _rc_probe
    args id cmd
    local tmp "`c(tmpdir)'"
    global RC_SEQ = $RC_SEQ + 1
    local f "rc_$RC_SEQ"
    capture log close rcp
    capture graph drop _all
    log using "`tmp'/`f'.log", text replace name(rcp)
    capture noisily `cmd'
    local rc = _rc
    log close rcp
    local svg ""
    if `rc' == 0 {
        quietly graph export "`tmp'/`f'.svg", replace
        local svg "svg"
    }
    file write $RC_RH `"`id'|`rc'|`svg'`f'|`cmd'"' _n
end

tempfile recs
tempname rh
file open `rh' using "`recs'", write text replace
global RC_RH `rh'
global RC_SEQ 0

_rc_data
* The bases each recast is compared with.
_rc_probe B-line      "twoway line y x"
_rc_probe B-scatter   "twoway scatter y x"
_rc_probe B-connected "twoway connected y x"
_rc_probe B-bar       "twoway bar y x"
_rc_probe B-rspike    "twoway rspike y y2 x"
_rc_probe B-rscatter  "twoway rscatter y y2 x"
_rc_probe B-rbar      "twoway rbar y y2 x"
_rc_probe B-pcspike   "twoway pcspike y x y2 x"
_rc_probe B-pcbarrow  "twoway pcbarrow y x y2 x"
_rc_probe B-pccapsym  "twoway pccapsym y x y2 x"
_rc_probe B-tsconn    "twoway connected y t, sort"
_rc_probe B-2line     "twoway line y y2 x"
_rc_probe B-2scatter  "twoway scatter y y2 x"
_rc_probe B-dot       "twoway dot y x"
_rc_probe B-function  "twoway function y=x, range(1 5)"
* Within a class: the target's drawing.
_rc_probe W-sc-line     "twoway scatter y x, recast(line)"
_rc_probe W-li-scatter  "twoway line y x, recast(scatter)"
_rc_probe W-sc-co       "twoway scatter y x, recast(co)"
_rc_probe W-sc-b        "twoway scatter y x, recast(b)"
_rc_probe W-sc-li       "twoway scatter y x, recast(li)"
_rc_probe W-rl-line     "twoway rline y y2 x, recast(line)"
_rc_probe W-rl-rsc      "twoway rline y y2 x, recast(rsc)"
_rc_probe W-rl-rbarm    "twoway rline y y2 x, recast(rbarm)"
_rc_probe W-pc-pcbar    "twoway pcspike y x y2 x, recast(pcbar)"
_rc_probe W-pc-pccaps   "twoway pcspike y x y2 x, recast(pccaps)"
_rc_probe W-ts-conn     "twoway tsline y, recast(connected)"
_rc_probe W-2-line      "twoway scatter y y2 x, recast(line)"
_rc_probe W-2-lineline  "twoway scatter y y2 x, recast(line line)"
_rc_probe W-dot-line    "twoway dot y x, recast(line)"
_rc_probe W-fn-scatter  "twoway function y=x, range(1 5) recast(scatter)"
* Precedence and spellings.
_rc_probe PR-1 "twoway scatter y x, recast(line) type(bar)"
_rc_probe PR-2 "twoway scatter y x, type(bar) recast(line)"
_rc_probe PR-3 "twoway scatter y x, recastas(bar) recast(line)"
_rc_probe PR-4 "twoway scatter y x, recast(line) recast(bar)"
_rc_probe PR-5 "twoway scatter y x, type(line) type(bar)"
_rc_probe PR-6 "twoway scatter y x, recasta(line)"
_rc_probe PR-7 "twoway scatter y x, ty(line)"
_rc_probe SP-l    "twoway scatter y x, recast(l)"
_rc_probe SP-LINE "twoway scatter y x, recast(LINE)"
_rc_probe SP-rsc  "twoway scatter y x, recast(rsc)"
_rc_probe SP-pcl  "twoway pcspike y x y2 x, recast(pcl)"
_rc_probe SP-ls   "twoway scatter y y2 x, recast(line scatter)"
* Fallbacks.
_rc_probe FB-line    "twoway line y x, recast(rline)"
_rc_probe FB-rline   "twoway rline y y2 x, recast(pcspike)"
_rc_probe FB-pcspike "twoway pcspike y x y2 x, recast(line)"
_rc_probe FB-func    "twoway function y=x, range(1 5) recast(rline)"
_rc_probe FB-rbogus  "twoway rline y y2 x, recast(bogus)"
* Refusals.
_rc_probe RF-rec     "twoway scatter y x, rec(line)"
foreach tt in lfitci qfitci lpolyci fpfitci {
    _rc_probe RF-`tt'-recast   "twoway `tt' y x, recast(line)"
    _rc_probe RF-`tt'-recastas "twoway `tt' y x, recastas(line)"
    _rc_probe RF-`tt'-type     "twoway `tt' y x, type(line)"
}
* Literals.
_rc_probe L-scatteri "twoway scatteri 1 1 2 2 3 1, recast(line)"
_rc_probe L-pci      "twoway pci 1 1 2 2, recast(pcarrow)"
* Derived types on auto.
sysuse auto, clear
_rc_probe D-kdensity-area   "twoway kdensity mpg, recast(area)"
_rc_probe D-kdensity-base   "twoway kdensity mpg"
_rc_probe D-lfit-scatter    "twoway lfit mpg weight, recast(scatter)"
_rc_probe D-lfit-base       "twoway lfit mpg weight"
_rc_probe D-lfit-rline      "twoway lfit mpg weight, recast(rline)"
_rc_probe D-histogram-line  "twoway histogram mpg, recast(line)"
_rc_probe D-histogram-base  "twoway histogram mpg"
_rc_probe D-histogram-rline "twoway histogram mpg, recast(rline)"
_rc_probe D-function-scatter "twoway function y=x^2, range(0 3) recast(scatter)"
file close `rh'

python:
import json, os, re, glob
from sfi import Macro
repo = Macro.getLocal("repo")
tmp = Macro.getLocal("tmp")
base = Macro.getLocal("sysbase")

def _body(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    return re.sub(r"<desc>.*?</desc>", "", text, flags=re.S)

def _counts(path):
    b = _body(path)
    return {k: len(re.findall(r"<" + k + r"[\s>/]", b))
            for k in ("circle", "path", "line", "rect", "polygon")}

def _lines(log):
    out = []
    try:
        with open(log, encoding="utf-8", errors="replace") as fh:
            rows = fh.read().splitlines()
    except OSError:
        return out
    for r in rows:
        s = r.rstrip()
        if s.startswith("(note:") or "not allowed" in s:
            out.append(s)
    return out

probes = {}
with open(Macro.getLocal("recs"), encoding="utf-8") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if not line:
            continue
        pid, rc, svg, cmd = line.split("|", 3)
        f = svg[3:] if svg.startswith("svg") else svg
        rec = {"cmd": cmd, "rc": int(rc),
               "lines": _lines(os.path.join(tmp, f + ".log"))}
        p = os.path.join(tmp, f + ".svg")
        if svg.startswith("svg") and os.path.exists(p):
            rec["counts"] = _counts(p)
            rec["_body"] = _body(p)
        probes[pid] = rec

bases = [k for k in probes if k.startswith("B-")]
for pid, rec in probes.items():
    rec["equal_to"] = ""
    if "_body" in rec and not pid.startswith("B-"):
        for b in bases:
            if probes[b].get("_body") == rec["_body"]:
                rec["equal_to"] = b
                break
for rec in probes.values():
    rec.pop("_body", None)

classes = {}
for path in sorted(glob.glob(os.path.join(base, "style", "*type-*.style"))):
    name = os.path.basename(path)[:-len(".style")]
    cls, _, member = name.partition("-")
    classes.setdefault(cls, []).append(member)
classes = {k: sorted(v) for k, v in classes.items()
           if k in ("yxtype", "y2xtype", "yxyxtype", "functiontype")}

out = {"probes": probes,
       "_meta": {"stata_version": Macro.getLocal("stata_version"),
                 "born_date": Macro.getLocal("born_date"),
                 "dash_commit": Macro.getLocal("dash_commit").strip(),
                 "extracted": Macro.getLocal("extracted"),
                 "scheme": "stcolor",
                 "classes": classes}}
path = os.path.join(repo, "test", "fixtures", "recast_truth.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote " + path)
end
