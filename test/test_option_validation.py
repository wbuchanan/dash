"""Every option value is validated, and no unknown style name is silent.

ROADMAP WP-15 / GAPS.md E5.  The rule, from the implementation contract:
dash refuses a value where twoway refuses it, refuses a non-number where a
number-only option got a word twoway would silently ignore, and -- like
twoway's own ``(note: named style X not found in class Y, default attributes
used)`` -- reports and falls back on the scheme where a STYLE NAME (colour,
symbol, size, line width, pattern, angle, clock position, intensity) is
unknown.

Two halves.  The Stata half is a declarative table in ``dash.ado``
(``_dash_option_rules``) read by ``_dash_validate_opts`` and
``_dash_validate_value``; the tests here read that table back out of the
file and check its shape against the parsers that declare the options, so a
rule for an option no parser accepts, a malformed kind, or a plot-type
qualifier naming a type dash cannot draw is caught without running Stata.

The renderer half is measured.  Before this work a bad style name was one
of three things depending on where it landed: silently dropped (``except
ValueError: pass`` in the option appliers), a hand-written warning of its
own wording (mlcolor, mlwidth), or an abort of the whole render --
``scatteri ..., msize(abc)`` and ``dropline ..., jitter(abc)`` raised
``ValueError`` out of the mapper, and ``jitterseed(-1)`` died inside
``numpy.random.default_rng``.  Every case below now renders, in both modes,
with exactly one warning that names the option, and the two modes raise the
same list -- the served app copies ``GlyphMapper`` and ``OptionTranslator``
by source, so the note helper must travel with them.
"""
import itertools
import json
import os
import re
import sys
import tempfile
import warnings

import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import LabelSet

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import make_data_json, load_app  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_abbreviations import _program_body, _syntax_options  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_ADO = os.path.join(_HERE, "..", "dash.ado")
_BEGIN = "// BEGIN option-validation table (WP-15)"
_END = "// END option-validation table (WP-15)"

# scheme since WP-17: the table's `scheme=scheme' (a shipped scheme, a
# theme or a .scheme file in the working directory).  Checked against the
# branches _dash_validate_value really has (_validator_kinds below): a kind
# the chain has no branch for would pass every value unvalidated.
# axislist since WP-28 S14 (GAPS2 B1): the axis-label and tick options,
# expanded by Stata's numlist and never refused.
KINDS = {"num", "int", "pos", "style", "istyle", "enum", "numlist", "var",
         "varlist", "byvarlist", "format", "scheme", "axislist",
         # WP-30 P1.5 (S17's P1.23b): zlabel()'s format() is judged as the
         # axis-label options' is.
         "keyformat",
         # 14 -> 15: WP-30 P1.13a the colour kind (a comma-written plot
         # colour is refused in twoway's words).
         "colour",
         # 15 -> 16: WP-31 C10a the range kind (two numbers, a `.' for the
         # data's bound with ,m, or a variable's min and max).
         "range"}

#: The contract's table, token for token (DESIGN.md section 2).  The test
#: asserts the table in dash.ado carries every one of these; it may carry
#: more, and the structural checks below apply to all of it.
# WP-30 P1.12b: the line-width rules read Stata units (,u)
CONTRACT_PLOT_RULES = """
msize=style  mlabsize=style  mlabgap=style
lwidth=style,0,10000,u  mlwidth=style,0,10000,u
msangle=style,-360,360  mlabposition=style  fintensity=style
jitter=num,0,100  jitterseed=int,0  jseed=int,0
yaxis=int,1,2  xaxis=int,1,2
malpha=num,0,100  lalpha=num,0,100  falpha=num,0,100
base=num  barwidth=pos  level=num@lfitci|qfitci|fpfitci
degree=int,0,3  bwidth=num@lowess  bwidth=num,0@kdensity  bwidth=pos
kernel=enum,epanechnikov|epan2|biweight|cosine|gaussian|parzen|rectangle|triangle
n=int,1,300@mspline  n=int,1,10000  bin=int,1,1000  width=pos  start=num  bands=int,1,200
level=num,10,99.99@lpolyci
colornlevels=int,2,256
colpalette=enum,viridis|magma|inferno|plasma|cividis|turbo|greys|blues|reds
colorcuts=numlist,1  colorvar=var  mlabel=var
range=range,2,2,m@lfit|qfit|lfitci|qfitci  range=range,2,2
"""
CONTRACT_GRAPH_RULES = """
xsize=style,1,100  ysize=style,1,100  aspectratio=num,0  hover=varlist  by=byvarlist
"""
CONTRACT_KPI_RULES = "fmt=format"

# The contract's five, and scheme, the graph rule WP-17 added.
GRAPH_OPTIONS = {"xsize", "ysize", "aspectratio", "hover", "by", "scheme"}
KPI_OPTIONS = {"fmt"}

# option=kind[,p1[,p2[,p3]]][@type1|type2]
# The kind is any word.  It listed the kinds this file knew, so a rule of
# any other kind was never parsed and the kind check could not fail: the
# real rule `scheme=scheme' was invisible to every test here (measured
# 24sep2026: 42 rules parsed, 43 tokens in the table).
_TOKEN = re.compile(
    r"(?<![\w`'\"])([a-z][a-z0-9]*)="
    r"([a-z]+)"
    r"((?:,[^\s\"'`@]*)?)((?:@[a-z0-9|]+)?)(?![\w])")


from conftest import render_models  # noqa: E402


def _ado():
    with open(_ADO, encoding="utf-8") as fh:
        return fh.read()


def _parse_rules(text):
    """``[(option, kind, (p1, p2, ...), (type, ...)), ...]`` from rule text.

    Stata comments are dropped first: the table's own header spells the
    grammar as ``option=kind[,p1...]``, which is not a rule."""
    text = re.sub(r"(?m)(^|\s)//.*$", r"\1", text)
    out = []
    for opt, kind, params, types in _TOKEN.findall(text):
        ps = tuple(params[1:].split(",")) if params else ()
        ts = tuple(types[1:].split("|")) if types else ()
        out.append((opt, kind, ps, ts))
    return out


def _unparse(rule):
    """A parsed rule written back as its table token."""
    opt, kind, ps, ts = rule
    return (f"{opt}={kind}" + ("," + ",".join(ps) if ps else "")
            + ("@" + "|".join(ts) if ts else ""))


def _table_block():
    src = _ado()
    if _BEGIN not in src or _END not in src:
        return None
    i = src.index(_BEGIN)
    return src[i:src.index(_END, i)]


_BLOCK = _table_block()


@pytest.fixture
def _the_table():
    """Fails -- it used to SKIP -- a test that reads the table when the
    WP-15 sentinel comments are gone.  The skip dates from before the
    table existed; since it shipped, a lost sentinel skipped three classes
    and three more tests (36 in all, measured 24sep2026) and emptied the
    parametrize below, without a failure anywhere
    (test_the_table_sentinels_are_there guards too)."""
    if _BLOCK is None:
        pytest.fail(f"dash.ado has lost the option-validation table's "
                    f"sentinel comments ({_BEGIN!r} ... {_END!r})")


_needs_table = pytest.mark.usefixtures("_the_table")


def _table_tokens():
    """Every whitespace-separated token of the ``local plot`` and ``local
    graph`` lines of _dash_option_rules, continuations joined: what
    _dash_validate_opts reads, whether or not _TOKEN can parse it."""
    body = _program_body(_ado(), "_dash_option_rules") or ""
    joined = re.sub(r"///[^\n]*\n", " ", body)
    toks = []
    for m in re.finditer(r"^\s*local\s+(?:plot|graph)\s+(.*)$", joined,
                         re.M):
        toks += m.group(1).split()
    return toks


def _validator_kinds():
    """The kinds _dash_validate_value's else-if chain has a branch for:
    ``if "`kind'" == "x"`` and ``inlist("`kind'", "x", ...)`` heads at the
    chain's indent (the nested tests inside a branch are not heads)."""
    body = _program_body(_ado(), "_dash_validate_value") or ""
    kinds = set()
    for cond in re.findall(r"^    (?:else )?if (.*)\{\s*$", body, re.M):
        kinds |= set(re.findall(r'"`kind\'"\s*==\s*"(\w+)"', cond))
        for args in re.findall(r'inlist\("`kind\'",\s*([^)]*)\)', cond):
            kinds |= set(re.findall(r'"(\w+)"', args))
    return kinds


def _is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def _is_integer(s):
    return re.fullmatch(r"-?\d+", s) is not None


# ---------------------------------------------------------------------------
# (a) The table in dash.ado
# ---------------------------------------------------------------------------

