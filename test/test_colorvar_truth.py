"""test_colorvar_truth.py -- dash's colorvar() groups against twoway's own
(GAPS2 X2).

test/fixtures/colorvar_truth.json is written by
scripts/extract_colorvar_truth.do: for each probe, twoway's exported SVG
is read through scripts/svg_truth.py and every in-region marker's fill is
recorded in document order, which the fixture's self-check proves is
observation order.  Each probe's options are rendered through dash's own
mapper over the same column, and the partition of observations by dash's
colour factor must equal the partition by twoway's fill.
"""
import json
import math
import os
import re
import sys
import warnings

import numpy as np
import pytest
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402

sys.path.insert(0, _HERE)
import colour_bins as cb  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "colorvar_truth.json")


def _truth():
    if not os.path.exists(_FIXTURE):
        pytest.fail("section 16 task 16-03 must land first: "
                    "test/fixtures/colorvar_truth.json is missing")
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _probe_ids():
    # WP-33 CV-16's cv16_* probes (other plot types, by(), a refusal) are
    # compared by TestTheKeyAgainstTwoway, TestEveryTypeColours and
    # TestTheRefusals below; this partition test reads scatter markers.
    if not os.path.exists(_FIXTURE):
        return ["missing-fixture"]
    with open(_FIXTURE, encoding="utf-8") as fh:
        return sorted(p for p in json.load(fh)["probes"]
                      if not p.startswith("cv16_"))


_FLAGS = ("colordiscrete", "colorvarminmax")
_VALUED = ("colorvar", "colorcuts", "colorlevels")


def _opts_of(command):
    """The colorvar options of a twoway command line (test helper only)."""
    out = {}
    for k in _VALUED:
        m = re.search(r"\b%s\(([^)]*)\)" % k, command)
        if m:
            out[k] = m.group(1).strip()
    for k in _FLAGS:
        if re.search(r"\b%s\b" % k, command):
            out[k] = k
    return out


def _canonical(labels):
    seen, out = {}, []
    for lab in labels:
        seen.setdefault(lab, len(seen))
        out.append(seen[lab])
    return out


class TestAgainstTwoway:

    @pytest.mark.parametrize("pid", _probe_ids())
    def test_every_probe_partitions_the_observations_as_twoway_does(self, pid):
        truth = _truth()
        probe = truth["probes"][pid]
        if "twoway_rc" in probe:
            # A refusal probe: dash answers with twoway's return code.
            assert probe["rc"] == probe["twoway_rc"], probe
            return
        assert probe["rc"] == 0
        col = truth["_data"][probe["dataset"]]
        opts = _opts_of(probe["command"])
        values = [np.nan if v is None else v for v in col[opts["colorvar"]]]
        assert probe["n_markers"] == len(values)
        # Flipped (WP-33 CV-16): the continuous default is compared.
        if not ({"colordiscrete", "colorcuts", "colorlevels"} & set(opts)):
            gm = dr.GlyphMapper(dr.OptionTranslator(),
                                dr.SchemeParser("s2color"))
            src = ColumnDataSource({"v": values, "y": [1.0] * len(values)})
            fig = figure()
            rend = fig.scatter(x="v", y="y", source=src)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                gm._apply_colorvar(fig, rend, src, dict(opts, colorvar="v"))
            got = [_cv_colour(cb.colour_mapper(rend), v)
                   for v in cb.colour_values(rend)]
            assert len(got) == probe["n_markers"], pid
            # Flipped (WP-42 CV-8): the continuous key was a 256-step
            # gradient; twoway bins at its z ticks (CV-8), so the
            # partition is compared too.  zlabel() moves the cuts and is
            # not read by this mapper alone (TestEveryTypeColours draws
            # it); zscale(log) and zscale(reverse) keep the linear levels.
            if "zlabel(" not in probe["command"]:
                assert len(set(got)) == probe["n_groups"], (pid, set(got))
                if truth["_meta"]["marker_order_selfcheck"] == "observation":
                    assert _canonical(got) == _canonical(
                        probe["fill_groups"]), pid
            return
        gm = dr.GlyphMapper(dr.OptionTranslator(), dr.SchemeParser("s2color"))
        src = ColumnDataSource({"v": values, "y": [1.0] * len(values)})
        fig = figure()
        rend = fig.scatter(x="v", y="y", source=src)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            gm._apply_colorvar(fig, rend, src, dict(opts, colorvar="v"))
        # WP-29 P0.16: the missing sentinel is None / the colour column is named under __dash_cvar.
        binned = cb.colour_values(rend)
        assert len(set(binned)) == probe["n_groups"], (pid, sorted(set(binned)))
        if truth["_meta"]["marker_order_selfcheck"] == "observation":
            assert _canonical(binned) == _canonical(probe["fill_groups"]), pid
        else:
            assert sorted(np.bincount(_canonical(binned))) == \
                sorted(np.bincount(probe["fill_groups"]))

    def test_the_fixture_self_check_held(self):
        assert _truth()["_meta"]["marker_order_selfcheck"] == "observation"

    def test_the_fixture_meta_carries_the_four_provenance_keys(self):
        meta = _truth()["_meta"]
        for key in ("stata_version", "born_date", "dash_commit", "extracted"):
            assert key in meta


