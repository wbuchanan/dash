* extract_embedded_rows_truth.do -- twoway's sersets and Stata's counts,
* levels and means for WP-29 P0.11 (what a saved page holds), written to
* test/fixtures/embedded_rows_truth.json for test/test_embedded_rows.py.
*
* Run (never the GUI; the slot wrapper of scripts/stata_slot.sh):
*   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_embedded_rows_truth.do
* The tree is DASH_REPO, else the current directory when it is a dash tree.

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_embedded_rows_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_embedded_rows_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZA_REPO "`repo'"

clear all
set more off

local stata_version = c(stata_version)
local born_date "`c(born_date)'"
tempfile gh
shell git -C "${ZA_REPO}" rev-parse HEAD > "`gh'"
tempname fh
file open `fh' using "`gh'", read text
file read `fh' dash_commit
file close `fh'
local extracted "`c(current_date)'"

* ---- p1: two layers with their own if --------------------------------------
sysuse auto, clear
local p1_cmd "twoway (scatter mpg weight if foreign) (scatter mpg weight if price>10000), nodraw"
twoway (scatter mpg weight if foreign) (scatter mpg weight if price>10000), nodraw
serset set 0
serset
local p1_n0 = r(N)
serset set 1
serset
local p1_n1 = r(N)
gen long obs = _n
quietly levelsof obs if foreign, local(p1_l0) separate(,)
quietly levelsof obs if price>10000, local(p1_l1) separate(,)
quietly levelsof obs if foreign | price>10000, local(p1_u) separate(,)
quietly count if foreign | price>10000
local p1_un = r(N)

* ---- p2: missing values stay selected ---------------------------------------
sysuse auto, clear
local p2_cmd "twoway scatter rep78 weight if !foreign, nodraw"
twoway scatter rep78 weight if !foreign, nodraw
serset set 0
serset
local p2_n = r(N)
quietly count if !foreign
local p2_c = r(N)
quietly count if !foreign & !missing(rep78)
local p2_nm = r(N)

* ---- p3: by() panels --------------------------------------------------------
sysuse auto, clear
local p3_single_cmd "twoway (scatter mpg weight if foreign==0), by(foreign)"
local p3_two_cmd "twoway (scatter mpg weight if foreign==0) (scatter mpg weight if price>15000), by(foreign)"
local p3_with_all_cmd "twoway (scatter mpg weight if foreign==0) (scatter mpg weight), by(foreign)"
tempfile svg_single svg_two svg_with_all
foreach k in single two with_all {
    graph drop _all
    serset clear
    `p3_`k'_cmd'
    graph export "`svg_`k''.svg", as(svg) replace
    local p3_`k'_svg "`svg_`k''.svg"
    serset dir
    local p3_`k'_ns ""
    forvalues s = 0/20 {
        capture serset set `s'
        if _rc continue
        serset
        local p3_`k'_ns "`p3_`k'_ns' `r(N)'"
    }
}
graph drop _all
local lab0 : label (foreign) 0
local lab1 : label (foreign) 1

* ---- p4: auto widget and card values ----------------------------------------
sysuse auto, clear
quietly summarize price if foreign
local p4_pf_min = r(min)
local p4_pf_max = r(max)
quietly summarize price
local p4_pa_min = r(min)
local p4_pa_max = r(max)
quietly levelsof rep78 if foreign, local(p4_rf) separate(,)
quietly levelsof rep78, local(p4_ra) separate(,)
quietly summarize mpg if foreign | price > 10000
local p4_mu : display %21.17g r(mean)
local p4_mu_t : display %9.0g r(mean)
quietly count if foreign==1 in 40/60
local p4_c4060 = r(N)

* ---- p5: the parity frame (test_mode_parity._DF) ----------------------------
clear
input double(mpg weight foreign price)
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
quietly summarize price if price > 4500
local p5_min = r(min)
local p5_max = r(max)
quietly levelsof price if price > 4500, local(p5_lv) separate(,)
foreach k in fi38 i38 f all {
    if "`k'" == "fi38" local c "if foreign == 1 in 3/8"
    if "`k'" == "i38" local c "in 3/8"
    if "`k'" == "f" local c "if foreign == 1"
    if "`k'" == "all" local c ""
    quietly summarize mpg `c'
    local p5_`k'_m : display %21.17g r(mean)
    local p5_`k'_t : display %9.0g r(mean)
    local p5_`k'_cmd "summarize mpg `c'"
}

