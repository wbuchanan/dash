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
import importlib.util
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
from conftest import make_data_json

_SEQ = itertools.count()

_RNG = np.random.default_rng(19780101)
_N = 74                                   # auto's observation count
_W = np.linspace(1760.0, 4840.0, _N)
_M = 40.0 - 0.0055 * _W + _RNG.normal(0.0, 1.8, _N)
_DF = pd.DataFrame({"mpg": _M, "weight": _W})


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
    ms = importlib.util.spec_from_file_location(f"_stat_app_{tag}", str(ap))
    mod = importlib.util.module_from_spec(ms)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ms.loader.exec_module(mod)
        doc = Document()
        mod.make_document(doc)
    return [m.data for m in doc.select({"type": ColumnDataSource})]


def _standalone_sources(tmp_path, spec):
    _tag, sp, dp = _write(tmp_path, spec)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = dr.DashRenderer(sp, dp)
        r.render()
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
