"""`dash` claimed to ignore options it actually honours.

The user's decision for this work was that an unsupported option is accepted
and **named in a note**, never silently dropped and never an abort. `dash.ado`
builds that note from a hand-written list — the ``_dash_pending`` blocks — and
the list went stale as later sections implemented the options on it. So

    . dash scatter mpg weight, level(90)
    dash: ignoring unsupported option(s): level()

while the confidence interval was in fact computed at 90. A note that names
the wrong options is worse than no note: it tells the user to stop using
something that works.

**Measured** before this test existed — comparing two different non-default
values of each option and diffing the rendered document:

    plot-level  (12): bin falpha fraction frequency kernel level mlcolor
                      mlwidth n percent start width
    graph-level  (5): scheme xsize xtick ysize ytick

This test cannot go stale, because it does not hold a list of its own. It
reads the ``_dash_pending`` blocks out of ``dash.ado`` and, for each option
there, renders twice with two different values and asserts the output does
**not** change. Implement an option and forget to take it off the list, and
this fails.

The values matter. An earlier version of this measurement compared each
option against a no-option baseline and used ``ysize(4)``, which is Stata's
default — so a live option looked dead. Two non-default values have no such
trap.
"""
import hashlib
import inspect
import json
import os
import re
import sys
import tempfile
import warnings

import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr
from conftest import make_data_json

_ADO = os.path.join(_HERE, "..", "dash.ado")

_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_PID = re.compile(r"\bp\d{3,6}\b")

_DF = pd.DataFrame({
    "mpg": [22.0, 17.0, 25.0, 30.0, 21.0, 19.0, 14.0, 28.0, 16.0, 23.0,
            20.0, 18.0, 26.0, 15.0, 24.0],
    "weight": [2930.0, 3350.0, 2200.0, 1800.0, 3000.0, 3100.0, 4080.0,
               2010.0, 3600.0, 2650.0, 2800.0, 3200.0, 2400.0, 3900.0, 2500.0],
})

# Two DIFFERENT non-default values per option, and the plot type the option
# belongs to. A new option on the pending list with no entry here fails
# test_every_pending_option_is_covered, which is the point.
PLOT_VALUES = {
    "at": ("mpg", "weight", "bar"),
    "b1title": ("b1", "bA", "scatter"),
    "b2title": ("b2", "bB", "scatter"),
    "bands": ("20", "55", "kdensity"),
    "bin": ("5", "9", "histogram"),
    "blabel": ("total", "bar", "bar"),
    "ciopts": ("lcolor(red)", "lcolor(blue)", "lfitci"),
    "cmissing": ("n", "y", "line"),
    "color": ("maroon", "navy", "scatter"),
    "colorlist": ("red blue", "green orange", "scatter"),
    "coloruseplegend": ("coloruseplegend", "", "scatter"),
    "connect": ("l", "J", "line"),
    "density": ("density", "frequency", "histogram"),
    "falpha": ("30", "80", "area"),
    "fitopts": ("lcolor(red)", "lcolor(blue)", "lfitci"),
    "fraction": ("fraction", "frequency", "histogram"),
    "frequency": ("frequency", "percent", "histogram"),
    "fxsize": ("50", "80", "scatter"),
    "fysize": ("50", "80", "scatter"),
    "horizontal": ("horizontal", "", "bar"),
    "jitterseed": ("7", "99", "scatter"),
    "kernel": ("epan2", "gaussian", "kdensity"),
    "l1title": ("l1", "lA", "scatter"),
    "l2title": ("l2", "lB", "scatter"),
    "level": ("80", "99", "lfitci"),
    "lineopts": ("lcolor(red)", "lcolor(blue)", "kdensity"),
    "lstyle": ("p3", "p7", "line"),
    "mlabwidth": ("thick", "vthin", "scatter"),
    "mlcolor": ("navy", "maroon", "scatter"),
    "mlpattern": ("dash", "dot", "scatter"),
    "mlstyle": ("p1", "p5", "scatter"),
    "mlwidth": ("thick", "vthin", "scatter"),
    "mstyle": ("p1", "p5", "scatter"),
    "n": ("30", "70", "kdensity"),
    "nodraw": ("nodraw", "", "scatter"),
    "percent": ("percent", "frequency", "histogram"),
    "play": ("x", "y", "scatter"),
    "pstyle": ("p2", "p6", "scatter"),
    "r1title": ("r1", "rA", "scatter"),
    "r2title": ("r2", "rB", "scatter"),
    "range": ("10 30", "12 28", "kdensity"),
    "recast": ("line", "area", "scatter"),
    "scale": ("1.5", "0.5", "scatter"),
    "scheme": ("economist", "s1mono", "scatter"),
    "sort": ("sort", "", "line"),
    "start": ("8", "11", "histogram"),
    "subtitle2": ("S2", "SS", "scatter"),
    "t1title": ("t1", "tA", "scatter"),
    "t2title": ("t2", "tB", "scatter"),
    "text": ('20 3000 "hi"', '25 2500 "yo"', "scatter"),
    "title2": ("T2", "TT", "scatter"),
    "vertical": ("vertical", "", "bar"),
    "width": ("2", "4", "histogram"),
    "xmlabel": ("5(5)40", "10(10)40", "scatter"),
    "xmtick": ("5(1)40", "10(2)40", "scatter"),
    "xsize": ("3", "9", "scatter"),
    "xtick": ("5(5)40", "10(10)40", "scatter"),
    "ymlabel": ("5(5)40", "10(10)40", "scatter"),
    "ymtick": ("5(1)40", "10(2)40", "scatter"),
    "ysize": ("2", "9", "scatter"),
    "ytick": ("5(5)40", "10(10)40", "scatter"),
}


