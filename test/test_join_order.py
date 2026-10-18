"""line, connected, area, rline, rarea and rconnected join as twoway joins.

twoway joins the points of these six types in the data's order; ``sort``
joins them in the order of x, and ``sort(varlist)`` in the order Stata's
``sort varlist`` gives, whether or not ``sort`` is also given (the rightmost
non-empty copy wins).  tsline and tsrline join in time order whatever they
are given.  Each bound of rline (and tsrline) keeps the rows where that
bound is present.  Measured on StataNow 19.5 and recorded in
``test/fixtures/join_order_truth.json`` (``scripts/extract_join_order_truth.do``).

dash used to join every one of them in x order, in both render modes, at
first paint and after every filter move (BUGS.md, WP-29 P0.1): ``dash line
mpg weight`` on the ten-car parity frame drew 1800, 2010, 2200, ... where
twoway draws 2930, 3350, 2200, ...; ``sort(varlist)`` was ignored with a
note; and rline left a row out of both bounds when one bound was missing.

``sort(varlist)`` is resolved in Stata: dash.ado writes one rank column
``__dashs<k>`` per distinct varlist, made by ``sort varlist obs``, and names
it in ``build_options.sort_cols``; the renderers take it out of the frame
(``_dash_take_sort_columns``) and order each joined layer by it
(``_dash_join_key``, ``GlyphMapper._join_order``).  No rank column and no
sort variable reaches the page, a source, a tooltip, a filter or the csv.
"""
import itertools
import json
import os
import sys
import tempfile
import time
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import (BooleanFilter, CDSView, ColumnDataSource,
                          HoverTool, Line, VArea)
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from conftest import make_data_json, load_app  # noqa: E402
from test_saved_filter_layers import _move  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_SEQ = itertools.count()
_TMP = tempfile.mkdtemp(prefix="dash_join_order_")
_FIXTURE = os.path.join(_HERE, "fixtures", "join_order_truth.json")

_JOIN = ["line", "connected", "area", "rline", "rarea", "rconnected"]
_RANGE = {"rline", "rarea", "rconnected", "tsrline"}
_MAPPER = {t: "map_" + t for t in _JOIN}


def _truth():
    if not os.path.exists(_FIXTURE):
        pytest.fail("test/fixtures/join_order_truth.json is missing: run "
                    "task 02-03 (scripts/extract_join_order_truth.do)")
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


# ===========================================================================
# The datasets of scripts/extract_join_order_truth.do
# ===========================================================================

#: Dataset A: 8 observations, tie-free under every key; y = 100 * obs.
_A = pd.DataFrame({
    "x": [4.0, 1.0, 3.0, 2.0, 8.0, 5.0, 7.0, 6.0],
    "y": [100.0 * i for i in range(1, 9)],
    "y2": [100.0 * i + 1 for i in range(1, 9)],
    "g": [1.0, 2.0, 1.0, 2.0, np.nan, 1.0, 2.0, 1.0],
    "t": [3.0, 8.0, 1.0, 6.0, 2.0, 7.0, 4.0, 5.0],
})
#: Dataset B: missing values, x distinct where present.
_B = pd.DataFrame({
    "x": [2.0, 5.0, 3.0, 6.0, 1.0, np.nan, 7.0],
    "y": [10.0, 20.0, np.nan, 40.0, 50.0, 45.0, 60.0],
    "y2a": [11.0, np.nan, 31.0, 41.0, 51.0, 46.0, 61.0],
    "y2b": [11.0, 21.0, np.nan, 41.0, 51.0, 46.0, 61.0],
})


def _with(df, **cols):
    out = df.copy()
    for k, v in cols.items():
        out[k] = [float(a) for a in v]
    return out


def _quals(n, rows):
    keep = set(rows)
    return [1.0 if i + 1 in keep else 0.0 for i in range(n)]


def _plot(ptype, xvar="x", y="y", y2="y2", options=None, sortvars=None):
    p = {"type": ptype, "xvar": xvar, "options": dict(options or {}),
         "if_expr": "", "in_expr": ""}
    if ptype in _RANGE:
        p["yvar1"], p["yvar2"] = y, y2
    else:
        p["yvar"] = y
    if sortvars:
        p["sortvars"] = sortvars
    return p


def _spec(plots, bo=None, go=None, qual_col=""):
    extra = {"if_expr": "", "in_expr": ""}
    if qual_col:
        extra["qual_col"] = qual_col
    return tp._spec(graphs=[("g1", plots, go or {}, extra)],
                    build_options=bo)


# ===========================================================================
# Both renderers, given a frame
# ===========================================================================

def _data_json(df, value_labels=None, label_names=None):
    d = make_data_json(df, value_labels, label_names)
    # Labels named explicitly (index.md A7): each variable labelled by its
    # name, whatever the helper's default.
    d["StataJSON"]["variableLabels"] = {c: c for c in df.columns}
    return d


