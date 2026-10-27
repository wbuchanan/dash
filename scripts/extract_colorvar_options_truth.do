*! extract_colorvar_options_truth.do -- WP-31 section 17 (GAPS3 C8b):
*! measure how twoway draws the colorvar options colorrule() colorstart()
*! colorend() colorlist() colorfillonly colorformissing() colorkeysrange
*! colorkeysreverse colorallowmultiple colorotherlabel() coloruseplegend,
*! colorvar(i.var), and the graph options clegend() plegend() pcycle().
*! twoway only: the output is the same before and after dash changes.
*!
*! Output: test/fixtures/colorvar_options_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_colorvar_options_truth.do
*!
*! PROBES (sysuse auto, scheme s2color unless named; the key's swatch
*! colours are read from the exported SVG in document order: the colour
*! key draws the highest level first, the plot legend its own order)
*!   D*      `twoway scatter mpg weight, colorvar(...) <options>': rc, the
*!           key's swatch fills (and fill opacities), its swatch kind
*!           (marker or bar), its texts, and the outline colours of the
*!           plotted markers.  D14*: colorkeysreverse on a key that is
*!           not discrete (WP-31 C8e, section 26).
*!   S_<s>   every scheme dash ships: the default rule's colours for
*!           colorlevels(2) (the rule's two ends) and for colordiscrete
*!           on rep78 (five levels), and the scheme file's own
*!           zyx2rule contour, color contour_begin and color contour_end.
*!   R*      refusals: rc and the lines twoway prints.
*!   G*      clegend() and plegend(): the key's place and whether drawn.
*!   P*      pcycle(): the marker colours of three series, and refusals.
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zo_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zo_bad' {
    display as error "extract_colorvar_options_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zo_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zo_rc' | _rc {
    local _zo_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_colorvar_options_truth.do: `_zo_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZO_REPO "`repo'"
global ZO_OUT "${ZO_REPO}/test/fixtures/colorvar_options_truth.json"

local work "`c(tmpdir)'dash_colorvar_options_probe"
capture mkdir "`work'"
global ZO_WORK "`work'"


quietly shell git -C "${ZO_REPO}" rev-parse HEAD > "${ZO_WORK}/git_head.txt"
global ZO_VERSION "`c(stata_version)'"
global ZO_BORN "`c(born_date)'"
global ZO_WHEN "`c(current_date)' `c(current_time)'"

* _zo_run key cmd: run `cmd' with its printed lines in a log; the rc in
* ZO_RC_<key>; the graph exported to <key>.svg when it drew.
capture program drop _zo_run
program define _zo_run
    gettoken key 0 : 0
    quietly log using "${ZO_WORK}/`key'.log", text replace name(zoref)
    capture noisily `0'
    local rc = _rc
    * A {p} paragraph twoway leaves open is written when the next line is.
    display as text "{p_end}"
    quietly log close zoref
    global ZO_RC_`key' "`rc'"
    if `rc' == 0 {
        capture graph describe zo1
        if _rc == 0 {
            quietly graph export "${ZO_WORK}/`key'.svg", replace
            graph drop zo1
        }
    }
    global ZO_KEYS "${ZO_KEYS} `key'"
end
global ZO_KEYS ""

sysuse auto, clear
set scheme s2color
local sc "twoway scatter mpg weight"
local nm "name(zo1, replace)"

