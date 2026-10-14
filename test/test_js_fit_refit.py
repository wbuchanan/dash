"""WP-31 F1a: lfit and qfit refit on the saved page; the JS prelude and
helpers every later estimator port uses.

GAPS3 F1: the saved page recomputed only histogram and kdensity after a
filter move; an lfit or qfit line stayed the build's regression, dimmed and
keyed "(unfiltered)", while the served app refitted it from the kept rows.
Measured at the base on ``test_mode_parity._DF`` with the dropdown moved to
Foreign: the saved lfit still started at 29.1052 (``regress mpg weight`` on
every row), the served one at 29.9174 (``if foreign == 1``).

The oracle is the Python mapper (``map_lfit``/``map_qfit``), itself pinned
to twoway by test_statistical_truth.py and the U10 truth block, run on the
same rows; and the served app after the same move.
"""
import json
import math
import os
import sys
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.models import ColumnDataSource, GlyphRenderer, Line
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import js_runner  # noqa: E402
from js_runner import requires_node, run_js  # noqa: E402
from test_mode_parity import (_DF, _fire, _served, _spec,  # noqa: E402
                              _widgets_of)
from test_saved_filter_layers import _MOVES, _move, _render  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_E = float(dr._STATA_EPOCH_UNIX_MS)
#: The D-10.a keys every fit config carries.
_KEYS = {"type", "xvar", "yvar", "wvar", "wtype", "wneg", "xdatekind",
         "ydatekind", "wdatekind", "xaxiskind", "yaxiskind", "cols", "n",
         "range"}

_RNG = np.random.default_rng(20261013)
#: Thirty rows with a spread x, a noisy quadratic y and positive integer
#: weights, for the branch twins.
_FRAME = pd.DataFrame({
    "x": np.round(_RNG.uniform(1500.0, 5000.0, 30), 1),
    "w": _RNG.integers(1, 6, 30).astype(float),
})
_FRAME["y"] = (40.0 - 0.006 * _FRAME["x"] + 6e-7 * _FRAME["x"] ** 2
               + np.round(_RNG.normal(0.0, 2.0, 30), 2))


def _gm(date_vars=None):
    gm = dr.GlyphMapper()
    gm.date_vars = dict(date_vars or {})
    return gm


def _map(ptype, df, opts=None, xvar="x", yvar="y", date_vars=None):
    """The mapper's renderer for *ptype* on *df*, warnings silenced."""
    gm = _gm(date_vars)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return getattr(gm, "map_" + ptype)(
            figure(), ColumnDataSource(df), yvar, xvar, dict(opts or {}))


def _fit_js():
    return js_runner.fit_helpers_js()


def _js(expr):
    """Evaluate the JS *expr* after the fit helpers; JSON back."""
    return run_js(_fit_js() + "\nprocess.stdout.write(JSON.stringify("
                  + expr + "));")


def _nan(v):
    return np.array([np.nan if e is None else e for e in v], dtype=float)


# ---------------------------------------------------------------------------
# The config the mappers tag
# ---------------------------------------------------------------------------

class TestTheConfig:
    def test_lfit_config_keys(self):
        r = _map("lfit", _FRAME)
        cfg = r._dash_agg_config
        assert set(cfg) == _KEYS
        assert r._dash_agg_source is r.data_source
        assert hasattr(r, "_dash_agg_rows")
        assert cfg["type"] == "lfit"
        assert (cfg["xvar"], cfg["yvar"]) == ("x", "y")
        assert cfg["wvar"] is None and cfg["wtype"] is None
        assert cfg["cols"] == ["x", "y"] and cfg["n"] == 100
        assert cfg["range"] is None and cfg["wneg"] == "drop"
        json.dumps(cfg, allow_nan=False)

    def test_qfit_config_keys(self):
        r = _map("qfit", _FRAME, {"weight": "aweight", "wexp": "w",
                                  "range": ". 3000", "n": "3"})
        cfg = r._dash_agg_config
        assert set(cfg) == _KEYS
        assert cfg["type"] == "qfit"
        assert (cfg["wvar"], cfg["wtype"]) == ("w", "aw")
        # qfit, n(3) plots 100 (twoway_qfit_parse.class).
        assert cfg["n"] == 100
        assert cfg["range"] == [None, 3000.0]

    def test_an_empty_layer_is_tagged(self):
        r = _map("lfit", _FRAME.iloc[:1])
        assert len(r.data_source.data["x"]) == 0
        assert r._dash_agg_config["type"] == "lfit"
        assert r._dash_agg_source is r.data_source

    def test_a_stair_lfit_records_three_points_and_its_join(self):
        cfg = _map("lfit", _FRAME, {"connect": "stairstep"})._dash_agg_config
        assert cfg["n"] == 3 and cfg["join"] == {"style": "stairstep"}

    def test_a_refused_weight_is_not_read(self):
        cfg = _map("lfit", _FRAME, {"weight": "iweight",
                                    "wexp": "w"})._dash_agg_config
        assert cfg["wvar"] is None and cfg["wtype"] is None

    def test_a_recast_layer_is_not_tagged(self):
        r = _map("lfit", _FRAME, {"recast": "scatter"})
        assert not hasattr(r, "_dash_agg_config")

    def test_date_kinds(self):
        df = pd.DataFrame({"y": _DF["mpg"],
                           "d": _DF["when"] * 86_400_000.0 + _E})
        cfg = _map("lfit", df, xvar="d",
                   date_vars={"d": "td"})._dash_agg_config
        assert (cfg["xdatekind"], cfg["xaxiskind"]) == ("td", "td")
        assert cfg["ydatekind"] is None and cfg["yaxiskind"] is None
        # A date sharing a numeric axis is drawn in its Stata values.
        r = _render(_spec([plot_for("scatter"),
                           plot_for("lfit", yvar="mpg", xvar="when")],
                          {"formats": {"when": "%td"}}))
        cfg = [x for x in r.figures["g1"].renderers
               if hasattr(x, "_dash_agg_config")][0]._dash_agg_config
        assert (cfg["xdatekind"], cfg["xaxiskind"]) == ("td", None)


