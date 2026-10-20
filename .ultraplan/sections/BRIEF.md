# Writing brief for the WP-33..WP-50 section files

Every section file in this directory is written to this standard so the least
capable coding agent builds and ships it correctly the first time (CLAUDE.md
rule 8). Order of precedence: `review/DECISIONS.md` (Phase 4 rulings) >
`index.md` > this brief > the section file. This brief is WP-31's brief
(archived at `.ultraplan-archive-20261020/sections/BRIEF.md`) with the GAPS4
register, the `NN-MM` section ids and the 20oct2026 rulings substituted.

## Inputs (read all before writing or executing)

1. `.ultraplan/sections/index.md` -- the manifest (section, slug, items, batch,
   dependencies, risk, JS flag, owned hot functions), the decision record
   (M1-M14 maintainer rulings, PD-1..PD-18 architect decisions), the batch
   procedure (k.0-k.7), the WP start/end steps (W0, WE), merge rules R1-R14,
   gates G1-G4, Appendix A (every item: lead id, other ids, Sev, Kind) and
   Appendix B (the false-sentence checklist). Do not renumber.
2. `.ultraplan/PRD.md` -- the approved requirements; §7 the exclusions.
3. `.ultraplan/DISCOVERY.md` -- the maintainer's answers Q1-Q58 and amendments
   A1-A3. A section must not contradict them.
4. `.ultraplan/RESEARCH.md` (conflicts C1-C5 resolved) and the three reports:
   `research/codebase-mechanics.md` [C] (per-package code map with anchors at
   `090d928`, tracking/cscript machinery, gallery mechanics, dash-only words),
   `research/stata-ground-truth.md` [S] (corpus, SVG export, zero
   observations, ts operators, dash-only words, twoway__contour_gen,
   aspectratio, a(b)c) and `research/bokeh-web.md` [B] (SVG export, verdict
   machinery, item-by-item Bokeh models for P6-P10, P1-5, WebGL, SMCL runs,
   legend keys). Cite them by letter and heading.
5. `.ultraplan/review/DROPIN-AUDIT-19oct2026.md` -- the item's bullet in its
   package (title, ids, Evidence, Fix) and every appendix finding that carries
   one of the item's ids (twoway's behaviour, dash's behaviour, evidence,
   verifier). The item's audit text is the requirement unless a ruling
   narrows it.
6. The code itself, at the anchors [C] gives. Re-read before citing: anchors
   drift by a few lines.
7. `CLAUDE.md` -- rules 1 (honesty), 2 (full suite only at batch end), 3 (a
   unit test per function), 4 (pull before commit), 6 (no tooling names in
   commit messages), 7 (a failing regression test before every fix), 9
   (Stata only as `arch -arm64 /usr/local/bin/stata-mp -b do`, through
   `scripts/stata_slot.sh`), 10 (targeted pytest while iterating).

## Banned topics (index R14; maintainer rulings M1, M2, A1)

Never list heatmap or sunflower as a twoway plot type; never mention
matamatrix() except where PD-10 removes it; never reference Stata editions or
edition limits (restate any limit -- c(macrolen), c(maxvar) -- without naming
an edition); never add a browser other than Chrome. Contour's own `heatmap`
option is in scope.

## XML task schema

```
<task type="auto|checkpoint" id="NN-MM-KK">
  <name>3 to 8 words, starting with a verb</name>
  <files>path[, path[, path]]</files>          <!-- at most 3 PRIMARY paths, or none; the tracking documents (BUGS.md, GAPS4.md, CHANGELOG.md, TWOWAY_COVERAGE_AUDIT.md, dash.sthlp's Unsupported list), the test maps and the flipped tests a closing task edits are implied -->
  <action><![CDATA[ 2-6 sentences: what to do, where, how; a new file is said here ("Create ...") ]]></action>
  <verify><![CDATA[ the command(s) and the exact expected output ]]></verify>
  <done>One past-tense sentence stating what became true.</done>
</task>
```

Task ids are `NN-MM-01, NN-MM-02, ...` (e.g. `34-02-03`), sequential, no gaps.
A `checkpoint` task has `<files>none</files>` and asks the maintainer to
approve something. Every `<action>` names files, functions, line anchors and
the exact rule; "etc.", "and so on" and "the way the repo does" are not
allowed. Any `<action>`, `<verify>` or `<done>` holding `&`, `<` or `>` is
wrapped in `<![CDATA[ ... ]]>`. An action that adds code gives the code, or the
exact signature and the exact arithmetic; an action that edits a list gives the
line to add and the line it goes after.

## File layout (in this order)

