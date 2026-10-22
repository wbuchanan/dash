"""WP-30 S52 (P1.18b): the ``add`` sub-option on the axis label options.

BUGS.md P1.18b: ``ylabel(25, add)`` drew one tick at 25 and named ``add``
in a note, where twoway draws its default ticks 10 20 30 40 and adds 25;
an axis(2) ``add`` was named, not drawn.  Every expectation is twoway's
own, from ``test/fixtures/axis_add_truth.json``
(``scripts/extract_axis_add_truth.do``): one test per mode loops over every
probe row and reports every mismatch (the maintainer's test-writing rule).
The spec each probe is drawn from is the value dash.ado writes for the
command (its Mata merge and expander, test_suboption_reporting.cscript
AD-01..AD-09), or the command's own text where the renderer reads it the
same way.

While iterating: ``python3 -m pytest test/test_axis_add.py -q``.
"""
import json
import os
import re
import sys

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import js_runner  # noqa: E402
import test_axis2_suboptions as a2  # noqa: E402
import test_axis_suboptions as tas  # noqa: E402
import test_by_scales as tb  # noqa: E402
import test_default_axes as tda  # noqa: E402
from test_date_axis_residuals import _L  # noqa: E402
from test_date_range import _filter, _saved, _served  # noqa: E402
from test_date_range import _spec as _dspec  # noqa: E402
from probe_groups import probe_params, representative  # noqa: E402

with open(os.path.join(_HERE, "fixtures", "axis_add_truth.json"),
          encoding="utf-8") as _fh:
    _FIX = json.load(_fh)
_P = _FIX["probes"]
_MODES = ("saved", "served")
_SC = tb.SC

#: Each auto probe: the graph options dash draws it from and the axis read.
_AUTO = {
    "base": ({}, "y"),
    "add25": ({"ylabel": "25, add"}, "y"),
    "add5": ({"ylabel": "5, add"}, "y"),
    "add50": ({"ylabel": "50, add"}, "y"),
    "addto": ({"ylabel": "15 25 35, add"}, "y"),
    "addslash": ({"ylabel": "15/17, add"}, "y"),
    "addmixed": ({"ylabel": '15 "a" 25(10)45, add'}, "y"),
    "addlab": ({"ylabel": '25 "x", add'}, "y"),
    "rule": ({"ylabel": "15(10)35, add"}, "y"),
    "rule50": ({"ylabel": "15(10)35 50, add"}, "y"),
    "n2": ({"ylabel": "#2, add"}, "y"),
    "n2_25": ({"ylabel": "#2 25, add"}, "y"),
    "minmax": ({"ylabel": "minmax, add"}, "y"),
    "none": ({"ylabel": "none, add"}, "y"),
    "empty": ({"ylabel": ", add"}, "y"),
    "m_plain": ({"ylabel": "25 35"}, "y"),
    "m_both": ({"ylabel": "25 35, add"}, "y"),
    "m_second": ({"ylabel": "35"}, "y"),
    "m_nolab": ({"ylabel": "25 35, nolabels"}, "y"),
    "a01": ({"ylabel": "25, nolabels add"}, "y"),
    "a02": ({"ylabel": "25, labsize(small) add"}, "y"),
    "a05": ({"ylabel": "#3 25, add"}, "y"),
    "a06": ({"ylabel": "25, add norescale"}, "y"),
    "a07": ({"ylabel": "50, add norescale"}, "y"),
    "a08": ({"xlabel": "5000 1500, add"}, "x"),
    "nr_rule": ({"ylabel": "0(10)100, norescale"}, "y"),
    "nr_list": ({"ylabel": "0 10 20, norescale"}, "y"),
    "noticks": ({"ylabel": "25, noticks add"}, "y"),
}
#: The probes whose added values union with the default ticks: the values.
_UNION = {"add25": (25.0,), "add50": (50.0,),
          "addmixed": (15.0, 25.0, 35.0, 45.0), "m_both": (25.0, 35.0),
          "a07": (50.0,)}


def _axis_of(f, letter):
    return a2._left(f) if letter == "y" else a2._bottom(f)


def _add_notes(caught):
    return [w for w in caught
            if "sub-option" in w and "add" in w.split(":")[-1].split()]


def _sorted(v):
    return sorted(float(x) for x in v)


class TestTheFixture:
    def test_it_is_stamped(self):
        m = _FIX["_meta"]
        assert all(k in m for k in ("stata_version", "born_date",
                                    "dash_commit", "extracted"))
        assert m["stata_version"].startswith("19.")
        assert set(_AUTO) | {"a03", "a04", "b00", "b01", "b02", "by",
                             "by_base", "ts_base", "ts_x492",
                             "ts_tlabel"} == set(_P)
        assert all(p["rc"] == 0 for p in _P.values())


