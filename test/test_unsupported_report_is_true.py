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
    # For the converse tests: a category, a second numeric, an integer code
    # and a column with a missing value (colorvar, by, hover, mlabel,
    # colormissing).  Both renders of a pair share the data, so the
    # comparisons above are unaffected.
    "foreign": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0,
                0.0, 1.0, 0.0, 1.0, 0.0],
    "price": [4099.0, 4749.0, 3799.0, 4816.0, 5788.0, 4453.0, 5189.0,
              10372.0, 4082.0, 11385.0, 6165.0, 3955.0, 7140.0, 4425.0,
              5079.0],
    "rep78": [3.0, 4.0, 3.0, 5.0, 4.0, 3.0, 5.0, 4.0, 3.0, 4.0,
              2.0, 3.0, 4.0, 5.0, 3.0],
    "pricemiss": [4099.0, None, 3799.0, 4816.0, 5788.0, 4453.0, 5189.0,
                  10372.0, None, 11385.0, 6165.0, 3955.0, 7140.0, 4425.0,
                  5079.0],
})

# Two DIFFERENT non-default values per option, and the plot type the option
# belongs to. A new option on the pending list with no entry here fails
# test_every_pending_option_is_covered, which is the point.
PLOT_VALUES = {
    # twoway's fitarea options: drawn on a ci fit's band
    # (test_ci_band_style.py), accepted and named on every other type.
    "acolor": ("red", "blue", "scatter"),
    "alcolor": ("red", "blue", "scatter"),
    "alwidth": ("thick", "vthin", "scatter"),
    "alpattern": ("dash", "dot", "scatter"),
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
    # link() and filter() belong to dash build; written on a graph they
    # are stored, read by nothing, and named in the note (WP-13 TR-13.1).
    "filter": ("foreign, type(dropdown)", "weight, type(range)", "scatter"),
    "fxsize": ("50", "80", "scatter"),
    "fysize": ("50", "80", "scatter"),
    "link": ("g1", "g2", "scatter"),
    "horizontal": ("horizontal", "", "bar"),
    "jitterseed": ("7", "99", "scatter"),
    "kernel": ("epan2", "gaussian", "kdensity"),
    "l1title": ("l1", "lA", "scatter"),
    "l2title": ("l2", "lB", "scatter"),
    "level": ("80", "99", "lfitci"),
    "lineopts": ("lcolor(red)", "lcolor(blue)", "kdensity"),
    # WP-22 TR-22.3: twoway options that used to land in the note as
    # unknown, now declared -- named by their full names -- and not drawn.
    "mlabtextstyle": ("heading", "body", "scatter"),
    "mlabvposition": ("rep78", "foreign", "scatter"),
    "mlabwidth": ("thick", "vthin", "scatter"),
    "mlcolor": ("navy", "maroon", "scatter"),
    "mlpattern": ("dash", "dot", "scatter"),
    # WP-30 P1.14b: kept and named, not drawn (P2.9 dot rows, P2.8 marker
    # back lines); twoway accepts all three on scatter (plan E9.7).
    "dstyle": ("p3", "p5", "scatter"),
    "dlstyle": ("p3", "p5", "scatter"),
    "bmlinestyle": ("p3", "p5", "scatter"),
    "mlwidth": ("thick", "vthin", "scatter"),
    "n": ("30", "70", "kdensity"),
    "nodraw": ("nodraw", "", "scatter"),
    "percent": ("percent", "frequency", "histogram"),
    "play": ("x", "y", "scatter"),
    "r1title": ("r1", "rA", "scatter"),
    "r2title": ("r2", "rB", "scatter"),
    "range": ("10 30", "12 28", "kdensity"),
    "recast": ("line", "area", "scatter"),
    "scale": ("1.5", "0.5", "scatter"),
    "scheme": ("economist", "s1mono", "scatter"),
    # Flipped (WP-29 P0.1): sort is honoured on line now -- twoway joins a
    # line in x order under it -- so the inert case is on scatter, where it
    # is still named and draws nothing.
    "sort": ("sort", "", "scatter"),
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
    "xoverhangs": ("xoverhangs", "", "scatter"),
    "xsize": ("3", "9", "scatter"),
    "xtick": ("5(5)40", "10(10)40", "scatter"),
    "ymlabel": ("5(5)40", "10(10)40", "scatter"),
    "ymtick": ("5(1)40", "10(2)40", "scatter"),
    "yoverhangs": ("yoverhangs", "", "scatter"),
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
         "frequency", "horizontal", "nodraw", "percent", "sort", "vertical",
         # WP-22: twoway's advanced options, declared XOVERHANGs/YOVERHANGs.
         "xoverhangs", "yoverhangs",
         # The seven statistical sub-options (WP-18): discrete on
         # histogram; stdp/stdf/stdr on lfitci and qfitci; mean, noweight,
         # adjust and logit on lowess.
         "discrete", "stdp", "stdf", "stdr", "mean", "noweight", "adjust",
         "logit"}


