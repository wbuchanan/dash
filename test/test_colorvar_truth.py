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
    if not os.path.exists(_FIXTURE):
        return ["missing-fixture"]
    with open(_FIXTURE, encoding="utf-8") as fh:
        return sorted(json.load(fh)["probes"])


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
        if not ({"colordiscrete", "colorcuts", "colorlevels"} & set(opts)):
            return  # the continuous default is not compared (DISCOVERY Q5)
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
        assert cb.colour_bars(_render(spec, mode)) == [
            (p["summ_min"], p["summ_max"])]

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
        assert cb.colour_bars(_render(spec, mode)) == [
            (p["summ_min"], p["summ_max"])]

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
        spec = _linked_spec([plot_for("scatter", {"colorvar": "price"})],
                            go={"by": "foreign"}, linked=linked)
        bars = [cb.colour_bars(f)[0]
                for f in _colour_figs(_render(spec, mode))]
        assert bars == [(probes[k]["summ_min"], probes[k]["summ_max"])
                        for k in ("by_lv4_p0", "by_lv4_p1")]

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
