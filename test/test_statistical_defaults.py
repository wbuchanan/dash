"""test_statistical_defaults.py — S07: statistical values come from the data.

Part A (this file, written first) covers the defects that are visible WITHOUT
any reference to Stata, because they are self-inconsistencies inside dash:

  * ``x^2`` parses as a bitwise XOR, not a power, and draws an empty line.
  * ``lowess, bwidth(notanumber)`` crashes the whole render.
  * the initial KDE and the filter-callback KDE use different bandwidth rules,
    so touching an inert filter makes the curve jump.
  * ``fpfit`` and ``fpfitci`` plot over different x-ranges on different grids.
  * the bootstrap resample count is 200 in three places and 500 in a fourth,
    and the seed is frozen at 42.
  * ``lpoly, bwidth(5)`` clamps to the whole x-range — the opposite of a
    5-unit bandwidth.

Part B (``test_statistical_truth.py``) asserts agreement with Stata itself,
driven by ``test/fixtures/stat_truth.json``.

Every assertion here is on a computed VALUE, not on the presence of a glyph:
a test that only checks a renderer was returned passes today for every one of
these defects.
"""
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
# conftest.py holds the shared spec/data builders; add the test directory
# itself to sys.path so it imports as a plain module regardless of the
# directory pytest was invoked from.
sys.path.insert(0, _HERE)

import dash_render
from dash_render import GlyphMapper, OptionTranslator, SchemeParser

from conftest import make_dr


@pytest.fixture
def mapper():
    return GlyphMapper(OptionTranslator(), SchemeParser("s2color"))


def _xy(n=200, seed=0, x_lo=0.0, x_hi=1000.0):
    """Paired arrays with real local structure, so a bandwidth change shows."""
    rng = np.random.default_rng(seed)
    x = np.linspace(x_lo, x_hi, n)
    y = np.sin(x / 40.0) * 10.0 + rng.normal(0, 0.5, n)
    return x, y


def _src(x, y, xname="weight", yname="mpg"):
    return ColumnDataSource({xname: list(x), yname: list(y)})


# ======================================================================
# map_function — the caret, the grid and the domain
# ======================================================================

class TestFunctionOperatorAndDomain:
    """``twoway function`` must evaluate Stata expressions, over Stata's grid."""

    def test_caret_is_exponentiation_not_bitwise_xor(self, mapper):
        """``y=x^2`` must draw a parabola.

        In Stata ``^`` is exponentiation.  Python parses it as ``BitXor``,
        which survives the AST whitelist, then raises TypeError on a float
        array — so the curve is silently empty and red.
        """
        fig = figure()
        mapper.map_function(fig, "x^2", (0.0, 10.0), 5)
        r = fig.renderers[-1]
        ys = list(r.data_source.data["y_fn"])
        assert ys, "x^2 produced an empty curve — '^' was not read as a power"
        np.testing.assert_allclose(ys, [0.0, 6.25, 25.0, 56.25, 100.0])

    def test_caret_inside_a_larger_expression(self, mapper):
        fig = figure()
        mapper.map_function(fig, "2*x^3 + x^2 - 1", (1.0, 2.0), 2)
        ys = list(fig.renderers[-1].data_source.data["y_fn"])
        assert ys == pytest.approx([2.0, 2 * 8 + 4 - 1])

    def test_double_star_still_works(self, mapper):
        """``**`` is not Stata's: ``twoway function y = x**2`` is r(198).

        Flipped (WP-29 P0.6): it used to draw x squared through Python's
        operator; it now draws nothing, as twoway draws nothing, and the
        same curve is ``x^2``."""
        fig = figure()
        mapper.map_function(fig, "x**2", (0.0, 10.0), 5)
        ys = list(fig.renderers[-1].data_source.data["y_fn"])
        assert ys == []
        mapper.map_function(fig, "x^2", (0.0, 10.0), 5)
        ys = list(fig.renderers[-1].data_source.data["y_fn"])
        np.testing.assert_allclose(ys, [0.0, 6.25, 25.0, 56.25, 100.0])

    def test_caret_translation_does_not_loosen_the_whitelist(self, mapper,
                                                             monkeypatch):
        """Rewriting ^ must not become a hole in the AST validator."""
        # "Drew nothing" alone cannot fail for five of these six: evaluation
        # swallows its own errors into the same empty curve (the names are
        # absent from the evaluation namespace, and a bare `x.__class__' is
        # no array of numbers), so only `(lambda: 1)()' drew when the
        # whitelist was bypassed (measured 24sep2026).  The grammar's own
        # verdict is read instead: map_function hands a tree to
        # _stata_fn_eval only after _stata_fn_parse accepted it (WP-29
        # P0.6; flipped from the _floats_only spy, which is gone with the
        # eval() it guarded), so every hostile expression must reach it
        # zero times -- and `x^2', the positive control, once.
        accepted = []
        real = dash_render._stata_fn_eval

        def verdict(tree, x):
            accepted.append(tree)
            return real(tree, x)

        monkeypatch.setattr(dash_render, "_stata_fn_eval", verdict)
        fig = figure()
        for hostile in (
            "__import__('os').system('true')",
            "x.__class__",
            "open('/etc/passwd')",
            "(lambda: 1)()",
            "[].__class__.__base__",
            "x^__import__('os').getpid()",
        ):
            n_before = len(fig.renderers)
            mapper.map_function(fig, hostile, (0.0, 1.0), 3)
            r = fig.renderers[-1]
            assert len(fig.renderers) == n_before + 1
            assert list(r.data_source.data["y_fn"]) == [], (
                f"hostile expression {hostile!r} was evaluated"
            )
            assert not accepted, (
                f"hostile expression {hostile!r} passed the whitelist")
        mapper.map_function(fig, "x^2", (0.0, 1.0), 3)
        assert len(accepted) == 1, "the verdict count saw no accepted tree"
        assert list(fig.renderers[-1].data_source.data["y_fn"]) == \
            pytest.approx([0.0, 0.25, 1.0])

    def test_default_grid_is_300_points(self):
        """Stata's ``twoway function`` default is n(300); dash uses 200."""
        dr = make_dr([{"type": "function", "expr": "x", "options": {}}])
        ys = _function_curve(dr)
        assert len(ys) == 300

    def test_n_option_is_honoured(self):
        dr = make_dr([{"type": "function", "expr": "x",
                       "options": {"n": "400", "range": "0 10"}}])
        assert len(_function_curve(dr)) == 400

    def test_range_option_is_honoured(self):
        dr = make_dr([{"type": "function", "expr": "x",
                       "options": {"range": "0 10", "n": "11"}}])
        xs = _function_domain(dr)
        assert xs[0] == pytest.approx(0.0)
        assert xs[-1] == pytest.approx(10.0)

    def test_default_domain_is_zero_to_one_even_beside_another_plot(self):
        """Stata assumes range(0 1) when range() is absent.

        The plan's register asserted the default should follow the x-axis
        range.  Stata's own documentation says otherwise --
        twoway_function.sthlp: "If range() is not specified, range(0 1) is
        assumed" -- so dash's existing behaviour was correct and this test
        pins it against a well-meant "fix".
        """
        df = pd.DataFrame({"mpg": [10.0, 20.0, 30.0],
                           "weight": [2000.0, 3000.0, 4000.0]})
        dr = make_dr(
            [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}},
             {"type": "function", "expr": "x", "options": {}}],
            df=df,
        )
        xs = _function_domain(dr)
        assert xs[0] == pytest.approx(0.0)
        assert xs[-1] == pytest.approx(1.0)


