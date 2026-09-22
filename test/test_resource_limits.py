"""One option value destroyed the whole dashboard, or never returned.

A dashboard is many graphs, KPIs and filters built in one pass. An exception
raised while one layer is drawn is not a bad layer -- it is the loss of
everything the user built. Five values did that, or worse:

    histogram mpg, width(1e-310)   OverflowError: cannot convert float
                                   infinity to integer
    bar y x, barwidth(-5)          ValueError: Distances must be positive!
    function <50,000 terms>        RecursionError: maximum recursion depth
                                   exceeded
    function 9^9^9^9               never returns -- measured past 20s with
                                   the GIL held, so Stata's Break key cannot
                                   recover it and the process must be killed
    mband y x, bands(4000000)      7.7s and an 8 GB allocation at bands(1e9);
                                   the generated server app clamps this to
                                   1000 and the standalone renderer did not

Stata rejects a negative barwidth with a clear r(198). dash lost the
dashboard and reported a Bokeh internal message naming neither the option
nor the plot.

The contract these tests assert is the one the rest of the file already
follows: a bad option value is REPORTED and the default used, never fatal,
and never unbounded.
"""
import os
import subprocess
import sys
import warnings

import numpy as np
import pytest
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr


@pytest.fixture
def gm():
    return dr.GlyphMapper()


@pytest.fixture
def src():
    return ColumnDataSource({
        "mpg":    [22.0, 17.0, 25.0, 30.0, 21.0, 19.0, 14.0, 28.0],
        "weight": [2930.0, 3350.0, 2200.0, 1800.0, 3000.0, 3100.0,
                   4080.0, 2010.0],
    })


def _warns(fn):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        out = fn()
    return out, [str(w.message) for w in caught]


class TestAHistogramWidthCannotOverflow:
    @pytest.mark.parametrize("w", ["1e-310", "1e-320", "4.9e-324"])
    def test_a_denormal_width_is_reported_not_fatal(self, gm, src, w):
        _r, msgs = _warns(
            lambda: gm.map_histogram(figure(), src, "mpg", {"width": w}))
        assert any("width" in m for m in msgs), (
            f"width({w}) was accepted silently; it used to raise "
            f"OverflowError and take the whole dashboard with it"
        )

    def test_an_ordinary_width_still_works(self, gm, src):
        r = gm.map_histogram(figure(), src, "mpg", {"width": "2"})
        d = r.data_source.data
        np.testing.assert_allclose(
            np.asarray(d["right"]) - np.asarray(d["left"]), 2.0)


class TestABarWidthMustBePositive:
    @pytest.mark.parametrize("bw", ["-5", "-0.1", "nan", "inf", "-inf"])
    def test_a_non_positive_width_is_reported_not_fatal(self, gm, src, bw):
        _r, msgs = _warns(
            lambda: gm.map_bar(figure(), src, "mpg", "weight",
                               {"barwidth": bw}))
        assert any("barwidth" in m or "width" in m for m in msgs), (
            f"barwidth({bw}) was accepted silently; it used to raise inside "
            f"Bokeh and lose the whole dashboard"
        )

    def test_a_real_width_is_still_honoured(self, gm, src):
        r = gm.map_bar(figure(), src, "mpg", "weight", {"barwidth": "50"})
        glyph = (r[0] if isinstance(r, list) else r).glyph
        assert float(glyph.width) == pytest.approx(50.0)


