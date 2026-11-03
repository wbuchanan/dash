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


from conftest import render_models  # noqa: E402


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
    render_models(dr)
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


def _cell(fig):
    """The figure's colour key cell (WP-42 CV-3), or None."""
    return getattr(fig, "_dash_key_cell", None)


def _cell_labels(fig):
    import colour_bins
    return colour_bins.axis_key_texts(_cell(fig))


_DISCRETE = [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
              "options": {"colorvar": "rep78", "colordiscrete": "yes"}}]


class TestTheDiscreteColourKeySurvives:

    def test_the_legend_is_still_on_the_figure(self):
        fig, _ = _render(_DISCRETE)
        assert _legends(fig), "the colorvar legend was removed entirely"

    def test_it_keeps_one_key_per_category(self):
        fig, _ = _render(_DISCRETE)
        # Flipped (WP-42 CV-3): dash's colour key was a Legend of value
        # labels; twoway draws swatches beside a z axis labelled at its
        # ticks, no value labels without zlabel(, valuelabel) (CV-3;
        # colorvar_key_truth.json K1).
        assert _cell(fig) is not None
        assert _cell_labels(fig) == ["5", "4", "3", "2", "1"]
        assert len(_cell(fig)._dash_keycell["src"].data["c"]) == 5

    def test_it_is_visible(self):
        fig, _ = _render(_DISCRETE)
        # Flipped (WP-42 CV-3): dash's colour key was a Legend of value
        # labels; twoway draws swatches beside a z axis labelled at its
        # ticks, no value labels without zlabel(, valuelabel) (CV-3;
        # colorvar_key_truth.json K1).
        assert _cell(fig) is not None and _cell(fig).visible is True

    def test_the_y_variable_is_not_a_colour_key(self):
        fig, _ = _render(_DISCRETE)
        # Flipped (WP-42 CV-3): dash's colour key was a Legend of value
        # labels; twoway draws swatches beside a z axis labelled at its
        # ticks, no value labels without zlabel(, valuelabel) (CV-3;
        # colorvar_key_truth.json K1).
        assert "mpg" not in _cell_labels(fig)


class TestTheSchemeChromeIsStillApplied:
    """Returning early would silently undo an earlier fix."""

    def test_the_colour_key_takes_the_schemes_background(self):
        fig, dr = _render(_DISCRETE, scheme="economist")
        want = dr.scheme.legend_bg_color
        assert want
        # Flipped (WP-42 CV-3): dash's colour key was a Legend in the
        # scheme's legend box; twoway draws swatches beside a z axis with
        # no box of its own (CV-3), so the graph region shows through.
        c = _cell(fig)
        assert c is not None
        assert c.background_fill_alpha == 0.0 and c.border_fill_alpha == 0.0
        for leg in _legends(fig):
            assert str(leg.background_fill_color) == want, (
                f"legend background {leg.background_fill_color} is not the "
                f"scheme's {want}"
            )

    def test_the_colour_key_takes_the_schemes_border(self):
        fig, dr = _render(_DISCRETE, scheme="economist")
        want = dr.scheme.legend_border_color
        assert want
        # Flipped (WP-42 CV-3): twoway's colour key has no frame (CV-3).
        assert _cell(fig) is not None
        assert _cell(fig).outline_line_color is None
        for leg in _legends(fig):
            assert str(leg.border_line_color) == want

    def test_an_explicit_legend_size_still_wins(self):
        from dash_render import _COLORVAR_LEGEND_NAME
        fig, _ = _render(_DISCRETE, scheme="economist",
                         gopts={"legend": "on size(4)"})
        plain, _ = _render(_DISCRETE, scheme="economist",
                           gopts={"legend": "on"})
        sizes = {str(l.label_text_font_size) for l in _legends(fig)
                 if l.name != _COLORVAR_LEGEND_NAME}
        # WP-30 P1.12a (Evidence E4): legend(size(4)) is 4 % of the 4-inch
        # reference, twoway's 11.52 pt (was '4px').
        assert "11.52pt" in sizes, sizes
        # Flipped (WP-42 CV-5): legend(size()) reached the colour key too;
        # twoway's legend(size()) leaves the colour key at its own size
        # (CV-5, colorvar_plegend_truth.json Q1, Q3).
        def key_size(f):
            return str(_cell(f)._dash_keycell["axis"]
                       .major_label_text_font_size)
        assert key_size(fig) == key_size(plain)


class TestTheMixedCase:
    """A colorvar plot and a plain plot in one figure."""

    _MIXED = [
        {"type": "scatter", "yvar": "mpg", "xvar": "weight",
         "options": {"colorvar": "rep78", "colordiscrete": "yes"}},
        {"type": "scatter", "yvar": "price", "xvar": "weight", "options": {}},
    ]

    def test_the_colour_key_keeps_its_categories(self):
        fig, _ = _render(self._MIXED)
        # Flipped (WP-42 CV-3): dash's colour key was a Legend of value
        # labels; twoway draws swatches beside a z axis labelled at its
        # ticks, no value labels without zlabel(, valuelabel) (CV-3;
        # colorvar_key_truth.json K1).
        # All five levels, in order.
        assert _cell_labels(fig) == ["5", "4", "3", "2", "1"]
        assert sorted(_cell(fig)._dash_keycell["src"].data["y"]) == [
            1.0, 2.0, 3.0, 4.0, 5.0]

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
        # Flipped (WP-42 CV-3): the colour key is a key cell beside the
        # figure (twoway's axis-style key), the series legend the
        # figure's one Legend: still two keys, never merged.
        assert _cell(fig) is not None
        assert len(_legends(fig)) == 1, [_labels(l) for l in _legends(fig)]


class TestTheContinuousPathIsUnchanged:
    """Guards the fix against over-reach; passes before and after."""

    def test_a_continuous_colorvar_keeps_its_colorbar(self):
        from bokeh.models import ColorBar
        fig, _ = _render([{"type": "scatter", "yvar": "mpg",
                           "xvar": "weight",
                           "options": {"colorvar": "length"}}])
        # Flipped (WP-42 CV-3): dash's colour key was a ColorBar; twoway
        # draws swatches beside a z axis (CV-3): the key cell.
        assert not list(fig.select({"type": ColorBar}))
        assert _cell(fig) is not None and _cell(fig).visible is True


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