def _write(spec, df, value_labels=None, label_names=None):
    tag = next(_SEQ)
    sp = os.path.join(_TMP, f"spec_{tag}.json")
    dp = os.path.join(_TMP, f"data_{tag}.json")
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(_data_json(df, value_labels, label_names), fh)
    return tag, sp, dp


def _saved(spec, df, labels=False, page=False):
    vl, ln = (tp._VALUE_LABELS, tp._LABEL_NAMES) if labels else (None, None)
    _, sp, dp = _write(spec, df, vl, ln)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r = dr.DashRenderer(sp, dp)
        html = r.render()
    if page:
        return r, sorted(str(w.message) for w in caught), html
    return r


def _served_module(spec, df, labels=False):
    vl, ln = (tp._VALUE_LABELS, tp._LABEL_NAMES) if labels else (None, None)
    tag, sp, dp = _write(spec, df, vl, ln)
    ap = os.path.join(_TMP, f"app_{tag}.py")
    with warnings.catch_warnings(record=True) as built:
        warnings.simplefilter("always")
        dr.ServerAppBuilder(sp, dp).build(ap)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mod = load_app(ap, f"_join_order_{tag}")
    return mod, [str(w.message) for w in built]


def _served(spec, df, labels=False, msgs=False):
    mod, built = _served_module(spec, df, labels)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        doc = Document()
        mod.make_document(doc)
    if msgs:
        return doc, sorted(built + [str(w.message) for w in caught])
    return doc


def _saved_move(spec, df, action):
    r = _saved(spec, df, labels=True)
    _move(r, action)
    return r


def _served_move(spec, df, action):
    """The served document after one widget move, and every warning the
    move raised."""
    doc = _served(spec, df, labels=True)
    kind, want = action
    ws = [w for w in tp._widgets_of(doc) if type(w).__name__ == kind]
    assert ws, f"no {kind} widget in the served document"
    w = ws[0]
    raw = [v for v, lab in w.options if lab == want]
    assert raw, f"no option labelled {want!r}: {w.options}"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        tp._fire(w, raw[0])
    return doc, [str(m.message) for m in caught]


def _figs_of(root):
    out = []

    def visit(m):
        if isinstance(m, (list, tuple)):
            for x in m:
                visit(x)
            return
        if m is None:
            return
        if type(m).__name__ == "figure":
            out.append(m)
            return
        for attr in ("children", "tabs", "child"):
            k = getattr(m, attr, None)
            if k is not None:
                visit(k)
    visit(root)
    return out


def _saved_figs(r):
    return _figs_of(r._last_layout_root)


def _served_figs(doc):
    out = []
    for root in doc.roots:
        out.extend(_figs_of(root))
    return out


def _joined(fig, xvar):
    """Each Line and VArea renderer's x column, in drawn order."""
    out = []
    for g in fig.renderers:
        if isinstance(g.glyph, (Line, VArea)):
            data = g.data_source.data
            if xvar in data:
                out.append([float(v) for v in data[xvar]])
    return out


def _obs(xs, df, xvar="x"):
    """x values to 1-based observation numbers (x is distinct)."""
    m = {float(v): i + 1 for i, v in enumerate(df[xvar]) if v == v}
    return [m[float(v)] for v in xs]


# ===========================================================================
# The rule
# ===========================================================================

class TestTheJoinOrderRule:

    def test_the_precedence(self):
        src = ColumnDataSource({"x": [2.0, 5.0, 3.0, 6.0, 1.0]})
        idx = np.arange(5)
        jo = dr.GlyphMapper._join_order
        assert list(jo(src, idx, "x", {})) == [0, 1, 2, 3, 4]
        assert list(jo(src, idx, "x", {"sort": "sort"})) == [4, 0, 2, 1, 3]
        assert list(jo(src, idx, "x", {"sort": "sort"},
                       order=[5, 4, 3, 2, 1])) == [4, 3, 2, 1, 0]
        assert list(jo(src, idx, "x", {}, order=[5, 4, 3, 2, 1],
                       by_x=True)) == [4, 0, 2, 1, 3]
        assert list(jo(src, np.arange(0), "x", {"sort": "sort"})) == []
        with pytest.raises(ValueError):
            jo(src, idx, "x", {}, order=[1, 2, 3])


# ===========================================================================
# The mappers
# ===========================================================================

_X = [2.0, 5.0, 3.0, 6.0, 1.0]


def _src(x=_X, **extra):
    n = len(x)
    d = {"x": list(x), "y": [10.0 * (i + 1) for i in range(n)],
         "y2": [10.0 * (i + 1) + 1 for i in range(n)],
         dr._ROW_ID_COLUMN: list(range(n))}
    d.update(extra)
    return ColumnDataSource(d)


