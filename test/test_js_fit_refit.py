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
         "range",
         # WP-31 C4: atobs, the grid of the kept x (S16 reads it).
         "atobs"}

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
        # lfitci and qfitci are refitted too (WP-31 F1b): TestCiStaleKind.
        # lpoly too (WP-31 F1d): TestLpolyStaleKind.  Flipped (WP-31
        # F1e): listed lpolyci, refitted since (TestLpolyciStaleKind).
        for t in ("fpfit", "fpfitci", "mband", "mspline"):
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
    # A lowess line's columns are x_lw and y_lw (WP-31 F1c), an lpoly's
    # x_lp and y_lp (F1d).
    cx, cy = (("x_lw", "y_lw") if "x_lw" in d
              else ("x_lp", "y_lp") if "x_lp" in d else ("x", "y"))
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

# lowess takes no atobs (it is drawn at the observations): C4 added atobs
# to the lfit/qfit keys only.
_LW_KEYS = (_KEYS - {"atobs"}) | {"bwidth", "mean", "noweight", "adjust",
                                  "logit", "y_all_mean", "max_ops"}
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


# ---- WP-31 F1b: lfitci and qfitci ----
#
# GAPS3 F1b: an lfitci or qfitci on the saved page kept the build's line
# and band after a filter move, dimmed and keyed "(unfiltered)", while the
# served app refitted both from the kept rows.  The oracle is map_lfitci
# and map_qfitci (regress, predict stdp/stdf/stdr, invttail at level()),
# pinned to twoway by test_statistical_truth.py's ci_bands and fitci_std
# and the U13 truth block, run on the same rows; and the served app after
# the same move.

_CI_COLS = ["x_fit", "y_fit", "y_lower", "y_upper"]
#: S10's keys plus the band's level and standard error (D-13.b).
_CI_KEYS = _KEYS | {"level", "std"}
_FW = {"weight": "fweight", "wexp": "w"}
_PWT = {"weight": "pweight", "wexp": "w"}


def _ci_map(ptype, df, opts=None):
    """``(line, band)``: the ci mapper's two renderers on *df*."""
    rends = _map(ptype, df, opts)
    assert len(rends) == 2
    return rends[0], rends[1]


class TestCiConfig:
    def test_lfitci_config_keys(self):
        line, band = _ci_map("lfitci", _FRAME)
        cfg = line._dash_agg_config
        assert set(cfg) == _CI_KEYS
        assert cfg["type"] == "lfitci" and cfg["cols"] == _CI_COLS
        assert cfg["level"] == 95.0 and isinstance(cfg["level"], float)
        assert cfg["std"] == "stdp" and cfg["n"] == 100
        assert line._dash_agg_source is line.data_source
        assert band.data_source is line.data_source
        assert hasattr(line, "_dash_agg_rows")
        json.dumps(cfg, allow_nan=False)

    def test_qfitci_config_keys(self):
        line, _band = _ci_map("qfitci", _FRAME, {
            "level": "90", "stdr": "stdr", "n": "3", "range": "1000 6000"})
        cfg = line._dash_agg_config
        assert set(cfg) == _CI_KEYS
        assert cfg["type"] == "qfitci"
        assert (cfg["level"], cfg["std"]) == (90.0, "stdr")
        # qfitci reads n() as given: n(3) plots 3 (qfit's n(3) plots 100).
        assert cfg["n"] == 3 and cfg["range"] == [1000.0, 6000.0]

    def test_the_band_renderer_is_not_tagged(self):
        for t in ("lfitci", "qfitci"):
            _line, band = _ci_map(t, _FRAME)
            assert not hasattr(band, "_dash_agg_config")
            outline = getattr(band, "_dash_ci_outline", None)
            assert outline is None or not hasattr(outline,
                                                  "_dash_agg_config")

    def test_std_none_for_aw_stdf(self):
        line, _ = _ci_map("lfitci", _FRAME, dict(_AW, stdf="stdf"))
        assert line._dash_agg_config["std"] == "none"
        line, _ = _ci_map("qfitci", _FRAME, dict(_FW, stdf="stdf"))
        assert line._dash_agg_config["std"] == "stdf"

    def test_an_empty_layer_is_tagged(self):
        for t in ("lfitci", "qfitci"):
            line, band = _ci_map(t, _FRAME.iloc[:1], {"level": "90"})
            cfg = line._dash_agg_config
            assert cfg["type"] == t and cfg["level"] == 90.0
            assert line._dash_agg_source is line.data_source
            assert band.data_source is line.data_source
            assert len(line.data_source.data["x_fit"]) == 0

    def test_a_points_layer_is_not_tagged(self):
        # estopts()/predopts()/estcmd(): Stata's points, frozen (D3).
        pts = {"x": [2000.0, 3000.0], "y": [11.0, 21.0],
               "lo": [9.0, 20.0], "hi": [13.0, 22.0], "nobs": 30}
        for t in ("lfitci", "qfitci"):
            rends = _map(t, _FRAME, {"estopts": "noconstant",
                                     "points": dict(pts)})
            rends = rends if isinstance(rends, list) else [rends]
            assert not any(hasattr(r, "_dash_agg_config") for r in rends)

    @pytest.mark.parametrize("opts", [{"ciplot": "rline"},
                                      {"fitplot": "scatter"}],
                             ids=["ciplot(rline)", "fitplot(scatter)"])
    def test_a_band_or_line_drawn_as_another_type_is_not_tagged(self, opts):
        # Drawn from a fresh source by _dash_draw_range_as/_dash_draw_xy_as,
        # which the page does not refit: the layer keeps the cue.
        for t in ("lfitci", "qfitci"):
            gm = _gm()
            fig = figure()
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                getattr(gm, "map_" + t)(fig, ColumnDataSource(_FRAME), "y",
                                        "x", dict(opts))
            assert not any(hasattr(r, "_dash_agg_config")
                           for r in fig.renderers)
            assert dr._dash_stale_kind(t, opts) == "fit"


class TestCiStaleKind:
    def test_lfitci_and_qfitci_are_refit(self):
        for t in ("lfitci", "qfitci"):
            assert dr._dash_stale_kind(t, {}) is None
            # rarea and line are twoway's own band and line.
            assert dr._dash_stale_kind(t, {"ciplot": "rarea",
                                           "fitplot": "line"}) is None
            assert dr._dash_stale_kind(t, {"nofit": "nofit"}) is None
        assert {"lfitci", "qfitci"} <= dr._DASH_JS_REFIT_TYPES


def _ci_case(ptype, df, opts):
    """The ci branch on *df*'s kept rows against the mapper's columns."""
    line, _band = _ci_map(ptype, df, opts)
    x, y, w = _rows(df, opts)
    got = js_runner.run_fit_js_block(line._dash_agg_config, x, y, w)
    data = line.data_source.data
    assert sorted(got) == sorted(_CI_COLS)
    for c in _CI_COLS:
        np.testing.assert_allclose(_nan(got[c]), np.asarray(data[c], float),
                                   rtol=1e-8, atol=1e-10, equal_nan=True,
                                   err_msg=c)
    return {c: _nan(got[c]) for c in _CI_COLS}


_LFITCI_CASES = [
    ("default", _FRAME, {}),
    ("level(90)", _FRAME, {"level": "90"}),
    ("level(0)", _FRAME, {"level": "0"}),
    ("level(-20)", _FRAME, {"level": "-20"}),
    ("level(100)", _FRAME, {"level": "100"}),
    ("stdf", _FRAME, {"stdf": "stdf"}),
    ("stdr", _FRAME, {"stdr": "stdr"}),
    ("aw", _FRAME, _AW),
    ("aw stdf", _FRAME, dict(_AW, stdf="stdf")),
    ("fw", _FRAME, _FW),
    ("fw stdf", _FRAME, dict(_FW, stdf="stdf")),
    ("pw", _FRAME, _PWT),
    ("constant x", _FRAME.assign(x=2500.0), {}),
    ("two rows", _FRAME.iloc[:2], {}),
    ("one row", _FRAME.iloc[:1], {}),
    ("range(1000 6000)", _FRAME, {"range": "1000 6000"}),
    ("atobs", _FRAME, {"atobs": "atobs"}),
    ("stairstep", _FRAME, {"connect": "stairstep", "n": "5"}),
]


