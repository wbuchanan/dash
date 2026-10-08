* extract_connect_truth.do -- twoway's own connect() and cmissing() (WP-30
* P1.8a, section 40), written to test/fixtures/connect_truth.json for
* test/test_connect_options.py and the CM cases of the cscripts.
*
* Records:
*   probes[<id>]  cmd, rc, lines (the log's "(note:" and error lines), and
*                 for the P and F probes paths: every <path d> of the SVG
*                 split at M into subpaths of [x, y] in data units (1e-6);
*                 for the S probes equal_to: the canonical probe whose SVG
*                 the spelling's SVG equals (apart from <desc>), or "".
*   matrix[<type>][<option>]  rc, lines, same_as_base for the forty types.
*
* Run (never the GUI; the slot wrapper of scripts/stata_slot.sh):
*   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_connect_truth.do
* SVGs and logs go to c(tmpdir).

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_connect_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_connect_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
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

capture program drop _cm_dataT
program _cm_dataT
    clear
    quietly set obs 8
    generate double x  = .
    generate double y  = .
    generate double y2 = .
    local xs  2 5 3 6 1 . 7 4
    local ys  10 20 . 40 50 45 60 70
    local y2s 12 22 32 42 . 47 62 72
    forvalues i = 1/8 {
        quietly replace x  = `: word `i' of `xs''  in `i'
        quietly replace y  = `: word `i' of `ys''  in `i'
        quietly replace y2 = `: word `i' of `y2s'' in `i'
    }
    generate double y3 = y + 1
    generate double t  = _n
    quietly tsset t
end

capture program drop _cm_dataTIE
program _cm_dataTIE
    clear
    quietly set obs 7
    generate double x = .
    local xs 1 3 3 2 4 5 6
    forvalues i = 1/7 {
        quietly replace x = `: word `i' of `xs'' in `i'
    }
    generate double y = 10 * _n
end

capture program drop _cm_dataA
program _cm_dataA
    sysuse auto, clear
    quietly replace mpg = . in 5
    generate lo = mpg - 2
    generate hi = mpg + 2
    generate t  = _n
    quietly tsset t
end

* One probe: the command under a named log; svg "" draws nothing.
capture program drop _cm_probe
program _cm_probe
    args kind id cmd svg
    local tmp "`c(tmpdir)'"
    // Files are named by a running number: the probe ids differ by case
    // alone (c(L), c(l)), which a case-insensitive file system merges.
    global CM_SEQ = $CM_SEQ + 1
    local f "cm_$CM_SEQ"
    capture log close cmp
    capture graph drop _all
    log using "`tmp'/`f'.log", text replace name(cmp)
    capture noisily `cmd'
    local rc = _rc
    log close cmp
    if `"`svg'"' != "" & `rc' == 0 {
        quietly graph export "`tmp'/`f'.svg", replace
    }
    else local svg ""
    file write $CM_RH `"`kind'|`id'|`rc'|`svg'`f'|`cmd'"' _n
end

tempfile recs
tempname rh
file open `rh' using "`recs'", write text replace
global CM_RH `rh'
global CM_SEQ 0

* ---- P: paths on data T --------------------------------------------------
_cm_dataT
local P01 "twoway scatter y x, c(l)"
local P02 "twoway line y x, c(J)"
local P03 "twoway line y x, c(stepstair) sort"
local P04 "twoway line y x, c(L)"
local P06 "twoway line y x, c(i) legend(on)"
local P07 "twoway scatter y x, c(bogus)"
local P08 "twoway line y x, cmissing(n)"
local P09 "twoway scatter y x, c(l) cmissing(n)"
local P10 "twoway scatter y x, c(l) cmissing(n) sort"
local P11 "twoway line y x if _n != 5, cmissing(n)"
local P12 "twoway line y y2 x, cmissing(n)"
local P13 "twoway line y y2 x, cmissing(n ..)"
local P14 "twoway rline y y2 x, cmissing(n)"
local P15 "twoway rconnected y y2 x, cmissing(n)"
local P16 "twoway line y x, cmissing(n) c(J)"
local P17 "twoway line y x, cmissing(n) c(L)"
local P20 "twoway scatter y y2 x, c(l)"
local P21 "twoway scatter y y2 x, c(. l)"
local P22 "twoway scatter y y2 y3 x, c(l ..)"
local P23 "twoway scatter y y2 y3 x, c(J =)"
local P24 "twoway scatter y y2 y3 x, c(l . J)"
local P25 "twoway line y x, c(l) c(J)"
local P26 "twoway scatter y x, c(l) sort"
local P27 "twoway scatter y y2 x, c(l) sort(y2)"
local P28 "twoway scatter y x, c(l) clcolor(red)"
local P29 "twoway tsline y, c(J)"
local P29b "twoway tsrline y y2, cmissing(n)"
local P30 "twoway scatteri 1 2 3 4 2 6, c(J)"
foreach p in P01 P02 P03 P04 P06 P07 P08 P09 P10 P11 P12 P13 P14 P15 P16 P17 P20 P21 P22 P23 P24 P25 P26 P27 P28 P29 P29b P30 {
    _cm_probe P `p' `"``p''"' svg
}
_cm_dataTIE
_cm_probe P P05 "twoway line y x, c(L)" svg
clear
_cm_probe P P18 "twoway function y=sqrt(x^2-1), range(-2 2)" svg
_cm_probe P P19 "twoway function y=sqrt(x^2-1), range(-2 2) cmissing(n)" svg

