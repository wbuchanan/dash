"""`dash.sthlp` and `dash.ado` are checked against each other, mechanically.

Sixteen sections of work added roughly a hundred option declarations to
`dash.ado`. The help file did not follow, and nothing made it: reading two
files side by side is how 98 accepted options ended up undocumented, how five
options that dash honours ended up under a heading that says they are
unsupported, and how `xlabel()` came to be advertised with two different
minimum abbreviations nine lines apart.

This file is the test that stops them separating again. It asserts in BOTH
directions, because one direction only is how the undocumented half grew.

The help is not meant to restate `twoway`. `dash.sthlp:127-131` redirects the
reader to Stata's own documentation for anything that behaves as it does in
`twoway`, and that is the right call -- so requiring every accepted option to
be documented here would demand a second copy of the twoway manual. The rule
used instead is mechanical: `test/fixtures/abbrev_truth.json` records every
option probed against REAL twoway, so an option in that file is one the
redirect covers, and an option **not** in it is dash's own invention and has
no other documentation anywhere. Those must be in the help.

Parsing the help is the part that goes wrong quietly. SMCL puts an option
name in several shapes, and the naive regexes each miss most of the surface:
a strict ``{cmdab:a:b}`` with a closing-brace anchor finds 9 of 28 options,
because the tail carries the open paren (``{cmdab:ml:abel(}``) or a whole
argument (``{cmdab:xsc:ale(log)}``); a colon-only ``{opt:...}`` finds none at
all, because this file uses the space form throughout, which is the entire
Unsupported section; and "first token of a synopt row" sweeps in the eleven
KPI statistic names, the thirteen server-mode comparison rows and an empty
label. Each rule below exists because one of those failures was measured.
"""
import json
import os
import re
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from test_abbreviations import _program_body, _syntax_options   # noqa: E402

_ADO = os.path.join(_HERE, "..", "dash.ado")
_HELP = os.path.join(_HERE, "..", "dash.sthlp")
_TRUTH = os.path.join(_HERE, "fixtures", "abbrev_truth.json")


# ---------------------------------------------------------------------------
# The help side
# ---------------------------------------------------------------------------

# Tables whose rows are values, not options: the KPI statistic list and the
# server-vs-standalone feature comparison. Keyed by the {marker} they follow
# so that moving them does not silently re-admit them.
_NON_OPTION_TABLES = ("kpi_statistics", "mode_comparison")

# Names that look like options but are not: the generated app's CLI flags,
# Stata globals and c() settings, and SMCL's own brace escapes.
_NOT_OPTIONS = re.compile(r"^(?:--|\$|c\(|-\(|\)-)")


def _help_text():
    with open(_HELP, encoding="utf-8") as fh:
        return fh.read()


def _name_from_cmdab(head, tail):
    """`{cmdab:ml:abel(}` is mlabel, min ml. An empty tail (`{cmdab:fmt:}`)
    is legal and means the full name admits no abbreviation."""
    return (head + re.match(r"^[A-Za-z0-9_]*", tail).group(0)).lower()


