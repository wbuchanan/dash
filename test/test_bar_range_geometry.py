"""
test_bar_range_geometry.py -- bar widths and range caps as twoway draws
them, in both renderers, before and after a filter move (WP-30 P1.17a).

The defect (measured at 10f1c58): ``dash bar y x`` and ``dash rbar lo hi x``
drew each bar 0.8 times the smallest gap between the x values (56 on the
parity frame's weights, 168 after a move to the Foreign cars); rbar ignored
``barwidth()``; on a ``%td`` axis a weekly bar was 5.6 days wide and
``barwidth(3)`` drew 3 milliseconds; rcap's caps were 0.2 times the gap in
data units whatever ``msize()`` said; rcapsym drew two cap lines twoway does
not draw and fixed 7-pixel markers.

twoway (StataNow 19.5, scripts/extract_bar_geometry_truth.do, fixture
test/fixtures/bar_geometry_truth.json):

    bar / rbar .plot1.bar_size     1 at x spacing .1, 1, 5 and uneven
    rbar barwidth(.3)              .3
    %td bar, barwidth(3)           1 day, 3 days
    %tm bar, barwidth(.5)          1 month, half a month
    rcap cap / min(W,H) * 100      the msize in Stata units (1.53 medium,
                                   2.43 large), at any x spacing
    rcapsym                        0 cap lines, 5 spines, 10 markers

Probe: ``DASH_REPO=<repo> scripts/stata_slot.sh <scratch>
scripts/extract_bar_geometry_truth.do``.
"""
import json
import math
import os
import sys
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure as bk_figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
import test_saved_filter_layers as tsfl  # noqa: E402
from conftest import make_data_json, load_app  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "bar_geometry_truth.json")
with open(_FIXTURE, encoding="utf-8") as _fh:
    _T = json.load(_fh)

_MODES = ("saved", "served")
_DAY = 86_400_000.0
_DROPDOWN = "foreign, type(dropdown)"

#: The fixture's x columns, as typed in the extractor.
_X = {"s1": [1.0, 2, 3, 4, 5], "s01": [.1, .2, .3, .4, .5],
      "s5": [5.0, 10, 15, 20, 25], "su": [1.0, 1.5, 4, 10, 11]}
_Y = [3.0, 4, 2, 5, 1]
_LO = [1.0, 2, 1, 3, 0]
_HI = [4.0, 5, 3, 6, 2]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

from conftest import render_models  # noqa: E402


def _spec(plots, formats=None, bo=None):
    b = {"formats": dict(formats or {})}
    b.update(bo or {})
    return tp._spec(plots, b)


def _write(tmp_path, spec, df):
    sp = os.path.join(str(tmp_path), "spec.json")
    dp = os.path.join(str(tmp_path), "data.json")
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    with open(dp, "w", encoding="utf-8") as fh:
        json.dump(make_data_json(df), fh)
    return sp, dp


_N = [0]


def _frac_units(ms, kind):
    """Epoch ms in fractional period units: the period it falls in plus
    its share of it (the inverse of _dash_units_to_axis)."""
    p = np.asarray(dr._dash_date_units(ms, kind), dtype=float)
    a = dr._dash_units_to_axis(p, kind)
    b = dr._dash_units_to_axis(p + 1.0, kind)
    return p + (np.asarray(ms, dtype=float) - a) / (b - a)


def _figs(mode, tmp_path, spec, df):
    """(figures, notes) of *spec* over *df* in *mode*.  A served app is
    imported outside the warning capture."""
    sp, dp = _write(tmp_path, spec, df)
    if mode == "saved":
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            r = dr.DashRenderer(sp, dp, os.path.join(str(tmp_path), "o.html"))
            render_models(r)
        return list(r.figures.values()), [str(w.message) for w in caught]
    _N[0] += 1
    ap = os.path.join(str(tmp_path), "app_%d.py" % _N[0])
    with warnings.catch_warnings(record=True) as built:
        warnings.simplefilter("always")
        dr.ServerAppBuilder(sp, dp).build(ap)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mod = load_app(ap, "_bg_app_%d" % _N[0])
    # The import's own render fills the global document; clear it so a
    # loop of builds stays as fast as one.
    from bokeh.io import curdoc
    curdoc().clear()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        doc = Document()
        mod.make_document(doc)
    figs = [m for m in tp._walk_models(doc) if type(m).__name__ == "figure"]
    return figs, [str(w.message) for w in list(built) + list(caught)]


def _glyphs(figs, name):
    return [r for f in figs for r in f.renderers
            if type(getattr(r, "glyph", None)).__name__ == name]


def _vbar(figs):
    [r] = _glyphs(figs, "VBar")
    return r


def _frame(xs, extra=None):
    d = {"x": list(xs), "y": _Y[:len(xs)], "lo": _LO[:len(xs)],
         "hi": _HI[:len(xs)]}
    d.update(extra or {})
    return pd.DataFrame(d)


def _bar(t, xvar="x", **o):
    if t == "bar":
        return {"type": "bar", "yvar": "y", "xvar": xvar, "options": o}
    return {"type": t, "yvar1": "lo", "yvar2": "hi", "xvar": xvar,
            "options": o}


def _gm(date_vars=None, scheme="s2color"):
    gm = dr.GlyphMapper(scheme=dr.SchemeParser(scheme))
    gm.date_vars = dict(date_vars or {})
    return gm


