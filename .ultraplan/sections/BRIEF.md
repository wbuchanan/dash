# Writing brief for WP-28 section files

Every section file in this directory is written to this standard so any developer or agent can build and ship it correctly the first time (CLAUDE.md rule 9).

## Inputs (read all before writing)

1. `.ultraplan/PRD.md` — approved requirements; §4 names the gap groups, §7 the exclusions.
2. `.ultraplan/DISCOVERY.md` — the 23 decisions and the four research amendments. A section must not contradict them.
3. `.ultraplan/RESEARCH.md` — merged findings; then the detailed report(s) named for your section in `.ultraplan/research/`.
4. `GAPS2.md` — the entry for each gap the section closes (`grep -n '^### B1\.' GAPS2.md`, read through the next `### `). Its **Gap**, **Closable** and **Plan** lines are the requirement; its file:line anchors were re-verified in the research reports (use the research anchors when they differ).
5. `.ultraplan/sections/index.md` — the manifest: section number, name, gaps, batch, dependencies. Do not renumber.
6. `.ultraplan-archive-20260925/sections/section-02-the-mask-mechanism.md` — the style exemplar for depth and voice (evidence with anchors and code excerpts, boundaries, TDD stubs, XML tasks).
7. `/Users/billy/.claude/skills/ultraplan/references/xml-task-format.md` — the task schema.
8. `CLAUDE.md` — project rules, especially 1 (security), 3 (a unit test per function, end-to-end tests), 7 (a failing regression test before every fix), 10 (Stata invocation), 11 (pytest invocation).

## File layout (in this order)

```
# Section NN: <name>

> Part of: WP-28 · Gaps: <ids> · Risk: <colour> · Batch: <n> · Depends on: <sections> · Blocks: <sections>

## Overview            plain English, 2-4 paragraphs: what is wrong today (quote GAPS2's measured symptom), what will be true after, why these gaps share this section
## Risk: [<colour>] — <one line>      then Why / Risk factors / Mitigation
## Dependencies        Depends on / Blocks / Parallel batch / Can run with; one sentence on why
## Evidence            the current code, with dash_render.py / dash.ado / dash_parse.mata anchors and 3-10 line excerpts, taken from the research reports; the Stata rule with its help/ado citation; the fixtures on disk; the existing tests that pin today's behaviour (these MUST be listed by file::Class::test so the executor flips them, never deletes them)
## User stories        US-NN.k "As a <PRD §3 persona>, I want … so that …" — one per user-visible behaviour
## Business requirements   BR-NN.k — what must be true for the user, testable, no implementation words
## Technical requirements  TR-NN.k — how, naming functions, files, keys, both renderers, the served copy lists, function_test_map.py, JS twins
## Boundaries          what this section must NOT touch (other sections' functions; the PRD §7 exclusions; the decisions in DISCOVERY)
## Stata truth         exactly which extract script/probes/fixture keys this section adds (or "none"), with the twoway command lines, the Stata invocation pattern from CLAUDE.md rule 10, the STATATMP rule, and the `git add -f` note for fixtures
## TDD test stubs      one line each, "Test: …", file::Class::test_name, both modes where a page exists; the FIRST stubs are the regression tests that fail at 91d97be; list the pinned tests to flip
## Test plan           table: what | how (pytest / cscript / node / Chrome) | fixture | both modes? — plus the acceptance criteria AC-NN.k
## Tasks               XML tasks per xml-task-format.md; task 1 writes the failing tests; 1-3 files per task; ordered; tasks are steps (commits are per gap, review D1); the final task closes the BUGS.md entry (closed form, naming the test), updates dash.sthlp, and replaces the gap's `<!-- WP-28 <ID> -->` CHANGELOG marker(s) that S01 placed in the list where the entry belongs (review D2)
## Section completion criteria
## Notes               traps for the executor (renderer order differences, copy lists, fixture exclude rules, python_exec hazard, etc.)
```

## Rules of content

- **Anchors are current.** Cite `file:line` from the research reports (checked at `91d97be`); say "about" only where research says the number may drift.
- **Both renderers, every time.** Any change in `dash_render.py` that the served app must share names the copy list (constants 24326-24428, functions 24466-24687) and the served template call site. A new function is added to `test/function_test_map.py`.
- **Failing test first.** Task NN-01 writes every regression test for the section, runs it against the unmodified tree, and records the failure in the commit message. Later tasks turn them green.
- **One commit per gap; tasks are steps, not commits (review D1).** The failing regression tests are written first (rule 7) and run against the unmodified tree, and their output at 91d97be is recorded in the fix commit's message and quoted as the old value in CHANGELOG; they are committed together with the fix that turns them green, never alone (rule 4: a red tree is never committed). Each gap's fix, its flipped tests and its BUGS.md entry (closed form: `- [x] Title:` / File Names and Line Numbers / Description / Suggested fix / `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). <what changed>. Pinned by test/<file>::<Class>::<test>.`, appended at the end of BUGS.md) are one commit. S01-S04 are one commit each.
- **Silent when honoured** (DISCOVERY Q22): once an option is drawn, nothing is printed; only options still not drawn are named through `_dash_report_suboptions`.
- **Refusals use Stata's codes**: r(109) string variables, r(110) reserved names, r(198) invalid syntax/format, r(134) limits.
- **Fixtures**: written by a `scripts/extract_*_truth.do` or `.py` script into `test/fixtures/<name>_truth.json`; the trailing `python:` block never calls Stata and writes a backtick as `\x60`; `git add -f` the fixture; a test names it (`test_fixtures_are_committed.py`).
- **Stata invocation**: only through `scripts/stata_slot.sh <scratch-dir> <file>.do` (review D6; it runs `cd <dir> && STATATMP=<dir>/tmp/ arch -arm64 /usr/local/bin/stata-mp -b do <file>.do` under one of three lock slots), never the GUI; the wrapper is what keeps concurrent Stata sessions at three. A full `make cert` or release-gate run is never launched inside a section (S19 only).
- **pytest invocation**: only the changed files while iterating; the full suite once before commit as `python3 -m pytest test/ -q`.
- **Security (rule 1)**: any text reaching HTML or JS is escaped; any name reaching a Bokeh field passes the name check; no `shell=True`; no user text in `exec`/`eval`.
- **No AI references** anywhere in commit messages, BUGS.md entries, CHANGELOG or help text.
- **Shared files within a batch** follow the merge rules R1-R6 in `index.md`.
- **XML text**: any `<action>`, `<verify>` or `<done>` holding `&`, `<` or `>` is wrapped in `<![CDATA[ … ]]>`, never entity-escaped.
- **Length**: as long as it needs to be for an executor with no other context, and no longer. The exemplar is 400-600 lines.
