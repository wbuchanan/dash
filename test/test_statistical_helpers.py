"""Direct unit tests for the statistical helpers WP-18 added.

CLAUDE.md rule 4: every function has a unit test.  The mapper-level
comparisons against Stata's own plotted points are in
test_statistical_truth.py; these pin each helper's contract on inputs small
enough to check by an INDEPENDENT computation -- a replicated dataset for a
frequency weight, a dense linear solve for the spline, a closed form for a
band, a running mean written out by hand -- so a helper that drifts fails
here, under its own name, and not only as a curve that moved.
"""
import math
import os
import sys
import warnings

import numpy as np
import pytest
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
import dash_render as dr  # noqa: E402

GM = dr.GlyphMapper
_RNG = np.random.default_rng(20260923)


# ======================================================================
# _dash_weight_spec -- the (type, variable) a plot's options carry
# ======================================================================
class TestWeightSpec:
    def test_no_clause_is_unweighted(self):
        assert dr._dash_weight_spec({}) == (None, "")
        assert dr._dash_weight_spec(None) == (None, "")
        assert dr._dash_weight_spec({"bwidth": "2"}) == (None, "")

    @pytest.mark.parametrize("full,short", [("aweight", "aw"), ("fweight", "fw"),
                                            ("pweight", "pw"), ("iweight", "iw")])
    def test_each_type_reduces_to_its_two_letters(self, full, short):
        assert dr._dash_weight_spec({"weight": full, "wexp": "price"}) == (short, "price")
        assert dr._dash_weight_spec({"weight": short, "wexp": "price"}) == (short, "price")
        assert dr._dash_weight_spec({"weight": " %s " % full.upper(),
                                     "wexp": " price "}) == (short, "price")

    def test_half_a_clause_is_unweighted(self):
        assert dr._dash_weight_spec({"weight": "aweight"}) == (None, "")
        assert dr._dash_weight_spec({"wexp": "price"}) == (None, "")
        assert dr._dash_weight_spec({"weight": "", "wexp": "price"}) == (None, "")

    def test_an_unknown_type_is_unweighted(self):
        assert dr._dash_weight_spec({"weight": "xweight", "wexp": "price"}) == (None, "")


# ======================================================================
# _dash_weight_norm / _dash_lpoly_weights -- the normalisations
# ======================================================================
class TestWeightNormalisation:
    W = np.array([2.0, 5.0, 1.0, 4.0])

    def test_no_weight_is_unit_weights(self):
        np.testing.assert_array_equal(dr._dash_weight_norm(None, None, 3), np.ones(3))
        assert dr._dash_lpoly_weights(None, None) is None

    def test_a_frequency_weight_is_left_raw(self):
        np.testing.assert_array_equal(dr._dash_weight_norm(self.W, "fw", 4), self.W)
        np.testing.assert_array_equal(dr._dash_lpoly_weights(self.W, "fw"), self.W)

    @pytest.mark.parametrize("wtype", ["aw", "pw"])
    def test_an_analytic_weight_sums_to_the_observation_count(self, wtype):
        got = dr._dash_weight_norm(self.W, wtype, 4)
        assert got.sum() == pytest.approx(4.0, rel=1e-15)
        np.testing.assert_allclose(got / got[0], self.W / self.W[0], rtol=1e-15)

    def test_lpoly_normalises_an_aweight_to_mean_one(self):
        got = dr._dash_lpoly_weights(self.W, "aw")
        assert got.mean() == pytest.approx(1.0, rel=1e-15)
        np.testing.assert_allclose(got / got[0], self.W / self.W[0], rtol=1e-15)


# ======================================================================
# _dash_wls -- regress y X [w], as Stata reports it
# ======================================================================
class TestWls:
    n = 12
    x = _RNG.uniform(1.0, 10.0, n)
    X = np.column_stack([np.ones(n), x])
    y = 2.0 + 3.0 * x + _RNG.normal(0.0, 1.0, n)
    fw = _RNG.integers(1, 5, n).astype(float)
    aw = _RNG.uniform(0.5, 3.0, n)

    def test_unweighted_is_ordinary_least_squares(self):
        fit = dr._dash_wls(self.X, self.y)
        beta, *_ = np.linalg.lstsq(self.X, self.y, rcond=None)
        e = self.y - self.X @ beta
        s2 = float(e @ e) / (self.n - 2)
        np.testing.assert_allclose(fit["beta"], beta, rtol=1e-12)
        assert fit["N"] == self.n and fit["df"] == self.n - 2
        assert fit["s2"] == pytest.approx(s2, rel=1e-12)
        np.testing.assert_allclose(fit["cov"], s2 * np.linalg.inv(self.X.T @ self.X),
                                   rtol=1e-10)

    def test_a_frequency_weight_is_the_replicated_regression(self):
        rep = np.repeat(np.arange(self.n), self.fw.astype(int))
        Xr, yr = self.X[rep], self.y[rep]
        want = dr._dash_wls(Xr, yr)
        got = dr._dash_wls(self.X, self.y, self.fw, "fw")
        assert got["N"] == pytest.approx(self.fw.sum()) and got["N"] == len(rep)
        assert got["df"] == pytest.approx(len(rep) - 2)
        np.testing.assert_allclose(got["beta"], want["beta"], rtol=1e-10)
        assert got["s2"] == pytest.approx(want["s2"], rel=1e-10)
        np.testing.assert_allclose(got["cov"], want["cov"], rtol=1e-9)

    def test_an_analytic_weight_is_scale_free_with_n_minus_k_df(self):
        got = dr._dash_wls(self.X, self.y, self.aw, "aw")
        scaled = dr._dash_wls(self.X, self.y, 7.0 * self.aw, "aw")
        W = np.diag(self.aw)
        beta = np.linalg.solve(self.X.T @ W @ self.X, self.X.T @ W @ self.y)
        e = self.y - self.X @ beta
        wn = self.aw * self.n / self.aw.sum()
        s2 = float(wn @ (e * e)) / (self.n - 2)
        np.testing.assert_allclose(got["beta"], beta, rtol=1e-10)
        assert got["N"] == pytest.approx(self.n) and got["df"] == pytest.approx(self.n - 2)
        assert got["s2"] == pytest.approx(s2, rel=1e-10)
        np.testing.assert_allclose(scaled["beta"], got["beta"], rtol=1e-10)
        np.testing.assert_allclose(scaled["cov"], got["cov"], rtol=1e-9)

    def test_a_pweight_gives_the_aweight_line_with_the_hc1_sandwich(self):
        got = dr._dash_wls(self.X, self.y, self.aw, "pw")
        aw = dr._dash_wls(self.X, self.y, self.aw, "aw")
        np.testing.assert_allclose(got["beta"], aw["beta"], rtol=1e-12)
        e = self.y - self.X @ got["beta"]
        A = np.linalg.inv(self.X.T @ (self.X * self.aw[:, None]))
        u = self.X * (self.aw * e)[:, None]
        hc1 = A @ (u.T @ u) @ A * self.n / (self.n - 2)
        np.testing.assert_allclose(got["cov"], hc1, rtol=1e-9)
        assert not np.allclose(got["cov"], aw["cov"])

    def test_a_collinear_column_is_omitted_as_regress_omits_it(self):
        # regress drops the later of a collinear pair and fits the rest,
        # df = N - rank: qfitci on an x with two values is the LINE (the
        # WP-18 review).  This asserted that a singular design raised.
        x = np.array([1.0, 1.0, 2.0, 2.0, 2.0])
        y = np.array([3.0, 4.0, 6.0, 7.0, 8.0])
        X = np.column_stack([np.ones(5), x, x * x])
        fit = dr._dash_wls(X, y)
        assert fit["keep"] == [0, 1] and fit["rank"] == 2 and fit["df"] == 3
        assert fit["beta"][2] == 0.0
        line = np.polyfit(x, y, 1)
        np.testing.assert_allclose(fit["beta"][:2], line[::-1], rtol=1e-12,
                                   atol=1e-12)
        # the band is the line's band
        lfit = dr._dash_wls(X[:, :2], y)
        xg = np.column_stack([np.ones(3), [1.0, 1.5, 2.0], [1.0, 2.25, 4.0]])
        np.testing.assert_allclose(dr._dash_fitci_se(xg, fit, "stdp"),
                                   dr._dash_fitci_se(xg[:, :2], lfit, "stdp"),
                                   rtol=1e-12)
        with pytest.raises(np.linalg.LinAlgError):
            dr._dash_wls(np.zeros((3, 2)), y[:3])

    def test_an_ill_conditioned_design_is_statas(self):
        # Hourly date-times in milliseconds -- an offset of 1.9e12 against a
        # range of 2.6e8 -- with the design [1, x/1e8, (x/1e8)^2].  Measured
        # 23sep2026: Stata's regress omits h1 for collinearity (df 70) and
        # predict gives the fit and stdp below at rows 1, 8, ..., 71.  dash
        # decides the rank on the raw design, as lstsq does: rank 2, df 70.
        # It truncates the SVD where Stata omits a column, two rank-2 fits
        # of almost the same column space -- 1.1e-5 of the span apart, the
        # stdp 2.3e-5 (dropping h1 itself would agree to 1e-11, but which
        # column regress drops from a NEARLY collinear pair is its own
        # pivoting, not emulated).  A centred full-rank fit is 30% off
        # Stata's band here, and s2 * inv(X'WX) 10% to 90%.
        x = 1.8934560e12 + 3.6e6 * np.arange(72.0)
        y = np.array(_ILLCOND_Y)
        X = np.column_stack([np.ones(72), x / 1e8, (x / 1e8) ** 2])
        fit = dr._dash_wls(X, y)
        assert fit["df"] == 70
        Xg = X[::7]
        np.testing.assert_allclose(
            Xg @ fit["beta"],
            [14.6034335722325, 15.157056096501, 15.7106859888736,
             16.2643232493647, 16.8179678779707, 17.3716198746806,
             17.9252792395091, 18.4789459724416, 19.0326200734926,
             19.5863015426512, 20.1399903799247], rtol=0, atol=2e-5 * 5.54)
        np.testing.assert_allclose(
            dr._dash_fitci_se(Xg, fit, "stdp"),
            [.21141500476388, .181283009260115, .153684600808918,
             .130240893293414, .11355541756077, .106843292015803,
             .111914078608432, .127368568902372, .150031887119091,
             .17715899053931, .207002604655714], rtol=5e-5)


