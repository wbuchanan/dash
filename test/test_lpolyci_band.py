"""lpolyci draws lpoly's analytic band, with pwidth() and var() (WP-29 P0.9).

dash drew a 200-resample bootstrap percentile band: 0.85-1.55 times
Stata's width at given bandwidths, edges up to 44.7 mpg off at degree(1),
4.2 s at N=20000; pwidth() and var() were ignored and level(5) drawn.
Stata's band ([R] lpoly eq. 4) is the smooth +/- invnormal x the sandwich
standard error with a degree p+2 pilot at pwidth() (default 1.5 times the
rule of thumb, even with bwidth()) or var().

Every number is from test/fixtures/lpolyci_truth.json
(scripts/extract_lpolyci_truth.do).  At given bandwidths the band is held
at 1e-8 x max(1, |y|); at the default bandwidths as exact as the rule of
thumb (noisy cases: 1e-4 of the band half-width).  Rows whose pilot fit has
no residual degrees of freedom (the fixture's ``no_df``, computed with
numpy from the data, not by dash) are pinched: se 0, where twoway draws
its own round-off -- no band, or a finite band that can be very wide
(documented divergence D4; dash.sthlp, stat:PT-16).
"""
import json
import os
import sys
import time
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.models import ColumnDataSource, Legend

# WP-50 50-03: the batch tier, run at batch ends (make test-all), ruled 13nov2026 at 50-01-04.
pytestmark = pytest.mark.batch

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import exec_app  # noqa: E402
import test_lpoly_rot as tl  # noqa: E402

_FIX = os.path.join(_HERE, "fixtures", "lpolyci_truth.json")


from conftest import render_models  # noqa: E402


def _load():
    if not os.path.exists(_FIX):
        pytest.fail("test/fixtures/lpolyci_truth.json is missing: run "
                    "scripts/extract_lpolyci_truth.do")
    with open(_FIX) as fh:
        return json.load(fh)


_T = _load() if os.path.exists(_FIX) else {"cases": [], "datasets": {},
                                           "no_df": {}, "serset": []}
_C = {c["id"]: c for c in _T["cases"]}
_NODF = _T.get("no_df", {})


def _case(cid):
    if cid not in _C:
        pytest.fail(f"lpolyci_truth.json has no case {cid}")
    return _C[cid]


def _arr(v):
    return np.array([np.nan if e is None else e for e in v], dtype=float)


def _sample(c):
    D = _T["datasets"][c["ds"]]
    x = np.array([D[c["x"]][i] for i in c["idx"]], dtype=float)
    y = np.array([D[c["y"]][i] for i in c["idx"]], dtype=float)
    w = None
    if c["w"]:
        w = np.array([D[c["w"]][i] for i in c["idx"]], dtype=float)
        if c["wtype"] == "aw":
            w = w * len(w) / w.sum()
    return x, y, w


def _df(ds):
    return pd.DataFrame(_T["datasets"][ds])


def _opts_of(c):
    """The spec options of a case: its own lpoly options."""
    o = {"degree": str(c["degree"]), "kernel": c["kernel"]}
    for k in ("bwidth", "pwidth", "level", "n"):
        tag = k + "("
        if tag in c["options"]:
            v = c["options"].split(tag, 1)[1].split(")", 1)[0]
            o[k] = v
    if "var(" in c["options"]:
        o["lpvar"] = c["options"].split("var(", 1)[1].split(")", 1)[0]
    if c["w"]:
        o["weight"] = {"aw": "aweight", "fw": "fweight"}[c["wtype"]]
        o["wexp"] = c["w"]
    return o


def _spec_of(c, extra=None):
    o = _opts_of(c)
    o.update(extra or {})
    s = tl._spec([{"type": "lpolyci", "yvar": c["y"], "xvar": c["x"],
                   "options": o}])
    cond = c["cond"]
    if cond.startswith("_n<="):
        s["graphs"][0]["in_expr"] = "1/" + cond[4:]
    elif cond != "1":
        s["graphs"][0]["if_expr"] = cond
    return s


