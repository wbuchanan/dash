"""The qualifier columns dash.ado exports select the rows, in both modes.

dash.ado evaluates every qualifier it writes -- a plot's, a graph's, a
KPI's, ``if`` and ``in`` together -- in Stata, once per distinct qualifier,
and exports the answer as a 0/1 byte column named ``__dashq<k>``; the graph,
plot or KPI object names it in ``"qual_col"`` and carries ``"if_expr":""``
and ``"in_expr":""``.  Both renderers select the rows whose column holds 1
and translate nothing (``_dash_take_qual_columns``, ``_dash_qualified_frame``
in dash_render.py).  The translation it replaces read a missing value, a
subscript, a function call and a date otherwise than Stata (BUGS.md, four
entries; test_qualifier_in_stata.cscript holds the rows drawn to Stata's
``count`` and ``levelsof`` through Stata itself).

This file holds the renderer's half of that contract:

* each mode selects a layer's, a graph's and a KPI's rows by the column,
  and never reaches the translator for a spec that names one;
* a served filter move intersects with the column: a layer's own qualifier
  survives the move (the reported case of test_served_filter_move.py, its
  ``in 40/60`` now a column);
* the column is validated before use -- a name dash writes, present in the
  data, 0 and 1 only -- and a column with the reserved prefix that the spec
  does not name is refused;
* no qualifier column ever reaches the user: not a source, a tooltip, a
  filter's choices, the CSV download, the KPI recompute's payload, a note or
  an axis;
* the adversarial cases (CLAUDE.md rule 18): a qual_col naming a user
  variable, an injection in the name, a value other than 0/1, a filter on a
  qualifier column, and many columns at once.
"""
import json
import os
import re
import sys
import time
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.models import HoverTool, Select

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

from conftest import exec_app  # noqa: E402
import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
import test_served_filter_move as sfm  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402


# ===========================================================================
# Helpers
# ===========================================================================

def _with_quals(df, **cols):
    """*df* with each named qualifier column: ``name=rows`` (1-based
    observation numbers that hold 1)."""
    out = df.copy()
    for name, rows in cols.items():
        keep = set(rows)
        out[name] = [1.0 if i + 1 in keep else 0.0 for i in range(len(out))]
    return out


def _graph(plots, qual_col="", go=None):
    """One graph named g1 as dash.ado writes it: the qualifier as a column,
    no text."""
    return ("g1", plots, go or {},
            {"if_expr": "", "in_expr": "", "qual_col": qual_col})


def _plot(ptype="scatter", qual_col="", **extra):
    return plot_for(ptype, if_expr="", in_expr="", qual_col=qual_col,
                    **extra)


def _rows_drawn(fig, df):
    """The observations (1-based) a figure's first scatter draws, read by
    its (mpg, weight) pairs, which are unique in the parity frame."""
    prof = tp._figure_profile(fig)
    sc = [g for g in prof["glyphs"] if g.get("coords")][0]
    xs, ys = sc["coords"]["x"][1], sc["coords"]["y"][1]
    return sorted(int(df.index[(df["weight"] == x) & (df["mpg"] == y)][0]) + 1
                  for x, y in zip(xs, ys))


@pytest.fixture
def parity_quals(monkeypatch):
    """The parity frame with two qualifier columns: __dashq1 holds rows
    2, 4, 6, 8, 10 (foreign, as `if foreign' selects them); __dashq2 rows
    1-3 (`in 1/3')."""
    df = _with_quals(tp._DF, __dashq1=[2, 4, 6, 8, 10], __dashq2=[1, 2, 3])
    monkeypatch.setattr(tp, "_DF", df)
    return tp._DF


def _boom(*_a, **_k):
    raise AssertionError("the translator was reached for a spec that names "
                         "a qualifier column")


# ===========================================================================
# The contract's functions
# ===========================================================================

