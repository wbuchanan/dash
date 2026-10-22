"""
test_by_remainder.py -- the rest of by() is drawn as twoway draws it
(WP-31 D10).

dash named by()'s graphregion()/plotregion(), subtitleformat() and the
shrink words as ignored, drew legend(ring(0)) beside the panels with a
note, drew an overall legend that a click did nothing to, gave each panel
the margin of f(panel count) whatever iscale() said, drew no box colour
or nobox from the graph's subtitle() on the panel labels, and left a
panel a filter emptied drawn empty.  The truth is
test/fixtures/by_remainder_truth.json
(scripts/extract_by_remainder_truth.do): per probe, twoway's graph
object and its SVG export's rects and texts.  Measured (and so drawn):

- by()'s graphregion() is the whole graph's region and replaces an outer
  copy; by()'s plotregion() is one region around the panel array; dash
  draws both on every panel's border and chrome cell, and names their
  margin() (twoway insets the array once).
- legend(ring(0)) stays outside the panels on its clock's side, aligned
  at the compass; the overall legend toggles a series in every panel.
- the panel margin is 2.2% x f(k) x iscale().
- subtitleformat() writes an unlabelled panel value in its format.
- the graph's own subtitle(, fcolor() lcolor() nobox) restyle the box.
- noshrink, noishrink, nooverallshrink, ishrink change nothing; the
  by_alternate scheme stubs change nothing.
- a one-panel by() with an empty value label draws no box and the
  Graphs-by note.
"""

import copy
import itertools
import json
import os
import sys
import tempfile
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_by_axes_keys as tk  # noqa: E402
import test_by_grid as tg  # noqa: E402
from by_panel_probe import panel_label, panel_label_title  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "by_remainder_truth.json")
_MODES = ("saved", "served")
_FIX = None
_BUILT = {}
_SEQ = itertools.count()
_TMP = tempfile.mkdtemp(prefix="dash_by_remainder_")
#: The modes, each on one xdist worker (pytest speed, 22oct2026): every
#: test of a mode reads _build_all's one page of every probe, which a
#: worker builds once (17 s served); spread over eight workers each paid
#: for it.
_ONE_BUILD = [pytest.param(m, marks=pytest.mark.xdist_group(
    "by-remainder-" + m)) for m in _MODES]


def _fix():
    global _FIX
    if _FIX is None:
        with open(_FIXTURE, encoding="utf-8") as fh:
            _FIX = json.load(fh)
    return _FIX


def _probe(pid):
    return _fix()["probes"][pid]


def _data():
    """by_grid's auto data with g4 = mod(_n, 4) and onee = 1 labelled
    "" (the extractor's empty value label)."""
    data = tg._data()
    for i, row in enumerate(data["values"], start=1):
        row["g4"] = float(i % 4)
        row["onee"] = 1.0
    for v in ("g4", "onee"):
        data["variableNames"].append(v)
        data["storageTypes"][v] = "float"
        data["variableIsString"][v] = False
        data["variableLabels"][v] = ""
    data["numberOfVariables"] += 2
    data["variableIndices"] = list(range(1, data["numberOfVariables"] + 1))
    data["valueLabels"]["brempty"] = {"1": ""}
    data["valueLabelNames"]["onee"] = "brempty"
    return data


