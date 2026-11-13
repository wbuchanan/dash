"""Refusal first lines in twoway's words (WP-49 section 49-01, plot:PT-7).

The help's Differences item 5 states the rule the refusals now follow:
where twoway refuses a command too, dash's first line is twoway's, naming
the option as it was typed (``option ba() not allowed`` for ``ba(3)``,
where dash used to print the table's ``bands()``); dash may add a line of
advice after it, and after a word that is no plot type the Supported list
(PD-11).  The applicability sentence says the same of ``kernel()``.

The Stata half -- what dash prints beside what twoway prints, read from
test/fixtures/refusal_line_truth.json (scripts/extract_refusal_line_truth.do)
-- is test_option_validation.cscript's Q4901-1 .. Q4901-5 and
test_wp49_truth.cscript's S01 block (Q4901-9).
"""
import json
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_HELP = os.path.join(_ROOT, "dash.sthlp")
_FIXTURE = os.path.join(_HERE, "fixtures", "refusal_line_truth.json")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _between(text, start, end):
    i = text.index(start)
    j = text.index(end, i + len(start))
    return text[i:j]


def _prose(text):
    """SMCL reduced to its words: directives unwrapped, lines joined."""
    t = re.sub(r"\{(?:cmd|it|opt|bf|ul|cmdab|err)[: ]([^{}]*)\}", r"\1", text)
    t = re.sub(r"\{helpb? [^:}]*:([^}]*)\}", r"\1", t)
    t = re.sub(r"\{helpb? ([^:}]*)\}", r"\1", t)
    return re.sub(r"\s+", " ", t)


def _item_five():
    return _prose(_between(_read(_HELP), "{phang2}5.  {ul:Unsupported twoway options.}",
                           "{phang2}6."))


class TestTheHelp:
    """The sentences of D-49-01.d, read from dash.sthlp."""

    def test_item_five(self):
        five = _item_five()
        assert ("Where twoway refuses the command too, a refusal's first line "
                "is twoway's, naming the option as you typed it (option ba() "
                "not allowed for ba()); dash may add a line of advice -- such "
                "as the twoway spelling of a synonym it used to accept, or "
                "what to do first -- and after a word that is not a plot "
                "type, the list of the plot types it draws.") in five

    def test_applicability_sentence(self):
        h = _prose(_read(_HELP))
        assert ("twoway's line option kernel() not allowed, naming the option "
                "as it was typed (ker(gaussian) on a scatter is option ker() "
                "not allowed)") in h
        assert "naming the option given" not in h


class TestTheFixture:
    """The measured lines the sentences rest on."""

    def test_the_example_is_measured(self):
        with open(_FIXTURE, encoding="utf-8") as fh:
            p = json.load(fh)["probes"]
        assert p["pt7.typed.applies_function"]["twoway_lines"][:1] == [
            "option ba() not allowed"]
        assert p["pt7.typed.applies_kernel"]["twoway_lines"][:1] == [
            "option ker() not allowed"]
        assert p["pt7.kept.ytitle2"]["twoway_lines"] == [
            "option ytitle2() not allowed"]
        assert p["pt7.kept.ytitle2"]["dash_lines"][1:] == [
            "use ytitle(..., axis(2))"]
