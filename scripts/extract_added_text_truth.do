* extract_added_text_truth.do -- twoway's own text() and ttext() (WP-30
* P1.10, section 56), written to test/fixtures/added_text_truth.json for
* test/test_added_text.py, the AT cases of
* test/test_twoway_option_parity.cscript and the S56 blocks of
* test/test_wp30_truth.cscript.
*
* Records, per probe id (probes[<id>]):
*   cmd, rc, error (the last line twoway printed when rc is not 0),
*   notes (every "(note: ...)" line), control (the probe whose texts are
*   the baseline), and for a drawn probe:
*   texts   every <text> the probe adds over its control, in document
*           order: text, x_px, y_px, size, fill, anchor, rotate;
*   boxes   every filled or outlined <path> drawn through <use>: left,
*           right, top, bottom (px), fill, stroke, stroke_width;
*   point   the text block's drawn centre in data units of the x axis and
*           the left y axis ({"x", "y"}), read through the probe's own
*           tick labels (svg_truth.svg_axis_reading): a boxed block's box
*           centre, else its first line's centre; a horizontal line's
*           centre is its baseline less 0.3504 of its size, a vertical
*           one's x likewise (measured: text(30 3000 "VVV",
*           orientation(vertical)) turns about (2402.11, 1075.61) and
*           "AAA" at the same point has its baseline at 1115.05, 39.44 px
*           = 0.3504 x 112.56 lower);
*   tick_x  the x axis's tick labels read (to check a date axis).
* _meta.compass: each place() spelling -> the canonical compass direction
*   twoway drew the block in relative to its point (n ne e se s sw w nw c),
*   or null when twoway named the spelling in a note (an unknown name,
*   drawn east).
* _meta.orient: each orientation() spelling -> the rotation twoway drew
*   (degrees, 0 for none), or null when it was refused or noted.
*
* Run (never the GUI; the slot wrapper of scripts/stata_slot.sh):
*   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_added_text_truth.do
* SVGs and logs go to c(tmpdir).  The trailing python: block never calls
* back into Stata and holds no backtick.

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_za_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_za_bad' {
    display as error "extract_added_text_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _za_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_za_rc' | _rc {
    local _za_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_added_text_truth.do: `_za_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}

clear all
set more off
set linesize 255
version 19
set scheme stcolor

local stata_version = c(stata_version)
local born_date "`c(born_date)'"
tempfile gh
shell git -C "`repo'" rev-parse HEAD > "`gh'"
tempname fh
file open `fh' using "`gh'", read text
file read `fh' dash_commit
file close `fh'
local extracted "`c(current_date)'"
local tmp "`c(tmpdir)'"

* The three datasets: auto; monthly (t %tm 1995m1-2004m12, tn its plain
* copy, y and y2, tsset t); daily (d %td from 01jan2001, every 5 days, y).
capture program drop _at_data
program _at_data
    version 19
    args ds
    if "`ds'" == "$AT_DS" exit
    if "`ds'" == "auto" {
        sysuse auto, clear
    }
    else if "`ds'" == "monthly" {
        clear
        quietly set obs 120
        generate t = tm(1995m1) + _n - 1
        format t %tm
        generate tn = t
        generate double y = 10 + mod(_n, 7)
        generate double y2 = 100 + mod(_n, 11)
        quietly tsset t
    }
    else if "`ds'" == "daily" {
        clear
        quietly set obs 100
        generate d = td(01jan2001) + 5 * (_n - 1)
        format d %td
        generate double y = 5 + mod(_n, 9)
    }
    global AT_DS "`ds'"
end

capture program drop _at_probe
program _at_probe
    version 19
    args id ds ctl cmd
    local tmp "`c(tmpdir)'"
    _at_data `ds'
    capture log close atp
    capture graph drop _all
    log using "`tmp'/at_`id'.log", text replace name(atp)
    capture noisily `cmd' name(zqt, replace)
    local rc = _rc
    log close atp
    capture erase "`tmp'/at_`id'.svg"
    if `rc' == 0 {
        quietly graph export "`tmp'/at_`id'.svg", name(zqt) replace
    }
    file write $AT_RH `"`id'|`ds'|`ctl'|`rc'|`cmd'"' _n
