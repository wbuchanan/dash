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
*! Version: 1.0.0  25mar2026

program define dash_setup
    version 16.0

    // ----------------------------------------------------------------
    // 1. Check Python availability
    // ----------------------------------------------------------------
    display as text _newline "{txt}dash_setup: checking dependencies..."
    display as text "{hline 60}"

    capture python query
    if _rc != 0 {
        display as error "Python is not available to Stata."
        display as error "Please install Python 3.8+ and link it to Stata:"
        display as error "  help python"
        exit 198
    }

    // Retrieve Python version string for display
    python: import sys; from sfi import Macro; Macro.setLocal("pyver", sys.version.split()[0])
    display as text "  Python ............. {res}OK{txt} (version `pyver')"

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
        python: ///
            import importlib.metadata, sfi; ///
            try: ///
                v = importlib.metadata.version("`pkg'"); ///
                sfi.Macro.setLocal("pkgver", v) ///
            except Exception: ///
                sfi.Macro.setLocal("pkgver", "unknown")

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