# ---------------------------------------------------------------------------
# colorlevels() outside 2..100, as twoway draws it (measured 30sep2026,
# StataNow 19, `twoway scatter mpg weight, colorvar(price) colorlevels(#)',
# exported SVG): 0 and 1 draw twoway's default (the z axis's ticks, as if
# the option were absent); 2 to 100 draw exactly # levels; a negative
# number or one over 100 (101, 110, 128, 150, 199, 200, 255, 256, 257,
# 300, 1000000) draws the same five levels and cuts (5,814 8,337 10,860
# 13,383 on price) as colorlevels(5); 2.5 is r(198).
# ---------------------------------------------------------------------------

def _cv_bins(opts, values):
    gm = dr.GlyphMapper(dr.OptionTranslator(), dr.SchemeParser("s2color"))
    src = ColumnDataSource({"v": list(values), "y": [1.0] * len(values)})
    fig = figure()
    rend = fig.scatter(x="v", y="y", source=src)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        gm._apply_colorvar(fig, rend, src, dict(opts, colorvar="v"))
    return {k: list(v) for k, v in src.data.items() if k != "v"}, rend


_CV_VALUES = [float(v) for v in range(1, 301)]


class TestColorlevelsOutsideTwoToAHundred:

    @pytest.mark.parametrize("n", ["0", "1"])
    def test_zero_and_one_draw_as_if_absent(self, n):
        got, rend = _cv_bins({"colorlevels": n}, _CV_VALUES)
        want, wrend = _cv_bins({}, _CV_VALUES)
        assert got == want
        g, w = rend.glyph.fill_color, wrend.glyph.fill_color
        assert type(g) is type(w)
        if hasattr(g, "transform"):
            assert g.field == w.field
            assert g.transform.properties_with_values(
                include_defaults=False).keys() == \
                w.transform.properties_with_values(
                    include_defaults=False).keys()
            for k in ("palette", "low", "high"):
                assert getattr(g.transform, k) == getattr(w.transform, k)
        else:
            assert g == w

    @pytest.mark.parametrize("n", ["-1", "-5", "101", "256", "257",
                                   "1000000"])
    def test_negative_or_over_a_hundred_draws_five_levels(self, n):
        got, rend = _cv_bins({"colorlevels": n}, _CV_VALUES)
        want, _ = _cv_bins({"colorlevels": "5"}, _CV_VALUES)
        assert got == want
        # WP-29 P0.16: the missing sentinel is None / the colour column is named under __dash_cvar.
        assert len(set(cb.colour_values(rend))) == 5

    @pytest.mark.parametrize("n", [2, 3, 50, 100])
    def test_two_to_a_hundred_draw_exactly_that_many(self, n):
        _got, rend = _cv_bins({"colorlevels": str(n)}, _CV_VALUES)
        # WP-29 P0.16: the missing sentinel is None / the colour column is named under __dash_cvar.
        assert len(set(cb.colour_values(rend))) == n


# ---------------------------------------------------------------------------
# WP-29 P0.16: the key is drawn from the layer's own rows, as twoway draws it
# (test/fixtures/colorvar_qualifier_truth.json, written by
# scripts/extract_colorvar_qualifier_truth.do in StataNow 19.5).
# ---------------------------------------------------------------------------

import pandas as pd  # noqa: E402

import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_QFIXTURE = os.path.join(_HERE, "fixtures", "colorvar_qualifier_truth.json")


