"""test_scheme_key_readers.py -- the scheme keys BUGS.md "Five scheme keys
are parsed and read by nothing" named, each read as twoway reads it
(WP-32, D39 item 1).

Measured 18oct2026 (StataNow 19.5, SVG export, s2color and a user scheme
``#include s2color`` plus the one key, on the ado-path for the session
only; the SVGs compared with their random clip-path ids masked):

* ``gridringstyle zyx2legend_ring #`` draws ``twoway contour depth
  northing easting`` (sandstone) and ``twoway scatter mpg weight,
  colorvar(price)`` (auto) as s2color with ``clegend(ring(#))`` does, for
  0, 1 and 2; ring 0 puts the colour key inside the plot region at its
  position (3, the right edge), the plot region taking the graph's width;
  1, 2 and s2color's 4 draw alike with no other key on that side, and
  beside ``legend(pos(3))`` (ring 3) ring 2 is drawn between the plot and
  the legend where 4 is drawn outside it.
"""
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import test_mode_parity as tp  # noqa: E402
from test_scheme_resolution import MODES, _draw  # noqa: E402
from test_scheme_review_fixes import _user_scheme  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402


def _bar(fig):
    """(side, key) of the colour key.  Flipped (WP-42 CV-3): it was a
    ColorBar on a side panel; twoway draws swatches beside a z axis, the
    figure's key cell, beside the figure on *side* or, at ring(0), over
    the plot region (``center``, at its right or left: the key's
    ``location`` center_right or center_left)."""
    cell = getattr(fig, "_dash_key_cell", None)
    if cell is not None:
        r0 = getattr(cell, "_dash_key_ring0", None)
        if r0 in ("left", "right"):
            return "center", type("K", (), {"location": "center_" + r0})()
        return cell._dash_key_side, cell
    for side in ("left", "right", "above", "below", "center"):
        for m in getattr(fig, side):
            if type(m).__name__ in ("ColorBar", "ContourColorBar"):
                return side, m
    return None, None


_PLOTS = {
    "scatter": lambda: [plot_for("scatter", {"colorvar": "price"})],
    "contour": lambda: [plot_for("contour")],
}


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("kind", sorted(_PLOTS))
class TestTheColourKeysRing:

    def _side(self, mode, kind, go=None, bo=None):
        spec = tp._spec(_PLOTS[kind](), bo or {}, go or {})
        # WP-42 CV-3: the served document's Plots include the key cell.
        [fig] = [f for f in _draw(spec, mode).figures
                 if "dash_key_cell" not in (f.tags or [])]
        side, bar = _bar(fig)
        return side, (bar.location if side == "center" else None)

    def test_s2color_draws_it_outside(self, mode, kind):
        assert self._side(mode, kind) == ("right", None)

    def test_clegend_ring_0_draws_it_inside(self, mode, kind):
        assert self._side(mode, kind, {"clegend": "ring(0)"}) == (
            "center", "center_right")
        assert self._side(mode, kind, {"clegend": "ring(0) pos(9)"}) == (
            "center", "center_left")
        assert self._side(mode, kind, {"clegend": "ring(1)"}) == (
            "right", None)

    def test_the_schemes_ring_is_the_default(self, mode, kind, tmp_path,
                                             monkeypatch):
        _user_scheme(tmp_path, monkeypatch, "wzr0.scheme",
                     ["#include s2color", "gridringstyle zyx2legend_ring 0"])
        assert self._side(mode, kind, bo={"scheme": "wzr0"}) == (
            "center", "center_right")
        # clegend(ring()) still wins.
        assert self._side(mode, kind, {"clegend": "ring(2)"},
                          {"scheme": "wzr0"}) == ("right", None)


@pytest.mark.parametrize("mode", MODES)
def test_the_ring_orders_the_key_beside_the_legend(mode):
    plots = [plot_for("scatter", {"colorvar": "price"}),
             plot_for("scatter", {})]
    plots[1]["yvar"] = "price"

    def order(go):
        figs = _draw(tp._spec(plots, {}, dict(go, legend="pos(3)")),
                     mode).figures
        # Flipped (WP-42 CV-3): the key was a ColorBar in the side panel;
        # it is a key cell, beside the figure (after its panel) or, inside
        # the legend's ring, laid over its spacer in the panel.
        fig = [f for f in figs if "dash_key_cell" not in (f.tags or [])][0]
        cell = fig._dash_key_cell
        names = ["Key" if getattr(m, "name", None) == "dash_key_spacer"
                 else type(m).__name__ for m in fig.right
                 if type(m).__name__ in ("Legend", "ColorBar")]
        if "Key" not in names and cell is not None \
                and cell._dash_key_side == "right":
            names.append("Key")
        return names

    # Bokeh draws a side's first model nearest the plot.
    assert order({}) == ["Legend", "Key"]
    assert order({"clegend": "ring(2)"}) == ["Key", "Legend"]


