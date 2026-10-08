"""Two filter-widget defects, one in each mode.

**`filter(label())` never reached the served widget.** The standalone
renderer resolves a widget title in three steps — the explicit ``label()``,
then the Stata *variable label*, then the bare variable name. The generated
server app read only the last two, so

    filter(rep78, type(range) label("Repair record"))

showed up in a served dashboard titled ``rep78``, the label silently
discarded, while the same command in standalone HTML titled it correctly.

**An integer slider stepped in fractions, in both modes.** ``step`` was
``(vmax - vmin) / 100``. On ``rep78``, which takes the values 1 to 5, that is
**0.04**: the handle stopped at 1.04, 1.08, 1.12 … and there was no position
for ``2``. Every integer variable — a count, a code, a year — had the same
problem.
"""
import importlib.util
import itertools
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import RangeSlider, Select, Slider

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
from conftest import make_data_json

_SEQ = itertools.count()
_DF = pd.DataFrame({
    "mpg": [22.0, 18.0, 25.0, 30.0, 21.0, 19.0, 27.0, 16.0],
    "weight": [2930.0, 3350.0, 2200.0, 1800.0, 3000.0, 3100.0, 2050.0, 3800.0],
    "rep78": [3.0, 1.0, 5.0, 2.0, 4.0, 3.0, 5.0, 1.0],
    # Genuinely fractional: mpg and weight above happen to be whole numbers,
    # so they are integer columns as far as the step rule is concerned.
    "ratio": [0.31, 0.47, 0.22, 0.65, 0.58, 0.19, 0.73, 0.41],
})


from conftest import render_models  # noqa: E402


def _spec(filter_raw):
    return {"graphs": [{"name": "g1", "graph_options": {"name": "g1"},
                        "options": {},
                        "plots": [{"type": "scatter", "yvar": "mpg",
                                   "xvar": "weight", "options": {}}]}],
            "kpis": [],
            "build_options": {"layout": "auto", "link": "",
                              "filter": filter_raw, "theme": "", "scheme": "",
                              "session_scheme": "", "title": "",
                              "subtitle": "", "registry": "g1", "tabs": "",
                              "filter_position": "top", "level": "95",
                              "formats": {}}}


def _widgets(tmp_path, filter_raw, server):
    tag = next(_SEQ)
    sp = tmp_path / f"s_{tag}.json"
    dp = tmp_path / f"d_{tag}.json"
    sp.write_text(json.dumps(_spec(filter_raw)))
    dp.write_text(json.dumps(make_data_json(_DF)))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if not server:
            r = dr.DashRenderer(str(sp), str(dp))
            render_models(r)
            found, seen = [], set()

            def walk(m):
                if isinstance(m, (list, tuple)):
                    for x in m:
                        if x is not None and not isinstance(x, (int, float, str)):
                            walk(x)
                    return
                if m is None or id(m) in seen:
                    return
                seen.add(id(m))
                if isinstance(m, (Slider, RangeSlider, Select)):
                    found.append(m)
                for attr in ("children", "tabs", "child"):
                    k = getattr(m, attr, None)
                    if k is not None:
                        walk(k)

            for w in getattr(r, "filter_widgets", []) or []:
                walk(w)
            if not found:
                for fig in r.figures.values():
                    walk(fig)
            return found

        ap = tmp_path / f"a_{tag}.py"
        dr.ServerAppBuilder(str(sp), str(dp)).build(str(ap))
        ms = importlib.util.spec_from_file_location(f"_fw_{tag}", str(ap))
        mod = importlib.util.module_from_spec(ms)
        ms.loader.exec_module(mod)
        doc = Document()
        mod.make_document(doc)
        return [m for m in doc.select({"type": object})
                if isinstance(m, (Slider, RangeSlider, Select))]


class TestTheLabelReachesTheServedWidget:
    def test_range_label(self, tmp_path):
        ws = _widgets(tmp_path,
                      'rep78, type(range) label("Repair record")', server=True)
        assert ws, "no filter widget in the served document"
        assert any("Repair record" in (w.title or "") for w in ws), (
            f"titles were {[w.title for w in ws]}"
        )

    def test_dropdown_label(self, tmp_path):
        ws = _widgets(tmp_path,
                      'rep78, type(dropdown) label("Repair record")',
                      server=True)
        assert any("Repair record" in (w.title or "") for w in ws)

    def test_slider_label(self, tmp_path):
        ws = _widgets(tmp_path,
                      'rep78, type(slider) label("Repair record")',
                      server=True)
        assert any("Repair record" in (w.title or "") for w in ws)

    def test_without_a_label_it_still_falls_back_to_the_name(self, tmp_path):
        ws = _widgets(tmp_path, "rep78, type(range)", server=True)
        assert any("rep78" in (w.title or "") for w in ws)


class TestAnIntegerSliderStepsByOne:
    @pytest.mark.parametrize("ftype", ["range", "slider"])
    def test_server(self, tmp_path, ftype):
        ws = _widgets(tmp_path, f"rep78, type({ftype})", server=True)
        steps = [w.step for w in ws if hasattr(w, "step")]
        assert steps and all(st == 1 for st in steps), (
            f"integer slider steps were {steps}"
        )

    @pytest.mark.parametrize("ftype", ["range", "slider"])
    def test_standalone(self, tmp_path, ftype):
        ws = _widgets(tmp_path, f"rep78, type({ftype})", server=False)
        steps = [w.step for w in ws if hasattr(w, "step")]
        assert steps and all(st == 1 for st in steps), (
            f"integer slider steps were {steps}"
        )

    @pytest.mark.parametrize("server", [True, False])
    def test_a_continuous_variable_still_steps_finely(self, tmp_path, server):
        ws = _widgets(tmp_path, "ratio, type(range)", server=server)
        steps = [w.step for w in ws if hasattr(w, "step")]
        assert steps and all(0 < st < 1 for st in steps), (
            f"a continuous variable should not step by 1; got {steps}"
        )
