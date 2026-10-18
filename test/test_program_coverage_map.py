"""test_program_coverage_map.py -- every Stata program and Mata function dash
ships has a test, and the list saying so cannot rot (WP-24 AC-24.3).

test/program_coverage_map.py names, for every ``program define`` in dash.ado
and dash_setup.ado and every function in dash_parse.mata, the certification
cases that exercise it.  This file holds that map to the sources:

* a program or function added without an entry fails, and so does an entry
  whose unit is gone;
* every reference must name a case its script really shows as
  ``"<id> PASS"`` (itself or through the helper that closes its cases), or
  a script that names the unit, so an entry cannot point at nothing, and
  every unit has one;
* every Mata function dash.ado calls is in the list _dash_require_mata
  checks after it reloads the library.  _dash_path_badchar was not, so a
  library without it passed and the first saving() ended in r(3499)
  (test_program_coverage.cscript PC-30).

The sources are parsed here on their own, and the parse is held to
scripts/measure_stata_coverage.py's, which instruments the same units: two
readings that must agree.
"""
import importlib.util
import os
import re
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)

import program_coverage_map as pcm  # noqa: E402

_ADO_FILES = ("dash.ado", "dash_setup.ado")
_MATA_FILES = ("dash_parse.mata",)
_SOURCES = _ADO_FILES + _MATA_FILES


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# Reading Stata and Mata source
# ---------------------------------------------------------------------------

def _code_lines(text):
    """``[(number, code)]`` with comments removed: ``*`` and ``//`` comment
    lines, ``/* */`` blocks, and a ``//`` tail that follows a blank (a URL's
    ``//`` follows a colon and is kept).  A ``///`` continuation is kept for
    _logical_lines to join on."""
    out = []
    in_block = False
    for n, line in enumerate(text.split("\n"), 1):
        code = line
        if in_block:
            if "*/" not in code:
                continue
            code = code.split("*/", 1)[1]
            in_block = False
        while "/*" in code:
            head, tail = code.split("/*", 1)
            if "*/" in tail:
                code = head + tail.split("*/", 1)[1]
            else:
                code = head
                in_block = True
        stripped = code.lstrip()
        if stripped.startswith("*") or (stripped.startswith("//")
                                        and not stripped.startswith("///")):
            continue
        m = re.search(r"(^|\s)//(?!/)", code)
        if m:
            code = code[:m.start()]
        if code.strip():
            out.append((n, code))
    return out


def _logical_lines(text):
    """Code lines with ``///`` continuations joined, as Stata joins them."""
    out, buf, start = [], "", None
    for n, code in _code_lines(text):
        m = re.search(r"(^|\s)///", code)
        cont = m is not None
        if cont:
            code = code[:m.start()]
        if start is None:
            start = n
        buf += " " + code.strip()
        if not cont:
            out.append((start, buf.strip()))
            buf, start = "", None
    if buf.strip():
        out.append((start, buf.strip()))
    return out


_PROGRAM = re.compile(r"^\s*program\s+(?:define\s+)?([A-Za-z_]\w*)")
_MATA_FUNC = re.compile(
    r"^(?:real|string|void|transmorphic|pointer|numeric|complex|matrix|"
    r"struct|class)\b[^(=;]*?\b([A-Za-z_]\w*)\s*\(")


def _ado_programs(text):
    """``{name: (first line, last line)}`` of every program defined."""
    lines = text.split("\n")
    code = dict(_code_lines(text))
    out = {}
    for n in sorted(code):
        m = _PROGRAM.match(code[n])
        if not m or m.group(1) in ("drop", "dir", "list"):
            continue
        end = n
        while end < len(lines) and not re.match(r"^end\s*$", lines[end - 1]):
            end += 1
        out[m.group(1)] = (n, end)
    return out


def _mata_functions(text):
    """``{name: (first line, last line)}`` of every Mata function: from its
    signature to the closing brace at the start of a line."""
    lines = text.split("\n")
    out = {}
    for i, line in enumerate(lines):
        m = _MATA_FUNC.match(line)
        if not m:
            continue
        end = i
        while end < len(lines) and not re.match(r"^\}\s*$", lines[end]):
            end += 1
        out[m.group(1)] = (i + 1, end + 1)
    return out


