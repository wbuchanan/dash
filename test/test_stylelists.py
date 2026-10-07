"""Stylelists of style options across an expanded varlist (WP-30 P1.1a).

The defect, measured at c96facd (probe p7.do): ``scatter mpg turn weight,
mcolor(red blue) msymbol(O T)`` gave both plot objects
``{'mcolor': 'red blue', 'msymbol': 'O T'}``, so both modes drew two
series in the scheme's navy and maroon circles with "mcolor(red blue) is
not a recognised colour" notes; ``mcolor(red)`` coloured both series red;
``mcolor("255 0 0" "0 0 255")`` lost its quotes (``255 0 0 0 0 255``);
``mcolor(red .. blue)`` was drawn with a note; and a single-y
``mcolor(red blue)`` drew the scheme's navy.

twoway (StataNow 19.5, s2color) reads each as a stylelist ([G-4]
stylelists): T01 draws red circles then blue triangles, T02
(``mcolor(red)``) red then p2 (#90353b), T23 (``mcolor(red)
mcolor("")``) p1 then p2, and ``mcolor(red .. blue)`` is
``mcolor(red .. blue):  invalid syntax``, r(198).

The Stata half (the splitter, the spec dash.ado writes, the refusals) is
test_varlist_expansion.cscript's SL run; this module pins the code's
structure, and that both renderers draw each series' own options object
in twoway's colour, symbol and dash.  The twoway readings below are the
measured ones of the section's probes (p1-01.md, p1.do, p3.do-p6.do); no
size, alpha or label style is compared.
"""
import os
import re
import sys

from bokeh.models import GlyphRenderer, Plot

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import test_mode_parity as mp  # noqa: E402
from test_abbreviations import _program_body  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_ADO = os.path.join(_HERE, "..", "dash.ado")
_MATA = os.path.join(_HERE, "..", "dash_parse.mata")
_HLP = os.path.join(_HERE, "..", "dash.sthlp")

_STYLE_KEYS = (
    "mcolor msymbol msize msangle mfcolor mlcolor mlwidth mlabcolor "
    "mlabsize mlabposition mlabgap mlabangle mlabformat lcolor lwidth "
    "lpattern clcolor clpattern clwidth color fcolor fintensity bfcolor "
    "blcolor acolor alcolor alwidth alpattern").split()
_NOT_YET = ("mlabel", "jitter", "base", "barwidth", "pstyle", "mstyle",
            "lstyle", "mlstyle", "mlabtextstyle", "connect", "cmissing",
            "malpha", "lalpha", "falpha", "jseed", "mlabwidth", "mlpattern",
            "marker")

# s2color's p1, p2 and p3.
P1, P2, P3 = "#1a476f", "#90353b", "#55752f"
RED, BLUE = "#ff0000", "#0000ff"

