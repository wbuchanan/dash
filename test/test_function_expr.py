"""test_function_expr.py -- a function layer draws twoway's points (WP-29 P0.6).

dash used to evaluate ``function y = <exp>`` itself, by rewriting Stata's
``^`` to Python's ``**`` and handing the text to ``eval``.  Stata's grammar
was lost: ``2^3^x`` drew 2 8 512 where twoway draws 1 8 64, ``pi*x`` drew
where twoway refuses it, and ``normalden(x)`` drew nothing where twoway
draws it.  Stata now evaluates the expression at registration, with the
generator twoway itself calls (twoway__function_gen), and stores the points
beside the graph (``"function_points"`` in the spec); both renderers draw
those numbers and never evaluate the expression.  A spec without points (one
written by hand) is drawn by a small interpreter of Stata's grammar and
missing-value rules (``_stata_fn_parse``/``_stata_fn_eval``).

The truth is twoway's own: ``test/fixtures/function_expr_truth.json``,
written by ``scripts/extract_function_truth.do`` (twoway's serset and the
generator's r(min), r(delta) and y for each probe, with twoway's rc).

Every test runs in both modes: the saved page (``DashRenderer``) and the
served app (``ServerAppBuilder``'s generated module).

P1.22 is closed by disposition (WP-30, maintainer decision M12): a graph
registered in Stata is always drawn from Stata's points, and the fallback
keeps its ten functions; a layer it cannot draw gives one note naming what
it needs and the function or name it met (``GlyphMapper._mark_needs_points``,
``GlyphMapper._needs_points_why``).
"""

import ast
import copy
import inspect
import itertools
import json
import math
import os
import re
import sys
import tempfile
import textwrap
import time
import warnings

import numpy as np
import pytest
from bokeh.document import Document
from bokeh.embed import file_html
from bokeh.models import CustomJS, Plot, Select
from bokeh.plotting import figure
from bokeh.resources import CDN

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import load_app  # noqa: E402
import test_mode_parity as mp  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "function_expr_truth.json")
_SEQ = itertools.count()
_TMP = tempfile.mkdtemp(prefix="dash_fnexpr_")
MODES = ["saved", "served"]

#: Probes twoway accepts that the points-free fallback does not know: they
#: are drawn from stored points only.
#: The fallback's ^ and transcendental functions may differ from Stata's by
#: about 1 ulp (Stata's 2^0.5 is 1.414213562373095); rtol 1e-15 holds
#: everywhere but in a power tower, where each step's ulp is raised to the
#: next exponent: ((1.25^9)^9)^9 is 4.440168821029654e+70 in numpy and
#: 4.440168821029662e+70 in Stata (1.8e-15 apart).
_RTOL = {"y = x^9^9^9": 1e-13}

_FALLBACK_UNSUPPORTED = {"y = c(pi)*x", "y = normalden(x)", "y = ln(x)",
                         "y = 1.8X+01*x", "y = (x>1)*x", "y = max(x,1)"}

#: The refusals of twoway (E3, u06 truth): each draws nothing in a spec
#: without points.
_REFUSED = ["pi*x", "e*x", "pi", "e", "PI", "E", "x**2", "x%2", "x//1", "+x",
            "2*+x", "(+x)", "x^", "2^^x", "ｓｉｎ(x)", "2x",
            "sin(x,1)", "sin (x)"]

#: WP-30 P1.22: what a spec without points meets, and the tail of the one
#: note it gives -- the first function the fallback refuses, the first bare
#: name, or neither (the tokenizer reads left to right, so the first
#: refusal decides).
_NEEDS_STATA_FUNCS = {"normalden(x)": "normalden", "normal(x)": "normal",
                      "ln(x)": "ln", "c(pi)*x": "c",
                      "cond(x>1,x,0)": "cond", "min(x,1)": "min",
                      "max(x,1)": "max", "round(x)": "round",
                      "int(x-1)": "int", "scalar(s)*x": "scalar",
                      "invlogit(x)": "invlogit",
                      "__import__('os')": "__import__"}
_NEEDS_STATA_NAMES = {"pi*x": "pi", "e*x": "e", "PI": "PI", "E": "E",
                      "s*x": "s", "_b[_cons]+_b[weight]*x": "_b",
                      "sin (x)": "sin"}
_NO_NAME = ["x>1", "(x>1)*x", "x^", "sin(x,1)", "2x", "ｓｉｎ(x)",
            "1>normalden(x)", "x**2"]
_HEAD = ("dash: graph 'g1' plot 1 (function) drew nothing: it needs the "
         "points Stata computes for it when dash registers the graph")
