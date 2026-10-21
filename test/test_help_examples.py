"""test_help_examples.py -- the help's example commands, as one reader sees them.

``test_help_examples.cscript`` runs every example command in ``dash.sthlp``
and ``dash_setup.sthlp`` in Stata, each group from a fresh session's state,
and holds each to what the help says.  It learns the examples at run time
from ``test/help_examples.py``, the reader this file imports, so the two
suites cannot disagree about what the examples are; this file pins what that
reader finds, so that a change to the help -- an example added, dropped,
split or merged -- is made on purpose:

* how many groups and commands there are, and how they group;
* that every ``{cmd:. `` line of both files is inside exactly one command,
  by a plain scan that shares nothing with the reader;
* that every group is one a user can type into a fresh session: it loads
  its own data and registers what its ``dash build`` needs;
* that nothing the help shows as a command is outside the harness: every
  command line and every dash command in a sentence is an example, the
  output of one, or pinned in the cscript as shown and not run;
* the cscript's pinned lists: each names what it should, each kind has a
  handler, every example that may not run as written is pinned, and the
  cscript reads the examples through this reader;
* the reader's rules -- SMCL escapes, ``///`` continuations, groups, the
  output the help shows, what is shown and not run -- and the judge's, on
  made-up help text and logs;
* one claim no log shows: every ``lpoly`` example draws a curve.  The
  Statistical Layer Options example read ``(lpoly mpg weight,
  bwidth(0.4))``; ``bwidth()`` there is in the units of x, and a window 0.4
  lb wide draws one point of the 50 -- measured, in dash and in
  ``twoway lpoly`` alike -- so the example drew no curve (WP-23).
"""
import os
import re
import sys

import numpy as np
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import help_examples as hx  # noqa: E402

_REPO = os.path.dirname(_HERE)
_CSCRIPT = os.path.join(_HERE, "test_help_examples.cscript")


@pytest.fixture(scope="module")
def groups():
    return hx.extract_all(_REPO)


@pytest.fixture(scope="module")
def shown():
    return hx.shown_all(_REPO)


def _commands(groups):
    return [c for g in groups for c in g.commands]


@pytest.fixture(scope="module")
def cscript_source():
    with open(_CSCRIPT, encoding="utf-8") as fh:
        return fh.read()


def _help_lines(name):
    with open(os.path.join(_REPO, name), encoding="utf-8") as fh:
        return fh.read().split("\n")


# ---------------------------------------------------------------------------
# The shape of the help's examples
# ---------------------------------------------------------------------------

class TestTheShapeOfTheExamples:
    """WP-23, after every example was made one a fresh session can run: 32
    groups, 98 commands, 102 lines (29, 63 and 65 at 4ede074); WP-30
    P1.11b's Text in graphs example makes 33, 100 and 104; WP-30 P1.7's
    Time-series operators example (sp500, tsset, dash line D.close date)
    makes 34, 103 and 107; WP-31 H2k's weighted KPI example makes 35,
    106 and 110; WP-31 J2's Linking example 36, 110 and 114."""

    # 6 -> 7 (the Tabs group): WP-31 D14 the per-tab layout() build.
    # New group of 2 at index 9: WP-31 H2k, the weighted KPI example.
    # New group of 4 at index 8: WP-31 J2, the Linking section's example
    # of a linked graph with its own if.
    GROUP_SIZES = [3, 3, 2, 2, 2, 4, 7, 4, 4, 2, 2, 1, 2, 2, 5, 4, 5, 2, 6,
                   4, 2, 2, 5, 2, 2, 2, 3, 2, 2, 2, 3, 7, 2, 3, 3, 2]

    def test_how_many(self, groups):
        # 34 -> 35: WP-31 H2k, the weighted KPI example group.
        # 35 -> 36: WP-31 J2, the Linking section's qualifier example.
        assert len(groups) == 36
        # 103 -> 104, 107 -> 108: WP-31 D14 the per-tab layout() build.
        # 104 -> 106, 108 -> 110: WP-31 H2k, the weighted KPI example.
        # 106 -> 110, 110 -> 114: WP-31 J2, its four lines.
        assert len(_commands(groups)) == 110
        assert sum(len(c.lines) for c in _commands(groups)) == 114

    def test_how_they_group(self, groups):
        assert [len(g.commands) for g in groups] == self.GROUP_SIZES

    def test_every_group_has_a_label(self, groups):
        assert all(g.label for g in groups)

    def test_every_example_is_in_dash_sthlp(self, groups):
        """dash_setup.sthlp writes its commands without the dot prompt, and
        they install packages: they are shown, not run (below)."""
        assert {g.file for g in groups} == {"dash.sthlp"}
        text = "\n".join(_help_lines("dash_setup.sthlp"))
        assert hx.prompt_lines(text) == []
        assert hx.extract_text(text, "dash_setup.sthlp") == []

    def test_the_continued_commands_are_joined(self, groups):
        joined = [c for c in _commands(groups) if len(c.lines) > 1]
        assert [c.text for c in joined] == [
            'dash build, saving(out.html) replace filter(foreign, '
            'type(dropdown)) filter(weight, type(range) exclude(k1))',
            'dash (scatter mpg weight, mc(red)) (lfit mpg weight), '
            'title("MPG vs Weight") saving(fit.html)',
            'dash build, saving(kpi.html) filter(foreign, type(dropdown)) '
            'replace',
        ]
        assert all(c.lines == tuple(range(c.lines[0], c.lines[-1] + 1))
                   for c in joined)

    def test_which_commands_the_help_shows_output_for(self, groups):
        shown_out = {c.text: len(c.outputs) for c in _commands(groups)
                     if c.outputs}
        # Flipped (WP-30 P1.10): text() is drawn, so the Differences
        # example names play() alone; it was play(x) text(20 3000 "hi").
        assert shown_out == {
            # Flipped (WP-32): play() of a missing recording is refused
            # and the named control is afcolor(), which dash names.
            'dash scatter mpg weight, afcolor(red)': 1,
            # Flipped (WP-31 C10c): yaxis(3) is drawn; the help's
            # refusal example was degree(8), dash's own bound.
            # Flipped (WP-31 D35): degree(8) is drawn, as twoway draws it;
            # the example is bin(2000).
            'dash (histogram mpg, bin(2000))': 1,
            'dash (scatter mpg weight, discrete)': 1,
            # Flipped (WP-31 A5): dash lfit mpg weight [aw=price+1] is
            # drawn, so the help shows no refusal for it.
            'dash build, saving(d.html) scheme(nosuchthing) replace': 1,
            # Flipped (WP-30 P1.14a): pstyle() is drawn, so the
            # Unsupported example names mlpattern() instead.
            # WP-31 D2: t1title("hi") -> scale(1.2), t1title() is drawn.
            # WP-31 D5: scale(1.2) -> play(x), scale() is drawn.
            # Flipped (WP-31 E2): mlpattern() -> mlabwidth(2), which is
            # still named; mlpattern() is taken as twoway takes it.
            # Flipped (WP-32): mlabwidth() is refused as twoway refuses it.
            'dash scatter mpg weight, afcolor(red) afintensity(50)': 1,
        }


