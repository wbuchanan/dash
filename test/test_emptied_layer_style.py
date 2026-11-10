"""An emptied layer keeps its style and key, as twoway keys it (WP-29 P0.18).

A layer left with no drawable rows -- by its own if, a by() panel or a
filter move -- was drawn as a bare Bokeh glyph, ``#1f77b4`` at width 1,
where twoway keys it in its own p# style (``stroke:#90353B;
stroke-width:8.64`` for the second plot under s2color; E-18.4).  The fits
and smooths at 0-2 rows and the histogram at 0 were bare in both modes; the
served build of bar, rbar, rarea and rspike at 0 rows too.

The oracle is ``test/fixtures/emptied_layer_truth.json``, written by
``scripts/extract_emptied_layer_truth.do`` from live twoway SVG exports
under s2color and s1mono: the (stroke, stroke-width) pairs of each probe's
key minus those of the base graph.
"""
import json
import os
import sys
import warnings

import pytest
from bokeh.document import Document
from bokeh.models import ColumnDataSource, Legend
from bokeh.plotting import figure as bk_figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from test_mode_parity import _served, _spec, _standalone  # noqa: E402
from test_mode_parity import _EMPTIED_LAYERS  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "emptied_layer_truth.json")
_QUAL = {0: "price > 20000", 1: "price >= 11385", 2: "price >= 10000"}
_PROPS = ("line_color", "fill_color", "line_width", "line_dash",
          "line_alpha", "fill_alpha")


def _truth():
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _style(r):
    g = r.glyph
    out = [type(g).__name__]
    for p in _PROPS:
        if p in g.properties():
            v = getattr(g, p)
            out.append((p, list(v) if isinstance(v, (list, tuple))
                        else (v if isinstance(v, (str, int, float))
                              or v is None else str(v))))
    return tuple(out)


def _legend_labels(fig, rends):
    ids = {id(x) for x in rends}
    out = []
    for side in (fig.center, fig.above, fig.below, fig.left, fig.right):
        for m in side:
            if isinstance(m, Legend):
                out += [getattr(i.label, "value", None) for i in m.items
                        if any(id(x) in ids for x in i.renderers)]
    return out


def _saved_layer(t, if_expr="", bo=None):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r, _ = _standalone(_spec([plot_for("scatter"),
                                  plot_for(t, if_expr=if_expr)], bo))
    fig = r.figures["g1"]
    rends = [x for x in fig.renderers[1:] if not dr._dash_is_swatch(x)]
    return [_style(x) for x in rends], _legend_labels(fig, rends), rends


def _served_layer(t, if_expr="", bo=None):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        doc, _ = _served(_spec([plot_for("scatter"),
                                plot_for(t, if_expr=if_expr)], bo))
    [fig] = [m for m in doc.models if type(m).__name__ == "figure"]
    rends = [x for x in fig.renderers[1:] if not dr._dash_is_swatch(x)]
    return [_style(x) for x in rends], _legend_labels(fig, rends), rends


def _emptied_keys(t, n, keys):
    """The keys twoway gives the layer emptied to *n* rows: an lfit or
    qfit with none is keyed by its y's name.  Flipped (WP-47 DG-7): the
    unfiltered layer's "Fitted values" at 0 rows was wrong because twoway
    leaves the fit's variable unlabelled (varlabel_mlabel_truth.json
    empty.lfit, empty.lfit_beside key "mpg")."""
    if n == 0 and t in ("lfit", "qfit", "lfitci", "qfitci"):
        return ["mpg" if k == "Fitted values" else k for k in keys]
    return keys


class TestAnEmptiedLayerKeepsItsStyle:

    @pytest.mark.parametrize("n", [0, 1, 2])
    @pytest.mark.parametrize("t", _EMPTIED_LAYERS)
    def test_saved(self, t, n):
        want = _saved_layer(t)
        got = _saved_layer(t, _QUAL[n])
        assert got[0] == want[0], (t, n)
        assert got[1] == _emptied_keys(t, n, want[1]), (t, n)

    @pytest.mark.parametrize("n", [0, 1, 2])
    @pytest.mark.parametrize("t", _EMPTIED_LAYERS)
    def test_served(self, t, n):
        want = _served_layer(t)
        got = _served_layer(t, _QUAL[n])
        assert got[0] == want[0], (t, n)
        assert got[1] == _emptied_keys(t, n, want[1]), (t, n)


def _key_cases():
    d = _truth()
    out = []
    for sch, s in d["schemes"].items():
        for t, e in s["probes"].items():
            # A Quad's key is its outline (WP-30 P1.4a: the histogram was
            # skipped while its key colour was left to P1.4).
            if e["rows0"]["rc"] != 0:
                continue
            out.append(pytest.param(sch, t, id=f"{sch}-{t}"))
    return out


class TestTheKeyIsTwoways:

    @pytest.mark.parametrize("scheme,t", _key_cases())
    def test_the_empty_layer_draws_in_twoways_key_colour(self, scheme, t):
        key = _truth()["schemes"][scheme]["probes"][t]["rows0"]["key_styles"]
        colours = {c for c, _w in key}
        _, _, rends = _saved_layer(t, _QUAL[0], {"scheme": scheme})
        g = rends[0].glyph
        # A band's and a bar's key is its fill (rbar draws no outline:
        # line_alpha 0); a line's is its stroke.
        c = (g.fill_color if type(g).__name__ in ("VArea", "VBar")
             else g.line_color)
        if type(g).__name__ in ("VArea", "VBar"):
            # The fixture records the key's stroke, the unblended colour;
            # the fill is that colour at the layer's (p2's) bar or area
            # intensity (WP-30 P1.2b; twoway's SVG, plan section 16
            # Evidence E3).
            sp = dr.SchemeParser(scheme)
            f = (sp.p_area_intensity if t == "rarea"
                 else sp.p_bar_intensity)[1]
            colours = {dr.GlyphMapper._blend_intensity(x, f,
                                                       sp.naturally_white)
                       for x in colours}
        assert str(c).lower() in colours, (scheme, t, c, colours)


