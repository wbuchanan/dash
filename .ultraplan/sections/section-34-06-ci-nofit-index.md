# Section 34-06: ci types with nofit count one plot

> Part of: WP-34 (Default drawing of common graphs, P1) · Items: PIC-3 · Risk: green · Batch: 34.2 · Depends on: none · Blocks: none · Tasks: 3, 1 commit · Case-id prefix: Q3406

## Overview

**What is wrong today.** twoway numbers its plots by drawn view, and a ci fit with `nofit` draws one view: `twoway_lfitci_parse.class`'s `log_create_serset` sets `.n = 2` only when `.fit` is on, else `.n = 1`. So in `(lfitci mpg weight, nofit) (scatter mpg weight) (lfit mpg weight)` the scatter is p2 (`#d41159` stcolor, `#90353b` s2color) and the lfit p3 (`#00bf7f`, `#55752f`); in gr_example #78 the scatter is p3 `#00bf7f`. dash counts every ci layer as two plots whatever `nofit` says: `_dash_plot_style_indices` (dash_render.py:57742) adds 2 for every `_DASH_CI_TYPES` layer (:57783-57787), so the scatter draws p3 and the lfit p4 (`#00bf7f`/`#ffd400` stcolor), and in #78 the scatter is `#4f2c99` (p5) -- colour, symbol, pattern and width all shift (PIC-3). The legend numbering (`_dash_legend_keys` :58256 and `_dash_apply_legend`'s `_plot_of` map :39411-39413) has the same `+2`, so `order()`/`label()` numbers after a nofit layer are off by one (the audit's likely knock-on; this section measures it). test/fixtures/ci_plot_index_truth.json has no nofit row.

**After this section**, in both modes: a ci layer (lfitci, qfitci, lpolyci, fpfitci) with `nofit` is one plot for the p# cycle, for the legend's numbers and for every later layer; without `nofit` it stays two. One helper gives the count to all three counters.

**Why one section.** One item, three counters that must agree.

**Test order and commit rule.** 34-06-01 measures nofit rows into the fixture, writes the regression tests and the cscript block, runs them red, saves `<scratch>/34-06-01-failure.txt`, no commit. 34-06-02 adds the helper and uses it in the three counters. 34-06-03 corrects the help, closes PIC-3 and commits `(WP-34 PIC-3)`.

### Section decisions

- **D-34-06.a. One helper.** `_dash_ci_plot_count(plot)` (new, module level) returns 2 for a dict whose type is in `_DASH_CI_TYPES` and whose `options["nofit"]` is blank or absent, else 1 (a hostile or non-dict plot is 1, as `_dash_plot_style_indices` treats it today).
- **D-34-06.b. A nofit layer's own index.** Under nofit the layer's entry in `_dash_plot_style_indices`' output is `_p(n)` (plot n+1's p#) and `n` grows by 1. Its band is still drawn in pstyle ci (unchanged); the index matters for `ciplot()` recasts that take a p# and for the layers after it.
- **D-34-06.c. fitplot()/ciplot().** With `nofit` and `fitplot()`, twoway still draws no line; the count stays 1. The extract measures `(lfitci mpg weight, nofit ciplot(rline)) (scatter mpg weight)` to confirm the next layer's p#.

## Risk: [green] -- a counting rule in three helpers; nofit is rare

**Why.** The helper is pure; the counters already loop over plots.

**Risk factors.** 1. The three counters must change together (legend numbers versus styles). 2. 34-05 (batch 34.1) made three edits to `_dash_legend_keys` (TR-34-05.7): the `keyed` list as the loop's first statement, the ci branch's `band`/`bkey`/`lkey` part keys (a `fitplot(area)` fit's VArea, which carries `_dash_area_ring`, is the fit, not the band; `ciplot(area)`/`fitplot(area)` swatches key their parts), and `if keyed and rends: rends = keyed` immediately before `if ptype in _DASH_CONTOUR_TYPES:`, after the ci branch -- keep all three in place. 3. dash.ado may count plot numbers (legend order validation): confirm.

**Mitigation.** One test per counter over the same nofit sequences; a grep of dash.ado/dash_parse.mata for a ci counter (34-06-01).

## Dependencies

- **Depends on:** none (34-05's three edits in `_dash_legend_keys` landed in batch 34.1; re-read).
- **Blocks:** none.
- **Parallel batch:** 34.2 with 34-03 and 34-08. This section is batch 34.2's one editor of `_dash_apply_legend` (R12). 34-03 edits the axis finish; 34-08 `_dash_expand_numlist`.

## Evidence

### Code at 090d928 (re-read before editing)

```python
57778     for plot in (plots or ()):
57779         ptype = plot.get("type") if isinstance(plot, dict) else None
57780         is_ci = (isinstance(ptype, str)
57781                  and ptype.strip().lower() in _DASH_CI_TYPES)
57782         if is_ci:
57783             line_series = _p(n + 1) + 1     # the line is plot n + 2
57784             out.append(max(line_series - 1, 1) - 1)
57785             n += 2
57786         else:
57787             out.append(_p(n))
57788             n += 1
```
`_dash_legend_keys` (:58213): `if ptype in _DASH_CI_TYPES: ... n += 2; continue` (:58241-58257). `_dash_apply_legend` (:39310), the `_plot_of` map:
```python
39408             for _pl, _r in live:
39409                 _plot_of[_pn] = _pl
39410                 if str(_pl.get("type", "")).lower() in _DASH_CI_TYPES:
39411                     _plot_of[_pn + 1] = _pl
39412                     _pn += 2
39413                 else:
39414                     _pn += 1
```
nofit is read as `bool(str(opts.get("nofit", "") or "").strip())` (:14904). Served: `_dash_plot_style_indices` is called in the served literals :70165-70167 and :70270; the three functions are copied by name (`_dash_legend_keys` in the tuple at :67429).

### twoway's truth

`twoway_lfitci_parse.class` (`.n = 1` without `.fit`); the audit's probe nf_stcolor/nf_s2color (scatter p2, lfit p3) and gr_example #78. Fixture test/fixtures/ci_plot_index_truth.json from scripts/extract_ci_plot_index_truth.do: cases `id|scheme|layers` (:95-114), each layer's plot number counted `+2` for a ci type (:131-133), the style read from `.Graph.plotregion1.plot<k>.style.stylename` (:139).

### Tests pinning today's behaviour

None asserts nofit's count. test/test_ci_plot_index.py::TestTheIndexAgainstStata::test_every_ci_type_takes_two_plots (:80) and TestBothModes::test_order_counts_a_ci_layer_as_two_keys (:283) stay green (no nofit).

## User stories

- US-34-06.1 As a Stata user with an existing twoway command, I want the layers after an `lfitci, nofit` drawn in twoway's colours and symbols, so that the picture matches.
- US-34-06.2 As that user, I want `legend(order())` numbers after a nofit layer to mean the plots twoway means.

## Business requirements

- BR-34-06.1 A ci layer with nofit counts as one plot for every later layer's style, in both modes.
- BR-34-06.2 Legend numbers count a nofit ci layer as one plot.
- BR-34-06.3 Without nofit nothing changes.

## Technical requirements

- TR-34-06.1 New module function after `_DASH_FIT_KEYS` (:57739):
```python
def _dash_ci_plot_count(plot):
    """How many plots twoway numbers for one layer (WP-34 PIC-3): 2 for a
    ci fit (_DASH_CI_TYPES), its band and its line, and 1 under nofit,
    which draws the band alone (twoway_lfitci_parse.class sets .n = 1
    without .fit); 1 for any other layer or a plot that is no dict."""
    if not isinstance(plot, dict):
        return 1
    ptype = plot.get("type")
    if not (isinstance(ptype, str) and ptype.strip().lower() in _DASH_CI_TYPES):
        return 1
    o = plot.get("options")
    nofit = isinstance(o, dict) and bool(str(o.get("nofit", "") or "").strip())
    return 1 if nofit else 2
```
- TR-34-06.2 `_dash_plot_style_indices`: `is_ci = _dash_ci_plot_count(plot) == 2`; the `else` branch (one plot) is taken for a nofit ci layer, so it gets `_p(n)` and `n += 1` (D-34-06.b). Docstring gains one sentence naming nofit.
- TR-34-06.3 `_dash_legend_keys`: in the ci branch replace `n += 2` with `n += _dash_ci_plot_count(plot)`; under nofit the band's key is `n` and no line key is added (the existing `_dash_nofit` filter already drops the line, and 34-05's `lkey` leaves out a nofit fit's swatch). Change nothing else in the branch: 34-05's `band`, `bkey` and `lkey` rules stay, and `if keyed and rends: rends = keyed` stays after the branch, immediately before `if ptype in _DASH_CONTOUR_TYPES:` (placed before the ci branch it would replace a `fitplot(area)` layer's renderers by its swatch and drop the band key).
- TR-34-06.4 `_dash_apply_legend`'s `_plot_of` loop: `if _dash_ci_plot_count(_pl) == 2:` replaces the type test.
- TR-34-06.5 Served copy list (R2): add `"_dash_ci_plot_count",` after `"_dash_legend_keys", "_dash_parse_legend_order",` (:67429). test/function_test_map.py: `'_dash_ci_plot_count': 'test/test_ci_plot_index.py::TestTheNofitCount::test_the_count',`.
- TR-34-06.6 Stata truth: scripts/extract_ci_plot_index_truth.do gains `local cmd_lfitcinf "lfitci mpg weight, nofit"`, `cmd_qfitcinf`, `cmd_lpolycinf`, `cmd_fpfitcinf` (same pattern), `cmd_lfitcinfr "lfitci mpg weight, nofit ciplot(rline)"`, `local ci_nofit "lfitcinf qfitcinf lpolycinf fpfitcinf lfitcinfr"`, the count rule `else if \`: list t in ci_nofit' local plot = \`plot' + 1` before the `else`, and cases `lfitcinf_scatter_lfit|stcolor|lfitcinf scatter lfit`, `lfitcinf_scatter_lfit_s2|s2color|lfitcinf scatter lfit`, `qfitcinf_scatter|s2color|qfitcinf scatter`, `lpolycinf_line|s2color|lpolycinf line`, `fpfitcinf_connected|s2color|fpfitcinf connected`, `scatter_lfitcinf_scatter|s2color|scatter lfitcinf scatter`, `lfitcinf_lfitci_lfit|s2color|lfitcinf lfitci lfit`, `lfitcinfr_scatter|s2color|lfitcinfr scatter`. Add one legend probe after the cases: `twoway (lfitci mpg weight, nofit) (scatter mpg weight) (lfit mpg weight), legend(order(2 3))` exported to SVG and its key texts read as scripts/extract_ts_operator_truth.do's `_keys` reads them (bare minus `legend(off)` twin), written as `"legend_nofit": {"cmd": ..., "keys": [...]}`. Regenerate, `git add -f`.

## Boundaries

- Only the three counters and the helper; no change to the band's pstyle ci drawing, to `ciplot()`/`fitplot()` mappers or to `_dash_layer_series`.
- Keep 34-05's three `_dash_legend_keys` edits (TR-34-05.7) exactly where they are.
- If dash.ado or dash_parse.mata counts plot numbers with a ci rule (grep `lfitci\|ci_types` in both), apply the same nofit rule there and name it in the commit body; if none, say so in the handback.

## Stata truth

`scripts/extract_ci_plot_index_truth.do` -> `test/fixtures/ci_plot_index_truth.json` (TR-34-06.6), run `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch> $WT/scripts/extract_ci_plot_index_truth.do`. Expected: `lfitcinf_scatter_lfit` pstyle [1, 2, 3] (the nofit layer's band is style `ci`, which `pnum` maps to its place in the cycle, plot 1), `legend_nofit.keys == ["Mileage (mpg)", "Fitted values"]`. Truth block, inserted directly above the first block whose `S<MM>` is higher than S06 (BRIEF "Block order"), or above `* ==== append new blocks above this line ====` if there is none (in batch 34.2 there is none; 34-03's S03 lands above S04 and 34-08's S08 after S06, in merge order):

```
* ==== S06 PIC-3: a ci fit with nofit is one plot ====
local only : env WP34_ONLY
if inlist("`only'", "", "S06") & `: list posof "S06" in w34_run' {
    display as text "S06 start " c(current_date) " " c(current_time)
    ...
    display as text "S06 end " c(current_date) " " c(current_time)
}
* ==== end S06 ====
```
- Q3406-1: `(lfitci mpg weight, nofit) (scatter mpg weight) (lfit mpg weight)` under stcolor: twoway's `.Graph.plotregion1.plot2.style.marker.fillcolor.rgb` (as the extract's colour read, :160-168) equals the saved page's scatter fill colour.
- Q3406-2: with `legend(order(2 3))`, the saved page's legend item labels are twoway's keys.

## TDD test stubs

Regression tests (red at the base):
- Test: `_dash_ci_plot_count` over ci types with and without nofit, other types, non-dicts -- test/test_ci_plot_index.py::TestTheNofitCount::test_the_count (red: NameError)
- Test: every nofit case of the fixture draws each layer in twoway's p# -- ::TestTheIndexAgainstStata::test_each_measured_sequence (the parametrised cases grow; red on the nofit ids)
- Test: both modes draw the scatter after `lfitci, nofit` in p2's colour and symbol -- ::TestBothModes::test_each_layer_takes_statas_plot_index[...nofit ids]
- Test: `legend(order(2 3))` after a nofit layer keys the scatter and the lfit -- ::TestBothModes::test_order_counts_nofit_as_one[saved|served]
cscript: Q3406-1, Q3406-2.
Pinned tests to flip: none.
Parity: append `_case("lfitci nofit then scatter", [plot_for("lfitci", {"nofit": "nofit"}), plot_for("scatter")])` to `CORPUS`.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| The count helper | pytest unit | -- | n/a |
| p# after nofit | pytest TestTheIndexAgainstStata + TestBothModes | ci_plot_index_truth.json | yes |
| Legend numbers | pytest + Q3406-2 | same (legend_nofit) | yes |
| Live colours | cscript Q3406-1 | -- | saved |
| Parity | CORPUS | -- | yes |

AC-34-06.1 every nofit case matches twoway's p#; AC-34-06.2 order() numbers match twoway's keys; AC-34-06.3 the old cases unchanged; AC-34-06.4 one green commit.

## Tasks

**Commit boundary.** 34-06-01 to 34-06-03 form one commit, subject `Count a ci fit with nofit as one plot (WP-34 PIC-3)`, made by 34-06-03 on branch `wp34-s06` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp34-s06`.

**Closing steps** (BRIEF "The corpus ledger and the known-differences tables", steps (1)-(3), and "Pull form"; D-33-05.i, D-33-10.h, D-33-09.c). The closing task (34-06-03 for PIC-3) runs them in `$WT` for the item's lead id `<id>`, before staging: (1) `awk -F'\t' -v id='<id>' '$1 == id {print NR ": " $0}' scripts/corpus/ledger.tsv` lists the item's plain rows of the corpus ledger; delete each line it prints (an `<id> (documented)` or `<id> (residual)` row stays, A-10), run `python3 scripts/corpus/ledger.py` (no run folder: `_meta` is kept, TR-33-05.3), `git add scripts/corpus/ledger.tsv` and `git add -f test/fixtures/corpus_ledger.json`, and run `python3 -m pytest test/test_corpus_ledger.py -q -n0 -p no:cacheprovider` (0 failed); (2) run `python3 test/known_differences.py <id>` (33-10, D-33-10.h) and delete every `<file>:<line>` row it prints from its `*_KNOWN` table, staging each file edited; a difference the item's ruling keeps moves instead into that table's deliberate dict -- `DELIBERATE` for `VALUE_KNOWN` (test/value_truth_known.py), `ABBREV_DELIBERATE` for `ABBREV_KNOWN` (test/test_abbreviations.py), and `SCALE_FRAME_DELIBERATE`, `BY_TYPES_DELIBERATE`, `BY_POSITION_DELIBERATE`, `STAT_COMBOS_DELIBERATE` or `COLORVAR_DELIBERATE` beside 33-11..33-13's `SCALE_FRAME_KNOWN`, `BY_TYPES_KNOWN`, `BY_POSITION_KNOWN`, `STAT_COMBOS_KNOWN` and `COLORVAR_KNOWN` -- as `"<key>": "<ruling id>: <what is kept>"`, the ruling id a DECISIONS or index id (P4-n, A-n, Q-n, M-n) (no ruling of this section keeps a difference, so nothing is expected to move); then run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`), 0 failed; (3) write the driver `printf 'cd "%s/test"\nglobal dash_nobrowser 1\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp33_truth.cscript > <scratch>/34-06/run_test_wp33_truth.do`, run `WP33_ONLY=S09 sh $WT/scripts/stata_slot.sh <scratch>/34-06 <scratch>/34-06/run_test_wp33_truth.do` and read `<scratch>/34-06/run_test_wp33_truth.log`; if Q3309-1 reports any change for a guard example -- `<example id> improved from ...` or `<example id>: <field> was <old> now <new>` (D-33-09.c) -- regenerate test/fixtures/corpus_guard_truth.json with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/34-06/s09 $WT/scripts/extract_corpus_guard_truth.do`, run S09 again until it prints `Q3309-1 PASS`, `git add -f test/fixtures/corpus_guard_truth.json` into this item's commit and add `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)` to its body (a verdict this item's change made worse is a regression: fix the code first, then run S09 again). Then it pulls from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main), runs `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a partial or truncated result is run again) and commits.

<task type="auto" id="34-06-01">
  <name>Measure nofit numbering and write failing tests</name>
  <files>scripts/extract_ci_plot_index_truth.do, test/test_ci_plot_index.py, test/test_wp34_truth.cscript</files>
  <action><![CDATA[
Re-read _dash_plot_style_indices, _dash_legend_keys (with 34-05's three edits) and _dash_apply_legend's _plot_of loop at the batch-34.2 base; run `node .gitnexus/run.cjs impact "_dash_plot_style_indices" --direction upstream --repo .` and the same for `_dash_legend_keys` and `_dash_apply_legend`, writing callers to <scratch>/34-06/anchors.txt; `grep -n "lfitci\|ci_types" dash.ado dash_parse.mata` and record any plot-number counter there. Apply TR-34-06.6, run the extractor, `git add -f test/fixtures/ci_plot_index_truth.json`. Add the TDD stubs to test/test_ci_plot_index.py (the class TestTheNofitCount; the order test in TestBothModes beside test_order_counts_a_ci_layer_as_two_keys, reading the fixture's legend_nofit). Insert the S06 block where the Stata truth section says. Run `python3 -m pytest test/test_ci_plot_index.py -q -n0 -p no:cacheprovider -rf > <scratch>/34-06/01.log`, the S06 block with WP34_ONLY=S06, and save the failures to <scratch>/34-06-01-failure.txt. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/ci_plot_index_truth.json'));print(sum('nf' in c['id'] for c in d['cases']), d['legend_nofit']['keys'])"` prints `8 ['Mileage (mpg)', 'Fitted values']`; `grep -c FAILED <scratch>/34-06/01.log` is at least 4; `test -s <scratch>/34-06-01-failure.txt`.]]></verify>
  <done>twoway's nofit numbering and keys were recorded and the regression tests were shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="34-06-02">
  <name>Count nofit layers as one plot</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
Add _dash_ci_plot_count (TR-34-06.1), use it in _dash_plot_style_indices (TR-34-06.2), _dash_legend_keys (TR-34-06.3) and _dash_apply_legend's _plot_of loop (TR-34-06.4), add the copy-list entry and the function_test_map.py row (TR-34-06.5), and apply the same rule to any dash.ado/dash_parse.mata counter 34-06-01 found. Run test/test_ci_plot_index.py, test/test_pcycle_fraction.py, test/test_legend*.py -k "order or label or ci", test/test_series_labels.py, test/test_fit_options*.py -k nofit, test/test_area_outline.py -k TheKey (34-05's keys, `fitplot(area)`/`ciplot(area)` and nofit included), test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName and test/test_function_test_map.py.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_ci_plot_index.py test/test_pcycle_fraction.py test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName test/test_function_test_map.py -q -n0 -p no:cacheprovider` ends with 0 failed; `python3 -m pytest test/test_area_outline.py -k TheKey -q -n0 -p no:cacheprovider` ends with 0 failed.]]></verify>
  <done>A nofit ci layer counts as one plot for styles and legend numbers in both modes.</done>
</task>

<task type="auto" id="34-06-03">
  <name>Correct the help and close PIC-3</name>
  <files>dash.sthlp, test/test_mode_parity.py, test/test_ci_plot_index.py</files>
  <action><![CDATA[
Help: in dash.sthlp:4441-4442 change "a confidence-interval fit such as {cmd:lfitci} is two, its band {it:n} and its line {it:n}+1." to "a confidence-interval fit such as {cmd:lfitci} is two, its band {it:n} and its line {it:n}+1, and one under {cmd:nofit}, which draws its band alone, as {cmd:twoway} numbers it." Add test/test_ci_plot_index.py::TestTheHelp::test_the_nofit_sentence (the `_between(_help(), ...)` pattern of test/test_help_claims_1.py). Append the CORPUS entry to test/test_mode_parity.py. TWOWAY_COVERAGE_AUDIT.md (M13, G1; REVIEW R2-9): append `[WP-34 PIC-3: corrected -- nofit counts one plot, so the next layers take twoway's p#]` to the `lfitci`, `qfitci`, `fpfitci` and `lpolyci` rows (:90, :91, :92, :95) and `[WP-34 PIC-3: corrected -- legend numbers count a nofit ci layer as one plot]` to the Legends row (:143). Close the BUGS.md entry 33-01 registered for PIC-3 (closed form: _dash_ci_plot_count used by _dash_plot_style_indices, _dash_legend_keys and _dash_apply_legend, both modes; pinned by test/test_ci_plot_index.py::TestBothModes::test_order_counts_nofit_as_one and Q3406-1; fixture ci_plot_index_truth.json); rewrite `- **PIC-3 Tracked:**` to the Closed form with `commit pending`; delete PIC-3's line from `GAPS4_OPEN` in test/test_tracking_documents.py; add `- A ci fit with nofit counts as one plot, so the layers after it take twoway's p# styles and legend numbers ((lfitci, nofit) (scatter): the scatter p3 -> p2) (WP-34, PIC-3)` under `### Fixed in WP-34`. Run the Closing steps for PIC-3 (Tasks; BRIEF steps (1)-(3)): (1) delete PIC-3's plain rows of scripts/corpus/ledger.tsv (its `(documented)` and `(residual)` rows stay), rerun `python3 scripts/corpus/ledger.py`, `git add -f test/fixtures/corpus_ledger.json` and run test/test_corpus_ledger.py; (2) run `python3 test/known_differences.py PIC-3`, delete every row it prints (nothing moves to a deliberate dict: no ruling here keeps a difference) and run the hygiene command it prints; (3) run the S09 guard block (`WP33_ONLY=S09`, driver in <scratch>/34-06) and, on any Q3309-1 change for a guard example (an improved verdict or a changed field), regenerate test/fixtures/corpus_guard_truth.json with scripts/extract_corpus_guard_truth.do, rerun S09 to `Q3309-1 PASS` and `git add -f` it with its `Fixture:` line. Run test/test_ci_plot_index.py, test/test_mode_parity.py -k nofit, test/test_help_conformance.py, test/test_tracking_documents.py, test/test_fixtures_are_committed.py and the S06 block; pull from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main); run `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a partial or truncated result is run again); commit with BRIEF's body lines; grep the message for claude|anthropic before and after.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_ci_plot_index.py test/test_help_conformance.py test/test_tracking_documents.py test/test_fixtures_are_committed.py -q -p no:cacheprovider` ends with 0 failed; `grep -c "Q3406-[12] PASS" <scratch>/34-06/run_test_wp34_truth.log` prints 2; `awk -F'\t' '$1 == "PIC-3"' scripts/corpus/ledger.tsv | wc -l` prints 0; `python3 test/known_differences.py PIC-3` prints no `<file>:<line>` row and the hygiene command it prints reports 0 failed; `grep -c "Q3309-1 PASS" <scratch>/34-06/run_test_wp33_truth.log` prints 1; `git log -1 --format=%s` ends `(WP-34 PIC-3)`.]]></verify>
  <done>Plot numbers after a nofit ci layer match twoway in styles and legend numbers, and PIC-3 is closed in one commit.</done>
</task>

## Section completion criteria

- Eight nofit fixture cases and the legend probe match in both modes; the old cases unchanged; the helper in the copy list and the function map; the help sentence corrected and pinned; tracking documents and the five TWOWAY_COVERAGE_AUDIT.md rows tagged; one green commit.

## Notes

- **R12:** 34-06 is batch 34.2's one editor of `_dash_apply_legend`.
- **Help (R3):** this section owns the one clause of dash.sthlp:4441-4442.
- **Trap:** the extract's `pnum` falls back to the cycle for a style that is no `p#` (the nofit layer's band is `ci`): the case's nofit entry compares that fallback with dash's `_p(n)`; confirm the two agree, else compare only the later layers and say why in the test docstring.
- **Commit body line forms:** `Regression: test/test_ci_plot_index.py::TestTheNofitCount::test_the_count -- failed at <base sha> with NameError`; `Fixture: test/fixtures/ci_plot_index_truth.json (scripts/extract_ci_plot_index_truth.do)`; `BUGS.md: "<title>" (closed)`; `GAPS4: PIC-3 Tracked`.
- Merge rules touched: R1, R2, R3, R6 (function map), R7, R8, R12.
