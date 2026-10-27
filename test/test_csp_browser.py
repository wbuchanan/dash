"""test_csp_browser.py -- what a browser runs on a dashboard page under its
Content-Security-Policy (WP-30 P1.29, GAPS2-I12-c).

test_csp.py pins the policy text.  Whether the policy blocks what it
should, and lets the page do everything it did, only a browser can say, so
each page here is loaded into headless Chrome and driven over the DevTools
protocol (``range_probe.RangeProbe``'s connection, extended below):

* a ``securitypolicyviolation`` listener is registered with
  ``Page.addScriptToEvaluateOnNewDocument`` before the page loads, so it
  sees every violation the page itself causes (the policy does not govern
  a script DevTools adds);
* an ``<img src="data:," onerror=...>`` and a created inline ``<script>``
  are injected with ``Runtime.evaluate`` -- what an escaping fault would
  let into a page -- and the test reads whether either ran;
* filters, hover, the brush and the exports are driven as a user drives
  them: a widget's value set from a page task (``setTimeout``), a mouse
  move with ``Input.dispatchMouseEvent``, a button's own click.

Saved pages are written by ``DashRenderer``; served pages come from a
generated app under ``python app.py`` and under ``bokeh serve``
(``test_server_serves``' launchers).  The controls in
``TestTheMethodSeesWhatItClaims`` show the method sees an injection that
runs and an eval the policy blocks.

Chrome is ``responsive_probe.find_chrome()``'s (``DASH_CHROME`` first).
Without it the module skips, and a skip is red under ``DASH_STRICT=1``.
"""
import atexit
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import responsive_probe  # noqa: E402

if responsive_probe.find_chrome() is None:
    pytest.skip("headless Chrome is not installed (set DASH_CHROME); "
                "a skip is red under DASH_STRICT=1", allow_module_level=True)

#: Headless Chrome: the release tier, not the default run (WP-30 D).
pytestmark = pytest.mark.release

import asyncio  # noqa: E402

from bokeh.io import curdoc  # noqa: E402

import dash_render as dr  # noqa: E402
import range_probe  # noqa: E402
from conftest import make_data_json  # noqa: E402
from test_csp import _standalone_page, _directives, _the_meta_policy  # noqa: E402,E501
from test_server_serves import _Launched, _Served  # noqa: E402

#: Every violation the page causes, as "<directive> <blocked URI>", in
#: window.__v and on the console (where it outlives a navigation).
_LISTEN_JS = r"""
document.addEventListener('securitypolicyviolation', (e) => {
  const v = e.violatedDirective + ' ' + e.blockedURI;
  (window.__v = window.__v || []).push(v);
  console.debug('DASHCSPV ' + v + ' ' + (e.sample || ''));
});
"""

#: What an escaping fault would let into a page: an inline handler and an
#: inline script.
_INJECT_JS = r"""
(() => {
  const img = document.createElement('div');
  img.innerHTML = '<img src="data:," onerror="window.__inj_img=1">';
  document.body.appendChild(img);
  const s = document.createElement('script');
  s.text = 'window.__inj_script=1;';
  document.body.appendChild(s);
  return 0;
})()
"""

#: The view of a model, found by walking every root view's children.
_HELPERS_JS = r"""
window.__dash_view = (model) => {
  const seen = new Set();
  const walk = (v) => {
    if (!v || seen.has(v)) return null;
    seen.add(v);
    if (v.model === model) return v;
    for (const k of ['child_views', 'children_views', 'renderer_views']) {
      let c = null;
      try { c = v[k]; } catch (e) { c = null; }
      if (!c) continue;
      const arr = (c instanceof Map) ? [...c.values()]
        : (typeof c[Symbol.iterator] === 'function' ? [...c] : []);
      for (const x of arr) { const r = walk(x); if (r) return r; }
    }
    return null;
  };
  for (const v of Object.values(Bokeh.index)) {
    const r = walk(v);
    if (r) return r;
  }
  return null;
};
window.__dash_models = (type) => {
  const out = [];
  for (const d of Bokeh.documents)
    for (const m of d.all_models) if (m.type === type) out.push(m);
  return out;
};
0
"""

