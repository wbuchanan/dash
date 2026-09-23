"""dash.sthlp's Option values, Subcommands, Dashboard Options and Exporting.

ROADMAP WP-23 (AC-23.1, TR-23.3) / GAPS.md F4.  Every claim dash.sthlp makes
between ``{marker validation}`` and ``{marker layout}`` (lines 317-585 at
4ede074) is either pinned by an existing test, by
``test_help_claims_2.cscript`` (the Stata half: every refusal, every twoway
measurement, the browser rule, dash clear, export delimited), or here, in
both render modes: the saved page (``DashRenderer``) and the served app
(``ServerAppBuilder`` + ``make_document``).

What was measured false in the help, and is corrected there (each pinned by
``TestTheHelpSaysWhatWasMeasured`` against the corrected text):

* ``msize(1e400)`` "is refused as twoway refuses it" -- twoway accepts it
  (rc 0); it refuses ``msize(1e308)``, "invalid syntax".
* ``mlabel(L.mpg)``, "which twoway draws" -- twoway refuses it, r(111)
  "variable L not found".
* "Two values twoway refuses, dash accepts" -- there are more: every style
  option given ``(())``, a string ``colorvar()`` (twoway r(7)) and a colour
  written with commas, ``mcolor(255,0,0)`` (twoway r(198)).
* "scheme() and theme() are refused where twoway draws s2color with a note"
  -- twoway has no ``theme()``; ``option theme() not allowed``.
* ``start()`` "any number" -- on histogram a start() above the variable's
  minimum is refused with twoway's own message.
* The dash-own bounds were listed as if complete; four forms twoway reads
  are refused and were not named: ``mlabel()`` with two variables,
  ``range(varname)``, a ``.`` in ``range()``, and a width or angle bound on
  a plot type that does not draw what it styles.
* "Colours, msymbol(), lpattern(), scheme() ... are not checked in Stata" --
  scheme() is (WP-17).
* Value labels "for categorical tick labels ... and legend entries" -- an
  axis never shows value labels (as in twoway), and the only legend that
  does is a discrete ``colorvar()``'s.
* ``dash serve``: "Unlike standalone HTML, the server recalculates
  aggregated layers ... and KPI values" -- a saved dashboard recomputes its
  KPI values, kernel densities and histogram bar heights too.
* ``dash serve`` "accepts every option dash build accepts" -- saving(),
  replace and server are named in a note and ignored.
* ``dash clear`` "Drops all $dash_* global macros" -- it keeps
  ``$dash_nobrowser`` and the ``$dash_max_*`` limits.
* The CSV "is written as Stata's export delimited writes one, with these
  differences" -- three were missing: CR LF line ends, an extended missing
  value written empty, and the spelling of a number; and its columns are in
  the order the dashboard names them, not the dataset's.
* ``$dash_nobrowser`` had no definition (TR-23.3).

And one claim was true of twoway and false of dash, fixed in the code:
"An unknown style inside one (title(T, size(bogus))) gets a note and the
default in twoway and in dash alike".  In dash an unknown size() or color()
inside title(), xtitle() or ytitle() was named ("ignoring it") and then
replaced the scheme's default with a literal -- 16px or 13px, and #000000,
which under s1rcolor drew the title black on black
(``TestAnUnknownStyleInsideAStructuredOption``; _dash_figure_title and
_dash_style_axis_titles in dash_render.py, shared by both modes).
"""
import json
import os
import re
import runpy
import subprocess
import sys
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.events import ButtonClick
from bokeh.models import (CategoricalColorMapper, ColumnDataSource, Div,
                          HoverTool, LabelSet, Legend, Select)

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_HELP = os.path.join(_ROOT, "dash.sthlp")


# ---------------------------------------------------------------------------
# Rendering one spec in both modes, over data of the test's own
# ---------------------------------------------------------------------------

_DF = pd.DataFrame({
    "mpg": [22.0, 17.0, 25.0, 30.0, 21.0, 19.0, 14.0, 28.0, 16.0, 23.0],
    "weight": [2930.0, 3350.0, 2200.0, 1800.0, 3000.0, 3100.0, 4080.0,
               2010.0, 3600.0, 2650.0],
    "foreign": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
    "price": [4099.0, 4749.0, 3799.0, 4816.0, 5788.0, 4453.0, 5189.0,
              10372.0, 4082.0, 11385.0],
    "make": ["AMC", "Audi", "Buick", "BMW", "Chev", "Datsun", "Dodge",
             "Fiat", "Ford", "Honda"],
})
_VARLABELS = {"mpg": "Mileage (mpg)", "weight": "Weight (lbs.)",
              "foreign": "Car origin", "price": "Price", "make": "Make"}
_VALLABELS = {"origin": {"0": "Domestic", "1": "Foreign"}}
_VLNAMES = {"foreign": "origin"}
_ATTACH = "if __name__ != '__main__':\n    make_document(curdoc())"


def _data_json(df=_DF, strings=("make",)):
    """jsonio's shape, with variable labels, value labels and a string."""
    names = list(df.columns)
    values = []
    for _, row in df.iterrows():
        rec = {}
        for c in names:
            v = row[c]
            rec[c] = None if isinstance(v, float) and np.isnan(v) else v
        values.append(rec)
    is_str = {c: c in strings for c in names}
    return {"StataJSON": {
        "variableNames": names,
        "variableLabels": {c: _VARLABELS.get(c, c) for c in names},
        "valueLabels": _VALLABELS, "valueLabelNames": _VLNAMES,
        "variableIsString": is_str, "variableTypeIsString": dict(is_str),
        "values": values}}


