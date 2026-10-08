"""Per-series value lists: mlabel(), jitter(), base() and barwidth() across
an expanded varlist (WP-30 P1.1b).

The defect, measured at c96facd (probe d1.do): ``dash scatter mpg turn
weight, mlabel(make rep78)`` was refused r(198), ``dash: mlabel() must name
one variable (got: make rep78)``; ``jitter(2 3)`` was refused ``dash:
jitter() must be a number between 0 and 100 (got: 2 3)``; and ``bar mpg
turn weight, base(10 20)`` was refused ``dash: base() must be a number
(got: 10 20)``.

twoway (StataNow 19.5, s2color) reads each as a stylelist, one element per
y: M01 labels series 1 with make and series 2 with rep78, and G01
(``bar y1 y2 x, barwidth(0.4 0.8) base(10 20)``) draws widths 0.4 and 0.8
from bases 10 and 20.  test/fixtures/value_list_truth.json records those
readings (scripts/extract_value_list_truth.do).

The Stata half (the spec dash.ado writes per series, the refusals in
twoway's words) is test_varlist_expansion.cscript's PS run and the S20
block of test_wp30_truth.cscript; this module checks the fixture, the
code's structure, and that both renderers draw each series' own value,
before and after a served filter move.
"""
import json
import os
import re
import sys

import pytest
from bokeh.models import GlyphRenderer

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import test_mode_parity as mp  # noqa: E402
from test_abbreviations import _program_body  # noqa: E402
from test_marker_label_parity import _field, _labelsets  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_ADO = os.path.join(_HERE, "..", "dash.ado")
_MATA = os.path.join(_HERE, "..", "dash_parse.mata")
_HLP = os.path.join(_HERE, "..", "dash.sthlp")
_FIX = os.path.join(_HERE, "fixtures", "value_list_truth.json")

_VALUE_KEYS = ("mlabel", "jitter", "base", "barwidth")

# case id -> the per-series plot dicts dash.ado now writes (the PS run of
# test_varlist_expansion.cscript asserts the same objects from Stata).
_SERIES = {
    "LAB": [plot_for("scatter", {"mlabel": "rep"}, yvar="mpg"),
            plot_for("scatter", {"mlabel": "foreign"}, yvar="price")],
    "BAR": [plot_for("bar", {"base": "10", "barwidth": "0.4"}, yvar="mpg",
                     xvar="rep"),
            plot_for("bar", {"base": "20", "barwidth": "0.8"}, yvar="price",
                     xvar="rep")],
    "JIT": [plot_for("scatter", {"jitterseed": "1"}, yvar="mpg"),
            plot_for("scatter", {"jitter": "5", "jitterseed": "1"},
                     yvar="price")],
}

# The fixture's measured reading of every case: rc, then the first error
# line where twoway refused it.
_RC = dict(
    {k: 0 for k in ("M01 M02 M03 M04 M05 M06 M07 M08 M09 M10 M11 M27 M29 "
                    "M35 V01 V02 V03 V04 V06 V07 V08 V09 V10 B01 B02 B03 "
                    "B05 B06 B07 B08 B09 B10 B11 B12 B13 G01 G02 G03 G04 "
                    "J01 J02 J03").split()},
    M30=103, M33=101, M34=111, B23=4026, B24=199)
_REFUSED = {
    ".. not allowed in option mlabel()": (198, "M12 M14 M25 M28 M31"),
    "... not allowed in option mlabel()": (198, "M13"),
    "=exp not allowed": (101, "M15 M16 M24"),
    "too few variables specified": (102, "M17 M18"),
    "variable nosuch not found": (111, "M19 M20 M21 M22 M23 M32"),
    "invalid syntax": (198, "M26"),
    "jitter(2 .. 5):  invalid syntax": (198, "V05"),
    "base(10 .. 20):  invalid syntax": (198, "B04"),
    "option barwidth() not allowed": (198, "B14 B15 B16 B17 B18 B19"),
    "option base() not allowed": (198, "B20 B21"),
    "option bwidth() not allowed": (198, "B22"),
}
_P1, _P2 = "#1a476f", "#90353b"


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _fixture():
    with open(_FIX, encoding="utf-8") as fh:
        return json.load(fh)


