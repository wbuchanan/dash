"""The drop-in audit's false-sentence checklist (WP-48 48-04, PD-8).

The audit of 19oct2026 found 22 sentences of dash.sthlp, README.md,
dash.pkg and their neighbours false (index Appendix B, HR-1..HR-22).  Each
has one test class here: HR-1..HR-22, 22 HRs in 21 classes (HR-5 and
HR-22, one sentence, share TestHR05and22).  HR-17 -- the Differences item
5 refusal sentences -- is 49-01's TestHR17, added in its plot:PT-7 commit
(D-48-04.c).

Six sentences are this section's own (HR-1, HR-3, HR-4, HR-6, HR-7 and the
HR-21 check): their classes assert the corrected sentence and that the
false one is gone.  Every other HR was corrected by the section whose item
made it true; its class asserts that owner's pin exists -- the owner's
closed BUGS.md entry names a pytest node or cert case that exists -- and,
only where that owner left no help-claim test reading the sentence, that
the audit's false phrase is absent (D-48-04.b).  Every phrase is matched on
``_prose()``, so a line break inside it does not matter.
"""
import os
import re
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)

import test_tracking_documents as T  # noqa: E402

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


def _root(name):
    return _read(os.path.join(_ROOT, name))


def _differences():
    return _between(_help(), "{marker differences}", "{marker subcommands}")


def _pkg_text():
    """dash.pkg's description as `net describe' shows it."""
    return re.sub(r"\s+", " ", " ".join(
        ln[2:] for ln in _root("dash.pkg").splitlines()
        if ln.startswith("d ")))


_STATE = {}


def _entries():
    if "bugs" not in _STATE:
        _STATE["bugs"] = T._parse_bugs(_root("BUGS.md"))[0]
    return _STATE["bugs"]


def _on_disk():
    """What exists under test/, in the shape T._references reads."""
    if "disk" not in _STATE:
        files = T._test_files()
        py = {f: T._python_names(os.path.join(_HERE, f))
              for f in files if f.endswith(".py")}
        cases = set()
        for f in files:
            if f.endswith((".cscript", ".do")):
                with open(os.path.join(_HERE, f), encoding="utf-8",
                          errors="replace") as fh:
                    cases |= T._displayed_cases(fh.read())
        classes = set()
        for cls, _funcs in py.values():
            classes |= set(cls)
        _STATE["disk"] = {"files": files, "py": py, "cases": cases,
                          "classes": classes}
    return _STATE["disk"]


def _resolution(e):
    return e["fields"].get("Resolution", "")


def _owner_entry(item_id):
    """The closed BUGS.md entry that closed GAPS4 *item_id*: its Resolution
    ends ``Closes GAPS4 <id> (`` or opens ``<Kind> <date> (WP-NN, <id>)``
    (the WP-47 entries carry only the second form)."""
    opens = re.compile(r"^\s*- Resolution: \w+ \w+ \(WP-\d+, %s\)"
                       % re.escape(item_id))
    found = [e for e in _entries()
             if "Closes GAPS4 %s (" % item_id in _resolution(e)
             or opens.match(_resolution(e))]
    assert found, "no BUGS.md entry closes %s" % item_id
    assert len(found) == 1, (item_id, [e["title"][:60] for e in found])
    e = found[0]
    assert e["closed"], "%s's entry %r is still open" % (item_id, e["title"])
    return e


def _owner_pin(item_id):
    """The nodes the owner's closed entry pins with: every test it names
    exists (a pytest node's file, class and method, read with ast; a cert
    case id displayed by its script), and it names at least one."""
    e = _owner_entry(item_id)
    found, dangling = T._references(_resolution(e), _on_disk())
    assert not dangling, (item_id, dangling)
    nodes = [n for n in found if "::" in n or not n.endswith(
        (".py", ".cscript", ".do"))]
    assert nodes, "%s's entry %r names no test node or cert case" % (
        item_id, e["title"][:80])
    return nodes


