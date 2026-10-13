"""The range(), n(), bwidth() and level() values twoway accepts (WP-31 C10a).

GAPS3 C10 (the part a rules-table edit closes, C10a): dash refused values
twoway draws -- ``lfit ..., range(. 4000)``, ``kdensity mpg,
range(weight)``, ``kdensity mpg, bwidth(0)``, ``lowess ..., bwidth(5)``,
``n(1)`` -- and bounded ``level()`` strictly inside 0-100 on lfitci, qfitci
and fpfitci, where twoway takes any number.  What twoway does is measured
in test/fixtures/value_bounds_truth.json
(scripts/extract_value_bounds_truth.do, twoway only):

* lfit, qfit, lfitci and qfitci read ``range()`` as two numbers, ``.``
  standing for the data's own bound; a variable name there is r(121)
  "range() invalid -- invalid numlist";
* kdensity and function read two numbers or one variable name (its min
  and max); a ``.`` there is r(127);
* lowess resets every ``bwidth()`` outside (0, 1) to .8 in silence;
* kdensity ``bwidth(0)`` is the default rule; lpoly and lpolyci refuse it;
* ``n(1)`` is accepted;
* lfitci, qfitci and fpfitci draw any ``level()`` (no band at 100 or
  above); lpolyci alone bounds it, 10 to 99.99.
"""
import inspect
import json
import os
import re
import sys
import tempfile
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_FIX = os.path.join(_HERE, "fixtures", "value_bounds_truth.json")
_ADO = os.path.join(_HERE, "..", "dash.ado")
_AUTO = os.path.join(_HERE, "fixtures", "data", "auto.csv")


@pytest.fixture(scope="module")
def truth():
    with open(_FIX, encoding="utf-8") as fh:
        return json.load(fh)


def _fixture():
    with open(_FIX, encoding="utf-8") as fh:
        return json.load(fh)


def _plot_tokens():
    """The tokens of _dash_option_rules' `local plot'."""
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


def _lines(models):
    """(x, y) of every Line glyph renderer among *models*."""
    from bokeh.models import GlyphRenderer, Line
    out = []
    for m in models:
        if isinstance(m, GlyphRenderer) and isinstance(m.glyph, Line):
            d = m.data_source.data
            out.append((np.asarray(d[m.glyph.x], dtype=float),
                        np.asarray(d[m.glyph.y], dtype=float)))
    return out


def _render(mode, plots):
    spec = tp._spec(plots)
    if mode == "saved":
        r, w = tp._standalone(spec)
        models = list(r._last_layout_root.references())
    else:
        doc, w = tp._served(spec)
        models = [m for root in doc.roots for m in root.references()]
    return models, w


class TestTheFixture:
    def test_meta_is_stamped(self, truth):
        assert sorted(truth["_meta"]) == ["born_date", "dash_commit",
                                          "extracted", "source",
                                          "stata_version"]
        assert truth["_meta"]["source"] == \
            "scripts/extract_value_bounds_truth.do"

    def test_twoways_readings(self, truth):
        # The readings the rules below are written from.
        assert truth["lowess_bwidth"]["5"]["reset"] == 1
        assert truth["lowess_bwidth"][".3"]["reset"] == 0
        assert truth["level"]["5"]["rc"] == 0
        assert truth["level"]["lpolyci_5"]["rc"] == 198
        assert truth["level"]["lpolyci_5"]["message"] == \
            "level() must be between 10 and 99.99 inclusive"
        assert truth["range"]["var_lfit"]["rc"] == 121
        assert truth["range"]["var_kdensity"]["rc"] == 0
        assert truth["range"]["dot_hi"]["rc"] == 0
        assert truth["n"]["one"]["rc"] == 0
        assert truth["bwidth"]["kdensity_0"]["rc"] == 0
        assert truth["bwidth"]["lpoly_0"]["rc"] == 198


class TestTheTokens:
    def test_level_is_typed(self):
        t = _plot_tokens()
        assert "level=num,0,100,x" not in t
        assert "level=num@lfitci|qfitci|fpfitci" in t
        assert "level=num,10,99.99@lpolyci" in t

    def test_range_is_the_range_kind(self):
        t = _plot_tokens()
        assert "range=numlist,2,2" not in t
        assert "range=range,2,2,m@lfit|qfit|lfitci|qfitci" in t
        assert "range=range,2,2" in t

    def test_n_allows_one(self):
        t = _plot_tokens()
        assert "n=int,1,10000" in t and "n=int,2,10000" not in t

    def test_bwidth_allows_zero_on_kdensity(self):
        t = _plot_tokens()
        assert "bwidth=num@lowess" in t
        assert "bwidth=num,0@kdensity" in t
        assert "bwidth=pos" in t and "bwidth=pos,1@lowess" not in t