class TestTheFixture:
    def test_meta_is_stamped(self):
        meta = _fixture()["_meta"]
        assert sorted(meta) == ["born_date", "dash_commit", "extracted",
                                "stata_version"]
        assert meta["stata_version"].startswith("19.")

    def test_every_case_reads_as_measured(self):
        cases = _fixture()["cases"]
        want = dict(_RC)
        for msg, (rc, ids) in _REFUSED.items():
            for i in ids.split():
                want[i] = (rc, msg)
        bad = []
        assert set(cases) == set(want), sorted(set(cases) ^ set(want))
        for cid, w in sorted(want.items()):
            rc, msg = w if isinstance(w, tuple) else (w, None)
            got = cases[cid]
            if got["rc"] != rc or (msg and got["message"] != msg):
                bad.append((cid, got["rc"], got["message"]))

        def groups(cid):
            return [(f, n, t[0]) for f, n, t in cases[cid]["labels"]]
        for cid, exp in {
                "M01": [(_P1, 74, "AMC Concord"), (_P2, 74, "3")],
                "M03": [(_P2, 74, "3")],
                "M05": [(_P1, 74, "AMC Concord")],
                "M11": [(_P1, 74, "3"), (_P2, 74, "Domestic")],
                "M10": []}.items():
            if groups(cid) != exp:
                bad.append((cid, groups(cid)))
        bars = {cid: {f: sorted({(w, lo) for w, lo, _hi in v})
                      for f, v in cases[cid]["bars"].items()}
                for cid in ("G01", "G02")}
        if bars["G01"] != {"#486c8c": [(0.4, 10.0)], "#a65d62": [(0.8, 20.0)]}:
            bad.append(("G01", bars["G01"]))
        if bars["G02"] != {"#486c8c": [(0.4, 10.0)], "#a65d62": [(0.4, 10.0)]}:
            bad.append(("G02", bars["G02"]))
        for cid, exp in {"J01": (31, 7), "J02": (7, 30),
                         "J03": (31, 30)}.items():
            j = cases[cid]["jitter"]
            if (j[_P1], j[_P2]) != exp:
                bad.append((cid, j))
        assert not bad, bad


class TestTheParserReadsValueLists:
    def test_the_four_are_declared_asis(self):
        body = _program_body(_read(_ADO), "_dash_parse_plot_opts")
        syn = body[body.index("syntax [,"):body.index("\n    ]\n")]
        decl = {m.group(1).lower(): m.group(2) for m in re.finditer(
            r"\b([A-Za-z0-9]+)\((string(?: asis)?)\)", syn)}
        for k in _VALUE_KEYS:
            assert decl[k] == "string asis", k

    def test_the_rules_name_the_value_lists_and_the_one_value_types(self):
        body = _program_body(_read(_ADO), "_dash_option_rules")
        assert 'local values "mlabel jitter base barwidth"' in body
        assert ('local onevalue "barwidth@rbar|histogram|rcap|rspike  '
                'base@rbar|histogram"') in body
        assert 'c_local _dash_rules_values "`values\'"' in body
        assert 'c_local _dash_rules_onevalue "`onevalue\'"' in body

    def test_validate_opts_takes_the_series_and_routes_the_lists(self):
        body = _program_body(_read(_ADO), "_dash_validate_opts")
        assert "args ptype nser" in body
        branch = body[body.index("if `: list o in _dash_rules_values' {"):]
        assert branch.index("_dash_value_list ") < branch.index(
            "_dash_validate_value ")
        chg = body[body.index("if `_chg' {"):]
        chg = chg[:chg.index("\n        }\n")]
        assert "local _snap_`o' : copy local _dash_vnorm" in chg
        seg = _program_body(_read(_ADO), "_dash_process_segment")
        # WP-30 P1.8a: the type connect() makes (_cn_ptype).
        call = seg.index('_dash_validate_opts "`_cn_ptype\'" `_sl_n\'')
        assert seg.rindex("local _sl_n 1", 0, call) > seg.rindex(
            "_dash_fold_bw", 0, call)

    def test_the_locals_reader_is_public_and_needed(self):
        assert re.search(r"^\*!   _dash_stylelist_locals\(raw, stub\)",
                         _read(_MATA), re.M)
        needed = _program_body(_read(_ADO), "_dash_require_mata")
        needed = needed[needed.index("local _needed"):needed.index(
            "local _missing")]
        assert re.search(r"\b_dash_stylelist_locals\b", needed)