class TestTheNamesASpecCarries:

    def test_each_name_once_in_order(self):
        spec = tp._spec(graphs=[_graph([_plot(qual_col="__dashq2"),
                                        _plot(qual_col="__dashq1")],
                                       "__dashq1")],
                        kpis=[tp._kpi(qual_col="__dashq3")])
        assert dr._dash_qual_cols_named(spec) == [
            "__dashq1", "__dashq2", "__dashq3"]

    def test_no_qualifier_names_nothing(self):
        assert dr._dash_qual_cols_named(tp._spec([_plot()])) == []

    @pytest.mark.parametrize("bad", [
        "mpg", "__dashq0", "__dashq01", "__dashq123456", "__dashq1 ",
        "__dashq1\n", "__dashq1') | (1", "__DASHQ1", 5, ["__dashq1"],
    ])
    def test_a_name_dash_does_not_write_is_refused(self, bad):
        spec = tp._spec(graphs=[_graph([_plot()], bad)])
        with pytest.raises(ValueError, match="qualifier column"):
            dr._dash_qual_cols_named(spec)


class TestTakingTheColumnsOut:

    def _spec(self):
        return tp._spec(graphs=[_graph([_plot(qual_col="__dashq2")],
                                       "__dashq1")])

    def test_the_masks_hold_statas_rows_and_the_frame_loses_the_columns(
            self, parity_quals):
        df, masks = dr._dash_take_qual_columns(parity_quals, self._spec())
        assert not [c for c in df.columns if c.startswith("__dashq")]
        assert list(df.columns) == list(tp._DF.columns[:-2])
        assert list(np.flatnonzero(masks["__dashq1"]) + 1) == [2, 4, 6, 8, 10]
        assert list(np.flatnonzero(masks["__dashq2"]) + 1) == [1, 2, 3]
        assert masks["__dashq1"].index.equals(df.index)

    def test_a_column_the_data_lack_is_refused(self, parity_quals):
        spec = tp._spec(graphs=[_graph([_plot(qual_col="__dashq2")],
                                       "__dashq1")],
                        kpis=[tp._kpi(qual_col="__dashq7")])
        with pytest.raises(ValueError, match="not in the data"):
            dr._dash_take_qual_columns(parity_quals, spec)

    @pytest.mark.parametrize("value", [2.0, -1.0, 0.5, np.nan, "x"])
    def test_a_value_other_than_0_and_1_is_refused(self, parity_quals,
                                                   value):
        df = parity_quals.astype({"__dashq1": object})
        df.loc[3, "__dashq1"] = value
        with pytest.raises(ValueError, match="other than 0"):
            dr._dash_take_qual_columns(df, self._spec())

    def test_a_reserved_column_the_spec_does_not_name_is_refused(
            self, parity_quals):
        spec = tp._spec(graphs=[_graph([_plot()], "__dashq1")])
        with pytest.raises(ValueError, match="reserved"):
            dr._dash_take_qual_columns(parity_quals, spec)

    def test_a_users_variable_is_never_read_as_one(self):
        """A qual_col naming an ordinary variable is refused by name before
        the data are read (adversarial: auth bypass of the contract)."""
        spec = tp._spec(graphs=[_graph([_plot()], "foreign")])
        with pytest.raises(ValueError, match="qualifier column"):
            dr._dash_take_qual_columns(tp._DF, spec)

    def test_the_mask_of_an_object(self, parity_quals):
        _df, masks = dr._dash_take_qual_columns(parity_quals, self._spec())
        assert dr._dash_qual_mask({"qual_col": ""}, masks) is None
        assert dr._dash_qual_mask({}, masks) is None
        assert dr._dash_qual_mask({"qual_col": "__dashq1"}, masks) is \
            masks["__dashq1"]
        with pytest.raises(ValueError):
            dr._dash_qual_mask({"qual_col": "__dashq9"}, masks)

    def test_the_frame_is_selected_by_index_and_the_text_ignored(
            self, parity_quals):
        df, masks = dr._dash_take_qual_columns(parity_quals, self._spec())
        # A slice first, as a filter move or a by() panel hands one on.
        part = df.iloc[3:]
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            out = dr._dash_qualified_frame(part, "this is not Stata", "1/2",
                                           qual=masks["__dashq1"])
        assert list(out.index + 1) == [4, 6, 8, 10]
        lay = dr._dash_layer_frame(df, part, "nor this", "9/9",
                                   qual=masks["__dashq2"])
        assert list(lay.index) == []


