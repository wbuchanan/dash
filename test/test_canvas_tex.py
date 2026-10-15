"""TeX delimiters in graph text are drawn as typed (WP-30 P1.11a).

The defect.  A ``$$..$$``, ``\\(..\\)`` or ``\\[..\\]`` pair in a title,
subtitle, note, caption, axis title, tick label, by() panel title, legend
key or colour key reached BokehJS raw.  BokehJS typesets such a pair with
MathJax, and a saved page shipped the MathJax bundle for it (3,087,832
bytes against 1,301,750 for the same page in plain words).  MathJax's
``html`` package makes ``\\href{javascript:...}`` a live link and
``\\style{...}`` a style attribute, so user text reached a TeX parser.

The truth.  twoway draws every such pair as typed: ``twoway scatter mpg
weight, title("\\(y\\)") subtitle("\\[z\\]") note("\\$\\$ x \\$\\$")
xtitle("\\(a\\) w") xlabel(2000 "\\(t\\)" 3000) legend(on label(1
"\\(k\\)"))`` exported to SVG holds the six text runs exactly as typed
(StataNow 19.5; the live comparison is the S09 block of
``test_wp30_truth.cscript``).

Where BokehJS parses TeX (3.8-3.9): ``TextAnnotationView._init_text``
(Title, Label), ``AxisView._init_axis_label`` and ``_init_major_labels``
(the axis label and every tick override), and the Title and axis a
ColorBar draws itself.  A Legend's entries and title are DOM text and a
tick formatter's output is plain text; they are finished too, so one rule
covers all graph text.

The fix: ``_dash_finish_graph_text`` applies ``_dash_inert_tex`` to every
canvas text sink, last in each mode.
"""
import inspect
import json
import os
import re
import sys
import textwrap
import time
import warnings

import pytest
import bokeh.models as bm
from bokeh.core.property.vectorization import Field, Value
from bokeh.document import Document
from bokeh.embed.bundle import _model_requires_mathjax
from bokeh.embed.util import contains_tex_string
from bokeh.model import Model
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import responsive_probe  # noqa: E402
from conftest import load_app, make_data_json  # noqa: E402
from js_runner import requires_node  # noqa: E402
from test_mode_parity import (_DF, _fire, _served, _spec,  # noqa: E402
                              _standalone_page, _widgets_of)
from test_saved_stale_cue import (_act, _items_of,  # noqa: E402
                                  _layer_rends, _render, _text)
from test_server_layer_defects import plot_for  # noqa: E402
from test_stale_cue_browser import _run_chrome  # noqa: E402

WJ = "⁠"
_DELIM = re.compile(r"\$\$|\\[()\[\]]")
_RAW = "\\(x\\)"


from conftest import render_models  # noqa: E402


def _live(s):
    return bool(_DELIM.search(s)) or contains_tex_string(s)


def _refs(roots):
    seen = {}
    for r in roots:
        for m in r.references():
            seen[m.id] = m
    return list(seen.values())


def _models(mode, spec):
    """Every model of the document *spec* builds in *mode*."""
    if mode == "standalone":
        r = _render(spec)
        return _refs([r._last_layout_root])
    doc, _ = _served(spec)
    return _refs(doc.roots)


def _sink_texts(m):
    """Every string a finished sink property of *m* draws."""
    out = []
    for prop, how in dr._dash_graph_text_props(m):
        v = getattr(m, prop)
        if how == "text" and isinstance(v, str):
            out.append(v)
        elif how == "map" and v:
            out.extend(x for x in dict(v).values() if isinstance(x, str))
        elif how == "value":
            t = _text(v) if not isinstance(v, str) else v
            if isinstance(t, str):
                out.append(t)
        elif how == "labels":
            out.extend(json.loads(v["labels"]).values())
    return out


# ---------------------------------------------------------------------------
# The pure helpers
# ---------------------------------------------------------------------------

