# Section 48-01: Stale help paragraphs rewritten and pinned

> Part of: WP-48 (Help, README and tracker accuracy, audit package 16) · Items: LT-27, plot:PT-5, basic:PT-16, GW-22 · Risk: green · Batch: 48.1 · Depends on: none (WP-34..47 landed) · Blocks: 48-02 · Tasks: 9, 4 commits · Case-id prefix: Q4801

## Overview

**What is wrong today.** Help paragraphs describe behaviour that later work changed:

- **LT-27 (GW-24, syn:SD-14, ECO-10, DT-05, TR-21, sil:SD-15).** dash.sthlp:6682-6687 ("Two further notes on the note itself ... a typo is reported as ignored rather than rejected: `titl(x)` abbreviates `title()` and works, while `titel(x)` appears in the note") contradicts :1026-1029 and the behaviour: `titel(x)` is refused, r(198) "option titel() not allowed" (probes R_typo, p4 d_titel, Y01, P04; test_help_claims_8.cscript:625-631 pins the refusal). The paragraph before it, :6629-6640 ("Some names that reach the note are not twoway options ... xreverse ... xcommon ... lockaspect, zoom() and ddensity"), is stale too: WP-32 made dash refuse those as twoway does (BUGS.md:2599; Differences item 5 names `xreverse` as refused; test_option_validation.cscript:2833, U50). The same paragraph's "It names option names, never the values supplied" is contradicted by sub-option notes that print values (`justification(right)`).
- **plot:PT-5 (ECO-9, DT-06).** dash.sthlp:854-858 ("graph is read only before twoway ... before any other word it is read as a plot type and refused, "unrecognised plot type 'graph'"") contradicts :156-163 and dash.ado:107-118 (`_dash_prefix_word`): `graph`, `gr`, `gra`, `grap`, `twoway`, `tw` .. are refused in every position, "graph is not a twoway plot type", r(198), as twoway refuses `twoway graph ...` (twoway_command_form_truth.json prefix[23],[24]). The quoted message exists nowhere in the code.
- **basic:PT-16 (DT-07..DT-12, stat:PT-18, BY-9).** Stale passages, each listed in the audit (:801) with its evidence: :332 ("On the other plot types these three options are named in the note": mangle/barbsize are silent off the arrow types, headlabel is silent or refused, `_dash_tw_silent_tab` dash_parse.mata:8240-8262); :3472-3475 (headlabel on pcscatter/pccapsym "named"); :3611-3613 (recast() on dot "taken and named": silent, :8258); :3676-3679 (degree() above 7 refused: drawn with a note since WP-31 D35, dash.ado:3878-3880, and the comment dash.ado:3633 "degree 0..7"); :3977-3985 (fpfit "accepts the three so a pasted command still runs": refused r(198) in twoway's words, probes P05/P18); :4084-4087 (acolor()... "named in the note" off the ci types: silent); :1239-1241 (mlabel(t*) "refused": expanded by unab, dash.ado:4612-4640, and 47-02 makes it draw no labels as twoway, basic:PT-3); :240-246 (x/y/top variables "shadowed in hover() and mlabel()": fixed by the `__dashu_` alias, BUGS.md:3707); :3635-3636 (merged keys and the lone-histogram legend "still drawn": fixed, :5612-5622); :3179-3180 (by(style(rescale)) "with a note": no note, P13); :3290-3292 (subtitle()'s fcolor/lcolor/nobox "do not restyle it ... named": they restyle, :3338-3340, `_DASH_BY_LABEL_BOX_WORDS`); :4782-4786 (lalign), :6573-6577 (dlalign), :6597-6600 ("measured on every plot type"); TWOWAY_COVERAGE_AUDIT.md:71/:81/:84 (headlabel); the `_dot_style` docstring (dash_render.py:23696-23705, "named by dash.ado"); test/test_lpoly_degree.py:15-17 (degree(8) "stays dash's own bound").
- **GW-22 (GW-23).** dash.sthlp:6249-6251 ("#pt, #in and #cm ... are converted at the scheme's smaller graphsize side (xsize() and ysize() do not change it)") contradicts :5708-5717 and `_dash_ref_in` (dash_render.py:27374-27401): the reference is min(xsize, ysize). :955-967 lists clegend(), plegend() and pcycle() among "the options dash names in its note" and says "Each one given once is still named in the note"; they are drawn (dash.sthlp:5469-5487; probe p1 d_pcyc: no note).

**After this section**, every passage above states what dash does at the WP-48 base, each pinned by a help-claim test (and, where measurable, a probe case showing dash does what the sentence says).

