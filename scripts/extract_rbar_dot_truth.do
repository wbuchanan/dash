*! extract_rbar_dot_truth.do -- WP-31 section 03 (C2, B5a): measure the
*! width twoway draws an rbar at with mwidth (its rbarm view: each bar as
*! wide as a marker of its msize()), what msize() does without mwidth,
*! how barwidth() reads beside mwidth, mwidth on histogram, and dot's
*! base() and recast(), so dash's rbar mwidth and dot are proved against
*! twoway itself.
*!
*! Output: test/fixtures/rbar_dot_truth.json
*!
*! Run through the slot wrapper only (CLAUDE.md rule 10):
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_rbar_dot_truth.do
*!
*! METHOD.  sysuse auto with yl = mpg - 1 and yh = mpg + 1, scheme s2color.
*! twoway only: dash is never run, so the fixture is the same before and
*! after dash changes.  rbar: .plot1.style.marker.size.val, .plot1's
*! class name, the SVG bar rects' widths (px), the canvas and ratio =
*! 100 * width / min(W, H).  dot: the y scale (.plotregion1.yscale.curmin
*! and curmax, .yaxis1.major min/delta/max) and the SVG circle count with
*! and without base().  recast() on dot, mwidth on histogram and the
*! refusals: rc and the error line (from a log), and the SVG path, circle
*! and rect counts.  The git commit is read from a file `shell' wrote,
*! never with shell=True.  Every SVG is erased.

clear all
set more off
set linesize 200

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_rbar_dot_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_rbar_dot_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZR_REPO "`repo'"
global ZR_OUT "${ZR_REPO}/test/fixtures/rbar_dot_truth.json"
global dash_nobrowser 1

local work "`c(tmpdir)'dash_rbar_dot_probe"
capture mkdir "`work'"
global ZR_WORK "`work'"


quietly shell git -C "${ZR_REPO}" rev-parse HEAD > "${ZR_WORK}/git_head.txt"
global ZR_VERSION "`c(stata_version)'"
global ZR_BORN "`c(born_date)'"
global ZR_WHEN "`c(current_date)' `c(current_time)'"

sysuse auto, clear
generate yl = mpg - 1
generate yh = mpg + 1
set scheme s2color

* rbar: key | command.  Each graph's marker size, plot class and SVG.
global ZR_RBAR ""
local R1 "plain|twoway rbar yl yh weight"
local R2 "mwidth|twoway rbar yl yh weight, mwidth"
local R3 "mwidth_small|twoway rbar yl yh weight, mwidth msize(small)"
local R4 "mwidth_large|twoway rbar yl yh weight, mwidth msize(large)"
local R5 "mwidth_vlarge|twoway rbar yl yh weight, mwidth msize(vlarge)"
local R6 "mwidth_2|twoway rbar yl yh weight, mwidth msize(2)"
local R7 "msize_only|twoway rbar yl yh weight, msize(large)"
local R8 "mwidth_bw03|twoway rbar yl yh weight, mwidth barwidth(.3)"
local R9 "mwidth_bw3|twoway rbar yl yh weight, mwidth barwidth(3)"
local R10 "spacing|twoway rbar yl yh turn, mwidth"
forvalues k = 1/10 {
    gettoken key rest : R`k', parse("|")
    gettoken bar cmd : rest, parse("|")
    local opt = cond(strpos(`"`cmd'"', ","), " ", ", ")
    quietly `cmd' `opt' name(zr, replace)
    global ZRR_`key'_ms "`.zr.plotregion1.plot1.style.marker.size.val'"
    global ZRR_`key'_cls "`.zr.plotregion1.plot1.classname'"
    quietly graph export "${ZR_WORK}/r_`key'.svg", replace
    global ZR_RBAR "${ZR_RBAR} `key'"
}

* dot base(): the y scale with no base, base(0) and base(50).
global ZR_DOT ""
foreach b in none 0 50 {
    local opt = cond("`b'" == "none", "", "base(`b')")
    quietly twoway dot mpg weight, `opt' name(zr, replace)
    global ZRD_`b' "`.zr.plotregion1.yscale.curmin' `.zr.plotregion1.yscale.curmax' `.zr.yaxis1.major.min' `.zr.yaxis1.major.delta' `.zr.yaxis1.major.max'"
    quietly graph export "${ZR_WORK}/d_`b'.svg", replace
    global ZR_DOT "${ZR_DOT} `b'"
}
quietly twoway line mpg weight, name(zr, replace)
quietly graph export "${ZR_WORK}/d_line.svg", replace
quietly twoway scatter mpg weight, name(zr, replace)
quietly graph export "${ZR_WORK}/d_scatter.svg", replace
quietly twoway histogram mpg, name(zr, replace)
quietly graph export "${ZR_WORK}/h_plain.svg", replace
graph drop _all

