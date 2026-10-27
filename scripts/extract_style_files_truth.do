* extract_style_files_truth.do -- Stata's style files as twoway reads them
* (WP-31 section 44, E10), written to test/fixtures/style_files_truth.json
* for test/test_style_files.py.
*
* Records:
*   find      findfile's answer for six of BASE's style files, and for
*             user files placed in a directory put on the ado-path for
*             this session (adopath ++, never c(sysdir_personal)): one in
*             the directory itself, one in its style/ subdirectory, one in
*             both, one in its l/ letter subdirectory;
*   draw      plot 1's resolved style (.g.plotregion1.plot1.style) for
*             each Stata style name of the four option classes outside
*             dash's transcribed table (SchemeParser._STYLE_KNOWN minus
*             _STYLE_TABLE, the p# entries left out), under stcolor and
*             s2color, with the call's rc and notes;
*   user      lstyle() and pstyle() of user style files on the ado-path;
*   scheme    user schemes (#include s2color) with class directives;
*   adoarchive  whether c(adoarchive) exists, and _stfilearchive's rc;
*   all.files the style file names in BASE/style, by class.
*
* Run (never the GUI):
*   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_style_files_truth.do

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zf_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zf_bad' {
    display as error "extract_style_files_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
if _rc {
    display as error "extract_style_files_truth.do: set DASH_REPO to the dash repository"
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1

clear all
set more off
set linesize 255
version 19
set graphics off
local entry_scheme "`c(scheme)'"
local stata_version = c(stata_version)
local born_date "`c(born_date)'"
tempfile gh
shell git -C "`repo'" rev-parse HEAD > "`gh'"
tempname fh
file open `fh' using "`gh'", read text
file read `fh' dash_commit
file close `fh'
local extracted "`c(current_date)'"

* ---- the user directory (session ado-path only) ----
tempfile ub
local ud "`ub'_u44"
capture mkdir "`ud'"
capture mkdir "`ud'/style"
capture mkdir "`ud'/l"
tempname w
foreach p in "linestyle-u44a.style|set width thick;set color red;set pattern dash" ///
    "style/linestyle-u44b.style|set width thick;set color red;set pattern dash" ///
    "linestyle-u44c.style|set width thin" ///
    "style/linestyle-u44c.style|set width vthick" ///
    "l/linestyle-u44d.style|set width thin" ///
    "style/shadestyle-u44s.style|set color red;set intensity inten50" ///
    "style/seriesstyle-u44p.style|set marker scheme p2;set line u44b;set area scheme p3" ///
    "scheme-u44.scheme|#include s2color;linestyle p1 u44b" ///
    "scheme-u44l.scheme|#include s2color;linestyle p1line u44b" ///
    "scheme-u44m.scheme|#include s2color;linestyle p1 nosuch" ///
    "scheme-u44s.scheme|#include s2color;shadestyle p1area u44s" ///
    "scheme-u44h.scheme|#include s2color;linestyle ci u44b" {
    gettoken f body : p, parse("|")
    local body = substr(`"`body'"', 2, .)
    file open `w' using "`ud'/`f'", write text replace
    while `"`body'"' != "" {
        gettoken ln body : body, parse(";")
        if `"`ln'"' != ";" file write `w' `"`ln'"' _n
    }
    file close `w'
}
adopath ++ "`ud'"

* ---- records file ----
tempfile records
tempname rf
file open `rf' using "`records'", write text replace
global SF_RF `rf'
global SF_SEQ 0

capture program drop _sf_read
program _sf_read
    // plot 1's resolved style as name=value; fields, in _sf_rec.
    version 19
    local rec ""
    foreach f in mf:marker.fillcolor.rgb mfop:marker.fillcolor.opacity ///
        mfs:marker.fillcolor.stylename ///
        ml:marker.linestyle.color.rgb mlop:marker.linestyle.color.opacity ///
        mls:marker.linestyle.color.stylename ///
        mlw:marker.linestyle.width.val ms:marker.symbol.stylename ///
        msz:marker.size.val lc:line.color.rgb lop:line.color.opacity ///
        lcs:line.color.stylename ///
        lw:line.width.val lp:line.pattern.stylename ///
        af:area.shadestyle.color.rgb afop:area.shadestyle.color.opacity ///
        afs:area.shadestyle.color.stylename ///
        ai:area.shadestyle.intensity.val al:area.linestyle.color.rgb ///
        alop:area.linestyle.color.opacity als:area.linestyle.color.stylename ///
        alw:area.linestyle.width.val ///
        alp:area.linestyle.pattern.stylename {
        gettoken nm path : f, parse(":")
        local path = substr("`path'", 2, .)
        local v ""
        capture local v "`.g.plotregion1.plot1.style.`path''"
        local v = strtrim(stritrim(`"`v'"'))
        local rec `"`rec'`nm'=`v';"'
    }
    c_local _sf_rec `"`rec'"'
end

capture program drop _sf_call
program _sf_call
    // _sf_call id scheme cmd: run twoway cmd under scheme, record plot 1.
    version 19
    args id scheme cmd
    quietly sysuse auto, clear
    set scheme `scheme'
    global SF_SEQ = ${SF_SEQ} + 1
    local log "`c(pwd)'/sf_${SF_SEQ}.log"
    capture graph drop g
    quietly log using "`log'", text replace name(sftruth)
    capture noisily twoway `macval(cmd)' name(g, replace) nodraw
    local rc = _rc
    quietly log close sftruth
    local rec ""
    if !`rc' {
        _sf_read
        local rec `"`_sf_rec'"'
    }
    mata: st_global("SF_CMD_" + st_global("SF_SEQ"), st_local("cmd"))
    file write $SF_RF `"`id'|${SF_SEQ}|`rc'|`log'|`rec'"' _n
end

* ---- find ----
local finds ""
foreach f in linestyle-refline markerstyle-refmarker areastyle-plotregion ///
    seriesstyle-fpall shadestyle-foreground linestyle-p#area ///
    linestyle-u44a linestyle-u44b linestyle-u44c linestyle-u44d {
    capture findfile `f'.style
    local fn ""
    if !_rc local fn "`r(fn)'"
    local finds `"`finds'`f'=`fn';"'
}

* ---- draw: the untranscribed names (dash's own sets, read by import) ----
python:
import os, sys
from sfi import Macro
sys.path.insert(0, Macro.getLocal("repo"))
import dash_render as dr
SP = dr.SchemeParser
opt = {"seriesstyle": "pstyle", "markerstyle": "mstyle",
       "areastyle": "astyle", "linestyle": "lstyle"}
out = []
for c in ("seriesstyle", "markerstyle", "areastyle", "linestyle"):
    for n in sorted(SP._STYLE_KNOWN[c] - set(SP._STYLE_TABLE[c])):
        if n == "p#":
            continue
        out.append("%s:%s" % (opt[c], n.replace("#", "3")))
Macro.setLocal("names57", " ".join(out))
end
display "draw: `: word count `names57'' names"
foreach s in stcolor s2color {
    foreach p of local names57 {
        gettoken o n : p, parse(":")
        local n = substr("`n'", 2, .)
        local t = cond("`o'" == "astyle", "area", "scatter")
        local srt = cond("`o'" == "astyle", "sort", "")
        _sf_call "draw|`s'|`o'|`n'" `s' `"(`t' mpg weight, `srt' `o'(`n')), legend(off)"'
    }
}

* ---- user files and user schemes ----
_sf_call "user|s2color|lstyle|u44a" s2color `"(line mpg weight, sort lstyle(u44a)), legend(off)"'
_sf_call "user|s2color|lstyle|u44b" s2color `"(line mpg weight, sort lstyle(u44b)), legend(off)"'
_sf_call "user|s2color|lstyle|u44c" s2color `"(line mpg weight, sort lstyle(u44c)), legend(off)"'
_sf_call "user|s2color|pstyle|u44p" s2color `"(connected mpg weight, sort pstyle(u44p)), legend(off)"'
foreach s in u44 u44l u44m u44s u44h {
    _sf_call "scheme|`s'|line" `s' `"(line mpg weight, sort), legend(off)"'
    _sf_call "scheme|`s'|scatter" `s' `"(scatter mpg weight), legend(off)"'
    _sf_call "scheme|`s'|area" `s' `"(area mpg weight, sort), legend(off)"'
    _sf_call "scheme|`s'|ci" `s' `"(line mpg weight, sort pstyle(ci)), legend(off)"'
}
file close `rf'
global SF_RF

* ---- adoarchive ----
capture local aa = c(adoarchive)
local aa_rc = _rc
capture _stfilearchive find linestyle-refline.style
local sfa_rc = _rc

python:
import json, os, re, glob
from sfi import Macro
repo = Macro.getLocal("repo")
ud = Macro.getLocal("ud")
def _hex(rgb):
    p = rgb.split()
    if len(p) != 3:
        return None
    try:
        return "#%02x%02x%02x" % tuple(int(float(x)) for x in p)
    except ValueError:
        return None
def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None
def _roles(rec):
    f = dict(x.split("=", 1) for x in rec.split(";") if "=" in x)
    g = lambda k: f.get(k, "")
    return {
        "marker": {"fill": _hex(g("mf")), "fill_opacity": _num(g("mfop")),
                   "fill_none": g("mfs") == "none",
                   "line": _hex(g("ml")), "line_opacity": _num(g("mlop")),
                   "line_none": g("mls") == "none",
                   "line_width": _num(g("mlw")), "symbol": g("ms"),
                   "size": _num(g("msz"))},
        "line": {"color": _hex(g("lc")), "opacity": _num(g("lop")),
                 "none": g("lcs") == "none", "width": _num(g("lw")),
                 "pattern": g("lp")},
        "area": {"fill": _hex(g("af")), "fill_opacity": _num(g("afop")),
                 "fill_none": g("afs") == "none", "intensity": _num(g("ai")),
                 "line": _hex(g("al")), "line_opacity": _num(g("alop")),
                 "line_none": g("als") == "none",
                 "line_width": _num(g("alw")), "line_pattern": g("alp")},
    }
def _notes(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return [" ".join(ln.split()) for ln in fh
                if ln.strip().startswith("(note:")]
out = {"draw": {}, "user": {}, "scheme": {}}
with open(Macro.getLocal("records"), encoding="utf-8") as fh:
    for ln in fh:
        parts = ln.rstrip("\n").split("|")
        rec, log, rc, seq = parts[-1], parts[-2], int(parts[-3]), parts[-4]
        rid = "|".join(parts[:-4])
        grid = parts[0]
        r = {"rc": rc, "cmd": Macro.getGlobal("SF_CMD_" + seq),
             "notes": _notes(log)}
        if rec:
            r.update(_roles(rec))
        out[grid]["|".join(parts[1:-4])] = r
        os.remove(log)
def _short(p):
    if not p:
        return None
    if p.startswith(ud + os.sep) or p.startswith(ud + "/"):
        return "USER/" + p[len(ud) + 1:]
    return p
finds = {}
for kv in Macro.getLocal("finds").split(";"):
    if "=" in kv:
        k, v = kv.split("=", 1)
        finds[k] = _short(v)
out["find"] = finds
base = os.path.dirname(os.path.dirname(finds["linestyle-refline"]))
out["find_base"] = base
files = {}
for c in ("seriesstyle", "markerstyle", "areastyle", "linestyle",
          "shadestyle", "bygraphstyle"):
    files[c] = sorted(os.path.basename(p)[len(c) + 1:-len(".style")]
                      for p in glob.glob(os.path.join(base, "style",
                                                      c + "-*.style")))
out["all.files"] = files
out["all.count"] = len(glob.glob(os.path.join(base, "style", "*.style")))
out["adoarchive"] = {"c_rc": int(Macro.getLocal("aa_rc")),
                     "stfilearchive_rc": int(Macro.getLocal("sfa_rc"))}
out["_meta"] = {"stata_version": Macro.getLocal("stata_version"),
                "born_date": Macro.getLocal("born_date"),
                "dash_commit": Macro.getLocal("dash_commit"),
                "extracted": Macro.getLocal("extracted"),
                "source": "scripts/extract_style_files_truth.do"}
dst = os.path.join(repo, "test", "fixtures", "style_files_truth.json")
with open(dst, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2, sort_keys=True)
    fh.write("\n")
print("style_files_truth: %d draw, %d user, %d scheme records" % (
    len(out["draw"]), len(out["user"]), len(out["scheme"])))
end
set scheme `entry_scheme'
foreach f in linestyle-u44a.style style/linestyle-u44b.style linestyle-u44c.style ///
    style/linestyle-u44c.style l/linestyle-u44d.style style/shadestyle-u44s.style ///
    style/seriesstyle-u44p.style scheme-u44.scheme scheme-u44l.scheme ///
    scheme-u44m.scheme scheme-u44s.scheme scheme-u44h.scheme {
    capture erase "`ud'/`f'"
}