_ILLCOND_Y = [
    14.198068574746552, 13.747641004371854, 14.895638377904751, 15.636445238065521,
    16.424046532489644, 15.469706399321808, 14.879352679463768, 14.719219644655722,
    16.32474577073459, 17.282783042958577, 15.992768775844722, 14.558671335969228,
    14.905734794563912, 17.53601908899911, 16.21088244050861, 14.347865157560413,
    16.068303807182975, 15.06077402655525, 15.666711905938445, 15.879994176723141,
    15.726686628367757, 17.06537847035329, 16.52091402807471, 16.066568741967394,
    17.137637826557118, 17.629855307061323, 15.228976628594323, 16.687269873634506,
    16.035252643955985, 16.91484477513797, 15.870581253246142, 17.25269039403759,
    17.266114258955934, 17.071662249041513, 16.400073494879756, 17.123809669526906,
    16.500671098304288, 16.308791253795263, 17.960785732459893, 16.698650062108634,
    19.050296101178294, 18.668587655873836, 16.02618330755028, 18.368128869412487,
    17.066283372418955, 18.27305722015827, 18.35563199256942, 16.39557021176888,
    18.22257747623423, 18.272209968600606, 19.562000531843097, 17.490553192043784,
    19.482041897845683, 17.71702723696359, 18.55670910730008, 18.11952683157779,
    20.48073128892167, 19.672213099788294, 21.607732502845213, 19.889916379082322,
    20.164992733719174, 20.23268287626534, 18.857388464090448, 19.46597155336162,
    20.958388867744628, 19.283449234827028, 19.9407995312911, 19.80277653958271,
    20.50521649283274, 19.60309125805263, 19.887638111243152, 20.354381428672152]


# ======================================================================
# _dash_fitci_std / _dash_fitci_se -- which band, and its standard error
# ======================================================================
class TestFitciStandardErrors:
    def test_the_default_is_stdp(self):
        assert dr._dash_fitci_std({}) == "stdp"
        assert dr._dash_fitci_std(None) == "stdp"
        assert dr._dash_fitci_std({"stdp": "stdp"}) == "stdp"

    def test_stdf_and_stdr_are_read(self):
        assert dr._dash_fitci_std({"stdf": "stdf"}) == "stdf"
        assert dr._dash_fitci_std({"stdr": "stdr"}) == "stdr"

    # x0' V x0 at the three rows below is 2, 4 and 14; s^2 is 4.
    FIT = {"cov": np.array([[2.0, 0.5], [0.5, 1.0]]), "s2": 4.0}
    XG = np.array([[1.0, 0.0], [1.0, 1.0], [1.0, 3.0]])

    def test_stdp_is_the_prediction_standard_error(self):
        np.testing.assert_allclose(dr._dash_fitci_se(self.XG, self.FIT, "stdp"),
                                   np.sqrt([2.0, 4.0, 14.0]), rtol=1e-15)

    def test_stdf_adds_the_residual_variance(self):
        np.testing.assert_allclose(dr._dash_fitci_se(self.XG, self.FIT, "stdf"),
                                   np.sqrt([6.0, 8.0, 18.0]), rtol=1e-15)

    def test_stdr_subtracts_it_and_is_missing_where_negative(self):
        got = dr._dash_fitci_se(self.XG, self.FIT, "stdr")
        assert got[0] == pytest.approx(math.sqrt(2.0), rel=1e-15)
        assert got[1] == 0.0
        assert np.isnan(got[2])


# ======================================================================
# _natural_cubic_spline
# ======================================================================
def _dense_natural_spline(kx, ky, xs):
    """Reference: the natural spline's moments from a dense solve."""
    k = len(kx)
    h = np.diff(kx)
    a = np.zeros((k, k))
    rhs = np.zeros(k)
    a[0, 0] = a[-1, -1] = 1.0
    for i in range(1, k - 1):
        a[i, i - 1], a[i, i], a[i, i + 1] = h[i - 1], 2 * (h[i - 1] + h[i]), h[i]
        rhs[i] = 6 * ((ky[i + 1] - ky[i]) / h[i] - (ky[i] - ky[i - 1]) / h[i - 1])
    m = np.linalg.solve(a, rhs)
    out = []
    for xv in xs:
        i = min(max(int(np.searchsorted(kx, xv, side="right")) - 1, 0), k - 2)
        dl, dr_ = xv - kx[i], kx[i + 1] - xv
        out.append(m[i] * dr_ ** 3 / (6 * h[i]) + m[i + 1] * dl ** 3 / (6 * h[i])
                   + (ky[i] / h[i] - m[i] * h[i] / 6) * dr_
                   + (ky[i + 1] / h[i] - m[i + 1] * h[i] / 6) * dl)
    return np.array(out), m


class TestNaturalCubicSpline:
    kx = np.array([0.0, 0.7, 1.9, 2.4, 4.0, 5.5, 7.1])
    ky = np.array([1.0, 3.0, 2.0, 2.5, -1.0, 0.5, 2.0])

    def test_it_passes_through_every_knot(self):
        np.testing.assert_allclose(dr._natural_cubic_spline(self.kx, self.ky, self.kx),
                                   self.ky, rtol=0, atol=1e-13)

    def test_it_equals_a_dense_solve_everywhere(self):
        xs = np.linspace(self.kx[0], self.kx[-1], 301)
        want, m = _dense_natural_spline(self.kx, self.ky, xs)
        assert m[0] == 0.0 and m[-1] == 0.0          # the natural end condition
        np.testing.assert_allclose(dr._natural_cubic_spline(self.kx, self.ky, xs),
                                   want, rtol=0, atol=1e-12)

    def test_collinear_knots_give_the_line(self):
        ky = 2.0 * self.kx + 1.0
        xs = np.linspace(0.0, 7.1, 50)
        np.testing.assert_allclose(dr._natural_cubic_spline(self.kx, ky, xs),
                                   2.0 * xs + 1.0, rtol=0, atol=1e-12)

    def test_two_knots_are_the_chord_and_fewer_are_flat_or_missing(self):
        got = dr._natural_cubic_spline(np.array([1.0, 3.0]), np.array([2.0, 6.0]),
                                       np.array([1.0, 2.0, 3.0]))
        np.testing.assert_allclose(got, [2.0, 4.0, 6.0], rtol=1e-15)
        np.testing.assert_array_equal(
            dr._natural_cubic_spline(np.array([1.0]), np.array([5.0]),
                                     np.array([0.0, 1.0])), [5.0, 5.0])
        assert np.isnan(dr._natural_cubic_spline(np.array([]), np.array([]),
                                                 np.array([0.0]))).all()


# ======================================================================
# _stata_weighted_percentile / _stata_kde_bandwidth
# ======================================================================
class TestWeightedPercentile:
    PS = (1, 5, 10, 25, 50, 75, 90, 95, 99)

    @pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 8, 37])
    def test_unit_weights_are_statas_unweighted_percentile(self, n):
        a = np.sort(_RNG.integers(0, 6, n).astype(float))   # ties on purpose
        for p in self.PS:
            assert dr._stata_weighted_percentile(a, np.ones(n), p) == \
                dr._stata_percentile(a, p), (n, p)

    @pytest.mark.parametrize("seed", range(6))
    def test_integer_weights_are_the_replicated_percentile(self, seed):
        rng = np.random.default_rng(seed)
        a = np.sort(rng.normal(0.0, 1.0, 9))
        w = rng.integers(1, 5, 9).astype(float)
        rep = np.repeat(a, w.astype(int))
        for p in self.PS:
            assert dr._stata_weighted_percentile(a, w, p) == \
                dr._stata_percentile(rep, p), (seed, p)

    def test_an_exact_boundary_averages_the_neighbours(self):
        a = np.array([1.0, 2.0, 3.0, 4.0])
        assert dr._stata_weighted_percentile(a, np.ones(4), 50) == 2.5
        assert dr._stata_weighted_percentile(a, np.array([1.0, 1.0, 2.0, 1.0]), 50) == 3.0

    def test_a_tie_the_float_running_sum_misses_is_still_a_tie(self):
        # The WP-18 review, 23sep2026: `summarize x [aw=w], detail' gives
        # p25 = 2.5 and `kdensity x [aw=w]' r(bwidth) 2.3152252 on these ten
        # values.  P = W/4 = .85 exactly in decimal, and the running sum of
        # the first two weights lands a hair below it in binary, so a
        # search with no tolerance skipped the tie: p25 3.0, bandwidth
        # 2.10475, the density 4.2% high at x = 1 -- and the page's own
        # JavaScript, which has the tolerance, moved the curve on the
        # first filter move.
        x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 30, 60], dtype=float)
        w = np.array([.15, .7, .15, .35, .2, .1, .35, .7, .35, .35])
        assert dr._stata_weighted_percentile(x, w, 25) == 2.5
        assert dr._stata_kde_bandwidth(x, w, "aw") == pytest.approx(2.3152252, rel=1e-7)

    def test_nothing_to_rank_is_missing(self):
        assert math.isnan(dr._stata_weighted_percentile(np.array([]), np.array([]), 50))
        assert math.isnan(dr._stata_weighted_percentile(np.array([1.0]),
                                                        np.array([0.0]), 50))


