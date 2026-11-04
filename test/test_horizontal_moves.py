"""horizontal after a filter move, and a turned layer's tooltip (WP-30
P1.9b, section 55).

BUGS.md P1.9b: "the saved page's redraw and the served app's geometry copy
write widths and vertical tooltip fields only, so a turned bar or range
would be redrawn upright after a filter move".  WP-30 P1.17a deleted both
width writers (IR-13: P1.17.3's cancellation of P1.9's step 5 stands), so a
turned bar's height is a build-time constant that no move touches; the
after-move tests here are guards that pin it, in both modes, for all 24
types twoway turns, under by(), on yaxis(2) and on a mixed-orientation
date axis.

What was still wrong at the batch-19 base is the fallback tooltip
(``_dash_build_hover``, shared by both modes and copied into the served
app).  It read the glyph's own property names, so on a layer WP-30 P1.9a
turned it read the other axis's column: a turned kdensity named the
density as its variable, a turned function swapped x and y, a turned pci
listed its ends in the wrong roles, a turned area band (HArea has y, x1,
x2) had no tooltip, and a turned histogram answered by horizontal
position (``vline``) across bins stacked along y.  Each is measured in
both modes, before and after a move.  twoway has no filter: the truth
after a move is the page dash builds from the kept rows, which
test_horizontal.py holds to twoway (test/fixtures/horizontal_truth.json).
"""
import copy
import json
import os
import sys

import pandas as pd
import pytest
from bokeh.models import (ColumnDataSource, CustomJS, GlyphRenderer,
                          HoverTool, Model)
from bokeh.models.glyph import Glyph
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_join_order as jo  # noqa: E402
import test_mode_parity as tp  # noqa: E402
import test_saved_filter_layers as sf  # noqa: E402
from js_runner import requires_node  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

MODES = ("saved", "served")
#: A saved move runs the page's own callback under node.
_MOVE_MODES = (pytest.param("saved", marks=requires_node), "served")
_H = {"horizontal": "horizontal"}
_TURNED = dr._DASH_HORIZONTAL_TYPES
#: The glyph classes the fallback tooltip reads.
_FALLBACK_CLASSES = ("VBar", "HBar", "VArea", "HArea", "Quad", "Segment",
                     "Line", "Scatter")
#: E2's involution: the upright role -> the property a turned glyph draws
#: it with.
_MIRROR = {"x": "y", "y": "x", "x0": "y0", "y0": "x0", "x1": "y1",
           "y1": "x1", "x2": "y2", "y2": "x2", "left": "bottom",
           "bottom": "left", "right": "top", "top": "right",
           "width": "height", "height": "width",
           # WP-32: a marker-wide bar's units turn with it (mwidth).
           "width_units": "height_units", "height_units": "width_units"}


def _opts(t, extra=None):
    o = {"range": "0 2"} if t == "function" else {}
    o.update(extra or {})
    return o


def _figs(spec, mode, df=None):
    df = tp._DF if df is None else df
    if mode == "saved":
        return jo._saved_figs(jo._saved(spec, df))
    return jo._served_figs(jo._served(spec, df))


def _hovers(fig):
    """Each HoverTool's tooltips and mode, with the classes it serves."""
    return [(list(h.tooltips), h.mode,
             sorted(type(r.glyph).__name__ for r in h.renderers)
             if isinstance(h.renderers, list) else str(h.renderers))
            for h in fig.tools if isinstance(h, HoverTool)]


def _rows(fig):
    """The tooltip rows, the mode, with the glyph classes left out."""
    return [(t, m) for t, m, _c in _hovers(fig)]


_PAIRS = {}


def _pairs(mode, types):
    """``{type: (upright fig, turned fig)}``, one build per mode."""
    key = (mode, tuple(types))
    if key not in _PAIRS:
        graphs = []
        for i, t in enumerate(types):
            graphs.append((f"u{i}", [plot_for(t, _opts(t))]))
            graphs.append((f"h{i}", [plot_for(t, _opts(t, _H))]))
        figs = _figs(tp._spec(graphs=graphs), mode)
        _PAIRS[key] = {t: (figs[2 * i], figs[2 * i + 1])
                       for i, t in enumerate(types)}
    return _PAIRS[key]


# ===========================================================================
# The role map
# ===========================================================================

