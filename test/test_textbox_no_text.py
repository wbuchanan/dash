"""WP-29 P0.4: a title option that gives only sub-options keeps the default.

twoway reads ``ytitle(, size(large))`` as "the default title, at large"
(``_gs_parse_and_log_axtitle.ado``: the text is replaced only when it is
not empty; the sub-options apply separately).  dash computed "given" over
the whole raw value, sub-options included, so every such option deleted
the default title, in both modes; ``ytitle(,)`` drew a literal comma, and a
second axis was never titled by default.  Measured truth:
``test/fixtures/text_truth.json`` (``scripts/extract_text_truth.do``).

The rule (u04 A4): the first comma outside strings and parentheses that is
followed, after blanks, by a name, another comma, or the end opens the
sub-options; empty slots are ignored.  Only a typed ``""`` removes a title.
"""
import itertools
import json
import os
import sys
import time
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import ColorBar, ContinuousAxis, LinearAxis, Title
from bokeh.plotting import figure as _FIG

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402
from conftest import make_data_json, load_app  # noqa: E402
from test_dual_axis import _lone_figure, _axes  # noqa: E402
from test_colorvar_forms import _both, _colorbar  # noqa: E402
from test_served_linked_views import _fire  # noqa: E402

MODES = ("saved", "served")
_ONE = [{"type": "scatter", "yvar": "y1", "xvar": "x", "options": {}}]
LARGE = f"{dr._textbox_size({'size': 'large'}, None):g}px"
_SEQ = itertools.count()
_FIXTURE = os.path.join(_HERE, "fixtures", "text_truth.json")


