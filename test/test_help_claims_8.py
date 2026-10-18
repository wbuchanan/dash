"""The claims in dash.sthlp's last four sections, held to the code.

WP-23 (ROADMAP.md) asks that every claim in ``dash.sthlp`` be true of the
shipped code and verified by a test, or corrected.  This file covers the
part of the help from ``{marker scheme}`` to the end -- Stata scheme support,
the Unsupported Stata twoway options, Dependencies and Also see -- together
with ``dash_setup.sthlp`` and the package descriptions in ``dash.pkg`` and
``stata.toc``.  The Stata-side claims are certified by
``test_help_claims_8.cscript`` (cases HC8-01 onward); this file holds the
ones the renderer, the generated server app and the shipped text can answer.

Every claim about ``twoway`` here was measured in console Stata 19.5
(``set graphics off``, ``graph export`` to SVG, tick marks read from the
SVG's ``<line>`` elements), 23sep2026:

* ``xtick()`` adds tick marks WITHOUT labels, at the full major length, and
  keeps every label -- the default rule's or ``xlabel()``'s.  Alone, on
  auto's weight, the labels stay 2,000 3,000 4,000 5,000 and six unlabelled
  marks join them; with ``xlabel(2000(1000)5000) xtick(2500(1000)4500)``
  both sets are drawn; with ``xlabel(none) xtick(2500 3500)`` only the two
  marks are.  ``xtick(minmax)`` marks the data's extremes, ``xtick(#10)``
  about ten positions, a label written inside ``xtick()`` is not drawn, and
  no grid line is drawn at a mark.  ``xmtick()`` marks are half length.
* ``title2()``, ``subtitle2()``, ``mlabwidth()``, ``at()``, ``blabel()``
  (on ``twoway bar``), ``ciopts()``, ``lineopts()`` and ``fitopts()`` (on
  ``lfitci`` and ``kdensity``), ``link()`` and ``filter()`` are refused,
  r(198), "option ... not allowed".  ``scale(1.5)`` is accepted and resizes
  the text, markers and lines ([G-3] scale_option); ``fxsize()`` and
  ``fysize()`` are accepted on any graph ([G-2] graph combine).
* ``sort(rep78)`` -- a variable with ties -- joined the same 74 points in a
  different order on each of three draws in one session, the sort seed
  advancing between them.
"""
import json
import ast
import os
import re
import subprocess
import sys
import textwrap
import warnings

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr                                         # noqa: E402
from bokeh.models import Plot                                    # noqa: E402
from bokeh.models.tickers import (BasicTicker, CustomJSTicker,   # noqa: E402
                                  FixedTicker)

from conftest import make_spec, stata_base                       # noqa: E402
from test_adversarial_matrix import (_app_source, _load_app,     # noqa: E402
                                     _session, _write_inputs)

_HELP = os.path.join(_ROOT, "dash.sthlp")
_SETUP_HELP = os.path.join(_ROOT, "dash_setup.sthlp")
_SETUP_ADO = os.path.join(_ROOT, "dash_setup.ado")
_ADO = os.path.join(_ROOT, "dash.ado")
_PKG = os.path.join(_ROOT, "dash.pkg")
_TOC = os.path.join(_ROOT, "stata.toc")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


# auto's weight span, so the default labels have room either side of the
# marks, and a y with no ties.
_DF = pd.DataFrame({
    "mpg": [22.0, 17.0, 25.0, 30.0, 21.0, 19.0, 14.0, 28.0, 16.0, 23.0,
            20.0, 18.0],
    "weight": [2930.0, 3350.0, 2200.0, 1800.0, 3000.0, 3100.0, 4080.0,
               2010.0, 3600.0, 2650.0, 4840.0, 1760.0],
    "price": [4099.0, 4749.0, 3799.0, 4816.0, 5788.0, 4453.0, 5189.0,
              10372.0, 4082.0, 11385.0, 6165.0, 3955.0],
    "foreign": [0.0, 1.0] * 6,
})


def _one_graph(plots, gopts=None, build=None):
    spec = make_spec(plots)
    spec["graphs"][0]["graph_options"].update(gopts or {})
    spec["build_options"].update(build or {})
    return spec


def _scatter(gopts=None, build=None):
    return _one_graph([{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                        "options": {}}], gopts, build)


def _saved_figure(tmp_path, spec, df=_DF):
    d = tmp_path / "saved"
    d.mkdir(parents=True, exist_ok=True)
    sp, dp = _write_inputs(d, spec, df)
    r = dr.DashRenderer(sp, dp)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        html = r.render()
    return r.figures["g1"], html, [str(x.message) for x in w]


def _served_figure(tmp_path, spec, df=_DF, tag="t"):
    d = tmp_path / "served"
    d.mkdir(parents=True, exist_ok=True)
    ns = _load_app(_app_source(d, spec, df), re.sub(r"\W", "_", tag))
    doc = _session(ns)
    plots = list(doc.select({"type": Plot}))
    assert plots, "the served document holds no figure"
    return plots[0], doc


def _figure(mode, tmp_path, spec, df=_DF, tag="t"):
    if mode == "saved":
        return _saved_figure(tmp_path, spec, df)[0]
    return _served_figure(tmp_path, spec, df, tag)[0]


_MODES = ("saved", "served")


# ===========================================================================
# 1. xtick() and ytick(): tick marks without labels, beside the labels
# ===========================================================================
#
# dash.sthlp's Unsupported section says "xtick() and xlabel() are honoured",
# and the axis table says xtick() is "x-axis tick positions without labels".
# Measured at 4ede074, in BOTH modes (one helper, _dash_apply_axis_options,
# draws both): xtick() alone REPLACED the default labels with labelled ticks
# at its own positions; beside xlabel() it was dropped (`raw = xlabel or
# xtick'); beside xlabel(none) nothing at all was drawn.  GAPS.md F4 had it
# as fixed by WP-14/15; it was not.

def _tick_plan(axis):
    """What an axis draws: (labels, marks).

    labels is ("fixed", [positions]) for a FixedTicker, or ("auto", name)
    for a ticker Bokeh evaluates in the browser (named for the ticker that
    places the labels).  marks are the unlabelled positions: a sorted list,
    or ("count", N) for xtick(#N).
    """
    t = axis.ticker
    if isinstance(t, CustomJSTicker):
        base = t.args.get("base")
        labels = (("fixed", sorted(base.ticks))
                  if isinstance(base, FixedTicker)
                  else ("auto", type(base).__name__))
        # The count's ticker and the positions, under either name the
        # ticker has carried them by (``marks_ticker``/``marks`` or
        # ``every``/``extra``): what the axis draws is the test.
        count_ticker = t.args.get("marks_ticker", t.args.get("every"))
        if count_ticker is not None and \
                dr._dash_count_of(count_ticker) is not None:
            marks = ("count", count_ticker.desired_num_ticks)
        else:
            marks = sorted(float(v) for v in
                           t.args.get("marks", t.args.get("extra", [])))
        return labels, marks
    if isinstance(t, FixedTicker):
        return ("fixed", sorted(t.ticks)), sorted(t.minor_ticks)
    return ("auto", type(t).__name__), []


@pytest.mark.parametrize("mode", _MODES)
class TestXtickDrawsMarksWithoutLabels:

    def test_alone_it_keeps_the_default_labels(self, tmp_path, mode):
        fig = _figure(mode, tmp_path, _scatter({"xtick": "2250(500)3750"}),
                      tag="alone")
        # WP-30 P1.3a: Bokeh's BasicTicker was wrong because a default axis
        # is now ticked as twoway ticks it (natscale #5, a FixedTicker).
        assert _tick_plan(fig.xaxis[0]) == (
            ("fixed", [2000.0, 3000.0, 4000.0, 5000.0]), [2250.0, 2750.0, 3250.0, 3750.0])

    def test_beside_xlabel_both_are_drawn(self, tmp_path, mode):
        fig = _figure(mode, tmp_path, _scatter(
            {"xlabel": "2000(1000)4000", "xtick": "2500 3500"}), tag="both")
        assert _tick_plan(fig.xaxis[0]) == (
            ("fixed", [2000.0, 3000.0, 4000.0]), [2500.0, 3500.0])

    def test_beside_xlabel_none_only_the_marks_are_drawn(self, tmp_path,
                                                         mode):
        fig = _figure(mode, tmp_path, _scatter(
            {"xlabel": "none", "xtick": "2500 3500"}), tag="none")
        assert _tick_plan(fig.xaxis[0]) == (("fixed", []), [2500.0, 3500.0])

    def test_beside_a_count_the_labels_stay_the_counts(self, tmp_path, mode):
        """xlabel(#4) over weight's 1760 to 4840 labels 2000(1000)5000, as
        twoway draws it (test/fixtures/natscale_truth.json, auto weight
        #4), and the marks sit beside those labels."""
        fig = _figure(mode, tmp_path, _scatter(
            {"xlabel": "#4", "xtick": "2500 3500"}), tag="count")
        plan = _tick_plan(fig.xaxis[0])
        assert plan == (("fixed", [2000.0, 3000.0, 4000.0, 5000.0]),
                        [2500.0, 3500.0])

    def test_ytick_alone_keeps_the_default_labels(self, tmp_path, mode):
        fig = _figure(mode, tmp_path, _scatter({"ytick": "15 25 35"}),
                      tag="ytick")
        # WP-30 P1.3a: Bokeh's BasicTicker was wrong because a default axis
        # is now ticked as twoway ticks it (natscale #5, a FixedTicker).
        assert _tick_plan(fig.yaxis[0]) == (
            ("fixed", [15.0, 20.0, 25.0, 30.0]), [15.0, 25.0, 35.0])
        # and the x axis is left as it was
        assert _tick_plan(fig.xaxis[0]) == (("fixed", [2000.0, 3000.0, 4000.0, 5000.0]), [])

    def test_minmax_marks_the_extremes(self, tmp_path, mode):
        fig = _figure(mode, tmp_path, _scatter({"xtick": "minmax"}),
                      tag="minmax")
        # WP-30 P1.3a: Bokeh's BasicTicker was wrong because a default axis
        # is now ticked as twoway ticks it (natscale #5, a FixedTicker).
        assert _tick_plan(fig.xaxis[0]) == (
            ("fixed", [2000.0, 3000.0, 4000.0, 5000.0]), [1760.0, 4840.0])

    def test_a_count_marks_about_that_many(self, tmp_path, mode):
        """xtick(#10) over weight's 1760 to 4840 marks 1500(500)5000, the
        positions twoway gives #10 there (natscale_truth.json, auto weight
        #10)."""
        fig = _figure(mode, tmp_path, _scatter({"xtick": "#10"}),
                      tag="tcount")
        # WP-30 P1.3a: Bokeh's BasicTicker was wrong because a default axis
        # is now ticked as twoway ticks it (natscale #5, a FixedTicker).
        assert _tick_plan(fig.xaxis[0]) == (
            ("fixed", [2000.0, 3000.0, 4000.0, 5000.0]), [1500.0 + 500 * i for i in range(8)])

    def test_a_label_written_in_xtick_is_not_drawn(self, tmp_path, mode):
        """twoway draws `xtick(2500 "a" 3500)' as two bare marks."""
        fig = _figure(mode, tmp_path, _scatter(
            {"xlabel": "2000(1000)4000", "xtick": '2500 "a" 3500'}),
            tag="lab")
        ax = fig.xaxis[0]
        assert _tick_plan(ax) == (
            ("fixed", [2000.0, 3000.0, 4000.0]), [2500.0, 3500.0])
        assert "a" not in dict(ax.major_label_overrides).values()

    def test_the_marks_are_drawn_at_the_major_length(self, tmp_path, mode):
        """Stata's xtick() marks are major ticks: measured, the same
        length and stroke as the labelled ones."""
        fig = _figure(mode, tmp_path, _scatter(
            {"xlabel": "2000(1000)4000", "xtick": "2500 3500"}), tag="len")
        ax = fig.xaxis[0]
        assert ax.minor_tick_out == ax.major_tick_out
        assert ax.minor_tick_in == ax.major_tick_in
        assert ax.minor_tick_line_color == ax.major_tick_line_color
        assert ax.minor_tick_line_width == ax.major_tick_line_width

    def test_no_grid_line_is_drawn_at_a_mark(self, tmp_path, mode):
        fig = _figure(mode, tmp_path, _scatter({"ytick": "15 25 35"}),
                      tag="grid")
        # The figure's one y grid (measured 24sep2026, both modes): an
        # all() over no grid held with the grid gone.
        assert len(fig.ygrid) == 1, len(fig.ygrid)
        assert all(g.minor_grid_line_color is None for g in fig.ygrid)

    def test_xtick_none_changes_nothing(self, tmp_path, mode):
        fig = _figure(mode, tmp_path, _scatter({"xtick": "none"}),
                      tag="tnone")
        # WP-30 P1.3a: Bokeh's BasicTicker was wrong because a default axis
        # is now ticked as twoway ticks it (natscale #5, a FixedTicker).
        assert _tick_plan(fig.xaxis[0]) == (("fixed", [2000.0, 3000.0, 4000.0, 5000.0]), [])


