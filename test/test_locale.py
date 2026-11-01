"""set dp comma, %tC's leap seconds and graph set fonts (WP-31 G2).

dash never read ``c(dp)``, converted ``%tC`` with ``%tc``'s epoch (up to
27 s off) and did not read the ``graph set`` font faces (GAPS3 G2).
Truth: test/fixtures/data_locale_truth.json
(scripts/extract_data_locale_truth.do).
"""
import copy
import json
import os
import re
import sys
import warnings

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import dash_render as dr  # noqa: E402
import test_by_axes_keys as tk  # noqa: E402
import test_by_grid as tg  # noqa: E402
from js_runner import requires_node, run_js  # noqa: E402
from conftest import load_app, render_models  # noqa: E402

_FIX = os.path.join(os.path.dirname(__file__), "fixtures",
                    "data_locale_truth.json")
_SRC = os.path.join(os.path.dirname(__file__), "..", "dash_render.py")
MODES = ("saved", "served")


def _truth():
    with open(_FIX, encoding="utf-8") as fh:
        return json.load(fh)


#: (fixture key, value, format): display under set dp comma.
DP_CASES = [("dp.f", 3.14159, "%9.2f"), ("dp.fc", 1234567.891, "%12.2fc"),
            ("dp.g", 0.5, "%9.0g")]


def _build(mode, plots, go, build=None, data=None):
    spec = tk._spec([tk._graph("g", plots, go)], scheme="s2color")
    spec["build_options"].update(build or {})
    return tk._build(mode, spec, data=data or copy.deepcopy(tg._data()))


def _models(roots):
    return [m for r in roots for m in r.references()]


class TestDpComma:
    @pytest.mark.parametrize("key,value,fmt", DP_CASES)
    def test_python_writer(self, key, value, fmt):
        assert dr._dash_fmt(value, fmt, dp="comma") == _truth()[key]

    @requires_node
    @pytest.mark.parametrize("key,value,fmt", DP_CASES)
    def test_js_twin(self, key, value, fmt):
        out = run_js(dr._DASH_FMT_JS + "\nprocess.stdout.write(JSON.stringify("
                     "dash_fmt(%r, %r, '', false, 'comma')));"
                     % (value, fmt))
        assert out == _truth()[key]

    def test_dates_unchanged(self):
        assert dr._dash_fmt_text(20000, "%td", dp="comma") == \
            _truth()["dp.td"]

    def test_comma_formats_are_statas(self):
        # dash.ado writes a variable's format with a comma under set dp
        # comma (_dash_dp_format); the twins read it as display does.
        t = _truth()
        assert [dr._dash_fmt_text(v, "%8,0gc") for v in (2000, 3000)] == \
            t["dp.axis"]["ticks"][4:6]
        assert [dr._dash_fmt_text(v, "%6,2f") for v in (2, 2.5)] == \
            t["dp.axis_dec"]["ticks"][4:6]
        assert dr._dash_dp_fmt("%9.2fc", "comma") == "%9,2fc"
        assert dr._dash_dp_fmt("%td", "comma") == "%td"
        assert dr._dash_dp_fmt("%9.2f", "period") == "%9.2f"

    def test_every_fmt_caller_passes_dp(self):
        with open(_SRC, encoding="utf-8") as fh:
            src = fh.read()
        bad = []
        for m in re.finditer(r"(?<![\w.])_dash_fmt(?:_text)?\(", src):
            line_start = src.rfind("\n", 0, m.start()) + 1
            line = src[line_start:src.find("\n", m.start())]
            if line.lstrip().startswith(("def ", "#", "``", ":func:")) \
                    or "``" in line or ":func:" in line:
                continue
            # The call's own text, to its closing parenthesis.
            depth, i = 0, m.end() - 1
            while i < len(src):
                if src[i] == "(":
                    depth += 1
                elif src[i] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                i += 1
            call = src[m.start():i + 1]
            if "dp=" in call or "dp)" in call or "no dp:" in line:
                continue
            bad.append(line.strip())
        assert not bad, bad

    def test_build_dp_reads_the_spec(self):
        assert dr._dash_build_dp({"build_options": {"dp": "comma"}}) == "comma"
        assert dr._dash_build_dp({"build_options": {}}) == "period"
        assert dr._dash_build_dp({"build_options": {"dp": "x"}}) == "period"

    def test_page_settings(self):
        class M:
            pass
        m, cache = M(), {}
        assert dr._dash_page_settings(m, cache, {"dp": "comma"}) == "comma"
        assert m.dp == "comma" and cache["dp"] == "comma"
        assert dr._dash_cache_dp(cache) == "comma"
        assert dr._dash_cache_dp(None) == "period"
        assert dr._dash_page_dp("comma") == "comma"
        assert dr._dash_page_dp() == "period"

    @pytest.mark.parametrize("mode", MODES)
    def test_axis_ticks_both_modes(self, mode):
        from bokeh.models import CustomJSTickFormatter
        roots, _n, _o = _build(mode, [{"type": "scatter", "yvar": "mpg",
                                       "xvar": "weight", "options": {}}],
                               {}, {"dp": "comma"})
        fmts = [m for m in _models(roots)
                if isinstance(m, CustomJSTickFormatter)]
        assert fmts
        assert {dict(m.args).get("dp") for m in fmts} == {"comma"}

    @pytest.mark.parametrize("mode", MODES)
    def test_default_formats_take_the_mark(self, mode):
        # A value with no variable format (a by() subtitleformat, the
        # %9.0g default) is written in the page's mark too.
        roots, _n, _o = _build(mode, [{"type": "scatter", "yvar": "mpg",
                                       "xvar": "weight", "options": {}}],
                               {"by": "g3, subtitleformat(%9.2f)"},
                               {"dp": "comma"})
        from by_panel_probe import panel_label
        labels = {panel_label(m) for m in _models(roots)
                  if type(m).__name__ == "figure"} - {""}
        assert labels and all("," in t for t in labels), labels


