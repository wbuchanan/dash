* extract_filter_truth.do -- Stata's own counts and means for section 17's
* filter states on sysuse auto (GAPS2 E2), written to
* test/fixtures/filter_truth.json for test/test_filter_exclusion_sets.py.
*
* Run (never the GUI; the slot wrapper of scripts/stata_slot.sh):
*   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_filter_truth.do
* The tree is DASH_REPO, else the current directory when it is a dash tree.

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_filter_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_filter_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global ZA_REPO "`repo'"

clear all
set more off
sysuse auto, clear

local stata_version = c(stata_version)
local born_date "`c(born_date)'"
tempfile gh
shell git -C "${ZA_REPO}" rev-parse HEAD > "`gh'"
tempname fh
file open `fh' using "`gh'", read text
file read `fh' dash_commit
file close `fh'
local extracted "`c(current_date)'"

local keys all foreign_1 price_4000_5000 foreign_1_price_4000_5000
local conds `""1" "foreign==1" "inrange(price,4000,5000)" "foreign==1 & inrange(price,4000,5000)""'
local i = 0
foreach c of local conds {
    local ++i
    local k : word `i' of `keys'
    quietly count if `c'
    local n_`k' = r(N)
    quietly summarize mpg if `c'
    local m_`k' : display %21.17g r(mean)
    local cmd_`k' `"count if `c'"'
}

python:
import json, os
from sfi import Macro, Data
repo = Macro.getGlobal("ZA_REPO")
out = {}
for k in ("all", "foreign_1", "price_4000_5000", "foreign_1_price_4000_5000"):
    out[k] = {"command": Macro.getLocal("cmd_" + k),
              "count": int(float(Macro.getLocal("n_" + k))),
              "mean_mpg": float(Macro.getLocal("m_" + k))}
out["data"] = {v: [float(x) for x in Data.get(v)]
               for v in ("mpg", "price", "foreign")}
out["_meta"] = {"stata_version": Macro.getLocal("stata_version"),
                "born_date": Macro.getLocal("born_date"),
                "dash_commit": Macro.getLocal("dash_commit").strip(),
                "extracted": Macro.getLocal("extracted"),
                "source": "scripts/extract_filter_truth.do"}
path = os.path.join(repo, "test", "fixtures", "filter_truth.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1)
    fh.write("\n")
print("wrote " + path)
end
