"""twoway's fit options atobs, nofit, fitplot(), ciplot(), smoothplot(),
estopts(), predopts() and estcmd() (WP-31 C4, GAPS3 C4).

They were declared nowhere: each fell to the parser's catch-all and was
named in "ignoring unsupported option(s)".  Measured on StataNow 19.5
(test/fixtures/fit_options_truth.json, scripts/extract_fit_options_truth.do):

* ``atobs`` evaluates lfit, qfit, lfitci and qfitci at the observed x, not
  on the n() grid (F01: 74 points on auto, duplicates kept); fpfitci takes
  it and draws as without it.  With range() it is refused, "may not combine
  atobs with range()", r(198).
* ``nofit`` keeps the band of lfitci, qfitci, fpfitci and lpolyci and drops
  the line and its key.
* ``fitplot()`` draws the line as one of yxtype's eight, ``ciplot()`` the
  band as a range type (or a yx type through its lower limit); an unknown
  name prints twoway's two notes.  lpolyci's ``smoothplot()`` is declared
  by its parser and never read: the graph is the one without it.
* ``estopts()``, ``predopts()`` and ``estcmd()`` are handed to regress,
  predict and fracpoly; dash.ado runs them in Stata at registration and
  writes the points, which the renderers draw as stored and never refit
  (maintainer decision D3): the saved page marks the layer stale after a
  move (kind "fit", no ``_dash_agg_*`` tag), the served app notes it.
"""
import json
import os
import re
import sys
import warnings

import numpy as np
import pytest
from bokeh.models import GlyphRenderer, Legend, Plot, Scatter

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from js_runner import requires_node  # noqa: E402
from test_mode_parity import (_DF, _fire, _served, _spec,  # noqa: E402
                              _standalone, _widgets_of)
from test_saved_filter_layers import _MOVES, _render  # noqa: E402
from test_saved_stale_cue import _act, _one_cue, _text  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_ROOT = os.path.dirname(_HERE)
_FIX = os.path.join(_HERE, "fixtures", "fit_options_truth.json")
_MODES = ["saved", "served"]
_CI = ["lfitci", "qfitci", "fpfitci", "lpolyci"]


def _truth():
    with open(_FIX, encoding="utf-8") as fh:
        return json.load(fh)


def _ado():
    with open(os.path.join(_ROOT, "dash.ado"), encoding="utf-8") as fh:
        return fh.read()


def _layer(mode, plots, bo=None):
    """``(renderers of figure g1, legend labels, warnings)`` in *mode*."""
    spec = _spec(plots, bo)
    if mode == "saved":
        r, w = _standalone(spec)
        fig = r.figures["g1"]
    else:
        doc, w = _served(spec)
        figs = [m for m in doc.models if isinstance(m, Plot)
                and any(isinstance(x, GlyphRenderer) for x in m.renderers)]
        assert len(figs) == 1, len(figs)
        fig = figs[0]
    rends = [x for x in fig.renderers if isinstance(x, GlyphRenderer)]
    labels = [_text(i.label) for side in (fig.center, fig.above, fig.below,
                                          fig.left, fig.right)
              for L in side if isinstance(L, Legend) for i in L.items]
    return rends, labels, w


def _xs(r):
    d = r.data_source.data
    col = r.glyph.x if isinstance(r.glyph.x, str) else r.glyph.x.field
    return [float(v) for v in d[col]]


def _ys(r, attr="y"):
    d = r.data_source.data
    v = getattr(r.glyph, attr)
    col = v if isinstance(v, str) else v.field
    return [float(t) for t in d[col]]


# ---------------------------------------------------------------------------
# atobs
# ---------------------------------------------------------------------------

