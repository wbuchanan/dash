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

Under WP-36's ruling M8 (plat:PT-1) nothing decides whether Python is there
at all: with no Python set, Stata finds one on the first ``python:`` line,
so no script skips for want of a ``c(python_exec)`` value, and a script on a
machine with no Python fails where it used to skip.  What stays is the rule
against concluding "no Python" from running Python: no ``python query``, no
decision from a bare ``capture python: pass``.

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
import sys

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
        # WP-30 P1.31a: r(maxsessions) and r(idletimeout), digits only.
        "_srv_maxs": "digits only, 1-1,000,000, checked byte by byte (_dash_is_digits) in _dash_serve_spec",
        "_srv_idle": "digits only, 0-525600, checked byte by byte (_dash_is_digits) in _dash_serve_spec",
    },
    # dash_setup.ado has no entry: its last in-string macro, `_spec' in the
    # inline pip call, went with that call (WP-29 P0.19) -- the spec now
    # reaches Python by sfi.Macro.getLocal in dash_setup_lib.stata_pip.
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


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


# The guards below keyed on literal text -- "capture python: pass",
# "capture python:", "SKIP: Python not available" -- and every one of them
# let the same command or message through in another spelling (measured
# 24sep2026): `cap python: pass' is Stata's own abbreviation, and seven
# scripts say "SKIP: no Python is linked to this Stata.", so the setting
# check skipped them.  One reading of each, self-tested below.

#: `capture' in every spelling Stata accepts, cap to capture.
_CAP = r"\bcap(?:t(?:u(?:r(?:e)?)?)?)?\s+"
#: Any quietly/noisily prefixes after it, in every spelling.
_QN = (r"(?:(?:qui(?:e(?:t(?:l(?:y)?)?)?)?|n(?:o(?:i(?:s(?:i(?:l(?:y)?)?)?)?)?)?)"
       r"\s+)*")
#: A bare warm-up call, `capture python: pass'.
_WARM_UP = re.compile(_CAP + _QN + r"python\s*:\s*pass\b")
#: A captured python one-liner as the import-probe rule counts one: capture
#: directly before `python:', as the literal it replaces.  Not `capture
#: noisily python:', which the rule has never read as a probe (SVG-05 in
#: test_setup_version_gate.cscript is one, after its own warm-up).
_CAPTURED_PY = re.compile(_CAP + r"python\s*:")
#: Any captured python call at all: a one-liner or `python query'.
_ANY_CAPTURED_PY = re.compile(_CAP + _QN + r"python\b")
#: A script's message that it skipped for want of Python.  Two wordings are
#: in use: "SKIP: Python not available" (35 scripts) and "SKIP: no Python is
#: linked to this Stata." (7).
_SKIPS_FOR_PYTHON = re.compile(r"SKIP[^\"\n]*\bPython\b")
#: A script's words for "Python is missing", in either wording.
_SAYS_NO_PYTHON = re.compile(r"(?i)\bpython\b[^\"\n]*\bnot\b|\bno\s+python\b")
#: A shipped ado file's words for it ("Python is not available to Stata.").
_ADO_SAYS_NO_PYTHON = re.compile(r"(?i)not available|python is not"
                                 r"|\bno\s+python\b")


def _decides_from_a_warm_up(lines, says):
    """1-based numbers of the lines that hold a bare warm-up call followed,
    within four lines, by *says*: "Python is missing" concluded from the rc
    of a call that fails under the runner whatever Python's state."""
    bad = []
    for i, line in enumerate(lines):
        if not _WARM_UP.search(line):
            continue
        if says.search("\n".join(lines[i + 1:i + 5])):
            bad.append(i + 1)
    return bad


def _import_probes(src):
    """``(probes, bad)``: the 0-based lines of every captured python call
    that imports, and the 1-based lines of those with no warm-up and retry
    -- fewer than three captured python calls in the six lines around."""
    code = [l.split("//", 1)[0] for l in src.splitlines()]
    probes = [i for i, l in enumerate(code)
              if _CAPTURED_PY.search(l) and "import" in l]
    bad = [i + 1 for i in probes
           if len(_CAPTURED_PY.findall(
               "\n".join(code[max(0, i - 3):i + 3]))) < 3]
    return probes, bad


class TestTheGuardReadersReadEverySpelling:
    """The readers above, on text they must and must not flag."""

    def test_a_warm_up_that_decides_python_is_missing_is_flagged(self):
        for text in (
                'capture python: pass\nif _rc {\n'
                '    display as error "SKIP: Python not available"\n'
                '    exit 222\n}\n',
                'cap python: pass\nif _rc {\n'
                '    display as text "SKIP: no Python is linked to this '
                'Stata."\n}\n',
                'capture quietly python: pass\n'
                'if _rc display "SKIP: Python is not configured"\n'):
            assert _decides_from_a_warm_up(text.splitlines(),
                                           _SAYS_NO_PYTHON) == [1], text

    def test_a_warm_up_before_a_real_probe_is_not(self):
        text = ('if `"`c(python_exec)\'"\' == "" {\n'
                '    display as error "SKIP: Python not available."\n'
                '    exit 222\n}\n'
                'capture python: pass\n'
                'capture python: import bokeh\n'
                'if _rc != 0 capture python: import bokeh\n'
                'if _rc != 0 {\n'
                '    display as error "SKIP: bokeh not installed."\n}\n')
        assert _decides_from_a_warm_up(text.splitlines(),
                                       _SAYS_NO_PYTHON) == []

    def test_the_ado_wording_is_flagged(self):
        text = ('capt python: pass\nif _rc {\n'
                '    display as error "Python is not available to Stata."\n'
                '}\n')
        assert _decides_from_a_warm_up(text.splitlines(),
                                       _ADO_SAYS_NO_PYTHON) == [1]

    def test_an_import_probe_needs_a_warm_up_and_a_retry(self):
        bare = ('cap python: import bokeh\nif _rc {\n'
                '    display "SKIP: bokeh not installed"\n}\n')
        assert _import_probes(bare) == ([0], [1])
        good = ('capt python: pass\ncap python: import bokeh\n'
                'if _rc != 0 capture python: import bokeh\n')
        assert _import_probes(good) == ([1, 2], [])
        # SVG-05's shape: an operation after a warm-up, not a probe.
        assert _import_probes('capture python: pass\ncapture noisily '
                              'python: from x import y; z = 1\n') == ([], [])

    def test_every_spelling_of_a_captured_python_call_is_seen(self):
        for text in ("capture python: pass", "cap python: pass",
                     "capture noisily python: pass", "capt python query",
                     "cap qui python: import bokeh"):
            assert _ANY_CAPTURED_PY.search(text), text
        assert not _ANY_CAPTURED_PY.search('display "python: pass"')

    def test_a_python_command_is_read_in_every_prefix_spelling(self):
        """The in-string macro rule reads python: commands through _PREFIX;
        a spelling it did not strip hid the whole command."""
        for prefix in ("", "capture ", "capt ", "cap noisily ",
                       "capture n ", "quie ", "qui cap "):
            cmds = _python_command_sources(prefix + 'python: x = "`m\'"\n')
            assert len(cmds) == 1, prefix
            assert _macros_inside_string_literals(cmds[0][1]) == {"m"}, prefix

    def test_both_skip_wordings_are_read(self):
        for text in ('display as error "SKIP: Python not available"',
                     'display as text "SKIP: no Python is linked to this '
                     'Stata."'):
            assert _SKIPS_FOR_PYTHON.search(text), text
        assert not _SKIPS_FOR_PYTHON.search(
            'display as error "SKIP: bokeh not installed."')


