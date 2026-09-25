# Section 19: Closeout

> Part of: WP-28 · Gaps: all 22 (closed by sections 05-18; recorded and proven here) · Risk: green · Batch: 4 · Depends on: all · Blocks: none 


## Review amendments (Phase 4, 2026-09-25) — binding; they override any conflicting text below

> Batch **4** · Depends on **all** · Blocks **none** · Risk **green** · Commits: closeout commits (no gap entries)

- D2: 19-01 verifies `grep -c '<!-- WP-28 ' CHANGELOG.md` prints 0 and each entry sits in the list `index.md` Gap coverage names (E2 and the E14 bar move under Results that change).
- D6: the `make cert` run handed over from S02 lives here; Q25: a task regenerates every checked-in demo page with the `scripts/regen_*.py` scripts on the merged tree and commits them before the release gate.
- D8: a `type="checkpoint"` task precedes the task that marks the residuals deferred in GAPS2.md (approve the deferred list, including the D1 colour-form residual).
- D3: verify every WP-28 BUGS.md entry uses `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). … Pinned by test/…`; 22 closed entries name existing tests; zero open S1/S2.
- Q24: CHANGELOG old values come from the failing tests' recorded output at 91d97be.

Applies to every section:
- D1 (binding): tasks are work steps; commits are per gap (S01-S04: one each). The failing regression tests are written first and run against the unmodified tree; their output at 91d97be is recorded in the fix commit's message (Q24) and they are committed together with the fix, never alone (CLAUDE.md rule 4).
- D3 (binding): each gap's BUGS.md entry is appended at the END of BUGS.md in the closed form with `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). <what changed>. Pinned by test/<file>::<Class>::<test>.`
- D2 (binding): each closing task replaces the gap's `<!-- WP-28 <ID> -->` marker(s) that S01 placed in the CHANGELOG list named above; it does not add a new line elsewhere.
- D6 (binding): every Stata run is `scripts/stata_slot.sh <scratch-dir> <file>.do` (see `index.md` step 0); no section launches the full cert suite or the release gate.
- D5 (binding): shared files follow merge rules R1-R6 in `index.md` (cscript registration and hygiene pins, copy lists and maps, help/CHANGELOG/BUGS.md, graph-key lists, fixtures, parity corpus).
- D7: XML fields holding `&`, `<` or `>` are CDATA-wrapped (done mechanically); task names over 8 words are shortened and `done` fields put in the past tense during the detailed fixer pass.

Detailed edits from `../review/consistency.md`, `../review/requirements-security.md` and `../review/feasibility.md` (as adjusted by `../review/DECISIONS.md`) are applied to this file in the fixer pass; until then this block governs.

## Overview

