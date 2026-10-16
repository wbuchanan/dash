*! extract_data_locale_truth.do
*! WP-31 S43 (G1, G2, G3): Stata's extended missing values, set dp comma,
*! the %tC leap-second table, graph set fonts and a variable named x.
*!
*! Probes (keys of test/fixtures/data_locale_truth.json):
*!   em.by_missing, em.by_missing_labelled  by(rep78, missing) panel titles
*!   em.mlabel                              marker label texts of .a/.b rows
*!   dp.f dp.fc dp.g dp.td                  display under set dp comma
*!   dp.axis, dp.axis_dec                   tick labels under set dp comma
*!   leap.table                             the %tc instants where Cofc()
*!                                          steps by one second
*!   leap.roundtrip                         cofC() of 20 %tC values
*!   leap.inside                            cofC() inside a leap second
*!   fonts.home, fonts.svg                  where graph set keeps a face
*!   shadow.hover                           twoway with a variable named x
*! The trailing python: block reads the records into the fixture, never
*! calls Stata and starts no subprocess.  The probe restores the svg
*! fontface it found.
*!
*! Run (Stata only through the slot wrapper, never the GUI):
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> \
*!       <repo>/scripts/extract_data_locale_truth.do

* Root: DASH_REPO, else the current directory when it is a dash tree.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_data_locale_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_data_locale_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1

clear all
set more off
set linesize 255
version 19
set graphics off
set scheme s2color
set dp period

global DL_REPO "`repo'"
local work "`c(tmpdir)'dash_data_locale_probe"
capture mkdir "`work'"
global DL_PDIR "`work'"

local stata_version = c(stata_version)
local born_date "`c(born_date)'"
local extracted "`c(current_date)'"
tempfile dlgit
quietly shell git -C "${DL_REPO}" rev-parse HEAD > "`dlgit'"
tempname dlgh
file open `dlgh' using "`dlgit'", read text
file read `dlgh' dlline
file close `dlgh'
local dash_commit = trim(`"`dlline'"')

tempname reg
file open `reg' using "${DL_PDIR}/registry.txt", write text replace

* ---- G1: extended missing values -----------------------------------------
sysuse auto, clear
local seen 0
forvalues i = 1/`=_N' {
    if missing(rep78[`i']) {
        local ++seen
        quietly replace rep78 = cond(`seen' <= 2, .a, .b) in `i'
    }
}
capture noisily twoway scatter mpg weight, by(rep78, missing)
file write `reg' "rc" _tab "em.by_missing" _tab "`=_rc'" _n
quietly graph export "${DL_PDIR}/em_by.svg", replace
label define rl .a "Not asked"
label values rep78 rl
capture noisily twoway scatter mpg weight, by(rep78, missing)
file write `reg' "rc" _tab "em.by_missing_labelled" _tab "`=_rc'" _n
quietly graph export "${DL_PDIR}/em_byl.svg", replace
label values rep78
capture noisily twoway scatter mpg weight, mlabel(rep78)
file write `reg' "rc" _tab "em.mlabel" _tab "`=_rc'" _n
quietly graph export "${DL_PDIR}/em_ml.svg", replace

* ---- G2: set dp comma ----------------------------------------------------
set dp comma
local f : display %9.2f 3.14159
file write `reg' "text" _tab "dp.f" _tab `"`f'"' _n
local f : display %12.2fc 1234567.891
file write `reg' "text" _tab "dp.fc" _tab `"`f'"' _n
local f : display %9.0g 0.5
file write `reg' "text" _tab "dp.g" _tab `"`f'"' _n
local f : display %td 20000
file write `reg' "text" _tab "dp.td" _tab `"`f'"' _n
sysuse auto, clear
capture noisily twoway scatter mpg weight
file write `reg' "rc" _tab "dp.axis" _tab "`=_rc'" _n
quietly graph export "${DL_PDIR}/dp_axis.svg", replace
capture noisily twoway scatter mpg gear_ratio
file write `reg' "rc" _tab "dp.axis_dec" _tab "`=_rc'" _n
quietly graph export "${DL_PDIR}/dp_axis_dec.svg", replace
set dp period

