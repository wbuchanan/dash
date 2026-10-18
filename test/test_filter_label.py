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
import html
import json
import os
import re
import sys
import tempfile
import warnings

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


def _document_widget_titles(page):
    """Every widget title in the Bokeh document embedded in *page*.

    Bokeh writes the document as JSON inside ``<script
    type="application/json">`` and escapes the markup characters in it, so
    this reads the document the way BokehJS will: unescaped and parsed.
    """
    m = re.search(r'<script type="application/json"[^>]*>(.*?)</script>',
                  page, re.DOTALL)
    assert m, "the page carries no Bokeh document"
    doc = json.loads(html.unescape(m.group(1)))
    titles = []

    def walk(node):
        if isinstance(node, dict):
            if node.get("name") in ("RangeSlider", "Slider", "Select"):
                titles.append(node.get("attributes", {}).get("title"))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(doc)
    return titles


def _document_strings_holding(page, needle):
    """``(model, attribute)`` for every string in the Bokeh document embedded
    in *page* that contains *needle*, one entry per string, in document
    order: a model's attribute values are searched to any depth -- a
    ColumnDataSource's data, a script's code and args, a widget's options --
    and each hit is charged to the innermost model holding it."""
    m = re.search(r'<script type="application/json"[^>]*>(.*?)</script>',
                  page, re.DOTALL)
    assert m, "the page carries no Bokeh document"
    hits = []

    def walk(node, owner):
        if isinstance(node, dict):
            if node.get("type") == "object" and "name" in node:
                for attr, value in (node.get("attributes") or {}).items():
                    walk(value, (node["name"], attr))
                return
            for v in node.values():
                walk(v, owner)
        elif isinstance(node, list):
            for v in node:
                walk(v, owner)
        elif isinstance(node, str) and needle in node:
            hits.append(owner)

    walk(json.loads(html.unescape(m.group(1))), None)
    return hits


class TestTheLabelIsNotAnInjectionVector:
    """It reaches a widget title that is rendered into the document."""

    _WIDGET = {"range": "RangeSlider", "slider": "Slider",
               "dropdown": "Select"}

    #: What each payload does, measured 24sep2026 at 68327a8.  None is
    #: refused outright and no render raises: the label is text, and a
    #: widget title is text.  The second payload loses its leading double
    #: quote, which _dash_filter_label strips as Stata's optional quotes
    #: around a label.  The third payload's ")" closes ``label(`` --
    #: Stata's own parenthesis rule, which _dash_filter_split follows -- so
    #: its label is the apostrophe before it, and each ";" after it parts
    #: another filter() group, refused aloud because "alert(1)" and "//)"
    #: are not variable names.  payload -> (widget title, refused groups).
    _OUTCOME = {
        "<script>alert(1)</script>": ("<script>alert(1)</script>", []),
        '"><img src=x onerror=alert(1)>':
            ("><img src=x onerror=alert(1)>", []),
        "');alert(1);//": ("'", ["alert(1)", "//)"]),
    }

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

        This used to wrap the render in ``except Exception: return``
        ("rejected outright is also a correct outcome"), so any exception
        at all -- a crash included -- passed.  Nothing is rejected outright:
        the outcome of every payload is measured and asserted as it is.
        """
        var = "foreign" if ftype == "dropdown" else "weight"
        df = pd.DataFrame({
            "mpg": np.linspace(12.0, 41.0, 20),
            "weight": np.linspace(1760.0, 4840.0, 20),
            "foreign": np.array([0.0, 1.0] * 10),
        })
        raw = "%s, type(%s) label(%s)" % (var, ftype, payload)
        label, refused_groups = self._OUTCOME[payload]
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr = _render_raw(raw, df=df)
        msgs = [str(c.message) for c in caught]
        # Since WP-14 a refused filter group is refused ALOUD, named with
        # the reason, never dropped in silence.
        refused = [m for m in msgs
                   if m.startswith("dash: filter(") and " refused: " in m]
        assert refused == [
            "dash: filter(%s) refused: %r is not a valid variable name; no "
            "widget was built." % (g, g) for g in refused_groups], msgs

        assert [type(w).__name__ for w in dr.filter_widgets] == \
            [self._WIDGET[ftype]], (raw, msgs)
        title = dr.filter_widgets[0].title
        # A one-sided slider appends its own operator to the title.
        want = label + " \u2265" if ftype == "slider" else label
        assert title == want, (raw, title)

        page = dr.rendered_html
        assert payload not in page, (
            "the payload reached the document unescaped")
        for markup in ("<script>alert(1)", "<img src=x"):
            assert markup not in page, (
                "executable markup %r reached the document" % markup)
        # The title did reach the document -- as data, which BokehJS sets
        # as text -- so the absence above is escaping at work and not a
        # title that never arrived.
        assert _document_widget_titles(page) == [want], raw
        # And the title is the ONLY place in the document that holds it.
        # Bokeh escapes the markup characters of the JSON it embeds, so the
        # page-text checks above see a payload only where it reached the
        # page outside the document: inside it, a label in an HTML sink --
        # a Div's text, which BokehJS sets as innerHTML -- or spliced into a
        # script's code passed them all (measured 24sep2026, both).  Every
        # string holding the payload's call is found, wherever it sits; the
        # third payload's label is its apostrophe alone, and its call is in
        # the refused groups, so nothing in the document holds it.
        # Flipped (WP-31 K6): the title alone was wrong because the label
        # also names the widget's host -- its html_attributes aria-label,
        # which BokehJS sets with setAttribute and never parses (an
        # attribute sink, test_label_sinks).  The host holds exactly a role
        # and that name: no payload becomes an attribute of its own.
        where = _document_strings_holding(page, "alert(1)")
        assert where == ([(self._WIDGET[ftype], "html_attributes"),
                          (self._WIDGET[ftype], "title")]
                         if "alert(1)" in label else []), (raw, where)
        host = dict(dr.filter_widgets[0].html_attributes or {})
        assert set(host) == {"role", "aria-label"}, (raw, host)
        assert host["role"] == "group", (raw, host)
        # The reader finds the label itself, the apostrophe too, where it is.
        assert (self._WIDGET[ftype], "title") in _document_strings_holding(
            page, label), raw


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
