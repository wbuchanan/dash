"""WP-30 P1.19: twoway's sub-option abbreviations.

legend(), the axis label and tick options, xline()/yline() and the
textboxes read a sub-option as twoway's own parsers read it (StataNow 19.5,
ado/base): lower case only, from the capitalised minimum to the full name,
in the order the parser stages try them.  The expectations are twoway's,
measured 03oct2026 (plan section 10, Evidence).
"""
import itertools
import json
import os
import random
import sys
import time
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402
from conftest import make_data_json, load_app  # noqa: E402

_MODES = ("saved", "served")
_SEQ = itertools.count()

# ---------------------------------------------------------------------------
# Measured twoway refusals: option text -> twoway's first line (r(198)).
# ---------------------------------------------------------------------------
_LEGEND_REFUSALS = {
    "po(9)": "option po() not allowed",
    "rin(0) pos(5)": "option rin() not allowed",
    "ord(2 1)": "option ord() not allowed",
    "o(2 1)": "option o() not allowed",
    'lastl(1 "XX")': "option lastl() not allowed",
    "of": "option of not allowed",
    "OFF": "option OFF not allowed",
    "POS(9)": "option POS() not allowed",
    "Pos(9)": "option Pos() not allowed",
    "SIZE(large)": "option SIZE() not allowed",
    "Cols(1)": "option Cols() not allowed",
    "c(2) cols(1)": "option cols() not allowed",
    "pos(9) position(6)": "option position() not allowed",
    "size(large) size(small)": "option size() not allowed",
    "size(large) s(small)": "option s() not allowed",
    "order(1 2) order(2 1)": "option order() not allowed",
    "on on": "option on not allowed",
    "holes(1) holes(2)": "option holes() not allowed",
    "rows(1) r(2)": "option r() not allowed",
    "ring(0) pos(5) ring(1)": "option ring() not allowed",
    "c(2) c(3) c(4)": "option c() not allowed",
    "cols": "option cols not allowed",
    "on(1)": "option on() not allowed",
    "garbage": "option garbage not allowed",
    "xoffset(x)": "option xoffset() not allowed",
    "xoffset()": "option xoffset() not allowed",
    "yoffset(1 2)": "option yoffset() not allowed",
}

_AXIS_REFUSALS = {
    "lab(large)": "option lab() not allowed",
    "LABS(large)": "option LABS() not allowed",
    "LABSize(large)": "option LABSize() not allowed",
    "a(0)": "option a() not allowed",
    "an(45)": "option an() not allowed",
    "f(%9.1f)": "option f() not allowed",
    "fo(%9.1f)": "option fo() not allowed",
    "gl(red)": "option gl() not allowed",
    "nola": "option nola not allowed",
    "no": "option no not allowed",
    "va": "option va not allowed",
    "labs": "option labs incorrectly specified",
    "labsize": "option labsize incorrectly specified",
    "nog(1)": "option nog() incorrectly specified",
    "nogrid(1)": "option nogrid() incorrectly specified",
    "angle(45) ang(0)": "option ang() not allowed",
    "labsize(large) labsize(small)": "option labsize() not allowed",
    "format(%9.1f) for(%9.2f)": "option for() not allowed",
    "glc(red) glcolor(blue)": "option glcolor() not allowed",
    "labs(large) bogus": "option bogus not allowed",
    "bogus labs(large) labs(small)": "option bogus not allowed",
    "labs(large) labs": "option labs not allowed",
    "labs labs(large)": "option labs incorrectly specified",
    "labs(large) LABSIZE(small)": "option LABSIZE() not allowed",
    "labelminlen(x)": "option labelminlen() incorrectly specified",
    "labelminlen(1.5)": "option labelminlen() incorrectly specified",
    "labelminlen()": "option labelminlen() incorrectly specified",
}

