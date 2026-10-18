*! dash_setup.ado
*! Installs and verifies all dependencies required by the dash command.
*!
*! Dependencies checked:
*!   - Python (via c(python_exec); its version, read from sys.version,
*!     is checked against the minimum)
*!   - Python packages: bokeh, numpy, pandas (all required; no plot type
*!                      needs scipy or statsmodels, see section 3)
*!   - dash's own files: dash_render.py, dash_setup_lib.py (which runs
*!     every pip and venv step; WP-29 P0.19) and the shipped schemes
*!   (No Stata package: dash writes its data from Python and has not used
*!   jsonio since 24sep2026, so it neither checks nor installs it.)
*!
*! Usage: dash_setup [, venv(path)]
*!
*! Author:  (see dash.sthlp)
*! Version: 0.1.0  18oct2026

program define dash_setup, rclass
    // WP-30 P1.35: the Stata floor first, before `version', so an older
    // Stata is refused in dash's words and nothing is checked or installed.
    _dash_setup_stata
    version 19
    // dash_setup.sthlp's Syntax section was the bare command, and there was
    // no `syntax' line at all -- so `dash_setup, garbage(1)' ran the whole
    // setup and ignored the option in silence.  It now takes venv(path)
    // (WP-29 P0.19), so another option is r(198) and an argument r(101).
    syntax [, VENV(string)]

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
    // WP-31 I3: what this run pip-installed, named in a failed summary
    // with the pip uninstall line that removes it.
    local installed_now ""

    // Minimum version requirements stored as locals, here so that venv()
    // can install them too.
    //
    // The package minimums are the stata pins of test/conftest.py
    // (bokeh 3.8.0, numpy 2.3.5, pandas 2.3.3, test/requirements-stata.txt);
    // both test suites, with both pin sets, pass under Python 3.11 and
    // above (WP-30 P1.33, the floor matrix of scripts/floor_matrix.sh).  Every
    // render imports CustomJSTicker, present only from bokeh 3.6.0, so an
    // installed bokeh 3.0-3.5 used to pass this check and then fail every
    // dash command with r(7102); pandas is declared here because bokeh
    // 3.9 no longer installs it as a dependency.
    //
    // bokeh has a ceiling too (WP-30 P1.30, M9): max_bokeh is exclusive,
    // the first minor dash was not verified on.  dash_render.py's
    // _DASH_BOKEH_CEIL holds the same.  It reaches pip only where dash
    // installs bokeh; a bokeh at or above it is reported, never changed.
    local min_bokeh       "3.8"
    local max_bokeh       "3.10"
    local min_numpy       "2.3"
    local min_pandas      "2.3"

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
    display as text "  Stata .............. {res}OK{txt} (version `c(stata_version)')"

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
            items(`"`fail_items'"') warnitems(`"`warn_items'"') ///
                installed(`"`installed_now'"')
        exit 198
    }

    // Retrieve Python version string and compare it to the minimum.
    //
    // Any linked Python answers, and this step used to read the version
    // only to print it.  dash_setup.sthlp says this step verifies the
    // declared minimum, so it now does: a user on a too-old Python was
    // told "OK (version ...)" and sent on to fail later inside bokeh, with
    // a message about neither Python nor dash.
    _dash_setup_pystart
    local pyver `"`r(pyver)'"'
    if `"`pyver'"' == "" {
        display as error "  Python ............. could not be started:"
        mata: display("    " + c("python_exec"), 1)
        if strpos(c(machine_type), "Mac") {
            mata: display("    Stata reports this computer as " + c("machine_type") + ".", 1)
            display as error "    On a Mac, Stata and Python must be built for the same processor:"
            display as error "    both arm64 (Apple Silicon) or both x86_64 (Intel)."
        }
        display as error "    Link Stata to a Python that starts here: {help python}"
        local n_fail = `n_fail' + 1
        local fail_items `"`fail_items' Python (could not be started)"'
        _dash_setup_summary , failures(`n_fail') warnings(`n_warn') ///
            items(`"`fail_items'"') warnitems(`"`warn_items'"') ///
                installed(`"`installed_now'"')
        exit 198
    }
    _dash_pyver_ok "`pyver'" "`c_pymin'"
    local pyok = r(ok)
    if `pyok' == 1 {
        display as text "  Python ............. {res}OK{txt} (version `pyver')"
    }
    else if `pyok' == 0 {
        display as error "  Python ............. version `pyver' is below the minimum `c_pymin'."
        display as error "    dash and the packages it needs are not tested below Python `c_pymin'."
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

    // WP-29 P0.19.  What the linked Python is, asked once, in a child
    // process (dash_setup_lib.py), before the first pip command: on an
    // externally managed (PEP 668) Python, or one without pip, no pip
    // command runs at all.  Until then it is treated as an ordinary
    // Python; a detection that fails leaves it so.
    local det_done 0
    local det_managed 0
    local det_pip 1
    local det_ensurepip 1
    local det_user 1
    local det_version "`pyver'"
    local hint_cmd ""
    local guide_shown 0

    // ----------------------------------------------------------------
    // venv(path): a private environment for a Python that refuses pip
    // installs (WP-29 P0.19).  Everything is decided before a process
    // starts: a linked Python below the minimum, then the path.
    // ----------------------------------------------------------------
    if `"`venv'"' != "" {
        if `pyok' == 0 {
            display as error "  venv() ............ not started: Python `pyver' is below `c_pymin'."
            local n_fail = `n_fail' + 1
            local fail_items `"`fail_items' venv() (Python `pyver' needs `c_pymin')"'
            _dash_setup_summary , failures(`n_fail') warnings(`n_warn') ///
                items(`"`fail_items'"') warnitems(`"`warn_items'"') ///
                installed(`"`installed_now'"')
        }
        _dash_setup_lib
        if r(ok) != 1 {
            local n_fail = `n_fail' + 1
            local fail_items `"`fail_items' dash's own files (dash_setup_lib.py)"'
            _dash_setup_summary , failures(`n_fail') warnings(`n_warn') ///
                items(`"`fail_items'"') warnitems(`"`warn_items'"') ///
                installed(`"`installed_now'"')
        }
        // The path is read by the helper with getLocal and held there for
        // _dash_setup_venv: it never passes through Stata's parser again.
        local venv_ok "0"
        python: import sys; sys.modules["_dash_setup_lib"].stata_venv_check()
        if "`venv_ok'" != "1" {
            local n_fail = `n_fail' + 1
            local fail_items `"`fail_items' venv() (path refused)"'
            _dash_setup_summary , failures(`n_fail') warnings(`n_warn') ///
                items(`"`fail_items'"') warnitems(`"`warn_items'"') ///
                installed(`"`installed_now'"')
        }
        _dash_setup_venv "`c_pymin'" "`min_bokeh'" "`min_numpy'" "`min_pandas'" "`max_bokeh'"
        local v_step "`r(step)'"
        local v_linked "`r(linked)'"
        local v_py `"`r(venv_python)'"'
        local v_base `"`r(python)'"'
        local hint_cmd `"`r(link_cmd)'"'
        return local python `"`v_base'"'
        return local hint_cmd `"`hint_cmd'"'
        if "`v_step'" != "" {
            local n_fail = `n_fail' + 1
            local fail_items `"`fail_items' venv() (`v_step' failed)"'
            _dash_setup_summary , failures(`n_fail') warnings(`n_warn') ///
                items(`"`fail_items'"') warnitems(`"`warn_items'"') ///
                installed(`"`installed_now'"')
        }
        return local venv_python `"`v_py'"'
        return local venv_linked "`v_linked'"
        if "`v_linked'" != "1" {
            _dash_setup_summary , failures(`n_fail') warnings(`n_warn') ///
                items(`"`fail_items'"') warnitems(`"`warn_items'"') ///
                installed(`"`installed_now'"') venvready
            exit
        }
        python: import importlib; importlib.invalidate_caches()
    }

    // Is anything missing?  Only then is the linked Python inspected
    // before step 2 (a run with everything present starts no process).
    local _need 0
    foreach m in packaging bokeh numpy pandas {
        python: import sys, os; _dash_sp = list(sys.path); sys.path[:] = [p for p in sys.path if p not in ("", os.getcwd())]
        capture python: import `m'
        local _imp_rc = _rc
        python: import sys; sys.path[:] = _dash_sp
        if `_imp_rc' != 0 local _need 1
    }
    if `_need' {
        // -- ensure detection (also before the below verdict) --
        if `det_done' == 0 {
            _dash_setup_detect
            local d_lib "`r(lib)'"
            local d_ok "`r(ok)'"
            local d_py `"`r(python)'"'
            local d_managed "`r(managed)'"
            local d_pip "`r(pip)'"
            local d_ensurepip "`r(ensurepip)'"
            local d_user "`r(user)'"
            local d_version "`r(version)'"
            if "`d_lib'" != "1" {
                local n_fail = `n_fail' + 1
                local fail_items `"`fail_items' dash's own files (dash_setup_lib.py)"'
                _dash_setup_summary , failures(`n_fail') warnings(`n_warn') ///
                    items(`"`fail_items'"') warnitems(`"`warn_items'"') ///
                installed(`"`installed_now'"')
            }
            local det_done 1
            return local python `"`d_py'"'
            if "`d_ok'" == "1" {
                local det_managed "`d_managed'"
                local det_pip "`d_pip'"
                local det_ensurepip "`d_ensurepip'"
                local det_user "`d_user'"
                local det_version "`d_version'"
                return local externally_managed "`det_managed'"
            }
        }
    }

    // ----------------------------------------------------------------
    // 2. Ensure `packaging` is available before version comparisons
    // ----------------------------------------------------------------
    // packaging is used inside the per-package version-gate loop; install
    // it FIRST so the loop never hits ModuleNotFoundError mid-run.
    python: import sys, os; _dash_sp = list(sys.path); sys.path[:] = [p for p in sys.path if p not in ("", os.getcwd())]
    capture python: import packaging
    local _imp_rc = _rc
    python: import sys; sys.path[:] = _dash_sp
    if `_imp_rc' != 0 {
        if "`det_managed'" == "1" {
            display as text "  packaging .......... {err}not installed{txt} — this Python is externally managed"
            if `guide_shown' == 0 {
                _dash_setup_guide managed "`det_ensurepip'" "`det_managed'" "`pyok\'" "`c_pymin\'"
                local hint_cmd `"`r(cmd)'"'
                return local hint_cmd `"`hint_cmd'"'
                local guide_shown 1
            }
            local pkg_has_packaging 0
            local n_warn = `n_warn' + 1
            local warn_items `"`warn_items' packaging (version checks approximate)"'
        }
        else if "`det_pip'" == "0" {
            display as text "  packaging .......... {err}not installed{txt} — this Python has no pip"
            _dash_setup_guide nopip "`det_ensurepip'" "`det_managed'" "`pyok\'" "`c_pymin\'"
            local hint_cmd `"`r(cmd)'"'
            return local hint_cmd `"`hint_cmd'"'
            local guide_shown 1
            local pkg_has_packaging 0
            local n_warn = `n_warn' + 1
            local warn_items `"`warn_items' packaging (version checks approximate)"'
        }
        else {
            display as text "  packaging .......... {res}missing{txt} — installing via pip..."
            // pip runs through dash_setup_lib.py (the linked interpreter, a
            // private directory, -P, no inherited PYTHONPATH), and its
            // output is shown: a failure here used to give no reason.  No
            // --user retry for packaging.
            _dash_setup_pip "packaging" 0 "`det_version'"
            if "`r(outcome)'" == "ok" local installed_now "`installed_now' packaging"
            python: import importlib; importlib.invalidate_caches()
            // Mark whether packaging is now available
            python: import sys, os; _dash_sp = list(sys.path); sys.path[:] = [p for p in sys.path if p not in ("", os.getcwd())]
            capture python: import packaging
            local _imp_rc = _rc
            python: import sys; sys.path[:] = _dash_sp
            if `_imp_rc' != 0 {
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
    }
    else {
        local pkg_has_packaging 1
    }

    // ----------------------------------------------------------------
    // 3. Check and install required Python packages
    // ----------------------------------------------------------------
    // bokeh, numpy and pandas are required -- dash_render.py imports them
    // at module scope, so without them nothing renders at all -- and they
    // are all dash needs.  scipy and statsmodels were OPTIONAL, one plot
    // type each (scipy for lfitci, qfitci, kdensity and mspline;
    // statsmodels for lowess), until every estimator became numpy code:
    // kdensity in S07, the rest in WP-18, which measured each against
    // Stata's own plotted points.  Nothing imports either any more, so
    // setup neither installs nor checks them.  Their minimums are set at
    // the top of this program.
    local pkg_list "bokeh numpy pandas"

    foreach pkg of local pkg_list {
        // Try importing the package; if it fails, pip-install it
        python: import sys, os; _dash_sp = list(sys.path); sys.path[:] = [p for p in sys.path if p not in ("", os.getcwd())]
        capture python: import `pkg'
        local _imp_rc = _rc
        python: import sys; sys.path[:] = _dash_sp
        if `_imp_rc' != 0 {
            // The minimum reaches pip.  It was declared at the top and only
            // ever used AFTER the install, to grumble at what pip had
            // chosen; the command itself was a bare name, so a fresh
            // install could land below the minimum dash requires and then
            // be reported as being below it.
            local _spec "`pkg'>=`min_`pkg''"
            // WP-30 P1.30: only bokeh has a ceiling.  This runs only when
            // the import failed, so nothing installed is replaced.
            if "`pkg'" == "bokeh" local _spec "`_spec',<`max_bokeh'"
            if "`det_managed'" == "1" | "`det_pip'" == "0" {
                display as text "  `pkg' ............. {err}missing{txt}"
                if `guide_shown' == 0 {
                    if "`det_managed'" == "1" {
                        _dash_setup_guide managed "`det_ensurepip'" "`det_managed'" "`pyok\'" "`c_pymin\'"
                    }
                    else {
                        _dash_setup_guide nopip "`det_ensurepip'" "`det_managed'" "`pyok\'" "`c_pymin\'"
                    }
                    local hint_cmd `"`r(cmd)'"'
                    return local hint_cmd `"`hint_cmd'"'
                    local guide_shown 1
                }
                local n_fail = `n_fail' + 1
                if "`det_managed'" == "1" {
                    local fail_items `"`fail_items' `pkg' (externally managed Python)"'
                }
                else {
                    local fail_items `"`fail_items' `pkg' (no pip)"'
                }
                _dash_setup_summary , failures(`n_fail') warnings(`n_warn') ///
                    items(`"`fail_items'"') warnitems(`"`warn_items'"') ///
                installed(`"`installed_now'"')
            }
            display as text "  `pkg' ............. {res}missing{txt} — installing via pip..."
            // A system Python the user cannot write to is the ordinary
            // reason this fails, and --user is the ordinary answer: tried
            // once by the helper, after an ordinary failure only, and never
            // in a venv, on a managed Python, or where the user site is
            // disabled.  A package --user installed is put on sys.path.
            local _user = ("`det_user'" == "1" & "`det_managed'" != "1")
            _dash_setup_pip "`_spec'" `_user' "`det_version'"
            if "`r(outcome)'" == "ok" local installed_now "`installed_now' `pkg'"
            local _outcome "`r(outcome)'"
            if "`_outcome'" == "externally-managed" & `guide_shown' == 0 {
                _dash_setup_guide managed "`det_ensurepip'" "`det_managed'" "`pyok\'" "`c_pymin\'"
                local hint_cmd `"`r(cmd)'"'
                return local hint_cmd `"`hint_cmd'"'
                local guide_shown 1
            }
            if "`_outcome'" == "no-pip" {
                _dash_setup_guide nopip "`det_ensurepip'" "`det_managed'" "`pyok\'" "`c_pymin\'"
                local hint_cmd `"`r(cmd)'"'
                return local hint_cmd `"`hint_cmd'"'
            }
            python: import importlib; importlib.invalidate_caches()
            // Re-check after install
            python: import sys, os; _dash_sp = list(sys.path); sys.path[:] = [p for p in sys.path if p not in ("", os.getcwd())]
            capture python: import `pkg'
            local _imp_rc = _rc
            python: import sys; sys.path[:] = _dash_sp
            if `_imp_rc' != 0 {
                if inlist("`_outcome'", "externally-managed", "no-pip") {
                    local fail_items `"`fail_items' `pkg' (`_outcome')"'
                }
                else {
                    display as error "  Failed to install `pkg'. Please install manually:"
                    local _maxv ""
                    if "`pkg'" == "bokeh" local _maxv "`max_bokeh'"
                    _dash_pip_command "`pkg'" "`min_`pkg''" manual "`_maxv'"
                    local hint_cmd `"`r(cmd)'"'
                    return local hint_cmd `"`hint_cmd'"'
                    local fail_items `"`fail_items' `pkg' (could not install)"'
                }
                // Still fatal -- nothing renders without bokeh, numpy and
                // pandas -- but routed through the summary so the exit code
                // and the message come from one place.
                local n_fail = `n_fail' + 1
                _dash_setup_summary , failures(`n_fail') warnings(`n_warn') ///
                    items(`"`fail_items'"') warnitems(`"`warn_items'"') ///
                installed(`"`installed_now'"')
            }
        }

        // Retrieve installed version and compare to minimum
        local minver "`min_`pkg''"
        local maxver ""
        if "`pkg'" == "bokeh" local maxver "`max_bokeh'"
        local pkgver ""
        _dash_pkg_version "`pkg'" pkgver

        // Version gate.  The four outcomes used to collapse into two, and
        // the `else' printed "OK (version unknown)" for every package
        // whenever `packaging' was missing -- although _dash_pkg_version had
        // already returned the real version.  A bokeh 2.4 was reported OK.
        _dash_setup_gate "`pkg'" "`pkgver'" "`minver'" `pkg_has_packaging' "`maxver'"
        local verdict "`r(verdict)'"

        if "`verdict'" == "ok" {
            display as text "  `pkg' ............. {res}OK{txt}" ///
                " (version `pkgver')"
        }
        else if "`verdict'" == "below" {
            display as text "  `pkg' ............. {res}`pkgver'{txt}" ///
                " {err}(below minimum `minver'){txt}"
            // -- ensure detection: is this Python managed? --
            if `det_done' == 0 {
                _dash_setup_detect
                local d_lib "`r(lib)'"
                local d_ok "`r(ok)'"
                local d_py `"`r(python)'"'
                local d_managed "`r(managed)'"
                local d_pip "`r(pip)'"
                local d_ensurepip "`r(ensurepip)'"
                local d_user "`r(user)'"
                local d_version "`r(version)'"
                if "`d_lib'" != "1" {
                    local n_fail = `n_fail' + 1
                    local fail_items `"`fail_items' dash's own files (dash_setup_lib.py)"'
                    _dash_setup_summary , failures(`n_fail') warnings(`n_warn') ///
                        items(`"`fail_items'"') warnitems(`"`warn_items'"') ///
                installed(`"`installed_now'"')
                }
                local det_done 1
                return local python `"`d_py'"'
                if "`d_ok'" == "1" {
                    local det_managed "`d_managed'"
                    local det_pip "`d_pip'"
                    local det_ensurepip "`d_ensurepip'"
                    local det_user "`d_user'"
                    local det_version "`d_version'"
                    return local externally_managed "`det_managed'"
                }
            }
            // An upgrade line pip would refuse is not printed on a managed
            // Python (N4): the private-environment guidance is, once.
            if "`det_managed'" == "1" {
                if `guide_shown' == 0 {
                    _dash_setup_guide managed "`det_ensurepip'" "`det_managed'" "`pyok\'" "`c_pymin\'"
                    local hint_cmd `"`r(cmd)'"'
                    return local hint_cmd `"`hint_cmd'"'
                    local guide_shown 1
                }
            }
            else {
                // The Python Stata is linked to (Q27), quoted for the
                // shell; the helper prints "To upgrade: <line>" as plain
                // text.
                _dash_pip_command "`pkg'" "`minver'" upgrade "`maxver'"
                local hint_cmd `"`r(cmd)'"'
                return local hint_cmd `"`hint_cmd'"'
            }
            // Reported as unmet rather than upgraded behind the user's
            // back: this package is already importable, so something else
            // in their environment may depend on the version they have.
            // AC-06.2 accepts either; reporting is the one that cannot
            // break unrelated work.
            local n_fail = `n_fail' + 1
            local fail_items `"`fail_items' `pkg' `pkgver' (needs `minver')"'
        }
        else if "`verdict'" == "above" {
            // WP-30 P1.30 (M9, A105, A107): newer than dash was verified
            // on.  A warning, never an install: something else in this
            // Python may need the bokeh it has.  dash notes it as it draws.
            display as text "  `pkg' ............. {res}`pkgver'{txt}" ///
                " (outside the verified range: `minver' or later, before `maxver')"
            local n_warn = `n_warn' + 1
            local warn_items `"`warn_items' `pkg' `pkgver' (outside the verified range)"'
            if `det_done' == 0 {
                _dash_setup_detect
                local d_lib "`r(lib)'"
                local d_ok "`r(ok)'"
                local d_py `"`r(python)'"'
                local d_managed "`r(managed)'"
                local d_pip "`r(pip)'"
                local d_ensurepip "`r(ensurepip)'"
                local d_user "`r(user)'"
                local d_version "`r(version)'"
                if "`d_lib'" != "1" {
                    local n_fail = `n_fail' + 1
                    local fail_items `"`fail_items' dash's own files (dash_setup_lib.py)"'
                    _dash_setup_summary , failures(`n_fail') warnings(`n_warn') ///
                        items(`"`fail_items'"') warnitems(`"`warn_items'"') ///
                installed(`"`installed_now'"')
                }
                local det_done 1
                return local python `"`d_py'"'
                if "`d_ok'" == "1" {
                    local det_managed "`d_managed'"
                    local det_pip "`d_pip'"
                    local det_ensurepip "`d_ensurepip'"
                    local det_user "`d_user'"
                    local det_version "`d_version'"
                    return local externally_managed "`det_managed'"
                }
            }
            if "`det_managed'" == "1" {
                if `guide_shown' == 0 {
                    _dash_setup_guide managed "`det_ensurepip'" "`det_managed'" "`pyok\'" "`c_pymin\'"
                    local hint_cmd `"`r(cmd)'"'
                    return local hint_cmd `"`hint_cmd'"'
                    local guide_shown 1
                }
            }
            else {
                display as text "      To install a verified one:"
                _dash_pip_command "`pkg'" "`minver'" manual "`maxver'"
                local hint_cmd `"`r(cmd)'"'
                return local hint_cmd `"`hint_cmd'"'
            }
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
    return local hint_cmd `"`hint_cmd'"'
    _dash_setup_summary , failures(`n_fail') warnings(`n_warn') ///
        items(`"`fail_items'"') warnitems(`"`warn_items'"') ///
                installed(`"`installed_now'"')

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

        The value is measured, never assumed (WP-30 P1.33): the lowest
        Python the floor matrix passes (scripts/floor_matrix.sh: both test
        suites with both pin sets, and a Stata session linked to it).
        test/test_version_floor.py pins it to the lowest Python of
        test/conftest.py's baselines.
    */
    return local pymin "3.11"
end

program define _dash_statamin, rclass
    /*
        The oldest Stata release dash runs on, named once.

        returns r(statamin): "19".

        _dash_setup_stata refuses below it.  dash.ado's
        _dash_require_stata holds the same number (a program defined in
        one ado-file cannot be called from another), and
        test/test_version_floor.py pins the two, every program's
        `version' line, dash.pkg and both help files equal.  No `version'
        line: it runs on the Stata it refuses.
    */
    return local statamin "19"
end

program define _dash_setup_stata
    version 13
    _dash_statamin
    local floor "`r(statamin)'"
    local h = c(stata_version)
    local w = real("`floor'")
    if missing(`w') | `h' < `w' {
        local shown : display %9.1f `h'
        local shown `shown'
        display as error "dash requires Stata `floor' or later; this is Stata `shown'"
        exit 9
    }
end

program define _dash_pyver_ok, rclass
    version 19
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
        forvalues -- neither took effect under language level 16, which
        dash_setup declared until WP-30 raised it to 19, and therefore the
        level this ran under in production.  Measured, with the loop body
        tracing itself:
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

/*
   _dash_setup_pystart  — start the linked Python and read its version
   (WP-30 P1.32)

   Returns r(pyver), sys.version's first word, or "" when Python could not
   be started, and r(tries), 1 or 2.  The first python call of a session
   can fail where Python works, so a line that set nothing is run once
   more; the value decides, never the return code.
*/
program define _dash_setup_pystart, rclass
    version 19
    local pyver ""
    capture python: import sys; from sfi import Macro; Macro.setLocal("pyver", sys.version.split()[0])
    local tries 1
    if `"`pyver'"' == "" {
        capture python: import sys; from sfi import Macro; Macro.setLocal("pyver", sys.version.split()[0])
        local tries 2
    }
    return local pyver `"`pyver'"'
    return scalar tries = `tries'
end

// ================================================================
// _dash_pip_command  — the pip install line dash_setup prints (Q27)
//
// The interpreter named is the one Stata is linked to (c(python_exec),
// resolved), never the bare word `python': installing with a different
// interpreter than the one Stata runs against would upgrade the wrong
// Python, and a bare `python' could be Python 2 or an unrelated
// environment.  The line is quoted for the shell by
// dash_setup_lib.stata_shell_line (WP-29 P0.19): printed bare, a shell read
// `bokeh>=3.8' as `bokeh' and a redirection into a file named =3.8; and
// cmd.exe ignores single quotes, so on Windows it is double-quoted.
//
// Syntax:
//   _dash_pip_command pkg minver [how] [maxver]
//   how: "" (print nothing), upgrade ("To upgrade: <line>"), manual
//   maxver: an exclusive ceiling, bokeh's (WP-30 P1.30); "" for none
//   -> r(cmd) the line ("" when the helper is not reachable), r(note) what
//      to add in PowerShell
// ================================================================
program define _dash_pip_command, rclass
    version 19
    args pkg minver how maxver
    _dash_setup_lib
    if r(ok) != 1 {
        return local cmd ""
        exit
    }
    local spec "`pkg'>=`minver'"
    if "`maxver'" != "" local spec "`spec',<`maxver'"
    local pip_cmd ""
    local pip_note ""
    python: import sys; sys.modules["_dash_setup_lib"].stata_shell_line()
    return local cmd `"`pip_cmd'"'
    return local note `"`pip_note'"'
end

program define _dash_pkg_version
    version 19
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
//   _dash_setup_summary , FAILures(int) WARNings(int) [ITEMS(string)
//       VENVready]
// venvready (WP-29 P0.19): dash_setup, venv() built an environment Stata
// is not linked to yet, so dash cannot be used until Stata is restarted
// and linked to it; with no failure that is what the banner says.
// ================================================================
program define _dash_setup_summary
    version 19
    // WP-31 I3: items() the failures, warnitems() the warnings (Unmet
    // named both when a run had both), installed() what this run
    // pip-installed (dash's own package names).
    syntax , FAILures(integer) WARNings(integer) [ITEMS(string) ///
        WARNITems(string) INSTalled(string) VENVready]
    // Unmet: and Warned: print items() as they come (each item starts
    // with its blank); the two new lines trim theirs.
    local warnshow = strtrim(`"`warnitems'"')
    local installed = strtrim(`"`installed'"')

    display as text "{hline 60}"

    if `failures' > 0 {
        display as error "dash_setup did not complete: `failures' unmet " ///
            "requirement(s)."
        if `"`items'"' != "" {
            display as error "  Unmet: `items'"
        }
        if `"`warnshow'"' != "" {
            display as text "  Warnings: `warnshow'"
        }
        if `"`installed'"' != "" {
            display as text "  Installed by this run: `installed'"
            local pkgs `"`installed'"'
            local pip_cmd ""
            capture _dash_setup_lib
            if _rc == 0 & r(ok) == 1 {
                python: import sys; sys.modules["_dash_setup_lib"].stata_undo_line()
            }
        }
        display as error "  dash will not work until these are resolved."
        display as error "  Fix them and run {cmd:dash_setup} again."
        // Non-zero, so a do-file or CI step that runs dash_setup stops here
        // rather than carrying on to use a dash that cannot work.  198 is
        // what the other failing branches of this command already use.
        exit 198
    }

    if "`venvready'" != "" {
        display as text "{res}dash_setup complete{txt} for the environment named above."
        display as text "Restart Stata, link it with the python set exec line above, and run {cmd:dash_setup} again."
        exit
    }

    if `warnings' > 0 {
        // A warning used to be an optional package, and this said the
        // layers needing it would render empty.  No package is optional
        // since WP-18; each item now says what it costs.
        display as text "{res}dash_setup complete{txt}, with `warnings' " ///
            "warning(s)."
        local items `"`items'`warnitems'"'
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
//   above       at or above the optional ceiling (bokeh's max_bokeh,
//               WP-30 P1.30): newer than dash was verified on
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
//   _dash_setup_gate pkg got want has_packaging [ceil]
// ================================================================
program define _dash_setup_gate, rclass
    version 19
    args pkg got want haspkg ceil

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

    // The ceiling (WP-30 P1.30): judged numerically, so 3.10.0rc1 is at
    // or above 3.10, which is what "above" needs.  `got' reaches Python
    // only through _dash_pyver_ok's getLocal, never interpolated.
    if `"`ceil'"' != "" & inlist("`verdict'", "ok", "unverified") {
        _dash_pyver_ok "`got'" "`ceil'"
        if r(ok) == 1 local verdict "above"
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
// findfile would locate PLUS/d/dash-s2color.scheme just as well on an install
// where the renderer could not read a single scheme, so a findfile check
// would have passed on the broken tree it exists to catch.
//
// Returns r(failures), the number of things that are missing.
// ================================================================
program define _dash_setup_check_files, rclass
    version 19

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
    // WP-31 I7: the probe writes no bytecode beside the installed renderer.
    python: import sys, sfi; sfi.Macro.setLocal("_dwb", "1" if sys.dont_write_bytecode else "0"); sys.dont_write_bytecode = True
    python: import sys, os; _dash_sp = list(sys.path); sys.path[:] = [p for p in sys.path if p not in ("", os.getcwd())]
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
    local _sch_rc = _rc
    python: import sys; sys.path[:] = _dash_sp
    python: import sys, sfi; sys.dont_write_bytecode = sfi.Macro.getLocal("_dwb") == "1"
    if `_sch_rc' != 0 | "`_sch_ok'" != "1" {
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


// ================================================================
// _dash_setup_lib  — load dash_setup_lib.py (WP-29 P0.19)
// ================================================================
// dash_setup's pip and venv steps run in dash_setup_lib.py, shipped beside
// dash_render.py.  It is found the way _dash_setup_check_files finds the
// renderer -- beside dash_setup.ado, else findfile (WP-31 I3) -- made absolute, and
// loaded once per path as sys.modules["_dash_setup_lib"], with no bytecode
// written.  findfile searches the working directory first (Stata's own
// rule), so it is the fallback only.
//
// Returns r(ok): 1 loaded, 0 not found or not loadable (each named).
// ================================================================
program define _dash_setup_lib, rclass
    version 19
    local lib ""
    // WP-31 I3: the copy beside dash_setup.ado first -- findfile searches
    // the working directory first, so a dash_setup_lib.py there was the
    // one loaded -- then the ado-path.
    capture findfile dash_setup.ado
    if _rc == 0 {
        local _ado `"`r(fn)'"'
        local _beside = substr(`"`_ado'"', 1, ///
            strlen(`"`_ado'"') - strlen("dash_setup.ado")) + "dash_setup_lib.py"
        capture confirm file `"`_beside'"'
        if _rc == 0 local lib `"`_beside'"'
    }
    if `"`lib'"' == "" {
        capture findfile dash_setup_lib.py
        if _rc == 0 local lib `"`r(fn)'"'
    }
    if `"`lib'"' == "" {
        display as error "  dash_setup_lib.py .. {err}not found{txt}"
        display as error "    dash_setup needs it to run pip. Reinstall dash, or put its directory on the ado-path."
        return scalar ok = 0
        exit
    }
    mata: st_local("lib", pathresolve(pwd(), st_local("lib")))
    python: import sys, sfi; sfi.Macro.setLocal("_dwb", "1" if sys.dont_write_bytecode else "0"); sys.dont_write_bytecode = True
    capture python: import importlib.util as _dsl_iu, sys, sfi; _dsl_p = sfi.Macro.getLocal("lib"); _dsl_m = sys.modules.get("_dash_setup_lib"); _dsl_new = _dsl_m is None or getattr(_dsl_m, "__file__", None) != _dsl_p; _dsl_s = _dsl_iu.spec_from_file_location("_dash_setup_lib", _dsl_p) if _dsl_new else None; _dsl_m = _dsl_iu.module_from_spec(_dsl_s) if _dsl_new else _dsl_m; (_dsl_s.loader.exec_module(_dsl_m) if _dsl_new else None); sys.modules["_dash_setup_lib"] = _dsl_m
    local _lrc = _rc
    python: import sys, sfi; sys.dont_write_bytecode = sfi.Macro.getLocal("_dwb") == "1"
    if `_lrc' != 0 {
        display as error "  dash_setup_lib.py .. {err}could not be loaded{txt}"
        return scalar ok = 0
        exit
    }
    return scalar ok = 1
end


// ================================================================
// _dash_setup_detect  — what the linked Python is (WP-29 P0.19)
// ================================================================
// Inspected in a child process (dash_setup_lib.stata_detect): externally
// managed (PEP 668), with pip, with ensurepip, in a venv, its user site
// usable, its version.  r(lib) is "0" when the helper could not be loaded;
// r(ok) "1" when the child answered.
// ================================================================
program define _dash_setup_detect, rclass
    version 19
    _dash_setup_lib
    if r(ok) != 1 {
        return local lib "0"
        exit
    }
    local det_ok "0"
    python: import sys; sys.modules["_dash_setup_lib"].stata_detect()
    return local lib "1"
    return local ok "`det_ok'"
    return local managed "`det_managed'"
    return local in_venv "`det_in_venv'"
    return local pip "`det_pip'"
    return local ensurepip "`det_ensurepip'"
    return local user "`det_user'"
    return local version "`det_version'"
    return local python `"`det_python'"'
end


// ================================================================
// _dash_setup_pip  — one pip install, through the helper (WP-29 P0.19)
// ================================================================
// Syntax: _dash_setup_pip spec user ver
//   spec  the requirement (a name and minimum from this file's constants)
//   user  1 allows one --user retry after an ordinary failure
//   ver   the linked Python's version (decides -P)
// Returns r(outcome) (ok, externally-managed, no-pip, user-unavailable,
// timeout, missing-interpreter, other) and r(user_tried).
// ================================================================
program define _dash_setup_pip, rclass
    version 19
    args spec user ver
    local pip_outcome "other"
    local pip_user "0"
    python: import sys; sys.modules["_dash_setup_lib"].stata_pip()
    return local outcome "`pip_outcome'"
    return local user_tried "`pip_user'"
end


// ================================================================
// _dash_setup_guide  — the way forward on a managed or pip-less Python
// ================================================================
// Syntax: _dash_setup_guide kind ensurepip managed pyok pymin
//   kind  managed (PEP 668: suggest venv()) or nopip (ensurepip, or the
//         distribution's packages)
//   pyok  dash_setup's verdict on the linked Python: 0 below pymin, the
//         floor.  A private environment made from a Python below the floor
//         is below it too, so then neither kind suggests venv(): the
//         guidance names the floor instead (WP-30 P1.33).
// Printed by the helper as plain text.  Returns r(cmd), the command it
// suggests ("" when it suggests none).  WP-29 P0.19.
// ================================================================
program define _dash_setup_guide, rclass
    version 19
    args kind ensurepip managed pyok pymin
    local guide_cmd ""
    python: import sys; sys.modules["_dash_setup_lib"].stata_guide()
    return local cmd `"`guide_cmd'"'
end


// ================================================================
// _dash_setup_venv  — create or reuse, install into and verify the venv
//                     stata_venv_check held (WP-29 P0.19)
// ================================================================
// Syntax: _dash_setup_venv pymin minb minn minp maxb
// (maxb: bokeh's exclusive ceiling, WP-30 P1.30)
// Returns r(step) ("" on success, else the step that failed: internal,
// create, inspect, python, pip, verify), r(linked) ("1" when Stata is
// already linked to it), r(venv_python), r(link_cmd) (the python set exec
// line) and r(python) (the linked interpreter).
// ================================================================
program define _dash_setup_venv, rclass
    version 19
    args pymin minb minn minp maxb
    local venv_step "internal"
    python: import sys; sys.modules["_dash_setup_lib"].stata_venv()
    return local step "`venv_step'"
    return local linked "`venv_linked'"
    return local venv_python `"`venv_python'"'
    return local link_cmd `"`venv_cmd'"'
    return local python `"`venv_base'"'
end
