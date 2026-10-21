# Section 35-01: Repeated options taken rightmost

> Part of: WP-35 (Accepted syntax and refusals) · Items: MS-1 (other ids stat:PT-3) · Risk: yellow · Batch: 35.1 · Depends on: none · Blocks: 35-03 · Tasks: 3, 1 commit · Case-id prefix: Q3501

## Overview

**What is wrong today.** The audit (package 11, MS-1, stat:PT-3): "Repeated options twoway takes rightmost are refused r(198): yvarlabel, xvarlabel, mlabprefix, mlabsuffix, lalign, mlabstyle (and yvarl) given twice, and repeated contour levels(), ccuts(), ccolors(), clabels(), format(), scolor/ecolor/crule/interp, clwidths/clpatterns". Measured by the audit: `scatter mpg weight, yvarlabel("Q") yvarlabel("R")` is rc 0 in twoway and draws the title R; dash gives `option yvarlabel() not allowed`, r(198). `contour ..., levels(5) levels(6)` is rc 0 in twoway (twoway_zyx2view_parse.class:61-62, 89-106: `_parse combop ... rightmost` for every contour option) and r(198) in dash. Repeated contour flags (minmax, reversekey, outlines, heatmap, colorlines) are refused by both, and must stay refused.

**Why.** Both helpers that read options the plot parser's `syntax` has no room for -- `_dash_label_split` (dash.ado:2517-2563) and `_dash_contour_split` (dash.ado:2447-2497) -- try each top-level token alone, collect every token that parsed, and then run ONE combined `syntax` over all of them (dash.ado:2551-2553 and :2487-2491). `syntax` refuses an option given twice, so the second copy kills the command. `_dash_opts_repeats` (dash.ado:10923), which applies twoway's rightmost rule elsewhere, never sees these options because they are taken out of the text first.

**After this section.** Each helper keeps only the LAST copy of each valued option (resolved by the option it binds to, so `yvarlabel("Q") yvarl("R")` is two copies of one option) before its combined `syntax`; flags keep every copy, so a repeated contour flag is still refused in `syntax`'s words, as twoway refuses it. The two helpers share one Mata function that picks the copies to keep. Both items share this section because they are the same defect in two sibling helpers; stat:PT-3 is an other id of MS-1 (Appendix A), so there is one commit.

**Test order and commit rule.** 35-01-01 runs GitNexus impact on the functions it edits, writes the regression tests (one pytest node and the S01 truth block), runs them on the unmodified tree, saves the failure text and does not commit. 35-01-02 makes the fix and turns them green. 35-01-03 updates help, tracking and CHANGELOG and makes the one commit `(WP-35 MS-1)`.

### Section decisions

- **D-35-01.a Which copy is kept.** The last token (in typed order) that `capture syntax` binds to a given option is kept; earlier tokens binding to the same option are dropped before the combined `syntax`. Tokens bound to a flag (`MINMAX`, `REVersekey`, `HEATMAP`, `OUTlines`, `COLORLINES`; `TABLE` keeps its existing second-copy rule) are all kept, so `syntax` refuses a repeated flag as today.
- **D-35-01.b One Mata helper.** `real rowvector _dash_rightmost_keep(string rowvector names, string scalar flags)`: for token i with option name `names[i]` ("" = token not bound), returns 1 when `names[i] == ""` (the caller decides), when `names[i]` is in the blank-separated `flags`, or when no later token j > i has `names[j] == names[i]`; else 0. No user text is expanded; names are option names the helper itself wrote.
- **D-35-01.c No note.** A dropped earlier copy is silent: twoway draws the last copy and prints nothing.

## Risk: [yellow] -- two parsing helpers every plot command passes through

**Why.** `_dash_label_split` and `_dash_contour_split` run inside `_dash_parse_plot_opts` (called from dash.ado:1237 and :1240) for every plot of every command; a mistake here breaks option parsing everywhere.

**Risk factors.** 1. The token loops read the user's text by value through Mata globals (`_dash_lb_tok`, `_dash_zyx_tok`); a copy through compound quotes would expand macros again (JSE-69). 2. Both helpers `c_local` their results; an option emptied by the drop must still be `c_local`ed as "". 3. 35-03 (batch 35.2) extends `_dash_label_split`'s syntax (subchar) after this lands.

