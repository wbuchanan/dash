"""
test_by_scales.py -- a by() graph's panels share one scale per axis, and
yrescale, xrescale and rescale give each panel its own (WP-29 P0.2,
section 10).

twoway draws every panel of a by() graph on ONE scale per axis -- x, y and
the second axes, the Total panel's too -- the union of what every panel
draws (bygraph_g.class axis_allrange); ``yrescale``, ``xrescale`` and
``rescale`` (their abbreviations and ``style(rescale|combine)``) give each
panel its own scale on that axis, and range() on a rescaled axis is not
applied.  dash drew every panel on its own autorange and named the
rescale sub-options as not implemented, in both modes.

The truth is ``test/fixtures/by_scales_truth.json``, measured by
``scripts/extract_by_scales_truth.do`` from twoway's ``.Graph.graphs[k]``
members; its ``data`` block is the frame these tests draw.  ``_served_doc``
is the one place a served document is built here.
"""
import copy
import itertools
import json
import os
import sys
import tempfile
import time
import types
import warnings

import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import make_data_json, load_app  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "by_scales_truth.json")
_NATSCALE = os.path.join(_HERE, "fixtures", "natscale_axes_truth.json")
_MODES = ("saved", "served")
_SEQ = itertools.count()
_TMP = tempfile.mkdtemp(prefix="dash_by_scales_")
_LABELS = {"mpg": "Mileage (mpg)", "weight": "Weight (lbs.)",
           "price": "Price", "turn": "Turn circle", "rep78": "Repair",
           "foreign": "Car origin", "length": "Length (in.)",
           "y": "y", "t": "t", "g": "g"}


def _truth():
    if not os.path.exists(_FIXTURE):
        pytest.fail("test/fixtures/by_scales_truth.json is missing: run "
                    "scripts/extract_by_scales_truth.do (WP-29 task 10-14)")
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _probe(pid):
    return {p["id"]: p for p in _truth()["probes"]}[pid]


def _frame(which="auto"):
    d = _truth()["data"]
    return pd.DataFrame(d[which])


def _plot(t, y=None, x=None, **opts):
    p = {"type": t, "options": {k: str(v) for k, v in opts.items()}}
    if t in ("histogram", "kdensity"):
        p["var"] = y
    elif t == "rarea":
        p.update({"yvar1": y[0], "yvar2": y[1], "xvar": x})
    else:
        p.update({"yvar": y, "xvar": x})
    return p


SC = [_plot("scatter", "mpg", "weight")]
DUAL_Y = [_plot("scatter", "mpg", "weight"),
          _plot("scatter", "price", "weight", yaxis=2)]
DUAL_X = [_plot("scatter", "mpg", "weight"),
          _plot("scatter", "mpg", "length", xaxis=2)]


def _graph(name, plots, go=None, if_expr=""):
    go = dict(go or {})
    go["name"] = name
    return {"name": name, "graph_options": go, "options": dict(go),
            "plots": plots, "if_expr": if_expr, "in_expr": ""}


def _spec(plots=None, go=None, graphs=None, filt="", link="", tabs="",
          formats=None, if_expr=""):
    gs = graphs or [_graph("g1", plots, go, if_expr)]
    return {"graphs": gs, "kpis": [],
            "build_options": {
                "layout": "auto", "link": link, "filter": filt, "theme": "",
                "scheme": "", "session_scheme": "", "title": "",
                "subtitle": "", "registry": " ".join(g["name"] for g in gs),
                "tabs": tabs, "filter_position": "top", "level": "95",
                "formats": formats or {}}}


def _write(spec, which="auto"):
    tag = next(_SEQ)
    sp = os.path.join(_TMP, "spec_%d.json" % tag)
    dp = os.path.join(_TMP, "data_%d.json" % tag)
    d = _truth()["data"]
    vl = d["auto_value_labels"] if which == "auto" else {}
    vln = d["auto_value_label_names"] if which == "auto" else {}
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(make_data_json(_frame(which), vl, vln, _LABELS), fh)
    return tag, sp, dp


