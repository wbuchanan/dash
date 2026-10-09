"""Stata's graph-text markup drawn as twoway draws it (WP-30 P1.11b).

The defect: dash translated no SMCL.  ``title("{bf:Bold} {&alpha} R{sup:2}")``
reached ``Title.text`` unchanged, as did variable and value labels, legend
keys, tick labels, by() panel titles, the colour key, marker labels, filter
titles, dropdown options and tooltip row names, in both modes.

twoway 19.5's grammar (measured, test/fixtures/graph_text_truth.json from
scripts/extract_graph_text_truth.do): a directive is ``{``, optional blanks,
a case-sensitive name, optional blanks, then ``:`` (it wraps text to its
matching ``}``) or ``}`` (a tag holds to the end of the line); unknown tags
and unclosed tags are drawn as typed; the innermost tag wins.  Rulings:
A31 a whole text's style is set only where the markup covers all of it
(one Bokeh text has one style, font and baseline), with one note when it
does not; A32 other SMCL is drawn as typed; A33 the dash-only DOM text
(filter titles, value-label dropdown options, tooltip row names) shows the
characters without style while KPI, tab and dashboard titles, string data
and the CSV stay raw; A34 ("Mirror twoway", ratified 06oct2026, measured
08oct2026) control codes are kept and carried escaped, and ``{c 0}`` cuts
off the rest of its own styled run on its own line.
"""

import ast
import base64
import html
import itertools
import json
import os
import re
import sys
import tempfile
import time
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from bokeh.core.properties import field  # noqa: E402
from bokeh.document import Document  # noqa: E402
from bokeh.models import (ColorBar, CustomJSTickFormatter,  # noqa: E402
                          FixedTicker, HoverTool, Label, LabelSet, Legend,
                          LegendItem, LinearAxis, Select, Title)
from bokeh.plotting import figure  # noqa: E402

from conftest import load_app, make_data_json  # noqa: E402
from js_runner import requires_node  # noqa: E402
from test_label_sinks import (_TEX_DELIM_RE, _TAG_RE, PAYLOADS,  # noqa: E402
                              _build, hostile_inputs, tag)
from test_mode_parity import (_DF, _fire, _sc, _spec,  # noqa: E402
                              _widgets_of)
from test_server_layer_defects import plot_for  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "graph_text_truth.json")
_EXTRACTOR = "scripts/extract_graph_text_truth.do"


def _truth():
    if not os.path.exists(_FIXTURE):
        return None
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _need_truth():
    d = _truth()
    if d is None:
        pytest.fail(f"{_FIXTURE} is missing; run {_EXTRACTOR}")
    return d


# ---------------------------------------------------------------------------
# Building both modes from one spec and its data
# ---------------------------------------------------------------------------

_SEQ = itertools.count()
_TMP = tempfile.mkdtemp(prefix="dash_graph_text_")
_VL = {"origin": {"0": "{it:Dom}", "1": "{&alpha}For"}}
_LN = {"foreign": "origin"}


def _df(ml=None):
    df = _DF.copy()
    df["ml"] = ml or ["{bf:Bx}" if f == 0 else "{&beta}b"
                      for f in df["foreign"]]
    return df


def _data(df, vl=None, ln=None, varlabels=None, strings=("ml",)):
    d = make_data_json(df, _VL if vl is None else vl,
                       _LN if ln is None else ln, varlabels)
    sj = d["StataJSON"]
    for c in strings:
        if c in df.columns:
            sj["variableIsString"][c] = True
            sj["variableTypeIsString"][c] = True
    return d


def _paths(spec, data):
    n = next(_SEQ)
    sp = os.path.join(_TMP, f"spec_{n}.json")
    dp = os.path.join(_TMP, f"data_{n}.json")
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(data, fh)
    return n, sp, dp


def _saved(spec, data):
    """(renderer, warnings, page)."""
    _, sp, dp = _paths(spec, data)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r = dr.DashRenderer(sp, dp)
        page = r.render()
    return r, [str(w.message) for w in caught], page


def _served(spec, data):
    """(document, warnings, source)."""
    n, sp, dp = _paths(spec, data)
    ap = os.path.join(_TMP, f"app_{n}.py")
    with warnings.catch_warnings(record=True) as built:
        warnings.simplefilter("always")
        dr.ServerAppBuilder(sp, dp).build(ap)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mod = load_app(ap, f"_graph_text_app_{n}")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        doc = Document()
        mod.make_document(doc)
    with open(ap, encoding="utf-8") as fh:
        src = fh.read()
    return doc, [str(w.message) for w in list(built) + list(caught)], src


def _models(mode, spec, data):
    """(models, warnings) of one mode's build."""
    if mode == "standalone":
        r, w, _ = _saved(spec, data)
        seen = {}
        for f in r.figures.values():
            for m in f.references():
                seen[id(m)] = m
        for wd in r.filter_widgets:
            seen[id(wd)] = wd
        root = getattr(r, "_last_layout_root", None)
        if root is not None:
            for m in root.references():
                seen[id(m)] = m
        return list(seen.values()), w
    doc, w, _ = _served(spec, data)
    return list(doc.models), w


MODES = ("standalone", "served")


def _of(models, cls):
    return [m for m in models if isinstance(m, cls)]


def _title_texts(models):
    return [m.text for m in _of(models, Title) if m.text]


# ---------------------------------------------------------------------------
# The truth: every fixture row, one test per family
# ---------------------------------------------------------------------------

def _twoway_text(lines):
    """twoway's runs joined, a raised or lowered run mapped through dash's
    Unicode table when every character has a form."""
    out = []
    for runs in lines:
        t = ""
        for r in runs:
            x = r["text"]
            if r["level"]:
                tb = dr._DASH_GT_SUP if r["level"] == "sup" else dr._DASH_GT_SUB
                if all(ch in tb or ch.isspace() for ch in x):
                    x = "".join(tb.get(ch, ch) for ch in x)
            t += x
        out.append(t)
    return "\n".join(out)


