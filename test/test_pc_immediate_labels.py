"""headlabel and the immediate types' labels (WP-47 section 47-01).

basic:PT-1 (with basic:PT-2, MS-6): ``headlabel`` was ignored on
``pcscatter`` and ``pccapsym`` with ``mlabel()`` and on ``pcarrowi``'s
own labels -- dash drew them at the first point, (x1, y1).  twoway draws
them at the second, (x2, y2): measured 10nov2026 from its SVG export,
test/fixtures/immediate_label_truth.json H01-H07
(scripts/extract_immediate_label_truth.do) -- "AMC Concord" at weight
2965, mpg 21.8 beside its first point (2930, 22) without headlabel and at
74.6, 10.8 beside its second (40, 11) with it; pcarrowi's "A" at 2020,
19.8 by its tail (2000, 20) and at 4020, 29.8 by its head (4000, 30).

MS-7 (with MS-8, MS-9): see TestImmediateRecast.
"""
import json
import math
import os
import re
import sys
import warnings

import pandas as pd
import pytest
from bokeh.models import ColumnDataSource, LabelSet
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from test_server_layer_defects import (make_spec, plot_for,  # noqa: E402
                                       served, standalone, _DF)

_FIXTURE = os.path.join(_HERE, "fixtures", "immediate_label_truth.json")
_MODES = ("saved", "served")
#: pcarrowi's and pci's records as dash.ado writes
#: `20 2000 30 4000 "A" 25 3000 35 4000 (9) "B"'.
_PC_VALUES = [[20.0, 2000.0, 30.0, 4000.0, "A", None],
              [25.0, 3000.0, 35.0, 4000.0, "B", 9]]


def _truth():
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _field(v):
    return v if isinstance(v, str) else getattr(v, "field", v)


def _label_points(figs):
    """{(text, x, y)} of every label drawn: each LabelSet's rows whose
    position is finite (a NaN position draws nothing)."""
    out = set()
    for f in figs:
        for ls in f.center:
            if not isinstance(ls, LabelSet):
                continue
            d = ls.source.data
            xs, ys = d[_field(ls.x)], d[_field(ls.y)]
            ts = d[_field(ls.text)]
            for x, y, t in zip(xs, ys, ts):
                if math.isfinite(float(x)) and math.isfinite(float(y)):
                    out.add((str(t), float(x), float(y)))
    return out


def _figs(mode, tmp_path, plot):
    spec = make_spec([plot])
    if mode == "saved":
        return standalone(tmp_path, spec)[0]
    return served(tmp_path, spec)[0]


def _points(figs):
    return {(x, y) for _t, x, y in _label_points(figs)}


# ===========================================================================
# basic:PT-1 -- headlabel
# ===========================================================================

