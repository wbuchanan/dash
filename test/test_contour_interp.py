"""twoway contour's surface: grid, duplicates, interpolation, cap (WP-31 B4a).

The helpers are the numerical half of contour and contourline: the grid
twoway draws on (the distinct x by the distinct y of the data), the
duplicate rule (the smallest z of a repeated (y, x) pair), Stata's
thin-plate spline (kernel r^2 log r with a degree-1 trend) and Shepard's
1/d^2 mean, interp(none), and the bounded fallback above
_DASH_CONTOUR_EXACT_MAX distinct points.  Nothing draws them yet (B4b).

Truth: test/fixtures/contour_truth.json, written by
scripts/extract_contour_truth.do from twoway's own generator
(_contour_heatmap, _contour_filled, _contour_line).
"""
import ast
import inspect
import json
import math
import os
import re
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import dash_render as dr  # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))
_FIXTURE = os.path.join(_HERE, "fixtures", "contour_truth.json")
_NAMES = ("_dash_contour_points", "_dash_tps_fit", "_dash_tps_eval",
          "_dash_shepard", "_dash_contour_grid", "_dash_contour_fallback_grid",
          "_dash_contour_interp", "_dash_contour_surface")
_CONSTANTS = ("_DASH_CONTOUR_EXACT_MAX", "_DASH_CONTOUR_FALLBACK_N",
              "_DASH_CONTOUR_INTERPS")


@pytest.fixture(scope="module")
def truth():
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _scatter(n, seed=7):
    rng = np.random.default_rng(seed)
    return rng.uniform(0, 10, n), rng.uniform(0, 5, n), rng.normal(size=n)


def _nodes_of(case, gx, gy):
    """(row, column) of each node rectangle's grid node, and the rect."""
    hm = case["nodes"]
    ix = np.searchsorted(gx, np.asarray(hm["x0"]), side="left")
    iy = np.searchsorted(gy, np.asarray(hm["y0"]), side="left")
    return iy, ix, hm


def _levels(z, cuts):
    # twoway's level ids: 1 below the first cut, a value on a cut goes up.
    return np.searchsorted(np.asarray(cuts, dtype=float), z, side="right") + 1


def _tolerance(note):
    # Relative agreement with twoway: 1e-9 on a well-conditioned system;
    # 1e-6 where twoway's own solve leaves a direction out (auto: its nodes
    # and Mata's qrsolve(), svsolve() and pinv() spread over 1e-7).
    return 1e-6 if note == "singular" else 1e-9


def _twoways_input(case):
    """The fixture's de-duplicated input (the smallest z per (y, x))."""
    inp = case["input"]
    return (np.asarray(inp["x"]), np.asarray(inp["y"]), np.asarray(inp["z"]))


# ======================================================================
# The grid and duplicate rules
# ======================================================================
class TestTheGridRule:
    def test_duplicates_keep_the_smallest_z(self):
        x = [1, 2, 1, 2, 2, np.nan, 3]
        y = [1, 1, 2, 2, 2, 1, np.inf]
        z = [1, 2, 3, 5, 4, 9, 9]
        px, py, pz = dr._dash_contour_points(x, y, z)
        assert list(zip(px, py, pz)) == [(1, 1, 1), (2, 1, 2), (1, 2, 3), (2, 2, 4)]

    def test_axes_are_the_distinct_values(self):
        gx, gy = dr._dash_contour_grid([3, 1, 3, 2], [5, 5, 4, 4])
        assert list(gx) == [1, 2, 3] and list(gy) == [4, 5]


