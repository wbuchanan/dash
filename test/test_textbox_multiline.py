"""Stata's multi-string text form must render as multiple lines.

Stata lets a text option take several quoted strings, each rendering as its
own line::

    twoway scatter mpg weight, title("line one" "line two")

Measured against real Stata, that stores ``mtextq(`""line one" "line two""')``
in the .gph -- two separate strings -- and the graph draws two lines.

dash collapsed every such value onto one line, for two separate reasons:

* ``title()`` and ``subtitle()`` were declared ``string`` rather than
  ``string asis`` in dash.ado, so Stata stripped the quotes at capture and the
  spec carried ``line one line two``.  The information was gone before the
  renderer ran.  ``note()`` and ``caption()`` were already ``asis``; that
  difference was the symptom people noticed, not the defect.
* ``_parse_textbox_opt`` then joined the quoted runs it *did* find with a
  SPACE, so even note() and caption() rendered ``note one note two``.

BokehJS renders ``\\n`` as a real line break in both ``Title`` and ``Label`` --
verified visually in a browser against bokeh 3.9 before this was written, not
assumed from the model accepting the character.

Quoted text, read as Stata reads it (24sep2026).  The spec carries a text
option as typed: ``title(`"a "b" c"')`` arrives as `` `"a "b" c"' ``.  The
parser took every plain-quoted run as a line (``re.findall(r'"([^"]*)"')``),
so that title drew the two lines ``a `` and `` c`` and lost ``"b"`` -- in both
modes -- and the comma scan toggled on every double quote, so a comma inside a
compound string could start the sub-options: ``title(`"a "b, color(red)"')``
drew ``a `` in red.  twoway draws ``a "b" c`` and ``a "b, color(red)`` in the
scheme's colour.  Stata's own reading is textbox.class (lines 84-104 in
StataNow 19.5): text with no double quote is one line; otherwise each token
``gettoken`` returns is a line, until the first empty one.  The sub-options
begin at the comma ``_parse comma`` finds in _fr_title_parse_and_log.ado:
the first outside every string and every parenthesis.  Every expected value
below was measured against twoway's drawing (graph export .svg) or, where
twoway refuses the command, textbox.class's own loop run on the text.
"""
import html as _htmllib
import json
import os
import re
import sys
import time
import warnings

import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
from conftest import make_data_json, make_spec, exec_app

_DF = pd.DataFrame({"y": [1.0, 2.0, 3.0, 4.0], "x": [1.0, 2.0, 3.0, 4.0]})