def _function_renderer(dr):
    for fig in dr._build_figures().values():
        for r in fig.renderers:
            if "y_fn" in getattr(r.data_source, "data", {}):
                return r
    raise AssertionError("no function renderer found")


def _function_curve(dr):
    return list(_function_renderer(dr).data_source.data["y_fn"])


def _function_domain(dr):
    return list(_function_renderer(dr).data_source.data["x_fn"])


# ======================================================================
# Bandwidth handling
# ======================================================================

class TestBandwidthSemantics:

    def test_lowess_non_numeric_bwidth_does_not_crash_the_render(self, mapper):
        """``float(options.get("bwidth", "0.8"))`` has no guard at all."""
        x, y = _xy(60)
        fig = figure()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            mapper.map_lowess(fig, _src(x, y), "mpg", "weight",
                              {"bwidth": "notanumber"})
        msgs = " ".join(str(w.message) for w in caught)
        assert "bwidth" in msgs, (
            "a non-numeric bwidth must be reported, not crash or vanish"
        )

    def test_lowess_out_of_range_bwidth_is_reported(self, mapper):
        """Stata's lowess bwidth is a fraction in (0,1); one outside is .8,
        in silence (lowess.ado:75-78).  Flipped (WP-31 C10a): dash noted
        bwidth(5); twoway draws it as bwidth(.8), measured
        (test/fixtures/value_bounds_truth.json lowess_bwidth)."""
        x, y = _xy(60)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            r5 = mapper.map_lowess(figure(), _src(x, y), "mpg", "weight",
                                   {"bwidth": "5"})
        assert not any("bwidth" in str(w.message) for w in caught)
        r8 = mapper.map_lowess(figure(), _src(x, y), "mpg", "weight",
                               {"bwidth": ".8"})
        d5, d8 = r5.data_source.data, r8.data_source.data
        k = [c for c in d5 if c.startswith("y")][0]
        np.testing.assert_array_equal(np.asarray(d5[k], float),
                                      np.asarray(d8[k], float))

    def test_lpoly_bwidth_is_absolute_in_data_units(self, mapper):
        """Stata's lpoly bwidth() is a bandwidth, not a fraction of the range.

        On x spanning 0-1000, ``bwidth(5)`` is a *narrow* window that tracks
        local structure.  dash clamps bwidth to [0.01, 1.0] and multiplies by
        the x-range, so bwidth(5) becomes h = 1000 — the whole dataset — and
        the fit collapses to a horizontal line.
        """
        x, y = _xy(300, x_lo=0.0, x_hi=1000.0)
        src = _src(x, y)
        # Go through map_lpoly, not _compute_lpoly_fit: the [0.01, 1.0] clamp
        # that destroys the request lives in map_lpoly, so calling the compute
        # helper directly would pass this test while the option stays broken.
        narrow = np.asarray(
            mapper.map_lpoly(figure(), src, "mpg", "weight",
                             {"bwidth": "5"}).data_source.data["y_lp"],
            dtype=float)
        wide = np.asarray(
            mapper.map_lpoly(figure(), src, "mpg", "weight",
                             {"bwidth": "500"}).data_source.data["y_lp"],
            dtype=float)
        assert np.nanstd(narrow) > 5 * np.nanstd(wide), (
            "bwidth(5) should follow the data closely; it was clamped to the "
            "whole x-range instead"
        )

    def test_lpoly_default_bwidth_comes_from_the_data(self, mapper):
        """Two datasets of very different x-scale must not share a bandwidth."""
        x1, y1 = _xy(200, x_lo=0.0, x_hi=10.0)
        x2, y2 = _xy(200, x_lo=0.0, x_hi=10000.0)
        h1 = GlyphMapper._default_lpoly_bwidth(x1, y1)
        h2 = GlyphMapper._default_lpoly_bwidth(x2, y2)
        assert h2 > 100 * h1, (
            "the default lpoly bandwidth must scale with the data, not be a "
            "fixed 0.5"
        )

    def test_kdensity_honours_bwidth(self, mapper):
        """``bwidth()`` reaches map_kdensity and is currently ignored."""
        x, _ = _xy(300)
        src = ColumnDataSource({"mpg": list(x)})
        fa, fb = figure(), figure()
        ra = mapper.map_kdensity(fa, src, "mpg", {})
        rb = mapper.map_kdensity(fb, src, "mpg", {"bwidth": "200"})
        ya = np.asarray(ra.data_source.data["y"], dtype=float)
        yb = np.asarray(rb.data_source.data["y"], dtype=float)
        assert ya.shape == yb.shape
        assert not np.allclose(ya, yb), "bwidth() made no difference to the KDE"

    def test_kdensity_bad_bwidth_is_reported(self, mapper):
        x, _ = _xy(60)
        src = ColumnDataSource({"mpg": list(x)})
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            mapper.map_kdensity(figure(), src, "mpg", {"bwidth": "zero"})
        assert any("bwidth" in str(w.message) for w in caught)


