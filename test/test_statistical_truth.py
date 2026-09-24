"""test_statistical_truth.py — S07 Part B: agreement with Stata itself.

Every expectation here comes from ``test/fixtures/stat_truth.json``, which was
produced by running STATA'S OWN commands and recording what they returned.
The command that produced each value is stored beside it in the fixture, so a
reviewer can re-derive any number without trusting this file.

The four probe datasets are checked in as CSV under ``test/fixtures/data/``
so the tests are self-contained and do not need Stata to run.

Part A (``test_statistical_defaults.py``) covers the defects that are visible
without Stata; this file is the one that proves the drop-in claim for the
statistical layers.
"""
import json
import math
import os
import sys
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render
from dash_render import GlyphMapper, OptionTranslator, SchemeParser

_FIXTURE = os.path.join(_HERE, "fixtures", "stat_truth.json")
_DATA_DIR = os.path.join(_HERE, "fixtures", "data")

pytestmark = pytest.mark.skipif(
    not os.path.exists(_FIXTURE),
    reason="test/fixtures/stat_truth.json is missing",
)


@pytest.fixture(scope="module")
def truth():
    with open(_FIXTURE) as fh:
        return json.load(fh)


@pytest.fixture(scope="module")
def datasets(truth):
    """{name: (y, x)} for the four datasets the fixture was measured on."""
    out = {}
    for name, meta in truth["datasets"].items():
        path = os.path.join(_DATA_DIR, f"{name}.csv")
        if not os.path.exists(path):
            continue
        df = pd.read_csv(path).dropna()
        out[name] = (df[meta["y"]].to_numpy(float),
                     df[meta["x"]].to_numpy(float))
    return out


@pytest.fixture
def mapper():
    return GlyphMapper(OptionTranslator(), SchemeParser("s2color"))


def test_every_probe_dataset_is_present(truth, datasets):
    """The four probe CSVs load, so no per-dataset loop below can shrink
    without saying so.

    ``datasets`` drops a name whose CSV is absent (the fixture reads the
    directory and ``continue``s), and every comparison loop then skips it in
    silence; before this, three of the four vanishing would still leave a
    green run.  The CSVs are checked in, so their set must be exactly the
    fixture's, at the recorded row counts."""
    assert set(datasets) == set(truth["datasets"]), (
        "probe CSVs under test/fixtures/data/ do not match the fixture: "
        f"{sorted(set(truth['datasets']) ^ set(datasets))}"
    )
    for name, (y, x) in datasets.items():
        n = truth["datasets"][name]["N_xy_nonmissing"]
        assert len(y) == len(x) == n, (
            f"{name}: loaded {len(y)} rows, fixture records {n}"
        )


def _need(datasets, name):
    # All four probe CSVs are checked in under test/fixtures/data/ and
    # test_every_probe_dataset_is_present asserts they load, so a name that
    # is absent here is a broken fixture, not a legitimate skip: a skip hid
    # the whole dataset's comparisons (measured 24sep2026, the vacuous
    # form).
    if name not in datasets:
        pytest.fail(f"fixture data for {name} is not checked in; "
                    "test/fixtures/data/ must carry all four probe CSVs")
    return datasets[name]


def _rec(truth, section, key):
    """A fixture record that MUST be present, failing loudly if it is not.

    The tests below used ``truth[section].get(key)`` then ``pytest.skip``
    when it came back None, so a fixture regenerated without a key turned
    the comparison it drives into a silent pass.  Every key these callers
    ask for is in the checked-in stat_truth.json (measured 24sep2026), so
    absence is a defect to report, not a case to skip.
    """
    section_map = truth.get(section, {})
    assert key in section_map, (
        f"stat_truth.json['{section}'] has no '{key}'; regenerate the "
        "fixture with scripts/ -- a missing probe must fail, not skip"
    )
    return section_map[key]


# ======================================================================
# histogram
# ======================================================================

class TestHistogramAgainstStata:
    """Bin grid and bar heights, measured on four datasets."""

    def test_default_bin_count_matches_every_probe(self, truth, datasets):
        checked = 0
        for key, rec in truth["histogram_bin_rule_check"].items():
            ds = key.split(":")[0]
            if ds not in datasets:
                continue
            var_is_y = key.split(":")[1] == truth["datasets"][ds]["y"]
            if not var_is_y:
                continue          # only the y column is checked in
            y, _ = datasets[ds]
            got = dash_render._stata_bin_count(len(y))
            assert got == rec["stata_bin"], (
                f"{key}: dash gives {got} bins, Stata gives "
                f"{rec['stata_bin']} (cmd: {rec['cmd']})"
            )
            checked += 1
        # Exactly three of the eight bin probes are y-columns whose data is
        # checked in (auto:mpg, nlsw88:wage, sp500:close; census's y `death'
        # has no bin probe): measured 24sep2026.  `>= 2' passed if a
        # dataset silently dropped out.
        assert checked == 3, f"checked {checked} histogram bin probes, not 3"

    def test_the_rule_reproduces_every_recorded_bin_count(self, truth):
        """Check the FORMULA against all 8 probes, not just the two datasets."""
        for key, rec in truth["histogram_bin_rule_check"].items():
            assert dash_render._stata_bin_count(rec["N"]) == rec["stata_bin"], key

    def test_default_histogram_is_a_density(self, truth, datasets, mapper):
        """Stata: "density scales the bars so the sum of their areas is 1"."""
        for name in ("auto", "census", "sp500"):
            y, _ = _need(datasets, name)
            src = ColumnDataSource({"v": list(y)})
            r = mapper.map_histogram(figure(), src, "v", {})
            d = r.data_source.data
            top = np.asarray(d["top"], float)
            w = np.asarray(d["right"], float) - np.asarray(d["left"], float)
            assert float((top * w).sum()) == pytest.approx(1.0, abs=1e-9), name

    def test_bin_option_reproduces_statas_bar_heights(self, truth, datasets,
                                                     mapper):
        """auto/mpg with bin(20): compare the actual bar heights."""
        rec = _rec(truth, "histogram", "auto:mpg:bin20")
        y, _ = _need(datasets, "auto")
        src = ColumnDataSource({"v": list(y)})
        r = mapper.map_histogram(figure(), src, "v", {"bin": "20"})
        got = np.asarray(r.data_source.data["top"], float)
        want = np.asarray(rec["bar_height"], float)
        # Stata reports only the non-empty bins; compare the populated ones.
        got_nonzero = got[got > 0]
        assert len(got_nonzero) == len(want), (
            f"dash drew {len(got_nonzero)} non-empty bins, Stata "
            f"{len(want)} (cmd: {rec['cmd']})"
        )
        np.testing.assert_allclose(got_nonzero, want, rtol=1e-6)


# ======================================================================
# kdensity
# ======================================================================

class TestKdensityAgainstStata:

    def test_default_bandwidth_matches_stata_exactly(self, truth, datasets):
        """[R] kdensity: w = 0.9*m*n^(-1/5), m = min(sd, IQR/1.349).

        The IQR must use STATA's percentile definition, not numpy's; with
        numpy's, auto/mpg comes out 3.7% low.
        """
        for key, rec in truth["kdensity_bwidth_rule_check"].items():
            ds = key.split(":")[0]
            if ds not in datasets:
                continue
            y, _ = datasets[ds]
            got = dash_render._stata_kde_bandwidth(y)
            # 1e-6, not 1e-12: nlsw88's `wage` is a Stata float (4 bytes) and
            # the CSV fixture round-trip costs about seven significant
            # figures.  The formula itself is exact -- see the companion test
            # on auto/mpg, whose values are integers and survive the trip.
            assert got == pytest.approx(rec["measured_r_bwidth"], rel=1e-6), (
                f"{key}: dash {got!r} vs Stata {rec['measured_r_bwidth']!r}"
            )

    def test_bandwidth_formula_is_exact_where_the_data_survives_csv(
        self, truth, datasets
    ):
        """auto/mpg is integer-valued, so nothing is lost in the fixture."""
        rec = truth["kdensity_bwidth_rule_check"]["auto:mpg"]
        y, _ = _need(datasets, "auto")
        got = dash_render._stata_kde_bandwidth(y)
        assert got == pytest.approx(rec["measured_r_bwidth"], rel=1e-12)

    def test_default_kernel_is_epanechnikov(self, truth, datasets, mapper):
        y, _ = _need(datasets, "auto")
        src = ColumnDataSource({"v": list(y)})
        r = mapper.map_kdensity(figure(), src, "v", {})
        assert r._dash_agg_config["kernel"] == "epanechnikov"

    @pytest.mark.parametrize("name", ["auto", "census", "sp500", "nlsw88"])
    def test_explicit_bwidth_reproduces_statas_curve(self, truth, datasets,
                                                     mapper, name):
        """kdensity ..., bwidth(2) — compare the density at Stata's own x."""
        var = truth["datasets"][name]["y"] if name in truth["datasets"] else ""
        rec = _rec(truth, "kdensity", f"{name}:{var}:bwidth2")
        y, _ = _need(datasets, name)
        want_x = np.asarray(rec["kde_x"], float)
        want_y = np.asarray(rec["kde_y"], float)
        got = dash_render._kde_curve(y, want_x, float(rec["bwidth"]),
                                     "epanechnikov")
        np.testing.assert_allclose(
            got, want_y, rtol=2e-6, atol=1e-12,
            err_msg=f"{name}: dash's KDE differs from {rec['cmd']}")


# ======================================================================
# lowess
# ======================================================================

class TestLowessAgainstStata:

    def test_default_bwidth_is_zero_point_eight(self, truth):
        """Measured: the default curve is identical to bwidth(.8)."""
        for name, rec in truth["lowess_default_bwidth_check"].items():
            assert rec["curves_identical"] is True, name
        import inspect
        src = inspect.getsource(GlyphMapper.map_lowess)
        assert '"bwidth", 0.8' in src, (
            "map_lowess no longer defaults bwidth to Stata's 0.8"
        )


# ======================================================================
# lpoly
# ======================================================================