#: The graphs one build per mode draws: name -> (plots, graph options).
_GRAPHS = {
    "rg_red": (tk._ONE, {"by": "foreign, graphregion(fcolor(red))"}),
    "rg_blue": (tk._ONE, {"by": "foreign, plotregion(fcolor(blue))"}),
    "rg_both": (tk._ONE, {"by": "foreign, graphregion(fcolor(red)) "
                                "plotregion(fcolor(blue))"}),
    "rg_outer": (tk._ONE, {"by": "foreign, graphregion(fcolor(red))",
                           "graphregion": "fcolor(green)"}),
    "rg_margin": (tk._ONE, {"by": "foreign, graphregion(margin(large))"}),
    "lg_beside": (tk._TWO, {"by": "rep78"}),
    "lg_hole": (tk._TWO, {"by": "rep78, legend(ring(0))"}),
    "lg_pos5": (tk._TWO, {"by": "rep78, legend(ring(0) pos(5))"}),
    "lg_full": (tk._TWO, {"by": "foreign, legend(ring(0))"}),
    "m2": (tk._ONE, {"by": "foreign"}),
    "m4": (tk._ONE, {"by": "g4"}),
    "m10": (tk._ONE, {"by": "g10"}),
    "m4_half": (tk._ONE, {"by": "g4, iscale(.5)"}),
    "stf_fmt": (tk._ONE, {"by": "foreign, subtitleformat(%9.2f)"}),
    "stf_g4": (tk._ONE, {"by": "g4, subtitleformat(%9.2f)"}),
    "stf_bad": (tk._ONE, {"by": "g4, subtitleformat(size(large) color(red))"}),
    "box_fl": (tk._ONE, {"by": "foreign",
                         "subtitle": ", fcolor(yellow) lcolor(blue)"}),
    "box_nobox": (tk._ONE, {"by": "foreign", "subtitle": ", nobox"}),
    "byin_box": (tk._ONE, {"by": "foreign, subtitle(, fcolor(yellow) "
                                 "lcolor(blue))"}),
    "shr_nil": (tk._ONE, {"by": "foreign, noshrink noishrink "
                                "nooverallshrink ishrink"}),
    "one_empty": (tk._ONE, {"by": "onee"}),
    # The D10 follow-up: an outer graphregion() under by(), and legend()
    # at a corner without ring(0).
    "rg_outer_only": (tk._ONE, {"by": "foreign",
                                "graphregion": "fcolor(green)",
                                "plotregion": "fcolor(yellow)"}),
    "lg_pos1": (tk._TWO, {"by": "rep78, legend(pos(1))"}),
}


def _build_all(mode):
    if mode not in _BUILT:
        graphs = [tk._graph(n, p, go)
                  for n, (p, go) in _GRAPHS.items()]
        spec = tk._spec(graphs, scheme="s2color")
        roots, notes, owner = tk._build(mode, spec, data=_data())
        _BUILT[mode] = (roots, notes, owner)
    return _BUILT[mode]


def _grid_of(mode, name):
    """The GridPlot of graph *name* (its panels' title is the name)."""
    from bokeh.models import GridPlot
    roots, _n, _o = _build_all(mode)
    grids = tk._grids(roots)
    if name in grids:
        return grids[name]
    # A panel with an empty label: found by its title.
    for root in roots:
        for m in root.references():
            if isinstance(m, GridPlot) and any(
                    getattr(c[0], "_dash_by_panel", False)
                    and str(c[0].title.text or "") == name
                    for c in m.children):
                return m
    raise AssertionError((name, sorted(grids)))


def _cells(mode, name):
    return [c[0] for c in _grid_of(mode, name).children]


def _panels(mode, name):
    out = [c for c in _cells(mode, name)
           if type(c).__name__ == "figure"
           and (getattr(c, "_dash_by_panel", False)
                or panel_label_title(c) is not None)]
    assert out, name
    return out


def _notes(mode):
    return _build_all(mode)[1]


def _legend(mode, name):
    from bokeh.models import Legend
    for c in _cells(mode, name):
        if getattr(c, "name", None) == "dash_by_legend":
            for side in ("left", "right", "above", "below", "center"):
                for m in getattr(c, side):
                    if isinstance(m, Legend):
                        return c, m
    return None, None


# ---------------------------------------------------------------------------

class TestTheFixture:
    def test_meta(self):
        assert sorted(_fix()["_meta"]) == [
            "born_date", "by_alt_stubs", "dash_commit", "extracted",
            "source", "stata_version"]
        assert _fix()["_meta"]["by_alt_stubs"][:2] == [
            "yesno by_alternate_xaxes no", "yesno by_alternate_yaxes no"]

    def test_keys(self):
        p = _fix()["probes"]
        for k in ("regions_graph_red", "regions_plot_blue", "regions_both",
                  "regions_outer_vs_by", "regions_margin", "legend_ring0_hole",
                  "legend_ring0_full", "legend_ring0_pos5", "alt_no",
                  "alt_yes", "margin_2", "margin_4", "margin_10",
                  "margin_iscale_half", "stf_fmt", "stf_var", "stf_textbox",
                  "sub_fcolor_lcolor", "sub_nobox", "one_panel_empty"):
            assert k in p and p[k]["rc"] == 0, k
        assert p["regions_comma"]["rc"] == 198


