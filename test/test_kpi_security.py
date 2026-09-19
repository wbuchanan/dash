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
default ``#212529``.

Written before the fix, per project rule 8; the adversarial cases are project
rule 18.
"""
import json
import os
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


def _render_kpi(**kpi_extra):
    """Render a dashboard with one KPI carrying the given fields."""
    spec = make_spec(_PLOTS)
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
        """The two paths must agree, or a KPI is safe only after filtering."""
        expected = _sanitize_css_color(payload, "#212529")
        _, dr = _render_kpi(color=payload)
        text = _kpi_div_text(dr)
        assert f"color:{expected}" in text, (
            f"the initial render did not use the sanitised colour "
            f"{expected!r}; div text was: {text[:300]}"
        )

    def test_a_semicolon_can_never_appear_inside_a_style_attribute_value(self):
        """The general property, not one payload at a time."""
        import re
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
        ("eltblue", "#b7c9e2"),
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
        assert "color:#212529" not in _kpi_div_text(dr), (
            f"color({good}) is a legitimate Stata colour and was replaced by "
            f"the default"
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

    def test_no_colour_given_uses_the_default(self):
        _, dr = _render_kpi()
        assert "#212529" in _kpi_div_text(dr)


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
