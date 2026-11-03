"""WP-29 P0.3: an unlabelled variable is named by its name, as twoway names it.

Stata's exporter writes an unlabelled variable's label as ``""``
(``dash_render._dash_write_stata_data``; jsonio's layout).  Every consumer
read the label with ``.get(v, v)``, whose fallback is dead when the key is
present with ``""``, so both renderers drew no axis titles, keyed layers by
their plot type (``scatter``) and named tooltip rows ``''``; the served
app's filter widgets were untitled, and a malformed ``variableLabels``
aborted the build.

twoway's rule (``test/fixtures/unlabelled_truth.json``, written by
``scripts/extract_unlabelled_truth.do``): the label when it is not ``""``,
otherwise the name.  A label of blanks is not empty and is drawn as given
(E.svg).  A histogram is keyed by its y-scale word and a kdensity layer
``kdensity <name>`` (HK.svg, KD2.svg, KDLAB.svg).

The data here are written by ``_dash_write_stata_data`` through
``FakeSfi``: byte for byte what Stata writes.
"""
import itertools
import json
import os
import re
import sys
import warnings

import pytest
from bokeh.document import Document
from bokeh.models import (Axis, ColorBar, CustomJS, HoverTool, Legend,
                          Plot, RangeSlider, Select, Slider)
from bokeh.plotting import figure as _FIG

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402
from by_panel_probe import side_title  # noqa: E402
from conftest import load_app  # noqa: E402
from test_string_value_export import FakeSfi  # noqa: E402
from test_served_linked_views import _fire  # noqa: E402

MODES = ("saved", "served")
_SEQ = itertools.count()

# ---------------------------------------------------------------------------
# The data: 12 rows mirroring scripts/extract_unlabelled_truth.do's _zu_data.
# ---------------------------------------------------------------------------
_NAMES = ["x", "y", "y1", "y2", "z", "g", "t", "w"]
_N = range(1, 13)
_COLUMNS = {
    "x": [2.0 * n for n in _N],
    "y": [n + 0.5 for n in _N],
    "y1": [float(n) for n in _N],
    "y2": [n + 3.0 for n in _N],
    "z": [float(n % 4) for n in _N],
    "g": [float(n % 2) for n in _N],
    "t": [14610.0 + n for n in _N],
    "w": [1.5 * n for n in _N],
}

_FIXTURE = os.path.join(_HERE, "fixtures", "unlabelled_truth.json")


from conftest import render_models  # noqa: E402


def _truth():
    if not os.path.exists(_FIXTURE):
        pytest.fail("test/fixtures/unlabelled_truth.json is missing: run "
                    "scripts/extract_unlabelled_truth.do (WP-29 task 03-02)")
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _probe(pid):
    return _truth()["probes"][pid]


def _rotated(pid):
    return [t for t, _x in _probe(pid)["rotated"]]


def _write_data(tmp_path, labels=None):
    path = str(tmp_path / f"data_{next(_SEQ)}.json")
    dr._dash_write_stata_data(
        path, " ".join(_NAMES),
        sfi=FakeSfi(dict(_COLUMNS), {v: "double" for v in _NAMES},
                    var_labels=dict(labels or {})))
    return path


def _plot(ptype, **kw):
    p = {"type": ptype, "options": kw.pop("options", {})}
    p.update(kw)
    return p


def _sc(y="y", x="x", **o):
    return _plot("scatter", yvar=y, xvar=x, options=o)


def _filter(var, ftype):
    return {"var": var, "varname": var, "type": ftype, "exclude": [],
            "label": ""}


def _spec(graphs, filters=None):
    """*graphs* is a list of (name, plots, graph_options)."""
    gs = []
    for name, plots, go in graphs:
        go = dict(go or {})
        go["name"] = name
        gs.append({"name": name, "graph_options": go, "options": dict(go),
                   "plots": plots, "if_expr": "", "in_expr": ""})
    bo = {"layout": "auto", "link": "", "filter": "", "theme": "",
          "scheme": "", "session_scheme": "", "title": "", "subtitle": "",
          "registry": " ".join(g[0] for g in graphs), "tabs": "",
          "filter_position": "top", "level": "95",
          "formats": {"t": "%td"}}
    if filters:
        bo["filters"] = list(filters)
    return {"graphs": gs, "kpis": [], "build_options": bo}