def test_the_table_sentinels_are_there():
    """Not skippable: every class below reads the table between these two
    comments, and the parametrize over its rules is empty without them."""
    assert _BLOCK is not None, (
        f"dash.ado has lost {_BEGIN!r} or {_END!r}")
    assert _parse_rules(_BLOCK), "no rule parsed between the sentinels"


@_needs_table
class TestTheTableIsWellFormed:
    def test_the_program_is_inside_the_sentinels(self):
        assert "program define _dash_option_rules" in _BLOCK

    def test_the_contract_tokens_are_all_there(self):
        """The plot and graph rules.  The KPI rule is applied by _dash_kpi
        itself (contract section 2), and is checked with that program."""
        parsed = set(_parse_rules(_BLOCK))
        want = set(_parse_rules(CONTRACT_PLOT_RULES)
                   + _parse_rules(CONTRACT_GRAPH_RULES))
        # 40 since WP-18: mspline's n() is twoway's own 1 to 300 ("n must
        # be between 1 and 300", r(198), measured), so it has a typed token
        # beside the untyped n=int,2,10000 of the other types.  41 since
        # WP-29 P0.9: lpolyci's level() is twoway's 10 to 99.99 ("level()
        # must be between 10 and 99.99 inclusive", r(198), measured).
        # 41 -> 43 (WP-31 C10a, measured: test/fixtures/value_bounds_truth
        # .json): level typed on lfitci, qfitci and fpfitci, which take any
        # number; range typed, with missingok on the four fits; kdensity
        # bwidth 0.
        assert len(want) == 43, "the contract text above lost a token"
        missing = sorted(want - parsed)
        assert not missing, f"contract rules absent from dash.ado: {missing}"

    def test_every_kind_is_one_the_validator_knows(self):
        rules = _parse_rules(_BLOCK)
        assert len(rules) >= 40
        # Every token _dash_validate_opts reads is a rule parsed here -- the
        # exact count, from the table itself (which may carry more than the
        # contract): a token _TOKEN cannot read is a rule no test checks.
        tokens = _table_tokens()
        assert len(tokens) >= 40, tokens
        assert len(rules) == len(tokens), (
            f"{len(tokens)} tokens in the table, {len(rules)} parsed: "
            f"{sorted(set(tokens) - {_unparse(r) for r in rules})}")
        # KINDS is the chain's own list, and every rule names one of them.
        assert KINDS == _validator_kinds(), (
            f"_dash_validate_value branches on {sorted(_validator_kinds())}"
            f", this file says {sorted(KINDS)}")
        bad = [r for r in rules if r[1] not in KINDS]
        assert not bad, bad

    @pytest.mark.parametrize("rule", _parse_rules(_BLOCK or ""),
                             ids=lambda r: r[0] + ("@" + "|".join(r[3])
                                                   if r[3] else ""))
    def test_the_parameters_fit_the_kind(self, rule):
        opt, kind, ps, _ = rule
        if kind == "num":
            assert len(ps) <= 3, rule
            for p in ps[:2]:
                assert p == "" or _is_number(p), rule
            if len(ps) == 3:
                assert ps[2] == "x", rule
        elif kind == "int":
            assert len(ps) <= 2, rule
            for p in ps:
                assert p == "" or _is_integer(p), rule
        elif kind == "pos":
            assert len(ps) <= 1, rule
            for p in ps:
                assert p == "" or _is_number(p), rule
        elif kind in ("style", "istyle"):
            # WP-30 P1.12b: the line-width rules read Stata units (,u)
            if kind == "style" and len(ps) == 3:
                assert ps[2] == "u", rule
                ps = ps[:2]
            assert len(ps) in (0, 2), rule
            for p in ps:
                assert _is_number(p), rule
            if kind == "istyle":
                for p in ps:
                    assert _is_integer(p), rule
        elif kind == "enum":
            assert len(ps) == 1, rule
            words = ps[0].split("|")
            assert words and all(re.fullmatch(r"[a-z][a-z0-9]*", w)
                                 for w in words), rule
        elif kind == "numlist":
            assert 1 <= len(ps) <= 2, rule
            assert _is_integer(ps[0]) and int(ps[0]) >= 1, rule
            if len(ps) == 2:
                assert ps[1] == "" or (
                    _is_integer(ps[1]) and int(ps[1]) >= int(ps[0])), rule
        elif kind == "range":
            # WP-31 C10a: min,max[,m] -- m is twoway's missingok.
            assert len(ps) in (2, 3), rule
            assert _is_integer(ps[0]) and _is_integer(ps[1]), rule
            if len(ps) == 3:
                assert ps[2] == "m", rule
        else:
            assert ps == (), f"{kind} takes no parameters: {rule}"

    def test_a_bounded_rule_has_lo_below_hi(self):
        for opt, kind, ps, _ in _parse_rules(_BLOCK):
            if kind in ("num", "int", "style", "istyle") and len(ps) >= 2 \
                    and ps[0] and ps[1]:
                assert float(ps[0]) < float(ps[1]), (opt, kind, ps)

    def test_every_plot_type_qualifier_is_a_type_dash_draws(self):
        drawn = (set(dr._dash_plot_type_names())
                 | tp._mata_expanded_types() | tp._ado_supported_types())
        for opt, kind, ps, types in _parse_rules(_BLOCK):
            for t in types:
                assert t in drawn, f"{opt}@{t}: no such plot type"

    def test_a_qualified_option_keeps_an_unqualified_fallback_or_not_at_all(
            self):
        """``bwidth=pos,1@lowess`` beside ``bwidth=pos``: the qualified token
        wins for its types and the bare one covers the rest.  Two bare tokens
        for one option would make the table ambiguous."""
        bare = [r[0] for r in _parse_rules(_BLOCK) if not r[3]]
        dupes = sorted({o for o in bare if bare.count(o) > 1})
        assert not dupes, f"two unqualified rules for one option: {dupes}"


@_needs_table
class TestEveryRuledOptionIsOneAParserDeclares:
    """A rule for an option the syntax block does not accept could never
    fire; a rule in the wrong parser's table would fire on the wrong
    command."""

    def _declared(self, program):
        body = _program_body(_ado(), program)
        assert body is not None, program
        return {full for _, full in _syntax_options(body)}

    def test_plot_rules_name_plot_options(self):
        declared = self._declared("_dash_parse_plot_opts")
        plot = sorted({r[0] for r in _parse_rules(_BLOCK)
                       if r[0] not in GRAPH_OPTIONS | KPI_OPTIONS})
        assert plot, "no plot rules parsed"
        undeclared = [o for o in plot if o not in declared]
        assert not undeclared, (
            f"rules for options _dash_parse_plot_opts does not declare: "
            f"{undeclared}")

    def test_graph_rules_name_graph_options(self):
        declared = self._declared("_dash_parse_graph_opts")
        graph = sorted({r[0] for r in _parse_rules(_BLOCK)
                        if r[0] in GRAPH_OPTIONS})
        assert set(graph) == GRAPH_OPTIONS, graph
        undeclared = [o for o in graph if o not in declared]
        assert not undeclared, undeclared

    def test_the_kpi_rule_names_a_kpi_option(self):
        """``fmt=format`` is applied by _dash_kpi directly, through the same
        _dash_validate_value, with the contract's kind."""
        declared = self._declared("_dash_kpi")
        assert KPI_OPTIONS <= declared
        body = _program_body(_ado(), "_dash_kpi")
        calls = re.findall(
            r'_dash_validate_value\s+"dash kpi"\s+"(\w+)"\s+"(\w+)"', body)
        assert ("fmt", "format") in calls, calls
        for opt, kind in calls:
            assert opt in declared and kind in KINDS, (opt, kind)
        assert [r for r in _parse_rules(CONTRACT_KPI_RULES)] == \
            [("fmt", "format", (), ())]


