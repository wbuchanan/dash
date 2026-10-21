"""Graphs from several frames (WP-33 33-07; DECISIONS A-17, A-23, A-27, A-28).

A graph registered under Stata's own prefix, ``frame cars: dash scatter mpg
weight, name(g1)``, is drawn from frame cars, as ``frame cars: twoway ...``
draws from it.  A variable two frames' graphs share, held differently in
each, travels in a split column ``__dashm<k>`` for the later frame, and the
spec's ``build_options.frame_cols`` maps it for that frame's graphs.  These
tests read the renderer's side: the map's validation, one graph's view of
the data and metadata, the filter widget's column, the context that puts the
renderer back, and a page whose two graphs keep each frame's labels.  The
Stata side is test_e2e_multi.cscript Q3307-5..17.
"""
import json
import os
import sys
import tempfile

import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
from conftest import load_app, make_data_json, render_models
from test_server_layer_defects import plot_for

_HELP = os.path.join(_HERE, "..", "dash.sthlp")
_NAN = float("nan")


def _help():
    with open(_HELP, encoding="utf-8") as fh:
        return fh.read()


def _between(text, start, end):
    i = text.index(start)
    j = text.index(end, i + len(start))
    return text[i:j]


class TestTheHelp:
    def test_the_frames_paragraph(self):
        h = _help()
        par = _between(h, "{marker frames}", "{marker ")
        for needle in ("frame cars: dash", "frame cars: twoway", "link()",
                       "exclude", "r(111)", "r(198)", "r(109)",
                       "time-series operators", "display format"):
            assert needle in par, needle
        assert "r(106)" not in par
        assert "{synopt:{cmd:frame(}" not in h


_MAP = {"g2": {"foreign": {"col": "__dashm1", "frame": "c2"}}}


def _spec_with(fc):
    return {"build_options": {"frame_cols": fc}}


class TestTheFrameColsSpec:
    def test_entries_dash_writes(self):
        assert dr._dash_frame_cols_named(_spec_with(_MAP)) == _MAP
        assert dr._dash_frame_cols_named(_spec_with({})) == {}
        assert dr._dash_frame_cols_named({"build_options": {}}) == {}
        for bad in ({"g2": {"foreign": {"col": "__dashq1", "frame": "c2"}}},
                    {"g2": {"foreign": {"col": "__dashm0", "frame": "c2"}}},
                    {"g2": {"1x": {"col": "__dashm1", "frame": "c2"}}},
                    {"g2": {"foreign": {"col": "__dashm1", "frame": "a b"}}},
                    {"g2": {"foreign": "__dashm1"}},
                    {"g2": "foreign"}):
            with pytest.raises(ValueError):
                dr._dash_frame_cols_named(_spec_with(bad))


def _meta():
    return {"variable_labels": {"date": "Date", "__dashm1": "Month"},
            "value_labels": {"date": {}, "__dashm1": {"1": "one"}},
            "value_label_names": {"__dashm1": "__dashl1"},
            "formats": {"date": "%td", "__dashm1": "%tm"},
            "numeric_formats": {}, "date_vars": {"date": "td"},
            "storage_types": {"date": "float", "__dashm1": "int"},
            "string_vars": set()}


