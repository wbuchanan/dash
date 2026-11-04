"""The KPI card was built five times, and the server's copy was unsafe.

Three defects, all measured.

**Security.** Standalone resolves a KPI colour through ``_resolve_kpi_color``
— translate the Stata colour name, then sanitise — because the value lands
inside ``style="...color:{color};"`` and ``html.escape`` does not stop a CSS
*property* injection: ``;``, ``(`` and ``)`` pass straight through. The
generated server app only escaped. Measured: ``color(red;
background:url(http://evil/x))`` reached the served document as

    style="font-size:28px;font-weight:bold;color:red; background:url(http://evil/x);"

a second declaration the browser honours, while the same spec rendered
standalone contained no such string.

**Correctness.** Stata colour names were never translated in server mode
either, so ``color(navy)`` gave CSS navy (#000080) where Stata's navy is
#1a476f, and ``gs10`` or ``red%50`` — both legitimate — were not CSS at all.

**Drift.** The KPI value was 36px standalone and 28px served, with different
padding, border and label colours. The same dashboard, two cards.
"""
import importlib.util
import itertools
import json
import os
import sys

import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import Div

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
from conftest import make_data_json
from conftest import drawn_renderers  # noqa: E402

_SEQ = itertools.count()
_DF = pd.DataFrame({"mpg": [22.0, 18.0, 25.0, 30.0],
                    "weight": [2930.0, 3350.0, 2200.0, 1800.0]})


def _spec(color="", bgcolor=""):
    return {
        "graphs": [{"name": "g1", "graph_options": {"name": "g1"},
                    "plots": [{"type": "scatter", "yvar": "mpg",
                               "xvar": "weight", "options": {}}],
                    "options": {}}],
        "kpis": [{"name": "k1", "stat": "mean", "var": "mpg",
                  "value": "23.75", "display": "23.75", "fmt": "%9.2f",
                  "title": "Avg", "subtitle": "n=4", "color": color,
                  "bgcolor": bgcolor, "update": "filter",
                  "if_expr": "", "in_expr": ""}],
        "build_options": {"layout": "auto", "link": "", "filter": "",
                          "theme": "", "scheme": "", "session_scheme": "",
                          "title": "", "subtitle": "", "registry": "g1 k1",
                          "tabs": "", "filter_position": "top",
                          "level": "95", "formats": {}},
    }


def _paths(tmp_path, spec):
    tag = next(_SEQ)
    sp = tmp_path / f"s_{tag}.json"
    dp = tmp_path / f"d_{tag}.json"
    sp.write_text(json.dumps(spec))
    dp.write_text(json.dumps(make_data_json(_DF)))
    return tag, str(sp), str(dp)


def _standalone_html(tmp_path, spec):
    _t, sp, dp = _paths(tmp_path, spec)
    return dr.DashRenderer(sp, dp).render()


def _server_doc(tmp_path, spec):
    tag, sp, dp = _paths(tmp_path, spec)
    ap = tmp_path / f"a_{tag}.py"
    dr.ServerAppBuilder(sp, dp).build(str(ap))
    ms = importlib.util.spec_from_file_location(f"_kpi_app_{tag}", str(ap))
    mod = importlib.util.module_from_spec(ms)
    ms.loader.exec_module(mod)
    doc = Document()
    mod.make_document(doc)
    return doc


def _server_divs(tmp_path, spec):
    doc = _server_doc(tmp_path, spec)
    out, seen = [], set()

    def walk(m):
        if isinstance(m, (list, tuple)):
            for x in m:
                if x is not None and not isinstance(x, (int, float, str)):
                    walk(x)
            return
        if m is None or id(m) in seen:
            return
        seen.add(id(m))
        if isinstance(m, Div):
            out.append(m.text)
        for attr in ("children", "tabs", "child"):
            k = getattr(m, attr, None)
            if k is not None:
                walk(k)

    for r in doc.roots:
        walk(r)
    return " ".join(out)


