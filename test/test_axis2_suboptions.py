"""
test_axis2_suboptions.py -- axis(#) on the axis options draws on the axis
it names (WP-29 P0.5, section 10).

twoway's ``axis(#)`` sub-option routes ``ytitle()``, ``ylabel()``,
``ytick()``, ``yline()`` and ``yscale()`` (and the x forms) to the axis it
names (graph_g.class ParseAndLogAxes).  dash applied every one of them to
the first axis and named ``axis(2)`` as not implemented, in both modes:
``ylabel(20 30, axis(2))`` put a FixedTicker [20, 30] on the LEFT axis,
``yline(5000, axis(2))`` drew a Span on the default range, and
``yscale(log axis(2))`` logged the left axis.

The truth is ``test/fixtures/axis2_truth.json``, measured by
``scripts/extract_axis2_truth.do`` from twoway's own ``.Graph`` members on
``sysuse auto``; its ``data`` block is the frame these tests draw.  Every
drawing test runs in both modes: the saved renderer
(``DashRenderer._build_figures``) and the served app (``ServerAppBuilder``,
import, ``make_document``).
"""
import copy
import itertools
import json
import os
import sys
import tempfile
import time
import warnings

import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import make_data_json, load_app  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "axis2_truth.json")
_MODES = ("saved", "served")
_SEQ = itertools.count()
_TMP = tempfile.mkdtemp(prefix="dash_axis2_")


def _truth():
    if not os.path.exists(_FIXTURE):
        pytest.fail("test/fixtures/axis2_truth.json is missing: run "
                    "scripts/extract_axis2_truth.do (WP-29 task 10-01)")
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _frame():
    return pd.DataFrame(_truth()["data"])


#: sysuse auto's own labels, passed explicitly (WP-29 A7).
_LABELS = {"mpg": "Mileage (mpg)", "weight": "Weight (lbs.)",
           "price": "Price", "length": "Length (in.)",
           "foreign": "Car origin"}
_VL = {"origin": {"0": "Domestic", "1": "Foreign"}}
_VLN = {"foreign": "origin"}


def _plot(t, y, x, **opts):
    return {"type": t, "yvar": y, "xvar": x,
            "options": {k: str(v) for k, v in opts.items()}}


#: twoway (scatter mpg weight) (scatter price weight, yaxis(2))
DUAL_Y = [_plot("scatter", "mpg", "weight"),
          _plot("scatter", "price", "weight", yaxis=2)]
#: twoway (scatter mpg weight) (scatter mpg length, xaxis(2))
DUAL_X = [_plot("scatter", "mpg", "weight"),
          _plot("scatter", "mpg", "length", xaxis=2)]
#: twoway scatter price weight, yaxis(2): one axis, on the left
LONE_Y = [_plot("scatter", "price", "weight", yaxis=2)]
ONE = [_plot("scatter", "mpg", "weight")]


def _spec(plots, go=None, filt="", formats=None, graphs=None):
    go = dict(go or {})
    go.setdefault("name", "g1")
    gs = graphs or [{"name": go["name"], "graph_options": go,
                     "options": dict(go), "plots": plots,
                     "if_expr": "", "in_expr": ""}]
    return {"graphs": gs, "kpis": [],
            "build_options": {
                "layout": "auto", "link": "", "filter": filt, "theme": "",
                "scheme": "", "session_scheme": "", "title": "",
                "subtitle": "", "registry": " ".join(g["name"] for g in gs),
                "tabs": "", "filter_position": "top", "level": "95",
                "formats": formats or {}}}


def _write(spec, df=None, labels=None):
    tag = next(_SEQ)
    sp = os.path.join(_TMP, "spec_%d.json" % tag)
    dp = os.path.join(_TMP, "data_%d.json" % tag)
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(make_data_json(_frame() if df is None else df, _VL, _VLN,
                                 _LABELS if labels is None else labels), fh)
    return tag, sp, dp


def _figures_of(models):
    from bokeh.plotting import figure as _Fig
    out, seen = [], set()
    for root in models:
        for m in root.references():
            if isinstance(m, _Fig) and id(m) not in seen:
                seen.add(id(m))
                out.append(m)
    return sorted(out, key=lambda f: str(getattr(f.title, "text", "") or ""))


