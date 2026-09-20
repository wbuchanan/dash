"""`lfit` and `lfitci` drew their lines at different x values.

S07 replaced the fitted-line grid with Stata's own rule -- `_fit_grid', which
is `n()' points, defaulting to 100, spanning the OBSERVED range, per
`ado/base/_/_gs_x_create.ado'. It was wired into `map_lfitci' and
`map_qfitci' and not into `map_lfit' or `map_qfit', which kept a 200-point
linspace over a range padded 10% at each end.

Measured on x spanning [1800, 4080]:

    lfit      200 pts  x in [1572.0, 4308.0]
    qfit      200 pts  x in [1572.0, 4308.0]
    lfitci    100 pts  x in [1800.0, 4080.0]
    qfitci    100 pts  x in [1800.0, 4080.0]

So `dash (scatter mpg weight) (lfit mpg weight) (lfitci mpg weight)' drew two
lines of the same fit that started and ended in different places, and the
lfit one ran 10% past the data at both ends -- which Stata does not do, and
which puts a fitted value on screen at an x no observation reaches.

The generated server app has always used 100 points over the observed range,
so the two modes disagreed as well. `test_mode_parity.py` could not see it:
it compares glyph PROPERTIES -- colour, width, dash -- not the data the glyph
is drawn from.

`n()` is Stata's option for the point count and neither `map_lfit` nor the
served copy read it.
"""
import importlib.util
import itertools
import json
import os
import sys
import warnings

import numpy as np
import pytest
from bokeh.document import Document
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
from conftest import make_data_json

_SEQ = itertools.count()

_LO, _HI, _N = 1800.0, 4080.0, 30
_W = np.linspace(_LO, _HI, _N)
_M = 40.0 - 0.0055 * _W + np.sin(np.linspace(0, 6, _N))


@pytest.fixture
def src():
    return ColumnDataSource({"mpg": _M.tolist(), "weight": _W.tolist()})


def _grid(gm, name, src, options=None):
    r = getattr(gm, "map_" + name)(figure(), src, "mpg", "weight",
                                   options or {})
    rs = r if isinstance(r, list) else [r]
    d = rs[0].data_source.data
    key = "x" if "x" in d else next(c for c in d if c.startswith("x"))
    return np.asarray(d[key], dtype=float)


@pytest.fixture
def gm():
    return dr.GlyphMapper()


class TestAFitSpansTheObservedRange:
    @pytest.mark.parametrize("name", ["lfit", "qfit", "lfitci", "qfitci"])
    def test_the_grid_starts_and_ends_at_the_data(self, gm, src, name):
        x = _grid(gm, name, src)
        assert x.min() == pytest.approx(_LO), (
            f"{name} starts at {x.min()}, before the smallest observation "
            f"({_LO}); Stata's fitted line spans the observed range"
        )
        assert x.max() == pytest.approx(_HI), (
            f"{name} ends at {x.max()}, past the largest observation ({_HI})"
        )

    @pytest.mark.parametrize("name", ["lfit", "qfit", "lfitci", "qfitci"])
    def test_the_grid_has_statas_default_point_count(self, gm, src, name):
        assert len(_grid(gm, name, src)) == dr._FIT_GRID

    def test_lfit_and_lfitci_agree_on_the_same_data(self, gm, src):
        np.testing.assert_allclose(_grid(gm, "lfit", src),
                                   _grid(gm, "lfitci", src),
                                   err_msg="lfit and lfitci draw the same fit "
                                           "at different x values")

    def test_qfit_and_qfitci_agree_on_the_same_data(self, gm, src):
        np.testing.assert_allclose(_grid(gm, "qfit", src),
                                   _grid(gm, "qfitci", src))


class TestTheGridPointCountIsAnOption:
    @pytest.mark.parametrize("name", ["lfit", "qfit", "lfitci", "qfitci"])
    def test_n_sets_the_point_count(self, gm, src, name):
        assert len(_grid(gm, name, src, {"n": "25"})) == 25

    def test_a_bad_n_is_reported_and_the_default_used(self, gm, src):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            x = _grid(gm, "lfit", src, {"n": "not a number"})
        assert len(x) == dr._FIT_GRID
        assert any("n" in str(w.message) for w in caught)


class TestTheServedFitUsesTheSameGrid:
    @staticmethod
    def _served(tmp_path, ptype, options=None):
        tag = next(_SEQ)
        sp = tmp_path / f"s_{tag}.json"
        dp = tmp_path / f"d_{tag}.json"
        sp.write_text(json.dumps({
            "graphs": [{"name": "g1", "graph_options": {"name": "g1"},
                        "options": {},
                        "plots": [{"type": ptype, "yvar": "mpg",
                                   "xvar": "weight",
                                   "options": options or {}}]}],
            "kpis": [],
            "build_options": {"layout": "auto", "registry": "g1",
                              "level": "95", "formats": {}, "theme": "",
                              "scheme": "", "session_scheme": ""}}))
        import pandas as pd
        dp.write_text(json.dumps(make_data_json(
            pd.DataFrame({"mpg": _M, "weight": _W}))))
        ap = tmp_path / f"a_{tag}.py"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(str(sp), str(dp)).build(str(ap))
        ms = importlib.util.spec_from_file_location(f"_fg_{tag}", str(ap))
        mod = importlib.util.module_from_spec(ms)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ms.loader.exec_module(mod)
            doc = Document()
            mod.make_document(doc)
        for m in doc.select({"type": ColumnDataSource}):
            if "x" in m.data and len(m.data["x"]) > 2:
                return np.asarray(m.data["x"], dtype=float)
        raise AssertionError(f"no fitted-line source found for {ptype}")

    @pytest.mark.parametrize("ptype", ["lfit", "qfit"])
    def test_the_two_modes_draw_at_the_same_x(self, gm, src, tmp_path, ptype):
        np.testing.assert_allclose(
            self._served(tmp_path, ptype), _grid(gm, ptype, src),
            err_msg=f"served {ptype} is drawn at different x values from the "
                    f"saved one")

    @pytest.mark.parametrize("ptype", ["lfit", "qfit"])
    def test_n_reaches_the_served_fit(self, gm, src, tmp_path, ptype):
        assert len(self._served(tmp_path, ptype, {"n": "25"})) == 25, (
            f"n() does not reach the served {ptype}"
        )
