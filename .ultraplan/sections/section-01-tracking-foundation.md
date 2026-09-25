# Section 01: Tracking foundation

> Part of: WP-28 · Gaps: all 22 (tracked here, closed elsewhere) · Risk: green · Batch: 1 · Depends on: none · Blocks: 19 


## Review amendments (Phase 4, 2026-09-25) — binding; they override any conflicting text below

> Batch **1** · Depends on **none** · Blocks **19** · Risk **green** · Commits: one commit (S01)

- D2: task 01-03 places 23 `<!-- WP-28 <ID> -->` markers **in the list where each gap's entry belongs** (see `index.md` Gap coverage: Results that change / Changed behaviour / Requirements / Fixed in WP-28; E14 gets two), not all under one heading.
- D3: the BUGS.md template's field name stays exactly `- Resolution:`; the text form is `Fixed <ddmonyyyy> (WP-28, <ID>). <what changed>. Pinned by test/<file>::<Class>::<test>.` (verify against `_FIELD` in test/test_tracking_documents.py:98-101).
- Q24: the commit convention records the failing test's output at 91d97be in the fix commit body; CHANGELOG quotes it as the old value.

Applies to every section:
- D1 (binding): tasks are work steps; commits are per gap (S01-S04: one each). The failing regression tests are written first and run against the unmodified tree; their output at 91d97be is recorded in the fix commit's message (Q24) and they are committed together with the fix, never alone (CLAUDE.md rule 4).
- D3 (binding): each gap's BUGS.md entry is appended at the END of BUGS.md in the closed form with `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). <what changed>. Pinned by test/<file>::<Class>::<test>.`
- D2 (binding): each closing task replaces the gap's `<!-- WP-28 <ID> -->` marker(s) that S01 placed in the CHANGELOG list named above; it does not add a new line elsewhere.
- D6 (binding): every Stata run is `scripts/stata_slot.sh <scratch-dir> <file>.do` (see `index.md` step 0); no section launches the full cert suite or the release gate.
- D5 (binding): shared files follow merge rules R1-R6 in `index.md` (cscript registration and hygiene pins, copy lists and maps, help/CHANGELOG/BUGS.md, graph-key lists, fixtures, parity corpus).
- D7: XML fields holding `&`, `<` or `>` are CDATA-wrapped (done mechanically); task names over 8 words are shortened and `done` fields put in the past tense during the detailed fixer pass.

Detailed edits from `../review/consistency.md`, `../review/requirements-security.md` and `../review/feasibility.md` (as adjusted by `../review/DECISIONS.md`) are applied to this file in the fixer pass; until then this block governs.

## Overview

Nothing in the repository can yet record WP-28 truthfully. `GAPS2.md`, the audit the whole
package answers, is untracked (`??` in `git status`), and `test/test_packaging.py:411` refuses
any file at the package root that is neither shipped nor on `_ROOT_ALSO`, so it cannot be
committed as it stands. `test/test_tracking_documents.py` knows one audit, `GAPS.md` of 21
September: `_parse_roadmap` (623-645) reads a package's `**Gaps closed:**` ids and, once the
package is headed `— DONE`, `test_every_gap_a_done_package_lists_is_closed_by_it` (765-790)
looks each id up in **GAPS.md**. GAPS2's ids reuse GAPS.md's letters (`B1`, `E1`, `G1` name
different gaps in the two audits), so a DONE WP-28 listing its gaps under that field would be
judged against the wrong document and fail; and the `X1`/`X2` ids match no reader at all.
`_matrix_gaps`/`_matrix_rows` (532-548) split ROADMAP.md on the literal text
`## Traceability matrix`, so that text may not appear anywhere in WP-28's section. And the
BUGS.md guard `TestNoOpenEntryBlocksARelease` (476-505) turns pytest red on any open S1 or S2
entry, which is why DISCOVERY's amended Q4 has every entry land **closed, in its fix commit**:
22 open entries opened up front would break every full run until the last closed.

After this section: WP-28 is open in `ROADMAP.md` in the WP-27 style, listing all 22 gaps
with severity, effort and the section that closes each in its own `#### GAPS2 traceability`
table; the tracking tests read a `**GAPS2 closed:**` field and resolve it against GAPS2.md's
`### <ID>.` headings, and once a package is DONE they require each listed entry's
`- **Tracked:**` line to name that package, a closed BUGS.md entry and a commit that exists;
`GAPS2.md` is committed and allowed at the root; `CHANGELOG.md` carries a `### Fixed in WP-28`
stub with a marker per gap; and the two conventions every later section copies, the BUGS.md
entry form and the commit-message form, are written down here.

These belong together because they are the guards every later commit must pass. They run in
batch 1 with no dependency: sections 05-18 need only the *text* of the conventions below,
which they read from this file, and section 19 needs the readers to prove closure.

**Test order (CLAUDE.md rule 7): task 01-01 writes the failing tests for this section**, runs
them against the unmodified tree and records the failure text for the commit that turns them
green. No shipped file changes here.

## Risk: [green] — one test module extended, one allowlist entry, three documents; every existing assertion kept verbatim

- **Why.** No renderer or ado code moves. The new readers are additive functions and a
  separate fixture key; `_parse_roadmap`'s output is unchanged, so `test_the_roadmap_reader`
  (815-829), which asserts exact dictionaries, passes untouched.