class TestTheChecksReachEveryScript:
    """A per-script check that finds nothing to check passes.  These pin how
    much each reader finds, measured 24sep2026."""

    def test_the_glob_finds_every_script(self):
        # 65 certification scripts, each also named by run_all_cscripts.do
        # (59, and WP-24's test_bug_regressions, test_program_coverage,
        # test_qualifier_literals and test_mata_library_guard; WP-27's
        # test_qualifier_in_stata and test_string_values; the S3 batch's
        # test_ci_band_options), less
        # test_jsonio.cscript, which certified jsonio itself and went with
        # it (24sep2026); plus WP-28's test_gaps2_truth, the one script the
        # package adds (review D11): every twoway/Stata-value comparison of
        # the GAPS2 fix package lives in this one script, one block per
        # section, so 66; plus WP-29's test_wp29_truth, the one script that
        # package adds (.ultraplan/wp29/index.md A3), so 67; plus WP-30's
        # test_wp30_truth, the one script that package adds
        # (.ultraplan/wp30/index.md A142), so 68 now; plus WP-31's
        # test_wp31_truth (.ultraplan/sections/index.md A5), so 69; plus
        # 69 -> 70: test_wp33_truth.cscript (WP-33 33-01).  An empty
        # glob would leave every per-script test above with no parameters,
        # and pytest reports that as a skip, not a failure.
        # 70 -> 71: test_wp34_truth.cscript (WP-34 W0).
        # 71 -> 72: test_wp35_truth.cscript (WP-35 W0).
        # 72 -> 73: test_wp36_truth.cscript (WP-36 W0).
        # 73 -> 74: test_wp37_truth.cscript (WP-37 W0).
        # 74 -> 75: test_wp38_truth.cscript (WP-38 W0).
        assert len(_CSCRIPTS) == 75, (
            f"{len(_CSCRIPTS)} .cscript files found in {_HERE}"
        )

    def test_every_script_that_skips_for_python_is_read(self):
        names = {_name(p) for p in _CSCRIPTS
                 if _SKIPS_FOR_PYTHON.search(_read(p))}
        # 42, and three of WP-24's new scripts: test_mata_library_guard
        # runs no Python.  And WP-27's test_qualifier_in_stata and
        # test_string_values.  WP-28's test_gaps2_truth gates on
        # c(python_exec) itself (its own line, not cert_svg.do's, which
        # loads after it and would otherwise be the only carrier), so 48;
        # WP-29's test_wp29_truth gates the same way, so 49; WP-30's
        # test_wp30_truth gates the same way, so 50; WP-31's test_wp31_truth
        # gates the same way, so 51.
        # 51 -> 52: test_wp33_truth gates on c(python_exec) (WP-33 33-01)
        # 52 -> 53: test_wp34_truth gates on c(python_exec) (WP-34 W0)
        # 53 -> 54: test_wp35_truth gates on c(python_exec) (WP-35 W0)
        # 54 -> 55: test_wp36_truth gates on c(python_exec) (WP-36 W0)
        # 55 -> 0: WP-36 plat:PT-1 -- no script skips for want of a Python setting (M8)
        assert len(names) == 0, f"{len(names)}: {sorted(names)}"

    def test_the_import_probes_are_found(self):
        with_probes = [_name(p) for p in _CSCRIPTS
                       if _import_probes(_read(p))[0]]
        # 11, and WP-24's test_bug_regressions and test_setup_honesty
        # (HON-19..25 probe the four packages dash_setup checks).  WP-28's
        # test_gaps2_truth carries no captured python: import probe, so
        # this stays 13 (verified by running the file, not by inspection).
        assert len(with_probes) == 13, with_probes


