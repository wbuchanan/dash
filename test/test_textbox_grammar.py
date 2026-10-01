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


def _in(base, name):
    p = base / name
    p.mkdir()
    return p


# ============================================================
# B3 (13-04 tests, 13-05 truth block, 13-06 fixture, 13-07..13-11 fix and
# flips, 13-12 close): sub-option abbreviations are read as sub-options,
# and axis(2) routes a title to the second axis.
# ============================================================

class TestTheTable:
    """_TEXTBOX_SUBOPTS / _textbox_canon: Stata's own abbreviation table
    (textbox_options.sthlp:41-77, title_options.sthlp:56-66,
    axis_title_options.sthlp:54-63).  ``colour`` and ``style`` are twoway's
    own refusals and are deliberately left out."""

    _TABLE = (
        ("tstyle", "tsty"), ("bcolor", "bc"),
        ("orientation", "orient"), ("fcolor", "fc"),
        ("size", "si"), ("lstyle", "ls"),
        ("color", "c"), ("lpattern", "lp"),
        ("justification", "j"), ("lwidth", "lw"),
        ("alignment", "al"), ("lcolor", "lc"),
        ("margin", "m"), ("lalign", "la"),
        ("linegap", "linegap"), ("width", "width"), ("height", "height"),
        ("bmargin", "bm"),
        ("box", "box"), ("nobox", "nobox"),
        ("bexpand", "bex"),
        ("placement", "place"), ("position", "pos"),
        ("ring", "ring"), ("span", "span"),
        ("prefix", "prefix"), ("suffix", "suffix"), ("axis", "axis"),
    )

    def test_every_prefix(self):
        for full, minimum in self._TABLE:
            for n in range(len(minimum), len(full) + 1):
                assert dr._textbox_canon(full[:n]) == full, (full, n)
        for bogus in ("s", "colour", "style", "z", "b"):
            assert dr._textbox_canon(bogus) is None, bogus

    def test_parse_canonicalises(self):
        text, opts = dr._parse_textbox_opt('"a", c(red) si(large) bex')
        assert text == "a"
        assert opts == {"color": "red", "size": "large",
                        "bexpand": "bexpand"}


class TestAbbreviationsAreSubOptions:
    """Every legal spelling of size()/color() changes the drawing, alone
    or beside each other's full name, and the text stays bare."""

    def test_c_red_is_a_red_title(self, tmp_path):
        saved, served, page = _both_modes(tmp_path, {"title": '"T", c(red)'})
        for got in (saved, served):
            assert got["title"] == "T"
            assert str(got["title_color"]).lower() in ("red", "#ff0000")

    def test_every_size_spelling(self, tmp_path):
        plain, _, _ = _both_modes(_in(tmp_path, "plain"), {"title": '"T"'})
        for i, spelling in enumerate(("si", "siz", "size")):
            saved, served, _ = _both_modes(
                _in(tmp_path, f"sz{i}"),
                {"title": f'"T", {spelling}(large)'})
            for got in (saved, served):
                assert got["title"] == "T"
                assert got["title_size"] != plain["title_size"]

    def test_a_full_name_and_an_abbreviation_together(self, tmp_path):
        saved1, served1, _ = _both_modes(
            _in(tmp_path, "a"), {"title": '"T", size(large) c(red)'})
        saved2, served2, _ = _both_modes(
            _in(tmp_path, "b"), {"title": '"T", color(red) si(large)'})
        for got in (saved1, served1, saved2, served2):
            assert got["title"] == "T"
            assert str(got["title_color"]).lower() in ("red", "#ff0000")
        assert saved1["title_size"] == saved2["title_size"]


#: Representative abbreviated sub-options (excludes size/color, honoured;
#: TestAbbreviationsAreSubOptions covers those with a full render).
_UNHONOURED_ABBREVS = (
    ("justification", "j"), ("alignment", "al"), ("margin", "m"),
    ("orientation", "orient"), ("position", "pos"), ("bcolor", "bc"),
    ("fcolor", "fc"), ("lstyle", "ls"), ("lpattern", "lp"),
    ("lwidth", "lw"), ("lcolor", "lc"), ("lalign", "la"),
    ("bmargin", "bm"), ("bexpand", "bex"), ("placement", "place"),
    ("tstyle", "tsty"),
)
_TEXT_OPTIONS = ("title", "subtitle", "note", "caption", "xtitle", "ytitle")


@pytest.mark.parametrize("full,minimum", _UNHONOURED_ABBREVS,
                         ids=[f for f, _ in _UNHONOURED_ABBREVS])
