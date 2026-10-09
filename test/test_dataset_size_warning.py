"""Nothing told the user their dashboard would be unopenable.

Neither renderer bounds or reports dataset size. Measured by the adversarial
pass: 2,000,000 rows x 2 columns rendered to 90.6 MB of HTML at 1.71 GB RSS,
with rc 0 and no warning; the served app embeds the same data base64
(35.7 MB of app.py for 500k rows), rebuilds the whole frame on every session,
and pushes 10 MB to each browser.

The user finds out when the file will not open. A Stata user has no way to
know in advance -- `dash scatter y x' looks the same on 74 observations and
on ten million.

So dash says so, once, at build time, with the number it measured and the
size it implies. It does not refuse: the user may well mean it, and Stata
does not refuse to draw a scatter of ten million points either.
"""
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
from conftest import make_data_json


def _render(tmp_path, n_rows, n_cols, tag):
    rng = np.random.default_rng(3)
    df = pd.DataFrame({f"v{i}": rng.normal(size=n_rows)
                       for i in range(n_cols)})
    # Every column beyond the scatter's own v0/v1 is a KPI's variable
    # (GAPS2 G3): a saved page's cells limit -- and this note -- now
    # counts only what is actually embedded, so a column nothing draws
    # from (no plot, no KPI, no filter) is no longer part of the count;
    # this fixture keeps every one of its n_cols columns embedded, as a
    # real dashboard's exported columns always are (dash.ado never
    # exports a variable nothing references).
    kpis = [{"name": f"k{i}", "stat": "mean", "var": f"v{i}", "fmt": "",
             "title": f"k{i}", "subtitle": "", "color": "", "bgcolor": "",
             "update": "filter", "if_expr": "", "in_expr": "",
             "qual_col": ""}
            for i in range(2, n_cols)]
    spec = {"graphs": [{"name": "g1", "graph_options": {"name": "g1"},
                        "options": {},
                        "plots": [{"type": "scatter", "yvar": "v0",
                                   "xvar": "v1", "options": {}}]}],
            "kpis": kpis,
            "build_options": {"layout": "auto",
                              "registry": "g1 " + " ".join(
                                  k["name"] for k in kpis),
                              "level": "95", "formats": {}, "theme": "",
                              "scheme": "", "session_scheme": ""}}
    sp = tmp_path / f"s_{tag}.json"
    dp = tmp_path / f"d_{tag}.json"
    sp.write_text(json.dumps(spec))
    dp.write_text(json.dumps(make_data_json(df)))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        dr.DashRenderer(str(sp), str(dp)).render()
    return [str(w.message) for w in caught]


class TestALargeDatasetIsReported:
    @pytest.mark.release  # a dataset over the size threshold (WP-30 D)
    def test_a_dataset_over_the_threshold_is_named(self, tmp_path):
        n_rows = int(dr._LARGE_DATASET_CELLS // 4) + 5000
        msgs = _render(tmp_path, n_rows, 4, "big")
        hits = [m for m in msgs if "observations" in m or "rows" in m]
        assert hits, (
            f"a {n_rows:,}-row dataset rendered without a word; the user "
            f"finds out when the file will not open"
        )
        assert any(str(n_rows) in m.replace(",", "") for m in hits), (
            f"the warning does not name the row count: {hits}"
        )

    @pytest.mark.release  # a dataset over the size threshold (WP-30 D)
    def test_the_warning_says_how_large_the_file_will_be(self, tmp_path):
        n_rows = int(dr._LARGE_DATASET_CELLS // 4) + 5000
        msgs = _render(tmp_path, n_rows, 4, "big2")
        assert any("MB" in m for m in msgs), (
            f"the warning gives no idea of the size: {msgs}"
        )

    def test_an_ordinary_dataset_is_not_reported(self, tmp_path):
        """The control: auto and nlsw88 must not trip it."""
        msgs = _render(tmp_path, 2246, 17, "nlsw88")
        assert not [m for m in msgs if "observations" in m], (
            f"a 2,246-row dataset the size of nlsw88 was reported as large: "
            f"{msgs}"
        )

    def test_the_threshold_is_a_documented_constant(self):
        """A documentation guard over dash_render.py's text, deliberately:
        the comment that says why the threshold is that number is not
        behaviour, and no run can show it."""
        import inspect
        src = inspect.getsource(dr)
        i = src.index("_LARGE_DATASET_CELLS")
        head = src[max(0, i - 600):i]
        assert "#" in head, (
            "_LARGE_DATASET_CELLS carries no comment saying why it is that "
            "number"
        )


class TestTheServedAppReportsItToo:
    @pytest.mark.release  # a dataset over the size threshold (WP-30 D)
    def test_the_builder_warns_on_the_same_data(self, tmp_path):
        rng = np.random.default_rng(3)
        n_rows = int(dr._LARGE_DATASET_CELLS // 4) + 5000
        df = pd.DataFrame({f"v{i}": rng.normal(size=n_rows)
                           for i in range(4)})
        sp = tmp_path / "ss.json"
        dp = tmp_path / "sd.json"
        sp.write_text(json.dumps({
            "graphs": [{"name": "g1", "graph_options": {"name": "g1"},
                        "options": {},
                        "plots": [{"type": "scatter", "yvar": "v0",
                                   "xvar": "v1", "options": {}}]}],
            "kpis": [],
            "build_options": {"layout": "auto", "registry": "g1",
                              "level": "95", "formats": {}, "theme": "",
                              "scheme": "", "session_scheme": ""}}))
        dp.write_text(json.dumps(make_data_json(df)))
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr.ServerAppBuilder(str(sp), str(dp)).build(str(tmp_path / "a.py"))
        msgs = [str(w.message) for w in caught]
        assert any("observations" in m for m in msgs), (
            f"`dash build, server' embeds the same data and says nothing: "
            f"{msgs}"
        )
