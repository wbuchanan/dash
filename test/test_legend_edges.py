"""legend() and title() edges (WP-31 D16, section 39).

GAPS3 D16: ``legend(po(9) top)`` named ``top`` where twoway refuses
``po()`` first; ``title("T", prefix suffix)`` printed no line where twoway
prints "option prefix ignored, may not be combined with suffix"; the words
inside ``legend(region())`` and ``legend(title())`` were not checked.

Measured (test/fixtures/tabs_legend_edges_truth.json): twoway refuses the
first legend() word it cannot read, left to right; it refuses an unknown
word inside region() or title() as "option xx not allowed", r(198); it
draws title(, size()) and title(, color()) inside legend() and notes a
style name it does not know.  label(1) with no text blanks key 1 (drawn
since WP-31 D4; the regex and both modes are pinned here as guards).
"""
import json
import os
import sys
import warnings

import pytest
from bokeh.models import Legend, Title

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
import test_tabs_layout_edges as T

_FIXTURE = os.path.join(_HERE, "fixtures", "tabs_legend_edges_truth.json")
_TRUTH = json.load(open(_FIXTURE))
MODES = ("saved", "served")


def _two_layer(go):
    sp = T._spec(["g1"])
    g = sp["graphs"][0]
    g["graph_options"].update(go)
    g["plots"].append({"type": "scatter", "yvar": "weight", "xvar": "mpg",
                       "options": {}})
    return sp


def _legends(roots):
    return [lg for r in roots for lg in r.select({"type": Legend})]


def _key_texts(roots):
    out = []
    for lg in _legends(roots):
        for it in lg.items:
            lab = it.label
            out.append(lab.get("value") if isinstance(lab, dict)
                       else getattr(lab, "value", lab))
    return out


class TestLabelBlank:
    def test_regex(self):
        m = dr._DASH_LEGEND_LABEL_RE.fullmatch("1")
        assert m and m.group(1) == "1" and m.group(2) is None
        m = dr._DASH_LEGEND_LABEL_RE.fullmatch('1 "A"')
        assert m and m.group(2).strip() == '"A"'

    @pytest.mark.parametrize("mode", MODES)
    def test_blank(self, mode):
        """twoway draws key 1 with no text (fixture label.one)."""
        assert "Mileage (mpg)" not in (_TRUTH["label"]["one"]["svg_texts"]
                                       or [])
        roots, _ = T._root(mode, _two_layer({"legend": "label(1)"}))
        texts = _key_texts(roots)
        assert texts and texts[0] == "", texts

    @pytest.mark.parametrize("mode", MODES)
    def test_text(self, mode):
        assert "A" in _TRUTH["label"]["one_text"]["svg_texts"]
        roots, _ = T._root(mode, _two_layer({"legend": 'label(1 "A")'}))
        assert _key_texts(roots)[0] == "A"


class TestPrefixSuffix:
    @pytest.mark.parametrize("mode", MODES)
    def test_winner(self, mode):
        """twoway draws the title's text, T, with prefix and suffix both
        given (fixture title.prefix_suffix)."""
        rec = _TRUTH["title"]["prefix_suffix"]
        assert rec["rc"] == 0 and "T" in rec["svg_texts"]
        roots, _ = T._root(mode, _two_layer({"title": '"T", prefix suffix'}))
        titles = [t.text for r in roots for t in r.select({"type": Title})
                  if t.text]
        assert "T" in titles, titles


class TestTheChecks:
    def test_records(self):
        for grp, keys in (("legend", ("po9_top", "top_po9", "top")),
                          ("title", ("prefix_suffix", "suffix_prefix")),
                          ("nested", ("region_lcolor_bogus",
                                      "region_fcolor_red", "region_bad_word",
                                      "title_size_bogus", "title_size_large",
                                      "title_bad_word"))):
            for k in keys:
                assert "rc" in _TRUTH[grp][k] and "lines" in _TRUTH[grp][k]
        assert _TRUTH["legend"]["po9_top"]["first"] == "option po() not allowed"
        assert _TRUTH["title"]["prefix_suffix"]["lines"] == [
            "option prefix ignored, may not be combined with suffix"]

    def test_kinds_exist(self):
        """Mata checks the words inside legend(region()) and
        legend(title()), and the legend's words in twoway's order."""
        src = open(os.path.join(_HERE, "..", "dash_parse.mata"),
                   encoding="utf-8").read()
        assert "_dash_subreq_nested(" in src
        assert "_dash_legend_first_refusal(" in src


