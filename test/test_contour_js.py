"""
test_contour_js.py -- the saved page refits contour and contourline after
a filter move (WP-31 B4c, section 29).

The defect (measured at 364f9e0): a saved page drew contour and
contourline at build and kept them after any filter move, dimmed and
marked "(grid unfiltered)" (``_dash_stale_kind`` "grid"), while the served
app redrew them from the kept rows; ``_FILTER_JS`` held no contouring code
(BokehJS has none either), so the page could not recompute the layer.

``_FILTER_JS`` now carries twins of S23's surface helpers
(``dash_contour_points``, ``dash_tps_kernel``, ``dash_tps_fit``,
``dash_tps_eval``, ``dash_shepard``, ``dash_contour_grid``,
``dash_contour_surface``; the thin-plate system solved minimum-norm as
``_dash_tps_fit``'s rank-revealing least squares, through the symmetric
eigensolver ``dash_symeig``) and a cutter (``dash_contour_segments``,
``dash_contour_link``, ``dash_contour_rings``, ``dash_contour_lines``,
``dash_contour_bands``) whose level sets are contourpy's, which Bokeh's
``contour_data`` draws on the Python side; and a contour/contourline
branch that rewrites the layer's source after a move within
``_DASH_CONTOUR_EXACT_MAX`` distinct points.  Above the cap the layer is
not registered and keeps the build and the cue (decision D4).

Measured (15oct2026): the JS surface equals the Python one to 1e-11 on the
synthetic and five-point cases and to 7.3e-8 of its range on auto, whose
system's condition is 2.5e17 (S23: two rank-revealing solvers agree there
to about 1e-7); every band's raster and area equal contourpy's on the
fixture's surfaces, on masked grids (interp(none), a cell with one missing
corner drawn as contourpy's corner triangle) and on random surfaces.
"""
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.plotting.contour import contour_data

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import js_runner  # noqa: E402
from js_runner import requires_node, run_js  # noqa: E402
import test_horizontal_moves as hm  # noqa: E402
import test_mode_parity as tp  # noqa: E402
import test_saved_filter_layers as sf  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "contour_truth.json")
with open(_FIXTURE, encoding="utf-8") as _fh:
    _T = json.load(_fh)

_INTERPS = ("thinplatespline", "shepard", "none")


def _f(v):
    """A JS array literal of floats (NaN kept)."""
    return "[" + ",".join("NaN" if not np.isfinite(float(e)) else repr(float(e))
                          for e in np.ravel(np.asarray(v, dtype=float))) + "]"


def _js(code):
    """Run *code* after the page's helpers; it writes JSON with out()."""
    return run_js(js_runner.fit_helpers_js()
                  + "\nconst out = (v) => process.stdout.write(JSON.stringify("
                  "v, (k, x) => (typeof x === 'number' && !Number.isFinite(x))"
                  " ? null : x));\n" + code)


def _nan(a):
    """Nested lists with None for NaN -> float arrays."""
    return np.array([np.nan if v is None else v for v in a], dtype=float)


def _rows(case):
    r = _T["cases"][case]["rows"]
    return np.asarray(r["x"], float), np.asarray(r["y"], float), \
        np.asarray(r["z"], float)


def _js_surface(x, y, z, interp, cap=1000):
    return _js("const S = dash_contour_surface(%s, %s, %s, %s, %d);"
               "out(S === null ? null : {gx: S.gx, gy: S.gy, gz: Array.from(S.gz),"
               " note: S.note, n: S.n});"
               % (_f(x), _f(y), _f(z), json.dumps(interp), cap))


def _even_odd(px, py, X, Y):
    """The points (X, Y) inside the ring (px, py), by the even-odd rule."""
    px, py = np.asarray(px, float), np.asarray(py, float)
    inside = np.zeros(X.shape, bool)
    j = len(px) - 1
    for i in range(len(px)):
        xi, yi, xj, yj = px[i], py[i], px[j], py[j]
        cross = (yi > Y) != (yj > Y)
        with np.errstate(divide="ignore", invalid="ignore"):
            xc = (xj - xi) * (Y - yi) / (yj - yi) + xi
        inside ^= cross & (X < xc)
        j = i
    return inside


def _raster(xs, ys, X, Y):
    """Each point's band index (-1 outside every band); each polygon's
    rings are filled even-odd, as BokehJS fills MultiPolygons."""
    lab = np.full(X.shape, -1)
    for k, (bx, by) in enumerate(zip(xs, ys)):
        m = np.zeros(X.shape, bool)
        for pxs, pys in zip(bx, by):
            for rx, ry in zip(pxs, pys):
                m ^= _even_odd(rx, ry, X, Y)
        lab[m] = k
    return lab


