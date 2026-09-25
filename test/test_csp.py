"""test_csp.py -- every dashboard page carries its Content-Security-Policy.

ROADMAP.md WP-20: TR-20.1 (emit the CSP in server mode), TR-20.2 (strengthen
the policy itself) and AC-20.1 ("A served document carries the CSP").

Before this, the only policy was ``script-src 'unsafe-inline'
'unsafe-eval'`` in a <meta>, written into the two standalone pages alone.
With no ``default-src``, everything it did not name -- styles, images,
fonts, connections, plugins, <base>, form targets -- was unrestricted, and
on the layout(bs) page the <meta> sat after the inlined BokehJS, which a
<meta> policy does not govern.  A served dashboard carried no policy and no
security header at all.

The policies are now module constants in dash_render.py:

* ``_DASH_CSP_STANDALONE`` -- the saved page: everything is inline and
  nothing may load from anywhere;
* ``_DASH_CSP_SERVED`` -- the served page, which also loads BokehJS from its
  own server's /static and opens a websocket back to it (``'self'``);
* ``_DASH_SECURITY_HEADERS`` -- what the ``python app.py`` launcher adds to
  every response: the served policy plus ``frame-ancestors 'none'`` (which
  the CSP specification ignores in a <meta>), nosniff, DENY and no-referrer.

The served <meta> is written by a Bokeh document template that extends
Bokeh's own page (``bokeh.core.templates.FILE``), so it holds under both
``python app.py`` and ``bokeh serve app.py``.  Only the launcher can add
headers: ``bokeh serve`` gives an app script no hook into its responses.

Whether a browser runs a dashboard under these policies is not something a
unit test can see; that was checked in Chromium when they were chosen.
These tests pin the policy text, where it sits in each page, that the
served app carries the same constants, and that each real server sends
what it should.  The live-server classes start subprocesses and are marked
``serve`` (deselect with ``-m 'not serve'``); no browser is ever opened.
"""
import ast
import asyncio
import html
import inspect
import json
import mimetypes
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import threading
import types
import urllib.error
import urllib.request

import numpy as np
import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.io import curdoc
from bokeh.io.doc import patch_curdoc

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import make_data_json, make_spec  # noqa: E402
from test_server_serves import (  # noqa: E402
    _Launched, _Served, _build_app, _free_port)


# ---------------------------------------------------------------------------
# What each page must carry -- exactly these directives, exactly these sources
# ---------------------------------------------------------------------------

STANDALONE_TEXT = (
    "default-src 'none'; script-src 'unsafe-inline' 'unsafe-eval'; "
    "style-src 'unsafe-inline'; img-src data: blob:; font-src data:; "
    "connect-src 'none'; object-src 'none'; base-uri 'none'; "
    "form-action 'none'")

SERVED_TEXT = (
    "default-src 'none'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
    "style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; "
    "font-src 'self' data:; connect-src 'self'; object-src 'none'; "
    "base-uri 'none'; form-action 'none'")

STANDALONE = {
    "default-src": {"'none'"},
    "script-src": {"'unsafe-inline'", "'unsafe-eval'"},
    "style-src": {"'unsafe-inline'"},
    "img-src": {"data:", "blob:"},
    "font-src": {"data:"},
    "connect-src": {"'none'"},
    "object-src": {"'none'"},
    "base-uri": {"'none'"},
    "form-action": {"'none'"},
}

SERVED = {
    "default-src": {"'none'"},
    "script-src": {"'self'", "'unsafe-inline'", "'unsafe-eval'"},
    "style-src": {"'self'", "'unsafe-inline'"},
    "img-src": {"'self'", "data:", "blob:"},
    "font-src": {"'self'", "data:"},
    "connect-src": {"'self'"},
    "object-src": {"'none'"},
    "base-uri": {"'none'"},
    "form-action": {"'none'"},
}

#: The header policy: the served one, and frame-ancestors, which only a
#: header can carry.
HEADER = dict(SERVED, **{"frame-ancestors": {"'none'"}})

#: The three headers besides the policy, by exact value.
OTHER_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
}

