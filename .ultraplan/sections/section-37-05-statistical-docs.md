# Section 37-05: lpolyci zero df, numeric limits and ties documented

> Part of: WP-37 (Statistical and computed layers) · Items: stat:PT-16, DT-26, stat:PT-21 · Risk: green · Batch: 37.1 · Depends on: none · Blocks: none · Tasks: 3, 3 commits · Case-id prefix: Q3705

## Overview

**What is wrong today.** Three statistical differences are documented loosely or not under Differences. stat:PT-16 (audit :655-657; appendix :1149-1154): at lpolyci grid points whose pilot window has no residual degrees of freedom, twoway draws a finite band that can be very wide -- `lpolyci mpg weight, degree(3)` at x = 4714.3 is -50.75 to 74.75 (lpolyci_truth.json case a_d3 row 47), and `[fw=rep78], degree(2)` -31.62 to 55.62 -- which rescales the y axis, and draws no band at some neighbouring points (rows 44-46 and 49) and a zero-width one at row 48, where dash pinches the band to zero width; the help (dash.sthlp:4032-4034) says Stata's value there "is round-off, often missing", which understates it. DT-26 (audit :658-660; appendix :2483-2488): the help documents numeric limits -- lpoly's bandwidth about 1% off at degree 6-7 (386.3 against 390.0), above degree 7 a note (degree 8: 484.23 in Stata against 400.94 in dash), three exact-polynomial cases, fpfit's model choice on a date-time x, dots thinned above 2,000,000 -- but none is listed under Differences. stat:PT-21 with BY-30 and DG-16 (audit :661-663; appendix :1173-1178, :3035-3040, :3344-3349): tied sort keys keep the data's order in dash, where twoway's order among ties changes from run to run (a lowess path through tied x, `sort` under by(), where cmissing(n) breaks a line); the help says so in one clause (:436-437) but not under Differences.

**What will be true after.** Rulings M9 (Q27: correct the help on lpolyci) and Q40: each item's help sentence states the difference with its measured numbers, and a one-line Differences entry links to it. No code changes. Each is pinned by a help-claim test; the measurable ones by a certification case showing dash does what the sentence says.

**Test order and commit rule.** Three items, three commits, in the manifest's order: stat:PT-16, DT-26, stat:PT-21. Task 37-05-01 writes the first item's failing class and saves the failure text, no commit; each later cycle appends its own class to test/test_help_statistical_limits.py, runs it red, edits the help, runs it green and commits with the subject ending `(WP-37 <id>)`.

### Section decisions

- **D-37-05.a No arithmetic is copied.** Stata's compiled round-off (the lpolyci pilot fit, the lpoly pilot at high degree) is out of reach (PRD §7, Q27); the help says what twoway draws and what dash draws.
- **D-37-05.b One Differences entry per item**, appended after the last Differences item at the base: `{ul:lpolyci where the pilot has no residual degrees of freedom.}`, `{ul:Numeric limits of the estimators.}`, `{ul:Points whose sort keys tie.}`, each one line linking to its topic paragraph (`{help dash##smoother_options:...}` for the first two; the ties sentence lives in the plot-types section, link `{help dash##plottypes:...}`; check the markers at the base).
- **D-37-05.c Ties are deterministic in dash and not in twoway.** The help says twoway's order among ties is not fixed (measured: `line mpg weight, sort [by(foreign)] nodraw` run four times in one session gives different orders, BY-30's verifier), so no fixed order can be matched; dash keeps the data's order.

## Risk: [green] -- help text only

**Why.** No code changes; risks are wrong numbers and pins on the old sentences.

