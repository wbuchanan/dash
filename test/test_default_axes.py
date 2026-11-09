"""WP-30 P1.3a (section 21): default axes as twoway draws them.

BUGS.md "Default numeric axes use Bokeh's ticker and 10 percent padding,
not twoway's natscale ticks and plot-region margin, and fit lines are left
out of the axis range".  Measured at the batch-7 base (41d6e10), in both
modes: ``scatter mpg weight`` drew Bokeh's 15(5)40 over 10.55-42.45 where
twoway draws 10(10)40 over 10-41 plus its plot-region margin; a fit was
clipped; a second axis kept Bokeh's ticks; nothing re-ticked after a
filter move.

Every expectation is twoway's own, from ``test/fixtures/default_axes_truth.
json`` (``scripts/extract_default_axes_truth.do``): one test per mode loops
over every probe row and reports every mismatch (the maintainer's
test-writing rule).  The helpers each have one test; the after-move,
reset, zoom, plan and budget rules one per mode.

While iterating: ``python3 -m pytest test/test_default_axes.py -q``.
"""
import json
import math
import os
import random
import sys
import time
import types
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import js_runner  # noqa: E402
import test_by_scales as tb  # noqa: E402
from conftest import make_data_json  # noqa: E402
from probe_groups import probe_params, representative  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "default_axes_truth.json")
_MODES = ("saved", "served")
P = tb._plot


from conftest import render_models  # noqa: E402


def _truth():
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Building pages
# ---------------------------------------------------------------------------

def _frame(which="auto"):
    df = tb._frame("auto")
    if which.startswith("g"):
        g = int(which[1:])
        df = df.assign(g=[float((i + 1) % g) for i in range(len(df))])
    elif which == "c5":
        df = df.assign(c=[5.0] * len(df))
    elif which == "tc":
        base = (pd.Timestamp("2001-01-01") - pd.Timestamp("1960-01-01")
                ).total_seconds() * 1000.0
        df = df.assign(t=[base + (i + 1) * 7 * 3600000.0
                          for i in range(len(df))])
    return df


def _write(spec, which="auto"):
    tag = next(tb._SEQ)
    sp = os.path.join(tb._TMP, "ns_spec_%d.json" % tag)
    dp = os.path.join(tb._TMP, "ns_data_%d.json" % tag)
    d = tb._truth()["data"]
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(make_data_json(_frame(which), d["auto_value_labels"],
                                 d["auto_value_label_names"], tb._LABELS), fh)
    return tag, sp, dp


def _spec(plots, go=None, scheme="", filt="", if_expr="", formats=None):
    s = tb._spec(plots, go, filt=filt, formats=formats, if_expr=if_expr)
    s["build_options"]["scheme"] = scheme
    return s


def _saved(spec, which="auto"):
    """The rendered saved page's renderer (figures, callbacks, widgets)."""
    _tag, sp, dp = _write(spec, which)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = dr.DashRenderer(sp, dp)
        render_models(r)
    return r


def _served(spec, which="auto"):
    """The served app's document, drawn once and outside any warning
    capture of its own: its session notes reach the caller's capture
    (test_axis_look_options reads them), as the import-time draw's did."""
    from bokeh.document import Document
    tag, sp, dp = _write(spec, which)
    ap = os.path.join(tb._TMP, "ns_app_%d.py" % tag)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(ap)
    mod = tb.load_app(ap, "_ns_app_%d" % tag, draw=False)
    doc = Document()
    mod.make_document(doc)
    return doc


def _figs(mode, spec, which="auto"):
    if mode == "saved":
        return tb._panels(list(_saved(spec, which).figures.values()))
    return tb._panels(tb._figs_of(_served(spec, which).roots))


def _axis(f, letter, name="default"):
    from bokeh.models.axes import ContinuousAxis
    sides = (f.left + f.right) if letter == "y" else (f.below + f.above)
    attr = letter + "_range_name"
    return [a for a in sides if isinstance(a, ContinuousAxis)
            and getattr(a, attr, "default") == name][0]


def _range(f, letter, name="default"):
    return (getattr(f, letter + "_range") if name == "default"
            else getattr(f, "extra_%s_ranges" % letter)[name])


def _ticks(f, letter, name="default"):
    return tb._major_ticks(_axis(f, letter, name))


def _inner(f, letter, name="default"):
    ax = _axis(f, letter, name)
    kind = "log" if type(ax).__name__ == "LogAxis" else None
    return dr._dash_range_hull(_range(f, letter, name), kind,
                               margin=f._dash_margin[letter])


def _steps(major):
    lo, d, hi = major
    if d is None or d == 0:
        return [lo] if lo == hi else [lo, hi]
    return [round(v, 9) for v in tb._steps(lo, hi, d)]


def _near(a, b, span, tol=1e-6):
    return abs(float(a) - float(b)) <= tol * max(abs(span), 1e-12)


# ---------------------------------------------------------------------------
# The probes: twoway's command -> dash's spec
# ---------------------------------------------------------------------------

