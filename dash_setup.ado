*! dash_setup.ado
*! Installs and verifies all dependencies required by the dash command.
*!
*! Dependencies checked:
*!   - Python (via Stata's python query)
*!   - Python packages: bokeh, numpy, scipy, statsmodels, pandas
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
    // 2. Check and install required Python packages
    // ----------------------------------------------------------------
    // Minimum version requirements stored as locals
    local pkg_list   "bokeh numpy scipy statsmodels pandas"
    local min_bokeh       "3.0"
    local min_numpy       "1.23"
    local min_scipy       "1.9"
    local min_statsmodels "0.13"
    local min_pandas      "1.5"

    foreach pkg of local pkg_list {
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
        // patched versions that still work)
        if "`pkgver'" != "unknown" {
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

    // packaging module needed for version comparisons above — install if absent
    capture python: import packaging
    if _rc != 0 {
        python: ///
            import subprocess, sys; ///
            subprocess.run([sys.executable, "-m", "pip", "install", "packaging"], ///
                capture_output=True)
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