_ACCEPTED = {
    "legend": ["cols(1) c(red)", "c(1) c(red)", "c(1) c(2)",
               "style(foreground) sty(foreground)",
               "region(fcolor(red)) reg(lcolor(blue))",
               'title("TA") title("TB")', 'label(1 "AA") lab(1 "BB")',
               "cols(2/2)", "cols(+2)", "cols()", "holes()", "label()",
               'label(01 "A")', 'label(+1 "A")', "pos( 9 )", "ring(-1)",
               "ring(1.5)", "on off", "off on", 't("TT")', 't1("TT")',
               ],
    "axis": ["labs(large)", "labsi(large)", "ang(45)", "form(%9.1f)",
             "for(%9.1f)", "nogr", "nog", "g", "gr", "gri", "glc(red)",
             "labc(red)", "nolab", "notick", "val", "valuelabel",
             "valuelabels", "nogr nogrid", "grid nogrid", "nogrid grid",
             "valuelabel novaluelabel", "labelminlen(3)"],
}


def _problem(text, table):
    return dr._dash_subopt_resolve(text, table)[1]


# ---------------------------------------------------------------------------
# Figures in both modes.  A generated app renders at import, so it is
# imported outside the warning capture; the capture covers make_document.
# ---------------------------------------------------------------------------
def _df():
    n = 6
    return pd.DataFrame({"mpg": np.linspace(12, 41, n),
                         "weight": np.linspace(1760, 4840, n),
                         "price": np.linspace(3000, 15000, n),
                         "foreign": np.array([0, 1, 0, 1, 0, 1], float),
                         "g": np.array(["a", "b", "a", "b", "a", "b"])})


def _spec(plots, go):
    g = dict({"title": '"t"'}, **go)
    g["name"] = "g1"
    return {"graphs": [{"plots": plots, "graph_options": g,
                        "if_expr": "", "in_expr": ""}],
            "kpis": [],
            "build_options": {"layout": "auto", "link": "", "filter": "",
                              "theme": "", "scheme": "", "session_scheme": "",
                              "title": "", "subtitle": "", "registry": "g1",
                              "tabs": "", "filter_position": "top",
                              "csv": "0", "level": "95",
                              "formats": {}, "limits": {}}}


def _sc(y="mpg", x="weight"):
    return {"type": "scatter", "yvar": y, "xvar": x, "options": {}}


def _lf(y="mpg", x="weight"):
    return {"type": "lfit", "yvar": y, "xvar": x, "options": {}}


def _figure(mode, tmp_path, go, plots=None, record=None):
    from bokeh.document import Document
    from bokeh.plotting import figure as _fig_cls
    plots = plots or [_sc(), _lf()]
    tag = next(_SEQ)
    sp = tmp_path / ("spec_%d.json" % tag)
    dp = tmp_path / ("data_%d.json" % tag)
    sp.write_text(json.dumps(_spec(plots, go)), encoding="utf-8")
    dp.write_text(json.dumps(make_data_json(_df())), encoding="utf-8")
    if mode == "served":
        ap = str(tmp_path / ("app_%d.py" % tag))
        dr.ServerAppBuilder(str(sp), str(dp)).build(ap)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mod = load_app(ap, "_soa_app_%d" % tag)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        if mode == "saved":
            figs = dr.DashRenderer(str(sp), str(dp))._build_figures()
            fig = figs[sorted(figs)[0]]
        else:
            doc = Document()
            mod.make_document(doc)
            fig = next(m for root in doc.roots for m in root.references()
                       if isinstance(m, _fig_cls))
    if record is not None:
        record.extend(str(w.message) for w in caught)
    return fig


def _plot_legend(fig):
    return [lg for lg in fig.legend if lg.items][0]


def _subopt_notes(msgs, option):
    return [m for m in msgs if ("%s() sub-option" % option) in m]


