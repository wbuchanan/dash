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
CLOSED_WITHOUT_A_TEST = frozenset({
    "Eight fills in comprehensive_demo.do render at a hundredth of the "
    "intended opacity",
    "Every successful `dash build' prints an unexplained \"file not found\"",
    "ylabel(#5, grid) was silently ignored",
})

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


def _parse_roadmap(text):
    """{WP-nn: {'done': bool, 'gaps': {gap: qualified?}}}."""
    wps = {}
    parts = re.split(r"^(?=## WP-\d{2} )", text, flags=re.M)
    for part in parts[1:]:
        head = part.split("\n", 1)[0]
        wp = re.match(r"^## (WP-\d{2}) ", head).group(1)
        section = re.split(r"^# ", part, flags=re.M)[0]
        section = re.split(r"^## (?!WP-)", section, flags=re.M)[0]
        done = (head.rstrip().endswith("\u2014 DONE")
                or re.search(r"^> \*\*DONE\b", section, re.M) is not None)
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


@pytest.fixture(scope="module")
def docs():
    roadmap = _read("ROADMAP.md")
    matrix = _matrix_gaps(roadmap)
    gaps, dupes = _parse_gaps(_read("GAPS.md"), matrix)
    return {"matrix": matrix, "gaps": gaps, "dupes": dupes,
            "wps": _parse_roadmap(roadmap)}


def _git(*args):
    return subprocess.run(["git", "-C", _ROOT] + list(args),
                          capture_output=True, text=True)


class TestEveryGapHasAStatus:

    def test_every_gap_in_the_matrix_has_one_heading(self, docs):
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
        if not shas:
            return
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