**Why one section.** All four items are stale help text the audit found by contrast with other help paragraphs and the code; one owner of those paragraphs (R3) keeps edits from colliding.

**Test order and commit rule.** Four commits `(WP-48 LT-27)`, `(WP-48 plot:PT-5)`, `(WP-48 basic:PT-16)`, `(WP-48 GW-22)`. For each item: one task writes its help-claim tests (they fail on the stale text), saves the failure text, does not commit; the next rewrites the text and commits. A passage another section already corrected (Appendix B HR-14: 47-01 for :3472-3475 and :332, 47-03 for :4782-4786 and :6573-6577) is verified, pinned, and listed in the commit body as "already corrected by <section>"; its pin then passes at the base, which the commit body records with the failure measured at `090d928` in a detached scratch worktree.

### Section decisions (binding on the executor)

- **D-48-01.a Passages are found by their words, not their line numbers.** WP-34..47 moved every anchor. Each task greps the quoted phrase (e.g. `grep -n "reported as ignored rather than" dash.sthlp`); if a phrase is gone, the section that removed it is named in the commit body (git log -S'<phrase>' -- dash.sthlp).
- **D-48-01.b Each rewrite states measured behaviour.** The new sentence for each passage is decided by a probe at the WP-48 base where the audit's claim depended on later work (headlabel, mlabel(t*), lalign, dlalign, degree()): the probe is a case in `test/test_help_claims_8.cscript` (the area script that already pins `titel()`), id `Q4801-<k>`, that runs the command, records rc and note, and the help sentence says exactly that.
- **D-48-01.c The two LT-27 paragraphs.** :6629-6640 is rewritten to: these words are refused as twoway refuses them, `option xreverse not allowed`, r(198), naming what twoway spells instead (`xscale(reverse)`, `xscale(alt)`, `graph combine`'s `xcommon`, the sub-option homes of `margin()`, `region()`, `altaxis`, `addplot()`'s commands), with lockaspect, zoom() and ddensity as options of no Stata graph command; the mlabfontface() sentence stays. :6682-6687 is replaced by one sentence: "A misspelled option is refused as twoway refuses it: titl(x) abbreviates title() and works, titel(x) is option titel() not allowed, r(198)." -- and "never the values supplied" is removed (sub-option notes print the token as typed).
- **D-48-01.d plot:PT-5 deletes the paragraph** (:854-858) and adds nothing: :156-163 already says it correctly; a help-claim test asserts the phrase "unrecognised plot type" is absent from dash.sthlp and that :156-163's sentence is present.
- **D-48-01.e GW-22.** :6249-6251's parenthesis becomes "(the smaller of xsize() and ysize() when either is given, as twoway converts them)"; :955-967's sentence lists only options that are noted at the WP-48 base (probe Q4801-9 registers `clegend(on)`, `plegend(on)`, `pcycle(2)`, `atobs` once each and records the note; the sentence names those the probe shows noted, and says clegend(), plegend() and pcycle() are drawn, linking to their paragraphs).

## Risk: [green] -- help text and docstrings only, each pinned

**Why.** No behaviour changes; the risk is pins that read the old sentences.