class TestTheParser:
    def test_add_is_read_from_the_tail(self):
        s = dr._dash_parse_axis_spec("25, add")
        assert s["add"] is True and s["unsupported"] == []
        assert dr._dash_parse_axis_spec('25 "add" 35')["add"] is False
        # A leading rule spends it (E6); a value list keeps it.
        for raw in ("15(10)35, add", "15(10)35 50, add", "#2 25, add",
                    "minmax, add", "none, add", ", add"):
            got = dr._dash_parse_axis_spec(raw)
            assert got["add"] is False and got["unsupported"] == [], raw
        for raw in ("15/17, add", "15 25 to 35, add", '"a" 25, add',
                    '15 "a" 25(10)45, add'):
            assert dr._dash_parse_axis_spec(raw)["add"] is True, raw


def _auto_category(pid):
    """An auto probe's family for the served subset: its axis, whether it
    adds, whether it keeps the scale (norescale) and its rule's form (a
    #n count, a (step) rule, minmax or none, or plain values)."""
    go, letter = _AUTO[pid]
    spec = " ".join(str(v) for v in go.values())
    form = ("count" if "#" in spec else "rule" if "(" in spec
            else "word" if re.search(r"\b(minmax|none)\b", spec)
            else "values" if spec.split(",")[0].strip() else "empty")
    return (letter, "add" in spec, "norescale" in spec, form)


#: The gate's served subset (pytest speed,
#: 22oct2026): the first probe of each _auto_category and every fourth
#: probe of the rest; release checks every probe served.
_AUTO_PARAMS = probe_params(sorted(_AUTO), representative(
    sorted(_AUTO), _auto_category, stride=4))


class TestAddUnionsWithTheDefault:
    @pytest.mark.parametrize("mode,group", _AUTO_PARAMS)
    def test_probe(self, mode, group):
        """Every auto probe: the axis's ticks, its hull and its labels'
        visibility are twoway's, and no note names add."""
        bad = []
        for pid in group:
            go, letter = _AUTO[pid]
            figs, caught = a2._draw(mode, a2._spec(_SC, go))
            f = figs[0]
            rec = _P[pid]["yaxis1" if letter == "y" else "xaxis1"]
            ax = _axis_of(f, letter)
            got = tb._major_ticks(ax)
            if got != _sorted(rec["ticks"]):
                bad.append((pid, "ticks", got, _sorted(rec["ticks"])))
            hull = tda._inner(f, letter)
            if hull[0] != pytest.approx(rec["range"][0]) \
                    or hull[1] != pytest.approx(rec["range"][1]):
                bad.append((pid, "range", hull, rec["range"]))
            shown = ax.major_label_text_font_size != "0px"
            if shown != rec["labels_shown"]:
                bad.append((pid, "labels", shown))
            if _add_notes(caught):
                bad.append((pid, "note", _add_notes(caught)))
        assert not bad, "\n".join(map(str, bad))

    def test_labels_are_kept(self):
        figs, _ = a2._draw("saved", a2._spec(_SC, {"ylabel": '25 "x", add'}))
        assert a2._left(figs[0]).major_label_overrides == {25.0: "x"}


class TestAfterAFilterMove:
    @pytest.mark.parametrize("mode", _MODES)
    def test_probe(self, mode):
        """A move that keeps every row draws the fixture's ticks; one that
        keeps half draws the moved default ticks plus the added values."""
        filt, kind, half = tda._RANGE
        df = tb._frame()
        whole = (float(df.price.min()), float(df.price.max()))
        f0 = tda._after(mode, tda._spec(_SC, filt=filt), kind, half)[0]
        base_half = tb._major_ticks(a2._left(f0))
        bad = []
        for pid, vals in _UNION.items():
            spec = tda._spec(_SC, _AUTO[pid][0], filt=filt)
            want = sorted(set(base_half) | set(vals))
            f = tda._after(mode, spec, kind, half)[0]
            got = tb._major_ticks(a2._left(f))
            if got != want:
                bad.append((pid, "half", got, want))
            # norescale keeps 50 out of the moved hull too (a07).
            if pid == "a07" and tda._inner(f, "y") != pytest.approx(
                    tda._inner(f0, "y")):
                bad.append((pid, "hull", tda._inner(f, "y"),
                            tda._inner(f0, "y")))
            got = tb._major_ticks(a2._left(tda._after(mode, spec, kind,
                                                      whole)[0]))
            if got != _sorted(_P[pid]["yaxis1"]["ticks"]):
                bad.append((pid, "whole", got))
        assert not bad, "\n".join(map(str, bad))