def _truth():
    if not os.path.exists(_FIXTURE):
        pytest.fail("test/fixtures/text_truth.json is missing: run "
                    "scripts/extract_text_truth.do (WP-29 task 03-12)")
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Building: unlabelled x, y1, y2, g (S03's helper writes "" labels).
# ---------------------------------------------------------------------------
_N = 20
_DF = pd.DataFrame({
    "x": [float(i) for i in range(1, _N + 1)],
    "y1": [float((i * 7) % 13) + 1.0 for i in range(_N)],
    "y2": [1000.0 + 37.0 * ((i * 5) % 11) for i in range(_N)],
    "g": [float(i % 2) for i in range(_N)],
})


def _spec(plots, go=None, filters=None):
    go = dict(go or {})
    go.setdefault("name", "g1")
    bo = {"layout": "auto", "link": "", "filter": "", "theme": "",
          "scheme": "", "session_scheme": "", "title": "", "subtitle": "",
          "registry": "g1", "tabs": "", "filter_position": "top",
          "level": "95", "formats": {}}
    if filters:
        bo["filters"] = filters
    return {"graphs": [{"name": "g1", "graph_options": go,
                        "options": dict(go), "plots": plots,
                        "if_expr": "", "in_expr": ""}],
            "kpis": [], "build_options": bo}


def _paths(tmp_path, spec, data):
    tag = next(_SEQ)
    sp, dp = tmp_path / f"s_{tag}.json", tmp_path / f"d_{tag}.json"
    sp.write_text(json.dumps(spec))
    dp.write_text(json.dumps(data))
    return str(sp), str(dp), str(tmp_path / f"a_{tag}.py")


def _document(mode, tmp_path, spec, data=None):
    """(renderer or document, warnings)."""
    data = data if data is not None else make_data_json(_DF)
    sp, dp, ap = _paths(tmp_path, spec, data)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        if mode == "saved":
            obj = dr.DashRenderer(sp, dp)
            obj.render()
        else:
            dr.ServerAppBuilder(sp, dp).build(ap)
            mod = load_app(ap, f"_tnt_app_{next(_SEQ)}")
            obj = Document()
            mod.make_document(obj)
    return obj, [str(w.message) for w in caught]


def _figs(mode, obj):
    roots = list(obj.figures.values()) if mode == "saved" else obj.roots
    out, seen = [], set()
    for r in roots:
        for f in r.select({"type": _FIG}):
            if f.id not in seen:
                seen.add(f.id)
                out.append(f)
    return out


def _fig(mode, tmp_path, plots, go=None, data=None):
    obj, caught = _document(mode, tmp_path, _spec(plots, go), data)
    figs = _figs(mode, obj)
    assert len(figs) == 1, figs
    return figs[0], caught


def _y(fig):
    (ax,) = _axes(fig.left)
    return ax


def _x(fig):
    (ax,) = _axes(fig.below)
    return ax


def _right(fig):
    axes = [a for a in fig.right if isinstance(a, ContinuousAxis)]
    assert len(axes) == 1, axes
    return axes[0]


def _notes(caught, option):
    return [w for w in caught if f"{option}() sub-option" in w]


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------
class TestTextboxHasText:
    @pytest.mark.parametrize("raw,want", [
        ("", False), (",", False), (",,", False), (", size(large)", False),
        (" , size(large)", False), (",size(large)", False),
        (", suffix", False),
        ('""', True), ('"", size(large)', True), ('" "', True), ("A", True),
        ("A,", True), ('"A",', True), ("A,,", True)])
    def test_cases(self, raw, want):
        assert dr._textbox_has_text(raw) is want


class TestTrailingComma:
    def test_split_point(self):
        assert [dr._textbox_split_point(s)
                for s in (",", "A,", "A, ", '"A",')] == [0, 1, 1, 3]

    def test_split_point_double(self):
        assert [dr._textbox_split_point(s)
                for s in ("A,,", "A, ,", ",,")] == [1, 1, 0]
        assert dr._textbox_split_point('"a", "b"') == -1
        assert dr._textbox_split_point('"a", 2 more') == -1

    def test_parse(self):
        assert dr._parse_textbox_opt("A,") == ("A", {})
        assert dr._parse_textbox_opt('"A",') == ("A", {})
        assert dr._parse_textbox_opt(",") == ("", {})

    @pytest.mark.parametrize("mode", MODES)
    def test_title_family_both_modes(self, mode, tmp_path):
        fig, _ = _fig(mode, tmp_path, _ONE, {"title": "A,"})
        assert fig.title.text == "A"
        fig, _ = _fig(mode, tmp_path, _ONE, {"title": ","})
        assert not (fig.title.text if fig.title is not None else "")
        obj, _ = _document(mode, tmp_path, _spec(_ONE, {"note": '"N",'}))
        texts = [getattr(m, "text", None) for f in _figs(mode, obj)
                 for m in f.select({"type": object})
                 if type(m).__name__ in ("Label", "Title")]
        assert "N" in texts and "N," not in texts

    @pytest.mark.parametrize("mode", MODES)
    def test_double_comma(self, mode, tmp_path):
        for raw in ("A,,", "A, ,"):
            fig, caught = _fig(mode, tmp_path, _ONE, {"ytitle": raw})
            assert _y(fig).axis_label == "A", raw
            assert not _notes(caught, "ytitle"), (raw, caught)
        fig, _ = _fig(mode, tmp_path, _ONE, {"ytitle": ",,"})
        assert _y(fig).axis_label == "y1"
        fig, caught = _fig(mode, tmp_path, _ONE,
                           {"ytitle": "A, size(large),"})
        assert _y(fig).axis_label == "A"
        assert _y(fig).axis_label_text_font_size == LARGE
        assert not _notes(caught, "ytitle"), caught

    @pytest.mark.parametrize("mode", MODES)
    def test_facet_title_keeps_its_panel(self, mode, tmp_path):
        obj, _ = _document(mode, tmp_path,
                           _spec(_ONE, {"by": "g", "title": "A,"}))
        titles = [f.title.text for f in _figs(mode, obj)
                  if f.title is not None and f.title.text]
        assert titles and all(t.startswith("A — ") for t in titles), titles

    def test_a_routed_double_comma_is_silent(self):
        spec = {"graphs": [{"graph_options": {"ytitle": "A,, axis(2)"}}]}
        go = dr._dash_route_axis_titles(spec)["graphs"][0]["graph_options"]
        assert "ytitle" not in go and go.get("ytitle2") == "A, ,", go
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            text, _opts = dr._dash_textbox("A, ,", "ytitle2")
        assert text == "A"
        assert not caught, [str(w.message) for w in caught]

    def test_comma_digit_is_still_text(self):
        assert dr._textbox_split_point('"a", 2 more') == -1
        assert dr._textbox_split_point("a, 1") == -1


class TestSubOptionsKeepTheDefault:
    @pytest.mark.parametrize("mode", MODES)
    def test_size_keeps_the_y_title(self, mode, tmp_path):
        fig, _ = _fig(mode, tmp_path, _ONE, {"ytitle": ", size(large)"})
        assert _y(fig).axis_label == "y1"
        assert _y(fig).axis_label_text_font_size == LARGE

    @pytest.mark.parametrize("mode", MODES)
    def test_colour_keeps_the_x_title(self, mode, tmp_path):
        fig, _ = _fig(mode, tmp_path, _ONE, {"xtitle": ", color(red)"})
        assert _x(fig).axis_label == "x"
        assert _x(fig).axis_label_text_color == "#ff0000"

    @pytest.mark.parametrize("mode", MODES)
    def test_every_spelling(self, mode, tmp_path):
        for raw in (", c(red)", ",size(large)", " , size(large)",
                    ", si(large)", ", axis(1) size(large)", ",", ",,"):
            fig, _ = _fig(mode, tmp_path, _ONE, {"ytitle": raw})
            assert _y(fig).axis_label == "y1", raw

    @pytest.mark.parametrize("mode", MODES)
    def test_unhonoured_suboption_keeps_title_and_is_named(self, mode,
                                                           tmp_path):
        for raw, name in ((", orientation(horizontal)", "orientation"),
                          (", lcolor(red) box", "lcolor")):
            fig, caught = _fig(mode, tmp_path, _ONE, {"ytitle": raw})
            assert _y(fig).axis_label == "y1", raw
            # One note.  The served app is built (Stata's process) and then
            # run (the server's), and each names it once to its own output,
            # so the served list is read as distinct notes.
            notes = _notes(caught, "ytitle")
            if mode == "served":
                notes = sorted(set(notes))
            assert len(notes) == 1 and name in notes[0], (raw, caught)

    @pytest.mark.parametrize("mode", MODES)
    def test_histogram_kdensity(self, mode, tmp_path):
        h = [{"type": "histogram", "var": "y1", "options": {}}]
        fig, _ = _fig(mode, tmp_path, h, {"ytitle": ", size(large)"})
        assert _y(fig).axis_label == "Density"
        hp = [{"type": "histogram", "var": "y1",
               "options": {"percent": "percent"}}]
        fig, _ = _fig(mode, tmp_path, hp, {"ytitle": ", size(large)"})
        assert _y(fig).axis_label == "Percent"
        k = [{"type": "kdensity", "var": "y1", "options": {}}]
        fig, _ = _fig(mode, tmp_path, k, {"ytitle": ", size(large)",
                                          "xtitle": ", size(large)"})
        assert _y(fig).axis_label == "kdensity y1"
        assert _x(fig).axis_label == "x"

    @pytest.mark.parametrize("mode", MODES)
    def test_lone_second_axis(self, mode, tmp_path):
        plots = [{"type": "scatter", "yvar": "y1", "xvar": "x",
                  "options": {"yaxis": "2"}}]
        fig = _lone_figure(mode, plots,
                           {"name": "fig1", "ytitle2": ", size(large)"})
        (ax,) = _axes(fig.left)
        assert ax.axis_label == "y1"
        assert ax.axis_label_text_font_size == LARGE

    @pytest.mark.parametrize("mode", MODES)
    def test_by_panels(self, mode, tmp_path):
        obj, _ = _document(mode, tmp_path,
                           _spec(_ONE, {"by": "g", "ytitle": ", size(large)"}))
        ys = [a for f in _figs(mode, obj) for a in _axes(f.left)]
        assert ys
        for a in ys:
            assert a.axis_label == "y1"
            assert a.axis_label_text_font_size == LARGE

    @pytest.mark.parametrize("mode", MODES)
    def test_merged_values(self, mode, tmp_path):
        fig, _ = _fig(mode, tmp_path, _ONE, {"ytitle": '"A", size(large)'})
        assert (_y(fig).axis_label,
                _y(fig).axis_label_text_font_size) == ("A", LARGE)
        fig, _ = _fig(mode, tmp_path, _ONE,
                      {"ytitle": ", size(large) color(red)"})
        a = _y(fig)
        assert (a.axis_label, a.axis_label_text_color,
                a.axis_label_text_font_size) == ("y1", "#ff0000", LARGE)
        fig, _ = _fig(mode, tmp_path, _ONE, {"ytitle": '"", size(large)'})
        assert not _y(fig).axis_label

    @pytest.mark.parametrize("mode", MODES)
    def test_empty_text_with_suffix(self, mode, tmp_path):
        fig, _ = _fig(mode, tmp_path, _ONE, {"ytitle": '"", suffix'})
        assert _y(fig).axis_label == "y1"

    @pytest.mark.parametrize("mode", MODES)
    def test_an_unlabelled_variable_is_styled(self, mode, tmp_path):
        fig, _ = _fig(mode, tmp_path, _ONE, {"ytitle": ", size(large)"},
                      data=make_data_json(_DF))
        assert make_data_json(_DF)["StataJSON"]["variableLabels"]["y1"] == ""
        assert (_y(fig).axis_label,
                _y(fig).axis_label_text_font_size) == ("y1", LARGE)

    def test_suffix_prefix_alone_and_empty_default(self):
        assert dr._dash_textbox_or_default(", suffix", "ytitle", "y1")[0] \
            == "y1"
        assert dr._dash_textbox_or_default('"e", suffix', "ytitle", "")[0] \
            == "e"
        assert dr._dash_textbox_or_default('"e", prefix', "ytitle",
                                           "y1")[0] == "e\ny1"
        assert dr._dash_textbox_or_default('"e", suffix', "ytitle",
                                           "y1")[0] == "y1\ne"


# ---------------------------------------------------------------------------
# Part B: the second axis
# ---------------------------------------------------------------------------
_DUAL = [{"type": "scatter", "yvar": "y1", "xvar": "x", "options": {}},
         {"type": "line", "yvar": "y2", "xvar": "x",
          "options": {"yaxis": "2"}}]


class TestSecondAxisDefaultTitle:
    @pytest.mark.parametrize("mode", MODES)
    def test_default_title(self, mode, tmp_path):
        fig, _ = _fig(mode, tmp_path, _DUAL)
        assert _right(fig).axis_label == "y2"
        fig, _ = _fig(mode, tmp_path, _DUAL, {"ytitle2": ", size(large)"})
        assert (_right(fig).axis_label,
                _right(fig).axis_label_text_font_size) == ("y2", LARGE)
        fig, _ = _fig(mode, tmp_path, _DUAL, {"ytitle2": ""})
        assert _right(fig).axis_label == "y2"
        x2 = [{"type": "scatter", "yvar": "y1", "xvar": "x", "options": {}},
              {"type": "scatter", "yvar": "y1", "xvar": "y2",
               "options": {"xaxis": "2"}}]
        fig, _ = _fig(mode, tmp_path, x2)
        tops = [a for a in fig.above if isinstance(a, ContinuousAxis)]
        assert [a.axis_label for a in tops] == ["y2"]
        fig, _ = _fig(mode, tmp_path, _DUAL, {"ytitle2": '""'})
        assert not _right(fig).axis_label

    @pytest.mark.parametrize("mode", MODES)
    def test_no_default_under_by(self, mode, tmp_path):
        obj, _ = _document(mode, tmp_path, _spec(_DUAL, {"by": "g"}))
        rights = [a for f in _figs(mode, obj) for a in f.right
                  if isinstance(a, ContinuousAxis)]
        assert rights
        assert all(not a.axis_label for a in rights), \
            [a.axis_label for a in rights]

    @pytest.mark.parametrize("mode", MODES)
    def test_histogram_on_axis_two(self, mode, tmp_path):
        plots = [{"type": "scatter", "yvar": "y1", "xvar": "x",
                  "options": {}},
                 {"type": "histogram", "var": "x",
                  "options": {"yaxis": "2"}}]
        fig, _ = _fig(mode, tmp_path, plots)
        assert _right(fig).axis_label == "Density"

    @pytest.mark.parametrize("mode", MODES)
    def test_suffix_alone(self, mode, tmp_path):
        fig, _ = _fig(mode, tmp_path, _DUAL, {"ytitle2": ", suffix"})
        assert _right(fig).axis_label == "y2"

    @pytest.mark.parametrize("mode", MODES)
    def test_scheme_style(self, mode, tmp_path):
        sch = dr.SchemeParser()
        props = ("axis_label_text_font_size", "axis_label_text_color",
                 "major_label_text_font_size", "major_label_text_color",
                 "axis_line_color", "axis_line_width")
        ref = LinearAxis()
        sch.apply_to_axis(ref)
        want = [getattr(ref, p) for p in props]
        fig, _ = _fig(mode, tmp_path, _DUAL)
        assert [getattr(_right(fig), p) for p in props] == want
        fig, _ = _fig(mode, tmp_path, _DUAL, {"xtitle": ", size(large)"})
        assert _right(fig).axis_label_text_font_size == \
            ref.axis_label_text_font_size

    def test_parity_under_ylabel_labsize(self, tmp_path):
        got = []
        for mode in MODES:
            fig, _ = _fig(mode, tmp_path, _DUAL,
                          {"ylabel": ", labsize(large)"})
            a = _right(fig)
            got.append([a.axis_label, a.axis_label_text_font_size,
                        a.axis_label_text_color,
                        a.major_label_text_font_size,
                        a.major_label_text_color])
        assert got[0] == got[1]


_AXIS_PROPS = ("axis_line_color", "axis_line_width",
               "axis_label_text_font_size", "major_label_text_font_size",
               "axis_label_text_color", "major_label_text_color")


class TestSchemeApplyToAxis:
    def test_unit(self):
        sch = dr.SchemeParser()
        ax = LinearAxis()
        sch.apply_to_axis(ax)
        assert ax.axis_line_color == sch.axis_line_color
        assert ax.axis_line_width == sch.axis_line_width
        assert ax.axis_label_text_font_size == sch.axis_title_font_size
        assert ax.major_label_text_font_size == sch.tick_label_font_size
        assert ax.axis_label_text_color == sch.axis_title_color
        assert ax.major_label_text_color == sch.tick_label_color
        fig = _FIG()
        sch.apply_to_figure(fig)
        for a in list(fig.xaxis) + list(fig.yaxis):
            assert [getattr(a, p) for p in _AXIS_PROPS] == \
                [getattr(ax, p) for p in _AXIS_PROPS]


# ---------------------------------------------------------------------------
# End to end
# ---------------------------------------------------------------------------
class TestEndToEnd:
    def test_saved_page_document(self, tmp_path):
        sp, dp, _ap = _paths(tmp_path, _spec(_ONE, {"ytitle": ", size(large)"}),
                             make_data_json(_DF))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            page = dr.DashRenderer(sp, dp).render()
        import html as _html
        import re as _re
        found = []
        for blob in _re.findall(
                r'<script type="application/json"[^>]*>(.*?)</script>',
                page, _re.S):
            stack = [json.loads(_html.unescape(blob))]
            while stack:
                v = stack.pop()
                if isinstance(v, dict):
                    if v.get("name") == "LinearAxis":
                        at = v.get("attributes", {})
                        sz = at.get("axis_label_text_font_size")
                        sz = sz.get("value") if isinstance(sz, dict) else sz
                        found.append((at.get("axis_label"), sz))
                    stack.extend(v.values())
                elif isinstance(v, list):
                    stack.extend(v)
        assert ("y1", LARGE) in found, found

    def test_served_app_after_a_filter_move(self, tmp_path):
        spec = _spec(_ONE, {"ytitle": ", size(large)"},
                     filters=[{"var": "y1", "varname": "y1", "type": "range",
                               "exclude": [], "label": ""}])
        doc, _ = _document("served", tmp_path, spec)
        (fig,) = _figs("served", doc)
        assert (_y(fig).axis_label,
                _y(fig).axis_label_text_font_size) == ("y1", LARGE)
        _fire(doc, "y1", (3.0, 12.0))
        assert (_y(fig).axis_label,
                _y(fig).axis_label_text_font_size) == ("y1", LARGE)


class TestLinearTime:
    def test_hostile_commas(self):
        for raw in ("a" + ", " * 200000, "," * 200000):
            t0 = time.perf_counter()
            dr._textbox_split_point(raw)
            dr._textbox_has_text(raw)
            dr._dash_textbox_or_default(raw, "ytitle", "d")
            assert time.perf_counter() - t0 < 2.0

    def test_hostile_double_commas(self):
        t0 = time.perf_counter()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            text, _opts = dr._dash_textbox("," * 200000, "ytitle")
        assert time.perf_counter() - t0 < 2.0
        assert text == ""
        assert not caught, [str(w.message)[:200] for w in caught]


class TestTheServedCopy:
    def test_names(self, tmp_path):
        sp, dp, ap = _paths(tmp_path, _spec(_DUAL), make_data_json(_DF))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(ap)
        with open(ap, encoding="utf-8") as fh:
            src = fh.read()
        assert "def _textbox_has_text(" in src
        assert "def _dash_textbox_or_default(" in src
        import re as _re
        assert _re.search(r"_dash_add_secondary_axes\(fig, plots, go, g_df,"
                          r"\s*_reported_subopts, gname,\s*var_labels, "
                          r"_DASH_SCHEME\)", src)


# ---------------------------------------------------------------------------
# Every new probe of text_truth.json, drawn by dash as twoway draws it
# ---------------------------------------------------------------------------
_AUTO = pd.DataFrame({
    "mpg": [22.0, 17.0, 25.0, 30.0, 21.0, 19.0, 14.0, 28.0, 16.0, 23.0],
    "weight": [2930.0, 3350.0, 2200.0, 1800.0, 3000.0, 3100.0, 4080.0,
               2010.0, 3600.0, 2650.0],
    "price": [4099.0, 4749.0, 3799.0, 4816.0, 5788.0, 4453.0, 5189.0,
              10372.0, 4082.0, 11385.0],
    "length": [186.0, 173.0, 168.0, 196.0, 222.0, 218.0, 170.0, 200.0,
               165.0, 182.0],
    "foreign": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
})
_AUTO_LABELS = {"mpg": "Mileage (mpg)", "weight": "Weight (lbs.)",
                "price": "Price", "length": "Length (in.)"}


def _p(ptype, **kw):
    d = {"type": ptype, "options": kw.pop("options", {})}
    d.update(kw)
    return d


_SC = [_p("scatter", yvar="mpg", xvar="weight")]
_Y2 = [_p("scatter", yvar="mpg", xvar="weight"),
       _p("line", yvar="price", xvar="weight", options={"yaxis": "2"})]
_X2 = [_p("scatter", yvar="mpg", xvar="weight"),
       _p("scatter", yvar="mpg", xvar="length", options={"xaxis": "2"})]
_LONE = [_p("scatter", yvar="mpg", xvar="weight", options={"yaxis": "2"})]
_H = [_p("histogram", var="mpg")]
_HP = [_p("histogram", var="mpg", options={"percent": "percent"})]
_K = [_p("kdensity", var="mpg")]
_HY2 = [_p("scatter", yvar="mpg", xvar="weight"),
        _p("histogram", var="weight", options={"yaxis": "2"})]
_Z = [_p("scatter", yvar="mpg", xvar="weight", options={"colorvar": "price"})]
_ROT, _FLAT = -90.0, None

#: pid: (plots, graph options, axis, expected text (None: removed),
#:       twoway rotation, style: "size", "red" or None)
_PINNED = {
    "t_ytitle_nt_size": (_SC, {"ytitle": ", size(large)"}, "left",
                         "Mileage (mpg)", _ROT, "size"),
    "t_xtitle_nt_color": (_SC, {"xtitle": ", color(red)"}, "below",
                          "Weight (lbs.)", _FLAT, "red"),
    "t_ytitle_nt_c": (_SC, {"ytitle": ", c(red)"}, "left",
                      "Mileage (mpg)", _ROT, "red"),
    "t_ytitle_nt_comma": (_SC, {"ytitle": ","}, "left", "Mileage (mpg)",
                          _ROT, None),
    "t_ytitle_trailing": (_SC, {"ytitle": "A,"}, "left", "A", _ROT, None),
    "t_ytitle_qtrailing": (_SC, {"ytitle": '"A",'}, "left", "A", _ROT, None),
    "t_ytitle_dcomma": (_SC, {"ytitle": "A,,"}, "left", "A", _ROT, None),
    "t_ytitle_spcomma": (_SC, {"ytitle": "A, ,"}, "left", "A", _ROT, None),
    "t_ytitle_size_trailing": (_SC, {"ytitle": "A, size(large),"}, "left",
                               "A", _ROT, "size"),
    "t_ytitle_empty_suffix": (_SC, {"ytitle": '"", suffix'}, "left",
                              "Mileage (mpg)", _ROT, None),
    "t_ytitle_merge_empty_size": (_SC, {"ytitle": '"", size(large)'}, "left",
                                  None, _ROT, None),
    "t_ytitle_merge_size_text": (_SC, {"ytitle": '"A", size(large)'}, "left",
                                 "A", _ROT, "size"),
    "t_ytitle_merge_trailing_size": (_SC, {"ytitle": "A, size(large)"},
                                     "left", "A", _ROT, "size"),
    "t_ytitle_merge_comma_size": (_SC, {"ytitle": ", size(large)"}, "left",
                                  "Mileage (mpg)", _ROT, "size"),
    "t_ytitle_axis2_nt_size": (_Y2, {"ytitle2": ", size(large)"}, "right",
                               "Price", _ROT, "size"),
    "t_ytitle_axis2_suffix": (_Y2, {"ytitle2": ", suffix"}, "right",
                              "Price", _ROT, None),
    "t_xtitle_axis2_nt_size": (_X2, {"xtitle2": ", size(large)"}, "above",
                               "Length (in.)", _FLAT, "size"),
    "t_ytitle_lone_nt_size": (_LONE, {"ytitle2": ", size(large)"}, "left",
                              "Mileage (mpg)", _ROT, "size"),
    "t_y2_hist": (_HY2, {}, "right", "Density", _ROT, None),
    "t_y2_by": (_Y2, {"by": "foreign"}, "right", None, _ROT, None),
    "t_hist_ytitle_nt_size": (_H, {"ytitle": ", size(large)"}, "left",
                              "Density", _ROT, "size"),
    "t_hist_pct_ytitle_nt_size": (_HP, {"ytitle": ", size(large)"}, "left",
                                  "Percent", _ROT, "size"),
    "t_kdens_ytitle_nt_size": (_K, {"ytitle": ", size(large)"}, "left",
                               "kdensity mpg", _ROT, "size"),
    "t_kdens_xtitle_nt_size": (_K, {"xtitle": ", size(large)"}, "below",
                               "x", _FLAT, "size"),
    "t_ztitle_nt_size": (_Z, {"ztitle": ", size(large)"}, "cbar",
                         "Price", _ROT, "size"),
    "t_ztitle_suffix": (_Z, {"ztitle": '"extra", suffix'}, "cbar",
                        "Price\nextra", _ROT, None),
    "t_ztitle_empty": (_Z, {"ztitle": '""'}, "cbar", None, _ROT, None),
}


#: A removal probe's text, which twoway draws in its control and not in it.
_GONE = {"t_ytitle_merge_empty_size": "Mileage (mpg)", "t_y2_by": "Price",
         "t_ztitle_empty": "Price"}


def _records(pid):
    probe = _truth()["probes"][pid]
    return probe, [tuple(r) for r in probe["text_records"]]


def _axis_of(fig, side):
    if side == "cbar":
        (bar,) = fig.select({"type": ColorBar})
        return bar.title, bar.title_text_font_size, bar.title_text_color
    if side in ("right", "above"):
        axes = [a for a in getattr(fig, side) if isinstance(a, ContinuousAxis)]
    else:
        axes = _axes(getattr(fig, side))
    assert axes, side
    return (axes[0].axis_label, axes[0].axis_label_text_font_size,
            axes[0].axis_label_text_color)


class TestTheFixtureIsPinned:
    @pytest.mark.parametrize("pid", sorted(_PINNED))
    def test_dash_draws_what_twoway_draws(self, pid, tmp_path):
        plots, go, side, want, rot, style = _PINNED[pid]
        probe, recs = _records(pid)
        assert probe["rc"] == 0, probe
        # (1) the fixture: twoway's drawing of the probe.
        first = (want or "").split("\n")[0]
        if want is None:
            gone = [r for r in recs if r[3] == rot and r[0] == _GONE[pid]]
            assert not gone, (pid, gone)
            _c, crecs = _records(probe["control"])
            assert [r for r in crecs if r[3] == rot and r[0] == _GONE[pid]]
        else:
            mine = [r for r in recs if r[0] == first and r[3] == rot]
            assert mine, (pid, first, recs)
            if style == "size":
                crecs = (_records(probe["control"])[1] if probe["control"]
                         else [])
                ctl_sizes = [r[1] for r in crecs
                             if r[0] == first and r[3] == rot]
                # No control (the lone axis probe): the scheme's default
                # title size, measured on every other control.
                base = max(ctl_sizes) if ctl_sizes else 112.56
                assert max(r[1] for r in mine) > base, (pid, mine, ctl_sizes)
            if style == "red":
                assert any(r[2] == "#ff0000" for r in mine), (pid, mine)
            if "\n" in want:
                for line in want.split("\n"):
                    assert any(r[0] == line for r in recs), (pid, line)
        # (2) dash, both modes.
        data = make_data_json(_AUTO, variable_labels=_AUTO_LABELS)
        for mode in MODES:
            obj, _ = _document(mode, tmp_path, _spec(plots, go), data)
            figs = _figs(mode, obj)
            assert figs, (pid, mode)
            for fig in figs:
                label, size, colour = _axis_of(fig, side)
                if want is None:
                    assert not label, (pid, mode, label)
                    continue
                assert label == want, (pid, mode, label)
                if style == "size":
                    assert size == LARGE, (pid, mode, size)
                if style == "red":
                    assert colour == "#ff0000", (pid, mode, colour)

