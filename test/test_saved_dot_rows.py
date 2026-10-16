"""dot's rows on the saved page after a filter move (WP-31 section 35,
GAPS3 B5c).

twoway draws a dot layer's rows over the finished scale
(yxview_dot_draw.ado; S18's test/fixtures/dot_truth.json), and a move's
truth is the graph drawn from the kept rows.  The served app refills the
rows after a move through ``_dash_refinish_axes``; the saved page now does
it in ``_DASH_AXIS_FINISH_JS`` (``dash_fill_dots``) from the axis plan's
``dots`` entries (``_dash_dots_plan``), with ``dash_dot_positions`` the
twin of ``GlyphMapper._dot_positions``.  The end-to-end move cases are
test_dot_rows.py::TestAfterASavedMove, test_saved_filter_layers' dot
cases and test_horizontal_moves' turned dot.
"""

import json
import os
import sys

import numpy as np
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from js_runner import requires_node, run_js  # noqa: E402
from test_mode_parity import _spec  # noqa: E402
from test_saved_filter_layers import _MOVES, _move, _render  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402


def _js_positions():
    js = dr._DASH_AXIS_FINISH_JS
    a = js.index("function dash_dot_positions(")
    b = js.index("// WP-31 B5c: each dot layer", a)
    return js[a:b]


_CASES = [
    (14.0, 22.0, [15.0, 20.0, float("nan")], True, 75.0, None),
    (14.0, 50.0, [15.0, 49.0], True, 75.0, None),
    (-5.0, 7.5, [-4.0, 2.0, 7.0], False, 20.0, None),
    (3.0, 9.0, [4.0, 8.0], True, 1.0, None),
    (-9.0, -2.0, [-3.0], True, 11.0, None),
    (0.0, 100.0, list(range(50)), True, 75.0, 500),
]


@requires_node
class TestTheTwin:
    def test_positions_match_python(self):
        calls = [[lo, hi, [v if np.isfinite(v) else None for v in vals],
                  ext, nd, lim if lim is not None else 1e18]
                 for lo, hi, vals, ext, nd, lim in _CASES]
        src = (_js_positions() + "\nconst C = " + json.dumps(calls) + ";\n"
               "console.log(JSON.stringify(C.map((c) => dash_dot_positions("
               "c[0], c[1], c[2].map((v) => v === null ? NaN : v), c[3], "
               "c[4], c[5]))));\n")
        got = run_js(src)
        for (lo, hi, vals, ext, nd, lim), (pos, rows) in zip(_CASES, got):
            want_pos, want_rows, _ = dr.GlyphMapper._dot_positions(
                lo, hi, vals, ext, nd, limit=lim)
            assert np.allclose(pos, want_pos, rtol=0, atol=0), (lo, hi)
            assert list(rows) == [int(r) for r in want_rows], (lo, hi)


class TestThePlan:
    def test_a_dot_layer_is_planned(self):
        r = _render(_spec([plot_for("dot")], {"filter": _MOVES[0][1]}))
        plan, models = dr._dash_axis_plan(r.figures,
                                          getattr(r, "_facet_map", {}),
                                          zoom=False)
        dots = [d for g in json.loads(plan) for p in g["panels"]
                for a in p["axes"] for d in a.get("dots", [])]
        assert len(dots) == 1
        d = dots[0]
        assert d["along"] == "mpg" and d["across"] == "weight"
        assert d["extend"] is True and d["ndots"] == 75.0
        assert d["max"] == dr._DASH_DOTS_MAX
        assert models[d["dsrc"]] is not models[d["msrc"]]

    def test_other_layers_plan_no_dots(self):
        r = _render(_spec([plot_for("scatter")], {"filter": _MOVES[0][1]}))
        plan, _ = dr._dash_axis_plan(r.figures, getattr(r, "_facet_map", {}),
                                     zoom=False)
        assert all(not a["dots"] for g in json.loads(plan)
                   for p in g["panels"] for a in p["axes"])

    def test_dots_plan_refuses_another_axis(self):
        r = _render(_spec([plot_for("dot")]))
        f = list(r.figures.values())[0]
        [d] = [x for x in f.renderers if "dash_dots" in (x.tags or ())]
        assert dr._dash_dots_plan(d, "x", "default", {}, []) is None
        assert dr._dash_dots_plan(d, "y", "y2", {}, []) is None
        models = []
        got = dr._dash_dots_plan(d, "y", "default", {}, models)
        assert got is not None and len(models) >= 2


@requires_node
class TestAMoveRebuildsTheRows:
    @pytest.mark.parametrize("opts", [{}, {"dotextend": "no"},
                                      {"ndots": "20"}])
    def test_saved_equals_the_kept_build(self, opts):
        """After the dropdown at Foreign (y 10..40 -> 14..40) the rows are
        the kept rows' own build's."""
        spec = _spec([plot_for("dot", opts)], {"filter": _MOVES[0][1]})
        r = _render(spec)
        _move(r, _MOVES[0][2])
        q = json.loads(json.dumps(spec))
        q["build_options"]["filter"] = ""
        q["graphs"][0]["if_expr"] = _MOVES[0][3]
        k = _render(q)

        def dots(rr):
            f = list(rr.figures.values())[0]
            [d] = [x for x in f.renderers if "dash_dots" in (x.tags or ())]
            return d.data_source.data

        a, b = dots(r), dots(k)
        assert np.allclose(a["y"], b["y"]) and list(a["x"]) == list(b["x"])
