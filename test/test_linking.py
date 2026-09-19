"""
test_linking.py
Unit tests for DashRenderer linked brushing via shared ColumnDataSource.

Tests: P1B-36 through P1B-40

Run with:  pytest test/test_linking.py -v
"""
import sys
import os
import json
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dash_render import DashRenderer
from bokeh.models import ColumnDataSource


# ================================================================
# Helpers (reused from test_layout.py pattern)
# ================================================================

def _make_graph_spec(name: str) -> dict:
    return {
        "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}],
        "graph_options": {"name": name},
        "if_expr": "",
        "in_expr": "",
    }


def _make_data_json(n: int = 20) -> dict:
    rows = [{"mpg": float(i), "weight": float(i * 50)} for i in range(1, n + 1)]
    return {
        "StataJSON": {
            "variableNames": ["mpg", "weight"],
            "variableLabels": {"mpg": "Mileage (mpg)", "weight": "Weight (lbs.)"},
            "valueLabels": {},
            "valueLabelNames": {},
            "variableTypeIsString": {"mpg": False, "weight": False},
            "values": rows,
        }
    }


def _make_renderer(graph_names: list[str], link: str = "") -> DashRenderer:
    graphs   = [_make_graph_spec(n) for n in graph_names]
    registry = " ".join(graph_names)
    master   = {
        "graphs": graphs,
        "kpis":   [],
        "build_options": {
            "layout":   "auto",
            "link":     link,
            "filter":   "",
            "theme":    "default",
            "title":    "",
            "subtitle": "",
            "registry": registry,
        },
    }
    data = _make_data_json()

    import tempfile
    spec_fd, spec_path = tempfile.mkstemp(suffix=".json")
    data_fd, data_path = tempfile.mkstemp(suffix=".json")
    out_fd,  out_path  = tempfile.mkstemp(suffix=".html")

    try:
        with os.fdopen(spec_fd, "w") as f:
            json.dump(master, f)
        with os.fdopen(data_fd, "w") as f:
            json.dump(data, f)
        os.close(out_fd)
        renderer = DashRenderer(spec_path, data_path, out_path)
    finally:
        # DashRenderer reads both files in __init__; safe to clean up now
        for _p in (spec_path, data_path, out_path):
            try:
                os.unlink(_p)
            except OSError:
                pass

    return renderer