class TestAtobs:

    def test_grid_is_the_observed_x(self):
        x = np.array([3.0, 1.0, 2.0, 2.0, 5.0])
        got = dr._fit_grid(x, {"atobs": "atobs", "n": "7"}, "lfit")
        assert list(got) == [1.0, 2.0, 3.0, 5.0]

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("t", ["lfit", "qfit", "lfitci", "qfitci"])
    def test_the_layer_is_drawn_at_the_observed_x(self, mode, t):
        rends, _, _ = _layer(mode, [plot_for(t, {"atobs": "atobs"})])
        line = [r for r in rends if type(r.glyph).__name__ == "Line"][-1]
        assert _xs(line) == sorted(set(_DF["weight"]))

    def test_twoways_points_are_the_observed_x(self):
        # F01: lfit mpg weight, atobs -- one point per observation, in x
        # order; dash draws each distinct x once, the same line.
        f01 = _truth()["points"]["F01"]
        assert len(f01["x"]) == 74 and f01["x"] == sorted(f01["x"])

    @pytest.mark.parametrize("t", ["lfit", "qfit"])
    def test_config_key(self, t):
        # The saved page's refit reads cfg.atobs (S16's dash_fit_grid).
        for opts, want in (({"atobs": "atobs"}, True), ({}, False)):
            r, _ = _standalone(_spec([plot_for(t, opts)]))
            tagged = [x for x in r.figures["g1"].renderers
                      if hasattr(x, "_dash_agg_config")]
            assert tagged, t
            assert tagged[0]._dash_agg_config["atobs"] is want


# ---------------------------------------------------------------------------
# nofit
# ---------------------------------------------------------------------------

class TestNofit:

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("t", _CI)
    def test_line_hidden_band_kept(self, mode, t):
        rends, labels, _ = _layer(mode, [plot_for(t, {"nofit": "nofit"})])
        lines = [r for r in rends if type(r.glyph).__name__ == "Line"]
        bands = [r for r in rends if type(r.glyph).__name__ == "VArea"]
        assert lines and all(r.visible is False for r in lines)
        assert bands and all(r.visible is not False for r in bands)
        assert labels == ["95% CI"], labels

    @pytest.mark.parametrize("t", _CI)
    def test_without_it_the_line_is_drawn(self, t):
        rends, labels, _ = _layer("saved", [plot_for(t)])
        lines = [r for r in rends if type(r.glyph).__name__ == "Line"]
        assert lines and all(r.visible is not False for r in lines)
        assert len(labels) == 2


# ---------------------------------------------------------------------------
# fitplot(), ciplot()
# ---------------------------------------------------------------------------

def _kinds(rends):
    return sorted(type(r.glyph).__name__ for r in rends
                  if r.visible is not False)


class TestFitplotCiplot:

    @pytest.mark.parametrize("mode", _MODES)
    def test_fitplot_scatter(self, mode):
        rends, _, _ = _layer(mode, [plot_for("lfitci",
                                             {"fitplot": "scatter"})])
        assert "Scatter" in _kinds(rends)
        assert "Line" not in _kinds(rends)
        assert "VArea" in _kinds(rends)

    @pytest.mark.parametrize("mode", _MODES)
    def test_ciplot_rcap_draws_caps(self, mode):
        rends, _, _ = _layer(mode, [plot_for("lfitci", {"ciplot": "rcap"})])
        k = _kinds(rends)
        assert "VArea" not in k, k
        assert "Segment" in k or "MultiLine" in k, k
        assert "Line" in k, k

    @pytest.mark.parametrize("mode", _MODES)
    def test_ciplot_yx_type_draws_the_lower_limit(self, mode):
        base, _, _ = _layer(mode, [plot_for("lfitci")])
        band = [r for r in base if type(r.glyph).__name__ == "VArea"][0]
        lo = _ys(band, "y1")
        rends, _, _ = _layer(mode, [plot_for("lfitci",
                                             {"ciplot": "scatter"})])
        sc = [r for r in rends if isinstance(r.glyph, Scatter)]
        assert sc and np.allclose(_ys(sc[0]), lo)

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("t", ["qfitci", "fpfitci", "lpolyci"])
    def test_each_ci_type(self, mode, t):
        rends, _, _ = _layer(mode, [plot_for(t, {"fitplot": "connected",
                                                 "ciplot": "rline"})])
        k = _kinds(rends)
        assert "Scatter" in k and "VArea" not in k, k

    def test_draw_range_as_names_an_unknown_target(self):
        rends, _, w = _layer("saved", [plot_for("lfitci",
                                                {"ciplot": "bogus"})])
        assert any("no glyph mapper" in m for m in w), w


# ---------------------------------------------------------------------------
# estopts(), predopts(), estcmd(): Stata's points, drawn as stored
# ---------------------------------------------------------------------------