When sections 01-18 have landed, every gap has a fix commit, a closed BUGS.md entry and a
CHANGELOG line, but nothing yet says so in one place, and nothing has measured the whole:
`ROADMAP.md`'s WP-28 is still open, GAPS2.md's 22 entries in scope still read
`- **Tracked:** new` (or the audit's other pre-fix text), the CHANGELOG's `### Fixed in WP-28`
may still hold a marker a section forgot, `dash.pkg`'s `Distribution-Date: 20260924` is older
than the shipped files it now describes (the gate refuses that: `scripts/release_verdict.py:213-215`),
and the exit criterion of PRD §8 (both suites green under both interpreters with no skip,
the certification suite with no skip, the release gate green from an installed package, no
open S1/S2, 22 closed entries naming existing tests, a clean tree) has been claimed by
sections one at a time, never measured on the merged tree.

After this section: the CHANGELOG lists every changed number, text, colour or layout once
under "Results that change" with the command, the old value and the new, the rest under
"Fixed", "Changed behaviour" and "Requirements"; each GAPS2 entry in scope carries
`Closed in WP-28, BUGS.md "<title>", commit <hash>`, and C4/E4 and the G1, G3, X2 and E14
residuals are marked deferred with DISCOVERY's reason; WP-28 is headed `— DONE` with a
`### Done, measured (<date>)` block that quotes the runs; the six version lines and the
Distribution-Date are dated; `make test`, `make test-dev`, `make cert` and `make gate` have
each run once on the final tree and passed; and the merge command is reported, never run.

The tracking tests of section 01 are this section's proof: writing `— DONE` turns
`test_every_gaps2_id_a_done_package_lists_is_closed_by_it` from vacuous into a check of all
22 Tracked lines, each against a closed BUGS.md entry and a commit that exists.

## Risk: [green] — documents, six dated lines, and four suite runs; no behaviour changes

- **Why.** No renderer, ado or Mata logic changes. The only shipped-file edits are the
  version-date lines one test already holds equal (`test/test_pkg_metadata.py:49-60`).
- **Risk factors.** (1) A run of certification SKIPs that is really Stata having lost its
  `python_exec` (report C §8) read as a pass. (2) The gate's Distribution-Date rule
  (`release_verdict.py:198-215`) failing on an undated package. (3) The PreToolUse hook's
  ledger refusing a third full launch, or a full run started while another executes. (4) A
  section's BUGS.md title holding a `"`, which the GAPS2 Tracked form cannot quote. (5) A
  marker left in the CHANGELOG, or a gap whose "Results that change" line lacks the old and
  new value. (6) The full runs measured on a tree that later edits change.
- **Mitigation.** (1) `display c(python_exec)` through `scripts/stata_python_exec.sh` before
  the cert suite and before trusting any SKIP; restore it if empty. (2) Task 19-05 dates the
  release before the gate. (3) `make` targets are run one at a time, in the background, each
  read from its log; the hook does not count `make`, the conftest lock still serialises.
  (4)-(5) are grep checks in 19-01 and 19-02. (6) Only ROADMAP.md's measured paragraph and the
  CHANGELOG heading change after the runs, and the targeted document tests are rerun.

## Dependencies

- Depends on: every section 01-18, merged into `s3-bugs` (each with `patch -p1` from its
  worktree, worktrees removed), so that the 22 fix commits, their BUGS.md entries and their
  CHANGELOG lines are on the branch.
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
each interpreter, 0 skipped, and 64 of 64 cert scripts (ROADMAP.md 4196-4203); the runner now
registers 65 (`test/run_all_cscripts.do`; `test_cscript_hygiene.py:418` requires registration).

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
- **E1/E3**: `%x` and `%H` are refused with r(198), not written (Q6). Not a residual: a
  documented refusal.

### The commit map this section reads

Section 01's TR-01.9 puts the gap id in every fix commit's subject, `… (GAPS2 B1)`, so
`git log --format='%h %s' 91d97be..HEAD | grep -F '(GAPS2 B1)'` gives B1's hash; each fix
commit also holds the gap's BUGS.md entry with `Resolution (WP-28, B1)`, whose title is what
the Tracked line quotes.

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

## Business requirements

- **BR-19.1** The CHANGELOG records every WP-28 gap once, in the right list, with before and
  after values wherever a drawn number, text, colour or layout changed; no marker remains.
- **BR-19.2** Every GAPS2 entry in scope names WP-28, its BUGS.md entry and its commit; C4/E4
  and the G1, G3, X2 and E14 residuals are marked deferred with DISCOVERY's reason; the audit
  text is otherwise unchanged (Q23).
- **BR-19.3** WP-28 is DONE in ROADMAP.md with a measured block quoting the four runs.
- **BR-19.4** The full pytest suite passes under both interpreters, strict, with no skip; the
  certification suite passes with no skip; the release gate passes from an installed package;
  BUGS.md has no open S1 or S2 and 22 closed WP-28 entries each naming a test that exists.
- **BR-19.5** The package is dated: version lines and Distribution-Date agree and are no
  older than the last shipped-file change.
- **BR-19.6** The working tree is clean of WP-28's work (the maintainer's own planning files
  may remain uncommitted, as at WP-27), and the merge command is reported, not run.

## Technical requirements

- **TR-19.1 Inventory (19-01).** From `git log --format='%h %s' 91d97be..HEAD`, build
  `<scratch>/wp28-map.tsv` with one row per gap: id, hash, BUGS.md title (from the entry whose
  Resolution starts `  - Resolution (WP-28, <ID>):`). Require exactly one fix commit and one
  entry per id, no title holding `"`, and no `<!-- WP-28 ` marker surviving. Run
  `python3 -m pytest test/test_tracking_documents.py test/test_packaging.py -q` first.
