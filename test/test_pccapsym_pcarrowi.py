"""pccapsym and pcarrowi: two twoway plot types dash refused (WP-22 TR-22.1).

Measured 23sep2026 with the console binary on this branch before the change:
``dash pccapsym mpg weight turn length`` and ``dash pcarrowi 20 3000 30 4000``
both exited r(198) "unrecognised plot type", where twoway draws both, rc 0.

What twoway does, from its own help and measured against it:

* ``twoway pccapsym y1 x1 y2 x2`` draws, per observation, a spike from
  (y1, x1) to (y2, x2) with the same marker symbol at each end.  Line options
  style the spike, marker options the markers, and marker labels go on the
  first coordinate (``headlabel`` would move them to the second).
* ``twoway pcarrowi`` is the immediate form of ``pcarrow``:
  ``#y1 #x1 #y2 #x2 [(#clockpos)] ["text for label"] ...``.  A label implies
  ``mlabel()`` and a clock position ``mlabvposition()``; the label sits at
  the arrow's tail, (y1, x1).

This file holds the renderer's half: ``GlyphMapper.map_pccapsym`` and
``map_pcarrowi``, the dispatch that reaches them, the served layer source,
and the served app drawing what the saved page draws.  dash.ado's half --
the Mata table, the routing, the immediate-value encoder and its refusals --
is test_parser.cscript P1A-49..57.
"""
import math
import os
import sys
import time
import warnings

import pandas as pd
import pytest
from bokeh.models import Arrow, ColumnDataSource, LabelSet
from bokeh.models.glyphs import Scatter, Segment
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from test_server_layer_defects import (make_spec, served,  # noqa: E402
                                       standalone)

NAN = float("nan")
# WP-30 P1.12a (Evidence E5, twoway measured): a pcarrowi label sits
# (radius + gap) from the tail, the radius half the scheme's marker size
# (symbolsize medium 1.52778 rs, 1 rs = 2.88 pt = 3.84 px) and the gap
# gsize label_gap 2 pt: 2.93334 + 2.66667 = 5.6 px.
_D = 1.52778 * 2.88 * (4 / 3) / 2 + 2 * (4 / 3)


def _pc_source(**extra):
    data = {"y1": [1.0, 2.0, NAN, 4.0], "x1": [10.0, 20.0, 30.0, 40.0],
            "y2": [5.0, 6.0, 7.0, 8.0], "x2": [15.0, 25.0, 35.0, 45.0]}
    data.update(extra)
    return ColumnDataSource(data)


def _labelsets(fig):
    return [r for r in fig.center if isinstance(r, LabelSet)]


def _col(renderer, attr):
    """The values a glyph draws for one of its coordinate fields."""
    field = getattr(renderer.glyph, attr)
    field = field if isinstance(field, str) else getattr(field, "field", field)
    return [float(v) for v in renderer.data_source.data[field]]


# ===========================================================================
# map_pccapsym
# ===========================================================================

