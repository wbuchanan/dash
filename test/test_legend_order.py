"""test_legend_order.py -- legend(order()), label(), lastlabel() and `-'
rows are read as twoway reads them (GAPS2 B5, WP-28 section 15).

GAPS2 B5 measured four symptoms, in both render modes with rc 0 and no
warning:

1. ``order(1 "Group 2" 3 "Three")`` drew the keys ``mpg`` / ``Fitted
   values`` / ``price``: order() was read as ``re.findall(r"\\d+")`` over
   displayed positions and its texts were ignored.
2. ``order(2 1) label(1 "Data")`` relabelled the fit: label() was applied
   by displayed position after the reorder, not by plot number.
3. ``order(1 - "Note" 2)`` dropped the text-only line.
4. ``lastlabel()`` was only named as a sub-option dash does not implement.

Ground truth is ``test/fixtures/text_truth.json`` group ``legend``,
measured by ``scripts/extract_text_truth.do`` from twoway's SVG export
against a ``legend(off)`` companion; ``keys_in_drawn_order`` is the
legend's texts top to bottom, then left to right.
"""
import html as _htmllib
import itertools
import json
import os
import re
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
from conftest import make_data_json, make_spec, load_app  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "text_truth.json")
_SEQ = itertools.count()
_N = 30
_DF = pd.DataFrame({
    "mpg": np.linspace(12.0, 41.0, _N),
    "weight": np.linspace(1760.0, 4840.0, _N),
    "price": np.linspace(3291.0, 15906.0, _N) + np.sin(np.arange(_N)) * 50,
})
#: auto.dta's variable labels, which twoway draws as the default keys.
_VLAB = {"mpg": "Mileage (mpg)", "weight": "Weight (lbs.)",
         "price": "Price"}


def _p(t, y="mpg"):
    return {"type": t, "yvar": y, "xvar": "weight", "options": {}}


P2 = [_p("scatter"), _p("lfit")]
P3 = [_p("scatter"), _p("lfit"), _p("qfit")]
PC = [_p("scatter"), _p("lfitci"), _p("scatter", "price")]
P1 = [_p("scatter")]


@pytest.fixture(scope="module")
def truth():
    if not os.path.exists(_FIXTURE):
        pytest.fail("section 15 task 15-05 must land first: "
                    "test/fixtures/text_truth.json has no legend group")
    with open(_FIXTURE, encoding="utf-8") as fh:
        doc = json.load(fh)
    if not any(p.get("group") == "legend" for p in doc["probes"].values()):
        pytest.fail("section 15 task 15-05 must land first: "
                    "test/fixtures/text_truth.json has no legend group")
    return doc