class TestStaleKind:
    def test_lfit_and_qfit_are_refit(self):
        assert dr._dash_stale_kind("lfit", {}) is None
        assert dr._dash_stale_kind("qfit", {}) is None
        # A recast fit is not refitted (GAPS3 C16) and keeps the cue.
        assert dr._dash_stale_kind("lfit", {"recast": "scatter"}) == "fit"
        # lowess is refitted too (WP-31 F1c): TestStaleKind
        # test_lowess_is_refit.
        for t in ("lfitci", "qfitci", "fpfit", "fpfitci", "lpoly",
                  "lpolyci", "mband", "mspline"):
            assert dr._dash_stale_kind(t, {}) == "fit", t


# ---------------------------------------------------------------------------
# The helpers, under node
# ---------------------------------------------------------------------------

_AC = {"xvar": "x", "yvar": "y", "wvar": None, "wtype": None,
       "wneg": "drop", "xdatekind": None, "ydatekind": None,
       "wdatekind": None}


@requires_node
class TestFitRows:
    def test_joint_drop(self):
        got = js_runner.run_fit_rows(_AC, {"x": [1, None, 3, 4, float("nan")],
                                           "y": [1, 2, None, 4, 5]})
        assert got == {"x": [1, 4], "y": [1, 4], "w": None}

    def test_positive_weights(self):
        ac = dict(_AC, wvar="w", wtype="aw")
        got = js_runner.run_fit_rows(ac, {"x": [1, 2, 3, 4, 5],
                                          "y": [1, 2, 3, 4, 5],
                                          "w": [1, 0, -1, None, 2]})
        assert got == {"x": [1, 5], "y": [1, 5], "w": [1, 2]}

    def test_a_layer_that_draws_nothing_on_a_weight_gets_no_rows(self):
        # A non-integer fweight: regress cannot use it, twoway draws
        # nothing (_layer_weight_values_state "nonint").
        ac = dict(_AC, wvar="w", wtype="fw")
        got = js_runner.run_fit_rows(ac, {"x": [1, 2, 3], "y": [1, 2, 3],
                                          "w": [1, 1.5, 2]})
        assert got == {"x": [], "y": [], "w": []}
        # A negative weight on a layer twoway refuses it for (r(402)).
        ac = dict(_AC, wvar="w", wtype="aw", wneg="empty")
        got = js_runner.run_fit_rows(ac, {"x": [1, 2, 3], "y": [1, 2, 3],
                                          "w": [1, -1, 2]})
        assert got == {"x": [], "y": [], "w": []}

    def test_dates(self):
        ac = dict(_AC, xdatekind="td")
        ms = [15340 * 86_400_000.0 + _E, 15341.5 * 86_400_000.0 + _E]
        got = js_runner.run_fit_rows(ac, {"x": ms, "y": [1, 2]})
        np.testing.assert_allclose(got["x"], [15340.0, 15341.5])

    def test_member_ids(self):
        got = js_runner.run_fit_rows(_AC, {"x": [1, 2, 3, 4],
                                           "y": [5, 6, 7, 8]}, keep=[1, 3])
        assert got == {"x": [2, 4], "y": [6, 8], "w": None}

    def test_missing_column(self):
        assert js_runner.run_fit_rows(_AC, {"x": [1, 2]}) is None
        ac = dict(_AC, wvar="w", wtype="aw")
        assert js_runner.run_fit_rows(ac, {"x": [1], "y": [1]}) is None