def _help_options():
    """Every option the help DEFINES, with the minimum it advertises.

    Returns ``{name: set_of_claimed_minimums}``. A name with no ``{cmdab:}``
    anywhere maps to an empty set -- documented, but with no abbreviation
    claim to check.
    """
    lines = _help_text().split("\n")
    syntax_lo, syntax_hi = None, None
    for i, ln in enumerate(lines):
        if ln.startswith("{marker syntax}"):
            syntax_lo = i
        elif syntax_lo is not None and ln.startswith("{marker description}"):
            syntax_hi = i
            break
    assert syntax_lo is not None and syntax_hi is not None, (
        "the Syntax section markers moved; every check below would go blind"
    )

    # Which {marker} each line sits under, so a table can be excluded by
    # section rather than by guessing at its contents.
    section, sections = "", []
    for ln in lines:
        m = re.match(r"\{marker ([a-z_]+)\}", ln)
        if m:
            section = m.group(1)
        sections.append(section)

    # The statistic table lives under {marker kpi} and the comparison table
    # under {marker server_mode}; name them so the exclusion is explicit.
    excluded = {"kpi": "kpi_statistics", "server_mode": "mode_comparison"}

    out: "dict[str, set]" = {}
    in_phang = False
    for i, ln in enumerate(lines):
        stripped = ln.lstrip()
        in_syntax = syntax_lo <= i < syntax_hi
        is_synopt = stripped.startswith("{synopt:")
        # A {phang2} entry may run over several lines, and a grouped entry
        # opens with {ul:...} and lists its options on the lines below. The
        # block ends at the blank line before the next paragraph.
        if stripped.startswith("{phang2}") or stripped.startswith("{phang}"):
            in_phang = bool(re.match(
                r"\{phang2?\}\s*(\{(opt|opth|cmdab|cmd)[: ]|\{ul:)", stripped))
        elif not stripped:
            in_phang = False
        if not (in_syntax or is_synopt or in_phang):
            continue                       # prose: a weaker tier, see below
        if is_synopt and excluded.get(sections[i]) in _NON_OPTION_TABLES:
            continue

        # {cmdab:head:tail...} -- no closing-brace anchor, the tail may carry
        # a paren or a whole argument.
        for head, tail in re.findall(r"\{cmdab:([A-Za-z0-9_]+):([^}]*)", ln):
            name = _name_from_cmdab(head, tail)
            if name and not _NOT_OPTIONS.match(name):
                out.setdefault(name, set()).add(head.lower())
        # {opt name(...)} / {opth name(...)} -- BOTH the colon and the space
        # form; never try to balance the parentheses.
        for name in re.findall(r"\{opth?[: ]\s*,?\s*([A-Za-z_][A-Za-z0-9_]*)",
                               ln):
            if not _NOT_OPTIONS.match(name):
                out.setdefault(name.lower(), set())
        # {cmd:name(} and {cmd:, name(} -- a leading comma introduces a
        # sub-option, which is still a documented name.
        for name in re.findall(r"\{cmd:\s*,?\s*([A-Za-z_][A-Za-z0-9_]*)\(", ln):
            if not _NOT_OPTIONS.match(name):
                out.setdefault(name.lower(), set())
    return out


def _help_mentions(name):
    """A weaker tier: the name appears in the help at all, anywhere."""
    return re.search(r"\b%s\b" % re.escape(name), _help_text()) is not None


# ---------------------------------------------------------------------------
# The ado side
# ---------------------------------------------------------------------------

_PROGRAMS = ("_dash_parse_plot_opts", "_dash_parse_graph_opts", "_dash_build",
             "_dash_kpi", "_dash_prepare_spec", "_dash_serve_spec")

# Declared by `syntax' for internal plumbing; never typed by a user.
_INTERNAL = {"specpath", "datapath", "cmdname", "inherit", "renderpy",
             "spec", "data", "output", "mode"}


def _ado_text():
    with open(_ADO, encoding="utf-8") as fh:
        return fh.read()


def _ado_declarations():
    """``{name: declared_minimum}`` over every user-facing syntax statement."""
    src = _ado_text()
    out = {}
    for prog in _PROGRAMS:
        body = _program_body(src, prog)
        assert body, f"program {prog} not found; the parser is looking in the wrong place"
        for mn, full in _syntax_options(body):
            if full not in _INTERNAL:
                out.setdefault(full, mn)
    return out


def _pending(prog):
    src = _ado_text()
    i = src.index("program define " + prog)
    j = src.index("local _dash_unknown", i)
    return set(re.findall(r"_dash_pending' (\w+)\"", src[i:j]))


def _ignored_options():
    return _pending("_dash_parse_plot_opts") | _pending("_dash_parse_graph_opts")


def _unsupported_section():
    """Option names listed under the help's Unsupported heading."""
    h = _help_text()
    i = h.index("{marker unsupported}")
    j = h.index("{marker dependencies}", i)
    # An {opt} inside a {phang2} ENTRY defines an option; an {opt} in a
    # {pstd} paragraph is prose. A grouped entry opens with {ul:Heading.} and
    # lists its options on the lines below, so the block runs from the
    # {phang2} to the blank line that ends it. Cross-references inside an
    # entry are written {cmd:...}, which is not collected here.
    out, in_entry = set(), False
    for ln in h[i:j].split("\n"):
        stripped = ln.lstrip()
        if stripped.startswith("{phang2}") or stripped.startswith("{phang}"):
            in_entry = True
        elif not stripped or stripped.startswith("{pstd}"):
            in_entry = False
        if in_entry:
            out.update(n.lower() for n in re.findall(
                r"\{opth?[: ]\s*([A-Za-z_][A-Za-z0-9_]*)", stripped))
    return out


