"""Weighted markers (WP-31 C9).

The defect (GAPS3 C9): ``dash scatter mpg weight [aw=price]`` drew every
marker at one size and named the weight in the note, where twoway sizes
each marker by its weight.  Measured on StataNow 19.5 from twoway's own SVG
export (test/fixtures/weighted_markers_truth.json, written by
scripts/extract_weighted_markers_truth.do; yxview.class
``_draw_weighted_points``):

* marker i is drawn at ``scale * sqrt(w_i)`` times the marker's own size --
  msize() included (W03: ``msize(huge)`` multiplies) -- where ``scale`` is
  ``1.5 / sqrt(w_min)``, cut to ``10 / sqrt(w_max)`` when the largest would
  pass ``max_wted_symsize`` (10) times the size (W04);
* aweight, fweight and pweight alike (W02);
* a weight at or below zero anywhere makes ``1.5 / sqrt(w_min)`` missing,
  so the cap's scale is used (W05, W06); a negative weight's marker is not
  drawn, a zero or missing weight's is drawn at size zero; no message;
* no positive weight at all: twoway stops, r(198), without a word (W06);
* marker labels (mlabel()) take twoway's labelled path, which draws every
  marker at its own size (W11_mlabel); a point symbol keeps its size;
* every marker type is sized: connected, dot (its marker, not its dot
  rows), dropline, rscatter, rcapsym, rconnected, pcscatter, pccapsym
  (W08-W10); the markerless types take the weight and say nothing (W07).
"""

import json
import os
import re
import sys
import warnings

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, REPO)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from js_runner import requires_node  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

FIXTURE = os.path.join(HERE, "fixtures", "weighted_markers_truth.json")
with open(FIXTURE, encoding="utf-8") as _fh:
    _FIX = json.load(_fh)

MODES = ["saved", "served"]
#: The marker types twoway sizes by the weight (W08-W10).
MARKER_TYPES = ["scatter", "connected", "dot", "dropline", "rscatter",
                "rcapsym", "rconnected", "pcscatter", "pccapsym"]
#: A stroke radius of a marker drawn at size zero in twoway's SVG.
_ZERO_R = 0.25


def _read(name):
    with open(os.path.join(REPO, name), encoding="utf-8") as fh:
        return fh.read()


def _rule(w, cap=10.0):
    """twoway's multiplier, written out here independently of the
    renderer: scale = 1.5/sqrt(min), else max/sqrt(max)."""
    w = np.asarray(w, dtype=float)
    fin = w[np.isfinite(w)]
    wmin, wmax = fin.min(), fin.max()
    scale = 1.5 / np.sqrt(wmin) if wmin > 0 else np.inf
    if scale * np.sqrt(wmax) > cap:
        scale = cap / np.sqrt(wmax)
    out = np.full(len(w), np.nan)
    ok = np.isfinite(w) & (w >= 0)
    out[ok] = scale * np.sqrt(w[ok])
    out[~np.isfinite(w)] = 0.0
    return out


# ---------------------------------------------------------------------------
# The fixture
# ---------------------------------------------------------------------------
class TestTheFixture:
    def test_meta_is_stamped(self):
        meta = _FIX["_meta"]
        assert sorted(meta) == ["born_date", "dash_commit", "extracted",
                                "source", "stata_version"]
        assert meta["source"] == "scripts/extract_weighted_markers_truth.do"
        assert re.fullmatch(r"[0-9a-f]{40}", meta["dash_commit"])

    def test_the_return_codes(self):
        for k, rec in _FIX.items():
            if k in ("_meta", "data"):
                continue
            want = 0
            if k in ("W06_allzero", "W06_allmis", "W06_allneg",
                     "W06_twolayers"):
                want = 198
            elif k.startswith("A5b_lowess") or k in ("A5b_mspline_expr",
                                                    "A5b_mband_expr"):
                want = 101
            elif k.startswith("A5b_lpoly"):
                want = 2000
            elif k.startswith("X_"):
                continue  # test_weight_expressions.TestTheYxviewWeightText
            assert rec["rc"] == want, k

    def test_twoway_says_nothing_of_a_marker_weight(self):
        for k, rec in _FIX.items():
            if k.startswith(("W", "R_")):
                assert rec["lines"] == [], (k, rec["lines"])


