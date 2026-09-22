{smcl}
{* *! version 2.0  27mar2026}{...}
{viewerjumpto "Syntax"      "dash_setup##syntax"}{...}
{viewerjumpto "Description" "dash_setup##description"}{...}
{viewerjumpto "Dependencies" "dash_setup##dependencies"}{...}
{viewerjumpto "Troubleshooting" "dash_setup##troubleshooting"}{...}
{vieweralsosee "dash" "help dash"}{...}

{title:Title}

{phang}
{cmd:dash_setup} {hline 2} Install and verify dependencies for the {cmd:dash} command


{marker syntax}
{title:Syntax}

{p 8 17 2}
{cmd:dash_setup}


{marker description}
{title:Description}

{pstd}
{cmd:dash_setup} checks that all software required by {helpb dash} is installed
and accessible to Stata.  It must be run once before using {cmd:dash} for the
first time.  It is safe to run again at any time; it will only install
components that are missing.

{pstd}
{cmd:dash_setup} performs the following checks in order:

{phang2}1.  Verifies that Python is available to Stata via {cmd:python query},
    then compares the linked interpreter's version against the 3.8 minimum
    and reports it.  A version below 3.8 is named as such rather than
    reported as {cmd:OK}: {cmd:python query} succeeds for any linked Python,
    so without the comparison a user on 3.7 was sent on to fail later inside
    {cmd:bokeh}.  The comparison is numeric per component, so 3.10 is
    correctly newer than 3.9.

{phang2}2.  Checks for each required Python package.  Missing packages are
    installed automatically via {cmd:pip}.

{phang2}3.  Checks for {cmd:jsonio}.  If missing, installs it from SSC automatically.

{pstd}
After a successful run, {cmd:dash} is ready to use.


{marker dependencies}
{title:Dependencies}

{pstd}{ul:Python}

{phang2}Python 3.8 or later must be installed and linked to Stata.
See {helpb python} for instructions on linking Python.

{pstd}{ul:Python packages (minimum versions)}

{pstd}Three are required.  Without any of them {cmd:dash} cannot draw
anything at all:

{synoptset 20 tabbed}{...}
{synopt:{opt bokeh}}3.0 or later{p_end}
{synopt:{opt numpy}}1.23 or later{p_end}
{synopt:{opt pandas}}1.5 or later{p_end}
{synoptline}

{pstd}Two are optional.  A missing optional package costs you the layers
that need it and nothing else: the layer is drawn empty and a warning names
the package, so the rest of the dashboard is unaffected and setup does not
stop:

{synoptset 20 tabbed}{...}
{synopt:{opt scipy}}1.9 or later — {cmd:lfitci}, {cmd:qfitci},
    {cmd:kdensity} and {cmd:mspline}{p_end}
{synopt:{opt statsmodels}}0.13 or later — {cmd:lowess}{p_end}
{synoptline}

{pstd}{cmd:dash_setup} also installs {cmd:packaging} before anything else,
because the version comparisons below use it.

{pstd}All packages are installed automatically if missing.  If automatic
installation fails (e.g., in a restricted network environment), install
manually:

{phang2}{cmd:python: import subprocess, sys}

{phang2}{cmd:python: subprocess.run([sys.executable, "-m", "pip", "install",}
{cmd:"bokeh", "numpy", "scipy", "statsmodels", "pandas"])}

{pstd}{ul:Stata package}

{phang2}{cmd:jsonio} — installed automatically from SSC if missing.
See {helpb jsonio} for details on this package.

{pstd}{ul:Bokeh Server / Tornado}

{phang2}The {cmd:dash serve} subcommand and {cmd:dash build, server} option use
the Bokeh Server, which is built on the Tornado web framework.
Tornado is bundled with Bokeh 3.0 and later — no additional installation
is required.  {cmd:dash_setup} reports the installed bokeh version and
warns when it is below 3.0; it does not refuse to continue, because a
patched or pre-release build below the nominal minimum often works.  A
warning there is the signal that Tornado may be absent.


{marker troubleshooting}
{title:Troubleshooting}

{pstd}{ul:Python not found}

{phang2}If Stata cannot find Python, set the path manually:{p_end}

{phang2}{cmd:python set exec "/path/to/python3", permanently}

{pstd}See {helpb python} for full instructions.

{pstd}{ul:pip install fails}

{phang2}In restricted environments (no internet, corporate proxy), install
packages using your organization's package mirror or a pre-downloaded wheel:

{phang2}{cmd:python: import subprocess, sys}

{phang2}{cmd:python: subprocess.run([sys.executable, "-m", "pip", "install",}
{cmd:"--index-url", "https://your.mirror/simple", "bokeh"])}

{pstd}{ul:jsonio not found after installation}

{phang2}If {cmd:jsonio} was just installed but Stata cannot find it,
restart Stata and run {cmd:dash_setup} again.

{pstd}{ul:Package version below minimum}

{phang2}Upgrade a specific package:

{phang2}{cmd:python: import subprocess, sys}

{phang2}{cmd:python: subprocess.run([sys.executable, "-m", "pip", "install",}
{cmd:"--upgrade", "bokeh"])}


{title:Also see}

{psee}
{helpb dash}, {helpb jsonio}, {helpb python}
