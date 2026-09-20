"""
test_jitter.py
Unit and integration tests for jitter() and jseed() options.

Run with:  pytest test/test_jitter.py -v
"""
import sys
import os
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dash_render import GlyphMapper, OptionTranslator, DashRenderer

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def auto_df():
    np.random.seed(42)
    n = 30
    return pd.DataFrame({
        "mpg":    np.random.randint(12, 40, n).astype(float),
        "weight": np.random.randint(1760, 4840, n).astype(float),
        "price":  np.random.randint(3291, 15906, n).astype(float),
        "make":   [f"car{i}" for i in range(n)],
    })


@pytest.fixture
def gm():
    return GlyphMapper()


def _make_source(df, xcol, ycol):
    return ColumnDataSource({xcol: df[xcol].tolist(), ycol: df[ycol].tolist()})


# ============================================================
# JIT-01 through JIT-06  map_scatter with jitter
# ============================================================

class TestMapScatterJitter:
    def test_jitter_uses_jit_columns_as_xy(self, auto_df, gm):
        """JIT-01: renderer x/y fields reference jittered columns when jitter is set."""
        fig = figure()
        src = _make_source(auto_df, "weight", "mpg")
        r = gm.map_scatter(fig, src, "mpg", "weight", {"jitter": "5", "jseed": "42"})
        assert r.glyph.x == "_x_jit"
        assert r.glyph.y == "_y_jit"

    def test_no_jitter_uses_original_columns(self, auto_df, gm):
        """JIT-02: renderer x/y use original column names when jitter absent."""
        fig = figure()
        src = _make_source(auto_df, "weight", "mpg")
        r = gm.map_scatter(fig, src, "mpg", "weight", {})
        assert r.glyph.x == "weight"
        assert r.glyph.y == "mpg"

    def test_jitter_cds_retains_original_columns(self, auto_df, gm):
        """JIT-03: original variable columns present in jittered CDS for hover."""
        fig = figure()
        src = _make_source(auto_df, "weight", "mpg")
        r = gm.map_scatter(fig, src, "mpg", "weight", {"jitter": "5", "jseed": "0"})
        cds_data = r.data_source.data
        assert "weight" in cds_data
        assert "mpg" in cds_data
        assert "_x_jit" in cds_data
        assert "_y_jit" in cds_data

    def test_deterministic_with_jseed(self, auto_df, gm):
        """JIT-04: two renders with same jseed produce identical jitter arrays."""
        fig1, fig2 = figure(), figure()
        src1 = _make_source(auto_df, "weight", "mpg")
        src2 = _make_source(auto_df, "weight", "mpg")
        r1 = gm.map_scatter(fig1, src1, "mpg", "weight", {"jitter": "5", "jseed": "42"})
        r2 = gm.map_scatter(fig2, src2, "mpg", "weight", {"jitter": "5", "jseed": "42"})
        np.testing.assert_array_equal(
            r1.data_source.data["_x_jit"],
            r2.data_source.data["_x_jit"],
        )

    def test_different_jseed_produces_different_jitter(self, auto_df, gm):
        """JIT-05: different jseed values produce different jitter."""
        fig1, fig2 = figure(), figure()
        src1 = _make_source(auto_df, "weight", "mpg")
        src2 = _make_source(auto_df, "weight", "mpg")
        r1 = gm.map_scatter(fig1, src1, "mpg", "weight", {"jitter": "5", "jseed": "1"})
        r2 = gm.map_scatter(fig2, src2, "mpg", "weight", {"jitter": "5", "jseed": "999"})
        assert not np.allclose(
            r1.data_source.data["_x_jit"],
            r2.data_source.data["_x_jit"],
        )

    def test_jitter_zero_no_jit_columns(self, auto_df, gm):
        """jitter(0) should not add jit columns (treated as no jitter)."""
        fig = figure()
        src = _make_source(auto_df, "weight", "mpg")
        r = gm.map_scatter(fig, src, "mpg", "weight", {"jitter": "0"})
        assert r.glyph.x == "weight"
        assert r.glyph.y == "mpg"

    def test_nonnumeric_jitter_ignored(self, auto_df, gm):
        """jitter with non-numeric value is silently ignored."""
        fig = figure()
        src = _make_source(auto_df, "weight", "mpg")
        r = gm.map_scatter(fig, src, "mpg", "weight", {"jitter": "abc"})
        assert r.glyph.x == "weight"
        assert r.glyph.y == "mpg"

    def test_injection_attempt_in_jitter_ignored(self, auto_df, gm):
        """jitter with injection attempt value is silently ignored."""
        fig = figure()
        src = _make_source(auto_df, "weight", "mpg")
        r = gm.map_scatter(fig, src, "mpg", "weight",
                           {"jitter": "5); import os"})
        # float() will raise ValueError → treated as 0 → no jitter
        assert r.glyph.x == "weight"

    def test_extreme_jitter_value_no_crash(self, auto_df, gm):
        """jitter(999999) is clamped to 100, no crash."""
        fig = figure()
        src = _make_source(auto_df, "weight", "mpg")
        r = gm.map_scatter(fig, src, "mpg", "weight", {"jitter": "999999"})
        assert "_x_jit" in r.data_source.data