# case id -> (ptype, per-series option dicts): the objects dash.ado writes
# (test_varlist_expansion.cscript SL-12..SL-17), and twoway's per-series
# reading, (colour, marker) or (colour, dashed).  The y variables are the
# parity data's mpg, price and rep.
_SERIES = {
    "T01": ("scatter", [{"mcolor": "red", "msymbol": "O"},
                        {"mcolor": "blue", "msymbol": "T"}],
            [(RED, "circle"), (BLUE, "triangle")]),
    "T02": ("scatter", [{"mcolor": "red"}, {}], [(RED, None), (P2, None)]),
    "T03": ("scatter", [{"mcolor": "red"}, {"mcolor": "blue"}, {}],
            [(RED, None), (BLUE, None), (P3, None)]),
    "T04": ("scatter", [{"mcolor": "red"}, {"mcolor": "blue"}],
            [(RED, None), (BLUE, None)]),
    "T05": ("scatter", [{}, {"mcolor": "blue"}], [(P1, None), (BLUE, None)]),
    "T06": ("scatter", [{"mcolor": "red"}, {"mcolor": "red"},
                        {"mcolor": "blue"}],
            [(RED, None), (RED, None), (BLUE, None)]),
    "T07": ("scatter", [{"mcolor": "red"}] * 3, [(RED, None)] * 3),
    "T08": ("scatter", [{"mcolor": "red"}] * 3, [(RED, None)] * 3),
    "T12": ("scatter", [{}, {"mcolor": "blue"}], [(P1, None), (BLUE, None)]),
    "T13": ("scatter", [{"mcolor": "red"}] * 3, [(RED, None)] * 3),
    "T15": ("scatter", [{}, {}, {}], [(P1, None), (P2, None), (P3, None)]),
    "T16": ("scatter", [{"mcolor": "red"}, {}, {}],
            [(RED, None), (P2, None), (P3, None)]),
    "T17": ("scatter", [{"mcolor": "red"}] * 3, [(RED, None)] * 3),
    "T18": ("scatter", [{}, {}, {}], [(P1, None), (P2, None), (P3, None)]),
    "T11": ("scatter", [{"mcolor": "255 0 0"}, {"mcolor": "0 0 255"}],
            [(RED, None), (BLUE, None)]),
    "T20": ("scatter", [{"mcolor": "red"}, {"mcolor": "blue"}],
            [(RED, None), (BLUE, None)]),
    "T21": ("scatter", [{}, {"mcolor": "blue"}], [(P1, None), (BLUE, None)]),
    "T22": ("scatter", [{"mcolor": "red"}, {}], [(RED, None), (P2, None)]),
    "T10": ("line", [{"lcolor": "red", "lpattern": "solid", "sort": "sort"},
                     {"lcolor": "blue", "lpattern": "dash", "sort": "sort"}],
            [(RED, False), (BLUE, True)]),
    "W36": ("line", [{"lcolor": "red", "sort": "sort"},
                     {"lpattern": "dash", "sort": "sort"}, {"sort": "sort"}],
            [(RED, False), (P2, True), (P3, False)]),
    "T09": ("scatter", [{"mcolor": "red"}], [(RED, None)]),
    "T19": ("scatter", [{"msymbol": "T"}], [(P1, "triangle")]),
}
_YVARS = ("mpg", "price", "rep")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _plots(case):
    ptype, objs, _ = _SERIES[case]
    return [plot_for(ptype, dict(o), yvar=_YVARS[i])
            for i, o in enumerate(objs)]


def _spec(case, **kw):
    return mp._spec(_plots(case), build_options={"scheme": "s2color"}, **kw)


def _figures(models):
    return [m for m in models if isinstance(m, Plot)]


def _series(fig):
    """(colour, marker, dashed) of each drawn glyph, in drawing order."""
    out = []
    for r in fig.renderers:
        if not isinstance(r, GlyphRenderer):
            continue
        g = r.glyph
        name = type(g).__name__
        if name == "Scatter":
            out.append((str(g.fill_color).lower(), str(g.marker), None))
        elif name == "Line":
            out.append((str(g.line_color).lower(), None, bool(g.line_dash)))
    return out


def _both(case, **kw):
    """{mode: (series of the one figure, warnings)}."""
    spec = _spec(case, **kw)
    r, w_saved = mp._standalone(spec)
    saved = _figures(r._last_layout_root.references())
    doc, w_served = mp._served(spec)
    served = _figures([m for root in doc.roots for m in root.references()])
    return {"saved": (saved, w_saved), "served": (served, w_served)}


def _check(case):
    want = _SERIES[case][2]
    for mode, (figs, _w) in _both(case).items():
        assert len(figs) == 1, (case, mode, figs)
        got = _series(figs[0])
        assert len(got) == len(want), (case, mode, got)
        for (gc, gm, gd), (wc, wk) in zip(got, want):
            assert gc == wc, (case, mode, got, want)
            if isinstance(wk, str):
                assert gm == wk, (case, mode, got, want)
            elif isinstance(wk, bool):
                assert gd is wk, (case, mode, got, want)


