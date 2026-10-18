"""test_file_headers.py -- the headers of dash_parse.mata and dash.ado say
what is there (WP-26 TR-26.8, AC-26.2; GAPS.md N1).

dash_parse.mata's header listed _dash_json_esc and _dash_html_esc as its
"Public API (called from dash.ado)", and nothing called either; it named
_dash_pc_immediate and _dash_kpi_fields, which dash.ado does not call, and
left out eight functions dash.ado does call -- _dash_extract_filters,
_dash_extract_qual_vars, _dash_option_names, _dash_path_badchar,
_dash_kpi_pctile, _dash_json_escape, _dash_link_refusal and _dash_qual_expand.
It, and dash.ado's header, said Mata did "option-key abbreviation
expansion", which it has not done since _expand_optkey was removed
(measured 24sep2026 at 480159f).  This holds the rewrite:

* the Public API entries of dash_parse.mata's header -- a line
  ``*!   name(args)`` -- are exactly the functions dash.ado calls, the list
  _dash_require_mata checks, ``_needed`` (test_program_coverage_map.py
  holds that list to the calls dash.ado makes), each once;
* every function either header names exists: in dash_parse.mata's header
  a name with a leading underscore written before "(", in dash.ado's any
  name with a leading underscore (it names no macro);
* neither says again that Mata expands option abbreviations.
"""
import os
import re
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)

import test_program_coverage_map as _units_parse  # noqa: E402


def _read(name, root=None):
    with open(os.path.join(root or _ROOT, name), encoding="utf-8") as fh:
        return fh.read()


def _header(text):
    """The ``*!`` lines a file starts with."""
    out = []
    for line in text.split("\n"):
        if not line.startswith("*!"):
            break
        out.append(line)
    return out


def _public_api(header):
    """The names of the Public API entries: after the line that begins
    ``*! Public API``, each line ``*!   name(`` (three blanks)."""
    starts = [i for i, l in enumerate(header) if l.startswith("*! Public API")]
    if not starts:
        return []
    return [m.group(1) for l in header[starts[0] + 1:]
            for m in [re.match(r"^\*!   ([A-Za-z_][A-Za-z0-9_]*)\(", l)] if m]


def _named_functions(header):
    """Every name with a leading underscore written before "(" in a
    header -- how the header writes a function."""
    return {m.group(1) for l in header for m in re.finditer(
        r"(?<![A-Za-z0-9_`$])(_[A-Za-z][A-Za-z0-9_]*)\(", l)}


def _named(header):
    """Every name with a leading underscore in a header."""
    return {m.group(1) for l in header for m in re.finditer(
        r"(?<![A-Za-z0-9_`$])(_[A-Za-z][A-Za-z0-9_]*)", l)}


def _needed(ado_text):
    """The names of _dash_require_mata's `_needed' list."""
    for _n, code in _units_parse._logical_lines(ado_text):
        m = re.match(r"^local\s+_needed\s+(.*)$", code)
        if m:
            return m.group(1).split()
    return []


@pytest.fixture(scope="module")
def sources():
    return {"mata": _read("dash_parse.mata"), "ado": _read("dash.ado")}


class TestTheMataLibraryHeader:

    def test_the_header_is_read(self, sources):
        """Guards the guard: a header this could not read would pass."""
        header = _header(sources["mata"])
        assert len(header) >= 60, len(header)
        api = _public_api(header)
        assert len(api) >= 20, api
        assert "_dash_split_segs" in api and "_dash_json_escape" in api

    def test_its_public_api_is_the_list_dash_ado_needs(self, sources):
        api = _public_api(_header(sources["mata"]))
        needed = _needed(sources["ado"])
        assert len(needed) >= 20, needed
        assert len(api) == len(set(api)), sorted(
            n for n in set(api) if api.count(n) > 1)
        assert set(api) == set(needed), (
            "dash_parse.mata's Public API is not the list of functions "
            "dash.ado calls (_needed in _dash_require_mata): listed and not "
            "called %s; called and not listed %s" % (
                sorted(set(api) - set(needed)),
                sorted(set(needed) - set(api))))

    def test_it_names_only_functions_that_exist(self, sources):
        header = _header(sources["mata"])
        funcs = set(_units_parse._mata_functions(sources["mata"]))
        programs = set(_units_parse._ado_programs(sources["ado"]))
        assert set(_public_api(header)) <= funcs, sorted(
            set(_public_api(header)) - funcs)
        gone = sorted(_named_functions(header) - funcs - programs)
        assert not gone, (
            "dash_parse.mata's header names functions that are not "
            "there: %s" % gone)


class TestTheAdoHeader:

    def test_it_names_only_what_exists(self, sources):
        header = _header(sources["ado"])
        assert len(header) >= 15, header
        names = _named(header)
        assert names, "dash.ado's header names no program or function"
        units = (set(_units_parse._mata_functions(sources["mata"]))
                 | set(_units_parse._ado_programs(sources["ado"])))
        assert not sorted(names - units), sorted(names - units)


@pytest.mark.parametrize("name", ["dash_parse.mata", "dash.ado"])
def test_no_header_says_mata_expands_option_abbreviations(name):
    """GAPS.md N1: both headers said it, years after the code went."""
    text = "\n".join(_header(_read(name)))
    assert text, name
    assert not re.search(r"abbreviation\s+expansion", text, re.I), name
    assert "Mata handles ONLY" not in text, name


class TestTheReadersSeeADivergence:
    """The checks above fail when the header and `_needed' part."""

    _HEADER = [
        "*! lib.mata",
        "*! Public API: the functions dash.ado calls.",
        "*!",
        "*!   _dash_a(s)",
        "*!       Calls _dash_c() for its work.",
        "*!",
        "*!   _dash_b(x, y)",
        "*!       A description, and _dash_d in words.",
        "*! Version: 1",
    ]

    def test_the_entries_are_read(self):
        assert _public_api(self._HEADER) == ["_dash_a", "_dash_b"]
        assert _named_functions(self._HEADER) == {"_dash_a", "_dash_b",
                                                  "_dash_c"}
        assert _named(self._HEADER) == {"_dash_a", "_dash_b", "_dash_c",
                                        "_dash_d"}
        assert _header("*! a\n*! b\n\n*! c") == ["*! a", "*! b"]

    def test_a_needed_list_is_read_across_continuations(self):
        ado = "\n".join(["program define x",
                         "    local _needed _dash_a ///",
                         "        _dash_b",
                         "end"])
        assert _needed(ado) == ["_dash_a", "_dash_b"]
