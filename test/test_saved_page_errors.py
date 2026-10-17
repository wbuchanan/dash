"""WP-31 H1: saved-page script errors reach a status line; sliders recompute
on release; the saved move twins the served redraw.

Measured at 1557f0b (the batch-17 base) under node: a saved-page filter or
brush callback that throws leaves no visible sign -- the exception reaches
the browser console only, with the widgets and sources half-updated; a
saved Slider and RangeSlider run the whole recompute on ``change:value``,
at every drag step, where the served app waits for ``value_throttled``;
and after a saved filter move (DECISIONS A23, D16) an area under
cmissing(n) bridges the gap its first picture split, a lowess line under
cmissing(n) bridges its missing points, and weighted markers keep the
build's scale (the layer was marked with the stale cue instead).  The
histogram's bin-to-rows twin (``dash_bin_members``) is the JavaScript twin
of S51's ``_dash_bin_members``, Stata's bar rule.

The after-a-move oracle is test_saved_filter_layers.py's: the page after a
move must draw what the same page draws of the kept rows, which
test_mode_parity.py holds to the served app.
"""
import json
import math
import os
import re
import sys

import numpy as np
import pytest
from bokeh.models import (ColumnDataSource, CustomJS, Div, RangeSlider,
                          Select, Slider)

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from js_runner import JsSession, fit_helpers_js, requires_node, run_js  # noqa: E402,E501
import test_saved_filter_layers as sl  # noqa: E402
from test_mode_parity import _DF, _diff, _spec  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_CATCH = "} catch (e) { dash_report_js_error(e); throw e; }"
_FIRST = "const orig        = orig_source.data;"


def _page(filt="price, type(slider)", plots=None, kpis=None, bo=None):
    return sl._render(_spec(plots or [plot_for("scatter")],
                            dict(bo or {}, filter=filt), kpis=kpis))


def _err_divs(r):
    return [m for m in r._last_layout_root.references()
            if isinstance(m, Div) and "dash_error_status" in (m.tags or [])]


def _row_of(r, model):
    """The children of the layout model that holds *model*."""
    for m in r._last_layout_root.references():
        kids = list(getattr(m, "children", None) or [])
        if any(k is model for k in kids):
            return kids
    raise AssertionError("not placed")


# ---------------------------------------------------------------------------
# The constant and the reporter
# ---------------------------------------------------------------------------

class TestTheConstant:
    def test_shape(self):
        h = dr._DASH_JS_ERROR_HTML
        for attr in ('role="status"', 'aria-live="polite"',
                     'aria-atomic="true"'):
            assert attr in h
        assert h.count("%s") == 1

    def test_it_is_a_string_literal(self):
        """The constant reaches the page's script as a JSON string, which
        is a JS string literal: no JSON.parse, no quoting rule."""
        js = dr._FILTER_JS
        lit = 'const _DASH_JS_ERROR_HTML = ' + json.dumps(
            dr._DASH_JS_ERROR_HTML) + ";"
        assert lit in js
        assert "__DASH_JS_ERROR_HTML__" not in js


# ---------------------------------------------------------------------------
# The wrapper
# ---------------------------------------------------------------------------

class TestTheWrapper:
    def _body(self):
        return dr._FILTER_JS[len(dr._DASH_FILTER_MASK_JS):]

    def test_shape(self):
        b = self._body()
        assert dr._FILTER_JS.startswith(dr._DASH_FILTER_MASK_JS)
        assert b.lstrip().startswith("try {")
        assert b.rstrip().endswith(_CATCH)
        assert b.count(_CATCH) == 1

    def test_markers_lie_inside_the_try(self):
        """Every marker the brush builder and js_runner slice by, and the
        axis finish call, lie between the try and its catch."""
        js = dr._FILTER_JS
        lo = len(dr._DASH_FILTER_MASK_JS) + self._body().index("try {")
        hi = js.rindex(_CATCH)
        for marker in ("// ---- KPI recompute, shared by",
                       "dash_apply_kpis(new_data,", "function dash_pctl(",
                       "// Stata's kernels ([R] kdensity)",
                       "function dash_own_col", "const ROW_ID = ",
                       "// agg_sources is a Bokeh model list",
                       "if (ac.type === 'histogram') {",
                       "function dash_natscale",
                       "dash_axis_finish(JSON.parse(axis_plans_json)"):
            i = js.index(marker)
            assert lo < i < hi, marker

    @requires_node
    def test_the_page_script_runs_under_node_wrapped(self):
        """A full move through the wrapped script draws the kept rows."""
        spec = _spec([plot_for("scatter")],
                     {"filter": "price, type(slider)"})
        after = sl._saved_after_move(spec, ("Slider", 4500.0))
        assert after == sl._saved_of_rows(spec, "price >= 4500")


