"""The saved page marks the layers it does not recompute (WP-29 P0.17).

A saved page's filter callback (``dash_render._FILTER_JS``) redraws every
row layer from the kept rows, but a fitted or smoothed line keeps the fit
it had at build (fpfit, fpfitci, lpolyci, mband, mspline; lfit and
qfit are refitted since WP-31 F1a, lowess since F1c, lfitci and qfitci since
F1b, lpoly since F1d), a histogram
keeps its bins and a density its grid.  Measured on ``test_mode_parity._DF`` with the dropdown moved to
Foreign: the lfit still starts at 29.1052, Stata's all-rows ``regress mpg
weight`` value at weight 1800 (29.105207), where ``regress mpg weight if
foreign==1`` gives 29.91739 -- and nothing on the page said so.

Decision M3 (binding): a VISIBLE cue, no JavaScript estimator.  While the
filters that reach a frozen layer have removed at least one row of its
estimation sample, the layer is dimmed to 30% of its alphas, its legend key
gains " (unfiltered)", " (bins unfiltered)" or " (grid unfiltered)", its
graph shows the caption ``Marked layers were computed before the filter``
and one ``role="status"`` line in the filter area says the same.  Moving
back to every row of the sample clears every mark.

The oracle is Stata's own sample rule:
- E-17.3, on ``_DF``: ``regress mpg weight`` b=-.00709441 (N=10), ``if
  foreign==1`` b=-.00833426; the slider at its minimum keeps N=10 and the
  same b, so it marks nothing.
- E-17.4, ``w = 1 0 2 1 1 3 1 2 1 1``: ``regress mpg weight [aw=w]`` N=9
  b=-0.00701112 with or without the zero-weight row, so dropping only that
  row marks nothing.

Expected ids, rows and panels are derived from the frames here with pandas,
never from literals.  Node tests run the page's own script through
``js_runner.JsSession``, which commits muted, visible and label back.
"""
import json
import math
import os
import re
import sys
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.models import (ColumnDataSource, Div, GlyphRenderer, Legend,
                          Line, Patch, RangeSlider, Select, Slider, Title,
                          VArea)

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from js_runner import JsSession, requires_node  # noqa: E402
from test_mode_parity import (_DF, _fire, _served, _spec,  # noqa: E402
                              _layout_tree, _widgets_of)
from test_saved_filter_layers import _MOVES, _render  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

#: The seven layers a saved page computes at build and does not refit.
# lfit and qfit (WP-31 F1a), lowess (F1c), lfitci and qfitci (F1b) and
# lpoly (F1d) are refitted by the saved page; see _REFIT.
_FROZEN = ["fpfit", "fpfitci",
           "lpolyci", "mband", "mspline", "histogram", "kdensity"]
#: The frozen fit layer the cue's own mechanics are measured on.  It was
#: lfit until the saved page refitted lfit (WP-31 F1a); fpfit stays frozen
#: longest (WP-31 F1g refits it last).
_STAND_IN = "fpfit"


def _kind_of(t):
    return {"histogram": "bins", "kdensity": "grid"}.get(t, "fit")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _session(r):
    """One shared JsSession per render, which commits."""
    if not hasattr(r, "_stl_session"):
        r._stl_session = JsSession(r.filter_callbacks)
    return r._stl_session


def _widget(r, kind):
    ws = [w for w in r.filter_widgets if type(w).__name__ == kind]
    assert len(ws) == 1, f"{len(ws)} {kind} widgets on the page"
    return ws[0]


def _set(r, kind, raw):
    """Set a widget's RAW value and run its own callback under node."""
    w = _widget(r, kind)
    w.value = raw
    cb = r.filter_callbacks[r.filter_widgets.index(w)]
    assert cb.code == dr._FILTER_JS
    _session(r).run(cb)


def _act(r, action):
    """A ``_MOVES`` action: ``(kind, want)``, a Select by option label."""
    kind, want = action
    if kind == "Select":
        w = _widget(r, kind)
        raw = [v for v, lab in w.options if lab == want]
        assert raw, f"no option labelled {want!r}: {w.options}"
        want = raw[0]
    _set(r, kind, want)


def _back(r, kind):
    """Every row again: a Select's sentinel, a RangeSlider's full span, a
    Slider's start."""
    w = _widget(r, kind)
    if isinstance(w, Select):
        _set(r, kind, getattr(w, "_dash_sentinel", "__all__"))
    elif isinstance(w, RangeSlider) or isinstance(w.value, tuple):
        _set(r, kind, (w.start, w.end))
    else:
        _set(r, kind, w.start)


def _legends(fig):
    return [m for side in (fig.center, fig.above, fig.below, fig.left,
                           fig.right) for m in side if isinstance(m, Legend)]


def _text(label):
    if isinstance(label, dict):
        return label.get("value")
    return getattr(label, "value", None)


def _cue(r):
    titles, muted, labels = {}, {}, {}
    for k, f in r.figures.items():
        titles[k] = [t.visible for t in f.above
                     if "dash_stale_cue" in (getattr(t, "tags", None) or [])]
        muted[k] = [x.muted for x in f.renderers if hasattr(x, "_dash_frozen")]
        labels[k] = [_text(i.label) for L in _legends(f) for i in L.items]
    st = (r.filter_callbacks[0].args.get("stale_status")
          if r.filter_callbacks else None)
    status = (st.visible, st.text) if st is not None else None
    return {"titles": titles, "muted": muted, "labels": labels,
            "status": status}


def _one_cue(r, key="g1"):
    cues = [t for t in r.figures[key].above
            if "dash_stale_cue" in (getattr(t, "tags", None) or [])]
    assert len(cues) == 1, (
        f"no Title tagged dash_stale_cue on {key} ({len(cues)} found)")
    return cues[0]


def _layer_rends(r, key="g1", start=1):
    """The renderers of every layer from plot *start* on (the scatter is
    plot 0 in most specs)."""
    f = r.figures[key]
    return [x for x in f.renderers if hasattr(x, "_dash_frozen")]


def _items_of(fig, rends):
    ids = {id(x) for x in rends}
    return [i for L in _legends(fig) for i in L.items
            if any(id(x) in ids for x in i.renderers)]