end

tempfile recs
tempname rh
file open `rh' using "`recs'", write text replace
global AT_RH `rh'
global AT_DS ""

local sc "twoway scatter mpg weight,"
* Controls.
_at_probe ctl auto "" `"`sc'"'
foreach s in s2color s1mono s1rcolor s2color8 {
    _at_probe ctl_`s' auto "" `"`sc' scheme(`s')"'
}
_at_probe ctl_by auto "" `"`sc' by(foreign)"'
_at_probe ctl_y2 auto "" `"twoway (scatter mpg weight) (scatter price weight, yaxis(2)),"'
_at_probe ctl_log auto "" `"`sc' xscale(log)"'
_at_probe ctl_rev auto "" `"`sc' xscale(reverse)"'
_at_probe ctl_lev auto "" `"twoway (scatter mpg weight) (scatter mpg length),"'
_at_probe ctl_seg auto "" `"twoway scatter mpg weight || scatter mpg length,"'

* E3's drawn rows.
_at_probe aaa auto ctl `"`sc' text(30 3000 "AAA")"'
_at_probe two auto ctl `"`sc' text(30 3000 "AAA", color(red) size(large)) text(20 4000 "BBB")"'
_at_probe lines auto ctl `"`sc' text(30 3000 "L1" "L2")"'
_at_probe far auto ctl `"`sc' text(100 3000 "FAR")"'
_at_probe above auto ctl `"`sc' text(43 3000 "ABOVE")"'
_at_probe vert auto ctl `"`sc' text(30 3000 "VVV", orientation(vertical))"'
_at_probe rvert auto ctl `"`sc' text(30 3000 "RVV", orientation(rvertical))"'
_at_probe rhor auto ctl `"`sc' text(30 3000 "RHH", orientation(rhorizontal))"'
_at_probe box auto ctl `"`sc' text(30 3000 "BOX", box fcolor(yellow) lcolor(blue) margin(medium))"'
_at_probe level_pg auto ctl_lev `"twoway (scatter mpg weight, text(30 3000 "PG")) (scatter mpg length), text(20 4000 "GL")"'
_at_probe level_seg auto ctl_seg `"twoway scatter mpg weight, text(30 3000 "S1") || scatter mpg length, text(20 4000 "S2")"'
_at_probe by auto ctl_by `"`sc' by(foreign) text(30 3000 "BYT")"'
_at_probe y2 auto ctl_y2 `"twoway (scatter mpg weight) (scatter price weight, yaxis(2)), text(10000 3000 "Y2T", yaxis(2))"'
_at_probe just auto ctl `"`sc' text(30 3000 "J1" "JJJJJJ2", just(left) box)"'
_at_probe log auto ctl_log `"`sc' xscale(log) text(30 3000 "LOG")"'
_at_probe rev auto ctl_rev `"`sc' xscale(reverse) text(30 3000 "REV")"'
_at_probe size_x2 auto ctl `"`sc' text(30 3000 "SZA", size(*2))"'
_at_probe size_pt auto ctl `"`sc' text(30 3000 "SZB", size(20pt))"'
_at_probe size_5 auto ctl `"`sc' text(30 3000 "SZC", size(5))"'
_at_probe size_huge auto ctl `"`sc' text(30 3000 "SZD", size(huge))"'
_at_probe empty auto ctl `"`sc' text(30 3000 "")"'
_at_probe nostr auto ctl `"`sc' text(30 3000)"'
_at_probe none auto ctl `"`sc' text()"'
_at_probe trail auto ctl `"`sc' text(30 3000 "TRL" 20 4000)"'
_at_probe html auto ctl `"`sc' text(30 3000 "<b>x</b>&amp;")"'
_at_probe abbr auto ctl `"`sc' text(30 3000 "ABR", c(red) si(large) orient(vert))"'
_at_probe noted auto ctl `"`sc' text(30 3000 "NTD", width(5) linegap(2) tstyle(heading))"'
foreach s in s2color s1mono s1rcolor s2color8 {
    _at_probe sch_`s' auto ctl_`s' `"`sc' scheme(`s') text(30 3000 "SCH")"'
    _at_probe schb_`s' auto ctl_`s' `"`sc' scheme(`s') text(30 3000 "SCB", box)"'
}
_at_probe schb_stcolor auto ctl `"`sc' text(30 3000 "SCB", box)"'

