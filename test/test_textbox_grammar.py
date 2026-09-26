"""test_textbox_grammar.py -- WP-28 section 13: B3, B6, B7.

Every text option twoway takes -- ``title()``, ``subtitle()``, ``note()``,
``caption()``, ``xtitle()``, ``ytitle()`` and dash's own ``ytitle2()``/
``xtitle2()`` -- is a *textbox*: ``"string" ["string" ...] [, suboptions]``,
where each string is a line and the sub-options may be abbreviated to
Stata's documented minimums (``c:olor``, ``si:ze``, ``j:ustification`` ...).

Three symptoms, measured 24sep2026 against real Stata (GAPS2 B3, B6, B7):

* **B3** -- dash read a sub-option only under its full spelling, so
  ``title("T", c(red))`` drew the three lines ``T``, ``,`` and ``c(red)`` in
  the scheme's colour, with no warning, and ``ytitle("Volume", axis(2))``
  titled the LEFT axis with the whole tail as text -- ``axis(2)`` routes a
  title to the second axis and nothing read it.
* **B6** -- ``xtitle("")``/``ytitle("")`` (Stata's own way to remove an axis
  title, axis_title_options.sthlp:218-228) still drew the variable's label:
  an option given with empty text was read the same as an absent option.
* **B7** -- ``ytitle2()``/``xtitle2()`` (the second axis's title) were never
  read as textboxes at all: ``ytitle2("P2")`` drew ``"P2"`` with its quote
  marks, ``ytitle2("a" "b")`` one quoted line, and ``ytitle2("P2",
  size(large))`` the sub-option text verbatim.

B7 is fixed first: B3's ``axis(2)`` route hands the second axis a raw
textbox and B6's ``ytitle2("")`` needs the same reader, so both depend on
the second axis being read as a textbox at all.
"""
import itertools
import json
import os
import sys
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import make_data_json, make_spec  # noqa: E402
from test_textbox_multiline import (  # noqa: E402
    _both_modes, _drawn, _cq, _PLOT, _DF)
from test_dual_axis import _lone_figure, _axes  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "text_truth.json")


@pytest.fixture(scope="module")
def truth():
    # Committed (test_fixtures_are_committed.py): missing is a defect, and
    # a skip here would pass every check below that reads it (CLAUDE.md
    # rule 4 -- a red tree is never hidden behind a skip).
    if not os.path.exists(_FIXTURE):
        pytest.fail(
            "section 13 task 13-06 must land first: "
            "test/fixtures/text_truth.json is missing")
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _second_axis(fig, side_name):
    """The ``ContinuousAxis`` of *fig* on *side_name* (``"right"`` or
    ``"above"``) whose range name is the second one (``y2``/``x2``)."""
    from bokeh.models import ContinuousAxis
    side = getattr(fig, side_name)
    want = "y2" if side_name == "right" else "x2"
    rattr = "y_range_name" if want == "y2" else "x_range_name"
    axes = [a for a in side if isinstance(a, ContinuousAxis)
            and getattr(a, rattr, "default") == want]
    assert len(axes) == 1, (side_name, want, [type(a).__name__ for a in side])
    return axes[0]


#: A two-layer graph: y1 on the first y axis, y2 on the second -- not the
#: "lone" case (every layer on axis 2), so the first axis keeps its own
#: default title and the second is drawn beside it, as twoway draws it.
_DUAL_Y = [
    {"type": "scatter", "yvar": "y1", "xvar": "x", "options": {}},
    {"type": "line", "yvar": "y2", "xvar": "x", "options": {"yaxis": "2"}},
]
_DUAL_X = [
    {"type": "scatter", "yvar": "y1", "xvar": "x", "options": {}},
    {"type": "scatter", "yvar": "y3", "xvar": "y2",
     "options": {"xaxis": "2"}},
]


def _y2_axis(mode, ytitle2):
    fig = _lone_figure(mode, _DUAL_Y, {"name": "fig1", "ytitle2": ytitle2})
    return _second_axis(fig, "right")


# ============================================================
# B7 (13-01 tests, 13-02 fix, 13-03 close): the second axis's title is a
# textbox, not raw text with its quotes on.
# ============================================================

@pytest.mark.parametrize("mode", ["saved", "served"])
class TestSecondAxisTitleIsATextbox:
    """_dash_add_secondary_axes (WP-28 B7) reads ``{n}title2`` through
    _dash_textbox: lines joined, quotes gone, size()/color() applied, the
    rest named once -- the same reader the first axis's title uses."""

    def test_text_lines_size_colour(self, mode):
        assert _y2_axis(mode, '"P2"').axis_label == "P2"
        assert _y2_axis(mode, '"a" "b"').axis_label == "a\nb"
        assert _y2_axis(mode, _cq('c "q" d')).axis_label == 'c "q" d'

        plain = _y2_axis(mode, '"P2"')
        sized = _y2_axis(mode, '"P2", size(large)')
        assert sized.axis_label == "P2"
        assert sized.axis_label_text_font_size != \
            plain.axis_label_text_font_size

        coloured = _y2_axis(mode, '"P2", color(red)')
        assert coloured.axis_label == "P2"
        assert str(coloured.axis_label_text_color).lower() in (
            "red", "#ff0000")

        # "position" is already in the OLD (pre-B3) split table, so the
        # split-and-name behaviour below is B7's alone; a name the split
        # only recognises after B3 widens it (any word, not just a known
        # keyword) is covered there instead.
        # (_lone_figure's served mode execs the generated app's own
        # curdoc() auto-attach as well as calling make_document itself,
        # so the served count below can be 1 or 2 -- what matters is that
        # every warning names exactly "position(6)", never the size()/
        # color() honoured above and never a different word.)
        with warnings.catch_warnings(record=True) as rec:
            warnings.simplefilter("always")
            ax = _y2_axis(mode, '"P2", position(6)')
        assert ax.axis_label == "P2"
        hits = {str(w.message) for w in rec
               if "ytitle2() sub-option" in str(w.message)}
        assert len(hits) == 1, hits
        assert "position(6)" in next(iter(hits))

    def test_xtitle2_is_read_the_same_way(self, mode):
        fig = _lone_figure(mode, _DUAL_X,
                           {"name": "fig1", "xtitle2": '"a" "b"'})
        assert _second_axis(fig, "above").axis_label == "a\nb"

    def test_styling_holds_in_either_renderer_order(self, mode):
        """The saved renderer adds the second axis AFTER
        _dash_style_axis_titles; the served template adds it BEFORE.
        Styling inside _dash_add_secondary_axes itself makes the order not
        matter: the font size must be the same string in both."""
        saved = _y2_axis("saved", '"P2", size(large)')
        served = _y2_axis("served", '"P2", size(large)')
        assert saved.axis_label_text_font_size == \
            served.axis_label_text_font_size