_SC = [P("scatter", "mpg", "weight")]
_SCI = {"type": "scatteri", "values": [[50.0, 1000.0]], "options": {}}
_PROBES = {
    # pid: (plots, graph options, scheme, data, if_expr, formats)
    "P01": (_SC, {}, "", "auto", "", None),
    "P01b": (_SC, {"ylabel": "#5", "xlabel": "#5"}, "", "auto", "", None),
    "P02": (_SC, {}, "s2color", "auto", "", None),
    "P10": (_SC, {}, "economist", "auto", "", None),
    "P13": (_SC, {"xsize": "4", "ysize": "4"}, "", "auto", "", None),
    "B03": (_SC, {"xsize": "10", "ysize": "3"}, "s2color", "auto", "", None),
    "B02": (_SC, {"title": '"t"', "note": '"n"', "legend": "on"}, "",
            "auto", "", None),
    "P03": ([P("scatter", "price", "mpg"), P("lfit", "price", "mpg")], {},
            "", "auto", "", None),
    "P05": (_SC + [_SCI], {}, "", "auto", "", None),
    "P06": ([P("scatter", "price", "weight")], {"yscale": "log"}, "", "auto",
            "", None),
    "P08": ([P("histogram", "mpg")], {}, "", "auto", "", None),
    # WP-34 AX-4: twoway ticks a histogram's bin axis over its first and
    # last bin midpoints.
    "H01": ([P("histogram", "price")], {}, "", "auto", "", None),
    "H02": ([P("histogram", "price", bin="8")], {}, "", "auto", "", None),
    "H03": ([P("histogram", "price", width="2000")], {}, "", "auto", "",
            None),
    "H04": ([P("histogram", "rep78", discrete="discrete")], {}, "", "auto",
            "", None),
    "H05": ([P("histogram", "weight", frequency="frequency")], {}, "",
            "auto", "", None),
    "H06": ([P("histogram", "length", percent="percent")], {}, "", "auto",
            "", None),
    "H07": ([P("histogram", "mpg", horizontal="horizontal")], {}, "",
            "auto", "", None),
    "H08": ([P("histogram", "c")], {}, "", "c5", "", None),
    "H09": ([P("histogram", "mpg", gap="50", baroffset="1")], {}, "",
            "auto", "", None),
    "H10": ([P("histogram", "mpg")], {"by": "foreign"}, "", "auto", "",
            None),
    "P09": ([P("bar", "price", "rep78")], {}, "", "auto", "", None),
    "P12": ([{"type": "function", "expr": "x^2",
              "options": {"range": "0 3"}}], {}, "", "auto", "", None),
    "P14": (_SC + [P("lfit", "mpg", "weight")], {}, "", "auto", "", None),
    "P15": ([P("kdensity", "mpg")], {}, "", "auto", "", None),
    "P16": (_SC, {}, "", "auto", "foreign == 1", None),
    "P17": (tb.DUAL_Y, {}, "", "auto", "", None),
    "X2": (_SC + [P("scatter", "mpg", "price", xaxis=2)], {}, "", "auto", "",
           None),
    "P20": (_SC + [P("qfitci", "mpg", "weight")], {}, "", "auto", "", None),
    "Q01": (_SC, {}, "", "auto", "price <= 7075.5", None),
    "Q02": ([P("scatter", "price", "mpg"), P("lfit", "price", "mpg")],
            {"by": "foreign"}, "", "auto", "", None),
    "Q06": (_SC + [P("lfit", "mpg", "weight")], {}, "", "auto",
            "price <= 7075.5", None),
    "Q08": (tb.DUAL_Y, {}, "", "auto", "foreign == 1", None),
    "Q09": ([P("rarea", ("mpg", "turn"), "weight")], {}, "", "auto", "",
            None),
    "Q10": ([P("spike", "mpg", "weight")], {}, "", "auto", "", None),
    "Q11": ([P("dropline", "mpg", "weight")], {}, "", "auto", "", None),
    "P22": ([P("area", "mpg", "weight")], {}, "", "auto", "", None),
    "B01": ([P("bar", "mpg", "weight")], {}, "", "auto", "", None),
    "B06": ([P("bar", "mpg", "weight", base=5)], {}, "", "auto", "", None),
    "Q12": (_SC, {"yscale": "log", "xscale": "log"}, "", "auto", "", None),
    "L00": (_SC, {}, "", "auto", "", None),
    "L01": (_SC, {"yline": "50"}, "", "auto", "", None),
    "L02": (_SC, {"xline": "6000"}, "", "auto", "", None),
    "L03": (_SC, {"text": '50 6000 "hi"'}, "", "auto", "", None),
    # twoway's probe labels make; any variable's labels leave the scale.
    "L04": ([P("scatter", "mpg", "weight", mlabel="rep78")], {}, "", "auto",
            "", None),
    "L05": (_SC + [{"type": "scatteri", "values": [[50.0, 6000.0]],
                    "options": {"msymbol": "none"}}], {}, "", "auto", "",
            None),
    "L07": (_SC + [{"type": "pcarrowi",
                    "values": [[50.0, 6000.0, 45.0, 5500.0]],
                    "options": {}}], {}, "", "auto", "", None),
    "TC": ([P("scatter", "mpg", "t")], {}, "", "tc", "", {"t": "%tc"}),
    "BY2": (_SC, {"by": "foreign"}, "", "auto", "", None),
    "BY3": (_SC, {"by": "g"}, "", "g3", "", None),
    "BY6": (_SC, {"by": "g"}, "", "g6", "", None),
    "BY10": (_SC, {"by": "g"}, "", "g10", "", None),
}


def _probe_spec(pid):
    plots, go, scheme, which, if_expr, formats = _PROBES[pid]
    return _spec(plots, go, scheme, if_expr=if_expr, formats=formats), which


#: Flipped (WP-34 AX-4): twoway's histogram is ticked over its bin
#: midpoints, P08 is compared now.
#: Flipped (WP-34 AX-2): twoway's by() styles set xlabels(#4) as well as
#: ylabels(#4); H10's x (10(10)40 over the midpoints 13.8125-39.1875,
#: where dash drew #5's 15(5)40) is compared now, so nothing is left out.
_NOT_DEFAULT = set()


