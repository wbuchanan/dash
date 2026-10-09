"""test_dropdown_values.py -- a dropdown's value, its listing and its mask
(GAPS2 X1).

Measured at 91d97be: ``_dash_option_value`` (dash_render.py) turned any
value that reads as a whole number into integer TEXT, string values
included, so '01', '1.0' and ' 2' all became '1' or '2' and merged into
one option; ``_dash_dropdown_values`` dropped the categories 'nan', 'None'
and 'NaT' from the list entirely; and ECMAScript writes ``5e-05`` as
``"0.00005"`` where Python writes ``"5e-05"``, so on the saved page a
numeric value below 1e-4 or at/above 1e21 selected no rows at all.
Research widened the symptom: the saved snapshot (``_dash_json_value``)
coerced a string code to a number too, so after a filter move a marker
label "007" read back as 7 and a ``dcount`` card merged '01' and '1'.

After this fix a numeric column's dropdown carries FLOAT values and both
twins compare them as numbers (an entry that stands for several values
sharing one display-format label, DISCOVERY Q26, selects every member); a
string column keeps its EXACT text -- 'nan', 'None', 'NaT', '01' and '1'
are ordinary, distinct categories, and Python's own ``None``/NaN (never
written by dash itself, but tolerated) fold into one blank ``""`` entry
alongside Stata's own missing string; and every saved-page snapshot keeps
a string column as text.

Run this file alone while iterating: ``python3 -m pytest
test/test_dropdown_values.py -q`` (CLAUDE.md rule 11).
"""
import json
import math
import os
import sys
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from js_runner import JsSession, mask_parity  # noqa: E402
import test_filter_exclude as tfe  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_adversarial_matrix import _write_inputs  # noqa: E402
from test_help_claims_3 import _card_value, _kpi_card  # noqa: E402
from conftest import make_data_json, make_spec  # noqa: E402

_NAN = float("nan")


# ---------------------------------------------------------------------------
# _dash_option_value / _dash_dropdown_values / _dash_filter_numeric
# ---------------------------------------------------------------------------

from conftest import render_models  # noqa: E402


class TestOptionValues:

    def test_a_string_code_keeps_its_exact_text(self):
        assert dr._dash_option_value("01") == "01"
        assert dr._dash_option_value(" 2") == " 2"
        assert dr._dash_option_value("1.0") == "1.0"
        assert dr._dash_option_value("nan") == "nan"
        assert dr._dash_option_value("None") == "None"
        assert dr._dash_option_value("NaT") == "NaT"

    def test_a_number_is_a_float_and_a_date_its_milliseconds(self):
        assert dr._dash_option_value(1.0) == 1.0
        assert isinstance(dr._dash_option_value(1.0), float)
        assert dr._dash_option_value(np.float32(0.1)) == float(np.float32(0.1))
        assert dr._dash_option_value(
            pd.Timestamp("2001-12-31")) == 1009756800000.0

    def test_nan_none_nat_and_blank_are_listed_on_a_string_column(self):
        got = dr._dash_dropdown_values(pd.Series(
            ["01", "1", "1.0", " 2", "None", "nan", "NaT", "", None]))
        assert got == ["", " 2", "01", "1", "1.0", "NaT", "None", "nan"]

    def test_numeric_missing_is_not_listed(self):
        got = dr._dash_dropdown_values(pd.Series([3.0, np.nan, 1.0]))
        assert got == [1.0, 3.0]

    def test_the_numeric_test_is_the_dtype(self):
        assert dr._dash_filter_numeric(pd.Series([1.0, 2.0]))
        assert dr._dash_filter_numeric(
            pd.Series(pd.to_datetime(["2020-01-01"])))
        assert not dr._dash_filter_numeric(pd.Series(["a", "b"]))
        assert not dr._dash_filter_numeric(pd.Series(["a", None]))


# ---------------------------------------------------------------------------
# The widget both modes build
# ---------------------------------------------------------------------------

