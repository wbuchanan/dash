*! extract_corpus_guard_truth.do
*! WP-33 section 33-09: the expected rows of the certification suite's
*! corpus guard (block S09 of test/test_wp33_truth.cscript), for
*! test/fixtures/corpus_guard_truth.json.
*!
*! WHY THIS EXISTS
*!
*! The guard draws about twenty help-file examples (scripts/corpus/
*! guard_examples.txt) with twoway and with dash in the certification
*! session and fails when any example's return codes, twoway's first line,
*! verdict, checks or summary moves (D-33-09.c).  This script records those
*! rows, and freezes each listed example's record (its setup and command)
*! so certification never reads a help file (D-33-09.g).
*!
*! Output: test/fixtures/corpus_guard_truth.json
*!
*! Run with:
*!
*!   DASH_REPO=<repo> sh <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_corpus_guard_truth.do
*!
*! METHOD
*!
*! A listed id the fixture already holds keeps its frozen record; only the
*! ids it lacks are extracted, by scripts/corpus/extract.py into a
*! temporary folder (every id at the first generation, none at a later
*! regeneration).  scripts/corpus/guard.py writes 33-03's twoway do-file,
*! 33-04's dash do-file and the guard.do that wraps them; guard.do runs
*! here; guard.measure exports each dash page at twoway's size in
*! headless Chrome and judges it with 33-05's judge under the committed
*! rules and ledger.  The python: blocks never use a shell (a backtick is
*! spelled \x60).  After a regeneration run block S09 until it prints
*! Q3309-1 PASS, then git add -f the fixture.
*! ---------------------------------------------------------------------------

clear all
set graphics off
set more off
version 19

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_corpus_guard_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_corpus_guard_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1

* A fresh folder Stata has not handed out before.
tempfile cgbase
local work "`cgbase'_cg"
capture mkdir "`work'"
if _rc {
    display as error "extract_corpus_guard_truth.do: cannot create the work directory"
    exit 603
}

global CG_REPO "`repo'"
global CG_WORK "`work'"
global CG_SDIR "`c(sysdir_stata)'"
global CG_SVER = c(stata_version)
global CG_BORN = c(born_date)
global CG_DATE = c(current_date) + " " + c(current_time)
global CG_GDO ""

python:
import json, os, sys
from sfi import Macro
_cg_repo = Macro.getGlobal("CG_REPO")
_cg_work = Macro.getGlobal("CG_WORK")
if _cg_repo not in sys.path:
    sys.path.insert(0, _cg_repo)
from scripts.corpus import datasets, extract, guard
_cg_path = os.path.join(_cg_repo, "test", "fixtures", "corpus_guard_truth.json")
_cg_fixture = None
if os.path.exists(_cg_path):
    with open(_cg_path, encoding="utf-8") as fh:
        _cg_fixture = json.load(fh)
_cg_ids = guard.read_list()
_cg_need = [i for i in _cg_ids
            if _cg_fixture is None or i not in _cg_fixture["examples"]]
_cg_x = os.path.join(_cg_work, "x")
if _cg_need:
    print("extract_corpus_guard_truth.do: extracting %d example(s)" % len(_cg_need))
    extract.extract(Macro.getGlobal("CG_SDIR"), _cg_repo, _cg_x)
_cg_recs = guard.records_from_run(_cg_x if _cg_need else None, _cg_ids, _cg_fixture)
_cg_g = os.path.join(_cg_work, "g")
guard.write_examples(_cg_recs, _cg_g)
Macro.setGlobal("CG_GDO", guard.guard_do([_cg_recs[i] for i in sorted(_cg_recs)], _cg_g,
                                         datasets.cache_dir(), _cg_repo))
end

do "${CG_GDO}"

// Provenance stamp: `shell' writes the commit into a file, read back.
tempfile cggitrev
quietly shell git -C "${CG_REPO}" rev-parse HEAD > "`cggitrev'"
tempname cgfh
file open `cgfh' using "`cggitrev'", read text
file read `cgfh' cggitline
file close `cgfh'
local dash_commit = trim(`"`cggitline'"')
capture assert ustrregexm(`"`dash_commit'"', "^[0-9a-f]{40}$")
if _rc {
    display as error "extract_corpus_guard_truth.do: git rev-parse HEAD did not print a 40-character commit"
    exit 498
}

python:
import shutil
_cg_rules = "test/fixtures/corpus_verdict_rules.json"
_cg_ledger = "test/fixtures/corpus_ledger.json"
try:
    _cg_rows = guard.measure(_cg_g, [_cg_recs[i] for i in sorted(_cg_recs)],
                             os.path.join(_cg_repo, _cg_rules),
                             os.path.join(_cg_repo, _cg_ledger),
                             os.path.join(_cg_repo, "GAPS4.md"))
    _cg_out = {
        "_meta": {"stata_version": Macro.getGlobal("CG_SVER"),
                  "born_date": Macro.getGlobal("CG_BORN"),
                  "dash_commit": Macro.getLocal("dash_commit"),
                  "extracted": Macro.getGlobal("CG_DATE"),
                  "source": "scripts/extract_corpus_guard_truth.do",
                  "rules": _cg_rules, "ledger": _cg_ledger},
        "examples": {i: dict(_cg_rows[i], record=_cg_recs[i]) for i in sorted(_cg_recs)},
    }
    with open(_cg_path, "w", encoding="utf-8") as fh:
        json.dump(_cg_out, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    for i in sorted(_cg_rows):
        r = _cg_rows[i]
        print("%s %s %s" % (i, r["verdict"], r["summary"]))
    print("WROTE test/fixtures/corpus_guard_truth.json examples=%d" % len(_cg_rows))
finally:
    shutil.rmtree(_cg_work, ignore_errors=True)
end

macro drop CG_*
display as text "extract_corpus_guard_truth.do: done"