def _one(plots, **go):
    return _spec([("g1", plots, go)])


def _spec_path(tmp_path, spec):
    sp = str(tmp_path / f"spec_{next(_SEQ)}.json")
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    return sp


def _saved(tmp_path, spec, dp):
    """The saved renderer, rendered."""
    sp = _spec_path(tmp_path, spec)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = dr.DashRenderer(sp, dp)
        render_models(r)
    return r


def _app_module(tmp_path, spec, dp):
    sp = _spec_path(tmp_path, spec)
    ap = str(tmp_path / f"app_{next(_SEQ)}.py")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(ap)
        mod = load_app(ap, f"_ul_app_{next(_SEQ)}")
    return mod, ap


def _served(tmp_path, spec, dp):
    """The served app's document."""
    mod, _ap = _app_module(tmp_path, spec, dp)
    doc = Document()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mod.make_document(doc)
    return doc


def _roots(mode, obj):
    if mode == "saved":
        return list(obj.figures.values()) + list(obj.filter_widgets or [])
    return list(obj.roots)


def _select(mode, obj, cls):
    out, seen = [], set()
    for root in _roots(mode, obj):
        for m in root.select({"type": cls}):
            if m.id not in seen:
                seen.add(m.id)
                out.append(m)
    return out


def _build(mode, tmp_path, spec, labels=None, dp=None):
    dp = dp or _write_data(tmp_path, labels)
    if mode == "saved":
        return _saved(tmp_path, spec, dp)
    return _served(tmp_path, spec, dp)


def _text(v):
    if isinstance(v, dict):
        return v.get("value")
    val = getattr(v, "value", None)
    if val is not None:
        return val
    return v


def _fig_profile(fig):
    def titles(side):
        return [a.axis_label for a in side if isinstance(a, Axis)]
    keys = []
    for lg in fig.select({"type": Legend}):
        if getattr(lg, "name", "") == dr._COLORVAR_LEGEND_NAME:
            continue
        keys.extend(_text(it.label) for it in lg.items)
    hover = [[lab for lab, _f in t.tooltips] for t in fig.tools
             if isinstance(t, HoverTool) and isinstance(t.tooltips, list)]
    return {"x": titles(fig.below), "y": titles(fig.left),
            "right": titles(fig.right), "legend": keys, "hover": hover}


def _profile(mode, obj):
    return [_fig_profile(f) for f in _select(mode, obj, _FIG)]


def _widget_titles(mode, obj):
    return sorted(w.title for cls in (Select, RangeSlider, Slider)
                  for w in _select(mode, obj, cls))


def _first(mode, tmp_path, spec, labels=None):
    obj = _build(mode, tmp_path, spec, labels)
    profs = _profile(mode, obj)
    assert profs, "no figure"
    return profs[0]


# ---------------------------------------------------------------------------
# The rule
# ---------------------------------------------------------------------------
class TestTheVarLabelRule:
    def test_an_empty_label_is_the_name(self):
        assert dr._dash_var_label({"y": ""}, "y") == "y"

    def test_a_label_wins(self):
        assert dr._dash_var_label({"y": "Mileage"}, "y") == "Mileage"

    def test_a_label_of_blanks_is_kept(self):
        assert dr._dash_var_label({"y": "   "}, "y") == "   "
        assert _rotated("ul_blank_title") == ["   "]

    def test_no_name_takes_the_default(self):
        assert dr._dash_var_label({}, "", "x") == "x"
        assert dr._dash_var_label({}, None, "y") == "y"

    def test_a_non_text_label_is_the_name(self):
        for bad in (5, None, {"a": 1}):
            assert dr._dash_var_label({"y": bad}, "y") == "y"

    def test_a_non_text_name_never_raises(self):
        assert dr._dash_var_label(dict(), ["a"]) == "['a']"
        assert dr._dash_var_label(dict(), {"a": 1}) == "{'a': 1}"
        assert dr._dash_var_label(["bad"], "y") == "y"