def _width_value(r):
    w = r.glyph.width
    return float(getattr(w, "value", w))


def _caps(figs):
    return [r for f in figs for r in f.renderers
            if "dash_cap" in (getattr(r, "tags", None) or [])]


def _scatter_size(mode, tmp_path, msize=None, scheme_df=None):
    o = {"msize": msize} if msize is not None else {}
    figs, _ = _figs(mode, tmp_path, _spec([{"type": "scatter", "yvar": "y",
                                            "xvar": "x", "options": o}]),
                    _frame(_X["s1"]))
    [s] = _glyphs(figs, "Scatter")
    return float(s.glyph.size)


# ---------------------------------------------------------------------------
# The fixture
# ---------------------------------------------------------------------------

class TestTheFixture:

    def test_meta_is_stamped(self):
        assert sorted(_T["_meta"]) == ["born_date", "dash_commit",
                                       "extracted", "stata_version"]
        assert all(_T["_meta"][k] for k in _T["_meta"])

    def test_every_case_was_measured(self):
        assert set(_T["widths"]) >= {
            "bar_s1", "bar_s01", "bar_s5", "bar_su", "rbar_s1", "rbar_s5",
            "rbar_bw03", "bar_td_weekly", "bar_td_weekly_bw3",
            "bar_td_daily", "bar_tm", "bar_tm_bw05", "rbar_tm"}
        assert set(_T["caps"]) >= {
            "rcap_%s" % m for m in ("default", "tiny", "small", "medium",
                                    "large", "vlarge", "n2", "x2", "s5",
                                    "wide", "stcolor")}
        assert set(_T["rcapsym"]) == {"default", "stcolor"}
        assert _T["refusals"]["rcap"]["rc"] == 198
        assert _T["refusals"]["rcapsym"]["message"] == \
            "option barwidth() not allowed"
        assert _T["refusals"]["rcap_barw"]["message"] == \
            "option barw() not allowed"
        for t in ("spike", "dropline", "area"):
            assert _T["refusals"][t]["rc"] == 0
        for k, v in _T["widths"].items():
            if v["svg_width_x_units"] is not None:
                assert v["svg_width_x_units"] == pytest.approx(
                    v["bar_size"], rel=1e-3), k


# ---------------------------------------------------------------------------
# Widths
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", _MODES)
class TestBarIsOneXUnit:

    def test_the_width_is_twoways(self, mode, tmp_path):
        bad = []
        for t in ("bar", "rbar"):
            for case in ("s1", "s01", "s5", "su"):
                key = "%s_%s" % (t, case)
                want = _T["widths"].get(
                    key, _T["widths"]["bar_" + case])["bar_size"]
                figs, _ = _figs(mode, tmp_path, _spec([_bar(t)]),
                                _frame(_X[case]))
                got = _width_value(_vbar(figs))
                if got != pytest.approx(want, abs=1e-9):
                    bad.append((key, got, want))
        assert not bad, bad


@pytest.mark.parametrize("mode", _MODES)
class TestRbarReadsBarwidth:

    def test_the_option_is_drawn(self, mode, tmp_path):
        want = _T["widths"]["rbar_bw03"]["bar_size"]
        for key in ("barwidth", "width"):
            figs, _ = _figs(mode, tmp_path,
                            _spec([_bar("rbar", **{key: ".3"})]),
                            _frame(_X["s1"]))
            assert _width_value(_vbar(figs)) == pytest.approx(want), key

    def test_no_note(self, mode, tmp_path):
        _, notes = _figs(mode, tmp_path,
                         _spec([_bar("rbar", barwidth=".3")]),
                         _frame(_X["s1"]))
        assert not [n for n in notes if "barwidth" in n], notes


class TestTheBarExtent:

    def test_each_kind(self):
        ms = np.array([dr._STATA_EPOCH_UNIX_MS + 14977 * _DAY])
        assert _gm()._bar_extent("x", [1.0], 2.0) == ("x", 2.0, {})
        assert _gm({"x": "td"})._bar_extent("x", ms, 3.0) == \
            ("x", 3 * _DAY, {})
        for k in ("tc", "tC"):
            assert _gm({"x": k})._bar_extent("x", ms, 5.0) == ("x", 5.0, {})
        for k in ("tw", "tm", "tq", "th", "ty"):
            gm = _gm({"x": k})
            xf, wf, cols = gm._bar_extent("x", ms, 1.0)
            assert (xf, wf) == (gm._BAR_XC, gm._BAR_W) == \
                ("__dash_bar_xc", "__dash_bar_w")
            u = dr._dash_date_units(ms, k)
            lo = dr._dash_units_to_axis(u - .5, k)
            hi = dr._dash_units_to_axis(u + .5, k)
            assert cols["__dash_bar_xc"] == pytest.approx((lo + hi) / 2)
            assert cols["__dash_bar_w"] == pytest.approx(hi - lo)

    def test_an_empty_column(self):
        gm = _gm({"x": "tm"})
        xf, wf, cols = gm._bar_extent("x", np.array([], dtype=float), 1.0)
        assert (xf, wf) == ("__dash_bar_xc", "__dash_bar_w")
        assert all(len(v) == 0 for v in cols.values())

    def test_a_width_past_statas_dates_stays_finite(self):
        ms = np.array([dr._STATA_EPOCH_UNIX_MS + 14977 * _DAY])
        _, w, _ = _gm({"x": "td"})._bar_extent("x", ms, 1e305)
        assert math.isfinite(w) and w > 0
        _, _, cols = _gm({"x": "tm"})._bar_extent("x", ms, 1e9)
        assert np.all(np.isfinite(cols["__dash_bar_w"]))
        assert np.all(np.isfinite(cols["__dash_bar_xc"]))


