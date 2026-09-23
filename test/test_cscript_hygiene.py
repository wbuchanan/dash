"""test_cscript_hygiene.py — the certification suite must actually certify.

Two defects, both of which made the Stata suite report success while testing
far less than it claimed.

**The guard that skipped everything.** Every Python-dependent script decided
whether Python was available with ``capture python: pass``.  Measured: that
returns a nonzero rc inside ``run_all_cscripts.do`` on a machine where the
very same session renders Bokeh output through ``dash build`` seconds later.
Nine of the fourteen scripts -- every end-to-end one -- skipped, and the
runner printed ``ALL TESTS PASSED (5 passed, 9 skipped)``.  The replacement
reads ``c(python_exec)``, which is configuration rather than execution and so
cannot fail for reasons unrelated to Python being configured.

**A line of HTML that ended a Stata string.** ``test_e2e_single.cscript``
read the generated dashboard line by line and tested each with
``strpos(lower("`ln'"), "bokeh")``.  Bokeh's HTML contains ``"`` characters,
which closed the Stata string early; the remainder of the line was then
parsed as code and the script died with ``r(111): Security not found`` --
"Security" being a word from the page.  Under the broken Python guard the
script never ran, so the failure was invisible.

Both checks are mechanical and run in the Python suite, because that is the
suite that runs on every change.
"""
import glob
import os
import re

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_CSCRIPTS = sorted(glob.glob(os.path.join(_HERE, "*.cscript")))
_RUNNER = os.path.join(_HERE, "run_all_cscripts.do")

_REPO = os.path.dirname(_HERE)
#: The shipped ado files. The rule below was written for the certification
#: scripts and enforced only there, so dash.ado and dash_setup.ado sat
#: outside the net that exists to catch exactly their mistake.
_ADOS = [os.path.join(_REPO, n) for n in ("dash.ado", "dash_setup.ado")]


#: Macros that legitimately appear inside a Python string literal on a
#: ``python:`` line, per shipped file, each with the reason it is safe.  Every
#: other in-string macro is a potential injection site and fails the test.
#:
#: The rule exists because ``dash_setup.ado`` interpolated an untrusted
#: distribution version as ``Version("`got'")`` and an untrusted file path as
#: ``r"`render_py'"``; a double quote in either closed the string and ran the
#: rest as code.  The fix reads such values with ``sfi.Macro.getLocal``, which
#: leaves no macro in the source at all -- so the closed sites appear in
#: neither this allowlist nor the files.
_ALLOWED_INLINE_PY_MACROS = {
    "dash.ado": {
        "_py_spec": r"escaped by _dash_json_str (\\ and \") before interpolation",
        "_py_data": "escaped by _dash_json_str before interpolation",
        "_py_output": "escaped by _dash_json_str before interpolation",
        "_py_mode": "escaped by _dash_json_str; only ever 'standalone'/'server'",
        "_py_renderpy": "escaped by _dash_json_str before interpolation",
        "_py_master": "escaped by _dash_json_str before interpolation",
        "_py_serve": "escaped by _dash_json_str before interpolation",
        "_py_render": "escaped by _dash_json_str before interpolation",
        "port_int": "validated ^[0-9]+$ and range 1024-65535 in _dash_serve_spec",
        "timeout": "validated ^[0-9]+$ in _dash_serve_spec",
    },
    "dash_setup.ado": {
        "_spec": "built only from the fixed pkg_list and min_* constants "
                 "in this file (e.g. 'bokeh>=3.0'), never from user or "
                 "package-supplied text",
    },
}


def _python_command_sources(src):
    """``(start_line, python_source)`` for every ``python:`` command.

    Joins ``python: ///`` continuations into one logical line, exactly as
    Stata does, and strips the ``capture``/``quietly``/``noisily`` prefixes so
    what remains is the Python the interpreter receives.  ``_stata_logical_lines``
    and ``_PREFIX`` are defined later in this module and resolved at call time.
    """
    out = []
    for start, code in _stata_logical_lines(src):
        stripped = _PREFIX.sub("", code)
        m = re.match(r"python\s*:\s?(.*)$", stripped)
        if m and m.group(1).strip():
            out.append((start, m.group(1)))
    return out