class TestTheWidget:

    def test_the_widget_carries_numbers_for_a_numeric_column_and_text_for_a_string_one(
            self, tmp_path):
        df = pd.DataFrame({
            "mpg": [22.0, 17.0, 25.0, 30.0, 21.0, 19.0, 14.0, 28.0, 16.0,
                    23.0],
            "foreign": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
            "s": ["01", "1", "1.0", "01", "1", "1.0", "01", "1", "1.0", "01"],
        })
        spec = make_spec(
            [{"type": "scatter", "yvar": "mpg", "xvar": "mpg",
              "options": {}}],
            filters=[{"varname": "foreign", "type": "dropdown"},
                    {"varname": "s", "type": "dropdown"}])
        sp, dp = _write_inputs(tmp_path, spec, df)
        data = json.load(open(dp))
        data["StataJSON"]["variableIsString"]["s"] = True
        data["StataJSON"]["variableTypeIsString"]["s"] = True
        with open(dp, "w") as fh:
            json.dump(data, fh)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = dr.DashRenderer(sp, dp)
            render_models(r)
        w_for, w_s = r.filter_widgets
        for_vals = [v for v, _ in w_for.options][1:]
        s_vals = [v for v, _ in w_s.options][1:]
        assert all(isinstance(v, float) for v in for_vals)
        assert all(isinstance(v, str) for v in s_vals)
        assert w_for._dash_numeric is True
        assert w_for._dash_groups == {0.0: (0.0,), 1.0: (1.0,)}
        assert not getattr(w_s, "_dash_numeric", False)
        assert not hasattr(w_s, "_dash_groups")
        cb = r.filter_callbacks[0]
        specs = json.loads(cb.args["filter_specs_json"])
        by_var = {s["varname"]: s for s in specs}
        assert by_var["foreign"]["numeric"] is True
        assert by_var["foreign"]["groups"] == [[0.0], [1.0]]
        assert not by_var["s"].get("numeric", False)
        assert "groups" not in by_var["s"]


# ---------------------------------------------------------------------------
# The saved snapshot, the CSV and derived text columns keep a string as text
# ---------------------------------------------------------------------------

class TestTheSnapshot:

    def test_the_snapshot_keeps_a_string_column_as_text(self):
        assert dr._dash_json_value("01") == "01"
        assert dr._dash_json_value("nan") == "nan"
        assert dr._dash_json_value("") == ""
        assert dr.DashRenderer._to_serialisable("007") == \
            dr._dash_json_value("007")

    def test_dcount_and_a_marker_label_survive_a_move(self, tmp_path):
        df = pd.DataFrame({
            "x": [1.0, 2.0, 3.0, 4.0, 5.0],
            "y": [1.0, 2.0, 3.0, 4.0, 5.0],
            "s": ["007", "1", "1", "2", "2"],
        })
        spec = make_spec(
            [{"type": "scatter", "yvar": "y", "xvar": "x",
              "options": {"mlabel": "s"}}],
            filters=[{"varname": "x", "type": "range"}],
            kpis=[dict(_kpi_card("k1", stat="dcount", var="s"),
                       update="filter")])
        sp, dp = _write_inputs(tmp_path, spec, df)
        data = json.load(open(dp))
        data["StataJSON"]["variableIsString"]["s"] = True
        data["StataJSON"]["variableTypeIsString"]["s"] = True
        with open(dp, "w") as fh:
            json.dump(data, fh)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = dr.DashRenderer(sp, dp)
            render_models(r)
        [w] = r.filter_widgets
        [cb] = r.filter_callbacks
        sess = JsSession(r.filter_callbacks)
        sess.set(w, (1.0, 5.0))
        sess.run(cb)
        [gsrc] = list(r.sources.values())
        # A string mlabel() variable draws directly from its own column
        # (GlyphMapper._apply_mlabel_opts: a __dash_mlabel_* derived text
        # column is built only for a NON-text column); the marker label
        # therefore reads correctly whenever the column itself keeps its
        # exact text after a move.
        assert gsrc.data["s"] == ["007", "1", "1", "2", "2"]
        k1 = r.kpi_divs["k1"]
        state = sess.state()
        text = state["divs"].get(k1.id, k1.text)
        assert _card_value(text, "k1") == "3"


