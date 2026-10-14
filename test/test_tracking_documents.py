"""test_tracking_documents.py -- ROADMAP.md WP-23: TR-23.5, BR-23.3, AC-23.3.

    "No tracking document in the repository claims work that is not done."

The tracking documents are BUGS.md (every defect, open or closed), GAPS.md
(every gap the audit of 187a786 found, and its state now) and ROADMAP.md
(the work packages, and the gaps each one closes).  TODO.md and PLAN.md
described a roadmap the others overtook (GAPS.md M1) and are retired.  This
file holds, mechanically:

1. Every BUGS.md entry is "- [x]" or "- [ ]" and carries the five fields --
   Title, File Names and Line Numbers, Description, Suggested fix,
   Resolution -- once each, in that order.
2. Every closed entry names a test that exists: a file under test/, a
   pytest node (``test_x.py::Class[::test]``) that resolves, or a
   certification case id that a script under test/ displays.  Every test
   class, node or file an entry names must exist, unless the entry records
   that it "no longer exists".  The few entries whose fix no test covers
   are listed by title in CLOSED_WITHOUT_A_TEST and must say so.
3. Every open entry says that it is open, and why.
4. Every GAPS.md gap heading carries a status.  A gap the body records as
   resolved is marked closed in its heading.  A closed gap names what
   closed it: a work package that ROADMAP.md heads DONE and that lists the
   gap, or a commit that exists.
5. ROADMAP.md's DONE work packages and GAPS.md agree the other way too:
   every gap a DONE package lists under "Gaps closed" is closed in GAPS.md
   by that package -- partly, where the listing is qualified, as in
   "E1 (nodraw)" -- save the gaps WP23_OPEN_UNTIL_INTEGRATION and
   ROADMAP_CORRECTIONS_PENDING name.  Both constants check that each of
   their entries is still needed, so neither can outlive its reason.
6. TODO.md and PLAN.md are gone, and nothing in the repository links them.
7. GAPS2.md (the audit of 91d97be) and ROADMAP.md agree: a package's
   **GAPS2 closed:** ids have headings; a DONE package's ids carry a
   Tracked line 'Closed in WP-nn, BUGS.md "title", commit sha' naming it,
   a closed BUGS.md entry and a commit that exists, and every such Tracked
   line is listed by its package.
8. WP-29's P0 entries (.ultraplan/wp29/index.md A4) are open in BUGS.md
   in the form "Not fixed because WP-29 section NN has not landed. Graded
   S1|S2 (WP-29): ..." and listed in WP29_OPEN, which alone exempts them
   from the release guard, with a "<!-- WP-29 <id> -->" marker in each
   CHANGELOG list WP29_LISTS names, until their section lands; then the
   key is gone, no marker is left, each of those lists holds a line ending
   "(WP-29, <id>)", and a closed entry's Resolution holds "(WP-29, <id>)".
   WP-29's closeout left WP29_OPEN empty; test_no_wp29_entry_remains_open
   keeps every P0 entry closed with no marker left.
9. WP-30's P1 entries (.ultraplan/wp30/index.md A144) are open in BUGS.md
   in the form "Not fixed because WP-30 section NN has not landed. Graded
   S1|S2|S3 (WP-30): ...", NN being the section WP30_SECTION names, and
   listed in WP30_OPEN, which alone (with WP29_OPEN) exempts them from the
   release guard, with a "<!-- WP-30 <id> -->" marker in each CHANGELOG
   list WP30_LISTS names, until their section lands; then the key is gone,
   no marker is left, each of those lists holds a line ending
   "(WP-30, <id>)", and a closed entry's Resolution holds "(WP-30, <id>)".
   WP-30's closeout left WP30_OPEN empty; test_no_wp30_entry_remains_open
   keeps every P1 entry closed with no marker left.
10. WP-31's entries (.ultraplan/sections/index.md A4) are open in BUGS.md
   in the form "Not fixed because WP-31 section NN has not landed. Graded
   S1|S2|S3 (WP-31): ...", NN being the section WP31_SECTION names, listed
   in WP31_OPEN, which with WP29_OPEN and WP30_OPEN exempts them from the
   release guard, tracked "Open (WP-31 section NN)." in GAPS3.md section 9,
   with a "<!-- WP-31 <id> -->" marker in each CHANGELOG list WP31_LISTS
   names, until their section lands; then the key is gone, the Tracked
   line reads Closed or Partly closed, no marker is left, each list holds a
   line ending "(WP-31, <id>)", and a closed Resolution holds it too.

Run against the documents of 4ede074, before WP-23 changed them, 11 of
these 24 tests failed, each where the documents were wrong: 26 closed
BUGS.md entries named no test that exists (20 named none; 3 more named none
and have no covering test, yet did not say so; 3 named a class 0591142 had
deleted); 6 of the 7 open entries gave no reason for being open; 14 gaps
that DONE work packages list were not closed in GAPS.md (A9, B1-B4, D1, D7,
E6, E7, J1-J5), and J6 did not record the part WP-06 closed; D2 named WP-09
as a closer, which does not list it; 10 gap bodies said RESOLVED under a
heading that did not (A9, B1-B4, J1-J3, J5, J6), and K3's heading said
RESOLVED and named nothing; the dead-code gap N carried no status; and
TODO.md and PLAN.md were present.
"""
import ast
import os
import re
import subprocess

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)

#: Gaps a DONE work package lists, or that WP-23 closes, which may stay
#: open until WP-23's parts are integrated: WP-23 closes F4, M1, M4 and M5
#: (ROADMAP.md WP-23, "Gaps closed"), and WP-17 lists F4's bare-name row.
#: WP-23's integration empties this; test_the_allowances_are_still_needed
#: fails as soon as one of them is closed while it is still listed here.
WP23_OPEN_UNTIL_INTEGRATION = frozenset()

#: Gaps a DONE work package lists under "Gaps closed" although the package
#: did not close all of it, so the two documents disagree until ROADMAP.md
#: is corrected; the value says what is still open.  This file may not
#: close such a gap in GAPS.md (it is not closed), so the correction is
#: ROADMAP.md's: qualify the listing, as "E1 (nodraw)" is qualified, or
#: finish the work.  test_the_allowances_are_still_needed fails once an
#: entry no longer describes the documents.
ROADMAP_CORRECTIONS_PENDING = {}

#: Closed BUGS.md entries whose fix no test covers, by title.  Each says
#: "No regression test covers this" in its Resolution; writing the test
#: and naming it there removes the entry from this list (GAPS.md L9,
#: WP-24).
CLOSED_WITHOUT_A_TEST = frozenset()

_NO_TEST_PHRASE = "No regression test covers this"

#: The user's own planning records, which this project keeps outside the
#: reconciliation: they cite TODO.md and PLAN.md historically and are not
#: this file's to judge (REMAINING.md, phases/, .ultraplan/ and the
#: .ultraplan-archive-* directories).
_USER_RECORDS = ("REMAINING.md", "phases", ".ultraplan")

_SKIP_DIRS = {".git", ".claude", "__pycache__", ".pytest_cache",
              "node_modules"}


def _read(name):
    with open(os.path.join(_ROOT, name), encoding="utf-8") as fh:
        return fh.read()


# ===========================================================================
# BUGS.md
# ===========================================================================

_ENTRY = re.compile(r"^- \[(?P<mark>[ x])\] Title: (?P<title>\S.*)$")
_FIELDS = ("File Names and Line Numbers", "Description", "Suggested fix",
           "Resolution")
_FIELD = re.compile(r"^  - (?P<name>File Names and Line Numbers|Description|"
                    r"Suggested fix|Resolution)(?P<qual> \([^()\n]*\))?: \S")


def _parse_bugs(text):
    """(entries, problems) for a BUGS.md text.

    An entry is a dict: ``line`` (1-based), ``closed``, ``title``,
    ``fields`` (name -> its text, continuation lines included), ``order``
    (the field names as they appear) and ``text`` (the whole entry).  A
    problem is a string naming a line that belongs to no entry or a line
    that looks like an entry and is not one.
    """
    entries, problems, cur, last = [], [], None, None
    for n, ln in enumerate(text.split("\n"), 1):
        m = _ENTRY.match(ln)
        if m:
            cur = {"line": n, "closed": m.group("mark") == "x",
                   "title": m.group("title").strip(), "fields": {},
                   "order": [], "lines": [ln]}
            entries.append(cur)
            last = None
            continue
        if not ln.strip():
            continue
        if ln.startswith("- ") or ln.startswith("-["):
            problems.append("line %d is not an entry header of the form "
                            "'- [x] Title: ...' or '- [ ] Title: ...': %r"
                            % (n, ln[:80]))
            cur = None
            continue
        if cur is None:
            problems.append("line %d belongs to no entry: %r" % (n, ln[:80]))
            continue
        cur["lines"].append(ln)
        f = _FIELD.match(ln)
        if f:
            last = f.group("name")
            cur["order"].append(last)
            cur["fields"][last] = cur["fields"].get(last, "") + ln
        elif ln.startswith("  - "):
            last = None            # a note between fields, allowed
        elif ln.startswith("    ") and last is not None:
            cur["fields"][last] += "\n" + ln
        elif not ln.startswith("    "):
            problems.append("line %d of the entry at line %d is neither a "
                            "field, a note nor a continuation: %r"
                            % (n, cur["line"], ln[:80]))
    for e in entries:
        e["text"] = "\n".join(e.pop("lines"))
    return entries, problems


def _format_problems(entries):
    bad = []
    for e in entries:
        if e["order"] != list(_FIELDS):
            bad.append("line %d %r: fields %s, expected %s once each in that "
                       "order" % (e["line"], e["title"][:60], e["order"],
                                  list(_FIELDS)))
    return bad


@pytest.fixture(scope="module")
def bugs():
    entries, problems = _parse_bugs(_read("BUGS.md"))
    return entries, problems


# ---------------------------------------------------------------------------
# What exists under test/
# ---------------------------------------------------------------------------

def _test_files():
    return {f for f in os.listdir(_HERE)
            if os.path.isfile(os.path.join(_HERE, f))}


def _python_names(path):
    """{class name: set of method names, inherited from same-module bases
    included}, and the set of module-level function names."""
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    own, bases, funcs = {}, {}, set()
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            own[node.name] = {b.name for b in node.body
                              if isinstance(b, (ast.FunctionDef,
                                                ast.AsyncFunctionDef))}
            bases[node.name] = [b.id for b in node.bases
                                if isinstance(b, ast.Name)]
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs.add(node.name)

    def methods(cls, seen=()):
        out = set(own.get(cls, ()))
        for b in bases.get(cls, ()):
            if b in own and b not in seen:
                out |= methods(b, seen + (cls,))
        return out

    return {c: methods(c) for c in own}, funcs


_DISPLAY = re.compile(
    r"\bdi(?:s(?:p(?:l(?:a(?:y)?)?)?)?)?[ \t]+(?:as[ \t]+\w+[ \t]+)?`?\"")
_CASE_ID = re.compile(r"(?<![A-Za-z0-9_-])([A-Z][A-Z0-9]{0,5}(?:-[A-Z]+)*"
                      r"-\d{1,3}[a-z]?)(?![A-Za-z0-9_])")


def _code_lines(text):
    for ln in text.split("\n"):
        s = ln.lstrip()
        if s.startswith("*") or s.startswith("//"):
            continue
        yield ln


def _displayed_cases(text):
    """The case ids a certification script displays: a display statement
    whose string starts with the id (then " PASS", a space or a colon),
    or a call whose first argument is the id to a program the script
    defines that displays its first argument followed by " PASS" -- itself
    or through another such program it hands the argument to."""
    ids = set()
    lines = list(_code_lines(text))
    for ln in lines:
        for m in _DISPLAY.finditer(ln):
            c = _CASE_ID.match(ln, m.end())
            if c and re.match(r"(?: PASS|[ \t:])", ln[c.end():]):
                ids.add(c.group(1))
    progs, prog, body = {}, None, []
    for ln in lines:
        m = re.match(r"^\s*program\s+(?:define\s+)?(\w+)", ln)
        if m:
            prog, body = m.group(1), []
            continue
        if prog and re.match(r"^\s*end\s*$", ln):
            src = "\n".join(body)
            args = re.search(r"^\s*args\s+(\w+)", src, re.M)
            progs[prog] = (args.group(1) if args else "1", src)
            prog = None
            continue
        if prog:
            body.append(ln)
    helpers = {p for p, (first, src) in progs.items()
               if re.search(r"`%s'\s+PASS" % re.escape(first), src)}
    grew = True
    while grew:
        grew = False
        for p, (first, src) in progs.items():
            if p in helpers:
                continue
            for q in re.findall(r"^\s*(\w+)\s+\"?`%s'\"?(?=\s|$)"
                                % re.escape(first), src, re.M):
                if q in helpers:
                    helpers.add(p)
                    grew = True
                    break
    for ln in lines:
        m = re.match(r"^\s*(\w+)\s+\"?([A-Z][A-Z0-9]{0,5}(?:-[A-Z]+)*"
                     r"-\d{1,3}[a-z]?)\"?(?=\s|$)", ln)
        if m and m.group(1) in helpers:
            ids.add(m.group(2))
    return ids


@pytest.fixture(scope="module")
def tests_on_disk():
    files = _test_files()
    py = {f: _python_names(os.path.join(_HERE, f))
          for f in files if f.endswith(".py")}
    cases = set()
    for f in files:
        if f.endswith((".cscript", ".do")):
            with open(os.path.join(_HERE, f), encoding="utf-8",
                      errors="replace") as fh:
                cases |= _displayed_cases(fh.read())
    classes = set()
    for cls, _funcs in py.values():
        classes |= set(cls)
    return {"files": files, "py": py, "cases": cases, "classes": classes}


_FILE_REF = re.compile(r"(?<![\w/.-])(?:test/)?(test_\w+\.(?:py|cscript|do))"
                       r"(?!\w)")
_NODE_REF = re.compile(r"(test_\w+\.py)::(\w+)(?:::(\w+))?")
_CLASS_REF = re.compile(r"(?<![\w.])(Test[A-Z]\w+)")


def _acknowledged_gone(text, name):
    return re.search(re.escape(name) + r"[`']?\s+no longer exists", text)


def _references(entry_text, on_disk):
    """(found, dangling) test references in an entry's text.  *found* is
    the list of references that resolve; *dangling* the ones that do not
    and that the entry does not record as gone."""
    found, dangling = [], []
    for f in sorted(set(_FILE_REF.findall(entry_text))):
        if f in on_disk["files"]:
            found.append(f)
        elif not _acknowledged_gone(entry_text, f):
            dangling.append(f)
    for f, a, b in _NODE_REF.findall(entry_text):
        node = "::".join(x for x in (f, a, b) if x)
        classes, funcs = on_disk["py"].get(f, ({}, set()))
        # file::Class::test, file::Class, file::function -- or
        # file::test for a test inside a class the entry did not name,
        # which names a test that exists, if not its pytest node id.
        ok = ((a in classes and (not b or b in classes[a]))
              or (not b and (a in funcs
                             or any(a in m for m in classes.values()))))
        if ok:
            found.append(node)
        elif not _acknowledged_gone(entry_text, b or a):
            dangling.append(node)
    for c in sorted(set(_CLASS_REF.findall(entry_text))):
        if c not in on_disk["classes"] and not _acknowledged_gone(
                entry_text, c):
            dangling.append(c)
    for c in sorted(set(_CASE_ID.findall(entry_text))):
        if c in on_disk["cases"]:
            found.append(c)
    return found, dangling