def _all_models(r):
    return list(r._last_layout_root.references())


def _render_df(spec, df):
    return _render(spec, df)


def _marked(r, key="g1"):
    """(caption visible, every frozen renderer muted) on figure *key*."""
    cue = _one_cue(r, key)
    m = [x.muted for x in r.figures[key].renderers
         if hasattr(x, "_dash_frozen")]
    assert m, f"no renderer of {key} carries _dash_frozen"
    return cue.visible, all(m), any(m)


def _assert_marked(r, key="g1"):
    vis, all_m, _ = _marked(r, key)
    assert vis and all_m, f"{key}: caption {vis}, all muted {all_m}"


def _assert_clear(r, key="g1"):
    vis, _, any_m = _marked(r, key)
    assert not vis and not any_m, f"{key}: caption {vis}, any muted {any_m}"


def _status(r):
    st = r.filter_callbacks[0].args.get("stale_status")
    assert st is not None, "no stale_status arg"
    return st.visible, st.text


# ---------------------------------------------------------------------------
# The cue on a move
# ---------------------------------------------------------------------------

@requires_node
class TestTheCueAppearsOnAMove:

    @pytest.mark.parametrize("move", _MOVES, ids=[m[0] for m in _MOVES])
    @pytest.mark.parametrize("t", _FROZEN)
    def test_a_layer_the_move_took_rows_from_is_marked(self, t, move):
        _, filt, action, _oracle = move
        r = _render(_spec([plot_for("scatter"), plot_for(t)],
                          {"filter": filt}))
        cue = _one_cue(r)
        built = _cue(r)["labels"]["g1"]
        assert cue.visible is False
        assert not any(x.muted for x in _layer_rends(r))
        assert _status(r) == (False, "")
        _act(r, action)
        rends = _layer_rends(r)
        assert rends and all(x.muted for x in rends)
        assert cue.visible is True
        suffix = dr._DASH_STALE_SUFFIX[_kind_of(t)]
        f = r.figures["g1"]
        items = _items_of(f, rends)
        assert items, f"{t}: no legend item for the layer"
        for it in items:
            assert _text(it.label).endswith(suffix), _text(it.label)
        scatter_items = _items_of(f, [f.renderers[0]])
        assert [_text(i.label) for i in scatter_items] == [built[0]]
        assert _status(r) == (True, dr._DASH_STALE_STATUS_HTML)

    def test_every_renderer_of_a_ci_layer_is_dimmed_and_both_keys_marked(
            self):
        # fpfitci: the ci layer still frozen (lfitci is refitted since
        # WP-31 F1b).
        r = _render(_spec([plot_for("scatter"), plot_for("fpfitci")],
                          {"filter": _MOVES[0][1]}))
        _one_cue(r)
        _act(r, _MOVES[0][2])
        rends = _layer_rends(r)
        assert sorted(type(x.glyph).__name__ for x in rends) == [
            "Line", "Patch", "VArea"]
        assert all(x.muted for x in rends)
        labs = sorted(_text(i.label) for i in _items_of(r.figures["g1"],
                                                         rends))
        assert labs == ["95% CI (unfiltered)", "Predicted mpg (unfiltered)"]

    @pytest.mark.parametrize("move", _MOVES, ids=["dropdown", "range",
                                                  "slider"])
    def test_every_source_of_an_lpolyci_is_dimmed_and_both_keys_marked(
            self, move):
        _, filt, action, _o = move
        r = _render(_spec([plot_for("scatter"), plot_for("lpolyci")],
                          {"filter": filt}))
        f = r.figures["g1"]
        layer = list(f.renderers[1:])
        srcs = [x.data_source for x in layer]
        if not (len(layer) == 3 and len({id(s) for s in srcs}) == 3
                and {"y_lower", "y_upper"} <= set(srcs[0].data)
                and set(srcs[2].data) >= {"x_lp", "y_lp"}
                and "y_lower" not in srcs[2].data):
            pytest.fail("needs S11 (P0.9 three-source lpolyci)")
        cue = _one_cue(r)
        tags = [getattr(x, "_dash_frozen", None) for x in layer]
        assert tags[0] is not None and all(tg is tags[0] for tg in tags)
        built = {id(i): _text(i.label) for i in _items_of(f, layer)}
        _act(r, action)
        assert all(x.muted for x in layer)
        for x in layer:
            for a in ("line_alpha", "fill_alpha", "hatch_alpha"):
                if a in x.glyph.properties():
                    g, mg = getattr(x.glyph, a), getattr(x.muted_glyph, a)
                    if isinstance(g, (int, float)):
                        assert mg == pytest.approx(g * 0.3)
        assert cue.visible is True
        band_items = _items_of(f, [layer[0]])
        line_items = _items_of(f, [layer[2]])
        assert band_items and line_items
        for it in band_items + line_items:
            assert _text(it.label).endswith(" (unfiltered)")
        assert [_text(i.label) for i in _items_of(f, [f.renderers[0]])] == [
            "mpg"]
        _back(r, action[0])
        assert not any(x.muted for x in layer)
        assert cue.visible is False
        assert {id(i): _text(i.label) for i in _items_of(f, layer)} == built

        # An empty lpolyci holds three empty sources and is never marked.
        r = _render(_spec([plot_for("scatter"),
                           plot_for("lpolyci", if_expr="price > 20000")],
                          {"filter": filt}))
        layer = list(r.figures["g1"].renderers[1:])
        assert len(layer) == 3
        cb = r.filter_callbacks[0]
        for c in json.loads(cb.args["stale_configs_json"]):
            assert c["members"] >= 0
            assert list(cb.args["stale_members"][c["members"]].data["id"]) \
                == []
        _act(r, action)
        assert not any(x.muted for x in layer)
        _back(r, action[0])
        assert not any(x.muted for x in layer)


#: WP-31 F1: the computed layers the saved page refits after a move.
_REFIT = ["lfit", "qfit", "lowess", "lfitci", "qfitci", "lpoly"]


