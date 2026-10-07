"""test_axis_options.py — S09: axes, legend, titles and reference lines.

The largest cluster of silent failures in the package.  Options that Stata's
``syntax`` accepts, because they are declared ``string asis``, arrive intact
at Python and then have their contents thrown away by parsers that recognise
two or three keywords.

Ground truth is ``test/fixtures/axis_truth.json``: 233 probes measured in
Stata, with tick positions read out of exported SVG (a live ``.gph`` records
the REQUEST, not the resulting positions, so it is not a tick oracle).

The single most consequential finding, and the one that changes existing
output: **twoway draws a legend if and only if the graph has two or more
keys.**  One key, no legend, no matter what else is passed;
``legend(position(6))`` on a one-key plot draws nothing at all.  Only
``legend(on)`` forces one.
"""
import json
import math
import os
import sys
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render
from dash_render import DashRenderer, GlyphMapper, OptionTranslator, SchemeParser

from conftest import make_dr, make_spec, make_data_json

_FIXTURE = os.path.join(_HERE, "fixtures", "axis_truth.json")


@pytest.fixture(scope="module")
def truth():
    # Committed (test_fixtures_are_committed.py): missing is a defect, and
    # a skip here passed every check below that reads it.
    assert os.path.exists(_FIXTURE), (
        "test/fixtures/axis_truth.json is missing")
    with open(_FIXTURE) as fh:
        return json.load(fh)


def _auto():
    """A deterministic auto-like frame spanning weight 1760-4840."""
    rng = np.random.default_rng(0)
    n = 74
    return pd.DataFrame({
        "mpg":    np.linspace(12, 41, n),
        "weight": np.linspace(1760, 4840, n),
        "price":  np.linspace(3291, 15906, n),
        "rep78":  np.array([1.0, 2.0, 3.0, 4.0, 5.0, np.nan] * 13)[:n],
        "foreign": np.array([0.0, 1.0] * 37)[:n],
    })


def _fig(plots, gopts=None, df=None, **kw):
    spec_plots = plots
    dr = make_dr(spec_plots, df=df if df is not None else _auto(), **kw)
    return dr._build_figures()["g1"], dr


def _fig_with_gopts(plots, gopts, df=None, build=None):
    """Build one figure with arbitrary graph_options (and build_options)."""
    import tempfile
    df = _auto() if df is None else df
    spec = make_spec(plots)
    spec["graphs"][0]["graph_options"].update(gopts)
    spec["build_options"].update(build or {})
    sp = tempfile.mkstemp(".json")[1]
    dp = tempfile.mkstemp(".json")[1]
    op = tempfile.mkstemp(".html")[1]
    with open(sp, "w") as f:
        json.dump(spec, f)
    with open(dp, "w") as f:
        json.dump(make_data_json(df), f)
    dr = DashRenderer(sp, dp, op)
    figs = dr._build_figures()
    for p in (sp, dp, op):
        try:
            os.unlink(p)
        except OSError:
            pass
    return figs["g1"], dr


