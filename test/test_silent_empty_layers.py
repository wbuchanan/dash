"""test_silent_empty_layers.py -- three layers twoway draws in silence (WP-32).

BUGS.md "An all-missing scatter, a constant-x lowess and a constant
kdensity keep dash's "drew nothing" note, where twoway draws in silence".
Measured 19oct2026 in StataNow 19.5 (console, sysuse auto, each serset
read with ``serset use``), rc 0 and no message for every one:

* ``twoway scatter m1 m2`` on two all-missing variables: a serset of one
  missing row -- nothing drawn.  ``if foreign`` the same.
* ``twoway lowess mpg c`` with c = 2500 everywhere: the smooth is missing
  on all 74 rows -- nothing drawn; ``bwidth(.5)`` and ``if foreign`` the
  same.
* ``twoway kdensity c22`` with c22 = 22 everywhere: 300 points, every one
  at (22, 0); ``n(5)`` five of them, ``n(7) range(10 30)`` seven at
  y = 0 from 10 to 30, ``[fw=rep78]``, ``gaussian``, ``area(2)``,
  ``horizontal`` and ``by(foreign)`` the same zeros; ``bwidth(1)`` seven
  points at (22, .3354102), the epanechnikov kernel's peak 3/(4*sqrt(5)):
  the bandwidth rule's zero is what gives zeros, the grid runs from the
  minimum to the maximum as on any other data.

dash said "drew nothing" for all three, and drew no kdensity points.  Now
both renderers draw what twoway draws and say nothing, and the saved
page's re-estimate after a move draws the same zeros on a constant subset.
"""
from __future__ import annotations

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

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import make_data_json, load_app  # noqa: E402
import js_runner  # noqa: E402

_SEQ = itertools.count()
_N = 10


def _df():
    return pd.DataFrame({
        "mpg": [float(20 + i) for i in range(_N)],
        "yl": [float(19 + i) for i in range(_N)],
        "w": [float(2000 + 100 * i) for i in range(_N)],
        "c": [2500.0] * _N,
        "c22": [22.0] * _N,
        "m1": [float("nan")] * _N,
        "m2": [float("nan")] * _N,
        "f": [float(1 + i % 3) for i in range(_N)],
    })


def _spec(plot):
    return {"graphs": [{"name": "g1", "graph_options": {"name": "g1"},
                        "options": {}, "plots": [plot]}],
            "kpis": [],
            "build_options": {"layout": "auto", "link": "", "filter": "",
                              "theme": "", "scheme": "", "title": "",
                              "subtitle": "", "registry": "g1", "tabs": "",
                              "filter_position": "top", "level": "95",
                              "formats": {}}}


def _write(tmp_path, plot):
    tag = next(_SEQ)
    sp = tmp_path / f"spec_{tag}.json"
    dp = tmp_path / f"data_{tag}.json"
    sp.write_text(json.dumps(_spec(plot)))
    dp.write_text(json.dumps(make_data_json(_df())))
    return tag, str(sp), str(dp)


def _saved(tmp_path, plot):
    """(renderers of g1, dash warnings) from the saved-page renderer."""
    _, sp, dp = _write(tmp_path, plot)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r = dr.DashRenderer(sp, dp)
        r.render()
    return (list(r.figures["g1"].renderers),
            [str(w.message) for w in caught
             if str(w.message).startswith("dash")])


def _served(tmp_path, plot):
    """(renderers of the served figure, dash warnings)."""
    tag, sp, dp = _write(tmp_path, plot)
    ap = tmp_path / f"app_{tag}.py"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(str(ap))
        mod = load_app(str(ap), f"_wp32_silent_{tag}", draw=False)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        doc = Document()
        mod.make_document(doc)
    figs = [m for m in doc.select({"type": object})
            if type(m).__name__ == "figure"]
    assert len(figs) == 1
    return (list(figs[0].renderers),
            [str(w.message) for w in caught
             if str(w.message).startswith("dash")])


_MODES = pytest.mark.parametrize("mode", ["saved", "served"])


def _run(mode, tmp_path, plot):
    return (_saved if mode == "saved" else _served)(tmp_path, plot)


def _points(renderers):
    """(x, y) of every data glyph's rows."""
    out = []
    for r in renderers:
        d = getattr(getattr(r, "data_source", None), "data", None)
        if not d:
            continue
        xk = "x" if "x" in d else None
        yk = "y" if "y" in d else None
        if xk and yk:
            out.append((list(map(float, d[xk])), list(map(float, d[yk]))))
    return out


class TestAnAllMissingScatter:
    @_MODES
    def test_draws_nothing_in_silence(self, mode, tmp_path):
        rs, notes = _run(mode, tmp_path, {"type": "scatter", "yvar": "m1",
                                          "xvar": "m2", "options": {}})
        assert notes == []
        assert not dr._dash_layer_drew_anything(rs)


class TestAConstantXLowess:
    @_MODES
    @pytest.mark.parametrize("opts", [{}, {"bwidth": ".5"}])
    def test_draws_nothing_in_silence(self, mode, opts, tmp_path):
        rs, notes = _run(mode, tmp_path, {"type": "lowess", "yvar": "mpg",
                                          "xvar": "c", "options": opts})
        assert notes == []
        assert not dr._dash_layer_drew_anything(rs)