* ---- F: fits on data A -----------------------------------------------------
_cm_dataA
foreach f in lfit qfit lowess lpoly fpfit mspline mband kdensity function lfitci qfitci lpolyci fpfitci {
    local v "mpg weight"
    if "`f'" == "kdensity" local v "mpg"
    if "`f'" == "function" local v "y=x^2, range(0 4)"
    local sep ","
    if "`f'" == "function" local sep ""
    foreach s in J stepstair i {
        _cm_probe F F-`f'-`s' `"twoway `f' `v'`sep' c(`s')"' svg
    }
    _cm_probe F F-`f'-base `"twoway `f' `v'"' svg
}

* ---- S: spellings on data T ------------------------------------------------
_cm_dataT
foreach c in direct ascending stairstep stepstair none {
    _cm_probe S S-c-`c' "twoway line y x, c(`c')" svg
}
foreach c in l line d direct c connected dir L a asc asce ascending J s stair stairs stairstep u upstairstep step stepstair n none i Direct j {
    _cm_probe S S-c-`c' "twoway line y x, c(`c')" svg
}
foreach m in y yes on t tr tru true n no off f fa fal fals false ye N x {
    _cm_probe S S-m-`m' "twoway line y x, cmissing(`m')" svg
}

* ---- R: refusals -----------------------------------------------------------
_cm_probe R R-01 "twoway line y x, c(l .. J)" ""
_cm_probe R R-01s "twoway scatter y x, c(l .. J)" ""
_cm_probe R R-02 "twoway line y y2 x, cmissing(n .. y)" ""
_cm_probe R R-03 "twoway line y y2 x, cmissing(n x)" svg
_cm_probe R R_EXTRA "twoway line y x, cmissing(n x)" svg
_cm_probe R R-04 "twoway line y x, cm(n)" ""
_cm_probe R R-05 "twoway line y x, cmiss(n)" svg
_cm_probe R R-06 "twoway line y x, cmissings(n)" svg
_cm_probe R R-07 "twoway scatter y x, c(i) clwidth(-1)" svg
_cm_probe R R-08 "twoway scatter y x, c(l) clwidth(-1)" svg
_cm_probe R C_BOGUS2 "twoway scatter y y2 x, c(bogus bogus)" svg
_cm_probe R R-09 "twoway line y x, cmissing(n) cmissing(y)" svg
_cm_probe R R-10 "twoway line y x, cmissing(N)" svg
_cm_probe R R-11 "twoway line y x, cmissing(x)" svg
_cm_probe R R-12 "twoway lfit y x, cmissing(x)" svg

