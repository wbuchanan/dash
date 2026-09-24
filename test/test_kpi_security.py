"""test_kpi_security.py — S13 defect 7: KPI colour injection on the initial render.

``dash kpi ..., color()`` and ``bgcolor()`` are embedded directly into an inline
``style="..."`` attribute by ``_make_kpi_div``.  That path applies
``html.escape`` and nothing else.

``html.escape`` is the wrong tool here.  It neutralises ``<``, ``>``, ``&`` and
the quote characters, so it does block an attribute breakout — but a CSS
*property* injection needs none of those.  ``;`` and ``(`` ``)`` pass through
untouched, so a value like::

    red; background:url(http://evil.example/x.png)

lands inside the style attribute as two CSS declarations, and the browser
honours the second one.  On a dashboard that is emailed or hosted, that is an
outbound request carrying the referrer, and ``}`` closes the rule entirely and
lets a fresh selector through.

The project already has the right tool — ``_sanitize_css_color`` — and the JS
filter-callback path calls it.  Only the initial render does not, so a KPI is
safe once you touch a filter and unsafe before you do.

Measured before the fix: all four payloads below reached the HTML verbatim,
while ``_sanitize_css_color`` would have reduced every one of them to the
default.

The default is the scheme's ``color text`` -- ``SchemeParser.text_color``,
#000000 under s2color, #ffffff under s1rcolor -- because the KPI card is
Stata's legend box (WP-16).  It used to be dash's own literal ``#212529``,
and this file pinned that literal in seven places, so it went red the day
the default moved without a single injection having got through.  Every
default here is now read from the renderer's scheme, and the value div's
colour is read on its own: the title and subtitle divs carry the scheme's
text colour too, so a substring test over the whole card cannot tell the
value's colour from theirs once the value's default IS that colour.

Written before the fix, per project rule 8; the adversarial cases are project
rule 18.
"""
import functools
import json
import os
import re
import sys
import tempfile
from html.parser import HTMLParser

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render
from dash_render import DashRenderer, _sanitize_css_color

from conftest import make_spec, make_data_json


def _df():
    return pd.DataFrame({
        "mpg": np.linspace(12.0, 41.0, 10),
        "weight": np.linspace(1760.0, 4840.0, 10),
    })


_PLOTS = [{"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}]


def _render_kpi(scheme=None, **kpi_extra):
    """Render a dashboard with one KPI carrying the given fields, under
    *scheme* when given (the default scheme otherwise)."""
    spec = make_spec(_PLOTS)
    if scheme:
        spec["build_options"]["scheme"] = scheme
    kpi = {"name": "k1", "stat": "mean", "var": "mpg",
           "title": "T", "fmt": "%9.1f"}
    kpi.update(kpi_extra)
    spec["kpis"] = [kpi]
    sp = tempfile.mkstemp(".json")[1]
    dp = tempfile.mkstemp(".json")[1]
    op = tempfile.mkstemp(".html")[1]
    with open(sp, "w") as f:
        json.dump(spec, f)
    with open(dp, "w") as f:
        json.dump(make_data_json(_df()), f)
    dr = DashRenderer(sp, dp, op)
    out = dr.render()
    for p in (sp, dp, op):
        try:
            os.unlink(p)
        except OSError:
            pass
    return out, dr


def _kpi_div_text(dr):
    return "\n".join(getattr(v, "text", "") for v in dr.kpi_divs.values())


_VALUE_DIV = re.compile(r'id="kpi_val_[^"]*"\s+style="([^"]*)"', re.S)


def _kpi_value_color(dr):
    """The colour declared on the VALUE div alone (see the module
    docstring: the title and subtitle divs carry the scheme's text colour
    as well)."""
    text = _kpi_div_text(dr)
    m = _VALUE_DIV.search(text)
    assert m, f"no kpi_val_ div in the card: {text[:300]}"
    mc = re.search(r"(?:^|[;\s])color\s*:\s*([^;\"]+)", m.group(1))
    return mc.group(1).strip() if mc else None


class _CardTags(HTMLParser):
    """The card's start tags, PARSED: [(tag, [(attribute, value), ...])].

    Parsed rather than searched, so a payload that broke out of
    style="..." is seen as the attribute it became (onload=...), and a
    declaration smuggled into a colour is seen as a declaration.  A
    substring test over the page cannot see either: two of the payloads
    below carry none of its needles, and the colours go into the style
    attribute unescaped (_dash_kpi_card_html interpolates the sanitiser's
    verdict, not html.escape's), so the sanitiser is the only guard."""

    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.feed(text or "")
        self.close()

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, attrs))