class TestEverySpellingOnEveryOption:
    """size/color applied, the rest named exactly once, in every text
    option, under any legal spelling from the minimum to the full name."""

    def test_spelling(self, full, minimum):
        mid = full[:max(len(minimum) + 1, len(minimum))] \
            if len(full) > len(minimum) else full
        spellings = {minimum, mid, full}
        for opt, spelling in itertools.product(_TEXT_OPTIONS, spellings):
            raw = f'"T", {spelling}(x)'
            with warnings.catch_warnings(record=True) as rec:
                warnings.simplefilter("always")
                text, _opts = dr._dash_textbox(raw, opt)
            assert text == "T", (opt, spelling)
            hits = {str(w.message) for w in rec
                   if f"{opt}() sub-option" in str(w.message)}
            assert len(hits) == 1, (opt, spelling, hits)
            assert f"{spelling}(x)" in next(iter(hits))

    def test_second_axis_spelling(self, full, minimum):
        # size/color spellings style the second axis too (B7's read).
        for opt in ("ytitle2", "xtitle2"):
            for spelling in ("si", "size"):
                text, opts_ = dr._dash_textbox(
                    f'"T", {spelling}(large)', opt)
                assert text == "T"
                assert opts_.get("size") == "large"
            for spelling in ("c", "color"):
                text, opts_ = dr._dash_textbox(
                    f'"T", {spelling}(red)', opt)
                assert text == "T"
                assert opts_.get("color") == "red"


class TestForeignWordsAreNamed:
    """A word after the sub-option comma that is not in Stata's table
    (colour, style, a misspelling) is named, not drawn."""

    def test_colour_and_style(self, truth):
        assert dr._textbox_canon("colour") is None
        assert dr._textbox_canon("style") is None
        with warnings.catch_warnings(record=True) as rec:
            warnings.simplefilter("always")
            text, _opts = dr._dash_textbox('"T", colour(red)', "title")
        assert text == "T"
        hits = {str(w.message) for w in rec
               if "title() sub-option" in str(w.message)}
        assert len(hits) == 1 and "colour(red)" in next(iter(hits))

        with warnings.catch_warnings(record=True) as rec2:
            warnings.simplefilter("always")
            text2, _opts2 = dr._dash_textbox('"T", style(x)', "title")
        assert text2 == "T"
        hits2 = {str(w.message) for w in rec2
                if "title() sub-option" in str(w.message)}
        assert len(hits2) == 1 and "style(x)" in next(iter(hits2))

        # Measured 25sep2026: twoway refuses title("T", colour(red)),
        # r(198), but ACCEPTS title("T", style(x)) at rc 0 -- style() is
        # not a real sub-option of any of title()'s families either, so
        # twoway's own generic comma-split parses it and draws "T" anyway,
        # silently.  dash's table leaves "style" out for the same reason
        # (TR-13.1); this fixture value is what makes that an observation
        # rather than a guess.
        assert truth["probes"]["t_colour_refused"]["rc"] == 198
        assert truth["probes"]["t_style_refused"]["rc"] == 0
        assert truth["probes"]["t_style_refused"]["added_texts"] == ["T"]


class TestAxisTwoRouting:
    """ytitle(, axis(2))/xtitle(, axis(2)) title the second axis; axis(1)
    the first; axis(3) and above are named (B3's Mata and Python route,
    TR-13.5/TR-13.6)."""

    def test_axis_2_titles_the_right_axis(self):
        for mode in ("saved", "served"):
            fig = _lone_figure(mode, _DUAL_Y,
                               {"name": "fig1",
                                "ytitle": '"Volume", axis(2)'})
            assert fig.yaxis[0].axis_label != "Volume"
            assert _second_axis(fig, "right").axis_label == "Volume"

    def test_lines_and_size_survive_the_route(self):
        for mode in ("saved", "served"):
            fig = _lone_figure(mode, _DUAL_Y,
                               {"name": "fig1",
                                "ytitle": '"a" "b", axis(2)'})
            assert _second_axis(fig, "right").axis_label == "a\nb"
            fig2 = _lone_figure(
                mode, _DUAL_Y,
                {"name": "fig1", "ytitle": '"P2", size(large) axis(2)'})
            ax2 = _second_axis(fig2, "right")
            assert ax2.axis_label == "P2"
            assert ax2.axis_label_text_font_size is not None

    def test_the_route_runs_before_the_lone_rewrite(self):
        for mode in ("saved", "served"):
            plots = [{"type": "scatter", "yvar": "y1", "xvar": "x",
                     "options": {"yaxis": "2"}}]
            fig = _lone_figure(mode, plots,
                               {"name": "fig1",
                                "ytitle": '"Lone", axis(2)'})
            assert len(_axes(fig.left)) == 1
            assert _axes(fig.right) == []
            assert [a.axis_label for a in _axes(fig.left)] == ["Lone"]

    def test_route_axis_titles_unit(self):
        route = dr._dash_route_axis_titles

        s1 = {"graphs": [{"plots": [{"type": "scatter", "options": {}}],
                          "graph_options": {"ytitle": '"T", axis(1)'}}]}
        before = json.dumps(s1, sort_keys=True)
        out1 = route(s1)
        assert json.dumps(s1, sort_keys=True) == before
        go1 = out1["graphs"][0]["graph_options"]
        assert go1["ytitle"] == '"T"'
        assert "ytitle2" not in go1

        s2 = {"graphs": [{"plots": [{"type": "scatter", "options": {}}],
                          "graph_options": {"ytitle": '"T", axis(3)'}}]}
        out2 = route(s2)
        assert out2["graphs"][0]["graph_options"]["ytitle"] == '"T", axis(3)'

        s3 = {"graphs": [{"plots": [{"type": "scatter", "options": {}}],
                          "graph_options": {"ytitle": '"T", axis(2)',
                                            "ytitle2": '"Explicit"'}}]}
        with warnings.catch_warnings(record=True) as rec:
            warnings.simplefilter("always")
            out3 = route(s3)
        go3 = out3["graphs"][0]["graph_options"]
        assert go3["ytitle2"] == '"Explicit"'
        assert "ytitle" not in go3
        assert any("ytitle2()" in str(w.message) for w in rec)

        for bad in (None, [], "x", {"graphs": "x"}):
            assert route(bad) == bad


