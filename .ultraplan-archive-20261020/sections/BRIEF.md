# Writing brief for WP-31 section files

Every section file in this directory is written to this standard so that the
least capable coding agent builds and ships it correctly the first time
(CLAUDE.md rule 9). Where a section's text and a rule here disagree,
`index.md` wins, then this brief. This brief is WP-28's brief (archived at
`.ultraplan-archive-20261010/sections/BRIEF.md`, reused by WP-29 and WP-30)
with WP-31's ids and forms substituted; the WP-30 deltas it absorbed are
marked (WP-30).

## Inputs (read all before writing or executing)

1. `.ultraplan/PRD.md` -- approved requirements; §4 the feature groups, §7 the
   exclusions.
2. `.ultraplan/DISCOVERY.md` -- the maintainer's decisions Q1-Q40 and the
   research conflict resolutions C1-C4 in `.ultraplan/RESEARCH.md`. A section
   must not contradict them.
3. `.ultraplan/RESEARCH.md` and the three reports in `.ultraplan/research/`:
   `codebase-mechanics.md` (how an option travels, how a plot type is
   registered, the JS recompute, the served move path, test conventions, the
   tracking reader, dependencies, accessibility hooks, the CSV/hover export),
   `stata-ground-truth.md` (parse-class option tables, rpcap/rpspike, contour,
   dot, arrows, legend/minor-tick/edge-title scheme stubs, textbox semantics,
   type-option semantics, mlabel defaults) and `bokeh-web.md` (Bokeh APIs with
   verified snippets, interpolation code, accessibility, export, 3.8 vs 3.9).
   Cite them by heading; their line anchors were read at `6370ca4`.
4. `GAPS3.md` -- the row(s) the section closes (section 4, tables 4.A-4.K; the
   partially finished work in section 5; register corrections in section 6).
   The row's Gap, Evidence and Task columns are the requirement.
5. `.ultraplan/sections/index.md` -- the manifest (section number, slug, GAPS3
   rows, batch, dependencies, risk, effort, case-id prefix), the decision
   record, the batch order, the execution conventions, the merge rules R1-R13
   and the hot-function owner table. Do not renumber.
6. `.ultraplan-archive-20261010/wp30/section-14-bar-widths-caps.md` -- the
   style exemplar for depth and voice (evidence with anchors and excerpts,
   measured truth, boundaries, TDD stubs, XML tasks).
7. The XML task schema below.
8. `CLAUDE.md` -- project rules, especially 1 (security), 3 (a unit test per
   function, end-to-end tests), 4 (a red tree is never committed), 6 (no
   tooling names in commit messages), 7 (a failing regression test before
   every fix), 10 (Stata invocation), 11 (pytest invocation).

## XML task schema

```
<task type="auto|checkpoint" id="NN-MM">
  <name>3 to 8 words, starting with a verb</name>
  <files>path[, path[, path]]</files>          <!-- at most 3 PRIMARY paths, or the word none; the tracking documents (BUGS.md, GAPS3.md, CHANGELOG.md, TWOWAY_COVERAGE_AUDIT.md, dash.sthlp's Unsupported list), the test maps and the flipped tests a closing task edits are implied (DECISIONS A13) -->
  <action><![CDATA[ 2-6 sentences: what to do, where, how; a new file is said here ("Create ...") ]]></action>
  <verify><![CDATA[ the command(s) and the exact expected output ]]></verify>
  <done>One past-tense sentence stating what became true.</done>
</task>
```

Ids are `NN-01, NN-02, ...`, sequential, no gaps, no letter suffixes. A
`checkpoint` task has `<files>none</files>` and asks the maintainer to approve
something. Every `<action>` names files, functions, line anchors and the exact
rule; "etc.", "and so on" and "the way the repo does" are not allowed. Any
`<action>`, `<verify>` or `<done>` holding `&`, `<` or `>` is wrapped in
`<![CDATA[ ... ]]>`, never entity-escaped; `<name>` and `<files>` hold no such
characters. An action that adds code gives the code, or the exact signature
and the exact arithmetic; an action that edits a list gives the line to add
and the line it goes after.

## File layout (in this order)