def _compare(pid, row, figs, bad):
    """Every axis of every panel of *figs* against twoway's *row*."""
    panels = row.get("panels") or [row]
    for k, f in enumerate(figs):
        want = panels[min(k, len(panels) - 1)]
        for axis in ("y", "x", "y2", "x2"):
            if axis not in want or (pid, axis) in _NOT_DEFAULT:
                continue
            shift = (dr._STATA_EPOCH_UNIX_MS if pid == "TC" and axis == "x"
                     else 0.0)
            letter, name = axis[0], (axis if axis[1:] else "default")
            got = [round(v - shift, 6) for v in (_ticks(f, letter, name)
                                                 or [])]
            if got != [round(v, 6) for v in _steps(want[axis]["major"])]:
                bad.append("%s panel %d %s ticks %s, twoway %s"
                           % (pid, k, axis, got, want[axis]["major"]))
            cur = want[axis].get("cur")
            if cur and None not in cur and name == "default":
                lo, hi = _inner(f, letter, name)
                span = cur[1] - cur[0]
                if not (_near(lo - shift, cur[0], span)
                        and _near(hi - shift, cur[1], span)):
                    bad.append("%s panel %d %s inner [%r, %r], twoway %s"
                               % (pid, k, axis, lo - shift, hi - shift, cur))
            t = _axis(f, letter, name).ticker
            if pid == "P01" and list(getattr(t, "minor_ticks", [1])) != []:
                bad.append("%s %s draws minor ticks" % (pid, axis))


def _category(pid):
    """A probe's family for the served subset: its first layer's plot
    type, whether it has a second layer and whether it has by()."""
    plots, go = _PROBES[pid][:2]
    return (plots[0].get("type"), len(plots) > 1, "by" in go)


#: Probes per node and the gate's served subset (pytest speed,
#: 22oct2026): the first probe of each _category and every fourth probe of
#: the rest; release checks every probe served.
_PARAMS = probe_params(sorted(_PROBES), representative(
    sorted(_PROBES), _category, stride=4), size=6, saved_size=21)


# ---------------------------------------------------------------------------
class TestStataTruth:
    """twoway's ticks and scale for every probe, in each mode."""

    def test_the_meta_stamp(self):
        m = _truth()["_meta"]
        assert all(m.get(k) for k in ("stata_version", "born_date",
                                      "dash_commit", "extracted"))

    @pytest.mark.parametrize("mode,group", _PARAMS)
    def test_probes(self, mode, group):
        rows, bad = _truth()["probes"], []
        for pid in group:
            spec, which = _probe_spec(pid)
            _compare(pid, rows[pid], _figs(mode, spec, which), bad)
        assert not bad, "\n".join(bad)

    @pytest.mark.parametrize("mode", _MODES)
    def test_schemes(self, mode):
        rows, bad = _truth()["schemes"], []
        for name in sorted(rows):
            fig = _figs(mode, _spec(_SC, {}, name))[0]
            _compare("scheme " + name, rows[name], [fig], bad)
        assert not bad, "\n".join(bad)

    def test_margin(self):
        """twoway's margin is r x min(W, H) a side, r the scheme's (times
        by()'s f(G)); dash's frame fraction is within A6's 0.008."""
        rows, bad = _truth()["probes"], []
        for pid in sorted(rows):
            row = rows[pid]
            plots, go, scheme, _w, _i, _f = _PROBES[pid]
            sch = dr.SchemeParser(scheme or "stcolor")
            g = len(row.get("panels") or [1])
            if row.get("gmetric") is not None:
                # Flipped (WP-30 P1.20b): a side of the pair, not one
                # number per axis; twoway's margin is per side.
                f = dr._dash_plot_margin(sch, go, panels=g)["y"][0] / (
                    sch.plot_margin_rs / 100.0 * min(
                        sch.graphsize_x, sch.graphsize_y) / sch.graphsize_y)
                if abs(f - row["gmetric"]) > 1e-9:
                    bad.append("%s f(G) %r, twoway %r" % (pid, f,
                                                          row["gmetric"]))
            ours = dr._dash_plot_margin(sch, go, panels=g)
            r = sch.plot_margin_rs / 100.0 * (row.get("gmetric") or 1.0)
            for letter, m in (row.get("svg_margin") or {}).items():
                if abs(m["margin_rel"] - r) > 0.0005:
                    bad.append("%s %s margin_rel %r, r %r"
                               % (pid, letter, m["margin_rel"], r))
                # A6: a title, legend or note shrinks twoway's plot region
                # (B02); dash's fraction is fixed at build.
                if pid != "B02" and g == 1 \
                        and abs(m["frame_frac"] - ours[letter][0]) > 0.008:
                    bad.append("%s %s frame %r, dash %r"
                               % (pid, letter, m["frame_frac"],
                                  ours[letter]))
        assert not bad, "\n".join(bad)


