* extract_refline_truth.do -- twoway's reference lines (WP-30 P1.21a,
* section 39), written to test/fixtures/refline_truth.json for
* test/test_reference_lines.py and the S39 block of
* test/test_wp30_truth.cscript.
*
* Probes, all `twoway scatter mpg weight, <opt>' on sysuse auto:
*   P  positions (s2color, SVG): each reference line's data position,
*      stroke, width and whether it is dashed;
*   R  refusals (nodraw): rc and the first error line;
*   S  lstyle()/lcolor() (SVG, under s2color, stcolor and s1mono):
*      stroke, width over the default xline's width, dashed, present,
*      notes; L lalign() likewise;
*   O  the order of a line between the grid and the markers;
*   B  by(foreign) xline(3000): lines per panel.
* A reference line is told from the grid by its place: the lines drawn
* before the first marker, after as many as the same command draws
* without the option (its baseline).
*
* Run (never the GUI; the slot wrapper of scripts/stata_slot.sh):
*   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_refline_truth.do
* The SVG and log files are written to the current directory.

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_rt_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_rt_bad' {
    display as error "extract_refline_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _rt_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_rt_rc' | _rc {
    local _rt_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_refline_truth.do: `_rt_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1

clear all
set more off
set linesize 255
version 19
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

tempfile records
tempname rf
file open `rf' using "`records'", write text replace
global RT_RF `rf'

capture program drop _rt_case
program _rt_case
    // _rt_case id scheme svg opt: run twoway scatter mpg weight, opt under
    // scheme, logging it; with svg 1 export it; append id|scheme|rc|svg|log.
    args id scheme svg opt
    quietly sysuse auto, clear
    set scheme `scheme'
    local log "`c(pwd)'/rt_`id'.log"
    local out ""
    capture graph drop g
    local nd = cond(`svg', "", "nodraw")
    quietly log using "`log'", text replace name(rtruth)
    capture noisily twoway scatter mpg weight, `macval(opt)' name(g, replace) `nd'
    local rc = _rc
    quietly log close rtruth
    if !`rc' & `svg' {
        local out "`c(pwd)'/rt_`id'.svg"
        quietly graph export "`out'", replace name(g)
    }
    file write $RT_RF "`id'|`scheme'|`rc'|`out'|`log'" _n
    mata: st_global("RT_OPT_`id'", st_local("opt"))
end

* Baselines: no reference line, and the default xline, per scheme.
foreach s in s2color stcolor s1mono {
    _rt_case Z0_`s' `s' 1 `"ylabel(, grid)"'
    _rt_case Z1_`s' `s' 1 `"ylabel(, grid) xline(3000)"'
}
local P1 "ylabel(, grid)"
_rt_case P01 s2color 1 `"`P1' xline(2000(500)3000)"'
_rt_case P02 s2color 1 `"`P1' xline(2000[500]3000)"'
_rt_case P03 s2color 1 `"`P1' xline(2000 (500) 3000)"'
_rt_case P04 s2color 1 `"`P1' xline(2000/2002)"'
_rt_case P05 s2color 1 `"`P1' xline(2000 2500 to 3500)"'
_rt_case P06 s2color 1 `"`P1' xline(2000 2500:3500)"'
_rt_case P07 s2color 1 `"`P1' xline(3500(-500)2000)"'
_rt_case P08 s2color 1 `"`P1' xline(2000(250.5)3000)"'
_rt_case P09 s2color 1 `"`P1' xline(2e3 3e3)"'
_rt_case P10 s2color 1 `"`P1' xline(+2000 -1)"'
_rt_case P11 s2color 1 `"`P1' xline(3000 3000)"'
_rt_case P12 s2color 1 `"`P1' yline(20, lcolor(red)) yline(10(5)40, lcolor(blue))"'
_rt_case P13 s2color 1 `"`P1' xline(2000(500)3000, lcolor(red)) xline(4000)"'
_rt_case P14 s2color 1 `"`P1' yline(10(5)40)"'
_rt_case P15 s2color 1 `"`P1' xline(1(1)2500) xline(2501(1)5000)"'