_GRIDS = [
    ("n(2)", {"n": "2"}), ("n(3)", {"n": "3"}), ("default", {}),
    ("n(1)", {"n": "1"}), ("range(1500 5500)", {"range": "1500 5500"}),
    ("range(6000 1000) n(7)", {"range": "6000 1000", "n": "7"}),
    ("range(. 3000)", {"range": ". 3000"}),
    ("range(. 1000)", {"range": ". 1000"}),
    ("range(4000 .)", {"range": "4000 ."}),
]


@requires_node
class TestFitGrid:
    @pytest.mark.parametrize("opts", [g[1] for g in _GRIDS],
                             ids=[g[0] for g in _GRIDS])
    def test_matches_python(self, opts):
        cfg = _map("lfit", _FRAME, opts)._dash_agg_config
        x = _FRAME["x"].tolist()
        got = _js("dash_fit_grid(%s, %s, %s)" % (
            json.dumps(x), json.dumps(cfg["n"]), json.dumps(cfg["range"])))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            want = dr._fit_grid(np.asarray(x), opts, "lfit")
        np.testing.assert_array_equal(got, want)

    def test_a_constant_x(self):
        got = _js("dash_fit_grid([2500, 2500, 2500], 5, null)")
        assert got == [2500.0] * 5


_KINDS = ["td", "tc", "tC", "tw", "tm", "tq", "th", "ty"]


@requires_node
class TestAxisValueOf:
    @pytest.mark.parametrize("kind", _KINDS)
    def test_every_kind(self, kind):
        base = {"ty": 2000.0, "tc": 1.3e12, "tC": 1.3e12}.get(kind, 500.0)
        vals = [base + d for d in (-3, -0.5, 0, 0.25, 0.5, 1, 51, 51.5, 52)]
        vals += [1e9, -1e9, 99.0, 9999.5, 10000.0]
        got = _nan(_js("%s.map(v => dash_axis_value_of(v, %s))" % (
            json.dumps(vals), json.dumps(kind))))
        want = dr._dash_units_to_axis(np.asarray(vals), kind)
        np.testing.assert_allclose(got, want, rtol=0, atol=1e-3,
                                   equal_nan=True)

    def test_no_kind_is_the_value(self):
        assert _js("[dash_axis_value_of(3.5, null), "
                   "dash_axis_value_of(NaN, null)]") == [3.5, None]


def _designs():
    mpg = [22.0, 17.0, 22.0, 20.0, 15.0, 18.0, 26.0, 20.0]
    w = [3.0, 3.0, 4.0, 2.0, 5.0, 3.0, 4.0, 1.0]
    one = np.arange(1.0, 9.0)
    return [
        ("unweighted", one, mpg, None, None),
        ("aw", one, mpg, w, "aw"),
        ("fw", one, mpg, w, "fw"),
        ("pw", one, mpg, w, "pw"),
        ("constant x", np.full(8, 2.0), mpg, None, None),
        ("two values 1 3", np.array([1.0, 3.0] * 4), mpg, None, None),
        ("two values -1 2", np.array([-1.0, 2.0] * 4), mpg, None, None),
        ("1e7 offset", 1e7 + one, mpg, None, None),
        ("5-minute tc", 1.3e12 + 300000.0 * np.arange(8.0), mpg, w, "aw"),
    ]


def _lfit_design(x, xg):
    mu = float(np.mean(x))
    return (np.column_stack([np.ones_like(x), x - mu]),
            np.column_stack([np.ones_like(xg), xg - mu]))


@requires_node
class TestWlsTwin:
    @pytest.mark.parametrize("kind", ["lfit", "qfit"])
    @pytest.mark.parametrize("case", _designs(), ids=[d[0] for d in
                                                      _designs()])
    def test_design(self, case, kind):
        _, x, y, w, wt = case
        x = np.asarray(x, dtype=float)
        xg = np.linspace(x.min(), x.max(), 7)
        X, Xg = (_lfit_design(x, xg) if kind == "lfit"
                 else dr._qfit_design(x, xg))
        fit = dr._dash_wls(X, np.asarray(y), None if w is None
                           else np.asarray(w), wt)
        got = _js("(() => { const f = dash_wls(%s, %s, %s, %s); "
                  "return {beta: f.beta, df: f.df, s2: f.s2, "
                  "stdp: dash_fitci_se(%s, f, 'stdp'), "
                  "stdf: dash_fitci_se(%s, f, 'stdf')}; })()" % (
                      json.dumps(X.tolist()), json.dumps(list(y)),
                      json.dumps(w), json.dumps(wt),
                      json.dumps(Xg.tolist()), json.dumps(Xg.tolist())))
        np.testing.assert_allclose(got["beta"], fit["beta"], rtol=1e-9,
                                   atol=1e-12)
        assert got["df"] == fit["df"]
        np.testing.assert_allclose(got["s2"], fit["s2"], rtol=1e-9)
        for std in ("stdp", "stdf"):
            np.testing.assert_allclose(
                got[std], dr._dash_fitci_se(Xg, fit, std), rtol=1e-8,
                atol=1e-12)


