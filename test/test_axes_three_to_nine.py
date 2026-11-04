"""yaxis(3)..yaxis(9) and xaxis(3)..xaxis(9): axes three to nine (WP-31 C10c).

GAPS3 C10: dash refused ``yaxis(3)`` -- "dash draws two axes", r(198) --
where twoway draws up to nine axes of each letter.  What twoway does,
measured in test/fixtures/axes_n_truth.json (scripts/extract_axes_n_truth.do,
s2color, from graph export svg and the .Graph class):

* ``sides``: with three or more axes of a letter every one is on the first
  side (y on the left, x below), axis 1 innermost and the rest outward in
  number order; with two the lower-numbered is on the first side and the
  higher opposite (axes 1 and 3: 3 on the right; 2 and 3: 2 on the left);
  a lone axis 3 is one left axis.
* ``ties``: a layer naming several axes joins them into one scale with
  every layer on any of them (``yaxis(1 3)`` beside ``yaxis(3)``: axes 1
  and 3 read 0-15906 and axis 2 its own).
* ``routed``: ylabel(), ytitle(), yscale(log), yline() and ytick() with
  ``axis(3)`` reach the third axis.

dash.ado routes the ``axis(3)``-``axis(9)`` options into the graph's
``axisn`` object; both renderers draw a ``y<n>``/``x<n>`` range and axis
for each axis a layer names, on twoway's side.
"""
import json
import os
import re
import sys
import tempfile
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402
from conftest import drawn_renderers  # noqa: E402

_FIX = os.path.join(_HERE, "fixtures", "axes_n_truth.json")
_SRC = os.path.join(_HERE, "..", "dash_render.py")
MODES = ("saved", "served")


@pytest.fixture(scope="module")
def truth():
    with open(_FIX, encoding="utf-8") as fh:
        return json.load(fh)


def _models(mode, spec):
    if mode == "saved":
        r, _w = tp._standalone(spec)
        return list(r._last_layout_root.references())
    doc, _w = tp._served(spec)
    return [m for root in doc.roots for m in root.references()]


def _build(mode, plots, go=None):
    from bokeh.models import GlyphRenderer, Plot
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        models = _models(mode, tp._spec(plots, None, go))
    figs = [m for m in models if isinstance(m, Plot)
            and any(isinstance(r, GlyphRenderer) for r in drawn_renderers(m))]
    assert len(figs) == 1, figs
    return figs[0]


def _axes(fig, letter):
    """``{axis number: (side, order from the plot region outward)}`` of
    *fig*'s continuous axes of *letter*."""
    from bokeh.models.axes import ContinuousAxis
    sides = ("left", "right") if letter == "y" else ("below", "above")
    out = {}
    for side in sides:
        on = [a for a in getattr(fig, side) if isinstance(a, ContinuousAxis)]
        for i, a in enumerate(on, 1):
            name = getattr(a, letter + "_range_name")
            n = 1 if name == "default" else int(name[1:])
            out[n] = (side, i)
    return out


def _glyphs(fig):
    from bokeh.models import GlyphRenderer
    return [r for r in drawn_renderers(fig) if isinstance(r, GlyphRenderer)]


def _three():
    return [plot_for("scatter", {}),
            plot_for("scatter", {"yaxis": "2"}, yvar="price"),
            plot_for("line", {"yaxis": "3"}, yvar="foreign")]


def _measured(truth, key):
    return {a["axis"]: (a["side"], a["order"])
            for a in truth["sides"][key]["axes"]}


class TestTheFixture:
    def test_meta(self, truth):
        assert sorted(truth["_meta"]) == ["born_date", "dash_commit",
                                          "extracted", "source",
                                          "stata_version"]
        assert truth["_meta"]["source"] == "scripts/extract_axes_n_truth.do"

    def test_keys(self, truth):
        assert sorted(truth) == ["_meta", "bounds", "refusals", "routed",
                                 "sides", "ties"]
        assert {"y2", "y3", "y4", "x3", "y13", "y23_no1",
                "y3_lone"} <= set(truth["sides"])
        assert truth["bounds"]["yaxis10"]["rc"] == 125
        assert truth["bounds"]["yaxis9"]["rc"] == 0


