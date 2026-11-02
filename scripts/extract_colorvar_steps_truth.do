*! extract_colorvar_steps_truth.do -- WP-42 section 42-01 (CV-8, sil:SD-4):
*! measure how twoway colours an unbinned numeric colorvar() -- the level
*! colours on every coloured type that is not a line, the marker partition,
*! the key's texts under three schemes and three forms -- how wide it draws
*! the colour key under s2color, stcolor and a scheme that sets
*! gsize clegend_width, and what the scheme's contour keys change.
*! twoway only: the output is the same before and after dash changes.
*!
*! Output: test/fixtures/colorvar_steps_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_colorvar_steps_truth.do
*!
*! PROBES
*!   T_<type>  the 17 coloured types that are not a line, each as
*!             extract_colorvar_types_truth.do writes it, with colorvar(z),
*!             z = price: rc, the distinct colours drawn in the plot region
*!             that the same command without colorvar() does not draw,
*!             the key's texts and swatch fills (lowest level first) and,
*!             for scatter, the marker partition in observation order.
*!   M_<s>     `twoway scatter mpg weight, colorvar(price) scheme(<s>)'
*!             under s1mono, stcolor and s2mono (and s2color): the markers'
*!             distinct fills, partition and the key's texts.
*!   L_<form>  zscale(log), zlabel(#3) and a %td colorvar: the same.
*!   B_<s>     the colour key's width (twice the distance from a swatch's
*!             centre to the key's axis line) and the graph's width, SVG
*!             units, under s2color, stcolor and scheme w42w (s2color with
*!             gsize clegend_width small).
*!   Z_<key>   `twoway contour depth northing easting' (sandstone) under
*!             s2color (ctl) and under a scheme including s2color with one
*!             contour key set: the plot's lastcuts, the <path>, <line>
*!             and <use> counts, the distinct colours and the key's width.
*!
*! The schemes are files in this script's work folder, put on the adopath
*! for this session only.  The git commit is read from a file `shell'
*! wrote, never with shell=True.

clear all
set more off
set linesize 200

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zs_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zs_bad' {
    display as error "extract_colorvar_steps_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zs_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zs_rc' | _rc {
    local _zs_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_colorvar_steps_truth.do: `_zs_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZS_REPO "`repo'"
global ZS_OUT "${ZS_REPO}/test/fixtures/colorvar_steps_truth.json"

local work "`c(tmpdir)'dash_colorvar_steps_probe"
capture mkdir "`work'"
global ZS_WORK "`work'"

quietly shell git -C "${ZS_REPO}" rev-parse HEAD > "${ZS_WORK}/git_head.txt"
global ZS_VERSION "`c(stata_version)'"
global ZS_BORN "`c(born_date)'"
global ZS_WHEN "`c(current_date)' `c(current_time)'"

* The user schemes, each s2color with one key set (session adopath only).
foreach s in w42w w42o w42c w42r w42n {
    capture erase "${ZS_WORK}/scheme-`s'.scheme"
}
local sk_w42w "gsize clegend_width small"
local sk_w42o "yesno contours_outline yes"
local sk_w42c "yesno contours_colorlines yes"
local sk_w42r "yesno contours_reversekey yes"
local sk_w42n "numstyle contours 4"
foreach s in w42w w42o w42c w42r w42n {
    tempname fh
    file open `fh' using "${ZS_WORK}/scheme-`s'.scheme", write text replace
    file write `fh' "#include s2color" _n
    file write `fh' "`sk_`s''" _n
    file close `fh'
}
adopath ++ "${ZS_WORK}"

* The types' data: extract_colorvar_types_truth.do's, z = price.
sysuse auto, clear
keep if rep78 < .
sort weight
generate t = _n
generate y = mpg
generate y2 = mpg + 5
generate y3 = mpg + 10
generate z = price
tempname dh
file open `dh' using "${ZS_WORK}/data_types.txt", write text replace
forvalues i = 1/`=_N' {
    file write `dh' (t[`i']) "|" (y[`i']) "|" (y2[`i']) "|" (y3[`i']) "|" (z[`i']) _n
}
file close `dh'

local tt `"scatter "scatter y t" bar "bar y t" spike "spike y t" dropline "dropline y t" dot "dot y t" rbar "rbar y y2 t" rspike "rspike y y2 t" rcap "rcap y y2 t" rcapsym "rcapsym y y2 t" rscatter "rscatter y y2 t" rpcap "rpcap y y3 y2 t" rpspike "rpspike y y3 y2 t" pcspike "pcspike y t y2 t" pccapsym "pccapsym y t y2 t" pcarrow "pcarrow y t y2 t" pcbarrow "pcbarrow y t y2 t" pcscatter "pcscatter y t y2 t""'
local tkeys ""
while `"`tt'"' != "" {
    gettoken ty tt : tt
    gettoken cmd tt : tt
    capture erase "${ZS_WORK}/t_`ty'.svg"
    capture erase "${ZS_WORK}/tp_`ty'.svg"
    capture noisily twoway `cmd', colorvar(z) scheme(s2color) name(c1, replace)
    global ZS_RC_T_`ty' = _rc
    if _rc == 0 {
        quietly graph export "${ZS_WORK}/t_`ty'.svg", replace
        graph drop c1
    }
    capture noisily twoway `cmd', scheme(s2color) name(c1, replace)
    if _rc == 0 {
        quietly graph export "${ZS_WORK}/tp_`ty'.svg", replace
        graph drop c1
    }
    local tkeys "`tkeys' `ty'"
}
global ZS_TKEYS "`tkeys'"