class TestPrefixSuffix:
    """A lone suffix/prefix on an axis title adds its line after or
    before twoway's own default; on title()/subtitle()/note()/caption()
    it changes nothing and says nothing (no default text to add to)."""

    def test_lone_suffix_and_prefix(self, truth):
        with warnings.catch_warnings(record=True) as rec:
            warnings.simplefilter("always")
            text, opts_ = dr._dash_textbox('"extra", suffix', "ytitle")
        assert text == "extra" and opts_.get("suffix") == "suffix"
        assert not [w for w in rec if "sub-option" in str(w.message)]

        text2, opts2 = dr._dash_textbox('"pre", prefix', "ytitle")
        assert text2 == "pre" and opts2.get("prefix") == "prefix"

        for mode in ("saved", "served"):
            fig = _lone_figure(
                mode, [{"type": "scatter", "yvar": "y1", "xvar": "x",
                       "options": {}}],
                {"name": "fig1", "ytitle": '"extra", suffix'})
            assert fig.yaxis[0].axis_label == "y1\nextra"
        for mode in ("saved", "served"):
            fig = _lone_figure(
                mode, [{"type": "scatter", "yvar": "y1", "xvar": "x",
                       "options": {}}],
                {"name": "fig1", "ytitle": '"pre", prefix'})
            assert fig.yaxis[0].axis_label == "pre\ny1"

        title_text, title_opts = dr._dash_textbox('"T", suffix', "title")
        assert title_text == "T" and title_opts.get("suffix") == "suffix"
        assert truth["probes"]["t_ytitle_suffix"]["added_texts"] == ["extra"]
        assert truth["probes"]["t_ytitle_prefix"]["added_texts"] == ["pre"]


#: probe id -> (option key, raw sub-option value as _dash_textbox reads
#: it) for every title-family probe whose ADDED text (twoway's SVG minus
#: its control's) is exactly the option's OWN text, independent of which
#: variable is on the axis: abbreviation and foreign-word probes.  The
#: empty-title probes are B6's (TestEmptyTitles); the suffix/prefix and
#: axis(2)/axis(3)/lone-axis probes combine with a variable-dependent
#: default and are pinned by TestAxisTwoRouting/TestPrefixSuffix instead,
#: which render a figure rather than comparing text alone.
_TEXT_OPT_PROBES = {
    "t_c_red": ("title", '"T", c(red)'),
    "t_color_red": ("title", '"T", color(red)'),
    "t_si_large": ("title", '"T", si(large)'),
    "t_size_large": ("title", '"T", size(large)'),
    "t_size_color_abbr": ("title", '"T", si(large) c(red)'),
    "t_size_c": ("title", '"T", size(large) c(red)'),
    "t_color_si": ("title", '"T", color(red) si(large)'),
    "t_j_left": ("title", '"A" "Bee", j(left)'),
    "t_bc_nobox": ("title", '"T", bc(red)'),
    "t_box_bc": ("title", '"T", box bc(red)'),
    "t_subtitle_c": ("subtitle", '"S", c(red)'),
    "t_note_si": ("note", '"N", si(large)'),
    "t_caption_c": ("caption", '"C", c(red)'),
    "t_xtitle_c": ("xtitle", '"W", c(red)'),
    "t_ytitle_si": ("ytitle", '"M", si(large)'),
    "t_xtitle_orient": ("xtitle", '"Weight", orient(vertical)'),
}


