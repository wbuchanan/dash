"""Statistical-type refusals twoway makes (WP-35 section 35-04).

twoway refuses, drawn, five things dash accepted
(test/fixtures/stat_refusal_truth.json, written by
scripts/extract_stat_refusal_truth.do): histogram's bins() with width()
and two of its scale words (stat:PT-1).

No pytest runs Stata: these pin the fixture's readings and the code's
shape.  test_option_validation.cscript's Q3504 cases and
test_wp35_truth.cscript's S04 blocks show dash refusing what twoway
refuses, in its words.
"""
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from test_abbreviations import _program_body  # noqa: E402

_ROOT = os.path.join(_HERE, "..")
_ADO = os.path.join(_ROOT, "dash.ado")
_FIX = os.path.join(_HERE, "fixtures", "stat_refusal_truth.json")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _truth():
    with open(_FIX, encoding="utf-8") as fh:
        return json.load(fh)


def _rows(probe):
    """A probe's serset as its rows, sorted: lowess writes tied x values'
    rows in another order from one run to the next."""
    s = probe["serset"]
    return sorted(zip(*[s[k] for k in sorted(s)]),
                  key=lambda r: [(v is not None, v) for v in r])


class TestTheFixture:
    def test_readings(self):
        d = _truth()
        assert sorted(d["_meta"]) == ["born_date", "dash_commit",
                                      "extracted", "source",
                                      "stata_version"]
        assert d["_meta"]["source"] == "scripts/extract_stat_refusal_truth.do"
        assert d["hist.bins_width"]["rc"] == 198
        assert d["hist.bins_width"]["message"] == \
            "options bins() and width() may not be combined"
        # The scale words are named in twoway's order, whatever was typed.
        assert d["hist.frequency_density"]["message"] == \
            "options density frequency may not be combined"
        assert d["hist.density_fraction_frequency"]["message"] == \
            "options density fraction frequency may not be combined"
        for f in ("density", "fraction", "frequency", "percent"):
            assert d["flag.histogram." + f]["rc"] == 0
        assert d["contour.levels_500"]["rc"] == 0
        assert d["contour.levels_501"]["rc"] == 198
        assert d["contour.ccuts_499"]["rc"] == 0
        assert d["contour.ccuts_500"]["rc"] == 198
        assert d["lowess.weight"]["rc"] == 0
        assert _rows(d["lowess.weight"]) == _rows(d["lowess.none"])
        assert d["lowess.noweight_weight"]["message"] == \
            "option noweight not allowed"
        assert d["bw.bar"]["rc"] == 198
        assert d["bw.bar"]["message"] == "option bw() not allowed"
        for t in ("lowess", "lpoly", "lpolyci", "kdensity"):
            assert d["bw." + t]["rc"] == 0


class TestTheHistogramPairs:
    def test_checks_in_twoways_order(self):
        """twoway__histogram_gen.ado checks discrete with bins(), then
        bins() with width(), then the scale words (density fraction
        frequency percent, in that order); _dash_validate_opts runs them
        in that order, on histogram."""
        body = _program_body(_read(_ADO), "_dash_validate_opts")
        assert body is not None
        dbin = body.find("options discrete and bins() may not be combined")
        bw = body.find("options bins() and width() may not be combined")
        words = body.find("foreach f in density fraction frequency percent")
        scale = body.find("may not be combined\"", words)
        assert -1 < dbin < bw < words < scale, (dbin, bw, words, scale)
        seg = body[dbin:scale]
        assert '"`ptype\'" == "histogram"' in seg


class TestTheFlags:
    def test_scale_words_are_histograms(self):
        """density, fraction, frequency and percent are histogram's
        switches: twoway refuses each on every other type, r(198),
        "option <word> not allowed" (fixture flag.<type>.<word>), as the
        flag rules of _dash_option_rules refuse them (stat:PT-2)."""
        d = _truth()
        for k, r in d.items():
            if k.startswith("flag.") and not k.startswith("flag.histogram."):
                f = k.split(".")[2]
                assert (r["rc"], r["message"]) == \
                    (198, "option %s not allowed" % f), k
        body = _program_body(_read(_ADO), "_dash_option_rules")
        assert "density|fraction|frequency|percent@histogram" in body


class TestTheContourBound:
    def test_500_and_499(self):
        """twoway draws levels() up to 500 and ccuts() of up to 499 values,
        and refuses more, r(198), "contour level must be between 0 and
        500" (fixture contour.*, drawn); _dash_contour_check gives that
        line for both, and dash's own 1,000 bound is gone (stat:PT-5)."""
        d = _truth()
        line = "contour level must be between 0 and 500"
        for k in ("levels_501", "levels_1000", "ccuts_500"):
            assert (d["contour." + k]["rc"], d["contour." + k]["message"]) \
                == (198, line), k
        for k in ("levels_500", "ccuts_499"):
            assert d["contour." + k]["rc"] == 0, k
        body = _program_body(_read(_ADO), "_dash_contour_check")
        assert body.count('display as error "%s"' % line) == 2
        assert "`_zl' > 500" in body
        assert "`r(numlist)'' >= 500" in body
        assert "1000" not in body
