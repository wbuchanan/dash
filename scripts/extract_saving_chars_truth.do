* extract_saving_chars_truth.do -- twoway's saving() on paths holding the
* characters WP-30 rules on (P1.29, S04; P1.27, S12): its return code and
* whether the file was written under the name as typed, on this machine.
* Writes test/fixtures/saving_chars_truth.json, read by
* test/test_saving_chars.py and test/test_wp30_truth.cscript (S04, S12).
* Run (never the GUI):
*   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_saving_chars_truth.do
* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_saving_chars_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_saving_chars_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1
version 19
set more off
sysuse auto, clear
local stata_version = c(stata_version)
local born_date "`c(born_date)'"
local os "`c(os)'"
local machine "`c(machine_type)'"
tempfile gh base
shell git -C "`repo'" rev-parse HEAD > "`gh'"
tempname fh
file open `fh' using "`gh'", read text
file read `fh' dash_commit
file close `fh'
local extracted "`c(current_date)'"
local d "`base'_sct"
capture mkdir "`d'"
capture mkdir "`d'/sub"
local keys  pct_path bang pct_pct caret amp semi pipe lt gt
local names `" "pct%PATH%x" "bang!x!y" "pct%%x" "caret^x" "R&D" "a;b" "a|b" "a<b" "a>b" "'
local i 0
foreach n of local names {
    local ++i
    local k : word `i' of `keys'
    capture erase `"`d'/tw_`n'.gph"'
    capture twoway scatter mpg weight, saving(`"`d'/tw_`n'.gph"', replace) nodraw
    local rc_`k' = _rc
    capture confirm file `"`d'/tw_`n'.gph"'
    local w_`k' = (_rc == 0)
    local f_`k' `"tw_`n'.gph"'
    capture erase `"`d'/tw_`n'.gph"'
}
capture twoway scatter mpg weight, saving("`d'/sub/../tw_dotdot.gph", replace) nodraw
local rc_dotdot = _rc
capture confirm file "`d'/tw_dotdot.gph"
local w_dotdot = (_rc == 0)
local f_dotdot "sub/../tw_dotdot.gph"
capture erase "`d'/tw_dotdot.gph"
capture rmdir "`d'/sub"
capture rmdir "`d'"
python:
import json, os
from sfi import Macro
keys = "pct_path bang pct_pct caret amp semi pipe lt gt dotdot".split()
probes = {}
for k in keys:
    f = Macro.getLocal("f_" + k)
    probes[k] = {"file": f,
                 "command": 'twoway scatter mpg weight, saving("<dir>/' + f + '", replace) nodraw',
                 "rc": int(float(Macro.getLocal("rc_" + k))),
                 "written": Macro.getLocal("w_" + k) == "1"}
out = {"probes": probes,
       "_meta": {"stata_version": Macro.getLocal("stata_version"),
                 "born_date": Macro.getLocal("born_date"),
                 "dash_commit": Macro.getLocal("dash_commit").strip(),
                 "extracted": Macro.getLocal("extracted"),
                 "os": Macro.getLocal("os"),
                 "machine_type": Macro.getLocal("machine"),
                 "scope": "macOS only; Windows is unmeasured (WP-30 M4)",
                 "source": "scripts/extract_saving_chars_truth.do"}}
path = os.path.join(Macro.getLocal("repo"), "test", "fixtures", "saving_chars_truth.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote " + path)
end