class TestFinishTextValue:

    def test_text_kind_breaks_every_delimiter(self):
        for t in ("\\(x\\)", "\\[x\\]", "$$x$$", "a $$ b", "\\) and \\(",
                  "$$$"):
            new, changed = dr._dash_finish_text_value(t, "text")
            assert changed is True, t
            assert not _live(new), t
            assert new.replace(WJ, "") == t

    def test_text_without_tex_is_unchanged_and_reported_so(self):
        assert dr._dash_finish_text_value("Price $", "text") == (
            "Price $", False)
        assert dr._dash_finish_text_value(None, "text") == (None, False)

    def test_map_kind_finishes_values_and_keeps_keys(self):
        v = {2000.0: "\\(t\\)", 3000.0: "plain"}
        new, changed = dr._dash_finish_text_value(v, "map")
        assert changed is True
        assert set(new) == {2000.0, 3000.0}
        assert new[3000.0] == "plain"
        assert not _live(new[2000.0])
        assert new[2000.0].replace(WJ, "") == "\\(t\\)"
        assert v == {2000.0: "\\(t\\)", 3000.0: "plain"}
        assert dr._dash_finish_text_value({1: "p"}, "map") == ({1: "p"},
                                                                False)

    def test_value_kind_finishes_a_fixed_label_and_leaves_a_field(self):
        want = {"value": dr._dash_inert_tex(_RAW)}
        for v in (Value(_RAW), {"value": _RAW}, _RAW):
            new, changed = dr._dash_finish_text_value(v, "value")
            assert changed is True and new == want, v
        f = Field("k")
        assert dr._dash_finish_text_value(f, "value") == (f, False)
        d = {"field": "k"}
        assert dr._dash_finish_text_value(d, "value") == (d, False)
        assert dr._dash_finish_text_value(None, "value") == (None, False)

    def test_labels_kind_rewrites_the_json_map(self):
        args = {"labels": json.dumps({"2000.0": "$$a$$", "3000.0": "b"})}
        new, changed = dr._dash_finish_text_value(args, "labels")
        assert changed is True
        assert new["labels"] == json.dumps(
            {"2000.0": dr._dash_inert_tex("$$a$$"), "3000.0": "b"})
        assert json.loads(args["labels"])["2000.0"] == "$$a$$"

    def test_a_malformed_label_map_is_left_alone(self):
        for args in ({"labels": "{bad"}, {"labels": json.dumps(["\\(x\\)"])},
                     {"labels": json.dumps({"a": 1, "b": "\\(x\\)"})},
                     {"x": "\\(y\\)"}, {"labels": 5}):
            assert dr._dash_finish_text_value(args, "labels") == (
                args, False), args


# ---------------------------------------------------------------------------
# The pass, on hand-built figures
# ---------------------------------------------------------------------------

def _label_map(text):
    return bm.CustomJSTickFormatter(
        args={"labels": json.dumps({"1.0": text})},
        code="const m = JSON.parse(labels); "
             "return m[String(tick)] || String(tick);")


def _full_figure(text):
    fig = figure(title=text, x_axis_label=text, y_axis_label=text)
    fig.xaxis[0].major_label_overrides = {2000: text}
    right = bm.LinearAxis(axis_label=text, major_label_overrides={1: text})
    fig.add_layout(right, "right")
    fig.yaxis[0].formatter = _label_map(text)
    fig.add_layout(bm.Label(x=0, y=0, text=text))
    r = fig.scatter([1, 2], [1, 2])
    fig.add_layout(bm.Legend(items=[
        bm.LegendItem(label=Value(text), renderers=[r]),
        bm.LegendItem(label=Field("k"), renderers=[r])], title=text),
        "right")
    fig.add_layout(bm.ColorBar(
        color_mapper=bm.LinearColorMapper(palette="Viridis256", low=0,
                                          high=1),
        title=text, major_label_overrides={0: text}), "right")
    return fig


def _all_sink_texts(fig):
    out = []
    for m in dr._dash_graph_text_models(fig):
        out.extend(_sink_texts(m))
    return out


def _doc_json(fig):
    doc = Document()
    doc.add_root(fig)
    return doc, json.dumps(doc.to_json(), sort_keys=True, default=str)