def _served_doc(spec, df=None, labels=None):
    """(document, build warnings, session warnings) of the served app."""
    from bokeh.document import Document
    tag, sp, dp = _write(spec, df, labels)
    ap = os.path.join(_TMP, "app_%d.py" % tag)
    with warnings.catch_warnings(record=True) as built:
        warnings.simplefilter("always")
        dr.ServerAppBuilder(sp, dp).build(ap)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mod = load_app(ap, "_axis2_app_%d" % tag, draw=False)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        doc = Document()
        mod.make_document(doc)
    return (doc, [str(w.message) for w in built],
            [str(w.message) for w in caught])


def _draw(mode, spec, df=None, labels=None):
    """(figures, warnings) the mode draws for *spec*."""
    if mode == "saved":
        _tag, sp, dp = _write(spec, df, labels)
        dr._dash_reset_notes()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            figs = dr.DashRenderer(sp, dp)._build_figures()
        return (sorted(figs.values(),
                       key=lambda f: str(getattr(f.title, "text", "") or "")),
                [str(w.message) for w in caught])
    doc, built, session = _served_doc(spec, df, labels)
    return _figures_of(doc.roots), built + session


def _one(mode, plots, go=None, **kw):
    figs, caught = _draw(mode, _spec(plots, go, **kw))
    assert len(figs) == 1, figs
    return figs[0], caught


def _cont(side):
    from bokeh.models import ContinuousAxis
    return [a for a in side if isinstance(a, ContinuousAxis)]


def _y2(fig):
    axes = [a for a in _cont(fig.right) if a.y_range_name == "y2"]
    assert len(axes) == 1, fig.right
    return axes[0]


def _x2(fig):
    axes = [a for a in _cont(fig.above) if a.x_range_name == "x2"]
    assert len(axes) == 1, fig.above
    return axes[0]


def _left(fig):
    axes = _cont(fig.left)
    assert len(axes) == 1, fig.left
    return axes[0]


def _bottom(fig):
    axes = _cont(fig.below)
    assert len(axes) == 1, fig.below
    return axes[0]


def _major(ax):
    """The labelled tick positions an axis was given, or None."""
    from bokeh.models import CustomJSTicker, FixedTicker
    t = ax.ticker
    if isinstance(t, CustomJSTicker):
        t = dict(t.args or {}).get("base")
    # A default axis's twoway ticks (WP-30 P1.3a) were not given.
    if isinstance(t, FixedTicker) and "dash_default" not in (t.tags or ()):
        return [float(v) for v in t.ticks]
    return None


def _extra(ax):
    """The tick-only positions (ytick()) an axis was given, or None."""
    from bokeh.models import CustomJSTicker
    t = ax.ticker
    if isinstance(t, CustomJSTicker):
        ex = dict(t.args or {}).get("extra")
        return None if ex is None else sorted(float(v) for v in ex)
    return None


def _spans(fig):
    from bokeh.models import Span
    return [s for s in fig.center if isinstance(s, Span)]


def _span_at(fig, loc):
    got = [s for s in _spans(fig) if abs(float(s.location) - loc) < 1e-9]
    assert len(got) == 1, [(s.location, s.y_range_name, s.x_range_name)
                           for s in _spans(fig)]
    return got[0]


def _no_axis_note(caught):
    bad = [w for w in caught if "axis(" in w or "ax(" in w or "axi(" in w]
    assert bad == [], bad