def _figs(mode, spec):
    figs, _ = mp._figures_in(mode, spec)
    return figs


def _glyphs(fig):
    return [r for r in fig.renderers if isinstance(r, GlyphRenderer)]


def _resolved(r, prop):
    """The one value a glyph property draws: a field's distinct column
    value, or the value itself."""
    v = getattr(r.glyph, prop)
    f = _field(v) if not isinstance(v, (int, float)) else None
    if f:
        vals = {float(x) for x in r.data_source.data[f]}
        return vals.pop() if len(vals) == 1 else sorted(vals)
    if isinstance(v, dict):
        v = v.get("value")
    return float(getattr(v, "value", v))


def _label_texts(fig):
    return [sorted({str(t) for t in ls.source.data[_field(ls.text)]})
            for ls in _labelsets(fig)]


@pytest.mark.parametrize("mode", ["saved", "served"])
class TestBothModesDrawEachSeriesValue:
    def test_each_series_draws_its_own_value(self, mode):
        (fig,) = _figs(mode, mp._spec(_SERIES["LAB"]))
        assert _label_texts(fig) == [["3", "4", "5"],
                                     ["Domestic", "Foreign"]]
        (fig,) = _figs(mode, mp._spec(_SERIES["BAR"]))
        bars = _glyphs(fig)
        assert [(_resolved(r, "bottom"), _resolved(r, "width"))
                for r in bars] == [(10.0, 0.4), (20.0, 0.8)]
        (fig,) = _figs(mode, mp._spec(_SERIES["JIT"]))
        xs = [_field(r.glyph.x) for r in _glyphs(fig)]
        assert xs[0] == "weight" and xs[1] != "weight"


class TestAfterAFilterMove:
    def test_served_move_keeps_each_series_value(self):
        spec = mp._spec(_SERIES["LAB"] + [], {"filter": "price, type(range)"})
        doc, _ = mp._served(spec)
        import test_served_filter_move as sfm
        before = [ls.source.data[_field(ls.text)]
                  for f in sfm._figures(doc) for ls in _labelsets(f)]
        sfm._move(doc, "RangeSlider", (4500.0, 11385.0))
        (fig,) = sfm._figures(doc)
        after = [list(ls.source.data[_field(ls.text)])
                 for ls in _labelsets(fig)]
        assert [len(a) for a in after] != [len(b) for b in before]
        assert set(map(str, after[0])) <= {"3", "4", "5"}
        assert set(map(str, after[1])) <= {"Domestic", "Foreign"}


class TestTheHelpSaysSo:
    def test_the_value_list_sentences(self):
        hlp = " ".join(_read(_HLP).split())
        assert ("{cmd:colorvar()} names one, {cmd:mlabel()} one per y"
                in hlp)
        assert ("{cmd:mlabel()}, {cmd:jitter()}, {cmd:base()} and "
                "{cmd:barwidth()} are read the same way, one element per y"
                in hlp)
        assert "{cmd:mlabel()} with more than one variable" not in hlp
        assert ("must be a number from 0 to 100, or a list of them, one per y"
                in hlp)
