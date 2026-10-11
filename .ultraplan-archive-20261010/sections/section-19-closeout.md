# Section 19: Closeout

> Part of: WP-28 · Gaps: all 22 (closed by sections 05 to 18; recorded and proven here) · Risk: green · Batch: 4 · Depends on: all · Blocks: none · Tasks: 12, six commits (S19)


## Review amendments (Phase 4, 2026-09-25) — binding; they override any conflicting text below

> Batch **4** · Depends on **all** · Blocks **none** · Risk **green** · Commits: six closeout commits, one per step (19-02, 19-04, 19-05, 19-06, 19-09, 19-12), subjects ending `(WP-28 S19)`; no gap entries

- D2 (as corrected in the fixer pass): the markers sit in the release's existing top-level lists -- the `**WP-28 (GAPS2 audit, 25sep2026)**` group at the end of `### Results that change` (B1 B2 B3 B5 B6 B7 C2 D1 E1 E2 E3 E14 G6 G16 X1 X2), the end of `### Changed behaviour` (G1 G2), the end of `### Requirements` (K2) and the new `### Fixed in WP-28` heading above `### Fixed after WP-27` (`E14 served`, F1, G3, G5, then S04's lines) -- and 19-01 verifies `grep -c '<!-- WP-28 ' CHANGELOG.md` prints 0 while 19-02 verifies, inside each list's awk range, `grep -c '(WP-28, <ID>)'` is at least 1 for every id that belongs there (E14 in two ranges); every gap line ends `(WP-28, <ID>)`.
- D6/D11: the `make cert` run handed over from S02 lives here (19-10); it is timed with `date +%s` around `make cert` and compared with the orchestrator's pre-batch-1 run in `<scratch>/cert-baseline.log` (`index.md` step 0b); per-block wall times come from the `S<NN> start`/`S<NN> end` lines every `test/test_gaps2_truth.cscript` block prints (the block form in `BRIEF.md`, "Certification scripts"); if the growth exceeds about five minutes the slowest blocks are folded in their owning sections before the gate. Every registered script is 66 after WP-28 (the 65 of 91d97be plus `test/test_gaps2_truth.cscript`, runner block `// 67.`; C7). A single cscript is run through the two-line driver of `BRIEF.md` "Running one cscript" (also `index.md` step 0a), never handed to `scripts/stata_slot.sh` directly.
- Q25, corrected by measurement (C15): no `.html` page is tracked (`.gitignore:5` is `*.html`; `git ls-files` lists none), so 19-07 regenerates the demo pages with `scripts/regen_dashboards.py`, `scripts/regen_comprehensive.py` and `scripts/regen_bootstrap_examples.py` on the merged tree and does NOT commit them.
- D8: the `type="checkpoint"` task 19-03 precedes 19-04, which marks the residuals deferred in GAPS2.md; it approves the list 19-01 collects from every `Residual, deferred (WP-28):` clause in BUGS.md (planned: G1, G3, X2, E14, D1, B5, K2) plus C4/E4 and the D1 colour-form note of D13/F-11.
- D3: verify every WP-28 BUGS.md entry uses `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). … Pinned by test/…`; `grep -c '^  - Resolution: Fixed .*(WP-28, ' BUGS.md` prints 22; 22 closed entries name existing tests; zero open S1/S2.
- D14: 19-06 appends "Invariants introduced by WP-28" to `AGENTS.md`, one paragraph per invariant naming its guarding test, with no Markdown link to `PLAN.md` or `TODO.md`, and commits `(WP-28 S19)`.
- Q24: CHANGELOG old values come from the failing tests' recorded output at 91d97be, quoted in each fix commit's body.

Applies to every section:
- D1 (binding): tasks are work steps; commits are per gap (S01-S04: one each). The failing regression tests are written first and run against the unmodified tree; their output at 91d97be is recorded in the fix commit's message (Q24) and they are committed together with the fix, never alone (CLAUDE.md rule 4).
- D3 (binding): each gap's BUGS.md entry is appended at the END of BUGS.md in the closed form with `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). <what changed>. Pinned by test/<file>::<Class>::<test>.`
- D2 (binding): each closing task replaces the gap's `<!-- WP-28 <ID> -->` marker(s) that S01 placed in the CHANGELOG list named above; it does not add a new line elsewhere.
- D6 (binding): every Stata run is `scripts/stata_slot.sh <scratch-dir> <file>.do` (see `index.md` step 0); no section launches the full cert suite or the release gate.
- D5 (binding): shared files follow merge rules R1-R6 in `index.md` (cscript registration and hygiene pins, copy lists and maps, help/CHANGELOG/BUGS.md, graph-key lists, fixtures, parity corpus).
- D7: XML fields holding `&`, `<` or `>` are CDATA-wrapped (done mechanically); task names over 8 words are shortened and `done` fields put in the past tense during the detailed fixer pass.

Detailed edits from `../review/consistency.md`, `../review/requirements-security.md` and `../review/feasibility.md` (as adjusted by `../review/DECISIONS.md`) were applied to this file in the fixer pass (2026-09-25); the text below conforms to this block.

## Overview