class TestTheFrameView:
    def test_a_graph_reads_its_own_frame(self):
        df = pd.DataFrame({"date": [1.0, 2.0], "__dashm1": [3.0, 4.0],
                           "make": ["a", "b"], "__dashm2": ["x", "y"]})
        meta = _meta()
        before = (df.copy(), json.dumps({k: (sorted(v) if isinstance(v, set)
                                             else v) for k, v in meta.items()},
                                         sort_keys=True))
        vdf, view = dr._dash_frame_view(df, meta, {"date": "__dashm1"})
        assert list(vdf["date"]) == [3.0, 4.0]
        assert "__dashm1" in vdf.columns
        assert view["formats"]["date"] == "%tm"
        assert view["variable_labels"]["date"] == "Month"
        assert view["value_labels"]["date"] == {"1": "one"}
        assert view["value_label_names"]["date"] == "__dashl1"
        assert "date" not in view["date_vars"]
        assert view["storage_types"]["date"] == "int"
        meta2 = dict(meta, string_vars={"__dashm2"})
        _vdf2, view2 = dr._dash_frame_view(df, meta2, {"make": "__dashm2"})
        assert "make" in view2["string_vars"]
        # The inputs are unchanged.
        pd.testing.assert_frame_equal(df, before[0])
        assert json.dumps({k: (sorted(v) if isinstance(v, set) else v)
                           for k, v in meta.items()},
                          sort_keys=True) == before[1]
        # No mapping: the same objects.
        same_df, same_meta = dr._dash_frame_view(df, meta, {})
        assert same_df is df and same_meta is meta

    def test_a_filter_reads_each_graphs_own_column(self):
        df = pd.DataFrame({"foreign": [0.0, 1.0, 0.0, _NAN, _NAN],
                           "__dashm1": [_NAN, _NAN, _NAN, 1.0, 0.0]})
        keep = df.copy()
        rows = {"g1": pd.Series([True, True, True, False, False]),
                "g2": pd.Series([False, False, False, True, True])}
        out = dr._dash_filter_frame_column(df, "foreign", _MAP, rows)
        assert list(out) == [0.0, 1.0, 0.0, 1.0, 0.0]
        assert not out.isna().any()
        pd.testing.assert_frame_equal(df, keep)
        # No graph maps foreign: the column as it is (pandas gives a new
        # Series object each time a column is read, so it is compared).
        pd.testing.assert_series_equal(
            dr._dash_filter_frame_column(df, "foreign", {}, rows),
            df["foreign"])


def _frames_spec(filt=""):
    def plot(q):
        p = plot_for("scatter", {"mlabel": "foreign"}, yvar="mpg",
                     xvar="weight")
        p["qual_col"] = q
        return p
    return {
        "graphs": [{"name": n, "graph_options": {"name": n},
                    "options": {"name": n}, "plots": [plot(q)],
                    "if_expr": "", "in_expr": "", "qual_col": q}
                   for n, q in (("g1", "__dashq1"), ("g2", "__dashq2"))],
        "kpis": [],
        "build_options": {
            "layout": "auto", "link": "", "filter": filt, "theme": "",
            "scheme": "", "session_scheme": "", "title": "",
            "subtitle": "", "registry": "g1 g2", "tabs": "",
            "filter_position": "top", "level": "95",
            "formats": {"foreign": "%8.0g", "__dashm1": "%8.0g"},
            "frame_cols": _MAP}}


def _frames_files(spec, df=None):
    if df is None:
        df = pd.DataFrame({
            "mpg": [22., 17, 25, 30, 21, 19, 14, 28, 16, 23],
            "weight": [2930., 3350, 2200, 1800, 3000, 3100, 4080, 2010,
                       3600, 2650],
            "foreign": [0., 1, 0, 1, 0] + [_NAN] * 5,
            "__dashm1": [_NAN] * 5 + [1., 0, 1, 0, 1],
            "__dashq1": [1.] * 5 + [0.] * 5,
            "__dashq2": [0.] * 5 + [1.] * 5,
        })
    d = tempfile.mkdtemp(prefix="dash_frames_")
    sp, dp = os.path.join(d, "spec.json"), os.path.join(d, "data.json")
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(make_data_json(
            df, {"foreign": {"0": "Domestic", "1": "Foreign"},
                 "__dashm1": {"0": "US", "1": "Abroad"}},
            {"foreign": "origin", "__dashm1": "__dashl1"},
            {"foreign": "Car origin", "__dashm1": "Made abroad"}), fh)
    return sp, dp


def _label_texts(fig):
    for a in fig.center:
        if type(a).__name__ == "LabelSet":
            return list(a.source.data[a.text])
    return None


