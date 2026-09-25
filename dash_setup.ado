*! dash_setup.ado
*! Installs and verifies all dependencies required by the dash command.
*!
*! Dependencies checked:
*!   - Python (via c(python_exec); its version, read from sys.version,
*!     is checked against the minimum)
*!   - Python packages: bokeh, numpy, pandas (all required; no plot type
*!                      needs scipy or statsmodels, see section 3)
*!   - dash's own files: dash_render.py and the shipped schemes
*!   (No Stata package: dash writes its data from Python and has not used
*!   jsonio since 24sep2026, so it neither checks nor installs it.)
*!
*! Usage: dash_setup
*!
*! Author:  (see dash.sthlp)
*! Version: 2.0  24sep2026

program define dash_setup
    version 16.0
    // dash_setup.sthlp's Syntax section is the bare command, and there was
    // no `syntax' line at all -- so `dash_setup, garbage(1)' ran the whole
    // setup and ignored the option in silence.
    syntax

    // Everything that went wrong, counted rather than merely displayed.
    // The summary below branches on these; it used to say "All dependencies
    // are satisfied" whatever had happened.  A FAILURE means dash cannot
    // work; a WARNING means dash works but something is done less well
    // than it could be (today: `packaging' could not be installed, so
    // versions are compared approximately).
    local n_fail 0
    local n_warn 0
    local fail_items ""
    local warn_items ""

    // ----------------------------------------------------------------
    // 1. Check Python availability
    // ----------------------------------------------------------------
    // The minimum Python dash_setup.sthlp advertises.  Held by a program
    // rather than a local so that a test can ask the code what it is
    // instead of parsing this file -- dash_setup.ado's own lines carry
    // compound quotes, and re-quoting them to scan for a pattern is
    // "too few quotes", r(132).
    _dash_pymin
    local c_pymin "`r(pymin)'"

    display as text _newline "{txt}dash_setup: checking dependencies..."
    display as text "{hline 60}"

    // Availability is CONFIGURATION, so it is read from configuration.
    // `capture python query' ran Python to ask whether Python was there,
    // and the certification suite has already paid for that mistake: the
    // first python call of a session returns a nonzero rc under the runner
    // on a machine where dash renders Bokeh output seconds later, so nine
    // scripts skipped and the runner printed ALL TESTS PASSED.  The
    // version is read below, from sys.version, once Python is known to be
    // configured.
    if `"`c(python_exec)'"' == "" {
        display as error "Python is not available to Stata."
        display as error "Please install Python `c_pymin' or later and link it to Stata:"
        display as error "  help python"
        local n_fail = `n_fail' + 1
        local fail_items `"`fail_items' Python (not linked to Stata)"'
        _dash_setup_summary , failures(`n_fail') warnings(`n_warn') ///
            items(`"`fail_items'`warn_items'"')
        exit 198
    }

    // Retrieve Python version string and compare it to the minimum.
    //
    // Any linked Python answers, and this step used to read the version
    // only to print it.  dash_setup.sthlp says this step verifies the
    // declared minimum, so it now does: a user on a too-old Python was
    // told "OK (version ...)" and sent on to fail later inside bokeh, with
    // a message about neither Python nor dash.
    python: import sys; from sfi import Macro; Macro.setLocal("pyver", sys.version.split()[0])
    _dash_pyver_ok "`pyver'" "`c_pymin'"
    local pyok = r(ok)
    if `pyok' == 1 {
        display as text "  Python ............. {res}OK{txt} (version `pyver')"
    }
    else if `pyok' == 0 {
        display as error "  Python ............. version `pyver' is below the minimum `c_pymin'."
        display as error "    bokeh and pandas will not install or import reliably."
        display as error "    Link Stata to Python `c_pymin' or later: {help python}"
        // Counted, not just printed.  This branch has never had an `exit',
        // so before this the run continued, installed against the too-old
        // interpreter, and ended by declaring success.
        local n_fail = `n_fail' + 1
        local fail_items `"`fail_items' Python `pyver' (needs `c_pymin')"'
    }
    else {
        display as text "  Python ............. {res}OK{txt} (version `pyver'; could not be compared to `c_pymin')"
    }

    // ----------------------------------------------------------------
    // 2. Ensure `packaging` is available before version comparisons
    // ----------------------------------------------------------------
    // packaging is used inside the per-package version-gate loop; install
    // it FIRST so the loop never hits ModuleNotFoundError mid-run.
    capture python: import packaging
    if _rc != 0 {
        display as text "  packaging .......... {res}missing{txt} — installing via pip..."
        // Its output was discarded, so a failure here gave no reason at
        // all.  The package loop below already prints pip's tail; this site
        // was the one that did not.
        python: ///
            import subprocess, sys; ///
            r = subprocess.run( ///
                [sys.executable, "-m", "pip", "install", "packaging"], ///
                capture_output=True, text=True ///
            ); ///
            print(r.stdout[-500:] if r.stdout else ""); ///
            print(r.stderr[-200:] if r.stderr else "")
        // Mark whether packaging is now available
        capture python: import packaging
        if _rc != 0 {
            display as text "  packaging .......... {err}could not install{txt} — " ///
                "versions will be compared approximately"
            local pkg_has_packaging 0
            local n_warn = `n_warn' + 1
            local warn_items `"`warn_items' packaging (version checks approximate)"'
        }
        else {
            local pkg_has_packaging 1
        }
    }
    else {
        local pkg_has_packaging 1
    }

    // ----------------------------------------------------------------
    // 3. Check and install required Python packages
    // ----------------------------------------------------------------
    // Minimum version requirements stored as locals.
    //
    // bokeh, numpy and pandas are required -- dash_render.py imports them
    // at module scope, so without them nothing renders at all -- and they
    // are all dash needs.  scipy and statsmodels were OPTIONAL, one plot
    // type each (scipy for lfitci, qfitci, kdensity and mspline;
    // statsmodels for lowess), until every estimator became numpy code:
    // kdensity in S07, the rest in WP-18, which measured each against
    // Stata's own plotted points.  Nothing imports either any more, so
    // setup neither installs nor checks them.
    local pkg_list "bokeh numpy pandas"
    // The stata baseline of test/conftest.py, measured 25sep2026: Python
    // 3.13.9, bokeh 3.8.0, numpy 2.3.5, pandas 2.3.3 -- the versions both
    // test suites run under; nothing older is tested (GAPS2 K2).  Every
    // render imports CustomJSTicker, present only from bokeh 3.6.0, so an
    // installed bokeh 3.0-3.5 used to pass this check and then fail every
    // dash command with r(7102); pandas is declared here because bokeh
    // 3.9 no longer installs it as a dependency.
    local min_bokeh       "3.8"
    local min_numpy       "2.3"
    local min_pandas      "2.3"

    foreach pkg of local pkg_list {
        // Try importing the package; if it fails, pip-install it
        capture python: import `pkg'
        if _rc != 0 {
            display as text "  `pkg' ............. {res}missing{txt} — installing via pip..."
            // The minimum reaches pip.  It was declared just above and only
            // ever used AFTER the install, to grumble at what pip had
            // chosen; the command itself was a bare name, so a fresh
            // install could land below the minimum dash requires and then
            // be reported as being below it.
            local _spec "`pkg'"
            if "`min_`pkg''" != "" local _spec "`pkg'>=`min_`pkg''"
            python: ///
                import subprocess, sys; ///
                r = subprocess.run( ///
                    [sys.executable, "-m", "pip", "install", "`_spec'"], ///
                    capture_output=True, text=True ///
                ); ///
                print(r.stdout[-500:] if r.stdout else ""); ///
                print(r.stderr[-200:] if r.stderr else "")
            // A system Python the user cannot write to is the ordinary
            // reason this fails, and --user is the ordinary answer.  Tried
            // only when the import still fails, so a successful install
            // never triggers a second pip run.
            capture python: import `pkg'
            if _rc != 0 {
                display as text "      retrying with --user..."
                python: ///
                    import subprocess, sys; ///
                    r = subprocess.run( ///
                        [sys.executable, "-m", "pip", "install", "--user", "`_spec'"], ///
                        capture_output=True, text=True ///
                    ); ///
                    print(r.stdout[-500:] if r.stdout else ""); ///
                    print(r.stderr[-200:] if r.stderr else "")
            }
            // Re-check after install
            capture python: import `pkg'
            if _rc != 0 {
                display as error "  Failed to install `pkg'. Please install manually:"
                display as error "    python -m pip install `_spec'"
                // Still fatal -- nothing renders without bokeh, numpy and
                // pandas -- but routed through the summary so the exit code
                // and the message come from one place.
                local n_fail = `n_fail' + 1
                local fail_items `"`fail_items' `pkg' (could not install)"'
                _dash_setup_summary , failures(`n_fail') warnings(`n_warn') ///
                    items(`"`fail_items'`warn_items'"')
                exit 198
            }
        }

        // Retrieve installed version and compare to minimum
        local minver "`min_`pkg''"
        local pkgver ""
        _dash_pkg_version "`pkg'" pkgver

        // Version gate.  The four outcomes used to collapse into two, and
        // the `else' printed "OK (version unknown)" for every package
        // whenever `packaging' was missing -- although _dash_pkg_version had
        // already returned the real version.  A bokeh 2.4 was reported OK.
        _dash_setup_gate "`pkg'" "`pkgver'" "`minver'" `pkg_has_packaging'
        local verdict "`r(verdict)'"

        if "`verdict'" == "ok" {
            display as text "  `pkg' ............. {res}OK{txt}" ///
                " (version `pkgver')"
        }
        else if "`verdict'" == "below" {
            display as text "  `pkg' ............. {res}`pkgver'{txt}" ///
                " {err}(below minimum `minver'){txt}"
            // The Python Stata is linked to (Q27), never the bare word
            // `python': installing with a different interpreter would
            // upgrade the wrong Python.
            _dash_pip_command "`pkg'" "`minver'"
            display as text "      To upgrade: `r(cmd)'"
            // Reported as unmet rather than upgraded behind the user's
            // back: this package is already importable, so something else
            // in their environment may depend on the version they have.
            // AC-06.2 accepts either; reporting is the one that cannot
            // break unrelated work.
            local n_fail = `n_fail' + 1
            local fail_items `"`fail_items' `pkg' `pkgver' (needs `minver')"'
        }
        else if "`verdict'" == "unverified" {
            display as text "  `pkg' ............. {res}`pkgver'{txt}" ///
                " {txt}(not verified against `minver')"
        }
        else {
            display as text "  `pkg' ............. {res}installed{txt}" ///
                " (version could not be read)"
        }
    }

    // ----------------------------------------------------------------
    // 4. Check dash's own files
    // ----------------------------------------------------------------
    // Setup checked Python, its packages and (then) jsonio, and never asked
    // whether dash itself was reachable -- which is how an install whose
    // fourteen schemes all fell back to built-in defaults was reported as
    // "All dependencies are satisfied".
    _dash_setup_check_files
    if `=r(failures)' > 0 {
        local n_fail = `n_fail' + `=r(failures)'
        local fail_items `"`fail_items' dash's own files"'
    }

    // ----------------------------------------------------------------
    // 5. Summary
    // ----------------------------------------------------------------
    _dash_setup_summary , failures(`n_fail') warnings(`n_warn') ///
        items(`"`fail_items'`warn_items'"')

end


// ================================================================
// _dash_pkg_version  — installed version of a Python package
//
// Stores the version of `pkg' in the caller's local `outmac', or
// "unknown" if the package is not installed.
//
// This exists because the question cannot be asked with a try/except
// inside a `python: ///' continuation: the continuation joins its lines
// with "; ", and try/except are compound statements that cannot be
// joined that way.  Measured, the previous form raised
//     SyntaxError: invalid syntax
//     r(7102)
// so `pkgver' was never set and the comparison after it ran on an empty
// string.  A `python:' ... `end' block cannot be used either -- inside
// the foreach loop this is called from, the block swallows the loop's
// closing brace and everything up to the next `end'.
//
// The lookup below needs no exception handling at all: it scans the
// installed distributions and takes a default when none matches.
// ================================================================
program define _dash_pymin, rclass
    /*
        The minimum Python version dash requires, named once.

        returns r(pymin): the version string, e.g. "3.8".

        dash_setup displays it, _dash_pyver_ok compares against it, and
        test/test_setup_python_gate.cscript asserts dash_setup.sthlp states
        the same number -- so the help cannot drift from the check.
    */
    return local pymin "3.13"
end

program define _dash_pyver_ok, rclass
    version 16.0
    /*
        Is a dotted version string at or above a minimum?

        args:  got  -- the version to test, e.g. "3.10.0" or "3.8.0rc1"
               want -- the minimum, e.g. "3.8"

        returns r(ok):  1 at or above, 0 below, -1 unreadable.

        Compared component by component as NUMBERS.  A string comparison
        gets this wrong in the one case that matters most -- "3.10" sorts
        before "3.9" -- and that is how the check is usually botched.

        An unreadable version returns -1 rather than 0: refusing to set up
        on a version dash merely failed to parse is worse than proceeding.

        THE ANSWER IS DECIDED ONCE AND RETURNED AFTER THE LOOP.  Written the
        obvious way -- `return scalar ok = 0' followed by `exit' inside the
        forvalues -- neither took effect under `version 16.0', which is the
        version dash_setup declares and therefore the version this runs
        under in production.  Measured, with the loop body tracing itself:
        at i=1 for "2.4" against "3.0" it computed gnum=2, wnum=3, did not
        take either branch, and carried on to i=2; every input then fell
        through to the final `ok = 1'.  So the comparator answered "at or
        above" for EVERYTHING -- 3.7.9 >= 3.8 -> 1, 0.9 >= 1.5 -> 1 -- and
        the Python minimum dash_setup.sthlp advertises never fired at all.
        Called from a certification script, which runs under the session's
        own version rather than 16.0, the same program answered correctly,
        which is why test_setup_python_gate.cscript passed throughout.
    */
    args got want

    local got  = strtrim(`"`got'"')
    local want = strtrim(`"`want'"')
    if "`got'" == "" | "`want'" == "" {
        return scalar ok = -1
        exit
    }

    local gparts = subinstr("`got'", ".", " ", .)
    local wparts = subinstr("`want'", ".", " ", .)
    local ng : word count `gparts'
    local nw : word count `wparts'
    local n = max(`ng', `nw')

    local decided 0
    local answer  1
    forvalues i = 1/`n' {
        if `decided' == 0 {
            local g : word `i' of `gparts'
            local w : word `i' of `wparts'
            if "`g'" == "" local g "0"
            if "`w'" == "" local w "0"

            // A component may carry a suffix -- "0rc1" -- so take its
            // leading digits and ignore the rest.
            if !regexm("`g'", "^([0-9]+)") {
                local decided 1
                local answer -1
            }
            else {
                local gnum = real(regexs(1))
                if !regexm("`w'", "^([0-9]+)") {
                    local decided 1
                    local answer -1
                }
                else {
                    local wnum = real(regexs(1))
                    if `gnum' > `wnum' {
                        local decided 1
                        local answer 1
                    }
                    else if `gnum' < `wnum' {
                        local decided 1
                        local answer 0
                    }
                }
            }
        }
    }
    return scalar ok = `answer'
end

// ================================================================
// _dash_pip_command  — the pip install line dash_setup prints (Q27)
//
// The interpreter named is the one Stata is linked to (c(python_exec)),
// never the bare word `python': installing with a different interpreter
// than the one Stata runs against would upgrade the wrong Python, and a
// bare `python' could be Python 2 or an unrelated environment.  Called
// only from the `below' branch, after Python-not-linked has already
// exited the run (line 58), so c(python_exec) is never empty here.
//
// Syntax:
//   _dash_pip_command pkg minver
//   -> r(cmd): "<c(python_exec)> -m pip install '<pkg>>=<minver>'"
// ================================================================
program define _dash_pip_command, rclass
    version 16.0
    args pkg minver
    return local cmd `"`c(python_exec)' -m pip install '`pkg'>=`minver''"'