class TestTheAvailabilityGuardIsReliable:

    def test_no_script_probes_python_by_executing_it(self, cscript):
        path, src = cscript
        code = "\n".join(l.split("//", 1)[0] for l in src.splitlines())
        lines = code.splitlines()
        # A bare warm-up before a real probe is fine and is in fact
        # required; what is not fine is concluding "Python is missing" from
        # its rc -- in any spelling of the warm-up, in either wording.
        bad = _decides_from_a_warm_up(lines, _SAYS_NO_PYTHON)
        assert not bad, (
            f"{_name(path)} lines {bad}: decides whether Python is available "
            f"by running it; measured, that reports a nonzero rc under the "
            f"runner on a machine where Python works, and the script "
            f"silently skips"
        )

    # Only the scripts that run an import probe (13, pinned by
    # TestTheChecksReachEveryScript): the others were 50 skips of this test.
    @pytest.mark.parametrize(
        "path", [p for p in _CSCRIPTS if _import_probes(_read(p))[0]],
        ids=_name)
    def test_a_probe_that_must_run_python_retries(self, path):
        """Checking for a package can only be done by importing it.

        The first python call of a session fails under the runner whatever it
        is, so such a probe must spend that failure on a throwaway call and
        ask its real question afterwards -- otherwise a machine with bokeh
        installed reports bokeh missing and the script skips.
        """
        src = _read(path)
        # `cap python: import bokeh' is a probe as much as the spelled-out
        # form, and counts toward the warm-up and retry the same way.
        probes, bad = _import_probes(src)
        assert probes, _name(path)
        assert not bad, (
            f"{_name(path)} line(s) {bad}: an import probe with no "
            f"warm-up and no retry; the first python call of the "
            f"session fails under the runner regardless of the import"
        )

    def test_the_runner_does_not_probe_python_by_executing_it(self):
        """A structural guard over the runner's text, deliberately: a probe
        that runs Python fails under the runner on a machine where Python
        works, and what follows is a silent SKIP of every script -- which no
        behavioural test sees, because a skipped suite is a green one."""
        with open(_RUNNER, encoding="utf-8") as fh:
            src = fh.read()
        code = "\n".join(l.split("//", 1)[0] for l in src.splitlines())
        assert "capture python" not in code, _RUNNER
        # `cap python: pass' and `capture noisily python: pass' are the same
        # probe in other spellings.
        hit = _ANY_CAPTURED_PY.search(code)
        assert not hit, f"{_RUNNER}: {hit.group(0) if hit else ''}"

    # Flipped (WP-36 plat:PT-1, M8): was
    # test_a_script_that_needs_python_says_so_through_the_setting,
    # parametrised over the scripts that could skip for want of Python; none
    # can now.  Not parametrised, so it never collects an empty set (which a
    # strict run counts as a skip).
    def test_no_script_skips_for_want_of_python(self):
        """The count pin above reads test/*.cscript; this reads the two
        files outside it, so no future truth script is born with the skip
        (the template) and cert_svg.do cannot skip for its callers."""
        for path in (_WP_TEMPLATE, os.path.join(_HERE, "cert_svg.do")):
            hit = _SKIPS_FOR_PYTHON.search(_read(path))
            assert not hit, (os.path.basename(path), hit.group(0) if hit else "")


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

    WP-36 plat:PT-1 (M8): neither file refuses an empty ``c(python_exec)``
    any more -- Stata finds its own Python on the first ``python:`` line --
    but each still reads the setting (for the Python it names) and neither
    runs ``python query`` or decides from a bare ``python: pass``.
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
        # Any spelling of the warm-up (`cap python: pass' slipped past the
        # literal this read), self-tested in TestTheGuardReadersReadEvery-
        # Spelling.
        bad = _decides_from_a_warm_up(lines, _ADO_SAYS_NO_PYTHON)
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
        commands = _python_command_sources(src)
        # A reader that finds no python: command checks nothing and passes.
        # Measured 01oct2026 (WP-29 P0.19): 23 in dash.ado, 21 in
        # dash_setup.ado.
        assert commands, f"{base}: no python: command was found to check"
        found = set()
        for start, py in commands:
            macros = _macros_inside_string_literals(py)
            found |= macros
            for macro in sorted(macros):
                if macro not in allowed:
                    bad.append(f"{base}:{start}: `{macro}' inside a Python "
                               f"string literal")
        # The positive control: every allowlisted macro is one the scanner
        # finds inside a string literal -- the reason it is on the list.  A
        # scanner that never entered a string, or a reader that missed the
        # lines, fails here instead of passing; so does a stale entry, which
        # would wave a reintroduced site through unread.
        stale = sorted(set(allowed) - found)
        assert not stale, (
            f"{base}: allowlisted but not found inside a Python string "
            f"literal on any python: line: {stale}"
        )
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


#: capture, noisily and quietly in every spelling Stata accepts (cap...,
#: n..., qui...).  It listed seven, so `capt python: ...' was not seen as a
#: python: command at all, and a macro inlined into it went unchecked.
_PREFIX = re.compile(r"^(?:(?:cap(?:t(?:u(?:r(?:e)?)?)?)?"
                     r"|n(?:o(?:i(?:s(?:i(?:l(?:y)?)?)?)?)?)?"
                     r"|qui(?:e(?:t(?:l(?:y)?)?)?)?)\b\s*:?\s*)+")
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
        """A structural guard over the harness's text, deliberately: a
        certification run that opens a browser window per dashboard still
        passes, so only reading cert_helpers.do can hold it to the rule."""
        assert _helpers_set_the_global(), (
            "cert_helpers.do does not set `global dash_nobrowser 1'; the "
            "scripts that load it right after `cscript' then build with "
            "the browser allowed, because cscript dropped the runner's"
        )

    def test_no_build_runs_with_the_browser_allowed(self, cscript):
        """A structural guard over each script's text, deliberately, for the
        same reason: the build succeeds whether or not a window opens, so
        the rule is read from the script (by the reader the class above
        tests), not observed."""
        path, src = cscript
        bad = _builds_with_the_browser_allowed(src, _helpers_set_the_global())
        assert not bad, (
            f"{_name(path)} builds a dashboard at line(s) {bad} with "
            f"$dash_nobrowser unset: `cscript' drops every global, so the "
            f"runner's setting does not reach the script.  Set `global "
            f"dash_nobrowser 1' after the cscript line, or load "
            f"cert_helpers.do there"
        )


# ---------------------------------------------------------------------------
# jsonio is not a dependency
# ---------------------------------------------------------------------------
# dash exported its data with jsonio until 24sep2026; it now writes the file
# itself from Stata's Python (dash.ado _dash_write_data).  dash_setup still
# installed jsonio from SSC and failed the run without it, and 49
# certification scripts still began `capture which jsonio ... exit 222': a
# skip on a package dash does not use, so a machine without it certified
# nothing and reported every script as skipped.

#: A `which jsonio' whose result can end the script within four lines.
_JSONIO_GUARD = re.compile(
    r"^[ \t]*(?:cap(?:t(?:u(?:r(?:e)?)?)?)?\s+)?which\s+jsonio\b[^\n]*"
    r"(?:\n[^\n]*){0,4}?\n[^\n]*\bexit\s+\d+", re.M)


