"""`bin(#)` used to sometimes draw #+1 bars, the last an infinite spike.

``_histogram_grid`` built the edges as ``start + width * arange(n+1)`` and
then guarded against losing the top observations::

    if edges[-1] < a_max:
        edges = np.append(edges, a_max)

When ``width`` was derived as ``span / n_bins``, ``edges[-1]`` *is* ``a_max``
in exact arithmetic — but in floating point it can land a few ulps below it.
The guard then fired and appended a bin of width ~1e-14.

**Measured** on a 74-observation fixture, ``bin(6)`` and ``bin(12)``:

    bin( 6) -> 7 bars   min_width=7.105e-15   max density = 1.902e+12
    bin(12) -> 13 bars  min_width=7.105e-15   max density = 1.902e+12

A density is count / (total x width), so a 1e-14-wide bin holding one
observation was a spike twelve orders of magnitude above every real bar, with
every other bar then drawn at visually zero height.

**WP-28 C2 removed the tolerance edge altogether.**  GAPS2 found the SAME
root cause on the other side: a value a few ULPs ABOVE ``edges[-1]`` (not
appended here, genuinely past it) fell outside NumPy's histogram bins and
was silently dropped -- 2245 of 2246 rows on nlsw88 ttl_exp ``bin(27)``, 49
of 50 on census pop ``bin(75)``.  The fix is not a better tolerance on the
old guard; it is Stata's own counting rule
(twoway__histogram_gen.ado:200-203), applied to the continuous grid the way
it already was to the discrete one: every observation is bar
``floor((v - start)/width)``, an index below 0 folded into bar 0 and one at
or past the last edge folded into the LAST bar, through
``GlyphMapper._histogram_counts``.  ``bin(#)`` therefore gives exactly #
bars by construction -- the grid is never widened to keep the top
observation, because the last bar simply claims anything at or beyond its
edge.  The spike this file measured cannot recur: there is no code path
left that appends an extra edge.
"""
import os
import sys
import warnings

import numpy as np
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr

_RNG = np.random.default_rng(19780101)
_W = np.linspace(1760.0, 4840.0, 74)
_M = 40.0 - 0.0055 * _W + _RNG.normal(0.0, 1.8, 74)


def _grid(options, arr=None):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return dr.GlyphMapper._histogram_grid(
            _M if arr is None else arr, options)


class TestBinCountIsWhatWasAsked:
    @pytest.mark.parametrize("n", [2, 3, 4, 5, 6, 7, 8, 10, 12, 15, 20, 33])
    def test_bin_n_gives_exactly_n_bars(self, n):
        edges, _ = _grid({"bin": str(n)})
        assert len(edges) - 1 == n, (
            f"bin({n}) produced {len(edges) - 1} bars"
        )

    @pytest.mark.parametrize("n", [6, 12])
    def test_no_bar_is_a_degenerate_spike(self, n):
        """The two counts that reproduced it."""
        edges, ymode = _grid({"bin": str(n)})
        widths = np.diff(edges)
        span = float(edges[-1] - edges[0])
        assert widths.min() > span * 1e-6, (
            f"bin({n}) produced a bar of width {widths.min():.3e} in a span "
            f"of {span:.3f}"
        )
        counts, _ = np.histogram(_M, bins=edges)
        tops = dr._histogram_heights(counts, edges, ymode)
        assert float(np.max(tops)) < 10.0, (
            f"a density of {float(np.max(tops)):.3e} is a spike, not a bar"
        )

    @pytest.mark.parametrize("seed", range(12))
    def test_it_does_not_come_back_on_other_data(self, seed):
        rng = np.random.default_rng(seed)
        arr = rng.normal(100.0, 15.0, 200)
        for n in range(2, 25):
            edges, _ = _grid({"bin": str(n)}, arr)
            assert len(edges) - 1 == n, f"seed {seed}, bin({n})"


def _frequency_sum(arr, options):
    """Every observation this section's mapper draws, through
    GlyphMapper.map_histogram -- the production path, not a private copy
    of its rule."""
    from bokeh.models import ColumnDataSource
    from bokeh.plotting import figure
    mapper = dr.GlyphMapper(dr.OptionTranslator(), dr.SchemeParser("s2color"))
    src = ColumnDataSource({"v": [float(v) for v in arr]})
    opts = dict(options, frequency="frequency")
    r = mapper.map_histogram(figure(), src, "v", opts)
    d = r.data_source.data
    return (np.asarray(d["top"], dtype=float), np.asarray(d["left"], dtype=float),
            np.asarray(d["right"], dtype=float))


class TestEveryObservationIsCounted:
    """WP-28 C2: the tolerance edge this file measured is gone; every
    observation is counted through GlyphMapper._histogram_counts instead,
    so none is dropped whether the grid's last edge lands a few ULPs
    below, on, or above the sample maximum."""

    def test_an_explicit_width_that_stops_short_still_covers_the_data(self):
        """An explicit start()/width() genuinely can leave the top
        observation past the grid's derived edge; it folds into the last
        bar (GlyphMapper._histogram_counts) rather than needing an
        appended one."""
        arr = np.array([0.0, 1.0, 2.0, 3.0, 9.7])
        tops, _left, _right = _frequency_sum(arr, {"start": "0", "width": "3"})
        assert int(tops.sum()) == len(arr), "an observation was dropped"

    def test_width_alone_still_covers_the_data(self):
        arr = np.array([2.0, 4.0, 6.0, 8.0, 11.5])
        tops, _, _ = _frequency_sum(arr, {"width": "3"})
        assert int(tops.sum()) == len(arr)

    def test_the_default_rule_is_unaffected(self):
        edges, _ = _grid({})
        assert len(edges) - 1 == dr._stata_bin_count(len(_M))
