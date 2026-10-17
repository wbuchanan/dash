"""test_export.py -- ROADMAP WP-21: getting the data out.

WP-21 adds a CSV download of the rows the dashboard's filters leave (opt-in:
``dash build, csv``), in both render modes, through ONE JavaScript formatter:
the saved page masks its full-frame snapshot in the browser; the served app
masks its frame on the server and hands the rows to the page, where the same
formatter writes them.  These tests run the shipped JavaScript under node.

Found on the way, and fixed first (CLAUDE.md rule 8): a range or slider
filter in the SAVED page let a missing value through whenever 0 lay inside
its bounds.  The snapshot carries a missing value as JSON null, and
JavaScript compares null as 0, so ``range(-1, 10)`` kept every missing row
and ``range(5, 10)`` dropped it; the served app, comparing in pandas, drops
it always, as dash's own ``if`` translation does (``x >= 5`` is false for
NaN).  The two modes filtered different rows and their KPI cards disagreed.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402


from conftest import render_models  # noqa: E402


def _node():
    node = shutil.which("node")
    if node is None:
        pytest.fail("node is not installed; the shipped JavaScript cannot "
                    "be run (a skip here would hide an untested export)")
    return node


def _run_js(source):
    """Run *source* under node and return what it printed, parsed."""
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False,
                                     encoding="utf-8") as fh:
        fh.write(source)
        path = fh.name
    try:
        res = subprocess.run([_node(), path], capture_output=True, text=True,
                             timeout=60)
        assert res.returncode == 0, res.stderr[:2000]
        return json.loads(res.stdout)
    finally:
        os.unlink(path)


# ===========================================================================
# 1. The saved page's filter mask and missing values
# ===========================================================================

def _saved_mask(orig, specs, values):
    """The row mask the SHIPPED filter callback computes, under node.

    Runs ``_FILTER_JS`` up to the point where the mask exists -- the same
    prefix before and after the mask became a function -- with stand-ins
    for the Bokeh models it reads.
    """
    js = dr._FILTER_JS
    prefix = js[:js.index("// Build new data arrays")]
    widgets = [{"value": v} for v in values]
    harness = (
        "const orig_source = {data: " + json.dumps(orig) + "};\n"
        "const filter_specs_json = " + json.dumps(json.dumps(specs)) + ";\n"
        "const kpi_config_json = '[]';\n"
        "const all_widgets = " + json.dumps(widgets) + ";\n"
        + prefix
        + "\nprocess.stdout.write(JSON.stringify(active));\n"
        # The prefix opens _FILTER_JS's try block (WP-31 H1).
        + "} finally {}\n")
    return _run_js(harness)


# x holds a missing value (null, as _to_serialisable writes NaN) in rows 1
# and 3; the served app and dash's `if' drop a missing row from any
# numeric comparison.
_ORIG = {"x": [-2.0, None, 0.0, None, 4.0, 9.0], "g": [1.0] * 6,
         dr._ROW_ID_COLUMN: [0, 1, 2, 3, 4, 5]}


class TestTheSavedFilterMaskFailsMissingValues:

    @pytest.mark.parametrize("lo,hi,want", [
        # 0 inside the bounds: null compared as 0 used to pass.
        (-1.0, 10.0, [False, False, True, False, True, True]),
        (-5.0, 0.5, [True, False, True, False, False, False]),
        # 0 outside the bounds: null failed, for the wrong reason.
        (1.0, 10.0, [False, False, False, False, True, True]),
    ])
    def test_a_range_filter(self, lo, hi, want):
        got = _saved_mask(_ORIG, [{"varname": "x", "type": "range"}],
                          [[lo, hi]])
        assert got == want

    @pytest.mark.parametrize("val,want", [
        (-5.0, [True, False, True, False, True, True]),
        (0.0, [False, False, True, False, True, True]),
        (5.0, [False, False, False, False, False, True]),
    ])
    def test_a_slider_filter(self, val, want):
        got = _saved_mask(_ORIG, [{"varname": "x", "type": "slider"}], [val])
        assert got == want

    def test_a_missing_value_written_as_nan_fails_too(self):
        orig = dict(_ORIG)
        js_nan = "NaN"
        harness_orig = json.dumps(orig).replace("null", js_nan)
        js = dr._FILTER_JS
        prefix = js[:js.index("// Build new data arrays")]
        got = _run_js(
            "const orig_source = {data: " + harness_orig + "};\n"
            "const filter_specs_json = " + json.dumps(json.dumps(
                [{"varname": "x", "type": "range"}])) + ";\n"
            "const kpi_config_json = '[]';\n"
            "const all_widgets = [{value: [-1, 10]}];\n"
            + prefix + "\nprocess.stdout.write(JSON.stringify(active));\n"
            # The prefix opens _FILTER_JS's try block (WP-31 H1).
            + "} finally {}\n")
        assert got == [False, False, True, False, True, True]

    def test_a_dropdown_never_matches_a_missing_value(self):
        got = _saved_mask({"x": [1.0, None, 2.0], dr._ROW_ID_COLUMN: [0, 1, 2]},
                          [{"varname": "x", "type": "dropdown",
                            "sentinel": "__all__"}], ["1"])
        assert got == [True, False, False]


# ===========================================================================
# 2. The one CSV formatter, run under node
# ===========================================================================

def _csv(data, rows, meta, text=None):
    """dash_csv_text as the page runs it."""
    return _run_js(
        dr._DASH_CSV_JS
        + "\nprocess.stdout.write(JSON.stringify(dash_csv_text("
        + json.dumps(data) + ", " + json.dumps(text if text is not None
                                               else data)
        + ", " + json.dumps(rows) + ", " + json.dumps(meta) + ")));\n")


def _meta(columns, strings=(), dates=None, labels=None):
    return {"columns": list(columns), "strings": list(strings),
            "dates": dates or {}, "labels": labels or {},
            "filename": "dashboard.csv"}


def _ms(iso):
    import pandas as pd
    return float(pd.Timestamp(iso).value // 1_000_000)


class TestTheCsvFormatter:

    def test_a_header_then_rows_with_crlf_line_ends(self):
        got = _csv({"a": [1.0, 2.0], "b": [3.0, 4.0]}, [0, 1],
                   _meta(["a", "b"]))
        assert got == "a,b\r\n1,3\r\n2,4\r\n"

    @pytest.mark.parametrize("v,want", [
        (0.1, "0.1"), (3.0, "3"), (-3.0, "-3"), (1 / 3, "0.3333333333333333"),
        (1e-7, "1e-7"), (123456789012.0, "123456789012"), (1e21, "1e+21"),
        (-0.0, "0"), (2.5e-5, "0.000025"),
    ])
    def test_a_number_is_javascripts_shortest_spelling(self, v, want):
        got = _csv({"x": [v]}, [0], _meta(["x"]))
        assert got == f"x\r\n{want}\r\n"

    def test_a_missing_value_is_an_empty_field(self):
        got = _csv({"x": [None, 1.0], "s": [None, "t"]}, [0, 1],
                   _meta(["x", "s"], strings=["s"]))
        assert got == "x,s\r\n,\r\n1,t\r\n"

    @pytest.mark.parametrize("kind,iso,want", [
        ("td", "2020-01-16", "2020-01-16"),
        ("tw", "2020-01-15", "2020-01-15"),
        ("tm", "2020-02-01", "2020-02-01"),
        ("tq", "2020-04-01", "2020-04-01"),
        ("th", "2020-07-01", "2020-07-01"),
        ("ty", "2020-01-01", "2020"),
        ("tc", "2020-01-15 13:45:30", "2020-01-15 13:45:30"),
        ("tc", "2020-01-15 13:45:30.250", "2020-01-15 13:45:30.25"),
        ("tC", "2020-01-15 13:45:30.001", "2020-01-15 13:45:30.001"),
    ])
    def test_a_date_is_iso_8601(self, kind, iso, want):
        got = _csv({"d": [_ms(iso)]}, [0], _meta(["d"], dates={"d": kind}))
        assert got == f"d\r\n{want}\r\n"

    def test_a_labelled_value_is_its_label(self):
        got = _csv({"f": [0.0, 1.0, 2.0]}, [0, 1, 2],
                   _meta(["f"], labels={"f": {"0": "Domestic",
                                              "1": "Foreign, imported"}}))
        assert got == 'f\r\nDomestic\r\n"Foreign, imported"\r\n2\r\n'

    def test_a_string_is_its_own_text(self):
        # The download reads the raw text source (since GAPS2 X1 the
        # snapshot keeps "007" as text too).
        got = _csv({"s": [7.0, 1.0]}, [0, 1], _meta(["s"], strings=["s"]),
                   text={"s": ["007", "1e5"]})
        assert got == "s\r\n007\r\n1e5\r\n"

    @pytest.mark.parametrize("raw,want", [
        ("=SUM(A1)", "'=SUM(A1)"), ("+1 555", "'+1 555"),
        ("-5 degrees", "'-5 degrees"), ("@cmd", "'@cmd"),
        ("\tx", "'\tx"), ("a=b", "a=b"),
    ])
    def test_a_text_cell_that_a_spreadsheet_would_run_is_defused(self, raw,
                                                                 want):
        got = _csv({"s": [raw]}, [0], _meta(["s"], strings=["s"]))
        assert got == f"s\r\n{want}\r\n"

    def test_a_label_that_a_spreadsheet_would_run_is_defused(self):
        got = _csv({"f": [1.0]}, [0], _meta(["f"],
                                           labels={"f": {"1": "=HYPERLINK()"}}))
        assert got == "f\r\n'=HYPERLINK()\r\n"

    def test_a_negative_number_is_not_defused(self):
        assert _csv({"x": [-2.0]}, [0], _meta(["x"])) == "x\r\n-2\r\n"

    @pytest.mark.parametrize("raw,want", [
        ("a,b", '"a,b"'), ('say "hi"', '"say ""hi"""'),
        ("two\nlines", '"two\nlines"'), ("cr\rhere", '"cr\rhere"'),
    ])
    def test_rfc_4180_quoting(self, raw, want):
        got = _csv({"s": [raw]}, [0], _meta(["s"], strings=["s"]))
        assert got == f"s\r\n{want}\r\n"

    def test_only_the_rows_asked_for_in_their_order(self):
        got = _csv({"x": [10.0, 11.0, 12.0, 13.0]}, [3, 1], _meta(["x"]))
        assert got == "x\r\n13\r\n11\r\n"

    def test_the_columns_are_the_metas_and_nothing_else(self):
        got = _csv({"b": [2.0], "a": [1.0], dr._ROW_ID_COLUMN: [0]}, [0],
                   _meta(["a", "b"]))
        assert got == "a,b\r\n1,2\r\n"

    def test_no_rows_is_the_header_alone(self):
        assert _csv({"x": [1.0]}, [], _meta(["x"])) == "x\r\n"

    def test_the_download_is_utf8_with_a_bom_under_the_given_name(self):
        got = _run_js(
            dr._DASH_CSV_JS + """
const made = [];
globalThis.URL.createObjectURL = (b) => { made.push(b); return "blob:x"; };
globalThis.URL.revokeObjectURL = () => {};
const link = {dispatchEvent: () => { link.clicked = true; }};
globalThis.document = {createElement: (t) => link};
globalThis.MouseEvent = function (t) { this.type = t; };
globalThis.setTimeout = () => 0;
dash_csv_download("a\\r\\nb\\r\\n", "dashboard.csv");
const blob = made[0];
const bytes = new Uint8Array(await blob.arrayBuffer());
process.stdout.write(JSON.stringify({type: blob.type, download: link.download,
    href: link.href, clicked: !!link.clicked,
    head: Array.from(bytes.slice(0, 4))}));
""")
        assert got == {"type": "text/csv;charset=utf-8",
                       "download": "dashboard.csv", "href": "blob:x",
                       "clicked": True, "head": [0xEF, 0xBB, 0xBF, 0x61]}


