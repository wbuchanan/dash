"""WP-31 H2l (section 51): several link groups, brush as a filter, a brush
on histogram bins, and concurrent brushes intersected.

GAPS3 H2: "one link group; brush cannot act as a filter".  GAPS3 H1's
selection clauses: "A box or lasso selection on bars or histograms drives
nothing; concurrent brushes are not intersected on the saved page".

Measured before the fix (1557f0b): ``link(g1 g2) link(g3 g4)`` reached the
renderer as one group of four (one source); ``brush(filter)`` did not
exist; a histogram's bins carried no rows and had no selection callback;
two brushes on two sources each recomputed the cards from their own
selection alone, on the saved page and in the served app.

The node tests run the shipped selection callback -- the ``CustomJS`` the
saved renderer attaches, its own ``code`` -- against plain stand-ins for
its Bokeh arguments (``_js_cb``), as test_kpi_brush.py runs it.
"""
import importlib.util
import itertools
import json
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import ColumnDataSource, CustomJS, DataTable, IndexFilter

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
from conftest import make_data_json

_N = 12
_DF = pd.DataFrame({
    "mpg": np.linspace(12.0, 34.0, _N),
    "weight": np.linspace(1800.0, 4000.0, _N),
    "price": np.linspace(3000.0, 14000.0, _N),
})
_SEQ = itertools.count()


def _graph(name, ptype="scatter", go=None):
    p = {"type": ptype, "yvar": "mpg", "xvar": "weight", "options": {}}
    if ptype == "histogram":
        p = {"type": "histogram", "yvar": "mpg", "var": "mpg",
             "options": {"bin": "4"}}
    g = {"name": name, "graph_options": dict({"name": name}, **(go or {})),
         "plots": [p], "if_expr": "", "in_expr": ""}
    return g


def _spec(graphs, link="", brush=None, kpis=None):
    bo = {"layout": "auto", "link": link, "filter": "", "theme": "",
          "scheme": "", "session_scheme": "", "title": "", "subtitle": "",
          "registry": " ".join([g["name"] for g in graphs]
                               + [k["name"] for k in (kpis or [])]),
          "tabs": "", "filter_position": "top", "level": "95",
          "formats": {}}
    if brush is not None:
        bo["brush"] = brush
    return {"graphs": graphs, "kpis": kpis or [], "build_options": bo}


def _kpi(update="brush", name="k1"):
    return {"name": name, "stat": "mean", "var": "mpg", "title": "T",
            "fmt": "%9.4f", "update": update}


def _saved(spec, df=_DF):
    tag = next(_SEQ)
    d = tempfile.mkdtemp()
    sp, dp, op = (os.path.join(d, f"{x}_{tag}") for x in ("s.json", "d.json",
                                                           "o.html"))
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(make_data_json(df), fh)
    r = dr.DashRenderer(sp, dp, op)
    r.render()
    shutil.rmtree(d, ignore_errors=True)
    return r


def _served(spec, tmp_path, df=_DF):
    tag = next(_SEQ)
    sp, dp, ap = (tmp_path / f"{x}_{tag}.{e}" for x, e in (
        ("s", "json"), ("d", "json"), ("a", "py")))
    sp.write_text(json.dumps(spec))
    dp.write_text(json.dumps(make_data_json(df)))
    dr.ServerAppBuilder(str(sp), str(dp)).build(str(ap))
    ms = importlib.util.spec_from_file_location(f"_s51_app_{tag}", str(ap))
    mod = importlib.util.module_from_spec(ms)
    ms.loader.exec_module(mod)
    doc = Document()
    mod.make_document(doc)
    return doc, mod


def _glyph_renderers(fig):
    return [r for r in fig.renderers
            if isinstance(getattr(r, "data_source", None), ColumnDataSource)
            and getattr(r, "glyph", None) is not None]


def _served_figs(doc):
    from bokeh.plotting import figure as _f
    return [m for m in doc.select({"type": _f})]


def _brush_callbacks(r):
    """``{id(source): CustomJS}``: the saved page's selection callback on
    each source."""
    out = {}
    srcs = list(r.sources.values())
    for f in r.figures.values():
        srcs += [x.data_source for x in _glyph_renderers(f)]
    for s in srcs:
        for cbs in (s.selected.js_property_callbacks or {}).values():
            for cb in cbs:
                if isinstance(cb, CustomJS) and "brush_source" in cb.args:
                    out[id(s)] = cb
    return out