- **Risk factors.** (1) A `**Gaps closed:**` line written into WP-28 by habit would be read
  by the old parser and, once DONE, judged against GAPS.md. (2) The text
  `## Traceability matrix` inside WP-28 would move the matrix reader's split point. (3) A line
  beginning `# ` or `## ` inside WP-28, even in a fenced code block, ends the section for
  `_parse_roadmap` (630-631). (4) Parallel batch-1 sections all append to BUGS.md and
  CHANGELOG.md, so `patch -p1` of their diffs may reject hunks at end-of-file.
- **Mitigation.** (1)-(3) are pinned mechanically: a new test counts the matrix heading once,
  and the WP-28 text in TR-01.6 uses the `**GAPS2 closed:**` field and `###`/`####` headings
  only. (4) is an executor note below.

## Dependencies

- Depends on: none.
- Blocks: section 19 (the closeout proves closure through the readers added here).
- Parallel batch: 1. Can run with sections 02-10; none touches `test_tracking_documents.py`,
  `test_packaging.py`, `ROADMAP.md` or the CHANGELOG heading this section adds.
- Why: every other section's final task writes a BUGS.md entry and a CHANGELOG line in the
  forms recorded here, and section 19 updates GAPS2.md's Tracked lines in the form the new
  parser reads.

## Evidence

### The BUGS.md parser and the release guard (research report C §7)

`test/test_tracking_documents.py:98-102`, the entry and field readers:

```python
  98	_ENTRY = re.compile(r"^- \[(?P<mark>[ x])\] Title: (?P<title>\S.*)$")
  99	_FIELDS = ("File Names and Line Numbers", "Description", "Suggested fix",
 100	           "Resolution")
 101	_FIELD = re.compile(r"^  - (?P<name><![CDATA[File Names and Line Numbers|Description|"
 102	                    r"Suggested fix|Resolution)(?P<qual> \([^()\n]*\))?: \S")
```

`_format_problems` (154-161) requires the four fields once each, in that order; a line inside
an entry that is neither a field, a `  - ` note nor a four-space continuation is a problem
(145-148). `_references` (295-325) turns every `test_*.py|cscript|do` name (`_FILE_REF`, 285),
every `test_x.py::Class[::test]` node (`_NODE_REF`, 287), every `Test[A-Z]\w+` word
(`_CLASS_REF`, 288) and every `AB-12`-shaped case id (`_CASE_ID`, 207) in an entry into a
reference that must exist on disk, unless the entry says "`X` no longer exists"
(`_acknowledged_gone`, 291). `TestNoOpenEntryBlocksARelease` (476-505):

```python
 487	    _GRADE = re.compile(r"\bGraded (S[1-3]) \(WP-\d{2}\): \S")
 ...
 498	    def test_no_open_entry_is_s1_or_s2(self, bugs):
 499	        bad = ["line %d: %s %s" % (e["line"], g, e["title"][:90])
 500	               for e in entries if not e["closed"]
 501	               for g in self._GRADE.findall(e["fields"].get("Resolution", ""))
 502	               if g in ("S1", "S2")]
```

BUGS.md today (report C §7): 2605 lines, 428 closed and 4 open entries (2523, 2559, 2595,
2601), all four graded S3. A closed entry's shape, `BUGS.md:2571-2576`:

