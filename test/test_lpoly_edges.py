"""lpoly's weight threshold, refusals and the five-row case (WP-31 C11).

twoway counts a kernel weight toward lpoly's two-observation rule only above
about 1e-14: ``lpoly mpg weight, kernel(gaussian) bwidth(1) n(50)`` draws 3
points where counting every positive gaussian weight drew 23.  twoway counts
the sample before it reads lpoly's options (one row is "insufficient
observations", r(2001), whatever pwidth() says), and refuses bwidth(),
degree(), n(), kernel() and pwidth(+800) in its own words.
Truth: test/fixtures/estimator_edges_truth.json
(scripts/extract_estimator_edges_truth.do).
"""
import json
import os
import re
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import dash_render as dr  # noqa: E402
from js_runner import requires_node  # noqa: E402
from test_js_fit_refit import _js_batch  # noqa: E402

_ROOT = os.path.join(os.path.dirname(__file__), "..")
_FIX = os.path.join(os.path.dirname(__file__), "fixtures",
                    "estimator_edges_truth.json")
with open(_FIX, encoding="utf-8") as _fh:
    _T = json.load(_fh)
_X = np.asarray(_T["auto"]["weight"], dtype=float)
_Y = np.asarray(_T["auto"]["mpg"], dtype=float)

#: (fixture key, kernel, bwidth)
_PROBES = [("lp.gauss_bw1", "gaussian", 1.0),
           ("lp.gauss_bw05", "gaussian", 0.5),
           ("lp.gauss_bw2", "gaussian", 2.0),
           ("lp.gauss_bw50", "gaussian", 50.0),
           ("lp.biweight_bw1", "biweight", 1.0)]


def _read(name):
    with open(os.path.join(_ROOT, name), encoding="utf-8") as fh:
        return fh.read()


def _finite(vals):
    return [v is not None and np.isfinite(v) for v in vals]


class TestTheFixture:
    def test_meta(self):
        assert sorted(_T["_meta"]) == ["born_date", "dash_commit",
                                      "extracted", "source",
                                      "stata_version"]
        assert _T["_meta"]["source"] == \
            "scripts/extract_estimator_edges_truth.do"
        assert sum(k.startswith("lp.") for k in _T) >= 13


class TestLpolyThreshold:

    @pytest.mark.parametrize("key,kernel,bw", _PROBES,
                             ids=[p[0] for p in _PROBES])
    def test_gaussian_grid_points(self, key, kernel, bw):
        rec = _T[key]
        xg = np.asarray(rec["xg"], dtype=float)
        _, yf = dr.GlyphMapper._compute_lpoly_fit(
            _X, _Y, bwidth=bw, degree=0, kernel=kernel, x_grid=xg)
        assert _finite(yf) == _finite(rec["yg"])
        want = np.asarray([np.nan if v is None else v for v in rec["yg"]])
        ok = np.isfinite(want)
        np.testing.assert_allclose(yf[ok], want[ok], rtol=1e-6)

    def test_lpolyci_pilot_agrees(self):
        # lpolyci's se runs through _lpoly_local_wls (the pilot and the
        # smooth's window): its finite set is twoway's se's.
        rec = _T["lp.gauss_bw1_ci"]
        xg = np.asarray(rec["xg"], dtype=float)
        rot = dr.GlyphMapper._default_lpoly_bwidth(_X, _Y, None, 0,
                                                   "gaussian")
        se = dr._lpoly_se(_X, _Y, xg, 1.0, 1.5 * rot, 0, "gaussian")
        _, yf = dr.GlyphMapper._compute_lpoly_fit(
            _X, _Y, bwidth=1.0, degree=0, kernel="gaussian", x_grid=xg)
        # map_lpolyci bands a point where the smooth and its se are finite
        banded = np.isfinite(yf) & np.isfinite(se)
        assert list(banded) == _finite(rec["sg"])
        want = np.asarray([np.nan if v is None else v for v in rec["sg"]])
        np.testing.assert_allclose(se[banded], want[banded], rtol=1e-6)

    def test_biweight_unchanged(self):
        # A biweight is exactly 0 outside its window: the rule cannot move
        # it, at any bandwidth.
        for bw in (1.0, 50.0, 400.0):
            xg = np.linspace(_X.min(), _X.max(), 50)
            pos = [int((dr._lpoly_kernel_weights(_X, x0, bw, "biweight")
                        > 0).sum()) >= 2 for x0 in xg]
            _, yf = dr.GlyphMapper._compute_lpoly_fit(
                _X, _Y, bwidth=bw, degree=0, kernel="biweight", x_grid=xg)
            assert _finite(yf) == pos

    @requires_node
    def test_js_twin_agrees(self):
        calls = []
        for key, kernel, bw in _PROBES:
            calls.append([_X.tolist(), _Y.tolist(), bw, 0, kernel, None,
                          _T[key]["xg"]])
        got = _js_batch("dash_lpoly_fit", calls)
        for (key, _k, _b), g in zip(_PROBES, got):
            assert _finite(g) == _finite(_T[key]["yg"]), key

    def test_substitution_is_own_statement(self):
        src = _read("dash_render.py")
        stmt = '_FILTER_JS = _FILTER_JS.replace("@@DASH_LPOLY_EPS@@"'
        assert src.count(stmt) == 1
        assembly = src.index("_FILTER_JS = (_FILTER_JS + _DASH_AXIS_FINISH_JS")
        assert src.index(stmt) < assembly
        loop = src[src.index('for _tok, _val in (("@@DASH_MAX_TICKS@@"'):
                   src.index("del _tok, _val")]
        assert "_LPOLY_WEIGHT_EPS" not in loop
        assert src.count("pos = kw > _LPOLY_WEIGHT_EPS") == 2
        assert "@@DASH_LPOLY_EPS@@" not in dr._FILTER_JS


