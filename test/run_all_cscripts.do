*! run_all_cscripts.do
*! Master test runner for dash certification scripts.
*! Run it with `make cert', or from the dash/ directory:
*!   sh scripts/stata_batch.sh -b do test/run_all_cscripts.do
*! The tree under test is DASH_REPO, else the current directory; either
*! must be a dash tree (dash.ado and test/run_all_cscripts.do), or the run
*! stops with r(601).
*!
*! On Apple silicon, scripts/stata_batch.sh starts Stata's arm64 slice.  A
*! long run of this file was observed launching the x86_64 slice, and the
*! arm64 libpython then cannot be loaded:
*!     dlopen(.../libpython3.13.dylib): incompatible architecture
*!       (have 'arm64', need 'x86_64')
*! Every Python-dependent script then fails for a reason that has nothing to
*! do with dash.  Choosing the slice makes the run reproducible.

// ----------------------------------------------------------------
// Setup
// ----------------------------------------------------------------
clear all
set more off

// ---- root: begin (WP-30 P1.34) ----
local dashdir : environment DASH_REPO
if `"`macval(dashdir)'"' == "" local dashdir `"`c(pwd)'"'
mata: st_local("_dash_bad", strofreal(any(strpos(st_local("dashdir"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_dash_bad' {
    display as error "run_all_cscripts.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`dashdir'"') > 1 & inlist(substr(`"`dashdir'"', -1, 1), "/", char(92)) {
    local dashdir = substr(`"`dashdir'"', 1, strlen(`"`dashdir'"') - 1)
}
capture confirm file `"`dashdir'/dash.ado"'
local _dash_rc = _rc
capture confirm file `"`dashdir'/test/run_all_cscripts.do"'
if `_dash_rc' | _rc {
    local _dash_show = substr(`"`dashdir'"', 1, 200)
    display as error `"run_all_cscripts.do: `_dash_show' is not a dash tree (it needs dash.ado and test/run_all_cscripts.do); set DASH_REPO to the tree to test"'
    exit 601
}
adopath ++ "`dashdir'/"
local testdir "`dashdir'/test"
cd "`dashdir'"
quietly findfile dash.ado
if `"`r(fn)'"' != `"`dashdir'/dash.ado"' {
    display as error `"run_all_cscripts.do: dash.ado resolves to `r(fn)', not `dashdir'/dash.ado"'
    exit 9
}
// ---- root: end ----

// WP-30 P1.33: link this session, and only this session, to another
// interpreter (the floor certification run).  Unset, nothing changes.
local _dash_pyx : environment DASH_PYTHON_EXEC
if `"`macval(_dash_pyx)'"' != "" {
    mata: st_local("_dash_pyx_bad", strofreal(any(strpos(st_local("_dash_pyx"), (char(34), char(36), char(96)))) | any(ascii(st_local("_dash_pyx")) :< 32)))
    if `_dash_pyx_bad' {
        display as error "DASH_PYTHON_EXEC holds a quote, backquote, dollar sign or control character"
        exit 198
    }
    python set exec `"`_dash_pyx'"'
    display as text "  Python linked for this run only: `_dash_pyx'"
}

display as text ""
display as text "============================================================"
display as text "  dash certification script runner"
display as text "  `c(current_date)' `c(current_time)'"
display as text "============================================================"
display as text ""

// ----------------------------------------------------------------
// Track results
// ----------------------------------------------------------------
local n_pass = 0
local n_fail = 0
local n_skip = 0

// Do not open a browser for every dashboard the suite builds.  Without this
// a full run opened one window per `dash build' -- dozens of them, in rapid
// succession, on the machine running the tests.
global dash_nobrowser 1

// A machine without Python still runs the parser-only scripts; the
// Python-dependent ones detect it for themselves through c(python_exec).
// Do NOT probe here with `capture python: pass' -- measured, that reports a
// nonzero rc in this context on a machine where Python works.
if "`c(python_exec)'" == "" {
    display as error "NOTE: Python is not configured; "                 ///
                     "the Python-dependent scripts will skip."
}

// Scripts run under -capture noisily-, not bare -capture-.  Quiet capture
// suppresses everything the scripts display, which hid the SKIP: messages
// and broke any check that verifies dash's own output -- a test of the
// unsupported-option note cannot see the note if the note is suppressed.
// ----------------------------------------------------------------
// 1. test_tokenizer.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_tokenizer.cscript"
cd "`testdir'"
capture noisily {
    do "test_tokenizer.cscript"
}
local rc = _rc
// A script that dies mid-scan leaves its `file open' handle open; clear all
// does not close file handles, and the next script's file open then fails for
// a reason that has nothing to do with what it is testing.
capture file close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_tokenizer.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_tokenizer.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_tokenizer.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 2. test_parser.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_parser.cscript"
cd "`testdir'"
capture noisily {
    do "test_parser.cscript"
}
local rc = _rc
// A script that dies mid-scan leaves its `file open' handle open; clear all
// does not close file handles, and the next script's file open then fails for
// a reason that has nothing to do with what it is testing.
capture file close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_parser.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_parser.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_parser.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 4. test_e2e_single.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_e2e_single.cscript"
cd "`testdir'"
capture noisily {
    do "test_e2e_single.cscript"
}
local rc = _rc
// A script that dies mid-scan leaves its `file open' handle open; clear all
// does not close file handles, and the next script's file open then fails for
// a reason that has nothing to do with what it is testing.
capture file close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_e2e_single.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_e2e_single.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_e2e_single.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 5. test_e2e_multi.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_e2e_multi.cscript"
cd "`testdir'"
capture noisily {
    do "test_e2e_multi.cscript"
}
local rc = _rc
// A script that dies mid-scan leaves its `file open' handle open; clear all
// does not close file handles, and the next script's file open then fails for
// a reason that has nothing to do with what it is testing.
capture file close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_e2e_multi.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_e2e_multi.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_e2e_multi.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 6. test_e2e_filters.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_e2e_filters.cscript"
cd "`testdir'"
capture noisily {
    do "test_e2e_filters.cscript"
}
local rc = _rc
// A script that dies mid-scan leaves its `file open' handle open; clear all
// does not close file handles, and the next script's file open then fails for
// a reason that has nothing to do with what it is testing.
capture file close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_e2e_filters.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_e2e_filters.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_e2e_filters.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 7. test_e2e_kpi.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_e2e_kpi.cscript"
cd "`testdir'"
capture noisily {
    do "test_e2e_kpi.cscript"
}
local rc = _rc
// A script that dies mid-scan leaves its `file open' handle open; clear all
// does not close file handles, and the next script's file open then fails for
// a reason that has nothing to do with what it is testing.
capture file close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_e2e_kpi.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_e2e_kpi.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_e2e_kpi.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 8. test_ado_loads.cscript (Bug 15 + 16 regression)
// Run from testdir — uses explicit do "../dash_parse.mata" + do "../dash.ado"
// ----------------------------------------------------------------
display as text "[ RUN ] test_ado_loads.cscript"
cd "`testdir'"
capture noisily {
    do "test_ado_loads.cscript"
}
local rc = _rc
// A script that dies mid-scan leaves its `file open' handle open; clear all
// does not close file handles, and the next script's file open then fails for
// a reason that has nothing to do with what it is testing.
capture file close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_ado_loads.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_ado_loads.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_ado_loads.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 9. test_mata_autoload.cscript (Bug 16 regression — auto-load)
// MUST run from dashdir so findfile finds dash_parse.mata via "." in adopath.
// ----------------------------------------------------------------
display as text "[ RUN ] test_mata_autoload.cscript"
cd "`dashdir'"
capture noisily {
    do "test/test_mata_autoload.cscript"
}
local rc = _rc
if `rc' == 222 {
    display as text "[ SKIP] test_mata_autoload.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_mata_autoload.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_mata_autoload.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 10. test_adversarial.cscript (security suite)
// Previously never invoked by this runner despite existing on disk, so the
// adversarial security checks were dead weight.  See CLAUDE.md rule 18.
// ----------------------------------------------------------------
display as text "[ RUN ] test_adversarial.cscript"
cd "`testdir'"
capture noisily {
    do "test_adversarial.cscript"
}
local rc = _rc
// A script that dies mid-scan leaves its `file open' handle open; clear all
// does not close file handles, and the next script's file open then fails for
// a reason that has nothing to do with what it is testing.
capture file close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_adversarial.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_adversarial.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_adversarial.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 11. test_e2e_serve.cscript (server mode end-to-end)
// Also previously never invoked.  Server mode has known defects that
// section 14 of the plan fixes; a failure here is expected until then and
// is informative rather than spurious.
// ----------------------------------------------------------------
display as text "[ RUN ] test_e2e_serve.cscript"
cd "`testdir'"
capture noisily {
    do "test_e2e_serve.cscript"
}
local rc = _rc
// A script that dies mid-scan leaves its `file open' handle open; clear all
// does not close file handles, and the next script's file open then fails for
// a reason that has nothing to do with what it is testing.
capture file close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_e2e_serve.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_e2e_serve.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_e2e_serve.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 12. test_abbreviations.cscript
// Stata-derived abbreviation conformance (section 04)
// ----------------------------------------------------------------
display as text "[ RUN ] test_abbreviations.cscript"
cd "`testdir'"
capture noisily {
    do "test_abbreviations.cscript"
}
local rc = _rc
// A script that dies mid-scan leaves its `file open' handle open; clear all
// does not close file handles, and the next script's file open then fails for
// a reason that has nothing to do with what it is testing.
capture file close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_abbreviations.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_abbreviations.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_abbreviations.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 13. test_option_surface.cscript
// every twoway command in the corpus must run (section 05)
// ----------------------------------------------------------------
display as text "[ RUN ] test_option_surface.cscript"
cd "`testdir'"
capture noisily {
    do "test_option_surface.cscript"
}
local rc = _rc
// A script that dies mid-scan leaves its `file open' handle open; clear all
// does not close file handles, and the next script's file open then fails for
// a reason that has nothing to do with what it is testing.
capture file close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_option_surface.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_option_surface.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_option_surface.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 14. test_varlist_expansion.cscript
// varlist and plot-spec correctness (section 06)
// ----------------------------------------------------------------
display as text "[ RUN ] test_varlist_expansion.cscript"
cd "`testdir'"
capture noisily {
    do "test_varlist_expansion.cscript"
}
local rc = _rc
// A script that dies mid-scan leaves its `file open' handle open; clear all
// does not close file handles, and the next script's file open then fails for
// a reason that has nothing to do with what it is testing.
capture file close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_varlist_expansion.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_varlist_expansion.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_varlist_expansion.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 15. test_path_validation.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_path_validation.cscript"
cd "`testdir'"
capture noisily {
    do "test_path_validation.cscript"
}
local rc = _rc
capture file close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_path_validation.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_path_validation.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_path_validation.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 16. test_setup_version_gate.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_setup_version_gate.cscript"
cd "`testdir'"
capture noisily {
    do "test_setup_version_gate.cscript"
}
local rc = _rc
capture file close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_setup_version_gate.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_setup_version_gate.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_setup_version_gate.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 17. test_clear_registry.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_clear_registry.cscript"
cd "`testdir'"
capture noisily {
    do "test_clear_registry.cscript"
}
local rc = _rc
capture file close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_clear_registry.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_clear_registry.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_clear_registry.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 19. test_filter_label.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_filter_label.cscript"
cd "`testdir'"
capture noisily {
    do "test_filter_label.cscript"
}
local rc = _rc
capture file close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_filter_label.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_filter_label.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_filter_label.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 20. test_server_build.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_server_build.cscript"
cd "`testdir'"
capture noisily {
    do "test_server_build.cscript"
}
local rc = _rc
capture file close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_server_build.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_server_build.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_server_build.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 18. test_examples_run.cscript
// ----------------------------------------------------------------
// Runs last: it is the slowest script, and it is the end-to-end gate.
display as text "[ RUN ] test_examples_run.cscript"
cd "`testdir'"
capture noisily {
    do "test_examples_run.cscript"
}
local rc = _rc
capture file close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_examples_run.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_examples_run.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_examples_run.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 21. test_serve_options.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_serve_options.cscript"
cd "`testdir'"
capture noisily {
    do "test_serve_options.cscript"
}
local rc = _rc
capture file close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_serve_options.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_serve_options.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_serve_options.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 22. test_render_log_clean.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_render_log_clean.cscript"
cd "`testdir'"
capture noisily {
    do "test_render_log_clean.cscript"
}
local rc = _rc
capture file close _all
capture log close _dashlog
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_render_log_clean.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_render_log_clean.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_render_log_clean.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 23. test_option_report_paren.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_option_report_paren.cscript"
cd "`testdir'"
capture noisily {
    do "test_option_report_paren.cscript"
}
local rc = _rc
capture file close _all
capture log close _optlog
capture program drop _dash_note_for
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_option_report_paren.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_option_report_paren.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_option_report_paren.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 24. test_setup_python_gate.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_setup_python_gate.cscript"
cd "`testdir'"
capture noisily {
    do "test_setup_python_gate.cscript"
}
local rc = _rc
capture file close _all
capture program drop _chk
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_setup_python_gate.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_setup_python_gate.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_setup_python_gate.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 25. test_conformance.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_conformance.cscript"
cd "`testdir'"
capture noisily {
    do "test_conformance.cscript"
}
local rc = _rc
capture file close _all
capture log close _cflog
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_conformance.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_conformance.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_conformance.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 26. test_parser_integrity.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_parser_integrity.cscript"
cd "`testdir'"
capture noisily {
    do "test_parser_integrity.cscript"
}
local rc = _rc
capture file close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_parser_integrity.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_parser_integrity.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_parser_integrity.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 27. test_textbox_multiline.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_textbox_multiline.cscript"
cd "`testdir'"
capture noisily {
    do "test_textbox_multiline.cscript"
}
local rc = _rc
capture file close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_textbox_multiline.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_textbox_multiline.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_textbox_multiline.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 28. test_serve_launch.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_serve_launch.cscript"
cd "`testdir'"
capture noisily {
    do "test_serve_launch.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_serve_launch.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_serve_launch.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_serve_launch.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 29. test_registry_collision.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_registry_collision.cscript"
cd "`testdir'"
capture noisily {
    do "test_registry_collision.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_registry_collision.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_registry_collision.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_registry_collision.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 30. test_graph_option_scope.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_graph_option_scope.cscript"
cd "`testdir'"
capture noisily {
    do "test_graph_option_scope.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_graph_option_scope.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_graph_option_scope.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_graph_option_scope.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 31. test_render_locate.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_render_locate.cscript"
cd "`testdir'"
capture noisily {
    do "test_render_locate.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_render_locate.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_render_locate.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_render_locate.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 32. test_theme_escaping.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_theme_escaping.cscript"
cd "`testdir'"
capture noisily {
    do "test_theme_escaping.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_theme_escaping.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_theme_escaping.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_theme_escaping.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 33. test_setup_honesty.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_setup_honesty.cscript"
cd "`testdir'"
capture noisily {
    do "test_setup_honesty.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_setup_honesty.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_setup_honesty.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_setup_honesty.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 34. test_env_guards.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_env_guards.cscript"
cd "`testdir'"
capture noisily {
    do "test_env_guards.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_env_guards.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_env_guards.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_env_guards.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 35. test_utf8_validation.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_utf8_validation.cscript"
cd "`testdir'"
capture noisily {
    do "test_utf8_validation.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_utf8_validation.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_utf8_validation.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_utf8_validation.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 36. test_json_escaping.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_json_escaping.cscript"
cd "`testdir'"
capture noisily {
    do "test_json_escaping.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_json_escaping.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_json_escaping.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_json_escaping.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 37. test_by_suboptions.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_by_suboptions.cscript"
cd "`testdir'"
capture noisily {
    do "test_by_suboptions.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_by_suboptions.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_by_suboptions.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_by_suboptions.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 38. test_nodraw_honoured.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_nodraw_honoured.cscript"
cd "`testdir'"
capture noisily {
    do "test_nodraw_honoured.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_nodraw_honoured.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_nodraw_honoured.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_nodraw_honoured.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 39. test_alias_semantics.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_alias_semantics.cscript"
cd "`testdir'"
capture noisily {
    do "test_alias_semantics.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_alias_semantics.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_alias_semantics.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_alias_semantics.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 40. test_suboption_reporting.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_suboption_reporting.cscript"
cd "`testdir'"
capture noisily {
    do "test_suboption_reporting.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_suboption_reporting.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_suboption_reporting.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_suboption_reporting.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 41. test_option_validation.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_option_validation.cscript"
cd "`testdir'"
capture noisily {
    do "test_option_validation.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_option_validation.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_option_validation.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_option_validation.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 42. test_custom_scheme.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_custom_scheme.cscript"
cd "`testdir'"
capture noisily {
    do "test_custom_scheme.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_custom_scheme.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_custom_scheme.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_custom_scheme.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 43. test_statistical_options.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_statistical_options.cscript"
cd "`testdir'"
capture noisily {
    do "test_statistical_options.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_statistical_options.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_statistical_options.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_statistical_options.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 44. test_caller_version.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_caller_version.cscript"
cd "`testdir'"
capture noisily {
    do "test_caller_version.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_caller_version.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_caller_version.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_caller_version.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 45. test_resource_limits.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_resource_limits.cscript"
cd "`testdir'"
capture noisily {
    do "test_resource_limits.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_resource_limits.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_resource_limits.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_resource_limits.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 46. test_serve_browser.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_serve_browser.cscript"
cd "`testdir'"
capture noisily {
    do "test_serve_browser.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_serve_browser.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_serve_browser.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_serve_browser.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 47. test_setup_injection.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_setup_injection.cscript"
cd "`testdir'"
capture noisily {
    do "test_setup_injection.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_setup_injection.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_setup_injection.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_setup_injection.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 48. test_echo_text.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_echo_text.cscript"
cd "`testdir'"
capture noisily {
    do "test_echo_text.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_echo_text.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_echo_text.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_echo_text.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 49. test_export.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_export.cscript"
cd "`testdir'"
capture noisily {
    do "test_export.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_export.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_export.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_export.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 50. test_twoway_option_parity.cscript (WP-22 TR-22.3)
// ----------------------------------------------------------------
display as text "[ RUN ] test_twoway_option_parity.cscript"
cd "`testdir'"
capture noisily {
    do "test_twoway_option_parity.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_twoway_option_parity.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_twoway_option_parity.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_twoway_option_parity.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 51. test_help_claims_1.cscript (WP-23: help lines 1-316, syntax, plot types, differences)
// ----------------------------------------------------------------
display as text "[ RUN ] test_help_claims_1.cscript"
cd "`testdir'"
capture noisily {
    do "test_help_claims_1.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_help_claims_1.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_help_claims_1.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_help_claims_1.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 52. test_help_claims_2.cscript (WP-23: option values, subcommands, dashboard options, export)
// ----------------------------------------------------------------
display as text "[ RUN ] test_help_claims_2.cscript"
cd "`testdir'"
capture noisily {
    do "test_help_claims_2.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_help_claims_2.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_help_claims_2.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_help_claims_2.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 53. test_help_claims_3.cscript (WP-23: layout, tabs, linking, toolbar, filters)
// ----------------------------------------------------------------
display as text "[ RUN ] test_help_claims_3.cscript"
cd "`testdir'"
capture noisily {
    do "test_help_claims_3.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_help_claims_3.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_help_claims_3.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_help_claims_3.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 54. test_help_claims_4.cscript (WP-23: KPI cards and server mode, a real dash serve)
// ----------------------------------------------------------------
display as text "[ RUN ] test_help_claims_4.cscript"
cd "`testdir'"
capture noisily {
    do "test_help_claims_4.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_help_claims_4.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_help_claims_4.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_help_claims_4.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 55. test_help_claims_5.cscript (WP-23: resource limits, faceting, marker labels)
// ----------------------------------------------------------------
display as text "[ RUN ] test_help_claims_5.cscript"
cd "`testdir'"
capture noisily {
    do "test_help_claims_5.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_help_claims_5.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_help_claims_5.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_help_claims_5.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 56. test_help_claims_6.cscript (WP-23: statistical layers and weights)
// ----------------------------------------------------------------
display as text "[ RUN ] test_help_claims_6.cscript"
cd "`testdir'"
capture noisily {
    do "test_help_claims_6.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_help_claims_6.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_help_claims_6.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_help_claims_6.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 57. test_help_claims_7.cscript (WP-23: regions, axes, colour, geometry, markers)
// ----------------------------------------------------------------
display as text "[ RUN ] test_help_claims_7.cscript"
cd "`testdir'"
capture noisily {
    do "test_help_claims_7.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_help_claims_7.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_help_claims_7.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_help_claims_7.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 58. test_help_claims_8.cscript (WP-23: schemes, the Unsupported list, dependencies)
// ----------------------------------------------------------------
display as text "[ RUN ] test_help_claims_8.cscript"
cd "`testdir'"
capture noisily {
    do "test_help_claims_8.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_help_claims_8.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_help_claims_8.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_help_claims_8.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 59. test_help_examples.cscript (WP-23: every example command in the help, run)
// ----------------------------------------------------------------
display as text "[ RUN ] test_help_examples.cscript"
cd "`testdir'"
capture noisily {
    do "test_help_examples.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_help_examples.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_help_examples.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_help_examples.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 60. test_bug_regressions.cscript (WP-24: the regression tests three closed BUGS.md entries lacked)
// ----------------------------------------------------------------
display as text "[ RUN ] test_bug_regressions.cscript"
cd "`testdir'"
capture noisily {
    do "test_bug_regressions.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_bug_regressions.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_bug_regressions.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_bug_regressions.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 61. test_program_coverage.cscript (WP-24 AC-24.3, GAPS L7: dash_setup end to end, display formats)
// ----------------------------------------------------------------
display as text "[ RUN ] test_program_coverage.cscript"
cd "`testdir'"
capture noisily {
    do "test_program_coverage.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
capture program drop ssc
capture program drop _pc_fail
capture program drop _pc_setup
capture program drop _pc_said
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_program_coverage.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_program_coverage.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_program_coverage.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 62. test_qualifier_literals.cscript (WP-24: a qualifier's string literals select the rows Stata selects)
// ----------------------------------------------------------------
display as text "[ RUN ] test_qualifier_literals.cscript"
cd "`testdir'"
capture noisily {
    do "test_qualifier_literals.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_qualifier_literals.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_qualifier_literals.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_qualifier_literals.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 63. test_mata_library_guard.cscript (WP-24: the Mata library guard refuses a library missing any function dash calls, and mends one it can)
// ----------------------------------------------------------------
display as text "[ RUN ] test_mata_library_guard.cscript"
cd "`testdir'"
capture noisily {
    do "test_mata_library_guard.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_mata_library_guard.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_mata_library_guard.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_mata_library_guard.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 64. test_qualifier_in_stata.cscript (WP-27: every qualifier dash writes is evaluated in Stata, and both modes draw Stata's rows)
// ----------------------------------------------------------------
display as text "[ RUN ] test_qualifier_in_stata.cscript"
cd "`testdir'"
capture noisily {
    do "test_qualifier_in_stata.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_qualifier_in_stata.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_qualifier_in_stata.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_qualifier_in_stata.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 65. test_string_values.cscript (WP-27: every string value, label and number reaches both renderers byte for byte; the export no longer uses jsonio)
// ----------------------------------------------------------------
display as text "[ RUN ] test_string_values.cscript"
cd "`testdir'"
capture noisily {
    do "test_string_values.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_string_values.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_string_values.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_string_values.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 66. test_ci_band_options.cscript (S3 batch: a ci fit's band is drawn in the scheme's ci style and takes twoway's fitarea options)
// ----------------------------------------------------------------
display as text "[ RUN ] test_ci_band_options.cscript"
cd "`testdir'"
capture noisily {
    do "test_ci_band_options.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_ci_band_options.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_ci_band_options.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_ci_band_options.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 67. test_gaps2_truth.cscript (WP-28: the one certification script for
// every twoway/Stata-value comparison the GAPS2 fix package needs; one
// block per section, appended above its own "append new blocks above
// this line" marker -- review D11)
// ----------------------------------------------------------------
display as text "[ RUN ] test_gaps2_truth.cscript"
cd "`testdir'"
capture noisily {
    do "test_gaps2_truth.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_gaps2_truth.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_gaps2_truth.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_gaps2_truth.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 68. test_wp29_truth.cscript (WP-29: the one certification script for
// every twoway/Stata-value comparison the drop-in P0 package needs; one
// block per section, appended above its own "append new blocks above
// this line" marker -- .ultraplan/wp29/index.md A3)
// ----------------------------------------------------------------
display as text "[ RUN ] test_wp29_truth.cscript"
cd "`testdir'"
capture noisily {
    do "test_wp29_truth.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_wp29_truth.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_wp29_truth.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_wp29_truth.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// 69. test_wp30_truth.cscript (WP-30: the one certification script for
// every twoway/Stata-value comparison the drop-in P1 package needs; one
// block per section, S01's scaffold and one block for each of S02-S57,
// above its "append new blocks above this line" marker --
// .ultraplan/wp30/index.md A142)
// ----------------------------------------------------------------
display as text "[ RUN ] test_wp30_truth.cscript"
cd "`testdir'"
capture noisily {
    do "test_wp30_truth.cscript"
}
local rc = _rc
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_wp30_truth.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_wp30_truth.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_wp30_truth.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}

// ----------------------------------------------------------------
// Summary
// ----------------------------------------------------------------
local n_total = `n_pass' + `n_fail' + `n_skip'
display as text ""
display as text "============================================================"
display as text "  Results: `n_pass' passed, `n_fail' failed, `n_skip' skipped  (of `n_total' total)"
display as text "============================================================"

if `n_fail' > 0 {
    display as error "SOME TESTS FAILED"
    exit 1
}
else if `n_pass' == 0 {
    // Every script skipped: nothing was asserted.  Reporting success here
    // would be a false pass -- a machine without Python would
    // previously print ALL TESTS PASSED having verified nothing.
    display as error "NO TESTS RAN -- all `n_skip' script(s) skipped."
    display as error "Install the missing dependencies (run dash_setup) and re-run."
    exit 1
}
else {
    display as text "ALL TESTS PASSED (`n_pass' passed, `n_skip' skipped)"
}