class TestTheParserKeepsQuotes:
    def _syntax(self):
        body = _program_body(_read(_ADO), "_dash_parse_plot_opts")
        return body[body.index("syntax [,"):body.index("\n    ]\n")]

    def test_each_style_option_is_declared_asis(self):
        decl = {m.group(1).lower(): m.group(2) for m in re.finditer(
            r"\b([A-Za-z0-9]+)\((string(?: asis)?)\)", self._syntax())}
        for k in _STYLE_KEYS:
            assert decl[k] == "string asis", k

    def test_the_later_lists_are_not_yet_asis(self):
        decl = {m.group(1).lower(): m.group(2) for m in re.finditer(
            r"\b([A-Za-z0-9]+)\((string(?: asis)?)\)", self._syntax())}
        for k in _NOT_YET:
            assert decl[k] == "string", k

    def test_empty_quotes_are_normalised_before_any_test(self):
        body = _program_body(_read(_ADO), "_dash_parse_plot_opts")
        after = body[body.index("\n    ]\n"):]
        code = [ln for ln in after.split("\n")
                if ln.strip() not in ("", "]")
                and not ln.strip().startswith("//")]
        assert "_dash_stylelist_keys()" in code[0]
        assert "_dash_stylelist_norm" in "\n".join(code[:4])
        assert after.index("_dash_stylelist_norm") < after.index(
            ": length local")


class TestOneList:
    def test_the_mata_key_list_is_the_declared_set(self):
        src = _read(_MATA)
        m = re.search(r"string scalar _dash_stylelist_keys\(\)\s*\{(.*?)\n\}",
                      src, re.S)
        lit = "".join(re.findall(r'"([^"]*)"', m.group(1)))
        assert lit.split() == _STYLE_KEYS

    def test_every_listed_key_reaches_the_json_writer(self):
        body = _program_body(_read(_ADO), "_dash_plot_opts_to_json")
        keys = re.search(r"foreach key in (.*?)\{", body, re.S).group(1)
        keys = set(keys.replace("///", " ").split())
        assert set(_STYLE_KEYS) <= keys

    def test_the_six_are_public_and_needed(self):
        six = ("_dash_stylelist_keys", "_dash_stylelist_norm",
               "_dash_stylelist_pick", "_dash_stylelist_bad",
               "_dash_stylelist_blank", "_dash_stylelist_probe")
        hdr = _read(_MATA)
        needed = _program_body(_read(_ADO), "_dash_require_mata")
        needed = needed[needed.index("local _needed"):needed.index(
            "local _missing")]
        for f in six:
            assert re.search(r"^\*!   %s\(" % f, hdr, re.M), f
            assert re.search(r"\b%s\b" % f, needed), f


class TestOneOptionsObjectPerSeries:
    def test_the_writer_takes_the_series(self):
        body = _program_body(_read(_ADO), "_dash_plot_opts_to_json")
        assert "args out_macro series" in body
        assert "_dash_stylelist_pick(" in body

    def test_the_writer_is_called_inside_the_y_loop(self):
        body = _program_body(_read(_ADO), "_dash_process_segment")
        loop = body[body.index("forvalues _yi = 1/`_nyv' {"):]
        loop = loop[:loop.index("\n        }\n")]
        assert "_dash_plot_opts_to_json _opts_json `_yi'" in loop

    def test_the_check_runs_after_validation(self):
        body = _program_body(_read(_ADO), "_dash_process_segment")
        v = body.index('_dash_validate_opts "`ptype\'"')
        c = body.index("_dash_stylelist_check")
        assert v < c

    def test_the_repeats_probe_rekeys_an_empty_style_copy(self):
        body = _program_body(_read(_ADO), "_dash_opts_repeats")
        loop = body[body.index("forvalues i = 1/`_rp_n'"):body.index(
            "_dash_rep_reduce(")]
        assert "_dash_stylelist_probe" in loop

    def test_the_blank_check_follows_the_dotdot_check(self):
        body = _program_body(_read(_ADO), "_dash_stylelist_check")
        bad = body.index("_dash_stylelist_bad")
        blank = body.index("_dash_stylelist_blank")
        rules = body.index("_dash_option_rules")
        assert bad < blank < rules
        tail = body[blank:rules]
        assert '_dash_say("err", "dash: ' in tail
        assert "is blank; use . for the default (got: " in tail
        assert "exit 198" in tail
        seg = _program_body(_read(_ADO), "_dash_process_segment")
        assert seg.index("_dash_stylelist_check") < seg.index(
            "_dash_plot_opts_to_json")