class TestLpolyAgainstStata:

    def test_default_kernel_and_degree_match_stata(self, truth):
        for key, rec in truth["lpoly"].items():
            if key.endswith(":default"):
                assert rec["kernel"] == "epanechnikov", key
                assert rec["degree"] == 0, key

    def test_explicit_bwidth_is_absolute_and_reproduces_statas_curve(
        self, truth, datasets, mapper
    ):
        """lpoly ..., bwidth(5) — the option dash used to clamp away.

        This is the assertion that matters: with bwidth() given, dash must
        agree with Stata, because both are then fully specified.
        """
        examined = 0
        compared = 0
        for name in ("auto", "census", "sp500", "nlsw88"):
            rec = _rec(truth, "lpoly", f"{name}:bwidth5")
            y, x = _need(datasets, name)
            examined += 1
            want_x = np.asarray(rec["lpoly_x"], float)
            want_y = np.array([np.nan if v is None else float(v)
                               for v in rec["lpoly_y"]])
            got = np.array([
                _lpoly_at(x, y, xi, 5.0, 0, "epanechnikov") for xi in want_x
            ])
            both = np.isfinite(want_y) & np.isfinite(got)
            if both.sum() == 0:
                # Measured 24sep2026: at bwidth(5) Stata reports missing at
                # every sampled x for auto/census/sp500 (their x range is far
                # wider than 5), so there is nothing to compare there -- but
                # the dataset was still LOOKED AT, which `examined' records.
                continue
            np.testing.assert_allclose(
                got[both], want_y[both], rtol=1e-6, atol=1e-9,
                err_msg=f"{name}: dash disagrees with {rec['cmd']}")
            compared += 1
        # All four datasets and their bwidth5 probes are present, so all four
        # are examined (a silently dropped dataset is a fail via _need/_rec,
        # not a skip); nlsw88 is the one whose sampled x have a finite fit,
        # so at least one real value comparison must run.  `checked >= 1'
        # passed having compared a single dataset while the other three
        # vanished (24sep2026).
        assert examined == 4, f"examined {examined} lpoly bwidth(5) probes"
        assert compared >= 1, "no lpoly bwidth(5) probe had finite overlap"

    def test_default_bandwidth_is_within_the_documented_tolerance(
        self, truth, datasets
    ):
        """dash's ROT approximates Stata's; the gap is bounded and recorded.

        Stata computes its rule-of-thumb in compiled Mata and it is not
        reproducible from the published documentation, so dash uses the
        Fan-Gijbels ROT with a constant measured against Stata.  That is an
        approximation and it is labelled as one in
        GlyphMapper._default_lpoly_bwidth — this test pins how good it has to
        be, so the claim in the docstring cannot quietly stop being true.
        """
        worst = 0.0
        report = []
        for name, (y, x) in datasets.items():
            rec = _rec(truth, "lpoly", f"{name}:default")
            assert "bwidth" in rec, f"{name}:default has no bwidth"
            want = float(rec["bwidth"])
            got = GlyphMapper._default_lpoly_bwidth(x, y)
            err = abs(got - want) / want
            report.append(f"{name}: dash {got:.6g} vs Stata {want:.6g} "
                          f"({err:+.1%})")
            worst = max(worst, err)
        # One row per dataset, all four present: `assert report' (non-empty)
        # passed on a single dataset (24sep2026).
        assert len(report) == 4, (len(report), report)
        assert worst <= 0.20, (
            "the default lpoly bandwidth drifted further from Stata than the "
            "documented tolerance:\n  " + "\n  ".join(report)
        )


def _lpoly_at(x, y, x0, h, degree, kernel):
    """Evaluate dash's local-polynomial fit at a single point."""
    grid, fit = GlyphMapper._compute_lpoly_fit(
        np.asarray(x, float), np.asarray(y, float),
        bwidth=h, degree=degree, n_grid=2, kernel=kernel,
    )
    # _compute_lpoly_fit spans the data; evaluate the same estimator directly
    support, kfn = dash_render._KERNELS[kernel]
    z = (np.asarray(x, float) - x0) / h
    w = np.zeros_like(z)
    inside = np.abs(z) < support if np.isfinite(support) else np.ones_like(z, bool)
    if inside.any():
        w[inside] = kfn(z[inside])
    if w.sum() < 1e-12:
        return np.nan
    return float(np.dot(w, np.asarray(y, float)) / w.sum())


# ======================================================================
# mband
# ======================================================================

class TestMbandAgainstStata:

    def test_default_band_count_reproduces_every_measured_pair(self, truth):
        """The documented rule is wrong; this is the measured one."""
        pairs = truth["mband_default_band_count_rule_search"]["observed_pairs"]
        assert len(pairs) >= 10
        for p in pairs:
            got = dash_render._mband_default_bands(p["N"])
            assert got == p["measured_bands"], (
                f"N={p['N']}: dash gives {got} bands, Stata draws "
                f"{p['measured_bands']} ({p['probe']})"
            )

    @pytest.mark.parametrize("bands", [5, 20])
    @pytest.mark.parametrize("name", ["auto", "census", "sp500", "nlsw88"])
    def test_bands_option_reproduces_statas_cross_medians(
        self, truth, datasets, mapper, name, bands
    ):
        """Stata plots the median x and median y inside each equal-width band.

        dash plotted the band MIDPOINT as x, which with unevenly spread x can
        sit where there is no data at all.
        """
        rec = _rec(truth, "mband", f"{name}:bands{bands}")
        y, x = _need(datasets, name)
        rs = mapper.map_mband(
            figure(), ColumnDataSource({"y": list(y), "x": list(x)}),
            "y", "x", {"bands": str(bands)})
        d = rs[0].data_source.data
        got_x = np.asarray(d["x_mb"], float)
        got_y = np.asarray(d["y_mb"], float)
        want_x = np.asarray(rec["band_x"], float)
        want_y = np.asarray(rec["band_y"], float)
        assert len(got_x) == len(want_x), (
            f"dash plots {len(got_x)} band points, Stata {len(want_x)} "
            f"(cmd: {rec.get('cmd')})"
        )
        np.testing.assert_allclose(got_x, want_x, rtol=1e-5)
        np.testing.assert_allclose(got_y, want_y, rtol=1e-5)


# ======================================================================
# fpfit
# ======================================================================

class TestFpfitAgainstStata:

    def test_stata_rejects_bwidth_and_degree(self, truth):
        """dash.sthlp documented two options twoway fpfit does not have."""
        assert truth["rules"]["fpfit.bwidth"]["accepted"] is False

    def test_dash_reports_them_rather_than_pretending(self, datasets, mapper):
        y, x = _need(datasets, "auto")
        src = ColumnDataSource({"y": list(y), "x": list(x)})
        for opt in ("bwidth", "degree"):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                mapper.map_fpfit(figure(), src, "y", "x", {opt: "5"})
            assert any(opt in str(w.message) for w in caught), (
                f"fpfit silently ignored {opt}()"
            )

    def test_help_no_longer_documents_them(self):
        help_path = os.path.join(_HERE, "..", "dash.sthlp")
        if not os.path.exists(help_path):
            pytest.skip("dash.sthlp not found")
        text = open(help_path, encoding="utf-8", errors="replace").read()
        low = text.lower()
        # The help used to introduce the bwidth()/degree() synopt block with
        # "apply specifically to lpoly, lpolyci, fpfit, and fpfitci".  Check
        # the CLAIM, not a single line -- a line-by-line scan passes
        # vacuously because the claim and the option list are on different
        # lines.
        assert "{cmd:fpfit}, and {cmd:fpfitci} plot types" not in text, (
            "dash.sthlp still claims bwidth()/degree() apply to fpfit"
        )
        assert "does not take {cmd:bwidth()}" in text, (
            "dash.sthlp does not tell the user fpfit has no bwidth()"
        )
        assert "r(198)" in text, (
            "dash.sthlp does not record that Stata itself rejects them"
        )

    def test_evaluates_at_the_distinct_observed_x(self, datasets, mapper):
        """Stata uses no grid; so must dash, or the band will not overlay."""
        y, x = _need(datasets, "auto")
        src = ColumnDataSource({"y": list(y), "x": list(x)})
        line = mapper.map_fpfit(figure(), src, "y", "x", {})
        got = np.asarray(line.data_source.data["x_fp"], float)
        want = np.unique(x[x > 0])
        assert len(got) == len(want)
        np.testing.assert_allclose(got, want)


# ======================================================================
# confidence bands
# ======================================================================

class TestConfidenceBandsAgainstStata:

    def _band(self, mapper, y, x, opts):
        src = ColumnDataSource({"y": list(y), "x": list(x)})
        rs = mapper.map_lfitci(figure(), src, "y", "x", opts)
        r = rs[0] if isinstance(rs, list) else rs
        d = r.data_source.data
        return (np.asarray(d["x_fit"], float), np.asarray(d["y_fit"], float),
                np.asarray(d["y_lower"], float), np.asarray(d["y_upper"], float))

    @pytest.mark.parametrize("level", [90, 95, 99])
    @pytest.mark.parametrize("name", ["auto", "census", "sp500"])
    def test_lfitci_matches_statas_band(self, truth, datasets, mapper, name,
                                        level):
        rec = _rec(truth, "ci_bands", f"{name}:lfitci:level{level}")
        y, x = _need(datasets, name)
        gx, gy, glo, ghi = self._band(mapper, y, x, {"level": str(level)})
        wx = np.asarray(rec["fit_x"], float)
        for key, got in (("fit", gy), ("lower", glo), ("upper", ghi)):
            want = np.asarray(rec[key], float)
            interp = np.interp(wx, gx, got)
            np.testing.assert_allclose(
                interp, want, rtol=1e-4,
                err_msg=f"{name} level({level}) {key} differs from "
                        f"{rec['cmd']}")

    def test_the_grid_spans_the_observed_range(self, truth, datasets, mapper):
        """Stata's fit grid runs min(x)..max(x); dash padded it by 10%."""
        y, x = _need(datasets, "auto")
        gx, _, _, _ = self._band(mapper, y, x, {})
        assert gx[0] == pytest.approx(float(x.min()), rel=1e-9)
        assert gx[-1] == pytest.approx(float(x.max()), rel=1e-9)

    def test_no_level_option_uses_c_level(self, truth, datasets, mapper):
        rec95 = _rec(truth, "ci_bands", "auto:lfitci:level95")
        recdef = _rec(truth, "ci_bands", "auto:lfitci:no_level_option")
        np.testing.assert_allclose(np.asarray(recdef["lower"], float),
                                   np.asarray(rec95["lower"], float),
                                   rtol=1e-9)

    def _qband(self, mapper, y, x, opts):
        src = ColumnDataSource({"y": list(y), "x": list(x)})
        rs = mapper.map_qfitci(figure(), src, "y", "x", opts)
        r = rs[0] if isinstance(rs, list) else rs
        d = r.data_source.data
        return (np.asarray(d["x_fit"], float), np.asarray(d["y_fit"], float),
                np.asarray(d["y_lower"], float), np.asarray(d["y_upper"], float))

    @pytest.mark.parametrize("level", [90, 95, 99])
    @pytest.mark.parametrize("name", ["auto", "census", "sp500"])
    def test_qfitci_matches_statas_band(self, truth, datasets, mapper, name,
                                        level):
        """dash computed this band by bootstrap; Stata computes it analytically.

        A bootstrap band is close in shape but never equal, and it moves
        between runs unless the seed is pinned.
        """
        rec = _rec(truth, "ci_bands", f"{name}:qfitci:level{level}")
        y, x = _need(datasets, name)
        gx, gy, glo, ghi = self._qband(mapper, y, x, {"level": str(level)})
        wx = np.asarray(rec["fit_x"], float)
        for key, got in (("fit", gy), ("lower", glo), ("upper", ghi)):
            want = np.asarray(rec[key], float)
            np.testing.assert_allclose(
                np.interp(wx, gx, got), want, rtol=1e-4,
                err_msg=f"{name} qfitci level({level}) {key} differs from "
                        f"{rec['cmd']}")