# ======================================================================
# The Scott / Silverman jump
# ======================================================================

_NODE = shutil.which("node")


def _run_filter_js_kde(vals, x_grid, kernel="epanechnikov", bw_fixed=None):
    """Execute dash's REAL filter-callback KDE code under node.

    The kdensity branch of ``_FILTER_JS`` is sliced out of the module verbatim
    and run, rather than reimplemented here.  A transliteration would only
    ever prove that the transliteration matches itself; this proves that the
    JavaScript users actually receive agrees with the Python that produced
    the first render.

    Returns:
        The density values the callback would put into the data source.
    """
    js = dash_render._FILTER_JS
    helpers = js[js.index("function dash_pctl"):
                 js.index("// agg_sources is a Bokeh model list")]
    blk_lo = js.index("// DASH_KDE_RULE")
    # The block ends where it writes the curve: an earlier emit clears the
    # source on data it cannot smooth, so the first emit is not the end.
    blk_end = js.index("src.data = { x: xs, y: ys };", blk_lo)
    blk_hi = js.index("src.change.emit();", blk_end) + len("src.change.emit();")
    block = js[blk_lo:blk_hi]

    harness = (
        helpers
        + "\nconst ac = " + json.dumps(
            {"kernel": kernel, "bw_fixed": bw_fixed, "x_grid": list(x_grid)})
        + ";\nconst vals = " + json.dumps([float(v) for v in vals])
        + ";\nconst n = vals.length;"
        + "\nlet out = null;"
        + "\nconst src = { data: null, change: { emit: () => {} } };"
        # `continue` is legal only inside a loop; the real block sits in one.
        + "\nfor (let _i = 0; _i < 1; _i++) {\n" + block + "\n}"
        + "\nout = src.data;"
        + "\nprocess.stdout.write(JSON.stringify(out === null ? null : out.y));"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False) as fh:
        fh.write(harness)
        path = fh.name
    try:
        res = subprocess.run([_NODE, path], capture_output=True, text=True,
                             timeout=60)
        if res.returncode != 0:
            raise AssertionError(
                f"the filter callback's KDE code failed under node:\n"
                f"{res.stderr[:2000]}"
            )
        return np.asarray(json.loads(res.stdout), dtype=float)
    finally:
        os.unlink(path)