# ---------------------------------------------------------------------------
@pytest.mark.parametrize("mode", _MODES)
class TestTheSecondAxisOptionsReachTheSecondAxis:
    """Each family's axis(2) form on the second axis (twoway c2-c5, x2-x5)."""

    def test_ylabel_axis2(self, mode):
        fig, caught = _one(mode, DUAL_Y, {"ylabel": "20 30, axis(2)"})
        assert _major(_y2(fig)) == [20.0, 30.0]
        assert _major(_left(fig)) != [20.0, 30.0]
        _no_axis_note(caught)

    def test_yscale_log_axis2(self, mode):
        from bokeh.models import LinearAxis, LogAxis
        fig, caught = _one(mode, DUAL_Y, {"yscale": "log axis(2)"})
        assert isinstance(_y2(fig), LogAxis)
        assert type(_left(fig)) is LinearAxis
        _no_axis_note(caught)

    def test_yline_axis2(self, mode):
        fig, caught = _one(mode, DUAL_Y, {"yline": "5000, axis(2)"})
        assert _span_at(fig, 5000.0).y_range_name == "y2"
        _no_axis_note(caught)

    def test_ytick_axis2(self, mode):
        from bokeh.models import CustomJSTicker
        base, _ = _one(mode, DUAL_Y)
        fig, caught = _one(mode, DUAL_Y, {"ytick": "5000 7500, axis(2)"})
        assert isinstance(_y2(fig).ticker, CustomJSTicker)
        assert _extra(_y2(fig)) == [5000.0, 7500.0]
        assert type(_left(fig).ticker) is type(_left(base).ticker)
        _no_axis_note(caught)

    def test_x_family(self, mode):
        from bokeh.models import LinearAxis, LogAxis
        fig, caught = _one(mode, DUAL_X, {
            "xlabel": "150 200, axis(2)", "xscale": "log axis(2)",
            "xline": "200, axis(2)", "xtick": "160, axis(2)"})
        assert isinstance(_x2(fig), LogAxis)
        assert _major(_x2(fig)) == [150.0, 200.0]
        assert _extra(_x2(fig)) == [160.0]
        assert type(_bottom(fig)) is LinearAxis
        assert _major(_bottom(fig)) != [150.0, 200.0]
        assert _span_at(fig, 200.0).x_range_name == "x2"
        _no_axis_note(caught)

    def test_axis1_and_unqualified_stay_first(self, mode):
        fig, caught = _one(mode, DUAL_Y, {"ylabel": "20 30, axis(1)"})
        assert _major(_left(fig)) == [20.0, 30.0]
        assert _major(_y2(fig)) != [20.0, 30.0]
        _no_axis_note(caught)
        fig, caught = _one(mode, DUAL_Y, {"ylabel": "20 30"})
        assert _major(_left(fig)) == [20.0, 30.0]

    @pytest.mark.parametrize("word", ["ax(2)", "axi(2)", "axis( 2 )",
                                      "axis(02)", "axis(2.0)", "axis(+2)",
                                      "axis(2e0)"])
    def test_axis_spellings(self, mode, word):
        fig, caught = _one(mode, DUAL_Y, {"ylabel": "5000, " + word})
        assert _major(_y2(fig)) == [5000.0]
        assert _major(_left(fig)) != [5000.0]
        _no_axis_note(caught)

    @pytest.mark.parametrize("word", ["axis(2.5)", "axis(a)", "axis()",
                                      "axis(1e300)", "axis(2147483648)"])
    def test_axis_spellings_that_mean_axis_one(self, mode, word):
        fig, caught = _one(mode, DUAL_Y, {"ylabel": "5000, " + word})
        assert _major(_left(fig)) == [5000.0]
        assert _major(_y2(fig)) != [5000.0]
        _no_axis_note(caught)

    def test_ytitle_ax2_titles_the_second_axis(self, mode):
        fig, caught = _one(mode, DUAL_Y, {"ytitle": '"T", ax(2)'})
        assert _y2(fig).axis_label == "T"
        assert _left(fig).axis_label != "T"
        _no_axis_note(caught)

    def test_extents(self, mode):
        def hull(go):
            fig, _ = _one(mode, DUAL_Y, go)
            return fig, dr._dash_range_hull(fig.extra_y_ranges["y2"])

        base, (lo0, hi0) = hull({})
        assert hi0 < 20000
        assert hull({"ytick": "20000, axis(2)"})[1][1] >= 20000 - 1e-6
        assert hull({"ylabel": "20000, axis(2)"})[1][1] >= 20000 - 1e-6
        assert hull({"yline": "30000, axis(2)"})[1][1] < 30000
        assert hull({"ytick": "20000, axis(2) norescale"})[1][1] < 20000
        assert hull({"ylabel": "20000, axis(2) norescale"})[1][1] < 20000
        # A9: the primary range is not touched by a y2 tick position.
        fig, _ = hull({"ytick": "20000, axis(2)"})
        a, b = base.y_range, fig.y_range
        assert type(a) is type(b)
        assert (getattr(a, "start", None), getattr(a, "end", None)) == \
            (getattr(b, "start", None), getattr(b, "end", None))

    def test_merged_line_copies_split(self, mode):
        fig, _ = _one(mode, DUAL_Y, {"yline": "5000, axis(2), 20"})
        assert _span_at(fig, 5000.0).y_range_name == "y2"
        assert _span_at(fig, 20.0).y_range_name == "default"

    def test_lone_second_axis(self, mode):
        from bokeh.models import LogAxis
        fig, caught = _one(mode, LONE_Y, {
            "ylabel": "1000(2000)5000, axis(2)", "yscale": "log axis(2)",
            "ytick": "4000, axis(2)", "yline": "3000, axis(2)"})
        assert _cont(fig.right) == []
        ax = _left(fig)
        assert isinstance(ax, LogAxis)
        assert _major(ax) == [1000.0, 3000.0, 5000.0]
        assert _extra(ax) == [4000.0]
        assert _span_at(fig, 3000.0).y_range_name == "default"
        _no_axis_note(caught)
        # A8: a lone axis joins its line copies.
        fig, _ = _one(mode, LONE_Y, {"yline": "20", "yline2": "3000"})
        assert _span_at(fig, 20.0).y_range_name == "default"
        assert _span_at(fig, 3000.0).y_range_name == "default"

    def test_by_panels(self, mode):
        figs, caught = _draw(mode, _spec(
            DUAL_Y, {"by": "foreign", "ylabel": "5000 10000, axis(2)"}))
        assert len(figs) == 2
        for f in figs:
            assert _major(_y2(f)) == [5000.0, 10000.0]
        _no_axis_note(caught)

    def test_date_primary_axis_line_on_y2(self, mode):
        df = pd.DataFrame({"when": [15340.0 + i for i in range(10)],
                           "mpg": [22.0, 17, 25, 30, 21, 19, 14, 28, 16, 23],
                           "price": [4099.0, 4749, 3799, 4816, 5788, 4453,
                                     5189, 10372, 4082, 11385]})
        spec = _spec([_plot("scatter", "mpg", "when"),
                      _plot("scatter", "price", "when", yaxis=2)],
                     {"yline": "5000, axis(2)"}, formats={"when": "%td"})
        figs, _ = _draw(mode, spec, df=df,
                        labels={"when": "Date", "mpg": "Mileage (mpg)",
                                "price": "Price"})
        span = _span_at(figs[0], 5000.0)
        assert span.y_range_name == "y2"

    def test_add_is_drawn_on_ylabel2(self, mode):
        # Flipped (WP-30 P1.18b): named and not drawn was wrong because
        # twoway draws an axis(2) add (axis_add_truth.json b01): the second
        # axis's default ticks plus the values, with no note.
        from test_by_scales import _major_ticks
        fig, caught = _one(mode, DUAL_Y,
                           {"ylabel": "6000 10000, axis(2) add"})
        assert not [w for w in caught if "add" in w.split(":")[-1].split()]
        assert _major_ticks(_y2(fig)) == [0.0, 5000.0, 6000.0, 10000.0,
                                          15000.0]
        assert _major_ticks(_left(fig)) == [10.0, 20.0, 30.0, 40.0]