class TestMbandBandsIsBounded:
    def test_an_enormous_band_count_is_clamped_and_reported(self, gm, src):
        _r, msgs = _warns(
            lambda: gm.map_mband(figure(), src, "mpg", "weight",
                                 {"bands": "4000000"}))
        assert any("bands" in m for m in msgs), (
            "bands(4000000) was accepted; the generated server app clamps "
            "the same option to 1000, so the two modes disagreed"
        )

    def test_the_two_modes_use_the_same_limit(self):
        """The server's clamp is the contract; standalone must match it."""
        import inspect
        srv = inspect.getsource(dr.ServerAppBuilder)
        assert "1000" in srv, "the server's bands clamp moved"
        std = inspect.getsource(dr.GlyphMapper.map_mband)
        assert "hi=" in std, (
            "map_mband reads bands() with no upper bound"
        )

    def test_an_ordinary_band_count_still_works(self, gm, src):
        r = gm.map_mband(figure(), src, "mpg", "weight", {"bands": "4"})
        ds = (r[0] if isinstance(r, list) else r).data_source
        col = next(c for c in ds.data if len(ds.data[c]))
        assert len(ds.data[col]) == 4


# ---------------------------------------------------------------------------
# The two that must not be run in-process: one hangs, one blows the C stack.
# ---------------------------------------------------------------------------

_PROBE = r'''
import sys, warnings
sys.path.insert(0, %r)
from bokeh.plotting import figure
import dash_render as dr
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    dr.GlyphMapper().map_function(figure(), %r, (0.0, 1.0), 10, {})
print("RETURNED")
'''


def _run_probe(expr, timeout=25):
    repo = os.path.join(_HERE, "..")
    p = subprocess.run(
        [sys.executable, "-c", _PROBE % (os.path.abspath(repo), expr)],
        capture_output=True, text=True, timeout=timeout,
    )
    return p


class TestAFunctionExpressionAlwaysReturns:
    def test_a_power_tower_does_not_hang(self):
        """`function 9^9^9^9' never returned; Stata's Break cannot help.

        The work happens inside Stata's embedded Python in one uninterruptible
        call, so the only way out was killing Stata.
        """
        try:
            p = _run_probe("9^9^9^9", timeout=25)
        except subprocess.TimeoutExpired:
            pytest.fail(
                "function 9^9^9^9 did not return within 25s; it has no "
                "magnitude bound and holds the GIL throughout"
            )
        assert "RETURNED" in p.stdout, p.stderr[-500:]

    def test_a_very_long_expression_is_reported_not_fatal(self):
        p = _run_probe("+".join(["x"] * 50000), timeout=60)
        assert "RETURNED" in p.stdout, (
            f"a 50,000-term expression took the render down rather than "
            f"being reported: {p.stderr[-400:]}"
        )
        assert "RecursionError" not in p.stderr

    def test_an_ordinary_expression_is_unaffected(self):
        p = _run_probe("sin(x) + x^2", timeout=25)
        assert "RETURNED" in p.stdout, p.stderr[-400:]


