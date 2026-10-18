"""test_accessibility_axe.py -- axe-core reports no WCAG 2.1 A/AA violation
on dashboard pages, saved and served (WP-31 K6, D-54d; the example pages,
DECISIONS A30).

axe-core 4.12.1 is fetched by the test (``axe_fetch``, pinned by SHA-256
and cdnjs's SRI hash) into a scratch directory and handed to headless
Chrome as text over DevTools (``Runtime.evaluate``) once the page has
loaded; no page dash writes names cdnjs or carries axe.  Each page runs
``axe.run(document, {runOnly: wcag2a, wcag2aa, wcag21aa})`` and the test
asserts ``violations == []`` with nothing allow-listed: each violation's
id, impact and first node's html are in the message.

Pages: a scatter with a dropdown filter, a KPI and tabs; a histogram and a
scatter with its data table, a multi filter, a right-to-left range and a
slider -- each saved (``DashRenderer``) and served (``bokeh serve`` through
``test_server_serves._Served``).  ``TestAxeExamples`` runs over the
``examples/*.html`` pages ``make gate`` builds (S61-04 runs it with ``-k
examples``) and skips when none is built.

Release tier; skips without Chrome or the network, red under
``DASH_STRICT=1`` as its siblings are.
"""
import glob
import json
import os
import sys
import time
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import responsive_probe  # noqa: E402

if responsive_probe.find_chrome() is None:
    pytest.skip("headless Chrome is not installed (set DASH_CHROME); "
                "a skip is red under DASH_STRICT=1", allow_module_level=True)

pytestmark = pytest.mark.release

import axe_fetch  # noqa: E402
import dash_render as dr  # noqa: E402
from test_accessibility import SPEC_A, SPEC_B  # noqa: E402
from test_csp_browser import _CspProbe  # noqa: E402
from test_mode_parity import _standalone_page, _write  # noqa: E402
from test_server_serves import _Served  # noqa: E402

_SPECS = {"a": SPEC_A, "b": SPEC_B}

#: Starts axe on the loaded page; the result lands in window.__axe.
_RUN_JS = (
    "window.__axe = null; axe.run(document, {runOnly: {type: 'tag', "
    "values: ['wcag2a', 'wcag2aa', 'wcag21aa']}}).then(r => { "
    "window.__axe = JSON.stringify(r.violations.map(v => ({id: v.id, "
    "impact: v.impact, help: v.help, nodes: v.nodes.length, "
    "html: (v.nodes[0] || {}).html, target: (v.nodes[0] || {}).target}))"
    "); }, e => { window.__axe = JSON.stringify([{id: 'axe-error', "
    "impact: 'error', html: String(e)}]); }); 0")


@pytest.fixture(scope="module")
def axe():
    try:
        return axe_fetch.axe_source()
    except axe_fetch.AxeUnavailable as exc:
        pytest.skip(str(exc))


def _violations(probe, axe_text, timeout=60):
    probe._eval(axe_text + "\n;0")
    probe._eval(_RUN_JS)
    end = time.time() + timeout
    while time.time() < end:
        got = probe._eval("window.__axe")
        if got:
            return json.loads(got)
        time.sleep(0.2)
    raise RuntimeError("axe.run did not finish")


def _say(violations):
    return "\n".join("%(id)s (%(impact)s, %(nodes)s nodes): %(html)s"
                     % dict({"nodes": "?", "html": ""}, **v)
                     for v in violations)


def _url(path):
    return "file://" + os.path.abspath(path)


class TestAxe:

    def test_the_bundle_hash_is_pinned(self, axe):
        axe_fetch.check(axe.encode("utf-8"))
        assert axe_fetch.AXE_URL.startswith(
            "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.12.1/")

    @pytest.mark.parametrize("spec", sorted(_SPECS))
    def test_saved_pages_have_no_violation(self, spec, axe, tmp_path):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _r, _w, page = _standalone_page(_SPECS[spec])
        assert "cdnjs" not in page and "axe" not in page.lower().split(
            "<body")[0]
        path = tmp_path / "page.html"
        path.write_text(page, encoding="utf-8")
        with _CspProbe(_url(str(path))) as p:
            v = _violations(p, axe)
        assert v == [], _say(v)

    @pytest.mark.parametrize("spec", sorted(_SPECS))
    def test_served_pages_have_no_violation(self, spec, axe, tmp_path):
        tag, sp, dp = _write(_SPECS[spec])
        ap = str(tmp_path / "app.py")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(ap)
        with _Served(ap) as srv:
            with _CspProbe(srv.url("/app")) as p:
                v = _violations(p, axe)
        assert v == [], _say(v)


_EXAMPLES = sorted(glob.glob(os.path.join(_ROOT, "examples", "*.html")))


@pytest.mark.skipif(not _EXAMPLES, reason="no examples/*.html built")
class TestAxeExamples:

    @pytest.mark.parametrize(
        "html", _EXAMPLES or ["none"],
        ids=[os.path.basename(p) for p in _EXAMPLES] or ["none"])
    def test_example_pages_have_no_violation(self, html, axe):
        with _CspProbe(_url(html)) as p:
            v = _violations(p, axe)
        assert v == [], _say(v)
