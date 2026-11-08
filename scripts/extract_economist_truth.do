*! extract_economist_truth.do -- WP-45 section 45-01 (PIC-4, PIC-7/PIC-8):
*! what twoway draws under economist for the note() box and for the lines
*! of the range, spike, drop-line and paired-coordinate plots, read from
*! twoway's own SVG export.
*!
*!   N_note     sysuse auto; scatter mpg weight, title("T") note("The note")
*!              scheme(economist): the note's box (rect x y w h, fill), its
*!              text (x y size fill anchor), the title's text, the graph
*!              size;
*!   N_note_pr  the same with plotregion(fcolor(red)): the plot region's
*!              rect; N_title_pr the title alone, N_note_only_pr the note
*!              alone, N_none_pr neither (the band each draws);
*!   N_note_s2  the first graph under s2color;
*!   W_<type>   rspike rcap rcapsym rline rconnected rarea (lo hi weight),
*!              pcspike pccapsym pcarrow pcbarrow (lo weight hi w2), spike
*!              dropline (price weight), under economist, s2color and wt45
*!              (a scheme written here: #include s2color, linewidth pother
*!              vvthick, linewidth p1arrowline vthick, linewidth parea
*!              vthin), so each line's chain is told apart: every stroke
*!              in the plot's colours as [tag, width, count, clipped], the
*!              width in relative units (SVG width / (min(W, H) / 100)).
*!              A clipped stroke is twoway's inside-aligned outline: the
*!              SVG draws it twice as wide and clips half away.
*!
*! twoway only: the output is the same before and after dash changes.
*! Settings are session-only (scheme() on each command, the wt45 file in
*! the probe directory); nothing is set permanently, graph set is never
*! called.
*!
*! Output: test/fixtures/economist_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> sh <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_economist_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set graphics off
set more off
set linesize 200

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_ze_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_ze_bad' {
    display as error "extract_economist_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _ze_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_ze_rc' | _rc {
    local _ze_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_economist_truth.do: `_ze_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZE_REPO "`repo'"
global ZE_OUT "${ZE_REPO}/test/fixtures/economist_truth.json"

local work "`c(tmpdir)'dash_economist_probe"
capture mkdir "`work'"
global ZE_WORK "`work'"

quietly shell git -C "${ZE_REPO}" rev-parse HEAD > "${ZE_WORK}/git_head.txt"
global ZE_VERSION "`c(stata_version)'"
global ZE_BORN "`c(born_date)'"
global ZE_WHEN "`c(current_date)' `c(current_time)'"

* The user scheme (session only: a file in the probe directory).
tempname fh
file open `fh' using "${ZE_WORK}/scheme-wt45.scheme", write text replace
file write `fh' "#include s2color" _n
file write `fh' "linewidth pother vvthick" _n
file write `fh' "linewidth p1arrowline vthick" _n
file write `fh' "linewidth parea vthin" _n
file close `fh'
adopath ++ "${ZE_WORK}"

* The note.
sysuse auto, clear
twoway scatter mpg weight, title("T") note("The note") scheme(economist)
graph export "${ZE_WORK}/N_note.svg", replace
twoway scatter mpg weight, title("T") note("The note") scheme(economist) plotregion(fcolor(red))
graph export "${ZE_WORK}/N_note_pr.svg", replace
twoway scatter mpg weight, title("T") scheme(economist) plotregion(fcolor(red))
graph export "${ZE_WORK}/N_title_pr.svg", replace
twoway scatter mpg weight, note("The note") scheme(economist) plotregion(fcolor(red))
graph export "${ZE_WORK}/N_note_only_pr.svg", replace
twoway scatter mpg weight, scheme(economist) plotregion(fcolor(red))
graph export "${ZE_WORK}/N_none_pr.svg", replace
twoway scatter mpg weight, title("T") note("The note") scheme(s2color)
graph export "${ZE_WORK}/N_note_s2.svg", replace

* The widths.  _ze_col <k>: plot 1's line, area-line and marker-line
* colours (r g b) into global ZE_C_<k>.
capture program drop _ze_col
program define _ze_col
    args key
    local a "`.Graph.plotregion1.plot1.style.line.color.setting'"
    local b "`.Graph.plotregion1.plot1.style.area.linestyle.color.setting'"
    local c "`.Graph.plotregion1.plot1.style.marker.linestyle.color.setting'"
    global ZE_C_`key' "`a'|`b'|`c'"
end

generate lo = price - 1000
generate hi = price + 1000
generate w2 = weight + 100
global ZE_TYPES "rspike rcap rcapsym rline rconnected rarea pcspike pccapsym pcarrow pcbarrow spike dropline"
global ZE_SCHEMES "economist s2color wt45"
foreach s of global ZE_SCHEMES {
    foreach t of global ZE_TYPES {
        if inlist("`t'", "pcspike", "pccapsym", "pcarrow", "pcbarrow") {
            local cmd "`t' lo weight hi w2"
        }
        else if inlist("`t'", "spike", "dropline") {
            local cmd "`t' price weight"
        }
        else {
            local cmd "`t' lo hi weight"
        }
        twoway `cmd', scheme(`s')
        _ze_col `s'_`t'
        graph export "${ZE_WORK}/W_`s'_`t'.svg", replace
        graph drop _all
    }
}

