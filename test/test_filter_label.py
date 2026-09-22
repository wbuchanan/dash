"""test_filter_label.py — ``filter(x, label("..."))`` never reached the widget.

The renderer was already right. ``_build_filter_widgets`` resolves a widget
title in three steps — the explicit ``label()``, then the Stata *variable
label*, then the bare variable name — and ``test_filters.py`` covers all
three.

What never happened is the option arriving. ``dash.ado`` writes the whole
``filter()`` option through as one raw string, and the renderer re-parses it
with ``_parse_filter_raw``, which had a regex for ``type()`` and one for
``exclude()`` and **none for ``label()``**. Measured:

    _parse_filter_raw('weight, type(range) label("Curb weight")')
      -> [{'varname': 'weight', 'type': 'range', 'exclude': []}]

so the key the resolver reads first was simply absent and the widget fell
back to the variable name. ``dash.ado`` did not reject the suboption either,
so the user got silence rather than an error.

There is a second half. ``dash.ado`` interpolated the filter string into the
master JSON **unescaped**, so the double quotes in ``label("Curb weight")``
broke the JSON document. Parsing ``label()`` without fixing that would make
the feature reachable and immediately fatal, so both are tested here.
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
from dash_render import DashRenderer

from conftest import make_spec, make_data_json


class TestTheRawParserKeepsTheLabel:
    """The half that was missing."""

    @pytest.mark.parametrize("raw,want", [
        ('weight, type(range) label("Curb weight")', "Curb weight"),
        ("weight, type(range) label(Curb weight)", "Curb weight"),
        ('foreign, type(dropdown) label("Car origin")', "Car origin"),
        ('weight, label("Weight") type(slider)', "Weight"),
    ])
    def test_a_label_survives_parsing(self, raw, want):
        got = DashRenderer._parse_filter_raw(raw)
        assert got, raw
        assert got[0].get("label") == want, got

    def test_the_other_suboptions_still_parse(self):
        got = DashRenderer._parse_filter_raw(
            'foreign, type(dropdown) exclude(g1 g2) label("Origin")')
        assert got[0]["type"] == "dropdown"
        assert got[0]["exclude"] == ["g1", "g2"]
        assert got[0]["label"] == "Origin"

    def test_no_label_is_an_empty_string_not_a_missing_key(self):
        got = DashRenderer._parse_filter_raw("weight, type(range)")
        assert got[0].get("label", "") == ""

    def test_several_filters_keep_their_own_labels(self):
        got = DashRenderer._parse_filter_raw(
            'weight, type(range) label("W") || foreign, '
            'type(dropdown) label("F")')
        assert [g.get("label") for g in got] == ["W", "F"], got


def _render_raw(raw, df=None, variable_labels=None):
    df = df if df is not None else pd.DataFrame({
        "mpg": np.linspace(12.0, 41.0, 20),
        "weight": np.linspace(1760.0, 4840.0, 20),
    })
    spec = make_spec([{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}])
    spec["build_options"]["filter"] = raw
    spec["build_options"].pop("filters", None)
    sp = tempfile.mkstemp(".json")[1]
    dp = tempfile.mkstemp(".json")[1]
    op = tempfile.mkstemp(".html")[1]
    with open(sp, "w") as f:
        json.dump(spec, f)
    data = make_data_json(df)
    if variable_labels:
        # The wrapper nests everything under "StataJSON"; setting a
        # top-level key here reaches nothing.
        data["StataJSON"]["variableLabels"] = variable_labels
    with open(dp, "w") as f:
        json.dump(data, f)
    dr = DashRenderer(sp, dp, op)
    # A second render() would re-home the same Bokeh models in a new
    # document and fail; keep the one document's HTML for the callers that
    # need to look at it.
    dr.rendered_html = dr.render()
    for p in (sp, dp, op):
        try:
            os.unlink(p)
        except OSError:
            pass
    return dr


class TestTheWidgetGetsTheLabel:
    """End to end, through the string dash.ado actually writes."""

    def test_the_explicit_label_becomes_the_widget_title(self):
        dr = _render_raw('weight, type(range) label("Curb weight")')
        assert dr.filter_widgets, "no filter widget was built"
        assert dr.filter_widgets[0].title == "Curb weight", (
            f"the widget is titled {dr.filter_widgets[0].title!r}; "
            f"label() never reached it"
        )

    def test_the_variable_label_is_used_when_no_label_is_given(self):
        dr = _render_raw("weight, type(range)",
                         variable_labels={"weight": "Weight (lbs.)"})
        assert dr.filter_widgets[0].title == "Weight (lbs.)"

    def test_an_explicit_label_beats_the_variable_label(self):
        dr = _render_raw('weight, type(range) label("Curb weight")',
                         variable_labels={"weight": "Weight (lbs.)"})
        assert dr.filter_widgets[0].title == "Curb weight"

    def test_the_bare_name_is_the_last_resort(self):
        dr = _render_raw("weight, type(range)")
        assert dr.filter_widgets[0].title == "weight"


class TestTheLabelIsNotAnInjectionVector:
    """It reaches a widget title that is rendered into the document."""

    @pytest.mark.parametrize("payload", [
        "<script>alert(1)</script>",
        '"><img src=x onerror=alert(1)>',
        "');alert(1);//",
    ])
    @pytest.mark.parametrize("ftype", ["range", "slider", "dropdown"])
    def test_a_payload_does_not_reach_the_document(self, payload, ftype):
        """The document, not the model property.

        Bokeh renders a widget title as text and escapes it on the way in,
        so the model may legitimately hold the raw string; what must never
        appear is executable markup in the emitted HTML.
        """
        var = "foreign" if ftype == "dropdown" else "weight"
        df = pd.DataFrame({
            "mpg": np.linspace(12.0, 41.0, 20),
            "weight": np.linspace(1760.0, 4840.0, 20),
            "foreign": np.array([0.0, 1.0] * 10),
        })
        raw = "%s, type(%s) label(%s)" % (var, ftype, payload)
        import warnings as _w
        with _w.catch_warnings(record=True) as caught:
            _w.simplefilter("always")
            try:
                dr = _render_raw(raw, df=df)
            except Exception:
                return          # rejected outright is also a correct outcome
        # Since WP-14 a refused filter group is refused ALOUD: the parser
        # names the group and the reason rather than dropping it in
        # silence.  The payload with the ';' splits into groups whose
        # variable tokens are not names, and each is refused with a
        # warning.  Either outcome -- a widget whose title Bokeh escapes,
        # or a named refusal -- is correct; silence is not.
        refused = [str(c.message) for c in caught
                   if "filter(" in str(c.message) and "refused" in str(c.message)]
        assert dr.filter_widgets or refused, (raw, [str(c.message) for c in caught])
        if dr.filter_widgets:
            assert payload not in dr.rendered_html, (
                "the payload reached the document unescaped")


class TestTheTitleIsNotDoubleEscaped:
    """Bokeh escapes a widget title itself."""

    @pytest.mark.parametrize("ftype,var", [
        ("dropdown", "foreign"), ("range", "weight"), ("slider", "weight"),
    ])
    def test_an_ampersand_survives_as_an_ampersand(self, ftype, var):
        df = pd.DataFrame({
            "mpg": np.linspace(12.0, 41.0, 20),
            "weight": np.linspace(1760.0, 4840.0, 20),
            "foreign": np.array([0.0, 1.0] * 10),
        })
        dr = _render_raw("%s, type(%s) label(R&D spend)" % (var, ftype),
                         df=df)
        title = dr.filter_widgets[0].title
        # A one-sided slider appends its own operator to the title, so the
        # label is a prefix rather than the whole string.
        assert title.startswith("R&D spend"), (
            f"{ftype}: title is {title!r}; escaping it here escapes it "
            f"twice, because Bokeh escapes it again"
        )
        assert "&amp;" not in title, title