* M_ and L_ and B_: the whole auto data, as dash's help examples use it.
sysuse auto, clear
generate d = mdy(1, 1, 1990) + _n * 10
format d %td
tempname ah
file open `ah' using "${ZS_WORK}/data_auto.txt", write text replace
forvalues i = 1/`=_N' {
    file write `ah' (mpg[`i']) "|" (weight[`i']) "|" (price[`i']) "|" (d[`i']) _n
}
file close `ah'
local mkeys ""
foreach s in s2color s1mono stcolor s2mono {
    capture erase "${ZS_WORK}/m_`s'.svg"
    capture noisily twoway scatter mpg weight, colorvar(price) scheme(`s') name(c1, replace)
    global ZS_RC_M_`s' = _rc
    if _rc == 0 {
        quietly graph export "${ZS_WORK}/m_`s'.svg", replace
        graph drop c1
    }
    local mkeys "`mkeys' `s'"
}
global ZS_MKEYS "`mkeys'"
local lkeys ""
foreach c in "zlog|colorvar(price) zscale(log)" "zlab|colorvar(price) zlabel(#3)" "date|colorvar(d)" {
    gettoken key opts : c, parse("|")
    local opts = substr(`"`opts'"', 2, .)
    capture erase "${ZS_WORK}/l_`key'.svg"
    capture noisily twoway scatter mpg weight, `opts' scheme(s2color) name(c1, replace)
    global ZS_RC_L_`key' = _rc
    global ZS_CMD_L_`key' `"twoway scatter mpg weight, `opts'"'
    if _rc == 0 {
        quietly graph export "${ZS_WORK}/l_`key'.svg", replace
        graph drop c1
    }
    local lkeys "`lkeys' `key'"
}
global ZS_LKEYS "`lkeys'"
local bkeys ""
foreach s in s2color stcolor w42w {
    capture erase "${ZS_WORK}/b_`s'.svg"
    capture noisily twoway scatter mpg weight, colorvar(price) scheme(`s') name(c1, replace)
    global ZS_RC_B_`s' = _rc
    if _rc == 0 {
        quietly graph export "${ZS_WORK}/b_`s'.svg", replace
        graph drop c1
    }
    local bkeys "`bkeys' `s'"
}
global ZS_BKEYS "`bkeys'"

* Z_: the scheme's contour keys.
sysuse sandstone, clear
local zkeys ""
foreach c in "ctl|s2color" "outline|w42o" "colorlines|w42c" "reversekey|w42r" "levels|w42n" {
    gettoken key s : c, parse("|")
    local s = substr("`s'", 2, .)
    capture erase "${ZS_WORK}/z_`key'.svg"
    capture noisily twoway contour depth northing easting, scheme(`s') name(c1, replace)
    global ZS_RC_Z_`key' = _rc
    global ZS_CUTS_Z_`key' ""
    if _rc == 0 {
        global ZS_CUTS_Z_`key' "`.c1.plotregion1.plot1.lastcuts'"
        quietly graph export "${ZS_WORK}/z_`key'.svg", replace
        graph drop c1
    }
    global ZS_SCH_Z_`key' "`s'"
    local zkeys "`zkeys' `key'"
}
global ZS_ZKEYS "`zkeys'"

python:
import json, os, re, sys
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


work = G("ZS_WORK")
sys.path.insert(0, os.path.join(G("ZS_REPO"), "scripts"))
from svg_truth import svg_document  # noqa: E402

_NUM = re.compile(r"-?\d+(?:\.\d+)?")


def read_doc(path):
    if not os.path.exists(path):
        return None, ""
    with open(path, encoding="utf-8", errors="replace") as fh:
        txt = fh.read()
    doc = svg_document(path)
    os.remove(path)
    return doc, txt


def first_xy(e):
    if "cx" in e:
        return e["cx"], e["cy"]
    if "x1" in e:
        return (e["x1"] + e["x2"]) / 2.0, (e["y1"] + e["y2"]) / 2.0
    if "w" in e:
        return e["x"] + (e["w"] or 0) / 2.0, e["y"] + (e["h"] or 0) / 2.0
    n = [float(v) for v in _NUM.findall(e.get("d") or "")]
    return (n[0], n[1]) if len(n) >= 2 else (None, None)


def inside(pr, x, y):
    return (pr is not None and x is not None and y is not None
            and pr["left"] <= x <= pr["right"]
            and pr["top"] <= y <= pr["bottom"])


def region_colours(doc):
    pr = doc["plotregion"]
    out = set()
    for kind in ("circles", "rects", "hlines", "vlines", "diaglines",
                 "paths"):
        for e in doc[kind]:
            x, y = first_xy(e)
            if not inside(pr, x, y):
                continue
            for k in ("fill", "stroke"):
                c = e.get(k)
                if c and c.startswith("#"):
                    out.add(c)
    return out


def markers(doc):
    pr = doc["plotregion"]
    return [c for c in doc["circles"]
            if inside(pr, c.get("cx"), c.get("cy"))
            and c.get("fill") and c["fill"] != "none"]


def groups(ms):
    seen, out = {}, []
    for m in ms:
        seen.setdefault(m["fill"], len(seen))
        out.append(seen[m["fill"]])
    return out


def key_texts(doc):
    pr = doc["plotregion"]
    return [t["text"] for t in doc["texts"]
            if pr is not None and t["x"] is not None and t["x"] > pr["right"]]


def key_swatches(doc):
    """The key's filled swatches right of the plot region, lowest first."""
    pr = doc["plotregion"]
    out = []
    for kind in ("circles", "rects", "paths"):
        for e in doc[kind]:
            x, y = first_xy(e)
            if pr is None or x is None or x <= pr["right"]:
                continue
            f = e.get("fill")
            if f and f.startswith("#"):
                out.append((y, x, f))
    out.sort(key=lambda r: -r[0])
    fills = []
    for _y, _x, f in out:
        if not fills or fills[-1] != f:
            fills.append(f)
    return fills, out


def key_axis_x(doc):
    pr = doc["plotregion"]
    xs = [v["x1"] for v in doc["vlines"]
          if pr is not None and v["x1"] > pr["right"]
          and (v.get("stroke") or "") == "#000000"]
    return min(xs) if xs else None


types = {}
for t in G("ZS_TKEYS").split():
    rec = {"rc": int(G("ZS_RC_T_" + t))}
    doc, _txt = read_doc(os.path.join(work, "t_%s.svg" % t))
    pdoc, _ptxt = read_doc(os.path.join(work, "tp_%s.svg" % t))
    if doc is not None:
        plain = region_colours(pdoc) if pdoc is not None else set()
        rec["colours"] = sorted(region_colours(doc) - plain)
        rec["key_texts"] = key_texts(doc)
        rec["key_fills"] = key_swatches(doc)[0]
        if t == "scatter":
            ms = markers(doc)
            rec["fill_groups"] = groups(ms)
            rec["n_markers"] = len(ms)
    types["T_" + t] = rec


def scatter_rec(path, rc):
    rec = {"rc": rc}
    doc, _txt = read_doc(path)
    if doc is None:
        return rec
    ms = markers(doc)
    order = []
    for m in ms:
        if m["fill"] not in order:
            order.append(m["fill"])
    rec["colours"] = sorted(order)
    rec["fill_groups"] = groups(ms)
    rec["n_markers"] = len(ms)
    rec["key_texts"] = key_texts(doc)
    rec["key_fills"] = key_swatches(doc)[0]
    return rec


out = dict(types)
for s in G("ZS_MKEYS").split():
    out["M_" + s] = scatter_rec(os.path.join(work, "m_%s.svg" % s),
                                int(G("ZS_RC_M_" + s)))
    out["M_" + s]["command"] = ("twoway scatter mpg weight, colorvar(price) "
                                "scheme(%s)" % s)
for k in G("ZS_LKEYS").split():
    out["L_" + k] = scatter_rec(os.path.join(work, "l_%s.svg" % k),
                                int(G("ZS_RC_L_" + k)))
    out["L_" + k]["command"] = G("ZS_CMD_L_" + k)
for s in G("ZS_BKEYS").split():
    rec = {"rc": int(G("ZS_RC_B_" + s))}
    doc, _txt = read_doc(os.path.join(work, "b_%s.svg" % s))
    if doc is not None:
        _f, sw = key_swatches(doc)
        ax = key_axis_x(doc)
        cx = [x for _y, x, _c in sw]
        rec["axis_x"] = ax
        rec["swatch_x"] = round(sum(cx) / len(cx), 2) if cx else None
        rec["key_width"] = (round(2 * (ax - rec["swatch_x"]), 2)
                            if ax is not None and cx else None)
        rec["graph_width"] = doc["canvas"]["w"]
    rec["command"] = ("twoway scatter mpg weight, colorvar(price) "
                      "scheme(%s)" % s)
    out["B_" + s] = rec
for k in G("ZS_ZKEYS").split():
    rec = {"rc": int(G("ZS_RC_Z_" + k)), "scheme": G("ZS_SCH_Z_" + k)}
    doc, txt = read_doc(os.path.join(work, "z_%s.svg" % k))
    if doc is not None:
        rec["lastcuts"] = [float(v) for v in G("ZS_CUTS_Z_" + k).split()]
        rec["n_path"] = txt.count("<path")
        rec["n_line"] = txt.count("<line")
        rec["n_use"] = txt.count("<use")
        rec["colours"] = sorted({h.lower() for h in re.findall(
            r"(?:fill|stroke):(#[0-9A-Fa-f]{6})", txt)})
        rec["strokes"] = sorted({h.lower() for h in re.findall(
            r"stroke:(#[0-9A-Fa-f]{6})", txt)})
        pr = doc["plotregion"]
        kx = []
        for p in doc["paths"]:
            n = [float(v) for v in _NUM.findall(p.get("d") or "")]
            xs = n[0::2]
            if xs and pr is not None and min(xs) > pr["right"]:
                kx += xs
        rec["key_width"] = round(max(kx) - min(kx), 2) if kx else None
        rec["key_texts"] = key_texts(doc)
        rec["graph_width"] = doc["canvas"]["w"]
    out["Z_" + k] = rec


def num(v):
    return None if v == "." else float(v)


data = {"types": {"t": [], "y": [], "y2": [], "y3": [], "price": []},
        "auto": {"mpg": [], "weight": [], "price": [], "d": []}}
with open(os.path.join(work, "data_types.txt"), encoding="utf-8") as fh:
    for line in fh:
        t, y, y2, y3, z = line.rstrip("\n").split("|")
        for k, v in zip(("t", "y", "y2", "y3", "price"), (t, y, y2, y3, z)):
            data["types"][k].append(num(v))
with open(os.path.join(work, "data_auto.txt"), encoding="utf-8") as fh:
    for line in fh:
        m, w, p, d = line.rstrip("\n").split("|")
        for k, v in zip(("mpg", "weight", "price", "d"), (m, w, p, d)):
            data["auto"][k].append(num(v))
for f in ("data_types.txt", "data_auto.txt"):
    os.remove(os.path.join(work, f))
for s in ("w42w", "w42o", "w42c", "w42r", "w42n"):
    try:
        os.remove(os.path.join(work, "scheme-%s.scheme" % s))
    except OSError:
        pass
out["_data"] = data
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZS_VERSION"), "born_date": G("ZS_BORN"),
                "dash_commit": commit, "extracted": G("ZS_WHEN"),
                "source": "scripts/extract_colorvar_steps_truth.do",
                "user_schemes": {"w42w": "gsize clegend_width small",
                                 "w42o": "yesno contours_outline yes",
                                 "w42c": "yesno contours_colorlines yes",
                                 "w42r": "yesno contours_reversekey yes",
                                 "w42n": "numstyle contours 4"}}
with open(G("ZS_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZS_OUT"))
end
