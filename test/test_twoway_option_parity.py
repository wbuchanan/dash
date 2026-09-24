"""twoway's clcolor(), clpattern(), clwidth(), mlabangle() and mlabformat().

ROADMAP WP-22 TR-22.3 / AC-22.2, GAPS.md F3.  Each of these options was
matched by the trailing ``*`` of dash's ``syntax`` statement, so it landed in
the note as UNKNOWN and was drawn as if it had not been written.  Measured
23sep2026 against twoway with SVG exports of the drawn picture (the WP-22
work notes hold the probes); what the renderer must reproduce:

* ``clcolor()``, ``clpattern()`` and ``clwidth()`` style the CONNECTING line
  only.  twoway_yxview_parse.class maps ``CLColor()`` to ``line(color())``
  and ``LColor()`` to ``line(color())`` AND ``area(linestyle(color()))``, and
  factors the cl options after the l options whatever order they were typed
  in -- so on ``line`` and ``connected``, ``lcolor(red) clcolor(blue)`` and
  ``clcolor(blue) lcolor(red)`` both draw a blue line, and ``color(green)
  clcolor(blue)`` draws a blue line with green markers.  On line, connected,
  lfit, qfit, fpfit, lpoly, lowess, mspline, mband, kdensity, function and
  tsline the cl option draws exactly what the l option draws; on lfitci,
  qfitci, lpolyci and fpfitci it styles the fit line alone (lcolor() also
  outlines the band there, which dash does not draw); on every other type it
  draws a picture identical to no option at all.  dash.ado writes the three
  keys only onto the types that draw the connecting line
  (test_twoway_option_parity.cscript certifies that half against twoway),
  and the renderer lets them style the line in place of lcolor(),
  lpattern() and lwidth() -- never the marker border, which twoway's cl
  options never reach (``connected ..., clcolor(red)`` leaves the markers
  alone in twoway).
* ``mlabangle()`` takes an anglestyle: the names in Stata's own
  anglestyle-*.style files, case-sensitively (``Vertical`` is "named style
  Vertical not found", drawn horizontal), or degrees from -360 to 360,
  counter-clockwise, as Bokeh's LabelSet angle is.
* ``mlabformat()`` formats numeric marker labels (``%9.2f`` draws 22.00,
  ``%9.1fc`` 4,099.0, ``%9.2e`` 4.10e+03); it changes nothing on a string or
  a value-labelled variable, and ``mlabformat(abc)`` is accepted by twoway
  without a word and changes nothing.

The served app copies ``GlyphMapper`` by source, so every check here runs in
both render modes and asserts they agree.
"""
import importlib.util
import itertools
import json
import math
import os
import sys
import tempfile
import warnings

import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import ColumnDataSource, LabelSet
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import make_data_json  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_DF = pd.DataFrame({
    "mpg": [22.0, 17.0, 25.0, 30.0, 21.0, 19.0, 14.0, 28.0, 16.0, 23.0],
    "weight": [2930.0, 3350.0, 2200.0, 1800.0, 3000.0, 3100.0, 4080.0,
               2010.0, 3600.0, 2650.0],
    "price": [4099.0, 4749.0, 3799.0, 4816.0, 5788.0, 4453.0, 5189.0,
              10372.0, 4082.0, 11385.0],
    "foreign": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
    "make": ["AMC Concord", "AMC Pacer", "AMC Spirit", "Buick Century",
             "Buick Electra", "Buick LeSabre", "Buick Opel", "Buick Regal",
             "Buick Riviera", "Buick Skylark"],
})
_VALUE_LABELS = {"origin": {"0": "Domestic", "1": "Foreign"}}
_LABEL_NAMES = {"foreign": "origin"}
_SEQ = itertools.count()
_TMP = tempfile.mkdtemp(prefix="dash_twoway_parity_")


def _write(spec):
    tag = next(_SEQ)
    sp = os.path.join(_TMP, f"spec_{tag}.json")
    dp = os.path.join(_TMP, f"data_{tag}.json")
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    data = make_data_json(_DF, _VALUE_LABELS, _LABEL_NAMES)
    # Real jsonio marks make as a string; the served app coerces an unmarked
    # column to NaN.
    for key in ("variableIsString", "variableTypeIsString"):
        data["StataJSON"][key]["make"] = True
    with open(dp, "w") as fh:
        json.dump(data, fh)
    return tag, sp, dp