class TestTheRoleMap:

    def test_it_agrees_with_the_transposition(self):
        """Guard: every pair WP-30 P1.9a swaps on a class the fallback reads
        is a pair of E2's involution, and every turned class is mapped."""
        bad = []
        for cls in _FALLBACK_CLASSES:
            assert cls in dr._DASH_TRANSPOSE, cls
            turned, pairs = dr._DASH_TRANSPOSE[cls]
            if turned not in dr._DASH_TRANSPOSE:
                bad.append((cls, turned))
            bad += [(cls, a, b) for a, b in pairs if _MIRROR.get(a) != b]
        assert not bad, bad


# ===========================================================================
# The tooltip follows the turn
# ===========================================================================

@pytest.mark.parametrize("mode", MODES)
class TestTheTooltipFollowsTheTurn:

    def test_a_turned_density_names_its_rows_as_upright(self, mode):
        """kdensity and function (the point-or-line shape): the turned
        tooltip is the upright one; a density's first field is its grid
        column, not the density."""
        pairs = _pairs(mode, ("kdensity", "function"))
        bad = [(t, _rows(h), _rows(u)) for t, (u, h) in pairs.items()
               if _rows(h) != _rows(u)]
        assert not bad, bad
        assert _rows(pairs["kdensity"][1])[0][0][0][1].startswith("@{x}")

    def test_turned_segments_keep_their_roles(self, mode):
        """pci and pcarrowi (the segment shape): rows in twoway's y1 x1 y2
        x2 order with the upright fields."""
        pairs = _pairs(mode, ("pci", "pcarrowi"))
        bad = [(t, _rows(h), _rows(u)) for t, (u, h) in pairs.items()
               if _rows(h) != _rows(u)]
        assert not bad, bad
        assert [r[0] for r in _rows(pairs["pci"][1])[0][0]] == [
            "y1", "x1", "y2", "x2"]

    def test_a_turned_histogram_answers_along_its_bins(self, mode):
        """The bin rows are the upright ones, and the tool fires anywhere
        within a bin's y-range (``hline``)."""
        u, h = _pairs(mode, ("histogram",))["histogram"]
        [(ut, um)] = _rows(u)
        [(ht, hm)] = _rows(h)
        assert (um, hm, ht) == ("vline", "hline", ut)


def _band_fig(glyph, turned):
    """A figure with one band drawn from computed columns, as the fallback
    sees a fit's band: upright (VArea x, y1, y2) or turned (HArea y, x1,
    x2), and the layer spec it belongs to."""
    fig = figure()
    src = ColumnDataSource({"a": [1.0, 2.0], "b": [3.0, 4.0],
                            "c": [5.0, 6.0]})
    if glyph == "area":
        r = (fig.harea(y="a", x1="b", x2="c", source=src) if turned
             else fig.varea(x="a", y1="b", y2="c", source=src))
    spec = {"type": "area", "yvar": "mpg", "xvar": "weight",
            "options": dict(_H) if turned else {}}
    return fig, [(spec, [r])]


class TestABandAlone:

    def test_a_turned_area_still_has_a_tooltip(self):
        """An HArea a turned layer draws gets the band tooltip with the
        upright rows; it had none (the fallback read x, y1, y2)."""
        got = {}
        for turned in (False, True):
            fig, layers = _band_fig("area", turned)
            dr._dash_build_hover(fig, "", "", "", [], var_labels={},
                                 date_vars={}, numeric_formats={},
                                 layers=layers, formats={})
            got[turned] = _rows(fig)
        assert got[False] and got[True] == got[False], got


# ===========================================================================
# Upright is untouched
# ===========================================================================

def _odd_line(layers_of):
    """A Line bound x="y", y="x" (an upright layer drawn from oddly named
    columns) and a Quad, with the layers *layers_of* gives them."""
    fig = figure()
    src = ColumnDataSource({"x": [1.0, 2.0], "y": [10.0, 20.0]})
    ln = fig.line(x="y", y="x", source=src)
    return fig, layers_of(ln)


