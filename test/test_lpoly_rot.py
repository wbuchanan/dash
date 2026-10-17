"""lpoly's default bandwidth is Stata's rule of thumb (WP-29 P0.7).

dash computed ``0.65 * (s^2/S)^(1/5)`` from a global quartic, ignored
kernel() and degree(), and fell back to range/10 below eight observations.
On sysuse auto, ``lpoly mpg weight, kernel(biweight) degree(2)`` got 63.80
where Stata's r(bwidth) is 302.45 (34 drawn points against 50), and
``lpoly mpg foreign`` drew a curve between the group means where twoway
draws a line at 0.

Stata's rule, as lpoly computes it in compiled Mata, is ported in
``_lpoly_rot_detail``: the Fan-Gijbels constant of the kernel by trapezoid
quadrature, a global fit of degree pe+3 in raw powers with Stata's invsym
column rule (relative 1e-9 and absolute 1e-19), quadcross overflow, and
Stata's float64 arithmetic where the global fit is exact.  The local fit
keeps the columns invsym keeps in a rank-deficient window (Part C).

Every number comes from test/fixtures/lpoly_rot_truth.json
(scripts/extract_lpoly_rot_truth.do).  Tolerances follow section 11's SD-1
tiers: ``exact`` rows 1e-7, ``noisy`` rows 5e-5, degree 4/5 5e-4, and the
four degree-2 rows of the offset sweep (weight + 1e3, 5e3, 5e4, 6e4) 1e-4,
by the maintainer's ruling of 01oct2026: Stata's own float64 round-off on
raw powers up to x^6, where dash's exact rule agrees with an all-Fraction
computation from the data to 1e-14.
"""
import math
import importlib.util
import itertools
import json
import os
import sys
import time
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import ColumnDataSource, Select

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import make_data_json  # noqa: E402

_FIX = os.path.join(_HERE, "fixtures", "lpoly_rot_truth.json")
_SEQ = itertools.count()
_KERNELS8 = ("epanechnikov", "epan2", "biweight", "cosine", "gaussian",
             "parzen", "rectangle", "triangle")

#: section 11 Evidence, "the constants" (the research prototype, bit for bit)
_EVIDENCE_C = {
    "epanechnikov": (0.7688119451983404, 1.4510983654380067, 2.119707526564211, 2.7849289975849043),
    "epan2": (1.7193092621259016, 3.245668826171823, 4.74230800612505, 6.232578887244081),
    "biweight": (2.0361684221829894, 3.6333572150005558, 5.158207981435779, 6.659696773488038),
    "cosine": (4.261325461635762, 7.465910256468045, 10.516178558247534, 13.52565407786959),
    "gaussian": (0.7763932398225403, 1.1605364963657514, 1.4508015133135794, 1.7147660572783578),
    "parzen": (2.679241025642047, 4.354113262700628, 5.908520000476076, 7.422676088655606),
    "rectangle": (1.3681484904911154, 2.849598716697929, 4.338920614551152, 5.832847955090462),
    "triangle": (1.8887652986701782, 3.420486711722465, 4.917653569707844, 6.4077843560534875),
}


from conftest import render_models  # noqa: E402


def _truth():
    if not os.path.exists(_FIX):
        pytest.fail("test/fixtures/lpoly_rot_truth.json is missing: run "
                    "scripts/extract_lpoly_rot_truth.do")
    with open(_FIX) as fh:
        return json.load(fh)


_T = _truth() if os.path.exists(_FIX) else {"rows": [], "curves": [],
                                            "datasets": {}, "serset": [],
                                            "divergences": []}
_ROWS = {r["id"]: r for r in _T["rows"]}
_CURVES = {c["id"]: c for c in _T["curves"]}
_DIVERGENT = {i for dv in _T.get("divergences", []) for i in dv["rows"]}


def _row(rid):
    if rid not in _ROWS:
        pytest.fail(f"fixture row {rid} is missing: rerun "
                    "scripts/extract_lpoly_rot_truth.do")
    return _ROWS[rid]


def _sample(row):
    """``x, y, lw`` of a fixture row: aw normalised to mean 1, fw raw."""
    D = _T["datasets"][row["ds"]]
    idx = row["idx"]
    x = np.array([D[row["x"]][i] for i in idx], dtype=float)
    y = np.array([D[row["y"]][i] for i in idx], dtype=float)
    if row.get("w"):
        w = np.array([D[row["w"]][i] for i in idx], dtype=float)
        if row["wtype"] == "aw":
            w = w * len(w) / w.sum()
        return x, y, w
    return x, y, None


def _count(x, y, h, row):
    _, yf = dr.GlyphMapper._compute_lpoly_fit(
        x, y, bwidth=h, degree=row["degree"], kernel=row["kernel"],
        n_grid=row["n_grid"], w=None if not row.get("w") else _sample(row)[2])
    return int(np.isfinite(yf).sum())


