"""No plot-type family in dash.ado may sit at an argument ceiling (WP-22 TR-22.4).

``_dash_process_segment`` routed each plot type to its varlist parser and its
JSON encoder with string ``inlist()`` tests, ten of them, and the range test
was

    inlist("`ptype'", "rarea", "rbar", "rspike", "rcap", "rline",
                      "rconnected", "rcapsym", "rscatter", "tsrline")

-- ptype and nine literals, which is exactly Stata's limit for a string
``inlist()``.  Measured 23sep2026 with the console binary: ptype and nine
literals is rc 0; ptype and ten is r(130) "expression too long".  So a tenth
range type could not be added without the command failing to run at all.

The fix names each family once, as a word list in
``_dash_plottype_families``, and tests membership with ``: list ptype in``,
which has no argument limit.  This file holds dash.ado to that:

* no string ``inlist()`` tests a plot type (the ten that did are gone);
* no string ``inlist()`` anywhere in dash.ado is within one argument of the
  ceiling, so no other list can be one addition away from the same failure;
* each family is defined exactly once, and the families are the renderer's
  own categories (``_DASH_RANGE_TYPES``, ``_DASH_PC_TYPES``,
  ``_DASH_LITERAL_TYPES``, ``_DASH_UNIVARIATE_TYPES``), so the Stata side
  and the Python side cannot disagree about which type is which;
* every family member is a plot type dash draws.

That the lists route every type, and that a tenth member is found by
``: list ... in`` where ``inlist()`` of the same membership is r(130), is
proved in Stata by test_parser.cscript P1A-56.
"""
import os
import re
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402

_ADO = os.path.join(_HERE, "..", "dash.ado")

#: Stata's argument limit for a string inlist(): the value and nine
#: literals is rc 0, ten literals is r(130) (measured 23sep2026).
_STRING_INLIST_MAX_ARGS = 10

#: Macros that hold a plot type in dash.ado.
_PLOT_TYPE_MACROS = ("ptype", "plottype", "pt", "_ptype", "_pt_exp")


def _ado_code_lines():
    """dash.ado with each ``//`` comment and ``*`` comment line removed and
    ``///`` continuations joined, as ``(first line number, statement)``."""
    with open(_ADO, encoding="utf-8") as fh:
        raw = fh.read().splitlines()
    out, i = [], 0
    while i < len(raw):
        line = raw[i]
        start = i + 1
        stripped = line.lstrip()
        if stripped.startswith("*") or stripped.startswith("//"):
            i += 1
            continue
        stmt = line
        while stmt.rstrip().endswith("///") and i + 1 < len(raw):
            i += 1
            stmt = stmt.rstrip()[:-3] + " " + raw[i].strip()
        # A trailing // comment; dash.ado keeps no // inside a string that
        # an inlist() could be part of.
        stmt = re.sub(r"\s//\s.*$", "", stmt)
        out.append((start, stmt))
        i += 1
    return out


def _inlist_calls(stmt):
    """Each ``inlist(...)`` in *stmt* as its list of top-level arguments."""
    calls = []
    for m in re.finditer(r"\binlist\(", stmt):
        depth, j, args, cur, in_q = 1, m.end(), [], "", False
        while j < len(stmt) and depth:
            c = stmt[j]
            if c == '"':
                in_q = not in_q
            elif not in_q and c == "(":
                depth += 1
            elif not in_q and c == ")":
                depth -= 1
                if depth == 0:
                    break
            if not in_q and depth == 1 and c == ",":
                args.append(cur.strip())
                cur = ""
            else:
                cur += c
            j += 1
        args.append(cur.strip())
        calls.append(args)
    return calls


def _is_string_arg(a):
    return a.startswith('"') or a.startswith('`"')