def _layer(srcs):
    """(band, line) sources of a drawn lpolyci: the band source carries
    y_lower, the line source x_lp/y_lp alone (or both in one source)."""
    band = [s for s in srcs if "y_lower" in s]
    line = [s for s in srcs if "x_lp" in s and "y_lower" not in s]
    return band, line


def _band_of(srcs):
    band, _ = _layer(srcs)
    assert len(band) == 1, len(band)
    b = band[0]
    return (np.asarray(b["x_lp"], float), np.asarray(b["y_lower"], float),
            np.asarray(b["y_upper"], float))


def _drawn(tmp_path, c, mode, extra=None):
    return tl._sources(tmp_path, _spec_of(c, extra), _df(c["ds"]), mode)


def _check_band(c, bx, lo, hi, tol_of, h_noisy=False):
    """The drawn band against gy -/+ z*gse."""
    gx, gy, gse = _arr(c["gx"]), _arr(c["gy"]), _arr(c["gse"])
    z = c["z"]
    nodf = set(_NODF.get(c["id"], []))
    assert np.isfinite(bx).all() and np.isfinite(lo).all() and np.isfinite(hi).all()
    seen = set()
    for a, l, u in zip(bx, lo, hi):
        j = int(np.nanargmin(np.abs(gx - a)))
        assert abs(gx[j] - a) <= 1e-9 * max(1.0, abs(a)), (a, gx[j])
        seen.add(j)
        if j in nodf:
            # D4: pinched, or Stata's round-off
            continue
        assert np.isfinite(gse[j]), ("drawn where Stata has no band", c["id"], j)
        tol = tol_of(j)
        assert abs(l - (gy[j] - z * gse[j])) <= tol, (c["id"], j, l, gy[j] - z * gse[j])
        assert abs(u - (gy[j] + z * gse[j])) <= tol, (c["id"], j, u, gy[j] + z * gse[j])
    for j in range(len(gx)):
        if np.isfinite(gse[j]) and j not in nodf:
            assert j in seen, ("Stata draws a band here", c["id"], j)


_GIVEN = ["a_d0_bw500_pw800", "a_d1_bw500_pw800", "a_d1_bw500_var10",
          "a_d0_rec_bw400_pw600", "a_d0_tri_bw400_pw600",
          "a_d0_par_bw400_pw600", "a_d0_cos_bw400_pw600",
          "a_d0_ep2_bw400_pw600", "a_d0_bw100_pw150", "a_d0_bw60_pw60",
          "a_d1_aw_bw500_pw800", "a_d1_fw_bw500_pw800", "n_d1_bw2_pw3",
          "rep_d2_bw06", "a_d0_lvl10", "a_d0_lvl90", "a_d0_lvl9999",
          "a_d0_bw500_pw800_n20"]
_DEFAULT = ["a_d0", "a_d1", "a_d2", "a_d3", "a_d0_gau", "a_d1_bi", "a_d0_aw",
            "a_d0_fw", "a_price_rep78_d0", "a_d0_foreign", "n_d0", "n_d1",
            "n_d2", "n_d0_aw", "r1000_d0"]
_MODES = ["saved", "served"]