def _node_exists(node):
    """file.py::Class::method (or ::Class) exists in test/."""
    parts = node.split("::")
    classes, funcs = _on_disk()["py"].get(parts[0], ({}, set()))
    if len(parts) == 2:
        return parts[1] in classes or parts[1] in funcs
    return parts[1] in classes and parts[2] in classes[parts[1]]


def _help_prose():
    return _prose(_help())


class TestTheReaders:
    """The checklist's own readers."""

    def test_owner_pin_reads_both_closing_forms(self):
        # WP-36's entry ends "Closes GAPS4 plat:PT-5 (...)"; WP-47's opens
        # "Fixed 10nov2026 (WP-47, MS-2)" and has no Closes clause.
        assert _owner_pin("plat:PT-5")
        assert _owner_pin("MS-2")
        with pytest.raises(AssertionError):
            _owner_entry("no:SUCH-1")

    def test_node_exists(self):
        assert _node_exists("test_false_sentences.py::TestTheReaders")
        assert _node_exists(
            "test_false_sentences.py::TestTheReaders::test_node_exists")
        assert not _node_exists("test_false_sentences.py::TestNoSuchClass")


# ===========================================================================
# This section's own sentences (group 1)
# ===========================================================================

class TestHR01:
    """HR-1: "dash accepts the same syntax as twoway" (Description, twice)
    -- the audit: say the twoway grammar, with the exceptions listed under
    Differences."""

    def test_grammar_not_same_syntax(self):
        d = _prose(_between(_help(), "{marker description}",
                            "{marker install}"))
        assert ("dash reads twoway's syntax and produces an interactive HTML "
                "file instead of a Stata graph window; where it reads or "
                "draws something differently, Differences from twoway says "
                "so.") in d
        assert ("Plot types, plot and graph options and if/in qualifiers "
                "are written as for twoway (see Differences from twoway for "
                "the exceptions).") in d
        assert "accepts the same syntax as" not in _help_prose()


_HR03 = ("Options are written as for twoway: what twoway refuses is "
         "refused, the options dash draws are drawn, and the few it does not "
         "draw are named in a note -- see {h}, Differences from twoway and "
         "Unsupported Stata twoway options; dash adds two options of its "
         "own, hover() and table (see {h}, dash's own options).")


class TestHR03:
    """HR-3: README and dash.pkg, "Most twoway options are honoured; the
    rest are accepted and named in a note"."""

    def test_readme_and_pkg(self):
        readme = re.sub(r"\s+", " ", _root("README.md"))
        pkg = _pkg_text()
        assert _HR03.format(h="`help dash`") in readme
        assert _HR03.format(h="-help dash-") in pkg
        for text in (readme, pkg):
            assert "the rest are accepted and named in a note" not in text
            assert "Most twoway options are honoured" not in text
            assert "dash adds two options of its own, hover() and table" \
                in text


class TestHR04:
    """HR-4: README's documentation list, "every difference from
    twoway"."""

    def test_no_every_difference(self):
        readme = re.sub(r"\s+", " ", _root("README.md"))
        assert ("`help dash` -- the syntax, the differences from `twoway`, "
                "and the dashboard options.") in readme
        assert "every difference from" not in readme


class TestHR06:
    """HR-6: the Unsupported intro, "a command copy-pasted from a do-file
    always runs"."""

    def test_no_always_runs(self):
        raw = _between(_help(), "{marker unsupported}",
                       "{p 12 12 2}{cmd:. sysuse auto, clear}")
        intro = _prose(raw)
        assert ("None of them given once is an error, so a command that uses "
                "them runs, and each that is supplied and not drawn is named "
                "in that command's note; an option twoway refuses is refused "
                "as twoway refuses it") in intro
        assert "except dash's own hover() and table" in intro
        assert "a value twoway refuses is refused with twoway's return code" \
            in intro
        assert "{help dash##dashonly:" in raw
        assert "{marker dashonly}" in _help()
        assert "{help dash##limits:Resource limits}" in raw
        assert "a command copy-pasted from a do-file always runs" not in \
            _help_prose()