# ---------------------------------------------------------------------------
@pytest.mark.parametrize("mode", _MODES)
class TestTheTitleRouteKeepsTheDefault:
    """An unlabelled variable's default title, restyled through the route
    (S03's rule kept; the case lands here, index "Why the dependencies")."""

    @pytest.mark.parametrize("raw", [", size(large) axis(1)",
                                     ", size(large)"])
    def test_unlabelled_title_restyled_through_the_route(self, mode, raw):
        figs, _ = _draw(mode, _spec(ONE, {"ytitle": raw}), labels={})
        ax = _left(figs[0])
        assert ax.axis_label == "mpg"
        # WP-30 P1.12a: twoway's size(large) is 14 pt, drawn as '14pt'
        # (it was the marker size, 15 px).
        want = "14pt"
        assert ax.axis_label_text_font_size == want


# ---------------------------------------------------------------------------
class TestAfterAFilterMove:
    def test_served_move_keeps_routing(self):
        import test_mode_parity as mp
        from bokeh.models import Select
        go = {"ylabel": "5000 10000, axis(2)", "yline": "6000, axis(2)",
              "yscale": "log axis(2)"}
        spec = _spec(DUAL_Y, go, filt="foreign, type(dropdown)")
        doc, _b, _s = _served_doc(spec)

        def profile(fig):
            return (type(_y2(fig)).__name__, _major(_y2(fig)),
                    _span_at(fig, 6000.0).y_range_name,
                    type(_left(fig)).__name__,
                    type(_left(fig).ticker).__name__)

        before = profile(_figures_of(doc.roots)[0])
        assert before == ("LogAxis", [5000.0, 10000.0], "y2", "LinearAxis",
                          before[4])
        w = [x for x in mp._widgets_of(doc) if isinstance(x, Select)][0]
        raw = [v for v, lab in w.options if lab == "Foreign"][0]
        mp._fire(w, raw)
        after = profile(_figures_of(doc.roots)[0])
        assert after == before
        saved, _ = _one("saved", DUAL_Y, go, filt="foreign, type(dropdown)")
        assert profile(saved) == after