def _code_only(src):
    """Stata source with // comments, *! and * comment lines dropped."""
    out = []
    for ln in src.splitlines():
        if ln.lstrip().startswith("*"):
            continue
        out.append(ln.split("//", 1)[0])
    return "\n".join(out)


def _display_seam_problems(src):
    """WP-30 P1.27: the undocumented test seam ``$dash__display`` may be set
    only after a stub is first on PATH (``os.environ["PATH"] =``) or the
    ado-path (``adopath ++`` naming a stub folder); must be dropped after
    it is set; and while it is on with ``$dash_nobrowser`` unset, no
    ``dash build`` may run outside the body of a program defined earlier
    (the stub controls' own helpers).  Returns the problems, as text."""
    out = []
    lines = src.splitlines()
    stub_seen = False
    set_at = None
    seam_on = False
    nb_unset = False
    in_prog = False
    for n, line in enumerate(lines, 1):
        code = line.split("//", 1)[0]
        st = code.strip()
        if re.match(r"program\s+(define\s+)?\w", st) and not st.startswith(
                "program drop"):
            in_prog = True
            continue
        if in_prog:
            if st == "end":
                in_prog = False
            continue
        if 'os.environ["PATH"] =' in code or (
                "adopath ++" in code and "stub" in code):
            stub_seen = True
        if re.match(r"\s*global\s+dash__display\s+\S", code):
            if not stub_seen:
                out.append(f"line {n}: sets the seam with no stub first")
            if set_at is None:
                set_at = n
            seam_on = True
        if re.search(r"macro\s+drop\s+dash__display", code):
            seam_on = False
        if re.search(r"macro\s+drop\s+dash_nobrowser", code) or re.match(
                r'\s*global\s+dash_nobrowser\s*(""\s*)?$', code):
            nb_unset = True
        elif re.match(r"\s*global\s+dash_nobrowser\s+\S", code):
            nb_unset = False
        if seam_on and nb_unset and re.match(
                r"\s*(cap(ture)?\s+(n(oisily)?\s+)?)?(qui(etly)?\s+)?"
                r"dash\s+build\b", code):
            out.append(f"line {n}: builds with the seam on and "
                       "$dash_nobrowser unset, outside a stub helper")
    if set_at is not None and not any(
            re.search(r"macro\s+drop\s+dash__display", l.split("//", 1)[0])
            for l in lines[set_at:]):
        out.append(f"line {set_at}: sets the seam and never drops it")
    return out


class TestTheDisplaySeamIsFenced:
    """The seam reaches no sink a user's session does not: only behind a
    stub, and always dropped (WP-30 P1.27)."""

    def test_the_detector_reads_the_seam(self):
        assert _display_seam_problems("global dash__display on\n")
        ok = ('python: os.environ["PATH"] = x\n'
              "global dash__display on\nmacro drop dash__display\n")
        assert _display_seam_problems(ok) == []
        undropped = 'adopath ++ "`stubdir\'"\nglobal dash__display on\n'
        assert _display_seam_problems(undropped)
        loose_build = ('adopath ++ "`stubdir\'"\nmacro drop dash_nobrowser\n'
                       "global dash__display on\n"
                       "dash build, saving(x.html)\n"
                       "macro drop dash__display\n")
        assert _display_seam_problems(loose_build)
        helper = ('program define _h\n    dash build, saving(x.html)\nend\n'
                  'adopath ++ "`stubdir\'"\nmacro drop dash_nobrowser\n'
                  "global dash__display on\n_h\nmacro drop dash__display\n")
        assert _display_seam_problems(helper) == []

    def test_no_script_sets_the_seam_without_a_stub_and_a_drop(self):
        bad = {}
        for path in sorted(glob.glob(os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "*.cscript"))):
            with open(path, encoding="utf-8") as fh:
                probs = _display_seam_problems(fh.read())
            if probs:
                bad[os.path.basename(path)] = probs
        assert bad == {}


class TestJsonioIsNotADependency:

    def test_the_guard_reader_finds_the_old_guard(self):
        old = ('capture which jsonio\nif _rc != 0 {\n'
               '    display as error "SKIP: jsonio not installed."\n'
               '    exit 222\n}\n')
        assert _JSONIO_GUARD.search(old)
        # HC8-17's check that jsonio is OFF the path is not a guard.
        ok = ('capture program drop jsonio\ncapture which jsonio\n'
              'local on = (_rc == 0)\n')
        assert not _JSONIO_GUARD.search(ok)

    def test_no_cscript_skips_or_stops_for_want_of_jsonio(self):
        bad = [_name(p) for p in _CSCRIPTS
               if _JSONIO_GUARD.search(_code_only(_read(p)))
               or re.search(r"SKIP[^\"\n]*jsonio not installed", _read(p))]
        assert not bad, (
            f"{bad}: skip or stop when jsonio is missing, a package dash "
            f"does not use")

    def test_dash_setup_neither_installs_nor_requires_jsonio(self):
        with open(_ADOS[1], encoding="utf-8") as fh:
            code = _code_only(fh.read())
        assert "jsonio" not in code, (
            "dash_setup.ado still checks or installs jsonio")


# ---------------------------------------------------------------------------
# WP-29's truth script: one block per section, gated, closed, in order
# ---------------------------------------------------------------------------
# test/test_wp29_truth.cscript is WP-29's one new certification script
# (.ultraplan/wp29/index.md A3, merge rule R1).  The fix sections append
# blocks to it from parallel worktrees: a block that is not gated cannot be
# run alone (WP29_ONLY=S<NN>), one that is not closed swallows the next,
# and one below the marker runs after the summary has judged the run.

_WP29_TRUTH = os.path.join(_HERE, "test_wp29_truth.cscript")
_W29_OPEN = re.compile(r"^\* ==== (S\d{2}) (.+) ====$")
_W29_CLOSE = re.compile(r"^\* ==== end (S\d{2}) ====$")
_W29_MARK = "* ==== append new blocks above this line ===="


