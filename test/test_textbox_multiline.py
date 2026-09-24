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
"""
import json
import os
import sys

import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
from conftest import make_data_json

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
    """Every Label the figure carries, as a list of their text."""
    from bokeh.models import Label
    out = []
    for fig in renderer.figures.values():
        for panel in ("above", "below", "left", "right", "center"):
            for item in getattr(fig, panel, []):
                if isinstance(item, Label):
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
        from bokeh.models import Label
        r = _render(tmp_path, {"note": '"N"', "caption": '"C"'})
        seen = {}
        for fig in r.figures.values():
            for item in fig.below:
                if isinstance(item, Label):
                    seen[item.text] = item.y
        assert seen.get("N") is not None and seen.get("C") is not None, seen
        assert seen["C"] >= 0, (
            "a negative screen y clips the caption out of its row: %r" % seen
        )

    def test_the_caption_is_added_after_the_note(self, tmp_path):
        """Stata puts the note at ring(4) and the caption at ring(5)."""
        from bokeh.models import Label
        r = _render(tmp_path, {"note": '"N"', "caption": '"C"'})
        for fig in r.figures.values():
            order = [i.text for i in fig.below if isinstance(i, Label)]
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