class TestKdeBandwidth:
    x = np.array([12, 14, 14, 15, 17, 18, 18, 18, 19, 21, 22, 24, 25, 25, 28, 31, 35.0])

    def test_a_frequency_weight_is_the_replicated_bandwidth(self):
        w = np.array([1, 2, 1, 3, 1, 1, 2, 1, 4, 1, 1, 2, 1, 1, 3, 1, 2.0])
        rep = np.repeat(self.x, w.astype(int))
        assert dr._stata_kde_bandwidth(self.x, w, "fw") == \
            pytest.approx(dr._stata_kde_bandwidth(rep), rel=1e-12)

    def test_an_analytic_weight_uses_weighted_moments_and_n_observations(self):
        w = np.linspace(0.5, 2.5, len(self.x))
        n = len(self.x)
        mu = float(w @ self.x) / w.sum()
        sd = math.sqrt(float(w @ (self.x - mu) ** 2) * n / w.sum() / (n - 1))
        iqr = (dr._stata_weighted_percentile(self.x, w, 75)
               - dr._stata_weighted_percentile(self.x, w, 25))
        want = 0.9 * min(sd, iqr / 1.349) * n ** -0.2
        assert dr._stata_kde_bandwidth(self.x, w, "aw") == pytest.approx(want, rel=1e-12)
        assert dr._stata_kde_bandwidth(self.x, 3.0 * w, "aw") == \
            pytest.approx(want, rel=1e-12)

    def test_nothing_to_smooth_is_zero(self):
        assert dr._stata_kde_bandwidth(np.array([3.0])) == 0.0
        assert dr._stata_kde_bandwidth(np.array([3.0, 3.0, 3.0])) == 0.0


# ======================================================================
# GlyphMapper._layer_weights
# ======================================================================
class TestLayerWeights:
    def _src(self):
        return ColumnDataSource({
            "x": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            "y": [2.0, 4.0, 5.0, np.nan, 7.0, 9.0],
            "w": [1.0, 2.0, np.nan, 4.0, 0.0, 3.0],
        })

    def test_an_unweighted_layer_is_masked_and_carries_no_weight(self):
        x, y, w, wt = GM._layer_weights(self._src(), None, {}, "lfit", "x", "y")
        np.testing.assert_array_equal(x, [1, 2, 3, 5, 6])
        np.testing.assert_array_equal(y, [2, 4, 5, 7, 9])
        assert w is None and wt is None

    def test_the_weight_joins_the_nan_drop_and_nonpositive_rows_leave(self):
        dr._dash_reset_notes()
        with pytest.warns(UserWarning, match="zero or negative weight"):
            x, y, w, wt = GM._layer_weights(
                self._src(), None, {"weight": "aweight", "wexp": "w"}, "lfit", "x", "y")
        # row 3 has no weight, row 4 no y, row 5 a zero weight
        np.testing.assert_array_equal(x, [1, 2, 6])
        np.testing.assert_array_equal(y, [2, 4, 9])
        np.testing.assert_array_equal(w, [1, 2, 3])
        assert wt == "aw"

    def test_the_view_restricts_the_rows_first(self):
        # A CDSView, as a by() panel or a qualifier hands the mapper: it
        # drops row 1 (x = 2), which every other rule would keep.
        from bokeh.models import BooleanFilter, CDSView
        view = CDSView(filter=BooleanFilter(
            booleans=[True, False, True, True, True, True]))
        x, y, w, wt = GM._layer_weights(
            self._src(), view, {"weight": "fweight", "wexp": "w"}, "lfit", "x", "y")
        np.testing.assert_array_equal(x, [1, 6])
        np.testing.assert_array_equal(w, [1, 3])
        assert wt == "fw"

    @pytest.mark.parametrize("layer,wtype", [("kdensity", "pweight"),
                                             ("histogram", "aweight"),
                                             ("lowess", "aweight"),
                                             ("lfit", "iweight")])
    def test_a_type_the_layer_refuses_is_named_and_not_applied(self, layer, wtype):
        dr._dash_reset_notes()
        with pytest.warns(UserWarning, match="not allowed"):
            out = GM._layer_weights(self._src(), None, {"weight": wtype, "wexp": "w"},
                                    layer, "x", "y")
        assert out[-2] is None and out[-1] is None
        np.testing.assert_array_equal(out[0], [1, 2, 3, 5, 6])

    @pytest.mark.parametrize("layer", ["mspline", "mband"])
    def test_an_inert_weight_changes_no_row(self, layer):
        # twoway draws the same curve with missing or zero weights (measured
        # 23sep2026: [aw=rep78] and a 0/1 weight give the unweighted serset).
        # Flipped (WP-31 A5b): the weight was named "does not use it",
        # which was wrong because twoway takes it and says nothing
        # (weighted_markers_truth.json I_mspline, I_mband).
        dr._dash_reset_notes()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            x, y, w, wt = GM._layer_weights(
                self._src(), None, {"weight": "aweight", "wexp": "w"}, layer, "x", "y")
        assert not caught, [str(c.message) for c in caught]
        np.testing.assert_array_equal(x, [1, 2, 3, 5, 6])
        assert w is None and wt is None

    def test_a_weight_the_data_do_not_carry_is_named(self):
        dr._dash_reset_notes()
        with pytest.warns(UserWarning, match="carries no variable"):
            out = GM._layer_weights(self._src(), None,
                                    {"weight": "aweight", "wexp": "nosuch"},
                                    "lfit", "x", "y")
        assert out[-2] is None and out[-1] is None


# ======================================================================
# GlyphMapper._stata_lowess
# ======================================================================
def _index_windows(n, bw):
    k = int((n * bw - 0.5) / 2.0)
    return [(max(0, i - k), min(n - 1, i + k)) for i in range(n)]


class TestStataLowess:
    x = np.array([3.0, 1.0, 4.0, 1.5, 5.0, 9.0, 2.0, 6.0, 5.5, 3.5])
    y = np.array([2.0, 7.0, 1.0, 8.0, 2.0, 8.0, 1.0, 8.0, 2.0, 8.0])

    def test_one_value_per_observation_in_x_order(self):
        xs, s = GM._stata_lowess(self.x, self.y)
        np.testing.assert_array_equal(xs, np.sort(self.x))
        assert len(s) == len(self.x)

    def test_noweight_mean_is_the_running_mean_over_the_index_window(self):
        o = np.argsort(self.x, kind="stable")
        ys = self.y[o]
        want = [ys[lo:hi + 1].mean() for lo, hi in _index_windows(len(ys), 0.5)]
        _, s = GM._stata_lowess(self.x, self.y, bw=0.5, mean=True, noweight=True)
        np.testing.assert_allclose(s, want, rtol=1e-14)

    def test_noweight_line_is_ols_over_the_index_window(self):
        o = np.argsort(self.x, kind="stable")
        xs, ys = self.x[o], self.y[o]
        want = []
        for i, (lo, hi) in enumerate(_index_windows(len(xs), 0.5)):
            b1, b0 = np.polyfit(xs[lo:hi + 1], ys[lo:hi + 1], 1)
            want.append(b0 + b1 * xs[i])
        _, s = GM._stata_lowess(self.x, self.y, bw=0.5, noweight=True)
        np.testing.assert_allclose(s, want, rtol=1e-12)

    def test_the_weights_are_tricube_on_1_0001_times_the_farthest(self):
        o = np.argsort(self.x, kind="stable")
        xs, ys = self.x[o], self.y[o]
        want = []
        for i, (lo, hi) in enumerate(_index_windows(len(xs), 0.8)):
            d = np.abs(xs[lo:hi + 1] - xs[i])
            w = (1 - (d / (1.0001 * d.max())) ** 3) ** 3
            want.append(float(w @ ys[lo:hi + 1]) / w.sum())
        _, s = GM._stata_lowess(self.x, self.y, bw=0.8, mean=True)
        np.testing.assert_allclose(s, want, rtol=1e-13)

    def test_a_straight_line_is_reproduced(self):
        _, s = GM._stata_lowess(self.x, 4.0 - 0.5 * self.x)
        np.testing.assert_allclose(s, 4.0 - 0.5 * np.sort(self.x), rtol=0, atol=1e-12)

    def test_tied_x_keep_dataset_order_and_their_own_values(self):
        x = np.array([1.0, 2.0, 2.0, 2.0, 3.0, 4.0, 5.0])
        y = np.array([1.0, 5.0, 0.0, 9.0, 2.0, 3.0, 1.0])
        _, s = GM._stata_lowess(x, y, bw=0.5, mean=True, noweight=True)
        # windows of one on each side: the three tied rows see different
        # neighbours in dataset order, so they get three different values
        assert s[1] == pytest.approx((1 + 5 + 0) / 3)
        assert s[2] == pytest.approx((5 + 0 + 9) / 3)
        assert s[3] == pytest.approx((0 + 9 + 2) / 3)

    def test_a_single_observation_and_a_constant_x(self):
        # No x spread in the window: the running LINE is missing, as
        # Stata's is (the WP-18 review); the running mean is the window's
        # mean.  map_lowess's own gate never smooths either sample.
        _, s = GM._stata_lowess(np.array([2.0]), np.array([7.0]))
        assert np.isnan(s).all()
        _, s = GM._stata_lowess(np.array([2.0]), np.array([7.0]), mean=True)
        np.testing.assert_array_equal(s, [7.0])
        _, s = GM._stata_lowess(np.full(5, 3.0), np.array([1.0, 2, 3, 4, 5]), bw=0.8)
        assert np.isnan(s).all()
        _, s = GM._stata_lowess(np.full(5, 3.0), np.array([1.0, 2, 3, 4, 5]), bw=0.8,
                                mean=True)
        want = [np.mean([1.0, 2, 3, 4, 5][lo:hi + 1]) for lo, hi in _index_windows(5, 0.8)]
        np.testing.assert_allclose(s, want, rtol=1e-15)