def _area(rx, ry):
    """The shoelace signed area of one ring."""
    rx, ry = np.asarray(rx, float), np.asarray(ry, float)
    return 0.5 * float(np.sum(rx * np.roll(ry, -1) - np.roll(rx, -1) * ry))


def _band_areas(xs, ys):
    return np.array([sum(_area(rx, ry) for pxs, pys in zip(bx, by)
                         for rx, ry in zip(pxs, pys))
                     for bx, by in zip(xs, ys)])


def _grid(gx, gy, n=300):
    xs = np.linspace(min(gx), max(gx), n + 1)
    ys = np.linspace(min(gy), max(gy), n + 1)
    return np.meshgrid((xs[:-1] + xs[1:]) / 2, (ys[:-1] + ys[1:]) / 2)


def _levels(gz, cuts):
    fin = gz[np.isfinite(gz)]
    return [float(fin.min()) - 1.0] + [float(c) for c in cuts] \
        + [float(fin.max()) + 1.0]


def _cuts_off_nodes(case, interp):
    """The fixture's cuts, moved off the node values (D-29g: a node on a
    cut may join rings differently)."""
    return [float(c) + 0.37 for c in
            _T["cases"][case]["shepard" if interp == "none" else interp]
            ["cuts"]]


def _masked_grid(seed):
    """A 9 x 8 grid with a quarter of its nodes missing, so interp(none)
    leaves void cells and cells with one missing corner."""
    rng = np.random.default_rng(seed)
    X0, Y0 = np.meshgrid(np.arange(9.0), np.arange(8.0))
    Z0 = np.sin(X0 / 2) + np.cos(Y0 / 3) + rng.normal(0, 0.2, X0.shape)
    keep = rng.uniform(size=X0.shape) > 0.25
    return X0[keep], Y0[keep], Z0[keep]


# ---------------------------------------------------------------------------
# The surface twins
# ---------------------------------------------------------------------------

@requires_node
class TestTwins:

    @pytest.mark.parametrize("interp", _INTERPS)
    @pytest.mark.parametrize("case", ["auto", "synthetic", "manual5"])
    def test_each_helper(self, case, interp):
        x, y, z = _rows(case)
        want = dr._dash_contour_surface(x, y, z, interp)
        got = _js_surface(x, y, z, interp)
        assert got["gx"] == want["gx"].tolist()
        assert got["gy"] == want["gy"].tolist()
        gz = _nan(got["gz"]).reshape(want["gz"].shape)
        fin = np.isfinite(want["gz"])
        assert (np.isfinite(gz) == fin).all()
        assert got["note"] == want["note"] and got["n"] == want["n_unique"]
        if fin.any():
            err = np.abs(gz[fin] - want["gz"][fin]).max() \
                / max(1.0, np.abs(want["gz"][fin]).max())
            # auto's thin-plate system has condition 2.5e17 (S23): two
            # rank-revealing solves agree to ~1e-7 there (7.3e-8 measured).
            tol = 1e-6 if (case, interp) == ("auto", "thinplatespline") \
                else 1e-9
            assert err <= tol, err
        px, py, pz = dr._dash_contour_points(x, y, z)
        p = _js("out(dash_contour_points(%s, %s, %s));" % (_f(x), _f(y), _f(z)))
        assert (p["x"], p["y"], p["z"]) == (px.tolist(), py.tolist(),
                                            pz.tolist())
        gx, gy = dr._dash_contour_grid(x, y)
        g = _js("out([dash_contour_grid(%s), dash_contour_grid(%s)]);"
                % (_f(x), _f(y)))
        assert g == [gx.tolist(), gy.tolist()]

    def test_kernel_eval_and_shepard(self):
        d2 = [0.0, 1e-12, 0.25, 1.0, 7.5, 3e8]
        k = _js("out(%s.map(dash_tps_kernel));" % _f(d2))
        np.testing.assert_allclose(k, dr._dash_tps_kernel(d2), rtol=1e-14,
                                   atol=0)
        x, y, z = _rows("synthetic")
        w, _note = dr._dash_tps_fit(x, y, z)
        gx, gy = [0.3, 1.7, -2.2], [0.1, 2.9, 0.4]
        e = _js("const w = %s; out([%s].map((u, i) => dash_tps_eval(w, %s, %s,"
                " u, %s[i])));" % (_f(w), ",".join(map(str, gx)), _f(x), _f(y),
                                   _f(gy)))
        np.testing.assert_allclose(e, dr._dash_tps_eval(w, x, y, gx, gy),
                                   rtol=1e-12)
        s = _js("out([dash_shepard(%s, %s, %s, 0.3, 0.1), "
                "dash_shepard(%s, %s, %s, %r, %r)]);"
                % (_f(x), _f(y), _f(z), _f(x), _f(y), _f(z), float(x[3]),
                   float(y[3])))
        assert s[1] == z[3]
        assert s[0] == pytest.approx(
            dr._dash_shepard(x, y, z, [0.3], [0.1])[0], rel=1e-14)

    def test_tps_singular(self):
        # Three collinear points: the trend's columns are dependent, the
        # minimum-norm solve leaves a direction out, as numpy's does.
        x, y, z = [0.0, 1.0, 2.0], [0.0, 1.0, 2.0], [1.0, 3.0, 2.0]
        want, note = dr._dash_tps_fit(x, y, z)
        got = _js("out(dash_tps_fit(%s, %s, %s));" % (_f(x), _f(y), _f(z)))
        assert note == got["note"] == "singular"
        np.testing.assert_allclose(got["w"], want, rtol=1e-9, atol=1e-12)
        # The fixture's smallest system, well conditioned.
        x, y, z = _rows("manual5")
        px, py, pz = dr._dash_contour_points(x, y, z)
        want, note = dr._dash_tps_fit(px, py, pz)
        got = _js("out(dash_tps_fit(%s, %s, %s));" % (_f(px), _f(py), _f(pz)))
        assert got["note"] == note
        np.testing.assert_allclose(got["w"], want, rtol=1e-12, atol=1e-12)

    def test_the_cap(self):
        rng = np.random.default_rng(4)
        x, y, z = rng.uniform(size=(3, 12))
        assert _js_surface(x, y, z, "shepard", cap=11) is None
        assert _js_surface(x, y, z, "shepard", cap=12)["n"] == 12
        deg = _js_surface([1.0, 2.0], [1.0, 2.0], [3.0, 4.0], "shepard")
        assert deg["note"] == "degenerate"
        assert all(v is None for v in deg["gz"])