def _wp29_blocks(src):
    """``(blocks, problems)`` for the truth script's text.  A block is
    ``(section, header line, end line)``; a problem names a marker line that
    is not there exactly once, or a block that is not closed by its own end
    line, not gated by its own section, below the marker, or out of section
    order."""
    lines = src.split("\n")
    bad = []
    marks = [n for n, ln in enumerate(lines, 1) if ln.rstrip() == _W29_MARK]
    if len(marks) != 1:
        bad.append("the line %r appears %d times" % (_W29_MARK, len(marks)))
    mark = marks[0] if marks else len(lines) + 1
    blocks, cur = [], None
    for n, ln in enumerate(lines, 1):
        o, c = _W29_OPEN.match(ln.rstrip()), _W29_CLOSE.match(ln.rstrip())
        if o:
            if cur:
                bad.append("%s (line %d) is not closed before line %d"
                           % (cur[0], cur[1], n))
            cur = (o.group(1), n)
        elif c:
            if cur is None or c.group(1) != cur[0]:
                bad.append("line %d closes %s, which is not the open block"
                           % (n, c.group(1)))
            else:
                blocks.append((cur[0], cur[1], n))
            cur = None
    if cur:
        bad.append("%s (line %d) is never closed" % cur)
    for k, (sec, first, last) in enumerate(blocks):
        code = [ln.strip() for ln in lines[first:last - 1] if ln.strip()]
        if code[:2] != ["local only : env WP29_ONLY",
                        'if inlist("`only\'", "", "%s") {' % sec]:
            bad.append("%s (line %d) is not gated by WP29_ONLY=%s"
                       % (sec, first, sec))
        if last > mark:
            bad.append("%s (line %d) is below the marker" % (sec, first))
        if k and sec < blocks[k - 1][0]:
            bad.append("%s (line %d) follows %s: blocks go in section order"
                       % (sec, first, blocks[k - 1][0]))
    return blocks, bad


class TestTheWp29TruthScript:
    """The scaffold section 01 writes, and every block a later section
    appends to it."""

    def test_the_scaffold_is_in_order(self):
        text = _read(_WP29_TRUTH)
        # Flipped (WP-36 plat:PT-1, M8): no Python skip gate.
        order = ['cscript "WP-29 truth', 
                 'do "cert_helpers.do"', 'do "cert_svg.do"', "* ==== S01 ",
                 "local only : env WP29_ONLY", "* ==== end S01 ====",
                 _W29_MARK, "test_wp29_truth: ALL CHECKS PASSED"]
        positions = [text.find(s) for s in order]
        assert -1 not in positions, dict(zip(order, positions))
        assert positions == sorted(positions), (order, positions)
        assert "capture python:" not in text

    def test_every_block_is_gated_closed_and_in_section_order(self):
        blocks, bad = _wp29_blocks(_read(_WP29_TRUTH))
        assert not bad, "\n".join(bad)
        assert blocks and blocks[0][0] == "S01", blocks

    def test_the_block_reader(self):
        good = ('cscript "x"\n'
                "* ==== S01 scaffold ====\nlocal only : env WP29_ONLY\n"
                'if inlist("`only\'", "", "S01") {\n}\n'
                "* ==== end S01 ====\n"
                "* ==== S10 P0.5: axis(2) ====\nlocal only : env WP29_ONLY\n"
                'if inlist("`only\'", "", "S10") {\n}\n'
                "* ==== end S10 ====\n" + _W29_MARK + "\nexit 9\n")
        blocks, bad = _wp29_blocks(good)
        assert bad == [], bad
        assert blocks == [("S01", 2, 6), ("S10", 7, 11)], blocks
        moved = good.replace(_W29_MARK + "\n", "")
        for text, says in (
                (good.replace('"S10") {', '"S01") {'), "not gated"),
                (good.replace("* ==== end S10 ====\n", ""), "never closed"),
                (good.replace("* ==== end S01 ====\n", ""),
                 "not closed before"),
                (good.replace("S10", "S00"), "section order"),
                (moved, "appears 0 times"),
                (moved.replace('cscript "x"\n',
                               'cscript "x"\n' + _W29_MARK + "\n"),
                 "below the marker")):
            _blocks, bad = _wp29_blocks(text)
            assert any(says in b for b in bad), (says, bad)


# ---------------------------------------------------------------------------
# WP-30's truth script: one block per section, gated, timed, closed, in order
# ---------------------------------------------------------------------------
# test/test_wp30_truth.cscript is WP-30's one new certification script
# (.ultraplan/wp30/index.md A142, merge rule R1).  Section 01 writes a stub
# block for every fix section (S02-S57) and each fills its own from a
# parallel worktree: a block that is not gated cannot be run alone
# (WP30_ONLY=S<NN>), one that is not closed swallows the next, one below the
# marker runs after the summary has judged the run, and one that does not
# print its start and end lines first and last cannot be timed (S58.7).

_WP30_TRUTH = os.path.join(_HERE, "test_wp30_truth.cscript")
_W30_OPEN = re.compile(r"^\* ==== (S\d{2}) (.+) ====$")
_W30_CLOSE = re.compile(r"^\* ==== end (S\d{2}) ====$")
_W30_MARK = "* ==== append new blocks above this line ===="
_W30_HEAD = re.compile(r"^(scaffold|P1\.\d{1,2}[abc]?): \S")


