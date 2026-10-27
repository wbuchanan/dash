*! extract_arrowhead_truth.do -- WP-31 section 02 (GAPS3 C1): measure the
*! heads twoway draws on pcarrow and pcbarrow -- _gr_arrowhead's geometry
*! (stroke length msize(), half-angle mangle(), barb depth barbsize()),
*! their colours and widths, a row missing its second point, headlabel's
*! label position and the values twoway refuses or notes -- from twoway's
*! own class values (.style.marker.size/angle/backsize) and its SVG.
*! twoway only: the output is the same before and after dash changes.
*!
*! Output: test/fixtures/arrowhead_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_arrowhead_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zh_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zh_bad' {
    display as error "extract_arrowhead_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zh_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zh_rc' | _rc {
    local _zh_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_arrowhead_truth.do: `_zh_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZH_REPO "`repo'"
global ZH_OUT "${ZH_REPO}/test/fixtures/arrowhead_truth.json"

local work "`c(tmpdir)'dash_arrowhead_probe"
capture mkdir "`work'"
global ZH_WORK "`work'"


quietly shell git -C "${ZH_REPO}" rev-parse HEAD > "${ZH_WORK}/git_head.txt"
global ZH_VERSION "`c(stata_version)'"
global ZH_BORN "`c(born_date)'"
global ZH_WHEN "`c(current_date)' `c(current_time)'"

* _zh_rec key: the class values of the graph named g's first plot into
* global ZH_C_<key> as "size angle backsize".
capture program drop _zh_rec
program define _zh_rec
    args key
    local s "`.g.plotregion1.plot1.style.marker.size.val'"
    local a "`.g.plotregion1.plot1.style.marker.angle.val'"
    local b "`.g.plotregion1.plot1.style.marker.backsize.val'"
    foreach v in s a b {
        if "``v''" == "" local `v' "."
    }
    global ZH_C_`key' "`s' `a' `b'"
    display as text "ZH `key': size `s' angle `a' backsize `b'"
end

clear
input y1 x1 y2 x2
1 1 2 2
2 1 3 3
3 2 4 2
4 3 5 4
5 4 6 6
end
generate y2m = y2
replace y2m = . in 3
generate str1 lab = word("a b c d e", _n)
set scheme s2color

local keys ""
foreach c in "default|pcarrow y1 x1 y2 x2" ///
    "msize_small|pcarrow y1 x1 y2 x2, msize(small)" ///
    "msize_large|pcarrow y1 x1 y2 x2, msize(large)" ///
    "msize_vlarge|pcarrow y1 x1 y2 x2, msize(vlarge)" ///
    "msize_2|pcarrow y1 x1 y2 x2, msize(2)" ///
    "msize_x2|pcarrow y1 x1 y2 x2, msize(*2)" ///
    "barb_medium|pcarrow y1 x1 y2 x2, barbsize(medium)" ///
    "barb_large|pcarrow y1 x1 y2 x2, barbsize(large)" ///
    "barb_msize|pcarrow y1 x1 y2 x2, barbsize(medium) msize(medium)" ///
    "mangle_45|pcarrow y1 x1 y2 x2, mangle(45)" ///
    "colours|pcarrow y1 x1 y2 x2, mcolor(red) mlcolor(blue) mfcolor(green) barbsize(medium) mlwidth(thick)" ///
    "mcolor|pcarrow y1 x1 y2 x2, mcolor(red)" ///
    "lcolor|pcarrow y1 x1 y2 x2, lcolor(red) lwidth(thick)" ///
    "lcolor_barb|pcarrow y1 x1 y2 x2, lcolor(red) lwidth(thick) barbsize(medium)" ///
    "pcbarrow|pcbarrow y1 x1 y2 x2" ///
    "onepoint|pcarrow y1 x1 y2m x2" ///
    "headlabel|pcarrow y1 x1 y2 x2, mlabel(lab) headlabel" ///
    "taillabel|pcarrow y1 x1 y2 x2, mlabel(lab)" {
    gettoken key cmd : c, parse("|")
    local cmd = substr(`"`cmd'"', 2, .)
    local sep = cond(strpos(`"`cmd'"', ","), " ", ", ")
    quietly twoway `cmd' `sep' name(g, replace)
    _zh_rec `key'
    quietly graph export "${ZH_WORK}/`key'.svg", replace
    graph drop g
    local keys "`keys' `key'"
}
global ZH_KEYS "`keys'"

* What twoway refuses or notes: rc and the lines it prints, each in its own
* log.
local rkeys ""
foreach c in "barb_neg|barbsize(-1)" "barb_abc|barbsize(abc)" ///
    "barb_big|barbsize(20000)" "mangle_abc|mangle(abc)" ///
    "mangle_400|mangle(400)" "mangle_m400|mangle(-400)" ///
    "headlabel_twice|headlabel headlabel" {
    gettoken key opt : c, parse("|")
    local opt = substr(`"`opt'"', 2, .)
    quietly log using "${ZH_WORK}/ref_`key'.log", text replace name(zhref)
    capture noisily twoway pcarrow y1 x1 y2 x2, `opt' name(g, replace)
    local rc = _rc
    quietly log close zhref
    capture graph drop g
    global ZH_RC_`key' "`rc'"
    local rkeys "`rkeys' `key'"
}
global ZH_RKEYS "`rkeys'"

python:
import json, math, os, re
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


work = G("ZH_WORK")
_LINE = re.compile(r"<line\b([^>]*)/?>")
_ATTR = re.compile(r'([\w:-]+)="([^"]*)"')
_USE = re.compile(r'<use xlink:href="#(path_\w+)" style="([^"]*)"')
_PATH = re.compile(r'<path id="(path_\w+)" d="([^"]*)"')
_TEXT = re.compile(r"<text\b([^>]*)>([^<]*)</text>")


def style(s):
    out = {}
    for part in s.split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip()] = v.strip().lower()
    return out


