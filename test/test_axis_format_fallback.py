"""Axis tick labels in twoway's display formats (WP-30 P1.5).

The defect (DROPIN-REMAINING.md P1.5, GAPS2 G10): a default axis kept
Bokeh's own tick text -- ``dash scatter mpg weight`` labelled weight
``2000 3000`` where twoway, reading weight's ``%8.0gc``, writes ``2,000
3,000 4,000 5,000``; ``xlabel(, format(%td...))`` was dropped without a
word; a numeric ``format()`` on a date axis wrote epoch milliseconds
(``9.47e+11``); ``format(bogus)`` drew unformatted ticks where twoway
refuses it; a second axis with no ``ylabel2()`` and ``xvarformat()``/
``yvarformat()`` were ignored.

twoway's rule (measured 03oct2026, StataNow 19.5; fixture
test/fixtures/axis_format_truth.json, written by
scripts/extract_axis_format_truth.do): an axis takes the format of its
first view's serset column.  That is the variable the first layer drawn on
that axis puts there (a range layer's first y, a pc layer's first pair) or
the layer's own ``xvarformat()``/``yvarformat()``; literal layers, the fits
and kdensity are ``%9.0g``; a histogram's height is ``%6.4g``; lowess and
fpfit write y in ``%9.0g``.  Of the layers on an axis, grouped by the axis
they use in the other dimension, the axis takes the first layer of the
group whose first layer comes last.

While iterating run only this file (CLAUDE.md rule 10):
``python3 -m pytest test/test_axis_format_fallback.py -q``.
"""
import json
import os
import sys
import time
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from bokeh.models import (CustomJSTickFormatter, LinearAxis,  # noqa: E402
                          LogAxis, RangeSlider)
from test_display_format_sites import (MODES, build, js_texts,  # noqa: E402
                                       spec_of, _graph, _scatter)
from test_mode_parity import _fire  # noqa: E402
from probe_groups import probe_params, representative  # noqa: E402

FIXTURE = os.path.join(_ROOT, "test", "fixtures", "axis_format_truth.json")

_N = 41


def _frame():
    """auto-like and sp500-like columns over their ranges."""
    return pd.DataFrame({
        "weight": np.linspace(1760, 4840, _N),
        "price": np.linspace(3291, 15906, _N),
        "mpg": np.linspace(12, 41, _N),
        "gear_ratio": np.linspace(2.19, 3.89, _N),
        "r": np.linspace(.219, .389, _N),
        "length": np.linspace(142, 233, _N),
        "foreign": [float(i % 2) for i in range(_N)],
        "date": np.linspace(14977, 15338, _N).round(),
        "close": np.linspace(965, 1374, _N),
        "m": np.linspace(492, 503, _N).round(),
    })


_AUTO = {"weight": "%8.0gc", "price": "%8.0gc", "mpg": "%8.0g",
         "gear_ratio": "%6.2f", "r": "%9.0g", "length": "%8.0g",
         "foreign": "%8.0g", "date": "%td", "close": "%9.0g", "m": "%tm"}
_STORE = {k: "double" for k in _AUTO}


def _fmts(**over):
    f = dict(_AUTO)
    f.update(over)
    return f


def _sc(y, x, **o):
    return _scatter(y, x, **o)


def _built(mode, plots, formats=None, **go):
    return build(mode, spec_of([_graph("g", plots, **go)],
                               formats=formats or _fmts()),
                 df=_frame(), storage=_STORE)


def _figs(b):
    return [m for m in b.models if type(m).__name__ == "figure"]


def _axis(fig, side):
    """The primary x/y axis, or the second (x2/y2) one."""
    if side in ("x", "y"):
        rng = "x_range_name" if side == "x" else "y_range_name"
        sides = ("below", "above") if side == "x" else ("left", "right")
        for s in sides:
            for a in getattr(fig, s):
                if (isinstance(a, (LinearAxis, LogAxis))
                        and getattr(a, rng, "default") == "default"):
                    return a
        raise AssertionError(f"no {side} axis")
    rng = "x_range_name" if side == "x2" else "y_range_name"
    for s in ("below", "above", "left", "right"):
        for a in getattr(fig, s):
            if getattr(a, rng, None) == side:
                return a
    raise AssertionError(f"no {side} axis")


def _writer(fig, side):
    fm = _axis(fig, side).formatter
    if isinstance(fm, CustomJSTickFormatter) and "fmt" in fm.args:
        return fm
    return None


def _fmt_of(fig, side):
    w = _writer(fig, side)
    return None if w is None else w.args["fmt"]


def _texts(fig, side, values):
    w = _writer(fig, side)
    assert w is not None, (side, _axis(fig, side).formatter)
    return js_texts(w, list(values), "tick")


def _ms(day):
    return (day - 3653) * 86_400_000.0


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------

