"""Stylelist edge forms read or refused as twoway does (WP-31 E4).

Measured in StataNow 19.5 (16oct2026; test/fixtures/
colour_width_edges_truth.json sl.*, scripts/
extract_colour_width_edges_truth.do, and the probes the section's
hand-back records):

- an element with a glued ``=`` inside or after it (``red=blue``,
  ``red=``, ``T=O``) draws the default for that y, silently, rc 0 --
  ``mcolor(red=blue green)`` is p1's navy then green; dash drew black
  with a "not a recognised colour" note;
- an element opening with ``(`` (``(red)``, ``"(red)"``, ``red (blue)``)
  is read as an option and refused, "option(s) ( red ) not allowed",
  r(198); dash drew it black;
- an element led by a glued ``=`` (``=blue``) is refused, r(198), with a
  class path ("color.editstyle invalid name"); dash refuses it in its
  own words;
- an unknown msymbol() element is noted and the scheme's symbol drawn
  (circles under s2color), as S40 already draws it.

The Stata half runs in test_option_validation.cscript U41-11, U41-12 and
test_wp31_truth.cscript U41-02..U41-04; this module pins the fixture,
the code's structure and the renderer's half.
"""
import json
import os
import re
import sys

import pytest
from bokeh.models import GlyphRenderer

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402
from test_abbreviations import _program_body  # noqa: E402
from test_scheme_resolution import MODES, _draw  # noqa: E402

with open(os.path.join(_HERE, "fixtures", "colour_width_edges_truth.json"),
          encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)

_MATA = os.path.join(_HERE, "..", "dash_parse.mata")
_ADO = os.path.join(_HERE, "..", "dash.ado")


def _mata_fn(name):
    with open(_MATA, encoding="utf-8") as fh:
        src = fh.read()
    m = re.search(r"^\w+ \w+ %s\(.*?^\}" % re.escape(name), src, re.S | re.M)
    assert m, name
    return m.group(0)


class TestStylelistEdges:
    def test_glued_equals_matches_twoway(self):
        for key in ("sl.eq_glued", "sl.eq_trail"):
            rec = TRUTH[key]
            assert rec["rc"] == 0 and rec["text"] == "", key
            fills = [e[1] for e in rec["elements"]
                     if e[0] == "circle" and e[1] not in ("", "none")]
            assert fills == ["#1a476f", "#90353b"], (key, fills)
        pick = _mata_fn("_dash_stylelist_pick")
        assert 'else if (bare & strpos(t, "=") > 1) v = ""' in pick

    def test_paren_is_refused_or_drawn(self):
        rec = TRUTH["sl.paren"]
        assert rec["rc"] == 198
        assert rec["text"] == "option(s) ( red ) not allowed"
        assert "_dash_stylelist_paren" in _mata_fn("_dash_stylelist_paren")
        with open(_ADO, encoding="utf-8") as fh:
            body = _program_body(fh.read(), "_dash_stylelist_check")
        assert "_dash_stylelist_paren(" in body
        assert '"option(s) ", st_local("_sl_p"), " not allowed"' in body
        assert "_dash_stylelist_eqlead(" in body

    def test_both_are_required(self):
        with open(_ADO, encoding="utf-8") as fh:
            src = fh.read()
        for name in ("_dash_stylelist_paren", "_dash_stylelist_eqlead"):
            assert re.search(r"_needed[^\n]*\n(?:.*\n){0,80}.*\b%s\b" % name,
                             src), name

    @pytest.mark.parametrize("mode", MODES)
    def test_unknown_symbol_element(self, mode):
        rec = TRUTH["sl.msym_unknown"]
        assert rec["rc"] == 0 and "named style bogus not found" in rec["text"]
        assert {e[0] for e in rec["elements"]
                if e[1] in ("#1a476f", "#90353b")} == {"circle"}
        d = _draw(tp._spec([{"type": "scatter", "yvar": "mpg",
                             "xvar": "weight",
                             "options": {"msymbol": "bogus"}}],
                           {"scheme": "s2color"}), mode)
        gs = [r.glyph for r in d.figures[0].renderers
              if isinstance(r, GlyphRenderer) and not dr._dash_is_swatch(r)]
        assert gs[0].marker == "circle"
        assert len([w for w in d.warnings if "bogus" in w]) == 1
