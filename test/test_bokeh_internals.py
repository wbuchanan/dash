"""The Bokeh internals dash's protections rely on fail closed (WP-30 P1.30,
A109).

The defect (GAPS2 H4e, K5): dash's Content-Security-Policy, its websocket
origin check and its key check ride on Bokeh internals -- the page
template's ``preamble``, ``js_resources`` and ``inner_body`` blocks, the
saved page's ``<head>``, ``bokeh.server.util.match_host`` and
``check_allowlist``, the AuthProvider hook and the session token's
layout.  Measured at the window's commit: a template without
``preamble`` served a page with no policy and raised nothing; a missing
``match_host`` was a bare AttributeError; a ``check_allowlist`` that stopped
calling ``match_host`` kept Bokeh 3.8's lenient matcher; a renamed hook was
ignored, so Gate A admitted everything; ``bokeh serve`` never hardened the
origin check at all (Q-41.1).

Now each refuses with one message naming the internal, the bokeh version
and dash_setup: the server does not start, a served session is refused or
the saved page is not written.  ``_DASH_BOKEH_INTERNALS`` lists them.
"""
import ast
import json
import os
import subprocess
import sys
import tempfile
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import bokeh  # noqa: E402
import bokeh.core.templates  # noqa: E402
import bokeh.embed  # noqa: E402,F401
import bokeh.models  # noqa: E402,F401
import bokeh.plotting  # noqa: E402,F401
import bokeh.resources  # noqa: E402,F401
import bokeh.server.server  # noqa: E402,F401
import bokeh.server.util as bk_util  # noqa: E402
import bokeh.util.token as bk_token  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from bokeh.io import curdoc  # noqa: E402
from bokeh.server.auth_provider import AuthProvider  # noqa: E402
from markupsafe import Markup  # noqa: E402

import dash_render as dr  # noqa: E402
from conftest import load_app, make_data_json, make_spec  # noqa: E402

PROBE = ("localhost.dash-origin-check.invalid:1", ["localhost:1"])
KEY = "dashTestKey_0123456789abcdefghijklmnopqrstuvwxyz"


