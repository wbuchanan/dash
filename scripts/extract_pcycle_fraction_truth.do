*! extract_pcycle_fraction_truth.do -- WP-31 section 32 (C8d): measure
*! twoway's pcycle() with fractional values on graphs of 1, 2, 3 and 16
*! series: the return code and words, and the p# style each series is
*! drawn in, read from the marker colours of the SVG export against the
*! same graph without pcycle() (s2color's p1..p15 colours are distinct).
*! twoway only: the output is the same before and after dash changes.
*!
*! Output: test/fixtures/pcycle_fraction_truth.json
*!
*! Run through the slot wrapper only:
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_pcycle_fraction_truth.do
*!
*! The git commit is read from a file `shell' wrote, never with shell=True.

clear all
set more off
set linesize 200

local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zp_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zp_bad' {
    display as error "extract_pcycle_fraction_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_pcycle_fraction_truth.do: `_zp_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZP_REPO "`repo'"
global ZP_OUT "${ZP_REPO}/test/fixtures/pcycle_fraction_truth.json"

local work "`c(tmpdir)'dash_pcycle_fraction_probe"
capture mkdir "`work'"
global ZP_WORK "`work'"


quietly shell git -C "${ZP_REPO}" rev-parse HEAD > "${ZP_WORK}/git_head.txt"
global ZP_VERSION "`c(stata_version)'"
global ZP_BORN "`c(born_date)'"
global ZP_WHEN "`c(current_date)' `c(current_time)'"

* _zp_run key cmd: run `cmd' with its printed lines in a log; the rc in
* ZP_RC_<key>; the graph exported to <key>.svg when it drew.
capture program drop _zp_run
program define _zp_run
    gettoken key 0 : 0
    quietly log using "${ZP_WORK}/`key'.log", text replace name(zpref)
    capture noisily `0'
    local rc = _rc
    display as text "{p_end}"
    quietly log close zpref
    global ZP_RC_`key' "`rc'"
    if `rc' == 0 {
        capture graph describe zp1
        if _rc == 0 {
            quietly graph export "${ZP_WORK}/`key'.svg", replace
            graph drop zp1
        }
    }
    global ZP_KEYS "${ZP_KEYS} `key'"
end
global ZP_KEYS ""

sysuse auto, clear
set scheme s2color
local nm "name(zp1, replace)"
forvalues k = 1/16 {
    generate double y`k' = mpg + 10 * `k'
}
foreach n in 1 2 3 4 16 {
    local ys ""
    forvalues k = 1/`n' {
        local ys "`ys' y`k'"
    }
    _zp_run n`n'_none twoway scatter `ys' weight, `nm'
    foreach p in 0 -1 0.5 1 1.2 1.5 2 2.2 2.5 3.5 15.5 16.5 {
        local pk = subinstr(subinstr("`p'", ".", "p", .), "-", "m", .)
        _zp_run n`n'_`pk' twoway scatter `ys' weight, pcycle(`p') `nm'
    }
}

python:
import json, os, re
from sfi import Macro


def G(k):
    return Macro.getGlobal(k)


work = G("ZP_WORK")
_ATTR = re.compile(r'([\w:-]+)="([^"]*)"')
_EL = re.compile(r"<circle\b([^>]*)/?>")


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


def series_fills(path):
    """The fill of each run of 74 markers, in document order."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        txt = fh.read()
    os.remove(path)
    fills = []
    for m in _EL.finditer(txt):
        a = dict(_ATTR.findall(m.group(1)))
        st = dict(p.split(":", 1) for p in a.get("style", "").split(";")
                  if ":" in p)
        f = st.get("fill", "").strip().lower()
        if f and f != "none":
            fills.append(f)
    return [fills[i] for i in range(0, len(fills), 74)]


out = {}
for key in G("ZP_KEYS").split():
    rec = {"rc": int(G("ZP_RC_" + key)), "lines": log_lines(key)}
    svg = os.path.join(work, key + ".svg")
    if os.path.exists(svg):
        rec["fills"] = series_fills(svg)
    out[key] = rec
base = out["n16_none"]["fills"]
for key, rec in out.items():
    if "fills" in rec:
        # p# of each series: the first series of the default graph drawn
        # in its colour (p1..p15 are distinct under s2color).
        rec["pstyle"] = [base.index(f) + 1 if f in base else None
                         for f in rec["fills"]]
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZP_VERSION"), "born_date": G("ZP_BORN"),
                "dash_commit": commit, "extracted": G("ZP_WHEN"),
                "source": "scripts/extract_pcycle_fraction_truth.do"}
with open(G("ZP_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZP_OUT"))
end
