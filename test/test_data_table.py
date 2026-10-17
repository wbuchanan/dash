"""A graph given ``table`` draws a folded data table of its drawn rows
under it, in Stata's display formats, in both modes (WP-31 H2t).

twoway has no data table; the option is dash's own.  Before WP-31 no
``DataTable`` existed in dash_render.py: a reader who wanted the numbers
behind a graph had only the CSV button, which writes raw values for the
whole dataset.  ``table`` now puts a ``Toggle`` labelled "Data table", a
``DataTable`` and a fixed note under the graph's figure (or its by()
grid), the table folded away until the toggle is pressed (DISCOVERY Q38).
The table lists the rows the graph draws, its columns the plotted
variables in tooltip order then the hover() variables (a by() graph's
variables first), each cell the variable's Stata display text with value
labels applied and ``.`` for a missing value (Q39).  At most ``rows()``
rows are listed, default the ``table_rows`` limit, 1,000 (Q40), the first
N DRAWN rows (DECISIONS A29).

The text travels as string columns ``__dash_tbl_<var>`` of the graph's own
source, so a saved filter move (which rewrites the source's rows) and a
served move (which re-slices the frame) carry it with no new JavaScript.

The Chrome class is the release tier; without Chrome it skips, and a skip
is red under ``DASH_STRICT=1``.
"""
import html
import itertools
import json
import os
import re
import sys
import tempfile
import time
import warnings
from unittest import mock

import numpy as np
import pandas as pd
import pytest
from bokeh.models import (Column, CustomJS, DataTable, Div, IndexFilter,
                          Select, Toggle)

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import load_app, make_data_json, render_models  # noqa: E402
from js_runner import JsSession, requires_node  # noqa: E402
from test_mode_parity import _spec  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_SEQ = itertools.count()
_TMP = tempfile.mkdtemp(prefix="dash_table_")

_DF = pd.DataFrame({
    "mpg": [22.0, 17.0, 25.0, 30.0, 21.0, 19.0, 14.0, 28.0, 16.0, 23.0],
    "weight": [2930.0, 3350.0, 2200.0, 1800.0, 3000.0, 3100.0, 4080.0,
               2010.0, 3600.0, 2650.0],
    "foreign": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
    "price": [4099.0, 4749.0, 3799.0, 4816.0, 5788.0, 4453.0, 5189.0,
              10372.0, 4082.0, 11385.0],
    "rep": [3.0, np.nan, 3.0, 5.0, 4.0, 3.0, 5.0, 4.0, 3.0, 4.0],
})
_VALUE_LABELS = {"origin": {"0": "Domestic", "1": "Foreign"}}
_LABEL_NAMES = {"foreign": "origin"}
_VAR_LABELS = {"mpg": "Mileage (mpg)", "foreign": "Car origin",
               "price": "Price"}
_FORMATS = {"price": "%8.0gc", "mpg": "%8.0g", "weight": "%8.0gc",
            "foreign": "%8.0g", "rep": "%8.0g"}


def _table_spec(go=None, bo=None, plots=None, if_expr=""):
    return _spec(plots or [plot_for("scatter")],
                 dict({"formats": dict(_FORMATS)}, **(bo or {})),
                 go, None, None, if_expr)


def _write(spec, df=_DF):
    tag = next(_SEQ)
    sp = os.path.join(_TMP, f"spec_{tag}.json")
    dp = os.path.join(_TMP, f"data_{tag}.json")
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(make_data_json(df, _VALUE_LABELS, _LABEL_NAMES,
                                 _VAR_LABELS), fh)
    return tag, sp, dp


def _saved(spec, df=_DF):
    _, sp, dp = _write(spec, df)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return render_models(dr.DashRenderer(sp, dp))


def _served(spec, df=_DF):
    from bokeh.document import Document
    tag, sp, dp = _write(spec, df)
    ap = os.path.join(_TMP, f"app_{tag}.py")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(ap)
        mod = load_app(ap, f"_table_app_{tag}")
        doc = Document()
        mod.make_document(doc)
    return doc


def _models(root):
    """Every model reachable from *root* (a layout or a Document)."""
    roots = root.roots if hasattr(root, "roots") else [root]
    out, seen = [], set()
    for r in roots:
        for m in r.references():
            if m.id not in seen:
                seen.add(m.id)
                out.append(m)
    return out