python:
import json, os, re
from collections import Counter
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


work = G("ZE_WORK")


def read(name):
    with open(os.path.join(work, name + ".svg"), encoding="utf-8") as fh:
        return fh.read()


def size(svg):
    m = re.search(r'viewBox="0 0 ([0-9.]+) ([0-9.]+)"', svg)
    return float(m.group(1)), float(m.group(2))


def attrs(el):
    return dict(re.findall(r'([a-z:-]+)="([^"]*)"', el))


def style(a):
    return dict(p.split(":", 1) for p in a.get("style", "").split(";")
                if ":" in p)


def rects(svg, fill):
    out = []
    for el in re.findall(r"<rect [^>]*>", svg):
        a = attrs(el)
        if style(a).get("fill", "").upper() == fill.upper():
            out.append([float(a[k]) for k in ("x", "y", "width", "height")])
    return out


def texts(svg):
    out = []
    for el, body in re.findall(r"(<text [^>]*>)([^<]*)</text>", svg):
        a, st = attrs(el), style(attrs(el))
        out.append({"text": body, "x": float(a["x"]), "y": float(a["y"]),
                    "size": float(st["font-size"].rstrip("px")),
                    "fill": st.get("fill", "").lower(),
                    "anchor": a.get("text-anchor", "start")})
    return out


def note_case(name, plotregion=False):
    svg = read(name)
    w, h = size(svg)
    box = rects(svg, "#7B92A8")
    tx = texts(svg)
    case = {"graph": [w, h],
            "note_box": box[0] if box else None,
            "note_box_fill": "#7b92a8" if box else None,
            "note_text": next((t for t in tx if t["text"] == "The note"),
                              None),
            "title_text": next((t for t in tx if t["text"] == "T"), None)}
    if plotregion:
        pr = rects(svg, "#FF0000")
        case["plotregion"] = pr[0] if pr else None
    return case


note = {"N_note": note_case("N_note"),
        "N_note_pr": note_case("N_note_pr", True),
        "N_title_pr": note_case("N_title_pr", True),
        "N_note_only_pr": note_case("N_note_only_pr", True),
        "N_none_pr": note_case("N_none_pr", True),
        "N_note_s2": note_case("N_note_s2")}


def hexof(rgb):
    # "62 100 125 %100": r g b, then an opacity Stata appends.
    try:
        r, g, b = (int(v) for v in rgb.split()[:3])
    except ValueError:
        return None
    return "#%02x%02x%02x" % (r, g, b)


widths = {}
for s in G("ZE_SCHEMES").split():
    widths[s] = {}
    for t in G("ZE_TYPES").split():
        svg = read("W_%s_%s" % (s, t))
        w, h = size(svg)
        unit = min(w, h) / 100.0
        cols = {c for c in (hexof(v) for v in G("ZE_C_%s_%s" % (s, t))
                            .split("|")) if c}
        groups = Counter()
        for el in re.findall(r"<(?:line|path|use|circle|polygon|polyline)"
                             r" [^>]*>", svg):
            tag = el[1:].split(" ", 1)[0]
            st = style(attrs(el))
            col = st.get("stroke", "").lower()
            if col not in cols or "stroke-width" not in st:
                continue
            clipped = "clip-path" in el
            groups[(tag, round(float(st["stroke-width"]) / unit, 3),
                    clipped)] += 1
        widths[s][t] = {"colours": sorted(cols), "strokes": sorted(
            [tag, rs, n, cl] for (tag, rs, cl), n in groups.items())}

out = {"note": note, "widths": widths,
       "schemes": {"wt45": ("#include s2color\nlinewidth pother vvthick\n"
                            "linewidth p1arrowline vthick\n"
                            "linewidth parea vthin\n")},
       "_about": ("SVG user units, 720 per inch.  note: the box rect "
                  "[x, y, w, h] filled #7b92a8, the note and title texts, "
                  "the plot region rect where plotregion(fcolor(red)) was "
                  "drawn.  widths: twoway <type> lo hi weight (range), lo "
                  "weight hi w2 (pc), price weight (spike, dropline) on "
                  "sysuse auto; every stroke in plot 1's line, area-line "
                  "or marker-line colour as [tag, relative width, count, "
                  "clipped], relative = SVG width / (min(W, H) / 100); a "
                  "clipped stroke draws half its width (inside aligned).")}
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZE_VERSION"), "born_date": G("ZE_BORN"),
                "dash_commit": commit, "extracted": G("ZE_WHEN"),
                "source": "scripts/extract_economist_truth.do"}
with open(G("ZE_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
for f in os.listdir(work):
    if f.endswith(".svg") or f in ("git_head.txt", "scheme-wt45.scheme"):
        try:
            os.remove(os.path.join(work, f))
        except OSError:
            pass
print("wrote", G("ZE_OUT"))
end