# ================================================================
# P1B-36 — graphs in link() share the exact same ColumnDataSource
# ================================================================
class TestLinkedBrushing:
    def test_linked_graphs_share_cds(self):
        """P1B-36: graphs in link() share exact same ColumnDataSource object."""
        renderer = _make_renderer(["s1", "s2", "s3"], link="s1 s2")
        sources  = renderer._setup_sources()
        # s1 and s2 should be the identical object
        assert sources["s1"] is sources["s2"], (
            "s1 and s2 should share the same ColumnDataSource"
        )

    def test_linked_graphs_all_point_to_same_cds(self):
        """P1B-36: all three linked graphs share one CDS."""
        renderer = _make_renderer(["a", "b", "c"], link="a b c")
        sources  = renderer._setup_sources()
        assert sources["a"] is sources["b"]
        assert sources["b"] is sources["c"]

    # ----------------------------------------------------------------
    # P1B-37 — graphs NOT in link() have distinct ColumnDataSource objects
    # ----------------------------------------------------------------
    def test_non_linked_graph_has_own_cds(self):
        """P1B-37: graph not in link() group has its own independent CDS."""
        renderer = _make_renderer(["s1", "s2", "s3"], link="s1 s2")
        sources  = renderer._setup_sources()
        # s3 is not linked — must be a different object from s1/s2
        assert sources["s3"] is not sources["s1"], (
            "Non-linked graph s3 should have its own CDS"
        )

    def test_no_link_all_independent(self):
        """P1B-37: without link(), all three graphs have distinct CDS objects."""
        renderer = _make_renderer(["x", "y", "z"], link="")
        sources  = renderer._setup_sources()
        assert sources["x"] is not sources["y"]
        assert sources["y"] is not sources["z"]
        assert sources["x"] is not sources["z"]

    # ----------------------------------------------------------------
    # P1B-38 — link(_all) → all figures share one ColumnDataSource
    # ----------------------------------------------------------------
    def test_link_all_shares_one_cds(self):
        """P1B-38: link('_all') makes all graphs share one CDS."""
        renderer = _make_renderer(["p", "q", "r"], link="_all")
        sources  = renderer._setup_sources()
        assert sources["p"] is sources["q"]
        assert sources["q"] is sources["r"]

    # ----------------------------------------------------------------
    # P1B-39 — nonselection_alpha=0.15 on renderers in linked figures
    # ----------------------------------------------------------------
    def test_linked_renderers_have_nonselection_alpha(self):
        """P1B-39: glyph renderers in linked figures have nonselection_alpha=0.15."""
        renderer = _make_renderer(["s1", "s2"], link="s1 s2")
        figs = renderer._build_figures()
        sources = renderer._setup_sources()

        # Rebuild with shared source
        for name in ["s1", "s2"]:
            fig = figs[name]
            for r in fig.renderers:
                if hasattr(r, "nonselection_glyph") and r.nonselection_glyph is not None:
                    ns_glyph = r.nonselection_glyph
                    if hasattr(ns_glyph, "fill_alpha"):
                        assert ns_glyph.fill_alpha == pytest.approx(0.15, abs=0.01), (
                            f"nonselection fill_alpha={ns_glyph.fill_alpha}, expected 0.15"
                        )

    # ----------------------------------------------------------------
    # P1B-40 — single link group enforced (no second link() group)
    # ----------------------------------------------------------------
    def test_a_semicolon_does_not_create_a_second_link_group(self):
        """dash.sthlp:295 — "Only one link group per dashboard is supported."

        This test used to contain **no assert statement at all**. Its body
        was a try/except whose except branch was ``pass`` and whose try
        branch discarded its own result, so it passed identically whether
        the renderer produced one group, four groups, or raised — the exact
        outcomes its own comment said had to be distinguished.

        Measured: ``_parse_link_and_filters`` does
        ``raw.replace(";", " ").split()``, so "a b; c d" flattens to four
        names sharing ONE ColumnDataSource. That is the documented contract,
        so it is what is asserted. (A malformed namelist never gets this far
        from Stata: ``dash.ado`` checks every word against the registry and
        exits 198 on the token carrying the semicolon.)
        """
        import tempfile
        graphs   = [_make_graph_spec(n) for n in ["a", "b", "c", "d"]]
        master   = {
            "graphs": graphs,
            "kpis":   [],
            "build_options": {
                "layout":   "auto",
                "link":     "a b; c d",
                "filter":   "",
                "theme":    "default",
                "title":    "",
                "subtitle": "",
                "registry": "a b c d",
            },
        }
        data = _make_data_json()
        spec_fd, spec_path = tempfile.mkstemp(suffix=".json")
        data_fd, data_path = tempfile.mkstemp(suffix=".json")
        out_fd,  out_path  = tempfile.mkstemp(suffix=".html")
        try:
            with os.fdopen(spec_fd, "w") as f:
                json.dump(master, f)
            with os.fdopen(data_fd, "w") as f:
                json.dump(data, f)
            os.close(out_fd)
            renderer = DashRenderer(spec_path, data_path, out_path)
        finally:
            for _p in (spec_path, data_path, out_path):
                try:
                    os.unlink(_p)
                except OSError:
                    pass

        sources = renderer._setup_sources()
        assert set(sources) >= {"a", "b", "c", "d"}, sorted(sources)
        assert len({id(sources[n]) for n in ("a", "b", "c", "d")}) == 1, (
            "the semicolon created more than one link group; the documented "
            "contract is that a dashboard has exactly one"
        )
        assert sources["a"] is sources["d"], (
            "graphs on opposite sides of the semicolon must still share a "
            "source, or brushing one will not brush the other"
        )