def _twoway_style(lines):
    styles = set()
    fams = set()
    for runs in lines:
        for r in runs:
            if r["text"].strip():
                styles.add("bold" if r["weight"] == "bold" else r["style"])
                fams.add(r["family"])
    return styles, fams


def _case_input(case):
    if case["id"].startswith("ml_"):
        return "\n".join(re.findall(r'"([^"]*)"', case["input"]))
    return case["input"]


#: Codes twoway's SVG writer lays out rather than writes (a tab as spaces,
#: a line feed and carriage return as line breaks): dash keeps the
#: character, so the comparison skips them.
_LAYOUT_CODES = {"9", "10", "13"}


class TestGraphTextTruth:

    def test_the_fixture_carries_its_stamp(self):
        d = _need_truth()
        assert {"stata_version", "born_date", "dash_commit", "extracted",
                "c0_rule"} <= set(d["_meta"])
        assert re.fullmatch(r"[0-9a-f]{40}", d["_meta"]["dash_commit"])
        assert (len(d["symbols"]), len(d["chars"]), len(d["stsymbol"])) == (
            148, 255, 88)

    def test_symbols(self):
        d = _need_truth()
        bad = [(k, v, dr._dash_graph_text_plain("{&%s}" % k))
               for k, v in d["symbols"].items()
               if dr._dash_graph_text_plain("{&%s}" % k) != v]
        assert not bad

    def test_char_codes(self):
        d = _need_truth()
        bad = []
        for k, v in d["chars"].items():
            if k in _LAYOUT_CODES:
                continue
            got = dr._dash_graph_text_plain("{c %s}" % k).replace(
                " ", " ")
            if got != v:
                bad.append((k, v, got))
        assert not bad

    def test_char_names(self):
        d = _need_truth()
        bad = [(k, v) for k, v in d["cnames"].items()
               if dr._dash_graph_text_plain("{c %s}" % k) != v]
        assert not bad

    def test_stsymbol(self):
        d = _need_truth()
        bad = [(k, v) for k, v in d["stsymbol"].items()
               if dr._dash_graph_text_plain("{stSymbol:%s}" % k) != v]
        assert not bad

    def test_measured_cases(self):
        """Every graph_text case: twoway's text, and its one style and
        family where it has one."""
        d = _need_truth()
        bad = []
        for case in d["cases"]:
            if case["category"] != "graph_text":
                continue
            plain, style, font, flags = dr._dash_graph_text_parts(
                _case_input(case))
            want = _twoway_text(case["lines"])
            styles, fams = _twoway_style(case["lines"])
            if plain != want:
                bad.append((case["id"], "text", plain, want))
            if len(styles) == 1:
                s0 = next(iter(styles))
                if style != (None if s0 == "normal" else s0):
                    bad.append((case["id"], "style", style, s0))
            elif len(styles) > 1 and (style, "inline" in flags) != (
                    None, True):
                bad.append((case["id"], "inline style", style, flags))
            if len(fams) == 1:
                fam = next(iter(fams))
                ok = (font is None and fam in ("Helvetica", "Symbol")) or (
                    font is not None and fam in font)
                if not ok:
                    bad.append((case["id"], "font", font, fam))
        assert not bad

    def test_documented_differences(self):
        """Other SMCL is drawn as typed (A32); a symbol inside {stSymbol:}
        is drawn as itself (twoway draws its UTF-8 bytes in Symbol)."""
        d = _need_truth()
        bad = []
        for case in d["cases"]:
            got = dr._dash_graph_text_plain(case["input"])
            if case["category"] == "other_smcl" and got != case["input"]:
                bad.append((case["id"], got))
            if case["category"] == "difference" and got != "αβ":
                bad.append((case["id"], got))
        assert not bad
        assert {c["category"] for c in d["cases"]} == {
            "graph_text", "other_smcl", "difference"}


# ---------------------------------------------------------------------------
# The scanner
# ---------------------------------------------------------------------------

