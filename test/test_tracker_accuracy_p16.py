"""
test_tracker_accuracy_p16.py -- the tracking documents and dash_setup's
help say what is true (WP-48 section 48-03, DT-29; also DT-30, TR-22).

The defect (drop-in audit of 19oct2026, package 16): dash_setup.sthlp said
venv() installs the packages "at their minimums" where every install runs
the hash-pinned lock, and dash.sthlp said "Only bokeh has a ceiling" where
dash_setup.sthlp gives numpy and pandas theirs; CHANGELOG.md's 0.1.0 list
kept lines later work in the same release reversed; TWOWAY_COVERAGE_AUDIT.md
kept open text later work closed; GAPS3.md's H5, I1, K1 and K5 said nowhere
where they are tracked; DROPIN-REMAINING.md's P2.34 and P2.64 were mapped to
nothing; test/fixtures/rejected_options.json's narrative described the
18oct2026 state with help line numbers.

Plain file reads only.  No test reads the Stata-version sentences the plan
keeps byte-identical, or the lines section 35-09 corrected.
"""
import ast
import json
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.normpath(os.path.join(_HERE, ".."))


def _read(rel):
    with open(os.path.join(_ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def _flat(text):
    """*text* with every run of white space one blank."""
    return re.sub(r"\s+", " ", text)


def _between(text, start, end):
    i = text.index(start)
    j = text.index(end, i + len(start))
    return text[i:j]


class TestSetupHelp:
    """dash_setup.sthlp and dash.sthlp agree on what venv() installs and
    which packages have ceilings."""

    def test_venv_uses_the_lock(self):
        h = _flat(_read("dash_setup.sthlp"))
        item = _between(h, "{opt venv(path)} sets up", "{phang2}")
        assert "at their minimums" not in item, item
        assert ("installs packaging, bokeh, numpy and pandas from the "
                "hash-pinned lock (see {help dash_setup##lock:The "
                "hash-pinned lock}) into it;") in item, item
        # The lock section the sentence links says venv()'s install is
        # the lock's too.
        lock = _between(h, "{marker lock}", "{marker options}")
        assert "{cmd:venv()} one included" in lock, lock

    def test_ceilings_agree(self):
        setup = _flat(_read("dash_setup.sthlp"))
        assert ("{cmd:numpy>=2.3,<2.5} and {cmd:pandas>=2.3,<3.1}"
                in setup)
        assert "only bokeh's ceiling is reported" in setup
        dash = _flat(_read("dash.sthlp"))
        item = _between(dash, "{phang2}{ul:Python packages, required}",
                        "{phang2}{ul:Python packages, optional}")
        assert "Only bokeh has a ceiling" not in item, item
        assert ("bokeh, numpy and pandas have ceilings (see {helpb "
                "dash_setup}); only bokeh's is reported.") in item, item
        # The lock's own requirements line carries the same three windows.
        req = [ln for ln in _read("dash_requirements.txt").splitlines()
               if ln.startswith("# requirements:")]
        assert len(req) == 1, req
        for spec in ("bokeh>=3.8,<3.10", "numpy>=2.3,<2.5",
                     "pandas>=2.3,<3.1"):
            assert spec in req[0], (spec, req[0])


class TestChangelog:
    """Every 0.1.0 line later work reversed keeps its text and names what
    superseded it, before any marker comment."""

    #: (phrase that finds the line, what supersedes it must name)
    _REVERSED = (
        ("`rpcap` and `rpspike` are refused by name", "WP-31"),
        ("`tmlabel()` and `tmtick()` are accepted and named until minor "
         "ticks are drawn", "WP-31"),
        ("`lwidth(-1)` or `yaxis(3)` is r(198) or r(111)", "WP-31"),
        ("`[aw=price+1]` is r(198)", "WP-31"),
        ("is now named as mlalign() until it is drawn", "WP-47"),
        ("are filed as open BUGS.md entries. (WP-32, K4)", "WP-32"),
        ("is filed as an open BUGS.md entry. (WP-32, K3)", "WP-32"),
    )

    def test_reversed_lines_are_annotated(self):
        lines = _read("CHANGELOG.md").splitlines()
        bad = []
        for phrase, wp in self._REVERSED:
            hits = [i for i, ln in enumerate(lines) if phrase in ln]
            if len(hits) != 1:
                bad.append("%r is on %d lines" % (phrase, len(hits)))
                continue
            i = hits[0]
            near = [ln for ln in lines[i:i + 2]
                    if "(Superseded in 0.1.0:" in ln]
            if not near:
                bad.append("%r: no '(Superseded in 0.1.0:' on its line or "
                           "the next" % phrase)
                continue
            ln = near[0]
            note = ln[ln.index("(Superseded in 0.1.0:"):]
            if wp not in note:
                bad.append("%r: the annotation names no %s" % (phrase, wp))
            if "<!--" in ln and ln.index("<!--") < ln.index(
                    "(Superseded in 0.1.0:"):
                bad.append("%r: the annotation follows a marker" % phrase)
        assert not bad, "\n".join(bad)


class TestCoverageAudit:
    """No TWOWAY_COVERAGE_AUDIT.md row states as open a defect that is
    closed: the words are gone, or a [Closed in ...] tag follows them."""

    _STALE = (
        "Upright only",
        "saved HTML does not recompute",
        "standalone HTML does not recompute",
        "remains fixed in saved HTML",
        "saved HTML retains the original bins",
        "the saved page still does not recompute",
        "fits and smooths are not recomputed",
        "`fxsize()`, `fysize()`, and `scale()` ignored",
        "the bystyles other than compact and default stay named",
        "`rows()`, `holes()`, `compact`, and `yrescale` ignored",
    )

    def test_no_stale_open_text(self):
        text = _read("TWOWAY_COVERAGE_AUDIT.md")
        assert ("Unknown option names are normally accepted and reported "
                "as ignored") not in text
        bad = []
        seen = set()
        for n, ln in enumerate(text.splitlines(), 1):
            if "headlabel" in ln:
                continue
            for phrase in self._STALE:
                if phrase in ln:
                    seen.add(phrase)
                    if "[Closed in" not in ln[ln.index(phrase):]:
                        bad.append("line %d: %r untagged" % (n, phrase))
        assert not bad, "\n".join(bad)
        for phrase in ("**176 option names**", "**3,612 passing tests"):
            ln = [x for x in text.splitlines() if phrase in x]
            assert len(ln) == 1 and "[Counts of" in ln[0] \
                and "superseded]" in ln[0], (phrase, ln)
        summary = [x for x in text.splitlines()
                   if x.startswith("- An option name twoway refuses")]
        assert len(summary) == 1, summary
        assert "titel()" in summary[0] and "Unsupported" in summary[0]


def _gaps4_tracked():
    """{GAPS4 id: text of its Tracked line}."""
    out = {}
    for ln in _read("GAPS4.md").splitlines():
        m = re.match(r"^- \*\*(\S+) Tracked:\*\* (.*)$", ln)
        if m:
            out[m.group(1)] = m.group(2)
    return out


class TestRegisters:
    """GAPS3's H5, I1, K1 and K5 and DROPIN's P2.34 and P2.64 say where
    each is tracked now."""

    def test_gaps3_rows_say_where(self):
        text = _read("GAPS3.md")
        sec = text[text.index("## 9. Tracking"):]
        intro = _flat(sec[:sec.index("\n- **")])
        lead = ("H5, I1, K1 and K5 are residuals the WP-31 index expected; "
                "where each is tracked now: ")
        tracked = {m.group(1) for m in re.finditer(
            r"^- \*\*(\S+) Tracked:\*\*", sec, re.M)}
        assert lead in intro, intro
        said = intro[intro.index(lead) + len(lead):]
        gaps4 = _gaps4_tracked()
        for pid in ("H5", "I1", "K1", "K5"):
            assert pid in tracked or re.search(
                r"(^|; )%s: " % pid, said), (pid, said)
        for gid in re.findall(r"GAPS4 ([\w:-]+)", said):
            assert gid.rstrip(",") in gaps4, gid

    def test_dropin_rows_are_mapped(self):
        rows, section = {}, None
        for ln in _read(".ultraplan/handoff/DROPIN-REMAINING.md"
                        ).splitlines():
            if ln.startswith("### "):
                section = ln[4:7]
            m = re.match(r"^(\d+)\. (.*)$", ln)
            if m and section == "P2:":
                rows[int(m.group(1))] = m.group(2)
        gaps4 = _gaps4_tracked()
        for n in (34, 64):
            row = rows[n]
            assert "[Mapped to GAPS4 " in row, (n, row)
            tag = row[row.index("[Mapped to GAPS4 "):]
            for gid, state in re.findall(r"([\w:-]+-\d+) \((\w+)", tag):
                assert gid in gaps4, (n, gid)
                assert gaps4[gid].startswith(state), (n, gid, state,
                                                      gaps4[gid])
            if any(gaps4[g].startswith("Open")
                   for g, _s in re.findall(r"([\w:-]+-\d+) \((\w+)", tag)
                   if g in gaps4):
                assert "[Closed in" not in row and "Written closed" \
                    not in row, (n, row)


def _script_notes():
    """NOTES, the constants scripts/extract_rejected_options.do's python
    block writes into the fixture."""
    s = _read("scripts/extract_rejected_options.do")
    i = s.index("\npython:\n")
    src = s[i + len("\npython:\n"):s.index("\nend", i)]
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and getattr(
                node.targets[0], "id", "") == "NOTES":
            return ast.literal_eval(node.value)
    raise AssertionError("NOTES not found")


def _fixture():
    with open(os.path.join(_HERE, "fixtures", "rejected_options.json"),
              encoding="utf-8") as fh:
        return json.load(fh)


def _narrative(d):
    """{field: text} of the fixture's (or NOTES') narrative strings."""
    defects = d.get("blocking_defects") or [d.get("blocking_defect")]
    return {"purpose": d["purpose"], "root_cause": d["root_cause"],
            "dash_only_note": d["dash_only_note"],
            "blocking_defect.summary": defects[0]["summary"],
            "blocking_defect.note": defects[0]["note"]}


class TestRejectedNarrative:
    """rejected_options.json's narrative is current and written by its
    script."""

    def test_no_help_line_numbers(self):
        for k, v in _narrative(_fixture()).items():
            assert not re.search(r"\.(sthlp|ado|mata|py):\d", v), (k, v)

    def test_written_by_its_script(self):
        assert _narrative(_fixture()) == _narrative(_script_notes())