* The rc and error line of each probe; an SVG of each that draws.
global ZR_PROBES ""
quietly log using "${ZR_WORK}/probes.log", text replace name(zrlog)
local P1 "dot_recast_line|twoway dot mpg weight, recast(line)"
local P2 "dot_recast_scatter|twoway dot mpg weight, recast(scatter)"
local P3 "histogram_mwidth|twoway histogram mpg, mwidth"
local P4 "rbar_mwidth_twice|twoway rbar yl yh weight, mwidth mwidth"
local P5 "scatter_mwidth|twoway scatter mpg weight, mwidth"
local P6 "bar_mwidth|twoway bar mpg weight, mwidth"
forvalues k = 1/6 {
    gettoken key rest : P`k', parse("|")
    gettoken bar cmd : rest, parse("|")
    display "ZR-MARK `key'"
    capture noisily `cmd' name(zr, replace)
    global ZRP_`key'_rc = _rc
    if _rc == 0 {
        quietly graph export "${ZR_WORK}/p_`key'.svg", replace
        graph drop zr
    }
    display "ZR-END `key'"
    global ZR_PROBES "${ZR_PROBES} `key'"
}
quietly log close zrlog

python:
import json, os, re, sys
from sfi import Macro

G = Macro.getGlobal
sys.path.insert(0, os.path.join(G("ZR_REPO"), "scripts"))
from svg_truth import svg_document  # noqa: E402

work = G("ZR_WORK")
written = []


def _num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def _bar_rects(doc):
    """The bars' widths (px): the narrow rects (under a third of the
    canvas wide) of the commonest fill among them."""
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


def _counts(sp):
    doc = svg_document(sp)
    nl = len(doc["hlines"]) + len(doc["vlines"]) + len(doc["diaglines"])
    return doc, {"paths": len(doc["paths"]), "circles": len(doc["circles"]),
                 "rects": len(doc["rects"]), "lines": nl}


rbar = {}
for key in G("ZR_RBAR").split():
    sp = os.path.join(work, "r_%s.svg" % key)
    written.append(sp)
    doc = svg_document(sp)
    W, H = doc["canvas"]["w"], doc["canvas"]["h"]
    rw = sorted(_bar_rects(doc))
    med = rw[len(rw) // 2] if rw else None
    rbar[key] = {"marker_size_val": _num(G("ZRR_%s_ms" % key)),
                 "classname": G("ZRR_%s_cls" % key),
                 "n_rects": len(rw),
                 "width_px": med,
                 "width_min_px": rw[0] if rw else None,
                 "width_max_px": rw[-1] if rw else None,
                 "canvas": [W, H],
                 "ratio": (100.0 * med / min(W, H)) if med else None}

# barwidth() beside mwidth: does the width track the number as a marker
# size, stay at the mwidth default, or follow x units?
_m = rbar["mwidth"]
_b03, _b3 = rbar["mwidth_bw03"], rbar["mwidth_bw3"]


def _close(a, b, tol=0.02):
    return a is not None and b is not None and abs(a - b) <= tol * max(abs(b), 1e-9)


if _close(_b03["ratio"], 0.3) and _close(_b3["ratio"], 3.0):
    _rule = "marker size"
elif _close(_b03["width_px"], _m["width_px"]) and _close(_b3["width_px"], _m["width_px"]):
    _rule = "ignored"
else:
    _rule = "x units"
rbar["mwidth_barwidth_rule"] = _rule

dot = {}
for b in G("ZR_DOT").split():
    sp = os.path.join(work, "d_%s.svg" % b)
    written.append(sp)
    f = [_num(w) for w in G("ZRD_%s" % b).split()]
    f += [None] * (5 - len(f))
    _d, c = _counts(sp)
    dot["base_" + b] = {"curmin": f[0], "curmax": f[1], "ticks": f[2:5],
                        "svg": c}
for k in ("line", "scatter"):
    sp = os.path.join(work, "d_%s.svg" % k)
    written.append(sp)
    dot["plain_" + k] = _counts(sp)[1]
sp = os.path.join(work, "h_plain.svg")
written.append(sp)
_hd, _hc = _counts(sp)
hist_plain = {"svg": _hc, "widths_px": sorted(set(round(w, 3) for w in _bar_rects(_hd)))}

with open(os.path.join(work, "probes.log"), encoding="utf-8",
          errors="replace") as fh:
    plog = fh.read().splitlines()
written.append(os.path.join(work, "probes.log"))
msgs, cur = {}, None
for ln in plog:
    s = ln.strip()
    m = re.match(r"^ZR-MARK (\S+)$", s)
    if m:
        cur = m.group(1)
        continue
    if re.match(r"^ZR-END ", s):
        cur = None
        continue
    if cur and cur not in msgs and s and not s.startswith(".") \
            and not s.startswith("r(") and not s.startswith("(note"):
        msgs[cur] = s
probes = {}
for key in G("ZR_PROBES").split():
    rc = int(G("ZRP_%s_rc" % key))
    entry = {"rc": rc, "message": msgs.get(key) if rc else None}
    sp = os.path.join(work, "p_%s.svg" % key)
    if rc == 0 and os.path.exists(sp):
        written.append(sp)
        pd, entry["svg"] = _counts(sp)
        if key == "histogram_mwidth":
            entry["widths_px"] = sorted(set(round(w, 3) for w in _bar_rects(pd)))
    probes[key] = entry
probes["histogram_plain"] = hist_plain

try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
written.append(os.path.join(work, "git_head.txt"))
out = {"rbar": rbar, "dot": dot, "probes": probes,
       "_meta": {"stata_version": G("ZR_VERSION"), "born_date": G("ZR_BORN"),
                 "dash_commit": commit, "extracted": G("ZR_WHEN"),
                 "source": "scripts/extract_rbar_dot_truth.do"}}
with open(G("ZR_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
for p in written:
    try:
        os.remove(p)
    except OSError:
        pass
print("wrote", G("ZR_OUT"))
end