* Placement and orientation spellings.
local k 0
foreach p in n north 12 t top 1 2 ne neast 3 e east r right 4 5 se seast 6 s south b bottom 7 8 sw swest 9 w west l left 10 11 nw nwest 0 c center zz {
    local ++k
    _at_probe pl_`k' auto ctl `"`sc' text(30 3000 "PX", place(`p'))"'
    global AT_PL_`k' "`p'"
}
global AT_PL_N `k'
local k 0
foreach o in horizontal h horiz vertical v vert rvertical rv rvert rhorizontal rh rhoriz bogus {
    local ++k
    _at_probe or_`k' auto ctl `"`sc' text(30 3000 "OX", orientation(`o'))"'
    global AT_OR_`k' "`o'"
}
global AT_OR_N `k'

* E3's refusals.
_at_probe r_onept auto "" `"`sc' text(30 "AAA")"'
_at_probe r_missy auto "" `"`sc' text(. 3000 "MISS")"'
_at_probe r_alpha auto "" `"`sc' text(a 3000 "x")"'
_at_probe r_expr auto "" `"`sc' text(1+1 3000 "x")"'
_at_probe r_big auto "" `"`sc' text(30 1e400 "x")"'
_at_probe r_e3 auto ctl `"`sc' text(30 3e3 "E3")"'
_at_probe r_bare auto "" `"`sc' text(30 3000 x)"'
_at_probe r_trail1 auto "" `"`sc' text(30 3000 "x" 20)"'
_at_probe r_nosuch auto "" `"`sc' text(30 3000 "x", nosuch(1))"'
_at_probe r_ori auto "" `"`sc' text(30 3000 "x", ori(v))"'
_at_probe r_tex auto "" `"`sc' tex(30 3000 "x")"'
_at_probe r_y2 auto "" `"`sc' text(30 3000 "x", yaxis(2))"'
_at_probe r_x2 auto "" `"`sc' text(30 3000 "x", xaxis(2))"'
_at_probe r_y2ok auto ctl_y2 `"twoway (scatter mpg weight) (scatter price weight, yaxis(2)), text(30 3000 "Y2OK", yaxis(2))"'
_at_probe r_nopt_y2 auto "" `"`sc' text(, yaxis(2))"'
_at_probe r_onebad auto "" `"`sc' text(30 3000 "ok") text(30 "bad")"'

* ttext() (commit 2).
_at_probe ctl_m monthly "" `"twoway tsline y,"'
_at_probe tt_m monthly ctl_m `"twoway tsline y, ttext(12 2001m1 "TT1")"'
_at_probe tt_mq monthly ctl_m `"twoway tsline y, ttext(12 "2001m1" "TT2")"'
_at_probe tt_q monthly ctl_m `"twoway tsline y, ttext(12 2001q1 "TT3")"'
_at_probe tt_text monthly "" `"twoway tsline y, text(12 2001m1 "x")"'
_at_probe tt_fn monthly "" `"twoway tsline y, ttext(12 tm(2001m1) "x")"'
_at_probe tt_m13 monthly "" `"twoway tsline y, ttext(12 2001m13 "x")"'
_at_probe tt_auto auto "" `"`sc' ttext(30 2001m1 "x")"'
_at_probe tt_dot auto "" `"`sc' ttext(30 . "x")"'
_at_probe tt_num auto ctl `"`sc' ttext(30 3000 "TTN")"'
_at_probe ctl_d daily "" `"twoway line y d,"'
_at_probe tt_d daily ctl_d `"twoway line y d, ttext(10 01jun2001 "D1")"'
_at_probe tt_dm daily "" `"twoway line y d, ttext(10 2001m6 "x")"'
_at_probe tt_two1 monthly "" `"twoway (line y tn) (line y t), ttext(12 2001m1 "x")"'
_at_probe ctl_two2 monthly "" `"twoway (line y t) (line y tn),"'
_at_probe tt_two2 monthly ctl_two2 `"twoway (line y t) (line y tn), ttext(12 2001m1 "TW2")"'
_at_probe ctl_xl monthly "" `"twoway line y tn, xlabel(, format(%tm))"'
_at_probe tt_xl monthly ctl_xl `"twoway line y tn, xlabel(, format(%tm)) ttext(12 2001m1 "XL")"'
_at_probe ctl_xl9 monthly "" `"twoway line y t, xlabel(, format(%9.0g))"'
_at_probe tt_xl9 monthly ctl_xl9 `"twoway line y t, xlabel(, format(%9.0g)) ttext(12 2001m1 "XL9")"'
_at_probe tt_rev monthly "" `"twoway line t y, ttext(2001m1 12 "x")"'
file close `rh'

local pl_spell ""
forvalues i = 1/$AT_PL_N {
    local pl_spell "`pl_spell' pl_`i'=${AT_PL_`i'}"
}
local or_spell ""
forvalues i = 1/$AT_OR_N {
    local or_spell "`or_spell' or_`i'=${AT_OR_`i'}"
}

python:
import collections, datetime, json, math, os, re, sys
from sfi import Macro
repo = Macro.getLocal("repo")
tmp = Macro.getLocal("tmp")
sys.path.insert(0, os.path.join(repo, "scripts"))
import svg_truth

_HDR = re.compile(r"^\s*(name|log|log type|opened on|closed on):")
CENTRE = 0.3504


def _log_rows(pid):
    try:
        with open(os.path.join(tmp, "at_" + pid + ".log"),
                  encoding="utf-8", errors="replace") as fh:
            rows = fh.read().splitlines()
    except OSError:
        return []
    out = []
    for r in rows:
        if _HDR.match(r) or set(r.strip()) <= set("-"):
            continue
        out.append(r.rstrip())
    return out


_MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep",
           "oct", "nov", "dec"]


