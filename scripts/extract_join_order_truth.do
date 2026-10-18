* extract_join_order_truth.do -- Stata's own join order for line, connected,
* area, rline, rarea and rconnected (WP-29 P0.1, section 02), written to
* test/fixtures/join_order_truth.json for test/test_join_order.py.
*
* Records: the serset order of each command on dataset A (J1-J7, J10, J11),
* the per-panel serset order under by() (J9), the vertex x of every drawn
* path of the SVG on dataset B, which holds missing values (J8), and the rank
* per observation that dash's _dash_sort_gen makes for each sort() key.
*
* Run (never the GUI; the slot wrapper of scripts/stata_slot.sh):
*   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_join_order_truth.do
* The SVG files are written to the current directory (the slot wrapper's
* scratch directory).

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_join_order_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_join_order_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1

clear all
set more off
version 19

local stata_version = c(stata_version)
local born_date "`c(born_date)'"
tempfile gh
shell git -C "`repo'" rev-parse HEAD > "`gh'"
tempname fh
file open `fh' using "`gh'", read text
file read `fh' dash_commit
file close `fh'
local extracted "`c(current_date)'"
local svgdir "`c(pwd)'"

capture program drop _jo_obs
program _jo_obs, rclass
    // The current serset's observations, read from y = 100 * obs.
    preserve
    serset use, clear
    local o
    forvalues i = 1/`=_N' {
        local o `o' `=round(y[`i'] / 100)'
    }
    restore
    return local obs `"`o'"'
end

capture program drop _jo_dataA
program _jo_dataA
    clear
    quietly set obs 8
    generate double obs = _n
    generate double x = .
    generate double z = .
    generate str1 s = ""
    generate double zz = .
    generate double keyw = 9 - _n
    generate double g = .
    generate double t = .
    local xs  4 1 3 2 8 5 7 6
    local zs  3 .b 1 .a 2 . 5 4
    local ss  `""b" "B" "a" "" "_" "A" "C" "c""'
    local zzs 2 1 2 1 1 2 1 2
    local gs  1 2 1 2 . 1 2 1
    local ts  3 8 1 6 2 7 4 5
    forvalues i = 1/8 {
        quietly replace x  = `: word `i' of `xs''  in `i'
        quietly replace z  = `: word `i' of `zs''  in `i'
        quietly replace s  = `"`: word `i' of `ss''"' in `i'
        quietly replace zz = `: word `i' of `zzs'' in `i'
        quietly replace g  = `: word `i' of `gs''  in `i'
        quietly replace t  = `: word `i' of `ts''  in `i'
    }
    generate double y  = 100 * obs
    generate double y2 = y + 1
end

capture program drop _jo_dataB
program _jo_dataB
    clear
    quietly set obs 7
    generate double x   = .
    generate double y   = .
    generate double y2a = .
    generate double y2b = .
    local xs  2 5 3 6 1 . 7
    local ys  10 20 . 40 50 45 60
    local as  11 . 31 41 51 46 61
    local bs  11 21 . 41 51 46 61
    forvalues i = 1/7 {
        quietly replace x   = `: word `i' of `xs'' in `i'
        quietly replace y   = `: word `i' of `ys'' in `i'
        quietly replace y2a = `: word `i' of `as'' in `i'
        quietly replace y2b = `: word `i' of `bs'' in `i'
    }
end

tempfile recs
tempname rh
file open `rh' using "`recs'", write text replace

* ---- orders: J1-J7, J10 on dataset A --------------------------------------
_jo_dataA
local types line connected area rline rarea rconnected
local J_opts1 ""
local J_opts2 "sort"
local J_opts3 "sort(z)"
local J_opts4 "sort(s)"
local J_opts5 "sort(zz x)"
local J_opts6 "sort sort(z)"
local J_opts7 "sort(z) sort(x)"
foreach j in 1 2 3 4 5 6 7 {
    foreach t of local types {
        if inlist("`t'", "rline", "rarea", "rconnected") local v "y y2 x"
        else local v "y x"
        serset clear
        graph drop _all
        local cmd "twoway `t' `v', `J_opts`j'' nodraw"
        `cmd'
        _jo_obs
        file write `rh' "orders|J`j'-`t'|`t'|`J_opts`j''|`cmd'|`r(obs)'" _n
    }
}
foreach q in in if {
    if "`q'" == "in" local qual "in 2/6"
    else local qual "if g==1"
    foreach t of local types {
        if inlist("`t'", "rline", "rarea", "rconnected") local v "y y2 x"
        else local v "y x"
        serset clear
        graph drop _all
        local cmd "twoway `t' `v' `qual', nodraw"
        `cmd'
        _jo_obs
        file write `rh' "orders|J10-`q'-`t'|`t'|`qual'|`cmd'|`r(obs)'" _n
    }
}

* ---- orders: J11 tsline / tsrline in time order ---------------------------
quietly tsset t
sort obs
foreach t in tsline tsrline {
    if "`t'" == "tsrline" local v "y y2"
    else local v "y"
    foreach o in none sort sorty {
        if "`o'" == "none" local op ""
        if "`o'" == "sort" local op "sort"
        if "`o'" == "sorty" local op "sort(y)"
        serset clear
        graph drop _all
        local cmd "twoway `t' `v', `op' nodraw"
        `cmd'
        _jo_obs
        file write `rh' "orders|J11-`t'-`o'|`t'|`op'|`cmd'|`r(obs)'" _n
    }
}
quietly tsset, clear
sort obs

* ---- by: J9 per-panel sersets ---------------------------------------------
foreach t in line rline {
    if "`t'" == "rline" local v "y y2 x"
    else local v "y x"
    foreach b in by total totalmissing {
        if "`b'" == "by" local bo "by(g)"
        if "`b'" == "total" local bo "by(g, total)"
        if "`b'" == "totalmissing" local bo "by(g, total missing)"
        foreach so in none sort {
            local sx ""
            if "`so'" == "sort" local sx "sort"
            serset clear
            graph drop _all
            local cmd "twoway `t' `v', `bo' `sx' nodraw"
            `cmd'
            local panels ""
            forvalues k = 0/40 {
                capture serset set `k'
                if !_rc {
                    _jo_obs
                    local panels `"`panels';`r(obs)'"'
                }
            }
            file write `rh' "by|J9-`t'-`b'-`so'|`t'|`bo' `sx'|`cmd'|`panels'" _n
        }
    }
}