```
# Section NN-MM: <name>

> Part of: WP-NN (<WP title>) · Items: <lead ids> · Risk: <colour> · Batch: NN.b · Depends on: <sections> · Blocks: <sections> · Tasks: n, k commits · Case-id prefix: QNNMM

## Overview            plain English, 2-4 paragraphs: what is wrong today (quote the audit's evidence), what will be true after, why these items share this section; then the "Test order and commit rule" paragraph
### Section decisions  D-NN-MM.a ...: rulings this file makes within the maintainer's decisions (binding on the executor)
## Risk: [<colour>] -- <one line>      then Why / Risk factors / Mitigation
## Dependencies        Depends on / Blocks / Parallel batch / Can run with; one sentence why
## Evidence            per item: the current code at 090d928 with anchors and 3-10 line excerpts; twoway's rule with its help/ado/class citation; the measured truth ([S] or the audit's appendix); the fixtures on disk; the existing tests that pin today's behaviour, by file::Class::test, so the executor flips them, never deletes them
## User stories        US-NN-MM.k "As a <PRD §3 persona>, I want ... so that ..." -- one per user-visible behaviour
## Business requirements   BR-NN-MM.k -- what must be true for the user, testable, no implementation words
## Technical requirements  TR-NN-MM.k -- how: functions, files, keys, both modes, served copy-list entries (R2, with the anchor each goes after), function_test_map.py / program_coverage_map.py entries, JS twins, the exact arithmetic or rule
## Boundaries          what this section must NOT touch (other sections' owned functions per the index; PRD §7; the rulings)
## Stata truth         which extract script, probes and fixture keys this section adds (or "none"), with the twoway command lines, the scripts/stata_slot.sh run, the _meta stamp and the git add -f note
## TDD test stubs      one line each, "Test: ...", file::Class::test_name, both modes where a page exists; FIRST the regression tests that fail at the base; then the cscript cases (QNNMM-k); then the pinned tests to flip; then the parity corpus entries
## Test plan           table: what | how (pytest / cscript block / node / Chrome) | fixture | both modes? -- plus acceptance criteria AC-NN-MM.k
## Tasks               opens with a "Commit boundary" paragraph naming which tasks form which item's commit and the subject suffix; then the XML tasks
## Section completion criteria
## Notes               traps for the executor; the help paragraphs this section owns (R3); merge rules touched by number; the commit-body line forms
```

## Rules of content

- **Anchors are current.** Cite `file:line` as read at `090d928`; tell the
  executor to re-read before editing.
- **Both modes, every time.** A change in dash_render.py that the served app
  must share names the served copy-list entry (R2) and the served template line
  if the code is written there as a string literal ([C] §5 "Served"). Methods
  of `OptionTranslator`, `SchemeParser` and `GlyphMapper` are copied whole and
  need no entry. A new Bokeh model used by shared code is imported inside the
  function that uses it, or added to both import lists.
- **The saved page's JavaScript.** Only a section with JS = yes in the
  manifest edits `_FILTER_JS`, `_DASH_AXIS_FINISH_JS` or
  `_DASH_CVAR_RELEVEL_JS` in its batch; its JS twin is pinned to the Python
  twin through `test/js_runner.py` (node) and a parity entry (R8).
- **Failing test first.** Task NN-MM-01 writes every regression test for the
  section's first item, runs it against the unmodified tree, saves the
  failure text to `<scratch>/NN-MM-01-failure.txt` and does NOT commit
  (CLAUDE.md rule 4: a red tree is never committed). Later tasks turn the
  tests green; pinned tests asserting today's behaviour are flipped in the fix
  commit with a `Flipped:` line, never deleted.
- **One commit per item; tasks are steps.** Each item's failing tests, fix,
  flipped tests, fixture, help/Unsupported/coverage-audit edits, CHANGELOG
  line, GAPS4 Tracked line and closed BUGS.md entry are one commit, made by the
  item's closing task on the worktree branch `wpNN-sMM` after the section's
  own tests and the cscript it changed ran green; no full suite inside a
  section. Subjects end `(WP-NN <lead id>)`, e.g. `(WP-34 AX-4)`. A section
  with several items repeats the cycle per item, in the manifest's order.
  No test-only commit ever exists.
- **Commit bodies (verbatim line forms).** The saved failure text, the
  measured defect, what changed and where, then one line each: `Regression:
  test/<file>.py::<Class>::<test> -- failed at <base sha> with <text>`,
  `Flipped: <node> -- <old expectation> was wrong because <why>`, `Fixture:
  test/fixtures/<name>.json (scripts/<extract script>)`, `BUGS.md: "<title>"
  (closed|documented)`, `GAPS4: <lead id> Tracked`. No tooling or vendor names
  (grep `claude|anthropic` before and after committing).
