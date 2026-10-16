"""Second axes after a filter move, the first-used axis, and the axis titles
of a horizontal layer on yaxis(2) (WP-31 section 35, GAPS3 D9).

twoway's truth is test/fixtures/axis2_move_truth.json
(scripts/extract_axis2_move_truth.do): the second axes' scales with and
without ``if foreign == 1``, the side of each axis when the first layer is
not on axis 1, and the titles of ``bar mpg weight, horizontal yaxis(2)``.

A move's truth is the graph drawn under the rows the move keeps -- the
saved renderer given them as an ``if`` (test_mode_parity's oracle) --
compared with the saved page's own callback run under node
(test/js_runner.py) and with the served app after the same move.
"""

import json
import os
import sys
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from test_mode_parity import (_MOVES, _layout_tree, _sc, _served,  # noqa: E402
                              _served_after_move, _spec)
from test_saved_filter_layers import _move, _render  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "axis2_move_truth.json")
with open(_FIXTURE, encoding="utf-8") as _fh:
    _TRUTH = json.load(_fh)

#: auto's variable labels, as twoway titles the axes with them; dash's test
#: frame has none, so it titles them with the names.
_LABEL_OF = {"Weight (lbs.)": "weight", "Mileage (mpg)": "mpg",
             "Price": "price"}

_Y2 = [_sc(), plot_for("line", {"yaxis": "2"}, yvar="price")]
_X2 = [_sc(), plot_for("scatter", {"xaxis": "2"}, xvar="price")]
_Y3 = [_sc(), plot_for("scatter", {"yaxis": "2"}, yvar="price"),
       plot_for("line", {"yaxis": "3"}, yvar="foreign")]
_RANGE = ("range to 2000-3000", "weight, type(range)",
          ("RangeSlider", (2000.0, 3000.0)), "weight >= 2000 & weight <= 3000")
_EVERY = ("range over every row", "price, type(range)",
          ("RangeSlider", (0.0, 1e9)), "price >= 0")


def _extra(fig):
    """``{name: (start, end)}`` of a Bokeh figure's extra ranges."""
    return {k: (float(v.start), float(v.end)) for k, v in
            list(fig.extra_y_ranges.items())
            + list(fig.extra_x_ranges.items())}


def _extra_of_profile(p):
    a = p["axes"]
    return {k: (v["start"], v["end"])
            for k, v in list(a["extra_y"].items()) + list(a["extra_x"].items())}


def _figs(r):
    return list(r.figures.values())


def _oracle(spec, if_expr):
    """The saved renderer's extra ranges with *if_expr* on every graph."""
    q = json.loads(json.dumps(spec))
    q["build_options"]["filter"] = ""
    for g in q["graphs"]:
        g["if_expr"] = if_expr
    return [_extra(f) for f in _figs(_render(q))]


def _saved_moved(spec, action):
    r = _render(spec)
    _move(r, action)
    return [_extra(f) for f in _figs(r)]


def _served_moved(spec, action):
    figs, _ = _served_after_move(spec, action)
    return [_extra_of_profile(f) for f in figs]


def _close(a, b, tol=1e-9):
    assert len(a) == len(b), (a, b)
    for fa, fb in zip(a, b):
        assert sorted(fa) == sorted(fb), (a, b)
        for k in fa:
            for x, y in zip(fa[k], fb[k]):
                assert abs(x - y) <= tol * max(1.0, abs(y)), (k, a, b)


def _profiles(mode, spec):
    """The figure profiles of *spec* in *mode*."""
    figs = []
    if mode == "saved":
        _layout_tree(_render(spec)._last_layout_root, figs)
    else:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            doc, _ = _served(spec)
        _layout_tree(doc.roots[0], figs)
    return figs


def _sides(profile, letter):
    """``[(panel, title, range name)]`` of the visible axes of *letter*."""
    which = 1 if letter == "y" else 0
    return [(a["panel"], a["label"], a["range_names"][which])
            for a in profile["axes"][letter] if a["visible"]]


class TestTheFixture:
    def test_meta(self):
        assert sorted(_TRUTH["_meta"]) == ["born_date", "dash_commit",
                                           "extracted", "source",
                                           "stata_version"]
        assert _TRUTH["_meta"]["source"] == \
            "scripts/extract_axis2_move_truth.do"

    def test_keys(self):
        assert sorted(_TRUTH) == ["_meta", "first_used", "horizontal",
                                  "move"]
        assert {"full", "foreign", "x2full", "x2foreign", "x2range"} <= \
            set(_TRUTH["move"])
        assert {"y23", "y32", "y2opts", "y12"} <= set(_TRUTH["first_used"])
        assert {"y2", "ctrl"} <= set(_TRUTH["horizontal"])


