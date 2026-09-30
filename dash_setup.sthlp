{smcl}
{* *! version 0.1.0  30sep2026}{...}
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

{pstd}
It takes no arguments and no options; either is r(101).


{marker description}
{title:Description}

{pstd}
{cmd:dash_setup} checks that the software {helpb dash} needs is installed and
reachable from Stata, and installs the parts it can: the Python packages.
Run it once before you first use {cmd:dash}.  Running it
again is safe: it installs only what is missing, and a package that is
present but older than {cmd:dash} needs is reported, not upgraded.

{pstd}
{cmd:dash_setup} works through these steps in order:

{phang2}1.  Python.  Whether Python is linked to Stata is read from the
    setting {cmd:c(python_exec)}; with none, {cmd:dash_setup} stops at once,
    r(198).  The linked interpreter's version is then compared with the
    3.13 minimum, numerically per component, so 3.10 is correctly newer
    than 3.9; a version below 3.13 is reported as such and counted as
    unmet.

{phang2}2.  {cmd:packaging}, which the version comparisons below use, is
    installed with {cmd:pip} if it is missing.  If it cannot be installed,
    versions are compared approximately and the run ends with a warning.

{phang2}3.  The required Python packages.  Each missing one is installed
    with {cmd:pip}, asking for at least its minimum version, and once more
    with {cmd:--user} if that fails; a package that still cannot be
    imported stops the run, r(198).  An installed package below its
    minimum is reported, with the command that upgrades it, and counted as
    unmet.

{phang2}4.  {cmd:dash}'s own files: {cmd:dash_render.py} must be found, and
    the renderer must be able to read a shipped scheme.

{pstd}
The run ends with a summary.  It says {cmd:dash_setup complete} only when
every requirement is met, with the number of warnings if there were any;
otherwise it names what is unmet and exits with r(198), so a do-file that
runs {cmd:dash_setup} stops there.


{marker dependencies}
{title:Dependencies}

{pstd}{ul:Python}

{phang2}Python 3.13 or later must be installed and linked to Stata.
{cmd:dash_setup} does not install Python.  See {helpb python} for
instructions on linking Python.

{pstd}{ul:Python packages (minimum versions)}

{pstd}Three are required.  {cmd:dash}'s renderer imports all three when it
starts, so without any of them {cmd:dash} cannot draw anything at all:

{synoptset 20 tabbed}{...}
{synopt:{opt bokeh}}3.8 or later{p_end}
{synopt:{opt numpy}}2.3 or later{p_end}
{synopt:{opt pandas}}2.3 or later{p_end}
{synoptline}

{pstd}Nothing else is needed.  Earlier versions listed {cmd:scipy} and
{cmd:statsmodels} as optional; no plot type uses either now -- every
statistical layer is computed with {cmd:numpy} -- so {cmd:dash_setup}
neither installs nor checks them, and an installed copy is not used.

{pstd}{cmd:dash_setup} also installs {cmd:packaging}, before the packages
above, because the version comparisons use it.

{pstd}These minimums are the versions {cmd:dash}'s own test suites run
under (Python 3.13.9, bokeh 3.8.0, numpy 2.3.5, pandas 2.3.3 when this was
written); nothing older is tested.  bokeh before 3.6 lacks
{cmd:CustomJSTicker}, which every {cmd:dash} render imports, and
{cmd:pandas} is required by {cmd:dash} itself: bokeh 3.9 no longer
installs it.  A package below its minimum is not upgraded for you;
{cmd:dash_setup} prints the {cmd:pip} command for the Python Stata is
linked to and stops.

{pstd}Missing packages are installed automatically.  If automatic
installation fails (e.g., in a restricted network environment), install
manually -- the command {cmd:dash_setup} prints names the Python Stata is
linked to, {cmd:c(python_exec)}, not necessarily {cmd:sys.executable}
below if you run this outside Stata:

{phang2}{cmd:python: import subprocess, sys}

{phang2}{cmd:python: subprocess.run([sys.executable, "-m", "pip", "install",}
{cmd:"bokeh>=3.8", "numpy>=2.3", "pandas>=2.3"])}

{pstd}{ul:Stata packages}

{phang2}None.  {cmd:dash} writes its data through Stata's Python and no
longer uses {cmd:jsonio}, so {cmd:dash_setup} neither checks nor installs
it.

{pstd}{ul:Bokeh Server / Tornado}

{phang2}The {cmd:dash serve} subcommand and the {cmd:server} option of
{cmd:dash build} use the Bokeh Server, which runs on the Tornado web
framework.  Tornado is installed with Bokeh, which depends on it, so no
separate installation is needed and {cmd:dash_setup} does not check it.
{cmd:dash_setup} reports the installed bokeh version; one below 3.8 is
reported as an unmet requirement -- it is not upgraded for you -- and the
run ends with r(198).


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

{pstd}{ul:Package version below minimum}

{phang2}Upgrade a specific package:

{phang2}{cmd:python: import subprocess, sys}

{phang2}{cmd:python: subprocess.run([sys.executable, "-m", "pip", "install",}
{cmd:"--upgrade", "bokeh"])}


{title:Also see}

{psee}
{helpb dash}, {helpb python}