def _decoded_document_blob(page: str) -> str:
    """The page's embedded Bokeh document JSON, decoded back to raw text.

    Bokeh escapes ``<``, ``>`` and ``&`` when it writes the document into
    the ``<script type="application/json">`` block, so a search of the page
    source for a raw ``<script>`` can never match.  ``json.loads`` reverses
    that escaping: a user value that reached any model is a plain string in
    the result, exactly as it would be if the browser rebuilt the model.
    Returns every such block re-serialised, joined -- so a payload that
    survived into a title, a Div or a label field would appear verbatim.
    """
    import re as _re
    blobs = []
    for raw in _re.findall(
            r'<script type="application/json"[^>]*>(.*?)</script>',
            page, _re.S):
        try:
            blobs.append(json.dumps(json.loads(raw)))
        except ValueError:
            continue
    return "\n".join(blobs)


def _both(plots, go=None):
    """(renderer, document, standalone warnings, served warnings)."""
    spec = tp._spec(plots, None, go)
    _, sp, dp = _write(spec)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        r = dr.DashRenderer(sp, dp)
        r.render()
    std_w = sorted(str(w.message) for w in caught)

    tag, sp, dp = _write(spec)
    ap = os.path.join(_TMP, f"app_{tag}.py")
    with warnings.catch_warnings(record=True) as built:
        warnings.simplefilter("always")
        dr.ServerAppBuilder(sp, dp).build(ap)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ms = importlib.util.spec_from_file_location(f"_twp_{tag}", ap)
        mod = importlib.util.module_from_spec(ms)
        ms.loader.exec_module(mod)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        doc = Document()
        mod.make_document(doc)
    srv_w = sorted(str(w.message) for w in list(built) + list(caught))
    return r, doc, std_w, srv_w


def _figures(r, doc):
    """(saved figure, served figure) of a one-graph spec."""
    std = list(r.figures.values())[0]
    srv = [m for m in tp._walk_models(doc) if type(m).__name__ == "figure"][0]
    return std, srv


def _glyphs(fig, kind):
    return [r.glyph for r in fig.renderers
            if type(getattr(r, "glyph", None)).__name__ == kind]


def _labelset(fig):
    sets = [x for x in (list(fig.center) + list(fig.above) + list(fig.below)
                        + list(fig.left) + list(fig.right))
            if isinstance(x, LabelSet)]
    assert len(sets) == 1, sets
    return sets[0]


def _texts(ls):
    """The values the LabelSet draws, exactly as its source holds them.

    Not str()-ed: a raw float 22.0 is drawn by the browser as "22", and
    str() would make it look like a formatted "22.0".
    """
    field = ls.text if isinstance(ls.text, str) else ls.text.get("field")
    return list(ls.source.data[field])


def _hex(name):
    """The colour ``_apply_line_opts`` draws for a colour name."""
    return dr.OptionTranslator.parse_color_alpha(name)[0].lower()


def _notes(fn):
    dr._dash_reset_notes()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        out = fn()
    return out, [str(w.message) for w in caught]


# ===========================================================================
# 0. What dash.ado declares, read from the source
# ===========================================================================

from test_abbreviations import _program_body, _syntax_options  # noqa: E402

_ADO = os.path.join(_HERE, "..", "dash.ado")


def _ado():
    with open(_ADO, encoding="utf-8") as fh:
        return fh.read()


def _declared(prog):
    return dict((full, mn) for mn, full in
                _syntax_options(_program_body(_ado(), prog)))


#: The F3 options twoway takes where the user writes them, with twoway's own
#: minimum abbreviation -- read from twoway_yxview_parse.class (CLColor,
#: CLPattern, CLWidth, MLABANGle, MLABFormat, MLABTextstyle, MLABVposition,
#: SORT SORT1) and advanced_options.sthlp (yoverhangs, xoverhangs), and
#: measured with a .gph identity ladder (the shortest prefix twoway accepts
#: whose saved graph is the full name's).  sort1's is sort: a digit ends
#: -syntax-'s run of capitals, so SORT1 admits sort(), and twoway takes
#: sort(t) as sort1(t) -- measured 23sep2026, identical .gph, where so(t)
#: and sor(t) are r(198).  It read sort1 while test_abbreviations counted
#: the digit into the run.
_F3_PLOT = {"clcolor": "clc", "clpattern": "clp", "clwidth": "clw",
            "mlabangle": "mlabang", "mlabformat": "mlabf",
            "mlabtextstyle": "mlabt", "mlabvposition": "mlabv",
            "sort1": "sort", "xoverhangs": "xoverhang",
            "yoverhangs": "yoverhang"}
_F3_GRAPH = {"xoverhangs": "xoverhang", "yoverhangs": "yoverhang"}

