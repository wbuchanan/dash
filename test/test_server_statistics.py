"""Server mode computed different statistics from the same command.

S07 rewrote the statistical layers to Stata's own rules — the kernel-density
bandwidth ``0.9 * min(sd, IQR/1.349) * n^(-1/5)`` with Stata's kernels, the
median-band count ``round(min(sqrt(N), 10*log10(N)))`` taken at the band's
*cross-median* x, lowess at Stata's default ``bwidth(0.8)``. It rewrote them
in ``DashRenderer`` only. ``ServerAppBuilder`` emits its own copies, and they
were left on the pre-S07 code:

* ``_compute_kdensity`` called ``scipy.stats.gaussian_kde``, i.e. a Gaussian
  kernel on Scott's rule — neither Stata's kernel nor Stata's bandwidth — and
  read neither ``kernel()`` nor ``bwidth()``.
* ``_compute_mband`` binned by ``clip(ceil(n/5), 2, 20)`` and placed each
  point at the bin *midpoint*. On auto that is 15 bands where Stata draws 9.
* ``_compute_lowess`` used ``frac=0.5``; Stata's default is 0.8.
* ``_compute_lfit`` evaluated on 100 points where standalone uses 200.

So the same command produced two different curves, and the served one was not
Stata's. These tests compare the two modes' *numbers*, not their appearance.
"""
import itertools
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import ColumnDataSource

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
from conftest import make_data_json, load_app

_SEQ = itertools.count()

_RNG = np.random.default_rng(19780101)
_N = 74                                   # auto's observation count
_W = np.linspace(1760.0, 4840.0, _N)
_M = 40.0 - 0.0055 * _W + _RNG.normal(0.0, 1.8, _N)
_DF = pd.DataFrame({"mpg": _M, "weight": _W})


from conftest import render_models  # noqa: E402


def _spec(ptype, options=None):
    return {"graphs": [{"name": "g1", "graph_options": {"name": "g1"},
                        "options": {},
                        "plots": [{"type": ptype, "yvar": "mpg",
                                   "xvar": "weight",
                                   "options": options or {}}]}],
            "kpis": [],
            "build_options": {"layout": "auto", "registry": "g1",
                              "level": "95", "formats": {}, "theme": "",
                              "scheme": "", "session_scheme": ""}}


def _write(tmp_path, spec):
    tag = next(_SEQ)
    sp = tmp_path / f"s_{tag}.json"
    dp = tmp_path / f"d_{tag}.json"
    sp.write_text(json.dumps(spec))
    dp.write_text(json.dumps(make_data_json(_DF)))
    return tag, str(sp), str(dp)


def _server_sources(tmp_path, spec):
    """Every ColumnDataSource in the served document, by column-name set."""
    tag, sp, dp = _write(tmp_path, spec)
    ap = tmp_path / f"a_{tag}.py"
    dr.ServerAppBuilder(sp, dp).build(str(ap))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mod = load_app(str(ap), f"_stat_app_{tag}", draw=False)
        doc = Document()
        mod.make_document(doc)
    return [m.data for m in doc.select({"type": ColumnDataSource})]


def _standalone_sources(tmp_path, spec):
    _tag, sp, dp = _write(tmp_path, spec)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = dr.DashRenderer(sp, dp)
        render_models(r)
    out = []
    for fig in r.figures.values():
        for ren in fig.renderers:
            src = getattr(ren, "data_source", None)
            if src is not None:
                out.append(src.data)
    return out


def _pick(sources, *cols):
    for d in sources:
        if set(cols) <= set(d) and len(d[cols[0]]) > 0:
            return {c: np.asarray(d[c], dtype=float) for c in cols}
    return None


class TestKernelDensity:
    def test_the_server_uses_statas_bandwidth_and_kernel(self, tmp_path):
        spec = _spec("kdensity")
        srv = _pick(_server_sources(tmp_path, spec), "x", "y")
        std_all = _standalone_sources(tmp_path, spec)
        std = _pick(std_all, "x_kd", "y_kd") or _pick(std_all, "x", "y")
        assert srv is not None and std is not None
        sx, sy = srv["x"], srv["y"]
        tx = std.get("x_kd", std.get("x"))
        ty = std.get("y_kd", std.get("y"))
        on = np.interp(sx, tx, ty)
        peak = float(np.nanmax(ty))
        worst = float(np.nanmax(np.abs(on - sy)))
        assert worst <= 0.02 * peak, (
            f"served density differs from standalone by {worst:.5f} "
            f"({100 * worst / peak:.1f}% of the peak) — the server is not "
            f"using Stata's bandwidth rule"
        )

    def test_the_kernel_option_reaches_the_server(self, tmp_path):
        a = _server_sources(tmp_path, _spec("kdensity", {"kernel": "gaussian"}))
        b = _server_sources(tmp_path, _spec("kdensity", {"kernel": "rectangle"}))
        ya = _pick(a, "x", "y")
        yb = _pick(b, "x", "y")
        assert ya is not None and yb is not None
        assert not np.allclose(ya["y"], yb["y"]), (
            "kernel() changes nothing in server mode"
        )