class TestTheFixtureIsPinned:
    """dash's textbox reader draws exactly what twoway's SVG drew for the
    fixture's title probes, minus the six empty-title ids (B6),
    t_axis3/t_axis2_no_layer (refusals: dash.ado refuses both, r(198), in
    twoway's words, pinned by test_twoway_option_parity.cscript AX-03,
    WP-29 P0.5) and the two refused-word ids (TestForeignWordsAreNamed)."""

    @pytest.mark.parametrize("pid", sorted(_TEXT_OPT_PROBES))
    def test_dash_draws_what_twoway_draws(self, truth, pid):
        key, raw = _TEXT_OPT_PROBES[pid]
        text, _opts = dr._dash_textbox(raw, key)
        got = text.split("\n") if text else []
        assert got == truth["probes"][pid]["added_texts"], (pid, got)

    def test_meta_carries_the_stata_build(self, truth):
        for k in ("stata_version", "born_date", "dash_commit", "extracted"):
            assert k in truth["_meta"], k


class TestTheServedCopy:
    """The served app carries the section's own names, or the served
    _textbox_canon raises NameError at build time."""

    def test_the_names_are_copied(self, tmp_path):
        spec = make_spec([dict(_PLOT)])
        sp, dp, ap = (str(tmp_path / n)
                     for n in ("spec.json", "data.json", "app.py"))
        with open(sp, "w", encoding="utf-8") as fh:
            json.dump(spec, fh)
        with open(dp, "w", encoding="utf-8") as fh:
            json.dump(make_data_json(_DF), fh)
        dr.ServerAppBuilder(sp, dp).build(ap)
        with open(ap, encoding="utf-8") as fh:
            src = fh.read()
        for name in ("_TEXTBOX_SUBOPTS", "_textbox_canon",
                     "_dash_route_axis_titles", "_DASH_TEXTBOX_HONOURED"):
            assert name in src, name


# ============================================================
# B6 (13-13 tests, 13-14 fix, 13-15 close): an option given with empty
# text removes the title; an absent option keeps twoway's default.
# ============================================================

_EMPTY_IDS = ("t_ytitle_axis2_empty", "t_xtitle_empty", "t_ytitle_empty",
              "t_both_empty", "t_xtitle_empty_size", "t_hist_ytitle_empty")
_HIST = [{"type": "histogram", "var": "y1", "options": {}}]
_KDENS = [{"type": "kdensity", "var": "y1", "options": {}}]
_ONE = [{"type": "scatter", "yvar": "y1", "xvar": "x", "options": {}}]


class TestEmptyTitles:
    """xtitle("")/ytitle("") remove the axis title (axis_title_options.sthlp
    218-228), in both modes and on the second axis.  Bokeh stores an
    empty axis_label as None; either means no title is drawn."""

    def test_empty_text_removes_the_title(self, truth):
        for mode in ("saved", "served"):
            fig = _lone_figure(mode, _ONE, {"name": "fig1", "xtitle": '""',
                                            "ytitle": '""'})
            assert fig.xaxis[0].axis_label in ("", None)
            assert fig.yaxis[0].axis_label in ("", None)
        assert set(truth["probes"]["t_both_empty"]["removed_texts"]) == {
            "Mileage (mpg)", "Weight (lbs.)"}

    def test_empty_text_with_a_sub_option(self):
        for mode in ("saved", "served"):
            fig = _lone_figure(mode, _ONE, {"name": "fig1",
                                            "xtitle": '"", size(large)'})
            assert fig.xaxis[0].axis_label in ("", None)

    def test_defaults_stay_when_absent(self):
        for mode in ("saved", "served"):
            assert _lone_figure(mode, _HIST, {"name": "fig1"}) \
                .yaxis[0].axis_label == "Density"
            assert _lone_figure(mode, _KDENS, {"name": "fig1"}) \
                .yaxis[0].axis_label == "kdensity y1"
            assert _lone_figure(mode, _HIST, {"name": "fig1",
                                              "ytitle": '""'}) \
                .yaxis[0].axis_label in ("", None)

    def test_second_axis_empty(self):
        lone = [{"type": "scatter", "yvar": "y1", "xvar": "x",
                 "options": {"yaxis": "2"}}]
        for mode in ("saved", "served"):
            assert _y2_axis(mode, '""').axis_label in ("", None)
            fig = _lone_figure(mode, lone, {"name": "fig1", "ytitle2": '""'})
            assert [a.axis_label or "" for a in _axes(fig.left)] == [""]

    @pytest.mark.parametrize("pid", _EMPTY_IDS)
    def test_the_fixture_probes_show_no_title(self, truth, pid):
        probe = truth["probes"][pid]
        assert probe["rc"] == 0
        assert probe["removed_texts"], pid
        # Nothing but tick labels (numbers) is ever added by an empty title.
        assert not [t for t in probe["added_texts"]
                    if not t.replace(",", "").replace(".", "").isdigit()], pid
