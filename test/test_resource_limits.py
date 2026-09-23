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


# ===========================================================================
# WP-19 -- the resource limits
# ===========================================================================
#
# No constant bounded a dropdown, a by(), the tabs, the filters, the graphs,
# a graph's plots or the dataset (GAPS.md I2).  Measured 23sep2026:
#
#     filter on 200,000 distinct values   200,001 options, 38.8 MB, 954 MB RSS
#     by() on 1,000 groups                29.2 s, 7.3 MB, 1,000 figures
#     300 graphs                          7.9 s, 4.0 MB
#     tabs() with 3,000 tabs              14.4 s, 3.9 MB
#     4,000,000 cells                     94.9 MB, 2.1 GB RSS, rc 0
#
# Each is now a limit with a default, a hard ceiling, and a global macro
# that moves it; every clamp says so, naming the limit and the global
# (ROADMAP BR-19.2).  dash.ado refuses graphs, plots and cells before the
# renderer runs; the renderer holds every limit itself as well, in both
# modes, for a spec that did not come through dash.ado.

import importlib.util
import itertools
import json as _json
import symtable

import pandas as pd
from bokeh.document import Document
from bokeh.models import RangeSlider, Select

sys.path.insert(0, _HERE)
from conftest import make_data_json  # noqa: E402

_SEQ = itertools.count(1)


def _graph(name, plots=None, **graph_opts):
    go = {"name": name}
    go.update(graph_opts)
    return {"name": name, "graph_options": go, "options": {},
            "plots": plots or [{"type": "scatter", "yvar": "y", "xvar": "x",
                                "options": {}}]}


def _spec(graphs, build=None, kpis=None, limits=None):
    kpis = kpis or []
    names = [g["name"] for g in graphs] + [k["name"] for k in kpis]
    bo = {"layout": "auto", "registry": " ".join(names), "level": "95",
          "formats": {}, "theme": "", "scheme": "", "session_scheme": ""}
    bo.update(build or {})
    if limits is not None:
        bo["limits"] = limits
    return {"graphs": graphs, "kpis": kpis, "build_options": bo}


def _kpi(name, var="y"):
    return {"name": name, "stat": "mean", "var": var, "fmt": "",
            "title": name, "subtitle": "", "color": "", "bgcolor": "",
            "update": "filter"}


def _frame(n=12, groups=None):
    """y, x and g (``groups`` distinct values), plus a string column s."""
    groups = groups or n
    return pd.DataFrame({
        "y": [float(i % 7) for i in range(n)],
        "x": [float(i) for i in range(n)],
        "g": [float(i % groups) for i in range(n)],
        "s": ["v%03d" % (i % groups) for i in range(n)],
    })


def _write(tmp_path, spec, df):
    tag = next(_SEQ)
    sp = tmp_path / f"rl_spec_{tag}.json"
    dp = tmp_path / f"rl_data_{tag}.json"
    sp.write_text(_json.dumps(spec))
    data = make_data_json(df)
    # make_data_json marks every column numeric; a text column here is a
    # Stata string variable, as jsonio would say.  (pandas 3 gives text its
    # own `str' dtype, not object.)
    for col in df.columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            data["StataJSON"]["variableIsString"][col] = True
            data["StataJSON"]["variableTypeIsString"][col] = True
    dp.write_text(_json.dumps(data))
    return tag, str(sp), str(dp)


def _standalone(tmp_path, spec, df):
    """``(renderer, html, warnings)`` from the saved-dashboard renderer."""
    _, sp, dp = _write(tmp_path, spec, df)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r = dr.DashRenderer(sp, dp)
        html = r.render()
    return r, html, [str(w.message) for w in caught]


def _served(tmp_path, spec, df):
    """``(document, build warnings, session warnings, app source)``."""
    tag, sp, dp = _write(tmp_path, spec, df)
    ap = tmp_path / f"rl_app_{tag}.py"
    with warnings.catch_warnings(record=True) as built:
        warnings.simplefilter("always")
        dr.ServerAppBuilder(sp, dp).build(str(ap))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ms = importlib.util.spec_from_file_location(f"_rl_app_{tag}", str(ap))
        mod = importlib.util.module_from_spec(ms)
        ms.loader.exec_module(mod)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        doc = Document()
        mod.make_document(doc)
    return (doc, [str(w.message) for w in built],
            [str(w.message) for w in caught], ap.read_text())