def _rows(*classes, maxdeg=5):
    return [pytest.param(r["id"], id=r["id"]) for r in _T["rows"]
            if r["class"] in classes and r["degree"] <= maxdeg
            and r["id"] not in _DIVERGENT]


def _rot(x, y, w=None, degree=0, kernel="epanechnikov"):
    """GlyphMapper._default_lpoly_bwidth with degree and kernel.  Before
    P0.7 the rule took neither, so the old three-argument call stands in
    and the failure shows the old value, not a TypeError."""
    f = dr.GlyphMapper._default_lpoly_bwidth
    try:
        return f(x, y, w, degree, kernel)
    except TypeError:
        return f(x, y, w)


def _need_s05():
    if not hasattr(dr, "_dash_date_units"):
        pytest.fail("needs S05 (u08 date units)")


# --------------------------------------------------------------- documents

def _auto_df(cols=("mpg", "weight", "price", "foreign", "rep78")):
    D = _T["datasets"]["auto"]
    return pd.DataFrame({c: D[c] for c in cols})


_VL = {"origin": {"0": "Domestic", "1": "Foreign"}}
_VLN = {"foreign": "origin"}


def _spec(plots, go=None, bo=None):
    go = dict(go or {})
    go.setdefault("name", "g1")
    b = {"layout": "auto", "registry": "g1", "level": "95", "formats": {},
         "theme": "", "scheme": "", "session_scheme": "", "filter": "",
         "link": "", "title": "t", "subtitle": ""}
    b.update(bo or {})
    return {"graphs": [{"name": "g1", "graph_options": go, "options": dict(go),
                        "plots": plots}],
            "kpis": [], "build_options": b}


def _plot(ptype="lpoly", y="mpg", x="weight", **opts):
    return {"type": ptype, "yvar": y, "xvar": x,
            "options": {k: str(v) for k, v in opts.items()}}


def _write(tmp_path, spec, df):
    tag = next(_SEQ)
    sp = tmp_path / f"s_{tag}.json"
    dp = tmp_path / f"d_{tag}.json"
    sp.write_text(json.dumps(spec))
    dp.write_text(json.dumps(make_data_json(
        df, _VL, _VLN, variable_labels={c: c for c in df.columns})))
    return tag, str(sp), str(dp)


def _sources_saved(tmp_path, spec, df):
    """(sources in figure order, warnings) of the saved renderer."""
    _tag, sp, dp = _write(tmp_path, spec, df)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r = dr.DashRenderer(sp, dp)
        render_models(r)
    out = []
    for fig in r.figures.values():
        for ren in fig.renderers:
            src = getattr(ren, "data_source", None)
            if src is not None:
                out.append(dict(src.data))
    return out, [str(w.message) for w in caught]


def _served_doc(tmp_path, spec, df):
    tag, sp, dp = _write(tmp_path, spec, df)
    ap = tmp_path / f"a_{tag}.py"
    with warnings.catch_warnings(record=True) as built:
        warnings.simplefilter("always")
        dr.ServerAppBuilder(sp, dp).build(str(ap))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ms = importlib.util.spec_from_file_location(f"_lprot_{tag}", str(ap))
        mod = importlib.util.module_from_spec(ms)
        ms.loader.exec_module(mod)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        doc = Document()
        mod.make_document(doc)
    return doc, [str(w.message) for w in list(built) + list(caught)], str(ap)


def _doc_sources(doc):
    out, seen = [], set()
    for m in doc.select({"type": ColumnDataSource}):
        if id(m) not in seen:
            seen.add(id(m))
            out.append(dict(m.data))
    return out


def _sources(tmp_path, spec, df, mode):
    if mode == "saved":
        return _sources_saved(tmp_path, spec, df)
    doc, w, _ap = _served_doc(tmp_path, spec, df)
    return _doc_sources(doc), w


def _lp(sources):
    """The lpoly line sources (``x_lp``/``y_lp``), as float arrays."""
    return [(np.asarray(s["x_lp"], float), np.asarray(s["y_lp"], float))
            for s in sources if "x_lp" in s and "y_lp" in s
            and "y_lower" not in s]


def _fire(widget, value):
    widget.value = value
    for key in ("value", "value_throttled"):
        for cb in list(widget._callbacks.get(key, [])):
            cb("value", None, value)


def _move_to(doc, label):
    """Pick the dropdown option labelled *label* in the served document."""
    sel = [m for m in doc.select({"type": Select}) if hasattr(m, "_dash_var")]
    assert sel, "no dropdown in the served document"
    raw = [v for v, lab in sel[0].options if lab == label]
    assert raw, sel[0].options
    _fire(sel[0], raw[0])


def _near(px, py, gx, gy, tol):
    """Each drawn (px, py) lies within *tol* of Stata's gy at the same gx."""
    gx = np.asarray(gx, float)
    gy = np.asarray(gy, float)
    for a, b in zip(px, py):
        j = int(np.argmin(np.abs(gx - a)))
        assert abs(gx[j] - a) <= 1e-9 * max(1.0, abs(a)), (a, gx[j])
        assert abs(gy[j] - b) <= tol, (a, b, gy[j])