class TestMapPccapsym:
    def _draw(self, options=None, source=None, color_idx=0, view=None):
        fig = figure()
        gm = dr.GlyphMapper()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            out = gm.map_pccapsym(fig, source or _pc_source(), "y1", "x1",
                                  "y2", "x2", dict(options or {}),
                                  view=view, color_idx=color_idx)
        return gm, fig, out

    def test_it_returns_a_spike_and_its_markers(self):
        _, _, out = self._draw()
        assert [type(r.glyph) for r in out] == [Segment, Scatter]

    def test_the_spike_runs_from_the_first_coordinate_to_the_second(self):
        _, _, (seg, _dots) = self._draw()
        assert _col(seg, "x0") == [10.0, 20.0, 40.0]
        assert _col(seg, "y0") == [1.0, 2.0, 4.0]
        assert _col(seg, "x1") == [15.0, 25.0, 45.0]
        assert _col(seg, "y1") == [5.0, 6.0, 8.0]

    def test_a_marker_caps_each_end(self):
        _, _, (_seg, dots) = self._draw()
        assert _col(dots, "x") == [10.0, 20.0, 40.0, 15.0, 25.0, 45.0]
        assert _col(dots, "y") == [1.0, 2.0, 4.0, 5.0, 6.0, 8.0]

    def test_a_row_with_a_missing_coordinate_draws_neither(self):
        """Row 3 has no y1: no spike, and no marker at either end."""
        _, _, (seg, dots) = self._draw()
        assert 30.0 not in _col(seg, "x0")
        assert 30.0 not in _col(dots, "x") and 35.0 not in _col(dots, "x")

    def test_the_default_colours_follow_the_scheme(self):
        for idx in (0, 2):
            gm, _, (seg, dots) = self._draw(color_idx=idx)
            assert seg.glyph.line_color == gm.scheme.default_color(idx, "pccapsym")
            assert dots.glyph.fill_color == gm.scheme.default_color(idx, "pcscatter")
            assert dots.glyph.line_color == gm.scheme.default_color(idx, "pcscatter")

    def test_the_marker_is_the_schemes_symbol_and_size(self):
        gm, _, (_seg, dots) = self._draw(color_idx=1)
        assert dots.glyph.marker == gm.scheme.default_symbol(1)
        assert dots.glyph.size == gm.scheme.default_marker_size(1)

    def test_line_options_style_the_spike_and_not_the_markers(self):
        gm, _, (seg, dots) = self._draw({"lcolor": "magenta", "lwidth": "thick",
                                         "lpattern": "dash"})
        assert seg.glyph.line_color == "#ff00ff"
        assert seg.glyph.line_width == gm.tr.translate_lwidth("thick")
        assert list(seg.glyph.line_dash) == list(gm.tr.translate_lpattern("dash"))
        # twoway: lcolor() and lwidth() are the spike's; the marker outline
        # is mlcolor()/mlwidth().
        base_gm, _, (_s, base_dots) = self._draw()
        assert dots.glyph.line_color == base_dots.glyph.line_color
        assert dots.glyph.line_width == base_dots.glyph.line_width

    def test_marker_options_style_the_markers_and_not_the_spike(self):
        gm, _, (seg, dots) = self._draw({"msymbol": "D", "mcolor": "red",
                                         "msize": "large"})
        assert dots.glyph.marker == gm.tr.translate_msymbol("D")
        assert dots.glyph.fill_color == gm.tr.translate_mcolor("red")
        # Flipped (WP-31 E1): the size was msize(large) alone; a diamond is
        # sqrt(2) of the circle's height, as twoway draws D
        # (symbol_pattern_truth.json), so it is msize(large) times that.
        assert dots.glyph.size == pytest.approx(
            gm.tr.translate_msize("large") * 2 ** 0.5)
        assert seg.glyph.line_color == gm.scheme.default_color(0, "pccapsym")

    def test_mlcolor_and_mlwidth_are_the_marker_outline(self):
        gm, _, (seg, dots) = self._draw({"mlcolor": "green",
                                         "mlwidth": "thick"})
        assert dots.glyph.line_color == gm.tr.translate_mcolor("green")
        assert dots.glyph.line_width == gm.tr.translate_lwidth("thick")
        assert seg.glyph.line_color == gm.scheme.default_color(0, "pccapsym")

    def test_color_colours_the_spike_and_the_markers(self):
        gm, _, (seg, dots) = self._draw({"color": "red"})
        red = gm.tr.translate_mcolor("red")
        assert seg.glyph.line_color == red
        assert dots.glyph.fill_color == red and dots.glyph.line_color == red

    def test_mlabel_labels_the_first_coordinate(self):
        src = _pc_source(lab=["a", "b", "c", "d"])
        _, fig, (seg, _dots) = self._draw({"mlabel": "lab"}, source=src)
        (ls,) = _labelsets(fig)
        assert ls.x == "x1" or getattr(ls.x, "field", None) == "x1"
        assert ls.y == "y1" or getattr(ls.y, "field", None) == "y1"
        assert list(ls.source.data["lab"]) == ["a", "b", "d"]

    def test_a_missing_label_does_not_drop_a_spike(self):
        src = _pc_source(lab=[None, "b", "c", "d"])
        _, fig, (seg, _dots) = self._draw({"mlabel": "lab"}, source=src)
        assert _col(seg, "x0") == [10.0, 20.0, 40.0]

    def test_no_label_is_drawn_without_mlabel(self):
        _, fig, _ = self._draw(source=_pc_source(lab=["a", "b", "c", "d"]))
        assert not _labelsets(fig)

    def test_a_repeated_variable_is_one_column(self):
        """``pccapsym y x y x`` is a legal command."""
        src = ColumnDataSource({"y": [1.0, 2.0], "x": [3.0, 4.0]})
        fig = figure()
        out = dr.GlyphMapper().map_pccapsym(fig, src, "y", "x", "y", "x", {})
        assert _col(out[0], "x0") == [3.0, 4.0]

    def test_a_date_label_with_a_missing_value_saves(self):
        """mlabel(datevar), one date missing: the page must still save.

        Found by the WP-22 review (23sep2026): the label column was rebuilt
        as a Python list, which turns a %td column into Timestamps and NaT,
        and Bokeh writes NaT as a bare NaN -- file_html raised "Out of range
        float values are not JSON compliant" and no dashboard was written.
        map_scatter, handed the same source, saves."""
        import numpy as np
        from bokeh.embed import file_html
        from bokeh.resources import INLINE
        d = np.array(["2020-01-01", "NaT", "2020-01-03", "2020-01-04"],
                     dtype="datetime64[us]")
        fig = figure()
        gm = dr.GlyphMapper()
        gm.date_vars = {"d": "td"}
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            gm.map_pccapsym(fig, _pc_source(d=d), "y1", "x1", "y2", "x2",
                            {"mlabel": "d"})
            html = file_html(fig, INLINE, "pccapsym date label")
        (ls,) = _labelsets(fig)
        assert len(ls.source.data[ls.text]) == 3
        assert "pccapsym date label" in html