class TestTheBandIsStatas:
    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("cid", _GIVEN)
    def test_at_given_bandwidths(self, tmp_path, cid, mode):
        c = _case(cid)
        srcs, _ = _drawn(tmp_path, c, mode)
        bx, lo, hi = _band_of(srcs)
        gy = _arr(c["gy"])
        _check_band(c, bx, lo, hi,
                    lambda j: 1e-8 * max(1.0, abs(gy[j])))

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("cid", _DEFAULT)
    def test_at_default_bandwidths(self, tmp_path, cid, mode):
        c = _case(cid)
        srcs, _ = _drawn(tmp_path, c, mode)
        bx, lo, hi = _band_of(srcs)
        gy, gse = _arr(c["gy"]), _arr(c["gse"])
        noisy = c["degree"] >= 2
        x, y, w = _sample(c)
        rot = dr.GlyphMapper._default_lpoly_bwidth(x, y, w, c["degree"],
                                                   c["kernel"])
        # the rule of thumb itself, at its tier
        assert abs(rot / c["bwidth"] - 1) <= (5e-5 if noisy else 1e-7)
        assert abs(1.5 * rot / c["pwidth"] - 1) <= (5e-5 if noisy else 1e-7)

        def tol(j):
            t = 1e-8 * max(1.0, abs(gy[j]))
            if noisy:
                t += 1e-4 * c["z"] * gse[j]
            return t
        _check_band(c, bx, lo, hi, tol)

    def test_pwidth_default_is_one_and_a_half_rot(self):
        c = _case("a_d0_bw500")
        assert c["bwidth"] == 500.0
        assert abs(c["pwidth"] / 105.964382033088 - 1) < 1e-12
        x, y, w = _sample(c)
        rot = dr.GlyphMapper._default_lpoly_bwidth(x, y, w, 0)
        assert abs(1.5 * rot / c["pwidth"] - 1) <= 1e-7

    @pytest.mark.parametrize("sid", ["a_d1_bw500_pw800", "a_d0", "a_d0_foreign",
                                     "a_d1_bi", "n_d1_bw2_pw3", "a_d0_lvl90"])
    def test_matches_twoways_drawn_serset(self, tmp_path, sid):
        s = [e for e in _T["serset"] if e["id"] == sid][0]
        c = _case(sid)
        gx = _arr(c["gx"])
        cols = {k: _arr(v) for k, v in s["values"].items()}
        # identify the columns: x is the grid, y the smooth (in floats)
        xk = min(cols, key=lambda k: np.nanmax(np.abs(cols[k][:len(gx)] - gx)))
        rest = [k for k in cols if k != xk]
        yk = min(rest, key=lambda k: np.nanmax(np.abs(cols[k][:len(gx)] - _arr(c["gy"]))))
        lu = [k for k in rest if k != yk]
        lk, uk = sorted(lu, key=lambda k: np.nanmax(cols[k]))
        srcs, _ = _drawn(tmp_path, c, "saved")
        bx, lo, hi = _band_of(srcs)
        nodf = set(_NODF.get(sid, []))
        pinched = []
        n = 0
        for i in range(len(cols[xk])):
            xv, lv, uv = cols[xk][i], cols[lk][i], cols[uk][i]
            if not np.isfinite(xv):
                continue
            hit = np.where(np.abs(bx - xv) <= 1e-6 * abs(xv))[0]
            j = int(np.nanargmin(np.abs(gx - xv)))
            if not np.isfinite(lv):
                # no band in twoway: none in dash, or a pinch on a D4 row
                assert not len(hit) or (j in nodf and lo[hit[0]] == hi[hit[0]]), (sid, xv)
                continue
            assert len(hit) == 1, (sid, xv)
            k = hit[0]
            if j in nodf:
                # D4: dash pinches where the pilot has no residual df;
                # twoway's band there is Stata's round-off.
                assert lo[k] == hi[k], (sid, xv)
                pinched.append((float(xv), float(uv - lv)))
                continue
            np.testing.assert_allclose([lo[k], hi[k]], [lv, uv], rtol=1e-6,
                                       atol=1e-6, err_msg=f"{sid} x={xv}")
            n += 1
        assert n > 0

    def test_qualified_stat_truth_foreign_band_pinches_where_twoway_does(self, tmp_path):
        with open(os.path.join(_HERE, "fixtures", "qualified_stat_truth.json")) as fh:
            q = json.load(fh)["layers"]["lpolyci"]
        for key, cid in (("all", "a_d0"), ("foreign1", "a_d0_foreign")):
            e = q[key]
            c = _case(cid)
            nodf = set(_NODF.get(cid, []))
            srcs, _ = _drawn(tmp_path, c, "saved")
            bx, lo, hi = _band_of(srcs)
            for g, (xv, lv, uv) in enumerate(zip(e["grid_x"], e["lower"], e["upper"])):
                if lv is None:
                    continue
                k = np.where(np.abs(bx - xv) <= 1e-6 * xv)[0]
                assert len(k) == 1, (key, xv)
                if g in nodf and lo[k[0]] == hi[k[0]]:
                    continue    # D4: dash pinches, twoway's band is round-off
                np.testing.assert_allclose([lo[k[0]], hi[k[0]]], [lv, uv],
                                           rtol=1e-6, atol=1e-5,
                                           err_msg=f"{key} x={xv}")
        # 1760 on the foreign cars: lower = upper = 27.6727848
        k = np.where(np.abs(bx - 1760.0) < 1e-9)[0][0]
        assert abs(lo[k] - 27.6727848) < 1e-6 and lo[k] == hi[k]