def _macros_inside_string_literals(py_src):
    """The Stata macros ( `` `name' `` ) that fall inside a Python string
    literal in one line of Python source.

    A minimal string-state scanner: it opens on ``"`` or ``'`` (noting an
    ``r`` prefix so a backslash does not escape inside a raw string) and, while
    open, records any `` `macro' `` token before the matching quote.  A macro
    OUTSIDE every string -- ``import `pkg'``, whose value is a bare identifier
    from a fixed list -- is not an injection into a string literal and is not
    reported.
    """
    found = set()
    i, n = 0, len(py_src)
    in_str, quote, raw = False, "", False
    while i < n:
        c = py_src[i]
        if in_str:
            if not raw and c == "\\":
                i += 2
                continue
            if c == quote:
                in_str, quote, raw = False, "", False
                i += 1
                continue
            if c == "`":
                j = py_src.find("'", i + 1)
                if j != -1:
                    found.add(py_src[i + 1:j])
                    i = j + 1
                    continue
            i += 1
        else:
            if c in "\"'":
                k, pref = i - 1, ""
                while k >= 0 and py_src[k].isalpha():
                    pref = py_src[k].lower() + pref
                    k -= 1
                raw = "r" in pref
                in_str, quote = True, c
            i += 1
    return found


def _name(path):
    return os.path.basename(path)


@pytest.fixture(scope="module", params=_CSCRIPTS, ids=_name)
def cscript(request):
    with open(request.param, encoding="utf-8") as fh:
        return request.param, fh.read()


class TestTheAvailabilityGuardIsReliable:

    def test_no_script_probes_python_by_executing_it(self, cscript):
        path, src = cscript
        code = "\n".join(l.split("//", 1)[0] for l in src.splitlines())
        lines = code.splitlines()
        bad = []
        for i, line in enumerate(lines):
            if "capture python: pass" not in line:
                continue
            # A bare warm-up is fine and is in fact required; what is not
            # fine is deciding anything from its rc.
            # A bare warm-up before a real probe is fine and is in fact
            # required; what is not fine is concluding "Python is missing"
            # from its rc.
            after = "\n".join(lines[i + 1:i + 5])
            if "Python not available" in after:
                bad.append(i + 1)
        assert not bad, (
            f"{_name(path)} lines {bad}: decides whether Python is available "
            f"by running it; measured, that reports a nonzero rc under the "
            f"runner on a machine where Python works, and the script "
            f"silently skips"
        )

    def test_a_probe_that_must_run_python_retries(self, cscript):
        """Checking for a package can only be done by importing it.

        The first python call of a session fails under the runner whatever it
        is, so such a probe must spend that failure on a throwaway call and
        ask its real question afterwards -- otherwise a machine with bokeh
        installed reports bokeh missing and the script skips.
        """
        path, src = cscript
        code = [l.split("//", 1)[0] for l in src.splitlines()]
        probes = [i for i, l in enumerate(code)
                  if "capture python:" in l and "import" in l]
        if not probes:
            pytest.skip("this script runs no import probe")
        for i in probes:
            window = "\n".join(code[max(0, i - 3):i + 3])
            assert window.count("capture python:") >= 3, (
                f"{_name(path)} line {i + 1}: an import probe with no "
                f"warm-up and no retry; the first python call of the "
                f"session fails under the runner regardless of the import"
            )

    def test_the_runner_does_not_probe_python_by_executing_it(self):
        with open(_RUNNER, encoding="utf-8") as fh:
            src = fh.read()
        code = "\n".join(l.split("//", 1)[0] for l in src.splitlines())
        assert "capture python" not in code, _RUNNER

    def test_a_script_that_needs_python_says_so_through_the_setting(self,
                                                                    cscript):
        path, src = cscript
        if "SKIP: Python not available" not in src:
            pytest.skip("this script does not depend on Python")
        assert "c(python_exec)" in src, (
            f"{_name(path)} reports Python as unavailable without consulting "
            f"Stata's Python configuration"
        )