def _walk(doc):
    seen, out = set(), []

    def visit(m):
        if m is None or id(m) in seen:
            return
        seen.add(id(m))
        out.append(m)
        for attr in ("children", "tabs", "child", "toolbar"):
            k = getattr(m, attr, None)
            if isinstance(k, (list, tuple)):
                for c in k:
                    visit(c[0] if isinstance(c, tuple) else c)
            elif k is not None and hasattr(k, "id"):
                visit(k)

    for root in doc.roots:
        visit(root)
    return out


def _named(msgs, *needles):
    return [m for m in msgs if all(n in m for n in needles)]


class TestTheLimitsTable:
    """One table: a default, a ceiling nothing moves, and the global."""

    def test_every_limit_has_a_default_within_its_ceiling(self):
        assert set(dr._DASH_LIMITS) == {
            "cells", "graphs", "plots", "filter_options", "by_groups",
            "tabs", "filters"}
        for key, (default, ceiling, glob) in dr._DASH_LIMITS.items():
            assert 1 <= default <= ceiling, key
            assert glob == "dash_max_" + key, key

    def test_no_limit_is_set_by_default(self):
        assert dr._dash_limits({}) == {
            k: v[0] for k, v in dr._DASH_LIMITS.items()}
        assert dr._dash_limits(None) == dr._dash_limits({})
        assert dr._dash_limits({"limits": "cells=5"}) == dr._dash_limits({})

    def test_a_set_limit_is_honoured(self):
        got = dr._dash_limits({"limits": {"cells": 100, "tabs": "7",
                                          "by_groups": 3.0}})
        assert got["cells"] == 100
        assert got["tabs"] == 7
        assert got["by_groups"] == 3
        assert got["graphs"] == dr._DASH_LIMITS["graphs"][0]

    @pytest.mark.parametrize("bad", [0, -1, 1001, 1.5, True, "abc", "1e3",
                                     "", None, [5], "12345678901"])
    def test_a_bad_value_is_named_and_the_default_used(self, bad):
        dr._dash_reset_notes()
        got, msgs = _warns(lambda: dr._dash_limits(
            {"limits": {"graphs": bad}}))
        assert got["graphs"] == dr._DASH_LIMITS["graphs"][0]
        assert _named(msgs, "dash_max_graphs", "1,000"), msgs

    def test_the_ceiling_cannot_be_lifted_by_the_spec(self):
        dr._dash_reset_notes()
        got, msgs = _warns(lambda: dr._dash_limits(
            {"limits": {"cells": 20_000_001}}))
        assert got["cells"] == 5_000_000
        assert _named(msgs, "dash_max_cells", "20,000,000"), msgs
        got = dr._dash_limits({"limits": {"cells": 20_000_000}})
        assert got["cells"] == 20_000_000

    def test_the_hint_names_the_global_and_its_ceiling(self):
        assert dr._dash_limit_hint("tabs", "draw more") == (
            "set global dash_max_tabs to draw more (at most 500)")
        assert dr._dash_limit_hint("tabs", "draw more", start=True) \
            .startswith("Set global dash_max_tabs")