class TestTheVarianceRule:
    def test_degree0_closed_form(self):
        c = _case("a_d0_bw500_pw800")
        x, y, w = _sample(c)
        gx = _arr(c["gx"])
        se = dr._lpoly_se(x, y, gx, 500.0, 800.0, 0, "epanechnikov", None, 1.0)
        for i, x0 in enumerate(gx):
            k = dr._lpoly_kernel_weights(x, x0, 500.0, "epanechnikov")
            if (k > 0).sum() < 2:
                continue
            assert se[i] ** 2 == pytest.approx(np.sum(k * k) / np.sum(k) ** 2,
                                               rel=1e-12)

    def test_var_replaces_sigma2(self):
        c = _case("a_d1_bw500_var10")
        x, y, _ = _sample(c)
        gx = _arr(c["gx"])
        a = dr._lpoly_se(x, y, gx, 500.0, 105.964382033088, 1, "epanechnikov", None, 10.0)
        b = dr._lpoly_se(x, y, gx, 500.0, 105.964382033088, 1, "epanechnikov", None, 40.0)
        ok = np.isfinite(a)
        np.testing.assert_allclose(b[ok], 2 * a[ok], rtol=1e-12)
        np.testing.assert_allclose(a[ok], _arr(c["gse"])[ok], rtol=1e-8)

    def test_a_pilot_window_of_one_is_missing_even_with_var(self):
        c = _case("a_d1_bw500_var10")
        x, y, _ = _sample(c)
        gx = _arr(c["gx"])
        j = int(np.argmin(np.abs(gx - 4588.57)))
        assert c["gse"][j] is None and abs(gx[j] - 4588.57) < 0.01
        se = dr._lpoly_se(x, y, gx, 500.0, c["pwidth"], 1, "epanechnikov",
                          None, 10.0)
        assert np.isnan(se[j])

    def test_no_residual_df_pinches(self):
        c = _case("a_d2")
        assert _NODF["a_d2"] == [44, 45, 46, 47, 48, 49]
        x, y, _ = _sample(c)
        se = dr._lpoly_se(x, y, _arr(c["gx"]), c["bwidth"], c["pwidth"], 2,
                          "epanechnikov")
        assert all(se[i] == 0.0 for i in range(44, 50)), se[44:]

    def test_fweight_equals_replication(self):
        c = _case("a_d1_fw_bw500_pw800")
        x, y, w = _sample(c)
        gx = _arr(c["gx"])
        a = dr._lpoly_se(x, y, gx, 500.0, 800.0, 1, "epanechnikov", w)
        k = w.astype(int)
        b = dr._lpoly_se(np.repeat(x, k), np.repeat(y, k), gx, 500.0, 800.0,
                         1, "epanechnikov")
        np.testing.assert_allclose(a, b, rtol=1e-9, equal_nan=True)

    def test_aweight_rescaling_invariant(self):
        c = _case("a_d1_aw_bw500_pw800")
        x, y, w = _sample(c)
        gx = _arr(c["gx"])
        raw = np.array([_T["datasets"]["auto"]["price"][i] for i in c["idx"]])
        a = dr._lpoly_se(x, y, gx, 500.0, 800.0, 1, "epanechnikov",
                         dr._dash_lpoly_weights(raw, "aw"))
        b = dr._lpoly_se(x, y, gx, 500.0, 800.0, 1, "epanechnikov",
                         dr._dash_lpoly_weights(raw * 7.0, "aw"))
        np.testing.assert_allclose(a, b, rtol=1e-12, equal_nan=True)
        np.testing.assert_allclose(a, _arr(c["gse"]), rtol=1e-8, equal_nan=True)

    def test_x_scale_invariant(self):
        c = _case("a_d1_bw500_pw800")
        x, y, _ = _sample(c)
        gx = _arr(c["gx"])
        a = dr._lpoly_se(x, y, gx, 500.0, 800.0, 1, "epanechnikov")
        b = dr._lpoly_se(x * 1000, y, gx * 1000, 5e5, 8e5, 1, "epanechnikov")
        np.testing.assert_allclose(a, b, rtol=1e-9, equal_nan=True)

    def test_rank_deficient_windows_share_the_local_fits_kept_columns(self):
        c = _case("r1000_d2_bw600")
        x, y, _ = _sample(c)
        gx = _arr(c["gx"])
        _, yf = dr.GlyphMapper._compute_lpoly_fit(x, y, bwidth=600.0,
                                                  degree=2, x_grid=gx)
        gy = _arr(c["gy"])
        ok = np.isfinite(gy)
        np.testing.assert_allclose(yf[ok], gy[ok], rtol=2e-9)
        se = dr._lpoly_se(x, y, gx, 600.0, c["pwidth"], 2, "epanechnikov")
        gse = _arr(c["gse"])
        ok = np.isfinite(gse)
        np.testing.assert_allclose(se[ok], gse[ok], rtol=1e-8)
        # a_d3 at x = 4400, Stata's own bandwidth: 7.0604 (dash was -6.6719)
        a = _case("a_d3")
        ax, ay, _ = _sample(a)
        _, v = dr.GlyphMapper._compute_lpoly_fit(
            ax, ay, bwidth=120.792907978892, degree=3, x_grid=np.array([4400.0]))
        assert abs(v[0] - 7.0604) < 5e-5, v

    def test_zero_aweights_are_dropped_before_normalising(self, tmp_path):
        a = _case("a_d0_awz")
        b = _case("a_d0_awmiss")
        assert a["N"] == b["N"] == 59
        np.testing.assert_allclose(_arr(a["gse"]), _arr(b["gse"]), rtol=3e-8,
                                   equal_nan=True)
        sa, _ = _drawn(tmp_path, a, "saved")
        sb, _ = _drawn(tmp_path, b, "saved")
        xa, la, ua = _band_of(sa)
        xb, lb, ub = _band_of(sb)
        np.testing.assert_allclose(xa, xb, rtol=1e-12)
        np.testing.assert_allclose(la, lb, rtol=3e-8)
        np.testing.assert_allclose(ua, ub, rtol=3e-8)

    def test_constant_x_has_no_band(self, tmp_path):
        c = _case("cx_n5")
        assert c["bwidth"] is None and all(v == 0 for v in c["gy"])
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            srcs, notes = tl._sources_saved(tmp_path, _spec_of(c), _df("auto"))
        band, line = _layer(srcs)
        assert all(len(b["y_lower"]) == 0 for b in band)
        drawn = [s for s in line if len(s["x_lp"])]
        assert len(drawn) == 1 and np.all(np.asarray(drawn[0]["y_lp"]) == 0)
        assert len(drawn[0]["x_lp"]) == 5