class TestEveryBugsEntryIsWellFormed:
    """Five fields, once each, in order; nothing between entries."""

    def test_every_line_belongs_to_an_entry(self, bugs):
        _entries, problems = bugs
        assert not problems, "\n".join(problems)

    def test_every_entry_has_the_five_fields_in_order(self, bugs):
        entries, _problems = bugs
        bad = _format_problems(entries)
        assert not bad, "\n".join(bad)

    def test_there_are_entries(self, bugs):
        entries, _problems = bugs
        assert len(entries) > 200

    def test_the_parser_finds_what_is_wrong(self):
        good = ("- [x] Title: T\n  - File Names and Line Numbers: f\n"
                "  - Description: d\n  - Suggested fix: s\n"
                "  - Resolution (partial): r\n    a continuation\n"
                "  - Note on something: n\n")
        entries, problems = _parse_bugs(good)
        assert not problems and not _format_problems(entries)
        assert entries[0]["closed"] and entries[0]["title"] == "T"
        for bad in (good.replace("- [x]", "- [X]"),
                    good.replace("  - Description: d\n", ""),
                    good.replace("  - Suggested fix: s\n", "") +
                    "  - Suggested fix: s\n",
                    "stray text\n" + good,
                    good + "unindented tail\n"):
            entries, problems = _parse_bugs(bad)
            assert problems or _format_problems(entries), bad


class TestEveryClosedEntryNamesATestThatExists:
    """A closed entry points at the test that would fail if the defect came
    back -- or says that none does and is listed in CLOSED_WITHOUT_A_TEST."""

    def test_every_closed_entry_names_an_existing_test(self, bugs,
                                                       tests_on_disk):
        entries, _p = bugs
        missing = []
        for e in entries:
            if not e["closed"] or e["title"] in CLOSED_WITHOUT_A_TEST:
                continue
            found, _dangling = _references(e["text"], tests_on_disk)
            if not found:
                missing.append("line %d: %s" % (e["line"], e["title"][:90]))
        assert not missing, (
            "closed BUGS.md entries that name no test file, pytest node or "
            "displayed cert case that exists:\n" + "\n".join(missing))

    def test_no_entry_names_a_test_that_does_not_exist(self, bugs,
                                                       tests_on_disk):
        entries, _p = bugs
        bad = []
        for e in entries:
            _found, dangling = _references(e["text"], tests_on_disk)
            if dangling:
                bad.append("line %d %s: %s" % (e["line"], e["title"][:60],
                                               dangling))
        assert not bad, (
            "BUGS.md entries naming a test that does not exist (say `X` no "
            "longer exists, and name the test that covers it):\n"
            + "\n".join(bad))

    def test_the_entries_without_a_test_say_so(self, bugs):
        entries, _p = bugs
        by_title = {e["title"]: e for e in entries}
        for title in CLOSED_WITHOUT_A_TEST:
            assert title in by_title, "no BUGS.md entry titled %r" % title
            e = by_title[title]
            assert e["closed"], "%r is listed as closed and is open" % title
            assert _NO_TEST_PHRASE in e["fields"]["Resolution"], (
                "%r must say %r in its Resolution" % (title, _NO_TEST_PHRASE))
        saying = {e["title"] for e in entries
                  if _NO_TEST_PHRASE in e["fields"].get("Resolution", "")}
        assert saying <= CLOSED_WITHOUT_A_TEST, (
            "entries saying no test covers them, not listed in "
            "CLOSED_WITHOUT_A_TEST: %s" % sorted(saying - CLOSED_WITHOUT_A_TEST))

    def test_the_reference_reader(self):
        on_disk = {"files": {"test_a.py", "test_b.cscript"},
                   "py": {"test_a.py": ({"TestX": {"test_y"}}, {"test_f"})},
                   "cases": {"AB-01"}, "classes": {"TestX"}}
        assert _references("see test/test_a.py", on_disk) == (
            ["test_a.py"], [])
        assert _references("test_a.py::TestX::test_y", on_disk)[0] == [
            "test_a.py", "test_a.py::TestX::test_y"]
        assert _references("test_a.py::TestX::test_z", on_disk)[1] == [
            "test_a.py::TestX::test_z"]
        assert _references("case AB-01 passes", on_disk)[0] == ["AB-01"]
        assert _references("case AB-02 passes", on_disk) == ([], [])
        assert _references("class TestGone", on_disk)[1] == ["TestGone"]
        assert _references("`TestGone` no longer exists; test_b.cscript",
                           on_disk) == (["test_b.cscript"], [])

    def test_the_case_detector(self):
        text = ('display "P9-01 PASS: x"\n'
                'else display as text "SR-07 PASS: y"\n'
                'display "C-05: counted"\n'
                '// display "P7-01 PASS: in a comment"\n'
                '*! OV-99 described in a header\n'
                'display "  P19-17..21: a summary line"\n'
                'capture program drop _k_case\n'
                'program define _k_case\n'
                '    args id cmd\n'
                '    display as text `"`id\' PASS: `cmd\'"\'\n'
                'end\n'
                '_k_case OV-01 `"dash scatter"\'\n'
                '_k_other OV-02\n'
                'program define _k_tally\n'
                '    args id bad\n'
                '    if !`bad\' display as text `"`id\' PASS"\'\n'
                'end\n'
                'program define _k_probe\n'
                '    args id cmd\n'
                '    _k_tally "`id\'" 0\n'
                'end\n'
                '_k_probe SO-01 `"dash lfit"\'\n')
        ids = _displayed_cases(text)
        assert {"P9-01", "SR-07", "C-05", "OV-01", "SO-01"} <= ids
        assert not ids & {"P7-01", "OV-99", "P19-17", "OV-02"}


class TestEveryOpenEntrySaysWhyItIsOpen:
    """An open entry states that it is open and gives the reason: its
    Resolution carries "Not fixed", "still open", "stays open" or "remains
    open", and a "because"."""

    _OPEN = re.compile(r"\b(not fixed|still open|stays open|remains open)\b",
                       re.I)

    def test_every_open_entry_says_why(self, bugs):
        entries, _p = bugs
        bad = []
        for e in entries:
            if e["closed"]:
                continue
            res = e["fields"].get("Resolution", "")
            if not (self._OPEN.search(res) and re.search(r"\bbecause\b",
                                                         res)):
                bad.append("line %d: %s" % (e["line"], e["title"][:90]))
        assert not bad, (
            "open BUGS.md entries whose Resolution does not say it is open "
            "and why:\n" + "\n".join(bad))


class TestNoResidualNamesAClosedRow:
    """A Resolution that hands a residual on as "(P2.<n>)" names a DROPIN
    P2 row that is still open; a row written closed is not cited as open
    work (WP-30 follow-up: P1.10's residual named P2.46 after 4fda248
    closed it)."""

    _ROW = re.compile(r"^(\d+)\. (.*)$")
    _CITED = re.compile(r"\(P2\.(\d+)\)")

    def test_every_cited_row_is_open(self, bugs):
        rows, section = {}, None
        for line in _read(".ultraplan/handoff/DROPIN-REMAINING.md"
                          ).splitlines():
            if line.startswith("### "):
                section = line[4:7]
            m = self._ROW.match(line)
            if m and section == "P2:":
                rows[int(m.group(1))] = m.group(2)
        entries, _p = bugs
        bad = []
        for e in entries:
            for n in self._CITED.findall(e["fields"].get("Resolution", "")):
                row = rows.get(int(n), "")
                if "Written closed" in row or "[Closed in" in row:
                    bad.append("line %d: P2.%s in %s" % (
                        e["line"], n, e["title"][:70]))
        assert rows, "DROPIN-REMAINING.md's P2 list was not found"
        assert not bad, ("residuals that name a closed DROPIN row:\n"
                         + "\n".join(bad))


class TestNoOpenEntryBlocksARelease:
    """WP-27's BR-27.2: no S1 or S2 defect is open at release.

    Every open entry carries its grade on GAPS.md's scale in its Resolution,
    once, as "Graded S<n> (WP-27): <why>" -- S1 silently wrong output or a
    documented feature broken outright, S2 a documented or accepted
    capability that fails visibly, S3 fidelity, hygiene, coverage or
    documentation drift -- and none is S1 or S2.  An entry opened later is
    graded when it is written, and one graded S1 or S2 stops the release.
    """

    _GRADE = re.compile(r"\bGraded (S[1-3]) \(WP-\d{2}\): \S")

    def test_every_open_entry_is_graded_once(self, bugs):
        entries, _p = bugs
        bad = ["line %d: %s" % (e["line"], e["title"][:90])
               for e in entries if not e["closed"]
               and len(self._GRADE.findall(e["fields"].get("Resolution", "")))
               != 1]
        assert not bad, ("open BUGS.md entries without exactly one "
                         "'Graded S<n> (WP-NN): <why>':\n" + "\n".join(bad))

    def test_no_open_entry_is_s1_or_s2(self, bugs):
        entries, _p = bugs
        # WP-29's P0 entries stayed open, S1 or S2, until their sections
        # landed (WP29_OPEN, empty since its closeout); WP-30's P1 entries
        # do the same until theirs land (WP30_OPEN), and TestWp30Tracking
        # holds each one to its WP-30 form.  WP-31's entries do the same
        # until theirs land (WP31_OPEN; TestWp31Tracking).
        allowed = (set(WP29_OPEN.values()) | set(WP30_OPEN.values())
                   | set(WP31_OPEN.values()))
        bad = ["line %d: %s %s" % (e["line"], g, e["title"][:90])
               for e in entries if not e["closed"]
               and e["title"] not in allowed
               for g in self._GRADE.findall(e["fields"].get("Resolution", ""))
               if g in ("S1", "S2")]
        assert not bad, ("open S1/S2 BUGS.md entries block the release:\n"
                         + "\n".join(bad))

    def test_the_grade_reader(self):
        entries, _p = _parse_bugs(
            "- [ ] Title: a\n  - File Names and Line Numbers: f\n"
            "  - Description: d\n  - Suggested fix: s\n"
            "  - Resolution: Not fixed because x. Graded S1 (WP-27): wrong "
            "output.\n")
        res = entries[0]["fields"]["Resolution"]
        assert self._GRADE.findall(res) == ["S1"]
        assert self._GRADE.findall("Graded S3: no package") == []


# ===========================================================================
# GAPS.md and ROADMAP.md
# ===========================================================================

_DASH = " \u2014 "
_STATUS_START = re.compile(r"^(S[1-3]\b|MEASURED|READ|SUSPECTED|RESOLVED|"
                           r"no gap|not a gap)", re.I)
_GAP_HEADING = re.compile(r"^(#{2,3}) ([A-N]\d{0,2})\. (.+)$")
_RESOLVED_BODY = re.compile(r"^\*\*(?:RESOLVED|CORRECTED, then CLOSED|"
                            r"Closed\b|CLOSED\b|Finished by|\w+ closed by)")
_WP = re.compile(r"\bWP-\d{2}\b")
_SHA = re.compile(r"\b[0-9a-f]{7,40}\b")


def _matrix_gaps(roadmap):
    part = roadmap.split("## Traceability matrix", 1)[1]
    part = part.split("\n## ", 1)[0]
    return {m.group(1) for m in re.finditer(r"^\| ([A-N]\d{0,2}) \|", part,
                                            re.M)}


def _matrix_rows(roadmap):
    """The body rows of ROADMAP.md's traceability matrix: its table's
    lines after the header and the rule, read as table lines and nothing
    more, so they count what _matrix_gaps should have read."""
    part = roadmap.split("## Traceability matrix", 1)[1]
    part = part.split("\n## ", 1)[0]
    table = [ln for ln in part.split("\n") if ln.startswith("|")]
    assert len(table) > 2 and table[0].startswith("| Gap |") and \
        set(table[1]) <= set("|-: "), table[:2]
    return table[2:]


def _status(title):
    """The status part of a gap heading's title, or ''."""
    parts = title.split(_DASH)
    for i in range(1, len(parts)):
        if _STATUS_START.match(parts[i]):
            return _DASH.join(parts[i:])
    return ""


def _closers(segment):
    """The work packages and commits named after "CLOSED by" in a status
    segment; a parenthetical is commentary, not a closer."""
    tail = segment.split("CLOSED by", 1)[1]
    while re.search(r"\([^()]*\)", tail):
        tail = re.sub(r"\([^()]*\)", " ", tail)
    return set(_WP.findall(tail)), set(_SHA.findall(tail))


def _classify(status):
    """(kind, full closers, partial closers).  kind is 'none' for no gap,
    'closed', 'partial' or 'open'."""
    if re.match(r"^(no gap|not a gap)", status, re.I):
        return "none", None, None
    segs = [s.strip() for s in status.split(";")]
    full = _closers(segs[0]) if "CLOSED by" in segs[0] else None
    partial = [_closers(s) for s in segs[1:] if "CLOSED by" in s]
    if full:
        return "closed", full, partial
    return ("partial" if partial else "open"), None, partial


def _parse_gaps(text, matrix):
    gaps, dupes = {}, []
    lines = text.split("\n")
    heads = [(i, _GAP_HEADING.match(ln)) for i, ln in enumerate(lines)]
    heads = [(i, m) for i, m in heads
             if m and (m.group(1) == "###" or m.group(2) in matrix)]
    for k, (i, m) in enumerate(heads):
        gid = m.group(2)
        nxt = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        body = []
        for ln in lines[i + 1:nxt]:
            if ln.startswith("## ") or ln.startswith("# "):
                break
            body.append(ln)
        status = _status(m.group(3))
        kind, full, partial = _classify(status) if status else (
            "missing", None, None)
        if gid in gaps:
            dupes.append(gid)
        gaps[gid] = {"title": m.group(3), "status": status, "kind": kind,
                     "full": full, "partial": partial, "body": body,
                     "line": i + 1}
    return gaps, dupes


def _split_items(field):
    items, depth, cur = [], 0, ""
    for ch in field:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            items.append(cur)
            cur = ""
        else:
            cur += ch
    items.append(cur)
    return [i.strip() for i in items if i.strip()]


def _wp_sections(text):
    """(wp, head, section, done) for every ``## WP-nn ...`` section of a
    ROADMAP.md text, in order.  Factored out of _parse_roadmap so a second
    reader (_parse_roadmap_gaps2) can share the same splitting without
    changing _parse_roadmap's return value (test_the_roadmap_reader pins
    that value exactly)."""
    parts = re.split(r"^(?=## WP-\d{2} )", text, flags=re.M)
    for part in parts[1:]:
        head = part.split("\n", 1)[0]
        wp = re.match(r"^## (WP-\d{2}) ", head).group(1)
        section = re.split(r"^# ", part, flags=re.M)[0]
        section = re.split(r"^## (?!WP-)", section, flags=re.M)[0]
        done = (head.rstrip().endswith("\u2014 DONE")
                or re.search(r"^> \*\*DONE\b", section, re.M) is not None)
        yield wp, head, section, done


def _parse_roadmap(text):
    """{WP-nn: {'done': bool, 'gaps': {gap: qualified?}}}."""
    wps = {}
    for wp, _head, section, done in _wp_sections(text):
        gaps = {}
        m = re.search(r"^\*\*Gaps closed:\*\* (.+?)(?: \u00b7 |$)", section,
                      re.M)
        if m:
            for item in _split_items(m.group(1)):
                g = re.match(r"^(?:and\s+)?([A-N]\d{0,2})(?![A-Za-z0-9-])"
                             r"(.*)$", item)
                if g:
                    rest = g.group(2).strip()
                    gaps[g.group(1)] = rest.startswith(("(", "'s"))
        wps[wp] = {"done": done, "gaps": gaps}
    return wps


