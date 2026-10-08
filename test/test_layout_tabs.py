"""test_layout_tabs.py — S12 defects 2-6: named layout, tabs, and the dead path.

Five defects that share one shape: an option is accepted, carried all the way
to Python, and then quietly dropped.

2. ``layout(name:row,col ...)`` is validated in ``dash.ado`` and documented in
   ``dash.sthlp``, and never implemented — ``_compute_grid`` splits on
   whitespace and calls ``int(parts[0])`` on ``"s1:1,1"``, raises
   ``ValueError``, and falls through to the automatic grid.
3. ``tabs()`` is parsed, passed to Python, and discarded unless the layout is
   Bootstrap — with no warning.
4. Tab labels are forcibly ``.title()``-cased, so ``tabs(MPG stuff: u1)``
   renders "Mpg Stuff" and there is no way to suppress it.
5. ``_NONSELECTION_ALPHA`` is applied only in ``_build_figures``, which
   ``render()`` never calls, so linked-brush dimming has never shipped.
6. ``_setup_sources`` and ``_build_figures`` are duplicates of ``render()``'s
   phases that have already diverged. Verified independently: ``"_all"`` is
   expanded at exactly two sites, one in each of them, and neither is on the
   path ``render()`` takes.

On defect 6 the plan says to delete both helpers. That would repoint roughly
ninety call sites across eleven test files, and ``render()`` returns HTML
rather than figures, so the tests could not follow. These tests instead pin
the property the plan is actually after — **one implementation, not two** — by
requiring that ``render()`` and ``_build_figures()`` agree. Deleting is one way
to get there; making ``render()`` use them is another, and it keeps the
figures reachable for testing.
"""
import html
import json
import os
import re
import sys
import tempfile

import numpy as np
import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import Plot, Tabs

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render
from dash_render import DashRenderer

from conftest import make_spec, make_data_json


def _page_docs(out):
    """The Bokeh documents a saved page embeds, read back as models.

    A needle searched in the page text is not enough: the page inlines
    BokehJS, and "Group", "Alpha" and "Beta" are in it -- measured
    24sep2026 in a page with no tabs() at all, under auto, bs and "2 1".
    file_html (every layout but bs) puts the document in a <script
    type="application/json"> block; components() (layout(bs)) puts it in
    the JS string ``const docs_json = '...'``, whose backslashes are
    doubled.  Both are HTML-escaped."""
    texts = [html.unescape(b) for b in re.findall(
        r'<script type="application/json" id="[^"]+">\s*(.*?)\s*</script>',
        out, re.S)]
    texts += [html.unescape(m.group(1).replace("\\\\", "\\"))
              for m in re.finditer(r"const docs_json = '(.*?)';", out, re.S)]
    return [Document.from_json(d) for t in texts
            for d in json.loads(t).values()]


def _tab_titles(out):
    """The titles of the tabs the page's Tabs models carry, in order."""
    return [p.title for d in _page_docs(out)
            for t in d.select({"type": Tabs}) for p in t.tabs]


def _placements(out):
    """{figure id: how many times the page's layouts place it} -- every
    root of every embedded document walked through its layout children
    (a Tabs' panels, a grid's cells), counting each figure reached."""
    counts = {}

    def visit(m):
        if isinstance(m, (list, tuple)):
            for x in m:
                if x is not None and not isinstance(x, (int, float, str)):
                    visit(x)
            return
        if m is None:
            return
        if isinstance(m, Plot):
            counts[m.id] = counts.get(m.id, 0) + 1
        for attr in ("children", "tabs", "child"):
            k = getattr(m, attr, None)
            if k is not None:
                visit(k)

    for d in _page_docs(out):
        for root in d.roots:
            visit(root)
    return counts