When sections 01 to 18 have landed, every gap has a fix commit, a closed BUGS.md entry and a
CHANGELOG line, but nothing yet says so in one place, and nothing has measured the whole:
`ROADMAP.md`'s WP-28 is still open, GAPS2.md's 22 entries in scope still read
`- **Tracked:** new` (or the audit's other pre-fix text), the CHANGELOG may still hold a
`<!-- WP-28 <ID> -->` marker a section forgot, `dash.pkg`'s `Distribution-Date: 20260924` is older
than the shipped files it now describes (the gate refuses that: `scripts/release_verdict.py:213-215`),
and the exit criterion of PRD §8 (both suites green under both interpreters with no skip,
the certification suite with no skip, the release gate green from an installed package, no
open S1/S2, 22 closed entries naming existing tests, a clean tree) has been claimed by
sections one at a time, never measured on the merged tree.

After this section: the CHANGELOG lists every changed number, text, colour or layout once
in the WP-28 group of `### Results that change` with the command, the old value (the failing
test's recorded output at 91d97be, Q24) and the new, the rest under `### Fixed in WP-28`,
`### Changed behaviour` and `### Requirements`, every gap line ending `(WP-28, <ID>)`; each GAPS2 entry in scope carries
`Closed in WP-28, BUGS.md "<title>", commit <hash>`, and C4/E4 and the G1, G3, X2, E14 and
D1 residuals are marked deferred with DISCOVERY's reason, after the maintainer has approved
the deferred list (D8); WP-28 is headed `— DONE` with a `### Done, measured (<date>)` block
that quotes the runs, the certification suite's wall time before and after the package (D11)
and the demo pages regenerated; `AGENTS.md` carries the invariants WP-28 introduced, each
with its guarding test (D14); the demo pages are regenerated on the merged tree and left
untracked, as they are (C15); the six version lines and the Distribution-Date are dated;
`make test`, `make test-dev`, `make cert` and `make gate` have each run once on the final tree
and passed; and the merge command is reported, never run.

The tracking tests of section 01 are this section's proof: writing `— DONE` turns
`test_every_gaps2_id_a_done_package_lists_is_closed_by_it` from vacuous into a check of all
22 Tracked lines, each against a closed BUGS.md entry and a commit that exists.

**Commit rule (D1): this section commits per step**, six times, subjects ending `(WP-28 S19)`
(19-02, 19-04, 19-05, 19-06, 19-09, 19-12); it fixes no gap, so no commit here carries a
`(GAPS2 <ID>)` subject. It adds no regression test; its failing-first step is the guard proof
recorded in 19-05.

## Risk: [green] — documents, six dated lines, and four suite runs; no behaviour changes

- **Why.** No renderer, ado or Mata logic changes. The only shipped-file edits are the
  version-date lines one test already holds equal (`test/test_pkg_metadata.py:49-60`).
- **Risk factors.** (1) A run of certification SKIPs that is really Stata having lost its
  `python_exec` (report C §8) read as a pass. (2) The gate's Distribution-Date rule
  (`release_verdict.py:198-215`) failing on an undated package. (3) The PreToolUse hook's
  ledger refusing a third full launch, or a full run started while another executes. (4) A
  section's BUGS.md title holding a `"`, which the GAPS2 Tracked form cannot quote. (5) A
  marker left in the CHANGELOG, or a gap whose "Results that change" line lacks the old and
  new value. (6) The full runs measured on a tree that later edits change. (7) The
  certification suite grown past the five-minute budget of D11 by the blocks
  `test/test_gaps2_truth.cscript` gained.
- **Mitigation.** (1) `display c(python_exec)` through `scripts/stata_python_exec.sh` before
  the cert suite and before trusting any SKIP; restore it if empty. (2) Tasks 19-08 and 19-09
  date the release before the gate. (3) `make` targets are run one at a time, in the
  background, each read from its log; the hook does not count `make`, the conftest lock still
  serialises. (4)-(5) are grep checks in 19-01 and 19-02. (6) Only ROADMAP.md's measured
  paragraph and the CHANGELOG heading change after the runs, and the targeted document tests
  are rerun. (7) The cert suite's growth is measured against the orchestrator's baseline
  (D11); a growth over about five minutes is folded in the owning section's blocks before
  the gate, never by dropping a case.

## Dependencies

- Depends on: every section 01 to 18, merged into `s3-bugs` (each with `patch -p1` from its
  worktree, worktrees removed), so that the 22 fix commits, their BUGS.md entries and their
  CHANGELOG lines are on the branch; and the orchestrator's pre-batch-1 certification run,
  `<scratch>/cert-baseline.log` (`index.md` step 0b, D11), whose first and last lines are the
  `date +%s` before and after `make cert` on the unmodified tree.
- Blocks: none. Parallel batch: 4, alone.
- Why: the closure proof reads the fix commits' hashes and BUGS.md titles, and the suites
  must run on the merged tree, not on any section's worktree.

## Evidence

### The four runs and their verdicts (research report C §6, §8)

`Makefile:32-50`:

```make
test:
	@py="$${STATA_PYTHON:-$$(STATA='$(STATA)' sh scripts/stata_python_exec.sh)}"; \
	...
	DASH_STRICT=1 DASH_BASELINE=stata "$$py" -m pytest test/ $(PYTEST_ARGS)
test-dev:
	@DASH_STRICT=1 DASH_BASELINE=dev $(PYTHON) -m pytest test/ $(PYTEST_ARGS)
cert:
	@STATA='$(STATA)' PYTHON='$(PYTHON)' sh scripts/run_cert_suite.sh
gate:
	@STATA='$(STATA)' PYTHON='$(PYTHON)' sh scripts/run_release_gate.sh
```

Interpreters (report C §6): Stata's `c(python_exec)` is `/opt/anaconda3/bin/python3` (3.13.9,
bokeh 3.8.0, pandas 2.3.3, numpy 2.3.5); the development `python3` is
`/opt/homebrew/bin/python3` (3.14.5, bokeh 3.9.0, pandas 3.0.1, numpy 2.4.3). Under
`DASH_STRICT=1`, `test/conftest.py` refuses a drifted environment before any test and turns
any skip red at the end (`pytest_sessionfinish`, 128-138). WP-27 measured 16,693 passed under
each interpreter, 0 skipped, and 64 of 64 cert scripts (ROADMAP.md 4196-4203), recording no
wall time; the runner registers 65 at 91d97be (`test/run_all_cscripts.do`;
`test_cscript_hygiene.py:418` requires registration; the pins at :292 and :308 read 65 and
47; a third pin, `with_probes == 13` at :315, counts the scripts with import probes). After
WP-28 it registers 66: S02 adds the ONE new script, `test/test_gaps2_truth.cscript`, as runner
block `// 67.` (the runner's blocks are numbered to 66 today for 65 scripts) and sets the pins
to 66 and 48 (and :315 if the new script has probes); every later Stata-truth comparison is a
block appended to that script, gated by `GAPS2_ONLY` and printing `S<NN> start <time>` and
`S<NN> end <time>` (the block form in `BRIEF.md`, "Certification scripts"), and every refusal, message or setup check joins the existing
script for its area (D11, C7). No other `.cscript` file is new. The runner prints one
timestamp, at its start (`run_all_cscripts.do:33`, `c(current_date) c(current_time)`), and
none at its end, so the suite's wall time is measured around `make cert` with `date +%s`,
not read from the log; the per-block times are read from the block lines, which the runner's
`capture noisily` keeps in `run_all_cscripts.log`. The runner does `cd "<repo>/test"` (:66)
before each `do "test_x.cscript"` and every script opens `cscript "…" adodir ".."` and
`do "cert_helpers.do"` relative to that directory, so one script is run through a two-line
driver (`cd "<repo>/test"` then `do "<repo>/test/<script>.cscript"`) handed to
`scripts/stata_slot.sh`, never the script itself (`BRIEF.md` "Running one cscript"; `index.md` step 0a).

`scripts/run_cert_suite.sh` runs the runner from `mktemp -d` with `STATATMP="$dir/tmp/"`
through `arch -arm64 "$STATA" -b do`, then `scripts/cert_verdict.py`, which passes only when
every registered script printed `[ PASS]`, none `[ FAIL]` or `[ SKIP]`, and the summary line
`ALL TESTS PASSED (n passed, 0 skipped)` agrees. `scripts/run_release_gate.sh` copies exactly
what `dash.pkg` ships plus `stata.toc` to `$dir/src`, runs `scripts/release_gate.do` (net
install into a scratch PLUS, every `examples/*.do`, one page per shipped scheme, `adoupdate`
against the source and a one-day-newer copy, PLUS restored), and judges the log with
`scripts/release_verdict.py`, whose Distribution-Date rule is:

```python
 198	    # adoupdate, and a current Distribution-Date
 209	        problems.append("dash.pkg declares no Distribution-Date")
 213	    elif m.group(1) < min_date:
 214	        problems.append("Distribution-Date %s is older than the newest "
 215	                        "change to a shipped file, %s" % (m.group(1), min_date))
```

`min_date` is today when a shipped file is uncommitted, else the date of the last commit
touching a shipped file (`run_release_gate.sh:27-31`). WP-28 changes shipped files, so the
package must be dated no earlier than that commit. The verdict also allows no diagnostic
(`DIAGNOSTICS`: "ignor", "not found", "fallback", "warning", "traceback", "error:", "drew
nothing") in any example's log unless the example declares it with `*! release-gate allows:`.

### What holds the version lines equal

`test/test_pkg_metadata.py:49-60` reads the version and date from `dash.ado`,
`dash_parse.mata`, `dash_setup.ado` (`*! Version: <v> <date>`), `dash.pkg`
(`d Version: <v>  <date>`), `dash.sthlp` and `dash_setup.sthlp` (`{* *! version <v>  <date>}`);
`test/test_help_claims_1.py::TestTheHeader::test_the_version_line_is_dash_ados` (190-196)
holds `dash.sthlp`'s to `dash.ado`'s. Today all six read `2.0  24sep2026` (dash.pkg:24,
dash.ado:29, dash_setup.ado:16, dash.sthlp:2, dash_setup.sthlp:2) and `dash.pkg:25` is
`d Distribution-Date: 20260924`. `CHANGELOG.md:3-5` reads `## 2.0, 24sep2026 (release
candidate)` and "adoupdate compares the Distribution-Date, now 20260924".

### The guards this section turns on, and the launch limits

`test/test_tracking_documents.py` after section 01: `TestGaps2AndRoadmapAgree` reads
`**GAPS2 closed:**`, GAPS2.md's `### <ID>.` headings and `- **Tracked:**` lines
(`_GAPS2_CLOSED = ^Closed in (WP-\d{2}), BUGS\.md "([^"]+)", commit ([0-9a-f]{7,40})\b`,
`_GAPS2_DEFERRED = ^Deferred \((WP-\d{2})\): \S`), and for a DONE package requires each id's
line to be the Closed form naming it, a closed BUGS.md entry with that exact title whose
Resolution carries `(WP-28, <ID>)`, and a commit `git cat-file -e` finds.
`TestNoOpenEntryBlocksARelease` (476-505) fails on any open S1/S2; the four open entries at
BUGS.md 2523, 2559, 2595, 2601 are graded S3 and stay open.

`.claude/hooks/guard-full-suite.sh` blocks a full pytest or `run_all_cscripts.do` launch
while one executes (the conftest lock at `/tmp/dash-full-suite-<uid>.lock`, or a matching
process) and the third full launch in a session unless prefixed `FULL_SUITE_RERUN=1`; a
`make …` command is not matched by its `PYTEST`/`STATA` regexes, but the conftest lock still
refuses a second whole-suite pytest (`test/conftest.py:97-128`). The `python_exec` hazard
(report C §8, memory note `project_stata_cert_suite`): many concurrent console sessions can
rewrite `~/.stata19/console/stata19.rc` without its `python` lines, after which every Python
cscript SKIPs (rc 222) in 0-1 s; `scripts/stata_python_exec.sh` prints `c(python_exec)` from
a batch session, and `set python_exec /opt/anaconda3/bin/python3, permanently` restores it.

### What the closeout records (PRD §7, DISCOVERY "Deliberate exclusions" and amendments)

- **C4 / E4**: out of scope by decision (Q3); nothing ported to `_FILTER_JS` on its account.
- **G1 residual** (Q7, amended): the qualifier, by()-order and ustrfix columns stay generated
  in the user's dataset (a dataset at `c(maxvar)` may still fail); a user variable named like
  a Bokeh glyph field (`x`, `y`, `top`, `count`, `density`, …) is still shadowed by the
  derived value in `hover()` and `mlabel()`.
- **G3 residual** (Q9): the export stays JSON; row-drawing layers stay bounded by the limit;
  the served app embeds every row, so the relaxed count applies to the saved page only.
- **X2 residual** (Q5): the continuous colour default and `colorrule()`, `colorstart()`,
  `colorend()` stay as documented.
- **E14 residual** (research amendment): the `filterposition(left)` layout difference is
  recorded, not fixed.
- **D1 residual** (D13, Q30, requirements F-11): third-party scheme files are out of scope by
  decision, so GAPS2 D1 plan step 4's sweep of the locally installed schemes and the d3colors
  pin are excluded, not deferred; and the CMYK, hsv and `colour*#` colour forms of plan step
  2 are GAPS2 D7's, not read here. Both go into D1's Tracked line.
- **B5 residual** (S15): a layer that drew nothing has no key, so `order()` naming its number
  draws nothing where twoway draws the key.
- **K2 residual** (Q8): no Python 3.10 venv matrix; the floor is the tested one, proven by
  sandbox fakes, not by installs below it.
- **E1/E3**: `%x`, `%H` and `%L` (the IEEE byte dumps) are refused with r(198), not written
  (Q6; S04). Not a residual: a documented refusal.
- The list above is the plan's; the list that is written comes from BUGS.md itself: 19-01
  collects every `Residual, deferred (WP-28):` clause of the 22 entries (S01 TR-01.8's optional
  last sentence), 19-03 has it approved, 19-04 writes each clause into its Tracked line.

### The commit map this section reads

Section 01's TR-01.9 puts the gap id in every fix commit's subject, `… (GAPS2 B1)`, so
`git log --format='%h %s' 91d97be..HEAD | grep -F '(GAPS2 B1)'` gives B1's hash; each fix
commit also holds the gap's BUGS.md entry whose Resolution field reads
`- Resolution: Fixed <ddmonyyyy> (WP-28, B1). …` (D3), whose title is what the Tracked line
quotes. Each fix commit's body opens with the failing tests' recorded output at 91d97be
(Q24), which is the old value its CHANGELOG line quotes, and carries the `Regression:`,
`Flipped:`, `Fixture:` and `BUGS.md:` lines of TR-01.9 that 19-05 reads.

### The demo pages are not tracked (C15)

`.gitignore:5` is `*.html` and `git ls-files | grep -c '\.html$'` prints 0 at 91d97be: no
demo page is committed, so the plan's earlier assumption that the pages were checked in (Q25
as first answered) was wrong. The scripts that write them, from the package root:
`scripts/regen_dashboards.py` (`scatter.html`, `dashboard.html`, `full_dashboard.html`,
`kelly22ex_dashboard.html`), `scripts/regen_comprehensive.py` (`comprehensive_demo.html`)
and `scripts/regen_bootstrap_examples.py` (`bs_equal_cols.html`, `bs_kpi_hero.html`,
`bs_stacked.html`, `bs_responsive.html`); each imports `dash_render` from the root and writes
beside it. `scripts/regen_option_surface.py` regenerates dash.ado's option surface, not a
page, and is not run. A root `.html` that were committed would also fail
`test_packaging.py::test_the_package_root_holds_only_what_ships_and_the_repositorys_own`
(411-434), whose `_ROOT_ALSO` names no page.

### AGENTS.md (D14)

`AGENTS.md` is a 22-line numbered list of rules with no heading; it is on
`test_packaging.py:413`'s `_ROOT_ALSO` already, so a section appended to it needs no allowlist
change. `test_tracking_documents.py::TestTodoAndPlanAreRetired::test_nothing_links_them`
(875-888) reads every `.md` for a Markdown link to `TODO.md` or `PLAN.md` (`_MD_LINK`, 837):
the appended section names tests and scripts, never a link to a retired document.

## User stories

- **US-19.1** As the maintainer, I want one measured record that WP-28 is done, both suites
  green under both interpreters, the certification suite and the gate green from an
  installed package, no open S1/S2, so that the release can be judged after the fact from
  the documents alone.
- **US-19.2** As the Stata user with published figures, I want the CHANGELOG to tell me every
  number, text, colour or layout that changed, with the command and the old and new values,
  so that I can tell which of my dashboards look different and why.
- **US-19.3** As the next auditor, I want each GAPS2 entry in scope to name the package, the
  BUGS.md entry and the commit that closed it, and each residual to say why it was deferred,
  so that the audit is not re-reported.
- **US-19.4** As the maintainer, I want the merge command reported and not run, so that
  `main` moves only by my hand (CLAUDE.md rule 5).
- **US-19.5** As the next agent working on dash, I want the invariants WP-28 introduced
  written in `AGENTS.md`, each with the test that guards it, so that I neither break them nor
  rediscover them (Q29, D14).
- **US-19.6** As the maintainer, I want the demo pages regenerated from the merged renderer
  and left untracked as they are, so that what I open locally shows the fixed drawing and
  nothing ignored is forced into the history (Q25, C15).
- **US-19.7** As the maintainer, I want the certification suite's wall time measured before
  and after the package, so that the five-minute budget of Q28 is a number, not a claim.

## Business requirements

- **BR-19.1** The CHANGELOG records every WP-28 gap once, in the right list, with before and
  after values wherever a drawn number, text, colour or layout changed; no marker remains.
- **BR-19.2** Every GAPS2 entry in scope names WP-28, its BUGS.md entry and its commit; C4/E4
  and the G1, G3, X2 and E14 residuals are marked deferred with DISCOVERY's reason; the audit
  text is otherwise unchanged (Q23).
- **BR-19.3** WP-28 is DONE in ROADMAP.md with a measured block quoting the four runs.
- **BR-19.4** The full pytest suite passes under both interpreters, strict, with no skip; the
  certification suite (every registered script, 66) passes with no skip and its wall time has
  grown by at most about five minutes over the pre-WP-28 run (Q28, D11); the release gate
  passes from an installed package; BUGS.md has no open S1 or S2 and 22 closed WP-28 entries
  each naming a test that exists.
- **BR-19.5** The package is dated: version lines and Distribution-Date agree and are no
  older than the last shipped-file change.
- **BR-19.6** The working tree is clean of WP-28's work (the maintainer's own planning files
  may remain uncommitted, as at WP-27; the regenerated `.html` pages are ignored), and the
  merge command is reported, not run.
- **BR-19.7** `AGENTS.md` ends with a section "Invariants introduced by WP-28" naming, for
  each invariant, the test that guards it (D14).
- **BR-19.8** The demo pages are regenerated once on the merged tree by the three
  `scripts/regen_*.py` page scripts and not committed (C15).

## Technical requirements

- **TR-19.1 Inventory (19-01).** From `git log --format='%h %s' 91d97be..HEAD`, build
  `<scratch>/wp28-map.tsv` with one row per gap: id, hash, BUGS.md title (from the entry whose
  Resolution field reads `  - Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). …`, D3; found with
  `grep -n '^  - Resolution: Fixed .*(WP-28, <ID>)' BUGS.md`, then the nearest `- [x] Title:`
  line above it). Require exactly one fix commit and one entry per id (a subject naming several
  ids, `(GAPS2 E3, G6)`, is the one commit of each id it names), no title holding `"`,
  and no `<!-- WP-28 ` marker surviving. Collect every `Residual, deferred (WP-28): <text>`
  clause of those 22 entries into `<scratch>/wp28-residuals.txt` (id, title, clause text);
  the plan expects G1, G3, X2, E14, D1, B5 and K2 (Evidence), but the file is what BUGS.md
  says. Run `python3 -m pytest test/test_tracking_documents.py test/test_packaging.py -q`
  first.
- **TR-19.2 CHANGELOG (19-02).** The WP-28 lines live in four places (S01 TR-01.7, D2): the
  `**WP-28 (GAPS2 audit, 25sep2026)**` group at the end of `### Results that change`, the end
  of `### Changed behaviour (may need your do-files changed)`, the end of `### Requirements`,
  and the new `### Fixed in WP-28` heading above `### Fixed after WP-27`. Verify each gap's
  line is in its place and complete, editing only for completeness or placement, never
  rewording a section's fact. Results group: B1 (six unlabelled ticks → three labelled;
  `10 20 to 40` lost 30; `1/5` named), B2 (`ylabel(0(20)100)` ended at 41; `yscale(range(100))`
  inverted; `range(20 30)` hid data), B3 (`title("T", c(red))` drew `T`, `,`, `c(red)` as three
  lines in the scheme colour; `ytitle("Volume", axis(2))` titled the left axis), B5
  (`order(1 "Group 2" 3 "Three")` ignored its text; `order(2 1) label(1 "Data")` relabelled the
  fit), B6 (`xtitle("")` drew the variable name), B7 (`ytitle2("P2")` drew the quotes), C2
  (nlsw88 ttl_exp `bin(27)` counted 2245 of 2246, census pop `bin(75)` 49 of 50), D1 (a scheme
  file with quoted RGB drew every series #606060), E1 (`fmt(%10.0g)` of 6165.2567 showed
  `6e+03`; `%9,2f`, `%12.0fc`, `%td` unapplied; the variable's own %g dropped), E2 (after price
  → [4000,5000], foreign=1, price → full range: g1=3, g2=5, k1=3 rows where the widgets imply
  5, 5, 5), E3 (a %td dropdown listed `2001-12-31 00:00:00`; a %tm card `Oct 2000` for
  `2000m10`; a %tm axis `Jan 2000` for `2000m1`; %tC tooltips lost the time), E14 (the saved
  `layout(bs)` filter bar moves below the header), G6 (a float 0.1 shown as
  `0.10000000149011612`; a tooltip `1.235e+4` for 12345.67; `%9.0g` of 1234567.5 as
  `1.23457e+06` for `1234568`), G16 (numbers where `valuelabel` and `hover()` show value
  labels), X1 (`'01'` listed as `'1'`; `'nan'`, `'None'`, `'NaT'` categories dropped; 5e-05
  unselectable on the saved page), X2 (`colordiscrete colorcuts(2 4)` coloured 1, 3 and 5 as
  intervals where twoway draws them gray; an empty `≤0` level kept). Changed behaviour: G1 (a
  variable named `__dash…` is r(110); `__dash_row__` was overwritten in silence, y 100..140
  drawn as 0..4), G2 (a string plot variable is r(109), as twoway; it was drawn as nonsense or
  ended in a traceback). Requirements: K2 (Python 3.13+, bokeh 3.8+, pandas 2.3+, numpy 2.3+,
  from 3.8/3.0/2.0/1.23; the generated app imports annotations from `__future__`), and the
  floor items above it (330-336 at 91d97be) must already state the new floor (section 09's
  edit; fail if not). Fixed in WP-28: E14 served (viewport tag, 0.15 dimming, rspike/rconnected
  selection, 992 px reflow with KPI minimum heights), F1 (non-zero rc and "no server started
  on port N: the port is in use"; `--port` outside 1024-65535 refused; URL printed once
  /health answers), G3 (a computed-only graph counts its drawn output; the size note reports
  embedded bytes; a 5,000,001-observation histogram builds), G5 (Unicode names in `filter()`,
  `dash kpi`, `by()`, `hover()`, `colorvar()`), then S04's shared-component lines ending
  `(WP-28 S04)`. Every gap line ends `(WP-28, <ID>)`; a Results line names the command, the
  old value and the new; the old value is the failing test's recorded output at 91d97be (Q24),
  which opens the gap's fix commit body -- where a section's line lacks it, take it from that
  body, never from a fresh checkout. A WP-28 line found anywhere else (another group of
  `### Results that change`, `### Fixed`, `### New`, `### Security`) is moved to its place.
  The awk ranges: `/^### Results that change/,/^### Security/`,
  `/^### Changed behaviour/,/^### Removed/`, `/^### Requirements/,/^### Fixed in WP-28/`,
  `/^### Fixed in WP-28/,/^### Fixed after WP-27/`.
