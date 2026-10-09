* extract_style_name_truth.do -- twoway's other named styles (WP-30
* P1.14b, section 36), written to test/fixtures/style_name_truth.json for
* test/test_style_names.py.
*
* Each call runs `twoway (...) (...) ..., nodraw legend(off)' of at most 25
* layers, one style name per layer, and reads every plot's resolved style
* from the graph object (.g.plotregion1.plot<k>.style: marker, line, area
* and the label colour), with the call's rc and the `(note:  ...)' lines of
* its text log.  A note names its style and class, so a batched call's
* notes stay attributable.
*
* Grids (record id GRID|SCHEME|OPTION|NAME; a name with characters a
* record id cannot hold is numbered, its text kept in "name"):
*   N  every table name of every class (stcolor, s2color, s1mono,
*      s1rcolor), the plain names and the p1/p3/p15 template instances
*      under the other 22 schemes;
*   U  names twoway does not know, on plots 2.. after a plain plot 1;
*   K  Stata-known names outside dash's table (stcolor);
*   C  the ci fits under pstyle() (stcolor, s2color);
*   T  pstyle(ci)/pstyle(ci2) on each type (stcolor, s2color);
*   Q  note counts (stcolor);  D  dstyle/dlstyle/bmlinestyle (stcolor);
*   H  hostile names (stcolor);  S  SVG of the none forms (stcolor).
*
* Run (never the GUI; the slot wrapper of scripts/stata_slot.sh), whole:
*   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_style_name_truth.do
* or in three parallel parts and a merge, each part in its own directory:
*   OS_PART=1|2|3 ... stata_slot.sh <scratch>/p<k> ...   (writes os_part.json there)
*   OS_PART=merge OS_PARTS="<p1>/os_part.json;<p2>/...;<p3>/..." ... stata_slot.sh <scratch>/m ...

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_style_name_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zr_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zr_rc' | _rc {
    display as error "extract_style_name_truth.do: set DASH_REPO to the dash repository"
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
if `"`c(python_exec)'"' == "" {
    display as error "extract_style_name_truth.do: python is not set up (c(python_exec) is empty)"
    exit 601
}
local part : environment OS_PART
timer clear 36
timer on 36

local stata_version = c(stata_version)
local born_date "`c(born_date)'"
tempfile gh
shell git -C "`repo'" rev-parse HEAD > "`gh'"
tempname fh
file open `fh' using "`gh'", read text
file read `fh' dash_commit
file close `fh'
local extracted "`c(current_date)'"

if "`part'" == "merge" {
    timer off 36
    quietly timer list 36
    local seconds = r(t36)
    python:
import json, os
from sfi import Macro
repo = Macro.getLocal("repo")
paths = [p for p in os.environ.get("OS_PARTS", "").split(";") if p]
out = {"records": {}, "notes": {}, "svg": {}, "cmds": {}, "schemes": [],
       "seconds": 0.0}
for p in paths:
    with open(p, encoding="utf-8") as fh:
        d = json.load(fh)
    for k in ("records", "notes", "svg", "cmds"):
        out[k].update(d[k])
    out["schemes"] = sorted(set(out["schemes"]) | set(d["schemes"]))
    out["seconds"] += float(d["_meta"]["seconds"])
meta = {"stata_version": Macro.getLocal("stata_version"),
        "born_date": Macro.getLocal("born_date"),
        "dash_commit": Macro.getLocal("dash_commit"),
        "extracted": Macro.getLocal("extracted"),
        "source": "scripts/extract_style_name_truth.do",
        "seconds": round(out.pop("seconds"), 1)}
out["_meta"] = meta
dst = os.path.join(repo, "test", "fixtures", "style_name_truth.json")
with open(dst, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2, sort_keys=True)
    fh.write("\n")
print("style_name_truth: wrote %d records in %s s" % (len(out["records"]), meta["seconds"]))
end
    exit
}