# ---------------------------------------------------------------------------
# The cutter
# ---------------------------------------------------------------------------

_LINK = """
function surf(gx, gy, gz) {
    return {gx: gx, gy: gy, gz: Float64Array.from(gz), nx: gx.length,
            ny: gy.length};
}
"""


@requires_node
class TestRings:

    def test_every_ring_closes(self):
        """200 seeded random 8 x 8 surfaces x 3 cuts: the region's
        segments link into closed rings only, each segment used once."""
        rng = np.random.default_rng(29)
        cases = []
        for _ in range(200):
            gz = rng.normal(size=64)
            gz[rng.uniform(size=64) < 0.1] = np.nan
            cases.append(gz.tolist())
        res = _js(_LINK + """
const cases = %s;
const g = [0, 1, 2, 3, 4, 5, 6, 7];
let open = 0, segs = 0, used = 0;
for (const gz of cases) for (const c of [-0.5, 0.1, 0.9]) {
    const S = surf(g, g, gz.map(v => v === null ? NaN : v));
    const s = dash_contour_segments(S, c, true);
    const paths = dash_contour_link(s);
    segs += s.length;
    for (const p of paths) { used += p.xs.length - 1; if (!p.closed) open++; }
}
out({open: open, segs: segs, used: used});
""" % json.dumps([[None if not np.isfinite(v) else v for v in c]
                  for c in cases]))
        assert res["open"] == 0 and res["segs"] == res["used"] > 0

    def test_saddles(self):
        """Cases 5 and 10: the cell's mean decides whether the high
        corners join (one band crossing the cell) or are cut apart."""
        res = _js(_LINK + """
const r = [];
for (const gz of [[1, 0, 0, 1], [1, 0, 0, 1.4], [0, 1, 1, 0], [0, 1.4, 1, 0]]) {
    for (const c of [0.45, 0.55]) {
        // corners 00, 10 then 01, 11 (row-major)
        const S = surf([0, 1], [0, 1], gz);
        r.push(dash_contour_rings(S, c).length);
    }
}
out(r);
""")
        # mean 0.5: joined at c 0.45 (one ring), apart at 0.55 (two);
        # mean 0.6: joined at both.
        assert res == [1, 2, 1, 1, 1, 2, 1, 1]

    def test_lines_open_at_the_boundary(self):
        res = _js(_LINK + """
const S = surf([0, 1, 2], [0, 1, 2], [0, 1, 2, 1, 2, 3, 2, 3, 4]);
out(dash_contour_link(dash_contour_segments(S, 1.5, false)));
""")
        [p] = res
        assert p["closed"] is False and len(p["xs"]) == 4
        # The line x + y = 1.5 runs with the high side on its left: from
        # the left edge to the bottom one.
        assert (p["xs"][0], p["ys"][0]) == (0.0, 1.5)
        assert (p["xs"][-1], p["ys"][-1]) == (1.5, 0.0)