class TestUprightIsUntouched:

    def test_a_renderer_of_no_turned_layer_reads_its_own_properties(self):
        """Guard: with no layers, and in a layer without horizontal, the
        first row reads ``glyph.x``'s column, and a Quad's bins ``vline``."""
        plain = {"type": "line", "yvar": "mpg", "xvar": "weight",
                 "options": {}}
        for layers_of in (lambda r: None, lambda r: [(plain, [r])]):
            fig, layers = _odd_line(layers_of)
            dr._dash_build_hover(fig, "", "", "", [], var_labels={},
                                 date_vars={}, numeric_formats={},
                                 layers=layers, formats={})
            [(rows, mode)] = _rows(fig)
            assert rows[0][1].startswith("@{y}") and mode == "mouse"
            qf = figure()
            q = qf.quad(left="left", right="right", top="top", bottom=0,
                        source=ColumnDataSource({"left": [0.0],
                                                 "right": [1.0],
                                                 "top": [2.0]}))
            hist = {"type": "histogram", "var": "mpg", "options": {}}
            dr._dash_build_hover(qf, "", "", "", [], var_labels={},
                                 date_vars={}, numeric_formats={},
                                 layers=None if layers is None
                                 else [(hist, [q])], formats={})
            assert _rows(qf)[0][1] == "vline"

    def test_an_unmapped_class_stays_upright(self, monkeypatch):
        """Guard: a horizontal layer whose glyph class WP-30 P1.9a does not
        map (left upright, with a note) keeps its upright rows."""
        turned = {"type": "line", "yvar": "mpg", "xvar": "weight",
                  "options": dict(_H)}
        tr = dict(dr._DASH_TRANSPOSE)
        tr.pop("Line")
        monkeypatch.setattr(dr, "_DASH_TRANSPOSE", tr)
        fig, layers = _odd_line(lambda r: [(turned, [r])])
        dr._dash_build_hover(fig, "", "", "", [], var_labels={},
                             date_vars={}, numeric_formats={},
                             layers=layers, formats={})
        [(rows, _mode)] = _rows(fig)
        assert rows[0][1].startswith("@{y}")


# ===========================================================================
# After a move: the page of the kept rows, still turned
# ===========================================================================

def _plain(v):
    """*v* with a date the oracle holds as text (a datetime column) written
    as the epoch milliseconds a moved page holds."""
    if isinstance(v, (list, tuple)):
        return type(v)(_plain(x) for x in v)
    if isinstance(v, dict):
        return {k: _plain(x) for k, x in v.items()}
    if isinstance(v, str) and len(v) >= 19 and v[4] == "-" and v[10] == "T":
        return tp._num(pd.Timestamp(v).value / 1e6)
    return v


def _geometry(figs):
    """Glyphs, annotations, ranges, ticks and date kinds of each figure:
    the after-move profile (tooltips are compared on their own, since
    their precision is fixed at build time)."""
    out = []
    for f in figs:
        p = tp._figure_profile(f)
        ax = p["axes"]
        out.append({"glyphs": _plain(p["glyphs"]), "annotations": p["annotations"],
                    "axes": {k: ax[k] for k in ("x_range", "y_range",
                                                "extra_x", "extra_y")},
                    "ticks": [(a["label"], a["ticks"], a["formatter"])
                              for a in ax["x"] + ax["y"]],
                    "kinds": list(getattr(f, "_dash_date_kinds",
                                          (None, None)))})
    return out


def _qualified(spec, if_expr):
    q = json.loads(json.dumps(spec))
    q["build_options"]["filter"] = ""
    for g in q["graphs"]:
        own = (g.get("if_expr") or "").strip()
        g["if_expr"] = f"({own}) & ({if_expr})" if own else if_expr
    return q


def _saved_moved(spec, action, df=None):
    df = tp._DF if df is None else df
    r = jo._saved(spec, df, labels=True)
    sf._move(r, action)
    return r, jo._saved_figs(r)


def _served_moved(spec, action, df=None):
    df = tp._DF if df is None else df
    doc = jo._served(spec, df, labels=True)
    kind, want = action
    [w] = [w for w in tp._widgets_of(doc) if type(w).__name__ == kind]
    if kind == "Select":
        want = [v for v, lab in w.options if lab == want][0]
    tp._fire(w, want)
    return doc, jo._served_figs(doc)


def _moved(spec, action, mode, df=None):
    return (_saved_moved if mode == "saved" else _served_moved)(
        spec, action, df)[1]


def _kept(spec, oracle, mode, df=None):
    df = tp._DF if df is None else df
    q = _qualified(spec, oracle)
    if mode == "saved":
        return jo._saved_figs(jo._saved(q, df, labels=True))
    return jo._served_figs(jo._served(q, df, labels=True))