class TestTheFrameRenderer:
    def test_the_context_puts_everything_back(self):
        sp, dp = _frames_files(_frames_spec())
        r = dr.DashRenderer(sp, dp)
        names = ("df",) + dr._DASH_FRAME_META_KEYS + ("string_vars",)
        orig = {k: getattr(r, k) for k in names}
        with r._dash_graph_frame("g2"):
            assert r.df is not orig["df"]
            assert r.variable_labels["foreign"] == "Made abroad"
            assert r.mapper.variable_labels["foreign"] == "Made abroad"
        for k in names:
            assert getattr(r, k) is orig[k], k
        assert r.mapper.variable_labels["foreign"] == "Car origin"
        with pytest.raises(RuntimeError):
            with r._dash_graph_frame("g2"):
                raise RuntimeError("inside")
        for k in names:
            assert getattr(r, k) is orig[k], k
        with r._dash_graph_frame("g1"):
            assert r.df is orig["df"]


class TestTheFramePage:
    def test_each_graph_keeps_its_frame_metadata(self):
        sp, dp = _frames_files(_frames_spec())
        r = render_models(dr.DashRenderer(sp, dp))
        assert set(_label_texts(r.figures["g1"])) == {"Domestic", "Foreign"}
        assert set(_label_texts(r.figures["g2"])) == {"US", "Abroad"}
        # With a filter: g2's source holds its own frame's foreign, which
        # the page's filter mask tests (DECISIONS A-27), and the widget's
        # choices hold no missing value.
        sp, dp = _frames_files(_frames_spec("foreign"))
        r = render_models(dr.DashRenderer(sp, dp))
        src = r.figures["g2"].renderers[0].data_source.data
        assert list(src["foreign"]) == [1.0, 0.0, 1.0, 0.0, 1.0]
        opts = [w for w in r.filter_widgets] if isinstance(
            getattr(r, "filter_widgets", None), list) else []
        for w in opts:
            for o in (getattr(w, "options", None) or []):
                text = o[1] if isinstance(o, (list, tuple)) else o
                assert str(text) not in (".", "nan", "")
        # A split column the spec does not map is a reserved column.
        spec = _frames_spec()
        del spec["build_options"]["frame_cols"]
        sp, dp = _frames_files(spec)
        with pytest.raises(ValueError, match="reserved"):
            dr.DashRenderer(sp, dp)

    def test_the_served_app_keeps_each_frames_metadata(self):
        # The served app builds each graph from its frame's view too
        # (D-33-07.m): g2's labels are US/Abroad and its filter column its
        # own frame's values.
        from bokeh.document import Document
        from bokeh.models import LabelSet
        sp, dp = _frames_files(_frames_spec("foreign"))
        ap = os.path.join(os.path.dirname(sp), "app.py")
        dr.ServerAppBuilder(sp, dp).build(ap)
        mod = load_app(ap, "_frames_served_app")
        doc = Document()
        mod.make_document(doc)
        texts = [sorted(set(m.source.data[m.text])) for m in doc.models
                 if isinstance(m, LabelSet)]
        assert ["Abroad", "US"] in texts and ["Domestic", "Foreign"] in texts
        fsrc = [list(m.source.data["foreign"]) for m in doc.models
                if isinstance(m, LabelSet)]
        assert [1.0, 0.0, 1.0, 0.0, 1.0] in fsrc

    def test_a_served_move_filters_each_graph_by_its_own_frame(self):
        # A filter move tests each graph's own frame's values (A-27): the
        # Foreign choice keeps g1's foreign == 1 rows and g2's rows whose
        # split column holds 1.
        from bokeh.document import Document
        from bokeh.models import LabelSet, Select
        from test_mode_parity import _fire, _widgets_of
        sp, dp = _frames_files(_frames_spec("foreign, type(dropdown)"))
        ap = os.path.join(os.path.dirname(sp), "app.py")
        dr.ServerAppBuilder(sp, dp).build(ap)
        mod = load_app(ap, "_frames_served_move")
        doc = Document()
        mod.make_document(doc)
        w = [x for x in _widgets_of(doc) if isinstance(x, Select)][0]
        _fire(w, [v for v, lab in w.options if lab == "Foreign"][0])
        kept = sorted(len(m.source.data["foreign"]) for m in doc.models
                      if isinstance(m, LabelSet))
        assert kept == [2, 3]
        for m in doc.models:
            if isinstance(m, LabelSet):
                assert set(m.source.data["foreign"]) == {1.0}

    def test_a_split_plotted_variable_keeps_its_rows(self):
        # The page plan (_ensure_embed) picks rows by qualifier column and
        # cells by column name, so a graph that plots a split variable --
        # missing in the stack's own column on its rows -- keeps every row,
        # drawn at its own frame's values, saved and served.
        from bokeh.document import Document
        from bokeh.models import GlyphRenderer
        spec = _frames_spec()
        for g in spec["graphs"]:
            p = plot_for("scatter", yvar="mpg", xvar="foreign")
            p["qual_col"] = g["qual_col"]
            g["plots"] = [p]
        sp, dp = _frames_files(spec)
        r = render_models(dr.DashRenderer(sp, dp))
        assert list(r.figures["g2"].renderers[0].data_source.data[
            "foreign"]) == [1.0, 0.0, 1.0, 0.0, 1.0]
        ap = os.path.join(os.path.dirname(sp), "app.py")
        dr.ServerAppBuilder(sp, dp).build(ap)
        doc = Document()
        load_app(ap, "_frames_served_plot").make_document(doc)
        drawn = sorted(list(m.data_source.data.get("foreign", []))
                       for m in doc.models if isinstance(m, GlyphRenderer))
        assert [1.0, 0.0, 1.0, 0.0, 1.0] in drawn
        assert [0.0, 1.0, 0.0, 1.0, 0.0] in drawn

    def test_a_table_writes_each_frames_text(self):
        # A data table (table) of a graph reading a split variable shows
        # that frame's value labels on its rows, saved and served.
        from bokeh.document import Document
        from bokeh.models import DataTable
        spec = _frames_spec()
        for g in spec["graphs"]:
            g["graph_options"].update(table="on", hover="foreign")
        sp, dp = _frames_files(spec)
        r = dr.DashRenderer(sp, dp)
        col = list(r.df["__dash_tbl_foreign"])
        assert col[:5] == ["Domestic", "Foreign", "Domestic", "Foreign",
                           "Domestic"]
        assert col[5:] == ["Abroad", "US", "Abroad", "US", "Abroad"]
        ap = os.path.join(os.path.dirname(sp), "app.py")
        dr.ServerAppBuilder(sp, dp).build(ap)
        doc = Document()
        load_app(ap, "_frames_served_table").make_document(doc)
        texts = [set(m.source.data.get("__dash_tbl_foreign", []))
                 for m in doc.models if isinstance(m, DataTable)]
        assert {"Abroad", "US"} in texts and {"Domestic", "Foreign"} in texts

    def test_the_download_heads_a_split_column_by_its_frame(self):
        spec = _frames_spec()
        spec["build_options"]["csv"] = "1"
        sp, dp = _frames_files(spec)
        page = dr.DashRenderer(sp, dp).render()
        assert "foreign [frame c2]" in page


class TestStataTicks:
    def test_a_split_axis_asks_for_its_own_column(self):
        # Stata's ticks (WP-31 D15) of a graph that reads date from its
        # frame's split column are asked over that column, in its format.
        g = {"graph_options": {"name": "g2"}, "qual_col": "__dashq2",
             "plots": [{"type": "line", "yvar": "close", "xvar": "date",
                        "options": {}, "qual_col": "__dashq2"}]}
        fc = {"g2": {"date": {"col": "__dashm1", "frame": "spm"}}}
        fm = {"date": "%td", "__dashm1": "%tm", "close": "%9.0g"}
        xs = [r for r in dr._dash_stata_tick_requests([g], fm, fc)
              if r["layers"][0][0] == ("__dashm1",)]
        assert xs and all(r["unit"] == dr._dash_stata_unit_of("%tm")
                          for r in xs)
        plain = dr._dash_stata_tick_requests([g], fm)
        assert not [r for r in plain if r["layers"][0][0] == ("__dashm1",)]