# ---------------------------------------------------------------------------
# A node harness for the shipped selection callback
# ---------------------------------------------------------------------------

_PRELUDE = r"""
const __M = {};
function __src(o) {
  return {__id: o.__id, data: o.data, tags: o.tags || [],
          selected: {indices: o.indices || []},
          get_length() { const k = Object.keys(this.data);
                         return k.length ? this.data[k[0]].length : 0; }};
}
function __build(v) {
  if (v === null || typeof v !== 'object') return v;
  if (Array.isArray(v)) return v.map(__build);
  if (v.__ref__ !== undefined) return __M[v.__ref__];
  const o = {}; for (const k of Object.keys(v)) o[k] = __build(v[k]);
  return o;
}
"""


def _plain(v):
    if isinstance(v, float) and not np.isfinite(v):
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        f = float(v)
        return f if np.isfinite(f) else None
    return v


def _encode(v, models):
    """JSON for a callback's args; each model once, by reference."""
    from bokeh.model import Model
    if isinstance(v, Model):
        if v.id not in models:
            models[v.id] = None
            if isinstance(v, ColumnDataSource):
                models[v.id] = {"kind": "src", "data": {
                    str(c): [_plain(x) for x in list(col)]
                    for c, col in v.data.items()}, "tags": list(v.tags)}
            elif isinstance(v, IndexFilter):
                models[v.id] = {"kind": "obj", "o": {
                    "indices": [int(i) for i in (v.indices or [])],
                    "tags": list(v.tags)}}
            elif isinstance(v, DataTable):
                models[v.id] = {"kind": "obj", "o": {
                    "tags": list(v.tags),
                    "source": _encode(v.source, models),
                    "view": {"filter": _encode(v.view.filter, models)}}}
            elif hasattr(v, "text"):
                models[v.id] = {"kind": "obj", "o": {"text": v.text}}
            else:
                models[v.id] = {"kind": "obj", "o": {}}
        return {"__ref__": v.id}
    if isinstance(v, dict):
        return {str(k): _encode(x, models) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_encode(x, models) for x in v]
    return _plain(v)


def _js_cb(cb, indices, *, state=None, probe=()):
    """Run *cb* (a saved brush ``CustomJS``) under node with ``cb_obj``'s
    indices; *state* seeds ``brush_state.data``.  Returns ``{"cards":
    [text...], "state": brush_state.data, "sel": {model id: indices},
    "flt": {model id: indices}}``."""
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    models = {}
    args = _encode(dict(cb.args), models)
    lines = [_PRELUDE]
    for mid, m in models.items():
        if m["kind"] == "src":
            lines.append("__M[%s] = __src(%s);" % (
                json.dumps(mid), json.dumps({"__id": mid, "data": m["data"],
                                             "tags": m["tags"]})))
        else:
            lines.append("__M[%s] = {};" % json.dumps(mid))
    for mid, m in models.items():
        if m["kind"] == "obj":
            lines.append("Object.assign(__M[%s], __build(%s));" % (
                json.dumps(mid), json.dumps(m["o"])))
    names = list(args)
    lines.append("const __A = __build(%s);" % json.dumps(args))
    if state is not None:
        lines.append("if (__A.brush_state) __A.brush_state.data = %s;"
                     % json.dumps(state))
    lines.append("const __cb = {indices: %s};" % json.dumps(list(indices)))
    lines.append("(function(%s, cb_obj) {\n%s\n})(%s, __cb);" % (
        ", ".join(names), cb.code,
        ", ".join("__A[%s]" % json.dumps(n) for n in names)))
    lines.append(r"""
const __out = {cards: [], state: null, sel: {}, flt: {}};
for (const d of (__A.kpi_divs || [])) __out.cards.push(d.text);
if (__A.brush_state) __out.state = __A.brush_state.data;
for (const k of Object.keys(__M)) {
  const m = __M[k];
  if (m && m.selected) __out.sel[k] = m.selected.indices;
  if (m && m.indices !== undefined && m.tags) __out.flt[k] = m.indices;
}
process.stdout.write(JSON.stringify(__out));
""")
    with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False,
                                     encoding="utf-8") as fh:
        fh.write("\n".join(lines))
        path = fh.name
    try:
        res = subprocess.run([node, path], capture_output=True, text=True,
                             timeout=60)
        assert res.returncode == 0, res.stderr[:3000]
        return json.loads(res.stdout)
    finally:
        os.unlink(path)


