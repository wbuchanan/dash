"""
test_contour_key_moves.py -- after a filter move the contour's cuts and its
colour bar follow the kept rows (WP-31 B4d, section 29; DECISIONS D22).

The defect (measured after WP-31 B4c): twoway cuts a contour at the z
axis's ticks over the rows it draws (zlabel(#5) by default; levels(#)
over their z range), so ``twoway contour price mpg weight if foreign == 1``
cuts where the rule puts the subset's ticks.  After a move the served app
redrew the bands at the kept rows' cuts but its ContourColorBar kept the
build's levels and ticks -- a bar whose level count no longer matched the
bands, which BokehJS refuses to paint ("Inconsistent number of filled
contour levels") -- and the saved page's refit (B4c) cut the kept rows at
the build's cuts.

Now both modes recompute the cuts with twoway's rule after a move
(``_dash_contour_cut_rule`` hands the rule to the page's
``dash_contour_cuts``/``dash_contour_fill_levels``, twins of
``_dash_contour_cuts``/``_dash_contour_fill_levels``), colour the bands
for their new count, and give the colour bar the new cuts and ticks.  The
bar keeps the span it was built with (``_dash_contour_bar_follow``):
BokehJS sizes a contour colour bar's range once, from its first levels.
"""
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import js_runner  # noqa: E402
from js_runner import requires_node, run_js  # noqa: E402
import test_contour_js as cj  # noqa: E402
import test_contour_layers as cl  # noqa: E402
import test_horizontal_moves as hm  # noqa: E402
import test_saved_filter_layers as sf  # noqa: E402

#: (zmin, zmax) pairs the rule is run over.
_RANGES = [(12.0, 41.0), (14.0, 35.0), (-3.25, 2.5), (3291.0, 15906.0),
           (0.001, 0.009)]


def _js(code):
    js = dr._FILTER_JS
    nat = js[js.index("function dash_natscale"):
             js.index("function dash_axis_ticks")]
    return cj._js(nat + "\n" + code)


def _bar(figs):
    [b] = cl._bars(figs[0])
    return b


def _contour(figs):
    [cr] = cl._contours(figs[0])
    return cr


# ---------------------------------------------------------------------------
# The rule's twin
# ---------------------------------------------------------------------------

class TestTheRule:

    @pytest.mark.parametrize("probe", sorted(cl._CUT_PROBES))
    def test_rule_reads_the_options(self, probe):
        opts, go = cl._CUT_PROBES[probe]
        rule = dr._dash_contour_cut_rule(opts, go)
        assert rule["kind"] in ("cuts", "levels", "ticks", "count", "minmax")
        json.dumps(rule, allow_nan=False)
        if probe == "default":
            assert rule == {"kind": "count", "n": 5}

    @requires_node
    def test_js_cuts_follow_python(self):
        cases, want = [], []
        for probe, (opts, go) in sorted(cl._CUT_PROBES.items()):
            rule = dr._dash_contour_cut_rule(opts, go)
            for lo, hi in _RANGES:
                cuts, ticks = dr._dash_contour_cuts(opts, lo, hi, go)
                cases.append([rule, lo, hi])
                want.append([probe, [float(c) for c in cuts],
                             [float(t) for t in ticks],
                             dr._dash_contour_fill_levels(cuts, ticks, lo,
                                                          hi)])
        got = _js("out(%s.map(([r, lo, hi]) => { const c = "
                  "dash_contour_cuts(r, lo, hi); return [c.cuts, c.ticks, "
                  "dash_contour_fill_levels(c.cuts, c.ticks, lo, hi)]; }));"
                  % json.dumps(cases))
        for (probe, cuts, ticks, lv), (gc, gt, gl) in zip(want, got):
            assert gc == pytest.approx(cuts, rel=1e-15, abs=0), probe
            assert gt == pytest.approx(ticks, rel=1e-15, abs=0), probe
            assert gl == pytest.approx(lv, rel=1e-15, abs=0), probe


# ---------------------------------------------------------------------------
# After a move
# ---------------------------------------------------------------------------

def _spec(ptype="contour", opts=None, go=None, filt=None):
    spec = cj._page_spec(ptype, opts, filt)
    if go:
        spec["graphs"][0].setdefault("graph_options", {}).update(go)
    return spec


#: (options, graph options): the rules whose cuts follow the rows.
_FOLLOWING = {
    "default": ({}, None),
    "levels4": ({"levels": "4"}, None),
    "zlabel3": ({}, {"zlabel": "#3"}),
}