@requires_node
class TestARefitLayerIsNeverMarked:
    """A layer the saved page refits (WP-31 F1a) is never dimmed, keyed
    "(unfiltered)" or named in the status line: it shows the fit on the
    kept rows, as the served app does."""

    @pytest.mark.parametrize("move", _MOVES, ids=[m[0] for m in _MOVES])
    @pytest.mark.parametrize("t", _REFIT)
    def test_not_marked(self, t, move):
        _, filt, action, _oracle = move
        r = _render(_spec([plot_for("scatter"), plot_for(t)],
                          {"filter": filt}))
        _act(r, action)
        f = r.figures["g1"]
        rends = list(f.renderers[1:])
        assert rends and not any(x.muted for x in rends)
        for it in _items_of(f, rends):
            assert not _text(it.label).endswith(
                dr._DASH_STALE_SUFFIX["fit"]), _text(it.label)
        st = r.filter_callbacks[0].args.get("stale_status")
        assert st is None or st.visible is False


@requires_node
class TestTheCueClears:

    @pytest.mark.parametrize("move", _MOVES, ids=["dropdown", "range",
                                                  "slider"])
    def test_moving_back_to_every_row_clears_it(self, move):
        _, filt, action, _o = move
        r = _render(_spec([plot_for("scatter"), plot_for(_STAND_IN)],
                          {"filter": filt}))
        _one_cue(r)
        built = _cue(r)["labels"]
        _act(r, action)
        _assert_marked(r)
        _back(r, action[0])
        _assert_clear(r)
        assert _cue(r)["labels"] == built
        assert _status(r) == (False, "")

    def test_a_second_move_keeps_it_and_the_reset_clears_it(self):
        r = _render(_spec([plot_for("scatter"), plot_for(_STAND_IN)],
                          {"filter": "foreign, type(dropdown) || "
                                     "price, type(range)"}))
        _one_cue(r)
        _act(r, ("Select", "Foreign"))
        _assert_marked(r)
        _set(r, "RangeSlider", (4500.0, 11385.0))
        _assert_marked(r)
        _back(r, "Select")
        _assert_marked(r)
        _back(r, "RangeSlider")
        _assert_clear(r)


# ---------------------------------------------------------------------------
# No false cue
# ---------------------------------------------------------------------------

