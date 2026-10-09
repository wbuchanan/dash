"""A continuous histogram dropped the observation at its last bin edge.

GAPS2 C2, measured: ``dash histogram ttl_exp, bin(27)`` on nlsw88 counted
2245 of 2246 rows; ``dash histogram pop, bin(75)`` on census counted 49 of
50; about 4% of random rounded layers lost a row.  No note was printed, and
density bars were rescaled to the rows that remained.

The cause: the continuous branch of ``GlyphMapper.map_histogram`` counted
with ``np.histogram(arr, bins=edges)``, whose last bin is closed on the
right at ``edges[-1]``.  ``edges[-1]`` is built as
``start + width*n_bins`` and equals the sample maximum only in EXACT
arithmetic; in floating point it can land a few ULPs below it, and the
tolerance-based extra edge (``_histogram_grid``) did not fire because the
shortfall was smaller than its tolerance.  A value at or a few ULPs above
``edges[-1]`` then fell outside every bin and was silently excluded.  The
saved page's JavaScript recount (``_FILTER_JS``) made the same choice with
a hard range test (``v < edges[0] || v > edges[edges.length - 1]``).

Stata never has this problem: ``twoway__histogram_gen.ado:200-203`` counts
every observation as ``floor((v - min)/h)``, then folds an index below 0
into bar 0 and an index equal to ``bin`` into bar ``bin-1`` -- a value at
or floating above the last edge is in the last bar, by construction, and
a value below a tolerated ``start()`` is in the first.

After the fix, ``GlyphMapper.map_histogram`` counts the continuous branch
exactly as its discrete branch already did: floor, clamp, ``np.bincount``,
through the new ``GlyphMapper._histogram_counts``.  The aggregate config
the recount reads carries ``start``, ``width`` and ``bin``, and the saved
page's JavaScript applies the same floor-and-clamp with those numbers
instead of rebuilding ``h`` from the edges.
"""
import importlib.util
import json
import os
import sys

import numpy as np
import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402

GM = dr.GlyphMapper

from js_runner import run_filter_js_block, NODE
from test_statistical_helpers import _hist
from conftest import make_data_json

_DATA_DIR = os.path.join(_HERE, "fixtures", "data")


from conftest import render_models  # noqa: E402


def _load(name):
    return pd.read_csv(os.path.join(_DATA_DIR, f"{name}.csv"))


_NLSW88 = _load("nlsw88")
_CENSUS = _load("census")
_TTL_EXP = _NLSW88["ttl_exp"].dropna().to_numpy(dtype=float)
_POP = _CENSUS["pop"].dropna().to_numpy(dtype=float)


def _mapper():
    return GM(dr.OptionTranslator(), dr.SchemeParser("s2color"))


def _floor_clamp_reference(arr, start, width, nb):
    """An independent (test-only) restatement of Stata's rule, used only to
    derive an expected value; production code must go through
    ``GlyphMapper._histogram_counts`` itself, never this copy."""
    idx = np.floor((np.asarray(arr, dtype=float) - start) / width)
    idx = np.clip(idx, 0, nb - 1).astype(np.int64)
    return np.bincount(idx, minlength=nb).astype(float)


class TestNlsw88AndCensusRegressions:
    """The two cases GAPS2 measured directly, plus the guarantees BR-05.1
    and BR-05.8 make about every histogram."""

    @pytest.mark.parametrize("n", [27, 51, 54, 83])
    def test_ttl_exp_bin_27_51_54_83_count_every_row(self, n):
        tops, left, right, _ = _hist(_TTL_EXP, {"bin": str(n),
                                                "frequency": "frequency"})
        assert tops.sum() == 2246, (
            f"bin({n}): dash counted {tops.sum()} of 2246 rows")
        assert len(tops) == n

    def test_census_pop_bin_75_counts_every_row(self):
        tops, left, right, _ = _hist(_POP, {"bin": "75",
                                            "frequency": "frequency"})
        assert tops.sum() == 50, f"bin(75): dash counted {tops.sum()} of 50 rows"
        assert len(tops) == 75

    def test_density_bars_integrate_to_one_on_ttl_exp_bin_27(self):
        tops, left, right, _ = _hist(_TTL_EXP, {"bin": "27"})
        widths = right - left
        assert float((tops * widths).sum()) == pytest.approx(1.0, abs=1e-12)
        # The last bar's density must follow from the FOLD-CORRECTED count,
        # not from whatever count np.histogram happened to give it.
        h = float(widths[-1])
        start = float(left[0])
        want_counts = _floor_clamp_reference(_TTL_EXP, start, h, len(tops))
        want_last = float(want_counts[-1]) / (float(want_counts.sum()) * h)
        assert tops[-1] == pytest.approx(want_last, rel=1e-9)

    def test_a_missing_value_row_is_dropped_before_counting(self, tmp_path):
        # F-13's guarantee: _layer_weights -> _masked drops a NaN row before
        # the count ever sees it.  This holds today (the mapper's masking is
        # untouched by this section); it is a guard, not a regression.
        tops, left, right, _ = _hist([1.0, float("nan"), 2.0, 3.0],
                                     {"bin": "3", "frequency": "frequency"})
        assert tops.sum() == 3
        assert len(tops) == 3

        # And in the served build over the same four rows.
        df = pd.DataFrame({"v": [1.0, float("nan"), 2.0, 3.0]})
        spec = _one_histogram_spec("v", {"bin": "3", "frequency": "frequency"})
        served_top = _served_histogram_bars(spec, df, tmp_path)
        assert served_top is not None
        assert float(np.sum(served_top)) == 3