class TestTheTickMarkCodeCarriesNoUserText:
    """The CustomJSTicker's code is constant; the positions are data."""

    def test_the_code_is_the_same_for_any_positions(self, tmp_path):
        a = _saved_figure(tmp_path, _scatter({"xtick": "2500 3500"}))[0]
        t = a.xaxis[0].ticker
        assert isinstance(t, CustomJSTicker)
        assert "2500" not in t.major_code + t.minor_code
        assert all(isinstance(v, float)
                   for v in t.args.get("marks", t.args.get("extra")))

    def test_a_hostile_label_in_xtick_reaches_no_model(self, tmp_path):
        evil = '2500 "</script><script>alert(1)</script>" 3500'
        fig, html, _w = _saved_figure(tmp_path, _scatter({"xtick": evil}))
        assert "<script>alert(1)" not in html
        assert _tick_plan(fig.xaxis[0])[1] == [2500.0, 3500.0]
        # The check on the page above cannot see a model: Bokeh escapes the
        # document it embeds, so a label a model carries reaches the page
        # as &lt;script&gt;alert(1)...  Measured 24sep2026 with the same
        # label in xlabel(), where labels are drawn: it is in the axis's
        # major_label_overrides and the CustomJSTickFormatter's args, the
        # page holds "alert(1)" twice -- and "<script>alert(1)" not once.
        # So the models are read, and the page for "alert(1)", which the
        # escaping leaves as it is; the xlabel() page is the control that
        # both readings find the label when a model does carry it.
        def carriers(f):
            return sorted({(type(m).__name__, k) for m in f.references()
                           for k, v in m.properties_with_values(
                               include_defaults=False).items()
                           if "alert(1)" in str(v)})
        assert carriers(fig) == [], carriers(fig)
        assert "alert(1)" not in html
        ctl, ctl_html, _w = _saved_figure(tmp_path / "control",
                                          _scatter({"xlabel": evil}))
        assert carriers(ctl) == [("CustomJSTickFormatter", "args"),
                                 ("LinearAxis", "major_label_overrides")]
        assert ctl_html.count("alert(1)") == 2
        assert "<script>alert(1)" not in ctl_html

    @pytest.mark.parametrize("mode", _MODES)
    def test_a_huge_request_is_bounded(self, tmp_path, mode):
        """Resource exhaustion: xtick(#N) with an absurd N is clamped to
        _MAX_AXIS_TICKS, and an a(b)c that would make millions of marks
        makes none -- the parser's bound, shared with xlabel()."""
        import time
        t0 = time.time()
        fig = _figure(mode, tmp_path / "count", _scatter(
            {"xtick": "#" + "9" * 400}), tag="hugecount")
        # Clamped to #2000, which twoway draws over 1760 to 4840 as
        # 1760(2)4840, 1,541 marks (`_natscale 1760 4840 2000', measured).
        marks = _tick_plan(fig.xaxis[0])[1]
        assert len(marks) == 1541 and marks[0] == 1760.0 \
            and marks[-1] == 4840.0
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            fig = _figure(mode, tmp_path / "range", _scatter(
                {"xtick": "0(0.000001)1000000"}), tag="hugerange")
        # WP-30 P1.3a: the default labels are now natscale's FixedTicker.
        assert _tick_plan(fig.xaxis[0]) == (("fixed", [2000.0, 3000.0, 4000.0, 5000.0]), [])
        assert time.time() - t0 < 30


class TestXtickSubOptionsAreNamed:
    """A tick sub-option dash does not draw is named, not dropped; grid,
    which twoway draws, is drawn."""

    @pytest.mark.parametrize("mode", _MODES)
    def test_grid_on_xtick_draws_gridlines_and_is_not_named(self, tmp_path,
                                                             mode):
        """Measured 23sep2026 (twoway SVG, WP-23's integration): with
        `xtick(2500 3500, grid)` twoway draws grid lines at the marks -- 56
        more line segments than without `grid` -- so dash draws them too,
        as minor grid lines, and does not name the sub-option."""
        spec = _scatter({"xtick": "2500 3500, grid"})
        if mode == "saved":
            fig, _html, msgs = _saved_figure(tmp_path, spec)
        else:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                d = tmp_path / "served"
                d.mkdir()
                doc = _document_for(_load_app(_app_source(d, spec, _DF),
                                              "subopt"))
            msgs = [str(x.message) for x in w]
            fig = next(iter(doc.select({"type": Plot})))
        assert not any("sub-option" in m and "grid" in m for m in msgs), msgs
        assert any(g.minor_grid_line_color is not None for g in fig.xgrid)


def _document_for(ns):
    """make_document on a fresh Document, warnings left to the caller."""
    from bokeh.document import Document
    doc = Document()
    ns["make_document"](doc)
    return doc


# ===========================================================================
# 2. Dependencies: no layer imports scipy or statsmodels, in either mode
# ===========================================================================
#
# dash.sthlp (Dependencies) and dash_setup.sthlp say every statistical layer
# is computed with numpy and that an installed scipy or statsmodels is
# "neither required nor read".  test_dependency_guards.py blocks one package
# per GlyphMapper method, in-process; nothing ran the WHOLE renderer -- the
# module import, every plot type, both modes, and the served recompute --
# with the packages unimportable.  This does, in a fresh interpreter (the
# test process has long since imported whatever it imported), twice: once
# with both packages made unimportable, and once watching an installed copy
# to prove nothing even asks for it.

_DEP_SCRIPT = textwrap.dedent(r'''
    import importlib.abc, json, os, sys, tempfile, warnings
    ROOT, HERE, MODE = sys.argv[1], sys.argv[2], sys.argv[3]
    BLOCK = ("scipy", "statsmodels")
    attempts = []

    class _Watch(importlib.abc.MetaPathFinder):
        def find_spec(self, name, path=None, target=None):
            if name.split(".")[0] in BLOCK:
                attempts.append(name)
                if MODE == "block":
                    raise ModuleNotFoundError(
                        "No module named %r (made unimportable)" % name,
                        name=name)
            return None

    for _m in [m for m in sys.modules if m.split(".")[0] in BLOCK]:
        del sys.modules[_m]
    sys.meta_path.insert(0, _Watch())
    sys.path[:0] = [ROOT, HERE]

    import dash_render as dr
    from bokeh.document import Document
    from bokeh.models import GlyphRenderer, Select
    from test_every_plot_type_draws import _DATA, _plot_for

    KERNELS = ("epanechnikov", "epan2", "biweight", "cosine", "gaussian",
               "parzen", "rectangle", "triangle")
    VARIANTS = {
        "lfitci": [{"stdf": "stdf"}, {"stdr": "stdr"}, {"level": "90"}],
        "qfitci": [{"stdf": "stdf"}, {"stdr": "stdr"}, {"level": "90"}],
        "fpfitci": [{"level": "90"}],
        "lpolyci": [{"level": "90"}, {"degree": "2"}],
        "lpoly": [{"degree": "0"}, {"degree": "2"}, {"kernel": "gaussian"}],
        "lowess": [{"mean": "mean"}, {"noweight": "noweight"},
                   {"adjust": "adjust"}, {"bwidth": "0.5"}],
        "kdensity": [{"kernel": k} for k in KERNELS] + [{"n": "30"}],
        "mspline": [{"bands": "5"}, {"n": "20"}],
        "mband": [{"bands": "5"}],
        "histogram": [{"bin": "5"}, {"discrete": "discrete"},
                      {"frequency": "frequency"}, {"percent": "percent"},
                      {"fraction": "fraction"}],
    }
    CURDOC = "if __name__ != '__main__':\n    make_document(curdoc())"

    def layers():
        for ptype in sorted(dr._dash_plot_type_names()):
            base = _plot_for(ptype)
            if ptype == "function":
                base = dict(base, expr="sin(x) + sqrt(x)")
            yield ptype, base
            for extra in VARIANTS.get(ptype, []):
                p = json.loads(json.dumps(base))
                p["options"].update(extra)
                yield ptype + " " + json.dumps(extra, sort_keys=True), p

    def spec_for(plot):
        return {"graphs": [{"graph_options": {"name": "g1"},
                            "plots": [plot], "if_expr": "", "in_expr": ""}],
                "kpis": [],
                "build_options": {"layout": "auto", "level": "95",
                                  "registry": "g1",
                                  "filters": [{"varname": "g",
                                               "type": "dropdown"}]}}

    def drawn(renderers):
        return sum(1 for r in renderers
                   if any(len(v) for v in r.data_source.data.values()))

    failures, counts = [], {}
    for label, plot in layers():
        td = tempfile.mkdtemp()
        sp, dp = os.path.join(td, "s.json"), os.path.join(td, "d.json")
        with open(sp, "w") as fh:
            json.dump(spec_for(plot), fh)
        with open(dp, "w") as fh:
            json.dump(_DATA, fh)
        try:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                r = dr.DashRenderer(sp, dp)
                r.render()
                saved = drawn([x for x in r.figures["g1"].renderers
                               if isinstance(x, GlyphRenderer)])
                ap = os.path.join(td, "app.py")
                dr.ServerAppBuilder(sp, dp).build(ap)
                with open(ap, encoding="utf-8") as fh:
                    src = fh.read()
                ns = {"__name__": "dash_dep_app"}
                exec(compile(src.replace(CURDOC, "pass"), ap, "exec"), ns)
                doc = Document()
                ns["make_document"](doc)
                served = drawn(list(doc.select({"type": GlyphRenderer})))
                # The served recompute: the filter moves, and the layer is
                # computed again by the app's copy of the same code.
                for s in doc.select({"type": Select}):
                    for cb in s._callbacks.get("value", []):
                        cb("value", s.value, "1")
                after = drawn(list(doc.select({"type": GlyphRenderer})))
            dep = [str(x.message) for x in w
                   if any(b in str(x.message).lower() for b in BLOCK)]
            counts[label] = [saved, served, after]
            if not (saved and served and after):
                failures.append("%s drew nothing: saved %d, served %d, "
                                "after the filter %d" % (label, saved,
                                                         served, after))
            if dep:
                failures.append("%s warned about %s" % (label, dep))
        except BaseException as exc:          # the point of the test
            failures.append("%s raised %s: %s" % (label, type(exc).__name__,
                                                  exc))
    print(json.dumps({
        "attempts": sorted(set(attempts)),
        "loaded": sorted(m for m in sys.modules
                         if m.split(".")[0] in BLOCK),
        "failures": failures, "counts": counts}))
''')


def _run_dep_script(mode):
    proc = subprocess.run(
        [sys.executable, "-c", _DEP_SCRIPT, _ROOT, _HERE, mode],
        capture_output=True, text=True, timeout=600)
    assert proc.returncode == 0, proc.stderr[-4000:]
    return json.loads(proc.stdout.strip().splitlines()[-1])


