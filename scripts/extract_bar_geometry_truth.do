*! extract_bar_geometry_truth.do -- WP-30 section 14 (P1.17a): measure the
*! width twoway draws a bar and a range bar at, and the cap rcap draws, so
*! dash's bar widths and range caps are proved against twoway itself.
*!
*! Output: test/fixtures/bar_geometry_truth.json
*!
*! Run through the slot wrapper only (CLAUDE.md rule 10):
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_bar_geometry_truth.do
*!
*! METHOD.  Five rows typed with input (x at spacing 1, .1, 5 and uneven;
*! %td weekly and daily dates; %tm months).  It is twoway-only: dash is
*! never run, so the fixture is the same before and after dash changes.
*! widths: each bar or rbar graph's .plot1.bar_size, and the SVG rects'
*! width in x units (a numeric x label format, so a date axis reads in the
*! variable's own units).  caps: each rcap graph's horizontal cap lines
*! (the spines' stroke), the canvas, ratio = 100 * cap / min(W, H), and
*! .plot1.style.marker.size.val.  rcapsym: its cap lines (0), spines and
*! markers.  refusals: the rc and error line of barwidth() on each type.
*! The git commit is read from a file `shell' wrote, never with
*! shell=True.  Every SVG is erased.

clear all
set more off
set linesize 200

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_bar_geometry_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_bar_geometry_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global BG_REPO "`repo'"
global BG_OUT "${BG_REPO}/test/fixtures/bar_geometry_truth.json"

adopath ++ "${BG_REPO}"
global dash_nobrowser 1

local work "`c(tmpdir)'dash_bargeom_probe"
capture mkdir "`work'"
global BG_WORK "`work'"

if `"`c(python_exec)'"' == "" {
    display as error "extract_bar_geometry_truth.do needs Python (c(python_exec) is empty)"
    exit 601
}

quietly shell git -C "${BG_REPO}" rev-parse HEAD > "${BG_WORK}/git_head.txt"
global BG_VERSION "`c(stata_version)'"
global BG_BORN "`c(born_date)'"
global BG_WHEN "`c(current_date)' `c(current_time)'"

input x1 xp1 x5 xu y lo hi
1 .1 5 1 3 1 4
2 .2 10 1.5 4 2 5
3 .3 15 4 2 1 3
4 .4 20 10 5 3 6
5 .5 25 11 1 0 2
end
generate d = 14975 + 7 * (_n - 1)
format d %td
generate dd = 14975 + (_n - 1)
format dd %td
generate m = 720 + (_n - 1)
format m %tm

set scheme s2color
global BG_WIDTHS ""
* key | command | the x variable (its label format is made numeric)
local W1 "bar_s1|twoway bar y x1|x1"
local W2 "bar_s01|twoway bar y xp1|xp1"
local W3 "bar_s5|twoway bar y x5|x5"
local W4 "bar_su|twoway bar y xu|xu"
local W5 "rbar_s1|twoway rbar lo hi x1|x1"
local W6 "rbar_s5|twoway rbar lo hi x5|x5"
local W7 "rbar_bw03|twoway rbar lo hi x1, barwidth(.3)|x1"
local W8 "bar_td_weekly|twoway bar y d|d"
local W9 "bar_td_weekly_bw3|twoway bar y d, barwidth(3)|d"
local W10 "bar_td_daily|twoway bar y dd|dd"
local W11 "bar_tm|twoway bar y m|m"
local W12 "bar_tm_bw05|twoway bar y m, barwidth(.5)|m"
local W13 "rbar_tm|twoway rbar lo hi m|m"
forvalues k = 1/13 {
    gettoken key rest : W`k', parse("|")
    gettoken bar rest : rest, parse("|")
    gettoken cmd rest : rest, parse("|")
    gettoken bar xv : rest, parse("|")
    gettoken bar xv : xv, parse("|")
    local opt = cond(strpos(`"`cmd'"', ","), " ", ", ")
    quietly `cmd' `opt' xlabel(, format(%12.2f)) name(bg, replace)
    global BGW_`key'_bs = `.bg.plotregion1.plot1.bar_size'
    quietly graph export "${BG_WORK}/w_`key'.svg", replace
    global BG_WIDTHS "${BG_WIDTHS} `key'"
}

global BG_CAPS ""
local C1 "rcap_default|twoway rcap lo hi x1"
local C2 "rcap_tiny|twoway rcap lo hi x1, msize(tiny)"
local C3 "rcap_small|twoway rcap lo hi x1, msize(small)"
local C4 "rcap_medium|twoway rcap lo hi x1, msize(medium)"
local C5 "rcap_large|twoway rcap lo hi x1, msize(large)"
local C6 "rcap_vlarge|twoway rcap lo hi x1, msize(vlarge)"
local C7 "rcap_n2|twoway rcap lo hi x1, msize(2)"
local C8 "rcap_x2|twoway rcap lo hi x1, msize(*2)"
local C9 "rcap_s5|twoway rcap lo hi x5"
local C10 "rcap_wide|twoway rcap lo hi x1, xsize(11) ysize(4)"
local C11 "rcap_stcolor|twoway rcap lo hi x1, scheme(stcolor)"
forvalues k = 1/11 {
    gettoken key rest : C`k', parse("|")
    gettoken bar cmd : rest, parse("|")
    local opt = cond(strpos(`"`cmd'"', ","), " ", ", ")
    quietly `cmd' `opt' name(bg, replace)
    global BGC_`key'_ms = `.bg.plotregion1.plot1.style.marker.size.val'
    quietly graph export "${BG_WORK}/c_`key'.svg", replace
    global BG_CAPS "${BG_CAPS} `key'"
}
quietly twoway rcapsym lo hi x1, name(bg, replace)
global BGS_default_ms = `.bg.plotregion1.plot1.style.marker.size.val'
quietly graph export "${BG_WORK}/s_default.svg", replace
quietly twoway rcapsym lo hi x1, scheme(stcolor) name(bg, replace)
global BGS_stcolor_ms = `.bg.plotregion1.plot1.style.marker.size.val'
quietly graph export "${BG_WORK}/s_stcolor.svg", replace
graph drop _all

global BG_REFUSALS ""
quietly log using "${BG_WORK}/refusals.log", text replace name(bgref)
foreach t in rcap rcapsym rspike rscatter rarea rline rconnected scatter line spike dropline area {
    local vars "lo hi x1"
    if inlist("`t'", "scatter", "line", "spike", "dropline", "area") local vars "y x1"
    display "BGR-MARK `t'"
    capture noisily twoway `t' `vars', barwidth(.5)
    global BGR_`t'_rc = _rc
    global BG_REFUSALS "${BG_REFUSALS} `t'"
}
foreach w in barw barwi bw {
    display "BGR-MARK rcap_`w'"
    capture noisily twoway rcap lo hi x1, `w'(.5)
    global BGR_rcap_`w'_rc = _rc
    global BG_REFUSALS "${BG_REFUSALS} rcap_`w'"
}
quietly log close bgref
graph drop _all
python:
import json, os, re, sys
from sfi import Macro

G = Macro.getGlobal
sys.path.insert(0, os.path.join(G("BG_REPO"), "scripts"))
from svg_truth import svg_document, svg_axis_reading  # noqa: E402

work = G("BG_WORK")
written = []


def _plot_rects(doc):
    """The bars' widths: the narrow rects (under a third of the canvas
    wide) of the commonest fill among them."""
    cw = doc["canvas"]["w"]
    narrow = [r for r in doc["rects"] if r["w"] and r["h"]
              and 0 < r["w"] < cw / 3.0 and r["h"] > 0]
    fills = {}
    for r in narrow:
        fills[r["fill"]] = fills.get(r["fill"], 0) + 1
    if not fills:
        return []
    f = max(fills, key=fills.get)
    return [r["w"] for r in narrow if r["fill"] == f]


widths = {}
for key in G("BG_WIDTHS").split():
    sp = os.path.join(work, "w_%s.svg" % key)
    written.append(sp)
    doc = svg_document(sp)
    rd = svg_axis_reading(sp, "x", doc=doc)
    fit = rd.get("fit")
    upp = abs(fit["units_per_px"]) if fit else None
    rw = _plot_rects(doc)
    svg_w = (sorted(rw)[len(rw) // 2] * upp) if (rw and upp) else None
    widths[key] = {"bar_size": float(G("BGW_%s_bs" % key)),
                   "svg_width_x_units": svg_w}


def _caps(sp):
    """A cap is a horizontal line centred on a spine's x at one of its
    ends; a spine is a vertical line with a cap at an end."""
    doc = svg_document(sp)
    W, H = doc["canvas"]["w"], doc["canvas"]["h"]
    caps, spines = [], set()
    for k, v in enumerate(doc["vlines"]):
        found = []
        for e in (v["y1"], v["y2"]):
            for h in doc["hlines"]:
                mid = (h["x1"] + h["x2"]) / 2.0
                if abs(mid - v["x1"]) < 0.5 and abs(h["y1"] - e) < 0.5 \
                        and abs(h["x2"] - h["x1"]) > 0:
                    found.append(abs(h["x2"] - h["x1"]))
                    break
        # A spine has a cap at BOTH ends (an axis line meeting a tick
        # has one).
        if len(found) == 2:
            caps.extend(found)
            spines.add(k)
    return doc, W, H, sorted(spines), caps


caps = {}
for key in G("BG_CAPS").split():
    sp = os.path.join(work, "c_%s.svg" % key)
    written.append(sp)
    doc, W, H, spines, cl = _caps(sp)
    cap = (sorted(cl)[len(cl) // 2]) if cl else None
    caps[key] = {"cap_svg": cap, "canvas": [W, H],
                 "ratio": (100.0 * cap / min(W, H)) if cap else None,
                 "marker_size_val": float(G("BGC_%s_ms" % key)),
                 "n_caps": len(cl), "n_spines": len(spines)}

rcapsym = {}
for key in ("default", "stcolor"):
    sp = os.path.join(work, "s_%s.svg" % key)
    written.append(sp)
    doc, W, H, spines, cl = _caps(sp)
    # A spine runs from one end marker's centre to the other's.
    cs = [(c["cx"], c["cy"]) for c in doc["circles"]
          if c["cx"] is not None and c["cy"] is not None]

    def _at(x, y):
        return any(abs(x - cx) < 0.5 and abs(y - cy) < 0.5 for cx, cy in cs)

    nsp = sum(1 for v in doc["vlines"]
              if _at(v["x1"], v["y1"]) and _at(v["x2"], v["y2"]))
    rcapsym[key] = {"cap_lines": len(cl), "spines": nsp,
                    "circles": len(doc["circles"]),
                    "marker_size_val": float(G("BGS_%s_ms" % key))}

with open(os.path.join(work, "refusals.log"), encoding="utf-8",
          errors="replace") as fh:
    rlog = fh.read().splitlines()
written.append(os.path.join(work, "refusals.log"))
msgs, cur = {}, None
for ln in rlog:
    m = re.match(r"^BGR-MARK (\S+)\s*$", ln.strip())
    if m:
        cur = m.group(1)
        continue
    if cur and cur not in msgs and ln.strip().startswith("option "):
        msgs[cur] = ln.strip()
refusals = {}
for key in G("BG_REFUSALS").split():
    refusals[key] = {"rc": int(G("BGR_%s_rc" % key)),
                     "message": msgs.get(key)}

try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
written.append(os.path.join(work, "git_head.txt"))
out = {"widths": widths, "caps": caps, "rcapsym": rcapsym,
       "refusals": refusals,
       "_meta": {"stata_version": G("BG_VERSION"), "born_date": G("BG_BORN"),
                 "source": "scripts/extract_bar_geometry_truth.do",
                 "dash_commit": commit, "extracted": G("BG_WHEN")}}
with open(G("BG_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
for p in written:
    try:
        os.remove(p)
    except OSError:
        pass
print("wrote", G("BG_OUT"))
end