_zo_run D01  `sc', colorvar(rep78) colordiscrete `nm'
_zo_run D01n `sc' if rep78 < ., colorvar(rep78) colordiscrete `nm'
_zo_run D01f `sc', colorvar(foreign) colordiscrete `nm'
_zo_run D01c `sc', colorvar(rep78) `nm'
_zo_run D02a `sc', colorvar(rep78) colorlevels(3) `nm'
_zo_run D02b `sc', colorvar(rep78) colorlevels(8) `nm'
_zo_run D02c `sc', colorvar(rep78) colorcuts(2 3 4) `nm'
_zo_run D03  `sc', colorvar(rep78) colordiscrete colorlist(red blue) `nm'
_zo_run D03b `sc', colorvar(rep78) colordiscrete colorlist(red blue green orange navy) `nm'
_zo_run D04  `sc', colorvar(rep78) colordiscrete colorrule(linear) colorstart(white) colorend(navy) `nm'
_zo_run D04b `sc', colorvar(rep78) colordiscrete colorrule(linear) colorend(navy) `nm'
_zo_run D04c `sc', colorvar(rep78) colorlevels(4) colorrule(linear) colorstart(red) colorend(blue) `nm'
_zo_run D04d `sc', colorvar(rep78) colordiscrete colorrule(revlinear) colorstart(white) colorend(navy) `nm'
_zo_run D04e `sc', colorvar(rep78) colordiscrete colorrule(Hue) `nm'
_zo_run D05  `sc', colorvar(rep78) colordiscrete colorcuts(3 4) colorotherlabel(rest) `nm'
_zo_run D05p `sc', colorvar(rep78) colordiscrete coloruseplegend colorcuts(3 4) colorotherlabel(rest) `nm'
_zo_run D05m `sc', colorvar(rep78) colordiscrete colorcuts(3 4) colorformissing(red) `nm'
_zo_run D06  `sc', colorvar(rep78) colordiscrete colorrule(intensity) colorend(navy) `nm'
_zo_run D06b `sc', colorvar(rep78) colorlevels(4) colorrule(intensity) `nm'
_zo_run D06c `sc', colorvar(rep78) colordiscrete colorrule(intensity) colorstart(red) colorend(navy) `nm'
_zo_run D07  `sc', colorvar(rep78) colordiscrete colorrule(phue) `nm'
_zo_run D07b `sc', colorvar(rep78) colordiscrete colorrule(phue *0.5) `nm'
_zo_run D08  `sc', colorvar(rep78) colordiscrete colorrule(chue) colorstart(blue) colorend(red) `nm'
_zo_run D08b `sc', colorvar(rep78) colordiscrete colorrule(chue) colorstart(red) colorend(blue) `nm'
_zo_run D08c `sc', colorvar(rep78) colordiscrete colorrule(chue) colorstart(blue) colorend(blue) `nm'
_zo_run D08d `sc', colorvar(rep78) colordiscrete colorrule(hue) colorstart(green) colorend(blue) `nm'
_zo_run D08e `sc', colorvar(rep78) colordiscrete colorrule(hue) colorstart(gs8) colorend(navy) `nm'
_zo_run D08f `sc', colorvar(rep78) colordiscrete colorrule(hue) colorstart(blue) colorend(blue) `nm'
_zo_run D09  `sc', colorvar(rep78) colordiscrete colorrule(hue %50 *1.5) `nm'
_zo_run D09b `sc', colorvar(rep78) colordiscrete colorrule(hue *0.5) `nm'
_zo_run D09c `sc', colorvar(rep78) colordiscrete colorrule(linear %30) colorstart(white) colorend(navy) `nm'
_zo_run D10  `sc', colorvar(rep78) colordiscrete colorfillonly `nm'
_zo_run D11  `sc', colorvar(rep78) colorlevels(4) colorkeysrange `nm'
_zo_run D11b `sc', colorvar(rep78) colorlevels(4) `nm'
* WP-31 C8e (section 26): colorkeysreverse on a colour key that is not
* discrete -- unbinned, binned by colorlevels(), and with colorkeysrange.
_zo_run D14  `sc', colorvar(price) `nm'
_zo_run D14r `sc', colorvar(price) colorkeysreverse `nm'
_zo_run D14br `sc', colorvar(rep78) colorlevels(4) colorkeysreverse `nm'
_zo_run D14kr `sc', colorvar(rep78) colorlevels(4) colorkeysrange colorkeysreverse `nm'
_zo_run D12  `sc', colorvar(rep78) colordiscrete colorkeysreverse `nm'
_zo_run D13  `sc', colorvar(i.rep78) `nm'
_zo_run D13b `sc', colorvar(rep78) colordiscrete coloruseplegend `nm'
_zo_run D13r `sc' if rep78 < ., colorvar(rep78) colordiscrete coloruseplegend colorkeysreverse `nm'