def _twoway_options():
    """Options probed against real twoway, so covered by the help's redirect."""
    with open(_TRUTH, encoding="utf-8") as fh:
        return set(json.load(fh)["options"])


# ---------------------------------------------------------------------------
# Guards on the parsers themselves
# ---------------------------------------------------------------------------

class TestTheParsersFoundSomething:
    """Every assertion below is vacuous if a parser silently returns little."""

    def test_the_help_parser_finds_the_whole_surface(self):
        found = _help_options()
        assert len(found) >= 50, (
            f"only {len(found)} options parsed out of dash.sthlp; the naive "
            f"regexes found 9-17, so this parser has regressed to one of them"
        )

    def test_the_help_parser_handles_a_paren_carrying_tail(self):
        """{cmdab:ml:abel(} -- the construct that defeats a brace anchor."""
        assert "mlabel" in _help_options()

    def test_the_help_parser_handles_an_argument_carrying_tail(self):
        """{cmdab:xsc:ale(log)} -- a whole argument inside the directive."""
        assert "xscale" in _help_options()

    def test_the_help_parser_handles_the_space_form_of_opt(self):
        """The entire Unsupported section uses `{opt name(...)}`."""
        assert "recast" in _help_options()

    def test_the_help_parser_handles_an_empty_cmdab_tail(self):
        """{cmdab:fmt:} means fmt, which admits no abbreviation."""
        assert "fmt" in _help_options()

    def test_the_help_parser_excludes_the_statistic_table(self):
        """The KPI statistic rows are values, not options."""
        found = _help_options()
        assert "dcount" not in found and "median" not in found

    def test_the_ado_parser_finds_the_whole_surface(self):
        assert len(_ado_declarations()) >= 120

    def test_the_ignored_list_was_found(self):
        assert len(_ignored_options()) >= 20

    def test_the_unsupported_section_was_found(self):
        assert len(_unsupported_section()) >= 3


# ---------------------------------------------------------------------------
# 1. Everything the help defines must be accepted
# ---------------------------------------------------------------------------

class TestEveryDocumentedOptionIsAccepted:
    def test_no_documented_option_is_rejected(self):
        declared = _ado_declarations()
        documented = _help_options()
        # Sub-options live inside another option's parentheses and so are
        # never declared by `syntax' themselves.
        subopts = {"type", "exclude", "label", "format", "replace", "cols",
                   "rows", "color", "lcolor", "lwidth", "fcolor", "off", "on",
                   "range", "degree", "estopts"}
        missing = sorted(set(documented) - set(declared) - subopts)
        assert not missing, (
            f"{len(missing)} options the help documents are not declared by "
            f"any syntax statement, so `dash' would report them as unknown: "
            f"{missing}"
        )


# ---------------------------------------------------------------------------
# 2. The abbreviations the help advertises must be the ones dash accepts
# ---------------------------------------------------------------------------

class TestAbbreviationsAgree:
    def test_every_cmdab_claim_matches_the_declaration(self):
        declared = _ado_declarations()
        bad = []
        for name, claims in sorted(_help_options().items()):
            if name not in declared:
                continue
            for claim in sorted(claims):
                if claim != declared[name]:
                    bad.append(f"{name}: help says {claim!r}, "
                               f"dash.ado accepts {declared[name]!r}")
        assert not bad, (
            "the help advertises a different minimum abbreviation from the "
            "one dash accepts:\n  " + "\n  ".join(bad)
        )

    def test_the_help_does_not_contradict_itself(self):
        two = {n: sorted(c) for n, c in _help_options().items() if len(c) > 1}
        assert not two, (
            f"the help advertises two different minimum abbreviations for "
            f"the same option: {two}"
        )


# ---------------------------------------------------------------------------
# 3. Everything dash invented must be documented
# ---------------------------------------------------------------------------