@_needs_table
class TestTheNewProgramsKeepTheirConstraints:
    PROGRAMS = ("_dash_option_rules", "_dash_validate_opts",
                "_dash_validate_value")

    @pytest.mark.parametrize("program", PROGRAMS)
    def test_it_exists(self, program):
        assert _program_body(_ado(), program) is not None, program

    @pytest.mark.parametrize("program", PROGRAMS)
    @pytest.mark.parametrize("forbidden", [
        "foreach gk in", "foreach gkey in", "sreturn clear",
    ])
    def test_it_contains_no_forbidden_text(self, program, forbidden):
        """A structural guard over dash.ado's text, deliberately: the
        validators' charter (no `sreturn clear', no hand-kept graph-key
        list, no Mata validation -- test_its_mata_only_moves_tests_or_echoes
        _text) is a property of their source; the refusals themselves run
        in test_option_validation.cscript."""
        body = _program_body(_ado(), program) or ""
        assert forbidden not in body, f"{program} contains {forbidden!r}"

    #: The Mata functions the validators may call.  Validation is Stata's;
    #: Mata holds character-level helpers only (dash_parse.mata's charter).
    #: _dash_say is the echo: WP-20 routes every echo of the user's text
    #: through it, so a refused value is shown as typed instead of drawn as
    #: SMCL (P20-02..06).  The rest read and hand on the user's text by
    #: value -- _dash_text_args, st_local, st_global, st_strscalar -- or
    #: test its characters -- strtrim, strpos, char, strofreal: in quotes,
    #: in an -args- list or in a Stata expression a value holding "' ended
    #: the quotes, and a copy through them expanded a macro in it again
    #: (24sep2026; test_json_escaping.cscript JSE-46, JSE-47, JSE-69).  No
    #: regular expression and no number parsing: those stay Stata's.
    _MATA_ALLOWED = frozenset({
        "_dash_say", "_dash_text_args", "st_local", "st_global",
        "st_strscalar", "strofreal", "strtrim", "strpos", "char",
        # WP-30 P1.5: _dash_axis_fmts reads format() words by value and
        # tests their characters; _dash_imm_echo cuts an echo at 80.
        "_dash_axis_fmts", "_dash_imm_echo",
    })

    @staticmethod
    def _mata_calls(body):
        """[(statement, [function, ...]), ...] for every `mata:' line in
        `body', continuation lines joined, string literals left out."""
        out = []
        lines = body.split("\n")
        i = 0
        while i < len(lines):
            ln = lines[i].strip()
            i += 1
            if not ln.startswith("mata:"):
                continue
            stmt = ln
            while stmt.endswith("///") and i < len(lines):
                stmt = stmt[:-3] + " " + lines[i].strip()
                i += 1
            code = re.sub(r'"[^"]*"', '""', stmt[len("mata:"):])
            out.append((stmt, re.findall(r"\b([A-Za-z_]\w*)\s*\(", code)))
        return out

    @pytest.mark.parametrize("program", PROGRAMS)
    def test_its_mata_only_moves_tests_or_echoes_text(self, program):
        """A structural guard over dash.ado's text, deliberately (the
        charter above): every Mata call in a validator moves the user's
        text by value, tests its characters or echoes it."""
        body = _program_body(_ado(), program) or ""
        bad = ["%s: %s" % (sorted(set(fns) - self._MATA_ALLOWED), stmt)
               for stmt, fns in self._mata_calls(body)
               if set(fns) - self._MATA_ALLOWED]
        assert not bad, "%s calls Mata beyond the charter:\n  %s" % (
            program, "\n  ".join(bad))

    def test_the_charter_scan_sees_what_it_looks_for(self):
        """The scan above is vacuous if it finds no Mata, or cannot tell a
        forbidden call inside an allowed one."""
        body = _program_body(_ado(), "_dash_validate_value") or ""
        found = self._mata_calls(body)
        fns = {f for _, calls in found for f in calls}
        # The echo and the by-value reading are there (measured 24sep2026).
        assert {"_dash_say", "_dash_text_args", "st_strscalar"} <= fns, fns
        # A validation hidden inside an allowed call is still seen, and a
        # function named inside a message is not one.
        probe = ('    mata: st_local("ok", strofreal(regexm(st_local("v"), ///\n'
                 '        "^[0-9]+$")))\n'
                 '    mata: _dash_say("err", "x() must be a number (got: ", '
                 'st_local("value"), ")")')
        calls = [c for _, c in self._mata_calls(probe)]
        assert calls == [["st_local", "strofreal", "regexm", "st_local"],
                         ["_dash_say", "st_local"]], calls

    def test_the_validator_still_echoes_through_say(self):
        """The refusals echo the user's text through _dash_say, whose
        behaviour is P20-02..06."""
        body = _program_body(_ado(), "_dash_validate_value") or ""
        calls = re.findall(r"mata:\s*(\w+)\(", body)
        assert "_dash_say" in calls, calls

    @pytest.mark.parametrize("program", PROGRAMS)
    def test_it_has_no_syntax_line(self, program):
        """A structural guard over dash.ado's text, deliberately: the
        validators take positional arguments, never `syntax', which would
        re-parse the user's value (the charter above)."""
        body = _program_body(_ado(), program) or ""
        lines = [ln for ln in body.split("\n")
                 if re.match(r"^\s*syntax\b", ln)]
        assert not lines, f"{program} has a syntax line: {lines}"

    def test_the_validators_are_called(self):
        src = _ado()
        for name in ("_dash_option_rules", "_dash_validate_opts",
                     "_dash_validate_value"):
            calls = [m.start() for m in re.finditer(r"\b%s\b" % name, src)]
            defn = src.index("program define " + name)
            assert [c for c in calls if c != defn + len("program define ")], (
                f"{name} is defined but never called")

    def test_validate_opts_follows_fold_bw(self):
        src = _ado()
        # WP-30 P1.8a: both read the type connect() makes (_cn_ptype).
        # Flipped (WP-30 P1.8b): both read _rc_own, which is _cn_ptype but
        # a derived layer's own type under recast() (a recast lfit's
        # options are still lfit's), where _cn_ptype was wrong because the
        # recast target would judge them (recast_truth.json).
        i = src.index('_dash_fold_bw "`_rc_own\'"')
        j = src.index('_dash_validate_opts "`_rc_own\'"')
        assert i < j, "_dash_validate_opts must run after _dash_fold_bw"

    def test_the_old_level_text_is_gone_from_the_plot_parser(self):
        body = _program_body(_ado(), "_dash_parse_plot_opts")
        assert "level() must be a number between 0 and 100" not in body
        assert "level() must be between 0 and 100 (exclusive)" not in body

    def test_kpi_validates_fmt_before_it_displays(self):
        body = _program_body(_ado(), "_dash_kpi")
        # On its own line, in a block: a one-line `if exp command' expands
        # its command a second time, so fmt(\$m) reached the validator as
        # what $m holds (measured 24sep2026, JSE-58).
        call = re.search(r'^\s*_dash_validate_value "dash kpi" "fmt"', body,
                         re.M)
        assert call, (
            "_dash_kpi does not validate fmt() through _dash_validate_value")
        # The formatter itself, not a comment that mentions it.
        shown = re.search(r"^\s*local \w+\s*:\s*display\b", body, re.M)
        assert shown, "_dash_kpi no longer formats through `: display'"
        assert call.start() < shown.start()
        # Contract section 2: no fmt() test puts the value inside quotes,
        # where a quote in it could end them early.  It was compound-quoted;
        # since 24sep2026 fmt() is measured by length and both the check and
        # the display site test the length.
        length = re.search(r"^\s*local (\w+)\s*:\s*length local fmt\s*$",
                           body, re.M)
        assert length, "fmt() is no longer measured by length"
        guards = [m.start() for m in re.finditer(
            r"^\s*if `%s' > 0 \{\s*$" % re.escape(length.group(1)), body,
            re.M)]
        assert any(g < call.start() for g in guards), (
            "the fmt() check is not guarded by its length")
        assert any(call.start() < g < shown.start() for g in guards), (
            "the fmt() display site is not guarded by its length")
        assert not re.search(r'"`fmt\'"', body), (
            "a fmt() test puts the value inside quotes")

    def test_no_message_calls_a_refused_value_unsupported(self):
        """test_option_surface counts 'unsupported option' lines as the
        drop note; a refusal must not be mistaken for one."""
        for program in self.PROGRAMS:
            body = _program_body(_ado(), program) or ""
            assert "unsupported option" not in body, program
            assert "ignoring unsupported" not in body, program


# ---------------------------------------------------------------------------
# (b), (c), (d): the renderer, in both modes
# ---------------------------------------------------------------------------

#: The parity frame in test_mode_parity has no string variable, and the
#: cases below label with one (``mlabel(make)``), so the two modes are
#: rendered here the way test_suboption_warnings._both renders them, over a
#: frame that has ``make``.
_DF = pd.DataFrame({
    "mpg": [22.0, 17.0, 25.0, 30.0, 21.0, 19.0, 14.0, 28.0, 16.0, 23.0],
    "weight": [2930.0, 3350.0, 2200.0, 1800.0, 3000.0, 3100.0, 4080.0,
               2010.0, 3600.0, 2650.0],
    "foreign": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
    "price": [4099.0, 4749.0, 3799.0, 4816.0, 5788.0, 4453.0, 5189.0,
              10372.0, 4082.0, 11385.0],
    "make": ["AMC Concord", "AMC Pacer", "AMC Spirit", "Buick Century",
             "Buick Electra", "Buick LeSabre", "Buick Opel", "Buick Regal",
             "Buick Riviera", "Buick Skylark"],
})
_SEQ = itertools.count()
_TMP = tempfile.mkdtemp(prefix="dash_optval_")