# ======================================================================
# Stata's thin-plate spline: kernel r^2 log r, trend 1 + x + y
# ======================================================================
class TestTps:
    @pytest.mark.parametrize("ds", ["auto", "synthetic"])
    def test_exact_at_the_data(self, truth, ds):
        x, y, z = _twoways_input(truth["cases"][ds]["thinplatespline"])
        w, note = dr._dash_tps_fit(x, y, z)
        # auto's system has condition 2.5e17: twoway's rank-revealing solve
        # leaves one direction out, and the fit is exact to 1e-7 there.
        assert note == ("singular" if ds == "auto" else "")
        tol = _tolerance(note)
        got = dr._dash_tps_eval(w, x, y, x, y)
        assert np.allclose(got, z, rtol=tol, atol=tol * np.ptp(z))

    def test_a_plane_is_the_trend(self):
        x, y, _ = _scatter(30)
        w, _note = dr._dash_tps_fit(x, y, 2 + 3 * x - y)
        assert np.allclose(w[:30], 0, atol=1e-9)
        assert np.allclose(w[30:], (2, 3, -1), atol=1e-9)

    def test_the_kernel_is_r2_log_r(self):
        # Measured: twoway's value at the unobserved node (2, 1) of the
        # five points of the fixture's `words' case is 4.243974703476991;
        # the r kernel the plan transcribed gives 3.6747.
        x, y, z = [1, 3, 1, 2, 3], [1, 1, 3, 2, 3], [1, 2, 3, 10, 4]
        w, _ = dr._dash_tps_fit(x, y, z)
        assert dr._dash_tps_eval(w, x, y, [2.0], [1.0])[0] == pytest.approx(
            4.243974703476991, rel=1e-13)

    def test_collinear_points_fall_back_to_least_squares(self):
        w, note = dr._dash_tps_fit([1, 1, 1, 1], [1, 2, 3, 4], [1, 2, 3, 4])
        assert note == "singular" and np.all(np.isfinite(w))


# ======================================================================
# Shepard: 1/d^2 weights
# ======================================================================
class TestShepard:
    def test_exact_at_the_data(self):
        x, y, z = _scatter(25)
        assert np.array_equal(dr._dash_shepard(x, y, z, x, y), z)

    def test_midpoint_of_two(self):
        got = dr._dash_shepard([0, 2], [0, 0], [1, 5], [1.0], [0.0])
        assert got[0] == pytest.approx(3.0)

    def test_measured_value(self):
        x, y, z = [1, 3, 1, 2, 3], [1, 1, 3, 2, 3], [1, 2, 3, 10, 4]
        assert dr._dash_shepard(x, y, z, [2.0], [1.0])[0] == pytest.approx(
            4.2352941176470589, rel=1e-13)


class TestNone:
    def test_only_observed_nodes(self):
        s = dr._dash_contour_surface([1, 3, 1, 2, 3], [1, 1, 3, 2, 3],
                                     [1, 2, 3, 10, 4], "none")
        assert s["gz"].shape == (3, 3)
        assert np.isfinite(s["gz"]).sum() == 5
        assert s["gz"][1, 1] == 10 and np.isnan(s["gz"][0, 1])


# ======================================================================
# The cap (DECISIONS D4)
# ======================================================================
class TestTheCap:
    def test_above_the_cap_is_a_100_grid(self):
        x, y, z = _scatter(dr._DASH_CONTOUR_EXACT_MAX + 1)
        s = dr._dash_contour_surface(x, y, z)
        assert s["capped"] is True and s["gz"].shape == (100, 100)
        assert s["n_unique"] == 1001
        gx, gy = dr._dash_contour_fallback_grid(x, y)
        assert np.array_equal(s["gx"], gx) and np.array_equal(s["gy"], gy)
        assert gx[0] == x.min() and gx[-1] == x.max() and gy.size == 100
        # Seeded: the same rows give the same surface.
        again = dr._dash_contour_surface(x, y, z)
        assert np.array_equal(s["gz"], again["gz"])

    def test_at_the_cap_is_exact(self):
        x, y, z = _scatter(dr._DASH_CONTOUR_EXACT_MAX, seed=3)
        # interp(none): the exact grid without the 10^6-node evaluation.
        s = dr._dash_contour_surface(x, y, z, "none")
        assert s["capped"] is False and s["gz"].shape == (1000, 1000)
        assert np.isfinite(s["gz"]).sum() == 1000

    def test_the_constants(self):
        assert dr._DASH_CONTOUR_EXACT_MAX == 1000
        assert dr._DASH_CONTOUR_FALLBACK_N == 100
        assert dr._DASH_CONTOUR_INTERPS == ("thinplatespline", "shepard", "none")