end

program define _dash_pkg_version
    version 16.0
    args pkg outmac

    // The name is READ inside Python with sfi.Macro.getLocal (below), so it
    // reaches the query as a string value and can never be parsed as code.
    // The regex is kept as defence in depth: it rejects an obviously bad name
    // up front, without touching Python at all.
    if !regexm("`pkg'", "^[A-Za-z0-9._-]+$") {
        c_local `outmac' "unknown"
        exit 0
    }

    // The version comes back from the distribution's metadata, which is as
    // untrusted as the name: dash_setup displays it, and passes it to
    // _dash_setup_gate inside double quotes.  A version holding {bf:X}
    // would be drawn as SMCL -- {stata} makes a link a click runs -- and
    // one holding a double quote would end the quotes it is passed in.  So
    // only a version made of the characters PEP 440 spells versions with,
    // 64 of them at most, is kept; anything else is "unknown".  re's
    // fullmatch, not Stata's regexm, whose `$' also matches before a
    // trailing newline.
    local _pv "unknown"
    capture python: import importlib.metadata as _im, re as _dash_re, sfi; _dash_pv = next((d.version for d in _im.distributions() if (d.metadata["Name"] or "").lower() == sfi.Macro.getLocal("pkg").lower()), "unknown"); sfi.Macro.setLocal("_pv", _dash_pv if isinstance(_dash_pv, str) and _dash_re.fullmatch(r"[A-Za-z0-9.+!_-]{1,64}", _dash_pv) else "unknown")
    if _rc != 0 local _pv "unknown"
    if "`_pv'" == "" local _pv "unknown"
    c_local `outmac' "`_pv'"
end


// ================================================================
// _dash_setup_summary  — the closing banner, told the truth
// ================================================================
// dash_setup used to end with four unconditional `display' lines saying
// "All dependencies are satisfied", and FOUR branches reached them after
// reporting a failure: Python below the minimum (which has no `exit'), a
// required package below its minimum, an optional package that could not be
// installed, and `packaging' itself failing.  A user on Python 3.7 was told
// their setup was fine and sent on to fail inside bokeh.
//
// It is a separate program so a certification script can drive it with the
// state it wants to report.  While the banner was four inline lines, the
// requirement "the summary must reflect what actually happened" could not
// be tested at all without pip-installing into the user's environment.
//
// Syntax:
//   _dash_setup_summary , FAILures(int) WARNings(int) [ITEMS(string)]
// ================================================================
program define _dash_setup_summary
    version 16.0
    syntax , FAILures(integer) WARNings(integer) [ITEMS(string)]

    display as text "{hline 60}"

    if `failures' > 0 {
        display as error "dash_setup did not complete: `failures' unmet " ///
            "requirement(s)."
        if `"`items'"' != "" {
            display as error "  Unmet: `items'"
        }
        display as error "  dash will not work until these are resolved."
        display as error "  Fix them and run {cmd:dash_setup} again."
        // Non-zero, so a do-file or CI step that runs dash_setup stops here
        // rather than carrying on to use a dash that cannot work.  198 is
        // what the other failing branches of this command already use.
        exit 198
    }

    if `warnings' > 0 {
        // A warning used to be an optional package, and this said the
        // layers needing it would render empty.  No package is optional
        // since WP-18; each item now says what it costs.
        display as text "{res}dash_setup complete{txt}, with `warnings' " ///
            "warning(s)."
        if `"`items'"' != "" {
            display as text "  Warned: `items'"
        }
        display as text "  dash works; each item above says what it costs."
    }
    else {
        display as text "{res}dash_setup complete.{txt} All dependencies are satisfied."
    }
    display as text "You can now use {cmd:dash} to create interactive dashboards."
    display as text "Type {cmd:help dash} to get started."