class TestTheServerSanitisesAKpiColour:
    @pytest.mark.parametrize("payload", [
        "red; background:url(http://evil/x)",
        "red;background-image:url(//evil)",
        "blue) ; x:url(http://evil/y",
        "expression(alert(1))",
    ])
    def test_a_css_property_injection_does_not_reach_the_document(
            self, tmp_path, payload):
        srv = _server_divs(tmp_path, _spec(color=payload))
        assert "evil" not in srv
        assert "url(" not in srv
        assert "expression(" not in srv

    def test_a_bgcolor_payload_is_blocked_too(self, tmp_path):
        srv = _server_divs(
            tmp_path, _spec(bgcolor="white; background:url(http://evil/z)"))
        assert "evil" not in srv

    def test_standalone_was_already_safe_and_stays_safe(self, tmp_path):
        html = _standalone_html(
            tmp_path, _spec(color="red; background:url(http://evil/x)"))
        assert "evil" not in html


class TestAStataColourNameMeansStatasColour:
    def test_navy_is_statas_navy_not_css_navy(self, tmp_path):
        srv = _server_divs(tmp_path, _spec(color="navy"))
        expected = dr.OptionTranslator.translate_mcolor("navy")
        assert expected.lower() in srv.lower()
        assert expected.lower() != "#000080"

    def test_a_greyscale_name_resolves(self, tmp_path):
        srv = _server_divs(tmp_path, _spec(color="gs10"))
        expected = dr.OptionTranslator.translate_mcolor("gs10")
        assert expected.lower() in srv.lower()


class TestTheCardLooksTheSameInBothModes:
    def test_the_value_font_size_matches(self, tmp_path):
        spec = _spec()
        html = _standalone_html(tmp_path, spec)
        srv = _server_divs(tmp_path, spec)
        assert "font-size:36px" in html.replace(" ", "")
        assert "font-size:36px" in srv.replace(" ", ""), (
            "the KPI value is a different size in server mode"
        )

    def test_the_title_and_subtitle_are_present(self, tmp_path):
        srv = _server_divs(tmp_path, _spec())
        assert "Avg" in srv and "n=4" in srv

    def test_the_card_class_is_the_same(self, tmp_path):
        assert "db-kpi-card" in _server_divs(tmp_path, _spec())

    def test_html_in_a_title_is_still_escaped(self, tmp_path):
        spec = _spec()
        spec["kpis"][0]["title"] = "<script>alert(1)</script>"
        srv = _server_divs(tmp_path, spec)
        assert "<script>" not in srv


class TestAPlotOfAVariableAgainstItself:
    def test_scatter_y_y_does_not_crash_the_server_app(self, tmp_path):
        """`twoway scatter mpg mpg' is legal; the app raised DuplicateError.

        The plot source is built as g_df[[xvar, yvar]], which pandas rejects
        when the two names are the same. Standalone renders it.
        """
        spec = _spec()
        spec["graphs"][0]["plots"] = [{"type": "scatter", "yvar": "mpg",
                                       "xvar": "mpg", "options": {}}]
        from bokeh.models import GlyphRenderer
        want = list(_DF["mpg"])
        _t, sp, dp = _paths(tmp_path, spec)
        std = dr.DashRenderer(sp, dp)
        std.render()                                   # must not raise
        drawn = {}
        for mode, renderers in (
                ("saved", drawn_renderers(std.figures["g1"])),
                ("served", [m for m in drawn_renderers(
                                _server_doc(tmp_path, spec).models)
                            if isinstance(m, GlyphRenderer)])):
            # Both modes draw the four points on the diagonal: x and y are
            # the one column.
            assert [type(r.glyph).__name__ for r in renderers] == \
                ["Scatter"], mode
            glyph, data = renderers[0].glyph, renderers[0].data_source.data
            drawn[mode] = ([float(v) for v in data[glyph.x]],
                           [float(v) for v in data[glyph.y]])
        assert drawn["saved"] == drawn["served"] == (want, want), drawn
