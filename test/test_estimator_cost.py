"""test_estimator_cost.py -- lowess and fpfit cost less and draw the same
values (BUGS.md, S3 batch: "lowess and fpfit cost more than they need to on
large data, and a served filter move reruns them unthrottled").

The served throttle is WP-19's (test_served_throttle.py).  What this file
holds is the estimators' own cost:

* ``GlyphMapper._stata_lowess`` stays O(N x window), its definition, but no
  longer runs two libm ``pow()`` calls per window element, allocates a
  fresh array per step, or hands each window's sums to OpenBLAS's thread
  pool through ``np.dot``.  Its values are held to the old loop, kept here
  verbatim as the oracle, within 1e-12 of the size of what is drawn, with
  the missing values in the same places, on the four datasets of
  fixtures/stat_truth.json and on random data of several sizes; the
  fixture's Stata curves are held by test_statistical_truth.py.
* ``GlyphMapper._fp_fit`` screens the 36 power pairs through their 2x2
  normal equations and fits in full only the ones that could win, so the
  fit it returns is the old search's own, bit for bit.

Timings measured 24sep2026 on a 12-core machine under a load average of
50 to 180 (other sessions): lowess on 1e4 rows 1.21 s before, 0.35 s after;
on 1e5 rows 27 s after (BUGS.md measured 116 s before, Stata 22 s); fpfit
0.04 -> 0.004 s on 1e4 rows, 1.45 -> 0.04 s on 1e5, 14.8 -> 0.53 s on 1e6,
the same coefficients bit for bit.  The bounds below are generous on
purpose.
"""
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import js_runner  # noqa: E402
from dash_render import GlyphMapper as GM  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "stat_truth.json")
_DATA_DIR = os.path.join(_HERE, "fixtures", "data")


# ----------------------------------------------------------------------
# The oracles: the code before the S3 batch, verbatim.
# ----------------------------------------------------------------------

def _old_lowess(x, y, bw=0.8, mean=False, noweight=False):
    order = np.argsort(x, kind="stable")
    xs = np.asarray(x, dtype=float)[order]
    ys = np.asarray(y, dtype=float)[order]
    n = len(xs)
    k = int((n * bw - 0.5) / 2.0)
    out = np.empty(n)
    for i in range(n):
        lo, hi = max(0, i - k), min(n - 1, i + k)
        xi = xs[lo:hi + 1]
        yi = ys[lo:hi + 1]
        d = np.abs(xi - xs[i])
        delta = 1.0001 * float(d.max())
        if noweight or delta == 0.0:
            w = np.ones_like(xi)
        else:
            w = (1.0 - (d / delta) ** 3) ** 3
        sw = float(w.sum())
        ym = float(np.dot(w, yi)) / sw
        if mean:
            out[i] = ym
            continue
        xm = float(np.dot(w, xi)) / sw
        sxx = float(np.dot(w, (xi - xm) ** 2))
        if sxx <= 0.0:
            out[i] = np.nan
        else:
            b = float(np.dot(w, (xi - xm) * (yi - ym))) / sxx
            out[i] = ym + b * (xs[i] - xm)
    return xs, out


def _old_fp_fit(x, y, w=None, wtype=None):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(y) == 0 or not (float(np.ptp(y)) > 0.0):
        return None
    shift, scale = GM._fp_prepare(x)
    if not (scale > 0.0):
        return None
    xx = (x + shift) / scale
    best = None
    for i, p1 in enumerate(GM._FP_POWERS):
        for p2 in GM._FP_POWERS[i:]:
            X = GM._fp_design(xx, p1, p2)
            if not np.all(np.isfinite(X)):
                continue
            try:
                fit = dr._dash_wls(X, y, w, wtype)
            except np.linalg.LinAlgError:
                continue
            if not np.isfinite(fit["rss"]):
                continue
            if best is None or fit["rss"] < best["rss"]:
                best = dict(fit, p1=float(p1), p2=float(p2),
                            shift=shift, scale=scale)
    return best


# ----------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------