# The CSP lists a sha256 of every inline script, and those scripts carry
# Bokeh's per-render ids: the hashes differ whenever the ids do (WP-30 P1.29).
_CSP_HASH = re.compile(r"'sha256-[A-Za-z0-9+/]{43}='")


def _norm(html: str) -> str:
    html = _CSP_HASH.sub("'HASH'", html)
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
        """Guards the guard: the pending-list scanner still finds its blocks
        in dash.ado, so the tests that use its lists cannot pass on
        nothing."""
        # Exact counts, measured 24sep2026: _dash_parse_plot_opts names 48
        # pending options (44 before the S3 batch's four fitarea options)
        # and _dash_parse_graph_opts 23.  `> 5' passed after
        # a refactor dropped most of a block from the regex's reach, which
        # would turn every "reported unsupported really is" case below into
        # a silent no-op.
        # Flipped (WP-30 P1.14a): 48 -> 44: pstyle(), lstyle(), mstyle()
        # and mlstyle() are drawn (p1-p15), so they leave the list.
        # 44 -> 47: P1.14b dstyle dlstyle bmlinestyle declared and named
        assert len(_plot_pending()) == 47, sorted(_plot_pending())
        assert len(_graph_pending()) == 23, sorted(_graph_pending())


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
    """A structural guard, deliberately: every flag the RENDERER reads,
    taken from its own source, is off dash.ado's pending list -- so a
    fifth flag added to the renderer cannot be left on it.  The behaviour
    for today's four is test_statistical_options.cscript SO-97..100, which
    runs `dash histogram mpg, <flag>' and requires no note and the flag in
    the registry (measured, WP-24: density put back on the list fails
    SO-97)."""
    assert flag not in _plot_pending(), (
        f"_histogram_grid reads {flag}() and sets the y axis from it, but "
        f"dash.ado still names {flag}() in the ignoring-unsupported note"
    )


# ===========================================================================
# The converse: an option NOT on the pending list must do something.
#
# ROADMAP WP-13 TR-13.5.  The tests above certify "pending => inert".  The
# other half of the contract -- "nothing is ever dropped without being named"
# (dash.sthlp) -- had no guard at all, and GAPS.md E2 lists what that
# allowed: link(), filter() and saving() written on a graph were stored,
# read by nothing, and named nowhere.  Every option the two syntax blocks
# declare is now classified: PENDING (reported, and inert by the tests
# above), an ALIAS (folded onto its target in dash.ado before the spec is
# written, so never a spec key; pinned in test_alias_semantics.cscript), one
# of the two options that choose a route or a path rather than a rendering
# (NOT_IN_FILE, pinned by reading the ado), or LIVE -- in which case
# rendering with two different values must give two different documents.
# A declared option in none of those is the failure that tells the next
# maintainer to decide: honour it, or put it on the list.
# ===========================================================================

from test_abbreviations import _program_body, _syntax_options  # noqa: E402


def _declared(prog):
    with open(_ADO, encoding="utf-8") as fh:
        src = fh.read()
    return [full for _, full in _syntax_options(_program_body(src, prog))]


def _declared_plot():
    return _declared("_dash_parse_plot_opts")


def _declared_graph():
    return _declared("_dash_parse_graph_opts")


#: Short forms dash.ado folds onto their target before the spec is written
#: (the t/b/l/r titles, bins(), bw(), mlg(), cv()/colv(), pbgc() and the
#: *2 axis abbreviations).  They never appear as a spec key, so neither
#: direction here can see them; test_alias_semantics.cscript pins them.
ALIASES = {"t", "b", "l", "r", "bins", "bw", "mlg", "cv", "colv", "pbgc",
           "xla2", "xsc2", "xti2", "yla2", "ysc2", "yti2",
           # sort(varlist).  Stata's -syntax- spells an option that may be
           # written bare or with an argument as a pair -- SORT SORT1() --
           # exactly as twoway_yxview_parse.class declares it; the argument
           # form is reported as sort() and never written to the spec
           # (WP-22, pinned in test_twoway_option_parity.cscript TP-06).
           "sort1"}