@requires_node
class TestCiBranch:
    @pytest.mark.parametrize("df,opts", [c[1:] for c in _LFITCI_CASES],
                             ids=[c[0] for c in _LFITCI_CASES])
    def test_lfitci_matches_python(self, df, opts):
        _ci_case("lfitci", df, opts)

    def test_two_rows_draw_the_line_and_no_band(self):
        got = _ci_case("lfitci", _FRAME.iloc[:2], {})
        assert np.isfinite(got["y_fit"]).sum() == 100
        assert np.isnan(got["y_lower"]).all()
        assert np.isnan(got["y_upper"]).all()
        got = _ci_case("qfitci", _FRAME.iloc[:3], {})
        assert np.isfinite(got["y_fit"]).sum() == 100
        assert np.isnan(got["y_lower"]).all()

    @pytest.mark.parametrize("ptype", ["lfitci", "qfitci"])
    def test_nearly_collinear_design(self, ptype):
        # D-13.c: a 5-minute %tc x (1.9e12 + 300000 i).  _dash_wls's rank
        # cut on the raw design and dash_wls's Gram-Schmidt keep the same
        # columns on the centred, scaled design: line and band agree.
        _ci_case(ptype, _FRAME.assign(x=1.9e12 + 300000.0 * np.arange(30)),
                 {})

    def test_one_row_writes_empty_columns(self):
        got = _ci_case("lfitci", _FRAME.iloc[:1], {})
        assert all(len(v) == 0 for v in got.values())

    def test_level_100_draws_no_band(self):
        got = _ci_case("qfitci", _FRAME, {"level": "100"})
        assert np.isfinite(got["y_fit"]).all()
        assert np.isnan(got["y_lower"]).all()

    @pytest.mark.parametrize("ptype", ["lfitci", "qfitci"])
    @pytest.mark.parametrize("std", ["stdp", "stdf", "stdr"])
    def test_the_band_is_statas_on_auto(self, ptype, std):
        # stat_truth.json fitci_std: twoway's serset (float) on auto.
        with open(_TRUTH) as fh:
            truth = json.load(fh)["fitci_std"]["auto:%s:%s" % (ptype, std)]
        auto = pd.read_csv(os.path.join(_DATA, "auto.csv"))
        df = auto[["mpg", "weight"]].rename(columns={"mpg": "y",
                                                     "weight": "x"})
        opts = {} if std == "stdp" else {std: std}
        line, _ = _ci_map(ptype, df, opts)
        x, y, w = _rows(df, opts)
        got = js_runner.run_fit_js_block(line._dash_agg_config, x, y, w)
        at = [i - 1 for i in truth["sample_index"]]
        for col, key in (("x_fit", "fit_x"), ("y_fit", "fit"),
                         ("y_lower", "lower"), ("y_upper", "upper")):
            np.testing.assert_allclose(np.asarray(got[col])[at], truth[key],
                                       rtol=1e-6, err_msg=col)

    @pytest.mark.parametrize("df,opts", [
        (_FRAME, {}),
        (_FRAME, {"level": "99"}),
        (_FRAME, _AW),
        (_FRAME, dict(_FW, stdf="stdf")),
        (_FRAME, dict(_PWT, stdr="stdr")),
        (_FRAME.iloc[:3], {}),
        (_FRAME.iloc[:2], {}),
        (_FRAME.iloc[:1], {}),
        (_FRAME.assign(x=np.where(np.arange(30) % 2, 1.0, 3.0)), {}),
        (_FRAME.assign(x=np.where(np.arange(30) % 2, -1.0, 2.0)), {}),
        (_FRAME, {"n": "3"}),
        (_FRAME.assign(x=2500.0), {}),
        (_FRAME.assign(x=_FRAME["x"] + 1e7), {}),
    ], ids=["default", "level(99)", "aw", "fw stdf", "pw stdr",
            "three rows", "two rows", "one row", "two values, x^2 kept",
            "two values, x kept", "n(3) plots 3", "constant x",
            "1e7 offset"])
    def test_qfitci_matches_python(self, df, opts):
        _ci_case("qfitci", df, opts)


@requires_node
class TestCiWrite:
    def test_rows(self):
        # dash_fit_write keeps a row whose band is missing (twoway's
        # missing limits, a NaN cell) and drops one a finite value of
        # which has no date on its axis (_drop_off_dates).
        ac = {"cols": _CI_COLS, "xaxiskind": None, "yaxiskind": "td"}
        got = _js("(() => { const s = {data: null, change: {emit: () => "
                  "{}}}; dash_fit_write(s, " + json.dumps(ac) + ", "
                  "[1, 2, 3], [10, 11, 12], [[NaN, 1e12, 9], "
                  "[NaN, 13, 13]]); return s.data; })()")
        assert got["x_fit"] == [1, 3]
        assert got["y_lower"][0] is None and got["y_upper"][0] is None
        assert got["y_fit"] == [10 * 86_400_000.0 + _E,
                                12 * 86_400_000.0 + _E]


def _ci_data(renderers):
    """The four columns of the one ci layer's line source, after checking
    the band reads the same source."""
    lines = [r for r in renderers if isinstance(r, GlyphRenderer)
             and isinstance(r.glyph, Line) and "y_lower" in r.data_source.data]
    assert len(lines) == 1, f"{len(lines)} ci lines"
    src = lines[0].data_source
    bands = [r for r in renderers if isinstance(r, GlyphRenderer)
             and r is not lines[0] and r.data_source is src]
    assert bands, "the band does not read the line's source"
    return {c: np.asarray(src.data[c], dtype=float) for c in _CI_COLS}


def _served_ci_after(spec, action):
    doc, _ = _served(spec)
    kind, want = action
    w = [m for m in _widgets_of(doc) if type(m).__name__ == kind][0]
    if kind == "Select":
        want = [v for v, lab in w.options if lab == want][0]
    _fire(w, want)
    return _ci_data([m for m in doc.models if isinstance(m, GlyphRenderer)])


_CI_SPECS = [
    ("lfitci", [plot_for("scatter"), plot_for("lfitci")]),
    ("qfitci", [plot_for("scatter"), plot_for("qfitci")]),
    ("lfitci level(90) stdf", [plot_for("lfitci", {"level": "90",
                                                   "stdf": "stdf"})]),
    ("qfitci [aw=rep] n(7)", [plot_for("qfitci", {"weight": "aweight",
                                                  "wexp": "rep", "n": "7"})]),
    ("lfitci [fw=rep] nofit", [plot_for("lfitci", {"weight": "fweight",
                                                   "wexp": "rep",
                                                   "nofit": "nofit"})]),
]


@requires_node
class TestTheSavedCiRefits:
    @pytest.mark.parametrize("move", _MOVES, ids=[m[0] for m in _MOVES])
    @pytest.mark.parametrize("plots", [s[1] for s in _CI_SPECS],
                             ids=[s[0] for s in _CI_SPECS])
    def test_saved_equals_served(self, plots, move):
        _, filt, action, _oracle = move
        spec = _spec(plots, {"filter": filt})
        r = _render(spec)
        built = _ci_data(r.figures["g1"].renderers)
        _move(r, action)
        saved = _ci_data(r.figures["g1"].renderers)
        served = _served_ci_after(spec, action)
        for c in _CI_COLS:
            np.testing.assert_allclose(saved[c], served[c], rtol=1e-8,
                                       atol=1e-9, equal_nan=True, err_msg=c)
        assert (built["y_lower"].shape != saved["y_lower"].shape
                or not np.allclose(built["y_lower"], saved["y_lower"],
                                   equal_nan=True)), "the move changed nothing"

    def test_a_move_leaving_two_rows_draws_the_line_and_no_band(self):
        spec = _spec([plot_for("scatter"), plot_for("lfitci")],
                     {"filter": "price, type(slider)"})
        r = _render(spec)
        _move(r, ("Slider", 10000.0))
        got = _ci_data(r.figures["g1"].renderers)
        assert len(got["x_fit"]) == 100 and np.isfinite(got["y_fit"]).all()
        assert np.isnan(got["y_lower"]).all()
        assert np.isnan(got["y_upper"]).all()