# One worker for the class, so each of its two subprocess sweeps runs
# once, not once per worker its tests land on (WP-30 test performance
# A4; measured 07oct2026: the 33-second blocked sweep ran on three).
@pytest.mark.xdist_group(name="hc8-no-scipy-or-statsmodels")
class TestNoLayerNeedsScipyOrStatsmodels:

    @pytest.fixture(scope="class")
    def blocked(self):
        return _run_dep_script("block")

    @pytest.fixture(scope="class")
    def watched(self):
        return _run_dep_script("watch")

    @pytest.mark.release  # a 33-second subprocess sweep (WP-30 D)
    def test_every_layer_draws_with_both_packages_unimportable(self, blocked):
        assert not blocked["failures"], "\n".join(blocked["failures"])

    @pytest.mark.release  # a 33-second subprocess sweep (WP-30 D)
    def test_nothing_asks_for_them_when_they_are_unimportable(self, blocked):
        assert blocked["attempts"] == [], blocked["attempts"]

    @pytest.mark.release  # a 33-second subprocess sweep (WP-30 D)
    def test_every_plot_type_was_run(self, blocked):
        ran = {k.split()[0] for k in blocked["counts"]}
        assert ran == set(dr._dash_plot_type_names())
        assert len(blocked["counts"]) >= 70, len(blocked["counts"])
        # Every row ran: a layer that raises is left out of `counts', so
        # the floor passed with three of them gone.  Measured 24sep2026:
        # one row a plot type (40) and the 33 of _DEP_SCRIPT's VARIANTS.
        assert len(blocked["counts"]) == len(dr._dash_plot_type_names()) + 33, (
            sorted(blocked["counts"]))

    @pytest.mark.release  # a 33-second subprocess sweep (WP-30 D)
    def test_an_installed_copy_is_not_read(self, watched):
        """With scipy and statsmodels importable, nothing imports them --
        not dash, not a library dash calls on the way."""
        assert watched["attempts"] == [], watched["attempts"]
        assert watched["loaded"] == [], watched["loaded"]
        assert not watched["failures"], "\n".join(watched["failures"])

    def test_no_source_line_imports_either(self):
        """Every import statement in dash_render.py, at any depth."""
        import ast
        tree = ast.parse(_read(os.path.join(_ROOT, "dash_render.py")))
        bad = []
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            elif (isinstance(node, ast.Call) and node.args
                  and isinstance(node.args[0], ast.Constant)
                  and isinstance(node.args[0].value, str)
                  and getattr(node.func, "attr",
                              getattr(node.func, "id", "")) in (
                                  "import_module", "__import__",
                                  "_optional_import")):
                names = [node.args[0].value]
            bad += [(n, node.lineno) for n in names
                    if n.split(".")[0] in ("scipy", "statsmodels")]
        assert not bad, bad


# ===========================================================================
# 3. Stata scheme support
# ===========================================================================

#: Stata's base ado tree: DASH_STATA_BASE, else StataNow's (WP-30 P1.34).
_STATA_BASE = stata_base()


def _stata_file(rel):
    """One of Stata's own files, or a skip on a machine without Stata."""
    p = os.path.join(_STATA_BASE, rel)
    if not os.path.isfile(p):
        pytest.skip("Stata's %s is not on this machine" % rel)
    return _read(p)


def _help_between(start, end, path=_HELP):
    h = _read(path)
    i = h.index(start)
    return h[i:h.index(end, i)]


def _flat(text):
    return " ".join(text.split())


def _smcl_text(text):
    """SMCL as read: {cmd:x}, {bf:x}, {it:x} and friends keep their text,
    every other directive goes, whitespace folds."""
    text = re.sub(r"\{(?:cmd|bf|it|opt|hi|res|txt|err):([^}]*)\}", r"\1",
                  text)
    text = re.sub(r"\{help(?:b)? [^:}]*:([^}]*)\}", r"\1", text)
    return _flat(re.sub(r"\{[^}]*\}", "", text))


def _scheme_row(name):
    """The scheme table's row for *name*, whitespace folded."""
    sec = _help_between("{marker scheme}", "{marker unsupported}")
    m = re.search(r"\{synopt:\{cmd:%s\}\}(.*?)\{p_end\}" % re.escape(name),
                  sec, re.S)
    assert m, "no row for %s in the scheme table" % name
    return _flat(m.group(1))


def _directives(path):
    """(key, value) for every directive line of a .scheme file."""
    out = []
    for ln in _read(path).splitlines():
        s = ln.strip()
        if not s or s.startswith("*"):
            continue
        parts = s.split(None, 2)
        out.append((" ".join(parts[:2]), parts[2] if len(parts) > 2 else ""))
    return out


_SCHEMES = _ROOT
_S2MONO_FAMILY = ("s2mono", "s2manual", "s2gmanual", "sj", "stsj", "stmono2")


class TestTheSchemeTableSaysWhatStataSays:
    """Each row is read against Stata's own help and scheme files.

    _stata_file skips its test on a machine without Stata, and each test
    here read Stata's file first -- so the half of it that reads only
    dash's own help, shipped schemes and constants was skipped with it,
    and on such a machine a wrong row or a wrong size passed unseen
    (24sep2026).  That half is a test of its own, ``..._in_dash``, which
    needs no Stata and runs everywhere."""

    def test_stcolor_is_the_default_as_of_stata_18(self):
        assert ("default scheme as of Stata 18"
                in _flat(_stata_file("s/scheme_st.sthlp")))

    def test_stcolor_is_the_default_as_of_stata_18_in_dash(self):
        assert "as of Stata 18" in _scheme_row("stcolor")

    def test_s2color_was_the_default_before_stata_18(self):
        """The row said "the default from Stata 10 to 17"; Stata's own help
        says only "prior to Stata 18" (s2color was the default from Stata
        8, whose graphics it came with)."""
        assert ("Scheme s2color was Stata's default scheme prior to Stata 18"
                in re.sub(r"\{cmd:([^}]*)\}", r"\1",
                          _flat(_stata_file("s/scheme_s2.sthlp"))))

    def test_s2color_was_the_default_before_stata_18_in_dash(self):
        row = _scheme_row("s2color")
        assert "before Stata 18" in row and "Stata 10" not in row

    def test_s2manual_and_s2gmanual_are_the_manuals_before_stata_13(self):
        s2 = _smcl_text(_stata_file("s/scheme_s2.sthlp"))
        assert "s2manual is the scheme used in the Stata manuals prior to Stata 13" in s2
        assert ("s2gmanual is the scheme used in the Stata Graphics Reference "
                "Manual prior to Stata 13") in s2

    def test_s2manual_and_s2gmanual_are_the_manuals_before_stata_13_in_dash(
            self):
        assert "before Stata 13" in _scheme_row("s2manual")
        assert "before Stata 13" in _scheme_row("s2gmanual")

    def test_stgcolor_alt_is_stcolor_alt_at_the_manuals_size(self):
        st = _flat(_stata_file("s/scheme_st.sthlp"))
        assert "3.588 and 2.392 inches" in st

    def test_stgcolor_alt_is_stcolor_alt_at_the_manuals_size_in_dash(self):
        sch = dr.SchemeParser("stgcolor_alt")
        assert (sch.graphsize_x, sch.graphsize_y) == (3.588, 2.392)
        assert "stcolor_alt" in _scheme_row("stgcolor_alt")

    def test_sttrans_is_s2color_restyled_with_tols_muted_colours(self):
        src = _stata_file("s/scheme-sttrans.scheme")
        assert re.search(r"^#include s2color\s*$", src, re.M)
        assert "Paul Tol's muted" in src
        assert re.search(r"^color background\s+white\b", src, re.M)
        assert re.search(r"^clockdir legend_position\s+3\b", src, re.M)
        # Every p1..p15 declared at twenty percent, in Stata and in dash.
        stata_p = dict(re.findall(r'^color (p\d+)\s+"([^"]+)"', src, re.M))
        assert all(stata_p["p%d" % i].endswith("%20") for i in range(1, 16))
        ours = dict(_directives(os.path.join(_SCHEMES, "dash-sttrans.scheme")))
        for i in range(1, 16):
            r, g, b = (int(v) for v in stata_p["p%d" % i].split()[:3])
            assert ours["color p%d" % i].lower() == (
                "#%02x%02x%02x%%20" % (r, g, b)), i

    def test_sttrans_is_s2color_restyled_with_tols_muted_colours_in_dash(
            self):
        ours = dict(_directives(os.path.join(_SCHEMES, "dash-sttrans.scheme")))
        # Every p1..p15 at twenty percent in dash's file too.
        assert all(ours["color p%d" % i].endswith("%20")
                   for i in range(1, 16))
        # p2..p9 are Tol's muted rose, sand, green, cyan, wine, teal,
        # olive and purple; p1 stays Stata blue.
        tol = ["#cc6677", "#ddcc77", "#117733", "#88ccee", "#882255",
               "#44aa99", "#999933", "#aa4499"]
        assert [ours["color p%d" % i][:7] for i in range(2, 10)] == tol
        row = _scheme_row("sttrans")
        assert "based on Paul Tol's muted" in row and "%20" in row

    def test_s2color8_uses_the_8_colours_where_the_row_says(self):
        src = _stata_file("s/scheme-s2color8.scheme")
        for key, val in (("color background", "ltbluishgray8"),
                         ("color major_grid", "ltbluishgray8"),
                         ("color box", "bluishgray8"),
                         ("color p1", "navy8"), ("color p15", "bluishgray8")):
            assert re.search(r"^%s\s+%s\s*$" % (key, val), src, re.M), key

    def test_s1manual_is_s1mono_smaller_with_larger_markers(self):
        s1 = _smcl_text(_stata_file("s/scheme_s1.sthlp"))
        assert "s1manual is the same as s1mono but presents graphs at a smaller overall size" in s1

    def test_s1manual_is_s1mono_smaller_with_larger_markers_in_dash(self):
        man, mono = dr.SchemeParser("s1manual"), dr.SchemeParser("s1mono")
        assert (man.graphsize_x, man.graphsize_y) == (3.12, 2.392)
        assert man.marker_size > mono.marker_size
        assert "larger markers" in _scheme_row("s1manual")

    def test_s1rcolor_is_light_on_dark(self):
        sch = dr.SchemeParser("s1rcolor")
        assert sch.background_color.lower() == "#000000"
        assert sch.text_color.lower() == "#ffffff"


def _two_layer(ptype, scheme, extra=None):
    """A black scatter first, then *ptype*, which takes the p2 cycle."""
    from test_every_plot_type_draws import _plot_for
    second = _plot_for(ptype)
    if ptype == "function":
        second = dict(second, expr="x")
    second = json.loads(json.dumps(second))
    second["options"].update(extra or {})
    return {"graphs": [{"graph_options": {"name": "g1"},
                        "plots": [{"type": "scatter", "yvar": "y",
                                   "xvar": "x",
                                   "options": {"mcolor": "black"}}, second],
                        "if_expr": "", "in_expr": ""}],
            "kpis": [],
            "build_options": {"layout": "auto", "level": "95",
                              "registry": "g1", "scheme": scheme}}


def _layer_styles(mode, tmp_path, spec, tag):
    """Sorted (colour, alpha) of every glyph but the black first layer's.

    A glyph's outline drawn in a named colour (a histogram's white) is not
    a scheme colour and is left out."""
    from test_every_plot_type_draws import _DATA
    df = pd.DataFrame(_DATA["values"])
    fig = _figure(mode, tmp_path, spec, df, tag)
    out = []
    for r in fig.renderers:
        g = getattr(r, "glyph", None)
        if g is None:
            continue
        for c, a in (("line_color", "line_alpha"),
                     ("fill_color", "fill_alpha")):
            col = getattr(g, c, None)
            if (isinstance(col, str) and col.startswith("#")
                    and col.lower() != "#000000"):
                out.append((col.lower(), getattr(g, a)))
    return sorted(out)