# ===========================================================================
# map_pcarrowi
# ===========================================================================

_LABELLED = [[0.0, 0.0, 0.0, 1.0, "3 o'clock", 3],
             [0.0, 0.0, 1.0, 0.0, "12 o'clock", 12]]


class TestMapPcarrowi:
    def _draw(self, values, options=None, color_idx=0):
        fig = figure()
        gm = dr.GlyphMapper()
        # Notes are once per render (_DASH_NOTED); each draw here is one.
        dr._dash_reset_notes()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            out = gm.map_pcarrowi(fig, values, dict(options or {}),
                                  color_idx=color_idx)
        return gm, fig, out, [str(w.message) for w in caught]

    def test_it_draws_what_pcarrow_draws_from_the_same_numbers(self):
        values = [[20.0, 3000.0, 30.0, 4000.0], [25.0, 2000.0, 22.0, 3500.0]]
        _, fig_i, out_i, _ = self._draw(values)
        fig_v = figure()
        src = ColumnDataSource({"y1": [20.0, 25.0], "x1": [3000.0, 2000.0],
                                "y2": [30.0, 22.0], "x2": [4000.0, 3500.0]})
        out_v = dr.GlyphMapper().map_pcarrow(fig_v, src, "y1", "x1", "y2",
                                             "x2", {})
        assert [type(r.glyph) for r in out_i] == [type(r.glyph) for r in out_v]
        for attr in ("x0", "y0", "x1", "y1"):
            assert _col(out_i[0], attr) == _col(out_v[0], attr)
        # Flipped (WP-31 C1): an OpenHead Arrow was wrong because twoway's
        # head is _gr_arrowhead's geometry, two open strokes in the series
        # colour by default; a filled head needs barbsize(); Bokeh's
        # ArrowHead is no longer used.  pcarrowi's head glyph and script
        # args equal pcarrow's from the same numbers.
        assert not _arrow_annotations(fig_i) and not _arrow_annotations(fig_v)
        heads_i, heads_v = _head_cbs(fig_i), _head_cbs(fig_v)
        assert len(heads_i) == len(heads_v) == 1
        assert [type(r.glyph).__name__ for r in _head_glyphs(fig_i)] == \
            [type(r.glyph).__name__ for r in _head_glyphs(fig_v)] == ["MultiLine"]
        for k in ("ends", "barb", "ang", "hpx"):
            assert heads_i[0].args[k] == heads_v[0].args[k]
        assert _head_rows(heads_i) == _head_rows(heads_v)
        assert len(_head_rows(heads_i)) == 2

    def test_it_honours_the_options_pcarrow_honours(self):
        gm, fig, (seg,), _ = self._draw([[0, 0, 1, 1]],
                                        {"lcolor": "magenta", "lwidth": "thick",
                                         "lpattern": "dash"})
        assert seg.glyph.line_color == "#ff00ff"
        assert seg.glyph.line_width == gm.tr.translate_lwidth("thick")
        assert list(seg.glyph.line_dash) == list(gm.tr.translate_lpattern("dash"))
        # Flipped (WP-31 C1): the head in the shaft's lcolor() was wrong
        # because twoway's line options are the shaft's (measured
        # 13oct2026: lcolor(red) lwidth(thick) leave the heads in the
        # series colour); mcolor()/mlcolor() colour the head.
        (head,) = _head_glyphs(fig)
        assert head.glyph.line_color == gm.scheme.default_color(0, "pcarrow")

    def test_the_default_colour_is_pcarrows(self):
        gm, _, (seg,), _ = self._draw([[0, 0, 1, 1]], color_idx=3)
        assert seg.glyph.line_color == gm.scheme.default_color(3, "pcarrow")

    def test_a_label_is_drawn_at_the_tail_at_its_clock_position(self):
        _, fig, _, _ = self._draw(_LABELLED)
        got = sorted(((round(ls.x_offset, 4), round(ls.y_offset, 4)),
                      list(ls.source.data[ls.text if isinstance(ls.text, str)
                                          else ls.text.field]),
                      [float(v) for v in ls.source.data["x1"]],
                      [float(v) for v in ls.source.data["y1"]])
                     for ls in _labelsets(fig))
        # WP-30 P1.12a (Evidence E5, twoway measured): pcarrow's origin is
        # half the scheme marker size (2.93334 px) + gap 2pt (2.66667 px).
        assert got == [((0, round(_D, 4)), ["12 o'clock"], [0.0], [0.0]),
                       ((round(_D, 4), 0), ["3 o'clock"], [0.0], [0.0])]

    def test_a_label_without_a_clock_takes_mlabposition(self):
        _, fig, _, _ = self._draw([[0, 0, 0, 1, "A", None]],
                                  {"mlabposition": "9"})
        (ls,) = _labelsets(fig)
        # WP-30 P1.12a (Evidence E5, twoway measured): pcarrow's origin is
        # half the scheme marker size (2.93334 px) + gap 2pt (2.66667 px).
        assert ls.x_offset == pytest.approx(-_D)
        assert ls.y_offset == 0

    def test_a_label_without_a_clock_or_mlabposition_is_at_three(self):
        _, fig, _, _ = self._draw([[0, 0, 0, 1, "A"]])
        (ls,) = _labelsets(fig)
        # WP-30 P1.12a (Evidence E5, twoway measured): pcarrow's origin is
        # half the scheme marker size (2.93334 px) + gap 2pt (2.66667 px).
        assert ls.x_offset == pytest.approx(_D)
        assert ls.y_offset == 0

    def test_a_record_without_a_label_draws_no_label(self):
        _, fig, _, _ = self._draw([[0, 0, 0, 1], [1, 1, 2, 2, "", 6]])
        assert not _labelsets(fig)

    def test_the_label_style_options_apply(self):
        gm, fig, _, _ = self._draw([[0, 0, 0, 1, "A", 3]],
                                   {"mlabcolor": "red", "mlabsize": "large"})
        (ls,) = _labelsets(fig)
        assert ls.text_color == gm.tr.translate_mcolor("red")
        # WP-30 P1.12a (Evidence E5, twoway measured): label sizes are CSS
        # points; gsize large is 4.8611 units x 2.88 = 14pt.
        assert ls.text_font_size == "14pt"

    def test_a_missing_coordinate_draws_neither_arrow_nor_label(self):
        _, fig, (seg,), _ = self._draw([[0, 0, None, 1, "A", 3],
                                        [1, 1, 2, 2]])
        assert _head_rows(_head_cbs(fig)) == [(1.0, 1.0, 2.0, 2.0)]
        assert _col(seg, "x0") == [1.0]
        assert not _labelsets(fig)

    def test_a_clock_that_is_not_a_whole_number_is_drawn_at_twelve_once(self):
        """twoway accepts (3.5) and draws the label above the tail, where
        (12) puts it, noting "named style 3.5 not found in class clockdir,
        default attributes used" -- measured 23sep2026 from the SVG export
        of ``twoway pcarrowi 0 0 0 1 (3.5) "A" ...``.  It was drawn at 3."""
        _, fig, _, warns = self._draw([[0, 0, 0, 1, "A", 3.5],
                                       [1, 1, 2, 2, "B", 3.25]])
        (ls,) = _labelsets(fig)
        # WP-30 P1.12a (Evidence E5, twoway measured): pcarrow's origin is
        # half the scheme marker size (2.93334 px) + gap 2pt (2.66667 px).
        assert ls.x_offset == 0
        assert ls.y_offset == pytest.approx(_D)
        assert sorted(ls.source.data[ls.text if isinstance(ls.text, str)
                                     else ls.text.field]) == ["A", "B"]
        notes = [w for w in warns if "pcarrowi" in w and "clock" in w]
        assert len(notes) == 1, warns

    def test_each_layers_odd_clock_positions_are_named(self):
        """Two pcarrowi layers, each with a clock position that is not a
        whole number: both are named.  The review (23sep2026) measured one
        note for the whole render, so the second layer's 7.25 was drawn at
        3 without a word."""
        fig = figure()
        gm = dr.GlyphMapper()
        dr._dash_reset_notes()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            gm.map_pcarrowi(fig, [[0, 0, 0, 1, "A", 3.5]], {})
            gm.map_pcarrowi(fig, [[1, 1, 2, 2, "B", 7.25]], {}, color_idx=1)
            gm.map_pcarrowi(fig, [[2, 2, 3, 3, "C", 3.5]], {}, color_idx=2)
        notes = [str(w.message) for w in caught
                 if "pcarrowi" in str(w.message) and "clock" in str(w.message)]
        assert len(notes) == 2, notes
        assert "3.5" in notes[0] and "7.25" in notes[1]

    def test_the_arrow_heads_are_added_in_one_change(self):
        """Every arrow's head reaches the figure in ONE change of its
        annotation list, however many arrows there are.

        Found by the WP-22 review (23sep2026): map_pcarrow, which pcarrowi
        draws through, called add_layout() once per arrow, and each call
        copies the list -- quadratic: 1,000 arrows took 1.45 s and 8,000
        took 46 s (85 s here), for a list a command line can make as long as
        the macro limit allows.  Counted rather than timed, so a loaded
        machine cannot make it pass or fail: five add_layout() calls are
        five changes of `center', one assignment is one.  The count for 500
        arrows must be the count for one (the segment's legend is a change
        of its own either way)."""
        def changes_for(n):
            fig = figure()
            seen = []
            fig.on_change("center", lambda attr, old, new: seen.append(1))
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                dr.GlyphMapper().map_pcarrowi(
                    fig, [[i, i, i + 1, i + 1] for i in range(n)], {})
            # WP-31 C1: one head script over the shaft's rows.
            heads = _head_cbs(fig)
            assert len(heads) == 1 and len(_head_rows(heads)) == n
            return len(seen)

        one, many = changes_for(1), changes_for(500)
        assert many == one, (
            f"{many} changes of the figure's annotations for 500 arrows, "
            f"{one} for one: a change per arrow is quadratic")

    def test_the_label_is_text_not_markup(self):
        payload = '<img src=x onerror=alert(1)>{bf:X}"],"expr":"1'
        _, fig, _, _ = self._draw([[0, 0, 0, 1, payload, 3]])
        (ls,) = _labelsets(fig)
        # Flipped (WP-30 P1.11b): {bf:X} is graph-text markup, which twoway
        # draws as the bold text; the label stays text, never HTML or
        # script, and the raw column still holds the payload.
        assert list(ls.source.data[ls.text if isinstance(ls.text, str)
                                   else ls.text.field]) == [
            payload.replace("{bf:X}", "X")]
        assert payload in [v for c in ls.source.data.values() for v in c]

    @pytest.mark.parametrize("bad", [
        [[0, 0, "x", 1]], [[0, 0, 1]], [[0, 0, 1, 1, "a", 3, 9]], ["0 0 1 1"],
        [[0, 0, True, 1]],
    ])
    def test_a_malformed_record_is_named(self, bad):
        with pytest.raises(ValueError, match="pcarrowi"):
            dr.GlyphMapper().map_pcarrowi(figure(), bad, {})

    def test_no_values_draws_nothing_and_does_not_raise(self):
        _, fig, out, _ = self._draw([])
        assert not fig.select({"type": Arrow})
        assert all(not any(len(v) for v in r.data_source.data.values())
                   for r in out)

    def test_a_non_finite_coordinate_is_missing(self):
        _, fig, (seg,), _ = self._draw([[0, 0, float("inf"), 1],
                                        [1, 1, 2, 2]])
        assert _col(seg, "x0") == [1.0]

    def test_a_hundred_thousand_records_are_read_in_bounded_time(self):
        """The record reader is linear: no quadratic join or append."""
        values = [[i, i, i + 1, i + 1, "", None] for i in range(100_000)]
        t0 = time.perf_counter()
        recs = dr.GlyphMapper._pc_immediate_records(values, "pcarrowi")
        assert time.perf_counter() - t0 < 5.0
        assert len(recs[0]) == 100_000