# ---------------------------------------------------------------------------
# The rule
# ---------------------------------------------------------------------------
class TestTheRule:
    def test_arithmetic(self):
        got = dr._dash_weighted_sizes([1.0, 4.0, 9.0], 10.0)
        assert np.allclose(got, [15.0, 30.0, 45.0])

    def test_cap(self):
        got = dr._dash_weighted_sizes([1.0, 10000.0], 1.0)
        assert np.allclose(got, [0.1, 10.0])
        got = dr._dash_weighted_sizes([1.0, 10000.0], 1.0, max_mult=5.0)
        assert np.allclose(got, [0.05, 5.0])

    def test_missing(self):
        got = dr._dash_weighted_sizes([np.nan, 4.0, 9.0], 1.0)
        assert np.allclose(got, [0.0, 1.5, 2.25])

    def test_zero_and_negative(self):
        got = dr._dash_weighted_sizes([0.0, 4.0, 100.0], 1.0)
        assert np.allclose(got, [0.0, 2.0, 10.0])
        got = dr._dash_weighted_sizes([-1.0, 4.0, 100.0], 1.0)
        assert np.isnan(got[0]) and np.allclose(got[1:], [2.0, 10.0])

    def test_no_positive_weight_draws_nothing(self):
        for w in ([0.0, 0.0], [np.nan, np.nan], [-1.0, -2.0], []):
            got = dr._dash_weighted_sizes(w, 1.0)
            assert len(got) == len(w) and np.isnan(got).all()

    @pytest.mark.parametrize("probe,col,ref", [
        ("W01", "price", "R_med"), ("W02_pw", "price", "R_med"),
        ("W02_fw", "rep78", "R_med"), ("W03_huge", "price", "R_huge"),
        ("W04_cap", "wbig", "R_med"), ("W05_neg", "wneg", "R_med"),
        ("W06_zero", "wz", "R_med"), ("W06_mis", "wmis", "R_med")])
    def test_matches_twoway(self, probe, col, ref):
        d = _FIX["data"]
        price = np.array(d["price"], dtype=float)
        rep = np.array([np.nan if v is None else v for v in d["rep78"]])
        cols = {"price": price, "rep78": rep,
                "wbig": np.where(np.arange(8) == 0, 10000.0, 1.0),
                "wz": np.where(np.arange(8) == 0, 0.0, price),
                "wmis": np.where(np.arange(8) == 0, np.nan, price),
                "wneg": np.where(np.arange(8) == 0, -1.0, price)}
        base = _FIX[ref]["radii"][0]
        got = dr._dash_weighted_sizes(cols[col], base)
        drawn = [g for g in got if not np.isnan(g)]
        radii = _FIX[probe]["radii"]
        assert len(drawn) == len(radii)
        for g, r in zip(drawn, radii):
            if r == _ZERO_R:
                assert g == 0.0
            else:
                assert abs(g - r) <= 0.02 * r, (probe, g, r)


# ---------------------------------------------------------------------------
# The renderers
# ---------------------------------------------------------------------------
def _figs(mode, spec):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if mode == "saved":
            r, _ = tp._standalone(spec)
            return list(r.figures.values()), r
        doc, _ = tp._served(spec)
    from bokeh.models import Plot
    return [m for root in doc.roots for m in root.select({"type": Plot})], doc


def _markers(figs):
    """Every marker renderer drawn from the data: Scatter glyphs, without
    dot rows and colorvar swatches."""
    out = []
    for f in figs:
        for r in f.renderers:
            g = getattr(r, "glyph", None)
            if type(g).__name__ != "Scatter":
                continue
            if "dash_dots" in (r.tags or []) or dr._dash_is_swatch(r):
                continue
            out.append(r)
    return out


def _sizes(r):
    s = r.glyph.size
    if isinstance(s, str):
        return np.asarray(r.data_source.data[s], dtype=float)
    return None


def _wspec(ptype, wt="aweight", wexp="price", filt="", **o):
    opts = dict(o)
    if wt:
        opts.update(weight=wt, wexp=wexp)
    return tp._spec([plot_for(ptype, opts)],
                    {"filter": filt} if filt else None)


def _base(mode, ptype, **o):
    """The marker size the unweighted layer draws."""
    figs, _ = _figs(mode, _wspec(ptype, wt="", **o))
    sizes = {float(r.glyph.size) for r in _markers(figs)}
    assert len(sizes) == 1, sizes
    return sizes.pop()


def _want(base, w):
    return np.sort(base * _rule(w))