_zo_run R01  `sc', colorvar(rep78) coloruseplegend
_zo_run R02  `sc', colorvar(rep78) colorrule(bogus)
_zo_run R02b `sc', colorvar(rep78) colorrule(hue foo)
_zo_run R02c `sc', colorvar(rep78) colorrule(hue %50 *x)
_zo_run R03  twoway scatter mpg weight, colorvar(rep78) || scatter price weight, colorvar(rep78)
_zo_run R03b twoway scatter mpg weight, colorvar(rep78) || scatter price weight, colorvar(rep78) colorallowmultiple `nm'
_zo_run R03c twoway scatter mpg weight, colorvar(rep78) colorallowmultiple || scatter price weight, colorvar(rep78)
_zo_run R04  `sc', colorvar(rep78) colormissing(red)
_zo_run R04b `sc', colorvar(rep78) colorformissing(red) `nm'
_zo_run R05  `sc', colorvar(rep78) colorrule(hue) colorrule(linear)
_zo_run R05b `sc', colorvar(rep78) colorstart(red) colorstart(blue)

_zo_run G01  `sc', colorvar(rep78) clegend(position(6) ring(1) width(5) height(20) title("Z")) `nm'
_zo_run G01d `sc', colorvar(rep78) `nm'
_zo_run G02  `sc', colorvar(rep78) colordiscrete coloruseplegend plegend(off) `nm'
_zo_run G03  `sc', colorvar(rep78) clegend(off) `nm'

local p3 "twoway scatter mpg trunk turn weight"
_zo_run P00  `p3', `nm'
_zo_run P01  `p3', pcycle(2) `nm'
_zo_run P01b `p3', pcycle(1) `nm'
_zo_run P01c `p3', pcycle(16) `nm'
_zo_run P02a `p3', pcycle(0)
_zo_run P02b `p3', pcycle(-1)
_zo_run P02c `p3', pcycle(2) pcycle(3)
_zo_run P02d `p3', pcycle(1.5)
_zo_run P02e `p3', pcycle(abc)
_zo_run P02f twoway scatter mpg weight, pcycle(1.5) `nm'

* S_<scheme>: the default rule of each scheme dash ships.
local schemes "economist meta s1color s1manual s1mono s1rcolor s2color s2color8 s2gcolor s2gmanual s2manual s2mono sj stcolor stcolor_alt stcolor_meta stcolor_mv stcoloralias stgcolor stgcolor_alt stgcolor_meta stgcolor_mv stmono1 stmono2 stsj sttrans"
global ZO_SCHEMES ""
foreach s of local schemes {
    capture findfile scheme-`s'.scheme
    global ZO_SFILE_`s' "`r(fn)'"
    _zo_run S2_`s' `sc', colorvar(rep78) colorlevels(2) scheme(`s') `nm'
    _zo_run S5_`s' `sc', colorvar(rep78) colordiscrete scheme(`s') `nm'
    global ZO_SCHEMES "${ZO_SCHEMES} `s'"
}

python:
import json, os, re
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


work = G("ZO_WORK")
_ATTR = re.compile(r'([\w:-]+)="([^"]*)"')
_EL = re.compile(r"<(circle|rect|path|use|polygon)\b([^>]*)/?>")
_TEXT = re.compile(r'<text x="([\d.]+)" y="([\d.]+)"[^>]*>([^<]*)</text>')
_XT = "Weight (lbs.)</text>"


def style(a):
    out = {}
    for part in a.get("style", "").split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip()] = v.strip().lower()
    return out


def read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        txt = fh.read()
    os.remove(path)
    return txt