end


// ================================================================
// _dash_setup_gate  — is an installed version good enough?
// ================================================================
// Returns r(verdict), one of:
//   ok          at or above the minimum, established by `packaging'
//   below       under the minimum
//   unverified  a real version that could not be compared authoritatively
//   unknown     no version could be read at all
//
// The old gate collapsed the last three into
//     bokeh ............. OK (version unknown)
// whenever `packaging' was missing -- although _dash_pkg_version had
// already returned the real version (measured: bokeh 3.8.0, numpy 2.3.5,
// pandas 2.3.3, scipy 1.16.3, statsmodels 0.14.5).  So a bokeh 2.4 was
// reported OK.
//
// dash's own _dash_pyver_ok is used as the fallback, NOT as a replacement.
// Measured against packaging on nine pairs it agrees on six and disagrees
// on three, all pre/post-release forms:
//     0.13.0rc1 >= 0.13   _dash_pyver_ok 1, packaging 0
//     3.0b1     >= 3.0    _dash_pyver_ok 1, packaging 0
//     3.0.post1 >= 3.0    _dash_pyver_ok -1, packaging 1
// PEP 440 puts a release candidate before its release and the numeric
// comparator cannot see that.  So the fallback may report `below' (where it
// is conservative and safe) but never `ok' -- an at-or-above answer it
// produced alone is reported as `unverified'.
//
// Syntax:
//   _dash_setup_gate pkg got want has_packaging
// ================================================================
program define _dash_setup_gate, rclass
    version 16.0
    args pkg got want haspkg

    if `"`got'"' == "" | `"`got'"' == "unknown" {
        return local verdict "unknown"
        exit
    }

    // The fallback answer is computed FIRST, before anything that could
    // disturb r(), and the authoritative one overwrites it.  Written the
    // other way round -- try packaging, fall through on failure -- the
    // fallback's `r(ok)' read came after a `capture' and measured as
    // missing, so a bokeh 2.4 scored 0 by _dash_pyver_ok still came back
    // "unverified" instead of "below".  There is no fall-through here: the
    // verdict is always set before any branch runs.
    _dash_pyver_ok "`got'" "`want'"
    local n = r(ok)
    local verdict "unverified"
    if `n' == 0 local verdict "below"

    if "`haspkg'" == "1" {
        // `capture' because Version() raises InvalidVersion on a string it
        // cannot parse, and without it the whole of dash_setup ended at
        // r(7102) with no message of its own.  Measured on "0.1.0_1".
        //
        // `got' is an installed package's version, read from distribution
        // metadata by _dash_pkg_version -- UNTRUSTED.  It is handed to Python
        // with sfi.Macro.getLocal, NOT interpolated as `Version("`got'")': a
        // double quote in the value used to close the Python string so the
        // rest ran as code (measured: `1.0") == __import__("os").system(...)
        // or Version("1.0' created a file and returned "ok").  getLocal reads
        // THIS program's own locals, so `got' and `want' reach Version() as
        // string values that are never parsed.  test_setup_injection.cscript
        // drives this with hostile metadata; test_cscript_hygiene.py forbids
        // the interpolated form in either shipped ado file.
        local ver_ok ""
        capture python: ///
            from packaging.version import Version; ///
            import sfi; ///
            sfi.Macro.setLocal("ver_ok", ///
                "1" if Version(sfi.Macro.getLocal("got")) >= Version(sfi.Macro.getLocal("want")) else "0")
        if _rc == 0 {
            if "`ver_ok'" == "1" local verdict "ok"
            if "`ver_ok'" == "0" local verdict "below"
        }
    }

    return local verdict "`verdict'"
