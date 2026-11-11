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

// ---- selection: begin (WP-30 test performance, C) ----
// Which scripts this session runs.  DASH_CERT_SHARD=k/N runs shard k of N
// (N 2 to 8, the table below), so that scripts/run_cert_suite.sh can run N
// sessions side by side; DASH_CERT_ONLY="test_a test_b" runs only the
// scripts it names (a subset, by hand, whatever their tier).
// DASH_CERT_TIER (22oct2026) picks the tier: default (or unset), every
// script but the release tier's (the _cert_release line under the table:
// the closed work packages' truth scripts); release, those alone; all,
// every script.  Unset, the session runs the default tier's scripts.
// Each block below runs when its script is in _cert_run, and the log says
// which shard and tier this is ([SHARD] k/N, [ TIER] <tier>), so that
// scripts/cert_verdict.py can judge the shards' logs together.  A script
// whose shards are * runs in every shard and splits itself, reading
// DASH_CERT_SHARD (test_wp30_truth.cscript runs part k of N of its blocks).
// ---- shards: begin (scripts/cert_shards.py writes this block) ----
// Each certification script: the seconds it takes, 1 when it runs
// dash serve on a fixed port (5006, 5097, 5098, 5099), and its shard
// when DASH_CERT_SHARD splits the run in 2 to 8 (a column each):
// longest first onto the least loaded shard, the fixed-port scripts
// as one unit so that they never serve at once; *r when a script
// runs in every shard and splits itself (it reads DASH_CERT_SHARD),
// its parts turned by r (cert_helpers.do's cert_split_part: session
// k runs part ((k - 1 - r) mod N) + 1), the turns chosen to even the
// sessions before the other scripts are placed.  Unset, the run is
// every script, in this session.
// Seconds: an eight-session run of 11nov2026 under set rmsg on (its [
// TIME] lines summed; test_mata_autoload, which prints none, 0.5 s; the
// release tier keeps its seconds)
local _cert_shards ///
    test_abbreviations.cscript          119.8 0  2 1 4 4 2 5 1 ///
    test_ado_loads.cscript                0.2 0  2 3 2 1 4 4 3 ///
    test_adversarial.cscript             21.6 0  2 1 1 4 2 5 7 ///
    test_alias_semantics.cscript         20.9 0  2 2 1 5 3 7 4 ///
    test_bug_regressions.cscript         22.5 1  1 2 4 1 5 3 4 ///
    test_by_suboptions.cscript           72.0 0  1 2 3 4 3 6 5 ///
    test_caller_version.cscript           1.3 0  1 2 1 4 1 6 2 ///
    test_ci_band_options.cscript          8.7 0  1 1 3 5 4 3 4 ///
    test_clear_registry.cscript           0.4 0  1 1 3 4 5 5 8 ///
    test_conformance.cscript             19.4 0  2 2 3 2 3 2 1 ///
    test_custom_scheme.cscript           16.5 0  1 2 2 3 2 6 3 ///
    test_e2e_filters.cscript             10.3 0  1 3 4 2 4 2 7 ///
    test_e2e_kpi.cscript                  5.8 0  1 2 1 3 5 5 2 ///
    test_e2e_multi.cscript               10.2 0  2 1 4 4 3 7 2 ///
    test_e2e_serve.cscript               18.3 1  1 2 4 1 5 3 4 ///
    test_e2e_single.cscript               6.8 0  1 2 4 4 6 7 5 ///
    test_echo_text.cscript                2.8 0  2 3 4 1 2 1 5 ///
    test_env_guards.cscript              11.8 1  1 2 4 1 5 3 4 ///
    test_examples_run.cscript            28.0 0  1 1 4 5 3 4 3 ///
    test_export.cscript                  10.0 0  2 2 2 2 1 4 6 ///
    test_filter_label.cscript             1.1 0  2 3 3 5 6 5 2 ///
    test_gaps2_truth.cscript             20.4 0  2 3 3 4 1 3 3 ///
    test_graph_option_scope.cscript       1.3 0  2 1 3 3 3 2 4 ///
    test_help_claims_1.cscript           21.3 0  1 3 4 3 4 2 2 ///
    test_help_claims_2.cscript           20.7 0  1 1 2 2 5 4 5 ///
    test_help_claims_3.cscript            8.4 0  2 3 3 3 3 2 3 ///
    test_help_claims_4.cscript           12.9 1  1 2 4 1 5 3 4 ///
    test_help_claims_5.cscript           17.1 0  2 3 1 4 1 3 5 ///
    test_help_claims_6.cscript           20.2 0  1 2 4 1 2 6 8 ///
    test_help_claims_7.cscript           20.1 0  2 1 1 3 6 5 7 ///
    test_help_claims_8.cscript           10.2 0  1 3 1 1 5 1 1 ///
    test_help_examples.cscript           27.6 0  2 3 3 2 1 3 1 ///
    test_json_escaping.cscript           29.6 0  2 1 3 1 5 5 8 ///
    test_mata_autoload.cscript            0.5 0  2 2 4 4 2 6 8 ///
    test_mata_library_guard.cscript      29.4 0  1 3 2 4 2 2 4 ///
    test_nodraw_honoured.cscript          1.2 0  1 2 1 4 5 6 7 ///
    test_option_report_paren.cscript      0.4 0  1 2 4 3 3 3 4 ///
    test_option_surface.cscript          28.5 0  2 2 1 3 4 7 5 ///
    test_option_validation.cscript      139.7 0  1 2 3 2 1 4 7 ///
    test_parser.cscript                  86.6 0  2 3 2 1 3 2 8 ///
    test_parser_integrity.cscript         1.6 0  1 1 2 3 5 5 8 ///
    test_path_validation.cscript          5.1 0  2 3 1 5 1 1 1 ///
    test_program_coverage.cscript        22.8 0  1 2 2 1 5 6 8 ///
    test_qualifier_in_stata.cscript     210.7 0  2 3 1 5 6 1 6 ///
    test_qualifier_literals.cscript      39.2 0  2 1 1 3 5 6 3 ///
    test_registry_collision.cscript      13.8 0  2 1 3 5 6 5 8 ///
    test_render_locate.cscript            9.6 1  1 2 4 1 5 3 4 ///
    test_render_log_clean.cscript         3.8 0  2 1 4 2 3 3 6 ///
    test_resource_limits.cscript          6.4 0  2 1 2 1 2 6 7 ///
    test_serve_browser.cscript            3.5 1  1 2 4 1 5 3 4 ///
    test_serve_launch.cscript            24.3 1  1 2 4 1 5 3 4 ///
    test_serve_options.cscript            3.1 0  1 3 3 5 6 7 1 ///
    test_server_build.cscript             4.6 0  1 2 2 2 4 4 8 ///
    test_setup_honesty.cscript           32.3 0  2 3 2 3 4 3 5 ///
    test_setup_injection.cscript          0.0 0  2 1 2 1 6 5 3 ///
    test_setup_python_gate.cscript        0.0 0  2 1 2 1 6 5 3 ///
    test_setup_version_gate.cscript       0.5 0  1 2 2 3 2 1 4 ///
    test_statistical_options.cscript     19.8 0  1 3 2 5 4 7 2 ///
    test_string_values.cscript           34.3 0  1 1 3 2 2 2 3 ///
    test_suboption_reporting.cscript     31.1 0  1 2 4 2 1 6 3 ///
    test_textbox_multiline.cscript        0.5 0  2 3 1 2 1 7 7 ///
    test_theme_escaping.cscript           0.8 0  1 1 2 1 4 2 3 ///
    test_tokenizer.cscript                0.2 0  2 1 1 2 4 2 7 ///
    test_twoway_option_parity.cscript   125.8 0  1 1 2 3 4 7 2 ///
    test_utf8_validation.cscript          0.2 0  1 3 3 4 2 6 2 ///
    test_varlist_expansion.cscript       17.2 0  1 1 4 1 5 4 4 ///
    test_wp29_truth.cscript             138.4 1  1 2 4 1 5 3 4 ///
    test_wp30_truth.cscript             628.1 0  *1 * *1 * *2 *3 *1 ///
    test_wp31_truth.cscript             520.1 0  * * *3 *4 * *4 *5 ///
    test_wp33_truth.cscript              76.3 0  *1 *2 *1 *4 *4 *5 *6 ///
    test_wp34_truth.cscript              55.2 0  * *1 * *3 *1 *2 *7 ///
    test_wp35_truth.cscript              70.7 0  * *1 *3 *2 *5 *6 *4 ///
    test_wp36_truth.cscript               4.8 0  * *2 * *4 *4 *4 * ///
    test_wp37_truth.cscript              33.9 0  * *1 *2 *3 *3 *3 *2 ///
    test_wp38_truth.cscript               6.3 0  * *2 *3 *2 *1 *3 *5 ///
    test_wp40_truth.cscript              36.2 0  *1 * *1 *1 *3 *1 *1 ///
    test_wp41_truth.cscript              19.1 0  * *2 *3 *2 *4 *6 *5 ///
    test_wp42_truth.cscript             101.6 0  * * *2 *1 *2 *3 *2 ///
    test_wp43_truth.cscript             164.4 0  * * * * * * * ///
    test_wp44_truth.cscript             104.6 0  * *2 *1 * *2 *4 *3 ///
    test_wp45_truth.cscript             105.7 0  * *2 *2 *3 * *1 *7 ///
    test_wp46_truth.cscript               8.2 0  *1 *1 *2 *3 *1 *3 *4 ///
    test_wp47_truth.cscript              42.1 0  *1 *2 * * *5 *4 *1
