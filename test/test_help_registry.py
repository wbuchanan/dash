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


class TestSavingExisting:
    """GW-14: saving() onto a file that exists, and twoway's not-found note."""

    def test_rc_and_the_missing_note(self):
        p = _paragraph("saving() onto a file that exists.")
        assert '"file {it:x}.gph already exists", {cmd:r(602)}' in p
        assert ("\"dash: file '{it:x}.html' already exists. Use replace option to "
                "overwrite.\", {cmd:r(198)}") in p
        assert "{ul:saving() keeps a file that is already there.}" in p
        assert '"(file {it:x}.gph not found)"' in p
        assert "is not printed by {cmd:dash}" in p

    def test_the_sub_point(self):
        s = _sub_point("saving() onto a file that exists.")
        assert "{cmd:r(198)} where {cmd:twoway} gives {cmd:r(602)}" in s
        assert 'no "(file not found)" note' in s
        assert _LINK in s


class TestNodrawAsis:
    """GW-15: nodraw with saving(, asis) writes the page; twoway: r(601)."""

    def test_both_answers(self):
        p = _paragraph("nodraw with saving(, asis).")
        assert '"no current graph", {cmd:r(601)}' in p
        assert "{cmd:dash} writes the page and opens no browser" in p
        assert "{ul:nodraw still writes the page.}" in p

    def test_the_sub_point(self):
        s = _sub_point("nodraw with saving(, asis).")
        assert "The page is written where {cmd:twoway} refuses {cmd:r(601)}" in s
        assert _LINK in s


class TestPlay:
    """GW-16: play() refuses a readable recording; there is no Graph Editor."""

    def test_both_refusals_and_no_editor(self):
        p = _paragraph("play().")
        assert "as {cmd:twoway} refuses it, {cmd:r(601)}" in p
        assert "a readable recording is refused, {cmd:r(198)}" in p
        assert "no Graph Editor can open a dashboard" in p
        assert "{help dash##unsupported:" in p

    def test_the_sub_point(self):
        s = _sub_point("play().")
        assert "A readable recording is refused {cmd:r(198)}" in s
        assert "there is no Graph Editor" in s
        assert _LINK in s


class TestNameSubOptions:
    """GW-9: a name() sub-option other than replace is refused as a name."""

    def test_both_answers(self):
        p = _paragraph("name()'s sub-options.")
        assert "one sub-option, {cmd:replace}, in full and lower case" in p
        assert '"option {it:word} not allowed", {cmd:r(198)}' in p
        assert "refuses it as an invalid name" in p
        assert "the comma and blank shown as {cmd:?}" in p
        assert "(\"dash: invalid graph name 'g??rep'. ...\"), {cmd:r(198)}" in p
        assert "Write {cmd:name(}{it:name}{cmd:, replace)}" in p

    def test_the_sub_point(self):
        s = _sub_point("name()'s sub-options.")
        assert "A word other than {cmd:replace} is refused as an invalid name" in s
        assert 'not as "option {it:word} not allowed"' in s
        assert _LINK in s


class TestDashClear:
    """ECO-5: dash clear takes no names and empties the whole registry."""

    def test_no_names_whole_registry(self):
        p = _paragraph("dash clear.")
        assert "{cmd:dash clear} takes no names" in p
        assert "anything after it is ignored" in p
        assert "the whole registry is emptied" in p
        assert "clears every graph and card, rc 0" in p
        for cmd in ("graph dir", "graph describe", "graph drop"):
            assert "{cmd:%s}" % cmd in p
        assert "those commands do not see registered items" in p
        assert "{cmd:name(}{it:name}{cmd:, replace)}" in p
        assert "{cmd:$dash_graph_registry}" in p

    def test_dlgtab_links_here(self):
        d = _flat(_between(_help(), "{dlgtab:dash clear}",
                           "{marker registry}"))
        assert "takes no names" in d
        assert _LINK in d

    def test_the_sub_point(self):
        s = _sub_point("dash clear.")
        assert "It takes no names and empties the whole registry" in s
        assert "nothing lists, describes or drops one item" in s
        assert _LINK in s
