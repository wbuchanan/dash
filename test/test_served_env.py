"""The served app's environment and /health (WP-31 H4).

GAPS3 H4: ``BOKEH_RESOURCES=cdn`` blanked the served page silently (the
page asked a CDN for BokehJS, which the policy does not allow), and
``BOKEH_MINIFIED``/``BOKEH_DEV`` changed the bundle of both pages without a
word; ``/health`` reported only ok and a timestamp.  Section 55 (D-55b,
D-55c): the launcher refuses a resource mode other than server or inline,
exit 2, before any server exists; both renderers say when the bundle is not
the shipped one; ``/health`` adds sessions, the limit, the two versions and
the uptime, and nothing else (DECISIONS A30: no rows).
"""
import json
import os
import re
import subprocess
import sys
import warnings

import pytest
from bokeh.document import Document

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import make_spec  # noqa: E402
from serve_token_probe import TEST_TOKEN  # noqa: E402
from test_adversarial_matrix import (_SCATTER, _app_source,  # noqa: E402
                                     _load_app)
from test_serve_token import _app_cmd, _free_port, _Proc, _status  # noqa: E402

_REFUSAL = ("dash: BOKEH_RESOURCES is set to 'cdn'; this app serves Bokeh "
            "from itself (mode server) and cannot run with another resource "
            "mode. Unset it and start again.")
_FIELDS = {"status", "timestamp", "sessions", "max_sessions", "bokeh",
           "dash", "uptime_s"}


@pytest.fixture(scope="module")
def app_path(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("env_app")
    _app_source(tmp, make_spec([dict(_SCATTER)]))
    return os.path.join(str(tmp), "app.py")


@pytest.fixture(scope="module")
def app_ns(app_path):
    with open(app_path, encoding="utf-8") as fh:
        return _load_app(fh.read(), "env")


def _env(**extra):
    env = {k: v for k, v in os.environ.items()
           if not k.startswith("BOKEH_") and k != "DASH_SERVE_TOKEN"}
    env["DASH_SERVE_TOKEN"] = TEST_TOKEN
    env.update(extra)
    return env


def _dash_ado_version():
    with open(os.path.join(_HERE, "..", "dash.ado"), encoding="utf-8") as fh:
        m = re.search(r"^\*! Version: (\S+)", fh.read(), re.M)
    return m.group(1)


# ===========================================================================
class TestBokehResources:
    def test_cdn_is_refused_with_exit_2(self, app_path):
        r = subprocess.run(_app_cmd(app_path, _free_port()),
                           env=_env(BOKEH_RESOURCES="cdn"),
                           stdin=subprocess.DEVNULL, capture_output=True,
                           text=True, timeout=60)
        out = r.stdout + r.stderr
        assert r.returncode == 2, out
        assert _REFUSAL in out
        assert "preparing the dashboard" not in out

    def test_the_value_is_shown_printable_and_bounded(self, app_path):
        r = subprocess.run(_app_cmd(app_path, _free_port()),
                           env=_env(BOKEH_RESOURCES="x\ty" + "z" * 80),
                           stdin=subprocess.DEVNULL, capture_output=True,
                           text=True, timeout=60)
        out = r.stdout + r.stderr
        assert r.returncode == 2
        shown = re.search(r"is set to '([^']*)'", out).group(1)
        assert len(shown) == 40 and "\t" not in shown

    @pytest.mark.parametrize("mode", ["server", "inline"])
    def test_server_and_inline_pass(self, app_path, mode):
        port = _free_port()
        with _Proc(_app_cmd(app_path, port), env=_env(BOKEH_RESOURCES=mode),
                   port=port) as app:
            assert _status("http://127.0.0.1:%d/health" % port)[0] == 200
        assert "BOKEH_RESOURCES" not in app.said()


# ===========================================================================
class TestBundleNote:
    def test_no_note_for_the_shipped_bundle(self, monkeypatch):
        for k in ("BOKEH_MINIFIED", "BOKEH_DEV"):
            monkeypatch.delenv(k, raising=False)
        assert dr._dash_env_bundle_note() is None
        monkeypatch.setenv("BOKEH_MINIFIED", "yes")
        assert dr._dash_env_bundle_note() is None

    def test_the_two_notes(self, monkeypatch):
        monkeypatch.delenv("BOKEH_DEV", raising=False)
        monkeypatch.setenv("BOKEH_MINIFIED", "no")
        assert dr._dash_env_bundle_note() == (
            "dash: BOKEH_MINIFIED is set, so Bokeh's unminified bundle is "
            "used; the page is larger than the shipped one but behaves the "
            "same")
        monkeypatch.delenv("BOKEH_MINIFIED")
        monkeypatch.setenv("BOKEH_DEV", "yes")
        assert dr._dash_env_bundle_note() == (
            "dash: BOKEH_DEV is set, so Bokeh's development bundle is used; "
            "the page is larger than the shipped one but behaves the same")

    def test_minified_prints_once_saved(self, tmp_path, monkeypatch):
        from test_adversarial_matrix import _write_inputs
        monkeypatch.setenv("BOKEH_MINIFIED", "no")
        sp, dp = _write_inputs(tmp_path, make_spec([dict(_SCATTER)]))
        with warnings.catch_warnings(record=True) as got:
            warnings.simplefilter("always")
            dr.main(sp, dp, str(tmp_path / "p.html"))
        said = [str(w.message) for w in got
                if "BOKEH_MINIFIED is set" in str(w.message)]
        assert len(said) == 1

    def test_dev_prints_once_served(self, app_ns, monkeypatch):
        monkeypatch.setenv("BOKEH_DEV", "yes")
        app_ns["_DASH_STATE"].bundle_noted = False
        with warnings.catch_warnings(record=True) as got:
            warnings.simplefilter("always")
            for _ in range(2):
                app_ns["make_document"](Document())
        said = [str(w.message) for w in got
                if "BOKEH_DEV is set" in str(w.message)]
        assert len(said) == 1


# ===========================================================================
@pytest.fixture(scope="module")
def health(app_path):
    port = _free_port()
    with _Proc(_app_cmd(app_path, port, "--max-sessions", "7"),
               env=_env(), port=port):
        st, body, headers, _ = _status("http://127.0.0.1:%d/health" % port)
    assert st == 200
    return json.loads(body), headers


class TestHealth:
    def test_fields(self, health):
        import bokeh
        got, headers = health
        assert got["status"] == "ok"
        assert re.match(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$", got["timestamp"])
        assert got["sessions"] == 0
        assert got["max_sessions"] == 7
        assert got["bokeh"] == bokeh.__version__
        assert got["dash"] == _dash_ado_version()
        assert isinstance(got["uptime_s"], int) and got["uptime_s"] >= 0
        assert headers["Content-Type"].startswith("application/json")

    def test_no_extra_fields(self, health):
        assert set(health[0]) == _FIELDS
