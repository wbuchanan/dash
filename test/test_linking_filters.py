"""test_linking_filters.py — S13: linking and filter row-masking.

Two silent defects, both of which produce a plausible-looking dashboard
showing the wrong thing.

**link(_all) produces an unlinked dashboard.** ``_all`` is expanded in exactly
two places, ``_setup_sources`` and ``_build_figures`` — and neither is on the
path ``render()`` takes. Verified by locating every expansion site:

    line 9616: inside _setup_sources
    line 9744: inside _build_figures

``render()`` derives ``link_names`` itself and never expands the token, so the
graphs get separate sources. The command returns rc 0, which is why it has
always looked implemented. A test asserting on ``rc``, or on the presence of a
source, passes today and proves nothing — so these tests assert on
**ColumnDataSource identity**.

**filter() + by() masks the wrong rows.** The generated JS computes one boolean
row-mask from the primary source's snapshot and applies it **by row index** to
every source, on the strength of this inline comment:

    // above; since all sources share the same underlying row universe this mask

They do not share one. A ``by()`` graph gets one source per facet holding only
that facet's rows, and an unlinked qualified graph gets a pre-filtered source.
Both are shorter than the primary, so ``active[i]`` for the derived source's
row *i* is the primary's row *i* — a different observation entirely.
"""
import json
import os
import shutil
import subprocess
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

_NODE = shutil.which("node")


# ======================================================================
# Fixtures
# ======================================================================