@pytest.mark.skipif(NODE is None, reason="node is not installed; set DASH_NODE")
class TestTheJavaScriptRecountAgrees:
    def test_ttl_exp_bin_27_under_node_sums_to_2246(self):
        tops, left, right, r = _hist(_TTL_EXP, {"bin": "27",
                                                "frequency": "frequency"})
        got = run_filter_js_block("histogram", r._dash_agg_config,
                                  _TTL_EXP.tolist())
        assert sum(got["top"]) == 2246
        np.testing.assert_array_equal(got["top"], tops)


def _one_histogram_spec(var, options):
    return {
        "graphs": [{
            "name": "g1",
            "graph_options": {"name": "g1"},
            "options": {"name": "g1"},
            "plots": [{"type": "histogram", "var": var, "options": dict(options)}],
        }],
        "kpis": [],
        "build_options": {
            "layout": "auto", "link": "", "filter": "", "theme": "",
            "scheme": "", "session_scheme": "", "title": "", "subtitle": "",
            "registry": "g1", "tabs": "", "filter_position": "top",
            "level": "95", "formats": {},
        },
    }


def _write_spec_and_data(spec, df, tmp_path, tag="hist_edge"):
    sp = tmp_path / f"{tag}_spec.json"
    dp = tmp_path / f"{tag}_data.json"
    sp.write_text(json.dumps(spec))
    dp.write_text(json.dumps(make_data_json(df)))
    return str(sp), str(dp)


def _saved_histogram_bars(spec, df, tmp_path, tag="hist_edge"):
    sp, dp = _write_spec_and_data(spec, df, tmp_path, tag)
    r = dr.DashRenderer(sp, dp)
    render_models(r)
    fig = r.figures["g1"]
    for gr in fig.renderers:
        data = getattr(gr.data_source, "data", {})
        if "left" in data:
            return np.asarray(data["top"], dtype=float)
    return None


def _served_histogram_bars(spec, df, tmp_path, tag="hist_edge"):
    sp, dp = _write_spec_and_data(spec, df, tmp_path, tag)
    ap = tmp_path / f"{tag}_app.py"
    dr.ServerAppBuilder(sp, dp).build(str(ap))
    ms = importlib.util.spec_from_file_location(f"_{tag}_app", str(ap))
    mod = importlib.util.module_from_spec(ms)
    ms.loader.exec_module(mod)
    doc = Document()
    mod.make_document(doc)
    for root in doc.roots:
        for m in root.references():
            if type(m).__name__ == "figure":
                for gr in m.renderers:
                    data = getattr(gr.data_source, "data", {})
                    if "left" in data:
                        return np.asarray(data["top"], dtype=float)
    return None


class TestBothModes:
    def test_the_served_app_draws_the_same_2246_bars(self, tmp_path):
        df = _NLSW88[["ttl_exp"]].dropna()
        spec = _one_histogram_spec("ttl_exp", {"bin": "27",
                                               "frequency": "frequency"})
        saved_top = _saved_histogram_bars(spec, df, tmp_path)
        served_top = _served_histogram_bars(spec, df, tmp_path)
        assert saved_top is not None and served_top is not None
        assert float(saved_top.sum()) == 2246, (
            f"saved page drew {saved_top.sum()} of 2246 bars")
        assert float(served_top.sum()) == 2246, (
            f"served app drew {served_top.sum()} of 2246 bars")
        np.testing.assert_array_equal(saved_top, served_top)


