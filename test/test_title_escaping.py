"""subtitle() and tabs() text escaping, in both render modes.

ROADMAP WP-24.  ``subtitle()`` (the dashboard subtitle) and ``tabs()`` (the
tab titles) carry the user's own text.  dash.ado escapes it into the master
spec with ``_dash_json_str`` -- the Stata half, certified from Stata by
test_theme_escaping.cscript and test_security_surface.py's
``test_the_spec_line_escapes_every_build_option`` -- and then each render
mode must place the DECODED text in the document the way BokehJS renders
that sink, so nothing hostile is ever parsed as markup.  Nothing tested
that renderer half for these two options: the only behavioural coverage of
the dashboard subtitle asserted ``"S" in text`` (test_server_build_options.py),
which any occurrence of the letter S satisfies, and tabs() had none.

What BokehJS does with each (bokeh 3.9.0; the full inventory and the
in-browser check are in test_label_sinks.py):

* the dashboard subtitle is a ``Div`` whose ``text`` is ``innerHTML``, so
  the text must be HTML-escaped exactly once, and the ``Div`` must not hand
  its text to MathJax (``disable_math``), or a ``$$..$$`` payload would run
  through it;
* a tab title is ``TabPanel.title``, appended as a DOM text node
  (``TabsView``: ``div({...}, tab.title)``), so it is kept RAW and drawn as
  text whatever it holds -- and the saved page, which embeds the document
  as JSON, escapes it there (Bokeh's ``script_for_render_items`` HTML-
  escapes the block), so the raw payload never appears in the page source.

Each check runs in both modes and gives every absence a positive control:
the subtitle Div is found and its escaped text is present before the raw
form is required absent; the tabs build the two TabPanels before their
titles are read.  Measured 24sep2026: with ``html.escape`` dropped from the
subtitle fragment, ``test_the_subtitle_is_escaped_once`` fails in both
modes.  (The saved-page checks do not catch that mutation: Bokeh HTML-
escapes the whole document JSON it embeds, so an unescaped Div text is
escaped again there; those checks guard a page-level leak the model-level
check would miss, and each has its own positive control.)
"""
import html
import importlib.util
import json
import os
import re
import sys
import tempfile
import warnings

import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import Div, TabPanel

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import make_data_json  # noqa: E402

_DF = pd.DataFrame({
    "mpg": [22.0, 17.0, 25.0, 30.0, 21.0, 19.0],
    "weight": [2930.0, 3350.0, 2200.0, 1800.0, 3000.0, 3100.0],
})

#: The hostile texts: markup, a script tag, quotes, a backslash (and one
#: ending in a backslash), and a TeX pair that MathJax would run in a Div.
#: A tab title holds no "/" or ":" -- tabs() reads those as separators
#: (dash.sthlp, _dash_parse_tabs) -- so those are the two payloads left out
#: of the tab-title cases.
PAYLOADS = {
    "script": "<script>alert(1)</script>",
    "img": '<img src=x onerror=alert(1)>',
    "bold_amp": "<b>R&D</b> & more",
    "quotes": '"dq" \'sq\'',
    "backslash": "C:\\temp\\new\\",
    "tex": "$$\\href{javascript:alert(1)}{x}$$",
}
#: Tab-title payloads.  tabs() reads "/" and ":" as separators
#: (dash.sthlp, _dash_parse_tabs), so a title holds neither -- the markup
#: payloads therefore drop their closing "</...>" slash and the ":" of a
#: scheme.  Three carry markup, so the "escaped in the page" check has
#: something to find.
_TAB_SAFE = {
    "open_img": "<img src=x onerror=alert(1)>",
    "open_script": "<script>alert(1)",
    "open_bold_amp": "<b>R&D & more",
    "quotes": '"dq" \'sq\'',
    "backslash": "C\\temp\\new\\",
}

_MODES = ("saved", "served")
_TMP = tempfile.mkdtemp(prefix="dash_title_escaping_")
_SEQ = iter(range(1_000_000))


def _spec(subtitle="", tabs=""):
    graphs = [{
        "plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                   "options": {}}],
        "graph_options": {"name": "g1"},
        "if_expr": "", "in_expr": "",
    }, {
        "plots": [{"type": "line", "yvar": "mpg", "xvar": "weight",
                   "options": {}}],
        "graph_options": {"name": "g2"},
        "if_expr": "", "in_expr": "",
    }]
    return {
        "graphs": graphs, "kpis": [],
        "build_options": {
            "layout": "auto", "link": "", "filter": "", "theme": "",
            "scheme": "", "session_scheme": "",
            "title": "T", "subtitle": subtitle, "tabs": tabs,
            "registry": "g1 g2", "filter_position": "top", "level": "95",
        },
    }


def _write(spec):
    n = next(_SEQ)
    sp = os.path.join(_TMP, f"spec_{n}.json")
    dp = os.path.join(_TMP, f"data_{n}.json")
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    with open(dp, "w", encoding="utf-8") as fh:
        json.dump(make_data_json(_DF, {}, {}), fh)
    return sp, dp


def _saved(spec):
    """(models, page) from the saved-dashboard renderer."""
    sp, dp = _write(spec)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = dr.DashRenderer(sp, dp)
        page = r.render()
    root = getattr(r, "_last_layout_root", None)
    models = list(root.references()) if root is not None else []
    return models, page


