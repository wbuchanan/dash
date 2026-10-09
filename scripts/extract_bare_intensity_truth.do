*! extract_bare_intensity_truth.do
*! WP-30 section 43 (P1.13b): ground truth for a bare colour intensity or
*! opacity (*#, %#, *#%#) at every colour site, for
*! test/fixtures/bare_intensity_truth.json.
*!
*! WHY THIS EXISTS
*!
*! twoway reads a colour without a name of its own, such as mcolor(*.5),
*! as the colour the element would draw without the option, adjusted.
*! dash kept the default unadjusted.  This script records, per scheme
*! (s2color, stcolor, sttrans, s1rcolor), per probe and per value, the
*! colours of the SVG that are new against the same graph without the
*! option (a multiset difference): each as (tag, fill, fill-opacity,
*! stroke, stroke-opacity) and its count.
*! The unknown-colour probes (U*) record the same under s2color, plus the
*! notes twoway printed.
*!
*! Run (never the GUI; the slot wrapper):
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_bare_intensity_truth.do
*!
*! Never calls back into Stata from the trailing python: block.
*! ---------------------------------------------------------------------------

clear all
set graphics off
set more off
set linesize 255

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zb_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zb_bad' {
    display as error "extract_bare_intensity_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zb_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zb_rc' | _rc {
    local _zb_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_bare_intensity_truth.do: `_zb_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1
global ZB_REPO "`repo'"

local stata_version = c(stata_version)
local born_date "`c(born_date)'"
local extracted "`c(current_date)'"
tempfile gh
quietly shell git -C "${ZB_REPO}" rev-parse HEAD > "`gh'"
tempname fh
file open `fh' using "`gh'", read text
file read `fh' dash_commit
file close `fh'

local pdir "`c(tmpdir)'"
while strlen(`"`pdir'"') > 1 & inlist(substr(`"`pdir'"', -1, 1), "/", char(92)) {
    local pdir = substr(`"`pdir'"', 1, strlen(`"`pdir'"') - 1)
}
local pdir "`pdir'/bare_intensity_probes"
capture mkdir "`pdir'"
local _sf : dir "`pdir'" files "*"
foreach f of local _sf {
    erase "`pdir'/`f'"
}
global ZB_PDIR "`pdir'"
tempname reg
file open `reg' using "`pdir'/registry.txt", write text replace
global ZB_REG "`reg'"
global ZB_SEQ 0

* ---- _bi_probe id scheme value : command ------------------------------------
* Runs <command> scheme(<scheme>) under capture noisily inside a named log
* and exports the SVG when rc is 0.  value is "-" for the probe's base.
capture program drop _bi_probe
program define _bi_probe
    version 19
    gettoken id 0 : 0
    gettoken sch 0 : 0
    gettoken val 0 : 0
    gettoken colon 0 : 0
    local cmd = strtrim(`"`macval(0)'"')
    graph drop _all
    global ZB_SEQ = ${ZB_SEQ} + 1
    local f "p${ZB_SEQ}"
    capture log close bi_probe
    quietly log using "${ZB_PDIR}/`f'.log", text replace name(bi_probe)
    capture noisily `macval(cmd)' scheme(`sch')
    local rc = _rc
    quietly log close bi_probe
    if `rc' == 0 {
        quietly graph export "${ZB_PDIR}/`f'.svg", as(svg) replace
    }
    file write ${ZB_REG} `"`f'"' _tab `"`id'"' _tab `"`sch'"' _tab `"`val'"' _tab `"`rc'"' _tab `"`macval(cmd)'"' _n
end

sysuse auto, clear
gen t = _n