# ===========================================================================
# Both modes select by the column and never translate
# ===========================================================================

class TestBothModesSelectByTheColumn:

    def _spec(self, kpis=()):
        # A graph qualifier (foreign) and a second layer's own (in 1/3),
        # as dash.ado writes `dash (scatter mpg weight) (scatter mpg weight
        # in 1/3) if foreign`: its rows are both columns' -- row 2.
        return tp._spec(graphs=[_graph(
            [_plot(), _plot(qual_col="__dashq2")], "__dashq1")],
            kpis=list(kpis))

    def test_the_saved_page(self, parity_quals, monkeypatch):
        monkeypatch.setattr(dr, "_stata_if_to_pandas", _boom)
        monkeypatch.setattr(dr, "_validate_if_expr", _boom)
        r, msgs = tp._standalone(self._spec())
        (fig,) = [f for f in r.figures.values()]
        prof = tp._figure_profile(fig)
        drawn = [g for g in prof["glyphs"] if g.get("coords")]
        assert len(drawn) == 2
        assert not [m for m in msgs if "skipped" in m]
        rows = []
        for g in drawn:
            xs, ys = g["coords"]["x"][1], g["coords"]["y"][1]
            rows.append(sorted(
                int(tp._DF.index[(tp._DF["weight"] == x)
                                 & (tp._DF["mpg"] == y)][0]) + 1
                for x, y in zip(xs, ys)))
        assert rows == [[2, 4, 6, 8, 10], [2]]

    def test_the_served_app(self, parity_quals):
        # The app copies its helpers from this module's source, so the
        # translator is replaced in the app itself, in the next test.
        doc, msgs = tp._served(self._spec())
        (fig,) = sfm._figures(doc)
        prof = tp._figure_profile(fig)
        drawn = [g for g in prof["glyphs"] if g.get("coords")]
        rows = []
        for g in drawn:
            xs, ys = g["coords"]["x"][1], g["coords"]["y"][1]
            rows.append(sorted(
                int(tp._DF.index[(tp._DF["weight"] == x)
                                 & (tp._DF["mpg"] == y)][0]) + 1
                for x, y in zip(xs, ys)))
        assert rows == [[2, 4, 6, 8, 10], [2]]
        assert not [m for m in msgs if "skipped" in m]

    def test_the_served_app_has_no_translation_to_reach(self, parity_quals,
                                                       tmp_path):
        """The generated app's own copies: its translator replaced by one
        that fails, and the session still draws."""
        sp, dp = tp._write(self._spec())[1:]
        ap = os.path.join(str(tmp_path), "app.py")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(ap)
        with open(ap, encoding="utf-8") as fh:
            src = fh.read()
        attach = "if __name__ != '__main__':\n    make_document(curdoc())"
        ns = {"__name__": "_qc_app"}
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            exec_app(src.replace(attach, "pass"), "_qc_app.py", ns)
        ns["_stata_if_to_pandas"] = _boom
        ns["_validate_if_expr"] = _boom
        from bokeh.document import Document
        doc = Document()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ns["make_document"](doc)
        assert sfm._figures(doc)

    def test_a_kpi_reads_its_column_in_both_modes(self, parity_quals):
        # mean(mpg) over rows 1-3: (22 + 17 + 25) / 3.
        spec = self._spec(kpis=[tp._kpi(stat="mean", var="mpg",
                                        fmt="%9.4f",
                                        qual_col="__dashq2")])
        r, _ = tp._standalone(spec)
        saved = tp._kpi_card(r.kpi_divs["k1"].text)
        doc, _ = tp._served(spec)
        served = sfm._served_cards(doc)
        assert saved[1] == served["k1"] == "21.3333"


# ===========================================================================
# A served filter move intersects with the column
# ===========================================================================