def _fixture_datasets():
    if not os.path.exists(_FIXTURE):
        return {}
    with open(_FIXTURE) as fh:
        truth = json.load(fh)
    out = {}
    for name, meta in truth["datasets"].items():
        path = os.path.join(_DATA_DIR, f"{name}.csv")
        if os.path.exists(path):
            df = pd.read_csv(path).dropna()
            out[name] = (df[meta["x"]].to_numpy(float),
                         df[meta["y"]].to_numpy(float))
    return out


_DATASETS = _fixture_datasets()


def _random(n, seed, ties=False, offset=0.0):
    rng = np.random.default_rng(seed)
    x = rng.normal(size=n) * 1000.0 + offset
    if ties:
        x = np.round(x / 250.0) * 250.0
    y = np.sin(x / 700.0) * 300.0 + rng.normal(size=n) * 100.0
    return x, y


_RANDOM = {f"n{n}_s{s}{'_ties' if t else ''}": _random(n, s, t, off)
           for n, s, t, off in [(3, 1, False, 0.0), (10, 2, False, 0.0),
                                (100, 3, True, 0.0), (1000, 4, False, 5e3),
                                (1000, 5, True, 0.0), (4000, 6, False, 1e6)]}

_VARIANTS = {"default": {}, "mean": {"mean": True},
             "noweight": {"noweight": True},
             "mean_noweight": {"mean": True, "noweight": True}}


def _assert_lowess_same(x, y, bw, opts, exact):
    xs0, s0 = _old_lowess(x, y, bw, **opts)
    xs1, s1 = GM._stata_lowess(x, y, bw, **opts)
    assert np.array_equal(xs0, xs1)
    assert np.array_equal(np.isnan(s0), np.isnan(s1))
    ok = ~np.isnan(s0)
    if exact:
        assert np.array_equal(s0[ok], s1[ok]), "not bit for bit"
    else:
        size = max(1.0, float(np.max(np.abs(y), initial=0.0)))
        diff = float(np.max(np.abs(s0[ok] - s1[ok]), initial=0.0))
        assert diff <= 1e-12 * size, (diff, size)


class TestLowessDrawsWhatItDrew:

    @pytest.mark.skipif(not _DATASETS, reason="probe datasets missing")
    @pytest.mark.parametrize("variant", list(_VARIANTS))
    @pytest.mark.parametrize("bw", [0.8, 0.5, 0.2])
    @pytest.mark.parametrize("name", ["auto", "census", "nlsw88", "sp500"])
    def test_on_the_truth_fixture_datasets(self, name, bw, variant):
        if name not in _DATASETS:
            pytest.fail(f"{name}.csv is missing from test/fixtures/data")
        x, y = _DATASETS[name]
        _assert_lowess_same(x, y, bw, _VARIANTS[variant],
                            exact=False)

    @pytest.mark.parametrize("variant", list(_VARIANTS))
    @pytest.mark.parametrize("name", list(_RANDOM))
    def test_on_random_data(self, name, variant):
        x, y = _RANDOM[name]
        for bw in (0.8, 0.3, 0.05):
            _assert_lowess_same(x, y, bw, _VARIANTS[variant],
                                exact=False)

    def test_a_constant_x_and_one_observation(self):
        for x, y in ((np.full(7, 2.0), np.arange(7.0)),
                     (np.array([1.0]), np.array([4.0])),
                     (np.array([]), np.array([]))):
            for opts in _VARIANTS.values():
                _assert_lowess_same(x, y, 0.8, opts, exact=False)


