"""test_accessibility.py -- every figure, filter, KPI card and tab strip is
named for assistive technology, and tabs work from the keyboard, in both
modes (WP-31 K6, section 54).

Before K6 the only ARIA markup was the stale and error status lines: a
figure's host (a ``<canvas>`` and an events layer) had no name, a filter
widget had a ``title`` and no ``aria-label``, a KPI card was a bare
``div``, and the ``Tabs`` headers were ``div tabIndex=0`` with a click
handler only, so Enter and Space did nothing.

Now (D-54a, D-54b, D-54e):

* every figure's host carries ``role="img"`` and an ``aria-label``: the
  graph's title text, else its first layer described (``"scatter of mpg
  versus weight"``) and ``", <n> more layers"``, at most 120 characters
  (``_dash_figure_name``);
* every filter widget (Select, MultiChoice, the sliders and ranges in
  either direction()), the Reset filters button, the data table's toggle
  and the DataTable carry an ``aria-label``; the toggle also says
  ``aria-expanded``;
* every KPI card is ``role="group"`` named by its title;
* the ``Tabs`` host is a named region, and a ``document_ready`` CustomJS
  (``_DASH_TABS_KEYS_JS``) makes its header row a tablist and each header
  a tab moved by Enter, Space, the arrows, Home and End;
* the served recompute cue is ``role="status" aria-live="polite"``;
* the saved error line keeps its ``role="status"`` paragraph (WP-31 H1).

Attributes go on the host (``html_attributes``) only.  The Chrome class is
the release tier and skips without Chrome; a skip is red under
``DASH_STRICT=1``.
"""
import os
import time
import re
import sys
import warnings

import pytest
from bokeh.models import (Button, CustomJS, DataTable, Div, MultiChoice,
                          RangeSlider, Select, Slider, Tabs, Toggle)

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from test_mode_parity import (_kpi, _render_pair, _served, _spec,  # noqa: E402
                              _standalone, _standalone_page)

_SCATTER = {"type": "scatter", "yvar": "mpg", "xvar": "weight",
            "options": {}}
_LFIT = {"type": "lfit", "yvar": "mpg", "xvar": "weight", "options": {}}
_HIST = {"type": "histogram", "var": "mpg", "options": {}}


def _filters(*rows):
    return [dict({"exclude": [], "label": ""}, **r) for r in rows]


#: Page A: a titled scatter and an untitled two-layer graph in two tabs, a
#: dropdown filter and a KPI.
SPEC_A = _spec(
    graphs=[("g1", [_SCATTER], {"title": "Mileage by weight"}),
            ("g2", [_SCATTER, _LFIT], {})],
    kpis=[_kpi("k1", title="Average mileage")],
    build_options={"tabs": "One: g1 / Two: g2",
                   "filters": _filters({"varname": "foreign",
                                        "type": "dropdown"})})

#: Page B: a histogram, a scatter with its data table, a multi filter, a
#: range read right to left and a slider.
SPEC_B = _spec(
    graphs=[("g1", [_HIST], {}), ("g2", [_SCATTER], {"table": "on"})],
    build_options={"filters": _filters(
        {"varname": "rep", "type": "multi"},
        {"varname": "weight", "type": "range", "direction": "rtl"},
        {"varname": "price", "type": "slider"})})


def _saved_models(spec):
    r, _w = _standalone(spec)
    return r, list(r._last_layout_root.references())


def _served_models(spec):
    doc, _w = _served(spec)
    out = []
    for root in doc.roots:
        out.extend(root.references())
    return doc, out


def _both(spec):
    """``{"saved": models, "served": models}`` of *spec*."""
    return {"saved": _saved_models(spec)[1], "served": _served_models(spec)[1]}


def _figures(models):
    return [m for m in models if type(m).__name__ == "figure"]


def _attrs(m):
    return dict(m.html_attributes or {})


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