#: Range, spike, fit, band, density, function and immediate layers: the
#: ones dash.sthlp used to say took the scheme's colour but not yet its
#: opacity (WP-30 P1.4a carried it to them).
_NOT_YET_OPACITY = ("rspike", "rcap", "rarea", "spike", "dropline", "lfit",
                    "lfitci", "kdensity", "function", "scatteri", "pci",
                    "pcspike", "mband")


@pytest.mark.parametrize("mode", _MODES)
class TestTheSchemeOpacityStopsWhereTheHelpSays:

    @pytest.mark.parametrize("ptype", _NOT_YET_OPACITY)
    def test_the_colour_and_the_opacity(self, tmp_path, mode, ptype):
        """Under sttrans the second layer is drawn in sttrans' p2, #cc6677,
        at its declared %20 -- twoway's stroke-opacity and fill-opacity
        0.20 (measured 03oct2026) -- and under s2color, which declares
        none, opaque.  lfitci's band is not in p2: it is the scheme's ci
        style, opaque gs12 under both, as twoway draws it.

        Flipped (WP-30 P1.4a): this was test_the_colour_but_not_the_opacity,
        which expected sttrans' alphas to equal s2color's; twoway draws
        these layers at 0.20."""
        trans = _layer_styles(mode, tmp_path / "t",
                              _two_layer(ptype, "sttrans"), "t" + ptype)
        plain = _layer_styles(mode, tmp_path / "p",
                              _two_layer(ptype, "s2color"), "p" + ptype)
        if ptype == "lfitci":
            assert ("#c0c0c0", 1.0) in trans and ("#c0c0c0", 1.0) in plain
            trans = [s for s in trans if s[0] != "#c0c0c0"]
            plain = [s for s in plain if s[0] != "#c0c0c0"]
        # rarea's fill is p2 at its p2area intensity, inten80 (WP-30 P1.2b;
        # twoway's SVG, plan section 16 Evidence E3).
        want_t, want_p = (("#d68592", "#a65d62") if ptype == "rarea"
                          else ("#cc6677", "#90353b"))
        # Flipped (WP-31 E8): rarea's outline Lines are p2 itself, at the
        # scheme's opacity, as twoway strokes the polygon (fixture
        # ol.rarea_p2).
        _ol_t, _ol_p = ({"#cc6677"}, {"#90353b"}) if ptype == "rarea" \
            else (set(), set())
        assert trans and {c for c, _a in trans} == {want_t} | _ol_t, trans
        assert plain and {c for c, _a in plain} == {want_p} | _ol_p, plain
        assert all(abs(a - 0.2) < 1e-9 for _c, a in trans), trans
        assert {a for _c, a in plain} == {1.0}, plain

    def test_malpha_wins_over_the_declared_opacity(self, tmp_path, mode):
        spec = _one_graph([{"type": "scatter", "yvar": "mpg",
                            "xvar": "weight", "options": {"malpha": "50"}}],
                          build={"scheme": "sttrans"})
        fig = _figure(mode, tmp_path, spec, tag="malpha")
        g = [r.glyph for r in fig.renderers if hasattr(r, "glyph")][0]
        assert g.fill_alpha == pytest.approx(0.5)


@pytest.mark.parametrize("mode", _MODES)
class TestAFunctionTakesItsPlaceInTheCycle:
    """dash.sthlp: the series take the scheme's p1..p15 cycle.  Measured in
    Stata 19.5 under s2color: `twoway (scatter) (function)' draws the
    function in p2's #90353B, first it is p1's #1A476F, third p3's #55752F.
    dash drew every function in p1's colour, wherever it stood."""

    @pytest.mark.parametrize("position,colour", [
        (0, "#1a476f"), (1, "#90353b"), (2, "#55752f")])
    def test_the_function_is_drawn_in_its_positions_colour(
            self, tmp_path, mode, position, colour):
        fn = {"type": "function", "expr": "20", "options":
              {"range": "2000 4000"}}
        sc = [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
               "options": {"mcolor": "black"}} for _ in range(position)]
        spec = _one_graph(sc + [fn], build={"scheme": "s2color"})
        fig = _figure(mode, tmp_path, spec, tag="fn%d" % position)
        lines = [r.glyph for r in fig.renderers
                 if type(getattr(r, "glyph", None)).__name__ == "Line"]
        assert [g.line_color.lower() for g in lines] == [colour]


@pytest.mark.parametrize("mode", _MODES)
class TestARangeLineIsOneSeries:
    """twoway draws both boundaries of rline, rconnected and tsrline -- and
    rconnected's markers at both ends -- in the layer's own pstyle.
    Measured in Stata 19.5 under s2color: first, every path and marker is
    p1's #1A476F; after a scatter, p2's #90353B.  dash drew the upper
    boundary in the NEXT series' colour (and, for rconnected, its symbol)."""

    @pytest.mark.parametrize("ptype", ["rline", "rconnected", "tsrline"])
    @pytest.mark.parametrize("position,colour", [(0, "#1a476f"),
                                                 (1, "#90353b")])
    def test_both_boundaries_take_the_layers_colour(self, tmp_path, mode,
                                                    ptype, position, colour):
        from test_every_plot_type_draws import _DATA, _plot_for
        df = pd.DataFrame(_DATA["values"])
        sc = [{"type": "scatter", "yvar": "y", "xvar": "x",
               "options": {"mcolor": "black"}}] * position
        spec = _one_graph(sc + [_plot_for(ptype)],
                          build={"scheme": "s2color"})
        fig = _figure(mode, tmp_path, spec, df,
                      tag="%s%d" % (ptype, position))
        cols = set()
        for r in fig.renderers:
            g = getattr(r, "glyph", None)
            for a in ("line_color", "fill_color"):
                c = getattr(g, a, None)
                if isinstance(c, str) and c.startswith("#"):
                    cols.add(c.lower())
        cols.discard("#000000")
        assert cols == {colour}, cols

    def test_rconnected_draws_one_symbol(self, tmp_path, mode):
        from test_every_plot_type_draws import _DATA, _plot_for
        df = pd.DataFrame(_DATA["values"])
        spec = _one_graph([_plot_for("rconnected")],
                          build={"scheme": "s2mono"})
        fig = _figure(mode, tmp_path, spec, df, tag="rconsym")
        markers = {r.glyph.marker for r in fig.renderers
                   if type(getattr(r, "glyph", None)).__name__ == "Scatter"}
        assert len(markers) == 1, markers


@pytest.mark.parametrize("mode", _MODES)
class TestAGridTheOptionTurnsOnIsTheSchemes:

    def test_ylabel_grid_under_a_scheme_that_draws_none(self, tmp_path,
                                                        mode):
        spec = _scatter({"ylabel": ", grid"}, build={"scheme": "s1color"})
        fig = _figure(mode, tmp_path, spec, tag="ygrid")
        want = dr.SchemeParser("s1color").grid_color
        assert [g.grid_line_color for g in fig.ygrid] == [want]
        assert [g.grid_line_color for g in fig.xgrid] == [None]


@pytest.mark.parametrize("mode", _MODES)
class TestAnExplicitOptionBeatsTheScheme:
    """Under economist, whose every default differs from s2color's."""

    def test_bgcolor_and_plotregion(self, tmp_path, mode):
        # Flipped (WP-30 P1.20a): a lone bgcolor(red) on the border was
        # wrong because twoway paints bgcolor() under the graph region (region_truth.json D26-D29); it shows where the
        # graph region is none, and alone it changes nothing visible.
        spec = _scatter({"bgcolor": "red", "plotregion": "color(blue)",
                         "graphregion": "color(none)"},
                        build={"scheme": "economist"})
        fig = _figure(mode, tmp_path, spec, tag="regions")
        assert fig.border_fill_color.lower() == "#ff0000"
        assert fig.background_fill_color.lower() == "#0000ff"

    def test_lwidth(self, tmp_path, mode):
        spec = _one_graph([{"type": "line", "yvar": "mpg", "xvar": "weight",
                            "options": {"lwidth": "vthin"}}],
                          build={"scheme": "economist"})
        fig = _figure(mode, tmp_path, spec, tag="lwidth")
        g = [r.glyph for r in fig.renderers if hasattr(r, "glyph")][0]
        assert g.line_width == dr.OptionTranslator.translate_lwidth("vthin")
        assert g.line_width < dr.SchemeParser("economist").default_line_width

    def test_title_size_and_colour(self, tmp_path, mode):
        spec = _scatter({"title": "T, size(small) color(green)"},
                        build={"scheme": "economist"})
        fig = _figure(mode, tmp_path, spec, tag="title")
        assert fig.title.text == "T"
        assert fig.title.text_color.lower() in ("#008000", "green")
        assert fig.title.text_font_size != dr.SchemeParser(
            "economist").heading_font_size


def _custom_scheme(src_name, background):
    """A shipped scheme's text with its background replaced."""
    out = []
    for ln in _read(os.path.join(_SCHEMES, "dash-" + src_name + ".scheme")).splitlines():
        if re.match(r"^color background\s", ln):
            ln = "color background      %s" % background
        out.append(ln)
    return "\n".join(out) + "\n"


def _chrome_and_figure(mode, tmp_path, spec, tag):
    """(page text, figure background) in *mode*."""
    if mode == "saved":
        fig, html, _w = _saved_figure(tmp_path, spec)
        return html, fig.border_fill_color
    fig, doc = _served_figure(tmp_path, spec, tag=tag)
    return str(doc.to_json()), fig.border_fill_color


@pytest.mark.parametrize("mode", _MODES)
class TestAWorkingDirectorySchemeWinsOverAShippedOne:
    """WP-30 P1.25b reversed the claim this class was named for: a file in
    the working directory named like a shipped scheme no longer replaces it,
    as it never does in twoway, whose BASE comes first (dash.sthlp: "no
    longer wins over the shipped one").  test_installed_layout.py pins the
    lookup on an installed tree; this renders it, in both modes, from a
    checkout."""

    @pytest.mark.parametrize("where", ["build", "graph"])
    def test_s2color_in_the_working_directory(self, tmp_path, monkeypatch,
                                              mode, where):
        wd = tmp_path / "wd"
        wd.mkdir()
        (wd / "s2color.scheme").write_text(_custom_scheme("s2color",
                                                          "#123456"))
        monkeypatch.chdir(wd)
        spec = (_scatter(build={"scheme": "s2color"}) if where == "build"
                else _scatter({"scheme": "s2color"}))
        page, bg = _chrome_and_figure(mode, tmp_path, spec, "wd" + where)
        assert bg.lower() == dr.SchemeParser("s2color").background_color.lower()
        assert "#123456" not in page.lower()


