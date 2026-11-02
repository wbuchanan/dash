"""
test_colorvar_key.py -- dash draws the colour key twoway draws (WP-42
section 42-03).

CV-8a (D68): under by() a contour's colour key is a by() colour key.
twoway draws no key under ``by(date)`` and one key beside the panels
under ``by(date, clegend(on))`` (sysuse surface, ``contour temperature
latitude longitude, levels(10)``; graph export SVG, 02nov2026: by(date)
has no key text right of the panels; by(date, clegend(on)) one key at the
right ticked 4.81 to 17.69, titled "Sea surface temperature (Deg. C)";
by(date, clegend(on pos(6))) the same key below the panels).  dash kept
every panel's ContourColorBar: ``_dash_by_keys`` collected only
``ColorBar``, of which ``ContourColorBar`` is not a subclass.
test_wp42_truth.cscript block S03 CV-8a measures it live.
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import test_by_axes_keys as tbk  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from conftest import make_data_json  # noqa: E402

_MODES = ("saved", "served")


def _surface():
    """A two-date surface: z = x + y on a 6 x 6 grid, each date its own
    offset (sysuse surface's shape, small)."""
    xs, ys = np.meshgrid(np.arange(6.0), np.arange(6.0))
    rows = []
    for d, off in ((1.0, 0.0), (2.0, 3.0)):
        for x, y in zip(xs.ravel(), ys.ravel()):
            rows.append({"date": d, "lon": x, "lat": y, "temp": x + y + off})
    return pd.DataFrame(rows)


def _contour_bars(model):
    sides = ("left", "right", "above", "below", "center")
    return [m for s in sides for m in getattr(model, s)
            if type(m).__name__ in ("ColorBar", "ContourColorBar")
            and getattr(m, "name", None) != "dash_by_label_box"]


def _by_build(mode, by):
    spec = tp._spec([{"type": "contour", "zvar": "temp", "yvar": "lat",
                      "xvar": "lon", "options": {"levels": "10"}}],
                    None, {"by": by, "name": "g1"})
    data = make_data_json(_surface(),
                          variable_labels={"temp": "Temperature"})
    roots, _notes, _owner = tbk._build(mode, spec, data)
    (grid,) = tbk._grids(roots).values()
    return grid


@pytest.mark.parametrize("mode", _MODES)
class TestTheByContourKey:
    """CV-8a: a by() contour draws twoway's one key."""

    def test_no_key_under_by(self, mode):
        """by(date): no panel keeps a key and no key cell is drawn."""
        grid = _by_build(mode, "date")
        for f in tbk._panels(grid):
            assert not _contour_bars(f)
        assert tbk._cell(grid, "dash_by_clegend") is None

    def test_one_key_under_clegend_on(self, mode):
        """by(date, clegend(on)): one key at the right of the panels,
        none on a panel, titled with z's label."""
        grid = _by_build(mode, "date, clegend(on)")
        for f in tbk._panels(grid):
            assert not _contour_bars(f)
        cell = tbk._cell(grid, "dash_by_clegend")
        assert cell is not None
        assert tbk._cell_side(grid, cell) == "right"
        (bar,) = _contour_bars(cell[0])
        assert bar.title == "Temperature"

    def test_one_key_below_under_pos6(self, mode):
        """by(date, clegend(on pos(6))): the one key below the panels."""
        grid = _by_build(mode, "date, clegend(on pos(6))")
        for f in tbk._panels(grid):
            assert not _contour_bars(f)
        cell = tbk._cell(grid, "dash_by_clegend")
        assert cell is not None
        assert tbk._cell_side(grid, cell) == "below"
        assert len(_contour_bars(cell[0])) == 1


# ---------------------------------------------------------------------------
# twoway's axis-style colour key, as measured (test/fixtures/
# colorvar_key_truth.json, scripts/extract_colorvar_key_truth.do): what the
# key cell of CV-3 is drawn to.
# ---------------------------------------------------------------------------

import json  # noqa: E402

_KEY_FIXTURE = os.path.join(_HERE, "fixtures", "colorvar_key_truth.json")

#: The swatch each plot type keys its levels with (S_<type>): a marker
#: (circle), a rect, a line, a marker on a line, or no key at all.
_SWATCH_KIND = {
    "scatter": "marker", "connected": "marker+line", "line": "line",
    "area": "none", "bar": "rect", "spike": "rect", "dropline": "marker",
    "dot": "marker", "rarea": "none", "rbar": "rect", "rspike": "rect",
    "rcap": "marker", "rcapsym": "marker", "rscatter": "marker",
    "rline": "line", "rconnected": "marker+line", "pcspike": "rect",
    "pccapsym": "marker", "pcarrow": "rect", "pcbarrow": "rect",
    "pcscatter": "marker",
}


def _key_truth():
    with open(_KEY_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _key_texts(rec):
    """twoway's unrotated key texts right of the plot region, top first."""
    r = rec["plot"]["right"]
    return [t["text"] for t in sorted(rec["texts"], key=lambda t: t["y"])
            if t["x"] > r + 1 and not t["rotate"]]


def _swatch_kind(rec):
    k = rec["key"]
    filled = [c for c in k.get("circles", []) if c.get("fill") != "none"]
    lines = [h for h in k.get("hlines", []) if h.get("stroke") != "#000000"]
    if filled and lines:
        return "marker+line"
    if filled:
        return "marker"
    if k.get("rects"):
        return "rect"
    return "line" if lines else "none"


class TestTwowaysKey:
    """The measured key: highest level at the top, labelled at the z axis'
    ticks, no missing entry, the title up the right of the labels."""

    def test_discrete_key_is_an_axis(self):
        t = _key_truth()
        assert _key_texts(t["K1"]) == ["5", "4", "3", "2", "1"]
        assert _key_texts(t["K2"]) == ["1", ".8", ".6", ".4", ".2", "0"]
        assert _key_texts(t["K7"])[0] == "Foreign"
        assert _key_texts(t["K3"]) == ["3.66667", "2.33333"]
        assert _key_texts(t["K4"]) == ["4", "2"]
        assert _key_texts(t["K_cont"]) == ["15,000", "10,000", "5,000", "0"]
        for pid in ("K1", "K8", "E_allmiss"):
            assert not any("missing" in x["text"] or x["text"] == "rest"
                           for x in t[pid]["texts"])
        (title,) = [x for x in t["K1"]["texts"] if x["rotate"]
                    and x["x"] > t["K1"]["plot"]["right"]]
        assert title["rotate"] == -90.0
        assert title["text"] == "Repair record 1978"

    def test_swatch_kind(self):
        t = _key_truth()
        got = {p[2:]: _swatch_kind(r) for p, r in t.items()
               if p.startswith("S_")}
        assert got == _SWATCH_KIND
