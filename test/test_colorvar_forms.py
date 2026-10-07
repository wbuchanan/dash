"""test_colorvar_forms.py -- colorvar()'s explicit forms and the colour
key's own axis options (GAPS2 X2).

Measured at 91d97be: `colorvar(rep78) colordiscrete colorcuts(2 4)` gives
<=2 / 2-4 / >4, so rep78 = 1, 3 and 5 are coloured as ranges where twoway
draws them gray. `colorcuts(0 2 4)` keeps an empty '<=0' level. No note is
printed for either case. `colorlevels()`, `colorvarminmax`, `zlabel()`,
`ztitle()` and `zscale()` were only named in a note or not read at all.

After the fix: under `colordiscrete` with `colorcuts()` each cut is a
level and every other value joins missing in gray (twoway's
colorvar_options.sthlp:119-121); a cut below the column minimum is
dropped (:111-116); `colorlevels(#)` and `colorvarminmax` are read
(:124-140); `zlabel()`/`ztitle()`/`zscale()` are drawn on the colour key.
The continuous default is unchanged (DISCOVERY Q5).
"""
import os
import sys
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.models import ColorBar, ColumnDataSource, CustomJS, Legend
from bokeh.models.tickers import BasicTicker, FixedTicker
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from conftest import make_spec, make_data_json, exec_app  # noqa: E402
import colour_bins as cb  # noqa: E402

_LE, _DASH = chr(0x2264), chr(0x2013)   # ASCII source, whatever the editor

_VL = {"repair": {"1": "Poor", "2": "Fair", "3": "Avg", "4": "Good",
                  "5": "Exc"}}
_VLN = {"rep78": "repair"}