* ---- ranks: _dash_sort_gen's rule ------------------------------------------
foreach k in z s zzx keyw x {
    local key "`k'"
    if "`k'" == "zzx" local key "zz x"
    sort obs
    tempvar o r
    generate double `o' = _n
    sort `key' `o'
    generate double `r' = _n
    sort `o'
    local rk ""
    forvalues i = 1/8 {
        local rk `rk' `=`r'[`i']'
    }
    drop `o' `r'
    file write `rh' "ranks|`key'|||sort `key' obs|`rk'" _n
}

* ---- missing: J8 SVG paths on dataset B -------------------------------------
_jo_dataB
local j8a `""line y x" "connected y x" "area y x" "rline y y2a x" "rconnected y y2a x" "rarea y y2a x""'
local n = 0
foreach set in a b {
    if "`set'" == "a" local cmds `"`j8a'"'
    else local cmds `""rarea y y2b x""'
    foreach c of local cmds {
        local t : word 1 of `c'
        foreach so in none sort {
            local sx ""
            if "`so'" == "sort" local sx "sort"
            local ++n
            serset clear
            graph drop _all
            local cmd "twoway `c', `sx' xscale(range(0 8)) xlabel(0(2)8)"
            `cmd'
            local svg "`svgdir'/j8_`n'.svg"
            quietly graph export "`svg'", replace
            file write `rh' "missing|J8`set'-`t'-`so'|`t'|`sx'|`cmd'|`svg'" _n
        }
    }
}
file close `rh'

python:
import json, os, re, sys
from sfi import Macro
repo = Macro.getLocal("repo")
sys.path.insert(0, os.path.join(repo, "scripts"))
import svg_truth

def _svg_xs(path):
    reading = svg_truth.svg_axis_reading(path, "x")
    pairs = reading.get("pairs") or []
    if len(pairs) < 2:
        raise ValueError("no x axis pairs in " + path)
    n = float(len(pairs))
    mx = sum(p for p, _ in pairs) / n
    mv = sum(v for _, v in pairs) / n
    b = (sum((p - mx) * (v - mv) for p, v in pairs)
         / sum((p - mx) ** 2 for p, _ in pairs))
    a = mv - b * mx
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    paths = []
    for d in re.findall(r'<path[^>]*\sd="([^"]*)"', text):
        nums = re.findall(r"[ML]\s*(-?[0-9.]+)\s+(-?[0-9.]+)", d)
        xs = []
        for px, _py in nums:
            v = a + b * float(px)
            if abs(v - round(v)) > 1e-3:
                raise ValueError("vertex x %r is not an integer in %s" % (v, path))
            xs.append(int(round(v)))
        paths.append(xs)
    return paths

out = {"orders": [], "by": [], "missing": [], "ranks": {}}
with open(Macro.getLocal("recs"), encoding="utf-8") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if not line:
            continue
        kind, rid, ptype, opt, cmd, val = line.split("|", 5)
        if kind == "orders":
            out["orders"].append({"id": rid, "type": ptype, "option": opt,
                                  "command": cmd,
                                  "obs": [int(v) for v in val.split()]})
        elif kind == "by":
            panels = [[int(v) for v in p.split()] for p in val.split(";")[1:]]
            out["by"].append({"id": rid, "type": ptype, "option": opt,
                              "command": cmd, "panels": panels})
        elif kind == "missing":
            out["missing"].append({"id": rid, "type": ptype, "option": opt,
                                   "command": cmd, "paths": _svg_xs(val)})
        elif kind == "ranks":
            out["ranks"][rid] = [int(float(v)) for v in val.split()]
out["_meta"] = {"stata_version": Macro.getLocal("stata_version"),
                "born_date": Macro.getLocal("born_date"),
                "source": "scripts/extract_join_order_truth.do",
                "dash_commit": Macro.getLocal("dash_commit").strip(),
                "extracted": Macro.getLocal("extracted")}
path = os.path.join(repo, "test", "fixtures", "join_order_truth.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2, sort_keys=True)
    fh.write("\n")
print("wrote " + path)
end