def _table_cells(root):
    """The Columns the layout draws a table in: (cell, toggle, table, note)."""
    out = []
    for m in _models(root):
        if not isinstance(m, Column):
            continue
        kids = list(m.children)
        if len(kids) == 4 and isinstance(kids[1], Toggle) \
                and isinstance(kids[2], DataTable):
            out.append((m, kids[1], kids[2], kids[3]))
    return out


def _one(root):
    cells = _table_cells(root)
    assert len(cells) == 1, f"{len(cells)} table cells"
    return cells[0]


def _rows(dt):
    """The listed rows' text, column by column, in view order."""
    src = dt.source
    n = len(next(iter(src.data.values())))
    idx = [i for i in dt.view.filter.indices if 0 <= i < n]
    return {c.title: [src.data[c.field][i] for i in idx] for c in dt.columns}


# ---------------------------------------------------------------------------
# The option draws a table, in both modes
# ---------------------------------------------------------------------------

class TestATableIsDrawn:

    def test_saved_cell_is_a_column_of_figure_toggle_table_note(self):
        r = _saved(_table_spec({"table": "on"}))
        cell, toggle, dt, note = _one(r._last_layout_root)
        assert cell.children[0] is r.figures["g1"]
        assert isinstance(note, Div)
        assert toggle.label == "Data table"
        assert r.figures["g1"]._dash_table == (toggle, dt, note)

    def test_served_cell_is_the_same(self):
        doc = _served(_table_spec({"table": "on"}))
        cell, toggle, dt, note = _one(doc)
        assert type(cell.children[0]).__name__ == "figure"
        assert toggle.label == "Data table"
        assert [c.title for c in dt.columns] == [
            c.title for c in _one(_saved(_table_spec(
                {"table": "on"}))._last_layout_root)[2].columns]

    def test_without_the_option_nothing_is_added(self):
        r = _saved(_table_spec())
        assert not _table_cells(r._last_layout_root)
        assert not [c for c in r.df.columns
                    if str(c).startswith("__dash_tbl_")]
        assert not [m for m in _models(r._last_layout_root)
                    if isinstance(m, DataTable)]
        doc = _served(_table_spec())
        assert not [m for m in _models(doc) if isinstance(m, DataTable)]


# ---------------------------------------------------------------------------
# Columns, text
# ---------------------------------------------------------------------------

class TestTheColumns:

    def test_order_and_titles(self):
        spec = _table_spec({"table": "on", "hover": "price rep mpg"})
        for root in (_saved(spec)._last_layout_root, _served(spec)):
            dt = _one(root)[2]
            # x then y (the tooltip's order), then hover() not yet listed.
            assert [c.field for c in dt.columns] == [
                "__dash_tbl_weight", "__dash_tbl_mpg", "__dash_tbl_price",
                "__dash_tbl_rep"]
            assert [c.title for c in dt.columns] == [
                "weight", "Mileage (mpg)", "Price", "rep"]
            assert all(c.sortable for c in dt.columns)
            assert dt.sortable and dt.index_position is None

    def test_table_vars_rule(self):
        g = {"graph_options": {"by": "foreign rep, cols(1)",
                               "hover": "price mpg bad-name price"},
             "plots": [plot_for("scatter"),
                       plot_for("rcap")]}
        assert dr._dash_table_vars(g) == [
            "foreign", "rep", "weight", "mpg", "price"]

    def test_table_spec_rule(self):
        lim = dr._dash_limits({})
        assert dr._dash_table_spec({}, lim) is None
        assert dr._dash_table_spec({"table": ""}, lim) is None
        assert dr._dash_table_spec({"table": "on"}, lim) == {
            "rows": 1000, "open": False}
        assert dr._dash_table_spec({"table": "rows(50) open"}, lim) == {
            "rows": 50, "open": True}
        assert dr._dash_table_spec({"table": "rows(999999)"}, lim)[
            "rows"] == 100_000
        lim2 = dr._dash_limits({"limits": {"table_rows": 20}})
        assert dr._dash_table_spec({"table": "on"}, lim2)["rows"] == 20