def _write(tmp_path, spec, df=_DF):
    sp = os.path.join(str(tmp_path), "spec.json")
    dp = os.path.join(str(tmp_path), "data.json")
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    with open(dp, "w", encoding="utf-8") as fh:
        json.dump(_data_json(df), fh, default=str)
    return sp, dp


def _saved(tmp_path, spec, df=_DF):
    """(renderer, page, warnings) from the saved-dashboard renderer."""
    sp, dp = _write(tmp_path, spec, df)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        r = dr.DashRenderer(sp, dp)
        page = r.render()
    return r, page, sorted(str(x.message) for x in w)


def _served(tmp_path, spec, df=_DF):
    """(document, namespace, warnings) from the generated server app."""
    sp, dp = _write(tmp_path, spec, df)
    op = os.path.join(str(tmp_path), "app.py")
    with warnings.catch_warnings(record=True) as built:
        warnings.simplefilter("always")
        dr.ServerAppBuilder(sp, dp).build(op)
    with open(op, encoding="utf-8") as fh:
        src = fh.read()
    assert _ATTACH in src, "the generated app's curdoc attach moved"
    ns = {"__name__": "help_claims_2_app"}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        exec(compile(src.replace(_ATTACH, "pass"), op, "exec"), ns)
    with warnings.catch_warnings(record=True) as made:
        warnings.simplefilter("always")
        doc = Document()
        ns["make_document"](doc)
    return doc, ns, sorted(str(x.message) for x in list(built) + list(made))


def _both(tmp_path, spec, df=_DF):
    """Both modes, each in a directory of its own."""
    r, page, sw = _saved(_sub(tmp_path, "saved"), spec, df)
    doc, ns, vw = _served(_sub(tmp_path, "served"), spec, df)
    return r, page, sw, doc, ns, vw


def _sub(tmp_path, name):
    p = tmp_path / name
    p.mkdir(exist_ok=True)
    return p


def _figure_models(doc):
    return [m for m in tp._walk_models(doc) if type(m).__name__ == "figure"]


def _saved_figure(r):
    return list(r.figures.values())[0]


def _served_figure(doc):
    figs = _figure_models(doc)
    assert figs, "the served document has no figure"
    return figs[0]


def _spec(plots, go=None, bo=None, kpis=None):
    s = tp._spec(plots, bo, go, kpis=kpis)
    return s


def _filtered_spec(plots, var="foreign", go=None, kpis=None, csv=""):
    bo = {"filter": f"{var}, type(dropdown)", "csv": csv}
    s = _spec(plots, go, bo, kpis)
    s["build_options"]["filters"] = [{"varname": var, "type": "dropdown"}]
    return s


def _naming(ws, option):
    return [w for w in ws if f"{option}(" in w]


# ---------------------------------------------------------------------------
# The help's own text, collapsed as a reader reads it
# ---------------------------------------------------------------------------

def _help():
    with open(_HELP, encoding="utf-8") as fh:
        return fh.read()


def _section(start, end):
    h = _help()
    i = h.index("{marker %s}" % start)
    j = h.index("{marker %s}" % end, i)
    return re.sub(r"\s+", " ", h[i:j])


# ===========================================================================
# 0. The help says what was measured
# ===========================================================================

