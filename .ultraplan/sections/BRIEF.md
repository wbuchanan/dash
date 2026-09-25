# Writing brief for WP-28 section files

Every section file in this directory is written to this standard so any developer or agent can build and ship it correctly the first time (CLAUDE.md rule 9). Where a section's text and a rule here disagree, `review/DECISIONS.md` wins, then this brief.

## Inputs (read all before writing)

1. `.ultraplan/PRD.md` — approved requirements; §4 names the gap groups, §7 the exclusions and residuals.
2. `.ultraplan/DISCOVERY.md` — decisions Q1-Q31 (Q24-Q31 are the Phase 4 refinement answers) and the four research amendments. A section must not contradict them.
3. `.ultraplan/RESEARCH.md` — merged findings; then the detailed report(s) named for your section in `.ultraplan/research/`.
4. `GAPS2.md` — the entry for each gap the section closes (`grep -n '^### B1\.' GAPS2.md`, read through the next `### `). Its **Gap**, **Closable** and **Plan** lines are the requirement; its file:line anchors were re-verified in the research reports (use the research anchors when they differ).
5. `.ultraplan/sections/index.md` — the manifest (section number, name, gaps, batch, dependencies), step 0 (`scripts/stata_slot.sh`, the cert baseline), the batch merge orders, the merge rules R1-R6 and the copy-list anchor table. Do not renumber.
6. `.ultraplan-archive-20260925/sections/section-02-the-mask-mechanism.md` — the style exemplar for depth and voice (evidence with anchors and code excerpts, boundaries, TDD stubs, XML tasks).
7. The XML task schema below (review D7). The maintainer's `ultraplan` skill keeps a reference named `xml-task-format.md`; it is not available to executors, and the block here is authoritative for WP-28.
8. `CLAUDE.md` — project rules, especially 1 (security), 3 (a unit test per function, end-to-end tests), 4 (a red tree is never committed), 7 (a failing regression test before every fix), 10 (Stata invocation), 11 (pytest invocation).
9. `.ultraplan/review/DECISIONS.md` — D1-D14, how the Phase 4 review's contested points are resolved; a decision there wins over any section text.

## XML task schema (D7)

```
<task type="auto|checkpoint" id="NN-MM">
  <name>3 to 8 words, starting with a verb</name>
  <files>path[, path[, path]]</files>          <!-- at most 3 paths; or the word none -->
  <action><![CDATA[ 2-6 sentences: what to do, where, how; a new file is said here ("Create …") ]]></action>
  <verify><![CDATA[ the command(s) and the exact expected output ]]></verify>
  <done>One past-tense sentence stating what became true.</done>
</task>
```

Ids are `NN-01, NN-02, …`, sequential, no gaps, no letter suffixes. A `checkpoint` task has `<files>none</files>` and asks the maintainer to approve something (D8). Every `<action>` names files, functions, line anchors and the exact rule; "etc.", "and so on" and "the way the repo does" are not allowed. Any `<action>`, `<verify>` or `<done>` holding `&`, `<` or `>` is wrapped in `<![CDATA[ … ]]>`, never entity-escaped; `<name>` and `<files>` hold no such characters.

## File layout (in this order)

```
# Section NN: <name>

> Part of: WP-28 · Gaps: <ids> · Risk: <colour> · Batch: <n> · Depends on: <sections> · Blocks: <sections> · Tasks: n, k commits

## Review amendments    the binding Phase 4 block, kept; its closing sentence says the fixer pass applied the reviews
## Overview            plain English, 2-4 paragraphs: what is wrong today (quote GAPS2's measured symptom), what will be true after, why these gaps share this section; then the "Test order and commit rule" paragraph
## Risk: [<colour>] — <one line>      then Why / Risk factors / Mitigation
## Dependencies        Depends on / Blocks / Parallel batch / Can run with; one sentence on why
## Evidence            the current code, with dash_render.py / dash.ado / dash_parse.mata anchors and 3-10 line excerpts, taken from the research reports; the Stata rule with its help/ado citation; the fixtures on disk; the existing tests that pin today's behaviour (these MUST be listed by file::Class::test so the executor flips them, never deletes them)
## User stories        US-NN.k "As a <PRD §3 persona>, I want … so that …" — one per user-visible behaviour
## Business requirements   BR-NN.k — what must be true for the user, testable, no implementation words
## Technical requirements  TR-NN.k — how, naming functions, files, keys, both renderers, the served copy lists (with the anchor each entry goes after), function_test_map.py, JS twins
## Boundaries          what this section must NOT touch (other sections' functions; the PRD §7 exclusions; the decisions in DISCOVERY)
## Stata truth         exactly which extract script/probes/fixture keys this section adds (or "none"), with the twoway command lines, the `scripts/stata_slot.sh` run (it implements CLAUDE.md rule 10 and the STATATMP rule), the `_meta` stamp (D12) and the `git add -f` note for fixtures
## TDD test stubs      one line each, "Test: …", file::Class::test_name, both modes where a page exists; the FIRST stubs are the regression tests that fail at 91d97be; list the pinned tests to flip
## Test plan           table: what | how (pytest / cscript block / node / Chrome) | fixture | both modes? — plus the acceptance criteria AC-NN.k
## Tasks               opens with a "Commit boundary" paragraph naming which tasks form which gap's commit and the subject suffix; then XML tasks per the schema above; task 1 writes the failing tests, runs them against the unmodified tree, saves the failure text to <scratch>/NN-01-failure.txt and never commits; 1-3 files per task; ordered; tasks are steps, commits are per gap (D1); the closing task of each gap closes the BUGS.md entry (D3 form, naming the tests), updates dash.sthlp, replaces the gap's `<!-- WP-28 <ID> -->` CHANGELOG marker(s) in place (D2) and makes the gap's one commit
## Section completion criteria
## Notes               traps for the executor (renderer order differences, copy lists, fixture exclude rules, python_exec hazard); cites merge rules R1-R6 by number for the shared files touched; states the commit-body line forms
```