def _write(spec):
    tag = next(_SEQ)
    sp = os.path.join(_TMP, f"spec_{tag}.json")
    dp = os.path.join(_TMP, f"data_{tag}.json")
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    data = make_data_json(_DF)
    # make_data_json marks every column numeric; real jsonio marks make as
    # a string, and the served app coerces an unmarked column to NaN.
    for key in ("variableIsString", "variableTypeIsString"):
        data["StataJSON"][key]["make"] = True
    with open(dp, "w") as fh:
        json.dump(data, fh)
    return tag, sp, dp


def _both(plots, go=None, kpis=None):
    """(renderer, document, standalone warnings, served warnings)."""
    spec = tp._spec(plots, None, go, kpis=kpis)
    _, sp, dp = _write(spec)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r = dr.DashRenderer(sp, dp)
        render_models(r)
    std_w = sorted(str(w.message) for w in caught)

    tag, sp, dp = _write(spec)
    ap = os.path.join(_TMP, f"app_{tag}.py")
    with warnings.catch_warnings(record=True) as built:
        warnings.simplefilter("always")
        dr.ServerAppBuilder(sp, dp).build(ap)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mod = load_app(ap, f"_optval_{tag}")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        doc = Document()
        mod.make_document(doc)
    srv_w = sorted(str(w.message) for w in list(built) + list(caught))
    return r, doc, std_w, srv_w


def _naming(warnings_, option):
    return [w for w in warnings_ if f"{option}(" in w]


def _the_one(std_w, srv_w, option):
    """The single warning naming *option*, identical in both modes."""
    assert std_w == srv_w, (option, std_w, srv_w)
    hits = _naming(std_w, option)
    assert len(hits) == 1, (
        f"expected exactly one warning naming {option}(), got {hits} "
        f"in {std_w}")
    return hits[0]


STYLE_CASES = [
    # (plot type, options, the option the one warning must name)
    ("scatter", {"mcolor": "notacolour"}, "mcolor"),
    ("scatter", {"mfcolor": "notacolour"}, "mfcolor"),
    ("scatter", {"mlcolor": "notacolour"}, "mlcolor"),
    ("line", {"lcolor": "notacolour"}, "lcolor"),
    ("area", {"fcolor": "notacolour"}, "fcolor"),
    ("scatter", {"mlabel": "make", "mlabcolor": "notacolour"}, "mlabcolor"),
    ("scatter", {"msymbol": "nonsense"}, "msymbol"),
    ("scatter", {"marker": "nonsense"}, "marker"),
    ("scatter", {"msize": "abc"}, "msize"),
    # WP-30 P1.12a (E5): twoway reads msize(*2) as a relative size, so it
    # draws without a note; msize(Large) is still unknown (names are
    # case-sensitive in twoway).  The row was {"msize": "*2"}.
    ("scatter", {"msize": "Large"}, "msize"),
    ("scatter", {"mlabel": "make", "mlabsize": "abc"}, "mlabsize"),
    ("scatter", {"mlabel": "make", "mlabgap": "abc"}, "mlabgap"),
    ("scatter", {"lwidth": "abc"}, "lwidth"),
    ("scatter", {"mlwidth": "abc"}, "mlwidth"),
    ("line", {"lpattern": "bogus"}, "lpattern"),
    ("scatter", {"msangle": "abc"}, "msangle"),
    ("area", {"fintensity": "abc"}, "fintensity"),
    ("scatter", {"mlabel": "make", "mlabposition": "13"}, "mlabposition"),
    # The bar-specific colours, which the contract lists with the others.
    ("bar", {"bfcolor": "notacolour"}, "bfcolor"),
    ("bar", {"blcolor": "notacolour"}, "blcolor"),
    ("rbar", {"bfcolor": "notacolour"}, "bfcolor"),
    ("rbar", {"blcolor": "notacolour"}, "blcolor"),
]


def _case_id(c):
    ptype, opts, opt = c
    return f"{ptype} {opt}({opts[opt]})"


@pytest.mark.parametrize("ptype,opts,option", STYLE_CASES,
                         ids=[_case_id(c) for c in STYLE_CASES])
class TestAnUnknownStyleNameIsNamedOnceInBothModes:
    def test_one_note_naming_the_option(self, ptype, opts, option):
        r, doc, std_w, srv_w = _both([plot_for(ptype, opts)])
        line = _the_one(std_w, srv_w, option)
        assert line.startswith(f"dash: {option}({opts[option]}) is not a "
                               f"recognised "), line
        assert "; using " in line, line

    def test_the_layer_is_still_drawn(self, ptype, opts, option):
        r, doc, _, _ = _both([plot_for(ptype, opts)])
        fig = list(r.figures.values())[0]
        assert fig.renderers, "the saved figure drew nothing"
        srv = [m for m in tp._walk_models(doc)
               if type(m).__name__ == "figure"]
        assert srv and srv[0].renderers, "the served figure drew nothing"


class TestTheDefaultIsWhatTheSchemeGives:
    def test_a_bad_msymbol_draws_the_schemes_symbol(self):
        r, _, _, _ = _both([plot_for("scatter", {"msymbol": "nonsense"})])
        fig = list(r.figures.values())[0]
        assert fig.renderers[0].glyph.marker == \
            r.mapper.scheme.default_symbol(0)

    def test_a_bad_msize_draws_the_schemes_size(self):
        r, _, _, _ = _both([plot_for("scatter", {"msize": "abc"})])
        fig = list(r.figures.values())[0]
        assert float(fig.renderers[0].glyph.size) == float(
            r.mapper.scheme.default_marker_size(0))

    def test_a_bad_mcolor_draws_black(self):
        """Flipped (WP-30 P1.13a): twoway draws mcolor(bogus) black with a
        note (colour_grammar_truth.json opt_87); this drew p1."""
        r, _, _, _ = _both([plot_for("scatter", {"mcolor": "notacolour"})])
        fig = list(r.figures.values())[0]
        assert fig.renderers[0].glyph.fill_color == "#000000"

    def test_a_bad_clock_position_labels_at_twelve_oclock(self):
        """Where twoway draws it: measured (test_help_claims_5.cscript
        HC5-03), mlabposition(13) is noted and drawn at 12 o'clock under
        every scheme measured.  This asserted 3 o'clock, where dash drew
        it."""
        r, _, _, _ = _both([plot_for("scatter", {"mlabel": "make",
                                                 "mlabposition": "13"})])
        fig = list(r.figures.values())[0]
        ls = [x for x in fig.center if isinstance(x, LabelSet)]
        assert len(ls) == 1
        # WP-30 P1.12a: twoway's mlabgap default is 1.4 % of the 4-inch
        # reference, 5.6 px (it was 4); approx absorbs the 4e-6 px the
        # point-to-pixel constant carries.
        assert (ls[0].x_offset, ls[0].y_offset) == (0, pytest.approx(5.6, abs=1e-4))
        assert (ls[0].text_align, ls[0].text_baseline) == ("center",
                                                           "bottom")


class TestAGoodValueIsSilent:
    @pytest.mark.parametrize("ptype,opts", [
        ("scatter", {"mcolor": "navy%50", "msymbol": "Oh", "msize": "large",
                     "msangle": "45", "mlwidth": "thin", "mlcolor": "red"}),
        ("scatter", {"mlabel": "make", "mlabcolor": "maroon",
                     "mlabsize": "small", "mlabgap": "2",
                     "mlabposition": "12"}),
        ("line", {"lcolor": "242 194 44", "lwidth": "0", "lpattern": "dash"}),
        ("area", {"fcolor": "ltblue", "fintensity": "inten40"}),
        ("area", {"fcolor": "ltblue", "fintensity": "60"}),
        ("scatteri", {"msize": "3", "msymbol": "triangle"}),
        ("dropline", {"jitter": "5", "jitterseed": "20260920"}),
        ("scatter", {"jitter": "4", "jseed": "0"}),
    ])
    def test_no_style_note(self, ptype, opts):
        _, _, std_w, srv_w = _both([plot_for(ptype, opts)])
        assert std_w == srv_w
        noisy = [w for w in std_w
                 if "is not a recognised" in w or "must be" in w
                 or "is not a number" in w]
        assert not noisy, noisy


# ---- (c) the three aborts --------------------------------------------------

