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
* ECO-1 -- a registered graph keeps its command and frame, not its data
  (TestDataAtBuild).
* ECO-4 -- graph combine maps to dash build's layout() and tabs(); its
  options are refused (TestGraphCombine).
* ECO-15 -- each one-line command writes and opens its own page; five
  previews are kept (TestOnePagePerCommand).

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


#: 33-07's sentence after the qualifier paragraph (dash.sthlp, Description),
#: given verbatim in the ECO-1 paragraph (TR-38-01.4).
_FRAMES = ("A graph registered in another frame ({cmd:frame} {it:name}{cmd::} "
           "{cmd:dash} ...{cmd:, name()}) reads that frame instead; see "
           "{help dash##frames:Graphs from several frames}.")


class TestDataAtBuild:
    """ECO-1: a registered graph keeps its command and frame, not its data
    (Q3801-3: collapse undone by restore, and a tempvar gone at build)."""

    def test_the_paragraph(self):
        t = _topic()
        para = t[t.index("{ul:A registered graph keeps no data.}"):]
        for claim in (
                "{cmd:name()} stores the command and the frame it was "
                "registered in, not its data: {cmd:dash build} draws every "
                "registered graph from that frame's data as they are when "
                "the build runs,",
                "So {cmd:preserve}, {cmd:collapse}, {cmd:dash} ...{cmd:, "
                "name(g1)}, {cmd:restore}, {cmd:dash build} draws the "
                "restored data, with no note -- where {cmd:twoway}'s "
                "{cmd:g1} keeps the collapsed graph --",
                "a graph of a temporary variable fails at build once the "
                "variable is gone",
                "\"variable {it:name} not found\", {cmd:r(111)}.",
                "What counts is the data when {cmd:dash build} runs, not "
                "when the graph is registered:"):
            assert claim in para, claim

    def test_frame_is_named(self):
        """D-38-01.c, A-17: the frame prefix in 33-07's words, the KPI
        rule, and no frame() option."""
        assert _FRAMES in _description()
        t = _topic()
        para = t[t.index("{ul:A registered graph keeps no data.}"):]
        assert _FRAMES in para
        assert "{help dash##frames:" in para
        assert "{cmd:frame} {it:name}{cmd::}" in para
        assert "KPI cards read the frame current at {cmd:dash build}" in para
        assert "{cmd:frame(" not in t
        assert "every other graph from the frame current at build" not in t

    def test_the_sub_point(self):
        line = _sub_point("Data at build.")
        assert ("A named graph draws its frame's data as they are at "
                "{cmd:dash build}; see " + _LINK + ".") in line


#: graph combine's options dash build refuses, "option X not allowed",
#: r(198), each measured at the WP-38 base (Q3801-4).
_COMBINE_REFUSED = ("cols()", "rows()", "holes()", "colfirst", "xcommon",
                    "ycommon", "iscale()", "imargin()", "note()",
                    "caption()", "xsize()", "ysize()")


class TestGraphCombine:
    """ECO-4: dash build plays graph combine's part (Q3801-4)."""

    def _para(self):
        t = _topic()
        i = t.index("{ul:graph combine.}")
        return t[i:t.index("{ul:", i + 5)] if "{ul:" in t[i + 5:] else t[i:]

    def test_every_option_listed(self):
        para = self._para()
        for opt in _COMBINE_REFUSED:
            assert "{cmd:%s}" % opt in para, opt
        assert ("are not {cmd:dash build}'s options and are refused, "
                "\"option {it:name} not allowed\", {cmd:r(198)};") in para
        assert ("{cmd:graph combine g1} after {cmd:dash} is refused, \"g1 "
                "is not a memory graph\", {cmd:r(198)}.") in para

    def test_layout_is_the_counterpart(self):
        para = self._para()
        assert ("{cmd:dash build} plays {cmd:graph combine}'s part: it "
                "places the registered graphs and KPI cards in "
                "{cmd:layout()}'s grid or in {cmd:tabs()} (see "
                "{help dash##layout:Layout}), with {cmd:title()} and "
                "{cmd:subtitle()} over them.") in para
        assert "{cmd:layout(}{it:rows} {it:cols}{cmd:)}" in para
        assert "{cmd:layout(}{it:name}{cmd::}{it:row}{cmd:,}{it:col}" in para

    def test_the_sub_point(self):
        line = _sub_point("graph combine.")
        assert ("{cmd:dash build} with {cmd:layout()} combines registered "
                "graphs; see " + _LINK + ".") in line


class TestOnePagePerCommand:
    """ECO-15: each one-line command writes and opens its own page
    (test_graph_integration_code.py::TestPreviews pins the five)."""

    def test_the_paragraph(self):
        t = _topic()
        para = t[t.index("{ul:One page per command.}"):]
        for claim in (
                "Each one-line command without {cmd:saving()} writes a "
                "preview page of its own, under a new name, and, in "
                "interactive Stata, opens it, so a do-file of ten graphs "
                "opens ten pages;",
                "the newest five previews of a session are kept and older "
                "ones are removed, except one a browser was asked to open "
                "in the last minute (see "
                "{help dash##tempfiles:Temporary files and privacy}).",
                "{cmd:saving()} writes the page where it says and opens "
                "nothing; {cmd:$dash_nobrowser} keeps every window shut "
                "(see {help dash##nobrowser_global:The global "
                "dash_nobrowser});",
                "{cmd:twoway} instead draws every graph into its one Graph "
                "window."):
            assert claim in para, claim

    def test_the_sub_point(self):
        line = _sub_point("One page per command.")
        assert ("Each one-line command opens its own page; see "
                + _LINK + ".") in line
