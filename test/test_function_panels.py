"""function under by() is evaluated per panel (WP-31 C12).

Measured (StataNow 19.5): twoway evaluates a function layer once per by()
panel, each over the same range() (0 1 unless given; xrescale does not
change it), in panel order, so ``function y = runiform(), by(foreign)``
draws different points in each panel; dash evaluated it once and drew the
same points in every panel.  dash.ado now writes, under by(), the layer's
points as ``{"panels": {"<i>": points}}`` (i the panel's place from 0) and
both renderers draw panel i's own.  ``function =x`` is refused r(198) as
twoway refuses it (dash drew it).
"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402

_ROOT = os.path.join(os.path.dirname(__file__), "..")


def _pts(y):
    return {"x0": 0.0, "dx": 1.0 / (len(y) - 1), "y": list(y)}


def _fn_spec(points):
    return tp._spec([{"type": "function", "expr": "y = runiform()",
                      "options": {"n": "3"}, "points": points}],
                    graph_options={"by": "foreign"})


def _figures(model, out):
    """Every figure under *model*, in layout order."""
    if type(model).__name__.lower() == "figure":
        out.append(model)
        return out
    for kid in getattr(model, "children", None) or []:
        if isinstance(kid, tuple):
            kid = kid[0]
        _figures(kid, out)
    return out


def _panel_ys(mode, spec):
    """The function line's y in each panel, in layout order."""
    if mode == "saved":
        r, _w = tp._standalone(spec)
        roots = [r._last_layout_root]
    else:
        doc, _w = tp._served(spec)
        roots = list(doc.roots)
    figs = []
    for root in roots:
        _figures(root, figs)
    out = []
    for f in figs:
        ys = [list(np.asarray(g.data_source.data[g.glyph.y], dtype=float))
              for g in f.renderers
              if type(g.glyph).__name__ == "Line"]
        if ys:
            out.append(ys[0])
    return out


class TestFunctionPerPanel:

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_points_per_panel(self, mode):
        spec = _fn_spec({"panels": {"0": _pts([0.1, 0.2, 0.3]),
                                    "1": _pts([0.7, 0.8, 0.9])}})
        got = _panel_ys(mode, spec)
        assert got == [[0.1, 0.2, 0.3], [0.7, 0.8, 0.9]]

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_flat_form_when_one_range(self, mode):
        spec = _fn_spec(_pts([0.1, 0.2, 0.3]))
        assert _panel_ys(mode, spec) == [[0.1, 0.2, 0.3]] * 2

    def test_panel_spec(self):
        g = {"plots": [{"type": "function", "points": {
            "panels": {"0": _pts([1, 2]), "1": _pts([3, 4])}}},
            {"type": "scatter"}]}
        p1 = dr._dash_fn_panel_spec(g, 1)
        assert p1["plots"][0]["points"]["y"] == [3, 4]
        assert p1["plots"][1] is g["plots"][1]
        assert dr._dash_fn_panel_spec(g, 5)["plots"][0]["points"] is None
        flat = {"plots": [{"type": "function", "points": _pts([1, 2])}]}
        assert dr._dash_fn_panel_spec(flat, 0) is flat

    def test_malformed_words(self):
        # twoway: `function 2x' "error in expression: 2x" r(198); `y='
        # and `y = ' "nothing found where expression expected" r(111) --
        # dash already said these; `=x' r(198), where dash drew it.
        with open(os.path.join(_ROOT, "dash.ado"), encoding="utf-8") as fh:
            ado = fh.read()
        assert "WP-31 C12: a bare `=' before the expression" in ado