tempfile records
tempname rf
file open `rf' using "`records'", write text replace
global OS_RF `rf'
global OS_SEQ 0

capture program drop _os_read
program _os_read
    // _os_read k: plot k's resolved style, one ;-separated record of
    // name=value fields, in the caller's _os_rec ("" when absent).
    version 19
    args k
    local rec ""
    capture local t "`.g.plotregion1.plot`k'.style.marker.fillcolor.rgb'"
    if _rc | `"`t'"' == "" {
        c_local _os_rec ""
        exit
    }
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
        alp:area.linestyle.pattern.stylename labc:label.textstyle.color.rgb {
        gettoken nm path : f, parse(":")
        local path = substr("`path'", 2, .)
        local v ""
        capture local v "`.g.plotregion1.plot`k'.style.`path''"
        local v = strtrim(stritrim(`"`v'"'))
        local rec `"`rec'`nm'=`v';"'
    }
    c_local _os_rec `"`rec'"'
end

capture program drop _os_call
program _os_call
    // _os_call callid scheme nplots svg ids cmd: run twoway cmd under
    // scheme on auto, log it, and append one line per plot: the record id
    // of plot k is word k of ids ("-" skips the plot).
    version 19
    args callid scheme nplots svg ids cmd
    quietly sysuse auto, clear
    set scheme `scheme'
    global OS_SEQ = ${OS_SEQ} + 1
    local log "`c(pwd)'/os_${OS_SEQ}.log"
    local svgf ""
    capture graph drop g
    quietly log using "`log'", text replace name(ostruth)
    local nd = cond("`svg'" == "1", "", "nodraw")
    capture noisily twoway `macval(cmd)' name(g, replace) `nd'
    local rc = _rc
    quietly log close ostruth
    if !`rc' & "`svg'" == "1" {
        local svgf "`c(pwd)'/os_${OS_SEQ}.svg"
        quietly graph export "`svgf'", replace name(g)
    }
    mata: st_global("OS_CMD_" + st_global("OS_SEQ"), st_local("cmd"))
    forvalues k = 1/`nplots' {
        local id : word `k' of `ids'
        if "`id'" == "-" continue
        local rec ""
        if !`rc' {
            _os_read `k'
            local rec `"`_os_rec'"'
        }
        file write $OS_RF `"`callid'|${OS_SEQ}|`id'|`k'|`rc'|`svgf'|`log'|`rec'"' _n
    }
    if `nplots' == 0 {
        file write $OS_RF `"`callid'|${OS_SEQ}|-|0|`rc'|`svgf'|`log'|"' _n
    }
end

capture program drop _os_batch
program _os_batch
    // _os_batch grid scheme opt type plain names: twoway calls of at most
    // 25 layers, `type mpg weight in 1/2, opt(name)', one name per layer;
    // plain 1 puts a plain layer first (the U grid).
    version 19
    args grid scheme opt type plain names
    local n : word count `names'
    local i = 1
    local call = 0
    while `i' <= `n' {
        local ++call
        local cmd ""
        local ids ""
        local np = 0
        if `plain' {
            local cmd `"(`type' mpg weight in 1/2)"'
            local ids "-"
            local np = 1
        }
        local j = 0
        while `j' < 25 & `i' <= `n' {
            local nm : word `i' of `names'
            local cmd `"`cmd' (`type' mpg weight in 1/2, `opt'(`nm'))"'
            local ids "`ids' `grid'|`scheme'|`opt'|`nm'"
            local ++np
            local ++j
            local ++i
        }
        _os_call "`grid'|`scheme'|`opt'|call`call'" `scheme' `np' 0 "`ids'" `"`cmd', legend(off)"'
    }
end

* ---- The names (StataNow 19.5, /Applications/StataNow/ado/base/style) ----
local L_plain "axisline background ci ci2 ci2_area ci_area clegend cvcvline cvlsline cvseline dendrogram dot dotchart dotchart_area dotmark dots editor foreground foreground_center fpall fpall_area fpci fpcumul fpes fpesinside fpesrefline fpgraph fpgrp fpgrp_area fphrule fpnullrefline fpspacer grid grid_foreground histogram hrule legend major_grid mat_label_box matrix_plotregion matrixmark medforeground minor_grid minortick none pie plotregbg plotregion refline refmarker reverse_big solid sunflower sunflowerdb sunflowerdf sunflowerlb sunflowerlf symbol text_option tick wide_background xyline yxline zyx2"
local L_tmpl "area arrow arrowline bar box boxmark dotmark line mark other solid"
local S_plain "ci ci2 histogram"
local S_tmpl "line bar area box dot arrow"
local M_plain "ci ci2 histogram none"
local M_tmpl "box dot arrow"
local A_plain "background ci ci2 foreground histogram none"
local A_tmpl "area bar box"

local all "economist meta s1color s1manual s1mono s1rcolor s2color s2color8 s2gcolor s2gmanual s2manual s2mono sj stcolor stcolor_alt stcolor_meta stcolor_mv stcoloralias stgcolor stgcolor_alt stgcolor_meta stgcolor_mv stmono1 stmono2 stsj sttrans"
local full "stcolor s2color s1mono s1rcolor"
local mine ""
local w = 0
foreach s of local all {
    local ++w
    if "`part'" == "" | mod(`w' - 1, 3) + 1 == real("0`part'") local mine "`mine' `s'"
}