```
# Section NN: <name>

> Part of: WP-31 · GAPS3 rows: <ids> · Risk: <colour> · Batch: <n> · Depends on: <sections> · Blocks: <sections> · Tasks: n, k commits · Case-id prefix: U<NN>

## Overview            plain English, 2-4 paragraphs: what is wrong today (quote GAPS3's evidence), what will be true after, why these rows share this section; then the "Test order and commit rule" paragraph
### Section decisions  D-NN.a.. : rulings this file makes within the maintainer's decisions (binding on the executor)
## Risk: [<colour>] -- <one line>      then Why / Risk factors / Mitigation
## Dependencies        Depends on / Blocks / Parallel batch / Can run with; one sentence on why
## Evidence            the current code at 6370ca4 with dash_render.py / dash.ado / dash_parse.mata anchors and 3-10 line excerpts (from the research reports or read from the tree); the Stata rule with its help/ado/class citation (research/stata-ground-truth.md); the fixtures on disk; the existing tests that pin today's behaviour, listed by file::Class::test so the executor flips them, never deletes them
## User stories        US-NN.k "As a <PRD §3 persona>, I want ... so that ..." -- one per user-visible behaviour
## Business requirements   BR-NN.k -- what must be true for the user, testable, no implementation words
## Technical requirements  TR-NN.k -- how: functions, files, keys, both renderers, the served copy list entries (with the anchor each goes after), function_test_map.py / program_coverage_map.py entries, JS twins, the exact arithmetic or rule
## Boundaries          what this section must NOT touch (other sections' functions; PRD §7; the decisions)
## Stata truth         exactly which extract script, probes and fixture keys this section adds (or "none"), with the twoway command lines, the scripts/stata_slot.sh run, the _meta stamp and the git add -f note
## TDD test stubs      one line each, "Test: ...", file::Class::test_name, both modes where a page exists; the FIRST stubs are the regression tests that fail at 6370ca4; then the cscript cases (U<NN>-<k>); then the pinned tests to flip; then the parity corpus entries
## Test plan           table: what | how (pytest / cscript block / node / Chrome) | fixture | both modes? -- plus the acceptance criteria AC-NN.k
## Tasks               opens with a "Commit boundary" paragraph naming which tasks form which row's commit and the subject suffix; then XML tasks; task 1 writes the failing tests, runs them against the unmodified tree, saves the failure text to <scratch>/NN-01-failure.txt and never commits; 1-3 files per task; ordered; the closing task of each row closes its BUGS.md entry, writes the GAPS3 Tracked line, updates dash.sthlp, replaces the row's CHANGELOG marker in place and makes the row's one commit
## Section completion criteria
## Notes               traps for the executor (renderer order differences, copy lists, fixture exclude rules, python_exec hazard); cites merge rules R1-R13 by number for the shared files touched; states the commit-body line forms
```

## Rules of content

- **Anchors are current.** Cite `file:line` as read at `6370ca4`; re-read the
  file before editing (the research reports warn that numbers drift).
- **Both renderers, every time.** Any change in `dash_render.py` that the
  served app must share names the copy list (constants tuple at
  dash_render.py:46584-46784, functions tuple :46822-47270, statistical helpers
  :47446-47503) and the served template call site, and says which existing
  entry the new name goes after (R2). Methods of `OptionTranslator`,
  `SchemeParser` and `GlyphMapper` are copied whole and need no entry. A new
  Bokeh model used by shared code is imported inside the function that uses
  it (the `_dash_reference_lines` pattern) or added to both import lists. A new
  function is added to `test/function_test_map.py`; a new Stata program or
  Mata function to `test/program_coverage_map.py` and to `_dash_require_mata`'s
  `_needed` list (dash.ado:448-479) and the dash_parse.mata header index.
- **The saved page's JavaScript.** New estimator helpers go between
  `dash_kernel` and the "// agg_sources is a Bokeh model list" comment in
  `_FILTER_JS`, as named functions, so `js_runner.run_filter_js_block`'s helper
  slice carries them; never between `dash_pctl` and "// Stata's kernels". A new
  `else if (ac.type === '<type>')` branch goes after the kdensity branch. A
  type that gains a refit makes `_dash_stale_kind` return None for itself and
  flips `test_saved_stale_cue.py::_FROZEN`. One JS section per batch (R12).
