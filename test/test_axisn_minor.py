"""Minor ticks and labels on axes 2 to 9 (WP-31 section 35, GAPS3 D1b).

twoway's truth is test/fixtures/axisn_minor_truth.json
(scripts/extract_axisn_minor_truth.do):

* ``ymlabel(##2, axis(2))`` labels the far-side axis 2 between its majors,
  and under ``if foreign == 1`` (the rows a filter move keeps) between the
  majors that scale gives (``m2.full`` 2,500 7,500 12,500; ``m2.foreign``
  5,000 ... 13,000);
* ``ymlabel(##2, axis(3))``, ``ymlabel(165 215, axis(3))``,
  ``ymtick(##2, axis(3))`` and ``xmlabel(##2, axis(3))`` draw on axis 3
  (``m3.*``); ``tmlabel(##2, axis(2))`` draws as ``xmlabel(##2, axis(2))``.

dash drew the far side's ``##N`` labels once, as one Label per position,
and held them after a move; axes 3-9 kept ymlabel()/ymtick() as typed and
named them.  The labels of an axis that is not the innermost on its side
(axes 3-9, or the far side) are a pool of Labels anchored on the axis's own
edge (``Node(target=<axis>)``), which both finishers re-place after a move.
"""

import json
import os
import sys
import warnings

import numpy as np
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from js_runner import requires_node  # noqa: E402
from test_saved_filter_layers import _MOVES, _move, _render  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_FIX = os.path.join(_HERE, "fixtures", "axisn_minor_truth.json")
with open(_FIX, encoding="utf-8") as _fh:
    _T = json.load(_fh)

MODES = ("saved", "served")
# y2 runs over weight: the dropdown at Foreign moves its scale (1,800 to
# 4,080 -> 1,800 to 3,350) and its majors with it.
_TWO = [plot_for("scatter"), plot_for("scatter", {"yaxis": "2"},
                                      yvar="weight")]
_THREE = [plot_for("scatter"), plot_for("scatter", {"yaxis": "2"},
                                        yvar="rep"),
          plot_for("line", {"yaxis": "3"}, yvar="weight")]
_X3 = [plot_for("scatter"), plot_for("scatter", {"xaxis": "2"},
                                     xvar="price"),
       plot_for("scatter", {"xaxis": "3"}, xvar="rep")]