_KNOWS = ("without them dash evaluates only x, _pi, numbers, + - * / ^ and "
          "sin(), cos(), tan(), exp(), log(), log10(), sqrt(), abs(), "
          "floor() and ceil()")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fixture():
    if not os.path.exists(_FIXTURE):
        pytest.fail(f"missing fixture {_FIXTURE}: run "
                    f"scripts/extract_function_truth.do")
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _num(v):
    return None if v is None else float(v)


def _floats(vals):
    return np.array([np.nan if v is None else float(v) for v in vals],
                    dtype=float)


def _fn_plot(expr, rng="0 2", n="3", points=None):
    p = {"type": "function", "expr": expr,
         "options": {"range": rng, "n": str(n)}}
    if points is not None:
        p["points"] = points
    return p


def _write(spec, raw=None):
    """Write *spec* (with each ``raw`` sentinel string replaced by its JSON
    text) and the parity data; return the two paths."""
    tag = next(_SEQ)
    sp = os.path.join(_TMP, f"spec_{tag}.json")
    dp = os.path.join(_TMP, f"data_{tag}.json")
    text = json.dumps(spec)
    for k, v in (raw or {}).items():
        text = text.replace(json.dumps(k), v)
    with open(sp, "w", encoding="utf-8") as fh:
        fh.write(text)
    with open(dp, "w") as fh:
        json.dump(mp.make_data_json(mp._DF, mp._VALUE_LABELS,
                                    mp._LABEL_NAMES), fh)
    return tag, sp, dp


def _render(mode, spec, raw=None, spy=None):
    """``(models, warnings, module)`` of *spec* drawn in *mode*.

    *spy*, a callable ``spy(target)`` -> restore function, is applied to the
    module whose ``_stata_fn_parse`` the drawing calls: ``dash_render`` when
    saved, the generated app's own module when served (amendment A9: a spy
    on ``dash_render`` sees nothing the served app does).
    """
    tag, sp, dp = _write(spec, raw)
    if mode == "saved":
        undo = spy(dr) if spy else None
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                r = dr.DashRenderer(sp, dp)
                r.render()      # the page: a test serialises its document
        finally:
            if undo:
                undo()
        root = r._last_layout_root
        return (list(root.references()),
                [str(w.message) for w in caught], None)
    ap = os.path.join(_TMP, f"app_{tag}.py")
    with warnings.catch_warnings(record=True) as built:
        warnings.simplefilter("always")
        dr.ServerAppBuilder(sp, dp).build(ap)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mod = load_app(ap, f"_fnexpr_{tag}")
    undo = spy(mod) if spy else None
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            doc = Document()
            mod.make_document(doc)
    finally:
        if undo:
            undo()
    models = []
    for root in doc.roots:
        models.extend(root.references())
    mod._dash_test_doc = doc
    return (models, [str(w.message) for w in list(built) + list(caught)],
            mod)


def _fn_sources(models, title=None):
    """The function ColumnDataSources (data holds ``x_fn``), by figure."""
    out = []
    for m in models:
        if not isinstance(m, Plot):
            continue
        if title is not None and (m.title is None or m.title.text != title):
            continue
        for g in m.renderers:
            src = getattr(g, "data_source", None)
            if src is not None and "x_fn" in src.data:
                out.append(src)
    return out


def _xy(models, title=None):
    srcs = _fn_sources(models, title)
    assert len(srcs) == 1, f"expected one function source, got {len(srcs)}"
    d = srcs[0].data
    return (np.asarray(list(d["x_fn"]), dtype=float),
            np.asarray(list(d["y_fn"]), dtype=float))


def _empty_notes(warns, gname="g1"):
    return [w for w in warns if "drew nothing" in w
            and (gname is None or f"'{gname}'" in w)]


def _draw(mode, expr, rng="0 2", n="3", points=None, raw=None, fp=None,
          bo=None):
    spec = mp._spec([_fn_plot(expr, rng, n, points)], build_options=bo)
    if fp is not None:
        spec["function_points"] = fp
    models, warns, mod = _render(mode, spec, raw)
    x, y = _xy(models)
    return x, y, warns, mod


def _same(a, b):
    return np.array_equal(np.asarray(a, dtype=float),
                          np.asarray(b, dtype=float), equal_nan=True)


def _bridged(vals):
    """The points twoway's line joins: *vals* less its missing values.
    WP-30 P1.8a: under the default cmissing(y) a function's missing
    points are bridged, so the drawn source leaves them out; a value
    where Stata has a missing one is still an extra point."""
    a = np.asarray(vals, dtype=float)
    return a[~np.isnan(a)]


def _points_of(probe):
    return {"x0": _num(probe["x0"]), "dx": _num(probe["dx"]),
            "y": [_num(v) for v in probe["gen_y"]]}