class TestCleanVarLabels:
    def test_empty_and_non_text_labels_become_the_name(self):
        assert dr._dash_clean_var_labels(
            {"y": "", "x": "Lab", "w": None}) == \
            {"y": "y", "x": "Lab", "w": "w"}

    def test_a_non_mapping_is_empty(self):
        for bad in (["a"], None, "str"):
            assert dr._dash_clean_var_labels(bad) == {}

    def test_a_non_text_or_empty_key_is_dropped(self):
        assert dr._dash_clean_var_labels({3: "z", "": "q"}) == {}


class TestFilterBaseTitle:
    def test_label_then_variable_label_then_name(self):
        f = dr._dash_filter_base_title
        assert f("", {"x": ""}, "x") == "x"
        assert f("  ", {"x": "  "}, "x") == "x"
        assert f("L", {"x": "Lab"}, "x") == "L"
        assert f("", {"x": "Lab"}, "x") == "Lab"
        assert f("", ["x"], "x") == "x"


# ---------------------------------------------------------------------------
# Both modes, on data Stata wrote
# ---------------------------------------------------------------------------
def _dashboard():
    return _spec(
        [("sc", [_sc()], {}),
         ("two", [_sc("y1"), _sc("y2")], {}),
         ("fit", [_sc(), _plot("lfit", yvar="y", xvar="x")], {}),
         ("hist", [_plot("histogram", var="x")], {}),
         ("rcap", [_plot("rcap", yvar1="y1", yvar2="y2", xvar="x")], {})],
        filters=[_filter("x", "range"), _filter("g", "dropdown")])


def _key(p):
    return json.dumps(p, sort_keys=True)