def _drawn(name, src, options=None, **kw):
    """Every Line/VArea renderer's (x, y) columns a mapper drew."""
    fig = figure()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if name.replace("map_", "") in _RANGE:
            res = getattr(dr.GlyphMapper(), name)(
                fig, src, "y", "y2", "x", dict(options or {}), **kw)
        else:
            res = getattr(dr.GlyphMapper(), name)(
                fig, src, "y", "x", dict(options or {}), **kw)
    out = []
    for g in fig.renderers:
        if isinstance(g.glyph, Line):
            d = g.data_source.data
            out.append(([float(v) for v in d[g.glyph.x]],
                        [float(v) for v in d[g.glyph.y]]))
        elif isinstance(g.glyph, VArea):
            d = g.data_source.data
            out.append(([float(v) for v in d[g.glyph.x]],
                        [float(v) for v in d[g.glyph.y2]]))
    return out


class TestTheDefaultIsTheDataOrder:

    @pytest.mark.parametrize("name", [_MAPPER[t] for t in _JOIN])
    def test_a_mapper_joins_in_data_order(self, name):
        got = [xs for xs, _ in _drawn(name, _src())]
        assert got, name
        for xs in got:
            assert xs == _X, (name, xs)

    @pytest.mark.parametrize("name", [_MAPPER[t] for t in _JOIN])
    def test_bare_sort_joins_in_x_order(self, name):
        got = [xs for xs, _ in _drawn(name, _src(), {"sort": "sort"})]
        assert got
        for xs in got:
            assert xs == sorted(_X), (name, xs)

    @pytest.mark.parametrize("name", ["map_line", "map_connected",
                                      "map_area"])
    def test_ties_keep_the_data_order_under_sort(self, name):
        src = ColumnDataSource({"x": [2.0, 1.0, 2.0, 1.0],
                                "y": [10.0, 20.0, 30.0, 40.0],
                                dr._ROW_ID_COLUMN: [0, 1, 2, 3]})
        [(xs, ys)] = _drawn(name, src, {"sort": "sort"})
        assert ys == [20.0, 40.0, 10.0, 30.0]

    @pytest.mark.parametrize("name", [_MAPPER[t] for t in _JOIN])
    @pytest.mark.parametrize("opts", [{}, {"sort": "sort"}])
    def test_x_keeps_its_pairing_with_each_y(self, name, opts):
        want = {x: 10.0 * (i + 1) for i, x in enumerate(_X)}
        for xs, ys in _drawn(name, _src(), opts):
            for x, y in zip(xs, ys):
                assert y in (want[x], want[x] + 1), (name, x, y)

    def test_area_with_a_missing_y_bridges_in_data_order(self):
        src = ColumnDataSource({c: list(_B[c]) for c in ("x", "y")})
        [(xs, _)] = _drawn("map_area", src)
        rec = {r["id"]: r for r in _truth()["missing"]}["J8a-area-none"]
        path = rec["paths"][0]
        dedup = [v for i, v in enumerate(path) if i == 0 or v != path[i - 1]]
        assert xs == [float(v) for v in dedup[:-1]] == [2, 5, 6, 1, 7]


class TestTimeSeriesJoinInTimeOrder:

    @pytest.mark.parametrize("name", ["map_tsline", "map_tsrline"])
    @pytest.mark.parametrize("how", ["none", "sort", "key"])
    def test_whatever_they_are_given(self, name, how):
        src = _src()
        fig = figure()
        ptype = name.replace("map_", "")
        opts = {"sort": "sort"} if how == "sort" else {}
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if how == "key":
                dr._dash_add_glyph(
                    dr.GlyphMapper(), fig, src, ptype, "y", "x", opts,
                    y2var="y2" if ptype == "tsrline" else "",
                    order=[1.0, 2.0, 3.0, 4.0, 5.0])
            elif ptype == "tsrline":
                dr.GlyphMapper().map_tsrline(fig, src, "y", "y2", "x", opts)
            else:
                dr.GlyphMapper().map_tsline(fig, src, "y", "x", opts)
        lines = [g for g in fig.renderers if isinstance(g.glyph, Line)]
        assert lines
        for g in lines:
            assert [float(v) for v in g.data_source.data["x"]] == sorted(_X)


