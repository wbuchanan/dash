"""Filter widgets beyond one value (WP-31 H2f, section 49).

GAPS3 H2: "no multi-select filter, "(missing)" option, slider direction or
reset button".  At 7f28fde ``_DASH_FILTER_TYPES`` was dropdown, range and
slider; a dropdown listed only the non-missing values, so a reader could not
pick the observations with no value nor two categories at once; every slider
ran left to right; and nothing but a reload put the widgets back.

After it, in both modes, from the one shared builder
(``_dash_filter_widget``) and the two mask twins (``_DASH_FILTER_MASK_JS``'s
``dash_filter_mask`` and ``_dash_frame_filter_mask``):

* ``type(multi)`` draws a ``MultiChoice``; nothing chosen keeps every row,
  chosen values keep the rows equal to any of them;
* a dropdown or multi over a variable with a missing value lists
  ``(missing)`` last, which keeps exactly the missing rows;
* ``direction(rtl)`` reaches a slider's and a range's model;
* a dashboard with a filter ends its filter row in a "Reset filters"
  button that restores every widget's opening value.
"""
import itertools
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.events import ButtonClick
from bokeh.models import (Button, ColumnDataSource, MultiChoice, RangeSlider,
                          Select, Slider)

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import make_data_json, render_models  # noqa: E402
from js_runner import run_js  # noqa: E402
from test_adversarial_matrix import _load_app  # noqa: E402

_SEQ = itertools.count()

#: Ten rows: rep has two missing values, tag one empty string, foreign none.
_F = pd.DataFrame({
    "mpg": [22.0, 17.0, 25.0, 30.0, 21.0, 19.0, 14.0, 28.0, 16.0, 23.0],
    "weight": [2930.0, 3350.0, 2200.0, 1800.0, 3000.0, 3100.0, 4080.0,
               2010.0, 3600.0, 2650.0],
    "foreign": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
    "price": [4099.0, 4749.0, 3799.0, 4816.0, 5788.0, 4453.0, 5189.0,
              10372.0, 4082.0, 11385.0],
    "rep": [1.0, 2.0, np.nan, 3.0, 4.0, np.nan, 5.0, 3.0, 4.0, 2.0],
    "tag": ["a", "b", "", "c", "a", "b", "c", "a", "b", "c"],
})
_STRINGS = ("tag",)
_VL = {"origin": {"0": "Domestic", "1": "Foreign"}}
_VLN = {"foreign": "origin"}


def _spec(filters, kpis=None):
    return {"graphs": [{"plots": [{"type": "scatter", "yvar": "mpg",
                                   "xvar": "weight", "options": {}}],
                        "graph_options": {"name": "g1", "title": "g1"},
                        "if_expr": "", "in_expr": ""}],
            "kpis": list(kpis or []),
            "build_options": {
                "layout": "auto", "link": "", "theme": "", "title": "",
                "subtitle": "", "filters": list(filters),
                "registry": "g1"}}


