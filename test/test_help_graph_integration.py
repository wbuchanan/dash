"""dash.sthlp, Stata graph integration: a dashboard is not a Stata graph.

WP-38 section 38-01 (ruling M10: audit package 3 is resolved by the help).
A do-file written for twoway names, exports, combines and reuses its
graphs; under dash none of that works unchanged, and the help said so only
in pieces.  The topic section ``{marker graphintegration}`` states each
fact, measured at the WP-38 base; Differences item "A dashboard is not a
Stata graph" has one line per item linking to it.  One class per GAPS4
item:

* syn:SD-17 -- name() registers instead of drawing; saving() beside
  name() writes nothing (TestNameRegisters, TestTheDifferencesItem).
* GW-12 -- graph memory, graph export and the report commands do not see a
  dashboard (TestGraphMemory).

The Stata half -- each measurable sentence beside twoway in one run -- is
test_wp38_truth.cscript's block S01 (Q3801-k).
"""
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_HELP = os.path.join(_ROOT, "dash.sthlp")
_LINK = "{help dash##graphintegration:Stata graph integration}"


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
    """Lines joined, runs of blanks reduced to one."""
    return " ".join(text.split())


def _topic():
    return _flat(_between(_help(), "{marker graphintegration}",
                          "{marker accessibility}"))


def _description():
    return _flat(_between(_help(), "{marker description}",
                          "{marker install}"))


def _differences():
    return _between(_help(), "{marker differences}", "{marker subcommands}")


def _item():
    """Differences item "A dashboard is not a Stata graph", with its
    sub-points: from its number to the end of the section."""
    d = _differences()
    i = d.index("{ul:A dashboard is not a Stata graph.}")
    return d[d.rindex("{phang2}", 0, i):]


def _sub_point(heading):
    """The one line of the item's sub-point *heading*."""
    for line in _item().split("\n"):
        if line.startswith("{phang2}    {ul:%s}" % heading):
            return line
    raise AssertionError("no sub-point %r" % heading)


class TestTheDifferencesItem:

    def test_the_item_links_to_the_section(self):
        """The new item is the last numbered one and links the section;
        the link lands on its marker, which has a Jump To entry."""
        d = _differences()
        nums = [int(n) for n in re.findall(r"^\{phang2\}(\d+)\.", d, re.M)]
        head = re.search(r"^\{phang2\}(\d+)\.  \{ul:A dashboard is not a "
                         r"Stata graph\.\}", d, re.M)
        assert head, "no Differences item 'A dashboard is not a Stata graph'"
        assert int(head.group(1)) == max(nums) == len(nums)
        item = _flat(_item())
        assert ("{cmd:dash} writes a web page; nothing in Stata's graph "
                "memory sees it. See " + _LINK) in item
        h = _help()
        assert h.count("{marker graphintegration}{...}\n"
                       "{title:Stata graph integration}") == 1
        assert re.search(r'\{viewerjumpto "Stata graph integration"\s+'
                         r'"dash##graphintegration"\}', h)
        # After Exporting, before Accessibility (D-38-01.a).
        assert (h.index("{marker export}") < h.index(
            "{marker graphintegration}") < h.index("{marker accessibility}"))

    def test_every_sub_point_is_one_line_with_the_link(self):
        """D-38-01.b: each sub-point is one line ending in the link."""
        subs = [ln for ln in _item().split("\n")
                if ln.startswith("{phang2}    {ul:")]
        assert subs
        for ln in subs:
            assert ln.endswith("; see " + _LINK + "."), ln