# ---------------------------------------------------------------------------
class TestTheTables:

    _TABLES = ("_DASH_LEGEND_SUBOPT_TABLE", "_DASH_AXLABEL_SUBOPT_TABLE",
               "_DASH_REFLINE_SUBOPT_TABLE", "_DASH_AXSCALE_SUBOPT_TABLE",
               "_DASH_TITLE_SUBOPT_TABLE", "_DASH_AXTITLE_SUBOPT_TABLE")

    def test_every_prefix_from_minimum_to_full(self):
        for tname in self._TABLES:
            table = getattr(dr, tname)
            first = {}
            for row in table:
                full, minimum = row[0], row[1]
                assert full.startswith(minimum), (tname, row)
                for n in range(len(minimum), len(full) + 1):
                    got = dr._dash_subopt_canon(full[:n], table)
                    # An earlier row may shadow a short spelling (c is
                    # cols in legend()); the full name is always its own.
                    first.setdefault(full[:n], got)
                    assert got is not None, (tname, full[:n])
                assert dr._dash_subopt_canon(full, table) is not None
                assert dr._dash_subopt_resolve(
                    [[full + ("(1)" if row[3] != "w" else "")]],
                    table)[0][0][0] is not None or row[5], (tname, row)

    def test_twoways_shadowing(self):
        L = dr._DASH_LEGEND_SUBOPT_TABLE
        A = dr._DASH_AXLABEL_SUBOPT_TABLE
        R = dr._DASH_REFLINE_SUBOPT_TABLE
        for nm, full in (("c", "cols"), ("la", "lalign"), ("s", "size"),
                         ("b", "box"), ("r", "rows"), ("t", "title"),
                         ("t1", "t1title")):
            assert dr._dash_subopt_canon(nm, L) == full, nm
        for nm, full in (("g", "grid"), ("nog", "nogrid"),
                         ("val", "valuelabels"), ("for", "format"),
                         ("tl", "tlength")):
            assert dr._dash_subopt_canon(nm, A) == full, nm
        for nm, full in (("st", "style"), ("la", "lalign")):
            assert dr._dash_subopt_canon(nm, R) == full, nm

    def test_refused_spellings_have_no_name(self):
        L = dr._DASH_LEGEND_SUBOPT_TABLE
        A = dr._DASH_AXLABEL_SUBOPT_TABLE
        for nm in ("po", "rin", "ord", "o", "lastl", "of", "OFF", "POS",
                   "Pos", "SIZE", "Cols", "garbage", ""):
            assert dr._dash_subopt_canon(nm, L) is None, nm
        for nm in ("lab", "LABS", "a", "an", "f", "fo", "gl", "nola", "no",
                   "va", "labelmin"):
            assert dr._dash_subopt_canon(nm, A) is None, nm

    def test_the_textbox_table_is_statas(self):
        for nm, full in (("s", "size"), ("a", "alignment"),
                         ("lst", "lstyle"), ("nob", "nobox"), ("b", "box"),
                         ("si", "size")):
            assert dr._textbox_canon(nm) == full, nm
        for nm in ("ls", "SIZE", "Size", "colour", "style"):
            assert dr._textbox_canon(nm) is None, nm


class TestTheResolver:

    def test_the_measured_refusals(self):
        for text, msg in _LEGEND_REFUSALS.items():
            p = _problem(text, dr._DASH_LEGEND_SUBOPT_TABLE)
            assert p is not None and p[2:] == (198, msg), (text, p)
        for text, msg in _AXIS_REFUSALS.items():
            p = _problem(text, dr._DASH_AXLABEL_SUBOPT_TABLE)
            assert p is not None and p[2:] == (198, msg), (text, p)
        for text in _ACCEPTED["legend"]:
            assert _problem(text, dr._DASH_LEGEND_SUBOPT_TABLE) is None, text
        for text in _ACCEPTED["axis"]:
            assert _problem(text, dr._DASH_AXLABEL_SUBOPT_TABLE) is None, \
                text

    def test_fall_through_and_repeats(self):
        L = dr._DASH_LEGEND_SUBOPT_TABLE
        res = dr._dash_subopt_resolve
        assert res("cols(1) c(red)", L)[0] == [["cols", "color"]]
        assert res("style(foreground) sty(foreground)", L)[0] == \
            [["style", "style"]]
        names, prob = res("c(1) c(2) c(3)", L)
        assert names == [["cols", "color", None]]
        assert prob == (0, 2, 198, "option c() not allowed")
        # Two copies: each takes its own a-options; a leftover in the
        # second copy is that copy's.
        names, prob = res([["c(2)"], ["cols(1)", "po(9)"]], L)
        assert names == [["cols"], ["cols", None]]
        assert prob == (1, 1, 198, "option po() not allowed")
        A = dr._DASH_AXLABEL_SUBOPT_TABLE
        assert res("nogr nogrid", A) == ([["nogrid", "nogrid"]], None)
        assert res(["grid", "nogrid"], A) == ([["grid", "nogrid"]], None)

    def test_linear_on_a_long_copy(self):
        rng = random.Random(30019)
        words = ["cols(1)", "lab(1 \"a\")", "on", "s(small)", "region(x)",
                 "c(red)", "title(x)"]
        toks = [rng.choice(words) for _ in range(20000)]
        t0 = time.perf_counter()
        dr._dash_subopt_resolve([toks], dr._DASH_LEGEND_SUBOPT_TABLE)
        assert time.perf_counter() - t0 < 2.0


