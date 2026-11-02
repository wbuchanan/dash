*! extract_colorvar_parts_truth.do -- WP-42 section 42-02 (CV-1, CV-6,
*! CV-7): measure how twoway paints a colorvar() layer's parts under
*! colorfillonly, which colour key and plot legend it draws for two
*! colorvar() layers, and the colour of a colorvar() layer's key in the
*! plot legend.  twoway only: the output is the same before and after dash
*! changes.
*!
*! Output: test/fixtures/colorvar_parts_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_colorvar_parts_truth.do
*!
*! PROBES (scheme s2color unless named)
*!   F_<type>  `twoway <type> ..., colorvar(z) colorfillonly' with z =
*!             rep78 (missing kept) over the auto data sorted by weight,
*!             t = _n, y = mpg, y2 = mpg + 5: rc and, inside the plot
*!             region, the sorted distinct colours of the <line> strokes
*!             (line_strokes; those with a round cap, head_strokes), of
*!             the markers' fills and outlines (marker_fills,
*!             marker_strokes), of the bars' fills and outlines (bar_fills,
*!             bar_strokes) and of the filled paths (path_fills,
*!             path_strokes).
*!   M1        `scatter mpg weight, colorvar(rep78) || scatter price
*!             weight, colorvar(foreign) colorallowmultiple'.
*!   M2        `scatter mpg weight, colorvar(rep78) colordiscrete
*!             coloruseplegend || scatter price weight'.
*!   M3        `contour depth northing easting || scatter northing
*!             easting, colorvar(depth) colorallowmultiple' (sandstone).
*!   K9        `scatter mpg weight, colorvar(rep78) || scatter price
*!             weight'; K9st the same under scheme stcolor.
*!   For M* and K*: rc, the texts right of the plot region (key_texts),
*!   the distinct fills drawn right of it (right_fills), the markers
*!   right of it, top to bottom (right_marker_fills), the texts below the
*!   plot region (below_texts) and the markers below it, left to right
*!   (legend_marker_fills).
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zp_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zp_bad' {
    display as error "extract_colorvar_parts_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zp_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zp_rc' | _rc {
    local _zp_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_colorvar_parts_truth.do: `_zp_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZP_REPO "`repo'"
global ZP_OUT "${ZP_REPO}/test/fixtures/colorvar_parts_truth.json"

local work "`c(tmpdir)'dash_colorvar_parts_probe"
capture mkdir "`work'"
global ZP_WORK "`work'"

quietly shell git -C "${ZP_REPO}" rev-parse HEAD > "${ZP_WORK}/git_head.txt"
global ZP_VERSION "`c(stata_version)'"
global ZP_BORN "`c(born_date)'"
global ZP_WHEN "`c(current_date)' `c(current_time)'"