def _fill_of(pid, w_min):
    """The fill of the first solid rect at least *w_min* wide after the
    canvas (twoway's graph region, or the array's region)."""
    return [r["fill"] for r in _probe(pid)["rects"][1:]
            if r["fill"] not in (None, "none") and r["w"] >= w_min][0]


class TestRegions:
    @pytest.mark.parametrize("mode", _ONE_BUILD)
    def test_each_panel(self, mode):
        """by()'s graphregion() fills every panel's border and chrome cell
        (twoway's whole graph region, regions_graph_red); by()'s
        plotregion() fills every panel's border, the array's region
        (regions_plot_blue: one rect around the panels), the frames
        staying white."""
        red = _fill_of("regions_graph_red", 3900)
        assert red == "#ff0000"
        blue = [r["fill"] for r in _probe("regions_plot_blue")["rects"]
                if 3000 < (r["w"] or 0) < 3900 and r["fill"] != "none"]
        assert blue == ["#0000ff"]
        for f in _panels(mode, "rg_red"):
            assert str(f.border_fill_color).lower() == red
            assert str(f.background_fill_color).lower() == "#ffffff"
        heads = [c for c in _cells(mode, "rg_red")
                 if getattr(c, "name", "") == "dash_by_foot"]
        assert heads and all(str(c.border_fill_color).lower() == red
                             for c in heads)
        for f in _panels(mode, "rg_blue"):
            assert str(f.border_fill_color).lower() == "#0000ff"
            assert str(f.background_fill_color).lower() == "#ffffff"
        for f in _panels(mode, "rg_both"):
            assert str(f.border_fill_color).lower() == "#0000ff"
        foot = [c for c in _cells(mode, "rg_both")
                if getattr(c, "name", "") == "dash_by_foot"]
        assert str(foot[0].border_fill_color).lower() == red

    @pytest.mark.parametrize("mode", _ONE_BUILD)
    def test_by_copy_wins(self, mode):
        assert _fill_of("regions_outer_vs_by", 3900) == "#ff0000"
        for f in _panels(mode, "rg_outer"):
            assert str(f.border_fill_color).lower() == "#ff0000"

    @pytest.mark.parametrize("mode", _ONE_BUILD)
    def test_silent(self, mode):
        bad = [n for n in _notes(mode) if "not implemented" in n and (
            "graphregion(fcolor" in n or "plotregion(fcolor" in n)]
        assert bad == []

    @pytest.mark.parametrize("mode", _ONE_BUILD)
    def test_margin_named(self, mode):
        """twoway insets the whole array by by()'s margin() once
        (regions_margin: panel 1 moves right, panel 2 does not).  Flipped
        (WP-31 D10b): dash insets the array too (test_by_array.py), so it
        is no longer named."""
        p = _probe("regions_margin")["rects"]
        base = _probe("by_foreign")["rects"]
        assert p[3]["x"] > base[3]["x"] and p[5]["x"] == base[5]["x"]
        assert not any("graphregion(margin(large))" in n
                       for n in _notes(mode))