@pytest.mark.parametrize("mode", _MODES)
class TestLegendAbbreviations:

    def test_each_spelling_draws_as_the_full_name(self, mode, tmp_path):
        msgs = []
        for spelling in ("c(1)", "co(1)", "col(1)"):
            lg = _plot_legend(_figure(mode, tmp_path, {"legend": spelling},
                                      record=msgs))
            assert lg.ncols == 1, spelling
        lg = _plot_legend(_figure(mode, tmp_path, {"legend": "r(1)"},
                                  record=msgs))
        assert lg.nrows == 1 and lg.ncols == "auto"
        lg = _plot_legend(_figure(mode, tmp_path,
                                  {"legend": 'lab(1 "XX")'}, record=msgs))
        assert lg.items[0].label["value"] == "XX"
        lg = _plot_legend(_figure(mode, tmp_path,
                                  {"legend": 'lastlab(1 "ZZ")'},
                                  record=msgs))
        assert lg.items[0].label["value"] == "ZZ"
        f_full = _figure(mode, tmp_path, {"legend": "position(9)"})
        f_abbr = _figure(mode, tmp_path, {"legend": "posi(9)"}, record=msgs)
        assert _plot_legend(f_abbr) in f_abbr.left
        assert len(f_full.left) == len(f_abbr.left)
        big = _plot_legend(_figure(mode, tmp_path, {"legend": "size(large)"}))
        for sp in ("s(large)", "si(large)"):
            lg = _plot_legend(_figure(mode, tmp_path, {"legend": sp},
                                      record=msgs))
            assert lg.label_text_font_size == big.label_text_font_size, sp
        assert not _subopt_notes(msgs, "legend"), msgs

    def test_la_is_lalign_and_named(self, mode, tmp_path):
        msgs = []
        lg = _plot_legend(_figure(mode, tmp_path, {"legend": 'la(1 "XX")'},
                                  record=msgs))
        assert lg.items[0].label["value"] != "XX"
        assert any('la(1 "XX")' in m for m in _subopt_notes(msgs, "legend"))