* ---- G2: %tC leap seconds ------------------------------------------------
foreach d in 30jun1972 31dec1972 31dec1973 31dec1974 31dec1975 31dec1976 ///
    31dec1977 31dec1978 31dec1979 30jun1981 30jun1982 30jun1983 30jun1985 ///
    31dec1987 31dec1989 31dec1990 30jun1992 30jun1993 30jun1994 31dec1995 ///
    30jun1997 31dec1998 31dec2005 31dec2008 30jun2012 30jun2015 31dec2016 {
    local t = tc(`d' 23:59:59.999) + 1
    local before = Cofc(`t' - 1) - (`t' - 1)
    local after = Cofc(`t') - `t'
    file write `reg' "leap" _tab "`d'" _tab %21.0f (`t') _tab %21.0f (`before') _tab %21.0f (`after') _n
}
set seed 4301
local lo = tC(01jan1972 00:00:00)
local hi = tC(01jan2026 00:00:00)
forvalues i = 1/20 {
    local C = round(`lo' + runiform() * (`hi' - `lo'))
    file write `reg' "trip" _tab "`i'" _tab %21.0f (`C') _tab %21.0f (cofC(`C')) _n
}
* Three table instants T (midnight after the leap second, %tc): a %tC
* value inside the leap second, Cofc(T) - 500, and the spec's
* Cofc(T) + 500 (half a second after midnight).
foreach d in 31dec1972 31dec1998 31dec2016 {
    local T = tc(`d' 23:59:59.999) + 1
    local Ci = Cofc(`T') - 500
    local Ca = Cofc(`T') + 500
    file write `reg' "inside" _tab "`d'" _tab %21.0f (`Ci') _tab %21.0f (cofC(`Ci')) _tab %21.0f (`Ca') _tab %21.0f (cofC(`Ca')) _n
}

* ---- G2: graph set fonts -------------------------------------------------
* The face in force before the probe, restored after it.
quietly log using "${DL_PDIR}/fonts_before.log", text replace name(dlf0)
graph set svg
quietly log close dlf0
sysuse auto, clear
capture noisily twoway scatter mpg weight, title("{stSans:a}")
quietly graph export "${DL_PDIR}/fonts_default.svg", replace
quietly log using "${DL_PDIR}/fonts_home.log", text replace name(dlf1)
graph set svg fontface Courier
graph set svg
graph query, schemes
macro list
char list
display "c(fontface)=[`c(fontface)']"
quietly log close dlf1
capture noisily twoway scatter mpg weight, title("{stSans:a}")
quietly graph export "${DL_PDIR}/fonts_svg.svg", replace
graph set svg fontfacesans Courier
capture noisily twoway scatter mpg weight, title("{stSans:a}")
quietly graph export "${DL_PDIR}/fonts_sans.svg", replace
* Restore the faces found before the probe (the log's fontface lines).
tempname fh
file open `fh' using "${DL_PDIR}/fonts_before.log", read text
local prev "default"
local prevsans "default"
file read `fh' line
while r(eof) == 0 {
    if ustrregexm(`"`macval(line)'"', "^ *fontface +(.+[^ ]) +font name *$") {
        local prev = strtrim(ustrregexs(1))
    }
    if ustrregexm(`"`macval(line)'"', "^ *fontfacesans +(.+[^ ]) +font name *$") {
        local prevsans = strtrim(ustrregexs(1))
    }
    file read `fh' line
}
file close `fh'
if inlist(`"`prev'"', "", "Helvetica") local prev "default"
if inlist(`"`prevsans'"', "", "Helvetica") local prevsans "default"
graph set svg fontface `"`prev'"'
graph set svg fontfacesans `"`prevsans'"'

* ---- G3: a variable named x ----------------------------------------------
sysuse auto, clear
generate x = price
capture noisily twoway scatter mpg weight
file write `reg' "rc" _tab "shadow.hover" _tab "`=_rc'" _n

file close `reg'

python:
import json, os, re, sys
from sfi import Macro

def L(n):
    return Macro.getLocal(n)

repo = Macro.getGlobal("DL_REPO")
pdir = Macro.getGlobal("DL_PDIR")
sys.path.insert(0, os.path.join(repo, "scripts"))
import svg_truth

out = {}
rows = []
with open(os.path.join(pdir, "registry.txt"), encoding="utf-8") as fh:
    for line in fh:
        rows.append(line.rstrip("\n").split("\t"))

rc = {r[1]: int(r[2]) for r in rows if r[0] == "rc"}

def texts(name):
    return [t["text"] for t in svg_truth.svg_texts(os.path.join(pdir, name))]

# A by() panel title is one of rep78's values, its label or a missing code.
def titles(name):
    keep = {"1", "2", "3", "4", "5", ".", "Not asked"} | {
        "." + c for c in "abcdefghijklmnopqrstuvwxyz"}
    return [t for t in texts(name) if t in keep]

out["em.by_missing"] = {"rc": rc["em.by_missing"],
                        "titles": titles("em_by.svg")}
out["em.by_missing"]["panels"] = len(out["em.by_missing"]["titles"])
out["em.by_missing_labelled"] = {"rc": rc["em.by_missing_labelled"],
                                 "titles": titles("em_byl.svg")}
ml = [t for t in texts("em_ml.svg") if t.startswith(".")]
out["em.mlabel"] = {"rc": rc["em.mlabel"],
                    "labels": {t: ml.count(t) for t in sorted(set(ml))}}

for r in rows:
    if r[0] == "text":
        out[r[1]] = r[2]

def ticks(name):
    return [t for t in texts(name) if re.fullmatch(r"[0-9.,]+", t)]

out["dp.axis"] = {"rc": rc["dp.axis"], "ticks": ticks("dp_axis.svg")}
out["dp.axis_dec"] = {"rc": rc["dp.axis_dec"],
                      "ticks": ticks("dp_axis_dec.svg")}

leaps = [r for r in rows if r[0] == "leap"]
out["leap.candidates"] = [
    {"date": r[1], "tc": int(r[2]), "before": int(r[3]), "after": int(r[4])}
    for r in leaps]
out["leap.table"] = [int(r[2]) for r in leaps
                     if int(r[4]) - int(r[3]) == 1000]
out["leap.roundtrip"] = [[int(r[2]), int(r[3])] for r in rows
                         if r[0] == "trip"]
out["leap.inside"] = [[int(r[2]), int(r[3])] for r in rows
                      if r[0] == "inside"]
out["leap.after_midnight"] = [[int(r[4]), int(r[5])] for r in rows
                              if r[0] == "inside"]

def read(name):
    with open(os.path.join(pdir, name), encoding="utf-8",
              errors="replace") as fh:
        return fh.read()

home = read("fonts_home.log")
out["fonts.home"] = {
    "log": home[:20000],
    "graph_set_prints_face": bool(re.search(r"fontface\s+Courier", home)),
    "global_holds_face": bool(re.search(r"^\S+:\s.*Courier", home,
                                        re.M)),
}

def family(name):
    raw = read(name)
    m = re.search(r"<text[^>]*>\s*a\s*</text>", raw)
    if not m:
        return None
    f = re.search(r'font-family\s*[:=]\s*"?([^";>]+)', m.group(0))
    return f.group(1).strip() if f else None

out["fonts.svg"] = {"default": family("fonts_default.svg"),
                    "fontface_courier": family("fonts_svg.svg"),
                    "fontfacesans_courier": family("fonts_sans.svg")}
out["shadow.hover"] = {"rc": rc["shadow.hover"]}

for f in os.listdir(pdir):
    os.remove(os.path.join(pdir, f))
os.rmdir(pdir)

out["_meta"] = {"stata_version": L("stata_version"),
                "born_date": L("born_date"),
                "dash_commit": L("dash_commit").strip(),
                "extracted": L("extracted"),
                "source": "scripts/extract_data_locale_truth.do"}
path = os.path.join(repo, "test", "fixtures", "data_locale_truth.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
Macro.setGlobal("DL_N", str(len(out) - 1))
end
display as text "data_locale_truth: wrote ${DL_N} records"