def _units(path):
    text = _read(path)
    if path.endswith(".mata"):
        return _mata_functions(text)
    return _ado_programs(text)


@pytest.fixture(scope="module")
def units():
    return {f: _units(os.path.join(_ROOT, f)) for f in _SOURCES}


# ---------------------------------------------------------------------------
# Reading certification scripts
# ---------------------------------------------------------------------------

_DISPLAY = r"\bdi(?:s(?:p(?:l(?:a(?:y)?)?)?)?)?\b"
_REF = re.compile(r"^(test_[A-Za-z0-9_]+\.cscript)(?::([A-Z][A-Z0-9]*-\d+[a-z]?))?$")


def _shows_case(text, case_id):
    """True when the script shows ``<case_id> PASS``: a display whose string
    starts with the id, or a helper call whose first argument is the id in
    a script whose helper displays `` `id' PASS``."""
    lines = [c for _n, c in _code_lines(text)]
    literal = re.compile(_DISPLAY + r"[^\n]*?`?\"" + re.escape(case_id)
                         + r"(?: PASS|[ \t])")
    if any(literal.search(c) for c in lines):
        return True
    helper_display = re.compile(_DISPLAY + r"[^\n]*?`?\"`[A-Za-z_]\w*' PASS")
    if not any(helper_display.search(c) for c in lines):
        return False
    as_argument = re.compile(
        r"^\s*(?:(?:capture|cap|noisily|noi|quietly|qui)\s+)*[A-Za-z_]\w*\s+"
        r"\"?" + re.escape(case_id) + r"\"?(?:\s|$)")
    return any(as_argument.search(c) for c in lines)


def _names_in_code(text, name):
    word = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(name)
                      + r"(?![A-Za-z0-9_])")
    return any(word.search(c) for _n, c in _code_lines(text))


@pytest.fixture(scope="module")
def scripts():
    cache = {}

    def get(name):
        if name not in cache:
            path = os.path.join(_HERE, name)
            cache[name] = _read(path) if os.path.isfile(path) else None
        return cache[name]
    return get


def _all_refs():
    for f, entries in pcm.COVERAGE.items():
        for unit, refs in entries.items():
            for ref in refs:
                yield f, unit, ref


# ---------------------------------------------------------------------------
# The map covers the sources, both ways
# ---------------------------------------------------------------------------

class TestTheMapCoversEveryUnit:

    def test_the_parse_finds_the_units(self, units):
        """Guards the guard: an empty parse would pass every check below."""
        assert len(units["dash.ado"]) >= 56, sorted(units["dash.ado"])
        assert len(units["dash_setup.ado"]) >= 7
        assert len(units["dash_parse.mata"]) >= 55
        for f, name in (("dash.ado", "dash"), ("dash.ado", "_dash_serve"),
                        ("dash_setup.ado", "dash_setup"),
                        ("dash_parse.mata", "_dash_split_segs"),
                        ("dash_parse.mata", "_dash_spec_types_in")):
            assert name in units[f], (f, name)

    @pytest.mark.parametrize("f", _SOURCES)
    def test_every_unit_has_an_entry(self, units, f):
        missing = sorted(set(units[f]) - set(pcm.COVERAGE.get(f, {})))
        assert not missing, (
            f"{f} defines {missing} and test/program_coverage_map.py has no "
            f"entry for them: name the certification case that exercises "
            f"each (write one if none does).  A unit nothing calls is dead "
            f"code: delete it (test_no_orphans.py)")

    @pytest.mark.parametrize("f", _SOURCES)
    def test_no_entry_names_a_unit_that_is_gone(self, units, f):
        stale = sorted(set(pcm.COVERAGE.get(f, {})) - set(units[f]))
        assert not stale, (
            f"test/program_coverage_map.py lists {stale} under {f}, which "
            f"no longer defines them")

    def test_the_map_names_no_other_file(self):
        assert set(pcm.COVERAGE) == set(_SOURCES)

    def test_every_unit_has_a_test(self):
        """No exemption: the uncalled units the map once excused with an
        empty entry (its UNCALLED list) were deleted by WP-26, and
        test_no_orphans.py fails on a unit nothing calls."""
        bare = sorted(u for entries in pcm.COVERAGE.values()
                      for u, refs in entries.items() if not refs)
        assert not bare, f"units with no test reference: {bare}"