class TestASortKeySetsTheOrder:

    _KEY = [3.0, 1.0, 5.0, 2.0, 4.0]      # x 5, 6, 2, 1, 3

    @pytest.mark.parametrize("name", [_MAPPER[t] for t in _JOIN])
    def test_the_key_orders_the_rows(self, name):
        got = [xs for xs, _ in _drawn(name, _src(), order=self._KEY)]
        assert got
        for xs in got:
            assert xs == [5.0, 6.0, 2.0, 1.0, 3.0], (name, xs)

    def test_the_key_beats_a_bare_sort(self):
        [(xs, _)] = _drawn("map_line", _src(), {"sort": "sort"},
                           order=self._KEY)
        assert xs == [5.0, 6.0, 2.0, 1.0, 3.0]

    def test_the_key_under_a_view(self):
        view = CDSView(filter=BooleanFilter(
            booleans=[True, False, True, True, False]))
        [(xs, _)] = _drawn("map_line", _src(), view=view, order=self._KEY)
        # Rows 0, 2, 3 (x 2, 3, 6) by their keys 3, 5, 2: 6, 2, 3.
        assert xs == [6.0, 2.0, 3.0]


# ===========================================================================
# The key of a source
# ===========================================================================

class TestTheJoinKey:

    _KEYS = {"__dashs1": pd.Series([10.0, 30.0, 20.0], index=[0, 1, 2])}

    def test_saved_source_by_row_id(self):
        src = ColumnDataSource({"x": [1.0, 2.0, 3.0],
                                dr._ROW_ID_COLUMN: [2, 0, 1]})
        assert list(dr._dash_join_key(src, self._KEYS, "__dashs1")) == [
            20.0, 10.0, 30.0]

    def test_served_source_by_index_label(self):
        keys = {"__dashs1": pd.Series([10.0, 30.0, 20.0], index=[3, 5, 7])}
        src = ColumnDataSource({"x": [1.0, 2.0], "index": [7, 3]})
        assert list(dr._dash_join_key(src, keys, "__dashs1")) == [20.0, 10.0]

    def test_no_identity_is_refused(self):
        with pytest.raises(ValueError):
            dr._dash_join_key(ColumnDataSource({"x": [1.0]}), self._KEYS,
                              "__dashs1")

    @pytest.mark.parametrize("ids", [[0, 3], [-1, 0]])
    def test_an_out_of_range_id_is_refused(self, ids):
        src = ColumnDataSource({"x": [1.0, 2.0], dr._ROW_ID_COLUMN: ids})
        with pytest.raises(ValueError):
            dr._dash_join_key(src, self._KEYS, "__dashs1")

    def test_a_non_integer_id_is_refused(self):
        src = ColumnDataSource({"x": [1.0], dr._ROW_ID_COLUMN: [1.5]})
        with pytest.raises(ValueError):
            dr._dash_join_key(src, self._KEYS, "__dashs1")

    def test_an_unknown_column_is_refused(self):
        src = ColumnDataSource({"x": [1.0], dr._ROW_ID_COLUMN: [0]})
        with pytest.raises(ValueError):
            dr._dash_join_key(src, self._KEYS, "__dashs2")

    def test_no_column_gives_none(self):
        src = ColumnDataSource({"x": [1.0], dr._ROW_ID_COLUMN: [0]})
        assert dr._dash_join_key(src, self._KEYS, "") is None


# ===========================================================================
# The rank columns, taken out of the frame
# ===========================================================================

def _key_spec(sortvars="z", col="__dashs1", ptype="line", extra=None):
    bo = {"sort_cols": {sortvars: col}}
    bo.update(extra or {})
    return _spec([_plot(ptype, sortvars=sortvars)], bo)