class TestTheHelpSaysWhatWasMeasured:
    """Each false claim the help made in lines 317-585 is gone, and the
    corrected one is there, word for word where a test elsewhere measures
    it (the case named in each docstring)."""

    def _values(self):
        return _section("validation", "subcommands")

    def test_the_overflow_example_is_one_twoway_refuses(self):
        """HC2-06: twoway refuses msize(1e308) and accepts msize(1e400)."""
        v = self._values()
        assert ("such as {cmd:msize(1e400)}, is refused as {cmd:twoway} "
                "refuses it") not in v
        assert ("such as {cmd:msize(1e308)}, is refused as {cmd:twoway} "
                "refuses it") in v
        assert "{cmd:msize(1e400)}" in v      # named among dash's own

    def test_twoway_does_not_draw_a_time_series_label(self):
        """HC2-10d: twoway mlabel(L.mpg) is r(111)."""
        v = self._values()
        assert "which {cmd:twoway} draws and {cmd:dash} cannot" not in v
        assert ("{cmd:mlabel(L.mpg)} is refused, as {cmd:twoway} refuses "
                "it") in v

    def test_start_is_bounded_by_the_minimum_on_histogram(self):
        """HC2-07."""
        v = self._values()
        assert "{cmd:base()} and {cmd:start()} any number" not in v
        assert "option start() may not be larger than minimum of mpg" in v

    def test_the_options_twoway_does_not_have_are_named_as_such(self):
        """HC2-14y-C: colornlevels(), jseed(), malpha(), colpalette(),
        hover() are not twoway options."""
        v = self._values()
        assert "{cmd:colornlevels()} 2 to 256, {cmd:jitter()}" not in v
        assert ("{cmd:colornlevels()}, {cmd:colpalette()} and {cmd:hover()} "
                "are options {cmd:twoway} does not have") in v

    def test_the_forms_dash_refuses_are_named(self):
        """HC2-18."""
        v = self._values()
        for s in ("{cmd:mlabel()} with more than one variable",
                  "{cmd:range(}{it:varname}{cmd:)} on {cmd:function} and "
                  "{cmd:kdensity}",
                  "{cmd:scatter mpg weight, lwidth(-1)}, which {cmd:twoway} "
                  "draws, is refused"):
            assert s in v, s

    def test_the_values_dash_accepts_are_all_named(self):
        """HC2-16, and TestAStyleOptionGivenEmptyParenthesesIsReported,
        TestAStringColorvarIsDrawnAColourPerValue,
        TestAColourWrittenWithCommasIsReadAsTheTriplet."""
        v = self._values()
        assert "Two values {cmd:twoway} refuses" not in v
        for s in ("{cmd:kernel(GAUSSIAN)} is read as {cmd:kernel(gaussian)}",
                  "{cmd:msize(())} or {cmd:xsize(())}",
                  "{cmd:colorvar()} takes a string variable",
                  "{cmd:mcolor(255,0,0)}"):
            assert s in v, s

    def test_theme_is_not_a_twoway_option(self):
        """HC2-17c."""
        v = self._values()
        assert ("{cmd:scheme()} and {cmd:theme()} are refused where "
                "{cmd:twoway} draws") not in v
        assert "an option {cmd:twoway} does not have" in v

    def test_scheme_is_checked_in_stata(self):
        """HC2-09: an unknown scheme() is refused before Python."""
        v = self._values()
        assert ("Colours, {cmd:msymbol()}, {cmd:lpattern()}, {cmd:scheme()} "
                "and") not in v
        assert ("Colours, {cmd:msymbol()}, {cmd:lpattern()} and the "
                "sub-options") in v

    def test_the_labels_dash_reads_are_the_ones_it_uses(self):
        """TestLabelsUsedAutomatically."""
        v = self._values()
        assert "categorical tick labels" not in v
        assert "{cmd:by()} panels, marker labels, the legend of a discrete" \
            in v
        assert "An axis is labelled with numbers, as in {cmd:twoway}" in v

    def test_dash_serve_says_what_each_mode_recomputes(self):
        """TestWhatTheServerRecomputes, TestWhatASavedPageRecomputes."""
        s = _section("subcommands", "dashboard_options")
        assert "Unlike standalone HTML, the server recalculates" not in s
        assert ("every layer computed from the data -- a histogram's bins as "
                "well as its bars") in s
        assert ("A saved dashboard recomputes those cards, its kernel density "
                "curves and its histogram bar heights in the browser") in s

    def test_dash_serve_names_the_build_only_options(self):
        """HC2-25c."""
        s = _section("subcommands", "dashboard_options")
        assert ("{cmd:saving()}, {cmd:replace} and {cmd:server}, which write "
                "a file, are named in a note and ignored") in s

    def test_dash_clear_keeps_the_settings(self):
        """HC2-28."""
        s = _section("subcommands", "dashboard_options")
        assert "Drops all {cmd:$dash_*} global macros" not in s
        assert ("{cmd:$dash_nobrowser} and the {cmd:$dash_max_*} limits "
                "remain") in s

    def test_dash_nobrowser_is_defined(self):
        """TR-23.3; HC2-30 to HC2-36."""
        h = _help()
        assert "{marker nobrowser_global}" in h
        d = _section("nobrowser_global", "export")
        for s in ("{cmd:global dash_nobrowser 1}",
                  "{cmd:global dash_nobrowser 0} keeps windows shut too",
                  "{cmd:dash clear} leaves it set",
                  "{cmd:macro drop dash_nobrowser}",
                  "The one-line form has no {cmd:nobrowser} option"):
            assert s in d, s
        # Both nobrowser rows lead to it.
        assert h.count("{help dash##nobrowser_global:") >= 2

    def test_the_csv_differences_are_all_listed(self):
        """HC2-37, HC2-38; test_export.py's formatter tests."""
        e = _section("export", "layout")
        for s in ("every line ends in a carriage return and a line feed",
                  "an extended missing value ({cmd:.a} to {cmd:.z}) is an "
                  "empty field",
                  "{cmd:1.00000000000e-07}",
                  "not in the order of the dataset"):
            assert s in e, s


# ===========================================================================
# 1. Option values -- what the renderer does with what Stata lets through
# ===========================================================================

#: A style option given an empty pair of parentheses: twoway refuses every
#: one ("option(s) ( ) not allowed", test_help_claims_2.cscript HC2-16),
#: dash lets it through as a name, and the renderer names it once.
_EMPTY_PARENS = [
    ("line", {"lwidth": "()"}, None, "lwidth"),
    ("line", {"clwidth": "()"}, None, "clwidth"),
    ("scatter", {"msize": "()"}, None, "msize"),
    ("scatter", {"msangle": "()"}, None, "msangle"),
    ("scatter", {"mlwidth": "()"}, None, "mlwidth"),
    ("scatter", {"mlabel": "price", "mlabsize": "()"}, None, "mlabsize"),
    ("scatter", {"mlabel": "price", "mlabgap": "()"}, None, "mlabgap"),
    ("scatter", {"mlabel": "price", "mlabposition": "()"}, None,
     "mlabposition"),
    ("scatter", {"mlabel": "price", "mlabangle": "()"}, None, "mlabangle"),
    ("area", {"fintensity": "()"}, None, "fintensity"),
    ("scatter", {}, {"xsize": "()"}, "xsize"),
    ("scatter", {}, {"ysize": "()"}, "ysize"),
]


@pytest.mark.parametrize("ptype,opts,go,option", _EMPTY_PARENS,
                         ids=[c[3] for c in _EMPTY_PARENS])