def _date_value(s):
    """A %tm or %td tick label in Stata units, or None."""
    s = (s or "").strip()
    m = re.fullmatch(r"(\d{4})m(\d{1,2})", s)
    if m:
        return (int(m.group(1)) - 1960) * 12 + int(m.group(2)) - 1
    m = re.fullmatch(r"(\d{2})([a-z]{3})(\d{4})", s)
    if m and m.group(2) in _MONTHS:
        d = datetime.date(int(m.group(3)), _MONTHS.index(m.group(2)) + 1,
                          int(m.group(1)))
        return (d - datetime.date(1960, 1, 1)).days
    return None


def _mapping(rd):
    pairs = rd.get("pairs") or []
    fit = rd.get("fit")
    if len(pairs) < 2:
        lab = rd.get("labels") or []
        tp = rd.get("tick_px") or []
        pairs = [(p, _date_value(l)) for p, l in zip(tp, lab)
                 if _date_value(l) is not None]
        fit = {"space": "linear"} if len(pairs) >= 2 else None
    if fit is None or len(pairs) < 2:
        return None
    (p0, v0), (p1, v1) = pairs[0], pairs[-1]
    if fit["space"] == "log10":
        a0, a1 = math.log10(v0), math.log10(v1)
        to_v = lambda px: 10 ** (a0 + (a1 - a0) * (px - p0) / (p1 - p0))
        to_px = lambda v: p0 + (math.log10(v) - a0) * (p1 - p0) / (a1 - a0)
    else:
        to_v = lambda px: v0 + (v1 - v0) * (px - p0) / (p1 - p0)
        to_px = lambda v: p0 + (v - v0) * (p1 - p0) / (v1 - v0)
    return to_v, to_px