# ---------------------------------------------------------------------------
# GAPS2.md and WP-28's **GAPS2 closed:** field (TR-01.2, TR-01.3)
# ---------------------------------------------------------------------------
#
# GAPS2.md (the audit of 91d97be) heads each gap ``### <ID>. <title>`` and
# ends its entry with a ``- **Tracked:** ...`` line.  A package that closes
# GAPS2 gaps declares them through a new ``**GAPS2 closed:**`` header
# field, never the old ``**Gaps closed:**`` field _parse_roadmap reads
# above (that regex does not match this text, so the old reader silently
# ignores it -- proven by test_the_gaps2_readers).

_GAPS2_HEADING = re.compile(r"^### (?P<id>[A-NX]\d{1,2})\. (?P<title>\S.*)$")
_GAPS2_TRACKED = re.compile(r"^- \*\*Tracked:\*\* (?P<text>\S.*)$")
_GAPS2_CLOSED = re.compile(
    r'^Closed in (WP-\d{2}), BUGS\.md "([^"]+)", commit ([0-9a-f]{7,40})\b')
_GAPS2_DEFERRED = re.compile(r"^Deferred \((WP-\d{2})\): \S")


def _parse_gaps2(text):
    """({id: entry}, dupes) for a GAPS2.md text.  An entry is a dict:
    ``title``, ``line`` (1-based), ``tracked`` (the Tracked line's text,
    or None), ``closed`` (a (wp, bugs_title, sha) tuple when the Tracked
    text matches _GAPS2_CLOSED) and ``deferred`` (a wp string when it
    matches _GAPS2_DEFERRED).  Text after the point either pattern stops
    matching is commentary (residuals, the original audit text) and is not
    read further."""
    entries, dupes = {}, []
    lines = text.split("\n")
    heads = [(i, m) for i, ln in enumerate(lines)
             for m in (_GAPS2_HEADING.match(ln),) if m]
    for k, (i, m) in enumerate(heads):
        gid = m.group("id")
        nxt = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        tracked = None
        for ln in lines[i + 1:nxt]:
            if ln.startswith("## ") or ln.startswith("# "):
                break
            tm = _GAPS2_TRACKED.match(ln)
            if tm:
                tracked = tm.group("text")
                break
        closed = deferred = None
        if tracked:
            cm = _GAPS2_CLOSED.match(tracked)
            if cm:
                closed = (cm.group(1), cm.group(2), cm.group(3))
            else:
                dm = _GAPS2_DEFERRED.match(tracked)
                if dm:
                    deferred = dm.group(1)
        if gid in entries:
            dupes.append(gid)
        entries[gid] = {"title": m.group("title"), "line": i + 1,
                        "tracked": tracked, "closed": closed,
                        "deferred": deferred}
    return entries, dupes


def _parse_roadmap_gaps2(text):
    """{wp: {'done': bool, 'gaps2': {id: qualified?}}}, read from each
    section's ``**GAPS2 closed:**`` field.  Mirrors _parse_roadmap's own
    ``**Gaps closed:**`` reading, on the new field, so the two never
    collide: a section with only the old field yields ``{}`` here, and a
    section with only the new field yields ``{}`` from _parse_roadmap
    (test_the_gaps2_readers pins both directions)."""
    wps2 = {}
    for wp, _head, section, done in _wp_sections(text):
        gaps2 = {}
        m = re.search(r"^\*\*GAPS2 closed:\*\* (.+?)(?: \u00b7 |$)", section,
                      re.M)
        if m:
            for item in _split_items(m.group(1)):
                g = re.match(r"^(?:and\s+)?([A-NX]\d{0,2})"
                             r"(?![A-Za-z0-9-])(.*)$", item)
                if g:
                    rest = g.group(2).strip()
                    gaps2[g.group(1)] = rest.startswith(("(", "'s"))
        wps2[wp] = {"done": done, "gaps2": gaps2}
    return wps2


@pytest.fixture(scope="module")
def docs():
    roadmap = _read("ROADMAP.md")
    matrix = _matrix_gaps(roadmap)
    gaps, dupes = _parse_gaps(_read("GAPS.md"), matrix)
    gaps2, gaps2_dupes = _parse_gaps2(_read("GAPS2.md"))
    return {"matrix": matrix, "gaps": gaps, "dupes": dupes,
            "wps": _parse_roadmap(roadmap), "gaps2": gaps2,
            "gaps2_dupes": gaps2_dupes, "wps2": _parse_roadmap_gaps2(roadmap)}


def _git(*args):
    return subprocess.run(["git", "-C", _ROOT] + list(args),
                          capture_output=True, text=True)


class TestEveryGapHasAStatus:

    def test_every_gap_in_the_matrix_has_one_heading(self, docs):
        # Every row of the matrix is read: one gap id per body row.  A row
        # the reader cannot read -- an id outside A-N, a bold id, a doubled
        # blank -- was a gap this never looked for, and a matrix read as
        # nothing had no gap to miss.  Measured 24sep2026: a row "| O1 |
        # ... |" added to the matrix, with no heading in GAPS.md, passed.
        rows = _matrix_rows(_read("ROADMAP.md"))
        assert len(docs["matrix"]) == len(rows), (
            "the matrix has %d rows and %d gaps were read from it: %s"
            % (len(rows), len(docs["matrix"]),
               [r[:40] for r in rows
                if not re.match(r"^\| ([A-N]\d{0,2}) \|", r)]))
        missing = sorted(docs["matrix"] - set(docs["gaps"]))
        assert not missing, "gaps with no GAPS.md heading: %s" % missing
        assert not docs["dupes"], "gaps with two headings: %s" % docs["dupes"]

    def test_every_gap_heading_carries_a_status(self, docs):
        bad = ["%s (line %d): %s" % (g, v["line"], v["title"])
               for g, v in sorted(docs["gaps"].items())
               if v["kind"] == "missing"]
        assert not bad, (
            "gap headings with no status (MEASURED, READ, SUSPECTED, CLOSED "
            "by ..., no gap):\n" + "\n".join(bad))

    def test_a_resolved_body_is_a_closed_heading(self, docs):
        bad = []
        for g, v in sorted(docs["gaps"].items()):
            claims = [ln for ln in v["body"] if _RESOLVED_BODY.match(ln)]
            if "RESOLVED" in v["status"] and "CLOSED by" not in v["status"]:
                bad.append("%s: the heading says RESOLVED and names nothing"
                           % g)
            elif claims and "CLOSED by" not in v["status"]:
                bad.append("%s: the body says %r under the heading %r"
                           % (g, claims[0][:50], v["status"]))
        assert not bad, "\n".join(bad)

    def test_the_status_reader(self):
        assert _status("x \u2014 what slips through \u2014 S3, MEASURED") == \
            "S3, MEASURED"
        assert _status("Auth \u2014 not a gap \u2014 note (WP-20)") == \
            "not a gap \u2014 note (WP-20)"
        assert _status("no status here") == ""
        assert _classify("S1, READ, CLOSED by WP-09 (with WP-10)") == (
            "closed", ({"WP-09"}, set()), [])
        assert _classify("S1, MEASURED, CLOSED by 9c7dbf7 (WP-01)")[1] == (
            set(), {"9c7dbf7"})
        assert _classify("S2, READ; nodraw CLOSED by WP-13") == (
            "partial", None, [({"WP-13"}, set())])
        assert _classify("S1, MEASURED; fixed by 81ebbc5")[0] == "open"
        assert _classify("no gap")[0] == "none"


class TestGapsAndRoadmapAgree:

    def test_every_closed_gap_names_what_closed_it(self, docs):
        bad = []
        for g, v in sorted(docs["gaps"].items()):
            named = ([v["full"]] if v["full"] else []) + (v["partial"] or [])
            if v["kind"] in ("closed", "partial") and any(
                    not (wps or shas) for wps, shas in named):
                bad.append("%s: %s" % (g, v["status"]))
        assert not bad, (
            "gaps marked closed without naming a work package or commit:\n"
            + "\n".join(bad))

    def test_a_closing_work_package_is_done_and_lists_the_gap(self, docs):
        bad = []
        for g, v in sorted(docs["gaps"].items()):
            named = ([v["full"]] if v["full"] else []) + (v["partial"] or [])
            for wps, _shas in named:
                for wp in sorted(wps):
                    info = docs["wps"].get(wp)
                    if info is None:
                        bad.append("%s names %s, which ROADMAP.md lacks"
                                   % (g, wp))
                    elif not info["done"]:
                        bad.append("%s names %s, which ROADMAP.md does not "
                                   "head DONE" % (g, wp))
                    elif g not in info["gaps"]:
                        bad.append("%s names %s, whose \"Gaps closed\" does "
                                   "not list it" % (g, wp))
        assert not bad, "\n".join(bad)

    def test_a_closing_commit_exists(self, docs):
        shas = {(g, s) for g, v in docs["gaps"].items()
                for _w, ss in (([v["full"]] if v["full"] else [])
                               + (v["partial"] or []))
                for s in ss}
        # GAPS.md closes ten gaps by a named commit (measured 24sep2026).
        # None found is a parser that stopped reading them, not a document
        # with nothing to check: this returned green on it.
        assert shas, "no gap heading names a closing commit"
        # Environmental: a copy with no .git (an unpacked package) has no
        # history to check the names against.
        if _git("rev-parse", "--git-dir").returncode != 0:
            pytest.skip("not a git working tree")
        bad = sorted("%s names %s" % (g, s) for g, s in shas
                     if _git("cat-file", "-e", s + "^{commit}").returncode)
        assert not bad, "gaps naming a commit git does not have:\n" + \
            "\n".join(bad)

    def test_every_gap_a_done_package_lists_is_closed_by_it(self, docs):
        bad = []
        for wp, info in sorted(docs["wps"].items()):
            if not info["done"]:
                continue
            for g, qualified in sorted(info["gaps"].items()):
                if g in WP23_OPEN_UNTIL_INTEGRATION or \
                        g in ROADMAP_CORRECTIONS_PENDING:
                    continue
                v = docs["gaps"].get(g)
                if v is None:
                    bad.append("%s lists %s, which GAPS.md lacks" % (wp, g))
                    continue
                full_by = v["full"][0] if v["full"] else set()
                part_by = set().union(*[w for w, _s in (v["partial"] or [])])
                if qualified:
                    ok = wp in full_by or wp in part_by
                else:
                    ok = wp in full_by
                if not ok:
                    bad.append("%s is DONE and lists %s%s; GAPS.md says %r"
                               % (wp, g, " (qualified)" if qualified else "",
                                  v["status"]))
        assert not bad, (
            "gaps a DONE work package lists that GAPS.md does not mark "
            "closed by it:\n" + "\n".join(bad))

    def test_the_allowances_are_still_needed(self, docs):
        stale = []
        for g in sorted(WP23_OPEN_UNTIL_INTEGRATION):
            v = docs["gaps"].get(g)
            if v is None or v["kind"] == "closed":
                stale.append("%s is closed in GAPS.md: remove it from "
                             "WP23_OPEN_UNTIL_INTEGRATION" % g)
        for g in sorted(ROADMAP_CORRECTIONS_PENDING):
            v = docs["gaps"].get(g)
            listers = [wp for wp, info in docs["wps"].items()
                       if info["done"] and info["gaps"].get(g) is False]
            if not listers:
                stale.append("no DONE work package lists %s unqualified any "
                             "more: remove it from "
                             "ROADMAP_CORRECTIONS_PENDING" % g)
            elif v is None or v["kind"] == "closed":
                stale.append("%s is closed in GAPS.md: remove it from "
                             "ROADMAP_CORRECTIONS_PENDING" % g)
            elif not any(set(listers) & w for w, _s in (v["partial"] or [])):
                stale.append("%s: GAPS.md no longer records the part %s did "
                             "close" % (g, listers))
        assert not stale, "\n".join(stale)

    def test_the_roadmap_reader(self):
        text = ("## WP-01 \u00b7 A\n\n**Gaps closed:** A1, A2 \u00b7 "
                "**Severity:** S1\n\n## WP-02 \u00b7 B \u2014 DONE\n\n"
                "**Gaps closed:** E1 (nodraw), F4's bare-name row, "
                "WP-05's AC-05.3 \u00b7 **Severity:** S2\n\n"
                "## WP-03 \u00b7 C\n\n**Gaps closed:** A4, A5, and A3 "
                "finished (weights honoured, not only named) \u00b7 x\n\n"
                "> **DONE.** it is.\n\n# Milestone\n")
        wps = _parse_roadmap(text)
        assert wps["WP-01"] == {"done": False,
                                "gaps": {"A1": False, "A2": False}}
        assert wps["WP-02"] == {"done": True,
                                "gaps": {"E1": True, "F4": True}}
        assert wps["WP-03"] == {"done": True, "gaps": {
            "A4": False, "A5": False, "A3": False}}


# ===========================================================================
# TODO.md and PLAN.md
# ===========================================================================

_RETIRED = ("TODO.md", "PLAN.md")
_MD_LINK = re.compile(r"(?:\]\(\s*|<|\]:\s*|href=[\"'])(?:\./)?"
                      r"(?:TODO|PLAN)\.md\b")
_PLAIN = re.compile(r"(?<![\w/.-])(?:\./)?(?:TODO|PLAN)\.md\b")
_TEXT_EXT = (".md", ".py", ".ado", ".do", ".cscript", ".mata", ".sthlp",
             ".pkg", ".toc", ".toml", ".cfg", ".ini", ".txt", ".json",
             ".yml", ".yaml", ".sh", ".scheme", ".smcl", ".hlp")


def _repository_files():
    for dirpath, dirnames, filenames in os.walk(_ROOT):
        rel = os.path.relpath(dirpath, _ROOT)
        dirnames[:] = [d for d in dirnames
                       if d not in _SKIP_DIRS
                       and not (rel == "." and d.startswith(_USER_RECORDS))]
        for f in filenames:
            if rel == "." and f in _USER_RECORDS:
                continue
            if f.endswith(_TEXT_EXT):
                yield os.path.join(dirpath, f)


def _links_to_retired(path, text):
    """The lines of *text* that link TODO.md or PLAN.md: in Markdown a
    link, anywhere else any mention of either name."""
    rx = _MD_LINK if path.endswith(".md") else _PLAIN
    return [ln.strip()[:100] for ln in text.split("\n") if rx.search(ln)]


class TestTodoAndPlanAreRetired:
    """GAPS.md M1: TODO.md (555 items, all checked) and PLAN.md described a
    roadmap ROADMAP.md overtook.  They are deleted -- git keeps them, last
    changed at 5f857fc -- and nothing may point a reader at them."""

    @pytest.mark.parametrize("name", _RETIRED)
    def test_it_is_gone(self, name):
        assert not os.path.exists(os.path.join(_ROOT, name)), (
            "%s is retired (GAPS.md M1); delete it" % name)

    def test_nothing_links_them(self):
        me = os.path.abspath(__file__)
        bad = []
        for path in _repository_files():
            if os.path.abspath(path) == me:
                continue
            try:
                with open(path, encoding="utf-8") as fh:
                    text = fh.read()
            except (UnicodeDecodeError, OSError):
                continue
            for ln in _links_to_retired(path, text):
                bad.append("%s: %s" % (os.path.relpath(path, _ROOT), ln))
        assert not bad, "links to a retired document:\n" + "\n".join(bad)

    def test_the_link_reader(self):
        assert _links_to_retired("a.md", "see [the plan](PLAN.md) here")
        assert _links_to_retired("a.md", "[t]: ./TODO.md")
        assert not _links_to_retired("a.md", "`TODO.md` was retired")
        assert not _links_to_retired("a.md", "see .ultraplan/PLAN.md")
        assert _links_to_retired("dash.pkg", "f TODO.md")
        assert not _links_to_retired("x.py", "MY_PLAN.md_x = 1")