def _declarations(attrs):
    """[(property, value)] of an element's style attribute, split on ';'."""
    style = dict(attrs).get("style") or ""
    out = []
    for decl in style.split(";"):
        if decl.strip():
            prop, _, val = decl.partition(":")
            out.append((prop.strip().lower(), val.strip()))
    return out


# A colour and nothing else: hex, a word, or rgb()/hsl() of numbers.  The
# test's own grammar, so a sanitiser that regressed is not also the judge.
_ONLY_A_COLOUR = re.compile(
    r"#[0-9a-fA-F]{3,8}|[A-Za-z]{2,30}"
    r"|(?:rgb|rgba|hsl|hsla)\(\s*[0-9.]+%?(?:\s*,\s*[0-9.]+%?){2,3}\s*\)")


@functools.lru_cache(maxsize=None)
def _honest_card_tags():
    """The shape of a card whose color() and bgcolor() are honest."""
    _, dr = _render_kpi(color="red", bgcolor="blue")
    return tuple((t, tuple(a)) for t, a in _CardTags(_kpi_div_text(dr)).tags)


def _assert_card_is_inert(dr, what):
    """A hostile colour left the card the shape an honest one has: the same
    elements, no attribute and no CSS property beyond theirs (none twice),
    and nothing but a colour in a color or background declaration."""
    want = _honest_card_tags()
    got = _CardTags(_kpi_div_text(dr)).tags
    assert [t for t, _ in got] == [t for t, _ in want], (
        f"{what}: the card's elements changed: {got}")
    for (tag, attrs), (_, ref) in zip(got, want):
        names = [a for a, _ in attrs]
        assert (set(names) <= {a for a, _ in ref}
                and len(names) == len(set(names))), (
            f"{what}: a <{tag}> gained an attribute: {attrs}")
        decls = _declarations(attrs)
        props = [p for p, _ in decls]
        assert (set(props) <= {p for p, _ in _declarations(ref)}
                and len(props) == len(set(props))), (
            f"{what}: a <{tag}>'s style gained a declaration: {decls}")
        for prop, val in decls:
            if prop in ("color", "background"):
                assert _ONLY_A_COLOUR.fullmatch(val), (
                    f"{what}: {prop}:{val!r} is not a colour")


# ======================================================================
# The injection itself
# ======================================================================

_CSS_PAYLOADS = [
    # A second CSS declaration: the browser honours it, and the url() is an
    # outbound request from whoever opens the dashboard.
    "red; background:url(http://evil.example/x.png)",
    # Closing the rule and opening a fresh selector.
    "red;} body{display:none",
    # Legacy dynamic-property vector.
    "expression(alert(1))",
    # Attribute breakout; html.escape does stop this one, which is exactly why
    # escaping looked sufficient.
    '#fff" onload="alert(1)',
    # Comment-smuggled property.
    "red;/**/background:url(http://evil.example/y)",
    # Unicode-escaped semicolon, to defeat a naive character blacklist.
    "red\\3b background:red",
]