**Risk factors.** 1. The numbers must come from committed fixtures, not memory. 2. Pins on the lpolyci sentence (grep "round-off" in test/*.py).

**Mitigation.** 1. Task 01 reads lpolyci_truth.json (case a_d3, rows 44-49), the lpoly bandwidth fixture and the fpfit/ndots fixtures named in the help, and writes the values into `<scratch>/37-05-values.txt`; the sentences use those values. 2. Any pin on the old words is flipped in stat:PT-16's commit.

## Dependencies

- **Depends on:** none. **Blocks:** none.
- **Parallel batch:** 37.1 with 37-01 and 37-04; merge order 37-01, 37-04, 37-05.
- **Can run with:** both: 37-01 edits dash.sthlp :340-355 and :505-524; 37-04 edits :6550-6557 and appends to the `{ul:Fit options.}` paragraph (:3546-3579); this section edits :432-440, :1164-1172, :3793-3796, :3893-3918, :3968-3977, :4026-4040 and appends Differences entries (37-01 and 37-04 add none).

## Evidence

- dash.sthlp:4031-4034: "A grid point whose pilot window has no residual degrees of freedom is drawn with zero width; Stata's value there is round-off, often missing."
- test/fixtures/lpolyci_truth.json case `a_d3` (lpolyci mpg weight, degree(3); `cases` is a list, the entry with `id` "a_d3"; 50 grid points, 0-based): at index 47 (x 4714.29, `gy` 12.0) `cl` -50.75, `cu` 74.75, `gse` 32.0; indices 44-46 and 49 missing; index 48 `cl` = `cu` = 12.0 (a zero-width band) -- checked 20oct2026 (REVIEW R3-24). Divergence D4 is read in test/test_lpolyci_band.py::TestTheBandIsStatas (:168; the D4 rows are skipped there, :234-265) and named in that file's docstring (:16); no class `TestLpolyDocumented` exists (REVIEW R3-36).
- dash.sthlp:1166-1170 (degree() above 7: "drawn with a note that the result can differ from Stata's, fitted at most at degree 30"), :3893-3916 (bandwidth at degree 6-7, 386.3 vs 390.0; exact-polynomial cases), :3968-3975 (fpfit on a date-time x, curves within 5e-4), :3793-3796 (above 2,000,000 dots fewer are drawn). The degree-8 numbers 484.23 / 400.94: `_lpoly_degree_note` (dash_render.py:20951-20966) and the audit's SD-19 (:2774-2779); re-measure in Q3705-2.
- dash.sthlp:436-437: "Points whose keys tie keep the order of the data ({cmd:twoway}'s order among them changes from one run to the next)." Pinned by test/test_join_order.py:329 (data order by design); BUGS.md G6 closed.

## User stories

- US-37-05.1 As a Stata user comparing pictures, I want the help to say where dash's lpolyci, lpoly, fpfit and dots cannot match Stata's numbers and by how much, so that I trust the rest.
- US-37-05.2 As a Stata user, I want to know that tied points are joined in data order in dash and in no fixed order in twoway.

## Business requirements

- BR-37-05.1 (stat:PT-16) The lpolyci paragraph says twoway can draw a very wide band at a grid point with no residual degrees of freedom (with the measured example) and no band at neighbouring points, and that dash draws zero width there; a Differences entry links to it.
- BR-37-05.2 (DT-26) Each documented numeric limit is stated with its measured value, and one Differences entry lists them by name with a link.
- BR-37-05.3 (stat:PT-21) The ties sentence names the three places ties show (a lowess path, `sort` under by(), where cmissing(n) breaks a line) and a Differences entry links to it.

## Technical requirements

- **TR-37-05.1 (stat:PT-16).** Replace dash.sthlp:4031-4034's sentence with: "At a grid point whose pilot window leaves no residual degrees of freedom, {cmd:dash} draws the band with zero width.  {cmd:twoway} draws there what its own round-off gives: sometimes no band, and sometimes a finite band that can be very wide and rescale the y axis ({cmd:lpolyci mpg weight, degree(3)} draws -50.75 to 74.75 at a weight of 4,714, where the smooth is about 12, and no band at the three grid points before it and at the second after it)." Differences entry: `{phang2}N.  {ul:lpolyci where the pilot has no residual degrees of freedom.}  {cmd:dash} draws zero width where {cmd:twoway} may draw a very wide band; see {help dash##smoother_options:Statistical layer options}.` The sentence it links to stands under `{marker smoother_options}` (dash.sthlp:3532 at 090d928), the marker in force at :4031; `{marker ciband}` (:4041) marks the paragraph after it and is not the link.
- **TR-37-05.2 (DT-26).** dash.sthlp:1166-1170 gains, after "can differ from Stata's": "(measured at degree 8 on {cmd:lpoly mpg weight}: a bandwidth of 400.94 where Stata's is 484.23)". Differences entry: `{phang2}N.  {ul:Numeric limits of the estimators.}  {cmd:lpoly}'s default bandwidth at degree 6 and above, three exact-polynomial cases, {cmd:fpfit} on a date-time {it:x}, and {cmd:dot}'s dots above 2,000,000 differ from Stata's by the measured amounts in {help dash##smoother_options:Statistical layer options}.` The other limits are already stated with values at :3893-3916, :3968-3975 and :3793-3796; check each value against its fixture and correct any that differs.
- **TR-37-05.3 (stat:PT-21).** dash.sthlp:436-437 becomes: "Points whose keys tie keep the order of the data.  {cmd:twoway}'s order among them is not fixed -- it changes from one run to the next, so no fixed order can match it -- which shows where tied points are joined: the path of a {cmd:lowess} through a tied {it:x}, a {cmd:sort} under {cmd:by()}, and where {cmd:cmissing(n)} breaks a line at a tie." Differences entry: `{phang2}N.  {ul:Points whose sort keys tie.}  {cmd:dash} joins them in the data's order; {cmd:twoway}'s order among them changes from run to run; see {help dash##plottypes:Plot types}.`
- **TR-37-05.4 Tests.** test/test_help_statistical_limits.py with `TestLpolyciZeroDf` (stat:PT-16: the new sentence's facts, and that they match the fixture -- index 47's band wider than 100, indices 44-46 and 49 without a band, index 48 zero width; "round-off, often missing" gone; the Differences entry), `TestNumericLimits` (DT-26: 400.94 and 484.23; each of the five limits named in the Differences entry; the values at :3893-3916, :3968-3975, :3793-3796 present), `TestTies` (stat:PT-21: the three places; the entry), with `_help` and `_between` copied from test/test_help_claims_1.py (:89, :93) and `_flat` from test/test_version_floor.py (:50).

## Boundaries

- No code change; edit only the help paragraphs listed (R3) and append the three Differences entries.
- Do not reword 37-01's paragraphs (:340-355, :505-524) or 37-04's (:6550-6557, the `{ul:Fit options.}` paragraph :3546-3579 with the sentences 37-04 appends).

## Stata truth

No extract script. Measurable claims get live cases in test/test_wp37_truth.cscript (R1), one block per item, each appended in its commit after the blocks already there (section order: S01, S04, then S05):
- `* ==== S05 stat:PT-16: lpolyci with no residual df ====` -- Q3705-1: from test/fixtures/lpolyci_truth.json case a_d3 (the committed truth; not re-run), twoway's band at index 47 is finite and wider than 100 (-50.75 to 74.75); dash's band at the same grid point, computed by a python helper calling the lpolyci band function the renderer uses (find it with `grep -n 'def .*lpolyci\|def _lpoly_local_wls' dash_render.py`) on auto's mpg and weight at degree(3) over the fixture's grid, has zero width (upper minus lower below 1e-9).
- `* ==== S05 DT-26: numeric limits ====` -- Q3705-2: `lpoly mpg weight, degree(8) nograph` r(bwidth) = 484.23 (to 0.01) and dash's default bandwidth at degree 8 (python helper calling dash_render's bandwidth function) = 400.94 (to 0.01).
- `* ==== S05 stat:PT-21: tied sort keys ====` -- Q3705-3: dash's drawn order of `line mpg weight, sort` keeps data order at the tied weights 3370, 3600 and 4060 (the saved page's Line source x/y read by a python helper), the same over two builds.

## TDD test stubs

- Test (stat:PT-16 cycle, red at base): test/test_help_statistical_limits.py::TestLpolyciZeroDf::test_the_sentence, ::test_the_old_words_are_gone, ::test_the_differences_entry; cscript Q3705-1.
- Test (DT-26): ::TestNumericLimits::test_degree_8_values, ::test_the_differences_entry, ::test_the_stated_values (guard); cscript Q3705-2.
- Test (stat:PT-21): ::TestTies::test_the_three_places, ::test_the_differences_entry; cscript Q3705-3.
- Pins: any node quoting "round-off, often missing" (`grep -rn "often missing" test/`), flipped in stat:PT-16's commit.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| lpolyci sentence and entry | pytest TestLpolyciZeroDf; cscript Q3705-1 | lpolyci_truth.json | n/a |
| numeric limits | pytest TestNumericLimits; cscript Q3705-2 | -- | n/a |
| ties | pytest TestTies; cscript Q3705-3 | -- | saved |

- AC-37-05.1 Each class was red before its item's edit and green after; Q3705-1..3 pass.

## Tasks

**Commit boundary.** Three commits, one per item, each staging its class of test/test_help_statistical_limits.py, its help edits and Differences entry, its S05 block, the item's BUGS.md entry closed `Documented <ddmonyyyy> (WP-37, <id>). dash.sthlp:<paragraph>. Pinned by <class>, Q3705-k. Closes GAPS4 <id> (WP-37, <id>).`, its GAPS4 Tracked line `Documented in WP-37, BUGS.md "<title>", commit pending.`, its `GAPS4_OPEN` deletion and a CHANGELOG line under `### Fixed in WP-37`. Subjects: `Describe lpolyci's band where the pilot has no residual degrees of freedom (WP-37 stat:PT-16)`; `List the estimators' numeric limits under Differences (WP-37 DT-26)`; `Document how tied sort keys are joined (WP-37 stat:PT-21)`. TWOWAY_COVERAGE_AUDIT.md: stat:PT-16 appends to the lpolyci row (:95, re-read) `[WP-37 stat:PT-16: documented -- zero width where the pilot has no residual degrees of freedom, where twoway may draw a very wide band]` and DT-26 to the lpoly row (:94) `[WP-37 DT-26: documented -- the measured numeric limits are listed under Differences]`; stat:PT-21's commit body says "no coverage-audit row". Before each commit: `git pull --ff-only . main` (CLAUDE.md rule 4; `Already up to date.` at the batch base -- if it refuses, stop and report to the orchestrator, never a merge commit on a section branch) and `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a `partial` or `truncated` result is run again; the section edits no function, so `impact` is not needed; REVIEW R3-17). `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp37-s05`.

**Closing steps (BRIEF 'The corpus ledger and the known-differences tables'; D-33-05.i; D-33-10.h).** For each lead id <id> (stat:PT-16, DT-26, stat:PT-21), after the tracking edits and before its commit: (1) delete the plain `<id>` rows of `scripts/corpus/ledger.tsv`, keep or add its `<id> (documented)` rows, run `python3 scripts/corpus/ledger.py` and `git add -f` the regenerated ledger fixture; (2) run `python3 test/known_differences.py <id>`, delete the plain rows it prints (a documented difference stays as a `(documented)` row or moves into that table's deliberate dict with the ruling id, `"Q27: <what is kept>"` for stat:PT-16 and `"M9: <what is kept>"` otherwise), and run the hygiene command it prints; (3) if 33-09's Q3309-1 reports any change for a guard example, regenerate `test/fixtures/corpus_guard_truth.json` with its extract script and commit it with the item.

<task type="auto" id="37-05-01">
  <name>Read the values, write the lpolyci test</name>
  <files>test/test_help_statistical_limits.py</files>
  <action><![CDATA[
    In $WT, re-read every help anchor of Evidence and the Differences section's last item number; read lpolyci_truth.json case a_d3 (indices 44-49 of the `cases` entry with `id` "a_d3") and the fixtures behind :3893-3916, :3968-3975 and :3793-3796, and write the values to `<scratch>/37-05-values.txt`. Create test/test_help_statistical_limits.py with the helpers and the class TestLpolyciZeroDf only. Run `python3 -m pytest test/test_help_statistical_limits.py -q -n0 -p no:cacheprovider -rf > <scratch>/37-05-01.log`; save the failing nodes to `<scratch>/37-05-01-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/37-05-01.log` prints 3; `grep -c "a_d3" <scratch>/37-05-values.txt` is at least 1; `test -s <scratch>/37-05-01-failure.txt`.]]></verify>
  <done>The measured values were read from the committed fixtures and the lpolyci help claim was tested and shown failing.</done>
</task>

<task type="auto" id="37-05-02">
  <name>Document lpolyci zero df and numeric limits</name>
  <files>dash.sthlp, test/test_help_statistical_limits.py, test/test_wp37_truth.cscript</files>
  <action><![CDATA[
    stat:PT-16: apply TR-37-05.1, flip any "often missing" pin, append the `S05 stat:PT-16` block (Q3705-1) above the marker after the blocks present, run the class, `python3 -m pytest test/test_help_conformance.py test/test_lpolyci_band.py test/test_lpolyci_options.py -q -n0 -p no:cacheprovider` and the block through the driver (`WP37_ONLY=S05`), close the item, run the closing steps (1)-(3) for stat:PT-16, append its coverage-audit line, pull and detect-changes, and commit. DT-26: append TestNumericLimits, run it red (append to the failure file), apply TR-37-05.2 (correct any stated value that disagrees with `<scratch>/37-05-values.txt`), append the `S05 DT-26` block (Q3705-2), run the class and the block, close, run the closing steps (1)-(3) for DT-26, append its coverage-audit line, pull and detect-changes, and commit. Grep each message for `claude|anthropic` before and after.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_statistical_limits.py test/test_help_conformance.py -q -p no:cacheprovider`'s last line reads `<n> passed in ...` with no `failed` or `error`; `grep -c "Q3705-[12] PASS" <scratch>/run_test_wp37_truth.log` prints 2; `git log --format=%s -2 | grep -c "(WP-37 \(stat:PT-16\|DT-26\))"` prints 2.]]></verify>
  <done>The lpolyci zero-df difference and the estimators' numeric limits were stated with measured values and Differences entries, and both commits landed.</done>
</task>

<task type="auto" id="37-05-03">
  <name>Document tied sort keys, hand back</name>
  <files>dash.sthlp, test/test_help_statistical_limits.py, test/test_wp37_truth.cscript</files>
  <action><![CDATA[
    stat:PT-21: append TestTies, run it red, apply TR-37-05.3, append the `S05 stat:PT-21` block (Q3705-3), run the class, test/test_join_order.py and the block through the driver, close the item, run the closing steps (1)-(3) for stat:PT-21, pull and detect-changes, and commit (grep for `claude|anthropic` before and after). Run test_help_statistical_limits.py, test_help_conformance.py and test_tracking_documents.py once more and write `<scratch>/37-05-handback.txt` with the three shas.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_statistical_limits.py test/test_join_order.py test/test_help_conformance.py test/test_tracking_documents.py -q -p no:cacheprovider`'s last line reads `<n> passed in ...` with no `failed` or `error`; `grep -c "Q3705-3 PASS" <scratch>/run_test_wp37_truth.log` prints 1; `git log --format=%s <base>..HEAD | grep -c "(WP-37 "` prints 3.]]></verify>
  <done>The tie rule was documented with its three visible places, and stat:PT-16, DT-26 and stat:PT-21 were each closed as documented in their own commits on wp37-s05.</done>
</task>

## Section completion criteria

- Three Differences entries and three corrected topic paragraphs; Q3705-1..3 pass; three BUGS entries `Documented`, three Tracked lines, three `GAPS4_OPEN` lines deleted.

## Notes

- **Help paragraphs owned (R3):** dash.sthlp :432-440 (ties), :1164-1172 (degree()), :3793-3796 (ndots), :3893-3918 (bandwidth), :3968-3977 (fpfit), :4026-4040 (lpolyci), and the three new Differences entries.
- **Merge rules touched:** R1 (three S05 blocks, in order after S01 and S04), R3, R9 (if a pin quotes the old lpolyci words).
- **Trap:** blocks of one WP truth script must stay in non-decreasing section order (the WP-truth reader); S05 comes after S04, which 37-04 appends in the same batch: append S05 after S04 when merging (the merger keeps the order); 37-02 and 37-03 later insert S02 and S03 above S04 (BRIEF "Block order").
- **GitNexus and rule 4.** No function is edited, so no `impact` run; `git pull --ff-only . main` and `detect-changes --scope all` before each of the three commits (REVIEW R3-17).
- **Commit-body line forms:** `Regression: test/test_help_statistical_limits.py::TestLpolyciZeroDf::test_the_sentence -- failed at <base> with <text>`; `BUGS.md: "<title>" (documented)`; `GAPS4: <id> Tracked`; `TWOWAY_COVERAGE_AUDIT.md: <row> row documented` or `no coverage-audit row`.