@pytest.mark.parametrize("mode", _MODES)
class TestLegendInOneCopy:

    def test_rows_beat_cols(self, mode, tmp_path):
        lg = _plot_legend(_figure(mode, tmp_path,
                                  {"legend": "cols(3) rows(1)"}))
        assert lg.nrows == 1 and lg.ncols == "auto"

    def test_on_beats_off(self, mode, tmp_path):
        for text in ("on off", "off on"):
            fig = _figure(mode, tmp_path, {"legend": text}, plots=[_sc()])
            assert any(lg.visible for lg in fig.legend), text

    def test_a_second_c_is_color(self, mode, tmp_path):
        msgs = []
        lg = _plot_legend(_figure(mode, tmp_path,
                                  {"legend": "cols(1) c(red)"}, record=msgs))
        assert lg.ncols == 1
        assert any("c(red)" in m for m in _subopt_notes(msgs, "legend"))

    def test_position_takes_twoways_names(self, mode, tmp_path):
        base = _figure(mode, tmp_path, {})
        for text in ("position(13)", "pos(06)", "pos(3.0)"):
            msgs = []
            fig = _figure(mode, tmp_path, {"legend": text}, record=msgs)
            for side in ("left", "right", "above", "below"):
                assert len(getattr(fig, side)) == \
                    len(getattr(base, side)), (text, side)
            assert not _subopt_notes(msgs, "legend"), (text, msgs)
        fig = _figure(mode, tmp_path, {"legend": "pos( 9 )"})
        assert _plot_legend(fig) in fig.left

    def test_a_non_integer_order_word_voids_order(self, mode, tmp_path):
        lg = _plot_legend(_figure(mode, tmp_path,
                                  {"legend": "order(2 x)"}))
        assert len(lg.items) == 2
        assert dr._dash_parse_legend_order("1 x") == []
        assert [k for k, _ in dr._dash_parse_legend_order("+1 2")] == [1, 2]
        assert [k for k, _ in dr._dash_parse_legend_order("-2 1")] == [1]

    def test_a_signed_key(self, mode, tmp_path):
        lg = _plot_legend(_figure(mode, tmp_path,
                                  {"legend": 'label(+1 "A")'}))
        assert lg.items[0].label["value"] == "A"

    def test_a_one_value_numlist(self, mode, tmp_path):
        lg = _plot_legend(_figure(mode, tmp_path, {"legend": "cols(2/2)"}))
        assert lg.ncols == 2


def _yaxis(fig):
    return [a for a in fig.yaxis
            if getattr(a, "y_range_name", "default") == "default"][0]


def _xaxis(fig):
    return [a for a in fig.xaxis
            if getattr(a, "x_range_name", "default") == "default"][0]


@pytest.mark.parametrize("mode", _MODES)
class TestAxisAbbreviations:

    def test_each_spelling_draws_as_the_full_name(self, mode, tmp_path):
        msgs = []

        def prof(spec):
            fig = _figure(mode, tmp_path, {"ylabel": spec}, record=msgs)
            ax = _yaxis(fig)
            return (ax.major_label_text_font_size,
                    ax.major_label_orientation,
                    type(ax.formatter).__name__,
                    getattr(ax.formatter, "format", None),
                    fig.ygrid[0].grid_line_color if fig.ygrid else None)
        pairs = [("labsize(large)", "labs(large)"),
                 ("angle(45)", "ang(45)"),
                 ("format(%9.1f)", "for(%9.1f)"),
                 ("format(%9.1f)", "form(%9.1f)"),
                 ("nogrid", "nog"), ("nogrid", "nogr"),
                 ("grid", "g"), ("grid", "gr")]
        for full, abbr in pairs:
            assert prof(", " + full) == prof(", " + abbr), (full, abbr)
        assert not _subopt_notes(msgs, "ylabel"), msgs
        for text in ("valuelabels", "val"):
            spec = dr._dash_parse_axis_spec("0 1, " + text)
            assert spec["valuelabel"] is True and not spec["unsupported"]

    def test_undrawn_spellings_are_named_as_typed(self, mode, tmp_path):
        msgs = []
        _figure(mode, tmp_path, {"ylabel": ", glc(red)"}, record=msgs)
        assert any("glc(red)" in m for m in _subopt_notes(msgs, "ylabel"))
        msgs = []
        _figure(mode, tmp_path, {"ytick": ", labs(large)"}, record=msgs)
        assert any("labs(large)" in m for m in _subopt_notes(msgs, "ytick"))

    def test_second_axis(self, mode, tmp_path):
        spec = dr._dash_parse_axis_spec(", labs(large)")
        assert spec["labsize"] == "large"
        assert spec["typed"] == {"labsize": "labs(large)"}


class TestZlabel:

    def test_zlabel_names_as_typed(self):
        spec = dr._dash_parse_axis_spec(", for(%9.1f) ang(45) nog")
        assert spec["typed"] == {"format": "for(%9.1f)",
                                 "angle": "ang(45)", "nogrid": "nog"}