class TestDashInvnormal:
    def test_matches_stata(self):
        for cid in ("a_d0_lvl10", "a_d0_lvl90", "a_d0", "a_d0_lvl9999"):
            c = _case(cid)
            p = 0.5 * (1 - c["level"] / 100) + c["level"] / 100
            assert dr._dash_invnormal(p) == pytest.approx(c["z"], rel=1e-15)
        assert dr._dash_invnormal(.975) == pytest.approx(1.959963984540054,
                                                         rel=1e-15)


class TestNoBootstrap:
    def test_never_resamples(self, tmp_path, monkeypatch):
        calls = []
        real = dr.GlyphMapper._bootstrap_ci

        def spy(*a, **k):
            calls.append(1)
            return real(*a, **k)
        monkeypatch.setattr(dr.GlyphMapper, "_bootstrap_ci", staticmethod(spy))
        _drawn(tmp_path, _case("a_d1_bw500_pw800"), "saved")
        assert calls == []

    def test_jitterseed_changes_nothing(self, tmp_path):
        c = _case("a_d1_bw500_pw800")
        a, _ = _drawn(tmp_path, c, "saved")
        b, _ = _drawn(tmp_path, c, "saved", {"jitterseed": "7"})
        for p, q in zip(_band_of(a), _band_of(b)):
            assert np.array_equal(p, q)

    def test_two_local_fits_per_grid_point(self, tmp_path, monkeypatch):
        calls = []
        real = dr._lpoly_local_wls

        def spy(*a, **k):
            calls.append(1)
            return real(*a, **k)
        monkeypatch.setattr(dr, "_lpoly_local_wls", spy)
        _drawn(tmp_path, _case("a_d1_bw500_pw800"), "saved")
        assert 0 < len(calls) <= 2 * 50