class TestLegend:
    def test_fixture_rule(self):
        """ring(0): outside the panels, below them, as without ring(0)
        but nearer; hole and full grid alike; pos(5) right-aligned."""
        def box(pid):
            return [r for r in _probe(pid)["rects"]
                    if r["fill"] == "#ffffff" and r["w"] > 1900
                    and r["h"] < 200][0]
        hole, full = box("legend_ring0_hole"), box("legend_ring0_full")
        beside, pos5 = box("legend_beside"), box("legend_ring0_pos5")
        panels_bottom = 1355.23 + 775.32
        assert hole["y"] > panels_bottom and hole["y"] < beside["y"]
        assert (hole["x"], hole["y"]) == (full["x"], full["y"])
        assert abs(pos5["x"] + pos5["w"] - (2688.84 + 1135.65)) < 1

    @pytest.mark.parametrize("mode", _ONE_BUILD)
    def test_no_warning(self, mode):
        assert not [n for n in _notes(mode) if "drawn beside the panels" in n]

    @pytest.mark.parametrize("mode", _ONE_BUILD)
    def test_hole(self, mode):
        """ring(0) with a hole: the legend cell stays below the panels,
        centred (pos 6)."""
        cell, leg = _legend(mode, "lg_hole")
        assert leg is not None and leg.location == "center"
        assert leg in cell.above

    @pytest.mark.parametrize("mode", _ONE_BUILD)
    def test_full_grid(self, mode):
        cell, leg = _legend(mode, "lg_pos5")
        assert leg.location == "right"
        cell, leg = _legend(mode, "lg_full")
        assert leg.location == "center"

    @pytest.mark.parametrize("mode", _ONE_BUILD)
    def test_items_span_panels(self, mode):
        _c, leg = _legend(mode, "lg_beside")
        panels = _panels(mode, "lg_beside")
        assert leg.click_policy == "hide"
        assert len(panels) == 5
        for it in leg.items:
            owners = [p for p in panels
                      if any(r in p.renderers for r in it.renderers)]
            assert len(owners) == len(panels)
        # each item reaches its own series in every panel
        first = [p.renderers for p in panels]
        r0 = [r for r in leg.items[0].renderers if r in first[0]]
        r1 = [r for r in leg.items[1].renderers if r in first[0]]
        assert r0 and r1 and r0[0] is not r1[0]

    def test_click_hides_every_panel(self):
        """BokehJS hides every renderer of a clicked item (click_policy
        hide); the items are in one document, so the saved page validates
        with no error."""
        from bokeh.core.validation import check_integrity
        roots, _n, _o = _build_all("saved")
        refs = set()
        for r in roots:
            refs |= set(r.references())
        issues = check_integrity(refs)
        assert not issues.error, issues.error


class TestAlternateAxes:
    def test_alternate(self):
        """The by_alternate stubs set yes change nothing twoway draws
        (bygraph_g.class's alternate code is commented out)."""
        a, b = _probe("alt_no"), _probe("alt_yes")
        assert b["alternate_xaxes"] and b["alternate_yaxes"]
        assert a["texts"] == b["texts"] and a["rects"] == b["rects"]

    @pytest.mark.parametrize("mode", _ONE_BUILD)
    def test_default_unchanged(self, mode):
        assert dr.SchemeParser("s2color") is not None
        assert "alt_xaxes" not in dr._DASH_BY_FLAG_DEFAULTS


def _measured_margin(pid):
    """twoway's panel margin over 2.2% of min(W, H): the right inset of
    the first panel, from its region's edge to the 5,000 tick."""
    p = _probe(pid)
    reg = [r for r in p["rects"] if r["fill"] == "#ffffff"
           and r["stroke"] is None][0]
    x5 = [t["x"] for t in p["texts"] if t["t"] == "5,000"
          and reg["x"] < t["x"] < reg["x"] + reg["w"]][0]
    m = min(p["canvas"]["w"], p["canvas"]["h"])
    return (reg["x"] + reg["w"] - x5) / m / 0.022


class TestMargin:
    @pytest.mark.parametrize("mode", _ONE_BUILD)
    @pytest.mark.parametrize("name,pid", [("m2", "margin_2"),
                                          ("m4", "margin_4"),
                                          ("m10", "margin_10")])
    def test_count(self, mode, name, pid):
        want = _measured_margin(pid)
        for f in _panels(mode, name):
            got = f._dash_margin["x"][1] / (0.022 * 4.0 / 5.5)
            assert abs(got - want) < 2e-3, (name, got, want)

    @pytest.mark.parametrize("mode", _ONE_BUILD)
    def test_iscale(self, mode):
        want = _measured_margin("margin_iscale_half")
        assert abs(want - 0.5) < 2e-3
        for f in _panels(mode, "m4_half"):
            got = f._dash_margin["x"][1] / (0.022 * 4.0 / 5.5)
            assert abs(got - want) < 2e-3