class TestTakingTheSortColumnsOut:

    def test_the_frame_loses_the_columns_and_the_keys_hold_statas_ranks(self):
        ranks = _truth()["ranks"]
        df = _with(_A, __dashs1=ranks["z"], __dashs2=ranks["zz x"])
        spec = _spec([_plot("line", sortvars="z"),
                      _plot("rline", sortvars="zz x")],
                     {"sort_cols": {"z": "__dashs1", "zz x": "__dashs2"}})
        out, keys = dr._dash_take_sort_columns(df, spec)
        assert list(out.columns) == list(_A.columns)
        assert list(keys["__dashs1"]) == ranks["z"]
        assert list(keys["__dashs2"]) == ranks["zz x"]
        assert keys["__dashs1"].index.equals(out.index)

    @pytest.mark.parametrize("cols", [
        {"z": "__dashq1"}, {"z": "__dashs0"}, {"z": "__dashs123456"},
        {"z": "x"}, {"z": 5}, {'z"': "__dashs1"}, {"z  y": "__dashs1"},
        {"a" * 33: "__dashs1"}, {"z": "__dashs1", "y": "__dashs1"},
        ["z"],
    ], ids=["qual", "zero", "long", "user", "nonstr", "quote", "blank",
            "33chars", "shared", "notdict"])
    def test_the_map_is_validated(self, cols):
        spec = _spec([_plot("line")], {"sort_cols": cols})
        with pytest.raises(ValueError, match="__dashs"):
            dr._dash_sort_cols_named(spec)

    def test_a_plot_naming_an_unknown_list_is_refused(self):
        spec = _spec([_plot("line", sortvars="q")],
                     {"sort_cols": {"z": "__dashs1"}})
        with pytest.raises(ValueError):
            dr._dash_sort_cols_named(spec)

    def test_a_column_the_data_lack_is_refused(self):
        with pytest.raises(ValueError, match="not in the data"):
            dr._dash_take_sort_columns(_A, _key_spec())

    @pytest.mark.parametrize("bad", [
        [1, 1, 2, 3, 4, 5, 6, 7], [0, 1, 2, 3, 4, 5, 6, 7],
        [-1, 1, 2, 3, 4, 5, 6, 7], [1.5, 1, 2, 3, 4, 5, 6, 7],
        [np.nan, 1, 2, 3, 4, 5, 6, 7], [np.inf, 1, 2, 3, 4, 5, 6, 7],
        [2.0 ** 53 + 2, 1, 2, 3, 4, 5, 6, 7],
    ], ids=["dup", "0", "-1", "1.5", "nan", "inf", "2**53+2"])
    def test_a_bad_value_is_refused(self, bad):
        df = _A.copy()
        df["__dashs1"] = bad
        with pytest.raises(ValueError):
            dr._dash_take_sort_columns(df, _key_spec())

    def test_a_key_that_is_not_one_to_n_is_taken(self):
        df = _A.iloc[:3].copy()
        df["__dashs1"] = [10.0, 30.0, 20.0]
        out, keys = dr._dash_take_sort_columns(df, _key_spec())
        assert list(keys["__dashs1"]) == [10.0, 30.0, 20.0]
        assert "__dashs1" not in out.columns

    def test_an_unnamed_dashs_column_is_refused(self):
        df = _with(_A, __dashs1=range(1, 9), __dashs9=range(1, 9))
        out, _keys = dr._dash_take_sort_columns(df, _key_spec())
        assert "__dashs9" in out.columns
        with pytest.raises(ValueError, match="reserved"):
            dr._dash_take_qual_columns(out, _key_spec())

    def test_qualifier_columns_are_still_taken(self):
        df = _with(_A, __dashs1=range(1, 9), __dashq1=_quals(8, [1, 2]))
        spec = _key_spec()
        spec["graphs"][0]["qual_col"] = "__dashq1"
        out, keys = dr._dash_take_sort_columns(df, spec)
        out, masks = dr._dash_take_qual_columns(out, spec)
        assert list(out.columns) == list(_A.columns)
        assert list(np.flatnonzero(masks["__dashq1"]) + 1) == [1, 2]
        assert list(keys) == ["__dashs1"]

    def test_the_column_of_a_plot(self):
        spec = _key_spec("zz x", "__dashs3")
        assert dr._dash_sort_col_of(_plot("line", sortvars="zz x"),
                                    spec) == "__dashs3"
        assert dr._dash_sort_col_of(_plot("line"), spec) == ""
        with pytest.raises(ValueError):
            dr._dash_sort_col_of(_plot("line", sortvars="q"), spec)

    def test_labels_and_formats_lose_the_column(self):
        df = _with(_A, __dashs1=range(1, 9))
        spec = _key_spec()
        spec["build_options"]["formats"] = {"__dashs1": "%9.0g"}
        r = _saved(spec, df)
        for where in (list(r.df.columns), list(r.variable_labels),
                      list(r.value_label_names), list(r.formats),
                      list(r.numeric_formats), list(r.storage_types),
                      list(r.string_vars)):
            assert not [c for c in where if str(c).startswith("__dashs")]
        mod, _ = _served_module(spec, df)
        _sp, sdf, meta = mod._load_spec_and_data()
        assert not [c for c in sdf.columns if str(c).startswith("__dashs")]
        for k in ("var_labels", "val_label_names", "type_is_str",
                  "date_vars", "storage_types"):
            assert not [c for c in (meta.get(k) or {})
                        if str(c).startswith("__dashs")], k
        assert list(meta["sort_keys"]) == ["__dashs1"]


# ===========================================================================
# Both modes against Stata
# ===========================================================================

_KEY_OF = {"J3": "z", "J4": "s", "J5": "zz x", "J6": "z", "J7": "x"}
_SORT_OF = {"J2", "J6"}


def _orders_cases():
    if not os.path.exists(_FIXTURE):
        return [pytest.param(None, id="fixture-missing")]
    with open(_FIXTURE, encoding="utf-8") as fh:
        recs = json.load(fh)["orders"]
    return [pytest.param(r, id=r["id"]) for r in recs]