class TestTheDocumentPass:

    def test_each_sink_is_finished(self):
        fig = _full_figure(_RAW)
        assert dr._dash_finish_graph_text({"g1": fig}) == 9
        texts = _all_sink_texts(fig)
        assert len(texts) == 12
        for t in texts:
            assert not _live(t), t
            assert t.replace(WJ, "") == _RAW

    def test_text_without_tex_leaves_the_document_unchanged(self):
        fig = _full_figure("plain words")
        doc, before = _doc_json(fig)
        assert dr._dash_finish_graph_text({"g1": fig}) == 0
        assert json.dumps(doc.to_json(), sort_keys=True,
                          default=str) == before

    def test_a_second_call_changes_nothing(self):
        fig = _full_figure(_RAW)
        assert dr._dash_finish_graph_text({"g1": fig}) == 9
        doc, before = _doc_json(fig)
        assert dr._dash_finish_graph_text({"g1": fig}) == 0
        assert json.dumps(doc.to_json(), sort_keys=True,
                          default=str) == before

    def test_a_finished_model_is_not_visited_again(self):
        fig = figure(title=_RAW)
        setattr(fig.title, dr._DASH_GRAPH_TEXT_DONE, True)
        assert dr._dash_finish_graph_text({"g1": fig}) == 0
        assert fig.title.text == _RAW

    def test_every_other_model_is_left_alone(self):
        src = bm.ColumnDataSource(data={"x": [1], "y": [1], "s": [_RAW]})
        fig = figure()
        r = fig.scatter("x", "y", source=src, name=_RAW)
        cmap = bm.CategoricalColorMapper(factors=[_RAW], palette=["red"])
        ls = bm.LabelSet(x="x", y="y", text="s", source=src)
        fig.add_layout(ls)
        ls_text = ls.text
        hov = bm.HoverTool(tooltips=[(_RAW, "@s")])
        fig.add_tools(hov)
        fmt = bm.CustomJSTickFormatter(
            args={"fmt": _RAW, "kind": "n", "storage": "d"},
            code="return String(tick);")
        fig.xaxis[0].formatter = fmt
        dr._dash_finish_graph_text({"g1": fig})
        assert src.data["s"] == [_RAW]
        assert r.name == _RAW
        assert list(cmap.factors) == [_RAW]
        assert ls.text == ls_text
        assert hov.tooltips == [(_RAW, "@s")]
        assert fmt.args["fmt"] == _RAW

    def test_the_walk_finds_every_text_model_and_no_source(self, monkeypatch):
        fig = _full_figure(_RAW)
        models = dr._dash_graph_text_models(fig)
        kinds = [type(m).__name__ for m in models]
        assert any(m is fig.title for m in models)
        for k in ("LinearAxis", "CustomJSTickFormatter", "Legend",
                  "LegendItem", "ColorBar", "Label"):
            assert k in kinds, kinds
        assert kinds.count("LegendItem") == 2
        assert not any(isinstance(m, bm.ColumnDataSource) for m in models)

        def boom(self, *a, **k):
            raise AssertionError("the pass walked references()")

        monkeypatch.setattr(Model, "references", boom)
        assert dr._dash_finish_graph_text({"g1": fig}) == 9

    def test_the_sink_props_name_only_text_sinks(self):
        P = dr._dash_graph_text_props
        assert P(bm.Title()) == (("text", "text"),)
        assert P(bm.Label()) == (("text", "text"),)
        assert P(bm.LinearAxis()) == (("axis_label", "text"),
                                      ("major_label_overrides", "map"))
        assert P(bm.ColorBar()) == (("title", "text"),
                                    ("major_label_overrides", "map"))
        assert P(bm.Legend()) == (("title", "text"),)
        assert P(bm.LegendItem()) == (("label", "value"),)
        assert P(_label_map("x")) == (("args", "labels"),)
        disp = bm.CustomJSTickFormatter(
            args={"fmt": "%9.0g", "kind": "n", "storage": "d"},
            code="return String(tick);")
        assert P(disp) == ()
        assert P(bm.Grid()) == ()
        assert P(bm.Span()) == ()

    def test_a_hundred_panels_take_well_under_a_second(self):
        figs = {}
        for i in range(100):
            f = figure(title=f"{_RAW} - {i}", x_axis_label=_RAW,
                       y_axis_label=_RAW)
            f.scatter(list(range(200)), list(range(200)))
            figs[f"g1__by__{i}"] = f
        t0 = time.perf_counter()
        assert dr._dash_finish_graph_text(figs) == 300
        assert time.perf_counter() - t0 < 1.0