class TestAStyleOptionGivenEmptyParenthesesIsReported:
    """dash.sthlp: "a style option given an empty pair of parentheses, such
    as lwidth(()), passes as a name that the renderer then reports"."""

    def test_one_note_naming_it_identical_in_both_modes(self, tmp_path,
                                                        ptype, opts, go,
                                                        option):
        spec = _spec([plot_for(ptype, opts)], go)
        _, _, sw, _, _, vw = _both(tmp_path, spec)
        assert sw == vw, (sw, vw)
        hits = _naming(sw, option)
        assert len(hits) == 1, hits
        assert f"{option}(())" in hits[0], hits[0]

    def test_the_figure_is_still_drawn(self, tmp_path, ptype, opts, go,
                                       option):
        spec = _spec([plot_for(ptype, opts)], go)
        r, _, _, doc, _, _ = _both(tmp_path, spec)
        assert _saved_figure(r).renderers
        assert _served_figure(doc).renderers


class TestAStringColorvarIsDrawnAColourPerValue:
    """dash.sthlp: colorvar() "takes a string variable, drawn a colour per
    value, where twoway wants a numeric one" (twoway r(7): HC2-16l)."""

    def _mapper(self, fig):
        for rnd in fig.renderers:
            fc = rnd.glyph.fill_color
            tr = getattr(fc, "transform", None) if not isinstance(
                fc, str) else None
            if isinstance(tr, CategoricalColorMapper):
                return tr
        return None

    def test_both_modes(self, tmp_path):
        spec = _spec([plot_for("scatter", {"colorvar": "make"})])
        r, _, sw, doc, _, vw = _both(tmp_path, spec)
        for fig, where in ((_saved_figure(r), "saved"),
                           (_served_figure(doc), "served")):
            m = self._mapper(fig)
            assert m is not None, f"{where}: no categorical colour mapper"
            assert sorted(m.factors) == sorted(_DF["make"]), (where,
                                                              m.factors)
        assert sw == vw


class TestAColourWrittenWithCommasIsReadAsTheTriplet:
    """dash.sthlp: "a colour written with commas, mcolor(255,0,0), which
    twoway refuses, dash reads as the triplet 255 0 0" (HC2-16o/p)."""

    def test_both_modes_draw_red_and_say_nothing(self, tmp_path):
        spec = _spec([plot_for("scatter", {"mcolor": "255,0,0"})])
        r, _, sw, doc, _, vw = _both(tmp_path, spec)
        for fig in (_saved_figure(r), _served_figure(doc)):
            g = fig.renderers[0].glyph
            assert str(g.fill_color).lower() == "#ff0000", g.fill_color
        assert sw == vw == []


#: An unknown style inside a structured option, and the property it would
#: have set.  Measured before the fix: title(T, size(bogus)) drew 16px and
#: title(T, color(bogus)) #000000 where title(T) draws the scheme's heading
#: (14pt; #1e2d53 under s2color, #ffffff under s1rcolor -- black on the dark
#: scheme's black), and xtitle()/ytitle() 13px and #000000 where the scheme
#: says 10pt and its axis-title colour: the note said "ignoring it" and the
#: renderer drew a literal instead.  subtitle(), note(), caption(),
#: legend(), xline() and xlabel() already kept the default.
_TEXTBOX_STYLE = [
    ("title", "T", "size(bogus)", lambda f: f.title.text_font_size),
    ("title", "T", "color(bogus)", lambda f: f.title.text_color),
    ("xtitle", "X", "size(bogus)",
     lambda f: f.xaxis[0].axis_label_text_font_size),
    ("xtitle", "X", "color(bogus)",
     lambda f: f.xaxis[0].axis_label_text_color),
    ("ytitle", "Y", "size(bogus)",
     lambda f: f.yaxis[0].axis_label_text_font_size),
    ("ytitle", "Y", "color(bogus)",
     lambda f: f.yaxis[0].axis_label_text_color),
]


@pytest.mark.parametrize("scheme", ["s2color", "s1rcolor"])
@pytest.mark.parametrize("option,text,sub,prop", _TEXTBOX_STYLE,
                         ids=[f"{c[0]}-{c[2]}" for c in _TEXTBOX_STYLE])
class TestAnUnknownStyleInsideAStructuredOption:
    """dash.sthlp: "An unknown style inside one (title(T, size(bogus))) gets a
    note and the default in twoway and in dash alike" (twoway: HC2-21f)."""

    def test_one_note_and_the_schemes_default_in_both_modes(
            self, tmp_path, scheme, option, text, sub, prop):
        plain = _spec([plot_for("scatter")], {option: text},
                      {"scheme": scheme})
        bogus = _spec([plot_for("scatter")], {option: f"{text}, {sub}"},
                      {"scheme": scheme})
        r0, _, _, d0, _, _ = _both(_sub(tmp_path, "plain"), plain)
        r1, _, sw, d1, _, vw = _both(_sub(tmp_path, "bogus"), bogus)
        assert sw == vw
        assert len([w for w in sw if sub in w]) == 1, sw
        assert prop(_saved_figure(r1)) == prop(_saved_figure(r0)), \
            "saved: the unknown style replaced the scheme's default"
        assert prop(_served_figure(d1)) == prop(_served_figure(d0)), \
            "served: the unknown style replaced the scheme's default"

    def test_a_known_style_is_still_honoured(self, tmp_path, scheme, option,
                                             text, sub, prop):
        good = sub.replace("bogus", "red" if sub.startswith("color")
                           else "vlarge")
        spec = _spec([plot_for("scatter")], {option: f"{text}, {good}"},
                     {"scheme": scheme})
        plain = _spec([plot_for("scatter")], {option: text},
                      {"scheme": scheme})
        r1, _, sw, d1, _, _ = _both(_sub(tmp_path, "good"), spec)
        r0, _, _, _, _, _ = _both(_sub(tmp_path, "plain"), plain)
        assert not sw, sw
        assert prop(_saved_figure(r1)) != prop(_saved_figure(r0))
        assert prop(_saved_figure(r1)) == prop(_served_figure(d1))