# ===========================================================================
# Dispatch
# ===========================================================================

class TestTheDispatchReachesThem:
    def test_pccapsym_is_a_paired_coordinate_type(self):
        gm = dr.GlyphMapper()
        assert "pccapsym" in dr._DASH_PC_TYPES
        assert dr._dash_pc_dispatch(gm)["pccapsym"] == gm.map_pccapsym

    def test_pcarrowi_is_a_literal_type(self):
        assert "pcarrowi" in dr._DASH_LITERAL_TYPES
        assert "pcarrowi" not in dr._DASH_PC_TYPES

    def test_the_parity_guard_sees_both(self):
        assert {"pccapsym", "pcarrowi"} <= dr._dash_plot_type_names()


# ===========================================================================
# The served layer source
# ===========================================================================

class TestTheServedPcSourceCarriesTheLabel:
    _DF = pd.DataFrame({"y1": [1.0, NAN, 3.0], "x1": [1.0, 2.0, 3.0],
                        "y2": [4.0, 5.0, 6.0], "x2": [7.0, 8.0, 9.0],
                        "lab": ["a", "b", None]})

    def test_the_label_column_is_carried(self):
        src, ok = dr._dash_pc_source(self._DF, "y1", "x1", "y2", "x2", "lab")
        labs = list(src.data["lab"])
        assert ok and len(labs) == 2 and labs[0] == "a"
        # The row whose label is missing is kept, its label missing.
        assert labs[1] is None or (isinstance(labs[1], float)
                                   and math.isnan(labs[1]))

    def test_a_missing_label_keeps_its_row(self):
        src, _ = dr._dash_pc_source(self._DF, "y1", "x1", "y2", "x2", "lab")
        assert list(src.data["x1"]) == [1.0, 3.0]

    def test_without_a_label_nothing_else_changes(self):
        src, ok = dr._dash_pc_source(self._DF, "y1", "x1", "y2", "x2")
        assert ok and "lab" not in src.data
        assert list(src.data["x1"]) == [1.0, 3.0]

    def test_a_label_the_data_lacks_is_ignored(self):
        src, ok = dr._dash_pc_source(self._DF, "y1", "x1", "y2", "x2", "zz")
        assert ok and "zz" not in src.data