# ---------------------------------------------------------------------------
# `vertical_text text_option': text()'s vertical alignment
# ---------------------------------------------------------------------------
#
# Measured 18oct2026 (s2color, SVG, ``twoway scatter mpg weight, text(30
# 3000 "TXT")``): a user scheme's `vertical_text text_option top', `bottom'
# and `baseline' draw byte for byte as text()'s alignment(top), (bottom)
# and (baseline), at the default size and at size(huge).  The baseline is
# below the point by 0.35 of the text size at middle, 0.20 at top and
# bottom (alike) and 0.50 at baseline; two lines shift together.  dash
# drew every alignment at middle and named alignment().

#: The text's shift from middle's place, up, in units of its size.
_VALIGN_SHIFT = {"middle": 0.0, "top": 0.15, "bottom": 0.15,
                 "baseline": -0.15}


def _text_labels(go, bo, mode, opts=""):
    import test_added_text as tat
    spec = tat._spec([tat._at(30, 3000, ["TXT"], opts)], go=go, bo=bo)
    return tat._all_labels(spec, "saved" if mode == "standalone" else
                           "served")


def _shift_px(lab):
    import test_added_text as tat
    return tat._pt(lab.text_font_size) * 96.0 / 72.0


@pytest.mark.parametrize("mode", MODES)
class TestTextVerticalAlignment:

    @pytest.mark.parametrize("valign", sorted(_VALIGN_SHIFT))
    @pytest.mark.parametrize("size", ["", " size(huge)"])
    def test_alignment_shifts_the_text(self, mode, valign, size):
        (lab,) = _text_labels({}, {"scheme": "s2color"}, mode,
                              f"alignment({valign}){size}")
        want = _VALIGN_SHIFT[valign] * _shift_px(lab)
        assert lab.y_offset == pytest.approx(want, abs=0.01)
        assert lab.x_offset == pytest.approx(0.0, abs=0.01)

    def test_the_schemes_alignment_is_the_default(self, mode, tmp_path,
                                                  monkeypatch):
        _user_scheme(tmp_path, monkeypatch, "wtvb.scheme",
                     ["#include s2color", "vertical_text text_option "
                      "baseline"])
        (lab,) = _text_labels({}, {"scheme": "wtvb"}, mode)
        assert lab.y_offset == pytest.approx(-0.15 * _shift_px(lab),
                                             abs=0.01)
        (lab,) = _text_labels({}, {"scheme": "wtvb"}, mode,
                              "alignment(middle)")
        assert lab.y_offset == pytest.approx(0.0, abs=0.01)

    def test_a_vertical_text_shifts_across(self, mode):
        """orientation(vertical): the shift is along the text's own up,
        which is screen left."""
        (lab,) = _text_labels({}, {"scheme": "s2color"}, mode,
                              "alignment(top) orientation(vertical)")
        assert lab.x_offset == pytest.approx(-0.15 * _shift_px(lab),
                                             abs=0.01)
        assert lab.y_offset == pytest.approx(0.0, abs=0.01)


# ---------------------------------------------------------------------------
# `numticks_g horizontal_minor' and `vertical_minor': the minor tickset
# ---------------------------------------------------------------------------
#
# Measured 18oct2026 (s2color, SVG, ``twoway scatter mpg weight``): a user
# scheme's `numticks_g horizontal_minor 4' draws byte for byte as
# xmlabel(#4), and `vertical_minor 3' as ymlabel(#3) -- a labelled minor
# tickset at the minortick_label size; xmlabel(#2) beside the scheme's 4
# draws its own two.  dash drew no minor tickset for the scheme's count.