_USE = re.compile(r"<use ([^>]*?)/>")
_PATHD = re.compile(r'<path id="([^"]+)" d="([^"]+)"')


def _boxes(svg):
    with open(svg, encoding="utf-8", errors="replace") as fh:
        txt = fh.read()
    paths = {}
    for pid, d in _PATHD.findall(txt):
        nums = [float(v) for v in re.findall(r"-?[0-9.]+", d)]
        xs, ys = nums[0::2], nums[1::2]
        if xs and ys:
            paths[pid] = (min(xs), max(xs), min(ys), max(ys))
    out = collections.OrderedDict()
    for m in _USE.finditer(txt):
        a = dict(re.findall(r'([\w:-]+)="([^"]*)"', m.group(1)))
        ref = a.get("xlink:href", "").lstrip("#")
        if ref not in paths:
            continue
        st = {}
        for part in a.get("style", "").split(";"):
            if ":" in part:
                k, v = part.split(":", 1)
                st[k.strip()] = v.strip()
        l, r, t, b = paths[ref]
        rec = out.setdefault(ref, {"left": l, "right": r, "top": t,
                                   "bottom": b, "fill": None, "stroke": None,
                                   "stroke_width": None})
        if st.get("fill", "none") != "none":
            rec["fill"] = st["fill"].lower()
        if st.get("stroke", "none") != "none":
            rec["stroke"] = st["stroke"].lower()
            try:
                rec["stroke_width"] = float(st.get("stroke-width"))
            except (TypeError, ValueError):
                pass
    return [v for v in out.values() if v["fill"] or v["stroke"]]


recs = []
with open(Macro.getLocal("recs"), encoding="utf-8") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if line:
            pid, ds, ctl, rc, cmd = line.split("|", 4)
            recs.append((pid, ds, ctl, int(rc), cmd.rstrip(",").strip()))

docs, texts = {}, {}
for pid, ds, ctl, rc, cmd in recs:
    p = os.path.join(tmp, "at_" + pid + ".svg")
    if rc == 0 and os.path.exists(p):
        docs[pid] = svg_truth.svg_document(p)
        texts[pid] = docs[pid]["texts"]