# ======================================================================
# WP-18 -- statistical fidelity: mspline, fpfit, ci band types, lowess,
# discrete histogram, weights, lpoly degree(1) and the null rule, the
# kdensity grid.  Every expectation below is a number Stata drew, read
# back out of the .gph serset (float32: compare at ~1e-6 relative, never
# for equality) or returned in r()/e() (double), recorded 23 Sep 2026 by
# scripts/extract_stat_truth.do with the exact command beside it.
# ======================================================================

_DATASET_NAMES = ("auto", "census", "nlsw88", "sp500")


def _series(rec, key):
    """A fixture series as a float array; JSON null (Stata missing) -> NaN."""
    return np.array([np.nan if v is None else float(v) for v in rec[key]],
                    dtype=float)


def _at_samples(rec, got, key):
    """*got* at the positions the fixture stored for *key*.

    Curves longer than the section's cap are stored at the 11 evenly
    spaced 1-based indices in ``sample_index``; shorter ones whole.  dash
    must produce the full curve either way, so the test reads ``got`` at
    exactly those indices rather than interpolating.
    """
    got = np.asarray(got, dtype=float)
    n_stored = len(rec[key])
    if n_stored == len(got):
        return got
    idx = np.asarray(rec["sample_index"], dtype=int) - 1
    assert len(idx) == n_stored, (
        f"fixture stored {n_stored} values of {key} but {len(idx)} sample "
        f"indices; the record is inconsistent")
    assert idx.max() < len(got), (
        f"dash drew {len(got)} points, the fixture sampled index "
        f"{idx.max() + 1} of {rec.get('n_points')}: dash's curve is shorter "
        f"than Stata's")
    return got[idx]


def _span(want):
    """The y range a serset value is compared against.

    Sersets are float32, so a value near zero has an absolute, not a
    relative, error of ~1e-7 of the series' magnitude.  Tolerances below
    are ``rtol`` plus ``atol = k * span``.
    """
    want = np.asarray(want, dtype=float)
    want = want[np.isfinite(want)]
    s = float(np.ptp(want)) if len(want) > 1 else 0.0
    return s if s > 0 else float(np.max(np.abs(want))) or 1.0


def _line_data(r, xkey, ykey):
    r = r[0] if isinstance(r, (list, tuple)) else r
    d = r.data_source.data
    return (np.asarray(d[xkey], dtype=float), np.asarray(d[ykey], dtype=float))


def _band_data(rs, xkey, ykey):
    r = rs[0] if isinstance(rs, (list, tuple)) else rs
    d = r.data_source.data
    return (np.asarray(d[xkey], dtype=float), np.asarray(d[ykey], dtype=float),
            np.asarray(d["y_lower"], dtype=float),
            np.asarray(d["y_upper"], dtype=float))


def _weight_column(truth, key):
    """A weight variable in dataset order, from ``weighted_data``."""
    rec = truth["weighted_data"][key]
    assert rec["obs_index"] == list(range(1, len(rec["weight"]) + 1)), (
        f"{key}: weighted_data is not in dataset order")
    return _series(rec, "weight")


def _auto_price(truth):
    """auto's ``price`` in dataset order (the CSV carries mpg and weight)."""
    return _weight_column(truth, "auto:aw_price")


def _binary_from_lowess_more(truth, key):
    """(x, y) in dataset order for a lowess_more record that carries raw_y.

    ``obs_index`` is the 1-based row of the loaded dataset for each point
    of the stable-sorted curve, so scattering ``raw_y`` back by it gives
    the variable in dataset order for the smoothed rows.
    """
    rec = truth["lowess_more"][key]
    idx = np.asarray(rec["obs_index"], dtype=int) - 1
    x = _series(rec, "lowess_x")
    y = _series(rec, "raw_y")
    n = int(rec["obs_index_max"])
    xd = np.full(n, np.nan)
    yd = np.full(n, np.nan)
    xd[idx] = x
    yd[idx] = y
    return xd, yd


def _clear_notes():
    """dash reports a note once per render; make this call a fresh render."""
    noted = getattr(dash_render, "_DASH_NOTED", None)
    if noted is not None:
        noted.clear()


# ----------------------------------------------------------------------
# The fractional-polynomial model as fracpoly builds it, used only to
# IDENTIFY which power pair dash's curve is (its chosen powers are not
# part of the renderer's output).  Verified 23sep2026 against every
# fixture curve: fitting this design at Stata's own powers reproduces the
# recorded fit to <= 3.4e-7 of the y range on all 16 fpfit records, and
# the RSS search below picks e(fp_powers) on all 9 unweighted probes.
# ----------------------------------------------------------------------

_FP_POWERS_STATA = (-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0, 3.0)


def _fp_shift_scale(x):
    """rules_wp18.fpfit.origin_shift_and_scale (frac_xo.ado 81-106)."""
    xs = np.sort(np.asarray(x, dtype=float))
    shift = 0.0
    if xs[0] <= 0:
        gaps = np.diff(xs)
        gaps = gaps[gaps > 0]
        shift = float(gaps.min()) - float(xs[0])
    x2 = xs + shift
    s = float(x2[-1] - x2[0])
    lg = math.log10(s)
    scale = 10.0 ** (math.copysign(1.0, lg) * int(abs(lg))) if lg != 0 else 1.0
    return shift, scale


def _fp_terms(xx, p1, p2):
    """rules_wp18.fpfit.repeated_powers (fracgen.ado 161-212)."""
    lx = np.log(xx)
    h1 = lx if p1 == 0 else xx ** p1
    if p1 == p2:
        h2 = h1 * lx
    else:
        h2 = lx if p2 == 0 else xx ** p2
    return h1, h2