class TestEveryExampleLineIsRead:
    """A plain scan for ``{cmd:. `` finds the lines; the reader must have put
    each in exactly one command.  A line it skipped would be an example
    nothing runs."""

    @pytest.mark.parametrize("name", hx.HELP_FILES)
    def test_every_prompt_line_is_in_exactly_one_command(self, name, groups):
        want = hx.prompt_lines("\n".join(_help_lines(name)))
        got = [n for c in _commands(groups) if c.file == name
               for n in c.lines]
        assert len(got) == len(set(got))
        assert sorted(got) == want

    def test_the_scan_found_something(self):
        assert len(hx.prompt_lines("\n".join(_help_lines("dash.sthlp")))) \
            >= 100


# ---------------------------------------------------------------------------
# Every group is one a fresh session can run
# ---------------------------------------------------------------------------

_LOADS = re.compile(r"^(?:sysuse|use|webuse|input|import|set\s+obs)\b")
_NEEDS_DATA = re.compile(r"^dash\s+(?!(?:build|serve|clear)\b)")
_BUILDS = re.compile(r"^dash\s+(?:build|serve)\b")


class TestEveryGroupRunsInAFreshSession:
    """The cscript starts every group with no data in memory and an empty
    registry; this is the same rule, read from the text alone."""

    def test_each_group_loads_its_data_and_registers_what_it_builds(
            self, groups):
        bad = []
        for g in groups:
            data = registered = False
            for c in g.commands:
                if _LOADS.match(c.text):
                    data = True
                elif _NEEDS_DATA.match(c.text):
                    if not data:
                        bad.append("%s:%d uses data its group never loads: %r"
                                   % (c.file, c.line, c.text))
                    registered = registered or bool(
                        hx.registered_name(c.text))
                elif _BUILDS.match(c.text) and not registered:
                    bad.append("%s:%d builds with nothing registered in its "
                               "group: %r" % (c.file, c.line, c.text))
        assert not bad, "\n".join(bad)


# ---------------------------------------------------------------------------
# Every example renders as it is typed
# ---------------------------------------------------------------------------

class TestEveryExampleStartsAParagraph:
    """Measured with Stata's translator (smcl2txt): ``{pstd}`` / text /
    ``{phang2}{cmd:. ...}{p_end}``, with no blank line or ``{p_end}``
    between, renders every directive after it as text.  dash.sthlp had that
    shape at every ``{it:Example:}`` from the Faceting section on, so from
    there to the end each example read ``. dash scatter mpg weight,
    by(foreign){p_end}``.  The line before an example block, or a command
    line shown without the prompt, must close the paragraph above it.  (The
    cscript translates both files and checks the text itself.)"""

    @pytest.mark.parametrize("name", hx.HELP_FILES)
    def test_the_line_before_each_block_closes_the_paragraph(
            self, name, groups, shown):
        lines = _help_lines(name)
        firsts = [g.line for g in groups if g.file == name]
        firsts += [s.line for s in shown if s.file == name
                   and s.form == "line"]
        bad = []
        for n in firsts:
            prev = lines[n - 2] if n > 1 else ""
            if prev.strip() and not prev.rstrip().endswith("{p_end}"):
                bad.append("%s:%d follows %r" % (name, n, prev))
        assert not bad, "\n".join(bad)

    #: What Stata rendered from the failing shape, measured (smcl2txt).
    BROKEN = ("          Example:\n\n"
              "              . dash scatter mpg weight, by(foreign){p_end}"
              " Next {pstd}After\n"
              "                  {phang2}. dash scatter mpg weight{p_end}\n")
    #: ... and from the same lines with the paragraph closed.
    GOOD = ("          Example:\n\n"
            "              . sysuse auto, clear\n"
            "              . dash (scatter mpg weight) (lfit mpg weight),\n"
            "                  title(\"MPG\") saving(fit.html)\n"
            "              . dash build, saving(kpi.html) ///\n"
            "              .     filter(foreign, type(dropdown)) replace\n\n"
            "      Next\n\n"
            "          After x, powers from {-2, -1, 0, 3}.\n")

    def test_the_rendering_check_sees_a_directive_left_in_the_text(self):
        probs = hx.rendered_problems(self.BROKEN, 2)
        assert probs[0] == ("1 example lines rendered as lines of their own; "
                            "the file has 2")
        assert "{p_end} Next {pstd}After" in probs[1]

    def test_a_well_rendered_help_passes(self):
        assert hx.rendered_prompt_lines(self.GOOD) == [
            ". sysuse auto, clear",
            '. dash (scatter mpg weight) (lfit mpg weight), title("MPG") '
            "saving(fit.html)",
            ". dash build, saving(kpi.html) ///",
            ".     filter(foreign, type(dropdown)) replace"]
        assert hx.rendered_problems(self.GOOD, 4) == []

    def test_fewer_example_lines_than_the_file_has_fails(self):
        assert hx.rendered_problems(self.GOOD, 5) == [
            "4 example lines rendered as lines of their own; the file has 5"]

    def test_more_example_lines_than_the_file_has_fails(self):
        """As many lines render with the prompt as the file has example
        lines, no more either: a line written ``{input}. dash ...`` renders
        with the prompt, and neither the reader nor the plain scan (both
        look for ``{cmd:.``) sees it, so it would never run.  Until
        24sep2026 rendered_problems() failed only too few lines, and a
        comparison of ``<`` for its ``!=`` passed every other test here."""
        assert hx.rendered_problems(self.GOOD, 3) == [
            "4 example lines rendered as lines of their own; the file has 3"]


# ---------------------------------------------------------------------------
# No SMCL is left as text anywhere: the renderer's rules, and the twin
# ---------------------------------------------------------------------------

#: The heading each case below ends with, so a case that loses the rest of
#: the file shows it: ``NEXT`` does not render as a heading.
_TAIL = "\n\n{title:NEXT}\n\n{pstd}AFTER {cmd:x}.{p_end}\n"