class TestTheScanner:

    def test_heads_name_known_directives_only(self):
        h = dr._dash_gt_head
        assert h("bf", ":") == ("open", "style", "bold")
        assert h(" it ", "}") == ("set", "style", "italic")
        assert h("BF", ":") == ("frame",)
        assert h("& alpha", "}") == ("unit",)
        assert h("&alpha", "}") == ("emit", "α")
        assert h("&nosuch", "}") == ("unit",)
        assert h("c 0XE9", "}") == ("unit",)
        assert h("c 256", "}") == ("unit",)
        assert h("c " + "9" * 5000, "}") == ("unit",)
        assert h("c 0x41", "}") == ("emit", "A")
        assert h("c 0", "}") == h("c 00", "}") == h("char 0", "}") == (
            "cut",)
        assert h("c 0x0", "}") == ("unit",)
        assert h("c 1", "}") == ("emit", "\x01")
        assert h("c a:", "}") == ("emit", "ä")
        assert h('fontface "a;(<x>)"', ":") == ("open", "font", "ax")
        assert h("foo", "}") == ("unit",)

    def test_c0_cuts_off_its_own_run(self):
        """``{c 0}`` drops the rest of its styled run on its line; the
        next tag that opens, closes or is set draws again (measured
        08oct2026)."""
        p = dr._dash_graph_text_parts
        assert p("a{c 0}b{bf:c}d") == ("acd", None, None, ("inline",))
        assert p("{bf:a{c 0}b}c")[0] == "ac"
        assert p("a{c 0}{&alpha}b")[0] == "a"
        assert p("{foo:a{c 0}b}c")[0] == "{foo:a"
        assert p("a\nb{c 0}c\nd")[0] == "a\nb\nd"
        assert p("{c 0}x") == ("", None, None, ())
        assert p("{c 0x0}x")[0] == "{c 0x0}x"
        assert p("{c -(}c 0{c )-}x")[0] == "{c 0}x"
        t0 = time.perf_counter()
        assert p("{" * 100000 + "{c 0}x")[0] == "{" * 100000
        assert time.perf_counter() - t0 < 1.0

    def test_whole_style_and_font_only_when_markup_asks(self):
        p = dr._dash_graph_text_parts
        serif = dr._DASH_GT_FONTS["stSerif"]
        assert p("{bf:a}{bf:b}") == ("ab", "bold", None, ())
        assert p("{bf:a}b") == ("ab", None, None, ("inline",))
        assert p("{stSerif:a}{stSerif:b}") == ("ab", None, serif, ())
        assert p("{stSerif:a}b") == ("ab", None, None, ("inline",))
        assert p("{bf:}") == ("", None, None, ())
        assert p("{it:x}\n{it:y}") == ("x\ny", "italic", None, ())
        assert p("{bf}a\nb")[3] == ("inline",)

    def test_sup_and_sub_in_unicode_or_flagged(self):
        p = dr._dash_graph_text_parts
        assert p("R{sup:2}")[0] == "R²"
        assert p("x{sub:1}")[0] == "x₁"
        assert p("{sup:-(n)}")[0] == "⁻⁽ⁿ⁾"
        assert p("x{sub:i}")[::3] == ("xi", ("level",))
        assert p("{sup:{&alpha}}")[::3] == ("α", ("level",))

    def test_lines_are_read_one_by_one(self):
        p = dr._dash_graph_text_parts
        assert p("{bf}a\nb")[0] == "a\nb"
        assert p("{bf:a\nb}")[0] == "{bf:a\nb}"

    def test_fontface_names_are_sanitised(self):
        p = dr._dash_graph_text_parts
        assert p('{fontface "Cour;ier<x>(u)":t}')[2] == "Courierxu"
        assert p('{fontface "%s":t}' % ("a" * 100))[2] == "a" * 64
        assert p('{fontface "":t}')[2] is None
        assert p('{fontface "a}b":t}')[0] == '{fontface "a}b":t}'

    def test_the_result_passes_inert_tex_last(self):
        from bokeh.embed.util import contains_tex_string
        for s in ("{c S|}{c S|}x{c S|}{c S|}", "{c 92}(y{c 92})"):
            got = dr._dash_graph_text(s)[0]
            assert not _TEX_DELIM_RE.search(got), got
            assert not contains_tex_string(got)
        assert dr._dash_graph_text_plain("{c S|}{c S|}x{c S|}{c S|}") == (
            "$$x$$")

    def test_text_without_markup_is_unchanged(self):
        for s in list(PAYLOADS.values()) + [
                "Price $", "{safe} @x $index", "a}b:c{", "{foo} {zz:q}"]:
            assert dr._dash_graph_text_plain(s) == s


class TestLinearTime:

    def test_hostile_text_stays_linear(self):
        shapes = {
            "open": "{" * 100000, "close": "}" * 100000,
            "bf": "{bf:" * 25000,
            "nested": "{bf:" * 10000 + "x" + "}" * 10000,
            "amp": "{&" * 50000, "c": "{c " * 30000,
            "fontface": '{fontface "' * 20000,
            "sup": "{sup:" + "1" * 100000 + "}",
            "mixed": "{bf:a}{&alpha}{c 233}}{:" * 4000,
        }
        slow = {}
        for name, s in shapes.items():
            t0 = time.perf_counter()
            dr._dash_graph_text(s)
            dt = time.perf_counter() - t0
            if dt >= 1.0:
                slow[name] = dt
        t0 = time.perf_counter()
        dr._dash_graph_text("{" * 1000000)
        if time.perf_counter() - t0 >= 5.0:
            slow["million"] = time.perf_counter() - t0
        assert not slow


# ---------------------------------------------------------------------------
# The canvas-text pass
# ---------------------------------------------------------------------------

def _fig():
    return figure(width=200, height=200)


