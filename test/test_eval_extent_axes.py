"""
test_eval_extent_axes.py -- the axes of a layer that draws no point.

BUGS.md "Axes of a layer that draws no point: twoway keeps the scale of
what it evaluates" (WP-32).  Where a layer has rows but draws no point,
twoway still scales the axis it evaluates on and leaves the other empty;
dash drew both axes empty.  Measured 18oct2026 (StataNow 19.5) on
test_mode_parity._DF (ten rows), `.Graph.xaxis1.major` and the scales:

* ``twoway (lowess mpg weight) if price >= 10000`` (two rows): x 2000(200)
  2600, y empty;
* qfit, fpfit and lowess ``if price >= 11385`` (one row): x ticks 2649 and
  2651, y empty;
* lpoly ``if foreign == 1``: x 1500(500)3500; lpoly and lpolyci ``if price
  >= 4500``: x 2000(500)4000, y empty;
* ``lpoly mpg weight`` on all ten rows (one point drawn): x 2000(500)4000;
* a histogram of no rows: y ticks -1 and 1, x empty.

The layer's evaluation x (the x range of its estimation sample) is in the
x hull, and a histogram's 0 in its density axis, in the build, the served
re-finish and the saved page's finish.
"""
import os
import sys
import warnings

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import dash_render as dr  # noqa: E402
import js_runner  # noqa: E402
import test_by_scales as tb  # noqa: E402
import test_mode_parity as tm  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_MODES = ("saved", "served")
_K25 = [2000.0, 2500.0, 3000.0, 3500.0, 4000.0]

#: (id, plot type, graph if, x ticks, y ticks), measured (module doc).
_BUILD = [
    ("lowess-two-rows", "lowess", "price >= 10000",
     [2000.0, 2200.0, 2400.0, 2600.0], []),
    ("qfit-one-row", "qfit", "price >= 11385", [2649.0, 2651.0], []),
    ("fpfit-one-row", "fpfit", "price >= 11385", [2649.0, 2651.0], []),
    ("lowess-one-row", "lowess", "price >= 11385", [2649.0, 2651.0], []),
    ("lpoly-foreign", "lpoly", "foreign == 1",
     [1500.0, 2000.0, 2500.0, 3000.0, 3500.0], []),
    ("lpoly-4500", "lpoly", "price >= 4500", _K25, []),
    ("lpolyci-4500", "lpolyci", "price >= 4500", _K25, []),
    ("histogram-no-rows", "histogram", "price > 1e9", [], [-1.0, 1.0]),
]


def _ticks(f, letter):
    sides = (f.left + f.right) if letter == "y" else (f.below + f.above)
    ax = [a for a in sides if type(a).__name__.endswith("Axis")][0]
    return [float(v) for v in tb._major_ticks(ax)]


def _spec(ptype, if_expr="", filt=""):
    spec = tm._spec([plot_for(ptype, {})],
                    {"filter": filt} if filt else None)
    if if_expr:
        spec["graphs"][0]["if_expr"] = if_expr
        spec["graphs"][0]["graph_options"]["if_expr"] = if_expr
    return spec


def _built(mode, spec):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if mode == "saved":
            r, _ = tm._standalone(spec)
            return r, list(r.figures.values())[0]
        doc, _ = tm._served(spec)
        return doc, tb._figs_of(doc.roots)[0]


class TestTheBuildScalesWhatTheLayerEvaluates:
    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("case", _BUILD, ids=[c[0] for c in _BUILD])
    def test_ticks_match_twoway(self, case, mode):
        _id, ptype, q, want_x, want_y = case
        _, f = _built(mode, _spec(ptype, q))
        assert (_ticks(f, "x"), _ticks(f, "y")) == (want_x, want_y)

    @pytest.mark.parametrize("mode", _MODES)
    def test_lpoly_on_every_row_scales_its_grid(self, mode):
        """One point drawn of the ten-point grid: x over the grid."""
        _, f = _built(mode, _spec("lpoly"))
        assert _ticks(f, "x") == _K25

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_drawn_fit_keeps_its_axes(self, mode):
        """Where the fit draws, the evaluation x is the line's own span:
        lowess on every row keeps the ticks it drew before."""
        _, f = _built(mode, _spec("lowess"))
        assert _ticks(f, "x") == _K25


class TestAfterAMove:
    """The same scale after a move that leaves the layer drawing nothing,
    the saved page through its own script under node."""

    @staticmethod
    def _moved(mode, spec, kind, value):
        obj, _f = _built(mode, spec)
        if mode == "saved":
            r = obj
            w = [x for x in r.filter_widgets if type(x).__name__ == kind][0]
            w.value = value
            js_runner.JsSession(r.filter_callbacks).run(
                r.filter_callbacks[r.filter_widgets.index(w)])
            return list(r.figures.values())[0]
        w = [x for x in tm._widgets_of(obj) if type(x).__name__ == kind][0]
        tm._fire(w, value)
        return tb._figs_of(obj.roots)[0]

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("ptype", ["lpoly", "lpolyci"])
    def test_lpoly_slider_to_4500(self, mode, ptype):
        f = self._moved(mode, _spec(ptype, filt="price, type(slider)"),
                        "Slider", 4500.0)
        assert (_ticks(f, "x"), _ticks(f, "y")) == (_K25, [])

    @pytest.mark.parametrize("mode", _MODES)
    def test_lowess_slider_to_10000(self, mode):
        f = self._moved(mode, _spec("lowess", filt="price, type(slider)"),
                        "Slider", 10000.0)
        assert (_ticks(f, "x"), _ticks(f, "y")) == (
            [2000.0, 2200.0, 2400.0, 2600.0], [])


class TestTheHelpers:
    def test_tag_takes_the_samples_x_range(self):
        """_dash_tag_eval_extent: finite x and y rows only, a range() or a
        recast() leaves the layer unstamped, a histogram's 0 on its density
        axis (y, x when horizontal)."""
        from bokeh.models import ColumnDataSource
        from bokeh.plotting import figure
        src = ColumnDataSource({"x": [1.0, 5.0, 9.0, float("nan")],
                                "y": [2.0, float("nan"), 3.0, 4.0]})
        m = type("M", (), {"date_vars": {}})()

        def stamp(pt, opts):
            fig = figure()
            fig.line([0, 1], [0, 1])
            dr._dash_tag_eval_extent(m, fig, frozenset(), pt, src, None,
                                     opts, "y", "x")
            return getattr(fig.renderers[0], "_dash_eval_extent", None)

        ev = stamp("lowess", {})
        assert ev["letter"] == "x" and ev["source"].data["v"] == [1.0, 9.0]
        assert stamp("lowess", {"range": "0 4"}) is None
        assert stamp("lpoly", {"recast": "scatter"}) is None
        assert stamp("scatter", {}) is None
        h = stamp("histogram", {})
        assert (h["letter"], h["source"].data["v"]) == ("y", [0.0])
        assert stamp("histogram", {"horizontal": "horizontal"})["letter"] \
            == "x"

    def test_values_read_one_letter(self):
        from bokeh.models import ColumnDataSource
        r = type("R", (), {})()
        r._dash_eval_extent = {"letter": "x", "source": ColumnDataSource(
            {"v": [3.0, float("nan"), 7.0]})}
        assert dr._dash_eval_values(r, "x") == [3.0, 7.0]
        assert dr._dash_eval_values(r, "y") == []
        assert dr._dash_eval_values(object(), "x") == []