@pytest.mark.parametrize("mode", _MODES)
class TestAxisInOneCopy:

    def test_grid_beats_nogrid(self, mode, tmp_path):
        for text in ("grid nogrid", "nogrid grid"):
            assert dr._dash_parse_axis_spec(", " + text)["grid"] is True
        a = _figure(mode, tmp_path, {"ylabel": ", grid nogrid"})
        b = _figure(mode, tmp_path, {"ylabel": ", grid"})
        assert [g.grid_line_color for g in a.ygrid] == \
            [g.grid_line_color for g in b.ygrid]

    def test_quoted_text_is_text(self, mode, tmp_path):
        spec = dr._dash_parse_axis_spec('10 "labsize(large)" 20')
        assert spec["labsize"] is None
        assert spec["labels"].get(10.0) == "labsize(large)" or \
            "labsize(large)" in str(spec["labels"])
        base = _yaxis(_figure(mode, tmp_path, {}))
        ax = _yaxis(_figure(mode, tmp_path,
                            {"ylabel": '10 "labsize(large)" 20'}))
        assert ax.major_label_text_font_size == \
            base.major_label_text_font_size

    def test_capitals_are_unread(self, mode, tmp_path):
        msgs = []
        base = _yaxis(_figure(mode, tmp_path, {}))
        ax = _yaxis(_figure(mode, tmp_path, {"ylabel": ", LABSIZE(large)"},
                            record=msgs))
        assert ax.major_label_text_font_size == \
            base.major_label_text_font_size
        assert any("LABSIZE(large)" in m
                   for m in _subopt_notes(msgs, "ylabel"))

    def test_the_note_names_the_typed_spelling(self, mode, tmp_path):
        msgs = []
        _figure(mode, tmp_path, {"ylabel": ", labs(bogus)"}, record=msgs)
        assert any("labs(bogus)" in m for m in msgs), msgs


def _span(fig):
    from bokeh.models import Span
    s = [m for m in fig.center if isinstance(m, Span)]
    return [(x.line_color, list(x.line_dash) if not isinstance(
        x.line_dash, str) else x.line_dash, x.line_width) for x in s]


@pytest.mark.parametrize("mode", _MODES)
class TestReflineAbbreviations:

    def test_each_spelling_draws_as_the_full_name(self, mode, tmp_path):
        msgs = []
        full = _span(_figure(mode, tmp_path, {
            "xline": "3000, lcolor(red) lpattern(dash) lwidth(thick)"}))
        for abbr in ("3000, lc(red) lp(dash) lw(thick)",
                     "3000, lcol(red) lpatte(dash) lwid(thick)"):
            assert _span(_figure(mode, tmp_path, {"xline": abbr},
                                 record=msgs)) == full, abbr
        assert not _subopt_notes(msgs, "xline"), msgs
        assert full and full[0][0] == "#ff0000" or full[0][0] == "red"

    def test_refused_spellings_are_named(self, mode, tmp_path):
        base = _span(_figure(mode, tmp_path, {"xline": "3000"}))
        for text in ("LCOLOR(red)", "l(red)", "c(red)", "color(red)",
                     "ls(x)"):
            msgs = []
            got = _span(_figure(mode, tmp_path, {"xline": "3000, " + text},
                                record=msgs))
            assert got == base, text
            assert any(text in m for m in _subopt_notes(msgs, "xline")), \
                (text, msgs)

    def test_the_note_names_the_typed_spelling(self, mode, tmp_path):
        msgs = []
        _figure(mode, tmp_path, {"xline": "3000, lc(bogus)"}, record=msgs)
        assert any("xline(lc(bogus))" in m for m in msgs), msgs


@pytest.mark.parametrize("mode", _MODES)
class TestTextboxShortSize:

    def test_s_is_size(self, mode, tmp_path):
        msgs = []
        full = _figure(mode, tmp_path, {"title": '"T", size(small)'})
        abbr = _figure(mode, tmp_path, {"title": '"T", s(small)'},
                       record=msgs)
        assert abbr.title.text_font_size == full.title.text_font_size
        assert not [m for m in msgs if "s(small)" in m], msgs
        msgs = []
        _figure(mode, tmp_path, {"title": '"T", SIZE(small)'}, record=msgs)
        assert any("SIZE(small)" in m for m in msgs), msgs