# ---------------------------------------------------------------------------
class TestTheRouteUnit:
    def test_route_axis_options_unit(self):
        route = dr._dash_route_axis_options

        def one(go, plots=None):
            spec = _spec(plots or DUAL_Y, go)
            before = copy.deepcopy(spec)
            out = route(spec)
            assert spec == before, "the caller's spec was modified"
            return out["graphs"][0]["graph_options"]

        go = one({"ylabel": "20 30, axis(1)"})
        assert go["ylabel"] == "20 30" and "ylabel2" not in go
        go = one({"ylabel": "5000, axis(2)"})
        assert go["ylabel2"] == "5000" and "ylabel" not in go
        go = one({"ylabel": "5000, axis(2) angle(0)"})
        assert go["ylabel2"] == "5000, angle(0)"
        go = one({"ytick": "5000 7500, axis(2)"})
        assert go["ytick2"] == "5000 7500" and "ytick" not in go
        go = one({"yscale": "log axis(2)"})
        assert go["yscale2"] == "log" and "yscale" not in go
        go = one({"xscale": "log ax(2)", "xlabel": "1, axi(2)"})
        assert go["xscale2"] == "log" and go["xlabel2"] == "1"
        go = one({"yline": "5000, axis(2), 20"})
        assert go["yline2"] == "5000" and go["yline"] == "20"
        go = one({"yline": "5000, axis(2) lcolor(red), 20, 30, axis(2)"})
        assert go["yline2"] == "5000, lcolor(red), 30"
        assert go["yline"] == "20"
        go = one({"yline": "5000, axis(2)", "yline2": "7000"})
        assert go["yline2"] == "7000, 5000"
        # axis(3) is kept for the refusal (dash.ado) to name
        go = one({"ylabel": "5000, axis(3)"})
        assert go["ylabel"] == "5000, axis(3)" and "ylabel2" not in go
        # an explicit ylabel2() wins, with one note
        dr._dash_reset_notes()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            go = one({"ylabel": "5000, axis(2)", "ylabel2": "6000"})
        assert go["ylabel2"] == "6000" and "ylabel" not in go
        notes = [str(w.message) for w in caught]
        assert notes == ["dash: ylabel(..., axis(2)) and ylabel2() both "
                         "given; ylabel2() is drawn"], notes
        # a quoted "axis(2)" and an upper-case AXIS(2) are left as typed
        for raw in ('5000 "axis(2)"', "5000, AXIS(2)",
                    "5000, axis(2) axis(1)"):
            go = one({"ylabel": raw})
            assert go["ylabel"] == raw and "ylabel2" not in go
        # malformed specs pass through
        for bad in (None, 42, {}, {"graphs": "x"},
                    {"graphs": [1, {"graph_options": "x"}]}):
            assert route(bad) is bad or route(bad) == bad
        # linear: 2,000 graphs
        big = _spec(None, graphs=[
            {"name": "g%d" % i, "plots": DUAL_Y,
             "graph_options": {"name": "g%d" % i,
                               "ylabel": "5000, axis(2)",
                               "yline": "1, axis(2), 2",
                               "yscale": "log axis(2)"}}
            for i in range(2000)])
        t0 = time.perf_counter()
        out = route(big)
        assert time.perf_counter() - t0 < 2.0
        assert out["graphs"][-1]["graph_options"]["ylabel2"] == "5000"

    def test_axis_word_unit(self):
        w = dr._dash_axis_word
        assert w("axis(2)") == (True, True, "2")
        assert w("ax( 2 )") == (True, True, " 2 ")
        assert w("axi(3)") == (True, True, "3")
        assert w("AXIS(2)") == (True, False, "2")
        assert w("Ax(2)") == (True, False, "2")
        for no in ("a(2)", "axes(2)", "axis", "angle(0)", "lcolor(red)"):
            assert w(no)[0] is False, no
        ws = dr._dash_axis_words
        assert ws(["angle(0)", "axis(2)"]) == (2, 1)
        assert ws(["angle(0)"]) == (1, None)
        assert ws(["axis(2.5)"]) == (1, 0)
        assert ws(["axis(2)", "axis(1)"]) == (None, None)
        assert ws(["AXIS(2)"]) == (None, None)
        assert ws(["axis(3)"]) == (3, 0)

    def test_route_line_copies_unit(self):
        c = dr._dash_route_line_copies
        assert c("5000, axis(2), 20") == ("20", "5000", True)
        assert c("20 25, lcolor(red)") == ("20 25, lcolor(red)", "", False)
        assert c("5000, axis(2) lcolor(red), 20, 30, axis(2)") == (
            "20", "5000, lcolor(red), 30", True)
        assert c("5000, axis(1)") == ("5000", "", True)
        # axis(3), and an axis word in capitals, stay as typed on axis 1
        assert c("5000, axis(3)") == ("5000, axis(3)", "", False)
        assert c("5000, AXIS(2)") == ("5000, AXIS(2)", "", False)

    @pytest.mark.parametrize("arg,want", [
        ("2", 2), ("02", 2), ("2.0", 2), (" 2 ", 2), ("+2", 2), ("2e0", 2),
        ("1", 1), ("a", 1), ("", 1), ("2.5", 1), ("1.5", 1), ("2 1", 1),
        ("#2", 1), (".", 1), ("1e300", 1), ("2147483648", 1),
        ("-2147483649", 1), ("-9999999999", 1), ("inf", 1), ("nan", 1),
        ("1_0", 1), ("1.0x+1", 1), ("2147483647", 2147483647),
        ("-2147483648", -2147483648), ("1e9", 1000000000), ("-0", 0),
        ("1e1", 10), ("3", 3), (None, 1)])
    def test_axis_number_unit(self, arg, want):
        got = dr._dash_axis_number(arg)
        assert got == want and isinstance(got, int)