def _pending(block_start_marker: str) -> "list[str]":
    """The option names one `_dash_pending` block lists."""
    with open(_ADO, encoding="utf-8") as fh:
        src = fh.read()
    i = src.index(block_start_marker)
    j = src.index("local _dash_unknown", i)
    return re.findall(r"_dash_pending' (\w+)\"", src[i:j])


def _plot_pending():
    return _pending("program define _dash_parse_plot_opts")


def _graph_pending():
    return _pending("program define _dash_parse_graph_opts")


# Flag-style options: `syntax' gives them their own name as the value, so
# two different values of the same key are the same flag. For these the only
# meaningful comparison is present against absent -- and a flag has no
# default value to be confused with, so that comparison has no trap.
FLAGS = {"colordiscrete", "coloruseplegend", "density", "fraction",
         "frequency", "horizontal", "nodraw", "percent", "sort", "vertical"}


def _norm(html: str) -> str:
    return hashlib.sha256(
        _PID.sub("PID", _UUID.sub("UUID", html)).encode()).hexdigest()


def _render(tmp_path, ptype, popts, gopts, tag):
    spec = {"graphs": [{"name": "g1",
                        "graph_options": dict(gopts, name="g1"),
                        "options": dict(gopts),
                        "plots": [{"type": ptype, "yvar": "mpg",
                                   "xvar": "weight", "options": popts}]}],
            "kpis": [],
            "build_options": {"layout": "auto", "registry": "g1",
                              "level": "95", "formats": {}, "theme": "",
                              "scheme": "", "session_scheme": ""}}
    sp = tmp_path / f"s_{tag}.json"
    dp = tmp_path / f"d_{tag}.json"
    sp.write_text(json.dumps(spec))
    dp.write_text(json.dumps(make_data_json(_DF)))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return _norm(dr.DashRenderer(str(sp), str(dp)).render())


class TestTheListIsCoveredAndHonest:
    def test_every_pending_option_is_covered_here(self):
        """A new entry on the list must come with values to test it."""
        missing = sorted(set(_plot_pending() + _graph_pending())
                         - set(PLOT_VALUES))
        assert not missing, (
            f"options reported as unsupported with no test values: {missing}"
        )

    def test_the_blocks_were_actually_found(self):
        assert len(_plot_pending()) > 5
        assert len(_graph_pending()) > 5