- **TR-19.2 CHANGELOG (19-02).** Under `### Fixed in WP-28`, verify each gap's line is in its
  list and complete, editing only for completeness or placement, never rewording a section's
  fact: "Results that change" B1 (six unlabelled ticks → three labelled; `10 20 to 40` lost
  30; `1/5` named), B2 (`ylabel(0(20)100)` ended at 41; `yscale(range(100))` inverted;
  `range(20 30)` hid data), B3 (`title("T", c(red))` drew `T`, `,`, `c(red)` as three lines in
  the scheme colour; `ytitle("Volume", axis(2))` titled the left axis), B5 (`order(1 "Group 2"
  3 "Three")` ignored its text; `order(2 1) label(1 "Data")` relabelled the fit), B6
  (`xtitle("")` drew the variable name), B7 (`ytitle2("P2")` drew the quotes), C2 (nlsw88
  ttl_exp `bin(27)` counted 2245 of 2246, census pop `bin(75)` 49 of 50), D1 (a copied scheme
  with quoted RGB drew every series #606060), E1 (`fmt(%10.0g)` of 6165.2567 showed `6e+03`;
  `%9,2f`, `%12.0fc`, `%td` unapplied; the variable's own %g dropped), E3 (a %td dropdown
  listed `2001-12-31 00:00:00`; a %tm card `Oct 2000` for `2000m10`; a %tm axis `Jan 2000`
  for `2000m1`; %tC tooltips lost the time), E14 (the saved `layout(bs)` filter bar moves
  below the header), G6 (a float 0.1 shown as `0.10000000149011612`; a tooltip `1.235e+4` for
  12345.67; `%9.0g` of 1234567.5 as `1.23457e+06` for `1234568`), G16 (numbers where
  `valuelabel` and `hover()` show value labels), X1 (`'01'` listed as `'1'`; `'nan'`, `'None'`,
  `'NaT'` categories dropped; 5e-05 unselectable on the saved page), X2 (`colordiscrete
  colorcuts(2 4)` coloured 1, 3 and 5 as intervals where twoway draws them gray; an empty
  `≤0` level kept). "Changed behaviour": G1 (a variable named `__dash…` is r(110); `__dash_row__`
  was overwritten in silence, y 100..140 drawn as 0..4), G2 (a string plot variable is r(109),
  as twoway; it was drawn as nonsense or ended in a traceback). "Requirements": K2 (Python
  3.13+, bokeh 3.8+, pandas 2.3+, numpy 2.3+, from 3.8/3.0/2.0/1.23; the generated app imports
  annotations from `__future__`), and the top-level `### Requirements` (330-334) must already
  state the new floor (section 09's edit; fail if not). "Fixed": E2 (after price → [4000,5000],
  foreign=1, price → full range, g1=3, g2=5, k1=3 where the widgets imply 5, 5, 5), F1
  (non-zero rc and "no server started on port N: the port is in use"; `--port` outside
  1024-65535 refused; URL printed once /health answers), G3 (a computed-only graph counts its
  drawn output; the size note reports embedded bytes; a 5,000,001-observation histogram
  builds), G5 (Unicode names in `filter()`, `dash kpi`, `by()`, `hover()`, `colorvar()`), E14
  served (viewport tag, 0.15 dimming, rspike/rconnected selection, 992 px reflow with KPI
  minimum heights). Every line ends `(WP-28)`; a "Results that change" line names the
  command, the old value and the new.
- **TR-19.3 GAPS2.md Tracked lines (19-03).** For each of the 22 ids, replace the entry's
  `- **Tracked:** <old>` with `- **Tracked:** Closed in WP-28, BUGS.md "<title>", commit
  <hash>[; residual deferred (WP-28): <reason>]; was: <old>` — the old text kept after
  `was:`, never dropped. Residual reasons: G1, G3, X2, E14 as in Evidence above. C4:
  `- **Tracked:** Deferred (WP-28): out of scope by decision (DISCOVERY Q3), with its duplicate
  E4; nothing is ported to _FILTER_JS on its account; was: <old>`. E4's pointer line
  (`**E4. …** -- same gap as C4; see there.`) is not edited. No other GAPS2 text changes.