def _render(tmp_path, graph_options):
    """Render one scatter with the given graph_options; return the renderer."""
    data_path = tmp_path / "data.json"
    data_path.write_text(json.dumps(make_data_json(_DF)), encoding="utf-8")
    spec = {
        "graphs": [{
            "plots": [{"type": "scatter", "yvar": "y", "xvar": "x",
                       "options": {}, "if_expr": "", "in_expr": ""}],
            "graph_options": graph_options,
            "if_expr": "", "in_expr": "",
        }],
        "build_options": {"layout": "1 1", "level": "95", "formats": {}},
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    renderer = dr.DashRenderer(str(spec_path), str(data_path))
    renderer.render()
    return renderer


def _labels(renderer):
    """Every text box the figure carries -- a Label, or a side-panel Title
    other than the figure's own title -- as a list of their text.
    Flipped (WP-30 P1.2a): Labels only was wrong because twoway places
    subtitle(), note() and caption() by the scheme's clock, which S15
    draws as side-panel Titles."""
    from bokeh.models import Label, Title
    out = []
    for fig in renderer.figures.values():
        for panel in ("above", "below", "left", "right", "center"):
            for item in getattr(fig, panel, []):
                if isinstance(item, Label) or (
                        isinstance(item, Title) and item is not fig.title):
                    out.append(item.text)
    return out


# ============================================================
# _parse_textbox_opt — the unit under the behaviour
# ============================================================

class TestParseTextboxOpt:
    """The parser must separate the strings, not concatenate them."""

    def test_two_quoted_strings_become_two_lines(self):
        text, _ = dr._parse_textbox_opt('"line one" "line two"')
        assert text == "line one\nline two", (
            "two quoted strings must join with a newline, not a space -- "
            "Stata renders them as two lines"
        )

    def test_three_quoted_strings_become_three_lines(self):
        text, _ = dr._parse_textbox_opt('"a" "b" "c"')
        assert text == "a\nb\nc"

    def test_a_single_quoted_string_is_unchanged(self):
        text, _ = dr._parse_textbox_opt('"just one"')
        assert text == "just one"
        assert "\n" not in text

    def test_abbreviations_are_the_same_sub_options(self):
        """WP-28 B3: Stata's minimum abbreviations are the sub-options."""
        assert dr._parse_textbox_opt('"a", si(large) c(red)') == \
            dr._parse_textbox_opt('"a", size(large) color(red)')

    def test_an_unquoted_value_is_unchanged(self):
        text, _ = dr._parse_textbox_opt("plaintext")
        assert text == "plaintext"
        assert "\n" not in text

    def test_an_empty_value_is_unchanged(self):
        text, opts = dr._parse_textbox_opt("")
        assert text == ""
        assert opts == {}

    def test_suboptions_still_parse_alongside_multiple_strings(self):
        text, opts = dr._parse_textbox_opt('"a" "b", size(large)')
        assert text == "a\nb"
        assert opts.get("size") == "large"

    def test_suboptions_still_parse_with_one_string(self):
        text, opts = dr._parse_textbox_opt('"only", size(small) color(red)')
        assert text == "only"
        assert opts.get("size") == "small"
        assert opts.get("color") == "red"


class TestCommaInsideTheUsersText:
    """A comma in the text is the user's, not a sub-option separator.

    The sub-option keywords are ordinary English -- size, color, just, width,
    height, style, span, box, margin, position -- so a bare regex search over
    the whole value truncated real titles.  Measured before the fix:
    ``title("Sales, size matters")`` rendered as ``Sales``.
    """

    @pytest.mark.parametrize("raw,expected", [
        ('"Sales, size matters"', "Sales, size matters"),
        ('"Revenue, color coded"', "Revenue, color coded"),
        ('"A, just testing"', "A, just testing"),
        ('"Wide, width of it"', "Wide, width of it"),
        ('"Tall, height of it"', "Tall, height of it"),
        ('"Plain, ordinary text"', "Plain, ordinary text"),
    ])
    def test_a_comma_inside_quotes_does_not_truncate(self, raw, expected):
        text, opts = dr._parse_textbox_opt(raw)
        assert text == expected
        assert opts == {}

    def test_a_genuine_suboption_still_splits(self):
        text, opts = dr._parse_textbox_opt('"Real, text here", size(large)')
        assert text == "Real, text here"
        assert opts.get("size") == "large"

    def test_an_unquoted_value_still_splits_on_a_real_suboption(self):
        text, opts = dr._parse_textbox_opt("nosize, size(large)")
        assert text == "nosize"
        assert opts.get("size") == "large"

    def test_multiple_strings_with_a_comma_in_one_of_them(self):
        text, opts = dr._parse_textbox_opt('"a, size b" "c", color(red)')
        assert text == "a, size b\nc"
        assert opts.get("color") == "red"

    def test_it_reaches_the_document(self, tmp_path):
        r = _render(tmp_path, {"note": '"Source, size of sample: 74"'})
        assert "Source, size of sample: 74" in _labels(r)


# ============================================================
# End to end — the text that reaches the document
# ============================================================

class TestMultilineReachesTheDocument:

    def test_title_renders_two_lines(self, tmp_path):
        r = _render(tmp_path, {"title": '"line one" "line two"'})
        titles = [f.title.text for f in r.figures.values()]
        assert titles == ["line one\nline two"]

    def test_subtitle_renders_two_lines(self, tmp_path):
        r = _render(tmp_path, {"subtitle": '"sub one" "sub two"'})
        assert "sub one\nsub two" in _labels(r)

    def test_note_renders_two_lines(self, tmp_path):
        r = _render(tmp_path, {"note": '"note one" "note two"'})
        assert "note one\nnote two" in _labels(r)

    def test_caption_renders_two_lines(self, tmp_path):
        r = _render(tmp_path, {"caption": '"cap one" "cap two"'})
        assert "cap one\ncap two" in _labels(r)

    @pytest.mark.parametrize("key", ["title", "subtitle", "note", "caption"])
    def test_a_single_string_never_gains_a_newline(self, tmp_path, key):
        """The common case must not regress into a spurious line break."""
        r = _render(tmp_path, {key: '"just one"'})
        if key == "title":
            got = [f.title.text for f in r.figures.values()]
        else:
            got = _labels(r)
        assert any(t == "just one" for t in got), got
        assert not any("\n" in (t or "") for t in got)

    @pytest.mark.parametrize("key", ["title", "subtitle", "note", "caption"])
    def test_an_unquoted_value_never_gains_a_newline(self, tmp_path, key):
        r = _render(tmp_path, {key: "plaintext"})
        if key == "title":
            got = [f.title.text for f in r.figures.values()]
        else:
            got = _labels(r)
        assert any(t == "plaintext" for t in got), got
        assert not any("\n" in (t or "") for t in got)

    def test_the_caption_is_positioned_where_it_can_be_drawn(self, tmp_path):
        """A negative screen offset clips the Label out of its own row.

        The caption carried y = -12.0, meant to push it below the note.  What
        separates them is the order they are added in -- add_layout(...,
        "below") gives each its own row -- so the offset only pushed the
        caption outside the row Bokeh sized for it.  Measured in a browser
        against bokeh 3.9: an identical Label renders at y = 0.0 and y = 2.0
        and does not render at all at y = -12.0.  No dash dashboard has ever
        drawn a caption.  A model-only assertion cannot see this, so assert
        the property that makes it drawable.
        """
        # Flipped (WP-30 P1.2a): both are Title rows of fig.below, note
        # first; a Title has no screen offset to clip it out of its row.
        from bokeh.models import Title
        r = _render(tmp_path, {"note": '"N"', "caption": '"C"'})
        for fig in r.figures.values():
            rows = [i.text for i in fig.below if isinstance(i, Title)]
            assert rows == ["N", "C"], rows

    def test_the_caption_is_added_after_the_note(self, tmp_path):
        """Stata puts the note at ring(4) and the caption at ring(5)."""
        # Flipped (WP-30 P1.2a): the rows are Titles.
        from bokeh.models import Title
        r = _render(tmp_path, {"note": '"N"', "caption": '"C"'})
        for fig in r.figures.values():
            order = [i.text for i in fig.below if isinstance(i, Title)]
            if "N" in order and "C" in order:
                assert order.index("N") < order.index("C"), order

    def test_the_stray_quotes_never_reach_the_document(self, tmp_path):
        """Whatever the join, a literal '"' must not survive into the text.

        This is the property the original report was really about: note() is
        declared `asis` so its spec value carries quotes, and they must be
        consumed by the parser rather than drawn on the page.
        """
        r = _render(tmp_path, {"note": '"N text"', "caption": '"C text"'})
        labels = _labels(r)
        # The note and caption must actually be drawn, or the loop below
        # runs zero times and the "no stray quote" property is asserted
        # against nothing (measured 24sep2026: the render draws
        # ['N text', 'C text']).
        assert "N text" in labels and "C text" in labels, labels
        for text in labels:
            assert '"' not in (text or ""), text


# ============================================================
# Quoted text, read as Stata reads it (24sep2026)
# ============================================================

_BT, _AP = "`", "'"


def _cq(text):
    """*text* in Stata's compound quotes, as the spec carries a compound-
    quoted string: a backtick and a double quote, the text, a double quote
    and an apostrophe."""
    return _BT + '"' + text + '"' + _AP


#: (id, the value as the spec carries it, the lines twoway draws).  The id
#: names the measurement: each f, g and m id is a 24sep2026 run of
#: ``twoway scatter mpg weight, title(<value>)`` in StataNow 19.5 (console
#: binary), exported to .svg and its title lines read.  g10 and g11 are
#: forms twoway itself refuses -- r(109) "type mismatch" and r(100) ")
#: required": its own title code puts the text inside compound quotes, and
#: an opening "' ends them -- so their lines are textbox.class's loop, run
#: in Stata on the text by value.  dash stores both forms.
_MEASURED_LINES = [
    ("f01-compound-holding-quotes", _cq('a "b" c'), ['a "b" c']),
    ("f02-two-plain-strings", '"line 1" "line 2"', ["line 1", "line 2"]),
    ("f03-compound-then-plain", _cq("x") + ' "y"', ["x", "y"]),
    ("f04-compound-apostrophe", _cq("it's"), ["it's"]),
    ("f05-compound-apostrophe-first", _cq("'90s cars"), ["'90s cars"]),
    ("f06-compound-ending-in-a-quote", _cq('a "b"') + ' "second"',
     ['a "b"', "second"]),
    ("f07-bare-words-around-a-string", 'a "b" c', ["a", "b", "c"]),
    ("f08-no-quotes-one-line", "a b c", ["a b c"]),
    ("f09-nested-compound", _cq("a " + _cq("nested") + " b"),
     ["a " + _cq("nested") + " b"]),
    ("f13-strings-without-a-blank", _cq("x") + '"y"', ["x", "y"]),
    ("f14-bare-word-after-a-string", '"a"b', ["a", "b"]),
    ("f15-quotes-inside-a-word", 'a"b"c', ['a"b"c']),
    ("f19-compound-odd-quote", _cq('a"b'), ['a"b']),
    ("f20-mixed", '"x" ' + _cq('y "z"') + " w", ["x", 'y "z"', "w"]),
    ("f21-apostrophes-in-both", _cq("it's") + " \"and 'more'\"",
     ["it's", "and 'more'"]),
    ("f22-compound-apostrophe-alone", _cq("'"), ["'"]),
    ("f23-plain-apostrophe-not-first", "\"a '90s car\"", ["a '90s car"]),
    ("f29-bare-and-quoted-words", 'a "b c" d e', ["a", "b c", "d", "e"]),
    ("f30-compound-holding-both", _cq("a " + _cq("b") + ' "c" d'),
     ["a " + _cq("b") + ' "c" d']),
    ("f31-plain-bare-plain", '"a" b "c"', ["a", "b", "c"]),
    ("f32-blanks-around", '  "a"   "b"  ', ["a", "b"]),
    ("g01-a-quoted-blank-inside-a-word", 'a"b c"d', ['a"b c"d']),
    ("g10-plain-apostrophe-first", "\"'90s cars\"", ["'90s cars"]),
    ("g11-second-string-apostrophe-first", "\"x\" \"'90s\"",
     ["x", "'90s"]),
    ("g22-no-quotes-apostrophe-first", "'90s cars", ["'90s cars"]),
    ("g23-a-word-holding-a-string", '"a"b"c"', ["a", 'b"c"']),
    ("g24-nested-only", _cq(_cq("a")), [_cq("a")]),
    ("g27-a-blank-line", '" "', [" "]),
    ("g33-no-quotes-ending-in-apostrophe", "the 90s'", ["the 90s'"]),
    ("g34-compound-ending-in-apostrophe", _cq("the 90s'"), ["the 90s'"]),
    ("g35-plain-then-compound-apostrophe", '"x" ' + _cq("'90s cars"),
     ["x", "'90s cars"]),
    ("m01-compound-inside-a-word", "a" + _cq("b c") + "d",
     ["a" + _cq("b c") + "d"]),
    ("m03-quoted-blank-in-a-word", '"a" b"c d"e f', ["a", 'b"c d"e', "f"]),
    ("m04-a-word-right-after-a-string", 'a "b"c d', ["a", "b", "c", "d"]),
    ("m05-plain-right-after-compound", _cq("a") + '"b"', ["a", "b"]),
]

#: textbox.class reads lines while gettoken returns one that is not empty
#: (``while `"`line'"' != `""'``), so twoway draws nothing after an empty
#: string -- measured as above.
_MEASURED_EMPTY = [
    ("f17-an-empty-string-ends-the-lines", '"a" "" "b"', ["a"]),
    ("g25-a-trailing-empty-string", '"a"  ""', ["a"]),
    ("g26-an-empty-first-string-draws-nothing", '"" "a"', []),
    ("g28-after-a-bare-word", 'x "" y', ["x"]),
    ("f16-one-empty-string", '""', []),
    ("f18-one-empty-compound", _cq(""), []),
]

#: (id, value, the lines, the sub-options dash reads).  The c ids are
#: 24sep2026 runs as above, with _fr_title_parse_and_log's own
#: ``_parse comma`` run on the value by value: its split is the first comma
#: outside every string, compound ones included, and every parenthesis.  A
#: color(red) twoway applied is read from the drawing's fill.
_MEASURED_SPLITS = [
    ("f10-a-comma-inside-a-compound", _cq("x, size(large)"),
     ["x, size(large)"], {}),
    ("c02-an-odd-quote-then-a-comma", _cq('a "b, size(large)'),
     ['a "b, size(large)'], {}),
    ("c13-an-odd-quote-no-blank", _cq('a"b, size(large)'),
     ['a"b, size(large)'], {}),
    ("c01-a-comma-in-a-quote-inside-a-word", 'a"b, size(large) c"d',
     ['a"b, size(large) c"d'], {}),
    ("c03-a-comma-in-parentheses", "x (a, size(large)) y",
     ["x (a, size(large)) y"], {}),
    ("c08-a-comma-after-inner-quotes", _cq('a "b" c, color(red)'),
     ['a "b" c, color(red)'], {}),
    ("c11-a-comma-in-a-nested-compound", _cq(_cq("n, size(large)")),
     [_cq("n, size(large)")], {}),
    ("c12-parentheses-after-a-string", '"x" (a, size(large))',
     ["x", "(a,", "size(large))"], {}),
    ("g16-a-comma-after-an-odd-quote", _cq('x"y", size(large)'),
     ['x"y", size(large)'], {}),
    ("f11-a-real-comma-after-a-compound", _cq('a "b"') + ", size(large)",
     ['a "b"'], {"size": "large"}),
    ("f12-a-comma-in-a-string-and-a-real-one",
     '"a, b" "c", size(large)', ["a, b", "c"], {"size": "large"}),
    ("f25-both-suboptions", _cq('a "b" c') + ", size(large) color(red)",
     ['a "b" c'], {"size": "large", "color": "red"}),
    ("c10-a-comma-in-the-second-string",
     '"a" "b, size(large)", color(red)', ["a", "b, size(large)"],
     {"color": "red"}),
    ("f35-a-blank-before-the-comma", _cq("a") + " , size(large)", ["a"],
     {"size": "large"}),
    ("c06-no-blank-after-the-comma", '"a",size(large)', ["a"],
     {"size": "large"}),
]


class TestTheTextIsReadAsStataReadsIt:
    """Each value draws the lines twoway draws for it.

    Measured 24sep2026 before the fix: f01 drew the two lines "a " and
    " c" (the "b" lost), f06 "a ", "" and "second", f07 "b" alone, f09
    "a `" and "' b", f15 "b"; c02 drew "a " with size(large) and c03
    "x (a" with it.
    """

    @pytest.mark.parametrize("raw,lines",
                             [c[1:] for c in _MEASURED_LINES],
                             ids=[c[0] for c in _MEASURED_LINES])
    def test_the_lines_are_twoways(self, raw, lines):
        text, opts = dr._parse_textbox_opt(raw)
        assert text == "\n".join(lines)
        assert opts == {}

    @pytest.mark.parametrize("raw,lines",
                             [c[1:] for c in _MEASURED_EMPTY],
                             ids=[c[0] for c in _MEASURED_EMPTY])
    def test_an_empty_string_ends_the_lines(self, raw, lines):
        """dash drew title("a" "" "b") as "a", a blank line and "b", and
        title("" "a") as a blank line and "a"; twoway draws "a", and no
        title at all."""
        text, _ = dr._parse_textbox_opt(raw)
        assert text == "\n".join(lines)

    @pytest.mark.parametrize("raw,lines,opts",
                             [c[1:] for c in _MEASURED_SPLITS],
                             ids=[c[0] for c in _MEASURED_SPLITS])
    def test_the_suboptions_begin_outside_every_string(self, raw, lines,
                                                       opts):
        text, got = dr._parse_textbox_opt(raw)
        assert text == "\n".join(lines)
        assert got == opts


class TestTextboxSplitPoint:
    """The index of the comma that begins the sub-options, or -1."""

    def test_a_comma_inside_a_compound_string_is_text(self):
        # The scan toggled on every double quote, so the odd inner quote
        # left this comma outside: it returned 6.
        assert dr._textbox_split_point(_cq('a "b, size(large)')) == -1

    def test_a_comma_inside_parentheses_is_text(self):
        # _parse comma binds parentheses (c03): it returned 4.
        assert dr._textbox_split_point("x (a, size(large)) y") == -1

    def test_the_comma_after_the_strings_splits(self):
        raw = _cq('a "b"') + ", size(large)"
        assert dr._textbox_split_point(raw) == raw.index(", size")
        raw2 = '"a" "b, size(large)", color(red)'
        assert dr._textbox_split_point(raw2) == raw2.index(", color")

    def test_a_comma_before_any_word_splits(self):
        """WP-28 B3: twoway's _parse comma splits before any name, not
        only a known one; a digit or a quote after the comma stays text."""
        assert dr._textbox_split_point('"a", bogus(1)') == 3
        assert dr._textbox_split_point('"a", 2 more') == -1
        assert dr._textbox_split_point('"a", "b"') == -1

    def test_a_comma_before_another_comma_or_the_end_splits(self):
        """WP-29 P0.4 (u04 A4): a comma followed, after blanks, by another
        comma or by nothing also opens the (empty) sub-option list, as
        twoway reads ytitle(A,) and ytitle(A,,)."""
        assert dr._textbox_split_point("A,") == 1
        assert dr._textbox_split_point("A,,") == 1
        assert dr._textbox_split_point("A, ,") == 1
        assert dr._textbox_split_point('"A",') == 3
        assert dr._textbox_split_point(",") == 0

    def test_a_stray_close_parenthesis_does_not_hide_the_comma(self):
        # -syntax- refuses an unbalanced parenthesis, so only a spec written
        # by hand holds one; a stray ")" closes nothing that was open.
        raw = 'a) "b", size(large)'
        assert dr._textbox_split_point(raw) == raw.index(", size")


class TestTextboxLines:
    """The lines of a text with its sub-options already cut off."""

    def test_text_without_a_double_quote_is_one_line(self):
        # textbox.class wraps such text in quotes whole (its ct == 0 case).
        assert dr._textbox_lines("it's a `b' $c") == ["it's a `b' $c"]

    def test_each_token_is_a_line_and_an_empty_one_ends_them(self):
        assert dr._textbox_lines(_cq('a "b"') + ' c "" d') == ['a "b"', "c"]

    def test_a_tab_is_not_a_separator(self):
        # gettoken parses on blanks: measured, title("a"<TAB>"b") drew "a"
        # and <TAB>"b" -- the tab, then the quoted b, as one word.
        assert dr._textbox_lines('"a"\t"b"') == ["a", '\t"b"']

    def test_nothing_is_no_lines(self):
        assert dr._textbox_lines("") == []


class TestTextboxStringEnd:
    """``(start, end, after)`` of the string that opens at an index."""

    def test_a_compound_string_ends_at_its_own_close(self):
        raw = _cq('a "b" c') + " x"
        assert dr._textbox_string_end(raw, 0) == (2, 9, 11)
        assert raw[2:9] == 'a "b" c'

    def test_nested_compound_strings_are_counted(self):
        assert dr._textbox_string_end(_cq(_cq("a")), 0) == (2, 7, 9)

    def test_a_plain_string_ends_at_the_next_quote(self):
        assert dr._textbox_string_end('"ab" c', 0) == (1, 3, 4)
        assert dr._textbox_string_end("\"'90s\"", 0) == (1, 5, 6)

    def test_an_unclosed_string_runs_to_the_end(self):
        # As gettoken reads one: measured 24sep2026, textbox.class's loop
        # reads "a b, and `"a b, as the one line a b.
        assert dr._textbox_string_end('"ab', 0) == (1, 3, 3)
        assert dr._textbox_string_end(_BT + '"ab', 0) == (2, 4, 4)


_PLOT = {"type": "scatter", "yvar": "y", "xvar": "x", "options": {},
         "if_expr": "", "in_expr": ""}
_CURDOC_ATTACH = "if __name__ != '__main__':\n    make_document(curdoc())"


def _drawn(fig):
    """The text one figure draws: its title (and the title's colour and
    size), its text boxes' text (Labels, and side-panel Titles since WP-30
    P1.2a), and its axis titles."""
    from bokeh.models import Label, Title
    labels = [m.text for side in ("above", "below", "left", "right",
                                  "center")
              for m in getattr(fig, side)
              if isinstance(m, Label) or (isinstance(m, Title)
                                          and m is not fig.title)]
    title = fig.title
    return {
        "title": None if title is None else title.text,
        "title_color": None if title is None else title.text_color,
        "title_size": None if title is None else title.text_font_size,
        "labels": sorted(labels),
        "xtitle": fig.xaxis[0].axis_label,
        "ytitle": fig.yaxis[0].axis_label,
    }


def _both_modes(tmp_path, graph_options):
    """``(saved, served, page)`` for one scatter with *graph_options*: what
    the saved renderer's figure draws, what the generated app's figure
    draws (its make_document, on a fresh Document), and the saved page."""
    from bokeh.document import Document
    from bokeh.models import Plot
    spec = make_spec([dict(_PLOT)])
    spec["graphs"][0]["graph_options"].update(graph_options)
    sp, dp, ap = (str(tmp_path / n) for n in ("spec.json", "data.json",
                                              "app.py"))
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    with open(dp, "w", encoding="utf-8") as fh:
        json.dump(make_data_json(_DF), fh)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        renderer = dr.DashRenderer(sp, dp)
        page = renderer.render()
        dr.ServerAppBuilder(sp, dp).build(ap)
    with open(ap, encoding="utf-8") as fh:
        src = fh.read()
    assert _CURDOC_ATTACH in src, "the generated app's curdoc attach moved"
    ns = {"__name__": "dash_textbox_app"}
    doc = Document()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        exec_app(src.replace(_CURDOC_ATTACH, "pass"), "dash_textbox_app.py",
                 ns)
        ns["make_document"](doc)
    saved = [_drawn(f) for f in renderer.figures.values()]
    served = [_drawn(f) for f in doc.select({"type": Plot})]
    assert len(saved) == 1 and len(served) == 1, (saved, served)
    return saved[0], served[0], page


def _page_titles(page):
    """The Title texts of the one document the saved page embeds, read back
    as the browser reads it: HTML-unescaped, then parsed."""
    from bokeh.document import Document
    from bokeh.models import Title
    blocks = re.findall(r'<script type="application/json" id="[^"]+">'
                        r'\s*(.*?)\s*</script>', page, re.S)
    docs = [d for b in blocks
            for d in json.loads(_htmllib.unescape(b)).values()]
    assert len(docs) == 1, f"{len(docs)} embedded documents, not 1"
    return [t.text for t in Document.from_json(docs[0]).select(
        {"type": Title})]


class TestBothModesDrawTheTextAsTyped:
    """The generated app copies _parse_textbox_opt and its helpers
    (ServerAppBuilder's copy list), so both modes read a text one way.
    Measured 24sep2026 before the fix: title(`"a "b" c"') drew "a \\n c"
    saved and served alike, and so did the saved page's document."""

    @pytest.mark.parametrize("raw,want", [
        (_cq('a "b" c'), 'a "b" c'),
        (_cq('a "b"') + ' "second"', 'a "b"\nsecond'),
        (_cq("it's"), "it's"),
        (_cq("'90s cars"), "'90s cars"),
        ("\"'90s cars\"", "'90s cars"),
        (_cq("the 90s'"), "the 90s'"),
        ('a "b" c', "a\nb\nc"),
    ], ids=["compound-holding-quotes", "multi-line-mix",
            "compound-apostrophe", "compound-apostrophe-first",
            "plain-apostrophe-first", "compound-ending-in-apostrophe",
            "bare-words-around-a-string"])
    def test_the_title_is_the_same_saved_and_served(self, tmp_path, raw,
                                                    want):
        saved, served, page = _both_modes(tmp_path, {"title": raw})
        assert saved["title"] == want
        assert served["title"] == want
        assert _page_titles(page) == [want]

    def test_subtitle_note_and_caption_are_the_same_saved_and_served(
            self, tmp_path):
        saved, served, _ = _both_modes(tmp_path, {
            "subtitle": _cq('a "b"') + ' "second"',
            "note": _cq("it's") + " " + _cq("'90s"),
            "caption": _cq('x "y" z'),
        })
        want = sorted(['a "b"\nsecond', "it's\n'90s", 'x "y" z'])
        assert saved["labels"] == want
        assert served["labels"] == want

    def test_an_axis_title_is_the_same_saved_and_served(self, tmp_path):
        # Measured: xtitle(`"a "b" c"') draws a "b" c, and ytitle(`"x"'
        # "y") x and y (m06, m09), as title() does.
        saved, served, _ = _both_modes(tmp_path, {
            "xtitle": _cq('a "b" c'), "ytitle": _cq("x") + ' "y"'})
        assert saved["xtitle"] == served["xtitle"] == 'a "b" c'
        assert saved["ytitle"] == served["ytitle"] == "x\ny"


class TestTextboxAdversarial:
    """CLAUDE.md rule 18 for the renderer's text boxes (the
    graph_text_options surface, test_adversarial_matrix.py): the text a
    string holds stays text, arrives as written, and is read in bounded
    time -- in both modes."""

    def test_text_inside_a_string_never_becomes_a_suboption(self, tmp_path):
        """Bypass: text that looks like the end of its string and a
        sub-option after it.  Measured 24sep2026, twoway draws each value
        below whole, in the colour and size title("T") gets (black,
        157.44px in the SVG), and applies a real color(red) size(huge) --
        red, 224.94px.  dash drew title(`"a "b, color(red) size(huge)"')
        as "a " in red and x (a, color(red) size(huge)) y as "x (a" in red,
        in both modes."""
        def _in(name):
            (tmp_path / name).mkdir()
            return tmp_path / name

        control, control_served, _ = _both_modes(_in("control"),
                                                 {"title": '"T"'})
        real, real_served, _ = _both_modes(
            _in("real"), {"title": '"T", color(red) size(huge)'})
        # The check can see a sub-option applied.
        assert real["title_color"] != control["title_color"]
        assert real["title_size"] != control["title_size"]
        assert real_served["title_color"] == real["title_color"]
        attempts = [
            (_cq('a "b, color(red) size(huge)'),
             'a "b, color(red) size(huge)'),
            ("x (a, color(red) size(huge)) y",
             "x (a, color(red) size(huge)) y"),
            (_cq(_cq("n") + ", color(red) size(huge)"),
             _cq("n") + ", color(red) size(huge)"),
            ('a"b, color(red) size(huge) c"d',
             'a"b, color(red) size(huge) c"d'),
        ]
        for i, (raw, want) in enumerate(attempts):
            saved, served, _ = _both_modes(_in(str(i)), {"title": raw})
            for got in (saved, served):
                assert got["title"] == want, raw
                assert got["title_color"] == control["title_color"], raw
                assert got["title_size"] == control["title_size"], raw
        assert control_served["title_color"] == control["title_color"]

    def test_macro_smcl_markup_and_python_in_a_string_arrive_as_written(
            self, tmp_path):
        """Injection: Stata macro syntax, SMCL, markup, JSON and Python
        escapes and Python code, inside a compound string with double
        quotes of its own, are the title's and the note's text exactly --
        nothing expanded, decoded or run -- in both modes and on the saved
        page.  Before the fix the text was cut at every inner quote."""
        sentinel = tmp_path / "executed"
        payload = ("`x' $HOME ${HOME} `=2+2' {bf:\"z\"} {stata dash clear} "
                   "<script>alert(\"x\")</script> <b>'q'</b> & &amp; "
                   "__import__('os').system(\"touch " + str(sentinel)
                   + "\") \\n \\u0022 %s {0}")
        # One compound string: the payload holds no "' and no `" of its own.
        assert '"' + _AP not in payload and _BT + '"' not in payload
        saved, served, page = _both_modes(tmp_path, {"title": _cq(payload),
                                                     "note": _cq(payload)})
        for got in (saved, served):
            assert got["title"] == payload
            assert got["labels"] == [payload]
        # Flipped (WP-30 P1.2a): [payload] was wrong because the note is
        # now a side-panel Title too, so the page holds the title and the
        # note, each the payload as typed.
        assert _page_titles(page) == [payload, payload]
        assert not sentinel.exists()

    def test_long_runs_of_quotes_and_apostrophes_are_read_in_bounded_time(
            self, tmp_path):
        """Exhaustion: long runs of "' pairs, of apostrophes, of nested and
        of unclosed compound quotes, each read whole and at once; and the
        sub-options after a comma.  Measured 24sep2026 before the fix, the
        sub-option reader took 32.5 s on '"x", size(' and 50,000 "a(", and
        71.6 s on 40,000 "a( " -- quadratic in the text -- and the saved
        renderer reads a title twice (counted: the figure's, and
        _dash_figure_title's)."""
        dq = '"'
        pairs = (dq + _AP) * 100000
        nested = (_BT + dq) * 50000 + "x" + (dq + _AP) * 50000
        unclosed = (_BT + dq + _AP) * 70000
        cases = [
            ('"x", size(' + "a(" * 50000, "x", {}),
            ('"x", size(' + "a( " * 40000, "x", {}),
            ('"x", size(' + " " * 100000 + "large)", "x",
             {"size": "large"}),
            (pairs, _AP + "\n" + pairs[3:], {}),
            (nested, nested[2:-2], {}),
            (_AP * 200000, _AP * 200000, {}),
            (unclosed, unclosed[2:], {}),
        ]
        for raw, text, opts in cases:
            t0 = time.monotonic()
            got = dr._parse_textbox_opt(raw)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                dr._dash_textbox(raw, "title")
            dr._textbox_split_point(raw)
            elapsed = time.monotonic() - t0
            assert elapsed < 5, (len(raw), elapsed)
            assert got == (text, opts), len(raw)
        # And a whole render in both modes, on the slowest of them.
        t0 = time.monotonic()
        saved, served, _ = _both_modes(
            tmp_path, {"title": '"x", size(' + "a( " * 40000})
        assert time.monotonic() - t0 < 60
        assert saved["title"] == served["title"] == "x"


# ============================================================
# legend(label(# text)) is read as Stata reads a text (24sep2026)
# ============================================================
#
# BUGS.md "The renderer does not draw a legend label given in compound
# quotes".  _dash_apply_legend took a label only as ``# "text"`` -- one
# plain-quoted string (its pattern, ``\s*(\d+)\s+"([^"]*)"\s*``) -- and
# kept the default key for anything else, in both modes: label(1
# `"'90s lc"') drew the variable's label, where twoway's exported SVG draws
# '90s lc.  Each expected value below is a 24sep2026 run of ``twoway
# (scatter mpg weight) (line mpg weight), legend(label(1 <text>))`` in
# StataNow 19.5 (console binary), exported to .svg and its key text read;
# the nested form was measured on title(), which twoway reads with the same
# textbox code.  A legend key is a DOM text node with ``white-space: pre``
# (bokeh's legend CSS, .bk-label), so a newline is a line break there and
# the text is never parsed as HTML.

def _legend_both_modes(tmp_path, legend):
    """``(saved, served, page)``: ``(keys, visible)`` of the one legend each
    mode draws for a scatter and a line under ``legend(<legend>)``, and the
    saved page."""
    from bokeh.document import Document
    from bokeh.models import Legend
    line = dict(_PLOT, type="line")
    spec = make_spec([dict(_PLOT), line])
    spec["graphs"][0]["graph_options"]["legend"] = legend
    sp, dp, ap = (str(tmp_path / n) for n in ("spec.json", "data.json",
                                              "app.py"))
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    with open(dp, "w", encoding="utf-8") as fh:
        json.dump(make_data_json(_DF), fh)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        renderer = dr.DashRenderer(sp, dp)
        page = renderer.render()
        dr.ServerAppBuilder(sp, dp).build(ap)
    with open(ap, encoding="utf-8") as fh:
        src = fh.read()
    assert _CURDOC_ATTACH in src, "the generated app's curdoc attach moved"
    ns = {"__name__": "dash_legend_app"}
    doc = Document()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        exec_app(src.replace(_CURDOC_ATTACH, "pass"), "dash_legend_app.py", ns)
        ns["make_document"](doc)

    def keys(legends):
        return [([_legend_text(i.label) for i in lg.items], lg.visible)
                for lg in legends]

    saved = keys([m for f in renderer.figures.values()
                  for m in f.select({"type": Legend})])
    served = keys(list(doc.select({"type": Legend})))
    assert len(saved) == 1 and len(served) == 1, (saved, served)
    return saved[0], served[0], page


def _legend_text(label):
    if isinstance(label, dict):
        return label.get("value")
    return getattr(label, "value", label)


def _page_legend_labels(page):
    """The LegendItem labels of the saved page's one embedded document,
    read back as the browser reads it."""
    from bokeh.document import Document
    from bokeh.models import LegendItem
    blocks = re.findall(r'<script type="application/json" id="[^"]+">'
                        r'\s*(.*?)\s*</script>', page, re.S)
    docs = [d for b in blocks
            for d in json.loads(_htmllib.unescape(b)).values()]
    assert len(docs) == 1, f"{len(docs)} embedded documents, not 1"
    return [_legend_text(i.label)
            for i in Document.from_json(docs[0]).select({"type": LegendItem})]


class TestALegendLabelIsReadAsStataReadsIt:
    """label(# text) is read with _textbox_lines, the reader every other
    text option uses, in both modes and on the saved page."""

    @pytest.mark.parametrize("text,want", [
        (_cq("'90s lc"), "'90s lc"),
        (_cq('a "b" c'), 'a "b" c'),
        ('"top" "bottom"', "top\nbottom"),
        ("Foreign cars here", " Foreign cars here"),
        ('a "b" c', "a\nb\nc"),
        ('"a" "" "b"', "a"),
        (_cq("a " + _cq("b") + " c"), "a " + _cq("b") + " c"),
        ('"plain"', "plain"),
    ], ids=["compound-apostrophe", "compound-holding-quotes",
            "two-strings-two-lines", "bare-words",
            "bare-words-around-a-string", "an-empty-string-ends-the-lines",
            "nested-compound", "plain"])
    def test_the_key_is_twoways_in_both_modes(self, tmp_path, text, want):
        saved, served, page = _legend_both_modes(
            tmp_path, "label(1 %s)" % text)
        assert saved[0][0] == want, saved
        assert served[0][0] == want, served
        assert want in _page_legend_labels(page)
        # The second key keeps its default text.
        assert saved[0][1] == served[0][1] != want

    def test_a_key_number_out_of_range_changes_nothing(self, tmp_path):
        (tmp_path / "c").mkdir()
        (tmp_path / "x").mkdir()
        control, _, _ = _legend_both_modes(tmp_path / "c", "")
        saved, served, _ = _legend_both_modes(tmp_path / "x",
                                              "label(9 %s)" % _cq("z"))
        assert saved[0] == served[0] == control[0]


class TestALegendLabelAdversarial:
    """CLAUDE.md rule 18 for the label now read: markup is text, a label's
    words are never sub-options, and a long label is read in bounded time."""

    _XSS = [
        "<script>alert(1)</script>",
        "<img src=x onerror=alert(1)>",
        '</script><script>alert("x")</script>',
        "<svg onload=alert(1)>",
        "\" onmouseover=\"alert(1)",
    ]

    @pytest.mark.parametrize("payload", _XSS, ids=[
        "script", "img-onerror", "close-script", "svg-onload",
        "attribute-break"])
    def test_markup_is_the_keys_text_and_never_raw_on_the_page(
            self, tmp_path, payload):
        saved, served, page = _legend_both_modes(
            tmp_path, "label(1 %s)" % _cq(payload))
        # A DOM text node: the raw text is what displays it inertly.
        assert saved[0][0] == served[0][0] == payload
        assert payload in _page_legend_labels(page)
        # Bokeh escapes the document it embeds: the markup never appears
        # raw in the saved file, so it cannot close the script block.
        assert payload not in page
        # The text of a tag may appear escaped (&lt;img ...); the tag never.
        assert "<script>alert" not in page
        assert "<img src=x" not in page
        assert "<svg onload" not in page

    def test_python_and_stata_in_a_label_run_nowhere(self, tmp_path):
        sentinel = tmp_path / "executed"
        payload = ("__import__('os').system(\"touch %s\") `x' $HOME "
                   "{stata dash clear} %%s {0}" % sentinel)
        saved, served, _ = _legend_both_modes(
            tmp_path, "label(1 %s)" % _cq(payload))
        assert saved[0][0] == served[0][0] == payload
        assert not sentinel.exists()

    def test_a_labels_words_are_never_sub_options(self, tmp_path):
        """Bypass: a label that looks like its own end and more
        sub-options after it."""
        text = 'x") off pos(9) label(2 "pwn'
        saved, served, _ = _legend_both_modes(
            tmp_path, "label(1 %s)" % _cq(text))
        for keys, visible in (saved, served):
            assert keys[0] == text
            assert keys[1] != "pwn"
            assert visible is True

    def test_a_long_label_is_read_in_bounded_time(self, tmp_path):
        dq = '"'
        nested = (_BT + dq) * 20000 + "x" + (dq + _AP) * 20000
        quotes = ('a "b" ' + _AP) * 20000
        t0 = time.monotonic()
        saved, served, _ = _legend_both_modes(
            tmp_path, "label(1 %s) label(2 %s)" % (nested, _cq(quotes)))
        assert time.monotonic() - t0 < 60
        assert saved[0][0] == served[0][0] == nested[2:-2]
        assert saved[0][1] == served[0][1] == quotes