class TestTheText:

    def test_formats_labels_and_missing(self):
        spec = _table_spec({"table": "on", "hover": "price foreign rep"})
        for root in (_saved(spec)._last_layout_root, _served(spec)):
            rows = _rows(_one(root)[2])
            assert rows["Price"] == [dr._dash_fmt_text(v, "%8.0gc")
                                     for v in _DF["price"]]
            assert rows["Price"][0] == "4,099"
            assert rows["Car origin"] == ["Domestic", "Foreign"] * 5
            assert rows["rep"][1] == "."
            assert rows["weight"][0] == "2,930"

    def test_formats_each_distinct_value_once(self):
        df = pd.DataFrame({"x": [1.5, 1.5, 2.5, np.nan] * 50})
        with mock.patch.object(dr, "_dash_fmt_text",
                               wraps=dr._dash_fmt_text) as fmt:
            cols = dr._dash_table_text_frame(
                df, ["x", "missing_var"], {"x": "%9.2f"}, {}, {}, {}, {},
                {})
        assert fmt.call_count == 2
        assert cols == [("x", "x")]
        assert list(df["__dash_tbl_x"][:4]) == ["1.50", "1.50", "2.50", "."]

    def test_a_date_reads_as_its_format(self):
        df = pd.DataFrame({"d": pd.to_datetime(["2002-01-03", None])})
        dr._dash_table_text_frame(df, ["d"], {"d": "%td"}, {}, {}, {}, {},
                                  {"d": "td"})
        assert list(df["__dash_tbl_d"]) == ["03jan2002", "."]

    def test_the_csv_omits_the_text_columns(self):
        meta = dr._dash_csv_meta(["mpg", "__dash_tbl_mpg"], {}, {}, {}, {})
        assert meta["columns"] == ["mpg"]


# ---------------------------------------------------------------------------
# The view: the first N drawn rows (A29)
# ---------------------------------------------------------------------------

class TestTheView:

    def test_first_n_drawn_rows(self):
        dt = _one(_saved(_table_spec({"table": "rows(4)"}))
                  ._last_layout_root)[2]
        assert isinstance(dt.view.filter, IndexFilter)
        assert list(dt.view.filter.indices) == [0, 1, 2, 3]

    @staticmethod
    def _linked(go, bo=None, if_expr="mpg > 22"):
        spec = _table_spec(go, dict({"link": "g1 g2"}, **(bo or {})),
                           if_expr=if_expr)
        spec["graphs"].append(dict(spec["graphs"][0], name="g2",
                                   graph_options={"name": "g2"},
                                   if_expr="", in_expr=""))
        spec["build_options"]["registry"] = "g1 g2"
        return spec

    def test_a_qualified_graph_lists_its_first_drawn_rows(self):
        # A linked graph draws the link group's source through a view; its
        # table lists the graph's own rows, the first three of them -- not
        # the source's first three, which the qualifier drops.
        spec = self._linked({"table": "rows(3)"})
        want = [dr._dash_fmt_text(v, "%8.0g") for v in _DF["mpg"] if v > 22]
        for root in (_saved(spec)._last_layout_root, _served(spec)):
            dt = _one(root)[2]
            assert _rows(dt)["Mileage (mpg)"] == want[:3]
        assert _DF["mpg"][0] <= 22

    @requires_node
    def test_a_linked_table_follows_a_saved_move(self):
        spec = self._linked({"table": "on", "hover": "foreign"},
                            {"filter": "foreign, type(dropdown)"})
        r = _saved(spec)
        dt = _one(r._last_layout_root)[2]
        w = r.filter_widgets[0]
        w.value = [v for v, lab in w.options if lab == "Foreign"][0]
        cb = r.filter_callbacks[0]
        JsSession([]).run_code(cb.code, cb.args)
        keep = _DF[(_DF["mpg"] > 22) & (_DF["foreign"] == 1)]
        assert _rows(dt)["Car origin"] == ["Foreign"] * len(keep)
        assert _rows(dt)["Mileage (mpg)"] == [
            dr._dash_fmt_text(v, "%8.0g") for v in keep["mpg"]]

    def test_a_linked_table_follows_a_served_move(self):
        from test_mode_parity import _fire, _widgets_of
        doc = _served(self._linked({"table": "on", "hover": "foreign"},
                                   {"filter": "foreign, type(dropdown)"}))
        dt = _one(doc)[2]
        w = [x for x in _widgets_of(doc) if isinstance(x, Select)][0]
        _fire(w, [v for v, lab in w.options if lab == "Foreign"][0])
        keep = _DF[(_DF["mpg"] > 22) & (_DF["foreign"] == 1)]
        assert _rows(dt)["Mileage (mpg)"] == [
            dr._dash_fmt_text(v, "%8.0g") for v in keep["mpg"]]

    @requires_node
    def test_after_a_saved_move_the_kept_positions_are_a_range(self):
        spec = _table_spec({"table": "rows(3)", "hover": "foreign"},
                           {"filter": "foreign, type(dropdown)"})
        r = _saved(spec)
        dt = _one(r._last_layout_root)[2]
        w = r.filter_widgets[0]
        w.value = [v for v, lab in w.options if lab == "Foreign"][0]
        cb = r.filter_callbacks[0]
        JsSession([]).run_code(cb.code, cb.args)
        n = len(dt.source.data[dr._ROW_ID_COLUMN])
        assert n == 5
        assert set(dt.source.data["__dash_tbl_foreign"]) == {"Foreign"}
        listed = [i for i in dt.view.filter.indices if i < n]
        assert listed == list(range(min(3, n)))

    @pytest.mark.parametrize("go", [{"table": "on"},
                                    {"table": "on", "by": "foreign"}],
                             ids=["plain", "by"])
    def test_a_served_move_rewrites_the_table(self, go):
        from test_mode_parity import _fire, _widgets_of
        doc = _served(_table_spec(dict(go, hover="foreign"),
                                  {"filter": "foreign, type(dropdown)"}))
        dt = _one(doc)[2]
        w = [x for x in _widgets_of(doc) if isinstance(x, Select)][0]
        _fire(w, [v for v, lab in w.options if lab == "Foreign"][0])
        assert list(dt.source.data["__dash_tbl_foreign"]) == ["Foreign"] * 5

    def test_the_cap_is_in_the_tags(self):
        dt = _one(_saved(_table_spec({"table": "rows(7)"}))
                  ._last_layout_root)[2]
        assert dt.tags == ["dash_table", "dash_table_cap=7"]