class TestFewObservations:
    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("n", [2, 3])
    def test_bwidth_1000_draws_statas_smooth_and_no_band(self, tmp_path, n, mode):
        c = _case(f"in{n}_bw1000")
        assert int(c["ngrid"]) == 50 and all(v is None for v in c["gse"])
        srcs, notes = _drawn(tmp_path, c, mode)
        band, line = _layer(srcs)
        assert all(len(b["y_lower"]) == 0 for b in band)
        drawn = [s for s in line if len(s["x_lp"])]
        assert len(drawn) == 1
        np.testing.assert_allclose(np.asarray(drawn[0]["y_lp"], float),
                                   _arr(c["gy"]), rtol=1e-9)
        assert not [m for m in notes if "lpolyci" in m], notes


def _layer_sources(renderers):
    out = []
    for r in renderers:
        s = getattr(r, "data_source", None)
        if s is not None and s not in out:
            out.append(s)
    return out


class TestSources:
    @pytest.mark.parametrize("mode", _MODES)
    def test_the_band_joins_across_a_missing_ci(self, tmp_path, mode):
        c = _case("a_d1_bw500_var10")
        srcs, _ = _drawn(tmp_path, c, mode)
        bx, lo, hi = _band_of(srcs)
        assert np.isfinite(lo).all() and np.isfinite(hi).all()
        miss = [i for i, v in enumerate(c["gse"]) if v is None and c["gy"][i] is not None]
        assert miss
        gx = _arr(c["gx"])
        for i in miss:
            assert not (np.abs(bx - gx[i]) <= 1e-9 * gx[i]).any()

    def _three(self, renderers):
        rs = [r for r in renderers
              if type(r.glyph).__name__ in ("VArea", "Patch", "Line")]
        kinds = [type(r.glyph).__name__ for r in rs]
        srcs = [r.data_source for r in rs]
        return kinds, srcs

    @pytest.mark.parametrize("mode", _MODES)
    def test_three_sources_drawn_or_empty(self, tmp_path, mode):
        for in_expr in ("", "1/1"):
            spec = tl._spec([{"type": "lpolyci", "yvar": "mpg",
                              "xvar": "weight", "options": {}}])
            if in_expr:
                spec["graphs"][0]["in_expr"] = in_expr
            figs = self._figures(tmp_path, spec, mode)
            kinds, srcs = self._three(figs[0].renderers)
            assert kinds == ["VArea", "Patch", "Line"], kinds
            assert len({id(s) for s in srcs}) == 3, in_expr

    def _figures(self, tmp_path, spec, mode):
        from bokeh.models import Plot
        if mode == "saved":
            _t, sp, dp = tl._write(tmp_path, spec, _df("auto"))
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                r = dr.DashRenderer(sp, dp)
                render_models(r)
            return list(r.figures.values())
        doc, _w, _ap = tl._served_doc(tmp_path, spec, _df("auto"))
        return [p for p in doc.select({"type": Plot}) if p.renderers]

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_empty_branch_keeps_line_styling(self, tmp_path, mode):
        spec = tl._spec([{"type": "lpolyci", "yvar": "mpg", "xvar": "weight",
                          "options": {"lcolor": "red", "lpattern": "dash"}}])
        spec["graphs"][0]["in_expr"] = "1/1"
        figs = self._figures(tmp_path, spec, mode)
        line = [r for r in figs[0].renderers if type(r.glyph).__name__ == "Line"][0]
        assert line.glyph.line_color == "#ff0000"
        assert list(line.glyph.line_dash) == [8, 4]

    def test_a_served_refit_that_empties_a_panel_warns_nothing(self, tmp_path):
        c = _case("a_d0_bw500_pw800")
        spec = _spec_of(c)
        spec["graphs"][0]["graph_options"]["by"] = "foreign"
        spec["graphs"][0]["options"]["by"] = "foreign"
        spec["build_options"]["filter"] = "foreign, type(dropdown)"
        doc, _w, _ap = tl._served_doc(tmp_path, spec, _df("auto"))
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            tl._move_to(doc, "Foreign")
        assert not [str(m.message) for m in caught if "redrew" in str(m.message)]


