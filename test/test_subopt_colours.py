"""Comma colours, the width multiplier and the UNCLEAR pair (WP-31 E5).

Measured in StataNow 19.5 (16oct2026; test/fixtures/
colour_width_edges_truth.json, scripts/extract_colour_width_edges_truth.do):

- a colour written with commas in a colour sub-option of title(),
  subtitle(), note(), caption(), xline(), yline(), xlabel(), ylabel(),
  plotregion() and graphregion() (color and lcolor) and legend() is
  refused, "invalid '2'" for "1,2,3", r(198) (sc.*); dash drew it black
  with a note.  dash.ado refuses it (Mata _dash_subopt_colour_comma);
  the Stata half is test_option_validation.cscript U41-13 and
  test_wp31_truth.cscript U41-05, U41-10;
- mcolor("red",blue) draws red, silently (sl.quoted_comma); dash drew
  black with a note;
- lwidth(*#) multiplies the unfloored width and floors after: under a
  scheme whose line is vvthin, *10 and *2 draw the 0.3 pt floor (lw.*),
  and on medium *2, *.5 and *10 draw 17.28, 4.32 and 86.40 SVG units;
- mcolor(navy*52) draws #010304 and mcolor(bg fg) a background-outlined
  first series: recorded only, UNCLEAR by decision (D-41c).
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
from test_server_layer_defects import plot_for  # noqa: E402

with open(os.path.join(_HERE, "fixtures", "colour_width_edges_truth.json"),
          encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)

T = dr.OptionTranslator
#: dash's pixels per twoway SVG unit (0.1 pt).
PX_PER_UNIT = 0.1 * T.PX_PER_PT
HOSTS = ("title", "subtitle", "note", "caption", "xline", "yline",
         "xlabel", "ylabel", "plotregion", "graphregion", "legend")
_ADO = os.path.join(_HERE, "..", "dash.ado")
_MATA = os.path.join(_HERE, "..", "dash_parse.mata")


def _series_stroke(key):
    return float([e for e in TRUTH[key]["elements"]
                  if e[0] == "path" and e[2] == "#1a476f"][0][3])


class TestSubOptionCommaColours:
    @pytest.mark.parametrize("host", HOSTS)
    def test_each_host(self, host):
        recs = {k: v for k, v in TRUTH.items() if k.startswith(f"sc.{host}.")}
        assert recs, host
        for k, rec in recs.items():
            assert rec["rc"] == 198 and rec["text"] == "invalid '2'", k
        with open(_ADO, encoding="utf-8") as fh:
            src = fh.read()
        assert "_dash_subopt_colour_check" in _program_body(
            src, "_dash_validate_opts")
        body = _program_body(src, "_dash_subopt_colour_check")
        m = re.search(r"foreach _h in ([a-z ]+) \{\n\s+mata: st_local\(\"_sc\", "
                      r"_dash_subopt_colour_comma", body)
        assert m and host in m.group(1).split(), host

    def test_the_reader_compares_text(self):
        with open(_MATA, encoding="utf-8") as fh:
            src = fh.read()
        fn = re.search(r"^string scalar _dash_subopt_colour_comma\(.*?^\}",
                       src, re.S | re.M).group(0)
        assert "_dash_rep_toks(value, 1)" in fn
        assert "stata(" not in fn and "st_global" not in fn

    @pytest.mark.parametrize("mode", MODES)
    def test_quoted_comma_draws_its_string(self, mode):
        rec = TRUTH["sl.quoted_comma"]
        assert rec["rc"] == 0 and rec["text"] == ""
        assert [e[1] for e in rec["elements"]
                if e[0] == "circle" and e[1] not in ("", "none")] == \
            ["#ff0000"]
        with open(_MATA, encoding="utf-8") as fh:
            assert 'substr(stem, p, 1) == ","' in fh.read()
        # dash.ado writes the element's string, "red", into the spec.
        d = _draw(tp._spec([plot_for("scatter", {"mcolor": "red"})],
                           {"scheme": "s2color"}), mode)
        gs = [r.glyph for r in d.figures[0].renderers
              if isinstance(r, GlyphRenderer) and not dr._dash_is_swatch(r)]
        assert gs[0].fill_color == "#ff0000" and not d.warnings


class TestWidthMultiplierFloor:
    def test_order(self):
        vv_pt = T._LWIDTH_RS["vvthin"] * T.PT_PER_RS
        floor_units = _series_stroke("lw.vvthin")
        assert floor_units == 3.0
        for key, mult in (("lw.vvthin_x10", "*10"), ("lw.vvthin_x2", "*2")):
            assert _series_stroke(key) == floor_units, key
            assert T.translate_lwidth(mult, default_pt=vv_pt) == \
                pytest.approx(_series_stroke(key) * PX_PER_UNIT), key
        med_pt = T._LWIDTH_RS["medium"] * T.PT_PER_RS
        for key, mult in (("lw.medium_x2", "*2"), ("lw.medium_x0_5", "*.5"),
                          ("lw.medium_x10", "*10")):
            assert T.translate_lwidth(mult, default_pt=med_pt) == \
                pytest.approx(_series_stroke(key) * PX_PER_UNIT), key

    @pytest.mark.parametrize("mode", MODES)
    def test_plot_line_under_a_vvthin_scheme(self, mode, tmp_path,
                                             monkeypatch):
        """The plot path multiplies the scheme's unfloored width."""
        (tmp_path / "u41w.scheme").write_text(
            "#include s2color\nlinewidth p vvthin\n", encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        for mult in ("*10", "*2"):
            d = _draw(tp._spec([plot_for("line", {"lwidth": mult})],
                               {"scheme": "u41w"}), mode)
            gs = [r.glyph for r in d.figures[0].renderers
                  if isinstance(r, GlyphRenderer)
                  and not dr._dash_is_swatch(r)]
            assert gs[0].line_width == pytest.approx(
                _series_stroke("lw.vvthin_x10") * PX_PER_UNIT), mult


class TestUnclearStaysDocumented:
    def test_values(self):
        navy = [e[1] for e in TRUTH["unclear.navy52"]["elements"]
                if e[0] == "circle" and e[1] not in ("", "none")]
        assert navy == ["#010304"]
        with open(os.path.join(_HERE, "..", "dash.sthlp"),
                  encoding="utf-8") as fh:
            hlp = fh.read()
        assert "{cmd:mcolor(navy*52)}" in hlp and "#010304" in hlp