- **TR-19.3 GAPS2.md Tracked lines (19-03, 19-04).** The maintainer first approves the
  deferred list (19-03, checkpoint, D8): `<scratch>/wp28-residuals.txt` plus C4/E4 plus D1's
  colour-form note. Then, for each of the 22 ids, replace the entry's `- **Tracked:** <old>`
  with `- **Tracked:** Closed in WP-28, BUGS.md "<title>", commit <hash>[; residual deferred
  (WP-28): <reason>]; was: <old>` -- the old text kept after `was:`, never dropped; each
  Tracked line is one physical line (wrap nothing). The `<reason>` is the entry's collected
  `Residual, deferred (WP-28):` clause text; D1's line always ends its reason with `CMYK, hsv
  and colour*# scheme values are D7's (GAPS2 D7), not read here; third-party scheme files
  excluded by decision (DISCOVERY Q30)` (D13, F-11), whether or not S06's clause says so.
  C4: `- **Tracked:** Deferred (WP-28): out of scope by decision (DISCOVERY Q3), with its
  duplicate E4; nothing is ported to _FILTER_JS on its account; was: <old>`. E4's pointer line
  (`**E4. …** -- same gap as C4; see there.`) is not edited. No other GAPS2 text changes.
- **TR-19.4 WP-28 DONE (19-05).** Append ` — DONE` (em dash, as WP-27's heading) to the
  `## WP-28 · …` heading and add `### Done, measured (<ddmonyyyy>)` after its test plan and
  traceability table, in WP-27's shape (4180-4239): one bullet per BR/AC group stating what was
  measured, with the numbers to be filled by 19-12 written as `<to be measured in 19-12>` in
  that commit only. The block also lists the fixtures the package added (from
  `git diff --stat 91d97be..HEAD -- test/fixtures`), the tests flipped (from the commit
  bodies' `Flipped:` lines), the residuals deferred, the certification suite's wall time
  before and after the package with the growth in minutes (D11), the demo pages regenerated
  and left untracked (C15), the `AGENTS.md` section added (D14), and the merge command as text.
- **TR-19.5 Date the release (19-08, 19-09).** Set the six version lines to `2.0  <ddmonyyyy>`
  and `dash.pkg:25` to `Distribution-Date: <yyyymmdd>` for the same day; the version number
  stays 2.0 (WP-27's precedent: adoupdate compares the date). The six files are two steps of
  three files (D7's three-file rule) and ONE commit, because `test/test_pkg_metadata.py:49-60`
  and `test_help_claims_1.py:190-196` hold the lines equal. Run
  `python3 -m pytest test/test_pkg_metadata.py test/test_help_claims_1.py test/test_packaging.py -q`,
  then `make test` and `make test-dev`, each in the background with output to
  `<scratch>/make-test.log` / `<scratch>/make-test-dev.log`, one at a time, read from the
  log on exit; both must end with 0 failed and 0 skipped and no strict-mode line. Commit.
- **TR-19.6 Certification and its wall time (19-10).** `STATA=/usr/local/bin/stata-mp sh scripts/stata_python_exec.sh`
  must print `/opt/anaconda3/bin/python3` (this is `display c(python_exec)` through the
  console binary); if it prints nothing, write `<scratch>/pyexec_fix.do` holding
  `set python_exec /opt/anaconda3/bin/python3, permanently`, run it as
  `scripts/stata_slot.sh <scratch> <scratch>/pyexec_fix.do`, and check again. Then run
  `{ date +%s; make cert; echo "exit=$?"; date +%s; } > <scratch>/make-cert.log 2>&1` in the
  background (the same wrapper `index.md` step 0b used for the baseline); read the log on
  exit: the verdict must say every registered script (66 after WP-28: the 65 of 91d97be plus
  `test/test_gaps2_truth.cscript`) passed and none skipped, `exit=0`, and the wall time is the
  last line minus the first. If any script SKIPped, check `python_exec` again before reading
  the skip as real; a skip is not a pass. Compare the wall time with the baseline
  `<scratch>/cert-baseline.log` (last line minus first line; the orchestrator's `make cert`
  on the unmodified tree before batch 1; WP-27's `### Done, measured` block records only
  `64 of 64`, no time). If the growth exceeds about five minutes (300 s), find the slowest
  blocks of `test/test_gaps2_truth.cscript` from the `S<NN> start <time>` / `S<NN> end <time>`
  lines in the cert log (`grep -E '^S[0-9]{2} (start|end) ' <cert log>`), fold them in the
  owning sections' files under their rules (fewer probes per block, one `graph export` shared
  by a block's assertions; never a dropped comparison; D11), commit with those gaps' ids, and
  rerun 19-10. Both times and the growth go into the `### Done, measured` block in 19-12. If
  the baseline log is absent, record "baseline not measured" and the after time alone; do not
  re-check out 91d97be to measure it (Q24's rule against re-checkouts). One script or one
  block is rerun through the driver of `BRIEF.md` "Running one cscript":
  `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "<repo>" "<repo>" "<script>.cscript" > <scratch>/run_<script>.do`
  then `scripts/stata_slot.sh <scratch> <scratch>/run_<script>.do` (log
  `<scratch>/run_<script>.log`), with `GAPS2_ONLY=S<NN>` in the environment to run one block
  of `test_gaps2_truth.cscript`; `<repo>` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash`.
- **TR-19.7 Gate (19-11).** `make gate` in the background to `<scratch>/make-gate.log`; the
  verdict must list no problem: install rc 0, every example rc 0 with no diagnostic, every
  scheme page rc 0, adoupdate as expected, Distribution-Date current, PLUS restored.
- **TR-19.8 Record and report (19-12).** Fill the measured numbers into the `### Done,
  measured` block (passed/skipped per interpreter and the interpreter versions, cert `n of n`
  and the two wall times, gate examples and scheme pages, the log paths, the nine pages
  regenerated); set `CHANGELOG.md:3` to `## 2.0, <ddmonyyyy> (release candidate)` and line 5's
  "now <yyyymmdd>" to the new date; run the final checks of AC-19.1..19.10; commit; report the
  merge command `git checkout main && git merge s3-bugs` in the task's report and in the
  block. Do not run it.
- **TR-19.9 Security (rule 1).** Nothing new reaches a page. The scratch files hold no
  secrets; every Stata run of this section is the console binary in batch from a scratch
  directory with its own `STATATMP=<dir>/tmp/` (trailing slash, not the log's directory):
  `make cert` and `make gate` through their own runner scripts, the one-off do-files and
  drivers through `scripts/stata_slot.sh`; no `shell=True`; no GUI Stata. The `AGENTS.md`
  text and the regenerated pages come from the repository's own scripts and tests, not from
  user input.
- **TR-19.10 Invariants in AGENTS.md (19-06; D14, Q29).** Append to `AGENTS.md`, after its
  last numbered rule and a blank line, a heading `## Invariants introduced by WP-28` and one
  paragraph per invariant, each naming the guarding test by `test/<file>.py::<Class>[::<test>]`
  as it exists on the merged tree: (1) the `__dash` column prefix -- every internal column
  the renderer or the ado creates starts with `__dash`, a user variable under it is refused
  with r(110), and the guard is `test/test_reserved_names.py` (S07: name its prefix class and
  the test that no internal literal lacks the prefix); (2) the served copy lists --
  `dash_render.py`'s served constants and functions tuples must name every module-level name
  the served template reads, guarded by
  `test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName` and
  `test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads`, plus
  `test/function_test_map.py` for every new function; (3) the Python/JavaScript twins --
  `_dash_fmt`/`dash_fmt` (`_DASH_FMT_JS`), the filter mask (`_dash_frame_filter_mask` /
  `_DASH_FILTER_MASK_JS`) and the histogram recount, each pinned against the other under node
  (`test/test_display_format_writer.py::TestJavaScriptTwin`, `test/test_js_runner.py::TestMaskParity`
  with S17's `test_node_and_pandas_agree`, S05's `TestTheJavaScriptRecountAgrees`; `node` is
  read from `DASH_NODE` or `PATH`, and the tests skip without it except under `DASH_STRICT`);
  (4) `scripts/stata_slot.sh <scratch-dir> <file>.do` -- the one way agent work runs Stata in
  batch (three `mkdir` slots, `STATATMP` under the scratch directory, the console binary of
  CLAUDE.md rule 10; a cscript goes through the two-line driver `BRIEF.md` "Running one cscript" gives); (5) the
  CHANGELOG marker convention -- a package's tracking section places `<!-- WP-nn <ID> -->`
  markers in the release's existing list where each gap's line belongs and each fix replaces
  its own marker with a line ending `(WP-nn, <ID>)`; the closeout greps zero markers (no test
  reads CHANGELOG.md beyond the retired-link scan); (6) the BUGS.md Resolution form
  `- Resolution: Fixed <ddmonyyyy> (WP-nn, <ID>). … Pinned by test/… .` with the id inside the
  text and the field name unchanged, read by
  `test/test_tracking_documents.py::TestGaps2AndRoadmapAgree::test_every_closed_gaps2_entry_names_a_closed_bugs_entry_and_a_commit`;
  (7) the fixture `_meta` stamp -- every Stata-measured fixture's `_meta` holds
  `stata_version`, `born_date`, `dash_commit` and `extracted`, asserted by the fixture test of
  the section that wrote it (name each from the commit bodies' `Fixture:` lines) and every
  fixture is named by a test (`test/test_fixtures_are_committed.py`). The section writes no
  Markdown link to `PLAN.md` or `TODO.md` (`test_tracking_documents.py::TestTodoAndPlanAreRetired::test_nothing_links_them`
  scans `AGENTS.md`). Run `python3 -m pytest test/test_tracking_documents.py test/test_packaging.py -q`
  and prove every node named exists with `python3 -m pytest --collect-only -q <node> …` (one
  command listing every `::` node; each must collect at least one test). Commit `AGENTS.md`
  alone with the subject `Record the invariants WP-28 introduced, each with its guarding test (WP-28 S19)`.
- **TR-19.11 Demo pages (19-07; Q25 corrected, C15).** From the repository root run
  `python3 scripts/regen_dashboards.py`, `python3 scripts/regen_comprehensive.py` and
  `python3 scripts/regen_bootstrap_examples.py` once each on the merged tree; each must exit
  0 and each of the nine pages it names must exist and hold `<title>`. They are untracked and
  ignored (`.gitignore:5`): do not `git add`, do not `git add -f`, do not commit them; record
  the nine names and sizes in the closeout report and the `### Done, measured` block. If a
  later commit of this section changes `dash_render.py` (a fix found by 19-10 or 19-11),
  rerun the three scripts before 19-12.

## Boundaries

- Do not fix a gap here. A red test, a failed cert script, a gate problem or a missing
  BUGS.md entry is a defect of the section that owns the gap: fix it in that section's
  files, under that section's rules (a failing regression test first), in a commit with
  that gap's id, and then return to the closeout step that found it. Never weaken or delete
  a test to make a run green; never mark a skip as a pass.
- Do not reword a section's CHANGELOG fact, BUGS.md entry or help text; only placement,
  completeness and the release date are this section's.
- Do not rewrite GAPS2.md's audit text (DISCOVERY Q23): only the 23 Tracked lines change
  (22 in scope plus C4), each keeping its old text after `was:`; no residual is written
  before the maintainer approved the list (19-03).
- Do not touch GAPS.md, the `## Traceability matrix`, WP-01..27, or any test's assertion.
- Do not run `git checkout main`, `git merge` (other than `git merge --no-edit main` before a
  commit, which must report `Already up to date`), `git push`, or `make hooks`; do not commit
  to `main` (CLAUDE.md rule 5).
- Do not add C4/E4 to `**GAPS2 closed:**`; do not "close" a residual.
- Do not start a second full run while one executes, and do not relaunch to check on one
  (CLAUDE.md rule 11): read its log.
- Do not commit any `.html` page (they are ignored; `git add -f` is not used for them), and
  do not add a page to `test_packaging.py`'s `_ROOT_ALSO`.
- Do not add a `.cscript` file, edit `test/run_all_cscripts.do` or the hygiene pins (D11:
  S02 alone did); a fold of `test_gaps2_truth.cscript` blocks is done in the owning section's
  files under that section's rules, not here.
- Do not write the invariants into `CLAUDE.md` (D14: `AGENTS.md`).

## Stata truth

None added. This section runs Stata only through `make cert` and `make gate`, whose runner
scripts (`scripts/run_cert_suite.sh`, `scripts/run_release_gate.sh`) invoke the console binary
of CLAUDE.md rule 10 in batch from a `mktemp -d` directory with `STATATMP="$dir/tmp/"`, one
session at a time (this section runs alone in batch 4, so no slot is contended); plus the
one-line `python_exec` check (`scripts/stata_python_exec.sh`) and, if needed, the one-line
restore do-file of TR-19.6 and the single-script driver of `BRIEF.md` "Running one cscript", both run as
`scripts/stata_slot.sh <scratch> <scratch>/<file>.do` (C14). No fixture is written; nothing
needs `git add -f`.

## TDD test stubs

This section adds no test. Its failing-first step is documentary: after 19-05 writes
`— DONE` and before 19-04 has run, `test/test_tracking_documents.py::TestGaps2AndRoadmapAgree::test_every_gaps2_id_a_done_package_lists_is_closed_by_it`
fails naming every id whose Tracked line is not the Closed form; 19-04 turns it green. (The
tasks below order 19-04 before 19-05 so the tree is never committed red; the executor proves
the guard bites inside 19-05, on an uncommitted reverted Tracked line, and records its output
in 19-05's commit body as a `Regression:` line.)

Tests that become non-vacuous at DONE (all in `test/test_tracking_documents.py::TestGaps2AndRoadmapAgree`,
from section 01): `test_every_gaps2_id_a_done_package_lists_is_closed_by_it`,
`test_every_closed_gaps2_entry_is_listed_by_its_package`,
`test_every_closed_gaps2_entry_names_a_closed_bugs_entry_and_a_commit`,
`test_a_deferred_gaps2_entry_names_its_package_and_a_reason`.

Pinned tests to flip: none. Tests that must already have been flipped by their sections
(check they are, by name, from the commit bodies' `Flipped:` lines): the port-clamp tests
(`test_render_cli_port.py:151,161`, `test_resource_limits.py:1279`, `test_adversarial_matrix.py:860,878`),
`test_help_claims_4.py:1643` (viewport), `TestTheModesDifferHere.test_a_brush_dims_unselected_points_less_when_served`,
`test_dates.py::TestNumericDisplayFormats`, `test_axis_options.py::TestAxisScale`,
`test_suboption_warnings.py` (`valuelabel`), `test_help_claims_7.cscript` HC7-02, the old
minimum assertions in `test_setup_python_gate.cscript`, `test_setup_honesty.cscript`,
`test_program_coverage.cscript` PC-19..21, `test_help_claims_8.cscript:786`,
`test_help_claims_8.py:1647`, and `test_mode_parity.py`'s bs `ALLOWED` clause.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| 22 fix commits, 22 closed entries, titles quotable, residual clauses collected | `git log 91d97be..HEAD`, `grep -c '^  - Resolution: Fixed .*(WP-28, ' BUGS.md` = 22, grep for `"` in those titles, grep `Residual, deferred (WP-28):` (19-01) | git, BUGS.md | n/a |
| No CHANGELOG marker left; each gap in its list; before/after present | `grep -c '<!-- WP-28 ' CHANGELOG.md` = 0; per-gap `grep -c '(WP-28, <ID>)'` inside each list's awk range (19-02) | CHANGELOG.md | n/a |
| The deferred list approved before it is written | checkpoint 19-03 | — | n/a |
| Every Tracked line in scope is the Closed form; C4 deferred | pytest, `test_tracking_documents.py::TestGaps2AndRoadmapAgree` (all), after 19-05 | GAPS2.md, ROADMAP.md, BUGS.md, git | n/a |
| No open S1/S2; every closed entry names an existing test | pytest, `test_tracking_documents.py::TestNoOpenEntryBlocksARelease`, `::TestEveryClosedEntryNamesATestThatExists` | BUGS.md, test/ | n/a |
| The invariants section exists and names tests that exist | `grep -c '^## Invariants introduced by WP-28' AGENTS.md` = 1; `pytest --collect-only -q` over every node it names (19-06) | AGENTS.md | n/a |
| The demo pages regenerate from the merged renderer and stay untracked | the three `scripts/regen_*.py` page scripts exit 0; nine pages hold `<title>`; `git status --porcelain` lists no `.html` (19-07) | — | saved pages |
| Version lines and Distribution-Date agree and are current | pytest, `test_pkg_metadata.py`, `test_help_claims_1.py::TestTheHeader`; the gate's date rule (19-08, 19-09) | six files | n/a |
| Full suite, strict, no skip | `make test` (Stata's Python), `make test-dev` (development interpreter), one at a time (19-09) | whole suite | yes: the parity corpus and every both-mode test run inside |
| Certification suite, no skip, within budget | `make cert` after the `python_exec` check, timed with `date +%s`; growth over `<scratch>/cert-baseline.log` at most about 300 s; per-block times from the `S<NN> start/end` lines (19-10) | every registered script (66) | yes: the scripts build saved and served pages |
| Release gate from an installed package | `make gate` (19-11) | examples/, schemes/ | yes: examples include server mode |
| Working tree clean of WP-28's work | `git status --porcelain` filtered of the maintainer's planning paths (19-12) | git | n/a |

Acceptance criteria:

- **AC-19.1** `grep -c '<!-- WP-28 ' CHANGELOG.md` prints 0; each of the 22 ids appears in a
  line ending `(WP-28, <ID>)` in its place: B1 B2 B3 B5 B6 B7 C2 D1 E1 E2 E3 E14 G6 G16 X1 X2
  in the `**WP-28 (GAPS2 audit, 25sep2026)**` group at the end of `### Results that change`,
  G1 G2 at the end of `### Changed behaviour`, K2 at the end of `### Requirements`, E14
  (served) F1 G3 G5 under `### Fixed in WP-28` (S04's lines there end `(WP-28 S04)`); the
  `### Requirements` items above K2 state Python 3.13, bokeh 3.8, pandas 2.3, numpy 2.3.
- **AC-19.2** `grep -c '^- \*\*Tracked:\*\* Closed in WP-28, BUGS\.md "' GAPS2.md` prints 22
  and `grep -c '^- \*\*Tracked:\*\* Deferred (WP-28):' GAPS2.md` prints 1; every such line
  ends with `was: …`; the number of Tracked lines holding `residual deferred (WP-28):` equals
  the number of entries in `<scratch>/wp28-residuals.txt` (D1 counted once); D1's line holds
  `CMYK, hsv and colour*#`.
- **AC-19.3** `grep -c '^## WP-28 .* — DONE$' ROADMAP.md` prints 1, and
  `python3 -m pytest test/test_tracking_documents.py -q` passes, no skip.
- **AC-19.4** `make test` and `make test-dev` logs each end with `0 failed`, no `skipped`,
  no `strict mode` line; the interpreter and versions are printed at the top of each log.
- **AC-19.5** `make cert`'s verdict: every registered script (66) passed, 0 skipped, and
  `scripts/stata_python_exec.sh` printed `/opt/anaconda3/bin/python3` before the run; the
  wall time minus the baseline's is at most about 300 s (D11), or the fold of TR-19.6 was
  done and the rerun is within it.
- **AC-19.6** `make gate` exits 0 with no problem line; its log path is recorded.
- **AC-19.7** `grep -c '^- \[ \] Title:' BUGS.md` prints the count of open entries, all
  graded S3 (`TestNoOpenEntryBlocksARelease` green); `grep -c '^  - Resolution: Fixed .*(WP-28, ' BUGS.md`
  prints 22.
- **AC-19.8** `git status --porcelain | grep -v -E '^(.. )?(\.ultraplan|phases/|REMAINING\.md|CLAUDE\.md|scripts/__pycache__)'`
  prints nothing (the regenerated `.html` pages are ignored and never appear); the final
  report states `git checkout main && git merge s3-bugs` and that it was not run.
- **AC-19.9** `grep -c '^## Invariants introduced by WP-28' AGENTS.md` prints 1; the section
  has seven paragraphs, each naming at least one `test/` path; every `test_*.py::` node it
  names collects; `test_packaging.py` and `test_tracking_documents.py` pass.
- **AC-19.10** The three page scripts exited 0 on the merged tree; the nine pages exist and
  hold `<title>`; `git ls-files | grep -c '\.html$'` prints 0.

## Tasks

Commit boundary: **six commits, one per step**, made by 19-02 (CHANGELOG), 19-04 (GAPS2.md),
19-05 (ROADMAP.md DONE), 19-06 (AGENTS.md), 19-09 (the six dated files) and 19-12 (the
measurements), every subject ending `(WP-28 S19)`; no gap entries and no `(GAPS2 <ID>)`
subject here (a gap defect found by a run is fixed and committed in its own section). This
section runs in the main checkout on `s3-bugs` (batch 4, alone; no worktree, nothing landed
with `patch -p1`). Before each commit: `git merge --no-edit main` (expected `Already up to
date`) and the targeted tests the task names; the full suite runs in 19-09 as `make test` and
`make test-dev` (rule 11). Every one-off Stata run goes through
`scripts/stata_slot.sh <scratch> <scratch>/<file>.do` (C14; a cscript through the driver of
`BRIEF.md` "Running one cscript"); `make cert` and `make gate` run only here, in batch 4. No AI references anywhere.

<task type="auto" id="19-01">
  <name>Inventory the merged branch and the guards</name>
  <files>none</files>
  <action><![CDATA[
    In `/Users/billy/Desktop/Programs/StataPrograms/d/dash`, confirm `git worktree list` shows
    only the main checkout and `git status --porcelain` shows only the maintainer's planning
    paths (AC-19.8's filter). Run `python3 -m pytest test/test_tracking_documents.py test/test_packaging.py -q`.
    Build `<scratch>/wp28-map.tsv` (TR-19.1): for each of the 22 ids, the hash from
    `git log --format='%h %s' 91d97be..HEAD | grep -E "\(GAPS2 ([A-Z][0-9]+, )*<ID>(, [A-Z][0-9]+)*\)"`
    (a subject may name several ids: section 12 closes E3 and G6 in one commit whose subject
    ends `(GAPS2 E3, G6)`, and that one commit is the fix commit of both) and the title of the
    BUGS.md entry whose Resolution field reads `  - Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). …`
    (D3; `grep -n '^  - Resolution: Fixed .*(WP-28, <ID>)' BUGS.md`, then the nearest
    `- [x] Title:` line above it). Build `<scratch>/wp28-residuals.txt` from every
    `Residual, deferred (WP-28):` clause in those 22 entries (id, title, clause text; the plan
    expects G1, G3, X2, E14, D1, B5, K2). Fail the task, naming the section, if an id has no
    commit or more than one, no entry or more than one, a title holding `"`, or if
    `grep -c '<!-- WP-28 ' CHANGELOG.md` is not 0 (a section's CHANGELOG line is missing).
    Check `grep -n 'Requires:' dash.pkg` and the `### Requirements` items of CHANGELOG.md
    state the K2 floor. Check `<scratch>/cert-baseline.log` exists and its first and last
    lines are epoch seconds (index.md step 0b); if not, note it for 19-10. Run the
    python_exec check of TR-19.6 and record its output. No commit.
  ]]></action>
  <verify><![CDATA[`wc -l <scratch>/wp28-map.tsv` prints 22; `awk -F'\t' '{print $1}' <scratch>/wp28-map.tsv | sort | tr '\n' ' '` prints the 22 ids; `grep -c '^  - Resolution: Fixed .*(WP-28, ' BUGS.md` prints 22; `wc -l <scratch>/wp28-residuals.txt` equals `grep -c 'Residual, deferred (WP-28):' BUGS.md`; the two targeted pytest files pass; the CHANGELOG marker count is 0; `scripts/stata_python_exec.sh` printed `/opt/anaconda3/bin/python3`.]]></verify>
  <done>Every gap had exactly one fix commit and one closed BUGS.md entry in the D3 form with a quotable title, the residual clauses were collected, the CHANGELOG had no marker left, the K2 floor was stated, the tracking guards were green on the merged tree, the cert baseline's presence was noted, and Stata's Python was set.</done>
</task>

<task type="auto" id="19-02">
  <name>Reconcile the CHANGELOG for WP-28</name>
  <files>CHANGELOG.md</files>
  <action><![CDATA[
    In `/Users/billy/Desktop/Programs/StataPrograms/d/dash/CHANGELOG.md`, check each gap's
    line against TR-19.2 in its place: the `**WP-28 (GAPS2 audit, 25sep2026)**` group at the
    end of `### Results that change` for B1 B2 B3 B5 B6 B7 C2 D1 E1 E2 E3 E14 G6 G16 X1 X2,
    the end of `### Changed behaviour (may need your do-files changed)` for G1 G2, the end of
    `### Requirements` for K2, and `### Fixed in WP-28` for E14 served, F1, G3, G5 and S04's
    `(WP-28 S04)` lines; a Results line names the command, the value dash drew (the failing
    test's recorded output at 91d97be, from the gap's fix commit body, Q24) and the value it
    now draws (twoway's); every gap line ends `(WP-28, <ID>)`; each place keeps the order of
    S01 TR-01.7's markers. Move or complete a line, never reword its fact; where a value is
    missing, take it from the gap's BUGS.md entry or its commit body; a WP-28 line found in
    another group or heading is moved to its place. Leave `## 2.0, 24sep2026` and line 5's
    date for 19-12. Run `python3 -m pytest test/test_tracking_documents.py -q` (the
    retired-link scan reads every .md), `git merge --no-edit main`, and commit with the
    subject `List what WP-28 changed, once, in the CHANGELOG (WP-28 S19)`; the body says no
    test reads CHANGELOG.md beyond that scan and that the full runs follow in 19-09.
  ]]></action>
  <verify><![CDATA[`for id in B1 B2 B3 B5 B6 B7 C2 D1 E1 E2 E3 E14 G6 G16 X1 X2; do awk '/^### Results that change/,/^### Security/' CHANGELOG.md | grep -c "(WP-28, $id)"; done` prints 1 sixteen times and each id's command appears in that range; `for id in G1 G2; do awk '/^### Changed behaviour/,/^### Removed/' CHANGELOG.md | grep -c "(WP-28, $id)"; done` prints 1 twice; `awk '/^### Requirements/,/^### Fixed in WP-28/' CHANGELOG.md | grep -c '(WP-28, K2)'` prints 1; `for id in E14 F1 G3 G5; do awk '/^### Fixed in WP-28/,/^### Fixed after WP-27/' CHANGELOG.md | grep -c "(WP-28, $id)"; done` prints 1 four times; `grep -c '(WP-28, ' CHANGELOG.md` prints 23; `grep -c '<!-- WP-28 ' CHANGELOG.md` prints 0; `git log -1 --format=%B | grep -ci 'claude\|anthropic'` prints 0.]]></verify>
  <done><![CDATA[The CHANGELOG recorded each of the 22 gaps once, in its place, every gap line ending `(WP-28, <ID>)`, with before and after values for every changed number, text, colour or layout, and was committed.]]></done>
</task>

<task type="checkpoint" id="19-03">
  <name>Approve the deferred residuals</name>
  <files>none</files>
  <action><![CDATA[
    Present to the maintainer, before any GAPS2.md line is written, the deferred list as it
    will be written: every entry of `<scratch>/wp28-residuals.txt` with its clause text (the
    plan expects G1: the qualifier, by()-order and ustrfix columns stay in the user's dataset
    and a user variable named like a Bokeh glyph field is still shadowed in `hover()`/`mlabel()`,
    DISCOVERY Q7 amended; G3: JSON export stays, row-drawing layers stay bounded, the served
    app embeds every row, Q9; X2: the continuous colour default and `colorrule()`/`colorstart()`/`colorend()`
    stay as documented, Q5; E14: `filterposition(left)` recorded, not fixed; D1: CMYK, hsv and
    `colour*#` values are GAPS2 D7's and third-party scheme files are excluded by decision Q30,
    review F-11 and D13; B5: a layer that drew nothing has no key, so `order()` naming its
    number draws nothing; K2: no Python 3.10 venv matrix, Q8), plus C4/E4 (out of scope by
    Q3; nothing ported to `_FILTER_JS`). Show the exact Tracked-line text for each of these
    and for the plain Closed lines of the other ids. Ask for a yes, or for a residual to be
    sent back to its section before 19-04 runs.
  ]]></action>
  <verify><![CDATA[The maintainer approves every deferred reason and the Tracked-line texts as shown, or names the residual to revisit and the section that owns it; nothing was written to GAPS2.md.]]></verify>
  <done>The maintainer approved the residuals WP-28 defers, with their reasons as BUGS.md records them, before they were written into the audit.</done>
</task>

<task type="auto" id="19-04">
  <name>Record the closures in GAPS2.md</name>
  <files>GAPS2.md</files>
  <action><![CDATA[
    Using `<scratch>/wp28-map.tsv` and the list 19-03 approved, rewrite the `- **Tracked:**`
    line of each of the 22 entries in `/Users/billy/Desktop/Programs/StataPrograms/d/dash/GAPS2.md`
    to TR-19.3's form, `Closed in WP-28, BUGS.md "<title>", commit <hash>`, appending
    `; residual deferred (WP-28): <clause text>` for every id in `<scratch>/wp28-residuals.txt`
    (D1's reason always ending `CMYK, hsv and colour*# scheme values are D7's (GAPS2 D7), not
    read here; third-party scheme files excluded by decision (DISCOVERY Q30)`), and
    `; was: <old text>` for all 22. Rewrite C4's line to `Deferred (WP-28): out of scope by
    decision (DISCOVERY Q3), with its duplicate E4; nothing is ported to _FILTER_JS on its
    account; was: <old text>`. Locate each line with `grep -n '^### <ID>\.' GAPS2.md` and the
    first `- **Tracked:**` after it; each Tracked line stays one physical line (wrap nothing);
    change nothing else. Run `python3 -m pytest test/test_tracking_documents.py -q` (WP-28 is
    not DONE yet, so the closure tests are still vacuous on the documents) and the reader
    one-liner `python3 -c "import sys; sys.path.insert(0,'test'); import test_tracking_documents as t; g,_=t._parse_gaps2(open('GAPS2.md').read()); print(sum(1 for v in g.values() if v['closed']), sum(1 for v in g.values() if v['deferred']))"`,
    which must print `22 1`. `git merge --no-edit main`; commit with the subject `Name the
    package, entry and commit that closed each GAPS2 gap in scope (WP-28 S19)`.
  ]]></action>
  <verify><![CDATA[`grep -c '^- \*\*Tracked:\*\* Closed in WP-28, BUGS\.md "' GAPS2.md` prints 22; `grep -c '^- \*\*Tracked:\*\* Deferred (WP-28):' GAPS2.md` prints 1; `grep -c '; was: ' GAPS2.md` prints 23; `grep -c '; residual deferred (WP-28): ' GAPS2.md` equals the number of ids in `<scratch>/wp28-residuals.txt` (D1 counted once); `grep -c 'CMYK, hsv and colour\*#' GAPS2.md` is at least 1; `git diff --stat HEAD~1 -- GAPS2.md` shows 23 insertions and 23 deletions (each Tracked line is one physical line; wrap nothing); the Python one-liner prints `22 1`.]]></verify>
  <done>Each GAPS2 entry in scope named WP-28, its BUGS.md title and its commit, every residual and C4/E4 were marked deferred with their approved reasons, the old audit text was kept after `was:`, and the change was committed.</done>
</task>

<task type="auto" id="19-05">
  <name>Mark WP-28 done in ROADMAP.md</name>
  <files>ROADMAP.md</files>
  <action><![CDATA[
    In `/Users/billy/Desktop/Programs/StataPrograms/d/dash/ROADMAP.md`, append ` — DONE` to
    the `## WP-28 · …` heading and add the `### Done, measured (<ddmonyyyy>)` block of
    TR-19.4 after the `#### GAPS2 traceability` table and before the section's closing `---`,
    with `<to be measured in 19-12>` where the run numbers, the cert wall times and the page
    list go. Before editing, prove the guard bites: temporarily revert one Tracked line in
    GAPS2.md to `new.` (do not commit), run
    `python3 -m pytest test/test_tracking_documents.py -q -k Gaps2`, record the failure
    naming that id in `<scratch>/19-05-guard.txt`, restore the line (`git checkout -- GAPS2.md`).
    Then run `python3 -m pytest test/test_tracking_documents.py -q` (all green, none
    skipped), `git merge --no-edit main`, and commit with the subject `Mark WP-28 done: the
    22 GAPS2 gaps are closed, test first (WP-28 S19)`, the body opening with the guard's
    recorded failure as `Regression: test/test_tracking_documents.py::TestGaps2AndRoadmapAgree::test_every_gaps2_id_a_done_package_lists_is_closed_by_it -- failed on a reverted Tracked line with <text>`.
    Keep every line of the block free of `# `/`## ` at line start and of the text `Gaps closed`.
  ]]></action>
  <verify><![CDATA[`grep -c '^## WP-28 .* — DONE$' ROADMAP.md` prints 1; `grep -c '## Traceability matrix' ROADMAP.md` prints 1; `python3 -m pytest test/test_tracking_documents.py -q 2>&1 | tail -1` passes with no skip; `<scratch>/19-05-guard.txt` names the id whose line was reverted; `git status --porcelain -- GAPS2.md` is empty; `git log -1 --format=%B | grep -c '^Regression: '` prints 1.]]></verify>
  <done>WP-28 was headed DONE with a measured block awaiting the run numbers, the closure guard was seen to fail on a stale Tracked line and to pass on the real ones, and the change was committed with that proof in its body.</done>
</task>

<task type="auto" id="19-06">
  <name>Record the WP-28 invariants in AGENTS.md</name>
  <files>AGENTS.md</files>
  <action><![CDATA[
    Append to `/Users/billy/Desktop/Programs/StataPrograms/d/dash/AGENTS.md`, after its last
    numbered rule and one blank line, the heading `## Invariants introduced by WP-28` and the
    seven paragraphs of TR-19.10 in that order (the `__dash` prefix; the served copy lists;
    the Python/JavaScript twins; `scripts/stata_slot.sh` and the cscript driver; the
    CHANGELOG marker convention; the BUGS.md Resolution form `- Resolution: Fixed <ddmonyyyy>
    (WP-nn, <ID>). … Pinned by test/… .`; the fixture `_meta` stamp `stata_version`,
    `born_date`, `dash_commit`, `extracted`), each one paragraph naming its guarding test as
    `test/<file>.py::<Class>[::<test>]` exactly as it exists on the merged tree (read the S07,
    S03, S04, S05, S17 test files to take the names; take the fixture tests from the fix
    commits' `Fixture:` lines). Write no Markdown link to `PLAN.md` or `TODO.md`
    (`test_nothing_links_them` scans AGENTS.md) and no AI reference. Run
    `python3 -m pytest test/test_tracking_documents.py test/test_packaging.py -q`, then
    `python3 -m pytest --collect-only -q <every test_*.py::… node the section names>` and
    require each to collect at least one test. `git merge --no-edit main`; commit `AGENTS.md`
    alone with the subject `Record the invariants WP-28 introduced, each with its guarding
    test (WP-28 S19)`.
  ]]></action>
  <verify><![CDATA[`grep -c '^## Invariants introduced by WP-28' AGENTS.md` prints 1; `awk '/^## Invariants introduced by WP-28/,0' AGENTS.md | grep -c 'test/'` is at least 7; `awk '/^## Invariants introduced by WP-28/,0' AGENTS.md | grep -c '](PLAN.md)\|](TODO.md)'` prints 0; the `--collect-only` run lists at least one test per node and no error; `python3 -m pytest test/test_tracking_documents.py test/test_packaging.py -q 2>&1 | tail -1` passes; `git log -1 --format=%s | grep -c '(WP-28 S19)'` prints 1; `git log -1 --format=%B | grep -ci 'claude\|anthropic'` prints 0.]]></verify>
  <done>AGENTS.md ended with the seven WP-28 invariants, each naming a guarding test that collects on the merged tree, and the section was committed on its own.</done>
</task>

<task type="auto" id="19-07">
  <name>Regenerate the demo pages on the merged tree</name>
  <files>none</files>
  <action><![CDATA[
    From `/Users/billy/Desktop/Programs/StataPrograms/d/dash` run, one after another,
    `python3 scripts/regen_dashboards.py`, `python3 scripts/regen_comprehensive.py` and
    `python3 scripts/regen_bootstrap_examples.py`, capturing each exit status. They write
    nine untracked pages beside `dash_render.py`: `scatter.html`, `dashboard.html`,
    `full_dashboard.html`, `kelly22ex_dashboard.html`, `comprehensive_demo.html`,
    `bs_equal_cols.html`, `bs_kpi_hero.html`, `bs_stacked.html`, `bs_responsive.html`. The
    plan's earlier assumption that these pages were checked in was wrong: `.gitignore:5` is
    `*.html` and `git ls-files` holds none, so do not `git add` them, do not `git add -f`
    them, and do not commit them (C15). Record each page's name and size for the closeout
    report and for the `### Done, measured` block. No commit.
  ]]></action>
  <verify><![CDATA[Each of the three scripts exited 0; for each of the nine pages `test -s <page> && grep -c '<title>' <page>` prints at least 1; `git status --porcelain | grep -c '\.html$'` prints 0 and `git ls-files | grep -c '\.html$'` prints 0.]]></verify>
  <done>The nine demo pages were regenerated from the merged renderer and left untracked, as the repository keeps them, with nothing staged or committed.</done>
</task>

<task type="auto" id="19-08">
  <name>Date the three shipped source files</name>
  <files>dash.ado, dash_setup.ado, dash_parse.mata</files>
  <action><![CDATA[
    Set `*! Version: 2.0  <ddmonyyyy>` for today in `dash.ado:29`, `dash_setup.ado:16` and
    the line `grep -n '\*! Version:' dash_parse.mata` reports (the sixth anchor is that grep,
    not "the `*! Version:` line"). These three lines and the three of 19-09 are one commit,
    made by 19-09, because `test/test_pkg_metadata.py:49-60` and
    `test_help_claims_1.py:190-196` hold all six equal (TR-19.5); do not run the metadata
    test between the two steps, and if the two steps straddle midnight redo this one. No
    commit.
  ]]></action>
  <verify><![CDATA[`grep -n '^\*! Version: 2.0  ' dash.ado dash_setup.ado dash_parse.mata` prints three lines carrying today's `ddmonyyyy`; `git status --porcelain` lists exactly those three files as modified.]]></verify>
  <done>The three shipped source files carried today's version date, uncommitted, awaiting the package and help lines of 19-09.</done>
</task>

<task type="auto" id="19-09">
  <name>Date the package and run both suites</name>
  <files>dash.pkg, dash.sthlp, dash_setup.sthlp</files>
  <action><![CDATA[
    Set `{* *! version 2.0  <ddmonyyyy>}` in `dash.sthlp:2` and `dash_setup.sthlp:2`, and in
    `dash.pkg` `d Version: 2.0  <ddmonyyyy>` (24) and `d Distribution-Date: <yyyymmdd>` (25),
    for the same day as 19-08. Run
    `python3 -m pytest test/test_pkg_metadata.py test/test_help_claims_1.py test/test_packaging.py -q`.
    Then `git merge --no-edit main` (expect "Already up to date"), and run `make test` in the
    background with output to `<scratch>/make-test.log`; when it has exited, read the log's
    tail; then `make test-dev` to `<scratch>/make-test-dev.log` the same way. Never start the
    second while the first runs; never relaunch to check. If either is red, stop: the failing
    test belongs to a section, fix it there under that section's rules and commit with that
    gap's id, then rerun only that file (`python3 -m pytest test/<file> -q`) and, once green,
    rerun the make target that failed (prefix `FULL_SUITE_RERUN=1` if the hook asks). Commit
    the six dated files (19-08's three and these three) as ONE commit with the subject `Date
    the 2.0 release candidate for WP-28 (WP-28 S19)`, the body quoting both logs' final lines
    and interpreter versions.
  ]]></action>
  <verify><![CDATA[`tail -3 <scratch>/make-test.log` and `tail -3 <scratch>/make-test-dev.log` each show a pass count, `0 failed` or no `failed`, no `skipped`, no `strict mode`; the targeted three files pass; `grep -n 'Distribution-Date' dash.pkg` shows today's date; `git show --stat HEAD | grep -c '^ dash'` prints 6 (the six dated files in one commit); `git log -1 --format=%B | grep -ci 'claude\|anthropic'` prints 0.]]></verify>
  <done>The package was dated today in all seven lines, and the full pytest suite passed strict with no skip under Stata's Python and under the development interpreter on the dated tree, which was committed as one commit.</done>
</task>

<task type="auto" id="19-10">
  <name>Run the certification suite and time it</name>
  <files>none</files>
  <action><![CDATA[
    Run `STATA=/usr/local/bin/stata-mp sh scripts/stata_python_exec.sh` and require
    `/opt/anaconda3/bin/python3`; if empty, write `<scratch>/pyexec_fix.do` as TR-19.6 says,
    run `scripts/stata_slot.sh <scratch> <scratch>/pyexec_fix.do`, and check again. Then run
    `{ date +%s; make cert; echo "exit=$?"; date +%s; } > <scratch>/make-cert.log 2>&1` in
    the background and wait for it to exit (it runs every registered script -- 66 after
    WP-28, the 65 of 91d97be plus `test/test_gaps2_truth.cscript` -- through the console
    binary from a scratch directory with its own STATATMP; do not run any other Stata
    meanwhile). Read the log: the verdict must list every registered script as passed and the
    summary as `(n passed, 0 skipped)`, `exit=0`, and the wall time is the last line minus
    the first. If any script SKIPped, run the python_exec check again before believing it; if
    `python_exec` was lost, restore it and rerun (prefix `FULL_SUITE_RERUN=1` if the hook
    asks). A FAIL belongs to a section: fix it there, commit with the gap's id, rerun that
    one script through the driver (`printf 'cd "%s/test"\ndo "%s/test/%s"\n' "<repo>" "<repo>" "<script>.cscript" > <scratch>/run_<script>.do`
    then `scripts/stata_slot.sh <scratch> <scratch>/run_<script>.do`, with `GAPS2_ONLY=S<NN>`
    in the environment for one block of `test_gaps2_truth.cscript`) and read its log, then
    rerun this task. Compare the wall time with `<scratch>/cert-baseline.log` (last line minus
    first line; the orchestrator's run on the unmodified tree, index.md step 0b): if the
    growth exceeds 300 s, read the per-block times from the `S<NN> start`/`S<NN> end` lines
    of the cert log (`grep -E '^S[0-9]{2} (start|end) ' <cert log>`), fold the slowest blocks
    in the owning sections' files under their rules (D11: never a dropped comparison), commit
    with those gaps' ids, and rerun this task. Save the certification log path the runner
    prints, both wall times and the growth. If the baseline log is absent, record "baseline
    not measured" and the after time. No commit.
  ]]></action>
  <verify><![CDATA[`grep -E 'passed|skipped|FAIL|exit=' <scratch>/make-cert.log | tail -5` shows every script passed, `0 skipped` and `exit=0`; `head -1 <scratch>/make-cert.log` and `tail -1 <scratch>/make-cert.log` are epoch seconds; the line `certification log: /…/run_all_cscripts.log` names a file that exists; `grep -c '\[ SKIP\]' <that log>` prints 0; `grep -c '\[ PASS\]' <that log>` prints 66; `grep -c '^S[0-9][0-9] end ' <that log>` equals the number of blocks in `test/test_gaps2_truth.cscript`; the wall time minus the baseline's is at most about 300 (or the fold was done and the rerun is).]]></verify>
  <done>The certification suite passed with every registered script and no skip, on a Stata whose python_exec was verified before and, if any skip appeared, after the run, and its wall time was measured and held within about five minutes of the pre-WP-28 baseline.</done>
</task>

<task type="auto" id="19-11">
  <name>Run the release gate from an installed package</name>
  <files>none</files>
  <action><![CDATA[
    Run `make gate; echo "exit=$?"` in the background with output to `<scratch>/make-gate.log`
    and wait for it to exit: it copies what `dash.pkg` ships to a scratch source, net
    installs into a scratch PLUS, runs every `examples/*.do` and one page per shipped scheme
    from the install, checks adoupdate, and judges the log with `scripts/release_verdict.py`.
    Read the log: `exit=0` and no problem line. A `Distribution-Date … older than the newest
    change` problem means 19-09 was not committed before a shipped file changed again:
    re-date and recommit. An example that prints a diagnostic, a scheme page that falls back,
    or an install that fails belongs to the section whose change caused it: fix there, commit
    with the gap's id, and rerun `make gate` (and 19-10 if a shipped file changed, and 19-07
    if `dash_render.py` changed). Save the gate log path the runner prints. No commit.
  ]]></action>
  <verify><![CDATA[`tail -5 <scratch>/make-gate.log` shows no problem line, the line `exit=0`, and `release gate log: /…/*.log` naming a file that exists.]]></verify>
  <done>The release gate passed from a net-installed copy of exactly what dash.pkg ships: every example and every scheme page at rc 0 with no diagnostic, adoupdate as expected, the Distribution-Date current.</done>
</task>

<task type="auto" id="19-12">
  <name>Record the measurements and report the merge</name>
  <files>ROADMAP.md, CHANGELOG.md</files>
  <action><![CDATA[
    Replace every `<to be measured in 19-12>` in WP-28's `### Done, measured` block with the
    numbers from the four logs: passed and skipped counts and the interpreter versions for
    `make test` and `make test-dev`, `66 of 66` cert scripts with the wall time before
    (`<scratch>/cert-baseline.log`) and after and the growth in minutes (D11), the gate's
    example and scheme-page counts, each log's path, and the nine regenerated pages with
    their sizes (untracked, C15); state that no S1/S2 entry is open and 22 closed WP-28
    entries name their tests (`TestEveryClosedEntryNamesATestThatExists`), that `AGENTS.md`
    carries the invariants (19-06), that the tree is clean of WP-28's work, and end with the
    merge command as text: `git checkout main && git merge s3-bugs` — reported, not run. Set
    `CHANGELOG.md:3` to `## 2.0, <ddmonyyyy> (release candidate)` and line 5's `now
    <yyyymmdd>` to the Distribution-Date of 19-09. Run the final checks of
    AC-19.1..AC-19.10 (targeted: `python3 -m pytest test/test_tracking_documents.py test/test_pkg_metadata.py test/test_packaging.py -q`;
    the full runs of 19-09..19-11 measured a tree that differs from this one only by these
    two documents, and no shipped file changed since). `git merge --no-edit main`; commit
    with the subject `Record WP-28's release measurements (WP-28 S19)`. Then report, in this
    order: the four log verdicts with paths, the cert wall times and growth, the open-entry
    count and grades, the 22 closed entries, the residuals deferred, the nine pages
    regenerated, and the merge command with the words "not run".
  ]]></action>
  <verify><![CDATA[`grep -c 'to be measured' ROADMAP.md` prints 0; `awk '/^## WP-28 /,/^## Traceability matrix/' ROADMAP.md | grep -c 'git checkout main && git merge s3-bugs'` prints 1; `awk '/^## WP-28 /,/^## Traceability matrix/' ROADMAP.md | grep -c 'wall time'` is at least 1; `sed -n '3p' CHANGELOG.md` shows the new date; the targeted pytest run passes with no skip; AC-19.8's filtered `git status --porcelain` prints nothing; `git log -1 --format=%B | grep -ci 'claude\|anthropic'` prints 0.]]></verify>
  <done>WP-28's measured block quoted the four green runs by number and log path, the cert suite's wall times and growth, and the regenerated pages; the CHANGELOG was dated; the working tree was clean of WP-28's work; every commit was on `s3-bugs`; and the merge command had been reported and not run.</done>
</task>

## Section completion criteria

- Six commits on `s3-bugs` (19-02, 19-04, 19-05, 19-06, 19-09, 19-12), each with a subject
  ending `(WP-28 S19)`, none mentioning an AI, none on `main`; `git checkout main && git merge
  s3-bugs` reported, not run.
- The maintainer approved the deferred list (19-03) before 19-04 wrote it.
- `make test`, `make test-dev`, `make cert` and `make gate` each ran once on the final tree
  (or once more after a section's fix), all green, no skip, logs named in ROADMAP.md; the
  cert suite ran every registered script (66) and its wall time grew by at most about five
  minutes over the pre-WP-28 baseline, or was folded until it did (D11).
- `TestGaps2AndRoadmapAgree`, `TestNoOpenEntryBlocksARelease` and
  `TestEveryClosedEntryNamesATestThatExists` green with WP-28 DONE; 22 Closed Tracked lines
  and one Deferred; 22 entries whose Resolution reads `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). …`;
  no `<!-- WP-28 ` marker; every gap's CHANGELOG line ends `(WP-28, <ID>)` in its place.
- `AGENTS.md` ends with "Invariants introduced by WP-28", seven paragraphs, every named test
  collecting (19-06).
- The nine demo pages were regenerated on the merged tree and are untracked (19-07).
- The seven date lines agree and equal the Distribution-Date; the gate's date rule passed.

## Notes

- **Order matters for the date rule.** Commit 19-09 before `make gate`; any later commit that
  touches a shipped file (a section's fix found by 19-10 or 19-11) makes the newest
  shipped-file change later than the Distribution-Date, so re-date in that same day or bump
  the date again before rerunning the gate.
- **`make` is not counted by the launch hook, the conftest lock still is.** Two pytest
  targets in a row are fine sequentially; a second whole-suite pytest started while one runs
  fails at once with `a full test-suite run is already in progress`. Start each target in the
  background, wait for its exit, read its log; never poll by relaunching.
- **A run of cert SKIPs in 0-1 s each is the `python_exec` drop**, not a pass. Check
  `scripts/stata_python_exec.sh` before the suite and after any skip; restore with
  `set python_exec /opt/anaconda3/bin/python3, permanently` from a batch do-file run through
  `scripts/stata_slot.sh`, never the GUI (`.claude/hooks/block-stata-gui.sh` blocks it anyway).
- **The cert baseline.** `<scratch>/cert-baseline.log` is written by the orchestrator before
  batch 1 (`index.md` step 0b) with `{ date +%s; make cert; date +%s; }`; the runner's log
  carries only its start timestamp (`run_all_cscripts.do:33`), so the log alone gives no
  duration; the per-block times come from the `S<NN> start`/`S<NN> end` lines the
  `test_gaps2_truth.cscript` blocks print (`BRIEF.md` "Certification scripts"). WP-27's block has no time to compare
  with. Do not re-check out 91d97be to measure it (Q24).
- **One script, one block.** A cscript is never handed to `scripts/stata_slot.sh` itself: the
  runner `cd`s into `test/` first and the scripts open `cscript … adodir ".."` and
  `do "cert_helpers.do"` relative to it, so a two-line driver in the scratch directory does
  the `cd` and the `do` (`BRIEF.md` "Running one cscript"; `index.md` step 0a); `GAPS2_ONLY=S<NN>` in the driver run's environment
  limits `test_gaps2_truth.cscript` to one section's block.
- **Where a red test belongs.** The closeout owns no fix. Find the section from the test file
  or the cscript case, fix it under that section's rules in that section's files, and commit
  with that gap's id so 19-04's map stays true; if the fix changes a BUGS.md entry's title,
  update the GAPS2 Tracked line in the same commit (the guard fails otherwise). A cscript case
  id keeps its section prefix (TBG-, AL-, LO-, CV-, AE-, KF-, SPU-, HON-, UN-, SV-, DL-, CQ-,
  QS-; C7), which is how the owning section is found inside `test_gaps2_truth.cscript`.
- **The gate allows no diagnostic**: a section that made an example print a note it did not
  declare must either stop the note (an honoured option prints nothing, DISCOVERY Q22) or, if
  the note is intended, declare it in the example's header `*! release-gate allows: <text>`.
- **The open entries stay four, all S3** (BUGS.md 2523, 2559, 2595, 2601) unless a section
  closed one on the way; `TestNoOpenEntryBlocksARelease` is the judge, not a count.
- **The maintainer's planning files** (`.ultraplan*`, `phases/`, `REMAINING.md`, `CLAUDE.md`,
  `scripts/__pycache__/`) were left uncommitted at WP-27 by choice; "clean" means clean of
  WP-28's work, as AC-19.8's filter says. Do not commit them. The regenerated `.html` pages are
  ignored (`.gitignore:5`) and never show in `git status`; do not force them in.
- **Commit bodies** (consistency #30): this section's own commits carry no `Regression:` line
  except 19-05's guard proof; the `Flipped:` lines 19-05 reads into ROADMAP.md come from the
  fix commits, whose bodies use S01 TR-01.9's forms verbatim (`Regression: …`, `Flipped: <node>
  -- <old expectation> was wrong because <why>`, `Fixture: …`, `BUGS.md: "<title>" (closed)`).
- **Shared files and merge rules R1-R6** (`index.md`): this section edits CHANGELOG.md and
  reads BUGS.md (R3: it moves or completes lines, replaces no marker of its own and appends no
  entry), edits GAPS2.md, ROADMAP.md, AGENTS.md and the six dated files, and touches no
  registry (R1: `test/run_all_cscripts.do` and the hygiene pins are S02's; a fold happens in
  the owning section), no copy list or map (R2), no graph-key list (R4), no fixture (R5) and
  no parity corpus (R6). Nothing is landed with `patch -p1` here: batch 4 runs on the branch.
- **Timing.** Each pytest target is about two minutes on this machine (WP-25); the cert suite
  and the gate take longer and must run to completion; use the Bash tool's background mode
  with output redirected, not a foreground call that would time out at ten minutes.