class TestFigureNames:

    def test_role_img_and_title_name_both_modes(self):
        for mode, models in _both(SPEC_A).items():
            names = sorted(_attrs(f).get("aria-label", "")
                           for f in _figures(models))
            roles = {_attrs(f).get("role") for f in _figures(models)}
            # Flipped: was {"img"}.  A figure built with its own toolbar
            # holds focusable controls (the toolbar's Bokeh logo link), and
            # role="img" makes its children presentational: axe's
            # nested-interactive on six example pages (WP-31 K6 follow-up).
            assert roles == {"group"}, (mode, roles)
            assert names == ["Mileage by weight",
                             "scatter of mpg versus weight, 1 more layer"], (
                mode, names)

    def test_name_from_plots_without_a_title(self):
        assert dr._dash_figure_name({}, [_SCATTER]) == \
            "scatter of mpg versus weight"
        assert dr._dash_figure_name({}, [_SCATTER, _LFIT, _LFIT]) == \
            "scatter of mpg versus weight, 2 more layers"
        assert dr._dash_figure_name(
            {}, [{"type": "rarea", "yvar1": "mpg", "yvar2": "price",
                  "xvar": "weight"}]) == "rarea of mpg price versus weight"
        assert dr._dash_figure_name({}, []) == "graph"
        assert dr._dash_figure_name({}, [{"type": "function"}]) == "function"

    def test_the_title_is_its_plain_text(self):
        go = {"title": '"{bf:First}" "second", size(5)'}
        assert dr._dash_figure_name(go, [_SCATTER]) == "First second"

    def test_capped_at_120(self):
        fig = dr.bokeh_figure()
        dr._dash_name_figure(fig, {"title": "x" * 300}, [_SCATTER])
        name = fig.html_attributes["aria-label"]
        assert len(name) == 120 and name.endswith("..."), name
        # Flipped: was "img" (a figure with a toolbar is a group; above).
        assert fig.html_attributes["role"] == "group"

    def test_a_figure_with_a_toolbar_is_a_group(self):
        """axe nested-interactive (examples/sp500_dates.do and the five
        layout(bs) examples): a figure's own toolbar holds a focusable link,
        and an img's children are presentational, so a figure with a
        toolbar is a named group; one with no toolbar stays a named img."""
        fig = dr.bokeh_figure()
        dr._dash_name_figure(fig, {"title": "T"}, [_SCATTER])
        assert _attrs(fig) == {"role": "group", "aria-label": "T"}
        bare = dr.bokeh_figure(toolbar_location=None)
        dr._dash_name_figure(bare, {"title": "T"}, [_SCATTER])
        assert _attrs(bare) == {"role": "img", "aria-label": "T"}
        empty = dr.bokeh_figure(tools="")
        dr._dash_name_figure(empty, {}, [_SCATTER])
        assert _attrs(empty)["role"] == "img"

    def test_pc_and_univariate_forms(self):
        assert dr._dash_figure_name({}, [_HIST]) == "histogram of mpg"
        pc = {"type": "pcspike", "y1var": "mpg", "x1var": "weight",
              "y2var": "price", "x2var": "rep"}
        assert dr._dash_figure_name({}, [pc]) == \
            "pcspike of mpg weight to price rep"

    def test_a_script_title_stays_text(self):
        """The name is set with setAttribute by BokehJS: the raw text
        reaches the attribute, and markup in it is never parsed."""
        go = {"title": "<script>alert(1)</script>"}
        fig = dr.bokeh_figure()
        dr._dash_name_figure(fig, go, [_SCATTER])
        assert fig.html_attributes["aria-label"] == \
            "<script>alert(1)</script>"

    def test_aria_merges_and_keeps_other_attributes(self):
        d = Div(html_attributes={"role": "note"})
        dr._dash_aria(d, "  two\nlines ", aria_live="polite")
        assert d.html_attributes == {"role": "note", "aria-live": "polite",
                                     "aria-label": "two lines"}
        dr._dash_aria(d, "")
        assert d.html_attributes["aria-label"] == "two lines"


# ---------------------------------------------------------------------------
# Widgets
# ---------------------------------------------------------------------------