* F_<type>: the types' data, rep78's missing rows kept.
sysuse auto, clear
sort weight
generate t = _n
generate y = mpg
generate y2 = mpg + 5
generate z = rep78
tempname dh
file open `dh' using "${ZP_WORK}/data_types.txt", write text replace
forvalues i = 1/`=_N' {
    file write `dh' (t[`i']) "|" (y[`i']) "|" (y2[`i']) "|" (z[`i']) _n
}
file close `dh'

local tt `"line "line y t" connected "connected y t" bar "bar y t" spike "spike y t" pcarrow "pcarrow y t y2 t" rcap "rcap y y2 t" rcapsym "rcapsym y y2 t" dropline "dropline y t" pcspike "pcspike y t y2 t" pccapsym "pccapsym y t y2 t" scatter "scatter y t""'
local fkeys ""
while `"`tt'"' != "" {
    gettoken ty tt : tt
    gettoken cmd tt : tt
    capture erase "${ZP_WORK}/f_`ty'.svg"
    capture noisily twoway `cmd', colorvar(z) colorfillonly scheme(s2color) name(c1, replace)
    global ZP_RC_F_`ty' = _rc
    global ZP_CMD_F_`ty' `"twoway `cmd', colorvar(z) colorfillonly"'
    if _rc == 0 {
        quietly graph export "${ZP_WORK}/f_`ty'.svg", replace
        graph drop c1
    }
    local fkeys "`fkeys' `ty'"
}
global ZP_FKEYS "`fkeys'"

* M1, M2, K9, K9st: the auto data.
sysuse auto, clear
local mkeys ""
foreach c in ///
    "M1|s2color|scatter mpg weight, colorvar(rep78) || scatter price weight, colorvar(foreign) colorallowmultiple scheme(s2color)" ///
    "M2|s2color|scatter mpg weight, colorvar(rep78) colordiscrete coloruseplegend || scatter price weight, scheme(s2color)" ///
    "K9|s2color|scatter mpg weight, colorvar(rep78) || scatter price weight, scheme(s2color)" ///
    "K9st|stcolor|scatter mpg weight, colorvar(rep78) || scatter price weight, scheme(stcolor)" {
    gettoken key rest : c, parse("|")
    local rest = substr(`"`rest'"', 2, .)
    gettoken s cmd : rest, parse("|")
    local cmd = substr(`"`cmd'"', 2, .)
    capture erase "${ZP_WORK}/m_`key'.svg"
    capture noisily twoway `cmd' name(c1, replace)
    global ZP_RC_`key' = _rc
    global ZP_CMD_`key' `"twoway `cmd'"'
    if _rc == 0 {
        quietly graph export "${ZP_WORK}/m_`key'.svg", replace
        graph drop c1
    }
    local mkeys "`mkeys' `key'"
}

* M3: sandstone.
sysuse sandstone, clear
capture erase "${ZP_WORK}/m_M3.svg"
capture noisily twoway contour depth northing easting || scatter northing easting, colorvar(depth) colorallowmultiple scheme(s2color) name(c1, replace)
global ZP_RC_M3 = _rc
global ZP_CMD_M3 "twoway contour depth northing easting || scatter northing easting, colorvar(depth) colorallowmultiple scheme(s2color)"
if _rc == 0 {
    quietly graph export "${ZP_WORK}/m_M3.svg", replace
    graph drop c1
}
local mkeys "`mkeys' M3"
global ZP_MKEYS "`mkeys'"

python:
import json, os, re, sys
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


work = G("ZP_WORK")
sys.path.insert(0, os.path.join(G("ZP_REPO"), "scripts"))
from svg_truth import svg_document  # noqa: E402

_NUM = re.compile(r"-?\d+(?:\.\d+)?")
_LINE = re.compile(r"<line\b([^>]*)/?>")
_ATTR = re.compile(r'([\w:-]+)="([^"]*)"')
# The s2color and stcolor chrome: canvas, regions, axes, grid.
_CHROME = {"#eaf2f3", "#ffffff", "#000000", "#dce7eb", "#f0f0f0",
           "#d9d9d9", "#e8e8e8"}


def read_doc(path):
    if not os.path.exists(path):
        return None, ""
    with open(path, encoding="utf-8", errors="replace") as fh:
        txt = fh.read()
    doc = svg_document(path)
    os.remove(path)
    return doc, txt


def inside(pr, x, y):
    return (pr is not None and x is not None and y is not None
            and pr["left"] <= x <= pr["right"]
            and pr["top"] <= y <= pr["bottom"])


def path_xy(e):
    n = [float(v) for v in _NUM.findall(e.get("d") or "")]
    return (n[0], n[1]) if len(n) >= 2 else (None, None)


def colour(c):
    return c if c and c.startswith("#") and c not in _CHROME else None


def distinct(vals):
    return sorted({v for v in vals if v})


def round_lines(txt, pr):
    out = []
    for m in _LINE.finditer(txt):
        a = dict(_ATTR.findall(m.group(1)))
        if a.get("stroke-linecap") != "round":
            continue
        st = {}
        for part in a.get("style", "").split(";"):
            if ":" in part:
                k, v = part.split(":", 1)
                st[k.strip()] = v.strip().lower()
        try:
            x = (float(a["x1"]) + float(a["x2"])) / 2.0
            y = (float(a["y1"]) + float(a["y2"])) / 2.0
        except (KeyError, ValueError):
            continue
        if inside(pr, x, y):
            out.append(colour(st.get("stroke")))
    return out


def parts(doc, txt):
    pr = doc["plotregion"]
    lines = [d for k in ("hlines", "vlines", "diaglines") for d in doc[k]
             if not d.get("dasharray")
             and inside(pr, (d["x1"] + d["x2"]) / 2.0,
                        (d["y1"] + d["y2"]) / 2.0)]
    circ = [c for c in doc["circles"] if inside(pr, c["cx"], c["cy"])]
    rects = [r for r in doc["rects"]
             if r["w"] is not None and r["h"] is not None
             and inside(pr, r["x"] + r["w"] / 2.0, r["y"] + r["h"] / 2.0)
             and not (abs(r["w"] - (pr["right"] - pr["left"])) < 1
                      and abs(r["h"] - (pr["bottom"] - pr["top"])) < 1)]
    paths = [p for p in doc["paths"] if inside(pr, *path_xy(p))]
    filled = [p for p in paths if p.get("fill") and p["fill"] != "none"]
    open_ = [p for p in paths if not p.get("fill") or p["fill"] == "none"]
    return {
        "line_strokes": distinct([colour(d["stroke"]) for d in lines]
                                 + [colour(p["stroke"]) for p in open_]),
        "head_strokes": distinct(round_lines(txt, pr)),
        "marker_fills": distinct(colour(c["fill"]) for c in circ),
        "marker_strokes": distinct(colour(c["stroke"]) for c in circ),
        "bar_fills": distinct(colour(r["fill"]) for r in rects),
        "bar_strokes": distinct(colour(r["stroke"]) for r in rects),
        "path_fills": distinct(colour(p["fill"]) for p in filled),
        "path_strokes": distinct(colour(p["stroke"]) for p in filled),
    }


def keys(doc):
    pr = doc["plotregion"]
    right = [t["text"] for t in doc["texts"]
             if t["x"] is not None and t["x"] > pr["right"]]
    fills = set()
    for kind in ("rects", "paths", "circles"):
        for e in doc[kind]:
            if kind == "rects":
                x = e["x"]
            elif kind == "circles":
                x = e["cx"]
            else:
                x = path_xy(e)[0]
            if x is not None and x > pr["right"] and colour(e.get("fill")):
                fills.add(e["fill"])
    rmark = sorted((c["cy"], c["fill"]) for c in doc["circles"]
                   if c["cx"] is not None and c["cx"] > pr["right"])
    below = sorted(((t["y"], t["x"], t["text"]) for t in doc["texts"]
                    if t["y"] is not None and t["y"] > pr["bottom"]
                    and t["x"] is not None and t["x"] <= pr["right"]))
    legm = sorted((c["cx"], c["fill"]) for c in doc["circles"]
                  if c["cy"] is not None and c["cy"] > pr["bottom"])
    return {"key_texts": right, "right_fills": sorted(fills),
            "right_marker_fills": [f for _y, f in rmark],
            "below_texts": [t for _y, _x, t in below],
            "legend_marker_fills": [f for _x, f in legm]}


out = {}
for t in G("ZP_FKEYS").split():
    rec = {"rc": int(G("ZP_RC_F_" + t)), "command": G("ZP_CMD_F_" + t)}
    doc, txt = read_doc(os.path.join(work, "f_%s.svg" % t))
    if doc is not None:
        rec.update(parts(doc, txt))
    out["F_" + t] = rec
for k in G("ZP_MKEYS").split():
    rec = {"rc": int(G("ZP_RC_" + k)), "command": G("ZP_CMD_" + k)}
    doc, txt = read_doc(os.path.join(work, "m_%s.svg" % k))
    if doc is not None:
        rec.update(keys(doc))
    out[k] = rec


def num(v):
    return None if v == "." else float(v)


data = {"t": [], "y": [], "y2": [], "z": []}
with open(os.path.join(work, "data_types.txt"), encoding="utf-8") as fh:
    for line in fh:
        vals = line.rstrip("\n").split("|")
        for k, v in zip(("t", "y", "y2", "z"), vals):
            data[k].append(num(v))
os.remove(os.path.join(work, "data_types.txt"))
out["_data"] = data
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZP_VERSION"), "born_date": G("ZP_BORN"),
                "dash_commit": commit, "extracted": G("ZP_WHEN"),
                "source": "scripts/extract_colorvar_parts_truth.do"}
with open(G("ZP_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZP_OUT"))
end