@pytest.mark.parametrize("go,option,word", [
    ({"legend": "garbage"}, "legend", "garbage"),
    ({"xscale": "bogus"}, "xscale", "bogus"),
])
class TestAnUnknownSubOptionWordIsNamedAndDrawnWithout:
    """dash.sthlp: "an unknown sub-option word, which twoway refuses
    (legend(garbage), xscale(bogus): r(198)), dash names in its sub-option
    note and draws without" (twoway: HC2-21h/k)."""

    def test_named_once_in_both_modes(self, tmp_path, go, option, word):
        spec = _spec([plot_for("scatter"), plot_for("lfit")], go)
        r, _, sw, doc, _, vw = _both(tmp_path, spec)
        assert sw == vw
        hits = [w for w in sw if f"{option}() sub-option" in w]
        assert len(hits) == 1 and hits[0].endswith(word), hits
        assert _saved_figure(r).renderers and _served_figure(doc).renderers


# ===========================================================================
# 2. Labels used automatically (item 6 of Differences from twoway)
# ===========================================================================

class TestLabelsUsedAutomatically:
    """dash.sthlp: variable labels for axis titles and filter titles; value
    labels for filter dropdowns, by() panel titles, marker labels, the
    legend of a discrete colorvar() and the CSV download.  An axis, as in
    twoway, is labelled with numbers, and so is a hover tooltip."""

    def test_axis_titles_are_the_variable_labels(self, tmp_path):
        spec = _spec([plot_for("scatter")])
        r, _, _, doc, _, _ = _both(tmp_path, spec)
        for fig in (_saved_figure(r), _served_figure(doc)):
            assert fig.xaxis[0].axis_label == "Weight (lbs.)"
            assert fig.yaxis[0].axis_label == "Mileage (mpg)"

    def test_a_filter_is_titled_by_its_variable_label_and_lists_labels(
            self, tmp_path):
        spec = _filtered_spec([plot_for("scatter")])
        r, _, _, doc, _, _ = _both(tmp_path, spec)
        saved = [w for w in r.filter_widgets if isinstance(w, Select)]
        served = list(doc.select({"type": Select}))
        assert saved and served
        for w in (saved[0], served[0]):
            assert "Car origin" in w.title, w.title
            labels = [o[1] if isinstance(o, (list, tuple)) else o
                      for o in w.options]
            assert "Domestic" in labels and "Foreign" in labels, w.options

    def test_by_panels_are_titled_by_the_value_labels(self, tmp_path):
        spec = _spec([plot_for("scatter")], {"by": "foreign"})
        r, _, _, doc, _, _ = _both(tmp_path, spec)
        saved = sorted(f.title.text for f in r.figures.values())
        served = sorted(f.title.text for f in _figure_models(doc))
        assert saved == served == ["Domestic", "Foreign"], (saved, served)

    def test_marker_labels_of_a_labelled_variable_are_its_labels(self,
                                                                 tmp_path):
        spec = _spec([plot_for("scatter", {"mlabel": "foreign"})])
        r, _, _, doc, _, _ = _both(tmp_path, spec)
        for fig in (_saved_figure(r), _served_figure(doc)):
            ls = [x for x in fig.center if isinstance(x, LabelSet)]
            assert len(ls) == 1
            text = set(str(t) for t in ls[0].source.data[ls[0].text])
            assert text == {"Domestic", "Foreign"}, text

    def test_a_discrete_colorvar_legend_shows_the_labels(self, tmp_path):
        spec = _spec([plot_for("scatter", {"colorvar": "foreign",
                                           "colordiscrete": "colordiscrete"})])
        r, _, _, doc, _, _ = _both(tmp_path, spec)
        for fig in (_saved_figure(r), _served_figure(doc)):
            legs = [x for x in fig.renderers + list(fig.center)
                    + list(fig.right) if isinstance(x, Legend)]
            got = set()
            for leg in legs:
                for it in leg.items:
                    lab = it.label
                    got.add(lab.get("value") if isinstance(lab, dict)
                            else getattr(lab, "value", str(lab)))
            assert {"Domestic", "Foreign"} <= got, got

    def test_an_axis_is_labelled_with_numbers(self, tmp_path):
        spec = _spec([plot_for("scatter", xvar="foreign")])
        r, _, _, doc, _, _ = _both(tmp_path, spec)
        for fig in (_saved_figure(r), _served_figure(doc)):
            ax = fig.xaxis[0]
            assert not dict(ax.major_label_overrides), ax.major_label_overrides
            assert type(ax.ticker).__name__ == "BasicTicker", ax.ticker
            assert type(ax.formatter).__name__ == "BasicTickFormatter"

    def test_a_hover_tooltip_shows_the_number(self, tmp_path):
        spec = _spec([plot_for("scatter")], {"hover": "foreign"})
        r, _, _, doc, _, _ = _both(tmp_path, spec)
        for fig in (_saved_figure(r), _served_figure(doc)):
            tools = [t for t in fig.tools if isinstance(t, HoverTool)]
            assert tools, "no hover tool"
            fields = [v for _k, v in tools[0].tooltips]
            # The raw column, with no formatter that could map 0 to Domestic.
            assert "@{foreign}" in fields, tools[0].tooltips
            assert not dict(tools[0].formatters), tools[0].formatters