class TestTheRefinishKeepsIt:
    def test_both_modes_agree(self):
        """The saved plan carries the added value as ``extra``; the node
        re-finish of the saved page and the served ``_dash_refinish_axes``
        write the same ticks and ranges after one move."""
        spec = tda._spec(_SC, {"ylabel": "25, add"}, filt=tda._RANGE[0])
        r = tda._saved(spec)
        plan, _models = dr._dash_axis_plan(r.figures, r._facet_map,
                                           zoom=False)
        ys = [a for g in json.loads(plan) for p in g["panels"]
              for a in p["axes"] if a["letter"] == "y"]
        assert ys and all(a["extra"] == [25.0] for a in ys), ys
        saved = tda._axes_of(tda._move_saved(r, *tda._RANGE[1:]))
        served = tda._axes_of(tda._move_served(tda._served(spec),
                                               *tda._RANGE[1:]))
        assert tda._same_axes(saved, served), (saved, served)
        assert 25.0 in saved[0][2]


#: A 60-month %tm frame (2000m1-2004m12), y = 100 + n.
_TM = pd.DataFrame({"t": np.arange(480.0, 540.0),
                    "y": 100.0 + np.arange(1.0, 61.0)})
_TM["tv"] = _TM["t"]


def _tm_build(tmp_path, mode, go):
    spec = _dspec([_L("line", "y", "t")], formats={"t": "%tm"},
                  graph_options=go, filters=[_filter("range", "tv")])
    if mode == "saved":
        r, caught = _saved(tmp_path, spec, _TM)
        return r, list(r.figures.values()), caught
    doc, caught = _served(tmp_path, spec, _TM)
    return doc, tb._figs_of(doc.roots), caught


def _x_ticks_tm(figs):
    ax = [a for a in figs[0].below if hasattr(a, "ticker")][0]
    return [round(dr._dash_unix_ms_to_unit(t, "m"), 6)
            for t in tb._major_ticks(ax)]


class TestOnADateAxis:
    @pytest.mark.parametrize("mode", _MODES)
    def test_one_date_is_added(self, tmp_path, mode):
        """``xlabel(492, add)`` on a %tm axis: the default date ticks plus
        2001m1, at build and after a move (twoway: ts_x492 = ts_base +
        492, and tlabel(2001m1, add) the same).  dash's model already
        ticks 492 over these 60 months, so 495 (2001m4), which it does
        not, is added too."""
        assert _sorted(_P["ts_x492"]["xaxis1"]["ticks"]) == sorted(
            set(_P["ts_base"]["xaxis1"]["ticks"]) | {492.0})
        assert _P["ts_tlabel"]["xaxis1"] == _P["ts_x492"]["xaxis1"]
        mv = tda._move_saved if mode == "saved" else tda._move_served
        bad = []
        for kept in (None, (480.0, 509.0)):
            got_t = []
            for i, go in enumerate(({}, {"xlabel": "492 495, add"})):
                sub = tmp_path / ("%s_%d_%s" % (mode, i, kept is None))
                sub.mkdir()
                obj, figs, caught = _tm_build(sub, mode, go)
                if kept is not None:
                    figs = mv(obj, "RangeSlider", kept)
                got_t.append(_x_ticks_tm(figs))
                if _add_notes(caught):
                    bad.append(("note", caught))
            if got_t[1] != sorted(set(got_t[0]) | {492.0, 495.0}):
                bad.append((kept, got_t))
        assert not bad, bad


class TestTheSecondAxis:
    @pytest.mark.parametrize("mode", _MODES)
    def test_add_is_drawn(self, mode):
        bad = []
        for pid, raw in (("b00", None), ("b01", "6000, add"),
                         ("b02", "6000 9000, add")):
            go = {"ylabel2": raw} if raw else {}
            figs, caught = a2._draw(mode, a2._spec(tb.DUAL_Y, go))
            got = tb._major_ticks(a2._y2(figs[0]))
            want = _sorted(_P[pid]["yaxis2"]["ticks"])
            if got != want:
                bad.append((pid, got, want))
            if _add_notes(caught):
                bad.append((pid, _add_notes(caught)))
        assert not bad, bad


class TestUnderBy:
    @pytest.mark.parametrize("mode", _MODES)
    def test_each_panel(self, mode):
        bad = []
        for pid, go in (("by_base", {"by": "foreign"}),
                        ("by", {"by": "foreign", "ylabel": "25, add"})):
            figs = [f for f in tda._figs(mode, tda._spec(_SC, go))
                    if f.renderers]
            want = [_sorted(_P[pid]["panel%d" % k]["ticks"])
                    for k in (1, 2)]
            got = [tb._major_ticks(a2._left(f)) for f in figs]
            if got != want:
                bad.append((pid, got, want))
        assert not bad, bad