class TestTheMoveKeepsIt:

    def test_no_page_script_rewrites_these(self):
        import re
        src = open(os.path.join(_HERE, "..", "dash_render.py"),
                   encoding="utf-8").read()
        js = "\n".join(re.findall(r'(?s)_DASH_[A-Z_]*JS\s*=\s*(?:r?"""|\()'
                                  r'(.*?)(?:"""|\n\))', src))
        for attr in ("ncols", "nrows", "label_text_font_size",
                     "major_label_text_font_size",
                     "major_label_orientation", "grid_line_color"):
            assert re.search(r"\.%s\s*=" % attr, js) is None, attr

    _GO = {"legend": 'c(1) lab(1 "XX") posi(9) s(large)',
           "ylabel": ", labs(large) ang(45) nog",
           "xline": "3000, lc(red) lp(dash) lw(thick)"}

    @staticmethod
    def _look(models):
        """What the three families draw on every figure among *models*."""
        from bokeh.models import Span
        from bokeh.plotting import figure as _fig_cls
        out = []
        for f in models:
            if not isinstance(f, _fig_cls):
                continue
            lgs = [lg for lg in f.legend if lg.items]
            ys = [a for a in f.yaxis
                  if getattr(a, "y_range_name", "default") == "default"]
            out.append((
                # The first key's text (label(1) here); the saved page cues
                # a fit drawn on all rows with its own suffix after a move.
                [(lg.ncols, lg.nrows, lg.label_text_font_size,
                  [str(i.label) for i in lg.items[:1]],
                  lg in f.left) for lg in lgs],
                [(a.major_label_text_font_size, a.major_label_orientation)
                 for a in ys],
                [(g.grid_line_color is None) for g in f.ygrid],
                sorted((x.line_color, str(x.line_dash), x.line_width)
                       for x in f.center if isinstance(x, Span))))
        return sorted(out, key=str)

    def _spec(self):
        from test_mode_parity import _spec as mp_spec
        from test_server_layer_defects import plot_for
        return mp_spec([plot_for("scatter"), plot_for("lfit")],
                       {"filter": "foreign, type(dropdown)"}, dict(self._GO))

    def _check(self, before, after):
        assert before, "no figure drawn"
        lg = before[0][0][0]
        assert lg[0] == 1 and "XX" in lg[3][0] and lg[4], before
        assert before[0][3] and before[0][3][0][0] == "#ff0000", before
        assert after == before

    def test_saved_after_a_move(self):
        import test_saved_filter_layers as sfl
        r = sfl._render(self._spec())
        before = self._look(r._last_layout_root.references())
        sfl._move(r, ("Select", "Foreign"))
        self._check(before, self._look(r._last_layout_root.references()))

    def test_served_after_a_move(self):
        # _served imports the generated app outside its warning capture.
        from test_mode_parity import _fire, _served, _widgets_of
        from bokeh.models import Select
        doc, _ = _served(self._spec())

        def models():
            return [m for root in doc.roots for m in root.references()]
        before = self._look(models())
        w = [x for x in _widgets_of(doc) if isinstance(x, Select)][0]
        raw = [v for v, lab in w.options if lab == "Foreign"][0]
        _fire(w, raw)
        self._check(before, self._look(models()))

    def test_resolution_is_pure(self):
        # Every reading is build-time and a pure function of the option
        # text, so a filter move (which re-runs nothing here) cannot alter
        # it: two resolutions of the same text are equal.
        for text in _ACCEPTED["legend"]:
            a = dr._dash_legend_parts(text)
            b = dr._dash_legend_parts(text)
            assert a == b
        for text in _ACCEPTED["axis"]:
            assert dr._dash_parse_axis_spec(", " + text) == \
                dr._dash_parse_axis_spec(", " + text)


_FIXTURE = os.path.join(_HERE, "fixtures", "subopt_abbrev_truth.json")