local i 0
foreach o in `"xline(, foo)"' `"xline(,)"' `"xline(abc, foo)"'          ///
    `"xline(3000, foo bar(1))"' `"xline(abc, lstyle(p1) lstyle(p2))"'  ///
    `"xline(1(1)2501)"' `"xline(3000 nan)"' `"xline(1_000)"'            ///
    `"xline(abc) yline(def)"' `"yline(def) xline(abc)"'                 ///
    `"xline(3000, lcolor(red)) xline(abc)"' `"xline(3000, LColor(red))"' ///
    `"xline(3000, lalign(inside) la(outside))"' `"xline(3000, ex ex)"'  ///
    `"xline(3000, st(unextended) style(default))"'                      ///
    `"xline(3000, ax(1) axis(1))"' `"xline(3000,, lcolor(red))"'        ///
    `"xline(3000, axis(2))"' `"xline(1(0)5)"' `"xline(.)"'              ///
    `"xline(. 3000)"' `"xline(1e400)"' `"xline(2000 3000 to)"'          ///
    `"xline(2000,3000)"' `"xline(3000, s(unextended))"'                 ///
    `"xline(3000, noe)"' `"xline(3000, ls(p1))"' `"xline(3000, l(red))"' ///
    `"xline(3000, NOEXTEND)"' `"xline(3000, extend extend)"'            ///
    `"xline(3000, ex extend)"' `"xline(3000, noex noextend)"'           ///
    `"xline(3000, noextend noextend)"' `"xline()"' `"xline(3000,)"'      ///
    `"xline(3000, st(default) lst(p1) lc(red) lw(thick) lp(dash) la(inside) ax(1) noex)"' ///
    `"xline(3000, ex)"' `"xline(3000, lpattern(bogus))"' {
    local ++i
    local id = "R" + string(`i', "%02.0f")
    _rt_case `id' s2color 0 `"`o'"'
}

foreach s in s2color stcolor s1mono {
    local i 0
    foreach o in `"lstyle(p1)"' `"lstyle(p3)"' `"lstyle(p1line)"'       ///
        `"lstyle(refline)"' `"lstyle(xyline)"' `"lstyle(ci)"'           ///
        `"lstyle(foreground)"' `"lstyle(grid)"' `"lstyle(none)"'        ///
        `"lstyle(p16)"' `"lstyle(P1)"' `"lstyle(nosuch)"'               ///
        `"lstyle(foreground) lcolor(red)"' `"lcolor(red) lstyle(foreground)"' ///
        `"lstyle(p1) lpattern(dash)"' `"lstyle(none) lcolor(red)"' {
        local ++i
        local id = "S" + string(`i', "%02.0f") + "_`s'"
        _rt_case `id' `s' 1 `"ylabel(, grid) xline(3000, `o')"'
    }
}
local i 0
foreach v in inside outside center nosuch {
    local ++i
    _rt_case L0`i' s2color 1 `"ylabel(, grid) xline(3000, lwidth(vthick) lalign(`v'))"'
}
_rt_case L00 s2color 1 `"ylabel(, grid) xline(3000, lwidth(vthick))"'
_rt_case O01 s2color 1 `"ylabel(, grid) xline(3000)"'
_rt_case B01 s2color 1 `"by(foreign) xline(3000)"'

file close `rf'
global RT_RF

python:
import json, os, re, sys
from sfi import Macro
repo = Macro.getLocal("repo")
sys.path.insert(0, os.path.join(repo, "scripts"))
import svg_truth

_EL = re.compile(r"<(line|circle|rect|path|polygon|text)\b([^>]*)>")