# ===========================================================================
# 3. The download in each mode, and the two modes agree
# ===========================================================================

import math  # noqa: E402
import warnings  # noqa: E402

import pandas as pd  # noqa: E402
from bokeh.document import Document  # noqa: E402
from bokeh.events import ButtonClick  # noqa: E402
from bokeh.models import ColumnDataSource, RangeSlider, Select  # noqa: E402

from conftest import make_data_json, make_spec, exec_app  # noqa: E402

_NAN = float("nan")
# Days since 1960 for 2020-01-16 .. 2020-01-21 (%td).
_DF = pd.DataFrame({
    "mpg": [22.0, 17.0, _NAN, 30.0, 21.0, 25.0],
    "foreign": [0.0, 1.0, 1.0, 0.0, 1.0, 1.0],
    "make": ["007", "=cmd()", "a,b", "", "x", "say \"hi\""],
    "day": [21930.0, 21931.0, 21932.0, _NAN, 21934.0, 21935.0],
})
_LABELS = {"origin": {"0": "Domestic", "1": "Foreign"}}


def _export_spec(csv=True, filters=True):
    spec = make_spec(
        [{"type": "scatter", "yvar": "mpg", "xvar": "day", "options": {}}],
        filters=([{"varname": "foreign", "type": "dropdown"},
                  {"varname": "mpg", "type": "range"}] if filters else None))
    if filters:
        spec["build_options"]["filter"] = (
            "foreign, type(dropdown) || mpg, type(range)")
    spec["build_options"]["formats"] = {"day": "%td"}
    if csv:
        spec["build_options"]["csv"] = "1"
    return spec