class TestTheRangeFollowsAMove:
    """Guards (measured at fdd8f45: both modes already re-fit the extra
    ranges through the axis plan and _dash_refinish_axes)."""

    def test_y2_saved(self):
        spec = _spec(_Y2, {"filter": _MOVES[0][1]})
        moved = _saved_moved(spec, _MOVES[0][2])
        _close(moved, _oracle(spec, _MOVES[0][3]))
        assert moved != [_extra(f) for f in _figs(_render(spec))]

    def test_y2_served(self):
        spec = _spec(_Y2, {"filter": _MOVES[0][1]})
        _close(_served_moved(spec, _MOVES[0][2]),
               _oracle(spec, _MOVES[0][3]), 1e-5)

    def test_x2_saved(self):
        spec = _spec(_X2, {"filter": _RANGE[1]})
        _close(_saved_moved(spec, _RANGE[2]), _oracle(spec, _RANGE[3]))

    def test_x2_served(self):
        spec = _spec(_X2, {"filter": _RANGE[1]})
        _close(_served_moved(spec, _RANGE[2]), _oracle(spec, _RANGE[3]),
               1e-5)

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_y3(self, mode):
        spec = _spec(_Y3, {"filter": _MOVES[0][1]})
        got = (_saved_moved if mode == "saved" else _served_moved)(
            spec, _MOVES[0][2])
        _close(got, _oracle(spec, _MOVES[0][3]), 1e-5)

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_by_panels(self, mode):
        spec = _spec([_sc(), plot_for("scatter", {"yaxis": "2"},
                                      yvar="price")],
                     {"filter": _MOVES[1][1]}, {"by": "foreign"})
        got = (_saved_moved if mode == "saved" else _served_moved)(
            spec, _MOVES[1][2])
        _close(got, _oracle(spec, _MOVES[1][3]), 1e-5)

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_identity_move(self, mode):
        spec = _spec(_Y2, {"filter": _EVERY[1]})
        before = [_extra(f) for f in _figs(_render(spec))]
        got = (_saved_moved if mode == "saved" else _served_moved)(
            spec, _EVERY[2])
        _close(got, before, 1e-5)

    def test_twoway_covers_the_kept_rows(self):
        """twoway's yaxis2 under ``if foreign == 1`` runs over the kept
        prices (3,748 to 14,000 on auto); the oracle's y2 range is the hull
        of the kept rows plus the plot-region margin, so it holds the kept
        rows (the hull rule widens it to the labels around them)."""
        t = _TRUTH["move"]["foreign"]["yscales"]["2"]
        assert t == [3748.0, 14000.0]
        spec = _spec(_Y2, {"filter": _MOVES[0][1]})
        lo, hi = _saved_moved(spec, _MOVES[0][2])[0]["y2"]
        import test_mode_parity as mp
        kept = mp._DF.loc[mp._DF["foreign"] == 1, "price"]
        assert lo < kept.min() and hi > kept.max()


class TestThePlan:
    def test_extra_axes_are_planned(self):
        r = _render(_spec(_Y3, {"filter": _MOVES[0][1]}))
        plan, _ = dr._dash_axis_plan(r.figures, getattr(r, "_facet_map", {}),
                                     zoom=False)
        axes = [a for g in json.loads(plan) for p in g["panels"]
                for a in p["axes"] if a["name"] != "default"]
        assert sorted(a["name"] for a in axes) == ["y2", "y3"]
        assert all(a["range"] >= 0 and a["layers"] for a in axes)


def _first_used_cases():
    a = plot_for("scatter", {"yaxis": "2"})
    b = plot_for("scatter", {"yaxis": "3"}, yvar="price")
    return [("y23", [a, b]), ("y32", [b, a])]


class TestFirstUsed:
    """twoway draws the first axis its layers use on the first side and
    the second opposite (fixture ``first_used``)."""

    @pytest.mark.parametrize("mode", ["saved", "served"])
    @pytest.mark.parametrize("key,plots", _first_used_cases(),
                             ids=["y23", "y32"])
    def test_sides(self, mode, key, plots):
        truth = {a["side"]: a["labels"] for a in
                 _TRUTH["first_used"][key]["axes"]
                 if a["side"] in ("left", "right")}
        # Which variable each side shows: mpg's labels run 10-40.
        want = {side: ("mpg" if "40" in labels else "price")
                for side, labels in truth.items()}
        p = _profiles(mode, _spec(plots))[0]
        got = {}
        for panel, title, _ in _sides(p, "y"):
            got.setdefault(panel, []).append(title)
        assert got == {side: [v] for side, v in want.items()}, got

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_options_follow_their_layer(self, mode):
        """``ylabel(0(10)50, axis(2))`` labels the axis the axis-2 layer is
        drawn on -- the left one when it is the first used."""
        a, b = _first_used_cases()[0][1]
        truth = {x["side"]: x["labels"] for x in
                 _TRUTH["first_used"]["y2opts"]["axes"]}
        assert truth["left"] == ["50", "40", "30", "20", "10", "0"]
        go = {"ylabel2": "0(10)50", "ytitle2": "Two"}
        p = _profiles(mode, _spec([a, b], None, go))[0]
        left = [x for x in p["axes"]["y"] if x["panel"] == "left"
                and x["visible"]]
        assert len(left) == 1
        assert left[0]["label"] == "Two"
        assert left[0]["ticks"] == [0.0, 10.0, 20.0, 30.0, 40.0, 50.0]

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_axis_one_first_is_unchanged(self, mode):
        """Guard: the first layer on axis 1 keeps it on the left."""
        p = _profiles(mode, _spec(_Y2))[0]
        assert [(s, t) for s, t, _ in _sides(p, "y")] == [
            ("left", "mpg"), ("right", "price")]

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_axis_one_second(self, mode):
        """``(scatter price weight, yaxis(2)) (scatter mpg weight)``: twoway
        draws axis 2, the first used, on the left and axis 1 on the right
        (fixture ``first_used.y12``)."""
        truth = {a["side"]: a["title"] for a in
                 _TRUTH["first_used"]["y12"]["axes"]
                 if a["side"] in ("left", "right")}
        assert truth == {"left": "AX2", "right": "AX1"}
        plots = [plot_for("scatter", {"yaxis": "2"}, yvar="price"),
                 plot_for("scatter")]
        p = _profiles(mode, _spec(plots))[0]
        assert [(s, t) for s, t, _ in _sides(p, "y")] == [
            ("left", "price"), ("right", "mpg")]