def _card_value(text):
    import re
    m = re.search(r'id="kpi_val_k\d"[^>]*>([^<]*)<', text or "")
    return float(m.group(1)) if m else None


# ---------------------------------------------------------------------------
# link groups
# ---------------------------------------------------------------------------

_FOUR = [_graph(n) for n in ("g1", "g2", "g3", "g4")]


class TestLinkGroups:
    def test_the_groups_are_read_from_the_separator(self):
        names = ["g1", "g2", "g3", "g4"]
        assert dr._dash_link_groups("g1 g2 || g3 g4", names) == [
            ["g1", "g2"], ["g3", "g4"]]
        assert dr._dash_link_groups(["g1", "g2", "||", "g3"], names) == [
            ["g1", "g2"], ["g3"]]
        assert dr._dash_link_groups("_all", names) == [names]
        assert dr._dash_link_groups("", names) == []
        # A semicolon is a blank, as older specs wrote it (one group).
        assert dr._dash_link_groups("g1;g2", names) == [["g1", "g2"]]

    def test_flat_names_are_the_union(self):
        names = ["g1", "g2", "g3", "g4"]
        assert dr._dash_link_names("g1 g2 || g3 g4", names) == [
            "g1", "g2", "g3", "g4"]
        assert dr._dash_link_names("g2 g1", names) == ["g2", "g1"]
        assert dr._dash_link_names("_all", names) == names

    def test_a_name_in_two_groups_is_refused_by_the_reader(self):
        """dash.ado refuses it; a hand-built spec keeps the first group's
        claim, with a note."""
        dr._DASH_NOTED.discard(("link-two-groups", "g2"))
        with pytest.warns(UserWarning, match="more than one link group"):
            got = dr._dash_link_groups("g1 g2 || g2 g3", ["g1", "g2", "g3"])
        assert got == [["g1", "g2"], ["g3"]]

    def test_two_groups_two_sources_saved(self):
        r = _saved(_spec(_FOUR, link="g1 g2 || g3 g4"))
        s = r.sources
        assert s["g1"] is s["g2"], "g1 and g2 do not share a source"
        assert s["g3"] is s["g4"], "g3 and g4 do not share a source"
        assert s["g1"] is not s["g3"], "g1 and g3 share one source"
        assert [r.figures[n]._dash_link_group for n in
                ("g1", "g2", "g3", "g4")] == [0, 0, 1, 1]

    def test_one_group_is_unchanged(self):
        r = _saved(_spec(_FOUR, link="g1 g2"))
        s = r.sources
        assert s["g1"] is s["g2"]
        assert s["g3"] is not s["g1"] and s["g4"] is not s["g3"]

    def test_two_groups_two_sources_served(self, tmp_path):
        doc, _ = _served(_spec(_FOUR, link="g1 g2 || g3 g4"), tmp_path)
        figs = _served_figs(doc)
        srcs = [_glyph_renderers(f)[0].data_source for f in figs]
        assert len({id(x) for x in srcs}) == 2, (
            "four graphs in two link groups drew from %d sources"
            % len({id(x) for x in srcs}))
        by = {}
        for x in srcs:
            by.setdefault(id(x), []).append(x)
        assert sorted(len(v) for v in by.values()) == [2, 2]

    def test_the_page_plan_holds_each_groups_rows(self):
        df = _DF.copy()
        graphs = [_graph("g1"), _graph("g2"), _graph("g3"), _graph("g4")]
        graphs[0]["if_expr"] = "mpg < 20"
        masks = {}
        plan = dr._dash_embed_plan(_spec(graphs), df, masks,
                                   "g1 g2 || g3 g4", [])
        assert len(plan["link_group_rows"]) == 2
        assert bool(plan["link_rows"].equals(
            plan["link_group_rows"][0] | plan["link_group_rows"][1]))


# ---------------------------------------------------------------------------
# brush(filter)
# ---------------------------------------------------------------------------