def _df(n=30):
    return pd.DataFrame({
        "mpg": np.linspace(12.0, 41.0, n),
        "weight": np.linspace(1760.0, 4840.0, n),
        "price": np.linspace(3291.0, 15906.0, n),
        "foreign": np.array([0.0, 1.0] * (n // 2)),
    })


def _g(name, *, title="", by=""):
    go = dict({"name": name}, **({"title": title} if title else {}))
    if by:
        go["by"] = by
    return {
        "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                   "options": {}}],
        "graph_options": go,
        "if_expr": "", "in_expr": "",
    }


# Value labels for foreign, so a by() facet has a panel title to look for.
_LABELS = {"origin": {"0": "Domestic", "1": "Foreign"}}
_LABEL_NAMES = {"foreign": "origin"}


def _render(graphs, layout, *, tabs="", link="", value_labels=None,
            value_label_names=None, build_extra=None):
    spec = make_spec(graphs[0]["plots"])
    spec["graphs"] = graphs
    spec["build_options"]["layout"] = layout
    spec["build_options"]["link"] = link
    spec["build_options"]["registry"] = " ".join(
        g["graph_options"]["name"] for g in graphs)
    if tabs:
        spec["build_options"]["tabs"] = tabs
    if build_extra:
        spec["build_options"].update(build_extra)
    sp = tempfile.mkstemp(".json")[1]
    dp = tempfile.mkstemp(".json")[1]
    op = tempfile.mkstemp(".html")[1]
    with open(sp, "w") as f:
        json.dump(spec, f)
    with open(dp, "w") as f:
        json.dump(make_data_json(_df(), value_labels=value_labels,
                                 value_label_names=value_label_names), f)
    dr = DashRenderer(sp, dp, op)
    out = dr.render()
    for p in (sp, dp, op):
        try:
            os.unlink(p)
        except OSError:
            pass
    return out, dr


_THREE = [_g("s1", title="First"), _g("s2", title="Second"),
          _g("s3", title="Third")]


# ======================================================================
# Defect 2 — layout(name:row,col)
# ======================================================================

class TestNamedPlacementLayout:
    """Validated in Stata, documented in the help, never implemented."""

    def test_compute_grid_does_not_fall_through_to_auto(self):
        """A spec whose answer DIFFERS from auto, so the two are separable.

        With three graphs the automatic grid is 2x2, so a placement spec that
        also wants 2x2 cannot show whether it was honoured or ignored. This
        one wants a single column.
        """
        _, dr = _render(_THREE, "auto")
        assert dr._compute_grid(3, "auto") == (2, 2), "auto changed shape"
        rows, cols = dr._compute_grid(3, "s1:0,0 s2:1,0 s3:2,0")
        assert (rows, cols) == (3, 1), (
            f"a single-column placement spec produced {rows}x{cols}; "
            f"int(parts[0]) on 's1:0,0' raises and the grid silently falls "
            f"back to the 2x2 automatic layout"
        )

    def test_each_graph_lands_at_its_named_cell(self):
        _, dr = _render(_THREE, "s1:0,0 s2:0,1 s3:1,0")
        placed = dr._placement_map("s1:0,0 s2:0,1 s3:1,0")
        assert placed == {"s1": (0, 0), "s2": (0, 1), "s3": (1, 0)}, placed

    def test_a_one_based_spec_is_accepted_too(self):
        """dash.ado's own validation allows the 1-based form."""
        _, dr = _render(_THREE, "auto")
        placed = dr._placement_map("s1:1,1 s2:1,2")
        assert placed, "the 1-based placement form was rejected outright"

    def test_a_graph_the_spec_omits_is_still_placed(self):
        """The Bootstrap path appends omitted names; match that."""
        out, dr = _render(_THREE, "s1:0,0 s2:0,1")
        # Every graph was built: the loop below sees only what was, so a
        # graph never built passed it.
        assert set(dr.figures) == {"s1", "s2", "s3"}, sorted(dr.figures)
        for name, fig in dr.figures.items():
            assert fig.id in out, (
                f"{name} was omitted from the placement spec and then "
                f"dropped from the dashboard entirely"
            )

    def test_the_ordinary_two_number_form_still_works(self):
        _, dr = _render(_THREE, "auto")
        assert dr._compute_grid(3, "1 3") == (1, 3)

    def test_auto_still_works(self):
        """Four items in ceil(sqrt(4)) = 2 columns, so 2 rows.  "rows >= 1
        and cols >= 1" passed any grid at all, four in one row included."""
        _, dr = _render(_THREE, "auto")
        rows, cols = dr._compute_grid(4, "auto")
        assert (rows, cols) == (2, 2)


# ======================================================================
# Defect 3 — tabs() outside Bootstrap
# ======================================================================

class TestTabsAreNotSilentlyConditional:

    def test_tabs_under_bootstrap_build_a_widget(self):
        """The control.  Read from the page's document: "Group" is in the
        inlined BokehJS of every page, tabs() or not (see _page_docs)."""
        out, dr = _render(_THREE, "bs", tabs="Group: s1 s2")
        assert _tab_titles(out) == ["Group"]

    def test_tabs_under_auto_are_not_silently_discarded(self):
        """Either build them or say why — never drop them in silence."""
        import warnings
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            out, dr = _render(_THREE, "auto", tabs="Group: s1 s2")
        # A tab in the page's document, not the word in its text: "Group"
        # in the page was always true, so `warned' was never needed.
        built = _tab_titles(out) == ["Group"]
        warned = any("tab" in str(w.message).lower() for w in caught)
        assert built or warned, (
            "tabs() under layout(auto) produced neither a tab widget nor a "
            "warning — the option was accepted and discarded"
        )

    def test_no_graph_is_lost_when_tabs_are_used(self):
        out, dr = _render(_THREE, "auto", tabs="Group: s1 s2")
        assert set(dr.figures) == {"s1", "s2", "s3"}, sorted(dr.figures)
        for name, fig in dr.figures.items():
            assert fig.id in out, f"{name} vanished when tabs() was used"


# ======================================================================
# Defect 4 — tab label casing
# ======================================================================

class TestTabLabelsKeepTheirCasing:

    @pytest.mark.parametrize("label", [
        "MPG stuff", "R&D panel", "iPhone sales", "a lower case tab",
    ])
    def test_the_users_text_is_used_verbatim(self, label):
        import html as _h
        out, _ = _render(_THREE, "bs", tabs=f"{label}: s1 s2")
        # The label reaches the document through Bokeh's JSON serialisation,
        # which escapes it; compare against the escaped form rather than
        # weakening the assertion.
        assert label in out or _h.escape(label) in out, (
            f"the tab label was rewritten; neither {label!r} nor its escaped "
            f"form appears in the output"
        )

    def test_title_casing_is_not_applied(self):
        out, _ = _render(_THREE, "bs", tabs="MPG stuff: s1 s2")
        assert "Mpg Stuff" not in out, (
            "the label was force-title-cased, which mangles an acronym"
        )


# ======================================================================
# Defect 5 — linked-brush dimming
# ======================================================================

class TestLinkedBrushDimming:
    """_NONSELECTION_ALPHA has never shipped."""

    def test_the_constant_exists_in_exactly_one_place(self):
        """A structural guard, deliberately: ONE definition of the dimming
        constant.  Two equal copies draw the same page, so no drawing can
        show a second one until the two drift."""
        src = open(os.path.join(_HERE, "..", "dash_render.py")).read()
        code = "\n".join(l.split("#", 1)[0] for l in src.splitlines())
        assert code.count("_NONSELECTION_ALPHA =") == 1, (
            "the dimming constant is defined more than once, so the two "
            "copies can drift"
        )

    def test_a_linked_graphs_glyphs_dim_when_not_selected(self):
        _, dr = _render([_g("a"), _g("b")], "auto", link="a b")
        dimmed = []
        for fig in dr.figures.values():
            for r in fig.renderers:
                g = getattr(r, "nonselection_glyph", None)
                if g is not None and getattr(g, "fill_alpha", None) is not None:
                    dimmed.append(float(g.fill_alpha))
        assert dimmed, (
            "no renderer on a linked dashboard has a nonselection glyph, so "
            "brushing one graph cannot dim the other"
        )
        assert all(a == pytest.approx(dash_render._NONSELECTION_ALPHA)
                   for a in dimmed), dimmed

    def test_it_ships_through_render_not_only_through_the_helper(self):
        """The whole point: render() is the path users reach.

        Bokeh gives every renderer a nonselection_glyph of its own, so merely
        asserting one exists passes today and proves nothing. The ALPHA is
        what has never shipped.
        """
        _, dr = _render([_g("a"), _g("b")], "auto", link="a b")
        alphas = [
            float(g.fill_alpha)
            for fig in dr.figures.values() for r in fig.renderers
            if (g := getattr(r, "nonselection_glyph", None)) is not None
            and getattr(g, "fill_alpha", None) is not None
        ]
        assert alphas, "no renderer carries a nonselection glyph at all"
        assert any(a == pytest.approx(dash_render._NONSELECTION_ALPHA)
                   for a in alphas), (
            f"render() left the nonselection alphas at {sorted(set(alphas))}; "
            f"the dimming constant {dash_render._NONSELECTION_ALPHA} has "
            f"never shipped"
        )


# ======================================================================
# Defect 6 — one implementation, not two
# ======================================================================

class TestThereIsOneRenderPath:
    """The property the plan is after, stated as a property.

    Deleting ``_setup_sources``/``_build_figures`` is one way to reach it.
    Making ``render()`` use them is another, and it keeps the figures
    reachable from the ~90 test call sites that need them.
    """

    def test_render_and_build_figures_produce_the_same_sources(self):
        spec_graphs = [_g("a"), _g("b"), _g("c")]
        _, dr = _render(spec_graphs, "auto", link="_all")
        via_render = {k: id(v) for k, v in dr.sources.items()}

        _, dr2 = _render(spec_graphs, "auto", link="_all")
        dr2.sources = {}
        dr2.figures = {}
        dr2._build_figures()
        via_helper = {k: id(v) for k, v in dr2.sources.items()}

        assert set(via_render) == set(via_helper), (
            f"the two paths register different graphs: "
            f"{sorted(via_render)} vs {sorted(via_helper)}"
        )
        assert (len(set(via_render.values()))
                == len(set(via_helper.values()))), (
            "the two paths disagree on how many distinct sources exist — "
            "which is exactly how link(_all) came to work in one and not "
            "the other"
        )

    def test_both_paths_expand_link_all(self):
        _, dr = _render([_g("a"), _g("b")], "auto", link="_all")
        assert id(dr.sources["a"]) == id(dr.sources["b"]), (
            "render() does not expand _all"
        )

    def test_both_paths_apply_nonselection_alpha(self):
        _, dr = _render([_g("a"), _g("b")], "auto", link="_all")
        alphas = [
            float(g.fill_alpha)
            for fig in dr.figures.values() for r in fig.renderers
            if (g := getattr(r, "nonselection_glyph", None)) is not None
            and getattr(g, "fill_alpha", None) is not None
        ]
        assert any(a == pytest.approx(dash_render._NONSELECTION_ALPHA)
                   for a in alphas), (
            "render() does not apply the dimming the helper applies"
        )

    def test_the_helpers_are_not_a_second_implementation(self):
        """Whichever resolution is chosen, they must not duplicate logic."""
        import inspect
        setup = inspect.getsource(DashRenderer._setup_sources)
        build = inspect.getsource(DashRenderer._build_figures)
        render = inspect.getsource(DashRenderer.render)
        # The one implementation, which all three call.  It was not in the
        # scan, so the marker was found nowhere (n == 0, measured
        # 24sep2026) and a second copy grown in any ONE of the three
        # passed `n <= 1'.
        one = inspect.getsource(DashRenderer._build_sources_and_figures)
        for s, who in ((setup, "_setup_sources"), (build, "_build_figures"),
                       (render, "render")):
            assert ("self._build_sources_and_figures(" in s
                    or "self._setup_sources()" in s), (
                f"{who}() no longer goes through the one implementation")
        # A duplicated implementation shows up as the same distinctive
        # expression appearing in both.
        marker = "linked_source = self._make_source"
        n = sum(marker in s for s in (setup, build, render, one))
        assert marker in one and n == 1, (
            f"{n} of render()/_setup_sources()/_build_figures()/"
            f"_build_sources_and_figures() build a linked source of their "
            f"own; there must be one implementation"
        )


# ======================================================================
# A tab that holds a faceted graph
# ======================================================================

class TestTabsHoldFacetedGraphs:
    """``tabs()`` and ``by()`` destroyed each other under ``layout(bs)``.

    Found by running the shipped examples end to end:
    ``examples/comprehensive_demo.do`` aborted with

        dash: the following graph(s) were built but never placed in the
        dashboard: m10, m7, m8, m9, u5

    and all five of those graphs carry ``by(foreign)``. Before the
    "no graph vanishes" guard existed this was silent — five panels simply
    absent from the dashboard, rc 0.

    The cause is one set used in two different name spaces.
    ``_build_tabs_widget`` puts the *registered* name (``"faceted"``) into the
    set it returns, and the Bootstrap caller then uses that same set as if it
    held *figure keys* (``"faceted__by__0"``, ``"faceted__by__1"``) — both to
    seed ``_placed_figs`` and to filter the grid with ``k not in
    tabbed_names``. The registered name matches neither facet key, so the
    panels were placed in the tab widget and recorded nowhere.

    ``layout(auto)`` was unaffected, which is why this survived: the two
    layouts disagreed and only one of them was checked.
    """

    @staticmethod
    def _tabbed(layout, *, by="foreign"):
        graphs = [
            _g("plain", title="Plain graph"),
            _g("faceted", by=by, title="Faceted graph"),
        ]
        return _render(graphs, layout,
                       tabs="one: plain / two: faceted",
                       value_labels=_LABELS, value_label_names=_LABEL_NAMES)

    @pytest.mark.parametrize("layout", ["auto", "bs"])
    def test_a_faceted_graph_in_a_tab_does_not_vanish(self, layout):
        out, dr = self._tabbed(layout)
        assert "Faceted graph" in out, (
            f"layout({layout}): the faceted graph was dropped from the tab"
        )

    @pytest.mark.parametrize("layout", ["auto", "bs"])
    @pytest.mark.parametrize("label", ["Domestic", "Foreign"])
    def test_both_facet_panels_are_in_the_tab(self, layout, label):
        out, _ = self._tabbed(layout)
        assert label in out, f"layout({layout}): facet panel {label!r} missing"

    @pytest.mark.parametrize("layout", ["auto", "bs"])
    def test_every_figure_reaches_the_document(self, layout):
        out, dr = self._tabbed(layout)
        assert set(dr.figures) == {"plain", "faceted__by__0",
                                   "faceted__by__1"}, sorted(dr.figures)
        for name, fig in dr.figures.items():
            assert fig.id in out, (
                f"layout({layout}): figure {name!r} was built but never "
                f"placed"
            )

    def test_the_widget_reports_the_figure_keys_it_placed(self):
        """The fix, at the level the defect lives.

        The caller needs figure keys; the grid filter needs registered names.
        One set cannot be both, so the builder returns both.
        """
        _, dr = self._tabbed("bs")
        spec = dr._parse_tabs_option("one: plain / two: faceted",
                                     ["plain", "faceted"])
        widget, placed_names, placed_keys = dr._build_tabs_widget(spec)
        assert widget is not None
        assert placed_names == {"plain", "faceted"}, placed_names
        assert placed_keys == {"plain", "faceted__by__0", "faceted__by__1"}, (
            f"the widget must report the FIGURE KEYS it consumed, not the "
            f"registered names: {placed_keys}"
        )

    def test_a_plain_graph_in_a_tab_still_works(self):
        """The fix must not change the ordinary case."""
        out, dr = self._tabbed("bs")
        assert "Plain graph" in out

    def test_a_tabbed_graph_is_not_also_drawn_in_the_grid(self):
        """It is placed once, in the tab — not twice."""
        # Counted in the page's layouts: `out.count(fig.id) >= 1' held for a
        # figure placed twice as well.
        out, dr = self._tabbed("bs")
        assert set(dr.figures) == {"plain", "faceted__by__0",
                                   "faceted__by__1"}, sorted(dr.figures)
        placed = _placements(out)
        for name, fig in dr.figures.items():
            assert out.count(fig.id) >= 1, name
            assert placed.get(fig.id) == 1, (
                f"{name} is placed {placed.get(fig.id, 0)} times")
        # ...and that one place is the tab.
        tabs = [t for d in _page_docs(out) for t in d.select({"type": Tabs})]
        assert len(tabs) == 1
        # Flipped (WP-30 P1.15a): the by() grid's chrome cells (Plots that
        # hold its overall text) are in the tab too and are not figures.
        from by_panel_probe import is_chrome
        in_tabs = {m.id for m in tabs[0].select({"type": Plot})
                   if not is_chrome(m)}
        assert in_tabs == {f.id for f in dr.figures.values()}, in_tabs


# ======================================================================
# tabs() and filterposition() under the DEFAULT layout
# ======================================================================

def _normalise(html_text):
    """Strip Bokeh's per-render ids, and the CSP's script hashes that are
    computed over them (WP-30 P1.29), so two documents can be compared."""
    html_text = re.sub(r"'sha256-[A-Za-z0-9+/]{43}='", "'HASH'", html_text)
    out = re.sub(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        "U", html_text)
    return re.sub(r"\bp\d{3,6}\b", "P", out)


class TestTabsWorkUnderEveryLayout:
    """``tabs()`` was Bootstrap-only, and said nothing about it.

    Measured: with ``layout(auto)`` — the **default** — the rendered document
    is byte-identical with and without ``tabs()`` once Bokeh's per-render ids
    are normalised. The option was parsed, validated against the registry,
    carried all the way into Python and then dropped, with no warning and
    rc 0.

    ``_build_tabs_widget`` returns an ordinary Bokeh ``Tabs``; nothing about
    it is Bootstrap-specific, so the plain path can hold it too.
    """

    @pytest.mark.parametrize("layout", ["auto", "bs", "2 1"])
    def test_tabs_change_the_document(self, layout):
        without, _ = _render(_THREE, layout)
        with_tabs, _ = _render(_THREE, layout,
                               tabs="One: s1 / Two: s2 s3")
        assert _normalise(without) != _normalise(with_tabs), (
            f"layout({layout}): tabs() changed nothing at all"
        )

    @pytest.mark.parametrize("layout", ["auto", "bs", "2 1"])
    def test_a_tabs_model_is_emitted(self, layout):
        out, _ = _render(_THREE, layout, tabs="One: s1 / Two: s2 s3")
        assert '"type":"Tabs"' in out or '"name":"Tabs"' in out, (
            f"layout({layout}): no Tabs model reached the document"
        )

    @pytest.mark.parametrize("layout", ["auto", "bs", "2 1"])
    def test_the_tab_titles_reach_the_document(self, layout):
        out, _ = _render(_THREE, layout, tabs="Alpha: s1 / Beta: s2 s3")
        # The titles of the page's Tabs model, read from its document.  The
        # words in the page text are no witness: both are in the inlined
        # BokehJS of every page, under auto, bs and "2 1" alike, tabs() or
        # not (measured 24sep2026), so `"Alpha" in out and "Beta" in out',
        # which stood here, could not fail and is gone.
        assert _tab_titles(out) == ["Alpha", "Beta"], layout

    @pytest.mark.parametrize("layout", ["auto", "bs", "2 1"])
    def test_every_graph_still_reaches_the_document(self, layout):
        out, dr = _render(_THREE, layout, tabs="One: s1 / Two: s2 s3")
        assert set(dr.figures) == {"s1", "s2", "s3"}, sorted(dr.figures)
        for name, fig in dr.figures.items():
            assert fig.id in out, (
                f"layout({layout}): figure {name!r} vanished once it was "
                f"put in a tab"
            )

    def test_a_graph_left_out_of_every_tab_is_still_drawn(self):
        """Naming two of three graphs must not lose the third."""
        out, dr = _render(_THREE, "auto", tabs="Only: s1")
        assert set(dr.figures) == {"s1", "s2", "s3"}, sorted(dr.figures)
        for name, fig in dr.figures.items():
            assert fig.id in out, name

    def test_no_tabs_option_leaves_the_document_unchanged(self):
        """The fix must not alter an ordinary dashboard."""
        a, _ = _render(_THREE, "auto")
        b, _ = _render(_THREE, "auto")
        assert _normalise(a) == _normalise(b)


class TestFilterPositionWorksUnderEveryLayout:
    """``filterposition(left)`` was Bootstrap-only, and said nothing.

    Measured: with ``layout(auto)`` the document is identical for
    ``filterposition(top)`` and ``filterposition(left)``.
    """

    _F = [{"varname": "foreign", "type": "dropdown", "exclude": [],
           "label": ""}]

    @staticmethod
    def _go(layout, pos):
        spec_extra = {"filters": TestFilterPositionWorksUnderEveryLayout._F,
                      "filter_position": pos}
        return _render(_THREE, layout, build_extra=spec_extra)

    @pytest.mark.parametrize("layout", ["auto", "bs"])
    def test_left_differs_from_top(self, layout):
        top, _ = self._go(layout, "top")
        left, _ = self._go(layout, "left")
        assert _normalise(top) != _normalise(left), (
            f"layout({layout}): filterposition(left) changed nothing"
        )

    @pytest.mark.parametrize("layout", ["auto", "bs"])
    def test_the_filter_widget_is_still_built(self, layout):
        _, dr = self._go(layout, "left")
        assert dr.filter_widgets, layout

    @pytest.mark.parametrize("layout", ["auto", "bs"])
    def test_every_graph_still_reaches_the_document(self, layout):
        out, dr = self._go(layout, "left")
        assert set(dr.figures) == {"s1", "s2", "s3"}, sorted(dr.figures)
        for name, fig in dr.figures.items():
            assert fig.id in out, f"layout({layout}): {name}"