* ---- N: the table names ----
foreach s of local mine {
    local nums "1 3 15"
    if `: list s in full' local nums "1 2 3 4 5 6 7 8 9 10 11 12 13 14 15"
    foreach c in L S M A {
        local names "``c'_plain'"
        foreach t of local `c'_tmpl {
            foreach k of local nums {
                local names "`names' p`k'`t'"
            }
        }
        if "`c'" == "L" _os_batch N `s' lstyle line 0 "`names'"
        if "`c'" == "S" _os_batch N `s' pstyle scatter 0 "`names'"
        if "`c'" == "M" _os_batch N `s' mstyle scatter 0 "`names'"
        if "`c'" == "A" _os_batch N `s' astyle area 0 "`names'"
    }
}

* ---- U: names twoway does not know (every scheme) ----
local u40 = "x" + 39 * "y"
foreach s of local mine {
    _os_batch U `s' pstyle scatter 1 "bogus P3 p16 p0 p03 Ci `u40' p16line p3other p3mark foreground"
    _os_batch U `s' mstyle scatter 1 "bogus P3 p16 p0 p03 Ci `u40' p16line p3other p3mark foreground p16box"
    _os_batch U `s' lstyle line 1 "bogus P3 p16 p0 p03 Ci `u40'"
    _os_batch U `s' astyle area 1 "bogus P3 p16 p0 p03 Ci `u40'"
}