## Rules of content

- **Anchors are current.** Cite `file:line` from the research reports (checked at `91d97be`); say "about" only where research says the number may drift.
- **Both renderers, every time.** Any change in `dash_render.py` that the served app must share names the copy list (constants 24326-24428, functions 24466-24687) and the served template call site, and says which existing entry the new name goes after (the anchor table under `index.md` R2). A new function is added to `test/function_test_map.py`, a new Stata program to `test/program_coverage_map.py`, in alphabetical place.
- **Failing test first.** Task NN-01 writes every regression test for the section, runs it against the unmodified tree, saves the failure text to `<scratch>/NN-01-failure.txt` and does NOT commit (rule 4). That text opens the gap's fix commit body and is the old value the gap's CHANGELOG line quotes (Q24). Later tasks turn the tests green; pinned tests that assert today's wrong behaviour are flipped in the fix commit with the reason, never deleted.
- **One commit per gap; tasks are steps, not commits (D1).** Each gap's failing tests, its fix, its flipped tests, its fixture and its closed BUGS.md entry are one commit, made by the gap's closing task on the section's worktree branch `wp28-s<NN>` after the full suite ran green once in that worktree (`python3 -m pytest test/ -q`); the merger lands it on `s3-bugs` with the recorded message (`index.md` step 1). Subjects end `(GAPS2 <ID>)`; S01-S04 commit once each and S19 once per step with `(WP-28 Snn)`. A section with several gaps commits once per gap and repeats the cycle per gap: the first gap's failing tests are written by task 1 against the unmodified tree, the next gap's against the tree the previous gap's commit leaves (unmodified at that gap's sites), each followed by its fix and its one commit, so no commit is ever red (S07, S08, S09, S13, S14, S17). No test-only commit ever exists.
- **Commit bodies (S01 TR-01.9, verbatim forms).** The body opens with the saved failure text, then the measured defect, then what changed and where, then one line each: `Regression: test/<file>.py::<Class>::<test> -- failed at 91d97be with <text>`, `Flipped: <node> -- <old expectation> was wrong because <why>` (one per flip), `Fixture: test/fixtures/<name>.json (scripts/<extract script>)`, `BUGS.md: "<title>" (closed)`.
- **BUGS.md entry (D3, S01 TR-01.8, verbatim).** Closed form appended at the END of BUGS.md: `- [x] Title:` (no `"` in the title) / File Names and Line Numbers / Description / Suggested fix / `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). <what changed, in which functions, in both renderers>. Pinned by test/<file>.py::<Class>::<test>[, test/<script>.cscript <CASE-ID>][; fixture test/fixtures/<name>.json]. [Residual, deferred (WP-28): <what and why>.]` The WP and gap id are inside the text; the field name is exactly `- Resolution:`, never with a parenthetical on it.
- **CHANGELOG (D2, S01 TR-01.7).** S01 places one `<!-- WP-28 <ID> -->` marker per gap in the release's existing lists -- the `**WP-28 (GAPS2 audit, 25sep2026)**` group at the end of `### Results that change`, the ends of `### Changed behaviour (may need your do-files changed)` and `### Requirements` -- and under a new `### Fixed in WP-28` heading (E14 has one in two places). A gap's closing task replaces only its own marker(s), in place, with line(s) ending `(WP-28, <ID>)` and adds nothing anywhere else; a Results line names the command, the old value and the new; S04's lines go under `### Fixed in WP-28` ending `(WP-28 S04)`.
- **Certification scripts (D11, C7).** One new script only, `test/test_gaps2_truth.cscript`, created and registered by S02 as runner block `// 67.` with the hygiene pins set to 66 and 48 (:292, :308; :315 if it has import probes); no other section touches the runner or the pins. Every later comparison with twoway's drawing or Stata's own values is a block appended above the script's last line `* ==== append new blocks above this line ====`, in section order (R1), of this form (fixer pass, 2026-09-25), so `GAPS2_ONLY=S<NN>` runs one block and S19 times each:

  ```
  * ==== S<NN> <ID>: <what> ====
  local only : env GAPS2_ONLY
  if inlist("`only'", "", "S<NN>") {
      display as text "S<NN> start `c(current_time)'"
      ... the cases, each displaying `<CASE-ID> PASS` ...
      display as text "S<NN> end `c(current_time)'"
  }
  * ==== end S<NN> ====
  ```

  Refusal, message, return-code and setup checks join the existing script for their area (C7's list: F1 → `test_serve_launch.cscript`; K2 → `test_setup_honesty.cscript`, `test_setup_python_gate.cscript`; G1 → `test_qualifier_in_stata.cscript`; G5 → `test_statistical_options.cscript`; G2, G3 → `test_adversarial.cscript`; D1 → `test_custom_scheme.cscript`; C2/X1/E2 page counts → `test_e2e_filters.cscript`). Case ids keep their section prefixes. No section adds a `SKIP…Python` line to a script that has none.
- **Running one cscript (fixer pass, 2026-09-25; `index.md` step 0a).** A cscript is never handed to `scripts/stata_slot.sh` itself (the runner `cd`s into `test/` first and the scripts open `cscript … adodir ".."` and `do "cert_helpers.do"` relative to it): write a two-line driver `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "<repo>" "<repo>" "<script>.cscript" > <scratch>/run_<script>.do` and run `scripts/stata_slot.sh <scratch> <scratch>/run_<script>.do` (log `<scratch>/run_<script>.log`; `<repo>` is the root of the tree under test: the section's worktree `<path>/wp28-s<NN>` while the section runs there, and the main checkout `/Users/billy/Desktop/Programs/StataPrograms/d/dash` when the merger or section 19 runs). An extract script under `scripts/` is run directly only if its own text sets its directories.
- **Fixtures (D12, R5).** Written by a `scripts/extract_*_truth.do` script into `test/fixtures/<name>_truth.json`; `_meta` holds `stata_version`, `born_date`, `dash_commit` and `extracted` (the do-file captures `git rev-parse HEAD` with `shell` into a local; the python block reads it through `Macro.getLocal`, never calls Stata and never uses `shell=True`; the section's fixture test asserts the four keys exist); existing `_meta` keys stay; the python block writes a backtick as `\x60`; `git add -f` the fixture; a test names it (`test_fixtures_are_committed.py`). A regenerated fixture is never patched by hand and is verified probe by probe outside `_meta` ("every pre-existing probe's records are unchanged"), never as "additions only".
- **Silent when honoured** (DISCOVERY Q22): once an option is drawn, nothing is printed; only options still not drawn are named through `_dash_report_suboptions`.
- **Refusals use Stata's codes**: r(109) string variables, r(110) reserved names, r(198) invalid syntax/format, r(134) limits.
- **Stata invocation**: only through `scripts/stata_slot.sh <scratch-dir> <file>.do` (`index.md` step 0: three `mkdir` slots, `STATATMP=<scratch-dir>/tmp/`, the console binary of CLAUDE.md rule 10), never the GUI, never a bare `arch -arm64 … -b do` inside a task; the wrapper is what keeps concurrent Stata sessions at three. A full `make cert` or release-gate run is never launched inside a section (S19 only).
- **pytest invocation**: only the changed files while iterating; the full suite once before the commit as `python3 -m pytest test/ -q`.
- **Security (rule 1)**: any text reaching HTML or JS is escaped; any name reaching a Bokeh field passes the name check; no `shell=True`; no user text in `exec`/`eval`; bounded lengths where text is echoed.
- **No AI references** anywhere in commit messages, BUGS.md entries, CHANGELOG or help text.
- **Shared files within a batch** follow the merge rules R1-R6 in `index.md`; every section's Notes cite them by number for the shared files it touches.
- **`<done>` is past tense** (D7; feasibility #4's present-tense proposal is not taken).
- **Length**: as long as it needs to be for an executor with no other context, and no longer. The exemplar is 400-600 lines.