class TestKpiColourIsSanitisedOnTheInitialRender:

    @pytest.mark.parametrize("payload", _CSS_PAYLOADS)
    def test_color_payload_does_not_reach_the_document(self, payload):
        out, dr = _render_kpi(color=payload)
        assert "evil.example" not in out, (
            f"color({payload!r}) reached the document and can make an "
            f"outbound request"
        )
        assert "expression(" not in out
        assert "body{display:none" not in out
        # The attribute breakout and the escaped semicolon hold none of the
        # three needles, so for them only the card's parsed markup can fail.
        _assert_card_is_inert(dr, f"color({payload!r})")

    @pytest.mark.parametrize("payload", _CSS_PAYLOADS)
    def test_bgcolor_payload_does_not_reach_the_document(self, payload):
        out, dr = _render_kpi(bgcolor=payload)
        assert "evil.example" not in out
        assert "expression(" not in out
        assert "body{display:none" not in out
        # bgcolor() has no sanitiser-agreement test of its own, and nothing
        # html-escapes it on its way into style="...": measured 24sep2026,
        # with the sanitiser bypassed '#fff" onload="alert(1)' became an
        # onload attribute of the card and this test still passed.
        _assert_card_is_inert(dr, f"bgcolor({payload!r})")

    @pytest.mark.parametrize("payload", _CSS_PAYLOADS)
    def test_the_rendered_value_is_what_the_sanitiser_would_give(self,
                                                                 payload):
        """The two paths must agree, or a KPI is safe only after filtering.

        The fallback is the scheme's text colour, the same default the
        renderer hands ``_resolve_kpi_color``."""
        _, dr = _render_kpi(color=payload)
        expected = _sanitize_css_color(payload, dr.scheme.text_color)
        text = _kpi_div_text(dr)
        assert f"color:{expected}" in text, (
            f"the initial render did not use the sanitised colour "
            f"{expected!r}; div text was: {text[:300]}"
        )
        assert _kpi_value_color(dr) == expected, (
            f"the value div's colour is {_kpi_value_color(dr)!r}, the "
            f"sanitiser gives {expected!r}"
        )

    def test_a_semicolon_can_never_appear_inside_a_style_attribute_value(self):
        """The general property, not one payload at a time.

        This searched each colour's value for "url(" and "expression(" with
        a capture that stopped at the first ';' -- neither payload holds
        either word, and the injected declaration lies past the ';', so it
        could not fail (measured 24sep2026: it passed with both colours
        written into the card raw).  The card is parsed instead: a
        semicolon that got through is a declaration the honest card does
        not have (background on the value div, content on the card)."""
        _, dr = _render_kpi(color="red; background:red",
                            bgcolor="blue; content:'x'")
        _assert_card_is_inert(dr, "color(red; background:red) "
                                  "bgcolor(blue; content:'x')")


class TestLegitimateColoursStillWork:
    """A security fix that breaks the feature is not a fix."""

    @pytest.mark.parametrize("good,expect", [
        # A hex value passes through; a NAME is translated through Stata's
        # colour table, so red is Stata's red and navy is Stata's navy
        # (#1a476f) rather than CSS navy (#000080). That translation is the
        # point -- these are Stata colour names, not CSS ones.
        ("#ff0000", "#ff0000"),
        ("#FFF", "#fff"),
        ("red", "#ff0000"),
        ("navy", "#1a476f"),
        # Stata's eltblue, from style/color-eltblue.style rgb "130 192 233".
        # This asserted #b7c9e2, which is not a colour Stata has.
        ("eltblue", "#82c0e9"),
        ("rebeccapurple", "rebeccapurple"),
        ("rgb(1,2,3)", "rgb(1,2,3)"),
    ])
    def test_a_valid_colour_survives(self, good, expect):
        _, dr = _render_kpi(color=good)
        assert f"color:{expect}" in _kpi_div_text(dr), (
            f"color({good}) rendered as something other than {expect}: "
            f"{_kpi_div_text(dr)[:200]}"
        )

    @pytest.mark.parametrize("good", ["gs10", "red%50", "eltblue"])
    def test_a_stata_only_colour_is_not_flattened_to_the_default(self, good):
        """Sanitising WITHOUT translating first turned these into grey, and
        the JS path then disagreed with the initial render."""
        _, dr = _render_kpi(color=good)
        got = _kpi_value_color(dr)
        assert got is not None and got != dr.scheme.text_color, (
            f"color({good}) is a legitimate Stata colour and was replaced by "
            f"the default {dr.scheme.text_color}"
        )
        assert "#212529" not in _kpi_div_text(dr), (
            "the pre-WP-16 literal default is back"
        )

    def test_a_stata_colour_name_is_translated_or_defaulted(self):
        """eltblue is a Stata name, not a CSS one.

        Either is defensible -- translate it, or fall back to the default --
        but it must never reach the document unrecognised.
        """
        _, dr = _render_kpi(color="eltblue")
        text = _kpi_div_text(dr)
        assert "color:eltblue" not in text, (
            "a Stata colour name reached the stylesheet untranslated"
        )

    def test_no_colour_given_uses_the_schemes_text_colour(self):
        """The default is the scheme's ``color text``, not a literal of
        dash's own (WP-16: the card is Stata's legend box)."""
        _, dr = _render_kpi()
        assert _kpi_value_color(dr) == dr.scheme.text_color
        assert "#212529" not in _kpi_div_text(dr)

    @pytest.mark.parametrize("scheme", ["s2color", "s1rcolor"])
    def test_the_default_follows_the_scheme(self, scheme):
        """s1rcolor's text is white on a black page; a fixed literal could
        not follow it.  Read from the renderer's parsed scheme, not from a
        table of this file's own."""
        _, dr = _render_kpi(scheme=scheme)
        assert _kpi_value_color(dr) == dr.scheme.text_color

    def test_the_two_schemes_defaults_really_differ(self):
        """Guards the test above: if both schemes' text colours were the
        same, following the scheme could not be told from a literal."""
        _, black = _render_kpi(scheme="s2color")
        _, white = _render_kpi(scheme="s1rcolor")
        assert _kpi_value_color(black) != _kpi_value_color(white)