def _wp30_blocks(src):
    """``(blocks, problems)`` for the truth script's text.  A block is
    ``(section, header line, end line)``; a problem names a marker line that
    is not there exactly once, a block that is not closed by its own end
    line, not headed by an entry id, not gated by its own section, not timed
    by its own start and end lines, below the marker or out of section
    order, or a section whose blocks name two entries."""
    lines = src.split("\n")
    bad = []
    marks = [n for n, ln in enumerate(lines, 1) if ln.rstrip() == _W30_MARK]
    if len(marks) != 1:
        bad.append("the line %r appears %d times" % (_W30_MARK, len(marks)))
    mark = marks[0] if marks else len(lines) + 1
    blocks, heads, cur = [], {}, None
    for n, ln in enumerate(lines, 1):
        o, c = _W30_OPEN.match(ln.rstrip()), _W30_CLOSE.match(ln.rstrip())
        if o:
            if cur:
                bad.append("%s (line %d) is not closed before line %d"
                           % (cur[0], cur[1], n))
            cur = (o.group(1), n, o.group(2))
        elif c:
            if cur is None or c.group(1) != cur[0]:
                bad.append("line %d closes %s, which is not the open block"
                           % (n, c.group(1)))
            else:
                blocks.append((cur[0], cur[1], n))
                head = _W30_HEAD.match(cur[2])
                if not head:
                    bad.append("%s (line %d) names no entry ('P1.<n>: <what>')"
                               % (cur[0], cur[1]))
                else:
                    heads.setdefault(cur[0], set()).add(head.group(1))
            cur = None
    if cur:
        bad.append("%s (line %d) is never closed" % cur[:2])
    for k, (sec, first, last) in enumerate(blocks):
        code = [ln.strip() for ln in lines[first:last - 1]
                if ln.strip() and not ln.strip().startswith(("//", "*"))]
        if code[:2] != ["local only : env WP30_ONLY",
                        'if inlist("`only\'", "", "%s") & `: list posof '
                        '"%s" in w30_run\' {' % (sec, sec)]:
            bad.append("%s (line %d) is not gated by WP30_ONLY=%s"
                       % (sec, first, sec))
        timed = ['display as text "%s %s " c(current_date) " " '
                 'c(current_time)' % (sec, w) for w in ("start", "end")]
        if code[2:3] != timed[:1] or code[-2:] != [timed[1], "}"]:
            bad.append("%s (line %d) does not print its start line first and "
                       "its end line last" % (sec, first))
        if last > mark:
            bad.append("%s (line %d) is below the marker" % (sec, first))
        if k and sec < blocks[k - 1][0]:
            bad.append("%s (line %d) follows %s: blocks go in section order"
                       % (sec, first, blocks[k - 1][0]))
    for sec, ids in sorted(heads.items()):
        if len(ids) > 1:
            bad.append("%s's blocks name %d entries: %s"
                       % (sec, len(ids), sorted(ids)))
    return blocks, bad


class TestTheWp30TruthScript:
    """The scaffold section 01 writes, and every block a later section
    fills or adds."""

    def test_the_scaffold_is_in_order(self):
        text = _read(_WP30_TRUTH)
        # Flipped (WP-36 plat:PT-1, M8): no Python skip gate.
        order = ['cscript "WP-30 truth', 
                 'do "cert_helpers.do"', 'do "cert_svg.do"',
                 "// ---- parts: begin", "local w30_sh : environment "
                 "DASH_CERT_SHARD", "// ---- parts: end", "* ==== S01 ",
                 "local only : env WP30_ONLY", "* ==== end S01 ====",
                 "* ==== S02 ", "* ==== end S57 ====", _W30_MARK,
                 "test_wp30_truth: ALL CHECKS PASSED"]
        positions = [text.find(s) for s in order]
        assert -1 not in positions, dict(zip(order, positions))
        assert positions == sorted(positions), (order, positions)
        assert "capture python:" not in text

    def test_every_block_is_gated_timed_closed_and_in_section_order(self):
        blocks, bad = _wp30_blocks(_read(_WP30_TRUTH))
        assert not bad, "\n".join(bad)
        assert sorted({b[0] for b in blocks}) == [
            "S%02d" % n for n in range(1, 58)], blocks
        assert blocks[0][0] == "S01", blocks

    def test_the_block_reader(self):
        def block(sec, head, body=""):
            return ("* ==== %s %s ====\nlocal only : env WP30_ONLY\n"
                    'if inlist("`only\'", "", "%s") & `: list posof "%s" '
                    'in w30_run\' {\n'
                    '    display as text "%s start " c(current_date) " " '
                    "c(current_time)\n%s"
                    '    display as text "%s end " c(current_date) " " '
                    "c(current_time)\n}\n* ==== end %s ====\n"
                    % (sec, head, sec, sec, sec, body, sec, sec))
        good = ('cscript "x"\n' + block("S01", "scaffold: smoke",
                                        "    // a case\n")
                + "\n" + block("S10", "P1.19: abbreviations")
                + _W30_MARK + "\nexit 9\n")
        blocks, bad = _wp30_blocks(good)
        assert bad == [], bad
        assert blocks == [("S01", 2, 9), ("S10", 11, 17)], blocks
        moved = good.replace(_W30_MARK + "\n", "")
        second = block("S10", "P1.20a: more")
        for text, says in (
                (good.replace('"S10") &', '"S01") &'), "not gated"),
                (good.replace('"S10" in w30_run', '"S01" in w30_run'),
                 "not gated"),
                (good.replace("* ==== end S10 ====\n", ""), "never closed"),
                (good.replace("* ==== end S01 ====\n", ""),
                 "not closed before"),
                (good.replace("S10", "S00"), "section order"),
                (moved, "appears 0 times"),
                (moved.replace('cscript "x"\n',
                               'cscript "x"\n' + _W30_MARK + "\n"),
                 "below the marker"),
                (good.replace('"S10 end "', '"S10 stop "'),
                 "does not print its start line first"),
                (good.replace("S10 P1.19: abbreviations", "S10 abbreviations"),
                 "names no entry"),
                (good.replace(_W30_MARK, second + _W30_MARK),
                 "blocks name 2 entries")):
            _blocks, bad = _wp30_blocks(text)
            assert any(says in b for b in bad), (says, bad)


# ---------------------------------------------------------------------------
# WP-31's truth script: S01's scaffold and the blocks sections append
# ---------------------------------------------------------------------------

_WP31_TRUTH = os.path.join(_HERE, "test_wp31_truth.cscript")
_W31_OPEN = re.compile(r"^\* ==== (S\d{2}) (.+) ====$")
_W31_CLOSE = re.compile(r"^\* ==== end (S\d{2}) ====$")
_W31_MARK = "* ==== append new blocks above this line ===="
_W31_HEAD = re.compile(r"^(scaffold|[A-K]\d{1,2}[a-gkltx]?): \S")


_W_MARK = "* ==== append new blocks above this line ===="
# A row a ruling split off another takes a letter (D42: syn:SD-20a .. e;
# D44: BY-24a).
_W_GAPS4_ID = r"(?:(?:plot|basic|stat|plat|syn|sil):)?[A-Z]{2,3}-\d{1,2}[a-z]?"
_W_HEAD = re.compile(r"^(scaffold|tool|%s): \S" % _W_GAPS4_ID)