#: The F3 names twoway itself refuses where the user writes them (measured
#: r(198) on `twoway scatter mpg weight, <option>'): an option of another
#: command, a sub-option of another option, or no Stata option at all.
_F3_NOT_TWOWAY = ("xreverse", "yreverse", "xalternate", "yalternate",
                  "xcommon", "ycommon", "lockaspect", "zoom", "altaxis",
                  "ddensity", "addplot", "margin", "region", "bargap")


class TestTheDeclarations:
    """Structural guards over dash.ado's -syntax- declarations and rule
    table, which pytest cannot run (they are Stata).  Each reads the
    declared minimum, or a rule's bound, out of the source.

    A declaration that matches twoway's minimum does not by itself prove
    dash behaves like twoway: the option could be rewritten to another name
    before -syntax- sees it (measured 24sep2026: with `mlaban(' rewritten
    to `mlabangle(', or `xoverhan' to `xoverhangs', ahead of the parser,
    every test here stayed green), and the clwidth ceiling read here is
    never exercised at its edge.  The behaviour -- twoway's minimum taken
    as the option, the spelling one letter shorter refused and named as
    typed, and clwidth()/lwidth() drawn at 0 and 10000 and refused past
    them -- is measured against twoway in test_twoway_option_parity.cscript
    TP-02..TP-06 and TP-13, which those four mutations each fail."""

    @pytest.mark.parametrize("name,minimum", sorted(_F3_PLOT.items()))
    def test_the_plot_parser_declares_it_with_twoways_minimum(self, name,
                                                             minimum):
        """Structural: the declared minimum, read from the source (see the
        class docstring).  The behaviour is the cscript's TP-13."""
        assert _declared("_dash_parse_plot_opts").get(name) == minimum

    @pytest.mark.parametrize("name,minimum", sorted(_F3_GRAPH.items()))
    def test_the_graph_parser_declares_it_with_twoways_minimum(self, name,
                                                              minimum):
        """Structural: the declared minimum, read from the source (see the
        class docstring).  The behaviour is the cscript's TP-13b."""
        assert _declared("_dash_parse_graph_opts").get(name) == minimum

    @pytest.mark.parametrize("name", _F3_NOT_TWOWAY)
    def test_no_parser_declares_what_twoway_refuses(self, name):
        """Declaring one would list it in the help as a twoway option dash
        does not honour -- which twoway itself does not have."""
        for prog in ("_dash_parse_plot_opts", "_dash_parse_graph_opts"):
            assert name not in _declared(prog), (prog, name)

    def test_sort1_is_reported_as_sort_and_never_written(self):
        body = _program_body(_ado(), "_dash_parse_plot_opts")
        assert "_dash_pending' sort1" not in body
        writer = _program_body(_ado(), "_dash_plot_opts_to_json")
        assert " sort1 " not in writer and "sort1 {" not in writer

    def test_the_cl_gate_lists_the_types_that_draw_the_connecting_line(self):
        body = _program_body(_ado(), "_dash_fold_cl") or ""
        m = __import__("re").search(r'local cl_types\s+"([^"]+)"', body)
        assert m, "_dash_fold_cl no longer holds its type list"
        assert sorted(m.group(1).split()) == sorted(_CL_TYPES + _CI_TYPES)

    def test_the_mlabangle_rule_names_the_types_twoway_refuses_it_on(self):
        """Measured: twoway refuses mlabangle(400), r(198), on scatter
        connected bar dot dropline rcapsym rconnected rscatter pcscatter
        pccapsym scatteri, and never evaluates it on line, spike, area,
        the range lines and bars, rcap and the fits, which draw no marker
        label.  pccapsym was measured with the marker-label parity work
        (23sep2026): r(198), where this rule accepted it.  pcarrow and
        pcbarrow draw labels and still return rc 0 -- twoway prints
        "textangle must be between -360.000 and 360.000" and draws the
        arrows without their labels -- so they are not refused either."""
        rules = _program_body(_ado(), "_dash_option_rules")
        m = __import__("re").search(r"mlabangle=style,-360,360@([a-z|]+)",
                                    rules)
        assert m, "no mlabangle rule"
        assert sorted(m.group(1).split("|")) == sorted(
            ["scatter", "connected", "bar", "dot", "dropline", "rcapsym",
             "rconnected", "rscatter", "pcscatter", "pccapsym", "scatteri"])

    def test_clwidth_has_lwidths_bounds(self):
        """Structural: the rule's bounds, read from the source (see the
        class docstring).  The ceiling is exercised at its edge -- 10000
        drawn, 10000.001 refused, for clwidth() and lwidth() alike -- in
        the cscript's TP-13c."""
        rules = _program_body(_ado(), "_dash_option_rules")
        assert "clwidth=style,0,10000" in rules