# ======================================================================
# The fractional polynomial helpers
# ======================================================================
class TestFpDesign:
    xx = np.array([0.5, 1.0, 2.0, 4.0])

    def test_two_different_powers(self):
        np.testing.assert_allclose(GM._fp_design(self.xx, -2.0, 0.5),
                                   np.column_stack([np.ones(4), self.xx ** -2,
                                                    self.xx ** 0.5]), rtol=1e-15)

    def test_power_zero_is_the_log(self):
        np.testing.assert_allclose(GM._fp_design(self.xx, 0.0, 3.0),
                                   np.column_stack([np.ones(4), np.log(self.xx),
                                                    self.xx ** 3]), rtol=1e-15)

    def test_a_repeated_power_multiplies_by_the_log(self):
        lx = np.log(self.xx)
        np.testing.assert_allclose(GM._fp_design(self.xx, 2.0, 2.0),
                                   np.column_stack([np.ones(4), self.xx ** 2,
                                                    self.xx ** 2 * lx]), rtol=1e-15)
        np.testing.assert_allclose(GM._fp_design(self.xx, 0.0, 0.0),
                                   np.column_stack([np.ones(4), lx, lx * lx]),
                                   rtol=1e-15)


class TestFpPrepare:
    def test_positive_x_is_only_scaled_by_its_range(self):
        assert GM._fp_prepare(np.array([1000.0, 1500.0, 2234.0])) == (0.0, 1000.0)
        assert GM._fp_prepare(np.array([1.0, 3.0, 9.0])) == (0.0, 1.0)
        shift, scale = GM._fp_prepare(np.array([0.10, 0.12, 0.15]))
        assert shift == 0.0 and scale == pytest.approx(0.1, rel=1e-15)

    def test_a_non_positive_minimum_is_shifted_past_zero(self):
        # sorted spacings 2, 1, 2 -> smallest positive 1 -> shift 1 - (-3)
        shift, scale = GM._fp_prepare(np.array([2.0, -3.0, 0.0, -1.0]))
        assert shift == 4.0
        assert scale == 1.0          # shifted range 5: 10^int(log10 5) = 1

    def test_a_constant_x_cannot_be_fitted(self):
        assert GM._fp_prepare(np.array([2.0, 2.0]))[1] == 0.0
        assert GM._fp_prepare(np.array([-1.0, -1.0])) == (0.0, 0.0)


class TestFpFitAndPrediction:
    x = np.linspace(0.5, 6.0, 40)

    @pytest.mark.parametrize("p,build", [
        ((0.0, 0.0), lambda x: 1 + 2 * np.log(x) + 0.7 * np.log(x) ** 2),
        ((-2.0, -2.0), lambda x: 3 - 1.5 * x ** -2 + 0.8 * x ** -2 * np.log(x)),
        ((-0.5, 3.0), lambda x: 1 + 0.9 * x ** -0.5 - 0.05 * x ** 3),
    ])
    def test_a_noise_free_fp2_model_is_found(self, p, build):
        # A last line asked the same of _fit_fp2, a test-only wrapper of
        # _fp_fit that WP-26 deleted (24sep2026); the first assertion is it,
        # of the function fpfit runs.
        y = build(self.x)
        fit = GM._fp_fit(self.x, y)
        assert (fit["p1"], fit["p2"]) == p
        np.testing.assert_allclose(GM._predict_fp2(self.x, fit), y, rtol=0, atol=1e-8)

    def test_the_prediction_is_the_design_times_beta_on_raw_x(self):
        y = 1 + np.log(self.x) + _RNG.normal(0, 0.1, len(self.x))
        fit = GM._fp_fit(self.x, y)
        xg = np.array([0.7, 2.0, 5.5])
        xx = (xg + fit["shift"]) / fit["scale"]
        np.testing.assert_allclose(GM._predict_fp2(xg, fit),
                                   GM._fp_design(xx, fit["p1"], fit["p2"]) @ fit["beta"],
                                   rtol=1e-14)

    def test_stdp_is_the_quadratic_form_of_the_covariance(self):
        y = 1 + np.log(self.x) + _RNG.normal(0, 0.1, len(self.x))
        fit = GM._fp_fit(self.x, y)
        xg = np.array([0.7, 2.0, 5.5])
        Xg = GM._fp_design((xg + fit["shift"]) / fit["scale"], fit["p1"], fit["p2"])
        want = np.sqrt(np.diag(Xg @ fit["cov"] @ Xg.T))
        np.testing.assert_allclose(GM._fp_stdp(xg, fit), want, rtol=1e-12)
        assert fit["df"] == len(self.x) - 3

    def test_no_model_for_a_constant_x(self):
        """No model, and nothing drawn.  Measured 24sep2026 on x = 2 for six
        observations and y = 0..5: `fracpoly regress y x' is r(498),
        "unable to identify optimal powers", and `twoway fpfit y x' and
        `twoway fpfitci y x' are rc 0 with the note "fracpoly could not fit
        model" and a serset of one observation whose fit (and band) is
        missing.  This also asked _fit_fp2, which answered a flat line at
        the mean of y (powers 1 2, beta [2.5, 0, 0]) that no render drew;
        WP-26 deleted it, and the same rows go through the mappers."""
        x, y = np.full(6, 2.0), np.arange(6.0)
        assert GM._fp_fit(x, y) is None
        src = ColumnDataSource({"x": x.tolist(), "y": y.tolist()})
        r = GM().map_fpfit(figure(), src, "y", "x", {})
        assert list(r.data_source.data["y_fp"]) == []
        line, band = GM().map_fpfitci(figure(), src, "y", "x", {})
        assert list(line.data_source.data["y_fp"]) == []
        assert list(band.data_source.data["y_lower"]) == []
        # The control: the same y over a varying x is fitted and drawn.
        ok = ColumnDataSource({"x": (x + np.arange(6.0)).tolist(),
                               "y": y.tolist()})
        assert len(GM().map_fpfit(figure(), ok, "y", "x", {})
                   .data_source.data["y_fp"]) > 0


class TestFpPlotGrid:
    def test_the_same_rows_give_every_distinct_x(self):
        x = np.array([3.0, 1.0, 1.0, 2.0])
        y = np.array([1.0, 5.0, 6.0, 7.0])
        np.testing.assert_array_equal(GM._fp_plot_grid(x, y, x, y), [1.0, 2.0, 3.0])

    def test_an_x_whose_lowest_y_row_left_the_sample_is_dropped(self):
        # twoway__fpfit_serset.ado: sort x y; keep if x != x[_n-1] over the
        # plot's rows, then fracpred predicts only if e(sample).
        x_all = np.array([1.0, 1.0, 2.0, 3.0])
        y_all = np.array([5.0, 6.0, 7.0, 8.0])
        np.testing.assert_array_equal(
            GM._fp_plot_grid(x_all, y_all, x_all[1:], y_all[1:]), [2.0, 3.0])

    def test_an_x_whose_higher_y_row_left_the_sample_stays(self):
        x_all = np.array([1.0, 1.0, 2.0, 3.0])
        y_all = np.array([5.0, 6.0, 7.0, 8.0])
        keep = np.array([True, False, True, True])
        np.testing.assert_array_equal(
            GM._fp_plot_grid(x_all, y_all, x_all[keep], y_all[keep]), [1.0, 2.0, 3.0])


# ======================================================================
# mband's and mspline's knots against Stata's own plotted points
# ======================================================================
# The WP-18 review, 23sep2026: twoway mband/mspline sersets read back from
# the saved .gph (float32, hence the 1e-6 tolerances).  An observation on a
# band edge belongs to the band ABOVE it -- band = floor((x - min) * B /
# range), the top band closed -- and np.linspace's edges put it below
# whenever the edge is not exactly representable.
_BAND_EDGES = os.path.join(os.path.dirname(__file__), "fixtures",
                           "mband_band_edges.json")


class TestCrossMediansAgainstStata:
    def test_tenths_each_in_their_own_band(self):
        # linspace's edge at .3 is 0.30000000000000004: .3 fell into the
        # band below and dash drew 8 knots where Stata draws 10.
        x = np.arange(11) / 10.0
        y = np.array([7, 3, 10, 6, 2, 9, 5, 1, 8, 4, 0], dtype=float)
        kx, ky = GM._cross_medians(x, y, 10)
        np.testing.assert_allclose(kx, [0, .1, .2, .3, .4, .5, .6, .7, .8, .95],
                                   rtol=0, atol=1e-7)
        np.testing.assert_allclose(ky, [7, 3, 10, 6, 2, 9, 5, 1, 8, 2],
                                   rtol=0, atol=1e-7)

    def test_thirds(self):
        x = np.arange(10) / 3.0
        y = np.array([(n * 5) % 7 for n in range(1, 11)], dtype=float)
        kx, ky = GM._cross_medians(x, y, 9)
        np.testing.assert_allclose(kx, [0, 1 / 3, 2 / 3, 1, 4 / 3, 5 / 3, 2,
                                        7 / 3, 2.8333333], rtol=0, atol=1e-6)
        np.testing.assert_allclose(ky, [5, 3, 1, 6, 4, 2, 0, 5, 2], rtol=0, atol=1e-7)

    @pytest.mark.parametrize("bands,key", [(20, "knots_bands20"), (7, "knots_bands7")])
    def test_two_hundred_values_rounded_to_hundredths(self, bands, key):
        import json
        with open(_BAND_EDGES, encoding="utf-8") as fh:
            d = json.load(fh)
        kx, ky = GM._cross_medians(np.array(d["x"]), np.array(d["y"]), bands)
        want = np.array(d[key])
        assert len(kx) == len(want)
        np.testing.assert_allclose(kx, want[:, 0], rtol=0, atol=1e-6)
        np.testing.assert_allclose(ky, want[:, 1], rtol=0, atol=1e-6)


class TestDefaultBandCount:
    """_gs_default_bands.ado: round(min(10*log10 N, sqrt N)), at least
    min(N, 2)."""

    @pytest.mark.parametrize("n,want", [(1, 1), (2, 2), (3, 2), (4, 2), (10, 3),
                                        (74, 9), (2246, 34)])
    def test_the_rule(self, n, want):
        assert dr._mband_default_bands(n) == want