def _df(n=20):
    return pd.DataFrame({
        "mpg": np.linspace(12.0, 41.0, n),
        "weight": np.linspace(1760.0, 4840.0, n),
        "price": np.linspace(3291.0, 15906.0, n),
        "rep78": np.array([1.0, 2.0, 3.0, 4.0, 5.0] * (n // 5)),
    })


def _bins(options, values):
    """The bin label _apply_colorvar gives each value, and the factors."""
    gm = dr.GlyphMapper(dr.OptionTranslator(), dr.SchemeParser("s2color"))
    src = ColumnDataSource({"v": list(values),
                            "y": [1.0] * len(values)})
    fig = figure()
    rend = fig.scatter(x="v", y="y", source=src)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        gm._apply_colorvar(fig, rend, src, dict(options, colorvar="v"))
    # WP-29 P0.16: the missing sentinel is None / the colour column is named under __dash_cvar.
    return cb.colour_values(rend), list(cb.colour_mapper(rend).factors)


def _both(bo=None, go=None, plots=None):
    """(saved renderer, served document, saved warnings, served warnings)."""
    spec = tp._spec(plots or [tp.plot_for("scatter")], bo, go)
    r, std_w = tp._standalone(spec)
    doc, srv_w = tp._served(spec)
    return r, doc, std_w, srv_w


def _colorbar(fig_or_doc):
    (bar,) = fig_or_doc.select({"type": ColorBar})
    return bar


def _colorvar_legend(fig_or_doc):
    for m in fig_or_doc.select({"type": Legend}):
        if getattr(m, "name", "") == dr._COLORVAR_LEGEND_NAME:
            return m
    return None


class TestColordiscreteWithCuts:
    """``colordiscrete`` with ``colorcuts()``: the cuts ARE the levels."""

    def test_colordiscrete_with_cuts_makes_each_cut_a_level(self):
        got, factors = _bins({"colordiscrete": "yes", "colorcuts": "2 4"},
                             [1.0, 2.0, 3.0, 4.0, 5.0, np.nan])
        # WP-29 P0.16: the missing sentinel is None / the colour column is named under __dash_cvar.
        assert got == [None, "2", None, "4", None, None]
        assert factors == ["2", "4"]


class TestCutsBelowTheMinimum:
    """A cut below colorvar's minimum is dropped."""

    def test_a_cut_below_the_minimum_is_dropped(self):
        got, factors = _bins({"colorcuts": "0 2 4"},
                             [1.0, 2.0, 3.0, 4.0, 5.0])
        lo, mid, hi = f"{_LE}2", f"2{_DASH}4", ">4"
        assert factors == [lo, mid, hi]
        assert f"{_LE}0" not in factors
        assert len(factors) == 3

    def test_all_cuts_below_the_minimum_use_the_minimum(self):
        got, factors = _bins({"colorcuts": "-3 0"}, [1.0, 2.0, 3.0])
        assert factors == [f"{_LE}1", ">1"]


class TestColorlevels:
    """``colorlevels(#)`` is twoway's own spelling of ``colornlevels(#)``."""

    def test_colorlevels_gives_levels_minus_one_cuts(self):
        vals = list(np.linspace(0.0, 12.0, 13))
        got_a, factors_a = _bins({"colorlevels": "4"}, vals)
        got_b, factors_b = _bins({"colornlevels": "4"}, vals)
        assert factors_a == factors_b
        assert len(factors_a) == 4
        assert got_a == got_b

    def test_colorlevels_under_colordiscrete_makes_the_cut_values_the_levels(self):
        got, factors = _bins({"colordiscrete": "yes", "colorlevels": "4"},
                             [0.0, 3.0, 6.0, 9.0, 12.0])
        # WP-29 P0.16: the missing sentinel is None / the colour column is named under __dash_cvar.
        assert factors == ["3", "6", "9"]
        assert got == [None, "3", "6", "9", None]


class TestColorvarminmax:
    """``colorvarminmax`` adds the minimum and maximum to the cuts."""

    def test_colorvarminmax_adds_min_and_max_to_the_cuts(self):
        got, factors = _bins({"colorcuts": "5", "colorvarminmax": "yes"},
                             [1.0, 5.0, 9.0])
        assert factors == [f"{_LE}1", f"1{_DASH}5", f"5{_DASH}9", ">9"]

    def test_colorvarminmax_alone_ticks_the_colour_bar_at_min_and_max(self):
        gm = dr.GlyphMapper(dr.OptionTranslator(), dr.SchemeParser("s2color"))
        src = ColumnDataSource({"v": [1.0, 5.0, 9.0],
                                "y": [1.0, 1.0, 1.0]})
        fig = figure()
        rend = fig.scatter(x="v", y="y", source=src)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            gm._apply_colorvar(fig, rend, src,
                               {"colorvar": "v", "colorvarminmax": "yes"})
        bar = _colorbar(fig)
        assert isinstance(bar.ticker, FixedTicker)
        assert 1.0 in bar.ticker.ticks
        assert 9.0 in bar.ticker.ticks


class TestTheCutHelper:
    """Unit tests of the module-level ``_dash_colorvar_cuts``."""

    def test_the_helper_drops_cuts_below_the_minimum(self):
        vals = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        assert dr._dash_colorvar_cuts(vals, [0.0, 2.0, 4.0], None, False) \
            == [2.0, 4.0]

    def test_sorted_and_deduplicated(self):
        vals = np.array([1.0, 5.0, 9.0])
        assert dr._dash_colorvar_cuts(vals, [5.0, 5.0, 2.0], None, False) \
            == [2.0, 5.0]

    def test_all_below_minimum_gives_the_minimum(self):
        vals = np.array([1.0, 2.0, 3.0])
        assert dr._dash_colorvar_cuts(vals, [-3.0, 0.0], None, False) == [1.0]

    def test_levels_gives_interior_points(self):
        vals = np.array([0.0, 12.0])
        assert dr._dash_colorvar_cuts(vals, None, 4, False) == [3.0, 6.0, 9.0]

    def test_minmax_appends_min_and_max(self):
        vals = np.array([1.0, 5.0, 9.0])
        assert dr._dash_colorvar_cuts(vals, [5.0], None, True) \
            == [1.0, 5.0, 9.0]

    def test_no_finite_values_gives_no_cuts(self):
        vals = np.array([np.nan, np.nan])
        assert dr._dash_colorvar_cuts(vals, [2.0], None, False) == []

    def test_a_plain_list_or_iterator_gives_the_array_s_answer(self):
        vals = [1.0, float("nan"), 5.0, 9.0]
        want = dr._dash_colorvar_cuts(np.array(vals), [5.0], None, True)
        assert want == [1.0, 5.0, 9.0]
        assert dr._dash_colorvar_cuts(vals, [5.0], None, True) == want
        assert dr._dash_colorvar_cuts(iter(vals), [5.0], None, True) == want


class TestTheBinHelper:
    """Unit tests of the module-level ``_dash_colorvar_bins``."""

    def test_the_bin_helper_in_both_modes(self):
        vals = np.array([1.0, 2.0, 2.0, 3.0, np.nan])

        labels, binned, has_missing = dr._dash_colorvar_bins(
            vals, [2.0], False, lambda v: f"{v:g}")
        assert labels == [f"{_LE}2", ">2"]
        # WP-29 P0.16: the missing sentinel is None / the colour column is named under __dash_cvar.
        assert binned == [f"{_LE}2", f"{_LE}2", f"{_LE}2", ">2", None]
        assert has_missing

        labels2, binned2, has_missing2 = dr._dash_colorvar_bins(
            vals, [2.0], True, lambda v: f"{v:g}")
        assert labels2 == ["2"]
        assert binned2 == [None, "2", "2", None, None]
        assert has_missing2

    def test_a_value_on_a_cut_is_in_the_bin_below(self):
        vals = np.array([2.0])
        _labels, binned, _hm = dr._dash_colorvar_bins(
            vals, [2.0, 4.0], False, lambda v: f"{v:g}")
        assert binned == [f"{_LE}2"]

    def test_empty_cuts_bins_every_value_as_missing(self):
        vals = np.array([1.0, 2.0, np.nan])
        labels, binned, has_missing = dr._dash_colorvar_bins(
            vals, [], False, lambda v: f"{v:g}")
        assert labels == []
        # WP-29 P0.16: the missing sentinel is None / the colour column is named under __dash_cvar.
        assert binned == [None, None, None]
        assert has_missing


class TestZOptions:
    """``ztitle()``/``zlabel()``/``zscale()`` on the colour key."""

    def test_ztitle_titles_the_discrete_key(self):
        plots = [tp.plot_for("scatter", {"colorvar": "rep",
                                         "colordiscrete": "colordiscrete"})]
        r, doc, std_w, srv_w = _both(go={"ztitle": "Repair"}, plots=plots)
        std_fig = list(r.figures.values())[0]
        std_leg = _colorvar_legend(std_fig)
        srv_leg = _colorvar_legend(doc)
        assert std_leg is not None and std_leg.title == "Repair"
        assert srv_leg is not None and srv_leg.title == "Repair"
        assert not any("ztitle" in w for w in std_w + srv_w)

    def test_ztitle_titles_the_colour_bar(self):
        plots = [tp.plot_for("scatter", {"colorvar": "price"})]
        r, doc, std_w, srv_w = _both(go={"ztitle": "Repair"}, plots=plots)
        std_fig = list(r.figures.values())[0]
        assert _colorbar(std_fig).title == "Repair"
        assert _colorbar(doc).title == "Repair"
        assert not any("ztitle" in w for w in std_w + srv_w)

    def test_zlabel_ticks_the_colour_bar(self):
        plots = [tp.plot_for("scatter", {"colorvar": "price"})]

        r, _doc, _sw, _rw = _both(go={"zlabel": "4000(4000)16000"},
                                  plots=plots)
        bar = _colorbar(list(r.figures.values())[0])
        assert isinstance(bar.ticker, FixedTicker)
        assert sorted(bar.ticker.ticks) == [4000.0, 8000.0, 12000.0,
                                            16000.0]

        r2, _doc2, _sw2, _rw2 = _both(go={"zlabel": "#3"}, plots=plots)
        bar2 = _colorbar(list(r2.figures.values())[0])
        # WP-30 P1.23b: zlabel(#3) as Bokeh's BasicTicker was wrong
        # because twoway places #N key ticks by its natscale rule (15,000
        # 15,200 15,400 for sp500's dates).
        assert isinstance(bar2.ticker, FixedTicker)
        assert list(bar2.ticker.ticks) == [5000.0, 10000.0, 15000.0]
        assert [bar2.major_label_overrides[t] for t in bar2.ticker.ticks] \
            == ["5,000", "10,000", "15,000"]

        r3, _doc3, _sw3, _rw3 = _both(go={"zlabel": "none"}, plots=plots)
        bar3 = _colorbar(list(r3.figures.values())[0])
        assert isinstance(bar3.ticker, FixedTicker)
        assert list(bar3.ticker.ticks) == []

    def test_zscale_range_widens_log_switches_reverse_flips(self):
        plots = [tp.plot_for("scatter", {"colorvar": "price"})]

        r, _d, _sw, _rw = _both(go={"zscale": "range(0 20000)"}, plots=plots)
        bar = _colorbar(list(r.figures.values())[0])
        assert bar.color_mapper.low == 0.0
        assert bar.color_mapper.high == 20000.0

        lo0, hi0 = float(tp._DF["price"].min()), float(tp._DF["price"].max())
        r2, _d2, _sw2, _rw2 = _both(go={"zscale": "range(5000 6000)"},
                                    plots=plots)
        bar2 = _colorbar(list(r2.figures.values())[0])
        # range() widens only: a narrower request leaves the data bounds.
        assert bar2.color_mapper.low == lo0
        assert bar2.color_mapper.high == hi0

        from bokeh.models import LogColorMapper
        r3, _d3, _sw3, _rw3 = _both(go={"zscale": "log"}, plots=plots)
        bar3 = _colorbar(list(r3.figures.values())[0])
        assert isinstance(bar3.color_mapper, LogColorMapper)

        r4, _d4, _sw4, _rw4 = _both(plots=plots)
        default_bar = _colorbar(list(r4.figures.values())[0])
        r5, _d5, _sw5, _rw5 = _both(go={"zscale": "reverse"}, plots=plots)
        rev_bar = _colorbar(list(r5.figures.values())[0])
        assert list(rev_bar.color_mapper.palette) == \
            list(reversed(default_bar.color_mapper.palette))

    def test_a_z_option_on_a_discrete_key_is_named_once(self):
        plots = [tp.plot_for("scatter", {"colorvar": "rep",
                                         "colordiscrete": "colordiscrete"})]
        _r, _d, std_w, srv_w = _both(go={"zlabel": "1(1)5"}, plots=plots)
        assert len([w for w in std_w if "zlabel" in w]) == 1
        assert len([w for w in srv_w if "zlabel" in w]) == 1

        plots_by = [tp.plot_for("scatter", {"colorvar": "rep",
                                            "colordiscrete": "colordiscrete"})]
        _r2, _d2, std_w2, _srv_w2 = _both(
            go={"zlabel": "1(1)5", "by": "foreign"}, plots=plots_by)
        assert len([w for w in std_w2 if "zlabel" in w]) == 1

    def test_an_unknown_z_sub_option_is_named(self):
        plots = [tp.plot_for("scatter", {"colorvar": "price"})]

        _r, _d, std_w, _sw = _both(
            go={"ztitle": '"Repair", orientation(vertical)'}, plots=plots)
        assert any("orientation(vertical)" in w for w in std_w)

        _r2, _d2, std_w2, _sw2 = _both(go={"zscale": "alt"}, plots=plots)
        assert any("alt" in w for w in std_w2)

        _r3, _d3, std_w3, _sw3 = _both(
            go={"zlabel": "4000(4000)12000, format(%9.2f)"}, plots=plots)
        # WP-30 P1.23b: naming format(%9.2f) was wrong because twoway
        # writes the key in it (0.00 5000.00 ...).
        assert not any("format(%9.2f)" in w for w in std_w3)
        bar3 = _colorbar(list(_r3.figures.values())[0])
        assert [bar3.major_label_overrides[t] for t in bar3.ticker.ticks] \
            == ["4000.00", "8000.00", "12000.00"]

    def test_ztitle_suboptions_keep_the_key_title(self):
        """WP-29 P0.4: ztitle() with only sub-options keeps the colour
        variable's title and styles it, as twoway draws it (f1, f2); a typed
        "" still removes it (f3).  It emptied the key's title."""
        # WP-30 P1.12a: _textbox_size returns the CSS string; twoway's
        # size(large) is 14 pt ('14pt').
        large = dr._textbox_size({'size': 'large'}, None)
        bar_plots = [tp.plot_for("scatter", {"colorvar": "price"})]
        r, doc, _sw, _rw = _both(go={"ztitle": ", size(large)"},
                                 plots=bar_plots)
        for bar in (_colorbar(list(r.figures.values())[0]), _colorbar(doc)):
            assert bar.title == "price"
            assert bar.title_text_font_size == large
        disc = [tp.plot_for("scatter", {"colorvar": "rep",
                                        "colordiscrete": "colordiscrete"})]
        r, doc, _sw, _rw = _both(go={"ztitle": ", color(red)"}, plots=disc)
        for leg in (_colorvar_legend(list(r.figures.values())[0]),
                    _colorvar_legend(doc)):
            assert leg is not None and leg.title == "rep"
            assert leg.title_text_color == "#ff0000"
        for raw, want in ((",", "price"), ('"extra", suffix', "price\nextra"),
                          ('""', "")):
            r, doc, _sw, _rw = _both(go={"ztitle": raw}, plots=bar_plots)
            assert _colorbar(list(r.figures.values())[0]).title == want, raw
            assert _colorbar(doc).title == want, raw


class TestBothModes:
    """The saved and served mapper draw the same factors (BR-16.8)."""

    @pytest.mark.parametrize("opts", [
        {"colorvar": "rep", "colordiscrete": "colordiscrete",
         "colorcuts": "2 4"},
        {"colorvar": "rep", "colorcuts": "0 2 4"},
        {"colorvar": "price", "colorlevels": "4"},
    ])
    def test_both_modes_draw_the_same_bins(self, opts):
        plots = [tp.plot_for("scatter", opts)]
        r, doc, _sw, _rw = _both(plots=plots)
        std_fig = list(r.figures.values())[0]
        # WP-29 P0.16: the missing sentinel is None / the colour column is named under __dash_cvar.

        def _bin_column(fig_or_doc):
            rends = cb.colour_renderers(fig_or_doc)
            return cb.colour_values(rends[0]) if rends else None

        std_binned = _bin_column(std_fig)
        srv_binned = _bin_column(doc)
        assert std_binned is not None and srv_binned is not None
        assert std_binned == srv_binned

    def test_both_modes_draw_the_same_minmax_ticks(self):
        # colorvarminmax alone (no cuts/levels) draws the continuous
        # ColorBar, not a binned column: the saved and served mapper must
        # still agree on its ticks.
        plots = [tp.plot_for("scatter", {"colorvar": "price",
                                         "colorvarminmax": "colorvarminmax"})]
        r, doc, _sw, _rw = _both(plots=plots)
        std_bar = _colorbar(list(r.figures.values())[0])
        srv_bar = _colorbar(doc)
        assert sorted(std_bar.ticker.ticks) == sorted(srv_bar.ticker.ticks)


class TestZTitleIsData:
    def test_ztitle_text_is_data_not_markup(self):
        payload = "<b>x</b> & y"
        plots = [tp.plot_for("scatter", {"colorvar": "price"})]
        r, doc, _sw, _rw = _both(go={"ztitle": '"%s"' % payload},
                                 plots=plots)
        std_fig = list(r.figures.values())[0]
        assert _colorbar(std_fig).title == payload
        assert _colorbar(doc).title == payload
        for m in doc.select({"type": CustomJS}):
            code = getattr(m, "code", "") or ""
            assert payload not in code


# ===========================================================================
# WP-29 P0.16: the colour key is drawn from the rows each layer draws
# ===========================================================================

import json  # noqa: E402
import math  # noqa: E402

from bokeh.document import Document  # noqa: E402
from bokeh.models import (BooleanFilter, CategoricalColorMapper,  # noqa: E402
                          CDSView, IndexFilter, LinearColorMapper, Select)

from js_runner import JsSession  # noqa: E402


def _mapper():
    return dr.GlyphMapper(dr.OptionTranslator(), dr.SchemeParser("s2color"))


def _apply(options, values, domain=None, extra=None):
    """(source, renderer, figure) after _apply_colorvar of colorvar(v)
    over *values*, with the mapper's colour domain set to *domain*."""
    gm = _mapper()
    data = {"v": list(values), "y": [1.0] * len(values)}
    data.update(extra or {})
    src = ColumnDataSource(data)
    fig = figure()
    rend = fig.scatter(x="y", y="y", source=src)
    gm.colorvar_domain = domain
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        gm._apply_colorvar(fig, rend, src, dict(options, colorvar="v"))
    return src, rend, fig


def _served_ns(spec):
    """(namespace, document) of one session of the generated app: the
    test_date_range._served pattern, so a test can read _DASH_MAPPER."""
    tag, sp, dp = tp._write(spec)
    ap = os.path.join(tp._TMP, f"app_ns_{tag}.py")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(ap)
        with open(ap, encoding="utf-8") as fh:
            src = fh.read()
        ns = {"__name__": f"colour_ns_{tag}"}
        exec_app(src, ap, ns)
    return ns


def _session(ns):
    doc = Document()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ns["make_document"](doc)
    return doc


def _saved_root(spec):
    r, _ = tp._standalone(spec)
    return r, r._last_layout_root


def _fire_select(doc, label):
    ws = [w for w in tp._widgets_of(doc) if isinstance(w, Select)]
    assert ws, "no Select widget"
    raw = [v for v, lab in ws[0].options if lab == label]
    tp._fire(ws[0], raw[0])


def _fire_range(doc, value):
    ws = [w for w in tp._widgets_of(doc)
          if type(w).__name__ == "RangeSlider"]
    assert ws, "no RangeSlider widget"
    tp._fire(ws[0], value)


class TestTheColourBinsHelpers:
    """test/colour_bins.py, on hand-built models."""

    def _model(self):
        fig = figure(title="t1")
        src = ColumnDataSource({"x": [1.0, 2.0, 3.0],
                                "__dash_cvar1_v": ["a", None, "b"]})
        m = CategoricalColorMapper(factors=["a", "b"],
                                   palette=["#111111", "#222222"],
                                   nan_color="#808080")
        r = fig.scatter(x="x", y="x", source=src,
                        fill_color={"field": "__dash_cvar1_v",
                                    "transform": m})
        sw = fig.scatter(x=[float("nan")], y=[float("nan")],
                         name=f"{dr._DASH_SWATCH_PREFIX}a", visible=False)
        plain = fig.scatter(x="x", y="x", source=src)
        fig.add_layout(Legend(items=[], name=dr._COLORVAR_LEGEND_NAME),
                       "right")
        return fig, r, sw, plain, m

    def test_colour_renderers_skip_swatches_and_plain_glyphs(self):
        fig, r, _sw, _plain, _m = self._model()
        assert cb.colour_renderers(fig) == [r]

    def test_field_mapper_and_values(self):
        fig, r, _sw, _plain, m = self._model()
        assert cb.colour_field(r) == "__dash_cvar1_v"
        assert cb.colour_mapper(r) is m
        assert cb.colour_values(r) == ["a", None, "b"]

    def test_drawn_values_follow_the_view(self):
        fig, r, _sw, _plain, _m = self._model()
        r.view = CDSView(filter=BooleanFilter(booleans=[True, False, True]))
        assert cb.drawn_colour_values(r) == ["a", "b"]
        r.view = CDSView(filter=IndexFilter(indices=[1, 2]))
        assert cb.drawn_colour_values(r) == [None, "b"]

    def test_bars_and_keys(self):
        fig = figure()
        fig.add_layout(ColorBar(color_mapper=LinearColorMapper(
            palette=["#000000", "#ffffff"], low=1.0, high=9.0)), "right")
        fig.add_layout(Legend(items=[], name=dr._COLORVAR_LEGEND_NAME),
                       "right")
        fig.add_layout(Legend(items=[]), "right")
        assert cb.colour_bars(fig) == [(1.0, 9.0)]
        assert cb.colour_keys(fig) == 2

    def test_interval_bounds(self):
        assert cb.interval_bounds(
            [f"3,748{_DASH}6,828.7", f"{_LE}2", ">4", "Avg"]) == [
            (3748.0, 6828.7), (None, 2.0), (4.0, None), (None, None)]

    def test_figures_by_title(self):
        fig, *_ = self._model()
        assert cb.figures_by_title([fig]) == {"t1": fig}

    def test_colour_keys_reads_both_modes(self, tmp_path):
        import filter_truth_check as ftc
        spec = tp._spec([tp.plot_for("scatter", {"colorvar": "price"})])
        sp, dp = str(tmp_path / "s.json"), str(tmp_path / "d.json")
        with open(sp, "w") as fh:
            json.dump(spec, fh)
        with open(dp, "w") as fh:
            json.dump(make_data_json(tp._DF, tp._VALUE_LABELS,
                                     tp._LABEL_NAMES), fh)
        got = ftc.colour_keys(sp, dp)
        r, root = _saved_root(spec)
        doc, _ = tp._served(spec)
        assert [f["bars"] for f in got["saved"]] == [
            [list(b) for b in cb.colour_bars(f)]
            for f in cb._figures(root)]
        assert [f["bars"] for f in got["served"]] == [
            [list(b) for b in cb.colour_bars(f)]
            for f in cb._figures(doc)]
        assert got["saved"][0]["bars"] == [[3799.0, 11385.0]]


class TestTheColourDomain:
    """``_dash_colorvar_domain``: the values a colorvar() key is drawn from."""

    def test_no_colorvar_gives_none(self):
        assert dr._dash_colorvar_domain({"price": [1.0]}, {}) is None
        assert dr._dash_colorvar_domain({"price": [1.0]},
                                        {"colorvar": " "}) is None

    @pytest.mark.parametrize("name", ["price; x", "a\x60b", 'a"b', "",
                                      "x" * 33])
    def test_a_refused_name_gives_none(self, name):
        assert dr._dash_colorvar_domain({name: [1.0, 2.0]},
                                        {"colorvar": name}) is None

    def test_a_proto_column_is_data(self):
        got = dr._dash_colorvar_domain({"__proto__": [1.0, 2.0]},
                                       {"colorvar": "__proto__"})
        assert list(got) == [1.0, 2.0]

    def test_an_absent_column_gives_none(self):
        assert dr._dash_colorvar_domain({"mpg": [1.0]},
                                        {"colorvar": "price"}) is None
        assert dr._dash_colorvar_domain(pd.DataFrame({"mpg": [1.0]}),
                                        {"colorvar": "price"}) is None

    def test_a_misaligned_mask_warns_and_gives_none(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            got = dr._dash_colorvar_domain(
                {"price": [1.0, 2.0, 3.0]}, {"colorvar": "price"},
                mask=[True, False], where="graph g1 plot 1")
        assert got is None
        msgs = [str(w.message) for w in caught]
        assert len(msgs) == 1 and "could not be restricted" in msgs[0]
        assert "graph g1 plot 1" in msgs[0] and "2 flags for 3 rows" in msgs[0]

    def test_a_frame_and_a_cds_dict_give_the_same_values(self):
        df = pd.DataFrame({"price": [3.0, np.nan, 5.0, 7.0]})
        mask = [True, True, False, True]
        a = dr._dash_colorvar_domain(df, {"colorvar": "price"}, mask)
        b = dr._dash_colorvar_domain(
            ColumnDataSource(df).data, {"colorvar": "price"}, mask)
        np.testing.assert_array_equal(a, b)
        np.testing.assert_array_equal(a, [3.0, np.nan, 7.0])

    def test_rows_with_a_missing_y_are_kept(self):
        df = pd.DataFrame({"y": [1.0, np.nan, 3.0],
                           "price": [10.0, 20.0, 30.0]})
        got = dr._dash_colorvar_domain(df, {"colorvar": "price"})
        assert list(got) == [10.0, 20.0, 30.0]

    def test_a_date_series_reads_in_milliseconds(self):
        s = pd.Series(pd.to_datetime(["2001-01-02", None])).astype(
            "datetime64[ms]")
        got = dr._dash_colorvar_domain(pd.DataFrame({"d": s}),
                                       {"colorvar": "d"})
        assert got[0] == 978393600000.0 and math.isnan(got[1])

    def test_a_string_column_is_a_list(self):
        got = dr._dash_colorvar_domain(
            pd.DataFrame({"s": ["a", "", "b"]}), {"colorvar": "s"},
            [True, False, True])
        assert got == ["a", "b"]


class TestTheBinHelperOverADomain:
    """``_dash_colorvar_bins(..., bin_values=)``: labels from the domain,
    one bin per bin value."""

    def test_labels_come_from_the_domain(self):
        labels, _b, _m = dr._dash_colorvar_bins(
            np.array([0.0, 10.0]), [5.0], False, str, closed_ends=True,
            bin_values=np.array([2.0, 8.0]))
        assert labels == [f"0{_DASH}5", f"5{_DASH}10"]

    def test_one_bin_per_bin_value(self):
        _l, binned, _m = dr._dash_colorvar_bins(
            np.array([0.0, 10.0]), [5.0], False, str,
            bin_values=np.array([1.0, 6.0, 9.0, 5.0]))
        assert binned == [f"{_LE}5", ">5", ">5", f"{_LE}5"]

    def test_has_missing_comes_from_the_domain_only(self):
        _l, binned, has_missing = dr._dash_colorvar_bins(
            np.array([0.0, 10.0]), [5.0], False, str,
            bin_values=np.array([1.0, np.nan]))
        assert binned == [f"{_LE}5", None]
        assert has_missing is False
        _l, _b, has_missing = dr._dash_colorvar_bins(
            np.array([0.0, np.nan, 10.0]), [5.0], False, str,
            bin_values=np.array([1.0]))
        assert has_missing is True
        _l, _b, has_missing = dr._dash_colorvar_bins(
            np.array([1.0, 2.0]), [2.0], True, str,
            bin_values=np.array([2.0]))
        assert has_missing is True   # the domain's 1 equals no cut

    def test_a_value_outside_the_domain_is_none(self):
        labels, binned, _m = dr._dash_colorvar_bins(
            np.array([4.0, 10.0]), [7.0], False, str, closed_ends=True,
            bin_values=np.array([1.0, 5.0, 9.0, 12.0]))
        assert labels == [f"4{_DASH}7", f"7{_DASH}10"]
        assert binned == [None, f"4{_DASH}7", f"7{_DASH}10", None]

    def test_without_bin_values_the_domain_is_binned(self):
        labels, binned, has_missing = dr._dash_colorvar_bins(
            np.array([1.0, 2.0, 2.0, 3.0, np.nan]), [2.0], False,
            lambda v: f"{v:g}")
        assert labels == [f"{_LE}2", ">2"]
        assert binned == [f"{_LE}2", f"{_LE}2", f"{_LE}2", ">2", None]
        assert has_missing


class TestApplyColorvarOverADomain:
    """``_apply_colorvar`` reads the mapper's ``colorvar_domain``."""

    def test_rows_outside_the_domain_are_none_and_not_a_factor(self):
        src, rend, _f = _apply({"colordiscrete": "colordiscrete"},
                               [1.0, 2.0, 3.0, 4.0, 5.0],
                               domain=np.array([1.0, 2.0, 3.0]))
        assert list(cb.colour_mapper(rend).factors) == ["1", "2", "3"]
        assert cb.colour_values(rend) == ["1", "2", "3", None, None]

    def test_the_missing_entry_follows_the_domain(self):
        _s, _r, fig = _apply({"colorlevels": "2"}, [1.0, 2.0, np.nan, 4.0],
                             domain=np.array([1.0, 2.0, 4.0]))
        labels = [i.label for i in _colorvar_legend(fig).items]
        assert "(missing)" not in str(labels)
        _s, _r, fig = _apply({"colorlevels": "2"}, [1.0, 2.0, 3.0, 4.0],
                             domain=np.array([1.0, np.nan, 4.0]))
        labels = [i.label for i in _colorvar_legend(fig).items]
        assert "(missing)" in str(labels)

    def test_an_empty_domain_adds_no_key_and_raises_nothing(self):
        src, rend, fig = _apply({}, [1.0, 2.0], domain=np.array([]))
        assert cb.colour_keys(fig) == 0
        assert cb.colour_mapper(rend) is None
        assert set(src.data) == {"v", "y"}

    def test_an_all_missing_domain_keys_missing_only(self):
        _s, rend, fig = _apply({}, [1.0, np.nan],
                               domain=np.array([np.nan, np.nan]))
        assert list(cb.colour_mapper(rend).factors) == []
        assert cb.colour_values(rend) == [None, None]
        labels = [str(i.label) for i in _colorvar_legend(fig).items]
        assert len(labels) == 1 and "(missing)" in labels[0]

    def test_nan_color_is_colormissing(self):
        want = _mapper().tr.translate_mcolor("red")
        _s, rend, _f = _apply({"colordiscrete": "colordiscrete",
                               "colormissing": "red"}, [1.0, np.nan])
        assert cb.colour_mapper(rend).nan_color == want
        assert "__missing__" not in list(cb.colour_mapper(rend).factors)


def _two_price_layers():
    return tp._spec([
        tp.plot_for("scatter", {"colorvar": "price"},
                    if_expr="foreign == 1"),
        tp.plot_for("scatter", {"colorvar": "price"})])


class TestTheDomainIsReset:
    """The domain is set for every layer and reset after it, so no later
    layer, figure, render or exception inherits it."""

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_a_later_layer_is_not_restricted(self, mode):
        spec = _two_price_layers()
        if mode == "saved":
            _r, root = _saved_root(spec)
        else:
            root, _ = tp._served(spec)
        bars = cb.colour_bars(root)
        assert len(bars) == 2
        assert bars[0] == (4453.0, 11385.0)
        assert bars[1] == (3799.0, 11385.0)

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_the_attribute_is_none_after_the_render(self, mode):
        spec = _two_price_layers()
        if mode == "saved":
            r, _root = _saved_root(spec)
            assert r.mapper.colorvar_domain is None
        else:
            ns = _served_ns(spec)
            _session(ns)
            assert ns["_DASH_MAPPER"].colorvar_domain is None

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_the_attribute_is_none_after_a_layer_raises(self, mode,
                                                        monkeypatch):
        spec = _two_price_layers()

        def _boom(*a, **k):
            raise RuntimeError("boom")

        if mode == "saved":
            tag, sp, dp = tp._write(spec)
            r = dr.DashRenderer(sp, dp)
            monkeypatch.setattr(r.mapper, "map_scatter", _boom)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with pytest.raises(RuntimeError):
                    r.render()
            assert r.mapper.colorvar_domain is None
        else:
            ns = _served_ns(spec)
            monkeypatch.setattr(ns["_DASH_MAPPER"], "map_scatter", _boom)
            with pytest.raises(RuntimeError):
                _session(ns)
            assert ns["_DASH_MAPPER"].colorvar_domain is None


class TestTheColourFieldName:
    """Each layer's colour bins are a column of its own, under the
    reserved ``__dash_cvar`` prefix."""

    def test_the_field_helper_takes_the_first_free_name(self):
        p = dr._DASH_CVAR_PREFIX
        assert dr._dash_colorvar_field({}, "price") == f"{p}1_price"
        assert dr._dash_colorvar_field(
            {f"{p}1_price": [], f"{p}2_price": []}, "price") == f"{p}3_price"
        assert dr._dash_colorvar_field({}, "a b") is None

    @pytest.mark.parametrize("opts,values", [
        ({"colordiscrete": "colordiscrete"}, [1.0, 2.0]),
        ({"colorlevels": "3"}, [1.0, 2.0, 3.0, 4.0]),
        ({}, ["a", "b"]),
    ], ids=["colordiscrete", "colorlevels(3)", "string"])
    def test_a_derived_field_is_under_the_reserved_prefix(self, opts,
                                                          values):
        src, rend, _f = _apply(opts, values)
        field = cb.colour_field(rend)
        assert field.startswith(dr._DASH_CVAR_PREFIX)
        assert field in src.data and list(src.data["v"]) == values

    @pytest.mark.parametrize("mode", ["saved", "served-after-move"])
    def test_a_user_variable_named_like_the_old_field_is_untouched(
            self, mode, monkeypatch):
        frame = tp._DF.copy()
        frame["_cvar_price_bin"] = [float(i) for i in range(len(frame))]
        monkeypatch.setattr(tp, "_DF", frame)
        spec = tp._spec([
            tp.plot_for("scatter", {"colorvar": "price",
                                    "colorlevels": "3"}),
            tp.plot_for("scatter", {"colorvar": "_cvar_price_bin"})],
            {"filter": "foreign, type(dropdown)"})
        if mode == "saved":
            _r, root = _saved_root(spec)
        else:
            root, _ = tp._served(spec)
            _fire_select(root, "Foreign")
        rends = cb.colour_renderers(root)
        assert len(rends) == 2
        user = rends[1]
        assert cb.colour_field(user) == "_cvar_price_bin"
        m = cb.colour_mapper(user)
        assert isinstance(m, LinearColorMapper)
        if mode == "saved":
            assert (m.low, m.high) == (0.0, 9.0)
            assert list(user.data_source.data["_cvar_price_bin"]) == \
                [float(i) for i in range(10)]
        factors = set(cb.colour_mapper(rends[0]).factors)
        drawn = cb.drawn_colour_values(rends[0])
        assert drawn and all(v in factors for v in drawn), drawn

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_two_colorvar_layers_on_one_graph_keep_their_own_bins(self,
                                                                  mode):
        spec = tp._spec([
            tp.plot_for("scatter", {"colorvar": "price",
                                    "colorlevels": "3"}),
            tp.plot_for("scatter", {"colorvar": "price",
                                    "colorlevels": "5"})])
        root = (_saved_root(spec)[1] if mode == "saved"
                else tp._served(spec)[0])
        rends = cb.colour_renderers(root)
        assert len(rends) == 2
        # One source holds one column per layer; two sources may each
        # hold their own first name.
        assert (cb.colour_field(rends[0]) != cb.colour_field(rends[1])
                or rends[0].data_source is not rends[1].data_source)
        for r in rends:
            factors = set(cb.colour_mapper(r).factors)
            vals = [v for v in cb.drawn_colour_values(r) if v is not None]
            assert vals and set(vals) <= factors, (vals, factors)

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_two_linked_graphs_keep_their_own_bins(self, mode):
        spec = tp._spec(None, {"link": "g1 g2",
                               "filter": "price, type(range)"}, None,
                        [("g1", [tp.plot_for("scatter", {
                            "colorvar": "price", "colorlevels": "3"})]),
                         ("g2", [tp.plot_for("scatter", {
                             "colorvar": "price", "colorlevels": "5"})])])

        def check(root):
            rends = cb.colour_renderers(root)
            assert len(rends) == 2
            assert cb.colour_field(rends[0]) != cb.colour_field(rends[1])
            for r in rends:
                factors = set(cb.colour_mapper(r).factors)
                n = len(next(iter(r.data_source.data.values())))
                assert len(cb.colour_values(r)) == n
                vals = [v for v in cb.drawn_colour_values(r)
                        if v is not None]
                assert vals and set(vals) <= factors, (vals, factors)

        if mode == "saved":
            r, root = _saved_root(spec)
            check(root)
            ws = [w for w in r.filter_widgets
                  if type(w).__name__ == "RangeSlider"]
            ws[0].value = (4500.0, 11385.0)
            i = r.filter_widgets.index(ws[0])
            JsSession([]).run_code(r.filter_callbacks[i].code,
                                   r.filter_callbacks[i].args)
            check(root)
        else:
            doc, _ = tp._served(spec)
            check(doc)
            _fire_range(doc, (4500.0, 11385.0))
            check(doc)


class TestAValueLabelCalledMissing:
    """A value label's text is a level, whatever it says, and missing is
    missing (BR-07.5)."""

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_a_label_is_a_level_and_missing_is_missing(self, mode,
                                                       monkeypatch):
        frame = tp._DF.copy()
        frame.loc[0, "rep"] = np.nan
        monkeypatch.setattr(tp, "_DF", frame)
        monkeypatch.setattr(tp, "_VALUE_LABELS", dict(
            tp._VALUE_LABELS, replab={"3": "__missing__", "4": "four"}))
        monkeypatch.setattr(tp, "_LABEL_NAMES", dict(
            tp._LABEL_NAMES, rep="replab"))
        spec = tp._spec([tp.plot_for("scatter", {
            "colorvar": "rep", "colordiscrete": "colordiscrete"})])
        root = (_saved_root(spec)[1] if mode == "saved"
                else tp._served(spec)[0])
        (rend,) = cb.colour_renderers(root)
        m = cb.colour_mapper(rend)
        assert list(m.factors) == ["__missing__", "four", "5"]
        assert len(m.palette) == len(m.factors)
        assert cb.colour_values(rend)[0] is None
        assert m.nan_color == "#808080"
        (fig,) = cb._figures(root)
        labels = [str(getattr(i.label, "value", i.label))
                  for i in _colorvar_legend(fig).items]
        assert labels[-1].endswith("(missing)"), labels


class TestOneKeyPerLayer:
    """twoway draws one key for an rconnected plot (E-16.2)."""

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_rconnected_draws_one_key(self, mode):
        spec = tp._spec([tp.plot_for("rconnected", {"colorvar": "price"})])
        root = (_saved_root(spec)[1] if mode == "saved"
                else tp._served(spec)[0])
        assert cb.colour_keys(root) == 1
        scat = [r for r in cb.colour_renderers(root)
                if type(r.glyph).__name__ == "Scatter"]
        assert len(scat) >= 2


class TestTheServedRedrawKeepsTheBuildDomain:
    """A served redraw keeps the build's bins (amendment 6)."""

    def test_a_redrawn_copy_keeps_the_build_bins(self):
        spec = tp._spec([tp.plot_for("rconnected", {
            "colorvar": "price", "colorlevels": "3"})],
            {"filter": "price, type(range)"})
        doc, _ = tp._served(spec)
        rends = cb.colour_renderers(doc)
        factors = set()
        fields = set()
        for r in rends:
            factors |= set(cb.colour_mapper(r).factors)
            fields.add(cb.colour_field(r))
        _fire_range(doc, (4500.0, 11385.0))
        bad = {}
        for m in doc.select({"type": ColumnDataSource}):
            for f in fields:
                for v in m.data.get(f, []):
                    if v is not None and v not in factors:
                        bad.setdefault(f, set()).add(v)
        assert not bad, f"values outside the build's factors {factors}: {bad}"