class TestKdeRenderFilterAgreement:
    """An inert filter must not move the curve."""

    @pytest.mark.skipif(_NODE is None, reason="node is not installed")
    def test_initial_kde_matches_the_filter_callback_kde(self, mapper):
        """Render and filter callback must agree on identical data.

        They did not: the render used scipy's Scott factor and a Gaussian
        kernel while the callback used Silverman and its own Gaussian, so
        every dashboard with a filter and a kdensity jumped on first
        interaction even when no rows were removed.
        """
        rng = np.random.default_rng(7)
        vals = rng.normal(20, 5, 400)
        src = ColumnDataSource({"mpg": list(vals)})
        r = mapper.map_kdensity(figure(), src, "mpg", {})
        rendered = np.asarray(r.data_source.data["y"], dtype=float)
        cfg = r._dash_agg_config
        js = _run_filter_js_kde(vals, cfg["x_grid"], cfg["kernel"],
                                cfg["bw_fixed"])
        assert js.shape == rendered.shape
        np.testing.assert_allclose(
            rendered, js, rtol=1e-9, atol=1e-12,
            err_msg="the initial KDE and the filtered-JS KDE disagree on "
                    "identical data — the curve jumps as soon as any filter "
                    "is touched",
        )

    @pytest.mark.skipif(_NODE is None, reason="node is not installed")
    @pytest.mark.parametrize("kernel", sorted(dash_render._KERNELS))
    def test_every_kernel_agrees_between_python_and_javascript(self, mapper,
                                                               kernel):
        rng = np.random.default_rng(13)
        vals = rng.normal(0, 1, 250)
        src = ColumnDataSource({"mpg": list(vals)})
        r = mapper.map_kdensity(figure(), src, "mpg", {"kernel": kernel})
        rendered = np.asarray(r.data_source.data["y"], dtype=float)
        cfg = r._dash_agg_config
        assert cfg["kernel"] == kernel
        js = _run_filter_js_kde(vals, cfg["x_grid"], kernel, cfg["bw_fixed"])
        np.testing.assert_allclose(rendered, js, rtol=1e-9, atol=1e-12)

    @pytest.mark.skipif(_NODE is None, reason="node is not installed")
    def test_explicit_bwidth_is_held_fixed_by_the_callback(self, mapper):
        rng = np.random.default_rng(3)
        vals = rng.normal(0, 1, 200)
        src = ColumnDataSource({"mpg": list(vals)})
        r = mapper.map_kdensity(figure(), src, "mpg", {"bwidth": "0.4"})
        cfg = r._dash_agg_config
        assert cfg["bw_fixed"] == pytest.approx(0.4)
        js = _run_filter_js_kde(vals, cfg["x_grid"], cfg["kernel"], 0.4)
        np.testing.assert_allclose(
            np.asarray(r.data_source.data["y"], dtype=float), js,
            rtol=1e-9, atol=1e-12)

    def test_the_javascript_records_which_rule_it_uses(self):
        """Guard against the two paths drifting apart again silently."""
        js = dash_render._FILTER_JS
        assert "DASH_KDE_RULE" in js, (
            "the KDE bandwidth rule used by the callback must be named in the "
            "JS so it cannot silently diverge from the Python one"
        )
        assert dash_render._KDE_BANDWIDTH_RULE in js, (
            "the JS names a different bandwidth rule from the Python constant"
        )


# ======================================================================
# fpfit / fpfitci agreement
# ======================================================================

class TestFpfitConsistency:

    def _grids(self, mapper, opts=None):
        rng = np.random.default_rng(3)
        x = np.linspace(1.0, 100.0, 120)
        y = 3.0 * np.log(x) + rng.normal(0, 0.2, 120)
        src = _src(x, y)
        fa, fb = figure(), figure()
        ra = mapper.map_fpfit(fa, src, "mpg", "weight", opts or {})
        rb = mapper.map_fpfitci(fb, src, "mpg", "weight", opts or {})
        rb = rb[0] if isinstance(rb, list) else rb
        return (np.asarray(ra.data_source.data["x_fp"], dtype=float),
                np.asarray(rb.data_source.data["x_fp"], dtype=float))

    def test_same_grid_size(self, mapper):
        a, b = self._grids(mapper)
        assert len(a) == len(b), (
            f"fpfit plots {len(a)} points and fpfitci {len(b)} — the same "
            "curve drawn two ways must use one grid"
        )

    def test_same_x_range(self, mapper):
        a, b = self._grids(mapper)
        assert a[0] == pytest.approx(b[0])
        assert a[-1] == pytest.approx(b[-1])

    def test_spans_the_full_estimation_range_not_the_1st_to_99th_percentile(
        self, mapper
    ):
        """Truncating to p1-p99 hides the ends of the fit the user asked for."""
        rng = np.random.default_rng(3)
        x = np.linspace(1.0, 100.0, 120)
        y = 3.0 * np.log(x) + rng.normal(0, 0.2, 120)
        r = mapper.map_fpfit(figure(), _src(x, y), "mpg", "weight", {})
        xs = np.asarray(r.data_source.data["x_fp"], dtype=float)
        assert xs[0] == pytest.approx(x.min(), rel=1e-6)
        assert xs[-1] == pytest.approx(x.max(), rel=1e-6)


