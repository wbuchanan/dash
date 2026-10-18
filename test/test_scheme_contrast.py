"""test_scheme_contrast.py -- WCAG AA contrast of the shipped schemes' text
(WP-31 K6, section 54, D-54c).

Each of the 26 ``dash-*.scheme`` files at the repository root is read
through ``SchemeParser`` and five text/background pairs are measured with
WCAG 2's relative-luminance formula:

* ``text/background``  -- ``color text`` on ``color background``;
* ``text/plotregion``  -- ``color text`` on ``color plotregion``;
* ``text/legend``      -- ``color text`` on ``color legend``;
* ``tick/plotregion``  -- ``color tick_label`` (else ``color text``) on
  ``color plotregion``;
* ``kpi/legend``       -- the KPI card's value colour (``color text``) on
  its box (``color legend``).

AA asks 4.5:1 of body text.  A pair below it is listed in
``KNOWN_LOW_CONTRAST`` with its measured ratio, and dash.sthlp's
Accessibility paragraph names the scheme.  The test fails on an unlisted
failure and on a listed pair that now passes, so the list and the help
cannot drift from the schemes.  The scheme files are not changed (they are
Stata's colours; M7/M17).
"""
import glob
import os
import re
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")
sys.path.insert(0, _ROOT)

import dash_render as dr  # noqa: E402

#: WCAG 2.x AA, normal text.
AA = 4.5

#: The shipped schemes, by the name SchemeParser takes.
SCHEMES = sorted(os.path.basename(p)[len("dash-"):-len(".scheme")]
                 for p in glob.glob(os.path.join(_ROOT, "dash-*.scheme")))

PAIRS = ("text/background", "text/plotregion", "text/legend",
         "tick/plotregion", "kpi/legend", "sidebar/background")

#: Every (scheme, pair) below AA, with the ratio measured on the scheme
#: files at this section's base (2c53468), rounded to 3 decimals.
KNOWN_LOW_CONTRAST = {
}


def rel_lum(hexcolour):
    """WCAG 2 relative luminance of ``#rrggbb``."""
    h = hexcolour.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = out
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    """WCAG 2 contrast ratio of two ``#rrggbb`` colours, 1 .. 21."""
    la, lb = rel_lum(a), rel_lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


_PARSED = {}


def _scheme(name):
    if name not in _PARSED:
        _PARSED[name] = dr.SchemeParser(name)
    return _PARSED[name]


def _pair_colours(name, pair):
    sp = _scheme(name)
    tick = (sp.tick_label_color if "color tick_label" in sp._props
            else sp.text_color)
    if pair == "sidebar/background":
        # The layout(bs) left sidebar's "Filters" label on the page
        # (WP-31 K6 follow-up: axe color-contrast on comprehensive_demo).
        return (_sidebar_colour(sp), sp.background_color)
    return {
        "text/background": (sp.text_color, sp.background_color),
        "text/plotregion": (sp.text_color, sp.plotregion_color),
        "text/legend": (sp.text_color, sp.legend_bg_color),
        "tick/plotregion": (tick, sp.plotregion_color),
        "kpi/legend": (sp.text_color, sp.legend_bg_color),
    }[pair]


def _sidebar_colour(sp):
    m = re.search(r"\.db-sidebar-label\s*\{\s*color:\s*(#[0-9a-fA-F]{6})",
                  dr._dash_sidebar_label_css(sp))
    assert m, "no colour in _dash_sidebar_label_css"
    return m.group(1)


def _ratio(name, pair):
    fg, bg = _pair_colours(name, pair)
    return round(contrast(fg, bg), 3)


class TestAA:

    def test_there_are_26_schemes(self):
        assert len(SCHEMES) == 26, SCHEMES

    @pytest.mark.parametrize("pair", PAIRS)
    @pytest.mark.parametrize("scheme", SCHEMES)
    def test_pair(self, scheme, pair):
        r = _ratio(scheme, pair)
        if (scheme, pair) in KNOWN_LOW_CONTRAST:
            assert r == KNOWN_LOW_CONTRAST[(scheme, pair)], (
                f"{scheme} {pair}: measured {r}, listed "
                f"{KNOWN_LOW_CONTRAST[(scheme, pair)]}")
            return
        fg, bg = _pair_colours(scheme, pair)
        assert r >= AA, (f"{scheme} {pair}: {fg} on {bg} is {r}:1, below "
                         f"AA {AA}:1 and not in KNOWN_LOW_CONTRAST")

    def test_the_known_list_is_current(self):
        """A listed pair that now meets AA is taken off the list (and out
        of the help)."""
        stale = {k: v for k, v in KNOWN_LOW_CONTRAST.items()
                 if _ratio(*k) >= AA}
        assert stale == {}, stale

    def test_the_known_list_names_shipped_schemes(self):
        assert {s for s, _p in KNOWN_LOW_CONTRAST} <= set(SCHEMES)
        assert {p for _s, p in KNOWN_LOW_CONTRAST} <= set(PAIRS)

    def test_the_help_names_every_low_contrast_scheme(self):
        with open(os.path.join(_ROOT, "dash.sthlp"), encoding="utf-8") as fh:
            text = fh.read()
        i = text.find("{title:Accessibility}")
        assert i >= 0, "dash.sthlp has no Accessibility paragraph"
        j = text.find("{title:", i + 10)
        para = text[i:j if j > 0 else len(text)]
        for s in sorted({s for s, _p in KNOWN_LOW_CONTRAST}):
            assert s in para, f"the help's Accessibility paragraph omits {s}"

    def test_the_formula_is_wcag(self):
        assert round(contrast("#000000", "#ffffff"), 3) == 21.0
        assert round(contrast("#777777", "#ffffff"), 3) == 4.478
        assert round(contrast("#ffffff", "#ffffff"), 3) == 1.0