class TestFpfitFitsWhatItFitted:

    @staticmethod
    def _same_fit(a, b):
        assert (a is None) == (b is None)
        if a is None:
            return
        assert set(a) == set(b)
        for key in a:
            va, vb = a[key], b[key]
            if isinstance(va, np.ndarray):
                assert np.array_equal(va, vb, equal_nan=True), key
            elif va is None or vb is None:
                assert va is vb, key
            elif isinstance(va, float) and np.isnan(va):
                assert np.isnan(vb), key
            else:
                assert va == vb, key

    @pytest.mark.skipif(not _DATASETS, reason="probe datasets missing")
    @pytest.mark.parametrize("name", ["auto", "census", "nlsw88", "sp500"])
    def test_on_the_truth_fixture_datasets(self, name):
        x, y = _DATASETS[name]
        self._same_fit(_old_fp_fit(x, y), GM._fp_fit(x, y))
        # And with each weight type (weights 1..5 cycling).
        w = (np.arange(len(x)) % 5 + 1).astype(float)
        for wtype in ("aw", "fw", "pw"):
            self._same_fit(_old_fp_fit(x, y, w, wtype),
                           GM._fp_fit(x, y, w, wtype))

    @pytest.mark.parametrize("name", list(_RANDOM))
    def test_on_random_data(self, name):
        x, y = _RANDOM[name]
        self._same_fit(_old_fp_fit(x, y), GM._fp_fit(x, y))

    @pytest.mark.parametrize("case", ["exact_log", "exact_power", "near_tie",
                                      "negative_x", "tiny_range",
                                      "two_values", "huge_x", "tiny_x"])
    def test_on_degenerate_data(self, case):
        """Data a screen could misjudge: y an exact FP curve (many pairs
        near rss 0), two pairs nearly tied, an x shifted to positive, an x
        whose range is 1e-9 of its size, two distinct x, an x near 1e150
        and one near 1e-150 (powers overflow)."""
        rng = np.random.default_rng(11)
        x = rng.uniform(1.0, 50.0, 300)
        y = np.log(x) + rng.normal(0, 0.1, 300)
        if case == "exact_log":
            y = 3.0 + 2.0 * np.log(x)
        elif case == "exact_power":
            y = 1.0 + x ** 0.5 - 0.1 * x
        elif case == "near_tie":
            y = x ** 0.5 + 1e-9 * rng.normal(size=300)
        elif case == "negative_x":
            x = x - 30.0
        elif case == "tiny_range":
            x = 1e6 + x * 1e-9
        elif case == "two_values":
            x = np.where(x > 25.0, 2.0, 1.0)
        elif case == "huge_x":
            x = x * 1e150
        elif case == "tiny_x":
            x = x * 1e-150
        self._same_fit(_old_fp_fit(x, y), GM._fp_fit(x, y))

    def test_the_screen_keeps_the_winner(self):
        x, y = _RANDOM["n1000_s4"]
        shift, scale = GM._fp_prepare(x)
        xx = (x + shift) / scale
        fit = _old_fp_fit(x, y)
        cand = GM._fp_screen(xx, y)
        assert (fit["p1"], fit["p2"]) in cand
        # It rules pairs out, or it saves nothing.
        assert len(cand) < 36

    def test_the_screen_fits_everything_when_it_cannot_vouch(self):
        """A column that is not finite, or y with no spread, leaves every
        pair to the full search."""
        xx = np.array([1.0, 2.0, 3.0, 4.0])
        assert len(GM._fp_screen(xx, np.ones(4))) == 36
        got = GM._fp_screen(np.array([0.0, 1.0, 2.0, 3.0]),
                            np.array([1.0, 3.0, 2.0, 5.0]))
        # ln 0 and 0^-p are not finite: every pair holding a power <= 0 is
        # left to the full search, which skips it itself.
        assert {(p1, p2) for p1, p2 in got if p1 <= 0.0} == {
            (p1, p2) for i, p1 in enumerate(GM._FP_POWERS)
            for p2 in GM._FP_POWERS[i:] if p1 <= 0.0}


# ----------------------------------------------------------------------
# Cost
# ----------------------------------------------------------------------

class TestTheCostIsBounded:
    """Generous bounds: they catch the old cost coming back, not a slow
    machine."""

    def test_lowess_is_several_times_faster_than_the_old_loop(self):
        x, y = _random(6000, 21)
        t0 = time.perf_counter()
        _old_lowess(x, y)
        t_old = time.perf_counter() - t0
        t0 = time.perf_counter()
        GM._stata_lowess(x, y)
        t_new = time.perf_counter() - t0
        # Measured about 4.7x; 2x leaves room for a loaded machine.
        assert t_new * 2.0 < t_old, (t_new, t_old)

    def test_lowess_on_ten_thousand_rows(self):
        x, y = _random(10000, 22)
        t0 = time.perf_counter()
        GM._stata_lowess(x, y)
        # About 0.3 s here; the old loop took 1.3 s.
        assert time.perf_counter() - t0 < 20.0

    def test_fpfit_is_several_times_faster_than_the_full_search(self):
        rng = np.random.default_rng(23)
        x = rng.uniform(1.0, 100.0, 50000)
        y = np.log(x) + rng.normal(0, 0.3, 50000)
        t0 = time.perf_counter()
        _old_fp_fit(x, y)
        t_old = time.perf_counter() - t0
        t0 = time.perf_counter()
        GM._fp_fit(x, y)
        t_new = time.perf_counter() - t0
        assert t_new * 2.0 < t_old, (t_new, t_old)

    def test_fpfit_on_a_million_rows(self):
        rng = np.random.default_rng(24)
        x = rng.uniform(1.0, 100.0, 1_000_000)
        y = np.log(x) + rng.normal(0, 0.3, 1_000_000)
        t0 = time.perf_counter()
        fit = GM._fp_fit(x, y)
        assert time.perf_counter() - t0 < 60.0
        assert fit is not None


