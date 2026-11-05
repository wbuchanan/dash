"""Markup on part of a text drawn as twoway draws it (WP-43 ST-14).

The defect (GAPS4 ST-14, S2): twoway draws ``title("a {bf:b} c")`` with
only the b bold, raises the q of ``a{sup:q}``, italicises only the p of
``{it:p}-value`` and styles each run of an explicit tick label, a legend
key or title, an added text and a by() title; dash gives a drawn text one
style, font and baseline and prints a note ("... is drawn in that text's
own style and font", "... is drawn on the line").

Measured truth: test/fixtures/smcl_runs_truth.json
(scripts/extract_smcl_runs_truth.do), each run's text, weight, slant,
font, size and baseline shift read from twoway's own SVG.

Known open.  Ruling D69 (04nov2026) withdrew the layout-time run placer
section 43-07 planned, and the 43-07-02 spike found no route D69 allows
that draws twoway's runs: Bokeh's TeX draws every run in MathJax's own
faces and adds 1.79 MB to each saved page; a Legend's title and keys are
DOM text that takes no TeX and no CSS on part of a text; Unicode
mathematical letters miss twoway's advances by up to an em.  The tests of
the drawn kinds are strict xfails until the maintainer rules; a kind that
starts drawing its runs turns its xfail into a failure, so the test is
flipped with the change that draws it.  The marker label's note and the
Unicode raised digits are pinned as they are.
"""
import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

import test_graph_text as tg  # noqa: E402
from bokeh.models import Title  # noqa: E402
from test_mode_parity import _sc, _spec  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "smcl_runs_truth.json")

with open(_FIXTURE, encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)

#: The note dash prints for a text it draws in one style.
_NOTE = "(help dash, Text in graphs)"

_OPEN = pytest.mark.xfail(
    strict=True,
    reason="ST-14 open: no drawing route ruling D69 allows draws twoway's "
           "runs (spike 43-07-02); the maintainer rules")


def _at(y, x, line):
    """One added-text record as dash.ado's _dash_at_json writes it."""
    return {"added_text": [{"at_kind": "text", "at_y": y, "at_x": x,
                            "at_yaxis": 1, "at_xaxis": 1,
                            "at_lines": [line], "at_opts": ""}],
            "added_text_n": "1"}


#: dash's spelling of each fixture probe, by kind of text: (plots, graph
#: options).  graph_text.sthlp's examples are drawn on a scatter.
_KINDS = {
    "titles": {
        "title.bold": ([_sc()], {"title": '"a {bf:b} c"'}),
        "title.italic": ([_sc()], {"title": '"{it:p}-value"'}),
        "title.supsub": ([_sc()], {"title": '"a{sup:q} b{sub:k}"'}),
        "note.mixed": ([_sc()],
                       {"note": '"{bf:Source}: {it:Consumer Reports}"'}),
        "t1title.italic": ([_sc()], {"t1title": '"x {it:y}"'}),
        "r1title.italic": ([_sc()], {"r1title": '"x {it:y}"'}),
        "title.vertical": ([_sc()],
                           {"title": '"{it:p} q", orientation(vertical)'}),
        "title.scale15": ([_sc()], {"title": '"a {bf:b} c"',
                                    "scale": "1.5"}),
        "help.italics": ([_sc()], {
            "title": '"This is {it:italics} in a graph title"'}),
        "help.caption": ([_sc()], {
            "caption": '"{bf:Source}: {it:Consumer Reports}, used with '
                       'permission"'}),
        "help.funcsup1": ([_sc()],
                          {"title": '"{&function}(x)=2e{superscript:-2x}"'}),
        "help.fonts": ([_sc()], {
            "title": '"Here are {stSerif:serif}, {stSans:sans serif}, and '
                     '{stMono:monospace}"'}),
    },
    "axis titles": {
        "xtitle.font": ([_sc()], {"xtitle": '"{stSerif:serif} sans"'}),
    },
    "tick labels": {
        "xlabel.runs": ([_sc()], {
            "xlabel": '3000 "{it:italic} text" 4000 "{bf:bold}" '
                      '5000 "a{sup:q}"'}),
    },
    "legend": {
        "legend.runs": ([_sc(), _sc(y="turn")], {
            "legend": 'label(1 "{it:Mileage} (mpg)") title("{bf:T} t")'}),
    },
    "added text": {
        "text.bold": ([_sc()], _at(30, 3000, "a {bf:b}")),
    },
    "by titles": {
        "by.title": ([_sc()], {"by": 'foreign, title("{it:t} u")'}),
    },
}


