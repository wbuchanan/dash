{smcl}
{* *! version 0.1.0  13nov2026}{...}
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

{phang2}1.  Python.  The Python {cmd:dash_setup} checks is the one Stata
    runs: the one {cmd:python set exec} set ({cmd:c(python_exec)}), or,
    with none set, the one Stata finds by itself the first time Python runs
    (see {helpb python}).  Its version is compared with the 3.11 minimum,
    numerically per component, so 3.10 is correctly newer than 3.9; a
    version below 3.11 is reported as such and counted as unmet.  Python is
    started to read its version; a first start that fails is tried once
    more, and a Python that still cannot be started is reported with
    Stata's own message and its path, and, on a Mac, a reminder that Stata
    and Python must be built for the same processor (both arm64 or both
    x86_64), r(198).

{phang2}2.  {cmd:packaging}, which the version comparisons below use, is
    installed with {cmd:pip} if it is missing.  If it cannot be installed,
    versions are compared approximately and the run ends with a warning.

{phang2}3.  The required Python packages.  Each missing one is installed
    with {cmd:pip} from {cmd:dash_requirements.txt}, at the version and
    hash it pins (see {help dash_setup##lock:The hash-pinned lock}),
    which is at least its minimum version.  If that fails
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

{marker lock}{...}
{pstd}
{ul:The hash-pinned lock.}  Every install {cmd:dash_setup} runs, the
{cmd:venv()} one included, is {cmd:pip install --require-hashes -r} over
lines of {cmd:dash_requirements.txt}, shipped beside {cmd:dash_setup.ado}:
each package {cmd:dash} needs, at the newest version its test suites run
under, and each of their dependencies, pinned with {cmd:==} to one release and to the sha256 hash of every wheel of it, for
Python 3.11, 3.12, 3.13 and 3.14 on five platforms: macOS arm64 and
x86_64, Linux x86_64 and aarch64, and Windows x86_64 (the
{cmd:# pythons:} and {cmd:# platforms:} lines at the top of
{cmd:dash_requirements.txt}).  {cmd:pip} refuses a file whose hash is not
listed, so the index cannot hand {cmd:dash_setup} anything else.  The
lines are the missing package's and those of each dependency that is not
installed: a package already installed is left as it is, and one whose
installed version does not meet a missing package's needs makes {cmd:pip}
stop, naming it, rather than replace it.  On another platform or Python
there is no wheel to match and {cmd:pip} stops; this includes Python 3.15
and later and Windows on ARM64, which the lock does not cover; install by
hand as below.
The lock is written by {cmd:scripts/make_requirements_lock.py} in
{cmd:dash}'s source repository, never by hand; to regenerate it after the
minimums change, or for a release, run
{cmd:python3 scripts/make_requirements_lock.py} there (it reads PyPI, and
installs nothing) and commit {cmd:dash_requirements.txt}.

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
packaging, bokeh, numpy and pandas from the hash-pinned lock (see
{help dash_setup##lock:The hash-pinned lock}) into it; checks their versions, and that {cmd:dash}'s
schemes can be read, inside it; and prints
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
below 3.11, or a reused environment whose Python is.  Missing directories
above {it:path} inside your home directory are created, readable by you
alone.  If a step fails, {cmd:dash_setup} names it and leaves the
environment in place; you may delete it.


{marker dependencies}
{title:Dependencies}

{pstd}{ul:Stata}

{phang2}Stata 19 or later; tested on StataNow 19.5 (MP), macOS arm64.
Measured on MP only: Stata 19.0, Stata/BE and Stata/SE are admitted but
have not been run.
It is run from the console; Windows, Linux, Intel macOS and Stata's
graphical interface have not been run.  {cmd:dash_setup} checks this
before anything else and reports {cmd:Stata .............. OK} with the
release; on an older Stata it stops at once with "dash requires Stata 19 or later; this is Stata
{it:#}", r(9), and checks and installs nothing.

{pstd}{ul:Python}

{phang2}Python 3.11 or later must be installed; Stata either finds it or uses
the one {cmd:python set exec} names.
{cmd:dash_setup} does not install Python.  See {helpb python} for
instructions on linking Python.

{pstd}{ul:Python packages (minimum versions)}

{pstd}Three are required.  {cmd:dash}'s renderer imports all three when it
starts, so without any of them {cmd:dash} cannot draw anything at all:

{synoptset 20 tabbed}{...}
{synopt:{opt bokeh}}3.8 or later, before 3.10{p_end}
{synopt:{opt numpy}}2.3 or later{p_end}
{synopt:{opt pandas}}2.3 or later{p_end}
{synoptline}

{pstd}Nothing else is needed.  Earlier versions listed {cmd:scipy} and
{cmd:statsmodels} as optional; no plot type uses either now -- every
statistical layer is computed with {cmd:numpy} -- so {cmd:dash_setup}
neither installs nor checks them, and an installed copy is not used.

{pstd}{cmd:dash_setup} also installs {cmd:packaging}, before the packages
above, because the version comparisons use it.

{pstd}These minimums are what {cmd:dash}'s own test suites run under:
bokeh 3.8.0, numpy 2.3.5 and pandas 2.3.3 under Python 3.11, 3.12 and 3.13,
and bokeh 3.9, numpy 2.4 and pandas 3.0 under 3.11 and 3.14 (measured
07oct2026); nothing older is tested.  bokeh before 3.6 lacks
{cmd:CustomJSTicker}, which every {cmd:dash} render imports, and
{cmd:pandas} is required by {cmd:dash} itself: bokeh 3.9 no longer
installs it.  A package below its minimum is not upgraded for you;
{cmd:dash_setup} prints the {cmd:pip} command for the Python Stata is
linked to, or on an externally managed Python the way to set up a private
environment, and stops.

{pstd}{ul:The verified range of bokeh.}  {cmd:dash} was verified on bokeh
3.8 and 3.9: its test suites, and a browser check that text from your data
-- a variable label in an axis title, a legend or a tooltip -- is drawn as
text.  A patch release of either is covered.  {cmd:dash_setup} installs
{cmd:bokeh>=3.8,<3.10}.  A bokeh at or above 3.10 that you already have is
reported as outside the verified range, a warning, and is never changed:
something else in that Python may need it.  On an externally managed
Python the way to set up a private environment is printed instead of a
{cmd:pip} line.

{pstd}{ul:numpy's and pandas' ceilings.}  {cmd:dash_setup} installs
{cmd:numpy>=2.3,<2.5} and {cmd:pandas>=2.3,<3.1}: each ceiling is the minor
after the newest version {cmd:dash}'s test suites run under (numpy 2.4.3
and pandas 3.0.1), and the hash-pinned lock pins those versions, with
bokeh 3.9.0.  A numpy or pandas at or above its ceiling that you already
have is left as it is and not reported; only bokeh's ceiling is reported.

{pstd}Missing packages are installed automatically.  If automatic
installation fails (e.g., in a restricted network environment), install
manually.  The command {cmd:dash_setup} prints names the Python Stata
runs ({cmd:c(python_exec)}, or the one Stata found), quoted for your system; in a terminal it
reads like this, with that path in place of {it:/path/to/python3}:

{phang2}{cmd:"/path/to/python3" -m pip install "bokeh>=3.8,<3.10" "numpy>=2.3,<2.5" "pandas>=2.3,<3.1"}

{pstd}That line installs by version, not by hash.  For the hash-checked
install {cmd:dash_setup} runs, name the lock instead (it installs every
package in it, replacing any installed at another version):

{phang2}{cmd:"/path/to/python3" -m pip install --only-binary=:all: --require-hashes -r "/path/to/dash_requirements.txt"}

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
run ends with r(198); one at or above 3.10 is reported as outside the
verified range, a warning, and left as it is.


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

{pstd}
On a Python below the minimum, a private environment made from it would be
below the minimum too, so {cmd:dash_setup} does not suggest one: link Stata
to Python 3.11 or later instead.


{marker troubleshooting}
{title:Troubleshooting}

{pstd}{ul:Python not found}

{phang2}If Stata cannot find Python, set the path manually:{p_end}

{phang2}{cmd:python set exec "/path/to/python3", permanently}

{pstd}See {helpb python} for full instructions.

{pstd}{ul:Python could not be started}

{phang2}A Python Stata cannot start is reported as
"Python ............. could not be started", with its path.  On a Mac with
Apple Silicon an arm64 Stata cannot start an x86_64 Python, nor the
reverse: link a Python built for the same processor ({helpb python}), then
run {cmd:dash_setup} again.

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

{phang2}{cmd:"/path/to/python3" -m pip install --index-url https://your.mirror/simple "bokeh>=3.8,<3.10"}

{pstd}{ul:Package version below minimum}

{phang2}Upgrade a specific package, unless the Python is externally managed (see above):

{phang2}{cmd:"/path/to/python3" -m pip install --upgrade "bokeh>=3.8,<3.10"}


{title:Also see}

{psee}
{helpb dash}, {helpb python}
