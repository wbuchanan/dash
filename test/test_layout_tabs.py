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
import json
import os
import re
import sys
import tempfile

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render
from dash_render import DashRenderer

from conftest import make_spec, make_data_json


def _df(n=30):
    return pd.DataFrame({
        "mpg": np.linspace(12.0, 41.0, n),
        "weight": np.linspace(1760.0, 4840.0, n),
        "price": np.linspace(3291.0, 15906.0, n),
        "foreign": np.array([0.0, 1.0] * (n // 2)),
    })


def _g(name, *, title=""):
    return {
        "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                   "options": {}}],
        "graph_options": dict({"name": name},
                              **({"title": title} if title else {})),
        "if_expr": "", "in_expr": "",
    }


def _render(graphs, layout, *, tabs="", link=""):
    spec = make_spec(graphs[0]["plots"])
    spec["graphs"] = graphs
    spec["build_options"]["layout"] = layout
    spec["build_options"]["link"] = link
    spec["build_options"]["registry"] = " ".join(
        g["graph_options"]["name"] for g in graphs)
    if tabs:
        spec["build_options"]["tabs"] = tabs
    sp = tempfile.mkstemp(".json")[1]
    dp = tempfile.mkstemp(".json")[1]
    op = tempfile.mkstemp(".html")[1]
    with open(sp, "w") as f:
        json.dump(spec, f)
    with open(dp, "w") as f:
        json.dump(make_data_json(_df()), f)
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
        for name, fig in dr.figures.items():
            assert fig.id in out, (
                f"{name} was omitted from the placement spec and then "
                f"dropped from the dashboard entirely"
            )

    def test_the_ordinary_two_number_form_still_works(self):
        _, dr = _render(_THREE, "auto")
        assert dr._compute_grid(3, "1 3") == (1, 3)

    def test_auto_still_works(self):
        _, dr = _render(_THREE, "auto")
        rows, cols = dr._compute_grid(4, "auto")
        assert rows >= 1 and cols >= 1


# ======================================================================
# Defect 3 — tabs() outside Bootstrap
# ======================================================================

class TestTabsAreNotSilentlyConditional:

    def test_tabs_under_bootstrap_build_a_widget(self):
        """The control."""
        out, dr = _render(_THREE, "bs", tabs="Group: s1 s2")
        assert "Group" in out

    def test_tabs_under_auto_are_not_silently_discarded(self):
        """Either build them or say why — never drop them in silence."""
        import warnings
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            out, dr = _render(_THREE, "auto", tabs="Group: s1 s2")
        built = "Group" in out
        warned = any("tab" in str(w.message).lower() for w in caught)
        assert built or warned, (
            "tabs() under layout(auto) produced neither a tab widget nor a "
            "warning — the option was accepted and discarded"
        )

    def test_no_graph_is_lost_when_tabs_are_used(self):
        out, dr = _render(_THREE, "auto", tabs="Group: s1 s2")
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
        # A duplicated implementation shows up as the same distinctive
        # expression appearing in both.
        marker = "linked_source = self._make_source"
        n = sum(marker in s for s in (setup, build, render))
        assert n <= 1, (
            f"{n} of render()/_setup_sources()/_build_figures() build a "
            f"linked source of their own; there must be one implementation"
        )