class TestWidgetNames:

    def test_every_filter_type_has_an_aria_label(self):
        for spec in (SPEC_A, SPEC_B):
            for mode, models in _both(spec).items():
                ws = [m for m in models if isinstance(
                    m, (Select, MultiChoice, RangeSlider, Slider))]
                assert ws, mode
                for w in ws:
                    assert _attrs(w) == {"role": "group",
                                         "aria-label": w.title}, (
                        mode, type(w).__name__, _attrs(w))
        kinds = {type(m).__name__ for m in _both(SPEC_B)["saved"]}
        assert {"MultiChoice", "RangeSlider", "Slider"} <= kinds, kinds

    def test_every_branch_of_the_builder_names_its_widget(self):
        import pandas as pd
        col = pd.Series([1.0, 2.0, 3.0])
        empty = pd.Series([float("nan")] * 3)
        for ftype, c in (("dropdown", col), ("multi", col), ("slider", col),
                         ("range", col), ("range", empty)):
            w, _s = dr._dash_filter_widget(ftype, "v", c, "{it:Vee}")
            assert w.html_attributes == {"role": "group",
                                         "aria-label": "Vee"}, ftype

    def test_reset_table_toggle_and_table(self):
        for mode, models in _both(SPEC_B).items():
            reset = [m for m in models if isinstance(m, Button)
                     and "dash_filter_reset" in (m.tags or [])]
            assert [_attrs(b) for b in reset] == [
                {"role": "group", "aria-label": "Reset filters"}], mode
            tog = [m for m in models if isinstance(m, Toggle)]
            assert [_attrs(t) for t in tog] == [
                {"role": "group",
                 "aria-label": "Show or hide the data table"}], mode
            dts = [m for m in models if isinstance(m, DataTable)]
            assert [_attrs(t) for t in dts] == [
                {"role": "region",
                 "aria-label": "Data table of scatter of mpg versus weight"}
            ], mode

    def test_the_slider_handles_are_named_once_both_modes(self):
        _r, _w, page = _standalone_page(SPEC_B)
        assert page.count('"name":"dash_slider_names"') == 1
        doc, models = _served_models(SPEC_B)
        hooks = [c for c in doc.callbacks._js_event_callbacks.get(
            "document_ready", []) if c.name == "dash_slider_names"]
        assert len(hooks) == 1
        assert sorted(type(s).__name__ for s in hooks[0].args["sliders"]) \
            == ["RangeSlider", "Slider"]
        assert hooks[0].code == dr._DASH_SLIDER_NAMES_JS
        assert dr._dash_slider_names_hook([]) == []
        assert "dash_slider_names" not in _standalone_page(SPEC_A)[2]

    def test_the_error_line_is_a_status(self):
        assert 'role="status"' in dr._DASH_JS_ERROR_HTML
        assert 'aria-live="polite"' in dr._DASH_JS_ERROR_HTML


# ---------------------------------------------------------------------------
# KPI cards
# ---------------------------------------------------------------------------

def _cards(models):
    return [m for m in models if isinstance(m, Div)
            and "db-kpi-card" in (m.text or "")]


class TestKpiCards:

    def test_role_group_and_name_both_modes(self):
        for mode, models in _both(SPEC_A).items():
            cards = _cards(models)
            assert [_attrs(c) for c in cards] == [
                {"role": "group", "aria-label": "Average mileage"}], mode

    def test_an_untitled_card_is_named_by_its_name(self):
        spec = _spec([_SCATTER], kpis=[_kpi("k9", title="")])
        for mode, models in _both(spec).items():
            assert [_attrs(c) for c in _cards(models)] == [
                {"role": "group", "aria-label": "k9"}], mode

    def test_survives_a_text_rebuild(self):
        """A move rewrites the card's text only, so the attributes stay."""
        _r, models = _saved_models(SPEC_A)
        card = _cards(models)[0]
        card.text = card.text.replace("db-kpi-card", "db-kpi-card x")
        assert _attrs(card) == {"role": "group",
                                "aria-label": "Average mileage"}


# ---------------------------------------------------------------------------
# Tabs, the served cue and the hook
# ---------------------------------------------------------------------------