#: Every source any dash policy may name.  Anything else -- a host, a
#: wildcard, http:, https: -- would admit another origin.
_KEYWORDS = {"'none'", "'self'", "'unsafe-inline'", "'unsafe-eval'"}
_SCHEMES = {"data:", "blob:"}

_META_RE = re.compile(
    r'<meta\s+http-equiv="Content-Security-Policy"\s+content="([^"]*)"\s*/?>')


# ---------------------------------------------------------------------------
# Reading a policy
# ---------------------------------------------------------------------------

def _directives(policy):
    """``{directive: [sources]}`` for a serialized policy.

    CSP3 2.2.1: split on ``;``, drop empty parts, the first token names the
    directive (case-insensitively) and the rest are its sources.  A
    repeated directive fails here: a browser ignores the repeat, so the
    text would claim more than it enforces.
    """
    out = {}
    for part in policy.split(";"):
        tokens = part.split()
        if not tokens:
            continue
        name = tokens[0].lower()
        assert name not in out, f"{name!r} appears twice in {policy!r}"
        out[name] = tokens[1:]
    return out


def _assert_policy(policy, expected):
    """Exactly ``expected``'s directives, each with exactly its sources."""
    got = _directives(policy)
    assert set(got) == set(expected), (
        f"directives {sorted(got)} != {sorted(expected)} in {policy!r}")
    for name, sources in got.items():
        assert len(set(sources)) == len(sources), (
            f"{name} repeats a source: {sources}")
        assert set(sources) == expected[name], (
            f"{name}: {sorted(sources)} != {sorted(expected[name])}")


def _assert_no_other_origin(policy):
    """No directive admits a wildcard, http:, https: or any host."""
    for name, sources in _directives(policy).items():
        for src in sources:
            assert "*" not in src, f"{name} admits a wildcard: {src!r}"
            assert src.lower() not in ("http:", "https:", "ws:", "wss:"), (
                f"{name} admits every {src} origin")
            assert src in _KEYWORDS or src in _SCHEMES, (
                f"{name} admits {src!r}, which names another origin")


def _the_meta_policy(page):
    """The one CSP <meta> in ``page``, as policy text."""
    count = page.lower().count('http-equiv="content-security-policy"')
    found = _META_RE.findall(page)
    assert count == 1 and len(found) == 1, (
        f"{count} CSP <meta> elements ({len(found)} in dash's form); "
        f"exactly one expected")
    return html.unescape(found[0])


def _assert_first(page, what):
    """The policy comes before every script, stylesheet and style element.

    A <meta> policy governs only what the page parses after it (CSP3 3.3),
    so a <script> ahead of it runs unchecked.
    """
    low = page.lower()
    at = low.find('http-equiv="content-security-policy"')
    assert at >= 0, f"{what}: no CSP <meta>"
    for tag in ("<script", "<style", "<link"):
        first = low.find(tag)
        if first >= 0:
            assert at < first, (
                f"{what}: the policy follows the first {tag} (at {at} vs "
                f"{first}); a <meta> policy does not govern what precedes it")


def _script_srcs(page):
    return re.findall(r'<script[^>]*\bsrc="([^"]*)"', page)


# ---------------------------------------------------------------------------
# Pages and apps
# ---------------------------------------------------------------------------

def _frame():
    return pd.DataFrame({
        "mpg": np.linspace(12.0, 41.0, 20),
        "weight": np.linspace(1760.0, 4840.0, 20),
        "foreign": np.array([0.0, 1.0] * 10),
    })


def _standalone_page(layout):
    """A saved dashboard -- a scatter, a dropdown filter and a KPI card --
    as ``DashRenderer.render()`` writes it, under ``layout``."""
    spec = make_spec(
        [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
          "options": {}}],
        filters=[{"varname": "foreign", "type": "dropdown", "exclude": [],
                  "label": ""}],
        kpis=[{"name": "k1", "stat": "mean", "var": "mpg",
               "title": "Avg MPG", "fmt": "%9.2f"}])
    spec["build_options"]["layout"] = layout
    spec["build_options"]["registry"] = "k1 g1"
    d = tempfile.mkdtemp(prefix="dash_csp_")
    sp, dp = os.path.join(d, "spec.json"), os.path.join(d, "data.json")
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(make_data_json(_frame()), fh)
    try:
        return dr.DashRenderer(sp, dp).render()
    finally:
        curdoc().clear()


