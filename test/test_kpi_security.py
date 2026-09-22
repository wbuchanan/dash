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
import json
import os
import re
import sys
import tempfile

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
        out, _ = _render_kpi(color=payload)
        assert "evil.example" not in out, (
            f"color({payload!r}) reached the document and can make an "
            f"outbound request"
        )
        assert "expression(" not in out
        assert "body{display:none" not in out

    @pytest.mark.parametrize("payload", _CSS_PAYLOADS)
    def test_bgcolor_payload_does_not_reach_the_document(self, payload):
        out, _ = _render_kpi(bgcolor=payload)
        assert "evil.example" not in out
        assert "expression(" not in out
        assert "body{display:none" not in out

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
        """The general property, not one payload at a time."""
        _, dr = _render_kpi(color="red; background:red",
                            bgcolor="blue; content:'x'")
        text = _kpi_div_text(dr)
        for m in re.finditer(r'(?:background|color)\s*:\s*([^;"\n]*)', text):
            val = m.group(1).strip()
            assert "url(" not in val and "expression(" not in val, val


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