def _hooks_of(doc):
    return [c for c in doc.callbacks._js_event_callbacks.get(
        "document_ready", []) if getattr(c, "name", "") == "dash_tabs_keys"]


class TestTabsAndHeader:

    def test_tablist_region_and_status(self):
        for mode, models in _both(SPEC_A).items():
            tabs = [m for m in models if isinstance(m, Tabs)]
            assert [_attrs(t) for t in tabs] == [
                {"role": "region", "aria-label": "Dashboard tabs"}], mode
        # The served recompute cue exists only under a live session
        # (_dash_worker_wanted), so its line in the generated app is read.
        import inspect
        tmpl = inspect.getsource(dr.ServerAppBuilder)
        i = tmpl.index("name='dash_updating'")
        assert ("html_attributes={'role': 'status', 'aria-live': 'polite'}"
                in tmpl[i:i + 300])

    def test_the_keys_hook_is_registered_once_both_modes(self):
        _r, _w, page = _standalone_page(SPEC_A)
        assert page.count('"name":"dash_tabs_keys"') == 1, \
            page.count("dash_tabs_keys")
        doc, _models = _served_models(SPEC_A)
        hooks = _hooks_of(doc)
        assert len(hooks) == 1
        assert [t.id for t in hooks[0].args["tabs"]] == [
            m.id for m in _models if isinstance(m, Tabs)]

    def test_no_tabs_no_hook(self):
        assert dr._dash_tabs_keys_hook([]) == []
        doc, _m = _served_models(SPEC_B)
        assert _hooks_of(doc) == []
        _r, _w, page = _standalone_page(SPEC_B)
        assert "dash_tabs_keys" not in page

    def test_the_hook_code_is_fixed_text(self):
        t = Tabs(tabs=[])
        (cb,) = dr._dash_tabs_keys_hook([t])
        assert isinstance(cb, CustomJS)
        assert cb.code == dr._DASH_TABS_KEYS_JS
        assert set(cb.args) == {"tabs"}
        for key in ("'Enter'", "' '", "'ArrowRight'", "'ArrowLeft'",
                    "'Home'", "'End'", "'tablist'", "'tab'",
                    "aria-selected", ".bk-tab", "parentElement"):
            assert key in dr._DASH_TABS_KEYS_JS, key


# ---------------------------------------------------------------------------
# The bundle
# ---------------------------------------------------------------------------

class TestTheBundle:

    def test_the_tab_header_class_exists_in_the_bundle(self):
        """The hook's class name is BokehJS's own (A109 pattern): the Tabs
        view's header class, and the header list it keeps, in the shipped
        bundle (3.8 and 3.9; the header row's own class is 3.9's only, so
        the hook takes the headers' parent)."""
        import bokeh
        path = os.path.join(os.path.dirname(bokeh.__file__), "server",
                            "static", "js", "bokeh.min.js")
        with open(path, encoding="utf-8") as fh:
            js = fh.read()
        assert re.search(r'\btab\s*=\s*"bk-tab"', js), "bk-tab is gone"
        assert "header_els" in js

    def test_the_slider_handle_class_exists_in_the_bundle(self):
        import bokeh
        path = os.path.join(os.path.dirname(bokeh.__file__), "server",
                            "static", "js", "bokeh-widgets.min.js")
        with open(path, encoding="utf-8") as fh:
            js = fh.read()
        # Bokeh's own view queries the handles by this selector, and
        # noUiSlider gives each the slider role.
        assert '".noUi-handle"' in js
        assert '"role","slider"' in js
        rows = [r for r in dr._DASH_BOKEH_INTERNALS
                if r[1].startswith("_dash_slider_names_hook")]
        assert len(rows) == 1
        rows = [r for r in dr._DASH_BOKEH_INTERNALS
                if r[1].startswith("_dash_tabs_keys_hook")]
        assert len(rows) == 1 and rows[0][2].endswith(
            "TestTheBundle::test_the_tab_header_class_exists_in_the_bundle")