class TestAnOversizedDatasetIsRefused:
    """AC-19.3: refused with a clear message, not written at 95 MB."""

    def test_at_the_limit_nothing_is_raised(self):
        dr._dash_refuse_oversized(50, 2, {"cells": 100}, "dashboard")

    def test_over_the_limit_the_message_says_what_and_how(self):
        with pytest.raises(dr.DashLimitError) as exc:
            dr._dash_refuse_oversized(51, 2, {"cells": 100}, "dashboard")
        msg = str(exc.value)
        for needle in ("102 values", "51 observations x 2 variables",
                       "more than the 100", "keep, drop, sample or collapse",
                       "set global dash_max_cells", "at most 20,000,000"):
            assert needle in msg, (needle, msg)
        assert "if" not in msg.split("Reduce")[1].split(",")[0], (
            "an if qualifier does not reduce what is exported")

    def test_the_saved_renderer_refuses_before_drawing(self, tmp_path):
        spec = _spec([_graph("g1")], limits={"cells": 10})
        _, sp, dp = _write(tmp_path, spec, _frame(12))   # 48 cells
        with pytest.raises(dr.DashLimitError, match="48 values"):
            dr.DashRenderer(sp, dp)

    def test_the_saved_renderer_draws_within_the_limit(self, tmp_path):
        spec = _spec([_graph("g1")], limits={"cells": 48})
        r, html, _ = _standalone(tmp_path, spec, _frame(12))
        assert "g1" in r.figures and len(html) > 1000

    def test_the_server_app_is_refused_at_build(self, tmp_path):
        spec = _spec([_graph("g1")], limits={"cells": 10})
        _, sp, dp = _write(tmp_path, spec, _frame(12))
        with pytest.raises(dr.DashLimitError, match="server app"):
            dr.ServerAppBuilder(sp, dp).build(str(tmp_path / "a.py"))
        assert not (tmp_path / "a.py").exists()

    def test_the_default_limit_is_five_million_cells(self):
        assert dr._dash_limits({})["cells"] == 5_000_000
        assert dr._LARGE_DATASET_CELLS < dr._DASH_LIMITS["cells"][0], (
            "the report must come before the refusal")

    def test_the_size_estimate_is_the_measured_one(self, tmp_path):
        """_HTML_BYTES_PER_CELL is used to tell the user how big the page
        will be; it must be within a factor of two of what is written."""
        n = 50_000
        rng = np.random.default_rng(5)
        df = pd.DataFrame({"y": rng.normal(size=n), "x": rng.normal(size=n)})
        spec = _spec([_graph("g1")])
        _, html, _ = _standalone(tmp_path, spec, df)
        est = n * 2 * dr._HTML_BYTES_PER_CELL
        assert 0.5 < len(html) / est < 2.0, (len(html), est)


class TestTheGraphAndPlotLimits:
    """TR-19.3: dash.ado refuses at registration; the renderer holds the
    same limits for a spec that did not come through it."""

    def test_graphs_and_kpis_past_the_limit_are_dropped_in_registry_order(self):
        spec = _spec([_graph("a"), _graph("b"), _graph("c")],
                     kpis=[_kpi("k1"), _kpi("k2")])
        spec["build_options"]["registry"] = "k1 a k2 b c"
        dr._dash_reset_notes()
        out, msgs = _warns(lambda: dr._dash_cap_spec(
            spec, dict(dr._dash_limits({}), graphs=3)))
        assert [g["name"] for g in out["graphs"]] == ["a"]
        assert [k["name"] for k in out["kpis"]] == ["k1", "k2"]
        assert _named(msgs, "5 graphs and KPI cards", "the 3",
                      "dash_max_graphs", "1,000"), msgs
        assert len(spec["graphs"]) == 3, "the caller's spec was modified"

    def test_a_graph_keeps_its_first_plots(self):
        plots = [{"type": "scatter", "yvar": "y%d" % i, "xvar": "x",
                  "options": {}} for i in range(5)]
        spec = _spec([_graph("g1", plots)])
        out, msgs = _warns(lambda: dr._dash_cap_spec(
            spec, dict(dr._dash_limits({}), plots=3)))
        assert [p["yvar"] for p in out["graphs"][0]["plots"]] == \
            ["y0", "y1", "y2"]
        assert _named(msgs, "'g1' has 5 plots", "the 3", "dash_max_plots"), \
            msgs
        assert len(spec["graphs"][0]["plots"]) == 5

    def test_within_the_limits_the_spec_is_unchanged(self):
        spec = _spec([_graph("a"), _graph("b")], kpis=[_kpi("k1")])
        out, msgs = _warns(lambda: dr._dash_cap_spec(spec, dr._dash_limits({})))
        assert out == spec and not msgs

    def test_both_modes_draw_only_the_graphs_within_the_limit(self, tmp_path):
        spec = _spec([_graph("a"), _graph("b"), _graph("c")],
                     limits={"graphs": 2})
        r, _, msgs = _standalone(tmp_path, spec, _frame())
        assert sorted(r.figures) == ["a", "b"]
        assert _named(msgs, "3 graphs and KPI cards", "dash_max_graphs")
        doc, built, _, _ = _served(tmp_path, spec, _frame())
        figs = [m for m in _walk(doc) if type(m).__name__ == "figure"]
        assert len(figs) == 2
        assert _named(built, "3 graphs and KPI cards", "dash_max_graphs")