# ============================================================
# JIT-06 through JIT-08  other plot types
# ============================================================

class TestJitterOnOtherPlots:
    def test_jitter_on_dot_plot(self, auto_df, gm):
        """JIT-06: jitter option works on map_dot (delegates to map_scatter)."""
        fig = figure()
        src = _make_source(auto_df, "weight", "mpg")
        r = gm.map_dot(fig, src, "mpg", "weight", {"jitter": "5", "jseed": "0"})
        # map_dot returns a list with one renderer
        renderer = r if hasattr(r, "glyph") else r[0]
        assert renderer.glyph.x == "_x_jit"

    def test_jitter_on_dropline(self, auto_df, gm):
        """JIT-07: jitter option on dropline adds offset columns to CDS."""
        fig = figure()
        src = _make_source(auto_df, "weight", "mpg")
        renderers = gm.map_dropline(fig, src, "mpg", "weight",
                                    {"jitter": "5", "jseed": "0"})
        # The dot renderer's source should have jittered "x" column != original
        dot = renderers[1]
        xs = np.array(dot.data_source.data["x"])
        orig = np.array(dot.data_source.data["weight"])
        # At least some values should differ
        assert not np.allclose(xs, orig)

    def test_jitter_on_scatteri(self, gm):
        """JIT-08: jitter option on scatteri produces jittered literal coords."""
        fig = figure()
        values = [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]
        r_no_jit = gm.map_scatteri(figure(), values, {})[0]
        r_jit = gm.map_scatteri(fig, values, {"jitter": "20", "jseed": "7"})[0]
        xs_orig = np.array(r_no_jit.data_source.data["x"])
        xs_jit  = np.array(r_jit.data_source.data["x"])
        assert not np.allclose(xs_orig, xs_jit)


# ============================================================
# JIT-09  Line plot ignores jitter
# ============================================================

class TestJitterNotOnLinePlot:
    def test_line_plot_ignores_jitter(self, auto_df, gm):
        """JIT-09: map_line silently ignores jitter option."""
        fig = figure()
        src = _make_source(auto_df, "weight", "mpg")
        r = gm.map_line(fig, src, "mpg", "weight", {"jitter": "5"})
        assert r.glyph.x == "weight"
        assert r.glyph.y == "mpg"
        assert "_x_jit" not in r.data_source.data


# ============================================================
# JIT-10  HTML integration test
# ============================================================

class TestJitterHtmlIntegration:
    def _render(self, options):
        import json as _json
        import tempfile
        data = {
            "mpg":    [20.0, 25.0, 30.0, 22.0, 28.0],
            "weight": [2000.0, 3000.0, 2500.0, 2800.0, 3200.0],
        }
        n = 5
        data_json = {
            "StataJSON": {
                "variableNames": list(data.keys()),
                "variableLabels": {k: k for k in data},
                "valueLabels": {},
                "valueLabelNames": {},
                "variableTypeIsString": {k: False for k in data},
                "values": [{k: data[k][i] for k in data} for i in range(n)],
            }
        }
        spec = {
            "graphs": [{
                "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                           "options": options}],
                "graph_options": {"name": "fig1"},
                "if_expr": "", "in_expr": "",
            }],
            "kpis": [],
            "build_options": {
                "layout": "auto", "link": "", "filter": "",
                "theme": "default", "title": "", "subtitle": "", "registry": "fig1",
            },
        }
        sp, dp, op = [tempfile.mkstemp(s)[1] for s in (".json", ".json", ".html")]
        try:
            with open(sp, "w") as f: _json.dump(spec, f)
            with open(dp, "w") as f: _json.dump(data_json, f)
            from dash_render import DashRenderer as DR
            return DR(sp, dp, op).render()
        finally:
            for p in (sp, dp, op):
                try: os.unlink(p)
                except OSError: pass

    def test_html_contains_jit_column(self):
        """JIT-I1: full render with jitter(5) embeds _x_jit column in Bokeh JSON."""
        html_str = self._render({"jitter": "5", "jseed": "42"})
        assert "_x_jit" in html_str

    def test_html_no_jit_column_without_jitter(self):
        """No jitter → no _x_jit column in output."""
        html_str = self._render({})
        assert "_x_jit" not in html_str


