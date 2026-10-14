"""
test_brushed_copies.py -- a layer's brushed-away (nonselection) and muted
copies draw its glyph's own look (WP-30 P1.12a, ratification row 27).

The defect (Evidence E10, measured at c96facd in both modes): Bokeh builds
a renderer's ``nonselection_glyph`` and ``muted_glyph`` once, from the
creation keywords, and dash's appliers then restyle ``renderer.glyph``
alone.  So ``scatter, msize(large) mcolor(red)`` drew its unselected points
at the scheme's default size and colour (size 15/8.0/8.0, fill #ff0000 /
#1a476f / #1a476f), a hollow ``msymbol(Oh)`` brushed away filled (fill
alpha 0.0/0.1/0.2) and ``malpha(5)`` twice as opaque as drawn
(0.05/0.1/0.2); lwidth(), lcolor(), fcolor() and colorvar() never reached
the copies either.

The rule (BR-08.9): after every applier of a layer, each copy carries the
glyph's own value of every property, except its alphas, each the smaller of
the glyph's and the copy's own dimming alpha (0.15 on a linked figure,
Bokeh's 0.1 otherwise, 0.2 muted).  Expectations are relations to the drawn
glyph, never pixel literals.
"""
import dataclasses
import os
import sys
import types
import warnings

import numpy as np
import pytest
from bokeh.model import Model
from bokeh.models import Circle, GlyphRenderer
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402
from test_size_units import _build, _figure, _sc  # noqa: E402

_MODES = ("saved", "served")
_SKIP = {"decorations", "defs"}


def _walk(glyph):
    """The property names TR-08.16's sync walks."""
    return sorted(set(type(glyph).properties())
                  - set(Model.properties()) - _SKIP)


def _norm(v):
    """A comparable form: a model by identity, a spec field by field."""
    if isinstance(v, Model):
        return ("model", v.id)
    if isinstance(v, dict):
        return {k: _norm(x) for k, x in v.items()}
    if isinstance(v, np.ndarray):
        return tuple(_norm(x) for x in v.tolist())
    if isinstance(v, (list, tuple)):
        return tuple(_norm(x) for x in v)
    if dataclasses.is_dataclass(v) and not isinstance(v, type):
        return (type(v).__name__,
                {f.name: _norm(getattr(v, f.name))
                 for f in dataclasses.fields(v)})
    return v


def _differences(a, b):
    """The non-alpha properties on which copy *b* differs from glyph *a*."""
    out = {}
    for name in _walk(a):
        if name.endswith("_alpha"):
            continue
        va, vb = _norm(getattr(a, name)), _norm(getattr(b, name))
        if va != vb:
            out[name] = (va, vb)
    return out


def _assert_same(glyph, copy, what=""):
    assert type(copy) is type(glyph), (what, type(glyph), type(copy))
    diff = _differences(glyph, copy)
    assert diff == {}, "%s: the copy differs from the glyph: %r" % (what,
                                                                    diff)


def _renderers(fig):
    return [r for r in fig.renderers if isinstance(r, GlyphRenderer)]


def _copies(r):
    return [(n, getattr(r, n)) for n in ("nonselection_glyph",
                                         "muted_glyph")
            if getattr(r, n, None) is not None
            and getattr(r, n) != "auto"]


def _assert_copies_same(fig, what):
    rends = _renderers(fig)
    assert rends, what
    seen = 0
    for r in rends:
        for n, c in _copies(r):
            _assert_same(r.glyph, c, "%s %s %s" % (what,
                                                   type(r.glyph).__name__,
                                                   n))
            seen += 1
    assert seen, what


def _alphas(g):
    return {a: getattr(g, a) for a in ("fill_alpha", "line_alpha",
                                       "hatch_alpha")
            if a in g.properties()
            and isinstance(getattr(g, a), (int, float))
            and not isinstance(getattr(g, a), bool)}


def _assert_no_brighter(fig, what):
    for r in _renderers(fig):
        ga = _alphas(r.glyph)
        for n, c in _copies(r):
            for a, v in _alphas(c).items():
                if a in ga:
                    assert v <= ga[a] + 1e-12, (what, n, a, v, ga[a])