# ---------------------------------------------------------------------------
# The saved page
# ---------------------------------------------------------------------------

def _lfit_spec(go=None):
    # fpfit recast(line): a fit the saved page still marks; lfit is
    # refitted (WP-31 F1a), fpfit too (F1g), a recast fit is not (GAPS3
    # C16).
    return _spec([plot_for("scatter"),
                   plot_for("fpfit", {"recast": "line"})],
                 {"filter": "foreign, type(dropdown)"}, go)


class TestTheSavedPage:

    def test_a_tex_title_ships_no_mathjax(self):
        r, _, page = _standalone_page(_spec([plot_for("scatter")], None,
                                            {"title": '"\\(y\\)"'}))
        _, _, plain = _standalone_page(_spec([plot_for("scatter")], None,
                                             {"title": '"y"'}))
        assert "bokeh-mathjax" not in page
        bad = [type(m).__name__ for m in _refs([r._last_layout_root])
               if _model_requires_mathjax(m)]
        assert not bad, bad
        n1, n0 = len(page.encode("utf-8")), len(plain.encode("utf-8"))
        assert abs(n1 - n0) < 2000, (n1, n0)

    def test_the_pass_runs_before_the_stale_cue_reads_the_legend(
            self, monkeypatch):
        calls = []
        orig_pass = dr._dash_finish_graph_text
        orig_cue = dr.DashRenderer._stale_cue_args

        def spy_pass(figures):
            calls.append("pass")
            return orig_pass(figures)

        def spy_cue(self, *a, **k):
            calls.append("stale")
            return orig_cue(self, *a, **k)

        monkeypatch.setattr(dr, "_dash_finish_graph_text", spy_pass)
        monkeypatch.setattr(dr.DashRenderer, "_stale_cue_args", spy_cue)
        _render(_lfit_spec())
        assert "pass" in calls and "stale" in calls, calls
        assert calls.index("pass") < calls.index("stale"), calls


class TestAfterAFilterMove:

    _GO = {"title": '"\\(y\\)"', "legend": 'label(2 "\\(fit\\)")'}

    def test_saved_stale_cue_carries_the_finished_key(self):
        r = _render(_lfit_spec(self._GO))
        cfgs = json.loads(r.filter_callbacks[0].args["stale_configs_json"])
        texts = [t for c in cfgs for _k, t in c["items"] if t is not None]
        assert texts
        for t in texts:
            assert not _live(t), t
            assert t.replace(WJ, "") == "\\(fit\\)"

    @requires_node
    def test_saved_key_after_the_move(self):
        r = _render(_lfit_spec(self._GO))
        f = r.figures["g1"]
        title = f.title.text
        _act(r, ("Select", "Foreign"))
        items = _items_of(f, _layer_rends(r))
        assert items
        want = (dr._dash_inert_tex("\\(fit\\)")
                + dr._DASH_STALE_SUFFIX["fit"])
        for it in items:
            assert _text(it.label) == want
            assert not _live(_text(it.label))
        assert f.title.text == title
        assert not _live(title)

    def test_served_text_is_unchanged_by_a_move(self):
        doc, _ = _served(_lfit_spec(self._GO))

        def snap():
            out = []
            for m in _refs(doc.roots):
                if dr._dash_graph_text_props(m):
                    for t in _sink_texts(m):
                        out.append((type(m).__name__, t))
            return sorted(out)

        before = snap()
        assert before
        sel = [w for w in _widgets_of(doc) if isinstance(w, bm.Select)][0]
        raw = [v for v, lab in sel.options if lab == "Foreign"]
        _fire(sel, raw[0])
        assert snap() == before
        for _k, t in before:
            assert not _live(t), t


# ---------------------------------------------------------------------------
# Both modes
# ---------------------------------------------------------------------------