class TestAServedFilterMoveKeepsALayersColumn:
    """test_served_filter_move.py's reported case, as dash.ado now writes
    it: `(scatter mpg weight in 40/60) (lfit mpg weight in 40/60)` with the
    dropdown on Foreign, each layer's in a column.  Stata, 24sep2026:
    ``count if foreign == 1 in 40/60`` is 8, observations 53 to 60, and
    ``regress mpg weight if foreign == 1 in 40/60`` gives 27.1737 at weight
    2020 and 19.352 at 2830."""

    @pytest.fixture(autouse=True)
    def _on_auto(self, monkeypatch):
        auto = _with_quals(sfm._auto(), __dashq1=range(40, 61))
        monkeypatch.setattr(tp, "_DF", auto)

    _SPEC = tp._spec(graphs=[_graph([_plot("scatter", "__dashq1"),
                                     _plot("lfit", "__dashq1")])],
                     build_options={"filter": "foreign, type(dropdown)"})

    def test_before_and_after_the_move(self):
        doc, msgs = tp._served(self._SPEC)
        (fig,) = sfm._figures(doc)
        before, _ = sfm.TestTheReportedCase._observations(
            tp._figure_profile(fig))
        assert before == list(range(40, 61))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            sfm._move(doc, "Select", "Foreign")
        obs, ends = sfm.TestTheReportedCase._observations(
            tp._figure_profile(fig))
        assert obs == list(range(53, 61)), obs
        assert ends == ((2020.0, 2830.0), (27.1737, 19.352)), ends

    def test_the_graphs_column_survives_a_move_too(self, monkeypatch):
        spec = tp._spec(graphs=[_graph([_plot("scatter")], "__dashq1")],
                        build_options={"filter": "foreign, type(dropdown)"})
        doc, _ = tp._served(spec)
        (fig,) = sfm._figures(doc)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            sfm._move(doc, "Select", "Foreign")
        sc = tp._figure_profile(fig)["glyphs"][0]
        auto = sfm._auto()
        obs = sorted(int(auto.index[(auto["weight"] == w)
                                    & (auto["mpg"] == m)][0]) + 1
                     for w, m in zip(sc["coords"]["x"][1],
                                     sc["coords"]["y"][1]))
        assert obs == list(range(53, 61)), obs

    def test_the_saved_page_draws_the_same_rows_first(self):
        r, _ = tp._standalone(self._SPEC)
        (fig,) = list(r.figures.values())
        obs, _ends = sfm.TestTheReportedCase._observations(
            tp._figure_profile(fig))
        assert obs == list(range(40, 61))


# ===========================================================================
# A by(, total) graph's Total panel reads its own column
# ===========================================================================