@pytest.mark.parametrize("mode", MODES)
class TestScatter:
    def test_size_field(self, mode):
        figs, _ = _figs(mode, _wspec("scatter"))
        (r,) = _markers(figs)
        got = _sizes(r)
        assert got is not None, "the marker size is one number"
        want = _want(_base(mode, "scatter"), tp._DF["price"])
        assert np.allclose(np.sort(got), want)

    def test_every_weight_type(self, mode):
        base = _base(mode, "scatter")
        for wt in ("fweight", "pweight"):
            figs, _ = _figs(mode, _wspec("scatter", wt=wt, wexp="rep"))
            (r,) = _markers(figs)
            assert np.allclose(np.sort(_sizes(r)),
                               _want(base, tp._DF["rep"])), wt

    def test_brushed_copies_carry_the_size(self, mode):
        figs, _ = _figs(mode, _wspec("scatter"))
        (r,) = _markers(figs)
        for attr in ("nonselection_glyph", "muted_glyph"):
            g = getattr(r, attr)
            if g is None or g == "auto":
                continue
            assert g.size == r.glyph.size, attr

    def test_msize_rule(self, mode):
        """W03: msize() is the size the weight multiplies."""
        figs, _ = _figs(mode, _wspec("scatter", msize="huge"))
        (r,) = _markers(figs)
        want = _want(_base(mode, "scatter", msize="huge"), tp._DF["price"])
        assert np.allclose(np.sort(_sizes(r)), want)

    def test_marker_labels_keep_one_size(self, mode):
        """W11_mlabel: twoway's labelled path draws no weighted marker."""
        figs, _ = _figs(mode, _wspec("scatter", mlabel="rep"))
        (r,) = _markers(figs)
        assert _sizes(r) is None

    def test_a_point_keeps_its_size(self, mode):
        """W11_point: a point is drawn at its size whatever the weight."""
        figs, _ = _figs(mode, _wspec("scatter", msymbol="p"))
        (r,) = _markers(figs)
        assert _sizes(r) is None


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("ptype", MARKER_TYPES[1:])
class TestEveryMarkerType:
    def test_sized(self, mode, ptype):
        figs, _ = _figs(mode, _wspec(ptype))
        rs = _markers(figs)
        assert rs
        base = _base(mode, ptype)
        want = _want(base, tp._DF["price"])
        for r in rs:
            got = _sizes(r)
            assert got is not None, (ptype, "one size")
            # Both ends in one renderer: each row's weight twice.
            w = (np.sort(np.concatenate([want, want]))
                 if len(got) == 2 * len(want) else want)
            assert np.allclose(np.sort(got), w), ptype
        if ptype in ("rscatter", "rcapsym", "rconnected", "pcscatter",
                     "pccapsym"):
            assert sum(len(_sizes(r)) for r in rs) == 2 * len(tp._DF)


@pytest.mark.parametrize("mode", MODES)
class TestBadWeights:
    def _drawn(self, mode, w):
        df = tp._DF.copy()
        old = tp._DF
        tp._DF = df.assign(wt=w)
        try:
            figs, _ = _figs(mode, _wspec("scatter", wexp="wt"))
        finally:
            tp._DF = old
        (r,) = _markers(figs)
        return _sizes(r)

    def test_negative(self, mode):
        w = list(tp._DF["price"])
        w[0] = -1.0
        got = self._drawn(mode, w)
        assert np.isnan(got).sum() == 1
        base = _base(mode, "scatter")
        assert np.allclose(np.sort(got[~np.isnan(got)]),
                           np.sort(base * _rule(w)[1:]))

    def test_missing(self, mode):
        w = list(tp._DF["price"])
        w[0] = np.nan
        got = self._drawn(mode, w)
        assert len(got) == len(w) and (got == 0.0).sum() == 1

    def test_zero(self, mode):
        w = list(tp._DF["price"])
        w[0] = 0.0
        got = self._drawn(mode, w)
        base = _base(mode, "scatter")
        assert np.allclose(np.sort(got), np.sort(base * _rule(w)))
        assert got.max() == pytest.approx(10.0 * base)

    def test_none_positive(self, mode):
        got = self._drawn(mode, [0.0] * len(tp._DF))
        assert np.isnan(got).all()