class TestBothModesNameAnUnlabelledVariable:
    @pytest.mark.parametrize("mode", MODES)
    def test_axis_titles_are_the_names(self, mode, tmp_path):
        assert _rotated("ul_scatter") == ["y"]
        assert "x" in _probe("ul_scatter")["flat"]
        p = _first(mode, tmp_path, _one([_sc()]))
        assert (p["x"], p["y"]) == (["x"], ["y"])

    @pytest.mark.parametrize("mode", MODES)
    def test_legend_keys_are_the_names(self, mode, tmp_path):
        want = _probe("ul_two_layers")["keys_in_drawn_order"]
        assert want == ["y1", "y2"]
        p = _first(mode, tmp_path, _one([_sc("y1"), _sc("y2")]))
        assert p["legend"] == want

    @pytest.mark.parametrize("mode", MODES)
    def test_a_fit_beside_data_keys_the_data_by_name(self, mode, tmp_path):
        want = _probe("ul_fit")["keys_in_drawn_order"]
        assert want == ["y", "Fitted values"]
        p = _first(mode, tmp_path,
                   _one([_sc(), _plot("lfit", yvar="y", xvar="x")]))
        assert p["legend"] == want

    @pytest.mark.parametrize("mode", MODES)
    def test_a_mixed_graph_uses_label_or_name(self, mode, tmp_path):
        want = _probe("ul_mixed")["keys_in_drawn_order"]
        assert want == ["First", "y2"]
        p = _first(mode, tmp_path, _one([_sc("y1"), _sc("y2")]),
                   labels={"y1": "First"})
        assert p["legend"] == want

    @pytest.mark.parametrize("mode", MODES)
    def test_a_label_of_blanks_is_drawn_blank(self, mode, tmp_path):
        assert _rotated("ul_blank_title") == ["   "]
        p = _first(mode, tmp_path, _one([_sc("w")]), labels={"w": "   "})
        assert p["y"] == ["   "]
        want = _probe("ul_blank_key")["keys_in_drawn_order"]
        assert want == ["   ", "y2"]
        p = _first(mode, tmp_path, _one([_sc("w"), _sc("y2")]),
                   labels={"w": "   "})
        assert p["legend"] == want

    @pytest.mark.parametrize("mode", MODES)
    def test_legend_on_keys_a_single_layer_by_name(self, mode, tmp_path):
        want = _probe("ul_legend_on")["keys_in_drawn_order"]
        assert want == ["y"]
        p = _first(mode, tmp_path, _one([_sc()], legend="on"))
        assert p["legend"] == want

    @pytest.mark.parametrize("mode", MODES)
    def test_histogram_titles_and_bin_row_name_the_variable(self, mode,
                                                           tmp_path):
        assert _rotated("ul_hist") == ["Density"]
        assert "x" in _probe("ul_hist")["flat"]
        p = _first(mode, tmp_path, _one([_plot("histogram", var="x")]))
        assert (p["x"], p["y"]) == (["x"], ["Density"])
        assert p["hover"] and p["hover"][0][0] == "x"

    @pytest.mark.parametrize("mode", MODES)
    def test_univariate_keys_follow_twoway(self, mode, tmp_path):
        cases = [("ul_hist_kd", {}), ("ul_histpct_kd", {"percent": "percent"}),
                 ("ul_histfreq_kd", {"frequency": "frequency"}),
                 ("ul_histfrac_kd", {"fraction": "fraction"})]
        for pid, hopts in cases:
            want = _probe(pid)["keys_in_drawn_order"]
            p = _first(mode, tmp_path,
                       _one([_plot("histogram", var="x", options=hopts),
                             _plot("kdensity", var="x")]))
            assert p["legend"] == want, pid
        assert _probe("ul_hist_kd")["keys_in_drawn_order"] == \
            ["Density", "kdensity x"]
        kd2 = _one([_plot("kdensity", var="x"), _plot("kdensity", var="y")])
        for pid, labels in (("ul_kd2", None),
                            ("ul_kd_labelled",
                             {"x": "Horizontal", "y": "Vertical"})):
            want = _probe(pid)["keys_in_drawn_order"]
            assert want == ["kdensity x", "kdensity y"]
            p = _first(mode, tmp_path, kd2, labels=labels)
            assert p["legend"] == want, pid

    @pytest.mark.parametrize("mode", MODES)
    def test_tooltip_rows_name_the_variables(self, mode, tmp_path):
        p = _first(mode, tmp_path, _one([_sc()], hover="z"))
        assert p["hover"] == [["x", "y", "z"]]

    @pytest.mark.parametrize("mode", MODES)
    def test_a_computed_layer_never_names_an_unrelated_variable(self, mode,
                                                               tmp_path):
        p = _first(mode, tmp_path, _one([_plot("lfit", yvar="y2", xvar="y1")]))
        assert p["hover"] == [["y1", "y2"]]
        p = _first(mode, tmp_path, _one([_plot("kdensity", var="z")]))
        # WP-30 P1.23b: kdensity z's rows x and y were wrong because they
        # are z's values and its density; the rule that no unrelated
        # variable is named still holds.
        assert p["hover"] == [["z", "Density"]]

    @pytest.mark.parametrize("mode", MODES)
    def test_a_range_tooltip_names_both_ends(self, mode, tmp_path):
        p = _first(mode, tmp_path,
                   _one([_plot("rcap", yvar1="y1", yvar2="y2", xvar="x")]))
        assert p["hover"] == [["x", "y1", "y2"]]

    @pytest.mark.parametrize("mode", MODES)
    def test_by_panels_title_axes_by_name(self, mode, tmp_path):
        assert _rotated("ul_by") == ["y"]
        obj = _build(mode, tmp_path, _one([_sc()], by="g"))
        titles = {t for p in _profile(mode, obj)
                  for t in p["x"] + p["y"] if t}
        # WP-30 P1.15c: twoway draws the titles once, beside and below the
        # panels, so they are read on the grid's title cells too.
        roots = [obj._last_layout_root] if mode == "saved" else obj.roots
        sides = dict(st for root in roots for m in root.references()
                     if isinstance(m, Plot)
                     and (st := side_title(m)) is not None)
        assert sides == {"y": "y", "x": "x"}
        assert titles | set(sides.values()) == {"x", "y"}

    @pytest.mark.parametrize("mode", MODES)
    def test_a_date_axis_is_titled_by_name(self, mode, tmp_path):
        assert "t" in _probe("ul_date")["flat"]
        p = _first(mode, tmp_path, _one([_plot("line", yvar="y", xvar="t")]))
        assert p["x"] == ["t"]

    @pytest.mark.parametrize("mode", MODES)
    def test_a_colour_key_is_titled_by_name(self, mode, tmp_path):
        assert "z" in _rotated("ul_colorvar")
        obj = _build(mode, tmp_path, _one([_sc(colorvar="z")]))
        # Flipped (WP-42 CV-3): the key was a ColorBar titled z; twoway
        # draws swatches beside a z axis, a key cell titled by its Label.
        assert not _select(mode, obj, ColorBar)
        from bokeh.models import Plot
        cells = [p for p in _select(mode, obj, Plot)
                 if "dash_key_cell" in (p.tags or [])]
        assert [c._dash_key_title.text for c in cells] == ["z"]

    @pytest.mark.parametrize("mode", MODES)
    def test_filter_widgets_are_titled_by_name(self, mode, tmp_path):
        spec = _spec([("g1", [_sc()], {})],
                     filters=[_filter("x", "range"), _filter("g", "dropdown"),
                              _filter("w", "range")])
        obj = _build(mode, tmp_path, spec, labels={"w": "   "})
        assert _widget_titles(mode, obj) == ["g", "w", "x"]

    def test_the_modes_agree(self, tmp_path):
        dp = _write_data(tmp_path)
        spec = _dashboard()
        saved = _saved(tmp_path, spec, dp)
        served = _served(tmp_path, spec, dp)
        a = sorted(_profile("saved", saved), key=_key)
        b = sorted(_profile("served", served), key=_key)
        assert len(a) == 5
        assert a == b
        assert _widget_titles("saved", saved) == \
            _widget_titles("served", served) == ["g", "x"]