class TestWhatAnIncludeResolvesTo:
    """A user file's #include resolves as scheme() does (WP-30 P1.25b): a
    shipped translation first, whatever file of that name is in the working
    directory, then Stata's scheme-<name>.scheme and <name>.scheme along the
    ado-path; one that resolves nowhere is read as s2color, with Stata's
    note."""

    @staticmethod
    def _parse(wd, text, monkeypatch):
        (wd / "mine.scheme").write_text(text)
        monkeypatch.chdir(wd)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            sch = dr.SchemeParser("mine")
        return sch, [str(x.message) for x in w]

    def test_the_working_directory_first(self, tmp_path, monkeypatch):
        wd = tmp_path / "wd"
        wd.mkdir()
        (wd / "s2color.scheme").write_text(_custom_scheme("s2color",
                                                          "#abcdef"))
        sch, w = self._parse(wd, "#include s2color\n", monkeypatch)
        # WP-30 P1.25b: the translation, never the working-directory file.
        assert (sch.background_color.lower()
                == dr.SchemeParser("s2color").background_color.lower()), w

    def test_then_a_shipped_translation(self, tmp_path, monkeypatch):
        wd = tmp_path / "wd"
        wd.mkdir()
        sch, w = self._parse(wd, "#include s2color\n", monkeypatch)
        assert (sch.background_color.lower()
                == dr.SchemeParser("s2color").background_color.lower())

    def test_never_statas_own_prefixed_file(self, tmp_path, monkeypatch):
        wd = tmp_path / "wd"
        wd.mkdir()
        (wd / "scheme-zzinc.scheme").write_text(
            "#include s2color\ncolor background #ff00ff\n")
        sch, w = self._parse(
            wd, "#include zzinc\ncolor p1 #112233\n", monkeypatch)
        # WP-30 P1.25b: Stata's setscheme tries scheme-NAME.scheme first.
        assert sch.background_color.lower() == "#ff00ff"
        assert sch.p_colors[0].lower() == "#112233"

    def test_an_include_that_resolves_to_nothing_stands_s2color_in(
            self, tmp_path, monkeypatch):
        """As Stata does (measured 24sep2026, `#include w26nosuch': "(note:
        scheme w26nosuch not found, using s2color)", rc 0, s2color drawn):
        s2color in its place, and Stata's note.  It used to be skipped in
        silence, which dash.sthlp said."""
        wd = tmp_path / "wd"
        wd.mkdir()
        sch, w = self._parse(
            wd, "#include w26nosuch\ncolor p1 #445566\n", monkeypatch)
        s2 = dr.SchemeParser("s2color")
        assert sch.p_colors[0].lower() == "#445566"
        assert sch.p_colors[1:] == s2.p_colors[1:]
        assert sch.background_color == s2.background_color
        assert (sch.graphsize_x, sch.graphsize_y) == (5.5, 4.0)
        assert any("(note: scheme w26nosuch not found, using s2color)"
                   in m for m in w), w
        help_text = re.sub(r"\s+", " ", _read(_HELP))
        assert "skipped in silence" not in help_text
        assert "(note: scheme} {it:name} {cmd:not found, using s2color)" \
            in help_text

    def test_colours_may_be_names_or_hex(self, tmp_path, monkeypatch):
        wd = tmp_path / "wd"
        wd.mkdir()
        sch, w = self._parse(
            wd, "#include s2color\ncolor p1 maroon\ncolor p2 #0a0b0c\n",
            monkeypatch)
        assert sch.p_colors[0].lower() == dr.OptionTranslator.translate_mcolor(
            "maroon").lower()
        assert sch.p_colors[1].lower() == "#0a0b0c"


class TestTheShippedFiles:

    @pytest.mark.parametrize("name", sorted(dr.SchemeParser._BUILTIN_NAMES))
    def test_the_directive_count_is_what_the_help_says(self, name):
        """100 to 170 directives, measured: 109 for the colour schemes
        (110 for s2color, 113 for economist), 139 to 141 for the
        monochrome ones, whose chains declare a connecting-line colour or
        pattern, a line-plot cycle and their marker symbols, 148 for
        s1manual, which declares symbolsize p1..p9, and 168 for s2gmanual,
        which declares every p#line and p#lineplot key.  They moved with
        WP-30 P1.2a's chrome keys (twenty-four more), P1.3a's three axis
        keys and P1.4a's four histogram keys, and lost graph bar's
        `intensity bar' and `intensity area' (P1.4a), which twoway's bar
        and area do not read.  WP-30 P1.4b added `gsize plabel' to every
        file and `color plabel' to the nine monochrome ones (s2gmanual
        168 -> 170, the bound).  Renamed (WP-30 P1.4a) from
        test_80_to_140_directives, whose name had outlived its bounds.
        WP-30 P1.14b carried the keys the named styles read: 219 to 279
        directives, measured over the 26 regenerated files."""
        n = sum(1 for k, _v in _directives(os.path.join(_SCHEMES,
                                                        "dash-" + name + ".scheme"))
                if not k.startswith(("sequence", "label")))
        # Flipped (WP-30 P1.14b): 100 to 170 was wrong because the files
        # now carry the keys Stata's style files read for the named styles.
        # 100..170 -> 210..280: P1.14b named-style keys (219 to 279,
        # rounded outward to ten).
        # Flipped (WP-30 P1.24): 210 to 280 was wrong because the files
        # now carry the keys the text box styles read for mlabtextstyle().
        # 210..280 -> 250..320: P1.24 textbox keys (251 to 311, rounded
        # outward to ten).
        # WP-30 P1.20b: the margin ladder (gsize *margin) is read now:
        # 250..320 -> 260..330 (262 to 322, rounded outward to ten).
        # Flipped (WP-30 P1.15c): 260..330 -> 280..350: P1.15c by() keys
        # (286 to 346, rounded outward to ten).
        # Flipped (WP-30 P1.10): 280..350 -> 290..360: text()'s six
        # text_option keys (292 to 352, rounded outward to ten).
        # WP-31 D2: the eight edge titles' textbox styles:
        # 290..360 -> 300..370 (300 to 366, rounded outward to ten).
        # Flipped (WP-31 D4): 300..370 -> 310..380: the ten legend
        # geometry keys twoway's legend_g reads (316 to 376, rounded
        # outward to ten).
        # Flipped (WP-31 D7): 310..380 -> 310..390: gsize axis_title_gap
        # (317 to 381, rounded outward to ten).
        assert 310 <= n <= 390, (name, n)
        help_text = _read(_HELP)
        assert re.search(r"310\s+to\s+390\s+directives", help_text)

    def test_the_s2mono_family_is_what_includes_s2mono(self):
        for name in _S2MONO_FAMILY:
            src = _stata_file("s/scheme-%s.scheme" % name)
            chain, cur = [], src
            while True:
                m = re.search(r"^#include\s+(\S+)", cur, re.M)
                if not m:
                    break
                chain.append(m.group(1))
                cur = _stata_file("s/scheme-%s.scheme" % m.group(1))
            assert "s2mono" in chain or name == "s2mono", (name, chain)

    def test_statas_s2color_has_2060(self):
        n = sum(1 for ln in _stata_file("s/scheme-s2color.scheme").splitlines()
                if ln.strip() and not ln.strip().startswith("*"))
        assert n == 2060, n

    @pytest.mark.parametrize("name", sorted(dr.SchemeParser._BUILTIN_NAMES))
    def test_the_include_chain_is_flattened(self, name):
        assert not re.search(r"^\s*#include",
                             _read(os.path.join(_SCHEMES, "dash-" + name + ".scheme")),
                             re.M)

    @pytest.mark.parametrize("name", sorted(dr.SchemeParser._BUILTIN_NAMES))
    def test_every_colour_is_rrggbb(self, name):
        for k, v in _directives(os.path.join(_SCHEMES, "dash-" + name + ".scheme")):
            if k.startswith("color "):
                # `none' is Stata's own colour for no line: economist's
                # plot region has no border.
                if k == "color plotregion_line" and v.split()[0] == "none":
                    assert name == "economist", (name, k, v)
                    continue
                # Flipped (WP-30 P1.14b): "only economist's plot-region
                # border is none" was wrong because the named styles carry
                # `color pieline' and `color fpspacer', which every Stata
                # scheme declares as none.
                if k in ("color pieline", "color fpspacer"):
                    assert v.split()[0] == "none", (name, k, v)
                    continue
                # sttrans' histogram keys carry the %20 too (WP-30 P1.4a).
                pat = (r"#[0-9a-f]{6}%20" if name == "sttrans"
                       and re.fullmatch(r"color (p\d*(line|bar|mark)?"
                                        r"|histogram(_line)?)", k)
                       else r"#[0-9a-f]{6}")
                assert re.fullmatch(pat, v.split()[0].lower()), (name, k, v)

    @pytest.mark.parametrize("mode", _MODES)
    def test_some_uncarried_directives_govern_what_dash_draws_its_own_way(
            self, tmp_path, mode):
        """Stata's s2color declares `color refline' and `color ci_area';
        no shipped file carries the first.  (xline() and yline() are not
        refline: twoway draws them in `linestyle xyline', which the
        shipped files do carry -- the S3 batch -- as they carry the ci
        band's keys.)"""
        src = _stata_file("s/scheme-s2color.scheme")
        assert re.search(r"^color refline\s", src, re.M)
        assert re.search(r"^color ci_area\s", src, re.M)
        assert re.search(r"^linestyle xyline\s+xyline\s", src, re.M)

    @pytest.mark.parametrize("mode", _MODES)
    def test_some_uncarried_directives_govern_what_dash_draws_its_own_way_in_dash(
            self, tmp_path, mode):
        """The half that needs no Stata (see TestTheSchemeTableSaysWhat-
        StataSays): every shipped file carries `color refline' (WP-30
        P1.14b: lstyle(refline) draws it) and
        carries `color ci_area' (the S3 batch's ci band); xline()
        takes the scheme's `color xyline' and `linepattern xyline' --
        s2color's cranberry and solid, as twoway draws it (measured
        24sep2026 from its SVG export)."""
        for name in dr.SchemeParser._BUILTIN_NAMES:
            keys = {k for k, _v in _directives(
                os.path.join(_SCHEMES, "dash-" + name + ".scheme"))}
            # Flipped (WP-30 P1.14b): "not in keys" was wrong because
            # lstyle(refline) draws `color refline' now.
            assert "color refline" in keys, name
            assert "color ci_area" in keys, name
            assert {"color xyline", "linepattern xyline"} <= keys, name
        fig = _figure(mode, tmp_path, _scatter({"xline": "3000"},
                                               build={"scheme": "s2color"}),
                      tag="refline")
        spans = [m for m in fig.center if type(m).__name__ == "Span"]
        assert spans and spans[0].line_color.lower() == "#c10534"
        assert list(spans[0].line_dash) == []

    def test_no_directive_for_what_dash_does_not_draw(self):
        """graph bar/box/pie/dot/matrix styling, margins."""
        # Flipped (WP-30 P1.14b): "no key matches" was wrong because the
        # named styles' group carries the line styles of those names
        # (lstyle(tick), lstyle(pie), lstyle(dot) ... draw them); the
        # pattern holds outside that group, read from the fixture.
        with open(os.path.join(_ROOT, "test", "fixtures",
                               "scheme_truth.json"), encoding="utf-8") as fh:
            truth = json.load(fh)
        keys = set()
        named = set()
        # Flipped (WP-30 P1.24): the text box styles' keys (matrix_label,
        # pbarlabel, pboxlabel ...) are drawn now, by mlabtextstyle().
        textbox = {f"{c} {k}" for k in
                   {k for pair in dr.SchemeParser._TEXTBOX_STYLES.values()
                    for k in pair} | {"pbarlabel", "pboxlabel"}
                   for c in ("gsize", "color")}
        # WP-30 P1.20b: the margin ladder (gsize tinymargin ...) is read
        # by margin_sides() for the marginstyle names now.
        ladder = {f"gsize {k}" for k in dr.SchemeParser._MARGIN_LADDER}
        for name in dr.SchemeParser._BUILTIN_NAMES:
            group = (set(truth[name]["named_style_directives"]) | textbox
                     | ladder)
            named |= group
            keys |= {k for k, _v in _directives(
                os.path.join(_SCHEMES, "dash-" + name + ".scheme"))
                if k not in group}
        assert {k for k in named if k.split()[0] in
                ("color", "linewidth", "linepattern")
                and re.search(r"pie|\bdot|matrix|tick", k)}, named
        bad = sorted(k for k in keys if re.search(
            # WP-30 P1.3a: `margin twoway' is drawn now (the plot-region
            # margin), so it is no longer in this list.  Flipped (WP-30
            # P1.15c): `margin by_indiv' (the space between by() panels)
            # and `margin subheading' (the panel label's box) are drawn
            # too, by the "by() axes and keys (WP-30 P1.15c)" group.
            # Flipped (WP-30 P1.10): `margin text_option' (text()'s box)
            # is drawn now.
            r"(?<!text)box|pie|\bdot|matrix|"
            # Flipped (WP-31 D4): `margin legend' and `margin
            # legend_boxmargin' are the legend box's inner and outer
            # margins, drawn as its padding and margin.
            # Flipped (WP-31 D11): `margin graph' is the graph region's
            # margin, drawn as the figure's borders (_dash_graph_margin).
            r"margin(?! twoway| by_indiv| subheading| text_option| legend"
            r"| graph)|"
            r"barlabel|"
            r"barstyle|bar_",
            k))
        # Flipped (WP-31 B5b): `symbol dots' and `symbolsize dots' are
        # carried because dash draws twoway dot's rows of dots in them
        # (SchemeParser.dots_style; test_dot_rows.py).
        bad = [k for k in bad if k not in ("symbol dots", "symbolsize dots")]
        # Flipped (WP-31 D4): `margin legend_boxmargin' is the space
        # around the legend box, drawn as its Bokeh margin.
        bad = [k for k in bad if k != "margin legend_boxmargin"]
        assert not bad, bad  # P1.2a: the scheme's tick keys are carried and drawn