class TestLpolyRefusals:

    def test_D6_order(self):
        # twoway counts first: one row with pwidth(0) or bwidth(abc) is
        # "insufficient observations", r(2001); dash.ado counts lpoly's
        # sample before its option parser.
        for k in ("lp.D6", "lp.D6_bw", "lp.D6_lpoly"):
            assert _T[k] == {"rc": 2001,
                             "text": ["insufficient observations"]}
        ado = _read("dash.ado")
        early = ado.index("WP-31 C11 (D6)")
        assert early < ado.index("_dash_parse_plot_opts , `macval(opts_raw)'",
                                 early - 20000)
        # two rows draw (lp.D6_n2)
        assert _T["lp.D6_n2"]["rc"] == 0

    @pytest.mark.parametrize("key", ["lp.D7.bwidth", "lp.D7.bwidth_neg",
                                     "lp.D7.degree_neg", "lp.D7.n",
                                     "lp.D7.n_abc", "lp.D7.kernel"])
    def test_D7_words(self, key):
        rec = _T[key]
        ado = _read("dash.ado")
        text = rec["text"][0]
        if key == "lp.D7.bwidth":
            # the variable's name is the user's; the words around it
            assert text == "variable abc not found" and rec["rc"] == 111
            assert '"variable ", st_strscalar(st_local("T")), " not found"' \
                in ado
        elif key in ("lp.D7.bwidth_neg", "lp.D7.n"):
            assert re.fullmatch(r"(bwidth|n)\(\) must be a positive number",
                                text)
            assert 'display as error "`opt\'() must be a positive number"' \
                in ado
        else:
            assert '"%s"' % text in ado
        assert rec["rc"] in (111, 198)

    def test_D8_plus(self):
        assert _T["lp.D8"] == {"rc": 3000, "text": ["expression invalid"]}
        mata = _read("dash_parse.mata")
        assert 'st_local("_lpo_rc", "3000")' in mata
        assert 'st_local("_lpo_msg", "expression invalid")' in mata
        # bwidth(+800) draws (lp.D8_bw): no sign rule there
        assert _T["lp.D8_bw"]["rc"] == 0


class TestLpolyDocumented:

    def test_help_names_the_maxima(self):
        hlp = _read("dash.sthlp")
        assert "does not count toward lpoly's two-observation rule" in hlp
        assert "A kernel weight of %g or" % dr._LPOLY_WEIGHT_EPS in hlp
        for k in ("lp.D1", "lp.D2_0", "lp.D2_1", "lp.D3"):
            assert k in _T
        m = re.search(r"differs by at most ([0-9.e+-]+)", hlp)
        assert m, "the help names the round-off maxima"
        assert float(m.group(1)) >= _round_off_max()


def _round_off_max():
    """The largest relative difference between dash's exact smooth and
    Stata's on D1 and D2, where Stata's round-off decides."""
    out = 0.0
    xs = _X
    for key, y, deg in (("lp.D1", 2 * xs + 1, 0), ("lp.D2_0", xs, 0),
                        ("lp.D2_1", xs, 1)):
        rec = _T[key]
        xg = np.asarray(rec["xg"], dtype=float)
        _, yf = dr.GlyphMapper._compute_lpoly_fit(
            xs, y, bwidth=rec["bwidth"], degree=deg, x_grid=xg)
        want = np.asarray([np.nan if v is None else v for v in rec["yg"]])
        ok = np.isfinite(want) & np.isfinite(yf)
        out = max(out, float(np.max(np.abs(yf[ok] - want[ok])
                                    / np.abs(want[ok]))))
    return out


class TestLpolyFiveRows:

    def test_matches_twoway(self):
        # The parity frame's five domestic rows: every one of twoway's five
        # grid points is missing -- the empty line dash draws (a guard).
        # Measured: twoway's rule of thumb there is 0.1827 and dash's
        # 0.2708; both are far below the rows' spacing, so neither draws.
        rec = _T["lp.five_rows"]
        x = np.array([2930.0, 2200.0, 3000.0, 4080.0, 3600.0])
        y = np.array([22.0, 25.0, 21.0, 14.0, 16.0])
        assert rec["bwidth"] < 1.0
        xg, yf = dr.GlyphMapper._compute_lpoly_fit(x, y)
        np.testing.assert_allclose(xg, rec["xg"], rtol=1e-6)
        assert _finite(yf) == _finite(rec["yg"]) == [False] * 5