@requires_node
class TestOrientation:

    def test_region_on_the_left(self):
        """Every ring has its region on the left: the domain's ring (a
        3 x 3 grid of unit cells' nodes, area +4) and a peak's ring run
        anticlockwise, a pit's hole clockwise."""
        res = _js(_LINK + """
const area = (p) => { let a = 0; for (let i = 0; i + 1 < p.xs.length; i++) a += p.xs[i] * p.ys[i + 1] - p.xs[i + 1] * p.ys[i]; return a / 2; };
const hi = surf([0, 1, 2], [0, 1, 2], [0, 0, 0, 0, 1, 0, 0, 0, 0]);
const lo = surf([0, 1, 2], [0, 1, 2], [1, 1, 1, 1, 0, 1, 1, 1, 1]);
out({dom: dash_contour_rings(hi, -Infinity).map(area),
     peak: dash_contour_rings(hi, 0.5).map(area),
     pit: dash_contour_rings(lo, 0.5).map(area).sort((a, b) => a - b)});
""")
        assert res["dom"] == [4.0]
        assert res["peak"] == [pytest.approx(0.5)]
        # the pit's region is the domain less a diamond: +4 and -0.5
        assert res["pit"] == [pytest.approx(-0.5), 4.0]


@requires_node
class TestMasking:

    @pytest.mark.parametrize("seed", [0, 1, 2])
    @pytest.mark.parametrize("interp", ["none", "shepard"])
    def test_void_cells(self, seed, interp):
        """interp(none) on a grid missing a quarter of its nodes: a void
        cell is in no band, a cell missing one corner draws contourpy's
        corner triangle, and every band's raster and area are
        contourpy's."""
        x, y, z = _masked_grid(seed)
        S = dr._dash_contour_surface(x, y, z, interp)
        lv = _levels(S["gz"], [0.13, 0.71, 1.29])
        cd = contour_data(S["gx"], S["gy"], S["gz"], lv).fill_data
        got = _js("const S = dash_contour_surface(%s, %s, %s, %s, 1000);"
                  "out(dash_contour_bands(S, %s));"
                  % (_f(x), _f(y), _f(z), json.dumps(interp), json.dumps(lv)))
        X, Y = _grid(S["gx"], S["gy"], 400)
        a = _raster(cd.xs, cd.ys, X, Y)
        b = _raster(got["xs"], got["ys"], X, Y)
        assert (a == b).mean() == 1.0
        if interp == "none":
            assert (a == -1).any()
        np.testing.assert_allclose(_band_areas(got["xs"], got["ys"]),
                                   _band_areas(cd.xs, cd.ys), atol=1e-9)