class TestAnInstalledTreeLooksOnlyForItsOwnTwenty:
    """test_installed_layout.py stages fourteen of the twenty-six; this
    stages all twenty-six where `net install` files them, plants a third-party scheme
    beside them, and asks for each."""

    def test_all_twenty_and_nothing_else(self, tmp_path, monkeypatch):
        import shutil
        from test_packaging import load_staged_render
        root = tmp_path / "plus"
        (root / "py").mkdir(parents=True)
        shutil.copy2(os.path.join(_ROOT, "dash_render.py"),
                     str(root / "py" / "dash_render.py"))
        names = sorted(dr.SchemeParser._BUILTIN_NAMES)
        assert len(names) == 26  # 20 -> 26: P1.25a ships the six StataCorp schemes
        for name in names:
            (root / "d").mkdir(exist_ok=True)
            shutil.copy2(os.path.join(_SCHEMES, "dash-" + name + ".scheme"),
                         str(root / "d" / ("dash-" + name + ".scheme")))
        (root / "s").mkdir()
        (root / "s" / "scheme-zzthird.scheme").write_text(
            "#include s2color\ncolor background #ff00ff\n")
        (root / "z").mkdir()
        (root / "z" / "zzthird.scheme").write_text(
            "color background #ff00ff\n")
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        monkeypatch.chdir(elsewhere)
        mod_name, mod = load_staged_render(str(root / "py"))
        try:
            for name in names:
                sch = mod.SchemeParser(name)
                assert sch.is_fallback is False and sch.name == name
            assert not mod.SchemeParser.can_resolve("zzthird")
            assert not mod.SchemeParser.can_resolve("scheme-zzthird")
            # WP-30 P1.25b: along the ado-path it is found, as Stata does.
            assert mod.SchemeParser.can_resolve("zzthird",
                                                ado_dirs=(str(root),))
        finally:
            sys.modules.pop(mod_name, None)


class TestTheUnitsAreStatas:
    """Stata's own style files and size help, which the Units paragraph
    restates; dash's conversions are pinned by test_scheme_rendered_output
    (TestTheUnitFunctions) and test_scheme_review_fixes (TestNumericGsize)."""

    def test_100_is_the_smaller_dimension(self):
        assert ("size 100 = minimum of width and height of graph"
                in _flat(_stata_file("s/size.sthlp")))

    # Each test that reads Stata's style files has an ``..._in_dash``
    # sibling for the half that reads only dash (see TestTheSchemeTable-
    # SaysWhatStataSays): it was skipped with the Stata half.

    def test_medium_text_is_3_8194_or_11_point(self):
        src = _stata_file("style/gsize-medium.style")
        assert re.search(r"set val\s+3\.8194\b", src)
        assert "11 pt based on a 4 inch high graph" in src

    def test_medium_text_is_3_8194_or_11_point_in_dash(self):
        # Flipped (WP-31 E13): one constant, OptionTranslator.PT_PER_RS.
        assert dr.OptionTranslator.PT_PER_RS == 2.88
        assert round(3.8194 * 2.88, 1) == 11.0
        assert round(6.0 * 2.88, 2) == 17.28

    def test_a_large_marker_is_7_point_and_medium_4_4(self):
        large = _stata_file("style/symbolsize-large.style")
        medium = _stata_file("style/symbolsize-medium.style")
        lv = float(re.search(r"set val\s+([\d.]+)", large).group(1))
        mv = float(re.search(r"set val\s+([\d.]+)", medium).group(1))
        assert round(lv * 2.88, 1) == 7.0 and round(mv * 2.88, 1) == 4.4

    def test_a_large_marker_is_7_point_and_medium_4_4_in_dash(self):
        assert dr.SchemeParser._SYMBOLSIZE_PT["large"] == 7.0
        assert dr.SchemeParser._SYMBOLSIZE_PT["medium"] == 4.4

    def test_a_medium_line_is_0_30(self):
        src = _stata_file("style/linewidth-medium.style")
        assert re.search(r"set val\s+\.30\b", src)

    def test_a_medium_line_is_0_30_in_dash(self):
        assert "linewidth p" in dict(_directives(
            os.path.join(_SCHEMES, "dash-economist.scheme")))

    def test_the_series_share_one_line_width(self):
        """The corrected Series paragraph: a scheme sets one line width,
        `linewidth p', not a per-series cycle -- no shipped file and none
        of Stata's twenty declares `linewidth p<N>' (economist's p<N>solid
        are a different style, all medium)."""
        for name in dr.SchemeParser._BUILTIN_NAMES:
            src = _stata_file("s/scheme-%s.scheme" % name)
            assert not re.search(r"^linewidth p\d+\s", src, re.M), name

    def test_the_series_share_one_line_width_in_dash(self):
        for name in dr.SchemeParser._BUILTIN_NAMES:
            keys = {k for k, _v in _directives(
                os.path.join(_SCHEMES, "dash-" + name + ".scheme"))}
            assert not [k for k in keys
                        if re.fullmatch(r"linewidth p\d+", k)], name
        sec = _flat(_help_between("{marker scheme}", "{marker unsupported}"))
        assert "line-width cycles" not in sec
        # ... and a user's `linewidth p#' reaches plot #'s line (S3 batch,
        # test/test_scheme_linewidth.py).
        assert ("the line width ({cmd:linewidth p}, and "
                "{cmd:linewidth p}{it:#} per plot)") in sec


class TestDashDrawsBokehsMinorTicks:
    """WP-30 P1.3a: an axis with its default labels no longer keeps Bokeh's
    minor ticks -- twoway draws them only for xmtick() or ymtick() -- so the
    old disclosure (BasicTicker with minor ticks) was wrong: the default
    axis is ticked by natscale on a FixedTicker with no minor ticks."""

    @pytest.mark.parametrize("mode", _MODES)
    def test_the_default_axis_has_minor_ticks(self, tmp_path, mode):
        fig = _figure(mode, tmp_path, _scatter(), tag="minor")
        for ax in (fig.xaxis[0], fig.yaxis[0]):
            assert isinstance(ax.ticker, FixedTicker)
            assert list(ax.ticker.minor_ticks) == []

    def test_the_help_says_so(self):
        sec = _flat(_help_between("{marker scheme}", "{marker unsupported}"))
        assert "minor ticks" in sec and "{cmd:xmtick()}" in sec


# ===========================================================================
# 4. The Unsupported section
# ===========================================================================

def _served_fingerprint(tmp_path, spec, df, tag):
    """A served document with its model ids taken out."""
    import hashlib
    d = tmp_path / tag
    d.mkdir(parents=True, exist_ok=True)
    ns = _load_app(_app_source(d, spec, df), re.sub(r"\W", "_", tag))
    doc = _session(ns)

    def _plain(o):
        if isinstance(o, memoryview):
            return bytes(o).hex()
        if hasattr(o, "__dict__"):
            return o.__dict__
        return repr(o)
    txt = json.dumps(doc.to_json(), sort_keys=True, default=_plain)
    txt = re.sub(r"\bp\d{3,7}\b", "PID", txt)
    txt = re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-"
                 r"[0-9a-f]{12}", "UUID", txt)
    return hashlib.sha256(txt.encode()).hexdigest()


def _pending_names(program):
    src = _read(_ADO)
    i = src.index("program define " + program)
    j = src.index("local _dash_unknown", i)
    return re.findall(r"_dash_pending' (\w+)\"", src[i:j])


#: A pending option whose probe needs the thing it would modify: labels for
#: the label options, a colour variable for the colorvar() sub-options.
_CONTEXT = {"mlabwidth": {"mlabel": "foreign"},
            "mlabtextstyle": {"mlabel": "foreign"},
            "mlabvposition": {"mlabel": "foreign"},
            "colorlist": {"colorvar": "price"},
            "coloruseplegend": {"colorvar": "foreign",
                                "colordiscrete": "colordiscrete"}}


def _served_pair(tmp_path, opt, level):
    from test_unsupported_report_is_true import _DF as UDF, FLAGS, PLOT_VALUES
    a, b, ptype = PLOT_VALUES[opt]
    ctx = dict(_CONTEXT.get(opt, {}))
    pairs = ([({opt: opt}, "on"), ({}, "off")] if opt in FLAGS
             else [({opt: a}, "a"), ({opt: b}, "b")])
    out = []
    for vals, tag in pairs:
        popts, gopts = dict(ctx), {}
        (popts if level == "plot" else gopts).update(vals)
        spec = {"graphs": [{"graph_options": dict(gopts, name="g1"),
                            "plots": [{"type": ptype, "yvar": "mpg",
                                       "xvar": "weight", "options": popts,
                                       # WP-31 B4b: contour's z.
                                       **({"zvar": "price"} if ptype in (
                                           "contour", "contourline")
                                          else {})}],
                            "if_expr": "", "in_expr": ""}],
                "kpis": [],
                "build_options": {"layout": "auto", "registry": "g1",
                                  "level": "95"}}
        out.append(_served_fingerprint(tmp_path, spec, UDF,
                                       "%s_%s_%s" % (level, opt, tag)))
    return out


class TestAnUnsupportedOptionIsInertWhenServed:
    """test_unsupported_report_is_true.py proves each listed option leaves
    the SAVED page unchanged; the help's "accepted and not honoured" is a
    claim about the served app too, which nothing checked."""

    @pytest.mark.parametrize("opt", sorted(set(_pending_names(
        "_dash_parse_plot_opts"))))
    def test_plot_level(self, tmp_path, opt):
        first, second = _served_pair(tmp_path, opt, "plot")
        assert first == second, "plot-level %s() changes the served app" % opt

    @pytest.mark.parametrize("opt", sorted(set(_pending_names(
        "_dash_parse_graph_opts"))))
    def test_graph_level(self, tmp_path, opt):
        first, second = _served_pair(tmp_path, opt, "graph")
        assert first == second, "graph-level %s() changes the served app" % opt

    def test_the_fingerprint_sees_a_live_option(self, tmp_path):
        """Guards the guard: mcolor() must change it."""
        from test_unsupported_report_is_true import _DF as UDF
        fps = []
        for col in ("red", "blue"):
            spec = _one_graph([{"type": "scatter", "yvar": "mpg",
                                "xvar": "weight",
                                "options": {"mcolor": col}}])
            fps.append(_served_fingerprint(tmp_path, spec, UDF, "live" + col))
        assert fps[0] != fps[1]