# ---------------------------------------------------------------------------
# Every reference names a test that exists
# ---------------------------------------------------------------------------

class TestEveryReferenceIsATest:

    def test_every_reference_is_well_formed(self):
        bad = [(f, u, r) for f, u, r in _all_refs() if not _REF.match(r)]
        assert not bad, f"references that are not script[:CASE-ID]: {bad}"

    def test_every_reference_names_a_script_that_exists(self, scripts):
        bad = sorted({r.split(":")[0] for _f, _u, r in _all_refs()
                      if _REF.match(r) and scripts(r.split(":")[0]) is None})
        assert not bad, f"no such certification script: {bad}"

    def test_every_case_is_shown_by_its_script(self, scripts):
        missing = []
        for f, unit, ref in _all_refs():
            m = _REF.match(ref)
            if not m or m.group(2) is None:
                continue
            text = scripts(m.group(1))
            if text is not None and not _shows_case(text, m.group(2)):
                missing.append(f"{unit}: {ref}")
        assert not missing, (
            "the map names cases their scripts never show as '<id> PASS':\n"
            + "\n".join(missing))

    def test_a_script_named_without_a_case_names_the_unit(self, scripts):
        bad = []
        for f, unit, ref in _all_refs():
            m = _REF.match(ref)
            if not m or m.group(2) is not None:
                continue
            text = scripts(m.group(1))
            if text is not None and not _names_in_code(text, unit):
                bad.append(f"{unit}: {ref}")
        assert not bad, (
            "a script cited without a case id must call the unit by name:\n"
            + "\n".join(bad))

    def test_the_case_detector(self):
        text = "\n".join([
            'display "P9-01 PASS: x"',
            "else display as text `\"P9-13 PASS: y\"'",
            '    else if `d\' display as text "TP-01 PASS `tt\': z"',
            '// display "P7-01 PASS: in a comment"',
            'display "  P19-17..21: a summary line"',
            'local s "P8-01 PASS"',
        ])
        assert _shows_case(text, "P9-01")
        assert _shows_case(text, "P9-13")
        assert _shows_case(text, "TP-01")
        assert not _shows_case(text, "P7-01")
        assert not _shows_case(text, "P19-17")
        assert not _shows_case(text, "P8-01")
        assert not _shows_case(text, "P9-0")
        helper = "\n".join([
            "program define _t",
            "    args id",
            "    display as text `\"`id' PASS: done\"'",
            "end",
            "_t HC6-06 0 \"a thing\"",
            '_t "HC2-37a" 1',
            "// _t HC6-99",
        ])
        assert _shows_case(helper, "HC6-06")
        assert _shows_case(helper, "HC2-37a")
        assert not _shows_case(helper, "HC6-99")
        assert not _shows_case(helper, "HC6-0")
        # An id as an argument is not a case where no helper displays PASS.
        assert not _shows_case("_t HC6-06\n", "HC6-06")


# ---------------------------------------------------------------------------
# _dash_require_mata checks every Mata function dash.ado calls
# ---------------------------------------------------------------------------

def _needed_and_called():
    ado = _read(os.path.join(_ROOT, "dash.ado"))
    funcs = set(_mata_functions(_read(os.path.join(_ROOT, "dash_parse.mata"))))
    needed = None
    called = set()
    for _n, code in _logical_lines(ado):
        m = re.match(r"^local\s+_needed\s+(.*)$", code)
        if m:
            needed = set(m.group(1).split())
        if "mata" not in code:
            continue
        for f in funcs:
            if re.search(r"(?<![A-Za-z0-9_])" + re.escape(f) + r"\s*\(", code):
                called.add(f)
    return needed, called, funcs