# ---------------------------------------------------------------------------
class TestTheMissFreeReaders:
    """``_dash_has`` and ``_dash_prop`` answer as ``hasattr`` and
    ``getattr`` do, without asking a Bokeh model for a name it lacks."""

    def test__dash_has(self, monkeypatch):
        from types import SimpleNamespace
        from bokeh.core.has_props import HasProps
        from bokeh.models import BooleanFilter, IndexFilter, Plot, RangeTool
        missed = []
        real = HasProps._raise_attribute_error_with_matches
        monkeypatch.setattr(
            HasProps, "_raise_attribute_error_with_matches",
            lambda self, n, p: missed.append(n) or real(self, n, p))
        objs = [IndexFilter(indices=[1]), BooleanFilter(booleans=[True]),
                Plot(), RangeTool(), SimpleNamespace(indices=[2]), None, 3]
        for o in objs:
            for n in ("indices", "booleans", "x_range", "formatter",
                      "source", "data_source"):
                monkeypatch.setattr(HasProps,
                                    "_raise_attribute_error_with_matches",
                                    real)
                want = hasattr(o, n)
                monkeypatch.setattr(
                    HasProps, "_raise_attribute_error_with_matches",
                    lambda self, n, p: missed.append(n) or real(self, n, p))
                assert dr._dash_has(o, n) is want, (o, n)
        assert missed == []

    def test__dash_prop(self):
        from types import SimpleNamespace
        from bokeh.models import IndexFilter
        f = IndexFilter(indices=[1, 3])
        assert list(dr._dash_prop(f, "indices")) == [1, 3]
        assert dr._dash_prop(f, "booleans") is None
        assert dr._dash_prop(f, "booleans", "d") == "d"
        assert dr._dash_prop(SimpleNamespace(source=4), "source") == 4
        assert dr._dash_prop(None, "source", 7) == 7