# ===========================================================================
# 1. The anglestyle reader
# ===========================================================================

class TestTheAnglestyleReader:
    """``_dash_anglestyle_degrees`` -- Stata's anglestyle names, measured.

    The ten names are the ones Stata installs as anglestyle-*.style under
    ado/base/style, with the ``set val`` each declares.
    """

    @pytest.mark.parametrize("name,deg", [
        ("horizontal", 0.0), ("vertical", 90.0), ("rvertical", 270.0),
        ("rhorizontal", 180.0), ("zero", 0.0), ("default", 0.0),
        ("forty_five", 45.0), ("ninety", 90.0), ("two_seventy", 270.0),
        ("stdarrow", 28.64),
    ])
    def test_every_named_style(self, name, deg):
        assert dr._dash_anglestyle_degrees(name) == pytest.approx(deg)

    @pytest.mark.parametrize("raw,deg", [
        ("45", 45.0), (" 45 ", 45.0), ("45.0", 45.0), ("+45", 45.0),
        ("-90", -90.0), ("1e1", 10.0), ("360", 360.0), ("-360", -360.0),
        ("0", 0.0),
    ])
    def test_a_number_is_degrees(self, raw, deg):
        assert dr._dash_anglestyle_degrees(raw) == pytest.approx(deg)

    @pytest.mark.parametrize("raw", [
        "Vertical", "VERTICAL", "abc", "", None, "400", "-361", "inf",
        "nan", "1e400", "45 90", "45deg",
    ])
    def test_anything_else_is_not_an_angle(self, raw):
        """Stata's style names are case-sensitive (measured: Vertical is
        "named style Vertical not found"), and twoway refuses a number
        outside -360 to 360 when it draws the label."""
        assert dr._dash_anglestyle_degrees(raw) is None


# ===========================================================================
# 2. The connecting-line options on one glyph
# ===========================================================================

def _line_with(options):
    gm = dr.GlyphMapper(scheme=dr.SchemeParser("s2color"))
    fig = figure()
    src = ColumnDataSource({"x": [1.0, 2.0, 3.0], "y": [3.0, 1.0, 2.0]})
    r = fig.line(x="x", y="y", source=src, line_color="#000000",
                 line_width=1.5)
    _, notes = _notes(lambda: gm._apply_line_opts(r, dict(options)))
    return r.glyph, notes


class TestTheConnectingLineOptions:
    def test_clcolor_colours_the_line(self):
        g, notes = _line_with({"clcolor": "red"})
        assert g.line_color.lower() == _hex("red") and not notes

    @pytest.mark.parametrize("options", [
        {"lcolor": "red", "clcolor": "blue"},
        {"clcolor": "blue", "lcolor": "red"},
    ], ids=["lcolor first", "clcolor first"])
    def test_clcolor_beats_lcolor_in_either_order(self, options):
        """twoway factors CLColor() after LColor(), whatever the order."""
        g, _ = _line_with(options)
        assert g.line_color.lower() == _hex("blue")

    def test_clcolor_beats_color(self):
        g, _ = _line_with({"color": "green", "clcolor": "blue"})
        assert g.line_color.lower() == _hex("blue")

    def test_clwidth_beats_lwidth(self):
        g, _ = _line_with({"lwidth": "vthin", "clwidth": "vthick"})
        assert g.line_width == pytest.approx(
            dr.OptionTranslator.translate_lwidth("vthick"))

    def test_clpattern_beats_lpattern(self):
        g, _ = _line_with({"lpattern": "dot", "clpattern": "dash"})
        assert list(g.line_dash) == list(
            dr.OptionTranslator.translate_lpattern("dash"))

    def test_the_l_options_still_work_alone(self):
        g, _ = _line_with({"lcolor": "red", "lwidth": "vthick",
                           "lpattern": "dash"})
        assert g.line_color.lower() == _hex("red")
        assert g.line_width == pytest.approx(
            dr.OptionTranslator.translate_lwidth("vthick"))

    def test_an_opacity_in_clcolor_is_honoured_and_lalpha_still_wins(self):
        g, _ = _line_with({"clcolor": "red%30"})
        assert g.line_alpha == pytest.approx(0.3)
        g, _ = _line_with({"clcolor": "red%30", "lalpha": "80"})
        assert g.line_alpha == pytest.approx(0.8)

    def test_clcolor_none_draws_no_line(self):
        g, _ = _line_with({"clcolor": "none"})
        assert g.line_alpha == 0.0

    def test_a_bad_clcolor_is_named_as_written(self):
        """twoway: "named style notacolour not found in class color, default
        attributes used" -- the DEFAULT, not lcolor()'s colour."""
        g, notes = _line_with({"lcolor": "red", "clcolor": "notacolour"})
        assert notes == ["dash: clcolor(notacolour) is not a recognised "
                         "colour; using the scheme's default."], notes
        assert g.line_color.lower() != _hex("red")

    def test_a_bad_clwidth_and_clpattern_are_named_as_written(self):
        _, notes = _line_with({"clwidth": "abc", "clpattern": "nopattern"})
        assert sorted(notes) == sorted([
            "dash: clwidth(abc) is not a recognised line width; using the "
            "scheme's default.",
            "dash: clpattern(nopattern) is not a recognised line pattern; "
            "using the scheme's default."]), notes


