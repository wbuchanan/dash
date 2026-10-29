"""
test_contour_key_degenerate.py -- a contour over too few points for a
surface draws its colour key, as twoway does (WP-37 section 37-02, DG-8).

The defect (measured at 72aafe2): ``dash contour price mpg weight in 1/2``
drew no key -- map_contour drew it only for a drawable surface, and two
points are degenerate -- where twoway draws an empty plot and a four-band
key labelled 4,000 to 4,800, titled Price (graph export SVG, 29oct2026:
labels 4,000 4,200 4,400 4,600 4,800, title Price; three points on one
line, ``contour price lin weight in 1/5`` with lin = 2*weight, key
4,000 ... 8,000; a constant z, ``contour c mpg weight in 1/10`` with c = 5,
key 4 and 6, title c).  test_wp37_truth.cscript Q3702-2 measures it live.
"""
import json
import os
import sys
import warnings

import pandas as pd
import pytest
from bokeh.document import Document

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from conftest import load_app, make_data_json, render_models  # noqa: E402

_MODES = ("saved", "served")
_N = [0]

#: auto's first five cars (sysuse auto): price, mpg, weight; lin is
#: 2 * weight (five points on one line), c a constant z.
_AUTO5 = pd.DataFrame({
    "price": [4099.0, 4749.0, 3799.0, 4816.0, 7827.0],
    "mpg": [22.0, 17.0, 22.0, 20.0, 15.0],
    "weight": [2930.0, 3350.0, 2640.0, 3250.0, 4080.0],
})
_AUTO5["lin"] = 2 * _AUTO5["weight"]
_AUTO5["c"] = 5.0
_LABELS = {"price": "Price", "mpg": "Mileage (mpg)",
           "weight": "Weight (lbs.)"}


def _figs(mode, tmp_path, ptype, z, y, x, rows):
    """The figures of ``<ptype> z y x in 1/<rows>`` over _AUTO5, with
    auto's variable labels, in *mode*."""
    spec = tp._spec([{"type": ptype, "zvar": z, "yvar": y, "xvar": x,
                      "options": {}}], {"formats": {}})
    sp = os.path.join(str(tmp_path), "spec.json")
    dp = os.path.join(str(tmp_path), "data.json")
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    with open(dp, "w", encoding="utf-8") as fh:
        json.dump(make_data_json(_AUTO5.iloc[:rows],
                                 variable_labels=_LABELS), fh)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if mode == "saved":
            r = dr.DashRenderer(sp, dp, os.path.join(str(tmp_path), "o.html"))
            render_models(r)
            return list(r.figures.values())
        _N[0] += 1
        ap = os.path.join(str(tmp_path), "app_%d.py" % _N[0])
        dr.ServerAppBuilder(sp, dp).build(ap)
        mod = load_app(ap, "_ckd_app_%d" % _N[0])
        doc = Document()
        mod.make_document(doc)
    return [m for m in tp._walk_models(doc) if type(m).__name__ == "figure"]


def _bars(fig):
    return [m for side in (fig.right, fig.left, fig.above, fig.below,
                           fig.center)
            for m in side if type(m).__name__ == "ContourColorBar"]


@pytest.mark.parametrize("mode", _MODES)
class TestTheKey:

    def test_two_points_draw_a_key(self, mode, tmp_path):
        """contour price mpg weight in 1/2: one key, titled Price, ticked
        4,000 to 4,800 by 200, as twoway labels it."""
        [fig] = _figs(mode, tmp_path, "contour", "price", "mpg", "weight", 2)
        [cb] = _bars(fig)
        assert cb.title == "Price"
        assert [float(t) for t in cb.ticker.ticks] == [
            4000.0, 4200.0, 4400.0, 4600.0, 4800.0]

    def test_points_on_one_line_draw_a_key(self, mode, tmp_path):
        """contour price lin weight in 1/5 (lin = 2*weight): one key ticked
        4,000 to 8,000 by 1,000, as twoway labels it."""
        [fig] = _figs(mode, tmp_path, "contour", "price", "lin", "weight", 5)
        [cb] = _bars(fig)
        assert cb.title == "Price"
        assert [float(t) for t in cb.ticker.ticks] == [
            4000.0, 5000.0, 6000.0, 7000.0, 8000.0]

    def test_contourline_draws_no_key(self, mode, tmp_path):
        """contourline keys its levels in the legend, not by a bar."""
        [fig] = _figs(mode, tmp_path, "contourline", "price", "mpg",
                      "weight", 2)
        assert not _bars(fig)

    def test_constant_z_unchanged(self, mode, tmp_path):
        """A constant z (c = 5 over ten points; here five) keeps the key
        it drew: twoway labels it 4 and 6, titled c."""
        [fig] = _figs(mode, tmp_path, "contour", "c", "mpg", "weight", 5)
        [cb] = _bars(fig)
        assert cb.title == "c"
        assert [float(t) for t in cb.ticker.ticks] == [4.0, 6.0]
