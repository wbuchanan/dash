"""Regression tests for closed BUGS.md entries that no test covered.

CLAUDE.md rule 8 asks for a test for every fixed defect -- one that fails if
the defect comes back.  WP-23 reconciled BUGS.md (TR-23.5) and found three
closed entries that had none (GAPS.md L9; ROADMAP WP-24, AC-24.4), listed
in ``test/test_tracking_documents.py``'s ``CLOSED_WITHOUT_A_TEST`` until
they had one:

* "Eight fills in comprehensive_demo.do render at a hundredth of the
  intended opacity" (fixed in b917c33).  The fix is data in a do-file that
  only Stata can read, so its test is ``test_bug_regressions.cscript``
  BR-01: it runs the example and reads the fills of the saved page and of
  the served document.
* "Every successful `dash build' prints an unexplained "file not found""
  (fixed in 81ebbc5).  A note Stata prints, so its test is BR-02 there.
* "ylabel(#5, grid) was silently ignored" (fixed in cc3c4ac).  A parse in
  ``dash_render.py``, tested here in both render modes, and through Stata
  against a live ``twoway`` in BR-03.

Each test here was run against its defect restored and failed there; the
mutation is recorded with the test.
"""
import importlib.util
import itertools
import json
import os
import sys
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import FixedTicker, Plot

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from conftest import make_data_json  # noqa: E402

_SEQ = itertools.count()
_MODES = ("saved", "served")


# ===========================================================================
# ylabel(#5, grid) was silently ignored
# ===========================================================================
#
# The defect (BUGS.md): `_dash_parse_axis_spec' stripped the recognised
# sub-option `grid' out of `#5, grid' and left its comma behind, so the
# keyword forms saw `#5,', matched none of them, and the count was dropped:
# the axis kept Bokeh's default ticker, BasicTicker(desired_num_ticks=6),
# with the grid on.  Fixed in cc3c4ac by `.rstrip(",")' on the remainder.
#
# What twoway draws -- measured 24sep2026, StataNow 19.5, `sysuse auto':
#
#     twoway scatter mpg weight, ylabel(#5, grid) scheme(s1color)
#
# records the rule in its live .gph as `.yaxis1.major.suggest_ticks 5' (and
# `ylabel(#5)' records the same line), and `.yaxis1.style.editstyle
# draw_major_grid(yes) editcopy' for the grid.  Its SVG (graph export) draws
# four labels, 10 20 30 40, and a solid #E0E0E0 gridline across the plot
# region at each of the four; the same command without `grid' draws the
# labels and no gridline, under s1color and s1mono alike, which draw no y
# grid by default.
#
# dash used to hand the count to Bokeh as desired_num_ticks, and Bokeh drew
# 15(5)40 over a y range of 10.55 to 42.45 (the pre-fix default ticker drew
# the same).  dash now places #N's ticks by twoway's rule over what the
# layers draw (BUGS.md "ylabel(#N) and xlabel(#N) ticks fall where Bokeh
# puts them", test_natscale.py), so what is compared with twoway here is
# the labels themselves, 10 20 30 40, and the grid at them in the scheme's
# colour.
#
# Mutation, run 24sep2026: with `.rstrip(",")' taken out of
# `_dash_parse_axis_spec', test_the_count_reaches_the_axis and
# test_the_sub_option_leaves_the_rule_alone fail in both modes (Bokeh's
# default ticker, no FixedTicker), and so does test_nothing_is_reported_as_
# ignored, because the reporter cc3c4ac added names the dropped `#5'.  The
# two grid tests pass there: the defect dropped the count, not the grid.

#: The labels twoway draws for it over mpg's 12 to 41 (SVG, measured).
_TWOWAY_LABELS = [10.0, 20.0, 30.0, 40.0]
#: The colour of the gridlines twoway draws under s1color (SVG, measured).
_TWOWAY_S1COLOR_GRID = "#e0e0e0"

_DF = pd.DataFrame({"mpg": np.linspace(12, 41, 74),
                    "weight": np.linspace(1760, 4840, 74)})


def _graph(name, title, ylabel):
    """One graph as dash.ado writes it for
    ``dash scatter mpg weight, ylabel(<ylabel>) title("<title>") name(<name>)``
    (measured: the spec `_dash_serve_spec' wrote on 24sep2026)."""
    return {"plots": [{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}, "if_expr": "", "in_expr": ""}],
            "graph_options": {"title": '"%s"' % title, "name": name,
                              "ylabel": ylabel},
            "if_expr": "", "in_expr": ""}


def _spec():
    """``dash build, scheme(s1color)`` over a graph with ``ylabel(#5, grid)``
    and one with ``ylabel(#5)``: s1color draws no y grid of its own, so a
    grid on the first is the sub-option's doing."""
    return {"graphs": [_graph("g1", "grid", "#5, grid"),
                       _graph("g2", "plain", "#5")],
            "kpis": [],
            "build_options": {
                "layout": "auto", "link": "", "filter": "", "theme": "",
                "scheme": "s1color", "session_scheme": "s1color",
                "title": "", "subtitle": "", "registry": "g1 g2", "tabs": "",
                "filter_position": "top", "csv": "0", "level": "95",
                "formats": {"mpg": "%8.0g", "weight": "%8.0gc"},
                "limits": {}}}