class TestTheAccessors:
    @pytest.mark.parametrize("value,expect", [
        ("1", [1]), ("2", [2]), ("1 2", [1, 2]), ("3", [3]), ("9 3", [3, 9]),
        ("abc", [1]), ("10", [1]), ("", [1]), (None, [1])])
    def test_axis_nos(self, value, expect):
        assert dr._dash_axis_nos({"yaxis": value}, "y") == expect

    def test_axis_nos_of_no_dict(self):
        assert dr._dash_axis_nos(None, "y") == [1]
        assert dr._dash_axis_nos({"xaxis": "4"}, "x") == [4]

    def test_axis_no_is_the_lowest(self):
        assert dr._dash_axis_no({"yaxis": "2 3"}, "y") == 2
        assert dr._dash_axis_no({"yaxis": "1 3"}, "y") == 1
        assert dr._dash_axis_no({}, "y") == 1

    def test_axisn_value(self):
        go = {"ylabel2": "0(1)5", "axisn": {"y3": {"label": "150(20)230",
                                                   "title": 5}}}
        assert dr._dash_axisn_value(go, "y", 2, "label") == "0(1)5"
        assert dr._dash_axisn_value(go, "y", 3, "label") == "150(20)230"
        assert dr._dash_axisn_value(go, "y", 3, "title") == ""
        assert dr._dash_axisn_value(go, "y", 4, "label") == ""
        assert dr._dash_axisn_value({"axisn": ["y3"]}, "y", 3, "label") == ""
        assert dr._dash_axisn_value({"axisn": {"y3": "x"}}, "y", 3,
                                    "label") == ""
        assert dr._dash_axisn_value(None, "y", 3, "label") == ""

    def test_groups(self, truth):
        # The fixture's ties: the axes one plot region reads are one group.
        cases = {
            "13": [{"yaxis": "1 3"}, {"yaxis": "3"}, {"yaxis": "2"}],
            "23": [{}, {"yaxis": "2 3"}, {"yaxis": "4"}],
        }
        for key, opts in cases.items():
            groups = dr._dash_axis_groups(
                [{"options": o} for o in opts], "y")
            regions = [sorted(int(t) for t in d.split())
                       for d in truth["ties"][key]["yaxis_dexes"]]
            for region in regions:
                assert len({groups[n] for n in region}) == 1, (key, region)
            assert len({groups[r[0]] for r in regions}) == len(regions)

    def test_range_canonical(self):
        from bokeh.models import Range1d
        from bokeh.plotting import figure
        fig = figure()
        shared = Range1d(0, 1)
        fig.extra_y_ranges = {"y2": shared, "y3": shared,
                              "y4": fig.y_range}
        assert dr._dash_range_canonical(fig, "y", "y3") == "y2"
        assert dr._dash_range_canonical(fig, "y", "y4") == "default"
        assert dr._dash_range_canonical(fig, "y", "y9") == "y9"
        assert dr._dash_range_canonical(fig, "y", "default") == "default"


class TestSides:
    @pytest.mark.parametrize("key", ["y2", "y3", "y4", "x3", "y13",
                                     "y23_no1", "y3_lone"])
    def test_each_measured_pair(self, truth, key):
        letter = key[0]
        measured = _measured(truth, key)
        used = sorted(measured)
        for n, (side, _order) in measured.items():
            assert dr._dash_axis_side_default(letter, n, used) == side, n
            assert dr.SchemeParser("s2color").axis_side(letter, n,
                                                        used) == side, n

    def test_two_axes_keep_the_alt_rule(self):
        sp = dr.SchemeParser("economist")
        assert sp.axis_side("y", 1) != sp.axis_side("y", 2)


