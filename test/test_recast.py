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
from conftest import drawn_renderers  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "recast_truth.json")
_HELP = os.path.join(os.path.dirname(_HERE), "dash.sthlp")


def _truth():
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _glyphs(fig):
    return [type(g.glyph).__name__ for g in drawn_renderers(fig)]


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
    # Flipped (WP-34 PIC-1): an area draws its outline ring and its key
    # swatch after the fill (A-6).
    ("lowess", "area", ["VArea", "Line", "Quad"]),
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
    columns, a histogram's quad midpoints and tops.  Flipped (WP-34
    PIC-1): not an area's outline ring, its whole polygon rebuilt from the
    fill's source (A-6), nor its key swatch."""
    out = set()
    for g in drawn_renderers(fig):
        if "dash_area_outline" in (g.tags or []) \
                or getattr(g, "_dash_key_glyph", False):
            continue
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
        bars = [g.glyph for g in drawn_renderers(fig)
                if type(g.glyph).__name__ == "VBar"]
        assert bars and all(float(b.width) == 1.0 for b in bars)


class TestRecastKeepsTheSeriesLabel:

    def test_key(self):
        """A derived layer keeps its type, so its key is the un-recast
        layer's; a base layer's is the variables' as before."""
        assert (dr._dash_legend_key(plot_for("lfit", {"recast": "scatter"}))
                == dr._dash_legend_key(plot_for("lfit")))
        # Flipped (WP-46 RH-3): the rline -> line layer keyed "mpg" by its
        # first bound was a dash-internal pin with no twoway truth: twoway
        # keys it by both bounds (recast_truth.json RB-02 "y/y2"), and
        # dash.ado now writes the second as options.recast_hi.
        p = {"type": "line", "recast_from": "rline", "yvar": "mpg",
             "xvar": "weight", "options": {"recast_hi": "price"}}
        assert dr._dash_legend_key(p) == "mpg/price"


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
        # The rline -> line form: its first bound.  Flipped (WP-46 RH-3):
        # "equals a plain line" was wrong because twoway keeps the second
        # bound on the axis (recast_truth.json RB-01); it equals a plain
        # line plus one invisible dash_bound_extent renderer at the second
        # bound, compared without it.
        graphs.append(("gr", [{"type": "line", "recast_from": "rline",
                               "yvar": "mpg", "xvar": "weight",
                               "options": {"recast_hi": "price"}}]))
        plain.append(("gr", [plot_for("line")]))
        got, ext = [], []
        for gs in (graphs, plain):
            spec = tp._spec(graphs=gs)
            figs = (jo._saved_figs(jo._saved(spec, tp._DF)) if mode == "saved"
                    else jo._served_figs(jo._served(spec, tp._DF)))
            ext.append([len([r for r in f.renderers if "dash_bound_extent"
                             in (r.tags or [])]) for f in figs])
            got.append([(_glyphs([r for r in drawn_renderers(f)
                                  if "dash_bound_extent" not in
                                  (r.tags or [])]),
                         sorted(_points([r for r in drawn_renderers(f)
                                         if "dash_bound_extent" not in
                                         (r.tags or [])])))
                        for f in figs])
        assert got[0] == got[1]
        assert ext == [[0] * len(pairs) + [1], [0] * (len(pairs) + 1)]


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
        # Flipped (WP-34 PIC-1): the fill, its outline ring and its key
        # swatch (A-6).
        assert out[0][0] == ["VArea", "Line", "Quad"] and out[0][1]
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

    def test_the_option_surface_record_holds_the_written_spec(self):
        """WP-30 P1.8b: rejected_options.json's recast probe records the
        spec dash.ado writes, the drawn type with ``recast_from``, not the
        pre-WP-30 scatter carrying ``options.recast``."""
        with open(os.path.join(_HERE, "fixtures", "rejected_options.json"),
                  encoding="utf-8") as fh:
            probes = {p["id"]: p for p in json.load(fh)["probes"]}
        plot = json.loads(probes["recast"]["spec_json"])["plots"][0]
        assert (plot["type"], plot.get("recast_from")) == ("line", "scatter")
        assert "recast" not in plot["options"]


class TestTheHelp:

    def test_recast_is_documented_and_named_only_where_not_drawn(self):
        with open(_HELP, encoding="utf-8") as fh:
            text = fh.read()
        assert "{phang}{ul:Recast.}  {opt recast(plottype)}" in text
        flat = re.sub(r"\s+", " ", text)
        # Flipped (WP-31 C7): "recast() on pci and pcarrowi" in the Not
        # drawn entry was wrong because twoway draws them as the pc type
        # named (area_cmissing_truth.json P01, P02) and dash now does; the
        # Recast paragraph says so, with histogram's range types.
        assert "{cmd:recast()} on {cmd:pci} and {cmd:pcarrowi}" not in flat
        assert "{cmd:pci} and {cmd:pcarrowi} take the {cmd:pc} types" in flat
        assert "{cmd:histogram} also takes the range types" in flat
        assert "name the plot type you want directly" not in flat