class TestBarwidthOnADateAxis:

    @pytest.mark.parametrize("mode", _MODES)
    def test_td_default_is_a_day(self, mode, tmp_path):
        df = _frame([14975.0 + 7 * k for k in range(5)])
        figs, _ = _figs(mode, tmp_path, _spec([_bar("bar")], {"x": "%td"}),
                        df)
        want = _T["widths"]["bar_td_weekly"]["bar_size"]
        assert _width_value(_vbar(figs)) == pytest.approx(want * _DAY)

    @pytest.mark.parametrize("mode", _MODES)
    def test_td_barwidth_is_days(self, mode, tmp_path):
        df = _frame([14975.0 + 7 * k for k in range(5)])
        figs, _ = _figs(mode, tmp_path,
                        _spec([_bar("bar", barwidth="3")], {"x": "%td"}), df)
        want = _T["widths"]["bar_td_weekly_bw3"]["bar_size"]
        assert _width_value(_vbar(figs)) == pytest.approx(want * _DAY)

    @pytest.mark.parametrize("mode", _MODES)
    def test_tc_is_a_millisecond(self, mode, tmp_path):
        df = _frame([1.3e12 + 60000.0 * k for k in range(5)])
        figs, _ = _figs(mode, tmp_path, _spec([_bar("bar")], {"x": "%tc"}),
                        df)
        assert _width_value(_vbar(figs)) == pytest.approx(1.0)

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_period_bar_spans_its_period(self, mode, tmp_path):
        for kind, base in (("tw", 2080.0), ("tm", 720.0), ("tq", 160.0),
                           ("th", 80.0), ("ty", 2000.0)):
            self._one_period(mode, kind, base, tmp_path)

    @staticmethod
    def _one_period(mode, kind, base, tmp_path):
        df = _frame([base + k for k in range(5)])
        figs, _ = _figs(mode, tmp_path,
                        _spec([_bar("bar")], {"x": "%" + kind}), df)
        r = _vbar(figs)
        assert getattr(r.glyph.x, "field", r.glyph.x) == "__dash_bar_xc"
        d = r.data_source.data
        u = np.array([base + k for k in range(5)])
        lo = dr._dash_units_to_axis(u - .5, kind)
        hi = dr._dash_units_to_axis(u + .5, kind)
        assert np.asarray(d["__dash_bar_w"], dtype=float) == \
            pytest.approx(hi - lo, abs=1.0)
        assert np.asarray(d["__dash_bar_xc"], dtype=float) == \
            pytest.approx((lo + hi) / 2, abs=1.0)
        if kind == "tm":
            # One month per bar: twoway's bar_size on %tm.
            back = _frac_units(hi, kind) - _frac_units(lo, kind)
            assert back == pytest.approx(
                [_T["widths"]["bar_tm"]["bar_size"]] * 5, abs=1e-6)

    @pytest.mark.parametrize("mode", _MODES)
    def test_rbar_on_a_period_axis(self, mode, tmp_path):
        df = _frame([720.0 + k for k in range(5)])
        figs, _ = _figs(mode, tmp_path,
                        _spec([_bar("rbar", barwidth=".5")], {"x": "%tm"}),
                        df)
        d = _vbar(figs).data_source.data
        u = np.array([720.0 + k for k in range(5)])
        lo = dr._dash_units_to_axis(u - .25, "tm")
        hi = dr._dash_units_to_axis(u + .25, "tm")
        assert np.asarray(d["__dash_bar_w"], dtype=float) == \
            pytest.approx(hi - lo, abs=1.0)
        xc = np.asarray(d["__dash_bar_xc"], dtype=float)
        w = np.asarray(d["__dash_bar_w"], dtype=float)
        assert _frac_units(xc + w / 2, "tm") - _frac_units(xc - w / 2, "tm") \
            == pytest.approx([_T["widths"]["bar_tm_bw05"]["bar_size"]] * 5,
                             abs=1e-6)

    def test_an_empty_period_layer_keeps_the_field_form(self):
        gm = _gm({"x": "tm"})
        src = ColumnDataSource({"x": [], "y": []})
        r = gm.map_bar(bk_figure(), src, "y", "x", {})
        r = r[0] if isinstance(r, list) else r
        assert getattr(r.glyph.x, "field", r.glyph.x) in (
            "__dash_bar_xc", {"field": "__dash_bar_xc"})
        assert getattr(r.glyph.width, "field", r.glyph.width) in (
            "__dash_bar_w", {"field": "__dash_bar_w"})
        assert len(r.data_source.data["__dash_bar_xc"]) == 0


# ---------------------------------------------------------------------------
# Moves
# ---------------------------------------------------------------------------

