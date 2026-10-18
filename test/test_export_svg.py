"""test_export_svg.py -- the toolbar's Save as SVG action (WP-30 P1.28b,
M8; register P1.28.2 and P1.28.7).

Every toolbar that holds a save button, in the saved page and the served
app, also holds ONE ``CustomAction`` tagged ``dash_svg_save``.  Its
``CustomJS`` asks BokehJS for a vector SVG of the model that toolbar's PNG
save writes -- ``Bokeh.index.find_one(grid).export("svg").to_blob()`` --
and downloads it as ``dashboard.svg`` or ``<name>.svg``.  No figure is drawn
with an SVG backend: in a ``gridplot`` that breaks the PNG save
(``drawImage`` TypeError, bokeh 3.8.0 and 3.9.0, measured).

The action is added by ``_dash_name_save``, the helper both modes already
name every save button through (the served app copies it by name), so the
model tests here cover both modes and the walks below read each mode's
documents.  The Chrome classes are the release tier, as
test_csp_browser.py's are; they skip only without Chrome, and a skip is
red under ``DASH_STRICT=1``.
"""
import base64
import json
import os
import re
import sys
import tempfile
import time
import warnings

import pytest
from bokeh.document import Document
from bokeh.layouts import gridplot
from bokeh.models import (CustomAction, Div, GridPlot, Plot, SaveTool,
                          Select)
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import js_runner  # noqa: E402
import responsive_probe  # noqa: E402
import test_toolbar as tt  # noqa: E402
from test_adversarial_matrix import _page_blocks  # noqa: E402

_TAG = "dash_svg_save"
_CHROME = responsive_probe.find_chrome() is not None


def _actions(model):
    """The Save as SVG actions on *model*'s own toolbar."""
    tools = getattr(getattr(model, "toolbar", None), "tools", None) or ()
    return [t for t in tools
            if isinstance(t, CustomAction) and _TAG in (t.tags or ())]


def _saves(model):
    tools = getattr(getattr(model, "toolbar", None), "tools", None) or ()
    return [t for t in tools if isinstance(t, SaveTool)]


# ---------------------------------------------------------------------------
# The constants
# ---------------------------------------------------------------------------

class TestTheConstants:

    def test_the_code_is_fixed_and_plain(self):
        js = dr._DASH_SVG_SAVE_JS
        assert isinstance(js, str)
        for need in ("find_one", 'export("svg")', "to_blob",
                     "URL.createObjectURL", "window.alert"):
            assert need in js, need
        for bad in ("eval(", "Function(", "innerHTML", "fetch("):
            assert bad not in js, bad

    def test_the_icon_is_a_small_data_uri(self):
        icon = dr._DASH_SVG_SAVE_ICON
        head = "data:image/svg+xml;base64,"
        assert icon.startswith(head) and len(icon) <= 1024, len(icon)
        assert base64.b64decode(icon[len(head):]).decode().startswith("<svg")


# ---------------------------------------------------------------------------
# _dash_name_save adds the action
# ---------------------------------------------------------------------------

def _fig():
    return figure(tools=dr._DASH_FIGURE_TOOLS)