# ===========================================================================
# WP-46 RH-11: the yx names on a y2xtype source, read in full
# ===========================================================================

_ADO = os.path.join(os.path.dirname(_HERE), "dash.ado")


def _y2x_spellings():
    """``name:minimum`` pairs dash.ado's _dash_recast_opt reads for the
    y2xtype class (range sources and histogram), its locals expanded."""
    with open(_ADO, encoding="utf-8") as fh:
        ado = fh.read()
    body = ado[ado.index("program define _dash_recast_opt"):]
    body = body[:body.index("\nend\n")]
    loc = dict(re.findall(r'local (_sp_\w+) "([^"]*)"', body))
    m = re.search(r'"`_rc_class\'" == "y2xtype" local _sp "([^"]*)"', body)
    assert m, "no y2xtype spellings"
    return re.sub(r"`(_sp_\w+)'", lambda g: loc[g.group(1)],
                  m.group(1)).split()


def _y2x_name(word):
    """The name dash.ado's match loop gives *word* in class y2xtype, or
    "" (twoway's two notes and rspike)."""
    for e in _y2x_spellings():
        n, mn = e.split(":")
        if len(word) >= int(mn) and n[:len(word)] == word:
            return n
    return ""


class TestY2xSpellings:

    def test_a_repeated_yx_name_is_one_unknown_name(self):
        """twoway reads recast(line line) on a range source or histogram
        as one unknown y2xtype name, the whole value in its note, and
        draws rspike; recast(rline rline) is rline, with no note (fixture
        RH11-06..08; dash's side: test_twoway_option_parity.cscript
        Q4601-37..39)."""
        probes = _truth()["probes"]
        for pid in ("RH11-06", "RH11-08"):
            rec = probes[pid]
            assert rec["rc"] == 0
            assert rec["lines"][0].startswith(
                "(note:  named style line line not found in class y2xtype")
            assert rec["lines"][1] == ("(note:  y2xtype not found in "
                                       "scheme, default attributes used)")
        assert probes["RH11-06"]["equal_to"] == "B-rspike"
        assert probes["RH11-07"]["rc"] == 0
        assert probes["RH11-07"]["lines"] == []

    @pytest.mark.parametrize("mode", ["saved", "served"])
    @pytest.mark.parametrize("pid", ["RH11-01", "RH11-02", "RH11-03",
                                     "RH11-04", "RH11-05"])
    def test_abbreviations_fall_back(self, mode, pid):
        """sc, li, co and b on a range source or histogram print twoway's
        two notes and draw rspike (fixture RH11-*: the notes, and the
        picture B-rspike draws); the full names and the range names still
        match."""
        rec = _truth()["probes"][pid]
        word = re.search(r"recast\((\w+)\)", rec["cmd"]).group(1)
        assert rec["rc"] == 0
        assert rec["lines"] == [
            "(note:  named style %s not found in class y2xtype, default "
            "attributes used)" % word,
            "(note:  y2xtype not found in scheme, default attributes used)"]
        if pid in ("RH11-01", "RH11-03", "RH11-04"):
            assert rec["equal_to"] == "B-rspike"
        assert _y2x_name(word) == ""
        for full in ("scatter", "line", "connected", "bar", "rscatter",
                     "rsc", "rbar"):
            assert _y2x_name(full) == ("rscatter" if full == "rsc"
                                       else full)
        # The fallback both modes draw: the range as rspike segments.
        p = dict(plot_for("rspike"), recast_from="rline")
        spec = tp._spec(graphs=[("g0", [p])])
        figs = (jo._saved_figs(jo._saved(spec, tp._DF)) if mode == "saved"
                else jo._served_figs(jo._served(spec, tp._DF)))
        kinds = set(_glyphs(figs[0]))
        assert "Segment" in kinds and not kinds & {"Scatter", "Line"}, kinds


# ===========================================================================
# WP-46 RH-3 (with RH-4): a range source or ciplot() drawn as a yx type
# keeps its second bound on the axis, in its title and in its key
# ===========================================================================

def _rb_plot(target, src):
    """The spec dash.ado writes for ``<src> mpg price weight,
    recast(<target>)``: the drawn type, the typed type as recast_from,
    the first bound as y and the second as options.recast_hi (WP-46
    RH-3)."""
    return {"type": target, "recast_from": src, "yvar": "mpg",
            "xvar": "weight", "options": {"recast_hi": "price"}}


_RB = {"RB-01": ("line", "rline"), "RB-03": ("bar", "rbar"),
       "RB-02": ("scatter", "rcap")}


def _rb_figs(mode, plots, build_options=None):
    spec = tp._spec(plots=plots, build_options=build_options)
    return (jo._saved_figs(jo._saved(spec, tp._DF)) if mode == "saved"
            else jo._served_figs(jo._served(spec, tp._DF)))