@pytest.fixture(scope="module")
def pages():
    """The default (layout auto) page and the layout(bs) page."""
    return {"auto": _standalone_page("auto"), "bs": _standalone_page("bs")}


@pytest.fixture(scope="module")
def app(tmp_path_factory):
    """A generated server app: its path, its source, and its namespace.

    The whole file is executed, launcher function included, under a name
    that is not ``__main__`` -- so the launcher block does not run -- and
    with ``curdoc()`` patched, so the module-level ``make_document(curdoc())``
    fills a throwaway document rather than this process's.
    """
    d = str(tmp_path_factory.mktemp("csp_app"))
    path = _build_app(d, title="CSP Dashboard",
                      filters=[{"varname": "foreign", "type": "dropdown",
                                "exclude": [], "label": ""}])
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    ns = {"__name__": "dash_csp_app_under_test"}
    # Named: patch_curdoc holds the document by weak reference only.
    throwaway = Document()
    with patch_curdoc(throwaway):
        exec(compile(src, path, "exec"), ns)
    return types.SimpleNamespace(path=path, src=src, ns=ns)


def _page_for(doc):
    """The page Bokeh's server writes for ``doc``: the same function, with
    the document's own template and template variables."""
    from bokeh.embed.elements import html_page_for_render_items
    return html_page_for_render_items(
        ('<script type="text/javascript" '
         'src="/static/js/bokeh.min.js"></script>', ""),
        {}, [], doc.title, template=doc.template,
        template_variables=doc.template_variables)


def _in_own_loop(fn):
    """Run ``fn()`` on a thread with its own asyncio event loop, which
    Tornado's IOLoop wraps, so building a Server never touches this
    thread's loop.  Returns ``fn``'s value or raises its exception."""
    box = {}

    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            box["value"] = fn()
        except BaseException as exc:          # re-raised on the caller
            box["error"] = exc
        finally:
            asyncio.set_event_loop(None)
            loop.close()

    t = threading.Thread(target=run, daemon=True)
    t.start()
    t.join(60)
    assert not t.is_alive(), "building the server did not return"
    if "error" in box:
        raise box["error"]
    return box.get("value")


def _fetch(srv, path):
    """``(status, headers, body)`` for ``path``, an HTTP error's included."""
    try:
        with urllib.request.urlopen(srv.url(path), timeout=20) as r:
            return r.status, r.headers, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read().decode("utf-8", "replace")


def _assert_headers(headers, where):
    """The four security headers, each exactly once, with dash's values."""
    csp = headers.get_all("Content-Security-Policy") or []
    assert len(csp) == 1, f"{where}: {len(csp)} Content-Security-Policy headers"
    _assert_policy(csp[0], HEADER)
    _assert_no_other_origin(csp[0])
    for name, value in OTHER_HEADERS.items():
        assert (headers.get_all(name) or []) == [value], (
            f"{where}: {name} is {headers.get_all(name)!r}, not [{value!r}]")


# ---------------------------------------------------------------------------
# The constants
# ---------------------------------------------------------------------------

