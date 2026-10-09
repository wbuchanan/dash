*! cert_truth.do -- twoway's own answers for the certification scripts,
*! recorded once and replayed (WP-30 test performance, B2).
*!
*! test_twoway_option_parity.cscript, test_parser.cscript and
*! test_help_claims_6.cscript ask twoway, before each dash command, what it
*! does with the same command -- its return code, the words it logs, a
*! serset it draws, a count read off its SVG -- and hold dash to it.  The
*! answers change only when Stata does, and drawing them cost about 120 s of
*! every certification run.  cert_truth.py keeps them, for each script, in
*! test/fixtures/<name>_truth.json, and DASH_CERT_REMEASURE says where an
*! answer comes from:
*!
*!   unset or empty  the fixture (a question it has no answer for fails the
*!                   script: run scripts/extract_twoway_oracle_truth.do);
*!   1               twoway, asked in the run, and every answer is held to
*!                   the fixture's (the release and closeout run);
*!   record          twoway, asked in the run, every answer written to
*!                   DASH_CERT_TRUTH_OUT for the extractor.
*!
*! Use, after cscript, from test/ (the runner's working directory):
*!     do "cert_truth.do"
*!     cert_truth_init <name>        reads fixtures/<name>_truth.json
*!     cert_truth_ctx <label>        the case group of the next questions
*!     capture cert_tw twoway ...    _rc is twoway's return code
*!     cert_truth_close              r(problems): the run's problems, each
*!                                   printed "TRUTH FAIL ..."; the script
*!                                   fails when there is one
*! A script's own logging and drawing helpers call cert_truth.py through
*! the Python name _dct (log_put/log_get, val_put/val_get, data_put/
*! data_get, flag), passing the NAMES of their locals, so no command or
*! answer is ever expanded as a macro.  Python names made inside a Stata
*! program end with it, so each such program binds _dct for itself:
*!     python: _dct = __import__("sys").modules["_dash_cert_truth"]
*! and the script binds it once at its own level after cert_truth_init.

capture program drop cert_truth_init
program define cert_truth_init
    version 16.0
    args name
    local _ct_mode : environment DASH_CERT_REMEASURE
    local _ct_out  : environment DASH_CERT_TRUTH_OUT
    local _ct_dir "`c(pwd)'"
    capture confirm file "`_ct_dir'/cert_truth.py"
    if _rc {
        display as error "cert_truth_init: run from test/, where cert_truth.py is"
        exit 601
    }
    python: import importlib.util as _dct_iu, sys as _dct_sys
    python: from sfi import Macro as _dct_M
    python: _dct_spec = _dct_iu.spec_from_file_location("_dash_cert_truth", _dct_M.getLocal("_ct_dir") + "/cert_truth.py")
    python: _dct = _dct_iu.module_from_spec(_dct_spec)
    python: _dct_spec.loader.exec_module(_dct)
    python: _dct_sys.modules["_dash_cert_truth"] = _dct
    python: _dct_M.setLocal("_ct_m", _dct.open_truth(_dct_M.getLocal("name"), _dct_M.getLocal("_ct_dir"), _dct_M.getLocal("_ct_mode"), _dct_M.getLocal("_ct_out")))
    display as text "  twoway's answers for `name': `_ct_m'"
end

capture program drop cert_truth_ctx
program define cert_truth_ctx
    version 16.0
    args label
    python: _dct = __import__("sys").modules["_dash_cert_truth"]
    python: _dct.ctx(__import__("sfi").Macro.getLocal("label"))
end

// capture cert_tw twoway ...: exits with the twoway command's return code,
// twoway's own in a live run (recorded or held to the fixture), the
// fixture's in a replay -- 9 when the fixture has none, which
// cert_truth_close reports.  The command is read by value (macval), as
// the line that called this expanded it.
capture program drop cert_tw
program define cert_tw
    version 16.0
    mata: st_local("_ct_ok", strofreal(substr(st_local("0"), 1, 7) == "twoway "))
    if !`_ct_ok' {
        display as error "cert_tw: the command must start with twoway"
        exit 198
    }
    python: _dct = __import__("sys").modules["_dash_cert_truth"]
    python: _dct.flag("_ct_l")
    if `_ct_l' {
        capture noisily `macval(0)'
        local _ct_rc = _rc
        python: _dct.rc_put("0", "_ct_rc")
        exit `_ct_rc'
    }
    python: _dct.rc_get("0", "_ct_rc")
    if "`_ct_rc'" == "" exit 9
    exit `_ct_rc'
end

capture program drop cert_truth_close
program define cert_truth_close, rclass
    version 16.0
    python: _dct = __import__("sys").modules["_dash_cert_truth"]
    python: _dct.finish("_ct_n")
    if `_ct_n' == 0 display as text "  twoway's answers: no problem"
    return scalar problems = `_ct_n'
end