@pytest.mark.parametrize("opt", sorted(set(_plot_pending())))
def test_a_plot_option_reported_unsupported_really_is(tmp_path, opt):
    a, b, ptype = PLOT_VALUES[opt]
    if opt in FLAGS:
        first = _render(tmp_path, ptype, {opt: opt}, {}, f"{opt}_on")
        second = _render(tmp_path, ptype, {}, {}, f"{opt}_off")
        how = f"writing {opt} rather than omitting it"
    else:
        first = _render(tmp_path, ptype, {opt: a}, {}, f"{opt}_a")
        second = _render(tmp_path, ptype, {opt: b}, {}, f"{opt}_b")
        how = f"changing it from {a!r} to {b!r}"
    assert first == second, (
        f"dash reports plot-level {opt}() as unsupported, but {how} changes "
        f"the rendered dashboard — the note names an option that works"
    )


@pytest.mark.parametrize("opt", sorted(set(_graph_pending())))
def test_a_graph_option_reported_unsupported_really_is(tmp_path, opt):
    a, b, ptype = PLOT_VALUES[opt]
    if opt in FLAGS:
        first = _render(tmp_path, ptype, {}, {opt: opt}, f"g_{opt}_on")
        second = _render(tmp_path, ptype, {}, {}, f"g_{opt}_off")
        how = f"writing {opt} rather than omitting it"
    else:
        first = _render(tmp_path, ptype, {}, {opt: a}, f"g_{opt}_a")
        second = _render(tmp_path, ptype, {}, {opt: b}, f"g_{opt}_b")
        how = f"changing it from {a!r} to {b!r}"
    assert first == second, (
        f"dash reports graph-level {opt}() as unsupported, but {how} changes "
        f"the rendered dashboard — the note names an option that works"
    )


# ---------------------------------------------------------------------------
# A flag that NAMES the default cannot be measured by present-against-absent.
# ---------------------------------------------------------------------------
#
# `density' is the histogram's default y axis, so rendering with it and
# rendering without it give the same document -- and the comparisons above
# therefore certify it as ignored whatever the renderer does with it. That is
# how it stayed on the pending list while `_histogram_grid' was reading it, so
#
#     . dash histogram mpg, density
#     dash: ignoring unsupported option(s): density()
#
# drew a density and then said density() had been ignored. Its three siblings
# -- frequency, percent, fraction -- each change the output, so each was found
# and taken off the list; density alone was invisible to that method.
#
# The discriminating question is not whether the output moves but whether the
# renderer READS the option. This takes the y-axis family straight out of
# `_histogram_grid' rather than listing it here, so a fifth member cannot be
# added to the renderer and left off this guard.


def _ymode_flags() -> "list[str]":
    """The y-axis flags the renderer reads, read out of its own source.

    The loop lives in `_dash_histogram_ymode' now -- the one place the
    histogram's scale is decided, for the bars and for the y-axis title,
    in both render modes -- and `_histogram_grid' calls it.
    """
    src = inspect.getsource(dr._dash_histogram_ymode)
    m = re.search(r"for flag in \(([^)]*)\):", src)
    if not m:
        return []
    return sorted(re.findall(r'"(\w+)"', m.group(1)))


def test_the_y_axis_family_was_actually_found():
    """Guards the guard: a moved loop must fail here, not silently pass."""
    assert _ymode_flags() == ["density", "fraction", "frequency", "percent"], (
        "the y-axis flag tuple is no longer where _ymode_flags looks for it, "
        "so the checks below would vacuously pass"
    )


@pytest.mark.parametrize("flag", _ymode_flags() or ["NOT_FOUND"])
def test_a_histogram_y_axis_flag_is_never_reported_unsupported(flag):
    assert flag not in _plot_pending(), (
        f"_histogram_grid reads {flag}() and sets the y axis from it, but "
        f"dash.ado still names {flag}() in the ignoring-unsupported note"
    )