class TestTheAction:

    def test_a_grid_and_a_figure_each_gain_one_action(self):
        grid = gridplot([[_fig(), _fig()]])
        fig = _fig()
        for model, name, want in ((grid, None, "dashboard"),
                                  (fig, "g1", "g1")):
            assert dr._dash_name_save(model, name) is model
            (act,) = _actions(model)
            (save,) = _saves(model)
            tools = list(model.toolbar.tools)
            assert tools.index(act) > tools.index(save), want
            assert act.description == "Save as SVG"
            assert act.icon == dr._DASH_SVG_SAVE_ICON
            assert act.callback.code == dr._DASH_SVG_SAVE_JS
            assert act.callback.args["grid"] is model
            assert act.callback.args["name"] == save.filename == want
        # the figure's nine tools, then the action
        assert tt._names(fig)[:9] == list(tt._NINE)
        assert tt._names(fig)[9:] == ["CustomAction"]

    def test_a_second_call_adds_nothing(self):
        fig = _fig()
        dr._dash_name_save(fig, "g1")
        dr._dash_name_save(fig, "g2")
        (act,) = _actions(fig)
        assert act.callback.args["name"] == "g2"
        assert act.callback.args["grid"] is fig

    def test_no_save_button_no_action(self):
        fig = figure(tools="pan,reset")
        div = Div(text="k1")
        assert dr._dash_name_save(fig, "g1") is fig
        assert dr._dash_name_save(div, "k1") is div
        assert dr._dash_name_save(None) is None
        assert tt._names(fig) == ["PanTool", "ResetTool"]

    def test_only_a_stata_name_reaches_the_arg(self):
        for bad in ("a/b", "../x", "<s>", "a" * 33, 5):
            fig = _fig()
            dr._dash_name_save(fig, bad)
            assert _actions(fig)[0].callback.args["name"] == "dashboard", bad

    @js_runner.requires_node
    def test_js_and_python_agree_on_the_stem(self):
        names = ["a/b", "../x", "<s>", "a" * 33, 5, "g1", "_x", "A9", "",
                 None, "é", "a b"]
        src = r"""
const out = [];
globalThis.window = {alert: () => out.push("ALERT")};
globalThis.document = {
  createElement: () => ({style: {}, remove() {},
                         click() { out.push(this.download); }}),
  body: {appendChild() {}}};
globalThis.Bokeh = {index: {find_one: () => ({export: () => ({
  to_blob: () => Promise.resolve({})})})}};
URL.createObjectURL = () => "blob:x";
URL.revokeObjectURL = () => {};
const f = new Function("grid", "name", %s);
(async () => {
  for (const n of %s) { f({}, n); await new Promise(r => setImmediate(r)); }
  console.log(JSON.stringify(out));
  process.exit(0);
})();
""" % (json.dumps(dr._DASH_SVG_SAVE_JS), json.dumps(names))
        got = js_runner.run_js(src)
        want = [dr._dash_save_filename(n) + ".svg" for n in names]
        assert got == want, list(zip(names, got, want))


# ---------------------------------------------------------------------------
# Every toolbar of both modes
# ---------------------------------------------------------------------------

#: test_toolbar's grids, a layout(bs) page with a KPI, a by() graph and a
#: graph, and a tab under layout(bs).
_CASES = dict(tt._CORPUS)
_CASES["layout(bs), a KPI and a by() graph"] = lambda: tt._spec(
    [tt._graph("g1"), tt._graph("g2", by="foreign")], kpis=[tt._kpi()],
    layout="bs")
_CASES["layout(bs) with a tab"] = lambda: tt._spec(
    [tt._graph("g1"), tt._graph("g2", [tt._LINE])], layout="bs",
    tabs="A: g2")


def _saved_docs(tmp_path, spec):
    """The documents a saved page embeds, read back from the page."""
    _r, page = tt._saved(tmp_path, spec)
    out = []
    for block in _page_blocks(page):
        import html as _html
        for dj in json.loads(_html.unescape(block)).values():
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                out.append(Document.from_json(dj))
    return out


def _served_docs(tmp_path, spec):
    return [tt._served(tmp_path, spec)[0]]


def _bars(docs):
    return [m for d in docs for m in d.models
            if isinstance(m, (Plot, GridPlot))]


_MODES = {"saved": _saved_docs, "served": _served_docs}


