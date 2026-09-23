"""test_scheme_grids.py — the scheme decides which grids are drawn.

``SchemeParser`` parsed two grid-visibility flags and **nothing ever read
them**. Measured with a counting proxy over a full ``render()``: attribute
reads of ``draw_major_hgrid`` / ``draw_major_vgrid`` during a whole render:
zero. ``apply_to_figure`` set a grid colour on every grid unconditionally, and
Bokeh draws both grids by default, so dash drew a grid Stata does not draw in
**10 of the 14 shipped schemes** — both grids under s1color, s1mono, s1rcolor
and stmono1, which draw none at all.

The second flag was also sourced from the **wrong key**. dash read
``yesno draw_major_grid``; Stata's scheme-level key for the vertical axis is
``draw_major_vgrid``. ``grep -rn "scheme draw_major_grid"`` over
``/Applications/StataNow/ado/base/style/`` returns **zero** hits — the key dash
read is dead at scheme level. Every shipped scheme declares it ``no``, which is
why the flag looked plausible.

**Which key governs which axis.** A Stata grid belongs to an *axis*, and the
key is named for that axis's orientation, not for the direction of the lines:

    style/axisstyle-horizontal_default.style:18
        set draw_major_grid    scheme draw_major_hgrid
    style/axisstyle-vertical_default.style:18
        set draw_major_grid    scheme draw_major_vgrid

The horizontal axis is x, and its major grid lines are the **vertical** ones at
the x ticks; the vertical axis is y, and its grid lines are **horizontal**. So
``draw_major_hgrid`` -> ``fig.xgrid`` and ``draw_major_vgrid`` -> ``fig.ygrid``.
This is the opposite of the reading the old code comment gave, and it is the
thing most likely to be "fixed" backwards later, so it has its own test below.

The resolved values, read from Stata's own ``#include`` chains under
``/Applications/StataNow/ado/base/s``, agree with how these schemes are known
to look: s2color draws horizontal lines only, s1color draws none, stcolor
draws both.
"""
import json
import os
import sys
import tempfile

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render
from dash_render import SchemeParser, DashRenderer

from conftest import make_spec, make_data_json


# Resolved from Stata's own scheme files through their #include chains:
#   (draw_major_hgrid -> x axis, draw_major_vgrid -> y axis)
_GRID_TRUTH = {
    "economist":   (False, True),
    "s1color":     (False, False),
    "s1mono":      (False, False),
    "s1rcolor":    (False, False),
    "s2color":     (False, True),
    "s2gcolor":    (False, True),
    "s2mono":      (False, True),
    "sj":          (False, True),
    "stcolor":     (True,  True),
    "stcolor_alt": (True,  True),
    "stgcolor":    (True,  True),
    "stmono1":     (False, False),
    "stmono2":     (True,  True),
    "stsj":        (False, True),
    # WP-17: the six added schemes, from their parents' chains --
    # s2manual/s2gmanual #include s2mono (-> s2color), s1manual #include
    # s1mono, s2color8 #include s2color, stgcolor_alt #include stcolor_alt;
    # sttrans #includes s2color and then sets `yesno draw_major_hgrid yes'
    # itself, so it is the one s2-family scheme that draws both.
    "s2manual":    (False, True),
    "s1manual":    (False, False),
    "s2gmanual":   (False, True),
    "s2color8":    (False, True),
    "sttrans":     (True,  True),
    "stgcolor_alt": (True,  True),
}

_FIXTURE = os.path.join(_HERE, "fixtures", "scheme_truth.json")


class TestTheTruthTableIsTheFixture:
    """The table above is hand-written; the fixture is extracted from Stata's
    files.  They must agree, and the table must cover every shipped scheme,
    or a scheme added later silently escapes these tests."""

    def test_the_table_covers_every_scheme_in_the_fixture(self):
        with open(_FIXTURE, encoding="utf-8") as fh:
            truth = json.load(fh)
        names = sorted(k for k in truth if k != "_meta")
        assert sorted(_GRID_TRUTH) == names, (
            f"_GRID_TRUTH covers {sorted(_GRID_TRUTH)}, the fixture {names}"
        )
        assert len(names) == 20

    @pytest.mark.parametrize("name,truth", sorted(_GRID_TRUTH.items()))
    def test_the_table_agrees_with_the_fixtures_effective_flags(self, name, truth):
        with open(_FIXTURE, encoding="utf-8") as fh:
            entry = json.load(fh)[name]
        effective = (entry["draw_major_hgrid"] == "yes",
                     entry["draw_major_vgrid"] == "yes")
        assert effective == truth, (
            f"{name}: the fixture's effective flags are {effective}, the "
            f"table says {truth}"
        )


def _render(scheme):
    df = pd.DataFrame({"mpg": np.linspace(12.0, 41.0, 20),
                       "weight": np.linspace(1760.0, 4840.0, 20)})
    spec = make_spec([{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}])
    spec["build_options"]["scheme"] = scheme
    sp = tempfile.mkstemp(".json")[1]
    dp = tempfile.mkstemp(".json")[1]
    op = tempfile.mkstemp(".html")[1]
    with open(sp, "w") as f:
        json.dump(spec, f)
    with open(dp, "w") as f:
        json.dump(make_data_json(df), f)
    dr = DashRenderer(sp, dp, op)
    dr.render()
    for p in (sp, dp, op):
        try:
            os.unlink(p)
        except OSError:
            pass
    return list(dr.figures.values())[0], dr