class TestThePolicyConstants:
    """One module constant per policy, so the policy can be adjusted in one
    place and every page that carries it follows."""

    def test_the_standalone_policy_is_exactly_the_verified_one(self):
        assert dr._DASH_CSP_STANDALONE == STANDALONE_TEXT
        _assert_policy(dr._DASH_CSP_STANDALONE, STANDALONE)

    def test_the_served_policy_is_exactly_the_verified_one(self):
        assert dr._DASH_CSP_SERVED == SERVED_TEXT
        _assert_policy(dr._DASH_CSP_SERVED, SERVED)

    def test_the_headers_are_exactly_four(self):
        headers = dict(dr._DASH_SECURITY_HEADERS)
        assert len(headers) == len(dr._DASH_SECURITY_HEADERS) == 4
        assert headers["Content-Security-Policy"] == (
            SERVED_TEXT + "; frame-ancestors 'none'")
        _assert_policy(headers["Content-Security-Policy"], HEADER)
        assert {k: v for k, v in headers.items()
                if k != "Content-Security-Policy"} == OTHER_HEADERS

    @pytest.mark.parametrize("name", ["_DASH_CSP_STANDALONE",
                                      "_DASH_CSP_SERVED"])
    def test_no_meta_policy_carries_frame_ancestors(self, name):
        """The CSP specification ignores frame-ancestors in a <meta>; a
        page that carried it would claim a protection it does not have."""
        assert "frame-ancestors" not in _directives(getattr(dr, name))

    @pytest.mark.parametrize("policy", [STANDALONE_TEXT, SERVED_TEXT,
                                        SERVED_TEXT + "; frame-ancestors "
                                        "'none'"])
    def test_no_policy_admits_another_origin(self, policy):
        _assert_no_other_origin(policy)

    def test_the_headers_cannot_be_changed_in_place(self):
        """A tuple of pairs: a caller that mutates what it was handed must
        not change what every later response carries."""
        assert isinstance(dr._DASH_SECURITY_HEADERS, tuple)
        assert all(isinstance(p, tuple) and len(p) == 2
                   for p in dr._DASH_SECURITY_HEADERS)

    def test_the_standalone_meta_is_built_from_the_constant(self):
        assert dr._CSP_META.startswith(
            dr._dash_csp_meta(dr._DASH_CSP_STANDALONE))

    def test_the_viewport_tag_is_kept(self):
        assert ('<meta name="viewport" '
                'content="width=device-width, initial-scale=1">'
                in dr._CSP_META)


class TestTheMetaWriter:
    """``_dash_csp_meta`` writes the one <meta> both modes carry."""

    def test_it_writes_the_element(self):
        assert dr._dash_csp_meta("default-src 'none'") == (
            '<meta http-equiv="Content-Security-Policy" '
            "content=\"default-src 'none'\">")

    @pytest.mark.parametrize("policy", [STANDALONE_TEXT, SERVED_TEXT])
    def test_every_policy_dash_writes_is_accepted(self, policy):
        assert _the_meta_policy(dr._dash_csp_meta(policy)) == policy

    @pytest.mark.parametrize("bad", [
        'script-src "x"',                  # closes the attribute
        "script-src <x>",                  # markup
        "script-src &quot;",               # an entity
        "script-src {{ x }}",              # a Jinja expression (served)
        "script-src {% x %}",              # a Jinja statement (served)
        "script-src 'self'\nX: y",         # a line break
        "script-src ‘self’",     # not ASCII
        "script-src 'self', 'none'",       # a comma separates policies
        "",
        "   ",
    ])
    def test_it_refuses_text_that_could_leave_the_attribute(self, bad):
        with pytest.raises(ValueError):
            dr._dash_csp_meta(bad)

    def test_it_refuses_a_non_string(self):
        with pytest.raises(TypeError):
            dr._dash_csp_meta(None)


# ---------------------------------------------------------------------------
# The standalone pages
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("layout", ["auto", "bs"])
class TestTheStandalonePages:

    def test_the_page_carries_exactly_the_policy(self, pages, layout):
        _assert_policy(_the_meta_policy(pages[layout]), STANDALONE)

    def test_no_directive_admits_another_origin(self, pages, layout):
        _assert_no_other_origin(_the_meta_policy(pages[layout]))

    def test_the_policy_precedes_every_script_and_style(self, pages, layout):
        """Both pages inline BokehJS in <head>.  On the layout(bs) page the
        <meta> used to follow it, so BokehJS itself ran unchecked."""
        _assert_first(pages[layout], f"layout({layout}) page")

    def test_the_page_is_the_layout_asked_for(self, pages, layout):
        assert ("db-container" in pages[layout]) == (layout == "bs")

    def test_the_viewport_tag_is_still_declared_once(self, pages, layout):
        assert pages[layout].count('name="viewport"') == 1


# ---------------------------------------------------------------------------
# The served page: its template
# ---------------------------------------------------------------------------

def _file_context():
    from bokeh.core.templates import FILE, MACROS
    return dict(title="T", bokeh_js='<script src="/static/js/x.js"></script>',
                bokeh_css="", plot_script="<script>var a = 1;</script>",
                docs=[], base=FILE, macros=MACROS, plot_div="")