class TestATotalPanelReadsItsOwnColumn:
    """twoway evaluates a by() graph's qualifiers with the data sorted on
    the by() variables, and its Total panel's in the data's own order
    (bygraph_g.class; measured 24sep2026 from each panel's serset,
    test_qualifier_in_stata.cscript QS-16).  dash.ado writes the groups'
    column as "qual_col" and the Total panel's as "qual_col_total" on each
    object whose qualifier can depend on that order.  Here __dashq1 (the
    groups') holds rows 1 and 2, and __dashq2 (the Total panel's) rows
    5, 6 and 7: the groups draw 1 (Domestic) and 2 (Foreign), the Total
    panel 5, 6 and 7, in both modes and after a served filter move."""

    @pytest.fixture(autouse=True)
    def _quals(self, monkeypatch):
        df = _with_quals(tp._DF, __dashq1=[1, 2], __dashq2=[5, 6, 7])
        monkeypatch.setattr(tp, "_DF", df)

    @staticmethod
    def _spec(build_options=None):
        plot = _plot(qual_col="__dashq1")
        plot["qual_col_total"] = "__dashq2"
        g = list(_graph([plot], "__dashq1", {"by": "foreign, total"}))
        g[3] = dict(g[3], qual_col_total="__dashq2")
        return tp._spec(graphs=[tuple(g)], build_options=build_options)

    @staticmethod
    def _by_label(figs):
        out = {}
        for f in figs:
            # Flipped (WP-30 P1.15a): split the label off "title — label";
            # twoway draws it as a row of its own (by_panel_probe).
            from by_panel_probe import panel_label
            label = panel_label(f)
            out[label] = _rows_drawn(f, tp._DF)
        return out

    def test_the_total_spec_swaps_the_columns(self):
        g = self._spec()["graphs"][0]
        t = dr._dash_total_spec(g)
        assert t is not g
        assert t["qual_col"] == "__dashq2"
        assert t["plots"][0]["qual_col"] == "__dashq2"
        assert "qual_col_total" not in t and \
            "qual_col_total" not in t["plots"][0]
        # g itself is untouched.
        assert g["qual_col"] == "__dashq1"
        assert g["plots"][0]["qual_col_total"] == "__dashq2"

    def test_a_graph_without_one_is_its_own_total_spec(self):
        g = tp._spec(graphs=[_graph([_plot(qual_col="__dashq1")],
                                    "__dashq1")])["graphs"][0]
        assert dr._dash_total_spec(g) is g
        assert dr._dash_total_spec(None) is None

    def test_both_names_are_read(self):
        assert dr._dash_qual_cols_named(self._spec()) == [
            "__dashq1", "__dashq2"]

    @pytest.mark.parametrize("bad", [
        "mpg", "__dashq0", "__dashq1') | (1", "__dashq1\n", 7, ["__dashq2"],
    ])
    def test_a_total_name_dash_does_not_write_is_refused(self, bad):
        """Adversarial: a hand-written spec cannot make the Total panel
        read a user's variable, or smuggle text through the name."""
        spec = self._spec()
        spec["graphs"][0]["qual_col_total"] = bad
        with pytest.raises(ValueError, match="qualifier column"):
            dr._dash_qual_cols_named(spec)
        with pytest.raises(ValueError, match="qualifier column"):
            dr._dash_take_qual_columns(tp._DF, spec)

    def test_the_saved_page(self):
        r, _ = tp._standalone(self._spec())
        got = self._by_label(r.figures.values())
        assert got == {"Domestic": [1], "Foreign": [2], "Total": [5, 6, 7]}

    def test_the_served_app(self):
        doc, _ = tp._served(self._spec())
        got = self._by_label(sfm._figures(doc))
        assert got == {"Domestic": [1], "Foreign": [2], "Total": [5, 6, 7]}

    def test_a_served_filter_move_keeps_the_total_column(self):
        doc, _ = tp._served(self._spec(
            build_options={"filter": "foreign, type(dropdown)"}))
        figs = sfm._figures(doc)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            sfm._move(doc, "Select", "Foreign")
        got = self._by_label(figs)
        assert got["Total"] == [6], got
        assert got["Foreign"] == [2], got

    def test_a_total_panel_with_rows_when_no_group_has_one(self):
        """twoway draws the Total panel alone when the groups' column
        selects no row and the Total panel's does (RunGraph skips each
        empty group, then draws Total)."""
        df = _with_quals(tp._DF.drop(columns=["__dashq1", "__dashq2"]),
                         __dashq1=[], __dashq2=[5, 6, 7])
        tp._DF = df
        r, _ = tp._standalone(self._spec())
        assert self._by_label(r.figures.values()) == {"Total": [5, 6, 7]}
        doc, _ = tp._served(self._spec())
        assert self._by_label(sfm._figures(doc)) == {"Total": [5, 6, 7]}


# ===========================================================================
# No qualifier column reaches the user
# ===========================================================================