- **BUGS.md and GAPS4 forms** are PD-3 and PD-4 exactly. The closing task
  rewrites only the Resolution and flips `- [ ]` to `- [x]`; it rewrites the
  item's Tracked line to the Closed/Documented/Partly form with `commit
  pending`; it deletes the id's line from `GAPS4_OPEN` in
  test/test_tracking_documents.py.
- **CHANGELOG** per PD-7: one line ending `(WP-NN, <lead id>)` under `###
  Fixed in WP-NN`, or under `### Changed behaviour (may need your do-files
  changed)` when a form dash accepted is now refused or a refused form now
  accepted; a results line names the command, the old value and the new.
- **Certification scripts (R1).** The WP's truth script exists before the
  WP's first batch (W0). A section appends one block per item above `* ====
  append new blocks above this line ====`, in section order, of the form:
  `* ==== S<MM> <lead id>: <what> ====` / `local only : env WP<NN>_ONLY` /
  `if inlist("\`only'", "", "S<MM>") & \`: list posof "S<MM>" in w<NN>_run' {`
  / `display as text "S<MM> start " c(current_date) " " c(current_time)` / the
  cases / `display as text "S<MM> end " ...` / `}` / `* ==== end S<MM> ====`.
  Case ids `Q<NN><MM>-<k>` (PD-5). Refusal, message and return-code cases go
  in the existing cscript for their area (test_option_validation.cscript,
  test_twoway_option_parity.cscript, test_parser.cscript,
  test_help_claims_*.cscript, test_env_guards.cscript ...) under the same ids.
  Truth is measured live in the block (`capture noisily twoway ...` beside
  `capture dash ...`, `.Graph` class values, `graph export ..., as(svg)` read
  with test/cert_svg.do) or read from a fixture an extract script wrote.
- **Running one cscript.** Write a two-line driver `printf 'cd
  "%s/test"\nglobal dash_nobrowser 1\ndo "%s/test/%s"\n' "<repo>" "<repo>"
  "<script>.cscript" > <scratch>/run_<script>.do` and run
  `scripts/stata_slot.sh <scratch> <scratch>/run_<script>.do` (`<repo>` is the
  worktree under test). Never the GUI; never a bare `stata-mp` inside a task;
  never `make cert` or `make test-all` inside a section. Select one block with
  `WP<NN>_ONLY=S<MM>` in the environment.
- **Fixtures (R7).** Written by a committed `scripts/extract_*_truth.do` into
  `test/fixtures/<name>_truth.json`; `_meta` holds `stata_version`,
  `born_date`, `dash_commit`, `extracted`, `source`; the do-file captures `git
  rev-parse HEAD` with `shell` into a local, the python block reads it through
  `Macro.getLocal`, never `shell=True`; a backtick is written as `\x60`; `git
  add -f` the fixture; a test names it (test_fixtures_are_committed.py). Never
  hand-patched.
- **Never change Stata preferences.** No `graph set`, no `set ..., permanently`,
  no `python set exec`, no `set scheme ..., permanently`. A section whose
  truth would need one (e.g. a font face) documents the behaviour instead.
- **Silent when honoured.** Once an option is drawn, nothing is printed; only
  options still not drawn are named. dash's extra refusal lines and the
  Supported list stay (M12, PD-11).
- **Refusals use twoway's return codes and words**, measured by the section's
  extract script or taken from a committed fixture ([S] §3-§5,
  value_truth.json, unknown_option_truth.json), never guessed.
- **Documented items (Kind = Document).** The help sentence goes in the topic
  section named by the section, with a one-line entry in "Differences from
  twoway" (`{marker differences}`, dash.sthlp:808-1403) linking to it
  (Q40); the BUGS entry closes `Documented ...`; a help-claim test reads the
  sentence (the `_between(_help(), ...)` pattern of test/test_help_claims_1.py)
  and, where measurable, a cscript case shows dash does what the sentence says.
- **Security (CLAUDE.md, M13).** Any text reaching HTML or JS is escaped
  (`dash_html_escape` in JS, `html.escape` in Python); a new inline script or
  style on the saved page goes through the nonce/hash path of
  `_dash_seal_saved_page`; no `shell=True`; no user text in `exec`/`eval`;
  bounded lengths where text is echoed; test_csp.py, test_csp_browser.py and
  test_serve_token.py stay green.
- **Bokeh 3.8 and 3.9.** Use only APIs present in both ([B] cites both
  versions); `make test` runs under Stata's Python with bokeh 3.8, `make
  test-all` under bokeh 3.9.
- **Help text (R3).** A section edits only the dash.sthlp paragraphs its Notes
  name, the Unsupported-list lines for options it draws, its Differences
  entries and their topic notes, and the Appendix B sentences the index assigns
  to it; test_help_conformance.py pins the Unsupported list to the pending
  blocks both ways.
- **Length.** As long as an executor with no other context needs, and no
  longer: about 250-500 lines; a documentation-only section may be shorter.