def _has_plain_arith(expr):
    """No ``^`` and no function call: the fallback is exact there."""
    body = expr.split("=", 1)[1]
    return "^" not in body and not re.search(r"[A-Za-z]\w*\(", body)


# ---------------------------------------------------------------------------
# Stored points
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", MODES)
class TestStoredPoints:
    def test_the_points_are_drawn_not_the_expression(self, mode):
        x, y, warns, _ = _draw(mode, "nosuch(x)",
                               points={"x0": 0, "dx": 1, "y": [1, 8, 64]})
        assert list(x) == [0.0, 1.0, 2.0]
        assert list(y) == [1.0, 8.0, 64.0]
        assert not _empty_notes(warns)

    def test_points_travel_beside_the_graphs(self, mode):
        x, y, _w, _ = _draw(
            mode, "2^3^x",
            fp={"g1": {"1": {"x0": 0, "dx": 1, "y": [1, 8, 64]}}})
        assert list(y) == [1.0, 8.0, 64.0]
        assert list(x) == [0.0, 1.0, 2.0]

    def test_the_points_survive_a_filter_move(self, mode):
        spec = mp._spec([_fn_plot("2^3^x"), mp._sc()],
                        build_options={"filter": "foreign, type(dropdown)"})
        spec["function_points"] = {
            "g1": {"1": {"x0": 0, "dx": 1, "y": [1, 8, 64]}}}
        models, _w, mod = _render(mode, spec)
        if mode == "saved":
            # Guard: the saved page never recomputes a function: its source
            # is referenced by no CustomJS, so a filter move cannot change it.
            # The axis re-finish and zoom code only read it (WP-30 P1.3a).
            (src,) = _fn_sources(models)
            for m in models:
                if isinstance(m, CustomJS):
                    for k, v in m.args.items():
                        if k == "axis_models" or (
                                k == "models" and "plan_json" in m.args):
                            continue
                        vals = v if isinstance(v, (list, tuple)) else [v]
                        assert all(getattr(u, "id", None) != src.id
                                   for u in vals)
            return
        doc = mod._dash_test_doc
        sel = [w for w in mp._widgets_of(doc) if isinstance(w, Select)]
        assert sel, "no Select in the served document"
        raw = [v for v, lab in sel[0].options if lab == "Foreign"]
        mp._fire(sel[0], raw[0])
        after = []
        for root in doc.roots:
            after.extend(root.references())
        _x, y = _xy(after)
        assert list(y) == [1.0, 8.0, 64.0]

    def test_null_points_draw_silently(self, mode):
        x, y, warns, _ = _draw(mode, "nosuch(x)",
                               points={"x0": 0, "dx": 1,
                                       "y": [None, None, None]})
        assert len(y) == 3 and np.isnan(y).all()
        assert list(x) == [0.0, 1.0, 2.0]
        assert not _empty_notes(warns)

    def test_an_unevaluable_expression_beside_points_is_never_parsed(
            self, mode):
        calls = []

        def spy(target):
            real = getattr(target, "_stata_fn_parse", None)

            def counting(text):
                calls.append(text)
                return real(text)
            target._stata_fn_parse = counting

            def undo():
                if real is None:
                    del target._stata_fn_parse
                else:
                    target._stata_fn_parse = real
            return undo

        spec = mp._spec([_fn_plot("__import__('os').system('true')",
                                  points={"x0": 0, "dx": 1,
                                          "y": [1, 8, 64]})])
        models, _w, _ = _render(mode, spec, spy=spy)
        _x, y = _xy(models)
        assert list(y) == [1.0, 8.0, 64.0]
        assert calls == []
        # The instrument is live: a points-free layer IS parsed.
        spec2 = mp._spec([_fn_plot("x")])
        _render(mode, spec2, spy=spy)
        assert calls == ["x"]


class TestStoredPointsExact:
    def test_x_is_rebuilt_exactly(self):
        for p in _fixture()["probes"]:
            if p["rc"] != 0:
                continue
            x = float(p["x0"]) + float(p["dx"]) * np.arange(p["n"],
                                                             dtype=float)
            assert sorted(x) == [float(v) for v in p["serset_x"]], p["id"]


# ---------------------------------------------------------------------------
# Hostile points
# ---------------------------------------------------------------------------