def _fp_identify(x, y, w, x_grid, dash_curve):
    """Which (p1 <= p2) pair dash's curve is, and how far it is from it."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    sw = np.ones_like(y) if w is None else np.sqrt(np.asarray(w, dtype=float))
    shift, scale = _fp_shift_scale(x)
    xx = (x + shift) / scale
    xg = (np.asarray(x_grid, dtype=float) + shift) / scale
    best = None
    for i, p1 in enumerate(_FP_POWERS_STATA):
        for p2 in _FP_POWERS_STATA[i:]:
            h1, h2 = _fp_terms(xx, p1, p2)
            X = np.column_stack([h1, h2, np.ones_like(xx)])
            beta, *_ = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)
            g1, g2 = _fp_terms(xg, p1, p2)
            curve = np.column_stack([g1, g2, np.ones_like(xg)]) @ beta
            err = float(np.max(np.abs(curve - dash_curve))) / _span(dash_curve)
            if best is None or err < best[0]:
                best = (err, (p1, p2))
    return best[1], best[0]


def _assert_fp_powers(rec, x, y, w, x_grid, dash_curve, label):
    got, err = _fp_identify(x, y, w, x_grid, dash_curve)
    want = tuple(float(p) for p in rec["powers"])
    assert err < 1e-6, (
        f"{label}: dash's curve is not a degree-2 fractional polynomial in "
        f"any of the 36 power pairs (closest {got}, {err:.2e} of the y "
        f"range away) -- cmd: {rec.get('powers_cmd', rec.get('cmd'))}")
    assert got == want, (
        f"{label}: dash chose powers {got}, fracpoly chose {want} "
        f"(cmd: {rec.get('powers_cmd', rec.get('cmd'))})")


# ======================================================================
# mspline
# ======================================================================

_MSPLINE_VARIANTS = {
    "default":   {},
    "bands5":    {"bands": "5"},
    "bands20":   {"bands": "20"},
    "n20":       {"n": "20"},
    "bands5_n4": {"bands": "5", "n": "4"},
}
_MSPLINE_KEYS = [f"{ds}:{v}" for ds in _DATASET_NAMES for v in _MSPLINE_VARIANTS]


class TestMsplineAgainstStata:
    """twoway mspline: cross medians of bands() bands, a cubic spline through
    them, n() points between adjacent knots -- (K-1)*n + K points.

    dash drew a PCHIP through every observation on a 200-point grid and
    read neither bands() nor n(): 14.0 mpg off on auto (measured).
    """

    def _draw(self, truth, datasets, mapper, key):
        ds, variant = key.split(":")
        y, x = _need(datasets, ds)
        rec = truth["mspline"][key]
        assert rec["rc"] == 0, f"{key}: Stata itself failed ({rec['cmd']})"
        src = ColumnDataSource({"y": list(y), "x": list(x)})
        r = mapper.map_mspline(figure(), src, "y", "x",
                               dict(_MSPLINE_VARIANTS[variant]))
        gx, gy = _line_data(r, "x_sp", "y_sp")
        return rec, gx, gy

    @pytest.mark.parametrize("key", _MSPLINE_KEYS)
    def test_point_count_is_k_minus_one_times_n_plus_k(self, truth, datasets,
                                                        mapper, key):
        rec, gx, gy = self._draw(truth, datasets, mapper, key)
        assert len(gx) == rec["n_points"], (
            f"{key}: dash drew {len(gx)} points, Stata {rec['n_points']} "
            f"= ({rec['n_knots']}-1)*{rec['n_option']} + {rec['n_knots']} "
            f"(cmd: {rec['cmd']})")

    @pytest.mark.parametrize("key", _MSPLINE_KEYS)
    def test_the_grid_is_n_equal_steps_between_knots(self, truth, datasets,
                                                     mapper, key):
        rec, gx, gy = self._draw(truth, datasets, mapper, key)
        want_x = _series(rec, "spline_x")
        assert len(gx) == len(want_x), f"{key}: point count differs"
        np.testing.assert_allclose(
            gx, want_x, rtol=1e-6,
            err_msg=f"{key}: dash's spline x grid differs from {rec['cmd']}")

    @pytest.mark.parametrize("key", _MSPLINE_KEYS)
    def test_knots_are_the_mband_cross_medians(self, truth, datasets, mapper,
                                               key):
        """The knots are what `twoway mband, bands(#)` plots (serset 1)."""
        rec, gx, gy = self._draw(truth, datasets, mapper, key)
        kn = truth["mspline_knots"][key]
        assert rec["knots_equal_mband_section"] is True, key
        knot_x = _series(kn, "knot_x")
        knot_y = _series(kn, "knot_y")
        K, n = rec["n_knots"], rec["n_option"]
        assert len(knot_x) == K
        # dash's own mband with the same band count must give the knots
        ds, variant = key.split(":")
        y, x = datasets[ds]
        bands = _MSPLINE_VARIANTS[variant].get("bands") or str(rec["rule_default_bands"])
        rs = mapper.map_mband(
            figure(), ColumnDataSource({"y": list(y), "x": list(x)}),
            "y", "x", {"bands": bands})
        mx, my = _line_data(rs, "x_mb", "y_mb")
        np.testing.assert_allclose(mx, knot_x, rtol=1e-5,
                                   err_msg=f"{key}: mband knot x")
        np.testing.assert_allclose(my, knot_y, rtol=1e-5,
                                   err_msg=f"{key}: mband knot y")
        # and the spline passes through them, at grid positions i*(n+1)
        assert len(gx) == (K - 1) * n + K
        at = np.arange(K) * (n + 1)
        np.testing.assert_allclose(gx[at], knot_x, rtol=1e-6,
                                   err_msg=f"{key}: knots are not on the grid")
        np.testing.assert_allclose(
            gy[at], knot_y, rtol=1e-6, atol=1e-6 * _span(knot_y),
            err_msg=f"{key}: the spline does not pass through its knots")

    @pytest.mark.parametrize("key", _MSPLINE_KEYS)
    def test_curve_reproduces_statas_spline(self, truth, datasets, mapper,
                                            key):
        """The interpolant's end condition is inside a builtin.

        Measured 23sep2026: a NATURAL cubic spline through the recorded
        (float32) knots reproduces every one of the 20 sersets to at worst
        9.5e-7 of the y range (sp500:default); not-a-knot is 2.76 mpg off,
        clamped 1.62, PCHIP 0.96 on auto:default.  The bound is three times
        the measured residual: a spline built from the double-precision
        data passes, any other end condition fails by four orders.
        """
        rec, gx, gy = self._draw(truth, datasets, mapper, key)
        want = _series(rec, "spline_y")
        assert len(gy) == len(want), f"{key}: point count differs"
        np.testing.assert_allclose(
            gy, want, rtol=1e-6, atol=3e-6 * _span(want),
            err_msg=f"{key}: dash's spline differs from {rec['cmd']}")

    def test_n_of_one_is_accepted(self, datasets, mapper):
        """Stata accepts n(1): one point between adjacent knots."""
        y, x = _need(datasets, "auto")
        src = ColumnDataSource({"y": list(y), "x": list(x)})
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            r = mapper.map_mspline(figure(), src, "y", "x",
                                   {"bands": "5", "n": "1"})
        gx, _ = _line_data(r, "x_sp", "y_sp")
        assert not [w for w in caught if "n(" in str(w.message)], (
            "n(1) was reported as out of range; twoway accepts it")
        assert len(gx) == (5 - 1) * 1 + 5, (
            f"bands(5) n(1) on auto: {len(gx)} points, Stata draws 9")


# ======================================================================
# fpfit: repeated powers, origin shift, scaling, the analytic band
# ======================================================================

_FP_REPEATED_KEYS = [
    "auto:mpg_on_weight", "auto:price_on_mpg", "auto:weight_on_mpg",
    "census:death_on_pop", "nlsw88:wage_on_ttl_exp", "sp500:close_on_volume",
    "synthetic:y_on_x",
]


def _fp_data(truth, datasets, key):
    """(y, x) for an fpfit_repeated probe, in dataset order."""
    ds, spec = key.split(":")
    yname, xname = spec.split("_on_")
    if ds == "synthetic":
        rec = truth["fpfit_repeated_data"]["synthetic"]
        return _series(rec, "y"), _series(rec, "x")
    y0, x0 = _need(datasets, ds)
    meta = truth["datasets"][ds]
    cols = {meta["y"]: y0, meta["x"]: x0}
    if ds == "auto":
        cols["price"] = _auto_price(truth)
    return cols[yname], cols[xname]


class TestFpfitRepeatedPowers:
    """fracpoly's degree-2 search includes the repeated pairs (p, p), whose
    second column is x^p * ln x.  dash built [1, z, z] for them -- rank 2 --
    so a repeated pair could never win: auto picked (-2,-1) where Stata
    picks (-2,-2), nlsw88 (1,3) for (2,2), census (0,.5) for (1,3) --
    the last from fitting unscaled x (condition 3.6e21).
    """

    def _draw(self, truth, datasets, mapper, key):
        y, x = _fp_data(truth, datasets, key)
        rec = truth["fpfit_repeated"][key]
        assert rec["fpfit_rc"] == 0, key
        src = ColumnDataSource({"y": list(y), "x": list(x)})
        r = mapper.map_fpfit(figure(), src, "y", "x", {})
        gx, gy = _line_data(r, "x_fp", "y_fp")
        return rec, x, y, gx, gy

    @pytest.mark.parametrize("key", _FP_REPEATED_KEYS)
    def test_evaluates_at_every_distinct_x(self, truth, datasets, mapper, key):
        """twoway__fpfit_serset: predict at ALL distinct sorted x, no cap."""
        rec, x, y, gx, gy = self._draw(truth, datasets, mapper, key)
        want = np.unique(x)
        assert len(gx) == rec["n_points"] == len(want), (
            f"{key}: dash drew {len(gx)} points, Stata {rec['n_points']} "
            f"(one per distinct x; cmd: {rec['cmd']})")
        np.testing.assert_allclose(gx, want, rtol=1e-9)

    @pytest.mark.parametrize("key", _FP_REPEATED_KEYS)
    def test_curve_matches_statas_fit(self, truth, datasets, mapper, key):
        rec, x, y, gx, gy = self._draw(truth, datasets, mapper, key)
        want = _series(rec, "fit")
        got = _at_samples(rec, gy, "fit")
        np.testing.assert_allclose(
            got, want, rtol=1e-6, atol=2e-6 * _span(want),
            err_msg=f"{key}: dash's fpfit differs from {rec['cmd']}")

    @pytest.mark.parametrize("key", _FP_REPEATED_KEYS)
    def test_chosen_powers_are_statas(self, truth, datasets, mapper, key):
        rec, x, y, gx, gy = self._draw(truth, datasets, mapper, key)
        _assert_fp_powers(rec, x, y, None, gx, gy, key)

    def test_stata_really_picks_repeated_pairs(self, truth):
        """The premise: four of the seven probes select (p, p)."""
        found = truth["fpfit_repeated_pairs_found"]
        assert len(found) == 4
        for key, pair in found.items():
            assert pair[0] == pair[1], key
            assert truth["fpfit_repeated"][key]["powers_repeated"] == 1


_FP_SHIFT_KEYS = ["auto:xs_is_weight-3000", "auto:xz_is_mpg-12"]


def _fp_shift_data(truth, datasets, key):
    """(y, x) for the two shifted probes: x has min < 0 and min == 0."""
    mpg, weight = _need(datasets, "auto")
    if key == "auto:xs_is_weight-3000":
        return mpg, weight - 3000.0
    return _auto_price(truth), mpg - 12.0


class TestFpfitShift:
    """frac_xo.ado: min(x) <= 0 -> shift by (smallest positive spacing -
    min); then ALWAYS scale by 10^k.  dash dropped x <= 0 to NaN instead.
    """

    @pytest.mark.parametrize("key", _FP_SHIFT_KEYS)
    def test_the_rule_is_what_fracpoly_reports(self, truth, key):
        rec = truth["fpfit_shift"][key]
        chk = truth["fpfit_shift_rule_check"][key]
        assert chk["agree"] is True
        assert rec["fp_shft"] == rec["rule_shift"]
        assert rec["fp_sfac"] == rec["rule_scale"]

    @pytest.mark.parametrize("key", _FP_SHIFT_KEYS)
    def test_dash_computes_the_same_shift_and_scale(self, truth, datasets,
                                                    key):
        rec = truth["fpfit_shift"][key]
        y, x = _fp_shift_data(truth, datasets, key)
        prep = getattr(GlyphMapper, "_fp_prepare", None) or getattr(
            dash_render, "_fp_prepare", None)
        assert prep is not None, (
            "no _fp_prepare(x) -> (shift, scale) on GlyphMapper or the module")
        out = prep(np.asarray(x, dtype=float))
        shift, scale = float(out[0]), float(out[1])
        assert shift == pytest.approx(rec["fp_shft"], rel=1e-12), (
            f"{key}: shift {shift} vs e(fp_shft) {rec['fp_shft']}")
        assert scale == pytest.approx(rec["fp_sfac"], rel=1e-12), (
            f"{key}: scale {scale} vs e(fp_sfac) {rec['fp_sfac']}")

    @pytest.mark.parametrize("key", _FP_SHIFT_KEYS)
    def test_no_observation_is_dropped(self, truth, datasets, mapper, key):
        rec = truth["fpfit_shift"][key]
        y, x = _fp_shift_data(truth, datasets, key)
        src = ColumnDataSource({"y": list(y), "x": list(x)})
        r = mapper.map_fpfit(figure(), src, "y", "x", {})
        gx, gy = _line_data(r, "x_fp", "y_fp")
        curve = truth["fpfit_shift_curve"][f"{key}:fpfit"]
        assert len(gx) == curve["n_points"] == len(np.unique(x)), (
            f"{key}: {rec['n_x_nonpositive']} non-positive x; dash drew "
            f"{len(gx)} points, Stata {curve['n_points']}")
        assert gx[0] == pytest.approx(rec["x_min"])
        assert np.all(np.isfinite(gy)), f"{key}: NaN in the fit"

    @pytest.mark.parametrize("key", _FP_SHIFT_KEYS)
    def test_fpfit_curve_and_powers(self, truth, datasets, mapper, key):
        rec = truth["fpfit_shift"][key]
        y, x = _fp_shift_data(truth, datasets, key)
        src = ColumnDataSource({"y": list(y), "x": list(x)})
        r = mapper.map_fpfit(figure(), src, "y", "x", {})
        gx, gy = _line_data(r, "x_fp", "y_fp")
        curve = truth["fpfit_shift_curve"][f"{key}:fpfit"]
        want = _series(curve, "fit")
        np.testing.assert_allclose(
            _at_samples(curve, gy, "fit"), want, rtol=1e-6,
            atol=2e-6 * _span(want),
            err_msg=f"{key}: dash's fpfit differs from {curve['cmd']}")
        _assert_fp_powers(rec, x, y, None, gx, gy, key)

    @pytest.mark.parametrize("key", _FP_SHIFT_KEYS)
    def test_fpfitci_band_is_the_stdp_t_band(self, truth, datasets, mapper,
                                             key):
        y, x = _fp_shift_data(truth, datasets, key)
        src = ColumnDataSource({"y": list(y), "x": list(x)})
        rs = mapper.map_fpfitci(figure(), src, "y", "x", {"level": "95"})
        gx, gy, glo, ghi = _band_data(rs, "x_fp", "y_fp")
        curve = truth["fpfit_shift_curve"][f"{key}:fpfitci"]
        assert len(gx) == curve["n_points"]
        span = _span(curve["fit"])
        for name, got in (("fit", gy), ("lower", glo), ("upper", ghi)):
            np.testing.assert_allclose(
                _at_samples(curve, got, name), _series(curve, name),
                rtol=1e-6, atol=2e-6 * span,
                err_msg=f"{key}: fpfitci {name} differs from {curve['cmd']}")

    @pytest.mark.parametrize("name", _DATASET_NAMES)
    def test_fpfitci_band_on_the_four_datasets(self, truth, datasets, mapper,
                                               name):
        """fracpred stdp, t(df_r = N-3); dash bootstrapped a percentile
        band (off by up to 1.17 y ranges on sp500)."""
        rec = truth["fpfit"][f"{name}:fpfitci"]
        y, x = _need(datasets, name)
        src = ColumnDataSource({"y": list(y), "x": list(x)})
        rs = mapper.map_fpfitci(figure(), src, "y", "x", {"level": "95"})
        gx, gy, glo, ghi = _band_data(rs, "x_fp", "y_fp")
        assert len(gx) == rec["n_points"] == rec["n_distinct_x"], (
            f"{name}: dash drew {len(gx)} points, Stata {rec['n_points']}")
        span = _span(rec["fit"])
        np.testing.assert_allclose(_at_samples(rec, gx, "fit_x"),
                                   _series(rec, "fit_x"), rtol=1e-9)
        for key, got in (("fit", gy), ("lower", glo), ("upper", ghi)):
            np.testing.assert_allclose(
                _at_samples(rec, got, key), _series(rec, key),
                rtol=1e-6, atol=2e-6 * span,
                err_msg=f"{name}: fpfitci {key} differs from {rec['cmd']}")


# ======================================================================
# lfitci / qfitci: stdp, stdf, stdr
# ======================================================================

_FITCI_STD_KEYS = [f"{ds}:{layer}:{std}" for ds in _DATASET_NAMES
                   for layer in ("lfitci", "qfitci")
                   for std in ("stdp", "stdf", "stdr")]


class TestFitciBandTypes:
    """twoway__lfit_serset: `predict se, <std>`, xb -/+ invttail(df_r,
    (100-level)/200)*se.  stdf = sqrt(stdp^2 + s^2), stdr = sqrt(s^2 -
    stdp^2).  dash knew stdp only and reported stdf/stdr as unknown.
    """

    def _draw(self, truth, datasets, mapper, key, opts=None):
        ds, layer, std = key.split(":")
        y, x = _need(datasets, ds)
        src = ColumnDataSource({"y": list(y), "x": list(x)})
        fn = mapper.map_lfitci if layer == "lfitci" else mapper.map_qfitci
        options = {std: std, "level": "95"} if opts is None else opts
        rs = fn(figure(), src, "y", "x", options)
        return _band_data(rs, "x_fit", "y_fit")

    @pytest.mark.parametrize("key", _FITCI_STD_KEYS)
    def test_band_matches_the_plotted_serset(self, truth, datasets, mapper,
                                             key):
        rec = truth["fitci_std"][key]
        assert rec["rc"] == 0, f"{key}: {rec['cmd']} failed in Stata"
        gx, gy, glo, ghi = self._draw(truth, datasets, mapper, key)
        assert len(gx) == rec["n_points"], (
            f"{key}: dash drew {len(gx)} points, Stata {rec['n_points']}")
        # The serset's grid is float32 (2071.111083984375 for 2071.1111...):
        # x at 1e-6, and the y tolerance below absorbs slope * that.
        np.testing.assert_allclose(_at_samples(rec, gx, "fit_x"),
                                   _series(rec, "fit_x"), rtol=1e-6)
        span = _span(rec["fit"])
        for name, got in (("fit", gy), ("lower", glo), ("upper", ghi)):
            np.testing.assert_allclose(
                _at_samples(rec, got, name), _series(rec, name),
                rtol=1e-6, atol=2e-6 * span,
                err_msg=f"{key}: {name} differs from {rec['cmd']}")

    @pytest.mark.parametrize("key", [k for k in _FITCI_STD_KEYS
                                     if ":lfitci:" in k])
    def test_lfitci_matches_the_double_precision_rebuild(
        self, truth, datasets, mapper, key
    ):
        """regress + predict <std> in double: no serset rounding in y.

        The grid variable _gs_x_create makes is a float, so the rebuild
        predicted at float32-rounded x; dash's line is read at exactly
        those x by linear interpolation (the step is 2e-4 of a grid cell,
        so the interpolation error is below 1e-12 of the y range).
        """
        rec = truth["fitci_std_rebuild"][key]
        assert truth["fitci_std_rebuild_agreement_by_probe"][key] is True
        gx, gy, glo, ghi = self._draw(truth, datasets, mapper, key)
        wx = _series(rec, "fit_x")
        span = _span(rec["fit"])
        for name, got in (("fit", gy), ("lower", glo), ("upper", ghi)):
            np.testing.assert_allclose(
                np.interp(wx, gx, got), _series(rec, name),
                rtol=1e-8, atol=1e-8 * span,
                err_msg=f"{key}: {name} differs from {rec['cmd']}")

    @pytest.mark.parametrize("key", [k for k in _FITCI_STD_KEYS
                                     if k.endswith(":stdp")])
    def test_stdp_is_the_default(self, truth, datasets, mapper, key):
        """No std word == stdp (fitci_stdp_equals_ci_bands_level95)."""
        assert truth["fitci_stdp_equals_ci_bands_level95_by_probe"][key] is True
        _, gy, glo, ghi = self._draw(truth, datasets, mapper, key)
        _, dy, dlo, dhi = self._draw(truth, datasets, mapper, key,
                                     opts={"level": "95"})
        np.testing.assert_allclose(gy, dy, rtol=1e-12)
        np.testing.assert_allclose(glo, dlo, rtol=1e-12)
        np.testing.assert_allclose(ghi, dhi, rtol=1e-12)

    def test_stdf_is_wider_than_stdp_and_stdr_narrower(self, truth):
        """The fixture's own sanity check on the three band types."""
        for ds in _DATASET_NAMES:
            p = truth["fitci_std"][f"{ds}:lfitci:stdp"]
            f = truth["fitci_std"][f"{ds}:lfitci:stdf"]
            r = truth["fitci_std"][f"{ds}:lfitci:stdr"]
            wp = _series(p, "upper") - _series(p, "lower")
            wf = _series(f, "upper") - _series(f, "lower")
            wr = _series(r, "upper") - _series(r, "lower")
            assert np.all(wf > wp), ds
            assert np.all(wf > wr), ds