class TestServedRefit:
    def test_a_move_to_foreign_redraws_statas_band(self, tmp_path):
        c = _case("a_d0_foreign_bw400_pw600")
        spec = _spec_of(dict(c, cond="1"))
        spec["build_options"]["filter"] = "foreign, type(dropdown)"
        doc, _w, _ap = tl._served_doc(tmp_path, spec, _df("auto"))
        tl._move_to(doc, "Foreign")
        bx, lo, hi = _band_of(tl._doc_sources(doc))
        gy = _arr(c["gy"])
        _check_band(c, bx, lo, hi, lambda j: 1e-8 * max(1.0, abs(gy[j])))


_HOSTILE = [("pwidth", "abc"), ("pwidth", "-1"), ("pwidth", "nan"),
            ("lpvar", "abc"), ("lpvar", "-1"), ("lpvar", "nan"),
            ("level", "5"), ("level", "abc")]


class TestHostileValues:
    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("value", ["pwidth=1e-300", "lpvar=8e307"]
                             + [f"{k}={v}" for k, v in _HOSTILE])
    def test_hostile_spec_values(self, tmp_path, value, mode):
        k, v = value.split("=", 1)
        c = _case("a_d1_bw500_pw800")
        srcs, notes = _drawn(tmp_path, c, mode, {k: v})
        for s in srcs:
            for col, vals in s.items():
                try:
                    a = np.asarray(vals, dtype=float)
                except (TypeError, ValueError):
                    continue
                assert not np.isinf(a).any(), (value, col)
        bx, lo, hi = _band_of(srcs)
        if value == "pwidth=1e-300":
            assert len(bx) == 0
            return
        if value == "lpvar=8e307":
            return
        named = [n for n in notes if v in n and (k.replace("lpvar", "var") in n)]
        assert len(named) == 1, notes
        # the default is used: the band is the default's
        ref, _ = _drawn(tmp_path, c, mode, {k: ""} if k != "level" else None)
        for p, q in zip(_band_of(ref), (bx, lo, hi)):
            np.testing.assert_allclose(p, q, rtol=1e-12)

    def test_a_bad_spec_value_is_noted_once_across_moves(self, tmp_path):
        c = _case("a_d1_bw500_pw800")
        spec = _spec_of(c, {"pwidth": "abc"})
        spec["build_options"]["filter"] = "foreign, type(dropdown)"
        doc, built, _ap = tl._served_doc(tmp_path, spec, _df("auto"))
        notes = [n for n in built if "pwidth" in n]
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            for lab in ("Foreign", "Domestic", "Foreign"):
                tl._move_to(doc, lab)
        notes += [str(m.message) for m in caught if "pwidth" in str(m.message)]
        assert len(notes) == 1, notes