class TestAConstantKdensity:
    @_MODES
    @pytest.mark.parametrize("opts,n,x0,x1", [
        ({}, 300, 22.0, 22.0),
        ({"n": "5"}, 5, 22.0, 22.0),
        ({"n": "7", "range": "10 30"}, 7, 10.0, 30.0),
        ({"n": "7", "kernel": "gaussian"}, 7, 22.0, 22.0),
        ({"n": "7", "area": "2"}, 7, 22.0, 22.0),
        ({"n": "7", "weight": "fweight", "wexp": "f"}, 7, 22.0, 22.0),
    ])
    def test_draws_twoways_zeros(self, mode, opts, n, x0, x1, tmp_path):
        rs, notes = _run(mode, tmp_path, {"type": "kdensity", "var": "c22",
                                          "options": opts})
        assert notes == []
        pts = _points(rs)
        assert len(pts) == 1, pts
        xs, ys = pts[0]
        assert len(xs) == n
        assert xs[0] == pytest.approx(x0) and xs[-1] == pytest.approx(x1)
        assert ys == [0.0] * n

    @_MODES
    def test_a_given_bandwidth_draws_the_kernel_peak(self, mode, tmp_path):
        rs, notes = _run(mode, tmp_path, {"type": "kdensity", "var": "c22",
                                          "options": {"n": "7",
                                                      "bwidth": "1"}})
        assert notes == []
        xs, ys = _points(rs)[0]
        assert xs == [22.0] * 7
        assert ys == pytest.approx([.3354102] * 7, abs=1e-7)


@js_runner.requires_node
class TestAfterAMove:
    """The saved page's re-estimate on a constant subset: twoway's zeros on
    the kept rows' grid, where it cleared the curve."""

    def _ac(self, **kw):
        ac = {"type": "kdensity", "varname": "c22", "x_grid": [1.0, 2.0],
              "kernel": "epanechnikov", "bw_rule": dr._KDE_BANDWIDTH_RULE,
              "bw_fixed": None, "wvar": None, "wtype": None, "area": 1.0,
              "boundary": False, "regrid": True, "n": 5}
        ac.update(kw)
        return ac

    def test_a_constant_subset_draws_zeros(self):
        out = js_runner.run_filter_js_block("kdensity", self._ac(),
                                            [22.0] * 6)
        assert out["x"] == [22.0] * 5
        assert out["y"] == [0.0] * 5

    def test_a_weighted_constant_subset_draws_zeros(self):
        out = js_runner.run_filter_js_block(
            "kdensity", self._ac(wvar="f", wtype="fw"), [22.0] * 6,
            wts=[1.0, 2.0, 3.0, 1.0, 2.0, 3.0])
        assert out["y"] == [0.0] * 5

    def test_a_given_bandwidth_draws_the_peak(self):
        out = js_runner.run_filter_js_block(
            "kdensity", self._ac(bw_fixed=1.0), [22.0] * 6)
        assert all(math.isclose(v, .3354102, abs_tol=1e-7)
                   for v in out["y"])

    def test_the_saved_page_carries_a_constant_curve_s_config(self, tmp_path):
        rs, _notes = _saved(tmp_path, {"type": "kdensity", "var": "c22",
                                       "options": {}})
        cfg = next(getattr(r, "_dash_agg_config", None) for r in rs
                   if getattr(r, "_dash_agg_config", None))
        assert cfg["type"] == "kdensity"
        assert np.allclose(cfg["x_grid"], 22.0)


#: BUGS.md "An all-missing line, area, bar or other plain layer says "drew
#: nothing", where twoway draws it in silence": measured 19oct2026, every
#: plain type below on an all-missing y (line, area, bar, spike, dropline
#: and tsline on m; the range types on m yl; the paired-coordinate types on
#: m w yl c) is rc 0 with no message and a serset whose y is missing on
#: every row; `twoway line mpg m' and `spike mpg m', a missing x, the same.
_PLAIN = [
    {"type": "line", "yvar": "m1", "xvar": "w"},
    {"type": "line", "yvar": "mpg", "xvar": "m1"},
    {"type": "area", "yvar": "m1", "xvar": "w"},
    {"type": "bar", "yvar": "m1", "xvar": "w"},
    {"type": "spike", "yvar": "m1", "xvar": "w"},
    {"type": "spike", "yvar": "mpg", "xvar": "m1"},
    {"type": "dropline", "yvar": "m1", "xvar": "w"},
    {"type": "tsline", "yvar": "m1", "xvar": "w"},
    {"type": "rarea", "yvar1": "m1", "yvar2": "yl", "xvar": "w"},
    {"type": "pcspike", "y1var": "m1", "x1var": "w", "y2var": "yl",
     "x2var": "c"},
    {"type": "pcarrow", "y1var": "m1", "x1var": "w", "y2var": "yl",
     "x2var": "c"},
    {"type": "pcscatter", "y1var": "m1", "x1var": "w", "y2var": "yl",
     "x2var": "c"},
]


class TestAnAllMissingPlainLayer:
    @_MODES
    @pytest.mark.parametrize("plot", _PLAIN,
                             ids=lambda p: p["type"] + "-" + "-".join(
                                 v for k, v in p.items() if k != "type"))
    def test_draws_nothing_in_silence(self, mode, plot, tmp_path):
        p = dict(plot, options={})
        rs, notes = _run(mode, tmp_path, p)
        assert notes == [], notes
        assert not dr._dash_layer_drew_anything(rs)

    def test_a_layer_with_a_complete_row_is_not_silenced(self):
        assert not dr._dash_layer_all_missing(
            {"type": "line", "yvar": "y", "xvar": "x"},
            {"y": [None, 2.0], "x": [1.0, 3.0]})
        assert dr._dash_layer_all_missing(
            {"type": "line", "yvar": "y", "xvar": "x"},
            {"y": [None, 2.0], "x": [1.0, float("nan")]})
        # A computed type is never decided here.
        assert not dr._dash_layer_all_missing(
            {"type": "lfit", "yvar": "y", "xvar": "x"},
            {"y": [None], "x": [None]})