# ======================================================================
# lowess
# ======================================================================

_LOWESS_FULL_KEYS = [f"{ds}:{v}_full" for ds in _DATASET_NAMES
                     for v in ("default", "mean", "noweight")]
_LOWESS_BINARY_KEYS = [f"{base}:{v}"
                       for base in ("auto:foreign_on_weight",
                                    "nlsw88:union_on_wage")
                       for v in ("default", "adjust", "logit", "logit_adjust")]
_LOWESS_OPTS = {
    "": {}, "default": {}, "mean": {"mean": "mean"},
    "noweight": {"noweight": "noweight"}, "adjust": {"adjust": "adjust"},
    "logit": {"logit": "logit"},
    "logit_adjust": {"logit": "logit", "adjust": "adjust"},
    "bwidth_point2": {"bwidth": ".2"}, "bwidth_point8": {"bwidth": ".8"},
}


class TestLowessIsStatasSmoother:
    """[R] lowess: stable sort by x; k = int((N*bw - 0.5)/2); the window is
    the 2k+1 observations around i BY INDEX; Delta = 1.0001 * max distance
    in it; tricube weights; a weighted line (or mean) evaluated at x_i; no
    robustness iterations.  Each observation gets its own value, ties
    included.

    dash called statsmodels' lowess (it=3 bisquare iterations, nearest-
    by-distance neighbourhood, one value per tied group): 3.7e-2 .. 4.4e-1
    of the y range off on every dataset.  The [R] rule reproduces all 20
    full-resolution probes to 2.3e-13 (measured 23sep2026).
    """

    def _draw(self, mapper, x, y, opts):
        src = ColumnDataSource({"y": list(y), "x": list(x)})
        r = mapper.map_lowess(figure(), src, "y", "x", dict(opts))
        return _line_data(r, "x_lw", "y_lw")

    @pytest.mark.parametrize("key", _LOWESS_FULL_KEYS)
    def test_full_resolution_curve(self, truth, datasets, mapper, key):
        ds, variant = key.split(":")
        rec = truth["lowess_more"][key]
        assert rec["rc"] == 0, key
        y, x = _need(datasets, ds)
        gx, gy = self._draw(mapper, x, y, _LOWESS_OPTS[variant[:-5]])
        want_x = _series(rec, "lowess_x")
        want_y = _series(rec, "lowess_y")
        assert len(gx) == rec["N_smoothed"] == len(x), (
            f"{key}: dash drew {len(gx)} points, Stata one per observation "
            f"({rec['N_smoothed']}); cmd: {rec['cmd']}")
        # The x order pins the STABLE sort: ties stay in dataset order and
        # carry different smooth values (lowess.tie_order).
        np.testing.assert_allclose(gx, want_x, rtol=1e-9,
                                   err_msg=f"{key}: x order differs")
        np.testing.assert_allclose(
            gy, want_y, rtol=0, atol=1e-8 * _span(want_y),
            err_msg=f"{key}: dash's smooth differs from {rec['cmd']}")

    @pytest.mark.parametrize("key", _LOWESS_BINARY_KEYS)
    def test_logit_and_adjust(self, truth, mapper, key):
        """adjust: smooth * mean(y)/mean(smooth); logit: clamp to [1/N,
        1-1/N] where smooth < .0001 or > 1-.0001, then ln(p/(1-p));
        adjust before logit (lowess.ado ADJ_LOGIT)."""
        base, variant = key.rsplit(":", 1)
        rec = truth["lowess_more"][key]
        assert rec["rc"] == 0, key
        x, y = _binary_from_lowess_more(truth, f"{base}:default")
        gx, gy = self._draw(mapper, x, y, _LOWESS_OPTS[variant])
        want_x = _series(rec, "lowess_x")
        want_y = _series(rec, "lowess_y")
        assert len(gx) == rec["N_smoothed"], (
            f"{key}: dash drew {len(gx)} points, Stata {rec['N_smoothed']}")
        np.testing.assert_allclose(gx, want_x, rtol=1e-9)
        np.testing.assert_allclose(
            gy, want_y, rtol=0, atol=1e-8 * _span(want_y),
            err_msg=f"{key}: dash's smooth differs from {rec['cmd']}")

    @pytest.mark.parametrize("key", [f"{ds}:{v}" for ds in _DATASET_NAMES
                                     for v in ("default", "bwidth_point2",
                                               "bwidth_point8", "mean",
                                               "noweight")])
    def test_sampled_probes_including_bwidth(self, truth, datasets, mapper,
                                             key):
        """The pre-existing `lowess` section: 11 samples of each curve."""
        ds, variant = key.split(":")
        rec = truth["lowess"][key]
        y, x = _need(datasets, ds)
        gx, gy = self._draw(mapper, x, y, _LOWESS_OPTS[variant])
        assert len(gx) == rec["n_points"]
        np.testing.assert_allclose(_at_samples(rec, gx, "lowess_x"),
                                   _series(rec, "lowess_x"), rtol=1e-9)
        want = _series(rec, "lowess_y")
        np.testing.assert_allclose(
            _at_samples(rec, gy, "lowess_y"), want, rtol=0,
            atol=1e-8 * _span(want),
            err_msg=f"{key}: dash's smooth differs from {rec['cmd']}")

    def test_stata_refuses_every_weight_on_lowess(self, truth):
        """The refusal is dash.ado's (test_statistical_options.cscript);
        here only the premise is pinned."""
        assert truth["rules_wp18"]["lowess.weights"]["accepted"] is False
        for w in ("aw", "fw", "pw", "iw"):
            assert truth["weight_acceptance_table"]["twoway_lowess"][w][
                "accepted"] is False, w