# ---- WP-31 F1d: lpoly ----
#
# GAPS3 F1d: an lpoly on the saved page kept the build's smooth after a
# filter move, dimmed and keyed "(unfiltered)", while the served app
# refitted it from the kept rows with Stata's rule-of-thumb bandwidth
# derived from them.  The oracles are GlyphMapper._compute_lpoly_fit and
# _lpoly_rot_detail (pinned to Stata by test_lpoly_rot.py on
# lpoly_rot_truth.json and the U19 truth block), map_lpoly around them,
# and the served app after the same move.

#: S10's keys (lpoly takes no atobs) plus lpoly's own (D-19.c) and
#: keepmissing, cmissing(n)'s kept missing grid points (WP-31 C6).
_LP_KEYS = (_KEYS - {"atobs"}) | {"bwidth", "degree", "kernel",
                                  "n_dataset", "n_user", "keepmissing"}
_LP_TRUTH = os.path.join(_HERE, "fixtures", "lpoly_rot_truth.json")
with open(_LP_TRUTH, encoding="utf-8") as _fh:
    _LPT = json.load(_fh)
_LP_DIVERGENT_FIXTURE = {i for dv in _LPT["divergences"] for i in dv["rows"]}
_LP_KERNELS = ("epanechnikov", "epan2", "biweight", "cosine", "gaussian",
               "parzen", "rectangle", "triangle")


def _lp_sample(rec):
    """x, y and lpoly's weights of a fixture row or curve: the dataset's
    columns ``rec["x"]``/``rec["y"]`` at the row indices ``rec["idx"]``
    (``datasets[ds]`` maps a column name to its values); the weight column
    ``rec["w"]`` (empty: none), aweights scaled to mean 1, fweights raw
    (``_dash_lpoly_weights``)."""
    D = _LPT["datasets"][rec["ds"]]
    idx = rec["idx"]
    x = np.array([D[rec["x"]][i] for i in idx], dtype=float)
    y = np.array([D[rec["y"]][i] for i in idx], dtype=float)
    w = None
    if rec.get("w"):
        w = dr._dash_lpoly_weights(
            np.array([D[rec["w"]][i] for i in idx], dtype=float),
            "fw" if rec.get("wtype") == "fw" else "aw")
    return x, y, w


def _lp_list(v):
    return None if v is None else [float(e) for e in v]


def _js_batch(fn, calls):
    """Run ``fn(*args)`` of the fit helpers on each argument list in
    *calls*, in ONE node process; NaN comes back as None."""
    return run_js(_fit_js() + "\nconst _calls = " + json.dumps(calls)
                  + ";\nprocess.stdout.write(JSON.stringify(_calls.map("
                  + "a => " + fn + "(...a))));")


_ROT_CACHE = {}


def _rot_pairs():
    """{row id: (JS h, Python's _lpoly_rot_detail)} for every fixture row,
    the JS run once."""
    if not _ROT_CACHE:
        calls, dets = [], []
        for row in _LPT["rows"]:
            x, y, w = _lp_sample(row)
            calls.append([x.tolist(), y.tolist(), _lp_list(w),
                          row["degree"], row["kernel"]])
            dets.append(dr._lpoly_rot_detail(x, y, w, row["degree"],
                                             row["kernel"]))
        got = _js_batch("dash_lpoly_rot", calls)
        for row, g, d in zip(_LPT["rows"], got, dets):
            _ROT_CACHE[row["id"]] = (np.nan if g is None else float(g), d)
    return _ROT_CACHE


def _rot_agrees(js, det, rel):
    h = det["h"]
    if not np.isfinite(h):
        return not np.isfinite(js)
    return np.isfinite(js) and abs(js - h) <= rel * abs(h)


def _rot_all_kept(row, det):
    pe = row["degree"] if row["degree"] % 2 else row["degree"] + 1
    return len(det["kept"]) == pe + 4


class TestLpolyConfig:
    def test_lpoly_config_keys(self):
        r = _map("lpoly", _FRAME, {"bwidth": "400", "degree": "1",
                                   "kernel": "biweight", "n": "20"})
        cfg = r._dash_agg_config
        assert set(cfg) == _LP_KEYS
        assert r._dash_agg_source is r.data_source
        assert hasattr(r, "_dash_agg_rows")
        assert cfg["type"] == "lpoly" and cfg["cols"] == ["x_lp", "y_lp"]
        assert cfg["bwidth"] == 400.0 and cfg["degree"] == 1
        assert cfg["kernel"] == "biweight"
        # No dataset: the layer's 30 rows stand in for _N (< 50: n = N).
        assert cfg["n_dataset"] == 30 and cfg["n_user"] == 20.0
        assert cfg["n"] == 30 and cfg["keepmissing"] is False
        json.dumps(cfg, allow_nan=False)
        d = _map("lpoly", _FRAME)._dash_agg_config
        assert d["bwidth"] is None and d["degree"] == 0
        assert d["kernel"] == "epanechnikov" and d["n_user"] is None
        assert _map("lpoly", _FRAME, {"bwidth": "0"}
                    )._dash_agg_config["bwidth"] is None
        assert _map("lpoly", _FRAME, {"cmissing": "n"}
                    )._dash_agg_config["keepmissing"] is True

    def test_lpoly_grid_plan(self):
        gm = _gm()
        assert gm._lpoly_grid_plan({}, "lpoly", 30) == (30, 30, None)
        gm.dataset = pd.DataFrame({"a": range(40)})
        assert gm._lpoly_grid_plan({"n": "20"}, "lpoly", 5) == (40, 40, 20.0)
        gm.dataset = pd.DataFrame({"a": range(74)})
        assert gm._lpoly_grid_plan({}, "lpoly", 22) == (50, 74, None)
        assert gm._lpoly_grid_plan({"n": "100"}, "lpoly", 22) == (74, 74,
                                                                  100.0)
        assert gm._lpoly_grid_plan({"n": "1"}, "lpoly", 22) == (50, 74, 1.0)
        assert gm._lpoly_grid_plan({"n": "20.7"}, "lpoly", 22)[0] == 20
        # _lpoly_grid_n, the plan's first value, is deleted (WP-31 F1e):
        # map_lpolyci, its last caller, reads the plan whole.
        assert gm._lpoly_grid_plan({"n": "100"}, "lpoly", 22)[0] == 74

    def test_lpoly_empty_layer_is_tagged(self):
        r = _map("lpoly", _FRAME.iloc[:1])
        assert len(r.data_source.data["x_lp"]) == 0
        assert r._dash_agg_config["type"] == "lpoly"
        assert r._dash_agg_source is r.data_source
        assert r._dash_agg_config["n_dataset"] == 1

    def test_a_recast_lpoly_is_not_tagged(self):
        r = _map("lpoly", _FRAME, {"recast": "scatter"})
        assert not hasattr(r, "_dash_agg_config")

    @pytest.mark.parametrize("degree", [4, 5, 6, 7])
    def test_degree_four_to_seven_is_fitted(self, degree):
        # twoway draws degree 4-7 (WP-31 C10b); the mapper read degree()
        # within 0-3 and drew degree 0 for them, with a warning.
        opts = {"degree": str(degree), "bwidth": "900"}
        r = _map("lpoly", _FRAME, opts)
        assert r._dash_agg_config["degree"] == degree
        x, y, _w = _rows(_FRAME, {})
        _gx, gy = dr.GlyphMapper._compute_lpoly_fit(
            x, y, bwidth=900.0, degree=degree, n_grid=30)
        np.testing.assert_allclose(r.data_source.data["y_lp"],
                                   gy[np.isfinite(gy)], rtol=1e-12)