def _write(wd, plots, legend):
    tag = next(_SEQ)
    spec = make_spec([dict(p) for p in plots])
    if legend:
        spec["graphs"][0]["graph_options"]["legend"] = legend
    data = make_data_json(_DF)
    data["StataJSON"]["variableLabels"] = dict(_VLAB)
    sp = os.path.join(str(wd), "spec_%d.json" % tag)
    dp = os.path.join(str(wd), "data_%d.json" % tag)
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    with open(dp, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    return tag, sp, dp


def _series_legend(fig):
    from bokeh.models import Legend
    lgs = [m for m in fig.select({"type": Legend})
           if str(getattr(m, "name", "") or "") != dr._COLORVAR_LEGEND_NAME]
    assert len(lgs) == 1, lgs
    return lgs[0]


def _build(mode, plots, legend, wd):
    """``(fig, warnings, page)``: the one figure *mode* draws, the
    warnings raised building it and, saved, the page."""
    from bokeh.document import Document
    from bokeh.models import Plot
    tag, sp, dp = _write(wd, plots, legend)
    if mode == "saved":
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            r = dr.DashRenderer(sp, dp)
            page = r.render()
        figs = list(r.figures.values())
        assert len(figs) == 1
        return figs[0], [str(w.message) for w in caught], page
    ap = os.path.join(str(wd), "app_%d.py" % tag)
    with warnings.catch_warnings(record=True) as built:
        warnings.simplefilter("always")
        dr.ServerAppBuilder(sp, dp).build(ap)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mod = load_app(ap, "_lo_app_%d" % tag, draw=False)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        doc = Document()
        mod.make_document(doc)
    figs = list(doc.select({"type": Plot}))
    assert len(figs) == 1
    return figs[0], [str(w.message) for w in list(built) + list(caught)], \
        None


def _legend(mode, plots, legend, wd):
    """``(fig, Legend)`` for one graph in *mode*."""
    fig, _, _ = _build(mode, plots, legend, wd)
    return fig, _series_legend(fig)


def _text(label):
    if isinstance(label, dict):
        return label.get("value")
    return getattr(label, "value", label)


def _rows(lg):
    return [_text(it.label) for it in lg.items]


def _drawn(lg):
    """What the viewer reads: every row's lines, none when hidden."""
    if not lg.visible:
        return []
    return [ln for it in lg.items for ln in str(_text(it.label)).split("\n")]


def _page_rows(page):
    """The series legend's rows of the saved page's embedded document, in
    ``Legend.items`` order."""
    from bokeh.document import Document
    from bokeh.models import Legend
    blocks = re.findall(r'<script type="application/json" id="[^"]+">'
                        r'\s*(.*?)\s*</script>', page, re.S)
    docs = [d for b in blocks
            for d in json.loads(_htmllib.unescape(b)).values()]
    assert len(docs) == 1
    lgs = [m for m in Document.from_json(docs[0]).select({"type": Legend})
           if str(m.name or "") != dr._COLORVAR_LEGEND_NAME]
    assert len(lgs) == 1
    return [_text(it.label) for it in lgs[0].items]


def _glyph(r):
    return type(getattr(r, "glyph", None)).__name__


def _scatters(fig):
    return [r for r in fig.renderers if _glyph(r) == "Scatter"]


MODES = ["saved", "served"]


# ---------------------------------------------------------------------------
# order() text and selection
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", MODES)
class TestOrderText:
    def test_text_after_a_number_retitles_that_key(self, mode, wd, truth):
        fig, lg = _legend(mode, P3, 'order(1 "Group 2" 3 "Three")', wd)
        want = truth["probes"]["l_order_text"]["keys_in_drawn_order"]
        assert want == ["Group 2", "Three"]
        assert _rows(lg) == want
        assert lg.items[0].renderers == _scatters(fig)
        assert [_glyph(r) for r in lg.items[1].renderers] == ["Line"]
        assert lg.visible

    def test_repeats_share_one_item(self, mode, wd, truth):
        _, lg = _legend(mode, P2, "order(1 2 1)", wd)
        assert _drawn(lg) == \
            truth["probes"]["l_order_repeat"]["keys_in_drawn_order"]
        assert len(lg.items) == 3
        assert len({id(it) for it in lg.items}) == 2
        assert lg.items[0] is lg.items[2]


# ---------------------------------------------------------------------------
# label() by plot number
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", MODES)
class TestLabelByNumber:
    def test_label_names_the_plot_not_the_position(self, mode, wd, truth):
        fig, lg = _legend(mode, P2, 'order(2 1) label(1 "Data")', wd)
        assert _rows(lg) == \
            truth["probes"]["l_order_label"]["keys_in_drawn_order"]
        assert _rows(lg) == ["Fitted values", "Data"]
        assert lg.items[1].renderers == _scatters(fig)

    def test_sub_option_order_does_not_matter(self, mode, wd, truth):
        fig, lg = _legend(mode, P2, 'label(1 "Data") order(2 1)', wd)
        assert _rows(lg) == \
            truth["probes"]["l_label_order"]["keys_in_drawn_order"]
        assert lg.items[1].renderers == _scatters(fig)

    def test_order_text_beats_label(self, mode, wd, truth):
        _, lg = _legend(mode, P2, 'order(1 "O") label(1 "L")', wd)
        assert _drawn(lg) == \
            truth["probes"]["l_order_beats_label"]["keys_in_drawn_order"]
        assert _drawn(lg) == ["O"]

    def test_a_label_for_no_key_is_ignored(self, mode, wd):
        control = _rows(_legend(mode, P2, "", wd)[1])
        for opt in ('label(9 "x")', 'label(0 "z")'):
            fig, msgs, _ = _build(mode, P2, opt, wd)
            lg = _series_legend(fig)
            assert _rows(lg) == control, opt
            assert not [m for m in msgs if "legend" in m], msgs
        _, lg = _legend(mode, P2, "order(0 1)", wd)
        assert _rows(lg) == ["Mileage (mpg)"]


# ---------------------------------------------------------------------------
# `-' rows
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", MODES)
class TestTextOnlyRows:
    def test_a_dash_inserts_a_text_row(self, mode, wd, truth):
        _, lg = _legend(mode, P2, 'order(1 - "Note" 2)', wd)
        assert _drawn(lg) == \
            truth["probes"]["l_dash_text"]["keys_in_drawn_order"]
        assert len(lg.items) == 3
        assert list(lg.items[1].renderers) == []
        assert _text(lg.items[1].label) == "Note"
        _, lg = _legend(mode, P2, 'order(1 - " " "Note" 2)', wd)
        assert _text(lg.items[1].label) == " \nNote"
        assert _drawn(lg) == \
            truth["probes"]["l_dash_blank"]["keys_in_drawn_order"]
        _, lg = _legend(mode, P2, 'order(1 - "" 2)', wd)
        assert len(lg.items) == 2
        assert _drawn(lg) == \
            truth["probes"]["l_dash_empty"]["keys_in_drawn_order"]
        _, lg = _legend(mode, P2, 'order(1 - "Line 1" "Line 2" 2)', wd)
        assert _drawn(lg) == \
            truth["probes"]["l_dash_two_lines"]["keys_in_drawn_order"]

    def test_one_key_and_a_text_row(self, mode, wd, truth):
        _, lg = _legend(mode, P1, 'order(1 - "Only")', wd)
        assert _drawn(lg) == \
            truth["probes"]["l_one_dash"]["keys_in_drawn_order"]


# ---------------------------------------------------------------------------
# lastlabel()
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", MODES)
class TestLastLabel:
    def test_lastlabel_wins_over_order_and_label(self, mode, wd, truth):
        _, lg = _legend(mode, P2,
                        'order(2 "Y" 1) label(2 "X") lastlabel(2 "L")', wd)
        assert _drawn(lg) == \
            truth["probes"]["l_lastlabel_all"]["keys_in_drawn_order"]
        _, lg = _legend(mode, P2, 'order(2 1) lastlabel(2 "L")', wd)
        assert _drawn(lg) == \
            truth["probes"]["l_lastlabel_pos"]["keys_in_drawn_order"]
        _, lg = _legend(mode, P2, 'order(1 - "Note" 2) lastlabel(3 "L")',
                        wd)
        assert _drawn(lg) == \
            truth["probes"]["l_lastlabel_dash"]["keys_in_drawn_order"]

    def test_lastlabel_is_quiet(self, mode, wd):
        _, msgs, _ = _build(mode, P2, 'order(2 1) lastlabel(2 "L")', wd)
        assert not [m for m in msgs if "sub-option" in m], msgs

    def test_two_lastlabels(self, mode, wd, truth):
        _, lg = _legend(mode, P2, 'lastlabel(1 "A") lastlabel(2 "B")', wd)
        assert _drawn(lg) == \
            truth["probes"]["l_lastlabel_two"]["keys_in_drawn_order"]
        # A lastlabel() on a repeated key renames that row only.
        _, lg = _legend(mode, P2, 'order(1 2 1) lastlabel(3 "Z")', wd)
        assert _rows(lg) == ["Mileage (mpg)", "Fitted values", "Z"]
        assert lg.items[0].renderers == lg.items[2].renderers


# ---------------------------------------------------------------------------
# Key numbers: a ci layer is two keys
# ---------------------------------------------------------------------------

class TestKeysAreNumberedByPlot:
    @pytest.mark.parametrize("mode", MODES)
    def test_a_ci_layer_is_two_keys(self, mode, wd, truth):
        fig, lg = _legend(mode, PC, "order(4 1)", wd)
        assert _rows(lg) == \
            truth["probes"]["l_ci_order_last"]["keys_in_drawn_order"]
        sc = _scatters(fig)
        assert lg.items[0].renderers == [sc[-1]]
        assert lg.items[1].renderers == [sc[0]]
        fig, lg = _legend(mode, PC, "order(2 3)", wd)
        assert _rows(lg) == \
            truth["probes"]["l_ci_order_band"]["keys_in_drawn_order"]
        assert _glyph(lg.items[0].renderers[0]) in ("VArea", "Band", "Patch")
        _, lg = _legend(mode, PC, "", wd)
        assert _rows(lg) == \
            truth["probes"]["l_ci_default"]["keys_in_drawn_order"]

    def test_numbers_unit(self):
        from bokeh.models import (ColumnDataSource, GlyphRenderer, Line,
                                  Scatter, VArea)
        src = ColumnDataSource({"x": [1, 2], "y": [1, 2], "y2": [2, 3]})

        def gr(g):
            return GlyphRenderer(glyph=g, data_source=src)
        s1, band, line, s2 = (gr(Scatter(x="x", y="y")),
                              gr(VArea(x="x", y1="y", y2="y2")),
                              gr(Line(x="x", y="y")),
                              gr(Scatter(x="x", y="y")))
        pr = [(_p("scatter"), [s1]), (_p("lfitci"), [band, line]),
              (_p("scatter", "price"), [s2])]
        got = dr._dash_legend_keys(pr, {}, 95)
        assert [(n, t) for n, t, _ in got] == [
            (1, "mpg"), (2, "95% CI"), (3, "Fitted values"), (4, "price")]
        assert [r for _, _, r in got] == [[s1], [band], [line], [s2]]
        # A layer that drew nothing consumes its number all the same.
        pr2 = [(_p("scatter"), [s1]), (_p("line"), []),
               (_p("scatter", "price"), [s2])]
        got = dr._dash_legend_keys(pr2, _VLAB, 95)
        assert [(n, t) for n, t, _ in got] == [
            (1, "Mileage (mpg)"), (3, "Price")]
        # The pair projection is unchanged.
        assert dr._dash_legend_entries(pr, {}, 95) == [
            (t, r) for _, t, r in dr._dash_legend_keys(pr, {}, 95)]


# ---------------------------------------------------------------------------
# The parser
# ---------------------------------------------------------------------------

_CQ_OPEN, _CQ_CLOSE = "`" + '"', '"' + "'"


class TestTheParser:
    @pytest.mark.parametrize("arg,want", [
        ('1 "Group 2" 3 "Three"', [(1, ["Group 2"]), (3, ["Three"])]),
        ('1 - "Note" 2', [(1, []), ("-", ["Note"]), (2, [])]),
        ('1 - " " "Note" 2', [(1, []), ("-", [" ", "Note"]), (2, [])]),
        ('1 - "" 2', [(1, []), ("-", []), (2, [])]),
        ('0 "z"', [(0, ["z"])]),
        ("1 " + _CQ_OPEN + 'a "b" c' + _CQ_CLOSE, [(1, ['a "b" c'])]),
        ('2 "a" "b"', [(2, ["a", "b"])]),
        ('1 "a" "" "b" 2', [(1, ["a"]), (2, [])]),
        ('1234567 "x" 2', [(2, [])]),
        ('1 "Group 2" - "Note" 3 "" 2',
         [(1, ["Group 2"]), ("-", ["Note"]), (3, []), (2, [])]),
        ("", []),
        ("2 1", [(2, []), (1, [])]),
    ])
    def test_cases(self, arg, want):
        assert dr._dash_parse_legend_order(arg) == want

    def test_a_hundred_thousand_tokens_parse_in_under_a_second(self):
        arg = " ".join(["1", '"x"', "-", '"y"'] * 25000)
        # CPU time, not wall time (WP-31 S60): the parser is single-threaded
        # pure Python, so the claim is about its own work; wall time also
        # counted the time other xdist workers held the CPU, and failed
        # under -n 8 while the parse itself took the same CPU.
        t0 = time.process_time()
        out = dr._dash_parse_legend_order(arg)
        assert time.process_time() - t0 < 1.0
        assert len(out) == 50000


# ---------------------------------------------------------------------------
# Every measured probe, and the two modes against each other
# ---------------------------------------------------------------------------

_PROBES = [
    ("l_two", P2, ""),
    ("l_order_text", P3, 'order(1 "Group 2" 3 "Three")'),
    ("l_order_label", P2, 'order(2 1) label(1 "Data")'),
    ("l_label_order", P2, 'label(1 "Data") order(2 1)'),
    ("l_order_beats_label", P2, 'order(1 "O") label(1 "L")'),
    ("l_dash_text", P2, 'order(1 - "Note" 2)'),
    ("l_dash_blank", P2, 'order(1 - " " "Note" 2)'),
    ("l_dash_empty", P2, 'order(1 - "" 2)'),
    ("l_dash_two_lines", P2, 'order(1 - "Line 1" "Line 2" 2)'),
    ("l_lastlabel_pos", P2, 'order(2 1) lastlabel(2 "L")'),
    ("l_lastlabel_all", P2, 'order(2 "Y" 1) label(2 "X") lastlabel(2 "L")'),
    ("l_lastlabel_dash", P2, 'order(1 - "Note" 2) lastlabel(3 "L")'),
    ("l_lastlabel_two", P2, 'lastlabel(1 "A") lastlabel(2 "B")'),
    ("l_label_two_lines", P2, 'label(1 "A" "B")'),
    ("l_order_repeat", P2, "order(1 2 1)"),
    ("l_ci_default", PC, ""),
    ("l_ci_order_last", PC, "order(4 1)"),
    ("l_ci_order_band", PC, "order(2 3)"),
    ("l_one_dash", P1, 'order(1 - "Only")'),
]


class TestBothModes:
    @pytest.mark.parametrize("pid,plots,legend", _PROBES,
                             ids=[p[0] for p in _PROBES])
    def test_the_page_and_the_app_agree(self, pid, plots, legend, wd,
                                        truth):
        sfig, _, page = _build("saved", plots, legend, wd)
        vfig, _, _ = _build("served", plots, legend, wd)
        slg, vlg = _series_legend(sfig), _series_legend(vfig)
        assert _rows(slg) == _rows(vlg) == _page_rows(page)
        assert slg.visible == vlg.visible
        want = truth["probes"][pid]["keys_in_drawn_order"]
        got = _drawn(slg)
        if pid == "l_label_two_lines":
            # Two lines beside one: the heights interleave in the SVG.
            got, want = sorted(got), sorted(want)
        assert got == want, (pid, got, want)


class TestTheServedCopy:
    def test_the_names_are_copied(self, wd):
        tag, sp, dp = _write(wd, P2, "")
        ap = os.path.join(str(wd), "app_%d.py" % tag)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.ServerAppBuilder(sp, dp).build(ap)
        with open(ap, encoding="utf-8") as fh:
            src = fh.read()
        for name in ("_dash_parse_legend_order", "_dash_legend_keys"):
            assert "def %s(" % name in src, name


class TestTheFixture:
    def test_meta_carries_the_four_provenance_keys(self):
        with open(_FIXTURE, encoding="utf-8") as fh:
            meta = json.load(fh)["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted"):
            assert k in meta, k


@pytest.fixture
def wd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path