# ===========================================================================
# Both modes
# ===========================================================================

def _glyphs(figs):
    out = []
    for f in figs:
        for r in f.renderers:
            g = getattr(r, "glyph", None)
            if g is None:
                continue
            data = r.data_source.data
            coords = {a: [float(v) for v in data[getattr(g, a)]]
                      for a in ("x0", "y0", "x1", "y1", "x", "y")
                      if isinstance(getattr(g, a, None), str)
                      and getattr(g, a) in data}
            out.append((type(g).__name__, g.line_color, coords))
    return out


def _labels(figs):
    return sorted((ls.x_offset, ls.y_offset,
                   tuple(str(v) for v in ls.source.data[
                       ls.text if isinstance(ls.text, str) else ls.text.field]))
                  for f in figs for ls in f.center if isinstance(ls, LabelSet))


def _heads(figs):
    return sorted(_head_rows([a for f in figs for a in _head_cbs(f)]))


def _arrow_annotations(fig):
    return [a for a in fig.center if isinstance(a, Arrow)]


def _head_cbs(fig):
    """The arrowhead scripts of *fig* (WP-31 C1)."""
    from bokeh.models import CustomJS
    return [m for m in fig.references()
            if isinstance(m, CustomJS) and m.name == "dash_arrow_head"]