@requires_node
class TestTPpf:
    @pytest.mark.parametrize("df", [1, 2, 5, 30, 72, 1e4])
    @pytest.mark.parametrize("p", [0.75, 0.95, 0.975, 0.995])
    def test_matches_python(self, p, df):
        got = _js("dash_t_ppf(%r, %r)" % (p, df))
        # At df 1e4 both twins difference lgamma near 5000, whose last bit
        # is 7e-12: they agree to 2e-11 there, to 1e-15 below.
        rel = 1e-10 if df >= 1e4 else 1e-12
        assert got == pytest.approx(dr._t_ppf(p, df), rel=rel)

    def test_lgamma(self):
        xs = [0.5, 1.0, 1.5, 2.5, 5.0, 10.5, 36.0, 500.5, 5000.0, 5e4]
        got = _js("%s.map(dash_lgamma)" % json.dumps(xs))
        for x, g in zip(xs, got):
            assert g == pytest.approx(math.lgamma(x), rel=1e-13, abs=1e-14)


@requires_node
class TestSolve:
    def test_singular(self):
        assert _js("dash_solve([[1, 2], [2, 4]], [1, 2])") is None

    def test_pivot(self):
        A = [[0.0, 2.0, 1.0], [1.0, 1.0, 1.0], [2.0, 1.0, 3.0]]
        b = [5.0, 6.0, 13.0]
        got = _js("dash_solve(%s, %s)" % (json.dumps(A), json.dumps(b)))
        np.testing.assert_allclose(got, np.linalg.solve(A, b), rtol=1e-13)


# ---------------------------------------------------------------------------
# The two branches against the Python mappers
# ---------------------------------------------------------------------------

def _rows(df, opts, xvar="x", yvar="y"):
    """x, y, w in Stata units as the mapper fits them."""
    gm = _gm()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        x, y, w, _wt = gm._layer_units(ColumnDataSource(df), None, opts,
                                       "lfit", xvar, yvar)
    return x, y, w


def _branch_case(ptype, df, opts):
    r = _map(ptype, df, opts)
    x, y, w = _rows(df, opts)
    got = js_runner.run_fit_js_block(r._dash_agg_config, x, y, w)
    data = r.data_source.data
    for c in ("x", "y"):
        np.testing.assert_allclose(_nan(got[c]), np.asarray(data[c], float),
                                   rtol=1e-9, atol=1e-12, equal_nan=True)
    return got


_AW = {"weight": "aweight", "wexp": "w"}
_LFIT_CASES = [
    ("unweighted", _FRAME, {}),
    ("aw", _FRAME, _AW),
    ("fw", _FRAME, {"weight": "fweight", "wexp": "w"}),
    ("pw", _FRAME, {"weight": "pweight", "wexp": "w"}),
    ("constant x", _FRAME.assign(x=2500.0), {}),
    ("constant x aw", _FRAME.assign(x=2500.0), _AW),
    ("one row", _FRAME.iloc[:1], {}),
    ("two rows", _FRAME.iloc[:2], {}),
    ("n(3)", _FRAME, {"n": "3"}),
    ("n(1)", _FRAME, {"n": "1"}),
    ("range(1500 5500)", _FRAME, {"range": "1500 5500"}),
    ("range(. 3000)", _FRAME, {"range": ". 3000"}),
    ("stairstep", _FRAME, {"connect": "stairstep"}),
    ("1e7 offset", _FRAME.assign(x=_FRAME["x"] + 1e7), {}),
]


@requires_node
class TestLfitBranch:
    @pytest.mark.parametrize("df,opts", [c[1:] for c in _LFIT_CASES],
                             ids=[c[0] for c in _LFIT_CASES])
    def test_matches_python(self, df, opts):
        _branch_case("lfit", df, opts)

    def test_one_row_writes_empty_columns(self):
        got = _branch_case("lfit", _FRAME.iloc[:1], {})
        assert got == {"x": [], "y": []}


_QFIT_CASES = [
    ("default", _FRAME, {}),
    ("two values, x squared kept", _FRAME.assign(
        x=np.where(np.arange(30) % 2, 1.0, 3.0)), {}),
    ("two values, x kept", _FRAME.assign(
        x=np.where(np.arange(30) % 2, -1.0, 2.0)), {}),
    ("n(3) plots 100", _FRAME, {"n": "3"}),
    ("aw", _FRAME, _AW),
    ("pw range(1000 6000) n(7)", _FRAME,
     {"weight": "pweight", "wexp": "w", "range": "1000 6000", "n": "7"}),
    ("one row", _FRAME.iloc[:1], {}),
    ("two rows", _FRAME.iloc[:2], {}),
    ("constant x", _FRAME.assign(x=2500.0), {}),
]