if inlist("`part'", "", "1") {
    * ---- K: Stata-known names outside the table (stcolor) ----
    foreach p in pstyle:fpall pstyle:dendrogram mstyle:sunflower mstyle:star astyle:plotregion astyle:outline {
        gettoken o n : p, parse(":")
        local n = substr("`n'", 2, .)
        local t = cond("`o'" == "astyle", "area", "scatter")
        _os_call "K|stcolor|`o'|`n'" stcolor 1 0 "K|stcolor|`o'|`n'" `"(`t' mpg weight in 1/2, `o'(`n')), legend(off)"'
    }

    * ---- C: the ci fits (stcolor, s2color); plot 1 the band, 2 the line ----
    foreach s in stcolor s2color {
        foreach f in lfitci lpolyci qfitci {
            foreach n in histogram p3bar p3line ci2 bogus {
                _os_call "C|`s'|`f'|`n'" `s' 2 0 "C|`s'|`f'|`n'|band C|`s'|`f'|`n'|line" `"(`f' mpg weight, pstyle(`n')), legend(off)"'
            }
        }
    }

    * ---- T: pstyle(ci)/ci2 on each type (stcolor, s2color) ----
    local T_scatter   "mpg weight in 1/10"
    local T_line      "mpg weight in 1/10, sort"
    local T_connected "mpg weight in 1/10, sort"
    local T_area      "mpg weight in 1/10, sort"
    local T_bar       "mpg weight in 1/10,"
    local T_rarea     "mpg turn weight in 1/10, sort"
    local T_spike     "mpg weight in 1/10,"
    local T_rcap      "mpg turn weight in 1/10,"
    local T_dropline  "mpg weight in 1/10,"
    foreach s in stcolor s2color {
        foreach t in scatter line connected area bar rarea spike rcap dropline {
            foreach n in ci ci2 {
                local a "`T_`t''"
                if strpos("`a'", ",") == 0 local a "`a',"
                _os_call "T|`s'|`t'|`n'" `s' 1 0 "T|`s'|`t'|`n'" `"(`t' `a' pstyle(`n')), legend(off)"'
            }
        }
    }

    * ---- Q: note counts (stcolor) ----
    _os_call "Q|stcolor|q1" stcolor 0 0 "" `"(line mpg weight, lstyle(bogus)) (line price weight, lstyle(bogus)), legend(off)"'
    _os_call "Q|stcolor|q2" stcolor 0 0 "" `"scatter mpg weight, lstyle(bogus) mstyle(bogus) legend(off)"'
    _os_call "Q|stcolor|q3" stcolor 0 0 "" `"(scatter mpg weight, lstyle(bogus)) (scatter price weight, lstyle(bogus)), legend(off)"'

    * ---- D: declared, not drawn (stcolor) ----
    local i = 0
    foreach c in "scatter mpg weight, dstyle(p3)" "scatter mpg weight, dst(p3)" ///
        "scatter mpg weight, dlstyle(p3)" "scatter mpg weight, dl(p3)" ///
        "scatter mpg weight, dls(p3)" ///
        "pcbarrow mpg weight price length in 1/5, bmlinestyle(p3)" ///
        "pcbarrow mpg weight price length in 1/5, bml(p3)" ///
        "scatter mpg weight, dstyle(bogus)" "scatter mpg weight, dlstyle(bogus)" ///
        "scatter mpg weight, bmlinestyle(bogus)" ///
        "scatter mpg turn weight, dstyle(p3 p4)" "scatter mpg weight, bm(p3)" {
        local ++i
        local id = "D|stcolor|d" + string(`i', "%02.0f")
        _os_call "`id'" stcolor 0 0 "" `"`c' legend(off)"'
    }

    * ---- H: hostile names (stcolor), numbered ----
    local i = 0
    local h200 = 200 * "z"
    foreach n in "../x" "{bf:x}" "p3;x" `""refline""' "REFLINE" "x.y" "3" "`h200'" {
        local ++i
        foreach p in lstyle:line pstyle:scatter {
            gettoken o t : p, parse(":")
            local t = substr("`t'", 2, .)
            _os_call "H|stcolor|`o'|h`i'" stcolor 1 0 "H|stcolor|`o'|h`i'" `"(`t' mpg weight in 1/2, `o'(`n')), legend(off)"'
            mata: st_global("OS_NAME_" + st_global("OS_SEQ"), st_local("n"))
        }
    }

    * ---- S: SVG of the none forms (stcolor) ----
    foreach p in lstyle:line:none mstyle:scatter:none astyle:area:none astyle:area:bogus lstyle:line:refline {
        tokenize "`p'", parse(":")
        _os_call "S|stcolor|`1'|`5'" stcolor 1 1 "S|stcolor|`1'|`5'" `"(`3' mpg weight in 1/10, sort `1'(`5')), legend(off)"'
    }
}

file close `rf'
global OS_RF
timer off 36
quietly timer list 36
local seconds = r(t36)

python:
import json, os, re, sys
from sfi import Macro
repo = Macro.getLocal("repo")
part = Macro.getLocal("part")
sys.path.insert(0, os.path.join(repo, "scripts"))
import svg_truth

_EL = re.compile(r"<(circle|path|polygon|line|rect|polyline|ellipse|use)\b([^>]*)>")


def _svg(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        txt = fh.read()
    strokes, fills = {}, {}
    for m in _EL.finditer(txt):
        a = svg_truth._attrs(m.group(2))
        st = svg_truth._style_of(a)
        for prop, out in (("stroke", strokes), ("fill", fills)):
            v = st.get(prop, a.get(prop))
            v = v.lower() if isinstance(v, str) else v
            if v and v != "none" and v.startswith("#"):
                out[v] = out.get(v, 0) + 1
    return {"strokes": sorted([k, n] for k, n in strokes.items()),
            "fills": sorted([k, n] for k, n in fills.items())}


def _notes(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return [" ".join(ln.split()) for ln in fh
                if ln.strip().startswith("(note:")]


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
        "label_color": _hex(g("labc")),
    }


records, notes, svg, cmds = {}, {}, {}, {}
schemes = set()
with open(Macro.getLocal("records"), encoding="utf-8") as fh:
    for ln in fh:
        parts = ln.rstrip("\n").split("|")
        # callid has 4 |-fields (GRID|SCHEME|OPT|NAME) or 3 (Q, D); the
        # record id likewise, or "-": parse from the right.
        rec = parts[-1]
        log = parts[-2]
        svgf = parts[-3]
        rc = int(parts[-4])
        k = int(parts[-5])
        head = parts[:-5]
        n_call = 3 if head[0] in ("Q", "D") else 4
        callid = "|".join(head[:n_call])
        seq = head[n_call]
        rid = "|".join(head[n_call + 1:])
        schemes.add(head[1])
        cmds[callid] = Macro.getGlobal("OS_CMD_" + seq)
        notes[callid] = _notes(log)
        if svgf:
            svg[callid] = _svg(svgf)
            os.remove(svgf)
        if rid and rid != "-":
            r = {"rc": rc, "plot": k, "call": callid}
            if rec:
                r.update(_roles(rec))
            nm = Macro.getGlobal("OS_NAME_" + seq)
            if nm:
                r["name"] = nm
            records[rid] = r
for fn in os.listdir(os.getcwd()):
    if re.fullmatch(r"os_\d+\.log", fn):
        os.remove(fn)
meta = {"stata_version": Macro.getLocal("stata_version"),
        "born_date": Macro.getLocal("born_date"),
        "dash_commit": Macro.getLocal("dash_commit"),
        "extracted": Macro.getLocal("extracted"),
        "source": "scripts/extract_style_name_truth.do",
        "seconds": round(float(Macro.getLocal("seconds") or 0), 1)}
out = {"_meta": meta, "schemes": sorted(schemes), "records": records,
       "notes": notes, "svg": svg, "cmds": cmds}
if part:
    dst = os.path.join(os.getcwd(), "os_part.json")
else:
    dst = os.path.join(repo, "test", "fixtures", "style_name_truth.json")
with open(dst, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2, sort_keys=True)
    fh.write("\n")
print("style_name_truth: wrote %d records in %s s" % (len(records), meta["seconds"]))
end

set scheme `entry_scheme'