class TestLpolyciCost:
    """WP-29 P0.9: lpolyci's band is lpoly's analytic band, two local fits
    per grid point, where it was a 200-resample bootstrap (4.23 s against
    lpoly's 0.022 s at N=20000, about 190x).  The spy tests of
    test_lpolyci_band.py (TestNoBootstrap) are the primary assertion; this
    bound is generous for a loaded machine (the module docstring)."""

    def test_the_band_costs_a_few_lpolys(self):
        from bokeh.models import ColumnDataSource
        from bokeh.plotting import figure
        rng = np.random.default_rng(20000)
        n = 20000
        x = rng.uniform(1500.0, 5000.0, n)
        y = 40.0 - 0.006 * x + rng.normal(0.0, 3.0, n)
        src = ColumnDataSource({"y": y, "x": x})
        m = dr.GlyphMapper()

        def best(fn):
            out = []
            for _ in range(3):
                t0 = time.perf_counter()
                fn(figure(), src, "y", "x", {"bwidth": "200"})
                out.append(time.perf_counter() - t0)
            return min(out)
        t_lp = best(m.map_lpoly)
        t_ci = best(m.map_lpolyci)
        assert t_ci <= 20.0 * t_lp, (t_ci, t_lp)


@js_runner.requires_node
class TestTheJsTwinsAreBounded:
    """WP-31 F1a, F1b (M10): the saved page's lfit, qfit, lfitci and
    qfitci refits on 100,000 kept rows finish under 2 s of node's own time
    each (lpoly since F1d, lpolyci since F1e, mband and mspline since
    F1f, fpfit and fpfitci since F1g)."""

    @pytest.mark.parametrize("ptype", ["lfit", "qfit"])
    def test_lfit_and_qfit_under_node_on_1e5_rows(self, ptype):
        rng = np.random.default_rng(5)
        x = rng.uniform(1000.0, 5000.0, 100_000)
        y = 40.0 - 0.006 * x + rng.normal(0.0, 2.0, x.size)
        ac = {"type": ptype, "cols": ["x", "y"], "n": 100, "range": None,
              "wtype": None, "xaxiskind": None, "yaxiskind": None}
        got = js_runner.run_fit_js_block(ac, x, y, timed=True)
        assert len(got["data"]["x"]) == 100
        assert got["ms"] < 2000.0, got["ms"]

    @pytest.mark.parametrize("ptype", ["lfitci", "qfitci"])
    def test_lfitci_and_qfitci_under_node_on_1e5_rows(self, ptype):
        # WP-31 F1b: the line and its band (fweighted, stdf) on 1e5 rows.
        rng = np.random.default_rng(13)
        x = rng.uniform(1000.0, 5000.0, 100_000)
        y = 40.0 - 0.006 * x + rng.normal(0.0, 2.0, x.size)
        w = rng.integers(1, 6, x.size).astype(float)
        ac = {"type": ptype, "cols": ["x_fit", "y_fit", "y_lower", "y_upper"],
              "n": 100, "range": None, "wtype": "fw", "xaxiskind": None,
              "yaxiskind": None, "level": 95.0, "std": "stdf"}
        got = js_runner.run_fit_js_block(ac, x, y, w, timed=True)
        assert len(got["data"]["y_lower"]) == 100
        assert all(v is not None for v in got["data"]["y_lower"])
        assert got["ms"] < 2000.0, got["ms"]

    @pytest.mark.parametrize("ptype", ["fpfit", "fpfitci"])
    def test_fpfit_and_fpfitci_under_node_on_1e5_rows(self, ptype):
        # WP-31 F1g (D-28.a): the full 36-pair search, no screen, and the
        # stdp band, on 1e5 rows (x uniform 1-100, y = ln x + noise).
        rng = np.random.default_rng(28)
        x = rng.uniform(1.0, 100.0, 100_000)
        y = np.log(x) + rng.normal(0.0, 0.5, x.size)
        cols = ["x_fp", "y_fp"] + (["y_lower", "y_upper"]
                                   if ptype == "fpfitci" else [])
        ac = {"type": ptype, "cols": cols, "n": 100, "range": None,
              "wtype": None, "wvar": None, "xaxiskind": None,
              "yaxiskind": None, "powers": [-2.0, -1.0, -0.5, 0.0, 0.5,
                                            1.0, 2.0, 3.0],
              "max_grid": 20000, "keepmissing": False, "level": 95.0,
              "std": "stdp"}
        got = js_runner.run_fit_js_block(ac, x, y, timed=True)
        assert len(got["data"]["x_fp"]) == 20000
        assert got["ms"] < 2000.0, got["ms"]

    #: A lowess config as map_lowess writes it (WP-31 F1c).
    _LW = {"type": "lowess", "cols": ["x_lw", "y_lw"], "n": 100,
           "range": None, "wtype": None, "xaxiskind": None,
           "yaxiskind": None, "bwidth": 0.8, "mean": False,
           "noweight": False, "adjust": False, "logit": False,
           "y_all_mean": None, "max_ops": 2e8}

    def test_lowess_under_node_on_1e4_rows(self):
        # WP-31 F1c: twoway's lowess is O(N x window); at 1e4 rows and bw
        # .8 it is 8e7 window operations, under the cap (D-16.e).  M10's
        # 1e5-row bound cannot hold for it (section-16 risk).
        rng = np.random.default_rng(16)
        x = rng.uniform(1000.0, 5000.0, 10_000)
        y = 40.0 - 0.006 * x + rng.normal(0.0, 2.0, x.size)
        got = js_runner.run_fit_js_block(self._LW, x, y, timed=True)
        assert len(got["data"]["x_lw"]) == 10_000
        assert got["ms"] < 2000.0, got["ms"]

    @pytest.mark.parametrize("degree", [0, 3])
    def test_lpoly_under_node_on_1e5_rows(self, degree):
        # WP-31 F1d (M10): the default bandwidth (the rule of thumb's
        # global fit of degree pe+3 on every kept row) and the local fits
        # at 50 grid points, on 1e5 rows.
        rng = np.random.default_rng(19)
        x = rng.uniform(1000.0, 5000.0, 100_000)
        y = 40.0 - 0.006 * x + rng.normal(0.0, 2.0, x.size)
        ac = {"type": "lpoly", "cols": ["x_lp", "y_lp"], "n": 50,
              "range": None, "wtype": None, "xaxiskind": None,
              "yaxiskind": None, "bwidth": None, "degree": degree,
              "kernel": "epanechnikov", "n_dataset": 100_000,
              "n_user": None, "keepmissing": False}
        got = js_runner.run_fit_js_block(ac, x, y, timed=True)
        assert len(got["data"]["x_lp"]) == 50
        assert all(v is not None for v in got["data"]["y_lp"])
        assert got["ms"] < 2000.0, got["ms"]

    def test_lpolyci_under_node_on_1e5_rows(self):
        # WP-31 F1e (M10): the rule of thumb, the smooth and the band's two
        # local fits per grid point (50 x 2 x 1e5) at degree 0, written to
        # the line and the band from one computation, on 1e5 rows.
        rng = np.random.default_rng(22)
        x = rng.uniform(1000.0, 5000.0, 100_000)
        y = 40.0 - 0.006 * x + rng.normal(0.0, 2.0, x.size)
        ac = {"type": "lpolyci", "cols": ["x_lp", "y_lp", "y_lower",
                                          "y_upper"],
              "n": 50, "range": None, "wtype": None, "xaxiskind": None,
              "yaxiskind": None, "bwidth": None, "pwidth": None,
              "lpvar": None, "level": 95.0, "degree": 0,
              "kernel": "epanechnikov", "n_dataset": 100_000,
              "n_user": None, "keepmissing": False}
        got = js_runner.run_fit_js_block_roles(ac, x, y, timed=True)
        assert len(got["line"]["x_lp"]) == 50
        assert len(got["band"]["y_lower"]) == 50
        assert all(v is not None for v in got["band"]["y_upper"])
        assert got["cache_size"] == 1
        assert got["ms"] < 2000.0, got["ms"]

    @pytest.mark.parametrize("ptype,cols", [("mband", ["x_mb", "y_mb"]),
                                            ("mspline", ["x_sp", "y_sp"])])
    def test_mband_and_mspline_under_node_on_1e5_rows(self, ptype, cols):
        # WP-31 F1f (M10): the default band count (50 on 1e5 rows), the
        # cross medians (two sorts per band) and mspline's spline.
        rng = np.random.default_rng(25)
        x = rng.uniform(1000.0, 5000.0, 100_000)
        y = 40.0 - 0.006 * x + rng.normal(0.0, 2.0, x.size)
        ac = {"type": ptype, "xvar": "x", "yvar": "y", "cols": cols,
              "n": 100, "range": None, "wtype": None, "xdatekind": None,
              "ydatekind": None, "xaxiskind": None, "yaxiskind": None,
              "bands": None, "max_bands": 1000, "n_between": 10}
        got = js_runner.run_fit_js_block(ac, x, y, timed=True)
        assert len(got["data"][cols[0]]) == (50 if ptype == "mband"
                                             else 49 * 10 + 50)
        assert got["ms"] < 2000.0, got["ms"]

    def test_lowess_is_capped_above_max_ops(self):
        # 20000 * (2 * 7999 + 1) = 3.2e8 > 2e8: the line is left empty.
        rng = np.random.default_rng(17)
        x = rng.uniform(1000.0, 5000.0, 20_000)
        got = js_runner.run_fit_js_block(self._LW, x, 0.5 * x, timed=True)
        assert got["data"] == {"x_lw": [], "y_lw": []}
        assert got["ms"] < 200.0, got["ms"]