class TestTheWidthHoldsAcrossAMove:

    def test_saved(self):
        for t in ("bar", "rbar"):
            r = tsfl._render(tp._spec([plot_for(t)], {"filter": _DROPDOWN}))
            [bar] = _glyphs(r.figures.values(), "VBar")
            assert _width_value(bar) == pytest.approx(1.0), t
            tsfl._move(r, tsfl._MOVES[0][2])
            assert _width_value(bar) == pytest.approx(1.0), t

    def test_served(self):
        for t in ("bar", "rbar"):
            spec = tp._spec([plot_for(t)], {"filter": _DROPDOWN})
            figs, _ = tp._served_after_move(spec, ("Select", "Foreign"))
            widths = [g["coords"].get("width") for f in figs
                      for g in f["glyphs"] if g["type"] == "VBar"]
            assert widths == [("value", 1.0)], (t, widths)

    def test_a_period_bar_after_a_saved_move(self):
        df = tp._DF.assign(m=[720.0 + k for k in range(10)])
        spec = tp._spec([{"type": "bar", "yvar": "mpg", "xvar": "m",
                          "options": {}}],
                        {"filter": _DROPDOWN, "formats": {"m": "%tm"}})
        r = tsfl._render(spec, df)
        [bar] = _glyphs(r.figures.values(), "VBar")
        before = [float(w) for w in bar.data_source.data["__dash_bar_w"]]
        tsfl._move(r, tsfl._MOVES[0][2])
        d = bar.data_source.data
        kept = [i for i, f in enumerate(tp._DF["foreign"]) if f == 1]
        assert [float(w) for w in d["__dash_bar_w"]] == pytest.approx(
            [before[i] for i in kept])


# ---------------------------------------------------------------------------
# Caps
# ---------------------------------------------------------------------------

# One of each form resolve_size reads: a keyword, a number, a multiplier
# (the keyword ladder itself is test_size_units.py's).
_MSIZES = ["small", "2", "*2"]


class TestRcapCapsAreScreenUnits:

    @pytest.mark.parametrize("mode", _MODES)
    def test_caps_are_dash_markers(self, mode, tmp_path):
        figs, _ = _figs(mode, tmp_path, _spec([_bar("rcap")]),
                        _frame(_X["s1"]))
        caps = _caps(figs)
        assert len(caps) == 2
        for c in caps:
            assert type(c.glyph).__name__ == "Scatter"
            assert c.glyph.marker == "dash"
            assert c.glyph.angle == 0
            assert c.glyph.line_cap == "round"

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_cap_is_a_marker_of_its_msize(self, mode, tmp_path):
        for m in _MSIZES:
            figs, _ = _figs(mode, tmp_path, _spec([_bar("rcap", msize=m)]),
                            _frame(_X["s1"]))
            want = _scatter_size(mode, tmp_path, m)
            for c in _caps(figs):
                assert float(c.glyph.size) == pytest.approx(want), m
            assert len(_caps(figs)) == 2, m

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_default_is_the_schemes_symbol_size(self, mode, tmp_path):
        for scheme in ("s2color", "stcolor"):
            spec = _spec([_bar("rcap")])
            spec["graphs"][0]["graph_options"]["scheme"] = scheme
            figs, _ = _figs(mode, tmp_path, spec, _frame(_X["s1"]))
            want = dr.SchemeParser(scheme).default_marker_size(0)
            caps = _caps(figs)
            assert caps and all(float(c.glyph.size) == pytest.approx(want)
                                for c in caps), scheme

    def test_the_cap_does_not_follow_the_x_spacing(self, tmp_path):
        sizes = []
        for case in ("s1", "s5", "s01"):
            d = tmp_path / case
            d.mkdir()
            figs, _ = _figs("saved", d, _spec([_bar("rcap")]),
                            _frame(_X[case]))
            sizes.append({float(c.glyph.size) for c in _caps(figs)})
        assert sizes[0] == sizes[1] == sizes[2] and len(sizes[0]) == 1

    def test_the_caps_are_unchanged_by_a_move(self):
        spec = tp._spec([plot_for("rcap", {"msize": "large"})],
                        {"filter": _DROPDOWN})
        r = tsfl._render(spec)
        caps = _caps(r.figures.values())
        before = [float(c.glyph.size) for c in caps]
        tsfl._move(r, tsfl._MOVES[0][2])
        assert [float(c.glyph.size) for c in caps] == before
        figs, _ = tp._served_after_move(spec, ("Select", "Foreign"))
        served = [g["size"] for f in figs for g in f["glyphs"]
                  if g["type"] == "Scatter" and g["marker"] == "dash"]
        assert len(served) == 2 and all(
            float(v) == pytest.approx(before[0]) for v in served), served

    def test_twoways_cap_is_its_msize(self):
        for k, v in _T["caps"].items():
            assert v["ratio"] == pytest.approx(v["marker_size_val"],
                                               rel=0.01), k

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_caps_take_the_p_line_colour(self, mode, tmp_path):
        figs, _ = _figs(mode, tmp_path, _spec([_bar("rcap")]),
                        _frame(_X["s1"]))
        sp = dr.SchemeParser("s2color")
        caps = _caps(figs)
        assert caps
        for c in caps:
            assert str(c.glyph.line_color).lower() == \
                str(sp.default_color(0, "rcap")).lower()

    def test_the_dash_marker_is_as_long_as_its_size(self):
        import bokeh
        p = os.path.join(os.path.dirname(bokeh.__file__), "server",
                         "static", "js", "bokeh.js")
        with open(p, encoding="utf-8") as fh:
            js = fh.read()
        i = js.index("function _one_line(ctx, r) {")
        body = js[i:i + 120]
        assert "ctx.moveTo(-r, 0);" in body and "ctx.lineTo(r, 0);" in body
        j = js.index("dash(ctx, i, r, visuals) {")
        assert "_one_line(ctx, r);" in js[j:j + 80]