class TestNoFileReadMacroIsExpandedInPlainQuotes:
    """A line of data may contain a quote; a line of code must survive it."""

    # `local ln' read from a file, expanded inside "..." rather than `"..."'
    _UNSAFE = re.compile(r'(?<!`)"`(ln|line|l|html_line|content)\'"')

    def test_no_unsafe_expansion(self, cscript):
        path, src = cscript
        bad = []
        for i, line in enumerate(src.splitlines(), 1):
            code = line.split("//", 1)[0]
            if self._UNSAFE.search(code):
                bad.append(f"{_name(path)}:{i}: {line.strip()}")
        assert not bad, (
            "a macro holding a line read from a file is expanded inside "
            "plain double quotes; a quote character in the data ends the "
            "Stata string and the rest of the line is parsed as code:\n"
            + "\n".join(bad)
        )


class TestEveryCscriptIsWiredIntoTheRunner:
    """A script the runner never calls is a script that never certifies."""

    def test_the_runner_calls_it(self, cscript):
        path, _ = cscript
        with open(_RUNNER, encoding="utf-8") as fh:
            runner = fh.read()
        assert _name(path) in runner, (
            f"{_name(path)} exists but run_all_cscripts.do never runs it"
        )


class TestTheShippedAdoFilesFollowTheSameRule:
    """The rule was enforced for .cscript files only.

    That is how ``dash_setup.ado`` kept ``capture python query`` as its
    availability probe, and how ``dash.ado`` reached ``python:`` with no
    check at all -- ``c(python_exec)`` appeared in neither file. The cost of
    probing by execution is already measured in this file's docstring: the
    first python call of a session returns a nonzero rc under the runner on
    a machine where dash renders Bokeh output seconds later.

    Availability is configuration. Running Python to ask whether Python is
    there can fail for reasons that have nothing to do with the answer.
    """

    @pytest.fixture(params=_ADOS, ids=lambda p: os.path.basename(p))
    def ado(self, request):
        with open(request.param, encoding="utf-8") as fh:
            return request.param, fh.read()

    @staticmethod
    def _code(src):
        """Source with // comments and *! header lines removed."""
        out = []
        for line in src.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("//") or stripped.startswith("*!"):
                continue
            out.append(line.split("//", 1)[0])
        return out

    def test_availability_is_not_decided_by_running_python(self, ado):
        path, src = ado
        bad = [
            f"{os.path.basename(path)}:{i}: {line.strip()}"
            for i, line in enumerate(self._code(src), 1)
            if "capture python query" in line
        ]
        assert not bad, (
            "availability is decided by running Python; use "
            "c(python_exec), which is configuration and cannot fail for "
            "reasons unrelated to the question:\n" + "\n".join(bad)
        )

    def test_availability_is_decided_by_the_setting(self, ado):
        path, src = ado
        code = "\n".join(self._code(src))
        assert "python_exec" in code, (
            f"{os.path.basename(path)} reaches Python but never consults "
            f"c(python_exec); a user with no linked Python gets a raw Stata "
            f"Python error naming neither dash nor the remedy"
        )

    def test_a_bare_python_pass_is_not_used_as_a_probe(self, ado):
        path, src = ado
        lines = self._code(src)
        bad = []
        for i, line in enumerate(lines):
            if "capture python: pass" not in line:
                continue
            after = "\n".join(lines[i + 1:i + 5])
            if "not available" in after or "Python is not" in after:
                bad.append(i + 1)
        assert not bad, (
            f"{os.path.basename(path)} lines {bad}: concludes Python is "
            f"missing from the rc of a bare warm-up call"
        )

    # -- No untrusted value may be inlined into Python SOURCE ----------------
    #
    # A Stata macro expanded inside a Python string literal on a ``python:``
    # line becomes part of the program text: a double quote in the value ends
    # the string and the rest runs as code.  ``dash_setup.ado`` shipped two
    # such sites -- ``Version("`got'")`` (an untrusted distribution version)
    # and ``r"`render_py'"`` (a file path) -- and both were exploitable
    # (measured: an ``os.system`` and an ``sfi.Macro.setGlobal`` injected
    # through them ran).  The safe form reads the value with
    # ``sfi.Macro.getLocal``, which passes it as a string argument the
    # interpreter never parses.
    #
    # Every in-string macro that remains must be on the per-file allowlist,
    # with its reason: escaped by ``_dash_json_str``, validated by a strict
    # regex, or drawn only from a fixed list of constants in the code.

    def test_no_untrusted_macro_is_inlined_into_python_source(self, ado):
        path, src = ado
        base = os.path.basename(path)
        allowed = _ALLOWED_INLINE_PY_MACROS.get(base, {})
        bad = []
        for start, py in _python_command_sources(src):
            for macro in sorted(_macros_inside_string_literals(py)):
                if macro not in allowed:
                    bad.append(f"{base}:{start}: `{macro}' inside a Python "
                               f"string literal")
        assert not bad, (
            "a Stata macro is expanded inside a Python string literal on a "
            "python: line; a quote in the value ends the string and the rest "
            "runs as code. Read the value with sfi.Macro.getLocal instead, or "
            "add it to _ALLOWED_INLINE_PY_MACROS with the reason it is safe "
            "(escaped, regex-validated, or from a fixed list):\n"
            + "\n".join(bad)
        )

    def test_the_known_setup_injection_sites_stay_closed(self):
        """A crisp regression guard for the three sites WP-20 closed in
        dash_setup.ado: the version gate, the scheme probe and the package
        version query.

        Independent of the allowlist above, so gaming the allowlist cannot
        quietly reopen them.
        """
        with open(os.path.join(_REPO, "dash_setup.ado"), encoding="utf-8") as fh:
            code = "\n".join(self._code(fh.read()))
        # The exact vulnerable interpolations must be gone ...
        assert 'Version("`got' + "'" + '")' not in code, (
            "the version gate again interpolates the untrusted `got' into "
            "Version(); read it with sfi.Macro.getLocal(\"got\")"
        )
        assert 'r"`render_py' + "'" + '"' not in code, (
            "the scheme probe again interpolates the path `render_py' into a "
            "raw string; read it with sfi.Macro.getLocal(\"render_py\")"
        )
        # ... and the safe reads must be present.
        assert 'getLocal("got")' in code and 'getLocal("want")' in code, (
            "the version gate must read got/want with sfi.Macro.getLocal"
        )
        assert 'getLocal("render_py")' in code, (
            "the scheme probe must read render_py with sfi.Macro.getLocal"
        )
        assert '"`pkg' + "'" + '".lower()' not in code and \
            'getLocal("pkg")' in code, (
            "the package version query must read pkg with sfi.Macro.getLocal"
        )