#: Minimal SMCL cases and what StataNow 19.5's translator (smcl2txt) made
#: of each, measured 23sep2026: ``({token: count} shown as text, [headings
#: that did not render as one])``.  Each ends with _TAIL.
_MEASURED = [
    # A paragraph directive while a paragraph is open: the rest is lost.
    ("{pstd}\ntext\n{phang2}{cmd:A}{p_end}", {}, ["NEXT"]),
    ("{pstd}\ntext\n{pstd}\nmore{p_end}", {}, ["NEXT"]),
    ("{pstd}\ntext\n{p 8 8 2}more{p_end}", {}, ["NEXT"]),
    ("{pstd}\ntext\n{synopt:{opt a}}desc{p_end}", {}, ["NEXT"]),
    ("{pstd}\ntext {phang2}mid{p_end}", {}, ["NEXT"]),
    ("{pstd}\ntext\n{synoptset 20}{...}\n{synopt:{opt a}}desc{p_end}", {},
     ["NEXT"]),
    ("{synoptset 20}{...}\n{synopt:{opt a}}desc\n{synopt:{opt b}}desc{p_end}",
     {}, ["NEXT"]),
    ("{phang2}{cmd:a}\n{phang2}{cmd:b}{p_end}", {}, ["NEXT"]),
    ("{phang2}\ntext\n{phang}more{p_end}", {}, ["NEXT"]),
    ("{pstd}\ntext\n{phang2}{cmd:A}", {}, ["NEXT"]),
    ("{pstd}\ntext\n{it:Example:}\n{phang2}{cmd:A}{p_end}\n\n{pstd}\n"
     "{it:Example:}\n{phang2}{cmd:B}{p_end}", {}, ["NEXT"]),
    ("{pstd}\ntext\n{p2col:a}b{p_end}", {}, ["NEXT"]),
    ("{pstd}\ntext\n{pmore}\nmore{p_end}", {}, ["NEXT"]),
    ("{pstd}\ntext\n{pin}more{p_end}", {}, ["NEXT"]),
    ("{pstd}\ntext\n{psee}more{p_end}", {}, ["NEXT"]),
    ("{pstd}\n{ul:Title.}\n{phang2}{cmd:x}{p_end}", {}, ["NEXT"]),
    ("{p 8 17 2}\n{cmd:dash} {it:x}\n{p 8 17 2}\n{cmd:dash clear}\n", {},
     ["NEXT"]),
    ("{pstd}\ntext\n{synoptline}\n{synopt:{opt a}}d{p_end}", {}, ["NEXT"]),
    # A line-mode directive inside an open paragraph is folded into it.
    ("{pstd}\ntext\n{title:X}", {}, ["X"]),
    ("{pstd}\ntext\n{marker m}{...}\n{title:X}", {}, ["X"]),
    ("{title:A}\n{pstd}\ntext\n{marker m}{...}\n{title:B}\n\n{pstd}more"
     "{p_end}", {}, ["B"]),
    ("{pstd}\ntext\n{dlgtab:X}", {}, []),
    ("{pstd}\ntext\n{dlgtab:X}\n\n{pstd}more{p_end}", {}, []),
    ("{pstd}\ntext\n{synoptline}", {}, []),
    ("{pstd}\ntext\n{synopthdr}", {}, []),
    ("{pstd}\ntext\n{synopthdr}\n{synoptline}\n", {}, []),
    ("{pstd}\ntext\n{center:X}", {}, []),
    # Shown as text, the rest rendering.
    ("{pstd}Use {opt x(}{it:y}{opt )} here.{p_end}", {"{opt": 1}, []),
    ("{pstd}Use {cmd:abc\ndef} here.{p_end}", {"{cmd:abc": 1}, []),
    ("{pstd}Use {it:if}/{in} and {xyz} and {it}i{sf} here.{p_end}",
     {"{in}": 1, "{xyz}": 1}, []),
    ("{pstd}\ntext\n{hline}", {"{hline}": 1}, []),
    ("{pstd}text {opt plotregion(color(}{it:color}{opt ))} more.{p_end}",
     {"{opt": 1}, []),
    ("{synopt:{opt plotregion(color(}{it:color}{opt ))}}background{p_end}",
     {"{opt": 1}, []),
    # Rendered as meant.
    ("{pstd}Use {opt a(b(c))} here.{p_end}", {}, []),
    ("{pstd}\ntext\n{ul:Heading.}  more text{p_end}", {}, []),
    ("{pstd}Use {opt by(varlist, cols(#))} and {opth v(varname)} here."
     "{p_end}", {}, []),
    ("{pstd}Use {cmd:x}{cmd:///} here.{p_end}", {}, []),
    ("{p 12 12 2}{cmd:. dash x}{p_end}\n{p 12 12 2}{cmd:dash: note}{p_end}",
     {}, []),
    ("{pstd}Use {cmd:b} and {c 164}bf:x{c )-} here.{p_end}", {}, []),
    ("{pstd}\ntext\n\n{phang2}{cmd:A}{p_end}", {}, []),
    ("{phang2}{cmd:A}\n{cmd:B}\n\n{pstd}C{p_end}", {}, []),
    ("{pstd}\n{it:Example:}{p_end}\n{phang2}{cmd:A}{p_end}", {}, []),
    ("{synoptset 20}{...}\n{synopt:{opt a}}desc\n    more{p_end}\n"
     "{synopt:{opt b}}desc{p_end}", {}, []),
    ("{pstd}\ntext\n{synoptset 20}{...}\n", {}, []),
    ("{pstd}\ntext\n{p2colset 5 20 22 2}{...}\n", {}, []),
    ("{phang}text{p_end}\n{synoptset 20}{...}\n{synopt:{opt a}}d{p_end}", {},
     []),
    ("{synoptset 20}{...}\n{synopt:{opt a}}d\n\n{pstd}x{p_end}", {}, []),
    ('{pstd}\ntext\n{viewerjumpto "X" "y##z"}{...}\n', {}, []),
    ("{pstd}\ntext\n{* a comment}{...}\n", {}, []),
    ("{pstd}text\n{p_end}\n{phang2}x{p_end}", {}, []),
    ("{p 8 17 2}\n{cmd:dash clear}\n", {}, []),
    ("{pstd}text {hline 2} more{p_end}", {}, []),
    ('{phang2}{cmd:python: f(1,}\n{cmd:"two")}\n\n{pstd}C{p_end}', {}, []),
    ("{pstd}\ntext{p_end}\n{title:X}", {}, []),
    ("{phang2}1.  {ul:A.}\n    text.\n\n{phang2}    {ul:B.}  more{p_end}",
     {}, []),
    ("{pstd}See {help dash##x:X} and {helpb dash} and "
     "{manhelp twoway G-2:graph twoway}.{p_end}", {}, []),
    ("{pstd}Weights {weight} and {ifin} here.{p_end}", {}, []),
    # A brace the source escapes is text: Stata drew "{b}" and "{bf:x}"
    # here, as meant; the marked copy draws the sentinel instead (the case
    # with {c 164} above), so the whole-file check leaves it alone.
    ("{pstd}Use {cmd:a {c -(}b{c )-} c} and {c -(}bf:x{c )-} here.{p_end}",
     {}, []),
]


