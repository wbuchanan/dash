"""WP-34 AX-2 (section 34-02): a by() graph's first x axes are ticked at
the scheme's count less one, as its y axes are.

twoway's by() styles (bygraphstyle-default/compact/altleg/econ.style)
set ``xlabels(#4) ylabels(#4)``, so every by() panel's first x axis takes
one tick fewer than the scheme's 5, as y does.  dash lowered y only: in
both modes ``scatter mpg length, by(foreign)`` drew x 140(20)240 where
twoway draws 150 200 250, and ``scatter mpg displacement, by(foreign)``
100(100)500 where twoway draws 100(100)400.

The truth is ``test/fixtures/by_scales_truth.json`` probes x01-x05
(``scripts/extract_by_scales_truth.do``); pages are drawn through
test_by_scales.py's ``_spec``/``_draw`` helpers.

While iterating: ``python3 -m pytest test/test_by_tick_count.py -q``.
"""
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_by_scales as tb  # noqa: E402
import test_default_axes as tda  # noqa: E402

_MODES = ("saved", "served")
P = tb._plot

#: probe id -> (plots, graph options), twoway's command in the fixture.
_ROWS = {
    "x01": ([P("scatter", "mpg", "length")], {"by": "foreign"}),
    "x02": ([P("scatter", "mpg", "length")], {"by": "foreign, cols(1)"}),
    "x03": ([P("scatter", "mpg", "length")], {"by": "rep78"}),
    "x04": ([P("scatter", "mpg", "length")], {"by": "foreign",
                                               "xsize": "10"}),
    "x05": ([P("scatter", "mpg", "displacement")], {"by": "foreign"}),
}


def _want(panel, letter):
    a = panel[letter]
    return tb._steps(a["major_min"], a["major_max"], a["major_delta"])


class TestTheCount:
    def test_the_rule(self):
        sch = dr.SchemeParser("stcolor")
        assert dr._dash_by_numticks(sch, {"by": "foreign"}) == {
            "x": 4, "y": 4, "x2": 5, "y2": 5}
        assert dr._dash_by_numticks(sch, {}) == {
            "x": 5, "y": 5, "x2": 5, "y2": 5}

    def test_style_combine_keeps_the_schemes_count(self):
        """WP-41 41-05 pair 2: by(rep78, style(combine)) draws each panel
        as graph combine draws a graph, at the scheme's count (twoway's
        SVG, figure_geometry_truth P2: panel 1's x 2,800(200)3,600, Stata's
        _natscale 2730 3470 5; #4 is 2,800(200)3,400; panel 4's x
        1,500(500)4,000, #5's, where #4 is 2,000(1,000)4,000)."""
        sch = dr.SchemeParser("stcolor")
        routed = dr._dash_bystyle_route({"graphs": [{"graph_options": {
            "by": "rep78, style(combine)"}}]})
        go = routed["graphs"][0]["graph_options"]
        assert dr._dash_by_is_combine(go["by"])
        assert dr._dash_by_numticks(sch, go) == {
            "x": 5, "y": 5, "x2": 5, "y2": 5}


class TestAgainstStata:
    @pytest.mark.parametrize("mode", _MODES)
    def test_rows(self, mode):
        """x01-x05: every panel's x and y ticks are twoway's."""
        bad = []
        for pid, (plots, go) in sorted(_ROWS.items()):
            probe = tb._probe(pid)
            assert probe["rc"] == 0, pid
            figs, _ = tb._draw(mode, tb._spec(plots, go))
            figs = [f for f in tb._panels(figs) if tb._title(f)]
            assert len(figs) == probe["n"], (pid, len(figs))
            for f, panel in zip(figs, probe["panels"]):
                for letter, ax in (("x", tb._bottom(f)), ("y", tb._left(f))):
                    got = tb._major_ticks(ax)
                    if got != _want(panel, letter):
                        bad.append("%s %s %s: dash %s, twoway %s" % (
                            pid, panel["title"], letter, got,
                            _want(panel, letter)))
        assert not bad, "\n".join(bad)


#: A price range whose kept lengths (147-233) tick differently at #4
#: (150 200 250) and #5 (140(20)240).
_MOVE = (4000.0, 15906.0)


def _kept_x_ticks():
    df = tb._frame()
    lo, hi = _MOVE
    rows = df[(df.price >= lo) & (df.price <= hi)]
    return [float(v) for v in dr._dash_natscale_ticks(
        rows.length.min(), rows.length.max(), 4)]


class TestAfterAMove:
    def _check(self, mode):
        spec = tda._spec(_ROWS["x01"][0], _ROWS["x01"][1],
                         filt=tda._RANGE[0])
        figs = tda._after(mode, spec, tda._RANGE[1], _MOVE)
        figs = [f for f in figs if tb._title(f)]
        assert len(figs) == 2
        want = _kept_x_ticks()
        assert want == [150.0, 200.0, 250.0]
        for f in figs:
            assert tda._ticks(f, "x") == want

    def test_saved(self):
        """The saved page's node re-finish ticks x at #4 over the kept
        rows."""
        self._check("saved")

    def test_served(self):
        """The served refit ticks x at #4 over the kept rows."""
        self._check("served")


class TestTheHelp:
    def test_the_count_sentence(self):
        import test_help_claims_1 as hc
        text = hc._between(
            " ".join(hc._help().split()),
            "With no {cmd:xlabel()} or {cmd:ylabel()} rule", "A zoom or pan")
        assert ("a {cmd:by()} graph's panels take one fewer on their "
                "first x and y axes, as {cmd:twoway}'s by() styles set "
                "them") in text
        assert "one fewer on y," not in text