class TestTheHelpers:
    def test_the_default_ticker_is_a_tagged_fixed_ticker(self):
        from bokeh.models import FixedTicker
        t = dr._dash_default_ticker(5)
        assert isinstance(t, FixedTicker)
        assert list(t.ticks) == [] and list(t.minor_ticks) == []
        assert dr._DASH_DEFAULT_TAG in t.tags
        assert dr._dash_count_of(t) == 5
        assert dr._dash_count_of(dr._dash_default_ticker(10 ** 9)) \
            == dr._MAX_AXIS_TICKS

    def test_the_plot_margin(self):
        """Flipped (WP-30 P1.20b): one number per axis was wrong because
        twoway's plot-region margin is per side (margin_truth.json); the
        scheme's default is the same on both sides of each axis."""
        # Flipped (WP-45 ST-21 residual): each side is over the plot
        # region's estimated side (the graph less the scheme's graph margin
        # and 11% of the smaller side for an axis), not the graph's: was
        # (0.0132, 0.022), (0.016, 0.022), (0.006, 0.006) and (0.022, 0.022).
        bad = []
        for scheme, go, want in (("stcolor", {}, (0.014798206278026908,
                                                  0.02682926829268293)),
                                 ("s2color", {}, (0.018410041841004185,
                                                  0.02682926829268293)),
                                 ("economist", {}, (0.007317073170731708,
                                                    0.007317073170731708)),
                                 ("stcolor", {"xsize": "4", "ysize": "4"},
                                  (0.02682926829268293,
                                   0.02682926829268293))):
            m = dr._dash_plot_margin(dr.SchemeParser(scheme), go)
            if any(abs(v - want[0]) > 1e-12 for v in m["x"]) \
                    or any(abs(v - want[1]) > 1e-12 for v in m["y"]):
                bad.append((scheme, go, m))
        assert not bad

    def test_the_by_factor(self):
        sch = dr.SchemeParser("stcolor")
        # Flipped (WP-30 P1.20b): a side of the per-side pair.
        got = [round(dr._dash_plot_margin(sch, {}, panels=g)["y"][0] / 0.022,
                     12)
               for g in (2, 3, 6, 10)]
        assert got == [0.85, 0.85, 0.8, 0.6]

    def test_the_by_tick_count(self):
        sch = dr.SchemeParser("stcolor")
        assert dr._dash_by_numticks(sch, {}) == {"x": 5, "y": 5, "x2": 5,
                                                 "y2": 5}
        # Flipped (WP-34 AX-2): twoway's by() styles set xlabels(#4) as
        # well as ylabels(#4).
        assert dr._dash_by_numticks(sch, {"by": "foreign"}) == {
            "x": 4, "y": 4, "x2": 5, "y2": 5}

    def test_a_hostile_size_is_bounded(self):
        sch = dr.SchemeParser("stcolor")
        for v in ("1e400", "-3", "abc", "x" * 100000):
            t0 = time.perf_counter()
            m = dr._dash_plot_margin(sch, {"xsize": v, "ysize": v})
            assert time.perf_counter() - t0 < 0.1
            # Flipped (WP-30 P1.20b): each axis is a (start, end) pair.
            assert all(math.isfinite(x) and 0 <= x <= 0.45
                       for pair in m.values() for x in pair)

    def test_padded_range_takes_a_margin(self):
        r = dr._dash_padded_range(10, 41, margin=0.022)
        pad = 0.022 / 0.956 * 31
        assert r.start == pytest.approx(10 - pad, rel=1e-12)
        assert r.end == pytest.approx(41 + pad, rel=1e-12)
        assert (r.reset_start, r.reset_end) == (r.start, r.end)
        assert r._dash_margin_f == 0.022
        legacy = dr._dash_padded_range(10, 41)
        assert legacy.start == pytest.approx(10 - 1.55)
        assert legacy._dash_margin_f is None

    def test_range_hull_inverts_any_margin(self):
        for f in (0.0, 0.006, 0.022, 0.2):
            for kind, lo, hi in ((None, -3.5, 41.0), ("log", 3291.0, 15906.0)):
                for rev in (False, True):
                    r = dr._dash_padded_range(lo, hi, kind, rev, margin=f)
                    a, b = dr._dash_range_hull(r, kind)
                    assert a == pytest.approx(lo, rel=1e-12, abs=1e-12)
                    assert b == pytest.approx(hi, rel=1e-12)
                    assert dr._dash_range_hull(r, kind, margin=f) == (a, b)

    def test_layer_extent_equals_the_python_reader(self):
        from bokeh.models import (BooleanFilter, CDSView, ColumnDataSource,
                                  IndexFilter)
        from bokeh.plotting import figure
        rnd = random.Random(21)
        for _ in range(500):
            n = rnd.randint(0, 12)
            col = [rnd.choice([float("nan"), rnd.uniform(-50, 50),
                               rnd.uniform(0.1, 9)]) for _ in range(n)]
            src = ColumnDataSource({"y": col, "x": list(range(n)),
                                    "b": [rnd.uniform(-5, 5)
                                          for _ in range(n)]})
            fig = figure()
            view = CDSView()
            pick = rnd.random()
            if pick < 0.3 and n:
                view = CDSView(filter=IndexFilter(sorted(rnd.sample(
                    range(n), rnd.randint(0, n)))))
            elif pick < 0.6 and n:
                view = CDSView(filter=BooleanFilter(
                    [rnd.random() < 0.5 for _ in range(n)]))
            r = fig.vbar(x="x", top="y", bottom="b" if rnd.random() < 0.5
                         else rnd.uniform(-3, 3), width=1, source=src,
                         view=view)
            if rnd.random() < 0.3:
                r._dash_auto_base = ("bottom",)
            kind = rnd.choice([None, "log"])
            _, vals = dr._dash_secondary_values(fig, "y_range_name",
                                                "default")
            if kind == "log":
                vals = [v for v in vals if v > 0]
            want = (min(vals), max(vals)) if vals else None
            assert dr._dash_layer_extent(fig.renderers, "y_range_name",
                                         "default", kind) == want

    def test_a_typed_layer_stays_off_a_date_axis(self):
        """Flipped (WP-30 P1.23a): a literal layer on a date axis is placed
        in date units, so it counts in the axis's hull like any other; the
        old ``_dash_raw_sif`` exclusion was wrong because twoway's scale
        spans a literal on a date axis (X 14976..15431 for scatteri 1300
        15400), and the stamp is gone."""
        from bokeh.models import ColumnDataSource
        from bokeh.plotting import figure
        fig = figure()
        a = fig.scatter(x="x", y="y", source=ColumnDataSource(
            {"x": [1.0e12, 1.1e12], "y": [1.0, 2.0]}))
        b = fig.scatter(x="x", y="y", source=ColumnDataSource(
            {"x": [5.0], "y": [9.0]}))
        # The old stamp, were anything to set it, is no longer read.
        b._dash_raw_sif = True
        assert a is not None
        assert dr._dash_layer_extent(fig.renderers, "x_range_name",
                                     "default", "td") == (5.0, 1.1e12)
        assert dr._dash_layer_extent(fig.renderers, "x_range_name",
                                     "default", None) == (5.0, 1.1e12)

    def test_hull_roles(self):
        """Flipped: the bar, bar_base, area, spike and dropline rows read
        S21's ``_dash_auto_base`` stamp -- the default base's role is now
        the renderer's dash_base: tag, read by _dash_base_spec, one marker
        for both modes and the page (P1.17b).  Flipped (WP-30 P1.23a): the
        literal rows asserted a ``_dash_raw_sif`` stamp, which was wrong
        once literals are placed in date units; no renderer carries it."""
        bad = []
        for t, opts, want in (("bar", {}, ("bottom",)),
                              ("bar", {"base": "5"}, None),
                              ("area", {}, ("y1",)),
                              ("spike", {}, ("y0",)),
                              ("dropline", {}, ("y0",)),
                              ("scatter", {}, None)):
            plots = [P(t, "mpg", "weight", **opts)]
            f = _figs("saved", _spec(plots))[0]
            # Flipped (WP-34 PIC-1): an area's outline ring is no tick or
            # hull input on either axis (its own row below) and its key
            # swatch is no layer; the fill keeps its base's role.
            got = {dr._dash_auto_base_props(r, "y") or None
                   for r in f.renderers
                   if type(r.glyph).__name__ != "Scatter"
                   and not dr._dash_is_swatch(r)
                   and "dash_area_outline" not in (r.tags or [])} or {None}
            for r in f.renderers:
                if "dash_area_outline" in (r.tags or []) and not (
                        "x" in dr._dash_auto_base_props(r, "x")
                        and "y" in dr._dash_auto_base_props(r, "y")):
                    bad.append((t, "ring", r.tags))
            if got != {want}:
                bad.append((t, opts, got))
        for lit in ({"type": "scatteri", "values": [[1.0, 2.0]]},
                    {"type": "pci", "values": [[1.0, 2.0, 3.0, 4.0]]},
                    {"type": "pcarrowi", "values": [[1.0, 2.0, 3.0, 4.0]]},
                    {"type": "function", "expr": "x",
                     "options": {"range": "0 1"}}):
            lit.setdefault("options", {})
            f = _figs("saved", _spec(_SC + [lit]))[0]
            flags = [hasattr(r, "_dash_raw_sif") for r in f.renderers]
            if any(flags):
                bad.append((lit["type"], flags))
        assert not bad, bad

    def test_refinish_axes_is_idempotent(self):
        r = _saved(_spec(tb.DUAL_Y, {"by": "foreign"}))
        def state():
            return [(id(getattr(f, a)), getattr(f, a).start, getattr(f, a).end)
                    for f in r.figures.values() for a in ("x_range",
                                                          "y_range")] + [
                (k, v.start, v.end) for f in r.figures.values()
                for k, v in f.extra_y_ranges.items()]
        before = state()
        dr._dash_refinish_axes(r.figures, r._facet_map)
        once = state()
        dr._dash_refinish_axes(r.figures, r._facet_map)
        assert once == state() == before

    def test_axis_plan_shape(self):
        r = _saved(_spec(tb.DUAL_Y, {"by": "foreign"}))
        plan_json, models = dr._dash_axis_plan(r.figures, r._facet_map,
                                               zoom=False)
        plan = json.loads(plan_json)
        assert len({id(m) for m in models}) == len(models)
        assert len(plan) == 1 and plan[0]["share"] == ["x", "y"]
        for p in plan[0]["panels"]:
            for a in p["axes"]:
                for k in ("range", "ticker"):
                    assert -1 <= a[k] < len(models)
                for L in a["layers"] + a["bars"]:
                    assert 0 <= L["src"] < len(models)