_HOSTILE = {
    "y a string": ({"x0": 0, "dx": 1, "y": "1,8,64"}, None),
    "y with True": ({"x0": 0, "dx": 1, "y": [1, True, 3]}, None),
    "y a dict": ({"x0": 0, "dx": 1, "y": {"a": 1}}, None),
    "nested list": ({"x0": 0, "dx": 1, "y": [[1], [2], [3]]}, None),
    "10001 values": ({"x0": 0, "dx": 1, "y": [1.0] * 10001}, None),
    "a NaN": ({"x0": 0, "dx": 1, "y": [1, "__NAN__", 3]},
              {"__NAN__": "NaN"}),
    "Infinity": ({"x0": 0, "dx": 1, "y": [1, "__INF__", 3]},
                 {"__INF__": "Infinity"}),
    "1e400": ({"x0": 0, "dx": 1, "y": [1, "__BIG__", 3]},
              {"__BIG__": "1e400"}),
    "10**400": ({"x0": 0, "dx": 1, "y": [1, 10 ** 400, 3]}, None),
    "dx Infinity": ({"x0": 0, "dx": "__INF__", "y": [1, 2, 3]},
                    {"__INF__": "Infinity"}),
    "no x0": ({"dx": 1, "y": [1, 2, 3]}, None),
    "x0 True": ({"x0": True, "dx": 1, "y": [1, 2, 3]}, None),
    "points a list": ([0, 1, [1, 2, 3]], None),
}


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("case", sorted(_HOSTILE))
class TestHostilePoints:
    def test_bad_points_draw_nothing(self, case, mode):
        points, raw = _HOSTILE[case]
        x, y, warns, _ = _draw(mode, "x", points=points, raw=raw)
        assert len(x) == 0 and len(y) == 0, f"{case}: drew {list(y)[:5]}"
        assert len(_empty_notes(warns)) == 1, warns


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------

class TestAttach:
    def test_the_transport(self):
        attach = getattr(dr, "_dash_attach_function_points")
        P1 = {"x0": 0, "dx": 1, "y": [1]}
        P3 = {"x0": 0, "dx": 1, "y": [3]}
        bad = {"x0": 0, "dx": 1, "y": [9]}
        fn = {"type": "function", "expr": "x", "options": {}}
        FN = {"type": "Function", "expr": "x", "options": {}}
        sc = {"type": "scatter", "yvar": "mpg", "xvar": "weight"}
        spec = {
            "graphs": [
                {"name": "g1", "graph_options": {"name": "g1"},
                 "plots": [dict(fn), dict(sc), dict(FN)]},
                {"name": "g1", "graph_options": {"name": "g1"},
                 "plots": [dict(fn)]},
                {"name": "g2", "graph_options": {"name": "g2"},
                 "plots": [dict(fn)]},
            ],
            "function_points": {
                "g1": {"1": P1, "3": P3, "0": bad, "4": bad, "01x": bad,
                       "١": bad, "2": bad},
                "g2": "not a table",
            },
        }
        before = copy.deepcopy(spec)
        out = attach(spec)
        assert spec == before, "the input was mutated"
        assert "function_points" not in out
        g1 = out["graphs"][0]["plots"]
        assert g1[0]["points"] == P1
        assert "points" not in g1[1]
        assert g1[2]["points"] == P3
        assert "points" not in out["graphs"][1]["plots"][0]
        assert "points" not in out["graphs"][2]["plots"][0]
        # A spec without the member comes back equal.
        plain = {"graphs": [{"name": "a", "plots": [dict(fn)]}]}
        assert attach(plain) == plain


class TestFunctionPoints:
    def test_valid_and_invalid(self):
        fp = getattr(dr, "_dash_function_points")
        x, y = fp({"x0": 2, "dx": -1, "y": [4, None, 0]})
        assert list(x) == [2.0, 1.0, 0.0]
        assert _same(y, [4.0, np.nan, 0.0])
        x, y = fp({"x0": 0.0, "dx": 0.5, "y": [1.5]})
        assert list(x) == [0.0] and list(y) == [1.5]
        for bad in (None, [], "x", {"x0": 0, "dx": 1, "y": []},
                    {"x0": 0, "dx": 1, "y": [1] * 10001},
                    {"x0": 0, "dx": 1, "y": [float("nan")]},
                    {"x0": 0, "dx": 1, "y": [float("inf")]},
                    {"x0": 0, "dx": 1, "y": [10 ** 400]},
                    {"x0": 0, "dx": float("inf"), "y": [1]},
                    {"x0": float("nan"), "dx": 1, "y": [1]},
                    {"x0": 0, "dx": 1, "y": [True]},
                    {"x0": False, "dx": 1, "y": [1]},
                    {"x0": "0", "dx": 1, "y": [1]},
                    {"x0": 1e308, "dx": 1e308, "y": [1, 2, 3]},
                    {"dx": 1, "y": [1]}):
            assert fp(bad) is None, bad
        assert fp({"x0": 0, "dx": 1, "y": [1, 2, 3]}, n_cap=2) is None