# ===========================================================================
# 3. dash serve: what the server recomputes, and what a saved page does
# ===========================================================================

def _move_dropdown(doc, value):
    """Set the served dropdown and run its callback, as the throttle does
    when a token is free."""
    w = list(doc.select({"type": Select}))[0]
    old, w.value = w.value, value
    for cb in w._callbacks.get("value", []):
        cb("value", old, value)


def _served_source_with(doc, key):
    for m in doc.select({"type": ColumnDataSource}):
        if key in m.data and len(m.data[key]):
            return {k: list(v) for k, v in m.data.items()}
    raise AssertionError(f"no served source carries {key!r}")


def _all_sources(doc):
    return [{k: [str(x) for x in list(v)] for k, v in m.data.items()}
            for m in doc.select({"type": ColumnDataSource})]


def _foreign_one(doc):
    """The served dropdown's value for foreign == 1."""
    w = list(doc.select({"type": Select}))[0]
    opts = [o[0] if isinstance(o, (list, tuple)) else o for o in w.options]
    return [o for o in opts if o in ("1", "1.0")][0]


#: Every plot type whose drawn layer is computed from the rows, rather than
#: the rows themselves.
_COMPUTED = ["lfit", "qfit", "lfitci", "qfitci", "lowess", "lpoly",
             "lpolyci", "fpfit", "fpfitci", "kdensity", "histogram",
             "mspline", "mband"]


class TestWhatTheServerRecomputes:
    """dash.sthlp: "When a filter moves, the server recomputes, from the rows
    the filters leave, every layer computed from the data -- a histogram's
    bins as well as its bars, a fitted or smoothed line, a kernel density
    curve -- and every KPI card that follows the filters."  The KPI half is
    test_server.py::test_filter_callback_updates_kpi_div; the values of
    several layers are test_server.py's *_filter_callback_recomputes."""

    @pytest.mark.parametrize("ptype", _COMPUTED)
    def test_every_computed_layer_is_recomputed(self, tmp_path, ptype):
        doc, _, _ = _served(tmp_path, _filtered_spec([plot_for(ptype)]))
        before = _all_sources(doc)
        _move_dropdown(doc, _foreign_one(doc))
        assert _all_sources(doc) != before, \
            f"the served {ptype} layer did not change when rows were dropped"

    def test_a_histograms_bins_move(self, tmp_path):
        spec = _filtered_spec([plot_for("histogram", {"bin": "4"})])
        doc, _, _ = _served(tmp_path, spec)
        before = _served_source_with(doc, "left")
        _move_dropdown(doc, _foreign_one(doc))
        after = _served_source_with(doc, "left")
        assert before["left"][0] != after["left"][0] or \
            before["right"][-1] != after["right"][-1], (before, after)


class TestWhatASavedPageRecomputes:
    """dash.sthlp: "A saved dashboard recomputes those cards, its kernel
    density curves and its histogram bar heights in the browser, and keeps
    its other computed layers, and its histogram bins, as they were built."
    The saved filter callback carries the layers it recomputes; the KPI half
    is test_filter_widget_data.py::test_the_filter_recomputes_the_card_in_both_modes,
    and "What histogram recompute means" (fixed edges) is test_export.py's
    and test_filter_widget_parity.py's."""

    def test_the_callback_recomputes_histogram_and_kdensity_only(self,
                                                                 tmp_path):
        spec = _filtered_spec([plot_for(p) for p in _COMPUTED])
        r, _, _ = _saved(tmp_path, spec)
        cb = r.filter_callbacks[0]
        kinds = sorted(c["type"] for c in json.loads(
            cb.args["agg_configs_json"]))
        assert kinds == ["histogram", "kdensity"], kinds

    @pytest.mark.parametrize("ptype", [p for p in _COMPUTED
                                       if p not in ("histogram", "kdensity")])
    def test_another_computed_layer_is_kept_as_built(self, tmp_path, ptype):
        r, _, _ = _saved(tmp_path, _filtered_spec([plot_for(ptype)]))
        layer = {id(x.data_source) for x in _saved_figure(r).renderers}
        cb = r.filter_callbacks[0]
        rewritten = {id(s) for s in list(cb.args["all_graph_sources"])
                     + list(cb.args["agg_sources"])}
        assert not layer & rewritten, f"the saved {ptype} layer is rewritten"


# ===========================================================================
# 4. dash build's page, and the launcher behind dash serve
# ===========================================================================

class TestTitleAndSubtitle:
    """dash.sthlp: title() is the dashboard page title, subtitle() its
    subtitle -- in both modes."""

    def test_both_modes(self, tmp_path):
        spec = _spec([plot_for("scatter")],
                     bo={"title": "Fleet", "subtitle": "By weight"})
        r, page, _, doc, _, _ = _both(tmp_path, spec)
        assert "<title>Fleet</title>" in page
        assert "Fleet" in page and "By weight" in page
        assert doc.title == "Fleet"
        texts = " ".join(m.text for m in tp._walk_models(doc)
                         if isinstance(m, Div))
        assert "Fleet" in texts and "By weight" in texts