class TestTheServedTemplate:
    """``_dash_served_template`` extends Bokeh's own page and adds the
    <meta>; it replaces nothing."""

    def test_it_is_bokehs_page_plus_the_two_metas(self):
        """WP-28 E14: the preamble now carries the viewport meta too, after
        the CSP meta; stripping both, in order, leaves Bokeh's own page."""
        from bokeh.core.templates import FILE
        ctx = _file_context()
        ours = dr._dash_served_template().render(ctx)
        theirs = FILE.render(ctx)
        meta = dr._dash_csp_meta(dr._DASH_CSP_SERVED)
        viewport = dr._DASH_VIEWPORT_META
        assert ours.count(meta) == 1
        assert ours.count(viewport) == 1
        stripped = re.sub(r"[ \t]*" + re.escape(meta) + r"\n?", "", ours,
                          count=1)
        stripped = re.sub(r"[ \t]*" + re.escape(viewport) + r"\n?", "",
                          stripped, count=1)
        assert stripped == theirs, (
            "the template changed more of Bokeh's page than its preamble")

    def test_the_policy_is_in_the_head_ahead_of_everything(self):
        page = dr._dash_served_template().render(_file_context())
        assert page.index("Content-Security-Policy") < page.index("</head>")
        _assert_first(page, "served template")
        _assert_policy(_the_meta_policy(page), SERVED)

    def test_it_names_its_base_itself(self):
        """Bokeh passes ``base`` today; the template does not depend on it."""
        ctx = _file_context()
        del ctx["base"]
        page = dr._dash_served_template().render(ctx)
        _assert_policy(_the_meta_policy(page), SERVED)


# ---------------------------------------------------------------------------
# The served app, in-process
# ---------------------------------------------------------------------------

class TestTheServedApp:

    def test_the_source_defines_the_policy_constants(self, app):
        """Copied through ServerAppBuilder's constant list: a name missing
        from it would be a NameError in the served app."""
        assigned = {}
        for node in ast.parse(app.src).body:
            if (isinstance(node, ast.Assign) and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)):
                assigned.setdefault(node.targets[0].id, []).append(node.value)
        for name in ("_DASH_CSP_SERVED", "_DASH_SECURITY_HEADERS"):
            values = assigned.get(name, [])
            assert len(values) == 1, f"{name} is assigned {len(values)} times"
            assert ast.literal_eval(values[0]) == getattr(dr, name), name
            assert app.ns[name] == getattr(dr, name), name

    @pytest.mark.parametrize("name", ["_dash_csp_meta",
                                      "_dash_served_template",
                                      "_dash_server_transforms"])
    def test_the_helpers_are_the_renderers_own_text(self, app, name):
        """A structural guard, deliberately: the app carries each helper
        once, as the renderer's own text -- which is what lets the tests
        that run the renderer's copies certify the app's."""
        defs = [n for n in ast.parse(app.src).body
                if isinstance(n, ast.FunctionDef) and n.name == name]
        assert len(defs) == 1, f"{name} is defined {len(defs)} times"
        own = textwrap.dedent(inspect.getsource(getattr(dr, name))).strip()
        assert own in app.src, f"{name} in the app is not the renderer's text"

    def test_make_document_sets_the_template(self, app):
        doc = Document()
        app.ns["make_document"](doc)
        assert doc.roots, "make_document built nothing"
        page = _page_for(doc)
        _assert_policy(_the_meta_policy(page), SERVED)
        _assert_first(page, "served page")
        assert "<title>CSP Dashboard</title>" in page

    def test_a_refused_session_is_served_under_the_policy_too(self, app,
                                                              monkeypatch):
        """The template is set before the rate limit is checked, so the
        429 page is no exception."""
        class _Refuse:
            def is_allowed(self, key):
                return False

        monkeypatch.setitem(app.ns, "_SESSION_LIMITER", _Refuse())
        doc = Document()
        app.ns["make_document"](doc)
        assert any("429" in (getattr(r, "text", "") or "")
                   for r in doc.roots), doc.roots
        _assert_policy(_the_meta_policy(_page_for(doc)), SERVED)