# ======================================================================
# Bootstrap: one resample count, and a settable seed
# ======================================================================

class TestBootstrapConfiguration:

    @staticmethod
    def _bootstrap_calls_with_n_boot(src):
        """Every ``_bootstrap_ci(...)`` call in *src* that passes an
        ``n_boot=`` keyword, as (lineno, literal-or-None).

        Read with ``ast``, not a regex: the old pattern balanced one level
        of parentheses and could not see past the qfitci fallback's own
        ``np.polyval(np.polyfit(xi, yi, 2), xg)`` argument, so an
        ``n_boot=500`` added THERE was invisible to it (measured
        24sep2026).  A keyword whose value is not a plain literal is
        reported as None, which still counts as an override.
        """
        import ast
        out = []
        for node in ast.walk(ast.parse(src)):
            if not isinstance(node, ast.Call):
                continue
            f = node.func
            name = (f.attr if isinstance(f, ast.Attribute)
                    else f.id if isinstance(f, ast.Name) else "")
            if name != "_bootstrap_ci":
                continue
            for kw in node.keywords:
                if kw.arg == "n_boot":
                    lit = (kw.value.value
                           if isinstance(kw.value, ast.Constant) else None)
                    out.append((node.lineno, lit))
        return out

    def test_all_ci_layers_use_the_same_resample_count(self):
        """200 in three call sites and 500 in a fourth is drift, not design."""
        src = open(
            os.path.join(os.path.dirname(__file__), "..", "dash_render.py")
        ).read()
        overrides = self._bootstrap_calls_with_n_boot(src)
        assert not overrides, (
            f"call sites override the bootstrap resample count: {overrides} — "
            "one constant must decide it for every CI layer"
        )
        assert "n_boot: int = _N_BOOT_DEFAULT" in src

    def test_the_override_scan_catches_an_added_n_boot(self):
        """Positive control: the scan must SEE an n_boot= at the very call
        site the old regex could not reach -- the qfitci fallback, whose
        argument nests ``np.polyval(np.polyfit(...), xg)``.  Without this,
        `not overrides' above passed on a scanner that matched nothing."""
        planted = (
            "y_lower, y_upper = GlyphMapper._bootstrap_ci(\n"
            "    x, y, x_fit,\n"
            "    lambda xi, yi, xg: np.polyval(np.polyfit(xi, yi, 2), xg),\n"
            "    fallback=y_fit, seed=1, n_boot=500,\n"
            ")\n"
        )
        found = self._bootstrap_calls_with_n_boot(planted)
        assert found == [(1, 500)], found

    def test_default_matches_the_documented_default(self):
        import inspect
        sig = inspect.signature(GlyphMapper._bootstrap_ci)
        default = sig.parameters["n_boot"].default
        doc = GlyphMapper._bootstrap_ci.__doc__ or ""
        assert f"default {default}" in doc, (
            "the docstring and the signature disagree on n_boot"
        )

    def test_seed_is_settable_and_changes_the_result(self):
        rng = np.random.default_rng(11)
        x = np.linspace(0, 10, 80)
        y = 2 * x + rng.normal(0, 1, 80)
        grid = np.linspace(0, 10, 25)

        def fn(xi, yi, xg):
            c = np.polyfit(xi, yi, 1)
            return np.polyval(c, xg)

        lo1, _ = GlyphMapper._bootstrap_ci(x, y, grid, fn, seed=1)
        lo2, _ = GlyphMapper._bootstrap_ci(x, y, grid, fn, seed=2)
        lo1b, _ = GlyphMapper._bootstrap_ci(x, y, grid, fn, seed=1)
        np.testing.assert_allclose(lo1, lo1b)
        assert not np.allclose(lo1, lo2), "seed had no effect"

    def test_confidence_level_widens_the_band(self):
        rng = np.random.default_rng(11)
        x = np.linspace(0, 10, 80)
        y = 2 * x + rng.normal(0, 1, 80)
        grid = np.linspace(0, 10, 25)

        def fn(xi, yi, xg):
            return np.polyval(np.polyfit(xi, yi, 1), xg)

        lo90, hi90 = GlyphMapper._bootstrap_ci(x, y, grid, fn, level=90.0, seed=1)
        lo99, hi99 = GlyphMapper._bootstrap_ci(x, y, grid, fn, level=99.0, seed=1)
        assert np.mean(hi99 - lo99) > np.mean(hi90 - lo90)


# ======================================================================
# Confidence level threaded from Stata
# ======================================================================