@pytest.mark.parametrize("mode", _MODES)
class TestRcapsymDrawsNoCaps:

    def test_spine_and_two_markers(self, mode, tmp_path):
        figs, _ = _figs(mode, tmp_path, _spec([_bar("rcapsym")]),
                        _frame(_X["s1"]))
        types = [type(r.glyph).__name__ for f in figs for r in f.renderers
                 if hasattr(r, "glyph")]
        assert types == ["Segment", "Scatter", "Scatter"], types
        assert _T["rcapsym"]["default"]["cap_lines"] == 0

    def test_the_markers_take_the_schemes_size(self, mode, tmp_path):
        figs, _ = _figs(mode, tmp_path, _spec([_bar("rcapsym")]),
                        _frame(_X["s1"]))
        want = dr.SchemeParser("s2color").default_marker_size(0)
        sc = _glyphs(figs, "Scatter")
        assert len(sc) == 2
        assert all(float(s.glyph.size) == pytest.approx(want) for s in sc)


# ---------------------------------------------------------------------------
# The machinery is gone; the tooltips are not
# ---------------------------------------------------------------------------

class TestTheSpacingMachineryIsGone:

    @pytest.mark.parametrize("mode", _MODES)
    def test_no_mapper_tags_a_source(self, mode, tmp_path):
        figs, _ = _figs(mode, tmp_path,
                        _spec([_bar("bar"), _bar("rbar"), _bar("rcap"),
                               _bar("rcapsym")]), _frame(_X["s1"]))
        for f in figs:
            for r in f.renderers:
                src = getattr(r, "data_source", None)
                assert not hasattr(src, "_dash_spacing")
                assert not hasattr(src, "_dash_spacing_glyphs")
        assert not hasattr(dr.GlyphMapper, "_tag_spacing")

    def test_the_page_script_holds_no_spacing_writer(self):
        for word in ("dash_spacing", "derived_spacing", "_dspacing"):
            assert word not in dr._FILTER_JS, word

    def test_no_callback_carries_spacing_args(self):
        r = tsfl._render(tp._spec([plot_for("bar")], {"filter": _DROPDOWN}))
        for cb in r.filter_callbacks:
            assert not [k for k in cb.args if "spacing" in k]

    def test_the_served_app_holds_no_geometry_copier(self, tmp_path):
        sp, dp = _write(tmp_path, tp._spec([plot_for("bar")],
                                           {"filter": _DROPDOWN}), tp._DF)
        ap = os.path.join(str(tmp_path), "app.py")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(ap)
        with open(ap, encoding="utf-8") as fh:
            assert "_dash_copy_redraw_geometry" not in fh.read()
        assert not hasattr(dr, "_dash_copy_redraw_geometry")


class TestTheTooltipsAreUnchanged:

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_fields(self, mode, tmp_path):
        for t in ("bar", "rbar", "rcap", "rcapsym"):
            self._one_type(mode, t, tmp_path)

    @staticmethod
    def _one_type(mode, t, tmp_path):
        spec = tp._spec([plot_for(t)])
        figs, _ = _figs(mode, tmp_path, spec, tp._DF)
        hovers = [h for f in figs for h in f.tools
                  if type(h).__name__ == "HoverTool"]
        assert hovers
        names = {lab for h in hovers for lab, _ in (h.tooltips or [])}
        want = ({"mpg", "weight"} if t == "bar"
                else {"mpg", "price", "weight"})
        assert want <= {n.strip() for n in names} or want <= {
            str(v).strip("@{}") for h in hovers
            for _, v in (h.tooltips or [])}, names


# ---------------------------------------------------------------------------
# P1.17b (WP-30 S27): twoway's default base and axis extent
# ---------------------------------------------------------------------------
#
# The defect (measured at c8807c2): with no base(), bar, spike, dropline and
# area were drawn from 0 in both modes -- a y of 10 to 14 stood on 0, below
# the axis twoway draws -- and on a %td axis 0 was 01jan1970.  twoway's rule
# (scripts/extract_default_base_truth.do, fixture
# test/fixtures/default_base_truth.json, from .plot#.drawn_base and
# .plotregion#.yscale.curmin/curmax): the default base is 0 clamped into
# the axis's finished scale, computed without it; under by() the common
# scale's, under yrescale each panel's, on yaxis(2) the second axis's.  An
# explicit base() widens the scale but places no tick.

with open(os.path.join(_HERE, "fixtures", "default_base_truth.json"),
          encoding="utf-8") as _fh:
    _DB = json.load(_fh)

#: The extractor's frame (x1 ypos y12 yneg ys g d ymix ydown).
_DB_FRAME = pd.DataFrame({
    "x1": [1.0, 2, 3, 4, 5], "ypos": [10.0, 11, 12, 13, 14],
    "y12": [12.0, 25, 33, 41, 18], "yneg": [-10.0, -11, -12, -13, -14],
    "ys": [1.0, 2, 3, 4, 5], "g": [1.0, 1, 2, 2, 2],
    "d": [15000.0, 15007, 15014, 15021, 15028],
    "ymix": [-3.0, 5, 8, 2, -1], "ydown": [14.0, 13, 12, 11, 10]})
_DB_BO = {"formats": {"d": "%td"}}


def _db_p(t, y, x="x1", **o):
    return {"type": t, "yvar": y, "xvar": x, "options": o}