class TestHeadlabel:
    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("ptype", ["pcscatter", "pccapsym"])
    def test_labels_the_second_point(self, mode, ptype, tmp_path):
        """plot_for's pc layer: y1 mpg, x1 weight, y2 price, x2 foreign."""
        plot = plot_for(ptype, {"mlabel": "mpg", "headlabel": "headlabel"})
        got = _points(_figs(mode, tmp_path, plot))
        want = set(zip(_DF["foreign"].astype(float), _DF["price"].astype(float)))
        assert got == want

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("ptype", ["pcscatter", "pccapsym"])
    def test_without_headlabel_the_first_point(self, mode, ptype, tmp_path):
        plot = plot_for(ptype, {"mlabel": "mpg"})
        got = _points(_figs(mode, tmp_path, plot))
        assert got == set(zip(_DF["weight"].astype(float),
                              _DF["mpg"].astype(float)))

    @pytest.mark.parametrize("mode", _MODES)
    def test_pcarrowi_labels_the_head(self, mode, tmp_path):
        plot = plot_for("pcarrowi", {"headlabel": "headlabel"},
                        values=_PC_VALUES)
        got = _label_points(_figs(mode, tmp_path, plot))
        assert got == {("A", 4000.0, 30.0), ("B", 4000.0, 35.0)}

    @pytest.mark.parametrize("mode", _MODES)
    def test_pcarrowi_recast_pcbarrow(self, mode, tmp_path):
        plot = plot_for("pcarrowi", {"headlabel": "headlabel",
                                     "recast": "pcbarrow"},
                        values=_PC_VALUES)
        got = _label_points(_figs(mode, tmp_path, plot))
        assert got == {("A", 4000.0, 30.0), ("B", 4000.0, 35.0)}

    @pytest.mark.parametrize("case", ["H01", "H02", "H03", "H04", "H05",
                                      "H06", "H07"])
    def test_positions_match_twoway(self, case):
        """Each label dash draws sits at the point twoway's same label is
        drawn beside: within 2% of the axis's span on each axis (the label's
        own 3 o'clock offset), and nearer that point than the other end."""
        fx = _truth()
        rec = fx[case]
        assert rec["twoway_rc"] == 0 and rec["labels"], case
        head = "headlabel" in rec["cmd"]
        gm = dr.GlyphMapper()
        fig = figure()
        if case in ("H05", "H06", "H07"):
            opts = {"headlabel": "headlabel"} if head else {}
            if "recast(pcbarrow)" in rec["cmd"]:
                opts["recast"] = "pcbarrow"
            ends = {"A": (2000.0, 20.0, 4000.0, 30.0),
                    "B": (3000.0, 25.0, 4000.0, 35.0)}
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                gm.map_pcarrowi(fig, _PC_VALUES, opts)
        else:
            pts = fx["points"]
            makes = sorted(pts)
            src = ColumnDataSource({
                "y1": [pts[m]["y1"] for m in makes],
                "x1": [pts[m]["x1"] for m in makes],
                "y2": [pts[m]["y2"] for m in makes],
                "x2": [pts[m]["x2"] for m in makes],
                "make": makes})
            ends = {m: (pts[m]["x1"], pts[m]["y1"], pts[m]["x2"],
                        pts[m]["y2"]) for m in makes}
            opts = {"mlabel": "make"}
            if head:
                opts["headlabel"] = "headlabel"
            mapper = gm.map_pcscatter if "pcscatter" in rec["cmd"] \
                else gm.map_pccapsym
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                mapper(fig, src, "y1", "x1", "y2", "x2", opts)
        drawn = {t: (x, y) for t, x, y in _label_points([fig])}
        xs = [v for e in ends.values() for v in (e[0], e[2])]
        ys = [v for e in ends.values() for v in (e[1], e[3])]
        sx, sy = max(xs) - min(xs), max(ys) - min(ys)
        for lab in rec["labels"]:
            x1, y1, x2, y2 = ends[lab["text"]]

            def dist(px, py):
                return math.hypot((lab["x"] - px) / sx, (lab["y"] - py) / sy)
            near = (x2, y2) if dist(x2, y2) < dist(x1, y1) else (x1, y1)
            assert near == ((x2, y2) if head else (x1, y1)), (case, lab)
            assert drawn[lab["text"]] == near, (case, lab, drawn)
            assert abs(lab["x"] - near[0]) / sx < 0.02, (case, lab)
            assert abs(lab["y"] - near[1]) / sy < 0.02, (case, lab)

    def test_saved_move_keeps_the_head(self):
        """The saved page's own filter callback, run under node: after a
        move the labels kept are still at their second points."""
        from test_saved_filter_layers import _MOVES, _move, _render
        from test_mode_parity import _DF as PDF, _spec
        _name, filt, action, _oracle = _MOVES[1]
        spec = _spec([plot_for("pcscatter", {"mlabel": "rep",
                                             "headlabel": "headlabel"})],
                     {"filter": filt})
        r = _render(spec)
        _move(r, action)
        figs = list(r.figures.values())
        keep = PDF[(PDF["price"] >= 4500) & (PDF["price"] <= 11385)]
        want = set(zip(keep["foreign"].astype(float),
                       keep["price"].astype(float)))
        assert _points(figs) == want

    def test_served_move_keeps_the_head(self):
        """The served app's own widget callback: after a move the labels
        kept are at their second points."""
        from bokeh.plotting import figure as _Figure
        from test_mode_parity import (_DF as PDF, _fire, _served, _spec,
                                      _walk_models, _widgets_of)
        spec = _spec([plot_for("pcscatter", {"mlabel": "rep",
                                             "headlabel": "headlabel"})],
                     {"filter": "price, type(range)"})
        doc, _ = _served(spec)
        w = [w for w in _widgets_of(doc)
             if type(w).__name__ == "RangeSlider"][0]
        _fire(w, (4500.0, 11385.0))
        figs = [m for m in _walk_models(doc) if isinstance(m, _Figure)]
        keep = PDF[(PDF["price"] >= 4500) & (PDF["price"] <= 11385)]
        want = set(zip(keep["foreign"].astype(float),
                       keep["price"].astype(float)))
        assert figs and _points(figs) == want

    @pytest.mark.parametrize("ptype", ["pcspike", "pccapsym", "pcarrow",
                                       "pcbarrow", "pcscatter", "pci",
                                       "pcarrowi", "rpcap", "rpspike"])
    def test_silent(self, ptype):
        """headlabel is never named in the note on a type twoway takes it
        on: an arrow type draws it (the _hl_named loop skips them), as do
        pcscatter and pccapsym (skipped by name), and every other type
        that takes it is in _dash_tw_silent_tab's headlabel row."""
        with open(os.path.join(_ROOT, "dash.ado"), encoding="utf-8") as fh:
            ado = fh.read()
        with open(os.path.join(_ROOT, "dash_parse.mata"),
                  encoding="utf-8") as fh:
            mata = fh.read()
        arrows = re.search(r'local arrow_types "([^"]*)"', ado).group(1).split()
        drawn = re.search(r'local _hl_drawn "([^"]*)"', ado)
        drawn = drawn.group(1).split() if drawn else []
        row = re.search(r't = t \\ \("headlabel", "([^"]*)"\)', mata)
        silent = row.group(1).split() if row else []
        assert ptype in set(arrows) | set(drawn) | set(silent), ptype
        if ptype in ("pcscatter", "pccapsym"):
            assert ptype in drawn


class TestTheHelp:
    def test_the_arrow_options_sentence(self):
        from test_help_claims_1 import _between, _help
        s = " ".join(_between(_help(), "{opt headlabel} puts the marker labels",
                              "A range type takes").split())
        assert "taken in silence, as {cmd:twoway} takes it" in s
        assert "refused, as {cmd:twoway} refuses it" in s
        assert ("{cmd:mangle()} and {cmd:barbsize()} off the arrow types "
                "are taken in silence") in s
        assert "named in the note" not in s

    def test_where_labels_are_drawn(self):
        from test_help_claims_1 import _between, _help
        s = " ".join(_between(_help(), "{ul:Where labels are drawn.}",
                              "A paired-coordinate observation").split())
        assert "dash} names it in the note" not in s
        assert ("{cmd:headlabel} moves those labels to the second point, the "
                "head, on {cmd:pcscatter}, {cmd:pccapsym}, {cmd:pcarrow}, "
                "{cmd:pcbarrow} and {cmd:pcarrowi}, as {cmd:twoway} does") in s