class TestFewKnots:
    """Stata's plotted points with two knots or fewer (the WP-18 review):
    mband draws its knots at any N; mspline draws only the knots when there
    are fewer than three -- no spline, no n() points between them."""

    @staticmethod
    def _xy(mapper, x, y, opts=None):
        fig = figure()
        out = getattr(GM(), mapper)(fig, ColumnDataSource({"x": x, "y": y}),
                                    "y", "x", dict(opts or {}))
        d = (out[0] if isinstance(out, list) else out).data_source.data
        key = "x_mb" if mapper == "map_mband" else "x_sp"
        ykey = "y_mb" if mapper == "map_mband" else "y_sp"
        return (np.asarray(d[key], dtype=float).tolist(),
                np.asarray(d[ykey], dtype=float).tolist())

    @pytest.mark.parametrize("mapper", ["map_mband", "map_mspline"])
    def test_two_observations(self, mapper):
        assert self._xy(mapper, [1.0, 2.0], [3.0, 5.0]) == ([1.0, 2.0], [3.0, 5.0])

    @pytest.mark.parametrize("mapper", ["map_mband", "map_mspline"])
    def test_three_observations_make_two_bands(self, mapper):
        assert self._xy(mapper, [1.0, 2.0, 3.0], [3.0, 5.0, 4.0]) == \
            ([1.0, 2.5], [3.0, 4.5])

    @pytest.mark.parametrize("mapper", ["map_mband", "map_mspline"])
    def test_one_band_is_one_point_and_two_bands_two(self, mapper):
        x = np.arange(1.0, 11.0)
        assert self._xy(mapper, x, x ** 2, {"bands": "1"}) == ([5.5], [30.5])
        assert self._xy(mapper, x, x ** 2, {"bands": "2"}) == ([3.0, 8.0], [9.0, 64.0])

    def test_three_knots_are_a_spline_again(self):
        x = np.arange(1.0, 11.0)
        xs, _ = self._xy("map_mspline", x, x ** 2, {"bands": "3", "n": "4"})
        assert len(xs) == (3 - 1) * 4 + 3


class TestMsplineNCeiling:
    def test_n_above_300_is_reported_and_the_default_used(self):
        # twoway mspline: "n must be between 1 and 300", r(198); dash.ado
        # refuses it, and a hand-written spec gets the default and a note.
        x = np.arange(1.0, 41.0)
        with pytest.warns(UserWarning, match=r"n\(400\)"):
            xs, _ = TestFewKnots._xy("map_mspline", x, np.sqrt(x), {"n": "400"})
        k = dr._mband_default_bands(40)
        assert len(xs) == (k - 1) * 10 + k
        xs, _ = TestFewKnots._xy("map_mspline", x, np.sqrt(x), {"n": "300"})
        assert len(xs) == (k - 1) * 300 + k


# ======================================================================
# histogram, discrete: the top value folds into the last bar
# ======================================================================
# twoway__histogram_gen.ado:200-203: midbin = floor((v - min)/h), and a
# value landing one past the last bin is folded back into it (`replace
# midbin = bin-1 if midbin == bin').  With discrete the grid is min - h/2
# and int((max - min)/h + .5) bins, so a width() coarser than the data's
# spacing leaves the maximum past the last edge -- and dash dropped it:
# `histogram mpg, discrete width(3)' lost the 41-mpg car and drew every
# density bar 74/73 too tall (the WP-18 review, 23sep2026).
_AUTO_MPG = [22, 17, 22, 20, 15, 18, 26, 20, 16, 19, 14, 14, 21, 29, 16, 22,
             22, 24, 19, 30, 18, 16, 17, 28, 21, 12, 12, 14, 22, 14, 15, 18,
             14, 20, 21, 19, 19, 18, 19, 24, 16, 28, 34, 25, 26, 18, 18, 18,
             19, 19, 19, 24, 17, 23, 25, 23, 35, 24, 21, 21, 25, 28, 30, 14,
             26, 35, 18, 31, 18, 23, 41, 25, 25, 17]


def _hist(values, opts, weights=None):
    data = {"v": [float(v) for v in values]}
    if weights is not None:
        data["w"] = [float(w) for w in weights]
        opts = dict(opts, weight="fweight", wexp="w")
    r = GM().map_histogram(figure(), ColumnDataSource(data), "v", dict(opts))
    d = r.data_source.data
    return (np.asarray(d["top"], dtype=float), np.asarray(d["left"], dtype=float),
            np.asarray(d["right"], dtype=float), r)


class TestHistogramDiscreteTopBar:
    def test_auto_mpg_width_3_frequency_is_statas(self):
        tops, left, right, _ = _hist(_AUTO_MPG, {"discrete": "discrete", "width": "3",
                                                 "frequency": "frequency"})
        # twoway__histogram_gen mpg, discrete width(3) frequency: r(bin) 10,
        # r(min) 10.5, r(max) 40.5, heights 2 12 21 13 12 6 4 1 2 1.
        np.testing.assert_array_equal(tops, [2, 12, 21, 13, 12, 6, 4, 1, 2, 1])
        assert left[0] == 10.5 and right[-1] == 40.5
        assert tops.sum() == 74

    def test_auto_mpg_width_3_density_is_statas(self):
        tops, *_ = _hist(_AUTO_MPG, {"discrete": "discrete", "width": "3"})
        np.testing.assert_allclose(
            tops, [.009009, .0540541, .0945946, .0585586, .0540541, .027027,
                   .018018, .0045045, .009009, .0045045], rtol=1e-5)

    def test_an_uneven_spacing_folds_too(self):
        # twoway__histogram_gen v, discrete frequency on 0, 1, 2.6, 2.6:
        # width 1, three bins from -.5, and 2.6 -- floor 3 -- in the third.
        tops, *_ = _hist([0, 1, 2.6, 2.6], {"discrete": "discrete",
                                            "frequency": "frequency"})
        np.testing.assert_array_equal(tops, [1, 1, 2])

    def test_a_folded_value_keeps_its_frequency_weight(self):
        tops, *_ = _hist([0, 1, 2.6, 2.6], {"discrete": "discrete",
                                            "frequency": "frequency"},
                         weights=[1, 1, 2, 3])
        np.testing.assert_array_equal(tops, [1, 1, 5])


# ======================================================================
# The saved page's JavaScript recount, run under node (test/js_runner.py,
# WP-28 S03).  ``_NODE`` and ``_run_filter_js_block`` stay as aliases of
# the shared module's ``NODE``/``run_filter_js_block``: S05's
# test_histogram_edge_rule.py imports both by these spellings.
# ======================================================================
from js_runner import (run_filter_js_block as _run_filter_js_block,  # noqa: E402,E501
                       requires_node, NODE as _NODE)


@requires_node
class TestFilterJavaScript:
    def test_the_discrete_recount_folds_the_top_value_as_python_does(self):
        tops, _, _, r = _hist(_AUTO_MPG, {"discrete": "discrete", "width": "3",
                                          "frequency": "frequency"})
        ac = r._dash_agg_config
        assert ac.get("discrete") is True
        got = _run_filter_js_block("histogram", ac, _AUTO_MPG)
        np.testing.assert_array_equal(got["top"], tops)

    def test_a_weighted_discrete_recount_folds_the_weight_too(self):
        tops, _, _, r = _hist([0, 1, 2.6, 2.6], {"discrete": "discrete",
                                                 "frequency": "frequency"},
                              weights=[1, 1, 2, 3])
        got = _run_filter_js_block("histogram", r._dash_agg_config,
                                   [0, 1, 2.6, 2.6], [1, 1, 2, 3])
        np.testing.assert_array_equal(got["top"], [1, 1, 5])
        np.testing.assert_array_equal(got["top"], tops)

    def test_a_kdensity_on_a_constant_subset_is_cleared_not_left_stale(self):
        # Python draws nothing on constant data; the JavaScript left the
        # previous curve on screen (`continue' before touching the source).
        r = GM().map_kdensity(figure(), ColumnDataSource({"v": [1.0, 2.0, 5.0, 7.0]}),
                              "v", {})
        got = _run_filter_js_block("kdensity", r._dash_agg_config, [3.0, 3.0, 3.0])
        assert got == {"x": [], "y": []}


class TestAStringWeightIsNotFatal:
    def test_a_non_numeric_weight_column_is_named_and_not_applied(self):
        # dash.ado refuses a string weight (twoway's r(109) "type mismatch");
        # a hand-written spec reached the renderer and crashed it.
        src = ColumnDataSource({"x": [1.0, 2.0, 3.0], "y": [2.0, 4.0, 7.0],
                                "w": ["a", "b", "c"]})
        dr._dash_reset_notes()
        with pytest.warns(UserWarning, match="not numeric"):
            x, y, w, wt = GM._layer_weights(src, None,
                                            {"weight": "aweight", "wexp": "w"},
                                            "lfit", "x", "y")
        np.testing.assert_array_equal(x, [1, 2, 3])
        assert w is None and wt is None


class TestHistogramOfOneValue:
    """twoway__histogram_gen.ado:98-100: every value equal and no width()
    gives width 1, so one bar from the value to the value + 1 (measured by
    the WP-18 review: v = 5 on 10 rows, r(bin) 1, r(min) 5, r(max) 6, a
    density of 1).  dash spread three bars of width |v|/3."""

    def test_one_bar_of_width_one(self):
        tops, left, right, _ = _hist([5.0] * 10, {})
        np.testing.assert_array_equal(left, [5.0])
        np.testing.assert_array_equal(right, [6.0])
        np.testing.assert_allclose(tops, [1.0])

    def test_bin_is_moot_when_every_value_is_equal(self):
        tops, left, right, _ = _hist([5.0] * 10, {"bin": "10", "frequency": "frequency"})
        np.testing.assert_array_equal(left, [5.0])
        np.testing.assert_array_equal(tops, [10.0])


# ======================================================================
# lowess at its edges, against Stata (the WP-18 review, 23sep2026)
# ======================================================================
_AUTO_WEIGHT = [2930, 3350, 2640, 3250, 4080, 3670, 2230, 3280, 3880, 3400,
                4330, 3900, 4290, 2110, 3690, 3180, 3220, 2750, 3430, 2120,
                3600, 3600, 3740, 1800, 2650, 4840, 4720, 3830, 2580, 4060,
                3720, 3370, 4130, 2830, 4060, 3310, 3300, 3690, 3370, 2730,
                4030, 3260, 1800, 2200, 2520, 3330, 3700, 3470, 3210, 3200,
                3420, 2690, 2830, 2070, 2650, 2370, 2020, 2280, 2750, 2130,
                2240, 1760, 1980, 3420, 1830, 2050, 2410, 2200, 2670, 2160,
                2040, 1930, 1990, 3170]