#: Fixture key -> (plots, graph options, if); the extractor's commands.
_DB_CASES = {
    "bar_ypos": ([_db_p("bar", "ypos")], {}, ""),
    "bar_y12": ([_db_p("bar", "y12")], {}, ""),
    "spike_y12": ([_db_p("spike", "y12")], {}, ""),
    "dropline_y12": ([_db_p("dropline", "y12")], {}, ""),
    "area_y12": ([_db_p("area", "y12")], {}, ""),
    "bar_yneg": ([_db_p("bar", "yneg")], {}, ""),
    "bar_ymix": ([_db_p("bar", "ymix")], {}, ""),
    "bar_scatter": ([_db_p("bar", "y12"), _db_p("scatter", "ys")], {}, ""),
    "bar_base5": ([_db_p("bar", "ypos", base="5")], {}, ""),
    "spike_base5": ([_db_p("spike", "ypos", base="5")], {}, ""),
    "area_base5": ([_db_p("area", "y12", base="5")], {}, ""),
    "bar_base20": ([_db_p("bar", "ypos", base="20")], {}, ""),
    "two_bars": ([_db_p("bar", "y12"), _db_p("bar", "ypos", base="30")],
                 {}, ""),
    "auto_explicit0": ([_db_p("bar", "ypos"), _db_p("bar", "y12", base="0")],
                       {}, ""),
    "bar_log": ([_db_p("bar", "ypos")], {"yscale": "log"}, ""),
    "area_log": ([_db_p("area", "ypos")], {"yscale": "log"}, ""),
    "bar_range0": ([_db_p("bar", "ypos")], {"yscale": "range(0)"}, ""),
    "bar_ylabel5": ([_db_p("bar", "ypos")], {"ylabel": "5(5)15"}, ""),
    "bar_reverse": ([_db_p("bar", "ypos")], {"yscale": "reverse"}, ""),
    "bar_if": ([_db_p("bar", "ypos")], {}, "x1>=3"),
    "bar_ydown": ([_db_p("bar", "ydown")], {}, ""),
    "bar_ydown_if": ([_db_p("bar", "ydown")], {}, "x1<=3"),
    "bar_y2": ([_db_p("scatter", "y12"), _db_p("bar", "ypos", yaxis="2")],
               {}, ""),
    "bar_by": ([_db_p("bar", "y12")], {"by": "g"}, ""),
    "bar_by_yrescale": ([_db_p("bar", "y12")], {"by": "g, yrescale"}, ""),
    "bar_by_y2": ([_db_p("scatter", "y12"),
                   _db_p("bar", "ypos", yaxis="2")], {"by": "g"}, ""),
}
_DB_PROPS = {"VBar": "bottom", "VArea": "y1", "Segment": "y0"}
#: yscale(range(0)): twoway ticks 10(1)14 over [0, 14], dash 0(5)15 over
#: [0, 15] -- S21's #N-over-range() rule, not the base; the base (0) is
#: checked, the scale and ticks are not.
_DB_TICKS_ELSEWHERE = {"bar_range0"}


def _db_figs(mode, tmp_path, plots, go=None, if_expr="", df=None, bo=None):
    spec = tp._spec(plots, dict(_DB_BO, **(bo or {})), go, if_expr=if_expr)
    figs, _ = _figs(mode, tmp_path, spec, _DB_FRAME if df is None else df)
    return sorted(figs, key=lambda f: str(getattr(f.title, "text", "")))


def _db_base(r):
    """The base a bar, area or spike renderer draws from: its column's one
    value, or the number; a list when the column holds several."""
    v = getattr(r.glyph, _DB_PROPS[type(r.glyph).__name__])
    fld = v if isinstance(v, str) else getattr(v, "field", None)
    if fld:
        vals = sorted({float(x) for x in r.data_source.data[fld]})
        return vals[0] if len(vals) == 1 else vals
    return float(getattr(v, "value", v))


def _db_based(f):
    return [r for r in f.renderers
            if type(getattr(r, "glyph", None)).__name__ in _DB_PROPS]


def _db_scale(f, name="default"):
    for h in getattr(f, "_dash_hull_entries", None) or ():
        if tuple(h["key"]) == (name, "y"):
            return h["lo"], h["hi"]
    return None


def _db_check(key, row, f, r, bad, ticks=True):
    """Compare the base of *r* and the scale and ticks of its axis on
    figure *f* with the fixture *row*."""
    name = getattr(r, "y_range_name", "default") or "default"
    got = _db_base(r)
    if got != pytest.approx(row["drawn_base"]):
        bad.append("%s: base %s, twoway %s" % (key, got, row["drawn_base"]))
    if key in _DB_TICKS_ELSEWHERE:
        return
    sc, want = _db_scale(f, name), (row["curmin"], row["curmax"])
    span = abs(want[1] - want[0]) or 1.0
    if sc is None or any(abs(a - b) > 1e-9 * span for a, b in zip(sc, want)):
        bad.append("%s: scale %s, twoway %s" % (key, sc, want))
    if ticks:
        import test_default_axes as tda
        got_t = tda._ticks(f, "y", name)
        want_t = tda._steps(row["ticks"])
        if got_t is None or [round(v, 9) for v in got_t] != want_t:
            bad.append("%s: ticks %s, twoway %s" % (key, got_t, want_t))