class TestTheMataLibraryCheckNamesEveryFunctionDashCalls:

    def test_the_list_is_found(self):
        needed, called, _funcs = _needed_and_called()
        assert needed and len(needed) >= 20, needed
        assert len(called) >= 20, called

    def test_every_function_dash_ado_calls_is_checked(self):
        needed, called, _funcs = _needed_and_called()
        missing = sorted(called - needed)
        assert not missing, (
            f"dash.ado calls {missing} but _dash_require_mata's _needed list "
            f"does not name them: a library that compiled without one passes "
            f"the check, and the call later fails with r(3499) naming an "
            f"internal function (test_program_coverage.cscript PC-30)")

    def test_the_list_names_only_functions_that_exist(self):
        needed, _called, funcs = _needed_and_called()
        assert not sorted(needed - funcs), sorted(needed - funcs)

    def test_the_list_names_only_functions_dash_ado_calls(self):
        needed, called, _funcs = _needed_and_called()
        assert not sorted(needed - called), sorted(needed - called)

    def test_the_repair_drops_every_function_the_library_defines(self):
        """The repair drops what is in memory before it reloads the file: a
        function already defined stops `run' at its definition, r(3000), so
        over a library loaded in part the reload would define nothing it
        lacks (test_env_guards.cscript ENV-23).  It drops ``_dash_*()``,
        which covers every function the library defines.

        Flipped: this read a hand list of the library's other names, which
        had to be exactly those; WP-31 H7 renamed the four (_json_escape,
        _is_utf8, _expand_plottype_str, _first_comma_pos) with the prefix,
        so there are none, and the list is gone."""
        ado = _read(os.path.join(_ROOT, "dash.ado"))
        funcs = set(_mata_functions(
            _read(os.path.join(_ROOT, "dash_parse.mata"))))
        wild = any(re.search(r"\bmata\s+drop\s+_dash_\*\(\)", code)
                   for _n, code in _logical_lines(ado))
        assert wild, "the repair no longer drops _dash_*() before it reloads"
        assert funcs
        others = sorted(f for f in funcs if not f.startswith("_dash_"))
        assert not others, (
            "the wildcard drop misses the library's functions %s" % others)


# ---------------------------------------------------------------------------
# The measurement script reads the same units
# ---------------------------------------------------------------------------

def _measure_module():
    """scripts/measure_stata_coverage.py, loaded without leaving a
    scripts/__pycache__ behind (no .gitignore rule covers it)."""
    path = os.path.join(_ROOT, "scripts", "measure_stata_coverage.py")
    spec = importlib.util.spec_from_file_location("_measure_stata_cov", path)
    mod = importlib.util.module_from_spec(spec)
    before = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = before
    return mod


def test_the_measurement_script_finds_the_same_units(units):
    got = {}
    for f, _kind, name, line in _measure_module().inventory(_ROOT):
        got.setdefault(f, {})[name] = line
    for f in _SOURCES:
        assert set(got.get(f, {})) == set(units[f]), f
        assert all(got[f][u] == units[f][u][0] for u in units[f]), f


def test_continuations_are_joined_and_comments_dropped():
    text = "\n".join([
        "local _needed a b ///",
        "    c d   // a trailing comment",
        "* a comment line",
        "display \"http://x\" /* inline */ // tail",
        "local e f",
    ])
    assert _logical_lines(text) == [(1, "local _needed a b c d"),
                                    (4, 'display "http://x"'),
                                    (5, "local e f")]


def test_the_parsers_read_definitions_only():
    ado = "\n".join([
        "program define a",
        "    capture program drop b",
        "end",
        "* program define c  (a comment)",
        "/* program define d",
        "   program define e */",
        "program f, rclass",
        "end",
    ])
    assert sorted(_ado_programs(ado)) == ["a", "f"]
    mata = "\n".join([
        "real scalar g(string scalar s) {",
        "    real scalar h",
        "    return(strlen(s))",
        "}",
        "// string scalar i(real scalar x)",
        "void j(string scalar s,",
        "       real scalar n)",
        "{",
        "}",
    ])
    assert _mata_functions(mata) == {"g": (1, 4), "j": (6, 9)}
