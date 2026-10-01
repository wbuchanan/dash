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
from conftest import make_spec, make_data_json  # noqa: E402

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
    return list(src.data["_cvar_v_bin"]), list(
        rend.glyph.fill_color["transform"].factors)


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
        assert got == ["__missing__", "2", "__missing__", "4",
                       "__missing__", "__missing__"]
        assert factors == ["2", "4", "__missing__"]


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
        assert factors == ["3", "6", "9", "__missing__"]
        assert got == ["__missing__", "3", "6", "9", "__missing__"]


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
        assert binned == [f"{_LE}2", f"{_LE}2", f"{_LE}2", ">2",
                          "__missing__"]
        assert has_missing

        labels2, binned2, has_missing2 = dr._dash_colorvar_bins(
            vals, [2.0], True, lambda v: f"{v:g}")
        assert labels2 == ["2"]
        assert binned2 == ["__missing__", "2", "2", "__missing__",
                           "__missing__"]
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
        assert binned == ["__missing__", "__missing__", "__missing__"]
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
        assert isinstance(bar2.ticker, BasicTicker)
        assert bar2.ticker.desired_num_ticks == 3

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
            go={"zlabel": "1(1)5, format(%9.2f)"}, plots=plots)
        assert any("format(%9.2f)" in w for w in std_w3)

    def test_ztitle_suboptions_keep_the_key_title(self):
        """WP-29 P0.4: ztitle() with only sub-options keeps the colour
        variable's title and styles it, as twoway draws it (f1, f2); a typed
        "" still removes it (f3).  It emptied the key's title."""
        large = f"{dr._textbox_size({'size': 'large'}, None):g}px"
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
        colorvar = opts["colorvar"]
        col = f"_cvar_{colorvar}_bin"

        def _bin_column(fig_or_doc):
            for m in fig_or_doc.select({"type": ColumnDataSource}):
                if col in m.data:
                    return list(m.data[col])
            return None

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