@requires_node
class TestQfitBranch:
    @pytest.mark.parametrize("df,opts", [c[1:] for c in _QFIT_CASES],
                             ids=[c[0] for c in _QFIT_CASES])
    def test_matches_python(self, df, opts):
        _branch_case("qfit", df, opts)


# ---------------------------------------------------------------------------
# The saved page after a move against the served app
# ---------------------------------------------------------------------------

def _fit_data(renderers, ptype=None):
    """x and y of the one fit line among *renderers*."""
    lines = [r for r in renderers if isinstance(r, GlyphRenderer)
             and isinstance(r.glyph, Line)]
    assert len(lines) == 1, f"{len(lines)} lines"
    d = lines[0].data_source.data
    # A lowess line's columns are x_lw and y_lw (WP-31 F1c).
    cx, cy = ("x_lw", "y_lw") if "x_lw" in d else ("x", "y")
    return (np.asarray(d[cx], dtype=float), np.asarray(d[cy], dtype=float))


def _served_fit_after(spec, action):
    doc, _ = _served(spec)
    kind, want = action
    w = [m for m in _widgets_of(doc) if type(m).__name__ == kind][0]
    if kind == "Select":
        want = [v for v, lab in w.options if lab == want][0]
    _fire(w, want)
    rends = [m for m in doc.models if isinstance(m, GlyphRenderer)]
    return _fit_data(rends)


_REFIT_SPECS = [
    ("lfit", [plot_for("scatter"), plot_for("lfit")]),
    ("qfit", [plot_for("scatter"), plot_for("qfit")]),
    ("lfit aw", [plot_for("lfit", {"weight": "aweight", "wexp": "rep"})]),
    ("qfit range(. 3000) n(7)",
     [plot_for("qfit", {"range": ". 3000", "n": "7"})]),
    # WP-31 F1c: lowess re-smooths the kept rows.
    ("lowess", [plot_for("scatter"), plot_for("lowess")]),
    ("lowess bwidth(.4) mean",
     [plot_for("lowess", {"bwidth": ".4", "mean": "mean"})]),
    ("lowess noweight adjust",
     [plot_for("lowess", {"noweight": "noweight", "adjust": "adjust"})]),
]


@requires_node
class TestTheSavedPageRefits:
    @pytest.mark.parametrize("move", _MOVES, ids=[m[0] for m in _MOVES])
    @pytest.mark.parametrize("plots", [s[1] for s in _REFIT_SPECS],
                             ids=[s[0] for s in _REFIT_SPECS])
    def test_saved_equals_served(self, plots, move):
        _, filt, action, _oracle = move
        spec = _spec(plots, {"filter": filt})
        r = _render(spec)
        built = _fit_data(r.figures["g1"].renderers)
        _move(r, action)
        sx, sy = _fit_data(r.figures["g1"].renderers)
        vx, vy = _served_fit_after(spec, action)
        np.testing.assert_allclose(sx, vx, rtol=1e-9, atol=1e-9)
        np.testing.assert_allclose(sy, vy, rtol=1e-9, atol=1e-9)
        assert (built[1].shape != sy.shape
                or not np.allclose(built[1], sy)), "the move changed nothing"

    def test_a_move_back_redraws_the_build(self):
        spec = _spec([plot_for("scatter"), plot_for("lfit")],
                     {"filter": _MOVES[0][1]})
        r = _render(spec)
        built = _fit_data(r.figures["g1"].renderers)
        _move(r, _MOVES[0][2])
        w = [x for x in r.filter_widgets if type(x).__name__ == "Select"][0]
        w.value = getattr(w, "_dash_sentinel", "__all__")
        from test_saved_filter_layers import _run
        _run(r.filter_callbacks[0].code, r.filter_callbacks[0].args)
        back = _fit_data(r.figures["g1"].renderers)
        np.testing.assert_allclose(back[1], built[1], rtol=1e-9)

    def test_a_move_leaving_one_row_empties_the_line(self):
        spec = _spec([plot_for("scatter"), plot_for("lfit")],
                     {"filter": "price, type(slider)"})
        r = _render(spec)
        _move(r, ("Slider", 11385.0))
        x, y = _fit_data(r.figures["g1"].renderers)
        assert len(x) == 0 and len(y) == 0