# ===========================================================================
# 3. On every layer that draws a connecting line, in both modes
# ===========================================================================

#: The types whose connecting line twoway styles with the cl options.
_CL_TYPES = ["line", "connected", "lfit", "qfit", "fpfit", "lpoly", "lowess",
             "mspline", "mband", "kdensity", "function", "tsline"]
_CI_TYPES = ["lfitci", "qfitci", "lpolyci", "fpfitci"]


def _one_line(fig):
    lines = _glyphs(fig, "Line")
    assert len(lines) == 1, [type(r.glyph).__name__ for r in fig.renderers]
    return lines[0]


@pytest.mark.parametrize("ptype", _CL_TYPES + _CI_TYPES)
def test_the_triple_styles_the_line_in_both_modes(ptype):
    opts = {"clcolor": "red", "clpattern": "dash", "clwidth": "vthick"}
    r, doc, std_w, srv_w = _both([plot_for(ptype, opts)])
    assert std_w == srv_w, (std_w, srv_w)
    assert not [w for w in std_w if "clcolor" in w or "clwidth" in w
                or "clpattern" in w], std_w
    for fig in _figures(r, doc):
        g = _one_line(fig)
        assert g.line_color.lower() == _hex("red"), (ptype, g.line_color)
        assert g.line_width == pytest.approx(
            dr.OptionTranslator.translate_lwidth("vthick"))
        assert list(g.line_dash) == list(
            dr.OptionTranslator.translate_lpattern("dash"))


@pytest.mark.parametrize("ptype", _CI_TYPES)
def test_on_a_ci_type_the_band_is_untouched(ptype):
    """clcolor() styles the fit line; the band keeps the scheme's fill."""
    r0, d0, _, _ = _both([plot_for(ptype)])
    r1, d1, _, _ = _both([plot_for(ptype, {"clcolor": "red"})])
    for (a, b) in zip(_figures(r0, d0), _figures(r1, d1)):
        fa = [g.fill_color for g in _glyphs(a, "VArea")]
        fb = [g.fill_color for g in _glyphs(b, "VArea")]
        assert fa and fa == fb, (fa, fb)


def test_on_connected_the_markers_are_untouched():
    """twoway: connected ..., clcolor(red) clwidth(vthick) restyles the line
    alone -- the markers are the ones drawn with no option at all."""
    r0, d0, _, _ = _both([plot_for("connected")])
    r1, d1, _, _ = _both([plot_for("connected", {"clcolor": "red",
                                                 "clwidth": "vthick"})])
    for (a, b) in zip(_figures(r0, d0), _figures(r1, d1)):
        ma, mb = _glyphs(a, "Scatter"), _glyphs(b, "Scatter")
        assert ma and len(ma) == len(mb)
        for x, y in zip(ma, mb):
            assert (x.line_color, x.line_width, x.fill_color) == \
                (y.line_color, y.line_width, y.fill_color)
        assert _one_line(b).line_color.lower() == _hex("red")


@pytest.mark.parametrize("options,want", [
    ({"lcolor": "red", "clcolor": "blue"}, "blue"),
    ({"clcolor": "blue", "lcolor": "red"}, "blue"),
    ({"color": "green", "clcolor": "blue"}, "blue"),
])
def test_precedence_in_both_modes(options, want):
    r, doc, std_w, srv_w = _both([plot_for("line", options)])
    assert std_w == srv_w
    for fig in _figures(r, doc):
        assert _one_line(fig).line_color.lower() == _hex(want)


def test_a_bad_clcolor_is_named_once_in_both_modes():
    _, _, std_w, srv_w = _both([plot_for("line", {"clcolor": "notacolour"})])
    assert std_w == srv_w
    hits = [w for w in std_w if "clcolor(notacolour)" in w]
    assert len(hits) == 1, std_w