class TestTheLookApplies:
    @pytest.mark.parametrize("mode", _MODES)
    def test_nolabels_and_noticks(self, mode):
        figs, _ = a2._draw(mode, a2._spec(_SC, {"ylabel": "25, add nolabels"}))
        ax = a2._left(figs[0])
        assert ax.major_label_text_font_size == "0px"
        assert tb._major_ticks(ax) == [10.0, 20.0, 25.0, 30.0, 40.0]
        figs, _ = a2._draw(mode, a2._spec(_SC, {"ylabel": "25, add noticks"}))
        ax = a2._left(figs[0])
        assert (ax.major_tick_in, ax.major_tick_out) == (0, 0)
        assert tb._major_ticks(ax) == [10.0, 20.0, 25.0, 30.0, 40.0]


class TestTheColourKeyNamesIt:
    @pytest.mark.parametrize("mode", _MODES)
    def test_named_once(self, mode):
        cv = [tas.plot_for("scatter", {"colorvar": "price"})]
        _f, caught = tas._figs(mode, {"zlabel": "4000 8000, add"}, cv)
        z = tas._notes(caught, "zlabel() sub-option")
        assert len(z) == 1 and z[0].split(":")[-1].split() == ["add"], caught


class TestTheTickOptionIgnoresIt:
    @pytest.mark.parametrize("mode", _MODES)
    def test_silent(self, mode):
        """``ytick(25, add)`` draws as ``ytick(25)`` (twoway a03 = a04)."""
        assert _P["a03"]["yaxis1"] == _P["a04"]["yaxis1"]
        drawn = []
        for raw in ("25", "25, add"):
            figs, caught = a2._draw(mode, a2._spec(_SC, {"ytick": raw}))
            ax = a2._left(figs[0])
            drawn.append((tb._major_ticks(ax), a2._extra(ax)))
            assert not [w for w in caught if "ytick()" in w], caught
        assert drawn[0] == drawn[1]
        assert drawn[1] == (_sorted(_P["a04"]["yaxis1"]["ticks"]),
                            _P["a04"]["yaxis1"]["unlabelled"])


class TestTheUnitFunctions:
    def test_axis_add(self):
        from bokeh.models import (BasicTicker, CategoricalAxis,
                                  CategoricalTicker, FixedTicker, LinearAxis)
        spec = dr._dash_parse_axis_spec('25 "x", add')
        ax = LinearAxis(ticker=dr._dash_default_ticker(5))
        keep = ax.ticker
        assert dr._dash_axis_add(ax, spec) is True
        assert ax.ticker is keep
        assert ax._dash_extra_ticks == [25.0]
        assert ax.major_label_overrides == {25.0: "x"}
        # A ticker that is no default one becomes a default placeholder of
        # numticks.
        for t in (FixedTicker(ticks=[1.0]), BasicTicker()):
            ax = LinearAxis(ticker=t, major_label_overrides={1.0: "one"})
            assert dr._dash_axis_add(ax, spec, numticks=7) is True
            assert dr._DASH_DEFAULT_TAG in ax.ticker.tags
            assert dr._dash_count_of(ax.ticker) == 7
        assert ax.major_label_overrides == {1.0: "one", 25.0: "x"}
        # norescale keeps the values out of the hull.
        ax = LinearAxis(ticker=dr._dash_default_ticker(5))
        assert dr._dash_axis_add(
            ax, dr._dash_parse_axis_spec("50, add norescale")) is True
        assert ax._dash_extra_norescale is True
        # A categorical axis, a spec without add or without values: False.
        cat = CategoricalAxis(ticker=CategoricalTicker())
        assert dr._dash_axis_add(cat, spec) is False
        assert isinstance(cat.ticker, CategoricalTicker)
        ax = LinearAxis(ticker=dr._dash_default_ticker(5))
        assert dr._dash_axis_add(ax, dr._dash_parse_axis_spec("25")) is False
        assert dr._dash_axis_add(ax, dr._dash_parse_axis_spec(", add")) \
            is False
        assert getattr(ax, "_dash_extra_ticks", None) is None


class TestTheHelp:
    def test_it_documents_add(self):
        with open(os.path.join(_HERE, "..", "dash.sthlp"),
                  encoding="utf-8") as fh:
            text = fh.read()
        assert "is named, not applied" not in text
        assert re.search(r"\{cmd:add\} adds the listed values to the "
                         r"axis's\s+default ticks", text)
        assert re.search(r"adds to that\s+axis's\s+default\s+ticks", text)