class TestMedianBands:
    def test_the_band_count_is_statas(self, tmp_path):
        srv = _server_sources(tmp_path, _spec("mband"))
        got = _pick(srv, "x_mb", "y_mb")
        assert got is not None, "no mband source in the served document"
        expected = dr._mband_default_bands(_N)
        assert len(got["x_mb"]) == expected, (
            f"server drew {len(got['x_mb'])} bands, Stata's rule gives "
            f"{expected}"
        )

    def test_the_x_is_the_bands_median_not_its_midpoint(self, tmp_path):
        spec = _spec("mband")
        srv = _pick(_server_sources(tmp_path, spec), "x_mb", "y_mb")
        std = _pick(_standalone_sources(tmp_path, spec), "x_mb", "y_mb")
        assert srv is not None and std is not None
        assert len(srv["x_mb"]) == len(std["x_mb"])
        assert np.allclose(srv["x_mb"], std["x_mb"], rtol=1e-9, atol=1e-9)
        assert np.allclose(srv["y_mb"], std["y_mb"], rtol=1e-9, atol=1e-9)


class TestLinearFit:
    def test_both_modes_evaluate_the_same_line(self, tmp_path):
        spec = _spec("lfit")
        srv = _pick(_server_sources(tmp_path, spec), "x", "y")
        std = _pick(_standalone_sources(tmp_path, spec), "x_fit", "y_fit") \
            or _pick(_standalone_sources(tmp_path, spec), "x", "y")
        assert srv is not None and std is not None
        tx = std.get("x_fit", std.get("x"))
        ty = std.get("y_fit", std.get("y"))
        on = np.interp(srv["x"], tx, ty)
        span = float(np.nanmax(ty) - np.nanmin(ty))
        assert float(np.nanmax(np.abs(on - srv["y"]))) <= 1e-6 * max(span, 1.0)


class TestTheConfidenceBandIsTheRightWidth:
    """`se` from scipy's linregress is the standard error of the SLOPE.

    The emitted `_compute_lfitci` used it where the residual standard error
    belongs, then multiplied by sqrt(n-2) to compensate. Measured on a
    74-point fixture: standalone's mean 95% band width is 1.39, the server's
    is 0.0015 — about 900 times too narrow, a hairline drawn on the fit and
    labelled a confidence interval.
    """

    @pytest.mark.parametrize("level", ["50", "95", "99"])
    def test_the_band_matches_standalone(self, tmp_path, level):
        spec = _spec("lfitci", {"level": level})
        srv = _pick(_server_sources(tmp_path, spec),
                    "x_fit", "y_lower", "y_upper")
        std = _pick(_standalone_sources(tmp_path, spec),
                    "x_fit", "y_lower", "y_upper")
        assert srv is not None and std is not None
        sw = float(np.nanmean(srv["y_upper"] - srv["y_lower"]))
        tw = float(np.nanmean(std["y_upper"] - std["y_lower"]))
        assert abs(sw - tw) <= 0.02 * tw, (
            f"level({level}): server band is {sw:.4f} wide, standalone "
            f"{tw:.4f}"
        )

    def test_the_quadratic_band_matches_standalone(self, tmp_path):
        spec = _spec("qfitci")
        srv = _pick(_server_sources(tmp_path, spec),
                    "x_fit", "y_lower", "y_upper")
        std = _pick(_standalone_sources(tmp_path, spec),
                    "x_fit", "y_lower", "y_upper")
        assert srv is not None and std is not None
        sw = float(np.nanmean(srv["y_upper"] - srv["y_lower"]))
        tw = float(np.nanmean(std["y_upper"] - std["y_lower"]))
        assert abs(sw - tw) <= 0.05 * tw, (
            f"server qfitci band is {sw:.4f} wide, standalone {tw:.4f}"
        )


