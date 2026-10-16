"""WP-31 S45 (D1d): an outer axis's ##N minor labels after a filter move
are not capped at its build's label pool.

A far-side or outer axis draws its ##N labels from a pool of Labels made
at the first finish (WP-31 D1b), which the saved page cannot add to after
load.  S35 sized it ``2 * n_build + 2 * max(N - 1, 1) + 4``: on a y2 over
544.565 to 1492.149 with ``ylabel(#8, axis(2)) ymlabel(##10, axis(2))`` a
move to 579.199 to 1015.518 needs more labels than that (twoway's ##N rule,
measured by S24: test/fixtures/minor_ticks_truth.json, draws every one).
The pool is now sized by the rule's bound over any scale the axis can take
(:func:`dash_render._dash_minor_pool_size`): at most n + 1 majors (natscale's
largest count), N positions an interval, the scale's margin either side.

While iterating: ``python3 -m pytest test/test_minor_label_pool_d1d.py -q``.
"""
import math
import os
import random
import sys
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import js_runner  # noqa: E402
import test_default_axes as tda  # noqa: E402
from test_axisn_minor import _minor_labels  # noqa: E402
from test_date_range import _filter, _saved, _served, _spec  # noqa: E402
from test_date_axis_residuals import _L  # noqa: E402

MODES = ("saved", "served")
_LO, _HI = 544.565209100813, 1492.1494388394729
_KEPT = (579.1993581170549, 1015.5177101036923)


def _frame():
    z = np.linspace(_LO, _HI, 60)
    z = np.unique(np.r_[z, list(_KEPT)])
    n = len(z)
    return pd.DataFrame({"obs": np.arange(n, dtype=float),
                         "a": np.linspace(10.0, 40.0, n),
                         "z": z, "zv": z})


_DF = _frame()
_GO = {"ylabel2": "#8", "ymlabel2": "##10"}
_FMT = {"obs": "%9.0g", "a": "%9.0g", "z": "%9.0g", "zv": "%9.0g"}


def _figs(tmp_path, mode, df=_DF, filt="zv", move=None):
    spec = _spec([_L("scatter", "a", "obs"),
                  _L("scatter", "z", "obs", yaxis="2")], formats=_FMT,
                 graph_options=dict(_GO),
                 filters=[_filter("range", filt)] if filt else None)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if mode == "saved":
            r, _w = _saved(tmp_path, spec, df)
            figs = list(r.figures.values())
            if move is not None:
                figs = tda._move_saved(r, "RangeSlider", move)
        else:
            doc, _w = _served(tmp_path, spec, df)
            figs = tda.tb._panels(tda.tb._figs_of(doc.roots))
            if move is not None:
                figs = tda._move_served(doc, "RangeSlider", move)
    return [f for f in figs if f.renderers][0]


class TestThePoolSize:
    def test_bound_holds_over_any_scale(self):
        """No scale the axis can take (natscale's majors over any range,
        its margin either side) places more ##N labels than the pool."""
        rnd = random.Random(45)
        for _ in range(20000):
            n = rnd.choice([1, 2, 3, 5, 8, 12, 20, 30])
            N = rnd.choice([2, 3, 5, 10, 20, 50])
            lo = rnd.uniform(-1000, 1000)
            hi = lo + 10 ** rnd.uniform(-2, 5)
            m = dr._dash_natscale_ticks(lo, hi, n)
            if not m or len(m) < 2:
                continue
            f = rnd.uniform(0.0, 0.3)
            pad = f / (1 - 2 * f)
            s0, s1 = min(m[0], lo), max(m[-1], hi)
            span = s1 - s0
            got = len(dr._dash_minor_between(
                dr._dash_minor_rule(m, ()), N, s0 - pad * span,
                s1 + pad * span, True, None))
            assert got <= dr._dash_minor_pool_size(0, N, n, (f, f)), \
                (n, N, lo, hi, f, got)

    def test_without_a_count(self):
        """An axis with no #N keeps S35's size; the tick cap bounds all."""
        assert dr._dash_minor_pool_size(7, 5, None, None) == 2 * 7 + 8 + 4
        assert dr._dash_minor_pool_size(0, 5, 10 ** 6, (0.4, 0.4)) == \
            dr._MAX_AXIS_TICKS + 1


class TestAMoveToTheLargestCount:
    @pytest.mark.parametrize("mode", MODES)
    def test_every_label_is_drawn(self, tmp_path, mode):
        """After the move the outer axis draws the labels the kept rows'
        own build draws."""
        (tmp_path / "a").mkdir()
        (tmp_path / "k").mkdir()
        after = _figs(tmp_path / "a", mode, move=_KEPT)
        kept_df = _DF[(_DF["zv"] >= _KEPT[0]) & (_DF["zv"] <= _KEPT[1])]
        kept = _figs(tmp_path / "k", mode, df=kept_df.reset_index(
            drop=True), filt=None)
        a = _minor_labels(after, "y", 2)
        k = _minor_labels(kept, "y", 2)
        assert len(a) == len(k) and np.allclose(a, k), (len(a), len(k))