# ===========================================================================
# GAPS2.md and WP-28 (item 7 of the module docstring)
# ===========================================================================

class TestGaps2AndRoadmapAgree:
    """GAPS2.md (the audit of 91d97be, `GAPS2 closed:` fields, item 7 of
    this module's docstring)."""

    def test_the_gaps2_readers(self):
        text = (
            "### B1. Axis-label rules misread quoted numeric text\n\n"
            "Body text describing the gap goes here.\n\n"
            "- **Tracked:** Closed in WP-28, BUGS.md \"Axis labels are "
            "wrong\", commit 0123abcd\n\n"
            "### G1. Internal column names can overwrite a user variable\n\n"
            "- **Tracked:** Deferred (WP-28): the c(maxvar) room issue "
            "stays open.\n\n"
            "### X1. Dropdown filters rewrite string codes\n\n"
            "- **Tracked:** new.\n"
        )
        gaps2, dupes = _parse_gaps2(text)
        assert dupes == []
        assert set(gaps2) == {"B1", "G1", "X1"}
        assert gaps2["B1"]["title"] == \
            "Axis-label rules misread quoted numeric text"
        assert gaps2["B1"]["closed"] == \
            ("WP-28", "Axis labels are wrong", "0123abcd")
        assert gaps2["B1"]["deferred"] is None
        assert gaps2["G1"]["closed"] is None
        assert gaps2["G1"]["deferred"] == "WP-28"
        assert gaps2["X1"]["closed"] is None
        assert gaps2["X1"]["deferred"] is None
        assert gaps2["X1"]["tracked"] == "new."

        roadmap = ("## WP-30 · Something\n\n"
                  "**GAPS2 closed:** B1, G1 · **Severity:** S1\n\n"
                  "> body\n")
        assert _parse_roadmap_gaps2(roadmap) == {
            "WP-30": {"done": False, "gaps2": {"B1": False, "G1": False}}}
        # the old reader's field regex does not match the new field, so a
        # section holding only **GAPS2 closed:** yields no gaps at all.
        assert _parse_roadmap(roadmap) == {
            "WP-30": {"done": False, "gaps": {}}}

    def test_every_gaps2_id_a_package_declares_has_a_heading(self, docs):
        text = ("## WP-30 · Something\n\n"
                "**GAPS2 closed:** B1, X9 · **Severity:** S1\n\n")
        wps2 = _parse_roadmap_gaps2(text)
        known = {"B1"}
        bad_inline = ["%s declares %s, which GAPS2.md has no heading for"
                     % (wp, gid)
                     for wp, info in wps2.items()
                     for gid in sorted(info["gaps2"])
                     if gid not in known]
        assert bad_inline == \
            ["WP-30 declares X9, which GAPS2.md has no heading for"]

        bad = ["%s declares %s, which GAPS2.md has no heading for"
              % (wp, gid)
              for wp, info in sorted(docs["wps2"].items())
              for gid in sorted(info["gaps2"])
              if gid not in docs["gaps2"]]
        assert not bad, "\n".join(bad)
        assert not docs["gaps2_dupes"], \
            "GAPS2.md ids with two headings: %s" % docs["gaps2_dupes"]

    def test_every_gaps2_id_a_done_package_lists_is_closed_by_it(self, docs):
        text_wp = ("## WP-30 · Something — DONE\n\n"
                  "**GAPS2 closed:** B1 · **Severity:** S1\n\n")
        text_gaps2 = "### B1. Axis labels misread\n\n- **Tracked:** new.\n"
        wps2 = _parse_roadmap_gaps2(text_wp)
        gaps2, _dupes = _parse_gaps2(text_gaps2)
        bad_inline = []
        for wp, info in wps2.items():
            if not info["done"]:
                continue
            for gid in sorted(info["gaps2"]):
                entry = gaps2.get(gid)
                if entry is None or entry["closed"] is None or \
                        entry["closed"][0] != wp:
                    bad_inline.append(
                        "%s is DONE and lists %s, whose Tracked line does "
                        "not say Closed in %s" % (wp, gid, wp))
        assert bad_inline == [
            "WP-30 is DONE and lists B1, whose Tracked line does not say "
            "Closed in WP-30"]

        bad = []
        for wp, info in sorted(docs["wps2"].items()):
            if not info["done"]:
                continue
            for gid in sorted(info["gaps2"]):
                entry = docs["gaps2"].get(gid)
                if entry is None:
                    bad.append("%s lists %s, which GAPS2.md lacks" %
                              (wp, gid))
                elif entry["closed"] is None or entry["closed"][0] != wp:
                    bad.append(
                        "%s is DONE and lists %s, whose Tracked line does "
                        "not say Closed in %s" % (wp, gid, wp))
        assert not bad, "\n".join(bad)

    def test_every_closed_gaps2_entry_is_listed_by_its_package(self, docs):
        text_gaps2 = (
            "### B1. Axis labels misread\n\n"
            "- **Tracked:** Closed in WP-30, BUGS.md \"x\", commit "
            "0123abc\n")
        text_wp = ("## WP-30 · Something\n\n"
                  "**GAPS2 closed:** · **Severity:** S1\n\n")
        gaps2, _dupes = _parse_gaps2(text_gaps2)
        wps2 = _parse_roadmap_gaps2(text_wp)
        bad_inline = []
        for gid, entry in sorted(gaps2.items()):
            if entry["closed"] is None:
                continue
            wp = entry["closed"][0]
            info = wps2.get(wp)
            if info is None or not info["done"] or gid not in info["gaps2"]:
                bad_inline.append(
                    "%s says Closed in %s, which does not list it as DONE"
                    % (gid, wp))
        assert bad_inline == [
            "B1 says Closed in WP-30, which does not list it as DONE"]

        bad = []
        for gid, entry in sorted(docs["gaps2"].items()):
            if entry["closed"] is None:
                continue
            wp = entry["closed"][0]
            info = docs["wps2"].get(wp)
            if info is None:
                bad.append("%s names %s, which ROADMAP.md lacks" %
                          (gid, wp))
            elif not info["done"]:
                bad.append("%s names %s, which is not headed DONE" %
                          (gid, wp))
            elif gid not in info["gaps2"]:
                bad.append(
                    "%s names %s, whose GAPS2 closed field does not list "
                    "it" % (gid, wp))
        assert not bad, "\n".join(bad)

    def test_every_closed_gaps2_entry_names_a_closed_bugs_entry_and_a_commit(
            self, docs, bugs):
        text_gaps2 = (
            "### B1. Axis labels misread\n\n"
            "- **Tracked:** Closed in WP-30, BUGS.md \"No such title\", "
            "commit 0123abc\n")
        gaps2, _dupes = _parse_gaps2(text_gaps2)
        fake_entries = [{"closed": True, "title": "A real title",
                        "fields": {"Resolution":
                                  "Fixed 01jan2027 (WP-30, B1)."}}]
        bad_inline = []
        for gid, entry in sorted(gaps2.items()):
            _wp, title, _sha = entry["closed"]
            if not [e for e in fake_entries if e["title"] == title]:
                bad_inline.append(
                    "%s: BUGS.md has no entry titled %r" % (gid, title))
        assert bad_inline == [
            "B1: BUGS.md has no entry titled 'No such title'"]

        bugs_entries, _problems = bugs
        bad = []
        for gid, entry in sorted(docs["gaps2"].items()):
            if entry["closed"] is None:
                continue
            wp, title, sha = entry["closed"]
            match = [e for e in bugs_entries if e["title"] == title]
            if not match:
                bad.append("%s: BUGS.md has no entry titled %r" %
                          (gid, title))
            else:
                e = match[0]
                if not e["closed"]:
                    bad.append("%s: BUGS.md entry %r is not closed" %
                              (gid, title))
                elif "(%s, %s)" % (wp, gid) not in \
                        e["fields"].get("Resolution", ""):
                    bad.append(
                        "%s: BUGS.md entry %r's Resolution lacks (%s, %s)"
                        % (gid, title, wp, gid))
            if re.fullmatch(r"[0-9a-f]{7,40}", sha) and \
                    _git("rev-parse", "--git-dir").returncode == 0:
                if _git("cat-file", "-e", sha + "^{commit}").returncode:
                    bad.append(
                        "%s names commit %s, which git does not have" %
                        (gid, sha))
        assert not bad, "\n".join(bad)

    def test_a_deferred_gaps2_entry_names_its_package_and_a_reason(
            self, docs):
        text_gaps2 = (
            "### B1. Axis labels misread\n\n"
            "- **Tracked:** Deferred (WP-28): out of scope for now.\n\n"
            "### G1. Names collide\n\n"
            "- **Tracked:** Deferred: no package named.\n")
        gaps2, _dupes = _parse_gaps2(text_gaps2)
        bad_inline = []
        for gid, entry in sorted(gaps2.items()):
            tracked = entry["tracked"] or ""
            if tracked.startswith("Deferred") and entry["deferred"] is None:
                bad_inline.append(
                    "%s: %r does not name a package and a reason" %
                    (gid, tracked))
        assert bad_inline == [
            "G1: 'Deferred: no package named.' does not name a package "
            "and a reason"]

        bad = []
        for gid, entry in sorted(docs["gaps2"].items()):
            tracked = entry["tracked"] or ""
            if tracked.startswith("Deferred") and entry["deferred"] is None:
                bad.append(
                    "%s: %r does not name a package and a reason" %
                    (gid, tracked))
            elif entry["deferred"] is not None and \
                    entry["deferred"] not in docs["wps2"]:
                bad.append("%s: deferred by %s, which ROADMAP.md lacks" %
                          (gid, entry["deferred"]))
        assert not bad, "\n".join(bad)

    def test_the_traceability_matrix_heading_appears_once(self):
        roadmap = _read("ROADMAP.md")
        assert roadmap.count("## Traceability matrix") == 1, (
            "the matrix reader splits ROADMAP.md on this exact text once; "
            "a second occurrence anywhere, including inside WP-28, would "
            "move its split point")
        # the GAPS2 reader must not mistake the heading, or anything past
        # it, for a WP section: pins the same hazard for the new field.
        _parse_roadmap_gaps2(roadmap)


# ===========================================================================
# WP-29's P0 entries (item 8 of the module docstring)
# ===========================================================================

#: WP-29 (.ultraplan/wp29/index.md, decision A4): the BUGS.md entries the
#: tracking foundation (S01) opened, one per P0 entry, while they were open.
#: Each fix section closed its entry in place and deleted its key here; the
#: closeout (S15.1) left the allowance empty, and
#: TestWp29Tracking::test_no_wp29_entry_remains_open keeps it so.
WP29_OPEN = {}

#: Every WP-29 P0 entry, permanently, and the CHANGELOG.md lists of the
#: current release its line belongs in (index.md "P0 coverage").  S01 put
#: one ``<!-- WP-29 <id> -->`` marker in each; the closing commit replaces
#: each marker in place with a line ending ``(WP-29, <id>)``.
WP29_LISTS = {
    "P0.1": ("Results that change", "Changed behaviour"),
    "P0.2": ("Results that change",),
    "P0.3": ("Results that change",),
    "P0.4": ("Results that change",),
    "P0.5": ("Results that change", "Changed behaviour"),
    "P0.6": ("Results that change", "Changed behaviour"),
    "P0.7": ("Results that change",),
    "P0.8": ("Results that change",),
    "P0.9": ("Results that change",),
    "P0.10": ("Fixed in WP-29",),
    "P0.11": ("Security",),
    "P0.12a": ("Security", "Changed behaviour"),
    "P0.12b": ("Security",),
    "P0.13": ("Security", "Fixed in WP-29"),
    "P0.14": ("Security",),
    "P0.15": ("Results that change",),
    "P0.16": ("Results that change",),
    "P0.17": ("Fixed in WP-29",),
    "P0.18": ("Results that change",),
    "P0.19": ("Requirements",),
    "P0.20": ("Results that change",),
}

#: The 21 ids, in P0 order.
WP29_ALL = tuple(WP29_LISTS)

_WP29_MARKER = re.compile(r"<!-- WP-29 (P0\.\d{1,2}[ab]?) -->")
_WP29_OPEN_FORM = re.compile(
    r"^  - Resolution: Not fixed because WP-29 section \d{2} has not landed\."
    r" Graded S[12] \(WP-29\): \S")


def _wp29_markers(text):
    """The ids of every ``<!-- WP-29 <id> -->`` marker in *text*, in order,
    repeats kept."""
    return _WP29_MARKER.findall(text)


def _changelog_lists(text):
    """{heading: body} for every ``### `` list of the newest release (the
    first ``## `` section) of a CHANGELOG.md text.  The heading is the text
    after ``### ``; the body runs to the next ``### `` or ``## `` line."""
    releases = re.split(r"^## ", text, flags=re.M)
    if len(releases) < 2:
        return {}
    parts = re.split(r"^### (.+)$", releases[1], flags=re.M)
    return {parts[i].strip(): parts[i + 1] for i in range(1, len(parts), 2)}


def _changelog_list(lists, name):
    """The body of the list *name* names: the heading equal to it, or that
    starts with it and a parenthesis ("Changed behaviour (may need ...)");
    None unless exactly one heading matches."""
    hits = [b for h, b in lists.items()
            if h == name or h.startswith(name + " (")]
    return hits[0] if len(hits) == 1 else None


def _wp29_open_problems(open_map, entries):
    """What is wrong with the allowance *open_map* ({id: title}) against the
    BUGS.md *entries*: an id WP-29 lacks, a title with a double quote or
    shared by two ids, a title no entry or two entries carry, an entry that
    is closed (the allowance is stale), or one not in the WP-29 open form."""
    bad = []
    unknown = sorted(set(open_map) - set(WP29_ALL))
    if unknown:
        bad.append("ids WP-29 does not have: %s" % unknown)
    titles = list(open_map.values())
    if len(set(titles)) != len(titles):
        bad.append("two ids share one title")
    for pid, title in open_map.items():
        if '"' in title:
            bad.append("%s: the title holds a double quote" % pid)
        match = [e for e in entries if e["title"] == title]
        if len(match) != 1:
            bad.append("%s: %d BUGS.md entries are titled %r"
                       % (pid, len(match), title))
            continue
        e = match[0]
        if e["closed"]:
            bad.append("%s: %r is closed; delete its WP29_OPEN key"
                       % (pid, title))
        elif not _WP29_OPEN_FORM.match(e["fields"].get("Resolution", "")):
            bad.append("%s: %r's Resolution is not 'Not fixed because WP-29 "
                       "section NN has not landed. Graded S1|S2 (WP-29): ...'"
                       % (pid, title))
    return bad


def _wp29_marker_problems(open_ids, markers):
    """A marker naming no WP-29 id, and an open id with no marker left."""
    bad = ["a marker names %s, which WP-29 does not have" % m
           for m in sorted(set(markers) - set(WP29_ALL))]
    bad += ["%s is open and CHANGELOG.md holds no marker for it" % pid
            for pid in WP29_ALL if pid in open_ids and pid not in markers]
    return bad


