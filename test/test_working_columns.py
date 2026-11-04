"""dash's working columns never clash with the user's variables (WP-35 DT-19).

twoway draws data holding a variable named ``__dashq1`` (rc 0); dash refused
it, r(110), because its own qualifier, join-order, time-series and weight
columns were named ``__dashq<k>``, ``__dashs<k>``, ``__dasht<k>`` and
``__dashw<k>`` in the user's frame, and both renderers refused any column
named with ``__dash`` the spec did not name.  Now each export picks a prefix
no variable of the data (nor, on a build, a value-label set) starts with --
``__dash``, else ``__dsh1_``, ``__dsh2_`` ... (``_dash_reserved_prefix``,
dash_parse.mata) -- names every column it makes with it, and writes it to
the spec as ``"_dash_prefix"``, which both renderers read
(``_dash_prefix_of``).  test_wp35_truth.cscript S08 (Q3508-1..3) measures
the Stata side live.
"""
import itertools
import json
import os
import re
import sys
import warnings

import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import render_models  # noqa: E402
from conftest import drawn_renderers  # noqa: E402
from test_adversarial_matrix import _load_app, _write_inputs  # noqa: E402

_SEQ = itertools.count()


def _read(name):
    with open(os.path.join(_ROOT, name), encoding="utf-8") as fh:
        return fh.read()


def _code_lines(text, comment):
    """The lines of *text* less their comments (``//`` for Stata and Mata,
    ``#`` for Python) and the ``*!`` header lines."""
    out = []
    for line in text.splitlines():
        if line.lstrip().startswith("*!"):
            continue
        out.append(line.split(comment, 1)[0])
    return out


class TestThePrefix:
    def test_reserved_prefix_is_defined(self):
        mata = _read("dash_parse.mata")
        assert re.search(r"^string scalar _dash_reserved_prefix\("
                         r"string rowvector names\)$", mata, re.M)
        ado = _read("dash.ado")
        # One continuation line of _needed, and one call per route.
        assert re.search(r"^ {8}_dash_reserved_prefix _dash_esample_sub "
                         r"_dash_expr_words ///$", ado, re.M)
        calls = re.findall(r"_dash_reserved_prefix\(tokens\(st_local\("
                           r"\"_rp_all\"\)\)\)", ado)
        assert len(calls) == 2
        # The spec carries the prefix on both routes.
        assert ado.count('"_dash_prefix": "`_dash_rp\'"') == 1
        assert ado.count('"_dash_prefix":"`_dash_rp\'"') == 1


class TestNoClashRefusal:
    def test_the_r110_refusals_are_gone(self):
        ado = _read("dash.ado")
        assert "reserved for the columns dash makes" not in ado
        assert not re.search(r"unab _d[qstw]_clash", ado)


class TestNoLiteral:
    def test_no_reserved_literal_outside_the_definitions(self):
        """No Stata-made working column is named with a ``__dash``
        literal: each is formed from the export's prefix (Mata:
        ``_dash_col_pfx()``; dash.ado: the generators' ``prefix`` argument
        and the local ``_dash_rp``), and each renderer pattern reads the
        spec's prefix (``_dash_col_name_re``)."""
        bad = []
        for name in ("dash.ado", "dash_parse.mata"):
            for i, line in enumerate(_code_lines(_read(name), "//"), 1):
                # __dashq`k', "__dasht" + ..., __dashs*, __dashm`k' ...
                if re.search(r"__dash[qstwml](`|\"|\*)", line):
                    bad.append("%s:%d: %s" % (name, i, line.strip()))
        for i, line in enumerate(_code_lines(_read("dash_render.py"), "#"),
                                 1):
            if re.search(r"__dash[qstwm]\[1-9\]", line) and not re.match(
                    r"_DASH_(QUAL|TSOP|SORT|FRAME_COL)_(NAME_)?RE = ", line):
                bad.append("dash_render.py:%d: %s" % (i, line.strip()))
        assert bad == []


# ---------------------------------------------------------------------------
# The renderers
# ---------------------------------------------------------------------------

def _user_df():
    """auto-like rows with a user variable named like a qualifier column."""
    return pd.DataFrame({
        "__dashq1": [22.0, 17.0, 25.0, 30.0],
        "weight": [2930.0, 3350.0, 2200.0, 1800.0],
        "__dsh1_q1": [1, 0, 1, 1],
    })


def _user_spec():
    plot = {"type": "scatter", "yvar": "__dashq1", "xvar": "weight",
            "options": {}, "if_expr": "", "in_expr": "",
            "qual_col": "__dsh1_q1"}
    return {"graphs": [{"plots": [plot],
                        "graph_options": {"name": "s08", "title": "s08"},
                        "if_expr": "", "in_expr": ""}],
            "kpis": [], "_dash_prefix": "__dsh1_",
            "build_options": {"layout": "auto", "link": "", "theme": "",
                              "title": "", "subtitle": "", "tabs": "",
                              "filter_position": "top", "registry": "s08"}}


