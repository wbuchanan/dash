*! extract_emptied_layer_truth.do -- WP-29 section 12 (P0.18): measure the
*! legend key style twoway draws for a computed, bar or range layer that its
*! own if leaves with 0, 1 or 2 observations, so dash's emptied layers are
*! proved against a live twoway export, not modelled.
*!
*! Output: test/fixtures/emptied_layer_truth.json
*!
*! Run through the slot wrapper only (CLAUDE.md rule 10):
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_emptied_layer_truth.do
*!
*! METHOD.  The ten rows of test_mode_parity._DF are typed with input.  For
*! each scheme (s2color, s1mono) the base graph `twoway scatter mpg weight,
*! legend(on)' is exported to SVG, then for each type the populated
*! reference `twoway (scatter mpg weight) (<type> <vars>)' and the probes
*! `... (<type> <vars> if <q>)' for q in price > 20000 (rows0), price >=
*! 11385 (rows1) and price >= 10000 (rows2), each under capture noisily with
*! its rc, exported only when rc is 0.  A trailing python: block reads each
*! SVG's (stroke, stroke-width) pairs; a probe's key_styles is its set minus
*! the base set; base_has_no_layer_colour compares (colour, width) pairs.
*! It never calls back into Stata: the git commit is read
*! from a file `shell' wrote, never with shell=True.  Every SVG is erased.

clear all
set more off
set linesize 200

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_emptied_layer_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_emptied_layer_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZE_REPO "`repo'"
global ZE_OUT "${ZE_REPO}/test/fixtures/emptied_layer_truth.json"

adopath ++ "${ZE_REPO}"
quietly do "${ZE_REPO}/dash_parse.mata"
quietly do "${ZE_REPO}/dash.ado"
global dash_nobrowser 1

local work "`c(tmpdir)'dash_emptied_probe"
capture mkdir "`work'"
global ZE_WORK "`work'"


quietly shell git -C "${ZE_REPO}" rev-parse HEAD > "${ZE_WORK}/git_head.txt"
global ZE_VERSION "`c(stata_version)'"
global ZE_BORN "`c(born_date)'"
global ZE_WHEN "`c(current_date)' `c(current_time)'"

input mpg weight foreign price
22 2930 0 4099
17 3350 1 4749
25 2200 0 3799
30 1800 1 4816
21 3000 0 5788
19 3100 1 4453
14 4080 0 5189
28 2010 1 10372
16 3600 0 4082
23 2650 1 11385
end

global ZE_TYPES "lfit qfit fpfit lowess lpoly mband mspline bar rarea rbar rspike histogram kdensity"
global ZE_SCHEMES "s2color s1mono"
global ZE_Q_rows0 "price > 20000"
global ZE_Q_rows1 "price >= 11385"
global ZE_Q_rows2 "price >= 10000"

foreach sch of global ZE_SCHEMES {
    set scheme `sch'
    quietly twoway scatter mpg weight, legend(on)
    quietly graph export "${ZE_WORK}/base_`sch'.svg", replace
    foreach t of global ZE_TYPES {
        local vars "mpg weight"
        if inlist("`t'", "rarea", "rbar", "rspike") local vars "mpg price weight"
        if inlist("`t'", "histogram", "kdensity") local vars "mpg"
        capture noisily twoway (scatter mpg weight) (`t' `vars')
        global ZR_`sch'_`t'_p = _rc
        if _rc == 0 quietly graph export "${ZE_WORK}/`sch'_`t'_populated.svg", replace
        foreach k in rows0 rows1 rows2 {
            capture noisily twoway (scatter mpg weight) (`t' `vars' if ${ZE_Q_`k'})
            global ZR_`sch'_`t'_`k' = _rc
            if _rc == 0 quietly graph export "${ZE_WORK}/`sch'_`t'_`k'.svg", replace
        }
    }
}
graph drop _all

python:
import json, os, re
from sfi import Macro

G = Macro.getGlobal
work = G("ZE_WORK")
pat = re.compile(r"stroke:(#[0-9A-Fa-f]{6});stroke-width:([0-9.]+)")


def styles(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return {(c.lower(), float(w)) for c, w in pat.findall(fh.read())}


types = G("ZE_TYPES").split()
out = {"schemes": {}}
written = []
for sch in G("ZE_SCHEMES").split():
    bp = os.path.join(work, "base_%s.svg" % sch)
    base = styles(bp)
    written.append(bp)
    probes = {}
    for t in types:
        entry = {}
        for k in ("populated", "rows0", "rows1", "rows2"):
            rc = int(G("ZR_%s_%s_%s" % (sch, t, "p" if k == "populated" else k)))
            e = {"rc": rc}
            if k != "populated":
                e["qualifier"] = G("ZE_Q_" + k)
            sp = os.path.join(work, "%s_%s_%s.svg" % (sch, t, k))
            if rc == 0 and os.path.exists(sp):
                e["key_styles"] = [list(p) for p in sorted(styles(sp) - base)]
                written.append(sp)
            else:
                e["key_styles"] = None
            entry[k] = e
        probes[t] = entry
    out["schemes"][sch] = {"base_styles": [list(p) for p in sorted(base)],
                           "probes": probes}

check = "held"
for sch, d in out["schemes"].items():
    for t, e in d["probes"].items():
        if t == "histogram":
            continue
        pop = {tuple(p) for p in (e["populated"]["key_styles"] or [])}
        for k in ("rows0", "rows1", "rows2"):
            ks = e[k]["key_styles"]
            if e[k]["rc"] == 0 and ks is not None \
                    and not {tuple(p) for p in ks} <= pop:
                if check == "held":
                    check = "failed: %s/%s/%s" % (sch, t, k)
basecheck = "held"
for sch, d in out["schemes"].items():
    # (colour, width) pairs, not colour alone (maintainer ruling,
    # 01oct2026): s1mono keys mband and mspline in the black its base
    # scatter outlines in, at another width.
    bpairs = {(c, w) for c, w in d["base_styles"]}
    for t, e in d["probes"].items():
        for k in ("rows0", "rows1", "rows2"):
            for c, w in (e[k]["key_styles"] or []):
                if (c, w) in bpairs and basecheck == "held":
                    basecheck = "failed: %s/%s/%s" % (sch, t, k)
try:
    with open(os.path.join(work, "git_head.txt")) as fh:
        commit = fh.read().strip()
except OSError:
    commit = ""
out["_meta"] = {"stata_version": G("ZE_VERSION"), "born_date": G("ZE_BORN"),
                "dash_commit": commit, "extracted": G("ZE_WHEN"),
                "source": "scripts/extract_emptied_layer_truth.do",
                "empty_matches_populated": check,
                "base_has_no_layer_colour": basecheck}
with open(G("ZE_OUT"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
for p in written:
    try:
        os.remove(p)
    except OSError:
        pass
try:
    os.remove(os.path.join(work, "git_head.txt"))
except OSError:
    pass
print("wrote", G("ZE_OUT"), "empty_matches_populated:", check,
      "base_has_no_layer_colour:", basecheck)
end
