"""test_layout_facets.py — S12: layout(bs) drops faceted graphs entirely.

The package's two headline features destroy each other. Measured on two
dashboards identical except for ``layout()``:

    marker in the generated HTML        layout(bs)   layout(auto)
    the by-graph's title                ABSENT       present
    the ordinary graph's title          present      present
    facet labels Domestic / Foreign     ABSENT       present

The Bootstrap grid resolves a registered name with ``name in self.figures``,
but a faceted graph is stored under generated keys ``name__by__0``,
``name__by__1``, ... so the lookup misses and the graph is **dropped from the
dashboard**, with no error and no warning.

``_build_tabs_widget`` already resolves this correctly — it consults
``self._facet_map`` first — which is both the model for the fix and the reason
the defect survived: one of the two resolvers was right.

These tests assert on the **rendered HTML**, not on ``self.figures``. The
figures exist; it is the layout that omits them, so a test against the internal
dict passes today and proves nothing. That distinction is how the defect
stayed hidden.

The general guard matters more than the specific fix: defect 1 is one instance
of a class, so ``TestNoGraphVanishes`` asserts that every registered graph
reaches the output under every layout.
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


def _df(n=40):
    return pd.DataFrame({
        "mpg": np.linspace(12.0, 41.0, n),
        "weight": np.linspace(1760.0, 4840.0, n),
        "foreign": np.array([0.0, 1.0] * (n // 2)),
    })


def _scatter(name, *, by="", title=""):
    gopts = {"name": name}
    if by:
        gopts["by"] = by
    if title:
        gopts["title"] = title
    return {
        "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                   "options": {}}],
        "graph_options": gopts,
        "if_expr": "",
        "in_expr": "",
    }


def _render(graphs, layout, *, kpis=None, value_labels=None,
            value_label_names=None):
    spec = make_spec(graphs[0]["plots"])
    spec["graphs"] = graphs
    spec["build_options"]["layout"] = layout
    spec["build_options"]["registry"] = " ".join(
        g["graph_options"]["name"] for g in graphs)
    if kpis:
        spec["kpis"] = kpis
        spec["build_options"]["registry"] = " ".join(
            [k["name"] for k in kpis]
            + [g["graph_options"]["name"] for g in graphs])
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


_LABELS = {"origin": {"0": "Domestic", "1": "Foreign"}}
_LABEL_NAMES = {"foreign": "origin"}


def _two_graphs():
    return [
        _scatter("plain", title="Plain graph"),
        _scatter("faceted", by="foreign", title="Faceted graph"),
    ]


#: The figures _two_graphs() builds: the plain graph, and the by(foreign)
#: graph's two panels.
_FIGURE_KEYS = ["faceted__by__0", "faceted__by__1", "plain"]


# ======================================================================
# The blocker
# ======================================================================

class TestFacetedGraphSurvivesEveryLayout:
    """The measurement that found the defect, encoded."""

    @pytest.mark.parametrize("layout", ["auto", "bs"])
    def test_the_plain_graphs_title_is_present(self, layout):
        """The control — this has always worked in both layouts."""
        out, _ = _render(_two_graphs(), layout,
                         value_labels=_LABELS,
                         value_label_names=_LABEL_NAMES)
        assert "Plain graph" in out, layout

    @pytest.mark.parametrize("layout", ["auto", "bs"])
    def test_the_faceted_graphs_title_is_present(self, layout):
        out, _ = _render(_two_graphs(), layout,
                         value_labels=_LABELS,
                         value_label_names=_LABEL_NAMES)
        assert "Faceted graph" in out, (
            f"layout({layout}): the faceted graph was dropped from the "
            f"dashboard, with no error and no warning"
        )

    @pytest.mark.parametrize("layout", ["auto", "bs"])
    @pytest.mark.parametrize("label", ["Domestic", "Foreign"])
    def test_every_facet_label_is_present(self, layout, label):
        out, _ = _render(_two_graphs(), layout,
                         value_labels=_LABELS,
                         value_label_names=_LABEL_NAMES)
        assert label in out, (
            f"layout({layout}): facet panel {label!r} is missing"
        )

    @pytest.mark.parametrize("layout", ["auto", "bs"])
    def test_both_facet_panels_reach_the_document(self, layout):
        """Not just the labels — the panels themselves."""
        out, dr = _render(_two_graphs(), layout,
                          value_labels=_LABELS,
                          value_label_names=_LABEL_NAMES)
        keys = [k for k in dr.figures if k.startswith("faceted__by__")]
        assert len(keys) == 2, f"expected two facet panels, got {keys}"
        ids = [dr.figures[k].id for k in keys]
        for fid in ids:
            assert fid in out, (
                f"layout({layout}): facet panel {fid} was built but never "
                f"placed in the document"
            )

    def test_a_faceted_graph_honours_an_explicit_bootstrap_span(self):
        out, dr = _render(_two_graphs(), "bs: plain=6 faceted=6",
                          value_labels=_LABELS,
                          value_label_names=_LABEL_NAMES)
        assert "Faceted graph" in out
        cells = re.findall(r'class="(db-col-12[^"]*)"', out)
        assert cells, "no Bootstrap cells were emitted"
        assert any("db-col-lg-6" in c for c in cells), cells[:4]
        # The plain graph's cell is lg-6 as well, so the line above never
        # read the faceted one.  Two cells, told apart by what each embeds:
        # the plain figure's, and the faceted graph's sub-grid.
        by_root = dict((root, cls.split()) for cls, root in re.findall(
            r'class="(db-col-12[^"]*)"><div id="[^"]*" data-root-id="([^"]+)"',
            out))
        plain = dr.figures["plain"].id
        assert len(by_root) == 2 and plain in by_root, by_root
        [faceted] = [r for r in by_root if r != plain]
        assert "db-col-lg-6" in by_root[plain], by_root
        assert "db-col-lg-6" in by_root[faceted], (
            f"the faceted graph's cell is {by_root[faceted]}")

    def test_a_faceted_graph_alone_under_bootstrap(self):
        """No plain graph to mask the omission."""
        out, _ = _render([_scatter("solo", by="foreign", title="Only graph")],
                         "bs", value_labels=_LABELS,
                         value_label_names=_LABEL_NAMES)
        assert "Only graph" in out
        assert "Domestic" in out and "Foreign" in out


# ======================================================================
# The guard that makes the class of defect impossible
# ======================================================================

class TestNoGraphVanishes:
    """Defect 1 is one instance of a class. This is the fix that matters."""

    @pytest.mark.parametrize("layout", [
        "auto", "bs", "1 2", "bs: plain=6 faceted=6",
    ])
    def test_every_registered_graph_reaches_the_document(self, layout):
        out, dr = _render(_two_graphs(), layout,
                          value_labels=_LABELS,
                          value_label_names=_LABEL_NAMES)
        # The loop reads the figures that were built: one never built
        # passed it.  Every registered graph is built, the by() graph as
        # its two panels.
        assert sorted(dr.figures) == _FIGURE_KEYS, sorted(dr.figures)
        for name, fig in dr.figures.items():
            assert fig.id in out, (
                f"layout({layout}): figure {name!r} was built but never "
                f"placed in the document"
            )

    def test_a_graph_omitted_from_the_spec_is_appended_not_dropped(self):
        """The documented contract: an unmentioned name gets its own row.

        So an explicit spec cannot be used to provoke the guard — which is
        the right design, and why the guard is exercised directly below.
        """
        out, dr = _render(_two_graphs(), "bs: plain=12",
                          value_labels=_LABELS, value_label_names=_LABEL_NAMES)
        assert "Faceted graph" in out
        assert sorted(dr.figures) == _FIGURE_KEYS, sorted(dr.figures)
        for name, fig in dr.figures.items():
            assert fig.id in out, name

    def test_the_guard_fires_when_a_figure_is_genuinely_unplaced(self):
        """Silence is what let the blocker survive; the guard must speak."""
        _, dr = _render(_two_graphs(), "bs",
                        value_labels=_LABELS, value_label_names=_LABEL_NAMES)
        assert dr.figures, "no figures were built"
        with pytest.raises(ValueError) as exc:
            dr._assert_every_graph_was_placed(set())
        assert "never placed" in str(exc.value)

    def test_the_guard_reports_the_registered_name_not_the_facet_key(self):
        """A user searching for "faceted__by__0" in their do-file finds
        nothing; the message must name what they wrote."""
        _, dr = _render(_two_graphs(), "bs",
                        value_labels=_LABELS, value_label_names=_LABEL_NAMES)
        with pytest.raises(ValueError) as exc:
            dr._assert_every_graph_was_placed({"plain"})
        msg = str(exc.value)
        assert "faceted" in msg, msg
        assert "__by__" not in msg, (
            f"the message leaks the generated facet key: {msg}"
        )

    def test_the_guard_names_every_missing_graph(self):
        graphs = _two_graphs() + [_scatter("third", title="Third graph")]
        _, dr = _render(graphs, "bs",
                        value_labels=_LABELS, value_label_names=_LABEL_NAMES)
        with pytest.raises(ValueError) as exc:
            dr._assert_every_graph_was_placed({"plain"})
        msg = str(exc.value)
        assert "faceted" in msg and "third" in msg, msg

    def test_the_guard_is_silent_when_everything_was_placed(self):
        """Silent means both: nothing raised and nothing said.  The two
        tests above are the control -- the same guard, a graph short,
        raises."""
        import warnings
        _, dr = _render(_two_graphs(), "bs",
                        value_labels=_LABELS, value_label_names=_LABEL_NAMES)
        assert len(dr.figures) > 1, "a faceted dashboard with one figure"
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            got = dr._assert_every_graph_was_placed(set(dr.figures))
        assert got is None
        assert not caught, [str(w.message) for w in caught]


# ======================================================================
# Both resolvers must agree
# ======================================================================

class TestFacetResolutionIsSharedNotDuplicated:
    """Two implementations of one lookup is how this diverged."""

    def test_a_single_helper_resolves_a_name_to_its_panels(self):
        import inspect
        src = inspect.getsource(dash_render)
        assert "_resolve_layout_names" in src, (
            "there is no single name->panels resolver, so the Bootstrap path "
            "and the tabs path each have their own"
        )

    def test_the_resolver_expands_a_faceted_name(self):
        _, dr = _render(_two_graphs(), "bs",
                        value_labels=_LABELS, value_label_names=_LABEL_NAMES)
        got = dr._resolve_layout_names("faceted")
        assert got == ["faceted__by__0", "faceted__by__1"], got

    def test_the_resolver_passes_a_plain_name_through(self):
        _, dr = _render(_two_graphs(), "bs",
                        value_labels=_LABELS, value_label_names=_LABEL_NAMES)
        assert dr._resolve_layout_names("plain") == ["plain"]

    def test_the_resolver_returns_nothing_for_an_unknown_name(self):
        _, dr = _render(_two_graphs(), "bs",
                        value_labels=_LABELS, value_label_names=_LABEL_NAMES)
        assert dr._resolve_layout_names("nosuchgraph") == []