class TestSubtitleFormat:
    def test_fixture(self):
        assert [l["text"] for l in _probe("stf_fmt")["labels"]] == [
            "0.00", "1.00"]
        assert [l["text"] for l in _probe("stf_var")["labels"]] == [
            "0.0", "1.0", "2.0", "3.0"]
        assert [l["text"] for l in _probe("stf_label")["labels"]] == [
            "Domestic", "Foreign"]
        assert [l["text"] for l in _probe("stf_textbox")["labels"]] == [
            "Domestic", "Foreign"]

    def test_unit(self):
        f = dr._dash_by_subtitle_format
        assert f("g, subtitleformat(%9.2f)") == "%9.2f"
        assert f("g, subtitleformat(var)") == "var"
        assert f("g, subtitleformat(size(large) color(red))") == ""
        assert f("g") == "" and f(None) == ""
        lab = dr._dash_facet_label(["g"], 1.0, subtitle_format="%9.2f")
        assert lab == "1.00"
        lab = dr._dash_facet_label(["g"], 1.0, subtitle_format="var",
                                   formats={"g": "%9.1f"})
        assert lab == "1.0"

    @pytest.mark.parametrize("mode", _ONE_BUILD)
    def test_subtitleformat(self, mode):
        assert [panel_label(f) for f in _panels(mode, "stf_g4")] == [
            "0.00", "1.00", "2.00", "3.00"]
        assert [panel_label(f) for f in _panels(mode, "stf_fmt")] == [
            "Domestic", "Foreign"]
        assert [panel_label(f) for f in _panels(mode, "stf_bad")] == [
            "0", "1", "2", "3"]
        assert not [n for n in _notes(mode) if "subtitleformat" in n]


def _box(fig):
    from bokeh.models import ColorBar
    for s in ("above", "below"):
        for m in getattr(fig, s):
            if isinstance(m, ColorBar) and m.name == "dash_by_label_box":
                return m
    return None


class TestLabelBox:
    @pytest.mark.parametrize("mode", _ONE_BUILD)
    def test_box_colours(self, mode):
        fills = [r for r in _probe("sub_fcolor_lcolor")["rects"]
                 if r["h"] and r["h"] < 130]
        assert fills[0]["fill"] == "#ffff00" and fills[1]["stroke"] == "#0000ff"
        for f in _panels(mode, "box_fl"):
            b = _box(f)
            assert b.color_mapper.palette[0].lower() == "#ffff00"
            assert str(b.bar_line_color).lower() == "#0000ff"
        assert not [n for n in _notes(mode) if "fcolor(yellow)" in n
                    and "box_fl" in n]

    @pytest.mark.parametrize("mode", _ONE_BUILD)
    def test_nobox(self, mode):
        assert not [r for r in _probe("sub_nobox")["rects"]
                    if r["h"] and r["h"] < 130]
        for f in _panels(mode, "box_nobox"):
            assert _box(f) is None
            assert panel_label_title(f).visible is True

    @pytest.mark.parametrize("mode", _ONE_BUILD)
    def test_by_subtitle_leaves_the_box(self, mode):
        """by()'s own subtitle() is the overall subtitle: its box words
        leave the panel labels' boxes as they are (byin_fcolor_lcolor)."""
        fills = [r["fill"] for r in _probe("byin_fcolor_lcolor")["rects"]
                 if r["h"] and r["h"] < 130 and r["fill"] != "none"]
        assert fills == ["#d9e6eb", "#d9e6eb"]
        for f in _panels(mode, "byin_box"):
            assert _box(f).color_mapper.palette[0].lower() == "#d9e6eb"


class TestShrink:
    def test_fixture(self):
        for g in ("g2", "g10"):
            base = _probe("shrink_title_%s" % g)
            for w in ("noshrink", "noishrink", "nooverallshrink", "ishrink"):
                p = _probe("shrink_%s_%s" % (w, g))
                assert p["marker_r"] == base["marker_r"], (w, g)
            for w in ("shrink", "overallshrink"):
                p = _probe("shrink_%s_%s" % (w, g))
                assert abs(p["marker_r"] / base["marker_r"] - 0.795) < 0.01

    @pytest.mark.parametrize("mode", _ONE_BUILD)
    def test_word(self, mode):
        """The four words that change nothing are honoured in silence."""
        assert not [n for n in _notes(mode) if "noishrink" in n
                    or "nooverallshrink" in n]


