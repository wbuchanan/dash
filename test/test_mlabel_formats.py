"""
test_mlabel_formats.py -- xvarformat() and yvarformat() format the marker
labels of the variable they format, as twoway writes them (WP-47 MS-5).

The defect (measured at 92ac512): scatter mpg weight in 1/5, mlabel(mpg)
yvarformat(%9.2f) labelled the markers 22, 17, ...; twoway
(test/fixtures/varlabel_mlabel_truth.json varformat.*, measured by
scripts/extract_varlabel_mlabel_truth.do) labels them 22.00, 17.00;
mlabel(weight) xvarformat(%9.1f) 2930.0; mlabel(price) yvarformat(%9.2f)
keeps price's own format (4,099); and mlabformat(%9.1f) wins over
yvarformat(%9.2f) (22.0).
"""
import os
import sys

import pandas as pd
import pytest
from bokeh.models import LabelSet

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.dirname(_HERE))

import dash_render as dr  # noqa: E402
from test_varlabel_options import MODES, T, VL, figs  # noqa: E402

# auto's first five rows, in their own display formats.
DF5 = pd.DataFrame({
    "mpg": [22.0, 17.0, 22.0, 20.0, 15.0],
    "weight": [2930.0, 3350.0, 2640.0, 3250.0, 4080.0],
    "price": [4099.0, 4749.0, 3799.0, 4816.0, 7827.0],
})
BO = {"formats": {"mpg": "%8.0g", "weight": "%8.0gc", "price": "%8.0gc"}}

CASES = {
    "y": {"mlabel": "mpg", "yvarformat": "%9.2f"},
    "x": {"mlabel": "weight", "xvarformat": "%9.1f"},
    "other": {"mlabel": "price", "yvarformat": "%9.2f"},
    "both": {"mlabel": "mpg", "yvarformat": "%9.2f", "mlabformat": "%9.1f"},
}


def _labels(fig):
    out = []
    for r in (list(fig.center) + list(fig.above) + list(fig.below)
              + list(fig.left) + list(fig.right) + list(fig.renderers)):
        if isinstance(r, LabelSet):
            fld = getattr(r.text, "field", None) or r.text
            out.extend(str(v) for v in r.source.data[fld])
    return out


class TestVarformatOnLabels:

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("case", sorted(CASES))
    def test_case(self, mode, case, tmp_path):
        rec = T["varformat"][case]
        want = [t["text"] for t in rec["texts"][:5]]
        plots = [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                  "options": CASES[case]}]
        f, _ = figs(mode, tmp_path, plots, df=DF5, vl=VL, bo=BO)
        assert _labels(f[0]) == want

    def test_the_format(self):
        # _dash_mlabel_varformat: mlabformat() first; else the layer's
        # y (x) format when the label variable is its y (x); only a
        # number format twoway writes with %f, %g or %e.
        f = dr._dash_mlabel_varformat
        assert f({"yvarformat": "%9.2f"}, "mpg", (("mpg",), "weight")) == \
            "%9.2f"
        assert f({"xvarformat": "%9.1fc"}, "weight",
                 (("mpg",), "weight")) == "%9.1fc"
        assert f({"yvarformat": "%9.2f", "mlabformat": "%9.1f"}, "mpg",
                 (("mpg",), "weight")) == "%9.1f"
        assert f({"yvarformat": "%9.2f"}, "price", (("mpg",), "weight")) == ""
        assert f({"yvarformat": "%td"}, "mpg", (("mpg",), "weight")) == ""
        assert f({"yvarformat": "%9.2f"}, "mpg", None) == ""
        assert f(None, "mpg", (("mpg",), "weight")) == ""

    def test_help(self):
        # AC-47-02.3: the help says the labels take the format.
        root = os.path.dirname(_HERE)
        with open(os.path.join(root, "dash.sthlp"), encoding="utf-8") as fh:
            hlp = " ".join(fh.read().split())
        assert ("and the marker labels of that variable, unless "
                "{cmd:mlabformat()} is given") in hlp