def _scatter_ys(fig):
    [sc] = [x for x in drawn_renderers(fig)
            if type(x.glyph).__name__ == "Scatter"]
    return list(sc.data_source.data["__dashq1"]), sc.data_source.data


class TestTheRenderer:
    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_both_modes_draw_a_user_dash_column(self, tmp_path, mode):
        sp, dp = _write_inputs(tmp_path, _user_spec(), df=_user_df())
        if mode == "saved":
            r = dr.DashRenderer(sp, dp)
            render_models(r)
            [fig] = list(r.figures.values())
        else:
            ap = os.path.join(str(tmp_path), "app_%d.py" % next(_SEQ))
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                dr.ServerAppBuilder(sp, dp).build(ap)
            with open(ap, encoding="utf-8") as fh:
                ns = _load_app(fh.read(), "wc_%d" % next(_SEQ))
            doc = Document()
            ns["make_document"](doc)
            [fig] = list(doc.select({"type": type(figure())}))
        ys, data = _scatter_ys(fig)
        # The user's values on the rows the qualifier column keeps; the
        # qualifier column itself never reaches the source.
        assert ys == [22.0, 25.0, 30.0]
        assert "__dsh1_q1" not in data

    def test_a_column_under_the_specs_prefix_is_still_refused(self, tmp_path):
        df = _user_df()
        df["__dsh1_zz"] = [1.0, 2.0, 3.0, 4.0]
        sp, dp = _write_inputs(tmp_path, _user_spec(), df=df)
        with pytest.raises(ValueError, match="__dsh1_"):
            dr.DashRenderer(sp, dp)

    def test_split_columns_take_the_prefix(self):
        ent = {"g2": {"foreign": {"col": "__dsh1_m1", "frame": "c2"}}}
        spec = {"_dash_prefix": "__dsh1_",
                "build_options": {"frame_cols": ent}}
        assert dr._dash_frame_cols_named(spec) == ent
        old = {"g2": {"foreign": {"col": "__dashm1", "frame": "c2"}}}
        with pytest.raises(ValueError):
            dr._dash_frame_cols_named(
                {"_dash_prefix": "__dsh1_",
                 "build_options": {"frame_cols": old}})
        # No prefix: 33-07's names, as its tests pin.
        assert dr._dash_frame_cols_named(
            {"build_options": {"frame_cols": old}}) == old

    def test_the_prefix_of_a_spec(self):
        assert dr._dash_prefix_of({}) == "__dash"
        assert dr._dash_prefix_of({"_dash_prefix": ""}) == "__dash"
        assert dr._dash_prefix_of({"_dash_prefix": "__dsh12_"}) == "__dsh12_"
        for bad in ("__dsh0_", "__dshx_", "x", 3, "__dash_", "__dsh1"):
            with pytest.raises(ValueError):
                dr._dash_prefix_of({"_dash_prefix": bad})

    def test_the_name_patterns_read_the_prefix(self):
        spec = {"_dash_prefix": "__dsh2_"}
        q = dr._dash_col_name_re(spec, "q", 4)
        assert q.match("__dsh2_q1") and q.match("__dsh2_q99999")
        assert not q.match("__dashq1") and not q.match("__dsh2_q0")
        assert not q.match("__dsh2_q100000")
        assert dr._dash_col_name_re({}, "t", 3).match("__dasht12")
        # The spec's own names are validated against it.
        g = {"plots": [], "graph_options": {"name": "g"},
             "qual_col": "__dashq1"}
        with pytest.raises(ValueError, match="__dsh2_q"):
            dr._dash_qual_cols_named({"_dash_prefix": "__dsh2_",
                                      "graphs": [g]})
        g["qual_col"] = "__dsh2_q3"
        assert dr._dash_qual_cols_named({"_dash_prefix": "__dsh2_",
                                         "graphs": [g]}) == ["__dsh2_q3"]
        ts = {"__dsh2_t1": {"expr": "L.close", "label": "close, L"},
              "__dsh2_w1": {"expr": "price+1", "label": "price+1"}}
        assert dr._dash_tsop_cols_named(
            {"_dash_prefix": "__dsh2_",
             "build_options": {"ts_cols": ts}}) == ts
        assert dr._dash_sort_cols_named(
            {"_dash_prefix": "__dsh2_",
             "build_options": {"sort_cols": {"mpg": "__dsh2_s1"}}}) == {
                 "mpg": "__dsh2_s1"}


# ---------------------------------------------------------------------------
# The renderers' own columns (TR-35-08.4): every name a renderer makes is
# formed from the spec's prefix, so a user variable named like one of them
# under the default prefix is data in both modes.
# ---------------------------------------------------------------------------

def _clash_df():
    return pd.DataFrame({
        "mpg": [22.0, 17.0, 25.0, 30.0],
        "weight": [2930.0, 3350.0, 2200.0, 1800.0],
        "__dash_row__": [101.0, 102.0, 103.0, 104.0],
        "__dash_mlabel_mpg": [1.0, 2.0, 3.0, 4.0],
        "__dashu_x": [5.0, 6.0, 7.0, 8.0],
    })