class TestOnePanel:
    def test_fixture(self):
        p = _probe("one_panel_empty")
        assert p["n"] == 1 and p["labels"][0]["text"] == ""
        assert p["note"] == "Graphs by onee"
        assert not [r for r in p["rects"] if r["fill"] == "#d9e6eb"
                    and r["h"] < 200]
        assert [t["t"] for t in p["texts"]
                if t["t"].startswith("Graphs by")] == ["Graphs by onee"]

    @pytest.mark.parametrize("mode", _ONE_BUILD)
    def test_chrome(self, mode):
        from by_panel_probe import chrome_texts
        cells = _cells(mode, "one_empty")
        figs = [c for c in cells if type(c).__name__ == "figure"]
        assert len(figs) == 1 and _box(figs[0]) is None
        foot = [c for c in cells if getattr(c, "name", "") == "dash_by_foot"]
        assert foot and any("Graphs by onee" in t
                            for t in chrome_texts(foot[0]))


# ---- the emptied panel ------------------------------------------------------

def _move_spec():
    import test_mode_parity as tp
    return tp._spec(plots=[{"type": "scatter", "yvar": "mpg",
                            "xvar": "weight", "options": {}}],
                    graph_options={"by": "foreign"},
                    build_options={"filter": "price, type(slider)"})


def _saved_panels(r):
    return [r.figures[k] for k, _l in r._facet_map["g1"]]


class TestEmptiedPanels:
    def test_saved_hidden(self):
        import test_saved_filter_layers as sl
        r = sl._render(_move_spec())
        sl._move(r, ("Slider", 11000.0))
        assert [f.visible for f in _saved_panels(r)] == [False, True]

    def test_saved_restored(self):
        import test_saved_filter_layers as sl
        r = sl._render(_move_spec())
        sl._move(r, ("Slider", 11000.0))
        sl._move(r, ("Slider", 3000.0))
        assert [f.visible for f in _saved_panels(r)] == [True, True]

    def _served(self):
        import test_mode_parity as tp
        doc, _w = tp._served(_move_spec())
        sliders = [w for w in tp._widgets_of(doc)
                   if type(w).__name__ == "Slider"]
        from bokeh.plotting import figure as _figure
        panels = [m for m in doc.select({"type": _figure})
                  if getattr(m, "_dash_by_panel", False)]
        panels.sort(key=lambda f: panel_label(f))
        return tp, sliders[0], panels

    def test_served_hidden(self):
        tp, w, panels = self._served()
        tp._fire(w, 11000.0)
        assert [f.visible for f in panels] == [False, True]

    def test_served_restored(self):
        tp, w, panels = self._served()
        tp._fire(w, 11000.0)
        tp._fire(w, 3000.0)
        assert [f.visible for f in panels] == [True, True]

    def test_a_hidden_panel_keeps_its_cell(self):
        import test_saved_filter_layers as sl
        r = sl._render(_move_spec())
        before = None
        from bokeh.models import GridPlot
        grids = [m for m in r._last_layout_root.references()
                 if isinstance(m, GridPlot)]
        before = [len(g.children) for g in grids]
        sl._move(r, ("Slider", 11000.0))
        assert [len(g.children) for g in grids] == before


class TestTheWiring:
    def test_js_position(self):
        js = dr._FILTER_JS
        i = js.index("function dash_kernel")
        j = js.index("// agg_sources is a Bokeh model list")
        assert i < js.index("function dash_panels_visibility") < j

    def test_builder_defaults(self):
        """Pages without a by() graph carry no panel args (their saved
        bytes are unchanged); a by() page carries the three."""
        import test_saved_filter_layers as sl
        r = sl._render(_move_spec())
        args = r.filter_callbacks[0].args
        assert json.loads(args["by_panels_json"]) == [[0, [0]], [1, [1]]]
        assert len(args["by_panel_figs"]) == 2

    def test_template_call(self):
        # WP-32: the template is _generate_app_source_body's; the method
        # of the old name wraps it (the sourceless renderer's stubs).
        src = "\n".join(l for l in dr.__dict__["ServerAppBuilder"]
                        ._generate_app_source_body.__code__.co_consts
                        if isinstance(l, str))
        assert "_dash_panel_visibility(_axis_figs, _axis_fmap)" in src