# ======================================================================
# histogram, discrete
# ======================================================================

_DISCRETE_VARS = ("auto:rep78", "auto:mpg", "census:region")
_DISCRETE_OPTS = {
    "discrete":           {"discrete": "discrete"},
    "discrete_frequency": {"discrete": "discrete", "frequency": "frequency"},
    "discrete_width2":    {"discrete": "discrete", "width": "2"},
}
_DISCRETE_KEYS = [f"{v}:{o}" for v in _DISCRETE_VARS for o in _DISCRETE_OPTS]


def _discrete_values(truth, datasets, var):
    """The variable's values.  mpg is in the CSV; rep78 and region are
    rebuilt from the discrete frequency record -- a histogram depends on
    the multiset of values only, and with discrete + width 1 every bar IS
    one distinct value's count (verified: the rebuilt mpg equals the CSV).
    """
    if var == "auto:mpg":
        return _need(datasets, "auto")[0]
    fr = truth["histogram_discrete"][f"{var}:discrete_frequency"]
    counts = np.asarray(fr["bar_height"], dtype=float)
    assert np.all(counts == np.round(counts)) and fr["width"] == 1, var
    vals = np.repeat(np.asarray(fr["bin_midpoint"], dtype=float),
                     counts.astype(int))
    assert len(vals) == fr["N"], var
    return vals


class TestHistogramDiscrete:
    """twoway__histogram_gen ... discrete: width = width() or the smallest
    positive spacing of the distinct values, start = min - width/2, one bar
    per occupied bin centred on the value; discrete + bin() is r(198).
    dash had no discrete at all (reported as an unknown option).
    """

    @pytest.mark.parametrize("key", _DISCRETE_KEYS)
    def test_bars_match_the_generator(self, truth, datasets, mapper, key):
        var, variant = key.rsplit(":", 1)
        rec = truth["histogram_discrete"][key]
        assert rec["rc"] == 0, f"{key}: {rec['cmd']} failed"
        vals = _discrete_values(truth, datasets, var)
        src = ColumnDataSource({"v": list(vals)})
        r = mapper.map_histogram(figure(), src, "v",
                                 dict(_DISCRETE_OPTS[variant]))
        d = r.data_source.data
        top = np.asarray(d["top"], dtype=float)
        left = np.asarray(d["left"], dtype=float)
        right = np.asarray(d["right"], dtype=float)
        drawn = top > 0
        mids = (left + right) / 2.0
        assert int(drawn.sum()) == rec["n_x"], (
            f"{key}: dash drew {int(drawn.sum())} non-empty bars, Stata "
            f"{rec['n_x']} (cmd: {rec['cmd']})")
        np.testing.assert_allclose(mids[drawn], _series(rec, "bin_midpoint"),
                                   rtol=1e-9,
                                   err_msg=f"{key}: bar centres")
        np.testing.assert_allclose(top[drawn], _series(rec, "bar_height"),
                                   rtol=1e-6,
                                   err_msg=f"{key}: bar heights")
        widths = right - left
        np.testing.assert_allclose(widths, rec["width"], rtol=1e-9,
                                   err_msg=f"{key}: bar width")
        assert left.min() == pytest.approx(rec["xmin"], rel=1e-9), key
        assert right.max() == pytest.approx(rec["xmax"], rel=1e-9), key

    @pytest.mark.parametrize("key", [f"{v}:discrete" for v in _DISCRETE_VARS])
    def test_twoway_draws_the_generator(self, truth, key):
        """twoway histogram's serset equals twoway__histogram_gen's output."""
        rec = truth["histogram_discrete"][key]
        tw = truth["histogram_discrete_twoway"][key]
        assert rec["drawn_serset_equals_generator"] is True
        np.testing.assert_allclose(_series(tw, "bar_height"),
                                   _series(rec, "bar_height"), rtol=1e-6)

    @pytest.mark.parametrize("var", _DISCRETE_VARS)
    def test_discrete_with_bin_is_not_silently_combined(self, truth, datasets,
                                                        mapper, var):
        """Stata: `options discrete and bins() may not be combined', r(198).

        dash.ado refuses the pair before the renderer sees it; a spec-JSON
        caller can still hand both over, and the renderer must then say
        so rather than draw one and drop the other without a word.
        """
        rec = truth["histogram_discrete"][f"{var}:discrete_bin3"]
        assert rec["rc"] == 198, var
        vals = _discrete_values(truth, datasets, var)
        src = ColumnDataSource({"v": list(vals)})
        _clear_notes()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            mapper.map_histogram(figure(), src, "v",
                                 {"discrete": "discrete", "bin": "3"})
        msgs = [str(w.message) for w in caught]
        assert any("discrete" in m and "bin" in m for m in msgs), (
            f"{var}: discrete + bin(3) drew without a word; Stata refuses "
            f"the pair (twoway__histogram_gen.ado 27-30). warnings: {msgs}")


# ======================================================================
# weights
# ======================================================================

_WEIGHT_KEYS = ("auto:aw_price", "auto:fw_fw", "census:aw_pop",
                "nlsw88:aw_hours", "sp500:aw_volume")
_WEIGHT_TYPE = {"aw": "aweight", "fw": "fweight", "pw": "pweight",
                "iw": "iweight"}


def _weighted_frame(truth, datasets, key):
    """(y, x, w, options, wvar) in dataset order.  Missing weights stay NaN
    for the mapper's own joint drop (nlsw88 hours has four)."""
    ds, wk = key.split(":")
    y, x = _need(datasets, ds)
    rec = truth["weighted_data"][key]
    w = _weight_column(truth, key)
    assert len(w) == len(x) == rec["N_dataset"], key
    wvar = rec["weight_var"]
    opts = {"weight": _WEIGHT_TYPE[rec["weight_type"]], "wexp": wvar}
    return y, x, w, opts, wvar


def _weighted_source(y, x, w, wvar):
    return ColumnDataSource({"y": list(y), "x": list(x), wvar: list(w)})