class TestThePass:

    def test_finish_text_runs_returns_each_result(self):
        f = dr._dash_finish_text_runs
        new, ch, res = f("{bf:a}", "text")
        assert (new, ch, res) == ("a", True, [("a", "bold", None, ())])
        new, ch, res = f({1.0: "{&alpha}", 2.0: 3}, "map")
        assert (new, ch, len(res)) == ({1.0: "α", 2.0: 3}, True, 1)
        assert f({"value": "{it:k}"}, "value")[:2] == ({"value": "k"}, True)
        assert f({"field": "{it:k}"}, "value")[:2] == ({"field": "{it:k}"},
                                                       False)
        args = {"labels": json.dumps({"1": "{bf:x}"})}
        new, ch, res = f(args, "labels")
        assert json.loads(new["labels"]) == {"1": "x"} and len(res) == 1
        assert dr._dash_finish_text_value("{bf:a}", "text") == ("a", True)
        assert dr._dash_finish_text_value("plain", "text") == ("plain", False)

    def test_style_is_set_only_where_markup_asks(self):
        fig = _fig()
        fig.title.text = "{bf:T}"
        fig.add_layout(Label(x=0, y=0, text="{it:L}"))
        fig.xaxis.axis_label = "{stMono:x}"
        fig.yaxis.axis_label = "plain"
        cb = ColorBar(title="{bf:c}")
        fig.add_layout(cb, "right")
        lg = Legend(title="{it:g}")
        fig.add_layout(lg)
        before_y = fig.yaxis[0].axis_label_text_font_style
        dr._dash_finish_graph_text({"g": fig})
        lab = _of(fig.center, Label)[0]
        assert (fig.title.text, fig.title.text_font_style) == ("T", "bold")
        assert (lab.text, lab.text_font_style) == ("L", "italic")
        assert fig.xaxis[0].axis_label_text_font == dr._DASH_GT_FONTS[
            "stMono"]
        assert cb.title_text_font_style == "bold"
        assert lg.title_text_font_style == "italic"
        assert fig.yaxis[0].axis_label_text_font_style == before_y

    def test_tick_labels_take_a_style_only_when_every_tick_shares_it(self):
        def run(overrides, counted=False):
            fig = _fig()
            ax = fig.xaxis[0]
            ax.ticker = FixedTicker(ticks=[1, 2])
            ax.major_label_overrides = overrides
            if counted:
                fig._dash_count_entries = [{"ax": ax}]
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                dr._dash_reset_notes()
                dr._dash_finish_graph_text({"g": fig})
            return ax.major_label_text_font_style, [str(x.message) for x in w]
        assert run({1: "{bf:a}", 2: "{bf:b}"}) == ("bold", [])
        style, notes = run({1: "{bf:a}", 2: "b"})
        assert style == "normal" and "part of a tick label" in notes[0]
        assert run({1: "{bf:a}", 2: "{bf:b}"}, counted=True)[0] == "normal"

    def test_legend_keys_take_a_style_only_when_every_key_shares_it(self):
        def run(a, b):
            fig = _fig()
            r = fig.scatter([1], [1])
            lg = Legend(items=[LegendItem(label=a, renderers=[r]),
                               LegendItem(label=b, renderers=[r])])
            fig.add_layout(lg)
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                dr._dash_reset_notes()
                dr._dash_finish_graph_text({"g": fig})
            return (lg.label_text_font_style, [it.label.value
                                               for it in lg.items],
                    len(w))
        assert run("{it:a}", "{it:b}") == ("italic", ["a", "b"], 0)
        assert run("{it:a}", "b") == ("normal", ["a", "b"], 1)

    def test_a_translated_model_is_never_translated_again(self):
        fig = _fig()
        fig.title.text = "{c -(}bf:x{c )-}"
        before = fig.title.text_font_style
        dr._dash_finish_graph_text({"a": fig, "b": fig})
        dr._dash_finish_graph_text({"a": fig})
        assert (fig.title.text, fig.title.text_font_style) == ("{bf:x}",
                                                               before)

    def test_tooltip_row_names_are_plain_text(self):
        fig = _fig()
        ht = HoverTool(tooltips=[("{&mu} mpg", "@{mpg}")])
        fig.add_tools(ht)
        tpl = HoverTool(tooltips="<b>{&mu}</b> @x")
        fig.add_tools(tpl)
        dr._dash_finish_graph_text({"g": fig})
        assert list(map(tuple, ht.tooltips)) == [("μ mpg", "@{mpg}")]
        assert getattr(ht, dr._DASH_GRAPH_TEXT_DONE)
        assert tpl.tooltips == "<b>{&mu}</b> @x"

    def test_hover_fields_and_other_models_are_left_alone(self):
        from bokeh.models import CategoricalColorMapper, ColumnDataSource
        fig = _fig()
        src = ColumnDataSource({"x": [1], "y": [1], "c": ["{bf:x}"]})
        r = fig.scatter("x", "y", source=src, name="{bf:x}")
        cm = CategoricalColorMapper(factors=["{bf:x}"], palette=["red"])
        ls = LabelSet(x="x", y="y", text="c", source=src)
        fig.add_layout(ls)
        ht = HoverTool(tooltips=[("a", "@{c}{bf:x}")])
        fig.add_tools(ht)
        fmt = CustomJSTickFormatter(code="return tick",
                                    args={"fmt": "{bf:x}", "kind": "",
                                          "storage": ""})
        fig.xaxis[0].formatter = fmt
        dr._dash_finish_graph_text({"g": fig})
        assert r.name == "{bf:x}" and cm.factors == ["{bf:x}"]
        assert list(src.data["c"]) == ["{bf:x}"] and ls.text == "c"
        assert list(map(tuple, ht.tooltips)) == [("a", "@{c}{bf:x}")]
        assert fmt.args["fmt"] == "{bf:x}"


# ---------------------------------------------------------------------------
# Notes
# ---------------------------------------------------------------------------

def _gt_notes(ws):
    return [w for w in ws if "Text in graphs" in w]


class TestTheNote:

    def test_one_note_per_graph_and_kind_naming_no_user_text(self):
        spec = _spec([_sc()], graph_options={
            "title": '"{bf:QZQ}x"', "xlabel": '3000 "{bf:QZQ}" 4000',
            "by": "foreign"})
        got = {}
        for mode in MODES:
            _, ws = _models(mode, spec, _data(_df()))
            notes = sorted(_gt_notes(ws))
            assert len(notes) == 2, notes
            assert all(n.startswith("dash: graph 'g1': ") for n in notes)
            assert not any("QZQ" in n for n in notes)
            assert any("part of a title" in n for n in notes)
            assert any("part of a tick label" in n for n in notes)
            got[mode] = notes
        assert got["standalone"] == got["served"]

    def test_no_note_for_whole_text_markup(self):
        spec = _spec([_sc()], graph_options={"title": '"{bf:Whole}"'})
        _, ws = _models("standalone", spec, _data(_df()))
        assert _gt_notes(ws) == []


# ---------------------------------------------------------------------------
# Every sink, both modes
# ---------------------------------------------------------------------------

_SINK_PAYLOAD = "{&alpha}{c 233}R{sup:2}{c -(}{c )-}{c S|}"
_SINK_WANT = "αéR²{}$"
_TRANSLATED = {"Title", "Label", "LinearAxis", "LogAxis", "DatetimeAxis",
               "ColorBar", "LegendItem", "Legend", "Select", "Slider",
               "RangeSlider", "DateSlider", "DateRangeSlider",
               "DatetimeRangeSlider", "HoverTool"}
_RAW = {"TabPanel", "CustomJS", "CategoricalColorMapper", "GlyphRenderer"}


@pytest.fixture(scope="module")
def sink_builds(tmp_path_factory):
    root = tmp_path_factory.mktemp("graph_text_sinks")
    cache = {}

    def get(mode, payload=_SINK_PAYLOAD):
        if (mode, payload) not in cache:
            cache[(mode, payload)] = _build(
                root, mode, "safe", inputs=hostile_inputs(payload))
        return cache[(mode, payload)]
    return get