@pytest.mark.parametrize("mode", _MODES)
class TestTheUnsupportedProseIsTrue:

    @pytest.mark.parametrize("opts", [{}, {"fxsize": "50", "scale": "1.5"}])
    def test_a_figure_stretches_to_the_width_it_is_given(self, tmp_path,
                                                         mode, opts):
        fig = _figure(mode, tmp_path, _scatter(opts), tag="stretch")
        assert fig.sizing_mode == "stretch_width"

    @pytest.mark.parametrize("flag", ["", "horizontal"])
    def test_bars_are_drawn_vertically_at_the_x_values(self, tmp_path, mode,
                                                       flag):
        """Flipped (WP-30 P1.9a): a VBar under horizontal was wrong because
        twoway turns the bars (horizontal_truth.json draw bar); they are
        an HBar at the x values, which run on the y axis."""
        opts = {"horizontal": "horizontal"} if flag else {}
        spec = _one_graph([{"type": "bar", "yvar": "mpg", "xvar": "weight",
                            "options": opts}])
        fig = _figure(mode, tmp_path, spec, tag="bar" + flag)
        cls, at = ("HBar", "y") if flag else ("VBar", "x")
        bars = [r for r in fig.renderers
                if type(getattr(r, "glyph", None)).__name__ == cls]
        assert len(bars) == 1
        g = bars[0].glyph
        xs = sorted(float(v) for v in bars[0].data_source.data[
            getattr(g, at)])
        assert xs == sorted(_DF["weight"].tolist())

    @pytest.mark.parametrize("ptype", ["line", "connected"])
    def test_a_missing_observation_is_dropped_so_the_line_joins_across_it(
            self, tmp_path, mode, ptype):
        """twoway's default, cmissing(y): one unbroken line (HC8-20
        measures twoway).  Dropped, not passed on as NaN, which Bokeh would
        draw as a break -- cmissing(n)'s picture."""
        df = pd.DataFrame({"y": [1.0, 2.0, np.nan, 4.0, 5.0],
                           "x": [1.0, 2.0, 3.0, 4.0, 5.0]})
        spec = _one_graph([{"type": ptype, "yvar": "y", "xvar": "x",
                            "options": {}}])
        fig = _figure(mode, tmp_path, spec, df, tag="miss" + ptype)
        lines = [r for r in fig.renderers
                 if type(getattr(r, "glyph", None)).__name__ == "Line"]
        assert lines
        d = lines[0].data_source.data
        ys = [float(v) for v in d[lines[0].glyph.y]]
        assert ys == [1.0, 2.0, 4.0, 5.0]

    def test_a_spike_is_drawn_upright_even_with_horizontal(self, tmp_path,
                                                           mode):
        """Flipped (WP-30 P1.9a): an upright spike under horizontal was
        wrong because twoway turns it (horizontal_truth.json draw spike):
        its segments are horizontal, y0 == y1."""
        spec = _one_graph([{"type": "spike", "yvar": "mpg", "xvar": "weight",
                            "options": {"horizontal": "horizontal"}}])
        fig = _figure(mode, tmp_path, spec, tag="spikeh")
        segs = [r for r in fig.renderers
                if type(getattr(r, "glyph", None)).__name__ == "Segment"]
        assert segs
        g, d = segs[0].glyph, segs[0].data_source.data
        assert list(d[g.y0]) == list(d[g.y1])      # horizontal segments

    def test_a_markers_outline_is_drawn_solid(self, tmp_path, mode):
        spec = _one_graph([{"type": "scatter", "yvar": "mpg",
                            "xvar": "weight",
                            "options": {"mlpattern": "dash"}}])
        fig = _figure(mode, tmp_path, spec, tag="mlpat")
        g = [r.glyph for r in fig.renderers
             if type(getattr(r, "glyph", None)).__name__ == "Scatter"][0]
        assert list(g.line_dash) == []

    def test_xtick_widens_the_axis(self, tmp_path, mode):
        """As twoway: a tick mark outside the data widens the axis to show
        it (GAPS2 B2; the old exception was dropped when B2 was fixed)."""
        fig = _figure(mode, tmp_path, _scatter({"xtick": "1000 6000"}),
                      tag="wide")
        assert fig.x_range.start <= 1000.0 and fig.x_range.end >= 6000.0
        assert _tick_plan(fig.xaxis[0])[1] == [1000.0, 6000.0]

    def test_xscale_alt_is_drawn_and_reverse_honoured(self, tmp_path, mode):
        # Flipped (WP-30 P1.18a), was test_xscale_alt_is_named_and_reverse_
        # honoured: twoway draws xscale(alt) above the plot, unnamed.
        spec = _scatter({"xscale": "alt"})
        if mode == "saved":
            fig, _html, msgs = _saved_figure(tmp_path, spec)
        else:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                fig = _served_figure(tmp_path, spec, tag="alt")[0]
            msgs = [str(x.message) for x in w]
        assert not any("xscale() sub-option" in m for m in msgs), msgs
        xs = [a for a in fig.above
              if getattr(a, "x_range_name", "default") == "default"
              and type(a).__name__.endswith("Axis")]
        assert xs, fig.above
        fig = _figure(mode, tmp_path / "rev", _scatter({"xscale": "reverse"}),
                      tag="rev")
        # WP-30 P1.3a: a flipped DataRange1d is now a Range1d high to low.
        assert fig.x_range.start > fig.x_range.end


class TestTheUnsupportedSectionSaysWhatTwowayDoes:
    """The corrected prose, pinned; HC8-02 to HC8-05, HC8-14, HC8-15 and
    HC8-20 measure what it says twoway and dash do."""

    @staticmethod
    def _sec():
        return _flat(_help_between("{marker unsupported}",
                                   "{marker dependencies}"))

    def test_the_list_is_checked_not_generated(self):
        s = self._sec()
        assert "are generated from the same declarations" not in s
        assert "test/test_help_conformance.py" in s

    def test_no_bokeh_rationale_that_is_false(self):
        s = self._sec()
        assert "Bokeh draws one tick level per axis" not in s
        assert "No Bokeh equivalent" not in s

    def test_xtick_is_described_as_twoway_draws_it(self):
        # Flipped (WP-31 D1): xtick() was described in the section's
        # "Minor ticks and minor labels" entry, which was wrong once minor
        # ticks and labels are drawn: the entry left the section, and
        # xtick() is described where the axis options are.
        s = self._sec()
        assert "Minor ticks and minor labels" not in s
        assert "{opt xmtick(" not in s and "{opt ymlabel(" not in s
        whole = open(os.path.join(os.path.dirname(os.path.abspath(
            __file__)), "..", "dash.sthlp"), encoding="utf-8").read()
        i = whole.index("{ul:Ticks without labels.}")
        assert "without labels" in whole[i:i + 600] \
            and "{cmd:xtick()}" in whole[i:i + 600]

    def test_scale_is_not_called_a_combine_option(self):
        s = self._sec()
        assert "these size a panel within" not in s
        # Flipped (WP-31 D5): scale() is drawn (test_sizing.py), so the
        # section no longer lists it; it was there as a pending option.
        assert "{opt scale(#)}" not in s and "fxsize" not in s

    def test_twoways_refusals_are_named_as_such(self):
        s = self._sec()
        for nm in ("title2", "subtitle2", "mlabwidth", "ciopts", "lineopts",
                   "fitopts", "at", "blabel"):
            assert "{opt %s(" % nm in s, nm
        assert s.count("r(198)") >= 3
        # Measured 24sep2026: six, one for each refusal the section names
        # -- title2()/subtitle2(), mlabwidth(), ciopts()/lineopts()/
        # fitopts(), blabel()/at(), link()/filter() -- and the note's.  At
        # least three passed with half of them dropped.
        # 6 -> 8: J1 the opening's refusal rule ("r(198), option X() not
        # allowed") and mlabfontface(), which twoway refuses on a marker
        # label and dash refuses in its words (MLF-01).
        assert s.count("r(198)") == 8, s.count("r(198)")

    def test_the_other_commands_named_are_statas(self):
        """ciopts() is marginsplot's and sts graph's, lineopts() the stcox
        diagnostics', and fitopts() no Stata help file's at all."""
        assert "{opt ciopts(" in _stata_file("m/marginsplot.sthlp")
        assert "{opt ciopts(" in _stata_file("s/sts_graph.sthlp")
        assert "{opt lineopts(" in _stata_file("s/stcox_diagnostics.sthlp")
        hits = []
        for dirpath, _d, files in os.walk(_STATA_BASE):
            for f in files:
                if f.endswith(".sthlp") and "fitopts(" in _read(
                        os.path.join(dirpath, f)).lower():
                    hits.append(f)
        assert hits == [], hits

    def test_the_other_commands_named_are_statas_in_dash(self):
        """The help's half, which needs no Stata: it was skipped with the
        Stata half above on a machine without Stata (24sep2026)."""
        s = self._sec()
        assert "{cmd:marginsplot}" in s and "{cmd:sts graph}" in s

    def test_every_listed_option_is_still_listed(self):
        """test_help_conformance.py's own check, restated so this file fails
        first when the rewrite drops one.

        Flipped (WP-31 J1): the list was the pending blocks alone, which was
        wrong because the twoway options that reach the catch-all are named
        in the same note (test/fixtures/catchall_options_truth.json)."""
        h = _help_between("{marker unsupported}", "{marker dependencies}")
        listed = set()
        in_entry = False
        for ln in h.split("\n"):
            st = ln.lstrip()
            if st.startswith("{phang2}") or st.startswith("{phang}"):
                in_entry = True
            elif not st or st.startswith("{pstd}"):
                in_entry = False
            if in_entry:
                listed |= {n.lower() for n in re.findall(
                    r"\{opth?[: ]\s*([A-Za-z_][A-Za-z0-9_]*)", st)}
        pending = (set(_pending_names("_dash_parse_plot_opts"))
                   | set(_pending_names("_dash_parse_graph_opts")))
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "fixtures", "catchall_options_truth.json"),
                  encoding="utf-8") as fh:
            pending |= set(json.load(fh)["options"])
        assert listed == pending, (sorted(listed - pending),
                                   sorted(pending - listed))


# ===========================================================================
# 5. Dependencies, dash_setup.sthlp, dash.pkg and stata.toc
# ===========================================================================

def _setup_minimums():
    src = _read(_SETUP_ADO)
    mins = dict(re.findall(r'^\s*local min_(\w+)\s+"([\d.]+)"', src, re.M))
    py = re.search(r'return local pymin "([\d.]+)"', src).group(1)
    pkgs = re.search(r'^\s*local pkg_list "([^"]*)"', src, re.M).group(1)
    return py, mins, pkgs.split()


class TestTheDependenciesAreOneList:

    def test_setup_checks_exactly_three_packages(self):
        _py, mins, pkgs = _setup_minimums()
        assert pkgs == ["bokeh", "numpy", "pandas"]
        assert set(mins) == set(pkgs)

    # test_neither_package_is_named_in_setups_code stood here.  It looked for
    # the words scipy and statsmodels in dash_setup.ado's code, and passed
    # with setup checking and pip-installing scipy again under a name built
    # from pieces ("sci" + "py"); test_program_coverage.cscript passed that
    # too (measured 24sep2026).  What it held -- setup neither checks nor
    # installs either -- is held by running setup:
    # test_setup_honesty.cscript HON-28 (both missing: neither is named, pip
    # is asked for nothing, and the run succeeds).

    def test_every_file_states_the_same_minimums(self):
        py, mins, _p = _setup_minimums()
        deps = _flat(_help_between("{marker dependencies}", "{marker author}"))
        assert "Python %s+" % py in deps
        for pkg, v in mins.items():
            assert "%s>=%s" % (pkg, v) in deps, (pkg, v, deps)
        setup = _flat(_read(_SETUP_HELP))
        assert "Python %s or later" % py in setup
        for pkg, v in mins.items():
            assert re.search(r"\{opt %s\}\}%s or later" % (pkg, re.escape(v)),
                             setup), pkg
        pkg_txt = _pkg_text()
        assert "Python %s+" % py in pkg_txt
        for pkg, v in mins.items():
            assert "%s>=%s" % (pkg, v) in pkg_txt, pkg

    def test_the_three_are_imported_by_the_renderer_at_module_scope(self):
        import ast
        tree = ast.parse(_read(os.path.join(_ROOT, "dash_render.py")))
        top = set()
        # WP-30 P1.32: the three are imported inside the top-level `try'
        # blocks that stop in one line naming dash_setup (_dash_dep_fail).
        body = []
        for node in tree.body:
            body += node.body if isinstance(node, ast.Try) else [node]
        for node in body:
            if isinstance(node, ast.Import):
                top |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                top.add(node.module.split(".")[0])
        assert {"bokeh", "numpy", "pandas"} <= top

    def test_dash_exports_the_data_itself_not_with_jsonio(self):
        """Text only: dash.ado exported with jsonio, and refused without
        it, until 24sep2026; jsonio's ado expanded the JSON it wrote as
        macro text, so a value holding a compound quote stopped every
        export (test_string_values.cscript).  Both routes now write through
        _dash_write_data, captured so the date formats are restored when
        the export fails (test_program_coverage.cscript PC-11), and the
        help says jsonio is no longer needed.  That dash draws without
        jsonio runs in test_help_claims_8.cscript -- HC8-17 on the
        immediate route and HC8-17b on dash build's."""
        ado = _read(_ADO)
        assert "which jsonio" not in ado
        assert not re.search(r"^\s*capture noisily quietly jsonio out\b",
                             ado, re.M)
        assert len(re.findall(r"^\s*capture noisily _dash_write_data\b",
                              ado, re.M)) == 2
        assert "dash: jsonio is required but not found." not in ado
        deps = _flat(_help_between("{marker dependencies}", "{marker author}"))
        assert "is no longer needed" in deps

    def test_the_help_does_not_say_setup_installs_python(self):
        deps = _flat(_help_between("{marker dependencies}", "{marker author}"))
        assert "installs and verifies all required software" not in deps
        assert "{cmd:c(python_exec)}" in _flat(_read(_SETUP_HELP))


