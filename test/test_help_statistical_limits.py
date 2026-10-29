"""Where dash's statistical layers cannot match twoway's numbers, as the
help states it (WP-37 section 37-05, rulings M9, Q27 and Q40: documented,
no code change).

Each class reads one item's sentences and its one-line entry under
"Differences from twoway": lpolyci at a grid point whose pilot window has
no residual degrees of freedom (stat:PT-16), the estimators' numeric
limits (DT-26) and the order of points whose sort keys tie (stat:PT-21).
Where a sentence quotes a number, the test checks it against the committed
fixture it was read from.  The measurable claims are probed in
test_wp37_truth.cscript block S05 (Q3705-1..3).
"""

import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_HELP = os.path.join(_ROOT, "dash.sthlp")
_LPOLYCI = os.path.join(_HERE, "fixtures", "lpolyci_truth.json")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _help():
    return _read(_HELP)


def _between(text, start, end):
    i = text.index(start)
    j = text.index(end, i + len(start))
    return text[i:j]


def _flat(text):
    return " ".join(text.split())


def _differences():
    """The "Differences from twoway" section, flattened."""
    return _flat(_between(_help(), "{marker differences}",
                          "{marker subcommands}"))


def _smoother_options():
    """The Statistical Layer Options section, flattened."""
    return _flat(_between(_help(), "{marker smoother_options}",
                          "{marker weights}"))


def _entry(title):
    """One Differences entry, from its title to the next entry."""
    text = _differences()
    i = text.index(title)
    j = text.find("{phang2}", i)
    return text[i:] if j < 0 else text[i:j]


def _a_d3():
    cases = json.loads(_read(_LPOLYCI))["cases"]
    [case] = [c for c in cases if c["id"] == "a_d3"]
    return case


class TestLpolyciZeroDf:
    """stat:PT-16: where the pilot window has no residual degrees of
    freedom dash draws the band with zero width; twoway draws its own
    round-off there -- no band, or a band wide enough to rescale the y
    axis (lpolyci_truth.json case a_d3, grid indices 44-49)."""

    SENTENCE = (
        "At a grid point whose pilot window leaves no residual degrees of "
        "freedom, {cmd:dash} draws the band with zero width. {cmd:twoway} "
        "draws there what its own round-off gives: sometimes no band, and "
        "sometimes a finite band that can be very wide and rescale the y "
        "axis ({cmd:lpolyci mpg weight, degree(3)} draws -50.75 to 74.75 "
        "at a weight of 4,714, where the smooth is about 12, and no band "
        "at the three grid points before it and at the second after it).")

    def test_the_sentence(self):
        assert self.SENTENCE in _smoother_options()
        # the sentence's numbers are the fixture's
        c = _a_d3()
        assert round(c["gx"][47]) == 4714
        assert round(c["gy"][47]) == 12
        assert round(c["cl"][47], 2) == -50.75
        assert round(c["cu"][47], 2) == 74.75
        assert c["cu"][47] - c["cl"][47] > 100
        for j in (44, 45, 46, 49):
            assert c["cl"][j] is None and c["cu"][j] is None, j
        assert c["cl"][48] == c["cu"][48]
        assert c["degree"] == 3 and (c["y"], c["x"]) == ("mpg", "weight")

    def test_the_old_words_are_gone(self):
        assert "round-off, often missing" not in _flat(_help())

    def test_the_differences_entry(self):
        assert (
            "{ul:lpolyci where the pilot has no residual degrees of "
            "freedom.} {cmd:dash} draws zero width where {cmd:twoway} may "
            "draw a very wide band; see {help dash##smoother_options:"
            "Statistical layer options}.") in _differences()


def _validation():
    """The Option values paragraph under Differences, flattened."""
    return _flat(_between(_help(), "{marker validation}",
                          "{marker stylelists}"))