_SCATTER = [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}]
_TWO = [
    {"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}},
    {"type": "lfit", "yvar": "mpg", "xvar": "weight", "options": {}},
]


# ======================================================================
# Axis label grammar
# ======================================================================

def _ticker_of(fig, axis="x"):
    ax = fig.xaxis if axis == "x" else fig.yaxis
    return ax[0].ticker if len(ax) else None


def _fixed_ticks(fig, axis="x"):
    from bokeh.models import FixedTicker
    t = _ticker_of(fig, axis)
    return list(t.ticks) if isinstance(t, FixedTicker) else None


class TestAxisLabelGrammar:
    """Every ``xlabel()`` form Stata accepts must produce Stata's ticks."""

    def test_explicit_numlist_still_works(self):
        fig, _ = _fig_with_gopts(_SCATTER, {"xlabel": "2000 3000 4000"})
        assert _fixed_ticks(fig) == [2000.0, 3000.0, 4000.0]

    def test_value_label_pairs_still_work(self):
        fig, _ = _fig_with_gopts(
            _SCATTER, {"xlabel": '2000 "low" 4000 "high"'})
        assert _fixed_ticks(fig) == [2000.0, 4000.0]
        ov = fig.xaxis[0].major_label_overrides
        assert set(ov.values()) == {"low", "high"}

    def test_increment_form_a_b_c(self):
        """1000(500)3000 is five ticks, not zero."""
        fig, _ = _fig_with_gopts(_SCATTER, {"xlabel": "1000(500)3000"})
        assert _fixed_ticks(fig) == [1000.0, 1500.0, 2000.0, 2500.0, 3000.0]

    def test_increment_form_with_spaces(self):
        fig, _ = _fig_with_gopts(_SCATTER, {"xlabel": "1990 (5) 2020"})
        assert _fixed_ticks(fig) == [1990.0, 1995.0, 2000.0, 2005.0, 2010.0,
                                     2015.0, 2020.0]

    def test_minmax_is_two_ticks_at_the_data_bounds(self, truth):
        """Measured: xlabel(minmax) on weight gives exactly 1760 and 4840."""
        fig, _ = _fig_with_gopts(_SCATTER, {"xlabel": "minmax"})
        assert _fixed_ticks(fig) == [1760.0, 4840.0]

    def test_none_produces_no_ticks_BY_INTENT(self):
        """It produced zero ticks by accident before — every token was dropped.

        The ticker type distinguishes the two: an empty FixedTicker is a
        decision, an empty parse result is a failure.
        """
        from bokeh.models import FixedTicker
        fig, _ = _fig_with_gopts(_SCATTER, {"xlabel": "none"})
        assert isinstance(_ticker_of(fig), FixedTicker)
        assert _fixed_ticks(fig) == []

    def test_none_also_removes_gridlines(self, truth):
        """Measured: xlabel(none) gives 0 ticks AND 0 gridlines."""
        fig, _ = _fig_with_gopts(_SCATTER, {"xlabel": "none"})
        assert fig.xgrid[0].grid_line_color is None

    def test_hash_n_is_a_suggestion_not_a_count(self, truth):
        """Stata's #10 on weight gives EIGHT ticks: #N is a suggestion.

        twoway draws 1500(500)5000 for it over 1760 to 4840 (graph record,
        test/fixtures/natscale_truth.json), and dash places them there by
        twoway's rule (test_natscale.py); Bokeh's desired_num_ticks, which
        this used to map to, chose its own positions.
        """
        fig, _ = _fig_with_gopts(_SCATTER, {"xlabel": "#10"})
        assert _fixed_ticks(fig) == [1500.0 + 500 * i for i in range(8)]

    def test_hash_one_behaves_like_minmax(self, truth):
        """#1 is tickset's minmax: the data's extremes."""
        fig, _ = _fig_with_gopts(_SCATTER, {"xlabel": "#1"})
        assert _fixed_ticks(fig) == [1760.0, 4840.0]

    def test_format_suboption_reaches_the_tick_labels(self):
        """ylabel(, format(%9.0fc)) rendered nothing at all."""
        # GAPS2 E3/G6, WP-28 S12: a Stata-writing CustomJSTickFormatter.
        from bokeh.models import CustomJSTickFormatter
        fig, _ = _fig_with_gopts(
            _SCATTER, {"ylabel": ", format(%9.0fc)"})
        fmt = fig.yaxis[0].formatter
        assert isinstance(fmt, CustomJSTickFormatter), type(fmt).__name__
        assert fmt.args["fmt"] == "%9.0fc"

    def test_format_with_explicit_ticks_together(self):
        # GAPS2 E3/G6, WP-28 S12: a Stata-writing CustomJSTickFormatter.
        from bokeh.models import CustomJSTickFormatter
        fig, _ = _fig_with_gopts(
            _SCATTER, {"xlabel": "2000 4000, format(%9.0fc)"})
        assert _fixed_ticks(fig) == [2000.0, 4000.0]
        assert isinstance(fig.xaxis[0].formatter, CustomJSTickFormatter)
        assert fig.xaxis[0].formatter.args["fmt"] == "%9.0fc"

    def test_labsize_changes_the_tick_label_size(self):
        fig_small, _ = _fig_with_gopts(_SCATTER, {"xlabel": ", labsize(small)"})
        fig_large, _ = _fig_with_gopts(_SCATTER, {"xlabel": ", labsize(large)"})
        s = fig_small.xaxis[0].major_label_text_font_size
        l = fig_large.xaxis[0].major_label_text_font_size
        assert s and l and s != l, (s, l)

    def test_angle_still_works(self):
        fig, _ = _fig_with_gopts(_SCATTER, {"xlabel": ", angle(45)"})
        assert fig.xaxis[0].major_label_orientation == pytest.approx(
            math.radians(45))

    def test_grid_and_nogrid(self):
        on, _ = _fig_with_gopts(_SCATTER, {"xlabel": "2000 4000, grid"})
        off, _ = _fig_with_gopts(_SCATTER, {"xlabel": "2000 4000, nogrid"})
        assert on.xgrid[0].grid_line_color is not None
        assert off.xgrid[0].grid_line_color is None

    def test_ylabel_takes_the_same_grammar(self):
        fig, _ = _fig_with_gopts(_SCATTER, {"ylabel": "10(10)40"})
        assert _fixed_ticks(fig, "y") == [10.0, 20.0, 30.0, 40.0]

    def test_xtick_is_honoured(self):
        """xtick() draws ticks WITHOUT labels beside the axis's own labels
        (WP-23).  This asserted a FixedTicker at the xtick() positions,
        which is what xtick() used to draw: LABELLED ticks, in place of the
        axis's labels.  The tick-only positions are now the minor ticks of a
        CustomJSTicker whose major, labelled ticks are the old ticker's."""
        fig, _ = _fig_with_gopts(_SCATTER, {"xtick": "2000 3000 4000"})
        from bokeh.models import BasicTicker, CustomJSTicker
        t = _ticker_of(fig)
        assert isinstance(t, CustomJSTicker)
        assert t.args["extra"] == [2000.0, 3000.0, 4000.0]
        assert isinstance(t.args["base"], BasicTicker)

    def test_a_date_axis_ignores_a_numeric_format_gracefully(self):
        """Regression guard for the S08 work: no exception, no silent mangle."""
        fig, _ = _fig_with_gopts(_SCATTER, {"xlabel": ", format(%td)"})
        assert fig is not None


# ======================================================================
# Axis scale
# ======================================================================

class TestAxisScale:

    def test_range_sets_the_axis_bounds(self):
        """range() widens the axis to include its values and never narrows
        it (axis_scale_options.sthlp:336-341): mpg 12-41 inside 0-50, the
        hull padded 5% a side (WP-28 B2; this pinned an exact 0 to 50)."""
        from bokeh.models import Range1d
        fig, _ = _fig_with_gopts(_SCATTER, {"yscale": "range(0 50)"})
        assert isinstance(fig.y_range, Range1d)
        assert dash_render._dash_range_hull(fig.y_range) == pytest.approx(
            (0.0, 50.0))

    def test_range_with_only_a_lower_bound(self):
        """range() never narrows (axis_scale_options.sthlp:336-341): 0 is
        included and the data's top kept, padded at both ends (WP-28 B2;
        this pinned a start of exactly 0)."""
        fig, _ = _fig_with_gopts(_SCATTER, {"yscale": "range(0)"})
        assert dash_render._dash_range_hull(fig.y_range) == pytest.approx(
            (0.0, 41.0))
        assert fig.y_range.start < 0.0 and fig.y_range.end > 41.0

    def test_range_combines_with_log(self):
        """range() never narrows (axis_scale_options.sthlp:336-341): on a
        log axis the hull is padded in log space (WP-28 B2; this pinned a
        start of exactly 1000)."""
        fig, _ = _fig_with_gopts(_SCATTER, {"xscale": "log range(1000 5000)"})
        from bokeh.models import LogAxis
        assert any(isinstance(a, LogAxis) for a in fig.xaxis)
        assert fig.x_range.start < 1000.0
        assert dash_render._dash_range_hull(fig.x_range, "log") == \
            pytest.approx((1000.0, 5000.0))

    def test_reverse_still_works(self):
        fig, _ = _fig_with_gopts(_SCATTER, {"yscale": "reverse"})
        assert getattr(fig.y_range, "flipped", False) is True

    def test_the_dead_xrange_keys_are_gone(self):
        """A dead option read is how the axis work got misled in the first place."""
        src = open(os.path.join(_HERE, "..", "dash_render.py")).read()
        code = "\n".join(l.split("#", 1)[0] for l in src.splitlines())
        for dead in ('graph_opts.get("xrange"', 'graph_opts.get("yrange"'):
            assert dead not in code, (
                f"{dead} is still read, but dash.ado never emits it"
            )

    def test_unsupported_scale_suboptions_are_reported(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            _fig_with_gopts(_SCATTER, {"yscale": "noextend"})
        assert any("noextend" in str(w.message) for w in caught)


# ======================================================================
# The legend rule
# ======================================================================

def _legend_items(fig):
    if not fig.legend:
        return []
    return [i for i in fig.legend[0].items]


def _legend_shown(fig):
    return bool(fig.legend) and fig.legend[0].visible and bool(
        _legend_items(fig))


class TestLegendRule:
    """twoway draws a legend iff there are two or more keys."""

    @pytest.mark.parametrize("ptype", [
        "scatter", "line", "bar", "area", "spike", "connected",
    ])
    def test_a_single_series_draws_no_legend(self, ptype):
        fig, _ = _fig([{"type": ptype, "yvar": "mpg", "xvar": "weight",
                        "options": {}}])
        assert not _legend_shown(fig), (
            f"a single {ptype} drew a legend; twoway would not"
        )

    @pytest.mark.parametrize("ptype", ["histogram", "kdensity"])
    def test_a_single_univariate_plot_draws_no_legend(self, ptype):
        fig, _ = _fig([{"type": ptype, "yvar": "mpg", "options": {}}])
        assert not _legend_shown(fig)

    def test_two_plots_draw_a_legend(self):
        fig, _ = _fig(_TWO)
        assert _legend_shown(fig)
        assert len(_legend_items(fig)) >= 2

    def test_two_y_variables_draw_a_legend(self):
        fig, _ = _fig([
            {"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}},
            {"type": "scatter", "yvar": "price", "xvar": "weight",
             "options": {}},
        ])
        assert _legend_shown(fig)

    def test_legend_on_forces_one_for_a_single_series(self, truth):
        """Measured: only legend(on) draws a legend on a one-key plot."""
        fig, _ = _fig_with_gopts(_SCATTER, {"legend": "on"})
        assert _legend_shown(fig)

    def test_position_alone_does_not_force_one(self, truth):
        """Measured: legend(position(6)) on a one-key plot draws nothing."""
        fig, _ = _fig_with_gopts(_SCATTER, {"legend": "position(6)"})
        assert not _legend_shown(fig)


class TestLegendOptions:

    def test_off_with_another_suboption_still_turns_it_off(self):
        """legend(pos(6) off) needed exact string equality before."""
        fig, _ = _fig_with_gopts(_TWO, {"legend": "pos(6) off"})
        assert not _legend_shown(fig)

    def test_off_first_also_works(self, truth):
        """Measured: order-independent in Stata."""
        fig, _ = _fig_with_gopts(_TWO, {"legend": "off pos(6)"})
        assert not _legend_shown(fig)

    @pytest.mark.parametrize("pos,side", [
        (3, "right"), (9, "left"), (12, "above"), (6, "below"),
        (2, "right"), (4, "right"), (8, "left"), (10, "left"),
        (11, "above"), (1, "above"), (5, "below"), (7, "below"),
    ])
    def test_clock_positions_place_the_legend_on_the_right_side(self, pos,
                                                                side):
        """Assert the SIDE, not merely that a location exists.

        The original version of this test asserted `leg.location is not None`
        for the left/right cases, which is true of every legend Bokeh builds
        and so could not detect a placement being ignored.
        """
        fig, _ = _fig_with_gopts(_TWO, {"legend": f"position({pos})"})
        assert _legend_shown(fig)
        leg = fig.legend[0]
        panels = {"above": fig.above, "below": fig.below,
                  "left": fig.left, "right": fig.right}
        assert leg in panels[side], (
            f"legend(position({pos})) should sit {side} of the plot; it is "
            f"in {[k for k, v in panels.items() if leg in v] or 'center'}"
        )

    @pytest.mark.parametrize("pos,want", [
        (11, "top_left"), (12, "top_center"), (1, "top_right"),
        (3, "center_right"), (4, "bottom_right"), (6, "bottom_center"),
        (7, "bottom_left"), (9, "center_left"),
    ])
    def test_ring_zero_places_the_legend_inside_the_plot(self, pos, want):
        """ring(0) means inside the plot region, at the clock position.

        Every ring(0) request collapsed to top_right, because a leftover
        keyword map from the previous implementation ran afterwards and the
        word "ring" in "ring(0)" matched its "ring" entry.
        """
        fig, _ = _fig_with_gopts(
            _TWO, {"legend": f"position({pos}) ring(0)"})
        assert _legend_shown(fig)
        assert str(fig.legend[0].location) == want, (
            f"legend(position({pos}) ring(0)) placed the legend at "
            f"{fig.legend[0].location!r}, not {want!r}"
        )

    def test_ring_zero_keeps_the_legend_out_of_the_side_panels(self):
        fig, _ = _fig_with_gopts(_TWO, {"legend": "position(4) ring(0)"})
        leg = fig.legend[0]
        for panel in (fig.above, fig.below, fig.left, fig.right):
            assert leg not in panel, (
                "ring(0) means inside the plot region, not in a side panel"
            )

    def test_existing_keywords_still_work(self):
        for kw in ("top", "bottom", "left", "right"):
            fig, _ = _fig_with_gopts(_TWO, {"legend": kw})
            assert _legend_shown(fig)

    def test_order_reorders_the_keys(self):
        base, _ = _fig_with_gopts(_TWO, {"legend": "on"})
        swapped, _ = _fig_with_gopts(_TWO, {"legend": "order(2 1)"})
        b = [str(i.label) for i in _legend_items(base)]
        s = [str(i.label) for i in _legend_items(swapped)]
        assert len(b) == len(s) >= 2
        assert s == list(reversed(b)), (b, s)

    def test_order_can_drop_a_key(self):
        fig, _ = _fig_with_gopts(_TWO, {"legend": "order(1)"})
        # One key left -> by Stata's own rule there is no legend to draw.
        assert len(_legend_items(fig)) <= 1

    def test_order_text_matches_the_measured_legend(self, truth):
        """WP-28 B5: text after a key number in order() retitles that key
        (axis_truth.json c_order_relab, order(2 "FIT" 1 "RAW"))."""
        fig, _ = _fig_with_gopts(_TWO, {"legend": 'order(2 "FIT" 1 "RAW")'})
        got = [getattr(i.label, "value", None) or i.label.get("value")
               for i in _legend_items(fig)]
        want = truth["findings"]["legend_cases"]["c_order_relab"][
            "keys_in_drawn_order"]
        assert got == want == ["FIT", "RAW"], got

    def test_cols_and_rows(self):
        fig, _ = _fig_with_gopts(_TWO, {"legend": "cols(2)"})
        assert fig.legend[0].ncols == 2
        fig2, _ = _fig_with_gopts(_TWO, {"legend": "rows(1)"})
        assert fig2.legend[0].nrows == 1

    def test_size_changes_the_label_size(self):
        small, _ = _fig_with_gopts(_TWO, {"legend": "size(small)"})
        large, _ = _fig_with_gopts(_TWO, {"legend": "size(large)"})
        assert (small.legend[0].label_text_font_size
                != large.legend[0].label_text_font_size)


# ======================================================================
# Titles, notes and captions
# ======================================================================

class TestTitleTextFidelity:
    """Nothing the user typed may appear as literal text inside the chart."""

    def test_title_suboptions_do_not_leak_into_the_text(self):
        fig, _ = _fig_with_gopts(
            _SCATTER, {"title": 'My Title, size(large) color(red)'})
        text = str(fig.title.text)
        assert text == "My Title", f"rendered {text!r}"
        assert "size(" not in text and "color(" not in text

    def test_note_keeps_neither_its_quotes_nor_its_suboptions(self, truth):
        fig, dr = _fig_with_gopts(_SCATTER, {"note": '"n=74", span'})
        texts = [str(getattr(r, "text", "")) for r in fig.center] + \
                [str(getattr(r, "text", "")) for r in fig.below]
        joined = " ".join(texts)
        assert "n=74" in joined, joined
        assert "span" not in joined and '"' not in joined, joined

    def test_title_size_and_colour_are_applied(self):
        plain, _ = _fig_with_gopts(_SCATTER, {"title": "T"})
        styled, _ = _fig_with_gopts(
            _SCATTER, {"title": "T, size(large) color(red)"})
        assert styled.title.text == "T"
        # WP-30 P1.12a (Evidence E4): twoway draws size(large) at 14 pt, which
        # is also the s2color title's own size, so the drawn size is '14pt'
        # (the same as the plain title), not a figure different from it.
        assert styled.title.text_font_size == plain.title.text_font_size == "14pt"
        assert str(styled.title.text_color).lower() in ("red", "#ff0000")

    def test_abbreviated_size_and_colour_are_applied(self):
        """WP-28 B3: si()/c() (the minimum abbreviations) style the title
        exactly as size()/color() do, and the drawn text matches what
        twoway drew for the same command (t_size_color_abbr)."""
        plain, _ = _fig_with_gopts(_SCATTER, {"title": "T"})
        styled, _ = _fig_with_gopts(
            _SCATTER, {"title": "T, si(large) c(red)"})
        assert styled.title.text == "T"
        with open(os.path.join(_HERE, "fixtures", "text_truth.json")) as fh:
            text_truth = json.load(fh)
        assert styled.title.text.split("\n") == \
            text_truth["probes"]["t_size_color_abbr"]["added_texts"]
        # WP-30 P1.12a (Evidence E4): twoway draws size(large) at 14 pt, which
        # is also the s2color title's own size, so the drawn size is '14pt'
        # (the same as the plain title), not a figure different from it.
        assert styled.title.text_font_size == plain.title.text_font_size == "14pt"
        assert str(styled.title.text_color).lower() in ("red", "#ff0000")

    def test_canvas_text_is_not_html_escaped(self):
        """Bokeh draws a title as a canvas glyph, not as HTML."""
        fig, _ = _fig_with_gopts(_SCATTER, {"title": "R&D spend"})
        assert str(fig.title.text) == "R&D spend", fig.title.text

    def test_axis_titles_are_not_html_escaped(self):
        fig, _ = _fig_with_gopts(
            _SCATTER, {"xtitle": "R&D spend", "ytitle": "Profit & loss"})
        assert str(fig.xaxis[0].axis_label) == "R&D spend"
        assert str(fig.yaxis[0].axis_label) == "Profit & loss"

    def test_an_apostrophe_survives_on_the_canvas(self):
        fig, _ = _fig_with_gopts(_SCATTER, {"title": "Ford's mileage"})
        assert str(fig.title.text) == "Ford's mileage"

    def test_note_and_caption_do_not_overlap(self):
        """Both were a Label at screen (0,0) added "below".

        What separates them is that each add_layout(..., "below") call gets a
        row of its own -- NOT a difference in y.  This used to assert
        ``note.y != caption.y``, which is a proxy for the wrong mechanism:
        the caption was given y = -12.0 to push it down, a negative screen
        offset puts a Label outside the row Bokeh sized for it, and it is
        clipped.  Measured in a browser against bokeh 3.9, an otherwise
        identical Label renders at y = 0.0 and y = 2.0 and does not render at
        all at y = -12.0 -- so this assertion passed for as long as the
        caption was invisible.  Assert the two properties that actually
        decide the outcome instead: separate rows, and a drawable offset.
        """
        # Flipped (WP-30 P1.2a): Labels with a y offset were wrong because
        # twoway places the boxes by the scheme's clock, which S15 draws as
        # side-panel Titles -- each its own row, with no offset to clip.
        from bokeh.models import Title
        fig, _ = _fig_with_gopts(
            _SCATTER, {"note": "the note", "caption": "the caption"})
        rows = [r for r in fig.below if isinstance(r, Title)]
        found = {str(r.text): r for r in rows}
        assert "the note" in found and "the caption" in found, list(found)
        assert found["the note"] is not found["the caption"], (
            "note and caption must be separate Titles in separate rows"
        )

    def test_the_caption_sits_below_the_note(self, truth):
        """Measured in Stata: note is ring(4), caption ring(5).

        Bokeh stacks the "below" panel in the order things are added to it, so
        the caption sitting lower is a matter of being added second -- not of
        carrying a smaller y, which only moves it within its own row (and, if
        negative, out of that row entirely).  This asserted
        ``caption.y < note.y`` and so passed while the caption was clipped
        away; it now asserts the ordering that actually places them.
        """
        fig, _ = _fig_with_gopts(
            _SCATTER, {"note": "the note", "caption": "the caption"})
        # Flipped (WP-30 P1.2a): the boxes are side-panel Titles (no y).
        from bokeh.models import Title
        below = [str(r.text) for r in fig.below if isinstance(r, Title)]
        assert "the note" in below and "the caption" in below, below
        assert below.index("the note") < below.index("the caption"), below

    def test_the_subtitle_does_not_collide_with_the_title(self):
        fig, _ = _fig_with_gopts(
            _SCATTER, {"title": "Main", "subtitle": "Second"})
        texts = [str(getattr(r, "text", ""))
                 for r in list(fig.above) + list(fig.center)]
        assert "Second" in " ".join(texts)


class TestDashboardTitleEscaping:
    """The Bootstrap path escaped the dashboard title twice.

    The two layouts have to be checked differently.  The Bootstrap path
    writes the header straight into the HTML document, so the file itself is
    the evidence.  The non-Bootstrap path puts it in a Bokeh ``Div`` model,
    whose text Bokeh then escapes again when it serialises the document into
    a ``<script type="application/json">`` block -- that second layer is
    correct and the browser undoes it, so the file is NOT evidence there and
    the model property is checked instead.
    """

    def _render(self, layout, title, subtitle=""):
        import tempfile
        spec = make_spec(_SCATTER)
        spec["build_options"]["layout"] = layout
        spec["build_options"]["title"] = title
        spec["build_options"]["subtitle"] = subtitle
        sp = tempfile.mkstemp(".json")[1]
        dp = tempfile.mkstemp(".json")[1]
        op = tempfile.mkstemp(".html")[1]
        with open(sp, "w") as f:
            json.dump(spec, f)
        with open(dp, "w") as f:
            json.dump(make_data_json(_auto()), f)
        dr = DashRenderer(sp, dp, op)
        html_text = dr.render()
        for p_ in (sp, dp, op):
            try:
                os.unlink(p_)
            except OSError:
                pass
        return html_text, dr

    def _header_html(self, layout, title, subtitle=""):
        """The header markup as the browser will see it, for either layout."""
        html_text, dr = self._render(layout, title, subtitle)
        if layout == "bs":
            return html_text
        from bokeh.models import Div
        parts = []
        for model in dr._last_layout_root.select({"type": Div}):
            parts.append(model.text)
        return "\n".join(parts)

    @pytest.mark.parametrize("layout", ["auto", "bs"])
    def test_an_ampersand_is_escaped_exactly_once(self, layout):
        out = self._header_html(layout, "Price & Weight")
        assert "&amp;amp;" not in out, f"{layout}: title escaped twice"
        assert "Price &amp; Weight" in out, (
            f"{layout}: the title is not escaped exactly once"
        )

    @pytest.mark.parametrize("layout", ["auto", "bs"])
    def test_an_apostrophe_is_escaped_exactly_once(self, layout):
        out = self._header_html(layout, "Ford's cars")
        assert "&amp;#x27;" not in out, f"{layout}: apostrophe escaped twice"
        assert "Ford&#x27;s cars" in out or "Ford's cars" in out

    @pytest.mark.parametrize("layout", ["auto", "bs"])
    def test_a_script_tag_is_still_escaped(self, layout):
        """Escaping once must still be escaping."""
        out = self._header_html(layout, "<script>alert(1)</script>")
        assert "<script>alert(1)</script>" not in out
        assert "&lt;script&gt;" in out

    def test_the_subtitle_behaves_the_same(self):
        out = self._header_html("bs", "T", "R&D")
        assert "&amp;amp;" not in out
        assert "R&amp;D" in out


# ======================================================================
# Reference lines
# ======================================================================

class TestReferenceLines:

    def _spans(self, fig):
        from bokeh.models import Span
        return [r for r in fig.center if isinstance(r, Span)] + \
               [r for r in fig.renderers if isinstance(r, Span)]

    def test_a_bare_xline_still_draws(self):
        fig, _ = _fig_with_gopts(_SCATTER, {"xline": "3000"})
        assert self._spans(fig), "xline(3000) drew nothing"

    def test_suboptions_are_applied(self):
        fig, _ = _fig_with_gopts(
            _SCATTER,
            {"xline": "3000, lcolor(red) lpattern(solid) lwidth(thick)"})
        spans = self._spans(fig)
        assert spans
        s = spans[0]
        assert str(s.line_color).lower() in ("red", "#ff0000"), s.line_color
        assert s.line_dash in ("solid", [], None), s.line_dash
        assert s.line_width and s.line_width >= 2.0

    def test_the_default_style_is_not_forced_grey_dashed(self, truth):
        """Measured: Stata's default xline is BLACK and dashed."""
        fig, _ = _fig_with_gopts(_SCATTER, {"xline": "3000"})
        s = self._spans(fig)[0]
        assert str(s.line_color).lower() not in ("grey", "gray", "#808080"), (
            f"the reference line is still forced grey: {s.line_color}"
        )
        # "Not grey" alone let a red, p1-coloured or solid line pass.  The
        # measurement is the fixture's e_xline_default, `twoway scatter mpg
        # weight, xline(3000)' under the scheme it records (stcolor): of the
        # lines drawn at x = 3000, the one spanning the plot region that is
        # not the gridline.  So compare under that scheme.  (Under s2color,
        # the "default" theme above, twoway draws the line cranberry
        # #C10534 and solid and dash draws it black and dashed: measured
        # 24sep2026 from graph export .svg, reported, not fixed here.)
        scheme = truth["_meta"]["scheme_in_force"]
        probe = truth["probes"]["e_xline_default"]
        xa = probe["x_axis"]
        at = xa["tick_px"][xa["tick_values"].index(3000.0)]
        top = probe["plotregion_px"]["top"]
        bottom = probe["plotregion_px"]["bottom"]
        grid = {g[0].lower() for g in xa["gridline_style"]}
        ref = [g for g in probe["svg_line_groups"]["vertical"]
               if abs(g["px"] - at) < 0.5
               and g["span_from"] <= top + 1 and g["span_to"] >= bottom - 1
               and g["stroke"].lower() not in grid]
        assert len(ref) == 1, f"the fixture's xline(3000) is not one line: {ref}"
        fig, dr = _fig_with_gopts(_SCATTER, {"xline": "3000"},
                                  build={"scheme": scheme})
        assert dr.scheme.name == scheme, dr.scheme.name
        spans = self._spans(fig)
        assert len(spans) == 1, f"xline(3000) drew {len(spans)} lines"
        s = spans[0]
        assert str(s.line_color).lower() == ref[0]["stroke"].lower(), (
            f"dash draws xline(3000) in {s.line_color}; Stata in "
            f"{ref[0]['stroke']}"
        )
        dashed = s.line_dash not in ("solid", "", None, [])
        assert dashed is ref[0]["dashed"], (
            f"dash's line_dash {s.line_dash!r}; Stata's dashed is "
            f"{ref[0]['dashed']}"
        )

    def test_multiple_values_draw_multiple_lines(self):
        fig, _ = _fig_with_gopts(_SCATTER, {"xline": "2000 3000 4000"})
        assert len(self._spans(fig)) == 3

    def test_yline_takes_the_same_suboptions(self):
        fig, _ = _fig_with_gopts(
            _SCATTER, {"yline": "20, lcolor(blue) lwidth(vthick)"})
        s = self._spans(fig)[0]
        assert str(s.line_color).lower() in ("blue", "#0000ff")


class TestRepeatedReferenceLines:
    """A repeated yline(): each copy is its own line in its own style.

    Measured 24sep2026 from twoway's SVG export: yline(20, lcolor(red))
    yline(30) draws a red line at 20 and a default one at 30 -- twoway
    executes each copy separately (added_line_options.sthlp) -- and
    yline(20) yline(30) draws what yline(20 30) draws.  dash.ado stores the
    copies joined with a comma, ``20, lcolor(red), 30``
    (test_twoway_option_parity.cscript TP-14d); the renderer drew every
    position in one style, the last sub-options found.
    """

    def _spans(self, fig):
        from bokeh.models import Span
        return [r for r in fig.center if isinstance(r, Span)] + \
               [r for r in fig.renderers if isinstance(r, Span)]

    def test_each_copy_keeps_its_own_style(self):
        fig, _ = _fig_with_gopts(
            _SCATTER, {"yline": "20, lcolor(red), 30"})
        spans = {s.location: s for s in self._spans(fig)}
        assert sorted(spans) == [20.0, 30.0], sorted(spans)
        assert str(spans[20.0].line_color).lower() in ("red", "#ff0000")
        assert str(spans[30.0].line_color).lower() not in ("red", "#ff0000")

    def test_a_later_copy_styles_only_itself(self):
        fig, _ = _fig_with_gopts(
            _SCATTER, {"xline": "2000, 3000, lcolor(blue)"})
        spans = {s.location: s for s in self._spans(fig)}
        assert sorted(spans) == [2000.0, 3000.0], sorted(spans)
        assert str(spans[3000.0].line_color).lower() in ("blue", "#0000ff")
        assert str(spans[2000.0].line_color).lower() not in ("blue", "#0000ff")

    def test_one_copy_reads_as_it_always_did(self):
        fig, _ = _fig_with_gopts(
            _SCATTER, {"yline": "20 30, lcolor(red)"})
        spans = self._spans(fig)
        assert len(spans) == 2
        assert all(str(s.line_color).lower() in ("red", "#ff0000")
                   for s in spans)

    def test_the_instances(self):
        bad = []
        got = dash_render._dash_refline_instances(
            "20, lcolor(red), 30 40, lwidth(thick) nosuch(1)", bad)
        assert got == [([20.0], {"lcolor": "red"}),
                       ([30.0, 40.0], {"lwidth": "thick"})], got
        assert bad == ["nosuch(1)"], bad

    def test_the_comma_split_honours_quotes_and_parentheses(self):
        assert dash_render._dash_by_tokens_commas(
            'a, b(c, d) "e, f", g') == ["a", ' b(c, d) "e, f"', " g"]

    def test_adversarial_many_copies_are_linear(self):
        """Resource exhaustion: 20,000 copies are read in one pass."""
        import time
        raw = ", ".join("%d, lcolor(red)" % i for i in range(20000))
        t0 = time.perf_counter()
        got = dash_render._dash_refline_instances(raw, [])
        assert len(got) == 20000
        assert time.perf_counter() - t0 < 5.0

    def test_adversarial_hostile_text_is_named_not_drawn(self):
        """Injection: text that is no position nor sub-option is named
        in the note, never drawn or evaluated."""
        bad = []
        got = dash_render._dash_refline_instances(
            '20, lcolor(red), <script>alert(1)</script>, __import__("os")',
            bad)
        assert got == [([20.0], {"lcolor": "red"})], got
        assert bad and all("20" not in b for b in bad), bad


# ======================================================================
# Marker, line and fill styling
# ======================================================================

class TestMarkerAndFillOptions:

    def _glyph(self, options, ptype="scatter"):
        fig, _ = _fig([{"type": ptype, "yvar": "mpg", "xvar": "weight",
                        "options": options}])
        for r in fig.renderers:
            if hasattr(r, "glyph") and hasattr(r.glyph, "fill_color"):
                return r.glyph
        return fig.renderers[0].glyph

    def test_mlcolor_colours_the_marker_border(self):
        g = self._glyph({"mlcolor": "red", "lcolor": "blue"})
        assert str(g.line_color).lower() in ("red", "#ff0000"), g.line_color

    def test_mlcolor_does_not_change_the_connecting_line(self):
        fig, _ = _fig([{"type": "connected", "yvar": "mpg", "xvar": "weight",
                        "options": {"mlcolor": "red", "lcolor": "blue"}}])
        lines = [r.glyph for r in fig.renderers
                 if type(r.glyph).__name__ == "Line"]
        assert lines, "no connecting line was drawn"
        assert str(lines[0].line_color).lower() in ("blue", "#0000ff")

    def test_mlwidth_sets_the_marker_border_width(self):
        g = self._glyph({"mlwidth": "thick"})
        assert g.line_width and g.line_width >= 2.0

    def test_fcolor_none_is_transparent_not_white(self):
        g = self._glyph({"fcolor": "none"}, ptype="area")
        assert (g.fill_alpha == 0 or g.fill_color is None), (
            f"fcolor(none) painted {g.fill_color!r} at alpha {g.fill_alpha!r}"
        )

    def test_falpha_is_honoured(self):
        a = self._glyph({"fcolor": "navy", "falpha": "20"}, ptype="area")
        b = self._glyph({"fcolor": "navy", "falpha": "80"}, ptype="area")
        assert a.fill_alpha != b.fill_alpha
        assert a.fill_alpha == pytest.approx(0.2)

    @pytest.mark.parametrize("sym,expect_hollow", [
        ("Oh", True), ("Sh", True), ("Dh", True),
        ("O", False), ("S", False), ("D", False),
    ])
    def test_hollow_symbols_are_hollow(self, sym, expect_hollow):
        g = self._glyph({"msymbol": sym})
        hollow = (g.fill_alpha == 0 or g.fill_color is None)
        assert bool(hollow) is expect_hollow, (
            f"msymbol({sym}): fill_color={g.fill_color!r} "
            f"fill_alpha={g.fill_alpha!r}"
        )

    @pytest.mark.parametrize("sym", ["i", "none"])
    def test_invisible_symbols_draw_nothing(self, sym):
        g = self._glyph({"msymbol": sym})
        invisible = ((getattr(g, "fill_alpha", 1) == 0
                      and getattr(g, "line_alpha", 1) == 0)
                     or getattr(g, "size", 1) == 0)
        assert invisible, (
            f"msymbol({sym}) still drew a visible marker: size={g.size!r}"
        )

    def test_mlabgap_accepts_a_size_keyword(self):
        """mlabgap(small) threw and was silently dropped."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            fig, _ = _fig([{"type": "scatter", "yvar": "mpg",
                            "xvar": "weight",
                            "options": {"mlabel": "price",
                                        "mlabgap": "small"}}])
        from bokeh.models import LabelSet
        labels = [r for r in fig.center if isinstance(r, LabelSet)]
        assert labels, "the marker labels were dropped"
        assert labels[0].x_offset not in (None, 0) or \
               labels[0].y_offset not in (None, 0)

    def test_colormissing_is_translated_to_css(self):
        fig, _ = _fig([{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                        "options": {"colorvar": "rep78",
                                    "colormissing": "eltblue"}}])
        from bokeh.models import LinearColorMapper, CategoricalColorMapper
        mappers = [m for m in fig.select({"type": LinearColorMapper})]
        mappers += [m for m in fig.select({"type": CategoricalColorMapper})]
        assert mappers, "no colour mapper was built"
        for m in mappers:
            nan_c = str(getattr(m, "nan_color", "") or "")
            if not nan_c:
                continue
            assert nan_c.startswith("#") or nan_c.isalpha(), (
                f"colormissing produced invalid CSS: {nan_c!r}"
            )
            assert nan_c != "eltblue", (
                "colormissing reached Bokeh untranslated"
            )
        # The loop skips a mapper with no nan_color and refuses only the
        # untranslated word, so a colormissing() ignored outright -- the
        # mapper keeping dash's own #808080 -- passed it (measured
        # 24sep2026).  Stata's eltblue is RGB 130 192 233
        # (color-eltblue.style), #82c0e9, and every mapper paints missing so.
        nans = [str(getattr(m, "nan_color", "") or "").lower()
                for m in mappers]
        assert nans and all(n == "#82c0e9" for n in nans), (
            f"colormissing(eltblue) painted missing values {nans}"
        )

    def test_colormissing_with_an_unknown_colour_does_not_kill_the_render(self):
        """It used to raise out of the mapper and take the whole figure down."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            fig, _ = _fig([{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                            "options": {"colorvar": "rep78",
                                        "colormissing": "notacolour"}}])
        assert fig is not None
        assert any("colormissing" in str(w.message) for w in caught)