_AUTO_FOREIGN = [0] * 52 + [1] * 22

# Twenty observations, ten tied at x = 1: `twoway lowess y x, bwidth(.2)'.
_Q1_X = [1.0] * 10 + [float(v) for v in range(2, 12)]
_Q1_Y = [float((n * 7) % 11) for n in range(1, 21)]


def _lowess_xy(x, y, opts, view=None, dataset=None):
    import pandas as pd
    gm = GM()
    if dataset is not None:
        gm.dataset = pd.DataFrame(dataset)
    r = gm.map_lowess(figure(), ColumnDataSource({"x": list(x), "y": list(y)}),
                      "y", "x", dict(opts), view=view)
    d = r.data_source.data
    return (np.asarray(d["x_lw"], dtype=float), np.asarray(d["y_lw"], dtype=float))


class TestLowessEdgesAgainstStata:
    def test_adjust_divides_by_the_mean_of_y_over_every_observation(self):
        # lowess.ado:207 runs `summ y, mean' with no if: the mean of y over
        # everything in memory, not over the smoothed sample.  twoway lowess
        # mpg weight if foreign, adjust -- its serset, read back:
        want_y = [23.1156485066745, 23.13026068298208, 24.3907695147686,
                  25.32910523204783, 25.27355037578206, 25.18587492582939,
                  24.71173792831581, 24.53493329397701, 23.78106473034507,
                  23.23089350912642, 22.93617326579328, 22.65783214743154,
                  22.49930368871291, 22.38005744001726, 20.85171712248686,
                  19.73487023155991, 17.63179258654797, 17.49170218967753,
                  16.93728186894514, 16.49375818666353, 14.02851554543624,
                  12.21369756741956]
        from bokeh.models import BooleanFilter, CDSView
        view = CDSView(filter=BooleanFilter(booleans=[bool(f) for f in _AUTO_FOREIGN]))
        x, y = _lowess_xy(_AUTO_WEIGHT, _AUTO_MPG, {"adjust": "adjust"}, view=view,
                          dataset={"x": _AUTO_WEIGHT, "y": _AUTO_MPG})
        np.testing.assert_array_equal(x, sorted(w for w, f in zip(_AUTO_WEIGHT, _AUTO_FOREIGN) if f))
        np.testing.assert_allclose(y, want_y, rtol=1e-9)

    def test_adjust_counts_y_where_x_is_missing(self):
        # lowess mpg weight, adjust with weight missing in 1/10: the ratio
        # adjusted/unadjusted is .9773663 on all 64 smoothed points.
        w = [np.nan] * 10 + _AUTO_WEIGHT[10:]
        data = {"x": w, "y": _AUTO_MPG}
        _, adj = _lowess_xy(w, _AUTO_MPG, {"adjust": "adjust"}, dataset=data)
        _, raw = _lowess_xy(w, _AUTO_MPG, {}, dataset=data)
        assert len(adj) == 64
        np.testing.assert_allclose(adj / raw, 0.9773663, rtol=1e-7)

    def test_a_window_with_no_x_spread_is_missing_and_not_drawn(self):
        # twoway's serset: missing at the first nine tied rows (their
        # three-row windows are all x = 1), then 6 0 7 3 10 6 2 9 5 1 8.
        x, y = _lowess_xy(_Q1_X, _Q1_Y, {"bwidth": ".2"})
        np.testing.assert_array_equal(x, [1.0] + [float(v) for v in range(2, 12)])
        np.testing.assert_allclose(y, [6, 0, 7, 3, 10, 6, 2, 9, 5, 1, 8],
                                   rtol=0, atol=1e-8)

    def test_logit_turns_a_missing_smooth_into_1_minus_1_over_n(self):
        # lowess yb x, bwidth(.2) logit: Stata's `ys > 1 - small' is true
        # for a missing smooth, so the nine become ln((1-1/20)/(1/20)).
        yb = [v / 11.0 for v in _Q1_Y]
        x, y = _lowess_xy(_Q1_X, yb, {"bwidth": ".2", "logit": "logit"})
        np.testing.assert_array_equal(x, _Q1_X)
        want = [math.log(19.0)] * 9 + [.18232156, -2.944439, .55961579, -.98082925,
                                       2.3025851, .18232156, -1.5040774, 1.5040774,
                                       -.18232156, -2.3025851, math.log(8 / 3)]
        np.testing.assert_allclose(y, want, rtol=0, atol=1e-6)

    def test_fewer_than_three_observations_or_no_spread_draws_nothing(self):
        # lowess.ado:89: r(N) >= 3 & r(max) - r(min) >= 1e-30.
        assert len(_lowess_xy([1.0, 2.0], [3.0, 5.0], {})[0]) == 0
        assert len(_lowess_xy([0.1] * 74, _AUTO_MPG, {})[0]) == 0
        # N = 3 at the default bandwidth: k = 0, every window one row wide,
        # no spread -- the running line is missing everywhere; the running
        # mean is each row's own y.
        assert len(_lowess_xy([1.0, 2.0, 3.0], [3.0, 5.0, 4.0], {})[0]) == 0
        x, y = _lowess_xy([1.0, 2.0, 3.0], [3.0, 5.0, 4.0], {"mean": "mean"})
        np.testing.assert_array_equal(y, [3.0, 5.0, 4.0])

    def test_adjust_on_a_smooth_whose_mean_is_zero(self):
        # y = 0 on auto: adjust divides by zero, every value missing -- no
        # line; with logit each missing value becomes ln(73), N = 74.
        zeros = [0.0] * 74
        assert len(_lowess_xy(_AUTO_WEIGHT, zeros, {"adjust": "adjust"})[0]) == 0
        x, y = _lowess_xy(_AUTO_WEIGHT, zeros, {"adjust": "adjust", "logit": "logit"})
        assert len(y) == 74
        np.testing.assert_allclose(y, math.log(73.0), rtol=1e-12)
        _, y = _lowess_xy(_AUTO_WEIGHT, zeros, {"logit": "logit"})
        np.testing.assert_allclose(y, -math.log(73.0), rtol=1e-12)


# ======================================================================
# lpoly's grid and its degree, against Stata (the WP-18 review, 23sep2026)
# ======================================================================
_AUTO_PRICE = [4099, 4749, 3799, 4816, 7827, 5788, 4453, 5189, 10372, 4082,
               11385, 14500, 15906, 3299, 5705, 4504, 5104, 3667, 3955, 3984,
               4010, 5886, 6342, 4389, 4187, 11497, 13594, 13466, 3829, 5379,
               6165, 4516, 6303, 3291, 8814, 5172, 4733, 4890, 4181, 4195,
               10371, 4647, 4425, 4482, 6486, 4060, 5798, 4934, 5222, 4723,
               4424, 4172, 9690, 6295, 9735, 6229, 4589, 5079, 8129, 4296,
               5799, 4499, 3995, 12990, 3895, 3798, 5899, 3748, 5719, 7140,
               5397, 4697, 6850, 11995]
_N = None
_AUTO_REP78 = [3, 3, _N, 3, 4, 3, _N, 3, 3, 3, 3, 2, 3, 3, 4, 3, 2, 2, 3, 5,
               2, 2, 2, 4, 3, 3, 3, 3, 4, 4, 3, 3, 4, 3, 4, 3, 3, 4, 3, 1, 3,
               3, 5, 3, _N, 2, 4, 1, 3, 3, _N, 2, 5, 3, 4, 4, 5, 4, 4, 3, 5, 4,
               4, _N, 3, 5, 5, 5, 5, 4, 5, 4, 4, 5]
_AUTO_REP78 = [np.nan if v is None else float(v) for v in _AUTO_REP78]


def _lp_xy(mapper, x, y, opts, view=None, dataset_rows=None):
    import pandas as pd
    gm = GM()
    if dataset_rows is not None:
        gm.dataset = pd.DataFrame({"row": np.arange(dataset_rows)})
    fig = figure()
    getattr(gm, mapper)(fig, ColumnDataSource({"x": list(x), "y": list(y)}),
                        "y", "x", dict(opts), view=view)
    for r in fig.renderers:
        d = r.data_source.data
        if "x_lp" in d and "y_lp" in d:
            return np.asarray(d["x_lp"], dtype=float), np.asarray(d["y_lp"], dtype=float)
    raise AssertionError("no lpoly line")


class TestLpolyGridAgainstStata:
    """twoway_lpoly_parse.class:56 sets n = _N when the DATASET has fewer
    than 50 rows, overriding n(); lpoly.ado:283-290 then takes n() or 50
    and caps it at _N.  _N is every row in memory, not the plot's sample:
    dash used min(sample N, 50) and never capped n()."""

    @pytest.mark.parametrize("mapper", ["map_lpoly", "map_lpolyci"])
    def test_a_subset_is_drawn_on_the_datasets_fifty_point_grid(self, mapper):
        import json
        from bokeh.models import BooleanFilter, CDSView
        with open(os.path.join(os.path.dirname(__file__), "fixtures",
                               "qualified_stat_truth.json"), encoding="utf-8") as fh:
            f1 = json.load(fh)["layers"]["lpoly"]["foreign1"]
        # twoway lpoly mpg weight if foreign==1: 22 cars, a 50-point grid
        # over their range, 28 non-missing points ending at 2810.2.  At
        # Stata's own bandwidth (dash's rule of thumb is not Stata's).
        view = CDSView(filter=BooleanFilter(booleans=[bool(v) for v in _AUTO_FOREIGN]))
        x, y = _lp_xy(mapper, _AUTO_WEIGHT, _AUTO_MPG,
                      {"bwidth": repr(f1["estimation"]["bwidth"])},
                      view=view, dataset_rows=74)
        np.testing.assert_allclose(x, f1["plotted"]["lp_x"], rtol=1e-12)
        np.testing.assert_allclose(y, f1["plotted"]["lp_y"], rtol=1e-9)

    def test_n_above_the_datasets_rows_is_capped_at_them(self):
        # `lpoly ..., n(100)' on auto: "(n() set to 74)".
        x, _ = _lp_xy("map_lpoly", _AUTO_WEIGHT, _AUTO_MPG,
                      {"bwidth": "2000", "n": "100"}, dataset_rows=74)
        assert len(x) == 74

    def test_below_fifty_rows_the_grid_is_every_row_whatever_n_says(self):
        xs, ys = _AUTO_WEIGHT[:30], _AUTO_MPG[:30]
        for opts in ({"bwidth": "2000", "n": "10"}, {"bwidth": "2000"}):
            x, _ = _lp_xy("map_lpoly", xs, ys, opts, dataset_rows=30)
            assert len(x) == 30, opts