class TestLpolyStaleKind:
    def test_lpoly_is_refit(self):
        assert "lpoly" in dr._DASH_JS_REFIT_TYPES
        assert dr._dash_stale_kind("lpoly", {}) is None
        assert dr._dash_stale_kind("lpoly", {"recast": "scatter"}) == "fit"
        # Flipped (WP-31 F1e): lpolyci was still marked; it is refitted
        # since (TestLpolyciStaleKind).
        assert dr._dash_stale_kind("lpolyci", {}) is None


def _spliced(name):
    js = dr._FILTER_JS
    head = "const %s = JSON.parse('" % name
    i = js.index(head) + len(head)
    return json.loads(js[i:js.index("')", i)])


class TestLpolyTables:
    def test_rot_constants_are_spliced(self):
        t = _spliced("_DASH_LPOLY_ROT_C")
        assert len(t) == 32
        assert t == {"%s|%d" % k: v
                     for k, v in dr._LPOLY_ROT_CONSTANTS.items()}
        assert t["epanechnikov|1"] == 0.7688119451983404

    def test_supports_are_spliced(self):
        t = _spliced("_DASH_LPOLY_SUPPORT")
        assert set(t) == set(dr._KERNELS)
        for k, (s, _f) in dr._KERNELS.items():
            assert t[k] == (None if math.isinf(s) else s)


@requires_node
class TestLpolyKw:
    @pytest.mark.parametrize("kernel", _LP_KERNELS)
    def test_each_kernel(self, kernel):
        sup = dr._KERNELS[kernel][0]
        s = 3.0 if math.isinf(sup) else sup
        z = [0.0, 0.3 * s, -0.3 * s, 0.6 * s, 0.999 * s, -0.999 * s, s, -s,
             1.2 * s]
        if math.isinf(sup):
            z += [8.0, -40.0]
        x0, h = 2500.0, 120.0
        x = [x0 + h * v for v in z]
        got = _js("dash_lpoly_kw(%s, %r, %r, %s)" % (
            json.dumps(x), x0, h, json.dumps(kernel)))
        want = dr._lpoly_kernel_weights(np.asarray(x), x0, h, kernel)
        np.testing.assert_allclose(got, want, rtol=1e-14, atol=1e-300)
        if not math.isinf(sup):
            assert got[6] == 0 and got[7] == 0 and got[8] == 0
            assert got[4] == pytest.approx(float(want[4]), rel=1e-14)


_ROT_IDS = [r["id"] for r in _LPT["rows"]]
_ROT_BY_ID = {r["id"]: r for r in _LPT["rows"]}
#: The fixture rows where the saved page's rule of thumb is not Python's
#: (D-19.a), measured at the F1d commit: 48 of 785, every one Python's
#: "float" route -- an exact global fit on 2 to 5 rows of auto (mpg on
#: weight, epanechnikov and gaussian, degree 0-3), where Stata's h is its
#: round-off; the page drew y = 0 there, and since WP-31 C11b keeps the
#: build and marks the layer (TestTheRotFlagsAnExactFit: every one is
#: flagged; a port of the round-off could not be shown to agree across
#: platforms, so the count stays).  The 737 others agree to 1e-6
#: (1.8e-10 at most), the rows whose raw columns invsym cuts among them.
_ROT_DIVERGENT_COUNT = 48


@requires_node
class TestRotTwin:
    @pytest.mark.parametrize("rid", _ROT_IDS)
    def test_fixture_rows(self, rid):
        row = _ROT_BY_ID[rid]
        js, det = _rot_pairs()[rid]
        if det["route"] == "exact" and _rot_all_kept(row, det):
            assert _rot_agrees(js, det, 1e-6), (js, det["h"])
        elif not np.isfinite(det["h"]):
            # Stata's r(bwidth) is missing: the page draws y = 0 too.
            assert not np.isfinite(js), js
        else:
            assert (not np.isfinite(js)) or _rot_agrees(js, det, 1e-3), (
                js, det)

    def test_divergence_count_is_recorded(self):
        pairs = _rot_pairs()
        div = []
        for rid, (js, det) in pairs.items():
            if _rot_agrees(js, det, 1e-6):
                continue
            row = _ROT_BY_ID[rid]
            div.append(rid)
            assert (rid in _LP_DIVERGENT_FIXTURE or det["route"] == "float"
                    or not _rot_all_kept(row, det)), (rid, js, det)
        print("lpoly rule of thumb: %d of %d fixture rows diverge (D-19.a)"
              % (len(div), len(pairs)))
        assert len(div) == _ROT_DIVERGENT_COUNT, sorted(div)

    def test_overflow_guard(self):
        x = np.arange(1.0, 11.0) * 1e60
        y = np.array([3.0, 1.0, 4.0, 1.0, 5.0, 9.0, 2.0, 6.0, 5.0, 3.0])
        assert np.isnan(dr._lpoly_rot_detail(x, y, None, 0, "epanechnikov"
                                             )["h"])
        got = _js("dash_lpoly_rot(%s, %s, null, 0, 'epanechnikov')" % (
            json.dumps(x.tolist()), json.dumps(y.tolist())))
        assert got is None

    def test_fewer_distinct_x_than_the_global_fit_is_missing(self):
        # x of 0 and 1 only: Stata's r(bwidth) is missing (twoway draws
        # y = 0); the scaled design is singular however round-off falls.
        x = np.array([0.0, 1.0] * 20)
        y = np.round(_RNG.normal(20.0, 3.0, 40), 2)
        assert np.isnan(dr._lpoly_rot_detail(x, y, None, 0, "epanechnikov"
                                             )["h"])
        got = _js("dash_lpoly_rot(%s, %s, null, 0, 'epanechnikov')" % (
            json.dumps(x.tolist()), json.dumps(y.tolist())))
        assert got is None


_LP_CURVE_IDS = [c["id"] for c in _LPT["curves"]]
_LP_CURVES = {c["id"]: c for c in _LPT["curves"]}
_FIT_CACHE = {}


def _fit_pairs():
    if not _FIT_CACHE:
        calls = []
        for c in _LPT["curves"]:
            x, y, w = _lp_sample(c)
            calls.append([x.tolist(), y.tolist(), float(c["bwidth"]),
                          c["degree"], c["kernel"], _lp_list(w),
                          [float(v) for v in c["gx"]]])
        got = _js_batch("dash_lpoly_fit", calls)
        for c, g in zip(_LPT["curves"], got):
            _FIT_CACHE[c["id"]] = _nan(g)
    return _FIT_CACHE


@requires_node
class TestLpolyFitTwin:
    @pytest.mark.parametrize("cid", _LP_CURVE_IDS)
    def test_fixture_curves(self, cid):
        c = _LP_CURVES[cid]
        x, y, w = _lp_sample(c)
        _gx, want = dr.GlyphMapper._compute_lpoly_fit(
            x, y, bwidth=float(c["bwidth"]), degree=c["degree"],
            kernel=c["kernel"], w=w, x_grid=np.asarray(c["gx"], float))
        np.testing.assert_allclose(_fit_pairs()[cid], want, rtol=1e-8,
                                   atol=1e-10, equal_nan=True)

    def test_kept_columns_two_values(self):
        # foreign == 1 biweight degree(2) at Stata's 287.78: a window of
        # two distinct x keeps {1, d^2} (_lpoly_kept_columns, Part C).
        D = _LPT["datasets"]["auto"]
        sel = [i for i, f in enumerate(D["foreign"]) if f == 1]
        x = np.array([D["weight"][i] for i in sel], float)
        y = np.array([D["mpg"][i] for i in sel], float)
        h = 287.78
        found = []
        for x0 in np.linspace(x.min(), x.max(), 200):
            kw = dr._lpoly_kernel_weights(x, x0, h, "biweight")
            pos = kw > 0
            if len(np.unique(x[pos])) != 2:
                continue
            X = np.vander(x[pos] - x0, 3, increasing=True)
            G = (X * kw[pos][:, None]).T @ X
            want = dr._lpoly_kept_columns(G)
            got = _js("dash_lpoly_kept(%s)" % json.dumps(G.tolist()))
            assert got == want, (x0, got, want)
            found.append(want)
        assert [0, 2] in found