class TestADropdownOnAContinuousVariable:
    """AC-19.1: it warns and is capped.  A numeric or date variable gets the
    widget a continuous variable wants; a string keeps its first values."""

    def test_a_numeric_variable_over_the_limit_becomes_a_range(self):
        dr._dash_reset_notes()
        col = pd.Series([float(i) for i in range(50)])
        eff, msgs = _warns(lambda: dr._dash_filter_effective_type(
            "dropdown", "price", col, 10))
        assert eff == "range"
        assert _named(msgs, "filter(price) has 50 distinct values",
                      "the 10 a dropdown lists", "type(range)",
                      "type(slider)", "dash_max_filter_options",
                      "100,000"), msgs

    def test_a_date_variable_over_the_limit_becomes_a_range(self):
        dr._dash_reset_notes()
        col = pd.Series(pd.date_range("2000-01-01", periods=30, freq="D"))
        eff, _ = _warns(lambda: dr._dash_filter_effective_type(
            "dropdown", "day", col, 10))
        assert eff == "range"

    def test_a_string_variable_over_the_limit_keeps_its_dropdown(self):
        dr._dash_reset_notes()
        col = pd.Series(["c%02d" % i for i in range(30)])
        eff, msgs = _warns(lambda: dr._dash_filter_effective_type(
            "dropdown", "make", col, 10))
        assert eff == "dropdown"
        assert _named(msgs, "filter(make) has 30 distinct values",
                      "the first 10 in sort order are listed",
                      "dash_max_filter_options"), msgs

    def test_within_the_limit_nothing_changes(self):
        dr._dash_reset_notes()
        col = pd.Series([1.0, 2.0, 2.0, None, 3.0])
        eff, msgs = _warns(lambda: dr._dash_filter_effective_type(
            "dropdown", "rep78", col, 3))
        assert eff == "dropdown" and not msgs
        for other in ("range", "slider"):
            assert dr._dash_filter_effective_type(
                other, "x", pd.Series(range(99)), 3) == other

    def test_the_widget_lists_at_most_the_limit(self):
        dr._dash_reset_notes()
        col = pd.Series(["c%02d" % i for i in range(30)])
        (w, _s), msgs = _warns(lambda: dr._dash_filter_widget(
            "dropdown", "make", col, "Make", max_options=10))
        assert len(w.options) == 11                     # All + 10
        assert [v for v, _ in w.options[1:]] == ["c%02d" % i
                                                 for i in range(10)]
        assert _named(msgs, "filter(make)", "dash_max_filter_options")

    def test_a_widget_built_without_a_limit_uses_the_default(self):
        dr._dash_reset_notes()
        n = dr._DASH_LIMITS["filter_options"][0] + 50
        col = pd.Series(["c%05d" % i for i in range(n)])
        (w, _s), msgs = _warns(lambda: dr._dash_filter_widget(
            "dropdown", "id", col, "Id"))
        assert len(w.options) == dr._DASH_LIMITS["filter_options"][0] + 1
        assert _named(msgs, "filter(id)"), "truncated without a word"

    def test_the_saved_page_draws_a_range_and_filters_by_one(self, tmp_path):
        spec = _spec([_graph("g1")], build={"filter": "x, type(dropdown)"},
                     limits={"filter_options": 5})
        r, html, msgs = _standalone(tmp_path, spec, _frame(12))
        kinds = [type(w).__name__ for w in r.filter_widgets]
        assert kinds == ["RangeSlider"], kinds
        assert _named(msgs, "filter(x) has 12 distinct values", "type(range)")
        # The page's script filters by the spec's type: it must say range,
        # or it would compare a slider's [lo, hi] as a category.
        cb_specs = [_json.loads(cb.args["filter_specs_json"])
                    for cb in r.filter_callbacks]
        assert cb_specs and all(s[0]["type"] == "range" for s in cb_specs)

    def test_the_served_app_draws_a_range_and_says_so_at_build(self, tmp_path):
        spec = _spec([_graph("g1")], build={"filter": "x, type(dropdown)"},
                     limits={"filter_options": 5})
        doc, built, _, src = _served(tmp_path, spec, _frame(12))
        assert list(doc.select({"type": RangeSlider}))
        assert not list(doc.select({"type": Select}))
        assert _named(built, "filter(x) has 12 distinct values",
                      "type(range)")
        assert "'type': 'range'" in src

    def test_a_saved_string_dropdown_lists_its_first_values(self, tmp_path):
        spec = _spec([_graph("g1")], build={"filter": "s, type(dropdown)"},
                     limits={"filter_options": 5})
        r, _, msgs = _standalone(tmp_path, spec, _frame(12))
        kinds = [type(w).__name__ for w in r.filter_widgets]
        assert kinds == ["Select"], kinds
        assert len(r.filter_widgets[0].options) == 6
        assert len(_named(msgs, "filter(s) has 12 distinct values")) == 1, (
            "said more than once in one render: %r" % msgs)

    def test_a_served_string_dropdown_lists_its_first_values(self, tmp_path):
        spec = _spec([_graph("g1")], build={"filter": "s, type(dropdown)"},
                     limits={"filter_options": 5})
        doc, built, _, _ = _served(tmp_path, spec, _frame(12))
        sel = list(doc.select({"type": Select}))
        assert len(sel) == 1 and len(sel[0].options) == 6
        assert _named(built, "filter(s) has 12 distinct values",
                      "the first 5")