def _wp29_closure_problems(open_ids, markers, entries):
    """A closed id (in WP29_ALL, not open) whose marker is still in the
    CHANGELOG, or whose (WP-29, <id>) no closed entry's Resolution holds."""
    bad = []
    for pid in WP29_ALL:
        if pid in open_ids:
            continue
        if pid in markers:
            bad.append("%s is closed and CHANGELOG.md still holds its "
                       "marker" % pid)
        tag = "(WP-29, %s)" % pid
        if not [e for e in entries if e["closed"]
                and tag in e["fields"].get("Resolution", "")]:
            bad.append("%s is closed and no closed BUGS.md entry's "
                       "Resolution holds %s" % (pid, tag))
    return bad


def _wp29_list_problems(lists_map, changelog):
    """Each id's marker or its (WP-29, <id>) line must sit in every list
    *lists_map* names for it, and its marker nowhere else."""
    lists = _changelog_lists(changelog)
    bad = []
    names = sorted({n for ls in lists_map.values() for n in ls})
    bodies = {n: _changelog_list(lists, n) for n in names}
    for n in names:
        if bodies[n] is None:
            bad.append("CHANGELOG.md has no single '### %s' list" % n)
    for pid, wanted in lists_map.items():
        mark, line = "<!-- WP-29 %s -->" % pid, "(WP-29, %s)" % pid
        for n in wanted:
            body = bodies.get(n)
            if body is not None and mark not in body and line not in body:
                bad.append("%s: '### %s' holds neither its marker nor a line "
                           "ending %s" % (pid, n, line))
        for h, body in lists.items():
            if mark in body and not any(
                    h == n or h.startswith(n + " (") for n in wanted):
                bad.append("%s: its marker sits under '### %s'" % (pid, h))
    return bad


class TestWp29Tracking:
    """WP-29's 21 P0 entries (index.md A4): open in BUGS.md with a marker in
    each CHANGELOG list they belong to until their section lands, then
    closed with no marker left and a Resolution naming (WP-29, <id>)."""

    def test_every_allowed_title_is_an_open_entry(self, bugs):
        entries, _p = bugs
        bad = _wp29_open_problems(WP29_OPEN, entries)
        assert not bad, "\n".join(bad)

    def test_an_open_p0_keeps_its_marker(self):
        bad = _wp29_marker_problems(
            set(WP29_OPEN), _wp29_markers(_read("CHANGELOG.md")))
        assert not bad, "\n".join(bad)

    def test_a_closed_p0_has_no_marker_and_a_resolution(self, bugs):
        entries, _p = bugs
        bad = _wp29_closure_problems(
            set(WP29_OPEN), set(_wp29_markers(_read("CHANGELOG.md"))),
            entries)
        assert not bad, "\n".join(bad)

    def test_each_p0_sits_in_its_changelog_lists(self):
        assert WP29_ALL == tuple(WP29_LISTS) and len(WP29_ALL) == 21
        bad = _wp29_list_problems(WP29_LISTS, _read("CHANGELOG.md"))
        assert not bad, "\n".join(bad)

    def test_the_marker_reader(self):
        text = ("# Changelog\n\n## 1.0, 01jan2027\n\nintro\n\n"
                "### Results that change\n\n- a line. (WP-29, P0.2)\n"
                "<!-- WP-29 P0.1 -->\n\n"
                "### Changed behaviour (may need your do-files changed)\n\n"
                "<!-- WP-29 P0.1 -->\n<!-- WP-29 P0.12a -->\n\n"
                "### Fixed in WP-29\n\n<!-- WP-29 P0.13 -->\n\n"
                "## 0.9, 01jan2026\n\n### Results that change\n\n"
                "<!-- WP-29 P0.99 -->\n")
        assert _wp29_markers(text) == ["P0.1", "P0.1", "P0.12a", "P0.13",
                                       "P0.99"]
        assert _wp29_markers("<!-- WP-28 B1 --> <!-- WP-29 P0.1-->") == []
        lists = _changelog_lists(text)
        assert list(lists) == [
            "Results that change",
            "Changed behaviour (may need your do-files changed)",
            "Fixed in WP-29"]
        assert "P0.99" not in "".join(lists.values())
        assert _changelog_list(lists, "Changed behaviour").startswith(
            "\n\n<!-- WP-29 P0.1 -->")
        assert _changelog_list(lists, "Security") is None
        assert _changelog_lists("no release heading") == {}

    def test_the_wp29_problem_readers(self):
        def entry(title, closed, res):
            return {"title": title, "closed": closed,
                    "fields": {"Resolution": "  - Resolution: " + res}}
        open_form = ("Not fixed because WP-29 section 02 has not landed. "
                     "Graded S1 (WP-29): wrong path.")
        good = [entry("T1", False, open_form),
                entry("T2", True, "Fixed 01oct2026 (WP-29, P0.2). Done.")]
        assert _wp29_open_problems({"P0.1": "T1"}, good) == []
        for open_map, entries, says in (
                ({"P0.1": "T2"}, good, "is closed"),
                ({"P0.1": "T9"}, good, "0 BUGS.md entries"),
                ({"P0.1": "T1"}, good + [entry("T1", False, open_form)],
                 "2 BUGS.md entries"),
                ({"P0.1": "T1"},
                 [entry("T1", False, "Not fixed because x. Graded S3 "
                        "(WP-27): y.")], "not 'Not fixed because WP-29"),
                ({"P0.99": "T1"}, good, "does not have"),
                ({"P0.1": 'a "q"'}, [entry('a "q"', False, open_form)],
                 "double quote"),
                ({"P0.1": "T1", "P0.3": "T1"}, good, "share one title")):
            bad = _wp29_open_problems(open_map, entries)
            assert any(says in b for b in bad), (says, bad)

        assert _wp29_marker_problems({"P0.1"}, ["P0.1"]) == []
        assert _wp29_marker_problems({"P0.1"}, []) == [
            "P0.1 is open and CHANGELOG.md holds no marker for it"]
        assert _wp29_marker_problems(set(), ["P0.12"]) == [
            "a marker names P0.12, which WP-29 does not have"]

        others = set(WP29_ALL) - {"P0.2"}
        assert _wp29_closure_problems(others, others, good) == []
        assert _wp29_closure_problems(others, others | {"P0.2"}, good) == [
            "P0.2 is closed and CHANGELOG.md still holds its marker"]
        assert _wp29_closure_problems(others, others, good[:1]) == [
            "P0.2 is closed and no closed BUGS.md entry's Resolution "
            "holds (WP-29, P0.2)"]
        # (WP-29, P0.1) is not read inside (WP-29, P0.12a) or (WP-29, P0.10)
        near = [entry("T3", True, "Fixed (WP-29, P0.12a). (WP-29, P0.10).")]
        assert _wp29_closure_problems(set(WP29_ALL) - {"P0.1"}, set(),
                                      near) == [
            "P0.1 is closed and no closed BUGS.md entry's Resolution "
            "holds (WP-29, P0.1)"]

        log = ("## 1.0\n\n### Results that change\n\n<!-- WP-29 P0.1 -->\n"
               "### Changed behaviour (may need your do-files changed)\n\n"
               "- a line. (WP-29, P0.1)\n### Security\n\n"
               "<!-- WP-29 P0.11 -->\n")
        rules = {"P0.1": ("Results that change", "Changed behaviour"),
                 "P0.11": ("Security",)}
        assert _wp29_list_problems(rules, log) == []
        assert _wp29_list_problems(
            {"P0.1": ("Results that change", "Changed behaviour"),
             "P0.11": ("Results that change",)}, log) == [
            "P0.11: '### Results that change' holds neither its marker nor "
            "a line ending (WP-29, P0.11)",
            "P0.11: its marker sits under '### Security'"]
        assert _wp29_list_problems({"P0.10": ("Fixed in WP-29",)}, log) == [
            "CHANGELOG.md has no single '### Fixed in WP-29' list"]

    def test_no_wp29_entry_remains_open(self, bugs):
        # WP-29's closeout (S15.1): every P0 entry is closed, the allowance
        # is empty and no marker is left, so the release guard exempts
        # nothing and each id's (WP-29, <id>) sits in a closed entry.
        # Reopening an entry, putting a key back or re-adding a marker
        # fails here.
        entries, _p = bugs
        assert WP29_OPEN == {}, (
            "WP29_OPEN is {} after WP-29's closeout; it holds %s"
            % sorted(WP29_OPEN))
        markers = _wp29_markers(_read("CHANGELOG.md"))
        assert not markers, (
            "markers left in CHANGELOG.md: %s" % markers)
        bad = _wp29_closure_problems(set(), set(markers), entries)
        bad += ["%r is open in the WP-29 form" % e["title"]
                for e in entries if not e["closed"]
                and _WP29_OPEN_FORM.match(e["fields"].get("Resolution", ""))]
        assert not bad, "\n".join(bad)


# ===========================================================================
# WP-30's P1 entries (item 9 of the module docstring)
# ===========================================================================

#: WP-30 (.ultraplan/wp30/index.md, decision A144): the BUGS.md entries the
#: tracking foundation (S01) opened, one per P1 entry, while they were open.
#: Each fix section closed its entry in place and deleted its key here; the
#: closeout (S58.1) left the allowance empty, and
#: TestWp30Tracking::test_no_wp30_entry_remains_open keeps it so.
WP30_OPEN = {}

#: Every WP-30 entry, permanently, and the CHANGELOG.md lists of the current
#: release its line belongs in (index.md "P1 coverage").  S01 put one
#: ``<!-- WP-30 <id> -->`` marker in each; the closing commit replaces each
#: marker in place with a line ending ``(WP-30, <id>)``.  A section that
#: needs another list edits its own row and its own markers in the same
#: commit (index.md R4).
WP30_LISTS = {
    "P1.1a": ("Results that change", "Changed behaviour"),
    "P1.1b": ("Results that change", "Changed behaviour", "Fixed in WP-30"),
    "P1.2a": ("Results that change",),
    "P1.2b": ("Results that change",),
    "P1.3a": ("Results that change",),
    "P1.3b": ("Results that change",),
    "P1.4a": ("Results that change",),
    "P1.4b": ("Results that change",),
    "P1.5": ("Results that change", "Changed behaviour"),
    "P1.6": ("New", "Changed behaviour"),
    "P1.7": ("New", "Changed behaviour"),
    "P1.8a": ("Results that change", "Changed behaviour"),
    "P1.8b": ("Results that change", "Changed behaviour"),
    "P1.9a": ("Results that change", "Changed behaviour"),
    "P1.9b": ("Fixed in WP-30",),
    "P1.10": ("New", "Changed behaviour"),
    "P1.11a": ("Security", "Results that change"),
    "P1.11b": ("Results that change",),
    "P1.12a": ("Results that change", "Changed behaviour"),
    "P1.12b": ("Results that change", "Changed behaviour"),
    "P1.13a": ("Results that change", "Changed behaviour"),
    "P1.13b": ("Results that change",),
    "P1.14a": ("Results that change",),
    "P1.14b": ("Results that change",),
    "P1.15a": ("Results that change",),
    "P1.15b": ("Results that change", "Changed behaviour"),
    "P1.15c": ("Results that change",),
    "P1.16": ("Results that change",),
    "P1.17a": ("Results that change", "Changed behaviour"),
    "P1.17b": ("Results that change",),
    "P1.18a": ("Results that change", "Changed behaviour"),
    "P1.18b": ("Results that change",),
    "P1.19": ("Changed behaviour", "Fixed in WP-30"),
    "P1.20a": ("Results that change", "Changed behaviour"),
    "P1.20b": ("Results that change",),
    "P1.21a": ("Results that change", "Changed behaviour"),
    "P1.21b": ("Results that change",),
    "P1.22": ("Fixed in WP-30",),
    "P1.23a": ("Results that change",),
    "P1.23b": ("Results that change",),
    "P1.24": ("Fixed in WP-30", "Changed behaviour"),
    "P1.25a": ("New",),
    "P1.25b": ("Results that change", "Security", "Changed behaviour"),
    "P1.26a": ("Changed behaviour", "Fixed in WP-30"),
    "P1.26b": ("Changed behaviour", "Fixed in WP-30"),
    "P1.27": ("Changed behaviour", "Fixed in WP-30"),
    "P1.28a": ("New", "Changed behaviour"),
    "P1.28b": ("New",),
    "P1.29": ("Security",),
    "P1.30": ("Requirements", "Security"),
    "P1.31a": ("New", "Security"),
    "P1.31b": ("Fixed in WP-30",),
    "P1.32": ("Requirements",),
    "P1.33": ("Requirements",),
    "P1.34": ("Fixed in WP-30",),
    "P1.35": ("Requirements", "Changed behaviour"),
}

#: The section that closes each entry (index.md "Section manifest"); an open
#: entry's Resolution names it.  Permanent.
WP30_SECTION = {
    "P1.1a": 11,
    "P1.1b": 20,
    "P1.2a": 15,
    "P1.2b": 16,
    "P1.3a": 21,
    "P1.3b": 44,
    "P1.4a": 24,
    "P1.4b": 33,
    "P1.5": 18,
    "P1.6": 51,
    "P1.7": 42,
    "P1.8a": 40,
    "P1.8b": 45,
    "P1.9a": 49,
    "P1.9b": 55,
    "P1.10": 56,
    "P1.11a": 9,
    "P1.11b": 29,
    "P1.12a": 8,
    "P1.12b": 13,
    "P1.13a": 30,
    "P1.13b": 43,
    "P1.14a": 32,
    "P1.14b": 36,
    "P1.15a": 28,
    "P1.15b": 48,
    "P1.15c": 53,
    "P1.16": 19,
    "P1.17a": 14,
    "P1.17b": 27,
    "P1.18a": 31,
    "P1.18b": 52,
    "P1.19": 10,
    "P1.20a": 38,
    "P1.20b": 47,
    "P1.21a": 39,
    "P1.21b": 50,
    "P1.22": 26,
    "P1.23a": 35,
    "P1.23b": 17,
    "P1.24": 37,
    "P1.25a": 7,
    "P1.25b": 34,
    "P1.26a": 6,
    "P1.26b": 23,
    "P1.27": 12,
    "P1.28a": 22,
    "P1.28b": 54,
    "P1.29": 4,
    "P1.30": 41,
    "P1.31a": 46,
    "P1.31b": 57,
    "P1.32": 25,
    "P1.33": 5,
    "P1.34": 2,
    "P1.35": 3,
}

#: The 56 ids, in entry order.
WP30_ALL = tuple(WP30_LISTS)

_WP30_MARKER = re.compile(r"<!-- WP-30 (P1\.\d{1,2}[abc]?) -->")
_WP30_OPEN_FORM = re.compile(
    r"^  - Resolution: Not fixed because WP-30 section (\d{2}) has not landed\."
    r" Graded S[1-3] \(WP-30\): \S")


def _wp30_markers(text):
    """The ids of every ``<!-- WP-30 <id> -->`` marker in *text*, in order,
    repeats kept."""
    return _WP30_MARKER.findall(text)