_PTS = {"x": [2000.0, 3000.0, 4000.0], "y": [11.0, 21.0, 31.0], "nobs": 10}
_PTS_CI = {"x": [2000.0, 3000.0, 4000.0], "y": [11.0, 21.0, 31.0],
           "lo": [9.0, 20.0, 28.0], "hi": [13.0, 22.0, 34.0], "nobs": 10}


def _pts_plot(t):
    pts = _PTS_CI if t.endswith("ci") else _PTS
    return plot_for(t, {"estopts": "noconstant", "points": dict(pts)})


class TestEstoptsPoints:

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("t", ["lfit", "qfit", "fpfit", "lfitci",
                                   "qfitci", "fpfitci"])
    def test_points_are_drawn_as_stored(self, mode, t, monkeypatch):
        def boom(*a, **k):
            raise AssertionError("a points layer was fitted")
        monkeypatch.setattr(dr, "_dash_wls", boom)
        monkeypatch.setattr(dr.GlyphMapper, "_fp_fit", boom)
        rends, _, _ = _layer(mode, [_pts_plot(t)])
        line = [r for r in rends if type(r.glyph).__name__ == "Line"][-1]
        assert _xs(line) == _PTS["x"] and _ys(line) == _PTS["y"]
        if t.endswith("ci"):
            band = [r for r in rends if type(r.glyph).__name__ == "VArea"][0]
            assert _ys(band, "y1") == _PTS_CI["lo"]
            assert _ys(band, "y2") == _PTS_CI["hi"]

    def test_the_helper_reads_and_checks(self):
        got = dr._dash_fit_points_of({"points": dict(_PTS_CI)})
        assert [list(a) for a in got] == [_PTS_CI[k] for k in
                                          ("x", "y", "lo", "hi")]
        got = dr._dash_fit_points_of({"points": {"x": [1, 2],
                                                 "y": [3, None]}})
        assert np.isnan(got[1][1]) and got[2] is None
        assert dr._dash_fit_points_of({}) is None
        for bad in ({"x": [1], "y": [1, 2]}, {"x": "1", "y": [1]},
                    {"x": [1, "a"], "y": [1, 2]}, [1, 2],
                    {"x": [1] * 100001, "y": [1] * 100001}):
            assert dr._dash_fit_points_of({"points": bad}) is False

    def test_bad_points_note(self):
        rends, _, w = _layer("saved", [plot_for(
            "lfit", {"estopts": "noconstant", "points": {"x": [1]}})])
        assert any("estopts()/predopts()/estcmd()" in m and
                   "cannot be read" in m for m in w), w
        line = [r for r in rends if type(r.glyph).__name__ == "Line"][-1]
        assert _xs(line) == []

    @pytest.mark.parametrize("t", ["lfit", "lfitci"])
    def test_saved_page_marks_it_frozen(self, t):
        r = _render(_spec([plot_for("scatter"), _pts_plot(t)],
                          {"filter": _MOVES[0][1]}))
        rends = list(r.figures["g1"].renderers[1:])
        assert rends
        for x in rends:
            assert not hasattr(x, "_dash_agg_config")
            assert x._dash_frozen["kind"] == "fit"

    @requires_node
    def test_a_saved_move_marks_it_unfiltered(self):
        r = _render(_spec([plot_for("scatter"), _pts_plot("lfit")],
                          {"filter": _MOVES[0][1]}))
        cue = _one_cue(r)
        line = r.figures["g1"].renderers[1]
        before = list(line.data_source.data["y"])
        _act(r, _MOVES[0][2])
        assert cue.visible is True and line.muted is True
        assert list(line.data_source.data["y"]) == before

    def test_served_move_keeps_points(self):
        doc, _ = _served(_spec([plot_for("scatter"), _pts_plot("lfit")],
                               {"filter": _MOVES[0][1]}))
        sel = [w for w in _widgets_of(doc) if type(w).__name__ == "Select"]
        raw = [v for v, lab in sel[0].options if lab == "Foreign"][0]
        dr._DASH_NOTED.clear()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            _fire(sel[0], raw)
            _fire(sel[0], raw)
        figs = [m for m in doc.models if isinstance(m, Plot)
                and any(isinstance(x, GlyphRenderer) for x in m.renderers)]
        lines = [x for x in figs[0].renderers
                 if type(getattr(x, "glyph", None)).__name__ == "Line"]
        assert _ys(lines[-1]) == _PTS["y"]
        # Flipped (WP-32, BUGS.md "Found by the runtime-notes parity
        # entry: a fit drawn from Stata's points is stale after a move and
        # the served page does not say so"): the app wrote one note to the
        # server's log, which no reader of the page sees; the page now
        # shows the saved page's cue -- the key's suffix, the caption and a
        # status line worded for dash serve -- and the log says nothing.
        notes = [str(c.message) for c in caught
                 if "is drawn as registered" in str(c.message)]
        assert notes == [], notes
        keys = [str(it.label.get("value") if isinstance(it.label, dict)
                    else getattr(it.label, "value", it.label))
                for m in doc.models if type(m).__name__ == "LegendItem"
                for it in [m]]
        assert "Fitted values" + dr._DASH_STALE_SUFFIX["fit"] in keys, keys
        cues = [m for m in doc.models if type(m).__name__ == "Title"
                and m.text == dr._DASH_STALE_CUE_TEXT]
        assert [c.visible for c in cues] == [True], cues
        status = [m for m in doc.models if type(m).__name__ == "Div"
                  and m.text == dr._DASH_STALE_SERVED_HTML]
        assert [d.visible for d in status] == [True], status

    def test_served_move_back_clears_the_cue(self):
        """Every row kept again: the layer is Stata's fit of them, so the
        served cue is taken off (the saved page's rule, P0.17)."""
        doc, _ = _served(_spec([plot_for("scatter"), _pts_plot("lfit")],
                               {"filter": _MOVES[0][1]}))
        sel = [w for w in _widgets_of(doc) if type(w).__name__ == "Select"]
        raw = [v for v, lab in sel[0].options if lab == "Foreign"][0]
        first = sel[0].value
        _fire(sel[0], raw)
        _fire(sel[0], first)
        cues = [m for m in doc.models if type(m).__name__ == "Title"
                and m.text == dr._DASH_STALE_CUE_TEXT]
        assert cues and not any(c.visible for c in cues)
        keys = [str(m.label.get("value") if isinstance(m.label, dict)
                    else getattr(m.label, "value", m.label))
                for m in doc.models if type(m).__name__ == "LegendItem"]
        assert "Fitted values" in keys, keys

    def test_attach_puts_points_on_a_fit_layer(self):
        spec = _spec([plot_for("lfit", {"estopts": "noconstant"}),
                      plot_for("scatter")])
        spec["function_points"] = {"g1": {"1": dict(_PTS), "2": dict(_PTS)}}
        out = dr._dash_attach_function_points(spec)
        plots = out["graphs"][0]["plots"]
        assert plots[0]["options"]["points"] == _PTS
        assert "points" not in plots[1]["options"]
        assert "points" not in plots[1]