class TestBothPathsAgree:
    """The JS callback sanitises; the initial render must match it."""

    def test_the_callback_config_and_the_div_use_the_same_colour(self):
        payload = "red; background:url(http://evil.example/x.png)"
        spec = make_spec(_PLOTS)
        spec["kpis"] = [{"name": "k1", "stat": "mean", "var": "mpg",
                         "title": "T", "fmt": "%9.1f", "color": payload}]
        spec["build_options"]["filters"] = [
            {"varname": "weight", "type": "range", "exclude": [], "label": ""}]
        sp = tempfile.mkstemp(".json")[1]
        dp = tempfile.mkstemp(".json")[1]
        op = tempfile.mkstemp(".html")[1]
        with open(sp, "w") as f:
            json.dump(spec, f)
        with open(dp, "w") as f:
            json.dump(make_data_json(_df()), f)
        dr = DashRenderer(sp, dp, op)
        dr.render()
        for p in (sp, dp, op):
            try:
                os.unlink(p)
            except OSError:
                pass
        assert dr.filter_callbacks, "no filter callback was built"
        cfg = json.loads(dr.filter_callbacks[0].args["kpi_config_json"])
        assert cfg, "the KPI did not reach the callback"
        js_colour = cfg[0]["color"]
        assert "evil.example" not in js_colour
        assert f"color:{js_colour}" in _kpi_div_text(dr), (
            f"the callback would set {js_colour!r} but the initial render "
            f"used something else -- the KPI changes colour on first filter"
        )
        assert _kpi_value_color(dr) == js_colour, (
            f"the value div is {_kpi_value_color(dr)!r}, the callback would "
            f"set {js_colour!r}"
        )


# ======================================================================
# WP-20: a KPI's text is never markup or maths, in either mode, before or
# after a filter moves
# ======================================================================
# The card is HTML (a Bokeh Div), so its title, subtitle and name are
# html-escaped by the one builder every path uses, _dash_kpi_card_html, and
# the Div sets disable_math: a Div otherwise runs its text through MathJax,
# where $$\href{javascript:...}{x}$$ is a live link (BUGS.md, WP-20).  The
# card is also rebuilt after the first render -- by the saved page's
# CustomJS, from the config it is handed, and by the served app's recompute,
# through the same builder -- so each mode is checked after a filter moves
# too.  The colour defect this file was written for was safe on one path and
# not on the other.

import html as _html  # noqa: E402
import warnings  # noqa: E402

from bokeh.document import Document  # noqa: E402
from bokeh.models import Div, Select  # noqa: E402