class TestTheFixture:

    def test_meta_is_stamped_and_the_selfchecks_held(self):
        m = _truth()["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted"):
            assert m.get(k), k
        assert m["empty_matches_populated"] == "held"
        assert m["base_has_no_layer_colour"] == "held"


def _gm(scheme="s2color"):
    return dr.GlyphMapper(dr.OptionTranslator(), dr.SchemeParser(scheme))


def _line_style(r):
    g = r.glyph
    return (g.line_color, g.line_width, list(g.line_dash), g.line_alpha)


class TestTheEmptyFitLine:

    def test_it_draws_the_populated_style(self):
        gm = _gm()
        fig = bk_figure()
        r = gm._empty_fit_line(fig, "x", "y", {}, 1, "mpg")
        assert len(r.data_source.data["x"]) == 0
        src = ColumnDataSource({"mpg": [1.0, 2.0, 3.0],
                                "weight": [1.0, 2.0, 4.0]})
        pop = gm.map_lfit(bk_figure(), src, "mpg", "weight", {},
                          color_idx=1)
        assert _line_style(r) == _line_style(pop)
        assert r.glyph.line_color != "#1f77b4"

    def test_it_takes_the_width_family_it_is_given(self):
        gm = _gm()
        a = gm._empty_fit_line(bk_figure(), "x", "y", {}, 1, "mpg")
        b = gm._empty_fit_line(bk_figure(), "x", "y", {}, 1, "mpg",
                               width_kind="")
        assert a.glyph.line_width == gm.scheme.plot_line_width(1, "lineplot")
        assert b.glyph.line_width == gm.scheme.plot_line_width(1, "")

    def test_mspline_and_mband_keep_their_own_width_family_when_empty(
            self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "w29lw.scheme").write_text(
            "#include s2color\nlinewidth plineplot vvthick\n")
        sp = dr.SchemeParser("w29lw")
        assert sp.plot_line_width(1, "lineplot") != sp.plot_line_width(1, "")
        gm = dr.GlyphMapper(dr.OptionTranslator(), sp)
        full = ColumnDataSource({"mpg": [1.0, 3.0, 2.0, 5.0, 4.0, 6.0],
                                 "weight": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]})
        empty = ColumnDataSource({"mpg": [], "weight": []})
        lfit = gm.map_lfit(bk_figure(), full, "mpg", "weight", {},
                           color_idx=1)
        for m in ("map_mspline", "map_mband"):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                pop = getattr(gm, m)(bk_figure(), full, "mpg", "weight", {},
                                     color_idx=1)
                emp = getattr(gm, m)(bk_figure(), empty, "mpg", "weight", {},
                                     color_idx=1)
            pop = pop[0] if isinstance(pop, list) else pop
            emp = emp[0] if isinstance(emp, list) else emp
            assert emp.glyph.line_width == pop.glyph.line_width, m
            assert emp.glyph.line_width != lfit.glyph.line_width, m


class TestTheHistogramQuads:

    def test_the_empty_and_populated_quads_share_a_style(self):
        gm = _gm()
        pop = gm.map_histogram(bk_figure(), ColumnDataSource(
            {"mpg": [1.0, 2.0, 2.0, 3.0]}), "mpg", {}, color_idx=1)
        emp = gm.map_histogram(bk_figure(), ColumnDataSource({"mpg": []}),
                               "mpg", {}, color_idx=1)
        pop = pop[0] if isinstance(pop, list) else pop
        emp = emp[0] if isinstance(emp, list) else emp
        assert _style(emp) == _style(pop)
        r = gm._histogram_quads(bk_figure(), ColumnDataSource(
            {"top": [], "left": [], "right": []}), {}, 1, "mpg")
        assert _style(r) == _style(pop)


def _rbar_width(gm, xs):
    src = ColumnDataSource({"x": list(xs), "y1": [1.0] * len(xs),
                            "y2": [2.0] * len(xs)})
    r = gm.map_rbar(bk_figure(), src, "y1", "y2", "x", {})
    r = r[0] if isinstance(r, list) else r
    return r


class TestTheBarWidthFallback:

    def test_one_rule_for_none_one_and_the_tag(self):
        """One rule with no rows and with one: one x unit, and no tag.

        Flipped (WP-30 P1.17a): 0.8 and 0.64 with a spacing tag were wrong
        because twoway draws a bar one x unit wide and caps as long as a marker of its msize (P1.17a).
        """
        gm = _gm()
        for xs in ([], [3.0]):
            src = ColumnDataSource({"x": list(xs), "y": [1.0] * len(xs)})
            r = gm.map_bar(bk_figure(), src, "y", "x", {})
            r = r[0] if isinstance(r, list) else r
            assert float(getattr(r.glyph.width, "value", r.glyph.width)) \
                == pytest.approx(1.0), xs
            assert not hasattr(r.data_source, "_dash_spacing")
            rr = _rbar_width(gm, xs)
            assert float(getattr(rr.glyph.width, "value", rr.glyph.width)) \
                == pytest.approx(1.0), xs
            assert not hasattr(rr.data_source, "_dash_spacing")