@pytest.mark.parametrize("mode", sorted(_MODES))
class TestEveryToolbar:

    def test_one_action_beside_each_save(self, tmp_path, mode):
        """A toolbar the page shows holds one action iff it holds a save
        button, named as that save button; a hidden toolbar (a figure's
        inside a grid), a by() chrome cell and a KPI card hold none."""
        # Flipped (WP-31 H2x): one action beside each save was wrong
        # because a top-level grid's toolbar now also carries Save
        # dashboard (tag dash_composite_png), three controls (DECISIONS
        # A30); its Save as SVG takes the composite's models, and a by()
        # sub-grid keeps the grid-alone SVG and no composite.
        bad, shown, composites = [], 0, 0
        for case in sorted(_CASES):
            sub = tmp_path / re.sub(r"\W+", "_", case)
            sub.mkdir()
            docs = _MODES[mode](sub, _CASES[case]())
            assert not [m for d in docs for m in d.models
                        if isinstance(m, Div) and _actions(m)], case
            for m in _bars(docs):
                acts, saves = _actions(m), _saves(m)
                visible = (m.toolbar_location is not None
                           and any(s.filename for s in saves))
                if len(acts) != (1 if visible else 0):
                    bad.append((case, type(m).__name__, m.name, len(acts)))
                elif acts:
                    shown += 1
                    tools = m.toolbar.tools
                    pngs = [t for t in tools if isinstance(t, CustomAction)
                            and "dash_composite_png" in (t.tags or ())]
                    whole = "header" in acts[0].callback.args
                    composites += whole
                    if len(pngs) != int(whole) or (
                            acts[0].callback.code != (
                                dr._DASH_COMPOSITE_JS + dr._DASH_SVG_SAVE_JS
                                if whole else dr._DASH_SVG_SAVE_JS)):
                        bad.append((case, "composite", m.name, len(pngs)))
                    if acts[0].callback.args["name"] != saves[0].filename:
                        bad.append((case, "name",
                                    acts[0].callback.args["name"],
                                    saves[0].filename))
        assert shown >= len(_CASES), shown
        assert composites >= len(_CASES), composites
        assert bad == [], bad


class TestNoSvgBackend:

    @pytest.mark.parametrize("mode", sorted(_MODES))
    def test_figures_keep_canvas_or_webgl(self, tmp_path, mode):
        docs = _MODES[mode](tmp_path, _CASES["a by() graph in a tab"]())
        got = {m.output_backend for m in _bars(docs) if isinstance(m, Plot)}
        assert got and got <= {"canvas", "webgl"}, got


class TestTheServedCopy:

    def test_the_app_defines_the_names(self, tmp_path):
        _doc, ns, _src = tt._served(tmp_path, tt._CORPUS["two graphs"]())
        assert ns["_DASH_SVG_SAVE_JS"] == dr._DASH_SVG_SAVE_JS
        assert ns["_DASH_SVG_SAVE_ICON"] == dr._DASH_SVG_SAVE_ICON


class TestTheBundle:
    """Guard: the three BokehJS calls the action makes are in the shipped
    bundle (on the Bokeh internals list, _DASH_BOKEH_INTERNALS)."""

    def test_the_calls_exist_in_the_shipped_bokehjs(self):
        from bokeh.util.paths import bokehjs_path
        path = os.path.join(str(bokehjs_path()), "js", "bokeh.min.js")
        with open(path, encoding="utf-8") as fh:
            js = fh.read()
        for need in ("find_one", "to_blob", "export("):
            assert need in js, need


# ---------------------------------------------------------------------------
# In Chrome
# ---------------------------------------------------------------------------

#: Record each blob the page makes into a URL, and each download's name,
#: without letting the download leave the page; hooked once, emptied on
#: every call.
_CAPTURE_JS = r"""
(() => {
  window.__svg = []; window.__dl = []; window.__alerts = [];
  if (window.__hooked) return 0;
  window.__hooked = true;
  const make = URL.createObjectURL.bind(URL);
  URL.createObjectURL = (b) => {
    const e = {type: b.type, size: b.size, text: null};
    window.__svg.push(e);
    b.text().then(t => { e.text = t; });
    return make(b);
  };
  HTMLAnchorElement.prototype.click = function () {
    window.__dl.push(this.download); };
  window.alert = (m) => { window.__alerts.push(String(m)); };
  return 0;
})()
"""