class TestFormatText:

    def test_the_word_read(self):
        f = dr._dash_axis_format_text
        assert f("%9.2f") == "%9.2f"
        assert f(' "%9.2f" ') == "%9.2f"
        assert f('`"%9.1f"\'') == "%9.1f"
        assert f("%9.2f %9.1f") == "%9.1f"
        assert f("%9.2f %9.1f", first=True) == "%9.2f"
        assert f("") == "" and f(None) == "" and f(5) == ""
        t0 = time.monotonic()
        got = f("%" + "9" * 1_000_000)
        assert time.monotonic() - t0 < 0.1
        assert len(got) == 61 and dr._dash_fmt_kind(got) is None


def _p(ptype, **kw):
    p = {"type": ptype, "options": kw.pop("options", {})}
    p.update(kw)
    return p


_NF = {"weight": "%8.0gc", "price": "%8.0gc", "mpg": "%8.0g",
       "length": "%8.0g"}


class TestTheHelper:

    _LAYERS = [
        (_p("scatter", yvar="mpg", xvar="weight"), "%8.0gc", "%8.0g"),
        (_p("line", yvar="price", xvar="weight"), "%8.0gc", "%8.0gc"),
        (_p("rarea", yvar1="price", yvar2="mpg", xvar="weight"),
         "%8.0gc", "%8.0gc"),
        (_p("rarea", yvar1="mpg", yvar2="price", xvar="weight"),
         "%8.0gc", "%8.0g"),
        (_p("pcspike", y1var="mpg", x1var="weight", y2var="price",
            x2var="length"), "%8.0gc", "%8.0g"),
        (_p("scatteri", values=[[20, 3000]]), "%9.0g", "%9.0g"),
        (_p("function", expr="x"), "%9.0g", "%9.0g"),
        (_p("lfit", yvar="price", xvar="weight"), "%9.0g", "%9.0g"),
        (_p("lpolyci", yvar="price", xvar="weight"), "%9.0g", "%9.0g"),
        (_p("kdensity", var="price"), "%9.0g", "%9.0g"),
        (_p("lowess", yvar="price", xvar="weight"), "%8.0gc", "%9.0g"),
        (_p("fpfit", yvar="price", xvar="weight"), "%8.0gc", "%9.0g"),
        (_p("mspline", yvar="price", xvar="weight"), "%8.0gc", "%8.0gc"),
        (_p("mband", yvar="price", xvar="weight"), "%8.0gc", "%8.0gc"),
        (_p("histogram", var="price"), "%8.0gc", "%6.4g"),
        (_p("scatter", yvar="mpg", xvar="nofmt"), "%9.0g", "%8.0g"),
        ]

    def test_each_layer_type(self):
        f = dr._dash_layer_tick_format
        for plot, x, y in self._LAYERS:
            assert f(plot, "x", _NF, {}) == (x, False), plot
            assert f(plot, "y", _NF, {}) == (y, False), plot

    def test_varformat_wins(self):
        p = _p("lfit", yvar="mpg", xvar="weight",
               options={"xvarformat": "%9.2f bogus", "yvarformat": "%9.1f"})
        assert dr._dash_layer_tick_format(p, "x", _NF, {}) == ("%9.2f", True)
        assert dr._dash_layer_tick_format(p, "y", _NF, {}) == ("%9.1f", True)

    def test_a_date_variable_gives_no_format(self):
        dv = {"date": "td"}
        # Flipped (WP-44 AX-18): "" for an lfit or kdensity of a date was
        # wrong because twoway labels their axis in %9.0g, the date's
        # numbers (date_axis_rule_truth.json ax18.first_lfit,
        # ax18.kdensity_alone: 15000 ... 15400); a line keeps "".
        assert dr._dash_layer_tick_format(
            _p("lfit", yvar="close", xvar="date"), "x", _NF, dv) == (
                "%9.0g", False)
        assert dr._dash_layer_tick_format(
            _p("line", yvar="close", xvar="date"), "x", _NF, dv) == ("", False)
        assert dr._dash_layer_tick_format(
            _p("kdensity", var="date"), "x", _NF, dv) == ("%9.0g", False)
        assert dr._dash_axis_tick_formats(None, _NF) == {
            "x": ("", False), "y": ("", False), "x2": ("", False),
            "y2": ("", False)}

    _SEVERAL = [
        # m01, m02: the first layer's first y.
        ([_p("scatter", yvar="mpg", xvar="weight"),
          _p("scatter", yvar="price", xvar="weight")], {"y": "%8.0g"}),
        # m03: x from the first layer (length).
        ([_p("scatter", yvar="mpg", xvar="length"),
          _p("scatter", yvar="mpg", xvar="weight")], {"x": "%8.0g"}),
        # m04: lfit first gives %9.0g on both.
        ([_p("lfit", yvar="price", xvar="weight"),
          _p("scatter", yvar="price", xvar="weight")],
         {"x": "%9.0g", "y": "%9.0g"}),
        # m07: y2 from its first layer.
        ([_p("scatter", yvar="mpg", xvar="weight"),
          _p("scatter", yvar="price", xvar="weight",
             options={"yaxis": "2"})],
         {"y": "%8.0g", "y2": "%8.0gc", "x": "%8.0gc"}),
        # m09 (w2): the y2 group's first layer comes last: x is weight's.
        ([_p("scatter", yvar="mpg", xvar="length"),
          _p("scatter", yvar="mpg", xvar="weight", options={"yaxis": "2"})],
         {"x": "%8.0gc"}),
        # m10 (w4): x is length's.
        ([_p("scatter", yvar="mpg", xvar="weight", options={"yaxis": "2"}),
          _p("scatter", yvar="mpg", xvar="length")], {"x": "%8.0g"}),
        # m11 (w7): x length's; y2 mpg's.
        ([_p("scatter", yvar="mpg", xvar="weight"),
          _p("scatter", yvar="mpg", xvar="length", options={"yaxis": "2"}),
          _p("scatter", yvar="price", xvar="weight",
             options={"yaxis": "2"})], {"x": "%8.0g", "y2": "%8.0g"}),
        # m12 (x5): x length's.
        ([_p("scatter", yvar="mpg", xvar="weight", options={"yaxis": "2"}),
          _p("scatter", yvar="mpg", xvar="weight", options={"yaxis": "2"}),
          _p("scatter", yvar="mpg", xvar="length")], {"x": "%8.0g"}),
        # m13 (x6): x weight's.
        ([_p("scatter", yvar="mpg", xvar="weight", options={"yaxis": "2"}),
          _p("scatter", yvar="mpg", xvar="length", options={"yaxis": "2"})],
         {"x": "%8.0gc"}),
        # m14 (y1): y price's; m15 (y2): y mpg's.
        ([_p("scatter", yvar="mpg", xvar="weight"),
          _p("scatter", yvar="price", xvar="weight",
             options={"xaxis": "2"})], {"y": "%8.0gc", "x2": "%8.0gc"}),
        ([_p("scatter", yvar="price", xvar="weight", options={"xaxis": "2"}),
          _p("scatter", yvar="mpg", xvar="weight")], {"y": "%8.0g"}),
        ([None, "x", _p("scatter", yvar="mpg", xvar="weight")],
         {"x": "%8.0gc"}),
        ]

    def test_the_several_layer_rule(self):
        for n, (plots, want) in enumerate(self._SEVERAL):
            got = dr._dash_axis_tick_formats(plots, _NF, {})
            assert {k: got[k][0] for k in want} == want, (n, got)