# ---------------------------------------------------------------------------
# After a filter move
# ---------------------------------------------------------------------------
_JS_TITLE_WRITE = re.compile(r"\.(axis_label|tooltips|title|label)\s*=(?!=)")


class TestAfterAFilterMove:
    def test_served_names_survive_a_move(self, tmp_path):
        """Flipped (WP-30 P1.16): a y title 'y' was wrong because twoway
        draws none when the layers' labels differ (series_label_truth.json
        M08)."""
        spec = _spec([("g1", [_sc(), _sc("y2")], {"hover": "z"})],
                     filters=[_filter("x", "range")])
        doc = _build("served", tmp_path, spec)
        before = _profile("served", doc)
        assert before[0]["x"] == ["x"] and before[0]["y"] == [None]
        assert before[0]["legend"] == ["y", "y2"]
        _fire(doc, "x", (4.0, 24.0))
        assert _profile("served", doc) == before
        assert _widget_titles("served", doc) == ["x"]

    def test_the_saved_scripts_never_rewrite_titles(self, tmp_path):
        spec = _spec([("g1", [_sc()], {})], filters=[_filter("x", "range")])
        dp = _write_data(tmp_path)
        sp = _spec_path(tmp_path, spec)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            page = dr.DashRenderer(sp, dp).render()
        codes = []

        def walk(o):
            if isinstance(o, dict):
                if o.get("name") == "CustomJS" or o.get("type") == "CustomJS":
                    code = (o.get("attributes") or {}).get("code") \
                        or o.get("code")
                    if isinstance(code, str):
                        codes.append(code)
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)

        for blob in re.findall(
                r'<script type="application/json"[^>]*>(.*?)</script>',
                page, re.S):
            try:
                walk(json.loads(blob))
            except ValueError:
                continue
        assert codes, "no CustomJS found on the saved page"
        module_js = [v for v in vars(dr).values()
                     if isinstance(v, str) and len(v) > 200
                     and ("function" in v or "=>" in v)]
        # Flipped by WP-29 P0.17: the stale cue's block, the last of
        # _FILTER_JS, writes one thing -- a frozen layer's legend key, as its
        # build text plus a fixed suffix (" (unfiltered)") and back.  It
        # never writes a title, axis label or tooltip, and no other write
        # is allowed anywhere.
        cue = "// ---- Marks on the layers a saved page does not recompute"
        # WP-30 P1.15c: the by() grid's stacked view (_DASH_BY_STACK_JS)
        # is a layout change, not a filter move: it writes each axis's
        # build-time label back from its JSON data, and nothing else.
        stack_write = "axes[i].axis_label = stacked ? r[2] : r[1];"
        # WP-32 (maintainer ruling over WP-29 BR-07.4): a colour key is
        # levelled again over the kept rows after a move, as twoway draws
        # it; its one label write is a key item's level text.  No title,
        # axis label or tooltip.
        relevel = dr._DASH_CVAR_RELEVEL_JS
        assert [m.group(0) for m in _JS_TITLE_WRITE.finditer(relevel)] \
            == [".label ="], relevel
        # WP-42 CV-4: the text is the bin's label, or under
        # coloruseplegend its level in the variable's format.
        key_write = "it.label = {value: lab};"
        assert key_write in relevel
        codes = [c.replace(key_write, "") for c in codes]
        module_js = [c.replace(key_write, "") for c in module_js]
        # WP-42 LT-22 (the same ruling): contourline's level legend keys
        # the kept rows' cuts after a move, its one label write a key's
        # level text (dash_contourline_legend).
        lt22 = "if (cur !== text) it.label = {value: text};"
        assert dr._FILTER_JS.count(lt22) == 1
        codes = [c.replace(lt22, "") for c in codes]
        module_js = [c.replace(lt22, "") for c in module_js]
        for code in codes + module_js:
            if code.strip() == dr._DASH_BY_STACK_JS.strip():
                assert [m.group(0) for m in _JS_TITLE_WRITE.finditer(code)] \
                    == [".axis_label ="], code
                assert stack_write in code
                assert "const restore = JSON.parse(labels_json);" in code
                continue
            if cue in code:
                head, block = code.split(cue, 1)
                assert [m.group(0) for m in _JS_TITLE_WRITE.finditer(block)] \
                    == [".label ="], block
                assert "_stl_items[k].label = {value:" in block
                code = head
            m = _JS_TITLE_WRITE.search(code)
            assert m is None, code[max(0, m.start() - 80):m.end() + 80]
        assert CustomJS  # the model the page scripts are