MODES = ("standalone", "served")


class TestBothModes:

    @pytest.mark.parametrize("mode", MODES)
    def test_the_colour_key_text(self, mode):
        cont = _spec([plot_for("scatter", {"colorvar": "price"})], None,
                     {"ztitle": '"\\(c\\)"', "zlabel": '5000 "$$a$$" 10000'})
        disc = _spec([plot_for("scatter", {"colorvar": "rep",
                                           "colordiscrete": "yes"})], None,
                     {"ztitle": '"\\[d\\]"'})
        for spec, wants, kinds in (
                (cont, {"\\(c\\)", "$$a$$"}, (bm.ColorBar,)),
                (disc, {"\\[d\\]"}, (bm.Legend, bm.LegendItem))):
            seen = set()
            for m in _models(mode, spec):
                if isinstance(m, kinds):
                    for t in _sink_texts(m):
                        assert not _live(t), (mode, type(m).__name__, t)
                        seen.add(t.replace(WJ, ""))
            assert wants <= seen, (mode, wants, seen)

    @pytest.mark.parametrize("mode", MODES)
    def test_a_pair_formed_by_the_panel_join_is_broken(self, mode, tmp_path):
        spec = _spec([plot_for("scatter")], None,
                     {"title": '"\\("', "by": "foreign, total"})
        data = make_data_json(_DF, {"origin": {"0": "Domestic",
                                               "1": "y\\)"}},
                              {"foreign": "origin"})
        sp, dp = tmp_path / "s.json", tmp_path / "d.json"
        sp.write_text(json.dumps(spec))
        dp.write_text(json.dumps(data))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if mode == "standalone":
                r = dr.DashRenderer(str(sp), str(dp))
                render_models(r)
                models = _refs([r._last_layout_root])
            else:
                ap = tmp_path / "app.py"
                dr.ServerAppBuilder(str(sp), str(dp)).build(str(ap))
                mod = load_app(str(ap), f"_canvas_tex_join_{mode}")
                doc = Document()
                mod.make_document(doc)
                models = _refs(doc.roots)
        titles = [m.text for m in models if isinstance(m, bm.Title)
                  and "dash_stale_cue" not in (m.tags or [])
                  and isinstance(m.text, str)]
        joined = [t for t in titles if "y\\)" in t.replace(WJ, "")]
        assert joined, titles
        assert len([t for t in titles if "Total" in t]) >= 1, titles
        for t in titles:
            assert not _live(t), (mode, t)

    @pytest.mark.parametrize("mode", MODES)
    def test_every_canvas_model_is_finished(self, mode, tmp_path):
        from test_label_sinks import _build
        b = _build(tmp_path, mode, "all")
        n = 0
        for m in b.models:
            if not dr._dash_graph_text_props(m):
                continue
            if isinstance(m, bm.Title) and "dash_stale_cue" in (m.tags or []):
                continue
            n += 1
            assert getattr(m, dr._DASH_GRAPH_TEXT_DONE, False), (
                f"{mode}: a {type(m).__name__} was made after the canvas-"
                f"text pass and not finished: {_sink_texts(m)!r}")
        assert n > 20


# ---------------------------------------------------------------------------
# The served app's source
# ---------------------------------------------------------------------------

def _app_source(tmp_path, spec):
    sp, dp, ap = (tmp_path / "s.json", tmp_path / "d.json",
                  tmp_path / "app.py")
    sp.write_text(json.dumps(spec))
    dp.write_text(json.dumps(make_data_json(
        _DF, {"origin": {"0": "Domestic", "1": "Foreign"}},
        {"foreign": "origin"})))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(str(sp), str(dp)).build(str(ap))
    return ap.read_text()