class TestTheBrushWrapper:
    def test_shape(self):
        r = _page(kpis=[{"name": "k1", "stat": "mean", "var": "mpg",
                         "title": "M", "fmt": "%9.2f", "update": "brush"}])
        cbs = [cb for src in r.sources.values()
               for cb in src.selected.js_property_callbacks.get(
                   "change:indices", [])]
        assert cbs
        for cb in cbs:
            assert cb.code.startswith(dr._DASH_JS_REPORT_JS + "try {\n")
            assert cb.code.endswith(_CATCH)
            assert cb.args["dash_error_status"] is _err_divs(r)[0]

    def test_guarded_text(self):
        assert dr._dash_js_guarded("x();") == (
            dr._DASH_JS_REPORT_JS + "try {\nx();\n" + _CATCH)
        assert "function dash_html_escape(" in dr._DASH_JS_REPORT_JS


# ---------------------------------------------------------------------------
# A throwing callback
# ---------------------------------------------------------------------------

@requires_node
class TestAThrowingCallback:
    def _throw(self, what):
        r = _page()
        cb = r.filter_callbacks[0]
        code = cb.code.replace(_FIRST, "throw " + what + ";", 1)
        assert code != cb.code
        JsSession([]).run_code(code, cb.args, expect_error=True)
        div = cb.args["dash_error_status"]
        return div

    def test_the_div_reports_it(self):
        div = self._throw('new TypeError("boom <b>")')
        assert div.visible is True
        assert "boom &lt;b&gt;" in div.text
        assert '<p role="status" aria-live="polite"' in div.text

    def test_long_message_is_bounded(self):
        div = self._throw('new Error("x".repeat(400))')
        assert "x" * 297 + "..." in div.text
        assert "x" * 298 not in div.text

    def test_hostile_message_is_text(self):
        div = self._throw(
            'new Error("__proto__ <img src=x onerror=alert(1)>")')
        assert "<img" not in div.text
        assert "__proto__ &lt;img src=x onerror=alert(1)&gt;" in div.text


# ---------------------------------------------------------------------------
# The Div
# ---------------------------------------------------------------------------

class TestTheErrorDiv:
    def test_one_div_per_page(self):
        """One hidden Div, before the stale status Div (an fpfitci the page
        does not refit is marked) and before the reset button."""
        from test_saved_stale_cue import _FROZEN_CI_OPTS
        r = _page(filt="foreign, type(dropdown)",
                  plots=[plot_for("scatter"),
                         plot_for("fpfitci", _FROZEN_CI_OPTS)])
        divs = _err_divs(r)
        assert len(divs) == 1
        d = divs[0]
        assert d.visible is False and d.text == ""
        assert "dash-error-status" in d.css_classes
        assert r.error_status_div is d
        row = _row_of(r, d)
        stale = [i for i, w in enumerate(row) if isinstance(w, Div)
                 and "dash_stale_status" in (w.tags or [])]
        at = [i for i, w in enumerate(row) if w is d][0]
        assert stale and at == stale[0] - 1
        assert at < len(row) - 1

    def test_every_callback_carries_it(self):
        r = _page(filt="price, type(slider)")
        d = r.error_status_div
        assert d is not None
        assert all(cb.args["dash_error_status"] is d
                   for cb in r.filter_callbacks)

    def test_no_div_without_a_filter(self):
        r = sl._render(_spec([plot_for("scatter")], {}))
        assert r.error_status_div is None
        assert not _err_divs(r)