class TestTheRenderTwinReproducesTheRenderer:
    """render_problems() predicts, from the SMCL source, what Stata's
    translator was measured to do with each case: which directives it shows
    as text and which headings it loses."""

    @pytest.mark.parametrize("body,left,lost", _MEASURED)
    def test_a_measured_case(self, body, left, lost):
        src = "{smcl}\n" + body + _TAIL
        assert hx.predicted_leftovers(src) == left
        assert hx.predicted_title_losses(src) == lost

    def test_the_cases_cover_each_kind(self):
        kinds = set()
        for body, _l, _t in _MEASURED:
            kinds.update(k for _n, k, _f, _m in
                         hx.render_problems("{smcl}\n" + body + _TAIL))
        assert kinds == {"literal", "inlined", "cascade"}


class TestTheHelpRendersWhole:
    """Every place Stata's renderer would leave SMCL as text, fold a heading
    into prose, or stop rendering, by the twin -- in both help files.  The
    cscript checks Stata's own rendering of them, and that it agrees."""

    @pytest.mark.parametrize("name", hx.HELP_FILES)
    def test_no_smcl_is_left_as_text(self, name):
        probs = hx.render_problems("\n".join(_help_lines(name)))
        assert not probs, "\n".join(
            "%s:%d (%s) %s" % (name, n, kind, msg)
            for n, kind, _frag, msg in probs)


class TestTheWholeFileCheck:

    def test_an_escaped_brace_is_marked_in_every_spelling(self):
        src = "a {c -(}b{c )-} {char -(} {c 123} {char 123} {c 0x7b} {c 0X7B}"
        marked = hx.with_braces_marked(src)
        assert marked.count(hx.SENTINEL) == 6
        assert "{c )-}" in marked

    def test_the_leftovers_of_a_rendering(self):
        assert hx.rendered_leftovers(
            "  a ({cmd:bands must be\n  and {in} {opt x(}y) {opt\n") == {
                "{cmd:bands": 1, "{in}": 1, "{opt": 2}
        # The sentinel, SMCL's {c 164}, where the help escapes a brace.
        assert hx.rendered_leftovers("  a " + chr(0xa4) + "bf:x} b\n") == {}

    def test_a_heading_must_render_as_a_line_of_its_own_in_order(self):
        rendered = "    Syntax\n        text\n    Examples\n    more Remarks\n"
        assert hx.rendered_title_losses(
            rendered, ["Syntax", "Examples", "Remarks"]) == ["Remarks"]
        assert hx.rendered_title_losses(
            rendered, ["Examples", "Syntax"]) == ["Syntax"]

    def test_stata_and_the_twin_agreeing(self):
        src = "{smcl}\n{title:A}\n\n{pstd}Use {in} here.{p_end}\n"
        rendered = "    A\n\n        Use {in} here.\n"
        (p,) = hx.whole_file_render_problems(src, rendered)
        assert p == "rendered with SMCL left in it: Use {in} here."

    def test_stata_and_the_twin_disagreeing_is_reported(self):
        src = "{smcl}\n{title:A}\n\n{pstd}Use {it:x} here.{p_end}\n"
        rendered = "    A\n\n        Use {it:x} here.\n"
        probs = hx.whole_file_render_problems(src, rendered)
        assert any("the Python twin predicts {}" in p for p in probs)

    def test_a_lost_heading_is_reported(self):
        src = "{smcl}\n{title:A}\n\n{pstd}x{p_end}\n\n{title:B}\n"
        probs = hx.whole_file_render_problems(src, "    A\n        x\n")
        assert "the heading 'B' did not render as one" in probs[0]

    def test_after_a_cascade_stata_may_show_more_than_the_twin_predicts(self):
        """What Stata rendered of the cascade put back at the Faceting
        example, in small: the rest shown as text, the heading lost."""
        src = ("{smcl}\n{title:A}\n\n{pstd}\n{it:Example:}\n"
               "{phang2}{cmd:. dash x}{p_end}\n\n{title:B}\n\n"
               "{pstd}y{p_end}\n")
        rendered = ("    A\n\n        Example:\n\n"
                    "            . dash x{p_end} B {pstd}y\n")
        probs = hx.whole_file_render_problems(src, rendered)
        assert not any("Python twin" in p for p in probs)
        assert any("the heading 'B'" in p for p in probs)


# ---------------------------------------------------------------------------
# Nothing shown as a command is outside the harness
# ---------------------------------------------------------------------------

#: A command line, by a plain pattern that shares nothing with the reader: a
#: paragraph directive, one or more {cmd:...}, an optional {p_end}.  A bare
#: {cmd:...} line is left out: it is the wrapped end of a {synopt} or a
#: sentence, or the continuation of the command line above it.
_PLAIN_CMD_LINE = re.compile(
    r"^\s*\{(?:p(?:\s+\d+)*|phang\d?|pstd|pin\d?|pmore\d?|psee)\}"
    r"(?:\{cmd:(?:[^{}]|\{c(?:har)?\s+[^{}]*\})*\})+"
    r"(?:\{p_end\})?\s*$")
_PLAIN_MENTION = re.compile(r"\{cmd:(dash\s[^{}]*)\}")
# dash image joined the subcommands' bare names in WP-33 33-06.
_NOT_A_COMMAND = re.compile(
    r"^dash\s+(?:build|serve|kpi|clear|image)\s*$|^dash(?:\s+\w+)?\s*:")


def _outside_syntax(name):
    """``(line number, text)`` for the lines of *name* not in a Syntax
    section, which is grammar."""
    out, in_syntax = [], False
    for n, ln in enumerate(_help_lines(name), 1):
        m = re.match(r"\{title:([^}]*)\}", ln)
        if m:
            in_syntax = m.group(1).strip() == "Syntax"
        if not in_syntax:
            out.append((n, ln))
    return out


class TestEveryCommandShownIsAccountedFor:

    @pytest.mark.parametrize("name", hx.HELP_FILES)
    def test_every_command_line_is_an_example_an_output_or_shown(
            self, name, groups, shown):
        known = set()
        for c in _commands(groups):
            if c.file == name:
                known.update(c.lines)
                known.update(c.output_lines)
        for s in shown:
            if s.file == name and s.form == "line":
                known.update(s.lines)
        stray = [(n, ln) for n, ln in _outside_syntax(name)
                 if _PLAIN_CMD_LINE.match(ln) and n not in known]
        assert not stray, (
            "a command line in %s is neither an example, the output of one, "
            "nor shown and pinned: %r" % (name, stray))

    @pytest.mark.parametrize("name", hx.HELP_FILES)
    def test_every_dash_command_in_a_sentence_is_found(self, name, shown):
        want = []
        for n, ln in _outside_syntax(name):
            if _PLAIN_CMD_LINE.match(ln):
                continue
            for m in _PLAIN_MENTION.finditer(ln):
                t = " ".join(m.group(1).split())
                if not _NOT_A_COMMAND.match(t):
                    want.append((n, t))
        got = [(s.line, s.text) for s in shown
               if s.file == name and s.form == "inline"]
        assert got == want