// The release tier: the closed work packages' truth scripts,
// which a default run (make cert, make test-all) leaves out and
// DASH_CERT_TIER=release or all runs (make cert-release, make
// cert-all, make gate); their shards are placed on top of the
// default tier's balance.
local _cert_release test_wp29_truth.cscript test_wp30_truth.cscript test_wp31_truth.cscript
// ---- shards: end ----
local _cert_sh : environment DASH_CERT_SHARD
mata: st_local("_cert_ok", strofreal(st_local("_cert_sh") == "" | ustrregexm(st_local("_cert_sh"), "^[1-8]/[1-8]$")))
local _cert_k 1
local _cert_N 1
if `_cert_ok' & "`_cert_sh'" != "" {
    local _cert_k = real(substr("`_cert_sh'", 1, 1))
    local _cert_N = real(substr("`_cert_sh'", 3, 1))
}
if !`_cert_ok' | `_cert_k' > `_cert_N' {
    display as error "run_all_cscripts.do: DASH_CERT_SHARD must be k/N, 1 <= k <= N <= 8"
    exit 198
}
local _cert_only : environment DASH_CERT_ONLY
mata: st_local("_cert_ok", strofreal(ustrregexm(st_local("_cert_only"), "^[ A-Za-z0-9_.]*$")))
if !`_cert_ok' {
    display as error "run_all_cscripts.do: DASH_CERT_ONLY holds script names only (letters, digits, _ and .)"
    exit 198
}
local _cert_tier : environment DASH_CERT_TIER
mata: st_local("_cert_ok", strofreal(ustrregexm(st_local("_cert_tier"), "^(default|release|all)?$")))
if !`_cert_ok' {
    display as error "run_all_cscripts.do: DASH_CERT_TIER must be default, release or all"
    exit 198
}
if "`_cert_tier'" == "" local _cert_tier default
local _cert_all ""
local _cert_run ""
local _cert_rest : copy local _cert_shards
while `"`_cert_rest'"' != "" {
    gettoken _cert_s _cert_rest : _cert_rest
    gettoken _cert_t _cert_rest : _cert_rest
    gettoken _cert_p _cert_rest : _cert_rest
    forvalues _cert_n = 2/8 {
        gettoken _cert_`_cert_n' _cert_rest : _cert_rest
    }
    local _cert_all `_cert_all' `_cert_s'
    local _cert_at 1
    if `_cert_N' > 1 local _cert_at `_cert_`_cert_N''
    if substr("`_cert_at'", 1, 1) == "*" | "`_cert_at'" == "`_cert_k'" local _cert_run `_cert_run' `_cert_s'
}
if "`_cert_only'" != "" {
    local _cert_want ""
    foreach _cert_o of local _cert_only {
        if substr("`_cert_o'", -8, .) != ".cscript" local _cert_o "`_cert_o'.cscript"
        local _cert_in : list _cert_o in _cert_all
        if !`_cert_in' {
            display as error "run_all_cscripts.do: DASH_CERT_ONLY names `_cert_o', which this runner does not run"
            exit 198
        }
        local _cert_want `_cert_want' `_cert_o'
    }
    local _cert_run : list _cert_run & _cert_want
}
else {
    if "`_cert_tier'" == "default" local _cert_run : list _cert_run - _cert_release
    if "`_cert_tier'" == "release" local _cert_run : list _cert_run & _cert_release
}
local _cert_nrun : word count `_cert_run'
local _cert_nall : word count `_cert_all'
// ---- selection: end ----