# ---------------------------------------------------------------------------
# The window hooks
# ---------------------------------------------------------------------------

class TestTheWindowHooks:
    def test_the_hook_model(self):
        d = Div()
        hooks = dr._dash_error_hooks(d)
        assert len(hooks) == 1 and isinstance(hooks[0], CustomJS)
        assert hooks[0].args["d"] is d
        assert "window.onerror = function" in hooks[0].code
        assert "addEventListener('unhandledrejection'" in hooks[0].code
        assert dr._dash_error_hooks(None) == []

    @pytest.mark.parametrize("layout", ["auto", "bs"])
    def test_wired_in_both_layouts(self, layout):
        import test_csp as tc
        page = tc._standalone_page(layout)
        assert page.count("window.onerror = function") == 1
        assert "document_ready" in page
        tc._assert_saved_policy(page)

    def test_the_template_has_the_hooks_list(self):
        with open(os.path.join(_HERE, "..", "dash_render.py"),
                  encoding="utf-8") as fh:
            text = fh.read()
        for line in ('"    _err_hooks = []",',
                     '"    _hooks = [*_by_hooks, *_err_hooks]",',
                     '"    if _hooks:",',
                     "\"        doc.js_on_event('document_ready', "
                     "*_hooks)\","):
            assert line in text, line
        assert text.count("_hooks = [*_by_hooks, *_err_hooks]") == 3

    @requires_node
    def test_onerror_writes_the_div(self):
        (hook,) = dr._dash_error_hooks(Div())
        out = run_js(
            "const L = {};\n"
            "globalThis.window = {addEventListener(t, f) { L[t] = f; }};\n"
            "const d = {text: '', visible: false};\n"
            "new Function('d', " + json.dumps(hook.code) + ")(d);\n"
            "window.onerror('m', 's', 1, 2, new Error('bad <x>'));\n"
            "const a = {text: d.text, visible: d.visible};\n"
            "L.unhandledrejection({reason: new Error('late')});\n"
            "process.stdout.write(JSON.stringify([a, d.text]));\n")
        assert out[0]["visible"] is True
        assert "bad &lt;x&gt;" in out[0]["text"]
        assert "late" in out[1]


# ---------------------------------------------------------------------------
# Sliders fire on release
# ---------------------------------------------------------------------------

class TestSlidersFireOnRelease:
    @pytest.mark.parametrize("filt,kind,key", [
        ("price, type(slider)", Slider, "change:value_throttled"),
        ("price, type(range)", RangeSlider, "change:value_throttled"),
        ("foreign, type(dropdown)", Select, "change:value"),
    ])
    def test_keys(self, filt, kind, key):
        r = _page(filt=filt)
        (w,) = r.filter_widgets
        assert isinstance(w, kind)
        assert list(w.js_property_callbacks) == [key]

    @requires_node
    def test_reset_still_recomputes_a_slider(self):
        """The reset writes value_throttled as well as value, under the
        hold, and then runs one filter callback."""
        out = run_js(
            "let runs = 0;\n"
            "const w = {value: 9, value_throttled: 9,"
            " properties: {value_throttled: {}}};\n"
            "const callback = {execute() { runs++; }};\n"
            "new Function('widgets', 'callback', 'initial_json', "
            + json.dumps(dr._DASH_FILTER_RESET_JS) + ")([w], callback, "
            "JSON.stringify([3]));\n"
            "process.stdout.write(JSON.stringify([w.value,"
            " w.value_throttled, runs]));\n")
        assert out == [3, 3, 1]


# ---------------------------------------------------------------------------
# The bin-members twin
# ---------------------------------------------------------------------------