class TestLeapSeconds:
    def test_table_is_statas(self):
        assert list(dr._STATA_LEAP_SECONDS_TC_MS) == _truth()["leap.table"]
        assert len(dr._STATA_LEAP_SECONDS_TC_MS) == 27

    @pytest.mark.parametrize("case", range(20))
    def test_roundtrip(self, case):
        C, c = _truth()["leap.roundtrip"][case]
        assert dr._dash_tc_from_tC([float(C)])[0] == float(c)

    @pytest.mark.parametrize("case", range(3))
    def test_inside_a_leap_second(self, case):
        C, c = _truth()["leap.inside"][case]
        assert dr._dash_tc_from_tC([float(C)])[0] == float(c)
        C, c = _truth()["leap.after_midnight"][case]
        assert dr._dash_tc_from_tC([float(C)])[0] == float(c)

    def test_missing_stays_missing(self):
        got = dr._dash_tc_from_tC([np.nan, np.inf])
        assert np.isnan(got[0]) and np.isinf(got[1])

    def test_no_warning(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            dr._stata_dates_to_datetime(pd.Series([1.0e12]), "tC")
        assert not [w for w in caught if "leap" in str(w.message).lower()]

    @pytest.mark.parametrize("mode", MODES)
    def test_tooltip_is_statas(self, mode):
        C, c = _truth()["leap.roundtrip"][0]
        data = copy.deepcopy(tg._data())
        for i, row in enumerate(data["values"]):
            row["t"] = float(C + 1000 * i)
        data["variableNames"].append("t")
        data["storageTypes"]["t"] = "double"
        data["variableIsString"]["t"] = False
        data["variableLabels"]["t"] = ""
        roots, _n, _o = _build(mode, [{"type": "scatter", "yvar": "mpg",
                                       "xvar": "t", "options": {}}],
                               {}, {"formats": {"t": "%tC"}}, data=data)
        xs = [m.data["t"] for m in _models(roots)
              if type(m).__name__ == "ColumnDataSource" and "t" in m.data]
        assert xs
        first = pd.Timestamp(np.asarray(xs[0])[0])
        want = pd.Timestamp("1960-01-01") + pd.Timedelta(milliseconds=c)
        assert first == want


class TestGraphSetFonts:
    def test_fonts_of(self):
        got = dr._dash_gt_fonts_of({"fontfacesans": "Courier",
                                    "fontfaceserif": "Times",
                                    "fontfacemono": "bad;face"})
        assert got["stSans"].startswith("Courier, Helvetica")
        assert got["stSerif"] == dr._DASH_GT_FONTS["stSerif"]
        assert got["stMono"] == dr._DASH_GT_FONTS["stMono"]
        assert dr._dash_gt_fonts_of(None) == dr._DASH_GT_FONTS

    @pytest.mark.parametrize("mode", MODES)
    def test_face_reaches_the_families(self, mode, tmp_path):
        # The measured rule: {stSans} follows fontfacesans (fonts.svg).
        assert _truth()["fonts.svg"]["fontfacesans_courier"] == "'Courier'"
        spec = tk._spec([tk._graph("g", [{"type": "scatter", "yvar": "mpg",
                                          "xvar": "weight", "options": {}}],
                                   {})], scheme="s2color")
        spec["build_options"]["fontfacesans"] = "Courier"
        sp = tmp_path / "s.json"
        dp = tmp_path / "d.json"
        sp.write_text(json.dumps(spec))
        dp.write_text(json.dumps(tg._data()))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if mode == "saved":
                r = dr.DashRenderer(str(sp), str(dp))
                render_models(r)
                mapper = r.mapper
            else:
                from bokeh.document import Document
                ap = tmp_path / "a.py"
                dr.ServerAppBuilder(str(sp), str(dp)).build(str(ap))
                mod = load_app(str(ap), "_s43_font_app", draw=False)
                mod.make_document(Document())
                mapper = mod._DASH_MAPPER
        assert mapper._dash_gt_fonts["stSans"].startswith("Courier")


class TestGraphSetFontsDrawn:
    """The font tags draw in the page's graph set faces: a title's run and
    a marker label's whole-label font, both modes (WP-31 G2)."""

    @staticmethod
    def _models(mode, tmp_path, opts=None, go=None):
        data = copy.deepcopy(tg._data())
        for row in data["values"]:
            row["lab"] = "{stSans:car}"
        data["variableNames"].append("lab")
        data["storageTypes"]["lab"] = "str12"
        data["variableIsString"]["lab"] = True
        data["variableLabels"]["lab"] = ""
        spec = tk._spec([tk._graph("g", [{"type": "scatter", "yvar": "mpg",
                                          "xvar": "weight",
                                          "options": dict(opts or {})}],
                                   dict(go or {}), title=False)],
                        scheme="s2color")
        spec["build_options"]["fontfacesans"] = "Courier"
        roots, _n, _o = tk._build(mode, spec, data=data)
        return [m for r in roots for m in r.references()]

    @pytest.mark.parametrize("mode", MODES)
    def test_title_run(self, mode, tmp_path):
        ms = self._models(mode, tmp_path, go={"title": '"{stSans:T}"'})
        fonts = [m.text_font for m in ms if type(m).__name__ == "Title"
                 and str(m.text or "") == "T"]
        assert fonts and all(str(f).startswith("Courier") for f in fonts), \
            fonts

    @pytest.mark.parametrize("mode", MODES)
    def test_mlabel_font(self, mode, tmp_path):
        ms = self._models(mode, tmp_path, opts={"mlabel": "lab"})
        fonts = [m.text_font for m in ms if type(m).__name__ == "LabelSet"]
        assert fonts and all(str(f).startswith("Courier") for f in fonts), \
            fonts

    def test_page_fonts(self):
        assert dr._dash_page_fonts({"stSans": "X"}) == {"stSans": "X"}
        assert dr._dash_page_fonts() == dr._DASH_GT_FONTS