class TestEveryDashOnlyOptionIsDocumented:
    def test_an_option_twoway_does_not_have_is_documented(self):
        twoway = _twoway_options()
        documented = set(_help_options())
        # Alias spellings of an option documented under its full name.
        aliases = {"bw": "bwidth", "mlg": "mlabgap", "colv": "colorvar",
                   "cv": "colorvar", "pbgc": "plotbgcolor",
                   "xla2": "xlabel2", "xsc2": "xscale2", "xti2": "xtitle2",
                   "yla2": "ylabel2", "ysc2": "yscale2", "yti2": "ytitle2",
                   "t": "t1title", "b": "b1title", "l": "l1title",
                   "r": "r1title", "bins": "bin", "sc": "scatter",
                   "li": "line", "hist": "histogram"}
        undocumented = []
        for name in sorted(_ado_declarations()):
            if name in twoway or name in documented:
                continue
            if aliases.get(name) in documented:
                continue
            if _help_mentions(name):
                continue                     # named in prose: weaker, allowed
            undocumented.append(name)
        assert not undocumented, (
            f"{len(undocumented)} options exist only in dash -- twoway has no "
            f"such option, so the help's redirect to the twoway manual cannot "
            f"cover them -- and they appear nowhere in dash.sthlp: "
            f"{undocumented}"
        )


# ---------------------------------------------------------------------------
# 4. The Unsupported section must say what dash actually ignores
# ---------------------------------------------------------------------------

class TestTheUnsupportedSectionIsTrue:
    def test_nothing_listed_there_is_honoured(self):
        listed = _unsupported_section()
        ignored = _ignored_options()
        honoured = sorted(listed - ignored)
        assert not honoured, (
            f"{len(honoured)} options are documented under \"Unsupported "
            f"Stata twoway options\" although dash honours them, so the help "
            f"tells the user to stop using something that works: {honoured}"
        )

    def test_everything_dash_ignores_is_listed_there(self):
        listed = _unsupported_section()
        missing = sorted(_ignored_options() - listed)
        assert not missing, (
            f"dash accepts {len(missing)} options and reports each one as "
            f"ignored, but the help's list of unsupported options does not "
            f"name them: {missing}"
        )


# ---------------------------------------------------------------------------
# 5. The KPI statistics the command accepts must be the ones it documents
# ---------------------------------------------------------------------------

class TestKpiStatisticsAreDocumented:
    @staticmethod
    def _valid_stats():
        m = re.search(r'local valid_stats\s+"([^"]+)"', _ado_text())
        assert m, "dash.ado's valid_stats list moved"
        return m.group(1).split()

    def test_the_list_was_found(self):
        assert len(self._valid_stats()) >= 10

    def test_every_accepted_statistic_is_in_the_table(self):
        h = _help_text()
        i = h.index("{marker kpi}")
        j = h.index("{marker server_mode}", i)
        table = h[i:j]
        missing = [s for s in self._valid_stats()
                   if not re.search(r"\{cmd:%s\}" % re.escape(s), table)]
        assert not missing, (
            f"`dash kpi' accepts {missing} and the help's table of supported "
            f"statistics does not list them"
        )


# ---------------------------------------------------------------------------
# 6. Every internal link must resolve
# ---------------------------------------------------------------------------

class TestInternalLinksResolve:
    """`{help dash##scheme:Stata scheme support}` pointed at nothing.

    dash.sthlp:176 told the reader to see a section on scheme support "below".
    There was no `{marker scheme}` anywhere in the file and no such section;
    scheme() was documented under the heading that says it is unsupported.
    A reader who followed the link landed at the top of the help.
    """

    def test_every_marker_reference_has_a_marker(self):
        h = _help_text()
        markers = set(re.findall(r"\{marker ([a-z_0-9]+)\}", h))
        refs = set(re.findall(r"dash##([a-z_0-9]+)", h))
        dead = sorted(refs - markers)
        assert not dead, (
            f"the help links to {dead}, and no {{marker}} of that name "
            f"exists, so the link goes nowhere"
        )

    def test_the_markers_are_unique(self):
        h = _help_text()
        seen, dupes = set(), set()
        for m in re.findall(r"\{marker ([a-z_0-9]+)\}", h):
            (dupes if m in seen else seen).add(m)
        assert not dupes, f"duplicate {{marker}} names: {sorted(dupes)}"

    def test_the_reference_scan_found_something(self):
        assert len(re.findall(r"dash##[a-z_0-9]+", _help_text())) >= 10