class TestTheSchemeKeys:
    def test_numticks_and_margin(self):
        bad = []
        for name in sorted(dr.SchemeParser._BUILTIN_NAMES):
            s = dr.SchemeParser(name)
            want = 0.6 if name == "economist" else 2.2
            if (s.numticks_x, s.numticks_y, s.plot_margin_rs) != (5, 5, want):
                bad.append((name, s.numticks_x, s.numticks_y,
                            s.plot_margin_rs))
        assert not bad


# ---------------------------------------------------------------------------
# After a filter move
# ---------------------------------------------------------------------------

def _pick(w, value):
    from bokeh.models import Select
    if isinstance(w, Select):
        return [v for v, lab in w.options if lab == value][0]
    return value


def _move_saved(r, kind, value):
    """Set the saved page's widget and run its filter callback under node."""
    w = [x for x in r.filter_widgets if type(x).__name__ == kind][0]
    w.value = _pick(w, value)
    js_runner.JsSession(r.filter_callbacks).run(
        r.filter_callbacks[r.filter_widgets.index(w)])
    return tb._panels(list(r.figures.values()))


def _move_served(doc, kind, value):
    import test_mode_parity as mp
    w = [x for x in mp._widgets_of(doc) if type(x).__name__ == kind][0]
    mp._fire(w, _pick(w, value))
    return tb._panels(tb._figs_of(doc.roots))


def _after(mode, spec, kind, value, which="auto"):
    if mode == "saved":
        return _move_saved(_saved(spec, which), kind, value)
    return _move_served(_served(spec, which), kind, value)


_RANGE = ("price, type(range)", "RangeSlider", (3291.0, 7075.5))
_DROP = ("foreign, type(dropdown)", "Select", "Foreign")
_SLIDE = ("price, type(slider)", "Slider", 4500.0)


def _axes_of(figs):
    out = []
    for f in figs:
        for letter, name in (("y", "default"), ("x", "default")) + tuple(
                ("y", k) for k in f.extra_y_ranges):
            rng = _range(f, letter, name)
            out.append((letter, name, _ticks(f, letter, name),
                        float(rng.start), float(rng.end)))
    return out


def _same_axes(a, b, rel=1e-9):
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if x[:3] != y[:3]:
            return False
        for u, v in zip(x[3:], y[3:]):
            if abs(u - v) > rel * max(abs(u), abs(v), 1.0):
                return False
    return True


class TestAfterAFilterMove:
    @pytest.mark.parametrize("mode", _MODES)
    def test_moves_match_twoway(self, mode):
        """Q01 (range), Q08 (dropdown, y2) and, served, Q06 (a refitted
        lfit): the moved axes are twoway's under the same `if'."""
        rows, bad = _truth()["probes"], []
        cases = [("Q01", _SC, _RANGE), ("Q08", tb.DUAL_Y, _DROP)]
        if mode == "served":
            cases.append(("Q06", _SC + [P("lfit", "mpg", "weight")], _RANGE))
        for pid, plots, (filt, kind, value) in cases:
            figs = _after(mode, _spec(plots, filt=filt), kind, value)
            _compare(pid, rows[pid], figs, bad)
        assert not bad, "\n".join(bad)

    def test_a_stale_fit_stays_in_the_saved_hull(self):
        """D-21e2: the saved page does not refit an lfit after a move; it
        stays drawn, so it stays in the re-finished hull, which equals the
        Python finisher run over the page's own written data."""
        r = _saved(_spec(_SC + [P("lfit", "mpg", "weight")],
                         filt=_RANGE[0]))
        f = _move_saved(r, *_RANGE[1:])[0]
        got = _axes_of([f])
        dr._dash_refinish_axes(r.figures, r._facet_map)
        assert _same_axes(got, _axes_of([f]))
        fit = [x for x in f.renderers if type(x.glyph).__name__ == "Line"][0]
        lo, hi = _inner(f, "y")
        assert lo <= min(fit.data_source.data["y"]) + 1e-9

    @pytest.mark.parametrize("mode", _MODES)
    def test_an_explicit_axis_rehulls_its_data(self, mode):
        figs = _after(mode, _spec(_SC, {"xlabel": "3000"}, filt=_RANGE[0]),
                      *_RANGE[1:])
        df = tb._frame()
        rows = df[(df.price >= 3291) & (df.price <= 7075.5)]
        assert _ticks(figs[0], "x") == [3000.0]
        lo, hi = _inner(figs[0], "x")
        assert lo == pytest.approx(min(rows.weight.min(), 3000.0))
        assert hi == pytest.approx(max(rows.weight.max(), 3000.0))

    def test_saved_equals_served(self):
        """Saved (node) and served agree on every axis after each move,
        where both draw the same layers."""
        bad = []
        for plots, go in ((_SC, {}), (_SC, {"by": "foreign"}),
                          (tb.DUAL_Y, {}), ([P("bar", "mpg", "weight")], {})):
            for filt, kind, value in (_DROP, _RANGE, _SLIDE):
                spec = _spec(plots, go, filt=filt)
                a = _axes_of(_after("saved", spec, kind, value))
                b = _axes_of(_after("served", spec, kind, value))
                if not _same_axes(a, b):
                    bad.append((plots[0]["type"], go, kind, a, b))
        assert not bad, bad