class TestDegenerate:
    def test_fewer_than_three(self, truth):
        s = dr._dash_contour_surface([1, 2], [1, 2], [1, 2])
        assert s["note"] == "degenerate" and np.all(np.isnan(s["gz"]))
        # twoway draws no rectangle and no polygon from two points.
        two = truth["degenerate"]["two_points"]
        assert two["nodes"]["n_rects"] == 0 and two["filled"]["n_rows"] == 0

    def test_one_x_draws_the_observed_column(self, truth):
        one = truth["degenerate"]["one_x"]
        rows = one["rows"]
        s = dr._dash_contour_surface(rows["x"], rows["y"], rows["z"])
        assert s["gz"].shape == (4, 1) and s["note"] == "singular"
        assert list(s["gz"][:, 0]) == one["nodes"]["z"]

    def test_unknown_interp(self, truth):
        # Measured: twoway passes interp() to its generator, which reads an
        # abbreviation of thinplatespline or shepard of four letters or
        # more and draws anything else as interp(none), r(0).
        words = truth["interp_abbrev"]
        for word, rec in words.items():
            if word == "rows":
                continue
            arg = "" if word == "EMPTY" else word
            assert rec["rc"] == 0
            assert dr._dash_contour_interp(arg) == rec["method"], word
        assert dr._dash_contour_interp(None) == "thinplatespline"
        s = dr._dash_contour_surface([1, 3, 1, 2, 3], [1, 1, 3, 2, 3],
                                     [1, 2, 3, 10, 4], "bogus")
        assert s["interp"] == "none" and np.isfinite(s["gz"]).sum() == 5


# ======================================================================
# Against twoway's generator
# ======================================================================
_CASES = [(ds, it) for ds in ("auto", "synthetic", "manual5")
          for it in ("thinplatespline", "shepard")]


class TestAgainstTheFixture:
    @pytest.mark.parametrize("ds,interp", _CASES)
    def test_node_levels_match_twoways_nodes(self, truth, ds, interp):
        case = truth["cases"][ds][interp]
        x, y, z = _twoways_input(case)
        gx, gy = dr._dash_contour_grid(x, y)
        iy, ix, hm = _nodes_of(case, gx, gy)
        # Under thin-plate and Shepard twoway keeps one z of a duplicate
        # (y, x) in an order that follows the sort seed (fixture `dupseed'),
        # not the smallest: fit to the z its node grid shows at each observed
        # node, so this compares the interpolation, not the pick.
        observed = {(a, b) for a, b in zip(np.searchsorted(gy, y),
                                           np.searchsorted(gx, x))}
        tz = z.copy()
        node_z = {(a, b): v for a, b, v in zip(iy, ix, hm["z"])}
        for k in range(z.size):
            key = (np.searchsorted(gy, y[k]), np.searchsorted(gx, x[k]))
            tz[k] = node_z[key]
        assert len(observed) == z.size
        s = dr._dash_contour_surface(x, y, tz, interp)
        assert s["gz"].shape == (gy.size, gx.size)
        assert len(hm["z"]) == gx.size * gy.size        # every node drawn
        got = s["gz"][iy, ix]
        want = np.asarray(hm["z"])
        span = s["zmax"] - s["zmin"]
        tol = _tolerance(s["note"])
        assert np.allclose(got, want, rtol=tol, atol=tol * span)
        # Levels where a node is not within noise of a cut, or is the very
        # value twoway has (an observed node on a cut: manual5).
        cuts = np.asarray(case["cuts"])
        far = np.min(np.abs(got[:, None] - cuts[None, :]), axis=1) > 1e-6 * span
        far |= got == want
        assert np.array_equal(_levels(got[far], cuts), np.asarray(hm["lev"])[far])
        assert far.mean() > 0.95

    @pytest.mark.parametrize("ds", ["auto", "synthetic", "manual5"])
    def test_grid_edges_are_the_midpoints(self, truth, ds):
        inp = truth["cases"][ds]["thinplatespline"]["input"]
        gx, gy = dr._dash_contour_grid(inp["x"], inp["y"])
        for axis, g in (("x", gx), ("y", gy)):
            edges = np.concatenate([[g[0]], (g[1:] + g[:-1]) / 2, [g[-1]]])
            assert np.allclose(edges, truth["grid"][ds][axis], rtol=1e-12)

    @pytest.mark.parametrize("ds", ["auto", "synthetic", "manual5"])
    def test_none_draws_the_observed_nodes(self, truth, ds):
        case = truth["cases"][ds]["none"]
        inp = case["input"]
        s = dr._dash_contour_surface(inp["x"], inp["y"], inp["z"], "none")
        iy, ix, hm = _nodes_of(case, s["gx"], s["gy"])
        assert np.isfinite(s["gz"]).sum() == inp["n_unique"] == hm["n_rects"]
        # interp(none) keeps the smallest z of a duplicate, as documented.
        assert np.array_equal(s["gz"][iy, ix], hm["z"])

    def test_the_duplicate_rule_follows_the_sort_seed_in_twoway(self, truth):
        dup = truth["dupseed"]
        assert set(dup["none"]["order1"] + dup["none"]["order2"]) == {4.0}
        assert {4.0, 5.0} <= set(dup["thinplatespline"]["order1"]
                                 + dup["thinplatespline"]["order2"])
        px, py, pz = dr._dash_contour_points([1, 2, 1, 2, 2], [1, 1, 2, 2, 2],
                                             [1, 2, 3, 4, 5])
        assert pz.size == 4 and pz[-1] == 4