def _qtruth():
    if not os.path.exists(_QFIXTURE):
        pytest.fail("WP-29 task 07-05 must land first: "
                    "test/fixtures/colorvar_qualifier_truth.json is missing")
    with open(_QFIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _auto_frame():
    """auto's columns from the fixture, with y2 and x2 as Stata built them
    (missing where price >= 15000)."""
    d = _qtruth()["_data"]["auto"]
    df = pd.DataFrame({k: [np.nan if v is None else float(v) for v in vs]
                       for k, vs in d.items()})
    df["y2"] = df["mpg"].where(df["price"] < 15000)
    df["x2"] = df["weight"].where(df["price"] < 15000)
    df = df.rename(columns={"rep78": "rep78"})
    return df


def _stepped_bar(lo, hi):
    """WP-42 CV-8: (low, high) of the stepped key's bar over a layer's
    rows *lo* .. *hi*: the key's ticks (natscale #5), the cuts those at or
    above *lo*, one step beyond the first and the last."""
    t = dr._dash_cvar_ticks(lo, hi, {"mode": "auto"})
    cuts = [x for x in t if x >= lo] or [lo]
    step = ((cuts[-1] - cuts[0]) / (len(cuts) - 1) if len(cuts) > 1
            else max(abs(hi - cuts[0]), abs(cuts[0] - lo), 1.0))
    return (cuts[0] - step, cuts[-1] + step)


def _render(spec, mode):
    if mode == "saved":
        r, _ = tp._standalone(spec)
        return r._last_layout_root
    doc, _ = tp._served(spec)
    return doc


def _colour_figs(root):
    return [f for f in cb._figures(root) if cb.colour_renderers(f)]


def _bounds(rend):
    """Every interval bound of *rend*'s factors, sorted."""
    out = set()
    for lo, hi in cb.interval_bounds(cb.colour_mapper(rend).factors):
        out |= {b for b in (lo, hi) if b is not None}
    return sorted(out)


def _key_numbers(texts):
    out = []
    for t in texts:
        try:
            out.append(float(t.replace(",", "")))
        except ValueError:
            pass
    return out


def _linked_spec(plots, go=None, if_expr="", linked=False, bo=None):
    """One graph, or (linked) the graph g1 linked with a plain g2."""
    if not linked:
        return tp._spec(plots, bo, go, None, None, if_expr)
    return tp._spec(None, dict(bo or {}, link="g1 g2"), None,
                    [("g1", plots, go, {"if_expr": if_expr}),
                     ("g2", [plot_for("scatter")])])


_MODES = ["saved", "served"]


class TestTheKeyIsDrawnFromTheLayersRows:
    """twoway draws a colorvar() key from the observations the plot draws:
    its own if/in, the graph's if/in and its by() panel, counting an
    observation whose y or x is missing."""

    @pytest.fixture(autouse=True)
    def _auto(self, monkeypatch):
        monkeypatch.setattr(tp, "_DF", _auto_frame())

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_layers_own_if(self, mode):
        p = _qtruth()["probes"]["q_if_cont"]
        spec = tp._spec([
            plot_for("scatter", {"colorvar": "price"},
                     if_expr="foreign == 1"),
            plot_for("scatter", if_expr="foreign == 0")])
        # Flipped (WP-42 CV-8): the continuous key was a 256-step gradient; twoway bins at its z ticks (CV-8); the bar is the stepped key over
        # the layer's own rows.
        assert cb.colour_bars(_render(spec, mode)) == [
            _stepped_bar(p["summ_min"], p["summ_max"])]

    @pytest.mark.parametrize("mode", _MODES)
    def test_colordiscrete_levels_of_a_layers_own_if(self, mode):
        spec = tp._spec([
            plot_for("scatter", {"colorvar": "rep78",
                                 "colordiscrete": "colordiscrete"},
                     if_expr="foreign == 1"),
            plot_for("scatter", if_expr="foreign == 0")])
        root = _render(spec, mode)
        (rend,) = cb.colour_renderers(root)
        assert list(cb.colour_mapper(rend).factors) == ["3", "4", "5"]
        (fig,) = _colour_figs(root)
        legs = [a for a in fig.right if type(a).__name__ == "Legend"
                and a.name == dr._COLORVAR_LEGEND_NAME]
        last = legs[0].items[-1].label
        assert "(missing)" in str(getattr(last, "value", last))

    @pytest.mark.parametrize("mode", _MODES)
    def test_colorlevels_cuts_of_a_layers_own_if(self, mode):
        truth = _qtruth()
        p = truth["probes"]["q_if_lv3"]
        spec = tp._spec([
            plot_for("scatter", {"colorvar": "price", "colorlevels": "3"},
                     if_expr="foreign == 1"),
            plot_for("scatter", if_expr="foreign == 0")])
        root = _render(spec, mode)
        (rend,) = cb.colour_renderers(root)
        b = _bounds(rend)
        assert b[0] == 3748.0 and b[-1] == 12990.0, b
        # WP-30 P1.23b: a bound read from a :g label was wrong because the
        # key is twoway's %8.0gc, 6,828.7 and 9,909.3, which the fixture's
        # key_texts hold.
        assert b[1:3] == [6828.7, 9909.3], b
        keys = _key_numbers(p["key_texts"])
        assert [round(x, 1) for x in b[1:3]] == [6828.7, 9909.3]
        assert {6828.7, 9909.3} <= set(keys), keys
        drawn = cb.drawn_colour_values(rend)
        n = len(p["qual_obs"])
        assert len(drawn) == n == 22
        assert _canonical(drawn) == _canonical(p["fills"][:n])

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_linked_graphs_own_if(self, mode):
        p = _qtruth()["probes"]["q_cmd_if"]
        spec = _linked_spec([plot_for("scatter", {"colorvar": "price"})],
                            if_expr="foreign == 1", linked=True)
        # Flipped (WP-42 CV-8): the continuous key was a 256-step gradient; twoway bins at its z ticks (CV-8).
        assert cb.colour_bars(_render(spec, mode)) == [
            _stepped_bar(p["summ_min"], p["summ_max"])]

    @pytest.mark.parametrize("linked", [False, True],
                             ids=["unlinked", "linked"])
    @pytest.mark.parametrize("mode", _MODES)
    def test_each_by_panel_maps_its_own_rows(self, mode, linked):
        probes = _qtruth()["probes"]
        spec = _linked_spec([plot_for("scatter", {"colorvar": "price",
                                                  "colorlevels": "4"})],
                            go={"by": "foreign"}, linked=linked)
        figs = _colour_figs(_render(spec, mode))
        assert len(figs) == 2
        for fig, pid in zip(figs, ("by_lv4_p0", "by_lv4_p1")):
            p = probes[pid]
            (rend,) = cb.colour_renderers(fig)
            b = _bounds(rend)
            assert (b[0], b[-1]) == (p["summ_min"], p["summ_max"]), (pid, b)
            drawn = cb.drawn_colour_values(rend)
            n = len(p["qual_obs"])
            assert len(drawn) == n
            assert _canonical(drawn) == _canonical(p["fills"][:n]), pid
        # Flipped (WP-30 P1.15c): a colour bar on every panel was wrong;
        # twoway draws no colour key under by() unless by(, clegend(on))
        # (by_chrome_truth.json q06), then one, showing panel 1's mapping
        # (q07).  Each panel's own mapping, above, is unchanged.
        spec = _linked_spec([plot_for("scatter", {"colorvar": "price"})],
                            go={"by": "foreign"}, linked=linked)
        assert [cb.colour_bars(f) for f in
                _colour_figs(_render(spec, mode))] == [[], []]
        spec = _linked_spec([plot_for("scatter", {"colorvar": "price"})],
                            go={"by": "foreign, clegend(on)"}, linked=linked)
        root = _render(spec, mode)
        roots = list(getattr(root, "roots", None) or [root])
        cells = [m for r in roots for m in r.references()
                 if getattr(m, "name", None) == "dash_by_clegend"]
        assert len(cells) == 1
        bars = [(a.color_mapper.low, a.color_mapper.high)
                for side in ("left", "right", "above", "below")
                for a in getattr(cells[0], side)
                if type(a).__name__ == "ColorBar"]
        # Flipped (WP-42 CV-8): the continuous key was a 256-step gradient; twoway bins at its z ticks (CV-8); panel 1's stepped key.
        assert bars == [_stepped_bar(probes["by_lv4_p0"]["summ_min"],
                                     probes["by_lv4_p0"]["summ_max"])]

    def _one_cut(self, mode, linked, ptype, y, x, pid):
        p = _qtruth()["probes"][pid]
        spec = _linked_spec([dict(plot_for(ptype, {"colorvar": "price",
                                                   "colorlevels": "2"}),
                                  yvar=y, xvar=x)], linked=linked)
        rends = cb.colour_renderers(_render(spec, mode))
        assert rends
        for rend in rends:
            b = _bounds(rend)
            assert len(b) == 3 and b[1] == 9598.5, (pid, b)
        assert 9598.5 in _key_numbers(p["key_texts"])

    @pytest.mark.parametrize("linked", [False, True],
                             ids=["unlinked", "linked"])
    @pytest.mark.parametrize("mode", _MODES)
    def test_rows_with_a_missing_y_count(self, mode, linked):
        self._one_cut(mode, linked, "scatter", "y2", "weight",
                      "missing_y_lv2")

    @pytest.mark.parametrize("linked", [False, True],
                             ids=["unlinked", "linked"])
    @pytest.mark.parametrize("mode", _MODES)
    def test_rows_with_a_missing_x_count(self, mode, linked):
        self._one_cut(mode, linked, "scatter", "mpg", "x2",
                      "missing_x_lv2")

    @pytest.mark.parametrize("linked", [False, True],
                             ids=["unlinked", "linked"])
    @pytest.mark.parametrize("mode", _MODES)
    def test_a_connected_layer_with_a_missing_y_counts(self, mode, linked):
        self._one_cut(mode, linked, "connected", "y2", "weight",
                      "missing_y_connected")

    def test_the_qualifier_fixture_carries_its_provenance_and_self_checks(
            self):
        truth = _qtruth()
        meta, probes = truth["_meta"], truth["probes"]
        for key in ("stata_version", "born_date", "dash_commit",
                    "extracted"):
            assert key in meta
        assert meta["qualified_order_selfcheck"] == "held"
        assert meta["by_panel_selfcheck"] == "held"
        assert probes["rconnected_key"]["key_title_count"] == 1
        assert probes["multi_colorvar"]["rc"] == 198
        assert probes["empty_layer"]["rc"] == 3001



# ---------------------------------------------------------------------------
# WP-33 33-13 (CV-16): the colour key's texts, order and frame, and each
# plot type's colours, against twoway's exported SVG, in both modes
# (test/fixtures/colorvar_truth.json, scripts/extract_colorvar_truth.do).
# ---------------------------------------------------------------------------

import functools  # noqa: E402

from known_differences import dead_rows, known_problems  # noqa: E402

#: Every probe of colorvar_truth.json, written out so collection never
#: depends on the fixture: the 18 of WP-28 S16, then D-33-13.e's 22.
_CV_PROBES = (
    "selfcheck_foreign", "default_rep78", "disc_rep78", "disc_cuts_2_4",
    "cuts_2_4", "cuts_0_2_4", "disc_cuts_0_2_4", "cuts_all_below",
    "levels_price_4", "levels_price_4_minmax", "cuts_price_minmax",
    "disc_levels_price_4", "ztitle_disc", "zlabel_price", "zscale_log",
    "zscale_rev", "cuts_and_levels", "levels_twice",
    "cv16_line_disc_rep78", "cv16_line_levels_price_4",
    "cv16_connected_disc_rep78", "cv16_connected_levels_price_4",
    "cv16_bar_disc_rep78", "cv16_bar_levels_price_4",
    "cv16_spike_disc_rep78", "cv16_spike_levels_price_4",
    "cv16_rcap_disc_rep78", "cv16_rcap_levels_price_4",
    "cv16_pcspike_disc_rep78", "cv16_pcspike_levels_price_4",
    "cv16_bar_fillonly", "cv16_line_fillonly", "cv16_line_plegend",
    "cv16_bar_keysrange", "cv16_line_cuts_list", "cv16_scatter_by",
    "cv16_two_layers", "cv16_legend_rows2", "cv16_disc_levels_rep78_3",
    "cv16_zlabel_bogus",
)
#: The refusal probes: twoway's rc and first line, no SVG.
_CV_REFUSALS = ("cuts_and_levels", "levels_twice", "cv16_zlabel_bogus")
_CV_DRAWN = tuple(p for p in _CV_PROBES if p not in _CV_REFUSALS)

#: D-33-13.f: each difference keyed "<probe>:<check>" to the live GAPS4
#: item that fixes it (known_differences.py's rules), measured 21oct2026,
#: the same in both modes (WP-42 CV-1 closed colorfillonly's line
#: colours, WP-42 CV-2 the colordiscrete + colorlevels(k) cuts).  CV-3: the
#: discrete/binned clegend (ascending, value labels and interval texts,
#: '(missing)', a frame); CV-4: the coloruseplegend key (WP-42 CV-6
#: closed the key a layer of two colorvar layers); CV-8: the continuous default's gradient and ColorBar
#: (zscale(log) and zscale(reverse) included); CV-10: zlabel(bogus) drawn
#: where twoway refuses r(198).
COLORVAR_KNOWN = {
    "selfcheck_foreign:key_texts": "CV-3",
    "selfcheck_foreign:key_frame": "CV-3",
    "disc_rep78:key_texts": "CV-3",
    "disc_rep78:key_frame": "CV-3",
    "disc_cuts_2_4:key_texts": "CV-3",
    "disc_cuts_2_4:key_frame": "CV-3",
    "cuts_2_4:key_texts": "CV-3",
    "cuts_2_4:key_frame": "CV-3",
    "cuts_0_2_4:key_texts": "CV-3",
    "cuts_0_2_4:key_frame": "CV-3",
    "disc_cuts_0_2_4:key_texts": "CV-3",
    "disc_cuts_0_2_4:key_frame": "CV-3",
    "cuts_all_below:key_texts": "CV-3",
    "cuts_all_below:key_frame": "CV-3",
    "levels_price_4:key_texts": "CV-3",
    "levels_price_4:key_frame": "CV-3",
    "levels_price_4_minmax:key_texts": "CV-3",
    "levels_price_4_minmax:key_frame": "CV-3",
    "cuts_price_minmax:key_texts": "CV-3",
    "cuts_price_minmax:key_frame": "CV-3",
    # WP-42 CV-2 closed the cuts: the texts left differ as CV-3's
    # (ascending, '(missing)').
    "disc_levels_price_4:key_texts": "CV-3",
    "disc_levels_price_4:key_frame": "CV-3",
    "ztitle_disc:key_texts": "CV-3",
    "ztitle_disc:key_frame": "CV-3",
    # WP-42 CV-8 closed the levels; the key drawn upside down under
    # zscale(reverse) is the key cell's (42-03, CV-3).
    "zscale_rev:key_texts": "CV-3",
    "cv16_line_disc_rep78:key_texts": "CV-3",
    "cv16_line_disc_rep78:key_frame": "CV-3",
    "cv16_line_levels_price_4:key_texts": "CV-3",
    "cv16_line_levels_price_4:key_frame": "CV-3",
    "cv16_connected_disc_rep78:key_texts": "CV-3",
    "cv16_connected_disc_rep78:key_frame": "CV-3",
    "cv16_connected_levels_price_4:key_texts": "CV-3",
    "cv16_connected_levels_price_4:key_frame": "CV-3",
    "cv16_bar_disc_rep78:key_texts": "CV-3",
    "cv16_bar_disc_rep78:key_frame": "CV-3",
    "cv16_bar_levels_price_4:key_texts": "CV-3",
    "cv16_bar_levels_price_4:key_frame": "CV-3",
    "cv16_spike_disc_rep78:key_texts": "CV-3",
    "cv16_spike_disc_rep78:key_frame": "CV-3",
    "cv16_spike_levels_price_4:key_texts": "CV-3",
    "cv16_spike_levels_price_4:key_frame": "CV-3",
    "cv16_rcap_disc_rep78:key_texts": "CV-3",
    "cv16_rcap_disc_rep78:key_frame": "CV-3",
    "cv16_rcap_levels_price_4:key_texts": "CV-3",
    "cv16_rcap_levels_price_4:key_frame": "CV-3",
    "cv16_pcspike_disc_rep78:key_texts": "CV-3",
    "cv16_pcspike_disc_rep78:key_frame": "CV-3",
    "cv16_pcspike_levels_price_4:key_texts": "CV-3",
    "cv16_pcspike_levels_price_4:key_frame": "CV-3",
    "cv16_bar_fillonly:key_texts": "CV-3",
    "cv16_bar_fillonly:key_frame": "CV-3",
    "cv16_line_fillonly:key_texts": "CV-3",
    "cv16_line_fillonly:key_frame": "CV-3",
    "cv16_line_plegend:key_texts": "CV-4",
    "cv16_line_plegend:key_frame": "CV-4",
    "cv16_bar_keysrange:key_texts": "CV-3",
    "cv16_bar_keysrange:key_frame": "CV-3",
    "cv16_line_cuts_list:key_texts": "CV-3",
    "cv16_line_cuts_list:key_frame": "CV-3",
    # WP-42 CV-6 closed the key a layer: the one key left is the last
    # layer's discrete key, drawn as CV-3's (ascending, '(missing)', a
    # frame), as disc_rep78's is.
    "cv16_two_layers:key_texts": "CV-3",
    "cv16_two_layers:key_frame": "CV-3",
    "cv16_legend_rows2:key_texts": "CV-3",
    "cv16_legend_rows2:key_frame": "CV-3",
    "cv16_disc_levels_rep78_3:key_texts": "CV-3",
    "cv16_disc_levels_rep78_3:key_frame": "CV-3",
    "cv16_zlabel_bogus:rc": "CV-10",
}
COLORVAR_DELIBERATE = {}

#: D-33-13.g: a probe twoway draws in one colour, with the reason.
_ONE_GROUP_BY_TWOWAY = {
    "disc_levels_price_4": "twoway draws every marker #808080 (measured); "
                           "cv16_disc_levels_rep78_3 is the non-vacuous "
                           "probe of the combination",
}

_CV_PLOT_KEYS = ("colorvar", "colordiscrete", "colorcuts", "colorlevels",
                 "colorvarminmax", "colorfillonly", "coloruseplegend",
                 "colorkeysrange", "colorlist", "colorallowmultiple", "sort")
_CV_GRAPH_KEYS = ("by", "legend", "ztitle", "zlabel", "zscale")
_CV_OPT = re.compile(r"(\w+)(\((?:[^()]|\([^()]*\))*\))?")


def _cv_split(text, sep):
    """*text* split at *sep* outside parentheses and quotes."""
    out, depth, quote, cur = [], 0, False, ""
    for ch in text:
        if ch == '"':
            quote = not quote
        elif not quote and ch == "(":
            depth += 1
        elif not quote and ch == ")":
            depth -= 1
        if ch == sep and depth == 0 and not quote:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    return out


def _cv_options(text):
    """{option: value} of an option list (a flag's value is its name)."""
    out = {}
    for m in _CV_OPT.finditer(text or ""):
        out[m.group(1)] = (m.group(2)[1:-1].strip() if m.group(2)
                           else m.group(1))
    return out


def _cv_spec(probe):
    """(plots, graph options) of a probe's twoway command, as dash.ado
    writes them (test_server_layer_defects.plot_for's shapes)."""
    cmd = probe["command"].strip()
    assert cmd.startswith("twoway "), cmd
    body = cmd[len("twoway "):].strip()
    if body.startswith("("):
        parts, gopts, depth, cur = [], "", 0, ""
        i = 0
        while i < len(body):
            ch = body[i]
            if ch == "(":
                depth += 1
                if depth == 1:
                    cur = ""
                    i += 1
                    continue
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    parts.append(cur)
                    i += 1
                    continue
            if depth == 0 and ch == ",":
                gopts = body[i + 1:]
                break
            if depth >= 1:
                cur += ch
            i += 1
        layers = parts
    else:
        head, _sep, rest = body.partition(",")
        layers, gopts = [head + "," + rest], rest
    plots, graph = [], {}
    for layer in layers:
        head, _sep, rest = layer.partition(",")
        words = head.split()
        ptype, vs = words[0], words[1:]
        opts = _cv_options(rest)
        for k in _CV_GRAPH_KEYS:
            if k in opts:
                graph[k] = opts.pop(k)
        p = plot_for(ptype, {k: v for k, v in opts.items()
                             if k in _CV_PLOT_KEYS})
        if ptype == "rcap":
            p.update(yvar1=vs[0], yvar2=vs[1], xvar=vs[2])
        elif ptype == "pcspike":
            p.update(y1var=vs[0], x1var=vs[1], y2var=vs[2], x2var=vs[3])
        else:
            p.update(yvar=vs[0], xvar=vs[1])
        plots.append(p)
    for k, v in _cv_options(gopts).items():
        if k in _CV_GRAPH_KEYS:
            graph[k] = v
    return plots, graph


def _cv_frame():
    d = _truth()["_data"]["auto"]
    return pd.DataFrame({k: [np.nan if v is None else float(v) for v in vs]
                         for k, vs in d.items()})


@functools.lru_cache(maxsize=None)
def _cv_models(mode, pid):
    """The models dash draws for probe *pid* in *mode* (saved: the
    renderer's layout root; served: the app's Document)."""
    plots, graph = _cv_spec(_truth()["probes"][pid])
    spec = tp._spec(plots, None, graph or None)
    saved_df = tp._DF
    tp._DF = _cv_frame()
    try:
        return _render(spec, mode)
    finally:
        tp._DF = saved_df


def _cv_hex(c):
    """A colour as lower-case #rrggbb (a Bokeh/CSS name converted)."""
    c = str(c).strip().lower()
    if c.startswith("#") and len(c) == 7:
        return c
    if c.startswith("#") and len(c) == 9:
        return c[:7]
    from bokeh.colors import named
    nc = getattr(named, c, None)
    return nc.to_hex().lower() if nc is not None else c


def _cv_colour(mapper, value):
    """The colour Bokeh draws *value* in through *mapper*."""
    nan = _cv_hex(mapper.nan_color)
    if value is None or (isinstance(value, float) and value != value):
        return nan
    pal = [_cv_hex(c) for c in mapper.palette]
    name = type(mapper).__name__
    if name == "CategoricalColorMapper":
        fac = list(mapper.factors)
        if value not in fac:
            return nan
        i = fac.index(value)
        return pal[i] if i < len(pal) else nan
    v = float(value)
    lo, hi = float(mapper.low), float(mapper.high)
    if name == "LogColorMapper":
        v, lo, hi = math.log(v), math.log(lo), math.log(hi)
    if v < lo:
        return _cv_hex(mapper.low_color) if mapper.low_color else pal[0]
    if v > hi:
        return _cv_hex(mapper.high_color) if mapper.high_color else pal[-1]
    if hi == lo:
        return pal[-1]
    k = int((v - lo) / (hi - lo) * len(pal))
    return pal[min(k, len(pal) - 1)]


def _cv_near(a, b):
    """Two #rrggbb colours within 1/255 a channel (test_colorvar_line_
    levels.py's tolerance: dash 0xcc where twoway writes 0xcb)."""
    try:
        return max(abs(int(a[j:j + 2], 16) - int(b[j:j + 2], 16))
                   for j in (1, 3, 5)) <= 1
    except ValueError:
        return a == b


def _cv_same_counts(got, want):
    """None when {colour: n} *got* is *want* to 1/255 a channel."""
    left = dict(got)
    for c, n in sorted(want.items()):
        hit = [g for g in left if _cv_near(g, c) and left[g] == n]
        if not hit:
            return (f"twoway {sorted(want.items())}, dash "
                    f"{sorted(got.items())}")
        left.pop(hit[0])
    if left:
        return f"twoway {sorted(want.items())}, dash {sorted(got.items())}"
    return None


#: The glyph twoway's per-observation colours are read from, by type, and
#: the SVG element kind that carries them.
_CV_KIND = {"scatter": "circle", "connected": "circle", "bar": "rect",
            "spike": "vline", "rcap": "vline", "pcspike": "diag",
            "line": "path"}
_CV_GLYPH = {"scatter": ("Scatter",), "connected": ("Scatter",),
             "bar": ("VBar", "Quad"), "spike": ("Segment",),
             "rcap": ("Segment",), "pcspike": ("Segment",)}


def _dash_colours(fig, ptype):
    """{colour: drawn rows} of the colour-mapped main glyph of each
    colorvar layer in *fig*; for line, {colour: lines}."""
    out = {}
    if ptype == "line":
        for r in fig.renderers:
            if dr._dash_is_swatch(r) or type(r.glyph).__name__ != "Line":
                continue
            # a level with no rows (its view selects none) draws nothing
            flt = getattr(getattr(r, "view", None), "filter", None)
            idx = getattr(flt, "indices", None)
            bools = getattr(flt, "booleans", None)
            data = r.data_source.data
            n = (len(idx) if idx is not None else
                 sum(bool(b) for b in bools) if bools is not None else
                 len(next(iter(data.values()), [])))
            if not n:
                continue
            c = _cv_hex(r.glyph.line_color)
            out[c] = out.get(c, 0) + 1
        return out
    seen = set()
    for r in cb.colour_renderers(fig):
        if type(r.glyph).__name__ not in _CV_GLYPH[ptype]:
            continue
        key = id(r.data_source), cb.colour_field(r)
        if key in seen:
            continue
        seen.add(key)
        m = cb.colour_mapper(r)
        for v in cb.drawn_colour_values(r):
            c = _cv_colour(m, v)
            out[c] = out.get(c, 0) + 1
    return out


def _cv_label(lab):
    v = getattr(lab, "value", None)
    if v is None and isinstance(lab, dict):
        v = lab.get("value")
    return str(lab if v is None else v)


def _dash_key(models):
    """(texts top to bottom, framed) of dash's colour key: a ColorBar's
    tick labels, the colorvar Legend's or the plot Legend's items."""
    figs = cb._figures(models) + cb._key_cells(models)
    for f in figs:
        for side in ("right", "left", "above", "below", "center"):
            for a in getattr(f, side):
                tn = type(a).__name__
                # WP-42 CV-6: a colorvar layer's plot-legend item is kept
                # (twoway's two-key rule hides a one-key legend), so a
                # hidden plot Legend is passed over: it is not drawn.
                if tn == "Legend" and a.items and a.visible is not False:
                    texts = [_cv_label(it.label) for it in a.items]
                    framed = bool(a.border_line_color) and \
                        (a.border_line_alpha or 0) > 0
                    return texts, framed
                if tn == "ColorBar" and a.name != "dash_by_label_box":
                    ticks = list(getattr(a.ticker, "ticks", []) or [])
                    over = dict(a.major_label_overrides or {})
                    if not ticks:
                        texts = ["<the ticker's own ticks>"]
                    else:
                        texts = [str(over.get(t, over.get(str(t), t)))
                                 for t in sorted(ticks, reverse=True)]
                    framed = bool(a.border_line_color) and \
                        (a.border_line_alpha or 0) > 0
                    return texts, framed
    return [], False


def _twoway_key(probe):
    """(texts top to bottom, framed) of twoway's key (D-33-13.d): the
    unrotated texts right of the plot region (of every by() panel),
    ordered by y then x; framed when a stroked rect, not white, encloses
    them all."""
    right = max([probe["plot"]["right"]]
                + [g["right"] for g in probe.get("panels", [])])
    key = sorted((t for t in probe["texts"]
                  if t["x"] is not None and t["x"] > right + 1
                  and not t["rotate"]), key=lambda t: (t["y"], t["x"]))
    texts = [t["text"] for t in key]
    framed = bool(key) and any(
        r["stroke"] not in ("#ffffff", "none") and r["w"] and r["h"]
        and all(r["x"] <= t["x"] <= r["x"] + r["w"]
                and r["y"] <= t["y"] <= r["y"] + r["h"] for t in key)
        for r in probe["rects"])
    return texts, framed


def _key_results(mode, pid):
    probe = _truth()["probes"][pid]
    models = _cv_models(mode, pid)
    tw_texts, tw_frame = _twoway_key(probe)
    d_texts, d_frame = _dash_key(models)
    return {
        f"{pid}:key_texts": None if d_texts == tw_texts else
        f"twoway {tw_texts}, dash {d_texts}",
        f"{pid}:key_frame": None if d_frame == tw_frame else
        f"twoway framed {tw_frame}, dash framed {d_frame}",
    }


def _colour_results(mode, pid):
    probe = _truth()["probes"][pid]
    models = _cv_models(mode, pid)
    plots, graph = _cv_spec(probe)
    ptype = plots[0]["type"]
    figs = [f for f in cb._figures(models) if f.renderers]
    if "by" in graph:
        want = probe["fills_by_panel"]
        got = [_dash_colours(f, ptype) for f in figs]
        if len(got) != len(want):
            diff = f"twoway {len(want)} panels, dash {len(got)}"
        else:
            diff = next((d for d in (_cv_same_counts(g, w)
                                     for g, w in zip(got, want)) if d),
                        None)
        return {f"{pid}:colours": diff}
    want = probe["elements"].get(_CV_KIND[ptype], {})
    got = {}
    for f in figs:
        for c, n in _dash_colours(f, ptype).items():
            got[c] = got.get(c, 0) + n
    return {f"{pid}:colours": _cv_same_counts(got, want)}


def _rows_of(pid, checks):
    """COLORVAR_KNOWN's rows of probe *pid* for the *checks* a test makes."""
    return {k: v for k, v in COLORVAR_KNOWN.items()
            if k in {f"{pid}:{c}" for c in checks}}


_KEY = ("key_texts", "key_frame")


def _drawn_params():
    return [pytest.param(p, marks=pytest.mark.xdist_group("cv-" + p))
            for p in _CV_DRAWN]


class TestTheKeyAgainstTwoway:
    """The colour key's texts, top to bottom, and its frame."""

    @pytest.mark.parametrize("pid", _drawn_params())
    def test_saved(self, pid):
        assert known_problems(_key_results("saved", pid), _rows_of(pid, _KEY),
                              "colorvar",
                              deliberate=COLORVAR_DELIBERATE) == []

    @pytest.mark.batch
    @pytest.mark.parametrize("pid", _drawn_params())
    def test_served(self, pid):
        assert known_problems(_key_results("served", pid), _rows_of(pid, _KEY),
                              "colorvar",
                              deliberate=COLORVAR_DELIBERATE) == []


class TestEveryTypeColours:
    """Each drawn element's colour, as twoway colours that plot type: the
    partition (count a colour) and the palette, to 1/255 a channel."""

    @pytest.mark.parametrize("pid", _drawn_params())
    def test_saved(self, pid):
        assert known_problems(_colour_results("saved", pid),
                              _rows_of(pid, ("colours",)),
                              "colorvar",
                              deliberate=COLORVAR_DELIBERATE) == []

    @pytest.mark.batch
    @pytest.mark.parametrize("pid", _drawn_params())
    def test_served(self, pid):
        assert known_problems(_colour_results("served", pid),
                              _rows_of(pid, ("colours",)), "colorvar",
                              deliberate=COLORVAR_DELIBERATE) == []


class TestTheRefusals:
    """A probe twoway refuses: dash's rc, and its first line where both
    refuse, against twoway's."""

    @pytest.mark.parametrize("pid", _CV_REFUSALS)
    def test_each(self, pid):
        probe = _truth()["probes"][pid]
        diff = None
        if probe["rc"] != probe["twoway_rc"]:
            diff = (f"twoway r({probe['twoway_rc']}) "
                    f"{probe.get('twoway_message', '')!r}, dash "
                    f"r({probe['rc']}) {probe['message']!r}")
        assert known_problems({f"{pid}:rc": diff}, _rows_of(pid, ("rc",)),
                              "colorvar",
                              deliberate=COLORVAR_DELIBERATE) == []


class TestNoVacuousProbe:

    def test_no_probe_passes_vacuously(self):
        probes = _truth()["probes"]
        assert sorted(probes) == sorted(_CV_PROBES)
        bad = []
        for pid in _CV_DRAWN:
            if not ({"colordiscrete", "colorcuts", "colorlevels"}
                    & set(_opts_of(probes[pid]["command"]))):
                continue
            ptype = _cv_spec(probes[pid])[0][0]["type"]
            n = len(probes[pid]["elements"].get(_CV_KIND[ptype], {}))
            if n < 2 and pid not in _ONE_GROUP_BY_TWOWAY:
                bad.append(pid)
        assert bad == []
        for pid in _ONE_GROUP_BY_TWOWAY:
            assert probes[pid]["n_groups"] == 1, pid
        assert probes["cv16_disc_levels_rep78_3"]["n_groups"] >= 2


class TestTheKnownDifferences:

    def test_every_known_difference_is_open(self):
        assert dead_rows(COLORVAR_KNOWN, "colorvar") == []
        for key in list(COLORVAR_KNOWN) + list(COLORVAR_DELIBERATE):
            assert key.split(":")[0] in _CV_PROBES, key