class TestDotRows:
    """WP-31 B5b: twoway dot's rows over 100,000 observations -- 7.6
    million dots at 75 a row -- are placed within two seconds, both ways
    (GlyphMapper._dot_positions: one step sequence each way, every row a
    prefix of it)."""

    def test_under_two_seconds(self):
        vals = np.random.default_rng(18).uniform(10.0, 40.0, 100_000)
        for extend in (True, False):
            t0 = time.perf_counter()
            pos, rows, nd = GM._dot_positions(10.0, 40.0, vals, extend, 75)
            assert time.perf_counter() - t0 < 2.0, extend
            assert nd == 75 and len(pos) == len(rows) > 100_000


def test_table_text_frame_under_two_seconds_at_100k():
    """WP-31 H2t: a data table's text columns over 100,000 rows of six
    variables are written within two seconds -- each distinct value is
    formatted once and mapped onto the rows (_dash_table_text_frame)."""
    rng = np.random.default_rng(19)
    n = 100_000
    df = pd.DataFrame({
        "a": rng.integers(0, 5000, n).astype(float),
        "b": rng.uniform(0.0, 1.0, n).round(2),
        "c": rng.integers(0, 2, n).astype(float),
        "d": rng.integers(1, 6, n).astype(float),
        "e": rng.integers(1000, 16000, n).astype(float),
        "f": rng.integers(10, 40, n).astype(float),
    })
    df.loc[::7, "d"] = np.nan
    fmts = {"a": "%9.0g", "b": "%9.2f", "c": "%8.0g", "d": "%8.0g",
            "e": "%8.0gc", "f": "%8.0g"}
    t0 = time.perf_counter()
    cols = dr._dash_table_text_frame(
        df, list(fmts), fmts, {}, {"cl": {"0": "No", "1": "Yes"}},
        {"c": "cl"}, {}, {})
    assert time.perf_counter() - t0 < 2.0
    assert [v for v, _t in cols] == list(fmts)
    assert df["__dash_tbl_d"].iloc[0] == "."
    assert set(df["__dash_tbl_c"]) == {"No", "Yes"}