class TestTheParserReadsTheRightKey:

    @pytest.mark.parametrize("name,truth", sorted(_GRID_TRUTH.items()))
    def test_the_flags_match_statas_resolved_values(self, name, truth):
        sp = SchemeParser(name)
        assert (sp.draw_major_hgrid, sp.draw_major_vgrid) == truth, (
            f"{name}: dash reads "
            f"({sp.draw_major_hgrid}, {sp.draw_major_vgrid}), Stata's "
            f"resolved include chain gives {truth}"
        )

    def test_the_dead_key_is_not_what_the_y_axis_reads(self):
        """Every scheme declares `draw_major_grid no`, so reading it gave
        False everywhere and looked plausible."""
        sp = SchemeParser("s2color")
        assert sp._props.get("yesno draw_major_grid", "").strip() == "no"
        assert sp.draw_major_vgrid is True, (
            "the y-axis flag is still coming from the dead draw_major_grid key"
        )


class TestTheRenderedFigureHonoursThem:

    @pytest.mark.parametrize("name,truth", sorted(_GRID_TRUTH.items()))
    def test_each_axis_grid_matches_the_scheme(self, name, truth):
        want_h, want_v = truth
        fig, dr = _render(name)
        got_h = fig.xgrid[0].grid_line_color is not None
        got_v = fig.ygrid[0].grid_line_color is not None
        assert (got_h, got_v) == (want_h, want_v), (
            f"{name}: drew (x={got_h}, y={got_v}); Stata draws "
            f"(x={want_h}, y={want_v})"
        )

    @pytest.mark.parametrize("name", sorted(_GRID_TRUTH))
    def test_a_drawn_grid_uses_the_schemes_colour(self, name):
        want_h, want_v = _GRID_TRUTH[name]
        fig, dr = _render(name)
        if want_h:
            assert fig.xgrid[0].grid_line_color == dr.scheme.grid_color
        if want_v:
            assert fig.ygrid[0].grid_line_color == dr.scheme.grid_color

    def test_a_scheme_that_draws_no_grid_draws_no_grid(self):
        """s1color, s1mono, s1rcolor and stmono1 drew BOTH."""
        for name in ("s1color", "s1mono", "s1rcolor", "stmono1"):
            fig, _ = _render(name)
            assert fig.xgrid[0].grid_line_color is None, name
            assert fig.ygrid[0].grid_line_color is None, name


class TestTheDirectionIsNotSwapped:
    """The regression this is most likely to reacquire."""

    def test_s2color_draws_horizontal_lines_and_no_vertical_ones(self):
        """s2color's familiar look: lines across the plot at the y ticks.

        Stata resolves it through style/axisstyle-vertical_default.style:18,
        ``set draw_major_grid scheme draw_major_vgrid`` — the VERTICAL axis
        (y), whose grid lines are horizontal.
        """
        fig, _ = _render("s2color")
        assert fig.ygrid[0].grid_line_color is not None, (
            "s2color must draw the horizontal lines at its y ticks"
        )
        assert fig.xgrid[0].grid_line_color is None, (
            "s2color must not draw vertical lines at its x ticks"
        )

    def test_a_scheme_with_hgrid_yes_draws_the_vertical_lines(self):
        """stcolor sets draw_major_hgrid yes; that is the x axis."""
        fig, _ = _render("stcolor")
        assert fig.xgrid[0].grid_line_color is not None


class TestExplicitOptionsStillWin:
    """A scheme decides the default; xlabel(,grid) decides the graph."""

    def test_nogrid_beats_a_scheme_that_draws_one(self):
        from conftest import make_spec as _ms
        df = pd.DataFrame({"mpg": np.linspace(12.0, 41.0, 20),
                           "weight": np.linspace(1760.0, 4840.0, 20)})
        spec = _ms([{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                     "options": {}}])
        spec["build_options"]["scheme"] = "stcolor"     # draws both
        spec["graphs"][0]["graph_options"]["xlabel"] = "2000 4000, nogrid"
        sp = tempfile.mkstemp(".json")[1]
        dp = tempfile.mkstemp(".json")[1]
        op = tempfile.mkstemp(".html")[1]
        with open(sp, "w") as f:
            json.dump(spec, f)
        with open(dp, "w") as f:
            json.dump(make_data_json(df), f)
        dr = DashRenderer(sp, dp, op)
        dr.render()
        fig = list(dr.figures.values())[0]
        for p in (sp, dp, op):
            try:
                os.unlink(p)
            except OSError:
                pass
        assert fig.xgrid[0].grid_line_color is None

    def test_grid_beats_a_scheme_that_draws_none(self):
        df = pd.DataFrame({"mpg": np.linspace(12.0, 41.0, 20),
                           "weight": np.linspace(1760.0, 4840.0, 20)})
        spec = make_spec([{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                           "options": {}}])
        spec["build_options"]["scheme"] = "s1color"     # draws neither
        spec["graphs"][0]["graph_options"]["xlabel"] = "2000 4000, grid"
        sp = tempfile.mkstemp(".json")[1]
        dp = tempfile.mkstemp(".json")[1]
        op = tempfile.mkstemp(".html")[1]
        with open(sp, "w") as f:
            json.dump(spec, f)
        with open(dp, "w") as f:
            json.dump(make_data_json(df), f)
        dr = DashRenderer(sp, dp, op)
        dr.render()
        fig = list(dr.figures.values())[0]
        for p in (sp, dp, op):
            try:
                os.unlink(p)
            except OSError:
                pass
        assert fig.xgrid[0].grid_line_color is not None, (
            "an explicit xlabel(, grid) must beat the scheme's default"
        )


class TestBokehStillDrawsBothByDefault:
    """If this ever changes, the "off" path stops being load-bearing."""

    def test_a_bare_figure_has_both_grids_on(self):
        from bokeh.plotting import figure
        f = figure()
        assert f.xgrid[0].grid_line_color is not None
        assert f.ygrid[0].grid_line_color is not None
