"""test_colorvar_legend.py — a colorvar plot must keep its colour key.

``_rebuild_legend`` takes ``fig.legend[0]`` as *the* legend and overwrites its
items with one key per plot layer, then applies Stata's "fewer than two keys,
no legend" rule. A discrete ``colorvar()`` plot builds its colour key as a
Legend too, and it is the only Legend on the figure — so the per-category key
was overwritten with a single key labelled with the y-variable and then
hidden. Measured end to end, before the fix:

    discrete colorvar  ->  Legend(title='rep78', items=['mpg'], visible=False)

Coloured points, and no way to tell what the colours mean. The continuous
path is unaffected: it builds a ``ColorBar``, not a Legend.

Two things make this easy to fix wrongly, and both are tested below.

**The scheme chrome must still be applied.** An earlier fix gave the legend
its background, border and label size from the scheme. Returning early when
the only Legend is a colorvar legend skips that loop and silently reinstates
the Bokeh-default legend on an economist plot region — measured, background
``#ffffff`` instead of ``#c6d3df``.

**One plot is not the general case.** With a colorvar plot *and* a plain plot
in the same figure there are two legends to keep apart, and a rule that asks
whether *every* item is a colour key gets the mixed case wrong.

The category labels come from Stata value labels, so a reader sees "Poor",
not "1".
"""
import json
import os
import sys
import tempfile

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render
from dash_render import DashRenderer

from conftest import make_spec, make_data_json

_VL = {"repair": {"1": "Poor", "2": "Fair", "3": "Avg", "4": "Good",
                  "5": "Exc"}}
_VLN = {"rep78": "repair"}
#: The colour key's labels, in order: every category of _VL.
_CATEGORIES = ["Poor", "Fair", "Avg", "Good", "Exc"]