def _minor(mode, go, bo):
    fig = _draw(tp._spec([plot_for("scatter")], bo, go), mode).figures[0]
    out = {}
    for letter, axes in (("x", fig.xaxis), ("y", fig.yaxis)):
        t = axes[0].ticker
        out[letter] = (list((getattr(t, "args", None) or {}).get("mextra")
                            or []) if type(t).__name__ == "CustomJSTicker"
                       else None)
    out["labelsets"] = sum(type(m).__name__ == "LabelSet"
                           for m in fig.center)
    return out


@pytest.mark.parametrize("mode", MODES)
class TestTheSchemesMinorTickset:

    def test_the_schemes_count_is_the_mlabel_rule(self, mode, tmp_path,
                                                  monkeypatch):
        _user_scheme(tmp_path, monkeypatch, "wnh4.scheme",
                     ["#include s2color", "numticks_g horizontal_minor 4"])
        _user_scheme(tmp_path, monkeypatch, "wnv3.scheme",
                     ["#include s2color", "numticks_g vertical_minor 3"])
        s2 = {"scheme": "s2color"}
        assert _minor(mode, {}, s2) == {"x": None, "y": None,
                                        "labelsets": 0}
        want_x = _minor(mode, {"xmlabel": "#4"}, s2)
        assert want_x["x"] and want_x["labelsets"] == 1
        assert _minor(mode, {}, {"scheme": "wnh4"}) == want_x
        assert _minor(mode, {}, {"scheme": "wnv3"}) == _minor(
            mode, {"ymlabel": "#3"}, s2)
        # xmlabel() still wins.
        assert _minor(mode, {"xmlabel": "#2"}, {"scheme": "wnh4"}) == \
            _minor(mode, {"xmlabel": "#2"}, s2)


# ---------------------------------------------------------------------------
# meta's legend: no outline (BUGS.md "meta's legend has no outline in
# twoway and a black one in dash")
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", MODES)
def test_metas_legend_and_kpi_cards_have_no_outline(mode):
    """twoway draws meta's legend with `linestyle legend none' (measured
    18oct2026: a zero-opacity stroke); dash drew it, and the KPI cards, in
    s2color's black."""
    from bokeh.models import Legend
    plots = [plot_for("scatter"), plot_for("scatter", {})]
    plots[1]["yvar"] = "price"
    d = _draw(tp._spec(plots, {"scheme": "meta"}, {},
                       kpis=[tp._kpi()]), mode)
    legends = [m for f in d.figures for side in ("right", "below", "center",
                                                 "left", "above")
               for m in getattr(f, side) if isinstance(m, Legend)]
    assert legends and all(lg.border_line_color is None for lg in legends)
    css = d.css + " ".join(d.div_css)
    card = css.split(".db-kpi-card", 1)[1].split("}")[0]
    assert "solid #000000" not in card and "solid #ffffff" in card, card
    assert "solid none" not in css
    # s2color keeps its black outline.
    d = _draw(tp._spec(plots, {"scheme": "s2color"}, {},
                       kpis=[tp._kpi()]), mode)
    legends = [m for f in d.figures for side in ("right", "below", "center",
                                                 "left", "above")
               for m in getattr(f, side) if isinstance(m, Legend)]
    assert legends and all(str(lg.border_line_color).lower() == "#000000"
                           for lg in legends)


# ---------------------------------------------------------------------------
# `yesno legend_span' and legend(span): the legend placed on the graph
# ---------------------------------------------------------------------------
#
# Measured 19oct2026 (StataNow 19.5, stcolor and s2color, SVG of ``twoway
# (scatter price weight) (scatter mpg weight), ylabel(, format(%15.2fc))``
# with legend(pos(#) [span])): span places the legend along its side on the
# whole graph where twoway otherwise places it on the plot region -- 6 and
# 12 centred on the graph's width (stcolor's box at x 2700 of 5400, the plot
# region's centre 3098), 3 and 9 on its height (y 1620 of 3240, the plot
# region's 1440), 7 and 11 at the graph's left end, 4 and 8 at its bottom;
# 1, 2, 5 and 10 sit where they did, the plot region reaching that end.
# ring(0) is unchanged.  A user scheme's `yesno legend_span yes' draws as
# legend(span) and legend(nospan) undoes it (BUGS.md "Five scheme keys are
# parsed and read by nothing").  Only BokehJS knows the frame's place in
# the canvas, so the figure carries _DASH_SPAN_JS on its laid-out size.

