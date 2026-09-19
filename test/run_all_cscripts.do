*! run_all_cscripts.do
*! Master test runner for dash certification scripts.
*! Run from the dash/ directory:
*!   arch -arm64 /usr/local/bin/stata-mp -b do test/run_all_cscripts.do
*!
*! On Apple silicon, run Stata through `arch -arm64'.  Stata and the
*! configured Python are both universal/native, but a long run of this file
*! was observed launching the x86_64 slice, and the arm64 libpython then
*! cannot be loaded:
*!     dlopen(.../libpython3.13.dylib): incompatible architecture
*!       (have 'arm64', need 'x86_64')
*! Every Python-dependent script then fails for a reason that has nothing to
*! do with dash.  Forcing the slice makes the run reproducible.

// ----------------------------------------------------------------
// Setup
// ----------------------------------------------------------------
clear all
set more off

// Add jsonio to the ado path (local installation)
adopath ++ "/Users/billy/Desktop/Programs/Java/StataJSON/"

// Add dash ado files to the path
adopath ++ "/Users/billy/Desktop/Programs/StataPrograms/d/dash/"

// Root project directory (all cd calls return here)
local dashdir "/Users/billy/Desktop/Programs/StataPrograms/d/dash"
local testdir "`dashdir'/test"

cd "`dashdir'"

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
// 3. test_jsonio.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_jsonio.cscript"
cd "`testdir'"
capture noisily {
    do "test_jsonio.cscript"
}
local rc = _rc
// A script that dies mid-scan leaves its `file open' handle open; clear all
// does not close file handles, and the next script's file open then fails for
// a reason that has nothing to do with what it is testing.
capture file close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_jsonio.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_jsonio.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_jsonio.cscript  (rc=`rc')"
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
    // would be a false pass -- a machine without jsonio or Python would
    // previously print ALL TESTS PASSED having verified nothing.
    display as error "NO TESTS RAN -- all `n_skip' script(s) skipped."
    display as error "Install the missing dependencies (run dash_setup) and re-run."
    exit 1
}
else {
    display as text "ALL TESTS PASSED (`n_pass' passed, `n_skip' skipped)"
}