# ---------------------------------------------------------------------------
# No certification script may build a dashboard with the browser allowed.
# ---------------------------------------------------------------------------
#
# run_all_cscripts.do sets `global dash_nobrowser 1' so that no dash build in
# the suite opens a window.  But every script starts with `cscript', and
# `cscript' drops EVERY global macro -- measured 23sep2026 on StataNow 19.5:
# `global dash_nobrowser 1', then `cscript "probe"', left the global empty,
# where `clear all', `clear *', `clear' and `program drop _all' all kept it.
# So inside the scripts the runner's setting was gone, and 13 of them built
# dashboards with nothing but an explicit `nobrowser' option -- or not even
# that -- standing between the suite and one browser window per build.  Under
# the console binary `xdg-open' is absent and nothing opened; a run from the
# Stata GUI would have opened them.
#
# The rule: after `cscript', before any dashboard is built, the script sets
# the global -- itself, or by loading cert_helpers.do, which sets it.  Built
# means `dash build', or an immediate `dash <plot>' with neither name()
# (which only registers) nor saving() (with which dash never opens a
# window).  `dash serve' is not counted: the suite never lets it launch.

_HELPERS = os.path.join(_HERE, "cert_helpers.do")


def _stata_logical_lines(src):
    """``(first line number, code)`` for each command in a do-file.

    Stata's own comment rules: a line whose first non-blank is ``*`` is a
    comment; ``/* */`` spans lines; ``//`` and ``///`` begin a comment only
    at the start of a line or after a blank; ``///`` also joins the next
    line on.  Strings are not parsed, so a ``//`` inside a URL after a blank
    ends the line early -- which can only hide text, and a hidden build is
    caught by the build itself being required to come after the global.
    """
    src = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"),
                 src, flags=re.S)
    out, buf, start = [], "", None
    for n, raw in enumerate(src.splitlines(), 1):
        line = raw
        if not buf and line.lstrip().startswith("*"):
            continue
        cont = False
        m = re.search(r"(^|\s)///", line)
        if m:
            line, cont = line[:m.start()], True
        else:
            m = re.search(r"(^|\s)//", line)
            if m:
                line = line[:m.start()]
        if start is None:
            start = n
        buf += " " + line
        if not cont:
            if buf.strip():
                out.append((start, buf.strip()))
            buf, start = "", None
    if buf.strip():
        out.append((start, buf.strip()))
    return out


