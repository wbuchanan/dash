# Section 44-05: Lone second-axis gridlines; non-numbers in label lists refused

> Part of: WP-44 (Axes, audit package 9) · Items: MS-12, DG-9 · Risk: green · Batch: 44.1 · Depends on: none · Blocks: none · Tasks: 5, 2 commits · Case-id prefix: Q4405

## Overview

**What is wrong today.**

- **MS-12.** "A graph whose only plot is on yaxis(2) is drawn with y gridlines; twoway draws none" (audit :476). `_dash_lone_second_axes` (dash_render.py:5003-5050; both loaders call it, :62129 saved, :66845 served) renumbers the lone axis to 1 and moves dash's internal keys `ytitle2`/`ylabel2`/`yscale2` (what `_dash_route_axis2` makes of `ytitle(..., axis(2))`, `ylabel(..., axis(2))` and `yscale(..., axis(2))`; they are not typed options -- twoway has none, and dash refuses them typed, P4-7) onto the first axis, so the axis takes axis 1's default look, grid included. twoway gives axis 2 and higher the `vertical_nogrid` axis style (twowaygraph_g.class `create_axes`: `local axlook = cond(\`m'==1, "vertical_default", "vertical_nogrid")`); `scatter mpg weight, yaxis(2)` and `pci 20 3000 30 4000, yaxis(2)` draw one left axis and no #EAF2F3 gridline (E14, C10; appendix :3231).
- **DG-9 (TR-8).** "A non-number in a label list (.a, a bare word) is noted and drawn; twoway refuses 'invalid label specifier'" (audit :494). `_dash_axlabel_refusal` (dash_parse.mata:2326-2396, called at dash.ado:8776-8782) refuses a label with no value, a second rule and an unfinished rule; a bare word or `.a` falls through to the renderer, which names it ("xlabel() sub-option(s) not implemented and ignored: .a") and draws. twoway: `xlabel(1/5 .a, valuelabel)` is r(198) "invalid label specifier, :  1/5 .a:" (T11); `xlabel(abc)`, `ylabel(abc)`, `xtick(abc)`, `ytick(abc)`, `xmlabel(abc)`, `ymlabel(abc)`, `xmtick(abc)`, `ymtick(abc)` are r(198) "invalid label specifier, : abc:" (value_truth.json `xlabel_1` and the seven rows after it). The minor options are not in dash's refusal loop at all. dash.sthlp:4522-4523 documents the note ("a word that is no value, form, rule or label is named in the note"), contradicting :1134 ("A value is refused where twoway refuses it").

**After this section**, in both modes: a graph drawn on a lone second (or third..ninth) axis has that axis's default look -- no gridlines unless asked; and every label or tick option refuses a list word twoway refuses, with twoway's rc and words, before anything is drawn.

**Why one section.** Both are small, independent axis fixes the index groups as 44-05 (owner of `_dash_lone_second_axes` and `_dash_axlabel_refusal`); they share no code with each other and none with 44-01 or 44-04.

**Test order and commit rule.** Two commits `(WP-44 MS-12)` then `(WP-44 DG-9)`. 44-05-01 writes the extract script (both items), runs it, and writes only MS-12's failing tests and block; saved failure; no commit. 44-05-02 fixes MS-12 and commits. 44-05-03 writes DG-9's failing cases (saved, no commit); 44-05-04 fixes and commits. 44-05-05 checks the section.

### Section decisions (binding on the executor)