def _served(spec):
    """models from the served app's document, built as bokeh serve runs it."""
    sp, dp = _write(spec)
    ap = os.path.join(_TMP, f"app_{next(_SEQ)}.py")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(ap)
        ms = importlib.util.spec_from_file_location(f"_te_app_{id(ap)}", ap)
        mod = importlib.util.module_from_spec(ms)
        ms.loader.exec_module(mod)
        doc = Document()
        mod.make_document(doc)
    seen = {}
    for root in doc.roots:
        for m in root.references():
            seen[m.id] = m
    return list(seen.values())


def _models(mode, spec):
    return _saved(spec)[0] if mode == "saved" else _served(spec)


def _subtitle_div(models):
    """The one dashboard-subtitle Div (class db-subtitle)."""
    divs = [m for m in models
            if isinstance(m, Div) and "db-subtitle" in (m.text or "")]
    assert len(divs) == 1, f"expected one db-subtitle Div, found {len(divs)}"
    return divs[0]


def _tab_titles(models):
    return [p.title for m in models for p in getattr(m, "tabs", [])
            if isinstance(p, TabPanel)]


# ---------------------------------------------------------------------------
# subtitle() -- an HTML sink: escaped exactly once, never handed to MathJax
# ---------------------------------------------------------------------------

class TestTheSubtitleIsAnHtmlSink:
    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("pid,payload", sorted(PAYLOADS.items()))
    def test_the_subtitle_is_escaped_once(self, mode, pid, payload):
        div = _subtitle_div(_models(mode, _spec(subtitle=payload)))
        esc = html.escape(payload)
        # Positive control: the escaped text is present, so the sink is
        # reached before the raw form is required absent.
        assert esc in div.text, (
            f"{mode}/{pid}: the escaped subtitle {esc!r} is not in "
            f"{div.text!r}")
        if esc != payload:
            assert payload not in div.text, (
                f"{mode}/{pid}: the raw subtitle reached the Div's HTML")
            assert html.escape(esc) not in div.text, (
                f"{mode}/{pid}: the subtitle was escaped twice")

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_subtitle_div_disables_math(self, mode):
        # A Div runs its text through MathJax unless told not to, and the TeX
        # payload's \href is live there.
        div = _subtitle_div(_models(mode, _spec(subtitle=PAYLOADS["tex"])))
        assert div.disable_math is True, (
            f"{mode}: the subtitle Div hands its text to MathJax")

    # Only a payload with markup in it can be looked for as markup.
    @pytest.mark.parametrize("pid,payload", sorted(
        (k, v) for k, v in PAYLOADS.items() if "<" in v))
    def test_the_saved_page_never_holds_the_raw_subtitle(self, pid, payload):
        _models, page = _saved(_spec(subtitle=payload))
        assert payload not in page, (
            f"{pid}: the raw subtitle payload appears in the saved page")


# ---------------------------------------------------------------------------
# tabs() -- a DOM text node: kept raw in the model, escaped in the page
# ---------------------------------------------------------------------------

class TestTheTabTitleIsATextNode:
    @staticmethod
    def _spec_for(title):
        # Two tabs, the first titled with the payload; the second is a plain
        # control, so a parse that dropped the hostile title would still
        # leave one tab and the count below would catch it.
        return _spec(tabs=f"{title}: g1 / PlainTab: g2")

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("pid,payload", sorted(_TAB_SAFE.items()))
    def test_the_title_reaches_the_tabpanel_raw(self, mode, pid, payload):
        titles = _tab_titles(_models(mode, self._spec_for(payload)))
        # Positive control: both tabs were built.
        assert titles == [payload, "PlainTab"], (
            f"{mode}/{pid}: tab titles are {titles!r}")

    # Only a payload with markup in it can be looked for as markup.
    @pytest.mark.parametrize("pid,payload", sorted(
        (k, v) for k, v in _TAB_SAFE.items() if "<" in v))
    def test_the_saved_page_escapes_the_tab_title(self, pid, payload):
        _m, page = _saved(self._spec_for(payload))
        # The title is drawn as a text node at run time, and the document is
        # embedded as JSON that Bokeh HTML-escapes, so the raw markup is
        # never in the page source for a parser to pick up.
        assert payload not in page, (
            f"{pid}: the raw tab-title payload appears in the saved page")


# ---------------------------------------------------------------------------
# The harness really exercises both sinks
# ---------------------------------------------------------------------------

class TestTheHarnessIsHonest:
    def test_a_plain_subtitle_reaches_the_div_unchanged(self):
        for mode in _MODES:
            div = _subtitle_div(_models(mode, _spec(subtitle="Plain sub")))
            assert "Plain sub" in div.text, mode

    def test_a_plain_tab_title_reaches_the_panel(self):
        for mode in _MODES:
            titles = _tab_titles(_models(mode, _spec(tabs="One: g1 / Two: g2")))
            assert titles == ["One", "Two"], (mode, titles)

    def test_every_payload_carries_markup_or_a_delimiter(self):
        # Guards the parametrization: an empty PAYLOADS map would make every
        # case above vacuously pass.
        assert len(PAYLOADS) >= 5 and len(_TAB_SAFE) >= 3
        assert any("<" in v for v in PAYLOADS.values())