class TestTheServedAppHasTheSameBounds:
    """A bound in one mode and not the other is not a bound.

    The generated app carries its own copy of the expression validator and
    its own `n_bands` clamp. The clamp was already there; the expression
    bounds were not, so `dash serve` would hang on an expression `dash build`
    now refuses.
    """

    @staticmethod
    def _emitted():
        """The builder's own source.

        Kept for any check that is genuinely about the BUILDER. It is no
        longer where the expression validator lives: the served app used to
        carry its own copy, written here as string literals, and now calls
        ``GlyphMapper.map_function``, which is copied into the app whole. A
        test that reads this source to check the validator is reading the
        wrong artifact and fails on a change that removed nothing.
        """
        import inspect
        return inspect.getsource(dr.ServerAppBuilder)

    def test_the_served_validator_bounds_the_expression_length(self):
        """The bound, asserted where it now lives and by what it does.

        Both modes run the same ``map_function``, so the bound is checked
        once, on the shared implementation. Over the limit the layer is
        drawn empty with a warning rather than recursing one frame per term.
        """
        assert dr._MAX_EXPR_CHARS > 0
        long_expr = "+".join(["x"] * (dr._MAX_EXPR_CHARS // 2 + 20))
        assert len(long_expr) > dr._MAX_EXPR_CHARS

        from bokeh.plotting import figure as _figure
        import warnings as _w
        mapper = dr.GlyphMapper()
        with _w.catch_warnings(record=True) as caught:
            _w.simplefilter("always")
            result = mapper.map_function(_figure(), long_expr, (0.0, 1.0), 5, {})
        rend = result[0] if isinstance(result, (list, tuple)) else result
        data = getattr(getattr(rend, "data_source", None), "data", {})
        assert len(data.get("x_fn", [])) == 0, (
            "an over-long expression was evaluated; the length bound is the "
            "only thing standing between a crafted expression and a "
            "recursion one frame deep per term"
        )
        assert any("over the" in str(c.message) for c in caught), (
            "the layer was dropped without saying why: %r"
            % [str(c.message) for c in caught]
        )

    def test_the_served_evaluator_does_not_compute_integer_powers(self):
        """`function 9^9^9^9' must not be computed exactly.

        The served app used to guarantee this by rewriting integer constants
        to floats before evaluating -- hence the old assertion on
        ``fix_missing_locations``. ``map_function`` reaches the same end
        another way, so the guarantee is asserted by BEHAVIOUR rather than by
        the spelling of one implementation of it. Every form below returned
        in well under a second and drew nothing; the sibling test above
        covers the served app end to end.
        """
        from bokeh.plotting import figure as _figure
        import time as _time
        import warnings as _w
        mapper = dr.GlyphMapper()
        for expr in ("9**9**9**9", "x**9**9**9", "x*9**9**9",
                     "2**10000000", "2**200000"):
            started = _time.time()
            with _w.catch_warnings():
                _w.simplefilter("ignore")
                result = mapper.map_function(_figure(), expr, (1.0, 2.0), 5, {})
            elapsed = _time.time() - started
            rend = result[0] if isinstance(result, (list, tuple)) else result
            data = getattr(getattr(rend, "data_source", None), "data", {})
            assert elapsed < 5.0, (
                "%r took %.1fs; an integer power bomb reached the evaluator"
                % (expr, elapsed)
            )
            assert len(data.get("x_fn", [])) == 0, (
                "%r produced points; it should have been refused" % expr
            )
        # And an ordinary power still works, so the guard is not a blanket ban.
        with _w.catch_warnings():
            _w.simplefilter("ignore")
            ok = mapper.map_function(_figure(), "x**2", (1.0, 2.0), 5, {})
        ok_r = ok[0] if isinstance(ok, (list, tuple)) else ok
        assert len(getattr(getattr(ok_r, "data_source", None), "data", {})
                   .get("x_fn", [])) == 5

    def test_a_power_tower_does_not_hang_the_served_app(self, tmp_path):
        import importlib.util
        import itertools
        import json
        import warnings as _w
        import pandas as pd
        sys.path.insert(0, _HERE)
        from bokeh.document import Document
        from conftest import make_data_json
        tag = next(itertools.count(9000))
        sp = tmp_path / "s.json"
        dp = tmp_path / "d.json"
        sp.write_text(json.dumps({
            "graphs": [{"name": "g1", "graph_options": {"name": "g1"},
                        "options": {},
                        "plots": [{"type": "scatter", "yvar": "y",
                                   "xvar": "x", "options": {}},
                                  {"type": "function", "expr": "9^9^9^9",
                                   "options": {}}]}],
            "kpis": [],
            "build_options": {"layout": "auto", "registry": "g1",
                              "level": "95", "formats": {}, "theme": "",
                              "scheme": "", "session_scheme": ""}}))
        dp.write_text(json.dumps(make_data_json(
            pd.DataFrame({"x": [1.0, 2.0], "y": [3.0, 4.0]}))))
        ap = tmp_path / f"a_{tag}.py"
        with _w.catch_warnings():
            _w.simplefilter("ignore")
            dr.ServerAppBuilder(str(sp), str(dp)).build(str(ap))
        ms = importlib.util.spec_from_file_location(f"_rl_{tag}", str(ap))
        mod = importlib.util.module_from_spec(ms)
        with _w.catch_warnings():
            _w.simplefilter("ignore")
            ms.loader.exec_module(mod)
            mod.make_document(Document())     # must return, not hang