- **Failing test first.** Task NN-01 writes every regression test for the
  section, runs it against the unmodified tree, saves the failure text to
  `<scratch>/NN-01-failure.txt` and does NOT commit (rule 4). That text opens
  the row's fix commit body and is the old value its CHANGELOG line quotes.
  Later tasks turn the tests green; pinned tests that assert today's wrong
  behaviour are flipped in the fix commit with a `Flipped:` line, never deleted.
- **One commit per GAPS3 row; tasks are steps, not commits.** Each row's
  failing tests, fix, flipped tests, fixture, GAPS3 Tracked line and closed
  BUGS.md entry are one commit, made by the row's closing task on the section's
  worktree branch `wp31-s<NN>` after the section's own tests and the cscript it
  changed ran green (DISCOVERY Q19: no full suite inside a section); the merger
  lands it on `s3-bugs` and the full suite and `make cert` run once at batch
  end. Subjects end `(WP-31 <row>)` where `<row>` is the GAPS3 id, e.g.
  `(WP-31 C1)`; S01 commits once with `(WP-31 S01)` and S61 once per step with
  `(WP-31 S61.k)`. A section with several rows repeats the cycle per row: the
  next row's failing tests are written against the tree the previous row's
  commit leaves. No test-only commit ever exists.
- **Commit bodies (verbatim line forms).** The body opens with the saved
  failure text, then the measured defect, then what changed and where, then one
  line each: `Regression: test/<file>.py::<Class>::<test> -- failed at 6370ca4
  with <text>`, `Flipped: <node> -- <old expectation> was wrong because <why>`
  (one per flip), `Fixture: test/fixtures/<name>.json (scripts/<extract
  script>)`, `BUGS.md: "<title>" (closed)`, `GAPS3: <row> Tracked`.
- **BUGS.md entry (verbatim forms).** S01 opens one entry per in-scope row at
  the END of BUGS.md in the open form: `- [ ] Title: <GAPS3 row's gap, no ">`
  / `  - File Names and Line Numbers: <GAPS3 evidence>` / `  - Description:
  GAPS3.md <row id>, re-verified at 6370ca4: <gap text>` / `  - Suggested fix:
  WP-31 section NN (<name>): <task column>` / `  - Resolution: Not fixed
  because WP-31 section NN has not landed. Graded S1|S2|S3 (WP-31): <why>`.
  The closing task rewrites only the Resolution: `  - Resolution: Fixed
  <ddmonyyyy> (WP-31, <row>). <what changed, in which functions, in both
  renderers>. Pinned by test/<file>.py::<Class>::<test>[, test/<script>.cscript
  <CASE-ID>][; fixture test/fixtures/<name>.json]. [Residual, deferred (WP-31):
  <what and why> (GAPS3 <row> Tracked).] Closes GAPS3 <row> (WP-31, <row>).`
  and flips `- [ ]` to `- [x]`. Field names are exact; one `Graded` clause per
  open entry.
- **GAPS3 Tracked lines (S01 TR-01.2, verbatim forms).** S01 adds a `## 9.
  Tracking` section to GAPS3.md with one line per in-scope row:
  `- **<row> Tracked:** Open (WP-31 section NN).` A closing task rewrites its
  line to `- **<row> Tracked:** Closed in WP-31, BUGS.md "<title>", commit
  pending.`; the merger's step k.3b replaces `pending` with the landed sha on
  `s3-bugs` in one tracking commit per batch (DECISIONS A11); the reader accepts
  `pending`, G2 forbids it after k.3b. or `- **<row> Tracked:** Partly closed in WP-31 (section NN, commit
  <sha>): <what is closed>; open: <what remains> (BUGS.md "<residual title>").`
  `test_tracking_documents.py`'s GAPS3 reader (S01) parses exactly these forms.
- **CHANGELOG (S01 TR-01.6).** S01 places one `<!-- WP-31 <row> -->` marker per
  row in the release's existing lists (`### Results that change`, `### Changed
  behaviour (may need your do-files changed)`, `### Requirements`) and under a
  new `### Fixed in WP-31` heading. A row's closing task replaces only its own
  marker(s), in place, with line(s) ending `(WP-31, <row>)`; a Results line
  names the command, the old value and the new; a Changed-behaviour line names
  the form now refused and twoway's words.
