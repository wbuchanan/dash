"""The help sentences WP-31 section 56 corrected (GAPS3 J1, J2), each held to
the code or a fixture that says what is true.

J1 is the Unsupported section's opening: it said every supplied option "is
named in that command's note, so nothing is dropped in silence", while an
option twoway refuses on a plot type is refused and the names reaching the
catch-all were missing from the list (test_help_conformance.py pins the
list itself).  The J2 tests below each read one sentence of dash.sthlp and
the code it describes.
"""
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")


def _read(name):
    with open(os.path.join(_ROOT, name), encoding="utf-8") as fh:
        return fh.read()


def _help():
    return _read("dash.sthlp")


def _between(text, start, end):
    i = text.index(start)
    return text[i:text.index(end, i)]


def _flat(text):
    """SMCL text with its line breaks and runs of spaces folded to one."""
    return re.sub(r"\s+", " ", text)


class TestTheSilenceSentence:
    def test_it_states_the_refusal_rule(self):
        sec = _flat(_between(_help(), "{marker unsupported}",
                             "{marker dependencies}"))
        assert "dropped in silence" not in sec
        assert "option X() not allowed" in sec
        assert "supplied and not drawn is named in that command's note" in sec