# ---------------------------------------------------------------------------
# Both modes
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", MODES)
class TestDefaultTicks:

    _FORMATS = [
        ("%8.0gc", "weight", [2000, 3000, 4000, 5000],
         ["2,000", "3,000", "4,000", "5,000"]),
        ("%9.0fc", "weight", [2000, 3000], ["2,000", "3,000"]),
        ("%9.2f", "weight", [2000], ["2000.00"]),
        ("%6.2f", "gear_ratio", [2], ["2.00"]),
        ("%9.0g", "r", [.2, .25], [".2", ".25"]),
        ("%9.2e", "price", [5000], ["5.00e+03"]),
        ("%9,2f", "gear_ratio", [2.5], ["2,50"]),
        ("%-9.0fc", "weight", [2000], ["2,000"]),
        ]

    def test_each_display_format_reaches_a_default_axis(self, mode):
        for fmt, var, vals, want in self._FORMATS:
            b = _built(mode, [_sc("mpg", var)], formats=_fmts(**{var: fmt}))
            (fig,) = _figs(b)
            assert _fmt_of(fig, "x") == fmt
            assert _texts(fig, "x", vals) == want, fmt

    def test_a_rule_or_list_keeps_the_fallback(self, mode):
        for go, side, vals, want in (
                ({"ylabel": "#5"}, "y", [5000], ["5,000"]),
                ({"xlabel": "2000(1000)5000"}, "x", [2000], ["2,000"]),
                ({"xlabel": "minmax"}, "x", [1760], ["1,760"])):
            b = _built(mode, [_sc("price", "weight")], **go)
            (fig,) = _figs(b)
            assert _texts(fig, side, vals) == want, go

    def test_log_axis_writes_the_help_examples_commas(self, mode):
        b = _built(mode, [_sc("price", "weight")], yscale="log",
                   ylabel="#5")
        (fig,) = _figs(b)
        assert _texts(fig, "y", [5000, 10000, 15000]) == [
            "5,000", "10,000", "15,000"]

    def test_every_by_panel(self, mode):
        b = _built(mode, [_sc("mpg", "weight")],
                   formats=_fmts(mpg="%9.2f"), by="foreign")
        figs = _figs(b)
        assert len(figs) >= 2
        assert {_fmt_of(f, "y") for f in figs} == {"%9.2f"}