def _read(rel):
    with open(os.path.join(_ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def _files(labels=None):
    df = pd.DataFrame({"mpg": np.linspace(12.0, 41.0, 12),
                       "weight": np.linspace(1760.0, 4840.0, 12)})
    spec = make_spec([{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}])
    d = tempfile.mkdtemp(prefix="dash_bki_")
    sp, dp = os.path.join(d, "spec.json"), os.path.join(d, "data.json")
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(make_data_json(df, variable_labels=labels), fh)
    return d, sp, dp, spec


@pytest.fixture(scope="module")
def app():
    d, sp, dp, _s = _files()
    op = os.path.join(d, "app.py")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(op)
    return op


#: A Bokeh page template lacking one of the blocks dash overrides.
_WITHOUT = {
    "preamble": "<html><head>{% block js_resources %}{% endblock %}</head>"
                "<body>{% block inner_body %}{% endblock %}</body></html>",
    "inner_body": "<html><head>{% block preamble %}{% endblock %}"
                  "{% block js_resources %}{% endblock %}</head>"
                  "<body></body></html>",
}


def _without(block):
    return bokeh.core.templates.FILE.environment.from_string(_WITHOUT[block])


def _boot(tmp_path, app_path, patch):
    p = tmp_path / "boot.py"
    p.write_text(
        "import os, runpy, sys\n"
        "import bokeh, bokeh.embed, bokeh.resources, bokeh.plotting\n"
        "import bokeh.models, bokeh.server.server, bokeh.core.templates\n"
        "from bokeh.server.auth_provider import AuthProvider\n"
        + patch + "\n"
        "app = %r\n"
        "sys.argv = [app] + sys.argv[1:]\n"
        "sys.path[0] = os.path.dirname(app)\n"
        "runpy.run_path(app, run_name='__main__')\n" % app_path)
    return str(p)


class TestTheTemplateFailsClosed:

    def test_a_template_without_the_blocks_is_refused(self, monkeypatch):
        for block in _WITHOUT:
            monkeypatch.setattr(bokeh.core.templates, "FILE",
                                _without(block))
            with pytest.raises(RuntimeError) as err:
                dr._dash_served_template()
            msg = str(err.value)
            for word in (block, "Content-Security-Policy", bokeh.__version__,
                         "dash_setup"):
                assert word in msg, (block, msg)

    def test_the_probe_page_is_counted(self, monkeypatch):
        dr._dash_check_served_template()
        body = '<script nonce="N">var s = "<script>";</script>'
        assert dr._dash_unsigned_scripts(body, "N") == 0
        assert dr._dash_unsigned_scripts(body + "<script>x()</script>",
                                         "N") == 1
        own = dr._dash_nonce_scripts
        for name, patch in (
                ("unsigned", lambda m, nonce: own(m, nonce).replace(
                    ' nonce="%s"' % nonce, "")),
                ("two policies", lambda m, nonce: own(m, nonce) + Markup(
                    '<meta http-equiv="Content-Security-Policy" '
                    'content="x">'))):
            monkeypatch.setattr(dr, "_dash_nonce_scripts", patch)
            with pytest.raises(RuntimeError) as err:
                dr._dash_check_served_template()
            assert "dash_setup" in str(err.value), name
            monkeypatch.setattr(dr, "_dash_nonce_scripts", own)

    def test_bokeh_serve_refuses_the_session(self, app, monkeypatch):
        monkeypatch.setattr(bokeh.core.templates, "FILE",
                            _without("preamble"))
        try:
            with warnings.catch_warnings():
                with pytest.raises(RuntimeError) as err:
                    load_app(app, "bokeh_app_t")
        finally:
            curdoc().clear()
            sys.modules.pop("_dash_app_notes", None)
        assert "preamble" in str(err.value)
        assert curdoc().roots == []


class TestTheSavedHeadFailsClosed:

    def test_a_page_without_its_policy_is_not_written(self, monkeypatch,
                                                      tmp_path):
        real = bokeh.embed.file_html
        edits = {
            "HEAD": lambda page: page.replace("<head>", "<HEAD>", 1),
            "two policies": lambda page: page.replace(
                "<head>", '<head><meta http-equiv="Content-Security-Policy"'
                ' content="x">', 1)}
        # layout(bs) writes its own <head>, so only Bokeh's head content
        # (a second policy) reaches it.
        for layout, name in (("auto", "HEAD"), ("auto", "two policies"),
                             ("bs", "two policies")):
            edit = edits[name]
            if True:
                monkeypatch.setattr(dr, "file_html",
                                    lambda *a, _e=edit, **k: _e(real(*a, **k)))
                d, sp, dp, spec = _files()
                spec["build_options"]["layout"] = layout
                with open(sp, "w") as fh:
                    json.dump(spec, fh)
                out = tmp_path / ("%s_%s.html" % (layout, name[:3]))
                try:
                    with pytest.raises(dr.DashScriptPolicyError) as err:
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore")
                            dr.main(sp, dp, str(out))
                finally:
                    curdoc().clear()
                assert "Content-Security-Policy" in str(err.value), name
                assert not out.exists(), (layout, name)

    def test_user_text_is_not_counted(self, tmp_path):
        """Guard: a label spelling a policy element is the body's data."""
        _d, sp, dp, _s = _files(labels={
            "mpg": '<meta http-equiv="Content-Security-Policy" content="x">'})
        out = tmp_path / "page.html"
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                dr.main(sp, dp, str(out))
        finally:
            curdoc().clear()
        assert out.exists()


class TestTheOriginCheckFailsClosed:

    def test_a_missing_matcher_is_a_named_error(self, monkeypatch):
        monkeypatch.delattr(bk_util, "match_host")
        with pytest.raises(RuntimeError) as err:
            dr._dash_harden_origin_check()
        assert "match_host" in str(err.value)
        assert "dash_setup" in str(err.value)

    def test_bokeh_serve_hardens_the_origin_check(self, app, monkeypatch):
        """Q-41.1: the bokeh-serve branch hardens too, idempotently."""
        def lenient(host, pattern):
            return host.split(".")[0].split(":")[0] == \
                pattern.split(":")[0]
        monkeypatch.setattr(bk_util, "match_host", lenient)
        assert bk_util.check_allowlist(*PROBE)
        try:
            with warnings.catch_warnings():
                load_app(app, "bokeh_app_o")
                assert not bk_util.check_allowlist(*PROBE)
                load_app(app, "bokeh_app_p")
        finally:
            curdoc().clear()
            sys.modules.pop("_dash_app_notes", None)
        assert not bk_util.check_allowlist(*PROBE)

    def test_a_matcher_the_handler_ignores_is_refused(self, monkeypatch):
        monkeypatch.setattr(bk_util, "match_host", bk_util.match_host)
        monkeypatch.setattr(bk_util, "check_allowlist",
                            lambda host, allow: any(
                                host.startswith(a.split(":")[0])
                                for a in allow))
        with pytest.raises(RuntimeError) as err:
            dr._dash_harden_origin_check()
        assert "dash_setup" in str(err.value)

    def test_the_real_bokeh_passes(self, monkeypatch):
        """Guard: the real Bokeh ends with the probe refused; the return
        value is whether its own matcher was lenient (3.8 True, 3.9
        False)."""
        monkeypatch.setattr(bk_util, "match_host", bk_util.match_host)
        lenient = bk_util.match_host("localhost.dash-origin-check.invalid:1",
                                     "localhost:1")
        assert dr._dash_harden_origin_check() is bool(lenient)
        assert not bk_util.check_allowlist(*PROBE)


class TestTheKeyCheckFailsClosed:

    def test_a_renamed_hook_is_a_named_error(self, monkeypatch):
        monkeypatch.setattr(AuthProvider, "get_user_async",
                            lambda self: None)
        with pytest.raises(RuntimeError) as err:
            dr._dash_token_auth(KEY)
        assert "get_user_async" in str(err.value)
        assert "dash_setup" in str(err.value)

    def test_a_changed_token_layout_is_a_named_error(self, monkeypatch):
        def no_payload(*a, **k):
            raise ImportError("moved")
        for name, value in (("get_token_payload", no_payload),
                            ("generate_jwt_token", lambda *a, **k: "e30.e30.x")):
            with monkeypatch.context() as m:
                m.setattr(bk_token, name, value)
                with pytest.raises(RuntimeError) as err:
                    dr._dash_token_auth(KEY)
            assert "token's layout" in str(err.value), name
        assert dr._dash_check_auth_internals() is None

    @pytest.mark.serve
    def test_the_launcher_stops_with_the_message(self, app, tmp_path):
        """python app.py: a changed template or hook stops the server
        before it listens, exit status 2, one message."""
        from test_server_serves import TEST_TOKEN, _free_port
        patches = {
            "preamble": "bokeh.core.templates.FILE = bokeh.core.templates."
                        "FILE.environment.from_string(%r)"
                        % _WITHOUT["preamble"],
            "get_user_async": "AuthProvider.get_user_async = "
                              "lambda self: None"}
        for word, patch in patches.items():
            p = subprocess.Popen(
                [sys.executable, _boot(tmp_path, app, patch), "--port",
                 str(_free_port())], stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True,
                env=dict(os.environ, DASH_SERVE_TOKEN=TEST_TOKEN))
            try:
                out, err = p.communicate(timeout=60)
            except subprocess.TimeoutExpired:
                p.kill()
                out, err = p.communicate()
            assert p.returncode == 2, (word, p.returncode, err[-2000:])
            assert word in err and "dash_setup" in err, (word, err[-2000:])
            assert "running" not in (out + err).lower(), word


class TestTheInternalsList:

    def test_every_entry_names_a_guard_and_a_test(self):
        entries = dr._DASH_BOKEH_INTERNALS
        assert ast.literal_eval(repr(entries)) == entries
        assert all(isinstance(e, tuple) and len(e) == 3 and
                   all(isinstance(x, str) and x for x in e)
                   for e in entries), entries
        trees = {}
        for _what, guard, test in entries:
            for g in guard.split(","):
                g = g.split("(")[0].strip()
                if g != "browser test":
                    assert callable(getattr(dr, g, None)), g
            path, *names = test.split("::")
            assert os.path.isfile(os.path.join(_ROOT, path)), test
            if path not in trees:
                trees[path] = ast.parse(_read(path))
            scope = trees[path].body
            for n in names:
                hit = [x for x in scope if getattr(x, "name", None) == n]
                assert hit, test
                scope = hit[0].body

    def test_the_app_runs_the_guards(self, app):
        with open(app, encoding="utf-8") as fh:
            src = fh.read()
        launch = src.index("def _dash_server_app(")
        server = src.index("    _dash_srv = Server(", launch)
        assert "    _dash_check_served_template()" in src[launch:server]
        branch = src.index("if __name__ != '__main__':")
        assert src[branch:src.index("make_document(curdoc())", branch)] == (
            "if __name__ != '__main__':\n"
            "    _dash_check_served_template()\n"
            "    _dash_harden_origin_check()\n\n"
            "if __name__ != '__main__':\n    ")
        try:
            mod = load_app(app, "dash_bki_app")
        finally:
            curdoc().clear()
        assert mod._DASH_BOKEH_INTERNALS == dr._DASH_BOKEH_INTERNALS
        assert callable(mod._dash_check_auth_internals)


class TestTheDocuments:

    def test_help_and_changelog_name_what_fails_closed(self):
        help_ = " ".join(_read("dash.sthlp").split())
        assert "page template's blocks" in help_
        assert "refuses to start" in help_
        log = _read("CHANGELOG.md")
        req = log[log.index("### Requirements"):]
        req = req[:req.index("\n### ")]
        sec = log[log.index("### Security"):]
        sec = sec[:sec.index("\n### ")]
        assert "bokeh>=3.8,<3.10" in req and "(WP-30, P1.30)" in req
        assert "refuses to start" in sec and "(WP-30, P1.30)" in sec