def _span_items(fig):
    """[(model type, kind, side, location), ...] the span hook places."""
    import dash_render as dr
    cbs = {id(cb): cb for k in ("inner_width", "inner_height",
                                "outer_width", "outer_height")
           for cb in fig.js_property_callbacks.get("change:" + k, [])
           if getattr(cb, "code", None) == dr._DASH_SPAN_JS}
    assert len(cbs) <= 1
    out = []
    for cb in cbs.values():
        assert cb.args["fig"] is fig
        out += [(type(it[0]).__name__, it[1], it[2], it[3])
                for it in cb.args["items"]]
    return out


def _two_keys():
    plots = [plot_for("scatter"), plot_for("scatter", {})]
    plots[1]["yvar"] = "price"
    return plots


@pytest.mark.parametrize("mode", MODES)
class TestTheLegendSpans:

    def _items(self, mode, legend, bo=None):
        spec = tp._spec(_two_keys(), bo or {"scheme": "s2color"},
                        {"legend": legend} if legend else {})
        return _span_items(_draw(spec, mode).figures[0])

    def test_span_places_the_legend_on_the_graph(self, mode):
        assert self._items(mode, "pos(6) span") == [
            ("Legend", "legend", "below", "center")]
        assert self._items(mode, "pos(3) span") == [
            ("Legend", "legend", "right", "center")]
        assert self._items(mode, "pos(7) span") == [
            ("Legend", "legend", "below", "bottom_left")]
        assert self._items(mode, "span") == [
            ("Legend", "legend", "below", "center")]

    def test_no_span_and_ring_0_place_nothing(self, mode):
        assert self._items(mode, "") == []
        assert self._items(mode, "pos(6)") == []
        assert self._items(mode, "pos(6) ring(0) span") == []
        assert self._items(mode, "pos(0) span") == []

    def test_the_schemes_span_is_the_default(self, mode, tmp_path,
                                            monkeypatch):
        _user_scheme(tmp_path, monkeypatch, "wls1.scheme",
                     ["#include s2color", "yesno legend_span yes"])
        bo = {"scheme": "wls1"}
        assert self._items(mode, "", bo) == [
            ("Legend", "legend", "below", "center")]
        assert self._items(mode, "pos(9)", bo) == [
            ("Legend", "legend", "left", "center")]
        # legend(nospan) undoes it.
        assert self._items(mode, "nospan", bo) == []

    def test_the_hook_holds_the_graph_regions_margins(self, mode):
        """twoway places a spanned box against the graph region's inner
        edge, the graph's margin in (measured 19oct2026: stcolor's 7
        o'clock box at 152.2 of 5400, the region's edge 113.4 (3.5% of
        3240) plus the 38.8 it keeps from the plot region without span;
        graphregion(margin(l+10)) moves it 324 = 10% of 3240), so the hook
        carries the margin graph sides (l, r, b, t), the user's included."""
        import dash_render as dr

        def sides(go):
            spec = tp._spec(_two_keys(), {"scheme": "s2color"},
                            dict(go, legend="pos(7) span"))
            fig = _draw(spec, mode).figures[0]
            (cb,) = {id(c): c for c in fig.js_property_callbacks[
                "change:inner_width"] if c.code == dr._DASH_SPAN_JS}.values()
            return cb.args["sides"]
        assert sides({}) == [3.5, 3.5, 3.5, 3.5]
        assert sides({"graphregion": "margin(l+10 b+5)"}) == [
            13.5, 3.5, 8.5, 3.5]

    def test_span_beside_nospan_spans(self, mode):
        """Measured 19oct2026 (stcolor and s2color): legend(pos(6) span
        nospan) and legend(pos(6) nospan span) both draw as legend(pos(6)
        span), whatever the order."""
        for opt in ("pos(6) span nospan", "pos(6) nospan span"):
            assert self._items(mode, opt) == [
                ("Legend", "legend", "below", "center")], opt

    def test_by_is_unchanged_by_the_schemes_span(self, mode, tmp_path,
                                                monkeypatch):
        _user_scheme(tmp_path, monkeypatch, "wls2.scheme",
                     ["#include s2color", "yesno legend_span yes"])
        spec = tp._spec(_two_keys(), {"scheme": "wls2"},
                        {"by": "foreign"})
        for fig in _draw(spec, mode).figures:
            # Flipped (WP-32, BUGS.md "Without span by()'s legend was
            # placed on its cell, not on the panels" and "Without span
            # by()'s title, note and caption were placed on their cell,
            # not on the panels"): the served app's figures include by()'s
            # legend and foot cells, whose legend and note are now placed
            # on the panels as twoway places them without span; the
            # scheme's span still places nothing on the grid.
            if str(getattr(fig, "name", None) or "").startswith("dash_by_"):
                import dash_render as dr
                for cb in [c for c in fig.js_property_callbacks.get(
                        "change:inner_width", [])
                        if c.code == dr._DASH_SPAN_JS]:
                    assert {it[5] for it in cb.args["items"]} == {"panels"}
                continue
            assert _span_items(fig) == []


