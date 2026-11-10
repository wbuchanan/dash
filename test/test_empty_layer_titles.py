"""
test_empty_layer_titles.py -- the titles and keys of emptied layers (WP-47
DG-7).

The defect (measured at b6ae36c): ``lfit mpg weight if price<0`` was titled
and keyed "Fitted values", ``histogram mpg if price<0`` titled "Mileage
(mpg)" on x, in both modes.

twoway (StataNow 19.5, scripts/extract_varlabel_mlabel_truth.do, fixture
test/fixtures/varlabel_mlabel_truth.json ``empty.*``): an lfit or qfit
whose sample is empty draws nothing, notes "(note:  regress could not fit
model)" and is titled and keyed by its y variable's name ("mpg": the
variable twoway makes for the fit is left unlabelled), its x by the x
variable's label; lfitci and qfitci key "95% CI", then "mpg"; a
yvarlabel() still names the fit ("Q"); an emptied histogram is titled by
its scale word over "x" (swapped under horizontal; an xvarlabel() still
names x); kdensity, lowess and scatter keep their texts; ``lfit y x`` on
no observations is titled y over x.  fpfit is refused, r(198) "observation
numbers out of range", by twoway and by dash.ado alike.

Emptiness is judged on the build rows (qualifiers applied, no filter
widget), the same in both modes (D-47-02.f): test_mode_parity's MOVE_CORPUS
case "a move that empties lfit keeps its title" holds that a filter move
changes no title.
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.dirname(_HERE))

import dash_render as dr  # noqa: E402
from test_varlabel_options import (DF, MODES, T, VL, axis_titles,  # noqa: E402
                                   figs)

E = T["empty"]
_Q = "__dashq1"
DFQ = DF.assign(**{_Q: [0.0] * len(DF)})
DFN = pd.DataFrame({"y": [np.nan] * 3, "x": [np.nan] * 3})


def _p(ptype, q=True, **opts):
    if ptype == "histogram":
        p = {"type": ptype, "var": "mpg", "options": opts}
    else:
        p = {"type": ptype, "yvar": "mpg", "xvar": "weight", "options": opts}
    if q:
        p["qual_col"] = _Q
    return p


_G = {"qual_col": _Q}
_ON = {"legend": "on"}
#: fixture case -> (plots, graph keys, graph options, frame).  A plot of
#: its own carries its if on the graph too, as dash.ado writes it.
CASES = {
    "lfit": ([_p("lfit")], _G, _ON, DFQ),
    "qfit": ([_p("qfit")], _G, _ON, DFQ),
    "lfitci": ([_p("lfitci")], _G, _ON, DFQ),
    "qfitci": ([_p("qfitci")], _G, _ON, DFQ),
    "lfit_vl": ([_p("lfit", yvarlabel='"Q"')], _G, _ON, DFQ),
    "lfit_aw": ([_p("lfit", weight="aweight", wexp="price")], _G, _ON, DFQ),
    "lfitci_nofit": ([_p("lfitci", nofit="nofit")], _G, _ON, DFQ),
    "lfit_beside": ([_p("scatter", q=False), _p("lfit")], None, _ON, DFQ),
    "lfit_first": ([_p("lfit"), _p("scatter", q=False)], None, _ON, DFQ),
    "lowess": ([_p("lowess")], _G, _ON, DFQ),
    "hist": ([_p("histogram")], _G, None, DFQ),
    "hist_freq": ([_p("histogram", frequency="frequency")], _G, None, DFQ),
    "hist_h": ([_p("histogram", horizontal="horizontal")], _G, None, DFQ),
    "hist_xvl": ([_p("histogram", xvarlabel='"M"')], _G, None, DFQ),
    "kdensity": ([{"type": "kdensity", "var": "mpg", "options": {},
                   "qual_col": _Q}], _G, None, DFQ),
    "scatter": ([_p("scatter")], _G, None, DFQ),
    "lfit_nodata": ([{"type": "lfit", "yvar": "y", "xvar": "x",
                      "options": {}}], None, _ON, DFN),
}


def _want(case):
    rec = E[case]
    return ("\n".join(rec["ytitle_lines"]), "\n".join(rec["xtitle_lines"]),
            rec["legend_labels"] if rec["legend_drawn"] else None)


def _drawn(mode, tmp_path, case):
    plots, extra, go, df = CASES[case]
    vl = {} if df is DFN else VL
    f, _ = figs(mode, tmp_path, plots, df=df, vl=vl, go=go, extra=extra)
    keys = [it.label.get("value") if isinstance(it.label, dict)
            else getattr(it.label, "value", it.label)
            for lg in f[0].legend if lg.visible for it in lg.items]
    return axis_titles(f[0]) + ((keys or None) if E[case]["legend_drawn"]
                                else None,)


class TestEmptiedLayers:

    def test_the_rows(self):
        # Every case twoway draws, and fpfit's refusal.
        for case in CASES:
            assert E[case]["rc"] == 0, case
        assert E["fpfit"]["rc"] == 198
        assert E["fpfit"]["error"] == "observation numbers out of range"

    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("case", sorted(CASES))
    def test_case(self, mode, case, tmp_path):
        got, want = _drawn(mode, tmp_path, case), _want(case)
        if case == "lfitci_nofit":
            # twoway titles a nofit ci fit's y "95% CI", with rows or
            # without; dash draws none either way -- BUGS.md "A nofit ci
            # fit draws no y title; twoway titles it by its band" (S3).
            # Its x title and its one key are DG-7's.
            got, want = got[1:], want[1:]
        assert got == want

    def test_the_series(self):
        # The texts of an emptied layer, read from the plot's mark.
        lf = dict(_p("lfit"), _dash_empty=True)
        assert dr._dash_layer_series(lf, VL) == [("mpg", "Weight (lbs.)")]
        ci = dict(_p("lfitci"), _dash_empty=True)
        assert dr._dash_layer_series(ci, VL) == [
            ("95% CI", "Weight (lbs.)"), ("mpg", "Weight (lbs.)")]
        h = dict(_p("histogram"), _dash_empty=True)
        assert dr._dash_layer_series(h, VL) == [("Density", "x")]
        assert dr._dash_legend_key(lf, VL) == "mpg"
        # Unmarked, the texts are the fit's own.
        assert dr._dash_layer_series(_p("lfit"), VL) == [
            ("Fitted values", "Weight (lbs.)")]

    def test_the_set(self):
        plots = [_p("scatter"), _p("lfit"), _p("qfitci"), _p("histogram"),
                 _p("lowess"), _p("lfit", q=False),
                 {"type": "kdensity", "var": "mpg", "options": {},
                  "qual_col": _Q}]
        masks = {_Q: pd.Series([False] * len(DF), index=DF.index)}
        got = dr._dash_empty_layers(plots, DF, masks)
        assert got == frozenset({1, 2, 3}) and isinstance(got, frozenset)
        # The graph's qualifier empties every layer it holds.
        assert dr._dash_empty_layers([_p("lfit", q=False)], DF, masks,
                                     {"qual_col": _Q}) == frozenset({0})
        # A hand-written qualifier, as text.
        assert dr._dash_empty_layers(
            [dict(_p("lfit", q=False), if_expr="price < 0")], DF) \
            == frozenset({0})
        assert dr._dash_empty_layers(
            [dict(_p("lfit", q=False), if_expr="price > 0")], DF) \
            == frozenset()
        # Missing y or x, or no weight above zero.
        df = DF.assign(mpg=[np.nan, np.nan, 1.0], z=[0.0, 0.0, 0.0])
        assert dr._dash_empty_layers(
            [{"type": "lfit", "yvar": "mpg", "xvar": "weight",
              "options": {"weight": "aweight", "wexp": "z"}},
             {"type": "lfit", "yvar": "mpg", "xvar": "weight",
              "options": {}}], df) == frozenset({0})

    def test_it_never_raises(self):
        # A missing column or mask counts as rows; anything else is no plot.
        assert dr._dash_empty_layers(
            [{"type": "lfit", "yvar": "nope", "xvar": "weight",
              "options": {}},
             dict(_p("lfit"), qual_col="__dashq9"), None, 3,
             {"type": "lfit", "options": 3}], DF, {}) == frozenset()
        assert dr._dash_empty_layers(None, None) == frozenset()
        assert dr._dash_empty_layers([_p("lfit")], "not a frame") \
            == frozenset()