def _bar_members(edges, xs, ids):
    """Stata's bar rule (GlyphMapper._histogram_counts): x is bar
    floor((x - start)/h), folded into the first and last bars."""
    edges = np.asarray(edges, dtype=float)
    nb = len(edges) - 1
    h = (edges[-1] - edges[0]) / nb
    out = [[] for _ in range(nb)]
    for x, i in zip(xs, ids):
        if x is None or not np.isfinite(x):
            continue
        j = int(np.floor((x - edges[0]) / h)) if h > 0 else 0
        out[min(max(j, 0), nb - 1)].append(i)
    return out


@requires_node
class TestBinMembersTwin:
    def test_agrees_with_the_bar_rule(self):
        """S51's twin: Stata's bar rule over equal-width edges, values on
        the edges and beyond both ends folded in."""
        rng = np.random.default_rng(52)
        edges = [0.0, 1.5, 3.0, 4.5, 6.0, 7.5, 9.0, 10.5]
        xs = list(rng.uniform(-1.0, 10.0, 1000).round(1))
        xs += edges + [None, float("nan")]
        ids = list(range(len(xs)))
        js_xs = [None if (x is None or not np.isfinite(x)) else x
                 for x in xs]
        out = run_js(fit_helpers_js()
                     + "process.stdout.write(JSON.stringify("
                     "dash_bin_members(" + json.dumps(edges) + ", "
                     + json.dumps(js_xs) + ", " + json.dumps(ids)
                     + ")));\n")
        assert out == _bar_members(edges, xs, ids)

    def test_a_move_recomputes_the_members(self):
        """A histogram source carrying __dash_bin_rows gets its members
        recomputed from the kept rows after a move."""
        r = _page(filt="foreign, type(dropdown)",
                  plots=[plot_for("histogram")])
        cb = r.filter_callbacks[0]
        (src,) = cb.args["agg_sources"]
        n = len(src.data["top"])
        src.data = dict(src.data, __dash_bin_rows=[[-1]] * n)
        (w,) = r.filter_widgets
        w.value = [v for v, lab in w.options if lab == "Foreign"][0]
        JsSession([]).run(cb)
        (ac,) = json.loads(cb.args["agg_configs_json"])
        kept = _DF[_DF["foreign"] == 1]
        nb = len(ac["bin_edges"]) - 1
        first = ac.get("bin_first") or 0
        grid = [ac["start"] + k * ac["width"]
                for k in range((ac.get("bin") or nb) + 1)]
        rid = cb.args["orig_source"].data[dr._ROW_ID_COLUMN]
        ids = [int(i) for i in np.asarray(rid)[(_DF["foreign"] == 1)
                                                .to_numpy()]]
        want = _bar_members(grid, list(kept["mpg"]), ids)[first:first + nb]
        got = [[int(i) for i in b] for b in src.data["__dash_bin_rows"]]
        assert got == want


# ---------------------------------------------------------------------------
# After a move: area gaps, lowess gaps, weighted sizes (A23, D16)
# ---------------------------------------------------------------------------

def _gappy():
    df = _DF.copy()
    # Rows 3 and 6: one domestic, one foreign car with no mpg.
    df.loc[[2, 5], "mpg"] = np.nan
    return df


_AFTER = [
    ("dropdown to Foreign", "foreign, type(dropdown)",
     ("Select", "Foreign"), "foreign == 1"),
    ("range keeping the gap rows", "price, type(range)",
     ("RangeSlider", (3500.0, 6000.0)), "price >= 3500 & price <= 6000"),
    ("slider dropping a gap row", "price, type(slider)",
     ("Slider", 4100.0), "price >= 4100"),
]


def _same_after(plot, move, df):
    _, filt, action, oracle = move
    spec = _spec([plot], {"filter": filt})
    after = sl._saved_after_move(spec, action, df)
    want = sl._saved_of_rows(spec, oracle, df)
    for i, (a, b) in enumerate(zip(after, want)):
        assert not _diff(a, b), (i, _diff(a, b)[:6])
    assert len(after) == len(want)