def _ul_headings(text):
    """The text of every {ul:...} heading, one level of nested directives
    allowed, reduced to its words without the closing stop."""
    out = []
    for m in re.finditer(r"\{ul:((?:[^{}]|\{[^{}]*\})*)\}", text):
        out.append(_prose(m.group(1)).strip().rstrip(".:").strip())
    return out


def _titles(text):
    return [_prose(m.group(1)).strip()
            for m in re.finditer(r"\{title:([^}]*)\}", text)]


def _norm(s):
    return re.sub(r"\s+", " ", s).strip().lower()


_DOCUMENTED = re.compile(
    r"^\s*- Resolution: Documented .*Closes GAPS4 (\S+) \(WP-(\d+), [^)]*\)"
    r"\.\s*$", re.S)


def _named_section(resolution, names):
    """True when a Resolution with no dash## link names a help section: the
    text after ``dash.sthlp `` up to the next ``.`` or `` and `` equals a
    {ul:} heading or a {title:} of dash.sthlp."""
    for m in re.finditer(r"dash\.sthlp ", resolution):
        rest = resolution[m.end():]
        cut = re.split(r"\.| and ", rest, maxsplit=1)[0]
        if _norm(cut) in names:
            return True
    return False


def _residual_titles():
    """{GAPS4 id: residual title} for every Partly Tracked line of a closed
    WP (GAPS4_CLOSED_WPS) or of WP-48."""
    out = {}
    wps = set(T.GAPS4_CLOSED_WPS) | {"WP-48"}
    for m in re.finditer(
            r"^- \*\*(\S+) Tracked:\*\* Partly closed in (WP-\d+) .*"
            r"\(BUGS\.md \"([^\"]+)\"\)\.\s*$", _root("GAPS4.md"), re.M):
        if m.group(2) in wps and m.group(1) not in T.GAPS4_OPEN:
            out[m.group(1)] = m.group(3)
    return out


class TestHR07:
    """HR-7: "where dash differs, this file says so under the option
    concerned" -- true only with every documented difference in the
    help."""

    def test_sentence(self):
        p = _prose(_between(_help(), "{marker plottypes}",
                            "{synoptset 22}"))
        assert ("where dash differs from twoway by design, this file says "
                "so, under the option concerned or under Differences from "
                "twoway.") in p
        assert "this file says so under the option concerned" not in p

    def test_every_documented_difference_is_in_the_help(self):
        help_ = _help()
        markers = set(re.findall(r"\{marker ([\w-]+)\}", help_))
        setup_markers = set(re.findall(r"\{marker ([\w-]+)\}",
                                       _root("dash_setup.sthlp")))
        names = {_norm(h) for h in _ul_headings(help_)} | {
            _norm(t) for t in _titles(help_)}
        bad, read = [], 0
        for e in _entries():
            res = _resolution(e)
            m = _DOCUMENTED.match(res)
            if not m or int(m.group(2)) < 33:
                continue
            read += 1
            links = re.findall(r"(?<![\w])dash##([\w-]+)", res)
            setup = re.findall(r"dash_setup##([\w-]+)", res)
            if links or setup:
                gone = [x for x in links if x not in markers] + [
                    "_setup " + x for x in setup if x not in setup_markers]
                if gone:
                    bad.append("%s: dash##%s names no marker"
                               % (e["title"][:70], ", dash##".join(gone)))
            elif not _named_section(res, names):
                bad.append("%s: names no dash.sthlp section by its heading"
                           % e["title"][:70])
        assert read >= 30, read
        # (b) A Partly row's residual is a difference not yet fixed, not
        # one by design: it is tracked as an open entry, never dropped.
        by_title = {e["title"]: e for e in _entries()}
        residuals = _residual_titles()
        assert residuals, "no Partly Tracked line was read"
        for gid, title in sorted(residuals.items()):
            e = by_title.get(title)
            if e is None:
                bad.append("%s: residual %r has no BUGS.md entry"
                           % (gid, title[:60]))
            elif e["closed"] and gid != "plot:PT-13":
                bad.append("%s: residual %r is closed; its row is not Partly"
                           % (gid, title[:60]))
        assert not bad, "\n".join(bad)