class TestTheShownCommands:

    def test_how_many(self, shown):
        forms = [(s.file, s.form) for s in shown]
        # 1 -> 3: WP-31 I2, the Installation section's net install and
        # dash_setup lines.
        assert forms.count(("dash.sthlp", "line")) == 3
        # WP-29 P0.8: two date-unit illustrations joined the six.
        # 8 -> 9: WP-30 batch 4 added one inline example.
        # 9 -> 10: WP-30 P1.26b's Notes paragraph shows dash build, server.
        # 10 -> 12: WP-30 P1.17b's base() and P1.32's guard sentences.
        # 12 -> 11: WP-31 B4b drew contour and contourline, and the
        # refusal sentence's inline dash scatter y x, colorvar(z) went.
        # 11 -> 12: WP-31 H2k, the weights sentence's dash kpi mean(mpg)
        # [aw=weight], which the example below it runs.
        assert forms.count(("dash.sthlp", "inline")) == 12
        # 7 -> 8: WP-32 I3, the hash-checked pip line naming the lock.
        assert forms.count(("dash_setup.sthlp", "line")) == 8
        # dash_setup.sthlp once also named `python set exec` inline, in the
        # prose; WP-23 rewrote that paragraph, and the command is shown
        # once, as a command line.
        assert forms.count(("dash_setup.sthlp", "inline")) == 0
        # WP-29 P0.19: the three two-line python: recipes and their shared
        # `python: import subprocess, sys' became four one-line shell
        # commands, and the venv() and ensurepip lines were added; WP-29
        # P0.8 added two date-unit illustrations (13 + 2).
        # WP-30 P1.17b and P1.32: two more sentence illustrations (15 + 2).
        # 17 -> 16: WP-31 B4b, the contour refusal's dash scatter is gone.
        # 16 -> 17: WP-31 H2k, the weighted KPI sentence.
        # 17 -> 19: WP-31 I2, the Installation section's two lines.
        # 19 -> 20: WP-32 I3, the hash-checked pip line.
        assert len({s.text for s in shown}) == 20

    def test_the_two_line_pip_commands_are_joined(self, shown):
        # WP-29 P0.19: the recipes became one-line shell commands that name
        # the linked Python and quote each requirement.
        pip = [s for s in shown if "pip" in s.text]
        # [1] * 4 -> [1] * 5: WP-32 I3, the hash-checked line.
        assert [len(s.lines) for s in pip] == [1, 1, 1, 1, 1]
        # Flipped (WP-30 P1.30): the help installs bokeh inside the
        # verified window.  Flipped (WP-32 I3): numpy and pandas carry
        # their ceilings too.
        assert pip[0].text == ('"/path/to/python3" -m pip install '
                               '"bokeh>=3.8,<3.10" "numpy>=2.3,<2.5" "pandas>=2.3,<3.1"')

    def test_each_passes_the_check_its_pin_names(self, shown, pins, groups):
        kind = {text: value for k, value, text in pins if k == "shown"}
        for s in shown:
            assert s.text in kind, "shown and not pinned: %r" % s
            assert hx.check_shown(s, kind[s.text], groups) == [], s


class TestCheckShown:

    @staticmethod
    def _examples(*cmds):
        return hx.extract_text("\n".join(
            "{phang2}{cmd:. %s}{p_end}" % c for c in cmds), "t.sthlp")

    @staticmethod
    def _item(text):
        return hx.Shown("t.sthlp", (1,), text, "line")

    def test_python_that_compiles(self):
        assert hx.check_shown(self._item("python: import os"), "python",
                              []) == []

    def test_python_that_does_not(self):
        (p,) = hx.check_shown(self._item("python: f([1,"), "python", [])
        assert "does not compile" in p

    def test_a_python_pin_on_something_else(self):
        (p,) = hx.check_shown(self._item("dash clear"), "python", [])
        assert "no python: line" in p

    def test_outside_runs_a_file_an_example_writes(self):
        gs = self._examples("dash build, saving(app.py) server replace")
        assert hx.check_shown(self._item("python app.py"), "outside",
                              gs) == []
        (p,) = hx.check_shown(self._item("python other.py"), "outside", gs)
        assert "no example writes" in p

    def test_described_is_run_by_an_example(self):
        gs = self._examples("dash build, saving(app.py) server replace")
        item = self._item("dash build, saving(app.py) server")
        assert hx.check_shown(item, "described", gs) == []
        (p,) = hx.check_shown(item, "described", [])
        assert "no example runs" in p

    @pytest.mark.parametrize("kind", ["placeholder", "fragment"])
    def test_accounted_for_only(self, kind):
        assert hx.check_shown(self._item("anything"), kind, []) == []

    def test_an_unknown_kind(self):
        assert hx.check_shown(self._item("x"), "nosuch", [])


# ---------------------------------------------------------------------------
# The cscript's pinned lists
# ---------------------------------------------------------------------------

_PIN = re.compile(r"""^_hx_pin\s+(\w+)\s+(\S+)\s+`"(.*)"'\s*$""")

#: The handlers the cscript implements for each kind (its _hx_pin_add
#: refuses any other value, and so does this file).
_HANDLERS = {
    "special": {"serve"},
    "check": {"titled", "bygroups", "pyapp"},
    # "install": WP-31 I2, the Installation section's two lines.
    "shown": {"outside", "python", "placeholder", "fragment", "described",
              "install"},
}


@pytest.fixture(scope="module")
def pins(cscript_source):
    return [m.groups() for m in
            (_PIN.match(ln) for ln in cscript_source.splitlines()) if m]