* id | base command (ends in a comma or options) | option template (@ = V)
local P01 "scatter mpg weight,|mcolor(@)"
local P02 "scatter mpg weight,|mfcolor(@)"
local P03 "scatter mpg weight,|mlcolor(@)"
local P04 "scatter mpg weight, pstyle(p3)|mcolor(@)"
local P05 "line mpg weight, sort|lcolor(@)"
local P06 "twoway connected mpg weight, sort|lcolor(@)"
local P07 "twoway bar mpg rep78 if rep78<.,|color(@)"
local P08 "twoway bar mpg rep78 if rep78<.,|fcolor(@)"
local P09 "twoway bar mpg rep78 if rep78<., fintensity(50)|fcolor(@)"
local P10 "twoway bar mpg rep78 if rep78<.,|lcolor(@)"
local P11 "twoway area mpg weight, sort|fcolor(@)"
local P12 "twoway rarea mpg turn weight, sort|fcolor(@)"
local P13 "twoway histogram mpg,|fcolor(@)"
local P14 "twoway lfitci mpg weight,|acolor(@)"
local P15 "twoway dropline mpg weight,|lcolor(@)"
local P16 "twoway rcap mpg turn weight,|lcolor(@)"
local P17 "twoway pcarrow mpg weight turn length,|lcolor(@)"
local P18 "twoway scatteri 20 3000,|mcolor(@)"
local P19 "scatter mpg weight, mlabel(make)|mlabcolor(@)"
local P20 "scatter mpg weight, title(T)|title(T, color(@))"
local P21 "scatter mpg weight, subtitle(S)|subtitle(S, color(@))"
local P22 "scatter mpg weight, note(N)|note(N, color(@))"
local P23 "scatter mpg weight, caption(C)|caption(C, color(@))"
local P24 "scatter mpg weight, ytitle(Y)|ytitle(Y, color(@))"
local P25 "scatter mpg weight,|ylabel(, labcolor(@))"
local P26 "scatter mpg weight,|yscale(lcolor(@))"
local P27 "scatter mpg weight,|graphregion(color(@))"
local P28 "scatter mpg weight,|plotregion(color(@))"
local P29 "scatter mpg weight,|plotregion(lcolor(@))"
local P30 "scatter mpg weight,|xline(3000, lcolor(@))"
local P31 "twoway (scatter mpg weight) (scatter price weight, yaxis(2)|mcolor(@)),"

foreach sch in s2color stcolor sttrans s1rcolor {
    forvalues k = 1/31 {
        local id = "P" + string(`k', "%02.0f")
        local row `"``id''"'
        local cut = strpos(`"`row'"', "|")
        local b = substr(`"`row'"', 1, `cut' - 1)
        local o = substr(`"`row'"', `cut' + 1, .)
        if "`id'" == "P31" {
            _bi_probe `id' `sch' - : `b'),
        }
        else {
            _bi_probe `id' `sch' - : `b'
        }
        foreach v in *.5 *2 %50 *.5%50 {
            local oo : subinstr local o "@" "`v'", all
            _bi_probe `id' `sch' `v' : `b' `oo'
        }
    }
}

* ---- U: an unknown colour at the direct sites (s2color) ---------------------
_bi_probe U01 s2color - : twoway bar mpg rep78 if rep78<.,
_bi_probe U01 s2color bogus : twoway bar mpg rep78 if rep78<., color(bogus)
_bi_probe U02 s2color - : twoway area mpg weight, sort
_bi_probe U02 s2color bogus : twoway area mpg weight, sort color(bogus)
_bi_probe U03 s2color - : twoway dropline mpg weight,
_bi_probe U03 s2color bogus : twoway dropline mpg weight, lcolor(bogus)
_bi_probe U04 s2color - : scatter mpg weight, mlabel(make)
_bi_probe U04 s2color bogus : scatter mpg weight, mlabel(make) mlabcolor(bogus)
_bi_probe U05 s2color - : scatter mpg weight,
_bi_probe U05 s2color bogus : scatter mpg weight, xline(3000, lcolor(bogus))

file close ${ZB_REG}

python:
import collections, json, os, re
from sfi import Macro