class TestSchemeWinsOverTheme:
    """dash.sthlp: theme() is an alias for a scheme, and "scheme() wins if
    both are given" -- in both modes, through the one resolver."""

    def test_the_resolver(self):
        spec = {"graphs": [], "kpis": [],
                "build_options": {"theme": "dark", "scheme": "economist",
                                  "session_scheme": ""}}
        assert dr._resolve_scheme_name(spec) == "economist"

    def test_both_modes_draw_the_scheme(self, tmp_path):
        both = _spec([plot_for("scatter")],
                     bo={"theme": "dark", "scheme": "economist"})
        econ = _spec([plot_for("scatter")], bo={"scheme": "economist"})
        r1, _, _, d1, _, _ = _both(_sub(tmp_path, "both"), both)
        r2, _, _, d2, _, _ = _both(_sub(tmp_path, "econ"), econ)
        assert _saved_figure(r1).background_fill_color == \
            _saved_figure(r2).background_fill_color
        assert _served_figure(d1).background_fill_color == \
            _served_figure(d2).background_fill_color


class TestTheSavedPageIsSelfContained:
    """dash.sthlp: without server, dash build "writes a self-contained
    standalone HTML file" -- BokehJS inline, nothing fetched."""

    def test_nothing_is_loaded_from_elsewhere(self, tmp_path):
        _, page, _ = _saved(tmp_path, _spec([plot_for("scatter")]))
        assert not re.findall(r"<script[^>]*\bsrc=", page)
        assert not re.findall(r"<link[^>]*\bhref=", page)
        assert "Bokeh" in page and len(page) > 200_000


class _FakeProc:
    waited = False

    def __init__(self, cmd):
        type(self).cmd = list(cmd)

    def wait(self):
        type(self).waited = True
        return 0


class TestTheLauncherBehindDashServe:
    """dash.sthlp: dash serve runs the server "in the foreground; Stata is
    blocked until you press Ctrl+C or the optional timeout() expires", and
    opens a browser unless nobrowser, the global or a nodraw says not to
    (test_serve_browser.cscript: --no-browser reaches the launcher).  Here:
    the launcher waits on the app it starts, passes --show only without
    --no-browser, and --timeout only when it is not 0.

    This is the launcher, given an --output that ends in .py.  At 4ede074
    `dash serve' itself hands the renderer an extension-less tempfile and
    the renderer refuses it before launching -- r(7102), "--output must
    end in .py for mode 'server'" (measured 23sep2026; another work
    package's fix) -- so these claims hold up to the launch and no further
    until that is fixed."""

    def _launch(self, tmp_path, monkeypatch, extra):
        spec = _spec([plot_for("scatter")])
        sp, dp = _write(tmp_path, spec)
        out = os.path.join(str(tmp_path), "app.py")
        _FakeProc.waited = False
        _FakeProc.cmd = None
        monkeypatch.setattr(subprocess, "Popen", _FakeProc)
        monkeypatch.setattr(sys, "argv", [
            "dash_render.py", "--spec", sp, "--data", dp, "--output", out,
            "--mode", "server", "--launch", "--port", "5123"] + extra)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            runpy.run_path(os.path.join(_ROOT, "dash_render.py"),
                           run_name="__main__")
        return _FakeProc.cmd, _FakeProc.waited

    def test_it_blocks_and_opens_a_browser_by_default(self, tmp_path,
                                                      monkeypatch):
        cmd, waited = self._launch(tmp_path, monkeypatch, ["--timeout", "0"])
        assert waited, "the launcher returned without waiting on the app"
        assert "--show" in cmd and "--timeout" not in cmd, cmd

    def test_no_browser_and_a_timeout(self, tmp_path, monkeypatch):
        cmd, waited = self._launch(tmp_path, monkeypatch,
                                   ["--timeout", "7", "--no-browser"])
        assert waited
        assert "--show" not in cmd, cmd
        assert cmd[cmd.index("--timeout") + 1] == "7", cmd


# ===========================================================================
# 5. Exporting
# ===========================================================================

def _button(root):
    found = list(root.select({"name": "dash_csv_download"}))
    return found[0] if found else None


def _parent_of(models, child):
    for m in models:
        kids = getattr(m, "children", None)
        if isinstance(kids, (list, tuple)) and any(k is child for k in kids):
            return m
    return None


class TestTheCsvButton:
    """dash.sthlp: "With csv, the dashboard carries a Download CSV button
    beside its filters"."""

    def test_it_sits_with_the_filters_in_both_modes(self, tmp_path):
        spec = _filtered_spec([plot_for("scatter")], csv="1")
        r, _, _, doc, _, _ = _both(tmp_path, spec)
        saved_models = list(r._last_layout_root.references())
        served_models = tp._walk_models(doc)
        for models, root in ((saved_models, r._last_layout_root),
                             (served_models, doc)):
            btn = _button(root)
            sel = [m for m in models if isinstance(m, Select)][0]
            assert btn is not None
            assert _parent_of(models, btn) is _parent_of(models, sel)


class TestTheCsvCarriesEveryVariableTheDashboardUses:
    """dash.sthlp: the CSV has "every variable the dashboard uses --
    including one that only a KPI card summarises"; "A saved dashboard with
    filters already contains those rows (the filters need them), but a
    served one sends the browser only what it draws."  (HC2-39 is the
    Stata half: the data dash.ado exports holds the card's variable.)"""

    def _spec(self, csv):
        return _filtered_spec([plot_for("scatter")], csv=csv,
                              kpis=[tp._kpi("k1", "mean", "price")])

    def test_the_card_variable_is_a_column_of_the_download(self, tmp_path):
        r, _, _ = _saved(_sub(tmp_path, "s"), self._spec("1"))
        a = _button(r._last_layout_root).js_event_callbacks[
            "button_click"][0].args
        assert "price" in json.loads(a["meta_json"])["columns"]
        doc, _, _ = _served(_sub(tmp_path, "v"), self._spec("1"))
        cb = _button(doc).js_property_callbacks["change:tags"][0]
        assert "price" in json.loads(cb.args["meta_json"])["columns"]

    def test_a_saved_page_with_filters_holds_every_row_without_csv(
            self, tmp_path):
        r, _, _ = _saved(tmp_path, self._spec(""))
        snap = r.filter_callbacks[0].args["orig_source"].data
        for c in _DF.columns:
            assert c in snap and len(snap[c]) == len(_DF), c

    def test_a_served_page_sends_only_what_it_draws(self, tmp_path):
        doc, _, _ = _served(tmp_path, self._spec(""))
        cols = set()
        for m in doc.select({"type": ColumnDataSource}):
            cols |= set(m.data)
        assert "price" not in cols and "make" not in cols, cols