def _ns_alphas(fig):
    out = []
    for r in _glyph_renderers(fig):
        ns = getattr(r, "nonselection_glyph", None)
        if ns is not None and hasattr(ns, "fill_alpha"):
            v = ns.fill_alpha
            out.append(v if isinstance(v, (int, float)) else v.get("value"))
    return out


class TestBrushFilter:
    def test_the_mode_is_read_from_the_build_options(self):
        assert dr._dash_brush_mode({}) == "highlight"
        assert dr._dash_brush_mode({"brush": "filter"}) == "filter"
        assert dr._dash_brush_mode({"brush": "highlight"}) == "highlight"
        assert dr._dash_brush_mode({"brush": "bogus"}) == "highlight"
        assert dr._dash_brush_mode(None) == "highlight"

    def test_nonselection_alpha_is_zero_under_filter_both_modes(
            self, tmp_path):
        spec = _spec(_FOUR[:2], link="_all", brush="filter")
        r = _saved(spec)
        for n in ("g1", "g2"):
            assert _ns_alphas(r.figures[n]) and all(
                a == 0.0 for a in _ns_alphas(r.figures[n])), n
        doc, _ = _served(spec, tmp_path)
        for f in _served_figs(doc):
            assert _ns_alphas(f) and all(a == 0.0 for a in _ns_alphas(f))

    def test_highlight_default_keeps_the_alpha(self, tmp_path):
        r = _saved(_spec(_FOUR[:2], link="_all"))
        assert all(a == pytest.approx(dr._NONSELECTION_ALPHA)
                   for a in _ns_alphas(r.figures["g1"]))

    def test_every_card_follows_under_filter(self):
        """An update(filter) card follows a selection under brush(filter);
        under the default it has no selection callback at all."""
        r = _saved(_spec(_FOUR[:2], link="_all", brush="filter",
                         kpis=[_kpi("filter")]))
        cbs = _brush_callbacks(r)
        assert cbs, "brush(filter) attached no selection callback"
        cb = cbs[id(r.sources["g1"])]
        out = _js_cb(cb, [0, 1, 2])
        want = float(_DF["mpg"].iloc[[0, 1, 2]].mean())
        assert _card_value(out["cards"][0]) == pytest.approx(want, abs=1e-3)
        r2 = _saved(_spec(_FOUR[:2], link="_all", kpis=[_kpi("filter")]))
        assert not _brush_callbacks(r2)

    def test_the_view_filters_are_python_built(self):
        r = _saved(_spec(_FOUR[:2], link="_all", brush="filter"))
        cb = _brush_callbacks(r)[id(r.sources["g1"])]
        views = cb.args["brush_views"]
        assert len(views) == 2
        for flt, src in views:
            assert isinstance(flt, IndexFilter)
            assert "dash_brush_view" in flt.tags
            # None: every row, until a selection writes the kept ones.
            assert flt.indices is None
            assert src is r.sources["g1"]

    def test_the_script_mutates_indices_and_restores(self):
        r = _saved(_spec(_FOUR[:2], link="_all", brush="filter"))
        cb = _brush_callbacks(r)[id(r.sources["g1"])]
        fids = [f.id for f, _s in cb.args["brush_views"]]
        out = _js_cb(cb, [3, 5])
        assert all(out["flt"][i] == [3, 5] for i in fids), out["flt"]
        st = out["state"]
        out2 = _js_cb(cb, [], state=st)
        # Cleared: null again, every row of whatever the source now holds.
        assert all(out2["flt"][i] is None for i in fids), out2["flt"]

    def test_the_table_view_follows_a_brush(self):
        graphs = [_graph("g1", go={"table": "rows(2)"}), _graph("g2")]
        r = _saved(_spec(graphs, link="_all", brush="filter"))
        cb = _brush_callbacks(r)[id(r.sources["g1"])]
        tables = cb.args["tables"]
        assert len(tables) == 1
        tid = tables[0].view.filter.id
        out = _js_cb(cb, [1, 4, 7])
        # The table lists a copy of the graph's rows, keyed by row id: the
        # first two of the three kept (its cap).
        tsrc = tables[0].source
        ids = list(tsrc.data[dr._ROW_ID_COLUMN])
        want = [i for i, v in enumerate(ids) if v in (1, 4, 7)][:2]
        assert out["flt"][tid] == want

    def test_served_cb_recomputes_every_card(self, tmp_path):
        doc, _ = _served(_spec(_FOUR[:2], link="_all", brush="filter",
                               kpis=[_kpi("filter")]), tmp_path)
        src = _glyph_renderers(_served_figs(doc)[0])[0].data_source
        src.selected.indices = [0, 1, 2]
        from bokeh.models import Div
        texts = [d.text for d in doc.select({"type": Div})
                 if "kpi_val_k1" in (d.text or "")]
        want = float(_DF["mpg"].iloc[[0, 1, 2]].mean())
        assert texts and _card_value(texts[0]) == pytest.approx(want,
                                                                 abs=1e-3)