class TestRangeBounds:
    def test_each_form(self):
        x = np.array([np.nan, 2.0, 5.0, 9.0, np.nan])
        f = dr._dash_range_bounds
        assert f({"range": "1 10"}, x) == (1.0, 10.0)
        assert f({"range": "10 1"}, x) == (1.0, 10.0)
        assert f({"range": ". 10"}, x) == (2.0, 10.0)
        assert f({"range": "1 ."}, x) == (1.0, 9.0)
        assert f({"range": ". ."}, x) == (2.0, 9.0)
        assert f({}, x) == (2.0, 9.0)

    def test_served_copy(self):
        spec = tp._spec([plot_for("lfit", {"range": ". 4000"})])
        _tag, sp, dp = tp._write(spec)
        with tempfile.TemporaryDirectory() as d:
            ap = os.path.join(d, "app.py")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                dr.ServerAppBuilder(sp, dp).build(ap)
            with open(ap, encoding="utf-8") as fh:
                assert "def _dash_range_bounds(" in fh.read()


class TestFitGrid:
    def test_one_point(self):
        x = np.array([3.0, 1.0, 7.0])
        g = dr._fit_grid(x, {"n": "1"}, "lfit")
        assert g.tolist() == [1.0]

    def test_dot_bound(self):
        x = np.array([1760.0, 3000.0, 4840.0])
        g = dr._fit_grid(x, {"range": ". 4000", "n": "3"}, "lfit")
        assert g.tolist() == [1760.0, 2880.0, 4000.0]
        g = dr._fit_grid(x, {"range": "1000 .", "n": "3"}, "lfit")
        assert g.tolist() == [1000.0, 2920.0, 4840.0]


def _reset_values():
    return sorted(v for v, r in _fixture()["lowess_bwidth"].items()
                  if r["reset"] == 1)


class TestLowessReset:
    @pytest.mark.parametrize("v", _reset_values())
    def test_reset_values(self, v, truth):
        auto = pd.read_csv(_AUTO)
        x = auto["weight"].to_numpy(float)
        y = auto["mpg"].to_numpy(float)
        _xs, got = dr.GlyphMapper._stata_lowess(x, y, bw=float(v))
        _xs, at8 = dr.GlyphMapper._stata_lowess(x, y, bw=0.8)
        _xs, at3 = dr.GlyphMapper._stata_lowess(x, y, bw=0.3)
        assert np.array_equal(got, at8)
        assert not np.allclose(got, at3)
        # twoway's own curve: its serset's y sum.
        assert abs(got.sum() - truth["lowess_bwidth"][v]["serset"][0]["sum"]) < 1e-6

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_silent(self, mode):
        base, w0 = _render(mode, [plot_for("lowess", {"bwidth": ".8"})])
        got, w = _render(mode, [plot_for("lowess", {"bwidth": "5"})])
        assert w == w0
        (bx, by), = _lines(base)
        (gx, gy), = _lines(got)
        assert np.array_equal(by, gy)


class TestKdensityZero:
    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_zero_is_the_rule(self, mode):
        base, w0 = _render(mode, [plot_for("kdensity")])
        got, w = _render(mode, [plot_for("kdensity", {"bwidth": "0"})])
        assert w == w0
        (bx, by), = _lines(base)
        (gx, gy), = _lines(got)
        assert np.array_equal(bx, gx) and np.array_equal(by, gy)
        if mode == "saved":
            cfg = [getattr(m, "_dash_agg_config", None) for m in got]
            cfg = [c for c in cfg if c and c.get("type") == "kdensity"]
            assert cfg and cfg[0]["bw_fixed"] is None

    def test_n_one(self):
        got, _w = _render("saved", [plot_for("kdensity", {"n": "1"})])
        (gx, gy), = _lines(got)
        assert gx.tolist() == [14.0]


class TestRangeVar:
    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_both_modes(self, mode):
        base, w0 = _render(mode, [plot_for("kdensity", {"range": "1800 4080"})])
        got, w = _render(mode, [plot_for("kdensity", {"range": "1800 4080",
                                                      "range_var": "weight"})])
        assert w == w0
        (bx, by), = _lines(base)
        (gx, gy), = _lines(got)
        assert np.array_equal(bx, gx) and np.array_equal(by, gy)


class TestLevel:
    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_any_level_draws_as_twoway(self, mode):
        # twoway lfitci level(150) and level(100) draw the fit with no band;
        # level(5) a narrow band; none is refused or noted.
        base, w0 = _render(mode, [plot_for("lfitci")])
        for lv in ("5", "100", "150", "-1"):
            _got, w = _render(mode, [plot_for("lfitci", {"level": lv})])
            assert w == w0, lv

    def test_band_missing_at_100_and_above(self):
        opts = {"level": "150"}
        assert dr._resolve_level(opts, 95.0, "lfitci") == 150.0
        assert np.isnan(dr._dash_ci_t(150.0, 10))
        assert np.isnan(dr._dash_ci_t(100.0, 10))
        assert dr._dash_ci_t(0.0, 10) == 0.0
        assert dr._dash_ci_t(-1.0, 10) < 0.0
        assert abs(dr._dash_ci_t(95.0, 10) - 2.2281388519649) < 1e-9

    def test_lpolyci_keeps_twoways_bound(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            assert dr._resolve_level({"level": "5"}, 95.0, "lpolyci") == 95.0


class TestMessages:
    def test_dash_own_sentences_removed(self):
        src = _validate_value_src()
        assert "fraction of the sample" not in src
        # n's 10000 is dash's own limit and keeps its sentence, for a value
        # above it only.
        assert "dash evaluates up to 10000 points." in src

    def test_range_kind_has_a_branch(self):
        assert 'else if "`kind\'" == "range"' in _validate_value_src()
