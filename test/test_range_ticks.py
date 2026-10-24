"""WP-34 section 34-03 (AX-1): range() widens a default axis, not its ticks.

GAPS4 AX-1.  On an axis with no label rule twoway's ``range()`` widens
only the scale; the ticks stay natscale over the data.  Measured at
e501552 (test/fixtures/range_ticks_truth.json, written by
scripts/extract_range_ticks_truth.do): ``scatter mpg weight,
yscale(range(0))`` labels 10 20 30 40 over 0-41 where dash drew
0(10)40; ``yscale(range(100))`` 10(10)40 where dash drew 20(20)100;
``xscale(range(0 6000))`` 2000(1000)5000 where dash drew 0(2000)6000.
Under ``#N`` (R5) and in a by() graph (R6) twoway ticks the data and the
range together, as dash did.

Every expectation is twoway's own: one test per mode loops over every
probe and reports every mismatch.

While iterating: ``python3 -m pytest test/test_range_ticks.py -q -n0``.
"""
import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_default_axes as da  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "range_ticks_truth.json")
_AXIS_TRUTH = os.path.join(_HERE, "fixtures", "axis_truth.json")
_MODES = ("saved", "served")
P = da.P
_SC = [P("scatter", "mpg", "weight")]
_Y2 = _SC + [P("scatter", "price", "weight", yaxis=2)]

#: probe id -> (plots, graph options): the fixture's twoway commands.
_PROBES = {
    "R1": (_SC, {"yscale": "range(0)"}),
    "R2": (_SC, {"yscale": "range(100)"}),
    "R3": (_SC, {"xscale": "range(0 6000)"}),
    "R4": (_SC, {"xscale": "range(1000 6100)"}),
    "R5": (_SC, {"ylabel": "#5", "yscale": "range(100)"}),
    "R6": (_SC, {"by": "foreign", "yscale": "range(0)"}),
    "R7": (_SC, {"yscale": "log range(5)"}),
    "R8": ([P("bar", "mpg", "weight")], {"yscale": "range(0)"}),
    "R9": (_SC + [P("lfit", "mpg", "weight")], {"yscale": "range(0)"}),
    "R10": (_Y2, {"yscale": "range(0) axis(2)"}),
    "R11": (_SC, {"ylabel": ", angle(0)", "yscale": "range(0)"}),
    "R12": (_Y2, {"yscale": "range(20000) axis(2)"}),
}
#: twoway's axis name -> (letter, which range).
_AXES = {"x1": ("x", "default"), "y1": ("y", "default"), "y2": ("y", 2)}


def _truth():
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _name(f, which):
    if which == "default":
        return "default"
    names = sorted(f.extra_y_ranges)
    return names[0] if len(names) == 1 else None


def _compare(pid, axes, f, bad, tag=""):
    """Append to *bad* every axis of figure *f* whose ticks or inner scale
    differ from twoway's *axes* (``{"y1": {"ticks": [...], "cur": [lo,
    hi]}}``)."""
    for ax, rec in sorted(axes.items()):
        letter, which = _AXES[ax]
        name = _name(f, which)
        if name is None:
            bad.append("%s%s %s: no second axis" % (pid, tag, ax))
            continue
        got = da._ticks(f, letter, name)
        want = sorted(rec["ticks"])
        if got is None or [round(v, 9) for v in got] != want:
            bad.append("%s%s %s: ticks %s, twoway %s"
                       % (pid, tag, ax, got, want))
        lo, hi = da._inner(f, letter, name)
        span = rec["cur"][1] - rec["cur"][0]
        if not (da._near(lo, rec["cur"][0], span)
                and da._near(hi, rec["cur"][1], span)):
            bad.append("%s%s %s: scale %s, twoway %s"
                       % (pid, tag, ax, [lo, hi], rec["cur"]))


class TestTheFixture:
    def test_the_meta_stamp_and_the_probes(self):
        t = _truth()
        assert {"stata_version", "born_date", "dash_commit", "extracted",
                "source"} <= set(t["_meta"])
        assert set(_PROBES) | {"R13"} == set(t["probes"])
        assert all(p["rc"] == 0 for p in t["probes"].values())


class TestAgainstStata:
    @pytest.mark.parametrize("mode", _MODES)
    def test_probes(self, mode):
        """R1-R4, R8, R9, R11, R12: ticks over the data, range() in the
        span; R5 (#5), R6 (by()), R7 (log, range below the data) and R10
        (axis 2's data ticks already reach 0) are guards."""
        probes, bad = _truth()["probes"], []
        for pid, (plots, go) in sorted(_PROBES.items()):
            figs = da._figs(mode, da._spec(plots, go))
            row = probes[pid]
            if "panels" in row:
                if len(figs) != len(row["panels"]):
                    bad.append("%s: %d panels, twoway %d"
                               % (pid, len(figs), len(row["panels"])))
                for k, (f, axes) in enumerate(zip(figs, row["panels"])):
                    _compare(pid, axes, f, bad, " panel %d" % (k + 1))
            else:
                _compare(pid, row["axes"], figs[0], bad)
        assert not bad, "\n".join(bad)