def _kept_x(r):
    """The x values renderer *r* draws through its view."""
    d = r.data_source.data
    xs = np.asarray(d[r.glyph.x], dtype=float)
    m = dr.GlyphMapper._view_mask(r.view, len(xs))
    return sorted(xs if m is None else xs[np.asarray(m, dtype=bool)])


@pytest.mark.parametrize("mode", ["saved", "served"])
class TestRangeRecastBounds:

    @pytest.mark.parametrize("pid", ["RB-01", "RB-03"])
    def test_axis_spans_both_bounds(self, mode, pid):
        """twoway's y axis spans both bounds of a range source drawn as
        a yx type (fixture: y2 reaches 11, the axis runs to 11); dash's
        y range covers the second bound too, in both modes."""
        rec = _truth()["probes"][pid]
        assert rec["rc"] == 0 and rec["yrange"][1] >= 11.0
        [f] = _rb_figs(mode, [_rb_plot(*_RB[pid])])
        assert f.y_range.end >= float(tp._DF["price"].max()), (
            f.y_range.start, f.y_range.end)
        assert f.y_range.start <= float(tp._DF["mpg"].min())

    @pytest.mark.parametrize("pid", ["RB-01", "RB-02"])
    def test_key_and_title(self, mode, pid):
        """twoway titles and keys the layer with both bounds, y/y2
        (fixture texts); dash keys and titles it mpg/price."""
        assert "y/y2" in _truth()["probes"][pid]["texts"]
        p = _rb_plot(*_RB[pid])
        assert dr._dash_legend_key(p) == "mpg/price"
        assert dr._dash_axis_default_titles([p])[1] == "mpg/price"
        [f] = _rb_figs(mode, [p, plot_for("scatter")] if pid == "RB-02"
                       else [p])
        if pid == "RB-01":
            assert f.yaxis[0].axis_label == "mpg/price"

    def test_after_a_move(self, mode):
        """After a filter move the bound's extent renderer draws the
        rows the layer draws (it shares the layer's source and view)."""
        spec = tp._spec(plots=[_rb_plot("line", "rline")],
                        build_options={"filter": "foreign, type(dropdown)"})
        act = ("Select", "Domestic")
        if mode == "saved":
            figs = jo._saved_figs(jo._saved_move(spec, tp._DF, act))
        else:
            figs = jo._served_figs(jo._served_move(spec, tp._DF, act)[0])
        [f] = figs
        ext = [r for r in f.renderers
               if "dash_bound_extent" in (r.tags or [])]
        line = [r for r in drawn_renderers(f)
                if type(r.glyph).__name__ == "Line"]
        assert len(ext) == 1 and line
        assert ext[0].glyph.y == "price"
        assert _kept_x(ext[0]) == _kept_x(line[0])
        assert len(_kept_x(ext[0])) == 5

    @pytest.mark.parametrize("pid", ["RB-04", "RB-05", "RB-06"])
    def test_ciplot_yx_spans_both_limits(self, mode, pid):
        """lfitci, ciplot(area|bar|scatter): twoway's y axis spans both
        limits, as the plain lfitci's does (fixture yrange equal to
        RB-08's); dash's y range covers the upper limit too."""
        probes = _truth()["probes"]
        assert probes[pid]["yrange"] == probes["RB-08"]["yrange"]
        tgt = re.search(r"ciplot\((\w+)\)", probes[pid]["cmd"]).group(1)
        [plain] = _rb_figs(mode, [plot_for("lfitci")])
        [f] = _rb_figs(mode, [plot_for("lfitci", {"ciplot": tgt})])
        assert f.y_range.end >= plain.y_range.end - 1e-9, (
            f.y_range.end, plain.y_range.end)


class TestTheBoundExtent:

    def test_drawn_from_the_layer_source(self):
        """_dash_bound_extent: an invisible scatter at x and recast_hi on
        the layer's own source and view, tagged dash_bound_extent; none
        without the option or its column."""
        from bokeh.models import BooleanFilter, CDSView
        src = ColumnDataSource({"x": [1.0, 2.0], "lo": [1.0, 2.0],
                                "hi": [5.0, 6.0]})
        view = CDSView(filter=BooleanFilter([True, False]))
        fig = figure()
        r = dr._dash_bound_extent(fig, src, view, "x", {"recast_hi": "hi"})
        assert r is fig.renderers[-1] and r.tags == ["dash_bound_extent"]
        assert (r.glyph.x, r.glyph.y) == ("x", "hi")
        assert r.data_source is src and r.view is view
        assert float(r.glyph.size) == 0.0
        for o in ({}, {"recast_hi": "nope"}):
            assert dr._dash_bound_extent(figure(), src, None, "x", o) is None


class TestTheBoundHelp:

    def test_the_second_bound_is_documented(self):
        """WP-46 RH-3: the Recast paragraph says a range type drawn as a
        yx type keeps both bounds on the axis, in its title and key."""
        with open(_HELP, encoding="utf-8") as fh:
            flat = re.sub(r"\s+", " ", fh.read())
        assert ("a range type named as a yx type draws its first bound "
                "and keeps both on the axis, in its title and key") in flat