- **Certification scripts (R1).** One new script only,
  `test/test_wp31_truth.cscript`, created and registered by S01 as runner block
  `// 70.` with the hygiene pins moved from 68 to 69 (test_cscript_hygiene.py:299,
  test_cert_shards.py:45, the shard table written by scripts/cert_shards.py);
  no other section touches the runner or the pins. Every comparison with
  twoway's drawing or Stata's own values is a block per GAPS3 row (DECISIONS
  A14: a section's task 01 appends only its first row's block; each later row's
  closing task appends its own) appended above the script's
  last line `* ==== append new blocks above this line ====`, in section order,
  of the WP-30 form (`* ==== S<NN> <row>: <what> ====`, `local only : env
  WP31_ONLY`, `if inlist("\`only'", "", "S<NN>") & \`: list posof "S<NN>" in
  w31_run' {`, start/end display lines, `* ==== end S<NN> ====`); helpers go
  above the header; case ids are `U<NN>-<k>`. Refusal, message, return-code and
  setup checks join the existing cscript for their area (test_option_validation.cscript,
  test_twoway_option_parity.cscript, test_parser.cscript, test_adversarial.cscript,
  test_help_claims_*.cscript, test_setup_*.cscript) under the same `U<NN>-<k>`
  ids. Truth is measured live in the block (`capture noisily twoway ...` beside
  `capture dash ...`, `.Graph` class values) or read from a fixture written by
  an extract script.
- **Running one cscript.** Write a two-line driver `printf 'cd "%s/test"\ndo
  "%s/test/%s"\n' "<repo>" "<repo>" "<script>.cscript" >
  <scratch>/run_<script>.do` and run `scripts/stata_slot.sh <scratch>
  <scratch>/run_<script>.do` (`<repo>` is the worktree under test). Set
  `global dash_nobrowser 1` in the driver. Never the GUI, never a bare `arch
  -arm64 ... -b do` inside a task. A full `make cert` or release gate is never
  launched inside a section (S61 and the batch-end merger only).
- **Fixtures (R7).** Written by a `scripts/extract_*_truth.do` script into
  `test/fixtures/<name>_truth.json`; `_meta` holds `stata_version`,
  `born_date`, `dash_commit`, `extracted`, `source`; the do-file captures `git
  rev-parse HEAD` with `shell` into a local, the python block reads it through
  `Macro.getLocal`, never `shell=True`; a backtick is written as `\x60`; `git
  add -f` the fixture; a test names it (test_fixtures_are_committed.py). A
  regenerated fixture is never patched by hand.
- **Silent when honoured** (DISCOVERY Q36): once an option is drawn, nothing is
  printed; only options still not drawn are named.
- **Refusals use twoway's return codes and words** (DISCOVERY Q15, Q17, Q36):
  r(198) "option X() not allowed" for an option on a type that does not take
  it; r(109) string variables; r(111) variable not found; r(102)/r(103)
  variable counts in twoway's sentences; the text is measured in the section's
  extract script, never guessed.
- **Scheme files hold RGB and Stata's RGBA forms only** (DISCOVERY Q17): no
  section adds CMYK/HSV/intensity reading for scheme files.
- **Security (rule 1)**: any text reaching HTML or JS is escaped (`dash_html_escape`
  in JS, `html.escape` in Python); a new inline script or style on the saved
  page goes through the nonce/hash path of `_dash_seal_saved_page` as a Bokeh
  `CustomJS`/`InlineStyleSheet`, never as raw `<script>`; any name reaching a
  Bokeh field passes the name check; no `shell=True`; no user text in
  `exec`/`eval`; bounded lengths where text is echoed; test_csp.py and
  test_serve_token.py stay green.
- **Tests stay on Bokeh 3.8's property set**: no `link_layouts`,
  `*_text_outline_width`, `Markdown` (RESEARCH §2).
- **No tooling or vendor names** anywhere in commit messages, BUGS.md entries,
  CHANGELOG or help text (CLAUDE.md rule 6).
- **Help text** that a section changes: the owning paragraph is named in the
  index's R3 table; a section edits only its own paragraphs and the Unsupported
  list lines for the options it draws (test_help_conformance.py pins the list
  to the pending blocks both ways).
- **Length**: as long as it needs to be for an executor with no other context,
  and no longer. The exemplar is 400-650 lines.