# ---------------------------------------------------------------------------
# Malformed labels
# ---------------------------------------------------------------------------
class TestMalformedLabels:
    @pytest.mark.parametrize("mode", MODES)
    @pytest.mark.parametrize("labels", [["a"], {"y": 5}, {"y": {"a": 1}},
                                        {"y": None}],
                             ids=["list", "int", "dict", "null"])
    def test_the_build_draws_names(self, mode, labels, tmp_path):
        dp = _write_data(tmp_path)
        with open(dp, encoding="utf-8") as fh:
            doc = json.load(fh)
        inner = doc.get("StataJSON", doc)
        inner["variableLabels"] = labels
        with open(dp, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)
        obj = _build(mode, tmp_path, _one([_sc()]), dp=dp)
        assert _profile(mode, obj)[0]["y"] == ["y"]


# ---------------------------------------------------------------------------
# The served copy
# ---------------------------------------------------------------------------
class TestTheServedCopy:
    def test_the_app_defines_the_helpers(self, tmp_path):
        dp = _write_data(tmp_path)
        _mod, ap = _app_module(tmp_path, _one([_sc()]), dp)
        with open(ap, encoding="utf-8") as fh:
            src = fh.read()
        for name in ("_dash_var_label", "_dash_clean_var_labels",
                     "_dash_filter_base_title"):
            assert f"def {name}(" in src, name
        assert re.search(r"var_labels = _dash_clean_var_labels\(", src)


# ---------------------------------------------------------------------------
# The fixture
# ---------------------------------------------------------------------------
_TABLE = ("ul_scatter", "ul_multi_y", "ul_two_layers", "ul_mixed",
          "ul_blank_title", "ul_blank_key", "ul_fit", "ul_hist",
          "ul_kdensity", "ul_hist_kd", "ul_histpct_kd", "ul_histfreq_kd",
          "ul_histfrac_kd", "ul_kd2", "ul_kd_labelled", "ul_by",
          "ul_by_labelled", "ul_colorvar", "ul_legend_on", "ul_xlabelled",
          "ul_date", "ul_axis2", "ul_ytitle_size", "ul_rcap", "ul_range_key")


class TestTheFixture:
    def test_meta_keys_and_probes(self):
        d = _truth()
        m = d["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted",
                  "scheme_in_force"):
            assert k in m, k
        assert re.fullmatch(r"[0-9a-f]{40}", m["dash_commit"])
        for pid in _TABLE:
            assert d["probes"][pid]["rc"] == 0, pid