class TestEverySinkBothModes:

    @pytest.mark.parametrize("mode", MODES)
    def test_every_canvas_and_dom_sink_draws_the_translation(
            self, sink_builds, mode):
        """Canvas, legend, widget-title, value-label option and tooltip
        sinks hold the translation; HTML, tabs, string data, callback args
        and identifiers hold the raw text."""
        b = sink_builds(mode)
        bad = []
        for c in b.carriers:
            if c.prop == "options.value":
                continue
            if c.kind == "Select" and c.prop == "options.label":
                sid = _TAG_RE.search(c.text).group(1)
                want_raw = sid.startswith("sv")
            elif c.kind in _TRANSLATED:
                want_raw = False
            elif c.kind in _RAW:
                want_raw = True
            else:
                continue
            raw_in = _SINK_PAYLOAD in c.text or "{c " in c.text
            if want_raw != raw_in or (not want_raw
                                      and _SINK_WANT not in c.text):
                bad.append((c.kind, c.prop, c.text))
        assert not bad
        derived = [m.data.get("__dash_mlabel_make") for m in b.models
                   if type(m).__name__ == "ColumnDataSource"
                   and "__dash_mlabel_make" in m.data]
        assert derived and all(_SINK_WANT in str(v) for v in derived[0])
        fmts = [m for m in b.models if isinstance(m, CustomJSTickFormatter)
                and "labels" in (m.args or {})]
        for m in fmts:
            assert all(_SINK_PAYLOAD not in v for v in
                       json.loads(m.args["labels"]).values())

    @pytest.mark.parametrize("mode", MODES)
    def test_whole_text_style_reaches_each_sink(self, mode):
        spec = _spec([_sc(colorvar="price")], graph_options={
            "title": '"{bf:T}"', "subtitle": '"{it:S}"',
            "xtitle": '"{stSerif:X}"', "ztitle": '"{bf:Z}"'})
        models, _ = _models(mode, spec, _data(_df()))
        titles = {m.text: m.text_font_style for m in _of(models, Title)}
        assert titles.get("T") == "bold" and titles.get("S") == "italic"
        axes = [a for a in _of(models, LinearAxis) if a.axis_label == "X"]
        assert axes and axes[0].axis_label_text_font == dr._DASH_GT_FONTS[
            "stSerif"]
        bars = [c for c in _of(models, ColorBar) if c.title == "Z"]
        assert bars and bars[0].title_text_font_style == "bold"

    @pytest.mark.parametrize("mode", MODES)
    def test_by_panel_labels_and_overall_text_are_translated(self, mode):
        """WP-30 P1.15a's by() sinks: panel labels from value labels and
        by()'s own title, subtitle, note and caption."""
        spec = _spec([_sc()], graph_options={
            "by": 'foreign, title("{bf:X}") subtitle("{&alpha}s") '
                  'note("{it:N}") caption("c{sup:2}")'})
        models, _ = _models(mode, spec, _data(_df()))
        got = {(m.text, m.text_font_style) for m in _of(models, Title)
               if m.text}
        assert {("Dom", "italic"), ("\u03b1For", "normal"), ("X", "bold"),
                ("\u03b1s", "normal"), ("N", "italic"),
                ("c\u00b2", "normal")} <= got, got

    @pytest.mark.parametrize("mode", MODES)
    def test_no_model_needs_mathjax(self, sink_builds, mode):
        from bokeh.embed.bundle import _model_requires_mathjax
        b = sink_builds(mode, "{c S|}{c S|}x{c S|}{c S|}")
        assert not [m for m in b.models if _model_requires_mathjax(m)]
        if mode == "standalone":
            assert "bokeh-mathjax" not in b.html


# ---------------------------------------------------------------------------
# Control codes at every sink (rule 1, TR-29.19)
# ---------------------------------------------------------------------------

_CTRL_PAYLOAD = ("a{c 1}b{c 27}c{c 127}d{c 129}e{c 157}f"
                 + "\x85\x9b  "
                 + "</script><script>alert(1)</script>\"'"
                 + "\\u0022" + "<img src=x onerror=alert(2)>")
_CTRL_RE = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f  ]")


def _ctrl_want(payload=_CTRL_PAYLOAD):
    d = _need_truth()
    out = payload
    for n in ("1", "27", "127", "129", "157"):
        out = out.replace("{c %s}" % n, d["chars"][n])
    return out


def _ctrl_spec(payload, layout="auto"):
    q = payload.replace('"', "")
    spec = _spec([_sc(mlabel="ml"), plot_for("lfit")],
                 {"filter": "foreign, type(dropdown)", "layout": layout},
                 {"title": '"%s"' % q, "xtitle": '"%s"' % q,
                  "xlabel": '3000 "%s" 4000' % q,
                  "legend": 'label(1 "%s")' % q, "hover": "price"})
    df = _df([payload] * len(_DF))
    data = _data(df, {"origin": {"0": payload, "1": "B"}},
                 varlabels={"price": payload})
    return spec, data


def _page_json(page, layout):
    if layout == "auto":
        m = re.search(r'<script type="application/json"[^>]*>(.*?)</script>',
                      page, re.S)
        return json.loads(html.unescape(m.group(1)))
    m = re.search(r"const docs_json = '(.*?)';", page, re.S)
    raw = m.group(1).replace("&#x27;", "'").replace("\\\\", "\\")
    return json.loads(html.unescape(raw))


def _json_strings(v):
    if isinstance(v, str):
        yield v
    elif isinstance(v, dict):
        for x in v.values():
            yield from _json_strings(x)
    elif isinstance(v, list):
        for x in v:
            yield from _json_strings(x)


_CTRL_LAYOUTS = {"default": "auto", "layout": "bs: g1=12"}