class TestAgainstScipyFormula:
    def test_thin_plate_kernel_degree_one(self):
        interp = pytest.importorskip("scipy.interpolate")
        x, y, z = _scatter(40, seed=11)
        gx, gy = np.meshgrid(np.linspace(0, 10, 13), np.linspace(0, 5, 7))
        ref = interp.RBFInterpolator(np.column_stack([x, y]), z,
                                     kernel="thin_plate_spline", degree=1)
        want = ref(np.column_stack([gx.ravel(), gy.ravel()]))
        w, _ = dr._dash_tps_fit(x, y, z)
        assert np.allclose(dr._dash_tps_eval(w, x, y, gx, gy), want,
                           rtol=1e-10, atol=1e-10)


# ======================================================================
# The fixture, the served app, the dependencies
# ======================================================================
class TestTheFixture:
    def test_meta_and_cases(self, truth):
        assert sorted(truth["_meta"]) == ["born_date", "dash_commit", "extracted",
                                          "source", "stata_version"]
        assert truth["_meta"]["source"] == "scripts/extract_contour_truth.do"
        assert sorted(truth["cases"]) == ["auto", "manual5", "synthetic"]
        for ds in truth["cases"]:
            for it in ("thinplatespline", "shepard", "none"):
                case = truth["cases"][ds][it]
                assert case["rc"] == {"nodes": 0, "filled": 0, "line": 0}
                assert case["filled"]["n_rows"] > 0 and case["line"]["n_rows"] > 0
        assert truth["cases"]["manual5"]["thinplatespline"]["input"]["n_unique"] == 4
        assert sorted(truth["grid"]) == ["auto", "manual5", "synthetic"]
        assert sorted(truth["degenerate"]) == ["one_x", "two_points"]
        assert truth["interp_abbrev"]["bogus"]["method"] == "none"


class TestServedCarries:
    def test_names_copied(self):
        lines = dr.ServerAppBuilder._shared_stat_lines()
        src = "\n".join(lines)
        tree = ast.parse(src)
        defined = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
        defined |= {t.id for n in tree.body if isinstance(n, ast.Assign)
                    for t in n.targets if isinstance(t, ast.Name)}
        assert set(_NAMES) | set(_CONSTANTS) <= defined
        # The copied text runs on its own: the constants precede the
        # defaults that read them.
        ns = {"np": np, "math": math}
        exec(compile(src, "<served stat helpers>", "exec"), ns)  # noqa: S102
        s = ns["_dash_contour_surface"]([1, 3, 1, 2, 3], [1, 1, 3, 2, 3],
                                        [1, 2, 3, 10, 4])
        ref = dr._dash_contour_surface([1, 3, 1, 2, 3], [1, 1, 3, 2, 3],
                                       [1, 2, 3, 10, 4])
        assert np.array_equal(s["gz"], ref["gz"])


class TestNoDependency:
    def test_numpy_only(self):
        for name in _NAMES:
            src = inspect.getsource(getattr(dr, name))
            assert not re.search(r"^\s*(import|from)\s", src, re.M), name
            assert "scipy" not in src and "contourpy" not in src, name