@pytest.mark.parametrize("mode", MODES)
class TestThreeAxes:
    def test_ranges_axes_and_sides(self, truth, mode):
        fig = _build(mode, _three())
        assert sorted(fig.extra_y_ranges) == ["y2", "y3"]
        assert _axes(fig, "y") == _measured(truth, "y3")
        assert [r.y_range_name for r in _glyphs(fig)] == ["default", "y2",
                                                          "y3"]
        assert fig.extra_y_ranges["y2"] is not fig.extra_y_ranges["y3"]

    def test_four_y_axes(self, truth, mode):
        fig = _build(mode, _three() + [
            plot_for("scatter", {"yaxis": "4"}, yvar="rep")])
        assert _axes(fig, "y") == _measured(truth, "y4")

    def test_three_x_axes(self, truth, mode):
        fig = _build(mode, [
            plot_for("scatter", {}),
            plot_for("scatter", {"xaxis": "2"}, xvar="price"),
            plot_for("scatter", {"xaxis": "3"}, xvar="foreign")])
        assert _axes(fig, "x") == _measured(truth, "x3")
        assert [r.x_range_name for r in _glyphs(fig)] == ["default", "x2",
                                                          "x3"]

    def test_axes_one_and_three(self, truth, mode):
        fig = _build(mode, [plot_for("scatter", {}),
                            plot_for("scatter", {"yaxis": "3"},
                                     yvar="price")])
        assert _axes(fig, "y") == _measured(truth, "y13")

    def test_ties(self, mode):
        # ties.13 and ties.23: one range object per plot region.
        fig = _build(mode, [plot_for("scatter", {"yaxis": "1 3"}),
                            plot_for("scatter", {"yaxis": "3"},
                                     yvar="price"),
                            plot_for("scatter", {"yaxis": "2"},
                                     yvar="foreign")])
        assert fig.extra_y_ranges["y3"] is fig.y_range
        assert fig.extra_y_ranges["y2"] is not fig.y_range
        assert [r.y_range_name for r in _glyphs(fig)] == ["default",
                                                          "default", "y2"]
        assert fig.y_range.end >= 11385.0
        fig = _build(mode, [plot_for("scatter", {}),
                            plot_for("scatter", {"yaxis": "2 3"},
                                     yvar="price"),
                            plot_for("scatter", {"yaxis": "3"},
                                     yvar="weight"),
                            plot_for("scatter", {"yaxis": "4"},
                                     yvar="foreign")])
        er = fig.extra_y_ranges
        assert er["y2"] is er["y3"] and er["y4"] is not er["y2"]
        assert [r.y_range_name for r in _glyphs(fig)] == ["default", "y2",
                                                          "y2", "y4"]
        assert er["y2"].start <= 1800.0 and er["y2"].end >= 11385.0

    def test_both_axes_layer_stays_tied(self, mode):
        # WP-31 C10b's yaxis(1 2): one layer, axis 2 on axis 1's range.
        fig = _build(mode, [plot_for("line", {"yaxis": "1 2"}),
                            plot_for("line", {"yaxis": "3"}, yvar="price")])
        assert fig.extra_y_ranges["y2"] is fig.y_range
        assert fig.extra_y_ranges["y3"] is not fig.y_range
        assert [r.y_range_name for r in _glyphs(fig)] == ["default", "y3"]


@pytest.mark.parametrize("mode", MODES)
class TestEachRangeSpansItsLayer:
    def test_hull(self, mode):
        fig = _build(mode, _three())
        for name, var in (("y2", "price"), ("y3", "foreign")):
            rng = fig.extra_y_ranges[name]
            lo, hi = sorted((rng.start, rng.end))
            vals = tp._DF[var]
            assert lo <= vals.min() and hi >= vals.max(), name
            assert hi - lo < 2 * (vals.max() - vals.min()) + 1, name


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("family", ["title", "label", "scale", "line",
                                    "tick"])
