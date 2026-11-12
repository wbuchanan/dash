"""The help passages the drop-in audit's package 16 found stale (WP-48
section 48-01): each corrected sentence of dash.sthlp, and the docstrings
and coverage-audit rows that repeated them, held to what dash does.

* LT-27 (TestTypoParagraph): the Unsupported section said a typo such as
  ``titel(x)`` "appears in the note" and that xreverse, xcommon, lockaspect
  and the like "reach the note"; dash refuses each as twoway refuses it,
  r(198) (test_help_claims_8.cscript HC8-06, Q4801-1, Q4801-2).

The Stata half -- what dash does when the sentence's command is run -- is
test_help_claims_8.cscript's Q4801 block.
"""
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_HELP = os.path.join(_ROOT, "dash.sthlp")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _help():
    return _read(_HELP)


def _between(text, start, end):
    i = text.index(start)
    j = text.index(end, i + len(start))
    return text[i:j]


def _prose(text):
    """SMCL reduced to its words: directives unwrapped, lines joined."""
    t = re.sub(r"\{(?:cmd|it|opt|bf|ul|cmdab)[: ]([^{}]*)\}", r"\1", text)
    t = re.sub(r"\{helpb? [^:}]*:([^}]*)\}", r"\1", t)
    t = re.sub(r"\{helpb? ([^:}]*)\}", r"\1", t)
    return re.sub(r"\s+", " ", t)


def _paragraphs(text):
    """The {pstd}/{phang2} paragraphs of *text*, each reduced to prose."""
    return [_prose(p) for p in re.split(r"\{(?:pstd|phang2?)\}", text)]


def _unsupported():
    return _between(_help(), "{marker unsupported}", "{marker dependencies}")


class TestTypoParagraph:
    """LT-27: the two paragraphs at the end of the Unsupported section."""

    def test_titel_is_refused(self):
        sec = _prose(_unsupported())
        assert ("titl(x) abbreviates title() and works, titel(x) is "
                "option titel() not allowed, r(198)") in sec
        assert "appears in the note" not in sec
        assert "reported as ignored rather than" not in sec
        # The sub-option notes print the token as typed, value and all
        # (Q4801-1: legend(note("N")) is named note("N")).
        assert "never the values supplied" not in sec

    def test_names_are_refused(self):
        paras = [p for p in _paragraphs(_unsupported()) if "xreverse" in p]
        assert len(paras) == 1, paras
        p = paras[0]
        assert "reach the note" not in p
        assert ("refuses them as twoway refuses them, option xreverse not "
                "allowed, r(198)") in p
        for word in ("xscale(reverse)", "xscale(alt)", "graph combine",
                     "plotregion()", "legend()", "clegend()", "addplot()",
                     "lockaspect, zoom() and ddensity are options of no "
                     "Stata graph command"):
            assert word in p, word