class TestHR21:
    """HR-21: the Differences section lists the resource limits and the
    recast-with-horizontal quirk; no heading names jitter or the Python
    requirement (Q50, Q49)."""

    def test_differences_link_the_limits_and_recast_notes(self):
        d = _differences()
        assert "{help dash##limits:Resource limits}" in d
        assert "{marker limits}" in _help()
        assert "{help dash##recast:Recast}" in d
        assert "{marker recast}" in _help()
        heads = _ul_headings(d)
        assert len(heads) > 17, heads
        assert any("recast() with horizontal" in h for h in heads), heads
        assert any(h == "Resource limits" for h in heads), heads
        for h in heads:
            assert "jitter" not in h.lower(), h
            assert "python" not in h.lower(), h


# ===========================================================================
# Sentences an earlier section owns (owner pins, D-48-04.b)
# ===========================================================================

class TestHR02:
    """HR-2: the drop-in caveats -- name() registers and there is no graph
    memory or export (38-01, help), and the tested platform (36-04, help and
    README)."""

    def test_name_registers(self):
        nodes = _owner_pin("syn:SD-17")
        assert any(n.startswith("test_help_graph_integration.py::"
                                "TestNameRegisters") for n in nodes), nodes

    def test_no_graph_memory(self):
        nodes = _owner_pin("GW-12")
        assert any(n.startswith("test_help_graph_integration.py::"
                                "TestGraphMemory") for n in nodes), nodes

    def test_tested_platform(self):
        nodes = _owner_pin("plat:PT-5")
        assert any(n.startswith("test_help_environment.py::TestThePlatform")
                   for n in nodes), nodes


class TestHR05and22:
    """HR-5 and HR-22: the plot-type list named two words twoway does not
    take as plot types.  35-09's PD-10 commit (WP-35 A2, no GAPS4 row)
    removed them and left a help pin, so only its nodes are asserted."""

    def test_owner_pin(self):
        for node in ("test_command_grammar.py::TestGeneric::"
                     "test_no_by_name_refusal",
                     "test_help_claims_9.py::TestTheUndrawnTypes::"
                     "test_not_drawn_names_every_refused_type"):
            assert _node_exists(node), node


class TestHR08:
    """HR-8: the empty graph drawn "with axes" (35-09, plot:PT-4)."""

    def test_owner_pin(self):
        assert _owner_pin("plot:PT-4")
        # The pin is a code test, not a help claim: the phrase too.
        assert "with axes and no plot" not in _help_prose()


class TestHR09:
    """HR-9: "works offline in any modern browser" (36-04, plat:PT-16, whose
    help pin TestTheBrowser reads the Description)."""

    def test_owner_pin(self):
        nodes = _owner_pin("plat:PT-16")
        assert any("TestTheBrowser" in n for n in nodes), nodes


class TestHR10:
    """HR-10: range() widening the ticks (34-03, AX-1) and Stata's own
    ticks at build (34-09, AX-3 and the natscale entry, PD-9)."""

    def test_owner_pin(self):
        assert _owner_pin("AX-1")
        assert _owner_pin("AX-3")
        assert _owner_pin("plot:PT-13")
        # AX-1's and AX-3's pins are code tests: the phrases too.
        assert "a range() that widens the ticks" not in _help_prose()
        assert "exact at build through S45's embedded ticks" not in \
            _root("ROADMAP.md")
        by_title = {e["title"]: e for e in _entries()}
        nat = [t for t in by_title
               if t.startswith("The natscale model misses three")]
        assert len(nat) == 1, nat
        text = re.sub(r"\s+", " ", by_title[nat[0]]["text"])
        assert "every axis a page built in Stata draws is Stata's own" \
            not in text


class TestHR11:
    """HR-11: by() "one fewer on y" (34-02, AX-2)."""

    def test_owner_pin(self):
        assert _owner_pin("AX-2")
        assert "one fewer on y" not in _help_prose()


class TestHR12:
    """HR-12: aspectratio() and xsize() "exactly as twoway does" (34-04 VF-3,
    45-04 VF-4)."""

    def test_owner_pin(self):
        assert _owner_pin("VF-3")
        assert _owner_pin("VF-4")
        # "xsize(9) gives a graph 9 inches wide and 4.5 tall, exactly as
        # twoway does" is measured true (test_geometry.py, geometry_truth):
        # no phrase is asserted absent.