class TestControlCodesAreEscapedAtEverySink:

    @pytest.mark.parametrize("which", sorted(_CTRL_LAYOUTS))
    def test_the_saved_page_holds_no_raw_control_and_no_injected_script(
            self, which):
        lay = _CTRL_LAYOUTS[which]
        _, _, page = _saved(*_ctrl_spec(_CTRL_PAYLOAD, lay))
        _, _, plain = _saved(*_ctrl_spec("x", lay))
        assert not _CTRL_RE.search(page)
        assert page.count("<script") == plain.count("<script")
        assert "<script>alert" not in page and "<img src=x" not in page
        for m in re.finditer(r"alert\(1\)", page):
            assert page[:m.start()].endswith("script&gt;")

    @pytest.mark.parametrize("which", sorted(_CTRL_LAYOUTS))
    def test_the_saved_document_json_decodes_to_the_mirrored_text(
            self, which):
        lay = _CTRL_LAYOUTS[which]
        _, _, page = _saved(*_ctrl_spec(_CTRL_PAYLOAD, lay))
        docs = _page_json(page, "auto" if which == "default" else "layout")
        strings = set(_json_strings(docs))
        want = _ctrl_want()
        want_q = _ctrl_want(_CTRL_PAYLOAD.replace('"', ""))
        assert want_q in strings          # title, axis title, tick, key
        assert want in strings            # mlabel column, option label
        assert ("α" not in want) and "{c 1}" not in want

    def test_the_tick_label_map_is_valid_json_with_escaped_codes(self):
        spec, data = _ctrl_spec(_CTRL_PAYLOAD)
        r, _, _ = _saved(spec, data)
        want = _ctrl_want(_CTRL_PAYLOAD.replace('"', ""))
        maps = []
        for f in r.figures.values():
            for m in f.references():
                if isinstance(m, CustomJSTickFormatter) and "labels" in (
                        m.args or {}):
                    maps.append(m.args["labels"])
        axes_over = [v for f in r.figures.values() for a in f.xaxis
                     for v in a.major_label_overrides.values()]
        # The map is json.dumps (ensure_ascii): ASCII, valid JSON; the page
        # then HTML-escapes it with the rest of the document (above).
        for raw in maps:
            assert raw.isascii()
            assert want in json.loads(raw).values()
        assert maps or want in axes_over

    def test_the_served_wire_json_is_escaped(self):
        from bokeh.core.json_encoder import serialize_json
        doc, _, _ = _served(*_ctrl_spec(_CTRL_PAYLOAD))
        wire = serialize_json(doc.to_json())
        assert wire.isascii()
        strings = set(_json_strings(json.loads(wire)))
        assert _ctrl_want(_CTRL_PAYLOAD.replace('"', "")) in strings
        assert _ctrl_want() in strings

    def test_the_served_app_source_holds_no_raw_control(self):
        _, _, src = _served(*_ctrl_spec(_CTRL_PAYLOAD))
        tree = ast.parse(src)
        assert not _CTRL_RE.search(src)
        assert "</script><script>alert" not in src
        consts = {}
        for node in tree.body:
            if (isinstance(node, ast.Assign) and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id.startswith("_DASH_GT_")):
                consts[node.targets[0].id] = ast.literal_eval(node.value)
        for name, val in consts.items():
            assert val == getattr(dr, name), name
        assert len(consts) == 8
        b64 = re.search(r'^_SPEC_B64 = "([A-Za-z0-9+/=]+)"', src, re.M)
        spec = json.loads(base64.b64decode(b64.group(1)).decode("utf-8"))
        assert spec["graphs"][0]["graph_options"]["title"] == (
            '"%s"' % _CTRL_PAYLOAD.replace('"', ""))

    def test_dash_written_html_escapes_quotes_and_script(self):
        frags = "".join(dr._dash_header_fragments(_CTRL_PAYLOAD,
                                                  _CTRL_PAYLOAD))
        card = dr._dash_kpi_card_html(_CTRL_PAYLOAD, "1", _CTRL_PAYLOAD,
                                      "", "", "k1",
                                      dr.SchemeParser("s2color"))
        for h in (frags, card):
            assert "&lt;/script&gt;" in h and "</script>" not in h
            assert "&quot;" in h and "&#x27;" in h
            assert "{c 1}" in h

    def test_notes_hold_no_control_character(self):
        _, ws, _ = _saved(*_ctrl_spec(_CTRL_PAYLOAD))
        _, ws2, _ = _served(*_ctrl_spec(_CTRL_PAYLOAD))
        for w in ws + ws2:
            assert not _CTRL_RE.search(w) and "alert(" not in w, w


# ---------------------------------------------------------------------------
# Marker labels
# ---------------------------------------------------------------------------

def _labelsets(models):
    return [m for m in _of(models, LabelSet)]