def svg(key):
    path = os.path.join(work, key + ".svg")
    with open(path, encoding="utf-8") as fh:
        txt = fh.read()
    vb = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', txt)
    W, H = float(vb.group(1)), float(vb.group(2))
    shafts, heads = [], []
    for m in _LINE.finditer(txt):
        a = dict(_ATTR.findall(m.group(1)))
        st = style(a.get("style", ""))
        d = {"x1": float(a["x1"]), "y1": float(a["y1"]),
             "x2": float(a["x2"]), "y2": float(a["y2"]),
             "stroke": st.get("stroke"),
             "width": float(st.get("stroke-width", "nan"))}
        if a.get("stroke-linecap") == "round":
            heads.append(d)
        elif st.get("stroke") not in ("#000000", "#eaf2f3"):
            shafts.append(d)
    paths = {}
    for pid, dd in _PATH.findall(txt):
        pts = [tuple(map(float, p.split()))
               for p in re.findall(r"[ML]([\d.\- ]+)", dd)]
        paths[pid] = pts
    polys = []
    for pid, st in _USE.findall(txt):
        s = style(st)
        if pid not in paths:
            continue
        rec = next((p for p in polys if p["id"] == pid), None)
        if rec is None:
            rec = {"id": pid, "pts": paths[pid]}
            polys.append(rec)
        if s.get("fill", "none") != "none":
            rec["fill"] = s["fill"]
        if s.get("stroke", "none") != "none":
            rec["stroke"] = s["stroke"]
            rec["width"] = float(s.get("stroke-width", "nan"))
    texts = [(dict(_ATTR.findall(a)), t.strip())
             for a, t in _TEXT.findall(txt)]
    os.remove(path)
    return W, H, shafts, heads, polys, texts


def ang(u, v):
    nu = math.hypot(*u)
    nv = math.hypot(*v)
    c = (u[0] * v[0] + u[1] * v[1]) / (nu * nv)
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def near(p, q):
    return abs(p[0] - q[0]) < 0.05 and abs(p[1] - q[1]) < 0.05


