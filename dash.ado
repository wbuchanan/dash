*! dash.ado  v2.0
*! Main entry point for the dash command — interactive HTML dashboards
*! from Stata twoway syntax.
*!
*! Subcommands:
*!   dash <plot_spec> [if] [in] [, <opts>]   — immediate single-graph render
*!       or                                   — named graph (accumulate for build)
*!   dash kpi <stat>(varname) [if] [in] [, <opts>]
*!   dash build [, <build_opts>]
*!   dash clear
*!   dash serve [, <serve_opts>]
*!
*! Architecture (v2.0):
*!   - Every option is parsed by Stata's -syntax-.  twoway's options are
*!     declared with twoway's own minimum abbreviations, so -syntax-
*!     resolves a prefix as twoway does; nothing rewrites an option word
*!     before it.
*!   - dash_parse.mata reads, by value, what must not be parsed as Stata
*!     code -- the command line split into plot segments, user text, the
*!     immediate values of scatteri, pci and pcarrowi, qualifiers and
*!     filter() groups -- and checks what -syntax- cannot, among them the
*!     plot type, UTF-8, layout(), link(), a KPI's percentile and a
*!     saving() path.  Its header lists every function dash.ado calls.
*!   - The spec is JSON assembled in Stata by string concatenation, every
*!     text in it escaped in Mata (_dash_json_str, _json_escape); the
*!     immediate values' records are written by dash_parse.mata.
*!
*! Author:  (see dash.sthlp)
*! Version: 0.1.0  30sep2026

// ================================================================
// Load Mata library (dash_parse.mata)
// ================================================================
// dash_parse.mata must be on the ado-path alongside dash.ado.
// findfile locates it; capture run compiles its Mata functions.
// capture is used because run of a .mata file returns rc=3000
// (Mata compilation marker) — that is normal and not an error.
// r(fn) is saved to a local immediately to survive any r() clearing.
// This top-level code executes once when dash.ado is first loaded.
// ================================================================
// Load Mata library (dash_parse.mata)
// ================================================================
// Strategy 1: use findfile to search the ado-path (works when the
//   current directory or the package's PLUS/d/ directory is on the path).
// Strategy 2: locate dash.ado via findfile to derive the package directory.
// capture run handles the Mata compilation rc=3000 without aborting.
capture findfile dash_parse.mata
if _rc == 0 {
    local _dash_matalib "`r(fn)'"
}
else {
    // Derive path from dash.ado's own location
    capture findfile dash.ado
    if _rc == 0 {
        local _dash_ado_fn "`r(fn)'"
        local _dash_matalib = substr("`_dash_ado_fn'", 1, ///
            strlen("`_dash_ado_fn'") - strlen("dash.ado")) + "dash_parse.mata"
        capture confirm file "`_dash_matalib'"
        if _rc != 0 local _dash_matalib ""
    }
}
// dash's Mata library.  The return code of `run' is DELIBERATELY not used
// as a verdict.  Measured:
//
//     state                       run rc    functions present
//     healthy, first load              0                  yes
//     healthy, loaded a second time 3000                  yes
//     nothing compiles              3000                   no
//     one unrelated function broken  199                  yes
//     file not found           (not run)          not by this
//
// A second load returns the SAME code as a total compile failure, so
// refusing to run on a non-zero rc would break every user -- and every
// certification script -- that loads dash_parse.mata itself before dash.ado.
// ROADMAP TR-07.4 asks for exactly that; it would be a regression.
//
// What is authoritative is whether the functions dash calls are there, and
// _dash_require_mata asks that at the entry to every command.  It is also
// the only check that sees a library cleared mid-session.
if `"`_dash_matalib'"' != "" {
    capture run "`_dash_matalib'"
}

program define dash
    version 16.0

    // Every subcommand parses through Mata, so this is the one place that
    // covers all of them.  Without it a broken or missing dash_parse.mata
    // surfaced as "<istmt>: 3499 _dash_check_utf8() not found", naming an
    // internal function and giving the user nothing to act on -- or, for a
    // partial compile, as rc 0 and "graph registered".
    _dash_require_mata

    // ----------------------------------------------------------------
    // Subcommand routing
    // ----------------------------------------------------------------
    // Extract the subcommand name: everything up to the first space or
    // comma.  This handles both "dash kpi ..." and "dash build, ..."
    // (where the comma immediately follows the subcommand name).
    //
    // Read by value, in Mata.  The command was put inside compound quotes
    // in regexm() and substr(), and a text holding "' -- title("'90s
    // cars"), a qualifier's literal "' or 1 or '" -- ended those quotes
    // early: `dash kpi mean(price), title("'90s price")' stopped here with
    // r(100) ") required", and nothing was registered (measured 24sep2026).
    //
    // The rest of the command is forwarded as a command line, through
    // macval().  A command line built from a macro is expanded again, so
    // text Stata had already expanded once, where the user typed it, was
    // expanded a second time: a title typed Cost in \$US was stored with the
    // global's value, and an =exp typed \`=...' to reach dash as written was
    // evaluated -- \`=filewrite(...)' wrote its file (measured 24sep2026;
    // test_json_escaping.cscript JSE-65..69 for a plot).  macval() hands
    // the text on as the subcommand's `0', as written.
    mata: st_local("_subcmd", ustrregexm(st_local("0"),                   ///
        "^[a-zA-Z][a-zA-Z0-9_]*") ? ustrregexs(0) : "")
    mata: st_local("_args", substr(st_local("0"),                         ///
        strlen(st_local("_subcmd")) + 1, .))

    if "`_subcmd'" == "kpi" {
        _dash_kpi `macval(_args)'
        exit
    }
    if "`_subcmd'" == "build" {
        _dash_build `macval(_args)'
        exit
    }
    if "`_subcmd'" == "clear" {
        _dash_clear
        exit
    }
    if "`_subcmd'" == "serve" {
        _dash_serve `macval(_args)'
        exit
    }

    // ----------------------------------------------------------------
    // Plot definition  (pass full args including plot-type word)
    // ----------------------------------------------------------------
    _dash_plot `macval(0)'
end


// ================================================================
// _dash_do_render  — invoke the Python renderer (private helper)
//
// In Stata, python:...end ALWAYS terminates the enclosing program
// define block.  Any Stata code written after a python:...end inside
// a program define is executed at file-load time rather than as part
// of the program, and the subsequent end token is then unrecognised
// (r(199)).
//
// The fix: isolate the python: block in this dedicated helper so that
// post-render Stata code (browser open, display messages) can live
// in the CALLER program after calling _dash_do_render.
//
// Syntax:
//   _dash_do_render, SPEC(path) DATA(path) OUTPUT(path)           ///
//                    RENDERPY(path) [MODE(string)]
//
// mode defaults to "standalone" if omitted.
// ================================================================
// ================================================================
// _dash_python_ok  — is Python configured?
// ================================================================
// A pure function of its argument, so the failing state can be reached from
// a certification script.  `c()' is read-only and `set python_exec' refuses
// a path that does not exist -- measured, r(601) -- so a machine that HAS
// Python cannot be made to look like one that has not, except by asking the
// question this way.
//
// The probe is `c(python_exec)', which is CONFIGURATION rather than
// execution.  `capture python query' and `capture python: pass' both run
// Python, and the certification suite already learned what that costs:
// measured, the first python call of a session returns a nonzero rc under
// the runner on a machine where dash renders Bokeh output seconds later, so
// nine scripts skipped and the runner printed ALL TESTS PASSED.
// test_cscript_hygiene.py has enforced the rule for .cscript files since;
// it now covers dash.ado and dash_setup.ado too.
//
// Syntax:
//   _dash_python_ok "<value of c(python_exec)>"   -> r(ok) 0 or 1
// ================================================================
program define _dash_python_ok, rclass
    version 16.0
    args probe
    local probe = strtrim(`"`probe'"')
    return scalar ok = cond(`"`probe'"' == "", 0, 1)
end


// ================================================================
// _dash_require_python  — refuse to start rather than fail inside Python
// ================================================================
// _dash_do_render and _dash_serve go straight to `python:'.  Without this a
// user with no linked Python got a raw Stata Python error naming neither
// dash nor the remedy -- while the jsonio check that stood a few lines away
// gave them a sentence they could act on.  This was modelled on that
// message.
// ================================================================
program define _dash_require_python
    version 16.0
    _dash_python_ok `"`c(python_exec)'"'
    if r(ok) != 1 {
        display as error "dash: Python is required but is not available to Stata."
        display as error "      Run {cmd:dash_setup} first, or link Stata to " ///
            "Python 3.13+: {help python}"
        exit 198
    }
end


// ================================================================
// _dash_require_mata  — refuse to start rather than fail on a missing function
// ================================================================
// `mata describe' of every function dash.ado calls is the witness, for a
// library never loaded, since cleared, or loaded only in part.  The return
// code of `run' is not (see the table at the top of this file): it is 3000
// for a healthy reload and for a total failure alike.  (This header said a
// "recorded load error" witnessed a partial compile; nothing records one,
// and the one-function check that followed passed a partial library --
// WP-24, test_env_guards.cscript ENV-23, test_mata_library_guard.cscript.)
// ================================================================
program define _dash_require_mata
    version 16.0

    // Every Mata function dash.ado calls, named once.  Checking a single
    // one would pass a library that compiled half way.  _dash_path_badchar
    // was missing, so a library without it passed and the first saving()
    // ended in r(3499) naming it (test_program_coverage.cscript PC-30);
    // test_program_coverage_map.py now fails a call this list does not name.
    local _needed _dash_check_utf8 _dash_route_axis2 _dash_comma_pos _dash_expand_plottype ///
        _dash_extract_filters _dash_extract_qual_vars _dash_extract_vars ///
        _dash_filter_refusal _dash_filter_setvars _dash_has_name_opt ///
        _dash_seg_by _dash_is_digits _dash_item_globals _dash_json_get_str _dash_json_str_args ///
        _dash_kpi_pctile _json_escape _dash_path_badchar ///
        _dash_layout_cells _dash_layout_refusal _dash_link_refusal ///
        _dash_option_names _dash_qual_expand _dash_qual_reset ///
        _dash_qual_rewrite _dash_qual_take _dash_qual_export _dash_qual_orders ///
        _dash_immediate _dash_say _dash_spec_types_in _dash_split_segs ///
        _dash_text_args _dash_undrawn_plottype _dash_kernel_full ///
        _dash_unbound_cands _dash_fn_names _dash_fn_space_call _dash_rep_scan ///
        _dash_rep_keyof _dash_rep_reduce _dash_rep_merge_locals ///
        _dash_rep_und_scan _dash_rep_und_cross _dash_log_split _dash_logit_typed ///
        _dash_foreign_scan _dash_kernel_clash _dash_kernel_flag ///
        _dash_computed_cells _dash_graph_touched _dash_qual_cols_in ///
        _dash_axis_pieces

    // Every one of them, not one.  The check asked for _dash_check_utf8
    // alone and took the library for whole when it was there, so a library
    // in memory only in part -- a copy whose compile stopped half way, or a
    // function defined by hand -- passed, and the first command died in
    // Mata with r(3499), "_dash_split_segs() not found" (measured 24sep2026;
    // test_env_guards.cscript ENV-23).  Asking for all of them costs 0.13
    // ms a command (measured, 1000 runs).
    local _missing ""
    foreach f of local _needed {
        quietly capture mata: mata describe `f'()
        if _rc != 0 local _missing `"`_missing' `f'()"'
    }
    if `"`_missing'"' == "" exit

    // Not loaded, or loaded in part.  REPAIR rather than refuse: measured,
    // the library is routinely absent at this point through no fault of the
    // install -- `clear all' drops it, `dash clear' never needed it, and
    // dash.ado's own top-level loader does not always run before the first
    // command when the file is reached through the ado-path.  A guard that
    // simply vetoed here failed test_examples_run.cscript, which runs
    // `clear all' before each of the eleven shipped examples.
    local _src ""
    capture findfile dash_parse.mata
    if _rc == 0 {
        local _src `"`r(fn)'"'
    }
    else {
        capture findfile dash.ado
        if _rc == 0 {
            local _ado `"`r(fn)'"'
            local _beside = substr(`"`_ado'"', 1, ///
                strlen(`"`_ado'"') - strlen("dash.ado")) + "dash_parse.mata"
            capture confirm file `"`_beside'"'
            if _rc == 0 local _src `"`_beside'"'
        }
    }
    if `"`_src'"' != "" {
        // A function already defined stops `run' at its definition, r(3000),
        // so over a library in memory in part the file would define nothing
        // it lacks.  What is there is dropped first -- the library's own
        // names only, which are _dash_* and the four below
        // (test_program_coverage_map.py holds the list to dash_parse.mata),
        // and only when there is a file to load it back from.
        capture mata: mata drop _dash_*()
        foreach f in _expand_plottype_str _first_comma_pos _is_utf8 ///
                _json_escape {
            capture mata: mata drop `f'()
        }
        capture run `"`_src'"'
    }

    // Only now is it a real failure.  Without this the user got
    // "<istmt>: 3499 _dash_check_utf8() not found", naming an internal
    // function, or -- when only part of the library was missing -- rc 0 and
    // "graph registered" for a command that had not run.
    local _missing ""
    foreach f of local _needed {
        quietly capture mata: mata describe `f'()
        if _rc != 0 local _missing `"`_missing' `f'()"'
    }
    if `"`_missing'"' != "" {
        display as error "dash: dash's Mata library could not be loaded."
        display as error "      Missing:`_missing'"
        // Where the file was found, the report says so: it said the library
        // "is not on the ado-path and not beside dash.ado" when it had just
        // been loaded from there (measured 24sep2026; ENV-22).  The path is
        // shown as text, _asis, never as SMCL.
        if `"`_src'"' == "" {
            display as error "      dash_parse.mata is not on the ado-path and " ///
                "not beside dash.ado."
        }
        else {
            display as error "      dash_parse.mata was found but did not load completely."
            display as error "      It is an older or damaged copy, loaded from " _asis `"`_src'"'
        }
        display as error "      Reinstall dash, or run {cmd:dash_setup}."
        exit 198
    }
end


// ================================================================
// _dash_find_render  — locate dash_render.py, once
// ================================================================
// Three programs carried their own copy of this search and the copies
// drifted: each ended with
//
//     local render_py "`c(sysdir_plus)'d/dash_render.py"
//
// which names a path that cannot exist.  Measured from a real `net install'
// into a clean PLUS, Stata files this one by EXTENSION rather than by first
// letter -- PLUS/py/dash_render.py -- while PLUS/d holds dash.ado,
// dash.sthlp, dash_parse.mata and the two dash_setup files and no .py at
// all.  The dash.ado-derived branch assumes the renderer sits beside
// dash.ado and computes the same wrong directory.
//
// Neither is reached on a healthy install: findfile DOES search the
// extension subdirectory, so candidate 1 wins for every installed user
// (measured, rc 0 -> PLUS/py/dash_render.py).  What made them worth
// removing is what happened when they WERE reached -- nothing confirmed the
// file existed, so the path went to `runpy.run_path' and the user got a
// Python FileNotFoundError naming a Stata internal directory, r(7102), and
// no message from dash.  `dash serve' announced "starting Bokeh Server ...
// Stata is blocked until the server stops" first and died after.
//
// Only the two candidates that can succeed are kept.  A candidate under
// $PLUS/py or $PERSONAL/py was considered and rejected: dash executes
// whatever this returns, `confirm file' is an existence check rather than a
// trust check, and those are trees the shipping code never ran from.
//
// Syntax:
//   _dash_find_render
//   -> r(fn), or rc 601 with a message naming what to do.
// ================================================================
program define _dash_find_render, rclass
    version 16.0

    capture findfile dash_render.py
    if _rc == 0 {
        return local fn `"`r(fn)'"'
        exit
    }

    // Beside dash.ado: the development layout, and any install that keeps
    // the package together.  Confirmed before it is returned, because the
    // caller hands it straight to Python.
    capture findfile dash.ado
    if _rc == 0 {
        local _ado_fn `"`r(fn)'"'
        local _beside = substr(`"`_ado_fn'"', 1, ///
            strlen(`"`_ado_fn'"') - strlen("dash.ado")) + "dash_render.py"
        capture confirm file `"`_beside'"'
        if _rc == 0 {
            return local fn `"`_beside'"'
            exit
        }
    }

    display as error "dash: cannot locate dash_render.py."
    display as error "      Not on the ado-path and not beside dash.ado."
    display as error "      Reinstall dash, or put its directory on the ado-path."
    exit 601
end


program define _dash_do_render
    version 16.0
    syntax, SPEC(string) DATA(string) OUTPUT(string) RENDERPY(string) ///
            [MODE(string)]

    // The directory the page or the app goes in must exist: refused here,
    // before Python, on every route, with twoway's r(603) (JSE-52).
    _dash_saving_dir `"`output'"'

    // Before `python:', not after: a user with no linked Python used to get
    // a raw Stata Python error naming neither dash nor the remedy.
    _dash_require_python

    if `"`mode'"' == "" local mode "standalone"

    // Escape each path so double-quotes and backslashes in user-supplied paths
    // cannot break the Python string literal or inject code.  _dash_json_str
    // replaces \ with \\ and " with \", which makes the values safe for
    // regular double-quoted Python string literals.
    _dash_json_str `"`spec'"'     _py_spec
    _dash_json_str `"`data'"'     _py_data
    _dash_json_str `"`output'"'   _py_output
    _dash_json_str `"`mode'"'     _py_mode
    _dash_json_str `"`renderpy'"' _py_renderpy

    // Single-line python: calls are used here instead of a python:...end block.
    // Reason: python:...end blocks inside program defines trigger an
    // IndentationError when the ado file is loaded from the adopath (Stata
    // prepends indentation to the stored block on ado-path loads).
    // Single-line python: statements do not have this issue.
    python: import sys, runpy
    python: sys.argv = ["dash_render.py", "--spec", "`_py_spec'", "--data", "`_py_data'", "--output", "`_py_output'", "--mode", "`_py_mode'"]
    // Assign the result.  A single-line `python:' ECHOES the value of the
    // expression it evaluates, and run_path returns the executed module's
    // globals dict -- so this line printed the whole of dash_render.py's
    // namespace into the Stata log on EVERY render.  Measured:
    // `dash scatter mpg weight, saving(x.html)' produced a 48 KB, 653-line
    // log, of which the dump began at line 91.  Contrary to project rule 14,
    // and it buries any message dash actually displays.
    python: _dash_render_ns = runpy.run_path("`_py_renderpy'", run_name="__main__")
end


// ================================================================
// _dash_validate_path  — check saving() path is safe
// ================================================================
program define _dash_validate_path
    version 16.0
    args fpath ext

    // The expected extension, so the server branch can share every other
    // check.  It used to hardcode .html, so server mode skipped the
    // validator entirely and tested only the suffix -- a .py saving() path
    // therefore got no traversal check, no shell-metacharacter check and no
    // quote check at all.
    if "`ext'" == "" local ext "html"

    // FIRST, before anything expands the path inside an expression.
    // Every check below reads `fpath' inside quotes, and a path containing
    // a double quote died in the first of them with
    //     too few quotes
    //     r(132)
    // so the strpos+char() check at the end -- the one written specifically
    // to catch that character -- never ran.  It failed closed, but the user
    // saw a quoting error rather than the diagnostic this program exists to
    // give.  _dash_path_badchar() reads the macro through st_local(), where
    // its contents are a value and cannot be parsed as code.
    mata: st_local("_pv_bad", strofreal(_dash_path_badchar(st_local("fpath"))))
    if `_pv_bad' != 0 {
        display as error "dash: saving() path contains disallowed characters (shell metacharacters not permitted)."
        exit(198)
    }

    // `~' is not expanded by Stata, and an unexpanded one reached Python and
    // ended in r(7102) -- measured on saving("~/dashtilde.html").  Expanding
    // it is friendlier than rejecting it and is what every other tool does.
    // Only a leading `~/' is expanded: `~user/' would need a password-file
    // lookup dash has no business doing, and a `~' anywhere else in a path
    // is an ordinary character.
    // The caller reads the result back from `_dash_vpath', which this
    // program always sets.  It cannot write through the argument: the
    // arguments are VALUES, not macro names.
    if substr(`"`fpath'"', 1, 2) == "~/" {
        local _home : environment HOME
        if `"`_home'"' == "" {
            display as error "dash: saving() path starts with '~' but HOME is not set; give a full path."
            exit(198)
        }
        local fpath `"`_home'/`=substr(`"`fpath'"', 3, .)'"'
    }

    // Path traversal is a `..' SEGMENT, not the two characters appearing
    // anywhere.  The old rule was `regexm("\.\.")', which rejected the
    // perfectly ordinary my..report.html -- measured, r(198) -- while
    // catching nothing the segment rule does not.
    if regexm(`"`fpath'"', "(^|[/\\])\.\.($|[/\\])") {
        display as error "dash: saving() path may not contain a '..' path segment (path traversal not allowed)."
        exit(198)
    }

    // A leading `-' on the file name makes the shell read the path as a
    // flag: `open -e.html' opens the argument in TextEdit rather than
    // treating it as a file.  Measured, saving("-e.html") was accepted.
    local _base `"`fpath'"'
    if regexm(`"`_base'"', "([^/\\]+)$") local _base = regexs(1)
    // The path is echoed through _dash_say, so a brace in it -- legal in a
    // file name -- is shown as written, not drawn as SMCL (P20-08).
    if substr(`"`_base'"', 1, 1) == "-" {
        display as error "dash: saving() file name may not start with '-'; the shell would read it as an option."
        mata: _dash_say("err", "      Write ./", st_local("_base"), " if that is really the name you want.")
        exit(198)
    }
    if !regexm(lower("`fpath'"), "\.`ext'$") {
        mata: _dash_say("err", "dash: saving() path must end in .`ext' (got: ", st_local("fpath"), ")")
        exit(198)
    }
    // Reject shell metacharacters to prevent command injection via shell open/start/xdg-open.
    // Printable metacharacters checked via regexm character class.
    // Chars that Stata would misinterpret during macro expansion (backtick=96, dollar=36)
    // and control characters (tab=9, newline=10, CR=13) checked via strpos+char() to
    // avoid the "too few quotes" crash that occurs when a compound-quoted macro value
    // contains a backtick.
    // Parentheses are NOT rejected: the one shell call site, _dash_open_page,
    // quotes the path (in single quotes on a Mac and Unix, double on
    // Windows), inside which ( and ) are literal, and rejecting them broke
    // every Windows path under "Program Files (x86)".
    // The characters that genuinely matter inside double quotes are handled
    // below; the rest are kept as defence in depth since paths rarely contain
    // them.
    if regexm("`fpath'", `"[;&|<>]"') {
        display as error "dash: saving() path contains disallowed characters (shell metacharacters not permitted)."
        exit(198)
    }
    // 34 = double quote, which would terminate the quoted argument at the
    // shell call site; it was previously not checked at all.
    foreach _cnum of numlist 96 36 34 9 10 13 {
        if strpos("`fpath'", char(`_cnum')) > 0 {
            display as error "dash: saving() path contains disallowed characters (shell metacharacters not permitted)."
            exit(198)
        }
    }

    // Always set, so a caller can use it unconditionally.  It differs from
    // what was passed in only when a leading `~/' was expanded.
    c_local _dash_vpath `"`fpath'"'
end


// ================================================================
// _dash_saving_dir  -- the directory a saving() path writes into exists
// ================================================================
// dash creates no directory, and twoway creates none either: twoway
// scatter ..., saving("/nonexistent/x.gph") is r(603), "file
// /nonexistent/x.gph could not be opened".  dash handed such a path to the
// renderer, which died in Python, r(7102) FileNotFoundError, on dash
// build, dash build, server and the one-line form alike --
// saving('/abs/path/x.html) among them, whose directory is '/abs/path --
// and dash build without replace said the file "already exists" (measured
// 24sep2026; test_json_escaping.cscript JSE-52).  Refused before anything
// is rendered, with twoway's code, naming the directory.
//
// Apart from _dash_validate_path, which judges a path's text alone and is
// certified on paths of other machines (test_path_validation.cscript
// PV-07's C:/Program Files (x86)/out.html).  dash build calls this before
// it looks for the file; _dash_do_render, which every route that writes a
// page or an app passes before Python, calls it for the one-line form.
//
// The directory is the path up to its last separator: / everywhere, and \
// on Windows as well -- elsewhere a \ is a character of a file name
// (JSE-09 writes js_a\b.html).  A path with no separator is written in the
// working directory.  Read in Mata, by value, and shown as written.
//
// Usage:  _dash_saving_dir `"<path _dash_validate_path has passed>"'
// ================================================================
program define _dash_saving_dir
    version 16.0
    args fpath

    mata: st_local("_sd_dir", ustrregexm(st_local("fpath"), ///
        c("os") == "Windows" ? "^.*[/\\]" : "^.*/") ? ustrregexs(0) : "")
    local _sd_len : length local _sd_dir
    if `_sd_len' == 0 exit
    mata: st_local("_sd_ok", strofreal(direxists(st_local("_sd_dir"))))
    if `_sd_ok' exit
    // Named without its trailing separator.
    mata: st_local("_sd_dir", substr(st_local("_sd_dir"), 1, ///
        strlen(st_local("_sd_dir")) - 1))
    mata: _dash_say("err", "dash: file ", st_local("fpath"), " could not be opened:")
    mata: _dash_say("err", "      the directory ", st_local("_sd_dir"), ///
        " does not exist.  Create it first, or save in a directory that exists.")
    exit 603
end


// ================================================================
// _dash_saving_clobber  -- saving() names a file that is there already
// ================================================================
// Without replace an existing file is refused, "<cmd>: file '...' already
// exists. Use replace option to overwrite.", r(198): dash build's message
// and code.  The one-line form had no such check and wrote its page over
// whatever saving() named, rc 0, and took no replace (measured 24sep2026 by
// WP-24; twoway refuses, r(602)).  A directory in the file's place is never
// written: without replace it is a file that exists, as twoway and dash
// build say, and with replace it is refused as twoway refuses it,
// "is read-only; cannot be modified or erased", r(608) -- dash build handed
// it to Python and died there, r(7102) IsADirectoryError.  A symbolic link
// is the file it points to.  The path is read in Mata, by value, and shown
// as written.  Called after _dash_validate_path and _dash_saving_dir.
//
// Usage:  _dash_saving_clobber `"<path>"' "<replace or empty>" "<cmd name>"
// ================================================================
program define _dash_saving_clobber
    version 16.0
    args fpath replace cmdname

    mata: st_local("_sc_dir", strofreal(direxists(st_local("fpath"))))
    mata: st_local("_sc_file", strofreal(fileexists(st_local("fpath"))))
    if "`replace'" == "" {
        if `_sc_dir' | `_sc_file' {
            mata: _dash_say("err", "`cmdname': file '", st_local("fpath"), "' already exists. Use replace option to overwrite.")
            exit 198
        }
        exit
    }
    if `_sc_dir' {
        mata: _dash_say("err", "`cmdname': file ", st_local("fpath"), " is a directory; it cannot be modified or erased")
        exit 608
    }
end


// ================================================================
// _dash_json_str  -- JSON string escaping, the text read by value in Mata
// Usage:  _dash_json_str `"`raw'"' _escaped
// After: local _escaped contains the JSON-safe string (no surrounding quotes)
// ================================================================
program define _dash_json_str
    version 16.0

    // JSON forbids EVERY unescaped byte below 0x20 inside a string, not just
    // the three that have short forms.  This escaped backslash, quote, TAB,
    // LF and CR and left the other twenty-seven raw, so
    //     dash build, title("bad" + char(1) + "title")
    // produced invalid JSON and ended in a Python JSONDecodeError with
    // r(7102) -- measured, on both the build and the immediate route.
    //
    // Escaping rather than rejecting is deliberate: the user story asks for
    // "either a clean dash error or a correct dashboard", and a correct
    // dashboard is the better of the two.  A stray control character pasted
    // in from a web page now survives into the title intact.
    //
    // The text is read and escaped in Mata, by value (_dash_json_str_args in
    // dash_parse.mata).  It was read with -args- and escaped by subinstr()
    // calls in compound quotes, and a text holding "' -- a compound-quoted
    // title(), note() or legend label, a compound-quoted literal in a
    // qualifier -- ended those quotes early: it came back empty or cut, with
    // rc 0 (measured 23sep2026 at ad13a0f: title(`"A "B" C"') stored
    // "title":"").  The result holds no backtick, dollar sign or
    // apostrophe -- each is written as its JSON escape, backslash u 0060,
    // 0024 and 0027 -- so every spec line can expand it inside compound
    // quotes.
    mata: _dash_json_str_args()
    c_local `_dash_jsn' `"`_dash_jsv'"'
end


// ================================================================
// _dash_parse_graph_opts
//
// Parse a raw graph-level options string using Stata's syntax command.
// Called as: _dash_parse_graph_opts [, opts...]
//            (i.e. pass the raw options string preceded by a comma)
//
// After the call all parsed values are in s() macros.
// ================================================================
program define _dash_parse_graph_opts, sclass
    version 16.0
    // Accept all standard graph-level options.
    // NOTE: this list and _dash_parse_plot_opts's were first written by
    // scripts/regen_option_surface.py from test/fixtures/abbrev_truth.json,
    // and have been edited by hand since.  The script no longer reproduces
    // them: run over dash.ado (measured 23sep2026, on a copy) it drops the
    // 33 declarations it never knew -- hover(), the WP-22 options, the
    // aliases -- and prepends its note again, which is how that note came
    // to stand here twice.  Do not run it; edit by hand, and
    // keep in step the other places the list appears: the plot parser's
    // syntax, the sreturn blocks, _dash_plot_opts_to_json's key list and
    // the graph-level loops in _dash_process_segment and _dash_plot.
    // Capitalised letters are the minimum abbreviation: as a rule twoway's
    // own where twoway has the option (measured, abbrev_truth.json) --
    // NAMe, ASPectratio and JITter are shorter, kept from dash's old table,
    // and MEan and BWIDth longer -- and dash's own choice where it has not.
    // -syntax- ends the run of capitals at a digit, so T1title's minimum is
    // t, and YTITLE2's is ytitle -- which YTitle, declared first, takes.
    // The trailing * is Stata's own catch-all: any option not declared
    // above is collected into `options' instead of aborting the user's
    // do-file.  dash.sthlp has always claimed copy-pasted twoway commands
    // still run; without this they did not.  Unmatched options are
    // reported by name, once per command -- never silently dropped.
    // Every text option is string asis, as title() is, so the quotes the
    // user typed reach the spec and the renderer reads the text as twoway's
    // textbox does.  xtitle(), ytitle(), xtitle2(), ytitle2() (and xti2(),
    // yti2()) and t1title() .. r2title() were declared string, and Stata
    // stripped the quotes before the spec was written: ytitle("line 1"
    // "line 2") was stored, and drawn, as one line where twoway draws two,
    // and xtitle(`"a "b" c"') lost the quotes around b (measured 24sep2026;
    // test_json_escaping.cscript JSE-46).
    syntax [, ///
        TItle(string asis)        SUBtitle(string asis)     NOTE(string asis) ///
        CAPtion(string asis)      NAMe(string)              SAVing(string) ///
        XTitle(string asis)       YTitle(string asis)       XLabel(string asis) ///
        YLabel(string asis)       XLIne(string asis)        YLIne(string asis) ///
        LEGend(string asis)       BY(string asis)           XSCale(string asis) ///
        YSCale(string asis)       ASPectratio(string)       SCHeme(string) ///
        PLOTRegion(string asis)   GRAPHRegion(string asis)  BGColor(string) ///
        PLOTBGCOLOR(string)       LINK(string)              FILTer(string asis) ///
        YTITLE2(string asis)      XTITLE2(string asis)      YLABEL2(string asis) ///
        XLABEL2(string asis)      YSCALE2(string asis)      XSCALE2(string asis) ///
        XSIZe(string)             YSIZe(string)             FXSIZE(string) ///
        FYSIZE(string)            SCALE(string)             TEXT(string asis) ///
        HOVer(string)             ///
        XTICk(string asis)        YTICk(string asis)        XMTick(string asis) ///
        YMTick(string asis)       XMLabel(string asis)      YMLabel(string asis) ///
        T1title(string asis)      T2title(string asis)      B1title(string asis) ///
        B2title(string asis)      L1title(string asis)      L2title(string asis) ///
        R1title(string asis)      R2title(string asis)      TITLE2(string) ///
        SUBTITLE2(string)         NODRAW                    PLAY(string) ///
        XOVERHANGs                YOVERHANGs                REPLACE ///
        PBGC(string)              XLA2(string asis)         XSC2(string asis) ///
        XTI2(string asis)         YLA2(string asis)         YSC2(string asis) ///
        YTI2(string asis) ///
        ZLABel(string asis)       ZTItle(string asis)       ZSCale(string asis) ///
        * ///
    ]

    // t(), b(), l() and r() are twoway's abbreviations of t1title(),
    // b1title(), l1title() and r1title(), and T1title() .. R1title() take
    // them as they stand: a digit ends -syntax-'s run of capitals, so
    // T1title's minimum is t (measured 23sep2026; test_abbreviations.py,
    // _syntax_options).  They were once declared again here as T() B() L()
    // R() and folded in, on the belief that the minimum was t1.  Declared
    // after T1title() .. R2title(), which admit t() first, those were
    // reached only by a third t() written after t1title() and t2title(),
    // and the fold then dropped it unnamed.  That t() now reaches the note,
    // as it always did in _dash_parse_plot_opts (WP-23 TR-23.6).
    // Fold alias forms onto their real option locals.  These are
    // ALIASES, not prefixes, so Stata's truncation-based abbreviation
    // cannot express them; they are declared above and merged here.
    // twoway accepts none of them, so this is a superset and cannot
    // break drop-in parity, but it keeps existing dash do-files working.
    if `: length local pbgc' & !`: length local plotbgcolor' local plotbgcolor : copy local pbgc
    if `: length local xla2' & !`: length local xlabel2' local xlabel2 : copy local xla2
    if `: length local xsc2' & !`: length local xscale2' local xscale2 : copy local xsc2
    if `: length local xti2' & !`: length local xtitle2' local xtitle2 : copy local xti2
    if `: length local yla2' & !`: length local ylabel2' local ylabel2 : copy local yla2
    if `: length local ysc2' & !`: length local yscale2' local yscale2 : copy local ysc2
    if `: length local yti2' & !`: length local ytitle2' local ytitle2 : copy local yti2

    // Options dash accepts but does not yet honour.  Each supplied one
    // is recorded by name so it is reported rather than silently
    // dropped while the owning section is outstanding.
    //
    // This list went stale once.  Later sections implemented bin(),
    // level(), kernel(), width(), start(), n(), fraction/percent/
    // frequency, falpha(), mlcolor(), mlwidth() and -- at graph level --
    // scheme(), xsize(), ysize(), xtick() and ytick(), and nothing took
    // them off it.  So
    //     . dash scatter mpg weight, level(90)
    //     dash: ignoring unsupported option(s): level()
    // while the interval was in fact computed at 90.  A note that names
    // the wrong options is worse than no note: it tells the user to stop
    // using something that works.
    //
    // test_unsupported_report_is_true.py reads this block and renders
    // every option it names with two different values, asserting the
    // output does not change.  Implement one and forget to remove it
    // here, and that test fails.
    local _dash_pending ""
    if `: length local b1title' local _dash_pending `"`_dash_pending' b1title"'
    if `: length local b2title' local _dash_pending `"`_dash_pending' b2title"'
    // link() and filter() belong to `dash build' and `dash serve', where
    // the link group and the filter widgets are made.  Written on a graph
    // they were stored in graph_options and read by nothing -- measured
    // 22sep2026: name(g1) link(g1) registered, built one source, said
    // nothing.  Named here, so nothing is dropped in silence.
    if `: length local filter' local _dash_pending `"`_dash_pending' filter"'
    if `: length local fxsize' local _dash_pending `"`_dash_pending' fxsize"'
    if `: length local fysize' local _dash_pending `"`_dash_pending' fysize"'
    if `: length local l1title' local _dash_pending `"`_dash_pending' l1title"'
    if `: length local l2title' local _dash_pending `"`_dash_pending' l2title"'
    if `: length local link' local _dash_pending `"`_dash_pending' link"'
    if `: length local play' local _dash_pending `"`_dash_pending' play"'
    if `: length local r1title' local _dash_pending `"`_dash_pending' r1title"'
    if `: length local r2title' local _dash_pending `"`_dash_pending' r2title"'
    if `: length local scale' local _dash_pending `"`_dash_pending' scale"'
    if `: length local subtitle2' local _dash_pending `"`_dash_pending' subtitle2"'
    if `: length local t1title' local _dash_pending `"`_dash_pending' t1title"'
    if `: length local t2title' local _dash_pending `"`_dash_pending' t2title"'
    if `: length local text' local _dash_pending `"`_dash_pending' text"'
    if `: length local title2' local _dash_pending `"`_dash_pending' title2"'
    if `: length local xmlabel' local _dash_pending `"`_dash_pending' xmlabel"'
    if `: length local xmtick' local _dash_pending `"`_dash_pending' xmtick"'
    // WP-22: twoway's advanced xoverhangs and yoverhangs, after the comma.
    if `: length local xoverhangs' local _dash_pending `"`_dash_pending' xoverhangs"'
    if `: length local ymlabel' local _dash_pending `"`_dash_pending' ymlabel"'
    if `: length local ymtick' local _dash_pending `"`_dash_pending' ymtick"'
    if `: length local yoverhangs' local _dash_pending `"`_dash_pending' yoverhangs"'
    // Whatever Stata could not match at all, via the trailing *.
    local _dash_unknown : copy local options

    sreturn local title        : copy local title
    sreturn local subtitle     : copy local subtitle
    sreturn local note         : copy local note
    sreturn local caption      : copy local caption
    sreturn local name         : copy local name
    sreturn local saving       : copy local saving
    sreturn local xtitle       : copy local xtitle
    sreturn local ytitle       : copy local ytitle
    sreturn local xlabel       : copy local xlabel
    sreturn local ylabel       : copy local ylabel
    sreturn local xline        : copy local xline
    sreturn local yline        : copy local yline
    sreturn local legend       : copy local legend
    sreturn local by           : copy local by
    sreturn local xscale       : copy local xscale
    sreturn local yscale       : copy local yscale
    sreturn local aspectratio  : copy local aspectratio
    sreturn local scheme       : copy local scheme
    sreturn local plotregion   : copy local plotregion
    sreturn local graphregion  : copy local graphregion
    sreturn local bgcolor      : copy local bgcolor
    sreturn local plotbgcolor  : copy local plotbgcolor
    sreturn local link         : copy local link
    sreturn local filter       : copy local filter
    sreturn local ytitle2      : copy local ytitle2
    sreturn local xtitle2      : copy local xtitle2
    sreturn local ylabel2      : copy local ylabel2
    sreturn local xlabel2      : copy local xlabel2
    sreturn local yscale2      : copy local yscale2
    sreturn local xscale2      : copy local xscale2
    sreturn local xsize        : copy local xsize
    sreturn local ysize        : copy local ysize
    sreturn local fxsize       : copy local fxsize
    sreturn local fysize       : copy local fysize
    sreturn local scale        : copy local scale
    sreturn local hover        : copy local hover
    sreturn local text         : copy local text
    sreturn local xtick        : copy local xtick
    sreturn local ytick        : copy local ytick
    sreturn local xmtick       : copy local xmtick
    sreturn local ymtick       : copy local ymtick
    sreturn local xmlabel      : copy local xmlabel
    sreturn local ymlabel      : copy local ymlabel
    sreturn local t1title      : copy local t1title
    sreturn local t2title      : copy local t2title
    sreturn local b1title      : copy local b1title
    sreturn local b2title      : copy local b2title
    sreturn local l1title      : copy local l1title
    sreturn local l2title      : copy local l2title
    sreturn local r1title      : copy local r1title
    sreturn local r2title      : copy local r2title
    sreturn local title2       : copy local title2
    sreturn local subtitle2    : copy local subtitle2
    sreturn local zlabel       : copy local zlabel
    sreturn local ztitle       : copy local ztitle
    sreturn local zscale       : copy local zscale
    sreturn local nodraw       : copy local nodraw
    sreturn local play         : copy local play
    sreturn local replace      : copy local replace
    sreturn local _pending  : copy local _dash_pending
    sreturn local _unknown  : copy local _dash_unknown
end


// ================================================================
// _dash_parse_plot_opts
//
// Parse plot-level (and possibly mixed graph-level) options.
// Called as: _dash_parse_plot_opts [, expanded_opts...]
//
// All option keys have already been expanded from abbreviations by
//
// After the call all parsed values are in s() macros.
// ================================================================
program define _dash_parse_plot_opts, sclass
    version 16.0
    // NOTE: edited by hand, like _dash_parse_graph_opts's list; the NOTE
    // there says why scripts/regen_option_surface.py must not be run over
    // it, and how the capitalised minimums are chosen.
    // The trailing * is Stata's own catch-all: any option not declared
    // above is collected into `options' instead of aborting the user's
    // do-file.  dash.sthlp has always claimed copy-pasted twoway commands
    // still run; without this they did not.  Unmatched options are
    // reported by name, once per command -- never silently dropped.
    // WP-22 TR-22.3 declared the twoway options GAPS.md F3 found in the
    // note as UNKNOWN, with twoway's own minimum abbreviations: CLColor,
    // CLPattern, CLWidth, MLABANGle, MLABFormat, MLABTextstyle and
    // MLABVposition are twoway_yxview_parse.class's declarations, and
    // SORT SORT1() is the pair -syntax- (and that class file) uses for an
    // option written bare, sort, or with an argument, sort(varlist).
    // XOVERHANGs and YOVERHANGs are advanced_options.sthlp's xoverhangs and
    // yoverhangs; twoway's measured minimum is xoverhang and yoverhang.
    // The text options are string asis, as in _dash_parse_graph_opts (see
    // the note there on xtitle(), ytitle() and t1title() .. r2title()).
    // log and nolog are twoway's graph option logging, on lowess too, where
    // -syntax- would bind them to LOgit: taken out here, by value, and
    // handed to the catch-all as typed below (_dash_log_split).  dash read
    // lowess mpg weight, log as logit, a different curve, and refused
    // scatter mpg weight, log, where twoway draws both as if log were not
    // there (BUGS.md, S1).
    mata: _dash_log_split("0", "_dash_logw")
    syntax [, ///
        MColor(string)            Msymbol(string)           MSIze(string) ///
        MSAngle(string)           MFColor(string)           MLColor(string) ///
        MLabel(string)            MLABColor(string)         MLABSize(string) ///
        MLABPosition(string)      MLABGap(string)           MLABWidth(string) ///
        MALpha(string)            MARKER(string)            LColor(string) ///
        LWidth(string)            LPattern(string)          LALpha(string) ///
        FColor(string)            FIntensity(string)        FAlpha(string) ///
        AColor(string)            ALColor(string)           ALWidth(string) ///
        ALPattern(string) ///
        BARWidth(string)          BASE(string)              BLColor(string) ///
        BFColor(string)           JITter(string)            JSEed(string) ///
        YAXis(string)             XAXis(string)             COLORVar(string) ///
        COLPALette(string)        COLORDIScrete             COLORUSEPLEGend ///
        COLORNlevels(string)      COLORCUTs(string asis)    COLORMissing(string) ///
        COLORLEVels(string)       COLORVARMINMax ///
        BWIDth(string)            DEGree(string)            PSTYle(string) ///
        CMISSing(string)          RECAST(string)            Connect(string) ///
        BIN(string)               BINS(string)              Width(string) ///
        START(string) ///
        DISCrete                  STDP                      STDF ///
        STDR                      MEan                      NOWeight ///
        Adjust                    LOgit ///
        PERCENT                   FREQuency                 DENsity ///
        FRACtion                  Kernel(string)            N(string) ///
        LEvel(string)             BAnds(string)             AT(string asis) ///
        CIOPTS(string asis)       LINEOPTS(string asis)     FITOPTS(string asis) ///
        COLor(string)             MLWidth(string)           MSTyle(string) ///
        LStyle(string)            MLStyle(string)           MLPattern(string) ///
        BLABEL(string)            HORizontal                VERTical ///
        SORT                      RAnge(string asis)        COLORLIst(string asis) ///
        SORT1(string)             CLColor(string)           CLPattern(string) ///
        CLWidth(string)           MLABANGle(string)         MLABFormat(string) ///
        MLABTextstyle(string)     MLABVposition(string)     XOVERHANGs ///
        YOVERHANGs ///
        JITTERSEED(string)        TItle(string asis)        SUBtitle(string asis) ///
        NOTE(string asis)         CAPtion(string asis)      NAMe(string) ///
        SAVing(string)            XTitle(string asis)       YTitle(string asis) ///
        XLabel(string asis)       YLabel(string asis)       XLIne(string asis) ///
        YLIne(string asis)        LEGend(string asis)       BY(string asis) ///
        XSCale(string asis)       YSCale(string asis)       ASPectratio(string) ///
        SCHeme(string)            PLOTRegion(string asis)   GRAPHRegion(string asis) ///
        BGColor(string)           PLOTBGCOLOR(string)       LINK(string) ///
        FILTer(string asis)       YTITLE2(string asis)      XTITLE2(string asis) ///
        YLABEL2(string asis)      XLABEL2(string asis)      YSCALE2(string asis) ///
        XSCALE2(string asis)      XSIZe(string)             YSIZe(string) ///
        FXSIZE(string)            FYSIZE(string)            SCALE(string) ///
        TEXT(string asis)         XTICk(string asis)        YTICk(string asis) ///
        HOVer(string)             ///
        XMTick(string asis)       YMTick(string asis)       XMLabel(string asis) ///
        YMLabel(string asis)      T1title(string asis)      T2title(string asis) ///
        B1title(string asis)      B2title(string asis)      L1title(string asis) ///
        L2title(string asis)      R1title(string asis)      R2title(string asis) ///
        TITLE2(string)            SUBTITLE2(string)         NODRAW ///
        PLAY(string)              REPLACE ///
        BW(string)               MLG(string)               CV(string) ///
        COLV(string)              PBGC(string)              XLA2(string asis) ///
        XSC2(string asis)         XTI2(string asis)         YLA2(string asis) ///
        YSC2(string asis)         YTI2(string asis) ///
        ZLABel(string asis)       ZTItle(string asis)       ZSCale(string asis) ///
        * ///
    ]
    /* ---- plot-level ---- */

    // t(), b(), l() and r() need no fold: T1title() .. R1title() take them
    // as their own minimum abbreviations (see _dash_parse_graph_opts).
    // bins() is twoway histogram's own name for the bin count --
    // twoway_histogram_parse.class declares BINs(), and bins(5) draws what
    // bin(5) draws (measured 23sep2026) -- where dash declared only bin().
    // b() is not a third spelling of it: twoway reads b(5) as b1title(5),
    // on histogram as everywhere else (measured: the default eight bars,
    // under a bottom title "5"), and so does dash.
    if `: length local bins' & !`: length local bin' local bin : copy local bins

    // kernel(gau) is twoway's kernel(gaussian): each name is taken down to
    // twoway's minimum abbreviation (_dash_kernel_full, measured on lpoly,
    // lpolyci and kdensity), and written out in full before the enum rule
    // judges it and the renderer reads it.  It was refused, r(198).  Read
    // by value, in Mata.
    if `: length local kernel' {
        mata: st_local("kernel", _dash_kernel_full(st_local("kernel")))
    }

    // level() is no longer checked here: its rule (level=num,0,100,x) lives
    // in _dash_option_rules and runs in _dash_validate_opts, once per segment.

    // bw() is NOT folded here: what it means depends on the plot type,
    // which this parser does not know.  twoway reads bw() as bwidth() on
    // the bandwidth types and rejects it everywhere else; _dash_fold_bw,
    // called by _dash_process_segment once the type is known, resolves
    // it.  It used to become barwidth() on every type, so
    // `dash (lpoly mpg weight, bw(400))' drew the rule-of-thumb bandwidth
    // and said nothing.
    // Fold alias forms onto their real option locals.  These are
    // ALIASES, not prefixes, so Stata's truncation-based abbreviation
    // cannot express them; they are declared above and merged here.
    // twoway accepts none of them, so this is a superset and cannot
    // break drop-in parity, but it keeps existing dash do-files working.
    if `: length local mlg' & !`: length local mlabgap' local mlabgap : copy local mlg
    if `: length local cv' & !`: length local colorvar' local colorvar : copy local cv
    if `: length local colv' & !`: length local colorvar' local colorvar : copy local colv
    if `: length local pbgc' & !`: length local plotbgcolor' local plotbgcolor : copy local pbgc
    if `: length local xla2' & !`: length local xlabel2' local xlabel2 : copy local xla2
    if `: length local xsc2' & !`: length local xscale2' local xscale2 : copy local xsc2
    if `: length local xti2' & !`: length local xtitle2' local xtitle2 : copy local xti2
    if `: length local yla2' & !`: length local ylabel2' local ylabel2 : copy local yla2
    if `: length local ysc2' & !`: length local yscale2' local yscale2 : copy local ysc2
    if `: length local yti2' & !`: length local ytitle2' local ytitle2 : copy local yti2

    // Options dash accepts but does not yet honour.  Each supplied one
    // is recorded by name so it is reported rather than silently
    // dropped while the owning section is outstanding.
    //
    // This list went stale once.  Later sections implemented bin(),
    // level(), kernel(), width(), start(), n(), fraction/percent/
    // frequency, falpha(), mlcolor(), mlwidth() and -- at graph level --
    // scheme(), xsize(), ysize(), xtick() and ytick(), and nothing took
    // them off it.  So
    //     . dash scatter mpg weight, level(90)
    //     dash: ignoring unsupported option(s): level()
    // while the interval was in fact computed at 90.  A note that names
    // the wrong options is worse than no note: it tells the user to stop
    // using something that works.
    //
    // test_unsupported_report_is_true.py reads this block and renders
    // every option it names with two different values, asserting the
    // output does not change.  Implement one and forget to remove it
    // here, and that test fails.
    local _dash_pending ""
    if `: length local at' local _dash_pending `"`_dash_pending' at"'
    if `: length local b1title' local _dash_pending `"`_dash_pending' b1title"'
    if `: length local b2title' local _dash_pending `"`_dash_pending' b2title"'
    if `: length local blabel' local _dash_pending `"`_dash_pending' blabel"'
    if `: length local ciopts' local _dash_pending `"`_dash_pending' ciopts"'
    if `: length local cmissing' local _dash_pending `"`_dash_pending' cmissing"'
    if `: length local colorlist' local _dash_pending `"`_dash_pending' colorlist"'
    if `: length local coloruseplegend' local _dash_pending `"`_dash_pending' coloruseplegend"'
    if `: length local connect' local _dash_pending `"`_dash_pending' connect"'
    // As in the graph-level block: build-time options written on a graph.
    if `: length local filter' local _dash_pending `"`_dash_pending' filter"'
    if `: length local fitopts' local _dash_pending `"`_dash_pending' fitopts"'
    if `: length local fxsize' local _dash_pending `"`_dash_pending' fxsize"'
    if `: length local fysize' local _dash_pending `"`_dash_pending' fysize"'
    if `: length local horizontal' local _dash_pending `"`_dash_pending' horizontal"'
    if `: length local l1title' local _dash_pending `"`_dash_pending' l1title"'
    if `: length local l2title' local _dash_pending `"`_dash_pending' l2title"'
    if `: length local link' local _dash_pending `"`_dash_pending' link"'
    if `: length local lineopts' local _dash_pending `"`_dash_pending' lineopts"'
    if `: length local lstyle' local _dash_pending `"`_dash_pending' lstyle"'
    // WP-22: mlabtextstyle() names a text style in a .scheme file, and
    // mlabvposition() a variable of clock positions, one per observation;
    // dash draws a layer's labels at one position in the scheme's style.
    if `: length local mlabtextstyle' local _dash_pending `"`_dash_pending' mlabtextstyle"'
    if `: length local mlabvposition' local _dash_pending `"`_dash_pending' mlabvposition"'
    if `: length local mlabwidth' local _dash_pending `"`_dash_pending' mlabwidth"'
    if `: length local mlpattern' local _dash_pending `"`_dash_pending' mlpattern"'
    if `: length local mlstyle' local _dash_pending `"`_dash_pending' mlstyle"'
    if `: length local mstyle' local _dash_pending `"`_dash_pending' mstyle"'
    if `: length local play' local _dash_pending `"`_dash_pending' play"'
    if `: length local pstyle' local _dash_pending `"`_dash_pending' pstyle"'
    // fitarea_options, the look of a ci fit's band: twoway takes ac(),
    // alc(), alw() and alp() (measured 24sep2026; al() is alstyle()).
    // Drawn on lfitci, qfitci, lpolyci and fpfitci -- and pstyle() with
    // them -- where _dash_fold_typed takes them off this list once the
    // type is known; twoway accepts them on every type (rc 0), so
    // elsewhere they are named here.
    if `: length local acolor' local _dash_pending `"`_dash_pending' acolor"'
    if `: length local alcolor' local _dash_pending `"`_dash_pending' alcolor"'
    if `: length local alwidth' local _dash_pending `"`_dash_pending' alwidth"'
    if `: length local alpattern' local _dash_pending `"`_dash_pending' alpattern"'
    if `: length local r1title' local _dash_pending `"`_dash_pending' r1title"'
    if `: length local r2title' local _dash_pending `"`_dash_pending' r2title"'
    if `: length local recast' local _dash_pending `"`_dash_pending' recast"'
    if `: length local scale' local _dash_pending `"`_dash_pending' scale"'
    // sort(varlist) is named as sort(): the argument form arrives in
    // `sort1', the name -syntax- gives it, which is Stata's plumbing and not
    // a name the user wrote.  A bare sort is not named here: dash joins the
    // points of the connected types in the order of x, which is what sort
    // asks twoway for, so _dash_fold_typed names it only on the other types,
    // once the type is known.
    if `: length local sort1' local _dash_pending `"`_dash_pending' sort"'
    if `: length local subtitle2' local _dash_pending `"`_dash_pending' subtitle2"'
    if `: length local t1title' local _dash_pending `"`_dash_pending' t1title"'
    if `: length local t2title' local _dash_pending `"`_dash_pending' t2title"'
    if `: length local text' local _dash_pending `"`_dash_pending' text"'
    if `: length local title2' local _dash_pending `"`_dash_pending' title2"'
    if `: length local vertical' local _dash_pending `"`_dash_pending' vertical"'
    if `: length local xmlabel' local _dash_pending `"`_dash_pending' xmlabel"'
    if `: length local xmtick' local _dash_pending `"`_dash_pending' xmtick"'
    // WP-22: twoway's advanced xoverhangs and yoverhangs widen the graph
    // region so an end tick label does not run off the edge.
    if `: length local xoverhangs' local _dash_pending `"`_dash_pending' xoverhangs"'
    if `: length local ymlabel' local _dash_pending `"`_dash_pending' ymlabel"'
    if `: length local ymtick' local _dash_pending `"`_dash_pending' ymtick"'
    if `: length local yoverhangs' local _dash_pending `"`_dash_pending' yoverhangs"'
    // scheme(), xsize(), ysize(), xtick() and ytick() are NOT listed.  They
    // are twoway GRAPH-level options, and this program promotes them --
    // `sreturn local g_xsize' and friends just above, picked up by the
    // promotion loop in _dash_process_segment -- so however they are
    // written they reach the renderer and are honoured.  Naming them here
    // told a user who typed dash.sthlp's own example,
    //     dash scatter mpg weight, xsize(10) ysize(2)
    // that dash had ignored two options it had just applied.
    // Whatever Stata could not match at all, via the trailing *, and the
    // log and nolog taken out before -syntax- ran.
    if `: length local _dash_logw' {
        mata: st_local("options", strtrim(st_local("options") + " " + st_local("_dash_logw")))
    }
    local _dash_unknown : copy local options

    sreturn local mcolor           : copy local mcolor
    sreturn local msymbol          : copy local msymbol
    sreturn local msize            : copy local msize
    sreturn local msangle          : copy local msangle
    sreturn local mfcolor          : copy local mfcolor
    sreturn local mlcolor          : copy local mlcolor
    sreturn local mlabel           : copy local mlabel
    sreturn local mlabcolor        : copy local mlabcolor
    sreturn local mlabsize         : copy local mlabsize
    sreturn local mlabposition     : copy local mlabposition
    sreturn local mlabgap          : copy local mlabgap
    sreturn local mlabwidth        : copy local mlabwidth
    sreturn local malpha           : copy local malpha
    sreturn local marker           : copy local marker
    sreturn local lcolor           : copy local lcolor
    sreturn local lwidth           : copy local lwidth
    sreturn local lpattern         : copy local lpattern
    sreturn local lalpha           : copy local lalpha
    sreturn local fcolor           : copy local fcolor
    sreturn local fintensity       : copy local fintensity
    sreturn local falpha           : copy local falpha
    sreturn local acolor           : copy local acolor
    sreturn local alcolor          : copy local alcolor
    sreturn local alwidth          : copy local alwidth
    sreturn local alpattern        : copy local alpattern
    sreturn local barwidth         : copy local barwidth
    sreturn local base             : copy local base
    sreturn local blcolor          : copy local blcolor
    sreturn local bfcolor          : copy local bfcolor
    sreturn local jitter           : copy local jitter
    sreturn local jseed            : copy local jseed
    sreturn local yaxis            : copy local yaxis
    sreturn local xaxis            : copy local xaxis
    sreturn local colorvar         : copy local colorvar
    sreturn local colpalette       : copy local colpalette
    sreturn local colordiscrete    : copy local colordiscrete
    sreturn local coloruseplegend  : copy local coloruseplegend
    sreturn local colornlevels     : copy local colornlevels
    sreturn local colorcuts        : copy local colorcuts
    sreturn local colormissing     : copy local colormissing
    sreturn local colorlevels      : copy local colorlevels
    sreturn local colorvarminmax   : copy local colorvarminmax
    sreturn local bwidth           : copy local bwidth
    sreturn local bw               : copy local bw
    sreturn local degree           : copy local degree
    sreturn local pstyle           : copy local pstyle
    sreturn local cmissing         : copy local cmissing
    sreturn local recast           : copy local recast
    sreturn local connect          : copy local connect
    sreturn local bin              : copy local bin
    sreturn local width            : copy local width
    sreturn local start            : copy local start
    sreturn local percent          : copy local percent
    sreturn local frequency        : copy local frequency
    sreturn local density          : copy local density
    sreturn local fraction         : copy local fraction
    sreturn local kernel           : copy local kernel
    sreturn local n                : copy local n
    sreturn local level            : copy local level
    sreturn local bands            : copy local bands
    sreturn local at               : copy local at
    sreturn local ciopts           : copy local ciopts
    sreturn local lineopts         : copy local lineopts
    sreturn local fitopts          : copy local fitopts
    sreturn local color            : copy local color
    sreturn local mlwidth          : copy local mlwidth
    sreturn local mstyle           : copy local mstyle
    sreturn local lstyle           : copy local lstyle
    sreturn local mlstyle          : copy local mlstyle
    sreturn local mlpattern        : copy local mlpattern
    sreturn local blabel           : copy local blabel
    sreturn local horizontal       : copy local horizontal
    sreturn local vertical         : copy local vertical
    sreturn local sort             : copy local sort
    sreturn local range            : copy local range
    sreturn local colorlist        : copy local colorlist
    sreturn local jitterseed       : copy local jitterseed
    // WP-22: the honoured F3 options.  The connecting-line triple is kept
    // or dropped by plot type in _dash_fold_cl, once the type is known.
    sreturn local clcolor          : copy local clcolor
    sreturn local clpattern        : copy local clpattern
    sreturn local clwidth          : copy local clwidth
    sreturn local mlabangle        : copy local mlabangle
    sreturn local mlabformat       : copy local mlabformat
    // The seven statistical sub-options (WP-18): declared with twoway's own
    // minimum abbreviations (twoway_histogram_parse.class DISCrete;
    // twoway_lfitci_parse.class STDP STDF STDR, none abbreviable;
    // twoway_lowess_parse.class Mean noWeight Adjust LOgit).  MEan is
    // declared one letter longer than twoway's `m': this parser also
    // declares Msymbol(), and test_abbreviations.py refuses a prefix two
    // options could claim.  Which type each belongs to is enforced by the
    // flag rules in _dash_option_rules, not here.
    sreturn local discrete         : copy local discrete
    sreturn local stdp             : copy local stdp
    sreturn local stdf             : copy local stdf
    sreturn local stdr             : copy local stdr
    sreturn local mean             : copy local mean
    sreturn local noweight         : copy local noweight
    sreturn local adjust           : copy local adjust
    sreturn local logit            : copy local logit
    /* ---- graph-level (returned separately so _dash_plot can accumulate them) ---- */
    sreturn local g_title        : copy local title
    sreturn local g_subtitle     : copy local subtitle
    sreturn local g_note         : copy local note
    sreturn local g_caption      : copy local caption
    sreturn local g_name         : copy local name
    sreturn local g_saving       : copy local saving
    sreturn local g_xtitle       : copy local xtitle
    sreturn local g_ytitle       : copy local ytitle
    sreturn local g_xlabel       : copy local xlabel
    sreturn local g_ylabel       : copy local ylabel
    sreturn local g_xline        : copy local xline
    sreturn local g_yline        : copy local yline
    sreturn local g_legend       : copy local legend
    sreturn local g_by           : copy local by
    sreturn local g_xscale       : copy local xscale
    sreturn local g_yscale       : copy local yscale
    sreturn local g_aspectratio  : copy local aspectratio
    sreturn local g_scheme       : copy local scheme
    sreturn local g_plotregion   : copy local plotregion
    sreturn local g_graphregion  : copy local graphregion
    sreturn local g_bgcolor      : copy local bgcolor
    sreturn local g_plotbgcolor  : copy local plotbgcolor
    sreturn local g_link         : copy local link
    sreturn local g_filter       : copy local filter
    sreturn local g_ytitle2      : copy local ytitle2
    sreturn local g_xtitle2      : copy local xtitle2
    sreturn local g_ylabel2      : copy local ylabel2
    sreturn local g_xlabel2      : copy local xlabel2
    sreturn local g_yscale2      : copy local yscale2
    sreturn local g_xscale2      : copy local xscale2
    sreturn local g_xsize        : copy local xsize
    sreturn local g_ysize        : copy local ysize
    sreturn local g_fxsize       : copy local fxsize
    sreturn local g_fysize       : copy local fysize
    sreturn local g_scale        : copy local scale
    sreturn local g_hover        : copy local hover
    sreturn local g_text         : copy local text
    sreturn local g_xtick        : copy local xtick
    sreturn local g_ytick        : copy local ytick
    sreturn local g_xmtick       : copy local xmtick
    sreturn local g_ymtick       : copy local ymtick
    sreturn local g_xmlabel      : copy local xmlabel
    sreturn local g_ymlabel      : copy local ymlabel
    sreturn local g_t1title      : copy local t1title
    sreturn local g_t2title      : copy local t2title
    sreturn local g_b1title      : copy local b1title
    sreturn local g_b2title      : copy local b2title
    sreturn local g_l1title      : copy local l1title
    sreturn local g_l2title      : copy local l2title
    sreturn local g_r1title      : copy local r1title
    sreturn local g_r2title      : copy local r2title
    sreturn local g_title2       : copy local title2
    sreturn local g_subtitle2    : copy local subtitle2
    sreturn local g_zlabel       : copy local zlabel
    sreturn local g_ztitle       : copy local ztitle
    sreturn local g_zscale       : copy local zscale
    sreturn local g_nodraw       : copy local nodraw
    sreturn local g_play         : copy local play
    sreturn local g_replace      : copy local replace
    sreturn local _pending  : copy local _dash_pending
    sreturn local _unknown  : copy local _dash_unknown
end


// ================================================================
// _dash_parse_varpart_std  — varlist [if] [in]  (1-to-many vars)
// Sets s(varlist), s(if_clause), s(in_clause)
// ================================================================
program define _dash_parse_varpart_std, sclass
    version 16.0
    // numeric (GAPS2 G2): twoway's own y/x parser declares `varlist(min=2
    // numeric ts default=none)' (twoway_yxview_parse.class); a string
    // variable here is refused by this line, before any other check runs,
    // with the exact rc and words twoway's own `syntax' gives -- measured
    // identical across every family that takes variables (scatter,
    // histogram, rarea, pcspike, tsline, tsrline, lfit: "string variables
    // not allowed in varlist; <name> is a string variable", r(109)) --
    // never typed here by hand (test_adversarial.cscript SV-01..SV-87,
    // generated by scripts/gen_string_varlists_cscript.py).  Previously a
    // string x or y drew meaningless glyphs with no note.
    syntax varlist(numeric) [if] [in] [aweight fweight pweight iweight]
    // The weight type and its expression are handed to _dash_process_segment,
    // which honours, names or refuses them by plot type (WP-18).  syntax
    // leaves the expression in `exp' WITH its leading `= ' (measured:
    // `[aw=price]' gives exp `= price'); that is stripped here.
    if `"`weight'"' != "" sreturn local _weight `"`weight'"'
    // The expression is stripped in Mata, by value: in compound quotes inside
    // regexr() a weight holding "' -- [aw=cond(make=="'x",1,2)] -- ended
    // them (test_json_escaping.cscript JSE-47).  It and the qualifier go
    // back by `: copy local': through compound quotes a macro in them was
    // expanded again (JSE-66, JSE-69).
    if `: length local exp' {
        mata: st_local("_wx0", strtrim(regexr(st_local("exp"), "^[ ]*=[ ]*", "")))
        sreturn local _wexp : copy local _wx0
    }
    sreturn local varlist    "`varlist'"
    sreturn local if_clause  : copy local if
    sreturn local in_clause  : copy local in
end

// ================================================================
// _dash_parse_varpart_1v   — exactly 1 variable
// ================================================================
program define _dash_parse_varpart_1v, sclass
    version 16.0
    // varname(numeric) (GAPS2 G2): twoway's own declaration for the
    // univariate family (histogram.ado, kdensity.ado); varname sets
    // `varlist' too (one word), so the sreturns below stand unchanged.
    // Refuses a string variable with twoway's own rc and words, measured
    // identical to the y/x family's (test_adversarial.cscript
    // SV-01..SV-87).
    syntax varname(numeric) [if] [in] [aweight fweight pweight iweight]
    // The weight type and its expression are handed to _dash_process_segment,
    // which honours, names or refuses them by plot type (WP-18).  syntax
    // leaves the expression in `exp' WITH its leading `= ' (measured:
    // `[aw=price]' gives exp `= price'); that is stripped here.
    if `"`weight'"' != "" sreturn local _weight `"`weight'"'
    // The expression is stripped in Mata, by value: in compound quotes inside
    // regexr() a weight holding "' -- [aw=cond(make=="'x",1,2)] -- ended
    // them (test_json_escaping.cscript JSE-47).  It and the qualifier go
    // back by `: copy local': through compound quotes a macro in them was
    // expanded again (JSE-66, JSE-69).
    if `: length local exp' {
        mata: st_local("_wx0", strtrim(regexr(st_local("exp"), "^[ ]*=[ ]*", "")))
        sreturn local _wexp : copy local _wx0
    }
    sreturn local varlist    "`varlist'"
    sreturn local if_clause  : copy local if
    sreturn local in_clause  : copy local in
end

// ================================================================
// _dash_parse_varpart_3v   — the range plots' variables
//
// Any number: the count is checked by _dash_process_segment, in twoway's
// words for each type.  max=3 answered four variables "too many variables
// specified", where twoway says "rarea requires 3 variables: ...", and
// min=2 refused tsrline's one variable in -syntax-'s words, where twoway
// names the time variable (test_parser.cscript P1A-78).
// ================================================================
program define _dash_parse_varpart_3v, sclass
    version 16.0
    // numeric (GAPS2 G2): see _dash_parse_varpart_std; the range family
    // (rarea, rbar, rspike, rcap, rline, rconnected, rcapsym, rscatter,
    // tsrline) refuses a string variable the same way, with the same
    // measured words (test_adversarial.cscript SV-01..SV-87).
    syntax varlist(numeric) [if] [in] [aweight fweight pweight iweight]
    // The weight type and its expression are handed to _dash_process_segment,
    // which honours, names or refuses them by plot type (WP-18).  syntax
    // leaves the expression in `exp' WITH its leading `= ' (measured:
    // `[aw=price]' gives exp `= price'); that is stripped here.
    if `"`weight'"' != "" sreturn local _weight `"`weight'"'
    // The expression is stripped in Mata, by value: in compound quotes inside
    // regexr() a weight holding "' -- [aw=cond(make=="'x",1,2)] -- ended
    // them (test_json_escaping.cscript JSE-47).  It and the qualifier go
    // back by `: copy local': through compound quotes a macro in them was
    // expanded again (JSE-66, JSE-69).
    if `: length local exp' {
        mata: st_local("_wx0", strtrim(regexr(st_local("exp"), "^[ ]*=[ ]*", "")))
        sreturn local _wexp : copy local _wx0
    }
    sreturn local varlist    "`varlist'"
    sreturn local if_clause  : copy local if
    sreturn local in_clause  : copy local in
end

// ================================================================
// _dash_parse_varpart_4v   — the pc* plots' variables
//
// Any number, checked by _dash_process_segment in twoway's words: "pcspike
// requires 4 variables: mpg weight", where -syntax- said "too few
// variables specified" (test_parser.cscript P1A-78).
// ================================================================
program define _dash_parse_varpart_4v, sclass
    version 16.0
    // numeric (GAPS2 G2): see _dash_parse_varpart_std; the pc family
    // (pcspike, pcarrow, pcbarrow, pcscatter, pccapsym) refuses a string
    // variable the same way (test_adversarial.cscript SV-01..SV-87).
    syntax varlist(numeric) [if] [in] [aweight fweight pweight iweight]
    // The weight type and its expression are handed to _dash_process_segment,
    // which honours, names or refuses them by plot type (WP-18).  syntax
    // leaves the expression in `exp' WITH its leading `= ' (measured:
    // `[aw=price]' gives exp `= price'); that is stripped here.
    if `"`weight'"' != "" sreturn local _weight `"`weight'"'
    // The expression is stripped in Mata, by value: in compound quotes inside
    // regexr() a weight holding "' -- [aw=cond(make=="'x",1,2)] -- ended
    // them (test_json_escaping.cscript JSE-47).  It and the qualifier go
    // back by `: copy local': through compound quotes a macro in them was
    // expanded again (JSE-66, JSE-69).
    if `: length local exp' {
        mata: st_local("_wx0", strtrim(regexr(st_local("exp"), "^[ ]*=[ ]*", "")))
        sreturn local _wexp : copy local _wx0
    }
    sreturn local varlist    "`varlist'"
    sreturn local if_clause  : copy local if
    sreturn local in_clause  : copy local in
end

// ================================================================
// _dash_parse_varpart_any  — arbitrary tokens [if] [in]
// Used for scatteri (literal numbers), pci, function
// ================================================================
program define _dash_parse_varpart_any, sclass
    version 16.0
    // equalok: twoway function's documented form is `function y = exp`.  Without
    // it Stata rejects the "=" with r(101) "=exp not allowed", which made the
    // `y=` stripper further down unreachable and the canonical form unusable.
    //
    // Weights (WP-23): twoway function takes an aweight, fweight or pweight
    // and draws nothing different; scatteri, pci and pcarrowi refuse all
    // three, r(198) "weights not allowed" (_dash_process_segment); every
    // one refuses an iweight, r(101) "iweights not allowed", and a weight
    // naming no variable r(111) -- measured 23sep2026.  With no weight
    // clause declared, syntax answered every weight with r(101) "weights
    // not allowed".
    //
    // The plain parse runs first, and the weighted one only when it is
    // refused for a weight clause (r(101): the options were split off
    // before this runs).  Declaring weights up front made syntax read a
    // label that looks like one -- scatteri 1 2 "[aw=price]" -- as a
    // weight; twoway reads it as a label (rc 0, measured).  iweight is
    // left undeclared, so syntax gives twoway's own refusal for it,
    // before it reads the expression.
    //
    // The values are optional here: none at all -- `dash scatteri, name(x)',
    // or an if, an in or a weight alone -- is its caller's to refuse, in
    // twoway's words for each type (P1A-70, P1A-71).  syntax answered it
    // with "something required", r(100), which twoway never says.
    capture syntax [anything(name=vals equalok)] [if] [in]
    if _rc == 101 {
        syntax [anything(name=vals equalok)] [if] [in] [aweight fweight pweight]
        if `"`weight'"' != "" sreturn local _weight `"`weight'"'
        if `: length local exp' {
            mata: st_local("_wx0", strtrim(regexr(st_local("exp"), "^[ ]*=[ ]*", "")))
            sreturn local _wexp : copy local _wx0
        }
    }
    else if _rc {
        // Anything else is reported by syntax itself, as it always was.
        syntax [anything(name=vals equalok)] [if] [in]
    }
    // By value, as _dash_parse_varpart_std hands its back: a scatteri label
    // and a qualifier are the user's text (JSE-69).
    sreturn local vals       : copy local vals
    sreturn local if_clause  : copy local if
    sreturn local in_clause  : copy local in
end

// ================================================================
// _dash_graph_qualifier  -- the if/in written after the plot groups
//
// Usage:  _dash_graph_qualifier <qualifier text>
// After:  _gq_if and _gq_in in the caller hold the expression and the
//         range, without their keywords, or "".
//
// The text is every qualifier piece _dash_split_segs found at the top
// level of a parenthesised command -- after the last group, or before a
// `||' -- joined with blanks.  -syntax- reads it as twoway reads it: one
// `if' and one `in', in either order, and nothing else.  Measured against
// twoway, 23sep2026: a second `if' is r(198) there ("multiple global if's
// not allowed") and "invalid syntax" here; a plot group after the
// qualifier is "invalid '('" in both; a stray word is "invalid 'foo'" in
// both.  The keyword is taken off by position: -syntax- guarantees the
// macro starts with it, and `if(foreign==1)', which twoway takes, has no
// blank after it.
// ================================================================
program define _dash_graph_qualifier
    version 16.0
    syntax [if] [in]
    // The keyword comes off in Mata, by value, and the result goes back by
    // `: copy local'.  In compound quotes inside regexr() a qualifier
    // holding "' ended the quote: if make != "'x" came back as  make !=,
    // with rc 0 (measured 24sep2026; test_json_escaping.cscript JSE-45); and
    // a copy through them expanded a macro in it again (JSE-66).
    mata: st_local("_gi", strtrim(regexr(st_local("if"), "^[ ]*if", "")))
    mata: st_local("_gn", strtrim(regexr(st_local("in"), "^[ ]*in", "")))
    // Its abbreviations written out, as a plot's are in
    // _dash_process_segment (QL-22).
    mata: st_local("_gi", _dash_qual_expand(st_local("_gi")))
    c_local _gq_if : copy local _gi
    c_local _gq_in : copy local _gn
end


// ================================================================
// _dash_fold_bw  -- resolve the bw() alias once the plot type is known.
//
// twoway accepts bw() only as an abbreviation of bwidth(), and only on the
// bandwidth plot types (measured rc 0: lpoly, lpolyci, lowess, kdensity);
// on bar, rbar, histogram, dot, spike, scatter, line and fpfit it is
// r(198) "option bw() not allowed".  dash keeps its documented reading of
// bw() as barwidth() on the bar family, where twoway takes barwidth() --
// a superset that cannot change the meaning of a valid twoway command --
// and names bw() in the note everywhere else, as an option it has no
// reading for.  Called after _dash_parse_plot_opts, whose s() survives
// this second sclass call.
//
// It is also where the other options whose reading depends on the plot type
// are resolved: clcolor(), clpattern() and clwidth() (WP-22), in
// _dash_fold_cl below, mlabel(), in _dash_fold_mlab, and width() on
// kdensity, which is twoway's synonym for bwidth() there (WP-23) -- all
// before the early exit for a segment with no bw().
// ================================================================
program define _dash_fold_bw, sclass
    version 16.0
    args ptype
    _dash_fold_cl "`ptype'"
    _dash_fold_mlab "`ptype'"
    // A kernel written as an option of its own -- lpoly mpg weight,
    // gaussian: twoway's old syntax -- is kernel(gaussian) on lpoly,
    // lpolyci and kdensity, from each shortest spelling (gau, ep, epan2 ..)
    // to the full name (_dash_kernel_flag; measured 24sep2026, the serset
    // of kernel(<name>) each time).  It fell to the catch-all, was named in
    // the note, and the default epanechnikov was drawn.  Two kernels, or one
    // beside kernel(), were refused by _dash_opts_repeats before this; on
    // any other type the word stays where it is.  Read by value.
    mata: _dash_kernel_flag(st_global("s(_unknown)"), st_local("ptype"))
    if `: length local _kf_name' {
        sreturn local kernel : copy local _kf_name
        sreturn local _unknown : copy local _kf_rest
    }
    // kdensity: width(#) is twoway's own synonym for bwidth(#)
    // (twoway_kdensity_parse.class: Width(real 0) BWidth(real 0), the two
    // together "options width() and bwidth() may not be combined", r(198);
    // bw() is bwidth()'s abbreviation there, so it counts as bwidth()).
    // Measured 23sep2026: `twoway kdensity mpg, width(2)' plots bwidth(2)'s
    // serset.  dash's width() is histogram's bin width, and on kdensity it
    // reached the renderer as "width" and changed nothing (WP-23).
    // The values are the user's text, read from s() by value and put back by
    // `: copy local', or through macval() as bwidth() always was: read as
    // `"`s(bw)'"', bw("\`x'") was expanded to nothing and dropped with rc 0
    // (measured 24sep2026; test_json_escaping.cscript JSE-69).
    mata: st_local("_kw", st_global("s(width)"))
    if "`ptype'" == "kdensity" & `: length local _kw' {
        mata: st_local("_fb", strofreal(st_global("s(bwidth)") + st_global("s(bw)") != ""))
        if `_fb' {
            display as error "options width() and bwidth() may not be combined"
            exit 198
        }
        // The value goes on to bwidth()'s rule in _dash_validate_opts, which
        // refuses anything but a positive number.
        sreturn local bwidth `"`macval(_kw)'"'
        sreturn local width ""
    }
    mata: st_local("bw", st_global("s(bw)"))
    if !`: length local bw' exit
    local bandwidth_types "lpoly lpolyci lowess kdensity"
    local bar_types       "bar rbar histogram dot spike"
    if `: list ptype in bandwidth_types' {
        mata: st_local("_fb", strofreal(st_global("s(bwidth)") != ""))
        if `_fb' {
            // twoway: the same option twice.  Measured r(198).
            display as error "option bwidth() may not be repeated: bw() is its abbreviation"
            exit 198
        }
        sreturn local bwidth : copy local bw
    }
    else if `: list ptype in bar_types' {
        mata: st_local("_fb", strofreal(st_global("s(barwidth)") == ""))
        if `_fb' sreturn local barwidth : copy local bw
    }
    else {
        mata: st_local("_fb", st_global("s(_unknown)") + " bw(" + st_local("bw") + ")")
        sreturn local _unknown : copy local _fb
    }
    sreturn local bw ""
end

// ================================================================
// _dash_fold_cl  -- keep clcolor(), clpattern() and clwidth() on the plot
//                   types whose CONNECTING line twoway styles with them.
//
// ROADMAP WP-22 AC-22.2.  twoway_yxview_parse.class factors CLColor() to
// line(color()) alone, where LColor() is line(color()) AND
// area(linestyle(color())), and factors the cl options after the l options
// whatever order they were typed in.  Which types draw that `line' style
// was measured 23sep2026 from SVG exports of what twoway draws: on line,
// connected, lfit, qfit, fpfit, lpoly, lowess, mspline, mband, kdensity,
// function and tsline, clX draws exactly what lX draws; on lfitci, qfitci,
// lpolyci and fpfitci it styles the fit line alone; on every other type --
// area, bar, histogram, spike, dropline, dot, scatter, the range and
// paired-coordinate types, scatteri and pci -- the picture is identical to
// one drawn with no option at all, and clwidth(-1), which twoway refuses
// when it draws the line ("gm_linewidth must be between 0.000 and
// 1.0e+04", r(198)), is accepted, because it is never evaluated.
//
// So the three are kept for the renderer on the types that draw the line,
// where it lets them style it in place of lcolor(), lpattern() and
// lwidth(), and dropped everywhere else: twoway draws nothing for them
// there, dash draws nothing either, and the note does not name them,
// because nothing dash draws differs from what twoway draws.  A plot type
// added to dash later is not on the list, and the three are dropped there
// until it is measured.
//
// Called first thing by _dash_fold_bw, so before _dash_validate_opts:
// clwidth()'s rule fires exactly where twoway evaluates the width.
// ================================================================
program define _dash_fold_cl, sclass
    version 16.0
    args ptype
    local cl_types "line connected lfit qfit fpfit lpoly lowess mspline mband kdensity function tsline lfitci qfitci lpolyci fpfitci"
    if `: list ptype in cl_types' exit
    sreturn local clcolor   ""
    sreturn local clpattern ""
    sreturn local clwidth   ""
end

// ================================================================
// _dash_fold_mlab  -- mlabel() where twoway refuses it, or never reads it.
//
// Measured 23sep2026, one twoway probe per plot type (rc, and the SVG it
// exports): on mspline and mband twoway reads mlabel()'s variable as a
// third plotted variable and refuses the command -- "too many variables
// specified", r(103) -- whatever the variable, string or numeric; a
// variable that does not exist it refuses with r(111) on every type but
// histogram and function, which never read the option at all
// (mlabel(nosuchvar) is rc 0 there, and draws nothing).
//
// So mlabel() is refused on mspline and mband, naming it, when its
// variable exists -- one that does not is refused r(111) by the value
// rules, as twoway refuses it -- and dropped on histogram and function
// before those rules run, so a variable that does not exist is not
// refused where twoway accepts it.  Everywhere else it reaches the
// renderer, which draws the labels where twoway draws them and nowhere
// else: none on line, area, the fits and the range lines, bars and caps,
// among others (dash.sthlp, Marker Label Options).  The note does not
// name mlabel() on those, because twoway draws nothing for it there
// either.
//
// Called by _dash_fold_bw, after _dash_fold_cl and before
// _dash_validate_opts.  The value is read from s() by value and only ever
// put on a command line through macval(), so a backtick or a dollar sign
// in it cannot become a macro reference.
// ================================================================
program define _dash_fold_mlab, sclass
    version 16.0
    args ptype
    // By value: read as `"`s(mlabel)'"', mlabel("\`x'") was expanded to
    // nothing, so on histogram it was not dropped and the value rules
    // refused it, r(111), where twoway accepts it (measured 24sep2026;
    // test_json_escaping.cscript JSE-69).
    mata: st_local("v", st_global("s(mlabel)"))
    if !`: length local v' exit
    local mlab_unread  "histogram function"
    local mlab_refused "mspline mband"
    if `: list ptype in mlab_unread' {
        sreturn local mlabel ""
        exit
    }
    if `: list ptype in mlab_refused' {
        capture confirm variable `macval(v)'
        if !_rc {
            display as error "dash: mlabel() is not allowed on `ptype' (twoway: too many variables specified)"
            exit 103
        }
    }
end

// ================================================================
// _dash_fold_typed  -- options dash draws on some plot types only, named in
//                      the note on the others.
//
// ROADMAP WP-23 (GAPS.md F4).  Measured 23sep2026 in both render modes:
//
// colorvar() is drawn on scatter, connected, rconnected and dot -- the
// types whose markers go through GlyphMapper.map_scatter -- and on no
// other.  On the other 36 types it and its five companions (colordiscrete,
// colorcuts(), colpalette(), colornlevels(), colormissing()) were written
// to the spec, read by nothing and named nowhere, while dash.sthlp said
// "a plot layer may take its colour from a third variable".  twoway itself
// accepts colorvar() on every type and colours many of them (line and bar,
// measured by SVG; not area or lfit), so a pasted command still runs, and
// the note says what dash did not draw.  A companion written without
// colorvar() configures nothing and is named the same way.
//
// jitter() moves the markers of scatter, connected, rconnected, dot,
// dropline and scatteri.  twoway also jitters the markers of rscatter,
// rcapsym, pcscatter and pccapsym (SVG, 23sep2026); dash drew them where
// the data are, and said nothing.  On those four jitter() -- with the seed
// that goes with it -- is named.  On the types that draw no marker
// twoway's picture does not change either, so nothing is named there, as
// _dash_fold_cl leaves the connecting-line options unnamed where no line
// is drawn.
//
// Called by _dash_process_segment AFTER _dash_validate_opts, so a value
// is refused wherever twoway refuses it (colorvar(nosuchvar) is r(111) on
// every type) before it is named.  The options stay in the spec, as the
// options on the pending lists of _dash_parse_plot_opts do -- accepted,
// written, reported -- and the renderer draws nothing for them there.
// sclass: it appends to s(_pending), which the segment hands to
// _dash_report_ignored, and touches nothing else in s().
// ================================================================
program define _dash_fold_typed, sclass
    version 16.0
    args ptype
    local named ""
    local cv_types "scatter connected rconnected dot"
    local cv_drawn = 0
    // Whether each option was given, read by value: tested as
    // `"`s(colormissing)'"', colormissing("\`x'") was expanded to nothing
    // and went unnamed (test_json_escaping.cscript JSE-69).
    mata: st_local("_ft", strofreal(st_global("s(colorvar)") != ""))
    if `: list ptype in cv_types' & `_ft' local cv_drawn = 1
    if !`cv_drawn' {
        foreach o in colorvar colordiscrete colorcuts colpalette colornlevels colormissing colorlevels colorvarminmax {
            mata: st_local("_ft", strofreal(st_global("s(`o')") != ""))
            if `_ft' local named "`named' `o'"
        }
    }
    local jit_undrawn "rscatter rcapsym pcscatter pccapsym"
    mata: st_local("_ft", strofreal(st_global("s(jitter)") != ""))
    if `: list ptype in jit_undrawn' & `_ft' {
        foreach o in jitter jitterseed jseed {
            mata: st_local("_ft", strofreal(st_global("s(`o')") != ""))
            if `_ft' local named "`named' `o'"
        }
    }
    // A bare sort: twoway joins a connected type's points in the order of x
    // with it, and dash always joins line, connected, area, tsline and the
    // range line and area types in that order (map_line, map_area,
    // map_rline, map_rarea and the types drawn through them), so there it is
    // what dash draws and is not named.  On every other type it is named, as
    // it was.  sort(varlist) is named by _dash_parse_plot_opts on every type.
    local sort_types "line connected area tsline rline rarea rconnected tsrline"
    mata: st_local("_ft", strofreal(st_global("s(sort)") != ""))
    if `_ft' & !`: list ptype in sort_types' {
        mata: st_local("_ft", strofreal(strpos(" " + st_global("s(_pending)") + " ", " sort ") > 0))
        if !`_ft' local named "`named' sort"
    }
    // pstyle() and the fitarea options acolor(), alcolor(), alwidth() and
    // alpattern() are drawn on a ci fit -- its band in the style pstyle()
    // names, and in the scheme's ci style otherwise, as twoway draws it
    // (BUGS.md, S3, "A ci band is filled in its line's colour, where Stata
    // fills it in pstyle ci"; measured 24sep2026) -- so on lfitci, qfitci,
    // lpolyci and fpfitci they come off the list _dash_parse_plot_opts
    // named them on.  The list holds option names only, never values.
    local ci_types "lfitci qfitci lpolyci fpfitci"
    if `: list ptype in ci_types' {
        local ci_drawn "pstyle acolor alcolor alwidth alpattern"
        mata: st_local("_ftp", st_global("s(_pending)"))
        local _ftk : list _ftp - ci_drawn
        if "`_ftk'" != "`_ftp'" sreturn local _pending `"`_ftk'"'
    }
    if "`named'" != "" sreturn local _pending `"`s(_pending)'`named'"'
end

// ================================================================
// _dash_check_legend  -- legend(top), legend(bottom), legend(left) and
//                        legend(right), refused as twoway refuses them.
//
// ROADMAP WP-23 (GAPS.md F4).  twoway has no such keywords: measured
// 23sep2026, `twoway (scatter mpg weight) (lfit mpg weight), legend(top)'
// is "option top not allowed", r(198), and so are bottom, left and right,
// alone or beside another sub-option.  dash.sthlp documented all four and
// the renderer drew them INSIDE the plot (top_center ...), where twoway
// draws nothing; it found the word anywhere in the text, so
// legend(label(1 "left")) moved the legend as well.  They are refused
// here, with twoway's message and the position() that says what was
// meant.
//
// The contents are read one sub-option at a time by -gettoken-, with
// bind (a parenthesised argument is part of its option) and quotes (a
// quoted word stays quoted), so a word inside a quoted label or inside
// another sub-option's parentheses is never taken for the keyword: only a
// bare top-level word is.  -syntax- read them once, and gave up -- rc 0,
// nothing refused -- on a legend() of three thousand words; -gettoken-
// reads that in 0.06 seconds.  The values are only ever expanded through
// macval(), so a backtick in a label cannot become a macro reference.
// Not sclass: it is called from _dash_validate_opts and must not touch s().
// ================================================================
program define _dash_check_legend
    version 16.0
    // The argument is read by value (_dash_text_args), and neither the text
    // nor a token is put inside quotes in a test: -args- and the tests cut
    // legend(label(1 "'90s") top) at its "', and the top beside it, which
    // twoway refuses, went through with rc 0 (measured 24sep2026;
    // test_json_escaping.cscript JSE-47).  A token is one of the four
    // keywords only when Mata says it is.
    mata: _dash_text_args(0, 0, 0)
    local legval : copy local _dash_txt
    local rest `"`macval(legval)'"'
    while `: length local rest' {
        gettoken tok rest : rest, bind quotes
        mata: st_local("_kwhit", anyof(("top", "bottom", "left", "right"), st_local("tok")) ? st_local("tok") : "")
        foreach kw in `_kwhit' {
            if "`kw'" == "top"    local _clk "12"
            if "`kw'" == "top"    local _where "above"
            if "`kw'" == "bottom" local _clk "6"
            if "`kw'" == "bottom" local _where "below"
            if "`kw'" == "left"   local _clk "9"
            if "`kw'" == "left"   local _where "to the left of"
            if "`kw'" == "right"  local _clk "3"
            if "`kw'" == "right"  local _where "to the right of"
            display as error "option `kw' not allowed"
            display as error "      twoway's legend() has no `kw'; legend(position(`_clk')) places the legend `_where' the plot."
            exit 198
        }
    }
end

// BEGIN shipped schemes (WP-17)
// ================================================================
// The one list of what dash can draw by name.
//
// `_dash_schemes' are the twenty scheme translations the package ships in
// schemes/ -- dash_render.py's SchemeParser._BUILTIN_NAMES is the same
// list, and test/test_scheme_resolution.py holds the two together --
// and `_dash_themes' are the theme() aliases the renderer maps onto them.
// _dash_validate_value reads both for the `scheme' kind and
// _dash_prepare_spec for theme(), so a name is accepted or refused by
// this list and nowhere else.  Third-party schemes installed in PLUS/s
// are deliberately not on it and not looked for (WP-05: the letter
// directories are shared); the help says to copy such a file into the
// working directory.
// ================================================================
program define _dash_shipped_schemes
    version 16.0
    c_local _dash_schemes "economist s1color s1manual s1mono s1rcolor s2color s2color8 s2gcolor s2gmanual s2manual s2mono sj stcolor stcolor_alt stgcolor stgcolor_alt stmono1 stmono2 stsj sttrans"
    c_local _dash_themes  "default clean mono dark economist sj"
end
// END shipped schemes (WP-17)

// BEGIN option-validation table (WP-15)
// ================================================================
// Option-value validation.
//
// Principle: dash refuses a value where twoway refuses it, refuses a
// non-number where a number-only option got a word twoway would silently
// ignore, and -- like twoway's own "(note: named style X not found in
// class Y, default attributes used)" -- reports and falls back on the
// scheme where a STYLE NAME (colour, symbol, size, line width, pattern,
// angle, clock position, intensity) is unknown.  Every bound below was
// measured against twoway (22sep2026, StataNow 19.5).  Five bounds are
// dash's own rather than twoway's AND say so in a second sentence of the
// refusal: yaxis/xaxis 1..2, degree 0..3, bin 1..1000, n 2..10000 (mspline's
// n 1..300 and bands 1..200 are twoway's) and the lowess bwidth (0,1].  The other dash-own bounds -- colornlevels 2..256,
// jitter 0..100, level strictly inside 0..100, barwidth > 0, aspectratio
// >= 0, jitterseed()/jseed() >= 0, kdensity bwidth > 0 -- are refused with
// the one sentence only.
//
// Token grammar: option=kind[,p1[,p2[,p3]]][@type1|type2].  Tokens are
// whitespace-separated.  A token with @ applies only to the plot types it
// names; a token without @ applies to every type that has no @ token for
// the same option.  Kinds -- num: a finite number, p1/p2 inclusive bounds
// (either may be empty), p3 = x makes both exclusive; int: an integer,
// p1/p2 bounds; pos: a number > 0, p1 an inclusive ceiling; style: a name
// passes untouched, a number must lie in [p1,p2] where bounds are given
// (mlabposition and fintensity have none: twoway accepts 13, 2.5, 150 and
// -5 with a note or silently, and the renderer notes and defaults), and a
// token that looks numeric but overflows real() (1e400) is refused, not
// passed as a name; istyle: a name, or an integer in [p1,p2] (no token
// uses it today); enum: one of the |-separated words, case-insensitive,
// normalised to lower case; numlist: a Stata numlist of between p1 and p2
// numbers (p2 empty = no ceiling), normalised to the expanded,
// blank-separated list (1(1)5 -> 1 2 3 4 5; 0,10 -> 0 10); var: exactly
// one existing variable, abbreviations expanded (unab) and normalised to
// the full name, a time-series expression (L.price on tsset data)
// refused, since dash cannot draw one; varlist: one or more, likewise;
// byvarlist: the text before the first top-level comma is a varlist, the
// rest is kept verbatim; format: a numeric display format (the gate is
// spelled out in _dash_validate_value); scheme (WP-17): a shipped scheme
// or theme name from _dash_shipped_schemes, case-insensitive (a shipped
// name may carry the .scheme extension), or a .scheme
// file in the working directory named bare or with the extension -- no
// `/', `\' or `..' -- passed through as written.  A number that passes a num, int
// or pos rule reaches the renderer in one canonical spelling: an int as
// %21.0f (2.0, 02, +2 and 1E3 -> 2, 2, 2, 1000); a num or pos as written
// when it is a plain decimal or e-notation Python parses, else as %21.0g
// (1d3 -> 1000).  Tabs around a value are trimmed before it is read.
//
// test/test_option_validation.py reads this table out of dash.ado and
// test/test_option_validation.cscript exercises every token against Stata.
// ================================================================
program define _dash_option_rules
    version 16.0
    // Plot rules: validated once per segment, after _dash_fold_bw, from s().
    local plot ///
        msize=style  mlabsize=style  mlabgap=style ///
        lwidth=style,0,10000  mlwidth=style,0,10000 ///
        msangle=style,-360,360  mlabposition=style  fintensity=style ///
        jitter=num,0,100  jitterseed=int,0  jseed=int,0 ///
        yaxis=int,1,2  xaxis=int,1,2 ///
        malpha=num,0,100  lalpha=num,0,100  falpha=num,0,100 ///
        base=num  barwidth=pos  level=num,0,100,x ///
        degree=int,0,3  bwidth=pos,1@lowess  bwidth=pos ///
        kernel=enum,epanechnikov|epan2|biweight|cosine|gaussian|parzen|rectangle|triangle ///
        n=int,1,300@mspline  n=int,2,10000  bin=int,1,1000  width=pos  start=num  bands=int,1,200 ///
        colornlevels=int,2,256  colorlevels=int ///
        colpalette=enum,viridis|magma|inferno|plasma|cividis|turbo|greys|blues|reds ///
        colorcuts=numlist,1  colorvar=var  mlabel=var  range=numlist,2,2 ///
        clwidth=style,0,10000 ///
        alwidth=style,0,10000@lfitci|qfitci|lpolyci|fpfitci|area|bar|spike|dropline|histogram|rarea|rbar|rspike|rcap|rcapsym|rline|rconnected|tsrline|pcspike|pcarrow|pcbarrow|pcscatter|pccapsym|pci ///
        mlabangle=style,-360,360@scatter|connected|bar|dot|dropline|rcapsym|rconnected|rscatter|pcscatter|pccapsym|scatteri
    // alwidth(), the outline of a ci fit's band, has them too: measured
    // 24sep2026, `twoway lfitci mpg weight, alwidth(-1)' and alwidth(20000)
    // are "gm_linewidth must be between 0.000 and 1.0e+04", r(198), and
    // alwidth(0) and alwidth(10000) draw (fixtures/value_truth.json
    // alwidth_1-12).  Drawn, twoway refuses alwidth(-1) on exactly the
    // types listed -- every type with an area or a line style of its own
    // besides the connecting line -- and draws it on line, connected, the
    // fits and smooths, kdensity, function, tsline, scatter, dot, rscatter
    // and scatteri (measured per type 24sep2026; test_ci_band_options
    // .cscript asks twoway again).  Refused where twoway refuses it; dash
    // draws it on the four ci types and names it on every other
    // (_dash_fold_typed).
    // WP-22.  clwidth() has lwidth()'s bounds -- twoway refuses clwidth(-1)
    // and lwidth(-1) alike, "gm_linewidth must be between 0.000 and
    // 1.0e+04", r(198) -- but only where it draws the connecting line;
    // _dash_fold_cl has dropped the triple everywhere else before this runs,
    // so the rule needs no type list.  mlabangle() takes an anglestyle name
    // (never refused: twoway notes an unknown one) or degrees, and twoway
    // refuses a number outside -360..360, "textangle must be between
    // -360.000 and 360.000", r(198), where it draws marker labels --
    // measured 23sep2026 on exactly the types listed (pccapsym with the
    // marker-label parity work; the rule had left it out).  On pcarrow and
    // pcbarrow, which draw labels too, twoway prints that message and
    // returns rc 0, drawing the arrows without their labels, so they are
    // not refused; the renderer reports the angle and draws horizontal.
    // Elsewhere twoway never evaluates the angle, and neither does this
    // table.
    // Graph rules: validated once per segment in _dash_validate_opts, from
    // s(g_<opt>) -- so a value inside a segment is refused as twoway refuses
    // it even when a later segment or the after-comma part outranks it --
    // and once per graph in _dash_plot, from the g_<opt> accumulators,
    // after an after-comma option has outranked a segment's.
    // scheme (WP-17): a name the renderer could not resolve used to reach
    // it with rc 0 and be drawn as s2color under a warning, half applied
    // when the file existed and was named bare.  Refused here instead, on
    // the immediate route, on a registered graph and inside a segment
    // alike, by the same rule `dash build' and `dash serve' apply.
    local graph ///
        xsize=style,1,100  ysize=style,1,100  aspectratio=num,0  hover=varlist  by=byvarlist ///
        scheme=scheme ///
        xlabel=axislist  ylabel=axislist  xlabel2=axislist  ylabel2=axislist ///
        xtick=axislist  ytick=axislist  xmtick=axislist  ymtick=axislist ///
        xmlabel=axislist  ymlabel=axislist
    // Flag applicability (WP-18): flag[|flag...]@type[|type...].  A flag
    // written on a type outside its list is refused as twoway refuses it,
    // r(198) "option <flag> not allowed" (measured 23sep2026: scatter
    // discrete, lfit stdf, histogram mean, scatter noweight/logit/adjust,
    // lowess stdp).  Checked in _dash_validate_opts, which also refuses
    // more than one of stdp/stdf/stdr and discrete beside bin()/bins().
    // fpfitci is on the std list (WP-23): twoway fpfitci takes stdp -- its
    // band is the stdp band -- and refuses stdf and stdr in its own words,
    // which _dash_validate_opts reproduces (measured 23sep2026: stdp rc 0;
    // stdf, stdr r(198) "stdf not allowed").  dash refused stdp there.
    local flags ///
        discrete@histogram  stdp|stdf|stdr@lfitci|qfitci|fpfitci ///
        mean|noweight|adjust|logit@lowess
    c_local _dash_rules_plot  `"`plot'"'
    c_local _dash_rules_graph `"`graph'"'
    c_local _dash_rules_flags `"`flags'"'
end

// ----------------------------------------------------------------
// _dash_validate_value  prefix opt spec value ptype
//
// Checks ONE value against ONE spec (the part of a table token after "="
// and before any "@").  On refusal it prints one line, as error, and
// exits 198 -- or 111 for a variable that does not exist, twoway's own
// code for that.  It hands the value back in the caller's local
// _dash_vnorm, normalised where the kind says so (an expanded variable
// name, a lower-cased keyword) and otherwise exactly as it came in.
// The value is only ever expanded through macval(), so a backtick inside
// it cannot become a macro reference when it is tested or echoed.
// rclass, so numlist's and tsrevar's r() stay in here; it never touches
// s(), and it calls no sclass command: tsunab and fvunab clear s(), and
// measured 22sep2026 that wiped every option of the segment being
// validated (colorvar(L.price) jitter(5) msize(large) registered with
// options {}).
// ----------------------------------------------------------------
program define _dash_validate_value, rclass
    version 16.0
    // The arguments are read by value (_dash_text_args): prefix, opt, spec
    // and ptype are dash's own words and the value the user's text, which
    // -args- cut at a "' in it -- by(foreign, title(`"'90s bc"')) stopped
    // with r(133) (measured 24sep2026; test_json_escaping.cscript JSE-46).
    // Every test below reads the value through the string scalars V and T,
    // never inside quotes.
    mata: _dash_text_args(3, 1, 0)
    local prefix `"`_dash_a1'"'
    local opt    `"`_dash_a2'"'
    local spec   `"`_dash_a3'"'
    local ptype  `"`_dash_a4'"'
    local value : copy local _dash_txt

    local kind ""
    local p1 ""
    local p2 ""
    local p3 ""
    if regexm("`spec'", "^([^,]*),?([^,]*),?([^,]*),?([^,]*)$") {
        local kind = regexs(1)
        local p1   = regexs(2)
        local p2   = regexs(3)
        local p3   = regexs(4)
    }
    local norm `"`macval(value)'"'

    // The numeric reading of the value, with tabs and blanks trimmed off
    // first (syntax strips blanks but keeps tabs, and twoway accepts a
    // tab-padded jitter()).  real() is missing for a word, for "." and for
    // a magnitude beyond c(maxdouble) such as 1e308, and every one of those
    // is "not a number" here.  A scalar keeps full precision for the
    // comparisons below.  `plain' says the text is a decimal or e-notation
    // spelling Python's float() reads back; `numlike' says it is made of
    // digits, signs, dots and exponent letters only (1e400, 1d3), so that a
    // style kind can tell an overflow from a name.
    tempname V T
    mata: st_strscalar(st_local("V"), st_local("value"))
    scalar `T' = ustrtrim(scalar(`V'))
    mata: st_local("tv", st_strscalar(st_local("T")))
    tempname R
    scalar `R' = .
    capture scalar `R' = real(scalar(`T'))
    if _rc scalar `R' = .
    local isnum = (`R' < .)
    local plain   = regexm(scalar(`T'), "^[-+]?([0-9]+\.?[0-9]*|\.[0-9]+)([eE][-+]?[0-9]+)?$")
    local numlike = regexm(scalar(`T'), "^[-+.0-9eEdD]*[0-9][-+.0-9eEdD]*$")

    // Where the bound is dash's own and not twoway's, the message says so.
    local extra ""
    if inlist("`opt'", "yaxis", "xaxis") {
        local extra ". dash draws two axes."
    }
    else if "`opt'" == "degree" {
        local extra ". dash fits local polynomials up to degree 3."
    }
    else if "`opt'" == "bin" {
        local extra ". dash draws up to 1000 bins."
    }
    else if "`opt'" == "n" & "`ptype'" != "mspline" {
        // mspline's 1..300 is twoway's own ("n must be between 1 and 300").
        local extra ". dash evaluates up to 10000 points."
    }
    else if "`opt'" == "bwidth" & "`ptype'" == "lowess" {
        local extra ". lowess bwidth() is the fraction of the sample."
    }

    local bad ""
    if "`kind'" == "num" {
        if "`p3'" == "x"                     local bad "a number strictly between `p1' and `p2'"
        else if "`p1'" != "" & "`p2'" != ""  local bad "a number between `p1' and `p2'"
        else if "`p1'" != ""                 local bad "a number of at least `p1'"
        else if "`p2'" != ""                 local bad "a number no greater than `p2'"
        else                                 local bad "a number"
        local ok = `isnum'
        if `ok' {
            if "`p3'" == "x" {
                if `R' <= `p1' | `R' >= `p2' local ok = 0
            }
            else {
                if "`p1'" != "" {
                    if `R' < `p1' local ok = 0
                }
                if "`p2'" != "" {
                    if `R' > `p2' local ok = 0
                }
            }
        }
        if `ok' {
            local bad ""
            // As written when Python parses it; a Stata-only spelling
            // such as 1d3 goes out as the number it read.  A copy, not
            // macval() on a one-line if, whose command Stata expands again.
            if `plain' local norm : copy local tv
            else       local norm = strtrim(string(`R', "%21.0g"))
        }
    }
    else if "`kind'" == "int" {
        if "`p1'" != "" & "`p2'" != ""       local bad "an integer between `p1' and `p2'"
        else if "`p1'" != ""                 local bad "an integer of at least `p1'"
        else if "`p2'" != ""                 local bad "an integer no greater than `p2'"
        else                                 local bad "an integer"
        local ok = `isnum'
        if `ok' {
            if `R' != int(`R') local ok = 0
            if "`p1'" != "" {
                if `R' < `p1' local ok = 0
            }
            if "`p2'" != "" {
                if `R' > `p2' local ok = 0
            }
        }
        if `ok' {
            local bad ""
            // One canonical spelling: yaxis(2.0), yaxis(02), yaxis(+2) and
            // n(1E3) reach the renderer as 2, 2, 2 and 1000, where it
            // compares the text or calls int() on it.
            local norm = strtrim(string(`R', "%21.0f"))
        }
    }
    else if "`kind'" == "pos" {
        if "`p1'" != ""                      local bad "a positive number no greater than `p1'"
        else                                 local bad "a positive number"
        local ok = `isnum'
        if `ok' {
            if `R' <= 0 local ok = 0
            if "`p1'" != "" {
                if `R' > `p1' local ok = 0
            }
        }
        if `ok' {
            local bad ""
            if `plain' local norm : copy local tv
            else       local norm = strtrim(string(`R', "%21.0g"))
        }
    }
    else if "`kind'" == "style" {
        // A name is a style name and passes untouched: the renderer falls
        // back on the scheme, with a note, if it turns out to be unknown.
        // Only a NUMBER is held to the bounds, which are twoway's own.
        // A token made of digits and exponent letters whose real() is
        // missing (1e400, 1e308) is an overflow, not a name: refused, as
        // twoway's "invalid syntax", so the renderer never sees inf.
        if "`p1'" != "" & "`p2'" != "" {
            if `isnum' {
                if `R' < `p1' | `R' > `p2' local bad "a name or a number between `p1' and `p2'"
            }
            else if `numlike' local bad "a name or a number between `p1' and `p2'"
        }
        else if !`isnum' & `numlike' local bad "a name or a number"
    }
    else if "`kind'" == "istyle" {
        if `isnum' {
            if `R' != int(`R') | `R' < `p1' | `R' > `p2' {
                local bad "a name or an integer between `p1' and `p2'"
            }
        }
        else if `numlike' local bad "a name or an integer between `p1' and `p2'"
    }
    else if "`kind'" == "enum" {
        tempname L
        scalar `L' = lower(scalar(`T'))
        local lv = scalar(`L')
        local choices : subinstr local p1 "|" " ", all
        local hit = 0
        foreach c of local choices {
            if scalar(`L') == "`c'" local hit = 1
        }
        if `hit' local norm : copy local lv
        else {
            local pretty : subinstr local p1 "|" ", ", all
            local bad "one of `pretty'"
        }
    }
    else if "`kind'" == "numlist" {
        if "`p2'" == ""                      local bad "a list of at least `p1' numbers"
        else if "`p1'" == "`p2'"             local bad "a list of exactly `p1' numbers"
        else                                 local bad "a list of between `p1' and `p2' numbers"
        // A numlist holds no double quote; one that does is not one, and is
        // never put on numlist's command line, where a "' in it would end
        // the quotes and let the rest be read as numlist's own options.
        local _nlrc 7
        if !strpos(scalar(`V'), char(34)) {
            capture numlist `"`macval(value)'"'
            local _nlrc = _rc
        }
        if !`_nlrc' {
            local cnt : word count `r(numlist)'
            local ok = (`cnt' >= `p1')
            if "`p2'" != "" {
                if `cnt' > `p2' local ok = 0
            }
            if `ok' {
                local bad ""
                // The expanded, blank-separated list: the renderer splits
                // on blanks and reads floats, so 1(1)5 and 0,10 go out as
                // "1 2 3 4 5" and "0 10".
                local norm `"`r(numlist)'"'
            }
        }
    }
    else if "`kind'" == "axislist" {
        // WP-28 S14 (GAPS2 B1): every numlist run of an axis-label option
        // expanded by Stata's own numlist (_dash_axis_expand); never a
        // refusal -- a run numlist cannot read is left as written and the
        // renderer names or bounds it.
        _dash_axis_expand `"`macval(value)'"'
        mata: st_local("norm", st_global("r(norm)"))
    }
    else if inlist("`kind'", "var", "varlist", "byvarlist") {
        local head `"`macval(value)'"'
        local tail ""
        local hastail = 0
        if "`kind'" == "byvarlist" {
            // Split at the first comma outside parentheses: the by-variables
            // come before it, the sub-options (kept verbatim) after it.  The
            // value is read through V: by(foreign, title("'90s by")) is
            // twoway's own form.
            local len = strlen(scalar(`V'))
            local depth = 0
            local cut = 0
            forvalues i = 1/`len' {
                if substr(scalar(`V'), `i', 1) == "(" {
                    local depth = `depth' + 1
                }
                else if substr(scalar(`V'), `i', 1) == ")" {
                    local depth = `depth' - 1
                }
                else if substr(scalar(`V'), `i', 1) == "," & `depth' == 0 {
                    local cut = `i'
                    continue, break
                }
            }
            if `cut' > 0 {
                local head = substr(scalar(`V'), 1, `cut' - 1)
                local tail = strltrim(substr(scalar(`V'), `cut' + 1, .))
                local hastail = 1
            }
            mata: st_local("_bynone", strofreal(strtrim(st_local("head")) == ""))
            if `_bynone' {
                mata: _dash_say("err", "dash: by() must name at least one variable (got: ", st_local("value"), ")")
                exit 198
            }
        }
        // unab expands abbreviations and ranges.  When it refuses, tsrevar
        // (rclass: it leaves s() alone, where tsunab and fvunab clear it)
        // says whether the head is a valid time-series varlist -- one dash
        // cannot draw, so a token carrying an operator (L.price) is refused
        // as such.  tsrevar also passes `mpg if foreign', so the operator
        // itself is required before that refusal.  Otherwise the first
        // token that is not a variable is the one named -- twoway's own
        // "variable X not found" -- without quotes around it: a value that
        // ends in a double quote (by("foreign")) used to close the message's
        // compound quote early and garble it.
        local vv ""
        capture unab vv : `macval(head)'
        if _rc {
            capture tsrevar `macval(head)', list
            local ists = (_rc == 0)
            mata: st_local("badvar", strtrim(st_local("head")))
            local tsop = 0
            // Token by token, only when the head holds no double quote: a
            // quoted head is no varlist and is named whole, as it was
            // (by("foreign") names "foreign").  A token is tested through a
            // string scalar, never in quotes.
            mata: st_local("_hdq", strofreal(strpos(st_local("head"), char(34)) > 0))
            if !`_hdq' {
                tempname K
                foreach tok of local head {
                    capture confirm variable `macval(tok)'
                    if _rc {
                        local badvar `"`macval(tok)'"'
                        mata: st_strscalar(st_local("K"), st_local("tok"))
                        if regexm(scalar(`K'), "^[LlFfDdSs][LlFfDdSs0-9()/]*\.[A-Za-z_]") local tsop = 1
                        continue, break
                    }
                }
            }
            if `ists' & `tsop' {
                mata: _dash_say("err", "`prefix': `opt'() must name a variable, not a time-series expression (got: ", st_local("value"), ")")
                exit 198
            }
            mata: _dash_say("err", "`prefix': `opt'(): variable ", st_local("badvar"), " not found")
            exit 111
        }
        if "`kind'" == "var" & `: word count `vv'' > 1 {
            mata: _dash_say("err", "`prefix': `opt'() must name one variable (got: ", st_local("value"), ")")
            exit 198
        }
        local norm `"`vv'"'
        // A block, not a one-line if, whose command Stata expands again,
        // macval() or not: by(foreign, title("b\$G \`=exp'")) was stored
        // with $G's value and the =exp evaluated (measured 24sep2026;
        // test_json_escaping.cscript JSE-69).
        if `hastail' {
            local norm `"`vv', `macval(tail)'"'
        }
    }
    else if "`kind'" == "scheme" {
        // WP-17: a shipped translation or a theme alias, by name and
        // case-insensitively (a shipped name with or without the .scheme
        // extension), or a .scheme file in the working directory
        // named bare (mytheme) or with the extension (mytheme.scheme) --
        // the lookup dash_render.py's SchemeParser makes, so a name that
        // passes here resolves there.  A name carrying a path separator
        // or `..' is refused before any file is looked for; the renderer's
        // containment stays the second line of defence.  The value goes
        // through as written: the renderer lower-cases shipped names
        // itself, and a file name is the user's own.  Nothing outside the
        // working directory is looked for (third-party schemes in PLUS/s
        // included: WP-05, the letter directories are shared).
        _dash_shipped_schemes
        tempname L B
        scalar `L' = lower(scalar(`T'))
        // A shipped name written WITH the extension -- scheme(s2color.scheme),
        // in any case -- is the shipped scheme: the renderer's _resolve_path
        // reads that spelling from the package's schemes/ too, so no file
        // in the working directory is needed.  Measured 22sep2026: the
        // extension form was looked for as a working-directory file only,
        // and scheme(s2color.scheme) was refused although the renderer
        // would have drawn it.  The extension is dropped for the list test
        // only: a theme is not a file and takes no extension, and a name
        // that is not shipped still needs the file (below).  Read through
        // the string scalars T, L (lower case) and B (without .scheme).
        scalar `B' = scalar(`L')
        if substr(scalar(`L'), -7, .) == ".scheme" {
            scalar `B' = substr(scalar(`L'), 1, strlen(scalar(`L')) - 7)
        }
        local hit = 0
        foreach c of local _dash_schemes {
            if scalar(`B') == "`c'" local hit = 1
        }
        foreach c of local _dash_themes {
            if scalar(`L') == "`c'" local hit = 1
        }
        if !`hit' & scalar(`T') != "" {
            // A double quote is refused with the separators: a file name
            // put on confirm's command line must not end its quotes.
            local unsafe = strpos(scalar(`T'), "/") | ///
                           strpos(scalar(`T'), char(92)) | ///
                           strpos(scalar(`T'), "..") | ///
                           strpos(scalar(`T'), char(34))
            if !`unsafe' {
                if substr(scalar(`L'), -7, .) == ".scheme" {
                    capture confirm file `"`macval(tv)'"'
                }
                else {
                    capture confirm file `"`macval(tv)'.scheme"'
                }
                if !_rc local hit = 1
            }
        }
        if !`hit' local bad "a shipped scheme, a theme, or a .scheme file in the working directory"
    }
    else if "`kind'" == "format" {
        // 1. Character gate: one leading %, then only the characters a
        //    display format can contain -- no quote, blank, backtick, dollar
        //    or parenthesis -- and at most 60 of them.
        // 2. Stata's own judgement: `confirm numeric format' is rc 0 for
        //    %9.2f %12.0fc %-12.3e %9,2fc %tdCCYY-NN-DD %tcHH:MM:SS %21x
        //    %16H and rc 7 for %12s, bogus, 9.2f, %9.2, %9.2f_n, %c, %.
        // The token is then a single proven numeric %fmt, so `: display'
        // can stay the formatter (strofreal() returns "" for a bad format
        // without a word, so it is NOT a validator).
        local ok = 0
        if regexm(scalar(`V'), "^%[A-Za-z0-9_.,:!/+-]+$") & strlen(scalar(`V')) <= 60 {
            capture confirm numeric format `macval(value)'
            if !_rc local ok = 1
        }
        if !`ok' {
            mata: _dash_say("err", "`prefix': `opt'() must be a numeric display format such as %9.2f or %12.0fc (got: ", st_local("value"), ")")
            exit 198
        }
        // 3. confirm passes %21x, %16H and %16L, but the page cannot write
        //    a hexadecimal or IEEE byte dump (WP-28 S04): refused here, as
        //    dash_render.py's _dash_fmt_refusal refuses them.
        if regexm(scalar(`V'), "^%-?[0-9]*[xHL]$") {
            mata: _dash_say("err", "`prefix': `opt'() cannot be written by the dashboard: ", st_local("value"), " (hexadecimal %x and IEEE %H/%L formats are refused)")
            exit 198
        }
    }

    // Every refusal above and here echoes the value through _dash_say: the
    // value is read from Mata, never expanded into the display line, and
    // shown as written -- `jitter({bf:X})' printed a bold X (P20-02..06).
    // prefix, opt, bad and extra are this program's own words.
    if `"`bad'"' != "" {
        mata: _dash_say("err", "`prefix': `opt'() must be `bad' (got: ", st_local("value"), ")`extra'")
        exit 198
    }
    c_local _dash_vnorm `"`macval(norm)'"'
end

// ----------------------------------------------------------------
// _dash_axis_expand value
//
// WP-28 S14 (GAPS2 B1).  An axis-label option's value (xlabel(), ylabel(),
// their second-axis twins, xtick(), ytick(), xmtick(), ymtick(), xmlabel(),
// ymlabel()) with every bare numlist run replaced by Stata's own numlist
// expansion -- 1(2)10 becomes 1 3 5 7 9, 10 20 to 40 becomes 10 20 30 40 --
// while strings, sub-options and hostile runs (a backtick, $ or ') are kept
// exactly as written (_dash_axis_pieces).  numlist is always given
// max(2000), dash's own _MAX_AXIS_TICKS: measured 25sep2026, bare numlist
// has NO element cap (numlist "1/1800" is rc 0) and would try to expand
// 0(0.000001)1000000 whole, while max(2000) refuses it at once (r(123)).
// Never refuses: a run numlist cannot read -- a zero step, a bare word,
// more than 2,000 values -- is left as written, because twoway does not
// refuse those alike (xlabel(1(0)5) is rc 0, xlabel(2000 abc 4000) r(198))
// and numlist's rc cannot tell them apart; the renderer names what it
// cannot draw and bounds the rest.  Read by value (_dash_text_args).
// Returns r(norm).
// ----------------------------------------------------------------
program define _dash_axis_expand, rclass
    version 16.0
    mata: _dash_text_args(0, 0, 0)
    local value : copy local _dash_txt
    mata: _dash_axis_pieces(st_local("value"))
    local _n = `_ap_n'
    local out ""
    local tail ""
    forvalues j = 1/`_n' {
        local tag "`_ap_tag`j''"
        local txt : copy local _ap_txt`j'
        if "`tag'" == "T" {
            local tail : copy local txt
            continue
        }
        if "`tag'" == "B" {
            capture numlist `"`macval(txt)'"', max(2000)
            if !_rc local txt `"`r(numlist)'"'
        }
        if `"`macval(out)'"' == "" local out : copy local txt
        else                       local out `"`macval(out)' `macval(txt)'"'
    }
    return local norm `"`macval(out)'`macval(tail)'"'
end

// ----------------------------------------------------------------
// _dash_validate_opts ptype
//
// Runs every plot rule against this segment's s() values, once the plot
// type is known and bw() has been folded, and then every graph rule
// against the segment's s(g_<opt>) -- so `(scatter mpg weight,
// xsize(500)) , xsize(5)' is refused as twoway refuses it, although the
// after-comma value would have outranked the segment's.  A rule that
// names plot types applies only to them and displaces the untyped rule
// for the same option.  A normalised value is written back with sreturn
// local; nothing else in s() is touched, and s() is never cleared here.
// Defence in depth: every s() macro is snapshotted first, and one that
// comes back empty from a validation is put back, so a helper that
// clears s() can never again empty the segment's options in silence.
// ----------------------------------------------------------------
program define _dash_validate_opts, sclass
    version 16.0
    args ptype
    _dash_option_rules

    // The snapshot, the values and the restore are read and written by
    // value: s() holds the user's text, and a copy through compound quotes
    // expanded a macro in it again (test_json_escaping.cscript JSE-69).
    local _keys : s(macros)
    foreach _k of local _keys {
        mata: st_local("_snap_" + st_local("_k"), st_global("s(" + st_local("_k") + ")"))
    }

    // ---- The statistical flags (WP-18) ----
    // Each belongs to one plot family and is refused elsewhere as twoway
    // refuses it.  stdp, stdf and stdr name one band each: `twoway lfitci
    // mpg weight, stdf stdr' is r(198) "may not combine stdf stdr".
    // discrete decides the bins itself: `twoway histogram rep78, discrete
    // bin(3)' is r(198) "options discrete and bins() may not be combined",
    // while width() and start() combine with it (rc 0).  All measured
    // 23sep2026 (scratchpad/wp18/A/wording.log).
    foreach tok of local _dash_rules_flags {
        local at    = strpos("`tok'", "@")
        local names = substr("`tok'", 1, `at' - 1)
        local types = substr("`tok'", `at' + 1, .)
        local names : subinstr local names "|" " ", all
        local types : subinstr local types "|" " ", all
        if `: list ptype in types' continue
        foreach f of local names {
            if `"`s(`f')'"' != "" {
                display as error "option `f' not allowed"
                exit 198
            }
        }
    }
    local _std ""
    foreach f in stdp stdf stdr {
        if `"`s(`f')'"' != "" local _std "`_std' `f'"
    }
    if `: word count `_std'' > 1 {
        display as error "may not combine`_std'"
        exit 198
    }
    // stdf and stdr need regress's residual variance, which predict will
    // not give after weighted or robust estimation (regres_p.ado): twoway
    // lfitci/qfitci with an aweight say "not possible with weighted data",
    // r(135); with a pweight "option stdf not allowed after robust
    // estimation", r(198).  An fweight is replication and is fine; stdp is
    // fine under all three.  Measured 23sep2026.  s(weight) is set before
    // this runs, and only on a type that honours weights.
    local _std = strtrim("`_std'")
    // fpfitci draws the stdp band and no other: twoway_fpfitci_parse.class
    // runs lfitci's parser first ("may not combine", above) and then
    // refuses stdf and stdr as "stdf not allowed", r(198) (measured
    // 23sep2026).  stdp alone is its default, accepted.
    if "`ptype'" == "fpfitci" & ("`_std'" == "stdf" | "`_std'" == "stdr") {
        display as error "`_std' not allowed"
        exit 198
    }
    if "`_std'" == "stdf" | "`_std'" == "stdr" {
        if `"`s(weight)'"' == "aweight" {
            display as error "not possible with weighted data"
            exit 135
        }
        if `"`s(weight)'"' == "pweight" {
            display as error "option `_std' not allowed after robust estimation"
            exit 198
        }
    }
    mata: st_local("_dbin", strofreal(st_global("s(discrete)") != "" & st_global("s(bin)") != ""))
    if `_dbin' {
        display as error "options discrete and bins() may not be combined"
        exit 198
    }
    // colorcuts() and colorlevels() (GAPS2 X2, colorvar_options.sthlp:95-98)
    // "may not be combined": twoway refuses the pair with these words, r(198)
    // (measured 26sep2026, test/fixtures/colorvar_truth.json cuts_and_levels).
    mata: st_local("_cvcl", strofreal(st_global("s(colorcuts)") != "" & st_global("s(colorlevels)") != ""))
    if `_cvcl' {
        display as error "may not combine options colorcuts() and colorlevels()"
        exit 198
    }

    // Options that have a type-specific rule for THIS type: their untyped
    // rule is skipped below, so the specific one wins.
    local typed ""
    foreach tok of local _dash_rules_plot {
        local at = strpos("`tok'", "@")
        if `at' {
            local types = substr("`tok'", `at' + 1, .)
            local types : subinstr local types "|" " ", all
            local o = substr("`tok'", 1, strpos("`tok'", "=") - 1)
            if `: list ptype in types' local typed "`typed' `o'"
        }
    }
    foreach tok of local _dash_rules_plot {
        local body "`tok'"
        local at = strpos("`tok'", "@")
        if `at' {
            local body  = substr("`tok'", 1, `at' - 1)
            local types = substr("`tok'", `at' + 1, .)
            local types : subinstr local types "|" " ", all
            if !`: list ptype in types' continue
        }
        local eq   = strpos("`body'", "=")
        local o    = substr("`body'", 1, `eq' - 1)
        local spec = substr("`body'", `eq' + 1, .)
        if !`at' & `: list o in typed' continue
        mata: st_local("v", st_global("s(" + st_local("o") + ")"))
        // The tests read the values by value: in the quotes they were
        // compared in, a title holding "' beside an option with a rule --
        // title("'90s cars") msize(small) -- ended them
        // (test_json_escaping.cscript JSE-42).  The restore is a copy: a
        // one-line if expands its command again, macval() or not.
        if !`: length local v' continue
        _dash_validate_value "dash" "`o'" "`spec'" `"`macval(v)'"' "`ptype'"
        foreach _k of local _keys {
            if !`: length local _snap_`_k'' continue
            mata: st_local("_lost", strofreal(st_global("s(" + st_local("_k") + ")") == ""))
            if `_lost' sreturn local `_k' : copy local _snap_`_k'
        }
        mata: st_local("_chg", strofreal(st_local("_dash_vnorm") != st_local("v")))
        if `_chg' {
            sreturn local `o' `"`macval(_dash_vnorm)'"'
        }
    }

    // The graph rules, against what this segment wrote in parentheses.
    // _dash_plot validates the after-comma winners again; a value refused
    // here never gets that far.
    foreach tok of local _dash_rules_graph {
        local eq   = strpos("`tok'", "=")
        local o    = substr("`tok'", 1, `eq' - 1)
        local spec = substr("`tok'", `eq' + 1, .)
        mata: st_local("v", st_global("s(g_" + st_local("o") + ")"))
        if !`: length local v' continue
        _dash_validate_value "dash" "`o'" "`spec'" `"`macval(v)'"' ""
        foreach _k of local _keys {
            if !`: length local _snap_`_k'' continue
            mata: st_local("_lost", strofreal(st_global("s(" + st_local("_k") + ")") == ""))
            if `_lost' sreturn local `_k' : copy local _snap_`_k'
        }
        mata: st_local("_chg", strofreal(st_local("_dash_vnorm") != st_local("v")))
        if `_chg' {
            sreturn local g_`o' `"`macval(_dash_vnorm)'"'
        }
    }

    // legend(top), (bottom), (left) and (right) inside this segment:
    // refused as twoway refuses them, even where an after-comma legend()
    // outranks this one (WP-23).  _dash_plot checks the value it writes.
    mata: st_local("_leg", st_global("s(g_legend)"))
    if `: length local _leg' {
        _dash_check_legend `"`macval(_leg)'"'
    }
end
// END option-validation table (WP-15)

// BEGIN resource limits (WP-19)
// ================================================================
// Resource limits.
//
// ROADMAP WP-19: no user input may produce unbounded output or memory use
// (BR-19.1), and every limit names the setting that would raise it
// (BR-19.2).  Measured on the development machine, a standalone dashboard
// embedding 2,000,000 values is 47.6 MB of HTML and took 1.0 GB of RSS in
// the renderer; 4,000,000 is 94.9 MB and 2.1 GB; and Chrome cannot hold a
// string longer than about 512 MB, which is roughly 20,000,000 values.
//
// This is the one table of limits.  Each row is key=default,ceiling.  A
// session raises or lowers a limit with global dash_max_<key>: a whole
// number written in digits only, at most nine of them, from 1 to the
// ceiling.  dash.ado enforces four itself -- cells (values embedded:
// observations x variables exported), bytes (the bytes of text in the
// string values exported), graphs (graphs and KPI cards in the
// registry) and plots (plot entries in one graph, one per y variable) --
// and hands every limit the session has set to the renderer as
// build_options.limits, under these keys, for the four it enforces:
// filter_options, by_groups, tabs and filters.
// ================================================================
program define _dash_limit_table
    version 16.0
    local rows ///
        cells=5000000,20000000 ///
        bytes=50000000,500000000 ///
        graphs=100,1000 ///
        plots=100,1000 ///
        filter_options=1000,100000 ///
        by_groups=100,1000 ///
        tabs=50,500 ///
        filters=20,200
    c_local _dash_limit_rows "`rows'"
end

// ----------------------------------------------------------------
// _dash_count_fmt <out_macro> <exp>  -- a count for a message: 1,234,567
//
// %30.0fc rather than %12.0fc: the two give the same text for every
// number below 10^12, which covers every limit, but %12.0fc turns a
// thirteen-digit count into 1.23457e+12 (measured), and observations x
// variables can reach that.
// ----------------------------------------------------------------
program define _dash_count_fmt
    version 16.0
    gettoken out 0 : 0
    local s : display %30.0fc `0'
    local s = strtrim("`s'")
    c_local `out' "`s'"
end

// ----------------------------------------------------------------
// _dash_limit, name(<key>)  -- one limit, with its global validated
//
// r(value)    the effective limit: $dash_max_<key> when set, else the
//             default
// r(default)  r(ceiling)  from _dash_limit_table
// r(global)   the global's name, dash_max_<key>
//
// An unset or empty global means the default.  Anything else must be a
// whole number written in digits only, at most nine of them, from 1 to
// the ceiling, or it is refused with r(198), naming the global and the
// range and echoing the value reduced to safe characters.
//
// The global is read through st_global(), so its contents are a value and
// are never parsed as Stata code, and it is tested with extended macro
// functions, which work on a macro's value without expanding it.  It is
// expanded only once it is known to be nine digits at most.  No regular
// expression decides it: under a caller's version 16 or 17 Stata's old
// engine does not know bounded repetition, so {1,9} silently fails, and
// under StataNow's engine `$' also matches before a trailing newline --
// measured, regexm("12" + char(10), "^[0-9]+$") is 1.
// ----------------------------------------------------------------
program define _dash_limit, rclass
    version 16.0
    syntax , NAME(string)

    _dash_limit_table
    local def  ""
    local ceil ""
    foreach _row of local _dash_limit_rows {
        local _eq  = strpos("`_row'", "=")
        local _key = substr("`_row'", 1, `_eq' - 1)
        if `"`_key'"' != `"`macval(name)'"' continue
        local _vals = substr("`_row'", `_eq' + 1, .)
        local _cm   = strpos("`_vals'", ",")
        local def   = substr("`_vals'", 1, `_cm' - 1)
        local ceil  = substr("`_vals'", `_cm' + 1, .)
    }
    if "`def'" == "" {
        display as error "dash: internal error: _dash_limit was asked for a limit that does not exist."
        exit 198
    }

    local gname "dash_max_`name'"
    mata: st_local("_raw", st_global(st_local("gname")))
    local _len : strlen local _raw
    local val = `def'
    if `_len' > 0 {
        // Digits only, and nine at most: with every digit taken out,
        // nothing may be left.
        local _ok = (`_len' <= 9)
        if `_ok' {
            local _rest : copy local _raw
            forvalues _d = 0/9 {
                local _rest : subinstr local _rest "`_d'" "", all
            }
            local _restlen : strlen local _rest
            local _ok = (`_restlen' == 0)
        }
        if `_ok' {
            local val = real("`_raw'")
            local _ok = (`val' >= 1 & `val' <= `ceil')
        }
        if !`_ok' {
            // The echo: the first 20 bytes, each outside [A-Za-z0-9_.-]
            // shown as ?.  Read byte by byte from Mata, so a quote, a
            // backtick, a brace or a byte that is not UTF-8 never reaches
            // the display line as anything but a ?.
            local _safe ""
            local _nb = min(`_len', 20)
            forvalues _i = 1/`_nb' {
                mata: st_local("_b", strofreal(ascii(substr(st_local("_raw"), `_i', 1))))
                if inrange(`_b', 48, 57) | inrange(`_b', 65, 90) | ///
                   inrange(`_b', 97, 122) | inlist(`_b', 45, 46, 95) {
                    local _safe "`_safe'`=char(`_b')'"
                }
                else local _safe "`_safe'?"
            }
            local _cut ""
            if `_len' > 20 {
                _dash_count_fmt _len_s `_len'
                local _cut ", the first 20 of `_len_s' characters"
            }
            _dash_count_fmt _ceil_s `ceil'
            _dash_count_fmt _def_s  `def'
            display as error "dash: global `gname' must be a whole number from 1 to `_ceil_s', written in digits only (got '`_safe''`_cut')."
            display as error "      Drop it (macro drop `gname') to use the default, `_def_s'."
            exit 198
        }
    }

    return scalar value   = `val'
    return scalar default = `def'
    return scalar ceiling = `ceil'
    return local  global    "`gname'"
end

// ----------------------------------------------------------------
// _dash_limits_json  -- the limits this session has set, as JSON
//
// r(json) is the object written as build_options.limits: one key for each
// dash_max_<key> global that is set, in table order, validated through
// _dash_limit and written as a plain integer -- {"by_groups":7} -- or {}
// when none is set.  A limit the session has not set is left out, so the
// renderer keeps its own default for it.
// ----------------------------------------------------------------
program define _dash_limits_json, rclass
    version 16.0
    _dash_limit_table
    local json ""
    local n = 0
    foreach _row of local _dash_limit_rows {
        local _key = substr("`_row'", 1, strpos("`_row'", "=") - 1)
        local _set : strlen global dash_max_`_key'
        if `_set' == 0 continue
        _dash_limit, name(`_key')
        local _v : display %12.0f r(value)
        local _v = strtrim("`_v'")
        if `n' > 0 local json `"`json',"'
        local json `"`json'"`_key'":`_v'"'
        local ++n
    }
    return local json `"{`json'}"'
end

// ----------------------------------------------------------------
// _dash_graph_cap <already>  -- the registry limit
//
// Both registrars call this before they set or retire any global.  The
// graphs limit is read, and its global validated, on every registration;
// the cap itself applies only to a name the registry does not hold yet
// (<already> 0).  A name already registered is a replace and never counts.
// ----------------------------------------------------------------
program define _dash_graph_cap
    version 16.0
    args already
    _dash_limit, name(graphs)
    local lim  = r(value)
    local ceil = r(ceiling)
    if `already' == 1 exit
    local n : word count ${dash_graph_registry}
    if `n' < `lim' exit

    _dash_count_fmt _n_s    `n'
    _dash_count_fmt _lim_s  `lim'
    _dash_count_fmt _ceil_s `ceil'
    // A registry can hold more than the limit when the limit was lowered
    // after the items were registered; the message does not then claim
    // the count is the most one dashboard draws.
    if `n' == `lim' local _why "the most one dashboard draws"
    else            local _why "more than the `_lim_s' one dashboard draws"
    display as error "dash: the registry already holds `_n_s' graphs and KPI cards, `_why'."
    display as error "      Run dash clear, reuse a name with name(<name>, replace), or set global dash_max_graphs to a higher value (at most `_ceil_s')."
    exit 134
end

// ----------------------------------------------------------------
// _dash_plot_cap_refuse <lim> <ceil> [<n>]  -- the plot-limit refusal
//
// <n> is the graph's plot count when it is known.  It is left off when
// only a running total is known to have passed the limit and segments are
// still to come.
// ----------------------------------------------------------------
program define _dash_plot_cap_refuse
    version 16.0
    args lim ceil n
    _dash_count_fmt _lim_s  `lim'
    _dash_count_fmt _ceil_s `ceil'
    if "`n'" == "" {
        local _has "more than `_lim_s' plots (each y variable is one), the most one graph draws"
    }
    else {
        _dash_count_fmt _n_s `n'
        local _has "`_n_s' plots (each y variable is one), more than the `_lim_s' one graph draws"
    }
    display as error "dash: this graph has `_has'."
    display as error "      Split it into several graphs, or set global dash_max_plots to a higher value (at most `_ceil_s')."
    exit 134
end

// ----------------------------------------------------------------
// _dash_cell_cap <nvars> [<nobs>] [<extra>] [<served>]  -- the
//                                     embedded-data limit, before the
//                                     export
//
// The export (_dash_write_data) writes every observation of every
// variable it is given; the
// renderer applies if/in itself, so if/in reduce nothing here and are not
// offered as a remedy.  <nobs> is the observations exported, _N unless the
// caller exports fewer (the one-row placeholder a graph of literal values
// sends).  Both callers run this before the file is written, so a
// refusal leaves the data in memory exactly as it was.
//
// <extra> (GAPS2 G3) is the drawn output of computed-only graphs
// (histogram, kdensity, a fit or a smoother) that no filter, link(), csv
// or hover() reaches: those graphs' rows are never in <nvars>, so a
// saved page can hold more observations than the cells limit alone would
// allow.  <nvars> of 0 means every graph is computed-only and untouched
// -- nothing row-shaped is embedded at all.  <served> of 1 says every
// observation of every variable is embedded regardless (the served
// route always calls this with the full count and extra empty): a third
// line then says so.  The two-line message is byte for byte what it was
// before <extra> and <served> existed.
// ----------------------------------------------------------------
program define _dash_cell_cap
    version 16.0
    args nvars nobs extra served
    if "`nobs'"  == "" local nobs  = _N
    if "`extra'" == "" local extra = 0
    _dash_limit, name(cells)
    local lim  = r(value)
    local ceil = r(ceiling)
    local total = `nobs' * `nvars' + `extra'
    if `total' <= `lim' exit

    _dash_count_fmt _cells_s `total'
    _dash_count_fmt _lim_s   `lim'
    _dash_count_fmt _ceil_s  `ceil'
    if `nvars' == 0 {
        local _shape "the drawn output of its computed layers"
    }
    else {
        _dash_count_fmt _obs_s   `nobs'
        _dash_count_fmt _vars_s  `nvars'
        local _obs_w  = cond(`nobs' == 1, "observation", "observations")
        local _vars_w = cond(`nvars' == 1, "variable", "variables")
        if `extra' > 0 {
            _dash_count_fmt _extra_s `extra'
            local _shape "`_obs_s' `_obs_w' x `_vars_s' `_vars_w', and `_extra_s' values of computed layers"
        }
        else {
            local _shape "`_obs_s' `_obs_w' x `_vars_s' `_vars_w'"
        }
    }
    display as error "dash: this dashboard would embed `_cells_s' values (`_shape'), more than the `_lim_s' dash embeds."
    display as error "      Reduce the data in memory first (keep, drop, sample or collapse, inside preserve/restore), or set global dash_max_cells to a higher value (at most `_ceil_s')."
    if "`served'" == "1" {
        display as error "      A served app embeds every observation of every variable it uses."
    }
    exit 134
end

// ----------------------------------------------------------------
// _dash_byte_cap <varlist>  -- the bytes of text exported, before the
//                              export
//
// The cells limit counts values, not bytes, and the export writes a strL
// in full (_dash_write_data, 24sep2026): 60 observations of a
// 1,000,000-byte strL were 60 values and a 60 MB page.  This holds the
// bytes of text in the string values of <varlist> -- every observation, as
// Stata stores them, before JSON escaping -- to $dash_max_bytes.  Numbers
// are the cells limit's.  A name that is not a variable is skipped (the
// export reports it), and a variable named twice is counted once, as the
// export writes it once.
//
// Nothing is counted when it cannot matter: a str# variable holds at most
// its width in bytes, so when every string variable is a str# and width x
// _N summed is within the limit the data are not read.  Otherwise the
// lengths are summed in Mata, a million observations at a time, so no
// variable is made and no more than that is held at once; the sum stops
// once it is over the limit.  Both callers run this before the file is
// written, so a refusal leaves the data in memory as it was.
// ----------------------------------------------------------------
program define _dash_byte_cap
    version 16.0
    _dash_limit, name(bytes)
    local lim  = r(value)
    local ceil = r(ceiling)
    if _N == 0 exit
    local names ""
    foreach v of local 0 {
        capture unab u : `v', max(1)
        if _rc == 0 local names `names' `u'
    }
    local names : list uniq names
    local strs ""
    tempname bound tot
    scalar `bound' = 0
    foreach v of local names {
        capture confirm string variable `v'
        if _rc continue
        local strs `strs' `v'
        local t : type `v'
        if "`t'" == "strL" scalar `bound' = .
        else scalar `bound' = `bound' + real(substr("`t'", 4, .)) * _N
    }
    if "`strs'" == "" exit
    if `bound' <= `lim' exit
    scalar `tot' = 0
    local n = _N
    foreach v of local strs {
        forvalues a = 1(1000000)`n' {
            local b = min(`a' + 999999, `n')
            mata: st_numscalar(st_local("tot"), st_numscalar(st_local("tot")) + ///
                sum(strlen(st_sdata((`a', `b'), st_local("v")))))
            if `tot' > `lim' continue, break
        }
        if `tot' > `lim' continue, break
    }
    if `tot' <= `lim' exit

    // Over: the whole count, for the message.  Only a refusal pays for
    // the variables the running total did not reach.
    scalar `tot' = 0
    foreach v of local strs {
        forvalues a = 1(1000000)`n' {
            local b = min(`a' + 999999, `n')
            mata: st_numscalar(st_local("tot"), st_numscalar(st_local("tot")) + ///
                sum(strlen(st_sdata((`a', `b'), st_local("v")))))
        }
    }
    local nstr : word count `strs'
    _dash_count_fmt _bytes_s `tot'
    _dash_count_fmt _nstr_s  `nstr'
    _dash_count_fmt _lim_s   `lim'
    _dash_count_fmt _ceil_s  `ceil'
    local _str_w = cond(`nstr' == 1, "variable", "variables")
    display as error "dash: this dashboard would embed `_bytes_s' bytes of text (in `_nstr_s' string `_str_w'), more than the `_lim_s' dash embeds."
    display as error "      Reduce the data in memory first (keep, drop, sample or collapse, inside preserve/restore), or set global dash_max_bytes to a higher value (at most `_ceil_s')."
    exit 134
end
// END resource limits (WP-19)

// ================================================================
// _dash_plot_opts_to_json
//
// Emit the "options" JSON object fragment from s() values.
// Sets c_local `out_macro' to the JSON string.
// ================================================================
program define _dash_plot_opts_to_json, rclass
    version 16.0
    args out_macro

    local parts ""
    local nparts = 0

    // Helper: append a k:v JSON pair if value non-empty.
    // weight and wexp (WP-18) are not options: _dash_process_segment puts
    // them in s() for a weighted segment on a type that honours weights,
    // and an unweighted segment writes neither key, so its "options" text
    // is byte-identical to what it was.  clcolor, clpattern and clwidth
    // (WP-22) are non-empty only on the types _dash_fold_cl keeps them for.
    foreach key in mcolor msymbol msize msangle mfcolor mlcolor mlabel mlabcolor ///
                   mlabsize mlabposition mlabgap mlabwidth malpha marker lcolor ///
                   lwidth lpattern lalpha fcolor fintensity falpha barwidth base ///
                   blcolor bfcolor jitter jseed yaxis xaxis colorvar colpalette ///
                   colordiscrete coloruseplegend colornlevels colorcuts colormissing ///
                   colorlevels colorvarminmax ///
                   bwidth degree pstyle cmissing recast connect bin width start ///
                   percent frequency density fraction kernel n level bands at ciopts ///
                   lineopts fitopts color mlwidth mstyle lstyle mlstyle mlpattern ///
                   blabel horizontal vertical sort range colorlist jitterseed ///
                   discrete stdp stdf stdr mean noweight adjust logit ///
                   clcolor clpattern clwidth mlabangle mlabformat ///
                   acolor alcolor alwidth alpattern ///
                   weight wexp {
        // Read by value and measured, never copied or compared in quotes: a
        // copy through them expanded a macro in the value again --
        // mcolor("\$G") was stored as $G's value (measured 24sep2026;
        // test_json_escaping.cscript JSE-69).
        mata: st_local("val", st_global("s(" + st_local("key") + ")"))
        if `: length local val' {
            _dash_json_str `"`macval(val)'"' _jv
            if `nparts' > 0 local parts `"`parts',"'
            local parts `"`parts'"`key'":"`_jv'""'
            local nparts = `nparts' + 1
        }
    }

    c_local `out_macro' `"{`parts'}"'
end


// ================================================================
// _dash_seg_weight_s  -- put a segment's weight into s() (WP-18)
//
// _dash_process_segment is rclass, so it cannot sreturn; this sclass
// helper writes s(weight) and s(wexp) beside the parsed options, and
// the rest of s() survives the call as it survives _dash_fold_bw.
// ================================================================
program define _dash_seg_weight_s, sclass
    version 16.0
    args wtype wvar
    sreturn local weight `"`wtype'"'
    sreturn local wexp   `"`wvar'"'
end

// ================================================================
// _dash_plottype_families  -- the plot-type families, each named once
//
// _dash_process_segment routes a plot type to its varlist parser and its
// JSON keys by family.  It did so with string inlist() tests, and the
// range test was ptype and nine literals -- Stata's limit for a string
// inlist(): measured 23sep2026, ptype and nine literals is rc 0, ptype and
// ten is r(130) "expression too long" -- so a tenth range type could not
// have been added.  Each family is a word list here, tested with
// `: list ptype in <family>', which has no such limit (WP-22 TR-22.4).
// The four routing families are the renderer's _DASH_UNIVARIATE_TYPES,
// _DASH_RANGE_TYPES, _DASH_PC_TYPES and _DASH_LITERAL_TYPES;
// test/test_plottype_families.py holds the two sides together.
//
//   _pt_univar   one variable                       histogram kdensity
//   _pt_range    y1 y2 [x]                          the range types
//   _pt_pc       y1 x1 y2 x2                        the paired-coordinate types
//   _pt_literal  literal values or an expression    scatteri pci pcarrowi function
//   _pt_imm      immediate values, read as twoway   scatteri pci pcarrowi
//                reads them (dash_parse.mata 2c)
//   _pt_ts       x from tsset when it is not given  tsline tsrline
// ================================================================
program define _dash_plottype_families
    version 16.0
    c_local _pt_univar  "histogram kdensity"
    c_local _pt_range   "rarea rbar rspike rcap rline rconnected rcapsym rscatter tsrline"
    c_local _pt_pc      "pcspike pcarrow pcbarrow pcscatter pccapsym"
    c_local _pt_literal "scatteri pci pcarrowi function"
    c_local _pt_imm     "scatteri pci pcarrowi"
    c_local _pt_ts      "tsline tsrline"
    // The fits and smoothers: one y and one x, as twoway takes them.
    // twoway names the variables when it refuses more for all but the
    // three in _pt_onefit_bare (test_parser.cscript P1A-79).
    c_local _pt_onefit  "lfit qfit lfitci qfitci fpfit fpfitci mspline mband lowess lpoly lpolyci"
    c_local _pt_onefit_bare "lowess lpoly lpolyci"
end

// ================================================================
// _dash_by_parts <string scalar>
//
// A by() value, validated (its variables written out), read by value from
// the string scalar: c_local _by_vars gets the variables before the first
// comma outside parentheses, and _by_miss 1 when the sub-options give
// missing -- twoway's MISSing, abbreviated to miss at least
// (bygraph_g.class) -- 0 otherwise, and _by_total 1 when they give total
// (TOTal: tot at least).  A parenthesised sub-option's text,
// title("a miss"), is not read for either.  The value is never put inside
// quotes or on a command line.
// ================================================================
program define _dash_by_parts
    version 16.0
    args V
    local len = strlen(scalar(`V'))
    local depth = 0
    local cut = 0
    // As the byvarlist validator reads it: the text is compared through
    // the scalar, never through a macro.
    forvalues i = 1/`len' {
        if substr(scalar(`V'), `i', 1) == "(" {
            local depth = `depth' + 1
        }
        else if substr(scalar(`V'), `i', 1) == ")" {
            local depth = `depth' - 1
        }
        else if substr(scalar(`V'), `i', 1) == "," & `depth' == 0 {
            local cut = `i'
            continue, break
        }
    }
    if `cut' > 0 {
        mata: st_local("_bv", strtrim(substr(st_strscalar(st_local("V")), 1, `cut' - 1)))
        mata: st_local("_bt", substr(st_strscalar(st_local("V")), `cut' + 1, .))
    }
    else {
        mata: st_local("_bv", strtrim(st_strscalar(st_local("V"))))
        local _bt ""
    }
    // Parenthesised text is removed, innermost first, before the words are
    // read; each pass removes one pair, so the loop ends.
    mata: _dash_bt = st_local("_bt"); while (ustrregexm(_dash_bt, "\([^()]*\)")) _dash_bt = ustrregexrf(_dash_bt, "\([^()]*\)", " "); st_local("_bm", strofreal(ustrregexm(_dash_bt, "(^|[ ,])miss(i|in|ing)?($|[ ,])"))); st_local("_btot", strofreal(ustrregexm(_dash_bt, "(^|[ ,])tot(a|al)?($|[ ,])")))
    mata: mata drop _dash_bt
    c_local _by_vars `_bv'
    c_local _by_miss `_bm'
    c_local _by_total `_btot'
end

// ================================================================
// _dash_qual_mark <target> <value> <ifscalar> <inscalar> [varlist]
//
// replace target = value for the rows the if and the in select -- every
// row when both are empty -- evaluated with the data sorted, stably, on
// varlist when one is given: the order twoway evaluates a by() graph's
// qualifiers in (bygraph_g.class, `bysort varlist (sortedby obsnum)';
// test_qualifier_in_stata.cscript QS-16..).  The if and the in are read
// by value from the two string scalars, and the if is put inside the
// parentheses -syntax- proved it cannot leave, never expanded again.
// target and value are variable names (value may be 1), and varlist the
// by() variables _dash_by_parts read from the validated by().
// sortpreserve gives the data their order back; a sort marks nothing
// changed.
// ================================================================
program define _dash_qual_mark, sortpreserve
    version 16.0
    gettoken target 0 : 0
    gettoken value 0 : 0
    gettoken sif 0 : 0
    gettoken sin order : 0
    local order : list retokenize order
    mata: st_local("_qx", st_strscalar(st_local("sif")))
    mata: st_local("_qn", st_strscalar(st_local("sin")))
    if "`order'" != "" {
        tempvar _obs
        quietly generate double `_obs' = _n
        sort `order' `_obs'
    }
    local q ""
    // Blocks, never a one-line if: Stata expands a one-line if's command
    // again (P1A-83).
    if `: length local _qx' {
        local q `"if (`macval(_qx)')"'
    }
    if `: length local _qn' {
        local q `"`macval(q)' in `macval(_qn)'"'
    }
    quietly replace `target' = `value' `macval(q)'
end

// ================================================================
// _dash_by_panels varlist, panel(varname) [missing total check(varlist)
//                 rules(string)]
//
// The panels of a by(varlist) graph, as twoway draws them (bygraph_g.class
// RunGraph): the groups of the by() variables -- missing values dropped
// unless missing is given -- holding a row where panel() is 1, in sort
// order.  check() names, plot by plot, a 0/1 variable marking each plot's
// sample, and rules() its rule, one word each: R, the command stops when
// the sample has no row in a panel; D0, the panel is left out when it has
// one row or none; D1 and N1, when it has exactly one (N1: lfit and lfitci,
// which print regress's note as they stop).  In each panel the first plot
// whose rule applies decides.  total adds by()'s Total panel, after the
// groups, over the rows of every group and decided as a group is (it
// exists when a group does).  Returns r(n), the rows in panels (0: no
// panel); r(refuse), the place in check() of the plot that stops the
// command in the first panel where one does, or 0; r(kept), the panels
// drawn; r(d1note), 1 when an N1 plot left a panel out.  sortpreserve: the
// data keep their order.  tpanel() and tcheck() are the Total panel's
// panel() and check(), evaluated in the data's order where the groups'
// are evaluated sorted on the by() variables, as twoway evaluates each
// (_dash_qual_mark); the Total panel is drawn when tpanel() selects a row.
// ================================================================
program define _dash_by_panels, rclass sortpreserve
    version 16.0
    syntax varlist(min=1), PANEL(varname) [MISSing TOTal CHECK(varlist) ///
        RULES(string) TPANEL(varname) TCHECK(varlist)]
    tempvar p tp anyp grp dec deck cnt first
    quietly gen byte `p' = `panel' == 1
    if "`missing'" == "" markout `p' `varlist', strok
    // The Total panel's rows and samples: tpanel() and tcheck(), which
    // the caller evaluated in the data's order as twoway's Total panel
    // evaluates them (bygraph_g.class: bysort one (sortedby obsnum)), or
    // panel() and check().
    if "`tpanel'" == "" local tpanel `panel'
    if "`tcheck'" == "" local tcheck `check'
    quietly gen byte `tp' = 0
    if "`total'" != "" {
        quietly replace `tp' = `tpanel' == 1
        if "`missing'" == "" markout `tp' `varlist', strok
    }
    quietly count if `tp'
    local ntp = r(N)
    quietly count if `p' | `tp'
    return scalar n = r(N)
    return scalar refuse = 0
    return scalar kept = 0
    return scalar d1note = 0
    if r(N) == 0 exit
    quietly bysort `varlist': egen byte `anyp' = max(`p')
    quietly by `varlist': gen long `grp' = (_n == 1) & `anyp'
    quietly replace `grp' = sum(`grp')
    quietly gen byte `dec' = 0
    quietly gen int `deck' = 0
    local k = 0
    foreach c of local check {
        local ++k
        local rule : word `k' of `rules'
        capture drop `cnt'
        quietly by `varlist': egen double `cnt' = total(`c' == 1)
        if "`rule'" == "R"       local ev "2 * (`cnt' == 0)"
        else if "`rule'" == "D0" local ev "(`cnt' <= 1)"
        else if inlist("`rule'", "D1", "N1") local ev "(`cnt' == 1)"
        else continue
        quietly replace `deck' = `k' if `dec' == 0 & `ev' > 0
        quietly replace `dec' = `ev' if `dec' == 0
    }
    // total: the Total panel, drawn after the groups (bygraph_g.class),
    // holds the rows of every group -- `p', whose by() values are missing
    // only under missing -- and is decided as a group is: tdec and tdeck
    // are its `dec' and `deck'.  Each plot's sample lies inside the rows
    // that make the panels, so it is counted over `p'.
    local tdec 0
    local tdeck 0
    // A Total panel over no row is not drawn: twoway's RunGraph counts the
    // graph's qualifier over it and leaves it out.
    if "`total'" != "" & `ntp' == 0 local tdec 1
    if "`total'" != "" & `ntp' > 0 {
        local k = 0
        foreach c of local tcheck {
            local ++k
            local rule : word `k' of `rules'
            quietly count if `c' == 1 & `tp'
            local tc = r(N)
            if "`rule'" == "R"       local ev = 2 * (`tc' == 0)
            else if "`rule'" == "D0" local ev = (`tc' <= 1)
            else if inlist("`rule'", "D1", "N1") local ev = (`tc' == 1)
            else continue
            if `ev' > 0 {
                local tdec `ev'
                local tdeck `k'
                continue, break
            }
        }
    }
    // The first panel, in by() order, that stops the command; the Total
    // panel comes last.
    quietly summarize `grp' if `anyp' & `dec' == 2, meanonly
    if r(N) > 0 {
        local g = r(min)
        quietly summarize `deck' if `anyp' & `grp' == `g', meanonly
        return scalar refuse = r(min)
        exit
    }
    if `tdec' == 2 {
        return scalar refuse = `tdeck'
        exit
    }
    quietly by `varlist': gen byte `first' = (_n == 1) & `anyp'
    quietly count if `first' & `dec' != 1
    return scalar kept = r(N) + ("`total'" != "" & `tdec' != 1)
    local k = 0
    foreach c of local check {
        local ++k
        if "`: word `k' of `rules''" != "N1" continue
        quietly count if `first' & `dec' == 1 & `deck' == `k'
        if r(N) > 0 | (`tdec' == 1 & `tdeck' == `k') return scalar d1note = 1
    }
end

// ================================================================
// _dash_process_segment
//
// Parse one plot segment (full text including plot type name),
// and build its JSON fragment.
//
// Usage:  _dash_process_segment `"`seg_text'"' `plottype_out' `json_out' [nsegs]
//
// nsegs is the number of segments in the graph (default 1); it only
// decides whether a plot-limit refusal can state the graph's plot count.
//
// After the call:
//   - c_local `plottype_out' = expanded plot type name
//   - c_local `json_out'     = JSON fragment for this plot
//   - c_local _seg_nplots_out = number of plot objects in that fragment
//   - Caller's g_* locals are updated if graph-level opts were found.
// ================================================================
program define _dash_process_segment, rclass
    version 16.0
    // The segment is read by value (_dash_text_args in dash_parse.mata): its
    // text, less the quotes around it, then the two output names and the
    // optional count.  -args- read it inside the compound quotes it was
    // handed in, so a segment holding "' -- title("'90s cars"), if make ==
    // "' or 1 or '" -- was cut at the quote and its next words became the
    // output names: r(100) ") required" and r(198) (measured 24sep2026;
    // test_json_escaping.cscript JSE-42, JSE-44).  The segment's text is
    // then never put inside quotes in an expression or a Mata line, where
    // title(`"'90s cars"') stopped with r(133) (JSE-42): it is measured with
    // `: length local' and cut in Mata.
    mata: _dash_text_args(0, 2, 1)
    local seg_text : copy local _dash_txt
    local plottype_out `_dash_a1'
    local json_out     `_dash_a2'
    local nsegs        `_dash_a3'
    if "`nsegs'" == "" local nsegs 1

    // ---- extract plot type (first word) ----
    // The token is read from Mata by value: expanded inside the quotes of
    // the mata: line, a double quote in it ended the string.  A token that
    // is no plot type is echoed through _dash_say, as written -- `dash
    // {bf:X} mpg weight' printed a bold X (P20-01).
    //
    // The type ends at a blank or a comma, as twoway reads it: `twoway
    // scatteri, name(x)' is refused for the values it lacks.  It was read
    // up to a blank alone, so the comma became part of it and `dash
    // scatteri, name(x)', `dash (pci, name(x))' and every other type with
    // its comma glued on said "unrecognised plot type 'scatteri,'", r(198)
    // (measured 24sep2026; test_parser.cscript P1A-68).  The comma is left
    // in `rest', where it ends the varlist.
    gettoken plottype rest : seg_text, parse(" ,")
    mata: _dash_expand_plottype(strlower(st_local("plottype")), "_pt_exp")
    local ptype "`_pt_exp'"

    if "`ptype'" == "" {
        // contour and contourline are twoway plot types, and dash does not
        // draw them: each interpolates a surface over a grid of z values,
        // a data model no dash plot has.  They were answered "unrecognised
        // plot type", as if twoway had no such type; they are named for
        // what they are now, with what to use instead (WP-22 TR-22.1).
        // heatmap, rpcap and rpspike, twoway plot types in StataNow 19.5,
        // are refused the same way, each with its own reason (BR-22.1).
        // _pt_nodraw is one of those five names or "": never user text.
        mata: st_local("_pt_nodraw", _dash_undrawn_plottype(st_local("plottype")))
        if "`_pt_nodraw'" != "" {
            if "`_pt_nodraw'" == "contour" | "`_pt_nodraw'" == "contourline" {
                local _pt_why "it needs a surface interpolated over a grid. Use Stata's own twoway `_pt_nodraw', or dash scatter y x, colorvar(z) to colour each point by z."
            }
            else if "`_pt_nodraw'" == "heatmap" {
                local _pt_why "it colours the cells of a grid by z. Use Stata's own twoway heatmap, or dash scatter y x, colorvar(z) to colour each point by z."
            }
            else {
                local _pt_rng = cond("`_pt_nodraw'" == "rpcap", "rcap", "rspike")
                local _pt_why "it marks a point on a range. Use Stata's own twoway `_pt_nodraw', or draw the two together: dash (`_pt_rng' ylow yhigh x) (scatter y x)."
            }
            mata: _dash_say("err", "dash: '", st_local("plottype"), "' is a twoway plot type dash does not draw: " + st_local("_pt_why"))
            exit(198)
        }
        mata: _dash_say("err", "dash: unrecognised plot type '", st_local("plottype"), "'. ")
        display as error ///
            "Supported: scatter line connected area bar spike " _n ///
            "lfit qfit lfitci qfitci lowess lpoly lpolyci fpfit fpfitci " _n ///
            "histogram kdensity rarea rbar rspike rcap rline rconnected " _n ///
            "dot dropline rcapsym scatteri pcspike pcarrow pcbarrow " _n ///
            "pccapsym pci pcarrowi pcscatter tsline tsrline mspline mband " _n ///
            "rscatter function"
        exit(198)
    }

    // The families each plot type is routed by, named once (TR-22.4).
    _dash_plottype_families

    // ---- find comma separating varpart from options ----
    local comma_pos = 0
    mata: _dash_comma_pos(st_local("rest"), "comma_pos")

    if `comma_pos' > 0 {
        mata: st_local("varpart", strtrim(substr(st_local("rest"), 1, `comma_pos' - 1)))
        mata: st_local("opts_raw", strtrim(substr(st_local("rest"), `comma_pos' + 1, .)))
    }
    else {
        mata: st_local("varpart", strtrim(st_local("rest")))
        local opts_raw ""
    }

    // ---- the option text is handed to -syntax- as typed ----
    // Option keys used to be rewritten here by Mata before -syntax- saw
    // them, into an `opts_exp' copy.  That pre-pass is gone: dash.ado
    // declares Stata's own measured minimum abbreviations, so Stata
    // resolves prefixes itself, and opts_raw is what -syntax- reads.

    // ---- parse varlist + if/in using type-appropriate syntax program ----
    // Determine varpart syntax group for this plot type, by its family
    // (_dash_plottype_families):
    //   1v  : _pt_univar   histogram kdensity
    //   3v  : _pt_range    rarea rbar rspike rcap rline rconnected rcapsym
    //                      rscatter tsrline
    //   4v  : _pt_pc       pcspike pcarrow pcbarrow pcscatter pccapsym
    //   any : _pt_literal  scatteri pci pcarrowi function
    //
    // pcscatter takes FOUR VARIABLES in Stata -- `pcscatter y1 x1 y2 x2' --
    // and was routed to the literal parser, which wrote its variable names
    // into the spec as bare identifiers inside a JSON array:
    //     "values":[[mpg,weight],[mpg,price]]
    // which is not valid JSON.  The renderer read nothing from it and drew
    // an empty plot region, with rc 0 and no warning.
    //   std : everything else (including dot)

    // s() is not cleared when an sclass program starts, and the weight is
    // read below from s(_weight) and s(_wexp), which a varpart parser sets
    // only when the segment HAS a weight.  The `sreturn clear' further down
    // comes after the weight checks, so a command refused between the two
    // -- lowess or histogram refusing the weight, a weight expression, a
    // non-integer or negative fweight, tsline with no time variable -- left
    // its weight in s(), and the next dash command, written with no weight
    // at all, read it as its own; `dash clear' does not reach s().
    // Measured at 4ede074: after `dash lowess mpg weight [aw=price]'
    // (r(101)), `dash lfit mpg weight, name(g1)' registered an lfit
    // weighted by price; after a refused [aw=price+1], every weighted type
    // was refused with that expression's message; a scatter's note named
    // [aweight] (test_statistical_options.cscript SO-93..SO-96).  Nothing
    // this program reads from s() is set before this line: its caller saved
    // what it needed from _dash_parse_graph_opts before the segment loop.
    sreturn clear

    local yvar  ""
    local xvar  ""
    local yvar1 ""
    local yvar2 ""
    local y1var ""
    local x1var ""
    local y2var ""
    local x2var ""
    local expr  ""
    local vals  ""
    local if_cl ""
    local in_cl ""

    if `: list ptype in _pt_univar' {
        _dash_parse_varpart_1v `macval(varpart)'
        local yvar    = word("`s(varlist)'", 1)
        mata: st_local("if_cl", st_global("s(if_clause)"))
        mata: st_local("in_cl", st_global("s(in_clause)"))
    }
    else if `: list ptype in _pt_range' {
        _dash_parse_varpart_3v `macval(varpart)'
        local vl = "`s(varlist)'"
        local nv : word count `vl'
        // twoway's count, measured 24sep2026 with the console binary: one
        // variable is "too few variables specified", r(102); two are
        // "rscatter requires 3 variables: mpg weight", r(102), and four or
        // more the same words, r(103) -- for every range type in each
        // form, one-line, grouped or after ||.  With two, dash registered
        // the layer with no x and the render stopped in a KeyError
        // traceback, r(7102) (rspike drew nothing, rc 0): BUGS.md, S2.
        // tsrline takes two, and is counted below, after tsset.
        if "`ptype'" != "tsrline" & `nv' != 3 {
            if `nv' == 1 {
                display as error "too few variables specified"
                exit 102
            }
            mata: _dash_say("err", "`ptype' requires 3 variables: ", st_local("vl"), "")
            exit cond(`nv' < 3, 102, 103)
        }
        local yvar1 = word("`vl'", 1)
        local yvar2 = word("`vl'", 2)
        local xvar  = word("`vl'", 3)
        // twoway tsrline y1 y2: two variables, drawn against the time
        // variable tsset set -- there is no x to give.  Measured
        // 23sep2026: `twoway tsrline lo hi' is rc 0 on tsset data and
        // r(111) ("time variable not set") without, and a third variable is
        // r(103) ("rline requires 3 variables: lo hi turn t").  dash used
        // to read a third variable as the x and draw against it, a picture
        // twoway refuses to draw (test_help_claims_1.cscript HC1-09).
        if "`ptype'" == "tsrline" {
            // tsset first, as twoway asks it first: `tsrline lo hi t' on
            // un-tsset data is r(111) there, not r(103).
            if `"`_dta[_TStvar]'"' == "" {
                display as error "dash: tsrline needs a time variable: " ///
                    "tsset your data first, as twoway tsrline does."
                exit(111)
            }
            // twoway draws `rline y1 y2 t' and counts that: `tsrline
            // mpg' is "rline requires 3 variables: mpg t", r(102), and
            // three are the same words, r(103) (measured 24sep2026).
            if `nv' != 2 {
                mata: _dash_say("err", "rline requires 3 variables: ", ///
                    st_local("vl") + " " + st_global("_dta[_TStvar]"), "")
                exit cond(`nv' < 2, 102, 103)
            }
            local xvar `"`_dta[_TStvar]'"'
        }
        mata: st_local("if_cl", st_global("s(if_clause)"))
        mata: st_local("in_cl", st_global("s(in_clause)"))
    }
    else if `: list ptype in _pt_pc' {
        _dash_parse_varpart_4v `macval(varpart)'
        local vl = "`s(varlist)'"
        local nv : word count `vl'
        // twoway: one variable "too few variables specified", r(102); two
        // or three "pcspike requires 4 variables: mpg weight", r(102);
        // five or more the same words, r(103) (measured 24sep2026).
        if `nv' != 4 {
            if `nv' == 1 {
                display as error "too few variables specified"
                exit 102
            }
            mata: _dash_say("err", "`ptype' requires 4 variables: ", st_local("vl"), "")
            exit cond(`nv' < 4, 102, 103)
        }
        local y1var = word("`vl'", 1)
        local x1var = word("`vl'", 2)
        local y2var = word("`vl'", 3)
        local x2var = word("`vl'", 4)
        mata: st_local("if_cl", st_global("s(if_clause)"))
        mata: st_local("in_cl", st_global("s(in_clause)"))
    }
    else if `: list ptype in _pt_literal' {
        _dash_parse_varpart_any `macval(varpart)'
        if "`ptype'" == "function" {
            // Remove optional "y=" prefix, in Mata: an expression holding "'
            // -- strlen("'x") -- ended the compound quotes it was cut in
            // (test_json_escaping.cscript JSE-47).
            mata: st_local("vals", regexr(strtrim(st_global("s(vals)")), "^[a-zA-Z][a-zA-Z0-9_]*[ ]*=[ ]*", ""))
            local expr : copy local vals
            // No expression is refused in twoway's words: "expression
            // required", r(100), and after a `y =', "nothing found where
            // expression expected", r(111) -- with the comma glued, spaced
            // or absent, in parentheses, after ||, or with only an if, an
            // in or a weight (measured 24sep2026; P1A-71).  dash said
            // "something required", r(100), for the first, and registered
            // `function y =' with rc 0, drawn as an empty layer.
            if !`: length local expr' {
                mata: st_local("_fn_none", strofreal(st_global("s(vals)") == ""))
                if `_fn_none' {
                    display as error "expression required"
                    exit 100
                }
                display as error "nothing found where expression expected"
                exit 111
            }
            // A function Stata does not have is refused as twoway refuses
            // it, before anything is registered.
            _dash_fn_refuse `"`macval(expr)'"'
        }
        else {
            mata: st_local("vals", st_global("s(vals)"))
        }
        mata: st_local("if_cl", st_global("s(if_clause)"))
        mata: st_local("in_cl", st_global("s(in_clause)"))
        if `: list ptype in _pt_imm' {
            // twoway's immediate values, one record each:
            //     scatteri  #y #x            [(#clockpos)] ["text for label"]
            //     pci       #y1 #x1 #y2 #x2  [(#clockpos)] ["text for label"]
            //     pcarrowi  #y1 #x1 #y2 #x2  [(#clockpos)] ["text for label"]
            // read in Mata, as a value, as twoway's own parsers read them,
            // and written one record per point, segment or arrow: the
            // coordinates, then "label",clock when either is given.  The
            // grammar and what twoway does with each case are measured in
            // dash_parse.mata, section 2c.  What twoway refuses is refused
            // with its return code, r(198), the token shown as written;
            // what it drops at the end is dropped too -- and named, where
            // twoway says nothing.
            //
            // scatteri and pci used to be written token by token as they
            // were typed, checked only for an even count: `dash pci 0 0 0
            // abc' and `dash scatteri .5 3000' registered, rc 0, as
            // "values":[[0,0],[0,abc]] and [[.5,3000]], which are not JSON,
            // and the render stopped on a JSONDecodeError, r(7102)
            // (measured 23sep2026; test_parser.cscript P1A-60..67).
            if "`ptype'" == "scatteri" {
                local _imm_w    2
                local _imm_unit "point"
                local _imm_nw   "two"
                local _imm_xy   "#y #x"
            }
            else {
                local _imm_w    4
                local _imm_unit = cond("`ptype'" == "pci", "segment", "arrow")
                local _imm_nw   "four"
                local _imm_xy   "#y1 #x1 #y2 #x2"
            }
            mata: _dash_immediate(st_local("vals"), `_imm_w')
            // What ends twoway's loop early: a quoted "" where a record's
            // last coordinate belongs.
            local _imm_q = char(34) + char(34)
            local _imm_empty `"`_imm_q' where a `_imm_unit''s last number belongs ends the list, as in twoway `ptype'."'
            if "`_pci_err'" == "point" {
                mata: _dash_say("err", "dash: `ptype' takes `_imm_nw' numbers for each `_imm_unit', `_imm_xy'; '", st_local("_pci_bad"), "' is not a number.")
                display as error `"      Each `_imm_unit' is `_imm_xy' [(#clockpos)] ["text for label"], as in twoway `ptype'."'
                exit 198
            }
            if "`_pci_err'" == "position" {
                mata: _dash_say("err", "dash: `ptype': invalid position, ", st_local("_pci_bad"), "; a clock position is a number from 0 to 12.")
                exit 198
            }
            if "`_pci_err'" == "none" {
                display as error "dash: `ptype' needs at least one `_imm_unit', `_imm_nw' numbers `_imm_xy'."
                if "`_pci_stop'" == "empty" {
                    mata: _dash_say("err", "      '", st_local("_pci_left"), "': " + st_local("_imm_empty"))
                }
                else if `_pci_hasleft' {
                    mata: _dash_say("err", "      '", st_local("_pci_left"), "' is too little for one.")
                }
                exit 198
            }
            if "`_pci_stop'" == "empty" {
                mata: _dash_say("txt", "dash: `ptype' ignored '", st_local("_pci_left"), "' at the end: " + st_local("_imm_empty"))
            }
            else if `_pci_hasleft' {
                mata: _dash_say("txt", "dash: `ptype' ignored '", st_local("_pci_left"), "' at the end, too little for another `_imm_unit' (`_imm_xy'), as twoway does.")
            }
            // twoway pci is an immediate pcspike: its serset carries the
            // labels and it draws none of them (measured from its SVG
            // export, with mlabcolor() and mlabposition() or without).
            // Neither does dash -- and it says so, where twoway is silent.
            if "`ptype'" == "pci" & `_pci_nlab' > 0 {
                display as text "dash: pci draws no labels, as twoway pci draws none; a scatteri layer can label a point."
            }
        }
    }
    else {
        // Standard: the LAST variable is x; every variable before it is a
        // y-variable and becomes its own plot, exactly as twoway does.
        //   twoway scatter mpg price weight  ->  two series
        // dash used to keep word 1 and the last word and silently discard
        // everything between, so that command drew ONE series and half the
        // user's data vanished with no error and no warning.
        //
        // No variable at all is twoway's refusal, "varlist required",
        // r(100), which -syntax- gives in its own words.  The parse was
        // skipped when there was nothing to parse, so `dash scatter ,
        // name(g1)' registered a graph with no variables, rc 0 -- and line,
        // connected, area, bar, spike, dropline, dot, the fits, the
        // smoothers and tsline likewise -- and the bare `dash scatter' was
        // refused as "no variables identified in plot specification",
        // r(198) (measured 24sep2026; test_parser.cscript P1A-69).
        _dash_parse_varpart_std `macval(varpart)'
        local vl = "`s(varlist)'"
        local nv : word count `vl'
        local yvar = word("`vl'", 1)
        if `: list ptype in _pt_ts' {
            // twoway tsline y1 [y2 ...]: EVERY variable is a series,
            // each drawn against the time variable tsset set; there is
            // no x to give.  Measured 23sep2026 from twoway's saved
            // .gph: `tsline mpg turn' on tsset data is two lines, mpg
            // and turn, each against t -- and dash drew mpg against
            // turn, reading the last variable as the x.  Without tsset
            // twoway refuses every form, r(111) ("time variable not
            // set"), and so does dash (test_help_claims_1.cscript
            // HC1-09).  tsrline, a range type, is read above.
            local xvar `"`_dta[_TStvar]'"'
            if `"`xvar'"' == "" {
                display as error "dash: `ptype' needs a time variable: " ///
                    "tsset your data first, as twoway `ptype' does."
                exit(111)
            }
            // WP-19: one plot object per series, held to the plot limit
            // before any is built, as the y variables below are.
            if `nv' > 1 {
                _dash_limit, name(plots)
                if `nv' > r(value) {
                    if `nsegs' > 1 _dash_plot_cap_refuse `r(value)' `r(ceiling)'
                    else           _dash_plot_cap_refuse `r(value)' `r(ceiling)' `nv'
                }
            }
            local yvarlist "`vl'"
        }
        else if `nv' >= 3 & `: list ptype in _pt_onefit' {
            // A fit or smoother takes one y and one x.  twoway, measured
            // 24sep2026: "too many variables specified: mpg weight price",
            // r(103), on lfit qfit lfitci qfitci fpfit fpfitci mspline
            // mband; lowess, lpoly and lpolyci say it without the list.
            // dash drew one fit per y variable, rc 0 (P1A-79).
            if `: list ptype in _pt_onefit_bare' {
                display as error "too many variables specified"
            }
            else {
                mata: _dash_say("err", "too many variables specified: ", st_local("vl"), "")
            }
            exit 103
        }
        else if `nv' >= 2 {
            local xvar = word("`vl'", `nv')
            local nyv = `nv' - 1
            // WP-19: one plot object is built per y variable below, so
            // a segment whose y variables alone pass the plot limit is
            // refused here, before any of them is built.  In a graph
            // of several segments only "more than the limit" is known.
            if `nyv' > 1 {
                _dash_limit, name(plots)
                if `nyv' > r(value) {
                    if `nsegs' > 1 _dash_plot_cap_refuse `r(value)' `r(ceiling)'
                    else           _dash_plot_cap_refuse `r(value)' `r(ceiling)' `nyv'
                }
            }
            local yvarlist ""
            forvalues vi = 1/`nyv' {
                local _thisy = word("`vl'", `vi')
                local yvarlist `"`yvarlist' `_thisy'"'
            }
            local yvarlist = strtrim(`"`yvarlist'"')
        }
        else {
            // Every other type on this path takes a y AND an x (tsline,
            // which takes its x from tsset, is read above).  Measured
            // 22sep2026 with the console binary: `twoway bar price',
            // `twoway scatter mpg', and spike, area, line, dropline,
            // connected, dot, the fit and the smoother types all say
            // "too few variables specified" r(102).  dash registered
            // such a segment with rc 0 and the build then died in
            // Python on the empty x column, r(7102).  Refused here,
            // before any JSON is written, in twoway's words: dash said
            // "dash: scatter requires a y and an x variable (got: mpg)"
            // (BUGS.md, S3 batch; test_parser.cscript P1A-82).
            display as error "too few variables specified"
            exit(102)
        }
        mata: st_local("if_cl", st_global("s(if_clause)"))
        mata: st_local("in_cl", st_global("s(in_clause)"))
    }

    // Strip the "if"/"in" keyword prefix that syntax leaves in the macros.
    // Stata may store `if' as either " if <expr>" (with leading space) or
    // "if <expr>" (without leading space) depending on the context.
    // Using regexr() to strip the prefix robustly handles both cases.  In
    // Mata, by value: in compound quotes,  if make == "' or 1 or '"  ended
    // them (measured 24sep2026; test_json_escaping.cscript JSE-44).
    mata: st_local("if_expr", strtrim(regexr(st_local("if_cl"), "^[ ]*if[ ]+", "")))
    mata: st_local("in_expr", strtrim(regexr(st_local("in_cl"), "^[ ]*in[ ]+", "")))
    // Each variable the qualifier abbreviates is written out, as Stata
    // read it against the data in memory: -syntax- has just evaluated it
    // there.  The renderer evaluates the qualifier against the exported
    // columns, which carry full names, so `if dis > 100' named no column
    // and was skipped, every row drawn (measured 24sep2026;
    // test_qualifier_literals.cscript QL-22).  Literals are left as typed.
    mata: st_local("if_expr", _dash_qual_expand(st_local("if_expr")))

    // ---- The plot's sample, for the checks made here ----
    // A weight's values and histogram's start() are checked over the rows
    // the plot draws: its own if and in, and the graph's, written after
    // the plot groups (_dash_plot hands it over in $dash__gq_if and
    // $dash__gq_in, read by value).  The graph's was left out, so
    // `(lfit mpg weight [fw=halfint]) if foreign==1' was refused, r(401),
    // for rows twoway never reads (WP-27; test_help_claims_6.cscript
    // HC6-56).  Two ranges cannot share one `in': the graph's is then
    // marked in a temporary variable and read as a condition.
    mata: st_local("_gq_if_s", st_global("dash__gq_if"))
    mata: st_local("_gq_in_s", st_global("dash__gq_in"))
    local _ps_if ""
    if `: length local if_expr' {
        local _ps_if `"(`macval(if_expr)')"'
    }
    if `: length local _gq_if_s' {
        if `: length local _ps_if' {
            local _ps_if `"`macval(_ps_if)' & (`macval(_gq_if_s)')"'
        }
        else {
            local _ps_if `"(`macval(_gq_if_s)')"'
        }
    }
    local _ps_in ""
    if `: length local in_expr' & `: length local _gq_in_s' {
        tempvar _ps_mark
        quietly gen byte `_ps_mark' = 1 in `macval(_gq_in_s)'
        if `: length local _ps_if' {
            local _ps_if `"`macval(_ps_if)' & !missing(`_ps_mark')"'
        }
        else {
            local _ps_if `"!missing(`_ps_mark')"'
        }
        local _ps_in : copy local in_expr
    }
    else if `: length local in_expr' {
        local _ps_in : copy local in_expr
    }
    else if `: length local _gq_in_s' {
        local _ps_in : copy local _gq_in_s
    }
    local _psq ""
    if `: length local _ps_if' {
        local _psq `"if `macval(_ps_if)'"'
    }
    if `: length local _ps_in' {
        local _psq `"`macval(_psq)' in `macval(_ps_in)'"'
    }

    // ---- parse options (clear stale sreturn values first) ----
    // The varpart parsers sreturn the weight TYPE in s(_weight) and the
    // weight EXPRESSION, without its leading `=', in s(_wexp).  Both are
    // saved before the clear below destroys them.
    mata: st_local("_seg_weight", st_global("s(_weight)"))
    mata: st_local("_seg_wexp", st_global("s(_wexp)"))

    // ---- weights (WP-18) ----
    // Which type honours which weight is twoway's own acceptance table,
    // measured 23sep2026 (test/fixtures/stat_truth.json, weight_acceptance):
    // iweight is refused on every type; lowess refuses every weight;
    // histogram takes fweight only; kdensity, lpoly and lpolyci refuse
    // pweight; the fit, smoother and band types take aw, fw and pw.  Each
    // refusal is twoway's, r(101), in twoway's words.  On the glyph types
    // (scatter, line, bar ...) a weight is accepted and named in the note
    // by type, as WP-13 left it: dash draws every observation.
    local _wt_honoured "lfit qfit lfitci qfitci lpoly lpolyci fpfit fpfitci histogram kdensity mspline mband"
    // The types that refuse a pweight: a list, like every plot-type family,
    // rather than a string inlist() (TR-22.4).
    local _wt_nopw "kdensity lpoly lpolyci"
    if `"`_seg_weight'"' != "" {
        // scatteri, pci and pcarrowi take no weight: twoway refuses an
        // aweight, fweight or pweight there with r(198), "weights not
        // allowed" (measured 23sep2026; an iweight syntax has already
        // refused, r(101), as twoway does).  function takes one and draws
        // nothing different, and is named in the note below by type.
        if `: list ptype in _pt_imm' {
            display as error "weights not allowed"
            exit 198
        }
        local _wt_refused ""
        if "`_seg_weight'" == "iweight" {
            local _wt_refused "iweights not allowed"
        }
        else if "`ptype'" == "lowess" {
            local _wt_refused "weights not allowed"
        }
        else if "`ptype'" == "histogram" & "`_seg_weight'" != "fweight" {
            local _wt_refused "`_seg_weight's not allowed"
        }
        else if `: list ptype in _wt_nopw' & "`_seg_weight'" == "pweight" {
            local _wt_refused "pweights not allowed"
        }
        if `"`_wt_refused'"' != "" {
            display as error "`_wt_refused'"
            exit 101
        }
    }
    if `"`_seg_weight'"' != "" & `: list ptype in _wt_honoured' {
        // The data reach the renderer as exported, one column per
        // variable, so a weight must be ONE existing variable.  twoway
        // evaluates `[aw=price+1]' itself; dash cannot, and says so
        // rather than weighting by something else.  unab expands an
        // abbreviation (`[aw=pri]') to the full name the renderer reads.
        // It reads a VARLIST, so the expression must first be one name:
        // unab resolves the range `price-price' to price, where twoway
        // weights by the expression price-price, which is zero (measured
        // 23sep2026, rc 0).  confirm name accepts any Stata name,
        // Unicode included, and nothing else.
        local _wx ""
        capture confirm name `macval(_seg_wexp)'
        if !_rc {
            capture unab _wx : `macval(_seg_wexp)'
        }
        if _rc | `: word count `_wx'' != 1 {
            // The expression is echoed through _dash_say: read by value,
            // shown as written (a brace or a quote in it is the user's text).
            mata: _dash_say("err", "dash: [`_seg_weight'=", st_local("_seg_wexp"), "] must name one variable; dash cannot evaluate a weight expression.")
            mata: _dash_say("err", "      Generate it first: generate double w = ", st_local("_seg_wexp"), "")
            exit 198
        }
        local _seg_wexp "`_wx'"
        // twoway's own checks of the weight's values, measured 23sep2026:
        // a non-integer fweight is r(401) "may not use noninteger frequency
        // weights" on lfit lfitci lpoly lpolyci histogram kdensity; a
        // negative fweight is r(402) "negative weights encountered" on
        // lpoly lpolyci histogram kdensity, and so is a negative aweight on
        // lpoly lpolyci kdensity.  Elsewhere the command is accepted and
        // the renderer does what twoway draws: lfit, qfit, lfitci and
        // qfitci fit as if `if w > 0'; qfit, qfitci, fpfit and fpfitci
        // draw nothing for a non-integer fweight, and fpfit and fpfitci
        // nothing for any negative weight (regress and fracpoly "could not
        // fit model"); mspline and mband ignore the weight.  Each check
        // runs over the plot's own if/in sample -- a bad weight on a row
        // whose y is missing still refuses, one outside the if does not --
        // and a missing weight drops its observation without an error.
        // The graph's qualifier is part of that sample (_psq, above) --
        // except on kdensity, which twoway checks over its own qualifier
        // alone: `(kdensity mpg [aw=w]) if foreign==1', w negative on the
        // domestic cars only, is r(402) in twoway, and [fw=] non-integer
        // there r(401), where the same weights inside the parentheses, or
        // on lfit, lfitci, lpoly, lpolyci or histogram with the graph's
        // qualifier, are rc 0 (measured 24sep2026; HC6-56).
        local _wq : copy local _psq
        if "`ptype'" == "kdensity" {
            local _wq ""
            if `: length local if_expr' {
                local _wq `"if (`macval(if_expr)')"'
            }
            if `: length local in_expr' {
                local _wq `"`macval(_wq)' in `macval(in_expr)'"'
            }
        }
        local _w_neg ""
        if "`_seg_weight'" == "fweight" local _w_neg "lpoly lpolyci histogram kdensity"
        if "`_seg_weight'" == "aweight" local _w_neg "lpoly lpolyci kdensity"
        if "`_seg_weight'" == "fweight" {
            local _fw_int "lfit lfitci lpoly lpolyci histogram kdensity"
            if `: list ptype in _fw_int' {
                capture assert `_wx' == floor(`_wx') | missing(`_wx') `macval(_wq)'
                if _rc {
                    display as error "may not use noninteger frequency weights"
                    exit 401
                }
            }
        }
        if `: list ptype in _w_neg' {
            capture assert `_wx' >= 0 | missing(`_wx') `macval(_wq)'
            if _rc {
                display as error "negative weights encountered"
                exit 402
            }
        }
    }

    sreturn clear
    local _rp_gund_out ""
    // A weight-only segment goes through the parser and the validation
    // too, so the weight keys are in s() for the JSON writer and the flag
    // rules run on every segment; the parser takes an empty option list.
    if `: length local opts_raw' | `"`_seg_weight'"' != "" {
        // ytitle(, axis(2)) -> ytitle2() before the repeat merge folds
        // copies of ytitle into one (WP-28 B3, _dash_route_axis2).
        mata: st_local("opts_raw", _dash_route_axis2(st_local("opts_raw")))
        _dash_parse_plot_opts , `macval(opts_raw)'
        // An option it declares whose value -syntax- could not bind:
        // refused as twoway refuses it, not named as unsupported.
        _dash_refuse_unbound _dash_parse_plot_opts `"`macval(opts_raw)'"'
        // A second name() in this option list: -syntax- binds the first to
        // NAMe() and leaves any other to the catch-all, which is read by
        // value -- it is the user's text.
        mata: st_local("_seg_name2", strofreal(_dash_has_name_opt(st_global("s(_unknown)"))))
        if `_seg_name2' _dash_refuse_second_name
        // An option written in upper case -- ATOBS, MCOLOR(red) -- is no
        // option twoway takes: refused as twoway refuses it, naming the
        // first word it does not take (_dash_refuse_foreign).
        _dash_refuse_foreign _dash_parse_plot_opts `ptype' `"`macval(opts_raw)'"'
        // An option given more than once: read as twoway reads it -- the
        // last copy, the copies merged, or refused (_dash_opts_repeats).
        _dash_opts_repeats _dash_parse_plot_opts `ptype' `"`macval(opts_raw)'"'
        // lowess's logit, or its off form, on another plot type: refused
        // naming the word as typed, as twoway names it -- scatter mpg
        // weight, lo is "option lo not allowed", r(198) -- where the flag
        // rule below named logit whatever was typed, and nolo, nologi and
        // nologit were taken in silence.  log and nolog are logging.
        if "`ptype'" != "lowess" {
            mata: st_local("_lt_typed", _dash_logit_typed(st_local("opts_raw")))
            if `: length local _lt_typed' {
                mata: _dash_say("err", "option ", st_local("_lt_typed"), " not allowed")
                display as error "      logit is an option of lowess alone; log is twoway's graph option logging."
                exit 198
            }
        }
        _dash_fold_bw "`ptype'"
        if `"`_seg_weight'"' != "" & `: list ptype in _wt_honoured' {
            _dash_seg_weight_s "`_seg_weight'" "`_seg_wexp'"
        }
        _dash_validate_opts "`ptype'"
        // colorvar() and its companions, and jitter(), on a plot type dash
        // does not draw them on: named in the note -- after the validation
        // above, so a bad value is refused first, as twoway refuses it
        // (WP-23).
        _dash_fold_typed "`ptype'"
        // twoway__histogram_gen.ado:102-107: a start() above the variable's
        // minimum over the plot's sample is r(198), discrete or not.  dash
        // drew it, the observations below start() silently left out of
        // every bar (the WP-18 review, 23sep2026).
        if "`ptype'" == "histogram" & `"`s(start)'"' != "" {
            // The plot's sample, the graph's qualifier in it (_psq).
            local _hq : copy local _psq
            quietly summarize `yvar' `macval(_hq)', meanonly
            if r(N) > 0 {
                if r(min) < `s(start)' & reldif(r(min), `s(start)') > 1e-5 {
                    display as error "option start() may not be larger than minimum of `yvar'"
                    exit 198
                }
            }
        }
    }

    // ---- A sample twoway's statistical command cannot draw ----
    // Measured 24sep2026 with the console binary, on no observations, on
    // a sample the plot's if/in or the graph's qualifier empties, on one
    // observation, and on samples missing values and weights empty
    // (test_parser.cscript P1A-80; BUGS.md, S3):
    //   histogram  _N == 0: "observation numbers out of range", r(198),
    //              whatever the qualifier or option; a sample emptied by
    //              a qualifier or by missing values is drawn, rc 0
    //   lpoly(ci)  none in the sample: "no observations", r(2000); one:
    //              "insufficient observations", r(2001)
    //   lfit(ci)   one: "(note:  regress could not fit model)", then
    //              "insufficient observations", r(2001)
    //   kdensity   one: "insufficient observations", r(2001)
    //   fpfit(ci)  none the if and in select: "(note:  fracpoly could not
    //              fit model)", then "observation numbers out of range",
    //              r(198); emptied by missing values, the note, rc 0
    //   mspline,   none the if and in select, and no bands(): "bands must
    //   mband      be between 1 and 200", r(198)
    // The sample is _psq -- the plot's if and in and the graph's
    // qualifier -- and, where it is counted, the rows whose variables are
    // not missing and, weighted, whose weight is above zero (a zero
    // fweight or a missing aweight leaves lpoly "no observations").  dash
    // registered each and drew an empty layer, rc 0.  What twoway draws
    // with a note -- lfit on none, qfit, fpfit on one -- the renderer
    // notes (GlyphMapper._mark_unfit).  Under by() twoway answers panel by
    // panel -- lfit with one car in a panel notes it and leaves the panel
    // out, rc 0 -- and _dash_plot answers it so, once the graph's by() is
    // known (P1A-83).  The qualifier is run as
    // -syntax- read it, by value (macval), once per count.
    mata: st_local("_ss_bands", st_global("s(bands)"))
    local _pt_fpfam "fpfit fpfitci"
    local _pt_bands "mspline mband"
    local _pt_lpfam "lpoly lpolyci"
    local _ss_types "histogram lpoly lpolyci lfit lfitci kdensity fpfit fpfitci mspline mband"
    mata: st_local("_ss_by", st_global("s(g_by)") + st_global("dash__g_by"))
    if `: list ptype in _ss_types' & !`: length local _ss_by' {
        local _ss_ifin ""
        if `: length local _ps_in' {
            local _ss_ifin `"in `macval(_ps_in)'"'
        }
        if "`ptype'" == "histogram" {
            if _N == 0 {
                display as error "observation numbers out of range"
                exit 198
            }
        }
        else if `: list ptype in _pt_fpfam' | ///
            (`: list ptype in _pt_bands' & !`: length local _ss_bands') {
            quietly count `macval(_psq)'
            if r(N) == 0 {
                if `: list ptype in _pt_fpfam' {
                    display as text "(note:  fracpoly could not fit model)"
                    display as error "observation numbers out of range"
                }
                else {
                    display as error "bands must be between 1 and 200"
                }
                exit 198
            }
        }
        else if !`: list ptype in _pt_bands' & !`: list ptype in _pt_fpfam' {
            local _ss_c "!missing(`yvar')"
            if "`ptype'" != "kdensity" local _ss_c "!missing(`yvar', `xvar')"
            if `"`_seg_weight'"' != "" {
                local _ss_c "`_ss_c' & !missing(`_seg_wexp') & `_seg_wexp' > 0"
            }
            if `: length local _ps_if' {
                local _ss_c `"`_ss_c' & `macval(_ps_if)'"'
            }
            quietly count if `macval(_ss_c)' `macval(_ss_ifin)'
            local _ss_n = r(N)
            if `_ss_n' == 0 & `: list ptype in _pt_lpfam' {
                display as error "no observations"
                exit 2000
            }
            if `_ss_n' == 1 {
                if "`ptype'" == "lfit" | "`ptype'" == "lfitci" {
                    display as text "(note:  regress could not fit model)"
                }
                display as error "insufficient observations"
                exit 2001
            }
        }
    }

    // Accumulate this segment's unsupported options so _dash_plot can report
    // them once for the whole command rather than once per plot segment.
    // c_local cannot read the caller's local, so hand back only THIS
    // segment's list and let _dash_plot append it.
    // A weight on a type that does not honour it is named by TYPE, in
    // brackets, never by variable: [aweight].  On a type that honours it
    // (`_wt_honoured') it is written to the spec and nothing is named.
    local _seg_wtok ""
    if `"`_seg_weight'"' != "" & !`: list ptype in _wt_honoured' local _seg_wtok `" [`_seg_weight']"'
    mata: st_local("_seg_ign", st_global("s(_pending)") + " " + st_global("s(_unknown)") + st_local("_seg_wtok"))
    c_local _seg_ignored_out : copy local _seg_ign
    // The graph-wide options dash does not declare that this segment gave
    // (clegend(), pcycle(), notitling, ...): twoway takes each once from
    // the whole command, so _dash_plot counts them across segments.
    c_local _seg_gund_out : copy local _rp_gund_out
    // Whether this segment gave name(): _dash_plot counts them across the
    // command and refuses a second (_dash_refuse_second_name).
    mata: st_local("_seg_named", strofreal(st_global("s(g_name)") != ""))
    c_local _seg_named_out `_seg_named'

    // Hand the graph-level options found in this segment to _dash_plot as
    // _sg_* locals (they live in its frame, not here -- c_local propagates
    // them); _dash_plot merges each into its g_* accumulator as twoway
    // merges a repeated option (_dash_rep_merge).  They were c_local'ed
    // over the accumulator, so a later group's legend(label(2 "B")) threw
    // away an earlier group's legend(label(1 "A")), which twoway keeps.
    foreach gkey in title subtitle note caption name saving xtitle ytitle xlabel ///
            ylabel xline yline legend by xscale yscale aspectratio scheme ///
            plotregion graphregion bgcolor plotbgcolor link filter ytitle2 ///
            xtitle2 ylabel2 xlabel2 yscale2 xscale2 xsize ysize fxsize fysize ///
            scale text hover xtick ytick xmtick ymtick xmlabel ymlabel t1title ///
            t2title b1title b2title l1title l2title r1title r2title title2 ///
            subtitle2 zlabel ztitle zscale nodraw play replace {
        mata: st_local("gval", st_global("s(g_" + st_local("gkey") + ")"))
        if `: length local gval' {
            c_local _sg_`gkey' : copy local gval
        }
    }

    // ---- build plot JSON ----
    // Variable fields
    local vfields ""

    if `: list ptype in _pt_univar' {
        _dash_json_str "`yvar'" _jyv
        local vfields `""var":"`_jyv'""'
    }
    else if `: list ptype in _pt_range' {
        _dash_json_str "`yvar1'" _jy1
        _dash_json_str "`yvar2'" _jy2
        _dash_json_str "`xvar'"  _jxv
        local vfields `""yvar1":"`_jy1'","yvar2":"`_jy2'","xvar":"`_jxv'""'
    }
    else if `: list ptype in _pt_pc' {
        _dash_json_str "`y1var'" _jy1
        _dash_json_str "`x1var'" _jx1
        _dash_json_str "`y2var'" _jy2
        _dash_json_str "`x2var'" _jx2
        local vfields `""y1var":"`_jy1'","x1var":"`_jx1'","y2var":"`_jy2'","x2var":"`_jx2'""'
    }
    else if "`ptype'" == "function" {
        _dash_json_str `"`macval(expr)'"' _jex
        local vfields `""expr":"`_jex'""'
    }
    else if `: list ptype in _pt_imm' {
        // scatteri, pci and pcarrowi: read and checked with the varlist
        // above, one record per point, segment or arrow, every coordinate
        // a JSON number or null.  The array holds no apostrophe, backtick
        // or dollar sign -- a label carries each as a JSON unicode escape
        // (u0027, u0060, u0024 after a backslash) -- so it expands safely
        // inside any quotes.  scatteri's was built here token by token, as
        // typed, a label cut at its first blank (P1A-60).
        local vfields `""values":`_pci_json'"'
    }
    else {
        _dash_json_str "`yvar'" _jyv
        _dash_json_str "`xvar'" _jxv
        local vfields `""yvar":"`_jyv'","xvar":"`_jxv'""'
    }

    // Options JSON
    _dash_plot_opts_to_json _opts_json

    // if/in, in compound quotes.  In plain quotes a qualifier holding a
    // double quote was split at it: -args- in _dash_json_str took the text
    // before the first inner quote as the value and the word after it as
    // the name to store under, so  if make != "AMC Concord" & foreign == 1
    // stored "if_expr":"" -- the qualifier gone, every row drawn, no word
    // (measured 23sep2026 at ad13a0f) -- and  make != "<b>"  stopped with
    // "_< invalid name".
    _dash_json_str `"`macval(if_expr)'"' _jif
    _dash_json_str `"`macval(in_expr)'"' _jin

    // Assemble.  A standard varlist with several y-variables produces ONE plot
    // object per y-variable; they are comma-joined here and the caller splices
    // them into the plots array exactly as it does separate segments, so each
    // gets its own scheme style index downstream.
    if `"`yvarlist'"' != "" {
        local seg_json ""
        local _nyv : word count `yvarlist'
        forvalues _yi = 1/`_nyv' {
            local _thisy = word(`"`yvarlist'"', `_yi')
            _dash_json_str "`_thisy'" _jyv
            _dash_json_str "`xvar'"   _jxv
            local vfields `""yvar":"`_jyv'","xvar":"`_jxv'""'
            if `_yi' > 1 local seg_json `"`seg_json',"'
            local seg_json `"`seg_json'{"type":"`ptype'",`vfields',"options":`_opts_json',"if_expr":"`_jif'","in_expr":"`_jin'"}"'
        }
    }
    else {
        local _nyv = 1
        local seg_json `"{"type":"`ptype'",`vfields',"options":`_opts_json',"if_expr":"`_jif'","in_expr":"`_jin'"}"'
    }

    c_local `plottype_out' "`ptype'"
    c_local `json_out'     `"`seg_json'"'
    // How many plot objects seg_json holds, for _dash_plot's running total
    // against the plot limit (WP-19).
    c_local _seg_nplots_out `_nyv'
    // The plot's own if and in, as -syntax- read them (abbreviations
    // written out), and whether it gave bands(): _dash_plot answers a by()
    // graph's panels from them once every segment, and the graph's by(),
    // is known (_dash_by_refuse).
    c_local _seg_if_out : copy local if_expr
    c_local _seg_in_out : copy local in_expr
    c_local _seg_bands_out = `: length local _ss_bands' > 0
    // The plotted variables and the weight's, which a panel's sample
    // leaves out when missing (and a weight not above zero).
    c_local _seg_vars_out `yvar' `xvar'
    local _seg_wv ""
    if `"`_seg_weight'"' != "" & `: list ptype in _wt_honoured' local _seg_wv `_seg_wexp'
    c_local _seg_wvar_out `_seg_wv'
end




// ================================================================
// _dash_formats_json  -- build the "formats" map, and name the date
//                        variables that need numeric transport
//
// jsonio cannot emit display formats: its metadata branch is gated on
// inlist("`metaprint'`filenm'", ...) -- a CONCATENATION -- so with a
// non-empty filenm() the branch never fires and metaprint() is a no-op.
// StataAllToJSON has no format field either; it holds
// Variables.getDisplayFmt() internally and never serializes it.  So dash
// carries the formats itself, in its own master JSON.  jsonio is not
// modified.  The writer that replaced it (_dash_write_data) writes stored
// values only, so the formats still travel here.
// ================================================================
program define _dash_formats_json
    version 16.0
    args varlist_in out_macro datevars_macro

    local parts ""
    local nparts = 0
    local datevars ""
    local seen ""

    foreach v of local varlist_in {
        capture confirm variable `v'
        if _rc continue
        // The variable as Stata stores it, once.  A qualifier may
        // abbreviate one -- `if dis > 100' reads displacement -- and the
        // words of a qualifier's string literal are among the names read,
        // so `if make != "d"' names d too.  st_varformat() takes no
        // abbreviation, and every render of such a command stopped with
        // r(3500) "invalid Stata variable name" (measured 24sep2026,
        // test_program_coverage.cscript PC-31).  The format is keyed by
        // the stored name, the column the renderer reads.
        capture unab v : `v', max(1)
        if _rc continue
        if `: list v in seen' continue
        local seen `seen' `v'

        // The format is read, escaped and classified in Mata, by value,
        // never as macro text.  A display format is user text: Stata
        // accepts %td!" and %td!` (a ! puts any character into a date
        // picture) and %tdDD!$DD.  Read with `: format', the backtick
        // opened a compound quote that the test below never closed --
        // r(132), "too few quotes", on every render of the variable -- and
        // $DD was expanded as a global, so the spec said %tdDD! (measured
        // 24sep2026; test_program_coverage.cscript PC-03).
        mata: st_local("_fjv", _json_escape(st_varformat(st_local("v"))))
        // %t and %-t followed by one of the eight kind letters, case
        // sensitively: %tc and %tC are different formats.
        mata: st_local("_fdate", strofreal(regexm(st_varformat(st_local("v")), "^%-?t[cCdhmqwy]")))

        if `nparts' > 0 local parts `"`parts',"'
        local parts `"`parts'"`v'":"`_fjv'""'
        local nparts = `nparts' + 1
        if `_fdate' local datevars `"`datevars' `v'"'
    }

    c_local `out_macro'      `"{`parts'}"'
    c_local `datevars_macro' `"`datevars'"'
end


// ================================================================
// _dash_empty_data  — the data file of a dashboard that exports no
// variable
// ================================================================
// A dashboard whose graphs are all scatteri, pci, pcarrowi and function
// draws from its own values, as twoway draws them with no data in memory.
// jsonio needs a varlist, so dash.ado writes the file itself: jsonio's
// layout holding no variable and no observation, which both renderers read
// as an empty dataset (test_immediate_dashboards.py pins the same text).
// `dash build' refused such a dashboard, "no variables identified across
// registered graphs", r(198); the one-line form exported one observation
// of the first variable in memory, which no layer read, and with no data
// in memory was refused too (test_parser.cscript P1A-72).
program define _dash_empty_data
    version 16.0
    args path
    tempname fh
    // quietly: `write replace' notes a file that is not there yet.
    quietly file open `fh' using `"`path'"', write text replace
    file write `fh' `"{"values":[],"variableIsString":{},"variableNames":[],"variableLabels":{},"valueLabelNames":{},"valueLabels":{},"numberOfRecords":0,"numberOfVariables":0}"' _n
    file close `fh'
end


// ================================================================
// _dash_write_data <path> <varlist>  -- the data file both renderers read
// ================================================================
// Written from Python through the Stata Function Interface, by
// dash_render.py's _dash_write_stata_data, in jsonio's layout.  dash
// exported with jsonio, whose ado returns the JSON it wrote in a macro and
// expands it inside compound quotes: a string value, value label or
// variable label holding an unclosed compound quote or a lone backtick
// stopped every export with r(132) "too few quotes", and one holding the
// closing pair or a lone apostrophe with r(109) -- whatever the qualifier,
// so any dashboard over such data failed; and every strL arrived as "null"
// (measured 24sep2026; test_string_values.cscript).  sfi reads each value
// by value, so nothing the user typed passes through a macro here: the
// path and the names reach Python through Macro.getLocal(), never as code.
//
// Text that is not UTF-8 is read through Stata's ustrfix() -- each invalid
// sequence U+FFFD, as jsonio wrote it -- with a note naming the variable or
// label.  A binary strL, which is not text, is refused, r(198), naming the
// variable; the file is not written then.  The renderer's module is loaded
// once and kept, keyed by its path, size and time, so a second export in a
// session costs nothing to load.
program define _dash_write_data
    version 16.0
    gettoken _dw_path _dw_vars : 0
    // As Stata stores them, once each -- what jsonio's varlist gave.
    unab _dw_vars : `_dw_vars'
    local _dw_vars : list uniq _dw_vars
    _dash_require_python
    // The dash_render.py installed beside dash.ado first: the one the
    // package ships.  A renderer found earlier on the ado-path -- a
    // stand-in a test puts there to watch what it is handed -- replaces
    // the render, never the export (test_json_escaping.cscript runs
    // such a stand-in).  Then the ado-path, as the render looks.
    local _dw_py ""
    capture findfile dash.ado
    if _rc == 0 {
        mata: st_local("_dw_py", substr(st_global("r(fn)"), 1, ///
            strlen(st_global("r(fn)")) - strlen("dash.ado")) + "dash_render.py")
        capture confirm file `"`_dw_py'"'
        if _rc local _dw_py ""
    }
    if `"`_dw_py'"' == "" {
        _dash_find_render
        local _dw_py `"`r(fn)'"'
    }
    local _dw_err ""
    // One statement per line: a python: block inside a program fails to
    // load from the ado-path (see _dash_do_render).
    python: import sys, os, importlib.util
    python: from sfi import Macro as _dash_M
    python: _dash_rp = _dash_M.getLocal("_dw_py")
    python: _dash_st = os.stat(_dash_rp)
    python: _dash_key = (os.path.realpath(_dash_rp), _dash_st.st_size, _dash_st.st_mtime_ns)
    python: _dash_xm = sys.modules.get("_dash_render_export")
    // A single-line python: takes no compound statement, so the load is
    // written as expressions.  Every value is assigned: a bare expression
    // echoes its value into the log.  The module is kept only once it has
    // loaded.
    python: _dash_ok = _dash_xm is not None and getattr(_dash_xm, "_dash_export_key", None) == _dash_key
    python: _dash_xs = None if _dash_ok else importlib.util.spec_from_file_location("_dash_render_export", _dash_rp)
    python: _dash_xm = _dash_xm if _dash_ok else importlib.util.module_from_spec(_dash_xs)
    python: _dash_xr = _dash_ok or _dash_xs.loader.exec_module(_dash_xm)
    python: _dash_xm._dash_export_key = _dash_key
    python: sys.modules["_dash_render_export"] = _dash_xm
    python: _dash_M.setLocal("_dw_err", _dash_xm._dash_write_stata_data(_dash_M.getLocal("_dw_path"), _dash_M.getLocal("_dw_vars")))
    if `: length local _dw_err' {
        mata: _dash_say("err", st_local("_dw_err"), "", "")
        exit 198
    }
end


// ================================================================
// _dash_qual_gen <cmdname>  -- evaluate each distinct qualifier in Stata
//
// The table _dash_qual_rewrite and _dash_qual_take filled (dash_parse.mata)
// holds every distinct (if, in) pair the dashboard's plots, graphs and KPIs
// carry.  Each is evaluated here, once, against the data in memory in their
// order, into the byte variable __dashq<k>: 1 where Stata selects the row,
// 0 elsewhere -- `if' true where its expression is not zero, a missing
// value included, as Stata reads every qualifier.  The caller exports these
// with its variables and drops them at once, whether or not the export
// succeeded; the names come back in the caller's local _dash_qual_vars.
//
// Evaluating the qualifiers here is what makes the rows drawn Stata's: the
// renderers used to translate each into a pandas query, which read a
// missing value, a subscript, a function or a date otherwise than Stata
// (test_qualifier_in_stata.cscript).  A dashboard with no qualifier makes
// no variable.
//
// The __dash prefix is reserved for every column dash makes, not only the
// qualifier columns (G1, WP-28): data already holding a variable so named
// are refused, rc 110, rather than overwritten or exported beside a column
// of the same name -- the row identity __dash_row__, the marker-label and
// jitter columns dash.ado never sees are the renderer's own half of the
// same rule (_dash_take_qual_columns in dash_render.py).  The if is read
// by value -- macval() -- inside the
// parentheses _dash_qual_refusal proved it cannot leave, and the in is a
// range that check proved is one; a qualifier Stata cannot evaluate against
// the data now in memory (a variable dropped since the graph was
// registered) is refused with Stata's own error, as twoway refuses it, and
// nothing is left behind.
//
// A by() graph's qualifier that can depend on the order of the rows is
// evaluated in the order twoway evaluates it, sorted on the by()
// variables (_dash_qual_gen_by, below; _dash_qual_rewrite).
// ================================================================
program define _dash_qual_gen
    version 16.0
    args cmdname

    capture unab _dq_clash : __dash*
    if _rc == 0 {
        local _dq_first : word 1 of `_dq_clash'
        display as error "`cmdname': variable `_dq_first' is named with the prefix __dash, which is reserved for the columns dash makes (its qualifier columns __dashq#, its row identity __dash_row__ and its marker-label and jitter columns)."
        display as error "      Rename it first, for example: rename `_dq_first' newname"
        exit 110
    }

    local _dq_n = 0
    mata: _dash_qual_export()
    local made ""
    forvalues k = 1/`_dq_n' {
        quietly generate byte __dashq`k' = 0
        local made `made' __dashq`k'
    }
    // The data's own order: every column no by() graph sorts.
    forvalues k = 1/`_dq_n' {
        if `: length local _dq_by_`k'' continue
        local v "__dashq`k'"
        local _qx : copy local _dq_if_`k'
        local _qn : copy local _dq_in_`k'
        local _qr ""
        if `: length local _qn' {
            local _qr "in `_qn'"
        }
        if `: length local _qx' {
            capture noisily quietly replace `v' = 1 if (`macval(_qx)') `_qr'
        }
        else {
            capture noisily quietly replace `v' = 1 `_qr'
        }
        local rc = _rc
        if `rc' {
            drop `made'
            mata: _dash_say("err", "`cmdname': Stata cannot evaluate the qualifier ", ///
                strtrim((st_local("_qx") != "" ? "if " + st_local("_qx") : "") + " " + st_local("_qr")), ///
                " against the data in memory.")
            exit `rc'
        }
    }
    // A by() graph's columns, in its by() order: once per distinct order,
    // each column evaluated once (_dash_qual_gen_by).
    local _dq_nord = 0
    mata: _dash_qual_orders()
    forvalues j = 1/`_dq_nord' {
        capture noisily _dash_qual_gen_by "`cmdname'" `_dq_ord_`j''
        local rc = _rc
        if `rc' {
            drop `made'
            exit `rc'
        }
    }
    c_local _dash_qual_vars "`made'"
end

// ================================================================
// _dash_qual_gen_by <cmdname> <varlist>  -- the columns of one by() order
//
// Each __dashq<k> _dash_qual_export gives varlist as its order
// (_dash_qual_by_of named the variables, each a Stata name) is evaluated
// with the data sorted as twoway sorts a by() graph's: bygraph_g.class
// runs `bysort varlist (sortedby obsnum)', a stable sort on the by()
// variables -- ties keep the data's order, missing values sort last --
// and every plot's if and in, and the graph's, are evaluated once over
// the whole sorted data, _n never restarting within a group (measured
// 24sep2026 from each panel's serset; test_qualifier_in_stata.cscript
// QS-16..).  Only the by() variables the data hold are sorted on: the
// renderers facet on those alone.  sortpreserve gives the data their
// order back; a sort marks nothing changed.  The if is read by value, as
// in _dash_qual_gen, and each column is evaluated once.
// ================================================================
program define _dash_qual_gen_by, sortpreserve
    version 16.0
    gettoken cmdname order : 0
    local order : list retokenize order
    local _dq_n = 0
    mata: _dash_qual_export()
    local _sv ""
    foreach _b of local order {
        capture confirm variable `_b', exact
        if _rc == 0 local _sv `_sv' `_b'
    }
    if "`_sv'" != "" {
        tempvar _obs
        quietly generate double `_obs' = _n
        sort `_sv' `_obs'
    }
    forvalues k = 1/`_dq_n' {
        local _o : copy local _dq_by_`k'
        if !`: list _o == order' continue
        local v "__dashq`k'"
        local _qx : copy local _dq_if_`k'
        local _qn : copy local _dq_in_`k'
        local _qr ""
        if `: length local _qn' {
            local _qr "in `_qn'"
        }
        if `: length local _qx' {
            capture noisily quietly replace `v' = 1 if (`macval(_qx)') `_qr'
        }
        else {
            capture noisily quietly replace `v' = 1 `_qr'
        }
        local rc = _rc
        if `rc' {
            mata: _dash_say("err", "`cmdname': Stata cannot evaluate the qualifier ", ///
                strtrim((st_local("_qx") != "" ? "if " + st_local("_qx") : "") + " " + st_local("_qr")), ///
                " against the data in memory.")
            exit `rc'
        }
    }
end

// ================================================================
// _dash_report_ignored  — one note per command naming every option
//                         dash accepted but did not honour
// ================================================================
program define _dash_report_ignored
    version 16.0
    // Read by value (_dash_text_args): the unmatched options are the user's
    // text, and -args- cut foo("'x") bar(1) at its "', so bar() went
    // unnamed (test_json_escaping.cscript JSE-46).
    mata: _dash_text_args(0, 0, 0)
    local raw : copy local _dash_txt

    // `raw' mixes bare option names (pending, from the declared set) with the
    // verbatim text Stata could not match (unknown, from the trailing *).  Cut
    // each token at its opening parenthesis so the user sees option names, not
    // the values they supplied.
    // Walk the string with paren depth, so an option's argument is consumed
    // with its key.  `foreach tok of local raw' splits on whitespace and
    // parentheses are not grouping characters to it, so an unknown option
    // carrying a multi-word argument was reported as several options:
    //     dash scatter y x, addplot(line y2 x)
    //     dash: ignoring unsupported option(s): addplot() y2() x)()
    // naming two options that do not exist.
    mata: _dash_option_names("raw", "_dash_optnames")
    local raw : copy local _dash_optnames

    // Each name is cut, compared and joined in Mata, by value: a name is the
    // user's text -- a bare string dash could not match, "\$G", is one --
    // and in the quotes it was tested and copied in, a macro in it was
    // expanded again (test_json_escaping.cscript JSE-69).
    local seen " "
    local out  ""
    foreach tok of local raw {
        mata: st_local("tok", strtrim(st_local("tok")))
        mata: st_local("tok", strtrim(substr(st_local("tok"), 1, ///
            (strpos(st_local("tok"), "(") ? strpos(st_local("tok"), "(") - 1 : .))))
        if !`: length local tok' continue
        mata: st_local("dup", strofreal(strpos(st_local("seen"), " " + st_local("tok") + " ") > 0))
        if `dup' continue
        mata: st_local("seen", st_local("seen") + st_local("tok") + " ")
        // A weight is not an option and takes no argument: [aweight], not
        // aweight().
        mata: st_local("out", st_local("out") + " " + st_local("tok") + ///
            (substr(st_local("tok"), 1, 1) == "[" ? "" : "()"))
    }
    if !`: length local out' exit

    // The names are the user's text: shown as written, never as SMCL.
    mata: _dash_say("txt", "dash: ignoring unsupported option(s):", st_local("out"), "")
end

// ================================================================
// _dash_plot  — parse and route a plot definition (v2.0)
// ================================================================
program define _dash_plot
    version 16.0

    // ---- UTF-8 safety check ----
    // The command is read by value, here and at every command's gate: put
    // inside compound quotes in the Mata line, a text holding "' --
    // title(`"'90s cars"') -- ended them early, and the command stopped
    // with a Mata syntax error before anything was stored (measured
    // 24sep2026: r(3000) "'90s' found where almost anything else expected").
    mata: _dash_check_utf8(strtrim(st_local("0")))

    // ---- Split on || / () into segments + graph opts ----
    mata: _dash_split_segs(strtrim(st_local("0")))
    // Now locals _n_segs, _seg_1 .. _seg_N, _graph_opts_raw are set.

    // From here to the registry every piece of the command is the user's
    // text, and it is handed on by value.  Tested as  if `"`x'"' != "",  a
    // text holding "' -- title("'90s cars"), if make == "' or 1 or '" --
    // ended the quotes early, and the command stopped with r(109) or r(198),
    // or ran on with the test wrong (measured 24sep2026;
    // test_json_escaping.cscript JSE-42..49).  Copied as  local y `"`x'"'
    // or handed to a program on a command line, a macro in it was expanded
    // a second time (JSE-65..69).  So emptiness is `: length local', a copy
    // is `: copy local' or read in Mata, and a text handed to a program goes
    // through macval(), never on a one-line if, whose command Stata expands
    // again.
    local n_segs   = `_n_segs'
    local gopts_raw : copy local _graph_opts_raw

    // ---- The qualifier written between or after the plot groups ----
    // `dash (scatter y x) (line y x) if foreign==1': twoway applies it to
    // every plot (measured: 22 of auto's 74 in both), and dash.sthlp's
    // Syntax shows it, `dash plot_specs [if] [in]'.  The splitter used to
    // walk past it and drop it, so the graph drew every observation with
    // rc 0.  It is the graph's own qualifier now, read here with -syntax-,
    // which refuses what twoway refuses -- two ifs, a word or a plot group
    // after it -- before anything is parsed or reported.  Paren mode only:
    // in the || form a qualifier is the plot's own, as in twoway.
    local _gq_if ""
    local _gq_in ""
    if `: length local _graph_qual_raw' {
        _dash_graph_qualifier `macval(_graph_qual_raw)'
    }
    // The checks _dash_process_segment makes over a plot's sample -- a
    // weight's values, histogram's start() -- read the graph's qualifier
    // as part of that sample, as twoway does: `(lfit mpg weight
    // [fw=halfint]) if foreign==1' was checked on every row and refused,
    // r(401), where twoway draws it (WP-27; test_help_claims_6.cscript
    // HC6-56).  Handed over in two globals, set by value for every command
    // -- empty when there is no qualifier -- and dropped after the loop.
    mata: st_global("dash__gq_if", st_local("_gq_if"))
    mata: st_global("dash__gq_in", st_local("_gq_in"))
    // by() written after the plot groups' comma is the graph's: a plot's
    // sample is then counted panel by panel, which _dash_process_segment
    // leaves to the renderer (P1A-80).  Set below, once that comma's
    // options are read.
    global dash__g_by ""

    // ---- Initialise graph-level option accumulators ----
    foreach gk in title subtitle note caption name saving xtitle ytitle xlabel ///
          ylabel xline yline legend by xscale yscale aspectratio scheme ///
          plotregion graphregion bgcolor plotbgcolor link filter ytitle2 ///
          xtitle2 ylabel2 xlabel2 yscale2 xscale2 xsize ysize fxsize fysize ///
          scale text hover xtick ytick xmtick ymtick xmlabel ymlabel t1title ///
          t2title b1title b2title l1title l2title r1title r2title title2 ///
          subtitle2 zlabel ztitle zscale nodraw play replace {
        local g_`gk' ""
    }

    // ---- Parse graph-level opts from paren-mode suffix (if any) ----
    // _gund_acc: the graph-wide options dash does not declare given so far
    // (_dash_rep_und_scan's words), which twoway takes once from the whole
    // command -- after the comma, in any plot group or || segment.
    local _gund_acc ""
    local _rp_gund_out ""
    if `: length local gopts_raw' {
        mata: st_local("gopts_raw", _dash_route_axis2(st_local("gopts_raw")))
        _dash_parse_graph_opts , `macval(gopts_raw)'
        _dash_refuse_unbound _dash_parse_graph_opts `"`macval(gopts_raw)'"'
        // A second name() in the options after the comma, and whether they
        // gave one at all: a group's name() is then a second one too.
        mata: st_local("_g_name2", strofreal(_dash_has_name_opt(st_global("s(_unknown)"))))
        if `_g_name2' _dash_refuse_second_name
        // A plot option after the comma -- (lfit mpg weight), atobs -- or
        // an option in upper case: refused as twoway refuses it, even once,
        // naming the first word it does not take (_dash_refuse_foreign).
        _dash_refuse_foreign _dash_parse_graph_opts - `"`macval(gopts_raw)'"'
        // An option given twice after the comma, read as twoway reads it.
        _dash_opts_repeats _dash_parse_graph_opts - `"`macval(gopts_raw)'"'
        local _gund_acc : copy local _rp_gund_out
        mata: st_local("_g_names_n", strofreal(st_global("s(name)") != ""))
        foreach gk in title subtitle note caption name saving xtitle ytitle xlabel ///
              ylabel xline yline legend by xscale yscale aspectratio scheme ///
              plotregion graphregion bgcolor plotbgcolor link filter ytitle2 ///
              xtitle2 ylabel2 xlabel2 yscale2 xscale2 xsize ysize fxsize fysize ///
              scale text hover xtick ytick xmtick ymtick xmlabel ymlabel t1title ///
              t2title b1title b2title l1title l2title r1title r2title title2 ///
              subtitle2 zlabel ztitle zscale nodraw play replace {
            mata: st_local("_gv", st_global("s(" + st_local("gk") + ")"))
            if `: length local _gv' {
                // Kept apart and merged in after the segment loop: an option
                // written after the top-level comma applies to the GRAPH,
                // and twoway reads it after every plot's copy:
                //     twoway (scatter y x, title("INSIDE")) (line y x), title("AFTER")
                // stores "AFTER" -- measured from the saved .gph -- and
                // (scatter y x, title(A)), title(, color(red)) draws A in
                // red (measured 24sep2026 from the SVG export).
                local _gafter_`gk' : copy local _gv
            }
        }
        // The graph-level options dash cannot honour, captured HERE.
        //
        // _dash_parse_graph_opts sreturns them, and nothing read them: the
        // accumulator was initialised to "" just below, and the first thing
        // the segment loop does is `sreturn clear', which destroys s().  So
        // in paren mode -- `dash (scatter y x) (line y x), fxsize(30)' --
        // an unsupported graph-level option was dropped in complete
        // silence, which is the one thing the reporter exists to prevent,
        // while the identical option in comma mode was named correctly.
        mata: st_local("_dash_gopt_ignored", st_global("s(_pending)") + " " + st_global("s(_unknown)"))
    }

    local _dash_ignored_acc : copy local _dash_gopt_ignored
    if "`_g_names_n'" == "" local _g_names_n 0
    // The by() after the comma is held in _gafter_by until the segments
    // are merged: g_by, read here before, is still empty, so a plot group's
    // sample was counted as if there were no by() -- `(scatter mpg weight
    // if mpg > 1000) (lpoly mpg weight if mpg > 1000), by(foreign)' was
    // "no observations", r(2000), where twoway says "nothing to graph",
    // r(198) (P1A-83).
    mata: st_global("dash__g_by", st_local("_gafter_by"))
    // A by() given in any segment is the graph's too: twoway reads it from
    // every || segment and plot group before it draws a plot, so a plot in
    // a segment before the one that gives it -- `lfit mpg weight if _n==1
    // || scatter mpg weight, by(foreign)', rc 0 -- or after it is answered
    // panel by panel.  Read here, by value, before any segment is checked:
    // the other segments were checked as graphs of their own, r(2001)
    // "insufficient observations" (measured 24sep2026; test_parser.cscript
    // P1A-84).
    if !`: length global dash__g_by' {
        forvalues k = 1/`n_segs' {
            mata: st_local("_pre_by", _dash_seg_by(st_local("_seg_`k'")))
            if `: length local _pre_by' {
                mata: st_global("dash__g_by", st_local("_pre_by"))
                continue, break
            }
        }
    }

    // ---- Parse each plot segment ----
    // WP-19: a graph holds at most `plots' plot entries -- one per y
    // variable of a varlist, one for any other segment.  A single segment
    // over the limit is refused inside _dash_process_segment, before its
    // plot objects are built; the running total across segments is kept
    // here.  The limit is read once, before any segment is parsed, so a bad
    // dash_max_plots is refused first.  Refused here, nothing is registered.
    _dash_limit, name(plots)
    local _dash_plot_lim  = r(value)
    local _dash_plot_ceil = r(ceiling)
    local _dash_nplots    = 0
    local plots_json ""
    // The graph-level options twoway takes once from the whole command:
    // a second copy, in another plot group, another || segment or after
    // the comma, is "option scheme() not allowed", r(198) (measured
    // 24sep2026 for each; name() has its own check, above and below).
    local _g_unique "saving scheme aspectratio xsize ysize scale fxsize fysize nodraw play"
    foreach gk of local _g_unique {
        local _gseen_`gk' = `: length local _gafter_`gk'' > 0
    }
    forvalues k = 1/`n_segs' {
        local seg : copy local _seg_`k'

        local _seg_ignored_out ""
        local _seg_gund_out    ""
        local _seg_nplots_out  1
        local _seg_named_out   0
        local _seg_if_out      ""
        local _seg_in_out      ""
        local _seg_bands_out   0
        local _seg_vars_out    ""
        local _seg_wvar_out    ""
        foreach gk in title subtitle note caption name saving xtitle ytitle xlabel ///
              ylabel xline yline legend by xscale yscale aspectratio scheme ///
              plotregion graphregion bgcolor plotbgcolor link filter ytitle2 ///
              xtitle2 ylabel2 xlabel2 yscale2 xscale2 xsize ysize fxsize fysize ///
              scale text hover xtick ytick xmtick ymtick xmlabel ymlabel t1title ///
              t2title b1title b2title l1title l2title r1title r2title title2 ///
              subtitle2 zlabel ztitle zscale nodraw play replace {
            local _sg_`gk' ""
        }
        _dash_process_segment `"`macval(seg)'"' _pt_k _json_k `n_segs'
        // Kept for the by() answer below, by value.
        local _byq_pt_`k' `_pt_k'
        local _byq_if_`k' : copy local _seg_if_out
        local _byq_in_`k' : copy local _seg_in_out
        local _byq_bd_`k' `_seg_bands_out'
        local _byq_vv_`k' `_seg_vars_out'
        local _byq_wv_`k' `_seg_wvar_out'

        // A graph takes one name(): a second, in another group or ||
        // segment than the first, or beside the one after the comma, is
        // refused as twoway refuses it -- before this segment's name() can
        // overwrite the first and before anything is registered.
        local _g_names_n = `_g_names_n' + `_seg_named_out'
        if `_g_names_n' > 1 _dash_refuse_second_name

        // A graph-wide option dash does not declare, given in this segment
        // and in an earlier one or after the comma: refused as twoway
        // refuses it -- (scatter y x, notitling) (line y x, notitling) is
        // "option notitling not allowed", r(198) (measured 24sep2026).
        if `: length local _seg_gund_out' {
            mata: _dash_rep_und_cross("_gund_acc", "_seg_gund_out")
            if `: length local _rp_refuse' _dash_refuse_repeat `_rp_refuse'
        }

        local _dash_nplots = `_dash_nplots' + `_seg_nplots_out'
        if `_dash_nplots' > `_dash_plot_lim' {
            // The graph's total is known only once its last segment is in.
            if `k' == `n_segs' {
                _dash_plot_cap_refuse `_dash_plot_lim' `_dash_plot_ceil' `_dash_nplots'
            }
            else _dash_plot_cap_refuse `_dash_plot_lim' `_dash_plot_ceil'
        }

        if `: length local _seg_ignored_out' {
            mata: st_local("_dash_ignored_acc", st_local("_dash_ignored_acc") + " " + st_local("_seg_ignored_out"))
        }

        // _dash_process_segment hands back this segment's graph-level
        // options as _sg_* locals; each is merged into its g_* accumulator
        // as twoway merges a repeated option -- the last copy of most, the
        // copies joined for title() legend() xlabel() and the like -- and a
        // second copy of one twoway takes once is refused as twoway
        // refuses it.  The key is a word of the list and the values are
        // read by value, in Mata.
        foreach gk in title subtitle note caption name saving xtitle ytitle xlabel ///
              ylabel xline yline legend by xscale yscale aspectratio scheme ///
              plotregion graphregion bgcolor plotbgcolor link filter ytitle2 ///
              xtitle2 ylabel2 xlabel2 yscale2 xscale2 xsize ysize fxsize fysize ///
              scale text hover xtick ytick xmtick ymtick xmlabel ymlabel t1title ///
              t2title b1title b2title l1title l2title r1title r2title title2 ///
              subtitle2 zlabel ztitle zscale nodraw play replace {
            if !`: length local _sg_`gk'' continue
            if `: list gk in _g_unique' {
                if `_gseen_`gk'' {
                    display as error "option `gk'() not allowed"
                    display as error "      A graph takes one `gk'(); this command gives it more than once, which twoway refuses as well."
                    exit 198
                }
                local _gseen_`gk' 1
            }
            mata: _dash_rep_merge_locals(st_local("gk"), "g_`gk'", "_sg_`gk'", "g_`gk'")
        }

        if `k' > 1 local plots_json `"`plots_json',"'
        local plots_json `"`plots_json'`_json_k'"'
    }

    macro drop dash__gq_if dash__gq_in dash__g_by

    // ---- An after-comma option comes after every segment's ----
    // Merged after the segment loop, as twoway reads it: the last copy of
    // a rightmost option, so the after-comma one outranks a segment's, and
    // the copies joined for a merged one.  Only keys the after-comma parse
    // set are merged, so a graph that names an option only inside a
    // segment keeps that value.
    foreach gk in title subtitle note caption name saving xtitle ytitle xlabel ///
              ylabel xline yline legend by xscale yscale aspectratio scheme ///
              plotregion graphregion bgcolor plotbgcolor link filter ytitle2 ///
              xtitle2 ylabel2 xlabel2 yscale2 xscale2 xsize ysize fxsize fysize ///
              scale text hover xtick ytick xmtick ymtick xmlabel ymlabel t1title ///
              t2title b1title b2title l1title l2title r1title r2title title2 ///
              subtitle2 zlabel ztitle zscale nodraw play replace {
        if `: length local _gafter_`gk'' {
            mata: _dash_rep_merge_locals(st_local("gk"), "g_`gk'", "_gafter_`gk'", "g_`gk'")
        }
    }

    // ---- Validate the graph-level values (WP-15) ----
    // After the restore above, so the value checked is the one that will
    // be written, and before the report below, so a refused value is never
    // half-reported.  The rules live in _dash_option_rules; a normalised
    // value (an expanded variable name) is written back to its g_ local.
    _dash_option_rules
    foreach _vrule of local _dash_rules_graph {
        local _veq   = strpos("`_vrule'", "=")
        local _vopt  = substr("`_vrule'", 1, `_veq' - 1)
        local _vspec = substr("`_vrule'", `_veq' + 1, .)
        local _vval : copy local g_`_vopt'
        if !`: length local _vval' continue
        _dash_validate_value "dash" "`_vopt'" "`_vspec'" `"`macval(_vval)'"' ""
        local g_`_vopt' : copy local _dash_vnorm
    }
    // legend()'s direction words, refused as twoway refuses them -- here for
    // the legend() written after the graph's comma, which no segment's
    // validation sees (WP-23).  A block, not a one-line if: Stata expands a
    // one-line if's command again, macval() or not (JSE-69).
    if `: length local g_legend' {
        _dash_check_legend `"`macval(g_legend)'"'
    }

    // ---- A by() graph: its panels, as twoway answers them ----
    // Measured 24sep2026 with the console binary (graph.ado, and
    // bygraph_g.class RunGraph; test_parser.cscript P1A-83).  The panels
    // are the by() groups -- the by() variables not missing, unless
    // missing is given -- holding a row the graph's qualifier selects, or,
    // with none and one plot, that plot's if and in; with several plots
    // and no graph qualifier, every group of the data.  None is "nothing
    // to graph", r(198).  Each panel is then drawn plot by plot, and the
    // first plot that cannot be drawn in it decides:
    //   fpfit, fpfitci   its if and in select no row of the panel: "(note:
    //                    fracpoly could not fit model)", then "observation
    //                    numbers out of range", r(198) -- the command stops
    //   mspline, mband   the same, with no bands(): "bands must be between
    //                    1 and 200", r(198)
    //   lpoly, lpolyci   one observation in the panel's sample, or none: the
    //                    panel is left out, in silence
    //   lfit, lfitci     one: the panel is left out, after "(note:  regress
    //                    could not fit model)" and "insufficient
    //                    observations" (the renderer gives them)
    //   kdensity         one: the panel is left out, in silence
    // The sample counts rows whose plotted variables are not missing and
    // whose weight is above zero.  With every panel left out, "nothing to
    // graph", r(198).  The renderer leaves the same panels out
    // (_dash_by_panel_dropped) and answers every other one
    // (GlyphMapper._mark_unfit, _mark_silent).  dash drew every panel, rc
    // 0.  An immediate plot or a function reads no observations, and a
    // graph holding one is left as it was.  The qualifiers are run as
    // -syntax- read them, by value, once each.
    _dash_plottype_families
    local _by_lit 0
    forvalues k = 1/`n_segs' {
        if `: list _byq_pt_`k' in _pt_literal' local _by_lit 1
    }
    if `: length local g_by' & !`_by_lit' {
        // The by() variables and missing, read from the validated value
        // through a string scalar (_dash_by_parts).
        tempname _by_txt
        mata: st_strscalar(st_local("_by_txt"), st_local("g_by"))
        _dash_by_parts `_by_txt'
        // Every qualifier here is evaluated as twoway evaluates a by()
        // graph's: with the data sorted, stably, on the by() variables --
        // `bysort varlist (sortedby obsnum)' in bygraph_g.class -- and over
        // the whole sorted data, so `if _n == 1', `in 1/10' and `if mpg >
        // mpg[_n-1]' count rows in that order; by(, total)'s Total panel
        // evaluates them again in the data's own order (measured 24sep2026
        // from each panel's serset; test_qualifier_in_stata.cscript
        // QS-16..).  They were evaluated in the data's order alone, so on
        // data not sorted on the by() variables the panels were counted
        // over other rows than twoway draws.  _dash_qual_mark sorts, reads
        // the qualifier by value from a scalar, and gives the data their
        // order back.  Pass s is the by() order; pass t, under total alone,
        // the data's.
        local _by_passes "s"
        if `_by_total' local _by_passes "s t"
        tempname _by_sif _by_sin
        // The plots that can stop the command or leave a panel out, and
        // their rules.
        local _by_rules ""
        local _by_ks ""
        local _by_fpfam "fpfit fpfitci"
        local _by_bdfam "mspline mband"
        local _by_d0 "lpoly lpolyci"
        local _by_d1 "kdensity"
        local _by_n1 "lfit lfitci"
        forvalues k = 1/`n_segs' {
            local _pk `_byq_pt_`k''
            local _rule ""
            if `: list _pk in _by_fpfam' local _rule "R"
            if `: list _pk in _by_bdfam' & !`_byq_bd_`k'' local _rule "R"
            if `: list _pk in _by_d0' local _rule "D0"
            if `: list _pk in _by_d1' local _rule "D1"
            if `: list _pk in _by_n1' local _rule "N1"
            if "`_rule'" == "" continue
            local _by_ks `_by_ks' `k'
            local _by_rules `_by_rules' `_rule'
            local _by_seg_`: word count `_by_ks'' `k'
        }
        foreach _bp of local _by_passes {
            local _ord ""
            if "`_bp'" == "s" local _ord `_by_vars'
            // The rows the graph's qualifier selects.
            tempvar _by_gq_`_bp'
            quietly gen byte `_by_gq_`_bp'' = 0
            mata: st_strscalar(st_local("_by_sif"), st_local("_gq_if"))
            mata: st_strscalar(st_local("_by_sin"), st_local("_gq_in"))
            _dash_qual_mark `_by_gq_`_bp'' 1 `_by_sif' `_by_sin' `_ord'
            // The rows that make the panels: the graph's qualifier, or the
            // one plot's own.
            tempvar _by_base_`_bp'
            quietly gen byte `_by_base_`_bp'' = `_by_gq_`_bp''
            if `n_segs' == 1 & !`: length local _gq_if' & !`: length local _gq_in' {
                if `: length local _byq_if_1' | `: length local _byq_in_1' {
                    quietly replace `_by_base_`_bp'' = 0
                    mata: st_strscalar(st_local("_by_sif"), st_local("_byq_if_1"))
                    mata: st_strscalar(st_local("_by_sin"), st_local("_byq_in_1"))
                    _dash_qual_mark `_by_base_`_bp'' 1 `_by_sif' `_by_sin' `_ord'
                }
            }
            // Each such plot's sample.
            local _by_chk_`_bp' ""
            foreach k of local _by_ks {
                local _rule : word `: list posof "`k'" in _by_ks' of `_by_rules'
                tempvar _by_c`k'_`_bp'
                quietly gen byte `_by_c`k'_`_bp'' = 0
                mata: st_strscalar(st_local("_by_sif"), st_local("_byq_if_`k'"))
                mata: st_strscalar(st_local("_by_sin"), st_local("_byq_in_`k'"))
                _dash_qual_mark `_by_c`k'_`_bp'' `_by_gq_`_bp'' `_by_sif' `_by_sin' `_ord'
                if "`_rule'" != "R" {
                    // Rows with a plotted variable missing, or a weight
                    // missing or not above zero, are not in the sample.
                    foreach _v of local _byq_vv_`k' {
                        quietly replace `_by_c`k'_`_bp'' = 0 if missing(`_v')
                    }
                    if `: length local _byq_wv_`k'' {
                        quietly replace `_by_c`k'_`_bp'' = 0 if missing(`_byq_wv_`k'') | `_byq_wv_`k'' <= 0
                    }
                }
                local _by_chk_`_bp' `_by_chk_`_bp'' `_by_c`k'_`_bp''
            }
        }
        local _by_mopt ""
        if `_by_miss' local _by_mopt "missing"
        // by(, total): the Total panel is one more panel, answered as the
        // groups are -- `lfit mpg weight if _n==1 | _n==60, by(foreign,
        // total)' draws it alone, rc 0 (P1A-84) -- over the rows pass t
        // selects.
        if `_by_total' {
            local _by_mopt "`_by_mopt' total tpanel(`_by_base_t')"
            if `: length local _by_chk_t' local _by_mopt "`_by_mopt' tcheck(`_by_chk_t')"
        }
        local _by_copt ""
        if `: length local _by_chk_s' local _by_copt "check(`_by_chk_s') rules(`_by_rules')"
        _dash_by_panels `_by_vars', panel(`_by_base_s') `_by_mopt' `_by_copt'
        if r(n) == 0 {
            display as error "nothing to graph"
            exit 198
        }
        if r(refuse) > 0 {
            local k `_by_seg_`r(refuse)''
            if `: list _byq_pt_`k' in _by_fpfam' {
                display as text "(note:  fracpoly could not fit model)"
                display as error "observation numbers out of range"
            }
            else {
                display as error "bands must be between 1 and 200"
            }
            exit 198
        }
        if r(kept) == 0 {
            // lfit and lfitci on one observation say so as they stop.
            if r(d1note) {
                display as text "(note:  regress could not fit model)"
                display as text "insufficient observations"
            }
            display as error "nothing to graph"
            exit 198
        }
    }

    // ---- Report unsupported options, once, naming every one ----
    // dash accepts every twoway option so a pasted command never aborts; an
    // option it cannot honour is named here instead of vanishing.  One note
    // per command listing all of them.
    // saving() is honoured on the immediate route only: a named graph is
    // written by `dash build, saving()'.  Measured 22sep2026: name(g3)
    // saving(x.html) registered g3, wrote nothing and said nothing.  Named
    // here rather than on a pending list, because the immediate route
    // honours it and the note must not say otherwise there.
    if `: length local g_name' & `: length local g_saving' {
        mata: st_local("_dash_ignored_acc", st_local("_dash_ignored_acc") + " saving")
    }
    // replace after the comma, as dash build takes it, lets the one-line
    // form write over the file saving() names (_dash_saving_clobber).  It is
    // folded into saving() as twoway's own saving(name, replace), which
    // _dash_render_immediate reads, and never written to the spec.  With no
    // saving(), or on a named graph, which writes nothing, it has nothing
    // to replace and is named in the note.  The text is joined in Mata, by
    // value.
    if `: length local g_replace' {
        if `: length local g_saving' & !`: length local g_name' {
            mata: st_local("g_saving", st_local("g_saving") + ///
                (ustrregexm(st_local("g_saving"), ",[ \t]*replace[ \t]*$") ? "" : ", replace"))
        }
        else {
            mata: st_local("_dash_ignored_acc", st_local("_dash_ignored_acc") + " replace")
        }
        local g_replace ""
    }
    if `: length local _dash_ignored_acc' {
        _dash_report_ignored `"`macval(_dash_ignored_acc)'"'
    }

    // ---- The graph's name, as it will be registered ----
    // name()'s text may end in ", replace", which tells the registry to
    // overwrite; it is not part of the name.  The stored graph carries the
    // name alone, split by the rule _dash_register_graph applies, because
    // both renderers key every item by the stored name: written as
    // "g1, replace" it matched nothing layout(), tabs(), link() or exclude()
    // named (P20-33).  _dash_register_graph is still handed name()'s own
    // text, below, and decides replace from that text alone.
    //
    // name[, replace] is letters, digits, _, blanks and a comma, and a text
    // holding anything else is no name: it is left whole, for
    // _dash_register_graph to refuse, and never put on _dash_name_split's
    // command line, where a macro in it is expanded again and an =exp
    // evaluated -- name(\`=filewrite(...)') wrote its file (measured
    // 24sep2026; test_json_escaping.cscript JSE-68).  The KPI registrar
    // reads name() the same way.
    local _g_name_text : copy local g_name
    if `: length local g_name' {
        mata: st_local("_g_name_ok", strofreal(!ustrregexm(st_local("g_name"), "[^A-Za-z0-9_, \t]")))
        if `_g_name_ok' {
            _dash_name_split `"`g_name'"' g_name _g_name_replace
        }
    }

    // ---- Assemble graph_options JSON ----
    // Build JSON from the accumulated g_* locals
    local gopts_json "{"
    local gfirst = 1
    foreach gk in title subtitle note caption name saving xtitle ytitle xlabel ///
          ylabel xline yline legend by xscale yscale aspectratio scheme ///
          plotregion graphregion bgcolor plotbgcolor link filter ytitle2 ///
          xtitle2 ylabel2 xlabel2 yscale2 xscale2 xsize ysize fxsize fysize ///
          scale text hover xtick ytick xmtick ymtick xmlabel ymlabel t1title ///
          t2title b1title b2title l1title l2title r1title r2title title2 ///
          subtitle2 zlabel ztitle zscale nodraw play replace {
        local gv : copy local g_`gk'
        if `: length local gv' {
            _dash_json_str `"`macval(gv)'"' _gjv
            if !`gfirst' local gopts_json `"`gopts_json',"'
            local gopts_json `"`gopts_json'"`gk'":"`_gjv'""'
            local gfirst = 0
        }
    }
    local gopts_json `"`gopts_json'}"'

    // ---- Assemble full single-graph JSON ----
    // Promote if_expr / in_expr from the first plot segment to the graph level.
    // The renderer looks for graph-level "if_expr"/"in_expr" in graph_options or
    // at the top level.  BOTH renderers also read each plot's own qualifier and
    // apply it to that layer alone -- the saved dashboard has always done so,
    // and the served one does since WP-10 -- so the promotion below exists only
    // to give a single-segment command a graph-level qualifier as well.
    // We use _dash_json_get_str to extract the first occurrence from plots_json —
    // this correctly handles \" escape sequences inside the value.
    local if_expr ""
    local in_expr ""
    // A qualifier written after the plot groups IS the graph's: both
    // renderers apply the graph's qualifier to every layer and a layer's
    // own on top of it, as twoway does -- `(scatter y x if mpg>25)
    // (line y x) if foreign==1' draws 7 foreign cars and 22 (measured).
    // The layers keep their own; nothing is promoted over it.
    if `: length local _gq_if' | `: length local _gq_in' {
        local if_expr : copy local _gq_if
        local in_expr : copy local _gq_in
    }
    // Otherwise promote only when there is ONE segment, in which case the
    // qualifier was written on the command as a whole.  With several
    // segments each layer carries its own if_expr and the renderer applies
    // it per layer; promoting the FIRST layer's qualifier here used to apply
    // it to every layer, so
    //   dash (scatter y x) (scatter y x if foreign)
    // filtered both layers or neither.
    else if `n_segs' == 1 {
        mata: _dash_json_get_str(`"`plots_json'"', "if_expr", "if_expr")
        mata: _dash_json_get_str(`"`plots_json'"', "in_expr", "in_expr")
    }
    _dash_json_str `"`macval(if_expr)'"' _jif_top
    _dash_json_str `"`macval(in_expr)'"' _jin_top

    local graph_json `"{"plots":[`plots_json'],"graph_options":`gopts_json',"if_expr":"`_jif_top'","in_expr":"`_jin_top'"}"'

    // ---- Route: named or immediate ----
    // name()'s own text, ", replace" and all: _dash_register_graph splits
    // it by the same rule and needs the sub-option to decide whether an
    // existing name may be overwritten.  The whole command, handed over as
    // well, is stored for the record and never read for a replace.
    //
    // The three go to _dash_register_graph in string scalars, read there by
    // value.  They were three compound-quoted arguments read with -args-,
    // so a command holding "' ended the second early and the next of its
    // words became the third: after the plot groups  if make != "'x"
    // registered, rc 0, with the graph stored as the one word x and the
    // command cut at the quote (measured 24sep2026;
    // test_json_escaping.cscript JSE-45, JSE-47).  The immediate route
    // reads the graph JSON alone, which holds no apostrophe, backtick or
    // dollar sign; the command was handed to it as well, read by nothing,
    // and on its command line an =exp in it was evaluated (JSE-67).
    local graph_name : copy local _g_name_text

    if `: length local graph_name' {
        tempname _rg_name _rg_json _rg_spec
        mata: st_strscalar(st_local("_rg_name"), st_local("graph_name"))
        mata: st_strscalar(st_local("_rg_json"), st_local("graph_json"))
        mata: st_strscalar(st_local("_rg_spec"), st_local("0"))
        _dash_register_graph `_rg_name' `_rg_json' `_rg_spec'
    }
    else {
        _dash_render_immediate `"`graph_json'"'
    }
end


// ================================================================
// _dash_browser_wanted  — should this render open a browser window?
//
// r(open) is 1 only when no saving() was given, $dash_nobrowser is empty,
// and the spec does not carry Stata's own nodraw.  nodraw means "build it
// but do not display it", and opening a window is displaying it; it is a
// flag, so its serialised value is the word itself, and an unset flag
// serialises as an empty string, which must NOT suppress.
// ================================================================
program define _dash_browser_wanted, rclass
    version 16.0
    syntax , SPEC(string asis) [SAVing(string)]
    local open = 1
    if `"`saving'"' != "" local open = 0
    if "${dash_nobrowser}" != "" local open = 0
    if strpos(`"`spec'"', `""nodraw":"nodraw""') > 0 local open = 0
    return scalar open = `open'
end

// ================================================================
// _dash_registry_nodraw  — does any registered graph carry nodraw?
//
// dash.sthlp says a graph's nodraw keeps the browser shut on `dash build'
// as nobrowser does; measured 22sep2026 it did not -- the registry's
// graph_options were never read for it.  r(nodraw) is 1 when one is.
// ================================================================
program define _dash_registry_nodraw, rclass
    version 16.0
    local hit = 0
    foreach _rn in ${dash_graph_registry} {
        if strpos(`"${dash_json_`_rn'}"', `""nodraw":"nodraw""') > 0 local hit = 1
    }
    return scalar nodraw = `hit'
end

// ================================================================
// _dash_dashboard_browser [, nobrowser]  — does a dashboard of the whole
// registry open a browser window?
//
// The one rule `dash build' and `dash serve' decide by.  r(open) is 1
// unless the command's own nobrowser option was given, $dash_nobrowser is
// set (an empty global is an unset one), or a registered graph carries
// Stata's nodraw.  r(flag) is what `dash serve' hands the launcher:
// "--no-browser" when r(open) is 0, else empty.
//
// `dash serve' used to decide from its nobrowser option alone, so the
// global dash.sthlp says "suppresses the window for a whole session" did
// not: `global dash_nobrowser 1' then `dash serve, port(5006)' launched
// the app without --no-browser, and dash_render.py's launcher added --show
// and opened a window.  A registered graph's nodraw, which kept `dash
// build' shut, did not keep `dash serve' shut either.
// ================================================================
program define _dash_dashboard_browser, rclass
    version 16.0
    syntax [, NOBRowser]
    _dash_registry_nodraw
    local open = ("`nobrowser'" == "" & "${dash_nobrowser}" == "" ///
                  & r(nodraw) == 0)
    return scalar open = `open'
    if `open' return local flag ""
    else      return local flag "--no-browser"
end

// ================================================================
// _dash_open_page , path(string) [os(string) dryrun]  -- open a saved page
// in the system's browser: the one opener the one-line form and `dash
// build' share, once their decider has said a window is wanted.
//
// r(cmd) is the shell command: open '<path>' on a Mac, xdg-open '<path>'
// on Unix, start "" "<path>" on Windows, where start reads its first
// quoted argument as a window title.  r(os) is the platform it is for,
// os() or, when that is omitted, this machine's.  r(opened) is 1 when the
// command went to the shell.  dryrun builds and returns the command and
// runs nothing, and so does a set $dash_nobrowser, whichever caller asks.
//
// The two callers each carried their own three shell lines, and the
// Windows line ran only where Stata reports Windows, so no test ran it;
// the checks read dash.ado's text and passed with that branch unable to
// run at all.  With the platform an argument and dryrun, each platform's
// command is checked on any machine (test_serve_browser.cscript SB-13..20).
//
// The path is quoted for the shell that reads it, and built and run by
// value: in Mata, then through _stata() with macro expansion off, since a
// `$' or a backquote in the text `shell' is given is expanded again first
// (measured 24sep2026: shell `c' ran a single-quoted /tmp/q$PROBEGz.html
// as /tmp/q.html).  bash, which Stata's shell runs on a Mac and Unix, takes
// everything inside single quotes as written but the apostrophe itself,
// which is written '\''.  cmd.exe takes & ; and spaces inside double
// quotes as written, but a double quote there would end the argument; no
// Windows file name can hold one, so such a path is refused.  So is a line
// break, which would end the command, and a platform other than the three
// Stata reports.  The callers pass paths _dash_validate_path has already
// cleared; these refusals hold the program to itself.
// ================================================================
program define _dash_open_page, rclass
    version 16.0
    syntax , PATH(string) [OS(string) DRYrun]

    // A Mac is a Mac whichever binary runs.  The console binary reports
    // c(os) as "Unix" (c(machine_type) "Mac (Apple Silicon)", measured
    // 23sep2026), and dash ran xdg-open there, which macOS does not have --
    // "/bin/bash: xdg-open: command not found", no window, and no word of
    // where the file went.  os() is measured by its length, never read
    // inside quotes before it is known to be one of the three.
    local _op_osl : length local os
    if `_op_osl' == 0 {
        local os "`c(os)'"
        if "`c(os)'" == "MacOSX" | substr("`c(machine_type)'", 1, 3) == "Mac" {
            local os "MacOSX"
        }
    }
    mata: st_local("_op_known", strofreal(anyof(("MacOSX", "Unix", "Windows"), st_local("os"))))
    if `_op_known' == 0 {
        display as error "dash: cannot open a page on that platform; os() is MacOSX, Unix or Windows."
        exit 198
    }
    mata: st_local("_op_nl", strofreal(strpos(st_local("path"), char(10)) + strpos(st_local("path"), char(13)) > 0))
    if `_op_nl' {
        display as error "dash: a path holding a line break cannot be handed to the shell; the page was not opened."
        exit 198
    }

    if "`os'" == "Windows" {
        mata: st_local("_op_dq", strofreal(strpos(st_local("path"), char(34)) > 0))
        if `_op_dq' {
            display as error "dash: a Windows path cannot hold a double quote; the page was not opened."
            exit 198
        }
        mata: st_local("cmd", "start " + char(34) + char(34) + " " + char(34) + st_local("path") + char(34))
    }
    else {
        local _op_prog = cond("`os'" == "MacOSX", "open", "xdg-open")
        mata: st_local("cmd", st_local("_op_prog") + " " + char(39) + subinstr(st_local("path"), char(39), char(39) + char(92) + char(39) + char(39), .) + char(39))
    }

    local opened 0
    if "`dryrun'" == "" & "${dash_nobrowser}" == "" {
        mata: st_local("_op_rc", strofreal(_stata("shell " + st_local("cmd"), 0, 1)))
        local opened 1
    }
    return local os "`os'"
    return local cmd : copy local cmd
    return scalar opened = `opened'
end

// ================================================================
// _dash_register_graph  — store named graph in global registry
// ================================================================
// ================================================================
// _dash_drop_item  — retire every global a registry item owns
//
// Graphs and KPIs share one registry and one namespace, so replacing an
// item of one kind with the other has to take the loser's globals with it.
// A name left carrying both a `dash_json_' and a `dash_kpi_' marker is
// drawn as the KPI -- _dash_prepare_spec's graph loop passes over any
// entry with a KPI marker -- so the item the user just registered would
// vanish from the dashboard.
//
// Only the item's own globals, by EXACT name: dash_json_<name> and
// dash_spec_<name>, the marker dash_kpi_<name> and the fields
// dash_kpi_<name>__<field>.  `macro drop dash_kpi_g1*' would also take
// g10's, and a prefix took other names' globals: replacing KPI a deleted
// KPI a_b's (measured 23sep2026 at 9f48cf7).  See _dash_item_globals and
// _dash_kpi_fields in dash_parse.mata.
// ================================================================
program define _dash_drop_item
    version 16.0
    args name

    mata: _dash_item_globals("`name'", "_dash_item_kill")
    foreach _g of local _dash_item_kill {
        capture macro drop `_g'
    }
end


// ================================================================
// _dash_name_split  -- a graph's name() text as a name and a replace flag
//
// Usage:  _dash_name_split `"`raw'"' <name_macro> <flag_macro>
// After:  <name_macro> holds the name; <flag_macro> is 1 when the text
//         ended in ", replace", else 0.  Both are set in the caller.
//
// twoway's name(name[, replace]).  Stata's name(string) captures the whole
// of "g1, replace", so the sub-option has to be split off before the text
// is used as a name -- and every place that uses it must split it the same
// way.  _dash_register_graph did, and registered g1; _dash_plot did not,
// and wrote "g1, replace" into the stored graph as its name.  Both renderers
// key every item by that stored name, so the registry said g1 while the
// dashboard knew only "g1, replace" (measured 23sep2026 at 9f48cf7):
// layout(g2:1,1 g1:1,2) warned that g1 was not registered and drew it
// below g2, tabs(A: g1) built no tabs, link(g1 g2) left two sources,
// exclude(g1) did not protect it, and a plain build drew it last.  Both
// programs now read the name here (test_adversarial.cscript P20-33,
// test_registry_collision.cscript REG-17), and so does _dash_kpi, which
// kept a copy of the regex of its own until 23sep2026.
//
// The flag is the only word on replace.  _dash_register_graph also
// searched the whole command for name(...,replace) when the flag said no,
// so a re-used name whose title or note held those characters overwrote
// the graph it named (test_registry_collision.cscript REG-29 to REG-36).
//
// Spaces around the comma are allowed, as twoway allows them: name(g1
// ,replace) and name( g1 , replace ) are g1 and a replace.  Anything else
// after the comma -- rep, REPLACE, replace x -- is left in the name, where
// the name check refuses it, as twoway refuses it.  The regex is the one
// _dash_register_graph always used, unchanged.  regexm() follows the
// CALLER's user version; the pattern has no bounded repetition, so both
// engines read it, but below 18 the class [ \t] is a space, a backslash or
// a t rather than a space or a tab (measured 23sep2026).  Spaces work under
// both (test_caller_version.cscript CV-02).
// ================================================================
program define _dash_name_split
    version 16.0
    args raw name_macro flag_macro

    local _nm = strtrim(`"`raw'"')
    local _rep = 0
    if regexm(`"`_nm'"', "^([^,]+)[ \t]*,[ \t]*replace[ \t]*$") {
        local _nm = strtrim(regexs(1))
        local _rep = 1
    }
    c_local `name_macro' `"`_nm'"'
    c_local `flag_macro' `_rep'
end

// ================================================================
// _dash_refuse_second_name  -- a command gives name() more than once
// ================================================================
// twoway refuses a second name() wherever it is written -- in another plot
// group, after a paren command's comma, in another || segment or in the
// same option list, spelled name() or nam(), naming the same graph or two --
// with "option name() not allowed", r(198).  Measured 24sep2026: only when
// its FIRST name() names a graph it already holds, without replace, does it
// say "graph g1 already exists", r(110), instead, and when the first says
// replace it drops that graph before it refuses.  dash took one of the two
// -- the last group's, the one after the comma over a group's, the first of
// one list -- and named the other in its ignoring note, so a command twoway
// refuses replaced a registered graph, or registered a name twoway never
// would (test_registry_collision.cscript REG-37 to REG-41).  Refused here
// in twoway's words, before anything is registered or dropped.  The words
// hold no user text.
program define _dash_refuse_second_name
    version 16.0
    display as error "option name() not allowed"
    display as error "      A graph takes one name(); this command gives it more than once, which twoway refuses as well."
    exit 198
end


// ================================================================
// _dash_fn_refuse  -- a function layer calling a function Stata lacks
// ================================================================
// twoway refuses `twoway function y = nosuchfunction(x)' -- "error in
// expression: nosuchfunction(x)", r(133) -- and so it refuses any call of a
// name that is no Stata function (system(x), Sin(x), mpg(x)), wherever it
// stands in the expression (measured 24sep2026).  dash registered the
// layer, rc 0, and the renderer drew it empty with a note.
//
// Called as _dash_fn_refuse `"<expression>"', read by value
// (_dash_text_args).  Each name written directly before
// a `(' (_dash_fn_names, at most 100 of them) is put to Stata as a call with
// 32 arguments of 1, under capture: Stata answers r(133), "unknown
// function", only for a name that is no function, and checks a known
// function's arguments before it runs it, so none is evaluated -- the
// random-number state is unchanged (measured: runiform() and rnormal()
// with 32 arguments are r(198), c(rngstate) the same) -- save the pure
// ones that take any number (max(), inlist()).  The name is a Stata name
// (_dash_fn_names checks it), so it is safe on the command line, and the
// expression is echoed only through _dash_say, at most 200 characters of
// it.  A function Stata has but
// the renderer does not draw -- normal(x) -- is not refused here: twoway
// draws it, and the renderer's own check reports the layer it leaves empty.
//
// An operand written with blanks before a `(' (_dash_fn_space_call) is
// refused too: Stata never reads sin (x) as a call.  twoway refuses
// `function y = sin (x)' -- "error in expression:  sin (x)", r(111), sin
// looked for as a variable -- and r(198) when the name is one the data has
// (mpg, or mp for it), x, _n, _N or _pi, or the operand is a number, a
// string or a closing parenthesis; with tabs alone between the name and
// the `(' it is r(133), an unknown function (measured 24sep2026).  Stata
// reports whichever it meets first: nosuch(x) + sin (x) is r(133), sin (x)
// + nosuch(x) r(111), so only the calls written before the operand are
// asked about first.  dash drew sin (x) as sin(x), rc 0.  2 * (x) and x +
// (1) have an operator before the `(' and are drawn.  The name put to
// -confirm- is a Stata name (_dash_fn_space_call reads only letters,
// digits and _), and the expression is echoed only through _dash_say.
program define _dash_fn_refuse
    version 16.0
    mata: _dash_text_args(0, 0, 0)
    mata: st_local("_fn_sp", _dash_fn_space_call(st_local("_dash_txt")))
    local _fn_upto : copy local _dash_txt
    if `: length local _fn_sp' {
        local _fn_pos : word 2 of `_fn_sp'
        mata: st_local("_fn_upto", substr(st_local("_dash_txt"), 1, `_fn_pos' - 1))
    }
    mata: st_local("_fn_names", _dash_fn_names(st_local("_fn_upto"), 100))
    local _fn_args "1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1"
    foreach _fn of local _fn_names {
        capture local _fn_z = `_fn'(`_fn_args')
        if _rc == 133 {
            // twoway's words; an expression of more than 200 characters
            // is shown in its first 197, so a refusal is never a page long.
            mata: _dash_say("err", "error in expression: ", ///
                (ustrlen(st_local("_dash_txt")) > 200 ? ///
                usubstr(st_local("_dash_txt"), 1, 197) + "..." : st_local("_dash_txt")), "")
            mata: _dash_say("err", "      unknown function ", st_local("_fn"), "()")
            exit 133
        }
    }
    if !`: length local _fn_sp' exit
    local _fn_kind : word 1 of `_fn_sp'
    local _fn_nm : word 3 of `_fn_sp'
    mata: _dash_say("err", "error in expression: ", ///
            (ustrlen(st_local("_dash_txt")) > 200 ? ///
            usubstr(st_local("_dash_txt"), 1, 197) + "..." : st_local("_dash_txt")), "")
    if "`_fn_kind'" == "T" {
        display as error "      unknown function `_fn_nm'<tab>()"
        exit 133
    }
    local _fn_rc 198
    if "`_fn_kind'" == "N" {
        capture confirm variable `_fn_nm'
        if _rc & !inlist("`_fn_nm'", "x", "_n", "_N", "_pi") local _fn_rc 111
    }
    display as error "      A name or value and a parenthesis written apart are two operands to Stata, not a call."
    exit `_fn_rc'
end

// ================================================================
// _dash_refuse_unbound <parser> `"<options>"'  -- an option dash declares
//                      whose value Stata's -syntax- cannot bind
// ================================================================
// -syntax- leaves a declared option in the parser's catch-all when it
// cannot bind the value to the declared string: jitter(x"' _dup(3) "INJ"
// `") and msize() alike (measured 24sep2026).  dash then named it as an
// unsupported option -- "ignoring unsupported option(s): jitter()" -- and
// registered the graph without it, where twoway refuses the command:
// "type mismatch", r(109), for a value holding "', and "parentheses do not
// balance", r(198), for one like a" "b (measured on sixteen values;
// _dash_unbound_cands keeps the rule).  Refused here with twoway's return
// code, naming the option, before anything is registered.
//
// Called right after <parser> (_dash_parse_plot_opts or
// _dash_parse_graph_opts) read <options>, with its s() in place.  Each
// candidate from s(_unknown) is put to the parser twice, under capture:
// alone, as written -- if it binds then, it was a second copy of an option
// the list already gave, which -syntax- leaves to the catch-all and twoway
// accepts, so it stays in the note -- and as <name>(x), which binds only
// when the parser declares <name> with a value.  A flag written with a
// value, horizontal(x), binds neither way and stays in the note.  At most
// 50 candidates are put to the parser (each costs two parses); any beyond
// are named in the note as before.  When nothing is refused, <options> is
// parsed once more so the caller finds the s() it had.  The option text is
// read by value (_dash_text_args) and only reaches a command line through
// macval(); the name is a Stata name (_dash_unbound_cands checks it), and
// the message is printed through _dash_say.
program define _dash_refuse_unbound
    version 16.0
    mata: _dash_text_args(1, 0, 0)
    local parser : copy local _dash_a1
    local opts : copy local _dash_txt
    if !inlist("`parser'", "_dash_parse_plot_opts", "_dash_parse_graph_opts") exit
    mata: _dash_unbound_cands(st_global("s(_unknown)"), 50)
    if `_ru_n' == 0 exit
    local refuse 0
    forvalues i = 1/`_ru_n' {
        capture `parser' , `macval(_ru_tok`i')'
        if _rc continue
        mata: st_local("_ru_alone", strofreal(strtrim(st_global("s(_unknown)")) != ""))
        if !`_ru_alone' continue
        capture `parser' , `_ru_nm`i''(x)
        if _rc continue
        mata: st_local("_ru_decl", strofreal(strtrim(st_global("s(_unknown)")) == ""))
        if `_ru_decl' {
            local refuse `i'
            continue, break
        }
    }
    if `refuse' {
        local nm : copy local _ru_nm`refuse'
        local rc `_ru_rc`refuse''
        local why = cond(`rc' == 109, "type mismatch", "parentheses do not balance")
        mata: _dash_say("err", "dash: option ", st_local("nm"), ///
            "() has a value Stata cannot read, as twoway reads it: " + st_local("why") + ".")
        exit `rc'
    }
    `parser' , `macval(opts)'
end


// ================================================================
// _dash_opts_repeats <parser> <ptype> `"<options>"'  -- an option given
//                    more than once, read as twoway reads it
// ================================================================
// twoway takes most options more than once: the last copy of a rightmost
// one (mcolor(red) mcolor(blue) draws blue, and mc(red) mcolor(blue) too),
// the copies merged for title(), xlabel(), legend(), xscale(), by(),
// xline() and the like, and a unique one -- scheme(), saving(), xsize(), a
// bare sort, bwidth() on kdensity -- refused, "option scheme() not
// allowed", r(198) (measured 24sep2026 from twoway's SVG export; the rules
// are in dash_parse.mata beside _dash_rep_merge).  -syntax- bound the
// FIRST copy and left the others to the catch-all, which named them as
// unsupported -- or, for title(A) title(B), bound the second to title2()
// and the second xlabel() to xlabel2(), the second axis.
//
// Called right after <parser> read <options> (and _dash_refuse_unbound and
// the name() check ran), with its s() in place.  When the list may give an
// option twice (_dash_rep_scan: the catch-all is not empty, or one typed
// name is another's prefix), each distinct typed name, at most 100, is put
// to the parser alone, and the s() it sets is the option it spells
// (_dash_rep_keyof); _dash_rep_reduce writes the list again with one copy
// of each option, or names a unique one given twice, and the list is
// parsed once more so the caller finds the s() of the list twoway reads.
// Otherwise nothing is parsed again.  <ptype> is the plot type, or - for
// the graph parser.  The option text is read by value (_dash_text_args)
// and reaches a command line only through macval(); the refusal names an
// option by a Stata name.
program define _dash_opts_repeats
    version 16.0
    mata: _dash_text_args(2, 0, 0)
    local parser : copy local _dash_a1
    local ptype : copy local _dash_a2
    local opts : copy local _dash_txt
    if !inlist("`parser'", "_dash_parse_plot_opts", "_dash_parse_graph_opts") exit
    if "`ptype'" == "-" local ptype ""
    // First the options dash does not declare -- named in the note, one
    // copy at a time -- that twoway takes once: atobs twice on lfit is
    // "option atobs not allowed", r(198) (_dash_rep_und_tab).  The
    // graph-wide ones the list gives go back to the caller as
    // _rp_gund_out, which counts them across the command's lists.
    mata: _dash_rep_und_scan(st_local("opts"), st_local("ptype"))
    c_local _rp_gund_out : copy local _rp_gund
    if `: length local _rp_refuse' _dash_refuse_repeat `_rp_refuse'
    // Two kernels on lpoly, lpolyci or kdensity -- gaussian epan2, or
    // gaussian beside kernel() -- refused in twoway's words once no
    // repeated option is (_dash_kernel_clash): twoway refuses bwidth(1)
    // bwidth(2) gaussian epan2 for bwidth() first.
    mata: st_local("_rp_kern", _dash_kernel_clash(st_local("opts"), st_local("ptype")))
    mata: _dash_rep_scan(st_local("opts"), strtrim(st_global("s(_unknown)")) != "", 100)
    if !`_rp_go' {
        if `: length local _rp_kern' _dash_refuse_kernel `_rp_kern' `ptype'
        exit
    }
    forvalues i = 1/`_rp_n' {
        local _rp_key`i' ""
        sreturn clear
        capture `parser' , `macval(_rp_tok`i')'
        if _rc continue
        local _rp_sm : s(macros)
        mata: st_local("_rp_key`i'", _dash_rep_keyof(st_local("_rp_sm")))
    }
    mata: st_local("_rp_out", _dash_rep_reduce(st_local("opts"), st_local("ptype")))
    if `: length local _rp_refuse' _dash_refuse_repeat `_rp_refuse'
    if `: length local _rp_kern' _dash_refuse_kernel `_rp_kern' `ptype'
    sreturn clear
    `parser' , `macval(_rp_out)'
end


// _dash_refuse_repeat <name>  -- refuse a second copy of an option twoway
// takes once, in twoway's words and with its code: "option atobs not
// allowed", r(198).  <name> is the copy twoway names, a Stata name as
// typed, "()" after it when it took a value (_dash_rep_reduce,
// _dash_rep_und_scan); it is echoed as text.
program define _dash_refuse_repeat
    version 16.0
    args nm
    mata: _dash_say("err", "option ", st_local("nm"), " not allowed")
    display as error "      twoway takes this option once; this command gives it more than once."
    exit 198
end


// _dash_refuse_kernel <kind> <ptype>  -- two kernels in one option list of
// lpoly, lpolyci or kdensity (_dash_kernel_clash), refused in twoway's
// words, which differ on kdensity, with its code, r(198).
program define _dash_refuse_kernel
    version 16.0
    args kind ptype
    if "`kind'" == "one" {
        display as error "only one kernel may be specified"
    }
    else {
        local pre ""
        if "`ptype'" == "kdensity" local pre "option "
        display as error "`pre'kernel(): old syntax may not be combined with new syntax"
        display as error "      A kernel written as an option of its own, such as gaussian, and kernel() may not be given together."
    }
    exit 198
end


// _dash_refuse_foreign <parser> <ptype> `"<options>"'  -- a word twoway
// refuses even once, where dash would name it in its note.
// ================================================================
// twoway's option names are lower case: ATOBS, MCOLOR(red), Title(x) and
// dash's own HOVER() are no options, "option MCOLOR() not allowed",
// r(198).  And after the plot groups' comma twoway takes graph options
// only: (lfit mpg weight), atobs -- or mcolor(red), kernel(), lo -- is
// "option atobs not allowed", r(198), even once, though clegend(), below
// and logging are taken there.  Either way twoway names the first word of
// the list it does not take: (lfit mpg weight), bogus atobs is "option
// bogus not allowed" (measured 24sep2026).  dash named every one in its
// note and drew the graph.
//
// Called right after <parser> read <options>, with its s() in place, and
// before _dash_opts_repeats; <ptype> is the plot type, or - for the list
// after the paren-mode comma.  When the catch-all may hold such a word
// (_dash_foreign_scan), each option word twoway does not take on dash's
// behalf is put to the parser alone: one the parser takes (a repeat
// -syntax- left to the catch-all, or an option of dash's own, such as
// hover()) is skipped.  The first word left is the one twoway names, and
// the command is refused when some word left is in upper case, or -- after
// the comma -- is a plot option: a row of _dash_rep_und_tab for a plot, or
// a word the plot parser takes alone.  Otherwise the list is parsed again,
// so the caller finds its s() as it left it, and the note names the words
// as before.  The option text is read by value (_dash_text_args); the
// refusal names an option by a Stata name, echoed as text.
program define _dash_refuse_foreign
    version 16.0
    mata: _dash_text_args(2, 0, 0)
    local parser : copy local _dash_a1
    local ptype : copy local _dash_a2
    local opts : copy local _dash_txt
    if !inlist("`parser'", "_dash_parse_plot_opts", "_dash_parse_graph_opts") exit
    local graph = ("`ptype'" == "-")
    if `graph' local ptype ""
    mata: _dash_foreign_scan(st_local("opts"), st_local("ptype"), st_global("s(_unknown)"), `graph')
    if !`_fs_go' exit
    local first ""
    local trig 0
    forvalues i = 1/`_fs_n' {
        if `_fs_acc`i'' continue
        sreturn clear
        capture `parser' , `macval(_fs_tok`i')'
        if _rc continue
        mata: st_local("_fs_u", strofreal(strtrim(st_global("s(_unknown)")) != ""))
        if !`_fs_u' continue
        if !`: length local first' local first : copy local _fs_nm`i'
        local trig = `_fs_uc`i'' | (`graph' & `_fs_plot`i'')
        if `graph' & !`trig' {
            sreturn clear
            capture _dash_parse_plot_opts , `macval(_fs_tok`i')'
            if !_rc {
                mata: st_local("trig", strofreal(strtrim(st_global("s(_unknown)")) == ""))
            }
        }
        if `trig' continue, break
    }
    if `trig' {
        mata: _dash_say("err", "option ", st_local("first"), " not allowed")
        if `graph' {
            display as error "      After the plot groups' comma twoway takes graph options only; a plot's own options go inside its parentheses, and option names are lower case."
        }
        else display as error "      twoway does not take this option; its option names are lower case."
        exit 198
    }
    sreturn clear
    `parser' , `macval(opts)'
end


// _dash_register_graph <name text> <graph JSON> <command>, each argument the
// name of a string scalar holding it.  All three are read by value: they
// were three compound-quoted arguments read with -args-, and a command
// holding "' ended the second early, its next word becoming the third --
// if make != "'x" after the plot groups registered with rc 0, the graph
// stored as the one word x and the command cut at the quote (measured
// 24sep2026; test_json_escaping.cscript JSE-45, JSE-47).
program define _dash_register_graph
    version 16.0
    args name_sc json_sc spec_sc
    mata: st_local("name", st_strscalar(st_local("name_sc")))
    mata: st_local("json_spec", st_strscalar(st_local("json_sc")))
    mata: st_local("raw_spec", st_strscalar(st_local("spec_sc")))

    // Split off a ", replace" sub-option BEFORE validating the name.  Stata's
    // name(string) captures the whole of "g1, replace", which then failed the
    // name regex below -- so name(g1, replace) was impossible, and the error
    // message further down told the user to type the very syntax that could
    // not work.  _dash_plot splits the stored graph's name by the same rule,
    // so the name registered here is the name the stored JSON carries, and
    // the flag is the only word on replace (see below).  raw_spec, the
    // whole command, is stored and never read for it.
    //
    // Only a text that can be name[, replace] -- letters, digits, _, blanks
    // and a comma -- is split; any other is refused below as the name it is
    // not.  Split, it was expanded again on _dash_name_split's command line:
    // name(\$m) registered under whatever $m held, and an =exp in it was
    // evaluated (measured 24sep2026; test_json_escaping.cscript JSE-68).
    mata: st_local("_nm_raw_ok", strofreal(!ustrregexm(st_local("name"), "[^A-Za-z0-9_, \t]")))
    local replace_flag 0
    if `_nm_raw_ok' {
        _dash_name_split `"`name'"' _nm replace_flag
        local name `"`_nm'"'
    }

    // Validate name format.  No bounded repetition such as {0,31}: regexm()
    // follows the CALLER's user version, and below 18 it runs Stata's old
    // engine, which does not know it -- every name was refused in a do-file
    // that began `version 16' (test_caller_version.cscript).  The length is
    // checked on its own, and it is 22, not 32: the name becomes part of the
    // globals dash_json_<name> and dash_spec_<name>, and a global's name is
    // at most 32 characters.  A 23- to 32-character name used to pass here
    // and then fail on the global with Stata's bare "invalid name".  Until
    // it passes, the name is read through a string scalar: in plain quotes a
    // name holding a double quote ended them -- name(`"q"7"') stopped with
    // r(303), "equation [a-zA-Z_] not found" (measured 24sep2026;
    // test_json_escaping.cscript JSE-47, JSE-68).  After, it is letters,
    // digits and underscores.
    tempname NS
    mata: st_strscalar(st_local("NS"), st_local("name"))
    if !`_nm_raw_ok' | !regexm(scalar(`NS'), "^[a-zA-Z_][a-zA-Z0-9_]*$") | strlen(scalar(`NS')) > 22 {
        // Echoed as text: a refused name may hold anything, and shown raw
        // name(a{bf:X}) printed a bold X -- the user's text drawn as SMCL.
        mata: st_local("_name_safe", ustrregexra(usubstr( ///
            st_local("name"), 1, 40), "[^A-Za-z0-9_.\-]", "?"))
        display as error "dash: invalid graph name '`_name_safe''. " ///
            "Names must start with a letter or underscore, contain only " ///
            "letters, digits, and underscores, and be at most 22 characters."
        exit(198)
    }

    // Two underscores in a row are dash's own.  The renderer names what it
    // generates with them -- a by() graph g1's panels are g1__by__0,
    // g1__by__1, ..., a KPI's per-panel cards the same, and the saved
    // layout(bs) page keys its tab strip and filters __tabs__ and __fw_0__
    // -- so a name holding them took one of those places without a word
    // (measured 23sep2026: name(g1__by__0) beside by(foreign) name(g1) was
    // drawn as g1's first panel).  A rule of its own, after the format
    // check, so the message names the one rule broken; by now the name is
    // letters, digits and underscores.  The renderer refuses such a name in
    // a spec that did not come through here (_dash_named_once).
    if strpos("`name'", "__") {
        mata: _dash_say("err", "dash: graph name '", st_local("name"), ///
            "' holds two underscores in a row, which dash keeps for the " + ///
            "names it generates, such as a by() graph's panels. " + ///
            "Choose a name without __.")
        exit(198)
    }

    // _all is link()'s word for every graph: a graph named _all made
    // link(_all g2) build, linking every graph when saved and two when
    // served (measured 23sep2026).  Stata itself keeps the word.
    if "`name'" == "_all" {
        display as error "dash: graph name '_all' is the word link(_all) " ///
            "uses for every graph. Choose another name."
        exit(198)
    }

    // name()'s own text, split above, is the only thing that decides a
    // replace.  This program also searched the WHOLE command for
    // name(...,replace) whenever that text held none -- lower-cased and
    // anywhere, rename( included -- so a re-used name overwrote the graph
    // it named when a title, note, caption, text(), an if qualifier or an
    // unsupported NAME() option held those characters.  Measured 23sep2026
    // at ad13a0f: rc 0 in silence, and a graph given a KPI's name deleted
    // the card, where twoway refuses every one with r(110).  The search was
    // this program's first way of reading replace (25mar2026, the first
    // commit): meant to read name()'s value, it read the whole command, and
    // the name check before it refused any name() text holding a replace,
    // so it only ever acted on text outside name().
    // Stata's name(string) captures name()'s whole text on every route --
    // a plot's options, a paren command's graph options, any || segment --
    // so the search decided nothing that text did not, except to say yes
    // where it said no: text elsewhere, or a second name() dash does not
    // read, which twoway refuses as well (test_registry_collision.cscript
    // REG-29 to REG-36).

    // Check if name already in registry
    local registry = "${dash_graph_registry}"
    local already  = 0
    local ntokens : word count `registry'
    forvalues k = 1/`ntokens' {
        if "`:word `k' of `registry''" == "`name'" local already = 1
    }

    if `already' == 1 & `replace_flag' == 0 {
        display as error "dash: graph name '`name'' already exists. " ///
            "Use name(`name', replace) to overwrite."
        exit(198)
    }

    // WP-19: the registry holds at most `graphs' graphs and KPI cards.  A
    // NEW name past the limit is refused here, before any global is set or
    // retired; a name already registered is a replace and never counts.
    _dash_graph_cap `already'

    // Retire whatever held this name before.  Without this a graph that
    // replaced a KPI kept the KPI's marker, and _dash_prepare_spec then
    // skipped the graph -- the user replaced an item and lost both.
    if `already' == 1 {
        _dash_drop_item "`name'"
    }

    // Store spec and JSON, by value: through compound quotes the command
    // was expanded again, and an =exp in it evaluated (JSE-67).
    mata: st_global("dash_spec_" + st_local("name"), st_local("raw_spec"))
    mata: st_global("dash_json_" + st_local("name"), st_local("json_spec"))

    // Update registry
    if `already' == 0 {
        if "${dash_graph_registry}" == "" {
            global dash_graph_registry "`name'"
        }
        else {
            global dash_graph_registry "${dash_graph_registry} `name'"
        }
    }

    display as text "dash: graph '`name'' registered."
end


// ================================================================
// _dash_render_immediate  — single-graph render path
// ================================================================
program define _dash_render_immediate
    version 16.0
    // The graph JSON alone; the command, handed over as well, was read by
    // nothing (see _dash_plot).
    args json_spec

    // ---- Extract saving() path from JSON ----
    local saving_path ""
    local open_browser = 0

    // Read it as JSON, not as text.  This used to slice the raw document at
    // the first quote after "saving":" -- but the value had been written by
    // _dash_json_str, so every backslash in it was doubled and the result was
    // then used as a FILESYSTEM PATH.  Measured: saving("<dir>a\b.html")
    // returned rc 0 and wrote "<dir>a\\b.html"; the file the user asked for
    // did not exist.  Every Windows saving() path on this route landed
    // somewhere other than where it was meant to.  Slicing at the first quote
    // also truncated any path containing one, since \" is a quote in the
    // document but not in the value.
    //
    // _dash_json_get_str already does this correctly, escapes and all -- it
    // is the same reader dash uses for every other spec value.
    mata: _dash_json_get_str(st_local("json_spec"), "saving", "saving_path")

    if `: length local saving_path' {
        // twoway accepts saving(name), saving(name.gph) and
        // saving(name, replace).  Normalise all three to a .html path BEFORE
        // validating: validation demands a .html suffix, and it used to run
        // before the suffix was appended, so every twoway-shaped saving()
        // aborted with r(198).  The path is the user's text, read through
        // the string scalar P until the validator has judged it: a macro in
        // it was expanded again here, so saving("\$D/x.html") wrote the page
        // where $D pointed (measured 24sep2026; test_json_escaping.cscript
        // JSE-68).
        tempname P
        local replace ""
        mata: st_strscalar(st_local("P"), strtrim(st_local("saving_path")))
        if regexm(scalar(`P'), "^(.+)[ \t]*,[ \t]*replace[ \t]*$") {
            scalar `P' = strtrim(regexs(1))
            local replace = "replace"
        }
        // The .gph note is shown only once the path is validated, and
        // through _dash_say: it was displayed first, inside plain quotes,
        // so a double quote in the name ended the string and what followed
        // ran as display directives, and a brace drew SMCL.
        local _gph = 0
        if regexm(lower(scalar(`P')), "\.gph$") {
            scalar `P' = substr(scalar(`P'), 1, strlen(scalar(`P')) - 4)
            local _gph = 1
        }
        if !regexm(lower(scalar(`P')), "\.html$") scalar `P' = scalar(`P') + ".html"
        mata: st_local("saving_path", st_strscalar(st_local("P")))
        _dash_validate_path `"`macval(saving_path)'"'
        local saving_path `"`_dash_vpath'"'   // `~/' expanded, if it was there
        if `_gph' {
            mata: _dash_say("txt", "dash: saving() writes HTML, not a Stata .gph; using ", st_local("saving_path"), "")
        }
        // A file that is there already is kept unless replace was given --
        // saving(name, replace), twoway's form, or replace after the comma,
        // dash build's, which _dash_plot folds into saving() -- and a
        // directory in its place is never written (_dash_saving_clobber).
        // This route wrote over the user's file with rc 0 (measured
        // 24sep2026 by WP-24; test_path_validation.cscript PV-22..27).  The
        // directory is checked first: one that does not exist holds no file.
        _dash_saving_dir `"`saving_path'"'
        _dash_saving_clobber `"`saving_path'"' "`replace'" "dash"
    }
    else {
        tempfile saving_path_tmp
        local saving_path = "`saving_path_tmp'.html"
        local open_browser = 1
    }

    if !regexm(lower("`saving_path'"), "\.html$") {
        local saving_path = "`saving_path'.html"
    }

    // ---- The qualifiers, evaluated in Stata ----
    // Each if/in pair of the graph and its plots becomes the column that
    // holds Stata's answer (_dash_qual_rewrite, _dash_qual_gen); the spec
    // carries the column's name and no qualifier text.  The graph as
    // registered is kept for a graph that needs no data, below.
    local _json_orig : copy local json_spec
    local _dq_err ""
    mata: _dash_qual_reset()
    mata: st_local("json_spec", _dash_qual_rewrite(st_local("_json_orig"), "_dq_err", 1))
    if `: length local _dq_err' {
        mata: _dash_say("err", "dash: the graph's qualifier cannot be evaluated: ", st_local("_dq_err"), ".")
        exit 198
    }

    // ---- Determine variables needed ----
    local needed_vars ""
    mata: _dash_extract_vars(`"`json_spec'"', "needed_vars")

    // ...including the ones named only in by().  A qualifier's variables
    // are not exported: its answer is (_dash_qual_gen), and the rewritten
    // spec holds no qualifier text for _dash_extract_qual_vars to read.
    // _dash_extract_vars reads plot-variable keys only, so the one-line form
    //     dash scatter mpg weight, by(foreign) saving(out.html)
    // serialised no `foreign' column at all: the renderer had nothing to
    // facet on, drew ONE panel instead of two and carried no value labels,
    // while the identical graph through `dash build' -- which has always
    // called _dash_extract_qual_vars -- drew two labelled panels.  Two
    // serialisation paths, one of them incomplete.
    local _qualvars ""
    mata: _dash_extract_qual_vars(`"`json_spec'"', "_qualvars")
    foreach _qv of local _qualvars {
        capture confirm variable `_qv'
        if _rc == 0 {
            if !`: list _qv in needed_vars' local needed_vars "`needed_vars' `_qv'"
        }
    }
    local needed_vars = strtrim("`needed_vars'")

    // The literal family -- scatteri, pci, pcarrowi and function -- takes
    // literal coordinates or an expression rather than variables, so having
    // no varlist is correct for them; this guard used to reject those plot
    // types outright.  The list comes from _dash_plottype_families, so a
    // literal type added there is admitted here: this list was written out
    // by hand and did not know pcarrowi (WP-22).  pcscatter was on it, from
    // when it was parsed as literals; it takes four variables and has no
    // need.
    //
    // A graph that names no variable is drawn when EVERY plot in it is of
    // that family (_dash_spec_types_in), and its data file holds no
    // variable (_dash_empty_data).  One literal plot used to be enough, so
    // a spec holding a scatteri beside a line with no variables was drawn
    // and the render died in Python, r(7102) -- a spec dash no longer
    // writes (P1A-69), but this program reads whatever spec it is handed
    // (P1A-74).  And the file held ONE observation of the first variable
    // in memory, a placeholder no layer read, so with no data in memory
    // `dash scatteri 1 2 3 4, saving(f)' was refused here, where twoway
    // draws it (measured 24sep2026; P1A-72).
    _dash_plottype_families
    local _varfree = 0
    if "`needed_vars'" == "" {
        mata: st_local("_varfree", strofreal(_dash_spec_types_in( ///
            st_local("json_spec"), st_local("_pt_literal"))))
        if !`_varfree' {
            display as error "dash: no variables identified in plot specification."
            exit(198)
        }
        // No data are exported, so no qualifier column: the literal family
        // draws its own values, which twoway's if and in do not reach.
        mata: _dash_qual_reset()
        mata: st_local("json_spec", _dash_qual_rewrite(st_local("_json_orig"), "_dq_err", 0))
    }

    // ---- Write the data file (_dash_write_data) ----
    tempfile data_json_path spec_json_path

    // Always export ALL rows for the needed variables.  Do NOT pre-filter with
    // if/in qualifiers here: multiple plots in the same graph can have different
    // qualifiers, and applying only the first plot's qualifier would silently
    // discard rows needed by other plots.  Each distinct qualifier -- the
    // graph's, promoted to the graph JSON by _dash_plot, and each plot's own --
    // is exported instead as the 0/1 column that holds Stata's answer
    // (_dash_qual_gen), and both renderers select a layer's rows with it.

    // The data file is written from Python through sfi (_dash_write_data):
    // jsonio, which wrote it until 24sep2026, is no longer needed.

    // ---- Resource limits (WP-19), before anything is exported ----
    // Every dash_max_* global the session has set is validated here -- a
    // bad one is refused before the export, not after it -- and travels to
    // the renderer as build_options.limits.  Then the size of what is
    // about to be embedded, every observation of every variable in
    // needed_vars, is held to the cells limit, and the text in its string
    // variables to the bytes limit.  All come before the file is written,
    // so a refusal leaves the user's data exactly as it was.
    _dash_limits_json
    local _dash_lim_json `"`r(json)'"'
    local _dash_nvars : word count `needed_vars'
    // Each qualifier column is embedded with the data, and counted.
    mata: _dash_qual_export()
    // GAPS2 G3: the one-line route draws a single graph and never takes
    // a server option (_dash_plot's own syntax has none), so the reduced
    // accounting always applies -- unless the graph names no variable at
    // all (the literal family, `_varfree'), which is never a computed-only
    // type either, so the plain count below is exactly today's.
    local _ri_gc = -1
    local _ri_gt = 1
    if !`_varfree' {
        _dash_limit, name(by_groups)
        local _ri_byg = r(value)
        mata: st_local("_ri_gc", strofreal(_dash_computed_cells( ///
            st_local("json_spec"), st_nobs(), `_ri_byg', ///
            "`_pt_univar' `_pt_onefit'")))
        mata: st_local("_ri_gt", strofreal(_dash_graph_touched( ///
            "", st_local("json_spec"), "", "", "")))
    }
    if `_ri_gc' >= 0 & !`_ri_gt' {
        _dash_cell_cap 0 "" `_ri_gc'
    }
    else {
        _dash_cell_cap `=`_dash_nvars' + `_dq_n''
    }
    _dash_byte_cap `needed_vars'

    // Collect display formats.  Each travels in the spec's formats map;
    // the data file carries every number as stored, whatever its format.
    _dash_formats_json "`needed_vars'" _dash_fmt_json _dash_date_vars
    local _dash_jrc = 0
    if `_varfree' {
        _dash_empty_data "`data_json_path'"
    }
    else {
        // The qualifier columns, made first: a qualifier Stata refuses
        // stops here, before any format is touched.  Dropped the moment
        // the file is written, or fails to be.  Estimates in memory are
        // held meanwhile, and restored when this program ends: with an
        // e(sample) present, jsonio named the first variable made after
        // it "(e)" rather than __dashq1, and the renderer refused the
        // spec (measured 24sep2026; test_qualifier_in_stata.cscript QS-15).
        local _dash_qual_vars ""
        if `_dq_n' > 0 {
            tempname _dash_eh
            _estimates hold `_dash_eh', restore nullok
        }
        _dash_qual_gen "dash"
        // Captured, so the qualifier columns are dropped when the export
        // fails too.  The writer reads each stored value whatever its
        // display format, so no format is touched (until 24sep2026 jsonio
        // needed each date variable %12.0g for the call, and a failed
        // export left it so: test_program_coverage.cscript PC-11).  Its
        // message is still shown and its code returned; no value is
        // expanded on the way (test_string_values.cscript).
        capture noisily _dash_write_data "`data_json_path'" `needed_vars' `_dash_qual_vars'
        local _dash_jrc = _rc
        if "`_dash_qual_vars'" != "" {
            capture drop `_dash_qual_vars'
        }
    }
    if `_dash_jrc' exit `_dash_jrc'

    // The file itself is the witness that the export ran.
    capture confirm file "`data_json_path'"
    if _rc != 0 {
        display as error "dash: the data could not be written. " ///
            "Check that all variables exist and the data is loaded."
        exit(198)
    }

    // ---- Write spec JSON to temp file ----
    // Carry the session confidence level so the renderer does not have to
    // assume 95.  A per-plot level() overrides it.
    local _dash_lvl = c(level)
    local _dash_sess_scheme = c(scheme)
    _dash_json_str `"`_dash_sess_scheme'"' _sess_scheme_esc
    local master_json = `"{"graphs": [`json_spec'], "build_options": {"layout": "1 1", "theme": "", "session_scheme": "`_sess_scheme_esc'", "level": "`_dash_lvl'", "formats": `_dash_fmt_json', "limits": `_dash_lim_json'}}"'

    tempname fh
    // quietly: `write replace' notes a missing file, and this path is a
    // fresh tempfile, so the note fired on every successful render.
    quietly file open `fh' using "`spec_json_path'", write replace text
    file write `fh' `"`master_json'"'
    file close `fh'

    // ---- Locate dash_render.py ----
    _dash_find_render
    local render_py `"`r(fn)'"'

    // ---- Invoke Python renderer via helper ----
    // (python:...end must be in a dedicated program; see _dash_do_render)
    _dash_do_render, spec("`spec_json_path'") data("`data_json_path'") ///
        output("`saving_path'") renderpy("`render_py'")

    // ---- Open in browser if no explicit saving() ----
    // The same suppression as `dash build'.  This path sets open_browser
    // only when no saving() was given, but a do-file run in batch still does
    // not want a browser window.
    // One decision, in a program a certification script can call without
    // launching anything: saving() given, $dash_nobrowser set, or the
    // graph's own nodraw each keep the window shut.  nodraw is honoured
    // here, and is therefore NOT on either _dash_pending list: the note
    // used to say "ignoring unsupported option(s): nodraw()" for an option
    // this line had just applied.
    if "`open_browser'" == "1" {
        _dash_browser_wanted, spec(`"`json_spec'"')
        local open_browser = r(open)
    }
    if "`open_browser'" == "1" {
        // The one opener, shared with dash build: the platform's command,
        // a Mac known by its machine type as well (see _dash_open_page).
        _dash_open_page, path(`"`saving_path'"')
    }
    else {
        // Shown as written: braces are legal in a file name (P20-07).
        mata: _dash_say("txt", "dash: dashboard saved to ", st_local("saving_path"), "")
    }
end


// ================================================================
// _dash_clear  — reset global registry
// ================================================================
program define _dash_clear
    version 16.0

    // Sweep dash's whole global namespace, not an enumerated list.
    //
    // Two things were wrong with enumerating.  The wildcard below it read
    //     macro drop _dash_*
    // -- globals with a LEADING underscore -- and dash's globals are named
    // `dash_*' with none, so it matched nothing and only the enumeration ran.
    // And an enumeration goes stale: the list named dash_kpi_<name>_stat
    // through _upd and did NOT name _if or _in, which carry a KPI's own
    // qualifier, so
    //     dash kpi mean(mpg) if foreign==1, name(k1)
    //     dash clear
    //     dash kpi mean(mpg), name(k1)
    // left the qualifier in place and the second, unqualified KPI displayed
    // the conditional mean.  A stale qualifier is worse than a stale label:
    // the number is wrong and looks plausible.
    //
    // The registry loop could only ever drop what the registry still named,
    // so a global belonging to a graph whose name had left the registry
    // survived indefinitely.  A prefix sweep has neither problem and needs
    // no maintenance when a new per-graph global is added.
    //
    // These four prefixes are dash's own namespace.  A user global that
    // happens to start with one of them is not distinguishable from dash's
    // and is cleared too; that is what `dash clear' means.
    //
    // The dash_max_* globals are deliberately NOT swept, and none of the
    // patterns here matches them.  They are the session's resource limits
    // (WP-19) -- settings the user chose, like $dash_nobrowser -- not
    // registry state: a do-file that raises dash_max_cells once and runs
    // `dash clear' between dashboards must keep the limit it set.
    capture macro drop dash_spec_*
    capture macro drop dash_json_*
    capture macro drop dash_opts_*
    capture macro drop dash_kpi_*

    capture macro drop dash_graph_registry
    // Leading-underscore globals, if any command ever sets one.
    capture macro drop _dash_*

    display as text "dash: registry cleared."
end


// ================================================================
// _dash_kpi  — KPI subcommand
// ================================================================
program define _dash_kpi
    version 16.0

    // Rule 16: text reaching the spec must be well-formed UTF-8 BEFORE it
    // leaves Stata.  The gate was applied at exactly one entry point --
    // _dash_plot -- so KPI titles, build titles and subtitles, tabs() and
    // filter labels had no gate at all, and a malformed sequence in any of
    // them went straight to Python.
    mata: _dash_check_utf8(strtrim(st_local("0")))

    syntax anything(name=statspec) [if] [in] , ///
        TItle(string)           ///
        NAMe(string)            ///
        [ FMT(string)           ///
          SUBtitle(string)      ///
          COLOR(string)         ///
          BGCOLOR(string)       ///
          UPDate(string)        ///
        ]

    // The statistic may carry a point: p97.5 (below).  Read by value, in
    // Mata, in one statement so regexs() reads this match: expanded in the
    // expression, a statistic holding $name or `...' was read again for
    // macros and taken for what it expanded to -- mean(\$v) for mean(price)
    // (measured 24sep2026; test_json_escaping.cscript JSE-58).  Mata's own
    // ustrregexm/ustrregexs, not Stata's regexm/regexs, which follows the
    // caller's version (5629 below): ICU is the same engine whatever
    // version this program runs under.  The variable name accepts Unicode
    // letters (G5, WP-28: 2916's rule) and is capped at 32 characters,
    // checked once the match has already set _kst_ok and kpi_var so a
    // failed match never reaches ustrregexs().
    mata: st_local("_kst_ok", strofreal(ustrregexm(st_local("statspec"), ///
        "^([a-zA-Z0-9.]+)\(([\p{L}_][\p{L}\p{N}_]*)\)$"))); ///
        st_local("stat", st_local("_kst_ok") == "1" ? ustrregexs(1) : ""); ///
        st_local("kpi_var", st_local("_kst_ok") == "1" ? ustrregexs(2) : ""); ///
        st_local("_kst_ok", strofreal(st_local("_kst_ok") == "1" & ///
            ustrlen(st_local("kpi_var")) <= 32))
    if !`_kst_ok' {
        display as error "dash kpi: syntax is stat(varname), e.g. mean(mpg)."
        exit(198)
    }

    local valid_stats "mean sum count dcount min max median sd var cv iqr skewness p25 p50 p75"
    // p# for any percentile Stata's _pctile computes -- p10, p97.5, p0.5 --
    // not only the three in the list.  Measured at 4ede074, p97.5 stopped at
    // the pattern above, which had no point in it, and the rule here read
    // whole numbers from 1 to 99 only, although the help promised p97.5 and
    // both renderers compute it.  _dash_kpi_pctile reads the number byte by
    // byte, keeps it to what _pctile accepts (greater than 0, less than 100)
    // and to 15 digits, and writes it once, so p097.50 is stored, echoed and
    // rendered as p97.5 (test_help_claims_4.cscript HC4-01..07).
    mata: _dash_kpi_pctile(st_local("stat"), "_pct_num", "_pct_why")
    // Any echo of the statistic is bounded: it holds only letters, digits
    // and points here, but it may be as long as a command line.
    mata: st_local("_stat_safe", usubstr(st_local("stat"), 1, 40) + ///
        (strlen(st_local("stat")) > 40 ? "..." : ""))
    if "`_pct_why'" == "form" {
        display as error "dash kpi: '`_stat_safe'' is not a percentile. " ///
            "Write p# with # a decimal number greater than 0 and less " ///
            "than 100, such as p97.5."
        exit(198)
    }
    if "`_pct_why'" == "digits" {
        display as error "dash kpi: the percentile in '`_stat_safe'' has " ///
            "more than 15 digits."
        exit(198)
    }
    if "`_pct_why'" == "range" {
        display as error "dash kpi: percentile must be greater than 0 and " ///
            "less than 100, as _pctile requires (got '`_stat_safe'')."
        exit(198)
    }
    local is_pctile = ("`_pct_why'" == "ok")
    if `is_pctile' local stat "p`_pct_num'"
    if !`: list stat in valid_stats' & !`is_pctile' {
        display as error "dash kpi: unsupported statistic '`_stat_safe''. " ///
            "Choose from: `valid_stats', or p# for any percentile."
        exit(198)
    }

    confirm variable `kpi_var'
    // count and dcount take a string variable -- its non-missing and its
    // distinct values -- and every other statistic needs a number.  A
    // string used to pass: summarize skips it, so mean(make) was stored as
    // "." and drawn as ".", and count(make) was stored as 0 while the card
    // counted every value, empty strings included (measured 23sep2026).
    capture confirm numeric variable `kpi_var'
    if _rc & !inlist("`stat'", "count", "dcount") {
        display as error "dash kpi: `stat'() needs a numeric variable; " ///
            "`kpi_var' is a string.  Only count() and dcount() take a " ///
            "string variable."
        exit(109)
    }

    // Split off a ", replace" sub-option BEFORE validating the name, by the
    // rule the graph registrar applies: syntax's name(string) captures the
    // whole of "k1, replace", which would then fail the name regex below.
    // This program kept a copy of that rule's regex; it reads name() through
    // _dash_name_split now, so one rule reads it for a graph and a KPI card
    // alike, and its flag is the only word on replace
    // (test_registry_collision.cscript REG-35, REG-36).
    //
    // name() is read by value.  name[, replace] is made of letters,
    // digits, _, blanks and a comma, and a text holding anything else is
    // refused below as the name it is not -- before _dash_name_split, which
    // takes its text as an argument, reads it: expanded in the name check,
    // name(`"q"7"') stopped here with r(303) "equation [a-zA-Z_] not
    // found", and name(\$m) was read again for macros and registered under
    // whatever $m held (measured 24sep2026; test_json_escaping.cscript
    // JSE-58).  twoway refuses a name holding a quote, r(198) (measured).
    mata: st_local("_nm_raw_ok", ///
        strofreal(!ustrregexm(st_local("name"), "[^A-Za-z0-9_, \t]")))
    local replace_flag 0
    if `_nm_raw_ok' {
        _dash_name_split `"`name'"' _nm replace_flag
        local name `"`_nm'"'
    }

    // The graph registrar's rule, without bounded repetition (see there).
    // A KPI's longest globals are its fields, dash_kpi_<name>__<field> with
    // a field of three letters (_dash_kpi_fields in dash_parse.mata): 14
    // characters around the name, so its limit is 18.
    mata: st_local("_nm_ok", strofreal(st_local("_nm_raw_ok") == "1" & ///
        regexm(st_local("name"), "^[a-zA-Z_][a-zA-Z0-9_]*$") & ///
        strlen(st_local("name")) <= 18))
    if !`_nm_ok' {
        // Echoed as text, as the graph registrar does (see there).
        mata: st_local("_name_safe", ustrregexra(usubstr( ///
            st_local("name"), 1, 40), "[^A-Za-z0-9_.\-]", "?"))
        display as error "dash kpi: invalid name '`_name_safe''. " ///
            "Names must start with a letter or underscore, contain only " ///
            "letters, digits, and underscores, and be at most 18 characters."
        exit(198)
    }
    // Two underscores in a row are dash's own, as for a graph (see there).
    if strpos("`name'", "__") {
        mata: _dash_say("err", "dash kpi: name '", st_local("name"), ///
            "' holds two underscores in a row, which dash keeps for the " + ///
            "names it generates, such as a by() graph's panels. " + ///
            "Choose a name without __.")
        exit(198)
    }
    // _all is link()'s word for every graph, as for a graph (see there).
    if "`name'" == "_all" {
        display as error "dash kpi: name '_all' is the word link(_all) " ///
            "uses for every graph. Choose another name."
        exit(198)
    }

    // Every option is proven BEFORE anything is retired: measured
    // 22sep2026, `name(k, replace) fmt(bogus)' was refused correctly but
    // had already dropped the old KPI's globals while the registry still
    // listed k, and the next `dash build' died on the corrupt registry
    // with a JSON traceback (update(bogus) did the same).
    //
    // update() is read by value: compared inside quotes, update(`"a"b"')
    // stopped with r(132) "too few quotes" and update(`"filter" name(x)"')
    // with r(109) "type mismatch", and update(\$m) was taken for whatever
    // $m held (measured 24sep2026; test_json_escaping.cscript JSE-55,
    // JSE-58).
    local _ulen : length local update
    if `_ulen' == 0 local update "filter"
    mata: st_local("_upd_ok", ///
        strofreal(anyof(("filter", "brush", "both"), st_local("update"))))
    if !`_upd_ok' {
        display as error "dash kpi: update() must be filter, brush, or both."
        exit(198)
    }
    // fmt() is proven a single numeric display format here, before any
    // computation, so `: display' below can stay the formatter (WP-15).
    // Measured by length and handed over through macval(), so a fmt(\$m)
    // is judged as the text it is, not as what $m holds (JSE-58).  In a
    // block: the one-line form `if exp command' expands its command a
    // second time, and macval() protects only the first -- measured
    // 24sep2026, fmt(\$m) reached the validator as %9.2f that way.
    local _fmlen : length local fmt
    if `_fmlen' > 0 {
        _dash_validate_value "dash kpi" "fmt" "format" `"`macval(fmt)'"' ""
    }

    // Graphs and KPIs share ONE registry and one namespace.
    // _dash_register_graph has always refused a duplicate unless replace was
    // given; this program checked nothing, so a KPI could quietly take a
    // name a graph already held -- and then win it, because the build's
    // graph loop passes over any entry carrying a KPI marker.  Measured:
    //     dash scatter mpg weight, name(g1)
    //     dash kpi mean(mpg), name(g1) title("Avg")
    //     dash build, saving(out.html) replace
    // returned rc 0 at every step, said nothing, and wrote a dashboard with
    // the KPI's text and no graph at all.  A second KPI of the same name
    // overwrote the first just as quietly.
    local _kpi_registry = "${dash_graph_registry}"
    local _kpi_already  = 0
    local _kpi_ntok : word count `_kpi_registry'
    forvalues k = 1/`_kpi_ntok' {
        if "`:word `k' of `_kpi_registry''" == "`name'" local _kpi_already = 1
    }
    if `_kpi_already' == 1 & `replace_flag' == 0 {
        display as error "dash kpi: name '`name'' already exists. " ///
            "Use name(`name', replace) to overwrite."
        exit(198)
    }
    // WP-19: the same registry limit as a graph, checked before any global
    // is set or retired and before the statistic is computed.  A KPI
    // replacing a registered name never counts.
    _dash_graph_cap `_kpi_already'
    // Retire whatever held the name before, so the entry does not end up
    // carrying a graph's JSON and a KPI's marker at the same time.
    if `_kpi_already' == 1 {
        _dash_drop_item "`name'"
    }

    // The qualifier is handed to each command through macval(), as typed:
    // expanded plainly, it was read again for macros, so if make !=
    // "\$m" was computed as make != <whatever $m held> while Stata's own
    // summarize, given the same line, compares make with the text $m
    // (measured 24sep2026; test_json_escaping.cscript JSE-58).
    local kpi_value ""

    if inlist("`stat'", "mean", "sum", "min", "max", "sd") {
        quietly summarize `kpi_var' `macval(if)' `macval(in)'
        if      "`stat'" == "mean"  local kpi_value = r(mean)
        else if "`stat'" == "sum"   local kpi_value = r(sum)
        else if "`stat'" == "min"   local kpi_value = r(min)
        else if "`stat'" == "max"   local kpi_value = r(max)
        else if "`stat'" == "sd"    local kpi_value = r(sd)
    }
    else if "`stat'" == "count" {
        // The non-missing values, as count if !missing() counts them: for a
        // number that is summarize's r(N), and a string, which summarize
        // skips, has its values that are not "" counted too.
        tempvar _dash_nm
        quietly generate byte `_dash_nm' = !missing(`kpi_var') `macval(if)' `macval(in)'
        quietly count if `_dash_nm' == 1
        local kpi_value = r(N)
    }
    else if "`stat'" == "dcount" {
        // codebook is NOT r-class: r(unique) is always missing, so this
        // statistic has never produced a value.  Measured alternatives:
        // inspect gives r(N_unique) but stops reporting at 100 distinct and
        // is numeric-only; tabulate dies at 200k distinct; levelsof fails
        // once r(levels) exceeds c(macrolen).  egen group() has no ceiling,
        // works for string and numeric alike, and was the fastest measured.
        tempvar _dash_grp
        quietly egen `_dash_grp' = group(`kpi_var') `macval(if)' `macval(in)'
        quietly summarize `_dash_grp', meanonly
        local kpi_value = cond(r(N) == 0, 0, r(max))
    }
    else if "`stat'" == "median" {
        quietly _pctile `kpi_var' `macval(if)' `macval(in)', p(50)
        local kpi_value = r(r1)
    }
    else if "`stat'" == "iqr" {
        quietly _pctile `kpi_var' `macval(if)' `macval(in)', p(25 75)
        local kpi_value = r(r2) - r(r1)
    }
    else if `is_pctile' {
        // Any percentile, not the three p(25 50 75) was frozen at.  The
        // number as _dash_kpi_pctile wrote it, which is the text the
        // renderers parse, so all three read the same double.
        quietly _pctile `kpi_var' `macval(if)' `macval(in)', p(`_pct_num')
        local kpi_value = r(r1)
    }
    else if inlist("`stat'", "var", "cv", "skewness") {
        quietly summarize `kpi_var' `macval(if)' `macval(in)', detail
        if      "`stat'" == "var"      local kpi_value = r(Var)
        else if "`stat'" == "cv"       local kpi_value = cond(r(mean)==0, ., r(sd)/r(mean))
        else if "`stat'" == "skewness" local kpi_value = r(skewness)
    }

    local kpi_display = "`kpi_value'"
    if `_fmlen' > 0 {
        local kpi_display : display `fmt' `kpi_value'
        local kpi_display = strtrim("`kpi_display'")
    }

    // Store each KPI field in its own global so multi-word titles/subtitles
    // are preserved.  A marker global (value "1") allows the registry to
    // detect that this name is a KPI rather than a graph.
    //
    // The fields are dash_kpi_<name>__<field>, two underscores, and are the
    // fields _dash_kpi_fields() in dash_parse.mata lists -- the list
    // _dash_item_globals retires.  With one underscore, dash_kpi_a_stat,
    // KPI a's statistic was the marker of any item named a_stat: measured
    // 23sep2026 at 9f48cf7, a graph a_stat beside KPI a was drawn as a
    // blank KPI card and no figure, and a KPI a_stat set KPI a's statistic
    // to "1".  No name may hold two underscores in a row (above), so no
    // name reaches these.
    global dash_kpi_`name'       "1"
    global dash_kpi_`name'__sta  "`stat'"
    global dash_kpi_`name'__var  "`kpi_var'"
    global dash_kpi_`name'__val  "`kpi_value'"
    global dash_kpi_`name'__dsp  "`kpi_display'"
    global dash_kpi_`name'__upd  "`update'"
    // The user's text is stored by value, from Mata.  global ... "`title'"
    // read it again for macros -- A\$g B \`=1+1' C was stored as "A<what $g
    // held> B 2 C", and a \`=filewrite(...)' in a title wrote a file -- and
    // the qualifier was cut where a "' closed the compound quotes it was
    // put in: if make == "' or 1 or '" was stored as "make ==", and the
    // saved page, finding no qualifier it could read, showed the
    // unconditional mean, 6165.26, where Stata's summarize gives .
    // (measured 24sep2026; test_json_escaping.cscript JSE-51, JSE-58).
    mata: st_global("dash_kpi_" + st_local("name") + "__fmt", st_local("fmt"))
    mata: st_global("dash_kpi_" + st_local("name") + "__tit", st_local("title"))
    mata: st_global("dash_kpi_" + st_local("name") + "__sub", st_local("subtitle"))
    mata: st_global("dash_kpi_" + st_local("name") + "__col", st_local("color"))
    mata: st_global("dash_kpi_" + st_local("name") + "__bg",  st_local("bgcolor"))
    // The KPI's own if/in.  Stata computes the right value above and
    // stores it, but the renderer recomputes from the full frame, so
    // without these `dash kpi mean(mpg) if foreign==1` displayed the
    // UNCONDITIONAL mean.
    // Its abbreviations written out, as a graph's are (QL-22).
    mata: st_global("dash_kpi_" + st_local("name") + "__if", ///
        _dash_qual_expand(strtrim(regexr(st_local("if"), "^[ ]*if[ ]+", ""))))
    mata: st_global("dash_kpi_" + st_local("name") + "__in", ///
        strtrim(regexr(st_local("in"), "^[ ]*in[ ]+", "")))

    local registry = "${dash_graph_registry}"
    local already  = 0
    local ntok : word count `registry'
    forvalues k = 1/`ntok' {
        if "`:word `k' of `registry''" == "`name'" local already = 1
    }
    if `already' == 0 {
        if "${dash_graph_registry}" == "" global dash_graph_registry "`name'"
        else global dash_graph_registry "${dash_graph_registry} `name'"
    }

    display as text "dash: KPI '`name'' registered (`stat'(`kpi_var') = `kpi_display')."
end


// ================================================================
// _dash_build  — build dashboard
// ================================================================
// ================================================================
// _dash_prepare_spec  — everything `dash build' and `dash serve' do
// before they hand the spec to Python: validate the build options,
// work out which variables have to be serialized, write them, and
// assemble the master JSON.
//
// WHY THIS PROGRAM EXISTS
//
// There were two copies of this, and they had drifted.  `dash build'
// carried every option the user gave it.  `dash serve' declared three
// options -- port(), nobrowser(), timeout() -- and wrote build_options
// that were literal constants:
//
//     "layout":"auto","link":"","filter":"","theme":"","title":"","subtitle":""
//
// with no scheme, tabs or filter_position key present at all.  So
// `dash serve' could not be given a filter and could not inherit one,
// which means the live server -- whose entire selling point is that a
// filter recomputes aggregates rather than masking precomputed ones --
// could never have a filter in it.  dash.sthlp documents the sequence
//
//     . dash build, saving(dashboard.html) filter(foreign, type(dropdown)) replace
//     . * -- or launch live server (filter recomputes aggregates) --
//     . dash serve, port(5006)
//
// which produced a served dashboard with no filter and no message.
//
// The caller owns the tempfiles: a `tempfile' macro is erased when the
// program that declared it ends, so specpath() and datapath() come in
// from the caller rather than being created here.
//
// The option list below is the full build surface.  It is repeated in
// `_dash_build' and `_dash_serve' because each of those also has
// options of its own; test_serve_options.py asserts the three lists
// agree, so they cannot drift again the way these two did.
// ================================================================
program define _dash_prepare_spec, rclass
    version 16.0

    // Rule 16: text reaching the spec must be well-formed UTF-8 BEFORE it
    // leaves Stata.  The gate was applied at exactly one entry point --
    // _dash_plot -- so KPI titles, build titles and subtitles, tabs() and
    // filter labels had no gate at all, and a malformed sequence in any of
    // them went straight to Python.
    mata: _dash_check_utf8(strtrim(st_local("0")))

    // filter() is taken out of the command here, by _dash_extract_filters,
    // which reads quotes -- the way dash build and dash serve take it out
    // of the user's command -- and not by -syntax-.  They hand it on as
    // filter(<the text as the user wrote it>).  It went in filter(`"..."'),
    // and a group holding "' closed that compound quote: label("'90s") was
    // lost, rc 0, and a label could put the rest of its text on this
    // command line as options -- label("') csv title(pwned) subtitle(")
    // titled the page "pwned" and turned the CSV download of every row on
    // (measured 24sep2026; test_json_escaping.cscript JSE-57).  FILTer()
    // stays declared, and never sees a value.
    mata: _dash_extract_filters("_filter_parts", "_cmd_nofilter")
    local 0 : copy local _cmd_nofilter

    syntax [, ///
        CMDname(string)         ///
        SPECpath(string)        ///
        DATApath(string)        ///
        INHERIT                 ///
        FILTer(string)          ///
        SAVing(string)          ///
        TItle(string)           ///
        SUBtitle(string)        ///
        LAYout(string)          ///
        LINK(string)            ///
        THEME(string)           ///
        SCHeme(string)          ///
        NOBRowser               ///
        REPLACE                 ///
        SERVER                  ///
        TABS(string asis)       ///
        FILTERPOSition(string)  ///
        CSV                     ///
    ]
    local filter : copy local _filter_parts

    if `"`cmdname'"' == "" local cmdname "dash build"

    // ---- inherit the preceding dash build's options ----
    //
    // Only what the user did not specify on this command.  An option
    // given here always wins; an option given on neither is empty, as
    // it was before.  Read through Mata rather than by expanding the
    // global inside quotes: these carry the user's own title() and
    // label() text, and expanding a value containing a double quote is
    // the failure this file has already been bitten by twice.  Kept by
    // copy: local `_bo' `"`_bo_val'"' read the value again for macros, so
    // an inherited title holding $m or `...' was expanded after all
    // (measured 24sep2026; test_json_escaping.cscript JSE-58).
    if "`inherit'" != "" {
        foreach _bo in title subtitle layout link theme scheme tabs filterposition filter csv {
            local _cur : length local `_bo'
            if `_cur' == 0 {
                mata: st_local("_bo_val", st_global("dash_opts_" + st_local("_bo")))
                local _bolen : length local _bo_val
                if `_bolen' > 0 local `_bo' : copy local _bo_val
            }
        }
    }

    // ---- check registry is not empty ----
    // saving(), replace and server describe writing a FILE.  That is what
    // `dash build' does and what `dash serve' does not -- dash.sthlp lists
    // serve's surface as port(), nobrowser(), timeout() and the dashboard
    // options, and none of these three is on it.  They arrive here through
    // the trailing * of _dash_serve_spec, are declared below for dash
    // build's sake, and were read by nobody, so
    //     . dash serve, saving(out.html)
    //     served a dashboard and wrote no file, in silence.
    //
    // The check lives HERE rather than in _dash_serve_spec because
    // test_serve_options.py requires that program to forward the build
    // surface untouched rather than enumerate it -- enumerating it is how
    // the two copies drifted apart in the first place.  This program already
    // declares all three, and already knows which command called it.
    if "`cmdname'" == "dash serve" {
        local _srv_na ""
        if `"`saving'"' != "" local _srv_na `"`_srv_na' saving()"'
        if "`replace'" != ""  local _srv_na `"`_srv_na' replace"'
        if "`server'"  != ""  local _srv_na `"`_srv_na' server"'
        if `"`_srv_na'"' != "" {
            display as text "dash serve: ignoring option(s) that only apply to dash build:" ///
                as result `"`_srv_na'"'
            display as text "  dash serve streams the dashboard; it writes no file."
        }
    }

    if "${dash_graph_registry}" == "" {
        display as error "`cmdname': no graphs registered. Define graphs with name() before running `cmdname'."
        exit(198)
    }
    local registry = "${dash_graph_registry}"

    // ---- validate layout ----
    local _llen : length local layout
    if `_llen' == 0 local layout "auto"
    if `"`layout'"' != "auto" {
        // Require strictly positive integers in "N M" grid layout.
        // ^[1-9][0-9]* rejects zero and leading-zero forms (e.g. "0 0", "0 2").
        if !regexm(`"`layout'"', "^[1-9][0-9]* [1-9][0-9]*$") & ///
           !regexm(`"`layout'"', "^[a-zA-Z_][a-zA-Z0-9_]*:[0-9]+,[0-9]+") & ///
           !regexm(lower(`"`layout'"'), "^bs") {
            display as error "`cmdname': layout() must be 'auto', 'N M' grid (N and M >= 1), 'name:row,col' placement, or 'bs[: name=span ...]' Bootstrap layout."
            exit(198)
        }

        // The whole value, not only its start.  A placement or Bootstrap
        // spec the renderer could not read, and a name the registry does
        // not hold, were handed on and drawn some other way, in silence:
        // measured at f2ecdd4, layout(p:1,1 junk) and layout(bs\) were
        // drawn as auto, layout(nosuch:1,1) was a 3 x 1 grid saved and
        // 1 x 2 served, and a Bootstrap span of 13 was clamped to 12
        // (P20-30).  A name must be in the registry, as link() and
        // exclude() require.  Read in Mata, by value; the refusal is
        // echoed through _dash_say.
        mata: st_local("_lref", _dash_layout_refusal(st_local("layout"), st_local("registry")))
        local _lreflen : length local _lref
        if `_lreflen' > 0 {
            mata: _dash_say("err", "`cmdname': ", st_local("_lref"), "")
            exit(198)
        }

        // The grid's size.  The saved page pads its grid out to rows x
        // cols cells before drawing it: measured 23sep2026, a 4000 x 4000
        // grid of two graphs peaked at 1.5 GB, and layout(99999 99999) --
        // ten billion cells -- could not finish.  No grid needs more cells
        // than a dashboard can hold graphs and KPI cards, so its cells are
        // held to the graphs limit.  _dash_layout_cells() is the
        // renderer's rule (dash_render.py's _dash_layout_cells), read in
        // Mata so the value is never expanded into an expression.
        mata: st_local("_lcells", strofreal(_dash_layout_cells(st_local("layout")), "%21.0f"))
        if "`_lcells'" != "." {
            _dash_limit, name(graphs)
            local _glim  = r(value)
            local _gceil = r(ceiling)
            if `_lcells' > `_glim' {
                _dash_count_fmt _glim_s  `_glim'
                _dash_count_fmt _gceil_s `_gceil'
                if `_lcells' >= 1e15 local _lcells_s "more than 999,999,999,999,999"
                else                 _dash_count_fmt _lcells_s `_lcells'
                display as error "`cmdname': layout() asks for a grid of `_lcells_s' cells, more than the `_glim_s' graphs and KPI cards one dashboard draws."
                display as error "      Use a smaller grid, or set global dash_max_graphs to a higher value (at most `_gceil_s')."
                exit(198)
            }
        }
    }

    // ---- validate filter_position ----
    // By value: compared inside quotes, filterposition(`"le"ft"') stopped
    // dash build with r(132) "too few quotes", and filterposition(\$m) was
    // taken for whatever $m held (measured 24sep2026;
    // test_json_escaping.cscript JSE-55, JSE-58).
    local _fplen : length local filterposition
    if `_fplen' == 0 local filterposition "top"
    mata: st_local("_fpok", ///
        strofreal(anyof(("top", "left"), st_local("filterposition"))))
    if !`_fpok' {
        // The option is declared FILTERPOSition(); naming it filter_position()
        // here sent the user to an option -syntax- does not accept.
        display as error "`cmdname': filterposition() must be 'top' (default) or 'left' (sidebar)."
        exit(198)
    }

    // ---- validate theme() and scheme() (WP-17) ----
    // Before anything is written, through the program that gates a
    // graph-level scheme(): theme() is one of the six aliases, scheme() a
    // shipped translation, a theme, or a .scheme file in the working
    // directory.  Measured 22sep2026: scheme(nosuchthing) and
    // theme(nosuchtheme) went through with rc 0 and a warning and were
    // drawn as s2color, and a hostile theme() reached the spec (escaped,
    // but reached it).  The session's c(scheme) is not validated -- it was
    // not asked for -- and the renderer warns once when it cannot
    // translate it.  Lengths, not expansions, decide whether a value is
    // present: these carry the user's own text.
    local _tlen : length local theme
    if `_tlen' > 0 {
        _dash_shipped_schemes
        local _tsorted : list sort _dash_themes
        local _tspec : subinstr local _tsorted " " "|", all
        _dash_validate_value "`cmdname'" "theme" "enum,`_tspec'" `"`macval(theme)'"' ""
        local theme `"`macval(_dash_vnorm)'"'
    }
    local _slen : length local scheme
    if `_slen' > 0 {
        _dash_validate_value "`cmdname'" "scheme" "scheme" `"`macval(scheme)'"' ""
    }

    // ---- validate link() names ----
    // Read by value, word by word as the renderer reads them, in Mata
    // (_dash_link_refusal): compared inside quotes and split by Stata's
    // word functions, link(`"g1"x"') stopped dash build with r(132) "too
    // few quotes" and link(`"g1" "g2"') with r(109) "type mismatch", and
    // link(`""g1""') passed as g1 while the renderer looks for a graph
    // named "g1", quotes and all (measured 24sep2026;
    // test_json_escaping.cscript JSE-56).
    // _all links every graph, so beside names it is a contradiction.  The
    // refusal is shown as written, never as SMCL (P20-09).
    local _lklen : length local link
    if `_lklen' > 0 {
        mata: st_local("_lkref", _dash_link_refusal(st_local("link"), ///
            st_local("registry")))
        local _lkreflen : length local _lkref
        if `_lkreflen' > 0 {
            mata: _dash_say("err", "`cmdname': ", st_local("_lkref"), "")
            exit(198)
        }
    }

    // ---- validate the filter() groups: exclude() names, variable names ----
    // Read in Mata, by value (_dash_filter_refusal): the filter string is
    // the user's text, label("...") included, and each group ends only at a
    // "||" or ";" outside quotes and parentheses.  This used to split the
    // string at EVERY "||" and ";" and take every "exclude(" for the
    // sub-option, wherever it stood: measured at 4ede074, label("A;B") and
    // label("A||B") stopped dash build with "too few quotes" r(132),
    // label(A;B) was refused as naming a variable 'B)', and
    // label("exclude(nosuch) me") as an exclude() of a graph named nosuch.
    // exclude() is still read in any case, as the renderer reads it, so
    // EXCLUDE(nosuch) is refused like exclude(nosuch) (P20-24).  Both
    // refusals are shown as written, never as SMCL (P19-24, P20-10); the
    // variables of the groups come back in _fvars, each an ASCII name, for
    // the serialisation below.
    local _fvars ""
    local _flen0 : length local filter
    if `_flen0' > 0 {
        mata: st_local("_fref", _dash_filter_refusal(st_local("filter"), ///
            st_local("registry"), "_fvars"))
        local _freflen : length local _fref
        if `_freflen' > 0 {
            mata: _dash_say("err", "`cmdname': ", st_local("_fref"), "")
            exit(198)
        }
    }

    // Do NOT substitute "default" for an unspecified theme.  "default" is a
    // real theme name that resolves to s2color, so writing it here made the
    // session's own c(scheme) unreachable -- the renderer's precedence is
    // scheme() then theme() then c(scheme), and a theme was always present.
    // An empty theme means "the user did not ask", which is the truth.

    // ---- determine all variables needed ----
    // And each distinct qualifier, which is evaluated in Stata and exported
    // as a column (_dash_qual_rewrite, _dash_qual_take, _dash_qual_gen).
    local all_vars ""
    // GAPS2 G3: the saved page's cells limit counts what it embeds, not
    // every exported variable -- row_vars/comp_cells decide that, beside
    // all_vars (which the export still uses unchanged, per DISCOVERY
    // Q9: the JSON export is not shrunk).  _pt_univar/_pt_onefit name the
    // computed-only types; by_groups is the LIMIT, not any graph's actual
    // group count, which is not known before the export.
    local row_vars ""
    local comp_cells = 0
    _dash_plottype_families
    _dash_limit, name(by_groups)
    local _by_groups_lim = r(value)
    mata: _dash_qual_reset()
    local ntok_reg : word count `registry'
    forvalues k = 1/`ntok_reg' {
        local gname : word `k' of `registry'

        // A KPI is exactly its marker: the global dash_kpi_<name> holding
        // "1", the one global _dash_kpi writes under that name -- here and
        // in the two loops that assemble the spec.  No other item's global
        // has that name: a KPI's fields are dash_kpi_<name>__<field>, and
        // no name holds two underscores in a row.  While they were
        // dash_kpi_<name>_stat, ..., a graph a_stat beside KPI a found KPI
        // a's statistic here, "mean", and was drawn as a blank KPI card
        // (measured 23sep2026 at 9f48cf7).
        if "${dash_kpi_`gname'}" == "1" {
            // _dash_kpi always stores a statistic and a variable.  A KPI
            // without them was not registered by this dash -- its marker
            // set by hand, or a KPI an older dash left in the session under
            // the one-underscore names, which are no longer read -- and it
            // was drawn as a blank card, in silence.  Measured by length,
            // so a hand-set value is never expanded.
            local _ksl : strlen global dash_kpi_`gname'__sta
            local _kvl : strlen global dash_kpi_`gname'__var
            if `_ksl' == 0 | `_kvl' == 0 {
                mata: _dash_say("err", "`cmdname': registry entry '", ///
                    st_local("gname"), "' holds a KPI with no statistic " + ///
                    "or variable. Run dash clear and register it again.")
                exit(198)
            }
            local kpi_var = "${dash_kpi_`gname'__var}"
            if !`: list kpi_var in all_vars' local all_vars "`all_vars' `kpi_var'"
            // GAPS2 G3: a KPI always counts its variable (and, below, its
            // own qualifier column) -- it never draws from a computed-only
            // layer, so it is never excluded from row_vars.
            if !`: list kpi_var in row_vars' local row_vars "`row_vars' `kpi_var'"
            // The KPI's own if and in: the column that will hold Stata's
            // answer (_dash_qual_gen), read by value from the registry.
            // Its variables are not exported -- the answer is.  They used
            // to be, so the renderer could translate the qualifier, and a
            // qualifier it read otherwise than Stata showed a card Stata
            // would not (test_qualifier_in_stata.cscript QS-03).
            local _dq_err ""
            mata: st_local("_kqc_`k'", _dash_qual_take( ///
                st_global("dash_kpi_" + st_local("gname") + "__if"), ///
                st_global("dash_kpi_" + st_local("gname") + "__in"), "_dq_err", 1))
            if `: length local _dq_err' {
                mata: _dash_say("err", "`cmdname': registry entry '", ///
                    st_local("gname"), "' holds a qualifier dash cannot evaluate: " + ///
                    st_local("_dq_err") + ". Run dash clear and register it again.")
                exit 198
            }
            if `: length local _kqc_`k'' {
                if !`: list _kqc_`k' in row_vars' local row_vars "`row_vars' `_kqc_`k''"
            }
            continue
        }

        // Use strlen to check if JSON global is set WITHOUT embedding JSON in a
        // double-quoted expression (which would break when JSON contains " chars)
        local _chk : strlen global dash_json_`gname'

        // Neither a KPI nor a graph: the registry names an item dash does
        // not hold.  No registrar leaves one -- each retires exactly the
        // item it replaces -- but the registry is ordinary globals.  Such
        // an entry went into the spec as an empty graph and the renderer
        // died on the JSON: measured 23sep2026 at 9f48cf7, r(7102) and a
        // Python JSONDecodeError on "[, {" or on a trailing comma.  Refused
        // here, by name, before anything is exported; the name is echoed
        // as text, since a hand-set registry may hold anything.
        if `_chk' == 0 {
            mata: _dash_say("err", "`cmdname': registry entry '", ///
                st_local("gname"), "' holds neither a graph nor a KPI. " + ///
                "Run dash clear and register it again.")
            exit(198)
        }
        if `_chk' > 0 {
            // The graph as the spec will carry it: each if/in pair replaced
            // by the column that holds Stata's answer, and no qualifier
            // text left for a renderer to translate.  Read by value.
            local _dq_err ""
            mata: st_local("_qg_`k'", _dash_qual_rewrite( ///
                st_global("dash_json_" + st_local("gname")), "_dq_err", 1))
            if `: length local _dq_err' {
                mata: _dash_say("err", "`cmdname': registry entry '", ///
                    st_local("gname"), "' holds a qualifier dash cannot evaluate: " + ///
                    st_local("_dq_err") + ". Run dash clear and register it again.")
                exit 198
            }
            local gvars ""
            mata: _dash_extract_vars(`"${dash_json_`gname'}"', "gvars")
            foreach v of local gvars {
                if !`: list v in all_vars' local all_vars "`all_vars' `v'"
            }
            // Also extract variables referenced only in faceting (by) -- these
            // may not appear in any plot-variable key but must be serialised
            // so the renderer can facet on them.  Read from the rewritten
            // graph, which holds no qualifier text: a qualifier's variables
            // are not exported, its answer is.
            local qvars ""
            mata: _dash_extract_qual_vars(st_local("_qg_`k'"), "qvars")
            foreach v of local qvars {
                capture confirm variable `v'
                if _rc == 0 {
                    if !`: list v in all_vars' local all_vars "`all_vars' `v'"
                }
            }

            // GAPS2 G3: does this graph draw only its own computed
            // output (_dash_computed_cells, on the rewritten graph so a
            // qualifier's text is never scanned), and does nothing else
            // reach its rows (_dash_graph_touched)?  filter is read here
            // in its pre-rewrite form -- _dash_graph_touched needs only
            // exclude()'s graph names, not the filter's own variable
            // name, so the full-name rewrite below does not matter yet.
            mata: st_local("_gc_`k'", strofreal(_dash_computed_cells( ///
                st_local("_qg_`k'"), st_nobs(), `_by_groups_lim', ///
                "`_pt_univar' `_pt_onefit'")))
            mata: st_local("_gt_`k'", strofreal(_dash_graph_touched( ///
                "`gname'", st_local("_qg_`k'"), st_local("filter"), ///
                st_local("link"), st_local("csv"))))
            if `_gc_`k'' >= 0 & !`_gt_`k'' {
                local comp_cells = `comp_cells' + `_gc_`k''
            }
            else {
                foreach v of local gvars {
                    if !`: list v in row_vars' local row_vars "`row_vars' `v'"
                }
                foreach v of local qvars {
                    capture confirm variable `v'
                    if _rc == 0 {
                        if !`: list v in row_vars' local row_vars "`row_vars' `v'"
                    }
                }
                mata: st_local("_gqc_`k'", _dash_qual_cols_in(st_local("_qg_`k'")))
                foreach v of local _gqc_`k' {
                    if !`: list v in row_vars' local row_vars "`row_vars' `v'"
                }
            }
        }
    }

    // ---- also include filter variables in the serialization ----
    // Filter variables (e.g. foreign from filter(foreign, type(dropdown)))
    // may not appear in any graph or KPI spec.  Without explicit inclusion,
    // the export would never write them, so the Python filter widgets would
    // be silently skipped.  _fvars holds each group's variable, read and
    // proven a name by _dash_filter_refusal above -- a top-level ";"
    // separates two groups as "||" does (BUG-45).  A filter must name a
    // real variable: silently skipping one meant
    //     dash build, filter(<script>alert, type(dropdown))
    // returned rc 0 with a filter that did nothing, and every other Stata
    // command rejects a name it cannot resolve.
    //
    // An abbreviation is the variable it abbreviates, as a varname is
    // anywhere in Stata, and the renderer is handed the full name: it looks
    // the name up in the data the export writes, which carries the full one, so
    // filter(fore) built with rc 0 and no widget -- "the variable is not in
    // the data" (measured at 4ede074).
    local _ffull ""
    foreach _fvar of local _fvars {
        capture confirm variable `_fvar'
        if _rc != 0 {
            display as error "`cmdname': filter() variable `_fvar' not found."
            exit(111)
        }
        unab _fvfull : `_fvar'
        local _ffull `_ffull' `_fvfull'
        if !`: list _fvfull in all_vars' {
            local all_vars "`all_vars' `_fvfull'"
        }
        // GAPS2 G3: a filter variable always counts, whatever it excludes.
        if !`: list _fvfull in row_vars' {
            local row_vars "`row_vars' `_fvfull'"
        }
    }
    if !`: list _ffull == _fvars' {
        mata: st_local("filter", _dash_filter_setvars(st_local("filter"), ///
            st_local("_ffull")))
    }

    local all_vars = strtrim("`all_vars'")
    local row_vars = strtrim("`row_vars'")

    // No variable to export: every graph must draw from its own values --
    // scatteri, pci, pcarrowi and function alone, which twoway draws with
    // no data in memory -- and the data file then holds no variable
    // (_dash_empty_data).  Such a dashboard was refused here whatever it
    // held: after `dash scatteri 1 2, name(a1)', `dash build' said "no
    // variables identified across registered graphs", r(198), saved and
    // served (measured 24sep2026; test_parser.cscript P1A-72).  A graph of
    // any other type that names no variable -- one dash no longer
    // registers (P1A-69), but the registry is ordinary globals -- is still
    // refused (P1A-74).  A KPI always names its variable.
    local _novars = ("`all_vars'" == "")
    if `_novars' {
        _dash_plottype_families
        forvalues k = 1/`ntok_reg' {
            local gname : word `k' of `registry'
            if "${dash_kpi_`gname'}" == "1" continue
            mata: st_local("_gvf", strofreal(_dash_spec_types_in( ///
                st_global("dash_json_" + st_local("gname")), ///
                st_local("_pt_literal"))))
            if !`_gvf' {
                display as error "`cmdname': no variables identified across registered graphs."
                exit(198)
            }
        }
        // No data are exported, so no qualifier column: the literal family
        // draws its own values, which twoway's if and in do not reach.
        mata: _dash_qual_reset()
        forvalues k = 1/`ntok_reg' {
            local gname : word `k' of `registry'
            if "${dash_kpi_`gname'}" == "1" continue
            mata: st_local("_qg_`k'", _dash_qual_rewrite( ///
                st_global("dash_json_" + st_local("gname")), "_dq_err", 0))
        }
    }

    // ---- write the data file (_dash_write_data) ----
    // From Python through sfi, as on the immediate route; jsonio is no
    // longer needed.

    // ---- resource limits (WP-19), before anything is exported ----
    // As on the immediate route: every dash_max_* global the session has
    // set is validated and carried to the renderer as build_options.limits,
    // and what is about to be embedded -- every observation of every
    // variable in all_vars -- is held to the cells limit, and the text in
    // its string variables to the bytes limit.  All come before the file
    // is written, so a refusal leaves the data as it was, and before `dash
    // build' records its dash_opts_* globals.
    _dash_limits_json
    local _dash_lim_json `"`r(json)'"'
    local _dash_nvars : word count `all_vars'
    // Each qualifier column is embedded with the data, and counted.
    mata: _dash_qual_export()
    // GAPS2 G3: the server route -- dash build, server (the SERVER
    // option here) or dash serve (which never passes its own server
    // option: `cmdname' alone decides it, checked above at "ignoring
    // option(s) that only apply to dash build") -- embeds every
    // observation of every variable and says so; the saved route counts
    // only what the page will hold.
    if "`server'" != "" | "`cmdname'" == "dash serve" {
        _dash_cell_cap `=`_dash_nvars' + `_dq_n'' "" 0 1
    }
    else {
        _dash_cell_cap `: word count `row_vars'' "" `comp_cells'
    }
    _dash_byte_cap `all_vars'

    // Collect display formats, as on the immediate route.
    _dash_formats_json "`all_vars'" _dash_fmt_json _dash_date_vars
    local _dash_jrc = 0
    if `_novars' {
        _dash_empty_data "`datapath'"
    }
    else {
        // The qualifier columns, as on the immediate route: made first,
        // exported with the data, dropped the moment the file is written, the
        // estimates in memory held meanwhile (QS-15).
        local _dash_qual_vars ""
        if `_dq_n' > 0 {
            tempname _dash_eh
            _estimates hold `_dash_eh', restore nullok
        }
        _dash_qual_gen "`cmdname'"
        // Captured for the same reason as on the immediate route.
        capture noisily _dash_write_data "`datapath'" `all_vars' `_dash_qual_vars'
        local _dash_jrc = _rc
        if "`_dash_qual_vars'" != "" {
            capture drop `_dash_qual_vars'
        }
    }
    if `_dash_jrc' exit `_dash_jrc'

    capture confirm file "`datapath'"
    if _rc != 0 {
        display as error "`cmdname': the data could not be written."
        exit(198)
    }

    // ---- assemble master JSON ----
    local graphs_json ""
    local n_graphs = 0

    forvalues k = 1/`ntok_reg' {
        local gname : word `k' of `registry'
        if "${dash_kpi_`gname'}" == "1" {
            // An entry should never hold a graph AND a KPI: both registrars
            // retire whatever held the name before.  If one does, this loop
            // would drop the graph from the dashboard in silence, which is
            // exactly the defect that used to be reachable through
            // `dash kpi ..., name(<an existing graph>)'.  The registry lives
            // in ordinary Stata globals, so a do-file that sets dash_* by
            // hand can still produce this; say so rather than swallow it.
            if `"${dash_json_`gname'}"' != "" {
                display as text "`cmdname': '`gname'' is registered as both " ///
                    "a graph and a KPI; drawing the KPI." 
                display as text "  Run {cmd:dash clear} and register it once, " ///
                    "or use {cmd:name(`gname', replace)}."
            }
            continue
        }

        if `n_graphs' > 0 local graphs_json `"`graphs_json', "'
        // The graph with its qualifiers replaced by their columns
        // (_dash_qual_rewrite, above), joined by value.
        mata: st_local("graphs_json", st_local("graphs_json") + st_local("_qg_`k'"))
        local n_graphs = `n_graphs' + 1
    }

    // assemble KPIs JSON
    local kpis_json ""
    local n_kpis = 0
    forvalues k = 1/`ntok_reg' {
        local gname : word `k' of `registry'
        if "${dash_kpi_`gname'}" != "1" continue

        // Read each KPI field from its dedicated global (preserves multi-word values)
        // then JSON-escape the string fields before insertion.  The fields
        // are dash_kpi_<name>__<field> (_dash_kpi_fields in dash_parse.mata).
        //
        // Every field is read and escaped by value, in Mata.  Expanded into
        // a command line, "${dash_kpi_<name>__tit}" was read again for
        // macros, so a title dash kpi had stored as written -- A$m B
        // `=1+1' C -- reached the spec expanded, and ran; so did a string
        // literal in the qualifier (measured 24sep2026;
        // test_json_escaping.cscript JSE-58).  _json_escape writes ` $ and '
        // as \u escapes, so each can be expanded inside the compound quotes
        // of the line below.  The statistic, variable, value and update()
        // are dash's own words, and are escaped all the same.
        mata: st_local("kstat",       _json_escape(st_global("dash_kpi_" + st_local("gname") + "__sta")))
        mata: st_local("kvar",        _json_escape(st_global("dash_kpi_" + st_local("gname") + "__var")))
        mata: st_local("kval",        _json_escape(st_global("dash_kpi_" + st_local("gname") + "__val")))
        mata: st_local("_kdisp_esc",  _json_escape(st_global("dash_kpi_" + st_local("gname") + "__dsp")))
        mata: st_local("_kfmt_esc",   _json_escape(st_global("dash_kpi_" + st_local("gname") + "__fmt")))
        mata: st_local("_ktitle_esc", _json_escape(st_global("dash_kpi_" + st_local("gname") + "__tit")))
        mata: st_local("_ksub_esc",   _json_escape(st_global("dash_kpi_" + st_local("gname") + "__sub")))
        mata: st_local("_kcol_esc",   _json_escape(st_global("dash_kpi_" + st_local("gname") + "__col")))
        mata: st_local("_kbg_esc",    _json_escape(st_global("dash_kpi_" + st_local("gname") + "__bg")))
        mata: st_local("kupdate",     _json_escape(st_global("dash_kpi_" + st_local("gname") + "__upd")))
        // The KPI's if and in travel as the column that holds Stata's
        // answer (_dash_qual_take, above), and as no text.
        local _kqc : copy local _kqc_`k'

        if `n_kpis' > 0 local kpis_json `"`kpis_json', "'
        local kpis_json `"`kpis_json'{"name":"`gname'","stat":"`kstat'","var":"`kvar'","value":"`kval'","display":"`_kdisp_esc'","fmt":"`_kfmt_esc'","title":"`_ktitle_esc'","subtitle":"`_ksub_esc'","color":"`_kcol_esc'","bgcolor":"`_kbg_esc'","update":"`kupdate'","if_expr":"","in_expr":"","qual_col":"`_kqc'"}"'
        local n_kpis = `n_kpis' + 1
    }

    // JSON-escape it, like every other string that goes into master_json.
    // It did not used to be: filter(weight, type(range) label("Curb weight"))
    // put bare double quotes straight into the document and broke it, which
    // is why label() could not be used even once the renderer learned to
    // parse it.
    local filter_json ""
    // `: length local' rather than a comparison: the value contains the
    // user's label("...") text, and expanding it inside an expression is the
    // hazard this file has already been bitten by twice.
    //
    // The user's text reaches _dash_json_str through macval(), here and
    // below: expanded plainly, the command line read it again for macros,
    // so a title holding $m or `=1+1' reached the page expanded and a
    // `=filewrite(...)' in one ran (measured 24sep2026;
    // test_json_escaping.cscript JSE-58).  layout(), link() and
    // filterposition() are proven to hold neither before this point, and
    // theme() to be one of its six names.
    // In a block, as the one-line `if exp command' expands its command a
    // second time (see _dash_kpi's fmt()).
    local _flen : length local filter
    if `_flen' > 0 {
        _dash_json_str `"`macval(filter)'"' filter_json
    }

    // Escape build-level title and subtitle for JSON safety
    _dash_json_str `"`macval(title)'"'    _title_esc
    _dash_json_str `"`macval(subtitle)'"' _subtitle_esc
    // Escape tabs string for JSON embedding
    _dash_json_str `"`macval(tabs)'"' _tabs_esc
    // Carry the session confidence level so the renderer does not have to
    // assume 95.  A per-plot level() overrides it.
    local _dash_lvl = c(level)
    // The session's own scheme.  A Stata user has already chosen how their
    // graphs should look; without this dash was the one command in the
    // session that ignored it.  An explicit scheme() or theme() still wins --
    // the renderer applies them in that order.
    local _dash_sess_scheme = c(scheme)
    // scheme() may be a .scheme file of the working directory, whose name
    // is the user's text: through macval() as well (JSE-58).
    _dash_json_str `"`macval(scheme)'"'    _scheme_esc
    _dash_json_str `"`_dash_sess_scheme'"' _sess_scheme_esc
    // theme() was the one user string on the master-spec line that went in
    // raw while every other went through _dash_json_str.  Measured:
    // theme("C:\temp\x"), theme("a\q"), theme("a\") and a theme()
    // containing a double quote each gave r(7102) and a Python
    // JSONDecodeError traceback, with no message from dash; theme("a\b")
    // gave rc 0 and silently delivered a BACKSPACE, because \b happens to
    // be a valid JSON escape.  The same values in scheme() were all fine.
    _dash_json_str `"`theme'"'             _theme_esc
    // layout() went in raw too, on the belief that its check had refused
    // any such value.  The check reads only the START of the value (bs...,
    // or name:r,c...), so layout("bs\") passed it and its backslash escaped
    // the closing quote of the JSON string: measured 23sep2026, r(7102) and
    // a JSONDecodeError traceback (P20-17).  link() and filterposition()
    // are proven to be registry names and top or left before this line,
    // and are escaped all the same, so no value on it goes in raw.
    _dash_json_str `"`layout'"'            _layout_esc
    _dash_json_str `"`link'"'              _link_esc
    _dash_json_str `"`filterposition'"'    _fpos_esc
    // csv (WP-21): offer a download of the rows the filters leave.  Opt-in,
    // because it hands any viewer every row of every variable the dashboard
    // uses -- a served dashboard otherwise sends the browser only what it
    // plots.  A flag, so only "1" or "0" reaches the spec.
    local _csv_flag = cond("`csv'" != "", "1", "0")
    local master_json `"{"graphs":[`graphs_json'],"kpis":[`kpis_json'],"build_options":{"layout":"`_layout_esc'","link":"`_link_esc'","filter":"`filter_json'","theme":"`_theme_esc'","scheme":"`_scheme_esc'","session_scheme":"`_sess_scheme_esc'","title":"`_title_esc'","subtitle":"`_subtitle_esc'","registry":"`registry'","tabs":"`_tabs_esc'","filter_position":"`_fpos_esc'","csv":"`_csv_flag'","level":"`_dash_lvl'","formats":`_dash_fmt_json',"limits":`_dash_lim_json'}}"'

    tempname fh
    // quietly: see the note at the other spec writer -- `write replace'
    // reports a missing file, and this path is always a fresh tempfile.
    quietly file open `fh' using "`specpath'", write replace text
    file write `fh' `"`master_json'"'
    file close `fh'

    return local layout          `"`layout'"'
    return local filterposition  `"`filterposition'"'
    return local n_graphs        = `n_graphs'
    return local n_kpis          = `n_kpis'
    return local vars            `"`all_vars'"'
end


program define _dash_build
    version 16.0

    // Rule 16: text reaching the spec must be well-formed UTF-8 BEFORE it
    // leaves Stata.  The gate was applied at exactly one entry point --
    // _dash_plot -- so KPI titles, build titles and subtitles, tabs() and
    // filter labels had no gate at all, and a malformed sequence in any of
    // them went straight to Python.
    mata: _dash_check_utf8(strtrim(st_local("0")))

    // Pre-extract ALL filter() options from `0' before -syntax- runs.
    // Stata's -syntax- only accepts one option of a given name; using two
    // filter() options (as in full_dashboard.do) would trigger an error.
    // _dash_extract_filters() scans `0', removes every filter(...) group,
    // joins their contents with " || ", and stores them in `_filter_parts'.
    // The cleaned command is stored in `_cmd_nofilter' and assigned back to
    // `0' so that -syntax- sees only the remaining options.  Both by copy:
    // local 0 `"`_cmd_nofilter'"' read the whole command again for macros,
    // so link(\$m), filterposition(\$m) and saving(\$m/x.html) were taken
    // for whatever $m held and a `=filewrite(...)' in a title ran, and local
    // filter `"`_filter_parts'"' drew a label holding $m as what $m held
    // (measured 24sep2026; test_json_escaping.cscript JSE-58).
    mata: _dash_extract_filters("_filter_parts", "_cmd_nofilter")
    local filter : copy local _filter_parts
    local 0      : copy local _cmd_nofilter

    syntax [, ///
        SAVing(string)          ///
        TItle(string)           ///
        SUBtitle(string)        ///
        LAYout(string)          ///
        LINK(string)            ///
        THEME(string)           ///
        SCHeme(string)          ///
        NOBRowser               ///
        REPLACE                 ///
        SERVER                  ///
        TABS(string asis)       ///
        FILTERPOSition(string)  ///
        CSV                     ///
    ]

    // ---- check registry is not empty ----
    if "${dash_graph_registry}" == "" {
        display as error "dash build: no graphs registered. Define graphs with name() before running dash build."
        exit(198)
    }

    // ---- validate saving() ----
    // Measured by its length, never read inside quotes before the validator
    // has seen it: `if "`saving'" == ""' ended its quotes at a double quote
    // in the path, r(132) "too few quotes", on both routes, and the
    // validator's "disallowed characters" was never reached (measured
    // 24sep2026; test_path_validation.cscript PV-21).
    local _svl : length local saving
    if `_svl' == 0 {
        display as error "dash build: saving() is required."
        exit(198)
    }
    if "`server'" != "" {
        // The same validator, asked for .py.  This branch used to check the
        // extension and nothing else, so a server-mode path skipped the
        // traversal, metacharacter and quote checks entirely.  It also kept
        // the old traversal rule, a '..' anywhere, in front of it: so
        // saving("my..report.py") server was refused, r(198), where
        // saving("my..report.html") builds.  The validator's rule, a '..'
        // path segment, is the one rule now (PV-20; ROADMAP AC-08.4).
        // The path goes to the validator as written, through macval(): a
        // saving(\$m/x.html) was read again for macros and written wherever
        // $m pointed, where the validator refuses a $ (JSE-58).
        _dash_validate_path `"`macval(saving)'"' "py"
        local saving `"`_dash_vpath'"'
    }
    else {
        _dash_validate_path `"`macval(saving)'"' "html"
        local saving `"`_dash_vpath'"'
    }
    // Before the file is looked for: a directory that does not exist is
    // not a file that "already exists" (JSE-52).
    _dash_saving_dir `"`saving'"'

    // An existing file without replace, r(198), and a directory in the
    // file's place with it, r(608): _dash_saving_clobber, shared with the
    // one-line form.  The path is shown as written (P20-08).
    _dash_saving_clobber `"`saving'"' "`replace'" "dash build"

    // ---- validate, collect, serialize and assemble ----
    //
    // Shared with `dash serve', which used to do all of this itself with
    // the build options hardcoded to blanks.  The tempfiles are declared
    // here because a `tempfile' macro is erased when the program that
    // declares it ends.
    //
    // `0' is the command's own option string with the filter() groups
    // already removed by _dash_extract_filters, so it is forwarded as
    // written rather than reassembled option by option -- reassembling
    // would expand the user's title() and label() text a second time.
    tempfile data_json_path master_json_path

    // -syntax- leaves `0' as it found it, which means it still carries the
    // leading comma.  Forwarding it after options of our own produced two
    // commas on one line, and everything after the second was read as a
    // positional argument: `invalid 'saving''.  `: subinstr local' replaces
    // the FIRST occurrence unless told otherwise, which is the leading
    // comma.  Both extended functions work on the macro's VALUE, so neither
    // expands the user's title() or label() text a second time.
    local _fwd_opts : copy local 0
    local _fwd_opts : subinstr local _fwd_opts "," ""

    // Everything is handed on as the user wrote it: the options through
    // macval(), so the line is not read again for macros, and filter() as
    // filter(<its text>), which _dash_prepare_spec takes out again with
    // the same scanner.  It went in filter(`"..."'), and a group holding "'
    // closed that compound quote: label("'90s") was lost, and label("')
    // csv title(pwned) subtitle(") put csv and title(pwned) on this line
    // (measured 24sep2026; test_json_escaping.cscript JSE-57).
    _dash_prepare_spec, cmdname("dash build") ///
        specpath("`master_json_path'") datapath("`data_json_path'") ///
        filter(`macval(filter)') `macval(_fwd_opts)'

    // ---- remember these for a later dash serve ----
    //
    // dash.sthlp documents building a dashboard and then serving it live
    // with a bare `dash serve, port()'.  That only means anything if the
    // options survive the first command, so they are recorded here and
    // `dash serve' inherits any the user does not restate.
    //
    // The user's text is recorded by value, from Mata: global ...
    // `"`title'"' read it again for macros, so a title holding $m or
    // `=1+1' was recorded expanded, and a `=filewrite(...)' in one ran
    // (measured 24sep2026; test_json_escaping.cscript JSE-58).  layout()
    // and filterposition() come back from _dash_prepare_spec validated.
    global dash_opts_layout         `"`r(layout)'"'
    global dash_opts_filterposition `"`r(filterposition)'"'
    global dash_opts_csv            "`csv'"
    foreach _bo in title subtitle link theme scheme tabs filter {
        mata: st_global("dash_opts_" + st_local("_bo"), st_local(st_local("_bo")))
    }

    // ---- Locate dash_render.py ----
    _dash_find_render
    local render_py `"`r(fn)'"'

    local render_mode "standalone"
    if "`server'" != "" local render_mode "server"

    // ---- Invoke Python renderer via helper ----
    // (python:...end must be in a dedicated program; see _dash_do_render)
    _dash_do_render, spec("`master_json_path'") data("`data_json_path'") ///
        output("`saving'") renderpy("`render_py'") mode("`render_mode'")

    if "`server'" != "" {
        mata: _dash_say("txt", "dash build: server app written to ", st_local("saving"), "")
        // Point at the app's OWN launcher, not `bokeh serve'.  Both work for
        // the dashboard now, but `bokeh serve' owns its Tornado application
        // and gives an app script no supported way to register a route, so
        // the /health endpoint project rule 17 asks for exists only when the
        // app serves itself.  Running it directly also honours --port and
        // the websocket origins, and opens no browser unless asked.
        mata: _dash_say("txt", "  To launch: python " + char(34), st_local("saving"), char(34))
        display as text `"  Options:   --port N  --show  --timeout MINUTES  (--help lists them all)"'
        display as text `"  Limits:    --sessions-per-client N  --new-clients-per-minute N  --sessions-per-minute N"'
    }
    else {
        mata: _dash_say("txt", "dash: dashboard saved to ", st_local("saving"), "")
        // nobrowser, or the global the certification runner sets once.
        // There was no way to suppress this at all: a suite that builds
        // twenty dashboards opened twenty browser tabs, and so did any
        // do-file run in batch.
        // A registered graph's nodraw keeps the window shut too, as the
        // help has always said it does -- the rule `dash serve' uses.
        _dash_dashboard_browser, `nobrowser'
        if r(open) {
            // The one opener, shared with the one-line form (see
            // _dash_open_page).
            _dash_open_page, path(`"`saving'"')
        }
    }
end


// ================================================================
// _dash_serve_spec  — everything `dash serve' does except the launch.
//
// Separated so the option pass-through can be certified without a
// certification script starting a server, which it must never do.
// test_serve_options.cscript calls this directly and reads the master
// JSON it writes.
//
// The caller owns the two paths: a `tempfile' macro is erased when the
// program that declares it ends, so a file created here would be gone
// before `_dash_serve' could launch anything from it.
// ================================================================
program define _dash_serve_spec, rclass
    version 16.0

    // Rule 16: text reaching the spec must be well-formed UTF-8 BEFORE it
    // leaves Stata.  The gate was applied at exactly one entry point --
    // _dash_plot -- so KPI titles, build titles and subtitles, tabs() and
    // filter labels had no gate at all, and a malformed sequence in any of
    // them went straight to Python.
    mata: _dash_check_utf8(strtrim(st_local("0")))

    // Pre-extract every filter() group before -syntax- runs, exactly as
    // `dash build' does: -syntax- accepts one option of a given name, and
    // a dashboard may legitimately have several filters.  Both by copy, as
    // dash build takes them (see there; JSE-58).
    mata: _dash_extract_filters("_filter_parts", "_cmd_nofilter")
    local filter : copy local _filter_parts
    local 0      : copy local _cmd_nofilter

    // Only the options `dash serve' owns are named here.  The trailing *
    // collects every build option into `options' exactly as the user
    // wrote it, so this program never has to enumerate the build surface
    // -- which is how the two copies drifted apart in the first place.
    syntax [, ///
        SPECpath(string)    ///
        DATApath(string)    ///
        PORT(string)        ///
        NOBRowser           ///
        TIMEOUT(string)     ///
        *                   ///
    ]

    // port() and timeout() go into the one-line python: statement that
    // launches the server, so each must be digits and nothing else.  They
    // are tested byte by byte (_dash_is_digits) and never by a regular
    // expression: StataNow's regexm() matches "^[0-9]+$" against "7" +
    // char(10), so timeout(7<LF>) was accepted and handed a newline to that
    // statement (P20-14).  timeout() is at most nine digits: a 400-digit
    // timeout() was accepted, and the launcher, multiplying it by 60 into a
    // float, died with OverflowError after binding its port (P20-19).  A
    // port of more than nine digits is out of range without being read.
    // Values are tested by length, never expanded into an expression, and
    // a refused one is echoed through _dash_say, as written.
    local _plen : length local port
    if `_plen' == 0 local port "5006"
    local _tlen : length local timeout
    if `_tlen' == 0 local timeout "0"

    mata: st_local("_pdig", strofreal(_dash_is_digits(st_local("port"), .)))
    if !`_pdig' {
        mata: _dash_say("err", "dash serve: port() must be a positive integer (got: ", st_local("port"), ")")
        exit(198)
    }
    local _plen : length local port
    local port_int = .
    if `_plen' <= 9 local port_int = real("`port'")
    if `port_int' < 1024 | `port_int' > 65535 {
        mata: _dash_say("err", "dash serve: port() must be between 1024 and 65535 (got: ", st_local("port"), ")")
        exit(198)
    }
    mata: st_local("_tdig", strofreal(_dash_is_digits(st_local("timeout"), 9)))
    if !`_tdig' {
        mata: _dash_say("err", "dash serve: timeout() must be a non-negative integer in minutes, at most nine digits (got: ", st_local("timeout"), ")")
        exit(198)
    }
    // Written as a plain integer: 007 goes to the launcher as 7.
    local timeout = strofreal(real("`timeout'"), "%12.0f")

    if `"`specpath'"' == "" | `"`datapath'"' == "" {
        display as error "dash serve: internal error — specpath() and datapath() are required."
        exit(198)
    }

    // inherit: reuse the options of a `dash build' earlier in this session
    // for anything not restated here.  dash.sthlp documents exactly that
    // sequence, and without this the served dashboard silently lost the
    // filter the documented example builds it with.  Handed on as written,
    // as dash build hands them on (see there): through macval(), and
    // filter(<its text>), which label("') csv title(pwned) subtitle(")
    // could close as filter(`"..."') (measured 24sep2026;
    // test_json_escaping.cscript JSE-57, JSE-58).
    _dash_prepare_spec, cmdname("dash serve") inherit ///
        specpath(`"`specpath'"') datapath(`"`datapath'"') ///
        filter(`macval(filter)') `macval(options)'

    return local master_json_path `"`specpath'"'
    return local data_json_path   `"`datapath'"'
    return local port             "`port_int'"
    return local timeout          "`timeout'"
    return local nobrowser        "`nobrowser'"
    return local layout           `"`r(layout)'"'
    return local filterposition   `"`r(filterposition)'"'
end


// ================================================================
// _dash_serve  — launch Bokeh Server for live interactive mode
// ================================================================
program define _dash_serve
    version 16.0

    // Rule 16: text reaching the spec must be well-formed UTF-8 BEFORE it
    // leaves Stata.  The gate was applied at exactly one entry point --
    // _dash_plot -- so KPI titles, build titles and subtitles, tabs() and
    // filter labels had no gate at all, and a malformed sequence in any of
    // them went straight to Python.
    mata: _dash_check_utf8(strtrim(st_local("0")))

    tempfile data_json_path master_json_path

    // `0' still carries the leading comma -syntax- left on it, so forwarding
    // it after options of our own put TWO commas on one line and everything
    // past the second was read as a positional argument:
    //     . dash serve, port(5006)
    //     invalid 'port'
    //     r(198);
    // -- every option dash.sthlp documents for this command, including the
    // port(5006) example it gives.  Only the bare form ran.  _dash_build has
    // fixed exactly this at its own forwarding site for some time; this path
    // never got the same treatment.  `: copy local' and `: subinstr local'
    // both work on the macro's VALUE, so neither expands the user's title()
    // or label() text a second time, and subinstr replaces only the FIRST
    // occurrence, which is the leading comma.
    local _srv_fwd : copy local 0
    local _srv_fwd : subinstr local _srv_fwd "," ""

    // Through macval(), so the line is not read again for macros: a
    // title(\$m) was served as whatever $m held (measured 24sep2026;
    // test_json_escaping.cscript JSE-58).
    _dash_serve_spec, specpath("`master_json_path'") datapath("`data_json_path'") `macval(_srv_fwd)'

    local port_int   "`r(port)'"
    local timeout    "`r(timeout)'"
    // The browser, by the rule `dash build' uses: its nobrowser option,
    // the session's $dash_nobrowser, or a registered graph's nodraw keeps
    // it shut.  This read the option alone (test_serve_browser.cscript).
    local _srv_nobr "`r(nobrowser)'"
    _dash_dashboard_browser, `_srv_nobr'
    local no_browser_flag "`r(flag)'"

    // ---- Locate dash_render.py ----
    // Before the announcement below, and before `python:'.  `dash serve'
    // used to print "starting Bokeh Server on port NNNN. Stata is blocked
    // until the server stops" and only then discover it could not run.
    _dash_require_python
    _dash_find_render
    local render_py `"`r(fn)'"'

    // Temp path for the generated Bokeh Server app.
    //
    // Use the tempfile macro DIRECTLY.  It used to be `_serve_app_base'.py',
    // a name Stata never registered, so Stata dutifully erased the
    // extension-less file it had registered -- which nothing ever wrote --
    // and left the .py behind for good.  Each one embeds the whole dataset
    // in decodable base64: measured on this machine, 142 orphans totalling
    // 18 MB, the newest decoding to 74 observations of mpg, weight and
    // foreign, in a directory any local user can read.
    //
    // No .py suffix is needed because the app is launched as
    // `python <path>', which does not care about the extension.  If that
    // ever reverts to `bokeh serve', which dispatches on the extension, the
    // suffix has to come back -- and so does an explicit erase.
    tempfile serve_app_path

    // Escape paths for safe Python string literal interpolation (see _dash_do_render).
    _dash_json_str `"`master_json_path'"' _py_master
    _dash_json_str `"`data_json_path'"'   _py_data
    _dash_json_str `"`serve_app_path'"'   _py_serve
    _dash_json_str `"`render_py'"'        _py_render

    display as text "dash serve: starting Bokeh Server on port `port_int'." ///
        "  Stata is blocked until the server stops (Ctrl+C)."

    // Single-line python: calls to avoid ado-path IndentationError (see _dash_do_render).
    python: import sys, runpy
    // --launch: `dash serve' is the path whose job IS to run a server.  The
    // renderer no longer starts one as a side effect of writing a file,
    // because `dash build, server' used that same entry point and was left
    // blocking forever with an orphaned server behind it.
    python: sys.argv = ["dash_render.py", "--spec", "`_py_master'", "--data", "`_py_data'", "--output", "`_py_serve'", "--mode", "server", "--launch", "--port", "`port_int'", "--timeout", "`timeout'"]
    if "`no_browser_flag'" != "" {
        python: sys.argv.append("--no-browser")
    }
    // GAPS2 F1: dash serve used to report success (rc 0) whatever the
    // launched app actually did -- a port already held by another program
    // failed only on the child's own process stderr, unseen here, after
    // about 1.7 seconds.  _dash_srv_rep is a dict shared by reference with
    // the executed module (a `python:' line inside an ado program takes
    // one statement per line and no compound statement, so a try/except
    // cannot be written here, and an exception escaping run_path is
    // r(7102) plus a traceback -- the opposite of a clean message).
    // dash_render.py's __main__ writes _dash_launch_app's failure text
    // into this dict instead of raising, when the dict is present.
    python: _dash_srv_rep = {}
    // Assign the result.  A single-line `python:' echoes the value of the
    // expression, and run_path returns the module globals dict, so this
    // line used to dump dash_render.py's whole namespace into the Stata log
    // on every render -- roughly 10 KB of noise per command.
    python: _dash_serve_ns = runpy.run_path("`_py_render'", init_globals={"_dash_launch_report": _dash_srv_rep}, run_name="__main__")
    python: from sfi import Macro as _dash_srv_M
    python: _dash_srv_M.setLocal("_srv_err", str(_dash_srv_rep.get("error", ""))[:4096])
    if `: length local _srv_err' {
        mata: _dash_say("err", "dash serve: ", st_local("_srv_err"), "")
        exit 198
    }
end