def _sensitive(x, y, w, h_stata, h_dash, degree, kernel, n_grid, tol):
    """Grid x where moving Stata's bandwidth by dash's actual relative gap
    (to dash's bandwidth) moves the curve more than *tol* (maintainer
    ruling, 01oct2026): there Stata's own round-off in r(bwidth) decides
    the curve, so the point is left out of a drawn-curve comparison, and
    named.  The gap itself is asserted at the row's tier by the caller."""
    gx, g0 = dr.GlyphMapper._compute_lpoly_fit(
        x, y, bwidth=h_stata, degree=degree, kernel=kernel, n_grid=n_grid,
        w=w)
    _, g1 = dr.GlyphMapper._compute_lpoly_fit(
        x, y, bwidth=h_dash, degree=degree, kernel=kernel, n_grid=n_grid,
        w=w)
    sens = np.abs(g1 - g0)
    return {float(gx[i]): float(sens[i]) for i in range(len(gx))
            if np.isfinite(sens[i]) and sens[i] > tol}


def _near_except(px, py, gx, gy, tol, excluded):
    """``_near`` on every point but the *excluded* (sensitive) ones."""
    keep = [i for i, a in enumerate(px)
            if not any(abs(a - e) <= 1e-9 * max(1.0, abs(e)) for e in excluded)]
    _near(np.asarray(px)[keep], np.asarray(py)[keep], gx, gy, tol)


def _finite_count(c):
    return sum(1 for v in c["gy"] if v is not None)


# ===================================================================== tests


class TestStataInvsym:
    def test_a_pivot_below_1e9_of_its_own_diagonal_is_dropped(self):
        # Mata, 01oct2026: diagonal(invsym(G)) :!= 0 is 01, 11, 10, 11 for
        # these four (the largest pivot is swept first, so in the unscaled
        # pair the SECOND column is kept and the first dropped).
        f = dr._stata_invsym_keep
        assert f([[1.0, 1.0], [1.0, 1.0 + 9.9e-10]]) == [1]
        assert f([[1.0, 1.0], [1.0, 1.0 + 1e-9]]) == [0, 1]
        assert f([[1e6, 1e3], [1e3, 1.0 + 9.9e-10]]) == [0]
        assert f([[1e6, 1e3], [1e3, 1.0 + 1e-9]]) == [0, 1]

    def test_an_absolute_pivot_below_1e_19_is_dropped(self):
        f = dr._stata_invsym_keep
        assert f([[1e-19]]) == [0]
        assert f([[float(np.nextafter(1e-19, 0.0))]]) == []
        assert f([[1e10, 0.0], [0.0, 5e-20]]) == [0]
        assert f([[1.0, 1e-6], [1e-6, 1e-12 + 5e-20]]) == [0]

    def test_the_largest_current_pivot_is_swept_first(self):
        V = np.array([[0.0, 9.0, 10.0], [2.0, 1.0, 0.0], [2e-6, 0.0, 0.0]])
        assert dr._stata_invsym_keep(V.T @ V) == [0, 2]
        # an exact tie keeps the first column
        assert dr._stata_invsym_keep([[1.0, 1.0], [1.0, 1.0]]) == [0]

    def test_the_order_argument_sweeps_those_columns_first(self):
        # A two-point window off-centre (x0 not between the points'
        # midpoint): with the intercept swept first, d^2 has the larger
        # pivot and d is then collinear, so the kept set is {1, d^2}.
        d = np.array([-100.0, 300.0])
        X = np.vander(d, 3, increasing=True)
        G = X.T @ X
        assert dr._stata_invsym_keep(G, order=(0,)) == [0, 2]
        # Without the order invsym sweeps d^2 first.  On d = (-100, 100)
        # Mata's invsym(X'X) keeps {d, d^2} (diagonal pattern 011).
        d = np.array([-100.0, 100.0])
        X = np.vander(d, 3, increasing=True)
        assert dr._stata_invsym_keep(X.T @ X) == [1, 2]