def test_the_span_hook_adds_replaces_and_drops():
    """_dash_span: one callback per figure on its four laid-out sizes; a
    second call for a model replaces its item; kind None drops it, and the
    callback with its last item."""
    import dash_render as dr
    from bokeh.models import Legend, Title
    from bokeh.plotting import figure
    f = figure(width=400, height=300)
    lg, t = Legend(), Title(text="T")
    dr._dash_span(f, lg)
    assert _span_items(f) == []
    dr._dash_span(f, lg, "legend", "below", "center")
    dr._dash_span(f, t, "title", "above", "left", 4)
    dr._dash_span(f, lg, "legend", "below", "bottom_left")
    assert _span_items(f) == [("Title", "title", "above", "left"),
                              ("Legend", "legend", "below", "bottom_left")]
    for k in dr._DASH_SPAN_KEYS:
        assert len(f.js_property_callbacks["change:" + k]) == 1
    dr._dash_span(f, lg)
    assert _span_items(f) == [("Title", "title", "above", "left")]
    dr._dash_span(f, t)
    assert _span_items(f) == []
    assert not any(f.js_property_callbacks.values())


def test_the_span_hook_is_in_the_served_app():
    with open(os.path.join(_HERE, "..", "dash_render.py"),
              encoding="utf-8") as fh:
        src = fh.read()
    assert src.count('"_dash_span",') == 1
    assert src.count('"_DASH_SPAN_JS", "_DASH_SPAN_KEYS",') == 1


@pytest.mark.parametrize("mode", ("saved", "served"))
def test_by_legend_span_places_the_cells_legend_on_the_grid(mode):
    """by(, legend(span)) (measured 19oct2026: twoway centres by()'s legend
    on the whole graph, 2700 of 5400 against 2756.3 without): the legend
    cell carries the span hook, placed on the by() grid ("grid")."""
    import dash_render as dr
    import test_by_axes_keys as bk
    from bokeh.models import Plot

    def cell_items(by):
        spec = bk._spec([bk._graph("g1", bk._TWO, {"by": by})])
        roots, _n, _o = bk._build(mode, spec)
        (cell,) = {id(m): m for r in roots for m in r.references()
                   if isinstance(m, Plot)
                   and m.name == "dash_by_legend"}.values()
        cbs = [c for c in cell.js_property_callbacks.get(
            "change:inner_width", []) if c.code == dr._DASH_SPAN_JS]
        return [(it[1], it[2], it[3], it[5]) for c in cbs
                for it in c.args["items"]]
    assert cell_items("foreign, legend(pos(6) span)") == [
        ("legend", "above", "center", "grid")]
    # Flipped (WP-32, BUGS.md "Without span by()'s legend was placed on
    # its cell, not on the panels"): without span twoway places by()'s
    # legend on the panels plus their axes (measured 19oct2026: pos(6)
    # centred at 2756.3 of 5400, the shared x title's centre; pos(3) at y
    # 1499.3, the shared y title's), so the cell's legend is placed on the
    # panels ("panels"); in a hole, at(), it stays in its cell.
    assert cell_items("foreign, legend(pos(6))") == [
        ("legend", "above", "center", "panels")]
    assert cell_items("foreign, legend(pos(3))") == [
        ("legend", "left", "center", "panels")]
    assert cell_items("foreign, legend(pos(7))") == [
        ("legend", "above", "left", "panels")]
    assert cell_items("foreign, total legend(at(4) pos(0))") == []
    # ring(0) (BUGS.md "by()'s legend(ring(0)) was placed on its cell, not
    # on the panels"): on the panels too, as twoway places it.
    assert cell_items("foreign, legend(ring(0) pos(6))") == [
        ("legend", "above", "center", "panels")]
    assert cell_items("foreign, legend(ring(0) pos(9))") == [
        ("legend", "right", "center", "panels")]