# ---------------------------------------------------------------------------
# Parity
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name,spec", [("a11y_a", SPEC_A),
                                       ("a11y_b", SPEC_B)])
def test_both_modes_carry_the_same_attributes(name, spec):
    pair = _render_pair(name, spec)

    def attrs(tree, out):
        if isinstance(tree, tuple) and tree and isinstance(tree[-1], tuple) \
                and tree[-1][:1] == ("attrs",):
            out.append((tree[0], tree[-1][1]))
        if isinstance(tree, (list, tuple)):
            for x in tree:
                attrs(x, out)
        return out
    std = attrs(pair["std"]["tree"], [])
    srv = attrs(pair["srv"]["tree"], [])
    assert std and std == srv, (std, srv)


# ---------------------------------------------------------------------------
# The keys in Chrome (release)
# ---------------------------------------------------------------------------

_TABS_STATE_JS = r"""
(() => {
  const t = __dash_models('Tabs')[0];
  const v = Bokeh.index.find_one(t);
  const hs = Array.from(v.shadow_el.querySelectorAll('.bk-tab'));
  return JSON.stringify({active: t.active,
    focus: hs.indexOf(v.shadow_el.activeElement),
    roles: hs.map(h => h.getAttribute('role')),
    selected: hs.map(h => h.getAttribute('aria-selected')),
    tabindex: hs.map(h => h.tabIndex),
    strip: hs[0].parentElement.getAttribute('role')});
})()
"""

_FOCUS_TAB_JS = (
    "(() => { const t = __dash_models('Tabs')[0]; "
    "const v = Bokeh.index.find_one(t); "
    "v.shadow_el.querySelectorAll('.bk-tab')[%d].focus(); return 0; })()")

_KEYS = {"ArrowRight": 39, "ArrowLeft": 37, "Home": 36, "End": 35,
         "Enter": 13, " ": 32}


@pytest.mark.release
class TestKeyboardInChrome:

    def test_arrow_and_enter_switch_tabs(self, tmp_path):
        import responsive_probe
        if responsive_probe.find_chrome() is None:
            pytest.skip("headless Chrome is not installed (set "
                        "DASH_CHROME); a skip is red under DASH_STRICT=1")
        from test_csp_browser import _CspProbe
        spec = _spec(
            graphs=[("g1", [_SCATTER], {}), ("g2", [_SCATTER], {}),
                    ("g3", [_SCATTER], {})],
            build_options={"tabs": "One: g1 / Two: g2 / Three: g3"})
        _r, _w, page = _standalone_page(spec)
        path = tmp_path / "page.html"
        path.write_text(page, encoding="utf-8")
        with _CspProbe("file://" + str(path)) as p:
            def key(k):
                for typ in ("keyDown", "keyUp"):
                    p._send("Input.dispatchKeyEvent", {
                        "type": typ, "key": k, "windowsVirtualKeyCode":
                        _KEYS[k], "code": "Space" if k == " " else k,
                        **({"text": " "} if k == " " and typ == "keyDown"
                           else {})})
                time.sleep(0.2)
                return p.read(_TABS_STATE_JS)
            st = p.read(_TABS_STATE_JS)
            assert st["roles"] == ["tab"] * 3 and st["strip"] == "tablist"
            assert st["selected"] == ["true", "false", "false"]
            assert st["tabindex"] == [0, -1, -1]
            p._eval(_FOCUS_TAB_JS % 0)
            st = key("ArrowRight")
            assert (st["active"], st["focus"]) == (1, 1), st
            assert st["selected"] == ["false", "true", "false"]
            assert st["tabindex"] == [-1, 0, -1]
            assert key("End")["active"] == 2
            st = key("ArrowRight")
            assert (st["active"], st["focus"]) == (0, 0), st
            assert key("ArrowLeft")["active"] == 2
            assert key("Home")["active"] == 0
            p._eval(_FOCUS_TAB_JS % 2)
            assert key("Enter")["active"] == 2
            p._eval(_FOCUS_TAB_JS % 1)
            assert key(" ")["active"] == 1
            assert p.js_errors() == [], p.js_errors()