class TestRotConstants:
    def test_table_is_statas_trapezoid_quadrature(self):
        tab = dr._LPOLY_ROT_CONSTANTS
        for k in _KERNELS8:
            for i, p in enumerate((1, 3, 5, 7)):
                c = dr._lpoly_rot_constant(k, p)
                assert abs(tab[(k, p)] / c - 1) <= 1e-13, (k, p)
                assert abs(tab[(k, p)] / _EVIDENCE_C[k][i] - 1) <= 1e-15, (k, p)
            # WP-31 D35: degree 8 and above, a literal written from the same
            # quadrature.  Its digits follow the numpy build there: measured
            # across Stata's Python and the development one, 2e-10 relative
            # to pe 13, 3e-7 at 17, 8% by pe 25 (the quadrature of high powers
            # loses its precision, which is part of why dash notes a degree
            # past 7); the literal keeps the page the same on every host.
            for p in range(9, (dr._LPOLY_DEGREE_FIT_MAX | 1) + 1, 2):
                c = dr._lpoly_rot_constant(k, p)
                assert tab[(k, p)] > 0 and math.isfinite(tab[(k, p)]), (k, p)
                if p <= 13:
                    assert abs(tab[(k, p)] / c - 1) <= 1e-9, (k, p)
        # The implied constant r(bwidth)/term of every exact row on
        # unshifted data: the rule's term is h/C, so r(bwidth)*C/h.  The
        # offset sweep (x = weight + a*10^e) is held by test_r_bwidth.
        for r in _T["rows"]:
            if r["class"] != "exact" or r["x"].startswith("wo"):
                continue
            x, y, w = _sample(r)
            h = dr._lpoly_rot_detail(x, y, w, r["degree"], r["kernel"])["h"]
            assert abs(r["bwidth"] / h - 1) <= 2e-9, r["id"]

    def test_support_is_strict(self):
        L, m = dr._LPOLY_ROT_GRID["rectangle"]
        z = np.linspace(-L, L, m)
        # the same quadrature with |z| <= 1 counted
        support, kfn = dr._KERNELS["rectangle"]
        hq = z[1] - z[0]
        wq = np.full(m, hq)
        wq[0] = wq[-1] = hq / 2
        f = np.where(np.abs(z) <= support, kfn(z), 0.0)
        mu = [float(np.sum(wq * z ** j * f)) for j in range(5)]
        e = np.linalg.solve(np.array([[mu[0], mu[1]], [mu[1], mu[2]]]),
                            [1.0, 0.0])
        ks = (e[0] + e[1] * z) * f
        c = (4.0 * np.sum(wq * ks * ks)
             / (4.0 * np.sum(wq * z * z * ks) ** 2)) ** (1 / 5)
        strict = dr._LPOLY_ROT_CONSTANTS[("rectangle", 1)]
        assert abs(c / strict - 1 - (-0.012687)) < 5e-6
        assert strict == pytest.approx(_EVIDENCE_C["rectangle"][0], rel=1e-15)


