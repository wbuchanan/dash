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
*!   - Mata handles ONLY segment splitting (|| / () syntax) and option-key
*!     abbreviation expansion.
*!   - ALL option parsing uses Stata's built-in -syntax- command, which
*!     provides correct varlist/if/in handling and unambiguous option matching.
*!   - JSON assembly is done in Stata using string concatenation after parsing.
*!
*! Author:  (see dash.sthlp)
*! Version: 2.0  27mar2026

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
    // Compound quotes are used with regexm/substr so that double-quoted
    // option values like title("My Title") are handled safely.
    local _subcmd ""
    if regexm(`"`0'"', "^([a-zA-Z][a-zA-Z0-9_]*)") {
        local _subcmd = regexs(1)
    }
    // Remaining text after the subcommand word (may start with , or space)
    local _subcmd_len = strlen("`_subcmd'")
    local _args = substr(`"`0'"', `_subcmd_len' + 1, .)

    if "`_subcmd'" == "kpi" {
        _dash_kpi `_args'
        exit
    }
    if "`_subcmd'" == "build" {
        _dash_build `_args'
        exit
    }
    if "`_subcmd'" == "clear" {
        _dash_clear
        exit
    }
    if "`_subcmd'" == "serve" {
        _dash_serve `_args'
        exit
    }

    // ----------------------------------------------------------------
    // Plot definition  (pass full args including plot-type word)
    // ----------------------------------------------------------------
    _dash_plot `0'
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
// dash nor the remedy -- while the jsonio check a few lines away has always
// given them a sentence they can act on.  This is modelled on that message.
// ================================================================
program define _dash_require_python
    version 16.0
    _dash_python_ok `"`c(python_exec)'"'
    if r(ok) != 1 {
        display as error "dash: Python is required but is not available to Stata."
        display as error "      Run {cmd:dash_setup} first, or link Stata to " ///
            "Python 3.8+: {help python}"
        exit 198
    }
end


// ================================================================
// _dash_require_mata  — refuse to start rather than fail on a missing function
// ================================================================
// Two checks, because neither covers the other.  The recorded load error is
// the only witness to a PARTIAL compile -- `run' returned 199 while the
// functions were still present -- and `mata describe' is the only witness to
// a library that was never loaded or has since been cleared, which `run'
// never gets to report.
// ================================================================
program define _dash_require_mata
    version 16.0

    // Every Mata function dash.ado calls, named once.  Checking a single
    // one would pass a library that compiled half way.
    local _needed _dash_check_utf8 _dash_comma_pos _dash_expand_plottype ///
        _dash_extract_filters _dash_extract_qual_vars _dash_extract_vars ///
        _dash_item_globals _dash_json_get_str _dash_option_names ///
        _dash_split_segs

    // The common case, and the cheap one.
    quietly capture mata: mata describe _dash_check_utf8()
    if _rc == 0 exit

    // Not loaded.  REPAIR rather than refuse: measured, the library is
    // routinely absent at this point through no fault of the install --
    // `clear all' drops it, `dash clear' never needed it, and dash.ado's
    // own top-level loader does not always run before the first command
    // when the file is reached through the ado-path.  A guard that simply
    // vetoed here failed test_examples_run.cscript, which runs `clear all'
    // before each of the eleven shipped examples.
    capture findfile dash_parse.mata
    if _rc == 0 {
        capture run `"`r(fn)'"'
    }
    else {
        capture findfile dash.ado
        if _rc == 0 {
            local _ado `"`r(fn)'"'
            local _beside = substr(`"`_ado'"', 1, ///
                strlen(`"`_ado'"') - strlen("dash.ado")) + "dash_parse.mata"
            capture confirm file `"`_beside'"'
            if _rc == 0 capture run `"`_beside'"'
        }
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
        display as error "      dash_parse.mata is not on the ado-path and " ///
            "not beside dash.ado."
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
    if substr(`"`_base'"', 1, 1) == "-" {
        display as error "dash: saving() file name may not start with '-'; the shell would read it as an option."
        display as error "      Write ./`_base' if that is really the name you want."
        exit(198)
    }
    if !regexm(lower("`fpath'"), "\.`ext'$") {
        display as error "dash: saving() path must end in .`ext' (got: `fpath')"
        exit(198)
    }
    // Reject shell metacharacters to prevent command injection via shell open/start/xdg-open.
    // Printable metacharacters checked via regexm character class.
    // Chars that Stata would misinterpret during macro expansion (backtick=96, dollar=36)
    // and control characters (tab=9, newline=10, CR=13) checked via strpos+char() to
    // avoid the "too few quotes" crash that occurs when a compound-quoted macro value
    // contains a backtick.
    // Parentheses are NOT rejected: every shell call site quotes the path
    // ("shell open \"`saving_path'\""), inside which ( and ) are literal, and
    // rejecting them broke every Windows path under "Program Files (x86)".
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
// _dash_json_str  — simple JSON string escaping in pure Stata
// Usage:  _dash_json_str `"`raw'"' "_escaped"
// After: local escaped contains the JSON-safe string (no surrounding quotes)
// ================================================================
program define _dash_json_str
    version 16.0
    args raw_val out_macro

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
    // Backslash first, always: every escape below introduces one.
    local v = subinstr(`"`raw_val'"', `"\"', `"\\"', .)
    local v = subinstr(`"`v'"', `"""', `"\""', .)

    // The five with short forms, which are what a reader expects to see.
    local v = subinstr(`"`v'"', char(8),  `"\b"', .)
    local v = subinstr(`"`v'"', char(9),  `"\t"', .)
    local v = subinstr(`"`v'"', char(10), `"\n"', .)
    local v = subinstr(`"`v'"', char(12), `"\f"', .)
    local v = subinstr(`"`v'"', char(13), `"\r"', .)

    // Everything else below 0x20, as \u00XX.  char(0) is not reachable: a
    // Stata string cannot carry a NUL, so it can never appear in `raw_val'.
    // Stata has no hex display format -- `: display %02x' is r(120) -- so
    // the two digits are taken from a digit string.
    local _hexdigits "0123456789abcdef"
    foreach _c of numlist 1/7 11 14/31 {
        if strpos(`"`v'"', char(`_c')) > 0 {
            local _hi = substr("`_hexdigits'", int(`_c'/16) + 1, 1)
            local _lo = substr("`_hexdigits'", mod(`_c', 16) + 1, 1)
            local v = subinstr(`"`v'"', char(`_c'), "\u00`_hi'`_lo'", .)
        }
    }

    c_local `out_macro' `"`v'"'
end


// ================================================================
// _dash_kv_json  — emit one JSON key:value pair fragment
// Sets c_local `out_macro' = `"\"key\":\"escaped_val\""'
// Only emits if val is non-empty (or force=1 passed).
// ================================================================
program define _dash_kv_json
    version 16.0
    args key val out_macro
    if `"`val'"' == "" {
        c_local `out_macro' ""
        exit
    }
    _dash_json_str `"`val'"' _esc
    c_local `out_macro' `""`key'":"`_esc'""'
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
    // NOTE: this block is generated by scripts/regen_option_surface.py
    // from test/fixtures/abbrev_truth.json.  Do not hand-edit; the same
    // option list appears in several places and the generator keeps them
    // in step.  Capitalised letters are the minimum abbreviation, measured
    // against real twoway rather than guessed.
    // NOTE: this block is generated by scripts/regen_option_surface.py
    // from test/fixtures/abbrev_truth.json.  Do not hand-edit; the same
    // option list appears in several places and the generator keeps them
    // in step.  Capitalised letters are the minimum abbreviation, measured
    // against real twoway rather than guessed.
    // The trailing * is Stata's own catch-all: any option not declared
    // above is collected into `options' instead of aborting the user's
    // do-file.  dash.sthlp has always claimed copy-pasted twoway commands
    // still run; without this they did not.  Unmatched options are
    // reported by name, once per command -- never silently dropped.
    syntax [, ///
        TItle(string asis)        SUBtitle(string asis)     NOTE(string asis) ///
        CAPtion(string asis)      NAMe(string)              SAVing(string) ///
        XTitle(string)            YTitle(string)            XLabel(string asis) ///
        YLabel(string asis)       XLIne(string asis)        YLIne(string asis) ///
        LEGend(string asis)       BY(string asis)           XSCale(string asis) ///
        YSCale(string asis)       ASPectratio(string)       SCHeme(string) ///
        PLOTRegion(string asis)   GRAPHRegion(string asis)  BGColor(string) ///
        PLOTBGCOLOR(string)       LINK(string)              FILTer(string asis) ///
        YTITLE2(string)           XTITLE2(string)           YLABEL2(string asis) ///
        XLABEL2(string asis)      YSCALE2(string asis)      XSCALE2(string asis) ///
        XSIZe(string)             YSIZe(string)             FXSIZE(string) ///
        FYSIZE(string)            SCALE(string)             TEXT(string asis) ///
        HOVer(string)             ///
        XTICk(string asis)        YTICk(string asis)        XMTick(string asis) ///
        YMTick(string asis)       XMLabel(string asis)      YMLabel(string asis) ///
        T1title(string)           T2title(string)           B1title(string) ///
        B2title(string)           L1title(string)           L2title(string) ///
        R1title(string)           R2title(string)           TITLE2(string) ///
        SUBTITLE2(string)         NODRAW                    PLAY(string) ///
        T(string)                 B(string)                 L(string) ///
        R(string) ///
        PBGC(string)              XLA2(string asis)         XSC2(string asis) ///
        XTI2(string)              YLA2(string asis)         YSC2(string asis) ///
        YTI2(string) ///
        * ///
    ]

    // twoway accepts t(), b(), l() and r() as abbreviations of t1title(),
    // b1title(), l1title() and r1title().  Stata's -syntax- derives the
    // minimum abbreviation from the leading run of capitals, and the digit in
    // "t1title" ends that run, so "T1title" yields a minimum of "t1", not "t".
    // The four single-letter forms are therefore declared as explicit aliases
    // and folded in here.  Verified against real twoway with a .gph resolution
    // oracle -- see test/fixtures/abbrev_truth.json.
    if `"`t'"' != "" & `"`t1title'"' == "" local t1title `"`t'"'
    if `"`b'"' != "" & `"`b1title'"' == "" local b1title `"`b'"'
    if `"`l'"' != "" & `"`l1title'"' == "" local l1title `"`l'"'
    if `"`r'"' != "" & `"`r1title'"' == "" local r1title `"`r'"'
    // Fold alias forms onto their real option locals.  These are
    // ALIASES, not prefixes, so Stata's truncation-based abbreviation
    // cannot express them; they are declared above and merged here.
    // twoway accepts none of them, so this is a superset and cannot
    // break drop-in parity, but it keeps existing dash do-files working.
    if `"`pbgc'"' != "" & `"`plotbgcolor'"' == "" local plotbgcolor `"`pbgc'"'
    if `"`xla2'"' != "" & `"`xlabel2'"' == "" local xlabel2 `"`xla2'"'
    if `"`xsc2'"' != "" & `"`xscale2'"' == "" local xscale2 `"`xsc2'"'
    if `"`xti2'"' != "" & `"`xtitle2'"' == "" local xtitle2 `"`xti2'"'
    if `"`yla2'"' != "" & `"`ylabel2'"' == "" local ylabel2 `"`yla2'"'
    if `"`ysc2'"' != "" & `"`yscale2'"' == "" local yscale2 `"`ysc2'"'
    if `"`yti2'"' != "" & `"`ytitle2'"' == "" local ytitle2 `"`yti2'"'


    // twoway accepts t(), b(), l() and r() as abbreviations of t1title(),
    // b1title(), l1title() and r1title().  Stata derives the minimum from the
    // leading run of capitals and the digit in "t1title" ends that run, so
    // "T1title" yields "t1", never "t".  The four single-letter forms are
    // declared separately and folded in here.  Measured against real twoway --
    // see test/fixtures/abbrev_truth.json.
    if `"`t'"' != "" & `"`t1title'"' == "" local t1title `"`t'"'
    if `"`b'"' != "" & `"`b1title'"' == "" local b1title `"`b'"'
    if `"`l'"' != "" & `"`l1title'"' == "" local l1title `"`l'"'
    if `"`r'"' != "" & `"`r1title'"' == "" local r1title `"`r'"'

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
    if `"`b1title'"' != "" local _dash_pending `"`_dash_pending' b1title"'
    if `"`b2title'"' != "" local _dash_pending `"`_dash_pending' b2title"'
    // link() and filter() belong to `dash build' and `dash serve', where
    // the link group and the filter widgets are made.  Written on a graph
    // they were stored in graph_options and read by nothing -- measured
    // 22sep2026: name(g1) link(g1) registered, built one source, said
    // nothing.  Named here, so nothing is dropped in silence.
    if `"`filter'"' != "" local _dash_pending `"`_dash_pending' filter"'
    if `"`fxsize'"' != "" local _dash_pending `"`_dash_pending' fxsize"'
    if `"`fysize'"' != "" local _dash_pending `"`_dash_pending' fysize"'
    if `"`l1title'"' != "" local _dash_pending `"`_dash_pending' l1title"'
    if `"`l2title'"' != "" local _dash_pending `"`_dash_pending' l2title"'
    if `"`link'"' != "" local _dash_pending `"`_dash_pending' link"'
    if `"`play'"' != "" local _dash_pending `"`_dash_pending' play"'
    if `"`r1title'"' != "" local _dash_pending `"`_dash_pending' r1title"'
    if `"`r2title'"' != "" local _dash_pending `"`_dash_pending' r2title"'
    if `"`scale'"' != "" local _dash_pending `"`_dash_pending' scale"'
    if `"`subtitle2'"' != "" local _dash_pending `"`_dash_pending' subtitle2"'
    if `"`t1title'"' != "" local _dash_pending `"`_dash_pending' t1title"'
    if `"`t2title'"' != "" local _dash_pending `"`_dash_pending' t2title"'
    if `"`text'"' != "" local _dash_pending `"`_dash_pending' text"'
    if `"`title2'"' != "" local _dash_pending `"`_dash_pending' title2"'
    if `"`xmlabel'"' != "" local _dash_pending `"`_dash_pending' xmlabel"'
    if `"`xmtick'"' != "" local _dash_pending `"`_dash_pending' xmtick"'
    if `"`ymlabel'"' != "" local _dash_pending `"`_dash_pending' ymlabel"'
    if `"`ymtick'"' != "" local _dash_pending `"`_dash_pending' ymtick"'
    // Whatever Stata could not match at all, via the trailing *.
    local _dash_unknown `"`options'"'

    sreturn local title        `"`title'"'
    sreturn local subtitle     `"`subtitle'"'
    sreturn local note         `"`note'"'
    sreturn local caption      `"`caption'"'
    sreturn local name         `"`name'"'
    sreturn local saving       `"`saving'"'
    sreturn local xtitle       `"`xtitle'"'
    sreturn local ytitle       `"`ytitle'"'
    sreturn local xlabel       `"`xlabel'"'
    sreturn local ylabel       `"`ylabel'"'
    sreturn local xline        `"`xline'"'
    sreturn local yline        `"`yline'"'
    sreturn local legend       `"`legend'"'
    sreturn local by           `"`by'"'
    sreturn local xscale       `"`xscale'"'
    sreturn local yscale       `"`yscale'"'
    sreturn local aspectratio  `"`aspectratio'"'
    sreturn local scheme       `"`scheme'"'
    sreturn local plotregion   `"`plotregion'"'
    sreturn local graphregion  `"`graphregion'"'
    sreturn local bgcolor      `"`bgcolor'"'
    sreturn local plotbgcolor  `"`plotbgcolor'"'
    sreturn local link         `"`link'"'
    sreturn local filter       `"`filter'"'
    sreturn local ytitle2      `"`ytitle2'"'
    sreturn local xtitle2      `"`xtitle2'"'
    sreturn local ylabel2      `"`ylabel2'"'
    sreturn local xlabel2      `"`xlabel2'"'
    sreturn local yscale2      `"`yscale2'"'
    sreturn local xscale2      `"`xscale2'"'
    sreturn local xsize        `"`xsize'"'
    sreturn local ysize        `"`ysize'"'
    sreturn local fxsize       `"`fxsize'"'
    sreturn local fysize       `"`fysize'"'
    sreturn local scale        `"`scale'"'
    sreturn local hover        `"`hover'"'
    sreturn local text         `"`text'"'
    sreturn local xtick        `"`xtick'"'
    sreturn local ytick        `"`ytick'"'
    sreturn local xmtick       `"`xmtick'"'
    sreturn local ymtick       `"`ymtick'"'
    sreturn local xmlabel      `"`xmlabel'"'
    sreturn local ymlabel      `"`ymlabel'"'
    sreturn local t1title      `"`t1title'"'
    sreturn local t2title      `"`t2title'"'
    sreturn local b1title      `"`b1title'"'
    sreturn local b2title      `"`b2title'"'
    sreturn local l1title      `"`l1title'"'
    sreturn local l2title      `"`l2title'"'
    sreturn local r1title      `"`r1title'"'
    sreturn local r2title      `"`r2title'"'
    sreturn local title2       `"`title2'"'
    sreturn local subtitle2    `"`subtitle2'"'
    sreturn local nodraw       `"`nodraw'"'
    sreturn local play         `"`play'"'
    sreturn local _pending  `"`_dash_pending'"'
    sreturn local _unknown  `"`_dash_unknown'"'
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
    // NOTE: this block is generated by scripts/regen_option_surface.py
    // from test/fixtures/abbrev_truth.json.  Do not hand-edit; the same
    // option list appears in several places and the generator keeps them
    // in step.  Capitalised letters are the minimum abbreviation, measured
    // against real twoway rather than guessed.
    // NOTE: this block is generated by scripts/regen_option_surface.py
    // from test/fixtures/abbrev_truth.json.  Do not hand-edit; the same
    // option list appears in several places and the generator keeps them
    // in step.  Capitalised letters are the minimum abbreviation, measured
    // against real twoway rather than guessed.
    // The trailing * is Stata's own catch-all: any option not declared
    // above is collected into `options' instead of aborting the user's
    // do-file.  dash.sthlp has always claimed copy-pasted twoway commands
    // still run; without this they did not.  Unmatched options are
    // reported by name, once per command -- never silently dropped.
    syntax [, ///
        MColor(string)            Msymbol(string)           MSIze(string) ///
        MSAngle(string)           MFColor(string)           MLColor(string) ///
        MLabel(string)            MLABColor(string)         MLABSize(string) ///
        MLABPosition(string)      MLABGap(string)           MLABWidth(string) ///
        MALpha(string)            MARKER(string)            LColor(string) ///
        LWidth(string)            LPattern(string)          LALpha(string) ///
        FColor(string)            FIntensity(string)        FAlpha(string) ///
        BARWidth(string)          BASE(string)              BLColor(string) ///
        BFColor(string)           JITter(string)            JSEed(string) ///
        YAXis(string)             XAXis(string)             COLORVar(string) ///
        COLPALette(string)        COLORDIScrete             COLORUSEPLEGend ///
        COLORNlevels(string)      COLORCUTs(string asis)    COLORMissing(string) ///
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
        JITTERSEED(string)        TItle(string asis)        SUBtitle(string asis) ///
        NOTE(string asis)         CAPtion(string asis)      NAMe(string) ///
        SAVing(string)            XTitle(string)            YTitle(string) ///
        XLabel(string asis)       YLabel(string asis)       XLIne(string asis) ///
        YLIne(string asis)        LEGend(string asis)       BY(string asis) ///
        XSCale(string asis)       YSCale(string asis)       ASPectratio(string) ///
        SCHeme(string)            PLOTRegion(string asis)   GRAPHRegion(string asis) ///
        BGColor(string)           PLOTBGCOLOR(string)       LINK(string) ///
        FILTer(string asis)       YTITLE2(string)           XTITLE2(string) ///
        YLABEL2(string asis)      XLABEL2(string asis)      YSCALE2(string asis) ///
        XSCALE2(string asis)      XSIZe(string)             YSIZe(string) ///
        FXSIZE(string)            FYSIZE(string)            SCALE(string) ///
        TEXT(string asis)         XTICk(string asis)        YTICk(string asis) ///
        HOVer(string)             ///
        XMTick(string asis)       YMTick(string asis)       XMLabel(string asis) ///
        YMLabel(string asis)      T1title(string)           T2title(string) ///
        B1title(string)           B2title(string)           L1title(string) ///
        L2title(string)           R1title(string)           R2title(string) ///
        TITLE2(string)            SUBTITLE2(string)         NODRAW ///
        PLAY(string) ///
        BW(string)                MLG(string)               CV(string) ///
        COLV(string)              PBGC(string)              XLA2(string asis) ///
        XSC2(string asis)         XTI2(string)              YLA2(string asis) ///
        YSC2(string asis)         YTI2(string) ///
        * ///
    ]
    /* ---- plot-level ---- */

    // twoway accepts t(), b(), l() and r() as abbreviations of t1title(),
    // b1title(), l1title() and r1title().  Stata derives the minimum from the
    // leading run of capitals and the digit in "t1title" ends that run, so
    // "T1title" yields "t1", never "t".  The four single-letter forms are
    // declared separately and folded in here.  Measured against real twoway --
    // see test/fixtures/abbrev_truth.json.
    if `"`t'"' != "" & `"`t1title'"' == "" local t1title `"`t'"'
    if `"`b'"' != "" & `"`b1title'"' == "" local b1title `"`b'"'
    if `"`l'"' != "" & `"`l1title'"' == "" local l1title `"`l'"'
    if `"`r'"' != "" & `"`r1title'"' == "" local r1title `"`r'"'
    // Fold alias forms onto their real option locals.  These are
    // ALIASES, not prefixes, so Stata's truncation-based abbreviation
    // cannot express them; they are declared above and merged here.
    // twoway accepts none of them, so this is a superset and cannot
    // break drop-in parity, but it keeps existing dash do-files working.
    // twoway histogram spells the bin count bins(); dash historically
    // declared only bin().  Stata accepts bin(), bins() and b() -- all
    // measured -- and they mean the same thing.
    if `"`bins'"' != "" & `"`bin'"' == "" local bin `"`bins'"'

    // level() is no longer checked here: its rule (level=num,0,100,x) lives
    // in _dash_option_rules and runs in _dash_validate_opts, once per segment.

    // bw() is NOT folded here: what it means depends on the plot type,
    // which this parser does not know.  twoway reads bw() as bwidth() on
    // the bandwidth types and rejects it everywhere else; _dash_fold_bw,
    // called by _dash_process_segment once the type is known, resolves
    // it.  It used to become barwidth() on every type, so
    // `dash (lpoly mpg weight, bw(400))' drew the rule-of-thumb bandwidth
    // and said nothing.
    if `"`mlg'"' != "" & `"`mlabgap'"' == "" local mlabgap `"`mlg'"'
    if `"`cv'"' != "" & `"`colorvar'"' == "" local colorvar `"`cv'"'
    if `"`colv'"' != "" & `"`colorvar'"' == "" local colorvar `"`colv'"'
    if `"`pbgc'"' != "" & `"`plotbgcolor'"' == "" local plotbgcolor `"`pbgc'"'
    if `"`xla2'"' != "" & `"`xlabel2'"' == "" local xlabel2 `"`xla2'"'
    if `"`xsc2'"' != "" & `"`xscale2'"' == "" local xscale2 `"`xsc2'"'
    if `"`xti2'"' != "" & `"`xtitle2'"' == "" local xtitle2 `"`xti2'"'
    if `"`yla2'"' != "" & `"`ylabel2'"' == "" local ylabel2 `"`yla2'"'
    if `"`ysc2'"' != "" & `"`yscale2'"' == "" local yscale2 `"`ysc2'"'
    if `"`yti2'"' != "" & `"`ytitle2'"' == "" local ytitle2 `"`yti2'"'

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
    if `"`at'"' != "" local _dash_pending `"`_dash_pending' at"'
    if `"`b1title'"' != "" local _dash_pending `"`_dash_pending' b1title"'
    if `"`b2title'"' != "" local _dash_pending `"`_dash_pending' b2title"'
    if `"`blabel'"' != "" local _dash_pending `"`_dash_pending' blabel"'
    if `"`ciopts'"' != "" local _dash_pending `"`_dash_pending' ciopts"'
    if `"`cmissing'"' != "" local _dash_pending `"`_dash_pending' cmissing"'
    if `"`colorlist'"' != "" local _dash_pending `"`_dash_pending' colorlist"'
    if `"`coloruseplegend'"' != "" local _dash_pending `"`_dash_pending' coloruseplegend"'
    if `"`connect'"' != "" local _dash_pending `"`_dash_pending' connect"'
    // As in the graph-level block: build-time options written on a graph.
    if `"`filter'"' != "" local _dash_pending `"`_dash_pending' filter"'
    if `"`fitopts'"' != "" local _dash_pending `"`_dash_pending' fitopts"'
    if `"`fxsize'"' != "" local _dash_pending `"`_dash_pending' fxsize"'
    if `"`fysize'"' != "" local _dash_pending `"`_dash_pending' fysize"'
    if `"`horizontal'"' != "" local _dash_pending `"`_dash_pending' horizontal"'
    if `"`l1title'"' != "" local _dash_pending `"`_dash_pending' l1title"'
    if `"`l2title'"' != "" local _dash_pending `"`_dash_pending' l2title"'
    if `"`link'"' != "" local _dash_pending `"`_dash_pending' link"'
    if `"`lineopts'"' != "" local _dash_pending `"`_dash_pending' lineopts"'
    if `"`lstyle'"' != "" local _dash_pending `"`_dash_pending' lstyle"'
    if `"`mlabwidth'"' != "" local _dash_pending `"`_dash_pending' mlabwidth"'
    if `"`mlpattern'"' != "" local _dash_pending `"`_dash_pending' mlpattern"'
    if `"`mlstyle'"' != "" local _dash_pending `"`_dash_pending' mlstyle"'
    if `"`mstyle'"' != "" local _dash_pending `"`_dash_pending' mstyle"'
    if `"`play'"' != "" local _dash_pending `"`_dash_pending' play"'
    if `"`pstyle'"' != "" local _dash_pending `"`_dash_pending' pstyle"'
    if `"`r1title'"' != "" local _dash_pending `"`_dash_pending' r1title"'
    if `"`r2title'"' != "" local _dash_pending `"`_dash_pending' r2title"'
    if `"`recast'"' != "" local _dash_pending `"`_dash_pending' recast"'
    if `"`scale'"' != "" local _dash_pending `"`_dash_pending' scale"'
    if `"`sort'"' != "" local _dash_pending `"`_dash_pending' sort"'
    if `"`subtitle2'"' != "" local _dash_pending `"`_dash_pending' subtitle2"'
    if `"`t1title'"' != "" local _dash_pending `"`_dash_pending' t1title"'
    if `"`t2title'"' != "" local _dash_pending `"`_dash_pending' t2title"'
    if `"`text'"' != "" local _dash_pending `"`_dash_pending' text"'
    if `"`title2'"' != "" local _dash_pending `"`_dash_pending' title2"'
    if `"`vertical'"' != "" local _dash_pending `"`_dash_pending' vertical"'
    if `"`xmlabel'"' != "" local _dash_pending `"`_dash_pending' xmlabel"'
    if `"`xmtick'"' != "" local _dash_pending `"`_dash_pending' xmtick"'
    if `"`ymlabel'"' != "" local _dash_pending `"`_dash_pending' ymlabel"'
    if `"`ymtick'"' != "" local _dash_pending `"`_dash_pending' ymtick"'
    // scheme(), xsize(), ysize(), xtick() and ytick() are NOT listed.  They
    // are twoway GRAPH-level options, and this program promotes them --
    // `sreturn local g_xsize' and friends just above, picked up by the
    // promotion loop in _dash_process_segment -- so however they are
    // written they reach the renderer and are honoured.  Naming them here
    // told a user who typed dash.sthlp's own example,
    //     dash scatter mpg weight, xsize(10) ysize(2)
    // that dash had ignored two options it had just applied.
    // Whatever Stata could not match at all, via the trailing *.
    local _dash_unknown `"`options'"'

    sreturn local mcolor           `"`mcolor'"'
    sreturn local msymbol          `"`msymbol'"'
    sreturn local msize            `"`msize'"'
    sreturn local msangle          `"`msangle'"'
    sreturn local mfcolor          `"`mfcolor'"'
    sreturn local mlcolor          `"`mlcolor'"'
    sreturn local mlabel           `"`mlabel'"'
    sreturn local mlabcolor        `"`mlabcolor'"'
    sreturn local mlabsize         `"`mlabsize'"'
    sreturn local mlabposition     `"`mlabposition'"'
    sreturn local mlabgap          `"`mlabgap'"'
    sreturn local mlabwidth        `"`mlabwidth'"'
    sreturn local malpha           `"`malpha'"'
    sreturn local marker           `"`marker'"'
    sreturn local lcolor           `"`lcolor'"'
    sreturn local lwidth           `"`lwidth'"'
    sreturn local lpattern         `"`lpattern'"'
    sreturn local lalpha           `"`lalpha'"'
    sreturn local fcolor           `"`fcolor'"'
    sreturn local fintensity       `"`fintensity'"'
    sreturn local falpha           `"`falpha'"'
    sreturn local barwidth         `"`barwidth'"'
    sreturn local base             `"`base'"'
    sreturn local blcolor          `"`blcolor'"'
    sreturn local bfcolor          `"`bfcolor'"'
    sreturn local jitter           `"`jitter'"'
    sreturn local jseed            `"`jseed'"'
    sreturn local yaxis            `"`yaxis'"'
    sreturn local xaxis            `"`xaxis'"'
    sreturn local colorvar         `"`colorvar'"'
    sreturn local colpalette       `"`colpalette'"'
    sreturn local colordiscrete    `"`colordiscrete'"'
    sreturn local coloruseplegend  `"`coloruseplegend'"'
    sreturn local colornlevels     `"`colornlevels'"'
    sreturn local colorcuts        `"`colorcuts'"'
    sreturn local colormissing     `"`colormissing'"'
    sreturn local bwidth           `"`bwidth'"'
    sreturn local bw               `"`bw'"'
    sreturn local degree           `"`degree'"'
    sreturn local pstyle           `"`pstyle'"'
    sreturn local cmissing         `"`cmissing'"'
    sreturn local recast           `"`recast'"'
    sreturn local connect          `"`connect'"'
    sreturn local bin              `"`bin'"'
    sreturn local width            `"`width'"'
    sreturn local start            `"`start'"'
    sreturn local percent          `"`percent'"'
    sreturn local frequency        `"`frequency'"'
    sreturn local density          `"`density'"'
    sreturn local fraction         `"`fraction'"'
    sreturn local kernel           `"`kernel'"'
    sreturn local n                `"`n'"'
    sreturn local level            `"`level'"'
    sreturn local bands            `"`bands'"'
    sreturn local at               `"`at'"'
    sreturn local ciopts           `"`ciopts'"'
    sreturn local lineopts         `"`lineopts'"'
    sreturn local fitopts          `"`fitopts'"'
    sreturn local color            `"`color'"'
    sreturn local mlwidth          `"`mlwidth'"'
    sreturn local mstyle           `"`mstyle'"'
    sreturn local lstyle           `"`lstyle'"'
    sreturn local mlstyle          `"`mlstyle'"'
    sreturn local mlpattern        `"`mlpattern'"'
    sreturn local blabel           `"`blabel'"'
    sreturn local horizontal       `"`horizontal'"'
    sreturn local vertical         `"`vertical'"'
    sreturn local sort             `"`sort'"'
    sreturn local range            `"`range'"'
    sreturn local colorlist        `"`colorlist'"'
    sreturn local jitterseed       `"`jitterseed'"'
    // The seven statistical sub-options (WP-18): declared with twoway's own
    // minimum abbreviations (twoway_histogram_parse.class DISCrete;
    // twoway_lfitci_parse.class STDP STDF STDR, none abbreviable;
    // twoway_lowess_parse.class Mean noWeight Adjust LOgit).  MEan is
    // declared one letter longer than twoway's `m': this parser also
    // declares Msymbol(), and test_abbreviations.py refuses a prefix two
    // options could claim.  Which type each belongs to is enforced by the
    // flag rules in _dash_option_rules, not here.
    sreturn local discrete         `"`discrete'"'
    sreturn local stdp             `"`stdp'"'
    sreturn local stdf             `"`stdf'"'
    sreturn local stdr             `"`stdr'"'
    sreturn local mean             `"`mean'"'
    sreturn local noweight         `"`noweight'"'
    sreturn local adjust           `"`adjust'"'
    sreturn local logit            `"`logit'"'
    /* ---- graph-level (returned separately so _dash_plot can accumulate them) ---- */
    sreturn local g_title        `"`title'"'
    sreturn local g_subtitle     `"`subtitle'"'
    sreturn local g_note         `"`note'"'
    sreturn local g_caption      `"`caption'"'
    sreturn local g_name         `"`name'"'
    sreturn local g_saving       `"`saving'"'
    sreturn local g_xtitle       `"`xtitle'"'
    sreturn local g_ytitle       `"`ytitle'"'
    sreturn local g_xlabel       `"`xlabel'"'
    sreturn local g_ylabel       `"`ylabel'"'
    sreturn local g_xline        `"`xline'"'
    sreturn local g_yline        `"`yline'"'
    sreturn local g_legend       `"`legend'"'
    sreturn local g_by           `"`by'"'
    sreturn local g_xscale       `"`xscale'"'
    sreturn local g_yscale       `"`yscale'"'
    sreturn local g_aspectratio  `"`aspectratio'"'
    sreturn local g_scheme       `"`scheme'"'
    sreturn local g_plotregion   `"`plotregion'"'
    sreturn local g_graphregion  `"`graphregion'"'
    sreturn local g_bgcolor      `"`bgcolor'"'
    sreturn local g_plotbgcolor  `"`plotbgcolor'"'
    sreturn local g_link         `"`link'"'
    sreturn local g_filter       `"`filter'"'
    sreturn local g_ytitle2      `"`ytitle2'"'
    sreturn local g_xtitle2      `"`xtitle2'"'
    sreturn local g_ylabel2      `"`ylabel2'"'
    sreturn local g_xlabel2      `"`xlabel2'"'
    sreturn local g_yscale2      `"`yscale2'"'
    sreturn local g_xscale2      `"`xscale2'"'
    sreturn local g_xsize        `"`xsize'"'
    sreturn local g_ysize        `"`ysize'"'
    sreturn local g_fxsize       `"`fxsize'"'
    sreturn local g_fysize       `"`fysize'"'
    sreturn local g_scale        `"`scale'"'
    sreturn local g_hover        `"`hover'"'
    sreturn local g_text         `"`text'"'
    sreturn local g_xtick        `"`xtick'"'
    sreturn local g_ytick        `"`ytick'"'
    sreturn local g_xmtick       `"`xmtick'"'
    sreturn local g_ymtick       `"`ymtick'"'
    sreturn local g_xmlabel      `"`xmlabel'"'
    sreturn local g_ymlabel      `"`ymlabel'"'
    sreturn local g_t1title      `"`t1title'"'
    sreturn local g_t2title      `"`t2title'"'
    sreturn local g_b1title      `"`b1title'"'
    sreturn local g_b2title      `"`b2title'"'
    sreturn local g_l1title      `"`l1title'"'
    sreturn local g_l2title      `"`l2title'"'
    sreturn local g_r1title      `"`r1title'"'
    sreturn local g_r2title      `"`r2title'"'
    sreturn local g_title2       `"`title2'"'
    sreturn local g_subtitle2    `"`subtitle2'"'
    sreturn local g_nodraw       `"`nodraw'"'
    sreturn local g_play         `"`play'"'
    sreturn local _pending  `"`_dash_pending'"'
    sreturn local _unknown  `"`_dash_unknown'"'
end


// ================================================================
// _dash_parse_varpart_std  — varlist [if] [in]  (1-to-many vars)
// Sets s(varlist), s(if_clause), s(in_clause)
// ================================================================
program define _dash_parse_varpart_std, sclass
    version 16.0
    syntax varlist [if] [in] [aweight fweight pweight iweight]
    // The weight type and its expression are handed to _dash_process_segment,
    // which honours, names or refuses them by plot type (WP-18).  syntax
    // leaves the expression in `exp' WITH its leading `= ' (measured:
    // `[aw=price]' gives exp `= price'); that is stripped here.
    if `"`weight'"' != "" sreturn local _weight `"`weight'"'
    if `"`exp'"' != "" sreturn local _wexp = strtrim(regexr(`"`exp'"', "^[ ]*=[ ]*", ""))
    sreturn local varlist    "`varlist'"
    sreturn local if_clause  `"`if'"'
    sreturn local in_clause  `"`in'"'
end

// ================================================================
// _dash_parse_varpart_1v   — exactly 1 variable
// ================================================================
program define _dash_parse_varpart_1v, sclass
    version 16.0
    syntax varlist(min=1 max=1) [if] [in] [aweight fweight pweight iweight]
    // The weight type and its expression are handed to _dash_process_segment,
    // which honours, names or refuses them by plot type (WP-18).  syntax
    // leaves the expression in `exp' WITH its leading `= ' (measured:
    // `[aw=price]' gives exp `= price'); that is stripped here.
    if `"`weight'"' != "" sreturn local _weight `"`weight'"'
    if `"`exp'"' != "" sreturn local _wexp = strtrim(regexr(`"`exp'"', "^[ ]*=[ ]*", ""))
    sreturn local varlist    "`varlist'"
    sreturn local if_clause  `"`if'"'
    sreturn local in_clause  `"`in'"'
end

// ================================================================
// _dash_parse_varpart_3v   — 2 to 3 variables (range plots)
// ================================================================
program define _dash_parse_varpart_3v, sclass
    version 16.0
    syntax varlist(min=2 max=3) [if] [in] [aweight fweight pweight iweight]
    // The weight type and its expression are handed to _dash_process_segment,
    // which honours, names or refuses them by plot type (WP-18).  syntax
    // leaves the expression in `exp' WITH its leading `= ' (measured:
    // `[aw=price]' gives exp `= price'); that is stripped here.
    if `"`weight'"' != "" sreturn local _weight `"`weight'"'
    if `"`exp'"' != "" sreturn local _wexp = strtrim(regexr(`"`exp'"', "^[ ]*=[ ]*", ""))
    sreturn local varlist    "`varlist'"
    sreturn local if_clause  `"`if'"'
    sreturn local in_clause  `"`in'"'
end

// ================================================================
// _dash_parse_varpart_4v   — exactly 4 variables (pc* plots)
// ================================================================
program define _dash_parse_varpart_4v, sclass
    version 16.0
    syntax varlist(min=4 max=4) [if] [in] [aweight fweight pweight iweight]
    // The weight type and its expression are handed to _dash_process_segment,
    // which honours, names or refuses them by plot type (WP-18).  syntax
    // leaves the expression in `exp' WITH its leading `= ' (measured:
    // `[aw=price]' gives exp `= price'); that is stripped here.
    if `"`weight'"' != "" sreturn local _weight `"`weight'"'
    if `"`exp'"' != "" sreturn local _wexp = strtrim(regexr(`"`exp'"', "^[ ]*=[ ]*", ""))
    sreturn local varlist    "`varlist'"
    sreturn local if_clause  `"`if'"'
    sreturn local in_clause  `"`in'"'
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
    syntax anything(name=vals equalok) [if] [in]
    sreturn local vals       `"`vals'"'
    sreturn local if_clause  `"`if'"'
    sreturn local in_clause  `"`in'"'
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
// ================================================================
program define _dash_fold_bw, sclass
    version 16.0
    args ptype
    local bw `"`s(bw)'"'
    if `"`bw'"' == "" exit
    local bandwidth_types "lpoly lpolyci lowess kdensity"
    local bar_types       "bar rbar histogram dot spike"
    if `: list ptype in bandwidth_types' {
        if `"`s(bwidth)'"' != "" {
            // twoway: the same option twice.  Measured r(198).
            display as error "option bwidth() may not be repeated: bw() is its abbreviation"
            exit 198
        }
        sreturn local bwidth `"`bw'"'
    }
    else if `: list ptype in bar_types' {
        if `"`s(barwidth)'"' == "" sreturn local barwidth `"`bw'"'
    }
    else {
        sreturn local _unknown `"`s(_unknown)' bw(`bw')"'
    }
    sreturn local bw ""
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
        colornlevels=int,2,256 ///
        colpalette=enum,viridis|magma|inferno|plasma|cividis|turbo|greys|blues|reds ///
        colorcuts=numlist,1  colorvar=var  mlabel=var  range=numlist,2,2
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
        scheme=scheme
    // Flag applicability (WP-18): flag[|flag...]@type[|type...].  A flag
    // written on a type outside its list is refused as twoway refuses it,
    // r(198) "option <flag> not allowed" (measured 23sep2026: scatter
    // discrete, lfit stdf, histogram mean, scatter noweight/logit/adjust,
    // lowess stdp).  Checked in _dash_validate_opts, which also refuses
    // more than one of stdp/stdf/stdr and discrete beside bin()/bins().
    local flags ///
        discrete@histogram  stdp|stdf|stdr@lfitci|qfitci ///
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
    args prefix opt spec value ptype

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
    local tv = ustrtrim(`"`macval(value)'"')
    tempname R
    scalar `R' = .
    capture scalar `R' = real(`"`macval(tv)'"')
    if _rc scalar `R' = .
    local isnum = (`R' < .)
    local plain   = regexm(`"`macval(tv)'"', "^[-+]?([0-9]+\.?[0-9]*|\.[0-9]+)([eE][-+]?[0-9]+)?$")
    local numlike = regexm(`"`macval(tv)'"', "^[-+.0-9eEdD]*[0-9][-+.0-9eEdD]*$")

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
            // such as 1d3 goes out as the number it read.
            if `plain' local norm `"`macval(tv)'"'
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
            if `plain' local norm `"`macval(tv)'"'
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
        local lv = lower(`"`macval(tv)'"')
        local choices : subinstr local p1 "|" " ", all
        local hit = 0
        foreach c of local choices {
            if `"`macval(lv)'"' == "`c'" local hit = 1
        }
        if `hit' local norm `"`macval(lv)'"'
        else {
            local pretty : subinstr local p1 "|" ", ", all
            local bad "one of `pretty'"
        }
    }
    else if "`kind'" == "numlist" {
        if "`p2'" == ""                      local bad "a list of at least `p1' numbers"
        else if "`p1'" == "`p2'"             local bad "a list of exactly `p1' numbers"
        else                                 local bad "a list of between `p1' and `p2' numbers"
        capture numlist `"`macval(value)'"'
        if !_rc {
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
    else if inlist("`kind'", "var", "varlist", "byvarlist") {
        local head `"`macval(value)'"'
        local tail ""
        local hastail = 0
        if "`kind'" == "byvarlist" {
            // Split at the first comma outside parentheses: the by-variables
            // come before it, the sub-options (kept verbatim) after it.
            local len = strlen(`"`macval(value)'"')
            local depth = 0
            local cut = 0
            forvalues i = 1/`len' {
                if substr(`"`macval(value)'"', `i', 1) == "(" {
                    local depth = `depth' + 1
                }
                else if substr(`"`macval(value)'"', `i', 1) == ")" {
                    local depth = `depth' - 1
                }
                else if substr(`"`macval(value)'"', `i', 1) == "," & `depth' == 0 {
                    local cut = `i'
                    continue, break
                }
            }
            if `cut' > 0 {
                local head = substr(`"`macval(value)'"', 1, `cut' - 1)
                local tail = strltrim(substr(`"`macval(value)'"', `cut' + 1, .))
                local hastail = 1
            }
            if strtrim(`"`macval(head)'"') == "" {
                display as error `"dash: by() must name at least one variable (got: `macval(value)')"'
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
            local badvar = strtrim(`"`macval(head)'"')
            local tsop = 0
            foreach tok of local head {
                capture confirm variable `macval(tok)'
                if _rc {
                    local badvar `"`macval(tok)'"'
                    if regexm(`"`macval(tok)'"', "^[LlFfDdSs][LlFfDdSs0-9()/]*\.[A-Za-z_]") local tsop = 1
                    continue, break
                }
            }
            if `ists' & `tsop' {
                display as error `"`prefix': `opt'() must name a variable, not a time-series expression (got: `macval(value)')"'
                exit 198
            }
            display as error `"`prefix': `opt'(): variable `macval(badvar)' not found"'
            exit 111
        }
        if "`kind'" == "var" & `: word count `vv'' > 1 {
            display as error `"`prefix': `opt'() must name one variable (got: `macval(value)')"'
            exit 198
        }
        local norm `"`vv'"'
        if `hastail' local norm `"`vv', `macval(tail)'"'
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
        local lv = lower(`"`macval(tv)'"')
        // A shipped name written WITH the extension -- scheme(s2color.scheme),
        // in any case -- is the shipped scheme: the renderer's _resolve_path
        // reads that spelling from the package's schemes/ too, so no file
        // in the working directory is needed.  Measured 22sep2026: the
        // extension form was looked for as a working-directory file only,
        // and scheme(s2color.scheme) was refused although the renderer
        // would have drawn it.  The extension is dropped for the list test
        // only: a theme is not a file and takes no extension, and a name
        // that is not shipped still needs the file (below).
        local lbase `"`macval(lv)'"'
        if substr(`"`macval(lv)'"', -7, .) == ".scheme" {
            local lbase = substr(`"`macval(lv)'"', 1, strlen(`"`macval(lv)'"') - 7)
        }
        local hit = 0
        foreach c of local _dash_schemes {
            if `"`macval(lbase)'"' == "`c'" local hit = 1
        }
        foreach c of local _dash_themes {
            if `"`macval(lv)'"' == "`c'" local hit = 1
        }
        if !`hit' & `"`macval(tv)'"' != "" {
            local unsafe = strpos(`"`macval(tv)'"', "/") | ///
                           strpos(`"`macval(tv)'"', char(92)) | ///
                           strpos(`"`macval(tv)'"', "..")
            if !`unsafe' {
                if substr(`"`macval(lv)'"', -7, .) == ".scheme" {
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
        if regexm(`"`macval(value)'"', "^%[A-Za-z0-9_.,:!/+-]+$") & strlen(`"`macval(value)'"') <= 60 {
            capture confirm numeric format `macval(value)'
            if !_rc local ok = 1
        }
        if !`ok' {
            display as error `"`prefix': `opt'() must be a numeric display format such as %9.2f or %12.0fc (got: `macval(value)')"'
            exit 198
        }
    }

    if `"`bad'"' != "" {
        display as error `"`prefix': `opt'() must be `bad' (got: `macval(value)')`extra'"'
        exit 198
    }
    c_local _dash_vnorm `"`macval(norm)'"'
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

    local _keys : s(macros)
    foreach _k of local _keys {
        local _snap_`_k' `"`s(`_k')'"'
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
    if `"`s(discrete)'"' != "" & `"`s(bin)'"' != "" {
        display as error "options discrete and bins() may not be combined"
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
        local v `"`s(`o')'"'
        if `"`macval(v)'"' == "" continue
        _dash_validate_value "dash" "`o'" "`spec'" `"`macval(v)'"' "`ptype'"
        foreach _k of local _keys {
            if `"`s(`_k')'"' == "" & `"`macval(_snap_`_k')'"' != "" {
                sreturn local `_k' `"`macval(_snap_`_k')'"'
            }
        }
        if `"`macval(_dash_vnorm)'"' != `"`macval(v)'"' {
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
        local v `"`s(g_`o')'"'
        if `"`macval(v)'"' == "" continue
        _dash_validate_value "dash" "`o'" "`spec'" `"`macval(v)'"' ""
        foreach _k of local _keys {
            if `"`s(`_k')'"' == "" & `"`macval(_snap_`_k')'"' != "" {
                sreturn local `_k' `"`macval(_snap_`_k')'"'
            }
        }
        if `"`macval(_dash_vnorm)'"' != `"`macval(v)'"' {
            sreturn local g_`o' `"`macval(_dash_vnorm)'"'
        }
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
// ceiling.  dash.ado enforces three itself -- cells (values embedded:
// observations x variables exported), graphs (graphs and KPI cards in the
// registry) and plots (plot entries in one graph, one per y variable) --
// and hands every limit the session has set to the renderer as
// build_options.limits, under these keys, for the four it enforces:
// filter_options, by_groups, tabs and filters.
// ================================================================
program define _dash_limit_table
    version 16.0
    local rows ///
        cells=5000000,20000000 ///
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
// _dash_cell_cap <nvars> [<nobs>]  -- the embedded-data limit, before jsonio
//
// jsonio exports every observation of every variable it is given; the
// renderer applies if/in itself, so if/in reduce nothing here and are not
// offered as a remedy.  <nobs> is the observations exported, _N unless the
// caller exports fewer (the one-row placeholder a graph of literal values
// sends).  Both callers run this before the date-format swap that
// brackets jsonio, so a refusal leaves the data in memory and every
// display format exactly as they were.
// ----------------------------------------------------------------
program define _dash_cell_cap
    version 16.0
    args nvars nobs
    if "`nobs'" == "" local nobs = _N
    _dash_limit, name(cells)
    local lim  = r(value)
    local ceil = r(ceiling)
    if `nobs' * `nvars' <= `lim' exit

    _dash_count_fmt _cells_s `nobs' * `nvars'
    _dash_count_fmt _obs_s   `nobs'
    _dash_count_fmt _vars_s  `nvars'
    _dash_count_fmt _lim_s   `lim'
    _dash_count_fmt _ceil_s  `ceil'
    local _obs_w  = cond(`nobs' == 1, "observation", "observations")
    local _vars_w = cond(`nvars' == 1, "variable", "variables")
    display as error "dash: this dashboard would embed `_cells_s' values (`_obs_s' `_obs_w' x `_vars_s' `_vars_w'), more than the `_lim_s' dash embeds."
    display as error "      Reduce the data in memory first (keep, drop, sample or collapse, inside preserve/restore), or set global dash_max_cells to a higher value (at most `_ceil_s')."
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
    // is byte-identical to what it was.
    foreach key in mcolor msymbol msize msangle mfcolor mlcolor mlabel mlabcolor ///
                   mlabsize mlabposition mlabgap mlabwidth malpha marker lcolor ///
                   lwidth lpattern lalpha fcolor fintensity falpha barwidth base ///
                   blcolor bfcolor jitter jseed yaxis xaxis colorvar colpalette ///
                   colordiscrete coloruseplegend colornlevels colorcuts colormissing ///
                   bwidth degree pstyle cmissing recast connect bin width start ///
                   percent frequency density fraction kernel n level bands at ciopts ///
                   lineopts fitopts color mlwidth mstyle lstyle mlstyle mlpattern ///
                   blabel horizontal vertical sort range colorlist jitterseed ///
                   discrete stdp stdf stdr mean noweight adjust logit ///
                   weight wexp {
        local val `"`s(`key')'"'
        if `"`val'"' != "" {
            _dash_json_str `"`val'"' _jv
            if `nparts' > 0 local parts `"`parts',"'
            local parts `"`parts'"`key'":"`_jv'""'
            local nparts = `nparts' + 1
        }
    }

    c_local `out_macro' `"{`parts'}"'
end


// ================================================================
// _dash_graph_opts_to_json
//
// Build the "graph_options" JSON object from g_* locals.
// Clears g_* locals from the caller context when done.
// Returns JSON via c_local `out_macro'.
// ================================================================
program define _dash_graph_opts_to_json, rclass
    version 16.0
    args out_macro

    local parts ""
    local nparts = 0

    foreach key in name saving title subtitle note caption               ///
                   xtitle ytitle xlabel ylabel xline yline legend by     ///
                   xscale yscale aspectratio scheme plotregion graphregion ///
                   bgcolor plotbgcolor link filter                        ///
                   ytitle2 xtitle2 ylabel2 xlabel2 yscale2 xscale2 {
        local val `"`g_`key''"'
        if `"`val'"' != "" {
            _dash_json_str `"`val'"' _jv
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
    args seg_text plottype_out json_out nsegs
    if "`nsegs'" == "" local nsegs 1

    // ---- extract plot type (first word) ----
    gettoken plottype rest : seg_text
    mata: _dash_expand_plottype(strlower("`plottype'"), "_pt_exp")
    local ptype "`_pt_exp'"

    if "`ptype'" == "" {
        display as error "dash: unrecognised plot type '`plottype''. " _n ///
            "Supported: scatter line connected area bar spike " _n ///
            "lfit qfit lfitci qfitci lowess lpoly lpolyci fpfit fpfitci " _n ///
            "histogram kdensity rarea rbar rspike rcap rline rconnected " _n ///
            "dot dropline rcapsym scatteri pcspike pcarrow pcbarrow " _n ///
            "pci pcscatter tsline tsrline mspline mband rscatter function"
        exit(198)
    }

    // ---- find comma separating varpart from options ----
    local comma_pos = 0
    mata: _dash_comma_pos(`"`rest'"', "comma_pos")

    if `comma_pos' > 0 {
        local varpart  = strtrim(substr(`"`rest'"', 1, `comma_pos' - 1))
        local opts_raw = strtrim(substr(`"`rest'"', `comma_pos' + 1, .))
    }
    else {
        local varpart  = strtrim(`"`rest'"')
        local opts_raw ""
    }

    // ---- pre-expand option abbreviations ----
    local opts_exp ""
    if `"`opts_raw'"' != "" {
        // Option keys used to be rewritten here by Mata before -syntax- saw
        // them.  That pre-pass is gone: dash.ado now declares Stata's own
        // measured minimum abbreviations, so Stata resolves prefixes itself.
        local opts_exp `"`opts_raw'"'  
    }

    // ---- parse varlist + if/in using type-appropriate syntax program ----
    // Determine varpart syntax group for this plot type:
    //   1v  : histogram kdensity
    //   3v  : rarea rbar rspike rcap rline rconnected rcapsym rscatter tsrline
    //   4v  : pcspike pcarrow pcbarrow pcscatter
    //   any : scatteri pci function
    //
    // pcscatter takes FOUR VARIABLES in Stata -- `pcscatter y1 x1 y2 x2' --
    // and was routed to the literal parser, which wrote its variable names
    // into the spec as bare identifiers inside a JSON array:
    //     "values":[[mpg,weight],[mpg,price]]
    // which is not valid JSON.  The renderer read nothing from it and drew
    // an empty plot region, with rc 0 and no warning.
    //   std : everything else (including dot)

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

    if inlist("`ptype'", "histogram", "kdensity") {
        _dash_parse_varpart_1v `varpart'
        local yvar    = word("`s(varlist)'", 1)
        local if_cl   `"`s(if_clause)'"'
        local in_cl   `"`s(in_clause)'"'
    }
    else if inlist("`ptype'", "rarea", "rbar", "rspike", "rcap", "rline", ///
                               "rconnected", "rcapsym", "rscatter", "tsrline") {
        _dash_parse_varpart_3v `varpart'
        local vl = "`s(varlist)'"
        local yvar1 = word("`vl'", 1)
        local yvar2 = word("`vl'", 2)
        local xvar  = word("`vl'", 3)
        // `twoway tsrline lo hi' on tsset data is legal Stata and takes the
        // time variable as x.  The tsset fallback existed only on the
        // two-variable path, which tsrline never reaches -- it is a range
        // type and so parsed with 2 or 3 variables -- so the x column name
        // stayed empty and the render aborted asking for a time variable
        // the user had already set.
        if "`ptype'" == "tsrline" & "`xvar'" == "" {
            local xvar `"`_dta[_TStvar]'"'
            if `"`xvar'"' == "" {
                // r(111) is what twoway itself returns on un-tsset data.
                display as error "dash: tsrline needs a time variable. " ///
                    "Either tsset your data first, or give the x " ///
                    "variable explicitly, as in: dash tsrline `yvar1' `yvar2' timevar"
                exit(111)
            }
        }
        local if_cl `"`s(if_clause)'"'
        local in_cl `"`s(in_clause)'"'
    }
    else if inlist("`ptype'", "pcspike", "pcarrow", "pcbarrow", "pcscatter") {
        _dash_parse_varpart_4v `varpart'
        local vl = "`s(varlist)'"
        local y1var = word("`vl'", 1)
        local x1var = word("`vl'", 2)
        local y2var = word("`vl'", 3)
        local x2var = word("`vl'", 4)
        local if_cl `"`s(if_clause)'"'
        local in_cl `"`s(in_clause)'"'
    }
    else if inlist("`ptype'", "scatteri", "pci", "function") {
        _dash_parse_varpart_any `varpart'
        if "`ptype'" == "function" {
            // Remove optional "y=" prefix
            local vals = regexr(strtrim(`"`s(vals)'"'), "^[a-zA-Z][a-zA-Z0-9_]*[ ]*=[ ]*", "")
            local expr `"`vals'"'
        }
        else {
            local vals `"`s(vals)'"'
        }
        local if_cl `"`s(if_clause)'"'
        local in_cl `"`s(in_clause)'"'
    }
    else {
        // Standard: the LAST variable is x; every variable before it is a
        // y-variable and becomes its own plot, exactly as twoway does.
        //   twoway scatter mpg price weight  ->  two series
        // dash used to keep word 1 and the last word and silently discard
        // everything between, so that command drew ONE series and half the
        // user's data vanished with no error and no warning.
        if `"`varpart'"' != "" {
            _dash_parse_varpart_std `varpart'
            local vl = "`s(varlist)'"
            local nv : word count `vl'
            local yvar = word("`vl'", 1)
            if `nv' >= 2 {
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
                local yvarlist "`yvar'"
                // tsline/tsrline with no x take the time variable from tsset,
                // as twoway does.  Without this xvar stayed empty, the renderer
                // hit a KeyError on "" and the user saw r(7102).
                if inlist("`ptype'", "tsline", "tsrline") {
                    local xvar `"`_dta[_TStvar]'"'
                    if `"`xvar'"' == "" {
                        // r(111) is what twoway itself returns here, verified
                        // by probe: `twoway tsline mpg' on un-tsset data gives
                        // r(111), and rc=0 once the data are tsset.
                        display as error "dash: `ptype' needs a time variable. " ///
                            "Either tsset your data first, or give the x " ///
                            "variable explicitly, as in: dash `ptype' `yvar' timevar"
                        exit(111)
                    }
                }
                else {
                    // Every other type on this path takes a y AND an x.
                    // Measured 22sep2026 with the console binary: `twoway
                    // bar price', `twoway scatter mpg', and spike, area,
                    // line, dropline, connected, dot, the fit and the
                    // smoother types all say "too few variables specified"
                    // r(102).  dash registered such a segment with rc 0 and
                    // the build then died in Python on the empty x column,
                    // r(7102).  Refused here, before any JSON is written.
                    display as error "dash: `ptype' requires a y and an x variable (got: `vl')"
                    exit(102)
                }
            }
            local if_cl `"`s(if_clause)'"'
            local in_cl `"`s(in_clause)'"'
        }
    }

    // Strip the "if"/"in" keyword prefix that syntax leaves in the macros.
    // Stata may store `if' as either " if <expr>" (with leading space) or
    // "if <expr>" (without leading space) depending on the context.
    // Using regexr() to strip the prefix robustly handles both cases.
    local if_expr ""
    local in_expr ""
    if `"`if_cl'"' != "" {
        local if_expr = strtrim(regexr(`"`if_cl'"', "^[ ]*if[ ]+", ""))
    }
    if `"`in_cl'"' != "" {
        local in_expr = strtrim(regexr(`"`in_cl'"', "^[ ]*in[ ]+", ""))
    }

    // ---- parse options (clear stale sreturn values first) ----
    // The varpart parsers sreturn the weight TYPE in s(_weight) and the
    // weight EXPRESSION, without its leading `=', in s(_wexp).  Both are
    // saved before the clear below destroys them.
    local _seg_weight `"`s(_weight)'"'
    local _seg_wexp   `"`s(_wexp)'"'

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
    if `"`_seg_weight'"' != "" {
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
        else if inlist("`ptype'", "kdensity", "lpoly", "lpolyci") & "`_seg_weight'" == "pweight" {
            local _wt_refused "pweights not allowed"
        }
        if `"`_wt_refused'"' != "" {
            display as error "`_wt_refused'"
            exit 101
        }
    }
    if `"`_seg_weight'"' != "" & `: list ptype in _wt_honoured' {
        // The data reach the renderer through jsonio, one column per
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
        if !_rc capture unab _wx : `macval(_seg_wexp)'
        if _rc | `: word count `_wx'' != 1 {
            display as error `"dash: [`_seg_weight'=`macval(_seg_wexp)'] must name one variable; dash cannot evaluate a weight expression. Generate it first: generate double w = `macval(_seg_wexp)'"'
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
        local _wq ""
        if `"`macval(if_expr)'"' != "" local _wq `"if (`macval(if_expr)')"'
        if `"`macval(in_expr)'"' != "" local _wq `"`macval(_wq)' in `macval(in_expr)'"'
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
    // A weight-only segment goes through the parser and the validation
    // too, so the weight keys are in s() for the JSON writer and the flag
    // rules run on every segment; the parser takes an empty option list.
    if `"`opts_exp'"' != "" | `"`_seg_weight'"' != "" {
        _dash_parse_plot_opts , `opts_exp'
        _dash_fold_bw "`ptype'"
        if `"`_seg_weight'"' != "" & `: list ptype in _wt_honoured' {
            _dash_seg_weight_s "`_seg_weight'" "`_seg_wexp'"
        }
        _dash_validate_opts "`ptype'"
        // twoway__histogram_gen.ado:102-107: a start() above the variable's
        // minimum over the plot's sample is r(198), discrete or not.  dash
        // drew it, the observations below start() silently left out of
        // every bar (the WP-18 review, 23sep2026).
        if "`ptype'" == "histogram" & `"`s(start)'"' != "" {
            local _hq ""
            if `"`macval(if_expr)'"' != "" local _hq `"if (`macval(if_expr)')"'
            if `"`macval(in_expr)'"' != "" local _hq `"`macval(_hq)' in `macval(in_expr)'"'
            quietly summarize `yvar' `macval(_hq)', meanonly
            if r(N) > 0 {
                if r(min) < `s(start)' & reldif(r(min), `s(start)') > 1e-5 {
                    display as error "option start() may not be larger than minimum of `yvar'"
                    exit 198
                }
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
    c_local _seg_ignored_out `"`s(_pending)' `s(_unknown)'`_seg_wtok'"'

    // Accumulate graph-level options found in this segment into g_* locals
    // (these live in _dash_plot's frame, not here — use c_local to propagate)
    foreach gkey in title subtitle note caption name saving xtitle ytitle xlabel ///
            ylabel xline yline legend by xscale yscale aspectratio scheme ///
            plotregion graphregion bgcolor plotbgcolor link filter ytitle2 ///
            xtitle2 ylabel2 xlabel2 yscale2 xscale2 xsize ysize fxsize fysize ///
            scale text hover xtick ytick xmtick ymtick xmlabel ymlabel t1title ///
            t2title b1title b2title l1title l2title r1title r2title title2 ///
            subtitle2 nodraw play {
        local gval `"`s(g_`gkey')'"'
        if `"`gval'"' != "" {
            c_local g_`gkey' `"`gval'"'
        }
    }

    // ---- build plot JSON ----
    // Variable fields
    local vfields ""

    if inlist("`ptype'", "histogram", "kdensity") {
        _dash_json_str "`yvar'" _jyv
        local vfields `""var":"`_jyv'""'
    }
    else if inlist("`ptype'", "rarea", "rbar", "rspike", "rcap", "rline", ///
                               "rconnected", "rcapsym", "rscatter", "tsrline") {
        _dash_json_str "`yvar1'" _jy1
        _dash_json_str "`yvar2'" _jy2
        _dash_json_str "`xvar'"  _jxv
        local vfields `""yvar1":"`_jy1'","yvar2":"`_jy2'","xvar":"`_jxv'""'
    }
    else if inlist("`ptype'", "pcspike", "pcarrow", "pcbarrow", "pcscatter") {
        _dash_json_str "`y1var'" _jy1
        _dash_json_str "`x1var'" _jx1
        _dash_json_str "`y2var'" _jy2
        _dash_json_str "`x2var'" _jx2
        local vfields `""y1var":"`_jy1'","x1var":"`_jx1'","y2var":"`_jy2'","x2var":"`_jx2'""'
    }
    else if "`ptype'" == "function" {
        _dash_json_str `"`expr'"' _jex
        local vfields `""expr":"`_jex'""'
    }
    else if inlist("`ptype'", "scatteri", "pci") {
        // Encode as a JSON array of [y, x] pairs, each optionally followed by a
        // quoted marker label:   scatteri 20 3000 "A" 30 4000 "B"
        // This used to pair tokens blindly, checking only that the count was
        // even, so a labelled list came out sheared -- [[20,3000],["A",30],
        // [4000,"B"]] -- which is not even the right shape.
        local words_raw `"`vals'"'
        local np : word count `words_raw'
        // A point's label rides on its own pair as an optional third element,
        // [y, x, "label"], which is the shape map_scatteri reads.
        local arr "["
        local nfirst = 1
        local pi = 1
        while `pi' <= `np' {
            local yv `"`=word(`"`words_raw'"', `pi')'"'
            local xv `"`=word(`"`words_raw'"', `=`pi'+1')'"'
            if `"`xv'"' == "" {
                display as error "dash: `ptype' needs coordinates in y x pairs;" ///
                    " '`yv'' has no matching x value."
                exit(198)
            }
            local pi = `pi' + 2

            // A following NON-NUMERIC token is this point's marker label --
            // but ONLY for scatteri.  pci and pcscatter take four values per
            // record (pcscatter's are variable NAMES, which are non-numeric by
            // definition), so applying the heuristic there would swallow a
            // coordinate and shear the whole list.
            local lab ""
            if `pi' <= `np' & "`ptype'" == "scatteri" {
                local nxt `"`=word(`"`words_raw'"', `pi')'"'
                if missing(real(`"`nxt'"')) & `"`nxt'"' != "" {
                    local lab = subinstr(`"`nxt'"', `"""', "", .)
                    local pi = `pi' + 1
                }
            }

            if !`nfirst' local arr "`arr',"
            if `"`lab'"' == "" {
                local arr "`arr'[`yv',`xv']"
            }
            else {
                _dash_json_str `"`lab'"' _jlab
                local arr `"`arr'[`yv',`xv',"`_jlab'"]"'
            }
            local nfirst = 0
        }
        local arr "`arr']"
        local vfields `""values":`arr'"'
    }
    else {
        _dash_json_str "`yvar'" _jyv
        _dash_json_str "`xvar'" _jxv
        local vfields `""yvar":"`_jyv'","xvar":"`_jxv'""'
    }

    // Options JSON
    _dash_plot_opts_to_json _opts_json

    // if/in
    _dash_json_str "`if_expr'" _jif
    _dash_json_str "`in_expr'" _jin

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
// modified.
// ================================================================
program define _dash_formats_json
    version 16.0
    args varlist_in out_macro datevars_macro

    local parts ""
    local nparts = 0
    local datevars ""

    foreach v of local varlist_in {
        capture confirm variable `v'
        if _rc continue
        local f : format `v'
        if `"`f'"' == "" continue

        _dash_json_str `"`f'"' _fjv
        if `nparts' > 0 local parts `"`parts',"'
        local parts `"`parts'"`v'":"`_fjv'""'
        local nparts = `nparts' + 1

        // %t and %-t followed by one of the eight kind letters, case
        // sensitively: %tc and %tC are different formats.
        if regexm(`"`f'"', "^%-?t[cCdhmqwy]") {
            local datevars `"`datevars' `v'"'
        }
    }

    c_local `out_macro'      `"{`parts'}"'
    c_local `datevars_macro' `"`datevars'"'
end


// ================================================================
// _dash_date_fmts_swap / _dash_date_fmts_restore
//
// jsonio renders a %t* variable THROUGH its display format and emits a
// JSON string ("02jan2001"), while still reporting variableIsString=false
// for it.  The renderer then coerced that to a missing value and dropped
// every row, so `dash line close date` produced a dashboard containing no
// data at all.  Giving the variable a plain numeric format for the
// duration of the jsonio call transports the underlying value intact; the
// original format is restored immediately afterwards and travels
// separately in the "formats" map.
// ================================================================
program define _dash_date_fmts_swap
    version 16.0
    args datevars

    local saved ""
    foreach v of local datevars {
        local f : format `v'
        local saved `"`saved' `f'"'
        format `v' %12.0g
    }
    c_local _dash_saved_fmts `"`saved'"'
end

program define _dash_date_fmts_restore
    version 16.0
    args datevars saved

    local i = 0
    foreach v of local datevars {
        local ++i
        local f : word `i' of `saved'
        if `"`f'"' != "" capture format `v' `f'
    }
end

// ================================================================
// _dash_report_ignored  — one note per command naming every option
//                         dash accepted but did not honour
// ================================================================
program define _dash_report_ignored
    version 16.0
    args raw

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
    local raw `"`_dash_optnames'"'

    local seen ""
    local out  ""
    foreach tok of local raw {
        local ppos = strpos("`tok'", "(")
        if `ppos' > 0 local tok = substr("`tok'", 1, `ppos' - 1)
        local tok = strtrim("`tok'")
        if "`tok'" == "" continue

        local dup = 0
        foreach prev of local seen {
            if "`prev'" == "`tok'" local dup = 1
        }
        if `dup' continue

        local seen `"`seen' `tok'"'
        // A weight is not an option and takes no argument: [aweight], not
        // aweight().
        if substr("`tok'", 1, 1) == "[" local out `"`out' `tok'"'
        else                            local out `"`out' `tok'()"'
    }
    if `"`out'"' == "" exit

    display as text "dash: ignoring unsupported option(s):" as result `"`out'"'
end

// ================================================================
// _dash_plot  — parse and route a plot definition (v2.0)
// ================================================================
program define _dash_plot
    version 16.0

    // ---- UTF-8 safety check ----
    mata: _dash_check_utf8(strtrim(`"`0'"'))

    // ---- Split on || / () into segments + graph opts ----
    mata: _dash_split_segs(strtrim(`"`0'"'))
    // Now locals _n_segs, _seg_1 .. _seg_N, _graph_opts_raw are set.

    local n_segs   = `_n_segs'
    local gopts_raw `"`_graph_opts_raw'"'

    // ---- Initialise graph-level option accumulators ----
    foreach gk in title subtitle note caption name saving xtitle ytitle xlabel ///
          ylabel xline yline legend by xscale yscale aspectratio scheme ///
          plotregion graphregion bgcolor plotbgcolor link filter ytitle2 ///
          xtitle2 ylabel2 xlabel2 yscale2 xscale2 xsize ysize fxsize fysize ///
          scale text hover xtick ytick xmtick ymtick xmlabel ymlabel t1title ///
          t2title b1title b2title l1title l2title r1title r2title title2 ///
          subtitle2 nodraw play {
        local g_`gk' ""
    }

    // ---- Parse graph-level opts from paren-mode suffix (if any) ----
    if `"`gopts_raw'"' != "" {
        // Pre-expand abbreviations
        local gopts_exp ""
        local gopts_exp `"`gopts_raw'"'  
        _dash_parse_graph_opts , `gopts_exp'
        foreach gk in title subtitle note caption name saving xtitle ytitle xlabel ///
              ylabel xline yline legend by xscale yscale aspectratio scheme ///
              plotregion graphregion bgcolor plotbgcolor link filter ytitle2 ///
              xtitle2 ylabel2 xlabel2 yscale2 xscale2 xsize ysize fxsize fysize ///
              scale text hover xtick ytick xmtick ymtick xmlabel ymlabel t1title ///
              t2title b1title b2title l1title l2title r1title r2title title2 ///
              subtitle2 nodraw play {
            if `"`s(`gk')'"' != "" {
                local g_`gk' `"`s(`gk')'"'
                // Remembered so the segment loop below cannot overwrite it.
                // An option written after the top-level comma applies to the
                // GRAPH, and twoway lets it beat one written inside a plot:
                //     twoway (scatter y x, title("INSIDE")) (line y x), title("AFTER")
                // stores "AFTER" -- measured from the saved .gph.  dash
                // stored "INSIDE", because these accumulators are filled here
                // first and _dash_process_segment then c_locals over them.
                local _gafter_`gk' `"`s(`gk')'"'
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
        local _dash_gopt_ignored `"`s(_pending)' `s(_unknown)'"'
    }

    local _dash_ignored_acc `"`_dash_gopt_ignored'"'

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
    forvalues k = 1/`n_segs' {
        local seg `"`_seg_`k''"'

        local _seg_ignored_out ""
        local _seg_nplots_out  1
        _dash_process_segment `"`seg'"' _pt_k _json_k `n_segs'

        local _dash_nplots = `_dash_nplots' + `_seg_nplots_out'
        if `_dash_nplots' > `_dash_plot_lim' {
            // The graph's total is known only once its last segment is in.
            if `k' == `n_segs' {
                _dash_plot_cap_refuse `_dash_plot_lim' `_dash_plot_ceil' `_dash_nplots'
            }
            else _dash_plot_cap_refuse `_dash_plot_lim' `_dash_plot_ceil'
        }

        if `"`_seg_ignored_out'"' != "" {
            local _dash_ignored_acc `"`_dash_ignored_acc' `_seg_ignored_out'"'
        }

        // _dash_process_segment pushes any found graph-level opts
        // into g_* locals via c_local; they are now visible here.

        if `k' > 1 local plots_json `"`plots_json',"'
        local plots_json `"`plots_json'`_json_k'"'
    }

    // ---- An after-comma option outranks a segment's ----
    // Restored after the segment loop rather than guarded inside it: the
    // loop reaches the accumulators through c_local from another program,
    // so there is no single place inside it to test.  Only keys the
    // after-comma parse actually set are restored, so a graph that names an
    // option only inside a segment keeps that value.
    foreach gk in title subtitle note caption name saving xtitle ytitle xlabel ///
              ylabel xline yline legend by xscale yscale aspectratio scheme ///
              plotregion graphregion bgcolor plotbgcolor link filter ytitle2 ///
              xtitle2 ylabel2 xlabel2 yscale2 xscale2 xsize ysize fxsize fysize ///
              scale text hover xtick ytick xmtick ymtick xmlabel ymlabel t1title ///
              t2title b1title b2title l1title l2title r1title r2title title2 ///
              subtitle2 nodraw play {
        if `"`_gafter_`gk''"' != "" local g_`gk' `"`_gafter_`gk''"'
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
        local _vval `"`g_`_vopt''"'
        if `"`macval(_vval)'"' == "" continue
        _dash_validate_value "dash" "`_vopt'" "`_vspec'" `"`macval(_vval)'"' ""
        local g_`_vopt' `"`macval(_dash_vnorm)'"'
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
    if `"`g_name'"' != "" & `"`g_saving'"' != "" {
        local _dash_ignored_acc `"`_dash_ignored_acc' saving"'
    }
    if `"`_dash_ignored_acc'"' != "" {
        _dash_report_ignored `"`_dash_ignored_acc'"'
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
          subtitle2 nodraw play {
        local gv `"`g_`gk''"'
        if `"`gv'"' != "" {
            _dash_json_str `"`gv'"' _gjv
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
    // Only promote when there is ONE segment, in which case the qualifier was
    // written on the command as a whole.  With several segments each layer
    // carries its own if_expr and the renderer applies it per layer; promoting
    // the FIRST layer's qualifier here used to apply it to every layer, so
    //   dash (scatter y x) (scatter y x if foreign)
    // filtered both layers or neither.
    if `n_segs' == 1 {
        mata: _dash_json_get_str(`"`plots_json'"', "if_expr", "if_expr")
        mata: _dash_json_get_str(`"`plots_json'"', "in_expr", "in_expr")
    }
    _dash_json_str `"`if_expr'"' _jif_top
    _dash_json_str `"`in_expr'"' _jin_top

    local graph_json `"{"plots":[`plots_json'],"graph_options":`gopts_json',"if_expr":"`_jif_top'","in_expr":"`_jin_top'"}"'

    // ---- Route: named or immediate ----
    local graph_name `"`g_name'"'

    if `"`graph_name'"' != "" {
        _dash_register_graph `"`graph_name'"' `"`0'"' `"`graph_json'"'
    }
    else {
        _dash_render_immediate `"`graph_json'"' `"`0'"'
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
// _dash_register_graph  — store named graph in global registry
// ================================================================
// ================================================================
// _dash_drop_item  — retire every global a registry item owns
//
// Graphs and KPIs share one registry and one namespace, so replacing an
// item of one kind with the other has to take the loser's globals with it.
// A name left carrying both a `dash_json_' and a `dash_kpi_' marker is
// skipped at build time -- _dash_prepare_spec's graph loop passes over any
// entry with a KPI marker -- so the item the user just registered would
// vanish from the dashboard without a word.
//
// The names are resolved in Mata against what Stata actually holds, because
// `macro drop dash_kpi_g1*' would also take g10's, and g1 and g10 can both
// be registered at once.  See _dash_item_globals in dash_parse.mata.
// ================================================================
program define _dash_drop_item
    version 16.0
    args name

    mata: _dash_item_globals("`name'", "_dash_item_kill")
    foreach _g of local _dash_item_kill {
        capture macro drop `_g'
    }
end


program define _dash_register_graph
    version 16.0
    args name raw_spec json_spec

    // Split off a ", replace" sub-option BEFORE validating the name.  Stata's
    // name(string) captures the whole of "g1, replace", which then failed the
    // name regex below -- so name(g1, replace) was impossible, and the error
    // message further down told the user to type the very syntax that could
    // not work.
    local replace_flag = 0
    local _nm = strtrim(`"`name'"')
    if regexm(`"`_nm'"', "^([^,]+)[ \t]*,[ \t]*replace[ \t]*$") {
        local _nm = strtrim(regexs(1))
        local replace_flag = 1
    }
    local name `"`_nm'"'

    // Validate name format.  No bounded repetition such as {0,31}: regexm()
    // follows the CALLER's user version, and below 18 it runs Stata's old
    // engine, which does not know it -- every name was refused in a do-file
    // that began `version 16' (test_caller_version.cscript).  The length is
    // checked on its own, and it is 22, not 32: the name becomes part of the
    // globals dash_json_<name> and dash_spec_<name>, and a global's name is
    // at most 32 characters.  A 23- to 32-character name used to pass here
    // and then fail on the global with Stata's bare "invalid name".
    if !regexm("`name'", "^[a-zA-Z_][a-zA-Z0-9_]*$") | strlen("`name'") > 22 {
        // Echoed as text: a refused name may hold anything, and shown raw
        // name(a{bf:X}) printed a bold X -- the user's text drawn as SMCL.
        mata: st_local("_name_safe", ustrregexra(usubstr( ///
            st_local("name"), 1, 40), "[^A-Za-z0-9_.\-]", "?"))
        display as error "dash: invalid graph name '`_name_safe''. " ///
            "Names must start with a letter or underscore, contain only " ///
            "letters, digits, and underscores, and be at most 22 characters."
        exit(198)
    }

    // Paren-mode fallback: the sub-option may have been written on the graph
    // suffix rather than captured in name().
    if `replace_flag' == 0 {
        local raw_lower = lower(`"`raw_spec'"')
        if regexm(`"`raw_lower'"', "name\([^)]*,[ \t]*replace") {
            local replace_flag = 1
        }
    }

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

    // Store spec and JSON
    global dash_spec_`name' `"`raw_spec'"'
    global dash_json_`name' `"`json_spec'"'

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
    args json_spec raw_spec

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

    if `"`saving_path'"' != "" {
        // twoway accepts saving(name), saving(name.gph) and
        // saving(name, replace).  Normalise all three to a .html path BEFORE
        // validating: validation demands a .html suffix, and it used to run
        // before the suffix was appended, so every twoway-shaped saving()
        // aborted with r(198).
        local _sv = strtrim(`"`saving_path'"')
        if regexm(`"`_sv'"', "^(.+)[ \t]*,[ \t]*replace[ \t]*$") {
            local _sv = strtrim(regexs(1))
            local replace = "replace"
        }
        if regexm(lower(`"`_sv'"'), "\.gph$") {
            local _sv = substr(`"`_sv'"', 1, strlen(`"`_sv'"') - 4)
            display as text "dash: saving() writes HTML, not a Stata .gph;" ///
                " using `_sv'.html"
        }
        if !regexm(lower(`"`_sv'"'), "\.html$") local _sv `"`_sv'.html"'
        local saving_path `"`_sv'"'
        _dash_validate_path `"`saving_path'"'
        local saving_path `"`_dash_vpath'"'   // `~/' expanded, if it was there
    }
    else {
        tempfile saving_path_tmp
        local saving_path = "`saving_path_tmp'.html"
        local open_browser = 1
    }

    if !regexm(lower("`saving_path'"), "\.html$") {
        local saving_path = "`saving_path'.html"
    }

    // ---- Determine variables needed ----
    local needed_vars ""
    mata: _dash_extract_vars(`"`json_spec'"', "needed_vars")

    // ...including the ones named only in by() or in an if-qualifier.
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

    // scatteri, pci, pcscatter and function take literal coordinates or an
    // expression rather than variables, so having no varlist is correct for
    // them -- this guard used to reject those plot types outright.
    local _varfree = 0
    foreach _vf in scatteri pci pcscatter function {
        if strpos(`"`json_spec'"', `""type":"`_vf'""') > 0 local _varfree = 1
    }
    local _dash_placeholder = 0
    if "`needed_vars'" == "" & `_varfree' {
        // Nothing to serialise, but jsonio still needs a non-empty varlist, so
        // send ONE observation of one variable, which the renderer will not
        // read.  It used to send every observation of it: a function graph
        // over ten million observations exported ten million values for
        // nothing, and under the cell limit (WP-19) was refused for them.
        capture unab _allv : _all
        if _rc == 0 {
            local needed_vars : word 1 of `_allv'
            local _dash_placeholder = 1
        }
    }
    if "`needed_vars'" == "" {
        display as error "dash: no variables identified in plot specification."
        exit(198)
    }

    // ---- Serialize data via jsonio ----
    tempfile data_json_path spec_json_path

    // Always export ALL rows for the needed variables.  Do NOT pre-filter with
    // if/in qualifiers here: multiple plots in the same graph can have different
    // qualifiers, and applying only the first plot's qualifier would silently
    // discard rows needed by other plots.  Both renderers apply the qualifiers
    // themselves, through _dash_qualified_frame: the graph-level "if_expr" /
    // "in_expr" promoted to the graph JSON by _dash_plot, and then each plot's
    // own, to that layer alone.

    // Check jsonio
    capture which jsonio
    if _rc != 0 {
        display as error "dash: jsonio is required but not found. Run dash_setup first."
        exit(198)
    }

    // ---- Resource limits (WP-19), before anything is exported ----
    // Every dash_max_* global the session has set is validated here -- a
    // bad one is refused before the export, not after it -- and travels to
    // the renderer as build_options.limits.  Then the size of what jsonio
    // is about to embed, every observation of every variable in
    // needed_vars, is held to the cells limit.  Both come before the
    // date-format swap, so a refusal leaves the user's data and formats
    // exactly as they were.
    _dash_limits_json
    local _dash_lim_json `"`r(json)'"'
    local _dash_nvars : word count `needed_vars'
    local _dash_in ""
    if `_dash_placeholder' & _N > 0 local _dash_in "in 1"
    _dash_cell_cap `_dash_nvars' `=cond(`_dash_placeholder', min(_N, 1), _N)'

    // Collect display formats, and transport date variables as
    // numbers so jsonio does not render them to text.
    _dash_formats_json "`needed_vars'" _dash_fmt_json _dash_date_vars
    local _dash_saved_fmts ""
    if `"`_dash_date_vars'"' != "" {
        _dash_date_fmts_swap "`_dash_date_vars'"
    }
    quietly jsonio out `needed_vars' `_dash_in', ///
        what(all) filenm("`data_json_path'") ///
        metaprint(varnames varlabels vallabs labelnames)

    // Restore the user's formats immediately, whether or not
    // jsonio succeeded: the data in memory is theirs.
    if `"`_dash_date_vars'"' != "" {
        _dash_date_fmts_restore "`_dash_date_vars'" "`_dash_saved_fmts'"
    }

    // jsonio returns non-zero _rc as part of normal operation (internal Stata
    // commands like restore set _rc).  Check for actual failure by verifying
    // the output file was created, not by checking _rc.
    capture confirm file "`data_json_path'"
    if _rc != 0 {
        display as error "dash: jsonio failed to serialize data. " ///
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
        // On Windows, `start` treats its first quoted argument as the window
        // title, not the file path.  Supply an empty title ("") so the second
        // quoted argument is interpreted as the target file.
        if "`c(os)'" == "MacOSX"  shell open        "`saving_path'"
        if "`c(os)'" == "Windows" shell start "" "`saving_path'"
        if "`c(os)'" == "Unix"    shell xdg-open "`saving_path'"
    }
    else {
        display as text `"dash: dashboard saved to `saving_path'"'
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
    mata: _dash_check_utf8(strtrim(`"`0'"'))

    syntax anything(name=statspec) [if] [in] , ///
        TItle(string)           ///
        NAMe(string)            ///
        [ FMT(string)           ///
          SUBtitle(string)      ///
          COLOR(string)         ///
          BGCOLOR(string)       ///
          UPDate(string)        ///
        ]

    if !regexm(`"`statspec'"', "^([a-zA-Z0-9]+)\(([a-zA-Z_][a-zA-Z0-9_]*)\)$") {
        display as error "dash kpi: syntax is stat(varname), e.g. mean(mpg)."
        exit(198)
    }
    local stat    = regexs(1)
    local kpi_var = regexs(2)

    local valid_stats "mean sum count dcount min max median sd var cv iqr skewness p25 p50 p75"
    // pNN for any percentile, not just the three _pctile was frozen at.
    local is_pctile = 0
    if regexm("`stat'", "^p([0-9]+)$") local is_pctile = 1
    if `is_pctile' {
        local pnum = real(regexs(1))
        if `pnum' <= 0 | `pnum' >= 100 {
            display as error "dash kpi: percentile must be between 1 and 99"
            exit(198)
        }
    }
    if !`: list stat in valid_stats' & !`is_pctile' {
        display as error "dash kpi: unsupported statistic '`stat''. Choose from: `valid_stats'"
        exit(198)
    }

    confirm variable `kpi_var'

    // Split off a ", replace" sub-option BEFORE validating the name, exactly
    // as _dash_register_graph does: syntax's name(string) captures the whole
    // of "k1, replace", which would then fail the name regex below.
    local replace_flag = 0
    local _nm = strtrim(`"`name'"')
    if regexm(`"`_nm'"', "^([^,]+)[ \t]*,[ \t]*replace[ \t]*$") {
        local _nm = strtrim(regexs(1))
        local replace_flag = 1
    }
    local name `"`_nm'"'

    // The graph registrar's rule, without bounded repetition (see there).
    // A KPI's longest global is dash_kpi_<name>_stat, 14 characters around
    // the name, so its limit is 18.
    if !regexm("`name'", "^[a-zA-Z_][a-zA-Z0-9_]*$") | strlen("`name'") > 18 {
        // Echoed as text, as the graph registrar does (see there).
        mata: st_local("_name_safe", ustrregexra(usubstr( ///
            st_local("name"), 1, 40), "[^A-Za-z0-9_.\-]", "?"))
        display as error "dash kpi: invalid name '`_name_safe''. " ///
            "Names must start with a letter or underscore, contain only " ///
            "letters, digits, and underscores, and be at most 18 characters."
        exit(198)
    }

    // Every option is proven BEFORE anything is retired: measured
    // 22sep2026, `name(k, replace) fmt(bogus)' was refused correctly but
    // had already dropped the old KPI's globals while the registry still
    // listed k, and the next `dash build' died on the corrupt registry
    // with a JSON traceback (update(bogus) did the same).
    if "`update'" == "" local update "filter"
    if !inlist("`update'", "filter", "brush", "both") {
        display as error "dash kpi: update() must be filter, brush, or both."
        exit(198)
    }
    // fmt() is proven a single numeric display format here, before any
    // computation, so `: display' below can stay the formatter (WP-15).
    if `"`fmt'"' != "" _dash_validate_value "dash kpi" "fmt" "format" `"`fmt'"' ""

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

    local kpi_value ""

    if inlist("`stat'", "mean", "sum", "min", "max", "sd", "count") {
        quietly summarize `kpi_var' `if' `in'
        if      "`stat'" == "mean"  local kpi_value = r(mean)
        else if "`stat'" == "sum"   local kpi_value = r(sum)
        else if "`stat'" == "min"   local kpi_value = r(min)
        else if "`stat'" == "max"   local kpi_value = r(max)
        else if "`stat'" == "sd"    local kpi_value = r(sd)
        else if "`stat'" == "count" local kpi_value = r(N)
    }
    else if "`stat'" == "dcount" {
        // codebook is NOT r-class: r(unique) is always missing, so this
        // statistic has never produced a value.  Measured alternatives:
        // inspect gives r(N_unique) but stops reporting at 100 distinct and
        // is numeric-only; tabulate dies at 200k distinct; levelsof fails
        // once r(levels) exceeds c(macrolen).  egen group() has no ceiling,
        // works for string and numeric alike, and was the fastest measured.
        tempvar _dash_grp
        quietly egen `_dash_grp' = group(`kpi_var') `if' `in'
        quietly summarize `_dash_grp', meanonly
        local kpi_value = cond(r(N) == 0, 0, r(max))
    }
    else if "`stat'" == "median" {
        quietly _pctile `kpi_var' `if' `in', p(50)
        local kpi_value = r(r1)
    }
    else if "`stat'" == "iqr" {
        quietly _pctile `kpi_var' `if' `in', p(25 75)
        local kpi_value = r(r2) - r(r1)
    }
    else if `is_pctile' {
        // Any percentile, not the three p(25 50 75) was frozen at.
        quietly _pctile `kpi_var' `if' `in', p(`pnum')
        local kpi_value = r(r1)
    }
    else if inlist("`stat'", "var", "cv", "skewness") {
        quietly summarize `kpi_var' `if' `in', detail
        if      "`stat'" == "var"      local kpi_value = r(Var)
        else if "`stat'" == "cv"       local kpi_value = cond(r(mean)==0, ., r(sd)/r(mean))
        else if "`stat'" == "skewness" local kpi_value = r(skewness)
    }

    local kpi_display = "`kpi_value'"
    if `"`fmt'"' != "" {
        local kpi_display : display `fmt' `kpi_value'
        local kpi_display = strtrim("`kpi_display'")
    }

    // Store each KPI field in its own global so multi-word titles/subtitles
    // are preserved.  A marker global (value "1") allows the registry to
    // detect that this name is a KPI rather than a graph.
    global dash_kpi_`name'       "1"
    global dash_kpi_`name'_stat  "`stat'"
    global dash_kpi_`name'_var   "`kpi_var'"
    global dash_kpi_`name'_val   "`kpi_value'"
    global dash_kpi_`name'_disp  "`kpi_display'"
    global dash_kpi_`name'_fmt   "`fmt'"
    global dash_kpi_`name'_tit   "`title'"
    global dash_kpi_`name'_sub   "`subtitle'"
    global dash_kpi_`name'_col   "`color'"
    global dash_kpi_`name'_bg    "`bgcolor'"
    global dash_kpi_`name'_upd   "`update'"
    // The KPI's own if/in.  Stata computes the right value above and
    // stores it, but the renderer recomputes from the full frame, so
    // without these `dash kpi mean(mpg) if foreign==1` displayed the
    // UNCONDITIONAL mean.
    local _kif = strtrim(regexr(`"`if'"', "^[ ]*if[ ]+", ""))
    local _kin = strtrim(regexr(`"`in'"', "^[ ]*in[ ]+", ""))
    global dash_kpi_`name'_if    `"`_kif'"'
    global dash_kpi_`name'_in    `"`_kin'"'

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
// work out which variables have to be serialized, run jsonio, and
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
    mata: _dash_check_utf8(strtrim(`"`0'"'))

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
    ]

    if `"`cmdname'"' == "" local cmdname "dash build"

    // ---- inherit the preceding dash build's options ----
    //
    // Only what the user did not specify on this command.  An option
    // given here always wins; an option given on neither is empty, as
    // it was before.  Read through Mata rather than by expanding the
    // global inside quotes: these carry the user's own title() and
    // label() text, and expanding a value containing a double quote is
    // the failure this file has already been bitten by twice.
    if "`inherit'" != "" {
        foreach _bo in title subtitle layout link theme scheme tabs filterposition filter {
            local _cur : length local `_bo'
            if `_cur' == 0 {
                mata: st_local("_bo_val", st_global("dash_opts_" + st_local("_bo")))
                local _bolen : length local _bo_val
                if `_bolen' > 0 local `_bo' `"`_bo_val'"'
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
    if "`layout'" == "" local layout "auto"
    if "`layout'" != "auto" {
        // Require strictly positive integers in "N M" grid layout.
        // ^[1-9][0-9]* rejects zero and leading-zero forms (e.g. "0 0", "0 2").
        if !regexm("`layout'", "^[1-9][0-9]* [1-9][0-9]*$") & ///
           !regexm("`layout'", "^[a-zA-Z_][a-zA-Z0-9_]*:[0-9]+,[0-9]+") & ///
           !regexm(lower("`layout'"), "^bs") {
            display as error "`cmdname': layout() must be 'auto', 'N M' grid (N and M >= 1), 'name:row,col' placement, or 'bs[: spec]' Bootstrap layout."
            exit(198)
        }
    }

    // ---- validate filter_position ----
    if "`filterposition'" == "" local filterposition "top"
    if "`filterposition'" != "top" & "`filterposition'" != "left" {
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
    if "`link'" != "" & "`link'" != "_all" {
        local ntok_link : word count `link'
        forvalues k = 1/`ntok_link' {
            local lname : word `k' of `link'
            if !`: list lname in registry' {
                display as error "`cmdname': link() name '`lname'' not found in registry."
                exit(198)
            }
        }
    }

    // ---- validate filter() exclude() names ----
    // Iterate over ALL exclude(...) groups in the (possibly ||/;-joined) filter string.
    // Compound quotes throughout: the filter string carries the user's own
    // label("...") text, and expanding it inside plain "..." ends the Stata
    // string at the first quote.  Measured: filter(weight, type(range)
    // label("Curb weight")) died here with `type mismatch' r(109), which
    // names neither the option nor the cause.
    local _flen0 : length local filter
    if `_flen0' > 0 {
        local _excl_rem `"`filter'"'
        local _excl_pos = strpos(`"`_excl_rem'"', "exclude(")
        while `_excl_pos' > 0 {
            local _excl_inner = substr(`"`_excl_rem'"', `_excl_pos' + 8, .)
            local _excl_end   = strpos(`"`_excl_inner'"', ")")
            if `_excl_end' > 0 {
                local _excl_names = strtrim(substr(`"`_excl_inner'"', 1, `_excl_end' - 1))
                local n_excl : word count `_excl_names'
                forvalues ke = 1/`n_excl' {
                    local ename : word `ke' of `_excl_names'
                    if !`: list ename in registry' {
                        display as error "`cmdname': filter exclude() name '`ename'' not found in registry."
                        exit(198)
                    }
                }
                // Advance past the closing ) of this exclude() group
                local _excl_rem = substr(`"`_excl_inner'"', `_excl_end' + 1, .)
            }
            else {
                // Malformed exclude() — no closing paren; stop scanning
                continue, break
            }
            local _excl_pos = strpos(`"`_excl_rem'"', "exclude(")
        }
    }

    // Do NOT substitute "default" for an unspecified theme.  "default" is a
    // real theme name that resolves to s2color, so writing it here made the
    // session's own c(scheme) unreachable -- the renderer's precedence is
    // scheme() then theme() then c(scheme), and a theme was always present.
    // An empty theme means "the user did not ask", which is the truth.

    // ---- determine all variables needed ----
    local all_vars ""
    local ntok_reg : word count `registry'
    forvalues k = 1/`ntok_reg' {
        local gname : word `k' of `registry'

        if "${dash_kpi_`gname'}" != "" {
            local kpi_var = "${dash_kpi_`gname'_var}"
            if !`: list kpi_var in all_vars' local all_vars "`all_vars' `kpi_var'"
            // A KPI qualifier may name variables that appear nowhere else
            // (dash kpi mean(mpg) if foreign==1 needs foreign serialised, or
            // the renderer cannot reproduce the conditional value).
            local _kifx = "${dash_kpi_`gname'_if}"
            if `"`_kifx'"' != "" {
                _dash_json_str `"`_kifx'"' _kifx_esc
                local kqvars ""
                mata: _dash_extract_qual_vars(`"{"if_expr":"`_kifx_esc'"}"', "kqvars")
                foreach v of local kqvars {
                    capture confirm variable `v'
                    if _rc == 0 {
                        if !`: list v in all_vars' local all_vars "`all_vars' `v'"
                    }
                }
            }
            continue
        }

        // Use strlen to check if JSON global is set WITHOUT embedding JSON in a
        // double-quoted expression (which would break when JSON contains " chars)
        local _chk : strlen global dash_json_`gname'
        if `_chk' > 0 {
            local gvars ""
            mata: _dash_extract_vars(`"${dash_json_`gname'}"', "gvars")
            foreach v of local gvars {
                if !`: list v in all_vars' local all_vars "`all_vars' `v'"
            }
            // Also extract variables referenced only in qualifiers (if_expr)
            // and faceting (by) — these may not appear in any plot-variable key
            // but must be serialised so the renderer can apply them correctly.
            local qvars ""
            mata: _dash_extract_qual_vars(`"${dash_json_`gname'}"', "qvars")
            foreach v of local qvars {
                capture confirm variable `v'
                if _rc == 0 {
                    if !`: list v in all_vars' local all_vars "`all_vars' `v'"
                }
            }
        }
    }

    // ---- also include filter variables in the serialization ----
    // Filter variables (e.g. foreign from filter(foreign, type(dropdown)))
    // may not appear in any graph or KPI spec.  Without explicit inclusion,
    // jsonio would never serialize them, so the Python filter widgets would
    // be silently skipped.  Parse the || -delimited filter spec and add each
    // variable name (first token before the comma in each segment).
    if `"`filter'"' != "" {
        local _filt_work `"`filter'"'
        // Normalize semicolons to "||" so that semicolon-delimited multi-filter
        // strings (e.g. "foreign, type(dropdown); weight, type(range)") are split
        // the same way as the Python renderer's _parse_filter_raw does.
        local _filt_work = subinstr(`"`_filt_work'"', ";", "||", .)
        local _filt_done = 0
        while !`_filt_done' {
            local _pipe_pos = strpos(`"`_filt_work'"', "||")
            if `_pipe_pos' > 0 {
                local _this_seg = strtrim(substr(`"`_filt_work'"', 1, `_pipe_pos' - 1))
                local _filt_work = strtrim(substr(`"`_filt_work'"', `_pipe_pos' + 2, .))
            }
            else {
                local _this_seg = strtrim(`"`_filt_work'"')
                local _filt_done = 1
            }
            // Extract variable name: first word before the comma
            local _comma_pos = strpos(`"`_this_seg'"', ",")
            if `_comma_pos' > 0 {
                local _fvar = strtrim(substr(`"`_this_seg'"', 1, `_comma_pos' - 1))
            }
            else {
                local _fvar = word(`"`_this_seg'"', 1)
            }
            // A filter must name a real variable.  Silently skipping one
            // that does not look like a variable name meant
            //     dash build, filter(<script>alert, type(dropdown))
            // returned rc 0 and produced a dashboard carrying a filter that
            // did nothing, with no message anywhere.  Every other Stata
            // command rejects a name it cannot resolve, and so does this.
            //
            // The offending token is echoed only after being reduced to
            // characters that are safe to display: a value that reaches
            // here is by definition not a variable name, and interpolating
            // it into a message is the same hazard the path validator had.
            if !regexm("`_fvar'", "^[a-zA-Z_][a-zA-Z0-9_]*$") {
                // EVERY unsafe character, and at most 40: regexr()
                // replaced the first run only, so `a b{bf:X}{hline 5}'
                // printed a bold X and a rule -- the text drawn as SMCL,
                // which has {browse} and {stata} links to follow.
                mata: st_local("_fvar_safe", ustrregexra(usubstr( ///
                    st_local("_fvar"), 1, 40), "[^A-Za-z0-9_.\-]", "?"))
                display as error "`cmdname': filter() names '`_fvar_safe''," ///
                    " which is not a valid Stata variable name."
                exit(198)
            }
            capture confirm variable `_fvar'
            if _rc != 0 {
                display as error "`cmdname': filter() variable `_fvar' not found."
                exit(111)
            }
            if !`: list _fvar in all_vars' {
                local all_vars "`all_vars' `_fvar'"
            }
        }
    }

    local all_vars = strtrim("`all_vars'")

    if "`all_vars'" == "" {
        display as error "`cmdname': no variables identified across registered graphs."
        exit(198)
    }

    // ---- serialize data via jsonio ----
    capture which jsonio
    if _rc != 0 {
        display as error "dash: jsonio is required but not found. Run dash_setup first."
        exit(198)
    }

    // ---- resource limits (WP-19), before anything is exported ----
    // As on the immediate route: every dash_max_* global the session has
    // set is validated and carried to the renderer as build_options.limits,
    // and what jsonio is about to embed -- every observation of every
    // variable in all_vars -- is held to the cells limit.  Both come before
    // the date-format swap, so a refusal leaves the data and formats as
    // they were, and before `dash build' records its dash_opts_* globals.
    _dash_limits_json
    local _dash_lim_json `"`r(json)'"'
    local _dash_nvars : word count `all_vars'
    _dash_cell_cap `_dash_nvars'

    // Collect display formats, and transport date variables as
    // numbers so jsonio does not render them to text.
    _dash_formats_json "`all_vars'" _dash_fmt_json _dash_date_vars
    local _dash_saved_fmts ""
    if `"`_dash_date_vars'"' != "" {
        _dash_date_fmts_swap "`_dash_date_vars'"
    }
    quietly jsonio out `all_vars', ///
        what(all) filenm("`datapath'") ///
        metaprint(varnames varlabels vallabs labelnames)

    // Restore the user's formats immediately, whether or not
    // jsonio succeeded: the data in memory is theirs.
    if `"`_dash_date_vars'"' != "" {
        _dash_date_fmts_restore "`_dash_date_vars'" "`_dash_saved_fmts'"
    }

    capture confirm file "`datapath'"
    if _rc != 0 {
        display as error "`cmdname': jsonio failed to serialize data."
        exit(198)
    }

    // ---- assemble master JSON ----
    local graphs_json ""
    local n_graphs = 0

    forvalues k = 1/`ntok_reg' {
        local gname : word `k' of `registry'
        if "${dash_kpi_`gname'}" != "" {
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
        local graphs_json `"`graphs_json'${dash_json_`gname'}"'
        local n_graphs = `n_graphs' + 1
    }

    // assemble KPIs JSON
    local kpis_json ""
    local n_kpis = 0
    forvalues k = 1/`ntok_reg' {
        local gname : word `k' of `registry'
        if "${dash_kpi_`gname'}" == "" continue

        // Read each KPI field from its dedicated global (preserves multi-word values)
        // then JSON-escape the string fields before insertion.
        local kstat   = "${dash_kpi_`gname'_stat}"
        local kvar    = "${dash_kpi_`gname'_var}"
        local kval    = "${dash_kpi_`gname'_val}"
        local kdisp   = "${dash_kpi_`gname'_disp}"
        local kfmt    = "${dash_kpi_`gname'_fmt}"
        _dash_json_str `"${dash_kpi_`gname'_tit}"' _ktitle_esc
        _dash_json_str `"${dash_kpi_`gname'_sub}"' _ksub_esc
        _dash_json_str `"${dash_kpi_`gname'_col}"' _kcol_esc
        _dash_json_str `"${dash_kpi_`gname'_bg}"'  _kbg_esc
        local kupdate = "${dash_kpi_`gname'_upd}"
        _dash_json_str `"${dash_kpi_`gname'_if}"' _kif_esc
        _dash_json_str `"${dash_kpi_`gname'_in}"' _kin_esc
        _dash_json_str `"`kdisp'"' _kdisp_esc
        _dash_json_str `"`kfmt'"'  _kfmt_esc

        if `n_kpis' > 0 local kpis_json `"`kpis_json', "'
        local kpis_json `"`kpis_json'{"name":"`gname'","stat":"`kstat'","var":"`kvar'","value":"`kval'","display":"`_kdisp_esc'","fmt":"`_kfmt_esc'","title":"`_ktitle_esc'","subtitle":"`_ksub_esc'","color":"`_kcol_esc'","bgcolor":"`_kbg_esc'","update":"`kupdate'","if_expr":"`_kif_esc'","in_expr":"`_kin_esc'"}"'
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
    local _flen : length local filter
    if `_flen' > 0 _dash_json_str `"`filter'"' filter_json

    // Escape build-level title and subtitle for JSON safety
    _dash_json_str `"`title'"'    _title_esc
    _dash_json_str `"`subtitle'"' _subtitle_esc
    // Escape tabs string for JSON embedding
    _dash_json_str `"`tabs'"' _tabs_esc
    // Carry the session confidence level so the renderer does not have to
    // assume 95.  A per-plot level() overrides it.
    local _dash_lvl = c(level)
    // The session's own scheme.  A Stata user has already chosen how their
    // graphs should look; without this dash was the one command in the
    // session that ignored it.  An explicit scheme() or theme() still wins --
    // the renderer applies them in that order.
    local _dash_sess_scheme = c(scheme)
    _dash_json_str `"`scheme'"'            _scheme_esc
    _dash_json_str `"`_dash_sess_scheme'"' _sess_scheme_esc
    // theme() was the one user string on the master-spec line that went in
    // raw while every other went through _dash_json_str.  Measured:
    // theme("C:\temp\x"), theme("a\q"), theme("a\") and a theme()
    // containing a double quote each gave r(7102) and a Python
    // JSONDecodeError traceback, with no message from dash; theme("a\b")
    // gave rc 0 and silently delivered a BACKSPACE, because \b happens to
    // be a valid JSON escape.  The same values in scheme() were all fine.
    // link(), layout() and filterposition() are validated before this line
    // and reject such a value with r(198); tabs() is escaped already.
    _dash_json_str `"`theme'"'             _theme_esc
    local master_json `"{"graphs":[`graphs_json'],"kpis":[`kpis_json'],"build_options":{"layout":"`layout'","link":"`link'","filter":"`filter_json'","theme":"`_theme_esc'","scheme":"`_scheme_esc'","session_scheme":"`_sess_scheme_esc'","title":"`_title_esc'","subtitle":"`_subtitle_esc'","registry":"`registry'","tabs":"`_tabs_esc'","filter_position":"`filterposition'","level":"`_dash_lvl'","formats":`_dash_fmt_json',"limits":`_dash_lim_json'}}"'

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
    mata: _dash_check_utf8(strtrim(`"`0'"'))

    // Pre-extract ALL filter() options from `0' before -syntax- runs.
    // Stata's -syntax- only accepts one option of a given name; using two
    // filter() options (as in full_dashboard.do) would trigger an error.
    // _dash_extract_filters() scans `0', removes every filter(...) group,
    // joins their contents with " || ", and stores them in `_filter_parts'.
    // The cleaned command is stored in `_cmd_nofilter' and assigned back to
    // `0' so that -syntax- sees only the remaining options.
    mata: _dash_extract_filters("_filter_parts", "_cmd_nofilter")
    local filter `"`_filter_parts'"'
    local 0      `"`_cmd_nofilter'"'

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
    ]

    // ---- check registry is not empty ----
    if "${dash_graph_registry}" == "" {
        display as error "dash build: no graphs registered. Define graphs with name() before running dash build."
        exit(198)
    }

    // ---- validate saving() ----
    if "`saving'" == "" {
        display as error "dash build: saving() is required."
        exit(198)
    }
    if "`server'" != "" {
        if regexm("`saving'", "\.\.") {
            display as error "dash build: saving() path may not contain '..' (path traversal not allowed)."
            exit(198)
        }
        // The same validator, asked for .py.  This branch used to check the
        // extension and nothing else, so a server-mode path skipped the
        // traversal, metacharacter and quote checks entirely.
        _dash_validate_path `"`saving'"' "py"
        local saving `"`_dash_vpath'"'
    }
    else {
        _dash_validate_path `"`saving'"' "html"
        local saving `"`_dash_vpath'"'
    }

    if "`replace'" == "" {
        capture confirm new file "`saving'"
        if _rc != 0 {
            display as error "dash build: file '`saving'' already exists. Use replace option to overwrite."
            exit(198)
        }
    }

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

    _dash_prepare_spec, cmdname("dash build") ///
        specpath("`master_json_path'") datapath("`data_json_path'") ///
        filter(`"`filter'"') `_fwd_opts'

    // ---- remember these for a later dash serve ----
    //
    // dash.sthlp documents building a dashboard and then serving it live
    // with a bare `dash serve, port()'.  That only means anything if the
    // options survive the first command, so they are recorded here and
    // `dash serve' inherits any the user does not restate.
    global dash_opts_title          `"`title'"'
    global dash_opts_subtitle       `"`subtitle'"'
    global dash_opts_layout         `"`r(layout)'"'
    global dash_opts_link           `"`link'"'
    global dash_opts_theme          `"`theme'"'
    global dash_opts_scheme         `"`scheme'"'
    global dash_opts_tabs           `"`tabs'"'
    global dash_opts_filterposition `"`r(filterposition)'"'
    global dash_opts_filter         `"`filter'"'

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
        display as text `"dash build: server app written to `saving'"'
        // Point at the app's OWN launcher, not `bokeh serve'.  Both work for
        // the dashboard now, but `bokeh serve' owns its Tornado application
        // and gives an app script no supported way to register a route, so
        // the /health endpoint project rule 17 asks for exists only when the
        // app serves itself.  Running it directly also honours --port and
        // the websocket origins, and opens no browser unless asked.
        display as text `"  To launch: python "`saving'""'
        display as text `"  Options:   --port N  --show  --timeout MINUTES  (--help lists them all)"'
        display as text `"  Limits:    --sessions-per-client N  --new-clients-per-minute N  --sessions-per-minute N"'
    }
    else {
        display as text `"dash: dashboard saved to `saving'"'
        // nobrowser, or the global the certification runner sets once.
        // There was no way to suppress this at all: a suite that builds
        // twenty dashboards opened twenty browser tabs, and so did any
        // do-file run in batch.
        // A registered graph's nodraw keeps the window shut too, as the
        // help has always said it does.
        _dash_registry_nodraw
        if "`nobrowser'" == "" & "${dash_nobrowser}" == "" & r(nodraw) == 0 {
            if "`c(os)'" == "MacOSX"  shell open        "`saving'"
            if "`c(os)'" == "Windows" shell start "" "`saving'"
            if "`c(os)'" == "Unix"    shell xdg-open "`saving'"
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
    mata: _dash_check_utf8(strtrim(`"`0'"'))

    // Pre-extract every filter() group before -syntax- runs, exactly as
    // `dash build' does: -syntax- accepts one option of a given name, and
    // a dashboard may legitimately have several filters.
    mata: _dash_extract_filters("_filter_parts", "_cmd_nofilter")
    local filter `"`_filter_parts'"'
    local 0      `"`_cmd_nofilter'"'

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

    if "`port'"    == "" local port    "5006"
    if "`timeout'" == "" local timeout "0"

    if !regexm("`port'", "^[0-9]+$") {
        display as error "dash serve: port() must be a positive integer (got: `port')"
        exit(198)
    }
    local port_int = real("`port'")
    if `port_int' < 1024 | `port_int' > 65535 {
        display as error "dash serve: port() must be between 1024 and 65535 (got: `port')"
        exit(198)
    }
    if !regexm("`timeout'", "^[0-9]+$") {
        display as error "dash serve: timeout() must be a non-negative integer in minutes (got: `timeout')"
        exit(198)
    }

    if `"`specpath'"' == "" | `"`datapath'"' == "" {
        display as error "dash serve: internal error — specpath() and datapath() are required."
        exit(198)
    }

    // inherit: reuse the options of a `dash build' earlier in this session
    // for anything not restated here.  dash.sthlp documents exactly that
    // sequence, and without this the served dashboard silently lost the
    // filter the documented example builds it with.
    _dash_prepare_spec, cmdname("dash serve") inherit ///
        specpath(`"`specpath'"') datapath(`"`datapath'"') ///
        filter(`"`filter'"') `options'

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
    mata: _dash_check_utf8(strtrim(`"`0'"'))

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

    _dash_serve_spec, specpath("`master_json_path'") datapath("`data_json_path'") `_srv_fwd'

    local port_int   "`r(port)'"
    local timeout    "`r(timeout)'"
    local no_browser_flag ""
    if "`r(nobrowser)'" == "nobrowser" local no_browser_flag "--no-browser"

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
    // Assign the result.  A single-line `python:' echoes the value of the
    // expression, and run_path returns the module globals dict, so this
    // line used to dump dash_render.py's whole namespace into the Stata log
    // on every render -- roughly 10 KB of noise per command.
    python: _dash_serve_ns = runpy.run_path("`_py_render'", run_name="__main__")
end