def _wp30_open_problems(open_map, entries):
    """What is wrong with the allowance *open_map* ({id: title}) against the
    BUGS.md *entries*: an id WP-30 lacks, a title with a double quote or
    shared by two ids, a title no entry or two entries carry, an entry that
    is closed (the allowance is stale), one not in the WP-30 open form, or
    one whose Resolution names another section than WP30_SECTION's."""
    bad = []
    unknown = sorted(set(open_map) - set(WP30_ALL))
    if unknown:
        bad.append("ids WP-30 does not have: %s" % unknown)
    titles = list(open_map.values())
    if len(set(titles)) != len(titles):
        bad.append("two ids share one title")
    for pid, title in open_map.items():
        if '"' in title:
            bad.append("%s: the title holds a double quote" % pid)
        match = [e for e in entries if e["title"] == title]
        if len(match) != 1:
            bad.append("%s: %d BUGS.md entries are titled %r"
                       % (pid, len(match), title))
            continue
        e = match[0]
        if e["closed"]:
            bad.append("%s: %r is closed; delete its WP30_OPEN key"
                       % (pid, title))
            continue
        form = _WP30_OPEN_FORM.match(e["fields"].get("Resolution", ""))
        if not form:
            bad.append("%s: %r's Resolution is not 'Not fixed because WP-30 "
                       "section NN has not landed. Graded S1|S2|S3 (WP-30): "
                       "...'" % (pid, title))
        elif int(form.group(1)) != WP30_SECTION.get(pid):
            bad.append("%s: its Resolution names section %s, not %s"
                       % (pid, form.group(1), WP30_SECTION.get(pid)))
    return bad


def _wp30_marker_problems(open_ids, markers):
    """A marker naming no WP-30 id, and an open id with no marker left."""
    bad = ["a marker names %s, which WP-30 does not have" % m
           for m in sorted(set(markers) - set(WP30_ALL))]
    bad += ["%s is open and CHANGELOG.md holds no marker for it" % pid
            for pid in WP30_ALL if pid in open_ids and pid not in markers]
    return bad


def _wp30_closure_problems(open_ids, markers, entries):
    """A closed id (in WP30_ALL, not open) whose marker is still in the
    CHANGELOG, or whose (WP-30, <id>) no closed entry's Resolution holds."""
    bad = []
    for pid in WP30_ALL:
        if pid in open_ids:
            continue
        if pid in markers:
            bad.append("%s is closed and CHANGELOG.md still holds its "
                       "marker" % pid)
        tag = "(WP-30, %s)" % pid
        if not [e for e in entries if e["closed"]
                and tag in e["fields"].get("Resolution", "")]:
            bad.append("%s is closed and no closed BUGS.md entry's "
                       "Resolution holds %s" % (pid, tag))
    return bad


def _wp30_list_problems(lists_map, changelog):
    """Each id's marker or its (WP-30, <id>) line must sit in every list
    *lists_map* names for it, and neither its marker nor such a line
    anywhere else (a section that needs another list widens its own row
    first, index.md R4)."""
    lists = _changelog_lists(changelog)
    bad = []
    names = sorted({n for ls in lists_map.values() for n in ls})
    bodies = {n: _changelog_list(lists, n) for n in names}
    for n in names:
        if bodies[n] is None:
            bad.append("CHANGELOG.md has no single '### %s' list" % n)
    for pid, wanted in lists_map.items():
        mark, line = "<!-- WP-30 %s -->" % pid, "(WP-30, %s)" % pid
        for n in wanted:
            body = bodies.get(n)
            if body is not None and mark not in body and line not in body:
                bad.append("%s: '### %s' holds neither its marker nor a line "
                           "ending %s" % (pid, n, line))
        for h, body in lists.items():
            if any(h == n or h.startswith(n + " (") for n in wanted):
                continue
            if mark in body:
                bad.append("%s: its marker sits under '### %s'" % (pid, h))
            if line in body:
                bad.append("%s: a line ending %s sits under '### %s'"
                           % (pid, line, h))
    return bad


class TestWp30Tracking:
    """WP-30's 56 P1 entries (index.md A144): open in BUGS.md, naming their
    section, with a marker in each CHANGELOG list they belong to until their
    section lands, then closed with no marker left and a Resolution naming
    (WP-30, <id>)."""

    def test_every_allowed_title_is_an_open_entry(self, bugs):
        entries, _p = bugs
        bad = _wp30_open_problems(WP30_OPEN, entries)
        assert not bad, "\n".join(bad)

    def test_an_open_p1_keeps_its_marker(self):
        bad = _wp30_marker_problems(
            set(WP30_OPEN), _wp30_markers(_read("CHANGELOG.md")))
        assert not bad, "\n".join(bad)

    def test_a_closed_p1_has_no_marker_and_a_resolution(self, bugs):
        entries, _p = bugs
        bad = _wp30_closure_problems(
            set(WP30_OPEN), set(_wp30_markers(_read("CHANGELOG.md"))),
            entries)
        assert not bad, "\n".join(bad)

    def test_each_p1_sits_in_its_changelog_lists(self):
        assert WP30_ALL == tuple(WP30_LISTS) and len(WP30_ALL) == 56
        assert tuple(WP30_SECTION) == WP30_ALL
        assert sorted(WP30_SECTION.values()) == list(range(2, 58))
        bad = _wp30_list_problems(WP30_LISTS, _read("CHANGELOG.md"))
        assert not bad, "\n".join(bad)

    def test_the_marker_reader(self):
        text = ("# Changelog\n\n## 1.0, 01jan2027\n\nintro\n\n"
                "### Results that change\n\n- a line. (WP-30, P1.2a)\n"
                "<!-- WP-30 P1.1a -->\n\n"
                "### Changed behaviour (may need your do-files changed)\n\n"
                "<!-- WP-30 P1.1a -->\n<!-- WP-30 P1.15c -->\n\n"
                "### Fixed in WP-30\n\n<!-- WP-30 P1.19 -->\n\n"
                "## 0.9, 01jan2026\n\n### Results that change\n\n"
                "<!-- WP-30 P1.99 -->\n")
        assert _wp30_markers(text) == ["P1.1a", "P1.1a", "P1.15c", "P1.19",
                                       "P1.99"]
        assert _wp30_markers("<!-- WP-29 P0.1 --> <!-- WP-30 P1.1a-->"
                             " <!-- WP-30 P1.1d -->") == []
        lists = _changelog_lists(text)
        assert list(lists) == [
            "Results that change",
            "Changed behaviour (may need your do-files changed)",
            "Fixed in WP-30"]
        assert "P1.99" not in "".join(lists.values())
        assert _changelog_list(lists, "Changed behaviour").startswith(
            "\n\n<!-- WP-30 P1.1a -->")
        assert _changelog_list(lists, "Security") is None

    def test_the_wp30_problem_readers(self):
        def entry(title, closed, res):
            return {"title": title, "closed": closed,
                    "fields": {"Resolution": "  - Resolution: " + res}}
        open_form = ("Not fixed because WP-30 section 11 has not landed. "
                     "Graded S2 (WP-30): wrong style.")
        good = [entry("T1", False, open_form),
                entry("T2", True, "Fixed 01nov2026 (WP-30, P1.2a). Done.")]
        assert _wp30_open_problems({"P1.1a": "T1"}, good) == []
        for open_map, entries, says in (
                ({"P1.1a": "T2"}, good, "is closed"),
                ({"P1.1a": "T9"}, good, "0 BUGS.md entries"),
                ({"P1.1a": "T1"}, good + [entry("T1", False, open_form)],
                 "2 BUGS.md entries"),
                ({"P1.1a": "T1"},
                 [entry("T1", False, "Not fixed because x. Graded S3 "
                        "(WP-27): y.")], "not 'Not fixed because WP-30"),
                ({"P1.1a": "T1"},
                 [entry("T1", False, open_form.replace("11", "12"))],
                 "names section 12, not 11"),
                ({"P1.99": "T1"}, good, "does not have"),
                ({"P1.1a": 'a "q"'}, [entry('a "q"', False, open_form)],
                 "double quote"),
                ({"P1.1a": "T1", "P1.1b": "T1"}, good, "share one title")):
            bad = _wp30_open_problems(open_map, entries)
            assert any(says in b for b in bad), (says, bad)

        assert _wp30_marker_problems({"P1.1a"}, ["P1.1a"]) == []
        assert _wp30_marker_problems({"P1.1a"}, []) == [
            "P1.1a is open and CHANGELOG.md holds no marker for it"]
        assert _wp30_marker_problems(set(), ["P1.1"]) == [
            "a marker names P1.1, which WP-30 does not have"]

        others = set(WP30_ALL) - {"P1.2a"}
        assert _wp30_closure_problems(others, others, good) == []
        assert _wp30_closure_problems(others, others | {"P1.2a"}, good) == [
            "P1.2a is closed and CHANGELOG.md still holds its marker"]
        assert _wp30_closure_problems(others, others, good[:1]) == [
            "P1.2a is closed and no closed BUGS.md entry's Resolution "
            "holds (WP-30, P1.2a)"]
        # (WP-30, P1.1a) is not read inside (WP-30, P1.11a) or (WP-30, P1.1b)
        near = [entry("T3", True, "Fixed (WP-30, P1.11a). (WP-30, P1.1b).")]
        assert _wp30_closure_problems(set(WP30_ALL) - {"P1.1a"}, set(),
                                      near) == [
            "P1.1a is closed and no closed BUGS.md entry's Resolution "
            "holds (WP-30, P1.1a)"]

        log = ("## 1.0\n\n### Results that change\n\n<!-- WP-30 P1.1a -->\n"
               "### Changed behaviour (may need your do-files changed)\n\n"
               "- a line. (WP-30, P1.1a)\n### Security\n\n"
               "<!-- WP-30 P1.29 -->\n")
        rules = {"P1.1a": ("Results that change", "Changed behaviour"),
                 "P1.29": ("Security",)}
        assert _wp30_list_problems(rules, log) == []
        assert _wp30_list_problems(
            {"P1.1a": ("Results that change", "Changed behaviour"),
             "P1.29": ("Results that change",)}, log) == [
            "P1.29: '### Results that change' holds neither its marker nor "
            "a line ending (WP-30, P1.29)",
            "P1.29: its marker sits under '### Security'"]
        # a closing line in a list its row does not name (R4 not followed)
        assert _wp30_list_problems(rules, log + "- x. (WP-30, P1.1a)\n") == [
            "P1.1a: a line ending (WP-30, P1.1a) sits under '### Security'"]
        assert _wp30_list_problems({"P1.19": ("Fixed in WP-30",)}, log) == [
            "CHANGELOG.md has no single '### Fixed in WP-30' list"]

    def test_no_wp30_entry_remains_open(self, bugs):
        # WP-30's closeout (S58.1): every P1 entry is closed, the allowance
        # is empty and no marker is left, so the release guard exempts
        # nothing and each id's (WP-30, <id>) sits in a closed entry.
        # Reopening an entry, putting a key back or re-adding a marker
        # fails here.
        entries, _p = bugs
        assert WP30_OPEN == {}, (
            "WP30_OPEN is {} after WP-30's closeout; it holds %s"
            % sorted(WP30_OPEN))
        markers = _wp30_markers(_read("CHANGELOG.md"))
        assert not markers, (
            "markers left in CHANGELOG.md: %s" % markers)
        bad = _wp30_closure_problems(set(), set(markers), entries)
        bad += ["%r is open in the WP-30 form" % e["title"]
                for e in entries if not e["closed"]
                and _WP30_OPEN_FORM.match(e["fields"].get("Resolution", ""))]
        assert not bad, "\n".join(bad)


# ===========================================================================
# WP-31's entries (item 10 of the module docstring)
# ===========================================================================