def _inputs(tmp_path, spec, df=_F, vl=_VL, vln=_VLN):
    d = os.path.join(str(tmp_path), "in%d" % next(_SEQ))
    os.makedirs(d)
    sp, dp = os.path.join(d, "spec.json"), os.path.join(d, "data.json")
    data = make_data_json(df, vl, vln)
    for key in ("variableIsString", "variableTypeIsString"):
        for col in _STRINGS:
            if col in df.columns and key in data["StataJSON"]:
                data["StataJSON"][key][col] = True
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    with open(dp, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    return sp, dp


def _saved(tmp_path, spec, **kw):
    sp, dp = _inputs(tmp_path, spec, **kw)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r = dr.DashRenderer(sp, dp)
        render_models(r)
    return r, [str(c.message) for c in caught]


def _served(tmp_path, spec, **kw):
    sp, dp = _inputs(tmp_path, spec, **kw)
    app = os.path.join(os.path.dirname(sp), "app.py")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(app)
    with open(app, encoding="utf-8") as fh:
        ns = _load_app(fh.read(), "fwext_%d" % next(_SEQ))
    doc = Document()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ns["make_document"](doc)
    return doc


def _served_filters(doc):
    return [m for m in doc.select({"type": object})
            if hasattr(m, "_dash_var")]


def _resets(models):
    return [m for m in models if isinstance(m, Button)
            and "dash_filter_reset" in (m.tags or [])]


def _saved_models(r):
    root = r._last_layout_root
    return list(root.references()) if root is not None else []


def _saved_specs(r):
    return json.loads(r.filter_callbacks[0].args["filter_specs_json"])


# ---------------------------------------------------------------------------
# type(multi)
# ---------------------------------------------------------------------------

class TestMulti:

    def test_type_multi_builds_a_multichoice_in_both_modes(self, tmp_path):
        spec = _spec([{"varname": "rep", "type": "multi"}])
        r, msgs = _saved(tmp_path, spec)
        assert [type(w).__name__ for w in r.filter_widgets] == [
            "MultiChoice"], msgs
        doc = _served(tmp_path, spec)
        assert [type(w).__name__ for w in _served_filters(doc)] == [
            "MultiChoice"]
        for w in (r.filter_widgets[0], _served_filters(doc)[0]):
            assert w.value == [] and w.placeholder == "All"

    def test_options_are_labels_and_values_strings(self, tmp_path):
        spec = _spec([{"varname": "foreign", "type": "multi"}])
        r, _ = _saved(tmp_path, spec)
        doc = _served(tmp_path, spec)
        want = [("0.0", "Domestic"), ("1.0", "Foreign")]
        for w in (r.filter_widgets[0], _served_filters(doc)[0]):
            assert [tuple(o) for o in w.options] == want
        [row] = _saved_specs(r)
        assert row["type"] == "multi"
        assert row["multi_values"] == {"0.0": 0.0, "1.0": 1.0}

    def test_over_the_limit_a_numeric_multi_becomes_range(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            got = dr._dash_filter_effective_type(
                "multi", "price_m", _F["price"], 3)
        assert got == "range"
        assert any("price_m" in str(c.message) and "type(range)"
                   in str(c.message) for c in caught), caught

    def test_over_the_limit_a_string_multi_is_truncated_with_a_note(self):
        col = pd.Series(["s%02d" % i for i in range(12)])
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            assert dr._dash_filter_effective_type(
                "multi", "strv_m", col, 5) == "multi"
            w, _ = dr._dash_filter_widget("multi", "strv_m2", col, "t",
                                          max_options=5)
        assert isinstance(w, MultiChoice)
        assert [o[0] for o in w.options] == ["s%02d" % i for i in range(5)]
        notes = [str(c.message) for c in caught]
        for v in ("strv_m", "strv_m2"):
            assert any("filter(%s)" % v in n and "12 distinct" in n
                       and "the first 5" in n for n in notes), notes


# ---------------------------------------------------------------------------
# (missing)
# ---------------------------------------------------------------------------

class TestTheMissingOption:

    @pytest.mark.parametrize("ftype", ["dropdown", "multi"])
    def test_listed_last_only_when_the_column_has_missing(self, ftype):
        w, _ = dr._dash_filter_widget(ftype, "rep", _F["rep"], "rep")
        assert w.options[-1][1] == "(missing)"
        assert w.options[-1][0] == w._dash_missing == "__missing__"
        assert sum(o[1] == "(missing)" for o in w.options) == 1
        w, _ = dr._dash_filter_widget(ftype, "foreign", _F["foreign"], "f")
        assert all(o[1] != "(missing)" for o in w.options)
        assert getattr(w, "_dash_missing", None) is None
        # A string column's missing value is "": listed once, as (missing).
        w, _ = dr._dash_filter_widget(ftype, "tag", _F["tag"], "tag")
        labels = [o[1] for o in w.options]
        assert labels[-1] == "(missing)" and "" not in labels, labels

    def test_the_sentinel_never_collides(self):
        col = pd.Series(["__missing__", "__missing___", "", "x"])
        for ftype in ("dropdown", "multi"):
            w, _ = dr._dash_filter_widget(ftype, "s", col, "s")
            assert w._dash_missing == "__missing____"
            values = [o[0] for o in w.options]
            assert "__missing__" in values and "__missing___" in values
            assert values[-1] == "__missing____"

    def test_the_spec_row_carries_the_sentinel(self, tmp_path):
        spec = _spec([{"varname": "rep", "type": "dropdown"},
                      {"varname": "foreign", "type": "dropdown"}])
        r, _ = _saved(tmp_path, spec)
        rep, foreign = _saved_specs(r)
        assert rep["missing_sentinel"] == "__missing__"
        assert "missing_sentinel" not in foreign


# ---------------------------------------------------------------------------
# The two mask twins
# ---------------------------------------------------------------------------

_MV = {"1.0": 1.0, "2.0": 2.0, "3.0": 3.0, "4.0": 4.0, "5.0": 5.0}
_MASK_CASES = {
    # name: (spec, widget value, the rows kept)
    "multi any of": (
        {"varname": "rep", "type": "multi", "numeric": True,
         "missing_sentinel": "__missing__", "multi_values": _MV},
        ["3.0", "4.0"], [r in (3.0, 4.0) for r in _F["rep"]]),
    "multi empty is all": (
        {"varname": "rep", "type": "multi", "numeric": True,
         "missing_sentinel": "__missing__", "multi_values": _MV},
        [], [True] * len(_F)),
    "missing in dropdown": (
        {"varname": "rep", "type": "dropdown", "numeric": True,
         "sentinel": "__all__", "missing_sentinel": "__missing__"},
        "__missing__", list(_F["rep"].isna())),
    "missing in a string dropdown": (
        {"varname": "tag", "type": "dropdown", "numeric": False,
         "sentinel": "__all__", "missing_sentinel": "__missing__"},
        "__missing__", [t == "" for t in _F["tag"]]),
    "missing in multi with a value": (
        {"varname": "rep", "type": "multi", "numeric": True,
         "missing_sentinel": "__missing__", "multi_values": _MV},
        ["__missing__", "1.0"],
        [bool(np.isnan(r) or r == 1.0) for r in _F["rep"]]),
    "a string multi": (
        {"varname": "tag", "type": "multi", "numeric": False,
         "missing_sentinel": "__missing__",
         "multi_values": {"a": "a", "b": "b", "c": "c"}},
        ["a", "__missing__"], [t in ("a", "") for t in _F["tag"]]),
}


def _orig():
    return {c: [dr._dash_json_value(v) for v in _F[c].tolist()]
            for c in _F.columns}


def _js_mask(spec, value):
    script = (dr._DASH_FILTER_MASK_JS
              + "\nconst orig = " + json.dumps(_orig())
              + ";\nconst specs = " + json.dumps([spec])
              + ";\nconst widgets = " + json.dumps([{"value": value}])
              + ";\nprocess.stdout.write(JSON.stringify("
              "dash_filter_mask(orig, specs, widgets)));")
    return run_js(script)


def _py_mask(spec, value):
    if spec["type"] == "multi":
        w = MultiChoice(value=list(value),
                        options=[(v, v) for v in value])
        w._dash_multi_values = spec.get("multi_values", {})
    else:
        w = Select(value=value, options=[(value, value)])
        w._dash_sentinel = spec.get("sentinel", "__all__")
    w._dash_var = spec["varname"]
    w._dash_ftype = spec["type"]
    w._dash_missing = spec.get("missing_sentinel")
    return dr._dash_frame_filter_mask(_F, [w]).tolist()


class TestTheMaskScript:

    @pytest.mark.parametrize("case", sorted(_MASK_CASES))
    def test_the_script_keeps_the_rows(self, case):
        spec, value, want = _MASK_CASES[case]
        assert _js_mask(spec, value) == want


class TestTheServedMask:

    @pytest.mark.parametrize("case", sorted(_MASK_CASES))
    def test_python_agrees_with_the_script(self, case):
        spec, value, want = _MASK_CASES[case]
        assert _py_mask(spec, value) == want


# ---------------------------------------------------------------------------
# direction()
# ---------------------------------------------------------------------------

class TestDirection:

    def test_rtl_reaches_slider_and_range_in_both_modes(self, tmp_path):
        spec = _spec([{"varname": "price", "type": "slider",
                       "direction": "rtl"},
                      {"varname": "weight", "type": "range",
                       "direction": "rtl"}])
        r, _ = _saved(tmp_path, spec)
        doc = _served(tmp_path, spec)
        for ws in (r.filter_widgets, _served_filters(doc)):
            assert sorted(type(w).__name__ for w in ws) == [
                "RangeSlider", "Slider"]
            assert [w.direction for w in ws] == ["rtl", "rtl"]
        # A date slider takes it too.
        col = pd.Series(pd.to_datetime(["2001-01-02", "2001-03-01"]))
        w, _ = dr._dash_filter_widget("range", "d", col, "d",
                                      date_kind="td", direction="rtl")
        assert type(w).__name__ == "DateRangeSlider" and w.direction == "rtl"

    def test_default_is_ltr(self, tmp_path):
        spec = _spec([{"varname": "price", "type": "slider"}])
        r, _ = _saved(tmp_path, spec)
        assert r.filter_widgets[0].direction == "ltr"

    def test_the_raw_option_carries_it(self):
        [f] = dr._dash_parse_filter_raw(
            "price, type(slider) direction(rtl)", warn=False)
        assert f["type"] == "slider" and f["direction"] == "rtl"
        [f] = dr._dash_parse_filter_raw("price, type(slider)", warn=False)
        assert "direction" not in f


# ---------------------------------------------------------------------------
# The reset button
# ---------------------------------------------------------------------------

_FOUR = [{"varname": "rep", "type": "dropdown"},
         {"varname": "foreign", "type": "multi"},
         {"varname": "price", "type": "slider"},
         {"varname": "weight", "type": "range"}]


class TestTheResetButton:

    def test_present_when_a_filter_exists_absent_otherwise(self, tmp_path):
        r, _ = _saved(tmp_path, _spec(_FOUR))
        [btn] = _resets(_saved_models(r))
        assert btn.label == "Reset filters"
        doc = _served(tmp_path, _spec(_FOUR))
        [sbtn] = _resets(doc.select({"type": object}))
        assert sbtn.label == "Reset filters"
        r, _ = _saved(tmp_path, _spec([]))
        assert _resets(_saved_models(r)) == []
        doc = _served(tmp_path, _spec([]))
        assert _resets(doc.select({"type": object})) == []

    def test_initial_values_recorded(self, tmp_path):
        r, _ = _saved(tmp_path, _spec(_FOUR))
        got = [w._dash_initial for w in r.filter_widgets]
        assert got == ["__all__", [], 3799.0, (1800.0, 4080.0)], got
        [btn] = _resets(_saved_models(r))
        [cb] = btn.js_event_callbacks["button_click"]
        assert cb.args["widgets"] == r.filter_widgets
        assert json.loads(cb.args["initial_json"]) == [
            "__all__", [], 3799.0, [1800.0, 4080.0]]
        assert cb.code == dr._DASH_FILTER_RESET_JS
        # The one run it makes is a filter callback's own.
        assert cb.args["callback"] is r.filter_callbacks[0]
        assert cb.args["callback"].code == dr._FILTER_JS

    def test_one_run_restores_the_opening_rows(self, tmp_path):
        """The reset holds every widget's own callback while it writes
        (``globalThis.__dash_filter_hold``) and then runs the filter
        callback ONCE, which reads every widget and keeps the opening
        rows.  At 1584acd each changed widget fired its own run."""
        r, _ = _saved(tmp_path, _spec(_FOUR))
        specs = _saved_specs(r)
        initial = [dr._dash_json_value(w._dash_initial)
                   if not isinstance(w._dash_initial, (list, tuple))
                   else list(w._dash_initial) for w in r.filter_widgets]
        moved = ["3.0", ["1.0"], 4500.0, [2000.0, 3000.0]]
        script = (dr._DASH_FILTER_MASK_JS
                  + "\nconst orig = " + json.dumps(_orig())
                  + ";\nconst specs = " + json.dumps(specs)
                  + ";\nconst starts = " + json.dumps(
                      [getattr(w, "start", None) for w in r.filter_widgets])
                  + ";\nconst ends = " + json.dumps(
                      [getattr(w, "end", None) for w in r.filter_widgets])
                  + ";\nconst moved = " + json.dumps(moved)
                  + ";\nconst initial_json = " + json.dumps(
                      json.dumps(initial))
                  + ";\nconst runs = [];\nconst widgets = [];\n"
                  "const count = () => dash_filter_mask(orig, specs, widgets)"
                  ".filter(Boolean).length;\n"
                  "const callback = {execute(obj, data) { runs.push(count()); }};\n"
                  "for (let i = 0; i < moved.length; i++) {\n"
                  "  const w = {_v: moved[i], start: starts[i], end: ends[i],"
                  " properties: {}};\n"
                  "  Object.defineProperty(w, 'value', {get() { return this._v; },"
                  " set(v) { this._v = v; if (!globalThis.__dash_filter_hold)"
                  " callback.execute(this, {}); }});\n"
                  "  widgets.push(w);\n}\n"
                  "const before = count();\n"
                  "const out = (() => {\n" + dr._DASH_FILTER_RESET_JS
                  + "\n})();\n"
                  "process.stdout.write(JSON.stringify({before, runs,"
                  " held: !!globalThis.__dash_filter_hold}));")
        got = run_js(script)
        assert got["before"] < len(_F)
        assert got["runs"] == [len(_F)], got
        assert got["held"] is False

    def test_the_filter_script_waits_while_held(self, tmp_path):
        """_FILTER_JS writes nothing while the reset holds it."""
        from js_runner import JsSession
        r, _ = _saved(tmp_path, _spec([{"varname": "rep",
                                        "type": "dropdown"}]))
        [cb] = r.filter_callbacks
        w = r.filter_widgets[0]
        src = cb.args["all_graph_sources"][0]
        n0 = len(src.data["mpg"])
        w.value = 3.0
        sess = JsSession(r.filter_callbacks)
        sess.run_code("globalThis.__dash_filter_hold = true;\n" + cb.code
                      + "\nglobalThis.__dash_filter_hold = false;",
                      cb.args, w)
        assert len(src.data["mpg"]) == n0
        sess.run(cb, w)
        assert len(src.data["mpg"]) == 2

    def test_served_reset_runs_one_move(self, tmp_path):
        doc = _served(tmp_path, _spec(_FOUR))
        ws = {w._dash_var: w for w in _served_filters(doc)}
        [btn] = _resets(doc.select({"type": object}))
        src = next(m for m in doc.select({"type": ColumnDataSource})
                   if "weight" in m.data and "mpg" in m.data
                   and len(m.data["mpg"]) == len(_F))
        n0 = len(src.data["mpg"])
        ws["rep"].value = 3.0
        ws["foreign"].value = ["1.0"]
        assert len(src.data["mpg"]) < n0
        writes = []
        doc.on_change(lambda ev: writes.append(ev))
        btn._trigger_event(ButtonClick(btn))
        assert ws["rep"].value == ws["rep"]._dash_initial
        assert ws["foreign"].value == []
        assert len(src.data["mpg"]) == n0
        # One recompute: the source is written once, not once per widget.
        data_writes = [e for e in writes
                       if getattr(e, "model", None) is src
                       and getattr(e, "attr", None) == "data"]
        assert len(data_writes) == 1, len(data_writes)


# ---------------------------------------------------------------------------
# In a browser (release)
# ---------------------------------------------------------------------------

@pytest.mark.release
class TestInChrome:

    def _page(self, tmp_path, spec, **kw):
        sp, dp = _inputs(tmp_path, spec, **kw)
        r = dr.DashRenderer(sp, dp)
        out = os.path.join(os.path.dirname(sp), "page.html")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with open(out, "w", encoding="utf-8") as fh:
                fh.write(r.render())
        return out

    def _probe(self, path):
        import test_csp_browser as tcb
        return tcb._CspProbe("file://" + path)

    _COUNT = ("JSON.stringify(__dash_models('ColumnDataSource')"
              ".filter(s => s.data.mpg && s.data.weight)"
              ".map(s => s.data.mpg.length)[0])")

    def test_saved_multi_missing_and_reset(self, tmp_path):
        path = self._page(tmp_path, _spec(
            [{"varname": "rep", "type": "multi"},
             {"varname": "price", "type": "slider"}]))
        with self._probe(path) as p:
            n0 = p.read(self._COUNT)
            assert n0 == len(_F)
            p.in_task("__dash_models('MultiChoice')[0].value = "
                      "['3.0', '4.0'];")
            assert p.wait_change(self._COUNT, n0) == 4
            p.in_task("__dash_models('MultiChoice')[0].value = "
                      "['__missing__'];")
            assert p.wait_change(self._COUNT, 4) == 2
            # A slider's callback runs on release (WP-31 H1): a drag ends
            # by writing value_throttled, which a value write alone does
            # not.
            p.in_task("__dash_models('Slider')[0].value = 5000; "
                      "__dash_models('Slider')[0].value_throttled = 5000;")
            assert p.wait_change(self._COUNT, 2) == 0
            p.in_task("(() => { const b = __dash_models('Button').find("
                      "b => b.tags.includes('dash_filter_reset'));"
                      " for (const cb of b.js_event_callbacks"
                      "['button_click'] || []) cb.execute(b); })();")
            assert p.wait_change(self._COUNT, 0) == n0
            assert _own_errors(p) == []

    def test_a_label_with_markup_renders_literally(self, tmp_path):
        vl = {"rl": {"1": "<b>x</b>"}}
        path = self._page(tmp_path, _spec(
            [{"varname": "rep", "type": "multi"}]), vl=vl, vln={"rep": "rl"})
        with self._probe(path) as p:
            text = p.read(
                "(() => { const out = [];"
                " const walk = (root) => { for (const el of"
                " root.querySelectorAll('*')) { if (el.shadowRoot)"
                " walk(el.shadowRoot); if (el.tagName === 'B') out.push('B');"
                " if ((el.textContent || '').includes('<b>x</b>') &&"
                " !el.children.length) out.push('text'); } };"
                " walk(document); return JSON.stringify(out); })()")
        assert "B" not in text and "text" in text, text


def _own_errors(p):
    return list(getattr(p, "_errors", []))