# ============================================================
# Stata spells the seed jitterseed(); dash read only its own jseed()
# ============================================================
#
# `twoway scatter' takes jitter(#) and jitterseed(#). There is no jseed() in
# Stata -- that spelling is dash's own. `_build_jitter_source' read the dash
# spelling and nothing else, and dash.ado put jitterseed on the
# ignoring-unsupported list, so a command pasted straight out of a Stata
# do-file:
#
#     . dash scatter mpg weight, jitter(5) jitterseed(12345)
#     dash: ignoring unsupported option(s): jitterseed()
#
# drew jitter from an unseeded generator -- a different cloud of points on
# every render of the same command -- while reporting the seed as dropped.
# Reproducibility is the entire purpose of the option.

class TestStatasOwnSeedSpelling:
    """The discriminating question is whether the SAME seed repeats.

    Two *different* seeds give two different clouds whether or not the seed
    is read at all, because an unread seed leaves the generator unseeded and
    unseeded draws differ anyway. Only "the same seed twice" separates a seed
    that works from one that is ignored.

    The jittered values live in the source's ``_x_jit``/``_y_jit`` columns,
    not in the original ones -- ``_build_jitter_source`` returns the effective
    names alongside the source. Reading the original column compares an
    untouched array against itself and passes no matter what.
    """

    @staticmethod
    def _cloud(gm, df, options):
        src = _make_source(df, "weight", "mpg")
        out, eff_x, eff_y = gm._build_jitter_source(
            src, "weight", "mpg", options)
        return (np.asarray(out.data[eff_x], dtype=float),
                np.asarray(out.data[eff_y], dtype=float))

    def test_the_jittered_columns_are_not_the_originals(self, gm, auto_df):
        """Guards the guard: if this stops holding, the checks below go blind."""
        src = _make_source(auto_df, "weight", "mpg")
        _out, eff_x, eff_y = gm._build_jitter_source(
            src, "weight", "mpg", {"jitter": "5", "jseed": "1"})
        assert (eff_x, eff_y) != ("weight", "mpg"), (
            "jitter now writes back into the original columns; the seed "
            "checks below must be re-pointed or they compare an untouched "
            "array against itself"
        )

    def test_jitterseed_makes_jitter_reproducible(self, gm, auto_df):
        a = self._cloud(gm, auto_df, {"jitter": "5", "jitterseed": "12345"})
        b = self._cloud(gm, auto_df, {"jitter": "5", "jitterseed": "12345"})
        np.testing.assert_allclose(
            a[0], b[0],
            err_msg="jitterseed() -- Stata's own spelling -- is not seeding "
                    "the generator, so the same command draws a different "
                    "cloud every time it is run",
        )
        np.testing.assert_allclose(a[1], b[1])

    def test_an_unseeded_jitter_really_is_unseeded(self, gm, auto_df):
        """Establishes that the check above can fail at all."""
        a = self._cloud(gm, auto_df, {"jitter": "5"})
        b = self._cloud(gm, auto_df, {"jitter": "5"})
        assert not np.allclose(a[0], b[0]), (
            "jitter with no seed is reproducible, so seeding it could not be "
            "measured by repeating a render"
        )

    def test_the_dash_spelling_still_works(self, gm, auto_df):
        """jseed() is documented, so it stays accepted."""
        a = self._cloud(gm, auto_df, {"jitter": "5", "jseed": "7"})
        b = self._cloud(gm, auto_df, {"jitter": "5", "jseed": "7"})
        np.testing.assert_allclose(a[0], b[0])

    def test_the_two_spellings_agree(self, gm, auto_df):
        """The same seed under either name must give the same jitter."""
        a = self._cloud(gm, auto_df, {"jitter": "5", "jseed": "99"})
        b = self._cloud(gm, auto_df, {"jitter": "5", "jitterseed": "99"})
        np.testing.assert_allclose(
            a[0], b[0],
            err_msg="jseed(99) and jitterseed(99) give different jitter",
        )

    def test_jseed_wins_when_both_are_given(self, gm, auto_df):
        """An explicit dash spelling is not silently overridden."""
        a = self._cloud(gm, auto_df,
                        {"jitter": "5", "jseed": "4", "jitterseed": "5"})
        b = self._cloud(gm, auto_df, {"jitter": "5", "jseed": "4"})
        np.testing.assert_allclose(a[0], b[0])

    def test_jitterseed_is_not_reported_as_unsupported(self):
        """dash.ado must not name an option the renderer honours."""
        import re as _re
        with open(os.path.join(os.path.dirname(__file__), "..", "dash.ado"),
                  encoding="utf-8") as fh:
            src = fh.read()
        i = src.index("program define _dash_parse_plot_opts")
        j = src.index("local _dash_unknown", i)
        pending = _re.findall(r"_dash_pending' (\w+)\"", src[i:j])
        assert "jitterseed" not in pending, (
            "jitterseed() seeds the jitter, but dash.ado still names it in "
            "the ignoring-unsupported note"
        )


