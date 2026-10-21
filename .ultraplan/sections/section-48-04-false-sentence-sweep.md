# Section 48-04: The audit's false-sentence checklist (HR-1..HR-22)

> Part of: WP-48 (Help, README and tracker accuracy, audit package 16) · Items: none (Appendix B checklist, PD-8) · Risk: green · Batch: 48.3 · Depends on: 48-02, 48-03 · Blocks: none (WE) · Tasks: 6, 2 commits · Case-id prefix: Q4804

## Overview

**What is wrong today.** The audit lists 22 help and README sentences that were false on 19oct2026 (audit :846-871; index Appendix B, HR-1..HR-22). PD-8 gives each to the section whose item makes it true or rewrites it; this section (a) corrects the six Appendix B gives to it -- HR-1, HR-3, HR-4, HR-6, HR-7 and the HR-21 check -- and (b) verifies all of them at the WP-48 base with one help-claim test each, correcting any an owner left false. The README keeps its drop-in claim (M14; "dash takes the place of twoway" stays).

The six this section owns:
- **HR-1.** dash.sthlp:172 ("dash accepts the same syntax as twoway and produces an interactive HTML file") and :181-182 ("For plot types, marker/line/axis options, and if/in qualifiers, dash accepts the same syntax as twoway") -- the audit: "say the twoway grammar, with the exceptions listed under Differences".
- **HR-3.** README.md:6-8 and dash.pkg:7-9 ("Most twoway options are honoured; the rest are accepted and named in a note") -- false: options twoway refuses are refused, some values and forms are refused or handled differently, and some options are noted and not drawn.
- **HR-4.** README.md:59 ("the syntax, every difference from twoway, and the dashboard options") -- "drop it, or make it true".
- **HR-6.** dash.sthlp:6459-6465 ("None of them given once is an error ... so a command copy-pasted from a do-file always runs") -- false: p3()-p19() (before 35-02), repeated label options (before 35-01), play(), dash's value bounds, resource limits, names, __dash variables and other forms are refused or limited.
- **HR-7.** dash.sthlp:281-282 at `090d928` (audit :286-289: "where dash differs, this file says so under the option concerned") -- false while differences were untracked; true once every audit item is closed or documented, which this section pins with a conformance test rather than an assertion of prose.
- **HR-21.** "The Differences section should list the resource limits, recast+horizontal quirks" (the histogram tick rule and continuous colorvar are fixed; jitter and the Python requirement are not added, Q50, Q49) -- 40-02 and 46-02 add the entries; this section checks them.

**After this section**, a test file `test/test_false_sentences.py` holds one test class per HR -- HR-5 and HR-22, the same sentence, share `TestHR05and22`, and HR-17's class is added by 49-01 (D-48-04.c) -- every one passes at the end of WP-48, and README.md, dash.pkg and dash.sthlp make no claim the audit found false.

**Why one section, alone in its batch.** The checklist reads dash.sthlp, README.md and dash.pkg after 48-01..48-03 and every earlier WP have edited them (index Owns: "dash.sthlp, README.md, dash.pkg (alone)").

**Test order and commit rule.** No audit item: two commits per task group (index: sections with no item commit once per task group). Group 1 (HR-1, HR-3, HR-4, HR-6, HR-7, HR-21): 48-04-01 writes the 20 test classes (21 HRs) and runs them on the base, saving the failure text (no commit); 48-04-02 and 48-04-03 correct the six and commit `Correct the help, README and package claims the audit found false (WP-48 48-04)`. Group 2 (owner sentences still false at the base, if any): 48-04-04 corrects them and commits `Correct false sentences left by earlier sections (WP-48 48-04)`; if none is left, no second commit (the hand-back says so).

### Section decisions (binding on the executor)