_READY_JS = ("document.readyState === 'complete' && !!window.Bokeh && "
             "Bokeh.documents.length > 0 && "
             "Object.keys(Bokeh.index).length > 0 && "
             "Object.values(Bokeh.index).every(v => v.has_finished())")

#: Each CDSView's index count: what a filter move changes on a saved page.
_VIEWS_JS = ("JSON.stringify(__dash_models('CDSView').map(m => m.indices"
             ".count))")

#: Each ColumnDataSource's length: what a served move changes.
_LENGTHS_JS = ("JSON.stringify(__dash_models('ColumnDataSource').map(m => "
               "m.get_length()))")

#: Set the first Select to its next option, in a page task.
_MOVE_SELECT_JS = (
    "const s = __dash_models('Select')[0]; const i = s.options.findIndex("
    "o => (Array.isArray(o) ? o[0] : o) === s.value); const o = "
    "s.options[(i + 1) % s.options.length]; s.value = Array.isArray(o) ? "
    "o[0] : o;")

#: Where the first scatter's fourth point is drawn, in page pixels.
_POINT_JS = r"""
(() => {
  let fig = null, gr = null;
  for (const m of __dash_models('Figure')) { if (!fig) fig = m; }
  for (const r of fig.renderers)
    if (r.type === 'GlyphRenderer' && r.data_source.get_length() > 3) {
      gr = r; break; }
  const fv = __dash_view(fig);
  const d = gr.data_source.data;
  const sx = fv.frame.x_scale.compute(d[gr.glyph.x.field][3]);
  const sy = fv.frame.y_scale.compute(d[gr.glyph.y.field][3]);
  const r = fv.canvas_view.el.getBoundingClientRect();
  return JSON.stringify([r.left + sx, r.top + sy]);
})()
"""

#: The text of every visible tooltip, shadow roots included.
_TOOLTIP_JS = r"""
(() => {
  const out = [];
  const walk = (root) => { for (const el of root.querySelectorAll('*')) {
    if (el.shadowRoot) walk(el.shadowRoot);
    if (String(el.className || '').includes('bk-tooltip-content')) {
      const r = el.getBoundingClientRect();
      if (r.width > 0 && r.height > 0) out.push(el.textContent);
    } } };
  walk(document);
  return JSON.stringify(out);
})()
"""

#: The text of every Div: the KPI cards'.
_DIVS_JS = "JSON.stringify(__dash_models('Div').map(m => m.text))"

#: The injected kind of each violation the page saw.
_INJECTED = {"script-src-attr inline", "script-src-elem inline"}