* ---- M: the forty types ----------------------------------------------------
_cm_dataA
local types "line connected lfit qfit fpfit lpoly lowess mspline mband kdensity function tsline lfitci qfitci lpolyci fpfitci scatter area bar spike dot dropline histogram rarea rbar rspike rcap rcapsym rline rconnected rscatter tsrline pcspike pcarrow pcbarrow pcscatter pccapsym scatteri pci"
foreach tt of local types {
    local v_`tt' "mpg weight"
}
foreach tt in rarea rbar rspike rcap rcapsym rline rconnected rscatter {
    local v_`tt' "lo hi weight"
}
foreach tt in pcspike pcarrow pcbarrow pcscatter pccapsym {
    local v_`tt' "mpg weight turn length"
}
local v_histogram "mpg"
local v_kdensity  "mpg"
local v_tsline    "mpg"
local v_tsrline   "lo hi"
local v_function  "y=x, range(0 1)"
local v_scatteri  "20 3000 30 4000"
local v_pci       "20 3000 30 4000"
local mk = 0
foreach tt of local types {
    local v `v_`tt''
    local sep ","
    if strpos("`v'", ",") local sep ""
    local ++mk
    _cm_probe M "M`mk'-base" `"twoway `tt' `v'"' svg
    local mo = 0
    foreach o in "c(J)" "c(L)" "c(i)" "c(bogus)" "cmissing(n)" "cmissing(x)" {
        local ++mo
        _cm_probe M "M`mk'-`mo'" `"twoway `tt' `v'`sep' `o'"' svg
        file write `rh' `"Mkey|M`mk'-`mo'|`tt'|`o'|M`mk'-base"' _n
    }
}
file close `rh'

python:
import json, os, re, sys
from sfi import Macro
repo = Macro.getLocal("repo")
tmp = Macro.getLocal("tmp")
sys.path.insert(0, os.path.join(repo, "scripts"))
import svg_truth

def _fit(path, axis):
    pairs = svg_truth.svg_axis_reading(path, axis).get("pairs") or []
    if len(pairs) < 2:
        return None
    n = float(len(pairs))
    mx = sum(p for p, _ in pairs) / n
    mv = sum(v for _, v in pairs) / n
    b = (sum((p - mx) * (v - mv) for p, v in pairs)
         / sum((p - mx) ** 2 for p, _ in pairs))
    return (mv - b * mx, b)

def _paths(path):
    fx = _fit(path, "x")
    fy = _fit(path, "y")
    if fx is None or fy is None:
        return None
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    out = []
    for el in re.findall(r"<path[^>]*>", text):
        m = re.search(r'\sd="([^"]*)"', el)
        if not m:
            continue
        d = m.group(1)
        # A filled path (a marker symbol, an area, a band) is recorded with
        # its fill so a reader can tell lines from shapes.
        fill = re.search(r'fill="([^"]*)"', el)
        style = re.search(r'style="([^"]*)"', el)
        filled = bool(fill and fill.group(1) not in ("none",)) or bool(
            style and "fill:" in style.group(1) and "fill:none" not in style.group(1).replace(" ", ""))
        stroke = re.search(r'stroke="([^"]*)"', el) or re.search(
            r"stroke:\s*([^;\"]*)", el)
        for sub in re.split(r"(?=M)", d):
            nums = re.findall(r"[ML]\s*(-?[0-9.]+)\s+(-?[0-9.]+)", sub)
            if not nums:
                continue
            pts = [[round(fx[0] + fx[1] * float(a), 6),
                     round(fy[0] + fy[1] * float(b), 6)] for a, b in nums]
            out.append({"pts": pts, "filled": filled, "closed": "Z" in sub or "z" in sub,
                        "stroke": stroke.group(1) if stroke else ""})
    return out

def _body(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    return re.sub(r"<desc>.*?</desc>", "", text, flags=re.S)

def _lines(log):
    out = []
    try:
        with open(log, encoding="utf-8", errors="replace") as fh:
            rows = fh.read().splitlines()
    except OSError:
        return out
    for i, r in enumerate(rows):
        s = r.rstrip()
        if s.startswith("(note:") or s.startswith(" not allowed") or s.endswith("invalid syntax") \
           or "not allowed" in s or "gm_linewidth" in s or s.startswith("r("):
            if s.startswith("r("):
                continue
            out.append(s)
    return out

probes, matrix, mkeys = {}, {}, []
with open(Macro.getLocal("recs"), encoding="utf-8") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if not line:
            continue
        parts = line.split("|", 4)
        if parts[0] == "Mkey":
            mkeys.append(parts[1:])
            continue
        kind, pid, rc, svg, cmd = parts
        f = svg[3:] if svg.startswith("svg") else svg
        rec = {"cmd": cmd, "rc": int(rc),
               "lines": _lines(os.path.join(tmp, f + ".log"))}
        svgp = os.path.join(tmp, f + ".svg")
        if svg.startswith("svg") and int(rc) == 0 and os.path.exists(svgp):
            rec["_svg"] = svgp
            if kind in ("P", "F"):
                rec["paths"] = _paths(svgp)
        rec["kind"] = kind
        probes[pid] = rec

for pid, rec in probes.items():
    if rec["kind"] == "S":
        rec["equal_to"] = ""
        if "_svg" in rec:
            mine = _body(rec["_svg"])
            canon = ["S-c-direct", "S-c-ascending", "S-c-stairstep", "S-c-stepstair", "S-c-none"]
            if pid.startswith("S-m-"):
                canon = ["S-m-y", "S-m-n"]
            for c in canon:
                if c != pid and "_svg" in probes.get(c, {}) and _body(probes[c]["_svg"]) == mine:
                    rec["equal_to"] = c
                    break
            if rec["equal_to"] == "" and pid in canon:
                rec["equal_to"] = pid

for pid, tt, opt, base in mkeys:
    rec = probes.pop(pid)
    same = None
    if "_svg" in rec and "_svg" in probes.get(base, {}):
        same = _body(rec["_svg"]) == _body(probes[base]["_svg"])
    matrix.setdefault(tt, {})[opt] = {"rc": rec["rc"], "lines": rec["lines"],
                                      "same_as_base": same, "cmd": rec["cmd"]}
for pid in [p for p in probes if p.startswith("M") and p.endswith("-base")]:
    probes.pop(pid)
for rec in probes.values():
    rec.pop("_svg", None)
    rec.pop("kind", None)

out = {"probes": probes, "matrix": matrix,
       "_meta": {"stata_version": Macro.getLocal("stata_version"),
                 "born_date": Macro.getLocal("born_date"),
                 "dash_commit": Macro.getLocal("dash_commit").strip(),
                 "extracted": Macro.getLocal("extracted"),
                 "scheme": "stcolor"}}
path = os.path.join(repo, "test", "fixtures", "connect_truth.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote " + path)
end