class TestTheHeaderTransform:
    """The Tornado output transform the launcher passes to ``Server``."""

    def _transform(self):
        return dr._dash_server_transforms({})[-1]

    def test_it_sets_the_four_headers(self):
        from tornado.httputil import HTTPHeaders
        h = HTTPHeaders({"Content-Type": "text/html; charset=UTF-8"})
        status, out, chunk = self._transform()(None).transform_first_chunk(
            200, h, b"<html></html>", True)
        assert (status, chunk) == (200, b"<html></html>")
        assert out["Content-Type"] == "text/html; charset=UTF-8"
        for name, value in dr._DASH_SECURITY_HEADERS:
            assert out.get_list(name) == [value], name

    def test_it_replaces_a_value_a_handler_set(self):
        from tornado.httputil import HTTPHeaders
        h = HTTPHeaders()
        h.add("X-Frame-Options", "SAMEORIGIN")
        h.add("Content-Security-Policy", "default-src *")
        _, out, _ = self._transform()(None).transform_first_chunk(
            200, h, b"", True)
        assert out.get_list("X-Frame-Options") == ["DENY"]
        assert out.get_list("Content-Security-Policy") == [
            dict(dr._DASH_SECURITY_HEADERS)["Content-Security-Policy"]]

    def test_it_leaves_the_status_and_later_chunks_alone(self):
        from tornado.httputil import HTTPHeaders
        t = self._transform()(None)
        assert t.transform_first_chunk(404, HTTPHeaders(), b"x", False)[0] \
            == 404
        assert t.transform_chunk(b"more", False) == b"more"

    @pytest.mark.parametrize("settings", [
        {}, {"compress_response": True}, {"gzip": True},
        {"compress_response": False}, None])
    def test_tornados_own_transforms_are_kept(self, settings):
        """Given ``transforms=``, Tornado adds none of its own; left alone it
        adds GZipContentEncoding when compress_response (or gzip) is set.
        The list keeps exactly what Tornado would have had, then adds one."""
        from tornado.web import Application, OutputTransform
        got = dr._dash_server_transforms(settings)
        assert got[:-1] == Application(**(settings or {})).transforms
        assert issubclass(got[-1], OutputTransform)


class TestTheLauncherServer:
    """``_dash_server_app`` builds the Server ``python app.py`` runs."""

    def test_the_transforms_reach_tornado(self, app):
        """``Server`` hands ``transforms=`` through ``BokehTornado`` to
        ``tornado.web.Application``, whose list is what every response
        passes through."""
        def build():
            srv = app.ns["_dash_server_app"](port=_free_port())
            try:
                return list(srv._tornado.transforms), dict(srv._tornado.settings)
            finally:
                srv.stop()

        transforms, settings = _in_own_loop(build)
        assert not settings.get("compress_response")
        assert not settings.get("gzip")
        assert [t.__name__ for t in transforms] == [
            t.__name__ for t in app.ns["_dash_server_transforms"](settings)]
        assert len(transforms) == 1

    def test_it_pins_the_script_and_style_types(self, app):
        """nosniff makes a browser refuse a script or stylesheet served under
        any other type, and Tornado types /static with ``mimetypes`` --
        which on Windows reads the registry, where ``.js`` is sometimes
        ``text/plain``.  That registry is simulated here."""
        try:
            mimetypes.add_type("text/plain", ".js")
            mimetypes.add_type("text/plain", ".css")
            assert mimetypes.guess_type("bokeh.min.js")[0] == "text/plain"
            _in_own_loop(
                lambda: app.ns["_dash_server_app"](port=_free_port()).stop())
            assert mimetypes.guess_type("bokeh.min.js")[0] == \
                "text/javascript"
            assert mimetypes.guess_type("bokeh.css")[0] == "text/css"
        finally:
            mimetypes.init()

    def test_help_still_works(self, app):
        r = subprocess.run([sys.executable, app.path, "--help"],
                           capture_output=True, text=True, timeout=180,
                           cwd=os.path.dirname(app.path))
        assert r.returncode == 0, r.stderr[-2000:]
        assert "usage:" in r.stdout and "--port" in r.stdout


# ---------------------------------------------------------------------------
# The real servers
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def launched(tmp_path_factory):
    """``python app.py --port N``, the launcher dash serve runs."""
    path = _build_app(str(tmp_path_factory.mktemp("csp_launched")),
                      title="CSP Launcher")
    with _Launched(path) as srv:
        yield srv