def _lpoly_case(df, opts, dataset=None):
    gm = _gm()
    if dataset is not None:
        gm.dataset = dataset
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = gm.map_lpoly(figure(), ColumnDataSource(df), "y", "x",
                         dict(opts))
    x, y, w = _rows(df, opts)
    got = js_runner.run_fit_js_block(r._dash_agg_config, x, y, w)
    data = r.data_source.data
    for c in ("x_lp", "y_lp"):
        np.testing.assert_allclose(_nan(got[c]), np.asarray(data[c], float),
                                   rtol=1e-8, atol=1e-10, equal_nan=True,
                                   err_msg=c)
    return got


_LP_FRAME60 = pd.concat([_FRAME, _FRAME.assign(x=_FRAME["x"] + 7.3)],
                        ignore_index=True)
_LPOLY_CASES = [
    ("default", _FRAME, {}, None),
    ("bwidth(400) degree(1) n(20)", _FRAME,
     {"bwidth": "400", "degree": "1", "n": "20"}, None),
    ("biweight degree(3) aw", _FRAME,
     {"kernel": "biweight", "degree": "3", "weight": "aweight",
      "wexp": "w"}, None),
    ("gaussian fw", _FRAME, {"kernel": "gaussian", "weight": "fweight",
                             "wexp": "w"}, None),
    ("degree(5) bwidth(900)", _FRAME, {"degree": "5", "bwidth": "900"},
     None),
    ("a 60-row dataset, n(20)", _LP_FRAME60.iloc[:25], {"n": "20"},
     _LP_FRAME60),
    ("a 60-row dataset, default n", _LP_FRAME60.iloc[:25], {},
     _LP_FRAME60),
    ("bwidth(60) leaves gaps", _FRAME, {"bwidth": "60"}, None),
    ("bwidth(60) cmissing(n)", _FRAME, {"bwidth": "60", "cmissing": "n"},
     None),
    ("stairstep", _FRAME, {"connect": "stairstep"}, None),
    ("one row", _FRAME.iloc[:1], {}, None),
    ("x of 0 and 1 only: the line at 0", _FRAME.assign(
        x=(np.arange(30) % 2).astype(float)), {}, None),
]


@requires_node
class TestLpolyBranch:
    @pytest.mark.parametrize("df,opts,dataset",
                             [c[1:] for c in _LPOLY_CASES],
                             ids=[c[0] for c in _LPOLY_CASES])
    def test_matches_python(self, df, opts, dataset):
        _lpoly_case(df, opts, dataset)

    def test_one_row_writes_empty_columns(self):
        assert _lpoly_case(_FRAME.iloc[:1], {}) == {"x_lp": [], "y_lp": []}

    def test_x_of_two_values_draws_zero(self):
        got = _lpoly_case(_FRAME.assign(x=(np.arange(30) % 2).astype(float)),
                          {})
        assert got["y_lp"] == [0.0] * 30

    def test_cmissing_n_keeps_the_missing_points(self):
        got = _lpoly_case(_FRAME, {"bwidth": "60", "cmissing": "n"})
        y = _nan(got["y_lp"])
        assert len(y) == 30 and np.isnan(y).any() and np.isfinite(y).any()


#: (name, plots, move): a saved lpoly after a move equals the served one.
_LP_REFIT = [
    ("lpoly bwidth(400) degree(1) n(20)",
     [plot_for("lpoly", {"bwidth": "400", "degree": "1", "n": "20"})], m)
    for m in _MOVES
] + [
    ("lpoly", [plot_for("scatter"), plot_for("lpoly")], _MOVES[1]),
    ("lpoly", [plot_for("scatter"), plot_for("lpoly")], _MOVES[2]),
    ("lpoly gaussian [fw=rep]",
     [plot_for("lpoly", {"kernel": "gaussian", "weight": "fweight",
                         "wexp": "rep"})], _MOVES[1]),
    ("lpoly biweight degree(3) [aw=weight] bwidth(900)",
     [plot_for("lpoly", {"kernel": "biweight", "degree": "3",
                         "weight": "aweight", "wexp": "weight",
                         "bwidth": "900"})], _MOVES[0]),
]


@requires_node
class TestTheSavedLpolyRefits:
    @pytest.mark.parametrize("plots,move", [c[1:] for c in _LP_REFIT],
                             ids=["%s-%s" % (c[0], c[2][0])
                                  for c in _LP_REFIT])
    def test_saved_equals_served(self, plots, move):
        _, filt, action, _oracle = move
        spec = _spec(plots, {"filter": filt})
        r = _render(spec)
        built = _fit_data(r.figures["g1"].renderers)
        _move(r, action)
        sx, sy = _fit_data(r.figures["g1"].renderers)
        vx, vy = _served_fit_after(spec, action)
        np.testing.assert_allclose(sx, vx, rtol=1e-8, atol=1e-9)
        np.testing.assert_allclose(sy, vy, rtol=1e-8, atol=1e-9)
        assert (built[1].shape != sy.shape
                or not np.allclose(built[1], sy)), "the move changed nothing"

    def test_an_exact_global_fit_draws_the_line_at_zero(self):
        """Flipped (WP-31 C11b): on the five Foreign rows the global fit
        of degree 4 is exact and Stata's bandwidth is its round-off, which
        the served app emulates and no float emulation can show across
        platforms (the served value itself rests on the BLAS's summation
        order); the saved page drew y = 0 over the kept rows' range, in
        silence.  It now keeps the build's smooth and marks the layer
        (M8), as it marks a layer it does not refit; the name is kept."""
        spec = _spec([plot_for("scatter"), plot_for("lpoly")],
                     {"filter": _MOVES[0][1]})
        r = _render(spec)
        built = _fit_data(r.figures["g1"].renderers)
        _move(r, _MOVES[0][2])
        sx, sy = _fit_data(r.figures["g1"].renderers)
        np.testing.assert_array_equal(sx, built[0])
        np.testing.assert_array_equal(sy, built[1])
        assert not (sy == 0).all()
        _assert_exact_fit_marked(r)

    def test_a_move_leaving_one_row_empties_the_line(self):
        spec = _spec([plot_for("scatter"), plot_for("lpoly")],
                     {"filter": "price, type(slider)"})
        r = _render(spec)
        _move(r, ("Slider", 11385.0))
        x, y = _fit_data(r.figures["g1"].renderers)
        assert len(x) == 0 and len(y) == 0


# ---- WP-31 F1e: lpolyci ----
#
# GAPS3 F1e: an lpolyci on the saved page kept the build's smooth and
# band after a filter move, dimmed and keyed "(unfiltered)" on both,
# while the served app refitted both from the kept rows.  The oracles
# are GlyphMapper.map_lpolyci and _lpoly_se (pinned to Stata's
# ``lpoly, ci se()`` by test_lpolyci_band.py on lpolyci_truth.json and the
# U22 truth block) and the served app after the same move.

#: S19's keys plus lpolyci's own (D-22.a, D-22.d): the pilot width, var()
#: as lpvar, the level and the renderer's role.
_LPCI_KEYS = _LP_KEYS | {"pwidth", "lpvar", "level", "role"}
_LPCI_COLS = ["x_lp", "y_lp", "y_lower", "y_upper"]
_LPCI_TRUTH = os.path.join(_HERE, "fixtures", "lpolyci_truth.json")
with open(_LPCI_TRUTH, encoding="utf-8") as _fh:
    _LPCIT = json.load(_fh)