_KPI_TEXT_PAYLOADS = [
    '<img src=x onerror="document.title=1">',
    "<script>document.title=2</script>",
    r"$$\href{javascript:document.title=3}{click}$$",
    r"\(x\)<img src=x onerror=4>",
]

_FDF = pd.DataFrame({
    "mpg": [22.0, 17.0, 25.0, 30.0, 21.0, 19.0, 14.0, 28.0, 16.0, 23.0],
    "weight": [2930.0, 3350.0, 2200.0, 1800.0, 3000.0, 3100.0, 4080.0,
               2010.0, 3600.0, 2650.0],
    "foreign": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
})
# The mean of mpg over the foreign == 1 rows, as the card formats it.
_FOREIGN_MEAN = f"{_FDF.loc[_FDF.foreign == 1, 'mpg'].mean():.1f}"
_CURDOC_ATTACH = "if __name__ != '__main__':\n    make_document(curdoc())"


def _tags(text):
    """The tag names in *text*.  A card has its own divs and nothing else."""
    return {t.lower() for t in
            re.findall(r"<\s*/?\s*([A-Za-z][A-Za-z0-9]*)", text or "")}


def _kpi_spec(**kpi_extra):
    kpi = {"name": "k1", "stat": "mean", "var": "mpg", "title": "T",
           "subtitle": "", "fmt": "%9.1f", "color": "", "bgcolor": "",
           "update": "both", "if_expr": "", "in_expr": ""}
    kpi.update(kpi_extra)
    return make_spec(_PLOTS, filters=[{"varname": "foreign",
                                       "type": "dropdown"}], kpis=[kpi])


def _inputs(tmp_path, spec):
    sp = os.path.join(str(tmp_path), "spec.json")
    dp = os.path.join(str(tmp_path), "data.json")
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    with open(dp, "w", encoding="utf-8") as fh:
        json.dump(make_data_json(_FDF), fh)
    return sp, dp


def _saved(tmp_path, spec):
    sp, dp = _inputs(tmp_path, spec)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = DashRenderer(sp, dp)
        r.render()
    return r


def _served_doc(tmp_path, spec):
    """A session of the generated app: (document, the app's namespace)."""
    sp, dp = _inputs(tmp_path, spec)
    op = os.path.join(str(tmp_path), "app.py")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dash_render.ServerAppBuilder(sp, dp).build(op)
        with open(op, encoding="utf-8") as fh:
            src = fh.read()
        assert _CURDOC_ATTACH in src, "the generated app's curdoc attach moved"
        ns = {"__name__": "kpi_security_app"}
        exec(compile(src.replace(_CURDOC_ATTACH, "pass"), op, "exec"), ns)
        doc = Document()
        ns["make_document"](doc)
    return doc


def _cards(doc):
    return [d for d in doc.select({"type": Div})
            if "db-kpi-card" in (d.text or "")]


def _pick_foreign_one(doc):
    """Move the served dropdown to foreign == 1 and run its recompute, as a
    browser's change would (unwrapped from the event throttle)."""
    sel = next(iter(doc.select({"type": Select})))
    value = None
    for opt in sel.options:
        v, label = (opt if isinstance(opt, (list, tuple)) else (opt, opt))
        if str(label).strip() in ("1", "1.0") or str(v).strip() in ("1", "1.0"):
            value = v
    assert value is not None, f"no foreign == 1 option in {sel.options}"
    cbs = sel._callbacks.get("value", [])
    assert cbs, "the served dropdown has no recompute callback"
    old = sel.value
    sel.value = value
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cbs[0]("value", old, value)