# ---------------------------------------------------------------------------
# The one rule: node and pandas agree, including a shared label's group
# ---------------------------------------------------------------------------

class TestOneRule:

    def _df(self):
        return pd.DataFrame({
            "s": ["01", "1", "1.0", " 2", "None", "nan", "NaT", ""],
            "x": [5e-05, 1e21, float(np.float32(0.1)), np.nan, 1.0, 2.0,
                  3.0, 4.0],
        })

    def test_node_and_pandas_agree(self):
        df = self._df()
        s_spec = {"varname": "s", "type": "dropdown", "sentinel": "__all__",
                  "numeric": False}
        x_spec = {"varname": "x", "type": "dropdown", "sentinel": "__all__",
                  "numeric": True}
        for text in ["01", "1", "1.0", " 2", "None", "nan", "NaT", ""]:
            js_mask, py_mask = mask_parity(df, [s_spec], [text])
            want = [v == text for v in df["s"]]
            assert js_mask == want, (text, js_mask, want)
            assert py_mask == want, (text, py_mask, want)
        for val in [5e-05, 1e21, float(np.float32(0.1))]:
            js_mask, py_mask = mask_parity(df, [x_spec], [val])
            want = [v == val for v in df["x"]]
            assert js_mask == want, (val, js_mask, want)
            assert py_mask == want, (val, py_mask, want)

    def test_two_values_sharing_a_label_select_both(self):
        # mask_parity's synthetic Select carries no _dash_groups (S03's
        # helper is groups-agnostic); the pandas side of THIS rule is
        # exercised directly through _dash_dropdown_mask (per test/js_
        # runner.py's own note: wrap a missing accessor in a test-local
        # helper rather than editing a section this one does not own).
        x = pd.DataFrame({"x": [1.2, 1.4, 2.0]})
        groups = [[1.2, 1.4], [2.0]]
        spec = {"varname": "x", "type": "dropdown", "sentinel": "__all__",
                "numeric": True, "groups": groups}
        js_mask, _ = mask_parity(x, [spec], [1.2])
        assert js_mask == [True, True, False]
        py_direct = dr._dash_dropdown_mask(
            x["x"], 1.2, {1.2: (1.2, 1.4), 2.0: (2.0,)})
        assert py_direct.tolist() == [True, True, False]

        y = pd.DataFrame({
            "y": [float(np.float32(0.1)), 0.1000000015, 0.5]})
        ygroups = [[float(np.float32(0.1)), 0.1000000015], [0.5]]
        yspec = {"varname": "y", "type": "dropdown", "sentinel": "__all__",
                 "numeric": True, "groups": ygroups}
        js_mask, _ = mask_parity(y, [yspec], [float(np.float32(0.1))])
        assert js_mask == [True, True, False]
        py_direct = dr._dash_dropdown_mask(
            y["y"], float(np.float32(0.1)),
            {float(np.float32(0.1)): (float(np.float32(0.1)), 0.1000000015),
             0.5: (0.5,)})
        assert py_direct.tolist() == [True, True, False]

    def test_a_hostile_text_value_is_data(self):
        df = pd.DataFrame({"s": ["__proto__", "<script>", 'a"b']})
        for text in ["__proto__", "<script>", 'a"b']:
            spec = {"varname": "s", "type": "dropdown",
                    "sentinel": "__all__", "numeric": False}
            js_mask, py_mask = mask_parity(df, [spec], [text])
            want = [v == text for v in df["s"]]
            assert js_mask == want
            assert py_mask == want


# ---------------------------------------------------------------------------
# Both render modes select the same rows
# ---------------------------------------------------------------------------