- **D-44-05.a The lone axis keeps its own number's look.** `_dash_lone_second_axes`, when it renumbers a lone y axis `k >= 2` (or x axis), also writes `graph_options["_dash_lone_from"] = {"y": k}` (`{"x": k}`; both when both move; an int, never user text) on the returned copy. New module function `_dash_lone_axis_look(fig, graph_opts, scheme=None)` turns the grid of that dimension off (`for g in (fig.ygrid or fig.xgrid): g.grid_line_color = None`) when the scheme's axis style for an axis numbered `k` draws no major grid -- `vertical_nogrid` / `horizontal_nogrid` (`style/axisstyle-vertical_nogrid.style`: `set draw_major_grid no`; every shipped scheme names these for `k >= 2`); it is called as the FIRST statement of `_dash_apply_axis_options` (dash_render.py:45217; both modes call it after the scheme is applied), before that function reads `ylabel()`'s `grid`/`nogrid`, so the user's `ylabel(, grid axis(2))` -- routed to dash's internal key `ylabel2` by `_dash_route_axis2`, then moved to `ylabel` by `_dash_lone_second_axes` -- still draws the grid, as twoway's `ylabel(, grid axis(2))` does (the fixture's `ms12.y2_grid` probe confirms). `ylabel2` here is dash's internal key after the axis(2) route, never a typed option: twoway has no `ylabel2()`, and dash refuses it as typed since 35-07 (P4-7). This keeps `_make_figure_body` and the served template untouched (R12: 44-04 is batch 44.1's editor of both). The x dimension follows the fixture (`ms12.x2`); under schemes whose x axis draws no grid by default nothing changes.
- **D-44-05.b A list word is a position, a rule or a label, else refused.** `_dash_axlabel_refusal`'s word loop (dash_parse.mata:2369-2393) refuses (returns `rest`, the head after the leading rule, as today) a word that is none of: a number (`strtoreal(t) < .`), a whole rule (`_dash_axlabel_rule(t)`), a numlist range `a/b` with both sides numbers, a quoted label (handled above), or one of the forms the fixture's `dg9.accept_*` probes show twoway drawing (candidates measured: `.` alone, `-5`, `1e3`, `+2`, `td(1jan1980)`, `tm(1980m1)`, `1(1)5`, `1[1]5`, `-1/1`). The pseudo-function test is by name: the fixture's accepted names only (`td tc tC tw tm tq th ty` measured), with a parenthesis pair after them; anything else -- `.a` .. `.z`, a bare word, `abc(1)` -- is refused. dash.ado's loop (:8776) gains the minor options `xmlabel ymlabel xmtick ymtick xmlabel2 ymlabel2 xmtick2 ymtick2` (and `tlabel ttick tmlabel tmtick` are NOT added: their words are dates, read by `_dash_tdate_*`; the fixture's `dg9.tlabel_abc` probe records what twoway prints and, if it differs from dash today, the case is named in the hand-back for 49-01, which owns t-axis words, DG-10). The printed line stays `invalid label specifier, :  <part>:` with the two blanks twoway writes (T11), exit 198.

## Risk: [green] -- one marker key read after the scheme, and one extra branch in a Mata refusal

**Why.** The lone-axis rule touches only graphs with no layer on axis 1; the refusal adds a branch for words that today reach a note.

**Risk factors.**
1. A spec key with a leading underscore must survive the served app's spec copy and the parity profile.
2. A valid label word the fixture did not probe (e.g. a `%td`-style literal on a date axis typed in `xlabel()`) would now be refused.
3. Pinned tests: test_dual_axis.py's lone-axis tests, test_axis_order_d9b.py, test_axisn_minor.py (:235) read `_dash_lone_second_axes`'s output; value_truth comparisons (33-10's probe-by-probe test) read the xlabel rows.

**Mitigation.**
1. `TestLoneAxisGrid::test_served_reads_the_marker` renders served and saved.
2. On a date axis dash's x options already refuse date literals (`_dash_taxis_fold`, dash.ado's t-option fold); 44-05-03 runs taxis_truth.json and axis_look_truth.json `ref_*` probes through the new rule (Q4405-3) before the fix lands.
3. The three files are run in each task; 33-10's value_truth test flips from "documented difference" to equal for the eight xlabel rows (its eight `VALUE_KNOWN` rows in test/value_truth_known.py are deleted by DG-9's known-differences step, D-33-10.h).

## Dependencies

- **Depends on:** none in WP-44. 33-10 (TR-11, value_truth compared probe by probe) landed in WP-33; its exemption list holds the eight rows this section closes.
- **Blocks:** none.
- **Parallel batch 44.1** with 44-01 and 44-04 (merge order 44-01, 44-04, 44-05). 44-01 adds a call at the END of `_dash_apply_axis_options`, 44-05 one at its START: two hunks of one function (not an R12 hot function) -- the merger keeps both. Neither edits `_make_figure_body` or the served template (44-04's, R12).

## Evidence

Anchors at `090d928`; re-read at the WP-44 base.

```python
5003 def _dash_lone_second_axes(spec):
5004     """The spec with a graph's lone second axis drawn as its only axis.
...
5011     layers (BUGS.md).  So when no layer of a graph is on the first axis of
5012     a side, its layers lose the yaxis(2)/xaxis(2) option and ytitle2(),
5013     ylabel2() and yscale2() (xtitle2() ...) become ytitle(), ylabel() and
5014     yscale() -- where one is given, it wins -- and both modes draw the one
5015     axis as they draw any first axis.
```

```
2385         else {
2386             p1 = strpos(t, "(")
2387             p2 = strpos(t, "[")
2388             // Only a number-led word is a rule: td(1jan2000) is a date.
2389             if ((p1 | p2) & (strtoreal(substr(t, 1, 1)) < . |
2390                 c == "-" | c == "+" | c == ".") & !_dash_axlabel_rule(t)) bad = 1
2391             prev = 1
2392         }
```

```
8776     foreach _alo in xlabel ylabel xtick ytick xlabel2 ylabel2 xtick2 ytick2 {
8777         mata: st_local("_alr", _dash_axlabel_refusal(st_local("g_`_alo'")))
8778         if `"`macval(_alr)'"' != "" {
8779             mata: _dash_say("err", "invalid label specifier, :  ", st_local("_alr"), ":")
8780             exit 198
```

Stata: twowaygraph_g.class `create_axes` (`axlook` line, after :851); `/Applications/StataNow/ado/base/style/axisstyle-vertical_nogrid.style`. Fixtures: value_truth.json `xlabel_1` .. (eight `invalid label specifier` rows), axis_look_truth.json `ref_*`.

### Tests that pin today's behaviour (flip, never delete)

- `grep -rn "named in the note\|not implemented and ignored" test/test_axis*.py test/test_help_claims_*.py | grep -i "label\|abc\|\.a"` -- any test asserting a bare word in a label list is noted (DG-9).
- The help-claim pin of dash.sthlp:4522-4523 (`grep -rn "no value, form, rule or label" test/`).
- 33-10's value_truth exemption list (the eight `xlabel_*` rows of `VALUE_KNOWN`, test/value_truth_known.py) -- deleted by DG-9's known-differences step (D-33-10.h).
- Lone-axis tests asserting a visible y grid: `grep -rn "grid_line_color" test/test_dual_axis.py test/test_axis_order_d9b.py`.

## User stories

- **US-44-05.1** As a Stata user who draws one series on `yaxis(2)`, I want the axis without gridlines, as twoway draws it.
- **US-44-05.2** As a Stata user who mistyped a label list, I want twoway's refusal, not a drawn graph and a note, so my do-file fails where twoway's does.

## Business requirements

- **BR-44-05.1** A graph whose every layer is on axis k >= 2 draws that axis without gridlines unless the user asked for them; a graph with a layer on axis 1 is unchanged.
- **BR-44-05.2** Every label/tick option (major and minor) refuses each fixture word twoway refuses, r(198), with twoway's words; every word twoway draws is still drawn.
- **BR-44-05.3** Saved page and served app agree.

## Technical requirements

- **TR-44-05.1** `_dash_lone_second_axes` writes `_dash_lone_from` (D-44-05.a); `_dash_lone_axis_look(fig, graph_opts, scheme=None)` new module function after `_dash_lone_second_axes`, called first in `_dash_apply_axis_options`; copy list (R2): the function after `"_dash_lone_second_axes"` in the functions tuple (grep it); function_test_map.py row -> `test/test_axis_misc_p9.py::TestLoneAxisGrid`.
- **TR-44-05.2** Mata: the word rule in `_dash_axlabel_refusal` (D-44-05.b) with the accepted pseudo-function names as a literal rowvector `("td", "tc", "tC", "tw", "tm", "tq", "th", "ty")` cut to the fixture's set; dash.ado's loop list gains the eight minor option names. program_coverage_map.py's `_dash_axlabel_refusal` row gains `test_option_validation.cscript:Q4405-2`.
- **TR-44-05.3** Parity (R8) `CORPUS` under `# WP-44 44-05`: `"lone yaxis(2) no grid"`, `"lone yaxis(2) ylabel axis(2) grid"` (command `scatter mpg weight, yaxis(2) ylabel(, grid axis(2))`, the `ms12.y2_grid` probe), `"pci lone yaxis(2)"`.
- **TR-44-05.4** Help (R3): dash.sthlp:4522-4523's sentence becomes "a word that is no value, form, rule or label is refused as twoway refuses it, invalid label specifier, r(198)"; the lone-axis paragraph (grep `lone` / `every layer is on yaxis(2)` in dash.sthlp) gains "and draws it with that axis's default look: no gridlines, as twoway draws a second axis".

## Boundaries

- Do not touch `_dash_axlabel_refusal`'s rule and label checks beyond the word branch, the custom refusal 44-02 adds after it (batch 44.2), the axis titles (44-01), date readers (44-04).
- t-axis option words belong to `_dash_tdate_*` (44-04) and their messages to 49-01 (DG-10).

## Stata truth

New `scripts/extract_axis_misc_truth.do` -> `test/fixtures/axis_misc_truth.json` (frame of `scripts/extract_axis_look_truth.do`; per key rc, log lines, SVG lines with stroke). Keys:
- `ms12.*`: `y2` (`scatter mpg weight, yaxis(2)`), `pci_y2` (`pci 20 3000 30 4000, yaxis(2)`), `y2_grid` (`scatter mpg weight, yaxis(2) ylabel(, grid axis(2))`), `y3` (`scatter mpg weight, yaxis(3)`), `x2` (`scatter mpg weight, xaxis(2)`), `y2_s2color` and `y2_stcolor` (the y2 command under each scheme), `control` (`scatter mpg weight`).
- `dg9.*`: `T11` (`scatter mpg rep78, xlabel(1/5 .a, valuelabel)`), `abc_<opt>` for `xlabel ylabel xtick ytick xmlabel ymlabel xmtick ymtick` (`scatter mpg weight, <opt>(abc)`), `mid_word` (`ylabel(10 abc 20)`), `fn_word` (`ylabel(abc(1))`), `accept_<k>` for each candidate of D-44-05.b (on `scatter mpg weight` for numbers, on `sysuse sp500`'s `line close date` for the pseudo-functions), `tlabel_abc` (`line close date, tlabel(abc)`).

Run twice through `scripts/stata_slot.sh` with DASH_REPO; `git add -f`. Truth block in test_wp44_truth.cscript: `* ==== S05 MS-12: lone second axis without gridlines ====`, gate `WP44_ONLY`/`"S05"`; the DG-9 refusal cases go in test/test_option_validation.cscript (R1) as Q4405-2 and Q4405-3.

## TDD test stubs

New file `test/test_axis_misc_p9.py`:
- Test: a lone yaxis(2) draws no y grid -- ::TestLoneAxisGrid::test_no_grid[saved|served] (fails at base: grid #eaf2f3); ::test_grid_when_asked; ::test_pci_lone_axis; ::test_axis_one_unchanged; ::test_served_reads_the_marker.
- Test: the help sentence reads the refusal -- ::TestLabelWords::test_the_help_sentence.
- cscript cases: Q4405-1 (S05 block: y2, pci_y2 with no gridline in both modes; y2_grid with one), Q4405-2 (every `dg9.abc_*`, `T11`, `mid_word`, `fn_word` refused r(198) with the fixture's line), Q4405-3 (every `dg9.accept_*` and the axis_look_truth `ref_*` probes keep their recorded rc).
- Flips: Evidence list. Parity: TR-44-05.3.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| lone axis grid | pytest TestLoneAxisGrid; Q4405-1 | axis_misc_truth.json ms12.* | yes |
| label words refused | Q4405-2 (test_option_validation.cscript) | dg9.*, value_truth.json xlabel_* | Stata side |
| accepted words unchanged | Q4405-3 | dg9.accept_*, axis_look_truth.json ref_* | Stata side |
| parity | test_mode_parity.py | -- | yes |

Acceptance criteria:
- **AC-44-05.1** `ms12.y2`, `pci_y2`, `y3` draw no y gridline in both modes; `y2_grid` and `control` draw them.
- **AC-44-05.2** Every `dg9` refusal probe gives twoway's rc and line; every accept probe draws; 33-10's value_truth comparison passes for the eight rows without exemption.

## Tasks

**Commit boundary.** MS-12: 44-05-01 (no commit) + 44-05-02 (commit `Draw a lone second axis without gridlines (WP-44 MS-12)`). DG-9: 44-05-03 (no commit) + 44-05-04 (commit `Refuse non-number words in axis label lists (WP-44 DG-9)`). 44-05-05 is the section check. Branch `wp44-s05`; `$WT` and the closing steps every closing task takes before its commit are in Notes ("Before every commit").

```xml
<task type="auto" id="44-05-01">
  <name>Measure; write MS-12 failing tests</name>
  <files>scripts/extract_axis_misc_truth.do, test/test_axis_misc_p9.py, test/test_wp44_truth.cscript</files>
  <action><![CDATA[Create scripts/extract_axis_misc_truth.do with every key of "Stata truth", run it twice through scripts/stata_slot.sh with DASH_REPO set, git add -f test/fixtures/axis_misc_truth.json (staged). Create test/test_axis_misc_p9.py with TestLoneAxisGrid and append "* ==== S05 MS-12: lone second axis without gridlines ====" (Q4405-1). Run on the unmodified tree; save to <scratch>/44-05-01-failure.txt.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_axis_misc_p9.py::TestLoneAxisGrid -q -n0 -> test_no_grid and test_pci_lone_axis fail ('#eaf2f3' is not None); test_axis_one_unchanged passes; Q4405-1 FAIL]]></verify>
  <done>The fixture exists and MS-12's tests fail on the unmodified tree.</done>
</task>

<task type="auto" id="44-05-02">
  <name>Keep a lone axis's own look</name>
  <files>dash_render.py, dash.sthlp, test/test_mode_parity.py</files>
  <action><![CDATA[Implement D-44-05.a (TR-44-05.1): the marker in _dash_lone_second_axes, _dash_lone_axis_look called as the first statement of _dash_apply_axis_options (both modes), copy list, map row, parity entries in test/test_mode_parity.py. Flip lone-axis pins asserting a visible grid. Add the help sentence (TR-44-05.4, lone-axis paragraph). Close MS-12 (BUGS closed form naming TestLoneAxisGrid and Q4405-1; GAPS4 Closed, commit pending; delete MS-12's GAPS4_OPEN line in test/test_tracking_documents.py; CHANGELOG under "### Fixed in WP-44"; TWOWAY_COVERAGE_AUDIT.md: grep `yaxis(2)` and the second-axis row, which gains "[WP-44 MS-12: corrected -- a lone second axis drawn without gridlines]", or the commit body says no row names it); take the three closing steps for `MS-12` (Notes, "Before every commit" (1)-(3)): (1) delete the plain `MS-12` rows of scripts/corpus/ledger.tsv, run `python3 scripts/corpus/ledger.py` and `git add -f test/fixtures/corpus_ledger.json`; (2) run `python3 test/known_differences.py MS-12`, delete each `<file>:<line>` row it prints or move a difference its ruling keeps into that table's deliberate dict, and run the hygiene command it prints; (3) run block S09 alone (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example, regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do through scripts/stata_slot.sh and `git add -f` it; then the pull `cd $WT && git pull --ff-only . main`, detect-changes and the message grep (Notes (4)-(6)); run TestLoneAxisGrid, test_dual_axis.py, test_axis_order_d9b.py, test_axisn_minor.py, test_tracking_documents.py, the block; commit.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_axis_misc_p9.py test/test_dual_axis.py test/test_axis_order_d9b.py test/test_axisn_minor.py test/test_tracking_documents.py test/test_corpus_ledger.py -q -n0 -> pass; "Q4405-1 PASS"; python3 test/known_differences.py MS-12 -> no `<file>:<line>` row, and the hygiene command it prints -> pass; WP33_ONLY=S09 -> "Q3309-1 PASS"; subject ends "(WP-44 MS-12)"; git log -1 --format=%B | grep -ci 'claude\|anthropic' -> 0]]></verify>
  <done>A lone second axis draws without gridlines in both modes and MS-12 is committed.</done>
</task>

<task type="auto" id="44-05-03">
  <name>Write DG-9 failing cases</name>
  <files>test/test_option_validation.cscript, test/test_axis_misc_p9.py</files>
  <action><![CDATA[Add cases Q4405-2 and Q4405-3 to test/test_option_validation.cscript under a comment header naming WP-44 DG-9 (each case: capture noisily dash <command>; compare _rc and the first error line with the fixture key's rc and message; for accept probes compare rc only), and TestLabelWords::test_the_help_sentence (reads the rewritten sentence; fails now). Run the cscript through a two-line driver on the tree as 44-05-02 left it; save to <scratch>/44-05-03-failure.txt.]]></action>
  <verify><![CDATA[the cscript log shows Q4405-2 FAIL lines (rc 0 where twoway gives 198) and Q4405-3 PASS; python3 -m pytest test/test_axis_misc_p9.py::TestLabelWords -q -n0 -> fails]]></verify>
  <done>DG-9's regression cases fail before the fix and the accepted forms are pinned.</done>
</task>

<task type="auto" id="44-05-04">
  <name>Refuse non-number label words</name>
  <files>dash_parse.mata, dash.ado, dash.sthlp</files>
  <action><![CDATA[Implement D-44-05.b (TR-44-05.2): the word branch of _dash_axlabel_refusal and the eight minor options in dash.ado's loop. Rewrite dash.sthlp:4522-4523 (TR-44-05.4). 33-10's value_truth exemption list -- the eight `xlabel_*` rows of `VALUE_KNOWN` in test/value_truth_known.py -- goes in the known-differences step below: `python3 test/known_differences.py DG-9` prints them and each is deleted (if 33-10's rule keyed one under another id, `python3 test/known_differences.py <that id>` prints it and it is deleted too, named in the commit body; D-33-10.h); a count pin over `VALUE_KNOWN` that moves gets `# old -> new: WP-44 DG-9 refuses them as twoway does` (R10). Flip the pins found by the Evidence grep. CHANGELOG under "### Changed behaviour (may need your do-files changed)" (a drawn form is now refused). Close DG-9 (BUGS names TR-8; GAPS4 Closed; GAPS4_OPEN line deleted in test/test_tracking_documents.py; TWOWAY_COVERAGE_AUDIT.md's axis-label row gains "[WP-44 DG-9: corrected -- a non-number in a label list refused as twoway refuses it]"); take the three closing steps for `DG-9` (Notes, "Before every commit" (1)-(3)): (1) delete the plain `DG-9` rows of scripts/corpus/ledger.tsv, run `python3 scripts/corpus/ledger.py` and `git add -f test/fixtures/corpus_ledger.json`; (2) run `python3 test/known_differences.py DG-9`, delete each `<file>:<line>` row it prints or move a difference its ruling keeps into that table's deliberate dict, and run the hygiene command it prints; (3) run block S09 alone (`WP33_ONLY=S09`) and, if Q3309-1 reports any change for a guard example, regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do through scripts/stata_slot.sh and `git add -f` it; then the pull `cd $WT && git pull --ff-only . main`, detect-changes and the message grep (Notes (4)-(6)); run test_option_validation.cscript, test_axis_look_options.py, test_axis_options.py, test_option_validation.py, TestLabelWords, test_program_coverage_map.py, test_tracking_documents.py; commit.]]></action>
  <verify><![CDATA[test_option_validation.cscript -> "Q4405-2 PASS", "Q4405-3 PASS", ALL CHECKS PASSED; python3 -m pytest test/test_axis_misc_p9.py test/test_option_validation.py test/test_axis_options.py test/test_tracking_documents.py test/test_corpus_ledger.py -q -n0 -> pass; python3 test/known_differences.py DG-9 -> no `<file>:<line>` row, and the hygiene command it prints -> pass; WP33_ONLY=S09 -> "Q3309-1 PASS"; subject ends "(WP-44 DG-9)"]]></verify>
  <done>Label-list words twoway refuses are refused in its words and DG-9 is committed.</done>
</task>

<task type="auto" id="44-05-05">
  <name>Check the section end to end</name>
  <files>none</files>
  <action><![CDATA[Run the section's tests, the S05 block, test_option_validation.cscript, test_mode_parity.py -k "44-05", test_help_conformance.py, test_statistical_helpers.py::TestTheServedAppCarriesEveryName, test_function_test_map.py, test_tracking_documents.py; grep both commit messages for claude|anthropic. If dg9.tlabel_abc differs from dash, write it to <scratch>/44-05-handback.txt for 49-01.]]></action>
  <verify><![CDATA[all pass; grep count 0]]></verify>
  <done>Both commits are green together and any t-axis word difference is handed on.</done>
</task>
```

## Section completion criteria

- Two commits `(WP-44 MS-12)`, `(WP-44 DG-9)` with failure texts, flips, tracking edits and the three closing steps (Notes: plain rows of scripts/corpus/ledger.tsv removed, corpus_ledger.json regenerated; `python3 test/known_differences.py <id>` printing no row -- DG-9's eight `VALUE_KNOWN` rows gone -- and every table's `test_every_known_difference_is_open` green; S09's Q3309-1 PASS, the guard fixture regenerated and committed with the item whenever Q3309-1 reported a change); `axis_misc_truth.json` committed and named by a test.
- Q4405-1..3 pass; parity entries agree.

## Notes

- **Traps.** (1) `_dash_lone_second_axes` returns a NEW dict; write the marker on the copy it returns, never on the caller's. (2) The grid rule is the first statement of `_dash_apply_axis_options`; do not move it after the function's grid handling, or `ylabel(, grid)` would be undone. (3) In the Mata word branch, a leading `-` or `+` followed by digits is a number (`strtoreal`), and `-1/1` is a range: test the range before refusing. (4) The part named in the refusal is the head after the leading rule (today's `rest`), with two blanks after the colon.
- **Help paragraphs this section owns (R3):** dash.sthlp:4522-4523 sentence; the lone-axis sentence.
- **Merge rules touched:** R1, R2, R3, R5, R6 (Mata function extended), R8, R9, R10 (a count pin over 33-10's `VALUE_KNOWN` that the deletion moves, if any).
- **Before every commit (BRIEF; CLAUDE.md rules 4 and 6; R13).** `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp44-s05` (BRIEF "Pull form"): every path and command below runs in it. Every closing task (44-05-02, 44-05-04) takes **the three closing steps** after its tracking edits and before its commit, in this order, whether the item closes `Closed` or `Documented` (BRIEF "The corpus ledger and the known-differences tables" (1)-(3); D-33-05.i, D-33-10.a, D-33-10.h, D-33-09.c; A-10): **(1) the ledger step** -- delete every row of `scripts/corpus/ledger.tsv` whose `gaps4_id` is the item's plain lead id (`MS-12`, `DG-9`), keep every `<id> (documented)` and `<id> (residual)` row, run `python3 scripts/corpus/ledger.py` (no `--run`: the fixture's `_meta` is kept), `git add -f test/fixtures/corpus_ledger.json`, and run `python3 -m pytest test/test_corpus_ledger.py test/test_tracking_documents.py -q -n0` in the task's verify; **(2) the known-differences step** -- run `python3 test/known_differences.py <lead id>` (33-10, D-33-10.h) and delete every `<file>:<line>` row it prints (a `*_KNOWN` row whose value is exactly the lead id; `(documented)` and `(residual)` rows are not printed and stay), except that a difference the item's ruling keeps moves into that table's deliberate dict -- the companion dict 33-10 names for it: `DELIBERATE` for `VALUE_KNOWN` (test/value_truth_known.py), `ABBREV_DELIBERATE` for `ABBREV_KNOWN` (test/test_abbreviations.py), and `<NAME>_DELIBERATE` beside every other `<NAME>_KNOWN` (`SCALE_FRAME_DELIBERATE` in test/scale_frame_known.py, `BY_POSITION_DELIBERATE` in test/test_by_text.py, `BY_TYPES_DELIBERATE` in test/test_by_types.py, `STAT_COMBOS_DELIBERATE` in test/test_statistical_truth.py, `COLORVAR_DELIBERATE` in test/test_colorvar_truth.py) -- written `"<key>": "<ruling id>: <what is kept>"` with a DECISIONS or index ruling id (P4-n, A-n, Q-n, M-n) (none is expected here: both items close `Closed` and no ruling keeps a difference of MS-12 or DG-9 -- DG-9's eight `xlabel_*` rows of `VALUE_KNOWN` in test/value_truth_known.py now agree with twoway and are deleted; a row the executor would keep without a ruling id is reported to the orchestrator, not moved); then run the hygiene command it prints (`python3 -m pytest <the files defining test_every_known_difference_is_open> -q -n0 -k every_known_difference_is_open`) in the task's verify; **(3) the guard step** -- run block S09 of test/test_wp33_truth.cscript alone (`WP33_ONLY=S09`, BRIEF's two-line driver with `<repo>` = `$WT`); if 33-09's guard check Q3309-1 reports any change for a guard example -- an improved verdict (`<id> improved from ...`) or a changed field (`<id>: <field> was <old> now <new>`) -- regenerate `test/fixtures/corpus_guard_truth.json` with its extract script (`DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s09 $WT/scripts/extract_corpus_guard_truth.do`), `git add -f` it, rerun S09 to its `Q3309-1 PASS` and commit it with the item (body line `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)`). Then, before the commit: (4) `cd $WT && git pull --ff-only . main` (BRIEF "Pull form"; CLAUDE.md rule 4; a no-op when the batch base already contains main -- if it refuses because main moved, stop and report to the orchestrator, never make a merge commit). (5) Run `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a `partial` or `truncated` result is re-run) and report HIGH/CRITICAL or UNKNOWN risk in the hand-back. (6) Grep the message for claude|anthropic before and after committing.
- **Commit-body lines:** `Regression: test/test_axis_misc_p9.py::TestLoneAxisGrid::test_no_grid -- failed at <base sha> with <text>`; `Flipped: <node> -- a grid on a lone axis 2 was wrong because twoway draws axis 2 in vertical_nogrid`; `Fixture: test/fixtures/axis_misc_truth.json (scripts/extract_axis_misc_truth.do)`; `Fixture: test/fixtures/corpus_ledger.json (scripts/corpus/ledger.py)` (every commit; plus `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)` when Q3309-1 reported a change); `BUGS.md: "<title>" (closed)`; `GAPS4: MS-12 Tracked`.
