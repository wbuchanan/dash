"""`lpolyci` and `lpoly` used different smoothers for the same options.

S07 rewrote `map_lpoly` to Stata's semantics: ``bwidth()`` is an **absolute**
bandwidth in x-units, defaulting to Stata's data-driven rule when it is
absent; ``degree()`` is 0-3; ``kernel()`` selects from ``_KERNELS`` and
defaults to epanechnikov.

`map_lpolyci` was left on the pre-S07 code::

    bwidth = max(0.01, min(1.0, float(options.get("bwidth", "0.5"))))

a **fraction** clamped to [0.01, 1.0], with no kernel lookup at all. So

    twoway lpoly   mpg weight, bwidth(500)
    twoway lpolyci mpg weight, bwidth(500)

asked for the same smoother and got two different ones — the second clamped
500 to 1.0 — and ``kernel(gaussian)`` on `lpolyci` was read by nothing. Both
silently: the curve is drawn, it is just not the curve that was requested,
and the confidence band is computed around the wrong curve.

The bootstrap resamples must use the same smoother as the point estimate, or
the band is not a band around the line that is drawn.
"""
import os
import sys

import numpy as np
import pytest
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
from bokeh.models import ColumnDataSource

_RNG = np.random.default_rng(20260920)
_X = np.linspace(1000.0, 5000.0, 60)
_Y = 40.0 - 0.005 * _X + _RNG.normal(0, 1.5, _X.size)

# 1% of the fixture's y-range. See the docstring on
# test_the_fitted_line_matches_lpoly_for_the_same_options for why.
_TOL = 0.01 * float(_Y.max() - _Y.min())


def _src():
    return ColumnDataSource({"weight": _X.tolist(), "mpg": _Y.tolist()})


def _fit_of(mapper_name, options):
    """The fitted line a mapper produces, as (x, y) arrays.

    Both mappers name the columns x_lp/y_lp; lpolyci's source carries the
    band's y_lower/y_upper alongside them.
    """
    gm = dr.GlyphMapper(scheme=dr.SchemeParser("s2color"))
    fig = figure()
    getattr(gm, mapper_name)(fig, _src(), "mpg", "weight", dict(options))
    for r in fig.renderers:
        d = r.data_source.data
        if "x_lp" in d and "y_lp" in d and len(d["x_lp"]) > 2:
            return np.asarray(d["x_lp"], float), np.asarray(d["y_lp"], float)
    raise AssertionError(f"{mapper_name} produced no fitted line")


class TestLpolyciUsesTheSameSmootherAsLpoly:
    def test_an_absolute_bandwidth_is_not_clamped_to_one(self):
        """bwidth() is in x-units; 500 must not become 1.0."""
        _, wide = _fit_of("map_lpolyci", {"bwidth": "1500"})
        _, narrow = _fit_of("map_lpolyci", {"bwidth": "200"})
        assert not np.allclose(wide, narrow, equal_nan=True), (
            "bwidth() changed nothing — it is still being clamped to [0.01, 1]"
        )

    @pytest.mark.parametrize("opts", [
        {"bwidth": "800"},
        {"bwidth": "800", "degree": "1"},
        {"bwidth": "600", "kernel": "gaussian"},
    ])
    def test_the_fitted_line_matches_lpoly_for_the_same_options(self, opts):
        """Equal to within grid resolution, which is the one legitimate gap.

        lpolyci evaluates on 100 points and lpoly on 200, for bootstrap
        speed, so interpolating one onto the other leaves a small residual.
        Measured on this fixture (y-range 21.4): with the bug the two curves
        differed by 1.5 to 5.4; with the same smoother they differ by at most
        0.03. _TOL is 1% of the range — an order of magnitude clear of both.
        """
        xa, ya = _fit_of("map_lpoly", opts)
        xb, yb = _fit_of("map_lpolyci", opts)
        worst = float(np.nanmax(np.abs(np.interp(xb, xa, ya) - yb)))
        assert worst <= _TOL, (
            f"lpoly and lpolyci disagree by {worst:.3f} for {opts} "
            f"(tolerance {_TOL:.3f}) — they are not using the same smoother"
        )

    def test_the_kernel_is_honoured(self):
        _, epan = _fit_of("map_lpolyci", {"bwidth": "600",
                                          "kernel": "epanechnikov"})
        _, gauss = _fit_of("map_lpolyci", {"bwidth": "600",
                                           "kernel": "gaussian"})
        assert not np.allclose(epan, gauss, equal_nan=True), (
            "kernel() is read by nothing in lpolyci"
        )

    def test_an_unknown_kernel_warns_rather_than_being_ignored(self):
        with pytest.warns(UserWarning, match="kernel"):
            _fit_of("map_lpolyci", {"bwidth": "600", "kernel": "no_such"})

    def test_a_non_positive_bandwidth_warns_and_falls_back(self):
        with pytest.warns(UserWarning, match="bwidth"):
            _fit_of("map_lpolyci", {"bwidth": "0"})

    def test_no_bwidth_uses_statas_rule_not_a_hardcoded_half(self):
        """The old default was the literal 0.5, which is not Stata's."""
        # bwidth(0.5) is now 0.5 x-UNITS, and x spans 1000-5000 in steps of
        # about 68, so no window holds two observations.  lpoly leaves a
        # grid point missing below two positive-weight observations (WP-18,
        # measured), so the curve vanishes: nothing is drawn.  Under the
        # old code 0.5 was a fraction of the range and gave a full curve --
        # which is exactly the semantics that had to change.
        _, auto = _fit_of("map_lpolyci", {})
        gm = dr.GlyphMapper(scheme=dr.SchemeParser("s2color"))
        fig = figure()
        gm.map_lpolyci(fig, _src(), "mpg", "weight", {"bwidth": "0.5"})
        drawn = [np.asarray(r.data_source.data["y_lp"], float)
                 for r in fig.renderers if "y_lp" in r.data_source.data]
        assert drawn, "map_lpolyci drew no line renderer at all"
        assert len(auto) > 2
        assert all(int(np.isfinite(y).sum()) == 0 for y in drawn), (
            "bwidth(0.5) still behaves like a fraction of the x-range"
        )
        xa, ya = _fit_of("map_lpoly", {})
        xb, yb = _fit_of("map_lpolyci", {})
        worst = float(np.nanmax(np.abs(np.interp(xb, xa, ya) - yb)))
        assert worst <= _TOL, (
            f"with no bwidth() the two mappers differ by {worst:.3f}; "
            f"lpolyci is not using Stata's rule"
        )


class TestTheBandSurroundsTheLineThatIsDrawn:
    def test_the_ci_brackets_the_fit(self):
        gm = dr.GlyphMapper(scheme=dr.SchemeParser("s2color"))
        fig = figure()
        gm.map_lpolyci(fig, _src(), "mpg", "weight", {"bwidth": "800"})
        band = None
        for r in fig.renderers:
            d = r.data_source.data
            if {"x_lp", "y_lower", "y_upper", "y_lp"} <= set(d):
                band = d
        assert band is not None
        lo = np.asarray(band["y_lower"], float)
        hi = np.asarray(band["y_upper"], float)
        y = np.asarray(band["y_lp"], float)
        ok = ~(np.isnan(lo) | np.isnan(hi) | np.isnan(y))
        assert ok.sum() > 10
        assert np.all(lo[ok] - 1e-9 <= y[ok]) and np.all(y[ok] <= hi[ok] + 1e-9)