def _families():
    """``{family: [types]}`` from the one program that defines them."""
    with open(_ADO, encoding="utf-8") as fh:
        src = fh.read()
    m = re.search(r"^program define _dash_plottype_families\b(.*?)^end\b",
                  src, re.S | re.M)
    assert m, "dash.ado defines no _dash_plottype_families program"
    fams = {}
    for name, words in re.findall(r'^\s*c_local\s+(_pt_\w+)\s+"([^"]*)"',
                                  m.group(1), re.M):
        assert name not in fams, f"{name} is defined twice"
        fams[name] = words.split()
    return fams


class TestNoPlotTypeTestIsAStringInlist:
    def test_no_string_inlist_tests_a_plot_type(self):
        hits = []
        for n, stmt in _ado_code_lines():
            for args in _inlist_calls(stmt):
                first = args[0].replace(" ", "")
                if any(first in (f'"`{m}\'"', f'`"`{m}\'"\'')
                       for m in _PLOT_TYPE_MACROS):
                    hits.append(f"dash.ado:{n}: inlist({', '.join(args)})")
        assert not hits, (
            "a plot type is still tested with a string inlist(), which takes "
            "at most ten arguments -- use a family list and `: list ptype "
            "in': \n" + "\n".join(hits))

    def test_no_string_inlist_is_one_argument_from_the_ceiling(self):
        """A string inlist() at 9 or 10 arguments cannot take two more."""
        near = []
        for n, stmt in _ado_code_lines():
            for args in _inlist_calls(stmt):
                if not any(_is_string_arg(a) for a in args):
                    continue
                if len(args) >= _STRING_INLIST_MAX_ARGS - 1:
                    near.append(f"dash.ado:{n}: {len(args)} arguments: "
                                f"inlist({', '.join(args)})")
        assert not near, "\n".join(near)

    def test_the_scan_sees_an_inlist(self):
        """Guards the guard: the scanner finds and splits a real call."""
        calls = _inlist_calls('if inlist("`ptype\'", "a", "b(c)", "d") {')
        assert calls == [['"`ptype\'"', '"a"', '"b(c)"', '"d"']]
        joined = [s for _, s in _ado_code_lines() if "inlist(" in s]
        assert joined, "no inlist() found in dash.ado at all"


class TestTheFamiliesAreNamedOnce:
    def test_every_family_is_defined(self):
        fams = _families()
        for name in ("_pt_univar", "_pt_range", "_pt_pc", "_pt_literal",
                     "_pt_ts"):
            assert name in fams, f"{name} is not defined"

    def test_no_family_is_redefined_elsewhere(self):
        with open(_ADO, encoding="utf-8") as fh:
            src = fh.read()
        body = re.search(r"^program define _dash_plottype_families\b.*?^end\b",
                         src, re.S | re.M).group(0)
        rest = src.replace(body, "")
        for name in _families():
            redef = re.findall(r"^\s*(?:c_)?local\s+%s\b" % re.escape(name),
                               rest, re.M)
            assert not redef, f"{name} is defined outside the families program"

    def test_the_families_are_the_renderers_categories(self):
        fams = _families()
        assert set(fams["_pt_range"]) == set(dr._DASH_RANGE_TYPES)
        assert set(fams["_pt_pc"]) == set(dr._DASH_PC_TYPES)
        assert set(fams["_pt_literal"]) == set(dr._DASH_LITERAL_TYPES)
        # The renderer's univariate set also carries the alias "hist",
        # which dash.ado never writes: the Mata table expands it first.
        assert set(fams["_pt_univar"]) == set(dr._DASH_UNIVARIATE_TYPES) - {"hist"}

    def test_every_member_is_a_type_dash_draws(self):
        drawn = dr._dash_plot_type_names()
        for name, types in _families().items():
            stray = sorted(set(types) - drawn)
            assert not stray, f"{name} names types dash does not draw: {stray}"

    def test_the_routing_families_do_not_overlap(self):
        """A type in two routing families would be parsed by the first."""
        fams = _families()
        order = ("_pt_univar", "_pt_range", "_pt_pc", "_pt_literal")
        seen = {}
        for name in order:
            for t in fams[name]:
                assert t not in seen, f"{t} is in {seen.get(t)} and {name}"
                seen[t] = name