@requires_node
class TestParityWithContourpy:

    @pytest.mark.parametrize("interp", _INTERPS)
    @pytest.mark.parametrize("case", ["auto", "synthetic"])
    def test_bands(self, case, interp):
        x, y, z = _rows(case)
        S = dr._dash_contour_surface(x, y, z, interp)
        if not np.isfinite(S["gz"]).any():
            pytest.skip("no finite node")
        lv = _levels(S["gz"], _cuts_off_nodes(case, interp))
        cd = contour_data(S["gx"], S["gy"], S["gz"], lv).fill_data
        got = _js("const S = dash_contour_surface(%s, %s, %s, %s, 1000);"
                  "out(dash_contour_bands(S, %s));"
                  % (_f(x), _f(y), _f(z), json.dumps(interp), json.dumps(lv)))
        assert got["lower_levels"] == lv[:-1]
        assert got["upper_levels"] == lv[1:]
        assert len(got["xs"]) == len(cd.xs) == len(lv) - 1
        X, Y = _grid(S["gx"], S["gy"])
        agree = (_raster(cd.xs, cd.ys, X, Y)
                 == _raster(got["xs"], got["ys"], X, Y)).mean()
        assert agree >= 0.99, agree
        a, b = _band_areas(cd.xs, cd.ys), _band_areas(got["xs"], got["ys"])
        np.testing.assert_allclose(b, a, rtol=0.01, atol=1e-9 * a.sum())

    @pytest.mark.parametrize("interp", ["thinplatespline", "shepard"])
    @pytest.mark.parametrize("case", ["auto", "synthetic"])
    def test_lines(self, case, interp):
        """Per level, as many vertices as contourpy's lines and each within
        1e-9 of one of theirs (relative to the grid's span; auto's
        thin-plate surface itself differs by 7.3e-8, so 1e-5 there)."""
        x, y, z = _rows(case)
        S = dr._dash_contour_surface(x, y, z, interp)
        cuts = _cuts_off_nodes(case, interp)
        ld = contour_data(S["gx"], S["gy"], S["gz"], cuts,
                          want_fill=False).line_data
        got = _js("const S = dash_contour_surface(%s, %s, %s, %s, 1000);"
                  "out(dash_contour_lines(S, %s));"
                  % (_f(x), _f(y), _f(z), json.dumps(interp),
                     json.dumps(cuts)))
        assert got["levels"] == cuts and len(got["xs"]) == len(cuts)
        span = max(np.ptp(S["gx"]), np.ptp(S["gy"]))
        tol = (1e-5 if (case, interp) == ("auto", "thinplatespline")
               else 1e-9) * span
        for k in range(len(cuts)):
            p = np.column_stack([ld.xs[k], ld.ys[k]])
            p = p[np.isfinite(p).all(axis=1)]
            q = np.column_stack([_nan(got["xs"][k]), _nan(got["ys"][k])])
            q = q[np.isfinite(q).all(axis=1)]
            assert len(q) == len(p), (k, len(q), len(p))
            for u, v in q:
                assert np.min(np.hypot(p[:, 0] - u, p[:, 1] - v)) <= tol


# ---------------------------------------------------------------------------
# The branch
# ---------------------------------------------------------------------------

def _mapped(ptype, df, opts=None):
    """The contour renderer map_contour draws on *df* (x, y, z)."""
    from bokeh.models import ColumnDataSource
    from bokeh.plotting import figure
    gm = dr.GlyphMapper()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cr, _hull = getattr(gm, "map_" + ptype)(
            figure(), ColumnDataSource(df), "y", "x", dict(opts or {}),
            zvar="z")
    return cr


def _frame(n=40, seed=11):
    rng = np.random.default_rng(seed)
    x = np.round(rng.uniform(0, 10, n), 2)
    y = np.round(rng.uniform(0, 10, n), 2)
    return pd.DataFrame({"x": x, "y": y,
                         "z": np.sin(x / 2) + np.cos(y / 3)
                         + np.round(rng.normal(0, 0.1, n), 3)})


def _branch(ac, df):
    return js_runner.run_fit_js_block(
        ac, [], [], data={c: df[c].tolist() for c in ("x", "y", "z")})


@requires_node
class TestTheBranch:

    def test_fill_shapes(self):
        df = _frame()
        cr = _mapped("contour", df, {"ccuts": "0.2 0.9 1.5"})
        ac = cr._dash_agg_config
        assert cr._dash_agg_source is cr.fill_renderer.data_source
        assert ac["part"] == "fill" and "varname" not in ac
        data = _branch(ac, df)
        want = cr.fill_renderer.data_source.data
        assert set(data) == set(want)
        assert data["fill_color"] == list(want["fill_color"])
        # the outer levels follow the surface's extreme nodes (1e-11)
        assert data["lower_levels"] == pytest.approx(
            list(want["lower_levels"]), rel=1e-9)
        assert data["upper_levels"] == pytest.approx(
            list(want["upper_levels"]), rel=1e-9)
        X, Y = _grid(df["x"], df["y"])
        agree = (_raster(want["xs"], want["ys"], X, Y)
                 == _raster(data["xs"], data["ys"], X, Y)).mean()
        assert agree >= 0.999, agree

    def test_line_shapes(self):
        df = _frame()
        cr = _mapped("contourline", df, {"ccuts": "0.2 0.9 1.5",
                                         "colorlines": "colorlines"})
        ac = cr._dash_agg_config
        assert cr._dash_agg_source is cr.line_renderer.data_source
        assert ac["part"] == "line"
        data = _branch(ac, df)
        want = cr.line_renderer.data_source.data
        assert set(data) == set(want)
        assert data["levels"] == [0.2, 0.9, 1.5]
        assert data["line_color"] == list(want["line_color"])
        assert data["line_width"] == list(want["line_width"])
        for k in range(3):
            assert np.isfinite(_nan(data["xs"][k])).sum() \
                == np.isfinite(np.asarray(want["xs"][k], float)).sum()

    def test_horizontal(self):
        df = _frame()
        cr = _mapped("contour", df, {"ccuts": "0.2 0.9 1.5",
                                     "horizontal": "horizontal"})
        data = _branch(cr._dash_agg_config, df)
        want = cr.fill_renderer.data_source.data
        X, Y = _grid(df["y"], df["x"])
        agree = (_raster(want["xs"], want["ys"], X, Y)
                 == _raster(data["xs"], data["ys"], X, Y)).mean()
        assert agree >= 0.999, agree

    def test_cap_leaves_it(self):
        n = dr._DASH_CONTOUR_EXACT_MAX + 1
        rng = np.random.default_rng(7)
        df = pd.DataFrame({"z": rng.normal(size=n), "y": rng.uniform(size=n),
                           "x": rng.uniform(size=n)})
        cr = _mapped("contour", df)
        assert cr._dash_contour_capped is True
        # Not registered: the page keeps the build, marked (D4).
        assert not hasattr(cr, "_dash_agg_config")
        # A config over the cap leaves the source alone.
        small = _frame(12)
        ac = dict(_mapped("contour", small, {"ccuts": "0.5"})
                  ._dash_agg_config, cap=11)
        assert _branch(ac, small) is None