# ---------------------------------------------------------------------------
_ORPHAN = ("dash: graph 'g1': ylabel2() (ylabel(..., axis(2))) is not "
           "drawn: no layer is on yaxis(2).")


class TestUnusedSecondAxisOptionsAreNamed:
    @pytest.mark.parametrize("mode", _MODES)
    def test_orphan_note(self, mode):
        figs, caught = _draw(mode, _spec(ONE, {"ylabel2": "5"}))
        assert caught.count(_ORPHAN) == 1, caught
        figs, caught = _draw(mode, _spec(ONE, {"ylabel": "20 30, axis(2)"}))
        assert _major(_left(figs[0])) != [20.0, 30.0]
        assert caught.count(_ORPHAN) == 1, caught

    def test_served_note_is_raised_at_build_time(self):
        _doc, built, session = _served_doc(_spec(ONE, {"ylabel2": "5"}))
        assert _ORPHAN in built
        assert (built + session).count(_ORPHAN) == 1


# ---------------------------------------------------------------------------
#: rc-0 probes of axis2_truth.json dash can draw: id -> (plots, the graph
#: options as dash stores them, family).  The stored form is what dash.ado
#: writes after its route (repeats already split per axis).
_DRAWN = {
    "c2": (DUAL_Y, {"ylabel": "5000 10000 15000, axis(2)"}, "label"),
    "c3": (DUAL_Y, {"yscale": "log axis(2)"}, "scale"),
    "c4": (DUAL_Y, {"yline": "5000, axis(2)"}, "line"),
    "c5": (DUAL_Y, {"ytick": "5000 7500, axis(2)"}, "tick"),
    "c8": (DUAL_Y, {"ylabel": "10 20", "ylabel2": "5000 10000"}, "label"),
    "c10": (DUAL_Y, {"ylabel2": "6000"}, "label"),
    "c11": (DUAL_Y, {"yline": "5000 10000, axis(2), 20"}, "line"),
    "c12": (DUAL_Y, {"yscale": "reverse", "yscale2": "log"}, "scale"),
    "c13": (DUAL_Y, {"ylabel": "20000, axis(2)"}, "label"),
    "c14": (DUAL_Y, {"ytick": "20000, axis(2)"}, "tick"),
    "c15": (DUAL_Y, {"yline": "30000, axis(2)"}, "line"),
    "c17": (DUAL_Y, {"ylabel": "5000, ax(2)"}, "label"),
    "c18": (DUAL_Y, {"ylabel": "5000, axi(2)"}, "label"),
    "c19": (DUAL_Y, {"ytick": "5000, ax(2)"}, "tick"),
    "c20": (DUAL_Y, {"yline": "5000, ax(2)"}, "line"),
    "c21": (DUAL_Y, {"yscale": "log ax(2)"}, "scale"),
    "c25": (DUAL_Y, {"ylabel": "5000, axis( 2 )"}, "label"),
    "c26": (DUAL_Y, {"ylabel": "5000, axis(02)"}, "label"),
    "c27": (DUAL_Y, {"ylabel": "5000, axis(2.0)"}, "label"),
    "c28": (DUAL_Y, {"ylabel": "5000, axis(+2)"}, "label"),
    "c29": (DUAL_Y, {"ylabel": "5000, axis(2e0)"}, "label"),
    "c31": (DUAL_Y, {"ylabel": "5000, axis(2.5)"}, "label"),
    "c32": (DUAL_Y, {"ylabel": "5000, axis(a)"}, "label"),
    "c34": (DUAL_Y, {"ylabel": "5000, axis()"}, "label"),
    "c35": (DUAL_Y, {"ylabel": "5000, axis(1.5)"}, "label"),
    "c37": (DUAL_Y, {"ylabel": "5000, axis(#2)"}, "label"),
    "c38": (DUAL_Y, {"ylabel": "5000, axis(.)"}, "label"),
    "c39": (DUAL_Y, {"ylabel": "5000, axis(1e300)"}, "label"),
    "c40": (DUAL_Y, {"ylabel": "5000, axis(2147483648)"}, "label"),
    "c41": (DUAL_Y, {"ylabel": "5000, axis(-2147483649)"}, "label"),
    "c42": (DUAL_Y, {"ylabel": "5000, axis(-9999999999)"}, "label"),
    "c49": (DUAL_Y, {"ytick": "5000, axis(2),"}, "tick"),
    "c54": (DUAL_Y, {"ylabel": "5000, axis(1)"}, "label"),
    "x2": (DUAL_X, {"xlabel": "150 200, axis(2)"}, "label"),
    "x3": (DUAL_X, {"xscale": "log axis(2)"}, "scale"),
    "x4": (DUAL_X, {"xline": "200, axis(2)"}, "line"),
    "x5": (DUAL_X, {"xtick": "160 180, axis(2)"}, "tick"),
    "x10": (DUAL_X, {"xlabel": "2000 3000", "xlabel2": "150 200"}, "label"),
    "x12": (DUAL_X, {"xline": "200, axis(2), 3000"}, "line"),
}