_PREFIX = re.compile(r"^(?:(?:capture|cap|noisily|noi|quietly|qui|n)\b\s*:?\s*)+")
_DISPLAY = re.compile(r"^di(s(p(l(a(y)?)?)?)?)?\b")
_BLOCK = re.compile(r"^(python|mata)\s*:?\s*$")
_ONE_LINER = re.compile(r"^(python|mata)\s*:")
_BLOCK_END = re.compile(r"^end\s*$")
#: `dash' at the start of a command, or at the start of a quoted command
#: handed to a helper (`_run "dash build, ..."'); the subcommand may be a
#: macro (`dash ${cmd}'), which is taken for a build since it may be one.
_DASH = re.compile(r"""(?:^|`"|")dash\s+(\(|[A-Za-z_]\w*|[`$])""")
_NOT_A_BUILD = {"serve", "kpi", "clear"}
_SAVING = re.compile(r"\bsav(i(n(g)?)?)?\s*\(")
_NAME = re.compile(r"\bnam(e)?\s*\(")
_SETS = re.compile(r"^global\s+dash_nobrowser\s+\S")
_DROPS = re.compile(r"^macro\s+drop\b.*(\bdash_nobrowser\b|\bdash_\*|\b_all\b)"
                    r"|^global\s+dash_nobrowser\s*(\"\")?\s*$")
_LOADS_HELPERS = re.compile(r"^(do|run)\s+\"?[^\"\s]*cert_helpers\.do")
_CSCRIPT = re.compile(r"^cscript\b")


def _builds(code):
    """Does this command build a dashboard?  `dash build', or an immediate
    plot with neither name() nor saving()."""
    for m in _DASH.finditer(code):
        sub = m.group(1)
        if sub == "build":
            return True
        if sub in _NOT_A_BUILD:
            continue
        rest = code[m.start():]
        if not _SAVING.search(rest) and not _NAME.search(rest):
            return True
    return False


def _helpers_set_the_global():
    with open(_HELPERS, encoding="utf-8") as fh:
        return any(_SETS.match(_PREFIX.sub("", code))
                   for _n, code in _stata_logical_lines(fh.read()))


def _builds_with_the_browser_allowed(src, helpers_set):
    """The line numbers of every dashboard built while $dash_nobrowser is
    not set: before `cscript' has run and the global been set after it, or
    after the global was dropped.  Program bodies are read where they are
    defined, which is where a script sets itself up; Python and Mata blocks
    are not Stata commands."""
    state, block, bad = False, False, []
    for n, raw in _stata_logical_lines(src):
        code = _PREFIX.sub("", raw)
        if block:
            if _BLOCK_END.match(code):
                block = False
            continue
        if _BLOCK.match(code):
            block = True
            continue
        if _ONE_LINER.match(code) or _DISPLAY.match(code):
            continue
        if _CSCRIPT.match(code):
            state = False
            continue
        if _SETS.match(code):
            state = True
        elif _DROPS.match(code):
            state = False
        elif _LOADS_HELPERS.match(code) and helpers_set:
            state = True
        if _builds(code) and not state:
            bad.append(n)
    return bad