def _mismatches(after, kept, label):
    bad = []
    if len(after) != len(kept):
        return [(label, "figure counts", len(after), len(kept))]
    for i, (a, b) in enumerate(zip(_geometry(after), _geometry(kept))):
        for k in a:
            if a[k] != b[k]:
                bad.append((label, i, k, tp._diff(a[k], b[k])
                            if isinstance(a[k], (list, dict)) else a[k]))
    return bad


def _turned_classes(figs):
    return [sorted(type(r.glyph).__name__ for r in f.renderers
                   if getattr(r, "glyph", None) is not None) for f in figs]


#: The saved page keeps a binned or density layer's bins and grid over
#: every row after a move, muted and marked "unfiltered" (WP-29 P0.17), so
#: the page of the kept rows is not its oracle: the upright layer after the
#: same move, turned, is.
_STALE = ("histogram", "kdensity")


def _all_turned(filt, upright=()):
    """The 24 turned types, one graph each, then *upright*'s types drawn
    upright, under one filter."""
    return tp._spec(graphs=[(f"h{i}", [plot_for(t, _opts(t, _H))])
                            for i, t in enumerate(_TURNED)]
                    + [(f"u{i}", [plot_for(t, _opts(t))])
                       for i, t in enumerate(upright)],
                    build_options={"filter": filt})


def _turned_profile(geom):
    """An upright figure's after-move geometry as it reads turned: each
    glyph's class and coordinate roles through the transposition, and the
    x and y ranges swapped.  The ranges are not compared: twoway's
    plot-region margin differs by axis (WP-30 P1.3a), before a move as
    after it."""
    g = copy.deepcopy(geom)
    for e in g["glyphs"]:
        e["type"] = dr._DASH_TRANSPOSE.get(e["type"], (e["type"],))[0]
        e["coords"] = {_MIRROR.get(k, k): v for k, v in e["coords"].items()}
    ax = g["axes"]
    ax["x_range"], ax["y_range"] = ax["y_range"], ax["x_range"]
    return g


@requires_node
class TestAfterASavedMove:

    def test_a_turned_layer_stays_turned(self):
        """Guard: for every move, each of the 24 turned types after the
        move equals the saved page built from the kept rows (glyphs and
        bindings, widths and heights, annotations, ranges and ticks after
        WP-30 P1.3a's re-finish), and keeps its turned glyph classes; a
        histogram's and a kdensity's glyphs and legend are the upright
        layer's after the same move, turned (_STALE)."""
        n = len(_TURNED)
        bad = []
        for label, filt, action, oracle in sf._MOVES:
            spec = _all_turned(filt, _STALE)
            built = _figs(spec, "saved")
            before = _turned_classes(built)
            after = _moved(spec, action, "saved")
            kept = _kept(spec, oracle, "saved")
            for i, t in enumerate(_TURNED):
                # Flipped (WP-31 B5c): a turned dot's rows are rebuilt
                # over the re-finished axis on the saved page too.
                if t in dr._DASH_CONTOUR_TYPES:
                    # WP-31 B4b: the saved page keeps a contour as built and
                    # marks it (grid unfiltered) until its twin (B4c,
                    # section 29); the served app refits it
                    # (TestAfterAServedMove).  Its glyphs, and the axes and
                    # ticks its extent sets, are held to the build -- the
                    # glyphs muted by the cue -- and the rest to the kept
                    # rows.
                    _frz = ("glyphs", "axes", "ticks")
                    bad += [m for m in _mismatches([after[i]], [built[i]],
                                                   (label, t))
                            if m[2] in _frz and not all(
                                str(d[0]).endswith("/muted")
                                for d in m[3])]
                    bad += [m for m in _mismatches([after[i]], [kept[i]],
                                                   (label, t))
                            if m[2] not in _frz]
                    continue
                if t not in _STALE:
                    bad += _mismatches([after[i]], [kept[i]], (label, t))
                    continue
                [a] = _geometry([after[i]])
                [u] = _geometry([after[n + _STALE.index(t)]])
                u = _turned_profile(u)
                for k in ("glyphs", "annotations"):
                    if a[k] == u[k]:
                        continue
                    d = tp._diff(a[k], u[k])
                    # Flipped: a turned kdensity or function is keyed by
                    # its grid's name, x, where the upright one is keyed
                    # by its own (WP-43 RH-13, legend_keys_truth.json
                    # hz_kdensity): only that key text may differ.
                    if k == "annotations" and t in ("kdensity", "function"):
                        d = [x for x in d if not (
                            "/items[" in str(x[0]) and x[1] == "x")]
                    if d:
                        bad.append((label, t, k, d))
            if _turned_classes(after) != before:
                bad.append((label, "classes", _turned_classes(after)))
        assert not bad, bad

    def test_turned_bars_keep_their_ends_on_the_axis(self):
        """Guard (TR-55.2): after a saved dropdown move the y range covers
        every kept bar's y +- height/2 and equals the served re-finish."""
        spec = tp._spec([plot_for("bar", _H)],
                        {"filter": sf._MOVES[0][1]})
        figs = {m: _moved(spec, sf._MOVES[0][2], m) for m in MODES}
        f = figs["saved"][0]
        [hb] = [r for r in f.renderers if type(r.glyph).__name__ == "HBar"]
        h = float(hb.glyph.height)
        ys = [float(y) for y in hb.data_source.data[hb.glyph.y]]
        lo, hi = sorted((f.y_range.start, f.y_range.end))
        assert ys and lo <= min(ys) - h / 2 and hi >= max(ys) + h / 2
        s = figs["served"][0]
        assert (f.y_range.start, f.y_range.end) == pytest.approx(
            (s.y_range.start, s.y_range.end))