class TestRoutedOptions:
    def test_each_family(self, truth, mode, family):
        from bokeh.models import LogAxis, Span
        value = {"title": '"Len"', "label": "0 0.5 1", "scale": "log",
                 "line": "0.5", "tick": "0.25 0.75"}[family]
        fig = _build(mode, _three(), go={"axisn": {"y3": {family: value}}})
        ax = [a for a in fig.left if getattr(a, "y_range_name", "") == "y3"]
        assert len(ax) == 1
        ax = ax[0]
        if family == "title":
            assert truth["routed"]["title3"]["axis3_title"] == "Len"
            assert ax.axis_label == "Len"
        elif family == "label":
            assert truth["routed"]["label3"]["axis3_labels"] == [
                "230", "210", "190", "170", "150"]
            assert list(ax.ticker.ticks) == [0.0, 0.5, 1.0]
        elif family == "scale":
            assert truth["routed"]["scale3"][
                "axis3_labels_evenly_spaced"] is False
            assert isinstance(ax, LogAxis)
        elif family == "line":
            assert truth["routed"]["line3"]["line_values"] == [
                pytest.approx(200.0, abs=0.01)]
            spans = [m for m in fig.center if isinstance(m, Span)]
            assert [(s.location, s.y_range_name) for s in spans] == [
                (0.5, "y3")]
        else:
            ticks = truth["routed"]["tick3"]["axis3_tick_values"]
            assert any(abs(t - 165) < 0.1 for t in ticks)
            assert any(abs(t - 215) < 0.1 for t in ticks)
            args = dict(getattr(ax.ticker, "args", None) or {})
            assert ax.ticker is not None and (
                "0.25" in json.dumps(args, default=str)
                or 0.25 in list(getattr(ax.ticker, "ticks", []) or []))


@pytest.mark.parametrize("mode", MODES)
class TestLone:
    def test_lone_three(self, truth, mode):
        assert _measured(truth, "y3_lone") == {3: ("left", 1)}
        fig = _build(mode, [plot_for("scatter", {"yaxis": "3"})],
                     go={"axisn": {"y3": {"title": '"Only"'}}})
        assert not fig.extra_y_ranges
        assert _axes(fig, "y") == {1: ("left", 1)}
        assert fig.left[0].axis_label == "Only"


class TestNotes:
    def test_unused_axis_n_named(self):
        g = {"graph_options": {"name": "g", "axisn": {"y3": {"label": "1"}}},
             "plots": [plot_for("scatter", {})]}
        notes = dr._dash_unused_second_axis_notes(g)
        assert [k for k, _t in notes] == [("axis2-unused", "g", "ylabel3")]
        assert "axis(3)" in notes[0][1]
        g["plots"].append(plot_for("scatter", {"yaxis": "3"}))
        assert dr._dash_unused_second_axis_notes(g) == []


class TestNoReaderTestsForTwo:
    def test_grep(self):
        with open(_SRC, encoding="utf-8") as fh:
            src = fh.read()
        assert not re.search(r'"2" (not )?in _dash_axis_numbers', src)
        assert not re.search(r'_dash_axis_numbers\([^)]*\) == \["2"\]', src)
        assert not re.search(
            r'axis", "1"\)\)?\s*\)?\.strip\(\) == "2"', src)
        assert 'str(p["options"].get(d + "axis", "1")).strip() == "2"' \
            not in src


class TestCopyLists:
    def test_names(self):
        spec = tp._spec(_three())
        _tag, sp, dp = tp._write(spec)
        with tempfile.TemporaryDirectory() as d:
            ap = os.path.join(d, "app.py")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                dr.ServerAppBuilder(sp, dp).build(ap)
            with open(ap, encoding="utf-8") as fh:
                src = fh.read()
        for name in ("_dash_axis_nos", "_dash_axis_no", "_dash_axis_groups",
                     "_dash_axisn_value", "_dash_axis_side_default",
                     "_dash_range_canonical"):
            assert "def %s(" % name in src, name