_LPCI_CASES = {c["id"]: c for c in _LPCIT["cases"]}
#: Every case with Stata's bandwidths (cx_n5, a constant x, has none).
_LPCI_IDS = sorted(k for k, c in _LPCI_CASES.items()
                   if c["bwidth"] is not None and c["pwidth"] is not None)
_LPCI_D4 = {k: set(v) for dv in _LPCIT["divergences"]
            for k, v in dv["rows"].items()}


def _lpci_map(df, opts=None, dataset=None):
    """map_lpolyci's [line, band] on *df*, warnings silenced."""
    gm = _gm()
    if dataset is not None:
        gm.dataset = dataset
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return gm.map_lpolyci(figure(), ColumnDataSource(df), "y", "x",
                              dict(opts or {}))


def _lpci_sample(c):
    """x, y and lpoly's weights of a fixture case (aweights scaled to mean
    1, fweights raw), as test_lpolyci_band.py reads them."""
    D = _LPCIT["datasets"][c["ds"]]
    x = np.array([D[c["x"]][i] for i in c["idx"]], dtype=float)
    y = np.array([D[c["y"]][i] for i in c["idx"]], dtype=float)
    w = None
    if c["w"]:
        w = dr._dash_lpoly_weights(
            np.array([D[c["w"]][i] for i in c["idx"]], dtype=float),
            "fw" if c["wtype"] == "fw" else "aw")
    return x, y, w


class TestLpolyciConfig:
    def test_both_renderers_are_tagged_with_roles(self):
        line_r, band_r = _lpci_map(_FRAME, {"bwidth": "400",
                                            "pwidth": "600"})
        lc, bc = line_r._dash_agg_config, band_r._dash_agg_config
        assert lc["role"] == "line" and bc["role"] == "band"
        assert dict(lc, role=None) == dict(bc, role=None)
        assert line_r._dash_agg_source is line_r.data_source
        assert band_r._dash_agg_source is band_r.data_source
        assert line_r.data_source is not band_r.data_source
        assert line_r._dash_agg_rows == band_r._dash_agg_rows
        json.dumps(lc, allow_nan=False)

    def test_lpolyci_config_keys(self):
        line_r, _b = _lpci_map(_FRAME, {"bwidth": "400", "pwidth": "600",
                                        "lpvar": "4", "level": "90",
                                        "degree": "1", "kernel": "cosine",
                                        "n": "20"})
        cfg = line_r._dash_agg_config
        assert set(cfg) == _LPCI_KEYS
        assert cfg["type"] == "lpolyci" and cfg["cols"] == _LPCI_COLS
        assert (cfg["bwidth"], cfg["pwidth"], cfg["lpvar"]) == (400.0, 600.0,
                                                                4.0)
        assert cfg["level"] == 90.0 and cfg["degree"] == 1
        assert cfg["kernel"] == "cosine" and cfg["n_user"] == 20.0
        d = _lpci_map(_FRAME)[0]._dash_agg_config
        assert (d["bwidth"], d["pwidth"], d["lpvar"]) == (None, None, None)
        assert d["level"] == 95.0 and d["keepmissing"] is False
        assert _lpci_map(_FRAME, {"cmissing": "n"}
                         )[0]._dash_agg_config["keepmissing"] is True

    def test_lpolyci_empty_layer_is_tagged(self):
        line_r, band_r = _lpci_map(_FRAME.iloc[:1])
        assert line_r.data_source.data["x_lp"] == []
        for r, role in ((line_r, "line"), (band_r, "band")):
            assert r._dash_agg_config["type"] == "lpolyci"
            assert r._dash_agg_config["role"] == role
            assert r._dash_agg_source is r.data_source

    @pytest.mark.parametrize("opts", [{"ciplot": "rline"},
                                      {"fitplot": "scatter"}])
    def test_a_band_or_line_drawn_as_another_type_is_not_tagged(self, opts):
        line_r, band_r = _lpci_map(_FRAME, opts)
        assert not hasattr(line_r, "_dash_agg_config")
        assert not hasattr(band_r, "_dash_agg_config")


class TestLpolyciStaleKind:
    def test_lpolyci_is_refit(self):
        assert "lpolyci" in dr._DASH_JS_REFIT_TYPES
        assert dr._dash_stale_kind("lpolyci", {}) is None
        assert dr._dash_stale_kind("lpolyci", {"ciplot": "rline"}) == "fit"
        assert dr._dash_stale_kind("lpolyci", {"fitplot": "scatter"}) == "fit"


_INVNORMAL_P = [0.5, 0.75, 0.9, 0.95, 0.975, 0.995, 0.9995, 0.025, 1e-6]


@requires_node
class TestInvnormal:
    @pytest.mark.parametrize("p", _INVNORMAL_P)
    def test_matches_python(self, p):
        got = _js("dash_invnormal(%r)" % p)
        want = dr._dash_invnormal(p)
        assert abs(got - want) <= 1e-13 * max(1.0, abs(want)), (got, want)

    def test_statas_975(self):
        got = _js("dash_invnormal(0.975)")
        assert abs(got - 1.959963984540054) <= 1e-14

    def test_gammainc(self):
        # P(1/2, x) = erf(sqrt(x)).
        for x in (0.5, 2.0, 10.0, 1e-8, 40.0):
            got = _js("dash_gammainc_p(0.5, %r)" % x)
            assert abs(got - math.erf(math.sqrt(x))) <= 1e-14, (x, got)
        assert _js("dash_gammainc_p(0.5, 0)") == 0
        # P(2, x) = 1 - (1 + x) e^-x.
        for x in (0.3, 3.0, 12.0):
            got = _js("dash_gammainc_p(2, %r)" % x)
            assert abs(got - (1 - (1 + x) * math.exp(-x))) <= 1e-14

    def test_outside_zero_one_is_nan(self):
        assert _js("[dash_invnormal(0), dash_invnormal(1), "
                   "dash_invnormal(-1)]") == [None, None, None]


_SE_CACHE = {}


def _se_pairs():
    """{case id: (JS se, Python _lpoly_se)} at Stata's own bandwidths,
    the JS run once."""
    if not _SE_CACHE:
        calls, want = [], []
        for cid in _LPCI_IDS:
            c = _LPCI_CASES[cid]
            x, y, w = _lpci_sample(c)
            gx = np.asarray(c["gx"], dtype=float)
            var = None if c["var"] is None else float(c["var"])
            calls.append([x.tolist(), y.tolist(), gx.tolist(),
                          float(c["bwidth"]), float(c["pwidth"]),
                          int(c["degree"]), c["kernel"], _lp_list(w), var])
            want.append(dr._lpoly_se(x, y, gx, c["bwidth"], c["pwidth"],
                                     int(c["degree"]), c["kernel"], w, var))
        got = _js_batch("dash_lpoly_se", calls)
        for cid, g, wv in zip(_LPCI_IDS, got, want):
            _SE_CACHE[cid] = (_nan(g), wv)
    return _SE_CACHE