* ---- p6: lowess adjust reads the whole data ---------------------------------
sysuse auto, clear
local p6_cmd "twoway lowess mpg weight if foreign, adjust nodraw"
serset clear
twoway lowess mpg weight if foreign, adjust nodraw
serset set 0
serset use, clear
describe
quietly ds
local p6_y : word 1 of `r(varlist)'
quietly summarize `p6_y'
local p6_m : display %21.17g r(mean)
local p6_t : display %9.0g r(mean)

python:
import json, os, sys
from sfi import Macro
repo = Macro.getGlobal("ZA_REPO")
sys.path.insert(0, os.path.join(repo, "scripts"))
import svg_truth


def L(name):
    return Macro.getLocal(name)


def nums(text):
    return [float(x) for x in text.split(",") if x.strip() != ""]


def rec(mean_name, text_name, cmd):
    return {"mean": float(L(mean_name)), "text": L(text_name).strip(),
            "command": cmd}


labels = {L("lab0"), L("lab1")}
out = {}
u = [int(x) for x in nums(L("p1_u"))]
out["p1"] = {"command": L("p1_cmd"),
             "serset_n": [int(L("p1_n0")), int(L("p1_n1"))],
             "layer_obs": [[int(x) for x in nums(L("p1_l0"))],
                           [int(x) for x in nums(L("p1_l1"))]],
             "union_obs": u, "union_n": int(L("p1_un"))}
out["p2"] = {"command": L("p2_cmd"), "serset_n": int(L("p2_n")),
             "count_if": int(L("p2_c")),
             "count_nonmissing": int(L("p2_nm"))}
p3 = {}
for k in ("single", "two", "with_all"):
    path = L("p3_" + k + "_svg")
    subs = [t["text"] for t in svg_truth.svg_texts(path)
            if t["text"] in labels]
    seen = []
    for s in subs:
        if s not in seen:
            seen.append(s)
    p3[k] = {"command": L("p3_" + k + "_cmd"), "subtitles": seen,
             "serset_n": [int(x) for x in L("p3_" + k + "_ns").split()]}
    os.remove(path)
out["p3"] = p3
out["p4"] = {"command": "sysuse auto; summarize price [if foreign]; "
                        "levelsof rep78 [if foreign]; summarize mpg if "
                        "foreign | price > 10000; count if foreign==1 in 40/60",
             "price_if_foreign": [float(L("p4_pf_min")), float(L("p4_pf_max"))],
             "price_all": [float(L("p4_pa_min")), float(L("p4_pa_max"))],
             "rep78_if_foreign": nums(L("p4_rf")),
             "rep78_all": nums(L("p4_ra")),
             "mpg_union": rec("p4_mu", "p4_mu_t",
                              "summarize mpg if foreign | price > 10000"),
             "count_foreign_in_40_60": int(L("p4_c4060"))}
out["p5"] = {"command": "the parity frame typed in with input; summarize "
                        "price if price > 4500; levelsof price if price > 4500",
             "price_gt_4500": [float(L("p5_min")), float(L("p5_max"))],
             "price_levels_gt_4500": nums(L("p5_lv")),
             "mpg_foreign_in_3_8": rec("p5_fi38_m", "p5_fi38_t", L("p5_fi38_cmd")),
             "mpg_in_3_8": rec("p5_i38_m", "p5_i38_t", L("p5_i38_cmd")),
             "mpg_foreign": rec("p5_f_m", "p5_f_t", L("p5_f_cmd")),
             "mpg_all": rec("p5_all_m", "p5_all_t", L("p5_all_cmd").strip())}
out["p6"] = {"command": L("p6_cmd"), "mean": float(L("p6_m")),
             "mean_text": L("p6_t").strip()}
out["_meta"] = {"stata_version": L("stata_version"),
                "born_date": L("born_date"),
                "dash_commit": L("dash_commit").strip(),
                "extracted": L("extracted"),
                "source": "scripts/extract_embedded_rows_truth.do"}
path = os.path.join(repo, "test", "fixtures", "embedded_rows_truth.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote " + path)
end