- **TR-19.4 WP-28 DONE (19-04).** Append ` — DONE` (em dash, as WP-27's heading) to the
  `## WP-28 · …` heading and add `### Done, measured (<ddmonyyyy>)` after its test plan and
  traceability table, in WP-27's shape (4180-4239): one bullet per BR/AC group stating what was
  measured, with the numbers to be filled by 19-08 written as `<to be measured in 19-08>` in
  that commit only. The block also lists the fixtures the package added (from
  `git diff --stat 91d97be..HEAD -- test/fixtures`), the tests flipped (from the commit
  bodies' `Flipped:` lines), the residuals deferred, and the merge command as text.
- **TR-19.5 Date the release (19-05).** Set the six version lines to `2.0  <ddmonyyyy>` and
  `dash.pkg:25` to `Distribution-Date: <yyyymmdd>` for the same day; the version number
  stays 2.0 (WP-27's precedent: adoupdate compares the date). Run
  `python3 -m pytest test/test_pkg_metadata.py test/test_help_claims_1.py test/test_packaging.py -q`,
  then `make test` and `make test-dev`, each in the background with output to
  `<scratch>/make-test.log` / `<scratch>/make-test-dev.log`, one at a time, read from the
  log on exit; both must end with 0 failed and 0 skipped and no strict-mode line. Commit.
- **TR-19.6 Certification (19-06).** `STATA=/usr/local/bin/stata-mp sh scripts/stata_python_exec.sh`
  must print `/opt/anaconda3/bin/python3` (this is `display c(python_exec)` through the
  console binary); if it prints nothing, write `<scratch>/pyexec_fix.do` holding
  `set python_exec /opt/anaconda3/bin/python3, permanently`, run it as
  `cd <scratch> && STATATMP=<scratch>/tmp/ arch -arm64 /usr/local/bin/stata-mp -b do pyexec_fix.do`,
  and check again. Then `make cert` in the background to `<scratch>/make-cert.log`; read it on
  exit; the verdict must say every registered script passed and none skipped. If any script
  SKIPped, check `python_exec` again before reading the skip as real; a skip is not a pass.
- **TR-19.7 Gate (19-07).** `make gate` in the background to `<scratch>/make-gate.log`; the
  verdict must list no problem: install rc 0, every example rc 0 with no diagnostic, every
  scheme page rc 0, adoupdate as expected, Distribution-Date current, PLUS restored.
- **TR-19.8 Record and report (19-08).** Fill the measured numbers into the `### Done,
  measured` block (passed/skipped per interpreter and the interpreter versions, cert `n of n`,
  gate examples and scheme pages, the log paths); set `CHANGELOG.md:3` to
  `## 2.0, <ddmonyyyy> (release candidate)` and line 5's "now <yyyymmdd>" to the new date;
  run the final checks of AC-19.1..19.8; commit; report the merge command
  `git checkout main && git merge s3-bugs` in the task's report and in the block. Do not run it.
- **TR-19.9 Security (rule 1).** Nothing new reaches a page. The scratch files hold no
  secrets; every Stata invocation is the console binary in batch from a scratch directory
  with its own `STATATMP=<dir>/tmp/` (trailing slash, not the log's directory); no
  `shell=True`; no GUI Stata.

## Boundaries

- Do not fix a gap here. A red test, a failed cert script, a gate problem or a missing
  BUGS.md entry is a defect of the section that owns the gap: fix it in that section's
  files, under that section's rules (a failing regression test first), in a commit with
  that gap's id, and then return to the closeout step that found it. Never weaken or delete
  a test to make a run green; never mark a skip as a pass.
- Do not reword a section's CHANGELOG fact, BUGS.md entry or help text; only placement,
  completeness and the release date are this section's.
- Do not rewrite GAPS2.md's audit text (DISCOVERY Q23): only the 23 Tracked lines change
  (22 in scope plus C4), each keeping its old text after `was:`.
- Do not touch GAPS.md, the `## Traceability matrix`, WP-01..27, or any test's assertion.
- Do not run `git checkout main`, `git merge`, `git push`, or `make hooks`; do not commit to
  `main` (CLAUDE.md rule 5).
- Do not add C4/E4 to `**GAPS2 closed:**`; do not "close" a residual.
- Do not start a second full run while one executes, and do not relaunch to check on one
  (CLAUDE.md rule 11): read its log.

## Stata truth

None added. This section runs Stata only through `make cert` and `make gate`, both of which
invoke `arch -arm64 /usr/local/bin/stata-mp -b do …` from a `mktemp -d` directory with
`STATATMP="$dir/tmp/"`, one session at a time; plus the one-line `python_exec` check
(`scripts/stata_python_exec.sh`) and, if needed, the one-line restore do-file of TR-19.6.
No fixture is written; nothing needs `git add -f`.

## TDD test stubs

This section adds no test. Its failing-first step is documentary: after 19-04 writes
`— DONE` and before 19-03 has run, `test/test_tracking_documents.py::TestGaps2AndRoadmapAgree::test_every_gaps2_id_a_done_package_lists_is_closed_by_it`
fails naming every id whose Tracked line is not the Closed form; 19-03 turns it green. (The
tasks below order 19-03 before 19-04 so the tree is never committed red; the executor runs
the check once in between, on the uncommitted DONE edit, and records its output in 19-04's
commit body as the proof the guard bites.)

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
| 22 fix commits, 22 closed entries, titles quotable | `git log 91d97be..HEAD`, `grep -c 'Resolution (WP-28, ' BUGS.md`, grep for `"` in those titles (19-01) | git, BUGS.md | n/a |
| No CHANGELOG marker left; each gap in its list; before/after present | `grep -c '<!-- WP-28 ' CHANGELOG.md` = 0; per-gap grep of `(WP-28)` lines under the four labels (19-02) | CHANGELOG.md | n/a |
| Every Tracked line in scope is the Closed form; C4 deferred | pytest, `test_tracking_documents.py::TestGaps2AndRoadmapAgree` (all), after 19-04 | GAPS2.md, ROADMAP.md, BUGS.md, git | n/a |
| No open S1/S2; every closed entry names an existing test | pytest, `test_tracking_documents.py::TestNoOpenEntryBlocksARelease`, `::TestEveryClosedEntryNamesATestThatExists` | BUGS.md, test/ | n/a |
| Version lines and Distribution-Date agree and are current | pytest, `test_pkg_metadata.py`, `test_help_claims_1.py::TestTheHeader`; the gate's date rule | six files | n/a |
| Full suite, strict, no skip | `make test` (Stata's Python), `make test-dev` (development interpreter), one at a time | whole suite | yes: the parity corpus and every both-mode test run inside |
| Certification suite, no skip | `make cert`, after the `python_exec` check | 65 cscripts | yes: the scripts build saved and served pages |
| Release gate from an installed package | `make gate` | examples/, schemes/ | yes: examples include server mode |
| Working tree clean of WP-28's work | `git status --porcelain` filtered of the maintainer's planning paths (19-08) | git | n/a |

Acceptance criteria:

- **AC-19.1** `grep -c '<!-- WP-28 ' CHANGELOG.md` prints 0; each of the 22 ids appears in a
  `(WP-28)` line under `### Fixed in WP-28`, B1 B2 B3 B5 B6 B7 C2 D1 E1 E3 E14 G6 G16 X1 X2
  under "Results that change", G1 G2 under "Changed behaviour", K2 under "Requirements", E2
  E14 F1 G3 G5 under "Fixed"; `### Requirements` (top level) states Python 3.13, bokeh 3.8,
  pandas 2.3, numpy 2.3.
- **AC-19.2** `grep -c '^- \*\*Tracked:\*\* Closed in WP-28, BUGS\.md "' GAPS2.md` prints 22
  and `grep -c '^- \*\*Tracked:\*\* Deferred (WP-28):' GAPS2.md` prints 1; every such line
  ends with `was: …`.
- **AC-19.3** `grep -c '^## WP-28 .* — DONE$' ROADMAP.md` prints 1, and
  `python3 -m pytest test/test_tracking_documents.py -q` passes, no skip.
- **AC-19.4** `make test` and `make test-dev` logs each end with `0 failed`, no `skipped`,
  no `strict mode` line; the interpreter and versions are printed at the top of each log.
- **AC-19.5** `make cert`'s verdict: every registered script passed, 0 skipped, and
  `scripts/stata_python_exec.sh` printed `/opt/anaconda3/bin/python3` before the run.
- **AC-19.6** `make gate` exits 0 with no problem line; its log path is recorded.
- **AC-19.7** `grep -c '^- \[ \] Title:' BUGS.md` prints the count of open entries, all
  graded S3 (`TestNoOpenEntryBlocksARelease` green); `grep -c '^  - Resolution (WP-28, ' BUGS.md`
  prints 22.
- **AC-19.8** `git status --porcelain | grep -v -E '^(.. )?(\.ultraplan|phases/|REMAINING\.md|CLAUDE\.md|scripts/__pycache__)'`
  prints nothing; the final report states `git checkout main && git merge s3-bugs` and that
  it was not run.

## Tasks

<task type="auto" id="19-01">
  <name>Inventory the merged branch and the guards</name>
  <files>none</files>
  <action><![CDATA[
    In `/Users/billy/Desktop/Programs/StataPrograms/d/dash`, confirm `git worktree list` shows
    only the main checkout and `git status --porcelain` shows only the maintainer's planning
    paths (AC-19.8's filter). Run `python3 -m pytest test/test_tracking_documents.py test/test_packaging.py -q`.
    Build `<scratch>/wp28-map.tsv` (TR-19.1): for each of the 22 ids, the hash from
    `git log --format='%h %s' 91d97be..HEAD | grep -F "(GAPS2 <ID>)"` and the title of the
    BUGS.md entry whose Resolution line starts `  - Resolution (WP-28, <ID>):`. Fail the task,
    naming the section, if an id has no commit or more than one, no entry or more than one,
    a title holding `"`, or if `grep -c '<!-- WP-28 ' CHANGELOG.md` is not 0 (a section's
    CHANGELOG line is missing). Check `grep -n 'Requires:' dash.pkg` and `sed -n '330,336p'
    CHANGELOG.md` state the K2 floor. Run the python_exec check of TR-19.6 and record its
    output. No commit.
  ]]></action>
  <verify><![CDATA[`wc -l <scratch>/wp28-map.tsv` prints 22; `awk -F'\t' '{print $1}' <scratch>/wp28-map.tsv | sort | tr '\n' ' '` prints the 22 ids; the two targeted pytest files pass; the CHANGELOG marker count is 0; `scripts/stata_python_exec.sh` printed `/opt/anaconda3/bin/python3`.]]></verify>
  <done>Every gap has exactly one fix commit and one closed BUGS.md entry with a quotable title, the CHANGELOG has no marker left, the K2 floor is stated, the tracking guards are green on the merged tree, and Stata's Python is set.</done>
</task>

<task type="auto" id="19-02">
  <name>Reconcile the CHANGELOG for WP-28</name>
  <files>CHANGELOG.md</files>
  <action>
    Under `### Fixed in WP-28` in `/Users/billy/Desktop/Programs/StataPrograms/d/dash/CHANGELOG.md`,
    check each gap's line against TR-19.2: it is under the right label ("Results that
    change", "Changed behaviour (may need your do-files changed)", "Requirements", "Fixed");
    a "Results that change" line names the command, the value dash drew and the value it now
    draws (twoway's); every line ends `(WP-28)`; the lists keep the order of TR-01.7's
    markers. Move or complete a line, never reword its fact; where a value is missing, take it
    from the gap's BUGS.md entry or its commit body. Leave `## 2.0, 24sep2026` and line 5's
    date for 19-08. Run `python3 -m pytest test/test_tracking_documents.py -q` (the retired-link
    scan reads every .md) and commit with the subject `List what WP-28 changed, once, in the
    CHANGELOG (WP-28 S19)`; the body says no test reads CHANGELOG.md beyond that scan and that
    the full runs follow in 19-05.
  </action>
  <verify><![CDATA[For each id in B1 B2 B3 B5 B6 B7 C2 D1 E1 E3 E14 G6 G16 X1 X2, `awk '/^### Fixed in WP-28/,/^### Fixed after WP-27/' CHANGELOG.md | awk '/^Results that change:/,/^Changed behaviour/' | grep -c "(WP-28)"` is at least 15 and the id's command appears in that block; G1 and G2 appear under "Changed behaviour", K2 under "Requirements", E2 E14 F1 G3 G5 under "Fixed"; `grep -c '<!-- WP-28 ' CHANGELOG.md` prints 0; `git log -1 --format=%B | grep -ci 'claude\|anthropic'` prints 0.]]></verify>
  <done>The CHANGELOG's WP-28 section records each of the 22 gaps once, in its list, with before and after values for every changed number, text, colour or layout, and is committed.</done>
</task>

<task type="auto" id="19-03">
  <name>Record the closures in GAPS2.md</name>
  <files>GAPS2.md</files>
  <action><![CDATA[
    Using `<scratch>/wp28-map.tsv`, rewrite the `- **Tracked:**` line of each of the 22
    entries in `/Users/billy/Desktop/Programs/StataPrograms/d/dash/GAPS2.md` to TR-19.3's
    form, `Closed in WP-28, BUGS.md "<title>", commit <hash>`, appending `; residual deferred
    (WP-28): <reason>` for G1, G3, X2 and E14 with the reasons in Evidence, and `; was: <old
    text>` for all 22. Rewrite C4's line to `Deferred (WP-28): out of scope by decision
    (DISCOVERY Q3), with its duplicate E4; nothing is ported to _FILTER_JS on its account;
    was: <old text>`. Locate each line with `grep -n '^### <ID>\.' GAPS2.md` and the first
    `- **Tracked:**` after it; change nothing else. Run
    `python3 -m pytest test/test_tracking_documents.py -q` (WP-28 is not DONE yet, so the
    closure tests are still vacuous on the documents; the reader test must parse every new
    line: add a temporary assertion-free check by running `python3 -c "import sys; sys.path.insert(0,'test'); import test_tracking_documents as t; g,_=t._parse_gaps2(open('GAPS2.md').read()); print(sum(1 for v in g.values() if v['closed']), sum(1 for v in g.values() if v['deferred']))"` and expect `22 1`). Commit with the subject
    `Name the package, entry and commit that closed each GAPS2 gap in scope (WP-28 S19)`.
  ]]></action>
  <verify>`grep -c '^- \*\*Tracked:\*\* Closed in WP-28, BUGS\.md "' GAPS2.md` prints 22; `grep -c '^- \*\*Tracked:\*\* Deferred (WP-28):' GAPS2.md` prints 1; `grep -c '; was: ' GAPS2.md` prints 23; `git diff --stat HEAD~1 -- GAPS2.md` shows 23 insertions and 23 deletions; the Python one-liner prints `22 1`.</verify>
  <done>Each GAPS2 entry in scope names WP-28, its BUGS.md title and its commit, the four residuals and C4/E4 are marked deferred with their reasons, the old audit text is kept after `was:`, and the change is committed.</done>
</task>

<task type="auto" id="19-04">
  <name>Mark WP-28 done in ROADMAP.md</name>
  <files>ROADMAP.md</files>
  <action><![CDATA[
    In `/Users/billy/Desktop/Programs/StataPrograms/d/dash/ROADMAP.md`, append ` — DONE` to
    the `## WP-28 · …` heading and add the `### Done, measured (<ddmonyyyy>)` block of
    TR-19.4 after the `#### GAPS2 traceability` table and before the section's closing `---`,
    with `<to be measured in 19-08>` where the run numbers go. Before editing, prove the
    guard bites: temporarily revert one Tracked line in GAPS2.md to `new.` (do not commit),
    run `python3 -m pytest test/test_tracking_documents.py -q -k Gaps2`, record the failure
    naming that id in `<scratch>/19-04-guard.txt`, restore the line (`git checkout -- GAPS2.md`).
    Then run `python3 -m pytest test/test_tracking_documents.py -q` (all green, none
    skipped) and commit with the subject `Mark WP-28 done: the 22 GAPS2 gaps are closed,
    test first (WP-28 S19)`, the body opening with the guard's recorded failure. Keep every
    line of the block free of `# `/`## ` at line start and of the text `Gaps closed`.
  ]]></action>
  <verify><![CDATA[`grep -c '^## WP-28 .* — DONE$' ROADMAP.md` prints 1; `grep -c '## Traceability matrix' ROADMAP.md` prints 1; `python3 -m pytest test/test_tracking_documents.py -q 2>&1 | tail -1` passes with no skip; `<scratch>/19-04-guard.txt` names the id whose line was reverted; `git status --porcelain -- GAPS2.md` is empty.]]></verify>
  <done>WP-28 is headed DONE with a measured block awaiting the run numbers, the closure guard was seen to fail on a stale Tracked line and passes on the real ones, and the change is committed.</done>
</task>

<task type="auto" id="19-05">
  <name>Date the release and run both pytest suites</name>
  <files>dash.pkg, dash.ado, dash_setup.ado, dash_parse.mata, dash.sthlp, dash_setup.sthlp</files>
  <action><![CDATA[
    Six one-line edits one test holds equal (`test/test_pkg_metadata.py:49-60`), so they are
    one task and one commit although they touch six files: set `*! Version: 2.0  <ddmonyyyy>`
    in `dash.ado:29`, `dash_setup.ado:16` and `dash_parse.mata`'s `*! Version:` line,
    `{* *! version 2.0  <ddmonyyyy>}` in `dash.sthlp:2` and `dash_setup.sthlp:2`, and in
    `dash.pkg` `d Version: 2.0  <ddmonyyyy>` (24) and `d Distribution-Date: <yyyymmdd>` (25),
    all for today. Run `python3 -m pytest test/test_pkg_metadata.py test/test_help_claims_1.py test/test_packaging.py -q`.
    Then `git merge --no-edit main` (expect "Already up to date"), and run `make test` in the
    background with output to `<scratch>/make-test.log`; when it has exited, read the log's
    tail; then `make test-dev` to `<scratch>/make-test-dev.log` the same way. Never start the
    second while the first runs; never relaunch to check. If either is red, stop: the failing
    test belongs to a section, fix it there under that section's rules and commit with that
    gap's id, then rerun only that file (`python3 -m pytest test/<file> -q`) and, once green,
    rerun the make target that failed (prefix `FULL_SUITE_RERUN=1` if the hook asks). Commit
    the six files with the subject `Date the 2.0 release candidate for WP-28 (WP-28 S19)`,
    the body quoting both logs' final lines and interpreter versions.
  ]]></action>
  <verify><![CDATA[`tail -3 <scratch>/make-test.log` and `tail -3 <scratch>/make-test-dev.log` each show a pass count, `0 failed` or no `failed`, no `skipped`, no `strict mode`; the targeted three files pass; `grep -n 'Distribution-Date' dash.pkg` shows today's date; `git log -1 --format=%B | grep -ci 'claude\|anthropic'` prints 0.]]></verify>
  <done>The package is dated today in all seven lines, and the full pytest suite passed strict with no skip under Stata's Python and under the development interpreter on the dated tree, which is committed.</done>
</task>

<task type="auto" id="19-06">
  <name>Run the certification suite</name>
  <files>none</files>
  <action><![CDATA[
    Run `STATA=/usr/local/bin/stata-mp sh scripts/stata_python_exec.sh` and require
    `/opt/anaconda3/bin/python3`; if empty, restore it as TR-19.6 says and check again. Then
    run `make cert` in the background with output to `<scratch>/make-cert.log` and wait for
    it to exit (it runs 65 scripts through the console binary from a scratch directory with
    its own STATATMP; do not run any other Stata meanwhile). Read the log: the verdict must
    list every registered script as passed and the summary as `(n passed, 0 skipped)`. If any
    script SKIPped, run the python_exec check again before believing it; if `python_exec` was
    lost, restore it and rerun `make cert` (prefix `FULL_SUITE_RERUN=1` if the hook asks). A
    FAIL belongs to a section: fix it there, commit with the gap's id, rerun that one script
    as `cd <scratch> && STATATMP=<scratch>/tmp/ arch -arm64 /usr/local/bin/stata-mp -b do <repo>/test/<script>.cscript`
    and read its log, then rerun `make cert`. Save the certification log path the runner
    prints. No commit.
  ]]></action>
  <verify><![CDATA[`grep -E 'passed|skipped|FAIL' <scratch>/make-cert.log | tail -5` shows every script passed and 0 skipped, and the line `certification log: /…/run_all_cscripts.log` names a file that exists; `grep -c '\[ SKIP\]' <that log>` prints 0.]]></verify>
  <done>The certification suite passed with every registered script and no skip, on a Stata whose python_exec was verified before and, if any skip appeared, after the run.</done>
</task>

<task type="auto" id="19-07">
  <name>Run the release gate from an installed package</name>
  <files>none</files>
  <action><![CDATA[
    Run `make gate` in the background with output to `<scratch>/make-gate.log` and wait for
    it to exit: it copies what `dash.pkg` ships to a scratch source, net installs into a
    scratch PLUS, runs every `examples/*.do` and one page per shipped scheme from the install,
    checks adoupdate, and judges the log with `scripts/release_verdict.py`. Read the log: exit
    0 and no problem line. A `Distribution-Date … older than the newest change` problem means
    19-05 was not committed before a shipped file changed again: re-date and recommit. An
    example that prints a diagnostic, a scheme page that falls back, or an install that fails
    belongs to the section whose change caused it: fix there, commit with the gap's id, and
    rerun `make gate`. Save the gate log path the runner prints. No commit.
  ]]></action>
  <verify><![CDATA[`tail -5 <scratch>/make-gate.log` shows no problem line and `release gate log: /…/*.log` naming a file that exists; the shell exit status of `make gate` was 0 (`echo $?` captured into the log by running `make gate; echo "exit=$?"`).]]></verify>
  <done>The release gate passed from a net-installed copy of exactly what dash.pkg ships: every example and every scheme page at rc 0 with no diagnostic, adoupdate as expected, the Distribution-Date current.</done>
</task>

<task type="auto" id="19-08">
  <name>Record the measurements and report the merge command</name>
  <files>ROADMAP.md, CHANGELOG.md</files>
  <action><![CDATA[
    Replace every `<to be measured in 19-08>` in WP-28's `### Done, measured` block with the
    numbers from the four logs: passed and skipped counts and the interpreter versions for
    `make test` and `make test-dev`, `n of n` cert scripts, the gate's example and scheme-page
    counts, and each log's path; state that no S1/S2 entry is open and 22 closed WP-28
    entries name their tests (`TestEveryClosedEntryNamesATestThatExists`), that the tree is
    clean of WP-28's work, and end with the merge command as text: `git checkout main && git
    merge s3-bugs` — reported, not run. Set `CHANGELOG.md:3` to `## 2.0, <ddmonyyyy> (release
    candidate)` and line 5's `now <yyyymmdd>` to the Distribution-Date of 19-05. Run the
    final checks of AC-19.1..AC-19.8 (targeted: `python3 -m pytest test/test_tracking_documents.py test/test_pkg_metadata.py test/test_packaging.py -q`;
    the full runs of 19-05..19-07 measured a tree that differs from this one only by these two
    documents, and no shipped file changed since). Commit with the subject `Record WP-28's
    release measurements (WP-28 S19)`. Then report, in this order: the four log verdicts with
    paths, the open-entry count and grades, the 22 closed entries, the residuals deferred, and
    the merge command with the words "not run".
  ]]></action>
  <verify><![CDATA[`grep -c 'to be measured' ROADMAP.md` prints 0; `awk '/^## WP-28 /,/^## Traceability matrix/' ROADMAP.md | grep -c 'git checkout main && git merge s3-bugs'` prints 1; `sed -n '3p' CHANGELOG.md` shows the new date; the targeted pytest run passes with no skip; AC-19.8's filtered `git status --porcelain` prints nothing; `git log -1 --format=%B | grep -ci 'claude\|anthropic'` prints 0.]]></verify>
  <done>WP-28's measured block quotes the four green runs by number and log path, the CHANGELOG is dated, the working tree is clean of WP-28's work, every commit is on `s3-bugs`, and the merge command has been reported and not run.</done>
</task>

## Section completion criteria

- Five commits on `s3-bugs` (19-02, 19-03, 19-04, 19-05, 19-08), none mentioning an AI, none
  on `main`; `git checkout main && git merge s3-bugs` reported, not run.
- `make test`, `make test-dev`, `make cert` and `make gate` each ran once on the final tree
  (or once more after a section's fix), all green, no skip, logs named in ROADMAP.md.
- `TestGaps2AndRoadmapAgree`, `TestNoOpenEntryBlocksARelease` and
  `TestEveryClosedEntryNamesATestThatExists` green with WP-28 DONE; 22 Closed Tracked lines
  and one Deferred; 22 `Resolution (WP-28, …)` entries; no `<!-- WP-28 ` marker.
- The seven date lines agree and equal the Distribution-Date; the gate's date rule passed.

## Notes

- **Order matters for the date rule.** Commit 19-05 before `make gate`; any later commit that
  touches a shipped file (a section's fix found by 19-06 or 19-07) makes the newest
  shipped-file change later than the Distribution-Date, so re-date in that same day or bump
  the date again before rerunning the gate.
- **`make` is not counted by the launch hook, the conftest lock still is.** Two pytest
  targets in a row are fine sequentially; a second whole-suite pytest started while one runs
  fails at once with `a full test-suite run is already in progress`. Start each target in the
  background, wait for its exit, read its log; never poll by relaunching.
- **A run of cert SKIPs in 0-1 s each is the `python_exec` drop**, not a pass. Check
  `scripts/stata_python_exec.sh` before the suite and after any skip; restore with
  `set python_exec /opt/anaconda3/bin/python3, permanently` from a batch do-file, never the
  GUI (`.claude/hooks/block-stata-gui.sh` blocks it anyway).
- **Where a red test belongs.** The closeout owns no fix. Find the section from the test file
  or the cscript case, fix it under that section's rules in that section's files, and commit
  with that gap's id so 19-03's map stays true; if the fix changes a BUGS.md entry's title,
  update the GAPS2 Tracked line in the same commit (the guard fails otherwise).
- **The gate allows no diagnostic**: a section that made an example print a note it did not
  declare must either stop the note (an honoured option prints nothing, DISCOVERY Q22) or, if
  the note is intended, declare it in the example's header `*! release-gate allows: <text>`.
- **The open entries stay four, all S3** (BUGS.md 2523, 2559, 2595, 2601) unless a section
  closed one on the way; `TestNoOpenEntryBlocksARelease` is the judge, not a count.
- **The maintainer's planning files** (`.ultraplan*`, `phases/`, `REMAINING.md`, `CLAUDE.md`,
  `scripts/__pycache__/`) were left uncommitted at WP-27 by choice; "clean" means clean of
  WP-28's work, as AC-19.8's filter says. Do not commit them.
- **Timing.** Each pytest target is about two minutes on this machine (WP-25); the cert suite
  and the gate take longer and must run to completion; use the Bash tool's background mode
  with output redirected, not a foreground call that would time out at ten minutes.
