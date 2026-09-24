"""A line-like glyph must be drawn in x order, not in dataset order.

Bokeh's ``line`` and ``varea`` connect their points in the order the
ColumnDataSource gives them. Stata's ``twoway line`` and ``twoway area`` draw
along x. So a mapper that hands over unsorted rows draws a shape that crosses
itself — the classic "scribble" plot — and it does so silently, because every
point is present and correct.

``map_line`` and ``map_connected`` sort. ``map_area`` did not. Measured on
x = [3, 1, 2]:

    map_line       x order: [1.0, 2.0, 3.0]
    map_connected  x order: [1.0, 2.0, 3.0]
    map_area       x order: [3.0, 1.0, 2.0]

The saved dashboard therefore drew a self-intersecting polygon for
``dash area y x`` on any dataset not already sorted by x. It was found while
comparing the two render modes for WP-09: the generated server app sorts in
its own inline area branch, so this is one of the places where the two
disagreed and the SERVER was right.

The tests below are about ordering only. What the glyph is filled with, and
which rows survive a qualifier, are other files' business.
"""
from __future__ import annotations

import os
import sys
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

from bokeh.models import ColumnDataSource
from bokeh.plotting import figure

import dash_render as dr

#: Deliberately not sorted, and not sorted by y either, so a mapper cannot
#: pass by accident.
_X = [3.0, 1.0, 2.0, 5.0, 4.0]
_Y = [9.0, 1.0, 4.0, 25.0, 16.0]

#: Every mapper that draws a path or a filled region along x.
_PATH_MAPPERS = ["map_line", "map_connected", "map_area"]

#: The range equivalents. A range plot names two y variables, so these take a
#: different call shape -- but the invariant is the same, and only for the
#: ones that draw a PATH or a BAND. ``rcap``, ``rspike``, ``rbar`` and
#: ``rcapsym`` draw one independent mark per row, so their order is invisible
#: and they are deliberately not listed.
_RANGE_PATH_MAPPERS = ["map_rline", "map_rarea", "map_rconnected",
                       "map_tsrline"]

_RX = [3.0, 1.0, 2.0, 5.0, 4.0]
_RY1 = [1.0, 2.0, 3.0, 4.0, 5.0]
_RY2 = [2.0, 3.0, 4.0, 5.0, 6.0]


def _range_source():
    return ColumnDataSource({
        "x": list(_RX), "y1": list(_RY1), "y2": list(_RY2),
        dr._ROW_ID_COLUMN: list(range(len(_RX))),
    })


def _range_drawn_x(name):
    """The x values a range mapper handed to Bokeh, in order."""
    mapper = dr.GlyphMapper()
    fig = figure()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = getattr(mapper, name)(fig, _range_source(), "y1", "y2", "x",
                                       {}, view=None, color_idx=0)
    renderers = result if isinstance(result, (list, tuple)) else [result]
    for rend in renderers:
        data = getattr(getattr(rend, "data_source", None), "data", {})
        for key, vals in data.items():
            if key.startswith("x") and len(vals) == len(_RX):
                return [float(v) for v in vals]
    raise AssertionError("%s produced no x column" % name)


def _source():
    return ColumnDataSource({
        "x": list(_X),
        "y": list(_Y),
        dr._ROW_ID_COLUMN: list(range(len(_X))),
    })


def _drawn_x(name):
    """The x values the mapper handed to Bokeh, in the order it handed them."""
    mapper = dr.GlyphMapper()
    fig = figure()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = getattr(mapper, name)(fig, _source(), "y", "x", {},
                                       view=None, color_idx=0)
    renderers = result if isinstance(result, (list, tuple)) else [result]
    for rend in renderers:
        data = getattr(getattr(rend, "data_source", None), "data", {})
        for key in ("x", "x_ar", "x_area"):
            if key in data and len(data[key]):
                return [float(v) for v in data[key]]
    raise AssertionError("%s produced no x column: %r" % (name, renderers))


@pytest.mark.parametrize("name", _PATH_MAPPERS)
def test_the_glyph_is_drawn_in_x_order(name):
    """The invariant. map_area failed this; the other two always passed."""
    got = _drawn_x(name)
    assert got == sorted(got), (
        "%s drew its points in dataset order %r; Bokeh joins points in the "
        "order they are given, so this is a self-intersecting shape where "
        "Stata draws a clean one" % (name, got)
    )


@pytest.mark.parametrize("name", _PATH_MAPPERS)
def test_no_row_is_lost_or_invented_by_the_sort(name):
    """Sorting must reorder the rows, not filter them."""
    got = _drawn_x(name)
    assert sorted(got) == sorted(_X), (
        "%s changed which rows are drawn: got %r, expected the same multiset "
        "as %r" % (name, got, _X)
    )


@pytest.mark.parametrize("name", _PATH_MAPPERS)
def test_the_pairing_of_x_and_y_survives_the_sort(name):
    """The point (3, 9) must still be the point (3, 9) afterwards.

    Sorting one column and not the other is the way this kind of fix goes
    wrong, and it is invisible in a plot of y = x**2 unless you look.
    """
    mapper = dr.GlyphMapper()
    fig = figure()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = getattr(mapper, name)(fig, _source(), "y", "x", {},
                                       view=None, color_idx=0)
    renderers = result if isinstance(result, (list, tuple)) else [result]
    expected = dict(zip(_X, _Y))
    for rend in renderers:
        data = getattr(getattr(rend, "data_source", None), "data", {})
        xkey = next((k for k in ("x", "x_ar", "x_area") if k in data), None)
        if xkey is None or not len(data[xkey]):
            continue
        ykey = next((k for k in ("y", "y_ar", "y_area", "y2") if k in data
                     and k != xkey), None)
        if ykey is None:
            continue
        for xv, yv in zip(data[xkey], data[ykey]):
            assert expected[float(xv)] == pytest.approx(float(yv)), (
                "%s paired x=%s with y=%s; it should be %s"
                % (name, xv, yv, expected[float(xv)])
            )
        return
    raise AssertionError("%s produced no comparable x/y columns" % name)