class TestRotAgainstStata:
    @pytest.mark.parametrize("rid", _rows("exact", "noisy"))
    def test_r_bwidth(self, rid):
        r = _row(rid)
        x, y, w = _sample(r)
        h = _rot(x, y, w, r["degree"], r["kernel"])
        assert np.isfinite(h) and abs(h / r["bwidth"] - 1) <= r["tol"], (
            h, r["bwidth"])

    def test_kept_columns_match_invsym_quadcross_on_raw_powers(self):
        bad = []
        for r in _T["rows"]:
            if r["class"] not in ("exact", "noisy") or r["id"] in _DIVERGENT:
                continue
            x, y, w = _sample(r)
            k = dr._lpoly_rot_detail(x, y, w, r["degree"], r["kernel"])["kept"]
            pat = "".join("1" if i in k else "0" for i in range(len(r["kept"])))
            if pat != r["kept"]:
                bad.append((r["id"], pat, r["kept"]))
        assert not bad, bad[:10]
        for rid, pat in (("auto-mpg-wtd--epanechnikov-d1-n74", "01111"),
                         ("sp500-close-date--epanechnikov-d2-n248", "0000111"),
                         ("uslifeexp-le-year--epanechnikov-d2-n100", "1000111"),
                         ("auto-price-rep78--epanechnikov-d3-n69", "1010111"),
                         ("auto-mpg-f38--epanechnikov-d0-n74", "00011")):
            assert _row(rid)["kept"] == pat

    def test_even_degree_takes_the_next_odd_rule(self):
        r = _row("auto-mpg-weight--epanechnikov-d0-n74")
        x, y, _ = _sample(r)
        for k in _KERNELS8:
            f = _rot
            assert f(x, y, None, 0, k) == f(x, y, None, 1, k)
            assert f(x, y, None, 2, k) == f(x, y, None, 3, k)

    def test_years_and_dates_follow_statas_raw_power_arithmetic(self):
        _need_s05()
        f = _rot
        for rid, want in (("uslifeexp-le-year--epanechnikov-d0-n100", 3.6430833364289748),
                          ("uslifeexp-le-year--epanechnikov-d2-n100", 31.878433756089901),
                          ("sp500-close-date--epanechnikov-d0-n248", 14.545570460491128),
                          ("sp500-close-date--epanechnikov-d2-n248", 200.51125382378513)):
            r = _row(rid)
            x, y, w = _sample(r)
            assert abs(r["bwidth"] / want - 1) < 1e-12
            assert abs(f(x, y, w, r["degree"], r["kernel"]) / want - 1) <= r["tol"]
        # NOT the exact-math value of the centred problem (2.7119 / 7.32)
        r = _row("uslifeexp-le-year--epanechnikov-d0-n100")
        x, y, w = _sample(r)
        assert abs(f(x, y, w, 0, "epanechnikov") - 2.7119) > 0.5

    def test_tc_datetime(self):
        _need_s05()
        f = _rot
        for rid, want in (("sp500-close-datetc--epanechnikov-d0-n248", 32504400.964425806),
                          ("sp500-close-datetc--epanechnikov-d2-n248", 2274141561.3559403)):
            r = _row(rid)
            x, y, w = _sample(r)
            assert abs(r["bwidth"] / want - 1) < 1e-9
            assert abs(f(x, y, w, r["degree"], "epanechnikov") / want - 1) <= 5e-5

    def test_small_x_scales(self):
        f = _rot
        n = 0
        for r in _T["rows"]:
            if not r["x"].startswith("wkm") or int(r["x"][3:]) > 9:
                continue
            x, y, w = _sample(r)
            h = f(x, y, w, r["degree"], r["kernel"])
            if r["bwidth"] is None or r["bwidth"] == 0:
                assert np.isnan(h), r["id"]
            else:
                assert abs(h / r["bwidth"] - 1) <= r["tol"], (r["id"], h)
            n += 1
        assert n == 36

    def test_weights(self):
        f = _rot
        for r in _T["rows"]:
            if r["ds"] == "auto" and r["w"] and r["class"] in ("exact", "noisy"):
                x, y, w = _sample(r)
                h = f(x, y, w, r["degree"], r["kernel"])
                assert abs(h / r["bwidth"] - 1) <= r["tol"], r["id"]
        # an fweight equals the same data with rows duplicated
        r = _row("auto-mpg-weight-fw.rep78-epanechnikov-d0-n69")
        x, y, w = _sample(r)
        k = w.astype(int)
        hf = f(x, y, w, 0, "epanechnikov")
        hd = f(np.repeat(x, k), np.repeat(y, k), None, 0, "epanechnikov")
        assert abs(hf / hd - 1) < 1e-9
        # a zero aweight equals a missing one (Stata drops both first)
        a = _row("auto-mpg-weight-aw.wz-epanechnikov-d0-n59")
        b = _row("auto-mpg-weight-aw.price-epanechnikov-d0-n59")
        assert a["idx"] == b["idx"] and a["bwidth"] == pytest.approx(b["bwidth"], rel=1e-12)
        xa, ya, wa = _sample(a)
        assert f(xa, ya, wa, 0, "epanechnikov") == pytest.approx(b["bwidth"], rel=1e-7)