# ======================================================================
# if qualifiers
# ======================================================================

class TestIfQualifierFunctions:
    """The three most common Stata qualifier forms rendered UNFILTERED."""

    def _n_rows(self, if_expr):
        import tempfile
        spec = make_spec(_SCATTER)
        spec["graphs"][0]["if_expr"] = if_expr
        sp = tempfile.mkstemp(".json")[1]
        dp = tempfile.mkstemp(".json")[1]
        op = tempfile.mkstemp(".html")[1]
        with open(sp, "w") as f:
            json.dump(spec, f)
        with open(dp, "w") as f:
            json.dump(make_data_json(_auto()), f)
        dr = DashRenderer(sp, dp, op)
        figs = dr._build_figures()
        for p in (sp, dp, op):
            try:
                os.unlink(p)
            except OSError:
                pass
        fig = figs["g1"]
        for r in fig.renderers:
            data = getattr(r.data_source, "data", {})
            if "weight" in data:
                return len(data["weight"])
        return None

    # The exact row counts, measured 24sep2026 on _auto(): rep78 cycles
    # 1 2 3 4 5 missing, so 12 of the 74 rows are missing and 26 are 1 or 2;
    # weight is linspace(1760, 4840, 74), so 24 rows lie in [2000, 3000] and
    # 37 rows above 3000 have rep78.  "0 < n < 74" -- the range these
    # replaced -- passed a qualifier translated wrongly, as long as it kept
    # some rows and dropped others.

    def test_baseline_is_all_rows(self):
        assert self._n_rows("") == 74

    def test_not_missing(self):
        n = self._n_rows("!missing(rep78)")
        assert n is not None and 0 < n < 74, n
        assert n == 62, n

    def test_missing_directly(self):
        n = self._n_rows("missing(rep78)")
        assert n is not None and 0 < n < 74, n
        assert n == 12, n

    def test_inlist(self):
        n = self._n_rows("inlist(rep78,1,2)")
        assert n is not None and 0 < n < 74, n
        assert n == 26, n

    def test_inrange(self):
        n = self._n_rows("inrange(weight,2000,3000)")
        assert n is not None and 0 < n < 74, n
        assert n == 24, n

    def test_stata_missing_idiom_less_than_dot(self):
        n = self._n_rows("rep78 < .")
        assert n is not None and 0 < n < 74, n
        assert n == 62, n

    def test_combined_with_ordinary_comparisons(self):
        n = self._n_rows("!missing(rep78) & weight > 3000")
        assert n is not None and 0 < n < 74, n
        assert n == 37, n