class TestLpolyDegreeAgainstStata:
    """Where the positive-weight observations have no more distinct x than
    the degree, Stata fits the degree they support (it drops the top
    powers); numpy's polyfit returned an arbitrary least-norm answer.
    lpoly price rep78, n(50) on auto -- rep78 takes five values."""

    def test_degree_1_on_a_window_with_one_value_is_its_mean(self):
        want = [4564.5, 4564.5, 4564.5, 4564.5, 4564.5, 5137.204081633,
                5251.744897959, 5366.285714286, 5480.826530612, 5967.625,
                5967.625, 5967.625, 5967.625, 5967.625, 5967.625, 5967.625,
                5967.625, 6146.615986395, 6184.29829932, 6221.980612245,
                6259.66292517, 6429.233333333, 6429.233333333, 6429.233333333,
                6429.233333333, 6429.233333333, 6429.233333333, 6429.233333333,
                6429.233333333, 6297.821088435, 6268.618367347, 6239.415646259,
                6210.21292517, 6071.5, 6071.5, 6071.5, 6071.5, 6071.5, 6071.5,
                6071.5, 6071.5, 6016.510204082, 6003.571428571, 5990.632653061,
                5977.693877551, 5913.0, 5913.0, 5913.0, 5913.0, 5913.0]
        x, y = _lp_xy("map_lpoly", _AUTO_REP78, _AUTO_PRICE,
                      {"degree": "1", "bwidth": ".3", "n": "50"}, dataset_rows=74)
        assert len(x) == 50
        np.testing.assert_allclose(y, want, rtol=0, atol=1e-6)

    def test_degree_2_on_a_window_with_two_values_is_a_line(self):
        want = [4564.5, 4679.040816327, 4793.581632653, 4908.12244898,
                5022.663265306, 5137.204081633, 5251.744897959, 5366.285714286,
                5480.826530612, 5687.126988755, 5780.492503124, 5867.58385395,
                5948.401041233, 6022.944064973, 6091.21292517, 6153.207621824,
                6208.928154935, 6146.615986395, 6184.29829932, 6221.980612245,
                6259.66292517, 6380.951530612, 6401.57133486, 6416.731136332,
                6426.430935027, 6430.670730945, 6429.450524087, 6422.770314452,
                6410.630102041, 6297.821088435, 6268.618367347, 6239.415646259,
                6210.21292517, 6159.850478967, 6134.464806331, 6110.406802721,
                6087.676468138, 6066.273802582, 6046.198806053, 6027.451478551,
                6010.031820075, 6016.510204082, 6003.571428571, 5990.632653061,
                5977.693877551, 5964.755102041, 5951.816326531, 5938.87755102,
                5925.93877551, 5913.0]
        x, y = _lp_xy("map_lpoly", _AUTO_REP78, _AUTO_PRICE,
                      {"degree": "2", "bwidth": ".6", "n": "50"}, dataset_rows=74)
        assert len(x) == 50
        np.testing.assert_allclose(y, want, rtol=0, atol=1e-6)


# ======================================================================
# fpfit / fpfitci on edge cases, against Stata's plotted points
# ======================================================================
# fixtures/fp_edge_truth.json (the WP-18 review, 23sep2026).  The band's
# covariance was s2 * inv(X'WX), which squares the condition number, so a
# date-time x (a large offset against its range) lost the band -- 0.09x to
# 1.2x Stata's half-width on hourly %tc -- and an x with two values, whose
# design is singular, had the wrong df and a band of width zero.  N = 2 or
# 3 and collapsed fweights drew nothing where Stata draws; a constant y, a
# negative weight and a non-integer fweight drew where Stata draws nothing.
_FP_EDGE = os.path.join(os.path.dirname(__file__), "fixtures", "fp_edge_truth.json")
# Ill-conditioned designs: a date-time x, or x offset by 1e6.  There
# Stata's own power choice rests on its rounding: on xoff it picks (-1,-1)
# where the residual sums of squares, computed to 60 digits, rank (-2,-2)
# first (800.86442 against 800.88519) -- dash's choice.  The curves differ
# by up to 5e-4 of their span (measured); the tolerance below is for that.
_FP_DATES = {"tc", "tc2", "d30", "d90", "daily", "xoff"}


def _fp_case(name):
    import json
    with open(_FP_EDGE, encoding="utf-8") as fh:
        return json.load(fh)["cases"][name]


def _fp_run(case):
    data = {"y": [np.nan if v is None else v for v in case["y"]],
            "x": [np.nan if v is None else v for v in case["x"]]}
    opts = {}
    if "w" in case:
        data["w"] = [np.nan if v is None else v for v in case["w"]]
        opts = {"weight": case["wtype"], "wexp": "w"}
    gm = GM()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fp = gm.map_fpfit(figure(), ColumnDataSource(data), "y", "x", dict(opts))
        ci = gm.map_fpfitci(figure(), ColumnDataSource(data), "y", "x", dict(opts))
    d1, d2 = fp.data_source.data, ci[0].data_source.data
    return ({k: np.asarray(d1[k], dtype=float) for k in ("x_fp", "y_fp")},
            {k: np.asarray(d2[k], dtype=float)
             for k in ("x_fp", "y_fp", "y_lower", "y_upper")})


@pytest.mark.parametrize("name", ["tc", "tc2", "d30", "d90", "daily", "bin0",
                                  "binx", "n2", "n3", "fw3", "yc", "awneg",
                                  "fwn", "xoff"])
def test_fpfit_and_fpfitci_edge_cases_against_stata(name):
    case = _fp_case(name)
    fp, ci = _fp_run(case)
    sfp, sci = case["stata"]["fp"], case["stata"]["ci"]
    if not sfp["fit"]:
        assert len(fp["x_fp"]) == 0 and len(ci["x_fp"]) == 0, \
            "twoway draws nothing here; dash drew %d points" % len(fp["x_fp"])
        return
    fit = np.asarray(sfp["fit"], dtype=float)
    span = max(float(np.ptp(fit)), 1e-12)
    # the sersets are float32; on date-time x Stata's own power choice rests
    # on its collinearity check and can differ, moving the curve by up to
    # 5e-4 of its span (measured) -- a tolerance for that, not a pass
    rel = 1e-3 if name in _FP_DATES else 1e-6
    tol = rel * span + 2e-7 * float(np.max(np.abs(fit)))
    np.testing.assert_array_equal(fp["x_fp"], sfp["fit_x"])
    np.testing.assert_allclose(fp["y_fp"], fit, rtol=0, atol=tol)
    np.testing.assert_array_equal(ci["x_fp"], sci["fit_x"])
    np.testing.assert_allclose(ci["y_fp"], np.asarray(sci["fit"], dtype=float),
                               rtol=0, atol=tol)
    lower = np.array([np.nan if v is None else v for v in sci["lower"]], dtype=float)
    upper = np.array([np.nan if v is None else v for v in sci["upper"]], dtype=float)
    # where Stata has no band (df 0) dash draws none
    np.testing.assert_array_equal(np.isnan(ci["y_lower"]), np.isnan(lower))
    have = ~np.isnan(lower)
    if have.any():
        half = np.maximum(upper[have] - fit[have], 1e-12)
        btol = (2e-3 if name in _FP_DATES else 1e-5) * half + tol
        assert np.all(np.abs(ci["y_lower"][have] - lower[have]) <= btol)
        assert np.all(np.abs(ci["y_upper"][have] - upper[have]) <= btol)


# ======================================================================
# qfit / qfitci and the weight rules (the WP-18 review, 23sep2026)
# ======================================================================
def _fit_line(mapper, x, y, opts=None, w=None, wtype=None):
    data = {"x": list(x), "y": list(y)}
    opts = dict(opts or {})
    if w is not None:
        data["w"] = list(w)
        opts.update(weight=wtype, wexp="w")
    fig = figure()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        out = getattr(GM(), mapper)(fig, ColumnDataSource(data), "y", "x", opts)
    r = out[0] if isinstance(out, list) else out
    return {k: np.asarray(v, dtype=float) for k, v in r.data_source.data.items()
            if k != "index"}


