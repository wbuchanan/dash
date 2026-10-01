{smcl}
{* *! version 0.1.0  30sep2026}{...}
{viewerjumpto "Syntax"      "dash_setup##syntax"}{...}
{viewerjumpto "Description" "dash_setup##description"}{...}
{viewerjumpto "Options" "dash_setup##options"}{...}
{viewerjumpto "Dependencies" "dash_setup##dependencies"}{...}
{viewerjumpto "Externally managed Pythons" "dash_setup##pep668"}{...}
{viewerjumpto "Troubleshooting" "dash_setup##troubleshooting"}{...}
{vieweralsosee "dash" "help dash"}{...}

{title:Title}

{phang}
{cmd:dash_setup} {hline 2} Install and verify dependencies for the {cmd:dash} command


{marker syntax}
{title:Syntax}

{p 8 17 2}
{cmd:dash_setup} [{cmd:,} {opt venv(path)}]

{pstd}
An option other than {opt venv()} is r(198), and an argument is r(101).
{cmd:venv()} with nothing in it is the same as no option.


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
    with {cmd:pip}, asking for at least its minimum version.  If that fails
    for any reason but the two below, it is tried once more with
    {cmd:--user}, except in a virtual environment or where the user site is
    disabled, and a package installed there is found in the same run.  A
    package that still cannot be imported stops the run, r(198).  An
    installed package below its minimum is reported and counted as unmet,
    with the command that upgrades it or, on an externally managed Python,
    the way to set up a private environment instead.

{phang2}4.  {cmd:dash}'s own files: {cmd:dash_render.py} must be found, and
    the renderer must be able to read a shipped scheme.

{pstd}
Before it runs {cmd:pip} for the first time, {cmd:dash_setup} inspects the
linked Python once, in a separate process: whether it is externally
managed, whether it has {cmd:pip}, and whether it is a virtual environment.
On an externally managed Python, or one without {cmd:pip}, no {cmd:pip}
command is run at all; see
{help dash_setup##pep668:Externally managed Pythons} and
{help dash_setup##troubleshooting:No pip}.

{pstd}
{cmd:pip} is always run as {cmd:c(python_exec)} {cmd:-m pip}, never as a
bare {cmd:python} or {cmd:pip}; from a new private directory, not Stata's
working directory; without Stata's {cmd:PYTHONPATH}; in Python's safe-path
mode (3.11 and later); from wheels only, so no package's build script runs;
without prompting; and with a time limit of 30 minutes per command.  Your
own {cmd:pip} settings -- an index, a proxy -- still apply.

{pstd}
The run ends with a summary.  It says {cmd:dash_setup complete} only when
every requirement is met, with the number of warnings if there were any;
otherwise it names what is unmet and exits with r(198), so a do-file that
runs {cmd:dash_setup} stops there.


{marker options}
{title:Options}

{phang}
{opt venv(path)} sets up a Python virtual environment at {it:path} holding
the packages {cmd:dash} needs, for a Python that refuses {cmd:pip}
installs.  {it:path} may be relative to the working directory and may start
with {cmd:~}.  {cmd:dash_setup} creates the environment with the linked
Python's {cmd:venv} module, or reuses one already at {it:path}; installs
packaging, bokeh, numpy and pandas at their minimums into it; checks their
versions, and that {cmd:dash}'s schemes can be read, inside it; and prints
the command that links Stata to it, such as

{phang2}{cmd:python set exec "/path/to/venv/bin/python", permanently}

{pmore}
On Windows the interpreter is {it:path}{cmd:\Scripts\python.exe}.  Stata
reads this setting only when it first starts Python, so restart Stata and
type the line before anything else uses Python -- otherwise it is r(7101),
which a {cmd:profile.do} that runs Python also causes -- then run
{cmd:dash_setup} again.  {cmd:dash_setup} never changes the setting itself.

{pmore}
A {it:path} that exists must be an empty directory or a virtual environment,
owned by you and writable by no one else.  A {it:path} that is a symbolic
link, or that holds a double quote, a backtick, a dollar sign or a control
character, is refused before anything runs, r(198); so is a linked Python
below 3.13, or a reused environment whose Python is.  Missing directories
above {it:path} inside your home directory are created, readable by you
alone.  If a step fails, {cmd:dash_setup} names it and leaves the
environment in place; you may delete it.


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
linked to, or on an externally managed Python the way to set up a private
environment, and stops.

{pstd}Missing packages are installed automatically.  If automatic
installation fails (e.g., in a restricted network environment), install
manually.  The command {cmd:dash_setup} prints names the Python Stata is
linked to, {cmd:c(python_exec)}, quoted for your system; in a terminal it
reads like this, with that path in place of {it:/path/to/python3}:

{phang2}{cmd:"/path/to/python3" -m pip install "bokeh>=3.8" "numpy>=2.3" "pandas>=2.3"}

{pstd}The double quotes matter: without them a shell reads {cmd:>} as a
redirection, installs bokeh unpinned and writes a file named {cmd:=3.8}.
The line runs as written in a macOS or Linux shell and in Windows Command
Prompt; in PowerShell, put {cmd:&} and a space before it.

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


{marker pep668}
{title:Externally managed Pythons}

{pstd}
Some Pythons are marked as managed by the operating system -- Homebrew's,
and the system Python of Debian 12, Ubuntu 23.04, Arch Linux and later
releases -- under PEP 668: a file named {cmd:EXTERNALLY-MANAGED} beside the
standard library.  They refuse {cmd:pip} installs, with or without
{cmd:--user}.  On such a Python {cmd:dash_setup} runs no {cmd:pip} command:
it says why, names the Python, and ends with r(198) when a required
package is missing or below its minimum (a missing {cmd:packaging} alone is
a warning).  It never uses {cmd:--break-system-packages} or {cmd:sudo}, and
a {cmd:pip} setting that turns that protection off is overridden.  Set up a
private environment instead, which leaves the managed Python as it is:

{phang2}{cmd:dash_setup, venv("~/.dash/venv")}

{pstd}
then restart Stata, type the {cmd:python set exec} line that command
prints, and run {cmd:dash_setup} again.  On Windows, {cmd:dash_setup}
suggests {cmd:%LOCALAPPDATA%\dash\venv}.


{marker troubleshooting}
{title:Troubleshooting}

{pstd}{ul:Python not found}

{phang2}If Stata cannot find Python, set the path manually:{p_end}

{phang2}{cmd:python set exec "/path/to/python3", permanently}

{pstd}See {helpb python} for full instructions.

{pstd}{ul:No pip}

{phang2}A Python without {cmd:pip} is not asked to run it.  Where the
Python has its standard {cmd:ensurepip} module, {cmd:dash_setup} prints the
command that installs {cmd:pip}:

{phang2}{cmd:"/path/to/python3" -m ensurepip --upgrade}

{phang2}Debian and Ubuntu remove {cmd:ensurepip}; there, install the
{cmd:python3-pip} and {cmd:python3-venv} packages with the system's
package manager, or use {opt venv()}.

{pstd}{ul:pip install fails}

{phang2}In restricted environments (no internet, corporate proxy), install
packages using your organization's package mirror or a pre-downloaded wheel:

{phang2}{cmd:"/path/to/python3" -m pip install --index-url https://your.mirror/simple "bokeh>=3.8"}

{pstd}{ul:Package version below minimum}

{phang2}Upgrade a specific package, unless the Python is externally managed (see above):

{phang2}{cmd:"/path/to/python3" -m pip install --upgrade "bokeh>=3.8"}


{title:Also see}

{psee}
{helpb dash}, {helpb python}