class TestTheBaseFixture:

    def test_meta_is_stamped(self):
        assert {"stata_version", "born_date", "dash_commit",
                "extracted"} <= set(_DB["_meta"])
        assert set(_DB_CASES) | {"bar_td", "dropline_td"} == set(_DB["bases"])


class TestTheDefaultBaseIsTwoways:

    @pytest.mark.parametrize("mode", _MODES)
    def test_every_case(self, mode, tmp_path):
        """Every bases.* row but the %td ones: the base each layer is drawn
        from, the scale of its axis and that axis's ticks are twoway's;
        under by() per panel (twoway draws a default base as 0 clamped
        into the axis's scale, P1.17b)."""
        bad = []
        for key, (plots, go, if_expr) in _DB_CASES.items():
            row = _DB["bases"][key]
            figs = _db_figs(mode, tmp_path, plots, go, if_expr)
            if "panels" in row:
                for f, prow in zip(figs, row["panels"]):
                    [r] = _db_based(f)
                    _db_check("%s/%s" % (key, f.title.text), prow, f, r, bad)
                continue
            [f] = figs
            rs = _db_based(f)
            _db_check(key, row, f, rs[0], bad)
            if "drawn_base2" in row:
                _db_check(key + "/2", dict(row, drawn_base=row["drawn_base2"]),
                          f, rs[1], bad)
            if "y" in row:
                sc, want = _db_scale(f), (row["y"]["curmin"],
                                          row["y"]["curmax"])
                if sc != pytest.approx(want):
                    bad.append("%s: y scale %s, twoway %s" % (key, sc, want))
        assert not bad, "\n".join(bad)

    @pytest.mark.parametrize("mode", _MODES)
    def test_auto(self, mode, tmp_path):
        """auto.* and auto3.*: `<t> mpg weight' (in 1/3) on the auto data
        stands where twoway stands it (10; 17)."""
        import test_by_scales as tb
        bad = []
        auto = tb._frame("auto")
        for which, df in (("auto", auto), ("auto3", auto.iloc[:3])):
            for t, row in _DB[which].items():
                spec = tp._spec([{"type": t, "yvar": "mpg", "xvar": "weight",
                                  "options": {}}])
                figs, _ = _figs(mode, tmp_path, spec, df.reset_index(drop=True))
                [f] = figs
                _db_check("%s.%s" % (which, t), row, f, _db_based(f)[0], bad)
        assert not bad, "\n".join(bad)


class TestTheBaseOnADateAxis:

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_default_base_is_1960_clamped(self, mode, tmp_path):
        """%td: the base is Stata's 0 (01jan1960) clamped into the scale --
        twoway's scale low end, 14997 (bases.bar_td, dropline_td), on the
        ticks twoway draws; never 0 ms (01jan1970).  WP-30 P1.17b: S44's
        hand-off, tightened from dash's own scale end."""
        def ms(v):
            return float(dr._dash_units_to_axis(np.array([v]), "td")[0])
        want = {t: _DB["bases"]["%s_td" % t]
                for t in ("bar", "dropline")}
        bad = []
        for t in ("bar", "spike", "dropline", "area"):
            row = want.get(t, want["bar"])
            [f] = _db_figs(mode, tmp_path, [_db_p(t, "d")])
            [r] = _db_based(f)
            got, sc = _db_base(r), _db_scale(f)
            if sc is None or got != pytest.approx(ms(row["drawn_base"])) \
                    or sc[0] != pytest.approx(ms(row["curmin"])):
                bad.append((t, got, sc))
        assert not bad, bad


class TestTheBaseAfterAMove:

    @pytest.mark.parametrize("mode", _MODES)
    def test_move_and_back(self, mode, tmp_path):
        """`bar ydown x1' with a range filter on x1: moved to x1 <= 3 the
        base is twoway's `if x1<=3' (12), moved back it is 10, saved (the
        page's own script under node) and served."""
        import test_default_axes as tda
        want = (_DB["bases"]["bar_ydown_if"]["drawn_base"],
                _DB["bases"]["bar_ydown"]["drawn_base"])
        bad = []
        for t in ("bar", "spike", "dropline", "area"):
            spec = tp._spec([_db_p(t, "ydown")],
                            dict(_DB_BO, filter="x1, type(range)"))
            sp, dp = _write(tmp_path, spec, _DB_FRAME)
            got = []
            if mode == "saved":
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    r = dr.DashRenderer(sp, dp)
                    render_models(r)
                for v in ((1.0, 3.0), (1.0, 5.0)):
                    [f] = tda._move_saved(r, "RangeSlider", v)
                    got.append(_db_base(_db_based(f)[0]))
            else:
                import test_mode_parity as mp
                _N[0] += 1
                ap = os.path.join(str(tmp_path), "app_%d.py" % _N[0])
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    dr.ServerAppBuilder(sp, dp).build(ap)
                    mod = load_app(ap, "_db_app_%d" % _N[0])
                    doc = Document()
                    mod.make_document(doc)
                for v in ((1.0, 3.0), (1.0, 5.0)):
                    [f] = tda._move_served(doc, "RangeSlider", v)
                    got.append(_db_base(_db_based(f)[0]))
            if got != [pytest.approx(w) for w in want]:
                bad.append((t, got, want))
        assert not bad, bad


