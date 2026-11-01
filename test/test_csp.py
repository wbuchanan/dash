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

WP-30 P1.29 took 'unsafe-inline' out of every script-src a page carries:
the saved page names each script Bokeh wrote by its SHA-256 hash
(``_dash_saved_head``) and dash refuses to write a page holding any other
inline script (``_dash_seal_saved_page``); the served page's <meta> names a
nonce made for that page, which every script of the page carries
(``_dash_served_template(nonce)``).  The launcher's header keeps its
policy, which cannot know the nonce (A99).

These tests pin the policy text, where it sits in each page, that the
served app carries the same constants, and that each real server sends
what it should.  Whether a browser runs a dashboard under these policies,
and refuses an injected script, is ``test_csp_browser.py``'s: it drives
both modes in headless Chrome.  The live-server classes here start
subprocesses and are marked ``serve`` (deselect with ``-m 'not serve'``);
no browser is opened here.
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
from conftest import exec_app, make_data_json, make_spec  # noqa: E402
from test_server_serves import (  # noqa: E402
    _Launched, _Served, _build_app, _free_port)


# ---------------------------------------------------------------------------
# What each page must carry -- exactly these directives, exactly these sources
# ---------------------------------------------------------------------------

# Flipped (WP-30 P1.29): script-src lost 'unsafe-inline'; each page inserts
# the hashes of its own scripts (_dash_csp_standalone).
STANDALONE_TEXT = (
    "default-src 'none'; script-src 'unsafe-eval'; "
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
    "script-src": {"'unsafe-eval'"},
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

#: The served page's own <meta> base (WP-30 P1.29): script-src names only
#: the page's nonce, inserted per page, and 'unsafe-eval'.
SERVED_META_TEXT = (
    "default-src 'none'; script-src 'unsafe-eval'; "
    "style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; "
    "font-src 'self' data:; connect-src 'self'; object-src 'none'; "
    "base-uri 'none'; form-action 'none'")

SERVED_META = dict(SERVED, **{"script-src": {"'unsafe-eval'"}})

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
    """No directive admits a wildcard, http:, https: or any host.

    Flipped (WP-30 P1.29): a script hash or a nonce, in exactly their
    forms, names no origin and is admitted too."""
    for name, sources in _directives(policy).items():
        for src in sources:
            assert "*" not in src, f"{name} admits a wildcard: {src!r}"
            assert src.lower() not in ("http:", "https:", "ws:", "wss:"), (
                f"{name} admits every {src} origin")
            assert (src in _KEYWORDS or src in _SCHEMES
                    or _HASH_RE.fullmatch(src) or _NONCE_RE.fullmatch(src)), (
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
# A page's own scripts, read the way a browser's parser reads them (WP-30
# P1.29) -- html.parser, not the renderer's scan, so the two are checked
# against each other
# ---------------------------------------------------------------------------

#: The type values under which a browser runs an inline script: none or an
#: empty one, a JavaScript MIME type, or ``module`` (HTML, "prepare the
#: script element").
_JS_TYPES = {"", "module", "application/ecmascript", "application/javascript",
             "application/x-ecmascript", "application/x-javascript",
             "text/ecmascript", "text/javascript", "text/javascript1.0",
             "text/javascript1.1", "text/javascript1.2", "text/javascript1.3",
             "text/javascript1.4", "text/javascript1.5", "text/jscript",
             "text/livescript", "text/x-ecmascript", "text/x-javascript"}

_HASH_RE = re.compile(r"'sha256-[A-Za-z0-9+/]{43}='")
_NONCE_RE = re.compile(r"'nonce-[A-Za-z0-9_-]{22,64}'")


def _script_elements(page):
    """``[(attrs, body)]`` for every script element of ``page``, in order,
    as ``html.parser`` reads them (a script's body is raw text up to its
    ``</script``)."""
    from html.parser import HTMLParser

    class _P(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.found, self.cur = [], None

        def handle_starttag(self, tag, attrs):
            if tag == "script":
                self.cur = [dict((k, v or "") for k, v in attrs), ""]
                self.found.append(self.cur)

        def handle_data(self, data):
            if self.cur is not None:
                self.cur[1] += data

        def handle_endtag(self, tag):
            if tag == "script":
                self.cur = None

    p = _P()
    p.feed(page)
    p.close()
    return [(a, b) for a, b in p.found]


def _executable_inline_hashes(page):
    """The base64 SHA-256 of every inline script ``page`` would run, over
    its LF text."""
    import base64
    import hashlib
    out = set()
    for attrs, body in _script_elements(page):
        if "src" in attrs:
            continue
        if attrs.get("type", "").strip().lower() not in _JS_TYPES:
            continue
        body = body.replace("\r\n", "\n").replace("\r", "\n")
        out.add(base64.b64encode(
            hashlib.sha256(body.encode("utf-8")).digest()).decode("ascii"))
    return out


def _the_page_nonce(page):
    """The one nonce the page's policy names."""
    srcs = _directives(_the_meta_policy(page)).get("script-src", [])
    found = [s for s in srcs if s.startswith("'nonce-")]
    assert len(found) == 1, (
        f"the page's script-src names {len(found)} nonces, not one: {srcs}")
    return found[0][len("'nonce-"):-1]


def _assert_scripts_carry(page, nonce):
    """Every script element of ``page`` carries ``nonce``."""
    elements = _script_elements(page)
    assert elements, "the page has no script"
    for attrs, body in elements:
        assert attrs.get("nonce") == nonce, (
            f"a script without the page's nonce: {attrs} {body[:80]!r}")


def _assert_saved_policy(page):
    """The saved page's policy: STANDALONE, with script-src naming exactly
    the page's own inline scripts by hash and 'unsafe-eval' (WP-30
    P1.29)."""
    hashes = {"'sha256-%s'" % h for h in _executable_inline_hashes(page)}
    assert hashes, "the page has no inline script"
    _assert_policy(_the_meta_policy(page), dict(
        STANDALONE, **{"script-src": {"'unsafe-eval'"} | hashes}))


def _assert_served_policy(page):
    """The served page's <meta> policy: SERVED_META, with script-src naming
    the page's one nonce and 'unsafe-eval', and every script of the page
    carrying that nonce (WP-30 P1.29)."""
    nonce = _the_page_nonce(page)
    _assert_policy(_the_meta_policy(page), dict(
        SERVED_META, **{"script-src": {"'unsafe-eval'",
                                       "'nonce-%s'" % nonce}}))
    _assert_scripts_carry(page, nonce)


# ---------------------------------------------------------------------------
# Pages and apps
# ---------------------------------------------------------------------------

def _frame():
    return pd.DataFrame({
        "mpg": np.linspace(12.0, 41.0, 20),
        "weight": np.linspace(1760.0, 4840.0, 20),
        "foreign": np.array([0.0, 1.0] * 10),
    })


def _saved_spec_files(layout, *, plots=None, tabs="", csv=False,
                      filter_position="", range_filter=False, by="",
                      colorvar="", xtitle="", title="", subtitle=""):
    """``(spec path, data path)`` of a saved dashboard -- a scatter, a
    dropdown filter and a KPI card -- under ``layout``; each keyword adds
    what one page family needs (WP-30 P1.29): tabs, the CSV button, a
    range filter, the filter sidebar, a by() graph, colorvar(), a TeX axis
    title (MathJax inlined), or other layers."""
    opts = {"colorvar": colorvar} if colorvar else {}
    filters = [{"varname": "foreign", "type": "dropdown", "exclude": [],
                "label": ""}]
    if range_filter:
        filters.append({"varname": "weight", "type": "range", "exclude": [],
                        "label": ""})
    spec = make_spec(
        plots or [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                   "options": opts}],
        filters=filters,
        kpis=[{"name": "k1", "stat": "mean", "var": "mpg",
               "title": "Avg MPG", "fmt": "%9.2f"}])
    go = spec["graphs"][0]["graph_options"]
    if by:
        go["by"] = by
    if xtitle:
        go["xtitle"] = xtitle
    bo = spec["build_options"]
    bo["layout"] = layout
    bo["registry"] = "k1 g1"
    if tabs:
        bo["tabs"] = tabs
    if csv:
        bo["csv"] = "1"
    if filter_position:
        bo["filter_position"] = filter_position
    bo["title"], bo["subtitle"] = title, subtitle
    d = tempfile.mkdtemp(prefix="dash_csp_")
    sp, dp = os.path.join(d, "spec.json"), os.path.join(d, "data.json")
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(make_data_json(_frame()), fh)
    return sp, dp


def _standalone_page(layout, **kw):
    """A saved dashboard as ``DashRenderer.render()`` writes it, under
    ``layout``; ``kw`` as :func:`_saved_spec_files` takes them."""
    sp, dp = _saved_spec_files(layout, **kw)
    try:
        return dr.DashRenderer(sp, dp).render()
    finally:
        curdoc().clear()


#: The saved page families whose scripts the policy must name (WP-30
#: P1.29): the default and layout(bs) pages; tabs with the CSV button and a
#: range filter; the filter sidebar; a TeX axis title, which inlines
#: MathJax; a by() graph; and the stale-cue page (an lfit beside the
#: scatter, with a title and subtitle).
_FAMILIES = {
    "auto": dict(layout="auto"),
    "bs": dict(layout="bs"),
    "csv_tabs_range": dict(layout="auto", tabs="Main: g1", csv=True,
                           range_filter=True),
    "filterposition_left": dict(layout="auto", filter_position="left"),
    "tex_title": dict(layout="auto", xtitle="$$\\beta$$"),
    "by": dict(layout="auto", by="foreign", colorvar="foreign"),
    "stale_cue": dict(layout="auto", title="T", subtitle="S", plots=[
        {"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}},
        {"type": "lfit", "yvar": "mpg", "xvar": "weight", "options": {}}]),
}


@pytest.fixture(scope="module")
def family_pages():
    """Each family's saved page, rendered once, when first asked for."""
    class _Pages(dict):
        def __missing__(self, name):
            kw = dict(_FAMILIES[name])
            self[name] = _standalone_page(kw.pop("layout"), **kw)
            return self[name]
    return _Pages()


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
        exec_app(src, path, ns)
    # WP-29 P0.12a: a key installed, as dash serve's is, so building a
    # Server here makes and announces none.
    ns["_DASH_SERVE_TOKEN"] = "dashTestKey_0123456789abcdefghijklmnopqrstuvwxyz"
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
                                      "_DASH_CSP_SERVED",
                                      "_DASH_CSP_SERVED_META",
                                      "_DASH_CSP_NO_SCRIPTS"])
    def test_no_meta_policy_carries_frame_ancestors(self, name):
        """The CSP specification ignores frame-ancestors in a <meta>; a
        page that carried it would claim a protection it does not have."""
        assert "frame-ancestors" not in _directives(getattr(dr, name))

    # Flipped (WP-30 P1.29): a hashed and a nonce'd policy, each source in
    # its exact form, admit no other origin either.
    @pytest.mark.parametrize("policy", [
        STANDALONE_TEXT, SERVED_TEXT, SERVED_META_TEXT,
        SERVED_TEXT + "; frame-ancestors 'none'",
        dr._dash_csp_standalone(["A" * 43 + "=", "b+/" * 14 + "c="]),
        dr._dash_csp_served("Nonce_-" * 4)])
    def test_no_policy_admits_another_origin(self, policy):
        _assert_no_other_origin(policy)

    def test_the_headers_cannot_be_changed_in_place(self):
        """A tuple of pairs: a caller that mutates what it was handed must
        not change what every later response carries."""
        assert isinstance(dr._DASH_SECURITY_HEADERS, tuple)
        assert all(isinstance(p, tuple) and len(p) == 2
                   for p in dr._DASH_SECURITY_HEADERS)

    def test_the_standalone_meta_is_built_from_the_constant(self):
        """Flipped (WP-30 P1.29): the saved page's head is built per page
        from the page's script hashes, no longer a constant."""
        h = _b64sha("x")
        assert dr._dash_saved_head([]).startswith(
            dr._dash_csp_meta(dr._DASH_CSP_STANDALONE))
        assert dr._dash_saved_head([h]).startswith(
            dr._dash_csp_meta(dr._dash_csp_standalone([h])))
        assert "'sha256-%s'" % h in dr._dash_saved_head([h])

    def test_the_viewport_tag_is_kept(self):
        """Flipped (WP-30 P1.29): read from _dash_saved_head."""
        assert ('<meta name="viewport" '
                'content="width=device-width, initial-scale=1">'
                in dr._dash_saved_head([]))


class TestTheMetaWriter:
    """``_dash_csp_meta`` writes the one <meta> both modes carry."""

    def test_it_writes_the_element(self):
        assert dr._dash_csp_meta("default-src 'none'") == (
            '<meta http-equiv="Content-Security-Policy" '
            "content=\"default-src 'none'\">")

    @pytest.mark.parametrize("policy", [
        STANDALONE_TEXT, SERVED_TEXT, SERVED_META_TEXT,
        dr._DASH_CSP_NO_SCRIPTS,
        dr._dash_csp_standalone(["A" * 43 + "=", "b+/" * 14 + "c="]),
        dr._dash_csp_served("Nonce_-" * 4)])
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
# The saved page's script hashes (WP-30 P1.29)
# ---------------------------------------------------------------------------

def _b64sha(text):
    import base64
    import hashlib
    return base64.b64encode(
        hashlib.sha256(text.encode("utf-8")).digest()).decode("ascii")


class TestTheScriptHashes:
    """``_dash_script_hashes`` names each inline script a browser would run
    by the base64 SHA-256 of its text -- the form a policy's
    ``'sha256-...'`` source takes."""

    def test_only_executable_inline_scripts_are_hashed(self):
        page = ('<html><head><script>a();</script>'
                '<script type="application/json" id="d">{"x": 1}</script>'
                '<script src="x.js"></script>'
                '<script type="text/javascript">b();</script>'
                '</head><body><script>a();</script></body></html>')
        got = dr._dash_script_hashes(page)
        assert got == sorted({_b64sha("a();"), _b64sha("b();")})
        assert set(got) == _executable_inline_hashes(page)
        assert dr._dash_script_hashes("<p>no script</p>") == []

    def test_forms_and_line_endings(self):
        lf = dr._dash_script_hashes("<script>a();\nb();\n</script>")
        assert dr._dash_script_hashes("<script>a();\r\nb();\r\n</script>") \
            == lf == dr._dash_script_hashes("<script>a();\rb();\r</script>")
        assert lf == [_b64sha("a();\nb();\n")]
        # Upper case, a module, a JavaScript MIME type with spaces and case.
        assert dr._dash_script_hashes("<SCRIPT>c()</SCRIPT>") == \
            [_b64sha("c()")]
        assert dr._dash_script_hashes(
            "<script type='module'>m()</script>") == [_b64sha("m()")]
        assert dr._dash_script_hashes(
            '<script type=" Text/JavaScript ">t()</script>') == \
            [_b64sha("t()")]
        # Not run inline: a src= script, JSON, any other type.
        assert dr._dash_script_hashes(
            '<script src="a.js">ignored()</script>'
            '<script type="application/json">{}</script>'
            '<script type="text/template">x</script>') == []
        # An unclosed script runs to the end of the text.
        assert dr._dash_script_hashes("<p></p><script>u()") == \
            [_b64sha("u()")]
        # A tag name that only begins with "script" is not a script.
        assert dr._dash_script_hashes("<scripts>x</scripts>") == []
        with pytest.raises(TypeError):
            dr._dash_script_hashes(None)


class TestTheStandalonePolicy:

    def test_hashes_are_inserted_sorted_and_once(self):
        h1, h2 = _b64sha("one"), _b64sha("two")
        lo, hi = sorted((h1, h2))
        policy = dr._dash_csp_standalone([hi, lo, hi])
        assert _directives(policy)["script-src"] == [
            "'sha256-%s'" % lo, "'sha256-%s'" % hi, "'unsafe-eval'"]
        _assert_policy(policy, dict(STANDALONE, **{"script-src": {
            "'sha256-%s'" % lo, "'sha256-%s'" % hi, "'unsafe-eval'"}}))
        assert dr._dash_csp_standalone([]) == dr._DASH_CSP_STANDALONE
        assert _the_meta_policy(dr._dash_csp_meta(policy)) == policy
        for bad in (["x"], [h1 + "x"], ["'%s'" % h1], [h1[:-1] + "!"]):
            with pytest.raises(ValueError):
                dr._dash_csp_standalone(bad)


# ---------------------------------------------------------------------------
# The standalone pages
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("layout", ["auto", "bs"])
class TestTheStandalonePages:

    def test_the_page_carries_exactly_the_policy(self, pages, layout):
        """Flipped (WP-30 P1.29): script-src is 'unsafe-eval' and the
        hashes of exactly the page's own scripts."""
        _assert_saved_policy(pages[layout])

    def test_no_directive_admits_another_origin(self, pages, layout):
        """Flipped (WP-30 P1.29): the page's hash sources are admitted."""
        _assert_no_other_origin(_the_meta_policy(pages[layout]))

    def test_the_policy_precedes_every_script_and_style(self, pages, layout):
        """Both pages inline BokehJS in <head>.  On the layout(bs) page the
        <meta> used to follow it, so BokehJS itself ran unchecked."""
        _assert_first(pages[layout], f"layout({layout}) page")

    def test_the_page_is_the_layout_asked_for(self, pages, layout):
        assert ("db-container" in pages[layout]) == (layout == "bs")

    def test_the_viewport_tag_is_still_declared_once(self, pages, layout):
        assert pages[layout].count('name="viewport"') == 1


@pytest.mark.parametrize("family", sorted(_FAMILIES))
class TestTheSavedPageAdmitsOnlyItsOwnScripts:
    """WP-30 P1.29: script-src named 'unsafe-inline', so any inline script
    or event handler that reached a saved page ran (BUGS.md:1337 records
    one).  It now names each script dash wrote by its hash."""

    def test_script_src_has_no_unsafe_inline(self, family_pages, family):
        src = _directives(_the_meta_policy(family_pages[family]))["script-src"]
        assert "'unsafe-inline'" not in src, (
            f"{family}: script-src still admits every inline script: {src}")

    def test_the_hashes_are_exactly_the_pages_scripts(self, family_pages,
                                                       family):
        page = family_pages[family]
        src = _directives(_the_meta_policy(page))["script-src"]
        named = {s[len("'sha256-"):-1] for s in src
                 if s.startswith("'sha256-")}
        assert named, f"{family}: the policy names no script hash: {src}"
        assert named == _executable_inline_hashes(page), (
            f"{family}: the hashes the policy names are not the page's "
            f"scripts")

    def test_eval_and_inline_styles_are_kept(self, family_pages, family):
        """BokehJS compiles CustomJS and formatters with ``new Function``
        and writes its styles as it draws (measured: 884 style
        violations without 'unsafe-inline')."""
        d = _directives(_the_meta_policy(family_pages[family]))
        assert "'unsafe-eval'" in d["script-src"]
        assert set(d["style-src"]) == {"'unsafe-inline'"}


_EVIL = "<script>window.__dash_evil = 1;</script>"


@pytest.mark.parametrize("where", ["bs_header", "auto_scheme_css"])
class TestAHostileFragmentIsNotAdmitted:
    """The hashes are taken over Bokeh's own output before dash splices its
    HTML in, and the finished page is checked against them: a script an
    escaping fault let into dash's own HTML is refused, never blessed."""

    def test_render_refuses_and_writes_nothing(self, monkeypatch, tmp_path,
                                               where):
        if where == "bs_header":
            monkeypatch.setattr(dr, "_dash_header_fragments",
                                lambda t, s: (_EVIL, ""))
            layout = "bs"
        else:
            own = dr.SchemeParser.css_style_element
            monkeypatch.setattr(dr.SchemeParser, "css_style_element",
                                lambda self: own(self) + _EVIL)
            layout = "auto"
        sp, dp = _saved_spec_files(layout, title="T")
        out = tmp_path / "page.html"
        err = None
        try:
            dr.main(sp, dp, str(out))
        except Exception as exc:          # the error is the point
            err = exc
        finally:
            curdoc().clear()
        assert err is not None, (
            "the page was written with the script (%s)"
            % ("on disk" if out.exists() else "not on disk"))
        assert type(err).__name__ == "DashScriptPolicyError", repr(err)
        assert isinstance(err, dr.DashScriptPolicyError)
        assert "nothing was written" in str(err)
        assert not out.exists()

    def test_the_seal_refuses_an_unhashed_script(self, where):
        # Fixture updated (WP-30 P1.30): a saved page's head holds its one
        # policy, which the seal now also requires.
        page = ("<html><head><meta http-equiv=\"Content-Security-Policy\" "
                "content=\"x\"><script>a();</script></head><body>"
                + ("<p>x</p>" if where == "bs_header" else "")
                + "</body></html>")
        hashes = dr._dash_script_hashes(page)
        assert dr._dash_seal_saved_page(page, hashes) == page
        bad = page.replace("</body>", _EVIL + "</body>")
        with pytest.raises(dr.DashScriptPolicyError,
                           match=r"1 inline script\(s\)"):
            dr._dash_seal_saved_page(bad, hashes)
        # A JSON block and a src= script run nothing inline.
        ok = page.replace("</body>", '<script type="application/json">{}'
                          '</script><script src="x.js"></script></body>')
        assert dr._dash_seal_saved_page(ok, hashes) == ok
        assert issubclass(dr.DashScriptPolicyError, RuntimeError)


class TestTheEmptyAndRedirectPages:
    """Neither page holds a script, so ``default-src 'none'`` costs them
    nothing (WP-30 P1.29.8)."""

    def test_the_empty_page_runs_nothing(self):
        spec = make_spec([{"type": "scatter", "yvar": "mpg",
                           "xvar": "weight", "options": {}}])
        spec["graphs"], spec["build_options"]["registry"] = [], ""
        spec["build_options"]["layout"] = "bs"
        d = tempfile.mkdtemp(prefix="dash_csp_empty_")
        sp, dp = os.path.join(d, "spec.json"), os.path.join(d, "data.json")
        with open(sp, "w") as fh:
            json.dump(spec, fh)
        with open(dp, "w") as fh:
            json.dump(make_data_json(_frame()), fh)
        try:
            page = dr.DashRenderer(sp, dp).render()
        finally:
            curdoc().clear()
        assert "No dashboard content." in page
        _assert_policy(_the_meta_policy(page), {"default-src": {"'none'"}})
        head = page[page.index("<head>") + len("<head>"):]
        assert head.startswith('<meta http-equiv="Content-Security-Policy"')
        assert "style=" not in page

    def test_the_redirect_page_runs_nothing(self):
        url = 'http://127.0.0.1:5006/?token=a&b="<x>'
        page = dr._dash_redirect_page(url)
        _assert_policy(_the_meta_policy(page), {"default-src": {"'none'"}})
        assert ('<meta charset="utf-8"><meta http-equiv='
                '"Content-Security-Policy" content="default-src \'none\'">'
                in page)
        assert '<meta name="referrer" content="no-referrer">' in page
        assert "<x>" not in page and "&lt;x&gt;" in page
        assert _script_elements(page) == []


# ---------------------------------------------------------------------------
# The served page: its template
# ---------------------------------------------------------------------------

def _file_context():
    from bokeh.core.templates import FILE, MACROS
    return dict(title="T", bokeh_js='<script src="/static/js/x.js"></script>',
                bokeh_css="", plot_script="<script>var a = 1;</script>",
                docs=[], base=FILE, macros=MACROS, plot_div="")


class TestTheNonce:
    """The served page's one-time nonce (WP-30 P1.29)."""

    def test_a_nonce_is_fresh_and_urlsafe(self):
        a, b = dr._dash_new_nonce(), dr._dash_new_nonce()
        assert a != b
        for n in (a, b):
            assert re.fullmatch(r"[A-Za-z0-9_-]{24}", n), n

    def test_the_served_policy_names_the_nonce_and_no_unsafe_inline(self):
        n = "Ab0_-" * 4 + "Zz9_"
        policy = dr._dash_csp_served(n)
        src = _directives(policy)["script-src"]
        assert src == ["'nonce-%s'" % n, "'unsafe-eval'"]
        assert "'unsafe-inline'" not in src
        _assert_policy(policy, dict(SERVED_META, **{"script-src": {
            "'nonce-%s'" % n, "'unsafe-eval'"}}))
        _assert_no_other_origin(policy)
        assert _the_meta_policy(dr._dash_csp_meta(policy)) == policy
        for bad in ("abc", "a" * 65, 'x"y' * 8, "{{x}}" * 5, "a b" * 8,
                    "é" * 24):
            with pytest.raises(ValueError):
                dr._dash_csp_served(bad)
        with pytest.raises(TypeError):
            dr._dash_csp_served(None)


class TestTheServedTemplate:
    """``_dash_served_template`` extends Bokeh's own page and adds the
    <meta>; it replaces nothing."""

    def test_only_script_elements_get_the_nonce(self):
        """Each script element's opening tag gains the nonce; a script's
        body is never edited, even where it holds the text of a tag (an
        INLINE bundle does: bokeh-tables.min.js twice, measured), and
        escaped text that only spells a tag gets nothing."""
        n = "Nonce_" * 4
        ctx = _file_context()
        ctx["title"] = "</title><script>alert(1)</script>"
        ctx["plot_script"] = (
            '<script>var s = "<script>";</script>\n'
            '<script type="application/json" id="d">'
            '{"t": "&lt;script&gt;"}</script>')
        page = dr._dash_served_template(n).render(ctx)
        _assert_scripts_carry(page, n)
        assert len(_script_elements(page)) == 3
        assert 'var s = "<script>";' in page
        assert "&lt;/title&gt;&lt;script&gt;alert(1)" in page
        assert page.count('nonce="%s"' % n) == 3
        assert _the_page_nonce(page) == n

        from bokeh.embed import file_html
        from bokeh.plotting import figure
        from bokeh.resources import INLINE
        fig = figure()
        fig.scatter([1, 2], [3, 4])
        page = file_html(fig, INLINE, "t", template=dr._dash_served_template(n))
        _assert_scripts_carry(page, n)
        assert len(_script_elements(page)) >= 3
        assert _the_page_nonce(page) == n

    def test_a_bad_nonce_is_refused(self):
        with pytest.raises(ValueError):
            dr._dash_served_template("bad")

    def test_it_is_bokehs_page_plus_the_two_metas(self):
        """WP-28 E14: the preamble carries the viewport meta too, after the
        CSP meta.  Rewritten (WP-30 P1.29): the template also gives every
        script element the page's nonce; stripping the two metas and every
        ` nonce="N"` leaves Bokeh's own page, byte for byte."""
        from bokeh.core.templates import FILE
        n = "Nonce_-" * 4
        ctx = _file_context()
        ours = dr._dash_served_template(n).render(ctx)
        theirs = FILE.render(ctx)
        meta = dr._dash_csp_meta(dr._dash_csp_served(n))
        viewport = dr._DASH_VIEWPORT_META
        assert ours.count(meta) == 1
        assert ours.count(viewport) == 1
        assert ours.count(' nonce="%s"' % n) == len(_script_elements(ours))
        stripped = re.sub(r"[ \t]*" + re.escape(meta) + r"\n?", "", ours,
                          count=1)
        stripped = re.sub(r"[ \t]*" + re.escape(viewport) + r"\n?", "",
                          stripped, count=1)
        stripped = stripped.replace(' nonce="%s"' % n, "")
        assert stripped == theirs, (
            "the template changed more of Bokeh's page than its preamble "
            "and its scripts' nonce")

    def test_the_policy_is_in_the_head_ahead_of_everything(self):
        page = dr._dash_served_template().render(_file_context())
        assert page.index("Content-Security-Policy") < page.index("</head>")
        _assert_first(page, "served template")
        # Flipped (WP-30 P1.29): the meta's policy names the page's nonce.
        _assert_served_policy(page)

    def test_it_names_its_base_itself(self):
        """Bokeh passes ``base`` today; the template does not depend on it."""
        ctx = _file_context()
        del ctx["base"]
        page = dr._dash_served_template().render(ctx)
        # Flipped (WP-30 P1.29): the meta's policy names the page's nonce.
        _assert_served_policy(page)


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
        for name in ("_DASH_CSP_SERVED", "_DASH_SECURITY_HEADERS",
                     "_DASH_CSP_SERVED_META", "_DASH_CSP_NO_SCRIPTS"):
            values = assigned.get(name, [])
            assert len(values) == 1, f"{name} is assigned {len(values)} times"
            assert ast.literal_eval(values[0]) == getattr(dr, name), name
            assert app.ns[name] == getattr(dr, name), name

    @pytest.mark.parametrize("name", ["_dash_csp_meta",
                                      "_dash_served_template",
                                      "_dash_server_transforms",
                                      "_dash_new_nonce", "_dash_csp_served",
                                      "_dash_nonce_scripts"])
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
        # Flipped (WP-30 P1.29): the meta's policy names the page's nonce.
        _assert_served_policy(page)
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
        # Flipped (WP-30 P1.29): the refused page is nonce'd too.
        _assert_served_policy(_page_for(doc))

    def test_each_document_gets_its_own_nonce(self, app):
        """One make_document call per session, one page per session: each
        page's scripts carry the nonce its own policy names."""
        pages = []
        for _ in range(2):
            doc = Document()
            app.ns["make_document"](doc)
            pages.append(_page_for(doc))
        nonces = [_the_page_nonce(p) for p in pages]
        assert nonces[0] != nonces[1]
        for page, n in zip(pages, nonces):
            _assert_scripts_carry(page, n)
            assert "'unsafe-inline'" not in _directives(
                _the_meta_policy(page))["script-src"]


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


# One worker for the class, so the module's launched server starts
# once, not once per worker its tests land on (WP-30 test
# performance A4; measured 07oct2026: 0.95 s on six).
@pytest.mark.xdist_group(name="csp-launched")
@pytest.mark.serve
class TestThePythonLauncherServes:

    def test_the_page_carries_the_meta(self, launched):
        status, _, page = _fetch(launched, "/")
        assert status == 200
        assert "CSP Launcher" in page
        # Flipped (WP-30 P1.29): the meta's policy names the page's nonce.
        _assert_served_policy(page)
        _assert_first(page, "launcher page")

    def test_the_page_carries_the_headers(self, launched):
        _, headers, _ = _fetch(launched, "/")
        _assert_headers(headers, "/")

    def test_every_script_carries_the_pages_nonce(self, launched):
        """Two GETs, two sessions, two nonces; the header policy, which
        cannot know them, is unchanged (A99)."""
        _, headers, first = _fetch(launched, "/")
        _, _, second = _fetch(launched, "/")
        n1, n2 = _the_page_nonce(first), _the_page_nonce(second)
        assert n1 != n2
        _assert_scripts_carry(first, n1)
        _assert_scripts_carry(second, n2)
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
        # Flipped (WP-29 P0.12a): the session carries the dashboard's key.
        session = pull_session(url=launched.url("/", token=False),
                               arguments={"token": launched.token})
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


# One worker for the class, so the module's bokeh serve process
# starts once, not once per worker its tests land on (WP-30 test
# performance A4; measured 07oct2026: 1.1 s on four).
@pytest.mark.xdist_group(name="csp-bokeh-served")
@pytest.mark.serve
class TestBokehServeServes:

    def test_the_page_carries_the_meta(self, bokeh_served):
        status, _, page = _fetch(bokeh_served, "/app")
        assert status == 200
        # Flipped (WP-30 P1.29): the meta's policy names the page's nonce.
        _assert_served_policy(page)
        _assert_first(page, "bokeh serve page")

    def test_its_scripts_are_same_origin(self, bokeh_served):
        _, _, page = _fetch(bokeh_served, "/app")
        srcs = _script_srcs(page)
        assert srcs
        assert all(s.startswith("/") and not s.startswith("//")
                   for s in srcs), srcs

    def test_every_script_carries_the_pages_nonce(self, bokeh_served):
        _, _, first = _fetch(bokeh_served, "/app")
        _, _, second = _fetch(bokeh_served, "/app")
        n1, n2 = _the_page_nonce(first), _the_page_nonce(second)
        assert n1 != n2
        _assert_scripts_carry(first, n1)
        _assert_scripts_carry(second, n2)

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

    def test_it_says_what_the_policy_protects(self):
        """WP-30 P1.29: the help said a saved dashboard "may run only the
        scripts and styles written into it", which 'unsafe-inline' did not
        enforce."""
        with open(os.path.join(_HERE, "..", "dash.sthlp"),
                  encoding="utf-8") as fh:
            h = fh.read()
        i = h.index("{marker server_mode}")
        sec = re.sub(r"\s+", " ", h[i:h.index("{marker examples}", i)])
        assert "may run only the scripts and styles written into it" \
            not in sec
        for phrase in ("SHA-256", "nonce", "{cmd:'unsafe-eval'}",
                       "inline styles", "CSP level 1",
                       "{cmd:default-src 'none'}"):
            assert phrase in sec, phrase