# ---------------------------------------------------------------------------
# bins to rows
# ---------------------------------------------------------------------------

def _hist_renderer(fig):
    for r in _glyph_renderers(fig):
        if "__dash_bin_rows" in r.data_source.data:
            return r
    return None


class TestBinRows:
    def test_members_agree_with_the_histogram_count(self):
        rng = np.random.default_rng(3)
        xs = rng.normal(size=200)
        xs[5] = np.nan
        edges = np.linspace(np.nanmin(xs), np.nanmax(xs), 9)
        ids = list(range(1000, 1200))
        got = dr._dash_bin_members(edges, xs, ids)
        fin = xs[np.isfinite(xs)]
        counts = dr.GlyphMapper._histogram_counts(
            fin, None, float(edges[0]), float(edges[1] - edges[0]), 8)
        assert [len(b) for b in got] == [int(c) for c in counts]
        assert 1005 not in {i for b in got for i in b}
        # Every finite row once.
        assert sorted(i for b in got for i in b) == sorted(
            i for i, x in zip(ids, xs) if np.isfinite(x))

    @pytest.mark.xfail(strict=False, reason="S52 inserts the twin")
    def test_members_agree_with_the_js_twin(self):
        import js_runner
        js = dr._FILTER_JS
        assert "function dash_bin_members(" in js
        helpers = js[js.index("function dash_bin_members("):
                     js.index("// agg_sources is a Bokeh model list")]
        edges = [0.0, 1.0, 2.0, 3.0]
        xs = [0.0, 0.5, 1.0, 2.999, 3.0, -1.0, None]
        ids = [1, 2, 3, 4, 5, 6, 7]
        out = js_runner.run_js(helpers + "\nprocess.stdout.write(JSON."
                               "stringify(dash_bin_members(%s, %s, %s)));"
                               % (json.dumps(edges), json.dumps(xs),
                                  json.dumps(ids)))
        assert out == dr._dash_bin_members(
            edges, [np.nan if x is None else x for x in xs], ids)

    def test_histogram_source_carries_bin_members(self):
        r = _saved(_spec([_graph("g1", "histogram")]))
        hr = _hist_renderer(r.figures["g1"])
        assert hr is not None, "the histogram's bins carry no rows"
        members = hr.data_source.data["__dash_bin_rows"]
        assert len(members) == len(hr.data_source.data["top"])
        assert sorted(i for b in members for i in b) == list(range(_N))

    def test_bar_source_carries_its_rows(self):
        """A twoway bar draws one bar per observation: its source holds
        the rows (no bins), and a selection on it reaches the brush."""
        r = _saved(_spec([_graph("g1", "bar")], kpis=[_kpi()]))
        bars = _glyph_renderers(r.figures["g1"])
        assert dr._ROW_ID_COLUMN in bars[0].data_source.data
        assert id(bars[0].data_source) in _brush_callbacks(r)

    def test_the_script_maps_bins_to_raw_rows(self):
        r = _saved(_spec([_graph("g1", "histogram")], kpis=[_kpi()]))
        hr = _hist_renderer(r.figures["g1"])
        cb = _brush_callbacks(r).get(id(hr.data_source))
        assert cb is not None, "a selection on the bins reaches no script"
        raw = cb.args["raw_source"]
        out = _js_cb(cb, [0])
        rid = list(raw.data[dr._ROW_ID_COLUMN])
        want_ids = set(hr.data_source.data["__dash_bin_rows"][0])
        assert out["sel"][raw.id] == [i for i, v in enumerate(rid)
                                      if v in want_ids]

    def test_served_cb_maps_bins_to_rows(self, tmp_path):
        doc, _ = _served(_spec([_graph("g1", "histogram")],
                               kpis=[_kpi()]), tmp_path)
        hr = None
        for f in _served_figs(doc):
            hr = _hist_renderer(f) or hr
        assert hr is not None, "the served histogram's bins carry no rows"
        members = hr.data_source.data["__dash_bin_rows"]
        hr.data_source.selected.indices = [0]
        from bokeh.models import Div
        texts = [d.text for d in doc.select({"type": Div})
                 if "kpi_val_k1" in (d.text or "")]
        rows = members[0]
        want = float(_DF["mpg"].iloc[list(rows)].mean())
        assert texts and _card_value(texts[0]) == pytest.approx(want,
                                                                 abs=1e-3)


