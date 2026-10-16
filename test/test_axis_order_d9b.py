"""WP-31 S45 (D9b): with three or more axes of a letter twoway draws them
in number order, and an added text(..., yaxis(#)) stays on its axis.

Measured (scripts/extract_axis2_move_truth.do, fixture
test/fixtures/axis2_move_truth.json ``first_used.y123 y132 y1432 y1342
y213 y243`` and ``text.y23 y23b``): with three or four y axes every axis is
on the left, outward in the order of their numbers whatever order the
layers first use them -- ``(scatter mpg weight, yaxis(2)) (scatter price
weight, yaxis(4)) (scatter trunk weight, yaxis(3))`` draws axes 2, 3, 4
outward, where dash's first-use renumbering (WP-31 D9, right for two
axes) drew 2, 4, 3; and ``text(30 3000 "TXT", yaxis(2))`` on a graph whose
axes 2 and 3 are drawn as 1 and 2 is placed on axis 2's scale (35 px below
its label 30, as ``text(10000 ..., yaxis(3))`` is 35 px below axis 3's
10,000), so it moves with its axis.

While iterating: ``python3 -m pytest test/test_axis_order_d9b.py -q``.
"""
import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from test_mode_parity import _MOVES, _spec  # noqa: E402
from test_second_axis_moves import _profiles, _sides, _TRUTH  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

MODES = ("saved", "served")

#: Each three-or-more-axis probe: the y axis number of each layer (auto's
#: mpg, price, trunk, turn in that order).  Its titles are AX<n>.
_CASES = {"y123": (1, 2, 3), "y132": (1, 3, 2), "y1432": (1, 4, 3, 2),
          "y1342": (1, 3, 4, 2), "y213": (2, 1, 3), "y243": (2, 4, 3)}
#: dash's test frame stands in four variables for auto's four.
_VARS = ("mpg", "price", "foreign", "rep")


def _measured_order(key):
    """The axis numbers twoway draws outward on the left."""
    axes = [a for a in _TRUTH["first_used"][key]["axes"]
            if a["side"] == "left"]
    assert all(a["title"].startswith("AX") for a in axes)
    return [int(a["title"][2:]) for a in sorted(axes,
                                                key=lambda a: a["order"])]


def _plots(key):
    if key == "y213":
        # auto: price on 2, mpg on 1, trunk on 3.
        order = (("price", 2), ("mpg", 1), ("foreign", 3))
    else:
        order = tuple(zip(_VARS, _CASES[key]))
    return [plot_for("scatter", {} if n == 1 else {"yaxis": str(n)},
                     yvar=v) for v, n in order]


class TestTheFixture:
    def test_probes(self):
        for key in _CASES:
            assert _TRUTH["first_used"][key]["rc"] == 0
            assert _measured_order(key) == sorted(_measured_order(key))
        assert {"y23", "y23b"} <= set(_TRUTH["text"])


class TestThreeOrMoreAxes:
    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("key", sorted(_CASES))
    def test_number_order(self, mode, key):
        """The left axes outward show the variables of the axes in number
        order, as twoway draws them."""
        plots = _plots(key)
        by_axis = {}
        for p in plots:
            n = int((p.get("options") or {}).get("yaxis", "1"))
            by_axis[n] = p["yvar"]
        want = [by_axis[n] for n in _measured_order(key)]
        prof = _profiles(mode, _spec(plots))[0]
        got = [t for side, t, _ in _sides(prof, "y") if side == "left"]
        assert got == want

    @pytest.mark.parametrize("mode", MODES)
    def test_kept_after_a_move(self, mode):
        """The order holds after a filter move (the axes are fixed when
        the spec is read; the move re-ranges them)."""
        from test_second_axis_moves import _saved_moved, _served_moved
        spec = _spec(_plots("y243"), {"filter": _MOVES[0][1]})
        got = (_saved_moved if mode == "saved" else _served_moved)(
            spec, _MOVES[0][2])
        assert got and all(set(r) >= {"y2", "y3"} for r in got)
        prof = _profiles(mode, spec)[0]
        assert [t for s, t, _ in _sides(prof, "y")] == ["mpg", "foreign",
                                                        "price"]

    def test_two_axes_keep_first_use(self):
        """Guard (D9): with two axes the first used is drawn first."""
        g = {"plots": [plot_for("scatter", {"yaxis": "3"}, yvar="price"),
                       plot_for("scatter", {"yaxis": "2"})],
             "graph_options": {}}
        out = dr._dash_lone_second_axes({"graphs": [g]})["graphs"][0]
        assert [p["options"].get("yaxis", "1") for p in out["plots"]] == \
            ["1", "2"]


class TestTextFollowsItsAxis:
    def _rec(self, yaxis):
        return {"at_y": 30.0, "at_x": 3000.0, "at_yaxis": yaxis,
                "at_xaxis": 1, "at_lines": ["TXT"], "at_opts": ""}

    def test_measured(self):
        """twoway places each text on its own axis's scale: the same
        offset below its label on axis 2 (30) and axis 3 (10,000)."""
        def off(key, label):
            r = _TRUTH["text"][key]
            txt = [t for t in r["texts"] if t["text"] == "TXT"][0]
            lab = [t for t in r["texts"] if t["text"] == label][0]
            return round(txt["y"] - lab["y"])
        assert off("y23", "30") == off("y23b", "10,000")

    @pytest.mark.parametrize("typed,drawn", [(2, 1), (3, 2)])
    def test_renumbered(self, typed, drawn):
        g = {"plots": [plot_for("scatter", {"yaxis": "2"}),
                       plot_for("scatter", {"yaxis": "3"}, yvar="price")],
             "graph_options": {"added_text": [self._rec(typed)]}}
        out = dr._dash_lone_second_axes({"graphs": [g]})["graphs"][0]
        assert out["graph_options"]["added_text"][0]["at_yaxis"] == drawn
        assert g["graph_options"]["added_text"][0]["at_yaxis"] == typed

    @pytest.mark.parametrize("mode", MODES)
    def test_drawn_on_its_axis(self, mode):
        """Both modes draw text(30 ..., yaxis(2)) on the axis mpg is drawn
        on (the first, after renumbering)."""
        from test_saved_filter_layers import _render
        import test_mode_parity as mp
        g = [plot_for("scatter", {"yaxis": "2"}),
             plot_for("scatter", {"yaxis": "3"}, yvar="price")]
        spec = _spec(g, None, {"added_text": [self._rec(2)]})
        if mode == "saved":
            models = list(_render(spec).figures.values())[0].references()
        else:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                doc, _ = mp._served(spec)
            models = doc.roots[0].references()
        labels = [m for m in models if type(m).__name__ == "Label"
                  and getattr(m, "text", "") == "TXT"]
        assert labels and all(m.y_range_name == "default" for m in labels)