@pytest.fixture(scope="module")
def bokeh_served(tmp_path_factory):
    """``bokeh serve app.py``, which has no launcher."""
    path = _build_app(str(tmp_path_factory.mktemp("csp_served")),
                      title="CSP Bokeh Serve")
    with _Served(path) as srv:
        yield srv


@pytest.mark.serve
class TestThePythonLauncherServes:

    def test_the_page_carries_the_meta(self, launched):
        status, _, page = _fetch(launched, "/")
        assert status == 200
        assert "CSP Launcher" in page
        _assert_policy(_the_meta_policy(page), SERVED)
        _assert_first(page, "launcher page")

    def test_the_page_carries_the_headers(self, launched):
        _, headers, _ = _fetch(launched, "/")
        _assert_headers(headers, "/")

    def test_health_carries_the_headers(self, launched):
        status, headers, body = _fetch(launched, "/health")
        assert status == 200 and json.loads(body)["status"] == "ok"
        _assert_headers(headers, "/health")

    def test_a_missing_page_carries_the_headers(self, launched):
        status, headers, _ = _fetch(launched, "/no-such-page")
        assert status == 404
        _assert_headers(headers, "404")

    def test_the_websocket_still_opens(self, launched):
        """The transform runs on the websocket handshake's response as well;
        a session must still open and deliver the whole document."""
        from bokeh.client import pull_session
        session = pull_session(url=launched.url("/"))
        try:
            assert list(session.document.roots), "the session is empty"
            assert session.document.title == "CSP Launcher"
        finally:
            session.close()

    def test_bokehjs_is_same_origin_and_typed_as_script(self, launched):
        """'self' covers BokehJS only if the page asks for it by a path on
        this server; nosniff lets it run only if it is typed as script."""
        _, _, page = _fetch(launched, "/")
        srcs = _script_srcs(page)
        assert srcs, "the page loads no script from the server"
        for src in srcs:
            assert src.startswith("/") and not src.startswith("//"), (
                f"{src!r} is not a path on this server; 'self' may not "
                f"cover it")
        status, headers, _ = _fetch(launched, srcs[0])
        assert status == 200
        assert headers.get_content_type() in (
            "text/javascript", "application/javascript"), (
            headers.get_content_type())
        _assert_headers(headers, srcs[0])


@pytest.mark.serve
class TestBokehServeServes:

    def test_the_page_carries_the_meta(self, bokeh_served):
        status, _, page = _fetch(bokeh_served, "/app")
        assert status == 200
        _assert_policy(_the_meta_policy(page), SERVED)
        _assert_first(page, "bokeh serve page")

    def test_its_scripts_are_same_origin(self, bokeh_served):
        _, _, page = _fetch(bokeh_served, "/app")
        srcs = _script_srcs(page)
        assert srcs
        assert all(s.startswith("/") and not s.startswith("//")
                   for s in srcs), srcs

    def test_it_sends_no_security_header(self, bokeh_served):
        """What dash.sthlp says: ``bokeh serve`` owns its responses, so only
        the <meta> applies there.  If Bokeh ever sends a policy of its own,
        this fails and the help is due for a change."""
        _, headers, _ = _fetch(bokeh_served, "/app")
        assert headers.get("Content-Security-Policy") is None
        assert headers.get("X-Frame-Options") is None


# ---------------------------------------------------------------------------
# The help
# ---------------------------------------------------------------------------

class TestTheHelpSaysWhatIsSent:

    def test_the_server_mode_section_names_the_policy_and_headers(self):
        with open(os.path.join(_HERE, "..", "dash.sthlp"),
                  encoding="utf-8") as fh:
            h = fh.read()
        i = h.index("{marker server_mode}")
        sec = re.sub(r"\s+", " ", h[i:h.index("{marker examples}", i)])
        assert "Content-Security-Policy in both modes" in sec
        assert "{cmd:frame-ancestors 'none'}" in sec
        for name, value in OTHER_HEADERS.items():
            assert "{cmd:%s: %s}" % (name, value) in sec, name
        assert "{cmd:bokeh serve app.py} sends none of these headers" in sec