@pytest.mark.parametrize("mode", MODES)
class TestLayerTypes:

    def test_the_axis_takes_the_serset_columns_format(self, mode):
        (fig,) = _figs(_built(mode, [_p("histogram", var="price")]))
        assert _fmt_of(fig, "y") == "%6.4g"
        assert _texts(fig, "y", [0.0001]) == ["1.0e-04"]
        (fig,) = _figs(_built(mode, [_p("lfit", yvar="price",
                                        xvar="weight"),
                                     _sc("price", "weight")]))
        assert _texts(fig, "x", [2000]) == ["2000"]
        assert _texts(fig, "y", [4000]) == ["4000"]
        (fig,) = _figs(_built(mode, [_p("rarea", yvar1="price",
                                        yvar2="mpg", xvar="weight")]))
        assert _fmt_of(fig, "y") == "%8.0gc"
        (fig,) = _figs(_built(mode, [_p("kdensity", var="price")]))
        assert _fmt_of(fig, "x") == "%9.0g"


_TWO = [_sc("mpg", "weight"), _sc("price", "weight", yaxis="2")]


@pytest.mark.parametrize("mode", MODES)
class TestSecondAxis:

    def test_ylabel2_absent_takes_the_layers_format(self, mode):
        (fig,) = _figs(_built(mode, _TWO))
        assert _texts(fig, "y2", [5000]) == ["5,000"]

    def test_explicit_axis2_format(self, mode):
        (fig,) = _figs(_built(mode, _TWO, ylabel2=", format(%9.1f)"))
        assert _texts(fig, "y2", [5000]) == ["5000.0"]

    def test_a_date_y2_is_left_alone(self, mode):
        """A guard (S35 owns date second axes): S18 sets no writer there."""
        plots = [_sc("close", "date"), _sc("date", "close", yaxis="2")]
        (fig,) = _figs(_built(mode, plots))
        fm = _axis(fig, "y2").formatter
        assert not (isinstance(fm, CustomJSTickFormatter)
                    and fm.args.get("fmt") and not fm.args.get("kind"))


_LINE_DATE = [{"type": "line", "yvar": "close", "xvar": "date",
               "options": {}}]
_LINE_M = [{"type": "line", "yvar": "close", "xvar": "m", "options": {}}]


@pytest.mark.parametrize("mode", MODES)
class TestExplicitFormat:

    def test_numeric_format_on_a_date_axis_writes_the_stata_value(
            self, mode):
        for xl, want in ((", format(%9.0fc)", "14,976"),
                         (", format(%9.0f)", "14976"),
                         (", for(%9.0fc)", "14,976")):
            (fig,) = _figs(_built(mode, _LINE_DATE, xlabel=xl))
            assert _texts(fig, "x", [_ms(14976)]) == [want], xl

    def test_date_picture_on_a_date_axis(self, mode):
        (fig,) = _figs(_built(mode, _LINE_DATE,
                              xlabel=", format(%tdDD/NN/CCYY)"))
        assert _texts(fig, "x", [_ms(14976)]) == ["01/01/2001"]
        (fig,) = _figs(_built(mode, _LINE_DATE, xlabel=", format(%tm)"))
        assert _texts(fig, "x", [_ms(14976)]) == ["3208m1"]

    def test_date_format_on_a_numeric_axis(self, mode):
        for xl in (", format(%td)", ", for(%td)"):
            b = _built(mode, [_sc("mpg", "weight")], xlabel=xl)
            (fig,) = _figs(b)
            assert _texts(fig, "x", [2000]) == ["23jun1965"], xl
            assert not [w for w in b.warnings if "format(" in w], b.warnings


@pytest.mark.parametrize("mode", MODES)
class TestUnwritableFormats:

    def test_one_rule(self, mode):
        # Flipped (WP-44 AX-15): format(%12s) and format(%21x) are written
        # as twoway writes them (test_tick_label_options_p9.py::
        # TestFormats), so only a word that is no format stays %9.0g.
        for xl in (", format(bogus)",):
            b = _built(mode, [_sc("mpg", "weight")], xlabel=xl)
            (fig,) = _figs(b)
            assert _fmt_of(fig, "x") == "%9.0g", xl
            word = xl.split("(", 1)[1].rstrip(")")
            notes = [w for w in b.warnings if f"format({word})" in w]
            assert len(notes) == 1, (xl, b.warnings)
        for xl, want in ((", format(%9.2f %9.1f)", "%9.1f"),
                         (', format("%9.2f")', "%9.2f"),
                         (", format()", "%8.0gc")):
            b = _built(mode, [_sc("mpg", "weight")], xlabel=xl)
            (fig,) = _figs(b)
            assert _fmt_of(fig, "x") == want, xl
            assert not [w for w in b.warnings if "format(" in w], b.warnings