# ---------------------------------------------------------------------------
# intersection
# ---------------------------------------------------------------------------

class TestIntersection:
    def _two(self):
        r = _saved(_spec(_FOUR[:2], kpis=[_kpi()]))
        cbs = _brush_callbacks(r)
        return r, cbs[id(r.sources["g1"])], cbs[id(r.sources["g2"])]

    def test_two_sources_intersect(self):
        r, c1, c2 = self._two()
        a = _js_cb(c1, [0, 1, 2, 3, 4])
        b = _js_cb(c2, [3, 4, 5, 6], state=a["state"])
        rid = list(r.sources["g2"].data[dr._ROW_ID_COLUMN])
        both = sorted({rid[i] for i in (3, 4, 5, 6)}
                      & set(list(r.sources["g1"].data[dr._ROW_ID_COLUMN])
                            [0:5]))
        want = float(_DF["mpg"].iloc[both].mean())
        assert _card_value(b["cards"][0]) == pytest.approx(want, abs=1e-3)

    def test_clearing_one_restores_the_other(self):
        r, c1, c2 = self._two()
        a = _js_cb(c1, [0, 1, 2])
        b = _js_cb(c2, [2, 3], state=a["state"])
        c = _js_cb(c2, [], state=b["state"])
        want = float(_DF["mpg"].iloc[[0, 1, 2]].mean())
        assert _card_value(c["cards"][0]) == pytest.approx(want, abs=1e-3)

    def test_the_state_holds_one_column_per_source_and_no_json(self):
        r, c1, c2 = self._two()
        st = c1.args["brush_state"]
        assert isinstance(st, ColumnDataSource) and st.name == \
            "dash_brush_state"
        assert c2.args["brush_state"] is st
        a = _js_cb(c1, [0, 1])
        b = _js_cb(c2, [1], state=a["state"])
        assert set(b["state"]) == {c1.args["src_key"], c2.args["src_key"]}
        assert all(isinstance(v, list) and len(v) == 1
                   and isinstance(v[0], list) for v in b["state"].values())
        assert "JSON.parse" not in dr._BRUSH_JS
        assert "JSON.stringify" not in dr._BRUSH_JS

    def test_the_served_app_agrees(self, tmp_path):
        doc, _ = _served(_spec(_FOUR[:2], kpis=[_kpi()]), tmp_path)
        f1, f2 = _served_figs(doc)[:2]
        s1 = _glyph_renderers(f1)[0].data_source
        s2 = _glyph_renderers(f2)[0].data_source
        s1.selected.indices = [0, 1, 2, 3, 4]
        s2.selected.indices = [3, 4, 5, 6]
        l1 = {s1.data["index"][i] for i in (0, 1, 2, 3, 4)}
        l2 = {s2.data["index"][i] for i in (3, 4, 5, 6)}
        from bokeh.models import Div
        texts = [d.text for d in doc.select({"type": Div})
                 if "kpi_val_k1" in (d.text or "")]
        # The served frame's rows are page ranks; read the values back by
        # the labels each source carries.
        vals = dict(zip(s1.data["index"], s1.data["mpg"]))
        vals.update(zip(s2.data["index"], s2.data["mpg"]))
        want = float(np.mean([vals[i] for i in sorted(l1 & l2)]))
        assert texts and _card_value(texts[0]) == pytest.approx(want,
                                                                 abs=1e-3)
        s2.selected.indices = []
        texts = [d.text for d in doc.select({"type": Div})
                 if "kpi_val_k1" in (d.text or "")]
        want1 = float(np.mean([vals[i] for i in sorted(l1)]))
        assert _card_value(texts[0]) == pytest.approx(want1, abs=1e-3)