def _notes(mode, plots, go, ml=None):
    df = tg._df(ml=ml)
    _, w = tg._models(mode, _spec(plots, graph_options=go), tg._data(df))
    return [str(x) for x in w if _NOTE in str(x)]


def _styles(key):
    """The distinct (weight, slant, font, size, shift) of the runs of the
    probe's texts in twoway's SVG."""
    out = set()
    for t in TRUTH[key]["texts"]:
        for r in t["runs"]:
            out.add((r["b"], r["i"], r["f"], r["s"], r["v"]))
    return out


class TestTheFixture:

    def test_meta_and_marker_label(self):
        """_meta is complete; mlabel_part's marker label holds a regular
        "a " and a bold "b" (the difference a marker label keeps)."""
        meta = TRUTH["_meta"]
        assert set(meta) == {"stata_version", "born_date", "dash_commit",
                             "extracted", "source"}
        assert meta["source"] == "scripts/extract_smcl_runs_truth.do"
        (t,) = TRUTH["mlabel_part"]["texts"]
        assert [(r["t"], r["b"]) for r in t["runs"]] == [("a ", False),
                                                        ("b", True)]

    def test_raised_ratios(self):
        """twoway draws {sup:} and {sub:} at 0.583 of the text's size,
        0.524 of it above the baseline and 0.143 below."""
        r = TRUTH["ratios"]
        assert r["sup_scale"] == r["sub_scale"] == pytest.approx(0.583,
                                                                 abs=1e-3)
        assert r["sup_shift"] == pytest.approx(0.5238, abs=1e-3)
        assert r["sub_shift"] == pytest.approx(-0.1428, abs=1e-3)


@pytest.mark.parametrize("mode", tg.MODES)
class TestRunsDrawn:

    @_OPEN
    @pytest.mark.parametrize("kind", sorted(_KINDS))
    def test_no_note(self, mode, kind):
        """Every probe of the kind, whose runs twoway styles apart, is
        drawn by dash with no one-style note."""
        for key, (plots, go) in _KINDS[kind].items():
            assert TRUTH[key]["rc"] == 0
            assert len(_styles(key)) > 1, key
            assert _notes(mode, plots, go) == [], key

    def test_unicode_raised_stays(self, mode):
        """A raised run whose characters all have a Unicode form is drawn
        with them and no note, as now: ytitle("m{sup:2}") reads m and a
        raised 2 in twoway's SVG and m² in dash."""
        assert [r["t"] for r in TRUTH["ytitle.unicode"]["texts"][0]["runs"]
                ] == ["m", "2"]
        assert _notes(mode, [_sc()], {"ytitle": '"m{sup:2}"'}) == []
        models, _ = tg._models(
            mode, _spec([_sc()], graph_options={"title": '"m{sup:2}"'}),
            tg._data(tg._df()))
        assert "m²" in [m.text for m in tg._of(models, Title)]

    def test_marker_label_note(self, mode):
        """A marker label holding "a {bf:b}" is drawn in one style with one
        note naming the marker label (twoway: mlabel_part)."""
        notes = _notes(mode, [_sc(mlabel="ml")], {},
                       ml=["a {bf:b}"] * len(tg._DF))
        assert len(notes) == 1
        assert "part of a marker label is drawn in that text's own style" \
            in notes[0]