def _wdf(**changes):
    df = _DF.copy()
    df["w"] = [1.0, 0.0, 2.0, 1.0, 1.0, 3.0, 1.0, 2.0, 1.0, 1.0]
    df["z"] = [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    for k, v in changes.items():
        df[k] = v
    return df


_AW = {"weight": "aweight", "wexp": "w"}
#: lpolyci refuses a pweight (r(101)): the frozen layer with a refused
#: weight since lowess (WP-31 F1c) and lpoly (F1d) are refitted.
_PW = {"weight": "pweight", "wexp": "w"}
#: A ci layer drawn from the points Stata computed (estopts(), WP-31 C4):
#: frozen with the kind "fit" whatever its type.
_POINTS = {"estopts": "noconstant",
           "points": {"x": [2000.0, 3000.0], "y": [11.0, 21.0],
                      "lo": [9.0, 20.0], "hi": [13.0, 22.0], "nobs": 9}}


@requires_node
class TestNoFalseCue:

    @pytest.mark.parametrize("col,opts", [("mpg", {}), ("weight", {}),
                                          ("w", _AW)],
                             ids=["y null", "x null", "weight null"])
    def test_a_move_that_removes_only_rows_the_fit_never_used(self, col,
                                                              opts):
        df = _wdf()
        df.loc[df["foreign"] == 0, col] = np.nan
        r = _render(_spec([plot_for("scatter"), plot_for(_STAND_IN, opts)],
                          {"filter": "foreign, type(dropdown)"}), df)
        _one_cue(r)
        _act(r, ("Select", "Foreign"))
        _assert_clear(r)

    def test_the_slider_at_its_minimum_marks_nothing(self):
        r = _render(_spec([plot_for("scatter"), plot_for(_STAND_IN)],
                          {"filter": "price, type(slider)"}))
        _one_cue(r)
        _set(r, "Slider", _widget(r, "Slider").start)
        _assert_clear(r)

    def test_an_empty_fit_is_never_marked(self):
        for _, filt, action, _o in _MOVES:
            r = _render(_spec([plot_for("scatter"),
                               plot_for(_STAND_IN, if_expr="price > 20000")],
                              {"filter": filt}))
            _one_cue(r)
            cb = r.filter_callbacks[0]
            [c] = json.loads(cb.args["stale_configs_json"])
            assert c["members"] >= 0
            assert list(cb.args["stale_members"][c["members"]].data["id"]) \
                == []
            _act(r, action)
            _assert_clear(r)

    @pytest.mark.parametrize("t", ["scatter", "line", "bar", "function"])
    def test_row_layers_and_function_are_never_marked(self, t):
        r = _render(_spec([plot_for("scatter"), plot_for(t)],
                          {"filter": "foreign, type(dropdown)"}))
        assert not any("dash_stale_cue" in (getattr(m, "tags", None) or [])
                       for f in r.figures.values() for m in f.above)
        assert all("stale_configs_json" not in cb.args
                   for cb in r.filter_callbacks)

    def test_a_density_over_its_own_range_is_never_marked(self):
        r = _render(_spec([plot_for("scatter"),
                           plot_for("kdensity", {"range": "10 35"})],
                          {"filter": "foreign, type(dropdown)"}))
        assert not any("dash_stale_cue" in (getattr(m, "tags", None) or [])
                       for f in r.figures.values() for m in f.above)


# ---------------------------------------------------------------------------
# The weighted sample (E-17.4)
# ---------------------------------------------------------------------------

@requires_node
class TestTheWeightedSample:
    """A row counts when its weight is finite and above zero (the rows
    ``GlyphMapper._layer_weights`` fits from); when the build drew nothing
    because of a weight state, any removed row with a finite weight."""

    def _run(self, df, plot):
        r = _render(_spec([plot_for("scatter"), plot],
                          {"filter": "z, type(dropdown)"}), df)
        _one_cue(r)
        w = _widget(r, "Select")
        raw = [v for v, lab in w.options if str(lab) in ("0", "0.0")]
        assert raw, w.options
        _set(r, "Select", raw[0])
        return r

    def test_dropping_only_a_zero_weight_row_marks_nothing(self):
        df = _wdf()
        dropped = df.index[df["z"] == 1]
        assert list(df.loc[dropped, "w"]) == [0.0]
        r = self._run(df, plot_for(_STAND_IN, _AW))
        _assert_clear(r)

    def test_dropping_a_positive_weight_row_marks_it(self):
        df = _wdf(z=[1.0] + [0.0] * 9)
        assert df.loc[df["z"] == 1, "w"].tolist() == [1.0]
        r = self._run(df, plot_for(_STAND_IN, _AW))
        _assert_marked(r)

    def test_dropping_the_negative_weight_rows_of_an_fpfit_marks_it(self):
        df = _wdf(z=[0.0, 0.0, 0.0, 1.0] + [0.0] * 6)
        df.loc[3, "w"] = -1.0
        r = self._run(df, plot_for("fpfit", _AW))
        assert r.figures["g1"].renderers[1]._dash_frozen["wrule"] == "any"
        _assert_marked(r)

    def test_a_negative_weight_on_lfit_is_outside_the_sample(self):
        # An lfitci drawn from Stata's points (estopts(), WP-31 C4), as
        # lfit excludes a negative weight and that layer is still frozen:
        # lfit (F1a) and lfitci (F1b) themselves are refitted by the saved
        # page.
        df = _wdf(z=[0.0, 0.0, 0.0, 1.0] + [0.0] * 6)
        df.loc[3, "w"] = -1.0
        r = self._run(df, plot_for("lfitci", dict(_AW, **_POINTS)))
        _assert_clear(r)

    def test_a_weight_twoway_refuses_is_not_read(self):
        # lpolyci [pw], frozen: lowess, which refuses every weight, and
        # lpoly are refitted by the saved page (WP-31 F1c, F1d).
        df = _wdf()
        r = self._run(df, plot_for("lpolyci", _PW))
        _assert_marked(r)


# ---------------------------------------------------------------------------
# Each target
# ---------------------------------------------------------------------------

def _panel(r, title):
    # Flipped (WP-30 P1.15a): a panel was found by its title, which held
    # its label; twoway draws the label as a row of its own.
    from by_panel_probe import panel_label
    keys = [k for k, f in r.figures.items() if panel_label(f) == title]
    assert len(keys) == 1, (title, [panel_label(f)
                                    for f in r.figures.values()])
    return keys[0]


@requires_node
class TestTheCueFollowsEachTarget:

    def test_by_panels(self):
        r = _render(_spec([plot_for("scatter"), plot_for(_STAND_IN)],
                          {"filter": "foreign, type(dropdown)"},
                          {"by": "foreign"}))
        dom, fo = _panel(r, "Domestic"), _panel(r, "Foreign")
        _one_cue(r, dom)
        _act(r, ("Select", "Foreign"))
        _assert_marked(r, dom)
        _assert_clear(r, fo)

    def test_by_with_total(self):
        r = _render(_spec([plot_for("scatter"), plot_for(_STAND_IN)],
                          {"filter": "foreign, type(dropdown)"},
                          {"by": "foreign, total"}))
        _one_cue(r, _panel(r, "Total"))
        _act(r, ("Select", "Foreign"))
        _assert_marked(r, _panel(r, "Domestic"))
        _assert_marked(r, _panel(r, "Total"))
        _assert_clear(r, _panel(r, "Foreign"))

    def test_a_layers_own_if(self):
        assert (_DF.loc[(_DF["foreign"] == 1) & (_DF["price"] < 4500)]
                .shape[0]) == 1
        spec = _spec([plot_for("scatter"),
                      plot_for(_STAND_IN, if_expr="foreign == 1")],
                     {"filter": "foreign, type(dropdown) || "
                                "price, type(range)"})
        r = _render(spec)
        _act(r, ("Select", "Foreign"))
        _assert_clear(r)
        _back(r, "Select")
        _set(r, "RangeSlider", (4500.0, 11385.0))
        _assert_marked(r)

    def test_an_excluded_graph_has_no_cue(self):
        graphs = [("g1", [plot_for("scatter"), plot_for(_STAND_IN)]),
                  ("g2", [plot_for("scatter"), plot_for(_STAND_IN)])]
        spec = _spec(graphs=graphs)
        spec["build_options"]["filters"] = [
            {"varname": "foreign", "type": "dropdown", "exclude": ["g1"]}]
        r = _render(spec)
        assert not any("dash_stale_cue" in (getattr(m, "tags", None) or [])
                       for m in r.figures["g1"].above)
        frozen_g1 = {id(x) for x in r.figures["g1"].renderers
                     if hasattr(x, "_dash_frozen")}
        rl = r.filter_callbacks[0].args["stale_renderers"]
        assert not any(id(x) in frozen_g1 for lst in rl for x in lst)
        _act(r, ("Select", "Foreign"))
        _assert_marked(r, "g2")
        assert not any(x.muted for x in r.figures["g1"].renderers)

    def test_a_linked_pair(self):
        graphs = [("g1", [plot_for("scatter")]), ("g2", [plot_for(_STAND_IN)])]
        r = _render(_spec(build_options={"filter": "foreign, type(dropdown)",
                                         "link": "g1 g2"}, graphs=graphs))
        _act(r, ("Select", "Foreign"))
        _assert_marked(r, "g2")

    def test_a_date_filter_and_a_fit_on_a_date_x(self):
        r = _render(_spec([plot_for("scatter", xvar="when"),
                           plot_for(_STAND_IN, xvar="when")],
                          {"filter": "when, type(range)",
                           "formats": {"when": "%td"}}))
        w = _widget(r, "DateRangeSlider")
        lo, hi = w.start, w.end
        _set(r, "DateRangeSlider", (lo + (hi - lo) / 2, hi))
        _assert_marked(r)
        _set(r, "DateRangeSlider", (lo, hi))
        _assert_clear(r)

    def test_a_fit_on_the_second_axis(self):
        r = _render(_spec([plot_for("scatter"),
                           plot_for(_STAND_IN, {"yaxis": "2"})],
                          {"filter": "foreign, type(dropdown)"}))
        _act(r, ("Select", "Foreign"))
        _assert_marked(r)

    def test_only_an_lfit_with_no_scatter_is_marked(self):
        r = _render(_spec([plot_for(_STAND_IN)],
                          {"filter": "foreign, type(dropdown)"}))
        _act(r, ("Select", "Foreign"))
        _assert_marked(r)


class TestNoCueWithoutAFilter:

    @pytest.mark.parametrize("plots,bo", [
        ([plot_for("scatter"), plot_for(_STAND_IN)], {}),
        ([plot_for("scatter")], {"filter": "foreign, type(dropdown)"}),
    ], ids=["no filter", "a filter with a scatter only"])
    def test_the_page_gains_no_model(self, plots, bo):
        r = _render(_spec(plots, bo))
        ms = _all_models(r)
        assert not any(isinstance(m, Title)
                       and "dash_stale_cue" in (m.tags or []) for m in ms)
        assert not any(isinstance(m, Div)
                       and "dash_stale_status" in (m.tags or []) for m in ms)
        assert not any(k.startswith("stale_") for cb in r.filter_callbacks
                       for k in cb.args)
        for f in r.figures.values():
            for x in f.renderers:
                if isinstance(x.glyph, Line) and x.glyph.line_alpha == 1.0:
                    assert x.muted_glyph.line_alpha == pytest.approx(0.2)


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

class TestTheStaleGlyph:

    def test_colour_width_and_dash_are_kept_and_every_alpha_scaled(self):
        g = Line(x="x", y="y", line_color="green", line_width=2,
                 line_dash="dashed", line_alpha=0.8)
        m = dr._dash_stale_glyph(g)
        assert m is not g
        assert m.line_alpha == pytest.approx(0.24)
        assert (m.line_color, m.line_width, list(m.line_dash)) == (
            "green", 2, list(g.line_dash))
        assert g.line_alpha == 0.8

    def test_alpha_zero_stays_zero_and_a_field_alpha_becomes_the_constant(
            self):
        assert dr._dash_stale_glyph(Line(line_alpha=0)).line_alpha == 0
        from bokeh.models import Segment
        m = dr._dash_stale_glyph(Segment(line_alpha="a"))
        assert m.line_alpha == dr._DASH_STALE_ALPHA

    def test_a_band_and_its_outline(self):
        v = dr._dash_stale_glyph(VArea(fill_alpha=0.5, hatch_alpha=1.0))
        assert (v.fill_alpha, v.hatch_alpha) == (pytest.approx(0.15),
                                                 pytest.approx(0.3))
        p = dr._dash_stale_glyph(Patch(line_alpha=1.0, fill_alpha=0.5,
                                       hatch_alpha=1.0))
        assert (p.line_alpha, p.fill_alpha, p.hatch_alpha) == (
            pytest.approx(0.3), pytest.approx(0.15), pytest.approx(0.3))

    def test_it_follows_a_restyle_made_after_the_draw(self):
        r = _render(_spec([plot_for("scatter"),
                           plot_for(_STAND_IN, {"lcolor": "green",
                                             "lpattern": "dash"})],
                          {"filter": "foreign, type(dropdown)"}))
        [x] = _layer_rends(r)
        assert x.muted_glyph.line_color == x.glyph.line_color
        assert list(x.muted_glyph.line_dash) == list(x.glyph.line_dash)
        assert x.muted_glyph.line_alpha == pytest.approx(
            x.glyph.line_alpha * 0.3)


class TestTheStaleKind:

    def test_each_type(self):
        fits = [t for t in _FROZEN if t not in ("histogram", "kdensity")]
        # 11 -> 9: F1a refits lfit and qfit; 9 -> 8: F1c refits lowess;
        # 8 -> 6: F1b refits lfitci and qfitci; 6 -> 5: F1d refits lpoly
        assert len(fits) == 5
        for t in fits:
            assert dr._dash_stale_kind(t, {}) == "fit"
        assert dr._dash_stale_kind("histogram", {}) == "bins"
        assert dr._dash_stale_kind("kdensity", {}) == "grid"
        assert dr._dash_stale_kind("kdensity", {"range": "10 35"}) is None
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            assert dr._dash_stale_kind("kdensity", {"range": "x"}) == "grid"
        assert caught == []
        assert dr._dash_stale_kind("scatter", {}) is None
        assert dr._dash_stale_kind("FPFIT", {}) == "fit"
        for t in _REFIT:
            assert dr._dash_stale_kind(t, {}) is None


def _wsrc():
    return ColumnDataSource({"y": [1.0, 2.0, 3.0, 4.0],
                             "x": [1.0, 2.0, 3.0, 5.0],
                             "w": [1.0, 2.0, 1.0, 1.0],
                             "s": ["a", "b", "c", "d"]})


class TestTheWeightColumn:

    @pytest.mark.parametrize("layer,opts,want", [
        ("lfit", {}, (None, "", "none")),
        ("lfit", {"weight": "aweight", "wexp": "zz"}, ("aw", "zz", "missing")),
        ("lfit", {"weight": "aweight", "wexp": "s"},
         ("aw", "s", "not-numeric")),
        ("lowess", _AW, ("aw", "w", "refused")),
        ("mspline", _AW, ("aw", "w", "inert")),
        ("lfit", _AW, ("aw", "w", None)),
    ], ids=["none", "missing", "not-numeric", "refused", "inert", "applied"])
    def test_it_decides_as_layer_weights_does(self, layer, opts, want):
        src = _wsrc()
        assert dr.GlyphMapper._layer_weight_column(src, opts, layer) == want
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr._dash_reset_notes()
            out = dr.GlyphMapper._layer_weights(src, None, opts, layer,
                                                "y", "x")
        assert (out[-1] is None) == (want[2] is not None)

    def test_the_value_state(self):
        st = dr.GlyphMapper._layer_weight_values_state
        neg = np.array([1.0, -1.0, 2.0])
        assert st(neg, "aw", "fpfit") == "negative"
        assert st(neg, "aw", "lfit") is None
        assert st(np.array([1.0, 1.5]), "fw", "qfit") == "nonint"
        assert st(np.array([1.0, 2.0]), "aw", "qfit") is None

    _REFUSALS = [
        ("missing", "lfit", {"weight": "aweight", "wexp": "zz"}, None,
         "dash: lfit [aweight=zz]: the data carries no variable 'zz', so "
         "the layer is drawn unweighted."),
        ("not-numeric", "lfit", {"weight": "aweight", "wexp": "s"}, None,
         "dash: lfit [aweight=s]: 's' is not numeric (twoway: type "
         "mismatch, r(109)); the layer is drawn unweighted."),
        ("refused", "histogram", _AW, None,
         "dash: histogram [aweight=w]: twoway histogram refuses it "
         "(aweights not allowed, r(101)); the layer is drawn unweighted."),
        ("lowess", "lowess", _AW, None,
         "dash: lowess [aweight=w]: twoway lowess refuses it (weights not "
         "allowed, r(101)); the layer is drawn unweighted."),
        ("inert", "mspline", _AW, None,
         "dash: mspline [aweight=w]: twoway mspline accepts the weight and "
         "does not use it (measured: the curve equals the unweighted one), "
         "so neither does dash."),
        ("negative", "fpfit", _AW, [1.0, -1.0, 1.0, 1.0],
         "dash: fpfit [aweight=w]: 1 negative weight(s) -- fracpoly cannot "
         "fit it, and twoway draws nothing; dash draws nothing for this "
         "layer."),
        ("nonint", "qfit", {"weight": "fweight", "wexp": "w"},
         [1.0, 1.5, 1.0, 1.0],
         "dash: qfit [fweight=w]: regress and fracpoly cannot use "
         "non-integer frequency weights, and twoway draws nothing; dash "
         "draws nothing for this layer."),
        ("nonpositive", "lfit", _AW, [1.0, 0.0, 1.0, 1.0],
         "dash: lfit [aweight=w]: 1 observation(s) with a zero or negative "
         "weight are excluded, as twoway excludes them."),
    ]

    @pytest.mark.parametrize("case,layer,opts,w,msg", _REFUSALS,
                             ids=[c[0] for c in _REFUSALS])
    def test_layer_weights_still_names_every_refusal(self, case, layer,
                                                     opts, w, msg):
        src = _wsrc()
        if w is not None:
            src.data["w"] = w
        dr._dash_reset_notes()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr.GlyphMapper._layer_weights(src, None, opts, layer, "y", "x")
        assert [str(c.message) for c in caught] == [msg]


# ---------------------------------------------------------------------------
# The tag, the registry, the args
# ---------------------------------------------------------------------------

def _ids_where(r, mask):
    src = r.sources["g1"]
    ids = list(src.data[dr._ROW_ID_COLUMN])
    return [int(i) for i, keep in zip(ids, list(mask)) if keep]


class TestTheFrozenTag:

    def test_the_tag_of_each_kind(self):
        r = _render(_spec([plot_for("scatter"), plot_for(_STAND_IN),
                           plot_for("histogram"),
                           plot_for(_STAND_IN, if_expr="price > 20000"),
                           # fpfitci [aw]: a weighted frozen layer
                           # ("positive"); lfitci is refitted since WP-31
                           # F1b.
                           plot_for("fpfitci", _AW),
                           # A refused weight: lpolyci [pw] (lowess
                           # and lpoly are refitted since WP-31 F1c, F1d).
                           plot_for("lpolyci", _PW)],
                          {"filter": "foreign, type(dropdown)"}), _wdf())
        tags = []
        for x in r.figures["g1"].renderers:
            t = getattr(x, "_dash_frozen", None)
            if t is not None and not any(t is u for u in tags):
                tags.append(t)
        assert [t["type"] for t in tags] == [_STAND_IN, "histogram",
                                             _STAND_IN, "fpfitci", "lpolyci"]
        lf, hi, empty, wl, lw = tags
        assert lf["vars"] == ["mpg", "weight"] and lf["kind"] == "fit"
        assert hi["vars"] == ["mpg"] and hi["kind"] == "bins"
        assert "member_ids" not in lf and "member_ids" not in hi
        assert empty["member_ids"] == []
        assert (lf["wvar"], lf["wrule"]) == (None, None)
        assert (wl["wvar"], wl["wrule"]) == ("w", "positive")
        assert (lw["wvar"], lw["wrule"]) == (None, None)

        df = _wdf()
        df.loc[3, "w"] = -1.0
        r2 = _render(_spec([plot_for("fpfit", _AW)]), df)
        [t2] = {id(x._dash_frozen): x._dash_frozen
                for x in r2.figures["g1"].renderers}.values()
        assert (t2["wvar"], t2["wrule"]) == ("w", "any")

        r3 = _render(_spec([plot_for("scatter"), plot_for(_STAND_IN)],
                           {"filter": "foreign, type(dropdown)"},
                           {"by": "foreign"}))
        for k, f in r3.figures.items():
            # Flipped (WP-30 P1.15a): the panel's label row, not its title.
            from by_panel_probe import panel_label
            want = 0.0 if panel_label(f) == "Domestic" else 1.0
            src = f.renderers[0].data_source
            ids = [int(i) for i, fo in zip(src.data[dr._ROW_ID_COLUMN],
                                           src.data["foreign"])
                   if fo == want]
            [t3] = {id(x._dash_frozen): x._dash_frozen
                    for x in f.renderers
                    if hasattr(x, "_dash_frozen")}.values()
            assert sorted(t3["member_ids"]) == sorted(ids)
            assert len(ids) == int((_DF["foreign"] == want).sum())

        src = r.sources["g1"]
        assert r._frozen_layer_tag("lfit", {}, src, None,
                                   ["nope", "weight"]) is None


class TestTheRegistry:

    def test_one_entry_per_layer_by_figure(self):
        r = _render(_spec([plot_for("scatter"), plot_for(_STAND_IN),
                           plot_for(_STAND_IN, {"lcolor": "red"})],
                          {"filter": "foreign, type(dropdown)"}))
        reg = r.frozen_layer_registry
        assert list(reg) == ["g1"]
        assert len(reg["g1"]) == 2
        for tag, rends in reg["g1"]:
            assert all(x._dash_frozen is tag for x in rends)
        r2 = _render(_spec([plot_for("scatter"), plot_for(_STAND_IN)],
                           {"filter": "foreign, type(dropdown)"},
                           {"by": "foreign"}))
        reg2 = r2.frozen_layer_registry
        assert sorted(reg2) == sorted(r2.figures)
        assert all(len(v) == 1 for v in reg2.values())
        r3 = _render(_spec([plot_for("scatter")]))
        assert r3.frozen_layer_registry == {}


class TestTheCueArgs:

    def test_the_models_and_lists(self):
        # fpfitci: a frozen ci layer (lfitci is refitted since WP-31 F1b).
        r = _render(_spec([plot_for("scatter"), plot_for(_STAND_IN),
                           plot_for("fpfitci")],
                          {"filter": "foreign, type(dropdown)",
                           "csv": "1"},
                          {"by": "foreign"}))
        cb = r.filter_callbacks[0]
        a = cb.args
        assert len(a["stale_titles"]) == len(r.figures)
        for k, f in r.figures.items():
            _one_cue(r, k)
        assert a["stale_status"].visible is False
        assert "dash_stale_status" in a["stale_status"].tags
        assert a["stale_status"].disable_math is True
        # One shared member source per distinct panel row set.
        assert len(a["stale_members"]) == 2
        assert len({tuple(m.data["id"]) for m in a["stale_members"]}) == 2
        cfgs = json.loads(a["stale_configs_json"])
        assert all("member_ids" not in c for c in cfgs)
        assert len(cfgs) == len(a["stale_renderers"]) == 4
        for c, rends in zip(cfgs, a["stale_renderers"]):
            for x in rends:
                assert x.muted is False
                assert x.muted_glyph is not None
                g = x.glyph
                for p in ("line_alpha", "fill_alpha"):
                    if p in g.properties() and isinstance(getattr(g, p),
                                                          (int, float)):
                        assert getattr(x.muted_glyph, p) == pytest.approx(
                            getattr(g, p) * 0.3)
            for k, text in c["items"]:
                assert _text(a["stale_legend_items"][k].label) == text
        assert json.loads(a["stale_text_json"]) == {
            "status_html": dr._DASH_STALE_STATUS_HTML}

    def test_the_status_is_last_before_the_csv_button(self):
        r = _render(_spec([plot_for("scatter"), plot_for(_STAND_IN)],
                          {"filter": "foreign, type(dropdown)",
                           "csv": "1"}))
        st = r.filter_callbacks[0].args["stale_status"]
        assert st not in r.filter_widgets
        row = self._filter_row(r)
        kids = list(row)
        i = kids.index(st)
        rest = kids[i + 1:]
        assert all(type(x).__name__ == "Button" for x in rest), rest

    @staticmethod
    def _filter_row(r):
        st = r.filter_callbacks[0].args["stale_status"]
        for m in r._last_layout_root.references():
            kids = getattr(m, "children", None)
            if isinstance(kids, list) and any(k is st for k in kids):
                return kids
        raise AssertionError("the status Div is in no layout")


class TestTheTitlePlacement:

    def test_the_cue_sits_nearest_the_frame_with_a_top_legend_and_subtitle(
            self):
        r = _render(_spec([plot_for("scatter"), plot_for(_STAND_IN)],
                          {"filter": "foreign, type(dropdown)"},
                          {"title": "T", "subtitle": "S",
                           "legend": "position(12)"}))
        f = r.figures["g1"]
        _one_cue(r)
        # Flipped (WP-30 P1.2a): the subtitle was a Label, which was wrong
        # because twoway places it by the scheme's clock; S15 draws it as a
        # side-panel Title, still outside the legend.
        assert [type(m).__name__ for m in f.above] == ["Title", "Legend",
                                                       "Title"]
        assert f.above[0].tags == ["dash_stale_cue"]

    def test_no_marked_figure_has_its_toolbar_above(self):
        seen = 0
        for bo, go in [({}, {}), ({}, {"by": "foreign"}),
                       ({"layout": "bs"}, {"by": "foreign"}),
                       ({"layout": "bs"}, {})]:
            r = _render(_spec([plot_for("scatter"), plot_for(_STAND_IN)],
                              dict(bo, filter="foreign, type(dropdown)"),
                              go))
            for f in r.figures.values():
                if any("dash_stale_cue" in (getattr(m, "tags", None) or [])
                       for m in f.above):
                    seen += 1
                    assert f.toolbar_location != "above"
        assert seen > 0


def _big_df(n=4000):
    rng = np.random.default_rng(0)
    return pd.DataFrame({
        "mpg": rng.normal(21, 5, n).round(1),
        "weight": rng.normal(3000, 700, n).round(0),
        "foreign": rng.integers(0, 2, n).astype(float),
        "price": rng.normal(6000, 2500, n).round(0),
        "rep": rng.integers(1, 6, n).astype(float),
        "when": 15340.0 + np.arange(n, dtype=float)})


_FOUR = ("foreign, type(dropdown) || price, type(range) || "
         "weight, type(slider) || rep, type(dropdown)")
_THREE = "foreign, type(dropdown) || price, type(range) || weight, type(slider)"


class TestThePageSize:

    def test_member_ids_are_one_shared_model_per_set(self):
        for filt in ("foreign, type(dropdown)", _THREE):
            r = _render(_spec([plot_for("scatter"), plot_for(_STAND_IN)],
                              {"filter": filt}, {"by": "foreign"}))
            cbs = r.filter_callbacks
            ms = cbs[0].args["stale_members"]
            assert len(ms) == 2
            assert all(cb.args["stale_members"] is ms for cb in cbs)
            assert len(cbs[0].args["stale_configs_json"]) < 2048
            html = _html(_spec([plot_for("scatter"), plot_for(_STAND_IN)],
                               {"filter": filt}, {"by": "foreign"}))
            assert html.count("dash_stale_members") == 2

    def test_page_size_grows_sublinearly_in_filters(self):
        df = _big_df()
        fit = [plot_for("scatter"), plot_for(_STAND_IN)]
        sc = [plot_for("scatter")]
        go = {"by": "foreign"}
        d_fit = (len(_html(_spec(fit, {"filter": _FOUR}, go), df))
                 - len(_html(_spec(fit, {"filter": "foreign, type(dropdown)"},
                                   go), df)))
        d_sc = (len(_html(_spec(sc, {"filter": _FOUR}, go), df))
                - len(_html(_spec(sc, {"filter": "foreign, type(dropdown)"},
                                  go), df)))
        r = _render(_spec(fit, {"filter": _FOUR}, go), df)
        assert "stale_members" in r.filter_callbacks[0].args
        assert d_fit - d_sc < 3 * 2048, (d_fit, d_sc)


def _html(spec, df=_DF):
    from test_saved_filter_layers import _write
    sp, dp = _write(spec, df)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return dr.DashRenderer(sp, dp).render()


# ---------------------------------------------------------------------------
# Hostile input
# ---------------------------------------------------------------------------

_HOSTILE = "</p><img src=x onerror=alert(1)>"


class TestTheCueAgainstHostileInput:

    @requires_node
    def test_a_hostile_label_is_data_not_markup(self):
        # The legend key's text is the user's: legend(label(2 "...")).
        spec = _spec([plot_for("scatter"), plot_for("histogram")],
                     {"filter": "foreign, type(dropdown)"},
                     {"legend": 'label(2 "%s")' % _HOSTILE})
        r = _render(spec)
        _one_cue(r)
        _act(r, ("Select", "Foreign"))
        f = r.figures["g1"]
        [it] = _items_of(f, _layer_rends(r))
        assert it.label.value == _HOSTILE + " (bins unfiltered)"
        assert _status(r) == (True, dr._DASH_STALE_STATUS_HTML)
        assert all(cb.code == dr._FILTER_JS for cb in r.filter_callbacks)
        assert "<img src=x onerror" not in _html(spec).lower()

    @requires_node
    def test_a_variable_named_proto_is_a_column(self):
        df = _DF.rename(columns={"mpg": "__proto__"})
        spec = _spec([plot_for(_STAND_IN, yvar="__proto__")],
                     {"filter": "foreign, type(dropdown)"})
        r = _render(spec, df)
        _act(r, ("Select", "Foreign"))
        _assert_marked(r)
        df2 = df.copy()
        df2.loc[df2["foreign"] == 0, "__proto__"] = np.nan
        r = _render(spec, df2)
        _act(r, ("Select", "Foreign"))
        _assert_clear(r)

    def test_every_callback_carries_the_same_lists(self):
        r = _render(_spec([plot_for("scatter"), plot_for(_STAND_IN)],
                          {"filter": _THREE}))
        cbs = r.filter_callbacks
        assert len(cbs) == 3
        keys = [k for k in cbs[0].args if k.startswith("stale_")]
        assert set(keys) == {"stale_configs_json", "stale_members",
                             "stale_renderers", "stale_titles",
                             "stale_legend_items", "stale_status",
                             "stale_text_json"}
        for k in keys:
            assert all(cb.args[k] is cbs[0].args[k] for cb in cbs), k

    def test_the_block_is_last_and_declares_no_arg(self):
        js = dr._FILTER_JS
        i = js.find('if (typeof stale_configs_json !== "undefined")')
        j = js.find("for (let ai = 0; ai < agg_configs.length; ai++)")
        assert j >= 0 and i > j
        assert re.search(r"\b(const|let|var|function)\s+stale_", js) is None
        assert "dash_stale_" not in js

    def test_the_brush_code_holds_no_stale_block(self):
        from test_mode_parity import _kpi
        spec = _spec([plot_for("scatter"), plot_for(_STAND_IN)],
                     {"filter": "foreign, type(dropdown)"},
                     kpis=[_kpi(update="brush")])
        r = _render(spec)
        from bokeh.models import CustomJS
        codes = [m.code for m in r._last_layout_root.references()
                 if isinstance(m, CustomJS) and m.code != dr._FILTER_JS]
        codes += [cb.code for f in r.figures.values()
                  for src in [f.renderers[0].data_source]
                  for cbs in src.js_property_callbacks.values()
                  for cb in cbs]
        assert codes, "no brush code on the page"
        assert not any("stale_configs_json" in c for c in codes)


# ---------------------------------------------------------------------------
# Both layouts
# ---------------------------------------------------------------------------

class TestBothLayouts:

    @pytest.mark.parametrize("layout,pos", [("auto", "top"),
                                            ("auto", "left"),
                                            ("bs", "top"), ("bs", "left")],
                             ids=["auto-top", "auto-left", "bs-top",
                                  "bs-left"])
    def test_the_title_is_in_each_figure_and_the_status_in_the_filter_area(
            self, layout, pos):
        spec = _spec([plot_for("scatter"), plot_for(_STAND_IN)],
                     {"filter": "foreign, type(dropdown) || "
                                "price, type(range)",
                      "layout": layout, "filter_position": pos},
                     {"by": "foreign"})
        from test_saved_filter_layers import _write
        sp, dp = _write(spec, _DF)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = dr.DashRenderer(sp, dp)
            page = r.render()
        for k in r.figures:
            _one_cue(r, k)
        st = r.filter_callbacks[0].args["stale_status"]
        if layout == "auto":
            want = "Row" if pos == "top" else "Column"
            holders = [m for m in r._last_layout_root.references()
                       if type(m).__name__ == want
                       and any(c is st for c in (getattr(m, "children", [])
                                                 or []))]
            assert holders, f"the status Div is in no filter {want}"
            assert any(any(c is w for c in h.children)
                       for h in holders for w in r.filter_widgets)
        else:
            cls = ("db-row db-filter-bar" if pos == "top"
                   else "db-sidebar-col")
            m = re.search(r'<div class="[^"]*\b' + re.escape(cls) + r'\b',
                          page)
            assert m, cls
            k = m.start()
            end = page.find('<div class="db-row', k + 10)
            if pos == "left":
                end = page.find('db-col-md-10', k)
            chunk = page[k:end if end > 0 else len(page)]
            assert f'data-root-id="{st.id}"' in chunk