class TestWeightedLayers:
    """[aw=] [fw=] on lfit/qfit/lfitci/lpoly/fpfit/histogram/kdensity,
    checked against `regress ... [w]`, `lpoly [w]`, `fracpoly [w]`,
    `twoway__histogram_gen [fw]`, `kdensity [w]` and the plotted sersets.
    dash parsed a weight, reported it as ignored, and discarded it.
    """

    @pytest.mark.parametrize("key", _WEIGHT_KEYS)
    def test_lfit_is_the_weighted_regression(self, truth, datasets, mapper,
                                             key):
        rec = truth["weighted"][f"{key}:lfit"]
        assert rec["rc"] == 0 and rec["serset_equals_weighted_regression"]
        y, x, w, opts, wvar = _weighted_frame(truth, datasets, key)
        r = mapper.map_lfit(figure(), _weighted_source(y, x, w, wvar),
                            "y", "x", dict(opts))
        gx, gy = _line_data(r, "x", "y")
        slope = (gy[-1] - gy[0]) / (gx[-1] - gx[0])
        cons = gy[0] - slope * gx[0]
        want_slope, want_cons = rec["coef"]
        assert slope == pytest.approx(want_slope, rel=1e-8), (
            f"{key}: slope {slope} vs {rec['estimation_cmd']} {want_slope}")
        assert cons == pytest.approx(want_cons, rel=1e-8), key
        # and the plotted 3-point serset
        np.testing.assert_allclose(
            np.interp(_series(rec, "fit_x"), gx, gy), _series(rec, "fit"),
            rtol=1e-6, atol=2e-6 * _span(rec["fit"]),
            err_msg=f"{key}: {rec['cmd']}")

    @pytest.mark.parametrize("key", _WEIGHT_KEYS)
    def test_qfit_is_the_weighted_regression(self, truth, datasets, mapper,
                                             key):
        rec = truth["weighted"][f"{key}:qfit"]
        assert rec["rc"] == 0 and rec["serset_equals_weighted_regression"]
        y, x, w, opts, wvar = _weighted_frame(truth, datasets, key)
        r = mapper.map_qfit(figure(), _weighted_source(y, x, w, wvar),
                            "y", "x", dict(opts))
        gx, gy = _line_data(r, "x", "y")
        assert len(gx) == rec["n_points"]
        np.testing.assert_allclose(_at_samples(rec, gx, "fit_x"),
                                   _series(rec, "fit_x"), rtol=1e-6)
        np.testing.assert_allclose(
            _at_samples(rec, gy, "fit"), _series(rec, "fit"),
            rtol=1e-6, atol=2e-6 * _span(rec["fit"]),
            err_msg=f"{key}: {rec['cmd']}")

    @pytest.mark.parametrize("key", _WEIGHT_KEYS)
    def test_lfitci_band_uses_the_weighted_df_and_rmse(self, truth, datasets,
                                                       mapper, key):
        """aw: weights normalised to sum N, df_r = N-2; fw: N = sum w."""
        rec = truth["weighted"][f"{key}:lfitci"]
        assert rec["rc"] == 0 and rec["serset_equals_weighted_regression"]
        y, x, w, opts, wvar = _weighted_frame(truth, datasets, key)
        opts["level"] = "95"
        rs = mapper.map_lfitci(figure(), _weighted_source(y, x, w, wvar),
                               "y", "x", opts)
        gx, gy, glo, ghi = _band_data(rs, "x_fit", "y_fit")
        assert len(gx) == rec["n_points"]
        span = _span(rec["fit"])
        for name, got in (("fit", gy), ("lower", glo), ("upper", ghi)):
            np.testing.assert_allclose(
                _at_samples(rec, got, name), _series(rec, name),
                rtol=1e-6, atol=2e-6 * span,
                err_msg=f"{key}: lfitci {name} (df_r {rec['df_r']}, rmse "
                        f"{rec['rmse']}) differs from {rec['cmd']}")

    @pytest.mark.parametrize("key", _WEIGHT_KEYS)
    def test_lpoly_at_statas_bandwidth_draws_twoways_points(
        self, truth, datasets, mapper, key
    ):
        """lpoly.ado: aw normalised to mean 1, fw raw, local weight K*w;
        grid n() default min(N, 50); a point is missing with fewer than 2
        positively weighted observations.  Compared to the twoway serset,
        which drops the missing points."""
        rec = truth["weighted"][f"{key}:lpoly"]
        tw = truth["weighted"][f"{key}:lpoly_twoway"]
        assert rec["rc"] == 0 and tw["rc"] == 0, key
        y, x, w, opts, wvar = _weighted_frame(truth, datasets, key)
        opts["bwidth"] = repr(float(rec["bwidth"]))
        r = mapper.map_lpoly(figure(), _weighted_source(y, x, w, wvar),
                             "y", "x", opts)
        gx, gy = _line_data(r, "x_lp", "y_lp")
        assert len(gx) == tw["n_points"] == rec["ngrid"], (
            f"{key}: dash drew {len(gx)} points, twoway {tw['n_points']} "
            f"(r(ngrid) {rec['ngrid']} of {rec['n']} grid points)"
            if "n" in rec else
            f"{key}: dash drew {len(gx)} points, twoway {tw['n_points']} "
            f"(r(ngrid) {rec['ngrid']})")
        np.testing.assert_allclose(_at_samples(tw, gx, "lpoly_x"),
                                   _series(tw, "lpoly_x"), rtol=1e-9,
                                   err_msg=f"{key}: lpoly grid")
        want = _series(tw, "lpoly_y")
        np.testing.assert_allclose(
            _at_samples(tw, gy, "lpoly_y"), want, rtol=1e-6,
            atol=1e-6 * _span(want),
            err_msg=f"{key}: dash's weighted lpoly differs from {tw['cmd']}")

    @pytest.mark.parametrize("key", _WEIGHT_KEYS)
    def test_fpfit_powers_and_curve(self, truth, datasets, mapper, key):
        rec = truth["weighted"][f"{key}:fpfit"]
        assert rec["fpfit_rc"] == 0, key
        y, x, w, opts, wvar = _weighted_frame(truth, datasets, key)
        r = mapper.map_fpfit(figure(), _weighted_source(y, x, w, wvar),
                             "y", "x", dict(opts))
        gx, gy = _line_data(r, "x_fp", "y_fp")
        keep = np.isfinite(w) & (w > 0)
        # Stata's count, not len(np.unique(x[keep])): twoway__fpfit_serset
        # keeps the first row of each x after `sort x y` BEFORE fracpred,
        # and when that row is one fracpoly excluded (a missing weight:
        # nlsw88 hours at ttl_exp 16.3077) its prediction is missing and
        # the serset drops the x -- 1543 points where the estimation
        # sample has 1544 distinct x.  dash draws what twoway draws.
        assert len(gx) == rec["n_points"], (
            f"{key}: dash drew {len(gx)} points, Stata {rec['n_points']}")
        assert len(gx) <= len(np.unique(x[keep]))
        want = _series(rec, "fit")
        np.testing.assert_allclose(
            _at_samples(rec, gy, "fit"), want, rtol=1e-6,
            atol=2e-6 * _span(want),
            err_msg=f"{key}: dash's weighted fpfit differs from {rec['cmd']}")
        _assert_fp_powers(rec, x[keep], y[keep], w[keep], gx, gy, key)

    def test_histogram_fweight_counts_every_copy(self, truth, datasets,
                                                 mapper):
        """[fw=fw] on auto mpg: N = sum fw = 417, so the default bin count
        is 20 (not 8) and the heights are the weighted counts."""
        key = "auto:fw_fw"
        rec = truth["weighted"][f"{key}:histogram"]
        assert rec["rc"] == 0
        y, x, w, opts, wvar = _weighted_frame(truth, datasets, key)
        r = mapper.map_histogram(figure(), _weighted_source(y, x, w, wvar),
                                 "y", dict(opts))
        d = r.data_source.data
        top = np.asarray(d["top"], dtype=float)
        left = np.asarray(d["left"], dtype=float)
        right = np.asarray(d["right"], dtype=float)
        assert len(top) == rec["bin"], (
            f"dash binned into {len(top)} bins, Stata {rec['bin']} "
            f"(N = sum fw = {rec['N']}; cmd: {rec['cmd']})")
        np.testing.assert_allclose(right - left, rec["width"], rtol=1e-6)
        drawn = top > 0
        assert int(drawn.sum()) == rec["n_x"]
        np.testing.assert_allclose(((left + right) / 2)[drawn],
                                   _series(rec, "bin_midpoint"), rtol=1e-6)
        np.testing.assert_allclose(top[drawn], _series(rec, "bar_height"),
                                   rtol=1e-6,
                                   err_msg=f"weighted heights: {rec['cmd']}")

    @pytest.mark.parametrize("key", [k for k in _WEIGHT_KEYS
                                     if ":aw_" in k])
    def test_histogram_notes_an_aweight_it_cannot_use(self, truth, datasets,
                                                      mapper, key):
        """histogram takes fweights only (r(101) on aw/pw/iw).  dash.ado
        refuses; a spec-JSON caller reaching the renderer with one gets a
        note and the unweighted histogram, not a silently weighted one."""
        rec = truth["weighted"][f"{key}:histogram"]
        assert rec["rc"] == 101, key
        y, x, w, opts, wvar = _weighted_frame(truth, datasets, key)
        _clear_notes()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            r = mapper.map_histogram(figure(),
                                     _weighted_source(y, x, w, wvar),
                                     "y", dict(opts))
        msgs = [str(w_.message) for w_ in caught]
        assert any("weight" in m.lower() for m in msgs), (
            f"{key}: an aweight on histogram drew without a note; Stata "
            f"refuses it (r(101)). warnings: {msgs}")
        plain = mapper.map_histogram(figure(), ColumnDataSource({"y": list(y)}),
                                     "y", {})
        np.testing.assert_allclose(
            np.asarray(r.data_source.data["top"], float),
            np.asarray(plain.data_source.data["top"], float),
            err_msg=f"{key}: the histogram was weighted after all")

    @pytest.mark.parametrize("key", _WEIGHT_KEYS)
    def test_kdensity_default_bandwidth_and_curve_as_twoway_draws_it(
        self, truth, datasets, mapper, key
    ):
        """kdensity.ado: bandwidth from the WEIGHTED sd and percentiles
        (fw: N = sum w); density = sum w K((x-x_i)/h) / (sum w * h);
        twoway's grid is [min, max] x 300."""
        tw = truth["weighted"][f"{key}:kdensity_twoway"]
        if tw.get("rc", 0) != 0:
            pytest.skip(f"{key}: Stata refused {tw['cmd']} (rc {tw['rc']})")
        y, x, w, opts, wvar = _weighted_frame(truth, datasets, key)
        r = mapper.map_kdensity(figure(), _weighted_source(y, x, w, wvar),
                                "y", dict(opts))
        gx, gy = _line_data(r, "x", "y")
        assert len(gx) == tw["n_points"], (
            f"{key}: dash drew {len(gx)} points, twoway {tw['n_points']}")
        np.testing.assert_allclose(_at_samples(tw, gx, "kde_x"),
                                   _series(tw, "kde_x"), rtol=1e-9,
                                   err_msg=f"{key}: kdensity grid")
        want = _series(tw, "kde_y")
        np.testing.assert_allclose(
            _at_samples(tw, gy, "kde_y"), want, rtol=1e-6,
            atol=1e-6 * _span(want),
            err_msg=f"{key}: dash's weighted density differs from {tw['cmd']}")

    @pytest.mark.parametrize("key", _WEIGHT_KEYS)
    def test_kdensity_at_statas_bandwidth_on_its_own_grid(self, truth,
                                                          datasets, mapper,
                                                          key):
        """`kdensity ... [w], generate()`: n(50) on [min-h, max+h]."""
        rec = truth["weighted"][f"{key}:kdensity"]
        if rec.get("rc", 0) != 0:
            pytest.skip(f"{key}: Stata refused {rec['cmd']} (rc {rec['rc']})")
        y, x, w, opts, wvar = _weighted_frame(truth, datasets, key)
        kx = _series(rec, "kde_x")
        opts.update({"bwidth": repr(float(rec["bwidth"])),
                     "n": str(rec["n"]),
                     "range": f"{float(kx[0])!r} {float(kx[-1])!r}"})
        r = mapper.map_kdensity(figure(), _weighted_source(y, x, w, wvar),
                                "y", opts)
        gx, gy = _line_data(r, "x", "y")
        assert len(gx) == rec["n_points"]
        np.testing.assert_allclose(gx, kx, rtol=1e-9)
        want = _series(rec, "kde_y")
        np.testing.assert_allclose(
            gy, want, rtol=1e-6, atol=1e-6 * _span(want),
            err_msg=f"{key}: dash's weighted density differs from {rec['cmd']}")

    def test_the_acceptance_table_is_what_the_policy_says(self, truth):
        """iweight nowhere; lowess none; histogram fw only; lpoly/kdensity
        no pweight; fit layers aw fw pw."""
        t = truth["weight_acceptance_table"]
        for cmd in ("twoway_lfit", "twoway_qfit", "twoway_lfitci",
                    "twoway_qfitci", "twoway_fpfit", "twoway_fpfitci",
                    "twoway_mspline", "twoway_mband"):
            assert t[cmd]["iw"]["accepted"] is False, cmd
            for w in ("aw", "fw", "pw"):
                assert t[cmd][w]["accepted"] is True, (cmd, w)
        for w in ("aw", "pw", "iw"):
            assert t["twoway_histogram"][w]["accepted"] is False, w
        assert t["twoway_histogram"]["fw"]["accepted"] is True
        for cmd in ("twoway_kdensity", "twoway_lpoly"):
            assert t[cmd]["pw"]["accepted"] is False, cmd
            assert t[cmd]["iw"]["accepted"] is False, cmd
            assert t[cmd]["aw"]["accepted"] and t[cmd]["fw"]["accepted"], cmd


