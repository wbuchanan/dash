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
import io
import json
import os
import re
import runpy
import socket
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
from conftest import exec_app  # noqa: E402
from serve_token_probe import FakeStdin  # noqa: E402  (WP-29 P0.12a)
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
        exec_app(src.replace(_ATTACH, "pass"), op, ns)
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
        # Flipped (WP-35 basic:PT-13, D60): read as msize(0), as twoway
        # draws it.
        assert "{cmd:msize(1e400)}" in v

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
        # Flipped (WP-35 DT-15): colornlevels(), colpalette(), jseed() and
        # malpha() named as dash's own was wrong; twoway refuses them, and
        # so does dash (DECISIONS.md P4-7); hover() is dash's own.
        assert "{cmd:colornlevels()}" not in v
        assert ("{cmd:hover()} is an option {cmd:twoway} does not have") in v

    def test_the_forms_dash_refuses_are_named(self):
        """HC2-18."""
        v = self._values()
        # P1.1b: twoway labels with the first variable (HC2-18a)
        # Flipped (WP-31 C10a): range(varname) on function and kdensity is
        # taken, as twoway takes it, so the help no longer names it here.
        # Flipped (WP-35 basic:PT-13): lwidth(-1) on scatter is drawn, as
        # twoway draws it (value_codes_truth.json lwidth_neg.scatter), so
        # the help no longer names it here.
        assert ("{cmd:scatter mpg weight, lwidth(-1)}, which {cmd:twoway} "
                "draws, is refused") not in v
        assert "an element of {cmd:mlabel()} that names several variables" in v

    def test_the_values_dash_accepts_are_all_named(self):
        """HC2-16, and TestAStyleOptionGivenEmptyParenthesesIsReported,
        TestAStringColorvarIsDrawnAColourPerValue,
        TestAColourWrittenWithCommasIsRefusedInStata."""
        v = self._values()
        assert "Two values {cmd:twoway} refuses" not in v
        # Flipped (WP-35 DT-15): kernel(GAUSSIAN), xsize(()) and a string
        # colorvar() accepted was wrong; twoway refuses them, and so does
        # dash now (DECISIONS.md P4-7).
        assert "{cmd:kernel(GAUSSIAN)} is read as {cmd:kernel(gaussian)}" not in v
        assert "{cmd:colorvar()} takes a string variable" not in v
        for s in ("These values are refused as {cmd:twoway} refuses them:",
                  "{cmd:kernel(GAUSSIAN)}, {cmd:invalid kernel function}",
                  "{cmd:xsize(())} and {cmd:ysize(())}",
                  "a string {cmd:colorvar()}, r(7)",
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
        # WP-30 P1.13a: a comma in a colour is checked in Stata.
        assert ("Colours (but for a comma), {cmd:msymbol()}, "
                "{cmd:lpattern()} and the sub-options") in v

    def test_the_labels_dash_reads_are_the_ones_it_uses(self):
        """TestLabelsUsedAutomatically."""
        v = self._values()
        assert "categorical tick labels" not in v
        # Flipped (WP-42 CV-3): a discrete key is labelled with its levels,
        # as twoway's, and its value labels under zlabel(, valuelabel).
        assert "{cmd:by()} panels, marker labels and the CSV download)" in v
        assert "its levels, as in {cmd:twoway}, and with their value " \
            "labels under {cmd:zlabel(, valuelabel)}" in v
        assert "An axis is labelled with numbers, as in {cmd:twoway}" in v

    def test_dash_serve_says_what_each_mode_recomputes(self):
        """TestWhatTheServerRecomputes, TestWhatASavedPageRecomputes."""
        s = _section("subcommands", "dashboard_options")
        assert "Unlike standalone HTML, the server recalculates" not in s
        assert ("every layer computed from the data -- a histogram's bins as "
                "well as its bars") in s
        # Flipped (WP-31 F1c): "its {cmd:lfit} and {cmd:qfit} lines".
        # Flipped (WP-31 F1b): and lfitci and qfitci with their bands.
        # Flipped (WP-31 F1d): and lpoly.
        # Flipped (WP-31 F1e, F1f): and lpolyci, mband and mspline.
        # Flipped (WP-31 F1g): and fpfit and fpfitci.
        # Flipped (WP-31 B4c): and contour and contourline within the cap.
        # Flipped (WP-31 H6 follow-up): and a default-grid histogram's bins;
        # bins set by bin(), width(), start() or discrete are kept.
        assert ("A saved dashboard recomputes those cards, its kernel density "
                "curves, its histogram bar heights (and the bins of a "
                "histogram on the default grid), its {cmd:lfit}, "
                "{cmd:qfit}, {cmd:fpfit}, {cmd:lowess}, {cmd:lpoly}, "
                "{cmd:mband} and {cmd:mspline} lines, its {cmd:lfitci}, "
                "{cmd:qfitci}, {cmd:fpfitci} and {cmd:lpolyci} lines and "
                "bands and, up to 1,000 distinct points, its {cmd:contour} "
                "and {cmd:contourline} layers in the browser, and keeps its "
                "other computed layers, and the bins a histogram's {cmd:bin()}, "
                "{cmd:width()}, {cmd:start()} or {cmd:discrete} set, as they "
                "were built") in " ".join(s.split())

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


class TestAColourWrittenWithCommasIsRefusedInStata:
    """dash.sthlp: a colour written with commas, mcolor(255,0,0), is refused
    as twoway refuses it, invalid '0', r(198) (HC2-16o/p).  A hand-written
    spec that still reaches the renderer reads it as an unknown colour.

    Flipped (WP-30 P1.13a): it drew red in silence; twoway refuses it in
    an option and draws an unknown colour black with a note."""

    def test_a_hand_written_spec_is_noted_and_drawn_black(self, tmp_path):
        spec = _spec([plot_for("scatter", {"mcolor": "255,0,0"})])
        r, _, sw, doc, _, vw = _both(tmp_path, spec)
        for fig in (_saved_figure(r), _served_figure(doc)):
            g = fig.renderers[0].glyph
            assert str(g.fill_color).lower() == "#000000", g.fill_color
        assert sw == vw
        # Flipped (18oct2026): twoway's words, naming the colour.
        assert [w for w in sw if "class color" in w] == [
            "dash: named style 255,0,0 not found in class color, default "
            "attributes used"]


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

    def test_one_note_and_twoways_default_in_both_modes(
            self, tmp_path, scheme, option, text, sub, prop):
        """A bad colour draws black, as twoway draws title("T",
        color(bogus)) (WP-30 P1.13a; it kept the scheme's colour, which
        the flip corrects).  A bad size draws
        twoway's medium, 11 pt, in both modes and both schemes (WP-30
        P1.12a, P1.12.2): twoway falls back to medium for an unknown size,
        not to the scheme's title size, so the size rows no longer compare
        against the plain figure."""
        plain = _spec([plot_for("scatter")], {option: text},
                      {"scheme": scheme})
        bogus = _spec([plot_for("scatter")], {option: f"{text}, {sub}"},
                      {"scheme": scheme})
        r0, _, _, d0, _, _ = _both(_sub(tmp_path, "plain"), plain)
        r1, _, sw, d1, _, vw = _both(_sub(tmp_path, "bogus"), bogus)
        assert sw == vw
        # Flipped (18oct2026): an unknown colour's note is twoway's, which
        # names the colour, not the sub-option.
        assert len([w for w in sw if sub in w or (
            sub == "color(bogus)" and "named style bogus not found in "
            "class color" in w)]) == 1, sw
        if sub.startswith("size"):
            # WP-30 P1.12a: twoway draws an unknown size as medium, 11 pt
            # (it was the plain figure's size).
            assert prop(_saved_figure(r1)) == "11pt"
            assert prop(_served_figure(d1)) == "11pt"
            return
        # WP-30 P1.13a: twoway draws an unknown colour black (measured,
        # colour_grammar_truth.json site_05).
        assert prop(_saved_figure(r1)) == "#000000", \
            "saved: an unknown colour is not drawn black"
        assert prop(_served_figure(d1)) == "#000000", \
            "served: an unknown colour is not drawn black"

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
    """An unknown sub-option word, which twoway refuses (legend(garbage),
    xscale(bogus): r(198), HC2-21h/k), and which dash.ado now refuses too
    (WP-30 P1.19, P1.18a), still reaches the renderer in a hand-written
    spec: there it is named once and the graph is drawn without it."""

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
    labels for filter dropdowns, by() panel titles, marker labels and the
    CSV download; a discrete colorvar() key with its levels, and their
    value labels under zlabel(, valuelabel).  An axis, as in twoway, is
    labelled with numbers, and so is a hover tooltip."""

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
        # Flipped (WP-30 P1.15a): the value labels title each panel as a
        # row of its own, as twoway draws them, not as the figure's title.
        from by_panel_probe import panel_label
        saved = sorted(panel_label(f) for f in r.figures.values())
        served = sorted(panel_label(f) for f in _figure_models(doc)
                        if panel_label(f))
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
        # Flipped (WP-42 CV-3): a Legend of the two labels unasked; twoway
        # draws swatches beside a z axis labelled 0 .2 .. 1 (K2), and
        # Domestic and Foreign at the levels under zlabel(, valuelabel)
        # (K7).  The help says so.
        plot = plot_for("scatter", {"colorvar": "foreign",
                                    "colordiscrete": "colordiscrete"})
        for go, want in (({}, None),
                         ({"zlabel": ", valuelabel"},
                          ["Domestic", "Foreign"])):
            r, _, _, doc, _, _ = _both(tmp_path, _spec([plot], go))
            for fig in (_saved_figure(r), _served_figure(doc)):
                assert not [x for x in fig.renderers + list(fig.center)
                            + list(fig.right) if isinstance(x, Legend)]
                ovr = dict(fig._dash_key_cell._dash_key_axis
                           .major_label_overrides or {})
                got = [ovr[k] for k in sorted(ovr, key=float)]
                if want is None:
                    assert "Domestic" not in got and got[0] == "0", got
                else:
                    assert [t for t in got if t in want] == want, got

    def test_an_axis_is_labelled_with_numbers(self, tmp_path):
        """Flipped (WP-30 P1.5): BasicTickFormatter was wrong because
        twoway writes the axis in the variable's display format; the
        formatter is Stata's writer, and it writes 0 and 1."""
        spec = _spec([plot_for("scatter", xvar="foreign")])
        r, _, _, doc, _, _ = _both(tmp_path, spec)
        for fig in (_saved_figure(r), _served_figure(doc)):
            ax = fig.xaxis[0]
            assert not dict(ax.major_label_overrides), ax.major_label_overrides
            # WP-30 P1.3a: BasicTicker was wrong because a default axis is
            # ticked by natscale (twoway's #5) on a FixedTicker.
            assert type(ax.ticker).__name__ == "FixedTicker", ax.ticker
            assert type(ax.formatter).__name__ == "CustomJSTickFormatter"
            fmt = ax.formatter.args["fmt"]
            assert "labels" not in ax.formatter.args
            assert [dr._dash_fmt_text(v, fmt) for v in (0, 1)] == ["0", "1"]

    def test_a_hover_tooltip_shows_the_label(self, tmp_path):
        """GAPS2 G16 (WP-28 S14): a hover() variable with value labels shows
        its label, as list and browse do -- the tooltip reads the derived
        column __dash_hover_foreign.  It showed the number (the raw
        @{foreign}) before, which this test used to pin."""
        spec = _spec([plot_for("scatter")], {"hover": "foreign"})
        r, _, _, doc, _, _ = _both(tmp_path, spec)
        for fig in (_saved_figure(r), _served_figure(doc)):
            tools = [t for t in fig.tools if isinstance(t, HoverTool)]
            assert tools, "no hover tool"
            fields = [v for _k, v in tools[0].tooltips]
            assert "@{__dash_hover_foreign}" in fields, tools[0].tooltips
            assert "@{foreign}" not in fields, tools[0].tooltips
            assert not dict(tools[0].formatters), tools[0].formatters
            col = fig.renderers[0].data_source.data["__dash_hover_foreign"]
            assert set(col) == {"Domestic", "Foreign"}


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
    # A number since GAPS2 X1 (a numeric column's dropdown carries floats).
    return [o for o in opts if o == 1.0 and not isinstance(o, str)][0]


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
    density curves, its histogram bar heights and its lfit, qfit and lowess
    lines in the browser, and keeps its other computed layers, and its
    histogram bins, as they were built." (lfit and qfit since WP-31 F1a,
    lowess since F1c, lfitci and qfitci with their bands since F1b, lpoly
    since F1d, lpolyci with its band since F1e, mband and mspline since
    F1f, fpfit and fpfitci since F1g.)
    The saved filter callback carries the layers it recomputes; the KPI half
    is test_filter_widget_data.py::test_the_filter_recomputes_the_card_in_both_modes,
    and "What histogram recompute means" (fixed edges) is test_export.py's
    and test_filter_widget_parity.py's."""

    def test_the_callback_recomputes_histogram_kdensity_lfit_and_qfit(
            self, tmp_path):
        # Flipped (WP-31 F1a): histogram and kdensity only, before the
        # saved page refitted lfit and qfit.  Flipped (WP-31 F1c): and
        # lowess, re-smoothed since.  Flipped (WP-31 F1b): and lfitci and
        # qfitci, refitted with their bands since.  Flipped (WP-31 F1d): and
        # lpoly.  Flipped (WP-31 F1e): and lpolyci, its line and its band
        # (two configs).  Flipped (WP-31 F1f): and mband and mspline.
        # Flipped (WP-31 F1g): and fpfit and fpfitci -- every computed type.
        spec = _filtered_spec([plot_for(p) for p in _COMPUTED])
        r, _, _ = _saved(tmp_path, spec)
        cb = r.filter_callbacks[0]
        kinds = sorted(c["type"] for c in json.loads(
            cb.args["agg_configs_json"]))
        assert kinds == ["fpfit", "fpfitci", "histogram", "kdensity", "lfit",
                         "lfitci", "lowess", "lpoly", "lpolyci", "lpolyci",
                         "mband", "mspline", "qfit", "qfitci"], kinds

    @pytest.mark.parametrize("ptype,opts", [("fpfit", {"recast": "line"}),
                                            ("fpfitci", {"ciplot": "rline"})],
                             ids=["fpfit recast(line)",
                                  "fpfitci ciplot(rline)"])
    def test_another_computed_layer_is_kept_as_built(self, tmp_path, ptype,
                                                     opts):
        """Flipped (WP-31 F1g): fpfit and fpfitci were the computed layers
        a saved page kept as built; it refits them since, so the layers it
        keeps are a recast() fit and a part ciplot() or fitplot() draws as
        another type (and Stata's estopts() points, test_fit_options.py)."""
        r, _, _ = _saved(tmp_path, _filtered_spec([plot_for(ptype, opts)]))
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
    """Stands in for subprocess.Popen (GAPS2 F1): the real launcher now
    pipes the child's stdout/stderr and reads its exit status
    (_dash_launch_app, TR-09.2), so the fake takes **kw and offers text
    streams, a returncode and poll()/terminate()/communicate() too, and a
    stdin the app is handed over on (WP-29 P0.12b)."""
    waited = False

    def __init__(self, cmd, **kw):
        type(self).cmd = list(cmd)
        type(self).kw = kw
        self.returncode = 0
        self.stdin = FakeStdin()
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()

    def poll(self):
        return self.returncode

    def wait(self):
        type(self).waited = True
        return self.returncode

    def terminate(self):
        pass

    def communicate(self):
        return ("", "")


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
        # A free port, not a fixed 5123: the launcher now pre-binds the
        # port before starting the (faked) child, so a fixed number would
        # fail on a machine where something else holds it (GAPS2 F1).
        with socket.socket() as _s:
            _s.bind(("127.0.0.1", 0))
            _port = _s.getsockname()[1]
        monkeypatch.setattr(sys, "argv", [
            "dash_render.py", "--spec", sp, "--data", dp, "--output", out,
            "--mode", "server", "--launch", "--port", str(_port)] + extra)
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
    including one that only a KPI card summarises"; "Without csv a saved
    dashboard holds only the observations its graphs, cards and filters
    select ...; with it the page holds them all, so that the download can
    be written in the browser, but a served one sends the browser only what
    it draws."  (HC2-39 is the Stata half: the data dash.ado exports holds
    the card's variable.)  Flipped (WP-29 P0.11): the docstring quoted "A
    saved dashboard with filters already contains those rows", which the
    page no longer does."""

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

    def test_a_saved_page_holds_the_rows_its_graphs_cards_and_filters_select(
            self, tmp_path):
        # The spec is unqualified and its card follows the filter, so every
        # row is selected (WP-29 P0.11; renamed from
        # test_a_saved_page_with_filters_holds_every_row_without_csv).
        r, _, _ = _saved(tmp_path, self._spec(""))
        snap = r.filter_callbacks[0].args["orig_source"].data
        for c in _DF.columns:
            assert c in snap and len(snap[c]) == len(_DF), c

    def test_a_graph_if_keeps_its_variables_on_its_rows_only(self, tmp_path):
        """WP-29 P0.11: under a graph ``if foreign == 1`` and no csv, the
        snapshot holds mpg on the foreign rows only (the card keeps every
        row on the page for price)."""
        spec = self._spec("")
        spec["graphs"][0]["if_expr"] = "foreign == 1"
        r, _, _ = _saved(tmp_path, spec)
        snap = r.filter_callbacks[0].args["orig_source"].data
        obs = [r._page_labels[int(i)] for i in snap["__dash_row__"]]
        held = sorted(o for o, v in zip(obs, snap["mpg"])
                      if v is not None and v == v)
        assert held == [i for i in range(len(_DF))
                        if _DF["foreign"].iloc[i] == 1.0], held

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