class TestAfterAServedMove:

    def test_a_turned_layer_stays_turned(self):
        """Guard: each of the 24 turned types after a served dropdown move
        equals a fresh served build on the kept rows, and keeps its turned
        glyph classes."""
        label, filt, action, oracle = sf._MOVES[0]
        spec = _all_turned(filt)
        before = _turned_classes(_figs(spec, "served"))
        after = _moved(spec, action, "served")
        bad = _mismatches(after, _kept(spec, oracle, "served"), label)
        assert _turned_classes(after) == before
        assert not bad, bad

    @pytest.mark.parametrize("mode", _MOVE_MODES)
    def test_the_tooltip_survives_a_move(self, mode):
        """A turned histogram's, kdensity's and function's tooltips after
        a move are their pre-move tooltips, which are the upright ones."""
        types = ("histogram", "kdensity", "function")
        label, filt, action, _oracle = sf._MOVES[0]
        graphs = []
        for i, t in enumerate(types):
            graphs.append((f"u{i}", [plot_for(t, _opts(t))]))
            graphs.append((f"h{i}", [plot_for(t, _opts(t, _H))]))
        spec = tp._spec(graphs=graphs, build_options={"filter": filt})
        before = [_hovers(f) for f in _figs(spec, mode)]
        after = [_hovers(f) for f in _moved(spec, action, mode)]
        assert after == before
        bad = [(t, after[2 * i + 1]) for i, t in enumerate(types)
               if [(r, m.replace("hline", "vline")) for r, m, _c in
                   after[2 * i + 1]] != [(r, m) for r, m, _c in after[2 * i]]]
        assert not bad, bad


# ===========================================================================
# by(), yaxis(2) and a date
# ===========================================================================

def _after_equals_kept(spec, mode, move=None, df=None):
    label, _filt, action, oracle = move or sf._MOVES[0]
    after = _moved(spec, action, mode, df)
    bad = _mismatches(after, _kept(spec, oracle, mode, df), label)
    assert not bad, bad
    return after