class TestBothModesDrawTwowaysSeries:
    def test_marker_lists(self):
        for c in ("T01", "T03"):
            _check(c)

    def test_padding_and_extras(self):
        for c in ("T02", "T04"):
            _check(c)

    def test_shorthands(self):
        for c in ("T05", "T06", "T07", "T08", "T12", "T13", "T15", "T16",
                  "T17", "T18"):
            _check(c)

    def test_quoted_elements(self):
        for c in ("T11", "T20", "T21", "T22"):
            _check(c)

    def test_line_lists(self):
        for c in ("T10", "W36"):
            _check(c)

    def test_single_y_takes_the_first(self):
        for c in ("T09", "T19"):
            _check(c)

    def test_no_unrecognised_note(self):
        for c in ("T01", "T10", "T11", "T09"):
            for mode, (_f, w) in _both(c).items():
                assert not [m for m in w if "not a recognised" in m], (
                    c, mode, w)


class TestAfterAFilterMove:
    def test_served_range_move_keeps_each_series_style(self):
        import test_served_filter_move as sfm
        spec = mp._spec(_plots("T01"), build_options={
            "scheme": "s2color", "filter": "weight, type(range)"})
        doc, _w = mp._served(spec)
        figs = _figures([m for root in doc.roots for m in root.references()])
        before = _series(figs[0])

        def rows():
            return [len(next(iter(r.data_source.data.values())))
                    for r in figs[0].renderers
                    if isinstance(r, GlyphRenderer)]
        n0 = rows()
        sfm._move(doc, "RangeSlider", (2500.0, 4000.0))
        assert _series(figs[0]) == before == [(RED, "circle", None),
                                              (BLUE, "triangle", None)]
        assert rows() != n0

    def test_saved_page_writes_no_glyph_style(self):
        from bokeh.models import CustomJS
        spec = mp._spec(_plots("T01"), build_options={
            "scheme": "s2color", "filter": "weight, type(range)"})
        r, _w = mp._standalone(spec)
        codes = [m.code for m in r._last_layout_root.references()
                 if isinstance(m, CustomJS)]
        assert codes
        for code in codes:
            for needle in (".fill_color =", ".line_color =", ".marker =",
                           ".line_dash ="):
                assert needle not in code


class TestByPanels:
    def test_every_panel_draws_each_series_style(self):
        both = _both("T01", graph_options={"by": "foreign"})
        for mode, (figs, _w) in both.items():
            panels = [f for f in figs if _series(f)]
            assert len(panels) >= 2, (mode, panels)
            for f in panels:
                assert _series(f) == [(RED, "circle", None),
                                      (BLUE, "triangle", None)], mode


class TestTheHelpSaysSo:
    def test_the_stylelists_paragraph(self):
        # Read with blank runs closed up: the paragraph wraps between words.
        h = " ".join(_read(_HLP).split())
        for needle in ("{marker stylelists}",
                       "{cmd:mcolor(red .. blue): invalid syntax}",
                       "is refused when a y uses it",
                       "padded with {cmd:.}",
                       "{cmd:malpha()}, {cmd:lalpha()}, {cmd:falpha()} and "
                       "{cmd:jseed()}"):
            assert needle in h, needle

    def test_rgb_is_quoted(self):
        h = _read(_HLP)
        assert '{cmd:mcolor("255 0 0")}' in h
        assert "{cmd:mcolor(255,0,0)}" in h