class TestRotDegenerate:
    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_x_of_zeros_and_ones_draws_a_line_at_zero(self, tmp_path, mode):
        srcs, notes = _sources(tmp_path, _spec([_plot(x="foreign")]),
                               _auto_df(), mode)
        lines = _lp(srcs)
        assert len(lines) == 1
        x, y = lines[0]
        assert len(x) == 50 and x[0] == 0.0 and x[-1] == 1.0
        assert np.all(y == 0.0), y
        assert not [n for n in notes if "lpoly" in n], notes

    def test_constant_x_and_huge_x_are_statas_missing_bandwidth(self):
        for rid in ("auto-mpg-one--epanechnikov-d0-n74",
                    "auto-mpg-wkp200--epanechnikov-d2-n74"):
            r = _row(rid)
            assert r["bwidth"] is None
            x, y, w = _sample(r)
            d = dr._lpoly_rot_detail(x, y, w, r["degree"], r["kernel"])
            assert np.isnan(d["h"]) and d["route"] == "missing"

    def test_quadcross_overflow_is_statas_missing(self):
        f = _rot
        for nm, deg in (("wkp22", 2), ("wkp25", 2), ("wkp30", 2),
                        ("wkp35", 0), ("wkp40", 0), ("wkp50", 0)):
            r = _row(f"auto-mpg-{nm}--epanechnikov-d{deg}-n74")
            assert r["bwidth"] is None or r["bwidth"] == 0
            x, y, w = _sample(r)
            assert np.isnan(f(x, y, w, deg, "epanechnikov")), nm
        for nm, deg in (("wkp20", 2), ("wkp30", 0)):
            r = _row(f"auto-mpg-{nm}--epanechnikov-d{deg}-n74")
            x, y, w = _sample(r)
            assert abs(f(x, y, w, deg, "epanechnikov") / r["bwidth"] - 1) <= r["tol"]

    def test_y_scale_extremes(self):
        f = _rot
        n = 0
        for r in _T["rows"]:
            if not r["y"].startswith("mk"):
                continue
            x, y, w = _sample(r)
            h = f(x, y, w, r["degree"], r["kernel"])
            n += 1
            if r["id"] in _DIVERGENT:
                assert r["id"] == "auto-mkm150-weight--epanechnikov-d2-n74"
                assert np.isnan(h)
            elif r["bwidth"] is None or r["bwidth"] == 0:
                assert np.isnan(h), r["id"]
            else:
                assert abs(h / r["bwidth"] - 1) <= r["tol"], r["id"]
        assert n == 18
        assert any(d["id"] == "D3" for d in _T["divergences"])

    def test_an_exact_fit_uses_statas_float_arithmetic(self):
        noise = [r for r in _T["rows"] if r["class"] == "noise"]
        assert len(noise) >= 40
        for r in noise:
            x, y, w = _sample(r)
            d = dr._lpoly_rot_detail(x, y, w, r["degree"], r["kernel"])
            assert d["route"] == "float", r["id"]
            assert np.isfinite(d["h"]) and d["h"] > 0, r["id"]
            # Counts on compact kernels: twoway counts a gaussian weight
            # toward its two-observation rule only above about 1e-14
            # (section 11 SD-10, not changed here).
            if r["kernel"] != "gaussian" and (
                    r["y"] in ("ycon", "ysq") or r["cond"].startswith("_n<=")):
                assert _count(x, y, d["h"], r) == int(r["ngrid"]), r["id"]
        # where Stata's curve does not depend on h, dash's equals it
        for cid in ("ycon_d0", "ycon_d1", "ycon_d2", "ycon_d3", "ysq_d2",
                    "ysq_d3", "ylin_d1", "ylin_d2", "ylin_d3", "yw_d2",
                    "yw_d3"):
            c = _CURVES[cid]
            r = _row(f"auto-{c['y']}-weight--epanechnikov-d{c['degree']}-n74")
            x, y, w = _sample(r)
            h = _rot(x, y, w, c["degree"])
            gx, gy = dr.GlyphMapper._compute_lpoly_fit(
                x, y, bwidth=h, degree=c["degree"], n_grid=50)
            ok = np.isfinite(gy)
            assert ok.sum() == _finite_count(c), cid
            want = np.array([v for v in c["gy"] if v is not None])
            np.testing.assert_allclose(gy[ok], want, rtol=1e-9, atol=1e-9 * np.abs(want).max(),
                                       err_msg=cid)
        ids = {d["id"]: d for d in _T["divergences"]}
        for dv in ("D1", "D2"):
            for rid in ids[dv]["rows"]:
                x, y, w = _sample(_row(rid))
                h = _rot(x, y, w, _row(rid)["degree"])
                assert np.isfinite(h) and h > 0

    def test_small_samples_draw_statas_ngrid(self):
        for n in range(2, 13):
            for d in range(4):
                r = _row(f"auto-mpg-weight--epanechnikov-d{d}-n{n}")
                x, y, w = _sample(r)
                h = _rot(x, y, w, d)
                assert _count(x, y, h, r) == int(r["ngrid"]), (n, d, h)

    def test_never_raises_and_is_fast(self):
        rng = np.random.default_rng(7)
        f = _rot
        cases = [
            (np.array([5e-324, 1e-323, 2e-323]), np.array([1.0, 2.0, 4.0])),
            (np.array([-1e300, 0.0, 1e300]), np.array([1.0, 3.0, 2.0])),
            (np.array([1.0, 1.0, 2.0, 2.0]), np.array([1.0, 1.0, 2.0, 2.0])),
            (np.array([1.0, 2.0]), np.array([3.0, 4.0])),
            (np.full(10, 3.0), np.full(10, 3.0)),
            (np.arange(10.0), np.full(10, 1e300)),
            (rng.normal(size=50) * 1e75, rng.normal(size=50)),
        ]
        auto = _row("auto-mpg-weight--epanechnikov-d0-n74")
        ax, ay, _ = _sample(auto)
        cases.append((ax * 1e75, ay))
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            for x, y in cases:
                for d in range(4):
                    for k in ("epanechnikov", "gaussian", "nonesuch"):
                        h = f(x, y, None, d, k)
                        assert isinstance(h, float)
                        assert np.isnan(h) or (np.isfinite(h) and h > 0), (x, d, h)
            x = rng.uniform(0, 100, 100000)
            y = np.sin(x / 7) + rng.normal(0, .3, 100000)
            t0 = time.perf_counter()
            h = f(x, y, None, 3, "biweight")
            assert time.perf_counter() - t0 < 1.0
            assert np.isfinite(h)