#: Options that decide where a command goes rather than what it draws.
NOT_IN_FILE = {
    "name": "routes the spec to the registry instead of the renderer",
    "saving": "chooses the output path on the immediate route; on a named "
              "graph it is named in the note (dash.ado, the route decision)",
    "nodraw": "keeps the browser window shut, at the launch decision; the "
              "file is the same with or without it, so it is pinned by "
              "reading the ado (test_nodraw_is_still_read_by_the_launch_"
              "decision) and certified by test_nodraw_honoured.cscript",
    "replace": "lets saving() write over a file that exists (WP-27); the "
               "page is the same with or without it, so it is certified by "
               "test_path_validation.cscript PV-22..27",
}

#: option -> (options A, options B, plot type, extra graph options).  Two
#: renders that must DIFFER.  Both sides carry the same extra options, so
#: an option that only means something in context (colpalette without
#: colorvar, xlabel2 without a layer on the second axis) is probed in it.
_CV = {"colorvar": "price"}
_ML = {"mlabel": "foreign"}
LIVE_VALUES = {
    # ---- plot-level -------------------------------------------------------
    # WP-30 P1.14a: drawn, p1-p15 (each pair of styles differs on its type).
    "alstyle": ({"alstyle": "p3"}, {"alstyle": "p7"}, "bar", {}),
    "astyle": ({"astyle": "p3"}, {"astyle": "p7"}, "area", {}),
    "bands": ({"bands": "3"}, {"bands": "6"}, "mband", {}),
    "barwidth": ({"barwidth": "50"}, {"barwidth": "150"}, "bar", {}),
    "base": ({"base": "10"}, {"base": "15"}, "bar", {}),
    "bfcolor": ({"bfcolor": "red"}, {"bfcolor": "blue"}, "bar", {}),
    "bin": ({"bin": "4"}, {"bin": "8"}, "histogram", {}),
    # WP-30 P1.14a: drawn, p1-p15
    "blstyle": ({"blstyle": "p3"}, {"blstyle": "p7"}, "bar", {}),
    # WP-30 P1.14a: drawn, p1-p15
    "bstyle": ({"bstyle": "p3"}, {"bstyle": "p7"}, "bar", {}),
    "blcolor": ({"blcolor": "red"}, {"blcolor": "blue"}, "bar", {}),
    "bwidth": ({"bwidth": "300"}, {"bwidth": "700"}, "lpoly", {}),
    "color": ({"color": "red"}, {"color": "blue"}, "scatter", {}),
    "colorcuts": ({**_CV, "colorcuts": "4000 6000"},
                  {**_CV, "colorcuts": "5000 9000"}, "scatter", {}),
    "colordiscrete": ({"colorvar": "foreign", "colordiscrete": "colordiscrete"},
                      {"colorvar": "foreign"}, "scatter", {}),
    "colormissing": ({"colorvar": "pricemiss", "colormissing": "red"},
                     {"colorvar": "pricemiss", "colormissing": "blue"},
                     "scatter", {}),
    "colornlevels": ({**_CV, "colornlevels": "3"}, {**_CV, "colornlevels": "7"},
                     "scatter", {}),
    "colorlevels": ({**_CV, "colorlevels": "3"}, {**_CV, "colorlevels": "7"},
                    "scatter", {}),
    "colorvarminmax": ({**_CV, "colorvarminmax": "colorvarminmax"}, dict(_CV),
                       "scatter", {}),
    "colorvar": ({"colorvar": "foreign"}, {"colorvar": "price"}, "scatter", {}),
    "colpalette": ({**_CV, "colpalette": "viridis"},
                   {**_CV, "colpalette": "magma"}, "scatter", {}),
    "degree": ({"degree": "0"}, {"degree": "2"}, "lpoly", {}),
    # The histogram scale flags: each against a DIFFERENT flag, because
    # density names the default and present-against-absent cannot see it.
    "density": ({"density": "density"}, {"frequency": "frequency"},
                "histogram", {}),
    "fraction": ({"fraction": "fraction"}, {"density": "density"},
                 "histogram", {}),
    "frequency": ({"frequency": "frequency"}, {"percent": "percent"},
                  "histogram", {}),
    "percent": ({"percent": "percent"}, {"fraction": "fraction"},
                "histogram", {}),
    "falpha": ({"falpha": "30"}, {"falpha": "80"}, "area", {}),
    "fcolor": ({"fcolor": "red"}, {"fcolor": "blue"}, "area", {}),
    "fintensity": ({"fintensity": "20"}, {"fintensity": "80"}, "area", {}),
    "jitter": ({"jitter": "3"}, {"jitter": "7"}, "scatter", {}),
    "jitterseed": ({"jitter": "5", "jitterseed": "7"},
                   {"jitter": "5", "jitterseed": "99"}, "scatter", {}),
    "jseed": ({"jitter": "5", "jseed": "7"}, {"jitter": "5", "jseed": "99"},
              "scatter", {}),
    "kernel": ({"kernel": "epan2"}, {"kernel": "gaussian"}, "kdensity", {}),
    "lalpha": ({"lalpha": "20"}, {"lalpha": "80"}, "line", {}),
    "lcolor": ({"lcolor": "red"}, {"lcolor": "blue"}, "line", {}),
    # WP-22: the connecting-line options, on a type that draws the line.
    "clcolor": ({"clcolor": "red"}, {"clcolor": "blue"}, "line", {}),
    "clpattern": ({"clpattern": "dash"}, {"clpattern": "dot"}, "line", {}),
    "clwidth": ({"clwidth": "vthin"}, {"clwidth": "vthick"}, "line", {}),
    # WP-30 P1.14a: drawn, p1-p15
    "clstyle": ({"clstyle": "p3"}, {"clstyle": "p7"}, "line", {}),
    # WP-30 P1.14a: drawn, p1-p15
    "lstyle": ({"lstyle": "p3"}, {"lstyle": "p7"}, "line", {}),
    # WP-30 P1.14a: drawn, p1-p15
    "mlstyle": ({"mlstyle": "p1"}, {"mlstyle": "p5"}, "scatter", {}),
    # WP-30 P1.14a: drawn, p1-p15
    "mstyle": ({"mstyle": "p1"}, {"mstyle": "p5"}, "scatter", {}),
    # WP-30 P1.14a: drawn, p1-p15
    "p": ({"p": "p2"}, {"p": "p6"}, "scatter", {}),
    # WP-30 P1.14a: drawn, p1-p15
    "pstyle": ({"pstyle": "p2"}, {"pstyle": "p6"}, "scatter", {}),
    "mlabangle": ({**_ML, "mlabangle": "45"}, {**_ML, "mlabangle": "90"},
                  "scatter", {}),
    "mlabformat": ({"mlabel": "price", "mlabformat": "%9.1f"},
                   {"mlabel": "price", "mlabformat": "%9.2f"}, "scatter", {}),
    "xvarformat": ({"xvarformat": "%9.2f"}, {"xvarformat": "%9.1f"},
                   "scatter", {}),
    "yvarformat": ({"yvarformat": "%9.2f"}, {"yvarformat": "%9.1f"},
                   "scatter", {}),
    "level": ({"level": "80"}, {"level": "99"}, "lfitci", {}),
    "lpattern": ({"lpattern": "dash"}, {"lpattern": "dot"}, "line", {}),
    "lwidth": ({"lwidth": "vthin"}, {"lwidth": "vthick"}, "line", {}),
    "malpha": ({"malpha": "20"}, {"malpha": "80"}, "scatter", {}),
    "marker": ({"marker": "O"}, {"marker": "T"}, "scatter", {}),
    "mcolor": ({"mcolor": "red"}, {"mcolor": "blue"}, "scatter", {}),
    "mfcolor": ({"mfcolor": "red"}, {"mfcolor": "blue"}, "scatter", {}),
    "mlabcolor": ({**_ML, "mlabcolor": "red"}, {**_ML, "mlabcolor": "blue"},
                  "scatter", {}),
    "mlabel": ({"mlabel": "foreign"}, {"mlabel": "rep78"}, "scatter", {}),
    "mlabgap": ({**_ML, "mlabgap": "tiny"}, {**_ML, "mlabgap": "vlarge"},
                "scatter", {}),
    "mlabposition": ({**_ML, "mlabposition": "3"},
                     {**_ML, "mlabposition": "9"}, "scatter", {}),
    "mlabsize": ({**_ML, "mlabsize": "tiny"}, {**_ML, "mlabsize": "vlarge"},
                 "scatter", {}),
    "mlcolor": ({"mlcolor": "navy"}, {"mlcolor": "maroon"}, "scatter", {}),
    "mlwidth": ({"mlwidth": "thick"}, {"mlwidth": "vthin"}, "scatter", {}),
    "msangle": ({"msymbol": "T", "msangle": "0"},
                {"msymbol": "T", "msangle": "45"}, "scatter", {}),
    "msize": ({"msize": "tiny"}, {"msize": "vlarge"}, "scatter", {}),
    "msymbol": ({"msymbol": "O"}, {"msymbol": "T"}, "scatter", {}),
    "n": ({"n": "30"}, {"n": "70"}, "kdensity", {}),
    # ---- the statistical sub-options (WP-18) ----------------------------
    # Flags: present against absent, except stdp, which NAMES the default
    # band (the density trap above), so it is paired against a sibling.
    # mpg has 15 distinct values in _DF, so `discrete' draws 15 unit-width
    # bars where the default bin rule for N=15 draws fewer; stdf and stdr
    # widen and narrow the band; the lowess four each change the smooth
    # (Stata's own smoother, in the renderer since WP-18: statsmodels'
    # lowess had none of these switches, so before it the flag rendered
    # byte-identical and this test failed, which is what it is for).
    "discrete": ({"discrete": "discrete"}, {}, "histogram", {}),
    "stdf": ({"stdf": "stdf"}, {}, "lfitci", {}),
    "stdr": ({"stdr": "stdr"}, {}, "lfitci", {}),
    "stdp": ({"stdp": "stdp"}, {"stdf": "stdf"}, "lfitci", {}),
    "mean": ({"mean": "mean"}, {}, "lowess", {}),
    "noweight": ({"noweight": "noweight"}, {}, "lowess", {}),
    "adjust": ({"adjust": "adjust"}, {}, "lowess", {}),
    "logit": ({"logit": "logit"}, {}, "lowess", {}),
    "range": ({"range": "10 30"}, {"range": "12 28"}, "kdensity", {}),
    "start": ({"start": "8"}, {"start": "11"}, "histogram", {}),
    "width": ({"width": "2"}, {"width": "4"}, "histogram", {}),
    # A lone layer on the second axis is drawn on the one axis twoway
    # draws, styled by the second axis's options (BUGS.md, S3): alone it
    # renders as the first axis does, so the probe gives the graph a
    # second-axis title, which only yaxis(2)/xaxis(2) reads.
    "xaxis": ({"xaxis": "1"}, {"xaxis": "2"}, "line",
              {"xtitle2": "Second"}),
    "yaxis": ({"yaxis": "1"}, {"yaxis": "2"}, "line",
              {"ytitle2": "Second"}),
    # ---- graph-level --------------------------------------------------------
    "aspectratio": ({}, {}, "scatter", ("aspectratio", "0.5", "2")),
    "bgcolor": ({}, {}, "scatter", ("bgcolor", "red", "blue")),
    "by": ({}, {}, "scatter", ("by", "foreign", "rep78")),
    "caption": ({}, {}, "scatter", ("caption", "A", "B")),
    "graphregion": ({}, {}, "scatter", ("graphregion", "color(red)",
                                         "color(blue)")),
    "hover": ({}, {}, "scatter", ("hover", "price", "rep78")),
    # One key: position() alone stays hidden under Stata's rule, so the
    # pair is on/off.
    "legend": ({}, {}, "scatter", ("legend", "on", "off")),
    "note": ({}, {}, "scatter", ("note", "A", "B")),
    "plotbgcolor": ({}, {}, "scatter", ("plotbgcolor", "red", "blue")),
    "plotregion": ({}, {}, "scatter", ("plotregion", "color(red)",
                                        "color(blue)")),
    "scheme": ({}, {}, "scatter", ("scheme", "economist", "s1mono")),
    "subtitle": ({}, {}, "scatter", ("subtitle", "A", "B")),
    "title": ({}, {}, "scatter", ("title", "A", "B")),
    "xlabel": ({}, {}, "scatter", ("xlabel", "2000(1000)4000",
                                    "1800 2400 3000")),
    "xlabel2": ({"xaxis": "2"}, {"xaxis": "2"}, "scatter",
                ("xlabel2", "2000 3000", "2500 3500")),
    "xline": ({}, {}, "scatter", ("xline", "3000", "3500")),
    "xscale": ({}, {}, "scatter", ("xscale", "log", "reverse")),
    "xscale2": ({"xaxis": "2"}, {"xaxis": "2"}, "scatter",
                ("xscale2", "log", "reverse")),
    "xsize": ({}, {}, "scatter", ("xsize", "3", "9")),
    "xtick": ({}, {}, "scatter", ("xtick", "2000 3000", "2500 3500")),
    "xtitle": ({}, {}, "scatter", ("xtitle", "A", "B")),
    "xtitle2": ({"xaxis": "2"}, {"xaxis": "2"}, "scatter",
                ("xtitle2", "A", "B")),
    "ylabel": ({}, {}, "scatter", ("ylabel", "10(10)30", "15 25")),
    "ylabel2": ({"yaxis": "2"}, {"yaxis": "2"}, "scatter",
                ("ylabel2", "15 25", "18 28")),
    # WP-29 P0.5: dash's own spellings of ytick(..., axis(2)) and
    # yline(..., axis(2)) (and the x forms), drawn on the second axis.
    "ytick2": ({"yaxis": "2"}, {"yaxis": "2"}, "scatter",
               ("ytick2", "15 25", "18 28")),
    "yline2": ({"yaxis": "2"}, {"yaxis": "2"}, "scatter",
               ("yline2", "20", "25")),
    "xtick2": ({"xaxis": "2"}, {"xaxis": "2"}, "scatter",
               ("xtick2", "2000 3000", "2500 3500")),
    "xline2": ({"xaxis": "2"}, {"xaxis": "2"}, "scatter",
               ("xline2", "3000", "3500")),
    "yline": ({}, {}, "scatter", ("yline", "20", "25")),
    "yscale": ({}, {}, "scatter", ("yscale", "log", "reverse")),
    "yscale2": ({"yaxis": "2"}, {"yaxis": "2"}, "scatter",
                ("yscale2", "log", "reverse")),
    "ysize": ({}, {}, "scatter", ("ysize", "3", "9")),
    "ytick": ({}, {}, "scatter", ("ytick", "15 25", "18 28")),
    "ytitle": ({}, {}, "scatter", ("ytitle", "A", "B")),
    "ytitle2": ({"yaxis": "2"}, {"yaxis": "2"}, "scatter",
                ("ytitle2", "A", "B")),
    # GAPS2 X2: the colour key's own axis options, drawn on the ColorBar.
    "zlabel": (dict(_CV), dict(_CV), "scatter",
               ("zlabel", "4000(4000)16000", "#3")),
    "zscale": (dict(_CV), dict(_CV), "scatter", ("zscale", "log", "reverse")),
    "ztitle": (dict(_CV), dict(_CV), "scatter", ("ztitle", "A", "B")),
}