def _write(tmp_path, spec):
    tag = next(_SEQ)
    sp = tmp_path / ("spec_%d.json" % tag)
    dp = tmp_path / ("data_%d.json" % tag)
    sp.write_text(json.dumps(spec), encoding="utf-8")
    dp.write_text(json.dumps(make_data_json(_DF)), encoding="utf-8")
    return tag, str(sp), str(dp)


def _plots(models):
    seen, out = set(), []
    for m in models:
        for x in m.references():
            if isinstance(x, Plot) and x.id not in seen:
                seen.add(x.id)
                out.append(x)
    return out


def _figures(mode, tmp_path, spec):
    """``({title: figure}, warnings)`` as the saved page or the served app
    draws the spec."""
    tag, sp, dp = _write(tmp_path, spec)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        if mode == "saved":
            r = dr.DashRenderer(sp, dp)
            r.render()
            figs = list(r.figures.values())
        else:
            ap = str(tmp_path / ("app_%d.py" % tag))
            dr.ServerAppBuilder(sp, dp).build(ap)
            ms = importlib.util.spec_from_file_location(
                "_bug_regressions_app_%d" % tag, ap)
            mod = importlib.util.module_from_spec(ms)
            ms.loader.exec_module(mod)
            doc = Document()
            mod.make_document(doc)
            figs = _plots(doc.roots)
    by_title = {getattr(f.title, "text", None): f for f in figs}
    return by_title, [str(w.message) for w in caught]


@pytest.fixture(scope="module")
def drawn(tmp_path_factory):
    """Both modes, rendered once for the class."""
    out = {}
    for mode in _MODES:
        figs, caught = _figures(mode, tmp_path_factory.mktemp(mode), _spec())
        assert set(figs) >= {"grid", "plain"}, (mode, sorted(figs, key=str))
        out[mode] = (figs, caught)
    return out


def _y_axis(fig):
    axes = [a for a in fig.left if hasattr(a, "ticker")]
    assert len(axes) == 1, axes
    return axes[0]


def _y_grids(fig):
    return [g for g in fig.center
            if type(g).__name__ == "Grid" and g.dimension == 1]


# One worker for the class, so the module's drawn pair is made once,
# not once per worker its tests land on (WP-30 test performance A4;
# measured 07oct2026: 0.55 s on six).
@pytest.mark.xdist_group(name="ylabel-grid-drawn")
@pytest.mark.parametrize("mode", _MODES)
class TestYlabelCountWithAGridIsHonoured:
    """``ylabel(#5, grid)``: the count reaches the axis and the grid is drawn
    at the labels, as twoway draws both (measured; see the note above)."""

    def test_the_count_reaches_the_axis(self, drawn, mode):
        """The count places the ticks where twoway draws them for #5 over
        12 to 41 -- 10 20 30 40 (SVG, measured) -- which dash computes by
        twoway's rule (test_natscale.py; BUGS.md "ylabel(#N) and xlabel(#N)
        ticks fall where Bokeh puts them").  A dropped count left Bokeh's
        default ticker, which draws 15(5)40."""
        figs, _ = drawn[mode]
        ticker = _y_axis(figs["grid"]).ticker
        assert isinstance(ticker, FixedTicker), type(ticker).__name__
        assert list(ticker.ticks) == _TWOWAY_LABELS, list(ticker.ticks)

    def test_the_sub_option_leaves_the_rule_alone(self, drawn, mode):
        """``#5, grid`` asks for what ``#5`` asks for, as twoway records the
        same suggest_ticks line for both."""
        figs, _ = drawn[mode]
        with_grid = _y_axis(figs["grid"]).ticker
        without = _y_axis(figs["plain"]).ticker
        assert type(with_grid) is type(without)
        assert list(with_grid.ticks) == list(without.ticks) == _TWOWAY_LABELS

    def test_the_grid_is_drawn_at_the_labels_in_the_schemes_colour(
            self, drawn, mode):
        """twoway draws one gridline at each y label, in #E0E0E0 under
        s1color.  A Bokeh grid with no ticker of its own draws at its
        axis's ticks -- the labels."""
        figs, _ = drawn[mode]
        fig = figs["grid"]
        grids = _y_grids(fig)
        assert len(grids) == 1, grids
        g = grids[0]
        assert g.grid_line_color is not None, "the grid was not drawn"
        assert str(g.grid_line_color).lower() == _TWOWAY_S1COLOR_GRID
        axis = _y_axis(fig)
        assert g.ticker is None or g.ticker is axis.ticker, g.ticker
        assert g.ticker is not None or g.axis is axis, (
            "the y grid is not tied to the y axis, so its lines need not "
            "sit at the labels")

    def test_without_the_sub_option_no_grid_is_drawn(self, drawn, mode):
        """s1color draws no y grid; neither does twoway without ``grid``."""
        figs, _ = drawn[mode]
        assert [g.grid_line_color for g in _y_grids(figs["plain"])] == [None]

    def test_nothing_is_reported_as_ignored(self, drawn, mode):
        """The defect was silent; so is the fix, and ``#5`` is no longer
        named as an unknown token either."""
        _, caught = drawn[mode]
        assert not [w for w in caught if "ylabel()" in w or "#5" in w], caught