@pytest.mark.parametrize("mode", MODES)
class TestLabelsAndFormat:

    def test_unlabelled_ticks_beside_text_labels_use_the_format(self, mode):
        (fig,) = _figs(_built(mode, [_sc("mpg", "weight")],
                              xlabel='2000 "two" 3000 4000'))
        fm = _writer(fig, "x")
        assert json.loads(fm.args["labels"]) == {"2000.0": "two"}
        assert "two" not in fm.code
        assert _texts(fig, "x", [2000, 3000, 4000]) == [
            "two", "3,000", "4,000"]
        (fig,) = _figs(_built(mode, [_sc("mpg", "weight")],
                              xlabel='2000 "two" 3000 4000, format(%9.1f)'))
        assert _texts(fig, "x", [3000]) == ["3000.0"]
        (fig,) = _figs(_built(mode, _LINE_DATE,
                              xlabel='15000 "mid" 15100'))
        assert _texts(fig, "x", [_ms(15100)]) == [
            dr._dash_fmt_text(15100, "%td")]


@pytest.mark.parametrize("mode", MODES)
class TestVarformat:

    def test_read_as_twoway_reads_it(self, mode):
        (fig,) = _figs(_built(mode, [_sc("mpg", "weight", xvarformat="%9.2f",
                                         yvarformat="%9.1f")]))
        assert _texts(fig, "x", [2000]) == ["2000.00"]
        assert _texts(fig, "y", [10]) == ["10.0"]
        (fig,) = _figs(_built(mode, [_sc("mpg", "weight"),
                                     _sc("price", "weight", yaxis="2",
                                         yvarformat="%9.1f")]))
        assert _texts(fig, "y2", [0]) == ["0.0"]
        (fig,) = _figs(_built(mode, [_p("lfit", yvar="mpg", xvar="weight",
                                        options={"xvarformat": "%9.2f"}),
                                     _sc("mpg", "weight")]))
        assert _texts(fig, "x", [2000]) == ["2000.00"]
        (fig,) = _figs(_built(mode, [_sc("mpg", "weight"),
                                     _sc("mpg", "weight",
                                         xvarformat="%9.1f")],
                              xlabel=", format(%9.3f)"))
        assert _fmt_of(fig, "x") == "%9.3f"
        b = _built(mode, [_sc("mpg", "weight", xvarformat="%21x")])
        (fig,) = _figs(b)
        assert _fmt_of(fig, "x") == "%9.0g"
        assert len([w for w in b.warnings if "xvarformat(%21x)" in w]) == 1


@pytest.mark.parametrize("mode", MODES)
class TestTeXInTickLabels:

    def test_the_label_map_is_still_finished(self, mode):
        (fig,) = _figs(_built(mode, [_sc("mpg", "weight")],
                              xlabel='2000 "\\(t\\)" 3000'))
        fm = _writer(fig, "x")
        assert fm.args["fmt"] == "%8.0gc"
        got = json.loads(fm.args["labels"])["2000.0"]
        assert got == dr._dash_inert_tex("\\(t\\)") != "\\(t\\)", got


class TestAfterAMove:

    def test_formatters_survive_a_move(self):
        graphs = [_graph("g", [_sc("mpg", "weight"),
                               _sc("price", "weight", yaxis="2")])]
        spec = spec_of(graphs, filters="weight, type(range)",
                       formats=_fmts())
        b = build("served", spec, df=_frame(), storage=_STORE)
        (fig,) = _figs(b)
        before = {s: dict(_writer(fig, s).args) for s in ("x", "y", "y2")}
        ws = [m for m in b.models if isinstance(m, RangeSlider)]
        assert ws, "no range slider"
        _fire(ws[0], (2000.0, 3000.0))
        figs = [m for r in b.obj.roots for m in r.references()
                if type(m).__name__ == "figure"]
        for f in figs:
            assert {s: dict(_writer(f, s).args)
                    for s in ("x", "y", "y2")} == before
        saved = build("standalone", spec, df=_frame(), storage=_STORE)
        for m in saved.models:
            code = getattr(m, "code", None)
            if isinstance(code, str) and not isinstance(
                    m, CustomJSTickFormatter):
                assert ".formatter" not in code, type(m).__name__


class TestAdversarial:

    def test_format_text_never_reaches_code(self):
        from bokeh.plotting import figure
        for bad in ("</script><script>alert(1)</script>", "%" + "9" * 1_000_000):
            fig = figure()
            spec = dr._dash_parse_axis_spec("")
            spec["format"] = bad
            dr._dash_reset_notes()
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                dr._dash_apply_axis_spec(fig.xaxis, fig.xgrid, spec,
                                         option="xlabel")
            fm = fig.xaxis[0].formatter
            assert fm.args["fmt"] == "%9.0g"
            assert "<script>alert" not in fm.code
            notes = [str(w.message) for w in caught]
            assert len(notes) == 1
            echoed = notes[0].split("format(", 1)[1].split(") is written")[0]
            assert len(echoed) <= 83


# ---------------------------------------------------------------------------
# Against twoway (axis_format_truth.json)
# ---------------------------------------------------------------------------