class TestOnlyTheFiltersCount:
    """dash.sthlp: "Only the filters count; a selection brushed on a graph
    and a graph's own if or in do not."  The saved download reads the
    unfiltered snapshot and the widgets and nothing else; the served one
    masks the whole frame by the widgets."""

    def test_the_saved_download_reads_no_graph_source(self, tmp_path):
        spec = _filtered_spec([plot_for("scatter")], csv="1")
        spec["graphs"][0]["if_expr"] = "foreign == 1"
        r, _, _ = _saved(tmp_path, spec)
        a = _button(r._last_layout_root).js_event_callbacks[
            "button_click"][0].args
        graph_sources = {id(x.data_source) for f in r.figures.values()
                         for x in f.renderers}
        assert id(a["orig_source"]) not in graph_sources
        # The snapshot is the whole frame: the graph's if does not cut it.
        assert len(a["orig_source"].data["mpg"]) == len(_DF)
        assert set(a) == {"orig_source", "text_source", "all_widgets",
                          "filter_specs_json", "meta_json"}, set(a)

    def test_the_served_download_ignores_a_brush_and_the_graphs_if(
            self, tmp_path):
        spec = _filtered_spec([plot_for("scatter")], csv="1")
        spec["graphs"][0]["if_expr"] = "foreign == 1"
        doc, _, _ = _served(tmp_path, spec)
        fig = _served_figure(doc)
        fig.renderers[0].data_source.selected.indices = [0]
        btn = _button(doc)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            btn._trigger_event(ButtonClick(btn))
        cb = btn.js_property_callbacks["change:tags"][0]
        rows = cb.args["src"].data
        assert len(rows["mpg"]) == len(_DF), len(rows["mpg"])


class TestTheServedDownloadRate:
    """dash.sthlp: "a session may download twice at once and then once every
    five seconds"."""

    def test_the_constants(self):
        assert dr._DASH_CSV_BURST == 2
        assert 1.0 / dr._DASH_CSV_RATE == pytest.approx(5.0)

    def test_the_bucket_with_a_clock(self):
        now = [100.0]
        ran, timers = [], []

        class _Doc:
            def add_timeout_callback(self, fn, ms):
                timers.append(ms)

        f = dr._dash_event_throttle(_Doc(), lambda *a: ran.append(now[0]),
                                    rate=dr._DASH_CSV_RATE,
                                    burst=dr._DASH_CSV_BURST,
                                    clock=lambda: now[0])
        f("clicks", None, None)
        f("clicks", None, None)
        assert ran == [100.0, 100.0]
        f("clicks", None, None)
        assert ran == [100.0, 100.0] and timers == [5000]
        now[0] += 5.0
        g = dr._dash_event_throttle(_Doc(), lambda *a: ran.append(now[0]),
                                    rate=dr._DASH_CSV_RATE,
                                    burst=dr._DASH_CSV_BURST,
                                    clock=lambda: now[0])
        # A fresh bucket starts full; after five seconds an empty one holds
        # exactly one more token.
        for _ in range(2):
            g("clicks", None, None)
        now[0] += 5.0
        g("clicks", None, None)
        assert ran[-1] == now[0]

    def test_the_served_app_uses_them(self, tmp_path):
        doc, ns, _ = _served(tmp_path, _filtered_spec([plot_for("scatter")],
                                                      csv="1"))
        assert ns["_DASH_CSV_BURST"] == 2
        assert ns["_DASH_CSV_RATE"] == dr._DASH_CSV_RATE


class TestAnIfDropsAMissingValue:
    """dash.sthlp: a moved range or slider filter "drops observations whose
    value is missing, as if x >= value does in dash" -- dash's if, unlike
    Stata's, where . sorts above every number.  Both modes draw through the
    one qualifier helper."""

    def test_the_helper(self):
        df = pd.DataFrame({"x": [1.0, np.nan, 30.0], "y": [1.0, 2.0, 3.0]})
        got = dr._dash_qualified_frame(df, "x >= 20", "")
        assert list(got["y"]) == [3.0]

    def test_both_modes_leave_the_missing_row_out(self, tmp_path):
        df = _DF.copy()
        df.loc[0, "mpg"] = np.nan          # weight and price still there
        spec = _spec([plot_for("scatter", yvar="price", xvar="weight")])
        spec["graphs"][0]["if_expr"] = "mpg >= 20"
        want = int((df["mpg"] >= 20).sum())
        r, _, _, doc, _, _ = _both(tmp_path, spec, df)
        for fig in (_saved_figure(r), _served_figure(doc)):
            rnd = fig.renderers[0]
            view = rnd.view
            n = len(rnd.data_source.data["price"])
            filt = getattr(view, "filter", None)
            idx = getattr(filt, "booleans", None)
            if idx is not None:
                n = sum(1 for b in idx if b)
            assert n == want, (n, want)