class _CspProbe(range_probe.RangeProbe):
    """One page, file or http, held open in headless Chrome with the
    violation listener registered before it loads."""

    def __init__(self, url, downloads=None, ready=_READY_JS, timeout=60):
        super().__init__(os.devnull, timeout=timeout)
        self.url = url
        self.downloads = downloads
        self.ready = ready
        self.console = []

    def __enter__(self):
        if not self.chrome:
            raise RuntimeError("no Chrome binary (set DASH_CHROME)")
        port = range_probe._free_port()
        self._profile = tempfile.mkdtemp(prefix="dash_csp_probe_")
        self._proc = subprocess.Popen(
            responsive_probe.chrome_argv(self.chrome) + [
             "--headless=new", "--no-first-run",
             "--no-default-browser-check", *self.CHROME_GPU_FLAGS,
             "--user-data-dir=" + self._profile,
             "--remote-debugging-port=%d" % port,
             "--window-size=1400,1000", "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            ws = self._page_ws(port)
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._ws = self._run(self._connect(ws))
            self._send("Runtime.enable")
            self._send("Page.enable")
            self._send("Page.addScriptToEvaluateOnNewDocument",
                       {"source": _LISTEN_JS})
            if self.downloads:
                self._send("Browser.setDownloadBehavior",
                           {"behavior": "allow",
                            "downloadPath": self.downloads})
            self._send("Page.navigate", {"url": self.url})
            self._wait_for(self.ready)
            self._eval(_HELPERS_JS)
            time.sleep(0.3)
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return self

    async def _call(self, method, params):
        self._seq += 1
        mid = self._seq
        await self._ws.write_message(json.dumps(
            {"id": mid, "method": method, "params": params or {}}))
        while True:
            raw = await self._ws.read_message()
            if raw is None:
                raise RuntimeError("Chrome closed the DevTools connection")
            msg = json.loads(raw)
            ev = msg.get("method")
            if ev == "Runtime.exceptionThrown":
                d = msg.get("params", {}).get("exceptionDetails", {})
                self._errors.append(
                    (d.get("exception") or {}).get("description")
                    or d.get("text") or "exception")
            elif ev == "Runtime.consoleAPICalled":
                args = msg.get("params", {}).get("args", [])
                if args and str(args[0].get("value", "")).startswith(
                        "DASHCSPV "):
                    self.console.append(args[0]["value"][len("DASHCSPV "):])
            if msg.get("id") == mid:
                return msg

    # ---- what a test reads and does ---------------------------------------
    def violations(self):
        return json.loads(self._eval("JSON.stringify(window.__v || [])"))

    def inject(self):
        self._eval(_INJECT_JS)
        time.sleep(0.5)

    def ran(self):
        return self._eval("[!!window.__inj_img, !!window.__inj_script]")

    def in_task(self, js):
        """Run *js* as a page task, as a user's action runs."""
        self._eval("setTimeout(() => { %s }, 0); 0" % js)

    def read(self, js):
        return json.loads(self._eval(js))

    def wait_change(self, js, before, timeout=10.0):
        """*js*'s value once it differs from *before*, or the last one."""
        end = time.time() + timeout
        cur = self.read(js)
        while cur == before and time.time() < end:
            time.sleep(0.1)
            cur = self.read(js)
        return cur


def _own(violations):
    """The violations the page caused itself, the injected ones aside."""
    return [v for v in violations if v not in _INJECTED]


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

_WORK = tempfile.mkdtemp(prefix="dash_csp_browser_")
atexit.register(shutil.rmtree, _WORK, True)


def _frame(n=20):
    i = np.arange(n, dtype=float)
    return pd.DataFrame({
        "mpg": 12.0 + 29.0 * ((i * 7) % n) / max(n - 1, 1),
        "weight": np.linspace(1760.0, 4840.0, n),
        "foreign": (i % 2),
    })


def _graph(name, plots, **go):
    go["name"] = name
    return {"name": name, "plots": plots, "graph_options": go,
            "if_expr": "", "in_expr": ""}


def _scatter(**opts):
    return {"type": "scatter", "yvar": "mpg", "xvar": "weight",
            "options": opts}


_DROPDOWN = {"varname": "foreign", "type": "dropdown", "exclude": [],
             "label": ""}
_RANGE = {"varname": "weight", "type": "range", "exclude": [], "label": ""}


def _spec(graphs, *, kpis=(), filters=(_DROPDOWN,), **bo):
    build = {"layout": "auto", "link": "", "theme": "default", "title": "",
             "subtitle": "", "filters": list(filters),
             "registry": " ".join([k["name"] for k in kpis]
                                  + [g["name"] for g in graphs])}
    build.update(bo)
    return {"graphs": list(graphs), "kpis": list(kpis),
            "build_options": build}


_KPI = {"name": "k1", "stat": "mean", "var": "mpg", "title": "Avg MPG",
        "fmt": "%9.2f"}


def _specs():
    """Each page family's ``(spec, data)``."""
    return {
        # tabs, csv, a dropdown and a range filter, the filter sidebar,
        # by(), colorvar(), a KPI, hover and a TeX axis title (MathJax).
        "rich": (_spec([_graph("g1", [_scatter(colorvar="mpg")],
                               hover="mpg weight", xtitle="$$\\beta$$"),
                        _graph("g2", [_scatter()], by="foreign")],
                       kpis=[_KPI], filters=[_DROPDOWN, _RANGE],
                       tabs="One: g1 / Two: g2", csv="1",
                       filter_position="left", title="Rich"), _frame()),
        # a formatted axis and a formatted tooltip: CustomJS formatters.
        "formats": (_spec([_graph("g1", [_scatter()], hover="mpg weight",
                                  ylabel=", format(%9.2fc)")],
                          formats={"mpg": "%9.2fc"}), _frame()),
        # above _WEBGL_THRESHOLD rows: the WebGL backend.
        "big": (_spec([_graph("g1", [_scatter()])]),
                _frame(dr._WEBGL_THRESHOLD + 2000)),
        # a KPI that follows a brushed selection.
        "brush": (_spec([_graph("g1", [_scatter()])],
                        kpis=[dict(_KPI, update="brush")]), _frame()),
    }


def _files(name, spec, df):
    d = tempfile.mkdtemp(prefix=name + "_", dir=_WORK)
    sp, dp = os.path.join(d, "spec.json"), os.path.join(d, "data.json")
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(make_data_json(df), fh)
    return d, sp, dp


_SAVED_CACHE = {}


def _saved_page(name):
    """The path of saved page family *name*, written once."""
    if name not in _SAVED_CACHE:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                if name in ("auto", "bs"):
                    page = _standalone_page(name)
                    d = tempfile.mkdtemp(prefix=name + "_", dir=_WORK)
                else:
                    d, sp, dp = _files(name, *_specs()[name])
                    page = dr.DashRenderer(sp, dp).render()
            finally:
                curdoc().clear()
        path = os.path.join(d, "page.html")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(page)
        _SAVED_CACHE[name] = path
    return _SAVED_CACHE[name]


def _copy_with_policy(name, edit):
    """A test copy of saved page *name* whose policy is ``edit(policy)``;
    production text is never touched."""
    with open(_saved_page(name), encoding="utf-8") as fh:
        page = fh.read()
    old = _the_meta_policy(page)
    page = page.replace('content="%s"' % old, 'content="%s"' % edit(old), 1)
    path = os.path.join(tempfile.mkdtemp(dir=_WORK), "copy.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(page)
    return path


def _url(path):
    return "file://" + path


def _app(name):
    d, sp, dp = _files("app_" + name, *_specs()[name])
    op = os.path.join(d, "app.py")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(op)
    return op


@pytest.fixture(scope="module")
def servers():
    """Each served app family under each server, started when first asked
    for and stopped with the module."""
    running, stack = {}, []

    def get(kind, name):
        key = (kind, name)
        if key not in running:
            srv = (_Launched if kind == "launcher" else _Served)(_app(name))
            srv.__enter__()
            stack.append(srv)
            running[key] = srv
        return running[key]
    yield get
    for srv in reversed(stack):
        srv.__exit__(None, None, None)
    shutil.rmtree(_WORK, ignore_errors=True)


def _served_url(srv):
    return srv.url("/" if isinstance(srv, _Launched) else "/app")


# ---------------------------------------------------------------------------
# Saved pages
# ---------------------------------------------------------------------------

class TestSavedPageInChrome:

    @pytest.mark.parametrize("name", ["auto", "bs", "rich"])
    def test_an_injected_script_and_handler_do_not_run(self, name):
        with _CspProbe(_url(_saved_page(name))) as p:
            p.inject()
            assert p.ran() == [False, False], (
                f"{name}: an injected handler or script ran: {p.ran()}")
            assert set(p.violations()) == _INJECTED, p.violations()

    @pytest.mark.parametrize("name", ["auto", "bs", "rich", "formats",
                                      "big", "brush"])
    def test_it_renders_with_no_violation_of_its_own(self, name):
        with _CspProbe(_url(_saved_page(name))) as p:
            assert p.violations() == [], p.violations()
            assert p.js_errors() == [], p.js_errors()
            assert p.read("JSON.stringify(__dash_models('Figure').length)")
            if name == "big":
                assert p.read("JSON.stringify(__dash_models('Figure')"
                              ".map(f => f.output_backend))")[0] == "webgl"

    @pytest.mark.parametrize("name", ["auto", "rich"])
    def test_a_filter_move_still_works_and_a_later_injection_is_blocked(
            self, name):
        with _CspProbe(_url(_saved_page(name))) as p:
            before = p.read(_VIEWS_JS)
            p.in_task(_MOVE_SELECT_JS)
            after = p.wait_change(_VIEWS_JS, before)
            assert after != before, "the dropdown's CustomJS changed nothing"
            assert p.violations() == [], p.violations()
            assert p.js_errors() == [], p.js_errors()
            p.inject()
            assert p.ran() == [False, False], p.ran()
            assert set(p.violations()) == _INJECTED, p.violations()

    def test_exports_still_work(self):
        """The CSV button and the toolbar's save, each through its own
        view, deliver a file."""
        dl = tempfile.mkdtemp(dir=_WORK)
        with _CspProbe(_url(_saved_page("rich")), downloads=dl) as p:
            p.in_task("__dash_view(__dash_models('Button')[0])"
                      ".button_el.click();")
            # Flipped (WP-31 H2x): the save button a reader can click, the
            # grid's merged one (named "dashboard").  SaveTool [0] in
            # document order is a hidden figure's own inside the grid, with
            # no file name: BokehJS stops at window.prompt() for one, so
            # the PNG never came (measured in Chrome, headless or not).
            p.in_task("__dash_models('SaveTool').filter(t => t.filename)[0]"
                      ".do.emit(undefined);")
            end = time.time() + 10
            while time.time() < end and not (
                    {"dashboard.csv", "dashboard.png"} <= set(os.listdir(dl))):
                time.sleep(0.2)
            assert {"dashboard.csv", "dashboard.png"} <= set(os.listdir(dl)), (
                os.listdir(dl))
            with open(os.path.join(dl, "dashboard.csv"),
                      encoding="utf-8") as fh:
                assert "mpg" in fh.readline()
            assert p.violations() == [], p.violations()
            assert p.js_errors() == [], p.js_errors()

    def test_hover_and_brush_run(self):
        with _CspProbe(_url(_saved_page("brush"))) as p:
            assert p.read(_TOOLTIP_JS) == []
            x, y = p.read(_POINT_JS)
            p._send("Input.dispatchMouseEvent",
                    {"type": "mouseMoved", "x": x, "y": y})
            tips = p.wait_change(_TOOLTIP_JS, [], timeout=5)
            assert tips and "mpg" in tips[0], tips
            before = p.read(_DIVS_JS)
            p.in_task("for (const s of __dash_models('ColumnDataSource')) "
                      "if (s.get_length() > 3) s.selected.indices = [0, 1, 2];")
            after = p.wait_change(_DIVS_JS, before)
            assert after != before, "the brushed KPI did not change"
            assert p.violations() == [], p.violations()
            assert p.js_errors() == [], p.js_errors()


# ---------------------------------------------------------------------------
# Served pages
# ---------------------------------------------------------------------------

@pytest.mark.serve
@pytest.mark.parametrize("kind", ["launcher", "bokeh_serve"])
class TestServedPageInChrome:

    def test_an_injected_script_and_handler_do_not_run(self, servers, kind):
        with _CspProbe(_served_url(servers(kind, "rich"))) as p:
            p.inject()
            assert p.ran() == [False, False], (
                f"{kind}: an injected handler or script ran: {p.ran()}")
            assert set(p.violations()) == _INJECTED, p.violations()

    def test_a_same_origin_script_without_the_nonce_is_refused(
            self, servers, kind):
        """Nonce-only (A102): a script from the server itself runs only
        with the page's nonce."""
        with _CspProbe(_served_url(servers(kind, "rich"))) as p:
            src = p._eval("document.querySelector("
                          "'script[src*=\"bokeh.min.js\"]').src")
            assert src.startswith("http://"), src
            p._eval("(() => { const s = document.createElement('script'); "
                    "s.onload = () => { window.__inj_src = 1; }; s.src = %s; "
                    "document.body.appendChild(s); return 0; })()"
                    % json.dumps(src))
            time.sleep(1.0)
            assert not p._eval("!!window.__inj_src"), (
                "a same-origin script without the nonce loaded")
            assert "script-src-elem " + src in p.violations(), p.violations()

    @pytest.mark.parametrize("name", ["rich", "big"])
    def test_it_renders_filters_and_round_trips(self, servers, kind, name):
        with _CspProbe(_served_url(servers(kind, name))) as p:
            assert p.violations() == [], p.violations()
            before = p.read(_LENGTHS_JS)
            p.in_task(_MOVE_SELECT_JS)
            after = p.wait_change(_LENGTHS_JS, before, timeout=20)
            assert after != before, "the server's update changed no source"
            assert p.violations() == [], p.violations()
            assert p.js_errors() == [], p.js_errors()
            p.inject()
            assert p.ran() == [False, False], p.ran()
            assert set(p.violations()) == _INJECTED, p.violations()


# ---------------------------------------------------------------------------
# The method sees what it claims
# ---------------------------------------------------------------------------

#: The saved page's policy at c96facd, before WP-30 P1.29.
_OLD_STANDALONE = (
    "default-src 'none'; script-src 'unsafe-inline' 'unsafe-eval'; "
    "style-src 'unsafe-inline'; img-src data: blob:; font-src data:; "
    "connect-src 'none'; object-src 'none'; base-uri 'none'; "
    "form-action 'none'")


class TestTheMethodSeesWhatItClaims:

    def test_under_the_old_policy_the_injection_runs(self):
        with _CspProbe(_url(_copy_with_policy(
                "auto", lambda old: _OLD_STANDALONE))) as p:
            p.inject()
            assert p.ran() == [True, True], p.ran()
            assert p.violations() == [], p.violations()

    def test_without_unsafe_eval_a_move_is_blocked_and_seen(self):
        """Flipped (WP-30 P1.5): "the page paints, then a move is blocked"
        was wrong once every numeric axis carries Stata's writer, because
        that writer is a CustomJSTickFormatter compiled at first paint:
        without 'unsafe-eval' the paint itself is blocked, and the eval
        violation is seen."""
        def no_eval(old):
            return re.sub(r" 'unsafe-eval'", "", old, count=1)
        path = _copy_with_policy("auto", no_eval)
        with _CspProbe(_url(path),
                       ready="document.readyState === 'complete'") as p:
            assert "'unsafe-eval'" not in _directives(
                p._eval("document.querySelector('meta[http-equiv]')"
                        ".content"))["script-src"]
            time.sleep(1.0)
            assert any(v.startswith("script-src") and v.endswith(" eval")
                       for v in p.violations()), p.violations()


@pytest.mark.serve
class TestTheRedirectPageInChrome:

    def test_it_still_forwards(self, servers):
        srv = servers("launcher", "rich")
        target = srv.url("/")
        path = os.path.join(tempfile.mkdtemp(dir=_WORK), "open.html")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(dr._dash_redirect_page(target))
        with _CspProbe(_url(path), ready=(
                "location.href.startsWith('http://') && " + _READY_JS)) as p:
            assert p._eval("location.href") == target
            assert p.console == [], p.console
            assert p.violations() == [], p.violations()


# ---------------------------------------------------------------------------
# WP-30 P1.23a (section 35): the date transform and the off-date axes
# ---------------------------------------------------------------------------

def _date_frame(n=12):
    i = np.arange(n, dtype=float)
    return pd.DataFrame({"date": 14977.0 + 30.0 * (i % 12),
                         "yr": 1990.0 + (i % 12),
                         "close": 1200.0 + 10.0 * (i % 12),
                         "obs": 1.0 + (i % 12)})


_CLOSE = {"varname": "close", "type": "range", "exclude": [], "label": ""}
_DATE_FORMATS = {"date": "%td", "yr": "%ty"}


def _date_specs():
    """The mixed axis (12 rows, and 12,000 for WebGL) and the two axes
    that reach past Stata's dates."""
    mixed = [{"type": "scatter", "yvar": "close", "xvar": "date",
              "options": {}},
             {"type": "scatter", "yvar": "close", "xvar": "obs",
              "options": {}}]

    def lit(x):
        return {"type": "scatteri", "values": [[1300.0, float(x)]],
                "options": {}}
    sp = (lambda plots: _spec([_graph("g1", plots)], filters=[_CLOSE],
                              formats=_DATE_FORMATS))
    return {
        "mixed": (sp(mixed), _date_frame()),
        "mixed_big": (sp(mixed), _date_frame(dr._WEBGL_THRESHOLD + 2000)),
        "scatteri_offrange": (sp([{"type": "line", "yvar": "close",
                                   "xvar": "date", "options": {}},
                                  lit(99999999)]), _date_frame()),
        "ty_negative": (sp([{"type": "line", "yvar": "close", "xvar": "yr",
                             "options": {}}, lit(-500)]), _date_frame()),
    }


_DATE_SAVED = {}


def _date_page(name):
    if name not in _DATE_SAVED:
        d, sp, dp = _files(name, *_date_specs()[name])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                page = dr.DashRenderer(sp, dp).render()
            finally:
                curdoc().clear()
        path = os.path.join(d, "page.html")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(page)
        _DATE_SAVED[name] = path
    return _DATE_SAVED[name]


def _date_app(name):
    d, sp, dp = _files("app_" + name, *_date_specs()[name])
    op = os.path.join(d, "app.py")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(op)
    return op


#: The first figure's x range and what its date transform makes of two
#: dates (02jan2001 and 02nov2001 in epoch ms).
_X_RANGE_JS = ("JSON.stringify((() => { const f = __dash_models('Figure')[0];"
               " const t = __dash_models('CustomJSTransform');"
               " return [f.x_range.start, f.x_range.end, t.length ? "
               "Array.from(t[0].v_compute([978393600000, 1004659200000])) "
               ": null]; })())")
#: Set the close slider to its lower 60%, in a page task.
_MOVE_CLOSE_JS = ("const s = __dash_models('RangeSlider')[0]; "
                  "s.value = [s.start, s.start + 0.6 * (s.end - s.start)];")
#: The first figure's bottom axis: its ticks and the text it writes there.
_TICKS_JS = ("JSON.stringify((() => { const a = __dash_models('Figure')[0]"
             ".below.filter(x => x.ticker)[0]; const t = a.ticker.ticks "
             "|| null; return [a.ticker.type, t, t ? a.formatter.doFormat("
             "t, {loc: 0}) : null, __dash_models('Figure')[0].x_range.start,"
             " __dash_models('Figure')[0].x_range.end]; })())")


def _check_mixed(p):
    lo, hi, units = p.read(_X_RANGE_JS)
    assert lo < 14977 < 15307 < hi < 1e6, (lo, hi)
    assert units == [14977, 15281], units


def _check_off_date(p, name):
    kind, fmt, lit = (("td", "%td", 8639684294400000.0)
                      if name == "scatteri_offrange"
                      else ("ty", "%ty", -77945673600000.0))
    typ, ticks, texts, lo, hi = p.read(_TICKS_JS)
    assert typ == "FixedTicker" and ticks, (typ, ticks)
    assert lo <= lit <= hi or hi <= lit <= lo, (lo, hi)
    if name == "ty_negative":
        assert -62167219200000.0 in ticks and -2208988800000.0 not in ticks
    want = [dr._dash_fmt_text(dr._dash_stata_number_of(t, kind), fmt)
            for t in ticks]
    assert texts == want, (texts, want)
    assert not any(t == "." or re.match(r"^[+-]\d{6}", t) for t in texts)


class TestTheDateTransformUnderTheCsp:

    @pytest.mark.parametrize("name", ["mixed", "mixed_big"])
    def test_saved_page(self, name):
        with _CspProbe(_url(_date_page(name))) as p:
            assert p.violations() == [], p.violations()
            if name == "mixed_big":
                assert p.read("JSON.stringify(__dash_models('Figure')"
                              ".map(f => f.output_backend))")[0] == "webgl"
            _check_mixed(p)
            before = p.read(_X_RANGE_JS)
            p.in_task(_MOVE_CLOSE_JS)
            p.wait_change(_X_RANGE_JS, before, timeout=10)
            _check_mixed(p)
            assert p.violations() == [], p.violations()
            assert p.js_errors() == [], p.js_errors()

    @pytest.mark.serve
    def test_served_page(self):
        with _Launched(_date_app("mixed")) as srv:
            with _CspProbe(srv.url("/")) as p:
                assert p.violations() == [], p.violations()
                _check_mixed(p)
                before = p.read(_X_RANGE_JS)
                p.in_task(_MOVE_CLOSE_JS)
                p.wait_change(_X_RANGE_JS, before, timeout=20)
                _check_mixed(p)
                assert p.violations() == [], p.violations()
                assert p.js_errors() == [], p.js_errors()


@pytest.mark.parametrize("name", ["scatteri_offrange", "ty_negative"])
class TestOffDateAxesInTheBrowser:

    def test_saved_page(self, name):
        with _CspProbe(_url(_date_page(name))) as p:
            assert p.violations() == [] and p.js_errors() == []
            _check_off_date(p, name)
            before = p.read(_TICKS_JS)
            p.in_task(_MOVE_CLOSE_JS)
            p.wait_change(_TICKS_JS, before, timeout=10)
            _check_off_date(p, name)
            assert p.violations() == [] and p.js_errors() == [], (
                p.violations(), p.js_errors())

    @pytest.mark.serve
    def test_served_page(self, name):
        with _Launched(_date_app(name)) as srv:
            with _CspProbe(srv.url("/")) as p:
                assert p.violations() == [] and p.js_errors() == []
                _check_off_date(p, name)
                before = p.read(_TICKS_JS)
                p.in_task(_MOVE_CLOSE_JS)
                p.wait_change(_TICKS_JS, before, timeout=20)
                _check_off_date(p, name)
                assert p.violations() == [] and p.js_errors() == []


# ---------------------------------------------------------------------------
# WP-30 P1.28b (section 54): the Save as SVG action under each policy
# ---------------------------------------------------------------------------

class TestSaveAsSvgUnderThePolicy:
    """Each Save as SVG action runs under the saved page's hashed policy
    and the served page's nonced one with no violation, and the policy
    still blocks an injection afterwards: the action is a CustomJS, never
    an inline script, so it needs no hash, no nonce and no new source."""

    @pytest.mark.parametrize("name", [
        "auto", "bs", "rich",
        pytest.param("served", marks=pytest.mark.serve)])
    def test_the_action_runs_with_no_violation(self, servers, name):
        from test_export_svg import (_CAPTURE_JS, _CLICK_JS, _DONE_JS,
                                     _N_ACTIONS_JS)
        url = (_served_url(servers("launcher", "rich")) if name == "served"
               else _url(_saved_page(name)))
        with _CspProbe(url) as p:
            assert p.violations() == [], p.violations()
            n = p.read(_N_ACTIONS_JS)
            assert n >= 1, f"{name}: no Save as SVG action on the page"
            for i in range(n):
                p._eval(_CAPTURE_JS)
                p.in_task(_CLICK_JS % i)
                end = time.time() + 30
                while time.time() < end and not p.read(_DONE_JS):
                    time.sleep(0.2)
                types = p.read("JSON.stringify(window.__svg.map(e => "
                               "e.type))")
                assert types == ["image/svg+xml"], (name, i, types,
                                                    p.js_errors())
            assert p.violations() == [], p.violations()
            assert p.js_errors() == [], p.js_errors()
            p.inject()
            assert p.ran() == [False, False], p.ran()
            assert set(p.violations()) == _INJECTED, p.violations()