def _fixture():
    if not os.path.exists(FIXTURE):
        pytest.fail("test/fixtures/axis_format_truth.json is missing")
    with open(FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def test_fixture_and_script_are_named():
    # Literal paths, for test_fixtures_are_committed.py.
    assert os.path.exists(os.path.join(
        _ROOT, "test/fixtures/axis_format_truth.json"))
    assert os.path.exists(os.path.join(
        _ROOT, "scripts/extract_axis_format_truth.do"))


def _line(y, x, **o):
    return {"type": "line", "yvar": y, "xvar": x, "options": o}


#: case id -> (plots, graph options, format overrides, axes compared).
#: Cases left out, and why: k04/k05 (the off-canvas 0 and log ticks are
#: S21's), l04/l14 (literal layers: same %9.0g, positions S21's), l15
#: (a date axis's own writer, unchanged), e11/e12 (%12s over a literal
#: layer's positions, and %21x, whose texts give no value to place them;
#: both written as twoway writes them since WP-44 AX-15, pinned by
#: test_tick_label_options_p9.py::TestFormats), v10 (date ticks are placed in day
#: units, S21's), v15 (twoway draws no labels), m13 y2 (the SVG reader
#: reads the axis title there).
_CASE_SPECS = {
    "d01": ([_sc("mpg", "weight")], {}, {}, ("x", "y")),
    "d02": ([_sc("mpg", "weight")], {}, {"weight": "%9.0fc"}, ("x",)),
    "d03": ([_sc("mpg", "weight")], {}, {"weight": "%9.2f"}, ("x",)),
    "d04": ([_sc("gear_ratio", "weight")], {}, {}, ("y",)),
    "d05": ([_sc("r", "weight")], {}, {}, ("y",)),
    "d06": ([_sc("price", "weight")], {}, {"price": "%9.2e"}, ("y",)),
    "d07": ([_sc("gear_ratio", "weight")], {}, {"gear_ratio": "%9,2f"},
            ("y",)),
    "d08": ([_sc("price", "weight")], {}, {"price": "%9.0g"}, ("y",)),
    "d09": ([_sc("mpg", "weight")], {}, {"weight": "%-9.0fc"}, ("x",)),
    "d10": ([_sc("mpg", "weight")], {"by": "foreign"}, {"mpg": "%9.2f"},
            ("y",)),
    "k01": ([_sc("price", "weight")], {"ylabel": "#5"}, {}, ("y",)),
    "k02": ([_sc("mpg", "weight")], {"xlabel": "2000(1000)5000"}, {},
            ("x",)),
    "k03": ([_sc("mpg", "weight")], {"xlabel": "minmax"}, {}, ("x",)),
    "k06": ([_sc("mpg", "weight")], {"xlabel": '2000 "two" 3000 4000'}, {},
            ("x",)),
    "k07": ([_sc("mpg", "weight")],
            {"xlabel": '2000 "two" 3000 4000, format(%9.1f)'}, {}, ("x",)),
    "l01": ([_p("rarea", yvar1="price", yvar2="mpg", xvar="weight")], {},
            {}, ("x", "y")),
    "l02": ([_p("rarea", yvar1="mpg", yvar2="price", xvar="weight")], {},
            {}, ("y",)),
    "l03": ([_p("pcspike", y1var="mpg", x1var="weight", y2var="price",
                x2var="length")], {}, {}, ("x", "y")),
    "l05": ([_p("lfit", yvar="price", xvar="weight")], {}, {}, ("x", "y")),
    "l06": ([_p("lpoly", yvar="price", xvar="weight")], {}, {}, ("x", "y")),
    "l07": ([_p("kdensity", var="price")], {}, {}, ("x", "y")),
    "l08": ([_p("lowess", yvar="price", xvar="weight")], {}, {}, ("x", "y")),
    "l09": ([_p("mspline", yvar="price", xvar="weight")], {}, {},
            ("x", "y")),
    "l10": ([_p("histogram", var="price")], {}, {}, ("x", "y")),
    "l11": ([_p("histogram", var="price", options={"frequency": "1"})], {},
            {}, ("y",)),
    "l12": ([_p("histogram", var="price", options={"fraction": "1"})], {},
            {}, ("y",)),
    "l13": ([_p("histogram", var="price", options={"percent": "1"})], {},
            {}, ("y",)),
    "l16": ([_p("fpfit", yvar="price", xvar="weight")], {}, {}, ("x", "y")),
    "l17": ([_p("mband", yvar="price", xvar="weight")], {}, {}, ("x", "y")),
    "m01": ([_sc("mpg", "weight"), _sc("price", "weight")], {}, {},
            ("x", "y")),
    "m02": ([_sc("price", "weight"), _sc("mpg", "weight")], {}, {}, ("y",)),
    "m03": ([_sc("mpg", "length"), _sc("mpg", "weight")], {}, {}, ("x",)),
    "m04": ([_p("lfit", yvar="price", xvar="weight"),
             _sc("price", "weight")], {}, {}, ("x", "y")),
    "m05": ([_sc("price", "weight"),
             _p("lfit", yvar="price", xvar="weight")], {}, {}, ("x", "y")),
    "m06": ([_p("kdensity", var="weight"), _sc("mpg", "weight")], {}, {},
            ("x",)),
    "m07": (_TWO, {}, {}, ("x", "y", "y2")),
    "m08": (_TWO, {"ylabel2": ", format(%9.1f)"}, {}, ("y2",)),
    "m09": ([_sc("mpg", "length"), _sc("mpg", "weight", yaxis="2")], {}, {},
            ("x", "y2")),
    "m10": ([_sc("mpg", "weight", yaxis="2"), _sc("mpg", "length")], {}, {},
            ("x", "y2")),
    "m11": ([_sc("mpg", "weight"), _sc("mpg", "length", yaxis="2"),
             _sc("price", "weight", yaxis="2")], {}, {}, ("x", "y2")),
    "m12": ([_sc("mpg", "weight", yaxis="2"), _sc("mpg", "weight",
                                                   yaxis="2"),
             _sc("mpg", "length")], {}, {}, ("x",)),
    "m13": ([_sc("mpg", "weight", yaxis="2"), _sc("mpg", "length",
                                                   yaxis="2")], {}, {},
            ("x",)),
    "m14": ([_sc("mpg", "weight"), _sc("price", "weight", xaxis="2")], {},
            {}, ("y", "x2")),
    "m15": ([_sc("price", "weight", xaxis="2"), _sc("mpg", "weight")], {},
            {}, ("y", "x2")),
    "e01": (_LINE_DATE, {"xlabel": ", format(%9.0fc)"}, {}, ("x",)),
    "e02": (_LINE_DATE, {"xlabel": ", format(%9.0f)"}, {}, ("x",)),
    "e03": (_LINE_DATE, {"xlabel": ", format(%tdDD/NN/CCYY)"}, {}, ("x",)),
    "e04": (_LINE_DATE, {"xlabel": ", format(%tm)"}, {}, ("x",)),
    "e06": ([_line("date", "close")], {"ylabel": ", format(%9.0g)"}, {},
            ("y",)),
    "e07": (_LINE_M, {"xlabel": ", format(%td)"}, {}, ("x",)),
    "e08": (_LINE_M, {"xlabel": ", format(%9.0fc)"}, {}, ("x",)),
    "e09": ([_sc("mpg", "weight")], {"xlabel": ", format(%td)"}, {}, ("x",)),
    "e10": ([_sc("mpg", "weight")], {"xlabel": ", format(%12s)"}, {},
            ("x",)),
    "e13": ([_sc("mpg", "weight")], {"xlabel": ", format(%9.2f %9.1f)"},
            {}, ("x",)),
    "e14": ([_sc("mpg", "weight")], {"xlabel": ', format("%9.2f")'}, {},
            ("x",)),
    "e15": ([_sc("mpg", "weight")], {"xlabel": ", format()"}, {}, ("x",)),
    "e16": ([_sc("mpg", "weight")], {"xlabel": ", for(%9.1f)"}, {}, ("x",)),
    "v01": ([_sc("mpg", "weight", xvarformat="%9.2f", yvarformat="%9.1f")],
            {}, {}, ("x", "y")),
    "v02": ([_sc("mpg", "weight"), _sc("price", "weight", yaxis="2",
                                       yvarformat="%9.1f")], {}, {},
            ("x", "y", "y2")),
    "v03": ([_p("lfit", yvar="mpg", xvar="weight",
                options={"xvarformat": "%9.2f", "yvarformat": "%9.1f"}),
             _sc("mpg", "weight")], {}, {}, ("x", "y")),
    "v04": ([_sc("mpg", "weight"),
             _p("lfit", yvar="mpg", xvar="weight",
                options={"xvarformat": "%9.2f", "yvarformat": "%9.1f"})],
            {}, {}, ("x", "y")),
    "v05": ([_sc("mpg", "weight"), _sc("price", "weight",
                                       yvarformat="%9.1f")], {}, {},
            ("y",)),
    "v06": ([_p("histogram", var="price",
                options={"yvarformat": "%9.3f"})], {}, {}, ("y",)),
    "v07": ([_p("histogram", var="price",
                options={"xvarformat": "%9.1f"})], {}, {}, ("x", "y")),
    "v08": ([_p("rarea", yvar1="price", yvar2="mpg", xvar="weight",
                options={"yvarformat": "%9.1f"})], {}, {}, ("y",)),
    "v09": ([_p("pcspike", y1var="mpg", x1var="weight", y2var="price",
                x2var="length",
                options={"yvarformat": "%9.1f", "xvarformat": "%9.2f"})],
            {}, {}, ("x", "y")),
    "v11": ([_sc("mpg", "weight", xvarformat="%9.1f")], {}, {}, ("x",)),
    "v12": ([_sc("mpg", "weight"), _sc("mpg", "weight",
                                       xvarformat="%9.1f")],
            {"xlabel": ", format(%9.3f)"}, {}, ("x",)),
    "v13": ([_sc("mpg", "weight", xvarformat="%9.1f")],
            {"xlabel": '2000 "two" 3000'}, {}, ("x",)),
    "v14": ([_sc("mpg", "weight", xvarformat="%9.2f bogus")], {}, {},
            ("x",)),
    "v16": ([_sc("mpg", "weight", xvarformat="")], {}, {}, ("x",)),
}

_SKIPPED = {"k04", "k05", "l04", "l14", "l15", "e05", "e11", "e12", "v10",
            "v15"}


def _twoway_number(text, comma_decimal=False):
    """twoway's label as a number: commas are grouping, or the decimal
    point under a comma-decimal format; ``None`` for a text label."""
    t = str(text).strip()
    if comma_decimal:
        t = t.replace(".", "").replace(",", ".")
    else:
        t = t.replace(",", "")
    try:
        return float(t)
    except ValueError:
        return None


class TestTheFixture:

    def test_the_meta_stamp(self):
        for path in (FIXTURE, os.path.join(_ROOT, "test", "fixtures",
                                           "format_truth.json")):
            with open(path, encoding="utf-8") as fh:
                meta = json.load(fh)["_meta"]
            for k in ("stata_version", "born_date", "dash_commit",
                      "extracted"):
                assert meta.get(k), (path, k)
        assert _fixture()["_meta"]["scheme"] == "stcolor"

    def test_the_refusal_set_is_confirm_formats(self):
        cases = _fixture()["cases"]
        for c, v in cases.items():
            if v["group"] == "r":
                assert v["rc"] == 198, c
            if v["group"] == "a":
                assert v["rc"] == 0, c
        assert cases["r01"]["errors"][0] == "invalid format, bogus"
        assert cases["r20"]["errors"][0] == "option xvarformat() not allowed"

    def test_every_case_is_mapped(self):
        cases = _fixture()["cases"]
        unmapped = [c for c, v in cases.items()
                    if v["group"] not in ("r", "a")
                    and c not in _CASE_SPECS and c not in _SKIPPED]
        assert not unmapped, unmapped


def _compared():
    if not os.path.exists(FIXTURE):
        return []
    return sorted(_CASE_SPECS)


class _Mismatch(Exception):
    """One fixture row that differs; collected, never swallowed: the
    loop that catches it fails naming every such row."""


def _expect(ok, why):
    if not ok:
        raise _Mismatch(why)


def _mismatches(ids, check):
    """``"id: why"`` for each id whose ``check(id)`` raised _Mismatch."""
    bad = []
    for i in ids:
        try:
            check(i)
        except _Mismatch as e:
            bad.append("%s: %s" % (i, str(e).splitlines()[0] if str(e)
                                   else "differs"))
    return bad


def _category(cid):
    """A case's family for the served subset: its fixture group and its
    first layer's plot type."""
    plots = _CASE_SPECS[cid][0]
    return (_fixture()["cases"][cid]["group"],
            plots[0].get("type") if plots else None)


#: Cases per node and the gate's served subset (pytest speed, 22oct2026):
#: the first case of each _category and every fifth case of the rest;
#: release checks every case served.  Without the fixture the one node of
#: each mode fails saying so.
_PARAMS = (probe_params(_compared(), representative(
    _compared(), _category, stride=5), size=8, saved_size=12)
    if _compared() else [pytest.param(m, (), id=m) for m in MODES])


class TestAgainstTwoway:

    @pytest.mark.parametrize("mode,group", _PARAMS)
    def test_the_axis_text(self, mode, group):
        """Every compared case of the group; the failing case ids are
        listed together."""
        from bokeh.io import curdoc
        cids = list(group)
        assert cids, FIXTURE
        fx = _fixture()

        def check(cid):
            try:
                self._one(mode, cid, fx)
            finally:
                curdoc().clear()
        bad = _mismatches(cids, check)
        assert not bad, "%d of %d cases differ:\n%s" % (
            len(bad), len(cids), "\n".join(bad))

    @staticmethod
    def _one(mode, cid, fx):
        case = fx["cases"][cid]
        _expect(case["rc"] == 0, case)
        plots, go, over, axes = _CASE_SPECS[cid]
        fmts = _fmts(**over)
        b = _built(mode, plots, formats=fmts, **go)
        fig = _figs(b)[0]
        src = fx["cases"].get(case["values_from"] or cid)
        for side in axes:
            want = case[side]
            _expect(want, (cid, side))
            fm = _writer(fig, side)
            _expect(fm is not None, (cid, side, _axis(fig, side).formatter))
            comma = "," in fm.args["fmt"].split(".")[0][1:]
            values = [_twoway_number(t, comma) for t in src[side]]
            pairs = [(v, t) for v, t in zip(values, want) if v is not None]
            if fm.args.get("labels"):
                labels = json.loads(fm.args["labels"])
                pairs = [(v, t) for v, t in pairs
                         if str(float(v)) not in labels]
            _expect(pairs, (cid, side))
            got = [dr._dash_fmt_text(v, fm.args["fmt"]) for v, _ in pairs]
            _expect(got == [t for _, t in pairs], (cid, side, fm.args["fmt"]))