```
- [x] Title: Under by(), a qualifier holding _n or a subscript selects its rows in the data's order, where twoway selects them after sorting on the by() variables
  - File Names and Line Numbers: dash.ado: `_dash_qual_gen' (the qualifier columns, filled in the data's order); the by() panel counts (`_dash_by_panels')
  - Description: Found 24sep2026 by the S3 batch's by() total-panel fix: twoway draws ...
  - Suggested fix: For a by() graph, evaluate its qualifiers ...
  - Resolution: Not fixed yet: ... **Fixed 24sep2026 (S3 batch).** ... Pinned by test/test_qualifier_in_stata.cscript QS-16 (...) and test/test_qualifier_columns.py::TestATotalPanelReadsItsOwnColumn (13 tests, all failing on the unfixed code).
```

### The ROADMAP readers and their GAPS.md lookup

`test/test_tracking_documents.py:623-645`:

```python
 623	def _parse_roadmap(text):
 624	    """{WP-nn: {'done': bool, 'gaps': {gap: qualified?}}}."""
 626	    parts = re.split(r"^(?=## WP-\d{2} )", text, flags=re.M)
 ...
 630	        section = re.split(r"^# ", part, flags=re.M)[0]
 631	        section = re.split(r"^## (?!WP-)", section, flags=re.M)[0]
 632	        done = (head.rstrip().endswith("— DONE")
 633	                or re.search(r"^> \*\*DONE\b", section, re.M) is not None)
 635	        m = re.search(r"^\*\*Gaps closed:\*\* (.+?)(?: · |$)", section,
 636	                      re.M)
 639	                g = re.match(r"^(?:and\s+)?([A-N]\d{0,2})(?![A-Za-z0-9-])"
```

The `docs` fixture (648-654) reads GAPS.md alone: `gaps, dupes = _parse_gaps(_read("GAPS.md"),
matrix)`. `test_every_gap_a_done_package_lists_is_closed_by_it` (765-790) then says, for a
DONE package, `"%s lists %s, which GAPS.md lacks"` or `"... GAPS.md says %r"`. The matrix
readers (532-548):

```python
 533	    part = roadmap.split("## Traceability matrix", 1)[1]
 534	    part = part.split("\n## ", 1)[0]
 535	    return {m.group(1) for m in re.finditer(r"^\| ([A-N]\d{0,2}) \|", part,
```

`test_the_roadmap_reader` (815-829) asserts `_parse_roadmap(text) == {"done": …, "gaps": …}`
dictionaries **exactly**, so the new field must not be added to that dictionary.

### ROADMAP.md, CHANGELOG.md and GAPS2.md as they stand

`ROADMAP.md:4131-4133` (WP-27's head) and the matrix at 4243, separated by a `---` at 4241:

```
4131	## WP-27 · Release closeout — DONE
4133	**Gaps closed:** M2, B4 (verification) · **Severity:** S3 · **Effort:** S · **Depends on:** all
4135	> **User story.** As the maintainer, I want one command sequence that proves
4138	### Business requirements
4145	### Technical requirements
4163	### Acceptance criteria — release gate
4173	### Test plan
4180	### Done, measured (24sep2026)
4241	---
4243	## Traceability matrix
```

WP-25 (3835-3990) also carries `#### The plan in detail` with `**US-25.1** As a maintainer, …`
user stories. `CHANGELOG.md` headings: `## 2.0, 24sep2026 (release candidate)` (3),
`### Results that change` (10), `### Security` (142), `### New` (178), `### Fixed` (219),
`### Changed behaviour (may need your do-files changed)` (280), `### Removed` (321),
`### Requirements` (330), `### Fixed after WP-27 (the S3 batch, 24sep2026)` (338),
`### Fixed in WP-27` (383). The newer of the last two sits above the older; each line ends
with its package in parentheses, `(WP-27)`. No test checks the CHANGELOG's structure.
`GAPS2.md` (2,070 lines) heads each gap `<a id="b1"></a>` then `### B1. <title>`, and each
entry ends with a `- **Tracked:** …` line (for example `- **Tracked:** new.` at 393); the
merged duplicates (`**B8. …** -- same gap as E3; see there.`, 455) are bold lines, not
headings. Severity and effort per gap come from the area tables (`| ID | Gap | Sev | Closable
| Effort |`, e.g. 1088, 1379, 1786) and the S1 table at 40-62. `git check-ignore GAPS2.md`
returns 1: it is untracked, not ignored, so a plain `git add` takes it.

`test/test_packaging.py:411-415`:

```python
 411	_ROOT_ALSO = frozenset({
 412	    "dash.pkg", "stata.toc", ".gitignore", "Makefile", "pyproject.toml",
 413	    "AGENTS.md", "BUGS.md", "CHANGELOG.md", "CLAUDE.md", "GAPS.md", "REMAINING.md",
 414	    "ROADMAP.md",
 415	})
```

`test_the_package_root_holds_only_what_ships_and_the_repositorys_own` (418-434) reads
`git ls-files`, so a staged GAPS2.md fails it until the allowlist names it.

### Existing tests that pin today's behaviour

None flips. Every test in `test/test_tracking_documents.py` and `test/test_packaging.py` keeps
its assertion; the new tests are additive. `test_tracking_documents.py::TestTodoAndPlanAreRetired::test_nothing_links_them`
scans every `.md` in the repository for Markdown links to `TODO.md`/`PLAN.md`; GAPS2.md holds
none (measured: `grep -n 'PLAN\.md\|TODO\.md' GAPS2.md` is empty), so committing it is safe.

## User stories

- **US-01.1** As the maintainer, I want WP-28 listed in `ROADMAP.md` with every gap, its
  severity, effort and the section that closes it, before the first fix lands, so that the
  plan is visible and its closure can be measured against a written list.
- **US-01.2** As the maintainer, I want the tracking tests to read GAPS2.md, so that a claim
  that WP-28 closed a gap is checked against the audit, a closed BUGS.md entry and a commit,
  not taken on trust.
- **US-01.3** As the maintainer, I want GAPS2.md committed on `s3-bugs`, so that the audit and
  the commits that answer it share one history.
- **US-01.4** As the developer or agent of any later section, I want one written form for a
  BUGS.md entry, a CHANGELOG line and a commit message, so that every section's records are
  uniform, parseable by the guards, and need no re-editing at closeout.

## Business requirements

- **BR-01.1** `ROADMAP.md` holds WP-28 in the same shape as WP-27, listing all 22 gaps of
  PRD §4 with severity, effort and closing section, and is not marked DONE.
- **BR-01.2** The full pytest suite stays green at every commit of WP-28 without any BUGS.md
  entry being opened; the release guard (no open S1/S2) is untouched.
- **BR-01.3** A GAPS2 gap a DONE package claims is provably closed: the audit entry names the
  package, a BUGS.md entry that is closed, and a commit that exists, and a test checks all
  three both ways (package → entry, entry → package).
- **BR-01.4** `GAPS2.md` is committed and the packaging test allows it at the root.
- **BR-01.5** `CHANGELOG.md` has a place for WP-28's lines, one marker per gap, under the
  current release heading.
- **BR-01.6** Every existing assertion of `test_tracking_documents.py` and `test_packaging.py`
  passes unchanged.
- **BR-01.7** The BUGS.md entry form, the CHANGELOG line form and the commit-message form are
  written down once, here, and sections 05-18 follow them verbatim.

## Technical requirements

- **TR-01.1 The field.** A work package may carry, on its header line beside `**Severity:**`,
  a `**GAPS2 closed:** <ids>` field. Ids match `[A-NX]\d{1,2}`, comma-separated, optionally
  qualified in parentheses as `**Gaps closed:**` items are. The old `**Gaps closed:**` regex
  (635) does not match this text, so `_parse_roadmap` ignores it.
- **TR-01.2 The GAPS2 reader.** Add `_parse_gaps2(text)` to `test_tracking_documents.py`
  returning `({id: entry}, dupes)`. A heading is `^### (?P<id>[A-NX]\d{1,2})\. (?P<title>\S.*)$`
  (`_GAPS2_HEADING`); the entry's Tracked line is the first `^- \*\*Tracked:\*\* (?P<text>\S.*)$`
  (`_GAPS2_TRACKED`) after it and before the next heading or `## ` line. The entry records
  `title`, `line`, `tracked` (the text), and its classification: `closed = (wp, bugs_title, sha)`
  when the text matches `_GAPS2_CLOSED = ^Closed in (WP-\d{2}), BUGS\.md "([^"]+)", commit ([0-9a-f]{7,40})\b`;
  `deferred = wp` when it matches `_GAPS2_DEFERRED = ^Deferred \((WP-\d{2})\): \S`; else
  `open`. Text after the first `;` is commentary (residuals, the original audit text) and is
  not read.
- **TR-01.3 The package reader.** Factor `_parse_roadmap`'s splitting (626-631) into
  `_wp_sections(text)` yielding `(wp, head, section, done)`, used by `_parse_roadmap` (whose
  return value is unchanged, so `test_the_roadmap_reader` passes verbatim) and by a new
  `_parse_roadmap_gaps2(text)` returning `{wp: {"done": bool, "gaps2": {id: qualified?}}}`
  from the `**GAPS2 closed:**` field, reusing `_split_items`. Extend the `docs` fixture with
  `"gaps2"`, `"gaps2_dupes"` and `"wps2"` keys; keep the existing keys.
- **TR-01.4 The tests**, in a new class `TestGaps2AndRoadmapAgree`:
  `test_every_gaps2_id_a_package_declares_has_a_heading` (every declared id resolves, DONE or
  not; no duplicate headings); `test_every_gaps2_id_a_done_package_lists_is_closed_by_it`
  (for each DONE package, each id's Tracked line is the Closed form naming that package);
  `test_every_closed_gaps2_entry_is_listed_by_its_package` (the reverse: the named package
  exists, is DONE, and lists the id); `test_every_closed_gaps2_entry_names_a_closed_bugs_entry_and_a_commit`
  (the quoted title equals exactly one BUGS.md entry's title and that entry is closed and its
  Resolution carries the qualifier `(<wp>, <id>)`; the commit resolves with
  `git cat-file -e <sha>^{commit}`, skipping only when `rev-parse --git-dir` fails, as
  `test_a_closing_commit_exists` does); `test_a_deferred_gaps2_entry_names_its_package_and_a_reason`
  (a Tracked line beginning `Deferred` matches `_GAPS2_DEFERRED` and its package exists in
  ROADMAP.md); `test_the_traceability_matrix_heading_appears_once`
  (`roadmap.count("## Traceability matrix") == 1`); and `test_the_gaps2_readers`, a unit test
  of both readers on inline text that also asserts `_parse_roadmap` of a section holding only
  `**GAPS2 closed:**` returns `gaps == {}`.
- **TR-01.5 The allowlist.** Add `"GAPS2.md"` to `_ROOT_ALSO` (`test_packaging.py:411`),
  between `"GAPS.md"` and `"REMAINING.md"`, and `git add GAPS2.md` (no `-f`: it is not
  ignored).
- **TR-01.6 WP-28 in ROADMAP.md.** Insert after the `---` at 4241 and before
  `## Traceability matrix` (4243), ending with its own `---`. Heading `## WP-28 · Close the
  GAPS2 audit's 22 gaps` (no `— DONE`; section 19 appends it). Header line:
  `**GAPS2 closed:** B1, B2, B3, B5, B6, B7, C2, D1, E1, E2, E3, E14, F1, G1, G2, G3, G5, G6, G16, K2, X1, X2 · **Severity:** S1 (15), S2 (4), S3 (3) · **Effort:** L · **Depends on:** WP-27`.
  Then `> **User story.** As the Stata user pasting twoway syntax, I want the numbers, text
  and colours twoway draws, and twoway's refusals; as the maintainer, I want each of the 22
  audited defects closed by a regression test that failed before its fix.`, then
  `### Business requirements` BR-28.1..k, `### Technical requirements` TR-28.1..k,
  `### Acceptance criteria` AC-28.1..k, `### Test plan`, and `#### GAPS2 traceability` with a
  table `| Gap | Title | Sev | Effort | Closable | Section |` of 22 rows (titles shortened
  from GAPS2's headings; Sev/Effort/Closable from GAPS2's area tables: B1 S1 M yes S14; B2 S1
  M yes S18; B3 S1 S yes S13; B5 S1 M yes S15; B6 S1 S yes S13; B7 S1 S yes S13; C2 S1 S yes
  S05; D1 S1 S yes S06; E1 S1 M yes S04+S11; E2 S1 M yes S17; E3 S2 L yes S04+S11+S12; E14 S3
  M yes S10; F1 S1 S yes S09; G1 S1 M yes S07; G2 S2 S yes S08; G3 S2 M partly S08; G5 S2 S
  yes S07; G6 S3 M yes S04+S12; G16 S3 S yes S14; K2 S2 S yes S09; X1 S1 S yes S17; X2 S1 M
  partly S16). The BRs come from PRD §4-§5 (one per component group: display formats, axis
  labels and scales, textbox grammar, legend, histogram, schemes, colorvar, filters,
  presentation parity, serve and floor, data handling, silent-when-honoured, refusals with
  twoway's codes); the TRs from RESEARCH.md "Key architecture decisions" 1-6 and the
  cross-cutting mechanisms (copy lists, `function_test_map.py`, fixtures with `git add -f`,
  the node runner, the SVG helper); the ACs from PRD §8 (a failing-then-passing test per gap in
  both modes; the fixtures listed; both suites green under both interpreters with no skips;
  the gate green from an installed package; no open S1/S2; 22 closed entries naming tests;
  every Tracked line in scope naming its commit; CHANGELOG complete); the test plan names
  `test/test_tracking_documents.py::TestGaps2AndRoadmapAgree` as the closure check and the
  section files as the per-gap plans. **Inside WP-28 no line may begin with `# ` or `## `,
  and the text `## Traceability matrix` and the field `**Gaps closed:**` may not appear.**
- **TR-01.7 CHANGELOG stub.** Insert before `### Fixed after WP-27 (the S3 batch, 24sep2026)`
  (338), after `### Requirements`'s last line:

  ```
  ### Fixed in WP-28

  The 22 gaps of GAPS2.md (the audit of 25sep2026) that WP-28 closes, one
  line each, each ending with its gap in parentheses.

  Results that change:

  <!-- WP-28 B1 -->
  <!-- WP-28 B2 -->
  … one marker per gap, in this order: B1 B2 B3 B5 B6 B7 C2 D1 E1 E3 E14 G6 G16 X1 X2

  Changed behaviour (may need your do-files changed):

  <!-- WP-28 G1 -->
  <!-- WP-28 G2 -->

  Requirements:

  <!-- WP-28 K2 -->

  Fixed:

  <!-- WP-28 E2 -->
  <!-- WP-28 E14 served -->
  <!-- WP-28 F1 -->
  <!-- WP-28 G3 -->
  <!-- WP-28 G5 -->
  ```

  A section replaces its gap's marker with its line(s); E14 replaces both of its markers
  (the bs filter bar under "Results that change", the served items under "Fixed"). A
  "Results that change" line states the command, the old value and the new value (DISCOVERY
  Q20). Section 19 removes any marker left and fails if one is.
- **TR-01.8 The BUGS.md entry form** (every section's final task; parsed by `_ENTRY`,
  `_FIELD`, `_references`):

  ```
  - [x] Title: <what was wrong, one sentence, no double-quote character>
    - File Names and Line Numbers: <file>: `<function>' (<lines at 91d97be>)[; <file>: ...]
    - Description: GAPS2 <ID>. <the measured symptom: the command, what dash drew, what twoway draws, with the Stata rule's help/ado citation>
    - Suggested fix: <GAPS2's plan in one or two sentences>
    - Resolution (WP-28, <ID>): Fixed <ddmonyyyy>. <what changed, in which functions, in both renderers>. Pinned by test/<file>.py::<Class>::<test>[, test/<file>.cscript <CASE-ID>][; fixture test/fixtures/<name>.json]. [Residual, deferred (WP-28): <what stays and why>.]
  ```

  Rules: appended at the end of BUGS.md with one blank line before it; the four fields once
  each, in this order, each on one line or continued on lines indented four spaces; no other
  line begins `- ` inside the entry; the title holds no `"` (section 19 quotes it in GAPS2.md)
  and is unique; every `test_*.py`/`.cscript` name, `test_x.py::Class::test` node, `Test…`
  word and `AB-12` case id in the entry must exist on disk when the entry is committed (a
  cert case id must be displayed by its script); the entry lands closed, in the gap's fix
  commit; no `Graded` line (that is for open entries). The Resolution qualifier `(WP-28, <ID>)`
  is what section 19 counts and what `_GAPS2_CLOSED`'s cross-check reads.
- **TR-01.9 The commit-message form.** Subject: what now happens, as a sentence, ending with
  the gap id in parentheses, `… (GAPS2 B1)`; a shared-component commit ends with its section,
  `… (WP-28 S02)`. Body: the measured defect before the change (command, drawn value,
  twoway's value, the rule's citation); what changed and where (functions, both renderers,
  the copy lists); then one line each: `Regression: test/<file>.py::<Class>::<test> -- failed
  at 91d97be with <the wrong number or assertion text>`, `Flipped: <node> -- <old expectation>
  was wrong because <why>` (one per flipped test), `Fixture: test/fixtures/<name>.json
  (scripts/<extract script>)`, `BUGS.md: "<title>" (closed)`. No AI reference anywhere, no
  trailer naming a model or vendor (CLAUDE.md rule 6 governs; grep the message for
  `claude|anthropic` before and after committing). One commit per gap; a red tree is never
  committed (rule 4): the regression tests are written and run first, their failure text
  saved to the scratch directory, and they land in the fix commit that turns them green.
- **TR-01.10 Security (rule 1).** Nothing here reaches HTML, JS, a Bokeh field or `exec`;
  the readers use anchored regular expressions and `git cat-file -e` with a hex-validated
  argument, and `subprocess.run` with a list, never `shell=True`.

## Boundaries

- Do not open any BUGS.md entry (DISCOVERY Q4, amended): every entry lands closed in its
  fix commit. Do not touch BUGS.md at all in this section.
- Do not mark WP-28 DONE, do not write a `### Done, measured` block, and do not update any
  GAPS2.md `- **Tracked:**` line: those are section 19's.
- Do not edit GAPS.md, the `## Traceability matrix`, WP-01..27, or `_parse_roadmap`'s return
  value; do not rename or delete any test.
- Do not change `dash_render.py`, `dash.ado`, `dash_parse.mata`, `dash.sthlp`, `dash.pkg`
  or any shipped file; GAPS2.md is not shipped and is not added to `dash.pkg`.
- Do not renumber sections or edit `.ultraplan/sections/index.md`.
- Do not add C4/E4 to WP-28 (PRD §7); the CHANGELOG stub has no marker for them.

## Stata truth

None. This section runs no Stata and adds no fixture or extract script.

## TDD test stubs

All in `test/test_tracking_documents.py`, class `TestGaps2AndRoadmapAgree`, written by task
01-01. Each fails at `91d97be` for the reason given.

- **Test: `test_the_gaps2_readers`** — inline text with two headings, a Closed line, a
  Deferred line and an open `new.` line; asserts the dict shapes, and that `_parse_roadmap`
  of a `**GAPS2 closed:**`-only section returns `{"done": False, "gaps": {}}`. Pre-fix
  failure: `NameError: name '_parse_gaps2' is not defined`.
- **Test: `test_every_gaps2_id_a_package_declares_has_a_heading`** — after task 01-03,
  every id of WP-28's field has a heading in GAPS2.md. Pre-fix failure: `NameError` on
  `_parse_roadmap_gaps2`.
- **Test: `test_every_gaps2_id_a_done_package_lists_is_closed_by_it`** — vacuous until
  section 19 writes `— DONE`; then every id's Tracked line must be `Closed in WP-28, …`.
  Assert on inline text as well, so the test has a failing case at 91d97be: a DONE package
  listing an id whose Tracked line is `new.` must be reported.
- **Test: `test_every_closed_gaps2_entry_is_listed_by_its_package`** — the reverse direction,
  on the documents and on inline text.
- **Test: `test_every_closed_gaps2_entry_names_a_closed_bugs_entry_and_a_commit`** — on the
  documents (no Closed line exists yet, so it passes vacuously on the documents) and on inline
  text with a title no entry has, which must be reported.
- **Test: `test_a_deferred_gaps2_entry_names_its_package_and_a_reason`** — inline
  `Deferred (WP-28): out of scope` passes; `Deferred: x` (no package) is reported.
- **Test: `test_the_traceability_matrix_heading_appears_once`** — `roadmap.count(...) == 1`;
  passes at 91d97be and pins hazard (2) for every later edit.
- **Test: `test_packaging.py::test_the_package_root_holds_only_what_ships_and_the_repositorys_own`**
  (existing) — fails at 91d97be once `git add GAPS2.md` is run: `stray: GAPS2.md`. This is
  the regression record for TR-01.5.

Pinned tests to flip: none.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| The readers parse headings, Tracked lines and the new field | pytest, `TestGaps2AndRoadmapAgree::test_the_gaps2_readers` | inline text | n/a |
| WP-28's 22 ids resolve in GAPS2.md | pytest, `…::test_every_gaps2_id_a_package_declares_has_a_heading` | ROADMAP.md, GAPS2.md | n/a |
| A DONE package's ids are closed by it, both directions | pytest, the two `…_is_closed_by_it` / `…_is_listed_by_its_package` tests | inline + documents | n/a |
| A Closed line names a real closed BUGS.md entry and a real commit | pytest, `…::test_every_closed_gaps2_entry_names_a_closed_bugs_entry_and_a_commit` | inline + documents, git | n/a |
| The matrix split point is unique | pytest, `…::test_the_traceability_matrix_heading_appears_once` | ROADMAP.md | n/a |
| GAPS2.md is allowed at the root | pytest, `test_packaging.py::test_the_package_root_holds_only_what_ships_and_the_repositorys_own` | git ls-files | n/a |
| Nothing existing changed | `python3 -m pytest test/test_tracking_documents.py test/test_packaging.py -q`, then the full suite before each commit | — | n/a |

Acceptance criteria:

- **AC-01.1** `git ls-files GAPS2.md` prints the file, and the packaging root test passes.
- **AC-01.2** `ROADMAP.md` has one `## WP-28 · …` section before `## Traceability matrix`,
  not headed DONE, with a `**GAPS2 closed:**` field of 22 ids, no `**Gaps closed:**` field,
  and a `#### GAPS2 traceability` table of 22 rows; `grep -c '## Traceability matrix' ROADMAP.md`
  prints 1.
- **AC-01.3** `python3 -m pytest test/test_tracking_documents.py -q` passes with 7 more tests
  than at 91d97be (26 → 33 test functions in the file), none skipped.
- **AC-01.4** `CHANGELOG.md` holds `### Fixed in WP-28` with 23 `<!-- WP-28 … -->` markers
  (22 gaps, E14 twice, C4/E4 none).
- **AC-01.5** The full suite is green under `python3 -m pytest test/ -q` before each of the
  two commits; no commit message mentions an AI.

## Tasks

<task type="auto" id="01-01">
  <name>Write the failing tracking tests]]></name>
  <files>test/test_tracking_documents.py</files>
  <action><![CDATA[
    In `/Users/billy/Desktop/Programs/StataPrograms/d/dash/test/test_tracking_documents.py`,
    append the class `TestGaps2AndRoadmapAgree` with the seven tests named under "TDD test
    stubs", exactly those names, using the fixture keys `docs["gaps2"]`, `docs["gaps2_dupes"]`
    and `docs["wps2"]` and the reader names `_parse_gaps2` and `_parse_roadmap_gaps2` (not
    yet defined). Give each document-level test an inline-text case too, so it has a failure
    to show on a tree where the documents are still vacuous. Extend the module docstring's
    numbered list with item 7: "GAPS2.md (the audit of 91d97be) and ROADMAP.md agree: a
    package's **GAPS2 closed:** ids have headings; a DONE package's ids carry a Tracked line
    'Closed in WP-nn, BUGS.md "title", commit sha' naming it, a closed BUGS.md entry and a
    commit that exists, and every such Tracked line is listed by its package." Do not define
    the readers in this task. Run `python3 -m pytest test/test_tracking_documents.py -q -k
    Gaps2 2>&1 | tail -15` against the unmodified readers and save the output to the scratch
    directory as `01-01-failure.txt`; every test in the class must fail with NameError. Do not
    commit: a red tree is never committed (CLAUDE.md rule 4); this text becomes the first
    paragraph of task 01-02's commit body.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_tracking_documents.py -q -k Gaps2 2>&1 | tail -3` reports 7 failed, 0 passed, and `python3 -m pytest test/test_tracking_documents.py -q -k "not Gaps2" 2>&1 | tail -1` still reports every existing test passing.]]></verify>
  <done>Seven new tests exist under `TestGaps2AndRoadmapAgree`, all failing with NameError on the unmodified readers, and every pre-existing test in the file still passes.</done>
</task>

<task type="auto" id="01-02">
  <name>Teach the tracking guards GAPS2.md and commit the audit</name>
  <files>test/test_tracking_documents.py, test/test_packaging.py, GAPS2.md</files>
  <action>
    Implement TR-01.2 and TR-01.3 in `test/test_tracking_documents.py` immediately after
    `_parse_roadmap` (645): `_GAPS2_HEADING`, `_GAPS2_TRACKED`, `_GAPS2_CLOSED`,
    `_GAPS2_DEFERRED`, `_parse_gaps2(text)`, `_wp_sections(text)` and `_parse_roadmap_gaps2(text)`;
    rewrite `_parse_roadmap` to iterate `_wp_sections` so its returned dictionaries are
    byte-for-byte what they were (run `test_the_roadmap_reader` to prove it). Extend the `docs`
    fixture (648-654) with `gaps2`, `gaps2_dupes` (from `_parse_gaps2(_read("GAPS2.md"))`) and
    `wps2`. The BUGS.md cross-check reuses the `bugs` fixture's entries: match the quoted title
    to exactly one entry, require `e["closed"]` and `"(%s, %s)" % (wp, gid)` in
    `e["fields"]["Resolution"]`. The commit check calls `_git("cat-file", "-e", sha + "^{commit}")`
    only after `re.fullmatch(r"[0-9a-f]{7,40}", sha)`. Add `"GAPS2.md"` to `_ROOT_ALSO` in
    `test/test_packaging.py:413` and run `git add GAPS2.md`. Then `git merge --no-edit main`
    (expected "Already up to date"), run the full suite once, `python3 -m pytest test/ -q`,
    and commit the three files with the subject `Teach the tracking guards GAPS2.md, and
    commit the audit (WP-28 S01)`, the body opening with 01-01's failure text, then the two
    directions the guard now checks, then `Regression: test/test_tracking_documents.py::TestGaps2AndRoadmapAgree`.
  </action>
  <verify><![CDATA[`python3 -m pytest test/test_tracking_documents.py test/test_packaging.py -q 2>&1 | tail -2` passes with no skip; `git ls-files GAPS2.md` prints `GAPS2.md`; `git log -1 --format=%B | grep -ci 'claude\|anthropic'` prints 0; `git status --porcelain -- test GAPS2.md` is empty.]]></verify>
  <done>The readers exist, the seven tests pass, `_parse_roadmap`'s output is unchanged, GAPS2.md is tracked and allowed at the root, and one commit on `s3-bugs` holds all of it.</done>
</task>

<task type="auto" id="01-03">
  <name>Open WP-28 in ROADMAP.md and stub the CHANGELOG</name>
  <files>ROADMAP.md, CHANGELOG.md</files>
  <action>
    Insert the WP-28 section of TR-01.6 into `/Users/billy/Desktop/Programs/StataPrograms/d/dash/ROADMAP.md`
    after the `---` at 4241 and before `## Traceability matrix` at 4243, ending with `---` and
    a blank line; write the user story, BR-28.1..k, TR-28.1..k, AC-28.1..k and the test plan
    from the sources TR-01.6 names, and the `#### GAPS2 traceability` table with the 22 rows
    given there. Check the hazards before saving: no line of the new text begins `# ` or
    `## ` except its own heading; the strings `Gaps closed` and `## Traceability matrix` do
    not occur in it; the heading has no `— DONE`. Insert the `### Fixed in WP-28` stub of
    TR-01.7 into `CHANGELOG.md` before line 338, `### Fixed after WP-27 (the S3 batch, 24sep2026)`,
    with its 23 markers. Run `python3 -m pytest test/test_tracking_documents.py -q`, then
    `git merge --no-edit main` and the full suite `python3 -m pytest test/ -q`, and commit the
    two files with the subject `Open WP-28: the 22 GAPS2 gaps, their sections and their
    CHANGELOG place (WP-28 S01)`, the body naming the 22 ids by severity and the conventions
    (BUGS.md entry form, commit form) this section file records.
  </action>
  <verify><![CDATA[`grep -c '^## WP-28 ' ROADMAP.md` prints 1 and `grep -c '## Traceability matrix' ROADMAP.md` prints 1; `awk '/^## WP-28 /,/^## Traceability matrix/' ROADMAP.md | grep -c 'Gaps closed'` prints 0; `awk '/^## WP-28 /,/^## Traceability matrix/' ROADMAP.md | grep -c '^| [A-KX][0-9]* |'` prints 22; `grep -c '<!-- WP-28 ' CHANGELOG.md` prints 23; `python3 -m pytest test/test_tracking_documents.py -q 2>&1 | tail -1` passes; `git log -1 --format=%B | grep -ci 'claude\|anthropic'` prints 0.]]></verify>
  <done>WP-28 is open in ROADMAP.md with its 22-row GAPS2 traceability table and no DONE mark, the CHANGELOG has a marker per gap under `### Fixed in WP-28`, the tracking tests read them, and the second commit of this section is on `s3-bugs`.</done>
</task>

## Section completion criteria

- Two commits on `s3-bugs`, each after a green full run, neither mentioning an AI.
- `test/test_tracking_documents.py` has `TestGaps2AndRoadmapAgree` (7 tests) and every
  previous test unchanged; `test/test_packaging.py` allows `GAPS2.md`; `GAPS2.md` is tracked.
- `ROADMAP.md` has WP-28 (not DONE) with `**GAPS2 closed:**` of 22 ids and a 22-row
  `#### GAPS2 traceability` table; `CHANGELOG.md` has `### Fixed in WP-28` with 23 markers.
- The BUGS.md entry form (TR-01.8), the CHANGELOG line rule (TR-01.7) and the commit form
  (TR-01.9) are recorded here for sections 05-18 and 19 to copy.

## Notes

- **Never write `**Gaps closed:**` in WP-28.** Once section 19 writes `— DONE`, the old
  reader would look those ids up in GAPS.md and fail with "GAPS.md says …". Only
  `**GAPS2 closed:**`.
- **No `# ` or `## ` at the start of any line inside WP-28**, including inside fenced code:
  `_parse_roadmap` (630-631) ends the section there, and the field would go unread.
- **`_CASE_ID` matches `WP-28`** (`[A-Z]{1,6}-\d{1,3}`); that is harmless (an unknown case id
  is neither found nor dangling), so `(WP-28, B1)` in a Resolution is safe. A `Test…` word or
  a `test_*.py` name that does not exist is *not* harmless: `test_no_entry_names_a_test_that_does_not_exist`
  fails. Sections must name only tests that exist in the same commit.
- **A BUGS.md title with a `"` cannot be quoted in a Tracked line** (`[^"]+`); use Stata's
  `\`x'` quoting or plain words in titles.
- **Parallel merges.** Batch-1 sections append to BUGS.md and CHANGELOG.md concurrently, so
  `patch -p1` of a worktree's diff may reject those hunks (`.rej` files). Apply them by hand:
  BUGS.md entries in section order at the end of the file, CHANGELOG lines in place of their
  markers. Never resolve by dropping an entry.
- **The CHANGELOG markers are HTML comments** so the stub renders as nothing; section 19
  fails the closeout if any `<!-- WP-28 ` marker survives.
- **GAPS2.md needs no `git add -f`** (`git check-ignore` returns 1); fixtures under
  `test/fixtures/*.json` do (`.git/info/exclude` hides `*.json`).
- **Two full runs in this section** (one per commit). The PreToolUse hook allows two free
  full launches per session; if a third is needed, prefix the command with
  `FULL_SUITE_RERUN=1` and say why in the report. Never launch a full run while one is
  executing; read its log.