def log_lines(key):
    p = os.path.join(work, key + ".log")
    with open(p, encoding="utf-8", errors="replace") as fh:
        lines = [ln.rstrip() for ln in fh
                 if ln.strip() and not ln.lstrip().startswith((".", "> "))
                 and "log:" not in ln and "log type:" not in ln
                 and "opened on:" not in ln and "closed on:" not in ln
                 and "name:" not in ln and not ln.startswith("---")
                 and ln.strip() != "{p_end}"]
    os.remove(p)
    return lines


def key_of(txt):
    """The key drawn after the x title: swatches in document order."""
    if _XT not in txt:
        return None
    head, tail = txt.split(_XT, 1)
    sw = []
    kind = None
    frame = None
    for m in _EL.finditer(tail):
        el, a = m.group(1), dict(_ATTR.findall(m.group(2)))
        st = style(a)
        f = st.get("fill")
        if not f or f == "none":
            continue
        if el == "rect":
            frame = f
            continue
        sw.append({"fill": f, "opacity": float(st["fill-opacity"])
                   if "fill-opacity" in st else None})
        kind = "bar" if el in ("use", "path") else "marker"
    texts = [s for _x, _y, s in _TEXT.findall(tail)]
    pos = [(float(x), float(y)) for x, y, _s in _TEXT.findall(tail)]
    return {"fills": [s["fill"] for s in sw],
            "opacities": [s["opacity"] for s in sw],
            "swatch": kind, "texts": texts, "frame": frame,
            "text_pos": pos}


def plot_strokes(txt):
    head = txt.split(_XT, 1)[0]
    out = set()
    for m in _EL.finditer(head):
        a = dict(_ATTR.findall(m.group(2)))
        st = style(a)
        if st.get("fill") == "none" and st.get("stroke") and m.group(1) == "circle":
            out.add(st["stroke"])
    return sorted(out)


def series_fills(txt):
    out = {}
    for m in _EL.finditer(txt):
        if m.group(1) != "circle":
            continue
        st = style(dict(_ATTR.findall(m.group(2))))
        f = st.get("fill")
        if f and f != "none":
            out[f] = out.get(f, 0) + 1
    return out


def scheme_rule(path):
    """zyx2rule contour (the last line wins), color contour_begin/end, and
    the #include chain, from a scheme file."""
    rec = {"rule": None, "begin": None, "end": None, "include": []}
    if not path or not os.path.exists(path):
        return rec
    with open(path, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            w = ln.split()
            if len(w) >= 3 and w[0] == "zyx2rule" and w[1] == "contour":
                rec["rule"] = w[2]
            elif len(w) >= 3 and w[0] == "color" and w[1] in ("contour_begin", "contour_end"):
                rec[w[1].split("_")[1]] = " ".join(w[2:])
            elif len(w) >= 2 and w[0] == "#include":
                rec["include"].append(w[1])
    return rec


out = {"probes": {}, "schemes": {}}
for key in G("ZO_KEYS").split():
    rec = {"rc": int(G("ZO_RC_" + key)), "lines": log_lines(key)}
    svg = os.path.join(work, key + ".svg")
    if os.path.exists(svg):
        txt = read(svg)
        rec["key"] = key_of(txt)
        rec["outline_strokes"] = plot_strokes(txt)
        rec["series_fills"] = series_fills(txt)
    if key.startswith(("S2_", "S5_")):
        s = key[3:]
        out["schemes"].setdefault(s, {})[key[:2]] = rec
    else:
        out["probes"][key] = rec
for s in G("ZO_SCHEMES").split():
    out["schemes"][s]["file"] = scheme_rule(G("ZO_SFILE_" + s))
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZO_VERSION"), "born_date": G("ZO_BORN"),
                "dash_commit": commit, "extracted": G("ZO_WHEN"),
                "source": "scripts/extract_colorvar_options_truth.do"}
with open(G("ZO_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZO_OUT"))
end