class TestThePinnedLists:
    """Structural guards over test_help_examples.cscript's pin lists,
    deliberately.  A pin decides how the Stata suite treats a help example
    it cannot simply run; a pin that names nothing the help holds, a kind
    with no handler, or an example left without a pin is an example the
    suite skips or misjudges without saying so, and the suite stays green.
    Only reading the pins against the help and the handlers can see that."""

    def test_every_pin_line_was_parsed(self, pins, cscript_source):
        """Guards the guard: a pin this file cannot read is checked by
        nothing below."""
        lines = [ln for ln in cscript_source.splitlines()
                 if ln.startswith("_hx_pin ")]
        # WP-29 P0.19: the four `python' recipe pins became six
        # `placeholder' pins (four shell lines, venv(), its link line);
        # WP-29 P0.8 pinned its two date-unit illustrations (22 + 2), and
        # WP-30 P1.17b and P1.32 two more sentence illustrations (24 + 2).
        # 26 -> 25: WP-31 A5 -- the [aw=price+1] example is drawn, no
        # longer an expected refusal.
        # 25 -> 24: WP-31 B4b -- the dash scatter fragment pin goes with
        # the contour refusal sentence that showed it.
        # 24 -> 25: WP-31 H2k -- the weighted KPI sentence's described pin.
        # 25 -> 27: WP-31 I2 -- the Installation section's two install pins.
        # 27 -> 28: WP-32 I3, the hash-checked pip line's pin.
        assert len(lines) == len(pins) == 28
        kinds = [k for k, _v, _t in pins]
        # expect 4 -> 3: WP-31 A5, as above.  shown 17 -> 16: WP-31 B4b.
        # shown 16 -> 17: WP-31 H2k, as above.  17 -> 19: WP-31 I2.
        # 19 -> 20: WP-32 I3, the hash-checked pip line.
        assert (kinds.count("special"), kinds.count("expect"),
                kinds.count("check"), kinds.count("shown")) == (1, 3, 4, 20)

    def test_every_pin_names_what_the_help_holds(self, pins, groups, shown):
        texts = [c.text for c in _commands(groups)]
        shown_texts = [s.text for s in shown]
        for kind, _value, text in pins:
            pool = shown_texts if kind == "shown" else texts
            assert text in pool, "the %s pin names nothing: %r" % (kind, text)

    def test_every_kind_has_a_handler(self, pins):
        for kind, value, _text in pins:
            if kind == "expect":
                assert re.match(r"^[1-9][0-9]*$", value), value
            else:
                assert value in _HANDLERS[kind], (kind, value)

    def test_the_cscript_accepts_the_same_handlers(self, cscript_source):
        for kind, values in _HANDLERS.items():
            for v in values:
                assert '"%s"' % v in cscript_source, (kind, v)

    def test_every_example_that_may_not_run_as_written_is_pinned(
            self, pins, groups):
        special = {text for kind, _v, text in pins if kind == "special"}
        unpinned = [c for c in _commands(groups)
                    if hx.must_pin(c.text) and c.text not in special]
        assert not unpinned, (
            "may not run as written and has no special pin in "
            "test_help_examples.cscript: %r" % unpinned)

    def test_the_examples_that_may_not_run_as_written(self, groups):
        assert [c.text for c in _commands(groups) if hx.must_pin(c.text)] \
            == ["dash serve, port(5006)"] * 2

    def test_a_refusal_pinned_is_one_the_help_shows(self, pins, groups):
        """An example the help presents as refused shows the refusal."""
        by_text = {c.text: c for c in _commands(groups)}
        expect = [text for kind, _v, text in pins if kind == "expect"]
        # 4 -> 3: WP-31 A5, as above.
        assert len(expect) == 3
        for text in expect:
            assert by_text[text].outputs, text

    def test_every_shown_command_is_pinned(self, pins, shown):
        pinned = {text for kind, _v, text in pins if kind == "shown"}
        assert not [s for s in shown if s.text not in pinned]


class TestTheCscriptReadsThroughThisReader:
    """The Stata suite and this one agree because they share one reader:
    the cscript takes its examples from help_examples.stata_plan(), judges
    each log with help_examples.stata_judge(), checks what is shown with
    help_examples.stata_check_shown(), and holds the reader to its own plain
    count of the example lines."""

    def test_it_takes_the_examples_from_the_reader(self, cscript_source):
        assert "import help_examples" in cscript_source
        for fn in ("stata_plan()", "stata_judge()", "stata_check_shown()"):
            assert "help_examples." + fn in cscript_source, fn

    def test_it_counts_the_example_lines_itself(self, cscript_source):
        assert "_hx_count_prompts" in cscript_source
        assert 'strpos(ln, "{cmd:. ")' in cscript_source

    def test_it_starts_each_group_with_no_data(self, cscript_source):
        loop = cscript_source.split("capture dash clear", 1)[1]
        assert loop.lstrip().startswith("clear\n")


# ---------------------------------------------------------------------------
# The reader's rules, on made-up help text
# ---------------------------------------------------------------------------

def _help(*lines):
    return "\n".join(lines)


def _read(*lines):
    return hx.extract_text(_help(*lines), "t.sthlp")


def _shown(*lines):
    return [(s.lines, s.form, s.text)
            for s in hx.shown_text(_help(*lines), "t.sthlp")]


class TestTheReadersRules:

    def test_a_heading_starts_a_group_and_the_setup_belongs_to_it(self):
        gs = _read("{title:Examples}", "",
                   "{pstd}{ul:One}{p_end}",
                   "{phang2}{cmd:. sysuse auto, clear}{p_end}",
                   "{phang2}{cmd:. dash scatter mpg weight}{p_end}",
                   "",
                   "{pstd}{ul:Two}{p_end}",
                   "{phang2}{cmd:. dash clear}{p_end}")
        assert [(g.label, [c.text for c in g.commands]) for g in gs] == [
            ("Examples / One", ["sysuse auto, clear",
                                "dash scatter mpg weight"]),
            ("Examples / Two", ["dash clear"]),
        ]

    def test_a_blank_line_ends_a_group(self):
        gs = _read("{phang2}{cmd:. dash clear}{p_end}", "",
                   "{phang2}{cmd:. dash clear}{p_end}")
        assert len(gs) == 2

    def test_a_dlgtab_is_part_of_the_label(self):
        gs = _read("{title:Subcommands}", "{dlgtab:dash serve}",
                   "{pstd}{ul:Inheriting.}  prose", "",
                   "{phang2}{cmd:. dash clear}{p_end}")
        assert gs[0].label == "Subcommands / dash serve / Inheriting."

    def test_a_continuation_is_joined(self):
        gs = _read("{phang2}{cmd:. dash scatter mpg weight, ///}{p_end}",
                   "{phang2}{cmd:.     title(x)}{p_end}")
        (c,) = gs[0].commands
        assert c.text == "dash scatter mpg weight, title(x)"
        assert c.lines == (1, 2)

    def test_a_continuation_with_nothing_after_it_is_refused(self):
        with pytest.raises(hx.HelpExampleError):
            _read("{phang2}{cmd:. dash scatter mpg weight, ///}{p_end}", "")

    def test_the_output_shown_belongs_to_the_command_above(self):
        gs = _read("{phang3}{cmd:. dash (scatter mpg weight, discrete)}{p_end}",
                   "{phang3}{cmd:option discrete not allowed}{p_end}",
                   "{phang3}{cmd:. dash clear}{p_end}")
        a, b = gs[0].commands
        assert a.outputs == ["option discrete not allowed"]
        assert a.output_lines == [2]
        assert b.outputs == []

    def test_smcl_escapes_are_undone(self):
        gs = _read("{phang2}{cmd:. dash scatter y x, note({c -(}a{c )-} "
                   "{c 124} {c |} {c S|}x {c 'g}y' {c 0x41}{char 66})}{p_end}")
        assert gs[0].commands[0].text == \
            "dash scatter y x, note({a} | | $x `y' AB)"

    def test_a_template_is_refused(self):
        with pytest.raises(hx.HelpExampleError):
            _read("{phang2}{cmd:. dash scatter {it:y} {it:x}}{p_end}")

    def test_an_unknown_character_code_is_refused(self):
        with pytest.raises(hx.HelpExampleError):
            _read("{phang2}{cmd:. dash scatter y x, note({c TLC})}{p_end}")

    def test_prose_beside_an_example_is_refused(self):
        with pytest.raises(hx.HelpExampleError):
            _read("{pstd}Type {cmd:. dash clear} to start again.{p_end}")

    def test_comments_are_removed_as_a_do_file_reader_removes_them(self):
        gs = _read('{phang2}{cmd:. display "a // b" // note}{p_end}',
                   "{phang2}{cmd:. display 1 /* x */ + 1}{p_end}",
                   "{phang2}{cmd:. * a comment stays, and runs}{p_end}")
        texts = [" ".join(c.text.split()) for c in gs[0].commands]
        assert texts == ['display "a // b"', "display 1 + 1",
                         "* a comment stays, and runs"]

    def test_a_directive_prose_runs_over_two_lines_is_no_error(self):
        assert _read("{pstd}twoway says ({cmd:bands must be between 1 and",
                     "200}).") == []


