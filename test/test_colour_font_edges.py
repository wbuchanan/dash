"""Colour intensity at Stata's clamp, blank style-list elements, and the
svg translator's plain-text font face (WP-45 section 45-05: ST-22, GW-10).

Measured in StataNow 19.5 (test/fixtures/colour_edges_truth.json,
scripts/extract_colour_edges_truth.do, s2color, the marker fill of
``scatter mpg weight, mcolor(<c>*<k>)``):

- I_*: seven colours at seventeen intensities.  ``navy*52`` is #010304
  (dash drew #010102), ``navy*51`` #010102.
- H_<c>: ``"<c> 255 255*<2c>"``, the smallest channel at exactly a half.
  Stata's own arithmetic rounds it down -- and so clamps -- for 60 values
  of c, all at most 127, and up for the rest; no float model of the
  division reproduces the set, so it is read from the measurement
  (``GlyphMapper._HALF_CLAMP``).  N_* (another channel at a half) and
  M_* (the clamp's division at a half) round half up.
- B_<option>: ``<option>(" " p1)`` on two y.  twoway refuses a used blank
  element, r(198), naming the option's class path: ``option(s)
  marker(fillcolor(`')  linestyle(color(`'))) not allowed`` for mcolor().
- F_query: ``translator query gph2svg`` (read only; no ``graph set``).
"""
import json
import os
import re
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, os.path.join(_HERE, "..", "scripts"))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402

with open(os.path.join(_HERE, "fixtures", "colour_edges_truth.json"),
          encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)
ROWS = TRUTH["rows"]
_MATA = os.path.join(_HERE, "..", "dash_parse.mata")
_ADO = os.path.join(_HERE, "..", "dash.ado")
_HELP = os.path.join(_HERE, "..", "dash.sthlp")
_I_ROWS = sorted(k for k in ROWS if k.startswith("I_"))


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _rgb_and_k(value):
    """``"26 255 255*52"`` -> ((26, 255, 255), 52.0)."""
    body, _, k = value.strip('"').partition("*")
    return tuple(int(x) for x in body.split()), float(k)


class TestIntensity:
    @pytest.mark.parametrize("row", _I_ROWS)
    def test_row(self, row):
        rec = ROWS[row]
        st, hx, _a = dr.OptionTranslator.stata_colour(rec["value"])
        assert (st, hx) == ("ok", rec["fill"]), rec["value"]

    def test_the_half_rows(self):
        """Every H_, N_ and M_ row: the blend equals twoway's fill."""
        bad = []
        for key, rec in sorted(ROWS.items()):
            if key[:2] not in ("H_", "N_", "M_"):
                continue
            rgb, k = _rgb_and_k(rec["value"])
            got = dr.GlyphMapper._blend_intensity("#%02x%02x%02x" % rgb, k)
            if got != rec["fill"]:
                bad.append(f"{key} {rec['value']}: {got} != {rec['fill']}")
        assert not bad, "\n".join(bad[:20])

    def test_the_half_set_is_the_measured_one(self):
        """_HALF_CLAMP holds exactly the c whose H_ row clamped."""
        clamped = set()
        for key, rec in ROWS.items():
            if not key.startswith("H_"):
                continue
            (c, _g, _b), _k = _rgb_and_k(rec["value"])
            g = (2 * 255 + c) // (2 * c)        # 255 / c, half up
            h = (255 + c) // (2 * c)            # 255 / 2c, half up
            if g != h and rec["fill"] == "#01%02x%02x" % (g, g):
                clamped.add(c)
            # Where the two agree (c > 170) the row cannot tell them
            # apart, and any c there draws the same either way.
        assert set(dr.GlyphMapper._HALF_CLAMP) == clamped

    def test_the_old_grid(self):
        """colour_grammar_truth.json's option probes all still match, navy*52
        (opt_17) among them and excluded no more."""
        with open(os.path.join(_HERE, "fixtures", "colour_grammar_truth.json"),
                  encoding="utf-8") as fh:
            d = json.load(fh)
        assert "opt_17" not in d["_meta"]["excluded"]
        bad, n = [], 0
        for pid, p in sorted(d["probes"].items()):
            if p["group"] != "opt" or p["kind"] != "marker" or p["owner"]:
                continue
            if "*" not in p["value"]:
                continue
            n += 1
            st, hx, _a = dr.OptionTranslator.stata_colour(p["value"])
            if st == "ok" and hx is not None and hx != p["fill"]:
                bad.append(f"{pid} {p['value']}: {hx} != {p['fill']}")
        assert n > 20 and not bad, "\n".join(bad)

    def test_the_scheme_extractor_agrees(self):
        """scripts/extract_scheme_truth.py's twin reads every H_ row alike."""
        import extract_scheme_truth as ex
        bad = []
        for key, rec in sorted(ROWS.items()):
            if key[:2] not in ("H_", "N_", "M_", "I_") or "*" not in rec["value"]:
                continue
            body = rec["value"].strip('"')
            if not body[0].isdigit():
                continue
            rgb, k = _rgb_and_k(rec["value"])
            got = "#%02x%02x%02x" % tuple(ex._apply_intensity(rgb, k))
            if got != rec["fill"]:
                bad.append(f"{key}: {got} != {rec['fill']}")
        assert not bad, "\n".join(bad[:20])


def _blank_table():
    """The Mata table _dash_stylelist_blank_words: option -> twoway's line,
    its ``@`` written as twoway's empty macro quote."""
    src = _read(_MATA)
    m = re.search(r"string scalar _dash_stylelist_blank_words\("
                  r"string scalar key\)\s*\{(.*?)\n\}", src, re.S)
    assert m, "_dash_stylelist_blank_words is not in dash_parse.mata"
    tab = {}
    for key, words in re.findall(r'"(\w+)",\s*"([^"]*)"', m.group(1)):
        tab[key] = words.replace("@", "\x60'")
    return tab


class TestBlankElements:
    def test_the_table_is_twoways(self):
        """Every option twoway refuses with r(198) has twoway's first line in
        the table; every other option (twoway accepts the blank, or refuses
        it for another reason) is not in it."""
        tab = _blank_table()
        bad = []
        for key, rec in sorted(ROWS.items()):
            if not key.startswith("B_"):
                continue
            opt = key[2:]
            if rec["rc"] == 198:
                if tab.get(opt) != rec["first_line"]:
                    bad.append(f"{opt}: {tab.get(opt)!r} != "
                               f"{rec['first_line']!r}")
            elif opt in tab:
                bad.append(f"{opt}: twoway rc {rec['rc']}, yet in the table")
        assert not bad, "\n".join(bad)

    def test_ado_text(self):
        """dash.ado prints twoway's line first, then dash's hint."""
        src = _read(_ADO)
        i = src.index("_dash_stylelist_blank(st_global(")
        body = src[i:i + 1200]
        tw = body.index("_dash_stylelist_blank_words(")
        hint = body.index("is blank; use . for the default")
        assert tw < hint