class TestLowess:
    def test_the_default_fraction_is_statas_point_eight(self, tmp_path):
        """The served lowess is the saved one, point for point.

        Both modes draw through GlyphMapper._stata_lowess since WP-18 --
        Stata's smoother in numpy, no statsmodels and so no skip -- and
        bind the same x_lw/y_lw columns, so the served default must equal
        the saved default exactly; the saved default's bwidth(0.8) against
        Stata's own points is TestLowessIsStatasSmoother.  This used to
        allow 2% of the range between two different smoothers.
        """
        spec = _spec("lowess")
        srv = _pick(_server_sources(tmp_path, spec), "x_lw", "y_lw")
        std = _pick(_standalone_sources(tmp_path, spec), "x_lw", "y_lw")
        assert srv is not None and std is not None
        np.testing.assert_allclose(np.asarray(srv["x_lw"], float),
                                   np.asarray(std["x_lw"], float), rtol=1e-12)
        np.testing.assert_allclose(np.asarray(srv["y_lw"], float),
                                   np.asarray(std["y_lw"], float), rtol=1e-12)


class TestConfidenceLevel:
    def test_level_reaches_the_server_ci(self, tmp_path):
        wide = _server_sources(tmp_path, _spec("lfitci", {"level": "99"}))
        narrow = _server_sources(tmp_path, _spec("lfitci", {"level": "50"}))
        w = _pick(wide, "x_fit", "y_lower", "y_upper")
        n = _pick(narrow, "x_fit", "y_lower", "y_upper")
        assert w is not None and n is not None, "no CI source in the document"
        w_width = float(np.nanmean(w["y_upper"] - w["y_lower"]))
        n_width = float(np.nanmean(n["y_upper"] - n["y_lower"]))
        assert w_width > n_width * 1.5, (
            f"level() does not reach the server CI: 99% band is "
            f"{w_width:.3f} wide, 50% band is {n_width:.3f}"
        )


def _hist(tmp_path, options):
    """The served histogram's (tops, lefts) for one option set."""
    srv = _server_sources(tmp_path, _spec("histogram", options))
    got = _pick(srv, "top", "left", "right")
    assert got is not None, "no histogram source in the served document"
    return got


def _hist_standalone(tmp_path, options):
    std = _standalone_sources(tmp_path, _spec("histogram", options))
    got = _pick(std, "top", "left", "right")
    assert got is not None, "no histogram source in the standalone document"
    return got


class TestTheServedHistogramIsTheSameHistogram:
    """It returned raw counts, i.e. Stata's `frequency', permanently.

    Standalone defaults to density, so the bars meant different quantities in
    the two modes with nothing saying the axis had changed.
    """

    def test_the_default_is_density_in_both_modes(self, tmp_path):
        srv = _hist(tmp_path, {})
        std = _hist_standalone(tmp_path, {})
        assert np.allclose(srv["top"], std["top"], rtol=1e-9, atol=1e-12)
        # ...and a density, not a count: the bar areas integrate to 1.
        widths = srv["right"] - srv["left"]
        assert abs(float(np.sum(srv["top"] * widths)) - 1.0) < 1e-9

    @pytest.mark.parametrize("ymode", ["frequency", "fraction", "percent",
                                       "density"])
    def test_each_y_axis_family_matches_standalone(self, tmp_path, ymode):
        srv = _hist(tmp_path, {ymode: ymode})
        std = _hist_standalone(tmp_path, {ymode: ymode})
        assert np.allclose(srv["top"], std["top"], rtol=1e-9, atol=1e-12), (
            f"{ymode}: served tops {srv['top'][:3]} vs standalone "
            f"{std['top'][:3]}"
        )

    def test_width_defines_the_grid(self, tmp_path):
        srv = _hist(tmp_path, {"width": "5"})
        std = _hist_standalone(tmp_path, {"width": "5"})
        assert len(srv["left"]) == len(std["left"])
        assert np.allclose(srv["left"], std["left"], rtol=1e-9, atol=1e-9)

    def test_start_and_width_together_define_the_grid(self, tmp_path):
        srv = _hist(tmp_path, {"start": "10", "width": "5"})
        std = _hist_standalone(tmp_path, {"start": "10", "width": "5"})
        assert np.allclose(srv["left"], std["left"], rtol=1e-9, atol=1e-9)
        assert abs(float(srv["left"][0]) - 10.0) < 1e-9

    @pytest.mark.parametrize("n", ["5", "6", "12"])
    def test_bin_still_wins_over_the_data_rule(self, tmp_path, n):
        srv = _hist(tmp_path, {"bin": n})
        assert len(srv["top"]) == int(n)


