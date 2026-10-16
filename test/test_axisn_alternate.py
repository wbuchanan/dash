"""alternate on a label option of axes 2 to 9 (WP-31 section 35, GAPS3
D6b).

twoway's truth is test/fixtures/axisn_alt_truth.json
(scripts/extract_axisn_alt_truth.do): on axis 2 and axis 3, as on axis 1,
the labels alternate between two rows (columns, on a y axis), the lowest
label on the row nearest the plot, and altgap() widens the gap between
them.  dash draws axis 1's alternate as a twin axis (``_dash_alt_axes``,
WP-31 D6); the second axes now take the same twin, in both modes.
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
import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_FIX = os.path.join(_HERE, "fixtures", "axisn_alt_truth.json")
with open(_FIX, encoding="utf-8") as _fh:
    _T = json.load(_fh)

MODES = ("saved", "served")
_TWO = [plot_for("scatter"), plot_for("scatter", {"yaxis": "2"},
                                      yvar="price")]
_THREE = _TWO + [plot_for("line", {"yaxis": "3"}, yvar="foreign")]
_X2 = [plot_for("scatter"), plot_for("scatter", {"xaxis": "2"},
                                     xvar="price")]


def _build(mode, plots, go):
    """(figure, notes) of *plots* with graph options *go* in *mode*."""
    from bokeh.models import GlyphRenderer, Plot
    spec = tp._spec(plots, None, go)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        if mode == "saved":
            r, _w = tp._standalone(spec)
            models = list(r._last_layout_root.references())
            notes = _w
        else:
            doc, notes = tp._served(spec)
            models = [m for root in doc.roots for m in root.references()]
    notes = list(notes) + [str(w.message) for w in caught]
    figs = [m for m in models if isinstance(m, Plot)
            and any(isinstance(x, GlyphRenderer) for x in m.renderers)]
    assert len(figs) == 1
    return figs[0], notes


def _on(fig, side, name):
    """(axis, twin or None) of range *name* on *side*: the twin is the
    ``dash_alt_axis`` directly outside it."""
    from bokeh.models.axes import ContinuousAxis
    on = [a for a in getattr(fig, side) if isinstance(a, ContinuousAxis)]
    kw = "y_range_name" if side in ("left", "right") else "x_range_name"
    for i, a in enumerate(on):
        if getattr(a, kw) == name and \
                "dash_alt_axis" not in (a.tags or ()):
            nxt = on[i + 1] if i + 1 < len(on) else None
            tw = nxt if nxt is not None and "dash_alt_axis" in (
                nxt.tags or ()) and getattr(nxt, kw) == name else None
            return a, tw
    return None, None


def _near_is_lowest(rec, side):
    """twoway: the row nearest the plot holds the lowest label."""
    cols = [c for c in rec["columns"][side]
            if all(t.replace(",", "").isdigit() for t in c[1])]
    near, far = cols[0][1], cols[1][1]
    lo = min(float(t.replace(",", "")) for t in near + far)
    return lo in [float(t.replace(",", "")) for t in near]


class TestTheFixture:
    def test_meta(self):
        assert _T["_meta"]["source"] == "scripts/extract_axisn_alt_truth.do"
        assert sorted(_T["_meta"]) == ["born_date", "dash_commit",
                                       "extracted", "source",
                                       "stata_version"]

    def test_twoway_alternates_axes_two_and_three(self):
        assert _near_is_lowest(_T["y"]["y2alt"], "right")
        assert _near_is_lowest(_T["x"]["x2alt"], "above")
        y3 = [c for c in _T["y"]["y3alt"]["columns"]["left"]
              if c[1] and c[1][0] in ("220", "240")]
        assert [c[1] for c in y3] == [["220", "180", "140"],
                                      ["240", "200", "160"]]


@pytest.mark.parametrize("mode", MODES)
class TestTheSecondAxesAlternate:
    def _check(self, fig, notes, side, name):
        ax, tw = _on(fig, side, name)
        assert ax is not None
        assert tw is not None, f"no twin outside {name} on {side}"
        assert ax.formatter.args["parity"] == 0
        assert tw.formatter.args["parity"] == 1
        assert tw.ticker is ax.ticker
        assert not [m for m in notes if "alternate" in m], notes

    def test_y2(self, mode):
        fig, notes = _build(mode, _TWO, {"ylabel2": ", alternate"})
        self._check(fig, notes, "right", "y2")

    def test_y3(self, mode):
        fig, notes = _build(mode, _THREE,
                            {"axisn": {"y3": {"label": ", alternate"}}})
        self._check(fig, notes, "left", "y3")

    def test_x2(self, mode):
        fig, notes = _build(mode, _X2, {"xlabel2": ", alternate"})
        self._check(fig, notes, "above", "x2")

    def test_altgap_as_axis_one(self, mode):
        f1, _n = _build(mode, _TWO, {"ylabel": ", alternate altgap(large)"})
        f2, notes = _build(mode, _TWO,
                           {"ylabel2": ", alternate altgap(large)"})
        _a1, t1 = _on(f1, "left", "default")
        _a2, t2 = _on(f2, "right", "y2")
        assert t2.major_label_standoff == t1.major_label_standoff
        assert not [m for m in notes if "altgap" in m], notes

    def test_axis_one_is_left_alone(self, mode):
        fig, _n = _build(mode, _TWO, {"ylabel2": ", alternate"})
        _a, tw = _on(fig, "left", "default")
        assert tw is None