class TestQuadraticFitsAgainstStata:
    # x with two values: regress keeps one of x and x^2 beside the
    # constant.  On these, 1.3 and 1.7, it omits x -- "note: x omitted
    # because of collinearity", y = -.66875 + 1.875 x^2 -- and twoway
    # qfitci, n(5) plots the serset below (measured 24sep2026 with the
    # console binary).  This class said qfit and qfitci were lfit and lfitci
    # here (x^2 omitted), which twoway does only when |a + b| <= 1
    # (_qfit_design; test_layer_reports.py).
    X2 = [1.3, 1.3, 1.7, 1.7, 1.7, 1.3, 1.7]
    Y2 = [2.0, 3.0, 4.5, 4.0, 5.5, 2.5, 5.0]
    Q2_FIT = [2.5, 3.00625, 3.55, 4.13125, 4.75]
    Q2_LO = [1.621979, 2.304605, 2.962462, 3.52941, 3.989612]
    Q2_HI = [3.378021, 3.707895, 4.137538, 4.733091, 5.510389]

    def test_qfitci_on_two_values_is_twoways(self):
        q = _fit_line("map_qfitci", self.X2, self.Y2, {"n": "5"})
        np.testing.assert_allclose(q["x_fit"], [1.3, 1.4, 1.5, 1.6, 1.7])
        np.testing.assert_allclose(q["y_fit"], self.Q2_FIT, rtol=1e-6)
        np.testing.assert_allclose(q["y_lower"], self.Q2_LO, rtol=1e-6)
        np.testing.assert_allclose(q["y_upper"], self.Q2_HI, rtol=1e-6)

    def test_qfit_on_two_values_is_twoways(self):
        q = _fit_line("map_qfit", self.X2, self.Y2, {"n": "5"})
        np.testing.assert_allclose(q["y"], self.Q2_FIT, rtol=1e-6)
        # ... and not lfit's line, which it was.
        l = _fit_line("map_lfit", self.X2, self.Y2, {"n": "5"})
        assert not np.allclose(q["y"], l["y"])

    def test_qfit_draws_qfitcis_own_line(self):
        rng = np.random.default_rng(11)
        x = rng.uniform(1800, 4800, 40)
        y = 40 - 0.01 * x + 1e-6 * x * x + rng.normal(0, 1, 40)
        np.testing.assert_allclose(_fit_line("map_qfit", x, y)["y"],
                                   _fit_line("map_qfitci", x, y)["y_fit"], rtol=1e-12)

    def test_three_observations_draw_the_fit_and_no_band(self):
        # df = N - 3 = 0: twoway draws the fit and no band.  _t_ppf(df=0)
        # raised, and took the whole dashboard with it.
        q = _fit_line("map_qfitci", [1.0, 2.0, 4.0], [3.0, 5.0, 4.0])
        assert len(q["y_fit"]) == 100 and np.isfinite(q["y_fit"]).all()
        assert np.isnan(q["y_lower"]).all() and np.isnan(q["y_upper"]).all()


class TestWeightValueRules:
    X = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    Y = [2.0, 3.5, 3.0, 5.0, 6.5, 6.0, 8.0, 9.5]

    def test_a_negative_weight_on_lfit_leaves_its_row_out(self):
        # twoway lfit with a negative aweight fits as if `if w > 0'.
        w = [1.0, 2.0, -1.0, 1.0, 3.0, 1.0, 2.0, 1.0]
        dr._dash_reset_notes()
        with pytest.warns(UserWarning, match="excluded, as twoway excludes them"):
            got = _fit_line_warned("map_lfit", self.X, self.Y, w, "aweight")
        keep = [i for i, v in enumerate(w) if v > 0]
        want = _fit_line("map_lfit", [self.X[i] for i in keep],
                         [self.Y[i] for i in keep], w=[w[i] for i in keep],
                         wtype="aweight")
        np.testing.assert_allclose(got["y"], want["y"], rtol=1e-12)

    @pytest.mark.parametrize("mapper,key", [("map_fpfit", "y_fp"), ("map_lpoly", "y_lp"),
                                            ("map_kdensity", "y")])
    def test_a_negative_weight_elsewhere_draws_nothing(self, mapper, key):
        # fpfit: fracpoly cannot fit it (twoway draws nothing); lpoly and
        # kdensity: twoway refuses it, r(402), which dash.ado reproduces.
        w = [1.0, 2.0, -1.0, 1.0, 3.0, 1.0, 2.0, 1.0]
        dr._dash_reset_notes()
        with pytest.warns(UserWarning, match="negative weight"):
            got = _fit_line_warned(mapper, self.X, self.Y, w, "aweight")
        assert len(got[key]) == 0

    @pytest.mark.parametrize("mapper,key", [("map_qfit", "y"), ("map_qfitci", "y_fit"),
                                            ("map_fpfit", "y_fp"), ("map_lfit", "y")])
    def test_a_non_integer_fweight_draws_nothing(self, mapper, key):
        # qfit, qfitci, fpfit, fpfitci: regress/fracpoly "could not fit
        # model", twoway draws nothing; lfit: twoway refuses it, r(401).
        w = [1.0, 2.0, 1.5, 1.0, 3.0, 1.0, 2.0, 1.0]
        dr._dash_reset_notes()
        with pytest.warns(UserWarning, match="non-integer|noninteger"):
            got = _fit_line_warned(mapper, self.X, self.Y, w, "fweight")
        assert len(got[key]) == 0

    def test_stdf_with_an_aweight_draws_the_fit_and_no_band(self):
        # twoway: "not possible with weighted data", r(135) -- dash.ado
        # refuses it; a hand-written spec gets the fit and a note.
        w = [1.0, 2.0, 1.0, 1.0, 3.0, 1.0, 2.0, 1.0]
        dr._dash_reset_notes()
        with pytest.warns(UserWarning, match="not possible with weighted data"):
            got = _fit_line_warned("map_lfitci", self.X, self.Y, w, "aweight",
                                   {"stdf": "stdf"})
        assert np.isfinite(got["y_fit"]).all()
        assert np.isnan(got["y_lower"]).all()


def _fit_line_warned(mapper, x, y, w, wtype, opts=None):
    """_fit_line without swallowing warnings, for pytest.warns."""
    data = {"x": list(x), "y": list(y), "w": list(w)}
    opts = dict(opts or {}, weight=wtype, wexp="w")
    if mapper == "map_kdensity":
        out = GM().map_kdensity(figure(), ColumnDataSource(data), "y", opts)
    else:
        out = getattr(GM(), mapper)(figure(), ColumnDataSource(data), "y", "x", opts)
    r = out[0] if isinstance(out, list) else out
    return {k: np.asarray(v, dtype=float) for k, v in r.data_source.data.items()
            if k != "index"}


class TestTheServedAppCarriesEveryName:
    def test_every_module_name_glyphmapper_reads_is_defined_in_the_app(self):
        # The served app copies GlyphMapper by source; a module-level helper
        # or constant it calls and the builder does not copy is a NameError
        # on the served page at DRAW time, not at build time.  This caught
        # _qfit_design and two weight tables during the WP-18 review.
        import ast
        import builtins
        import inspect
        import json
        import tempfile
        tree = ast.parse(inspect.getsource(dr.GlyphMapper))
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        wanted = {n for n in names if hasattr(dr, n) and not hasattr(builtins, n)
                  and not inspect.ismodule(getattr(dr, n))}
        # The set must actually have been collected: an empty or tiny
        # `wanted' makes `wanted - defined' empty and the check below pass
        # having verified nothing.  GlyphMapper references 63 module-level
        # names the app must carry (measured 24sep2026); a handful of them
        # are load-bearing and named explicitly so a broken walk cannot
        # slip through as a vacuous pass.
        assert len(wanted) >= 40, sorted(wanted)
        for critical in ("SchemeParser", "ColumnDataSource", "OptionTranslator",
                         "_dash_warn_once", "_N_BOOT_DEFAULT"):
            assert critical in wanted, (critical, sorted(wanted))
        spec = {"graphs": [{"plots": [{"type": "scatter", "yvar": "y", "xvar": "x",
                                        "options": {}}],
                            "graph_options": {"name": "g1"}}],
                "kpis": [], "build_options": {"layout": "auto", "registry": "g1"}}
        data = {"StataJSON": {"variableNames": ["x", "y"], "variableLabels": {},
                              "valueLabels": {}, "valueLabelNames": {},
                              "variableTypeIsString": {"x": False, "y": False},
                              "values": [{"x": 1.0, "y": 2.0}, {"x": 2.0, "y": 3.0}]}}
        with tempfile.TemporaryDirectory() as d:
            sp, dp, op = (os.path.join(d, f) for f in ("s.json", "d.json", "a.py"))
            with open(sp, "w") as fh:
                json.dump(spec, fh)
            with open(dp, "w") as fh:
                json.dump(data, fh)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                dr.ServerAppBuilder(sp, dp).build(op)
            with open(op, encoding="utf-8") as fh:
                app = ast.parse(fh.read())
        defined = set()
        # WP-30 P1.32: the header's package imports sit inside top-level
        # `try' blocks that stop in one line naming dash_setup.
        body = []
        for node in app.body:
            body += node.body if isinstance(node, ast.Try) else [node]
        for node in body:
            if isinstance(node, ast.Assign):
                defined |= {t.id for t in node.targets if isinstance(t, ast.Name)}
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                defined.add(node.target.id)
            elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                defined.add(node.name)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                defined |= {(a.asname or a.name).split(".")[0] for a in node.names}
        assert not sorted(wanted - defined), sorted(wanted - defined)

    def test_every_listed_name_exists(self):
        # WP-30 A149: _glyph_layer_lines copies each listed constant and
        # function through getattr(_mod, _name, None) and SKIPS a name
        # dash_render.py does not define, so a misspelt, renamed or deleted
        # entry fails only on the served page.  Every name in both copy
        # lists must be defined, and listed once.
        import ast
        import inspect
        import textwrap
        tree = ast.parse(textwrap.dedent(
            inspect.getsource(dr.ServerAppBuilder._glyph_layer_lines)))
        lists = {}
        for node in ast.walk(tree):
            if (isinstance(node, ast.For)
                    and isinstance(node.target, ast.Name)
                    and isinstance(node.iter, ast.Tuple)
                    and all(isinstance(e, ast.Constant)
                            and isinstance(e.value, str)
                            for e in node.iter.elts)):
                lists.setdefault(node.target.id, []).extend(
                    e.value for e in node.iter.elts)
        # The constants (_name) and the functions (_fn_name): 145 and 312
        # at c96facd.  A walk that finds nothing must not pass as a check.
        assert sorted(lists) == ["_fn_name", "_name"], sorted(lists)
        assert len(lists["_name"]) >= 140, len(lists["_name"])
        assert len(lists["_fn_name"]) >= 300, len(lists["_fn_name"])
        for kind, names in sorted(lists.items()):
            missing = sorted(n for n in set(names) if not hasattr(dr, n))
            assert not missing, (kind, missing)
            twice = sorted(n for n in set(names) if names.count(n) > 1)
            assert not twice, (kind, twice)