def _pair(mode, tmp_path, plots2):
    """A linked pair (test_help_claims_4's helpers); g2 draws *plots2*."""
    from test_help_claims_4 import (_pair_spec, _saved, _served_app,
                                    _served_session)
    from test_adversarial_matrix import _DF
    spec = _pair_spec(link="g1 g2", plots2=plots2)
    if mode == "saved":
        r = _saved(tmp_path, spec, _DF)
        figs = list(r.figures.values())
    else:
        doc = _served_session(_served_app(tmp_path, spec, _DF))
        figs = list(doc.select({"type": figure}))
    [g2] = [f for f in figs
            if any("price" in str(getattr(r.glyph, "y", ""))
                   for r in _renderers(f))]
    return g2


class TestBrushedCopiesFollowTheGlyph:

    # -- the two helpers, on hand-built renderers --------------------------

    def test_the_sync_helper(self):
        fig = figure()
        r = fig.scatter(x=[1, 2], y=[1, 2], size=8)
        r.glyph.size = 15
        r.glyph.fill_color = "red"
        r.glyph.line_color = "red"
        r.glyph.marker = "triangle"
        r.glyph.fill_alpha = 0.8
        r.glyph.name = "g"
        r.glyph.tags = ["t"]
        names = {n: (c.name, list(c.tags)) for n, c in _copies(r)}
        # A renderer listed in `before' is left alone.
        r2 = fig.scatter(x=[1, 2], y=[1, 2], size=8)
        r2.glyph.size = 20
        r2_before = {n: (c.size, c.fill_color) for n, c in _copies(r2)}
        # A None copy and a copy of another class are left alone.
        r3 = fig.scatter(x=[1, 2], y=[1, 2], size=8)
        r3.glyph.size = 30
        r3.nonselection_glyph = None
        other = Circle(x="x", y="y", radius=1)
        r3.muted_glyph = other

        assert dr.GlyphMapper._sync_brushed_copies(
            fig, frozenset({id(r2)})) is None

        _assert_same(r.glyph, r.nonselection_glyph, "nonselection")
        _assert_same(r.glyph, r.muted_glyph, "muted")
        assert r.nonselection_glyph.size == 15
        assert r.nonselection_glyph.fill_alpha == pytest.approx(min(0.1, 0.8))
        assert r.muted_glyph.fill_alpha == pytest.approx(min(0.2, 0.8))
        assert {n: (c.name, list(c.tags)) for n, c in _copies(r)} == names
        assert {n: (c.size, c.fill_color)
                for n, c in _copies(r2)} == r2_before
        assert r3.nonselection_glyph is None
        assert r3.muted_glyph is other and other.radius == 1

    def test_the_dim_helper_keeps_a_copy_no_brighter_than_its_glyph(self):
        fig = figure()
        faint = fig.scatter(x=[1, 2], y=[1, 2], fill_alpha=0.0,
                            line_alpha=0.05)
        opaque = fig.scatter(x=[1, 2], y=[1, 2])
        dr._dash_dim_nonselection(fig)
        assert faint.nonselection_glyph.fill_alpha == pytest.approx(0.0)
        assert faint.nonselection_glyph.line_alpha == pytest.approx(0.05)
        assert opaque.nonselection_glyph.fill_alpha == pytest.approx(
            dr._NONSELECTION_ALPHA)
        # A renderer with no glyph (test_served_bs_layout's stand-ins) is
        # dimmed to the alpha, as today.
        ns = types.SimpleNamespace(fill_alpha=0.1, line_alpha=0.1)
        stand_in = types.SimpleNamespace(
            renderers=[types.SimpleNamespace(nonselection_glyph=ns)])
        dr._dash_dim_nonselection(stand_in)
        assert (ns.fill_alpha, ns.line_alpha) == (dr._NONSELECTION_ALPHA,) * 2

    # -- both modes, end to end --------------------------------------------

    @pytest.mark.parametrize("mode", _MODES)
    def test_marker_options_reach_the_copies(self, mode, tmp_path):
        fig = _figure(mode, tmp_path, [_sc(msize="large", mcolor="red")])
        _assert_copies_same(fig, "scatter msize(large) mcolor(red)")
        fig = _figure(mode, tmp_path, [{
            "type": "connected", "yvar": "mpg", "xvar": "weight",
            "options": {"mcolor": "red", "lcolor": "blue",
                        "msize": "large"}}])
        assert len(_renderers(fig)) >= 2
        _assert_copies_same(fig, "connected")
        fig = _figure(mode, tmp_path, [{
            "type": "scatteri", "values": [[20.0, 3000.0], [30.0, 4000.0]],
            "options": {"msymbol": "D"}}])
        _assert_copies_same(fig, "scatteri msymbol(D)")

    @pytest.mark.parametrize("mode", _MODES)
    def test_line_and_outline_options_reach_the_copies(self, mode,
                                                       tmp_path):
        cases = [
            ("line", {"type": "line", "yvar": "mpg", "xvar": "weight",
                      "options": {"lwidth": "thick", "lcolor": "red",
                                  "lpattern": "dash"}}),
            ("scatter T", _sc(msymbol="T", mlwidth="thick",
                              mlcolor="blue")),
            ("rcap", {"type": "rcap", "yvar1": "mpg", "yvar2": "mpg2",
                      "xvar": "weight", "options": {"lcolor": "red"}}),
        ]
        for what, plot in cases:
            fig = _figure(mode, tmp_path, [plot])
            seen = 0
            for r in _renderers(fig):
                for n, c in _copies(r):
                    for p in ("line_color", "line_width", "line_dash"):
                        if p in r.glyph.properties():
                            assert _norm(getattr(c, p)) == _norm(
                                getattr(r.glyph, p)), (what, n, p)
                            seen += 1
            assert seen, what

    @pytest.mark.parametrize("mode", _MODES)
    def test_fill_and_colorvar_reach_the_copies(self, mode, tmp_path):
        cases = [
            ("bar", {"type": "bar", "yvar": "mpg", "xvar": "weight",
                     "options": {"fcolor": "red"}}),
            ("area", {"type": "area", "yvar": "mpg", "xvar": "weight",
                      "options": {"fcolor": "yellow"}}),
            ("colorvar", _sc(colorvar="price")),
        ]
        for what, plot in cases:
            fig = _figure(mode, tmp_path, [plot])
            seen = 0
            for r in _renderers(fig):
                if "fill_color" not in r.glyph.properties():
                    continue
                for n, c in _copies(r):
                    assert _norm(c.fill_color) == _norm(r.glyph.fill_color), (
                        what, n, c.fill_color, r.glyph.fill_color)
                    seen += 1
            assert seen, what

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_copy_is_never_more_opaque_than_the_glyph(self, mode,
                                                         tmp_path):
        fig = _figure(mode, tmp_path, [_sc(msymbol="Oh")])
        for r in _renderers(fig):
            for n, c in _copies(r):
                assert c.fill_alpha == pytest.approx(0.0), ("Oh", n)
        _assert_no_brighter(fig, "Oh")
        fig = _figure(mode, tmp_path, [_sc(malpha="5")])
        for r in _renderers(fig):
            for n, c in _copies(r):
                assert c.fill_alpha <= 0.05 + 1e-12, ("malpha(5)", n)
        _assert_no_brighter(fig, "malpha(5)")
        fig = _figure(mode, tmp_path, [_sc(msymbol="i")])
        for r in _renderers(fig):
            for g in [r.glyph] + [c for _, c in _copies(r)]:
                assert (g.fill_alpha, g.line_alpha) == (0.0, 0.0), "i"
        # On a linked pair, after _dash_dim_nonselection.
        g2 = _pair(mode, tmp_path, [{"type": "scatter", "yvar": "price",
                                     "xvar": "weight",
                                     "options": {"msymbol": "Oh"}}])
        for r in _renderers(g2):
            assert r.nonselection_glyph.fill_alpha == pytest.approx(0.0)
        _assert_no_brighter(g2, "linked Oh")

    @pytest.mark.parametrize("mode", _MODES)
    def test_paired_and_by_panel_layers(self, mode, tmp_path):
        fig = _figure(mode, tmp_path, [{
            "type": "pcscatter", "y1var": "mpg", "x1var": "weight",
            "y2var": "mpg2", "x2var": "weight2",
            "options": {"mcolor": "red", "msize": "large"}}])
        _assert_copies_same(fig, "pcscatter")
        figs, _, _ = _build(mode, tmp_path, [_sc(mcolor="red")],
                            go={"by": "foreign"})
        assert len(figs) >= 2
        for f in figs:
            _assert_copies_same(f, "by() panel")

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_copies_hold_after_a_move(self, mode, tmp_path):
        plots = [{"type": "connected", "yvar": "mpg", "xvar": "weight",
                  "options": {"msize": "large", "mcolor": "red",
                              "lwidth": "thick"}}]
        figs, _, doc = _build(mode, tmp_path, plots,
                              bo={"filter": "weight, type(range)"})
        [fig] = figs
        if mode == "served":
            from test_served_linked_views import _fire
            _fire(doc, "weight", (2000.0, 3500.0))
        _assert_copies_same(fig, "after a move")

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_bars_copies_keep_its_width_after_a_move(self, mode, tmp_path):
        """After a filter move a bar's nonselection and muted copies are as
        wide as the bar (WP-30 P1.17a, A61): the width no longer follows
        the kept rows, so no copy is left at the build's width.  The move
        to Foreign changes the kept rows' smallest weight gap (70 to 210),
        which moved the drawn width and left the copies behind."""
        import test_mode_parity as tp
        plots = [{"type": "bar", "yvar": "mpg", "xvar": "weight",
                  "options": {}}]
        spec = tp._spec(plots, {"filter": "foreign, type(dropdown)"})
        if mode == "saved":
            import test_saved_filter_layers as tsfl
            r = tsfl._render(spec)
            tsfl._move(r, ("Select", "Foreign"))
            figs = list(r.figures.values())
        else:
            from bokeh.models import Select
            doc, _ = tp._served(spec)
            [w] = [m for m in tp._walk_models(doc) if isinstance(m, Select)]
            [raw] = [v for v, lab in w.options if lab == "Foreign"]
            tp._fire(w, raw)
            figs = [m for m in tp._walk_models(doc)
                    if type(m).__name__ == "figure"]
        bars = [rr for f in figs for rr in _renderers(f)
                if type(rr.glyph).__name__ == "VBar"]
        assert bars
        for rr in bars:
            for n, c in _copies(rr):
                assert c.width == rr.glyph.width, (n, c.width, rr.glyph.width)

    # -- guards (pass before and after) -------------------------------------

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_dimming_alphas_are_kept(self, mode, tmp_path):
        fig = _figure(mode, tmp_path, [_sc()])
        for r in _renderers(fig):
            assert r.nonselection_glyph.fill_alpha == pytest.approx(0.1)
            assert r.muted_glyph.fill_alpha == pytest.approx(0.2)
        g2 = _pair(mode, tmp_path, None)
        for r in _renderers(g2):
            assert r.nonselection_glyph.fill_alpha == pytest.approx(
                dr._NONSELECTION_ALPHA)
            assert r.nonselection_glyph.fill_alpha == pytest.approx(0.15)
            assert r.muted_glyph.fill_alpha == pytest.approx(0.2)

    def test_the_stale_cue_still_rebuilds_the_muted_glyph(self):
        from test_saved_stale_cue import _layer_rends
        from test_mode_parity import _spec
        from test_saved_filter_layers import _render
        from test_server_layer_defects import plot_for
        # fpfit: a fit the saved page still marks (lfit is refitted,
        # WP-31 F1a).
        r = _render(_spec([plot_for("scatter"),
                           plot_for("fpfit", {"lcolor": "green",
                                              "lpattern": "dash"})],
                          {"filter": "foreign, type(dropdown)"}))
        [x] = _layer_rends(r)
        want = dr._dash_stale_glyph(x.glyph)
        assert type(x.muted_glyph) is type(x.glyph)
        assert x.muted_glyph.line_color == x.glyph.line_color == \
            want.line_color
        assert list(x.muted_glyph.line_dash) == list(x.glyph.line_dash)
        assert x.muted_glyph.line_alpha == pytest.approx(
            x.glyph.line_alpha * 0.3)
        assert x.muted_glyph.line_alpha == pytest.approx(want.line_alpha)