class TestIfQualifierWhitelistIsNotWeakened:
    """Adversarial, per project rule 18.

    The validator replaced a regex blacklist with an AST whitelist in commit
    700e770 to close an RCE.  Supporting Stata's functions must be a
    translation BEFORE validation, not a hole in it.
    """

    @pytest.mark.parametrize("hostile", [
        "__import__('os').system('true')",
        "().__class__.__bases__[0].__subclasses__()",
        "eval('1+1')",
        "exec('x=1')",
        "open('/etc/passwd').read()",
        "globals()",
        "locals()",
        "compile('1','','eval')",
        "getattr(weight,'__class__')",
        "weight.__class__.__mro__",
        "[x for x in ().__class__.__bases__]",
        "lambda: 1",
        "missing(__import__('os').getpid())",
        "inlist(__import__('os').getpid(),1)",
        "inrange(open('/etc/passwd'),1,2)",
        "missing(rep78) or __import__('os').system('true')",
        "inlist(rep78, 1, __import__('sys').exit())",
        "weight.__reduce__()",
    ])
    def test_hostile_expressions_are_rejected(self, hostile):
        """Rejected both raw and after the Stata translation step.

        The translation is what makes missing()/inlist()/inrange() work, so
        it is the thing that could have opened a hole. Both paths are checked.
        """
        cols = ["weight", "rep78"]
        assert dash_render._validate_if_expr(hostile, cols) is False, (
            f"the whitelist accepted {hostile!r}"
        )
        translated = dash_render._stata_if_to_pandas(hostile)
        assert dash_render._validate_if_expr(translated, cols) is False, (
            f"the translation turned {hostile!r} into something the "
            f"whitelist accepts: {translated!r}"
        )

    @pytest.mark.parametrize("ok", [
        "weight > 3000",
        "!missing(rep78)",
        "missing(rep78)",
        "inlist(rep78,1,2,3)",
        "inrange(weight,2000,3000)",
        "rep78 < .",
        "rep78 != .",
        "weight > 3000 & mpg < 30",
        "weight > 3000 | mpg < 30",
    ])
    def test_supported_forms_are_accepted(self, ok):
        """Through the real pipeline: translate, then validate.

        _validate_if_expr deliberately does NOT translate: a caller that
        validated one string and evaluated another would be unsafe, so the
        two steps stay separate and _apply_graph_filter runs them in order.
        """
        translated = dash_render._stata_if_to_pandas(ok)
        assert dash_render._validate_if_expr(
            translated, ["weight", "rep78", "mpg"]) is True, (
            f"the validator rejected {ok!r} (translated to {translated!r})"
        )

    def test_an_unknown_column_is_still_rejected(self):
        assert dash_render._validate_if_expr(
            "nosuchvar > 1", ["weight"]) is False