class TestABadValueNoLongerAbortsTheRender:
    def test_scatteri_msize(self):
        r, doc, std_w, srv_w = _both([plot_for("scatteri", {"msize": "abc"})])
        _the_one(std_w, srv_w, "msize")
        fig = list(r.figures.values())[0]
        assert fig.renderers and float(fig.renderers[0].glyph.size) == float(
            r.mapper.scheme.default_marker_size(0))

    def test_scatteri_msymbol(self):
        r, doc, std_w, srv_w = _both(
            [plot_for("scatteri", {"msymbol": "nonsense"})])
        _the_one(std_w, srv_w, "msymbol")
        fig = list(r.figures.values())[0]
        assert fig.renderers and fig.renderers[0].glyph.marker == "circle"

    def test_dropline_jitter(self):
        r, doc, std_w, srv_w = _both(
            [plot_for("dropline", {"jitter": "abc"})])
        line = _the_one(std_w, srv_w, "jitter")
        assert "is not a number" in line, line
        fig = list(r.figures.values())[0]
        assert len(fig.renderers) == 2, "dropline draws a segment and a dot"

    def test_negative_jitterseed(self):
        r, doc, std_w, srv_w = _both(
            [plot_for("scatter", {"jitter": "5", "jitterseed": "-1"})])
        line = _the_one(std_w, srv_w, "jitterseed")
        assert line == ("dash: jitterseed(-1) must be a non-negative "
                        "integer; drawing unseeded."), line
        fig = list(r.figures.values())[0]
        # G1 (WP-28): the jitter columns are named under the __dash prefix.
        assert fig.renderers[0].glyph.x == dr._DASH_JITTER_X, \
            "the jitter was drawn"

    def test_fractional_jitterseed(self):
        r, doc, std_w, srv_w = _both(
            [plot_for("scatter", {"jitter": "5", "jitterseed": "2.5"})])
        line = _the_one(std_w, srv_w, "jitterseed")
        assert line == ("dash: jitterseed(2.5) must be a non-negative "
                        "integer; drawing unseeded."), line


class TestTheSeedReader:
    def _seed(self, options):
        # Outside a render nothing clears the once-per-render set, and an
        # earlier render in this process may have named the same seed.
        dr._dash_reset_notes()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            val = dr._jitter_seed(options)
        return val, [str(w.message) for w in caught]

    @pytest.mark.parametrize("options,seed", [
        ({"jitterseed": "7"}, 7), ({"jseed": "0"}, 0),
        ({"jitterseed": "20260920"}, 20260920), ({}, None),
        ({"jitterseed": ""}, None), ({"jitterseed": " 12 "}, 12),
        # Every spelling of a non-negative integer, as dash.ado's rule
        # (jitterseed=int,0) reads it: 1e3 and 123.0 are integers too.
        ({"jseed": "1e3"}, 1000), ({"jitterseed": "123.0"}, 123),
    ])
    def test_a_good_seed_is_read_silently(self, options, seed):
        assert self._seed(options) == (seed, [])

    @pytest.mark.parametrize("key,raw", [
        ("jitterseed", "-1"), ("jitterseed", "2.5"), ("jitterseed", "abc"),
        ("jseed", "-3"), ("jseed", "inf"), ("jitterseed", "5); import os"),
    ])
    def test_a_bad_seed_is_named_and_dropped(self, key, raw):
        val, warned = self._seed({key: raw})
        assert val is None
        assert warned == [f"dash: {key}({raw}) must be a non-negative "
                          f"integer; drawing unseeded."]

    def test_jseed_wins_over_jitterseed(self):
        assert self._seed({"jseed": "3", "jitterseed": "9"}) == (3, [])


# ---- (d) mlabel with several names ---------------------------------------

class TestMlabelWithSeveralNamesUsesTheFirst:
    def _labelsets(self, fig):
        return [x for x in fig.center if isinstance(x, LabelSet)]

    def test_labels_come_from_the_first_and_the_rest_are_named(self):
        r, doc, std_w, srv_w = _both(
            [plot_for("scatter", {"mlabel": "make foreign"})])
        line = _the_one(std_w, srv_w, "mlabel")
        assert "make" in line and "foreign" in line, line
        fig = list(r.figures.values())[0]
        ls = self._labelsets(fig)
        assert len(ls) == 1 and ls[0].text == "make", ls
        srv = [m for m in tp._walk_models(doc)
               if type(m).__name__ == "figure"][0]
        sls = self._labelsets(srv)
        assert len(sls) == 1 and sls[0].text == "make", sls
        assert list(sls[0].source.data["make"]) == list(_DF["make"])

    def test_three_names_are_all_reported(self):
        _, _, std_w, srv_w = _both(
            [plot_for("scatter", {"mlabel": "make foreign price"})])
        line = _the_one(std_w, srv_w, "mlabel")
        assert "foreign" in line and "price" in line, line

    def test_a_single_name_is_silent(self):
        _, _, std_w, srv_w = _both([plot_for("scatter", {"mlabel": "make"})])
        assert std_w == srv_w
        assert not _naming(std_w, "mlabel"), std_w

    def test_a_line_plot_draws_no_label_and_says_nothing(self):
        """twoway accepts mlabel() on a line -- ``line y x, mlabel(zl t)``
        included -- and draws no label, without a note (measured 23sep2026);
        so there is nothing to label "from the first", and nothing to name.
        This used to assert the line was labelled from make."""
        r, doc, std_w, srv_w = _both(
            [plot_for("line", {"mlabel": "make foreign"})])
        assert std_w == srv_w and not _naming(std_w, "mlabel"), std_w
        fig = list(r.figures.values())[0]
        assert self._labelsets(fig) == []
        srv = [m for m in tp._walk_models(doc)
               if type(m).__name__ == "figure"][0]
        assert self._labelsets(srv) == []


# ---- the helpers themselves ------------------------------------------------

class TestTheNoteHelper:
    def test_its_wording(self):
        dr._dash_reset_notes()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr._dash_style_note("mcolor", "notacolour", "colour")
            dr._dash_style_note("mlabposition", "13", "clock position",
                                "12 (above)")
        assert [str(w.message) for w in caught] == [
            "dash: mcolor(notacolour) is not a recognised colour; using "
            "the scheme's default.",
            "dash: mlabposition(13) is not a recognised clock position; "
            "using 12 (above).",
        ]

    def test_parse_color_alpha_notes_only_when_told_the_option(self):
        dr._dash_reset_notes()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            # Flipped (WP-30 P1.13a): an unknown colour is black, its own
            # opacity kept, as twoway draws mcolor(bogus%50); it was
            # (None, None) and the caller's scheme colour.
            assert dr.OptionTranslator.parse_color_alpha("notacolour") == \
                ("#000000", None)
            assert dr.OptionTranslator.parse_color_alpha("navy%40") == \
                ("#1a476f", 0.4)
        assert not caught
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            assert dr.OptionTranslator.parse_color_alpha(
                "notacolour%40", "fcolor") == ("#000000", 0.4)
        assert [str(w.message) for w in caught] == [
            "dash: fcolor(notacolour%40) is not a recognised colour; using "
            "black."]

    def test_the_translators_still_raise(self):
        """test_options.py pins these; the notes are raised by the callers."""
        tr = dr.OptionTranslator
        for fn, bad in ((tr.translate_mcolor, "notacolour"),
                        (tr.translate_msymbol, "nonsense"),
                        (tr.translate_msize, "abc"),
                        (tr.translate_lwidth, "abc"),
                        (tr.translate_lpattern, "bogus")):
            with pytest.raises(ValueError):
                fn(bad)

    def test_the_helper_travels_to_the_served_app(self, tmp_path):
        spec = tp._spec([plot_for("scatter")])
        _, sp, dp = _write(spec)
        ap = str(tmp_path / "app.py")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(ap)
        with open(ap, encoding="utf-8") as fh:
            src = fh.read()
        assert "def _dash_style_note(" in src
        assert "def _dash_mlabel_names(" in src


# ---- (f) the adversarial review's amendments (DESIGN.md section 7.2) -------
#
# Measured after the first cut (review_result.json, "renderer"): two style
# values still aborted a render (plotregion(lwidth(abc)) standalone,
# msize(1e400) in both modes), one bad option was reported twice or four
# times (connected's line and marker border, rcapsym's two dots, every by()
# panel), and a handful of sites were still `except ...: pass' -- area
# color(), the four graph-level colours, xline() sub-options, legend(size()),
# a KPI's colour -- or silent only when served (xsize/ysize/aspectratio).