class TestLocalPolynomial:
    """The server carried its own `_lpoly_kernel_fit'.

    A hard-coded Gaussian weight, and `bwidth' treated as a FRACTION of the
    x-range clamped to [0.01, 1.0] — so `bwidth(500)' on weight became the
    whole range and `kernel()' was read by nothing. Measured: up to 7.5 mpg
    from the standalone curve for the same command.
    """

    @pytest.mark.parametrize("opts", [
        {},
        {"bwidth": "500"},
        {"kernel": "gaussian", "bwidth": "500"},
        {"degree": "1", "bwidth": "800"},
        {"kernel": "rectangle", "bwidth": "600"},
    ])
    def test_the_curve_is_the_standalone_curve(self, tmp_path, opts):
        spec = _spec("lpoly", opts)
        srv = _pick(_server_sources(tmp_path, spec), "x_lp", "y_lp")
        std = _pick(_standalone_sources(tmp_path, spec), "x_lp", "y_lp")
        assert srv is not None and std is not None
        on = np.interp(srv["x_lp"], std["x_lp"], std["y_lp"])
        worst = float(np.nanmax(np.abs(on - srv["y_lp"])))
        assert worst <= 1e-9, (
            f"{opts}: served lpoly differs from standalone by {worst:.6f}"
        )

    def test_an_absolute_bandwidth_is_not_a_fraction(self, tmp_path):
        a = _pick(_server_sources(tmp_path, _spec("lpoly", {"bwidth": "200"})),
                  "x_lp", "y_lp")
        b = _pick(_server_sources(tmp_path, _spec("lpoly", {"bwidth": "1500"})),
                  "x_lp", "y_lp")
        assert a is not None and b is not None
        assert not np.allclose(a["y_lp"], b["y_lp"])

    def test_the_kernel_reaches_the_server(self, tmp_path):
        a = _pick(_server_sources(
            tmp_path, _spec("lpoly", {"bwidth": "600",
                                      "kernel": "epanechnikov"})),
            "x_lp", "y_lp")
        b = _pick(_server_sources(
            tmp_path, _spec("lpoly", {"bwidth": "600",
                                      "kernel": "rectangle"})),
            "x_lp", "y_lp")
        assert a is not None and b is not None
        assert not np.allclose(a["y_lp"], b["y_lp"])


class TestServedDefaultBandwidth:
    """WP-29 P0.7: a served filter move recomputes the default lpoly
    bandwidth by Stata's rule from the rows the move keeps, so the smooth
    after a move to Foreign is ``lpoly mpg weight if foreign==1``
    (test/fixtures/lpoly_rot_truth.json, curve bi_d2_f1).  Before the fix
    the recompute derived 26.88 where Stata's is 287.78, and drew 5 points
    where Stata draws 50."""

    def _moved(self, tmp_path, plot, df):
        import test_lpoly_rot as tl
        spec = tl._spec([plot], bo={"filter": "foreign, type(dropdown)"})
        doc, _w, _ap = tl._served_doc(tmp_path, spec, df)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            tl._move_to(doc, "Foreign")
        return tl._lp(tl._doc_sources(doc)), [str(w.message) for w in caught]

    def test_served_default_is_statas(self, tmp_path):
        import test_lpoly_rot as tl
        lines, _ = self._moved(
            tmp_path, tl._plot(kernel="biweight", degree=2), tl._auto_df())
        drawn = [(x, y) for x, y in lines if len(x)]
        assert len(drawn) == 1
        x, y = drawn[0]
        c = tl._CURVES["bi_d2_f1"]
        assert len(x) == 50 == tl._finite_count(c), len(x)
        tl._near(x, y, c["gx"], c["gy"], 1e-4)

    def test_a_served_recompute_reaches_the_floor_and_overflow_paths(
            self, tmp_path):
        import test_lpoly_rot as tl
        # Stata, 01oct2026, `lpoly mpg <x> if foreign==1, degree(2)':
        # weight*1e-7 and weight*1e25 give r(bwidth) = . (a zero line);
        # weight*1e22 there gives 4.1305e21 and draws nothing (ngrid 0),
        # which dash matches, so the overflow case uses 1e25.
        df = tl._auto_df(("mpg", "weight", "price", "foreign", "rep78",
                          "wkm7", "wkp25"))
        for xv in ("wkm7", "wkp25"):
            lines, _ = self._moved(
                tmp_path, tl._plot(x=xv, degree=2), df)
            drawn = [(x, y) for x, y in lines if len(x)]
            assert len(drawn) == 1, xv
            assert np.all(drawn[0][1] == 0.0), (xv, drawn[0][1])