class TestMapLpolyUsesTheRule:
    def test_kernel_degree_and_weights_reach_the_rule(self, tmp_path, monkeypatch):
        seen = []
        real = dr.GlyphMapper._default_lpoly_bwidth

        def spy(x, y, w=None, degree=0, kernel="epanechnikov"):
            seen.append((len(x), None if w is None else len(w), degree, kernel))
            try:
                return real(x, y, w, degree, kernel)
            except TypeError:
                return real(x, y, w)
        monkeypatch.setattr(dr.GlyphMapper, "_default_lpoly_bwidth",
                            staticmethod(spy))
        srcs, _ = _sources_saved(
            tmp_path, _spec([_plot(kernel="biweight", degree=2)]), _auto_df())
        assert (74, None, 2, "biweight") in seen, seen
        (x, y), = _lp(srcs)
        c = _CURVES["bi_d2"]
        assert len(x) == 50 == _finite_count(c)
        _near(x, y, c["gx"], c["gy"], 1e-4)
        seen.clear()
        _sources_saved(tmp_path, _spec([_plot(weight="aweight", wexp="price")]),
                       _auto_df())
        assert any(s[1] == 74 and s[2] == 0 for s in seen), seen

    def test_lpolyci_line_uses_the_resolved_bandwidth(self, tmp_path):
        a, _ = _sources_saved(tmp_path, _spec([_plot(kernel="biweight", degree=2)]),
                              _auto_df())
        b, _ = _sources_saved(
            tmp_path, _spec([_plot("lpolyci", kernel="biweight", degree=2)]),
            _auto_df())
        (xa, ya), = _lp(a)
        ci = [s for s in b if "x_lp" in s and "y_lp" in s]
        xb = np.asarray(ci[-1]["x_lp"], float)
        yb = np.asarray(ci[-1]["y_lp"], float)
        np.testing.assert_allclose(xb, xa, rtol=1e-12)
        np.testing.assert_allclose(yb, ya, rtol=1e-12)

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_by_panels_use_their_own_bandwidth(self, tmp_path, mode):
        assert _row("auto-mpg-weight--epanechnikov-d0-n52")  # fixture sanity
        srcs, _ = _sources(tmp_path, _spec([_plot(kernel="biweight", degree=2)],
                                           go={"by": "foreign"}),
                           _auto_df(), mode)
        lines = _lp(srcs)
        assert len(lines) == 2, len(lines)
        D = _T["datasets"]["auto"]
        excluded_all = {}
        for cid in ("bi_d2_f0", "bi_d2_f1"):
            c = _CURVES[cid]
            # the panel whose grid starts where Stata's does (the served
            # document lists its sources in no fixed order)
            (x, y), = [ln for ln in lines if len(ln[0])
                       and abs(ln[0][0] - c["gx"][0]) < 1e-9 * c["gx"][0]]
            assert len(x) == _finite_count(c) == 50
            sx = np.array([D["weight"][i] for i in c["idx"]])
            sy = np.array([D["mpg"][i] for i in c["idx"]])
            h = _rot(sx, sy, None, 2, "biweight")
            # the bandwidth itself at its tier (degree 2: 5e-5)
            assert abs(h / c["bwidth"] - 1) <= 5e-5, (cid, h, c["bwidth"])
            exc = _sensitive(sx, sy, None, c["bwidth"], h, 2, "biweight",
                             50, 1e-4)
            excluded_all[cid] = exc
            _near_except(x, y, c["gx"], c["gy"], 1e-4, exc)
        # Measured: one point of the domestic panel (x = 4405.71 moves
        # 0.0061 mpg between Stata's 316.80386 and dash's 316.80514, a gap
        # of 4.1e-6) and none of the foreign.
        assert len(excluded_all["bi_d2_f0"]) >= 1, excluded_all
        assert not excluded_all["bi_d2_f1"], excluded_all
        for s in _T["serset"]:
            ys = [v for v in s["values"][s["vars"][0]] if v is not None]
            assert len(ys) == 50

    @pytest.mark.parametrize("mode", ["saved", "served"])
    @pytest.mark.parametrize("ptype", ["lpoly", "lpolyci"])
    def test_a_missing_bandwidth_draws_a_zero_line(self, tmp_path, ptype, mode):
        srcs, notes = _sources(tmp_path, _spec([_plot(ptype, x="foreign")]),
                               _auto_df(), mode)
        lines = [s for s in srcs if "x_lp" in s and "y_lp" in s
                 and len(s["x_lp"]) > 0]
        y = np.asarray(lines[-1]["y_lp"], float)
        assert len(y) == 50 and np.all(y == 0.0)
        assert not [n for n in notes if "lpoly" in n], notes
        if ptype == "lpolyci":
            bands = [s for s in srcs if "y_lower" in s]
            assert bands and all(len(s["y_lower"]) == 0 for s in bands)