@requires_node
class TestADateFitRefits:
    def test_td_x_round_trips(self):
        spec = _spec([plot_for("lfit", yvar="mpg", xvar="when")],
                     {"filter": _MOVES[1][1], "formats": {"when": "%td"}})
        r = _render(spec)
        cfg = [x for x in r.figures["g1"].renderers
               if hasattr(x, "_dash_agg_config")][0]._dash_agg_config
        assert cfg["xaxiskind"] == "td"
        _move(r, _MOVES[1][2])
        sx, sy = _fit_data(r.figures["g1"].renderers)
        vx, vy = _served_fit_after(spec, _MOVES[1][2])
        np.testing.assert_allclose(sx, vx, rtol=0, atol=1.0)
        np.testing.assert_allclose(sy, vy, rtol=1e-9)
        # Drawn in epoch milliseconds, over the kept rows' days.
        kept = _DF.query("price >= 4500 & price <= 11385")["when"]
        assert sx[0] == pytest.approx(kept.min() * 86_400_000.0 + _E)
        assert sx[-1] == pytest.approx(kept.max() * 86_400_000.0 + _E)


class TestThePageSize:
    def test_a_fit_config_is_small(self):
        r = _render(_spec([plot_for("scatter"), plot_for(
            "qfit", {"weight": "aweight", "wexp": "rep",
                     "range": "1000 6000", "connect": "stairstep"})]))
        cfgs = [c for _s, c in r.agg_source_registry["g1"]]
        assert cfgs and all(len(json.dumps(c)) < 600 for c in cfgs)


# ---- WP-31 F1c: lowess ----
#
# GAPS3 F1c: a lowess on the saved page kept the build's smooth after a
# filter move, dimmed and keyed "(unfiltered)", while the served app
# re-smoothed the kept rows.  The oracle is GlyphMapper._stata_lowess (and
# map_lowess around it), pinned to Stata by stat_truth.json's lowess curves
# and the U16 truth block.

_LW_KEYS = _KEYS | {"bwidth", "mean", "noweight", "adjust", "logit",
                    "y_all_mean", "max_ops"}
_LW_FRAME = _FRAME.assign(y01=(_FRAME["y"] > _FRAME["y"].median())
                          .astype(float))


class TestLowessConfig:
    def test_lowess_config_keys(self):
        r = _map("lowess", _FRAME, {"bwidth": ".4", "mean": "mean"})
        cfg = r._dash_agg_config
        assert set(cfg) == _LW_KEYS
        assert r._dash_agg_source is r.data_source
        assert hasattr(r, "_dash_agg_rows")
        assert cfg["type"] == "lowess" and cfg["cols"] == ["x_lw", "y_lw"]
        assert cfg["bwidth"] == 0.4 and cfg["mean"] is True
        assert cfg["noweight"] is False and cfg["adjust"] is False
        assert cfg["logit"] is False and cfg["y_all_mean"] is None
        assert cfg["max_ops"] == dr._DASH_LOWESS_JS_MAX_OPS == 2e8
        json.dumps(cfg, allow_nan=False)

    def test_an_out_of_range_bwidth_is_point_eight(self):
        # lowess.ado:75-78 (WP-31 C10a): outside (0, 1) is .8, silently.
        for bw in ("1.5", "-1", "0", "1"):
            assert _map("lowess", _FRAME, {"bwidth": bw}
                        )._dash_agg_config["bwidth"] == 0.8

    def test_lowess_adjust_mean_is_the_datasets(self):
        gm = _gm()
        gm.dataset = _FRAME.copy()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = gm.map_lowess(figure(), ColumnDataSource(_FRAME.iloc[:12]),
                              "y", "x", {"adjust": "adjust"})
        cfg = r._dash_agg_config
        assert cfg["adjust"] is True
        assert cfg["y_all_mean"] == pytest.approx(float(_FRAME["y"].mean()),
                                                  rel=1e-15)
        assert cfg["y_all_mean"] != pytest.approx(
            float(_FRAME["y"].iloc[:12].mean()))

    def test_lowess_empty_layer_is_tagged(self):
        for df in (_FRAME.iloc[:2], _FRAME.assign(x=2500.0)):
            r = _map("lowess", df)
            assert len(r.data_source.data["x_lw"]) == 0
            assert r._dash_agg_config["type"] == "lowess"
            assert r._dash_agg_source is r.data_source

    def test_a_recast_lowess_is_not_tagged(self):
        r = _map("lowess", _FRAME, {"recast": "scatter"})
        assert not hasattr(r, "_dash_agg_config")


class TestLowessStaleKind:
    def test_lowess_is_refit(self):
        assert "lowess" in dr._DASH_JS_REFIT_TYPES
        assert dr._dash_stale_kind("lowess", {}) is None
        assert dr._dash_stale_kind("lowess", {"recast": "scatter"}) == "fit"


_TRUTH = os.path.join(_HERE, "fixtures", "stat_truth.json")
_DATA = os.path.join(_HERE, "fixtures", "data")
_LW_VARIANTS = {"default": {}, "mean": {"mean": True},
                "noweight": {"noweight": True}}