#: WP-31 (.ultraplan/sections/index.md A4): the BUGS.md entries S01 opened,
#: one per manifest row id, by id, with their exact titles, one key per line
#: in Appendix A order.  A section's closing commit closes the entry in place
#: and deletes its own key line.  S61 leaves it {}.
WP31_OPEN = {
    "B4a": "contour and contourline are refused by name (the interpolation, grid rule, cap and truth extractor)",
    "D1": "xmtick, ymtick, xmlabel, ymlabel, tmtick and tmlabel and their *2 forms are pending and never read",
    "F1f": "The saved page does not refit mband and mspline after a filter move (the mband and mspline twins)",
    "B4b": "contour and contourline are refused by name (the type registration, options, colour rules, colour key and both modes)",
    "D2": "t1title to r2title are pending and title2 and subtitle2 are named where twoway refuses them",
    "F1g": "The saved page does not refit fpfit and fpfitci after a filter move (the fpfit and fpfitci twins)",
    "B4c": "contour and contourline are refused by name (the JavaScript twin)",
    "D3": "Textbox sub-options on titles are named and _dash_textbox_place is wired to scheme clocks only",
    "D13": "Added text ignores tstyle() and the textbox sub-options and does not expand a global macro in a drawn label",
    "D4": "Legend geometry sub-options are named, corner clocks are centred, pos(0) and ring(0) land at Bokeh's top_right, label(#) with no text is dropped, and identical keys are not merged",
    "C13": "A histogram-only graph draws a legend where twoway draws none",
    "D5": "scale(), fxsize(), fysize() and the overhangs are never read, and aspectratio() shapes the figure, loses to xsize/ysize and refuses placement()",
    "E11": "Sizes are relative to a 4-inch reference and scale() is pending",
    "D6": "Axis label and tick style sub-options are named, ##5 is read as #5, and label forms twoway refuses are drawn",
    "D7": "Axis-scale look options fill, outergap(), extend, fextend and lstyle are named and two yscale(alt) do not toggle back",
    "E6": "Line-width *# multiplies before the 0.3 pt floor and tlwidth() and glwidth() are named not drawn",
    "D8": "yvarlabel() and xvarlabel() are undeclared, noted and absent from the help",
    "C17": "mlabprefix(), mlabsuffix() and plot-level lalign() are undeclared and headlabel is accepted on types twoway may not take it on",
    "E3": "msangle(anglestyle name) is drawn at 0 degrees and mlalign(), mwidth and mlabstyle() are undeclared",
    "C14": "rscatter y y2 x, mlabel(y) draws where twoway refuses r(102)",
    "C15": "Bar marker labels default to 3 o'clock where twoway's bar default is 12",
    "D9": "The y2 and x2 range is built once and never follows a filter move, the first-used axis is not drawn left or bottom, and horizontal with yaxis(2) titles no x axis",
    "D10": "by() sub-options of its stage-3 grammar are named, overall legend placement and interaction differ, panel margins ignore iscale(), and panels emptied by a filter stay drawn",
    "D11": "graphregion margins are inexact, the intensity and shade options are named, several marginstyle forms are not parsed, and s1color's unfilled plot region is filled white",
    "D12": "An out-of-range xline() or yline() is clipped to the frame where twoway draws it outside",
    "D14": "tabs() drops unregistered names silently, the served layout() overwrites a cell silently, and there is no per-tab layout()",
    "D16": "legend(po(9) top) names top first, title(T, prefix suffix) prints no ignored line, and values nested in legend(region()) are unchecked",
    "E1": "Marker symbols arrow, arrowf, A, a and pipe are refused, pipe is horizontal, point is 8 px, V is filled, shorthands are full size and non-Stata names are accepted",
    "E2": "Line-pattern formula strings are refused, named pattern geometry differs from Stata's and mlpattern() is pending",
    "E12": "translate_msymbol and translate_lpattern lower-case names where Stata style names are case-sensitive",
    "E4": "Glued = stylelist forms and a parenthesised element reach the renderer as one unknown element",
    "E5": "A comma colour inside a structured sub-option is drawn black where twoway refuses r(198)",
    "E7": "A pstyle(p#) CI band under a scheme intensity above full is clamped to full",
    "E8": "rarea and rbar outlines are not stroked where twoway strokes them from the scheme",
    "E13": "_SIZE_MAP and _GSIZE_NUMERIC_PT_PER_UNIT are dead but kept and serialised, and histogram scheme opacity is unverified",
    "E9": "Inline SMCL style runs and raised text with no Unicode form are drawn in the text's own style, and hline, space, dup, cmd, hi, ccl, center and links are drawn as typed",
    "G1": "Extended missing .a to .z are merged into one null in by(, missing) panels, marker labels, filters and tooltips",
    "G2": "set dp comma is never read, %tC is converted without leap seconds and graph set font faces are not read",
    "G3": "Working columns are generated in the user's data, user variables named x, y, top, count or density are shadowed in hover() and mlabel(), numbers are embedded as JSON text and the cell count counts every exported row",
    "G4": "Carried hover, mlabel and row-id columns are upcast to object and handed to Bokeh as Python lists",
    "G5": "One format-writer model is emitted per distinct tick format and per tooltip kind",
    "E10": "User and third-party style files are not read, 57 Stata style names draw default attributes with a note, and a scheme cannot redefine a linestyle or areastyle",
    "D15": "Date #N ticks agree with _tsnatscale on 52 to 98 percent of ranges, xtick(#N) and xlabel(minmax) are held after a move, and the margin is a build-time fraction",
    "C11": "lpoly edge cases: tiny gaussian weights counted toward the two-observation rule, round-off cases, pwidth(0) and pwidth(+800) rc differences, and an empty line under a five-row if",
    "C12": "function under by() is evaluated once where twoway evaluates once per panel, and a malformed y form is echoed as typed",
    "C16": "A recast kdensity or histogram is marked stale after a move where the un-recast one is recounted",
    "G6": "Fractional %t values are floored on load and join-order edge cases differ",
    "G7": "%d and %tb axis formats are drawn %9.0g with a note and xvarformat(bogus) is noted where twoway refuses",
    "F5": "The map_qfitci docstring, the module header and the _dash_fold_typed comment describe code that no longer exists",
    "F2": "The function points-free fallback evaluates ten math names only",
    "F3": "Stata ground truth is missing for weighted qfitci and fpfitci bands, stdf and stdr under fw, the six kernels on lpolyci, pattern lengths and on-edge values",
    "H2t": "No per-graph data table shows the rows a graph draws (the data table)",
    "H2f": "Filters lack a multi-select dropdown, a (missing) option, a slider direction and a reset button (the filter widgets)",
    "H2k": "KPI cards take no weights and lack kurtosis, semean and range (the KPI statistics)",
    "H2l": "One link group only, brush cannot act as a filter, a brush on bars or histograms drives nothing and concurrent brushes are not intersected (the link groups and brush)",
    "H1": "Saved-page JavaScript errors fail silently and saved sliders fire on every drag step",
    "H2x": "No print stylesheet, and PNG and SVG export omit KPI cards, title, filters and the tab strip (the export and print parts)",
    "K6": "One aria-live region, no alt text and English-only interface",
    "H3": "The served make_document builds on the event loop, catch_warnings can swap filters, a brush made during a move is cleared, and the bundle ships bokeh-mathjax",
    "H4": "BOKEH_RESOURCES=cdn blanks the served page silently, BOKEH_MINIFIED and BOKEH_DEV change the saved page silently, /health reports only ok, and the browser-launch return code is never read",
    "H7": "Four unprefixed Mata functions are dropped by name on repair, sys.argv is overwritten and not restored, and three names are left in __main__",
    "J1": "The help says every supplied option is named in the note and its Unsupported section omits every name that reaches the generic note",
    "J2": "Help inconsistencies in the syntax line, the period-slider sentence, legend(ring(0)), msangle, the Not-drawn count, dot, the refusal-log claim and missing paragraphs",
    "J3": "Ten plot types, dash serve, weights and csv appear in no example, the feature_tour header is stale and no coverage test exists",
    "J4": "Stale tracking text in GAPS.md, ROADMAP.md, BUGS.md, DROPIN, TWOWAY_COVERAGE_AUDIT.md and several test docstrings",
    "J5": "The served app's header says Launch with bokeh serve, ServerAppBuilder docstrings are stale, title_safe is dead and _SIZE_MAP is emitted",
    "J6": "REMAINING.md and phases/ are superseded but in the tree with PARTIAL markers, and ROADMAP WP-01 to WP-11 headings lack the DONE suffix",
    "I2": "No README, dash.pkg has no Author or KW lines, no net install instruction in the help, the Author section is titled Also see, and the Jump To list is short",
    "I3": "A failed dash_setup leaves installed packages in place and does not say what it installed, the served child is sys.executable, Unmet lists warnings beside a failure, and a dash_setup_lib.py in the working directory is found first",
    "I4": "_dash_dep_versions() is printed nowhere but through Stata, so a hand-run renderer or app is silent, and Python below 3.7 dies at the parser",
    "I5": "Version headers disagree (dash_render.py 1.0.0 25mar2026, dash.ado and dash_parse.mata v2.0) and the pin reads only the Version lines",
    "I7": "The renderer bytecode is still cached under PLUS/py and ado uninstall leaves __pycache__ behind",
    "K2": "Stata end-to-end gaps: served layer-output assertions, computed layers on %t variables served, the serve start line, a served build from an installed tree, per-type by() parity, an inspect.getsource fallback",
    "K3": "Sixteen truth fixtures have no committed generator, nine carry absolute paths, there is no make truth and no metadata guard",
    "K4": "The server fixture leaks a process when __enter__ fails, no AST count of the app's dispatch, hand-written scheme-key enumeration, no CSS-guard served arm, two strict xfails",
    "H6": "The parity guard compares only glyphs, labels, arrowheads and KPI cards after a move and its oracle is the saved renderer, not the saved page's JS",
    "I6": "No secret scan, CI, ruff, pyflakes or bandit, the hooks CLAUDE.md relies on are git-ignored, and *.log is excluded only locally",
    # Batch 1-4 gap additions (DECISIONS D14, 14oct2026)
    "A3b": "The *2title options and name() take spellings shorter than twoway's minimum (b, l, r, t and nam)",
    "A3c": "aspectratio() takes asp, shorter than twoway's minimum",
    "C10d": "kdensity range() naming a string or all-missing variable draws over the data's span where twoway draws an empty curve",
    "C10e": "Axes 3 to 9 on a date variable are labelled in Stata numbers, and t-options with axis(3) to axis(9) are left as typed",
    "C18b": "An immediate coordinate written as a hexadecimal literal such as 1.0X+3ff is refused where twoway takes it",
    "C4b": "fitplot() and ciplot() lines and bands are drawn in the layer's own colour with twoway's colours for those views unmeasured",
    "C6b": "mband and mspline over data with missing y draw fewer vertices than twoway",
    "C8c": "A user-supplied scheme's colorvar() default colour rule falls back to s2color's",
    "C8d": "pcycle() refuses a fraction where twoway draws it on a graph of few series",
    "C8e": "colorkeysreverse on a colorvar() colour bar is named, not drawn",
    "B5c": "dot rows on the saved page keep the build's axis span after a filter move",
}

#: Every WP-31 entry, permanently, and the CHANGELOG.md lists of the current
#: release its line belongs in (section-01 Appendix A).
WP31_LISTS = {
    "C1": ("Results that change",),
    "C2": ("Results that change",),
    "B5a": ("Results that change",),
    "C3": ("Changed behaviour",),
    "C10a": ("Fixed in WP-31",),
    "C10b": ("Fixed in WP-31",),
    "C18": ("Fixed in WP-31",),
    "F4": ("Fixed in WP-31",),
    "A5": ("Fixed in WP-31",),
    "A6": ("Fixed in WP-31", "Changed behaviour",),
    "A7": ("Results that change",),
    "A8": ("Changed behaviour",),
    "A1": ("Fixed in WP-31",),
    "A2": ("Changed behaviour",),
    "A3": ("Fixed in WP-31",),
    "A4": ("Changed behaviour",),
    "C10c": ("Fixed in WP-31",),
    "F1a": ("Results that change",),
    "C4": ("Results that change",),
    "C5": ("Results that change",),
    "F1b": ("Results that change",),
    "C6": ("Results that change",),
    "C7": ("Results that change",),
    "C8a": ("Results that change",),
    "F1c": ("Results that change",),
    "C8b": ("Results that change",),
    "B5b": ("Results that change",),
    "F1d": ("Results that change",),
    "C9": ("Results that change",),
    "B1": ("Fixed in WP-31",),
    "B2": ("Fixed in WP-31",),
    "B3": ("Fixed in WP-31",),
    "F1e": ("Results that change",),
    "B4a": ("Fixed in WP-31",),
    "D1": ("Results that change",),
    "F1f": ("Results that change",),
    "B4b": ("Fixed in WP-31",),
    "D2": ("Results that change", "Changed behaviour",),
    "F1g": ("Results that change",),
    "B4c": ("Fixed in WP-31",),
    "D3": ("Results that change",),
    "D13": ("Results that change",),
    "D4": ("Results that change",),
    "C13": ("Results that change",),
    "D5": ("Results that change",),
    "E11": ("Results that change",),
    "D6": ("Results that change", "Changed behaviour",),
    "D7": ("Results that change",),
    "E6": ("Results that change",),
    "D8": ("Results that change",),
    "C17": ("Results that change",),
    "E3": ("Results that change",),
    "C14": ("Changed behaviour",),
    "C15": ("Results that change",),
    "D9": ("Results that change",),
    "D10": ("Results that change",),
    "D11": ("Results that change",),
    "D12": ("Results that change",),
    "D14": ("Changed behaviour", "Fixed in WP-31",),
    "D16": ("Changed behaviour", "Fixed in WP-31",),
    "E1": ("Results that change", "Changed behaviour",),
    "E2": ("Results that change",),
    "E12": ("Changed behaviour",),
    "E4": ("Changed behaviour",),
    "E5": ("Results that change", "Changed behaviour",),
    "E7": ("Results that change",),
    "E8": ("Results that change",),
    "E13": ("Fixed in WP-31",),
    "E9": ("Results that change",),
    "G1": ("Results that change",),
    "G2": ("Results that change",),
    "G3": ("Fixed in WP-31",),
    "G4": ("Fixed in WP-31",),
    "G5": ("Fixed in WP-31",),
    "E10": ("Results that change",),
    "D15": ("Results that change",),
    "C11": ("Results that change",),
    "C12": ("Results that change",),
    "C16": ("Fixed in WP-31",),
    "G6": ("Results that change",),
    "G7": ("Results that change", "Changed behaviour",),
    "F5": ("Fixed in WP-31",),
    "F2": ("Results that change",),
    "F3": ("Fixed in WP-31",),
    "H2t": ("Fixed in WP-31",),
    "H2f": ("Fixed in WP-31",),
    "H2k": ("Fixed in WP-31",),
    "H2l": ("Fixed in WP-31",),
    "H1": ("Fixed in WP-31",),
    "H2x": ("Fixed in WP-31",),
    "K6": ("Fixed in WP-31",),
    "H3": ("Fixed in WP-31",),
    "H4": ("Changed behaviour",),
    "H7": ("Fixed in WP-31",),
    "J1": ("Fixed in WP-31",),
    "J2": ("Fixed in WP-31",),
    "J3": ("Fixed in WP-31",),
    "J4": ("Fixed in WP-31",),
    "J5": ("Fixed in WP-31",),
    "J6": ("Fixed in WP-31",),
    "I2": ("Fixed in WP-31",),
    "I3": ("Fixed in WP-31",),
    "I4": ("Fixed in WP-31",),
    "I5": ("Fixed in WP-31",),
    "I7": ("Fixed in WP-31",),
    "K2": ("Fixed in WP-31",),
    "K3": ("Fixed in WP-31",),
    "K4": ("Fixed in WP-31",),
    "H6": ("Fixed in WP-31",),
    "I6": ("Fixed in WP-31",),
    # Batch 1-4 gap additions (DECISIONS D14, 14oct2026)
    "A3b": ("Changed behaviour",),
    "A3c": ("Changed behaviour",),
    "A3d": ("Changed behaviour",),
    "A5b": ("Results that change",),
    "C10d": ("Results that change",),
    "C10e": ("Results that change",),
    "C18b": ("Fixed in WP-31",),
    "C4b": ("Results that change",),
    "C6b": ("Results that change",),
    "C11b": ("Results that change",),
    "C8c": ("Results that change",),
    "C8d": ("Results that change",),
    "C8e": ("Results that change",),
    "B5c": ("Results that change",),
}

#: The section that closes each entry (index.md "Section manifest").
WP31_SECTION = {
    "C1": 2,
    "C2": 3,
    "B5a": 3,
    "C3": 4,
    "C10a": 5,
    "C10b": 6,
    "C18": 6,
    "F4": 6,
    "A5": 7,
    "A6": 7,
    "A7": 7,
    "A8": 7,
    "A1": 8,
    "A2": 8,
    "A3": 8,
    "A4": 8,
    "C10c": 9,
    "F1a": 10,
    "C4": 11,
    "C5": 12,
    "F1b": 13,
    "C6": 14,
    "C7": 14,
    "C8a": 15,
    "F1c": 16,
    "C8b": 17,
    "B5b": 18,
    "F1d": 19,
    "C9": 20,
    "B1": 21,
    "B2": 21,
    "B3": 21,
    "F1e": 22,
    "B4a": 23,
    "D1": 24,
    "F1f": 25,
    "B4b": 26,
    "D2": 27,
    "F1g": 28,
    "B4c": 29,
    "D3": 30,
    "D13": 30,
    "D4": 31,
    "C13": 31,
    "D5": 32,
    "E11": 32,
    "D6": 33,
    "D7": 33,
    "E6": 33,
    "D8": 34,
    "C17": 34,
    "E3": 34,
    "C14": 34,
    "C15": 34,
    "D9": 35,
    "D10": 36,
    "D11": 37,
    "D12": 38,
    "D14": 39,
    "D16": 39,
    "E1": 40,
    "E2": 40,
    "E12": 40,
    "E4": 41,
    "E5": 41,
    "E7": 41,
    "E8": 41,
    "E13": 41,
    "E9": 42,
    "G1": 43,
    "G2": 43,
    "G3": 43,
    "G4": 43,
    "G5": 43,
    "E10": 44,
    "D15": 45,
    "C11": 46,
    "C12": 46,
    "C16": 46,
    "G6": 46,
    "G7": 46,
    "F5": 46,
    "F2": 47,
    "F3": 47,
    "H2t": 48,
    "H2f": 49,
    "H2k": 50,
    "H2l": 51,
    "H1": 52,
    "H2x": 53,
    "K6": 54,
    "H3": 55,
    "H4": 55,
    "H7": 55,
    "J1": 56,
    "J2": 56,
    "J3": 57,
    "J4": 58,
    "J5": 58,
    "J6": 58,
    "I2": 59,
    "I3": 59,
    "I4": 59,
    "I5": 59,
    "I7": 59,
    "K2": 60,
    "K3": 60,
    "K4": 60,
    "H6": 60,
    "I6": 60,
    # Batch 1-4 gap additions (DECISIONS D14, 14oct2026)
    "A3b": 27,
    "A3c": 32,
    "A3d": 15,
    "A5b": 20,
    "C10d": 46,
    "C10e": 35,
    "C18b": 47,
    "C4b": 41,
    "C6b": 25,
    "C11b": 22,
    "C8c": 44,
    "C8d": 32,
    "C8e": 26,
    "B5c": 35,
}

WP31_ALL = tuple(WP31_LISTS)

_WP31_ID = r"[A-K]\d{1,2}[a-gkltx]?"
_WP31_MARKER = re.compile(r"<!-- WP-31 (%s) -->" % _WP31_ID)
_WP31_OPEN_FORM = re.compile(
    r"^  - Resolution: Not fixed because WP-31 section (\d{2}) has not landed\."
    r" Graded S[1-3] \(WP-31\): \S")