class TestStartTolerance:
    def test_rows_below_a_tolerated_start_land_in_bar_zero(self):
        start = float(_TTL_EXP.min()) * (1 + 5e-6)
        tops, left, right, r = _hist(
            _TTL_EXP, {"bin": "27", "frequency": "frequency",
                      "start": str(start)})
        assert tops.sum() == 2246
        assert left[0] == pytest.approx(start)
        h = float(right[0] - left[0])
        below_and_first = int(np.sum(_TTL_EXP < start + h))
        assert tops[0] == below_and_first


class TestEveryFrequencyHistogramSumsToN:
    """40 seeded cases across bin()/width()/start(), with and without
    fweights, in both Python and (when available) node."""

    def test_seeded_cases_sum_to_n_in_python_and_under_node(self):
        rng = np.random.RandomState(20260925)
        ran = 0
        for i in range(40):
            n = int(rng.randint(1, 501))
            loc = float(rng.uniform(-50.0, 50.0))
            scale = float(rng.uniform(0.5, 20.0))
            k = int(rng.randint(0, 4))
            vals = np.round(rng.normal(loc, scale, n), k)
            vmin, vmax = float(vals.min()), float(vals.max())
            span = (vmax - vmin) or 1.0
            eps = max(abs(vmin), 1.0) * 5e-6

            variant = i % 4
            opts = {"frequency": "frequency"}
            if variant == 0:
                opts["bin"] = str(int(rng.randint(1, 101)))
            elif variant == 1:
                w = round(span / float(rng.randint(2, 50)), k + 2) or 1.0
                opts["width"] = str(w)
            elif variant == 2:
                opts["bin"] = str(int(rng.randint(1, 101)))
                opts["start"] = str(vmin + eps)
            else:
                w = round(span / float(rng.randint(2, 50)), k + 2) or 1.0
                opts["width"] = str(w)
                opts["start"] = str(vmin + eps)

            weights = None
            if i % 5 == 4:
                weights = rng.randint(1, 4, n).astype(float)

            tops, left, right, r = _hist(vals, opts, weights=weights)
            want_n = float(weights.sum()) if weights is not None else float(n)
            assert tops.sum() == pytest.approx(want_n, rel=1e-9), (i, opts)
            if "bin" in opts:
                assert len(tops) == int(opts["bin"]), (i, opts)
            h = float(right[-1] - left[-1]) if len(right) > 1 else float(right[0] - left[0])
            assert float(right[-1]) == pytest.approx(
                float(left[0]) + h * len(tops), rel=1e-9), (i, opts)

            if NODE is not None:
                ac = r._dash_agg_config
                got = run_filter_js_block(
                    "histogram", ac, [float(v) for v in vals],
                    [float(w) for w in weights] if weights is not None else None)
                np.testing.assert_allclose(
                    np.asarray(got["top"], dtype=float), tops,
                    rtol=1e-9, atol=1e-9, err_msg=f"case {i}, opts {opts}")
            ran += 1
        assert ran == 40, "not every seeded case ran"


class TestHistogramCounts:
    """Direct unit tests of GlyphMapper._histogram_counts (rule 3)."""

    def test_a_value_below_start_is_in_bar_zero_and_one_at_the_last_edge_in_the_last_bar(self):
        got = GM._histogram_counts(
            np.array([-0.5, 0.0, 0.5, 2.0, 2.0000000001]), None, 0.0, 1.0, 2)
        np.testing.assert_array_equal(got, [3.0, 2.0])

        got_w = GM._histogram_counts(
            np.array([-0.5, 0.0, 0.5, 2.0, 2.0000000001]),
            np.array([1.0, 1.0, 1.0, 2.0, 3.0]), 0.0, 1.0, 2)
        np.testing.assert_array_equal(got_w, [3.0, 5.0])

    def test_a_nan_in_arr_is_refused_not_miscounted(self):
        with pytest.raises(ValueError, match="_layer_weights"):
            GM._histogram_counts(np.array([0.5, float("nan")]), None, 0.0, 1.0, 2)
        with pytest.raises(ValueError, match="_layer_weights"):
            GM._histogram_counts(np.array([0.5, 0.6]),
                                 np.array([1.0, float("nan")]), 0.0, 1.0, 2)


class TestTheAggConfigCarriesTheRule:
    def test_start_width_and_bin_are_numbers_the_page_can_read(self):
        tops, left, right, r = _hist(_TTL_EXP, {"bin": "27",
                                                "frequency": "frequency"})
        ac = r._dash_agg_config
        assert isinstance(ac["start"], float)
        assert isinstance(ac["width"], float)
        assert isinstance(ac["bin"], int)
        assert ac["width"] > 0
        assert ac["bin"] == len(ac["bin_edges"]) - 1
        assert "discrete" in ac
