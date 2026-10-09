* extract_line_width_truth.do -- twoway's line-width ladder, forms, refusals
* and drawn stroke widths for WP-30 S13 (P1.12b, Stata line-width ladder),
* written to test/fixtures/line_width_truth.json for
* test/test_line_width_units.py.
*
* Run (never the GUI; the slot wrapper of scripts/stata_slot.sh):
*   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_line_width_truth.do
* The tree is DASH_REPO, else the current directory when it is a dash tree.
*
* Each probe is one call of _lw_probe: it runs the twoway command under
* capture noisily inside a named text log (so the "(note: ...)" and
* "gm_linewidth" lines are kept), records _rc and the class setting, and,
* when rc is 0, exports the graph as SVG under c(tmpdir).  The probed
* stroke is drawn in magenta (255 0 255), so the python block reads its
* stroke-width from the SVG (scripts/svg_truth.py's attribute readers; it
* never calls Stata).  SVG: 720 units per inch, 10 units = 1 pt.

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_line_width_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_line_width_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the dash repository"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1
global ZL_REPO "`repo'"

clear all
set more off
version 19
set graphics off
set linesize 255
* Every probe is s2color unless its command names scheme() (Stata 19's
* own default is stcolor); session only, never permanently.
set scheme s2color

local stata_version = c(stata_version)
local born_date "`c(born_date)'"
tempfile gh
shell git -C "${ZL_REPO}" rev-parse HEAD > "`gh'"
tempname fh
file open `fh' using "`gh'", read text
file read `fh' dash_commit
file close `fh'
local extracted "`c(current_date)'"

* ---- the probe directory (never in the repository) and its registry -------
local pdir "`c(tmpdir)'"
while strlen(`"`pdir'"') > 1 & inlist(substr(`"`pdir'"', -1, 1), "/", char(92)) {
    local pdir = substr(`"`pdir'"', 1, strlen(`"`pdir'"') - 1)
}
local pdir "`pdir'/lw_probes"
capture mkdir "`pdir'"
local _sf : dir "`pdir'" files "*"
foreach f of local _sf {
    erase "`pdir'/`f'"
}
global ZL_PDIR "`pdir'"
tempname reg
file open `reg' using "`pdir'/registry.txt", write text replace
global ZL_REG "`reg'"
global ZL_SEQ 0

* ---- the ladder: Stata's own style files ----------------------------------
local ladder ""
local files : dir "`c(sysdir_base)'style" files "linewidth-*.style"
foreach f of local files {
    local nm = substr("`f'", 11, strlen("`f'") - 16)
    local val ""
    tempname sh
    file open `sh' using "`c(sysdir_base)'style/`f'", read text
    file read `sh' line
    while r(eof) == 0 {
        local w1 : word 1 of `macval(line)'
        local w2 : word 2 of `macval(line)'
        local w3 : word 3 of `macval(line)'
        if "`w1'" == "set" & "`w2'" == "val" local val "`w3'"
        file read `sh' line
    }
    file close `sh'
    local ladder "`ladder'|`nm'=`val'"
}
global ZL_LADDER "`ladder'"

* ---- _lw_probe key "value" command -----------------------------------------
capture program drop _lw_probe
program define _lw_probe
    version 19
    gettoken key 0 : 0
    gettoken value 0 : 0
    local command = strtrim(`"`macval(0)'"')
    graph drop _all
    // A numbered file id: the probe keys differ only in case (1pt, 1PT),
    // and a case-insensitive file system would merge them.
    global ZL_SEQ = ${ZL_SEQ} + 1
    local id "p${ZL_SEQ}"
    capture log close lw_probe
    log using "${ZL_PDIR}/`id'.log", text replace name(lw_probe)
    capture noisily `command'
    local rc = _rc
    log close lw_probe
    local sl ""
    local sm ""
    if `rc' == 0 {
        capture local sl "`.Graph.plotregion1.plot1.style.line.width.setting'"
        capture local sm "`.Graph.plotregion1.plot1.style.marker.linestyle.width.setting'"
        graph export "${ZL_PDIR}/`id'.svg", as(svg) replace
    }
    file write ${ZL_REG} `"`id'"' _tab `"`key'"' _tab `"`macval(value)'"' _tab `"`macval(command)'"' _tab `"`rc'"' _tab `"`sl'"' _tab `"`sm'"' _n
end

sysuse auto, clear
keep in 1/5
local M `""255 0 255""'

* ladder.<kw>
foreach kw in none vvvthin vvthin vthin thin medthin medium medthick thick vthick vvthick vvvthick {
    _lw_probe ladder.`kw' "`kw'" twoway line mpg weight, lwidth(`kw') lcolor(`M') legend(off)
}