# ======================================================================
# Secondary axis under filtering, and mlabel on lines
# ======================================================================

class TestSecondaryAxisRange:

    def test_the_secondary_range_follows_the_graph_qualifier(self):
        """It was computed from the UNFILTERED frame."""
        import tempfile
        plots = [
            {"type": "scatter", "yvar": "mpg", "xvar": "weight",
             "options": {}},
            {"type": "scatter", "yvar": "price", "xvar": "weight",
             "options": {"yaxis": "2"}},
        ]
        spec = make_spec(plots)
        spec["graphs"][0]["if_expr"] = "weight < 2500"
        sp = tempfile.mkstemp(".json")[1]
        dp = tempfile.mkstemp(".json")[1]
        op = tempfile.mkstemp(".html")[1]
        with open(sp, "w") as f:
            json.dump(spec, f)
        with open(dp, "w") as f:
            json.dump(make_data_json(_auto()), f)
        dr = DashRenderer(sp, dp, op)
        fig = dr._build_figures()["g1"]
        for p in (sp, dp, op):
            try:
                os.unlink(p)
            except OSError:
                pass
        rng = fig.extra_y_ranges["y2"]
        df = _auto()
        sub_max = float(df.loc[df["weight"] < 2500, "price"].max())
        full_max = float(df["price"].max())
        assert rng.end < full_max, (
            f"the secondary axis spans the unfiltered data: "
            f"end={rng.end}, filtered max={sub_max}, full max={full_max}"
        )


