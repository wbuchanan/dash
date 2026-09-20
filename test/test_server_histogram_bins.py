"""The two modes disagreed about how many bars a histogram has.

The standalone renderer derives the bin count from the data with Stata's own
rule (``_stata_bin_count``: ``k = min(sqrt(n), 10*ln(n)/ln(10))``, truncated,
verified against Stata on auto/mpg and nlsw88/wage). The generated server app
used a literal::

    try: nbins = max(1, min(int(opts.get('bin', 20)), 1000))

So ``dash histogram mpg`` on auto drew **8** bars standalone and **20**
served, and 20 is not the answer Stata gives. Same command, two histograms,
neither mode saying so.

The bin count stays fixed once chosen, rather than being re-derived from the
filtered row count on every widget move: the server recomputes the bin
*edges* and heights live, which is the documented difference between the
modes, but a histogram whose number of bars changes as you drag a slider is
not reporting the same statistic twice.
"""
import importlib.util
import itertools
import json
import os
import sys

import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import ColumnDataSource

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
from conftest import make_data_json

_SEQ = itertools.count()

# auto/mpg: n = 74 -> Stata gives 8 bins.
_MPG = [22, 17, 22, 20, 15, 18, 26, 20, 16, 19, 14, 14, 21, 29, 16, 22, 17,
        13, 20, 16, 17, 19, 18, 18, 22, 15, 17, 24, 25, 14, 18, 12, 16, 21,
        14, 18, 12, 15, 24, 14, 21, 18, 28, 19, 19, 34, 18, 18, 17, 17, 17,
        14, 21, 23, 24, 25, 23, 35, 24, 21, 21, 25, 28, 30, 14, 26, 18, 41,
        31, 25, 25, 17, 18, 14]


def _hist_widths(tmp_path, options=None, data=None):
    tag = next(_SEQ)
    df = pd.DataFrame({"mpg": [float(v) for v in (data or _MPG)]})
    graphs = [{"name": "g1", "graph_options": {"name": "g1"},
               "plots": [{"type": "histogram", "yvar": "mpg", "xvar": "",
                          "options": options or {}}],
               "options": {}}]
    bo = {"layout": "auto", "link": "", "filter": "", "theme": "",
          "scheme": "", "session_scheme": "", "title": "", "subtitle": "",
          "registry": "g1", "tabs": "", "filter_position": "top",
          "level": "95", "formats": {}}
    spec = tmp_path / f"s_{tag}.json"
    dpath = tmp_path / f"d_{tag}.json"
    app = tmp_path / f"a_{tag}.py"
    spec.write_text(json.dumps({"graphs": graphs, "kpis": [],
                                "build_options": bo}))
    dpath.write_text(json.dumps(make_data_json(df)))
    dr.ServerAppBuilder(str(spec), str(dpath)).build(str(app))
    ms = importlib.util.spec_from_file_location(f"_hist_app_{tag}", str(app))
    mod = importlib.util.module_from_spec(ms)
    ms.loader.exec_module(mod)
    doc = Document()
    mod.make_document(doc)
    for m in doc.select({"type": ColumnDataSource}):
        if "left" in m.data and "right" in m.data:
            return len(m.data["left"])
    raise AssertionError("no histogram source in the served document")


class TestTheServerUsesStatasBinRule:
    def test_auto_mpg_gets_statas_eight_bins(self, tmp_path):
        assert _hist_widths(tmp_path) == dr._stata_bin_count(len(_MPG)) == 8

    def test_an_explicit_bin_option_still_wins(self, tmp_path):
        assert _hist_widths(tmp_path, {"bin": "12"}) == 12

    def test_a_different_n_gives_a_different_count(self, tmp_path):
        small = _hist_widths(tmp_path, data=_MPG[:10])
        assert small == dr._stata_bin_count(10)
        assert small != 8

    def test_the_two_modes_now_agree(self, tmp_path):
        """The point of the change: one command, one histogram."""
        import numpy as np
        arr = np.array([float(v) for v in _MPG])
        edges, _ = dr.GlyphMapper._histogram_grid(arr, {})
        assert _hist_widths(tmp_path) == len(edges) - 1

    def test_a_silly_bin_count_is_still_clamped(self, tmp_path):
        assert _hist_widths(tmp_path, {"bin": "99999999"}) == 1000