class TestHR13:
    """HR-13: yvarlabel()/xvarlabel() reach every title and key (47-02,
    MS-2)."""

    def test_owner_pin(self):
        nodes = _owner_pin("MS-2")
        assert any("TestEveryTypeTakesThem" in n for n in nodes), nodes


class TestHR14:
    """HR-14: headlabel/mangle, lalign, dlalign and "every plot type"
    passages (47-01, 47-03, 48-01)."""

    def test_owner_pin(self):
        for item in ("basic:PT-1", "MS-7", "basic:PT-4", "basic:PT-5",
                     "basic:PT-6", "basic:PT-16"):
            assert _owner_pin(item)
        for m in ("test_mangle_barbsize_headlabel", "test_headlabel_pc",
                  "test_lalign", "test_dlalign", "test_every_plot_type"):
            assert _node_exists("test_help_claims_p16.py::TestStalePassages::"
                                + m), m


class TestHR15:
    """HR-15: the area outline (34-05, PIC-1), V/v drawn as an open chevron
    (47-06, PIC-2, measured: an open three-vertex path) and the economist
    note (45-01, PIC-4)."""

    def test_owner_pin(self):
        for item in ("PIC-1", "PIC-2", "PIC-4"):
            assert _owner_pin(item)


class TestHR16:
    """HR-16: horizontal (48-02, RH-15), levels() (35-04, stat:PT-5),
    placement() (43-05, LT-16), custom, tick grid (44-02, AX-5, AX-6) and
    fill (44-03, AX-7)."""

    def test_owner_pin(self):
        for item in ("RH-15", "stat:PT-5", "LT-16", "AX-5", "AX-6", "AX-7"):
            assert _owner_pin(item)
        h = _help_prose()
        # stat:PT-5's, AX-6's and AX-7's pins are code tests: their phrases.
        assert "twoway takes any integer" not in h
        assert "minor_grid style" not in h
        assert "fill draw the plain axis" not in h


class TestHR17:
    """HR-17: Differences item 5 and the applicability sentence said dash
    names "the word twoway names" and "the option given", while dash printed
    the table's name for a word typed short (bands() for ba()); 49-01
    (plot:PT-7) made the first line twoway's, the option as typed, and the
    sentences say so (test_refusal_lines_p17.py reads them)."""

    def test_refusal_sentences(self):
        assert _owner_pin("plot:PT-7")
        h = _help_prose()
        assert "naming the option given" not in h
        assert ("a refusal's first line is twoway's, naming the option as "
                "you typed it") in h
        assert _node_exists(
            "test_refusal_lines_p17.py::TestTheHelp::test_item_five")


class TestHR18:
    """HR-18: the export cap counts what the page embeds (40-01,
    plat:PT-7)."""

    def test_owner_pin(self):
        assert _owner_pin("plat:PT-7")


class TestHR19:
    """HR-19: colordiscrete (42-05, CV-2), msize() "any number" and one bar
    per value (40-02, sil:SD-11, sil:SD-1), zero weights (47-06, DG-12) and
    "gaps not scaled" (33-11, GW-11)."""

    def test_owner_pin(self):
        for item in ("CV-2", "sil:SD-11", "sil:SD-1", "DG-12", "GW-11"):
            assert _owner_pin(item)
        h = _help_prose()
        # CV-2's pin measures the colordiscrete rule against twoway, so its
        # "drawn as Stata draws them" stands; GW-11's is a geometry test.
        assert "gaps between boxes are not scaled" not in h


class TestHR20:
    """HR-20: "Python is required but is not available to Stata" (36-01,
    plat:PT-1, pinned by code tests)."""

    def test_owner_pin(self):
        assert _owner_pin("plat:PT-1")
        for f in ("dash_setup.sthlp", "dash.ado", "dash_setup.ado"):
            assert "Python is required but is not available to Stata" not in \
                re.sub(r"\s+", " ", _root(f)), f