@pytest.mark.parametrize("name", _RANGE_PATH_MAPPERS)
def test_a_range_path_is_drawn_in_x_order(name):
    """The same invariant, for the range plots that draw a path or a band.

    ``map_rconnected`` sorted; ``map_rline``, ``map_rarea`` and
    ``map_tsrline`` did not. Measured on x = [3, 1, 2, 5, 4], each of the
    three returned that order unchanged -- so ``dash rline y1 y2 x`` drew two
    self-crossing boundaries and ``dash rarea`` filled the region between
    them, which is a shape with no relation to the data.

    Found the same way as the ``map_area`` case above: the generated server
    app sorts in its own inline branch for these types, so this is a place
    where the two render modes disagreed and the SERVER was right.
    """
    got = _range_drawn_x(name)
    assert got == sorted(got), (
        "%s drew its points in dataset order %r; a path or band joined in "
        "that order crosses itself" % (name, got)
    )


@pytest.mark.parametrize("name", _RANGE_PATH_MAPPERS)
def test_a_range_path_keeps_every_row(name):
    got = _range_drawn_x(name)
    assert sorted(got) == sorted(_RX), (
        "%s changed which rows are drawn: %r" % (name, got)
    )


@pytest.mark.parametrize("name", _RANGE_PATH_MAPPERS)
def test_a_range_path_keeps_its_pairing(name):
    """y1 and y2 must follow x through the sort, or the band inverts."""
    mapper = dr.GlyphMapper()
    fig = figure()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = getattr(mapper, name)(fig, _range_source(), "y1", "y2", "x",
                                       {}, view=None, color_idx=0)
    renderers = result if isinstance(result, (list, tuple)) else [result]
    want1 = dict(zip(_RX, _RY1))
    want2 = dict(zip(_RX, _RY2))
    # Every renderer, and both bounds.  This returned after the first
    # renderer that held either bound -- map_rconnected draws y1 and y2 as
    # separate lines, so its y2 line was never read (measured 24sep2026) --
    # and SKIPPED a mapper whose columns it could not find, which is the
    # one case where the pairing is not checked at all.  No other test
    # checks range pairing.
    checked = set()
    for rend in renderers:
        data = getattr(getattr(rend, "data_source", None), "data", {})
        xkey = next((k for k in data if k.startswith("x")
                     and len(data[k]) == len(_RX)), None)
        if xkey is None:
            continue
        for ykey, want in (("y1", want1), ("y2", want2)):
            col = next((k for k in data if k.startswith(ykey)
                        and len(data[k]) == len(_RX)), None)
            if col is None:
                continue
            for xv, yv in zip(data[xkey], data[col]):
                assert want[float(xv)] == pytest.approx(float(yv)), (
                    "%s paired x=%s with %s=%s; expected %s"
                    % (name, xv, ykey, yv, want[float(xv)])
                )
            checked.add(ykey)
    if checked != {"y1", "y2"}:
        pytest.fail("%s exposes no comparable x/%s columns"
                    % (name, "/".join(sorted({"y1", "y2"} - checked))))


# ==========================================================================
# A layer that could not be computed must still carry the user's styling
# ==========================================================================

#: Mappers that compute a curve and fall back to an empty renderer when they
#: cannot -- too few points, an x that does not vary.
_DEGRADING_MAPPERS = ["map_lowess", "map_lpoly", "map_mspline", "map_mband",
                      "map_lfit", "map_qfit", "map_fpfit"]


def _degenerate_source():
    """x does not vary, so every smoother and fit takes its bail-out path."""
    return ColumnDataSource({
        "x": [1.0, 1.0, 1.0],
        "y": [1.0, 2.0, 3.0],
        dr._ROW_ID_COLUMN: [0, 1, 2],
    })


@pytest.mark.parametrize("name", _DEGRADING_MAPPERS)
def test_a_degraded_layer_still_applies_lwidth(name):
    """The empty renderer must be styled like the real one.

    Each of these returns an empty ColumnDataSource when it cannot compute
    its curve, and several returned it WITHOUT applying the plot's line
    options -- so ``lwidth(thick)`` was silently dropped for that layer.
    Measured with a constant x, which makes every one of them bail:

        map_lowess   line_width 1    (should be 2.5)
        map_mspline  line_width 1    (should be 2.5)
        map_mband    line_width 1    (should be 2.5)
        map_fpfit    line_width 1    (should be 2.5)
        map_lpoly, map_lfit, map_qfit  2.5   -- already correct

    It mattered beyond tidiness while ``statsmodels`` was an OPTIONAL
    dependency of lowess (until WP-18): on a machine without it EVERY
    lowess layer took this path. The generated server app applied the
    width regardless, which is how
    ``test_server.py::TestServerLineWidthAllTypes::test_lowess_applies_lwidth``
    caught this the moment lowess started going through the mapper.
    """
    mapper = dr.GlyphMapper()
    fig = figure()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = getattr(mapper, name)(fig, _degenerate_source(), "y", "x",
                                       {"lwidth": "thick"}, view=None,
                                       color_idx=0)
    renderers = result if isinstance(result, (list, tuple)) else [result]
    widths = [getattr(getattr(r, "glyph", None), "line_width", None)
              for r in renderers if r is not None]
    assert any(w == pytest.approx(2.5) for w in widths), (
        "%s dropped lwidth(thick) on its bail-out path; got %r. A layer that "
        "could not be computed is still the user's layer." % (name, widths)
    )