@requires_node
class TestLpolySeTwin:
    @pytest.mark.parametrize("cid", _LPCI_IDS)
    def test_fixture_cases(self, cid):
        js, py = _se_pairs()[cid]
        np.testing.assert_allclose(js, py, rtol=1e-8, atol=1e-10,
                                   equal_nan=True)
        # And Stata's se, where D4 does not name the row.
        st = _nan(_LPCI_CASES[cid]["gse"])
        ok = np.isfinite(st) & np.isfinite(js)
        ok[list(_LPCI_D4.get(cid, ()))] = False
        np.testing.assert_allclose(js[ok], st[ok], rtol=1e-6, atol=1e-9)

    @pytest.mark.parametrize("cid", sorted(set(_LPCIT["no_df"])
                                           & set(_LPCI_IDS)))
    def test_pinch_rows(self, cid):
        # The rows whose pilot has no residual degrees of freedom: the se
        # is exactly 0 where Python's is (D4's pinch), NaN where a window
        # holds fewer than two weighted rows, and var()'s se elsewhere.
        js, py = _se_pairs()[cid]
        rows = _LPCIT["no_df"][cid]
        assert [js[k] == 0.0 for k in rows] == [py[k] == 0.0 for k in rows]
        assert [np.isnan(js[k]) for k in rows] == [np.isnan(py[k])
                                                   for k in rows]

    def test_a_pilot_with_no_df_pinches(self):
        js, py = _se_pairs()["a_d2"]
        assert all(js[k] == 0.0 for k in range(44, 50)), js[44:]

    def test_overflow_guard(self):
        # auto at x0 = 2200, bwidth(500): a pwidth() of 1e-151 squares
        # past DBL_MAX, and Stata's se is missing (_lpoly_se).
        c = _LPCI_CASES["a_d0"]
        x, y, _w = _lpci_sample(c)
        args = [x.tolist(), y.tolist(), [2200.0], 500.0, 1e-151, 0,
                "epanechnikov", None, None]
        assert np.isnan(dr._lpoly_se(x, y, [2200.0], 500.0, 1e-151, 0,
                                     "epanechnikov")[0])
        assert _js_batch("dash_lpoly_se", [args]) == [[None]]


def _lpci_case(df, opts, dataset=None):
    """The branch's two roles against map_lpolyci's two sources."""
    line_r, band_r = _lpci_map(df, opts, dataset)
    x, y, w = _rows(df, opts)
    got = js_runner.run_fit_js_block_roles(line_r._dash_agg_config, x, y, w)
    for role, r, cols in (("line", line_r, _LPCI_COLS[:2]),
                          ("band", band_r, _LPCI_COLS)):
        data = r.data_source.data
        assert set(got[role]) == set(data), (role, sorted(got[role]))
        for c in cols:
            np.testing.assert_allclose(_nan(got[role][c]),
                                       np.asarray(data[c], float),
                                       rtol=1e-8, atol=1e-10, equal_nan=True,
                                       err_msg="%s %s" % (role, c))
    return got


_LPCI_BRANCH = [
    ("default", _FRAME, {}, None),
    ("degree(1) bwidth(400) pwidth(600) level(90)", _FRAME,
     {"degree": "1", "bwidth": "400", "pwidth": "600", "level": "90"}, None),
    ("var(4) aw", _FRAME, {"lpvar": "4", "weight": "aweight", "wexp": "w"},
     None),
    ("cosine fw", _FRAME, {"kernel": "cosine", "weight": "fweight",
                           "wexp": "w"}, None),
    ("degree(2) bwidth(500) n(20) of 60", _LP_FRAME60.iloc[:25],
     {"degree": "2", "bwidth": "500", "n": "20"}, _LP_FRAME60),
    ("bwidth(60) pwidth(60) leaves gaps", _FRAME,
     {"bwidth": "60", "pwidth": "60"}, None),
    ("bwidth(60) cmissing(n)", _FRAME, {"bwidth": "60", "pwidth": "60",
                                        "cmissing": "n"}, None),
    ("stairstep", _FRAME, {"connect": "stairstep"}, None),
    ("one row", _FRAME.iloc[:1], {}, None),
    ("x of 0 and 1 only: the line at 0, no band", _FRAME.assign(
        x=(np.arange(30) % 2).astype(float)), {}, None),
]


@requires_node
class TestLpolyciBranch:
    @pytest.mark.parametrize("df,opts,dataset",
                             [c[1:] for c in _LPCI_BRANCH],
                             ids=[c[0] for c in _LPCI_BRANCH])
    def test_matches_python(self, df, opts, dataset):
        _lpci_case(df, opts, dataset)

    def test_one_row_writes_empty_columns(self):
        got = _lpci_case(_FRAME.iloc[:1], {})
        assert got["line"] == {"x_lp": [], "y_lp": []}
        assert all(v == [] for v in got["band"].values())

    def test_x_of_two_values_draws_zero_and_no_band(self):
        got = _lpci_case(_FRAME.assign(x=(np.arange(30) % 2).astype(float)),
                         {})
        assert got["line"]["y_lp"] == [0.0] * 30
        assert got["band"]["x_lp"] == []

    def test_the_cache_serves_both_roles(self):
        line_r, _b = _lpci_map(_FRAME, {"bwidth": "150", "pwidth": "40"})
        x, y, w = _rows(_FRAME, {})
        got = js_runner.run_fit_js_block_roles(line_r._dash_agg_config, x,
                                               y, w)
        assert got["cache_size"] == 1
        line, band = got["line"], got["band"]
        assert len(band["x_lp"]) < len(line["x_lp"])
        at = {xv: yv for xv, yv in zip(line["x_lp"], line["y_lp"])}
        assert all(at[xv] == yv for xv, yv in zip(band["x_lp"],
                                                  band["y_lp"]))


def _lpci_data(renderers):
    """{"line": (x, y), "band": the four columns} of the one lpolyci layer
    among *renderers*: its line reads x_lp/y_lp alone, its band the four."""
    lines = [r for r in renderers if isinstance(r, GlyphRenderer)
             and isinstance(r.glyph, Line) and "x_lp" in r.data_source.data
             and "y_lower" not in r.data_source.data]
    bands = [r for r in renderers if isinstance(r, GlyphRenderer)
             and type(r.glyph).__name__ == "VArea"
             and "y_lower" in r.data_source.data]
    assert len(lines) == 1 and len(bands) == 1, (len(lines), len(bands))
    ld, bd = lines[0].data_source.data, bands[0].data_source.data
    return {"line": {c: np.asarray(ld[c], dtype=float)
                     for c in _LPCI_COLS[:2]},
            "band": {c: np.asarray(bd[c], dtype=float) for c in _LPCI_COLS}}


def _served_lpci_after(spec, action):
    doc, _ = _served(spec)
    kind, want = action
    w = [m for m in _widgets_of(doc) if type(m).__name__ == kind][0]
    if kind == "Select":
        want = [v for v, lab in w.options if lab == want][0]
    _fire(w, want)
    return _lpci_data([m for m in doc.models if isinstance(m, GlyphRenderer)])


#: (name, plots, move): a saved lpolyci after a move equals the served
#: one.  The default bandwidth on the five Foreign rows is an exact global
#: fit (C11b), so the dropdown move is given a bandwidth here.
_LPCI_REFIT = [
    ("lpolyci bwidth(400) pwidth(600)",
     [plot_for("scatter"), plot_for("lpolyci", {"bwidth": "400",
                                                "pwidth": "600"})],
     _MOVES[0]),
    ("lpolyci", [plot_for("scatter"), plot_for("lpolyci")], _MOVES[1]),
    ("lpolyci", [plot_for("scatter"), plot_for("lpolyci")], _MOVES[2]),
    ("lpolyci degree(1) bwidth(400) pwidth(600) level(90)",
     [plot_for("lpolyci", {"degree": "1", "bwidth": "400", "pwidth": "600",
                           "level": "90"})], _MOVES[1]),
    ("lpolyci var(4) [aw=weight]",
     [plot_for("lpolyci", {"lpvar": "4", "weight": "aweight",
                           "wexp": "weight"})], _MOVES[2]),
    # pwidth() given too (WP-31 C11b): the default pilot is 1.5 times the
    # rule of thumb, an exact fit on the Foreign rows, which the page marks.
    ("lpolyci cosine [fw=rep] bwidth(500) pwidth(750)",
     [plot_for("lpolyci", {"kernel": "cosine", "weight": "fweight",
                           "wexp": "rep", "bwidth": "500",
                           "pwidth": "750"})], _MOVES[0]),
]