**Risk factors.** (1) Existing help-claim tests read some of these sentences (test_help_claims_*.py, test_help_conformance.py's entry parser for the Unsupported section, which holds :6595-6606 and :6629-6687). (2) Removing or reflowing lines inside `{marker unsupported}` .. `{marker dependencies}` changes `_unsupported_section()`'s set if an `{opt}` moves into or out of a `{phang2}` entry.

**Mitigation.** (1) `grep -rn "<phrase>" test/` before each edit; flip each reader with a `Flipped:` line. (2) After each edit run `python3 -m pytest test/test_help_conformance.py -q -n0`; the count pin `len(_unsupported_section()) == 59` (or its value at the WP-48 base) must not move in this section (48-02 owns it).

## Dependencies

- **Depends on:** none in WP-48; every WP-34..47 section has landed (WP order), so the behaviour described is final for those items.
- **Blocks: 48-02** (batch 48.2), which edits the Unsupported list and its count pin.
- **Parallel batch 48.1** with 48-03. Shared file: TWOWAY_COVERAGE_AUDIT.md -- 48-01 edits only the headlabel rows (:71, :81, :84 at `090d928`) for basic:PT-16; 48-03 owns every other row. Merge order 48-01, 48-03; the hunks are disjoint.

## Evidence

At `090d928` (re-read by phrase at the WP-48 base):

```
6682 {pstd}
6683 Two further notes on the note itself.  It names option {it:names}, never the
6684 values supplied.  And because an unknown option cannot be told apart from a
6685 misspelled supported one, a typo is reported as ignored rather than
6686 rejected: {cmd:titl(x)} abbreviates {cmd:title()} and works, while
6687 {cmd:titel(x)} appears in the note.
```

```
854 {phang2}    {ul:graph is read only before twoway.}  After {cmd:dash},
855     {cmd:graph} is a prefix only when {cmd:twoway} follows it; before any
856     other word it is read as a plot type and refused, "unrecognised plot
857     type 'graph'", {cmd:r(198)}, where {cmd:graph} followed by a word that
858     is not one of its subcommands gives {cmd:r(4023)}.
```

```
6249 {it:#}{cmd:pt}, {it:#}{cmd:in} and {it:#}{cmd:cm}, which are converted at
6250 the scheme's smaller {cmd:graphsize} side ({cmd:xsize()} and {cmd:ysize()}
6251 do not change it).
```

The other passages are quoted in the Overview with their anchors. Existing pins: test/test_help_claims_8.cscript:625-631 (titel() refused), test_option_validation.cscript:2833 (U50, xreverse refused).

## User stories

- **US-48-01.1** As a Stata user reading the help, I want every sentence about notes and refusals to say what dash does, so I can trust it when I paste a command.
- **US-48-01.2** As the maintainer, I want each corrected sentence pinned, so a later change cannot make it false silently.

## Business requirements

- **BR-48-01.1** No sentence of dash.sthlp says a misspelled option or a non-twoway word reaches the note.
- **BR-48-01.2** dash.sthlp no longer describes graph as a prefix or quotes "unrecognised plot type".
- **BR-48-01.3** Each basic:PT-16 passage states the behaviour its probe measures at the WP-48 base; the two docstrings and the three coverage-audit rows agree with it.
- **BR-48-01.4** The units sentence and the :955-967 sentence state what dash draws and notes.
- **BR-48-01.5** Each corrected sentence has a help-claim test; each measurable one a probe case.

## Technical requirements

- **TR-48-01.1** New test file `test/test_help_claims_p16.py` (helpers copied from test/test_help_claims_1.py: `_read`, `_help`, `_between`, `_prose`; no import from another test module), one class per item: `TestTypoParagraph`, `TestGraphPrefix`, `TestStalePassages` (one test per passage), `TestUnitsAndDrawnOptions`.
- **TR-48-01.2** Probe cases in `test/test_help_claims_8.cscript` under a header `* WP-48 48-01: probes for the corrected sentences`, ids `Q4801-1` .. `Q4801-9`: Q4801-1 titel() refused and titl() drawn; Q4801-2 xreverse, xcommon, lockaspect refused r(198) with twoway's line; Q4801-3 `dash graph scatter mpg weight` refused "graph is not a twoway plot type"; Q4801-4 headlabel on pcscatter (rc and note); Q4801-5 recast(line) on dot (no note); Q4801-6 lpoly degree(8) (rc 0, note text); Q4801-7 fpfit bwidth(2) refused; Q4801-8 acolor(red) on scatter (no note); Q4801-9 the GW-23 options once each (notes recorded).
- **TR-48-01.3** Docstrings: `_dot_style` (dash_render.py `def _dot_style`, re-read) states how dlalign is taken at the WP-48 base (47-03's rule); test/test_lpoly_degree.py's module docstring states degree() above 7 is drawn with a note; dash.ado's comment "degree 0..7" (grep it) is corrected. These are text only; `function_test_map.py` is untouched.
- **TR-48-01.4** TWOWAY_COVERAGE_AUDIT.md: the headlabel rows (grep `headlabel`) say where headlabel is drawn at the WP-48 base (47-01's rule).
- **TR-48-01.5** CHANGELOG (PD-7): one line per item under `### Fixed in WP-48`, ending `(WP-48, <id>)` -- the four texts are in the closing tasks. GAPS4 Tracked lines in the Closed form (`Closed in WP-48, BUGS.md "<title>", commit pending.`). BUGS entries closed in PD-4's closed form verbatim: `  - Resolution: Fixed <ddmonyyyy> (WP-48, <id>). <the help paragraph rewritten, and where>. Pinned by <node>[, <cscript case>]. Closes GAPS4 <id> (WP-48, <id>).`

## Boundaries

- Do not edit the Unsupported list entries or its count pin (48-02), dash_setup.sthlp, CHANGELOG.md's existing lines (this section only appends its four `### Fixed in WP-48` lines, union-merged, R4), GAPS3.md, DROPIN-REMAINING.md, rejected_options.json, TWOWAY_COVERAGE_AUDIT.md rows other than headlabel (48-03), README.md and dash.pkg (48-04), any code.
- The existing Stata-version sentences (dash.sthlp:6700-6703 at `090d928`, and the others A-2 names: README.md:32-33, dash.pkg:17-18, dash_setup.sthlp:155-157, CHANGELOG.md:919, GAPS3.md:258; re-read by phrase) stay byte-identical, and this section adds no sentence about Stata versions (A-2, M2).
- Do not reword a sentence another section owns beyond the passages listed; Appendix B sentences outside this list belong to their owners and to 48-04.

## Stata truth

None new (no extract script, PD-6: WP-48 has no truth script). The probes are cases in test_help_claims_8.cscript (TR-48-01.2), run with `scripts/stata_slot.sh` through a two-line driver.

## TDD test stubs

- Test: the typo paragraph says titel() is refused -- test_help_claims_p16.py::TestTypoParagraph::test_titel_is_refused (fails at base: "appears in the note").
- Test: the reach-the-note paragraph says those words are refused -- ::TestTypoParagraph::test_names_are_refused.
- Test: no "unrecognised plot type" -- ::TestGraphPrefix::test_no_prefix_paragraph (fails at base).
- Test: each basic:PT-16 passage -- ::TestStalePassages::test_<passage> for `mangle_barbsize_headlabel`, `headlabel_pc`, `recast_on_dot`, `degree_above_7`, `fpfit_bwidth`, `acolor_off_ci`, `mlabel_pattern`, `shadowed_fields`, `merged_keys`, `style_rescale`, `subtitle_box`, `lalign`, `dlalign`, `every_plot_type`, `coverage_audit_headlabel`, `dot_style_docstring`, `lpoly_degree_docstring` (each fails at base unless already corrected; see the commit rule).
- Test: units and drawn options -- ::TestUnitsAndDrawnOptions::test_units_reference, ::test_drawn_not_noted.
- cscript: Q4801-1 .. Q4801-9 (test_help_claims_8.cscript).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| each corrected sentence | pytest test_help_claims_p16.py | dash.sthlp, docstrings, TWOWAY_COVERAGE_AUDIT.md | n/a (text) |
| the behaviour each states | cscript Q4801-1..9 | live Stata | one-line route |
| no collateral | test_help_conformance.py, test_help_claims_*.py | -- | n/a |

Acceptance criteria:
- **AC-48-01.1** Every test of test_help_claims_p16.py passes; every one failed at the WP-48 base or at `090d928` (recorded).
- **AC-48-01.2** Q4801-1..9 pass; each help sentence agrees with its case's recorded rc and note.
- **AC-48-01.3** `_unsupported_section()` is unchanged by this section.

## Tasks

**Commit boundary.** LT-27: 48-01-01 (no commit) + 48-01-02 (commit `Correct the help's typo and refusal paragraphs (WP-48 LT-27)`). plot:PT-5: 48-01-03 (commit `Remove the stale graph-prefix paragraph (WP-48 plot:PT-5)`; failing test written and saved first in the task). basic:PT-16: 48-01-04 (no commit) + 48-01-05 + 48-01-06 (one commit at the end of 48-01-06, `Correct stale passages on taken and refused options (WP-48 basic:PT-16)`). GW-22: 48-01-07 (no commit) + 48-01-08 (commit `Correct the units and drawn-options sentences (WP-48 GW-22)`). 48-01-09 is the section check.

```xml
<task type="auto" id="48-01-01">
  <name>Write LT-27 help-claim tests and probes</name>
  <files>test/test_help_claims_p16.py, test/test_help_claims_8.cscript</files>
  <action><![CDATA[Create test/test_help_claims_p16.py with the helpers of TR-48-01.1 and TestTypoParagraph (test_titel_is_refused: the Unsupported section's prose, via _prose(_between(_help(), "{marker unsupported}", "{marker dependencies}")), contains "titel(x) is option titel() not allowed" and not "appears in the note"; test_names_are_refused: the paragraph naming xreverse says "refused" and not "reach the note"). Add Q4801-1 and Q4801-2 to test_help_claims_8.cscript. Run the pytest class on the base and the cscript through stata_slot.sh; save to <scratch>/48-01-01-failure.txt.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_help_claims_p16.py::TestTypoParagraph -q -n0 -> both fail; the cscript log shows "Q4801-1 PASS" and "Q4801-2 PASS" (the behaviour already matches twoway)]]></verify>
  <done>The LT-27 pins fail on the stale text and the probes show the refusals.</done>
</task>

<task type="auto" id="48-01-02">
  <name>Rewrite the two LT-27 paragraphs</name>
  <files>dash.sthlp</files>
  <action><![CDATA[Find both paragraphs by phrase (D-48-01.a) and rewrite them as D-48-01.c says. Flip any reader found by grep -rn "reported as ignored\|reach the note" test/. Run test_help_claims_p16.py::TestTypoParagraph, test_help_conformance.py, test_help_claims_8.py; close LT-27's BUGS entry (TR-48-01.5's closed form; the Resolution names TestTypoParagraph and Q4801-1, and the ids GW-24, syn:SD-14, ECO-10, DT-05, TR-21, sil:SD-15) and GAPS4 line; delete its GAPS4_OPEN (test/test_tracking_documents.py) line; add "- The help says a misspelled option and the words that are no twoway option are refused, as dash refuses them; it said they reached the note (WP-48, LT-27)" under "### Fixed in WP-48". Before the commit take BRIEF's closing steps (1)-(3) for LT-27 (Notes "Before every commit" gives each command in full): (1) delete LT-27's plain rows of `$WT/scripts/corpus/ledger.tsv` (a `LT-27 (documented)` or `LT-27 (residual)` row stays, A-10), rerun `python3 $WT/scripts/corpus/ledger.py`, `git -C $WT add -f test/fixtures/corpus_ledger.json` and run test/test_corpus_ledger.py; (2) run `python3 $WT/test/known_differences.py LT-27` and delete every row it prints from its `*_KNOWN` table -- a difference LT-27's ruling keeps moves instead into that table's deliberate dict (`DELIBERATE` for `VALUE_KNOWN`, `<NAME>_DELIBERATE` for any other `<NAME>_KNOWN`) as `"<key>": "<ruling id>: <what is kept>"` -- then run the hygiene command it prints; (3) run the S09 guard block of test/test_wp33_truth.cscript (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example (an improved verdict or a changed field), regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do, `git -C $WT add -f` it and commit it with LT-27. Then take Notes' steps (4)-(6) (`git -C $WT pull --ff-only . main`, detect-changes, the message grep) and commit.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_help_claims_p16.py::TestTypoParagraph test/test_help_conformance.py test/test_tracking_documents.py test/test_corpus_ledger.py -q -n0 -> pass; subject ends "(WP-48 LT-27)"; grep -ci 'claude\|anthropic' on the message -> 0]]></verify>
  <done>The help says a typo and the non-twoway words are refused, pinned, and LT-27 is committed.</done>
</task>

<task type="auto" id="48-01-03">
  <name>Delete the graph-prefix paragraph</name>
  <files>dash.sthlp, test/test_help_claims_p16.py, test/test_help_claims_8.cscript</files>
  <action><![CDATA[First add TestGraphPrefix::test_no_prefix_paragraph (dash.sthlp holds neither "unrecognised plot type" nor "graph is read only before twoway"; the syntax paragraph holds "graph is not a twoway plot type" or the sentence listing graph among the refused prefix words) and Q4801-3; run on the base and save to <scratch>/48-01-03-failure.txt. Then delete the paragraph (D-48-01.d), run the class, test_help_conformance.py, test_tracking_documents.py and the cscript; close plot:PT-5 (BUGS in TR-48-01.5's closed form naming ECO-9 and DT-06; GAPS4; GAPS4_OPEN (test/test_tracking_documents.py); CHANGELOG "- The help no longer describes graph as a prefix read before twoway; dash refuses it in every position, as twoway does (WP-48, plot:PT-5)"). Before the commit take BRIEF's closing steps (1)-(3) for plot:PT-5 (Notes "Before every commit" gives each command in full): (1) delete plot:PT-5's plain rows of `$WT/scripts/corpus/ledger.tsv` (a `plot:PT-5 (documented)` or `plot:PT-5 (residual)` row stays, A-10), rerun `python3 $WT/scripts/corpus/ledger.py`, `git -C $WT add -f test/fixtures/corpus_ledger.json` and run test/test_corpus_ledger.py; (2) run `python3 $WT/test/known_differences.py plot:PT-5` and delete every row it prints from its `*_KNOWN` table -- a difference plot:PT-5's ruling keeps moves instead into that table's deliberate dict (`DELIBERATE` for `VALUE_KNOWN`, `<NAME>_DELIBERATE` for any other `<NAME>_KNOWN`) as `"<key>": "<ruling id>: <what is kept>"` -- then run the hygiene command it prints; (3) run the S09 guard block of test/test_wp33_truth.cscript (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example (an improved verdict or a changed field), regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do, `git -C $WT add -f` it and commit it with plot:PT-5. Then take Notes' steps (4)-(6) (`git -C $WT pull --ff-only . main`, detect-changes, the message grep) and commit.]]></action>
  <verify><![CDATA[before: test_no_prefix_paragraph fails; after: python3 -m pytest test/test_help_claims_p16.py::TestGraphPrefix -q -n0 -> pass; "Q4801-3 PASS"; subject ends "(WP-48 plot:PT-5)"]]></verify>
  <done>The stale graph-prefix paragraph is gone, pinned, and plot:PT-5 is committed.</done>
</task>

<task type="auto" id="48-01-04">
  <name>Probe and pin the basic:PT-16 passages</name>
  <files>test/test_help_claims_p16.py, test/test_help_claims_8.cscript</files>
  <action><![CDATA[Add Q4801-4 .. Q4801-8 (TR-48-01.2) and run them; record each case's rc and note in <scratch>/48-01-probes.txt. For each passage of the basic:PT-16 list write TestStalePassages::test_<passage> asserting the sentence the probe supports (D-48-01.b) and the absence of the stale phrase. Run on the base; for each test that passes already (a section of WP-34..47 corrected it), rerun it against 090d928 in a detached scratch worktree (git worktree add <scratch>/base090 090d928, copy the test file, run, remove the worktree) and record that failure. Save everything to <scratch>/48-01-04-failure.txt.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_help_claims_p16.py::TestStalePassages -q -n0 -> the tests for passages still stale fail; the failure file lists every test with a failure at the base or at 090d928]]></verify>
  <done>Every basic:PT-16 passage has a pin that failed on stale text, and the probes record the behaviour to describe.</done>
</task>

<task type="auto" id="48-01-05">
  <name>Rewrite the dash.sthlp passages</name>
  <files>dash.sthlp</files>
  <action><![CDATA[Rewrite each still-stale passage found by phrase: :332, :3472-3475, :3611-3613, :3676-3679, :3977-3985, :4084-4087, :1239-1241, :240-246, :3635-3636, :3179-3180, :3290-3292, :4782-4786, :6573-6577, :6597-6600 (anchors at 090d928), each to the behaviour <scratch>/48-01-probes.txt records or the code shows (the shadowed-fields passage: hover() and mlabel() read the user's variable through the __dashu_ alias; merged keys: drawn as twoway merges them; style(rescale): drawn with no note; subtitle() box words restyle the label boxes; "measured on every plot type": replaced by the measured scope the fixture noted_option_truth.json covers). Do not touch a passage already correct; list those in <scratch>/48-01-already.txt with the section that corrected them (git log -S).]]></action>
  <verify><![CDATA[python3 -m pytest test/test_help_claims_p16.py::TestStalePassages -q -n0 -> every dash.sthlp passage test passes; test_help_conformance.py -> pass with the Unsupported count unchanged]]></verify>
  <done>Every stale dash.sthlp passage of basic:PT-16 states the measured behaviour.</done>
</task>

<task type="auto" id="48-01-06">
  <name>Correct docstrings and audit rows; commit</name>
  <files>dash_render.py, test/test_lpoly_degree.py, TWOWAY_COVERAGE_AUDIT.md</files>
  <action><![CDATA[Apply TR-48-01.3 and TR-48-01.4 (text only; dash.ado's "degree 0..7" comment too). Flip any test that read the old help sentences (grep each stale phrase in test/). Run test_help_claims_p16.py, test_help_claims_*.py, test_help_conformance.py, test_lpoly_degree.py, test_help_claims_8.cscript; close basic:PT-16 (BUGS in TR-48-01.5's closed form naming DT-07..DT-12, stat:PT-18, BY-9 and listing the passages already corrected with their sections; GAPS4; GAPS4_OPEN (test/test_tracking_documents.py); CHANGELOG "- Stale help passages on taken, noted and refused options state what dash does (WP-48, basic:PT-16)"). The commit body lists every passage. Before the commit take BRIEF's closing steps (1)-(3) for basic:PT-16 (Notes "Before every commit" gives each command in full): (1) delete basic:PT-16's plain rows of `$WT/scripts/corpus/ledger.tsv` (a `basic:PT-16 (documented)` or `basic:PT-16 (residual)` row stays, A-10), rerun `python3 $WT/scripts/corpus/ledger.py`, `git -C $WT add -f test/fixtures/corpus_ledger.json` and run test/test_corpus_ledger.py; (2) run `python3 $WT/test/known_differences.py basic:PT-16` and delete every row it prints from its `*_KNOWN` table -- a difference basic:PT-16's ruling keeps moves instead into that table's deliberate dict (`DELIBERATE` for `VALUE_KNOWN`, `<NAME>_DELIBERATE` for any other `<NAME>_KNOWN`) as `"<key>": "<ruling id>: <what is kept>"` -- then run the hygiene command it prints; (3) run the S09 guard block of test/test_wp33_truth.cscript (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example (an improved verdict or a changed field), regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do, `git -C $WT add -f` it and commit it with basic:PT-16. Then take Notes' steps (4)-(6) (`git -C $WT pull --ff-only . main`, detect-changes, the message grep) and commit.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_help_claims_p16.py test/test_lpoly_degree.py test/test_help_conformance.py -q -n0 -> pass; the cscript -> "Q4801-4 PASS" .. "Q4801-8 PASS"; subject ends "(WP-48 basic:PT-16)"]]></verify>
  <done>The basic:PT-16 passages, docstrings and audit rows are correct and pinned, and the item is committed.</done>
</task>

<task type="auto" id="48-01-07">
  <name>Write GW-22 pins and probe</name>
  <files>test/test_help_claims_p16.py, test/test_help_claims_8.cscript</files>
  <action><![CDATA[Add TestUnitsAndDrawnOptions (test_units_reference: the units paragraph says the smaller of xsize() and ysize(), not "do not change it"; test_drawn_not_noted: the :955-967 sentence does not call clegend(), plegend() or pcycle() "named in the note") and Q4801-9. Run; save to <scratch>/48-01-07-failure.txt.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_help_claims_p16.py::TestUnitsAndDrawnOptions -q -n0 -> both fail; Q4801-9 PASS and its log records which of the options print a note]]></verify>
  <done>GW-22's pins fail on the stale text and the probe records what is noted.</done>
</task>

<task type="auto" id="48-01-08">
  <name>Rewrite the units and drawn sentences</name>
  <files>dash.sthlp</files>
  <action><![CDATA[Apply D-48-01.e. Run TestUnitsAndDrawnOptions, test_help_conformance.py, test_help_claims_7.py (the size paragraphs), test_sizing.py's help readers; close GW-22 (BUGS in TR-48-01.5's closed form naming GW-23; GAPS4; GAPS4_OPEN (test/test_tracking_documents.py); CHANGELOG "- The help's units sentence and its list of noted options say what dash draws (WP-48, GW-22)"). Before the commit take BRIEF's closing steps (1)-(3) for GW-22 (Notes "Before every commit" gives each command in full): (1) delete GW-22's plain rows of `$WT/scripts/corpus/ledger.tsv` (a `GW-22 (documented)` or `GW-22 (residual)` row stays, A-10), rerun `python3 $WT/scripts/corpus/ledger.py`, `git -C $WT add -f test/fixtures/corpus_ledger.json` and run test/test_corpus_ledger.py; (2) run `python3 $WT/test/known_differences.py GW-22` and delete every row it prints from its `*_KNOWN` table -- a difference GW-22's ruling keeps moves instead into that table's deliberate dict (`DELIBERATE` for `VALUE_KNOWN`, `<NAME>_DELIBERATE` for any other `<NAME>_KNOWN`) as `"<key>": "<ruling id>: <what is kept>"` -- then run the hygiene command it prints; (3) run the S09 guard block of test/test_wp33_truth.cscript (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example (an improved verdict or a changed field), regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do, `git -C $WT add -f` it and commit it with GW-22. Then take Notes' steps (4)-(6) (`git -C $WT pull --ff-only . main`, detect-changes, the message grep) and commit.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_help_claims_p16.py test/test_help_conformance.py test/test_help_claims_7.py test/test_tracking_documents.py test/test_corpus_ledger.py -q -n0 -> pass; subject ends "(WP-48 GW-22)"]]></verify>
  <done>The units and drawn-options sentences are true and pinned, and GW-22 is committed.</done>
</task>

<task type="auto" id="48-01-09">
  <name>Check the section end to end</name>
  <files>none</files>
  <action><![CDATA[Run test_help_claims_p16.py, every test_help_claims_*.py, test_help_conformance.py, test_tracking_documents.py, and test_help_claims_8.cscript; grep the four commit messages for claude|anthropic.]]></action>
  <verify><![CDATA[all pass; grep count 0]]></verify>
  <done>The four commits are green together.</done>
</task>
```

## Section completion criteria

- Four commits `(WP-48 LT-27)`, `(WP-48 plot:PT-5)`, `(WP-48 basic:PT-16)`, `(WP-48 GW-22)`; each BUGS entry closed in PD-4's closed form, GAPS4 line Closed, GAPS4_OPEN line deleted, one CHANGELOG line each.
- test_help_claims_p16.py passes; Q4801-1..9 pass; `_unsupported_section()` unchanged.

## Notes

- **Traps.** (1) Inside `{marker unsupported}`, keep each `{phang2}` entry's `{opt}` set unchanged; write new names in prose as `{cmd:...}` so 48-02's count is not moved here. (2) SMCL line breaks inside a sentence make `_prose()` necessary in every assertion. (3) A passage corrected by an earlier section still gets its pin; its failure is measured at `090d928`.
- **Help paragraphs this section owns (R3):** dash.sthlp:6629-6640, :6682-6687, :854-858, :332, :3472-3475 (verify; HR-14 owner 47-01), :3611-3613, :3676-3679, :3977-3985, :4084-4087, :1239-1241, :240-246, :3635-3636, :3179-3180, :3290-3292, :4782-4786 and :6573-6577 (verify; HR-14 owner 47-03), :6597-6600 (HR-14), :6249-6251, :955-967.
- **Merge rules touched:** R3, R4 (four CHANGELOG lines), R5, R9 (flipped help readers); TWOWAY_COVERAGE_AUDIT.md shared with 48-03 (disjoint rows, merge order 48-01 then 48-03).
- **Before every commit (BRIEF "The corpus ledger and the known-differences tables" and "Pull form"; CLAUDE.md rules 4 and 6; R13; D-33-05.i, D-33-10.h, 33-09).** `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp48-s01`. Every item's closing task -- Fix, Document or Partly alike -- takes steps (1)-(3) for its lead id `<id>`, then (4)-(6): (1) list the item's plain ledger rows with `awk -F'\t' -v id='<id>' '$1 == id {print NR ": " $0}' $WT/scripts/corpus/ledger.tsv` and delete every line it prints (`<id> (documented)` and `<id> (residual)` rows stay, A-10), `git -C $WT add scripts/corpus/ledger.tsv` when a line was deleted, rerun `python3 $WT/scripts/corpus/ledger.py` (no `--run`: `_meta` is kept, TR-33-05.3), `git -C $WT add -f test/fixtures/corpus_ledger.json` and run `python3 -m pytest $WT/test/test_corpus_ledger.py -q -n0`; (2) run `python3 $WT/test/known_differences.py <id>` (33-10, D-33-10.h) and delete every `<file>:<line>` row it prints from its `*_KNOWN` table, staging each file it edits -- a difference the item's ruling keeps moves instead into that table's deliberate dict, 33-10's companion dict (`DELIBERATE` beside `VALUE_KNOWN` in test/value_truth_known.py; `ABBREV_DELIBERATE`, `SCALE_FRAME_DELIBERATE`, `BY_POSITION_DELIBERATE`, `BY_TYPES_DELIBERATE`, `COLORVAR_DELIBERATE` and `STAT_COMBOS_DELIBERATE` beside `ABBREV_KNOWN`, `SCALE_FRAME_KNOWN`, `BY_POSITION_KNOWN`, `BY_TYPES_KNOWN`, `COLORVAR_KNOWN` and `STAT_COMBOS_KNOWN`), as `"<key>": "<ruling id>: <what is kept>"`, the ruling id a DECISIONS or index id (P4-n, A-n, Q-n, M-n) -- then run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`), which passes; (3) run the corpus guard block (test/test_wp33_truth.cscript with `WP33_ONLY=S09`, through BRIEF's two-line driver) and, if Q3309-1 reports any change for a guard example (an improved verdict or a changed field), regenerate the guard fixture with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s09 $WT/scripts/extract_corpus_guard_truth.do` (33-09), `git -C $WT add -f test/fixtures/corpus_guard_truth.json`, rerun the S09 block (Q3309-1 PASS) and add `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)` to the commit body; (4) pull from local main (CLAUDE.md rule 4): `git -C $WT pull --ff-only . main` (a no-op when the batch base already contains main); if it refuses, stop and report to the orchestrator, never a merge commit on a section branch; (5) run `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a `partial` or `truncated` result is run again) and name HIGH, CRITICAL or UNKNOWN risk in the hand-back; (6) grep the message for claude|anthropic before and after committing.
- **Commit-body lines:** `Regression: test/test_help_claims_p16.py::TestTypoParagraph::test_titel_is_refused -- failed at <base sha> with <text>`; `Flipped: <node> -- it read a sentence that was false because <why>`; `BUGS.md: "<title>" (closed)`; `GAPS4: LT-27 Tracked`.