class TestWhatTheReaderShowsAndDoesNotRun:

    def test_a_command_line_without_the_prompt_is_shown(self):
        assert _read("{pstd}Run it with:", "",
                     "{phang2}{cmd:python app.py}{p_end}") == []
        assert _shown("{pstd}Run it with:", "",
                      "{phang2}{cmd:python app.py}{p_end}") == [
            ((3,), "line", "python app.py")]

    def test_a_bare_line_continues_the_command_line_above(self):
        assert _shown("{phang2}{cmd:python: f(1,}",
                      '{cmd:"two")}') == [((1, 2), "line",
                                           'python: f(1, "two")')]

    def test_the_wrapped_end_of_a_synopt_is_not_a_command(self):
        assert _shown("{synopt:{opt bgcolor(color)}}shorthand for",
                      "    {cmd:graphregion(color())}{p_end}") == []

    def test_the_syntax_section_is_grammar(self):
        assert _shown("{title:Syntax}", "{p 8 17 2}", "{cmd:dash clear}",
                      "{cmd:dash kpi} {it:stat}", "",
                      "{title:Description}", "{pstd}text") == []

    def test_a_dash_command_in_a_sentence_is_shown(self):
        got = _shown("{pstd}{cmd:dash build, saving(a.py) server} writes an "
                     "app; {cmd:dash build} and {cmd:dash serve} are "
                     "subcommands, {cmd:dash} the command; dash prints "
                     "{cmd:dash: a note} and {cmd:dash build: an error}.")
        assert got == [((1,), "inline", "dash build, saving(a.py) server")]

    def test_the_output_of_an_example_is_not_shown(self):
        assert _shown("{phang3}{cmd:. dash (scatter mpg weight, discrete)}"
                      "{p_end}",
                      "{phang3}{cmd:option discrete not allowed}{p_end}") \
            == []


# ---------------------------------------------------------------------------
# What may not run as written
# ---------------------------------------------------------------------------

class TestWhatMayNotRunAsWritten:

    @pytest.mark.parametrize("text", [
        "dash serve", "dash serve, port(5006)",
        "capture dash serve, port(1)", "noi dash serve",
        "dash_setup", "python: import os", "shell ls", "!ls",
        "net install dash, from(x)", "ssc install jsonio", "webuse auto",
        'use "https://example.com/a.dta"', "cd /tmp",
        "set scheme s1color, permanently", "clear all", "clear *", "exit",
        "program drop _all", "macro drop _all", "mata: mata clear",
        "log close _all", "discard",
    ])
    def test_it_is_named(self, text):
        assert hx.must_pin(text)

    @pytest.mark.parametrize("text", [
        "dash scatter mpg weight", "dash build, saving(app.py) server replace",
        "sysuse auto, clear", "sysuse sp500, clear",
        "global dash_max_by_groups 250",
        "* Run outside Stata:  python app.py --show",
        "dash serverish mpg weight", "clear",
        "dash kpi mean(mpg), title(x) name(k1)",
    ])
    def test_it_is_not(self, text):
        assert hx.must_pin(text) == ""


# ---------------------------------------------------------------------------
# The judge, on made-up logs
# ---------------------------------------------------------------------------