probes = {}
for pid, ds, ctl, rc, cmd in recs:
    rows = _log_rows(pid)
    rec = {"cmd": cmd, "dataset": ds, "rc": rc, "control": ctl,
           "notes": [r.strip() for r in rows if r.strip().startswith("(note:")],
           "error": ""}
    if rc != 0:
        body = [r for r in rows if r.strip()]
        rec["error"] = body[-1] if body else ""
    if pid in docs:
        own = texts[pid]
        base = collections.Counter(t["text"] for t in texts.get(ctl, []))
        added = []
        for t in own:
            if base[t["text"]] > 0:
                base[t["text"]] -= 1
                continue
            added.append({"text": t["text"], "x_px": t["x"], "y_px": t["y"],
                          "size": t["size"], "fill": t["fill"],
                          "anchor": t["anchor"], "rotate": t["rotate"]})
        if not ctl:
            added = []
        rec["texts"] = added
        p = os.path.join(tmp, "at_" + pid + ".svg")
        cb = [(b["left"], b["top"]) for b in _boxes(
            os.path.join(tmp, "at_" + ctl + ".svg"))] if ctl in docs else []
        rec["boxes"] = [b for b in _boxes(p) if (b["left"], b["top"]) not in cb]
        rx = svg_truth.svg_axis_reading(p, "x", doc=docs[pid])
        ry = svg_truth.svg_axis_reading(p, "y", doc=docs[pid])
        rec["tick_x"] = [l for l in (rx.get("labels") or [])]
        mx, my = _mapping(rx), _mapping(ry)
        rec["point"] = None
        rec["px_of"] = None
        if added and mx and my:
            first = added[0]
            group = [t for t in added if t["x_px"] == first["x_px"]
                     and t["rotate"] == first["rotate"]] or [first]
            sz = first["size"] or 0.0
            # The baseline's centre lies CENTRE x size along the text's
            # "up", (0, -1) turned by the rotation (SVG y grows down).
            rot = math.radians(first["rotate"] or 0.0)
            bx = first["x_px"]
            by = sum(t["y_px"] for t in group) / len(group)
            cx = bx + math.sin(rot) * CENTRE * sz
            cy = by - math.cos(rot) * CENTRE * sz
            # A boxed block is centred in its box (a left-justified
            # block's lines start at the box's left edge).
            if rec["boxes"]:
                bx0 = rec["boxes"][0]
                cx = (bx0["left"] + bx0["right"]) / 2.0
                cy = (bx0["top"] + bx0["bottom"]) / 2.0
            rec["point"] = {"x": mx[0](cx), "y": my[0](cy)}
            rec["px_of"] = {"x": mx[1], "y": my[1]}
        probes[pid] = rec
    else:
        probes[pid] = rec


def _direction(pid, pt):
    rec = probes[pid]
    if not rec.get("texts") or not rec.get("px_of"):
        return None
    t = rec["texts"][0]
    px, py = rec["px_of"]["x"](pt[0]), rec["px_of"]["y"](pt[1])
    sz = t["size"] or 0.0
    cy = t["y_px"] - CENTRE * sz
    tol = 0.2 * sz
    if t["anchor"] == "start":
        dx = 1
    elif t["anchor"] == "end":
        dx = -1
    else:
        dx = 0 if abs(t["x_px"] - px) < tol else (1 if t["x_px"] > px else -1)
    dy = 0 if abs(cy - py) < tol else (1 if cy < py else -1)
    return {(0, 1): "n", (1, 1): "ne", (1, 0): "e", (1, -1): "se",
            (0, -1): "s", (-1, -1): "sw", (-1, 0): "w", (-1, 1): "nw",
            (0, 0): "c"}[(dx, dy)]


compass = {}
for tok in Macro.getLocal("pl_spell").split():
    pid, spell = tok.split("=", 1)
    d = _direction(pid, (3000.0, 30.0))
    noted = bool(probes[pid]["notes"])
    probes[pid]["direction"] = d
    compass[spell] = None if noted else d

orient = {}
for tok in Macro.getLocal("or_spell").split():
    pid, spell = tok.split("=", 1)
    rec = probes[pid]
    if rec["rc"] != 0 or rec["notes"] or not rec.get("texts"):
        orient[spell] = None
    else:
        r = rec["texts"][0]["rotate"]
        orient[spell] = 0.0 if r is None else r

for rec in probes.values():
    rec.pop("px_of", None)

out = {"probes": probes,
       "_meta": {"stata_version": Macro.getLocal("stata_version"),
                 "born_date": Macro.getLocal("born_date"),
                 "dash_commit": Macro.getLocal("dash_commit").strip(),
                 "extracted": Macro.getLocal("extracted"),
                 "scheme": "stcolor unless the command names one",
                 "compass": compass, "orient": orient,
                 "centre": CENTRE,
                 "data": ("auto; monthly: t %tm 1995m1-2004m12, tn = t "
                          "unformatted, y = 10 + mod(_n, 7), y2, tsset t; "
                          "daily: d %td from 01jan2001 every 5 days, "
                          "y = 5 + mod(_n, 9)")}}
path = os.path.join(repo, "test", "fixtures", "added_text_truth.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote " + path)
end