class TestConfidenceLevel:

    def _band_width(self, level=None):
        rng = np.random.default_rng(5)
        x = np.linspace(0, 10, 60)
        y = 2 * x + rng.normal(0, 1.5, 60)
        df = pd.DataFrame({"mpg": y, "weight": x})
        opts = {} if level is None else {"level": str(level)}
        dr = make_dr(
            [{"type": "lfitci", "yvar": "mpg", "xvar": "weight",
              "options": opts}],
            df=df,
        )
        for fig in dr._build_figures().values():
            for r in fig.renderers:
                d = getattr(r.data_source, "data", {})
                if "y_lower" in d and "y_upper" in d:
                    return float(np.mean(np.asarray(d["y_upper"], dtype=float)
                                         - np.asarray(d["y_lower"], dtype=float)))
        raise AssertionError("no CI band found")

    def test_level_option_widens_and_narrows_the_band(self):
        w90 = self._band_width(90)
        w95 = self._band_width(95)
        w99 = self._band_width(99)
        assert w90 < w95 < w99

    def test_default_level_is_the_session_default(self):
        """With no level(), dash must use whatever c(level) was serialized."""
        assert self._band_width(None) == pytest.approx(self._band_width(95),
                                                       rel=1e-9)

    def test_invalid_level_is_reported(self):
        # Flipped (WP-31 C10a): twoway lfitci takes level(150) and draws no
        # band (test/fixtures/value_bounds_truth.json level.100); a level
        # that is not a number is still reported.
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            w = self._band_width(150)
        assert not any("level" in str(m.message).lower() for m in caught)
        assert np.isnan(w)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            self._band_width("abc")
        assert any("level" in str(m.message).lower() for m in caught)


# ======================================================================
# Histogram: bins and the y-axis family
# ======================================================================