class TestLocalFitRank:
    def test_two_point_window_at_degree_two_keeps_the_square(self):
        c = _CURVES["bi_d2_f1_bw"]
        D = _T["datasets"]["auto"]
        x = np.array([D["weight"][i] for i in c["idx"]])
        y = np.array([D["mpg"][i] for i in c["idx"]])
        gx, gy = dr.GlyphMapper._compute_lpoly_fit(
            x, y, bwidth=c["bwidth_opt"], degree=2, kernel="biweight",
            n_grid=50)
        want = [17.018155991956533, 17.00884440400364, 17.167440598142775,
                17.87839549612948, 24.482964137111367, 11.34778718474287,
                13.518830077485545, 13.924429919784265]
        np.testing.assert_allclose(gy[41:49], want, rtol=1e-9)
        np.testing.assert_allclose(gy[41:49], c["gy"][41:49], rtol=1e-9)

    def test_one_value_window_at_degree_one_is_the_group_mean(self):
        c = _CURVES["r10_d1"]
        D = _T["datasets"]["auto"]
        x = np.array([D["r10"][i] for i in c["idx"]])
        y = np.array([D["price"][i] for i in c["idx"]])
        gx, gy = dr.GlyphMapper._compute_lpoly_fit(
            x, y, bwidth=3.0, degree=1, n_grid=41)
        got = [v for v in gy if np.isfinite(v)]
        want = [v for v in c["gy"] if v is not None]
        np.testing.assert_allclose(got, want, rtol=1e-9)
        for v in (4564.5, 5125.75, 5266.0625, 5406.375, 5967.625):
            assert any(abs(g - v) < 1e-6 for g in got), v

    def test_tiny_scale_windows_follow_the_absolute_floor(self):
        D = _T["datasets"]["auto"]
        for cid in ("ws6_d3", "ws7_d2", "ws7_d3"):
            c = _CURVES[cid]
            x = np.array([D[c["x"]][i] for i in c["idx"]])
            y = np.array([D["mpg"][i] for i in c["idx"]])
            gx, gy = dr.GlyphMapper._compute_lpoly_fit(
                x, y, bwidth=c["bwidth_opt"], degree=c["degree"], n_grid=50)
            want = np.array([np.nan if v is None else v for v in c["gy"]])
            assert np.array_equal(np.isfinite(gy), np.isfinite(want)), cid
            ok = np.isfinite(want)
            np.testing.assert_allclose(gy[ok], want[ok], rtol=0, atol=1e-9,
                                       err_msg=cid)

    def test_well_conditioned_windows_keep_the_polyfit_path(self, monkeypatch):
        r = _row("auto-mpg-weight--biweight-d2-n74")
        x, y, _ = _sample(r)
        h = 302.44936813331043
        support, kfn = dr._KERNELS["biweight"]
        grid = np.linspace(x.min(), x.max(), 50)
        full = 0
        for x0 in grid:
            z = (x - x0) / h
            kw = np.where(np.abs(z) < support, kfn(z), 0.0)
            pos = kw > 0
            X = np.vander(x[pos] - x0, 3, increasing=True)
            G = (X * kw[pos, None]).T @ X
            # Every window holding three or more distinct x keeps all its
            # columns; the last four grid points see only the two heaviest
            # cars (4720, 4840) and keep {1, d^2} (Part C).
            if len(set(x[pos])) >= 3:
                assert dr._lpoly_kept_columns(G) == [0, 1, 2]
                full += 1
            else:
                assert dr._lpoly_kept_columns(G) == [0, 2]
        assert full == 46
        calls = []
        real = np.polyfit

        def spy(*a, **k):
            calls.append(1)
            return real(*a, **k)
        monkeypatch.setattr(dr.np, "polyfit", spy)
        dr.GlyphMapper._compute_lpoly_fit(x, y, bwidth=h, degree=2,
                                          kernel="biweight", n_grid=50)
        assert len(calls) == full


class TestTheServedAppCarriesTheRule:
    def test_the_app_defines_the_new_helpers_and_constants(self, tmp_path):
        _doc, _w, ap = _served_doc(tmp_path, _spec([_plot()]), _auto_df())
        text = open(ap).read()
        for s in ("def _stata_invsym_keep(", "def _lpoly_rot_constant(",
                  "def _lpoly_rot_detail(", "def _lpoly_rot_float(",
                  "def _lpoly_kept_columns(", "_LPOLY_ROT_GRID =",
                  "_LPOLY_ROT_CONSTANTS ="):
            assert s in text, s
        assert "\n_LPOLY_ROT_C =" not in text and not text.startswith("_LPOLY_ROT_C =")
        assert not [ln for ln in text.splitlines() if ln.startswith("Fraction(")
                    or (ln and not ln[0].isspace() and "= Fraction(" in ln)]
        ns = {"__name__": "_lprot_exec"}
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            exec(compile(text, ap, "exec"), ns)
        r = _row("auto-mpg-weight--biweight-d2-n74")
        x, y, _ = _sample(r)
        h = ns["GlyphMapper"]._default_lpoly_bwidth(x, y, None, 2, "biweight")
        # The served rule is the saved one, bit for bit; against Stata the
        # row's own tier holds (degree 2: 5e-5; measured 2.3e-6, section 11
        # Evidence "auto mpg weight 2.3e-6").
        assert h == dr.GlyphMapper._default_lpoly_bwidth(x, y, None, 2,
                                                         "biweight")
        assert abs(h / 302.44936813331043 - 1) <= r["tol"]