class TestEverySeedSiteReadsBothSpellings:
    """Five places read the seed; one fix to one of them is not a fix.

    ``map_scatter`` went through ``_build_jitter_source``, but ``map_dropline``
    and ``map_scatteri`` each read ``options["jseed"]`` themselves, the
    bootstrap bands read it through ``_resolve_seed``, and the generated
    server app emits its own copy. Stata's ``jitterseed()`` reached none of
    them.
    """

    def test_dropline_honours_jitterseed(self, gm, auto_df):
        from bokeh.plotting import figure
        src = _make_source(auto_df, "weight", "mpg")

        def cloud():
            rs = gm.map_dropline(figure(), src, "mpg", "weight",
                                 {"jitter": "5", "jitterseed": "31"})
            return np.asarray(rs[0].data_source.data["x"], dtype=float)

        np.testing.assert_allclose(
            cloud(), cloud(),
            err_msg="map_dropline ignores jitterseed(), so the same command "
                    "draws a different figure every render",
        )

    def test_scatteri_honours_jitterseed(self, gm):
        from bokeh.plotting import figure

        def cloud():
            r = gm.map_scatteri(
                figure(),
                [[1.0, 10.0], [2.0, 20.0], [3.0, 30.0], [4.0, 40.0]],
                {"jitter": "5", "jitterseed": "31"})
            src = r[0].data_source if isinstance(r, list) else r.data_source
            return np.asarray(src.data["x"], dtype=float)

        np.testing.assert_allclose(
            cloud(), cloud(),
            err_msg="map_scatteri ignores jitterseed()",
        )

    def test_the_bootstrap_seed_reads_jitterseed(self):
        import dash_render as _dr
        assert _dr._resolve_seed({"jitterseed": "7"}, default=42) == 7, (
            "a resampling layer ignores jitterseed(), so it always "
            "bootstraps on seed 42"
        )
        assert _dr._resolve_seed({"jseed": "7"}, default=42) == 7
        assert _dr._resolve_seed({}, default=42) == 42
        assert _dr._resolve_seed({"jseed": "not a number"}, default=42) == 42

    def test_a_non_numeric_seed_does_not_crash_dropline(self, gm, auto_df):
        """`int(float(options["jseed"]))` raised on any non-numeric value."""
        from bokeh.plotting import figure
        src = _make_source(auto_df, "weight", "mpg")
        gm.map_dropline(figure(), src, "mpg", "weight",
                        {"jitter": "5", "jseed": "abc"})

    def test_the_served_app_reads_jitterseed(self):
        """The generated app emits its own seed read; it must read both."""
        import inspect as _inspect
        import dash_render as _dr
        src = _inspect.getsource(_dr.ServerAppBuilder)
        assert "jitterseed" in src, (
            "the generated server app never mentions jitterseed(), so a "
            "served figure jitters unseeded where a saved one does not"
        )
