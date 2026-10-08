"""WP-29 P0.10: every variable hover() names is exported, saved and served.

``hover(varlist)`` is dash's own option; dash.sthlp promises it adds the
variables' values to the tooltip of every layer whose marks are
observations, in the saved dashboard and the served app alike.  Measured
at 7421d3d (DROPIN-REMAINING P0.10): a variable named ONLY in hover() was
never exported.  ``dash scatter mpg weight, hover(rep78)`` returned rc 0
with a page holding 0 x ``__dash_hover_rep78``; through ``dash build,
server`` the tooltips were weight and mpg only (CDS columns
``['index', 'mpg', 'weight']``), with no note in any mode.  The renderers
dropped the absent name in silence.

The fix exports hover()'s variables on both routes (Mata
``_dash_extract_hover_vars``) and counts them against the data limits
where the page really holds them (design review A1): on the saved page
only when some layer of the graph can show them -- any type outside the
computed and literal families -- or when csv is given; in a served app
always.  The renderers name a hover() variable the data does not hold in
one bounded note per graph (``_dash_note_hover_missing``).

This file pins the code shape of both Stata routes (as text), the saved
bytes re-check's twin (``_dash_hover_unembedded``), the served app's copy
of the note, and two guards: rows whose hover() value is missing are kept,
and an unlabelled hover-only variable's row label follows P0.3.
"""
import importlib.util
import itertools
import json
import os
import re
import sys
import tempfile
import warnings

import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import HoverTool

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from conftest import make_data_json  # noqa: E402
from test_server_layer_defects import _figures_of, drawn_rows  # noqa: E402

_ROOT = os.path.join(_HERE, "..")
_SEQ = itertools.count()
_TMP = tempfile.mkdtemp(prefix="dash_hover_export_")


from conftest import render_models  # noqa: E402


def _read(name):
    with open(os.path.join(_ROOT, name), encoding="utf-8") as fh:
        return fh.read()


def _program(text, name):
    """The body of Stata program *name*: from ``program define <name>`` to
    the next ``\\nprogram define ``."""
    m = re.search(r"^program define " + re.escape(name) + r"\b", text,
                  re.M)
    assert m is not None, name
    end = text.find("\nprogram define ", m.end())
    return text[m.start():end if end >= 0 else len(text)]


def _mata_function(text, name):
    m = re.search(r"^void " + re.escape(name) + r"\(", text, re.M)
    assert m is not None, name
    end = text.find("\n}\n", m.end())
    return text[m.start():end + 3]


def _write(spec, data):
    tag = next(_SEQ)
    sp = os.path.join(_TMP, f"spec_{tag}.json")
    dp = os.path.join(_TMP, f"data_{tag}.json")
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(data, fh)
    return tag, sp, dp


def _saved(spec, data):
    _tag, sp, dp = _write(spec, data)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = dr.DashRenderer(sp, dp)
        render_models(r)
    return r


def _app_path(spec, data):
    tag, sp, dp = _write(spec, data)
    ap = os.path.join(_TMP, f"app_{tag}.py")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(ap)
    return tag, ap


def _served_doc(spec, data):
    tag, ap = _app_path(spec, data)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ms = importlib.util.spec_from_file_location(f"_hx_{tag}", ap)
        mod = importlib.util.module_from_spec(ms)
        ms.loader.exec_module(mod)
        doc = Document()
        mod.make_document(doc)
    return doc


class TestBothRoutesExportHover:
    """The Stata half, read as text: both routes call the checked Mata
    reader, union its names into the export, and count them only where a
    layer can show them (review A1)."""

    def test_the_extractor_is_required(self):
        ado = _read("dash.ado")
        m = re.search(r"local _needed (.*?)\n\n", ado, re.S)
        assert m is not None
        words = m.group(1).replace("///", " ").split()
        assert "_dash_extract_hover_vars" in words

    def test_the_immediate_route_unions_hover_into_needed_vars(self):
        body = _program(_read("dash.ado"), "_dash_render_immediate")
        call = body.find('_dash_extract_hover_vars(st_local("json_spec")')
        assert call >= 0
        assert call < body.find("_dash_cell_cap")
        assert call < body.find("_dash_write_data")
        assert "local needed_vars : list needed_vars | _hvars" in body
        after = body[call:]
        assert "exit 198" in after and "exit 111" in after
        assert after.find("exit 198") < after.find("_dash_write_data")
        assert "local _dash_nvars : word count `_cap_vars'" in body
        assert "_dash_byte_cap `_cap_vars'" in body

    def test_the_build_route_unions_hover_into_all_vars_and_row_vars(self):
        body = _program(_read("dash.ado"), "_dash_prepare_spec")
        call = body.find('_dash_extract_hover_vars(st_local("_qg_')
        assert call >= 0
        assert body.find('_dash_extract_qual_vars(st_local("_qg_')  < call
        assert call < body.find("_dash_graph_touched(")
        assert "local all_vars : list all_vars | _hv_k" in body
        assert "local row_vars : list row_vars | _hv_k" in body
        assert "local all_vars : list all_vars | _hv_hide" in body
        after = body[call:]
        i198 = after.find("exit 198")
        i111 = after.find("exit 111")
        assert i198 >= 0 and i111 >= 0
        assert "holds a hover() value" in after[:i198]
        assert "hover(): variable " in after[:i111]

    def test_both_routes_test_the_three_families(self):
        ado = _read("dash.ado")
        for name, key in (("_dash_render_immediate", "json_spec"),
                          ("_dash_prepare_spec", "_qg_")):
            body = _program(ado, name)
            call = body.find('_dash_extract_hover_vars(st_local("' + key)
            assert call >= 0, name
            after = body[call:]
            t = after.find("_dash_spec_types_in(")
            assert t >= 0, name
            arg = after[t:after.find("\n", after.find("_pt_literal", t))]
            for fam in ("_pt_univar", "_pt_onefit", "_pt_literal"):
                assert fam in arg, (name, fam, arg)
            if name == "_dash_prepare_spec":
                # The flag is set only when csv is not given.
                assert "`csv'\" == \"\"" in after[:t], after[:t][-300:]

    def test_the_saved_byte_cap_leaves_out_what_no_layer_shows(self):
        body = _program(_read("dash.ado"), "_dash_prepare_spec")
        caps = [m.start() for m in re.finditer(r"_dash_byte_cap `", body)]
        assert len(caps) == 2, caps
        served = body.find("_dash_byte_cap `all_vars'")
        saved = body.find("_dash_byte_cap `_byte_vars'")
        assert served >= 0 and saved >= 0
        branch = body.rfind('if "`server\'" != ""', 0, served)
        assert branch >= 0
        els = body.find("else {", served)
        assert branch < served < els < saved
        # No unconditional cap after the branch: both calls are its own.
        close = body.find("\n    }\n", saved)
        assert "_dash_byte_cap" not in body[close:]

    def test_the_mata_extractor_reads_the_value_as_designed(self):
        fn = _mata_function(_read("dash_parse.mata"),
                            "_dash_extract_hover_vars")
        for piece in ('_dash_json_get_str(json_str, "hover"',
                      "_dash_blank_words(", "_dash_is_varname(",
                      "_st_varindex(w, 0)", "asarray_create()",
                      'usubstr(w, 1, 77) + "..."'):
            assert piece in fn, piece
        assert "_dash_extract_vars" not in fn