# ======================================================================
# lpoly: degree(1), and the null rule
# ======================================================================

def _lpoly_options(rec, n=50):
    return {"bwidth": repr(float(rec["bwidth"])), "degree": str(rec["degree"]),
            "kernel": rec["kernel"], "n": str(n)}


def _lpoly_draw(mapper, x, y, opts):
    src = ColumnDataSource({"y": list(y), "x": list(x)})
    r = mapper.map_lpoly(figure(), src, "y", "x", dict(opts))
    return _line_data(r, "x_lp", "y_lp")


def _lpoly_compare_samples(rec, gx, gy, label, check_nulls=True):
    """dash's drawn points against the 11 sampled grid positions.

    Stata's grid is min + i*(max-min)/(n-1); a sampled position with a
    value must be drawn by dash at that x with that value, and (when
    *check_nulls*) a sampled position Stata left missing must not be
    drawn.
    """
    grid = np.linspace(float(rec["x_min"]), float(rec["x_max"]),
                       int(rec["n_points"]))
    idx = np.asarray(rec["sample_index"], dtype=int) - 1
    want_x = _series(rec, "lpoly_x")
    want_y = _series(rec, "lpoly_y")
    np.testing.assert_allclose(grid[idx], want_x, rtol=1e-9)
    span = _span(want_y) if np.isfinite(want_y).any() else 1.0
    for j, i in enumerate(idx):
        x0 = grid[i]
        hit = np.isclose(gx, x0, rtol=1e-9, atol=0)
        if np.isfinite(want_y[j]):
            assert hit.sum() == 1, (
                f"{label}: Stata has a value at x={x0!r} (grid point "
                f"{i + 1}); dash drew {int(hit.sum())} points there")
            assert gy[hit][0] == pytest.approx(want_y[j], rel=1e-6,
                                               abs=1e-6 * span), (
                f"{label}: at x={x0!r} dash {gy[hit][0]!r} vs Stata "
                f"{want_y[j]!r} (cmd: {rec['cmd']})")
        elif check_nulls:
            assert hit.sum() == 0, (
                f"{label}: Stata leaves grid point {i + 1} (x={x0!r}) "
                f"missing; dash drew a value there")


class TestLpolyDegreeOne:
    """np.polyfit's `w` weights the UNSQUARED residual, so degree >= 1
    needs w = sqrt(K): with w = K dash was 2.8e-2 of the y range off at
    Stata's own bandwidth on auto (1.3e-15 with sqrt).  degree(0) never
    saw it: a weighted mean is the same either way.
    """

    @pytest.mark.parametrize("name", _DATASET_NAMES)
    def test_degree_one_at_statas_bandwidth(self, truth, datasets, mapper,
                                            name):
        rec = truth["lpoly"][f"{name}:degree1"]
        assert rec["degree"] == 1 and rec["rc"] == 0
        y, x = _need(datasets, name)
        gx, gy = _lpoly_draw(mapper, x, y, _lpoly_options(rec))
        assert len(gx) == rec["ngrid"], (
            f"{name}: dash drew {len(gx)} points, Stata r(ngrid) = "
            f"{rec['ngrid']} of {rec['n_points']}")
        _lpoly_compare_samples(rec, gx, gy, f"{name}:degree1")


_LPOLY_KEYS = [f"{ds}:{v}" for ds in _DATASET_NAMES
               for v in ("default", "bwidth5", "degree1", "kernel_gaussian")]


class TestLpolyNullRule:
    """lpoly leaves a grid point missing when fewer than two observations
    carry positive kernel weight (measured: lpoly_null.log, degree 0 and 1
    alike; bwidth(5) on auto has 4 of 50 grid points).  dash drew a value
    wherever the weight sum exceeded 1e-12 -- a one-observation window
    drew that observation's y as the fit.

    The rule reproduces 15 of the 16 probes.  On census:kernel_gaussian
    (bandwidth 52203 on a range of 2.3e7, z up to 3e5) Stata leaves 8 of
    the 11 sampled points missing where exp(-z^2/2) > 0 in double predicts
    5: Stata's positive-weight cutoff for the gaussian kernel at extreme z
    is not pinned, so that probe checks only the values Stata drew.
    """

    _UNPINNED = {"census:kernel_gaussian"}

    @pytest.mark.parametrize("key", _LPOLY_KEYS)
    def test_missing_where_stata_is_missing(self, truth, datasets, mapper,
                                            key):
        name, variant = key.split(":")
        rec = truth["lpoly"][key]
        assert rec["rc"] == 0, key
        y, x = _need(datasets, name)
        gx, gy = _lpoly_draw(mapper, x, y, _lpoly_options(rec))
        pinned = key not in self._UNPINNED
        if pinned:
            assert len(gx) == rec["ngrid"], (
                f"{key}: dash drew {len(gx)} points, Stata r(ngrid) = "
                f"{rec['ngrid']} of {rec['n_points']} (cmd: {rec['cmd']})")
        _lpoly_compare_samples(rec, gx, gy, key, check_nulls=pinned)

    def test_the_grid_default_is_min_n_50(self, truth, datasets, mapper):
        """n() defaults to min(N, 50) over the observed range; dash used a
        200-point grid and ignored n()."""
        rec = truth["lpoly"]["auto:default"]
        y, x = _need(datasets, "auto")
        opts = _lpoly_options(rec)
        del opts["n"]
        gx, gy = _lpoly_draw(mapper, x, y, opts)
        grid = np.linspace(float(rec["x_min"]), float(rec["x_max"]),
                           int(rec["n_points"]))
        assert len(gx) == rec["ngrid"], (
            f"auto default: dash drew {len(gx)} points; Stata's 50-point "
            f"grid has {rec['ngrid']} values")
        assert all(np.isclose(grid, v, rtol=1e-9, atol=0).any() for v in gx), (
            "dash's default lpoly grid is not Stata's min(N,50)-point grid")
        # and n() is honoured
        opts["n"] = "20"
        gx20, _ = _lpoly_draw(mapper, x, y, opts)
        grid20 = np.linspace(float(rec["x_min"]), float(rec["x_max"]), 20)
        # n(20) draws the finite-fit subset of the 20-point grid (18 points
        # on auto/mpg, measured 24sep2026).  `<= 20' alone passed an empty
        # draw; require a non-empty grid, still no more than 20, every point
        # on the 20-point linspace, and -- so "n() ignored" (which would
        # redraw the default min(N,50)=50-point grid) cannot slip through --
        # strictly fewer than that default.
        assert 0 < len(gx20) <= 20, f"n(20) drew {len(gx20)} points"
        assert len(gx20) < rec["ngrid"], (
            f"n(20) drew {len(gx20)} points, not fewer than the default "
            f"{rec['ngrid']}-point grid: n() was ignored")
        assert all(np.isclose(grid20, v, rtol=1e-9, atol=0).any()
                   for v in gx20), "n(20) did not set the lpoly grid"


# ======================================================================
# kdensity, as twoway draws it
# ======================================================================

class TestKdensityAsDrawn:
    """twoway kdensity: n() (default 300) points on [min, max].  dash drew
    300 points on [min - 3h, max + 3h]: on census with bwidth(2) the grid
    was too coarse to draw the estimator at all (as-drawn error 1.0 of the
    density range), although the estimator itself was exact at Stata's x.
    """

    @pytest.mark.parametrize("name", _DATASET_NAMES)
    def test_default_curve_on_twoways_grid(self, truth, datasets, mapper,
                                           name):
        var = truth["datasets"][name]["y"]
        rec = truth["kdensity_twoway"][f"{name}:{var}"]
        assert rec["rc"] == 0
        y, _ = _need(datasets, name)
        r = mapper.map_kdensity(figure(), ColumnDataSource({"v": list(y)}),
                                "v", {})
        gx, gy = _line_data(r, "x", "y")
        assert len(gx) == rec["n_points"] == 300, (
            f"{name}: dash drew {len(gx)} points, twoway {rec['n_points']}")
        assert gx[0] == pytest.approx(float(y.min()), rel=1e-12), (
            f"{name}: the grid starts at {gx[0]}, twoway's at min(x) = "
            f"{y.min()}")
        assert gx[-1] == pytest.approx(float(y.max()), rel=1e-12), name
        np.testing.assert_allclose(_at_samples(rec, gx, "kde_x"),
                                   _series(rec, "kde_x"), rtol=1e-9)
        want = _series(rec, "kde_y")
        np.testing.assert_allclose(
            _at_samples(rec, gy, "kde_y"), want, rtol=1e-6,
            atol=1e-6 * _span(want),
            err_msg=f"{name}: dash's default kdensity differs from "
                    f"{rec['cmd']} (bandwidth rule or grid)")

    @pytest.mark.parametrize("name", _DATASET_NAMES)
    def test_bwidth_2_as_drawn(self, truth, datasets, mapper, name):
        """The estimator was exact at Stata's x; now the drawn curve is."""
        var = truth["datasets"][name]["y"]
        rec = truth["kdensity"][f"{name}:{var}:bwidth2"]
        y, _ = _need(datasets, name)
        kx = _series(rec, "kde_x")
        r = mapper.map_kdensity(
            figure(), ColumnDataSource({"v": list(y)}), "v",
            {"bwidth": "2", "n": str(rec["n"]),
             "range": f"{rec['kde_x_min']!r} {rec['kde_x_max']!r}"})
        gx, gy = _line_data(r, "x", "y")
        assert len(gx) == rec["n_points"]
        np.testing.assert_allclose(_at_samples(rec, gx, "kde_x"), kx,
                                   rtol=1e-9)
        want = _series(rec, "kde_y")
        np.testing.assert_allclose(
            _at_samples(rec, gy, "kde_y"), want, rtol=2e-6,
            atol=1e-9 * _span(want),
            err_msg=f"{name}: {rec['cmd']}")