class TestBothModes:

    def _spec_and_data(self, tmp_path):
        df = pd.DataFrame({
            "y": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            "s": ["01", "nan", "", "01", "01", "nan"],
            "x": [5e-05, 1e21, 1.0, 5e-05, 2.0, 1e21],
        })
        spec = make_spec(
            [{"type": "scatter", "yvar": "y", "xvar": "y", "options": {}}],
            filters=[{"varname": "s", "type": "dropdown"},
                    {"varname": "x", "type": "dropdown"}])
        sp, dp = _write_inputs(tmp_path, spec, df)
        data = json.load(open(dp))
        data["StataJSON"]["variableIsString"]["s"] = True
        data["StataJSON"]["variableTypeIsString"]["s"] = True
        with open(dp, "w") as fh:
            json.dump(data, fh)
        return sp, dp

    def test_both_modes_select_the_same_rows(self, tmp_path):
        sp, dp = self._spec_and_data(tmp_path)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = dr.DashRenderer(sp, dp)
            render_models(r)
        [w_s, w_x] = r.filter_widgets
        cb_of = dict(zip(r.filter_widgets, r.filter_callbacks))
        [gsrc] = list(r.sources.values())

        cases = [(w_s, "01", 3), (w_s, "nan", 2), (w_s, "", 1),
                 (w_x, 5e-05, 2), (w_x, 1e21, 2)]
        for w, val, n in cases:
            other = w_x if w is w_s else w_s
            other.value = other._dash_sentinel
            sess = JsSession(r.filter_callbacks)
            sess.set(w, val)
            sess.run(cb_of[w])
            assert sess.rows(gsrc) == n, (val, sess.rows(gsrc))

        app = os.path.join(str(tmp_path), "app_both.py")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(app)
        with open(app, encoding="utf-8") as fh:
            from test_adversarial_matrix import _load_app
            ns = _load_app(fh.read(), "dropdown_both")
        from bokeh.document import Document
        from bokeh.models import Select
        doc = Document()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ns["make_document"](doc)
        served_widgets = list(doc.select({"type": Select}))
        varname_of = {w_s: "s", w_x: "x"}
        for w_val, val, n in cases:
            var = varname_of[w_val]
            [sw] = [w for w in served_widgets if w._dash_var == var]
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                tp._fire(sw, val)
            [fig] = [f for f in tp._walk_models(doc)
                     if type(f).__name__ == "figure"]
            src = tfe._renderer_source(fig)
            assert tfe._rows(src) == n, (var, val, n, tfe._rows(src))
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                tp._fire(sw, sw._dash_sentinel)


# ---------------------------------------------------------------------------
# colorvar()'s string path: 'nan' is a category, not missing
# ---------------------------------------------------------------------------

class TestColorvarStrings:

    def test_colorvar_reads_the_text_nan_as_a_category(self, tmp_path):
        df = pd.DataFrame({
            "y": [1.0, 2.0, 3.0, 4.0],
            "x": [1.0, 2.0, 3.0, 4.0],
            "s": ["nan", "a", "", "a"],
        })
        spec = make_spec(
            [{"type": "scatter", "yvar": "y", "xvar": "x",
              "options": {"colorvar": "s"}}])
        sp, dp = _write_inputs(tmp_path, spec, df)
        data = json.load(open(dp))
        data["StataJSON"]["variableIsString"]["s"] = True
        data["StataJSON"]["variableTypeIsString"]["s"] = True
        with open(dp, "w") as fh:
            json.dump(data, fh)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = dr.DashRenderer(sp, dp)
            render_models(r)
        [gsrc] = list(r.sources.values())
        # WP-29 P0.16: the missing sentinel is None / the colour column is named under __dash_cvar.
        import colour_bins as cb
        (rend,) = cb.colour_renderers(r._last_layout_root)
        binned = cb.colour_values(rend)
        assert set(binned) == {None, "a", "nan"}