repo = Macro.getGlobal("ZB_REPO")
pdir = Macro.getGlobal("ZB_PDIR")
_EL = re.compile(r'<(circle|path|polygon|polyline|rect|line|text|use)\b([^>]*?)/?>', re.S)
_AT = re.compile(r'([\w:-]+)="([^"]*)"')

def _num(s):
    try:
        return round(float(s), 4)
    except (TypeError, ValueError):
        return None

def elements(path):
    """Counter of (tag, fill, fill-opacity, stroke, stroke-opacity) over
    every drawn element of *path*; opacity is the product of the element's
    own opacity and the fill/stroke opacity (1 when absent)."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        txt = fh.read()
    out = collections.Counter()
    for m in _EL.finditer(txt):
        a = dict(_AT.findall(m.group(2)))
        st = {}
        for part in a.get("style", "").split(";"):
            if ":" in part:
                k, v = part.split(":", 1)
                st[k.strip()] = v.strip()
        g = lambda k: st.get(k, a.get(k))
        op = _num(g("opacity"))
        op = 1.0 if op is None else op
        fo, so = _num(g("fill-opacity")), _num(g("stroke-opacity"))
        fill = (g("fill") or "").lower() or None
        stroke = (g("stroke") or "").lower() or None
        out[(m.group(1), fill, round((1.0 if fo is None else fo) * op, 4),
             stroke, round((1.0 if so is None else so) * op, 4))] += 1
    return out

def notes(f):
    p = os.path.join(pdir, f + ".log")
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8", errors="replace") as fh:
        return [ln.strip() for ln in fh
                if ln.strip().startswith(("(note:", "dash:"))]

rows = []
with open(os.path.join(pdir, "registry.txt"), encoding="utf-8") as fh:
    rows = [ln.rstrip("\n").split("\t") for ln in fh if ln.strip()]
base = {}
for f, pid, sch, val, rc, cmd in rows:
    if val == "-" and rc == "0":
        base[(pid, sch)] = elements(os.path.join(pdir, f + ".svg"))

schemes = {}
for f, pid, sch, val, rc, cmd in rows:
    if val == "-":
        continue
    rec = {"cmd": cmd, "rc": int(rc), "notes": notes(f), "new": []}
    p = os.path.join(pdir, f + ".svg")
    if int(rc) == 0 and os.path.exists(p) and (pid, sch) in base:
        now, was = elements(p), base[(pid, sch)]
        new, gone = now - was, was - now
        rec["new"] = [{"tag": t[0], "fill": t[1], "fill_opacity": t[2],
                       "stroke": t[3], "stroke_opacity": t[4], "n": n}
                      for t, n in sorted(new.items(), key=lambda x: (-x[1], str(x[0])))]
        rec["base"] = [{"tag": t[0], "fill": t[1], "fill_opacity": t[2],
                        "stroke": t[3], "stroke_opacity": t[4], "n": n}
                       for t, n in sorted(gone.items(), key=lambda x: (-x[1], str(x[0])))]
    schemes.setdefault(sch, {}).setdefault(pid, {})[val] = rec

for name in os.listdir(pdir):
    os.remove(os.path.join(pdir, name))
os.rmdir(pdir)

doc = {
    "_meta": {"stata_version": Macro.getLocal("stata_version"),
              "born_date": Macro.getLocal("born_date"),
              "dash_commit": Macro.getLocal("dash_commit").strip(),
              "extracted": Macro.getLocal("extracted"),
              "source": "scripts/extract_bare_intensity_truth.do",
              "reading": "new: the (tag, fill, fill-opacity, stroke, "
                         "stroke-opacity) tuples of the probe's SVG absent "
                         "from the same graph without the option; base: "
                         "those the option removed"},
    "schemes": schemes,
}
path = os.path.join(repo, "test", "fixtures", "bare_intensity_truth.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=1, sort_keys=True)
    fh.write("\n")
Macro.setGlobal("ZB_N", str(sum(len(v) for s in schemes.values() for v in s.values())))
end
display as text "bare_intensity_truth: wrote ${ZB_N} probes"