# ---------------------------------------------------------------------------
# The page
# ---------------------------------------------------------------------------

def _page_df(n=60, seed=3):
    """tp._DF's columns over *n* rows, so the parity corpus's filters
    apply; price is cut over the (weight, mpg) plane."""
    rng = np.random.default_rng(seed)
    mpg = np.round(rng.uniform(12, 41, n), 1)
    weight = np.round(rng.uniform(1760, 4840, n), 0)
    return pd.DataFrame({
        "mpg": mpg, "weight": weight,
        "foreign": (rng.uniform(size=n) < 0.5).astype(float),
        "price": np.round(3000 + 2 * weight - 80 * mpg
                          + rng.normal(0, 300, n), 0),
        "rep": rng.integers(1, 6, n).astype(float),
        "when": 15340.0 + np.arange(n)})


def _page_spec(ptype, opts=None, filt=None):
    return tp._spec([{"type": ptype, "zvar": "price", "yvar": "mpg",
                      "xvar": "weight", "options": dict(opts or {})}],
                    {"filter": filt or sf._MOVES[0][1]})


def _layer_data(figs, part):
    [cr] = [r for r in figs[0].renderers
            if type(r).__name__ == "ContourRenderer"]
    return (cr.fill_renderer if part == "fill"
            else cr.line_renderer).data_source.data


@requires_node
class TestWholePage:

    @pytest.mark.parametrize("move", sf._MOVES, ids=[m[0] for m in sf._MOVES])
    @pytest.mark.parametrize("ptype", ["contour", "contourline"])
    def test_move_refits(self, ptype, move):
        """The saved page after the move draws what the page of the kept
        rows draws (the Python oracle, contourpy's cut): the same bands
        to 99.9% of a raster, or the same lines, and no stale mark."""
        _label, filt, action, oracle = move
        df = _page_df()
        spec = _page_spec(ptype, {"ccuts": "6000 8000 10000"}, filt)
        r, after = hm._saved_moved(spec, action, df)
        kept = hm._kept(spec, oracle, "saved", df=df)
        part = "fill" if ptype == "contour" else "line"
        a, b = _layer_data(after, part), _layer_data(kept, part)
        if part == "fill":
            assert len(a["xs"]) == len(b["xs"]) == 4
            assert list(a["fill_color"]) == list(b["fill_color"])
            sub = df.query(oracle)
            X, Y = _grid(sub["weight"], sub["mpg"])
            agree = (_raster(a["xs"], a["ys"], X, Y)
                     == _raster(b["xs"], b["ys"], X, Y)).mean()
            assert agree >= 0.999, agree
            np.testing.assert_allclose(
                _band_areas(a["xs"], a["ys"]), _band_areas(b["xs"], b["ys"]),
                rtol=0.01, atol=1e-6)
        else:
            assert list(a["levels"]) == list(b["levels"])
            for k in range(len(b["xs"])):
                assert np.isfinite(_nan(a["xs"][k])).sum() \
                    == np.isfinite(np.asarray(b["xs"][k], float)).sum()
        assert not r.frozen_layer_registry
        st = r.filter_callbacks[0].args.get("stale_status")
        assert st is None or st.visible is not True