#: axis_truth.json b2_extent rows with a range() and a drawn numeric axis
#: -> (plots, graph options, letter).
_B2 = {
    "b2_range_0": (_SC, {"yscale": "range(0)"}, "y"),
    "b2_range_100": (_SC, {"yscale": "range(100)"}, "y"),
    "b2_range_20_30": (_SC, {"yscale": "range(20 30)"}, "y"),
    "b2_r_0_100": (_SC, {"yscale": "r(0 100)"}, "y"),
    "b2_range_dot_60": (_SC, {"yscale": "range(. 60)"}, "y"),
    "b2_range_60_dot": (_SC, {"yscale": "range(60 .)"}, "y"),
    "b2_range_unsorted": (_SC, {"yscale": "range(100 0)"}, "y"),
    "b2_range_three": (_SC, {"yscale": "range(0 50 100)"}, "y"),
    "b2_log_range": ([P("scatter", "price", "weight")],
                     {"yscale": "log range(1000 20000)"}, "y"),
    "b2_log_r_one": ([P("scatter", "price", "weight")],
                     {"yscale": "log r(100000)"}, "y"),
    "b2_rev_range": (_SC, {"yscale": "reverse range(0 50)"}, "y"),
    "b2_hash5_range100": (_SC, {"ylabel": "#5", "yscale": "range(100)"},
                          "y"),
    "b2_lfit_range0": (_SC + [P("lfit", "mpg", "weight")],
                       {"yscale": "range(0)"}, "y"),
    "b2_bar_xrange0": ([P("bar", "mpg", "weight")],
                       {"xscale": "range(0)"}, "x"),
}


class TestTheAxisTruthRows:
    @pytest.mark.parametrize("mode", _MODES)
    def test_b2_rows(self, mode):
        """Each row's numbers twoway labels (its SVG's tick labels,
        ``drawn_ticks``) are the ticks dash places."""
        with open(_AXIS_TRUTH, encoding="utf-8") as fh:
            rows = json.load(fh)["probes"]
        bad = []
        for pid, (plots, go, letter) in sorted(_B2.items()):
            want = sorted(rows[pid]["drawn_ticks"][letter])
            f = da._figs(mode, da._spec(plots, go))[0]
            got = da._ticks(f, letter)
            if got is None or [round(v, 9) for v in got] != want:
                bad.append("%s: ticks %s, twoway %s" % (pid, got, want))
        assert not bad, "\n".join(bad)


class TestAfterAMove:
    """R1 under the price range filter at 3291-7075.5 (R13, twoway's
    `if' over the same rows): the ticks are placed over the kept data
    and the span keeps 0."""

    @pytest.mark.parametrize("mode", _MODES)
    def test_after_a_range_move(self, mode):
        filt, kind, value = da._RANGE
        spec = da._spec(_SC, {"yscale": "range(0)"}, filt=filt)
        figs = da._after(mode, spec, kind, value)
        bad = []
        _compare("R13", _truth()["probes"]["R13"]["axes"], figs[0], bad)
        assert not bad, "\n".join(bad)

    def test_saved_equals_served(self):
        filt, kind, value = da._RANGE
        for go in ({"yscale": "range(0)"}, {"yscale": "range(100)"},
                   {"ylabel": "#5", "yscale": "range(100)"},
                   {"by": "foreign", "yscale": "range(0)"}):
            spec = da._spec(_SC, go, filt=filt)
            a = da._axes_of(da._after("saved", spec, kind, value))
            b = da._axes_of(da._after("served", spec, kind, value))
            assert da._same_axes(a, b), (go, a, b)


class TestTheStamp:
    @pytest.mark.parametrize("mode", _MODES)
    def test_both_modes(self, mode):
        """``fig._dash_by_graph`` is True on every panel of a by() graph
        and False without by(), in both modes."""
        for go, want in (({"by": "foreign"}, True), ({}, False),
                         ({"by": ""}, False)):
            figs = da._figs(mode, da._spec(_SC, dict(go, yscale="range(0)")))
            got = [getattr(f, "_dash_by_graph", None) for f in figs]
            assert got == [want] * len(figs), (go, got)

    def test_the_plan_carries_byg(self):
        for go, want in (({"by": "foreign"}, True), ({}, False)):
            r = da._saved(da._spec(_SC, go))
            plan, _models = dr._dash_axis_plan(r.figures, r._facet_map,
                                               zoom=False)
            got = {a["byg"] for grp in json.loads(plan)
                   for p in grp["panels"] for a in p["axes"]}
            assert got == {want}, (go, got)


class TestTheHelp:
    def test_the_range_sentence(self):
        """dash.sthlp states the rule (HR-10's range part) and no longer
        says range() widens the ticks."""
        import test_help_claims_1 as hc
        text = " ".join(hc._between(
            hc._help(), "An axis whose drawn range is not its variables'",
            "{marker").split())
        assert "a {cmd:range()} that widens the ticks" not in text
        assert ("On an axis with no rule, {cmd:range()} widens the axis but "
                "not its ticks, as in {cmd:twoway}: {cmd:yscale(range(0))} "
                "on {cmd:mpg} labels 10 20 30 40 over an axis from 0; with "
                "{cmd:#}{it:N}, or in a {cmd:by()} graph, the ticks are "
                "placed over the data and the range together.") in text