def _lowess_js(x, y, bw, mean=False, noweight=False):
    got = _js("dash_lowess(%s, %s, %r, %s, %s)" % (
        json.dumps([float(v) for v in x]), json.dumps([float(v) for v in y]),
        float(bw), json.dumps(bool(mean)), json.dumps(bool(noweight))))
    return np.asarray(got["xs"], float), _nan(got["ys"])


@requires_node
class TestLowessTwin:
    @pytest.mark.parametrize("variant", list(_LW_VARIANTS))
    @pytest.mark.parametrize("ds", ["auto", "census", "nlsw88", "sp500"])
    def test_fixture_curves(self, ds, variant):
        with open(_TRUTH) as fh:
            truth = json.load(fh)
        meta = truth["datasets"][ds]
        df = pd.read_csv(os.path.join(_DATA, ds + ".csv")).dropna()
        x = df[meta["x"]].to_numpy(float)
        y = df[meta["y"]].to_numpy(float)
        opts = _LW_VARIANTS[variant]
        gx, gy = _lowess_js(x, y, 0.8, **opts)
        wx, wy = dr.GlyphMapper._stata_lowess(x, y, 0.8, **opts)
        np.testing.assert_array_equal(gx, wx)
        np.testing.assert_allclose(gy, wy, rtol=1e-9, atol=1e-10,
                                   equal_nan=True)
        # And Stata's own curve, stored whole.
        key = f"{ds}:{variant}_full"
        assert truth["lowess_full_resolution_check"][key] is True
        rec = truth["lowess_more"][key]
        want = np.array([np.nan if v is None else v
                         for v in rec["lowess_y"]], float)
        span = float(np.nanmax(want) - np.nanmin(want))
        np.testing.assert_allclose(gy, want, rtol=0, atol=1e-8 * span,
                                   equal_nan=True)

    def test_ties_are_missing(self):
        x = np.array([1.0] * 10 + list(range(2, 12)), float)
        y = np.round(_RNG.normal(20.0, 3.0, 20), 2)
        gx, gy = _lowess_js(x, y, 0.2)
        wx, wy = dr.GlyphMapper._stata_lowess(x, y, 0.2)
        np.testing.assert_allclose(gy, wy, rtol=1e-9, atol=1e-10,
                                   equal_nan=True)
        assert np.isnan(gy[:9]).all() and np.isfinite(gy[9:]).all()

    def test_ties_keep_dataset_order(self):
        x = np.array([3.0, 1.0, 3.0, 2.0, 3.0, 1.0, 5.0, 4.0])
        y = np.array([9.0, 1.0, 7.0, 2.0, 8.0, 3.0, 4.0, 6.0])
        gx, gy = _lowess_js(x, y, 0.5, mean=True)
        wx, wy = dr.GlyphMapper._stata_lowess(x, y, 0.5, mean=True)
        np.testing.assert_allclose(gy, wy, rtol=1e-12)


def _lowess_case(df, opts, yvar="y", dataset=None):
    gm = _gm()
    if dataset is not None:
        gm.dataset = dataset
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = gm.map_lowess(figure(), ColumnDataSource(df), yvar, "x",
                          dict(opts))
    x, y, _w = _rows(df, opts, yvar=yvar)
    got = js_runner.run_fit_js_block(r._dash_agg_config, x, y)
    data = r.data_source.data
    for g, c in (("x_lw", "x_lw"), ("y_lw", "y_lw")):
        np.testing.assert_allclose(_nan(got[g]), np.asarray(data[c], float),
                                   rtol=1e-9, atol=1e-10, equal_nan=True)
    return got


_LOWESS_CASES = [
    ("default", _LW_FRAME, {}, "y", None),
    ("bwidth(.4) mean", _LW_FRAME, {"bwidth": ".4", "mean": "mean"}, "y",
     None),
    ("noweight", _LW_FRAME, {"noweight": "noweight"}, "y", None),
    ("adjust, the dataset's mean", _LW_FRAME.iloc[:15],
     {"adjust": "adjust"}, "y", _LW_FRAME),
    ("adjust, no dataset", _LW_FRAME.iloc[:15], {"adjust": "adjust"}, "y",
     None),
    ("logit on 0/1 y", _LW_FRAME, {"logit": "logit"}, "y01", None),
    ("logit adjust on 0/1 y", _LW_FRAME.iloc[:20],
     {"logit": "logit", "adjust": "adjust"}, "y01", _LW_FRAME),
    ("bwidth(5) is .8", _LW_FRAME, {"bwidth": "5"}, "y", None),
    ("stairstep", _LW_FRAME, {"connect": "stairstep"}, "y", None),
    ("two rows", _LW_FRAME.iloc[:2], {}, "y", None),
    ("constant x", _LW_FRAME.assign(x=2500.0), {}, "y", None),
]


