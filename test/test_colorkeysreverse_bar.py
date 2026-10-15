"""
test_colorkeysreverse_bar.py -- colorkeysreverse on a colorvar() colour key
that is not discrete (WP-31 C8e, section 26; DECISIONS D18).

The defect (S17's residual, at b1810e4): ``dash scatter mpg weight,
colorvar(price) colorkeysreverse`` drew the colour bar and named the option
in the note, "drawn unreversed", as if twoway reversed that key.

twoway (StataNow 19.5, scripts/extract_colorvar_options_truth.do probes
D14, D14r, D14br and D14kr, fixture test/fixtures/colorvar_options_truth.json):
on a key that is not discrete -- unbinned (colorvar(price)), binned by
colorlevels(4), and with colorkeysrange -- colorkeysreverse changes nothing:
the same swatches in the same order, the same texts.  Only a discrete key
(colordiscrete, D12) is reversed, which dash already draws.

dash's colour bar is therefore drawn as it is without the option, and the
option is taken in silence, in both modes.
"""
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

from bokeh.models import ColorBar  # noqa: E402

import test_colorvar_options as cvo  # noqa: E402
from test_colorvar_options import tmp  # noqa: E402,F401  (the fixture)

PROBES = cvo.PROBES
_REV = {"colorkeysreverse": "colorkeysreverse"}

#: The key with colorkeysreverse and the same key without it.
_PAIRS = [("D14r", "D14"), ("D14br", "D11b"), ("D14kr", "D11")]

#: dash's options for the measured keys that are colour bars.
_BARS = {"unbinned": {"colorvar": "price"}}


class TestTheMeasurement:

    @pytest.mark.parametrize("rev,plain", _PAIRS)
    def test_twoway_draws_the_same_key(self, rev, plain):
        a, b = PROBES[rev], PROBES[plain]
        assert a["rc"] == b["rc"] == 0
        assert a["key"] == b["key"], (a["key"], b["key"])
        # The discrete key is the one twoway reverses.
        assert PROBES["D12"]["key"]["fills"] != \
            PROBES["D01"]["key"]["fills"]


def _bar(fig):
    [cb] = [m for side in (fig.right, fig.left, fig.above, fig.below)
            for m in side if isinstance(m, ColorBar)]
    return cb


def _bar_view(cb):
    m = cb.color_mapper
    return (list(m.palette), m.low, m.high, list(cb.ticker.ticks),
            dict(cb.major_label_overrides), cb.title)


class TestDashDrawsItSilently:

    @pytest.mark.parametrize("mode", cvo.MODES)
    @pytest.mark.parametrize("name", sorted(_BARS))
    def test_the_bar_is_unchanged_and_nothing_is_named(self, tmp, mode,
                                                       name):
        opts = _BARS[name]
        plain_figs, _w0 = cvo._figs(tmp, mode, [cvo.plot_for("scatter",
                                                             dict(opts))])
        rev_figs, w = cvo._figs(tmp, mode, [cvo.plot_for(
            "scatter", dict(opts, **_REV))])
        assert _bar_view(_bar(rev_figs[0])) == _bar_view(_bar(plain_figs[0]))
        assert not [x for x in w if "colorkeysreverse" in x], w