def _export_inputs(tmp_path, spec):
    data = make_data_json(_DF, value_labels=_LABELS,
                          value_label_names={"foreign": "origin"})
    # make is a string variable, as jsonio says so.
    for key in ("variableIsString", "variableTypeIsString"):
        data["StataJSON"][key]["make"] = True
    sp = os.path.join(str(tmp_path), "spec.json")
    dp = os.path.join(str(tmp_path), "data.json")
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    with open(dp, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    return sp, dp


def _saved(tmp_path, spec):
    sp, dp = _export_inputs(tmp_path, spec)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = dr.DashRenderer(sp, dp)
        render_models(r)
    return r


_ATTACH = "if __name__ != '__main__':\n    make_document(curdoc())"


def _served(tmp_path, spec):
    sp, dp = _export_inputs(tmp_path, spec)
    op = os.path.join(str(tmp_path), "app.py")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(op)
        with open(op, encoding="utf-8") as fh:
            src = fh.read()
        assert _ATTACH in src
        ns = {"__name__": "export_app"}
        exec_app(src.replace(_ATTACH, "pass"), op, ns)
        doc = Document()
        ns["make_document"](doc)
    return doc


def _button(root):
    found = list(root.select({"name": "dash_csv_download"}))
    return found[0] if found else None


def _download(code, bindings):
    """Run a download callback's code under node; return the file's text."""
    decl = "".join(f"const {k} = {v};\n" for k, v in bindings.items())
    got = _run_js(
        "const made = [];\n"
        "globalThis.URL.createObjectURL = (b) => { made.push(b); return 'blob:x'; };\n"
        "globalThis.URL.revokeObjectURL = () => {};\n"
        "globalThis.document = {createElement: (t) => ({dispatchEvent: () => {}})};\n"
        "globalThis.MouseEvent = function (t) { this.type = t; };\n"
        "globalThis.setTimeout = () => 0;\n"
        + decl + code
        # Blob.text() drops a byte-order mark; read the bytes as written.
        + "\nconst t = new TextDecoder('utf-8', {ignoreBOM: true})"
          ".decode(await made[0].arrayBuffer());\n"
          "process.stdout.write(JSON.stringify(t));\n")
    assert got.startswith("﻿"), "no byte-order mark"
    return got[1:]


def _saved_file(r, values):
    """The saved page's download, the filter widgets at *values*."""
    btn = _button(r._last_layout_root)
    assert btn is not None, "no Download CSV button in the saved page"
    cb = btn.js_event_callbacks["button_click"][0]
    a = cb.args
    # The callback pairs widgets with filter specs by position.
    specs = json.loads(a["filter_specs_json"])
    widgets = [{"value": values.get(spec["varname"], w.value),
                "start": getattr(w, "start", None),
                "end": getattr(w, "end", None)}
               for spec, w in zip(specs, a["all_widgets"])]
    return _download(cb.code, {
        "orig_source": json.dumps({"data": dict(a["orig_source"].data)}),
        "text_source": json.dumps({"data": dict(a["text_source"].data)}),
        "all_widgets": json.dumps(widgets),
        "filter_specs_json": json.dumps(a["filter_specs_json"]),
        "meta_json": json.dumps(a["meta_json"]),
    })


def _csv_callback(doc):
    """The served button's tags callback: the page-side writer."""
    btn = _button(doc)
    cbs = btn.js_property_callbacks.get("change:tags") if btn else None
    return cbs[0] if cbs else None


def _csv_source(doc):
    cb = _csv_callback(doc)
    return cb.args["src"] if cb is not None else None


def _click(btn):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        btn._trigger_event(ButtonClick(btn))


def _served_file(doc, values):
    """The served page's download, the filter widgets at *values*."""
    for w in list(doc.select({"type": Select})) + list(
            doc.select({"type": RangeSlider})):
        v = getattr(w, "_dash_var", None)
        if v in values:
            w.value = values[v]
    btn = _button(doc)
    _click(btn)
    src = _csv_source(doc)
    assert src is not None and btn.tags, "the click sent no rows"
    cb = _csv_callback(doc)
    return _download(cb.code, {
        "src": json.dumps({"data": dict(src.data)}),
        "meta_json": json.dumps(cb.args["meta_json"]),
    })


class TestTheButtonIsThereWhenAsked:

    def test_the_saved_page_has_it_only_with_csv(self, tmp_path):
        assert _button(_saved(tmp_path, _export_spec(csv=True))
                       ._last_layout_root) is not None
        assert _button(_saved(tmp_path, _export_spec(csv=False))
                       ._last_layout_root) is None

    def test_the_served_app_has_it_only_with_csv(self, tmp_path):
        assert _button(_served(tmp_path, _export_spec(csv=True))) is not None
        assert _button(_served(tmp_path, _export_spec(csv=False))) is None

    @pytest.mark.parametrize("flag,want", [
        ("1", True), (1, True), (True, True), ("yes", True), ("0", False),
        ("", False), (None, False), ("no", False), (0, False)])
    def test_the_flag(self, flag, want):
        assert dr._dash_csv_wanted({"csv": flag}) is want
        assert dr._dash_csv_wanted(None) is False

    def test_a_dashboard_with_no_filter_downloads_every_row(self, tmp_path):
        r = _saved(tmp_path, _export_spec(csv=True, filters=False))
        text = _saved_file(r, {})
        assert text.count("\r\n") == len(_DF) + 1
        doc = _served(tmp_path, _export_spec(csv=True, filters=False))
        assert _served_file(doc, {}) == text

    def test_the_saved_button_reads_the_filter_callbacks_snapshot(self,
                                                                   tmp_path):
        r = _saved(tmp_path, _export_spec())
        a = _button(r._last_layout_root).js_event_callbacks[
            "button_click"][0].args
        assert r.filter_callbacks
        assert a["orig_source"] is r.filter_callbacks[0].args["orig_source"]
        assert a["filter_specs_json"] == \
            r.filter_callbacks[0].args["filter_specs_json"]


# The widget values both modes are given: foreign == 1 and 18 <= mpg <= 26.
_STATE = {"foreign": "1", "mpg": (18.0, 26.0)}


class TestTheFileHoldsTheFilteredRows:

    _WANT = ("mpg,foreign,make,day\r\n"
             "21,Foreign,x,2020-01-20\r\n"
             '25,Foreign,"say ""hi""",2020-01-21\r\n')

    def test_the_saved_page(self, tmp_path):
        r = _saved(tmp_path, _export_spec())
        assert _saved_file(r, _STATE) == self._WANT

    def test_the_served_app(self, tmp_path):
        doc = _served(tmp_path, _export_spec())
        assert _served_file(doc, _STATE) == self._WANT

    def test_all_rows_before_any_filter_moves_and_the_modes_agree(
            self, tmp_path):
        saved = _saved_file(_saved(tmp_path, _export_spec()), {})
        served = _served_file(_served(tmp_path, _export_spec()), {})
        assert saved == served
        lines = saved.split("\r\n")
        assert lines[0] == "mpg,foreign,make,day"
        assert lines[1] == "22,Domestic,007,2020-01-16"
        assert lines[2] == "17,Foreign,'=cmd(),2020-01-17"
        # The missing mpg is an empty field, the empty string too.
        assert lines[3] == ',Foreign,"a,b",2020-01-18'
        assert lines[4] == "30,Domestic,,"

    @pytest.mark.parametrize("state", [
        {"mpg": (-1.0, 40.0)}, {"foreign": "0"}, {"mpg": (26.0, 40.0)},
        {"foreign": "1", "mpg": (0.0, 1.0)}])
    def test_the_modes_agree_on_every_filter_state(self, tmp_path, state):
        saved = _saved_file(_saved(tmp_path, _export_spec()), state)
        served = _served_file(_served(tmp_path, _export_spec()), state)
        assert saved == served


class TestTheServedDownload:

    def test_the_same_rows_twice_are_two_downloads(self, tmp_path):
        doc = _served(tmp_path, _export_spec())
        btn = _button(doc)
        _click(btn)
        first = list(btn.tags)
        _click(btn)
        assert list(btn.tags) != first

    def test_a_burst_of_clicks_is_held_to_the_bucket(self, tmp_path):
        doc = _served(tmp_path, _export_spec())
        btn = _button(doc)
        for _ in range(dr._DASH_CSV_BURST + 3):
            _click(btn)
        assert btn.tags == [dr._DASH_CSV_BURST]

    def test_the_rows_travel_in_the_document(self, tmp_path):
        """A source nothing on the page refers to never reaches the
        browser; the writer's args are what put it in the document."""
        doc = _served(tmp_path, _export_spec())
        src = _csv_source(doc)
        assert src is not None
        assert src in set(doc.select({"type": ColumnDataSource}))

    def test_the_rows_carry_raw_strings_and_epoch_dates(self, tmp_path):
        doc = _served(tmp_path, _export_spec())
        _click(_button(doc))
        data = _csv_source(doc).data
        assert data["make"][0] == "007" and data["make"][3] is None
        assert data["day"][0] == float(pd.Timestamp("2020-01-16").value
                                       // 1_000_000)
        assert data["mpg"][2] is None
        assert dr._ROW_ID_COLUMN not in data


# ===========================================================================
# 4. The Python helpers, directly
# ===========================================================================

class TestTheHelpers:

    def test_csv_meta(self):
        m = dr._dash_csv_meta(
            ["mpg", "foreign", "make", "day", "q", dr._ROW_ID_COLUMN],
            {"day": "%td", "q": "%tq", "mpg": "%9.1f"}, {"make": True},
            {"origin": {"0": "Domestic"}, "mpg": {"1": "wrong"}},
            {"foreign": "origin"})
        assert m["columns"] == ["mpg", "foreign", "make", "day", "q"]
        assert m["strings"] == ["make"]
        assert m["dates"] == {"day": "td", "q": "tq"}
        # A label set named after the variable is found as the renderer finds it.
        assert m["labels"] == {"foreign": {"0": "Domestic"},
                               "mpg": {"1": "wrong"}}
        assert m["filename"] == "dashboard.csv"

    def test_csv_meta_survives_nonsense(self):
        m = dr._dash_csv_meta(["a"], None, None, None, None)
        assert m == {"columns": ["a"], "strings": [], "dates": {},
                     "labels": {}, "storage": {},
                     "filename": "dashboard.csv"}

    @pytest.mark.parametrize("v,want", [
        ("007", "007"), ("nan", "nan"), ("", None), (None, None),
        (_NAN, None), (3.0, "3.0")])
    def test_csv_text_value(self, v, want):
        assert dr._dash_csv_text_value(v) == want

    def test_csv_payload(self):
        m = dr._dash_csv_meta(["mpg", "make", "day"], {"day": "%td"},
                              {"make": True}, {}, {})
        got = dr._dash_csv_payload(_DF, m)
        assert list(got) == ["mpg", "make", "day"]
        assert got["make"][:2] == ["007", "=cmd()"]
        assert got["mpg"][2] is None
        assert got["day"][3] is None
        assert got["day"][0] == float(pd.Timestamp("2020-01-16").value
                                      // 1_000_000)

    def test_json_value(self):
        assert dr._dash_json_value(None) is None
        assert dr._dash_json_value(_NAN) is None
        assert dr._dash_json_value(float("inf")) is None
        assert dr._dash_json_value("car") == "car"
        assert dr._dash_json_value(2) == 2.0
        assert dr._dash_json_value(pd.Timestamp("2020-01-16")) == float(
            pd.Timestamp("2020-01-16").value // 1_000_000)
        assert dr._dash_json_value(pd.NaT) is None
        assert dr.DashRenderer._to_serialisable("007") == \
            dr._dash_json_value("007")

    def test_frame_filter_mask(self):
        class W:
            def __init__(self, var, kind, value, sentinel="__all__"):
                self._dash_var, self._dash_ftype = var, kind
                self.value, self._dash_sentinel = value, sentinel
        m = dr._dash_frame_filter_mask(_DF, [W("mpg", "range", (18.0, 26.0))])
        assert m.tolist() == [True, False, False, False, True, True]
        m = dr._dash_frame_filter_mask(_DF, [W("mpg", "slider", 25.0)])
        assert m.tolist() == [False, False, False, True, False, True]
        m = dr._dash_frame_filter_mask(_DF, [W("foreign", "dropdown", "0")])
        assert m.tolist() == [True, False, False, True, False, False]
        m = dr._dash_frame_filter_mask(_DF, [W("foreign", "dropdown", 0.0)])
        assert m.tolist() == [True, False, False, True, False, False]
        m = dr._dash_frame_filter_mask(_DF, [W("foreign", "dropdown",
                                               "__all__")])
        assert m.all()
        # A widget with no variable -- the button -- is skipped.
        m = dr._dash_frame_filter_mask(_DF, [object()])
        assert m.all()


class TestAFilterAtItsFullExtentRestrictsNothing:
    """A dropdown at "All" is no filter; a range at [start, end] and a slider
    at its start are none either.  Otherwise an untouched range filter
    dropped every missing value -- from the download before anyone moved
    it, and in the served app from every KPI as soon as ANY filter moved,
    since its recompute applies every widget."""

    def _widgets(self, lo, hi, start=-10.0, end=10.0):
        return [{"value": [lo, hi], "start": start, "end": end}]

    def test_the_saved_mask_keeps_missing_values_at_full_extent(self):
        js = dr._DASH_FILTER_MASK_JS + (
            "\nprocess.stdout.write(JSON.stringify(["
            "dash_filter_mask(ORIG, SPECS, [{value: [-10, 10], start: -10, end: 10}]),"
            "dash_filter_mask(ORIG, SPECS, [{value: [-10, 9], start: -10, end: 10}]),"
            "dash_filter_mask(ORIG, SLIDER, [{value: -10, start: -10, end: 10}]),"
            "dash_filter_mask(ORIG, SLIDER, [{value: -9, start: -10, end: 10}])]));\n")
        got = _run_js(
            "const ORIG = " + json.dumps(_ORIG) + ";\n"
            "const SPECS = [{varname: 'x', type: 'range'}];\n"
            "const SLIDER = [{varname: 'x', type: 'slider'}];\n" + js)
        assert got[0] == [True] * 6
        assert got[1] == [True, False, True, False, True, True]
        assert got[2] == [True] * 6
        assert got[3] == [True, False, True, False, True, True]

    def test_the_served_mask_keeps_missing_values_at_full_extent(self):
        class W:
            def __init__(self, kind, value, start, end):
                self._dash_var, self._dash_ftype = "mpg", kind
                self.value, self.start, self.end = value, start, end
        full = dr._dash_frame_filter_mask(
            _DF, [W("range", (17.0, 30.0), 17.0, 30.0)])
        assert full.all()
        moved = dr._dash_frame_filter_mask(
            _DF, [W("range", (17.0, 29.0), 17.0, 30.0)])
        assert moved.tolist() == [True, True, False, False, True, True]
        assert dr._dash_frame_filter_mask(
            _DF, [W("slider", 17.0, 17.0, 30.0)]).all()

    def test_a_widget_whose_bounds_cannot_be_compared_still_filters(self):
        class W:
            _dash_var, _dash_ftype = "mpg", "range"
            value, start, end = (18.0, 26.0), "a", None
        m = dr._dash_frame_filter_mask(_DF, [W()])
        assert m.tolist() == [True, False, False, False, True, True]