def _clash_spec():
    plot = {"type": "scatter", "yvar": "mpg", "xvar": "weight",
            "options": {"mlabel": "mpg"}, "if_expr": "", "in_expr": ""}
    return {"graphs": [{"plots": [plot],
                        "graph_options": {"name": "s08", "title": "s08",
                                          "hover": "__dash_row__ __dash_mlabel_mpg"},
                        "if_expr": "", "in_expr": ""}],
            "kpis": [], "_dash_prefix": "__dsh1_",
            "build_options": {"layout": "auto", "link": "", "theme": "",
                              "title": "", "subtitle": "", "tabs": "",
                              "filter_position": "top", "registry": "s08"}}


def _figure_of(tmp_path, mode, spec, df):
    sp, dp = _write_inputs(tmp_path, spec, df=df)
    if mode == "saved":
        r = dr.DashRenderer(sp, dp)
        render_models(r)
        [fig] = list(r.figures.values())
        return fig
    ap = os.path.join(str(tmp_path), "app_%d.py" % next(_SEQ))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(ap)
    with open(ap, encoding="utf-8") as fh:
        ns = _load_app(fh.read(), "wc_%d" % next(_SEQ))
    doc = Document()
    ns["make_document"](doc)
    [fig] = list(doc.select({"type": type(figure())}))
    return fig


class TestTheRendererNames:
    def test_row_id_of_a_spec(self):
        assert dr._dash_row_id({}) == "__dash_row__" == dr._ROW_ID_COLUMN
        assert dr._dash_row_id({"_dash_prefix": "__dsh1_"}) == "__dsh1__row__"

    def test_the_module_of_a_prefix(self):
        m = dr._dash_module_for({"_dash_prefix": "__dsh1_"})
        assert m is dr._dash_module_for({"_dash_prefix": "__dsh1_"})
        assert dr._dash_module_for({}) is sys.modules[dr.__name__]
        assert m._ROW_ID_COLUMN == "__dsh1__row__"
        assert m._DASH_MLABEL_PREFIX == "__dsh1__mlabel_"
        assert m._DASH_USER_ALIAS_PREFIX == "__dsh1_u_"
        assert m._DASH_CODE_TEXT_PREFIX == "__dsh1_t_"
        assert m._DASH_TABLE_PREFIX == "__dsh1__tbl_"
        assert m._DASH_CVAR_PREFIX == "__dsh1__cvar"
        assert m._DASH_JITTER_X == "__dsh1__xjit"
        # One error class across the copies, so a caller catches either.
        assert m.DashSpecError is dr.DashSpecError
        assert m.DashLimitError is dr.DashLimitError

    @pytest.mark.parametrize("mode", ["saved", "served"])
    def test_a_user_column_named_like_a_renderer_column(self, tmp_path,
                                                          mode):
        fig = _figure_of(tmp_path, mode, _clash_spec(), _clash_df())
        [sc] = [x for x in drawn_renderers(fig)
                if type(x.glyph).__name__ == "Scatter"]
        data = sc.data_source.data
        # hover(__dash_row__) reads the user's values, not row ids.
        assert list(data["__dash_row__"]) == [101.0, 102.0, 103.0, 104.0]
        assert list(data["__dash_mlabel_mpg"]) == [1.0, 2.0, 3.0, 4.0]
        # dash's own columns are named from the prefix.
        assert "__dsh1__mlabel_mpg" in data
        if mode == "saved":
            assert "__dsh1__row__" in data
        tips = [t for h in fig.select({"type": dr.HoverTool})
                for t in (h.tooltips or [])]
        assert any("@{__dash_row__}" in str(t) for t in tips)

    def test_a_spec_whose_prefix_the_module_does_not_hold_is_refused(
            self, tmp_path):
        m = dr._dash_module_for({"_dash_prefix": "__dsh1_"})
        spec = dict(_clash_spec(), _dash_prefix="__dsh2_")
        sp, dp = _write_inputs(tmp_path, spec, df=_clash_df())
        with pytest.raises(ValueError, match="_dash_prefix"):
            m.DashRenderer.__init__(object.__new__(m.DashRenderer), sp, dp)


class TestNoRendererLiteral:
    def test_no_renderer_column_literal(self):
        """Every column a renderer makes is formed from ``_DASH_RP``; no
        quoted ``__dash`` literal and no JavaScript ``.__dash`` property
        read is left, but the default itself, the filter script's own
        default code prefix, and the page's hold flag
        (``globalThis.__dash_filter_hold``, no column)."""
        bad = []
        for i, line in enumerate(_code_lines(_read("dash_render.py"), "#"),
                                 1):
            if "``" in line:              # a docstring's literal text
                continue
            s = (line.replace("globalThis.__dash_filter_hold", "")
                 .replace("|| '__dashm_'", ""))   # the script's default
            if re.search(r"[\"']__dash|\.__dash|\b__dash[a-z_]*\b\s*[:=]",
                         s) and "_DASH_RP_DEFAULT = " not in s:
                bad.append("dash_render.py:%d: %s" % (i, line.strip()))
        assert bad == []