class TestTheServedStaleCue:
    """The served page's cue for a fit drawn from Stata's points (WP-32,
    BUGS.md "Found by the runtime-notes parity entry: a fit drawn from
    Stata's points is stale after a move and the served page does not say
    so"), helper by helper."""

    @staticmethod
    def _agg():
        from bokeh.plotting import figure
        fig = figure()
        line = fig.line([1, 2], [3, 4], legend_label="Fitted values")
        dots = fig.scatter([1, 2], [3, 4], legend_label="Mileage")
        return fig, line, dots, {("g1", 1): {"frozen": [line], "fig": fig},
                                 ("g1", 0): {"sources": []}}

    @staticmethod
    def _keys(fig):
        return [it.label.get("value") if isinstance(it.label, dict)
                else it.label.value for it in fig.legend[0].items]

    def test_the_caption_is_the_saved_pages(self):
        t = dr._dash_stale_cue_title()
        assert (t.text, t.visible, t.tags) == (
            dr._DASH_STALE_CUE_TEXT, False, ["dash_stale_cue"])

    def test_models_give_one_caption_per_figure_and_one_status(self):
        fig, _l, _d, aggs = self._agg()
        aggs[("g1", 2)] = {"frozen": [_l], "fig": fig}
        status = dr._dash_points_stale_models(aggs)
        assert status.text == dr._DASH_STALE_SERVED_HTML
        assert status.visible is False
        assert fig.above[0] is aggs[("g1", 1)]["cue"] \
            is aggs[("g1", 2)]["cue"]
        assert len([m for m in fig.above
                    if m.text == dr._DASH_STALE_CUE_TEXT]) == 1
        assert "cue" not in aggs[("g1", 0)]

    def test_models_are_none_without_a_points_layer(self):
        assert dr._dash_points_stale_models({("g", 0): {"sources": []}}) \
            is None

    def test_follow_marks_a_stale_layer_and_clears_it(self):
        fig, _l, _d, aggs = self._agg()
        status = dr._dash_points_stale_models(aggs)
        aggs[("g1", 1)]["stale"] = True
        dr._dash_points_stale_follow(aggs)
        assert self._keys(fig) == ["Fitted values (unfiltered)", "Mileage"]
        assert fig.above[0].visible and status.visible
        dr._dash_points_stale_follow(aggs)   # twice: one suffix
        assert self._keys(fig)[0] == "Fitted values (unfiltered)"
        aggs[("g1", 1)]["stale"] = False
        dr._dash_points_stale_follow(aggs)
        assert self._keys(fig) == ["Fitted values", "Mileage"]
        assert not fig.above[0].visible and not status.visible