class TestTheServedApp:

    def test_make_document_runs_the_pass_after_the_panels_and_before_the_widgets(  # noqa: E501
            self, tmp_path):
        src = _app_source(tmp_path, _spec(
            [plot_for("scatter")], {"filter": "foreign, type(dropdown)"},
            {"by": "foreign"}))
        call = src.find("\n    _dash_finish_graph_text(figures)\n")
        assert call > 0
        assert src.rfind("_dash_share_by_scales([figures[_f]") < call
        # Flipped (WP-30 P1.15a): the anchor was the panel-title join,
        # which is gone; the label row is drawn by _dash_by_panel_label.
        assert 0 < src.find("_dash_by_panel_label(fig, _fac_label") < call
        assert call < src.find(
            "# ---- Persist per-graph qualifier metadata")
        assert call < src.find("# ---- Filter widgets + Python callbacks ----")

    def test_the_pass_travels_by_source(self, tmp_path):
        src = _app_source(tmp_path, _spec([plot_for("scatter")]))
        for fn in ("_dash_finish_graph_text", "_dash_graph_text_models",
                   "_dash_graph_text_props", "_dash_finish_text_value"):
            body = textwrap.dedent(inspect.getsource(getattr(dr, fn)))
            assert body in src, fn
        assert re.search(r"^_DASH_GRAPH_TEXT_SINKS = ", src, re.M)
        assert re.search(r"^_DASH_GRAPH_TEXT_DONE = ", src, re.M)


# ---------------------------------------------------------------------------
# In the browser
# ---------------------------------------------------------------------------

_PROBE = r"""
<script>
(function () {
  function kind(v) {
    return v && v.model ? (v.model.type || v.model.constructor.name) : null;
  }
  function count() {
    const out = {tex: 0, plain: 0};
    for (const root of Object.values(window.Bokeh.index)) {
      const views = root.owner ? [...root.owner.all_views()] : [];
      for (const v of views) {
        const subs = [v._text_view, v._axis_label_view];
        const ml = v._major_label_views;
        if (ml) {
          if (typeof ml.values === "function") subs.push(...ml.values());
          else subs.push(...Object.values(ml));
        }
        for (const s of subs) {
          const k = kind(s);
          if (k === "TeX") out.tex++;
          else if (k === "PlainText") out.plain++;
        }
      }
    }
    return out;
  }
  function wait() {
    if (!window.Bokeh || !window.Bokeh.index ||
        !Object.keys(window.Bokeh.index).length) {
      setTimeout(wait, 100);
      return;
    }
    setTimeout(function () {
      const pre = document.createElement("pre");
      pre.id = "r";
      try { pre.textContent = JSON.stringify(count()); }
      catch (e) { pre.textContent = JSON.stringify({error: String(e)}); }
      document.body.appendChild(pre);
    }, 1500);
  }
  wait();
})();
</script>
"""


@pytest.mark.release
class TestInChrome:

    def test_bokehjs_draws_every_canvas_text_as_plain_text(self):
        if responsive_probe.find_chrome() is None:
            pytest.skip("headless Chrome is not installed; set DASH_CHROME "
                        "(a skip is red under DASH_STRICT=1)")
        spec = _spec([plot_for("scatter"), plot_for("lfit"),
                      plot_for("scatter", {"colorvar": "price"})],
                     {"filter": "foreign, type(dropdown)"},
                     {"title": '"\\(y\\)"', "subtitle": '"\\[z\\]"',
                      "xtitle": '"$$x$$"', "xlabel": '3000 "\\(t\\)" 4000',
                      "legend": 'label(2 "\\(f\\)")',
                      "ztitle": '"\\(c\\)"'})
        _, _, page = _standalone_page(spec)
        got = _run_chrome(responsive_probe.admit_script(page, _PROBE))
        assert "error" not in got, got
        assert got["tex"] == 0, got
        assert got["plain"] >= 7, got


# ---------------------------------------------------------------------------
# The help
# ---------------------------------------------------------------------------

class TestTheHelp:

    def test_the_help_says_tex_is_drawn_as_typed(self):
        with open(os.path.join(_HERE, "..", "dash.sthlp"),
                  encoding="utf-8") as fh:
            paras = re.split(r"\n\s*\n", fh.read())
        hits = [" ".join(p.split()) for p in paras
                if "Within the file, data values are base64-encoded" in p]
        assert len(hits) == 1
        assert "is never handed to a TeX engine" in hits[0]
        assert "drawn as typed, as {cmd:twoway} draws them" in hits[0]
