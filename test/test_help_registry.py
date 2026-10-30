"""Where dash's registry answers a command differently from twoway's graph
memory, as the help states it (WP-38 section 38-02, ruling M10:
documented, no code change).

dash.sthlp's topic section "The registry: return codes and messages"
({marker registry}) sets out each difference beside twoway's measured
answer, and Differences from twoway item 2 gains one sub-point per item
linking to it.  Each class reads one item's paragraph and its sub-point.
The rcs and words quoted are what twoway and dash print at a3ffa90
(StataNow 19.5, 30oct2026); the measurable claims are probed beside
twoway in test_registry_collision.cscript (Q3802-1, Q3802-4, Q3802-5),
test_path_validation.cscript (Q3802-2) and test_nodraw_honoured.cscript
(Q3802-3), and play()'s refusal in test_option_validation.cscript U54.
"""

import os

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


def _flat(text):
    return " ".join(text.split())


def _topic():
    """The registry topic section, flattened."""
    return _flat(_between(_help(), "{marker registry}",
                          "{marker dashboard_options}"))


def _paragraph(heading):
    """One paragraph of the topic section, from its heading to the next."""
    text = _topic()
    i = text.index("{ul:%s}" % heading)
    j = text.find("{pstd}", i)
    return text[i:] if j < 0 else text[i:j]


def _item2():
    """Differences from twoway item 2 with its sub-points, flattened."""
    return _flat(_between(_help(), "{phang2}2.  ", "{phang2}3.  "))


def _sub_point(heading):
    """One sub-point of item 2, from its heading to the next sub-point."""
    text = _item2()
    i = text.index("{ul:%s}" % heading)
    j = text.find("{phang2}", i)
    return text[i:] if j < 0 else text[i:j]


_LINK = "{help dash##registry:The registry}"


class TestNames:
    """GW-13: name()'s limits and the rc of a name already held."""

    def test_limits_and_rc(self):
        p = _paragraph("Names.")
        # twoway: 32 characters rc 0, 33 refused; a__b rc 0; r(110).
        assert "up to 32 characters" in p
        assert "double underscores included" in p
        assert '"graph {it:name} already exists", {cmd:r(110)}' in p
        # dash: 22 and 18 characters, no __, its own words, r(198).
        assert "at most 22 characters for a graph and 18 for a KPI card" in p
        assert "no {cmd:__}" in p
        assert ("\"dash: graph name '{it:name}' already exists. Use "
                "name({it:name}, replace) to overwrite.\", {cmd:r(198)}") in p
        assert "{help dash##differences:" in p

    def test_the_sub_point(self):
        s = _sub_point("Names.")
        assert "at most 22 characters (18 for a KPI card)" in s
        assert "{cmd:r(198)} where {cmd:twoway} gives {cmd:r(110)}" in s
        assert _LINK in s