def _served_doc(spec, which="auto"):
    """(document, build warnings, session warnings) of the served app --
    the one place this file builds one (S13 may adjust it)."""
    from bokeh.document import Document
    tag, sp, dp = _write(spec, which)
    ap = os.path.join(_TMP, "app_%d.py" % tag)
    with warnings.catch_warnings(record=True) as built:
        warnings.simplefilter("always")
        dr.ServerAppBuilder(sp, dp).build(ap)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mod = load_app(ap, "_bsc_app_%d" % tag)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        doc = Document()
        mod.make_document(doc)
    return (doc, [str(w.message) for w in built],
            [str(w.message) for w in caught])


def _figs_of(models):
    from bokeh.plotting import figure as _Fig
    out, seen = [], set()
    for root in models:
        for m in root.references():
            if isinstance(m, _Fig) and id(m) not in seen:
                seen.add(id(m))
                out.append(m)
    return out


def _title(f):
    return str(getattr(f.title, "text", "") or "")


def _draw(mode, spec, which="auto"):
    """({panel title: figure}, warnings) as the mode draws *spec*."""
    if mode == "saved":
        _tag, sp, dp = _write(spec, which)
        dr._dash_reset_notes()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            figs = list(dr.DashRenderer(sp, dp)._build_figures().values())
        msgs = [str(w.message) for w in caught]
    else:
        doc, built, session = _served_doc(spec, which)
        figs, msgs = _figs_of(doc.roots), built + session
    return figs, msgs


def _panels(figs):
    return sorted(figs, key=_title)


def _emulated_hull(figs, letter):
    """What BokehJS spans on *letter* for the panels *figs* that share (or
    each own) a DataRange1d: the finite values of every listed renderer
    (or, with an empty list, every first-axis non-swatch renderer of those
    panels), through each renderer's view."""
    attr = letter + "_range"
    rname = letter + "_range_name"
    pool, seen = [], set()
    for f in figs:
        rng = getattr(f, attr)
        lst = list(rng.renderers) if isinstance(rng.renderers, list) else []
        if not lst:
            lst = [r for r in f.renderers
                   if getattr(r, rname, "default") == "default"
                   and not dr._dash_is_swatch(r)]
        for r in lst:
            if id(r) not in seen:
                seen.add(id(r))
                pool.append(r)
    _, vals = dr._dash_secondary_values(
        types.SimpleNamespace(renderers=pool), rname, "default")
    return (min(vals), max(vals)) if vals else None


def _close(a, b, tol=1e-6):
    return a is not None and b is not None and \
        all(abs(float(x) - float(y)) <= tol * max(1.0, abs(float(y)))
            for x, y in zip(a, b))


def _one_object(figs, letter):
    return len({id(getattr(f, letter + "_range")) for f in figs}) == 1


def _fixture_span(pid, panel, letter):
    p = _probe(pid)["panels"][panel][letter]
    return (p["min"], p["max"])


def _major_ticks(ax):
    from bokeh.models import CustomJSTicker, FixedTicker
    t = ax.ticker
    if isinstance(t, CustomJSTicker):
        t = dict(t.args or {}).get("base")
    return sorted(float(v) for v in t.ticks) if isinstance(t, FixedTicker) \
        else None


def _left(f):
    from bokeh.models import ContinuousAxis
    return [a for a in f.left if isinstance(a, ContinuousAxis)][0]


def _bottom(f):
    from bokeh.models import ContinuousAxis
    return [a for a in f.below if isinstance(a, ContinuousAxis)][0]


def _steps(lo, hi, d):
    out, v = [], float(lo)
    while v <= float(hi) + 1e-9:
        out.append(v)
        v += float(d)
    return out


# ---------------------------------------------------------------------------
_RULE = {
    frozenset(): ["", "norescale", "nor", "noyrescale", "r(1)",
                  "style(compact)", "style(resc)", "style(rescale) nor"],
    frozenset("xy"): ["rescale", "r", "re", "resc", "rescal",
                      "rescale noyrescale", "res noyr", "style(rescale)",
                      "style(combine)", "compact style(rescale)"],
    frozenset("y"): ["yrescale", "yr", "yresc", "yrescal",
                     "yrescale noyrescale", "yrescale norescale",
                     "norescale yrescale", "nor yr", "style(compact) yrescale",
                     "compact yrescale", "rows(1) yrescale", "total yrescale"],
    frozenset("x"): ["xrescale", "xr", "xresc",
                     "style(rescale) noyrescale"],
}
_SPELLINGS = [(s, w) for w, ss in _RULE.items() for s in ss]