class TestTheColumnsNeverReachTheUser:

    _BO = {"filter": "foreign, type(dropdown) || price, type(range)",
           "csv": "1"}

    def _spec(self):
        return tp._spec(
            graphs=[_graph([_plot(qual_col="__dashq2")], "__dashq1",
                           go={"hover": "mpg weight price",
                               "note": "n"})],
            kpis=[tp._kpi(qual_col="__dashq1", update="both")],
            build_options=self._BO)

    def _saved(self):
        r, msgs, page = tp._standalone_page(self._spec())
        return r, msgs, page

    def test_not_in_the_saved_page_at_all(self, parity_quals):
        _r, _m, page = self._saved()
        assert "__dashq" not in page

    def test_not_in_the_frame_or_its_labels(self, parity_quals):
        r, _m, _p = self._saved()
        for where in (list(r.df.columns), list(r.variable_labels),
                      list(r.value_label_names), list(r.formats),
                      list(r.string_vars)):
            assert not [c for c in where if str(c).startswith("__dashq")]

    def test_not_in_a_tooltip(self, parity_quals):
        r, _m, _p = self._saved()
        doc, _ = tp._served(self._spec())
        tips = []
        for fig in list(r.figures.values()) + sfm._figures(doc):
            for t in fig.select({"type": HoverTool}):
                tips.append(json.dumps(t.tooltips, default=str))
        assert tips
        assert not [t for t in tips if "__dashq" in t]

    def test_not_among_a_filters_choices(self, parity_quals):
        doc, _ = tp._served(self._spec())
        wid = tp._widgets_of(doc)
        assert wid
        for w in wid:
            assert "__dashq" not in json.dumps(
                getattr(w, "options", []), default=str)
            assert not str(getattr(w, "_dash_var", "")).startswith("__dashq")

    def test_a_filter_on_a_qualifier_column_draws_no_widget(
            self, parity_quals):
        spec = self._spec()
        spec["build_options"]["filter"] = "__dashq1, type(dropdown)"
        r, _m, page = tp._standalone_page(spec)
        assert "__dashq" not in page
        doc, _ = tp._served(spec)
        assert not tp._widgets_of(doc)

    def test_not_in_the_csv_download(self, parity_quals):
        r, _m, _p = self._saved()
        meta = dr._dash_csv_meta(r.df.columns, r.formats, {}, {}, {})
        assert not [c for c in meta["columns"] if c.startswith("__dashq")]
        doc, _ = tp._served(self._spec())
        assert "__dashq" not in json.dumps(doc.to_json(), default=str)

    def test_not_in_the_served_document_at_all(self, parity_quals):
        doc, _ = tp._served(self._spec())
        assert "__dashq" not in json.dumps(doc.to_json(), default=str)

    def test_not_in_a_note_or_axis(self, parity_quals):
        r, msgs, _p = self._saved()
        doc, smsgs = tp._served(self._spec())
        assert not [m for m in msgs + smsgs if "__dashq" in m]
        for fig in list(r.figures.values()) + sfm._figures(doc):
            for ax in list(fig.xaxis) + list(fig.yaxis):
                assert "__dashq" not in str(ax.axis_label or "")


# ===========================================================================
# Adversarial (CLAUDE.md rule 18)
# ===========================================================================

class TestAdversarialQualifierColumns:

    @pytest.mark.parametrize("name", [
        "foreign",                       # a user's variable, read as a mask
        "__dashq1) | (foreign",          # an injection in the name
        "__dashq" + "9" * 5000,          # an exhausting name
    ])
    def test_both_modes_refuse_a_bad_name(self, parity_quals, name):
        spec = tp._spec(graphs=[_graph([_plot()], name)])
        with pytest.raises(ValueError, match="qualifier column"):
            tp._standalone(spec)
        with pytest.raises(ValueError, match="qualifier column"):
            tp._served(spec)

    def test_both_modes_refuse_a_value_other_than_0_and_1(self,
                                                          monkeypatch):
        df = _with_quals(tp._DF, __dashq1=[1, 2])
        df.loc[4, "__dashq1"] = 7.0
        monkeypatch.setattr(tp, "_DF", df)
        spec = tp._spec(graphs=[_graph([_plot()], "__dashq1")])
        with pytest.raises(ValueError, match="other than 0"):
            tp._standalone(spec)
        with pytest.raises(ValueError, match="other than 0"):
            tp._served(spec)

    def test_many_columns_are_read_in_linear_time(self):
        """Resource exhaustion: 2,000 columns over 20,000 rows are taken
        out in one pass each, not a pass per row."""
        n, k = 20000, 2000
        rng = np.random.default_rng(27)
        cols = {"x": rng.random(n)}
        for j in range(1, k + 1):
            cols["__dashq%d" % j] = (rng.random(n) > 0.5).astype(float)
        df = pd.DataFrame(cols)
        spec = {"graphs": [{"plots": [{"qual_col": "__dashq%d" % j}
                                      for j in range(1, k + 1)]}]}
        t0 = time.perf_counter()
        out, masks = dr._dash_take_qual_columns(df, spec)
        took = time.perf_counter() - t0
        assert list(out.columns) == ["x"] and len(masks) == k
        assert took < 20.0, took