def _live_pair(opt):
    """``(popts_a, gopts_a, popts_b, gopts_b, ptype)`` for one live option."""
    pa, pb, ptype, g = LIVE_VALUES[opt]
    if isinstance(g, tuple):
        key, a, b = g
        return dict(pa), {key: a}, dict(pb), {key: b}, ptype
    return dict(pa), dict(g), dict(pb), dict(g), ptype


def _plot_live():
    return sorted(set(_declared_plot()) - set(_plot_pending()) - ALIASES
                  - set(NOT_IN_FILE) - set(_declared_graph()))


def _graph_live():
    return sorted(set(_declared_graph()) - set(_graph_pending()) - ALIASES
                  - set(NOT_IN_FILE))


class TestEveryDeclaredOptionIsClassified:
    def test_the_syntax_blocks_were_actually_found(self):
        """Guards the guard: the syntax-block scanner still finds dash.ado's
        declarations, so the classification below cannot pass on
        nothing."""
        # Exact, measured 24sep2026: the plot syntax block declares 160
        # (165 since GAPS2 X2 declared colorlevels(), colorvarminmax and
        # the three z options; the graph block 68 with the z options)
        # options (156 before the S3 batch declared acolor(), alcolor(),
        # alwidth() and alpattern()) and the graph block 65 (replace,
        # WP-27).  The `>= 130'/`>= 60' floors let a
        # syntax block shrink by twenty options -- silently un-classifying
        # them -- and still pass.
        # Flipped (WP-29 P0.5): 169 and 72, with ytick2(), xtick2(),
        # yline2() and xline2() declared in both blocks.
        # 169 -> 171: P1.5 xvarformat() and yvarformat() declared
        # Flipped (WP-30 P1.14a): 171 -> 177: astyle(), alstyle(),
        # bstyle(), blstyle(), clstyle() and p() declared.
        # 177 -> 180: P1.14b dstyle dlstyle bmlinestyle declared and named
        assert len(_declared_plot()) == 180, len(_declared_plot())
        assert len(_declared_graph()) == 72, len(_declared_graph())

    def test_every_declared_option_is_classified(self):
        """Pending, alias, route, or live -- a declared option with no
        classification is one the next maintainer must decide about."""
        declared = set(_declared_plot()) | set(_declared_graph())
        unclassified = sorted(declared - set(_plot_pending())
                              - set(_graph_pending()) - ALIASES
                              - set(NOT_IN_FILE) - set(LIVE_VALUES))
        assert not unclassified, (
            f"dash.ado declares {unclassified} and nothing here says whether "
            f"each is honoured (add LIVE_VALUES) or reported (add it to a "
            f"_dash_pending block and PLOT_VALUES)")

    def test_no_option_is_both_pending_and_live(self):
        """A structural guard over dash.ado's text and this file's tables,
        deliberately: no option is both named as ignored and expected to
        work.  For density -- the default, so a render cannot tell --
        this and test_a_histogram_y_axis_flag_is_never_reported_unsupported
        are the text-level half of SO-97."""
        both = sorted(set(LIVE_VALUES)
                      & (set(_plot_pending()) | set(_graph_pending())))
        assert not both, f"reported as ignored AND expected to work: {both}"

    def test_every_live_option_is_still_declared(self):
        """Table hygiene, deliberately over text: LIVE_VALUES names only
        options dash.ado still declares, so the render-diff tests driven by
        it are not probing options that no longer exist."""
        declared = set(_declared_plot()) | set(_declared_graph())
        gone = sorted(set(LIVE_VALUES) - declared)
        assert not gone, f"LIVE_VALUES names options dash.ado no longer declares: {gone}"