@requires_node
class TestLowessBranch:
    @pytest.mark.parametrize("df,opts,yvar,dataset",
                             [c[1:] for c in _LOWESS_CASES],
                             ids=[c[0] for c in _LOWESS_CASES])
    def test_matches_python(self, df, opts, yvar, dataset):
        _lowess_case(df, opts, yvar, dataset)

    def test_two_rows_and_no_spread_write_empty_columns(self):
        assert _lowess_case(_LW_FRAME.iloc[:2], {}) == {"x_lw": [],
                                                        "y_lw": []}
        assert _lowess_case(_LW_FRAME.assign(x=2500.0), {}) == {
            "x_lw": [], "y_lw": []}

    def test_capped(self):
        cfg = dict(_map("lowess", _FRAME)._dash_agg_config, max_ops=1e6)
        rng = np.random.default_rng(16)
        x = rng.uniform(0.0, 1.0, 20_000)
        got = js_runner.run_fit_js_block(cfg, x, 2.0 * x, timed=True)
        assert got["data"] == {"x_lw": [], "y_lw": []}
        assert got["ms"] < 200.0, got["ms"]


def _hist_ac(**extra):
    return dict({"type": "histogram", "varname": "v",
                 "bin_edges": [0.0, 1.0, 2.0, 3.0, 4.0], "start": 0.0,
                 "width": 1.0, "bin": 4, "ymode": "density"}, **extra)


def _kde_ac(**extra):
    return dict({"type": "kdensity", "varname": "v",
                 "x_grid": [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0],
                 "kernel": "epanechnikov", "bw_fixed": None}, **extra)


_VALS = [0.5, 1.5, 1.7, 2.2, 3.2, 1.1]


@requires_node
class TestPartnerKeys:
    """S16 reads the config keys its batch-4 partners write (DECISIONS
    A22): S12's histogram gap/baroffset and kdensity area, S11's atobs.
    Hand-written configs: the mappers that write the keys land after."""

    @pytest.mark.parametrize("vals", [_VALS, []], ids=["rows", "no rows"])
    def test_histogram_gap_and_offset(self, vals):
        got = js_runner.run_filter_js_block(
            "histogram", _hist_ac(gap=20, baroffset=0.5), vals)
        left, right = np.asarray(got["left"]), np.asarray(got["right"])
        np.testing.assert_allclose(right - left, [0.8] * 4, rtol=1e-12)
        mid = np.array([0.5, 1.5, 2.5, 3.5])
        np.testing.assert_allclose((left + right) / 2, mid + 0.5 * 0.8,
                                   rtol=1e-12)

    @pytest.mark.parametrize("vals", [_VALS, []], ids=["rows", "no rows"])
    def test_histogram_without_keys_unchanged(self, vals):
        for ac in (_hist_ac(), _hist_ac(gap=0, baroffset=0)):
            got = js_runner.run_filter_js_block("histogram", ac, vals)
            assert got["left"] == [0.0, 1.0, 2.0, 3.0]
            assert got["right"] == [1.0, 2.0, 3.0, 4.0]

    def test_kdensity_area(self):
        one = js_runner.run_filter_js_block("kdensity", _kde_ac(), _VALS)
        two = js_runner.run_filter_js_block("kdensity", _kde_ac(area=2),
                                            _VALS)
        assert two["x"] == one["x"]
        np.testing.assert_allclose(two["y"], 2.0 * np.asarray(one["y"]),
                                   rtol=1e-15)
        assert max(one["y"]) > 0

    def test_kdensity_without_key_unchanged(self):
        one = js_runner.run_filter_js_block("kdensity", _kde_ac(), _VALS)
        for ac in (_kde_ac(area=None), _kde_ac(area=1)):
            assert js_runner.run_filter_js_block("kdensity", ac,
                                                 _VALS) == one

    def test_atobs_grid(self):
        assert _js("dash_fit_grid([3, 1, 2, 1, 3], 100, null, true)") == [
            1.0, 2.0, 3.0]
        assert _js("dash_fit_grid([3, 1, 2], 3, null, false)") == [
            1.0, 2.0, 3.0]
        cfg = dict(_map("lfit", _FRAME)._dash_agg_config, atobs=True)
        x, y, _w = _rows(_FRAME, {})
        got = js_runner.run_fit_js_block(cfg, x, y)
        xu = np.unique(x)
        np.testing.assert_array_equal(got["x"], xu)
        np.testing.assert_allclose(got["y"], np.polyval(np.polyfit(x, y, 1),
                                                        xu), rtol=1e-9)
        cfg = dict(_map("qfit", _FRAME)._dash_agg_config, atobs=True)
        assert js_runner.run_fit_js_block(cfg, x, y)["x"] == xu.tolist()