class TestHorizontalTitle:
    """Guards (measured at fdd8f45: both modes title a horizontal yaxis(2)
    layer's axes as twoway does)."""

    def _check(self, mode, key, plots):
        truth = {a["side"]: _LABEL_OF[a["title"]] for a in
                 _TRUTH["horizontal"][key]["axes"] if a["order"] == 1}
        p = _profiles(mode, _spec(plots))[0]
        got = {s: t for s, t, _ in _sides(p, "y") + _sides(p, "x")}
        assert got == truth

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_y2(self, mode):
        self._check(mode, "y2", [plot_for("bar", {"horizontal": "horizontal",
                                                  "yaxis": "2"})])

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_two_layers(self, mode):
        self._check(mode, "two", [
            plot_for("scatter", yvar="weight", xvar="mpg"),
            plot_for("bar", {"horizontal": "horizontal", "yaxis": "2"})])

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_control(self, mode):
        self._check(mode, "ctrl", [plot_for("bar",
                                            {"horizontal": "horizontal"})])


class TestTheRenumbering:
    def test_options_move_with_their_axis(self):
        """``_dash_renumber_axis_options``: axis 2's options become axis
        1's, axis 3's (``axisn``) axis 2's, and an option of an axis no
        layer uses stays (WP-31 D9)."""
        go = {"ytitle2": "Two", "ylabel2": "0(10)50", "yline": "5",
              "yline2": "7"}
        axisn = {"y3": {"title": "Three", "scale": "log"}}
        dr._dash_renumber_axis_options(go, axisn, "y", {2: 1, 3: 2})
        assert go == {"ytitle": "Two", "ylabel": "0(10)50",
                      "yline": "5, 7", "ytitle2": "Three",
                      "yscale2": "log"}
        assert axisn == {"y3": {}}

    def test_a_swap(self):
        go = {"ytitle": "One", "ytitle2": "Two", "ylabel": "1 2"}
        dr._dash_renumber_axis_options(go, None, "y", {2: 1, 1: 2})
        assert go == {"ytitle": "Two", "ytitle2": "One", "ylabel2": "1 2"}

    def test_the_spec_rewrite(self):
        spec = _spec([plot_for("scatter", {"yaxis": "2"}),
                      plot_for("scatter", {"yaxis": "3"}, yvar="price")],
                     None, {"axisn": {"y3": {"title": "T3"}},
                            "ytitle2": "T2"})
        out = dr._dash_lone_second_axes(spec)
        g = out["graphs"][0]
        assert [p["options"].get("yaxis") for p in g["plots"]] == [None,
                                                                   "2"]
        assert g["graph_options"]["ytitle"] == "T2"
        assert g["graph_options"]["ytitle2"] == "T3"
        assert "axisn" not in g["graph_options"] \
            or not g["graph_options"]["axisn"]
        assert spec["graphs"][0]["plots"][0]["options"] == {"yaxis": "2"}

    def test_the_slots(self):
        go, axisn = {}, {"y3": {"title": "T"}}
        assert dr._dash_axis_option_slot(go, axisn, "y", 1, "ytitle") == (
            go, "ytitle")
        assert dr._dash_axis_option_slot(go, axisn, "y", 2, "ylabel") == (
            go, "ylabel2")
        box, key = dr._dash_axis_option_slot(go, axisn, "y", 3, "ytitle")
        assert (box, key) == ({"title": "T"}, "title")
        assert box is axisn["y3"]
        assert dr._dash_axis_option_slot(go, None, "y", 4, "ytitle") == (
            None, None)
