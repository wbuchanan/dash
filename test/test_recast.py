"""recast(), recastas() and type() drawn as twoway draws them (WP-30 P1.8b).

dash.ado reads the option (``_dash_recast_opt``; its parse, refusals,
spellings, fallbacks and notes are the RC cases of
test/test_twoway_option_parity.cscript) and writes a base, range, pc or
time-series layer as the type it is drawn as, the typed type kept as
``recast_from``; a derived layer (a fit, a smoother, kdensity, function,
histogram, scatteri) keeps its type and carries the target as
``options.recast``, which its mapper hands to
``GlyphMapper._dash_draw_xy_as``.  twoway's drawings are
test/fixtures/recast_truth.json (scripts/extract_recast_truth.do).
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
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_join_order as jo  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "recast_truth.json")
_HELP = os.path.join(os.path.dirname(_HERE), "dash.sthlp")


def _truth():
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _glyphs(fig):
    return [type(g.glyph).__name__ for g in fig.renderers]


# ===========================================================================
# The draw-as helper
# ===========================================================================

class TestTheDrawAsHelper:

    def test_each_target(self):
        """Each of the eight targets draws what its own mapper draws on
        the same points."""
        bad = []
        for t in dr.GlyphMapper._RECAST_DRAWN:
            pts = {"x": [1.0, 2.0, 3.0, 4.0, 5.0],
                   "y": [2.0, 1.0, 4.0, 3.0, 5.0]}
            f1, f2 = figure(), figure()
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                r = dr.GlyphMapper()._dash_draw_xy_as(
                    f1, ColumnDataSource(dict(pts)), "x", "y", t,
                    {"recast": t})
                getattr(dr.GlyphMapper(), "map_" + t)(
                    f2, ColumnDataSource(dict(pts)), "y", "x", {})
            if _glyphs(f1) != _glyphs(f2) or r is not f1.renderers[0]:
                bad.append((t, _glyphs(f1), _glyphs(f2)))
        assert not bad, bad

    def test_an_unknown_target_draws_nothing_and_says_so(self):
        for t in ("bogus", "__class__", "rline"):
            fig = figure()
            with pytest.warns(UserWarning, match="no glyph mapper"):
                r = dr.GlyphMapper()._dash_draw_xy_as(
                    fig, ColumnDataSource({"x": [1.0], "y": [1.0]}),
                    "x", "y", t, {})
            assert r is None and not fig.renderers


# ===========================================================================
# Both render modes
# ===========================================================================

#: (derived layer, target, the glyph classes the target draws).
_DERIVED = [
    ("lfit", "scatter", ["Scatter"]),
    ("qfit", "line", ["Line"]),
    ("lowess", "area", ["VArea"]),
    ("lpoly", "bar", ["VBar"]),
    ("fpfit", "spike", ["Segment"]),
    ("mspline", "dropline", ["Segment", "Scatter"]),
    ("mband", "connected", ["Line", "Scatter"]),
    ("kdensity", "bar", ["VBar"]),
    ("function", "scatter", ["Scatter"]),
    ("histogram", "line", ["Line"]),
    ("scatteri", "line", ["Line"]),
]


def _derived_spec(recast):
    graphs = []
    for i, (t, target, _) in enumerate(_DERIVED):
        p = plot_for(t, {"recast": target} if recast else {})
        graphs.append((f"g{i}", [p]))
    return tp._spec(graphs=graphs)


_BUILT = {}


def _figs(mode, recast):
    key = (mode, recast)
    if key not in _BUILT:
        spec = _derived_spec(recast)
        if mode == "saved":
            figs = jo._saved_figs(jo._saved(spec, tp._DF))
        else:
            figs = jo._served_figs(jo._served(spec, tp._DF))
        _BUILT[key] = figs
    return _BUILT[key]


def _points(fig):
    """The (x, y) points a layer drew: a Line/Scatter/VArea/VBar's x and y
    columns, a histogram's quad midpoints and tops."""
    out = set()
    for g in fig.renderers:
        d = g.data_source.data
        if "top" in d and "left" in d:
            for lo, hi, t in zip(d["left"], d["right"], d["top"]):
                out.add((round((float(lo) + float(hi)) / 2, 6),
                         round(float(t), 6)))
        else:
            for xc in [k for k in d if k == "x" or k.startswith("x_")]:
                yc = "y" + xc[1:]
                if yc not in d:
                    continue
                for a, b in zip(d[xc], d[yc]):
                    if a is not None and b is not None and a == a and b == b:
                        out.add((round(float(a), 6), round(float(b), 6)))
    return out


