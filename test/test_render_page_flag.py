"""WP-34 AX-3: ``DashRenderer.render(page=False)`` builds every figure as
``render()`` does and skips the page.

The served route draws its figures once inside Stata before it writes the
app, to ask Stata for the ticks the saved page would ask for
(``main()``'s pre-pass); that pass needs the figures, not the page.

While iterating: ``python3 -m pytest test/test_render_page_flag.py -q``.
"""
import os
import sys
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_default_axes as tda  # noqa: E402

P = tda.P


def _ticks_of(r):
    out = []
    for name in sorted(r.figures):
        f = r.figures[name]
        for ax in f.left + f.right + f.below + f.above:
            t = getattr(ax, "ticker", None)
            out.append((name, type(ax).__name__,
                        list(getattr(t, "ticks", None) or [])))
    return out


class TestPageFlag:
    @pytest.mark.parametrize("plots,go", [
        ([P("scatter", "price", "mpg")], {"by": "foreign"}),
        ([P("histogram", "mpg")], {}),
        ([P("scatter", "price", "mpg")], {"ymtick": "#4"}),
    ])
    def test_same_figures(self, plots, go):
        """page=False returns "" and leaves every figure's tick lists as
        render() leaves them."""
        _t, sp, dp = tda._write(tda._spec(plots, go))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            a = dr.DashRenderer(sp, dp)
            html = a.render()
            b = dr.DashRenderer(sp, dp)
            out = b.render(page=False)
        assert html.startswith("<!DOCTYPE html>") and out == ""
        assert _ticks_of(a) == _ticks_of(b) and _ticks_of(a)

    def test_bootstrap_layout(self):
        spec = tda._spec([P("scatter", "price", "mpg")])
        spec["build_options"]["layout"] = "bs"
        _t, sp, dp = tda._write(spec)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            a = dr.DashRenderer(sp, dp)
            a.render()
            b = dr.DashRenderer(sp, dp)
            assert b.render(page=False) == ""
        assert _ticks_of(a) == _ticks_of(b)