@pytest.mark.parametrize("mode", MODES)
class TestTheMarkerlessTypes:
    @pytest.mark.parametrize("ptype", ["line", "area", "bar", "spike",
                                       "rspike", "rcap", "rline", "rarea",
                                       "rbar", "pcspike", "pcarrow"])
    def test_nothing_sized_nothing_said(self, mode, ptype):
        spec = _wspec(ptype)
        if mode == "saved":
            r, said = tp._standalone(spec)
            figs = list(r.figures.values())
        else:
            doc, said = tp._served(spec)
            from bokeh.models import Plot
            figs = [m for root in doc.roots
                    for m in root.select({"type": Plot})]
        assert not [s for s in said if "weight" in s.lower()], said
        for f in figs:
            for r in f.renderers:
                src = getattr(r, "data_source", None)
                if src is not None:
                    assert not [c for c in src.data
                                if c.startswith("__dash_wsize")]


class TestAfterAMove:
    _FILT = "foreign, type(dropdown)"

    def test_served(self):
        """The served app sizes the markers from the rows a move keeps."""
        doc, _ = tp._served(_wspec("scatter", filt=self._FILT))
        from bokeh.models import Plot, Select
        ws = [w for w in tp._widgets_of(doc) if isinstance(w, Select)]
        raw = [v for v, lab in ws[0].options if lab == "Foreign"]
        tp._fire(ws[0], raw[0])
        figs = [m for root in doc.roots for m in root.select({"type": Plot})]
        (r,) = _markers(figs)
        kept = tp._DF.loc[tp._DF["foreign"] == 1, "price"]
        want = _want(_base("served", "scatter"), kept)
        assert np.allclose(np.sort(_sizes(r)), want)

    def test_saved_is_marked(self):
        """M8: until the saved page recomputes the sizes (S52), a move that
        removes a row marks the layer with the stale cue."""
        r, _ = tp._standalone(_wspec("scatter", filt=self._FILT))
        (mk,) = _markers(r.figures.values())
        tag = getattr(mk, "_dash_frozen", None)
        assert tag is not None
        assert tag["kind"] == "fit" and tag["wvar"] == "price"
        assert tag["wrule"] == "any"
        reg = r._collect_frozen_layers()
        assert any(mk in rends for groups in reg.values()
                   for _t, rends in groups)

    @requires_node
    def test_saved_page_shows_the_cue(self):
        """Under node, the page's own script: a move that removes rows
        dims the weighted markers and shows the caption; moving back to
        every row clears it."""
        import test_saved_stale_cue as sc
        from test_saved_filter_layers import _render
        r = _render(_wspec("scatter", filt=self._FILT))
        sc._assert_clear(r)
        sc._act(r, ("Select", "Foreign"))
        sc._assert_marked(r)
        sc._back(r, "Select")
        sc._assert_clear(r)

    @pytest.mark.xfail(strict=True,
                       reason="fixed in S52 (batch 17), DECISIONS A23")
    def test_saved(self):
        """The saved page recomputes the size column from the kept rows."""
        assert "__dash_wsize" in dr._FILTER_JS


class TestTheAdoText:
    def test_lists(self):
        ado = _read("dash.ado")
        m = re.search(r'local _wt_markers "([^"]*)"', ado)
        assert m and m.group(1).split() == MARKER_TYPES
        m = re.search(r'local _wt_honoured "([^"]*)"', ado)
        assert m and m.group(1).split() == [
            "lfit", "qfit", "lfitci", "qfitci", "lpoly", "lpolyci", "fpfit",
            "fpfitci", "histogram", "kdensity", "mspline", "mband",
            "`_wt_markers'"]
        assert "_seg_wtok" not in ado
        for t in MARKER_TYPES:
            assert dr._DASH_WEIGHT_ACCEPTS[t] == ("aw", "fw", "pw"), t


class TestTheServedCopy:
    def test_name(self, tmp_path):
        _, sp, dp = tp._write(_wspec("scatter"))
        ap = os.path.join(str(tmp_path), "app.py")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(ap)
        with open(ap, encoding="utf-8") as fh:
            assert "def _dash_weighted_sizes(" in fh.read()


class TestScheme:
    def test_max_wted_symsize(self, tmp_path, monkeypatch):
        assert dr.SchemeParser("s2color").max_wted_symsize == 10.0
        from test_scheme_review_fixes import _user_scheme
        _user_scheme(tmp_path, monkeypatch, "wcap.scheme",
                     ["#include s2color", "numstyle max_wted_symsize 5"])
        assert dr.SchemeParser("wcap").max_wted_symsize == 5.0