class TestByOnAHighCardinalityVariable:
    """AC-19.2: it warns and is capped."""

    def test_the_first_groups_in_sort_order_are_kept(self):
        dr._dash_reset_notes()
        df = pd.DataFrame({"g": [float(i % 12) for i in range(36)][::-1],
                           "y": [1.0] * 36})
        got, msgs = _warns(lambda: dr._dash_by_groups(
            df, ["g"], False, 5, "g1"))
        assert [k for k, _ in got] == [0.0, 1.0, 2.0, 3.0, 4.0]
        assert all(len(f) == 3 for _, f in got)
        assert _named(msgs, "by(g) on graph 'g1' has 12 groups",
                      "the 5 one graph draws", "dash_max_by_groups",
                      "1,000"), msgs

    def test_within_the_limit_every_group_is_kept_silently(self):
        dr._dash_reset_notes()
        df = pd.DataFrame({"g": [1.0, 2.0, 2.0, 3.0], "y": [1.0] * 4})
        got, msgs = _warns(lambda: dr._dash_by_groups(df, ["g"], False, 3))
        assert [k for k, _ in got] == [1.0, 2.0, 3.0] and not msgs

    def test_missing_is_one_more_group_only_when_asked_for(self):
        df = pd.DataFrame({"g": [1.0, np.nan, 2.0], "y": [1.0] * 3})
        kept = dr._dash_by_groups(df, ["g"], True, 10)
        assert len(kept) == 3
        assert len(dr._dash_by_groups(df.dropna(), ["g"], False, 10)) == 2

    def test_two_by_variables_count_their_combinations(self):
        dr._dash_reset_notes()
        df = pd.DataFrame({"a": [1.0, 1.0, 2.0, 2.0],
                           "b": [1.0, 2.0, 1.0, 2.0], "y": [1.0] * 4})
        got, msgs = _warns(lambda: dr._dash_by_groups(
            df, ["a", "b"], False, 3, "g1"))
        assert [k for k, _ in got] == [(1.0, 1.0), (1.0, 2.0), (2.0, 1.0)]
        assert _named(msgs, "by(a b)", "4 groups")

    def test_both_modes_draw_the_first_panels(self, tmp_path):
        spec = _spec([_graph("g1", by="g")], limits={"by_groups": 4})
        r, _, msgs = _standalone(tmp_path, spec, _frame(24, groups=12))
        panels = [k for k in r.figures if k.startswith("g1")]
        assert len(panels) == 4, sorted(r.figures)
        assert _named(msgs, "by(g) on graph 'g1' has 12 groups")
        doc, built, _, _ = _served(tmp_path, spec, _frame(24, groups=12))
        figs = [m for m in _walk(doc) if type(m).__name__ == "figure"]
        assert len(figs) == 4
        assert _named(built, "by(g) on graph 'g1' has 12 groups"), (
            "the served build did not say so; a server app's own output "
            "may never reach the user")

    def test_the_served_count_is_of_the_qualified_rows(self, tmp_path):
        # 12 groups overall, 3 inside the qualifier: no warning, 3 panels.
        spec = _spec([_graph("g1", by="g", if_expr="g < 3")],
                     limits={"by_groups": 4})
        doc, built, _, _ = _served(tmp_path, spec, _frame(24, groups=12))
        assert not _named(built, "groups, more than")
        figs = [m for m in _walk(doc) if type(m).__name__ == "figure"]
        assert len(figs) == 3