def _log(path):
    """The first error line and every note of a probe's log."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = [ln.rstrip("\n").replace(" ", " ") for ln in fh]
    first, notes, cur = "", [], None
    for ln in lines:
        s = ln.strip()
        if cur is not None:
            if s and not s.startswith(".") and not s.startswith("(note"):
                cur += " " + s
                continue
            notes.append(cur)
            cur = None
        if s.startswith("(note:"):
            cur = s
            continue
        if (not s or re.match(r"^r\(\d+\);$", s) or s.startswith(".")
                or s.startswith(">") or s.startswith("name:")
                or s.startswith("log:") or s.startswith("log type:")
                or s.startswith("opened on:") or s.startswith("closed on:")
                or s.startswith("---")):
            continue
        if not first:
            first = s
    if cur is not None:
        notes.append(cur)
    return first, [re.sub(r"\s+", " ", n) for n in notes]


def _style(a):
    m = re.search(r'style="([^"]*)"', a)
    out = {}
    for part in (m.group(1) if m else "").split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def _f(a, k):
    m = re.search(k + r'="([-0-9.]+)"', a)
    return float(m.group(1)) if m else None


def _pre_marker_lines(svg):
    """The <line> elements before the first marker, in document order."""
    with open(svg, encoding="utf-8", errors="replace") as fh:
        txt = fh.read()
    out = []
    for m in _EL.finditer(txt):
        if m.group(1) == "circle":
            break
        if m.group(1) != "line":
            continue
        a = m.group(2)
        st = _style(a)
        out.append({"x1": _f(a, "x1"), "y1": _f(a, "y1"), "x2": _f(a, "x2"),
                    "y2": _f(a, "y2"),
                    "stroke": st.get("stroke", "").lower(),
                    "width": float(st.get("stroke-width", "nan"))})
    return out


def _groups(lines):
    """One entry per drawn line: dashed lines are several segments."""
    g = {}
    for d in lines:
        vert = abs(d["x1"] - d["x2"]) < 0.01
        key = ("v" if vert else "h", round(d["x1"] if vert else d["y1"], 2),
               d["stroke"], d["width"])
        g.setdefault(key, []).append(d)
    return [{"dim": k[0], "px": k[1], "stroke": k[2], "width": k[3],
             "dashed": len(v) > 1} for k, v in g.items()]


def _value(fit, px, edge):
    return fit["low"] + (px - edge) * fit["units_per_px"] if not fit["reversed"] else fit["high"] + (px - edge) * fit["units_per_px"]


recs = []
with open(Macro.getLocal("records"), encoding="utf-8") as fh:
    for ln in fh:
        recs.append(ln.rstrip("\n").split("|"))
base = {}
for cid, scheme, rc, svg, log in recs:
    if cid.startswith("Z0_") and svg:
        base[scheme] = len(_pre_marker_lines(svg))
probes = {}
for cid, scheme, rc, svg, log in recs:
    first, notes = _log(log)
    rec = {"opt": Macro.getGlobal("RT_OPT_" + cid), "scheme": scheme,
           "rc": int(rc), "message": first, "notes": notes}
    if svg and not cid.startswith("Z0_"):
        pre = _pre_marker_lines(svg)
        nb = base[scheme]
        if cid == "B01":
            # Every panel draws the line: count the vertical lines of the
            # xyline colour before the markers of each panel.
            with open(svg, encoding="utf-8", errors="replace") as fh:
                txt = fh.read()
            n = sum(1 for m in _EL.finditer(txt) if m.group(1) == "line"
                    and abs((_f(m.group(2), "x1") or 0) - (_f(m.group(2), "x2") or 1)) < 0.01
                    and _style(m.group(2)).get("stroke", "").lower() == "#c10534")
            rec["lines"] = n
        else:
            refl = _groups(pre[nb:])
            if cid == "O01":
                rec["above_grid"] = nb > 0 and len(pre) > nb
                rec["below_markers"] = len(pre) > nb
            if cid == "P15":
                rec["lines"] = len(refl)
            else:
                doc = svg_truth.svg_document(svg)
                pr = doc["plotregion"]
                fx = svg_truth.svg_axis_reading(svg, "x", doc=doc)["fit"]
                fy = svg_truth.svg_axis_reading(svg, "y", doc=doc)["fit"]
                lines = []
                for g in sorted(refl, key=lambda g: (g["dim"], g["px"])):
                    if g["dim"] == "v":
                        pos = fx["low"] + (g["px"] - pr["left"]) * fx["units_per_px"]
                    else:
                        pos = fy["low"] + (g["px"] - pr["bottom"]) * fy["units_per_px"]
                    lines.append({"axis": "x" if g["dim"] == "v" else "y",
                                  "pos": round(pos, 1), "stroke": g["stroke"],
                                  "width": g["width"], "dashed": g["dashed"]})
                rec["lines"] = lines
    probes[cid] = rec
meta = {"stata_version": Macro.getLocal("stata_version"),
        "born_date": Macro.getLocal("born_date"),
        "source": "scripts/extract_refline_truth.do",
        "dash_commit": Macro.getLocal("dash_commit"),
        "extracted": Macro.getLocal("extracted")}
out = os.path.join(repo, "test", "fixtures", "refline_truth.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump({"probes": probes, "_meta": meta}, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote " + out)
end

set scheme `entry_scheme'
