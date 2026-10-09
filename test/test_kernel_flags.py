"""A kernel written as an option of its own draws that kernel (BUGS.md, S2).

``lpoly mpg weight, gaussian`` -- a kernel named as a flag, twoway's old
syntax -- draws the serset of ``kernel(gaussian)`` in twoway, on lpoly,
lpolyci and kdensity, from each shortest spelling (bi, cos, ep, epan2, gau,
par, rec, tri) to the full name (measured 24sep2026;
test_twoway_option_parity.cscript TP-16 asks twoway again on every run).
dash named the flag in its note and drew the default epanechnikov.

dash.ado now writes the flag to the spec as ``kernel(<name>)``
(``_dash_kernel_flag``); TP-16 holds that spec to twoway.  These tests hold
the other half: given ``kernel(<name>)``, both render modes draw that
kernel -- the standalone density is the density of that kernel, computed
here from Stata's formulas (kdensity manual) on dash's grid, and the served
curve is the standalone curve, for every kernel on every one of the three
types -- and no two kernels draw the same curve, so a kernel read as the
default could not pass.
"""
import itertools
import json
import math
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
_RNG = np.random.default_rng(20260924)
_N = 74
_W = np.linspace(1760.0, 4840.0, _N)
_M = 40.0 - 0.0055 * _W + _RNG.normal(0.0, 1.8, _N)
_DF = pd.DataFrame({"mpg": _M, "weight": _W})

KERNELS = ("epanechnikov", "epan2", "biweight", "cosine", "gaussian",
           "parzen", "rectangle", "triangle")


# Stata's kernels, written out from the kdensity manual on their own, so a
# renderer that read the wrong kernel -- or none -- cannot agree with them.
from conftest import render_models  # noqa: E402


def _stata_kernel(name, z):
    a = np.abs(z)
    if name == "epanechnikov":
        return np.where(a < math.sqrt(5.0),
                        0.75 * (1.0 - z * z / 5.0) / math.sqrt(5.0), 0.0)
    if name == "epan2":
        return np.where(a < 1.0, 0.75 * (1.0 - z * z), 0.0)
    if name == "biweight":
        return np.where(a < 1.0, 15.0 / 16.0 * (1.0 - z * z) ** 2, 0.0)
    if name == "cosine":
        return np.where(a < 0.5, 1.0 + np.cos(2.0 * math.pi * z), 0.0)
    if name == "gaussian":
        return np.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)
    if name == "parzen":
        return np.where(a <= 0.5, 4.0 / 3.0 - 8.0 * z * z + 8.0 * a ** 3,
                        np.where(a <= 1.0, 8.0 / 3.0 * (1.0 - a) ** 3, 0.0))
    if name == "rectangle":
        return np.where(a < 1.0, 0.5, 0.0)
    if name == "triangle":
        return np.where(a < 1.0, 1.0 - a, 0.0)
    raise ValueError(name)


def _spec(ptype, options):
    return {"graphs": [{"name": "g1", "graph_options": {"name": "g1"},
                        "options": {},
                        "plots": [{"type": ptype, "yvar": "mpg",
                                   "xvar": "weight",
                                   "options": dict(options)}]}],
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


def _served(tmp_path, spec):
    tag, sp, dp = _write(tmp_path, spec)
    ap = tmp_path / f"a_{tag}.py"
    dr.ServerAppBuilder(sp, dp).build(str(ap))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mod = load_app(str(ap), f"_kflag_app_{tag}")
        doc = Document()
        mod.make_document(doc)
    return [m.data for m in doc.select({"type": ColumnDataSource})]


def _standalone(tmp_path, spec):
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


def _curve(tmp_path, ptype, kernel, served):
    opts = {"kernel": kernel}
    if ptype != "kdensity":
        opts["bwidth"] = "600"
    srcs = (_served if served else _standalone)(tmp_path, _spec(ptype, opts))
    if ptype == "kdensity":
        c = _pick(srcs, "x_kd", "y_kd") or _pick(srcs, "x", "y")
        assert c is not None, "no density curve drawn"
        x = c.get("x_kd", c.get("x"))
        y = c.get("y_kd", c.get("y"))
    else:
        c = _pick(srcs, "x_lp", "y_lp")
        assert c is not None, f"no {ptype} curve drawn"
        x, y = c["x_lp"], c["y_lp"]
    return x, y


class TestTheStandaloneDensityIsTheNamedKernel:
    @pytest.mark.parametrize("kernel", KERNELS)
    def test_kdensity_draws_statas_density_of_that_kernel(self, tmp_path,
                                                          kernel):
        x, y = _curve(tmp_path, "kdensity", kernel, served=False)
        m = _DF["mpg"].to_numpy(dtype=float)
        h = float(dr._stata_kde_bandwidth(m, None, ""))
        z = (x[:, None] - m[None, :]) / h
        want = _stata_kernel(kernel, z).sum(axis=1) / (len(m) * h)
        worst = float(np.max(np.abs(want - y)))
        assert worst <= 1e-9 * max(1.0, float(np.max(want))), (
            f"kernel({kernel}): the drawn density is {worst:.3g} from "
            f"Stata's {kernel} density"
        )


class TestBothModesDrawTheNamedKernel:
    @pytest.mark.parametrize("ptype", ["lpoly", "lpolyci", "kdensity"])
    @pytest.mark.parametrize("kernel", KERNELS)
    def test_the_served_curve_is_the_standalone_curve(self, tmp_path, ptype,
                                                      kernel):
        sx, sy = _curve(tmp_path, ptype, kernel, served=True)
        tx, ty = _curve(tmp_path, ptype, kernel, served=False)
        on = np.interp(sx, tx, ty)
        worst = float(np.nanmax(np.abs(on - sy)))
        scale = max(1.0, float(np.nanmax(np.abs(ty))))
        tol = 0.02 if ptype == "kdensity" else 1e-9
        assert worst <= tol * scale, (
            f"{ptype} kernel({kernel}): served differs from standalone by "
            f"{worst:.3g}"
        )

    @pytest.mark.parametrize("served", [False, True],
                             ids=["standalone", "served"])
    @pytest.mark.parametrize("ptype", ["lpoly", "lpolyci", "kdensity"])
    def test_no_two_kernels_draw_the_same_curve(self, tmp_path, ptype,
                                                served):
        curves = {k: _curve(tmp_path, ptype, k, served) for k in KERNELS}
        for a, b in itertools.combinations(KERNELS, 2):
            ya, yb = curves[a][1], curves[b][1]
            same = ya.shape == yb.shape and np.allclose(ya, yb, rtol=0,
                                                        atol=1e-12)
            assert not same, f"{ptype}: kernel({a}) and kernel({b}) draw one curve"


class TestAdversarialKernelValues:
    """CLAUDE.md rule 18: a kernel value dash.ado would never write -- a
    flag-like word, markup, a very long string -- reaches the renderer only
    as a name it does not know; it is warned about by value and the default
    drawn, never evaluated."""

    @pytest.mark.parametrize("bad", [
        "gau", "__import__('os').system('echo INJ')", "<script>x</script>",
        "gaussian" * 5000,
    ], ids=["abbrev", "python", "markup", "long"])
    def test_an_unknown_kernel_draws_the_default(self, tmp_path, bad):
        _x, y_bad = _curve(tmp_path, "kdensity", bad, served=False)
        _x, y_def = _curve(tmp_path, "kdensity", "epanechnikov", served=False)
        assert np.allclose(y_bad, y_def)