class TestServed:

    @pytest.mark.parametrize("rule", sorted(_FOLLOWING))
    def test_the_bar_follows_the_move(self, rule):
        opts, go = _FOLLOWING[rule]
        _l, filt, action, oracle = sf._MOVES[0]
        df = cj._page_df()
        spec = _spec("contour", opts, go, filt)
        doc, after = hm._served_moved(spec, action, df)
        kept = hm._kept(spec, oracle, "served", df=df)
        b, k = _bar(after), _bar(kept)
        cr, kcr = _contour(after), _contour(kept)
        nband = len(cr.fill_renderer.data_source.data["xs"])
        # the bar's level count matches the bands (BokehJS asserts it)
        assert len(b.levels) == nband + 1
        assert list(b.levels[1:-1]) == pytest.approx(list(k.levels[1:-1]))
        assert list(kcr.levels[1:-1]) == list(k.levels[1:-1])
        e0, e1 = b.levels[0], b.levels[-1]
        assert list(b.ticker.ticks) == [t for t in k.ticker.ticks
                                         if e0 <= t <= e1]
        assert {float(t): v for t, v in b.major_label_overrides.items()} \
            == {float(t): v for t, v in k.major_label_overrides.items()
                if e0 <= float(t) <= e1}


@requires_node
class TestSaved:

    @pytest.mark.parametrize("rule", sorted(_FOLLOWING))
    def test_bands_and_bar_follow_the_move(self, rule):
        opts, go = _FOLLOWING[rule]
        _l, filt, action, oracle = sf._MOVES[0]
        df = cj._page_df()
        spec = _spec("contour", opts, go, filt)
        r, after = hm._saved_moved(spec, action, df)
        kept = hm._kept(spec, oracle, "saved", df=df)
        a = _contour(after).fill_renderer.data_source.data
        k = _contour(kept).fill_renderer.data_source.data
        assert len(a["xs"]) == len(k["xs"])
        assert list(a["fill_color"]) == list(k["fill_color"])
        assert list(a["lower_levels"]) == pytest.approx(
            list(k["lower_levels"]), rel=1e-9)
        sub = df.query(oracle)
        X, Y = cj._grid(sub["weight"], sub["mpg"])
        agree = (cj._raster(a["xs"], a["ys"], X, Y)
                 == cj._raster(k["xs"], k["ys"], X, Y)).mean()
        assert agree >= 0.999, agree
        b, kb = _bar(after), _bar(kept)
        assert len(b.levels) == len(a["xs"]) + 1
        assert list(b.levels[1:-1]) == pytest.approx(list(kb.levels[1:-1]),
                                                     rel=1e-12)
        e0, e1 = b.levels[0], b.levels[-1]
        assert list(b.ticker.ticks) == pytest.approx(
            [t for t in kb.ticker.ticks if e0 <= t <= e1], rel=1e-12)
        assert sorted(b.major_label_overrides.values()) == sorted(
            v for t, v in kb.major_label_overrides.items()
            if e0 <= float(t) <= e1)

    def test_contourline_levels_and_colours_follow(self):
        _l, filt, action, oracle = sf._MOVES[0]
        df = cj._page_df()
        spec = _spec("contourline", {"colorlines": "colorlines"}, None, filt)
        r, after = hm._saved_moved(spec, action, df)
        kept = hm._kept(spec, oracle, "saved", df=df)
        a = _contour(after).line_renderer.data_source.data
        k = _contour(kept).line_renderer.data_source.data
        assert list(a["levels"]) == pytest.approx(list(k["levels"]))
        assert list(a["line_color"]) == list(k["line_color"])
        assert list(a["line_width"]) == list(k["line_width"])


def _level_legend(figs):
    """contourline's level legend (WP-42 LT-22): each drawn item's (label,
    line colour, line width), highest level first."""
    from bokeh.models import Legend
    out = []
    for f in figs:
        for lg in f.select({"type": Legend}):
            if lg.name != dr._COLORVAR_LEGEND_NAME:
                continue
            for it in lg.items:
                lab = it.label
                v = getattr(lab, "value", None)
                if v is None and isinstance(lab, dict):
                    v = lab.get("value")
                g = it.renderers[0].glyph
                out.append((str(lab if v is None else v), str(g.line_color),
                            round(float(g.line_width), 6)))
    return out


class TestTheLevelLegendFollows:
    """LT-22: after a filter move twoway keys contourline's levels for the
    lines it draws over the kept rows (colorlines: one key a cut, highest
    first, in its line's colour and width); dash's legend kept the build's
    levels in both modes."""

    def _case(self):
        _l, filt, action, oracle = sf._MOVES[0]
        df = cj._page_df()
        spec = _spec("contourline", {"colorlines": "colorlines"}, None, filt)
        return spec, action, oracle, df

    def test_served(self):
        spec, action, oracle, df = self._case()
        _doc, after = hm._served_moved(spec, action, df)
        kept = hm._kept(spec, oracle, "served", df=df)
        want = _level_legend(kept)
        assert want
        assert _level_legend(after) == want

    @requires_node
    def test_saved(self):
        spec, action, oracle, df = self._case()
        _r, after = hm._saved_moved(spec, action, df)
        kept = hm._kept(spec, oracle, "saved", df=df)
        want = _level_legend(kept)
        assert want
        assert _level_legend(after) == want