def measure(key):
    W, H, shafts, heads, polys, texts = svg(key)
    rs = min(W, H) / 100.0
    cv = [float(w) if w != "." else None for w in G("ZH_C_" + key).split()]
    out = {"size_val": cv[0], "angle": cv[1], "backsize_val": cv[2],
           "canvas": [W, H], "shafts": len(shafts),
           "head_strokes": len(heads), "filled_heads": len(polys),
           "circles": 0}
    lens, halfs = [], []
    for h in heads:
        # The shaft this stroke belongs to: of every shaft end at the
        # stroke's tip (a tip can be another row's end or start), the one
        # the stroke leans back along at the smallest angle.
        tip = (h["x1"], h["y1"])
        sv = (h["x2"] - h["x1"], h["y2"] - h["y1"])
        best = None
        for s in shafts:
            for t, o in (((s["x2"], s["y2"]), (s["x1"], s["y1"])),
                         ((s["x1"], s["y1"]), (s["x2"], s["y2"]))):
                if near(tip, t):
                    a = ang((o[0] - t[0], o[1] - t[1]), sv)
                    if best is None or a < best:
                        best = a
        if best is not None:
            lens.append(math.hypot(*sv) / rs)
            halfs.append(best)
    if lens:
        out["stroke_len_rs"] = round(sum(lens) / len(lens), 4)
        out["stroke_len_rs_range"] = [round(min(lens), 4), round(max(lens), 4)]
        out["half_angle"] = round(sum(halfs) / len(halfs), 3)
        out["head_stroke_colours"] = sorted({h["stroke"] for h in heads})
        out["head_stroke_width_rs"] = round(heads[0]["width"] / rs, 4)
    if shafts:
        out["shaft_colour"] = shafts[0]["stroke"]
        out["shaft_width_rs"] = round(shafts[0]["width"] / rs, 4)
    if polys:
        p = polys[0]
        pts = p["pts"]
        distinct = [q for i, q in enumerate(pts) if not any(near(q, r) for r in pts[:i])]
        out["poly_vertices"] = len(distinct)
        out["poly_fill"] = p.get("fill")
        out["poly_stroke"] = p.get("stroke")
        # The polygon's stroke is clipped to its inside: half is drawn.
        out["poly_stroke_width_rs"] = (round(p["width"] / 2.0 / rs, 4)
                                       if "width" in p else None)
        T, A, B, C = distinct[0], distinct[1], distinct[2], distinct[3]
        sh = next(s for s in shafts if near((s["x2"], s["y2"]), T))
        back = (sh["x1"] - T[0], sh["y1"] - T[1])
        out["poly_tip_to_a_rs"] = round(math.hypot(A[0] - T[0], A[1] - T[1]) / rs, 4)
        out["poly_tip_to_b_rs"] = round(math.hypot(B[0] - T[0], B[1] - T[1]) / rs, 4)
        out["poly_half_angle"] = round(ang(back, (A[0] - T[0], A[1] - T[1])), 3)
        out["poly_angle_at_a"] = round(ang((T[0] - A[0], T[1] - A[1]),
                                           (B[0] - A[0], B[1] - A[1])), 3)
        # barbsize() = msize() puts B at the foot of the perpendicular
        # from A to the shaft: the right angle is at B.
        out["poly_angle_at_b"] = round(ang((A[0] - B[0], A[1] - B[1]),
                                           (T[0] - B[0], T[1] - B[1])), 3)
        out["poly_fills"] = sorted({q.get("fill") for q in polys})
    labs = [(a, t) for a, t in texts if t in ("a", "b", "c", "d", "e")]
    if labs:
        at = []
        for a, t in labs:
            s = shafts["abcde".index(t)] if len(shafts) == 5 else None
            lx, ly = float(a["x"]), float(a["y"])
            dh = math.hypot(lx - s["x2"], ly - s["y2"])
            dt = math.hypot(lx - s["x1"], ly - s["y1"])
            at.append("head" if dh < dt else "tail")
        out["labels_at"] = at
    return out


heads = {}
for k in G("ZH_KEYS").split():
    heads[k] = measure(k)
onepoint = heads.pop("onepoint")
onepoint["shafts_all_present"] = heads["default"]["shafts"]
onepoint["head_strokes_all_present"] = heads["default"]["head_strokes"]
onepoint["markers"] = onepoint["circles"]
onepoint["markers_all_present"] = heads["default"]["circles"]
headlabel = {"with": heads.pop("headlabel")["labels_at"],
             "without": heads.pop("taillabel")["labels_at"]}

refusals = {}
for k in G("ZH_RKEYS").split():
    p = os.path.join(work, "ref_%s.log" % k)
    with open(p, encoding="utf-8", errors="replace") as fh:
        lines = [ln.rstrip() for ln in fh
                 if ln.strip() and not ln.lstrip().startswith((".", "> "))
                 and "log:" not in ln and "log type:" not in ln
                 and "opened on:" not in ln and "closed on:" not in ln
                 and "name:" not in ln and not ln.startswith("---")]
    os.remove(p)
    refusals[k] = {"rc": int(G("ZH_RC_" + k)), "lines": lines}

out = {"heads": heads, "onepoint": onepoint, "headlabel": headlabel,
       "refusals": refusals}
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZH_VERSION"), "born_date": G("ZH_BORN"),
                "dash_commit": commit, "extracted": G("ZH_WHEN"),
                "source": "scripts/extract_arrowhead_truth.do"}
with open(G("ZH_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZH_OUT"))
end