class TestNameRegisters:
    """syn:SD-17: name() registers instead of drawing; saving() beside
    name() writes nothing (Q3801-1 measures both beside twoway)."""

    def test_the_topic_paragraph(self):
        t = _topic()
        assert "{title:Stata graph integration}" in t
        assert ("A dashboard is a web page, not a Stata graph. This section "
                "says what that means for a do-file written for "
                "{cmd:twoway}.") in t
        for claim in (
                "{ul:name() registers; it does not draw.}",
                "{cmd:twoway ..., name(g1)} draws the graph and keeps it as "
                "{cmd:g1} in graph memory.",
                "{cmd:dash} ...{cmd:, name(g1)} registers the graph for a "
                "later {cmd:dash build} and draws nothing;",
                "{cmd:saving()} beside {cmd:name()} writes nothing: it is "
                "named in the note {cmd:dash: ignoring unsupported "
                "option(s): saving()}.",
                "A do-file whose graphs all have names therefore writes no "
                "page until it runs {cmd:dash build} with {cmd:saving()}."):
            assert claim in t, claim

    def test_the_description_caveat(self):
        """Appendix B HR-2, help part: the drop-in sentence names its
        limit beside it, and the sentences around it stay."""
        d = _description()
        assert ("{cmd:dash} accepts the same syntax as {helpb twoway}. "
                "A graph with {cmd:name()} is registered for {cmd:dash build} "
                "instead of drawn, and no Stata graph is made: see "
                + _LINK + ". See {manhelp twoway G-2:graph twoway} for the "
                "full reference.") in d
        assert ("For plot types, marker/line/axis options, and "
                "{it:if}/{it:in} qualifiers,") in d

    def test_the_sub_point(self):
        line = _sub_point("name() registers.")
        assert ("A named graph is drawn by {cmd:dash build}, not when it is "
                "typed; see " + _LINK + ".") in line


def _export_truth():
    """graph_export_truth.json's cases: graph export measured in a fresh
    console batch session (scripts/extract_graph_export_truth.do)."""
    import json
    path = os.path.join(_HERE, "fixtures", "graph_export_truth.json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)["cases"]


class TestGraphMemory:
    """GW-12: graph memory, graph export and the report commands do not
    see a dashboard (Q3801-2; the r(601) cases in a fresh session are
    graph_export_truth.json's)."""

    def test_the_commands_listed(self):
        t = _topic()
        para = t[t.index("{ul:Graph memory and exports.}"):]
        for cmd in ("graph export", "graph save", "graph use",
                    "graph display", "graph combine", "graph dir",
                    "putdocx image", "putpdf image", "putexcel",
                    "dyndoc"):
            assert "{cmd:%s}" % cmd in para, cmd
        assert "markdown" in para
        assert "cannot use one." in para

    def test_export_after_dash(self):
        cases = _export_truth()
        for k in ("no_graph", "nodraw_only"):
            assert (cases[k]["rc"], cases[k]["first"]) == (
                601, "no Graph window open"), k
        assert cases["dropped"]["rc"] == 0
        t = _topic()
        assert ("After {cmd:dash}, {cmd:graph export} writes the last graph "
                "Stata drew -- an earlier one, even one since dropped with "
                "{cmd:graph drop} -- or fails with \"no Graph window open\", "
                "{cmd:r(601)}, when none was drawn in the session (a "
                "{cmd:nodraw} graph in memory is not enough).") in t
        assert ("{cmd:dash} returns the page's path in {cmd:r(filename)}; "
                "an image of a dashboard comes from its toolbar (PNG or "
                "SVG; see {help dash##export:Exporting}).") in t

    def test_the_sub_point(self):
        line = _sub_point("No graph memory.")
        assert ("{cmd:graph export}, {cmd:graph combine}, {cmd:putdocx} and "
                "the rest do not see a dashboard; see " + _LINK + ".") in line

    def test_description_and_exporting_link_here(self):
        d = _description()
        assert ("A dashboard is not a Stata graph: {cmd:graph export}, "
                "{cmd:graph save}, {cmd:putdocx} and {cmd:dyndoc} do not "
                "see it.") in d
        assert (_LINK + " says what each of them does after {cmd:dash}."
                ) in d
        ex = _flat(_between(_help(), "{marker export}", "{ul:graph export.}"))
        assert ("What Stata's graph commands do after {cmd:dash} is in "
                + _LINK + ".") in ex