#: Probe id -> (rc, first message or None): twoway's answers as Evidence
#: quotes them (plan section 10), held against the extracted fixture.
_FIXTURE_EXPECT = {
    "l_c_red": (121, "cols() invalid -- invalid number"),
    "l_po9": (198, "option po() not allowed"),
    "l_OFF": (198, "option OFF not allowed"),
    "l_c_dup": (198, "option cols() not allowed"),
    "l_rows_dup": (198, "option r() not allowed"),
    "l_cols0": (125, "cols() invalid -- invalid number, outside of allowed range"),
    "l_cols15": (126, "cols() invalid -- invalid number, noninteger value"),
    "l_cols12": (123, "cols() invalid -- single number required"),
    "l_colsdot": (127, "cols() invalid -- invalid number, missing not allowed"),
    "l_holes301": (123, "holes() invalid -- invalid numlist has too many elements"),
    "l_label_x": (198, "x not an integer in option label()"),
    "l_label_0": (198, "legend.labels[0] invalid name"),
    "l_garbage": (198, "option garbage not allowed"),
    "l_pos13": (0, "(note:  named style 13 not found in class clockdir, default attributes used)"),
    "l_order1x": (0, "x not an integer, option order() ignored"),
    "l_fall_c": (0, None), "l_cols22": (0, None), "l_label_plus": (0, None),
    "l_t_title": (0, None),
    "a_labs_word": (198, "option labs incorrectly specified"),
    "a_labs_labsword": (198, "option labs not allowed"),
    "a_a": (198, "option a() not allowed"),
    "a_grid_nogrid": (0, None), "a_dup_word": (0, None), "a_labs": (0, None),
    "o_x_y3": (198, "option a() not allowed"),
    "o_axis3_a": (198, "ylabels(, axis(3) a(45)) not allowed, yaxis3 does not exist"),
    "o_rows_cols": (121, "rows() invalid -- invalid number"),
    "x_l": (198, "option l() not allowed"),
    "x_abbr": (0, None),
    "t_s": (0, None),
    "t_SIZE": (198, "option SIZE() not allowed"),
    "t_ytitle_pfx_sfx": (198, "options prefix and suffix may not be combined"),
}


class TestTheFixture:

    @pytest.fixture(scope="class")
    def truth(self):
        with open(_FIXTURE, encoding="utf-8") as fh:
            return json.load(fh)

    def test_meta(self, truth):
        meta = truth["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted",
                  "scheme_in_force"):
            assert meta.get(k), k
        assert len(truth["probes"]) >= 150

    def test_every_probe_matches_the_measured_truth(self, truth):
        probes = truth["probes"]
        for pid, (rc, msg) in _FIXTURE_EXPECT.items():
            p = probes[pid]
            assert p["rc"] == rc, (pid, p)
            if msg is None:
                assert not [m for m in p["messages"]
                            if m.startswith("option")], (pid, p)
            else:
                assert p["messages"] and p["messages"][0] == msg, (pid, p)
        # Every one-legend() and one-ylabel() probe twoway refused with
        # "option ..." is refused by the resolver with the same words.
        import re
        for pid, p in probes.items():
            if pid[:2] in ("o_", "m_", "k_"):  # several options: order
                continue
            if p["rc"] != 198 or not p["messages"] \
                    or not p["messages"][0].startswith("option "):
                continue
            m = re.fullmatch(r".*?,\s*(legend|ylabel)\((.*)\)", p["cmd"])
            if not m or p["cmd"].count(m.group(1) + "(") != 1:
                continue
            if m.group(1) == "legend":
                body, table = m.group(2), dr._DASH_LEGEND_SUBOPT_TABLE
            else:
                body = dr._dash_axis_head_split(m.group(2))[1].lstrip(",")
                table = dr._DASH_AXLABEL_SUBOPT_TABLE
            prob = dr._dash_subopt_resolve(body.strip(), table)[1]
            assert prob is not None and prob[3] == p["messages"][0], \
                (pid, p["cmd"], prob)