def _twoway_axis_of(probe, family, d):
    """{index: values} of what twoway drew for *family* on side *d*."""
    out = {}
    if family in ("label", "tick"):
        st = "major" if family == "label" else "majornl"
        for k in (1, 2):
            v = probe["axes"].get("%saxis%d" % (d, k), {}).get(st)
            if v:
                out[k] = sorted(v)
    elif family == "scale":
        for pr in probe["plotregions"]:
            if pr[d]["transform"] == "log":
                out[int(pr["%saxis_dexes" % d][0])] = ["log"]
    else:
        for pr in probe["plotregions"]:
            zs = sorted(l["z"] for l in pr["lines"] if l["orientation"] == d)
            if zs:
                k = int(pr["%saxis_dexes" % d][0])
                out[k] = sorted(out.get(k, []) + zs)
    return out


def _dash_axis_of(fig, family, d):
    from bokeh.models import LogAxis
    first = _left(fig) if d == "y" else _bottom(fig)
    second = _y2(fig) if d == "y" else _x2(fig)
    out = {}
    for k, ax in ((1, first), (2, second)):
        if family == "label":
            v = _major(ax)
            # only an explicit list is compared (a default ticker is None)
            if v:
                out[k] = sorted(v)
        elif family == "tick":
            v = _extra(ax)
            if v:
                out[k] = v
        elif family == "scale":
            if isinstance(ax, LogAxis):
                out[k] = ["log"]
    if family == "line":
        attr = "y_range_name" if d == "y" else "x_range_name"
        dim = "width" if d == "y" else "height"
        for s in _spans(fig):
            if s.dimension != dim:
                continue
            k = 2 if getattr(s, attr) in ("y2", "x2") else 1
            out[k] = sorted(out.get(k, []) + [float(s.location)])
    return out