class TestLegendKey:
    def _keys(self, tmp_path, level, mode):
        c = _case("a_d0_bw500_pw800")
        spec = _spec_of(c, {"level": level})
        if mode == "saved":
            _t, sp, dp = tl._write(tmp_path, spec, _df("auto"))
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                r = dr.DashRenderer(sp, dp)
                render_models(r)
            figs = list(r.figures.values())
            srcs = tl._sources_saved(tmp_path, spec, _df("auto"))[0]
        else:
            doc, _w, _ap = tl._served_doc(tmp_path, spec, _df("auto"))
            from bokeh.models import Plot
            figs = [p for p in doc.select({"type": Plot}) if p.renderers]
            srcs = tl._doc_sources(doc)
        labels = []
        for f in figs:
            for lg in f.select({"type": Legend}):
                for it in lg.items:
                    lab = it.label
                    labels.append(lab.get("value") if isinstance(lab, dict)
                                  else getattr(lab, "value", lab))
        return labels, srcs

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("level", ["5", "abc", "90"])
    def test_the_key_reads_the_level_the_band_is_drawn_at(self, tmp_path, level, mode):
        labels, srcs = self._keys(tmp_path, level, mode)
        want = 90.0 if level == "90" else 95.0
        assert f"{want:g}% CI" in labels, labels
        c = _case("a_d0_lvl90" if level == "90" else "a_d0_bw500_pw800")
        bx, lo, hi = _band_of(srcs)
        z = dr._dash_invnormal(0.5 * (1 - want / 100) + want / 100)
        if level == "90":
            assert z == pytest.approx(1.6448536269514722, rel=1e-15)
        gse, gy = _arr(c["gse"]), _arr(c["gy"])
        gx = _arr(c["gx"])
        for a, l in zip(bx, lo):
            j = int(np.nanargmin(np.abs(gx - a)))
            if np.isfinite(gse[j]) and j not in set(_NODF.get(c["id"], [])):
                assert abs(l - (gy[j] - z * gse[j])) <= 1e-8 * max(1, abs(gy[j]))


class TestNoVarKey:
    def test_no_option_key_is_named_var(self):
        plots = [{"type": "lpolyci", "yvar": "mpg", "xvar": "weight",
                  "options": {"pwidth": "800", "lpvar": "10"}}]
        assert dr.DashRenderer._collect_plot_vars(plots) == ["mpg", "weight"]
        with open(os.path.join(_HERE, "..", "dash.ado")) as fh:
            ado = fh.read()
        i = ado.index("program define _dash_plot_opts_to_json")
        body = ado[i:ado.index("\nend", i)]
        assert " lpvar" in body and " pwidth" in body
        assert " var " not in body.replace("\n", " ")


class TestTheServedAppCarriesTheBandHelpers:
    def test_names_defined(self, tmp_path):
        c = _case("a_d1_bw500_pw800")
        _doc, _w, ap = tl._served_doc(tmp_path, _spec_of(c), _df("auto"))
        text = open(ap).read()
        for s in ("def _lpoly_kernel_weights(", "def _lpoly_local_wls(",
                  "def _lpoly_se(", "def _dash_invnormal(", "_LPOLY_DF_TOL ="):
            assert s in text, s
        ns = {"__name__": "_lpci_exec"}
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            exec_app(text, ap, ns)
        x, y, _ = _sample(c)
        gx = _arr(c["gx"])
        a = ns["_lpoly_se"](x, y, gx, 500.0, 800.0, 1, "epanechnikov")
        b = dr._lpoly_se(x, y, gx, 500.0, 800.0, 1, "epanechnikov")
        np.testing.assert_array_equal(a, b)