class TestAfterAMoveEdgeCases:
    @pytest.mark.parametrize("mode", _MODES)
    def test_a_move_that_empties_draws_an_empty_scale(self, mode):
        """A move that leaves a layer no rows leaves its axes empty: no
        ticks and the fixed empty extent, written in place (WP-32; BUGS.md
        "Found by the move-parity extension: axes of degenerate or emptied
        layers after a move").  Measured 18oct2026 on test_mode_parity's
        ten rows: `twoway (lfit mpg weight if foreign == 0) if price >=
        10000' (no rows; scatter, bar, kdensity, rarea alike) draws both
        scales empty -- .xscale.curmin 1e300, curmax -1e300 -- with no
        tick."""
        # Flipped: before == after was wrong because twoway draws no tick
        # and an empty scale where the axes held the build's.
        spec = _spec(_SC, filt="price, type(slider)")
        after = _axes_of(_after(mode, spec, "Slider", 1e9))
        lo, hi = dr._DASH_EMPTY_SCALE["linear"]
        assert after and all(a[2] == [] and (a[3], a[4]) == (lo, hi)
                             for a in after), after

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_build_with_no_rows_draws_the_same_empty_scale(self, mode):
        """The page built from no rows draws the form a move leaves, so the
        two agree (test_mode_parity's oracle is the build from the kept
        rows)."""
        f = _figs(mode, _spec(_SC, if_expr="price > 1e9"))[0]
        from bokeh.models import Range1d
        lo, hi = dr._DASH_EMPTY_SCALE["linear"]
        for letter in ("x", "y"):
            rng = _range(f, letter)
            assert isinstance(rng, Range1d), (letter, rng)
            assert (rng.start, rng.end, rng.reset_start, rng.reset_end) \
                == (lo, hi, lo, hi)
            assert _ticks(f, letter) == []

    @pytest.mark.parametrize("mode", _MODES)
    def test_one_row_left(self, mode):
        df = tb._frame()
        top = float(df.price.max())
        f = _after(mode, _spec(_SC, filt="price, type(slider)"), "Slider",
                   top)[0]
        v = float(df.loc[df.price == top, "mpg"].iloc[0])
        assert _ticks(f, "y") == [v - 1.0, v + 1.0]
        assert _inner(f, "y") == pytest.approx((v - 1.0, v + 1.0))

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_reversed_axis_stays_reversed(self, mode):
        f = _after(mode, _spec(_SC, {"yscale": "reverse"}, filt=_RANGE[0]),
                   *_RANGE[1:])[0]
        assert f.y_range.start > f.y_range.end
        assert _ticks(f, "y") == [15.0, 20.0, 25.0, 30.0, 35.0, 40.0]

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_log_axis_with_nothing_positive_is_empty(self, mode):
        # Flipped (WP-32): holding the build's axes was wrong because
        # twoway draws an empty scale with no tick (see above); a log
        # axis takes the empty extent above 0.
        spec = _spec([P("scatter", "price", "weight")], {"yscale": "log"},
                     filt="price, type(slider)")
        f = _after(mode, spec, "Slider", 1e9)[0]
        assert _ticks(f, "y") == []
        assert (f.y_range.start, f.y_range.end) == dr._DASH_EMPTY_SCALE["log"]


class TestResetReturnsToTheCurrentExtent:
    @pytest.mark.parametrize("mode", _MODES)
    def test_reset_follows(self, mode):
        spec = _spec(_SC, filt=_RANGE[0])
        f0 = _figs(mode, spec)[0]
        f1 = _after(mode, spec, *_RANGE[1:])[0]
        for f in (f0, f1):
            for rng in (f.x_range, f.y_range):
                assert (rng.reset_start, rng.reset_end) == (rng.start,
                                                            rng.end)
        assert f1.y_range.start != f0.y_range.start


# ---------------------------------------------------------------------------
def _zoom_cb(rng):
    cbs = (rng.js_property_callbacks or {}).get("change:start", [])
    return [c for c in cbs if dr._DASH_AXIS_ZOOM_JS in c.code][0]


class TestZoomRetick:
    def _y(self, mode):
        spec = _spec(_SC)
        if mode == "saved":
            return _saved(spec).figures["g1"]
        return tb._figs_of(_served(spec).roots)[0]

    @pytest.mark.parametrize("mode", _MODES)
    def test_zoomed_in(self, mode):
        f = self._y(mode)
        rng = f.y_range
        rng.start, rng.end = 20.0, 30.0
        cb = _zoom_cb(rng)
        js_runner.JsSession([cb]).run(cb, cb_obj=rng)
        assert _ticks(f, "y") == dr._dash_natscale_ticks(20.0, 30.0, 5)

    @pytest.mark.parametrize("mode", _MODES)
    def test_home_restores(self, mode):
        f = self._y(mode)
        rng = f.y_range
        cb = _zoom_cb(rng)
        rng.start, rng.end = 20.0, 30.0
        js_runner.JsSession([cb]).run(cb, cb_obj=rng)
        rng.start, rng.end = rng.reset_start, rng.reset_end
        js_runner.JsSession([cb]).run(cb, cb_obj=rng)
        assert _ticks(f, "y") == [10.0, 20.0, 30.0, 40.0]