- **D-48-04.a The new sentences (group 1).**
  - HR-1: :172 -> "dash reads twoway's syntax and produces an interactive HTML file instead of a Stata graph window; where it reads or draws something differently, Differences from twoway says so."; :181-182 -> "Plot types, plot and graph options and if/in qualifiers are written as for twoway (see Differences from twoway for the exceptions)."
  - HR-3 (README.md:6-8 and dash.pkg:7-9, the same sentence in both): "Options are written as for twoway: what twoway refuses is refused in twoway's words, the options dash draws are drawn, and the few it does not draw are named in a note -- see help dash, Differences from twoway and Unsupported Stata twoway options; dash adds two options of its own, hover() and table (see help dash, dash-only options)." The last clause keeps the sentence true for the two dash-only options P4-7 keeps (35-07's `{marker dashonly}` paragraph), which twoway does not have. dash.pkg's line wrapping keeps each line under 80 characters with `d ` prefixes; `-help dash-` replaces `help dash` there (both times).
  - HR-4: README.md:59 -> "`help dash` -- the syntax, the differences from `twoway`, and the dashboard options."
  - HR-6: the Unsupported intro (grep "a command copy-pasted from a do-file always runs") -> "None of them given once is an error, so a command that uses them runs, and each that is supplied and not drawn is named in that command's note; an option or value twoway refuses is refused as twoway refuses it, except dash's own {opt hover()} and {opt table} ({help dash##dashonly:dash-only options}), and the limits under Resource limits apply." (the rest of the paragraph and its example stay). The exception is the two options P4-7 keeps as dash's own; `dashonly` is the marker 35-07 (TR-35-07.5) gives their paragraph -- re-read its name at the WP-48 base.
  - HR-7: the sentence (grep "where {cmd:dash} differs") -> "where dash differs from twoway, this file says so: each difference has a line under Differences from twoway linking to its note." It is pinned by `TestHR07::test_every_documented_difference_is_in_the_help`, which reads only these entries (REVIEW-5 R5-12): (a) every BUGS.md entry whose Resolution starts `Documented ` (PD-4) and ends `Closes GAPS4 <id> (WP-NN, <id>).` with NN >= 33 (so WP-29..32 history entries, which also start `Documented`, are skipped) names a dash.sthlp section that exists, by this rule: every `dash##<name>` in the Resolution names an existing `{marker <name>}` of dash.sthlp; a Resolution with no such link must hold `dash.sthlp ` followed by a section name -- the text after `dash.sthlp ` up to the next `.` or ` and ` -- that equals, compared case-insensitively after collapsing runs of blanks, either the text of a `{ul:...}` entry heading or the text of a `{title:...}` section title of dash.sthlp (so PD-4's prose form `dash.sthlp Differences from twoway and the Recast paragraph` passes on `Differences from twoway`); a mismatch is reported with the entry's title and is group 2's to correct (48-04-04: the BUGS Resolution's section name is text, so the Resolution is corrected, never the help); (b) for every GAPS4 row whose Tracked line is the Partly form and whose WP is in `GAPS4_CLOSED_WPS` (test/test_tracking_documents.py) or is WP-48, the residual entry its Tracked line names has a BUGS Resolution naming a Differences line (its text found in `_between(_help(), "{marker differences}", "{marker subcommands}")`). Rows still in `GAPS4_OPEN` (WP-49's, in PD-4's open form) are skipped. The natscale residual (PD-9, plot:PT-13's entry, open by D41/M6) is named by its title and only its existence is asserted. Residuals documented by a ruling close Documented (A-5), so they are read by (a).
  - HR-21: no new text unless missing: `TestHR21` asserts the Differences section links to `dash##resourcelimits` (or the marker 40-02 used) and to the recast/horizontal note 46-02 wrote, and that no Differences entry heading -- the `{ul:...}` text that opens each entry between `{marker differences}` and `{marker subcommands}` -- names jitter or the Python requirement (Q50, Q49; at `090d928` none of the 17 headings does). It reads headings only: the Differences prose already holds `{cmd:jitter()} 0 to 100` (value bounds) and the word Python, and those stay (REVIEW-5 R5-29).
- **D-48-04.b Owner sentences: the owner's pin, never a second assertion (REVIEW-5 R5-27).** For each HR owned elsewhere, `TestHRnn::test_owner_pin` asserts the owner's pin exists: the owner's closed BUGS entry (found by `Closes GAPS4 <id>` for the owner's item) names a test node whose file, class and method exist (the file parsed with `ast`, as test/test_function_test_map.py:187 reads test files; a cscript case id is found in its script's text). It does not re-assert phrases the owner's pin already asserts (memory rule: one test per distinct behaviour). Only for a sentence the owner left with no help-claim node (its closed entry names none for that sentence) does the test assert, as the only pin, that the audit's false phrase is absent (the list below). A test that fails at the base is group 2's work: correct the sentence to the behaviour the owner's pin measures, citing the owner in the commit body.
- **D-48-04.c HR-17 waits for 49-01.** HR-17 (Differences item 5 and the refusal sentences "as twoway refuses them", "naming the option given") is 49-01's (WP-49, after WP-48). This section does not test it; 49-01 adds `TestHR17` to test/test_false_sentences.py in its plot:PT-7 commit (49-01's section says so). 48-04's file carries a module docstring line naming the 21 HRs it holds and HR-17's owner.

The owners, and the fallback phrase each test asserts absent only when the owner left no pin for that sentence (file; owner):
- HR-2: three parts, each in the owner-pin form (REVIEW-5 R5-28): `name()` registering (38-01), "no graph memory or export" (38-01, the help-only caveat of Appendix B), and the tested platform (36-04, help and README). The platform part's fallback asserts only the tokens `StataNow 19.5` and `macOS arm64` in 36-04's platform sentence of dash.sthlp and README.md -- no other token of that sentence, and never the existing Stata-version lines A-2 keeps (REVIEW-5 R5-26).
- HR-5 and HR-22 (one sentence; `TestHR05and22`, REVIEW-5 R5-27): the owner is 35-09's PD-10 commit `(WP-35 A2)`, which has no GAPS4 row; the test asserts that 35-09's pin `test/test_command_grammar.py::TestGeneric::test_no_by_name_refusal` exists and, only if 35-09's commit left no help-claim node for dash.sthlp:737-745 and :995-997 (anchors at `090d928`), that dash.sthlp no longer names the two words PD-10 removed (the words appear only as test input, A-9).
- HR-8: `with axes and no plot` absent (35-09).
- HR-9: `works offline in any modern browser` absent; `Chrome` present in the Description (36-04).
- HR-10: `a {cmd:range()} that widens the ticks` absent from dash.sthlp (34-03); dash.sthlp:4528-4529's "Stata's own ticks at build" claim (34-09's part; owner-pin form, REVIEW-5 R5-28); `exact at build through S45's embedded ticks` absent from ROADMAP.md, and the natscale BUGS entry (`The natscale model misses three`) does not say every axis is Stata's own at build (34-09, PD-9).
- HR-11: `one fewer on y` absent (34-02).
- HR-12: the xsize(9) and aspectratio() sentences (grep `exactly as {cmd:twoway} does`) per D-48-04.b (34-04, 45-04).
- HR-13: per D-48-04.b (47-02).
- HR-14: owner-pin form only (REVIEW-5 R5-27): 48-01's `test/test_help_claims_p16.py::TestStalePassages` nodes for the headlabel, mangle, lalign, dlalign and every-plot-type passages exist, and 47-01's and 47-03's closed entries name their nodes; no phrase is re-asserted here.
- HR-15: the area-outline sentence (grep `{cmd:area}` beside `outline`) matches 34-05's pin; `open chevron` absent for V/v unless 47-06 drew them so; the economist note sentence matches 45-01 (D-48-04.b).
- HR-16: `judged after {cmd:recast()}` absent (48-02); `twoway takes any integer` absent near levels() (35-04); the placement() sentence per D-48-04.b (43-05); the custom, tick-grid and fill sentences per 44-02/44-03's rewrites (`change nothing, as in`, `minor_grid} style`, `fill} draw the plain axis` absent).
- HR-18: per D-48-04.b (40-01).
- HR-19: `drawn as Stata draws them` near colordiscrete absent unless 42-05's pin backs it; msize "any number" absent (40-02); `one bar per value` qualified with the 1,000-bin cap (40-02); the zero-weight sentence matches 47-06's pin; `gaps between boxes are not scaled` absent (33-11).
- HR-20: `Python is required but is not available to Stata` absent from dash_setup.sthlp, dash.ado and dash_setup.ado (36-01).

## Risk: [green] -- prose, README and package description; one conformance test reading BUGS.md

**Why.** No code; the HR-7 test reads every Documented BUGS entry, so a malformed entry anywhere fails it.

**Risk factors.** (1) test_readme.py and test_dash_pkg*.py (grep) pin README/dash.pkg text and line lengths. (2) Earlier sections may have reworded a sentence so a phrase moved across a line break: assertions use `_prose()`. (3) The HR-7 test could fail on a Documented entry whose section name differs from its marker.

**Mitigation.** (1) Run them after each edit. (2) Every assertion runs on `_prose(...)`. (3) The test reports each mismatch; a mismatch from an earlier WP is corrected in group 2 (the BUGS Resolution's section name, which is text, not a marker).

## Dependencies

- **Depends on: 48-02** (batch 48.2: the Unsupported list and recast paragraphs) and **48-03** (batch 48.1: dash_setup help); and on every earlier WP's Appendix B owner having landed.
- **Blocks:** none; WP-48's WE follows. 49-01 adds HR-17's test to this section's file.
- **Parallel batch 48.3:** alone.

## Evidence

At `090d928` (re-read by phrase): dash.sthlp:172-174 (Description), :181-183, :281-282 ("described in {manhelp twoway G-2:graph twoway}; where {cmd:dash} differs, this file says so under the option concerned."), :6456-6465 (Unsupported intro); README.md:6-8, :15-16, :59; dash.pkg:7-9. The owner sentences are cited in index Appendix B with their audit lines (:850-871).

## User stories

- **US-48-04.1** As a Stata user evaluating dash from the README, I want its claims about options to be true, so I can judge the drop-in claim on evidence.
- **US-48-04.2** As the maintainer, I want one test per audited false sentence, so none returns.

## Business requirements

- **BR-48-04.1** None of the audit's 22 false sentences is false at the end of WP-48 (HR-17 at the end of WP-49).
- **BR-48-04.2** The README keeps "dash takes the place of twoway" and the drop-in framing (M14).
- **BR-48-04.3** Each HR has one test that fails if the false wording returns.

## Technical requirements

- **TR-48-04.1** New `test/test_false_sentences.py`: helpers `_read`, `_help`, `_between`, `_prose` copied from test/test_help_claims_1.py:84-117, and `_owner_pin(item_id)` (the D-48-04.b reader); 20 classes, one per HR from `TestHR01` to `TestHR22`, without `TestHR17` (49-01's) and with HR-5 and HR-22 in one class `TestHR05and22`; each has one test (HR-7 two: the sentence and the conformance test; HR-2 one per part).
- **TR-48-04.2** Edits of D-48-04.a in dash.sthlp, README.md, dash.pkg.
- **TR-48-04.3** No BUGS/GAPS4 row (PD-8: the HR lines are not rows); CHANGELOG: one line under `### Fixed in WP-48`: "The help, README and package description make no claim the drop-in audit found false (WP-48, HR-1..HR-22)" -- PD-7's `(WP-NN, <id>)` form with the HR range as the id.

## Boundaries

- Do not change behaviour; do not rewrite an owner's sentence that is already true (D-48-04.b); do not remove the README's drop-in claim; name no browser but Chrome; never list heatmap or sunflower as plot types (R14) -- `TestHR05and22` uses the words only as test input (A-9).
- **The existing Stata-version sentences stay byte-identical** (A-2, M2, REVIEW-5 R5-26): README.md:32-33, dash.pkg:17-18 (the `d Requires: Stata 19 or later; tested on StataNow 19.5 ...` line and the `d` line after it), dash_setup.sthlp:155-157, dash.sthlp:6700-6703, CHANGELOG.md:919 and GAPS3.md:258 (anchors at `090d928`; re-read by phrase, `grep -n "tested on StataNow 19.5"` in each file, GAPS3.md:258 by its `| I1 |` row). This section rewrites README.md:6-8 and :59 and dash.pkg:7-9 only (rewrapping the `d` lines of :7-9 never reaches :17-18), adds no sentence about Stata versions, and no test reads or asserts those lines.
- No jitter text is edited (Q50): `TestHR21` reads Differences headings only.

## Stata truth

None (prose). No cscript cases; Q4804 is reserved and unused.

## TDD test stubs

- Test: HR-1 -- test_false_sentences.py::TestHR01::test_grammar_not_same_syntax (fails at base).
- Test: HR-3 -- ::TestHR03::test_readme_and_pkg (asserts, through `_prose()`, D-48-04.a's HR-3 sentence in README.md and in dash.pkg, its last clause `dash adds two options of its own, hover() and table` included, and that the false phrase `the rest are accepted and named in a note` is absent from both; fails at base).
- Test: HR-4 -- ::TestHR04::test_no_every_difference (fails at base).
- Test: HR-6 -- ::TestHR06::test_no_always_runs (asserts the new Unsupported intro, its clause `except dash's own {opt hover()} and {opt table}` and the `dash##dashonly` link included, and that `a command copy-pasted from a do-file always runs` is absent; fails at base).
- Test: HR-7 -- ::TestHR07::test_sentence, ::test_every_documented_difference_is_in_the_help (the sentence test fails at base; the conformance test applies D-48-04.a HR-7's (a) rule -- WP-33..49 Documented entries only, a `dash##` link or a `dash.sthlp <section name>` equal to a `{ul:...}` heading or `{title:...}` -- and (b), reporting every mismatch by entry title).
- Test: HR-21 -- ::TestHR21::test_differences_link_the_limits_and_recast_notes (headings only for jitter and Python).
- Test: HR-2 -- ::TestHR02::test_name_registers, ::test_no_graph_memory, ::test_tested_platform (owner-pin form, D-48-04.b).
- Test: HR-5 and HR-22 -- ::TestHR05and22::test_owner_pin (35-09's node; the absence fallback only if 35-09 left no help pin).
- Test: HR-8 .. HR-16, HR-18 .. HR-20 -- ::TestHRnn::test_owner_pin, one each, as D-48-04.b lists (each should pass at the base; any failure is group 2's).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| the 21 HR sentences (20 classes) | pytest test_false_sentences.py | dash.sthlp, README.md, dash.pkg, dash_setup.sthlp, ROADMAP.md, BUGS.md | n/a |
| README and package pins | pytest test_readme.py and the dash.pkg readers | -- | n/a |
| help conformance | pytest test_help_conformance.py, test_help_claims_*.py | -- | n/a |

Acceptance criteria:
- **AC-48-04.1** test_false_sentences.py passes; the group-1 tests failed at the base (saved).
- **AC-48-04.2** test_readme.py, test_help_conformance.py and every test_help_claims_*.py pass.

## Tasks

**Commit boundary.** Group 1: 48-04-01 (no commit), 48-04-02 (no commit), 48-04-03 (commit `Correct the help, README and package claims the audit found false (WP-48 48-04)`). Group 2: 48-04-04 (commit `Correct false sentences left by earlier sections (WP-48 48-04)`, only if a sentence is still false). 48-04-05 runs the readers; 48-04-06 checks.

```xml
<task type="auto" id="48-04-01">
  <name>Write the HR checklist tests</name>
  <files>test/test_false_sentences.py</files>
  <action><![CDATA[Create test/test_false_sentences.py (TR-48-04.1) with the 20 classes: group-1 tests assert D-48-04.a's sentences; owner tests use D-48-04.b's owner-pin form (the absence fallback only where the owner left no pin). Run on the base; save the output to <scratch>/48-04-01-failure.txt and list in <scratch>/48-04-owner-fails.txt every owner test that fails.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_false_sentences.py -q -n0 -> TestHR01, TestHR03, TestHR04, TestHR06 and TestHR07::test_sentence fail; the owner list file exists (possibly empty)]]></verify>
  <done>Every audited sentence has a test and the failures to fix are recorded.</done>
</task>

<task type="auto" id="48-04-02">
  <name>Rewrite the help sentences HR-1, 6, 7</name>
  <files>dash.sthlp</files>
  <action><![CDATA[Apply D-48-04.a's HR-1, HR-6 and HR-7 sentences, each found by phrase. Check HR-21 (D-48-04.a); if a Differences link is missing because 40-02 or 46-02 named the note differently, add the one-line Differences entry linking to their note. Run TestHR01, TestHR06, TestHR07, TestHR21, test_help_conformance.py and test_help_claims_*.py; flip any reader of the old sentences with a Flipped: line.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_false_sentences.py::TestHR01 test/test_false_sentences.py::TestHR06 test/test_false_sentences.py::TestHR07 test/test_false_sentences.py::TestHR21 test/test_help_conformance.py -q -n0 -> pass]]></verify>
  <done>The four help sentences are true and pinned.</done>
</task>

<task type="auto" id="48-04-03">
  <name>Rewrite README and dash.pkg claims; commit</name>
  <files>README.md, dash.pkg</files>
  <action><![CDATA[Apply D-48-04.a's HR-3 sentence to README.md:6-8 and dash.pkg:7-9 and HR-4's to README.md:59; keep "dash takes the place of twoway" (M14). Run TestHR03, TestHR04, test_readme.py and every test that reads dash.pkg (grep -l "dash.pkg" test/*.py); confirm git diff -U0 README.md dash.pkg touches none of the A-2 lines (Boundaries): README.md:32-33 and both dash.pkg lines 17-18 (the `d Requires: Stata 19 or later; tested on StataNow 19.5 ...` line and the `d` line after it), located first by phrase with grep -n "tested on StataNow 19.5" README.md dash.pkg; add the CHANGELOG line (TR-48-04.3); take Notes' "Before every commit" steps (no GAPS4 item: steps (1)-(3) touch no row; then `git -C $WT pull --ff-only . main`, detect-changes, the message grep); commit group 1.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_false_sentences.py test/test_readme.py -q -n0 -> pass except tests listed in <scratch>/48-04-owner-fails.txt; subject ends "(WP-48 48-04)"; grep -ci 'claude\|anthropic' on the message -> 0]]></verify>
  <done>The README and package description make no false option claim and group 1 is committed.</done>
</task>

<task type="auto" id="48-04-04">
  <name>Correct owner sentences still false</name>
  <files>dash.sthlp, README.md, dash_setup.sthlp</files>
  <action><![CDATA[For each test in <scratch>/48-04-owner-fails.txt: read the owner's closed BUGS entry and pin (D-48-04.b), measure the behaviour with the owner's pin or a one-line probe, and rewrite the sentence to it (never an A-2 line); cite the owner section and HR in the commit body; take Notes' "Before every commit" steps (no GAPS4 item: steps (1)-(3) touch no row; then `git -C $WT pull --ff-only . main`, detect-changes, the message grep) and commit. If the list is empty, skip this task and write "no owner sentence was false at the WP-48 base" to <scratch>/48-04-handback.txt.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_false_sentences.py -q -n0 -> every test passes; subject ends "(WP-48 48-04)" when a commit was made]]></verify>
  <done>Every HR sentence held by this file is true.</done>
</task>

<task type="auto" id="48-04-05">
  <name>Run the help and README readers</name>
  <files>none</files>
  <action><![CDATA[Run test_help_conformance.py, every test_help_claims_*.py, test_help_claims_p16.py, test_tracker_accuracy_p16.py, test_readme.py and test_tracking_documents.py.]]></action>
  <verify><![CDATA[all pass]]></verify>
  <done>No other help or README reader broke.</done>
</task>

<task type="auto" id="48-04-06">
  <name>Record HR-17's hand-off</name>
  <files>none</files>
  <action><![CDATA[Append to <scratch>/48-04-handback.txt: "HR-17 is tested by 49-01 (TestHR17 added to test/test_false_sentences.py in the plot:PT-7 commit)"; grep the commit messages for claude|anthropic.]]></action>
  <verify><![CDATA[the hand-back file names HR-17's owner; grep count 0]]></verify>
  <done>The checklist is complete for WP-48 and HR-17's owner is recorded.</done>
</task>
```

## Section completion criteria

- test/test_false_sentences.py holds 20 classes covering 21 HRs, all passing; group 1 committed; group 2 committed or recorded as unnecessary.
- README keeps its drop-in claim; Chrome is the only browser named; no banned plot type.

## Notes

- **Traps.** (1) dash.pkg's `d` lines are read by `net describe`; keep each line under 80 characters and the `d` prefix. (2) Do not touch README's gallery block between `<!-- dash-gallery:start -->` and `<!-- dash-gallery:end -->` (33-08 writes it). (3) The HR-7 conformance test must read only Documented entries whose Resolution ends `Closes GAPS4 <id> (WP-NN, <id>).` with NN >= 33 and the residual entries of D-48-04.a's (b) (PD-4 forms), not WP-29..32 history (which also starts `Documented`) and not rows still in `GAPS4_OPEN`; its section-name rule is D-48-04.a HR-7's (a), never a free-text match.
- **Help paragraphs this section owns (R3):** dash.sthlp's Description (:172-174, :181-183), the plot-types sentence (:281-282), the Unsupported intro (:6456-6465), any Differences entry HR-21 finds missing; README.md:6-8 and :59; dash.pkg:7-9.
- **Merge rules touched:** R3, R4 (one CHANGELOG line), R14.
- **Before every commit (BRIEF "The corpus ledger and the known-differences tables" and "Pull form"; CLAUDE.md rules 4 and 6; R13).** `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp48-s04`. This section closes no GAPS4 item (PD-8's checklist), so BRIEF's closing steps (1)-(3) have no lead id to run on: no row of `scripts/corpus/ledger.tsv`, of a `*_KNOWN` table or of a deliberate dict is touched, and since the guard reads frozen example records and no help file (D-33-09.g), help, README and dash.pkg text cannot change Q3309-1, so `corpus_guard_truth.json` is not regenerated; run `python3 -m pytest $WT/test/test_corpus_ledger.py -q -n0` once. Then (4) pull from local main (CLAUDE.md rule 4): `git -C $WT pull --ff-only . main` (a no-op when the batch base already contains main); if it refuses, stop and report to the orchestrator, never a merge commit on a section branch; (5) run `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a `partial` or `truncated` result is run again) and name HIGH, CRITICAL or UNKNOWN risk in the hand-back; (6) grep the message for claude|anthropic before and after committing.
- **Commit-body lines:** `Regression: test/test_false_sentences.py::TestHR03::test_readme_and_pkg -- failed at <base sha> with <text>`; `Flipped: <node> -- it read a sentence the audit found false (HR-<n>)`.