class TestTheTabAndFilterLimits:
    def test_tabs_past_the_limit_are_dropped_with_a_note(self):
        dr._dash_reset_notes()
        got, msgs = _warns(lambda: dr._dash_parse_tabs(
            "A: g1 / B: g1 / C: g1 / D: g1", ["g1"], 2))
        assert [t for t, _ in got] == ["A", "B"]
        assert _named(msgs, "tabs() has 4 tabs", "the 2",
                      "dash_max_tabs", "500"), msgs

    def test_the_default_tab_limit_applies_without_one(self):
        dr._dash_reset_notes()
        n = dr._DASH_LIMITS["tabs"][0] + 10
        tabs = " / ".join("T%d: g1" % i for i in range(n))
        got, msgs = _warns(lambda: dr._dash_parse_tabs(tabs, ["g1"]))
        assert len(got) == dr._DASH_LIMITS["tabs"][0]
        assert _named(msgs, "tabs() has %d tabs" % n)

    def test_filters_past_the_limit_are_dropped_with_a_note(self):
        dr._dash_reset_notes()
        specs = [{"varname": "v%d" % i, "type": "dropdown"} for i in range(5)]
        got, msgs = _warns(lambda: dr._dash_cap_filters(specs, 3))
        assert [s["varname"] for s in got] == ["v0", "v1", "v2"]
        assert _named(msgs, "5 filters", "the 3", "dash_max_filters",
                      "200"), msgs

    def test_both_modes_draw_the_tabs_within_the_limit(self, tmp_path):
        spec = _spec([_graph("a"), _graph("b"), _graph("c")],
                     build={"tabs": "A: a / B: b / C: c"},
                     limits={"tabs": 2})
        r, html, msgs = _standalone(tmp_path, spec, _frame())
        assert html.count('"name":"TabPanel"') == 2, (
            html.count('"name":"TabPanel"'))
        assert _named(msgs, "tabs() has 3 tabs")
        doc, _b, _s, _ = _served(tmp_path, spec, _frame())
        tabs = [m for m in _walk(doc) if type(m).__name__ == "Tabs"]
        assert len(tabs) == 1 and len(tabs[0].tabs) == 2

    def test_both_modes_build_the_filters_within_the_limit(self, tmp_path):
        spec = _spec([_graph("g1")],
                     build={"filter": "x, type(range) || y, type(range) || "
                                      "g, type(range)"},
                     limits={"filters": 2})
        r, _, msgs = _standalone(tmp_path, spec, _frame())
        assert len(r.filter_widgets) == 2
        assert _named(msgs, "3 filters", "dash_max_filters")
        doc, built, _, _ = _served(tmp_path, spec, _frame())
        assert len(list(doc.select({"type": RangeSlider}))) == 2
        assert _named(built, "3 filters", "dash_max_filters")


class TestTheServedAppDefinesEveryNameItReads:
    """A name the builder forgets to copy is a NameError on the served page
    when a session opens, not when the app is built.  This reads every
    global name each function in the generated app refers to and requires
    each to be defined in the app or be a builtin -- the check that caught
    ``_dash_limit_hint`` missing from the copy list when a helper began to
    call it (measured by removing it: the check named it and its caller)."""

    def test_no_function_in_the_app_reads_an_undefined_global(self, tmp_path):
        import builtins
        spec = _spec([_graph("g1", by="g")],
                     build={"filter": "s, type(dropdown) || x, type(range)",
                            "tabs": "A: g1"},
                     kpis=[_kpi("k1")])
        _, _, _, src = _served(tmp_path, spec, _frame())
        top = symtable.symtable(src, "app.py", "exec")
        defined = {s.get_name() for s in top.get_symbols()
                   if s.is_assigned() or s.is_imported()}
        used = {}

        def walk(t, path):
            for c in t.get_children():
                p = path + [c.get_name()]
                for sym in c.get_symbols():
                    if sym.is_global() and sym.is_referenced():
                        used.setdefault(sym.get_name(), "/".join(p))
                walk(c, p)

        walk(top, [])
        missing = {n: where for n, where in used.items()
                   if n not in defined and not hasattr(builtins, n)}
        assert not missing, missing
        for name in ("_DASH_LIMITS", "_dash_limits", "_dash_limit_hint",
                     "_dash_by_groups", "_dash_dropdown_values",
                     "_dash_filter_truncation_note"):
            assert name in defined, name


