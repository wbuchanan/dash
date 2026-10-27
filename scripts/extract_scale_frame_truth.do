*! extract_scale_frame_truth.do -- WP-33 section 33-11 (GW-11): measure
*! where twoway puts the plot region, the graph region and each text under
*! scale(0.5 0.75 1 1.5 2) for two commands, from twoway's own SVG export
*! (the plot region and graph region are marked by sentinel outline
*! colours), and fit each plot side against the scale factor.  twoway
*! only: the output is the same before and after dash changes.
*!
*!   A  twoway scatter mpg weight, title("T")
*!   B  twoway (scatter mpg weight) (lfit mpg weight), title("T")
*!      subtitle("S") ytitle("Y") xtitle("X") note("N")
*!
*! Output: test/fixtures/scale_frame_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_scale_frame_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zf_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zf_bad' {
    display as error "extract_scale_frame_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zf_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zf_rc' | _rc {
    local _zf_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_scale_frame_truth.do: `_zf_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZF_REPO "`repo'"
global ZF_OUT "${ZF_REPO}/test/fixtures/scale_frame_truth.json"

local work "`c(tmpdir)'dash_scale_frame_probe"
capture mkdir "`work'"
global ZF_WORK "`work'"


quietly shell git -C "${ZF_REPO}" rev-parse HEAD > "${ZF_WORK}/git_head.txt"
global ZF_VERSION "`c(stata_version)'"
global ZF_BORN "`c(born_date)'"
global ZF_WHEN "`c(current_date)' `c(current_time)'"

* _zf_run key cmd: run `cmd'; the rc in ZF_RC_<key>; the graph exported
* to <key>.svg when it drew.  The key is a file name (A_0_5); the fixture
* key (A:0.5) is written by the python block.
capture program drop _zf_run
program define _zf_run
    gettoken key 0 : 0
    capture noisily `0'
    local rc = _rc
    global ZF_RC_`key' "`rc'"
    if `rc' == 0 {
        capture graph describe zf1
        if _rc == 0 {
            quietly graph export "${ZF_WORK}/`key'.svg", replace
            graph drop zf1
        }
    }
    global ZF_KEYS "${ZF_KEYS} `key'"
end
global ZF_KEYS ""

local zf_scheme "`c(scheme)'"
sysuse auto, clear
set scheme s2color
local nm "name(zf1, replace)"
* Sentinels: the plot region's outline #010203, the graph region's #040506.
local sn `"plotregion(lcolor("1 2 3")) graphregion(lcolor("4 5 6"))"'
local cA `"twoway scatter mpg weight, title("T")"'
local cB `"twoway (scatter mpg weight) (lfit mpg weight), title("T") subtitle("S") ytitle("Y") xtitle("X") note("N")"'

foreach c in A B {
    foreach k in 0.5 0.75 1 1.5 2 {
        local kk = subinstr("`k'", ".", "_", .)
        _zf_run `c'_`kk' `c`c'' scale(`k') `sn' `nm'
    }
}
set scheme `zf_scheme'

python:
import json, os, sys
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


sys.path.insert(0, os.path.join(G("ZF_REPO"), "scripts"))
import svg_truth  # noqa: E402
import svg_chrome  # noqa: E402

work = G("ZF_WORK")
SIDES = ("top", "left", "bottom", "right")


def box(r):
    if not r:
        return None
    return {k: round(r[k], 3) for k in SIDES}


def facts(path):
    doc = svg_truth.svg_document(path)
    return {"canvas": {"w": doc["canvas"]["w"], "h": doc["canvas"]["h"]},
            "plot": box(svg_chrome.svg_region(path, "#010203")),
            "graph": box(svg_chrome.svg_region(path, "#040506")),
            "texts": [{"text": d["text"], "x": d["x"], "y": d["y"],
                       "anchor": d["anchor"], "size": d["size"]}
                      for d in doc["texts"]]}


def fit(ks, ys):
    """The least-squares line of ys on ks: slope, intercept and the
    largest absolute residual."""
    n = len(ks)
    mk, my = sum(ks) / n, sum(ys) / n
    sxx = sum((k - mk) ** 2 for k in ks)
    slope = sum((k - mk) * (y - my) for k, y in zip(ks, ys)) / sxx
    icpt = my - slope * mk
    res = max(abs(y - (icpt + slope * k)) for k, y in zip(ks, ys))
    return {"slope": round(slope, 3), "intercept": round(icpt, 3),
            "max_residual": round(res, 3)}


out = {}
for key in G("ZF_KEYS").split():
    cmd, _, kk = key.partition("_")
    fkey = cmd + ":" + kk.replace("_", ".")
    rec = {"rc": int(G("ZF_RC_" + key))}
    svg = os.path.join(work, key + ".svg")
    if os.path.exists(svg):
        rec.update(facts(svg))
        os.remove(svg)
    out[fkey] = rec

rules = {}
for cmd in ("A", "B"):
    recs = sorted(((float(k.split(":")[1]), v) for k, v in out.items()
                   if k.startswith(cmd + ":") and v.get("plot")),
                  key=lambda t: t[0])
    ks = [k for k, _ in recs]
    rules[cmd] = {s: fit(ks, [v["plot"][s] for _, v in recs])
                  for s in SIDES} if len(ks) >= 2 else None
out["rules"] = rules

try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZF_VERSION"), "born_date": G("ZF_BORN"),
                "dash_commit": commit, "extracted": G("ZF_WHEN"),
                "source": "scripts/extract_scale_frame_truth.do"}
with open(G("ZF_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZF_OUT"))
end