# ===========================================================================
# 4. mlabangle()
# ===========================================================================

@pytest.mark.parametrize("raw,deg", [
    ("45", 45.0), ("vertical", 90.0), ("rvertical", 270.0),
    ("forty_five", 45.0), ("-30", -30.0),
])
def test_mlabangle_rotates_the_labels_in_both_modes(raw, deg):
    r, doc, std_w, srv_w = _both(
        [plot_for("scatter", {"mlabel": "make", "mlabangle": raw})])
    assert std_w == srv_w and not std_w, (std_w, srv_w)
    for fig in _figures(r, doc):
        ls = _labelset(fig)
        assert float(ls.angle) == pytest.approx(math.radians(deg))
        assert ls.angle_units == "rad"


def test_no_mlabangle_draws_horizontal_labels():
    r, doc, _, _ = _both([plot_for("scatter", {"mlabel": "make"})])
    for fig in _figures(r, doc):
        assert float(_labelset(fig).angle) == 0.0


@pytest.mark.parametrize("raw", ["Vertical", "400", "abc"])
def test_a_bad_mlabangle_is_named_and_drawn_horizontal(raw):
    """twoway notes an unknown name and draws horizontal; a number outside
    -360..360 dash.ado refuses where twoway does, and a spec that carries
    one anyway draws horizontal with the same note."""
    r, doc, std_w, srv_w = _both(
        [plot_for("scatter", {"mlabel": "make", "mlabangle": raw})])
    assert std_w == srv_w
    assert std_w == [f"dash: mlabangle({raw}) is not a recognised angle; "
                     f"using horizontal."], std_w
    for fig in _figures(r, doc):
        assert float(_labelset(fig).angle) == 0.0


def test_mlabangle_reaches_every_layer_that_labels():
    """rcapsym labels both of its ends -- one LabelSet each -- as twoway
    does (test_marker_label_parity.py), and the angle reaches both."""
    for ptype in ("connected", "bar", "dropline", "rcapsym"):
        r, doc, std_w, srv_w = _both(
            [plot_for(ptype, {"mlabel": "make", "mlabangle": "45"})])
        assert std_w == srv_w
        for fig in _figures(r, doc):
            sets = [x for x in fig.center if isinstance(x, LabelSet)]
            assert len(sets) == (2 if ptype == "rcapsym" else 1), ptype
            for ls in sets:
                assert float(ls.angle) == pytest.approx(
                    math.radians(45)), ptype


# ===========================================================================
# 5. mlabformat()
# ===========================================================================

@pytest.mark.parametrize("var,fmt,first_two", [
    ("mpg", "%9.2f", ["22.00", "17.00"]),
    ("price", "%9.1fc", ["4,099.0", "4,749.0"]),
    ("price", "%9.2e", ["4.10e+03", "4.75e+03"]),
    ("weight", "%9.0fc", ["2,930", "3,350"]),
    ("mpg", "%-9.1f", ["22.0", "17.0"]),
])
def test_mlabformat_formats_numeric_labels_in_both_modes(var, fmt, first_two):
    r, doc, std_w, srv_w = _both(
        [plot_for("scatter", {"mlabel": var, "mlabformat": fmt})])
    assert std_w == srv_w and not std_w, (std_w, srv_w)
    for fig in _figures(r, doc):
        assert _texts(_labelset(fig))[:2] == first_two


def test_mlabformat_changes_nothing_on_a_string_variable():
    r0, d0, _, _ = _both([plot_for("scatter", {"mlabel": "make"})])
    r1, d1, s1, v1 = _both(
        [plot_for("scatter", {"mlabel": "make", "mlabformat": "%9.2f"})])
    assert s1 == v1 and not s1, s1
    for a, b in zip(_figures(r0, d0), _figures(r1, d1)):
        assert _texts(_labelset(a)) == _texts(_labelset(b)) == list(_DF["make"])


def test_mlabformat_changes_nothing_on_a_value_labelled_variable():
    """twoway draws a value-labelled variable's labels whatever the format
    (measured: foreign with mlabformat(%9.2f) is the picture without it)."""
    r0, d0, _, _ = _both([plot_for("scatter", {"mlabel": "foreign"})])
    r1, d1, s1, v1 = _both(
        [plot_for("scatter", {"mlabel": "foreign", "mlabformat": "%9.2f"})])
    assert s1 == v1 and not s1, s1
    for a, b in zip(_figures(r0, d0), _figures(r1, d1)):
        assert _texts(_labelset(a)) == _texts(_labelset(b))