class TestNumericLimits:
    """DT-26 (and DECISIONS D45): each numeric limit of the estimators is
    stated with its measured value, and one Differences entry names them.
    lpoly mpg weight's r(bwidth) at degree 2, 6 and 8 was measured live
    (Q3705-2 re-measures degree 8); dash's are GlyphMapper's rule of
    thumb on the same data."""

    def test_degree_8_values(self):
        assert ("drawn with a note that the result can differ from "
                "Stata's (measured at degree 8 on {cmd:lpoly mpg weight}: "
                "a bandwidth of 400.94 where Stata's is 484.23), fitted at "
                "most at degree 30") in _validation()

    def test_the_differences_entry(self):
        entry = _entry("{ul:Numeric limits of the estimators.}")
        for name in ("{cmd:lpoly}'s default bandwidth at degree 2 and 3",
                     "at degree 6 and above",
                     "three exact-polynomial cases",
                     "{cmd:fpfit} on a date-time {it:x}",
                     "{cmd:dot}'s dots above 2,000,000",
                     "{help dash##smoother_options:Statistical layer "
                     "options}"):
            assert name in entry, name

    def test_the_stated_values(self):
        opts = _smoother_options()
        # D45: degree 2's round-off (lpoly_rot_truth.json's degree-2 row
        # on auto: 120.792907978892; dash 120.793187809046; the curve
        # against lpolyci_truth.json's a_d2 and a_d3, 3.7e-6 and 4.7e-6
        # of its value, measured 29oct2026)
        assert ("At degree 2 and 3 Stata's round-off shows only in the last "
                "digits ({cmd:lpoly mpg weight, degree(2)}: 120.7932 where "
                "{cmd:r(bwidth)} is 120.7929), and a point of the curve "
                "differs from Stata's by less than 5e-6 of its value.") in opts
        rows = {r["id"]: r for r in json.loads(_read(os.path.join(
            _HERE, "fixtures", "lpoly_rot_truth.json")))["rows"]}
        assert round(rows["auto-mpg-weight--epanechnikov-d2-n74"]["bwidth"],
                     4) == 120.7929
        # degree 6 and 7, and above 7
        assert ("({cmd:lpoly mpg weight, degree(6)}: 386.3 where "
                "{cmd:r(bwidth)} is 390.0); above degree 7 the two part further "
                "(degree 8: 400.94 where {cmd:r(bwidth)} is 484.23)") in opts
        # the three exact-polynomial cases, each a divergence of the fixture
        assert ("three cases are drawn differently: y exactly linear in x "
                "at {cmd:degree(0)}; y equal to x at {cmd:degree(0)} or "
                "{cmd:degree(1)}; and a y as small as 1e-150 times "
                "{cmd:mpg} at {cmd:degree(2)}") in opts
        div = json.loads(_read(os.path.join(
            _HERE, "fixtures", "lpoly_rot_truth.json")))["divergences"]
        assert [d["id"] for d in div] == ["D1", "D2", "D3"]
        # fpfit on a date-time x
        assert ("the curves then differ by no more than 5e-4 of their "
                "range (measured)") in opts
        # dot's thinning, at the renderer's own bound
        assert ("Above 2,000,000 dots in one layer {cmd:dash} draws fewer "
                "and says how many.") in _flat(_help())
        assert "_DASH_DOTS_MAX = 2_000_000\n" in _read(
            os.path.join(_ROOT, "dash_render.py"))


class TestTies:
    """stat:PT-21 (with BY-30 and DG-16): points whose sort keys tie are
    joined in the data's order in dash; twoway's order among them changes
    from run to run (BY-30's verifier: line mpg weight, sort by(foreign)
    four times in one session), which shows in three places."""

    def test_the_three_places(self):
        text = _flat(_between(_help(), "{ul:Join order.}",
                              "Strings sort byte by byte"))
        assert (
            "Points whose keys tie keep the order of the data. {cmd:twoway}'s "
            "order among them is not fixed -- it changes from one run to the "
            "next, so no fixed order can match it -- which shows where tied "
            "points are joined: the path of a {cmd:lowess} through a tied "
            "{it:x}, a {cmd:sort} under {cmd:by()}, and where "
            "{cmd:cmissing(n)} breaks a line at a tie.") in text

    def test_the_differences_entry(self):
        assert (
            "{ul:Points whose sort keys tie.} {cmd:dash} joins them in the "
            "data's order; {cmd:twoway}'s order among them changes from run "
            "to run; see {help dash##plottypes:Plot types}.") in _entry(
                "{ul:Points whose sort keys tie.}")