def _head_glyphs(fig):
    return [r for r in fig.renderers if "dash-arrowhead" in (r.tags or [])]


def _head_rows(arrows):
    """(x_start, y_start, x_end, y_end) of every head the Arrow annotations
    draw, in drawing order: a row of the source a field names, or the
    annotation's literal numbers.  pcarrow draws ONE annotation over the
    shaft's source, so its heads follow the rows the shaft follows."""
    out = []
    for a in arrows:
        if not isinstance(a, Arrow):
            # An arrowhead script (WP-31 C1): its source's rows.
            ar = a.args
            cols = [list(ar["src"].data[ar[k]]) for k in ("x1", "y1", "x2",
                                                         "y2")]
            out.extend(tuple(float(c[i]) for c in cols)
                       for i in range(len(cols[0])))
            continue
        specs = [getattr(a, k) for k in ("x_start", "y_start", "x_end",
                                        "y_end")]
        names = [getattr(v, "field", None) or (v.get("field")
                 if isinstance(v, dict) else None) for v in specs]
        if all(names):
            cols = [list(a.source.data[n]) for n in names]
            out.extend(tuple(float(c[i]) for c in cols)
                       for i in range(len(cols[0])))
        else:
            out.append(tuple(float(v) for v in specs))
    return out


class TestBothModesDrawTheSame:
    def _pair(self, tmp_path, plot):
        spec = make_spec([plot])
        s_figs, _html, s_w = standalone(tmp_path, spec)
        v_figs, _doc, v_w = served(tmp_path, spec)
        return s_figs, v_figs, s_w, v_w

    def test_pccapsym_with_marker_labels(self, tmp_path):
        """The label is a column that is NOT one of the four coordinates, so
        the served layer source must carry it for itself: a label that is
        also a coordinate (as mlabel(foreign) with x2var foreign) is there
        anyway and proves nothing (the WP-22 review, 23sep2026)."""
        plot = {"type": "pccapsym", "y1var": "mpg", "x1var": "weight",
                "y2var": "mpg", "x2var": "price",
                "options": {"mlabel": "foreign", "msymbol": "D",
                            "lcolor": "navy"}}
        s, v, sw, vw = self._pair(tmp_path, plot)
        assert _glyphs(s) == _glyphs(v) and _glyphs(s)
        assert _labels(s) == _labels(v)
        assert len(_labels(s)) == 1 and len(_labels(s)[0][2]) == 10
        assert sorted(sw) == sorted(vw)
        assert not [w for w in vw if "not in the data" in w], vw

    def test_pcarrowi_with_labels_and_clock_positions(self, tmp_path):
        plot = {"type": "pcarrowi", "values": _LABELLED,
                "options": {"lcolor": "maroon"}}
        s, v, sw, vw = self._pair(tmp_path, plot)
        assert _glyphs(s) == _glyphs(v) and _glyphs(s)
        assert _labels(s) == _labels(v) and len(_labels(s)) == 2
        assert _heads(s) == _heads(v) and len(_heads(s)) == 2
        assert sorted(sw) == sorted(vw)
