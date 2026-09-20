"""`bin(#)` sometimes drew #+1 bars, the last an infinite spike.

``_histogram_grid`` builds the edges as ``start + width * arange(n+1)`` and
then guards against losing the top observations::

    if edges[-1] < a_max:
        edges = np.append(edges, a_max)

When ``width`` was derived as ``span / n_bins``, ``edges[-1]`` *is* ``a_max``
in exact arithmetic — but in floating point it can land a few ulps below it.
The guard then fires and appends a bin of width ~1e-14.

**Measured** on a 74-observation fixture, ``bin(6)`` and ``bin(12)``:

    bin( 6) -> 7 bars   min_width=7.105e-15   max density = 1.902e+12
    bin(12) -> 13 bars  min_width=7.105e-15   max density = 1.902e+12

A density is count / (total x width), so a 1e-14-wide bin holding one
observation is a spike twelve orders of magnitude above every real bar. Every
other bar is then drawn at visually zero height. It is data-dependent, so it
strikes some datasets and not others, and the bar count silently disagrees
with what the user asked for.

The guard is still needed — an explicit ``start()``/``width()`` genuinely can
stop short of the data — so it is kept, with a tolerance.
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


class TestTheGuardStillGuards:
    def test_an_explicit_width_that_stops_short_still_covers_the_data(self):
        """width() chosen so the grid genuinely ends below the maximum."""
        arr = np.array([0.0, 1.0, 2.0, 3.0, 9.7])
        edges, _ = _grid({"start": "0", "width": "3"}, arr)
        assert float(edges[-1]) >= float(arr.max()), (
            "the top observation would fall outside every bin"
        )
        counts, _ = np.histogram(arr, bins=edges)
        assert int(counts.sum()) == len(arr), "an observation was dropped"

    def test_width_alone_still_covers_the_data(self):
        arr = np.array([2.0, 4.0, 6.0, 8.0, 11.5])
        edges, _ = _grid({"width": "3"}, arr)
        counts, _ = np.histogram(arr, bins=edges)
        assert int(counts.sum()) == len(arr)

    def test_the_default_rule_is_unaffected(self):
        edges, _ = _grid({})
        assert len(edges) - 1 == dr._stata_bin_count(len(_M))