def _frame(n=40):
    """A frame where every row is identifiable from its own values.

    Only variables a graph or filter actually references reach a
    ColumnDataSource, so the row identifier has to be one of them: ``x`` is
    ``arange(n)``, unique per row, and present in every source. ``grp``
    splits the rows into two facets by parity of ``x``, so a wrongly masked
    panel is identifiable by the actual x values it ends up showing — not
    merely by having the wrong count.
    """
    return pd.DataFrame({
        "y":      np.arange(n, dtype=float) * 2.0,
        "x":      np.arange(n, dtype=float),
        "grp":    np.array([0.0, 1.0] * (n // 2)),
        "filtvar": np.arange(n, dtype=float),
    })


def _build(graphs, *, link="", filters=None, registry=None, df=None):
    df = _frame() if df is None else df
    spec = make_spec(graphs[0]["plots"])
    spec["graphs"] = graphs
    spec["build_options"]["link"] = link
    spec["build_options"]["registry"] = registry or " ".join(
        g["graph_options"]["name"] for g in graphs)
    if filters:
        spec["build_options"]["filters"] = filters
    sp = tempfile.mkstemp(".json")[1]
    dp = tempfile.mkstemp(".json")[1]
    op = tempfile.mkstemp(".html")[1]
    with open(sp, "w") as f:
        json.dump(spec, f)
    with open(dp, "w") as f:
        json.dump(make_data_json(df), f)
    dr = DashRenderer(sp, dp, op)
    dr.render()
    for p in (sp, dp, op):
        try:
            os.unlink(p)
        except OSError:
            pass
    return dr


def _graph(name, *, by="", if_expr=""):
    return {
        "plots": [{"type": "scatter", "yvar": "y", "xvar": "x",
                   "options": {}}],
        "graph_options": dict({"name": name}, **({"by": by} if by else {})),
        "if_expr": if_expr,
        "in_expr": "",
    }


# ======================================================================
# link(_all)
# ======================================================================

class TestLinkAll:
    """Assert on source IDENTITY. rc proves nothing here."""

    def test_link_all_shares_one_source_across_every_graph(self):
        dr = _build([_graph("g1"), _graph("g2"), _graph("g3")], link="_all")
        ids = {id(dr.sources[n]) for n in ("g1", "g2", "g3")}
        assert len(ids) == 1, (
            f"link(_all) produced {len(ids)} distinct ColumnDataSource "
            f"objects — the dashboard is unlinked"
        )

    def test_an_explicit_list_shares_one_source(self):
        """The control: the explicit form has always worked."""
        dr = _build([_graph("g1"), _graph("g2"), _graph("g3")],
                    link="g1 g2 g3")
        ids = {id(dr.sources[n]) for n in ("g1", "g2", "g3")}
        assert len(ids) == 1

    def test_link_all_and_an_explicit_list_are_equivalent(self):
        a = _build([_graph("g1"), _graph("g2")], link="_all")
        b = _build([_graph("g1"), _graph("g2")], link="g1 g2")
        assert (id(a.sources["g1"]) == id(a.sources["g2"])) == \
               (id(b.sources["g1"]) == id(b.sources["g2"]))

    def test_no_link_leaves_the_graphs_independent(self):
        dr = _build([_graph("g1"), _graph("g2")], link="")
        assert id(dr.sources["g1"]) != id(dr.sources["g2"])

    def test_a_partial_list_links_only_those_named(self):
        dr = _build([_graph("g1"), _graph("g2"), _graph("g3")], link="g1 g2")
        assert id(dr.sources["g1"]) == id(dr.sources["g2"])
        assert id(dr.sources["g3"]) != id(dr.sources["g1"])

    def test_the_token_is_expanded_exactly_once(self):
        """A structural guard against the expansion drifting apart again.

        It used to live in ``_setup_sources`` AND ``_build_figures``, neither
        of which ``render()`` called, so it looked implemented twice over and
        shipped in neither.  Then the saved builder and the served app each
        had one, and they disagreed: ``link(_all g2)`` linked every graph
        saved and none served (23sep2026, test_keyword_names.py).  There is
        now one implementation, ``_dash_link_names``, reached by the saved
        builder, the server builder and the generated app.
        """
        import inspect
        shared = inspect.getsource(DashRenderer._build_sources_and_figures)
        assert "_dash_link_names(" in shared, (
            "the shared source builder does not read link() by the shared "
            "rule"
        )
        src = open(os.path.join(_HERE, "..", "dash_render.py")).read()
        code = "\n".join(l.split("#", 1)[0] for l in src.splitlines())
        assert code.count('if "_all" in names') == 1, (
            "_all is expanded in more than one place, so the copies can "
            "drift apart again"
        )
        assert "== '_all'" not in code and '== "_all"' not in code
        # Defined once, called by the saved builder, the server builder,
        # the app's make_document, and _dash_embedded_cells (GAPS2 G3,
        # WP-28 section 08: which graphs link() reaches decides whether a
        # computed-only graph's rows are counted), and _dash_embed_plan
        # (WP-29 P0.11), which CALLS it -- no copy.  Flipped: 5 -> 6.
        assert code.count("_dash_link_names(") == 6


# ======================================================================
# Filter row-masking
# ======================================================================

def _callback_payload(dr):
    """The snapshots and sources the filter callback actually receives."""
    assert dr.filter_callbacks, "no filter callback was built"
    cb = dr.filter_callbacks[0]
    return {
        # The snapshot is a shared ColumnDataSource now, not a JSON string
        # serialised into every callback's args -- see
        # test_filter_payload_size.py for why.
        "primary": dict(cb.args["orig_source"].data),
        "sources": list(cb.args["all_graph_sources"]),
        "snapshots": [dict(m.data)
                      for m in cb.args["all_graph_sources_orig"]],
        "specs": json.loads(cb.args["filter_specs_json"]),
    }


def _dashboard_with_a_filter():
    """A by() graph, a qualified graph and a plain graph, plus a filter."""
    return _build(
        [
            _graph("plain"),
            _graph("faceted", by="grp"),
            _graph("qualified", if_expr="x >= 20"),
        ],
        link="",
        filters=[{"varname": "filtvar", "type": "range", "exclude": [],
                  "label": ""}],
    )


class TestSourcesDoNotShareARowUniverse:
    """The premise the JS mask rests on, checked directly."""

    def test_the_derived_sources_are_shorter_than_the_primary(self):
        dr = _dashboard_with_a_filter()
        p = _callback_payload(dr)
        n_primary = len(next(iter(p["primary"].values())))
        lengths = [len(next(iter(s.values()))) for s in p["snapshots"] if s]
        assert lengths, "no per-source snapshots reached the callback"
        assert any(n != n_primary for n in lengths), (
            f"every source is {n_primary} rows long, so this dashboard does "
            f"not exercise the defect — the test data is wrong"
        )

    def test_the_javascript_no_longer_claims_a_shared_row_universe(self):
        js = dash_render._FILTER_JS
        assert "share the same underlying row universe" not in js, (
            "the mask still rests on an assumption that is false for "
            "faceted and qualified sources"
        )

    def test_every_source_carries_a_row_identifier(self):
        """The fix: mask by identity, not by position."""
        dr = _dashboard_with_a_filter()
        p = _callback_payload(dr)
        key = dash_render._ROW_ID_COLUMN
        for i, snap in enumerate(p["snapshots"]):
            if not snap:
                continue
            assert key in snap, (
                f"source {i} carries no {key!r} column, so the callback can "
                f"only mask it by position"
            )


class TestFilterSelectsTheRightRowsInEveryPanel:
    """The behaviour, computed the way the shipped JS computes it."""

    @staticmethod
    def _expected_rows(snapshot, lo, hi):
        """Rows of this source whose filtvar falls inside [lo, hi]."""
        vals = snapshot["filtvar"]
        return [snapshot["x"][i] for i, v in enumerate(vals)
                if v is not None and lo <= v <= hi]

    @staticmethod
    def _index_masked_rows(snapshot, active):
        """What an index-based mask would keep — the defect, reproduced."""
        ids = snapshot["x"]
        return [ids[i] for i in range(len(ids))
                if i < len(active) and active[i]]

    def test_an_index_based_mask_would_pick_the_wrong_rows(self):
        """Demonstrates the defect on real snapshots, before asserting the fix.

        If this ever stops holding, the test data no longer exercises the bug
        and the assertions below would pass vacuously.
        """
        dr = _dashboard_with_a_filter()
        p = _callback_payload(dr)
        lo, hi = 10.0, 25.0
        primary = p["primary"]
        active = [lo <= v <= hi for v in primary["filtvar"]]

        disagreed = False
        for snap in p["snapshots"]:
            if not snap or len(snap["x"]) == len(primary["x"]):
                continue
            if self._index_masked_rows(snap, active) != \
                    self._expected_rows(snap, lo, hi):
                disagreed = True
        assert disagreed, (
            "an index-based mask agreed with the correct answer on every "
            "source, so this dashboard does not exercise the defect"
        )

    def test_each_source_would_keep_exactly_its_own_matching_rows(self):
        """Identity masking, applied to the snapshots the callback holds."""
        dr = _dashboard_with_a_filter()
        p = _callback_payload(dr)
        lo, hi = 10.0, 25.0
        primary = p["primary"]
        key = dash_render._ROW_ID_COLUMN
        active_ids = {
            primary[key][i] for i, v in enumerate(primary["filtvar"])
            if v is not None and lo <= v <= hi
        }
        for i, snap in enumerate(p["snapshots"]):
            if not snap:
                continue
            kept = [snap["x"][j] for j, rid in enumerate(snap[key])
                    if rid in active_ids]
            assert kept == self._expected_rows(snap, lo, hi), (
                f"source {i} would keep {kept}, but the rows of that source "
                f"matching the filter are {self._expected_rows(snap, lo, hi)}"
            )

    def test_a_faceted_panel_holds_only_its_own_facets_rows(self):
        """grp splits on the parity of x, so a facet source is all-even or
        all-odd. A panel showing both parities has been masked wrongly."""
        dr = _dashboard_with_a_filter()
        p = _callback_payload(dr)
        facet_snaps = [
            s for s in p["snapshots"]
            if s and len(s["x"]) == 20
            and len({int(v) % 2 for v in s["x"]}) == 1
        ]
        assert len(facet_snaps) == 2, (
            f"expected two single-parity facet sources, got "
            f"{len(facet_snaps)}"
        )
        key = dash_render._ROW_ID_COLUMN
        for snap in facet_snaps:
            assert key in snap, (
                f"a facet source carries no {key!r}, so it can only be "
                f"masked by position"
            )


@pytest.mark.skipif(_NODE is None, reason="node is not installed")
class TestTheShippedJavascriptMasksByIdentity:
    """Run the real callback code, not a transliteration of it."""

    def test_the_mask_loop_uses_the_row_identifier(self):
        js = dash_render._FILTER_JS
        key = dash_render._ROW_ID_COLUMN
        lo = js.index("const _srcs_orig ")
        hi = js.index("// Also update the primary", lo)
        block = js[lo:hi]
        assert key in block, (
            "the per-source mask loop does not reference the row identifier, "
            "so it is still masking by position"
        )

    def test_the_real_loop_keeps_the_right_rows(self):
        """Execute the shipped mask loop against real snapshots under node."""
        dr = _dashboard_with_a_filter()
        p = _callback_payload(dr)
        lo_v, hi_v = 10.0, 25.0
        primary = p["primary"]
        key = dash_render._ROW_ID_COLUMN
        active = [bool(v is not None and lo_v <= v <= hi_v)
                  for v in primary["filtvar"]]

        js = dash_render._FILTER_JS
        lo = js.index("const _srcs_orig ")
        hi = js.index("// Also update the primary", lo)
        block = js[lo:hi]

        snapshots = [s for s in p["snapshots"] if s]
        harness = (
            # The snapshots are MODELS now, so the stub must expose each
            # one's `.data', as a real ColumnDataSource does.
            "const all_graph_sources_orig = "
            + json.dumps([{"data": s} for s in snapshots]) + ";\n"
            + "const _srcs = all_graph_sources_orig.map(() => "
            "({data:null, selected:{indices:[]}, change:{emit:()=>{}}}));\n"
            + "const active = " + json.dumps(active) + ";\n"
            + "const new_data = " + json.dumps(primary) + ";\n"
            + "const orig = new_data;\n"
            # The CDSView rebuild needs the view list; this harness exercises
            # the row masking, so an empty list is the right stub.
            + "const view_filters = [];\n"
            + block
            + "\nprocess.stdout.write(JSON.stringify("
            "_srcs.map(s => s.data ? s.data['x'] : null)));"
        )
        with tempfile.NamedTemporaryFile("w", suffix=".mjs",
                                          delete=False) as fh:
            fh.write(harness)
            path = fh.name
        try:
            res = subprocess.run([_NODE, path], capture_output=True,
                                 text=True, timeout=60)
            assert res.returncode == 0, (
                f"the shipped mask loop failed under node:\n{res.stderr[:1500]}"
            )
            got = json.loads(res.stdout)
        finally:
            os.unlink(path)

        for snap, kept in zip(snapshots, got):
            want = [snap["x"][i] for i, v in enumerate(snap["filtvar"])
                    if v is not None and lo_v <= v <= hi_v]
            assert kept == want, (
                f"the shipped callback kept rowids {kept} where the rows of "
                f"that source matching the filter are {want}"
            )