@pytest.mark.parametrize("mode", _MOVE_MODES)
class TestByAndSecondAxis:

    def test_by_panels_after_a_move(self, mode):
        """Guard: ``bar mpg weight, horizontal by(foreign)`` with a range
        move: every panel keeps its HBar and the page is the kept rows'."""
        spec = tp._spec([plot_for("bar", _H)], {"filter": sf._MOVES[1][1]},
                        {"by": "foreign"})
        after = _after_equals_kept(spec, mode, sf._MOVES[1])
        panels = [f for f in after if f.renderers]
        assert len(panels) == 2 and all(
            "HBar" in c for c in _turned_classes(panels))

    def test_yaxis2_after_a_move(self, mode):
        """Guard: ``(scatter mpg weight) (bar mpg weight, horizontal
        yaxis(2))``: the turned bar stays on y2, whose range spans the kept
        rows' weights, and keeps its title."""
        spec = tp._spec([plot_for("scatter"), plot_for("bar", dict(
            _H, yaxis="2"))], {"filter": sf._MOVES[0][1]})
        [f] = _after_equals_kept(spec, mode)
        [hb] = [r for r in f.renderers if type(r.glyph).__name__ == "HBar"]
        assert hb.y_range_name == "y2"
        kept = tp._DF[tp._DF.foreign == 1].weight
        rng = f.extra_y_ranges["y2"]
        assert rng.start <= kept.min() and rng.end >= kept.max()
        assert [a.axis_label for a in f.right if a.y_range_name == "y2"]

    @pytest.mark.parametrize("order", ("scatter-first", "bar-first"))
    def test_mixed_orientation_on_a_date_after_a_move(self, order, mode):
        """Guard: a %td date drawn by an upright scatter and a turned bar,
        in either order: after a move the date axis is the one the page of
        the kept rows has (WP-30 P1.9a's fixture rows HZ-26 and HZ-27)."""
        sc = plot_for("scatter", xvar="when")
        bar = plot_for("bar", _H, xvar="when")
        plots = [sc, bar] if order == "scatter-first" else [bar, sc]
        spec = tp._spec(plots, {"filter": sf._MOVES[0][1],
                                "formats": {"when": "%td"}})
        _after_equals_kept(spec, mode)


# ===========================================================================
# No property name from page data (G9)
# ===========================================================================

_HOSTILE = pd.DataFrame({
    "height": tp._DF.mpg, "width": tp._DF.weight, "top": tp._DF.rep,
    "__proto__": tp._DF.price, "foreign": tp._DF.foreign,
    "price": tp._DF.price})


def _reach(x, seen, out):
    """Every Model reachable from a callback arg, through lists, dicts and
    model references."""
    if isinstance(x, (list, tuple)):
        for v in x:
            _reach(v, seen, out)
    elif isinstance(x, dict):
        for v in x.values():
            _reach(v, seen, out)
    elif isinstance(x, Model) and x.id not in seen:
        seen.add(x.id)
        out.append(x)
        for m in x.references():
            if m.id not in seen:
                seen.add(m.id)
                out.append(m)


def _glyph_props(g):
    return {k: repr(v) for k, v in g.properties_with_values(
        include_defaults=False).items() if k != "id"}


class TestNoPropertyNameFromPageData:

    @pytest.mark.parametrize("mode", _MOVE_MODES)
    def test_a_column_named_like_a_property_changes_nothing(self, mode):
        """Guard: a turned bar drawn from columns named ``height`` and
        ``width``, beside ``top`` and ``__proto__``: after a move the
        glyph's height and width keep their build values and the page is
        the kept rows'."""
        spec = tp._spec([{"type": "bar", "yvar": "height", "xvar": "width",
                          "options": dict(_H)}],
                        {"filter": sf._MOVES[0][1]})
        [f0] = _figs(spec, mode, _HOSTILE)
        [b0] = [r for r in f0.renderers if type(r.glyph).__name__ == "HBar"]
        built = _glyph_props(b0.glyph)
        assert isinstance(b0.glyph.height, (int, float))
        [f] = _after_equals_kept(spec, mode, df=_HOSTILE)
        [hb] = [r for r in f.renderers if type(r.glyph).__name__ == "HBar"]
        assert _glyph_props(hb.glyph) == built

    def test_no_callback_can_reach_a_glyph(self):
        """Guard: every filter callback of a turned bar's saved page
        (dropdown, slider and range) runs the module's one filter code, and
        nothing its args reach is a Glyph or a GlyphRenderer."""
        spec = tp._spec([plot_for("bar", _H)], {
            "filter": " || ".join(m[1] for m in sf._MOVES)})
        r = jo._saved(spec, tp._DF, labels=True)
        assert len(r.filter_callbacks) == 3
        bad = []
        for cb in r.filter_callbacks:
            assert isinstance(cb, CustomJS) and cb.code == dr._FILTER_JS
            seen, out = set(), []
            _reach(cb.args, seen, out)
            bad += [type(m).__name__ for m in out
                    if isinstance(m, (Glyph, GlyphRenderer))]
        assert not bad, sorted(set(bad))
