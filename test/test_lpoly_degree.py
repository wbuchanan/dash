"""lpoly and lpolyci degree(4) to degree(7) (WP-31 C10b).

GAPS3 C10: dash refused ``degree()`` above 3 ("dash fits local
polynomials up to degree 3", r(198)) where twoway draws it; the rule of
thumb's constants for degree 4-7 (``_LPOLY_ROT_CONSTANTS``, pe 5 and 7)
were unreachable.  Measured in test/fixtures/parsed_values_truth.json
(scripts/extract_parsed_values_truth.do): twoway accepts degree 4 to 8;
the lpoly command's r(bwidth) for each degree and kernel is recorded.

dash's default bandwidth agrees with r(bwidth) to 5e-4 at degree 4 and 5
(test_lpoly_rot.py's tier) and to 1e-2 at degree 6 and 7: Stata's rule
fits a polynomial of degree 9 or 10 in raw powers of x there, and its
float64 round-off on that ill-conditioned fit is not reproduced (auto:
0.96% on every kernel, the same ratio, so the constants are right and the
global fit is Stata's round-off).  The constants stop at pe = 7, so
degree(8) -- which twoway draws -- stays dash's own bound, said in the
refusal.
"""
import json
import os
import re
import sys

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_FIX = os.path.join(_HERE, "fixtures", "parsed_values_truth.json")
_ADO = os.path.join(_HERE, "..", "dash.ado")
_AUTO = os.path.join(_HERE, "fixtures", "data", "auto.csv")
_KERNELS = ("epanechnikov", "epan2", "biweight", "cosine", "gaussian",
            "parzen", "rectangle", "triangle")
#: Relative agreement with r(bwidth): test_lpoly_rot.py's degree 4/5 tier;
#: degree 6/7 the measured round-off of Stata's degree 9/10 global fit.
_TOL = {4: 5e-4, 5: 5e-4, 6: 1e-2, 7: 1e-2}


@pytest.fixture(scope="module")
def truth():
    with open(_FIX, encoding="utf-8") as fh:
        return json.load(fh)


def _auto():
    d = pd.read_csv(_AUTO)
    return d["weight"].to_numpy(float), d["mpg"].to_numpy(float)


def _plot_tokens():
    with open(_ADO, encoding="utf-8") as fh:
        src = fh.read()
    start = src.index("program define _dash_option_rules")
    body = src[start:src.index("\nend\n", start)]
    m = re.search(r"local plot ///\n(.*?)\n    //", body, re.S)
    return m.group(1).replace("///", " ").split()


def _validate_value_src():
    with open(_ADO, encoding="utf-8") as fh:
        src = fh.read()
    start = src.index("program define _dash_validate_value")
    return src[start:src.index("\nend\n", start)]


class TestTheFixture:
    def test_meta_is_stamped(self, truth):
        assert sorted(truth["_meta"]) == ["born_date", "dash_commit",
                                          "extracted", "source",
                                          "stata_version"]
        for d in ("4", "5", "6", "7", "8"):
            r = truth["degree"][d]
            assert r["twoway_rc"] == 0
            assert np.isfinite(r["r_bwidth"]) and r["r_degree"] == int(d)


class TestDegree:
    @pytest.mark.parametrize("d", (4, 5, 6, 7))
    def test_four_to_seven(self, d, truth):
        x, y = _auto()
        h = dr.GlyphMapper._default_lpoly_bwidth(x, y, None, d,
                                                 "epanechnikov")
        want = truth["degree"][str(d)]["r_bwidth"]
        assert abs(h / want - 1) <= _TOL[d], (d, h, want)

    @pytest.mark.parametrize("k", _KERNELS)
    def test_kernels(self, k, truth):
        x, y = _auto()
        for d in (4, 6):
            h = dr.GlyphMapper._default_lpoly_bwidth(x, y, None, d, k)
            want = truth["degree"][str(d)]["kernels"][k]["r_bwidth"]
            assert abs(h / want - 1) <= _TOL[d], (d, k, h, want)


def _curve(mode, opts, ptype="lpoly"):
    from bokeh.models import GlyphRenderer, Line
    spec = tp._spec([plot_for(ptype, opts)])
    if mode == "saved":
        r, _w = tp._standalone(spec)
        models = list(r._last_layout_root.references())
    else:
        doc, _w = tp._served(spec)
        models = [m for root in doc.roots for m in root.references()]
    out = []
    for m in models:
        if isinstance(m, GlyphRenderer) and isinstance(m.glyph, Line):
            data = m.data_source.data
            out.append([float(v) for v in data[m.glyph.y]])
    return out


class TestBothModes:
    @pytest.mark.parametrize("mode", ("saved", "served"))
    def test_degree_five(self, mode):
        # bwidth() given: the parity frame's ten rows are too few for the
        # rule of thumb's global fit of degree 8.
        opts = {"degree": "5", "bwidth": "800"}
        got = _curve(mode, opts)
        assert len(got) == 1 and len(got[0]) > 1
        assert np.isfinite(got[0]).all()
        assert got == _curve("saved" if mode == "served" else "served", opts)


    @pytest.mark.parametrize("mode", ("saved", "served"))
    def test_lpolyci_degree_five_is_lpolys(self, mode):
        """map_lpolyci read degree() within 0-3 after C10b accepted 4-7,
        so lpolyci degree(5) was drawn at degree 0 with a warning (found
        by WP-31 section 19); its line is lpoly's at the same degree."""
        opts = {"degree": "5", "bwidth": "800"}
        ci = _curve(mode, opts, "lpolyci")
        assert ci and ci[0] == _curve(mode, opts)[0]
        assert ci[0] != _curve(mode, {"degree": "0", "bwidth": "800"})[0]


class TestTheRule:
    def test_degree_token_is_0_7(self):
        # Flipped (WP-31 D35): the token was degree=int,0,7 with dash's
        # "up to degree 7" sentence, wrong because twoway draws every
        # nonnegative degree (measured: degree(8) to degree(1000)); dash
        # draws it with a note (test_lpoly_edges.py::TestLpolyHighDegree).
        toks = _plot_tokens()
        assert "degree=int,0" in toks
        assert not [t for t in toks if t.startswith("degree=int,0,")]
        src = _validate_value_src()
        assert "dash fits local polynomials up to degree" not in src