#: Run the i-th Save as SVG action as its toolbar button does.
_CLICK_JS = ("__dash_models('CustomAction').filter(a => a.tags.includes("
             "'dash_svg_save'))[%d].do.emit(undefined);")

_N_ACTIONS_JS = ("JSON.stringify(__dash_models('CustomAction').filter(a => "
                 "a.tags.includes('dash_svg_save')).length)")

_DONE_JS = ("JSON.stringify(window.__svg.length > 0 && "
            "window.__svg.every(e => e.text !== null))")


def _cb():
    import test_csp_browser
    return test_csp_browser


def _export(p, i=0, timeout=30):
    """Click action *i* and return ``(blob entry, download name)``."""
    p._eval(_CAPTURE_JS)
    p.in_task(_CLICK_JS % i)
    end = time.time() + timeout
    while time.time() < end and not p.read(_DONE_JS):
        time.sleep(0.2)
    svg = p.read("JSON.stringify(window.__svg)")
    dl = p.read("JSON.stringify(window.__dl)")
    assert len(svg) == 1 and len(dl) == 1, (svg and svg[0]["type"], dl,
                                            p.js_errors())
    return svg[0], dl[0]


_MARK = re.compile(r'<path\b[^>]*fill="(?:#123456|rgb\(18, ?52, ?86\))"')


def _marks(entry):
    assert entry["type"] == "image/svg+xml", entry["type"]
    assert "<image" not in entry["text"]
    return len(_MARK.findall(entry["text"]))


def _write(html, name):
    path = os.path.join(tempfile.mkdtemp(prefix="dash_svg_"), name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)
    return path


def _marked_spec(cb, **bo):
    return cb._spec([cb._graph("g1", [cb._scatter(mcolor="#123456")])], **bo)


@pytest.mark.release
@pytest.mark.skipif(not _CHROME, reason="headless Chrome is not installed "
                    "(set DASH_CHROME); a skip is red under DASH_STRICT=1")