class TestKpiTextIsNeverMarkupOrMaths:

    def test_the_detector_sees_a_tag_that_is_not_the_cards(self):
        assert _tags('<div a="1"><IMG src=x></div>') == {"div", "img"}
        assert _tags("&lt;img src=x&gt;") == set()

    @pytest.mark.parametrize("field", ["title", "subtitle"])
    @pytest.mark.parametrize("payload", _KPI_TEXT_PAYLOADS)
    def test_the_saved_card_and_its_rebuild(self, tmp_path, field, payload):
        r = _saved(tmp_path, _kpi_spec(**{field: payload}))
        assert r.kpi_divs, "no KPI card was built"
        for div in r.kpi_divs.values():
            assert div.disable_math is True, "the card is read as maths"
            assert _tags(div.text) == {"div"}, div.text
            assert _html.escape(payload) in div.text
        # The saved page rebuilds the card in the browser from this config,
        # with no escaping of its own: it must arrive escaped.
        assert r.filter_callbacks, "no filter callback was built"
        cfg = json.loads(r.filter_callbacks[0].args["kpi_config_json"])
        assert cfg and cfg[0][field] == _html.escape(payload), cfg

    @pytest.mark.parametrize("field", ["title", "subtitle"])
    @pytest.mark.parametrize("payload", _KPI_TEXT_PAYLOADS)
    def test_the_served_card_before_and_after_a_filter_moves(
            self, tmp_path, field, payload):
        doc = _served_doc(tmp_path, _kpi_spec(**{field: payload}))
        cards = _cards(doc)
        assert cards, "no KPI card in the served document"
        _pick_foreign_one(doc)
        after = _cards(doc)
        assert _FOREIGN_MEAN in " ".join(d.text for d in after), (
            "the recompute did not run, so the check after it would be "
            "vacuous")
        for div in cards + after:
            assert div.disable_math is True, "the card is read as maths"
            assert _tags(div.text) == {"div"}, div.text
            assert _html.escape(payload) in div.text

    def test_a_hostile_name_stays_inside_its_attribute(self, tmp_path):
        """A hand-written spec's KPI name goes into the value div's id."""
        name = 'k1"><img src=x onerror=5>'
        r = _saved(tmp_path, _kpi_spec(name=name))
        text = "\n".join(d.text for d in r.kpi_divs.values())
        assert _tags(text) == {"div"}, text
        # The name did reach the card -- in the value div's id, escaped --
        # or the check above would be about a card that dropped it.
        assert f'id="kpi_val_{_html.escape(name)}"' in text, text
        cfg = json.loads(r.filter_callbacks[0].args["kpi_config_json"])
        assert cfg[0]["name_html"] == _html.escape(name)
        doc = _served_doc(tmp_path, _kpi_spec(name=name))
        _pick_foreign_one(doc)
        # A served app that drew no card for this name passed the loop
        # below with nothing in it; the card must be there, rebuilt by the
        # recompute (its value is the foreign == 1 mean), holding the name.
        cards = _cards(doc)
        assert cards, "no KPI card in the served document"
        served = " ".join(d.text for d in cards)
        assert _FOREIGN_MEAN in served, "the recompute did not run"
        assert f'id="kpi_val_{_html.escape(name)}"' in served, served
        for div in cards:
            assert _tags(div.text) == {"div"}, div.text


class TestAKpiFormatCannotBuildAHugeCard:
    """dash.ado checks fmt() with `confirm numeric format'; a hand-edited
    spec is held by the renderer to Stata's own bounds (width 1 to 2,045,
    fewer decimals than the width).  Measured before WP-20: a fmt of
    %9.999999999f made a 1,000,000,001-character card."""

    @pytest.mark.parametrize("fmt", ["%9.999999999f", "%2046.2f",
                                     "%99999999999.1f", "%9.30fc"])
    def test_both_modes_before_and_after_a_filter_moves(self, tmp_path, fmt):
        r = _saved(tmp_path, _kpi_spec(fmt=fmt))
        # The card is held to the bounds, not dropped: an empty kpi_divs
        # made the all() below true, where the served half already asks
        # for its card.
        assert r.kpi_divs, f"fmt({fmt}) left the saved page with no card"
        assert all(len(d.text) < 5000 for d in r.kpi_divs.values())
        doc = _served_doc(tmp_path, _kpi_spec(fmt=fmt))
        _pick_foreign_one(doc)
        cards = _cards(doc)
        assert cards and all(len(d.text) < 5000 for d in cards)

    def test_an_ordinary_format_is_still_applied(self, tmp_path):
        doc = _served_doc(tmp_path, _kpi_spec(fmt="%9.1f"))
        _pick_foreign_one(doc)
        assert _FOREIGN_MEAN in " ".join(d.text for d in _cards(doc))