# ---------------------------------------------------------------------------
# The fallback: Stata's grammar for a spec without points
# ---------------------------------------------------------------------------

_SIGN_AFTER_CARET = {
    "2^-1^2": [.25, .25, .25],
    "x^2^-1": [np.nan, 1, .25],
    "-x^-x^-1": [-1, -1, -4],
    "2^-x^2": [1, .25, .0625],
    "-2^-2^-2": [-16, -16, -16],
    "2^-2^-1": [4, 4, 4],
    "x^-1^-1": [np.nan, 1, 2],
    "2^+1": [2, 2, 2],
}

_UNARY = {
    "-2^2": [-4, -4, -4],
    "-x^2": [0, -1, -4],
    "3-2^2": [-1, -1, -1],
    "x*-2^2": [0, -4, -8],
    "2--x": [2, 3, 4],
    "2/-x": [np.nan, -2, -1],
}

_MISSING = ["x^.", ".", "(0^-1)^0+x", "1/(1/0)+x", "exp(-exp(1000))+x"]


@pytest.mark.parametrize("mode", MODES)
class TestStataGrammarFallback:
    def test_caret_is_left_associative(self, mode):
        _x, y, _w, _ = _draw(mode, "2^3^x")
        assert list(y) == [1.0, 8.0, 64.0]

    @pytest.mark.parametrize("expr", sorted(_SIGN_AFTER_CARET))
    def test_a_sign_after_caret_takes_one_operand(self, expr, mode):
        _x, y, _w, _ = _draw(mode, expr)
        assert _same(_bridged(y), _bridged(_SIGN_AFTER_CARET[expr])), (
            expr, list(y))

    @pytest.mark.parametrize("expr", sorted(_UNARY))
    def test_unary_minus_binds_looser_than_caret(self, expr, mode):
        _x, y, _w, _ = _draw(mode, expr)
        assert _same(_bridged(y), _bridged(_UNARY[expr])), (expr, list(y))

    def test_division_binds_tighter_than_multiplication(self, mode):
        _x, y, _w, _ = _draw(mode, "0.1*3/0.3")
        assert list(y) == [1.0, 1.0, 1.0]

    def test_subtraction_binds_tighter_than_addition(self, mode):
        _x, y, _w, _ = _draw(mode, "1e16+1-2")
        assert list(y) == [1e16] * 3
        _x, y, _w, _ = _draw(mode, "1+0.1-0.7")
        assert list(y) == [0.40000000000000002] * 3

    @pytest.mark.parametrize("expr", _REFUSED)
    def test_what_twoway_refuses_draws_nothing(self, expr, mode):
        x, y, warns, _ = _draw(mode, expr)
        assert len(y) == 0, (expr, list(y))
        assert len(_empty_notes(warns)) == 1, warns

    def test_underscore_pi_is_statas_pi(self, mode):
        _x, y, _w, _ = _draw(mode, "_pi*x")
        assert list(y) == [0.0, math.pi, 2 * math.pi]

    @pytest.mark.parametrize("expr", _MISSING)
    def test_missing_propagates_as_in_stata(self, expr, mode):
        _x, y, warns, _ = _draw(mode, expr)
        assert len(y) == 3 and np.isnan(y).all(), (expr, list(y))
        assert not _empty_notes(warns)


# ---------------------------------------------------------------------------
# Against twoway's fixture
# ---------------------------------------------------------------------------

class TestTheFixture:
    def test_meta_keys(self):
        meta = _fixture()["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted"):
            assert meta.get(k), k


def _probe_spec(probes, with_points):
    graphs = []
    for p in probes:
        rng = p["range"]
        plot = _fn_plot(p["expr"].split("=", 1)[1].strip(), rng, p["n"],
                        _points_of(p) if with_points else None)
        graphs.append((p["id"], [plot], {"title": p["id"]}))
    return mp._spec(graphs=graphs)


def _render_probes(mode, probes, with_points, chunk=40):
    """The probes drawn, one graph each, in dashboards of at most *chunk*
    graphs (under dash's graphs limit); models and warnings merged."""
    models, warns = [], []
    for i in range(0, len(probes), chunk):
        m, w, _ = _render(mode, _probe_spec(probes[i:i + chunk], with_points))
        models.extend(m)
        warns.extend(w)
    return models, warns