def _string_data():
    df = tp._DF.assign(make=[("car %02d " % i).ljust(30, "x")
                             for i in range(len(tp._DF))])
    data = make_data_json(df)
    data["StataJSON"]["variableIsString"]["make"] = True
    data["StataJSON"]["variableTypeIsString"]["make"] = True
    return data


class TestTheByteLimit:
    """A string hover() variable on a saved page counts toward
    $dash_max_bytes only when a layer can show it (review A1(b)); a
    served app embeds every column and counts it always."""

    _BO = {"limits": {"bytes": 100}}

    def test_a_string_hover_variable_a_layer_shows_counts_saved(self):
        spec = tp._spec([tp.plot_for("scatter")], self._BO,
                        {"hover": "make"})
        with pytest.raises(dr.DashLimitError, match="bytes of text"):
            _saved(spec, _string_data())

    def test_a_string_hover_variable_no_layer_shows_does_not_count_saved(
            self):
        spec = tp._spec([tp.plot_for("histogram", var="mpg")], self._BO,
                        {"hover": "make"})
        r = _saved(spec, _string_data())
        assert "g1" in r.figures

    def test_the_served_app_counts_it_whatever_the_graph(self):
        spec = tp._spec([tp.plot_for("histogram", var="mpg")], self._BO,
                        {"hover": "make"})
        with pytest.raises(dr.DashLimitError):
            _app_path(spec, _string_data())


class TestTheServedApp:

    def test_the_app_defines_and_calls_the_note(self):
        spec = tp._spec([tp.plot_for("scatter")], None, {"hover": "rep"})
        _tag, ap = _app_path(spec, make_data_json(tp._DF))
        with open(ap, encoding="utf-8") as fh:
            src = fh.read()
        assert "def _dash_note_hover_missing(" in src
        assert src.count("_dash_note_hover_missing(") >= 2


def _missing_extra():
    df = pd.DataFrame({"y": [1.0, 2.0, 3.0], "x": [1.0, 2.0, 3.0],
                       "extra": [1.0, float("nan"), 3.0]})
    spec = tp._spec([{"type": "scatter", "yvar": "y", "xvar": "x",
                      "options": {}}], None, {"hover": "extra"})
    return spec, make_data_json(df)


class TestRowsWithAMissingHoverValueAreKept:
    """Review A8: a row whose hover() value is missing is drawn, as
    twoway draws it (the served twin is test_server_layer_defects.py's
    test_an_extra_hover_column_does_not_change_which_rows_are_drawn)."""

    def test_saved(self):
        spec, data = _missing_extra()
        r = _saved(spec, data)
        fig = r.figures["g1"]
        rows = []
        for rend in fig.renderers:
            if type(rend.glyph).__name__ == "Scatter":
                data_ = rend.data_source.data
                rows.append(max(len(v) for v in data_.values()))
        assert rows == [3], rows

    def test_served(self):
        spec, data = _missing_extra()
        doc = _served_doc(spec, data)
        assert drawn_rows(_figures_of(doc)) == [("Scatter", 3)]


class TestAnUnlabelledHoverOnlyVariable:
    """Review A3: the row label of an unlabelled hover-only variable is
    its name once P0.3 (section 03, ``_dash_var_label``) has landed, and
    blank before; the assertion tightens by itself."""

    @pytest.mark.parametrize("mode", ("saved", "served"))
    def test_its_row_label_follows_p0_3(self, mode):
        data = make_data_json(tp._DF)
        data["StataJSON"]["variableLabels"]["rep"] = ""
        spec = tp._spec([tp.plot_for("scatter")], None, {"hover": "rep"})
        if mode == "saved":
            figs = list(_saved(spec, data).figures.values())
        else:
            figs = _figures_of(_served_doc(spec, data))
        rows = [(lab, field) for f in figs for t in f.tools
                if isinstance(t, HoverTool) and isinstance(t.tooltips, list)
                for lab, field in t.tooltips if field.startswith("@{rep}")]
        assert rows, "no tooltip row shows rep"
        want = "rep" if hasattr(dr, "_dash_var_label") else ""
        assert all(lab == want for lab, _f in rows), rows