class TestTheHelpDocumentsEveryLimit:
    """The user is told to set a global; the help must say which, what it
    defaults to, and how far it goes -- the same numbers the code uses."""

    @staticmethod
    def _help():
        with open(os.path.join(_HERE, "..", "dash.sthlp"),
                  encoding="utf-8") as fh:
            return fh.read()

    def test_every_global_appears_with_its_default_and_ceiling(self):
        text = self._help()
        sec = text[text.index("{marker limits}"):text.index("{marker examples}")]
        for key, (default, ceiling, glob) in dr._DASH_LIMITS.items():
            line_start = sec.index("{cmd:$%s}" % glob)
            # SMCL wraps its lines; the words are what the user reads.
            entry = " ".join(
                sec[line_start:sec.index("{p_end}", line_start)].split())
            assert "default %s" % f"{default:,}" in entry, (key, entry)
            assert "at most %s" % f"{ceiling:,}" in entry, (key, entry)

    def test_the_bytes_per_value_figure_matches_the_constant(self):
        assert "about %d bytes a value" % dr._HTML_BYTES_PER_CELL \
            in " ".join(self._help().split())


class TestTheSizeWarningGivesAdviceThatWorks:
    """It told the user to add an `if' or `in' qualifier.  dash exports every
    observation and applies qualifiers itself, so a qualifier does not shrink
    what is exported or held in memory, and shrinks a saved page only when
    it has no filter -- measured on 200,000 rows: 8.4 MB, 1.5 MB with
    `if x < 1000', 8.8 MB with the same qualifier and one filter."""

    def test_the_advice_is_to_reduce_the_data_in_memory(self):
        _, msgs = _warns(lambda: dr._report_dataset_shape(
            600_000, 2, "dashboard"))
        assert len(msgs) == 1, msgs
        assert "keep, drop, sample or collapse" in msgs[0]
        assert "qualifier" not in msgs[0]
        assert "roughly 29 MB" in msgs[0], msgs[0]      # 1.2e6 cells x 24

    def test_a_small_dataset_is_not_reported(self):
        _, msgs = _warns(lambda: dr._report_dataset_shape(
            1000, 17, "dashboard"))
        assert not msgs


class TestTheBoundsThatAlreadyWorkedAreKept:
    """TR-19.6: the bounds that already held stay where they were, in both
    modes.  A value pinned here and changed on purpose is a one-line edit;
    one changed by accident, or lost from the served app, is caught."""

    def test_the_values(self):
        assert dr._MAX_MBANDS == 1000
        assert dr._MAX_EXPR_CHARS == 5000
        assert dr._FP_GRID_MAX == 20000
        assert dr._WEBGL_THRESHOLD == 10_000
        # _histogram_grid's own bin ceiling is local to it; asserted by its
        # source.  The function layer's n() is clamped by behaviour.
        import inspect
        assert "_MAX_BINS = 1000" in inspect.getsource(dr.GlyphMapper)
        assert dr._dash_function_args({"n": "99999999"})[1] == 10000
        assert dr._dash_function_args({"n": "1"})[1] == 2

    def test_the_served_app_carries_the_same_values(self, tmp_path):
        spec = _spec([_graph("g1")])
        tag, sp, dp = _write(tmp_path, spec, _frame())
        ap = tmp_path / f"rl_bounds_{tag}.py"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(str(ap))
            ms = importlib.util.spec_from_file_location(
                f"_rl_bounds_{tag}", str(ap))
            mod = importlib.util.module_from_spec(ms)
            ms.loader.exec_module(mod)
        for name in ("_MAX_MBANDS", "_MAX_EXPR_CHARS", "_FP_GRID_MAX",
                     "_WEBGL_THRESHOLD", "_DASH_LIMITS"):
            assert getattr(mod, name) == getattr(dr, name), name

    def test_the_port_is_clamped_in_every_place_it_is_read(self):
        import inspect
        src = inspect.getsource(dr)
        # main(), the launcher, and the generated app's own flag.
        assert src.count("max(1024, min(") >= 3, (
            "a port read somewhere without the 1024..65535 clamp")