def test_the_index_filter_drops_out_of_range_indices():
    """BokehJS sets an IndexFilter's indices in a BitSet whose set() skips
    an index past the source's length with a warning, never a throw: a
    Python-built list longer than a moved source is safe."""
    import bokeh
    path = os.path.join(os.path.dirname(bokeh.__file__), "server", "static",
                        "js", "bokeh.js")
    with open(path, encoding="utf-8") as fh:
        js = fh.read()
    m = re.search(r"class IndexFilter extends[\s\S]*?compute_indices\(source\)"
                  r" \{([\s\S]*?)\n        \}", js)
    assert m and "Indices.from_indices(size, indices)" in m.group(1)
    s = re.search(r"\n        set\(k, v = true\) \{([\s\S]*?)\n        \}", js)
    assert s and "0 <= k && k < size" in s.group(1)
    assert "throw" not in s.group(1) and "logger.warn" in s.group(1)


# ---------------------------------------------------------------------------
# The cap and the toggle
# ---------------------------------------------------------------------------

class TestTheCap:

    def test_rows_sub_option(self):
        for root in (_saved(_table_spec({"table": "rows(5) open"}))
                     ._last_layout_root,
                     _served(_table_spec({"table": "rows(5) open"}))):
            _, toggle, dt, note = _one(root)
            assert len(dt.view.filter.indices) == 5
            assert note.visible is True
        _, toggle, dt, note = _one(_saved(_table_spec(
            {"table": "on"}))._last_layout_root)
        assert len(dt.view.filter.indices) == 10
        assert note.visible is False
        assert "dash_table_cap=1000" in dt.tags

    def test_the_note_is_fixed_text(self):
        _, toggle, dt, note = _one(_saved(_table_spec(
            {"table": "rows(5)"}))._last_layout_root)
        assert note.text == html.escape(
            dr._DASH_TABLE_CAP_NOTE.format(cap=5))
        assert note.text == "The table lists at most 5 rows of those drawn."
        assert note.html_attributes == {"role": "note"}
        assert note.visible is False
        cb = toggle.js_property_callbacks["change:active"][0]
        assert cb.args["capped"] is True
        _, toggle, _, _ = _one(_saved(_table_spec(
            {"table": "on"}))._last_layout_root)
        assert toggle.js_property_callbacks[
            "change:active"][0].args["capped"] is False


class TestTheToggle:

    def test_default_folded(self):
        for root in (_saved(_table_spec({"table": "on"}))._last_layout_root,
                     _served(_table_spec({"table": "on"}))):
            _, toggle, dt, note = _one(root)
            assert toggle.active is False and dt.visible is False
            cb = toggle.js_property_callbacks["change:active"][0]
            assert isinstance(cb, CustomJS)
            assert cb.code == dr._DASH_TABLE_TOGGLE_JS
            assert cb.args["dt"] is dt and cb.args["note"] is note

    def test_open(self):
        for root in (_saved(_table_spec({"table": "open"}))
                     ._last_layout_root,
                     _served(_table_spec({"table": "open"}))):
            _, toggle, dt, _ = _one(root)
            assert toggle.active is True and dt.visible is True