class TestTheRescaleSubOptions:
    @pytest.mark.parametrize("spelling,want", _SPELLINGS,
                             ids=[s or "(none)" for s, _ in _SPELLINGS])
    def test_the_rescaled_axes_match_twoway(self, spelling, want):
        got = dr._dash_by_rescale("foreign, " + spelling)
        assert got == want
        truth = _truth()["rescale_rule"][spelling]
        assert got == frozenset(truth), (spelling, sorted(got), truth)

    @pytest.mark.parametrize("by_raw,named", [
        ("foreign, yrescale", []), ("foreign, xr", []), ("foreign, r", []),
        ("foreign, norescale", []), ("foreign, noyrescale", []),
        ("foreign, rows(2) yrescale", ["rows(2)"]),
        ("foreign, r(1)", ["r(1)"]), ("foreign, rescale(1)", ["rescale(1)"])])
    def test_rescale_tokens_are_not_named(self, by_raw, named):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            out = dr._dash_parse_by(by_raw)
        assert out[4] == named
        lines = [str(w.message) for w in caught
                 if "by() sub-option(s) not implemented" in str(w.message)]
        if named:
            assert lines == ["dash: by() sub-option(s) not implemented and "
                             "ignored: " + " ".join(named)]
        else:
            assert lines == []

    def test_style_rescale_is_named_with_its_own_note(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            out = dr._dash_parse_by("foreign, style(rescale)")
        assert out[4] == []
        assert [str(w.message) for w in caught] == [
            "dash: by() sub-option style(rescale): only its separate scales "
            "are drawn; the rest of the style is not implemented."]
        assert dr._dash_parse_by("foreign, style(compact)",
                                 warn=False)[4] == ["style(compact)"]

    def test_hostile_by_text_never_raises(self):
        big = "foreign, " + " ".join(["yrescale"] * 100000)
        t0 = time.perf_counter()
        assert dr._dash_by_rescale(big) == frozenset("y")
        assert time.perf_counter() - t0 < 1.0
        for bad in ('foreign, title("yrescale")', 'foreign, "unbalanced',
                    "foreign, ((((", "foreign, yrescale(", None, 42, b"x",
                    "", ",", 'foreign, title(`"a "b" c"\') xr'):
            got = dr._dash_by_rescale(bad)
            assert isinstance(got, frozenset), bad
        assert dr._dash_by_rescale('foreign, title("yrescale")') == frozenset()


# ---------------------------------------------------------------------------
@pytest.mark.parametrize("mode", _MODES)
class TestPanelsShareOneScale:
    def test_default_shares_x_and_y(self, mode):
        figs, _ = _draw(mode, _spec(SC, {"by": "foreign"}))
        assert len(figs) == 2
        for letter in ("x", "y"):
            assert _one_object(figs, letter), letter
        assert _close(_emulated_hull(figs, "y"), _fixture_span("c01", 0, "y"))
        assert _close(_emulated_hull(figs, "x"), _fixture_span("c01", 0, "x"))
        rs = figs[0].y_range.renderers
        assert isinstance(rs, list) and len(rs) == 2

    @pytest.mark.parametrize("pid,by", [("c13", "foreign, total"),
                                        ("c14", "rep78, missing"),
                                        ("c27", "foreign rep78")])
    def test_total_missing_and_multi_var_panels_share(self, mode, pid, by):
        figs, _ = _draw(mode, _spec(SC, {"by": by}))
        assert len(figs) == _probe(pid)["n"]
        for letter in ("x", "y"):
            assert _one_object(figs, letter)
            assert _close(_emulated_hull(figs, letter),
                          _fixture_span(pid, 0, letter)), letter

    @pytest.mark.parametrize("ptype", ["histogram", "kdensity"])
    def test_auto_ranged_layers_share(self, mode, ptype):
        figs, _ = _draw(mode, _spec([_plot(ptype, "mpg")], {"by": "foreign"}))
        assert len(figs) == 2
        assert _one_object(figs, "y")
        assert figs[0].y_range.renderers == []

    def test_date_and_log_axes_share(self, mode):
        figs, _ = _draw(mode, _spec([_plot("scatter", "y", "t")],
                                    {"by": "g"}, formats={"t": "%td"}),
                        which="td")
        assert _one_object(figs, "x")
        lo, hi = _emulated_hull(figs, "x")
        # the axis is epoch milliseconds; the fixture is Stata days
        days = ((lo / 86400000.0) + 3653, (hi / 86400000.0) + 3653)
        assert _close(days, _fixture_span("c23", 0, "x"))
        figs, _ = _draw(mode, _spec(SC, {"by": "foreign",
                                         "yscale": "log"}))
        assert _one_object(figs, "y")
        assert _close(_emulated_hull(figs, "y"), _fixture_span("c18", 0, "y"))

    def test_a_linked_by_graph_shares(self, mode):
        spec = _spec(graphs=[_graph("g1", SC, {"by": "foreign"}),
                             _graph("g2", SC)], link="g1 g2")
        figs, _ = _draw(mode, spec)
        panels = [f for f in figs if _title(f) in ("Domestic", "Foreign")]
        assert len(panels) == 2 and _one_object(panels, "y")
        shared = panels[0].y_range.renderers
        for f in panels:
            own = [r for r in f.renderers if hasattr(r, "data_source")]
            assert any(r in shared for r in own), _title(f)

    def test_reverse_is_kept_on_the_shared_range(self, mode):
        figs, _ = _draw(mode, _spec(SC, {"by": "foreign",
                                         "xscale": "reverse"}))
        assert _one_object(figs, "x")
        assert dr._dash_range_reversed(figs[0].x_range)

    def test_qualified_rows_only(self, mode):
        figs, _ = _draw(mode, _spec(SC, {"by": "foreign"},
                                    if_expr="price>6000"))
        assert _one_object(figs, "y")
        assert _close(_emulated_hull(figs, "y"), _fixture_span("d47", 0, "y"))


# ---------------------------------------------------------------------------
def _hull_of(f, letter):
    from bokeh.models import Range1d
    rng = getattr(f, letter + "_range")
    if isinstance(rng, Range1d):
        return dr._dash_range_hull(rng)
    return _emulated_hull([f], letter)


@pytest.mark.parametrize("mode", _MODES)
class TestRescaleGivesEachPanelItsOwn:
    @pytest.mark.parametrize("pid,sub,letters", [
        ("c02", "yrescale", "y"), ("c03", "xrescale", "x"),
        ("c04", "rescale", "xy"), ("c05", "r", "xy"),
        ("e01", "style(rescale) noyrescale", "x")])
    def test_yrescale_xrescale_rescale(self, mode, pid, sub, letters):
        figs, _ = _draw(mode, _spec(SC, {"by": "foreign, " + sub}))
        figs = _panels(figs)
        for letter in ("x", "y"):
            if letter in letters:
                assert not _one_object(figs, letter), letter
                for k, f in enumerate(figs):
                    assert _close(_hull_of(f, letter),
                                  _fixture_span(pid, k, letter)), (letter, k)
            else:
                assert _one_object(figs, letter), letter

    def test_count_ticks_are_per_panel(self, mode):
        with open(_NATSCALE, encoding="utf-8") as fh:
            rec = [r for r in json.load(fh)["by"] if r["command"] ==
                   "twoway scatter mpg weight, by(foreign, yrescale) "
                   "ylabel(#5)"][0]
        figs, _ = _draw(mode, _spec(SC, {"by": "foreign, yrescale",
                                         "ylabel": "#5"}))
        figs = _panels(figs)
        for f, p in zip(figs, rec["panels"]):
            assert _major_ticks(_left(f)) == _steps(*p["y_major"])
        figs, _ = _draw(mode, _spec(SC, {"by": "foreign, rescale",
                                         "ylabel": "#5", "xlabel": "#4"}))
        figs = _panels(figs)
        for k, f in enumerate(figs):
            x = _probe("c30")["panels"][k]["x"]
            assert _major_ticks(_bottom(f)) == _steps(
                x["major_min"], x["major_max"], x["major_delta"])

    @pytest.mark.parametrize("pid,go,letter", [
        ("d19", {"by": "foreign, yrescale", "yscale": "range(0)"}, "y"),
        ("d44", {"by": "foreign, xrescale", "xscale": "range(0)"}, "x"),
        ("e10", {"by": "foreign, yrescale", "yscale": "range(5)"}, "y")])
    def test_range_is_not_applied_on_a_rescaled_axis(self, mode, pid, go,
                                                     letter):
        figs, msgs = _draw(mode, _spec(SC, go))
        figs = _panels(figs)
        for k, f in enumerate(figs):
            assert _close(_hull_of(f, letter),
                          _fixture_span(pid, k, letter)), k
        note = [m for m in msgs if "is not applied, as in twoway" in m]
        assert note == [
            "dash: graph 'g1': by(, %srescale) draws each panel on its own "
            "%s scale; %sscale(range()) is not applied, as in twoway."
            % (letter, letter, letter)]

    def test_range_on_one_panel(self, mode):
        figs, _ = _draw(mode, _spec(SC, {"by": "foreign, yrescale",
                                         "yscale": "range(0)"},
                                    if_expr="foreign == 1"))
        assert len(figs) == 1
        assert _close(_hull_of(figs[0], "y"), _fixture_span("f01", 0, "y"))

    @pytest.mark.parametrize("pid,go,letter", [
        ("d40", {"by": "foreign, yrescale", "xscale": "range(0)"}, "x"),
        ("d41", {"by": "foreign, xrescale", "yscale": "range(0)"}, "y")])
    def test_range_still_applies_on_the_shared_axis(self, mode, pid, go,
                                                    letter):
        figs, _ = _draw(mode, _spec(SC, go))
        assert _one_object(figs, letter)
        assert _close(dr._dash_range_hull(getattr(figs[0], letter + "_range")),
                      _fixture_span(pid, 0, letter))

    def test_count_ticks_ignore_range_on_a_rescaled_axis(self, mode):
        figs, _ = _draw(mode, _spec(SC, {"by": "foreign, yrescale",
                                         "ylabel": "#5",
                                         "yscale": "range(0)"}))
        figs = _panels(figs)
        for k, f in enumerate(figs):
            y = _probe("m07")["panels"][k]["y"]
            ticks = _major_ticks(_left(f))
            assert ticks == _steps(y["major_min"], y["major_max"],
                                   y["major_delta"])
            assert 0.0 not in ticks
            h = _hull_of(f, "y")
            assert h[0] > 0

    @pytest.mark.parametrize("pid,go,want", [
        ("c20", {"ylabel": "0(10)50"}, (0.0, 50.0)),
        ("d48", {"ytick": "0 60"}, (0.0, 60.0))])
    def test_labels_and_ticks_still_widen_each_panel(self, mode, pid, go,
                                                     want):
        figs, _ = _draw(mode, _spec(SC, dict(go, by="foreign, yrescale")))
        assert not _one_object(figs, "y")
        for f in figs:
            assert _close(_hull_of(f, "y"), want)

    def test_reverse_and_log_survive(self, mode):
        from bokeh.models import LogAxis
        figs, _ = _draw(mode, _spec(SC, {"by": "foreign, yrescale",
                                         "yscale": "reverse"}))
        assert all(dr._dash_range_reversed(f.y_range) for f in figs)
        figs, _ = _draw(mode, _spec(SC, {"by": "foreign, yrescale",
                                         "yscale": "log"}))
        assert all(isinstance(_left(f), LogAxis) for f in figs)


# ---------------------------------------------------------------------------
@pytest.mark.parametrize("mode", _MODES)
class TestTheSecondAxisIsShared:
    def test_y2_and_x2(self, mode):
        for pid, plots, go, name in (
                ("c16", DUAL_Y, {"by": "foreign"}, "y2"),
                ("k07", DUAL_Y, {"by": "foreign",
                                 "yscale2": "range(0)"}, "y2"),
                ("f02", DUAL_X, {"by": "foreign"}, "x2")):
            figs, _ = _draw(mode, _spec(plots, go))
            extra = "extra_%s_ranges" % name[0]
            objs = {id(getattr(f, extra)[name]) for f in figs}
            assert len(objs) == 1, pid
            p = _probe(pid)["panels"][0][name]
            assert _close(dr._dash_range_hull(getattr(figs[0], extra)[name]),
                          (p["min"], p["max"])), pid
        for pid, plots, go, name in (
                ("c17", DUAL_Y, {"by": "foreign, yrescale"}, "y2"),
                ("e12", DUAL_Y, {"by": "foreign, yrescale",
                                 "yscale2": "range(0)"}, "y2"),
                ("f03", DUAL_X, {"by": "foreign, xrescale"}, "x2")):
            figs, _ = _draw(mode, _spec(plots, go))
            figs = _panels(figs)
            extra = "extra_%s_ranges" % name[0]
            assert len({id(getattr(f, extra)[name]) for f in figs}) == 2, pid
            for k, f in enumerate(figs):
                p = _probe(pid)["panels"][k][name]
                assert _close(dr._dash_range_hull(getattr(f, extra)[name]),
                              (p["min"], p["max"])), (pid, k)


# ---------------------------------------------------------------------------
_MOVE = (3291.0, 7075.5)


class TestAfterAFilterMove:
    def test_the_shared_range_spans_the_union_after_a_move_served(self):
        import test_mode_parity as mp
        from bokeh.models import RangeSlider
        doc, _b, _s = _served_doc(_spec(SC, {"by": "foreign"},
                                        filt="price, type(range)"))
        w = [x for x in mp._widgets_of(doc) if isinstance(x, RangeSlider)][0]
        mp._fire(w, _MOVE)
        figs = _figs_of(doc.roots)
        assert len(figs) == 2 and _one_object(figs, "y")
        df = _frame()
        rows = df[(df.price >= _MOVE[0]) & (df.price <= _MOVE[1])]
        assert _close(_emulated_hull(figs, "y"),
                      (rows.mpg.min(), rows.mpg.max()))

    def test_the_shared_range_spans_the_union_after_a_move_saved(self):
        from bokeh.models import DataRange1d, Range1d
        _tag, sp, dp = _write(_spec(SC, {"by": "foreign"},
                                    filt="price, type(range)"))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = dr.DashRenderer(sp, dp)
            r.render()
        for cb in r.filter_callbacks:
            for v in (cb.args or {}).values():
                vs = v if isinstance(v, (list, tuple)) else [v]
                assert not any(isinstance(x, (DataRange1d, Range1d))
                               for x in vs)
        figs = list(r.figures.values())
        assert len(figs) == 2 and _one_object(figs, "y")


# ---------------------------------------------------------------------------
def _by_panels_of(figs, n):
    return [f for f in figs if _title(f) in ("Domestic", "Foreign")][:n]


@pytest.mark.parametrize("mode", _MODES)
class TestSharingStaysInOneGraph:
    def _check(self, figs, want=(2, 2)):
        groups = {}
        for f in figs:
            groups.setdefault(id(f.y_range), []).append(f)
        # each by() graph's panels share one object; nothing more is shared
        assert sorted(len(v) for v in groups.values()) == sorted(want)
        for fs in groups.values():
            own = {id(r) for f in fs for r in f.renderers}
            rs = fs[0].y_range.renderers
            if isinstance(rs, list) and rs:
                assert all(id(r) in own for r in rs)

    def test_two_by_graphs(self, mode):
        figs, _ = _draw(mode, _spec(graphs=[
            _graph("g1", SC, {"by": "foreign"}),
            _graph("g2", [_plot("scatter", "price", "weight")],
                   {"by": "foreign"})]))
        assert len(figs) == 4
        self._check(figs)

    def test_by_graphs_in_tabs(self, mode):
        figs, _ = _draw(mode, _spec(graphs=[
            _graph("g1", SC, {"by": "foreign"}),
            _graph("g2", [_plot("scatter", "price", "weight")],
                   {"by": "foreign"})], tabs="g1 g2"))
        self._check(figs)

    def test_by_graph_in_a_link_group_with_a_plain_graph(self, mode):
        figs, _ = _draw(mode, _spec(graphs=[
            _graph("g1", SC, {"by": "foreign"}), _graph("g2", SC)],
            link="g1 g2"))
        self._check(figs, want=(1, 2))


# ---------------------------------------------------------------------------
class TestTheNoteReachesTheUser:
    _GO = {"by": "foreign, rescale", "yscale": "range(0)",
           "xscale": "range(0)"}

    def test_one_note_per_letter_in_both_modes(self):
        got = {}
        for mode in _MODES:
            _f, msgs = _draw(mode, _spec(SC, self._GO))
            got[mode] = sorted(m for m in msgs if "is not applied" in m)
            assert len(got[mode]) == 2
        assert got["saved"] == got["served"]
        for go in ({"yscale": "range(0)"},
                   {"by": "foreign, rescale"}):
            for mode in _MODES:
                _f, msgs = _draw(mode, _spec(SC, go))
                assert not [m for m in msgs if "is not applied" in m]

    def test_served_build_raises_the_range_note(self):
        _doc, built, session = _served_doc(_spec(SC, self._GO))
        notes = [m for m in built if "is not applied" in m]
        assert len(notes) == 2
        assert len([m for m in built + session if "is not applied" in m]) == 2


# ---------------------------------------------------------------------------
class TestTheHelpers:
    def _figs(self, go, which="auto"):
        figs, _ = _draw("saved", _spec(SC, go), which)
        return _panels(figs)

    def test_share_by_scales_units(self):
        from bokeh.models import DataRange1d, Range1d
        from bokeh.plotting import figure
        # a single panel is a no-op
        f = figure()
        before = f.y_range
        dr._dash_share_by_scales([f], frozenset())
        assert f.y_range is before
        # mixed [] / list renderers expand; an empty panel; de-duplication
        a, b, c = figure(), figure(), figure()
        ra = a.scatter([1, 2], [3, 4])
        rb = b.scatter([5], [6])
        a.y_range.renderers = [ra, ra]
        dr._dash_share_by_scales([a, b, c], frozenset())
        assert a.y_range is b.y_range is c.y_range
        assert list(a.y_range.renderers) == [ra, rb]
        # idempotent
        dr._dash_share_by_scales([a, b, c], frozenset())
        assert a.y_range is b.y_range and list(a.y_range.renderers) == [ra, rb]
        # #N start and end survive the sharing (share before ticking)
        figs = self._figs({"by": "foreign", "ylabel": "#5"})
        rng = figs[0].y_range
        assert isinstance(rng, DataRange1d) and figs[1].y_range is rng
        assert rng.start is not None and rng.start <= 10.0
        assert rng.end is not None and rng.end >= 40.0
        # letters=("x",) leaves y alone
        p, q = figure(), figure()
        p.scatter([1], [2])
        q.scatter([3], [4])
        y_before = p.y_range
        dr._dash_common_count_ticks([p, q], letters=("x",))
        assert p.y_range is y_before
        # with made, _dash_hull_ranges gives one object
        figs = self._figs({"by": "foreign, yrescale", "xscale": "range(0)"})
        made = {}
        for f in figs:
            es = [e for e in f._dash_hull_axes if e["letter"] == "x"]
            dr._dash_hull_ranges(f, es, common={("default", "x"): (0, 5000)},
                                 made=made)
        assert figs[0].x_range is figs[1].x_range
        assert isinstance(figs[0].x_range, Range1d)


class TestTheFixtureIsPinned:
    def test_meta_stamp(self):
        meta = _truth()["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted"):
            assert str(meta.get(k, "")).strip(), k

    def test_every_probe_has_panels(self):
        for p in _truth()["probes"]:
            if p["rc"] == 0:
                assert p["n"] >= 1 and len(p["panels"]) == p["n"], p["id"]
            else:
                assert p["rc"] == 198, p["id"]