def _wp_blocks(src, wp, head=_W_HEAD, row="GAPS4 row"):
    """(blocks, bad) of WP-<wp>'s truth script: one marker; each block
    `* ==== S<MM> <head> ====` .. `* ==== end S<MM> ====` above it, gated by
    WP<wp>_ONLY and w<wp>_run, printing its start line first and its end
    line last, in non-decreasing section order.  blocks are (S<MM>, first
    line, last line, header text)."""
    lines = src.split("\n")
    bad = []
    marks = [n for n, ln in enumerate(lines, 1) if ln.rstrip() == _W_MARK]
    if len(marks) != 1:
        bad.append("the line %r appears %d times" % (_W_MARK, len(marks)))
    mark = marks[0] if marks else len(lines) + 1
    blocks, cur = [], None
    for n, ln in enumerate(lines, 1):
        o, c = _W31_OPEN.match(ln.rstrip()), _W31_CLOSE.match(ln.rstrip())
        if o:
            if cur:
                bad.append("%s (line %d) is not closed before line %d"
                           % (cur[0], cur[1], n))
            cur = (o.group(1), n, o.group(2))
        elif c:
            if cur is None or c.group(1) != cur[0]:
                bad.append("line %d closes %s, which is not the open block"
                           % (n, c.group(1)))
            else:
                blocks.append((cur[0], cur[1], n, cur[2]))
                if not head.match(cur[2]):
                    bad.append("%s (line %d) names no %s ('<id>: <what>')"
                               % (cur[0], cur[1], row))
            cur = None
    if cur:
        bad.append("%s (line %d) is never closed" % cur[:2])
    for k, (sec, first, last, _h) in enumerate(blocks):
        code = [ln.strip() for ln in lines[first:last - 1]
                if ln.strip() and not ln.strip().startswith(("//", "*"))]
        if code[:2] != ["local only : env WP%s_ONLY" % wp,
                        'if inlist("`only\'", "", "%s") & `: list posof '
                        '"%s" in w%s_run\' {' % (sec, sec, wp)]:
            bad.append("%s (line %d) is not gated by WP%s_ONLY=%s"
                       % (sec, first, wp, sec))
        timed = ['display as text "%s %s " c(current_date) " " '
                 'c(current_time)' % (sec, w) for w in ("start", "end")]
        if code[2:3] != timed[:1] or code[-2:] != [timed[1], "}"]:
            bad.append("%s (line %d) does not print its start line first and "
                       "its end line last" % (sec, first))
        if last > mark:
            bad.append("%s (line %d) is below the marker" % (sec, first))
        if k and sec < blocks[k - 1][0]:
            bad.append("%s (line %d) follows %s: blocks go in section order"
                       % (sec, first, blocks[k - 1][0]))
    return blocks, bad


def _wp31_blocks(src):
    """WP-31's reader: _wp_blocks with its GAPS3 head; blocks as
    (S<NN>, first line, last line)."""
    blocks, bad = _wp_blocks(src, "31", head=_W31_HEAD, row="GAPS3 row")
    return [b[:3] for b in blocks], bad


class TestTheWp31TruthScript:

    def test_the_scaffold_is_in_order(self):
        text = _read(_WP31_TRUTH)
        # Flipped (WP-36 plat:PT-1, M8): no Python skip gate.
        order = ['cscript "WP-31 truth', 
                 'do "cert_helpers.do"', 'do "cert_svg.do"',
                 "// ---- parts: begin", "local w31_sh : environment "
                 "DASH_CERT_SHARD", "// ---- parts: end", "* ==== S01 ",
                 "local only : env WP31_ONLY", "* ==== end S01 ====",
                 _W31_MARK, "has no block to run",
                 "test_wp31_truth: ALL CHECKS PASSED"]
        positions = [text.find(s) for s in order]
        assert -1 not in positions, dict(zip(order, positions))
        assert positions == sorted(positions), (order, positions)
        assert "capture python:" not in text

    def test_every_block_is_gated_timed_closed_and_in_section_order(self):
        blocks, bad = _wp31_blocks(_read(_WP31_TRUTH))
        assert not bad, "\n".join(bad)
        assert blocks and blocks[0][0] == "S01", blocks

    def test_the_block_reader(self):
        def block(sec, head, body=""):
            return ("* ==== %s %s ====\nlocal only : env WP31_ONLY\n"
                    'if inlist("`only\'", "", "%s") & `: list posof "%s" '
                    'in w31_run\' {\n'
                    '    display as text "%s start " c(current_date) " " '
                    "c(current_time)\n%s"
                    '    display as text "%s end " c(current_date) " " '
                    "c(current_time)\n}\n* ==== end %s ====\n"
                    % (sec, head, sec, sec, sec, body, sec, sec))
        good = ('cscript "x"\n' + block("S01", "scaffold: smoke", "    // a\n")
                + "\n" + block("S14", "C6: cmissing") + "\n"
                + block("S14", "C7: recast") + _W31_MARK + "\nexit 9\n")
        blocks, bad = _wp31_blocks(good)
        assert bad == [], bad
        assert [b[0] for b in blocks] == ["S01", "S14", "S14"], blocks
        for text, says in (
                (good.replace('"S14") &', '"S01") &'), "not gated"),
                (good.replace("* ==== end S14 ====\n", "", 1), "not closed"),
                (good.replace("C7: recast", "nothing"), "names no GAPS3 row"),
                (good.replace("S14", "S00"), "section order"),
                (good.replace(_W31_MARK + "\n", ""), "appears 0 times")):
            assert any(says in b for b in _wp31_blocks(text)[1]), (says,)


# ---------------------------------------------------------------------------
# The per-WP truth scripts of WP-33..WP-49 (index.md PD-6): one template,
# one block reader
# ---------------------------------------------------------------------------

_WP_TEMPLATE = os.path.join(_HERE, "templates", "wp_truth_template.cscript")
_WP_TRUTHS = sorted(
    p for p in glob.glob(os.path.join(_HERE, "test_wp*_truth.cscript"))
    if re.search(r"test_wp(3[3-9]|4[0-9])_truth\.cscript$", p))
# The seconds statement and its /// continuation lines: the one statement
# of a WP script's frame a later commit may rewrite (measured block costs).
_SECS = re.compile(r"^local w\d\d_secs[^\n]*(?:\n    [^\n]*)*\n", re.M)


