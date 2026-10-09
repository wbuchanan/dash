"""A row filter must line up with the rows it is filtering.

Some ``map_*`` methods build their own ``ColumnDataSource`` after dropping
rows with missing values, and then attach the CALLER'S ``view`` to the glyph
call.  The view's ``BooleanFilter`` is sized to the original source; the
rebuilt source is shorter.  Bokeh applies a mask positionally, so it selects
the wrong observations.

The defect was reported against seven named mappers.  Measured, it is a
different seven: three of the named ones keep every row and were never
affected, and three that were not named are.  See ``_AFFECTED`` below.

Measured end to end through ``DashRenderer`` before the fix, on a six-row
frame whose FIRST y is missing and a qualifier selecting the first three
rows::

    rebuilt source : [2.0, 3.0, 4.0, 5.0, 6.0]   (5 rows)
    mask           : [T, T, T, F, F, F]          (6 entries)
    drawn          : [2.0, 3.0, 4.0]
    selected       : [2.0, 3.0]

-- an extra spike from a row the qualifier excluded.  ``auto.dta``'s ``rep78``
has five missing values, so this is reachable with the shipped example data.

This is a sibling of the defect fixed in the previous commit but not the same
one: those fourteen mappers ignored their view entirely, whereas these
consume it and attach it to the wrong thing.

The NaN is placed BEFORE the selected rows in every case here.  That is what
makes a positional mask land on the wrong observations; a NaN after them can
still give the right answer by luck, which is how this survived.
"""
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

from bokeh.models import BooleanFilter, CDSView, ColumnDataSource
from bokeh.plotting import figure

import dash_render as dr
from conftest import make_data_json