def _the_one_reading(std_w, srv_w, text):
    """The single warning containing *text*, identical in both modes."""
    assert std_w == srv_w, (text, std_w, srv_w)
    hits = [w for w in std_w if text in w]
    assert len(hits) == 1, f"expected exactly one warning reading {text!r}, got {hits} in {std_w}"
    return hits[0]


def _figures(r, doc):
    """(saved figure, served figure) of a one-graph spec."""
    std = list(r.figures.values())[0]
    srv = [m for m in tp._walk_models(doc) if type(m).__name__ == "figure"][0]
    return std, srv


class TestOneNotePerOptionPerRender:
    """B3: one note per (option, value, what) per render, in both modes."""

    @pytest.mark.parametrize("go", [None, {"by": "foreign"}],
                             ids=["no by()", "by(foreign)"])
    def test_connected_lcolor(self, go):
        # The connecting line AND the marker border read lcolor(); each
        # noted it, and each by() panel noted it again: four lines.
        _, _, std_w, srv_w = _both(
            [plot_for("connected", {"lcolor": "notacolour"})], go)
        line = _the_one(std_w, srv_w, "lcolor")
        assert line.startswith("dash: lcolor(notacolour) is not a recognised colour")

    @pytest.mark.parametrize("opts,option", [
        ({"lwidth": "abc"}, "lwidth"), ({"color": "notacolour"}, "color"),
    ], ids=["lwidth", "color"])
    def test_connected_line_options(self, opts, option):
        _, _, std_w, srv_w = _both([plot_for("connected", opts)])
        line = _the_one(std_w, srv_w, option)
        assert line.startswith(f"dash: {option}({opts[option]}) is not a recognised")

    def test_scatter_mcolor_under_by(self):
        _, _, std_w, srv_w = _both(
            [plot_for("scatter", {"mcolor": "notacolour"})], {"by": "foreign"})
        _the_one(std_w, srv_w, "mcolor")

    def test_rcapsym_mcolor(self):
        # Two dot renderers, one note.
        _, _, std_w, srv_w = _both([plot_for("rcapsym", {"mcolor": "notacolour"})])
        _the_one(std_w, srv_w, "mcolor")

    def test_a_bad_seed_under_by(self):
        _, _, std_w, srv_w = _both(
            [plot_for("scatter", {"jitter": "5", "jitterseed": "-1"})],
            {"by": "foreign"})
        _the_one(std_w, srv_w, "jitterseed")

    def test_mlabposition_under_by(self):
        _, _, std_w, srv_w = _both(
            [plot_for("scatter", {"mlabel": "make", "mlabposition": "13"})],
            {"by": "foreign"})
        _the_one(std_w, srv_w, "mlabposition")

    def test_two_layers_with_the_same_mistake_are_one_note(self):
        _, _, std_w, srv_w = _both([plot_for("scatter", {"mcolor": "notacolour"}),
                                    plot_for("line", {"lcolor": "notacolour"},
                                             yvar="price")])
        _the_one(std_w, srv_w, "mcolor")
        _the_one(std_w, srv_w, "lcolor")

    def test_the_helper_dedups_until_reset(self):
        dr._dash_reset_notes()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr._dash_style_note("mcolor", "notacolour", "colour")
            dr._dash_style_note("mcolor", "notacolour", "colour")
            dr._dash_style_note("mcolor", "notacolour", "size")
            dr._dash_reset_notes()
            dr._dash_style_note("mcolor", "notacolour", "colour")
        assert [str(w.message) for w in caught] == [
            "dash: mcolor(notacolour) is not a recognised colour; using the scheme's default.",
            "dash: mcolor(notacolour) is not a recognised size; using the scheme's default.",
            "dash: mcolor(notacolour) is not a recognised colour; using the scheme's default.",
        ]

    def test_every_render_starts_afresh(self):
        # The set is module state; the second render of the same mistake
        # must name it again.  Both modes.
        for _ in range(2):
            _, _, std_w, srv_w = _both([plot_for("scatter", {"mcolor": "notacolour"})])
            _the_one(std_w, srv_w, "mcolor")

    def test_the_set_and_the_reset_travel_to_the_served_app(self, tmp_path):
        spec = tp._spec([plot_for("scatter")])
        _, sp, dp = _write(spec)
        ap = str(tmp_path / "app.py")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(ap)
        with open(ap, encoding="utf-8") as fh:
            src = fh.read()
        assert re.search(r"^_DASH_NOTED = set\(\)$", src, re.M), (
            "the app has no module-level _DASH_NOTED")
        assert "def _dash_reset_notes(" in src
        body = src[src.index("def make_document(doc):"):]
        assert "_dash_reset_notes()" in body, (
            "make_document does not reset the once-per-render set")


class TestABadStyleValueNeverAborts:
    """B1, B2: the two aborts the review found."""

    def test_plotregion_lwidth(self):
        r, doc, std_w, srv_w = _both([plot_for("scatter")],
                                     {"plotregion": "lwidth(abc)"})
        line = _the_one_reading(std_w, srv_w, "plotregion(lwidth(abc))")
        assert line == ("dash: plotregion(lwidth(abc)) is not a recognised "
                        "line width; using the default."), line
        std, srv = _figures(r, doc)
        assert std.renderers and srv.renderers

    def test_a_good_plotregion_lwidth_is_honoured_in_both_modes(self):
        r, doc, std_w, srv_w = _both([plot_for("scatter")],
                                     {"plotregion": "lwidth(thick)"})
        assert std_w == srv_w
        assert not [w for w in std_w if "plotregion" in w], std_w
        std, srv = _figures(r, doc)
        assert float(std.outline_line_width) == float(srv.outline_line_width) \
            == dr.OptionTranslator.translate_lwidth("thick")

    @pytest.mark.parametrize("ptype,opts,option", [
        ("scatter", {"msize": "1e400"}, "msize"),
        ("scatter", {"msize": "inf"}, "msize"),
        ("scatter", {"msize": "nan"}, "msize"),
        ("line", {"lwidth": "1e400"}, "lwidth"),
        ("line", {"lwidth": "-inf"}, "lwidth"),
        ("scatter", {"mlabel": "make", "mlabsize": "1e400"}, "mlabsize"),
        ("scatter", {"mlabel": "make", "mlabgap": "1e400"}, "mlabgap"),
    ], ids=lambda v: v if isinstance(v, str) else "")
    def test_a_non_finite_size_or_width(self, ptype, opts, option):
        # float('1e400') is inf, int(inf) is OverflowError -- which no
        # `except ValueError' caught, in either mode.
        r, doc, std_w, srv_w = _both([plot_for(ptype, opts)])
        line = _the_one(std_w, srv_w, option)
        assert line.startswith(f"dash: {option}({opts[option]}) is not a recognised")
        std, srv = _figures(r, doc)
        assert std.renderers and srv.renderers

    @pytest.mark.parametrize("fn", ["translate_msize", "translate_lwidth"])
    @pytest.mark.parametrize("bad", ["1e400", "inf", "-inf", "nan"])
    def test_the_translators_refuse_a_non_finite_number(self, fn, bad):
        with pytest.raises(ValueError):
            getattr(dr.OptionTranslator, fn)(bad)