@pytest.mark.parametrize("mode", MODES)
class TestAgainstTheFixture:
    def test_every_stored_probe(self, mode):
        probes = [p for p in _fixture()["probes"] if p["rc"] == 0]
        models, _w = _render_probes(mode, probes, True)
        bad = []
        for p in probes:
            x, y = _xy(models, p["id"])
            gy = _floats(p["gen_y"])
            if not _same(_bridged(y), _bridged(gy)):
                bad.append((p["id"], "y", list(y)[:4]))
            # The x of each joined point (gen_y and serset_x share an order).
            want_x = [float(v) for v, w in zip(p["serset_x"], gy)
                      if not np.isnan(w)]
            got_x = [float(v) for v, w in zip(x, np.asarray(y, dtype=float))
                     if not np.isnan(w)]
            if sorted(got_x) != want_x:
                bad.append((p["id"], "x", list(x)[:4]))
        assert not bad, bad

    def test_every_fallback_probe(self, mode):
        parse = getattr(dr, "_stata_fn_parse")
        probes = _fixture()["probes"]
        models, warns = _render_probes(mode, probes, False)
        bad = []
        for p in probes:
            text = p["expr"].split("=", 1)[1].strip()
            x, y = _xy(models, p["id"])
            notes = _empty_notes(warns, p["id"])
            try:
                parse(text)
                accepted = len(text) <= dr._MAX_EXPR_CHARS
            except ValueError:
                accepted = False
            if accepted:
                if p["rc"] != 0:
                    bad.append((p["id"], "accepted what twoway refuses"))
                    continue
                want = _bridged(_floats(p["gen_y"]))
                y = _bridged(y)
                if _has_plain_arith(p["expr"]):
                    ok = _same(y, want)
                else:
                    ok = (y.shape == want.shape and bool(np.allclose(
                        y, want, rtol=_RTOL.get(p["expr"], 1e-15), atol=0,
                        equal_nan=True)))
                if not ok:
                    bad.append((p["id"], list(y)[:4], list(want)[:4]))
            else:
                if p["rc"] == 0 and p["expr"] not in _FALLBACK_UNSUPPORTED:
                    bad.append((p["id"], "refused what twoway draws"))
                if len(y) != 0 or len(notes) != 1:
                    bad.append((p["id"], "not drawn empty with one note",
                                len(y), len(notes)))
        assert not bad, bad


# ---------------------------------------------------------------------------
# The parser
# ---------------------------------------------------------------------------

def _parse(text):
    return getattr(dr, "_stata_fn_parse")(text)


def _eval(text, x):
    return getattr(dr, "_stata_fn_eval")(_parse(text),
                                         np.asarray(x, dtype=float))


class TestTheParser:
    def test_power_nests_left(self):
        t = _parse("2^3^x")
        assert t == ("pow", ("c", 2.0), [(False, ("c", 3.0)),
                                         (False, ("x",))])
        assert list(_eval("2^3^x", [0, 1, 2])) == [1.0, 8.0, 64.0]

    def test_sign_binds_one_atom(self):
        assert _parse("2^-1^2") == ("pow", ("c", 2.0),
                                    [(True, ("c", 1.0)), (False, ("c", 2.0))])
        assert _parse("-x^2") == ("neg", ("pow", ("x",), [(False,
                                                            ("c", 2.0))]))
        assert _parse("--x") == ("x",)
        assert _parse("2^--1") == ("pow", ("c", 2.0), [(False, ("c", 1.0))])

    def test_precedence_levels(self):
        assert _parse("1+2-3") == ("fold", "+", [
            ("c", 1.0), ("fold", "-", [("c", 2.0), ("c", 3.0)])])
        assert _parse("1*2/3") == ("fold", "*", [
            ("c", 1.0), ("fold", "/", [("c", 2.0), ("c", 3.0)])])
        assert _parse("1-2-3") == ("fold", "-", [("c", 1.0), ("c", 2.0),
                                                 ("c", 3.0)])
        assert _parse("sin(x)") == ("call", "sin", ("x",))
        assert _parse("(x)") == ("x",)

    def test_ascii_names_only(self):
        assert _parse("_pi") == ("c", math.pi)
        for text in ("ｓｉｎ(x)", "pi", "e", "X", "_PI", "y",
                     "x\x00", "é", "nosuch(x)", "_b[x]"):
            with pytest.raises(ValueError):
                _parse(text)

    def test_numbers_and_missing(self):
        assert _parse("1e3") == ("c", 1000.0)
        assert _parse(".5") == ("c", 0.5)
        assert _parse("5.") == ("c", 5.0)
        assert _parse("1.5e-2") == ("c", 0.015)
        assert _parse("2E+1") == ("c", 20.0)
        for text in (".", ".a", ".z"):
            t = _parse(text)
            assert t[0] == "c" and math.isnan(t[1]), text
        for text in (".ab", "..", "1e", "1.2.3", "0x10", "1.8X+01"):
            with pytest.raises(ValueError):
                _parse(text)

    def test_refusals(self):
        for text in _REFUSED + ["", " ", "x+", "(x", "x)", "sin()", "sin",
                                "x>1", "x==1", "x&1", "!x", '"x"', "'x'",
                                "x,1", "x[1]", "max(x,1)", "c(pi)"]:
            with pytest.raises(ValueError):
                _parse(text)