# Six observations.  Row 0 is missing, so any rebuilt source is 5 rows while
# a row mask is 6 -- the misalignment this file is about.  The qualifier
# selects rows 0-2, of which only rows 1 and 2 survive the missing value.
_DF = pd.DataFrame({
    "x":  [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
    "y":  [np.nan, 2.0, 3.0, 4.0, 5.0, 6.0],
    "y2": [np.nan, 12.0, 13.0, 14.0, 15.0, 16.0],
    "x2": [11.0, 12.0, 13.0, 14.0, 15.0, 16.0],
    "g":  [1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
})
_QUALIFIER = _DF.g == 1.0
# What the user asked for: g==1 AND not missing -- rows 1 and 2.
_WANTED_X = [2.0, 3.0]
# Every x position that belongs to a row the user did NOT get: the three
# rows g==0 excludes, and row 0 which the missing value drops.  The paired
# layers legitimately draw a SECOND point per observation from x2, so the
# test asks that no EXCLUDED row appear rather than that only _WANTED_X does.
_FORBIDDEN_X = {1.0, 4.0, 5.0, 6.0,        # x of excluded / dropped rows
                11.0, 14.0, 15.0, 16.0}    # x2 of the same rows

# (name, positional varnames after `source`) -- see each signature.
#
# The defect was reported against seven mappers.  Measured, it is a different
# seven.  What matters is not whether a mapper builds its own source but
# whether that source is SHORTER than the one the mask describes:
#
#   REBUILDS A SHORTER SOURCE, so the mask slipped -- the real defect.
#     map_bar, map_spike, map_pcscatter, map_rscatter were reported and are
#     affected.  map_pcspike, map_pcarrow and map_pcbarrow were NOT reported
#     and are affected too: they pass a dropna'd DataFrame straight to
#     ColumnDataSource rather than a dict literal, so the scan that produced
#     the report passed over them.  Each gives a 5-row source against a
#     6-entry mask on the frame below.
#
#   KEEPS EVERY ROW, so the mask lines up and the view is correct.
#     map_rbar, map_rcap and map_rcapsym were reported but are NOT affected.
#     They put the full-length arrays into their source, NaN rows included,
#     and Bokeh simply draws nothing for a segment with a NaN coordinate.
#     Measured: 6-row source against a 6-entry mask, for all nine renderers
#     the three of them produce.  They are kept under test below as a guard
#     that they do not start dropping rows while still attaching the view.
_AFFECTED = [
    ("map_bar",       ("y", "x")),
    ("map_spike",     ("y", "x")),
    ("map_pcscatter", ("y", "x", "y2", "x2")),
    ("map_rscatter",  ("y", "y2", "x")),
    ("map_pcspike",   ("y", "x", "y2", "x2")),
    ("map_pcarrow",   ("y", "x", "y2", "x2")),
    ("map_pcbarrow",  ("y", "x", "y2", "x2")),
    # WP-22: pccapsym rebuilds a shorter source too (the dropna'd spike and
    # its markers), so it masks by the view before any row goes.
    ("map_pccapsym",  ("y", "x", "y2", "x2")),
]

_ALIGNED_ALREADY = [
    ("map_rbar",    ("y", "y2", "x")),
    ("map_rcap",    ("y", "y2", "x")),
    ("map_rcapsym", ("y", "y2", "x")),
]


from conftest import render_models  # noqa: E402


def _source(frame):
    """A ColumnDataSource carrying the row-identity column the views use."""
    data = {c: list(frame[c]) for c in frame.columns}
    data[dr._ROW_ID_COLUMN] = list(range(len(frame)))
    return ColumnDataSource(data)


def _mask_view(frame, condition):
    mask = [bool(v) for v in condition]
    assert len(mask) == len(frame)
    return CDSView(filter=BooleanFilter(booleans=mask))


def _draw(name, varnames, source, view):
    """Call one mapper; return the x values the figure will actually draw.

    A renderer's own view is applied here the way Bokeh applies it -- by
    position against the source the renderer draws from -- so this reports
    what a reader of the page would see, not merely what the source holds.
    """
    mapper = dr.GlyphMapper()
    fig = figure()
    fn = getattr(mapper, name)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = fn(fig, source, *varnames, {}, view=view, color_idx=0)
    renderers = result if isinstance(result, (list, tuple)) else [result]

    drawn = []
    for rend in renderers:
        src = getattr(rend, "data_source", None)
        if src is None:
            continue
        # The column holding the x position differs by glyph.
        for key in ("x0", "x", "left", "xs"):
            if key in src.data:
                xs = [float(v) for v in src.data[key]]
                break
        else:
            continue
        rview = getattr(rend, "view", None)
        bl = getattr(getattr(rview, "filter", None), "booleans", None)
        if bl is not None:
            bl = list(bl)
            xs = [x for x, keep in zip(xs, bl)
                  if keep] if len(bl) >= len(xs) else xs
        drawn.append(sorted(set(xs)))
    return drawn


@pytest.mark.parametrize("name,varnames", _AFFECTED,
                         ids=[n for n, _ in _AFFECTED])
class TestAQualifierSelectsTheRightRows:

    def test_only_the_selected_rows_are_drawn(self, name, varnames):
        """The defect: an excluded row is drawn because the mask slipped."""
        drawn = _draw(name, varnames, _source(_DF),
                      _mask_view(_DF, _QUALIFIER))
        assert drawn, "%s produced no positioned glyph" % name
        for xs in drawn:
            extra = [x for x in xs if x in _FORBIDDEN_X]
            assert not extra, (
                "%s drew %r, which includes %r -- positions belonging to rows "
                "the qualifier excluded or the missing value dropped"
                % (name, xs, extra)
            )

    def test_the_qualified_draw_matches_the_prefiltered_draw(
            self, name, varnames):
        """Correctness: masking must equal handing it only those rows."""
        via_view = _draw(name, varnames, _source(_DF),
                         _mask_view(_DF, _QUALIFIER))
        subset = _DF[_QUALIFIER].reset_index(drop=True)
        via_subset = _draw(name, varnames, _source(subset), None)
        assert via_view == via_subset, (
            "%s: through a view %r, pre-filtered %r"
            % (name, via_view, via_subset)
        )

    def test_no_view_is_unaffected(self, name, varnames):
        """The common case -- no qualifier -- must not move."""
        a = _draw(name, varnames, _source(_DF), None)
        b = _draw(name, varnames, _source(_DF), None)
        assert a == b

    def test_an_all_true_mask_matches_no_view(self, name, varnames):
        none_view = _draw(name, varnames, _source(_DF), None)
        all_true = _draw(name, varnames, _source(_DF),
                         _mask_view(_DF, np.ones(len(_DF), dtype=bool)))
        assert all_true == none_view, (name, all_true, none_view)


class TestTheReproductionFromTheReport:
    """The exact end-to-end case the defect was reported with."""

    def test_spike_through_the_renderer_draws_only_the_selected_rows(
            self, tmp_path):
        data_path = tmp_path / "data.json"
        data_path.write_text(json.dumps(make_data_json(_DF)), encoding="utf-8")
        spec = {
            "graphs": [{
                "plots": [{"type": "spike", "yvar": "y", "xvar": "x",
                           "options": {}, "if_expr": "g==1", "in_expr": ""}],
                "graph_options": {}, "if_expr": "", "in_expr": "",
            }],
            "build_options": {"layout": "1 1", "level": "95", "formats": {}},
        }
        spec_path = tmp_path / "spec.json"
        spec_path.write_text(json.dumps(spec), encoding="utf-8")
        renderer = dr.DashRenderer(str(spec_path), str(data_path))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            render_models(renderer)
        seen = []
        for fig in renderer.figures.values():
            for rend in fig.renderers:
                src = getattr(rend, "data_source", None)
                if src is None or "x0" not in src.data:
                    continue
                xs = [float(v) for v in src.data["x0"]]
                bl = getattr(getattr(getattr(rend, "view", None), "filter",
                                     None), "booleans", None)
                if bl is not None and len(list(bl)) >= len(xs):
                    xs = [x for x, k in zip(xs, list(bl)) if k]
                seen.append(sorted(set(xs)))
        assert seen, "no spike segment was produced"
        for xs in seen:
            assert xs == _WANTED_X, (
                "spike y x if g==1 drew %r; the qualifier selects %r"
                % (xs, _WANTED_X)
            )


class TestTheDoubledLayersStayPaired:
    """``pcscatter`` and ``rscatter`` emit two points per observation.

    A length-N row mask cannot apply to a 2N source directly, and getting the
    order wrong pairs each observation's low value with a different
    observation's high one -- which would look plausible and be wrong.
    """

    @pytest.mark.parametrize("name,varnames", [
        ("map_pcscatter", ("y", "x", "y2", "x2")),
        ("map_rscatter",  ("y", "y2", "x")),
    ])
    def test_both_points_of_each_selected_observation_are_drawn(
            self, name, varnames):
        drawn = _draw(name, varnames, _source(_DF),
                      _mask_view(_DF, _QUALIFIER))
        subset = _DF[_QUALIFIER].reset_index(drop=True)
        expected = _draw(name, varnames, _source(subset), None)
        assert drawn == expected, (name, drawn, expected)


@pytest.mark.parametrize("name,varnames", _ALIGNED_ALREADY,
                         ids=[n for n, _ in _ALIGNED_ALREADY])
class TestTheAlignedLayersStayAligned:
    """These three were reported as affected and are not.

    They kept every row -- missing values included -- in the source they
    built, so a mask sized to the caller's source lined up with it.  Since
    WP-27 they take the other correct design: the layer's rows are taken
    first and the copy is drawn with no view, so the saved page's filter
    script can keep a move's rows of it by row id (BUGS.md, "A filter on a
    saved page leaves line, tsline, area, bar, spike and dropline layers
    ...").  The guard holds either way: a renderer that attaches a view
    must hold one row per flag, and one that attaches none must hold the
    selected rows and no others.
    """

    def test_the_source_is_the_same_length_as_the_mask(self, name, varnames):
        view = _mask_view(_DF, _QUALIFIER)
        mapper = dr.GlyphMapper()
        fig = figure()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = getattr(mapper, name)(fig, _source(_DF), *varnames, {},
                                           view=view, color_idx=0)
        renderers = result if isinstance(result, (list, tuple)) else [result]
        checked = 0
        for rend in renderers:
            src = getattr(rend, "data_source", None)
            if src is None:
                continue
            key = next((k for k in ("x0", "x", "left") if k in src.data), None)
            if key is None:
                continue
            bl = getattr(getattr(getattr(rend, "view", None), "filter", None),
                         "booleans", None)
            checked += 1
            if bl is None:
                # No view: the source must hold the selected rows alone.
                assert len(src.data[key]) == int(_QUALIFIER.sum()), (
                    "%s attaches no view to a %d-row source where the "
                    "qualifier selects %d rows"
                    % (name, len(src.data[key]), int(_QUALIFIER.sum())))
                continue
            assert len(list(bl)) == len(src.data[key]), (
                "%s attaches a %d-entry mask to a %d-row source; it must "
                "either keep every row or mask its input and detach the view"
                % (name, len(list(bl)), len(src.data[key]))
            )
        assert checked, "%s drew no renderer to assert about" % name


# Rows spaced 10 apart in the selected group, 1 apart in the excluded one, so
# a width derived from the wrong rows is off by an order of magnitude and
# plainly visible rather than a rounding difference.
_SPACED = pd.DataFrame({
    "x":  [0.0, 10.0, 20.0, 30.0, 31.0, 32.0],
    "y":  [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
    "y2": [2.0, 3.0, 4.0, 5.0, 6.0, 7.0],
    "g":  [1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
})
_SPACED_QUALIFIER = _SPACED.g == 1.0


def _bar_width(name, varnames, source, view):
    """The bar width, or the cap's or end marker's size, the mapper draws.

    Flipped (WP-30 P1.17a): rcap's caps and rcapsym's markers are Scatters
    whose size is read, because twoway draws a bar one x unit wide and caps
    as long as a marker of its msize (P1.17a).
    """
    mapper = dr.GlyphMapper()
    fig = figure()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = getattr(mapper, name)(fig, source, *varnames, {},
                                       view=view, color_idx=0)
    renderers = result if isinstance(result, (list, tuple)) else [result]
    for rend in renderers:
        glyph = getattr(rend, "glyph", None)
        width = getattr(glyph, "width", None)
        if isinstance(width, (int, float)):
            return round(float(width), 6)
        size = getattr(glyph, "size", None)
        if type(glyph).__name__ == "Scatter" and isinstance(size, (int, float)):
            return round(float(size), 6)
        src = getattr(rend, "data_source", None)
        if src is None:
            continue
        cap = next((k for k in src.data if k.endswith("x0_cap")), None)
        if cap is not None:
            xcol = "x" if "x" in src.data else None
            if xcol is None:
                continue
            x = np.asarray(src.data[xcol], dtype=float)
            x0 = np.asarray(src.data[cap], dtype=float)
            return round(float(np.nanmax(np.abs(x - x0))), 6)
    return None


class TestADerivedWidthComesFromTheRowsDrawn:
    """No bar width or cap is derived from the rows any more (WP-30 P1.17a):
    a bar is one x unit wide and a cap is a marker of its msize(), so a
    qualifier never changes one.  These four once sized their glyphs from
    the spacing of the x values, three of them from the WHOLE column while
    drawing only the selected rows (0.8 where the subset alone gave 8.0).

    map_rbar, map_rcap and map_rcapsym do not have the stale-mask defect the
    rest of this file is about: their sources keep every row, so the mask
    lines up.  This is the other half of "honour the rows you were given".
    """

    @pytest.mark.parametrize("name,varnames", [
        ("map_bar",     ("y", "x")),
        ("map_rbar",    ("y", "y2", "x")),
        ("map_rcap",    ("y", "y2", "x")),
        ("map_rcapsym", ("y", "y2", "x")),
    ])
    def test_the_width_matches_the_prefiltered_width(self, name, varnames):
        via_view = _bar_width(name, varnames, _source(_SPACED),
                              _mask_view(_SPACED, _SPACED_QUALIFIER))
        subset = _SPACED[_SPACED_QUALIFIER].reset_index(drop=True)
        via_subset = _bar_width(name, varnames, _source(subset), None)
        assert via_view is not None, "%s exposed no width to check" % name
        assert via_view == via_subset, (
            "%s sized its glyphs %r through a qualifier but %r when handed "
            "the same rows directly -- the width came from rows that are not "
            "drawn" % (name, via_view, via_subset)
        )