@pytest.mark.parametrize("fmt", ["abc", "%9.3g", "%td", "%12s"])
def test_a_format_dash_does_not_reproduce_is_named(fmt):
    r0, d0, _, _ = _both([plot_for("scatter", {"mlabel": "mpg"})])
    r1, d1, s1, v1 = _both(
        [plot_for("scatter", {"mlabel": "mpg", "mlabformat": fmt})])
    assert s1 == v1
    assert s1 == [f"dash: mlabformat({fmt}) is not a display format dash "
                  f"reproduces; the labels are drawn without it."], s1
    for a, b in zip(_figures(r0, d0), _figures(r1, d1)):
        assert _texts(_labelset(a)) == _texts(_labelset(b))


def test_two_layers_label_one_variable_in_two_formats():
    """The saved page shares one source: a cached label column keyed by the
    variable alone would give the second layer the first layer's format."""
    r, doc, std_w, srv_w = _both([
        plot_for("scatter", {"mlabel": "mpg", "mlabformat": "%9.2f"}),
        plot_for("scatter", {"mlabel": "mpg", "mlabformat": "%9.1f"}),
    ])
    assert std_w == srv_w
    for fig in _figures(r, doc):
        sets = [x for x in fig.center if isinstance(x, LabelSet)]
        assert sorted(_texts(s)[0] for s in sets) == ["22.0", "22.00"]


def test_mlabformat_on_a_date_variable_is_named_and_the_dates_kept():
    """A date variable's labels are drawn as dates; the format is named.
    (The saved renderer only: the served app's date gap is BUGS.md's.)"""
    gm = dr.GlyphMapper(scheme=dr.SchemeParser("s2color"))
    gm.date_vars = {"when": "td"}
    fig = figure()
    src = ColumnDataSource({
        "x": [1.0, 2.0], "y": [3.0, 4.0],
        "when": list(pd.to_datetime(["2020-01-16", "2020-02-01"]))})
    _, notes = _notes(lambda: gm._apply_mlabel_opts(
        fig, src, {"mlabel": "when", "mlabformat": "%9.2f"}, "x", "y"))
    assert notes == ["dash: mlabformat(%9.2f) is not applied to the date "
                     "variable when; its labels are drawn as dates."], notes
    ls = _labelset(fig)
    assert ls.text == "__mlabel__when"
    assert _texts(ls) == ["16 Jan 2020", "01 Feb 2020"]


def test_the_formatted_column_is_named_by_variable_and_format():
    gm = dr.GlyphMapper(scheme=dr.SchemeParser("s2color"))
    src = ColumnDataSource({"x": [1.0], "y": [2.0], "v": [3.14159]})
    col = gm._mlabformat_column(src, "v", "%9.2f", "v")
    assert col == "__mlabel__v__fmt_" + "%9.2f".encode("utf-8").hex()
    assert list(src.data[col]) == ["3.14"]
    assert gm._mlabformat_column(src, "v", "%9.3f", "v") != col


def test_mlabformat_on_a_line_layer_in_both_modes():
    r, doc, std_w, srv_w = _both(
        [plot_for("connected", {"mlabel": "mpg", "mlabformat": "%9.1f"})])
    assert std_w == srv_w
    for fig in _figures(r, doc):
        assert "22.0" in _texts(_labelset(fig))


# ===========================================================================
# 6. Adversarial cases (CLAUDE.md rule 18), registered in
#    test_adversarial_matrix.py's SURFACES under style_plot_options
#    (clcolor()/clpattern()/clwidth(), mlabangle()) and text_plot_options
#    (mlabformat()).
# ===========================================================================

_ARABIC_45 = "\u0664\u0665"          # Arabic-Indic digits four, five
_ARABIC_FMT = "%\u0669.\u0662f"      # "%9.2f" in Arabic-Indic digits