# ---------------------------------------------------------------------------
# by(): one table under the grid (DECISIONS D6)
# ---------------------------------------------------------------------------

class TestByGraphs:

    def _both(self, go):
        spec = _table_spec(dict({"by": "foreign"}, **go))
        return [_saved(spec)._last_layout_root, _served(spec)]

    def test_one_table_under_the_grid_both_modes(self):
        for root in self._both({"table": "on"}):
            cell, toggle, dt, note = _one(root)
            assert type(cell.children[0]).__name__ not in ("figure",)
            assert [m for m in _models(cell.children[0])
                    if type(m).__name__ == "figure"]

    def test_rows_come_from_every_panel(self):
        for root in self._both({"table": "on"}):
            dt = _one(root)[2]
            assert len(dt.view.filter.indices) == 10

    def test_a_linked_by_graph_lists_its_panels_rows(self):
        spec = TestTheView._linked({"table": "on", "by": "foreign"})
        for root in (_saved(spec)._last_layout_root, _served(spec)):
            rows = _rows(_one(root)[2])
            assert sorted(rows["Mileage (mpg)"]) == sorted(
                dr._dash_fmt_text(v, "%8.0g") for v in _DF["mpg"] if v > 22)

    def test_the_panel_column_leads_with_the_panel_labels(self):
        for root in self._both({"table": "on"}):
            dt = _one(root)[2]
            assert dt.columns[0].title == "Car origin"
            rows = _rows(dt)
            assert sorted(set(rows["Car origin"])) == ["Domestic", "Foreign"]

    def test_the_cap_applies_to_the_union(self):
        for root in self._both({"table": "rows(5)"}):
            assert len(_one(root)[2].view.filter.indices) == 5


# ---------------------------------------------------------------------------
# Release tier: the table in a browser
# ---------------------------------------------------------------------------

_PROBE = r"""
<script>
(function () {
  function find(type) {
    for (const doc of window.Bokeh.documents)
      for (const m of doc.all_models) if (m.type === type) return m;
    return null;
  }
  function shown() {
    let n = 0;
    function walk(root) {
      const cells = root.querySelectorAll ? root.querySelectorAll(".slick-row") : [];
      n += cells.length;
      const all = root.querySelectorAll ? root.querySelectorAll("*") : [];
      for (const el of all) if (el.shadowRoot) walk(el.shadowRoot);
    }
    walk(document);
    return n;
  }
  function wait() {
    if (!window.Bokeh || !window.Bokeh.documents ||
        !window.Bokeh.documents.length || !find("Select")) {
      setTimeout(wait, 100);
      return;
    }
    setTimeout(function () {
      const res = {};
      const dt = find("DataTable"), tg = find("Toggle"), sel = find("Select");
      tg.active = true;
      setTimeout(function () {
        res.open_rows = shown();
        const opt = sel.options.find((o) => (Array.isArray(o) ? o[1] : o)
                                      === "Foreign");
        sel.value = Array.isArray(opt) ? opt[0] : opt;
        setTimeout(function () {
          res.after_len = dt.source.get_length();
          res.after_rows = shown();
          res.after_text = dt.source.data["__dash_tbl_foreign"].slice();
          const pre = document.createElement("pre");
          pre.id = "r";
          pre.textContent = JSON.stringify(res);
          document.body.appendChild(pre);
        }, 500);
      }, 500);
    }, 500);
  }
  wait();
})();
</script>
"""


@pytest.mark.release
class TestTheTableFollowsAMove:

    def _run(self, go):
        import responsive_probe
        from test_stale_cue_browser import _run_chrome
        if responsive_probe.find_chrome() is None:
            pytest.skip("headless Chrome is not installed; set DASH_CHROME "
                        "(a skip is red under DASH_STRICT=1)")
        spec = _table_spec(dict(go, hover="foreign"),
                           {"filter": "foreign, type(dropdown)"})
        _, sp, dp = _write(spec)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            page = dr.DashRenderer(sp, dp).render()
        return _run_chrome(responsive_probe.admit_script(page, _PROBE))

    def test_saved_page_in_chrome(self):
        got = self._run({"table": "on"})
        assert got["open_rows"] >= 1, got
        assert got["after_len"] == 5, got
        assert set(got["after_text"]) == {"Foreign"}, got
        assert got["after_rows"] >= 1, got

    def test_by_table_follows_a_move(self):
        got = self._run({"table": "on", "by": "foreign"})
        assert got["after_len"] == 5, got
        assert set(got["after_text"]) == {"Foreign"}, got