* forms.<id>
foreach v in .3 2 1pt .5cm 1in 10000rs 1e-7 *2 *0 0pt none vvvthin vvthin THICK Thick 1PT 20000pt *33333 1d3 +1pt {
    local id = subinstr(subinstr(subinstr("`v'", "*", "star", .), "-", "neg", .), ".", "p", .)
    _lw_probe forms.`id' "`v'" twoway line mpg weight, lwidth(`v') lcolor(`M') legend(off)
}
_lw_probe forms.default "" twoway line mpg weight, lcolor(`M') legend(off)

* refusals.<id>
_lw_probe refusals.line_lwidth_starneg1 "*-1" twoway line mpg weight, lwidth(*-1)
_lw_probe refusals.line_lwidth_neg1pt "-1pt" twoway line mpg weight, lwidth(-1pt)
_lw_probe refusals.line_lwidth_neg0p5in "-0.5in" twoway line mpg weight, lwidth(-0.5in)
_lw_probe refusals.line_lwidth_1e5rs "1e5rs" twoway line mpg weight, lwidth(1e5rs)
_lw_probe refusals.line_lwidth_neg1 "-1" twoway line mpg weight, lwidth(-1)
_lw_probe refusals.line_lwidth_10001 "10001" twoway line mpg weight, lwidth(10001)
_lw_probe refusals.line_lwidth_starneg0p0001 "*-0.0001" twoway line mpg weight, lwidth(*-0.0001)
_lw_probe refusals.line_lwidth_neg0p0001rs "-0.0001rs" twoway line mpg weight, lwidth(-0.0001rs)
_lw_probe refusals.scatter_mlwidth_starneg1 "*-1" twoway scatter mpg weight, mlwidth(*-1)
_lw_probe refusals.scatter_mlwidth_neg1pt "-1pt" twoway scatter mpg weight, mlwidth(-1pt)
_lw_probe refusals.line_clwidth_starneg1 "*-1" twoway line mpg weight, clwidth(*-1)
_lw_probe refusals.lfitci_alwidth_starneg1 "*-1" twoway lfitci mpg weight, alwidth(*-1)
_lw_probe refusals.lfitci_alwidth_neg1pt "-1pt" twoway lfitci mpg weight, alwidth(-1pt)
_lw_probe refusals.bar_lwidth_starneg1 "*-1" twoway bar mpg weight, lwidth(*-1)
_lw_probe refusals.scatter_lwidth_starneg1 "*-1" twoway scatter mpg weight, lwidth(*-1)
_lw_probe refusals.line_alwidth_starneg1 "*-1" twoway line mpg weight, alwidth(*-1)
_lw_probe refusals.line_lwidth_star40000 "*40000" twoway line mpg weight, lwidth(*40000)
_lw_probe refusals.economist_line_lwidth_20000pt "20000pt" twoway line mpg weight, lwidth(20000pt) scheme(economist)

* schemes.<scheme>.<id>
foreach sch in economist stcolor {
    _lw_probe schemes.`sch'.default "" twoway line mpg weight, lcolor(`M') legend(off) scheme(`sch')
    foreach v in abc *2 1pt medium {
        local id = subinstr("`v'", "*", "star", .)
        _lw_probe schemes.`sch'.`id' "`v'" twoway line mpg weight, lwidth(`v') lcolor(`M') legend(off) scheme(`sch')
    }
}

