"""test_no_orphans.py -- no Stata program or Mata function dash ships is
dead code (WP-26 AC-26.1, BR-26.1; GAPS.md N).

What an auditor reads must be what runs.  GAPS.md N listed code nothing
called: _dash_graph_opts_to_json and _dash_kv_json in dash.ado, and
_dash_json_esc, _dash_html_esc and _html_escape in dash_parse.mata.  The
first was a trap as well as dead: it read the g_* locals of its own scope,
which are always empty, and returned {} whatever its caller held, while
the graph JSON dash writes is assembled inline in _dash_plot.  WP-26
deleted the five (24sep2026), and two more that the reading below found at
480159f: _dash_imm_gettoken, a wrapper of _dash_imm_next that only
test_parser.cscript called, and _dash_pc_immediate, pcarrowi's entry until
c036fb6 gave dash.ado _dash_immediate(vals, 4) instead, called since by
tests alone.

This file holds it.  Every ``program define`` in dash.ado and
dash_setup.ado and every function in dash_parse.mata must be called from
outside its own body, and reached, call by call, from one of the two
commands, dash and dash_setup.  A call is

* a program named as the command of a statement: first, after any
  capture, noisily or quietly prefix, braces and else, or after the
  condition of a one-line if, outside its parentheses;
* a Mata function named before "(" in Mata code: a function body in
  dash_parse.mata, or what follows ``mata:`` on an ado-file line.

Comments, ``*!`` header lines and string literals are not calls, and a
name in a list is not either: a ``local`` or ``foreach`` list -- such as
_dash_require_mata's ``_needed`` and the list its repair drops -- a
``program drop``, or a ``mata drop`` / ``mata describe`` line.  A call made
through a macro, `` `cmd' args``, would not be seen; dash makes none, and
one would be reported as a unit nothing calls -- a loud failure, never a
silent pass.  The units are test_program_coverage_map.py's parse, which
that file holds to scripts/measure_stata_coverage.py's.

The ambiguity branch of _dash_expand_plottype_str went too (TR-26.6): it
refused a plot-type name that reached two rows of the table, and no name
can.  TestNoPlotTypePrefixReachesTwoRows fails when one could.
"""
import os
import re
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)

import test_program_coverage_map as _units_parse  # noqa: E402

_ADO_FILES = ("dash.ado", "dash_setup.ado")
_MATA_FILE = "dash_parse.mata"

#: The commands a user types; everything else must be reached from them.
_COMMANDS = ("dash", "dash_setup")