def _record_case(rec):
    truth = _truth()
    jid = rec["id"].split("-")[0]
    ptype = rec["type"]
    df = _A.copy()
    bo = {}
    opts = {"sort": "sort"} if (jid in _SORT_OF or
                                (jid == "J11" and rec["id"].endswith("-sort"))
                                ) else {}
    sortvars = None
    if jid in _KEY_OF:
        sortvars = _KEY_OF[jid]
        df["__dashs1"] = [float(v) for v in truth["ranks"][sortvars]]
        bo["sort_cols"] = {sortvars: "__dashs1"}
    qual = ""
    if jid == "J10":
        rows = (range(2, 7) if "-in-" in rec["id"]
                else [i + 1 for i, g in enumerate(_A["g"]) if g == 1])
        df["__dashq1"] = _quals(8, rows)
        qual = "__dashq1"
    xvar = "t" if jid == "J11" else "x"
    plot = _plot(ptype, xvar=xvar, options=opts, sortvars=sortvars)
    return _spec([plot], bo, qual_col=qual), df, xvar


class TestBothModesJoinAsTwowayDoes:

    @pytest.mark.parametrize("rec", _orders_cases())
    def test_saved_and_served_match_twoway(self, rec):
        if rec is None:
            _truth()
        spec, df, xvar = _record_case(rec)
        saved = [_obs(xs, _A, xvar) for f in _saved_figs(_saved(spec, df))
                 for xs in _joined(f, xvar)]
        served = [_obs(xs, _A, xvar) for f in _served_figs(_served(spec, df))
                  for xs in _joined(f, xvar)]
        assert saved and served
        for got in saved:
            assert got == rec["obs"], ("saved", got, rec["obs"])
        assert saved == served


# ===========================================================================
# A filter move
# ===========================================================================

_FOREIGN = ("Select", "Foreign")
_FOREIGN_DATA = [3350.0, 1800.0, 3100.0, 2010.0, 2650.0]
#: Descending price over the ten cars: the Foreign ones (2, 4, 6, 8, 10;
#: price 4749, 4816, 4453, 10372, 11385) join 10, 8, 4, 2, 6.
_FOREIGN_BY_PRICE = [2650.0, 2010.0, 1800.0, 3350.0, 3100.0]


def _move_spec(ptype, keyed):
    bo = {"filter": "foreign, type(dropdown)"}
    p = plot_for(ptype)
    df = tp._DF.copy()
    if keyed:
        p["sortvars"] = "nprice"
        bo["sort_cols"] = {"nprice": "__dashs1"}
        df["__dashs1"] = (-df["price"]).rank(method="first").astype(float)
    return tp._spec([p], bo), df


class TestAFilterMoveKeepsTheJoinOrder:

    @pytest.mark.parametrize("keyed", [False, True], ids=["data", "key"])
    @pytest.mark.parametrize("ptype", _JOIN)
    def test_saved_page_under_node(self, ptype, keyed):
        spec, df = _move_spec(ptype, keyed)
        r = _saved_move(spec, df, _FOREIGN)
        got = [xs for f in _saved_figs(r) for xs in _joined(f, "weight")]
        assert got
        want = _FOREIGN_BY_PRICE if keyed else _FOREIGN_DATA
        for xs in got:
            assert xs == want, (ptype, xs)

    @pytest.mark.parametrize("keyed", [False, True], ids=["data", "key"])
    @pytest.mark.parametrize("ptype", _JOIN)
    def test_served_app(self, ptype, keyed):
        spec, df = _move_spec(ptype, keyed)
        doc, _ = _served_move(spec, df, _FOREIGN)
        got = [xs for f in _served_figs(doc) for xs in _joined(f, "weight")]
        assert got
        want = _FOREIGN_BY_PRICE if keyed else _FOREIGN_DATA
        for xs in got:
            assert xs == want, (ptype, xs)


# ===========================================================================
# by() panels
# ===========================================================================

def _by_case(t, sub, so):
    rec = {r["id"]: r for r in _truth()["by"]}[f"J9-{t}-{sub}-{so}"]
    by = {"by": "g", "total": "g, total",
          "totalmissing": "g, total missing"}[sub]
    opts = {"sort": "sort"} if so == "sort" else {}
    return _spec([_plot(t, options=opts)], go={"by": by}), rec


def _panels(figs):
    out = set()
    for f in figs:
        for xs in _joined(f, "x"):
            out.add(tuple(_obs(xs, _A)))
    return out


class TestByPanelsJoinInDataOrder:

    @pytest.mark.parametrize("so", ["none", "sort"])
    @pytest.mark.parametrize("t", ["line", "rline"])
    @pytest.mark.parametrize("mode", ["saved", "served"])
    @pytest.mark.parametrize("sub", ["by", "total", "totalmissing"])
    def test_by(self, sub, mode, t, so):
        spec, rec = _by_case(t, sub, so)
        figs = (_saved_figs(_saved(spec, _A)) if mode == "saved"
                else _served_figs(_served(spec, _A)))
        assert _panels(figs) == {tuple(p) for p in rec["panels"]}

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_by_total(self, mode):
        self.test_by("total", mode, "line", "none")

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_by_total_missing(self, mode):
        self.test_by("totalmissing", mode, "line", "none")