@pytest.mark.parametrize("mode", ["saved", "served"])
class TestDerivedRecast:

    def test_type(self, mode):
        """Each derived layer is drawn as its target, at the points the
        un-recast layer draws (lfit at twoway's three)."""
        drawn, plain = _figs(mode, True), _figs(mode, False)
        assert len(drawn) == len(plain) == len(_DERIVED)
        bad = []
        for (t, target, want), fr, fp in zip(_DERIVED, drawn, plain):
            got = [c for c in _glyphs(fr) if c not in ("Text",)]
            if got != want:
                bad.append((t, target, "glyphs", got))
                continue
            pr, pp = _points(fr), _points(fp)
            if t == "lfit":
                xs = sorted(pp)
                pp = {xs[0], xs[-1]}
                pr = {p for p in pr if p[0] in (xs[0][0], xs[-1][0])}
            if not pr or not pr <= pp | _points(fr):
                bad.append((t, target, "points"))
            if t != "lfit" and pr != pp:
                bad.append((t, target, "points differ", len(pr), len(pp)))
        assert not bad, bad

    def test_bar_is_one_unit_wide(self, mode):
        """kdensity, recast(bar): S14's one-x-unit bar."""
        fig = _figs(mode, True)[[t for t, _, _ in _DERIVED].index("kdensity")]
        bars = [g.glyph for g in fig.renderers
                if type(g.glyph).__name__ == "VBar"]
        assert bars and all(float(b.width) == 1.0 for b in bars)


class TestRecastKeepsTheSeriesLabel:

    def test_key(self):
        """A derived layer keeps its type, so its key is the un-recast
        layer's; a base layer's is the variables' as before."""
        assert (dr._dash_legend_key(plot_for("lfit", {"recast": "scatter"}))
                == dr._dash_legend_key(plot_for("lfit")))
        p = {"type": "line", "recast_from": "rline", "yvar": "mpg",
             "xvar": "weight", "options": {}}
        assert dr._dash_legend_key(p) == "mpg"


class TestBaseRecast:
    """Guards: a base layer's spec names the drawn type, which both modes
    draw as the plain type."""

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_drawn_as_the_target(self, mode):
        pairs = [("scatter", "line"), ("line", "scatter"),
                 ("scatter", "connected"), ("scatter", "bar"),
                 ("rarea", "rline"), ("rspike", "rcap"),
                 ("pcspike", "pcarrow")]
        graphs, plain = [], []
        for i, (src, tgt) in enumerate(pairs):
            p = plot_for(tgt)
            graphs.append((f"g{i}", [dict(p, recast_from=src)]))
            plain.append((f"g{i}", [plot_for(tgt)]))
        # The rline -> line form: its first bound.
        graphs.append(("gr", [{"type": "line", "recast_from": "rline",
                               "yvar": "mpg", "xvar": "weight",
                               "options": {}}]))
        plain.append(("gr", [plot_for("line")]))
        got = []
        for gs in (graphs, plain):
            spec = tp._spec(graphs=gs)
            figs = (jo._saved_figs(jo._saved(spec, tp._DF)) if mode == "saved"
                    else jo._served_figs(jo._served(spec, tp._DF)))
            got.append([(_glyphs(f), sorted(_points(f))) for f in figs])
        assert got[0] == got[1]


class TestRecastAfterAMove:

    def test_lfit_scatter_is_marked_saved(self):
        """A recast fit keeps the saved page's stale cue, as an un-recast
        lfit does: its renderers carry the frozen tag."""
        spec = tp._spec(plots=[plot_for("lfit", {"recast": "scatter"})])
        r = jo._saved(spec, tp._DF)
        tagged = [rr for groups in r.frozen_layer_registry.values()
                  for _, rs in groups for rr in rs]
        assert any(type(rr.glyph).__name__ == "Scatter" for rr in tagged)

    def test_kdensity_area_served(self):
        """After a dropdown move the served app redraws the recast density
        over the kept rows, as the un-recast density."""
        move = tp._MOVES[0]
        _, filt, action, _ = move
        out = []
        for opts in ({"recast": "area"}, {}):
            spec = tp._spec(plots=[plot_for("kdensity", opts)],
                            build_options={"filter": filt})
            doc, _ = jo._served_move(spec, tp._DF, action)
            fig = jo._served_figs(doc)[0]
            out.append((_glyphs(fig), _points(fig)))
        assert out[0][0] == ["VArea"] and out[0][1]
        assert out[0][1] == out[1][1]


class TestTheFixture:

    def test_meta_and_classes(self):
        d = _truth()
        m = d["_meta"]
        assert all(k in m for k in ("stata_version", "born_date",
                                    "dash_commit", "extracted"))
        assert set(m["classes"]["yxtype"]) == set(dr.GlyphMapper._RECAST_DRAWN)
        assert set(m["classes"]["functiontype"]) == set(
            dr.GlyphMapper._RECAST_DRAWN) | {"function"}
        assert set(m["classes"]["yxyxtype"]) == {
            "pcarrow", "pcbarrow", "pccapsym", "pcscatter", "pcspike"}
        # Every within-class probe draws its target's base.
        p = d["probes"]
        assert p["W-sc-line"]["equal_to"] == "B-line"
        assert p["FB-line"]["equal_to"] == "B-scatter"
        assert p["D-lfit-scatter"]["counts"]["circle"] == 6


class TestTheHelp:

    def test_recast_is_documented_and_named_only_where_not_drawn(self):
        with open(_HELP, encoding="utf-8") as fh:
            text = fh.read()
        assert "{phang}{ul:Recast.}  {opt recast(plottype)}" in text
        flat = re.sub(r"\s+", " ", text)
        assert "{cmd:recast()} on {cmd:pci} and {cmd:pcarrowi}" in flat
        assert "name the plot type you want directly" not in flat