def _read(name, root=None):
    with open(os.path.join(root or _ROOT, name), encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# Reading Stata: statements with comments dropped and strings blanked
# ---------------------------------------------------------------------------

def _stata_line(line, in_block):
    """``(code, continued, in_block)`` for one physical line of Stata: its
    comments dropped, each string literal written as "" -- a simple one to
    the next double quote, a compound one from `" to the "' that closes it,
    nesting -- and whether it ends in a ``///`` continuation."""
    out = []
    i, n = 0, len(line)
    while i < n:
        if in_block:
            j = line.find("*/", i)
            if j < 0:
                return "".join(out), False, True
            i, in_block = j + 2, False
            continue
        if line.startswith("/*", i):
            in_block, i = True, i + 2
            continue
        after_blank = i == 0 or line[i - 1] in " \t"
        if line.startswith("///", i) and after_blank:
            return "".join(out), True, False
        if line.startswith("//", i) and after_blank:
            return "".join(out), False, False
        if line.startswith('`"', i):
            depth, j = 1, i + 2
            while j < n and depth:
                if line.startswith('`"', j):
                    depth, j = depth + 1, j + 2
                elif line.startswith('"\'', j):
                    depth, j = depth - 1, j + 2
                else:
                    j += 1
            out.append('""')
            i = j
            continue
        if line[i] == '"':
            j = line.find('"', i + 1)
            out.append('""')
            i = n if j < 0 else j + 1
            continue
        out.append(line[i])
        i += 1
    return "".join(out), False, in_block


def _stata_statements(text):
    """``[(first line, code)]`` of every statement of an ado file, its
    ``///`` continuations joined.  A ``*`` line that begins a statement is a
    comment, as it is to Stata."""
    out, buf, first = [], [], None
    in_block = cont = False
    for n, line in enumerate(text.split("\n"), 1):
        if not cont and not in_block and line.lstrip().startswith("*"):
            continue
        code, cont, in_block = _stata_line(line, in_block)
        if first is None and code.strip():
            first = n
        buf.append(code.strip())
        if not cont:
            stmt = " ".join(p for p in buf if p)
            if stmt:
                out.append((first, stmt))
            buf, first = [], None
    stmt = " ".join(p for p in buf if p)
    if stmt:
        out.append((first, stmt))
    return out


def _mata_code(text):
    """``[(line, code)]`` of the Mata block of a .mata file -- the lines
    between the one that is exactly ``mata:`` and the last that is exactly
    ``end`` -- with ``//`` and ``/* */`` comments dropped and each string
    literal written as "".  Mata has no escape inside a string."""
    lines = text.split("\n")
    starts = [i for i, l in enumerate(lines) if l.strip() == "mata:"]
    ends = [i for i, l in enumerate(lines) if l.strip() == "end"]
    if not starts or not ends:
        return []
    out, in_block = [], False
    for i in range(starts[0] + 1, ends[-1]):
        line, code, j, n = lines[i], [], 0, len(lines[i])
        while j < n:
            if in_block:
                k = line.find("*/", j)
                if k < 0:
                    j = n
                    continue
                j, in_block = k + 2, False
                continue
            if line.startswith("/*", j):
                in_block, j = True, j + 2
                continue
            if line.startswith("//", j):
                break
            if line.startswith('`"', j):
                depth, k = 1, j + 2
                while k < n and depth:
                    if line.startswith('`"', k):
                        depth, k = depth + 1, k + 2
                    elif line.startswith('"\'', k):
                        depth, k = depth - 1, k + 2
                    else:
                        k += 1
                code.append('""')
                j = k
                continue
            if line[j] == '"':
                k = line.find('"', j + 1)
                code.append('""')
                j = n if k < 0 else k + 1
                continue
            code.append(line[j])
            j += 1
        if "".join(code).strip():
            out.append((i + 1, "".join(code)))
    return out


# ---------------------------------------------------------------------------
# What a statement calls
# ---------------------------------------------------------------------------

#: What may stand before a command: braces, else, the capture / noisily /
#: quietly prefixes in every abbreviation Stata takes (with or without a
#: colon), version #: and by ...:.
_PREFIX = re.compile(
    r"^(?:\{|\}|else\b|"
    r"(?:cap|capt|captu|captur|capture|n|no|noi|nois|noisi|noisil|noisily|"
    r"qui|quie|quiet|quietl|quietly)\b\s*:?|"
    r"version\s+[0-9.]+\s*:|"
    r"(?:by|bys|byso|bysor|bysort)\b[^:]*:)\s*")

#: A name that is a word of its own: not part of a longer word, a macro's
#: name (after ` or $) or a member (after .).
_NAME = r"(?<![A-Za-z0-9_`$.])([A-Za-z_][A-Za-z0-9_]*)"


def _strip_prefixes(s):
    s = s.strip()
    while True:
        m = _PREFIX.match(s)
        if not m or not m.group(0):
            return s
        s = s[m.end():]


def _outside_parens(s):
    """s with what is inside parentheses blanked, positions kept."""
    out, depth = [], 0
    for c in s:
        if c == "(":
            depth += 1
        elif c == ")" and depth:
            depth -= 1
            out.append(" ")
            continue
        out.append(c if depth == 0 else " ")
    return "".join(out)


def _command(stmt, programs):
    """What a statement runs, its prefixes stripped.  For a one-line if, the
    command after the condition: the first program name, or mata, outside
    the condition's parentheses."""
    s = _strip_prefixes(stmt)
    m = re.match(r"if\b", s)
    if not m:
        return s
    rest = s[m.end():]
    for w in re.finditer(_NAME, _outside_parens(rest)):
        if w.group(1) in programs or w.group(1) == "mata":
            return _strip_prefixes(rest[w.start():])
    return ""


def _mata_calls(code, funcs):
    """The library functions a line of Mata code calls."""
    return {m.group(1) for m in re.finditer(_NAME + r"\s*\(", code)
            if m.group(1) in funcs}


def _statement_calls(stmt, programs, funcs):
    """The programs and Mata functions one Stata statement calls."""
    cmd = _command(stmt, programs)
    m = re.match(r"[A-Za-z_][A-Za-z0-9_]*", cmd)
    if not m:
        return set()
    if m.group(0) in programs:
        return {m.group(0)}
    if m.group(0) != "mata":
        return set()
    code = cmd[m.end():].lstrip()
    if code.startswith(":"):
        code = code[1:].lstrip()
    # mata drop / describe / which ... name functions without calling them.
    if re.match(r"mata\b", code):
        return set()
    return _mata_calls(code, funcs)


def _call_graph(ado_texts, mata_text):
    """``(units, edges)``: units ``{name: file}`` and edges ``{(caller,
    callee)}``.  A caller is a unit, or ``<file>`` for code outside every
    unit of that file (it runs when the file is loaded); a unit's call of
    itself is no edge."""
    programs, funcs = {}, {}
    spans = {}
    for f, text in ado_texts.items():
        for name, span in _units_parse._ado_programs(text).items():
            programs[name] = f
            spans.setdefault(f, []).append((name,) + span)
    for name, span in _units_parse._mata_functions(mata_text).items():
        funcs[name] = _MATA_FILE
        spans.setdefault(_MATA_FILE, []).append((name,) + span)

    def owner(f, line):
        for name, a, b in spans.get(f, ()):
            if a <= line <= b:
                return name
        return "<%s>" % f

    edges = set()
    for f, text in ado_texts.items():
        for line, stmt in _stata_statements(text):
            who = owner(f, line)
            for callee in _statement_calls(stmt, programs, funcs):
                if callee != who:
                    edges.add((who, callee))
    for line, code in _mata_code(mata_text):
        who = owner(_MATA_FILE, line)
        for callee in _mata_calls(code, funcs):
            if callee != who:
                edges.add((who, callee))
    units = dict(programs)
    units.update(funcs)
    return units, edges


def _reached(units, edges):
    """The units reached from the commands and from each file's top level."""
    roots = {u for u in _COMMANDS if u in units}
    roots |= {c for c, _d in edges if c.startswith("<")}
    seen, todo = set(roots), list(roots)
    while todo:
        u = todo.pop()
        for c, d in edges:
            if c == u and d not in seen:
                seen.add(d)
                todo.append(d)
    return seen


def _sources(root=None):
    return ({f: _read(f, root) for f in _ADO_FILES}, _read(_MATA_FILE, root))


@pytest.fixture(scope="module")
def graph():
    return _call_graph(*_sources())


# ---------------------------------------------------------------------------
# The reading is right (guards the guard)
# ---------------------------------------------------------------------------

class TestTheReading:

    def test_it_finds_the_units_and_the_calls_dash_makes(self, graph):
        """An empty or partial reading would pass every check below."""
        units, edges = graph
        assert sum(1 for f in units.values() if f == "dash.ado") >= 50
        assert sum(1 for f in units.values() if f == "dash_setup.ado") >= 7
        assert sum(1 for f in units.values() if f == _MATA_FILE) >= 50
        assert len(edges) >= 150, len(edges)
        for edge in (
                ("dash", "_dash_require_mata"),        # a bare command
                ("dash", "_dash_plot"),                # macval() arguments
                ("_dash_require_python", "_dash_python_ok"),
                # `if cond prog' and `else prog' (_dash_process_segment)
                ("_dash_process_segment", "_dash_plot_cap_refuse"),
                # a Mata call on a mata: line, inside st_local()
                ("_dash_process_segment", "_dash_expand_plottype"),
                ("_dash_validate_path", "_dash_path_badchar"),
                # Mata calling Mata
                ("_dash_check_utf8", "_dash_is_utf8"),
                ("_dash_item_globals", "_dash_kpi_fields"),
                ("_dash_expand_plottype", "_dash_expand_plottype_str"),
                ("_dash_imm_records", "_dash_imm_next"),
                ("dash_setup", "_dash_pymin")):
            assert edge in edges, edge

    def test_its_mata_calls_from_dash_ado_are_the_needed_list(self, graph):
        """A second reading agrees: the library functions this finds
        dash.ado calling are _dash_require_mata's `_needed' list, which
        test_program_coverage_map.py holds to the mata: lines it reads."""
        units, edges = graph
        top = {"<%s>" % f for f in _ADO_FILES}
        from_ado = {d for c, d in edges if units.get(d) == _MATA_FILE
                    and (units.get(c) in _ADO_FILES or c in top)}
        needed, called, _funcs = _units_parse._needed_and_called()
        assert from_ado == needed == called, (
            sorted(from_ado ^ needed), sorted(from_ado ^ called))

    def test_names_that_are_not_calls(self):
        """dash names victim and vfunc in every way that is not a call;
        victim calls itself and vfunc, and vfunc itself.  Neither is called
        from outside, so neither is reached."""
        ado = "\n".join([
            "*! victim and vfunc() named in a header line",
            "program define dash",
            "    // victim in a comment",
            "    * victim in a star comment",
            "    /* victim in a block",
            "       comment */",
            '    display "victim and vfunc() in a string"',
            '    display `"victim "in" a compound string, vfunc()"\'',
            "    local _needed victim vfunc",
            "    foreach f in victim vfunc {",
            "        capture mata: mata drop `f'()",
            "    }",
            "    capture program drop victim",
            "    capture mata: mata drop vfunc()",
            "    quietly capture mata: mata describe vfunc()",
            "    local v `victim'",
            "    display $victim",
            "    local n = victim_count + 1 ///",
            "        // victim after a continuation",
            "end",
            "program define victim",
            "    victim",
            "    mata: vfunc()",
            "end",
        ])
        mata = "\n".join([
            "*! vfunc() in the library's header",
            "mata:",
            "void vfunc() {",
            "    // vfunc() in a comment",
            '    printf("vfunc() in a string")',
            "    vfunc()",
            "}",
            "end",
        ])
        units, edges = _call_graph({"dash.ado": ado, "dash_setup.ado": ""},
                                   mata)
        assert set(units) == {"dash", "victim", "vfunc"}
        assert edges == {("victim", "vfunc")}, edges
        assert _reached(units, edges) == {"dash"}
        # One real call of victim, and both are reached.
        units, edges = _call_graph(
            {"dash.ado": ado.replace("    local _needed victim vfunc",
                                     "    victim"),
             "dash_setup.ado": ""}, mata)
        assert edges == {("dash", "victim"), ("victim", "vfunc")}, edges
        assert _reached(units, edges) == set(units)

    def test_calls_in_every_form_dash_writes(self):
        ado = "\n".join([
            "program define dash",
            "    p1",
            "    capture noisily p2 `\"a \"b\" c\"' x",
            "    quietly: p3",
            "    cap noi p4, opt(1)",
            "    if `x' > 1 p5 `r(value)'",
            "    else       p6",
            '    if inlist("`t\'", "a") & (1 == 1) p7',
            "    } else if `y' p8",
            "    mata: st_local(\"z\", f1(st_local(\"z\")))",
            "    capture mata: f2(\"x\")",
            "    if `z' mata: f3()",
            "    p9 ///",
            "        more",
            "end",
        ] + ["program define p%d\nend" % k for k in range(1, 10)])
        mata = "\n".join([
            "mata:",
            "real scalar f1(string scalar s)",
            "{",
            "    return(f4(s))",
            "}",
            "void f2(string scalar s) {",
            "}",
            "void f3() {",
            "}",
            "real scalar f4(string scalar s) {",
            "    return(strlen(s))",
            "}",
            "end",
        ])
        units, edges = _call_graph({"dash.ado": ado, "dash_setup.ado": ""},
                                   mata)
        want = {("dash", "p%d" % k) for k in range(1, 10)}
        want |= {("dash", "f1"), ("dash", "f2"), ("dash", "f3"),
                 ("f1", "f4")}
        assert want <= edges, sorted(want - edges)
        assert _reached(units, edges) >= set(units)

    def test_reachability_follows_calls_only(self):
        """A unit called only by a unit nothing reaches is not reached."""
        ado = "\n".join(["program define dash", "    a", "end",
                         "program define a", "end",
                         "program define b", "    c", "end",
                         "program define c", "end"])
        units, edges = _call_graph({"dash.ado": ado, "dash_setup.ado": ""},
                                   "")
        assert ("b", "c") in edges
        assert _reached(units, edges) == {"dash", "a"}

    @pytest.mark.parametrize("f", _ADO_FILES)
    def test_the_ado_files_hold_no_block_this_cannot_read(self, f):
        """A multi-line mata or python block would be read as Stata, and it
        ends at an `end' the program parse takes for the program's.  dash
        writes one-line `mata:' and `python:' statements only."""
        bad = [(n, l) for n, l in enumerate(_read(f).split("\n"), 1)
               if re.match(r"^\s*(?:mata|python)\s*(?::|\{)?\s*$", l)]
        assert not bad, bad


# ---------------------------------------------------------------------------
# Nothing is orphaned
# ---------------------------------------------------------------------------

class TestNothingIsOrphaned:

    @pytest.mark.parametrize("f", _ADO_FILES)
    def test_every_program_but_the_commands_has_a_caller(self, graph, f):
        units, edges = graph
        called = {d for _c, d in edges}
        orphans = sorted(u for u, g in units.items()
                         if g == f and u not in _COMMANDS and u not in called)
        assert not orphans, (
            f"{f} defines {orphans}, which nothing calls: delete them (and "
            f"their entries in test/program_coverage_map.py), or call them")

    def test_every_mata_function_is_called_from_dash_or_the_library(self,
                                                                    graph):
        units, edges = graph
        called = {d for _c, d in edges}
        orphans = sorted(u for u, g in units.items()
                         if g == _MATA_FILE and u not in called)
        assert not orphans, (
            f"dash_parse.mata defines {orphans}, which neither dash.ado nor "
            f"another function of the library calls: delete them (and their "
            f"entries in test/program_coverage_map.py), or call them")

    def test_every_unit_is_reached_from_a_command(self, graph):
        units, edges = graph
        lost = sorted(set(units) - _reached(units, edges))
        callers = {u: sorted(c for c, d in edges if d == u) for u in lost}
        assert not lost, (
            "these units are not reached from dash or dash_setup -- nothing "
            "calls them, or only units nothing reaches do: %r" % callers)


# ---------------------------------------------------------------------------
# No plot-type name reaches two rows of _dash_expand_plottype_str's table
# ---------------------------------------------------------------------------

def _plottype_rows(mata_text):
    """``[(full name, minimum)]`` of _dash_expand_plottype_str's table."""
    body = mata_text[mata_text.index("string scalar _dash_expand_plottype_str("):]
    body = body[:body.index("\n}\n")]
    return re.findall(r'\("([a-z]+)","([a-z]+)"\)', body)


def _names_reaching_two(rows):
    """``{prefix: [rows it reaches]}`` for every prefix of a full name that
    reaches more than one row: at least as long as the row's minimum and a
    prefix of its full name, the test _dash_expand_plottype_str makes."""
    out = {}
    for full, _mn in rows:
        for k in range(1, len(full) + 1):
            p = full[:k]
            hits = [f for f, m in rows if len(p) >= len(m) and f.startswith(p)]
            if len(hits) > 1:
                out[p] = hits
    return out


class TestNoPlotTypePrefixReachesTwoRows:
    """_dash_expand_plottype_str takes the first row a name reaches, which is
    right only while no name reaches two.  It counted the rows and refused
    a name that reached two, "an ambiguous prefix", and nothing could reach
    that branch (measured 24sep2026 at 480159f, in Stata through the real
    function: each of the 186 prefixes of the 40 names reached at most one
    row).  twoway has no ambiguous plot type to refuse either: of the 209
    prefixes of the 45 plot-type names probed it took each as the one type
    whose minimum it reaches, or refused it, "s is not a twoway plot type",
    r(198) -- as dash refuses it.  test_parser.cscript P1A-76 checks the
    same on the real function."""

    def test_the_table_is_read_whole(self):
        rows = _plottype_rows(_read(_MATA_FILE))
        assert len(rows) >= 40, rows
        # WP-31 B1: rpspike was the last row once rpcap and rpspike were
        # drawn; WP-31 B4b: contourline is, now contour and contourline are.
        assert rows[0] == ("scatter", "sc") and rows[-1] == ("contourline",
                                                              "contourline")
        assert len({f for f, _m in rows}) == len(rows), rows
        assert all(f.startswith(m) for f, m in rows), rows

    def test_no_prefix_reaches_two_rows(self):
        two = _names_reaching_two(_plottype_rows(_read(_MATA_FILE)))
        assert not two, (
            "these plot-type names reach two rows of _dash_expand_plottype_str's "
            "table, and the first row would be taken without a word: %r.  "
            "Give one of the rows a longer minimum, as twoway does." % two)

    def test_the_check_sees_a_prefix_two_rows_reach(self):
        two = _names_reaching_two([("scatter", "sc"), ("scatteri", "sc"),
                                   ("line", "li")])
        assert two == {"sc": ["scatter", "scatteri"],
                       "sca": ["scatter", "scatteri"],
                       "scat": ["scatter", "scatteri"],
                       "scatt": ["scatter", "scatteri"],
                       "scatte": ["scatter", "scatteri"],
                       "scatter": ["scatter", "scatteri"]}
        assert _names_reaching_two([("scatter", "sc"),
                                    ("scatteri", "scatteri")]) == {}


# ---------------------------------------------------------------------------
# The jsonio shims are gone
# ---------------------------------------------------------------------------

class TestTheJsonioShimsAreGone:
    """_dash_date_fmts_swap and _dash_date_fmts_restore gave each date
    variable %12.0g for the length of the `jsonio out' call, because jsonio
    wrote a %t* value through its display format.  dash writes its own data
    file from Python since 24sep2026, reading each stored value whatever
    its format, so the pair changed nothing that was written and was kept
    only by the calls around the export.  They are deleted; that dates still
    reach both renderers as dates is test_date_range.py's, test_dates.py's,
    test_served_dates.py's and test_program_coverage.cscript PC-08..11's."""

    def test_neither_is_defined_or_called(self):
        ado = _read("dash.ado")
        for name in ("_dash_date_fmts_swap", "_dash_date_fmts_restore"):
            assert name not in ado, name