@requires_node
class TestTheSavedLpolyciRefits:
    @pytest.mark.parametrize("plots,move", [c[1:] for c in _LPCI_REFIT],
                             ids=["%s-%s" % (c[0], c[2][0])
                                  for c in _LPCI_REFIT])
    def test_saved_equals_served(self, plots, move):
        _, filt, action, _oracle = move
        spec = _spec(plots, {"filter": filt})
        r = _render(spec)
        built = _lpci_data(r.figures["g1"].renderers)
        _move(r, action)
        saved = _lpci_data(r.figures["g1"].renderers)
        served = _served_lpci_after(spec, action)
        for role, cols in (("line", _LPCI_COLS[:2]), ("band", _LPCI_COLS)):
            for c in cols:
                np.testing.assert_allclose(saved[role][c], served[role][c],
                                           rtol=1e-8, atol=1e-9,
                                           equal_nan=True,
                                           err_msg="%s %s" % (role, c))
        assert (built["line"]["y_lp"].shape != saved["line"]["y_lp"].shape
                or not np.allclose(built["line"]["y_lp"],
                                   saved["line"]["y_lp"])), \
            "the move changed nothing"

    def test_a_move_leaving_one_row_empties_both(self):
        spec = _spec([plot_for("scatter"), plot_for("lpolyci")],
                     {"filter": "price, type(slider)"})
        r = _render(spec)
        _move(r, ("Slider", 11385.0))
        got = _lpci_data(r.figures["g1"].renderers)
        assert all(len(v) == 0 for v in got["line"].values())
        assert all(len(v) == 0 for v in got["band"].values())


# ---- WP-31 C11b: an exactly fitted rule of thumb is marked ----
#
# Where lpoly's rule-of-thumb global fit is exact (y an exact polynomial
# in x, or no more rows than its coefficients), Stata's r(bwidth) is the
# round-off of its float arithmetic.  The served app emulates it
# (_lpoly_rot_float); a JavaScript port agrees on 8 of the fixture's 48
# such rows, since numpy's matrix-vector products do not sum in a fixed
# order (measured: A @ v differs from the sequential sum by 2.8e-17) and
# the round-off is the whole of the residual.  So the saved page keeps
# the build's smooth there and marks the layer with the stale cue after
# a move (M8), never drawing y = 0 in silence.


def _assert_exact_fit_marked(r, key="g1"):
    """The lpoly/lpolyci layer of *key* is dimmed, keyed "(unfiltered)"
    and the caption shown."""
    from test_saved_stale_cue import _items_of as _its, _one_cue as _cue1
    f = r.figures[key]
    rends = [x for x in f.renderers
             if getattr(x, "_dash_frozen", None) is not None]
    assert rends and all(x.muted for x in rends), [x.muted for x in rends]
    assert _cue1(r, key).visible is True
    items = _its(f, rends)
    assert items and all(
        str(getattr(i.label, "value", i.label)).endswith(" (unfiltered)")
        for i in items)


@requires_node
class TestTheRotFlagsAnExactFit:
    def test_every_float_row_is_flagged_and_no_other(self):
        calls, routes = [], []
        for row in _LPT["rows"]:
            x, y, w = _lp_sample(row)
            calls.append([x.tolist(), y.tolist(), _lp_list(w),
                          row["degree"], row["kernel"]])
            routes.append(_rot_pairs()[row["id"]][1]["route"])
        got = run_js(_fit_js() + "\nconst _calls = " + json.dumps(calls)
                     + ";\nprocess.stdout.write(JSON.stringify(_calls.map("
                     "a => { const o = {}; dash_lpoly_rot(...a, o); "
                     "return !!o.exact; })));")
        assert [i for i, g in enumerate(got) if g] == [
            i for i, rt in enumerate(routes) if rt == "float"]

    def test_every_divergent_row_is_flagged(self):
        flagged = set()
        for row, (js, det) in zip(_LPT["rows"], [_rot_pairs()[r["id"]]
                                                  for r in _LPT["rows"]]):
            if not _rot_agrees(js, det, 1e-6):
                assert det["route"] == "float", row["id"]
                flagged.add(row["id"])
        assert len(flagged) == _ROT_DIVERGENT_COUNT


@requires_node
class TestTheExactFitIsMarked:
    def test_lpolyci_keeps_its_build_and_is_marked(self):
        spec = _spec([plot_for("scatter"), plot_for("lpolyci")],
                     {"filter": _MOVES[0][1]})
        r = _render(spec)
        built = _lpci_data(r.figures["g1"].renderers)
        _move(r, _MOVES[0][2])
        got = _lpci_data(r.figures["g1"].renderers)
        for role in ("line", "band"):
            for c, v in got[role].items():
                np.testing.assert_array_equal(v, built[role][c])
        _assert_exact_fit_marked(r)

    def test_lpolyci_with_a_bwidth_and_a_default_pilot_is_marked(self):
        # bwidth() given, pwidth() not: the pilot is 1.5 times the rule
        # of thumb, exact on the Foreign rows, so the band is the build's.
        spec = _spec([plot_for("scatter"),
                      plot_for("lpolyci", {"bwidth": "400"})],
                     {"filter": _MOVES[0][1]})
        r = _render(spec)
        _move(r, _MOVES[0][2])
        _assert_exact_fit_marked(r)

    @pytest.mark.parametrize("plot", [
        plot_for("lpoly", {"bwidth": "400"}),
        plot_for("lpolyci", {"bwidth": "400", "pwidth": "600"})],
        ids=["lpoly bwidth", "lpolyci bwidth pwidth"])
    def test_given_widths_are_never_conditional(self, plot):
        r = _render(_spec([plot_for("scatter"), plot],
                          {"filter": _MOVES[0][1]}))
        assert not any(hasattr(x, "_dash_frozen")
                       for x in r.figures["g1"].renderers)

    def test_a_move_the_rule_of_thumb_survives_marks_nothing(self):
        # The range move leaves an inexact global fit: refitted, unmarked.
        spec = _spec([plot_for("scatter"), plot_for("lpoly")],
                     {"filter": _MOVES[1][1]})
        r = _render(spec)
        _move(r, _MOVES[1][2])
        f = r.figures["g1"]
        rends = [x for x in f.renderers
                 if getattr(x, "_dash_frozen", None) is not None]
        assert rends and not any(x.muted for x in rends)
        sx, sy = _fit_data(f.renderers)
        vx, vy = _served_fit_after(spec, _MOVES[1][2])
        np.testing.assert_allclose(sy, vy, rtol=1e-8, atol=1e-9)

    def test_rot_conditional(self):
        lp = _map("lpoly", _FRAME)
        assert dr.GlyphMapper._rot_conditional([lp])
        assert not dr.GlyphMapper._rot_conditional(
            [_map("lpoly", _FRAME, {"bwidth": "400"})])
        assert dr.GlyphMapper._rot_conditional(
            _lpci_map(_FRAME, {"bwidth": "400"}))
        assert dr.GlyphMapper._rot_conditional(
            _lpci_map(_FRAME, {"pwidth": "600"}))
        assert not dr.GlyphMapper._rot_conditional(
            _lpci_map(_FRAME, {"bwidth": "400", "pwidth": "600"}))
        assert not dr.GlyphMapper._rot_conditional(
            [_map("lfit", _FRAME), _map("lpoly", _FRAME,
                                        {"recast": "scatter"})])
        assert not dr.GlyphMapper._rot_conditional([])

    def test_the_conditional_config_pairs_the_layer_and_its_mark(self):
        r = _render(_spec([plot_for("scatter"), plot_for("lpolyci")],
                          {"filter": _MOVES[0][1]}))
        cb = r.filter_callbacks[0]
        aggs = [c for c in json.loads(cb.args["agg_configs_json"])
                if c["type"] == "lpolyci"]
        stale = json.loads(cb.args["stale_configs_json"])
        assert len(aggs) == 2 and len(stale) == 1
        assert aggs[0]["mark"] == aggs[1]["mark"] == stale[0]["cond"]