class TestDashSetupHelpMatchesTheAdo:

    def test_availability_is_the_setting_not_python_query(self):
        """The help said setup verified Python "via python query"; the ado
        reads c(python_exec) and never runs python query.

        A structural guard over dash_setup.ado's text, deliberately:
        availability is decided from configuration, and the no-Python state
        cannot be produced in a test (c() is read-only; see
        test_cscript_hygiene.py's TestTheShippedAdoFilesFollowTheSameRule)."""
        help_ = _flat(_read(_SETUP_HELP))
        code = "\n".join(ln.split("//", 1)[0]
                         for ln in _read(_SETUP_ADO).splitlines())
        assert 'if `"`c(python_exec)\'"\' == ""' in code
        assert not re.search(r"^\s*(capture\s+)?python query", code, re.M)
        # The pattern above sees a bare or a capture'd `python query' at a
        # line's start.  Stata runs it under any prefix and takes `query'
        # down to `q' -- measured 24sep2026, StataNow 19.5 console: python
        # q, python qu, python quer, quietly/qui/cap/capture quietly/
        # noisily/n python query are all rc 0; py and pyth are r(199).  So
        # the word is looked for anywhere in the code, comments dropped
        # first (the *! header names python query), and the pattern is
        # shown to find every spelling Stata runs.
        pyq = re.compile(r"\bpython\s+q(?:u(?:e(?:r(?:y)?)?)?)?\b")
        for form in ("python query", "python q", "python quer",
                     "quietly python query", "qui python query",
                     "cap python query", "capture quietly python query",
                     "noisily python query", "n python qu"):
            assert pyq.search(form), form
        bare = re.sub(r"/\*.*?\*/", " ", code, flags=re.S)
        bare = "\n".join(ln for ln in bare.splitlines()
                         if not ln.lstrip().startswith("*"))
        found = pyq.search(bare)
        assert not found, bare[max(0, found.start() - 80):found.end() + 20]
        assert "via {cmd:python query}" not in help_

    def test_the_steps_are_the_ados_steps(self):
        """The help's list of steps names each one dash_setup takes.

        A structural guard over dash_setup.sthlp's text, deliberately: the
        claim here is what the help says.  What the ado does is held by
        running it in a sandbox that records pip and SSC and installs
        nothing.  This test used to read dash_setup.ado's text for it, and
        passed with dash's own files never checked, the --user retry never
        run, the minimum overwritten before pip saw it, and `, replace'
        dropped from the SSC install with the words left in a comment (each
        measured 24sep2026 on a scratch copy).  Each of those fails:
        the --user retry and the minimum reaching pip,
        test_program_coverage.cscript PC-19 and test_setup_honesty.cscript
        HON-22; no SSC install at all (jsonio is not used), PC-23; dash's
        own files, PC-15 and HON-25; packaging first, HON-27.
        """
        help_ = _flat(_read(_SETUP_HELP))
        for words in ("{cmd:packaging}", "{cmd:dash_render.py}",
                      "{cmd:--user}", "r(198)"):
            assert words in help_, words

    def test_a_package_below_its_minimum_is_unmet_not_a_warning(self):
        """The help said setup "warns when it is below 3.0; it does not
        refuse to continue".  The ado counts it as a failure, and the
        summary then exits r(198) (HC8-19).

        That the ado counts it is held by running it:
        test_program_coverage.cscript PC-21 (bokeh 2.4.3: r(198), "Unmet:
        bokeh 2.4.3 (needs 3.0)", nothing installed) and
        test_setup_honesty.cscript HON-20.  This test used to read the
        counter's line in dash_setup.ado, and passed with the count undone
        on the line after it (measured 24sep2026 on a scratch copy).  What
        is left is a structural guard over the help's text: the old words
        are gone, and the words that replaced them are there -- the control
        that shows the reader reads the passages they stood in."""
        help_ = _flat(_read(_SETUP_HELP))
        assert "it does not refuse to continue" not in help_
        assert "Tornado may be absent" not in help_
        # WP-29 P0.19 (A16): on an externally managed Python the upgrade
        # line is replaced by the way to set up a private environment.
        assert ("An installed package below its minimum is reported and "
                "counted as unmet, with the command that upgrades it or, on "
                "an externally managed Python, the way to set up a private "
                "environment instead.") in help_
        assert ("Tornado is installed with Bokeh, which depends on it, so no "
                "separate installation is needed") in help_
        # WP-30 P1.30: and one at or above the verified window's ceiling
        # is a warning.
        assert ("one below 3.8 is reported as an unmet requirement -- it is "
                "not upgraded for you -- and the run ends with r(198); one at "
                "or above 3.10 is reported as outside the verified range, a "
                "warning, and left as it is.") in help_

    def test_it_installs_only_what_is_missing(self):
        """Every pip install in dash_setup.ado sits in the branch a failed
        import opens: the nearest `capture' before it is that import, and
        the next line is `if _rc != 0 {'.  There is no SSC install: jsonio,
        the one Stata package setup installed, is no longer used.

        WP-29 P0.19: pip runs only through dash_setup_lib.py, whose
        pip_install_argv is its one pip vector; dash_setup.ado calls it as
        _dash_setup_pip, twice (packaging, then each missing package)."""
        lines = _read(_SETUP_ADO).splitlines()
        assert not [ln for ln in lines if '"pip", "install"' in ln
                    or "ssc install" in ln.split("//", 1)[0]]
        installs = [i for i, ln in enumerate(lines)
                    if re.match(r"\s*_dash_setup_pip\b", ln)]
        assert len(installs) == 2, installs
        for i in installs:
            j = i - 1
            while not lines[j].lstrip().startswith("capture "):
                j -= 1
            cap = lines[j].strip()
            assert cap.startswith("capture python: import "), (i + 1, cap)
            # Flipped (WP-31 I3): the import runs off the working directory,
            # so its rc is kept before sys.path is put back; the branch is
            # the same failed import's.
            assert [ln.strip() for ln in lines[j + 1:j + 4]] == [
                "local _imp_rc = _rc",
                "python: import sys; sys.path[:] = _dash_sp",
                "if `_imp_rc' != 0 {"], (i + 1, cap)
        lib = _read(os.path.join(_ROOT, "dash_setup_lib.py"))
        tree = ast.parse(lib)
        holders = sorted(n.name for n in ast.walk(tree)
                         if isinstance(n, ast.FunctionDef)
                         and '"-m", "pip", "install"' in ast.get_source_segment(lib, n))
        assert holders == ["pip_install_argv"], holders

    def test_the_help_explains_externally_managed_pythons(self):
        """WP-29 P0.19: dash_setup.sthlp documents PEP 668, venv(path), the
        restart and python set exec line, ensurepip, and never recommends
        --break-system-packages; the sys.executable recipes (wrong under a
        venv link) and the "either is r(101)" sentence are gone; dash.sthlp
        links the new section."""
        help_ = _flat(_read(_SETUP_HELP))
        for words in ("PEP 668", "{opt venv(path)}", "python set exec",
                      "permanently", "restart Stata", "ensurepip",
                      "It never uses {cmd:--break-system-packages}",
                      "r(7101)", "An option other than {opt venv()} is r(198)"):
            assert words in help_, words
        assert "sys.executable" not in help_
        assert "either is r(101)" not in help_
        dash_help = _flat(_read(os.path.join(_ROOT, "dash.sthlp")))
        assert "{help dash_setup##pep668:Externally managed Pythons}" in dash_help
        assert "{cmd:dash_setup} [{cmd:,} {it:{help dash_setup##options:setup_options}}]" in dash_help

    def test_neither_help_says_jsonio_is_installed_or_links_it(self):
        """dash_setup installed jsonio from SSC, and both help files said so
        and linked {helpb jsonio}, after dash stopped using it (24sep2026).
        What the ado does is run in test_program_coverage.cscript PC-23:
        jsonio off the ado-path, no SSC call and no word of jsonio."""
        setup_help = _flat(_read(_SETUP_HELP))
        dash_help = _flat(_read(os.path.join(_ROOT, "dash.sthlp")))
        for text in (setup_help, dash_help):
            assert "helpb jsonio" not in text
            assert '"help jsonio"' not in text
        assert "installed automatically from SSC" not in setup_help
        assert "jsonio not found after installation" not in setup_help
        assert "neither checks nor installs it" in setup_help
        assert "still installs jsonio" not in dash_help
        assert "Python packages and {cmd:jsonio}" not in dash_help
        with open(os.path.join(_ROOT, "dash.pkg"), encoding="utf-8") as fh:
            assert "packages and jsonio" not in fh.read()

    def test_tornado_comes_with_bokeh(self):
        import importlib.metadata as im
        reqs = [r for r in (im.requires("bokeh") or [])
                if r.lower().startswith("tornado")]
        assert reqs, "bokeh no longer depends on tornado"
        help_ = _flat(_read(_SETUP_HELP))
        assert "Tornado is installed with Bokeh" in help_


def _pkg_text():
    """dash.pkg's description as read: the text of its `d' lines."""
    return _flat(" ".join(ln[2:] for ln in _read(_PKG).splitlines()
                          if ln.startswith("d ")))


class TestThePackageDescription:

    def test_it_does_not_claim_full_twoway_compatibility(self):
        pkg = _pkg_text()
        assert "full twoway option compatibility" not in pkg
        assert "Unsupported Stata twoway options" in pkg

    def test_the_number_of_plot_types_is_the_dispatch_tables(self):
        # 40 -> 42: WP-31 B1 rpcap and rpspike drawn.
        # 42 -> 44: WP-31 B4b contour and contourline drawn.
        words = {40: "forty", 42: "forty-two", 44: "forty-four"}
        n = len(dr._dash_plot_type_names())
        assert "%s twoway plot types" % words.get(n, str(n)) in _pkg_text()

    def test_a_saved_dashboard_loads_nothing_from_elsewhere(self, tmp_path):
        _fig, html, _w = _saved_figure(tmp_path, _scatter())
        assert not re.search(r"<script[^>]+\bsrc\s*=", html, re.I)
        assert not re.search(r"<link[^>]+\bhref\s*=", html, re.I)
        pkg = _pkg_text()
        assert "self-contained" in pkg and "Bokeh Server" in pkg
        assert "All output is a self-contained" not in pkg

    def test_the_filter_widgets_are_the_three_named(self):
        # Flipped (WP-31 H2f): ["dropdown", "range", "slider"] was right
        # until filter() took type(multi).
        assert sorted(dr._DASH_FILTER_TYPES) == ["dropdown", "multi",
                                                 "range", "slider"]
        assert "(dropdown/multi/slider/range)" in _pkg_text()

    def test_setup_is_not_said_to_install_everything(self):
        pkg = _pkg_text()
        assert "to install all dependencies" not in pkg

    def test_the_toc_line(self):
        toc = _read(_TOC)
        assert re.search(r"^d dash: Interactive HTML dashboards from Stata "
                         r"twoway syntax$", toc, re.M)
        assert re.search(r"^p dash dash\.pkg", toc, re.M)