#: The lists the label probes ask for (one per axis they label).
_ASKED = {
    "c2": [[5000, 10000, 15000]], "c8": [[10, 20], [5000, 10000]],
    "c10": [[6000]], "c13": [[20000]], "x2": [[150, 200]],
    "x10": [[2000, 3000], [150, 200]],
    **{k: [[5000]] for k in ("c17", "c18", "c25", "c26", "c27", "c28",
                             "c29", "c31", "c32", "c34", "c35", "c37",
                             "c38", "c39", "c40", "c41", "c42", "c54")},
}


class TestTheFixtureIsPinned:
    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("pid", sorted(_DRAWN))
    def test_dash_draws_on_twoways_axis(self, mode, pid):
        probes = {p["id"]: p for p in _truth()["probes"]}
        probe = probes[pid]
        assert probe["rc"] == 0, probe
        plots, go, family = _DRAWN[pid]
        d = "x" if plots is DUAL_X else "y"
        want = _twoway_axis_of(probe, family, d)
        if family == "label":
            # twoway puts its default ticks on every axis; the axis the
            # option named is the one holding exactly the asked-for list.
            asked = [sorted(float(v) for v in a) for a in _ASKED[pid]]
            want = {k: v for k, v in want.items() if v in asked}
            assert len(want) == len(asked), (pid, want)
        fig, _ = _one(mode, plots, go)
        got = _dash_axis_of(fig, family, d)
        assert got == want, (pid, probe["command"], got, want)

    def test_meta_stamp(self):
        meta = _truth()["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted"):
            assert str(meta.get(k, "")).strip(), k

    def test_the_refusals_are_recorded(self):
        probes = {p["id"]: p for p in _truth()["probes"]}
        assert probes["c33"]["rc"] == 198
        assert probes["c33"]["error"] == (
            "ylabels(5000 10000) not allowed, yaxis1 does not exist")
        assert probes["x203"]["error"] == (
            "ylabels(5000, axis(1e9)) not allowed, yaxis1000000000 does "
            "not exist")
        assert probes["r1"]["rc"] == 1003