display as text ""
display as text "============================================================"
display as text "  dash certification script runner"
display as text "  `c(current_date)' `c(current_time)'"
display as text "============================================================"
display as text ""
display as text "[SHARD] `_cert_k'/`_cert_N': `_cert_nrun' of `_cert_nall' scripts"
display as text "[ TIER] `_cert_tier'"
display as text "[ PLAN] `_cert_run'"
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

// WP-36 plat:PT-1 (M8): no script decides whether Python is there; with no
// Python set, Stata finds one on the first python: line.

// Scripts run under -capture noisily-, not bare -capture-.  Quiet capture
// suppresses everything the scripts display, which hid the SKIP: messages
// and broke any check that verifies dash's own output -- a test of the
// unsupported-option note cannot see the note if the note is suppressed.
// ----------------------------------------------------------------
// 1. test_tokenizer.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_tokenizer.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_tokenizer.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_tokenizer.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_tokenizer.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_tokenizer.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 2. test_parser.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_parser.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_parser.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_parser.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_parser.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_parser.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 4. test_e2e_single.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_e2e_single.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_e2e_single.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_e2e_single.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_e2e_single.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_e2e_single.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 5. test_e2e_multi.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_e2e_multi.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_e2e_multi.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_e2e_multi.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_e2e_multi.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_e2e_multi.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 6. test_e2e_filters.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_e2e_filters.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_e2e_filters.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_e2e_filters.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_e2e_filters.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_e2e_filters.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 7. test_e2e_kpi.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_e2e_kpi.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_e2e_kpi.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_e2e_kpi.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_e2e_kpi.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_e2e_kpi.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 8. test_ado_loads.cscript (Bug 15 + 16 regression)
// Run from testdir — uses explicit do "../dash_parse.mata" + do "../dash.ado"
// ----------------------------------------------------------------
local _cert_go : list posof "test_ado_loads.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_ado_loads.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_ado_loads.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_ado_loads.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_ado_loads.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 9. test_mata_autoload.cscript (Bug 16 regression — auto-load)
// MUST run from dashdir so findfile finds dash_parse.mata via "." in adopath.
// ----------------------------------------------------------------
local _cert_go : list posof "test_mata_autoload.cscript" in _cert_run
if `_cert_go' {
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
}

// ----------------------------------------------------------------
// 10. test_adversarial.cscript (security suite)
// Previously never invoked by this runner despite existing on disk, so the
// adversarial security checks were dead weight.  See CLAUDE.md rule 18.
// ----------------------------------------------------------------
local _cert_go : list posof "test_adversarial.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_adversarial.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_adversarial.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_adversarial.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_adversarial.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 11. test_e2e_serve.cscript (server mode end-to-end)
// Also previously never invoked.  Server mode has known defects that
// section 14 of the plan fixes; a failure here is expected until then and
// is informative rather than spurious.
// ----------------------------------------------------------------
local _cert_go : list posof "test_e2e_serve.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_e2e_serve.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_e2e_serve.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_e2e_serve.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_e2e_serve.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 12. test_abbreviations.cscript
// Stata-derived abbreviation conformance (section 04)
// ----------------------------------------------------------------
local _cert_go : list posof "test_abbreviations.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_abbreviations.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_abbreviations.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_abbreviations.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_abbreviations.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 13. test_option_surface.cscript
// every twoway command in the corpus must run (section 05)
// ----------------------------------------------------------------
local _cert_go : list posof "test_option_surface.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_option_surface.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_option_surface.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_option_surface.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_option_surface.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 14. test_varlist_expansion.cscript
// varlist and plot-spec correctness (section 06)
// ----------------------------------------------------------------
local _cert_go : list posof "test_varlist_expansion.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_varlist_expansion.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_varlist_expansion.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_varlist_expansion.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_varlist_expansion.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 15. test_path_validation.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_path_validation.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_path_validation.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_path_validation.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_path_validation.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_path_validation.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 16. test_setup_version_gate.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_setup_version_gate.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_setup_version_gate.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_setup_version_gate.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_setup_version_gate.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_setup_version_gate.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 17. test_clear_registry.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_clear_registry.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_clear_registry.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_clear_registry.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_clear_registry.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_clear_registry.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 19. test_filter_label.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_filter_label.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_filter_label.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_filter_label.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_filter_label.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_filter_label.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 20. test_server_build.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_server_build.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_server_build.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_server_build.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_server_build.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_server_build.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 18. test_examples_run.cscript
// ----------------------------------------------------------------
// Runs last: it is the slowest script, and it is the end-to-end gate.
local _cert_go : list posof "test_examples_run.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_examples_run.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_examples_run.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_examples_run.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_examples_run.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 21. test_serve_options.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_serve_options.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_serve_options.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_serve_options.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_serve_options.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_serve_options.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 22. test_render_log_clean.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_render_log_clean.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_render_log_clean.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_render_log_clean.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_render_log_clean.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_render_log_clean.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 23. test_option_report_paren.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_option_report_paren.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_option_report_paren.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_option_report_paren.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_option_report_paren.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_option_report_paren.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 24. test_setup_python_gate.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_setup_python_gate.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_setup_python_gate.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_setup_python_gate.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_setup_python_gate.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_setup_python_gate.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 25. test_conformance.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_conformance.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_conformance.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_conformance.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_conformance.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_conformance.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 26. test_parser_integrity.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_parser_integrity.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_parser_integrity.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_parser_integrity.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_parser_integrity.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_parser_integrity.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 27. test_textbox_multiline.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_textbox_multiline.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_textbox_multiline.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_textbox_multiline.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_textbox_multiline.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_textbox_multiline.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 28. test_serve_launch.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_serve_launch.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_serve_launch.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_serve_launch.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_serve_launch.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_serve_launch.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 29. test_registry_collision.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_registry_collision.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_registry_collision.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_registry_collision.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_registry_collision.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_registry_collision.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 30. test_graph_option_scope.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_graph_option_scope.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_graph_option_scope.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_graph_option_scope.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_graph_option_scope.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_graph_option_scope.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 31. test_render_locate.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_render_locate.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_render_locate.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_render_locate.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_render_locate.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_render_locate.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 32. test_theme_escaping.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_theme_escaping.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_theme_escaping.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_theme_escaping.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_theme_escaping.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_theme_escaping.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 33. test_setup_honesty.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_setup_honesty.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_setup_honesty.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_setup_honesty.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_setup_honesty.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_setup_honesty.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 34. test_env_guards.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_env_guards.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_env_guards.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_env_guards.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_env_guards.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_env_guards.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 35. test_utf8_validation.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_utf8_validation.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_utf8_validation.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_utf8_validation.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_utf8_validation.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_utf8_validation.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 36. test_json_escaping.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_json_escaping.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_json_escaping.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_json_escaping.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_json_escaping.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_json_escaping.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 37. test_by_suboptions.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_by_suboptions.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_by_suboptions.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_by_suboptions.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_by_suboptions.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_by_suboptions.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 38. test_nodraw_honoured.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_nodraw_honoured.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_nodraw_honoured.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_nodraw_honoured.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_nodraw_honoured.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_nodraw_honoured.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 39. test_alias_semantics.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_alias_semantics.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_alias_semantics.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_alias_semantics.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_alias_semantics.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_alias_semantics.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 40. test_suboption_reporting.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_suboption_reporting.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_suboption_reporting.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_suboption_reporting.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_suboption_reporting.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_suboption_reporting.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 41. test_option_validation.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_option_validation.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_option_validation.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_option_validation.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_option_validation.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_option_validation.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 42. test_custom_scheme.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_custom_scheme.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_custom_scheme.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_custom_scheme.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_custom_scheme.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_custom_scheme.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 43. test_statistical_options.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_statistical_options.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_statistical_options.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_statistical_options.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_statistical_options.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_statistical_options.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 44. test_caller_version.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_caller_version.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_caller_version.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_caller_version.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_caller_version.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_caller_version.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 45. test_resource_limits.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_resource_limits.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_resource_limits.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_resource_limits.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_resource_limits.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_resource_limits.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 46. test_serve_browser.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_serve_browser.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_serve_browser.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_serve_browser.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_serve_browser.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_serve_browser.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 47. test_setup_injection.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_setup_injection.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_setup_injection.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_setup_injection.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_setup_injection.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_setup_injection.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 48. test_echo_text.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_echo_text.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_echo_text.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_echo_text.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_echo_text.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_echo_text.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 49. test_export.cscript
// ----------------------------------------------------------------
local _cert_go : list posof "test_export.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_export.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_export.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_export.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_export.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 50. test_twoway_option_parity.cscript (WP-22 TR-22.3)
// ----------------------------------------------------------------
local _cert_go : list posof "test_twoway_option_parity.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_twoway_option_parity.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_twoway_option_parity.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_twoway_option_parity.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_twoway_option_parity.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 51. test_help_claims_1.cscript (WP-23: help lines 1-316, syntax, plot types, differences)
// ----------------------------------------------------------------
local _cert_go : list posof "test_help_claims_1.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_help_claims_1.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_help_claims_1.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_help_claims_1.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_help_claims_1.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 52. test_help_claims_2.cscript (WP-23: option values, subcommands, dashboard options, export)
// ----------------------------------------------------------------
local _cert_go : list posof "test_help_claims_2.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_help_claims_2.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_help_claims_2.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_help_claims_2.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_help_claims_2.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 53. test_help_claims_3.cscript (WP-23: layout, tabs, linking, toolbar, filters)
// ----------------------------------------------------------------
local _cert_go : list posof "test_help_claims_3.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_help_claims_3.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_help_claims_3.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_help_claims_3.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_help_claims_3.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 54. test_help_claims_4.cscript (WP-23: KPI cards and server mode, a real dash serve)
// ----------------------------------------------------------------
local _cert_go : list posof "test_help_claims_4.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_help_claims_4.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_help_claims_4.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_help_claims_4.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_help_claims_4.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 55. test_help_claims_5.cscript (WP-23: resource limits, faceting, marker labels)
// ----------------------------------------------------------------
local _cert_go : list posof "test_help_claims_5.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_help_claims_5.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_help_claims_5.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_help_claims_5.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_help_claims_5.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 56. test_help_claims_6.cscript (WP-23: statistical layers and weights)
// ----------------------------------------------------------------
local _cert_go : list posof "test_help_claims_6.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_help_claims_6.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_help_claims_6.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_help_claims_6.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_help_claims_6.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 57. test_help_claims_7.cscript (WP-23: regions, axes, colour, geometry, markers)
// ----------------------------------------------------------------
local _cert_go : list posof "test_help_claims_7.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_help_claims_7.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_help_claims_7.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_help_claims_7.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_help_claims_7.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 58. test_help_claims_8.cscript (WP-23: schemes, the Unsupported list, dependencies)
// ----------------------------------------------------------------
local _cert_go : list posof "test_help_claims_8.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_help_claims_8.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_help_claims_8.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_help_claims_8.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_help_claims_8.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 59. test_help_examples.cscript (WP-23: every example command in the help, run)
// ----------------------------------------------------------------
local _cert_go : list posof "test_help_examples.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_help_examples.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_help_examples.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_help_examples.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_help_examples.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 60. test_bug_regressions.cscript (WP-24: the regression tests three closed BUGS.md entries lacked)
// ----------------------------------------------------------------
local _cert_go : list posof "test_bug_regressions.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_bug_regressions.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_bug_regressions.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_bug_regressions.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_bug_regressions.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 61. test_program_coverage.cscript (WP-24 AC-24.3, GAPS L7: dash_setup end to end, display formats)
// ----------------------------------------------------------------
local _cert_go : list posof "test_program_coverage.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_program_coverage.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_program_coverage.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_program_coverage.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_program_coverage.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 62. test_qualifier_literals.cscript (WP-24: a qualifier's string literals select the rows Stata selects)
// ----------------------------------------------------------------
local _cert_go : list posof "test_qualifier_literals.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_qualifier_literals.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_qualifier_literals.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_qualifier_literals.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_qualifier_literals.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 63. test_mata_library_guard.cscript (WP-24: the Mata library guard refuses a library missing any function dash calls, and mends one it can)
// ----------------------------------------------------------------
local _cert_go : list posof "test_mata_library_guard.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_mata_library_guard.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_mata_library_guard.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_mata_library_guard.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_mata_library_guard.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 64. test_qualifier_in_stata.cscript (WP-27: every qualifier dash writes is evaluated in Stata, and both modes draw Stata's rows)
// ----------------------------------------------------------------
local _cert_go : list posof "test_qualifier_in_stata.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_qualifier_in_stata.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_qualifier_in_stata.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_qualifier_in_stata.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_qualifier_in_stata.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 65. test_string_values.cscript (WP-27: every string value, label and number reaches both renderers byte for byte; the export no longer uses jsonio)
// ----------------------------------------------------------------
local _cert_go : list posof "test_string_values.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_string_values.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_string_values.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_string_values.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_string_values.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 66. test_ci_band_options.cscript (S3 batch: a ci fit's band is drawn in the scheme's ci style and takes twoway's fitarea options)
// ----------------------------------------------------------------
local _cert_go : list posof "test_ci_band_options.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_ci_band_options.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_ci_band_options.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_ci_band_options.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_ci_band_options.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 67. test_gaps2_truth.cscript (WP-28: the one certification script for
// every twoway/Stata-value comparison the GAPS2 fix package needs; one
// block per section, appended above its own "append new blocks above
// this line" marker -- review D11)
// ----------------------------------------------------------------
local _cert_go : list posof "test_gaps2_truth.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_gaps2_truth.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_gaps2_truth.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_gaps2_truth.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_gaps2_truth.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 68. test_wp29_truth.cscript (WP-29: the one certification script for
// every twoway/Stata-value comparison the drop-in P0 package needs; one
// block per section, appended above its own "append new blocks above
// this line" marker -- .ultraplan/wp29/index.md A3)
// ----------------------------------------------------------------
local _cert_go : list posof "test_wp29_truth.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_wp29_truth.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_wp29_truth.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_wp29_truth.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_wp29_truth.cscript"
    capture noisily profiler report
}
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
}

// ----------------------------------------------------------------
// 69. test_wp30_truth.cscript (WP-30: the one certification script for
// every twoway/Stata-value comparison the drop-in P1 package needs; one
// block per section, S01's scaffold and one block for each of S02-S57,
// above its "append new blocks above this line" marker --
// .ultraplan/wp30/index.md A142).  It runs in every shard, each session
// running its own part of the blocks (DASH_CERT_SHARD).
// ----------------------------------------------------------------
local _cert_go : list posof "test_wp30_truth.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_wp30_truth.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_wp30_truth.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_wp30_truth.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_wp30_truth.cscript"
    capture noisily profiler report
}
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
}

// 70. test_wp31_truth.cscript (WP-31: the one certification script for
// every twoway/Stata-value comparison the drop-in GAPS3 package needs; one
// block per GAPS3 row, S01's scaffold and the blocks S02-S60 append,
// above its "append new blocks above this line" marker --
// .ultraplan/sections/index.md A5).  It runs in every shard, each session
// running its own part of the blocks (DASH_CERT_SHARD).
// ----------------------------------------------------------------
local _cert_go : list posof "test_wp31_truth.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_wp31_truth.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_wp31_truth.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_wp31_truth.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_wp31_truth.cscript"
    capture noisily profiler report
}
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_wp31_truth.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_wp31_truth.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_wp31_truth.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}
}

// 71. test_wp33_truth.cscript (WP-33: the one certification script for
// every twoway/Stata-value comparison WP-33's sections need; S00's
// scaffold and one block per GAPS4 row or harness tool, above its "append
// new blocks above this line" marker -- .ultraplan/sections/index.md
// PD-6).  It runs in every shard, each session running its own part of
// the blocks (DASH_CERT_SHARD).
// ----------------------------------------------------------------
local _cert_go : list posof "test_wp33_truth.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_wp33_truth.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_wp33_truth.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_wp33_truth.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_wp33_truth.cscript"
    capture noisily profiler report
}
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_wp33_truth.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_wp33_truth.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_wp33_truth.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}
}

// 72. test_wp34_truth.cscript (WP-34: the one certification script for
// every twoway/Stata-value comparison WP-34's sections need; S00's
// scaffold and one block per GAPS4 row or harness tool, above its "append
// new blocks above this line" marker -- .ultraplan/sections/index.md
// PD-6).  It runs in every shard, each session running its own part of
// the blocks (DASH_CERT_SHARD).
// ----------------------------------------------------------------
local _cert_go : list posof "test_wp34_truth.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_wp34_truth.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_wp34_truth.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_wp34_truth.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_wp34_truth.cscript"
    capture noisily profiler report
}
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_wp34_truth.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_wp34_truth.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_wp34_truth.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}
}

// 73. test_wp35_truth.cscript (WP-35: the one certification script for
// every twoway/Stata-value comparison WP-35's sections need; S00's
// scaffold and one block per GAPS4 row or harness tool, above its "append
// new blocks above this line" marker -- .ultraplan/sections/index.md
// PD-6).  It runs in every shard, each session running its own part of
// the blocks (DASH_CERT_SHARD).
// ----------------------------------------------------------------
local _cert_go : list posof "test_wp35_truth.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_wp35_truth.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_wp35_truth.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_wp35_truth.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_wp35_truth.cscript"
    capture noisily profiler report
}
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_wp35_truth.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_wp35_truth.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_wp35_truth.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}
}

// 74. test_wp36_truth.cscript (WP-36: the one certification script for
// every twoway/Stata-value comparison WP-36's sections need; S00's
// scaffold and one block per GAPS4 row or harness tool, above its "append
// new blocks above this line" marker -- .ultraplan/sections/index.md
// PD-6).  It runs in every shard, each session running its own part of
// the blocks (DASH_CERT_SHARD).
// ----------------------------------------------------------------
local _cert_go : list posof "test_wp36_truth.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_wp36_truth.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_wp36_truth.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_wp36_truth.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_wp36_truth.cscript"
    capture noisily profiler report
}
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_wp36_truth.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_wp36_truth.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_wp36_truth.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}
}

// 75. test_wp37_truth.cscript (WP-37: the one certification script for
// every twoway/Stata-value comparison WP-37's sections need; S00's
// scaffold and one block per GAPS4 row or harness tool, above its "append
// new blocks above this line" marker -- .ultraplan/sections/index.md
// PD-6).  It runs in every shard, each session running its own part of
// the blocks (DASH_CERT_SHARD).
// ----------------------------------------------------------------
local _cert_go : list posof "test_wp37_truth.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_wp37_truth.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_wp37_truth.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_wp37_truth.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_wp37_truth.cscript"
    capture noisily profiler report
}
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_wp37_truth.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_wp37_truth.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_wp37_truth.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}
}

// 76. test_wp38_truth.cscript (WP-38: the one certification script for
// every twoway/Stata-value comparison WP-38's sections need; S00's
// scaffold and one block per GAPS4 row or harness tool, above its "append
// new blocks above this line" marker -- .ultraplan/sections/index.md
// PD-6).  It runs in every shard, each session running its own part of
// the blocks (DASH_CERT_SHARD).
// ----------------------------------------------------------------
local _cert_go : list posof "test_wp38_truth.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_wp38_truth.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_wp38_truth.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_wp38_truth.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_wp38_truth.cscript"
    capture noisily profiler report
}
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_wp38_truth.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_wp38_truth.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_wp38_truth.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}
}

// 77. test_wp40_truth.cscript (WP-40: the one certification script for
// every twoway/Stata-value comparison WP-40's sections need; S00's
// scaffold and one block per GAPS4 row or harness tool, above its "append
// new blocks above this line" marker -- .ultraplan/sections/index.md
// PD-6).  It runs in every shard, each session running its own part of
// the blocks (DASH_CERT_SHARD).
// ----------------------------------------------------------------
local _cert_go : list posof "test_wp40_truth.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_wp40_truth.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_wp40_truth.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_wp40_truth.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_wp40_truth.cscript"
    capture noisily profiler report
}
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_wp40_truth.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_wp40_truth.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_wp40_truth.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}
}

// 78. test_wp41_truth.cscript (WP-41: the one certification script for
// every twoway/Stata-value comparison WP-41's sections need; S00's
// scaffold and one block per GAPS4 row or harness tool, above its "append
// new blocks above this line" marker -- .ultraplan/sections/index.md
// PD-6).  It runs in every shard, each session running its own part of
// the blocks (DASH_CERT_SHARD).
// ----------------------------------------------------------------
local _cert_go : list posof "test_wp41_truth.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_wp41_truth.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_wp41_truth.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_wp41_truth.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_wp41_truth.cscript"
    capture noisily profiler report
}
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_wp41_truth.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_wp41_truth.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_wp41_truth.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}
}

// 79. test_wp42_truth.cscript (WP-42: the one certification script for
// every twoway/Stata-value comparison WP-42's sections need; S00's
// scaffold and one block per GAPS4 row or harness tool, above its "append
// new blocks above this line" marker -- .ultraplan/sections/index.md
// PD-6).  It runs in every shard, each session running its own part of
// the blocks (DASH_CERT_SHARD).
// ----------------------------------------------------------------
local _cert_go : list posof "test_wp42_truth.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_wp42_truth.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_wp42_truth.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_wp42_truth.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_wp42_truth.cscript"
    capture noisily profiler report
}
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_wp42_truth.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_wp42_truth.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_wp42_truth.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}
}

// 80. test_wp43_truth.cscript (WP-43: the one certification script for
// every twoway/Stata-value comparison WP-43's sections need; S00's
// scaffold and one block per GAPS4 row or harness tool, above its "append
// new blocks above this line" marker -- .ultraplan/sections/index.md
// PD-6).  It runs in every shard, each session running its own part of
// the blocks (DASH_CERT_SHARD).
// ----------------------------------------------------------------
local _cert_go : list posof "test_wp43_truth.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_wp43_truth.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_wp43_truth.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_wp43_truth.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_wp43_truth.cscript"
    capture noisily profiler report
}
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_wp43_truth.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_wp43_truth.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_wp43_truth.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}
}

// 81. test_wp44_truth.cscript (WP-44: the one certification script for
// every twoway/Stata-value comparison WP-44's sections need; S00's
// scaffold and one block per GAPS4 row or harness tool, above its "append
// new blocks above this line" marker -- .ultraplan/sections/index.md
// PD-6).  It runs in every shard, each session running its own part of
// the blocks (DASH_CERT_SHARD).
// ----------------------------------------------------------------
local _cert_go : list posof "test_wp44_truth.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_wp44_truth.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_wp44_truth.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_wp44_truth.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_wp44_truth.cscript"
    capture noisily profiler report
}
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_wp44_truth.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_wp44_truth.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_wp44_truth.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}
}

// 82. test_wp45_truth.cscript (WP-45: the one certification script for
// every twoway/Stata-value comparison WP-45's sections need; S00's
// scaffold and one block per GAPS4 row or harness tool, above its "append
// new blocks above this line" marker -- .ultraplan/sections/index.md
// PD-6).  It runs in every shard, each session running its own part of
// the blocks (DASH_CERT_SHARD).
// ----------------------------------------------------------------
local _cert_go : list posof "test_wp45_truth.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_wp45_truth.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_wp45_truth.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_wp45_truth.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_wp45_truth.cscript"
    capture noisily profiler report
}
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_wp45_truth.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_wp45_truth.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_wp45_truth.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}
}

// 83. test_wp46_truth.cscript (WP-46: the one certification script for
// every twoway/Stata-value comparison WP-46's sections need; S00's
// scaffold and one block per GAPS4 row or harness tool, above its "append
// new blocks above this line" marker -- .ultraplan/sections/index.md
// PD-6).  It runs in every shard, each session running its own part of
// the blocks (DASH_CERT_SHARD).
// ----------------------------------------------------------------
local _cert_go : list posof "test_wp46_truth.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_wp46_truth.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_wp46_truth.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_wp46_truth.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_wp46_truth.cscript"
    capture noisily profiler report
}
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_wp46_truth.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_wp46_truth.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_wp46_truth.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}
}

// 84. test_wp47_truth.cscript (WP-47: the one certification script for
// every twoway/Stata-value comparison WP-47's sections need; S00's
// scaffold and one block per GAPS4 row or harness tool, above its "append
// new blocks above this line" marker -- .ultraplan/sections/index.md
// PD-6).  It runs in every shard, each session running its own part of
// the blocks (DASH_CERT_SHARD).
// ----------------------------------------------------------------
local _cert_go : list posof "test_wp47_truth.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_wp47_truth.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_wp47_truth.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_wp47_truth.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_wp47_truth.cscript"
    capture noisily profiler report
}
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_wp47_truth.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_wp47_truth.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_wp47_truth.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}
}

// 85. test_wp49_truth.cscript (WP-49: the one certification script for
// every twoway/Stata-value comparison WP-49's sections need; S00's
// scaffold and one block per GAPS4 row or harness tool, above its "append
// new blocks above this line" marker -- .ultraplan/sections/index.md
// PD-6).  It runs in every shard, each session running its own part of
// the blocks (DASH_CERT_SHARD).
// ----------------------------------------------------------------
local _cert_go : list posof "test_wp49_truth.cscript" in _cert_run
if `_cert_go' {
display as text "[ RUN ] test_wp49_truth.cscript"
cd "`testdir'"
local _cert_c0 = clock(c(current_date) + " " + c(current_time), "DMYhms")
capture noisily {
    do "test_wp49_truth.cscript"
}
local rc = _rc
// Timing (timer 100, started by the script after its clear all; the
// wall clock survives a script that clears all again).
capture timer off 100
quietly timer list 100
local _cert_t = r(t100)
local _cert_w = (clock(c(current_date) + " " + c(current_time), "DMYhms") - `_cert_c0') / 1000
display as text "[ TIME] test_wp49_truth.cscript timer=" %9.3f `_cert_t' "s wall=" %6.0f `_cert_w' "s"
local _cert_prof : environment DASH_CERT_PROFILE
if "`_cert_prof'" != "" {
    capture profiler off
    display as text "[PROFILE] test_wp49_truth.cscript"
    capture noisily profiler report
}
capture file close _all
capture log close _all
cd "`dashdir'"
if `rc' == 222 {
    display as text "[ SKIP] test_wp49_truth.cscript  (dependency unavailable)"
    local n_skip = `n_skip' + 1
}
else if `rc' == 0 {
    display as text "[ PASS] test_wp49_truth.cscript"
    local n_pass = `n_pass' + 1
}
else {
    display as error "[ FAIL] test_wp49_truth.cscript  (rc=`rc')"
    local n_fail = `n_fail' + 1
}
}

// ----------------------------------------------------------------
// Summary
// ----------------------------------------------------------------
local n_total = `n_pass' + `n_fail' + `n_skip'
display as text ""
display as text "============================================================"
display as text "  Shard `_cert_k' of `_cert_N': `_cert_nrun' script(s) planned"
display as text "  Results: `n_pass' passed, `n_fail' failed, `n_skip' skipped  (of `n_total' total)"
display as text "============================================================"

if `n_fail' > 0 {
    display as error "SOME TESTS FAILED"
    exit 1
}
else if `n_pass' == 0 & `_cert_nrun' > 0 {
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
