* extract_twoway_oracle_truth.do -- twoway's own answers for three
* certification scripts, written to test/fixtures (WP-30 test performance,
* B2):
*
*   test_twoway_option_parity.cscript  test/fixtures/twoway_option_parity_truth.json
*   test_parser.cscript                test/fixtures/parser_twoway_truth.json
*   test_help_claims_6.cscript         test/fixtures/help_claims_6_truth.json
*
* Each script is run whole with DASH_CERT_REMEASURE=record: it asks twoway
* every question, as it always did, and hands each answer to
* test/cert_truth.py, which writes them to a scratch folder; then each
* fixture is written with its _meta stamp (Stata's version and born date,
* dash's commit, the date).  A script that fails, or that met twoway
* answering one question two ways, writes nothing.  Run it again whenever
* a script's questions change (a replay then says which answers it lacks)
* or Stata does; DASH_CERT_REMEASURE=1 on a certification run says
* whether the fixtures still hold.
*
* Run (never the GUI; the slot wrapper of scripts/stata_slot.sh):
*   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_twoway_oracle_truth.do
* DASH_TRUTH_ONLY="parser_twoway help_claims_6" limits it to those fixtures.

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_twoway_oracle_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_twoway_oracle_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1

clear all
set more off

local stata_version = c(stata_version)
local born_date "`c(born_date)'"
tempfile gh
shell git -C "`repo'" rev-parse HEAD > "`gh'"
tempname fh
file open `fh' using "`gh'", read text
file read `fh' dash_commit
file close `fh'
local extracted "`c(current_date)'"

// The fixtures and their scripts.
local all "twoway_option_parity parser_twoway help_claims_6"
local s_twoway_option_parity "test_twoway_option_parity.cscript"
local s_parser_twoway        "test_parser.cscript"
local s_help_claims_6        "test_help_claims_6.cscript"
local only : environment DASH_TRUTH_ONLY
if `"`only'"' == "" local only "`all'"
local bad : list only - all
if "`bad'" != "" {
    display as error "extract_twoway_oracle_truth.do: DASH_TRUTH_ONLY names no fixture: `bad'"
    exit 198
}

// The scratch folder the recorded answers go to, and the mode, for the
// scripts this session runs (each reads them with `: environment').
tempfile ob
local outdir "`ob'_truth"
capture mkdir "`outdir'"
// (Each line imports what it uses: the scripts clear Python's names.)
python: __import__("os").environ["DASH_CERT_REMEASURE"] = "record"
python: __import__("os").environ["DASH_CERT_TRUTH_OUT"] = __import__("sfi").Macro.getLocal("outdir")

local failed ""
foreach n of local only {
    capture erase "`outdir'/`n'.json"
    display as text _n "extract_twoway_oracle_truth: recording `s_`n''"
    cd "`repo'/test"
    capture noisily do "`s_`n''"
    local rc_`n' = _rc
    capture log close _all
    capture file close _all
    cd "`repo'"
    // cscript drops every global; the scripts set dash_nobrowser again.
    global dash_nobrowser 1
    if `rc_`n'' {
        display as error "extract_twoway_oracle_truth: `s_`n'' failed, r(`rc_`n''); its fixture is not written"
        local failed "`failed' `n'"
    }
}

python: _zx = __import__("os").environ.pop("DASH_CERT_REMEASURE", None)
python: _zx = __import__("os").environ.pop("DASH_CERT_TRUTH_OUT", None)

python:
import json, os
from sfi import Macro
repo = Macro.getLocal("repo")
outdir = Macro.getLocal("outdir")
failed = Macro.getLocal("failed").split()
meta = {"stata_version": Macro.getLocal("stata_version"),
        "born_date": Macro.getLocal("born_date"),
        "source": "scripts/extract_twoway_oracle_truth.do",
        "dash_commit": Macro.getLocal("dash_commit").strip(),
        "extracted": Macro.getLocal("extracted"),
        "method": ("each answer asked of twoway in a run of the script "
                   "with DASH_CERT_REMEASURE=record, by "
                   "scripts/extract_twoway_oracle_truth.do (test/cert_truth.py)")}
for n in Macro.getLocal("only").split():
    if n in failed:
        continue
    rec = os.path.join(outdir, n + ".json")
    if not os.path.exists(rec):
        print("extract_twoway_oracle_truth: no answers recorded for " + n)
        failed.append(n)
        continue
    with open(rec, encoding="utf-8") as fh:
        answers = json.load(fh)
    m = dict(meta)
    m["script"] = Macro.getLocal("s_" + n)
    m["answers"] = len(answers)
    path = os.path.join(repo, "test", "fixtures", n + "_truth.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"_meta": m, "answers": answers}, fh, indent=1,
                  sort_keys=True, ensure_ascii=True)
        fh.write("\n")
    print("wrote %s: %d answers" % (path, len(answers)))
Macro.setLocal("failed", " ".join(failed))
end
if "`failed'" != "" {
    display as error "extract_twoway_oracle_truth: not written:`failed'"
    exit 9
}