class TestStale:

    def test_kind_and_tag(self, tmp_path):
        assert dr._dash_stale_kind("contour", {}) is None
        assert dr._dash_stale_kind("contourline", {}) is None
        # within the cap: refit, not tagged
        r = hm.jo._saved(_page_spec("contour"), _page_df(), labels=True)
        assert not r.frozen_layer_registry
        # above it: tagged frozen with the grid kind
        n = dr._DASH_CONTOUR_EXACT_MAX + 1
        big = _page_df(n, seed=5)
        big["weight"] = big["weight"] + np.arange(n) * 1e-3
        r = hm.jo._saved(_page_spec("contour"), big, labels=True)
        [(tag, rends)] = [e for g in r.frozen_layer_registry.values()
                          for e in g]
        assert tag["kind"] == "grid" and tag["type"] == "contour"
        assert tag["vars"] == ["price", "mpg", "weight"]


class TestRegistration:

    @pytest.mark.parametrize("ptype,part", [("contour", "fill"),
                                            ("contourline", "line")])
    def test_one_entry(self, ptype, part):
        r = hm.jo._saved(_page_spec(ptype), _page_df(), labels=True)
        entries = [e for g in r.agg_source_registry.values() for e in g]
        [(src, cfg)] = entries
        assert cfg["type"] == ptype and cfg["part"] == part
        assert {"xvar", "yvar", "zvar", "cuts", "interp", "cap", "lo", "hi",
                "horizontal", "extra"} <= set(cfg)
        assert (cfg["xvar"], cfg["yvar"], cfg["zvar"]) == \
            ("weight", "mpg", "price")
        json.dumps(cfg, allow_nan=False)


class TestHelp:

    def test_sentences(self):
        with open(os.path.join(_HERE, "..", "dash.sthlp"),
                  encoding="utf-8") as fh:
            text = " ".join(fh.read().split())
        assert ("a saved page recomputes the layer after a filter move up "
                "to 1,000 distinct points") in text
        assert "the saved page does not recompute the layer" not in text


# ---------------------------------------------------------------------------
# A date on the plane (WP-31 B4c): twoway fits the surface in the
# variable's Stata units (days for %td, months for %tm); the page draws it
# on the date axis.
# ---------------------------------------------------------------------------

def _date_df(kind, n=40, seed=8):
    df = _page_df(n, seed)
    rng = np.random.default_rng(seed)
    if kind == "td":
        df["when"] = 15340.0 + np.round(rng.uniform(0, 400, n))
    else:
        df["when"] = 600.0 + np.round(rng.uniform(0, 48, n))
    return df


def _date_spec(kind, ptype, filt):
    spec = tp._spec([{"type": ptype, "zvar": "price", "yvar": "mpg",
                      "xvar": "when",
                      "options": {"ccuts": "6000 8000 10000"}}],
                    {"filter": filt, "formats": {"when": "%" + kind}})
    return spec


def _units_to_axis(v, kind):
    return np.asarray(dr._dash_units_to_axis(list(v), kind), float)


def _poly_points(d):
    """Every vertex of a fill source, as (x, y) arrays."""
    xs = [v for band in d["xs"] for poly in band for ring in poly for v in ring]
    ys = [v for band in d["ys"] for poly in band for ring in poly for v in ring]
    return np.asarray(xs, float), np.asarray(ys, float)