def test_panel_visibility_unit():
    from bokeh.models import ColumnDataSource
    from bokeh.plotting import figure
    f = figure()
    src = ColumnDataSource({"x": [1.0], "y": [2.0]})
    f.scatter("x", "y", source=src)
    f._dash_by_panel = True
    dr._dash_panel_visibility({"a": f}, {"g": [("a", "A")]})
    assert f.visible is True
    src.data = {"x": [], "y": []}
    dr._dash_panel_visibility({"a": f}, {"g": [("a", "A")]})
    assert f.visible is False
    assert dr._dash_panel_source_rows(figure()) is None


def test_region_options_unit():
    o = dr._dash_by_region_options(
        "foreign, graphregion(fcolor(red) margin(large)) plotregion(lcolor(black))")
    assert o["graphregion"] == "fcolor(red)"
    # Flipped (WP-31 D10b): the outline is read apart, drawn once around
    # the array.
    assert o["plotregion"] == "" and o["outline"] == "lcolor(black)"
    assert o["given"] and o["margin"] == ["graphregion(margin(large))"]
    assert dr._dash_by_region_options("foreign")["given"] is False


def test_compass_unit():
    c = dr._dash_by_compass_location
    assert c(5, "below") == "right" and c(7, "below") == "left"
    assert c(6, "below") == "center" and c(1, "above") == "right"
    assert c(10, "right") == "top" and c(3, "right") == "center"


def _kid(mode, name, cell_name):
    for c in _grid_of(mode, name).children:
        if getattr(c[0], "name", None) == cell_name:
            return c
    return None


class TestTheFollowUp:
    """Two differences found after the D10 commit, measured
    (by_remainder_truth.json): an outer graphregion() under by() draws
    nothing twoway shows, and legend(ring(0)) below the panels sits
    between them and the x title, where the default legend sits below the
    title; a corner position() is aligned with or without ring(0)."""

    def test_fixture(self):
        p = _probe("regions_outer_only")
        assert p["rects"][1]["fill"] == "#eaf2f3"
        assert not [r for r in p["rects"] if r["fill"] == "#008000"]
        assert [r["fill"] for r in p["rects"]
                if r["fill"] == "#ffff00"] == ["#ffff00", "#ffff00"]

        def ys(pid):
            t = {x["t"]: x["y"] for x in _probe(pid)["texts"]}
            return t["Mileage (mpg)"], t["Weight (lbs.)"]
        key, xt = ys("legend_ring0_hole")
        assert key < xt
        key, xt = ys("legend_beside")
        assert key > xt
        a = [r for r in _probe("legend_pos1")["rects"]
             if r["fill"] == "#ffffff" and r["w"] > 1900 and r["h"] < 200]
        b = [r for r in _probe("legend_ring0_pos1")["rects"]
             if r["fill"] == "#ffffff" and r["w"] > 1900 and r["h"] < 200]
        assert a == b and abs(a[0]["x"] + a[0]["w"] - (2688.84 + 1135.65)) < 1

    @pytest.mark.parametrize("mode", _ONE_BUILD)
    def test_outer_graphregion_draws_nothing(self, mode):
        for f in _panels(mode, "rg_outer_only"):
            assert str(f.border_fill_color).lower() == "#eaf2f3"
            assert str(f.background_fill_color).lower() == "#ffff00"

    @pytest.mark.parametrize("mode", _ONE_BUILD)
    def test_ring0_sits_inside_the_titles(self, mode):
        leg, xt = _kid(mode, "lg_hole", "dash_by_legend"), \
            _kid(mode, "lg_hole", "dash_by_xtitle")
        assert leg[1] < xt[1], (leg[1:], xt[1:])
        leg, xt = _kid(mode, "lg_beside", "dash_by_legend"), \
            _kid(mode, "lg_beside", "dash_by_xtitle")
        assert leg[1] > xt[1]

    @pytest.mark.parametrize("mode", _ONE_BUILD)
    def test_corner_aligned_without_ring0(self, mode):
        _c, leg = _legend(mode, "lg_pos1")
        assert leg.location == "right"
