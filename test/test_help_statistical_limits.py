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