# ===========================================================================
# Each bound of a range line keeps its own rows
# ===========================================================================

def _bounds(figs):
    return [_obs_b(xs) for f in figs for xs in _joined(f, "x")]


def _obs_b(xs):
    return [float(v) for v in xs]


class TestRangeBoundsKeepTheirOwnRows:

    def _rline(self):
        return _spec([_plot("rline", y2="y2a")])

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_rline_bounds(self, mode):
        rec = {r["id"]: r for r in _truth()["missing"]}["J8a-rline-none"]
        spec = self._rline()
        figs = (_saved_figs(_saved(spec, _B)) if mode == "saved"
                else _served_figs(_served(spec, _B)))
        got = _bounds(figs)
        assert got == [[float(v) for v in p] for p in rec["paths"]]
        assert got == [[2.0, 5.0, 6.0, 1.0, 7.0], [2.0, 3.0, 6.0, 1.0, 7.0]]

    def test_tsrline_bounds(self):
        src = ColumnDataSource({c: list(_B[c]) for c in ("x", "y", "y2a")})
        fig = figure()
        dr.GlyphMapper().map_tsrline(fig, src, "y", "y2a", "x", {})
        got = [[float(v) for v in g.data_source.data["x"]]
               for g in fig.renderers if isinstance(g.glyph, Line)]
        assert got == [[1.0, 2.0, 5.0, 6.0, 7.0], [1.0, 2.0, 3.0, 6.0, 7.0]]

    def test_rconnected_bounds(self):
        src = ColumnDataSource({c: list(_B[c]) for c in ("x", "y", "y2a")})
        fig = figure()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.GlyphMapper().map_rconnected(fig, src, "y", "y2a", "x", {})
        got = [sorted(float(v) for v in g.data_source.data["x"])
               for g in fig.renderers if isinstance(g.glyph, Line)]
        assert got == [[1.0, 2.0, 5.0, 6.0, 7.0], [1.0, 2.0, 3.0, 6.0, 7.0]]

    def test_rarea_both_bounds_missing_together(self):
        rec = {r["id"]: r for r in _truth()["missing"]}["J8b-rarea-none"]
        path = rec["paths"][0]
        lower = path[1:len(path) // 2]
        src = ColumnDataSource({c: list(_B[c]) for c in ("x", "y", "y2b")})
        fig = figure()
        dr.GlyphMapper().map_rarea(fig, src, "y", "y2b", "x", {})
        [area] = [g for g in fig.renderers if isinstance(g.glyph, VArea)]
        xs = [float(v) for v in area.data_source.data["x"]]
        assert xs == [float(v) for v in lower] == [2.0, 5.0, 6.0, 1.0, 7.0]

    _EMPTY_DF = pd.DataFrame({
        "x": [2.0, 5.0, 3.0, 6.0, 1.0, 7.0],
        "y": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
        "y2": [11.0, np.nan, np.nan, 41.0, 51.0, 61.0],
        "foreign": [0.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    })

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_a_move_that_empties_one_bound(self, mode):
        spec = _spec([_plot("rline")], {"filter": "foreign, type(dropdown)"})
        if mode == "saved":
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                r = _saved_move(spec, self._EMPTY_DF, _FOREIGN)
            msgs = [str(w.message) for w in caught]
            figs = _saved_figs(r)
        else:
            doc, msgs = _served_move(spec, self._EMPTY_DF, _FOREIGN)
            figs = _served_figs(doc)
        lines = [g for f in figs for g in f.renderers
                 if isinstance(g.glyph, Line)]
        assert len(lines) == 2
        assert len({id(g.data_source) for g in lines}) == 2
        assert not [m for m in msgs if "redrew" in m], msgs
        got = [[float(v) for v in g.data_source.data["x"]] for g in lines]
        assert got == [[5.0, 3.0], []], got


# ===========================================================================
# No rank column reaches the user
# ===========================================================================

class TestTheSortColumnsNeverReachTheUser:

    _BO = {"filter": "foreign, type(dropdown) || price, type(range)",
           "csv": "1", "sort_cols": {"nprice": "__dashs1"}}

    def _spec(self):
        p = plot_for("line")
        p["sortvars"] = "nprice"
        return tp._spec([p], dict(self._BO),
                        {"hover": "mpg weight price", "note": "n"})

    def _df(self):
        df = tp._DF.copy()
        df["__dashs1"] = (-df["price"]).rank(method="first").astype(float)
        return df

    def test_not_in_the_saved_page_at_all(self):
        _r, _m, page = _saved(self._spec(), self._df(), labels=True,
                              page=True)
        assert "__dashs" not in page
        assert "nprice" not in page

    def test_not_in_the_frame_or_its_labels(self):
        r = _saved(self._spec(), self._df(), labels=True)
        for where in (list(r.df.columns), list(r.variable_labels),
                      list(r.value_label_names), list(r.formats),
                      list(r.string_vars)):
            assert not [c for c in where if str(c).startswith("__dashs")]

    def test_not_in_a_tooltip(self):
        r = _saved(self._spec(), self._df(), labels=True)
        doc = _served(self._spec(), self._df(), labels=True)
        tips = []
        for fig in _saved_figs(r) + _served_figs(doc):
            for t in fig.select({"type": HoverTool}):
                tips.append(json.dumps(t.tooltips, default=str))
        assert tips
        assert not [t for t in tips if "__dashs" in t]

    def test_not_among_a_filters_choices(self):
        doc = _served(self._spec(), self._df(), labels=True)
        wid = tp._widgets_of(doc)
        assert wid
        for w in wid:
            assert "__dashs" not in json.dumps(
                getattr(w, "options", []), default=str)
            assert not str(getattr(w, "_dash_var", "")).startswith("__dashs")

    def test_not_in_the_csv_download(self):
        r = _saved(self._spec(), self._df(), labels=True)
        meta = dr._dash_csv_meta(r.df.columns, r.formats, {}, {}, {})
        assert not [c for c in meta["columns"] if c.startswith("__dashs")]

    def test_not_in_the_served_document_at_all(self):
        doc = _served(self._spec(), self._df(), labels=True)
        text = json.dumps(doc.to_json(), default=str)
        assert "__dashs" not in text

    def test_not_in_a_note_or_axis(self):
        _r, msgs, _p = _saved(self._spec(), self._df(), labels=True,
                              page=True)
        doc, smsgs = _served(self._spec(), self._df(), labels=True,
                             msgs=True)
        assert not [m for m in msgs + smsgs if "__dashs" in m]
        for fig in _saved_figs(_r) + _served_figs(doc):
            for ax in list(fig.xaxis) + list(fig.yaxis):
                assert "__dashs" not in str(ax.axis_label or "")


# ===========================================================================
# Cost
# ===========================================================================

class TestTheCostIsBounded:

    @pytest.mark.parametrize("case", ["map_line", "map_line_keyed",
                                      "map_area", "map_rline"])
    def test_a_million_rows(self, case):
        n = 1_000_000
        rng = np.random.default_rng(29)
        x = rng.permutation(n).astype(float)
        src = ColumnDataSource({"x": x, "y": x * 2.0, "y2": x * 2.0 + 1,
                                dr._ROW_ID_COLUMN: np.arange(n)})
        fig = figure()
        mp = dr.GlyphMapper()
        t0 = time.perf_counter()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if case == "map_line":
                mp.map_line(fig, src, "y", "x", {})
            elif case == "map_line_keyed":
                mp.map_line(fig, src, "y", "x", {}, order=x[::-1].copy())
            elif case == "map_area":
                mp.map_area(fig, src, "y", "x", {})
            else:
                mp.map_rline(fig, src, "y", "y2", "x", {})
        # 10 s, not 2 s (WP-29 closeout, 02oct2026).  Under Stata's Python
        # (bokeh 3.8.0) a million rows took 2.04-2.56 s alone (five runs)
        # and 5.1-6.2 s inside make test, because bokeh 3.8 validates the
        # 1M-item lists GlyphMapper._carry_cols builds with .tolist()
        # (profiled: 7.5 of 7.7 s); _join_order itself took 0.1 s.  10 s is
        # over 1.5 times the worst in-suite time and still fails a
        # quadratic join order, which a million rows cannot finish in.
        assert time.perf_counter() - t0 < 10.0


# ===========================================================================
# The fixture
# ===========================================================================

class TestTheFixture:

    def test_meta_stamp(self):
        meta = _truth()["_meta"]
        # Flipped: WP-32 regenerated the fixture; its generator now writes source.
        assert sorted(meta) == ["born_date", "dash_commit", "extracted",
                                "source", "stata_version"]
        assert all(str(v).strip() for v in meta.values())

    @pytest.mark.parametrize("jid", ["J3", "J4", "J5"])
    def test_the_rank_rule_is_twoways(self, jid):
        truth = _truth()
        rec = {r["id"]: r for r in truth["orders"]}[jid + "-line"]
        rank = truth["ranks"][_KEY_OF[jid]]
        by_rank = sorted(range(1, 9), key=lambda o: rank[o - 1])
        assert by_rank == rec["obs"]