class TestTheMappersMarkTheirBase:

    def test_each_mapper_tags_its_base(self):
        bad = []
        for t, prop in (("bar", "bottom"), ("area", "y1"), ("spike", "y0"),
                        ("dropline", "y0")):
            for opts, auto in (({}, True), ({"base": "5"}, False)):
                fig = bk_figure()
                src = ColumnDataSource({"x": [1.0, 2.0], "y": [3.0, 4.0]})
                out = getattr(_gm(), "map_" + t)(fig, src, "y", "x",
                                                 dict(opts))
                rs = [r for r in fig.renderers
                      if dr._dash_base_spec(r) is not None]
                specs = [dr._dash_base_spec(r) for r in rs]
                if specs != [{"auto": auto, "letter": "y", "prop": prop,
                              "zero": 0.0}]:
                    bad.append((t, opts, specs))
                    continue
                v = getattr(rs[0].glyph, prop)
                fld = v if isinstance(v, str) else getattr(v, "field", None)
                if t == "bar" and (fld == dr.GlyphMapper._BASE_COL) != auto:
                    bad.append((t, opts, fld))
                del out
        assert not bad, bad

    def test_base_value(self):
        gm = _gm()
        for raw in (None, "", ".", " . "):
            o = {} if raw is None else {"base": raw}
            assert gm._base_value(o, "bar") is None, raw
        assert gm._base_value({"base": "5"}, "bar") == 5.0
        for raw in ("abc", "inf", "nan"):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                dr._dash_reset_notes()
                assert gm._base_value({"base": raw}, "bar") is None, raw
            assert len(caught) == 1, (raw, [str(w.message) for w in caught])

    def test_base_zero(self):
        assert _gm()._base_zero("y") == 0.0
        for k in ("td", "tc", "tC", "tw", "tm", "tq", "th", "ty"):
            want = float(dr._dash_units_to_axis(np.array([0.0]), k)[0])
            want = want if math.isfinite(want) else 0.0  # %ty: no year 0
            assert _gm({"y": k})._base_zero("y") == want, k
        assert _gm({"y": "td"})._base_zero("y") == -315619200000.0


class TestTheBaseSpec:

    def test_reads_only_well_formed_tags(self):
        class R:
            def __init__(self, *tags):
                self.tags = list(tags)
        good = 'dash_base:{"auto":true,"letter":"y","prop":"y0","zero":0.0}'
        assert dr._dash_base_spec(R("x", good)) == {
            "auto": True, "letter": "y", "prop": "y0", "zero": 0.0}
        for bad in ("", "dash_base:{", "dash_base:[1]",
                    'dash_base:{"auto":true,"letter":"y","prop":"__proto__","zero":0}',
                    'dash_base:{"auto":true,"letter":"z","prop":"y0","zero":0}',
                    'dash_base:{"auto":true,"letter":"y","prop":"y0","zero":"0"}',
                    'dash_base:{"auto":true,"letter":"y","prop":"y0","zero":NaN}',
                    'dash_base:{"auto":1,"letter":"y","prop":"y0","zero":0}',
                    good[:-1] + " " * 200 + "}"):
            assert dr._dash_base_spec(R(bad)) is None, bad
        assert dr._dash_base_spec(R()) is None
        assert dr._dash_base_spec(object()) is None


class TestTheFill:

    @staticmethod
    def _fig(scale, auto=True, name="default"):
        fig = bk_figure()
        src = ColumnDataSource({"x": [1.0, 2.0], "y": [3.0, 4.0],
                                "b": [0.0, 0.0]})
        r = fig.vbar(x="x", top="y", bottom="b" if auto else 2.0,
                     width=1.0, source=src)
        dr.GlyphMapper._tag_base(r, "bottom", auto, 0.0)
        if scale is not None:
            fig._dash_hull_entries = [{"key": (name, "y"), "letter": "y",
                                       "name": name, "kind": None,
                                       "lo": scale[0], "hi": scale[1]}]
        return fig, r

    def test_the_axis_scale(self):
        fig, _ = self._fig((10.0, 14.0))
        assert dr._dash_axis_scale(fig, "y", "default") == (10.0, 14.0)
        assert dr._dash_axis_scale(fig, "y", "y2") is None
        fig._dash_secondary_hulls = {"y2": (3.0, 4.0, None, False)}
        assert dr._dash_axis_scale(fig, "y", "y2") == (3.0, 4.0)
        assert dr._dash_axis_scale(self._fig(None)[0], "y", "default") is None
        assert dr._dash_axis_scale(self._fig((math.nan, 1.0))[0], "y",
                                   "default") is None

    def test_clamps_zero_into_the_scale(self):
        for sc, want in (((10.0, 14.0), 10.0), ((-14.0, -10.0), -10.0),
                         ((-5.0, 5.0), 0.0)):
            fig, r = self._fig(sc)
            n = dr._dash_finish_auto_bases(fig)
            assert (n, list(r.data_source.data["b"])) == (
                int(want != 0.0), [want, want]), sc
        # No scale: nothing written.  An unchanged column: not rewritten.
        fig, r = self._fig(None)
        assert dr._dash_finish_auto_bases(fig) == 0
        fig, r = self._fig((10.0, 14.0))
        dr._dash_finish_auto_bases(fig)
        col = r.data_source.data["b"]
        assert dr._dash_finish_auto_bases(fig) == 0
        assert r.data_source.data["b"] is col
        # An explicit base is left alone.
        fig, r = self._fig((10.0, 14.0), auto=False)
        assert dr._dash_finish_auto_bases(fig) == 0
        assert r.glyph.bottom == 2.0
