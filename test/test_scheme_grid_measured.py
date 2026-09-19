"""test_scheme_grid_measured.py — the grid mapping, checked against Stata's
own rendered output rather than against its style files.

``test_scheme_grids.py`` establishes which key governs which axis by reading
``style/axisstyle-horizontal_default.style`` and its vertical counterpart.
That reasoning is correct, and it is also exactly the kind of thing that gets
"fixed" backwards later by someone who reads ``hgrid`` as "horizontal lines".
This file corroborates it from the other direction: by exporting a real Stata
graph and counting the lines in it.

The mapping, restated, because it is the trap: a Stata grid belongs to an
**axis** and is named for that axis's orientation, not for the direction of
the lines it draws.

* ``draw_major_hgrid`` is the *horizontal axis* (x). Its major grid lines are
  the **vertical** ones at the x ticks → Bokeh's ``fig.xgrid``.
* ``draw_major_vgrid`` is the *vertical axis* (y). Its lines are
  **horizontal** → Bokeh's ``fig.ygrid``.

**Procedure.** ``scatter mpg weight`` was exported from Stata under each
scheme with ``set graphics off`` and ``graph export``, and the long lines in
each SVG counted. stcolor's grid is dashed (``linepattern major_grid dash``),
so it arrives as many short segments sharing one coordinate rather than as one
long line; counting only long lines reported it as having no grid, which is
why the counts below are taken from coordinate clusters.

    scheme      horizontal lines   vertical lines   declares h / v
    s2color            4                 0             no / yes
    s2gcolor           4                 0             no / yes
    economist          4                 0             no / yes
    s1mono             0                 0             no / no
    stcolor            4 (dashed)        4 (dashed)    yes / yes

Every row matches the declared switches under the mapping above, and no row
matches the opposite mapping — which is what makes this evidence rather than
a restatement.
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

from dash_render import DashRenderer, SchemeParser

from conftest import make_spec, make_data_json


# scheme -> (x grid visible, y grid visible), from the measurement above.
_MEASURED = {
    "s2color":   (False, True),
    "s2gcolor":  (False, True),
    "economist": (False, True),
    "s2mono":    (False, True),
    "sj":        (False, True),
    "s1mono":    (False, False),
    "stcolor":   (True,  True),
}


def _figure(scheme):
    df = pd.DataFrame({"mpg": np.linspace(12.0, 41.0, 12),
                       "weight": np.linspace(1760.0, 4840.0, 12)})
    spec = make_spec([{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}])
    spec["build_options"]["scheme"] = scheme
    sp = tempfile.mkstemp(".json")[1]
    dp = tempfile.mkstemp(".json")[1]
    op = tempfile.mkstemp(".html")[1]
    with open(sp, "w") as f:
        json.dump(spec, f)
    with open(dp, "w") as f:
        json.dump(make_data_json(df), f)
    dr = DashRenderer(sp, dp, op)
    dr.render()
    for p in (sp, dp, op):
        try:
            os.unlink(p)
        except OSError:
            pass
    return next(iter(dr.figures.values()))


def _visible(grids):
    """True when at least one grid in the list will actually draw."""
    for g in grids:
        if getattr(g, "visible", True) and g.grid_line_color is not None:
            return True
    return False


class TestTheParserReadsTheRightKey:

    @pytest.mark.parametrize("scheme,expected", sorted(_MEASURED.items()))
    def test_the_vertical_axis_switch_comes_from_draw_major_vgrid(
        self, scheme, expected
    ):
        """It read the dead `draw_major_grid', so it was always False."""
        sp = SchemeParser(scheme)
        assert sp.draw_major_vgrid is expected[1], (
            f"{scheme} declares draw_major_vgrid "
            f"{sp._props.get('yesno draw_major_vgrid')!r}"
        )

    @pytest.mark.parametrize("scheme,expected", sorted(_MEASURED.items()))
    def test_the_horizontal_axis_switch_is_unchanged(self, scheme, expected):
        sp = SchemeParser(scheme)
        assert sp.draw_major_hgrid is expected[0]

    def test_the_two_switches_are_not_the_same_key(self):
        """s2color declares no / yes; reading one key for both loses that."""
        sp = SchemeParser("s2color")
        assert sp.draw_major_hgrid != sp.draw_major_vgrid


class TestTheFigureDrawsWhatTheSchemeAsksFor:

    @pytest.mark.parametrize("scheme,expected", sorted(_MEASURED.items()))
    def test_the_horizontal_grid_lines(self, scheme, expected):
        """Bokeh's ygrid draws horizontal lines, from draw_major_vgrid."""
        fig = _figure(scheme)
        assert _visible(list(fig.ygrid)) is expected[1], (
            f"{scheme}: horizontal grid lines should be "
            f"{'drawn' if expected[1] else 'absent'}"
        )

    @pytest.mark.parametrize("scheme,expected", sorted(_MEASURED.items()))
    def test_the_vertical_grid_lines(self, scheme, expected):
        """Bokeh's xgrid draws vertical lines, from draw_major_hgrid."""
        fig = _figure(scheme)
        assert _visible(list(fig.xgrid)) is expected[0], (
            f"{scheme}: vertical grid lines should be "
            f"{'drawn' if expected[0] else 'absent'}"
        )

    def test_s1mono_draws_no_grid_at_all(self):
        """The clearest case: Stata draws neither, dash drew both."""
        fig = _figure("s1mono")
        assert not _visible(list(fig.xgrid))
        assert not _visible(list(fig.ygrid))

    def test_stcolor_draws_both(self):
        """And the clearest case the other way, so the fix is not
        `hide everything'."""
        fig = _figure("stcolor")
        assert _visible(list(fig.xgrid))
        assert _visible(list(fig.ygrid))

    def test_a_drawn_grid_still_uses_the_schemes_colour(self):
        fig = _figure("s2color")
        sp = SchemeParser("s2color")
        assert any(str(g.grid_line_color) == sp.grid_color
                   for g in fig.ygrid)