class TestTheParserIsBounded:
    def test_long_chains_do_not_recurse(self):
        text = "+".join(["x"] * 2400)
        assert len(text) == 4799
        t0 = time.time()
        y = _eval(text, [0.0, 1.0, 2.0])
        assert time.time() - t0 < 1.0
        assert list(y) == [0.0, 2400.0, 4800.0]
        assert _parse("-" * 4999 + "x") == ("neg", ("x",))
        assert _parse("2^" + "^".join(["1"] * 2000)) is not None

    def test_nesting_is_capped(self):
        ok = "(" * 40 + "x" + ")" * 40
        assert list(_eval(ok, [0.0, 1.0])) == [0.0, 1.0]
        deep = "(" * 41 + "x" + ")" * 41
        with pytest.raises(ValueError):
            _parse(deep)
        with pytest.raises(ValueError):
            _parse("sin(" * 41 + "x" + ")" * 41)
        _x, y, _w, _ = _draw("saved", ok)
        assert len(y) == 3
        _x, y, warns, _ = _draw("saved", deep)
        assert len(y) == 0 and len(_empty_notes(warns)) == 1


class TestNoEval:
    def test_the_mapper_cannot_evaluate_python(self):
        pat = re.compile(r"(?<![A-Za-z0-9_.])(eval|compile|exec)\s*\(")
        for fn in (dr.GlyphMapper.map_function,
                   dr.GlyphMapper._mark_needs_points,
                   dr.GlyphMapper._needs_points_why,
                   getattr(dr, "_stata_fn_parse"),
                   getattr(dr, "_stata_fn_eval")):
            src = inspect.getsource(fn)
            assert not pat.search(src), fn.__name__


# ---------------------------------------------------------------------------
# WP-30 P1.22: a layer the fallback cannot draw says what it needs
# ---------------------------------------------------------------------------

def _refusal_tail(expr):
    if expr in _NEEDS_STATA_FUNCS:
        return _NEEDS_STATA_FUNCS[expr] + "() is not one of them."
    if expr in _NEEDS_STATA_NAMES:
        return "the name " + _NEEDS_STATA_NAMES[expr] + " is not one of them."
    return "the expression cannot be read with them."


@pytest.mark.parametrize("mode", MODES)
class TestTheFallbackSaysWhatItNeeds:
    def test_each_refusal_names_what_it_met(self, mode):
        """Every row: an empty layer and exactly one note, naming the first
        function (``name()``), the first bare name, or neither."""
        bad = []
        for expr in (sorted(_NEEDS_STATA_FUNCS) + sorted(_NEEDS_STATA_NAMES)
                     + _NO_NAME):
            _x, y, warns, _ = _draw(mode, expr)
            want = [_HEAD + ", and this spec carries none; " + _KNOWS
                    + ", and " + _refusal_tail(expr)]
            got = _empty_notes(warns)
            if len(y) != 0 or got != want:
                bad.append((expr, len(y), got))
        assert not bad, bad

    def test_points_that_cannot_be_read_say_so(self, mode):
        points, raw = _HOSTILE["points a list"]
        x, y, warns, _ = _draw(mode, "x", points=points, raw=raw)
        assert len(x) == 0 and len(y) == 0
        assert _empty_notes(warns) == [
            _HEAD + ", and the points this spec carries for it cannot be "
            "read."]