* sites.<id>
_lw_probe sites.xline_default "" twoway line mpg weight, xline(3000, lcolor(`M')) legend(off)
_lw_probe sites.xline_x2 "*2" twoway line mpg weight, xline(3000, lwidth(*2) lcolor(`M')) legend(off)
_lw_probe sites.xline_1pt "1pt" twoway line mpg weight, xline(3000, lwidth(1pt) lcolor(`M')) legend(off)
_lw_probe sites.xline_1_pt "1 pt" twoway line mpg weight, xline(3000, lwidth(1 pt) lcolor(`M')) legend(off)
_lw_probe sites.plotregion_x2 "*2" twoway line mpg weight, plotregion(lcolor(`M') lwidth(*2)) legend(off)
_lw_probe sites.plotregion_default "" twoway line mpg weight, plotregion(lcolor(`M')) legend(off)
_lw_probe sites.plotregion_thick "thick" twoway line mpg weight, plotregion(lcolor(`M') lwidth(thick)) legend(off)
_lw_probe sites.scatter_outline "" twoway scatter mpg weight, mlcolor(`M') legend(off)
_lw_probe sites.mlwidth_x2 "*2" twoway scatter mpg weight, mlcolor(`M') mlwidth(*2) legend(off)
_lw_probe sites.bar_outline "" twoway bar mpg weight, lcolor(`M') legend(off)
_lw_probe sites.bar_x2 "*2" twoway bar mpg weight, lcolor(`M') lwidth(*2) legend(off)
_lw_probe sites.economist_bar_outline "" twoway bar mpg weight, lcolor(`M') legend(off) scheme(economist)
_lw_probe sites.lfitci_outline "" twoway lfitci mpg weight, alcolor(`M') legend(off)
_lw_probe sites.lfitci_alwidth_x2 "*2" twoway lfitci mpg weight, alcolor(`M') alwidth(*2) legend(off)

* user_scheme.THICK: a scheme file written into the working directory
tempname us
file open `us' using "scheme-lwthickcase.scheme", write text replace
file write `us' "#include s2color" _n "linewidth p THICK" _n
file close `us'
_lw_probe user_scheme.THICK "THICK" twoway line mpg weight, scheme(lwthickcase) legend(off)
capture erase "scheme-lwthickcase.scheme"

file close ${ZL_REG}

python:
import json, os, re, sys
from sfi import Macro

def L(n):
    return Macro.getLocal(n)

repo = Macro.getGlobal("ZL_REPO")
pdir = Macro.getGlobal("ZL_PDIR")
sys.path.insert(0, os.path.join(repo, "scripts"))
import svg_truth

_DECL = re.compile(r'style="([^"]*)"|\{([^{}]*)\}')

def magenta_widths(path):
    """stroke-width (SVG units) of every magenta stroke, read from each
    style attribute and each CSS rule (Stata writes a band's outline as a
    class rule) through svg_truth's declaration reader."""
    with open(path, encoding="utf-8") as fh:
        txt = fh.read()
    out = []
    for m in _DECL.finditer(txt):
        st = svg_truth._style_of({"style": m.group(1) or m.group(2) or ""})
        if (st.get("stroke") or "").strip().lower() != "#ff00ff":
            continue
        w = svg_truth._fnum(st.get("stroke-width", ""))
        if w is not None:
            out.append(w)
    return out

def fnum(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None

def log_line(pid, needle):
    p = os.path.join(pdir, pid + ".log")
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            if needle in ln:
                return ln.strip()
    return ""

ladder_rs = {}
for part in Macro.getGlobal("ZL_LADDER").split("|"):
    if "=" in part:
        k, v = part.split("=", 1)
        ladder_rs[k] = fnum(v)

out = {"ladder": {}, "forms": {}, "refusals": {}, "schemes": {},
       "sites": {}, "user_scheme": {}}
with open(os.path.join(pdir, "registry.txt"), encoding="utf-8") as fh:
    rows = [ln.rstrip("\n").split("\t") for ln in fh if ln.strip()]
for pid, key, value, command, rc, sl, sm in rows:
    rc = int(rc)
    svg = os.path.join(pdir, pid + ".svg")
    ws = magenta_widths(svg) if rc == 0 and os.path.exists(svg) else []
    stroke_pt = round(max(ws) / 10.0, 4) if ws else (0.0 if rc == 0 else None)
    setting = fnum(sm if key.startswith("sites.") and "mlwidth" in key or
                   "scatter_outline" in key else sl)
    parts = key.split(".")
    area = parts[0]
    if area == "ladder":
        out["ladder"][parts[1]] = {"rc": rc, "setting": setting,
                                   "style_val": ladder_rs.get(parts[1])}
    elif area == "forms":
        out["forms"][parts[1]] = {"value": value, "rc": rc,
                                  "setting": setting, "stroke_pt": stroke_pt}
    elif area == "refusals":
        typ, opt = parts[1].split("_")[:2] if not parts[1].startswith(
            "economist") else parts[1].split("_")[1:3]
        out["refusals"][parts[1]] = {
            "option": opt, "type": typ, "value": value, "rc": rc,
            "words": log_line(pid, "gm_linewidth")}
    elif area == "schemes":
        out["schemes"].setdefault(parts[1], {})[parts[2]] = {
            "setting": setting, "stroke_pt": stroke_pt}
    elif area == "sites":
        out["sites"][parts[1]] = {"stroke_pt": stroke_pt}
    elif area == "user_scheme":
        out["user_scheme"][parts[1]] = {
            "rc": rc, "setting": setting,
            "note": log_line(pid, "not found in class linewidth")}

nz = [r["stroke_pt"] for r in out["forms"].values()
      if r["stroke_pt"] not in (None, 0.0)]
out["floor_pt"] = round(min(nz), 4)
assert out["floor_pt"] == 0.3, out["floor_pt"]

for f in os.listdir(pdir):
    os.remove(os.path.join(pdir, f))
os.rmdir(pdir)

out["_meta"] = {"stata_version": L("stata_version"),
                "born_date": L("born_date"),
                "dash_commit": L("dash_commit").strip(),
                "extracted": L("extracted"),
                "units": "SVG 720 units per inch; 10 units = 1 pt; 1 rs = min(graph width, height)/100",
                "source": "scripts/extract_line_width_truth.do"}
path = os.path.join(repo, "test", "fixtures", "line_width_truth.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
Macro.setGlobal("ZL_N", str(len(rows)))
end
display as text "line_width_truth: wrote ${ZL_N} probes"