def _wp_of(path):
    return re.search(r"test_wp(\d{2})_truth\.cscript$", path).group(1)


def _head_and_tail(text):
    """The frame of a WP truth script: everything through S00's end line
    (less the seconds statement) and everything from the marker on."""
    i = text.index("* ==== end S00 ====\n") + len("* ==== end S00 ====\n")
    j = text.index(_W_MARK)
    return _SECS.sub("", text[:i], count=1), text[j:]


class TestTheWpTruthScripts:

    def test_the_template_and_the_wp33_script_exist(self):
        assert os.path.isfile(_WP_TEMPLATE), _WP_TEMPLATE
        assert "test_wp33_truth.cscript" in [
            os.path.basename(p) for p in _WP_TRUTHS], _WP_TRUTHS

    @pytest.mark.parametrize("path", _WP_TRUTHS, ids=os.path.basename)
    def test_the_scaffold_is_in_order(self, path):
        wp = _wp_of(path)
        text = _read(path)
        # Flipped (WP-36 plat:PT-1, M8): no Python skip gate.
        order = ['cscript "WP-%s truth' % wp, 
                 'do "cert_helpers.do"', 'do "cert_svg.do"',
                 "// ---- parts: begin",
                 "local w%s_sh : environment DASH_CERT_SHARD" % wp,
                 "// ---- parts: end", "* ==== S00 ",
                 "local only : env WP%s_ONLY" % wp, "* ==== end S00 ====",
                 _W_MARK, "has no block to run",
                 "test_wp%s_truth: ALL CHECKS PASSED" % wp]
        positions = [text.find(s) for s in order]
        assert -1 not in positions, dict(zip(order, positions))
        assert positions == sorted(positions), (order, positions)
        assert "capture python:" not in text

    @pytest.mark.parametrize("path", _WP_TRUTHS, ids=os.path.basename)
    def test_every_block_is_gated_timed_closed_and_in_section_order(
            self, path):
        blocks, bad = _wp_blocks(_read(path), _wp_of(path))
        assert not bad, "\n".join(bad)
        assert blocks and blocks[0][0] == "S00", blocks
        assert blocks[0][3].startswith("scaffold: "), blocks[0]

    @pytest.mark.parametrize("path", _WP_TRUTHS, ids=os.path.basename)
    def test_each_block_names_a_row_of_its_own_section(self, path):
        sys.path.insert(0, _HERE)
        import test_tracking_documents as T
        wp = _wp_of(path)
        blocks, _bad = _wp_blocks(_read(path), wp)
        bad = []
        for sec, first, _last, head in blocks:
            m = re.match(r"^(%s): " % _W_GAPS4_ID, head)
            if not m:
                continue
            pid = m.group(1)
            if (T.GAPS4_WP.get(pid) != "WP-" + wp
                    or T.GAPS4_SECTION.get(pid) != "%s-%s" % (wp, sec[1:])):
                bad.append("%s (line %d) names %s, a row of %s section %s"
                           % (sec, first, pid, T.GAPS4_WP.get(pid),
                              T.GAPS4_SECTION.get(pid)))
        assert not bad, "\n".join(bad)

    def test_the_template_makes_a_clean_script(self):
        t = _read(_WP_TEMPLATE)
        assert t.count("@@WP@@") >= 100
        for left in ("WP-31", "w31", "U01-1", "GAPS3"):
            assert left not in t, left
        blocks, bad = _wp_blocks(t.replace("@@WP@@", "47"), "47")
        assert bad == [], bad
        assert [b[0] for b in blocks] == ["S00"], blocks

    @pytest.mark.parametrize("path", _WP_TRUTHS, ids=os.path.basename)
    def test_every_script_keeps_the_templates_head_and_tail(self, path):
        # Sections append only between the S00 block and the marker, and a
        # WP's W0 must not edit the frame.
        made = _read(_WP_TEMPLATE).replace("@@WP@@", _wp_of(path))
        assert _head_and_tail(_read(path)) == _head_and_tail(made)

    def test_the_block_reader(self):
        def block(sec, head, body=""):
            return ("* ==== %s %s ====\nlocal only : env WP47_ONLY\n"
                    'if inlist("`only\'", "", "%s") & `: list posof "%s" '
                    'in w47_run\' {\n'
                    '    display as text "%s start " c(current_date) " " '
                    "c(current_time)\n%s"
                    '    display as text "%s end " c(current_date) " " '
                    "c(current_time)\n}\n* ==== end %s ====\n"
                    % (sec, head, sec, sec, sec, body, sec, sec))
        good = ('cscript "x"\n' + block("S00", "scaffold: smoke")
                + block("S02", "AX-4: ticks")
                + block("S02", "plat:PT-1: python")
                + block("S09", "tool: guard") + _W_MARK + "\n")
        blocks, bad = _wp_blocks(good, "47")
        assert bad == [], bad
        assert [b[0] for b in blocks] == ["S00", "S02", "S02", "S09"], blocks
        swapped = good.replace(block("S09", "tool: guard"),
                               block("S09", "tool: guard")
                               + block("S01", "tool: late"))
        for text, wp, says in (
                (good.replace('"S00") &', '"S01") &'), "47", "not gated"),
                (good.replace("AX-4: ticks", "nothing"), "47",
                 "names no GAPS4 row"),
                (swapped, "47", "section order"),
                (good.replace(_W_MARK + "\n", ""), "47", "appears 0 times"),
                (good, "48", "not gated")):
            assert any(says in b for b in _wp_blocks(text, wp)[1]), (says,)

    def test_the_seconds_table_may_change(self):
        t = _read(_WP_TEMPLATE).replace("@@WP@@", "47")
        u = t.replace("local w47_secs S00 1\n",
                      "local w47_secs ///\n    S00 1 S09 150 ///\n"
                      "    S10 300\n")
        assert u != t
        assert _head_and_tail(u) == _head_and_tail(t)
        # WP-36 plat:PT-1: the template's head no longer holds a skip gate.
        u2 = t.replace('do "cert_helpers.do"', 'do "x.do"')
        assert _head_and_tail(u2) != _head_and_tail(t)
        assert len(_SECS.findall(t)) == 1