end


// ================================================================
// _dash_setup_check_files  — is dash itself installed and reachable?
// ================================================================
// dash_setup checked Python, its Python packages and (then) jsonio, and
// never asked whether dash's OWN files were reachable.  That is why a `net
// install' whose fourteen schemes all fell back to built-in defaults was
// reported as "All dependencies are satisfied" (see the BUGS.md entry).
//
// The schemes are checked by asking the RENDERER, not by `findfile'.
// findfile locates PLUS/s/s2color.scheme perfectly well on the very install
// where the renderer could not read a single scheme, so a findfile check
// would have passed on the broken tree it exists to catch.
//
// Returns r(failures), the number of things that are missing.
// ================================================================
program define _dash_setup_check_files, rclass
    version 16.0

    local nfail 0

    capture findfile dash_render.py
    if _rc != 0 {
        capture findfile dash.ado
        if _rc == 0 {
            local _ado `"`r(fn)'"'
            local _beside = substr(`"`_ado'"', 1, ///
                strlen(`"`_ado'"') - strlen("dash.ado")) + "dash_render.py"
            capture confirm file `"`_beside'"'
            if _rc == 0 local render_py `"`_beside'"'
        }
    }
    else {
        local render_py `"`r(fn)'"'
    }

    if `"`render_py'"' == "" {
        display as error "  dash_render.py ..... {err}not found{txt}"
        display as error "    dash cannot render without it. Reinstall dash," ///
            " or put its directory on the ado-path."
        local nfail = `nfail' + 1
        return scalar failures = `nfail'
        exit 0
    }
    display as text "  dash_render.py ..... {res}OK{txt}"

    // Ask the renderer whether it can actually read a scheme file.
    //
    // The probe's fallback warning is silenced for the probe ONLY.  This
    // used to call warnings.simplefilter("ignore") and leave it installed,
    // which silenced every warning Python raised for the rest of the Stata
    // session -- so a user who ran dash_setup and then dash saw none of
    // dash's reports: not the empty-layer report, not the by() sub-option
    // report, not the unknown-scheme report.  Measured: two warning lines
    // from one render before, zero after.  The filter list is saved and
    // put back; a `with' block cannot follow `;' on the one line Stata's
    // ado-path loader allows.
    // `render_py' is a file path from `findfile'.  It is handed to Python
    // with sfi.Macro.getLocal, NOT interpolated as `r"`render_py'"': a double
    // quote in the path closed the raw string the same way the version gate's
    // did (measured: a dash_render.py in a directory whose NAME closed the
    // string and called sfi.Macro.setGlobal ran that call).  getLocal passes
    // the true path -- backslashes and all, which is what `r"..."' was for --
    // as a value the interpreter never parses.
    local _sch_ok "0"
    capture python: ///
        import importlib.util as _iu, sfi, warnings; ///
        _sp = _iu.spec_from_file_location("_dash_setup_probe", sfi.Macro.getLocal("render_py")); ///
        _m = _iu.module_from_spec(_sp); ///
        _sp.loader.exec_module(_m); ///
        _dash_setup_filters = warnings.filters[:]; ///
        warnings.simplefilter("ignore"); ///
        sfi.Macro.setLocal("_sch_ok", ///
            "0" if _m.SchemeParser.resolve_or_fallback("s2color", "dash_setup").is_fallback else "1"); ///
        warnings.filters[:] = _dash_setup_filters
    if _rc != 0 | "`_sch_ok'" != "1" {
        display as error "  schemes ............ {err}unreachable{txt}"
        display as error "    dash found its renderer but the renderer could" ///
            " not read a .scheme file,"
        display as error "    so every dashboard would be drawn with built-in" ///
            " defaults. Reinstall dash."
        local nfail = `nfail' + 1
    }
    else {
        display as text "  schemes ............ {res}OK{txt}"
    }

    return scalar failures = `nfail'
end