@pytest.mark.parametrize("opt", _plot_live())
def test_a_plot_option_not_reported_unsupported_really_works(tmp_path, opt):
    pa, ga, pb, gb, ptype = _live_pair(opt)
    first = _render(tmp_path, ptype, pa, ga, f"live_{opt}_a")
    second = _render(tmp_path, ptype, pb, gb, f"live_{opt}_b")
    assert first != second, (
        f"dash accepts plot-level {opt}() without naming it in the "
        f"ignored-option note, but {pa} and {pb} render byte-identical "
        f"dashboards -- it is silently dropped (or the probe values collide)")


@pytest.mark.parametrize("opt", _graph_live())
def test_a_graph_option_not_reported_unsupported_really_works(tmp_path, opt):
    pa, ga, pb, gb, ptype = _live_pair(opt)
    first = _render(tmp_path, ptype, pa, ga, f"glive_{opt}_a")
    second = _render(tmp_path, ptype, pb, gb, f"glive_{opt}_b")
    assert first != second, (
        f"dash accepts graph-level {opt}() without naming it in the "
        f"ignored-option note, but {ga} and {gb} render byte-identical "
        f"dashboards -- it is silently dropped (or the probe values collide)")


# ---------------------------------------------------------------------------
# The two route options, pinned by reading the ado, since no rendering can
# see them.  nodraw is the third: honoured at the browser-launch decision,
# so it must NOT be on the pending list -- it was, and the note said
# "ignoring unsupported option(s): nodraw()" for an option it had applied.
# ---------------------------------------------------------------------------

def _ado_program(name):
    with open(_ADO, encoding="utf-8") as fh:
        return _program_body(fh.read(), name) or ""


def test_nodraw_is_never_reported_unsupported():
    assert "nodraw" not in _plot_pending() and "nodraw" not in _graph_pending(), (
        "dash.ado honours nodraw at the browser-launch decision and must not "
        "name it in the ignoring-unsupported note")


def test_nodraw_is_still_read_by_the_launch_decision():
    assert '"nodraw":"nodraw"' in _ado_program("_dash_browser_wanted"), (
        "the browser-launch decision no longer reads the graph's nodraw")


def test_saving_is_still_extracted_by_the_immediate_render():
    assert '_dash_json_get_str(st_local("json_spec"), "saving"' in \
        _ado_program("_dash_render_immediate")
