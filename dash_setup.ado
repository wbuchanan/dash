*! dash_setup.ado
*! Installs and verifies all dependencies required by the dash command.
*!
*! Dependencies checked:
*!   - Python (via Stata's python query)
*!   - Python packages: bokeh, numpy, pandas (required);
*!                      scipy, statsmodels (optional, per-plot-type)
*!   - Stata package: jsonio (auto-installed from SSC if missing)
*!
*! Usage: dash_setup
*!
*! Author:  (see dash.sthlp)
*! Version: 2.0  27mar2026

program define dash_setup
    version 16.0

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

    capture python query
    if _rc != 0 {
        display as error "Python is not available to Stata."
        display as error "Please install Python 3.8+ and link it to Stata:"
        display as error "  help python"
        exit 198
    }

    // Retrieve Python version string and compare it to the minimum.
    //
    // `python query' succeeds for ANY linked Python, 3.6 included, and this
    // step used to read the version only to print it.  dash_setup.sthlp says
    // this step verifies Python 3.8+, so it now does: a user on 3.7 was told
    // "OK (version 3.7.9)" and sent on to fail later inside bokeh, with a
    // message about neither Python nor dash.
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
        python: ///
            import subprocess, sys; ///
            subprocess.run([sys.executable, "-m", "pip", "install", "packaging"], ///
                capture_output=True)
        // Mark whether packaging is now available
        capture python: import packaging
        if _rc != 0 {
            display as text "  packaging .......... {err}could not install{txt} — " ///
                "version comparison will be skipped"
            local pkg_has_packaging 0
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
    // Only bokeh, numpy and pandas are genuinely required — dash_render.py
    // imports them at module scope, so without them nothing renders at all.
    // scipy and statsmodels are OPTIONAL: they are imported lazily, inside the
    // mapping method for one plot type each, and a missing one degrades that
    // layer to an empty glyph with a warning rather than aborting the render.
    //   scipy       -> lfitci, qfitci, kdensity, mspline
    //   statsmodels -> lowess only
    // Declaring them mandatory (and exiting 198 when pip fails) previously
    // blocked setup entirely for users who need none of those plot types.
    local pkg_required "bokeh numpy pandas"
    local pkg_optional "scipy statsmodels"
    local pkg_list   "`pkg_required' `pkg_optional'"
    local min_bokeh       "3.0"
    local min_numpy       "1.23"
    local min_scipy       "1.9"
    local min_statsmodels "0.13"
    local min_pandas      "1.5"
    local feat_scipy       "lfitci, qfitci, kdensity and mspline"
    local feat_statsmodels "lowess"

    foreach pkg of local pkg_list {
        local pkg_is_optional : list pkg in pkg_optional
        // Try importing the package; if it fails, pip-install it
        capture python: import `pkg'
        if _rc != 0 {
            display as text "  `pkg' ............. {res}missing{txt} — installing via pip..."
            python: ///
                import subprocess, sys; ///
                r = subprocess.run( ///
                    [sys.executable, "-m", "pip", "install", "`pkg'"], ///
                    capture_output=True, text=True ///
                ); ///
                print(r.stdout[-500:] if r.stdout else ""); ///
                print(r.stderr[-200:] if r.stderr else "")
            // Re-check after install
            capture python: import `pkg'
            if _rc != 0 {
                if `pkg_is_optional' {
                    // Optional: report the lost plot types and carry on.
                    display as text "  `pkg' ............. {err}unavailable{txt}" ///
                        " — `feat_`pkg'' will render empty."
                    display as text "      To enable them later:" ///
                        " python -m pip install `pkg'"
                    continue
                }
                display as error "  Failed to install `pkg'. Please install manually:"
                display as error "    python -m pip install `pkg'"
                exit 198
            }
        }

        // Retrieve installed version and compare to minimum
        local minver "`min_`pkg''"
        local pkgver ""
        _dash_pkg_version "`pkg'" pkgver

        // Version gate: warn if below minimum (non-fatal — user may have
        // patched versions that still work).  Only run when packaging is
        // available (guaranteed by the guard above, but check the flag as
        // a defence-in-depth measure).
        if "`pkgver'" != "unknown" & `pkg_has_packaging' {
            python: ///
                from packaging.version import Version; ///
                import sfi; ///
                ok = Version("`pkgver'") >= Version("`minver'"); ///
                sfi.Macro.setLocal("ver_ok", "1" if ok else "0")
            if "`ver_ok'" == "0" {
                display as text "  `pkg' ............. {res}`pkgver'{txt}" ///
                    " {err}(below minimum `minver'){txt}"
            }
            else {
                display as text "  `pkg' ............. {res}OK{txt}" ///
                    " (version `pkgver')"
            }
        }
        else {
            display as text "  `pkg' ............. {res}OK{txt} (version unknown)"
        }
    }

    // ----------------------------------------------------------------
    // 3. Check and install jsonio
    // ----------------------------------------------------------------
    capture which jsonio
    if _rc != 0 {
        display as text "  jsonio ............. {res}missing{txt} — installing from SSC..."
        capture ssc install jsonio, replace
        if _rc != 0 {
            display as error "  Failed to install jsonio from SSC."
            display as error "  Ensure you have an internet connection and try:"
            display as error "    ssc install jsonio"
            exit 198
        }
        capture which jsonio
        if _rc != 0 {
            display as error "  jsonio installed but not found on adopath. Restart Stata."
            exit 198
        }
    }
    display as text "  jsonio ............. {res}OK{txt}"

    // ----------------------------------------------------------------
    // 4. Summary
    // ----------------------------------------------------------------
    display as text "{hline 60}"
    display as text "{res}dash_setup complete.{txt} All dependencies are satisfied."
    display as text "You can now use {cmd:dash} to create interactive dashboards."
    display as text "Type {cmd:help dash} to get started."

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
    return local pymin "3.8"
end

program define _dash_pyver_ok, rclass
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

    forvalues i = 1/`n' {
        local g : word `i' of `gparts'
        local w : word `i' of `wparts'
        if "`g'" == "" local g "0"
        if "`w'" == "" local w "0"

        // A component may carry a suffix -- "0rc1" -- so take its leading
        // digits and ignore the rest.
        if !regexm("`g'", "^([0-9]+)") {
            return scalar ok = -1
            exit
        }
        local gnum = real(regexs(1))
        if !regexm("`w'", "^([0-9]+)") {
            return scalar ok = -1
            exit
        }
        local wnum = real(regexs(1))

        if `gnum' > `wnum' {
            return scalar ok = 1
            exit
        }
        if `gnum' < `wnum' {
            return scalar ok = 0
            exit
        }
    }
    return scalar ok = 1
end

program define _dash_pkg_version
    version 16.0
    args pkg outmac

    // Reject anything that is not a plain package name before it reaches
    // Python, so the name cannot carry code into the expression below.
    if !regexm("`pkg'", "^[A-Za-z0-9._-]+$") {
        c_local `outmac' "unknown"
        exit 0
    }

    local _pv "unknown"
    capture python: import importlib.metadata as _im, sfi; sfi.Macro.setLocal("_pv", next((d.version for d in _im.distributions() if (d.metadata["Name"] or "").lower() == "`pkg'".lower()), "unknown"))
    if _rc != 0 local _pv "unknown"
    if "`_pv'" == "" local _pv "unknown"
    c_local `outmac' "`_pv'"
end