class TestTheRemainingSilentSites:
    """B4, B5, B6: every `except ...: pass' around a style name is a note."""

    def test_area_color(self):
        r, doc, std_w, srv_w = _both([plot_for("area", {"color": "notacolour"})])
        line = _the_one(std_w, srv_w, "color")
        assert line.startswith("dash: color(notacolour) is not a recognised colour")
        std, srv = _figures(r, doc)
        # Flipped (WP-30 P1.13b): the scheme's #486c8c was wrong because
        # twoway draws an unknown area colour black at the area's
        # intensity, #333333 (bare_intensity_truth.json U02).
        assert std.renderers[0].glyph.fill_color == "#333333"

    @pytest.mark.parametrize("ptype", ["bar", "histogram"])
    def test_bar_color_beside_blcolor(self, ptype):
        # The color() pre-read was `pass', and the fold that would have
        # named it is skipped when blcolor() is given.
        _, _, std_w, srv_w = _both(
            [plot_for(ptype, {"color": "notacolour", "blcolor": "red"})])
        line = _the_one(std_w, srv_w, "color")
        assert line.startswith("dash: color(notacolour) is not a recognised colour")

    @pytest.mark.parametrize("go,text,prop", [
        # Flipped (WP-30 P1.20a): bgcolor() on the border was wrong because
        # twoway paints bgcolor() under the graph region (region_truth.json D26-D29); graphregion(color(none)) shows it.
        ({"bgcolor": "notacolour", "graphregion": "color(none)"},
         "bgcolor(notacolour)", "border_fill_color"),
        ({"plotbgcolor": "notacolour"}, "plotbgcolor(notacolour)",
         "background_fill_color"),
        ({"plotregion": "color(notacolour)"}, "plotregion(color(notacolour))",
         "background_fill_color"),
        ({"plotregion": "lcolor(notacolour)"}, "plotregion(lcolor(notacolour))",
         "outline_line_color"),
        ({"graphregion": "color(notacolour)"}, "graphregion(color(notacolour))",
         "border_fill_color"),
    ], ids=lambda v: v if isinstance(v, str) and "(" in v else "")
    def test_a_graph_level_colour(self, go, text, prop):
        r, doc, std_w, srv_w = _both([plot_for("scatter")], go)
        line = _the_one_reading(std_w, srv_w, text)
        # Flipped (WP-30 P1.13a): twoway draws graphregion(color(bogus))
        # black (colour_grammar_truth.json site_08); dash kept the scheme's.
        assert line == f"dash: {text} is not a recognised colour; using black.", line
        std, srv = _figures(r, doc)
        assert getattr(std, prop) == getattr(srv, prop) == "#000000", prop
        assert std.background_fill_color == srv.background_fill_color
        assert std.border_fill_color == srv.border_fill_color
        assert std.outline_line_color == srv.outline_line_color

    def test_a_good_graph_level_colour_is_silent_and_honoured(self):
        r, doc, std_w, srv_w = _both([plot_for("scatter")], {
            "bgcolor": "ltblue", "plotregion": "lcolor(navy%50)",
            "graphregion": "color(gs14)"})
        assert std_w == srv_w
        assert not [w for w in std_w if "recognised colour" in w], std_w
        std, srv = _figures(r, doc)
        # Flipped (WP-30 P1.20a): "graphregion(color()) is applied after
        # bgcolor(), so it wins" was wrong because twoway paints bgcolor() under the graph region (region_truth.json D26-D29):
        # the graph region is drawn over the canvas.
        assert std.border_fill_color == srv.border_fill_color == \
            dr.OptionTranslator.translate_mcolor("gs14")
        r2, doc2, _, _ = _both([plot_for("scatter")], {"bgcolor": "ltblue"})
        std2, srv2 = _figures(r2, doc2)
        assert std2.border_fill_color == srv2.border_fill_color == \
            dr.SchemeParser("s2color").background_color
        assert std.outline_line_color == srv.outline_line_color == "#1a476f"

    @pytest.mark.parametrize("sub,what,using", [
        ("lpattern(bogus)", "line pattern", "the default"),
        ("lwidth(abc)", "line width", "the default"),
        # Flipped (WP-30 P1.13a): twoway draws yline(25, lcolor(bogus))
        # black; dash kept the scheme's xyline colour.
        ("lcolor(notacolour)", "colour", "black"),
    ], ids=["lpattern", "lwidth", "lcolor"])
    def test_a_reference_line_sub_option(self, sub, what, using):
        r, doc, std_w, srv_w = _both([plot_for("scatter")],
                                     {"xline": f"3000, {sub}"})
        line = _the_one_reading(std_w, srv_w, f"xline({sub})")
        assert line == f"dash: xline({sub}) is not a recognised {what}; using {using}.", line
        from bokeh.models import Span
        std, srv = _figures(r, doc)
        for fig in (std, srv):
            spans = [x for x in fig.center if isinstance(x, Span)]
            assert len(spans) == 1 and spans[0].location == 3000.0
            if sub.startswith("lcolor"):
                assert spans[0].line_color == "#000000"

    def test_legend_size(self):
        _, _, std_w, srv_w = _both([plot_for("scatter"), plot_for("lfit")],
                                   {"legend": "size(abc)"})
        line = _the_one_reading(std_w, srv_w, "legend(size(abc))")
        # WP-30 P1.12a: twoway draws an unknown size as medium (11 pt), so
        # the note says "using medium." (it said "the scheme's default").
        assert line == ("dash: legend(size(abc)) is not a recognised size; "
                        "using medium."), line

    @staticmethod
    def _kpi_texts(r, doc):
        std_text = "\n".join(getattr(v, "text", "") for v in r.kpi_divs.values())
        srv_text = "\n".join(getattr(m, "text", "") for m in tp._walk_models(doc)
                             if type(m).__name__ == "Div" and "kpi_val_" in
                             str(getattr(m, "text", "")))
        return std_text, srv_text

    def test_a_kpi_colour(self):
        """The default a refused color() falls back to is the scheme's
        ``color text`` (WP-16: the card is Stata's legend box), in both
        modes.  This used to pin the ``#212529`` literal."""
        r, doc, std_w, srv_w = _both([plot_for("scatter")],
                                     kpis=[tp._kpi(color="notacolour")])
        line = _the_one_reading(std_w, srv_w, "color(notacolour)")
        assert line == ("dash kpi: color(notacolour) is not a recognised "
                        "colour; using the default."), line
        # The default, sanitised, in both cards.
        want = r.scheme.text_color.lower()
        for text in self._kpi_texts(r, doc):
            value = re.search(r'id="kpi_val_k1"\s+style="([^"]*)"', text)
            assert value, text[:300]
            colour = re.search(r"(?:^|[;\s])color\s*:\s*([^;]+)",
                               value.group(1))
            assert colour and colour.group(1).strip().lower() == want, (
                value.group(1))

    def test_a_kpi_bgcolour_falls_back_to_the_schemes_card(self):
        """WP-16: a refused bgcolor() is reported and then NOT replaced by
        an inline default.  The card carries no inline background at all;
        the scheme's legend box colours reach it through the .db-kpi-card
        class rule.  This used to assert ``background:#f8f9fa`` inline in
        both modes, which is the literal that drew a light card on
        s1rcolor's black page."""
        r, doc, std_w, srv_w = _both([plot_for("scatter")],
                                     kpis=[tp._kpi(bgcolor="notacolour")])
        line = _the_one_reading(std_w, srv_w, "bgcolor(notacolour)")
        assert line == ("dash kpi: bgcolor(notacolour) is not a recognised "
                        "colour; using the default."), line
        for text in self._kpi_texts(r, doc):
            outer = re.search(r"<div\b([^>]*)>", text)
            assert outer and 'class="db-kpi-card"' in outer.group(1), text[:300]
            style = re.search(r'style="([^"]*)"', outer.group(1))
            inline = style.group(1) if style else ""
            assert not re.search(r"(?:^|[;\s])background(?:-color)?\s*:",
                                 inline), inline

    def test_a_good_kpi_colour_is_silent(self):
        _, _, std_w, srv_w = _both([plot_for("scatter")],
                                   kpis=[tp._kpi(color="navy", bgcolor="gs14")])
        assert std_w == srv_w
        assert not [w for w in std_w if "dash kpi" in w], std_w


class TestGraphSizeOptionsAgreeAcrossModes:
    """B7: xsize()/ysize()/aspectratio() through one reader, one message."""

    def test_a_word_is_named_once_and_identically(self):
        _, _, std_w, srv_w = _both([plot_for("scatter")], {
            "aspectratio": "abc", "xsize": "abc", "ysize": "abc"})
        assert std_w == srv_w, (std_w, srv_w)
        for opt in ("aspectratio", "xsize", "ysize"):
            hits = _naming(std_w, opt)
            assert len(hits) == 1, (opt, hits)
            assert "is not a number" in hits[0], hits[0]

    def test_xsize_and_ysize_set_the_same_proportions(self):
        r, doc, std_w, srv_w = _both([plot_for("scatter")],
                                     {"xsize": "6", "ysize": "4"})
        assert std_w == srv_w
        std, srv = _figures(r, doc)
        assert float(std.aspect_ratio) == pytest.approx(1.5)
        assert float(srv.aspect_ratio) == pytest.approx(1.5)

    def test_aspectratio_is_inverted_in_both_modes(self):
        # Stata's aspectratio() is height/width; Bokeh's is width/height.
        # The served figure used to pass the value straight through.
        r, doc, std_w, srv_w = _both([plot_for("scatter")],
                                     {"aspectratio": "2"})
        assert std_w == srv_w
        std, srv = _figures(r, doc)
        assert float(std.aspect_ratio) == pytest.approx(0.5)
        assert float(srv.aspect_ratio) == pytest.approx(0.5)

    def test_a_zero_is_named_once(self):
        _, _, std_w, srv_w = _both([plot_for("scatter")], {"aspectratio": "0"})
        assert std_w == srv_w
        assert len(_naming(std_w, "aspectratio")) == 1, std_w


