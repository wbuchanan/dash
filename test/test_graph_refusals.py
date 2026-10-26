"""Graph-wide refusals in twoway's words (WP-35 section 35-06).

twoway refuses two omit options anywhere in one command, aspectratio()
with xoverhangs or yoverhangs, a maxaxes() that is no integer or below an
axis a layer asks for, a title with notitling, and factor-variable
notation in by(), colorvar() and mlabel(); it reads fxsiz() and fysiz()
as fxsize() and fysize() (test/fixtures/graph_refusal_truth.json, written
by scripts/extract_graph_refusal_truth.do).

No pytest runs Stata: these pin the fixture's readings and the code's
shape.  The Q3506 cases of test_option_validation.cscript,
test_twoway_option_parity.cscript, test_varlist_expansion.cscript and
test_wp35_truth.cscript's S06 block compare dash's rc and first line with
the fixture's on the one-line and the named route.
"""
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from test_abbreviations import _program_body  # noqa: E402

_ROOT = os.path.join(_HERE, "..")
_ADO = os.path.join(_ROOT, "dash.ado")
_MATA = os.path.join(_ROOT, "dash_parse.mata")
_FIX = os.path.join(_HERE, "fixtures", "graph_refusal_truth.json")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _fix():
    with open(_FIX, encoding="utf-8") as fh:
        return json.load(fh)


def _needed():
    body = _program_body(_read(_ADO), "_dash_require_mata")
    return body[body.index("local _needed"):body.index("local _missing")]


def _defined_and_needed(name):
    assert re.search(r"^string scalar %s\(" % name, _read(_MATA), re.M), name
    assert re.search(r"^\*!   %s\(" % name, _read(_MATA), re.M), name
    assert re.search(r"\b%s\b" % name, _needed()), name


class TestTheFixture:
    def test_readings(self):
        f = _fix()
        for k in ("stata_version", "born_date", "dash_commit", "extracted",
                  "source"):
            assert f["_meta"][k], k
        assert f["_meta"]["source"] == "scripts/extract_graph_refusal_truth.do"
        om = f["omit.omitanymiss_omitallmiss"]
        assert (om["rc"], om["first"]) == (
            198, "option omitanymissomitallmiss not allowed")
        # The words in twoway's fixed order, distinct, whatever was typed.
        assert f["omit.reversed"]["first"] == om["first"]
        assert f["omit.two_lists"]["first"] == om["first"]
        assert f["omit.twice"]["first"] == "option omitanymiss not allowed"
        assert f["omit.alone"]["rc"] == 0
        assert f["maxaxes.1_y2"]["rc"] == 125
        assert f["notitling.title"]["rc"] == 4018
        assert f["fv.by_i_foreign"]["rc"] == 101


class TestOmit:
    def test_pair_reader_defined_and_needed(self):
        _defined_and_needed("_dash_omit_pair")


class TestMaxaxes:
    def test_reader_defined_and_needed(self):
        _defined_and_needed("_dash_maxaxes_val")


class TestFxsize:
    def test_twoways_minimum_declared(self):
        # twoway's graph.ado declares FXSIZe() and FYSIZe(): fxsiz() and
        # fysiz() are fxsize() and fysize() (graph_refusal_truth.json fx.*).
        f = _fix()
        assert f["fx.fxsiz"]["plot"] == f["fx.fxsize"]["plot"]
        assert f["fx.fysiz"]["plot"] == f["fx.fysize"]["plot"]
        assert f["fx.fxsi"]["rc"] == 198
        for prog in ("_dash_parse_graph_opts", "_dash_parse_plot_opts"):
            body = _program_body(_read(_ADO), prog)
            assert "FXSIZe(string)" in body and "FYSIZe(string)" in body, prog
            assert "FXSIZE(" not in body and "FYSIZE(" not in body, prog


def _help():
    with open(os.path.join(_ROOT, "dash.sthlp"), encoding="utf-8") as fh:
        return fh.read()


def _between(text, a, b):
    i = text.index(a)
    return text[i:text.index(b, i + len(a))]


class TestContourLeniency:
    """syn:SD-22 (ruling D54): twoway's contour with levels() ignores an
    option it does not know; dash keeps refusing it, and the help says so."""

    def test_the_fixture_shows_twoways_leniency(self):
        f = _fix()
        for t in ("contour", "contourline"):
            assert f[t + ".levels_bogus"]["rc"] == 0, t
            assert (f[t + ".bogus"]["rc"], f[t + ".bogus"]["first"]) == (
                198, "option bogus() not allowed"), t
        assert f["contour.levels_region"]["rc"] == 0

    def test_the_help_states_it(self):
        note = " ".join(_between(_help(), "{marker contour_unknown}",
                                 "{phang2}").split())
        assert "With {opt levels()}, {cmd:twoway}'s {cmd:contour}" in note
        assert "{cmd:dash} refuses it with or without {opt levels()}" in note
        diff = " ".join(_between(_help(), "{marker differences}",
                                 "{marker subcommands}").split())
        assert ("{cmd:contour} with {opt levels()} refuses an option it does "
                "not know, which {cmd:twoway} ignores there; see "
                "{help dash##contour_unknown:") in diff