class TestTheNeedsPointsMark:
    def test_the_parser_names_what_it_refused(self):
        for text, want, msg in (
                ("normalden(x)", ("function", "normalden"),
                 "unknown function"),
                ("pi*x", ("name", "pi"), "unknown name"),
                ("ln(x)+normalden(x)", ("function", "ln"),
                 "unknown function")):
            with pytest.raises(ValueError) as ei:
                _parse(text)
            assert str(ei.value) == msg, text
            assert ei.value.dash_refused == want, text
        with pytest.raises(ValueError) as ei:
            _parse("x>1")
        assert getattr(ei.value, "dash_refused", None) is None

    def test_mark_needs_points_marks_each_renderer(self):
        f = figure()
        a, b = f.line(x=[], y=[]), f.line(x=[], y=[])
        mark = dr.GlyphMapper._mark_needs_points
        assert mark(a, "W") is a
        both = [a, b]
        assert mark(both, "W") is both
        assert a._dash_needs_points == b._dash_needs_points == "W"
        mark([object()], "W")  # raises nothing

    def test_the_why_of_each_refusal(self):
        why = dr.GlyphMapper._needs_points_why
        assert why() == ("it needs the points Stata computes for it when "
                         "dash registers the graph, and the points this "
                         "spec carries for it cannot be read")
        assert why(ValueError("x")) == (
            "it needs the points Stata computes for it when dash registers "
            "the graph, and this spec carries none; " + _KNOWS
            + ", and the expression cannot be read with them")

        def refused(got):
            e = ValueError("x")
            e.dash_refused = got
            return why(e)
        assert refused(("function", "normalden")).endswith(
            ", and normalden() is not one of them")
        assert refused(("name", "pi")).endswith(
            ", and the name pi is not one of them")
        assert refused(("function", "a" * 40)).endswith(
            ", and " + "a" * 32 + "...() is not one of them")
        assert "a" * 33 not in refused(("function", "a" * 40))
        for got in (("function", "{bf:x}"), ("function", "é"),
                    ("function", ""), ("name", "9x"), ("call", "x"),
                    ["function", "x"], ("function", 5), ("function", "a b")):
            # The expression tail, and nothing of the value echoed.
            assert refused(got) == why(ValueError("x")), got

    def test_the_note_lists_exactly_what_the_fallback_knows(self):
        tree = ast.parse(textwrap.dedent(inspect.getsource(
            dr._stata_fn_parse)))
        funcs = None
        for node in ast.walk(tree):
            if (isinstance(node, ast.Assign)
                    and any(getattr(t, "id", None) == "funcs"
                            for t in node.targets)):
                funcs = [e.value for e in node.value.elts]
        assert funcs and len(funcs) == 10
        text = dr.GlyphMapper._needs_points_why(ValueError("x"))
        assert re.findall(r"(\w+)\(\)", text)[:10] == funcs
        assert "x, _pi, numbers, + - * / ^" in text

    @pytest.mark.parametrize("mode", MODES)
    def test_the_mark_is_never_serialised(self, mode):
        spec = mp._spec([_fn_plot("normalden(x)")])
        models, _w, mod = _render(mode, spec)
        doc = (next(m.document for m in models if m.document is not None)
               if mode == "saved" else mod._dash_test_doc)
        page = file_html(doc, CDN)
        assert "_dash_needs_points" not in page
        assert "it needs the points" not in page


class TestTheReasonedReport:
    def _notes(self, fn, *a, **k):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            fn(*a, **k)
        return [str(w.message) for w in caught]

    def test_a_reason_follows_drew_nothing(self):
        rep = dr._dash_report_empty_layer
        assert self._notes(rep, "g1", 3, "function", why="it needs x") == [
            "dash: graph 'g1' plot 3 (function) drew nothing: it needs x."]
        assert self._notes(rep, "g1", 3, "function", why="") == [
            "dash: graph 'g1' plot 3 (function) drew nothing."]

    def test_the_function_branch_reads_the_mark(self):
        note = dr._dash_note_empty_layer
        r = figure().line(x=[], y=[])
        assert self._notes(note, "g1", 2, "function", 0, [r]) == [
            "dash: graph 'g1' plot 2 (function) drew nothing."]
        r._dash_needs_points = "W"
        assert self._notes(note, "g1", 2, "function", 0, [r]) == [
            "dash: graph 'g1' plot 2 (function) drew nothing: W."]
        assert self._notes(note, "g1", 2, "scatter", 6, [r]) == [
            "dash: graph 'g1' plot 2 (scatter) drew nothing from 6 "
            "observations."]
        for bad in (5, "x" * 1001):
            r._dash_needs_points = bad
            assert self._notes(note, "g1", 2, "function", 0, [r]) == [
                "dash: graph 'g1' plot 2 (function) drew nothing."], bad


class TestTheHelp:
    def test_the_fallback_rule_is_stated(self):
        with open(os.path.join(_HERE, "..", "dash.sthlp"),
                  encoding="utf-8") as fh:
            text = fh.read()
        a = text.index("{ul:Functions.}")
        b = text.index("{ul:Graphs that need no data.}", a)
        para = " ".join(re.sub(r"\{cmd:|\}", "", text[a:b]).split())
        for want in ("carries no points",
                     "needs the points Stata computes when dash registers "
                     "the graph",
                     "names the first function or name it uses that dash "
                     "cannot evaluate",
                     "Stored points that cannot be read get the same note",
                     "Registering the graph with dash computes its points "
                     "in Stata"):
            assert want in para, want
        assert "a note names it" not in para