@requires_node
class TestAreaGapsAfterAMove:
    @pytest.mark.parametrize("move", _AFTER, ids=[m[0] for m in _AFTER])
    @pytest.mark.parametrize("ptype", ["area", "rarea"])
    def test_the_gap_is_kept_after_a_move(self, ptype, move):
        _same_after(plot_for(ptype, {"cmissing": "n"}), move, _gappy())

    def test_the_record(self):
        """The area's copy records its gaps' row ids for the rebuild."""
        df = _gappy()
        r = sl._render(_spec([plot_for("area", {"cmissing": "n"})],
                             {"filter": "foreign, type(dropdown)"}), df)
        joins = json.loads(r.filter_callbacks[0].args["derived_join_json"])
        (rec,) = [j for j in joins if j and j.get("kind") == "area"]
        assert rec["cmiss"] == "n" and len(rec["gaps"]) == 2
        assert all(len(g) == 1 for g in rec["gaps"])


class TestTheGapHelpers:
    def test_gap_ids(self):
        """One list per zero-height pair _dash_fill_vertices draws, its
        missing rows' ids; leading and trailing missing rows close
        nothing."""
        ok = [False, True, False, False, True, True, False, True, False]
        ids = [10, 11, 12, 13, 14, 15, 16, 17, 18]
        assert dr._dash_fill_gap_ids(ok, ids) == [[12, 13], [16]]
        _xi, _yi, col = dr._dash_fill_vertices(
            list(range(len(ok))), ok, "direct", "n")
        assert int(col.sum()) == 2 * len(dr._dash_fill_gap_ids(ok, ids))

    def test_join_record(self):
        rec = dr._dash_fill_join("x", ("lo", "hi"), "lo", [[3], [5, 6]])
        assert rec == {"kind": "area", "cmiss": "n", "x": "x",
                       "ycols": ["lo", "hi"], "pin": "lo",
                       "gaps": [[3], [5, 6]]}
        json.dumps(rec)


@requires_node
class TestLowessGapsAfterAMove:
    @pytest.mark.parametrize("move", _AFTER, ids=[m[0] for m in _AFTER])
    def test_the_line_breaks_after_a_move(self, move):
        _same_after(plot_for("lowess", {"cmissing": "n"}), move, _gappy())


class TestWeightedSizesTwin:
    _CASES = [[1.0, 4.0, 9.0], [1.0, 10000.0], [2.0, None, 8.0, -1.0, 0.0],
              [None, -2.0], [3.0]]

    @requires_node
    def test_matches_python(self):
        js = (fit_helpers_js() + "const C = " + json.dumps(self._CASES)
              + ";\nprocess.stdout.write(JSON.stringify(C.map(w => "
              "dash_weighted_sizes(w, 6.5, 10).map(v => Number.isNaN(v) "
              "? 'nan' : v))));\n")
        out = run_js(js)
        for w, got in zip(self._CASES, out):
            want = dr._dash_weighted_sizes(
                [np.nan if v is None else v for v in w], 6.5, 10.0)
            for g, e in zip(got, want):
                if np.isnan(e):
                    assert g == "nan"
                else:
                    assert math.isclose(g, e, rel_tol=1e-12)

    @requires_node
    @pytest.mark.parametrize("move", _AFTER, ids=[m[0] for m in _AFTER])
    def test_a_move_rescales(self, move):
        _same_after(plot_for("scatter", {"weight": "aweight",
                                         "wexp": "price"}), move, _DF)

    def test_the_tag(self):
        r = _page(filt="foreign, type(dropdown)",
                  plots=[plot_for("scatter", {"weight": "aweight",
                                              "wexp": "price"})])
        tags = [t for s in r.sources.values() for t in (s.tags or [])
                if isinstance(t, str) and t.startswith("dash_wsize=")]
        assert len(tags) == 1
        col, wexp, xf, yf, base, cap = tags[0][len("dash_wsize="):].split("|")
        assert col == "__dash_wsize" and wexp == "price"
        assert (xf, yf) == ("weight", "mpg")
        assert float(cap) == 10.0 and float(base) > 0