class TestInChrome:

    def test_saved_page_before_and_after_a_move(self):
        cb = _cb()
        d, sp, dp = cb._files("svg_move", _marked_spec(cb), cb._frame(20))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            page = _write(dr.DashRenderer(sp, dp).render(), "page.html")
        with cb._CspProbe(cb._url(page)) as p:
            entry, name = _export(p)
            # Flipped (WP-31 H2x): dashboard.svg, the grid alone, was wrong
            # on a top-level grid because Save as SVG now writes the whole
            # dashboard there (A30); its grid is the same vector image.
            assert name == "dashboard-full.svg"
            before = _marks(entry)
            views = p.read(cb._VIEWS_JS)
            p.in_task(cb._MOVE_SELECT_JS)
            shown = p.wait_change(cb._VIEWS_JS, views)
            time.sleep(0.5)
            after = _marks(_export(p)[0])
            assert (before, after) == (20, min(shown)), (before, after, shown)
            assert p.violations() == [] and p.js_errors() == []

    def test_served_doc_before_and_after_a_move(self, tmp_path):
        from bokeh.embed import file_html
        from bokeh.resources import INLINE
        import test_mode_parity as mp
        cb = _cb()
        spec = _marked_spec(cb)
        src = tt._app_source(tmp_path, spec, cb._frame(20))
        doc = tt._session(tt._load_app(src, "svg_served"))
        got = []
        for step in ("before", "after"):
            if step == "after":
                (w,) = [x for x in mp._widgets_of(doc)
                        if isinstance(x, Select)]
                mp._fire(w, [v for v, _l in w.options if v != w.value][0])
            page = _write(file_html(list(doc.roots), INLINE, "served"),
                          step + ".html")
            with cb._CspProbe(cb._url(page)) as p:
                entry, name = _export(p)
                # Flipped (WP-31 H2x): the whole dashboard on a top-level
                # grid (A30), as on the saved page.
                assert name == "dashboard-full.svg"
                got.append(_marks(entry))
                assert p.js_errors() == [], p.js_errors()
        assert got == [20, 10], got

    def test_a_webgl_figure_exports_as_vector(self):
        cb = _cb()
        with cb._CspProbe(cb._url(cb._saved_page("big"))) as p:
            assert p.read("JSON.stringify(__dash_models('Figure')"
                          ".map(f => f.output_backend))") == ["webgl"]
            entry, _name = _export(p, timeout=120)
            assert entry["type"] == "image/svg+xml"
            assert "<image" not in entry["text"]
            n = entry["text"].count("<path")
            assert n >= dr._WEBGL_THRESHOLD + 2000, n

    def test_layout_bs_items_and_labels(self):
        cb = _cb()
        spec = cb._spec([cb._graph("g1", [cb._scatter()],
                                   subtitle="SUBTX", note="NOTEX"),
                         cb._graph("g2", [cb._scatter()], by="foreign")],
                        layout="bs")
        d, sp, dp = cb._files("svg_bs", spec, cb._frame(20))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            page = _write(dr.DashRenderer(sp, dp).render(), "bs.html")
        with cb._CspProbe(cb._url(page)) as p:
            assert p.read(_N_ACTIONS_JS) == 2
            names, texts = [], []
            for i in range(2):
                entry, name = _export(p, i)
                names.append(name)
                texts.append(entry["text"])
            # Flipped (WP-31 H2x): g1.svg was wrong because a layout(bs)
            # item's Save as SVG now writes the dashboard's header and
            # filters above the item (D-53f).
            assert sorted(names) == ["g1-full.svg", "g2-full.svg"], names
            g1 = texts[names.index("g1-full.svg")]
            for label in ("SUBTX", "NOTEX"):
                assert re.search(r"<text\b[^>]*>%s</text>" % label, g1), label
            assert p.violations() == [] and p.js_errors() == []

    def test_a_by_sub_grid_keeps_the_grid_alone(self):
        """WP-31 H2x: a by() sub-grid's Save as SVG has no composite
        models and still writes the sub-grid alone."""
        cb = _cb()
        spec = cb._spec([cb._graph("g1", [cb._scatter()], by="foreign"),
                         cb._graph("g2", [cb._scatter()])])
        d, sp, dp = cb._files("svg_by_alone", spec, cb._frame(20))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            page = _write(dr.DashRenderer(sp, dp).render(), "by.html")
        with cb._CspProbe(cb._url(page)) as p:
            acts = p.read("JSON.stringify(__dash_models('CustomAction')"
                          ".filter(a => a.tags.includes('dash_svg_save'))"
                          ".map(a => a.callback.code.startsWith("
                          "'function dash_html_escape')))")
            assert True in acts and False in acts, acts
            entry, name = _export(p, acts.index(False))
            assert not name.endswith("-full.svg"), name
            assert entry["type"] == "image/svg+xml"
            assert not entry["text"].startswith(
                '<svg xmlns="http://www.w3.org/2000/svg" width="'), (
                entry["text"][:120])
            assert p.violations() == [] and p.js_errors() == []

    def test_a_failure_is_said_once(self):
        cb = _cb()
        with cb._CspProbe(cb._url(cb._saved_page("auto"))) as p:
            p._eval(_CAPTURE_JS)
            p._eval("Bokeh.index.find_one = () => null; 0")
            p.in_task(_CLICK_JS % 0)
            alerts = p.wait_change("JSON.stringify(window.__alerts)", [])
            time.sleep(0.5)
            alerts = p.read("JSON.stringify(window.__alerts)")
            assert len(alerts) == 1 and "save button" in alerts[0], alerts
            assert p.read("JSON.stringify(window.__dl)") == []
            assert p.js_errors() == [], p.js_errors()