# ---------------------------------------------------------------------------
# The fixture, the ado text, the served copy
# ---------------------------------------------------------------------------

#: Where each option is taken, as dash.ado's _dash_fit_opts_check lists it.
_APPLIES = {"atobs": ["lfit", "qfit", "lfitci", "qfitci", "fpfitci"],
            "nofit": _CI, "fitplot": _CI, "ciplot": _CI,
            "smoothplot": ["lpolyci"],
            "estopts": ["lfit", "qfit", "lfitci", "qfitci", "fpfit",
                        "fpfitci"],
            "predopts": ["lfit", "qfit", "lfitci", "qfitci", "fpfit",
                         "fpfitci"],
            "estcmd": ["fpfit", "fpfitci"]}


class TestTheFixture:

    def test_meta_and_values(self):
        d = _truth()
        assert sorted(d["_meta"]) == ["born_date", "dash_commit",
                                      "extracted", "source", "stata_version"]
        assert d["_meta"]["source"] == "scripts/extract_fit_options_truth.do"
        for o, types in _APPLIES.items():
            took = [t for t in d["types"] if d["applies"][f"{o}@{t}"]["rc"] == 0]
            assert sorted(took) == sorted(types), o
        r = d["refusals"]
        assert (r["atobs_range"]["rc"], r["atobs_range"]["message"]) == (
            198, "may not combine atobs with range()")
        assert r["predopts_resid_range"]["message"] == (
            "may not combine residuals with range()")
        assert r["predopts_stdp_range"]["rc"] == 0
        assert r["fitplot_bogus"]["notes"] == [
            "(note:  named style bogus not found in class yxtype, default "
            "attributes used)",
            "(note:  yxtype not found in scheme, default attributes used)"]
        f04 = d["points"]["F04"]
        assert len(f04["x"]) == 100 and len(f04["lo"]) == 100

    def test_the_ado_lists_agree_with_the_fixture(self):
        src = _ado()
        body = src[src.index("program define _dash_fit_opts_check"):]
        body = body[:body.index("\nend\n")]
        for o, types in _APPLIES.items():
            m = re.search(r'local _fo_%s "([^"]*)"' % o, body)
            assert m, o
            assert sorted(m.group(1).split()) == sorted(types), o


class TestTheServedCopy:

    def test_names_defined(self):
        from test_mode_parity import _write
        _, sp, dp = _write(_spec([plot_for("lfit")]))
        ap = sp[:-5] + "_app.py"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(ap)
        with open(ap, encoding="utf-8") as fh:
            src = fh.read()
        assert "def _dash_fit_points_of(" in src


class TestTheAdoText:

    def test_declared_not_pending(self):
        src = _ado()
        body = src[src.index("program define _dash_parse_plot_opts"):]
        body = body[:body.index("\nend\n")]
        for word in ("ATObs", "ESTopts(string asis)", "PREDopts(string asis)",
                     "ESTCmd(string asis)", "FITPlot(string)",
                     "CIPlot(string)", "SMOOTHPlot(string)", "noFIT"):
            assert word in body, word
        pend = body[body.index('local _dash_pending ""'):
                    body.index("local _dash_unknown")]
        for o in _APPLIES:
            assert f"local {o}'" not in pend, o