_GAPS3_ROW = re.compile(r"^\| (?P<id>[A-K]\d{1,2}) \| (?P<gap>.+?) \| (?P<sev>S[1-3][^|]*)\| ")
_GAPS3_TRACKED = re.compile(r"^- \*\*(?P<id>%s) Tracked:\*\* (?P<text>\S.*)$" % _WP31_ID)
_GAPS3_OPEN = re.compile(r"^Open \(WP-31 section (\d{2})\)\.$")
#: A closing commit writes "commit pending"; the merger's step k.3b rewrites
#: it to the landed sha on s3-bugs (DECISIONS A11), so the reader accepts
#: both and the batch-end gate (G2) and S61.3 forbid "pending".
_GAPS3_CLOSED = re.compile(
    r'^Closed in WP-31, BUGS\.md "([^"]+)", commit ([0-9a-f]{7,40}|pending)\.$')
_GAPS3_PARTLY = re.compile(
    r'^Partly closed in WP-31 \(section (\d{2}), commit ([0-9a-f]{7,40}|pending)\): '
    r'(\S.*); open: (\S.*) \(BUGS\.md "([^"]+)"\)\.$')


def _wp31_markers(text):
    return _WP31_MARKER.findall(text)


def _wp31_open_problems(open_map, entries):
    """As _wp30_open_problems, for WP-31 (WP31_ALL, _WP31_OPEN_FORM,
    WP31_SECTION)."""
    bad = []
    unknown = sorted(set(open_map) - set(WP31_ALL))
    if unknown:
        bad.append("ids WP-31 does not have: %s" % unknown)
    titles = list(open_map.values())
    if len(set(titles)) != len(titles):
        bad.append("two ids share one title")
    for pid, title in open_map.items():
        if '"' in title:
            bad.append("%s: the title holds a double quote" % pid)
        match = [e for e in entries if e["title"] == title]
        if len(match) != 1:
            bad.append("%s: %d BUGS.md entries are titled %r"
                       % (pid, len(match), title))
            continue
        e = match[0]
        if e["closed"]:
            bad.append("%s: %r is closed; delete its WP31_OPEN key"
                       % (pid, title))
            continue
        form = _WP31_OPEN_FORM.match(e["fields"].get("Resolution", ""))
        if not form:
            bad.append("%s: %r's Resolution is not 'Not fixed because WP-31 "
                       "section NN has not landed. Graded S1|S2|S3 (WP-31): "
                       "...'" % (pid, title))
        elif int(form.group(1)) != WP31_SECTION.get(pid):
            bad.append("%s: its Resolution names section %s, not %s"
                       % (pid, form.group(1), WP31_SECTION.get(pid)))
    return bad


def _wp31_marker_problems(open_ids, markers):
    bad = ["a marker names %s, which WP-31 does not have" % m
           for m in sorted(set(markers) - set(WP31_ALL))]
    bad += ["%s is open and CHANGELOG.md holds no marker for it" % pid
            for pid in WP31_ALL if pid in open_ids and pid not in markers]
    return bad


def _wp31_closure_problems(open_ids, markers, entries):
    bad = []
    for pid in WP31_ALL:
        if pid in open_ids:
            continue
        if pid in markers:
            bad.append("%s is closed and CHANGELOG.md still holds its "
                       "marker" % pid)
        tag = "(WP-31, %s)" % pid
        if not [e for e in entries if e["closed"]
                and tag in e["fields"].get("Resolution", "")]:
            bad.append("%s is closed and no closed BUGS.md entry's "
                       "Resolution holds %s" % (pid, tag))
    return bad


def _wp31_list_problems(lists_map, changelog):
    lists = _changelog_lists(changelog)
    bad = []
    names = sorted({n for ls in lists_map.values() for n in ls})
    bodies = {n: _changelog_list(lists, n) for n in names}
    for n in names:
        if bodies[n] is None:
            bad.append("CHANGELOG.md has no single '### %s' list" % n)
    for pid, wanted in lists_map.items():
        mark, line = "<!-- WP-31 %s -->" % pid, "(WP-31, %s)" % pid
        for n in wanted:
            body = bodies.get(n)
            if body is not None and mark not in body and line not in body:
                bad.append("%s: '### %s' holds neither its marker nor a line "
                           "ending %s" % (pid, n, line))
        for h, body in lists.items():
            if any(h == n or h.startswith(n + " (") for n in wanted):
                continue
            if mark in body:
                bad.append("%s: its marker sits under '### %s'" % (pid, h))
            if line in body:
                bad.append("%s: a line ending %s sits under '### %s'"
                           % (pid, line, h))
    return bad


def _parse_gaps3(text):
    """(rows, tracked, dupes): rows {table id: gap text}, tracked
    {entry id: text of its Tracked line}, dupes the entry ids with two
    Tracked lines.  Only GAPS3.md's table rows and its section 9 lines are
    read."""
    rows, tracked, dupes = {}, {}, []
    for ln in text.split("\n"):
        m = _GAPS3_ROW.match(ln)
        if m:
            rows[m.group("id")] = m.group("gap")
        t = _GAPS3_TRACKED.match(ln)
        if t:
            if t.group("id") in tracked:
                dupes.append(t.group("id"))
            tracked[t.group("id")] = t.group("text")
    return rows, tracked, dupes


def _gaps3_problems(rows, tracked, dupes, open_ids, entries, sha_exists):
    """Every WP-31 id has one Tracked line whose table row exists; an Open
    line names the id's section and the id is open; a Closed line names a
    closed entry's title and a commit that exists (or "pending", before the
    merger's step k.3b), and the id is not open; a Partly line names an
    existing commit (or "pending") and an open residual entry."""
    bad = ["%s has two Tracked lines" % d for d in dupes]
    bad += ["a Tracked line names %s, which WP-31 does not have" % t
            for t in sorted(set(tracked) - set(WP31_ALL))]
    for pid in WP31_ALL:
        if pid not in tracked:
            bad.append("%s: GAPS3.md has 0 Tracked lines" % pid)
            continue
        if re.sub(r"[a-z]$", "", pid) not in rows:
            bad.append("%s: GAPS3.md has no table row for it" % pid)
        text = tracked[pid]
        o, c, p = (_GAPS3_OPEN.match(text), _GAPS3_CLOSED.match(text),
                   _GAPS3_PARTLY.match(text))
        if o:
            if int(o.group(1)) != WP31_SECTION[pid]:
                bad.append("%s: Open names section %s, not %s"
                           % (pid, o.group(1), WP31_SECTION[pid]))
            if pid not in open_ids:
                bad.append("%s: Tracked Open but its entry is closed" % pid)
        elif c:
            title, sha = c.group(1), c.group(2)
            if pid in open_ids:
                bad.append("%s: Tracked Closed but its entry is open" % pid)
            if not [e for e in entries if e["closed"] and e["title"] == title]:
                bad.append("%s: no closed BUGS.md entry is titled %r"
                           % (pid, title))
            if sha != "pending" and not sha_exists(sha):
                bad.append("%s: commit %s does not exist" % (pid, sha))
        elif p:
            if p.group(2) != "pending" and not sha_exists(p.group(2)):
                bad.append("%s: commit %s does not exist" % (pid, p.group(2)))
            if not [e for e in entries if not e["closed"]
                    and e["title"] == p.group(5)]:
                bad.append("%s: no open BUGS.md entry is titled %r"
                           % (pid, p.group(5)))
        else:
            bad.append("%s: Tracked line %r is in none of the three forms"
                       % (pid, text))
    return bad


def _sha_exists(sha):
    return _git("cat-file", "-e", sha + "^{commit}").returncode == 0


class TestWp31Tracking:
    """WP-31's entries (index.md A4; section-01): open in BUGS.md naming
    their section, tracked Open in GAPS3.md section 9, with a marker in each
    CHANGELOG list they belong to, until their section lands; then closed,
    tracked Closed or Partly, with no marker left and a Resolution naming
    (WP-31, <id>)."""

    def test_every_allowed_title_is_an_open_entry(self, bugs):
        entries, _p = bugs
        assert not _wp31_open_problems(WP31_OPEN, entries), "\n".join(
            _wp31_open_problems(WP31_OPEN, entries))

    def test_an_open_entry_keeps_its_marker(self):
        bad = _wp31_marker_problems(set(WP31_OPEN),
                                    _wp31_markers(_read("CHANGELOG.md")))
        assert not bad, "\n".join(bad)

    def test_a_closed_entry_has_no_marker_and_a_resolution(self, bugs):
        entries, _p = bugs
        bad = _wp31_closure_problems(
            set(WP31_OPEN), set(_wp31_markers(_read("CHANGELOG.md"))),
            entries)
        assert not bad, "\n".join(bad)

    def test_each_entry_sits_in_its_changelog_lists(self):
        # 110 -> 118: DECISIONS D14 adds the eight batch 1-4 gaps; 118 -> 119:
        # D16 adds C6b; 119 -> 120: D17 adds C11b.
        # 120 -> 123: D18 adds C8c, C8d, C8e.
        # 123 -> 124: D19 adds B5c.
        assert WP31_ALL == tuple(WP31_LISTS) and len(WP31_ALL) == 124
        assert tuple(WP31_SECTION) == WP31_ALL
        assert set(WP31_SECTION.values()) == set(range(2, 61))
        bad = _wp31_list_problems(WP31_LISTS, _read("CHANGELOG.md"))
        assert not bad, "\n".join(bad)

    def test_every_entry_has_one_gaps3_tracked_line(self, bugs):
        entries, _p = bugs
        rows, tracked, dupes = _parse_gaps3(_read("GAPS3.md"))
        bad = _gaps3_problems(rows, tracked, dupes, set(WP31_OPEN), entries,
                              _sha_exists)
        assert not bad, "\n".join(bad)

    def test_the_marker_reader(self):
        text = ("### Results that change\n\n<!-- WP-31 C1 -->\n"
                "### Changed behaviour (may need your do-files changed)\n\n"
                "<!-- WP-31 C10a --><!-- WP-31 H2t -->\n"
                "### Fixed in WP-31\n\n<!-- WP-31 F1g -->\n")
        assert _wp31_markers(text) == ["C1", "C10a", "H2t", "F1g"]
        assert _wp31_markers("<!-- WP-30 P1.1a --> <!-- WP-31 C1-->") == []
        assert _wp31_markers("<!-- WP-31 B5a --><!-- WP-31 B5b -->") == [
            "B5a", "B5b"]

    def test_the_wp31_problem_readers(self):
        def entry(title, closed, res):
            return {"title": title, "closed": closed,
                    "fields": {"Resolution": "  - Resolution: " + res}}
        open_form = ("Not fixed because WP-31 section 02 has not landed. "
                     "Graded S1 (WP-31): dropped.")
        good = [entry("T1", False, open_form),
                entry("T2", True, "Fixed 01nov2026 (WP-31, C2). Done.")]
        assert _wp31_open_problems({"C1": "T1"}, good) == []
        for open_map, entries, says in (
                ({"C1": "T2"}, good, "is closed"),
                ({"C1": "T9"}, good, "0 BUGS.md entries"),
                ({"C1": "T1"}, [entry("T1", False, open_form.replace(
                    "02", "03"))], "names section 03, not 2"),
                ({"Z9": "T1"}, good, "does not have"),
                ({"C1": 'a "q"'}, [entry('a "q"', False, open_form)],
                 "double quote")):
            assert any(says in b for b in _wp31_open_problems(
                open_map, entries)), (says, open_map)
        assert _wp31_marker_problems({"C1"}, []) == [
            "C1 is open and CHANGELOG.md holds no marker for it"]
        others = set(WP31_ALL) - {"C2"}
        assert _wp31_closure_problems(others, others, good) == []
        assert _wp31_closure_problems(others, others, good[:1]) == [
            "C2 is closed and no closed BUGS.md entry's Resolution holds "
            "(WP-31, C2)"]
        log = ("## 1.0\n\n### Results that change\n\n<!-- WP-31 C1 -->\n"
               "### Fixed in WP-31\n\n- x. (WP-31, J1)\n")
        assert _wp31_list_problems({"C1": ("Results that change",),
                                    "J1": ("Fixed in WP-31",)}, log) == []
        assert _wp31_list_problems({"J1": ("Results that change",)}, log) == [
            "J1: '### Results that change' holds neither its marker nor a "
            "line ending (WP-31, J1)",
            "J1: a line ending (WP-31, J1) sits under '### Fixed in WP-31'"]

    def test_the_gaps3_readers(self):
        text = ("| ID | Gap | Sev | Register | Evidence | Task |\n"
                "|---|---|---|---|---|---|\n"
                "| C1 | heads are fixed | S1 | P2.8 | r.py:1 | fix |\n"
                "| C8 | colorvar on 4 types | S2 | P2.10 | d.ado:2 | route |\n"
                "## 9. Tracking\n\n- **C1 Tracked:** Open (WP-31 section 02).\n"
                '- **C8a Tracked:** Closed in WP-31, BUGS.md "T2", commit '
                "0123abc.\n- **C8b Tracked:** Partly closed in WP-31 (section "
                '17, commit 0123abc): aliases; open: pcycle (BUGS.md "R1").\n')
        rows, tracked, dupes = _parse_gaps3(text)
        assert rows == {"C1": "heads are fixed", "C8": "colorvar on 4 types"}
        assert sorted(tracked) == ["C1", "C8a", "C8b"] and dupes == []
        entries = [{"title": "T2", "closed": True, "fields": {}},
                   {"title": "R1", "closed": False, "fields": {}}]
        tracked_all = {pid: "Open (WP-31 section %02d)." % WP31_SECTION[pid]
                       for pid in WP31_ALL}
        tracked_all.update(tracked)
        # Every other id needs a table row too, or it is reported as having
        # none; the synthetic table above holds only C1 and C8.
        rows_all = {re.sub(r"[a-z]$", "", pid): "gap" for pid in WP31_ALL}
        rows_all.update(rows)
        bad = _gaps3_problems(rows_all, tracked_all, dupes,
                              set(WP31_ALL) - {"C8a"}, entries,
                              lambda s: s == "0123abc")
        assert bad == [], bad
        bad = _gaps3_problems(rows_all, tracked_all, dupes, set(WP31_ALL),
                              entries, lambda s: False)
        assert "C8a: Tracked Closed but its entry is open" in bad
        assert "C8a: commit 0123abc does not exist" in bad
        assert "C8b: commit 0123abc does not exist" in bad
        rows2 = dict(rows_all)
        rows2.pop("C1")
        assert "C1: GAPS3.md has no table row for it" in _gaps3_problems(
            rows2, tracked_all, dupes, set(WP31_ALL), entries, lambda s: True)
        assert "C1: GAPS3.md has 0 Tracked lines" in _gaps3_problems(
            rows, {}, [], set(WP31_ALL), entries, lambda s: True)
        # "commit pending" (DECISIONS A11) passes without a sha check.
        pend = dict(tracked_all)
        pend["C8a"] = 'Closed in WP-31, BUGS.md "T2", commit pending.'
        pend["C8b"] = ("Partly closed in WP-31 (section 17, commit pending): "
                       'aliases; open: pcycle (BUGS.md "R1").')
        assert _gaps3_problems(rows_all, pend, dupes, set(WP31_ALL) - {"C8a"},
                               entries, lambda s: False) == []
        # Split-row ids (B5a/B5b, C10a..c, F1a..g, H2f/k/l/t/x) parse.
        for pid in ("B5a", "B5b", "C10c", "F1g", "H2t"):
            m = _GAPS3_TRACKED.match(
                "- **%s Tracked:** Open (WP-31 section 03)." % pid)
            assert m and m.group("id") == pid, pid