def _df(n=20):
    return pd.DataFrame({
        "mpg": np.linspace(12.0, 41.0, n),
        "weight": np.linspace(1760.0, 4840.0, n),
        "price": np.linspace(3291.0, 15906.0, n),
        "length": np.linspace(142.0, 233.0, n),
        "rep78": np.array([1.0, 2.0, 3.0, 4.0, 5.0] * (n // 5)),
    })


def _render(plots, *, scheme="", gopts=None):
    spec = make_spec(plots)
    if scheme:
        spec["build_options"]["scheme"] = scheme
    if gopts:
        spec["graphs"][0]["graph_options"].update(gopts)
    sp = tempfile.mkstemp(".json")[1]
    dp = tempfile.mkstemp(".json")[1]
    op = tempfile.mkstemp(".html")[1]
    with open(sp, "w") as f:
        json.dump(spec, f)
    with open(dp, "w") as f:
        json.dump(make_data_json(_df(), value_labels=_VL,
                                 value_label_names=_VLN), f)
    dr = DashRenderer(sp, dp, op)
    dr.render()
    for p in (sp, dp, op):
        try:
            os.unlink(p)
        except OSError:
            pass
    return list(dr.figures.values())[0], dr


def _legends(fig):
    from bokeh.models import Legend
    return list(fig.select({"type": Legend}))


def _labels(leg):
    """The literal text of each key.

    ``LegendItem.label`` is a Bokeh ``Value``, not a dict, so ``str(label)``
    gives ``Value(value='Poor', ...)`` and every comparison silently fails.
    """
    out = []
    for it in leg.items:
        lab = it.label
        if isinstance(lab, dict):
            out.append(lab.get("value"))
        else:
            out.append(getattr(lab, "value", None) or str(lab))
    return out


_DISCRETE = [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
              "options": {"colorvar": "rep78", "colordiscrete": "yes"}}]


class TestTheDiscreteColourKeySurvives:

    def test_the_legend_is_still_on_the_figure(self):
        fig, _ = _render(_DISCRETE)
        assert _legends(fig), "the colorvar legend was removed entirely"

    def test_it_keeps_one_key_per_category(self):
        fig, _ = _render(_DISCRETE)
        cv = [l for l in _legends(fig) if _labels(l) != ["mpg"]]
        assert cv, (
            f"every legend was overwritten with the y-variable key: "
            f"{[_labels(l) for l in _legends(fig)]}"
        )
        assert _labels(cv[0]) == ["Poor", "Fair", "Avg", "Good", "Exc"], (
            _labels(cv[0])
        )

    def test_it_is_visible(self):
        fig, _ = _render(_DISCRETE)
        cv = [l for l in _legends(fig) if len(l.items) > 1]
        assert cv, "no multi-key legend survived"
        assert cv[0].visible is True, (
            "the colour key was hidden by the plot legend's "
            "fewer-than-two-keys rule"
        )

    def test_the_y_variable_is_not_a_colour_key(self):
        fig, _ = _render(_DISCRETE)
        cv = [l for l in _legends(fig) if len(l.items) > 1]
        assert cv
        assert "mpg" not in _labels(cv[0])


class TestTheSchemeChromeIsStillApplied:
    """Returning early would silently undo an earlier fix."""

    def test_the_colour_key_takes_the_schemes_background(self):
        fig, dr = _render(_DISCRETE, scheme="economist")
        want = dr.scheme.legend_bg_color
        assert want
        # The loop below passed with no legend to check.  The colour key
        # must be one it checks -- under economist it is the only legend
        # (measured 24sep2026).
        assert [l for l in _legends(fig) if _labels(l) == _CATEGORIES], (
            [_labels(l) for l in _legends(fig)]
        )
        for leg in _legends(fig):
            assert str(leg.background_fill_color) == want, (
                f"legend background {leg.background_fill_color} is not the "
                f"scheme's {want}"
            )

    def test_the_colour_key_takes_the_schemes_border(self):
        fig, dr = _render(_DISCRETE, scheme="economist")
        want = dr.scheme.legend_border_color
        assert want
        assert [l for l in _legends(fig) if _labels(l) == _CATEGORIES], (
            [_labels(l) for l in _legends(fig)]
        )
        for leg in _legends(fig):
            assert str(leg.border_line_color) == want

    def test_an_explicit_legend_size_still_wins(self):
        fig, _ = _render(_DISCRETE, scheme="economist",
                         gopts={"legend": "on size(4)"})
        sizes = {str(l.label_text_font_size) for l in _legends(fig)}
        # WP-30 P1.12a (Evidence E4): legend(size(4)) is 4 % of the 4-inch
        # reference, twoway's 11.52 pt (was '4px').
        assert "11.52pt" in sizes, sizes


class TestTheMixedCase:
    """A colorvar plot and a plain plot in one figure."""

    _MIXED = [
        {"type": "scatter", "yvar": "mpg", "xvar": "weight",
         "options": {"colorvar": "rep78", "colordiscrete": "yes"}},
        {"type": "scatter", "yvar": "price", "xvar": "weight", "options": {}},
    ]

    def test_the_colour_key_keeps_its_categories(self):
        fig, _ = _render(self._MIXED)
        cv = [l for l in _legends(fig)
              if set(_labels(l)) >= {"Poor", "Exc"}]
        assert cv, (
            f"the colour key lost its categories: "
            f"{[_labels(l) for l in _legends(fig)]}"
        )
        # All five, in order: the two ends alone passed a key that had
        # dropped Fair, Avg and Good.
        assert _labels(cv[0]) == _CATEGORIES, _labels(cv[0])

    def test_the_plot_legend_is_separate_and_keys_the_series(self):
        fig, _ = _render(self._MIXED)
        plot = [l for l in _legends(fig)
                if set(_labels(l)) & {"mpg", "price"}]
        assert plot, (
            f"no plot legend: {[_labels(l) for l in _legends(fig)]}"
        )
        assert set(_labels(plot[0])) == {"mpg", "price"}, _labels(plot[0])

    def test_they_are_two_different_legends(self):
        fig, _ = _render(self._MIXED)
        assert len(_legends(fig)) >= 2, (
            "the colour key and the series key were merged into one legend"
        )
        # Exactly the two (measured 24sep2026); a duplicated key passed
        # ">= 2".
        assert len(_legends(fig)) == 2, [_labels(l) for l in _legends(fig)]


class TestTheContinuousPathIsUnchanged:
    """Guards the fix against over-reach; passes before and after."""

    def test_a_continuous_colorvar_keeps_its_colorbar(self):
        from bokeh.models import ColorBar
        fig, _ = _render([{"type": "scatter", "yvar": "mpg",
                           "xvar": "weight",
                           "options": {"colorvar": "length"}}])
        bars = list(fig.select({"type": ColorBar}))
        assert bars, "the continuous colour bar was removed"
        assert bars[0].visible is True


class TestNoColorvarIsUnchanged:
    """Stata's legend rule must still govern an ordinary plot."""

    def test_one_series_still_draws_no_legend(self):
        fig, _ = _render([{"type": "scatter", "yvar": "mpg",
                           "xvar": "weight", "options": {}}])
        assert all(l.visible is False for l in _legends(fig)), (
            "twoway draws no legend for a one-key plot"
        )

    def test_two_series_still_draw_one(self):
        fig, _ = _render([
            {"type": "scatter", "yvar": "mpg", "xvar": "weight",
             "options": {}},
            {"type": "scatter", "yvar": "price", "xvar": "weight",
             "options": {}},
        ])
        vis = [l for l in _legends(fig) if l.visible]
        assert vis and set(_labels(vis[0])) == {"mpg", "price"}