class TestTheRefinishBudget:
    def test_500k_rows_within_0_2_s(self):
        """A9: the served re-finish adds at most 0.2 s per figure per move
        at 500k rows (the reader alone took 0.561 s at 41d6e10)."""
        from bokeh.models import ColumnDataSource
        from bokeh.plotting import figure
        rnd = np.random.default_rng(1)
        n = 500_000
        fig = figure()
        fig.scatter("x", "y", source=ColumnDataSource(
            {"x": rnd.normal(size=n), "y": rnd.normal(size=n)}))
        fig._dash_margin = {"x": 0.0132, "y": 0.022}
        for ax in (fig.xaxis[0], fig.yaxis[0]):
            ax.ticker = dr._dash_default_ticker(5)
        dr._dash_finish_count_ticks(fig)
        best = 1e9
        for _ in range(3):
            t0 = time.perf_counter()
            dr._dash_refinish_axes({"g": fig}, {})
            best = min(best, time.perf_counter() - t0)
        assert best <= 0.2, best


class TestThePlanCarriesNoUserText:
    @pytest.mark.parametrize("mode", _MODES)
    def test_code_is_constant_and_args_are_data(self, mode):
        from bokeh.models import CustomJS
        spec = _spec(_SC, {"ytitle": '"</script>"'}, filt=_RANGE[0])
        if mode == "saved":
            r = _saved(spec)
            assert all(cb.code == dr._FILTER_JS for cb in r.filter_callbacks)
            figs = list(r.figures.values())
        else:
            figs = tb._figs_of(_served(spec).roots)
        cbs = [c for f in figs for rng in (f.x_range, f.y_range)
               for c in (rng.js_property_callbacks or {}).get(
                   "change:start", []) if isinstance(c, CustomJS)]
        assert cbs and all(c.code == dr._DASH_AXIS_FINISH_JS
                           + dr._DASH_AXIS_ZOOM_JS for c in cbs)
        plan = json.loads(cbs[0].args["plan_json"])
        texts = set()
        for g in plan:
            texts.update(g["share"])
            for p in g["panels"]:
                for a in p["axes"]:
                    texts.update([a["letter"], a["name"], a["key"], a["mode"],
                                  a["kind"] or ""])
                    for L in a["layers"]:
                        texts.update(L["fields"] + [L["fk"]])
        assert not any("<" in t or "script" in t for t in texts)


class TestAVariableNamedProto:
    def test_a_proto_column_is_read(self):
        df = tb._frame().rename(columns={"mpg": "__proto__"})
        from bokeh.models import ColumnDataSource
        from bokeh.plotting import figure
        fig = figure()
        fig.scatter(x="weight", y="__proto__",
                    source=ColumnDataSource(df[["weight", "__proto__"]]))
        fig._dash_margin = {"x": 0.0132, "y": 0.022}
        fig.yaxis[0].ticker = dr._dash_default_ticker(5)
        dr._dash_finish_count_ticks(fig)
        plan_json, models = dr._dash_axis_plan({"g": fig}, {}, zoom=False)
        fig.yaxis[0].ticker.ticks = []
        js_runner.JsSession(models).run_code(
            dr._DASH_AXIS_FINISH_JS
            + "dash_axis_finish(JSON.parse(plan_json), models);",
            {"plan_json": plan_json, "models": models})
        assert list(fig.yaxis[0].ticker.ticks) == [10.0, 20.0, 30.0, 40.0]


# ---------------------------------------------------------------------------
# Guards: green before and after
# ---------------------------------------------------------------------------

class TestTheColourKeyKeepsItsTicker:
    def test_zlabel_count_stays_basic(self):
        from bokeh.models import BasicTicker
        t = dr._dash_count_ticker(5)
        assert isinstance(t, BasicTicker) and t.desired_num_ticks == 5


class TestNoNote:
    @pytest.mark.parametrize("mode", _MODES)
    def test_no_axis_note(self, mode):
        for pid in ("P01", "P03", "P17", "Q02"):
            spec, which = _probe_spec(pid)
            figs, msgs = tb._draw(mode, spec, which)
            assert not [m for m in msgs if "axis" in m.lower()
                        or "tick" in m.lower()], (pid, msgs)


class TestPlotregionMarginIsStillIgnored:
    @pytest.mark.parametrize("mode", _MODES)
    def test_margin_zero_changes_nothing_yet(self, mode):
        """Flipped (WP-30 P1.20b): twoway draws margin(zero) with no
        margin; "the same ranges as no option" was wrong because twoway
        draws plotregion(margin()) (margin_truth.json ZERO)."""
        f = _figs(mode, _spec(_SC, {"plotregion": "margin(zero)"}))[0]
        for letter in ("x", "y"):
            rng = _range(f, letter)
            assert rng._dash_margin_f == (0.0, 0.0)
            assert f._dash_margin[letter] == (0.0, 0.0)
            lo, hi = _inner(f, letter)
            assert (float(rng.start), float(rng.end)) == (lo, hi)