class TestTheHelpersOneByOne:
    """Each new helper on its own (CLAUDE.md rule 4)."""

    def test_dropdown_values_are_the_listed_options_sorted(self):
        got = dr._dash_dropdown_values(pd.Series([3.0, 1.0, None, 1.0, 2.0]))
        assert got == sorted(set(got), key=dr._dash_option_sort_key)
        assert len(got) == 3
        assert dr._dash_dropdown_values(pd.Series(["b", "a", None, "b"])) \
            == ["a", "b"]

    def test_the_truncation_note_names_everything_the_user_needs(self):
        msg = dr._dash_filter_truncation_note("make", 3142, 1000)
        for needle in ("filter(make)", "3,142 distinct values",
                       "the 1,000 a dropdown lists", "first 1,000",
                       "set global dash_max_filter_options",
                       "at most 100,000"):
            assert needle in msg, (needle, msg)

    def test_a_renderer_built_without_init_has_the_default_limits(self):
        r = dr.DashRenderer.__new__(dr.DashRenderer)
        assert r._limits == dr._dash_limits({})
        r.limits = dict(dr._dash_limits({}), tabs=3)
        assert r._limits["tabs"] == 3

    def _builder(self, tmp_path, spec, df):
        _, sp, dp = _write(tmp_path, spec, df)
        return dr.ServerAppBuilder(sp, dp)

    def test_the_builder_parses_the_data_once(self, tmp_path):
        b = self._builder(tmp_path, _spec([_graph("g1")]), _frame())
        assert b._data() is b._data()

    def test_the_builders_frame_is_the_saved_renderers(self, tmp_path):
        spec = _spec([_graph("g1")])
        b = self._builder(tmp_path, spec, _frame())
        frame = b._frame()
        _, sp, dp = _write(tmp_path, spec, _frame())
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            saved = dr.DashRenderer(sp, dp).df
        pd.testing.assert_frame_equal(frame, saved)
        assert not pd.api.types.is_numeric_dtype(frame["s"])

    def test_the_by_plan_warns_over_the_limit_only(self, tmp_path):
        spec = _spec([_graph("g1", by="g")], limits={"by_groups": 4})
        b = self._builder(tmp_path, spec, _frame(24, groups=12))
        dr._dash_reset_notes()
        _, msgs = _warns(b._plan_by_groups)
        assert _named(msgs, "by(g) on graph 'g1' has 12 groups")
        spec = _spec([_graph("g1", by="g")], limits={"by_groups": 12})
        b = self._builder(tmp_path, spec, _frame(24, groups=12))
        dr._dash_reset_notes()
        _, msgs = _warns(b._plan_by_groups)
        assert not msgs

    def test_the_build_lets_go_of_the_parsed_data(self, tmp_path):
        spec = _spec([_graph("g1", by="g")], build={"filter": "g, type(dropdown)"})
        b = self._builder(tmp_path, spec, _frame())
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            b.build(str(tmp_path / "a.py"))
        assert b._data_cache is None and b._frame_cache is None


class TestTheTwoLanguagesAgree:
    """dash.ado enforces cells, graphs and plots itself and carries the
    user's globals to the renderer; the renderer holds every limit too.
    Two tables, so a test holds them equal: a default raised in one and not
    the other would refuse in Stata what the renderer allows, or the reverse."""

    def test_dash_ado_has_the_same_defaults_and_ceilings(self):
        import re
        with open(os.path.join(_HERE, "..", "dash.ado"), encoding="utf-8") as fh:
            ado = fh.read()
        start = ado.index("program define _dash_limit_table")
        body = ado[start:ado.index("\nend", start)]
        rows = dict((k, (int(d), int(c))) for k, d, c in
                    re.findall(r"(\w+)=(\d+),(\d+)", body))
        assert rows == {k: (v[0], v[1]) for k, v in dr._DASH_LIMITS.items()}

    def test_dash_ado_names_the_same_globals(self):
        with open(os.path.join(_HERE, "..", "dash.ado"), encoding="utf-8") as fh:
            ado = fh.read()
        assert 'local gname "dash_max_`name\'"' in ado
        for _key, (_d, _c, glob) in dr._DASH_LIMITS.items():
            assert glob == "dash_max_" + _key