class TestMarkerLabels:

    @pytest.mark.parametrize("mode", MODES)
    def test_a_string_variable_is_drawn_translated(self, mode):
        models, _ = _models(mode, _spec([_sc(mlabel="ml")]),
                            _data(_df()))
        ls = _labelsets(models)[0]
        assert ls.text == "__dash_mlabel_ml"
        assert ls.text_font_style == field("__dash_mlabstyle_ml")
        d = ls.source.data
        assert set(d["__dash_mlabel_ml"]) == {"βb", "Bx"}
        assert {(t, s) for t, s in zip(d["__dash_mlabel_ml"],
                                       d["__dash_mlabstyle_ml"])} == {
            ("βb", "normal"), ("Bx", "bold")}

    @pytest.mark.parametrize("mode", MODES)
    def test_value_labels_are_drawn_translated(self, mode):
        models, _ = _models(mode, _spec([_sc(mlabel="foreign")]),
                            _data(_df()))
        ls = _labelsets(models)[0]
        d = ls.source.data
        assert set(zip(d["__dash_mlabel_foreign"],
                       d["__dash_mlabstyle_foreign"])) == {
            ("Dom", "italic"), ("αFor", "normal")}

    @pytest.mark.parametrize("mode", MODES)
    def test_immediate_labels_are_drawn_translated(self, mode):
        si = plot_for("scatteri")
        si["values"] = [[2.0, 2.0, "{&beta}imm", 12],
                        [4.0, 3.0, "{bf:Bimm}", 12]]
        pa = plot_for("pcarrowi")
        pa["values"] = [[1.0, 1.0, 2.0, 2.0, "{&gamma}arr", 3]]
        spec = _spec(graphs=[("g1", [si], {}, {}), ("g2", [pa], {}, {})])
        models, _ = _models(mode, spec, _data(_df()))
        texts = set()
        for ls in _labelsets(models):
            texts |= {str(t) for t in ls.source.data[ls.text]}
        assert {"βimm", "Bimm", "γarr"} <= texts, texts

    def test_the_decision_reads_the_whole_dataset(self):
        ml = ["{&beta}b" if f == 1 else "plain" for f in _DF["foreign"]]
        spec = _spec([_sc(mlabel="ml")], graph_options={"by": "foreign"})
        for mode in MODES:
            models, _ = _models(mode, spec, _data(_df(ml)))
            names = {ls.text for ls in _labelsets(models)}
            assert names == {"__dash_mlabel_ml"}, (mode, names)

    def test_each_distinct_label_is_translated_once(self, monkeypatch):
        m = dr.GlyphMapper.__new__(dr.GlyphMapper)
        texts = ["{bf:x%d}" % (i % 1000) for i in range(10000)]
        calls = []
        real = dr._dash_graph_text

        def counting(t):
            calls.append(t)
            return real(t)
        monkeypatch.setattr(dr, "_dash_graph_text", counting)
        out, styles = m._mlabel_markup_rows(texts)
        assert len(calls) == 1000 and out[1] == "x1" and styles[1] == "bold"
        m._mlabel_markup_rows(texts)
        assert len(calls) == 1000

    def test_a_column_already_derived_is_not_translated_again(self):
        ml = ["{c -(}bf:x{c )-}"] * len(_DF)
        spec = _spec([_sc(mlabel="ml"), _sc(mlabel="ml", msymbol="d")])
        r, _, _ = _saved(spec, _data(_df(ml)))
        sets = [m for f in r.figures.values() for m in f.references()
                if isinstance(m, LabelSet)]
        assert len(sets) == 2
        for ls in sets:
            assert set(ls.source.data[ls.text]) == {"{bf:x}"}
            assert "__dash_mlabstyle_ml" not in ls.source.data

    def test_no_markup_no_new_column(self):
        ml = ["a", "b"] * (len(_DF) // 2)
        for mode in MODES:
            models, _ = _models(mode, _spec([_sc(mlabel="ml")]),
                                _data(_df(ml)))
            ls = _labelsets(models)[0]
            assert ls.text == "ml"
            assert not [c for c in ls.source.data
                        if c.startswith(("__dash_mlabel_",
                                         "__dash_mlabstyle_"))]


class TestAfterAFilterMove:

    @requires_node
    def test_saved_marker_labels_after_the_move(self):
        from test_saved_filter_layers import _run
        spec = _spec([_sc(mlabel="ml")],
                     {"filter": "foreign, type(dropdown)"})
        r, _, _ = _saved(spec, _data(_df()))
        w = [x for x in r.filter_widgets if isinstance(x, Select)][0]
        w.value = [v for v, lab in w.options if lab == "αFor"][0]
        cb = r.filter_callbacks[r.filter_widgets.index(w)]
        _run(cb.code, cb.args)
        ls = [m for f in r.figures.values() for m in f.references()
              if isinstance(m, LabelSet)][0]
        d = ls.source.data
        assert list(d["__dash_mlabel_ml"]) == ["βb"] * 5
        assert list(d["__dash_mlabstyle_ml"]) == ["normal"] * 5

    def test_a_served_move_keeps_the_translated_column(self):
        ml = ["{bf:B}" if f == 1 else "plain" for f in _DF["foreign"]]
        spec = _spec([_sc(mlabel="ml")],
                     {"filter": "foreign, type(dropdown)"})
        doc, _, _ = _served(spec, _data(_df(ml)))
        w = [x for x in _widgets_of(doc) if isinstance(x, Select)][0]
        ls = _of(list(doc.models), LabelSet)[0]
        for lab in ("Dom", "αFor", "All"):
            raw = [v for v, t in w.options if t == lab]
            _fire(w, raw[0])
            ls = _of(list(doc.models), LabelSet)[0]
            assert {"__dash_mlabel_ml", "__dash_mlabstyle_ml"} <= set(
                ls.source.data), lab

    @pytest.mark.parametrize("mode", MODES)
    def test_canvas_style_survives_a_move(self, mode):
        spec = _spec([_sc(), plot_for("lfit")],
                     {"filter": "foreign, type(dropdown)"},
                     {"title": '"{bf:T}"',
                      "legend": 'label(2 "{it:k}")'})
        data = _data(_df())
        if mode == "standalone":
            from test_saved_filter_layers import _run
            r, _, _ = _saved(spec, data)
            w = [x for x in r.filter_widgets if isinstance(x, Select)][0]
            w.value = [v for v, t in w.options if t == "Dom"][0]
            cb = r.filter_callbacks[r.filter_widgets.index(w)]
            if requires_node.args[0]:
                pytest.skip("node is not installed")
            _run(cb.code, cb.args)
            models = [m for f in r.figures.values() for m in f.references()]
        else:
            doc, _, _ = _served(spec, data)
            w = [x for x in _widgets_of(doc) if isinstance(x, Select)][0]
            _fire(w, [v for v, t in w.options if t == "Dom"][0])
            models = list(doc.models)
        t = [m for m in _of(models, Title) if m.text == "T"]
        assert t and t[0].text_font_style == "bold"
        keys = [i.label.value for i in _of(models, LegendItem)]
        assert any(k.startswith("k") for k in keys), keys


# ---------------------------------------------------------------------------
# The dash-only DOM sinks
# ---------------------------------------------------------------------------

class TestDomSinks:

    def test_filter_titles_show_the_characters(self):
        t = dr._dash_filter_title
        assert t("{&mu} mpg", "v", "dropdown") == "μ mpg"
        assert t("{&mu} mpg", "v", "range") == "μ mpg"
        assert t("{&mu} mpg", "v", "slider") == "μ mpg ≥"
        assert not _TEX_DELIM_RE.search(t("{bf:$$x$$}", "v", "range"))
        assert t("{bf:$$x$$}", "v", "dropdown") == "$$x$$"

    def test_dropdown_options_from_value_labels_show_the_characters(self):
        w = dr._dash_filter_widget("dropdown", "foreign", [0.0, 1.0], "t",
                                   {"0": "{it:Dom}", "1": "{&alpha}For"})[0]
        assert [lab for _, lab in w.options] == ["All", "Dom", "αFor"]
        s = dr._dash_filter_widget("dropdown", "s", ["{bf:a}", "b"], "t")[0]
        assert "{bf:a}" in [lab for _, lab in s.options]

    def test_string_values_kpis_tabs_and_titles_stay_raw(self, sink_builds):
        b = sink_builds("standalone")
        divs = " ".join(c.text for c in b.carriers if c.kind == "Div")
        for sid in ("ktitle", "ksub", "dtitle", "dsub"):
            assert tag(sid) + html.escape(_SINK_PAYLOAD) in divs, sid
        tabs = [c.text for c in b.carriers if c.kind == "TabPanel"]
        assert tabs and all("{c " in t for t in tabs)
        csv_cols = [c.text for c in b.carriers
                    if c.kind == "ColumnDataSource"
                    and re.match(r"QZsv[0-9]+ZQ", c.text)]
        assert any(_SINK_PAYLOAD in t for t in csv_cols)

    def test_plain_text_strips_style_and_keeps_tex(self):
        assert dr._dash_graph_text_plain("{bf:a}\\(b\\)") == "a\\(b\\)"


class TestTheServedApp:

    def test_the_translator_travels_by_source(self):
        _, _, src = _served(_spec([_sc()]), _data(_df()))
        import inspect
        for name in ("_dash_gt_char", "_dash_gt_head",
                     "_dash_graph_text_runs", "_dash_graph_text_parts",
                     "_dash_graph_text", "_dash_graph_text_plain",
                     "_dash_finish_text_runs", "_dash_graph_text_style",
                     "_dash_graph_text_note"):
            assert inspect.getsource(getattr(dr, name)) in src, name
        for name in ("_DASH_GT_SYMBOLS", "_DASH_GT_CNAMES",
                     "_DASH_GT_STSYMBOL", "_DASH_GT_SUP", "_DASH_GT_SUB",
                     "_DASH_GT_FONTS", "_DASH_GT_TAGS",
                     "_DASH_GT_STYLE_PROPS", "_DASH_MLABSTYLE_PREFIX"):
            assert re.search(r"^%s = " % name, src, re.M), name


# ---------------------------------------------------------------------------
# In Chrome
# ---------------------------------------------------------------------------

_PROBE = r"""
<script>
(function () {
  function done(res) {
    const pre = document.createElement("pre");
    pre.id = "r";
    pre.textContent = JSON.stringify(res);
    document.body.appendChild(pre);
  }
  function deep(root, sel, out) {
    for (const el of root.querySelectorAll(sel)) out.push(el);
    for (const el of root.querySelectorAll("*"))
      if (el.shadowRoot) deep(el.shadowRoot, sel, out);
    return out;
  }
  function wait(n) {
    if ((!window.Bokeh || !window.Bokeh.documents ||
         !window.Bokeh.documents.length ||
         !deep(document, "option", []).length) && n < 80) {
      setTimeout(function () { wait(n + 1); }, 100);
      return;
    }
    setTimeout(function () {
      const opts = deep(document, "option", []).map((o) => o.textContent);
      const legend = [];
      for (const doc of window.Bokeh.documents)
        for (const m of doc.all_models)
          if (m.type === "Legend") legend.push(m.label_text_font_style);
      done({options: opts, legend: legend,
            pwned: typeof window.__dash_pwned,
            scripts: document.scripts.length});
    }, 800);
  }
  wait(0);
})();
</script>
"""


def _chrome_page(spec, data):
    import responsive_probe
    _, _, page = _saved(spec, data)
    return responsive_probe.admit_script(page, _PROBE), page


def _chrome():
    import responsive_probe
    if responsive_probe.find_chrome() is None:
        pytest.skip("headless Chrome is not installed; set DASH_CHROME "
                    "(a skip is red under DASH_STRICT=1)")
    from test_stale_cue_browser import _run_chrome
    return _run_chrome


class TestInChrome:

    def test_the_page_shows_the_translated_text(self):
        run = _chrome()
        spec = _spec([_sc(), plot_for("lfit")],
                     {"filter": "foreign, type(dropdown)"},
                     {"title": '"{&alpha}"',
                      "legend": 'label(1 "{it:a}") label(2 "{it:b}")'})
        page, _ = _chrome_page(spec, _data(_df()))
        got = run(page)
        assert "αFor" in got["options"], got
        assert got["legend"] == ["italic"], got

    def test_control_codes_and_script_text_stay_text(self):
        run = _chrome()
        payload = _CTRL_PAYLOAD.replace("alert(1)", "window.__dash_pwned=1")
        payload = payload.replace("alert(2)", "window.__dash_pwned=1")
        page, raw = _chrome_page(*_ctrl_spec(payload))
        got = run(page)
        assert got["pwned"] == "undefined", got
        assert got["scripts"] == page.count("<script"), got
        assert any("\x01" in o and "</script>" in o
                   for o in got["options"]), got


# ---------------------------------------------------------------------------
# The help
# ---------------------------------------------------------------------------

class TestTheHelp:

    def test_the_help_documents_text_in_graphs(self):
        with open(os.path.join(_ROOT, "dash.sthlp"), encoding="utf-8") as fh:
            src = fh.read()
        at = src.index("{ul:Text in graphs.}")
        end = src.index("{ul:Tooltips.}")
        assert at < end
        para = src[at:end]
        for need in ("{help graph_text}", "one note", "drawn as typed",
                     "is cut off", "escaped text",
                     "keep the text as it is stored"):
            assert need in para, need
        assert "left out" not in para