**Mitigation.** 1. The keep mask is computed in Mata from option names only; the kept tokens are joined in Mata exactly as today. 2. The `foreach o of local lo { c_local ... }` blocks are unchanged. 3. 35-03 depends on this section (index).

## Dependencies

- **Depends on:** none (W0 has created `test/test_wp35_truth.cscript`).
- **Blocks:** 35-03 (it adds `SUBChar()` to `_dash_label_split`'s declarations).
- **Parallel batch 35.1:** with 35-02 (graph-level p#(), `_dash_tw_takes_tab`, `_dash_plot`) and 35-09 (`_dash_expand_plottype`, `_dash_split_groups`, `_dash_split_segs`, `_make_figure_body` empty branch). This section touches none of those.

## Evidence

Anchors at `090d928`; re-read before editing.

**`_dash_label_split`** (dash.ado:2517-2563). Declared options `lo "yvarlabel xvarlabel mlabprefix mlabsuffix lalign mlabstyle table table2"` (:2519); per-token loop (:2527-2547):

```stata
2530        capture syntax [, YVARLabel(string asis) XVARLabel(string asis) ///
2531            MLABPREfix(string asis) MLABSUFFix(string asis) LAlign(string) ///
2532            MLABSTyle(string asis) TABLE TABLE2(string asis) ]
...
2545        if `_rc_lb' mata: _dash_lb_out = _dash_lb_out + " " + _dash_lb_tok[`_li']
2546        else  mata: _dash_lb_in = _dash_lb_in + " " + _dash_lb_tok[`_li']
2548    mata: st_local("0", ", " + _dash_lb_in)
2549    syntax [, YVARLabel(string asis) ... TABLE TABLE2(string asis) ]
```

(Exact line numbers: re-read; [C] §5 P11 cites :2531-2547 for the loop and :2551-2553 for the combined syntax.)

**`_dash_contour_split`** (dash.ado:2447-2497). `zo` list (:2457), per-token `capture syntax` (:2477-2481), the in/out join (:2482-2483), combined `syntax` (:2486-2490). Flags in the declaration: `MINMAX`, `REVersekey`, `HEATMAP`, `OUTlines`, `COLORLINES`.

**twoway's rule.** advanced_options.sthlp calls yvarlabel(), xvarlabel(), mlabprefix(), mlabsuffix() "rightmost"; twoway_zyx2view_parse.class:89-106 `_parse combop 0 : 0, option(<X>) rightmost` for each contour option; repeated flags are refused by its `syntax`.

**Measured truth.** Audit appendix MS-1 (runs run1 D11, run2 E06, run3 G01-G04/G06: twoway rc 0, the last copy drawn -- title R, labels `<AMC Concord`, `AMC Concord>`) and stat:PT-3 (run3 #101-#104, #117-#119; probe2 #76, #77, #79-#81, #103, #104). No committed fixture holds these; this section measures them live in its truth block (twoway beside dash, SVG checksums), so no extract script is needed.

**Existing tests that pin today's behaviour.** None asserts the refusal (the audit: "Not in BUGS.md ... and not in TP-14a"). Guard tests that must stay green: test/test_twoway_option_parity.cscript TP-14a (:1683-1820, 39 rows) and TP-14b; test/test_json_escaping.cscript JSE-69 (by-value reads); test/test_parser.cscript U26-12.

## User stories

- **US-35-01.1** As a Stata user with an existing twoway command, I want `scatter mpg weight, yvarlabel("Q") yvarlabel("R")` to draw with the title R, as twoway does, so a do-file that builds its options in pieces runs.
- **US-35-01.2** As that user, I want `contour depth northing easting, levels(5) levels(6)` to draw six levels, as twoway does.
- **US-35-01.3** As that user, I want `contour ..., minmax minmax` still refused with twoway's words, so dash refuses what twoway refuses.

## Business requirements

- **BR-35-01.1** Each of yvarlabel(), xvarlabel(), mlabprefix(), mlabsuffix(), lalign(), mlabstyle() given twice (in any spelling twoway takes, yvarl() included) draws what the last copy alone draws; nothing is printed.
- **BR-35-01.2** Each valued contour option (levels(), ccuts(), ccolors(), clabels(), format(), scolor(), ecolor(), crule(), interp(), clwidths(), clpatterns()) given twice draws what the last copy alone draws.
- **BR-35-01.3** A contour flag given twice is refused with twoway's return code and first line.
- **BR-35-01.4** Saved and served pages agree (the registered spec is the same for the repeated form and its last-copy form, so both modes draw the same).

## Technical requirements

- **TR-35-01.1 `_dash_rightmost_keep`** (new, dash_parse.mata, placed directly above `_dash_opt_tokens`'s definition -- grep `_dash_opt_tokens(` for the line): signature and rule of D-35-01.b. Body: `real rowvector k; real scalar i, j, n; n = cols(names); k = J(1, n, 1); for (i = 1; i <= n; i++) { if (names[i] == "" | anyof(tokens(flags), names[i])) continue; for (j = i + 1; j <= n; j++) if (names[j] == names[i]) { k[i] = 0; break } }; return(k)`. Add its name on one new continuation line `        _dash_rightmost_keep ///` inserted directly after dash.ado:470 (the `        _dash_extract_filters _dash_extract_links _dash_extract_qual_vars _dash_extract_vars ///` line of the `_needed` list; re-read), touching no existing line of the list. The anchor is far from the other batch-35.1 edits of the list -- 35-02 inserts directly before its last line (`        _dash_abs_path _dash_graph_names ...`, :506) and 35-09 edits :485 and :492 -- because git's three-way merge conflicts on two insertions at one position and picks.sh does not union-merge dash.ado (R2-22). One new header-index entry `*!   _dash_rightmost_keep(names, flags)` with a two-line description, inserted directly after the `*!   _dash_opt_tokens(s)` entry's description (dash_parse.mata:107-110), touching no existing line (R6; 35-02's entries go after `_dash_stylelist_keys()`, :245). program_coverage_map.py: `"_dash_rightmost_keep": ("test_wp35_truth.cscript:Q3501-1",),` inserted directly after the `"_dash_opt_tokens": ...` row (:829), beside its name neighbours (the map groups rows by name), never at the end of the dict.
- **TR-35-01.2 `_dash_label_split`.** In the per-token loop, after `local _rc_lb = _rc` and the table rule, when `!_rc_lb`: set `local _lb_nm_`_li' ""`, then `foreach o in yvarlabel xvarlabel mlabprefix mlabsuffix lalign mlabstyle table table2 { if `: length local `o'' local _lb_nm_`_li' `o' }` (exactly one is non-empty after a one-token parse), and do NOT append to `_dash_lb_in` yet. After the loop, build a Mata row vector of the names (`mata: _dash_lb_nm = J(1, `_ln', "")` and one `mata: _dash_lb_nm[`_li'] = st_local("_lb_nm_`_li'")` per token; tokens refused by `capture syntax` keep ""), compute `mata: _dash_lb_keep = _dash_rightmost_keep(_dash_lb_nm, "table")`, then `forvalues _li = 1/`_ln'`: a token whose `_lb_nm_`_li'' is non-empty is appended to `_dash_lb_in` when `_dash_lb_keep[`_li']` is 1 and dropped otherwise; refused tokens go to `_dash_lb_out` as today (the existing order of `_dash_lb_out` is kept). Drop the new Mata globals in the existing `mata drop` line.
- **TR-35-01.3 `_dash_contour_split`.** The same change in its loop: names from `zo` (`foreach o of local zo`, with `heatmap`/`outlines` read from their own locals), flags string `"minmax reversekey heatmap outlines colorlines"`, Mata globals `_dash_zyx_nm`/`_dash_zyx_keep`, dropped at the end (`mata: mata drop _dash_zyx_nm _dash_zyx_keep`).
- **TR-35-01.4 If `_dash_opts_repeats` still refuses.** After TR-35-01.2/3, run Q3501-1. If any row still fails with `option <x>() not allowed` printed by `_dash_refuse_repeat` (dash.ado:11018), add the option's name to the rightmost list `_dash_rep_und_scan` reads in dash_parse.mata (grep the table's row for `yvarlabel`) with the comment `// WP-35 MS-1: rightmost, as twoway`. Record which branch was needed in `<scratch>/35-01-readings.txt`.
- **TR-35-01.5 Both modes.** No renderer change: the registered spec of a repeated form equals that of its last-copy form, and both renderers draw from the spec.
- **TR-35-01.6 Security.** User text is only moved between Mata string globals as today; option names compared in Mata are dash's own literals.

## Boundaries

- Do not touch `_dash_opts_repeats`'s logic beyond TR-35-01.4's one table row, `_dash_parse_plot_opts`'s syntax, `_dash_contour_check` (35-03, 35-04), `_dash_tw_takes_tab` (35-02), or any renderer file.
- Repeated GRAPH options and the merge of titles/legends are TP-14a's existing behaviour; unchanged.
- dash.sthlp: only the sentence named in Notes (R3).

## Stata truth

No extract script: measured live in the block. **Truth block** `* ==== S01 MS-1: repeated options taken rightmost ====` in `test/test_wp35_truth.cscript`, inserted directly above the first block whose S<MM> is higher than S01 (BRIEF Block order), or above `* ==== append new blocks above this line ====` if there is none, gated `local only : env WP35_ONLY` / `if inlist("`only'", "", "S01") & `: list posof "S01" in w35_run' {`, using the template's tally helpers (`_w35_expect id cond msg`, `_w35_done id msg`; re-read the scaffold W0 created for their exact names). A helper program `_s01_pair` (above the header) takes `id`, an R command and an E command (twoway syntax without the leading `twoway`), and: runs `capture graph drop _all`, `capture twoway <R>`, records rc; when 0 `graph export "<tmp>/s01_r.svg", replace` and `checksum`; the same for E; asserts both rc 0 and equal checksums (else the pair is wrong: FAIL naming the pair); then `capture noisily dash <R> name(s01r)` and `dash <E> name(s01e)` under a log, asserts both rc 0, `st_global("dash_json_s01r") == st_global("dash_json_s01e")` compared in Mata, and the log holds no `ignoring unsupported`.

- **Q3501-1** (auto): the seven label pairs -- `scatter mpg weight, yvarlabel("Q") yvarlabel("R")` / `scatter mpg weight, yvarlabel("R")`; the same for `xvarlabel`; `scatter mpg weight, mlabel(make) mlabprefix("[") mlabprefix("<")` / `... mlabprefix("<")`; `mlabsuffix(">")` likewise; `line mpg weight, sort lalign(inside) lalign(center)` / `line mpg weight, sort lalign(center)`; `scatter mpg weight, mlabel(make) mlabstyle(p1) mlabstyle(p2)` / `... mlabstyle(p2)`; `scatter mpg weight, yvarlabel("Q") yvarl("R")` / `scatter mpg weight, yvarlabel("R")`.
- **Q3501-2** (`sysuse sandstone, clear`): `contour depth northing easting, levels(5) levels(6)` / `levels(6)`; `ccuts(7600 7800) ccuts(7500 7700 7900)` / the second; `scolor(red) scolor(blue)`; `ecolor(red) ecolor(green)`; `crule(hue) crule(linear)`; `interp(none) interp(thinplatespline)`; `levels(3) ccolors(red green blue yellow) ccolors(navy maroon olive teal)`; `format(%9.0f) format(%9.2f)`; `contourline depth northing easting, clwidths(thin) clwidths(thick)`; `contourline ..., clpatterns(dash) clpatterns(solid)`; `contourline ..., ccuts(7600 7800) clabels(...)` twice -- clabels()'s pair is written from twoway_contourline.sthlp's syntax for clabels() (read it first); a pair whose E twoway refuses is a wrong probe: fix the probe, never the assertion.
- **Q3501-3** (sandstone): `contour depth northing easting, minmax minmax`, `reversekey reversekey`, `heatmap heatmap`, `outlines outlines`, `contourline depth northing easting, colorlines colorlines`: twoway's rc and first error line (captured with `capture noisily` under a log and read with `cert_file_has`-style reading of the first line after the command) equal dash's.

## TDD test stubs

Regression tests (fail at `090d928`):
- Test: `test/test_repeat_rightmost.py::TestTheHelper::test_the_helper_is_defined_and_needed` -- dash_parse.mata defines `real rowvector _dash_rightmost_keep(` and dash.ado's `_needed` list names it (red). This is the one existence node for the new Mata function (no pytest can run Mata); the behaviour of both splits is pinned by the cscript cases, so no "is called" node is added (REVIEW R2-47).
- Cscript: `test_wp35_truth.cscript` Q3501-1 and Q3501-2 (red: dash r(198)); Q3501-3 (green at base: a guard).

Pinned tests to flip: none found (grep `yvarlabel(.*yvarlabel\|levels(5) levels(` in test/ at 35-01-01 and list any hit in `<scratch>/35-01-flips.txt`).

Parity corpus (R8): none. The item changes only Stata-side parsing; the registered spec of a repeated form equals its last-copy form's (Q3501-1/-2 assert it), and both renderers read that one spec, so there is no twin to pin (REVIEW R2-6). A `CORPUS` entry is a `_case(name, plots, bo, go, ...)` spec (test/test_mode_parity.py:1480), never a command string.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| helper defined and in `_needed` | pytest test_repeat_rightmost.py | -- | n/a |
| label repeats drawn as the last copy | cscript Q3501-1 (twoway SVG checksum, dash spec equality) | live | spec equality covers both |
| contour repeats drawn as the last copy | cscript Q3501-2 | live | yes (spec) |
| repeated flags refused | cscript Q3501-3 | live | n/a |

**Acceptance criteria.**
- **AC-35-01.1** `WP35_ONLY=S01` run prints `Q3501-1 PASS`, `Q3501-2 PASS`, `Q3501-3 PASS` and no FAIL or SKIP.
- **AC-35-01.2** `python3 -m pytest test/test_repeat_rightmost.py test/test_program_coverage_map.py test/test_file_headers.py test/test_no_orphans.py -q -n0` reports 0 failed.
- **AC-35-01.3** test_twoway_option_parity.cscript still ends `ALL CHECKS PASSED` (TP-14a/b unchanged).

## Tasks

**Commit boundary.** 35-01-01..03 are the one MS-1 commit on `wp35-s01` (`$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp35-s01`), subject `Take repeated label and contour options rightmost, as twoway does (WP-35 MS-1)`. Body: the failure text of `<scratch>/35-01-01-failure.txt`; the defect (one combined syntax refused a second copy); what changed (dash_parse.mata `_dash_rightmost_keep`; dash.ado `_dash_label_split`, `_dash_contour_split`); `Regression: test/test_repeat_rightmost.py::TestTheHelper::test_the_helper_is_defined_and_needed -- failed at <base sha> with <text>` and one line each for `test_wp35_truth.cscript Q3501-1` and `Q3501-2`; `BUGS.md: "<the MS-1 title 33-01 wrote>" (closed)`; `GAPS4: MS-1 Tracked`; `Ledger: <n> rows of MS-1 removed; known differences: <m> rows removed`; the GitNexus risk of each edited function from `<scratch>/35-01/anchors.txt` (HIGH, CRITICAL or UNKNOWN named).

**Clear the known differences of MS-1** (35-01-03) means BRIEF's closing steps (1)-(3) ("The corpus ledger and the known-differences tables"; D-33-05.i, D-33-10.a/b/h, D-33-09.c), run in `$WT` before staging; MS-1 closes `Closed` and so should have no `(documented)` or `(residual)` row (one would be dead once it closes: hand it back), and the plain rows of its other id stat:PT-3 go with it in steps (1) and (2): (1) `awk -F'\t' -v id='MS-1' '$1 == id {print NR ": " $0}' scripts/corpus/ledger.tsv` lists the item's plain rows of the corpus ledger; delete each line it prints (an `MS-1 (documented)` or `MS-1 (residual)` row stays, A-10), run `python3 scripts/corpus/ledger.py` (no run folder: `_meta` is kept, TR-33-05.3), `git add scripts/corpus/ledger.tsv` and `git add -f test/fixtures/corpus_ledger.json`, and run `python3 -m pytest test/test_corpus_ledger.py -q -n0 -p no:cacheprovider` (0 failed); (2) run `python3 test/known_differences.py MS-1` (33-10, D-33-10.h) and delete every `<file>:<line>` row it prints from its `*_KNOWN` table, staging each file edited; a difference the item's ruling keeps moves instead into that table's deliberate dict -- `DELIBERATE` for `VALUE_KNOWN` (test/value_truth_known.py), `ABBREV_DELIBERATE` for `ABBREV_KNOWN` (test/test_abbreviations.py), and `SCALE_FRAME_DELIBERATE`, `BY_TYPES_DELIBERATE`, `BY_POSITION_DELIBERATE`, `STAT_COMBOS_DELIBERATE` or `COLORVAR_DELIBERATE` beside 33-11..33-13's `SCALE_FRAME_KNOWN`, `BY_TYPES_KNOWN`, `BY_POSITION_KNOWN`, `STAT_COMBOS_KNOWN` and `COLORVAR_KNOWN` -- as `"<key>": "<ruling id>: <what is kept>"`, the ruling id a DECISIONS or index id (P4-n, A-n, Q-n, M-n) (no ruling of this section keeps a difference, so nothing is expected to move); then run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`), 0 failed; (3) write the driver `printf 'cd "%s/test"\nglobal dash_nobrowser 1\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp33_truth.cscript > <scratch>/run_test_wp33_truth.do`, run `WP33_ONLY=S09 sh $WT/scripts/stata_slot.sh <scratch> <scratch>/run_test_wp33_truth.do` and read `<scratch>/run_test_wp33_truth.log`; if Q3309-1 reports any change for a guard example -- `<example id> improved from ...` or `<example id>: <field> was <old> now <new>` (D-33-09.c) -- regenerate test/fixtures/corpus_guard_truth.json with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s09 $WT/scripts/extract_corpus_guard_truth.do`, run S09 again until it prints `Q3309-1 PASS`, `git add -f test/fixtures/corpus_guard_truth.json` into this item's commit and add `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)` to its body (a verdict this item's change made worse is a regression: fix the code first, then run S09 again). After step (2), also run `WP33_ONLY=S10` of test_wp33_truth.cscript through the same driver: a row keyed to another id that S10 reports as now agreeing (known_problems rule 2: this fix fixed it) is deleted too and named in the body; a deleted row whose difference S10 still reports (rule 1) means the fix is incomplete -- fix the code, never put the row back. Then pull from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main).

<task type="auto" id="35-01-01">
  <name>Write the failing repeat tests</name>
  <files>test/test_repeat_rightmost.py, test/test_wp35_truth.cscript</files>
  <action><![CDATA[
    Check `git -C $WT branch --show-current` prints `wp35-s01` and `grep -c "append new blocks above this line" $WT/test/test_wp35_truth.cscript` prints 1 (W0 ran). From `$WT` run `node .gitnexus/run.cjs impact "_dash_label_split" --direction upstream --repo .` and the same for `_dash_contour_split` and `_dash_require_mata` (its `_needed` list gains a line), writing the callers, processes and risk to `<scratch>/35-01/anchors.txt` (a HIGH, CRITICAL or UNKNOWN risk is named in the handback; UNKNOWN is confirmed with `grep -n "_dash_label_split\|_dash_contour_split\|_dash_require_mata" dash.ado`). Create test/test_repeat_rightmost.py with the pytest node of "TDD test stubs" (read dash.ado and dash_parse.mata as text). Add the helper `_s01_pair` (directly above the block's header) and the S01 block (Q3501-1..3) of "Stata truth" to test/test_wp35_truth.cscript at the place "Stata truth" names. Write the driver `printf 'cd "%s/test"\nglobal dash_nobrowser 1\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp35_truth.cscript > <scratch>/run_test_wp35_truth.do`, run `WP35_ONLY=S01 sh $WT/scripts/stata_slot.sh <scratch> <scratch>/run_test_wp35_truth.do` and `python3 -m pytest test/test_repeat_rightmost.py -q -n0 -rf`; save both outputs' FAIL lines to `<scratch>/35-01-01-failure.txt`. Run the grep of "TDD test stubs" for pins into `<scratch>/35-01-flips.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED` on the pytest output is 1; `test -s <scratch>/35-01/anchors.txt`; the Stata log shows `Q3501-1 FAIL` and `Q3501-2 FAIL` (dash r(198)) and `Q3501-3 PASS`; no `twoway refused` / wrong-pair FAIL line (a wrong pair is fixed in the probe before going on); `test -s <scratch>/35-01-01-failure.txt`.]]></verify>
  <done>The rightmost cases were shown failing on the unmodified tree, and every twoway pair was confirmed to draw its last copy.</done>
</task>

<task type="auto" id="35-01-02">
  <name>Keep the last copy in both splits</name>
  <files>dash_parse.mata, dash.ado, test/program_coverage_map.py</files>
  <action><![CDATA[
    Make TR-35-01.1 (the helper above `_dash_opt_tokens`, the `_needed` list entry, the header-index line, the program_coverage_map.py row), TR-35-01.2 (`_dash_label_split`) and TR-35-01.3 (`_dash_contour_split`). Run the S01 block again; if a row still fails from `_dash_refuse_repeat`, make TR-35-01.4 and write which in `<scratch>/35-01-readings.txt`. Run `python3 -m pytest test/test_repeat_rightmost.py test/test_program_coverage_map.py test/test_no_orphans.py -q -n0`, and the area guards: test_twoway_option_parity.cscript, test_json_escaping.cscript and test_parser.cscript through the two-line driver pattern (one run each).
  ]]></action>
  <verify><![CDATA[S01 prints `Q3501-1 PASS`, `Q3501-2 PASS`, `Q3501-3 PASS`; the pytest run reports 0 failed; the three area cscripts end `ALL CHECKS PASSED` with no SKIP.]]></verify>
  <done>A repeated valued option was drawn as its last copy and a repeated contour flag was still refused, in both helpers, through one shared Mata function.</done>
</task>

<task type="auto" id="35-01-03">
  <name>Document, close MS-1 and commit</name>
  <files>dash.sthlp, CHANGELOG.md, TWOWAY_COVERAGE_AUDIT.md</files>
  <action><![CDATA[
    In dash.sthlp's repeats paragraph (the one holding "An option {cmd:twoway} takes once --", about :949; re-read), insert before that sentence: `{cmd:yvarlabel()}, {cmd:xvarlabel()}, {cmd:mlabprefix()}, {cmd:mlabsuffix()}, {cmd:lalign()}, {cmd:mlabstyle()} and the valued options of {cmd:contour} and {cmd:contourline} draw their last copy, as {cmd:twoway} draws it; a {cmd:contour} switch given twice ({cmd:minmax minmax}) is refused as {cmd:twoway} refuses it.` Append `[WP-35 MS-1: corrected -- a valued contour option given twice draws its last copy, as twoway does; a switch given twice is refused]` to the contour row of TWOWAY_COVERAGE_AUDIT.md (`| Surface/grid | \`contour\``, :101; re-read). CHANGELOG under `### Changed behaviour (may need your do-files changed)`: `- yvarlabel(), xvarlabel(), mlabprefix(), mlabsuffix(), lalign(), mlabstyle() and contour's valued options given twice draw the last copy, as twoway does; dash refused them, r(198). (WP-35, MS-1)`. BUGS.md: rewrite the MS-1 entry's Resolution in PD-4's closed form (`Fixed <ddmonyyyy> (WP-35, MS-1). _dash_label_split and _dash_contour_split keep each valued option's last copy (dash_parse.mata _dash_rightmost_keep); flags keep every copy and are still refused twice; the spec is shared by both modes. Pinned by test/test_repeat_rightmost.py::TestTheHelper::test_the_helper_is_defined_and_needed, test_wp35_truth.cscript Q3501-1, Q3501-2, Q3501-3. Closes GAPS4 MS-1 (WP-35, MS-1).`) and flip `- [ ]` to `- [x]`. GAPS4.md: the MS-1 Tracked line to `Closed in WP-35, BUGS.md "<title>", commit pending.`; delete MS-1's line from `GAPS4_OPEN` in test/test_tracking_documents.py. Run `python3 -m pytest test/test_tracking_documents.py test/test_help_conformance.py -q -n0`. Clear the known differences of MS-1 (Commit boundary; BRIEF steps (1)-(3): MS-1's plain rows of scripts/corpus/ledger.tsv and test/fixtures/corpus_ledger.json, `python3 test/known_differences.py MS-1` and the hygiene command it prints, the S09 guard and test/fixtures/corpus_guard_truth.json on any Q3309-1 change; then `WP33_ONLY=S10`). Pull from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main), stage the section's files, run `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a result marked partial or truncated is run again; the changed symbols must be only those this section names) and copy its summary to `<scratch>/35-01/detect.txt`, write the commit message to `<scratch>/35-01-msg.txt`, run `grep -Eic 'claude|anthropic' <scratch>/35-01-msg.txt` (0), commit with `git commit -F`, re-run the grep on `git log -1 --format=%B`.
  ]]></action>
  <verify><![CDATA[`git log -1 --format=%s` ends `(WP-35 MS-1)`; `grep -c "(WP-35, MS-1)" CHANGELOG.md` prints 1; `grep -c "WP-35 MS-1: corrected" TWOWAY_COVERAGE_AUDIT.md` prints 1; `test -s <scratch>/35-01/detect.txt`; the pytest run reports 0 failed; `test/test_corpus_ledger.py` 0 failed; `WP33_ONLY=S10` prints `Q3310-1 PASS` and `Q3310-2 PASS`; `python3 test/known_differences.py MS-1` prints no `<file>:<line>` row and the hygiene command it prints reports 0 failed; `grep -c "Q3309-1 PASS" <scratch>/run_test_wp33_truth.log` prints 1; the commit body holds the `Ledger:` line; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>The help and the coverage audit said the six options and contour's valued options take the last copy, MS-1 was closed in BUGS.md and GAPS4, and one green commit on wp35-s01 was ready for the merger.</done>
</task>

## Section completion criteria

- `_dash_rightmost_keep` exists, is in `_needed`, the header index and program_coverage_map.py.
- Both splits keep the last copy of each valued option; flags stay refused twice.
- Q3501-1..3 PASS; area cscripts green; one commit `(WP-35 MS-1)`; BUGS/GAPS4/CHANGELOG/TWOWAY_COVERAGE_AUDIT.md updated; MS-1's plain rows gone from ledger.tsv and from every `*_KNOWN` table (`python3 test/known_differences.py MS-1` prints none; any key a ruling kept in its table's deliberate dict), the S09 guard at `Q3309-1 PASS`, with test_corpus_ledger.py and `WP33_ONLY=S10` green; GitNexus impact and detect-changes recorded.

## Notes

- **Traps.** `heatmap` and `outlines` are read into locals named `heatmap`/`outlines` in `_dash_contour_split` but stored in s() as `_heatmap`/`_outlines` by `_dash_contour_check` (dash.ado:2610): use the split's local names. A token `capture syntax` refuses (any non-declared option) keeps its place in `_dash_lb_out`/`_dash_zyx_out` exactly as typed.
- **sandstone.** `sysuse sandstone` ships with Stata; every contour help example uses it. The block restores `sysuse auto, clear` at its end.
- **Help paragraph owned (R3):** the one sentence of 35-01-03 in the repeats paragraph (about :940-960).
- **Merge rules touched:** R1 (S01 block), R5, R6 (one Mata function, on its own `_needed` continuation line after :470 and its own header-index entry, apart from 35-02's insertions -- R2-22), R13 (GitNexus impact before editing, detect-changes before committing), R14 (contour's own `heatmap` option is in scope; it is an option, not a plot type). No R8 entry (no twin).
- **Functions edited** (for the index's Owns cell): `_dash_label_split`, `_dash_contour_split`, `_dash_rightmost_keep` (new), `_dash_require_mata`'s `_needed` list; and `_dash_rep_und_scan`'s table only if TR-35-01.4 is needed.
- **35-03 builds on the name loop.** 35-03 (batch 35.2) appends `subchar` to TR-35-01.2's per-token `foreach o in ...` loop, so its `SUBChar()` copies are kept rightmost too.
- **Commit body line forms:** BRIEF "Commit bodies"; no `Flipped:` line is expected (no pin asserts the refusal).