@requires_node
class TestDates:

    @pytest.mark.parametrize("kind", ["td", "tm"])
    def test_the_build_fits_in_stata_units(self, kind):
        """The built bands are contourpy's cut of the surface twoway fits
        in the date's own units, drawn at the axis's positions."""
        df = _date_df(kind)
        spec = _date_spec(kind, "contour", sf._MOVES[0][1])
        figs = hm.jo._saved_figs(hm.jo._saved(spec, df, labels=True))
        d = _layer_data(figs, "fill")
        S = dr._dash_contour_surface(df["when"], df["mpg"], df["price"])
        gx = _units_to_axis(S["gx"], kind)
        lv = _levels(S["gz"], [6000.0, 8000.0, 10000.0])
        cd = contour_data(gx, S["gy"], S["gz"], lv).fill_data
        X, Y = _grid(gx, S["gy"])
        agree = (_raster(cd.xs, cd.ys, X, Y)
                 == _raster(d["xs"], d["ys"], X, Y)).mean()
        assert agree >= 0.999, agree

    @pytest.mark.parametrize("ptype", ["contour", "contourline"])
    @pytest.mark.parametrize("kind", ["td", "tm"])
    def test_a_move_matches_the_served_app_and_the_build(self, kind, ptype):
        _label, filt, action, oracle = sf._MOVES[0]
        df = _date_df(kind)
        spec = _date_spec(kind, ptype, filt)
        _r, saved = hm._saved_moved(spec, action, df)
        _d, served = hm._served_moved(spec, action, df)
        kept = hm._kept(spec, oracle, "saved", df=df)
        part = "fill" if ptype == "contour" else "line"
        a, s, k = (_layer_data(f, part) for f in (saved, served, kept))
        if part == "fill":
            px, py = _poly_points(k)
            X, Y = _grid(px, py)
            want = _raster(k["xs"], k["ys"], X, Y)
            for got in (a, s):
                agree = (_raster(got["xs"], got["ys"], X, Y) == want).mean()
                assert agree >= 0.999, agree
            assert px.min() > 1e10      # epoch milliseconds on the axis
        else:
            for got in (a, s):
                for j in range(len(k["xs"])):
                    q = _nan(got["xs"][j])
                    p = np.asarray(k["xs"][j], float)
                    assert np.isfinite(q).sum() == np.isfinite(p).sum()
                    p = np.sort(p[np.isfinite(p)])
                    # within 1e-6 of the axis span: the twins' thin-plate
                    # surfaces differ by round-off (TestTwins)
                    np.testing.assert_allclose(
                        np.sort(q[np.isfinite(q)]), p, rtol=0,
                        atol=1e-6 * (np.ptp(p) if p.size else 1.0))


def _zdate_df(n=40, seed=9):
    df = _page_df(n, seed)
    df["zd"] = 14610.0 + 3.0 * df["price"]          # td(01jan2000) + 3 price
    return df


def _zdate_spec(ptype, filt):
    return tp._spec([{"type": ptype, "zvar": "zd", "yvar": "mpg",
                      "xvar": "weight", "options": {}}],
                    {"filter": filt, "formats": {"zd": "%td"}})


@requires_node
class TestDateZ:
    """twoway cuts a %td z in days and keys it in %8.0gc (measured
    15oct2026: twoway contour zd mpg weight on auto with zd =
    td(01jan2000) + 3*price cuts at 30000 40000 50000, ticks 20000(10000)
    60000, labelled "20,000" ... "60,000"; test_wp31_truth.cscript U29-8)."""

    def test_the_build_cuts_in_days(self):
        df = _zdate_df()
        figs = hm.jo._saved_figs(hm.jo._saved(_zdate_spec("contour", sf._MOVES[0][1]), df,
                                              labels=True))
        [cr] = [r for r in figs[0].renderers
                if type(r).__name__ == "ContourRenderer"]
        zmin, zmax = float(df["zd"].min()), float(df["zd"].max())
        cuts, ticks = dr._dash_contour_cuts({}, zmin, zmax)
        assert list(cr.levels[1:-1]) == pytest.approx(cuts)
        # Flipped (WP-42 CV-3): the key was a ContourColorBar; twoway draws
        # swatches beside a z axis, the figure's key cell, ticked and
        # labelled the same, in days and %8.0gc.
        kc = figs[0]._dash_key_cell._dash_keycell
        lo, hi = kc["axis"].bounds
        assert list(kc["ticker"].ticks) == pytest.approx(
            [t for t in ticks if lo <= t <= hi])
        ovr = dict(kc["axis"].major_label_overrides or {})
        assert ovr and all(v == dr._dash_fmt_text(float(t), "%8.0gc")
                           for t, v in ovr.items())

    @pytest.mark.parametrize("ptype", ["contour", "contourline"])
    def test_a_move_matches_the_served_app_and_the_build(self, ptype):
        _label, filt, action, oracle = sf._MOVES[0]
        df = _zdate_df()
        spec = _zdate_spec(ptype, filt)
        _r, saved = hm._saved_moved(spec, action, df)
        _d, served = hm._served_moved(spec, action, df)
        kept = hm._kept(spec, oracle, "saved", df=df)
        part = "fill" if ptype == "contour" else "line"
        a, s, k = (_layer_data(f, part) for f in (saved, served, kept))
        key = "lower_levels" if part == "fill" else "levels"
        sub = df.query(oracle)
        for got in (a, s):
            assert list(got[key])[1:] == pytest.approx(list(k[key])[1:],
                                                       rel=1e-9)
        if part == "fill":
            X, Y = _grid(sub["weight"], sub["mpg"])
            want = _raster(k["xs"], k["ys"], X, Y)
            for got in (a, s):
                assert (_raster(got["xs"], got["ys"], X, Y)
                        == want).mean() >= 0.999