def _fig_of(mode, spec, action=None):
    """(figure, notes) of *spec* in *mode*, after *action* when given."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        if mode == "saved":
            r = _render(spec)
            if action is not None:
                _move(r, action)
            figs = list(r.figures.values())
        else:
            doc, _w = tp._served(spec)
            if action is not None:
                kind, want = action
                [w] = [x for x in tp._widgets_of(doc)
                       if type(x).__name__ == kind]
                if kind == "Select":
                    want = [v for v, lab in w.options if lab == want][0]
                tp._fire(w, want)
            from bokeh.models import GlyphRenderer, Plot
            figs = [m for root in doc.roots for m in root.references()
                    if isinstance(m, Plot) and any(
                        isinstance(x, GlyphRenderer) for x in m.renderers)]
    assert len(figs) == 1
    return figs[0], [str(w.message) for w in caught]


def _axis(fig, letter, name):
    from bokeh.models.axes import ContinuousAxis
    kw = letter + "_range_name"
    sides = ("left", "right") if letter == "y" else ("below", "above")
    for side in sides:
        for a in getattr(fig, side):
            if isinstance(a, ContinuousAxis) and getattr(a, kw) == name \
                    and "dash_alt_axis" not in (a.tags or ()):
                return a
    return None


def _minor_labels(fig, letter, num):
    """Sorted positions of the visible minor labels of axis *num*."""
    from bokeh.models import Label, LabelSet
    pos = []
    for m in fig.center + fig.left + fig.right + fig.above + fig.below:
        if getattr(m, "name", None) != "dash_minor_labels" \
                or list(m.tags or []) != [letter, str(num)]:
            continue
        if isinstance(m, LabelSet):
            pos += [float(v) for v in m.source.data["pos"]]
        elif isinstance(m, Label) and m.visible:
            pos.append(float(m.x if letter == "x" else m.y))
    return sorted(pos)


def _midpoints(fig, ax, letter):
    """``##2``'s positions: one between each pair of the axis's majors,
    within its finished scale."""
    name = getattr(ax, letter + "_range_name")
    lo, hi = dr._dash_axis_scale(fig, letter, name)
    maj = sorted(float(v) for v in dr._dash_axis_majors(ax))
    step = maj[1] - maj[0]
    out, v = [], maj[0] - step / 2
    while v <= hi + 1e-9:
        if v >= lo - 1e-9:
            out.append(round(v, 9))
        v += step
    return [x for x in out if x not in maj]


class TestTheFixture:
    def test_meta(self):
        assert _T["_meta"]["source"] == \
            "scripts/extract_axisn_minor_truth.do"
        assert sorted(_T["_meta"]) == ["born_date", "dash_commit",
                                       "extracted", "source",
                                       "stata_version"]

    def test_twoway_draws_them(self):
        def col(rec, side, first):
            return [c[1] for c in rec["columns"][side]
                    if c[1] and c[1][0] == first][0]
        assert col(_T["m2"]["full"], "right", "12,500") == [
            "12,500", "7,500", "2,500"]
        assert col(_T["m2"]["foreign"], "right", "13,000") == [
            "13,000", "11,000", "9,000", "7,000", "5,000"]
        assert col(_T["m3"]["mlabel"], "left", "230") == [
            "230", "210", "190", "170", "150"]
        assert col(_T["m3"]["mlist"], "left", "215") == ["215", "165"]
        assert col(_T["m3"]["x3"], "below", "150") == [
            "150", "170", "190", "210", "230"]
        assert col(_T["m3"]["tmlabel"], "above", "2,500") == [
            "2,500", "7,500", "12,500"]
        assert _T["m3"]["unused"]["rc"] == 198


@pytest.mark.parametrize("mode", MODES)
class TestAxesThreeToNine:
    def test_mlabel_between(self, mode):
        fig, notes = _fig_of(mode, tp._spec(
            _THREE, None, {"axisn": {"y3": {"mlab": "##2"}}}))
        ax = _axis(fig, "y", "y3")
        assert _minor_labels(fig, "y", 3) == _midpoints(fig, ax, "y")
        assert not [n for n in notes if "mlabel" in n], notes

    def test_labels_sit_on_their_axis(self, mode):
        """An outer axis's labels are anchored on its own edge, not the
        frame's (measured in Chrome: Node(target=<axis 3>, symbol="right")
        resolves to axis 3's line, 61 px, where the frame's is 145)."""
        from bokeh.models import Label
        fig, _n = _fig_of(mode, tp._spec(
            _THREE, None, {"axisn": {"y3": {"mlab": "##2"}}}))
        ax = _axis(fig, "y", "y3")
        labs = [m for m in fig.center if isinstance(m, Label)
                and list(m.tags or []) == ["y", "3"]]
        assert labs
        assert all(m.x.target is ax and m.x.symbol == "right"
                   for m in labs)

    def test_mlabel_list(self, mode):
        fig, _n = _fig_of(mode, tp._spec(
            _THREE, None, {"axisn": {"y3": {"mlab": "2500 3500"}}}))
        assert _minor_labels(fig, "y", 3) == [2500.0, 3500.0]

    def test_mtick_between(self, mode):
        fig, notes = _fig_of(mode, tp._spec(
            _THREE, None, {"axisn": {"y3": {"mtick": "##2"}}}))
        ax = _axis(fig, "y", "y3")
        fx = dict(ax.ticker.args)["mfixed"]
        # The tick rule marks the majors' places too (axis 1's rule).
        ticks = {round(float(v), 9) for v in fx.ticks}
        assert set(_midpoints(fig, ax, "y")) <= ticks
        assert not [n for n in notes if "mtick" in n], notes

    def test_x3(self, mode):
        fig, _n = _fig_of(mode, tp._spec(
            _X3, None, {"axisn": {"x3": {"mlab": "##2"}}}))
        ax = _axis(fig, "x", "x3")
        assert _minor_labels(fig, "x", 3) == _midpoints(fig, ax, "x")


def _kept_build(spec, if_expr):
    q = json.loads(json.dumps(spec))
    q["build_options"]["filter"] = ""
    q["graphs"][0]["if_expr"] = if_expr
    return q


class TestTheFarSideAfterAMove:
    """ymlabel(##2, axis(2)): the far-side labels after the dropdown at
    Foreign are the kept rows' own build's."""

    def _check(self, mode, plots, go, letter, num):
        spec = tp._spec(plots, {"filter": _MOVES[0][1]}, go)
        after, _n = _fig_of(mode, spec, _MOVES[0][2])
        kept, _m = _fig_of(mode, _kept_build(spec, _MOVES[0][3]))
        built, _b = _fig_of(mode, spec)
        a = _minor_labels(after, letter, num)
        k = _minor_labels(kept, letter, num)
        assert a and np.allclose(a, k), (a, k)
        assert a != _minor_labels(built, letter, num)

    def test_served_y2(self):
        self._check("served", _TWO, {"ymlabel2": "##2"}, "y", 2)

    @requires_node
    def test_saved_y2(self):
        self._check("saved", _TWO, {"ymlabel2": "##2"}, "y", 2)

    @pytest.mark.parametrize("mode", MODES)
    def test_axis_three(self, mode):
        self._check(mode, _THREE, {"axisn": {"y3": {"mlab": "##2"}}},
                    "y", 3)


class TestARenumberedAxisKeepsItsMinorLabels:
    def test_lone_axis_three(self):
        """A lone yaxis(3) drawn as axis 1 (WP-31 D9) takes its axis-3
        ymlabel() (written ``mlab``) as ymlabel()."""
        spec = tp._spec([plot_for("scatter", {"yaxis": "3"})], None,
                        {"axisn": {"y3": {"mlab": "##2", "mtick": "##2"}}})
        g = dr._dash_lone_second_axes(spec)["graphs"][0]["graph_options"]
        assert g["ymlabel"] == "##2" and g["ymtick"] == "##2"


class TestTheInnermostAxis:
    def test_sides(self):
        from bokeh.models import LinearAxis
        from bokeh.plotting import figure
        f = figure()
        a2 = LinearAxis(y_range_name="y2")
        a3 = LinearAxis(y_range_name="y3")
        f.add_layout(a2, "left")
        f.add_layout(a3, "left")
        assert dr._dash_axis_innermost(f, f.left[0])
        assert not dr._dash_axis_innermost(f, a2)
        assert not dr._dash_axis_innermost(f, a3, "left")
        assert dr._dash_axis_innermost(f, LinearAxis())