class TestTheDetectorReadsStataAsStataDoes:
    """The rule below is only as good as its reading of a do-file."""

    def _bad(self, text, helpers_set=True):
        return _builds_with_the_browser_allowed(text, helpers_set)

    def test_a_build_before_the_global_is_flagged(self):
        assert self._bad('cscript "x"\ndash build, saving(a.html)\n') == [2]

    def test_the_global_set_after_cscript_protects(self):
        assert self._bad('cscript "x"\nglobal dash_nobrowser 1\n'
                         'dash build, saving(a.html)\n') == []

    def test_the_global_set_before_cscript_does_not(self):
        """cscript drops it: that is the whole defect."""
        assert self._bad('global dash_nobrowser 1\ncscript "x"\n'
                         'dash build, saving(a.html)\n') == [3]

    def test_loading_cert_helpers_protects_only_if_it_sets_the_global(self):
        text = 'cscript "x"\ndo "cert_helpers.do"\ndash build, saving(a.html)\n'
        assert self._bad(text, helpers_set=True) == []
        assert self._bad(text, helpers_set=False) == [3]

    def test_dropping_the_global_unprotects(self):
        assert self._bad('cscript "x"\nglobal dash_nobrowser 1\n'
                         'macro drop dash_nobrowser\n'
                         'capture noisily dash build, saving(a.html)\n') == [4]

    def test_an_immediate_plot_builds_unless_named_or_saved(self):
        text = ('cscript "x"\n'
                'dash scatter mpg weight\n'                       # 2: builds
                'dash scatter mpg weight, name(g1)\n'             # registers
                'dash (line mpg weight), saving("o.html")\n'      # never opens
                'dash scatter mpg ///\n    weight, sav(o.html)\n'  # joined line
                'dash kpi mean(mpg), name(k1)\n'
                'dash clear\n'
                'capture dash serve, port(1)\n')
        assert self._bad(text) == [2]

    def test_a_command_handed_to_a_helper_counts(self):
        assert self._bad('cscript "x"\n'
                         '_run `"dash build, saving("a.html")"\'\n') == [2]

    def test_a_macro_subcommand_counts(self):
        assert self._bad('cscript "x"\ncapture quietly dash ${CMD`i\'}\n') == [2]

    def test_comments_displays_and_embedded_code_do_not(self):
        text = ('cscript "x"\n'
                '* dash build, saving(a.html)\n'
                '// dash build\n'
                'di "dash build refused"\n'
                'display as error "V2 FAIL: -dash scatter mpg weight-"\n'
                '/* dash build\n   dash scatter mpg weight */\n'
                'python:\n'
                'x = "dash build"\n'
                'end\n'
                'mata: st_local("s", "dash build")\n'
                'local x = 1   // dash build\n')
        assert self._bad(text) == []

    def test_a_program_body_is_read_where_it_is_defined(self):
        text = ('cscript "x"\n'
                'program define _b\n'
                '    capture noisily dash build, saving(a.html) replace\n'
                'end\n'
                'global dash_nobrowser 1\n'
                '_b\n')
        assert self._bad(text) == [3]


class TestNoScriptBuildsWithTheBrowserAllowed:
    """Every script that builds a dashboard sets $dash_nobrowser after its
    `cscript' line, itself or through cert_helpers.do."""

    def test_cert_helpers_sets_the_global(self):
        assert _helpers_set_the_global(), (
            "cert_helpers.do does not set `global dash_nobrowser 1'; the "
            "scripts that load it right after `cscript' then build with "
            "the browser allowed, because cscript dropped the runner's"
        )

    def test_no_build_runs_with_the_browser_allowed(self, cscript):
        path, src = cscript
        bad = _builds_with_the_browser_allowed(src, _helpers_set_the_global())
        assert not bad, (
            f"{_name(path)} builds a dashboard at line(s) {bad} with "
            f"$dash_nobrowser unset: `cscript' drops every global, so the "
            f"runner's setting does not reach the script.  Set `global "
            f"dash_nobrowser 1' after the cscript line, or load "
            f"cert_helpers.do there"
        )