class TestLegendTitleStyle:
    """legend(title("T", color() size())): twoway draws them (fixture
    nested.title_size_large) and notes a name it does not know
    (nested.title_size_bogus, nested.title_color_bogus)."""

    @pytest.mark.parametrize("mode", MODES)
    def test_drawn(self, mode):
        roots, _ = T._root(mode, _two_layer(
            {"legend": 'title("T", color(red) size(large))'}))
        lg = _legends(roots)[0]
        assert lg.title == "T"
        assert str(lg.title_text_color).lower() in ("#ff0000", "red"), \
            lg.title_text_color
        assert lg.title_text_font_size != lg.label_text_font_size

    @pytest.mark.parametrize("probe,word,key", [
        ('title("T", color(bogus))', "colour", "title_color_bogus"),
        ('title("T", size(bogus))', "size", "title_size_bogus"),
    ])
    def test_named(self, probe, word, key):
        assert _TRUTH["nested"][key]["rc"] == 0
        assert "bogus" in _TRUTH["nested"][key]["lines"][0]
        _, msgs = T._root("saved", _two_layer({"legend": probe}))
        assert any("bogus" in m and word in m for m in msgs), msgs


class TestBareString:
    """A quoted string standing alone among the options (WP-31 D16b):
    twoway refuses it, r(198), in words that follow where it stands
    (fixture bare.*); dash's catch-all kept it and named it in the note.
    The refusal is Mata's _dash_bare_string_refusal, checked against every
    fixture row by test_option_validation.cscript U39-07."""

    def test_records(self):
        bare = _TRUTH["bare"]
        assert {r["lines"][0] for k, r in bare.items() if r["rc"]} >= {
            "quotes unbalanced", "invalid syntax",
            "parentheses do not balance"}
        assert bare["in_title"]["rc"] == 0 and bare["bars_ctrl"]["rc"] == 0

    def test_the_check_exists(self):
        src = open(os.path.join(_HERE, "..", "dash_parse.mata"),
                   encoding="utf-8").read()
        assert "string scalar _dash_bare_string_refusal(" in src
        ado = open(os.path.join(_HERE, "..", "dash.ado"),
                   encoding="utf-8").read()
        assert "_dash_bare_string_refusal(" in ado


class TestNestedNote:
    """A style name dash does not know, two levels down, is named as typed
    (WP-31 D16 follow-up): the note read legend(region(lcolor)(bogus))."""

    @pytest.mark.parametrize("opt,head", [
        ("region(lcolor(bogus))", "legend(region(lcolor(bogus)))"),
        ('title("T", color(bogus))', "legend(title(color(bogus)))"),
    ])
    def test_named_as_typed(self, opt, head):
        _, msgs = T._root("saved", _two_layer({"legend": opt}))
        assert any(m.startswith("dash: %s is not a recognised colour"
                                % head) for m in msgs), msgs

    def test_one_level_unchanged(self):
        dr._dash_reset_notes()
        import warnings as _w
        with _w.catch_warnings(record=True) as caught:
            _w.simplefilter("always")
            dr._dash_style_note("plotregion(lcolor)", "x", "colour", "black")
        assert [str(c.message) for c in caught] == [
            "dash: plotregion(lcolor(x)) is not a recognised colour; "
            "using black."]


class TestQuoteApostrophe:
    """A plain quote opened by an apostrophe, title("'90s"): twoway's own
    parse reads the "' as the close of a compound quote never opened and
    fails on what follows, in words that depend on it (quote.*: ")
    required", r(100), for title("'90s"), xlabel(), text() and by()'s
    title(); "type mismatch", r(109), for JSE-47's title; legend.jse47
    r(100)).  dash reads the "' as text inside the quote, as CLAUDE.md
    rule 18 requires, so it draws them; dash.sthlp says so."""

    def test_twoway_varies(self):
        q = _TRUTH["quote"]
        assert {q[k]["rc"] for k in ("title", "xlabel", "text",
                                     "bytitle")} == {100}
        assert q["title_jse47a"]["rc"] == 109
        assert q["note"]["rc"] == 0
        assert _TRUTH["legend"]["jse47"]["rc"] == 100

    def test_the_help_says_so(self):
        text = open(os.path.join(_HERE, "..", "dash.sthlp"),
                    encoding="utf-8").read()
        assert "close of a compound quote never opened" in text