class TestNumericOptionsFromASpec:
    """B8: a hand-written spec's jitter() and mlabel() are reported."""

    @pytest.mark.parametrize("ptype", ["scatter", "scatteri"])
    @pytest.mark.parametrize("bad", ["abc", "-3"])
    def test_jitter(self, ptype, bad):
        r, doc, std_w, srv_w = _both([plot_for(ptype, {"jitter": bad})])
        line = _the_one(std_w, srv_w, "jitter")
        assert line.startswith(f"dash: {ptype} option jitter({bad}) is"), line
        std, srv = _figures(r, doc)
        assert std.renderers and srv.renderers
        if ptype == "scatter":
            assert std.renderers[0].glyph.x == "weight", "no jitter was drawn"

    @pytest.mark.parametrize("go", [None, {"by": "foreign"}],
                             ids=["no by()", "by(foreign)"])
    def test_mlabel_naming_a_column_the_data_lacks(self, go):
        r, doc, std_w, srv_w = _both(
            [plot_for("scatter", {"mlabel": "nosuchvar"})], go)
        line = _the_one(std_w, srv_w, "mlabel")
        assert line == ("dash: mlabel(nosuchvar): the variable is not in the "
                        "data; drawing no labels."), line
        std, srv = _figures(r, doc)
        for fig in (std, srv):
            assert not [x for x in fig.center if isinstance(x, LabelSet)]


class TestUserTextIsEchoedThroughDashDisplay:
    """B9: printable characters only, and not more than 80 of them."""

    def test_the_style_note(self):
        dr._dash_reset_notes()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr._dash_style_note("mcolor", "a\x01b\n", "colour")
            dr._dash_style_note("msize", "x" * 200, "size")
        msgs = [str(w.message) for w in caught]
        assert msgs[0] == ("dash: mcolor(a?b?) is not a recognised colour; "
                           "using the scheme's default.")
        assert msgs[1] == (f"dash: msize({dr._dash_display('x' * 200)}) is not "
                           f"a recognised size; using the scheme's default.")
        assert len(dr._dash_display("x" * 200)) == 80
        assert all(ch.isprintable() for ch in msgs[0])

    def test_the_seed_warning(self):
        dr._dash_reset_notes()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            assert dr._jitter_seed({"jitterseed": "\x01\x02"}) is None
        assert [str(w.message) for w in caught] == [
            "dash: jitterseed(??) must be a non-negative integer; drawing unseeded."]

    def test_the_mlabel_extras_warning(self):
        _, _, std_w, srv_w = _both(
            [plot_for("scatter", {"mlabel": "make \x01bad " + "y" * 120})])
        line = _the_one(std_w, srv_w, "mlabel")
        assert all(ch.isprintable() for ch in line), line
        assert "?bad" in line and "..." in line, line


# ---- (e) the twoway oracle fixture keeps the table honest -----------------
#
# test/fixtures/value_truth.json is twoway's own verdict on bad values,
# measured 22sep2026 (248 probes; 311 with the additions _meta lists).  The kinds in dash.ado's table rest on
# it: `style` because twoway notes and defaults for a bad style NAME, and
# the number kinds because twoway refuses those values itself.

_FIXTURE = os.path.join(_HERE, "fixtures", "value_truth.json")

# Options twoway does not have, so the oracle cannot speak for them.
_DASH_ONLY = {"jseed", "malpha", "lalpha", "falpha", "colornlevels",
              "colpalette", "colorcuts", "colorvar", "hover",
              # dash's spellings of xlabel(..., axis(2)): the fixture's
              # xlabel2_1-3/ylabel2_1-3 record twoway's "option xlabel2()
              # not allowed" for every value (30sep2026).
              "xlabel2", "ylabel2",
              # WP-29 P0.5: dash's spellings of xtick(..., axis(2)) and
              # ytick(..., axis(2)); twoway refuses those names outright.
              "xtick2", "ytick2"}
# Options whose refusal is dash's own and documented as such (dash.sthlp,
# "Option values"): twoway accepts every value of these silently.  And
# scheme, which these tests never saw until _TOKEN read every kind
# (24sep2026): twoway draws s2color under "(note: scheme nonsense not
# found, using s2color)", rc 0 (the fixture's scheme_1), where dash refuses
# the name -- its own rule, documented in "Option values" and in "Stata
# scheme support" (a dashboard is a file you look at later).
_DELIBERATE = {"jitterseed", "xaxis", "scheme"}
# Options whose twoway probe is measured live beside dash's rule rather than
# in the oracle fixture: zlabel()'s format() (WP-30 P1.5, S17's P1.23b),
# twoway's "invalid format, bogus" r(198) next to dash's in
# test_option_validation.cscript AF-18 and the section-17 measurement.
_PROBED_LIVE = {"zlabel",
                # WP-30 P1.13a: the colour kind's twoway refusal (invalid
                # '<word>', r(198)) is measured in
                # fixtures/colour_grammar_truth.json (comma_*) and asked of
                # twoway again by test_colour_grammar.py::TestStataTruth.
                "mcolor", "mfcolor", "mlcolor", "mlabcolor", "lcolor",
                "fcolor", "color", "acolor", "alcolor", "bfcolor",
                "blcolor", "clcolor"}


def _fixture():
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


class TestTheOracleFixtureIsInStep:
    def test_the_fixture_counts_itself_correctly(self):
        fx = _fixture()
        counts = fx["_meta"]["counts"]
        assert counts["twoway"] == len(fx["twoway"])
        assert counts["twoway_rc0"] == sum(1 for p in fx["twoway"] if p["rc"] == 0)
        assert counts["twoway_rejected"] == sum(1 for p in fx["twoway"] if p["rc"] != 0)
        assert counts["twoway_rc0"] + counts["twoway_rejected"] == counts["twoway"]
        assert counts["formats"] == len(fx["formats"])
        for name, n in counts["vocab"].items():
            assert len(fx["vocab"][name]) == n, name

    @_needs_table
    def test_every_twoway_option_in_the_table_was_probed(self):
        """A structural guard, deliberately: every rule in dash.ado's table
        rests on a measured twoway probe in the fixture, so a new rule
        cannot be added with nothing behind it."""
        probed = {p["option"] for p in _fixture()["twoway"]}
        for opt, _kind, _ps, _ts in _parse_rules(_BLOCK):
            if opt not in _DASH_ONLY | _PROBED_LIVE:
                assert opt in probed, f"{opt}: no twoway probe behind its rule"

    @_needs_table
    def test_a_style_kind_rests_on_twoway_s_note(self):
        """twoway printed `named style ... not found` and drew (rc 0) for a
        word in every option the table calls a style.

        A structural guard, deliberately: it ties dash.ado's table to
        twoway's measured behaviour (the fixture) without running Stata;
        each rule's own behaviour runs in test_option_validation.cscript."""
        fx = _fixture()
        for opt, kind, _ps, _ts in _parse_rules(_BLOCK):
            if kind not in ("style", "istyle"):
                continue
            words = [p for p in fx["twoway"]
                     if p["option"] == opt and p["value"] == "abc"]
            assert words, f"{opt}: no word probe"
            for p in words:
                assert p["rc"] == 0 and "named style" in p["message"], p

    @_needs_table
    def test_a_refusing_kind_rests_on_a_twoway_refusal(self):
        """Where twoway has the option, it refused at least one probe, or
        the refusal is dash's own and documented.

        A structural guard, deliberately, as the test above: the table
        against the twoway fixture; the refusals themselves run in
        test_option_validation.cscript."""
        fx = _fixture()
        for opt, kind, _ps, _ts in _parse_rules(_BLOCK):
            if (kind in ("style", "istyle")
                    or opt in _DASH_ONLY | _DELIBERATE | _PROBED_LIVE):
                continue
            rejected = [p for p in fx["twoway"]
                        if p["option"] == opt and p["rc"] != 0]
            assert rejected, f"{opt}: twoway refused nothing, so this rule is dash's own and belongs in _DELIBERATE with a help entry"

    def test_the_format_probes_agree_with_the_gate(self):
        """`confirm numeric format` accepted exactly the numeric formats
        the help promises and refused the string and malformed ones."""
        fx = _fixture()
        # The last two probes are strofreal(), not confirm: it returns ""
        # for a bad format without a word, which is why it is not the
        # validator.  First verdict per value wins.
        verdict = {}
        for p in fx["formats"]:
            verdict.setdefault(p["value"], p["rc"])
        for good in ("%9.2f", "%12.0fc", "%9.0gc", "%-12.3e", "%tdCCYY-NN-DD",
                     "%tcHH:MM:SS", "%21x"):
            assert verdict[good] == 0, good
        for bad in ("%12s", "bogus", "9.2f", "%9.2", "%9.2f_n", "%c", "%"):
            assert verdict[bad] != 0, bad
