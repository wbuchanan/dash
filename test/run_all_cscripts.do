*! run_all_cscripts.do
*! Master test runner for dash certification scripts.
*! Run from the dash/ directory:
*!   /usr/local/bin/stata-mp do test/run_all_cscripts.do

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

// ----------------------------------------------------------------
// 1. test_tokenizer.cscript
// ----------------------------------------------------------------
display as text "[ RUN ] test_tokenizer.cscript"
cd "`testdir'"
capture {
    do "test_tokenizer.cscript"
}
local rc = _rc
cd "`dashdir'"
if `rc' == 0 {
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
capture {
    do "test_parser.cscript"
}
local rc = _rc
cd "`dashdir'"
if `rc' == 0 {
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
capture {
    do "test_jsonio.cscript"
}
local rc = _rc
cd "`dashdir'"
if `rc' == 0 {
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
capture {
    do "test_e2e_single.cscript"
}
local rc = _rc
cd "`dashdir'"
if `rc' == 0 {
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
capture {
    do "test_e2e_multi.cscript"
}
local rc = _rc
cd "`dashdir'"
if `rc' == 0 {
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
capture {
    do "test_e2e_filters.cscript"
}
local rc = _rc
cd "`dashdir'"
if `rc' == 0 {
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
capture {
    do "test_e2e_kpi.cscript"
}
local rc = _rc
cd "`dashdir'"
if `rc' == 0 {
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
capture {
    do "test_ado_loads.cscript"
}
local rc = _rc
cd "`dashdir'"
if `rc' == 0 {
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
capture {
    do "test/test_mata_autoload.cscript"
}
local rc = _rc
if `rc' == 0 {
    display as text "[ PASS] test_mata_autoload.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_mata_autoload.cscript  (rc=`rc')"
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
else {
    display as text "ALL TESTS PASSED"
}