class TestHistogramDefaults:

    def _hist(self, n, opts=None, lo=0.0, hi=100.0):
        rng = np.random.default_rng(2)
        vals = rng.uniform(lo, hi, n)
        src = ColumnDataSource({"mpg": list(vals)})
        gm = GlyphMapper(OptionTranslator(), SchemeParser("s2color"))
        r = gm.map_histogram(figure(), src, "mpg", opts or {})
        d = r.data_source.data
        return (np.asarray(d["top"], dtype=float),
                np.asarray(d["left"], dtype=float),
                np.asarray(d["right"], dtype=float))

    def test_bin_count_depends_on_n(self):
        """A fixed 10 bins is wrong for every N."""
        small = len(self._hist(30)[0])
        large = len(self._hist(5000)[0])
        assert small != large, (
            "the bin count did not change between N=30 and N=5000 — it is a "
            "constant, not a rule"
        )

    def test_bin_rule_matches_statas_formula(self):
        """Stata: k = min(sqrt(N), 10*ln(N)/ln(10)), rounded."""
        for n in (30, 74, 500, 2246, 5000):
            k = len(self._hist(n)[0])
            # Truncated, not rounded: Stata gives 8 bins for N=74 (8.602)
            # and 33 for N=2246 (33.514), both of which round up.
            expected = int(min(math.sqrt(n),
                               10 * math.log(n) / math.log(10)))
            assert k == expected, f"N={n}: got {k} bins, Stata's rule gives {expected}"

    def test_bin_option_overrides(self):
        assert len(self._hist(500, {"bin": "20"})[0]) == 20

    def test_width_option_sets_the_grid(self):
        top, left, right = self._hist(500, {"width": "2"}, lo=0.0, hi=100.0)
        np.testing.assert_allclose(right - left, 2.0)

    def test_start_option_sets_the_left_edge(self):
        _, left, _ = self._hist(500, {"width": "5", "start": "-10"},
                                lo=0.0, hi=100.0)
        assert left[0] == pytest.approx(-10.0)

    def test_default_y_axis_is_density(self):
        """Stata's histogram defaults to density for a continuous variable."""
        top, left, right = self._hist(2000, lo=0.0, hi=100.0)
        area = float(np.sum(top * (right - left)))
        assert area == pytest.approx(1.0, abs=1e-9), (
            f"bar areas sum to {area}, not 1 — the default is raw counts"
        )

    def test_explicit_density_is_honoured(self):
        """density() names the default, so it must still BE the default.

        Its three siblings each change the output and so were each found to
        be live; density() alone renders identically whether written or
        omitted, which is why dash.ado went on naming it in the
        ignoring-unsupported note long after _histogram_grid began reading
        it. See test_unsupported_report_is_true.py for that guard.
        """
        top, left, right = self._hist(2000, {"density": "density"},
                                      lo=0.0, hi=100.0)
        area = float(np.sum(top * (right - left)))
        assert area == pytest.approx(1.0, abs=1e-9)

    def test_frequency_gives_counts(self):
        top, _, _ = self._hist(2000, {"frequency": "frequency"})
        assert float(np.sum(top)) == pytest.approx(2000.0)

    def test_fraction_sums_to_one(self):
        top, _, _ = self._hist(2000, {"fraction": "fraction"})
        assert float(np.sum(top)) == pytest.approx(1.0)

    def test_percent_sums_to_one_hundred(self):
        top, _, _ = self._hist(2000, {"percent": "percent"})
        assert float(np.sum(top)) == pytest.approx(100.0)

    def test_max_bins_guard_still_holds_and_warns(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            top, _, _ = self._hist(100, {"bin": "999999"})
        assert len(top) <= 1000
        assert any("bin" in str(w.message).lower() for w in caught), (
            "clamping the bin count must be reported, not silent"
        )


# ======================================================================
# mband
# ======================================================================

class TestMband:

    def _points(self, opts=None, n=100):
        rng = np.random.default_rng(4)
        x = np.linspace(0, 100, n)
        y = x * 0.5 + rng.normal(0, 3, n)
        gm = GlyphMapper(OptionTranslator(), SchemeParser("s2color"))
        rs = gm.map_mband(figure(), _src(x, y), "mpg", "weight", opts or {})
        d = rs[0].data_source.data
        return (np.asarray(d["x_mb"], dtype=float),
                np.asarray(d["y_mb"], dtype=float))

    def test_bands_option_is_honoured(self):
        xs, _ = self._points({"bands": "5"})
        assert len(xs) == 5

    def test_x_is_the_within_band_median_not_the_band_midpoint(self):
        """Stata plots cross-medians: the median x within each band."""
        rng = np.random.default_rng(4)
        n = 100
        x = np.linspace(0, 100, n)
        y = x * 0.5 + rng.normal(0, 3, n)
        gm = GlyphMapper(OptionTranslator(), SchemeParser("s2color"))
        rs = gm.map_mband(figure(), _src(x, y), "mpg", "weight", {"bands": "4"})
        xs = np.asarray(rs[0].data_source.data["x_mb"], dtype=float)
        # With 100 equally-spaced points and 4 bands of 25, the median x of
        # band 1 is the mean of the 13th point -- not the band midpoint 12.5.
        band1 = np.sort(x)[:25]
        assert xs[0] == pytest.approx(float(np.median(band1))), (
            "mband plots band midpoints, not the median of x within the band"
        )


# ======================================================================
# The scipy-free Student-t quantile
# ======================================================================

class TestStudentTQuantile:
    """map_qfitci must match Stata AND keep working without scipy.

    Those two requirements together rule out both a bootstrap band and a
    scipy import, so dash computes the t quantile itself.  These tests are
    what make that defensible.
    """

    @pytest.mark.parametrize("df", [1, 2, 3, 5, 10, 30, 72, 100, 1000, 5000])
    @pytest.mark.parametrize("p", [0.55, 0.9, 0.95, 0.975, 0.99, 0.995, 0.9995])
    def test_matches_scipy(self, df, p):
        stats = pytest.importorskip("scipy.stats")
        got = dash_render._t_ppf(p, df)
        want = float(stats.t.ppf(p, df))
        assert got == pytest.approx(want, rel=1e-9)

    def test_symmetry(self):
        for df in (1, 4, 37, 500):
            for p in (0.6, 0.9, 0.99):
                assert dash_render._t_ppf(p, df) == pytest.approx(
                    -dash_render._t_ppf(1 - p, df), rel=1e-9)

    def test_median_is_zero(self):
        assert dash_render._t_ppf(0.5, 9) == pytest.approx(0.0, abs=1e-12)

    def test_monotone_in_p(self):
        vals = [dash_render._t_ppf(p, 12)
                for p in (0.51, 0.6, 0.75, 0.9, 0.95, 0.99, 0.999)]
        assert all(b > a for a, b in zip(vals, vals[1:]))

    @pytest.mark.parametrize("bad", [0.0, 1.0, -0.1, 1.5])
    def test_rejects_probabilities_outside_the_open_unit_interval(self, bad):
        with pytest.raises(ValueError):
            dash_render._t_ppf(bad, 10)

    @pytest.mark.parametrize("bad_df", [0, -1, -0.5])
    def test_rejects_non_positive_degrees_of_freedom(self, bad_df):
        with pytest.raises(ValueError):
            dash_render._t_ppf(0.975, bad_df)

    def test_large_df_approaches_the_normal(self):
        # z_{0.975} = 1.959963985
        assert dash_render._t_ppf(0.975, 10_000_000) == pytest.approx(
            1.959963985, rel=1e-6)


class TestKdensityRange:
    """`range()` limited a function plot's domain and was dropped by kdensity.

    Stata gives `twoway kdensity` a `range(# #)` option that sets the range
    over which the density is estimated. dash read `range()` in the function
    branch -- `range(0 10)` there really does span 0 to 10 -- and nowhere
    else, so `dash kdensity mpg, range(10 30)` estimated over the default
    span and said nothing, while dash.ado named range() in the
    ignoring-unsupported note, which was wrong for every function plot.

    The existing measurement in test_unsupported_report_is_true.py set
    range() on a kdensity, where it was dead, and so certified the option as
    ignored -- the plot type, not the option, was what made the comparison
    come out empty.
    """

    @staticmethod
    def _curve(options):
        rng = np.random.default_rng(7)
        arr = rng.normal(20.0, 5.0, 300)
        src = ColumnDataSource({"mpg": arr.tolist()})
        gm = GlyphMapper()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = gm.map_kdensity(figure(), src, "mpg", options)
        ds = (r[0] if isinstance(r, list) else r).data_source
        return np.asarray(ds.data["x"], dtype=float)

    def test_range_sets_the_estimation_span(self):
        x = self._curve({"range": "10 30"})
        assert x.min() == pytest.approx(10.0), (
            "kdensity ignores range(); the curve starts where the data and "
            "bandwidth put it, not where the user asked"
        )
        assert x.max() == pytest.approx(30.0)

    def test_a_different_range_moves_it(self):
        a = self._curve({"range": "10 30"})
        b = self._curve({"range": "5 25"})
        assert not np.allclose(a, b)

    def test_without_range_the_default_span_is_the_observed_range(self):
        """twoway kdensity draws n() (300) points on [min(x), max(x)].

        This used to pin "min-3h to max+3h, not the data range".  WP-18
        measured the drawn curve against the twoway serset: on census with
        bwidth(2) the padded grid was too coarse to show the estimator at
        all (as-drawn error 1.0 of the density range) although the
        estimator was exact at Stata's own x.  The default span is Stata's
        (test_statistical_truth.py::TestKdensityAsDrawn); range() is how a
        user asks for the tails.
        """
        x = self._curve({})
        rng = np.random.default_rng(7)
        arr = rng.normal(20.0, 5.0, 300)
        assert len(x) == 300
        assert x.min() == pytest.approx(arr.min(), rel=1e-12)
        assert x.max() == pytest.approx(arr.max(), rel=1e-12)

    def test_a_reversed_or_malformed_range_is_reported_not_fatal(self):
        for bad in ("30 10", "10", "", "a b", "10 20 30"):
            x = self._curve({"range": bad})
            # A malformed range falls back to the default span at the
            # default n() of 300 (measured 24sep2026), not to some short
            # degenerate grid: `len(x) > 1' passed a two-point stub.
            assert len(x) == 300 and np.all(np.isfinite(x)), (
                f"range({bad}) produced an unusable grid of {len(x)} points"
            )

    def test_range_is_not_reported_as_unsupported(self):
        import re as _re
        with open(os.path.join(os.path.dirname(__file__), "..", "dash.ado"),
                  encoding="utf-8") as fh:
            src = fh.read()
        i = src.index("program define _dash_parse_plot_opts")
        j = src.index("local _dash_unknown", i)
        pending = _re.findall(r"_dash_pending' (\w+)\"", src[i:j])
        # The regex must actually have matched the pending list, or
        # "range not in pending" holds vacuously: `_dash_parse_plot_opts'
        # carries 48 pending options (measured 24sep2026; 44 before the S3
        # batch's four fitarea options; 44 again since WP-30 P1.14a reads
        # pstyle, lstyle, mstyle and mlstyle), among them the
        # genuinely-unsupported sort/text/scale, and never `range'.
        # 44 -> 47: P1.14b names dstyle, dlstyle and bmlinestyle.
        # 47 -> 45: P1.24 reads mlabvposition() and mlabtextstyle().
        # 45 -> 44: P1.8b reads recast() (_dash_recast_opt).
        # 44 -> 42: P1.9a draws horizontal and refuses vertical as twoway does.
        # 42 -> 44: P1.6 stores and names tmlabel() and tmtick().
        # Flipped (WP-30 P1.10): 44 -> 43, text() is drawn, so it is no
        # longer among the genuinely-unsupported.
        # 43 -> 44: A4 mlalign declared and named.
        # 44 -> 42: C6 cmissing() and connect() drawn everywhere.
        # 42 -> 40: C8b colorlist() and coloruseplegend drawn; 40 -> 39: B5b
        # dstyle() dlstyle() drawn, dlalign() named.
        # 39 -> 33: D1 xmlabel xmtick tmlabel tmtick ymlabel ymtick drawn.
        # 33 -> 23: D2 the eight edge titles drawn, title2() and
        # subtitle2() refused.  23 -> 25: B4b two contour options
        # named.  25 -> 20: D5 fxsize fysize scale xoverhangs
        # yoverhangs drawn (scale was the second control; play is now).
        # 20 -> 19: E3 mlalign() read by the renderer.  19 -> 18: E2
        # mlpattern() taken as twoway takes it.
        # 18 -> 7: WP-32 refuses what twoway refuses (at(), blabel(),
        # ciopts(), fitopts(), lineopts(), mlabwidth(), filter(), link()),
        # checks play() as twoway does, and draws the fitarea and other
        # options twoway draws; the seven left are dropped from the note
        # by type where twoway is silent (_dash_silent_drop).
        # 7 -> 6: WP-47 basic:PT-5 dlalign() drawn.
        assert len(pending) == 6, (len(pending), pending)
        for really_pending in ("sort",):
            assert really_pending in pending, (really_pending, pending)
        assert "range" not in pending, (
            "range() sets a function plot's domain and a kdensity's "
            "estimation span, but dash.ado still names it in the "
            "ignoring-unsupported note"
        )
