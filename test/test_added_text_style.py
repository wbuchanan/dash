"""
test_added_text_style.py -- added text's tstyle() and the globals its lines
name (WP-31 D13, section 30).

The defect: dash.ado named text(..., tstyle()) and did not draw it, and a
line naming a global -- ``text(30 2000 "$label")`` reached by a command
twoway would draw it from, the $ kept by an escape or macval() -- was drawn
as the literal ``$label``.

twoway's rule (test/fixtures/textbox_truth.json, scripts/
extract_textbox_truth.do): ``text(30 2000 "P", tstyle(heading))`` draws P
in the heading's size (139.96 SVG units, 14pt); twoway expands ``$u30x``
and ``${u30x}`` to the global's value (hello, hello!), ``$$u30f$$`` to
``$$`` (the inner ``$u30f`` is F, ``$F`` empty), and a global holding
```=1+1'!`` is evaluated, 2!.

dash's rule: the lines are expanded once at registration by a textual
substitution of the globals' values (dash_parse.mata ``_dash_at_globals``)
that never evaluates: a global holding ```=1+1'!`` or ```c(pwd)'`` is
drawn as written (the documented difference from twoway, which evaluates
it).  The dash side is test/fixtures/added_text_globals.json, written by
scripts/extract_added_text_globals.do: each row the at_lines dash.ado
registered for its command, run through macval() so the do-file leaves
the $ for dash.
"""
import json
import os
import sys
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

from bokeh.models import Label  # noqa: E402

import dash_render as dr  # noqa: E402
import test_mode_parity as tp  # noqa: E402

MODES = ("saved", "served")

with open(os.path.join(_HERE, "fixtures", "textbox_truth.json"),
          encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)
with open(os.path.join(_HERE, "fixtures", "added_text_globals.json"),
          encoding="utf-8") as _fh:
    DASH = json.load(_fh)


def _rec(opts="", lines=("P",)):
    return {"at_kind": "text", "at_y": 30, "at_x": 2000, "at_yaxis": 1,
            "at_xaxis": 1, "at_lines": list(lines), "at_opts": opts}


def _labels(mode, opts):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        figs, _c = tp._figures_in(mode, tp._spec(
            [tp._sc()], {"scheme": "s2color"},
            {"added_text": [_rec(opts)]}))
    labs = [m for m in figs[0].center if isinstance(m, Label)
            and "dash_added_text" in (m.tags or [])]
    return labs, [str(w.message) for w in caught] + list(_c or [])


class TestAddedTextTstyle:

    @pytest.mark.parametrize("mode", MODES)
    def test_drawn(self, mode):
        assert "tstyle" in dr._DASH_ADDED_TEXT_HONOURED
        (lab,), caught = _labels(mode, "tstyle(heading)")
        s = dr.SchemeParser.resolve_or_fallback("s2color", "x")
        assert lab.text_font_size == s.textbox_style("heading")[0] == "14pt"
        assert lab.text_color == s.textbox_style("heading")[1]
        assert not [w for w in caught if "tstyle" in w], caught
        # twoway: P at heading's 139.96 SVG units.
        p = [t for t in TRUTH["at_tstyle"]["texts"] if t["text"] == "P"][0]
        assert p["size"] == pytest.approx(139.96)

    @pytest.mark.parametrize("mode", MODES)
    def test_size_wins(self, mode):
        (lab,), _c = _labels(mode, "size(small) tstyle(heading)")
        assert lab.text_font_size == "8pt"

    def test_unknown_named_once(self):
        (lab,), caught = _labels("saved", "tstyle(nosuch)")
        s = dr.SchemeParser.resolve_or_fallback("s2color", "x")
        assert lab.text_font_size == s.textbox_style("body")[0]
        assert len([w for w in caught if "named style nosuch not found in "
                    "class textboxstyle" in w]) == 1, caught


class TestGlobals:

    @pytest.mark.parametrize("case", ["global_plain", "global_dollars",
                                      "global_braces"])
    def test_substituted(self, case):
        """dash registers the line twoway draws."""
        assert DASH[case]["rc"] == 0
        assert DASH[case]["command"] in TRUTH[case]["command"]
        assert DASH[case]["at_lines"] == [TRUTH[case]["text"]]

    def test_each_line_and_an_unset_global(self):
        assert DASH["two_lines"]["at_lines"] == ["hello", "xF"]
        assert DASH["unset"]["at_lines"] == ["a b"]


class TestGlobalsAreSubstitutedNotEvaluated:

    @pytest.mark.parametrize("case,glob", [("eval_expr", "u30e"),
                                           ("eval_pwd", "u30p")])
    def test_raw(self, case, glob):
        """A global's value is drawn as written, never evaluated: twoway
        draws 2! for ```=1+1'!`` (global_eval), dash the value itself."""
        raw = DASH["_meta"]["globals"][glob]
        assert raw.startswith("\x60") and "'" in raw
        assert DASH[case]["at_lines"] == [raw]
        if case == "eval_expr":
            assert TRUTH["global_eval"]["text"] == "2!"