class TestAdversarialTwowayOptions:
    # ---- bypass: an encoding that must not pass for a value -------------
    def test_an_angle_in_another_scripts_digits_is_not_an_angle(self):
        """Python's float() reads Arabic-Indic digits as 45; Stata reads a
        name, notes it, and draws horizontal.  So must dash."""
        assert float(_ARABIC_45) == 45.0          # the trap is real
        assert dr._dash_anglestyle_degrees(_ARABIC_45) is None
        assert dr._dash_anglestyle_degrees("45\x00") is None
        assert dr._dash_anglestyle_degrees("\uff14\uff15") is None  # fullwidth

    def test_a_format_in_another_scripts_digits_is_not_applied(self):
        """_parse_stata_numeric_fmt's \\d reads Arabic-Indic digits, so the
        format is refused as not ASCII before it is parsed."""
        assert dr._parse_stata_numeric_fmt(_ARABIC_FMT) is not None  # trap
        gm = dr.GlyphMapper(scheme=dr.SchemeParser("s2color"))
        src = ColumnDataSource({"x": [1.0], "y": [2.0], "v": [3.14159]})
        col, notes = _notes(lambda: gm._mlabformat_column(
            src, "v", _ARABIC_FMT, "v"))
        assert col == "v"
        assert len(notes) == 1 and "is not a display format" in notes[0]
        assert list(src.data) == ["x", "y", "v"]

    # ---- injection: markup or code in a value -----------------------------
    @pytest.mark.parametrize("key,value", [
        ("mlabformat", "</script><script>alert(1)</script>"),
        ("mlabangle", "45); import os; os.system('x')"),
        ("mlabangle", "{bf:45}"),
    ])
    def test_markup_in_a_value_is_named_as_text_and_never_drawn(self, key,
                                                              value):
        opts = {"mlabel": "mpg", key: value}
        r, doc, std_w, srv_w = _both([plot_for("scatter", opts)])
        assert std_w == srv_w and len(std_w) == 1, std_w
        page = tp._standalone_page(tp._spec([plot_for("scatter", opts)]))[2]
        # The page-string search `"<script>alert(1)" not in page' could never
        # fail: Bokeh HTML-escapes the document JSON on the way into the page
        # (bokeh/embed/elements.py), so a raw "<script>" never reaches it,
        # and two of the three payloads do not even contain that needle
        # (24sep2026).  The security property is read on the DECODED
        # document instead -- json.loads reverses Bokeh's escaping, so a
        # payload that had reached any model would be a raw string there --
        # and the decode is its own positive control: it must reconstruct
        # the Scatter this graph draws, or it proves nothing.
        blob = _decoded_document_blob(page)
        assert "Scatter" in blob, (
            "the page's Bokeh document did not decode; the absence check "
            "below would be vacuous"
        )
        assert value not in blob, (
            f"the payload {value!r} survived into the served document"
        )
        assert "<script>alert(1)" not in blob and "os.system" not in blob
        for fig in _figures(r, doc):
            ls = _labelset(fig)
            assert float(ls.angle) == 0.0
            assert all(not isinstance(t, str) or "<" not in t
                       for t in _texts(ls))

    def test_a_colour_that_is_code_is_refused_by_the_colour_reader(self):
        _, notes = _line_with({"clcolor": "red\"; alert(1); \""})
        assert len(notes) == 1 and notes[0].startswith("dash: clcolor(")

    # ---- exhaustion: a value built to cost time or memory -------------------
    def test_a_megabyte_angle_is_judged_at_once(self):
        import time
        t0 = time.monotonic()
        assert dr._dash_anglestyle_degrees("4" * 1_000_000) is None
        assert dr._dash_anglestyle_degrees("vertical" * 100_000) is None
        assert time.monotonic() - t0 < 0.5

    @pytest.mark.parametrize("fmt", ["%9.999999999f", "%2046.2f",
                                     "%1" + "0" * 5000 + ".2f"])
    def test_a_format_stata_refuses_builds_no_giant_label(self, fmt):
        gm = dr.GlyphMapper(scheme=dr.SchemeParser("s2color"))
        src = ColumnDataSource({"x": [1.0, 2.0], "y": [2.0, 3.0],
                                "v": [1.5, 2.5]})
        col, notes = _notes(lambda: gm._mlabformat_column(src, "v", fmt, "v"))
        assert col == "v" and len(notes) == 1
        assert list(src.data) == ["x", "y", "v"]
        assert len(notes[0]) < 300

    def test_the_widest_format_stata_accepts_is_bounded_by_stata(self):
        """%2045.2044f is Stata's own ceiling (confirm numeric format); a
        label in it is at most 2,046 characters, as Stata would draw it."""
        gm = dr.GlyphMapper(scheme=dr.SchemeParser("s2color"))
        src = ColumnDataSource({"x": [1.0], "y": [2.0], "v": [1.5]})
        col = gm._mlabformat_column(src, "v", "%2045.2044f", "v")
        assert len(src.data[col][0]) <= 2046

    def test_a_non_finite_clwidth_is_named_not_drawn(self):
        g, notes = _line_with({"clwidth": "1e400"})
        assert notes and "clwidth(1e400)" in notes[0]
        assert math.isfinite(g.line_width)