class TestTheJudge:

    NOTE = "dash: ignoring unsupported option(s): play() text()"
    TWO = ("dash: [aweight=price+1] must name one variable; dash cannot "
           "evaluate a weight expression.\n"
           "      Generate it first: generate double w = price+1\n")
    ONE = ("dash: [aweight=price+1] must name one variable; dash cannot "
           "evaluate a weight expression. Generate it first: generate double "
           "w = price+1")

    def test_a_clean_run_passes(self):
        assert hx.judge("dash: dashboard saved to x.html\n", 0, 0, []) == []

    def test_the_return_code_is_held(self):
        (p,) = hx.judge("", 198, 0, [])
        assert "rc 198" in p

    def test_the_note_shown_passes(self):
        assert hx.judge(self.NOTE + "\n", 0, 0, [self.NOTE]) == []

    def test_a_note_with_more_after_it_is_not_the_note_shown(self):
        """What the s() leak printed after the refused weight example."""
        probs = hx.judge(self.NOTE + " [aweight]\n", 0, 0, [self.NOTE])
        assert any("the help shows" in p for p in probs)
        assert any("names an option as ignored" in p for p in probs)

    def test_a_note_the_help_does_not_show_is_flagged(self):
        (p,) = hx.judge("dash: ignoring unsupported option(s): [aweight]\n",
                        0, 0, [])
        assert "names an option as ignored" in p

    def test_a_message_on_two_lines_matches_the_line_the_help_shows(self):
        assert hx.judge(self.TWO, 198, 198, [self.ONE]) == []

    def test_a_wrapped_line_is_rejoined(self):
        log = ("dash build: scheme() must be a shipped scheme, a theme, or a "
               ".scheme file in th\n> e working directory (got: x)\n")
        want = ("dash build: scheme() must be a shipped scheme, a theme, or a "
                ".scheme file in the working directory (got: x)")
        assert hx.judge(log, 198, 198, [want]) == []

    def test_a_refusal_not_shown_is_reported(self):
        (p,) = hx.judge("something else\n", 198, 198, [self.ONE])
        assert "the log does not" in p

    @pytest.mark.parametrize("line", [
        "/p/dash_render.py:1: UserWarning: dash: graph 'g' plot 2 (lpoly) "
        "drew nothing from 74 observations.",
        "/p/x.py:9: FutureWarning: something changes",
        "dash: legend() sub-option(s) not implemented and ignored: span",
        "Traceback (most recent call last):",
    ])
    def test_a_warning_a_sub_option_note_or_a_traceback_is_flagged(self, line):
        assert len(hx.judge(line + "\n", 0, 0, [])) == 1

    #: WP-30 P1.26a: dash's notes print as twoway prints its notes, one
    #: "(note:  dash: ...)" line, with no "Warning:" in it; dash's copy of
    #: twoway's estimator note keeps its own words.
    @pytest.mark.parametrize("line", [
        "(note:  dash: graph 'g' plot 2 (lpoly) drew nothing from 74 "
        "observations.)",
        "(note:  dash: mcolor(x) is not a recognised colour; using the "
        "scheme's default.)",
        "dash: graph 'g' plot 2 (lfit): (note:  regress could not fit model)",
    ])
    def test_a_note_line_is_flagged(self, line):
        assert len(hx.judge(line + "\n", 0, 0, [])) == 1

    def test_an_ignored_option_note_keeps_its_reason(self):
        (p,) = hx.judge("(note:  dash: ignoring unsupported option(s): "
                        "[aweight])\n", 0, 0, [])
        assert "names an option as ignored" in p

    #: What Bokeh 3.9 logs to stderr when it finds the document it is saving
    #: broken, measured 24sep2026 (a glyph naming a column its source lacks,
    #: a figure with no renderers, a layout with no children): Python
    #: logging's basic format, LEVEL:logger:message.  The first is 265
    #: characters, so a Stata log at linesize 255 shows it wrapped, and it
    #: is given here as the log shows it.
    BOKEH_ERROR = ("ERROR:bokeh.core.validation.check:E-1001 (BAD_COLUMN_NAME): "
                   "Glyph refers to nonexistent column name. This could either "
                   "be due to a misspelling or typo, or due to an expected "
                   "column being missing. : y='b' [no close matches] "
                   "{renderer: GlyphRenderer(id='p1046', ...)}")
    BOKEH_LOGGED = [
        BOKEH_ERROR[:255] + "\n> " + BOKEH_ERROR[255:],
        "WARNING:bokeh.core.validation.check:W-1000 (MISSING_RENDERERS): "
        "Plot has no renderers: figure(id='p1053', ...)",
        "WARNING:bokeh.core.validation.check:W-1002 (EMPTY_LAYOUT): Layout "
        "has no children: Column(id='p1087', ...)",
    ]

    @pytest.mark.parametrize("logged", BOKEH_LOGGED)
    def test_a_line_bokeh_logs_is_flagged(self, logged):
        """help_examples.FLAGGED's LEVEL:logger: pattern.  Its "Warning:"
        pattern is case-sensitive and never matched these (24sep2026): an
        example whose page Bokeh logged as broken was judged clean, and
        with the LEVEL:logger: pattern taken out every test here passed."""
        whole = hx.log_lines(logged)[0]
        assert hx.judge(logged + "\n", 0, 0, []) == [
            "prints a logged warning or error: " + whole]

    def test_a_logged_line_the_help_shows_is_not_flagged(self):
        """The control: the pattern flags what the help does not show, not
        the words themselves."""
        line = self.BOKEH_LOGGED[1]
        assert hx.judge(line + "\n", 0, 0, [line]) == []

    def test_a_line_logged_below_warning_is_not_flagged(self):
        """INFO is no problem: the pattern names WARNING, ERROR and
        CRITICAL -- an INFO line in the same format is not flagged, and a
        CRITICAL one is."""
        info = "INFO:bokeh.server.server:Starting Bokeh server"
        critical = "CRITICAL:bokeh.server.server:Cannot start Bokeh server"
        assert hx.judge(info + "\n", 0, 0, []) == []
        assert hx.judge(critical + "\n", 0, 0, []) == [
            "prints a logged warning or error: " + critical]


class TestSavedFileAndRegisteredName:

    @pytest.mark.parametrize("text,want", [
        ("dash scatter mpg weight, saving(scatter.html)", "scatter.html"),
        ("dash build, saving(app.py) server replace", "app.py"),
        ('dash scatter y x, sav("a b.html")', "a b.html"),
        ("dash scatter y x, saving(out)", "out.html"),
        ("dash scatter y x, saving(g.gph)", "g.html"),
        ("dash scatter y x, saving(o.html, replace)", "o.html"),
        ("dash scatter y x", ""),
    ])
    def test_saved_file(self, text, want):
        assert hx.saved_file(text) == want

    @pytest.mark.parametrize("text,want", [
        ("dash scatter mpg weight, name(s1) title(x)", "s1"),
        ("dash kpi mean(mpg), title(x) name(k1)", "k1"),
        ("dash (scatter y x), name(g1, replace)", "g1"),
        ("dash build, saving(x.html)", ""),
        ("dash scatter y x, rename(q)", ""),
        ("global dash_max_by_groups 250", ""),
    ])
    def test_registered_name(self, text, want):
        assert hx.registered_name(text) == want


# ---------------------------------------------------------------------------
# Every lpoly example draws a curve
# ---------------------------------------------------------------------------

_LPOLY = re.compile(r"\b(lpolyci|lpoly)\s+([A-Za-z_]\w*)\s+([A-Za-z_]\w*)")


def _options_of(text, at):
    """The option text of the segment starting at *at*: from its comma to the
    parenthesis that closes the segment, or to the end."""
    depth, i, comma = 0, at, None
    while i < len(text):
        ch = text[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            if depth == 0:
                break
            depth -= 1
        elif ch == "," and depth == 0 and comma is None:
            comma = i
        i += 1
    return text[comma + 1:i] if comma is not None else ""


def _lpoly_examples(groups):
    out = []
    for c in _commands(groups):
        for m in _LPOLY.finditer(c.text):
            opts = _options_of(c.text, m.end())
            bw = re.search(r"\bbw(?:i(?:d(?:t(?:h)?)?)?)?\(\s*([^)\s]+)\s*\)",
                           opts)
            out.append((c, m.group(1), m.group(2), m.group(3),
                        bw.group(1) if bw else None))
    return out


class TestEveryLpolyExampleDrawsACurve:

    def test_the_help_has_one(self, groups):
        assert _lpoly_examples(groups), "no lpoly example found to check"

    def test_it_draws_a_curve_on_auto(self, groups):
        from test_statistical_helpers import (  # noqa: E402
            _AUTO_MPG, _AUTO_PRICE, _AUTO_WEIGHT, _lp_xy)
        auto = {"mpg": _AUTO_MPG, "price": _AUTO_PRICE,
                "weight": _AUTO_WEIGHT}
        for c, ptype, y, x, bw in _lpoly_examples(groups):
            assert y in auto and x in auto, (
                "add %s and %s to this test's auto columns: %r" % (y, x, c))
            opts = {"bwidth": bw} if bw else {}
            _xs, ys = _lp_xy("map_" + ptype, auto[x], auto[y], opts,
                             dataset_rows=74)
            drawn = int(np.isfinite(ys).sum())
            assert drawn >= 2, (
                "%s:%d draws %d point(s) of its curve -- a line needs two; "
                "bwidth() on %s is in the units of x: %r"
                % (c.file, c.line, drawn, ptype, c.text))