class TestMlabelOnLines:

    def test_labels_land_on_the_sorted_points(self):
        """A connected plot sorts its line by x; each marker label must stay
        on its own point.  (This was a `line' layer, which twoway -- and
        now dash -- draws no marker label on; connected labels its markers.)
        """
        from bokeh.models import LabelSet
        df = pd.DataFrame({
            "y": [1.0, 2.0, 3.0, 4.0],
            "x": [40.0, 10.0, 30.0, 20.0],
            "lab": [100.0, 200.0, 300.0, 400.0],
        })
        fig, _ = _fig([{"type": "connected", "yvar": "y", "xvar": "x",
                        "options": {"mlabel": "lab"}}], df=df)
        labels = [r for r in fig.center if isinstance(r, LabelSet)]
        assert labels, "no marker labels were drawn"
        src = labels[0].source
        xs = list(src.data[labels[0].x])
        texts = [float(t) for t in src.data[labels[0].text]]
        pairs = dict(zip(xs, texts))
        expected = {40.0: 100.0, 10.0: 200.0, 30.0: 300.0, 20.0: 400.0}
        assert pairs == expected, (
            f"marker labels attached to the wrong points: {pairs}"
        )


# ======================================================================
# The phantom hover() option
# ======================================================================

class TestHoverOptionIsRealOrGone:
    """The renderer read a hover() key dash.ado does not declare."""

    def test_dash_ado_declares_it_or_the_renderer_does_not_read_it(self):
        ado = open(os.path.join(_HERE, "..", "dash.ado"),
                   encoding="utf-8", errors="replace").read()
        src = open(os.path.join(_HERE, "..", "dash_render.py")).read()
        code = "\n".join(l.split("#", 1)[0] for l in src.splitlines())
        reads_it = 'graph_opts.get("hover"' in code
        declares_it = "HOVer(" in ado or "HOVER(" in ado
        assert reads_it == declares_it, (
            "dash_render reads a hover() option that dash.ado does not "
            "declare (or the reverse). A dead option read is exactly what "
            "misled the axis work."
            if reads_it else
            "dash.ado declares hover() but the renderer never reads it."
        )
