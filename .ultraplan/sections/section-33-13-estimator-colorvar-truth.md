# Section 33-13: Estimator combinations and colorvar key truth

> Part of: WP-33 (Verification corpus and README gallery) · Items: stat:PT-23, CV-16 · Risk: yellow · Batch: 33.4 · Depends on: 33-01, 33-10 (test/known_differences.py) · Blocks: WP-37 and WP-42 sections that fix listed differences (they delete rows) · Tasks: 6, 2 commits · Case-id prefix: Q3313

## Overview

**What is wrong today.** stat:PT-23 (audit :684-686, appendix :1185-1190): "Estimator combinations with no truth (all matched when measured)": the auditor measured, and dash matched, lpoly degree(4) and degree(8) at bwidth(800), `[aw]` gaussian degree 2, cosine degree 3 n(20); lpolyci biweight degree 2 and var() degree 1; kdensity `[aw]` boundary, `[fw]` area()+range()+n(), gaussian default, rectangle n(50), epan2 boundary; lfitci `[pw]` band; qfitci stdr level(80); lfitci range()+n()+stdf; fpfit `[pw]`; fpfitci `[fw]`; histogram discrete `[fw]` percent, discrete width(3) fraction, bin()+start() frequency; lowess mean noweight, mean adjust, logit bwidth -- and one mismatch, lpolyci `[fw]` degree 2 (stat:PT-16). The verifier confirmed none is in stat_truth.json or the seven other estimator fixtures. "A regression would pass."

CV-16 (audit :687-689, appendix :2899-2905): "colorvar fixtures never compare key texts, order or frames; non-scatter options and interactions are unmeasured; disc_levels_price_4 passes vacuously". `test/test_colorvar_truth.py:74-104` compares marker partitions only and returns early for the continuous default (:90-91, "not compared (DISCOVERY Q5)"); `key_texts` are recorded but read only for numbers (:301-370); colorfillonly, coloruseplegend, colorkeysrange, colorlist and cuts/levels are measured on scatter only; `disc_levels_price_4` has one group on both sides (#808080). The auditor's run1-run8 probe files no longer exist; this section writes the probe list anew.

**After this section.** extract_stat_truth.do records a `combos` section of 23 probes and test_statistical_truth.py compares dash's mappers with each, the lpolyci `[fw]` mismatch listed as stat:PT-16's documented difference. extract_colorvar_truth.do records every probe's texts with positions and the plot region, plus 22 new probes (six non-scatter types, the options on non-scatter types, by(), colorallowmultiple, legend() interplay, a non-vacuous colordiscrete+colorlevels, refusals), and test_colorvar_truth.py compares key texts, order, frame and per-type colours in both modes, the continuous default included, with known differences keyed by GAPS4 ids.

**Why one section.** Both widen an existing extractor and its reader with no dash change; both items' differences belong to later WPs (37, 42), which shrink the lists.

**Test order and commit rule.** stat:PT-23 (tasks 01-03), then CV-16 (tasks 04-06).

### Section decisions (binding on the executor)

- **D-33-13.a Combination probes** (section `combos`, keys `<dataset>:<name>`, data as the script's existing `weighted_data` defines `auto:aw_price`, `auto:fw_fw`, `auto:pw_price`): `lpoly_deg4_bw800` `lpoly mpg weight, degree(4) bwidth(800)`; `lpoly_deg8_bw800`; `lpoly_aw_gauss_deg2` `lpoly mpg weight [aw=price], kernel(gaussian) degree(2)`; `lpoly_cos_deg3_n20`; `lpolyci_biw_deg2` `lpolyci mpg weight, kernel(biweight) degree(2)`; `lpolyci_var_deg1` `lpolyci mpg weight, degree(1) var(10)`; `lpolyci_fw_deg2` `lpolyci mpg weight [fw=fw], degree(2)`; `kd_aw_boundary` `kdensity mpg [aw=price], boundary`; `kd_fw_area_range_n` `kdensity mpg [fw=fw], area(2) range(10 40) n(50)`; `kd_gauss` `kdensity mpg, kernel(gaussian)`; `kd_rect_n50`; `kd_epan2_boundary`; `lfitci_pw` `lfitci mpg weight [pw=price]`; `qfitci_stdr_l80` `qfitci mpg weight, stdr level(80)`; `lfitci_range_n_stdf` `lfitci mpg weight, range(1000 6000) n(20) stdf`; `fpfit_pw`; `fpfitci_fw`; `hist_disc_fw_pct` `histogram rep78 [fw=fw], discrete percent`; `hist_disc_w3_frac` `histogram rep78, discrete width(3) fraction`; `hist_bin_start_freq` `histogram mpg, bin(8) start(10) frequency`; `lowess_mean_noweight`, `lowess_mean_adjust`, `lowess_logit_bw` `lowess foreign weight, logit bwidth(0.5)` -- 23 keys. Each records the serset(s) of `twoway <cmd>, nodraw saving(<gph>)` with the script's `zq_serset` + `zq_curve` (extract_stat_truth.do:138-238), and for ci types every band column.
- **D-33-13.b Combination comparison.** Mapper level, as test_statistical_truth.py's weighted tests do (`mapper.map_<type>(figure(), source, "y", opts)` then `_line_data` / `_at_samples` / band columns): same point count, values within rtol 1e-6 (atol 1e-6 x span); histogram heights and edges within 1e-9. GlyphMapper is copied whole into the served app (BRIEF "Both modes"), so the mapper check covers both; no served build is added for this item.
- **D-33-13.c Known differences** (33-10's rule and value forms, D-33-10.a; A-10: a documented or residual row stays after its item closes): `STAT_COMBOS_KNOWN = {"auto:lpolyci_fw_deg2": "stat:PT-16 (documented)"}` plus anything the run finds, mapped to a live item (lpoly high degree -> `DT-26 (documented)`, 37-05; ties -> `stat:PT-21 (documented)`); an ownerless difference stops task 03. `STAT_COMBOS_DELIBERATE = {}` beside the table (D-33-10.a's companion dict for a difference a ruling keeps; empty) is passed as `deliberate=` to every `known_problems` call over it. Each key's test (`test_each_combination[<key>]`) runs the comparison and applies `known_problems` to that key alone, so rule 1 (a new difference) and rule 2 (a listed key that now agrees) are one test per key; rule 3 over every row is `test_every_known_difference_is_open`. No second recomputing test is kept (one test per behaviour).
- **D-33-13.d Colorvar texts.** For every probe (old and new) the extractor adds `texts` (each SVG text's string, x, y, anchor, size, from scripts/svg_truth.py `svg_texts`/`svg_document`) and `plot` (the plot region box from `svg_plotregion`, svg_truth.py:439). Key texts are derived in the test: the colour key's are the texts with x > plot.right + 1 unit, ordered by y ascending (top to bottom); a plot legend's (coloruseplegend, legend()) are the texts with y > the x axis title's y, ordered by row then x. The key frame is `true` when a stroked `<rect>` encloses every key text (svg_truth `svg_rects`). The old `key_texts` field stays (its readers stay).
- **D-33-13.e New colorvar probes** (ids `cv16_*`, auto; commands with `name(zqg, replace)` as the loop adds): six types x two colourings -- `line mpg weight, sort`, `connected mpg weight, sort`, `bar mpg weight`, `spike mpg weight`, `rcap mpg price weight`, `pcspike mpg weight price foreign`, each with `colorvar(rep78) colordiscrete` and with `colorvar(price) colorlevels(4)` (12); options on non-scatter types -- `bar mpg weight, colorvar(rep78) colordiscrete colorfillonly`, `line mpg weight, sort colorvar(rep78) colordiscrete colorfillonly`, `line mpg weight, sort colorvar(rep78) colordiscrete coloruseplegend`, `bar mpg weight, colorvar(price) colorlevels(4) colorkeysrange`, `line mpg weight, sort colorvar(rep78) colorcuts(2 4) colorlist(red green blue)` (5); interactions -- `scatter mpg weight, colorvar(rep78) colordiscrete by(foreign)`, `(scatter mpg weight, colorvar(rep78) colordiscrete) (scatter mpg length, colorvar(rep78) colordiscrete), colorallowmultiple`, `scatter mpg weight, colorvar(rep78) colordiscrete legend(rows(2))`, `scatter mpg weight, colorvar(rep78) colordiscrete colorlevels(3)` (the non-vacuous colordiscrete+colorlevels) (4); refusal -- `scatter mpg weight, colorvar(price) zlabel(bogus)` (rc and first line only) (1). 22 probes. Multi-plot and by() probes need the loop's body/opts split: register them with body `twoway` and the whole rest as opts, or add a `zcp2` form; record per-panel fills under by() (`fills_by_panel`).
- **D-33-13.f Colorvar comparisons** (test/test_colorvar_truth.py, both modes, served `pytest.mark.batch`): key texts and order; key frame; per-type colour partition and palette (the marker or segment colours of each drawn element against twoway's `fills`/`fill_groups`); the continuous default compared (the early `return` at :90-91 removed: `# Flipped (WP-33 CV-16): the continuous default is compared; its difference is CV-8's, 42-01`). Known differences (`COLORVAR_KNOWN = {"<probe>:<check>": "<id>"}`): discrete key order, value labels, '(missing)' row, swatch shape, frame -> `CV-3` (42-03); coloruseplegend key -> `CV-4` (42-04); legend() restyling the key -> `CV-5` (42-04); colorfillonly line parts -> `CV-1` (42-02); two colorvar layers -> `CV-6` (42-02); continuous default -> `CV-8` (42-01); colorlevels(k) cuts -> `CV-2` (42-05); colorkeysreverse/one-value levels -> `CV-11` (42-04); zlabel(bogus) accepted -> `CV-10` (42-05). The by() probe (`scatter mpg weight, colorvar(rep78) colordiscrete by(foreign)`) uses no coloruseplegend, so its differences take the first owner above that fits the check (a discrete key's order, texts, swatches or frame -> `CV-3`); `BY-14` (41-04) is used only for a coloruseplegend probe under by(), and this probe list has none (REVIEW-1 R1-39). Ownerless differences stop task 06. `COLORVAR_DELIBERATE = {}` beside the table (D-33-10.a; empty -- 42-05's closing commit moves into it any difference CV-14's ruling keeps, A-12) is passed as `deliberate=` to every `known_problems` call over `COLORVAR_KNOWN`.
- **D-33-13.g Vacuous probes.** `test_no_probe_passes_vacuously`: every probe with colordiscrete, colorcuts or colorlevels has twoway `n_groups >= 2`, or is in `_ONE_GROUP_BY_TWOWAY = {"disc_levels_price_4": "twoway draws every marker #808080 (measured); cv16_disc_levels_rep78_3 is the non-vacuous probe of the combination"}`.
- **D-33-13.h Spread and tiers (REVIEW-1 R1-38).** The colorvar tests are one test per probe, so xdist spreads the builds: `TestTheKeyAgainstTwoway::test_saved[<probe id>]`, `TestEveryTypeColours::test_saved[<probe id>]` and their `test_served[<probe id>]` twins (`pytest.mark.batch`), parametrised over the module tuple `_CV_PROBES` (the 18 old ids and D-33-13.e's 22, written out so collection never depends on the fixture), each `pytest.param(pid, marks=pytest.mark.xdist_group("cv-" + pid))` so a probe's key and colour tests share one worker and one build: `_cv_models(mode, pid)` is cached with `functools.lru_cache`. Each asserts `known_problems` over that probe's results and the `COLORVAR_KNOWN` rows whose key starts `"<pid>:"`; `TestTheKnownDifferences::test_every_known_difference_is_open` applies rule 3 over every row once, in the default tier. The hand-back reports the measured seconds of the saved and served classes for 50-01.

## Risk: [yellow] -- two large extractors widened; many differences expected in CV-16

**Risk factors.** (1) Regenerating stat_truth.json or colorvar_truth.json changes an old value (Stata drift) and flips an old test. (2) Key-text selection by geometry misreads a key at another position. (3) Many CV-16 differences.

**Mitigation.** (1) Diff the old keys after regeneration; a changed old value is reported in the commit body and the reading test decides (R7). (2) Every new probe keeps the key at its default position (right, ring 1) except coloruseplegend/legend() (bottom), handled by D-33-13.d's two rules. (3) That is the point: each goes to its WP-42 owner; the known table is the hand-off.

## Dependencies

- **Depends on: 33-01** (GAPS4.md, the BUGS entries, test_wp33_truth.cscript) and **33-10** (batch 33.2: `test/known_differences.py`, the known-differences rule D-33-10.a).
- **Parallel batch 33.4:** with 33-04 and 33-12. Disjoint files. 33-04 adds no block to test_wp33_truth.cscript; this section's two S13 blocks go directly above the marker, after 33-12's S12 blocks (picks.sh's `blockorder.py` keeps S12 before S13 when the batch merges; REVIEW-1 R1-31).

## Evidence

- `scripts/extract_stat_truth.do` (3,142 lines): record helpers `zq_s`/`zq_n`/`zq_a`/`zq_chunk` (:98-136), `zq_curve` (:138-205: all rows when n <= 41, else 11 samples at `round(1 + (k-1)*(n-1)/10)`), `zq_serset` (:207-238), datasets (:239ff); weighted data keys `auto:aw_price`, `auto:fw_fw`, `auto:pw_price` (stat_truth.json `weighted_data`). Fixture sections listed in stat_truth.json (`weighted`, `weighted_ci`, `kernels`, `lowess_more`, `histogram_discrete` ...); none holds D-33-13.a's keys (the verifier's check, appendix :1189).
- `test/test_statistical_truth.py` (2,058 lines): the weighted kdensity tests (:1588-1625) show the mapper pattern (`_weighted_frame`, `_weighted_source`, `mapper.map_kdensity`, `_line_data`, `_at_samples`, `_series`); module `pytestmark` skipif (:38).
- `scripts/extract_colorvar_truth.do` (329 lines): `zcp id ds body opts` (:73-84), 16 SVG probes (:86-101), two rc probes (:103-108), loop :114ff (`nodraw` and drawn runs, SVG export).
- `test/fixtures/colorvar_truth.json`: 18 probes; each `{colorvar, command, dataset, fill_groups, fills, key_texts, marker_order, message, n_groups, n_markers, rc}`; `disc_levels_price_4` `n_groups 1`, fills `{'0': '#808080'}`; `_meta.marker_order_selfcheck = "observation"`.
- `test/test_colorvar_truth.py`: `TestAgainstTwoway::test_every_probe_partitions_the_observations_as_twoway_does` (:74-104, the early return :90-91), `_opts_of` (:50-63), `_canonical` (:66-71); key_texts read at :301-370 for numbers. Related: test_colorvar_options.py:262-420, test_colorvar_coverage.py:245-295 (kept).

## User stories

- **US-33-13.1** As the Stata user, I want every estimator option combination I use to draw twoway's curve, and a change that breaks one caught.
- **US-33-13.2** As the Stata user with a colorvar() graph, I want the colour key's texts, order and frame, and each plot type's colours, as twoway draws them.

## Business requirements

- **BR-33-13.1** The 23 combinations have committed truth and a comparison with dash; their one known mismatch is listed as documented.
- **BR-33-13.2** colorvar key texts, order, frame and per-type colours are compared for every probe in both modes, the continuous default included; every difference is listed under a live GAPS4 row (D-33-10.a).
- **BR-33-13.3** No colorvar probe passes because both sides draw one colour, unless twoway's one colour is the measured answer and a non-vacuous probe covers the combination.

## Technical requirements

- **TR-33-13.1 (combos extract)** In scripts/extract_stat_truth.do add the section `* ==== WP-33 33-13: estimator combinations (stat:PT-23) ====` before the trailing python block, writing D-33-13.a's probes with the existing record helpers under section name `combos`; in the python block add `"combos"` to the sections it writes and `_meta.counts.combos`.
- **TR-33-13.2 (combos test)** test/test_statistical_truth.py: `STAT_COMBOS_KNOWN` and `STAT_COMBOS_DELIBERATE` (D-33-13.c), the module tuple `_COMBO_KEYS` (the 23 keys of D-33-13.a, written out so collection never depends on the fixture) and `class TestEstimatorCombinations` with `test_the_section_exists` (`sorted(truth["combos"]) == sorted(_COMBO_KEYS)`; a missing section raises `KeyError: 'combos'`); `test_each_combination[key]` parametrised over `_COMBO_KEYS`: D-33-13.b's comparison gives `None` or the difference, and the test asserts `known_problems({key: <it>}, {key: STAT_COMBOS_KNOWN[key]} if key in STAT_COMBOS_KNOWN else {}, "stat_combos", deliberate=STAT_COMBOS_DELIBERATE) == []` (a listed key that now agrees fails with "delete its row"; never `pytest.skip`: a skip fails a strict run); a probe twoway refused compares rc only; `test_every_known_difference_is_open` (`dead_rows(STAT_COMBOS_KNOWN, "stat_combos") == []`, D-33-10.a's rule 3, and every key one of `_COMBO_KEYS`).
- **TR-33-13.3 (combos block)** `* ==== S13 stat:PT-23: estimator combinations ====`, directly above the marker (after S12's blocks), in BRIEF's block form (gate `WP33_ONLY`, `S13 start`/`S13 end` lines): `sysuse auto`; `twoway lfitci mpg weight [pw=price], nodraw saving(<tmp>.gph)`, serset sampled values against `combos["auto:lfitci_pw"]` within 1e-9; the same for `histogram rep78 [fw=fw], discrete percent` (with `generate fw` as the script defines it); `Q3313-1`.
- **TR-33-13.4 (colorvar extract)** scripts/extract_colorvar_truth.do: D-33-13.d's `texts` and `plot` fields for every probe in the python block; D-33-13.e's 22 probes after :101 (and the refusal after :108); a `zcp2 id ds "full command"` registration for the multi-plot and by() probes whose command is not `body, opts`; under by() record `fills_by_panel` (fills grouped by the panel rect each marker lies in).
- **TR-33-13.5 (colorvar tests)** test/test_colorvar_truth.py: flip :90-91 (D-33-13.f); add `_cv_spec(probe)` (plot dict shaped as `test/test_server_layer_defects.py::plot_for` for the probe's type, options from `_opts_of`, graph options `by`/`legend`/`colorallowmultiple` from the command), `_cv_draw(mode, spec)` (saved: `DashRenderer` + `render_models`; served: `ServerAppBuilder` + `load_app` + `Document`, as test/test_by_text.py:109-143 does), `_dash_key(models)` (ColorBar: the ticker's tick labels top to bottom; discrete clegend Legend: item labels in drawn order; plegend items), `_CV_PROBES` and the cached `_cv_models(mode, pid)` (D-33-13.h), and classes `TestTheKeyAgainstTwoway::test_saved[<probe id>]`, `::test_served[<probe id>]` (batch), `TestEveryTypeColours::test_saved[<probe id>]`, `::test_served[<probe id>]` (batch), each for an rc-0 probe through `known_problems(<that probe's results>, <its prefixed COLORVAR_KNOWN rows>, "colorvar", deliberate=COLORVAR_DELIBERATE)`, `TestNoVacuousProbe::test_no_probe_passes_vacuously` and `TestTheKnownDifferences::test_every_known_difference_is_open` (`dead_rows(COLORVAR_KNOWN, "colorvar") == []`; every key's probe id in `_CV_PROBES`); the refusal probes compare rc (and first line) with dash's registration answer recorded by the extractor's existing dash run, if it has one, else by `known_problems` on rc only.
- **TR-33-13.6 (colorvar block)** `* ==== S13 CV-16: colorvar key truth ====`, directly after `* ==== end S13 ====` of the stat:PT-23 block, in BRIEF's block form: `twoway scatter mpg weight, colorvar(rep78) colordiscrete name(zqg, replace)`, export, the key texts by D-33-13.d's rule through a python helper on scripts/svg_truth.py, equal to the fixture's `disc_rep78` derived key texts; `Q3313-2`.
- **TR-33-13.7 Maps.** None.

## Boundaries

- No change to `_apply_colorvar`, `_colorvar_*`, `_dash_colorvar_cuts` or any mapper (WP-42's, WP-37's). No help edit.
- Old probes' commands stay as they are; only new fields are added to them.

## Stata truth

`scripts/extract_stat_truth.do` (combos, 23 probes) and `scripts/extract_colorvar_truth.do` (22 probes and two fields) regenerated through `scripts/stata_slot.sh` one at a time (`DASH_REPO=$WT`); `git add -f test/fixtures/stat_truth.json test/fixtures/colorvar_truth.json`; diff the old sections against `git show HEAD:<fixture>`. Live cases Q3313-1, Q3313-2.

## TDD test stubs

stat:PT-23 (red at the base):
- Test: `test/test_statistical_truth.py::TestEstimatorCombinations::test_each_combination[auto:lpoly_deg4_bw800]` ... (23 ids) -- red: each of the 23 `test_each_combination[...]` and `test_the_section_exists` fail with `KeyError: 'combos'` (the parametrisation is the written-out module tuple `_COMBO_KEYS` of TR-33-13.2, so collection never depends on the fixture).
- Test: `::test_every_known_difference_is_open`.
- cscript: `Q3313-1`.

CV-16 (red after stat:PT-23's commit):
- Test: `test/test_colorvar_truth.py::TestTheKeyAgainstTwoway::test_saved[<probe id>]` (40) -- red: no `texts` field.
- Test: `::TestEveryTypeColours::test_saved[<probe id>]`, `::TestNoVacuousProbe::test_no_probe_passes_vacuously` (red: no cv16 probes), `::TestTheKnownDifferences::test_every_known_difference_is_open`, served twins (batch).
- Flip: `TestAgainstTwoway::test_every_probe_partitions_the_observations_as_twoway_does` (:90-91).
- cscript: `Q3313-2`.

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| 23 estimator combinations | pytest, mapper level | stat_truth.json `combos` | shared mapper |
| twoway drift | cscript Q3313-1 | stat_truth.json | -- |
| colour key texts, order, frame | pytest, one test per probe (served batch) | colorvar_truth.json | yes |
| per-type colours | pytest, one test per probe (served batch) | colorvar_truth.json | yes |
| known-table hygiene (both tables) | pytest, default tier | stat_truth.json, colorvar_truth.json, GAPS4.md | -- |
| vacuous probes | pytest | colorvar_truth.json | -- |
| twoway drift | cscript Q3313-2 | colorvar_truth.json | -- |

- **AC-33-13.1** Both pytest files green with every listed row live (D-33-10.a rule 3); Q3313-1 and Q3313-2 PASS.
- **AC-33-13.2** Two commits ending `(WP-33 stat:PT-23)` and `(WP-33 CV-16)`.

## Tasks

**Commit boundary.** 33-13-01..03: stat:PT-23, subject `Record and compare the estimator combinations twoway was never measured on (WP-33 stat:PT-23)`. 33-13-04..06: CV-16, subject `Compare colorvar keys, frames and per-type colours with twoway's in both modes (WP-33 CV-16)`. Branch `wp33-s13` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp33-s13`.

**Closing steps** (BRIEF "The corpus ledger and the known-differences tables", steps (1)-(3), and "Pull form"; D-33-10.h). Each closing task (33-13-03 for stat:PT-23, 33-13-06 for CV-16) runs them in `$WT` before staging. Batch 33.4 lands before the corpus ledger (scripts/corpus/ledger.tsv and ledger.py, 33-05, batch 33.5) and the guard (Q3309-1, 33-09, batch 33.6) exist, so steps (1) and (3) have nothing to run on yet (BRIEF applies them from WP-34 on; 33-14 runs all three for TR-2 in batch 33.7); step (2) runs for the item's lead id `<id>`: run `python3 test/known_differences.py <id>` (33-10, D-33-10.h) and delete every `<file>:<line>` row it prints from its `*_KNOWN` table, staging each file edited; a difference the item's ruling keeps moves instead into that table's deliberate dict -- `DELIBERATE` for `VALUE_KNOWN` (test/value_truth_known.py), `ABBREV_DELIBERATE` for `ABBREV_KNOWN` (test/test_abbreviations.py), and `SCALE_FRAME_DELIBERATE`, `BY_TYPES_DELIBERATE`, `BY_POSITION_DELIBERATE`, `STAT_COMBOS_DELIBERATE` or `COLORVAR_DELIBERATE` beside 33-11..33-13's `SCALE_FRAME_KNOWN`, `BY_TYPES_KNOWN`, `BY_POSITION_KNOWN`, `STAT_COMBOS_KNOWN` and `COLORVAR_KNOWN` -- as `"<key>": "<ruling id>: <what is kept>"`, the ruling id a DECISIONS or index id (P4-n, A-n, Q-n, M-n) (no ruling of this section keeps a difference, so nothing is expected to move); then run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`), 0 failed. No row keyed to the closing item's own id is expected: STAT_COMBOS_KNOWN and COLORVAR_KNOWN key each difference to the item that fixes or documents it (D-33-13.c, D-33-13.f), so they stay live when this item closes. Then it pulls from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main), runs `node .gitnexus/run.cjs detect-changes --scope all --repo .` and commits.

<task type="auto" id="33-13-01">
  <name>Write the combination tests red</name>
  <files>test/test_statistical_truth.py, test/test_wp33_truth.cscript</files>
  <action><![CDATA[In worktree $WT (wp33-s13) add `TestEstimatorCombinations` (TR-33-13.2, with `_COMBO_KEYS` and `test_the_section_exists`), `STAT_COMBOS_KNOWN` and `STAT_COMBOS_DELIBERATE = {}` to test/test_statistical_truth.py; append the S13 stat:PT-23 block (TR-33-13.3). Run `python3 -m pytest test/test_statistical_truth.py -k TestEstimatorCombinations -q -n0 -p no:cacheprovider > <scratch>/s13/01.log 2>&1`; save the failure to <scratch>/33-13-01-failure.txt. Do not commit.]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/s13/01.log` is at least 1; `test -s <scratch>/33-13-01-failure.txt`.]]></verify>
  <done>The combination tests existed and failed for want of truth.</done>
</task>

<task type="auto" id="33-13-02">
  <name>Measure the combinations in Stata</name>
  <files>scripts/extract_stat_truth.do, test/fixtures/stat_truth.json</files>
  <action><![CDATA[Run `node .gitnexus/run.cjs impact "zq_serset" --direction upstream --repo .` and the same for `zq_curve` (Stata programs may be unresolved: an UNKNOWN is confirmed with `grep -n "zq_serset\|zq_curve" scripts/*.do`); the new section only calls them. Apply TR-33-13.1 (re-read :93-238 and the trailing python block first), run the script through the slot, `git add -f test/fixtures/stat_truth.json`, and diff every pre-existing section against `git show HEAD:test/fixtures/stat_truth.json` (`python3 -c` comparing `json.load` of both for keys other than `combos` and `_meta`); a changed old value goes into <scratch>/s13/changes.txt for the commit body and its reading test decides. Run the S13 block (Q3313-1 PASS).]]></action>
  <verify><![CDATA[`python3 -c "import json;print(len(json.load(open('test/fixtures/stat_truth.json'))['combos']))"` prints 23; the driver log shows `Q3313-1 PASS`.]]></verify>
  <done>The 23 combinations were committed truth from the committed extractor.</done>
</task>

<task type="auto" id="33-13-03">
  <name>List differences and commit stat:PT-23</name>
  <files>test/test_statistical_truth.py</files>
  <action><![CDATA[Run `python3 -m pytest test/test_statistical_truth.py -q -n 8 -p no:cacheprovider`; add each reported difference to STAT_COMBOS_KNOWN by D-33-13.c (lpolyci_fw_deg2 is expected; an ownerless one stops the task). Close the stat:PT-23 BUGS entry: `Fixed <ddmonyyyy> (WP-33, stat:PT-23). scripts/extract_stat_truth.do records 23 estimator combinations (section combos: lpoly high degree and weights, lpolyci, kdensity weights and boundary, ci bands with pw/stdr/stdf/range, fpfit weights, histogram discrete with fw/width/fraction, lowess flag combinations); test/test_statistical_truth.py::TestEstimatorCombinations compares dash's mappers with each; lpolyci [fw] degree 2 is listed as stat:PT-16's documented difference. Pinned by test/test_statistical_truth.py::TestEstimatorCombinations, test/test_wp33_truth.cscript Q3313-1; fixture test/fixtures/stat_truth.json. Closes GAPS4 stat:PT-23 (WP-33, stat:PT-23).`; `- [x]`; Tracked Closed `commit pending`; delete `"stat:PT-23"` from `GAPS4_OPEN` in test/test_tracking_documents.py; CHANGELOG `- Twenty-three estimator option combinations are measured in twoway and compared with dash (WP-33, stat:PT-23)`. Run the Closing steps for stat:PT-23 (Tasks): steps (1) and (3) have nothing to run on at batch 33.4 (no ledger, no guard yet); (2) run `python3 test/known_differences.py stat:PT-23`, delete every row it prints (none expected; nothing moves to a deliberate dict) and run the hygiene command it prints. Pull from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main); run `node .gitnexus/run.cjs detect-changes --scope all --repo .`; commit (body adds `Seconds: S13 stat:PT-23 <n>`).]]></action>
  <verify><![CDATA[The pytest run passes; `python3 test/known_differences.py stat:PT-23` prints no `<file>:<line>` row and the hygiene command it prints reports 0 failed; `git log -1 --format=%s` ends `(WP-33 stat:PT-23)`; the claude|anthropic grep prints 0.]]></verify>
  <done>stat:PT-23 was closed with the combinations measured and compared.</done>
</task>

<task type="auto" id="33-13-04">
  <name>Write the colorvar key tests red</name>
  <files>test/test_colorvar_truth.py, test/test_wp33_truth.cscript</files>
  <action><![CDATA[Run `node .gitnexus/run.cjs impact "test_every_probe_partitions_the_observations_as_twoway_does" --direction upstream --repo .` and the same for `_opts_of` before editing them (an UNKNOWN is confirmed with `grep -rn` over test/). Apply TR-33-13.5 to test/test_colorvar_truth.py (with `COLORVAR_KNOWN = {}`, `COLORVAR_DELIBERATE = {}` and the flip at :90-91) and append the S13 CV-16 block (TR-33-13.6). Run `python3 -m pytest test/test_colorvar_truth.py -q -n0 -p no:cacheprovider > <scratch>/s13/04.log 2>&1`; save the failures to <scratch>/33-13-04-failure.txt. Do not commit.]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/s13/04.log` is at least 3; `test -s <scratch>/33-13-04-failure.txt`.]]></verify>
  <done>The colorvar key and type tests existed and failed on the committed fixture.</done>
</task>

<task type="auto" id="33-13-05">
  <name>Widen the colorvar extractor and regenerate</name>
  <files>scripts/extract_colorvar_truth.do, test/fixtures/colorvar_truth.json</files>
  <action><![CDATA[Apply TR-33-13.4 (re-read :60-329 first), run the script through the slot, `git add -f test/fixtures/colorvar_truth.json`; diff the 18 old probes' old fields against `git show HEAD:...` (a change is reported, not hidden). Run the S13 CV-16 block (Q3313-2 PASS).]]></action>
  <verify><![CDATA[`python3 -c "import json;p=json.load(open('test/fixtures/colorvar_truth.json'))['probes'];print(len(p), all('texts' in v for v in p.values() if v['rc']==0))"` prints 40 and True; the old-field diff prints nothing; the driver log shows `Q3313-2 PASS`.]]></verify>
  <done>colorvar truth held positioned texts for every probe and 22 new probes.</done>
</task>

<task type="auto" id="33-13-06">
  <name>List colorvar differences and commit CV-16</name>
  <files>test/test_colorvar_truth.py</files>
  <action><![CDATA[Run `python3 -m pytest test/test_colorvar_truth.py test/test_colorvar_options.py test/test_colorvar_coverage.py -q -n 8 -p no:cacheprovider --durations=0` and `DASH_TEST_TIER=batch python3 -m pytest test/test_colorvar_truth.py -k served -q -n 8 -p no:cacheprovider --durations=0` (record each class's seconds for the hand-back, D-33-13.h); fill COLORVAR_KNOWN by D-33-13.f (ownerless differences stop the task). Close the CV-16 BUGS entry: `Fixed <ddmonyyyy> (WP-33, CV-16). scripts/extract_colorvar_truth.do records every probe's positioned texts and plot region and 22 new probes (six non-scatter types, colorfillonly/coloruseplegend/colorkeysrange/colorlist on them, by(), colorallowmultiple, legend() interplay, colordiscrete with colorlevels on rep78, a z refusal); test/test_colorvar_truth.py compares key texts, order, frame and per-type colours in both modes, the continuous default included, differences listed under <ids>; disc_levels_price_4's one colour is twoway's measured answer and cv16_disc_levels_rep78_3 covers the combination. Pinned by test/test_colorvar_truth.py::TestTheKeyAgainstTwoway, ::TestEveryTypeColours, ::TestNoVacuousProbe, test/test_wp33_truth.cscript Q3313-2; fixture test/fixtures/colorvar_truth.json. Closes GAPS4 CV-16 (WP-33, CV-16).`; `- [x]`; Tracked Closed `commit pending`; delete `"CV-16"` from `GAPS4_OPEN` in test/test_tracking_documents.py; CHANGELOG `- colorvar keys, frames and per-type colours are compared with twoway's (WP-33, CV-16)`. Run the Closing steps for CV-16 (Tasks): steps (1) and (3) have nothing to run on at batch 33.4 (no ledger, no guard yet); (2) run `python3 test/known_differences.py CV-16`, delete every row it prints (none expected; nothing moves to a deliberate dict) and run the hygiene command it prints. Pull from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main); run `node .gitnexus/run.cjs detect-changes --scope all --repo .`; commit with the `Flipped:` line for :90-91 (body adds `Seconds: S13 CV-16 <n>; key and colour classes <n> s saved, <n> s served`).]]></action>
  <verify><![CDATA[Both runs pass; `python3 test/known_differences.py CV-16` prints no `<file>:<line>` row and the hygiene command it prints reports 0 failed; `git log -1 --format=%s` ends `(WP-33 CV-16)`; the claude|anthropic grep prints 0.]]></verify>
  <done>CV-16 was closed with colorvar keys and per-type colours compared in both modes.</done>
</task>

## Section completion criteria

- Two commits; two fixtures regenerated by their scripts with old sections unchanged (or the change reported); the new tests green with every listed row live (D-33-10.a rule 3); Q3313-1, Q3313-2 PASS.

## Notes

- **fw data.** Use the script's own `auto:fw_fw` construction for every `[fw=fw]` probe so dash's test and twoway read the same weights.
- **Old readers.** test_colorvar_truth.py:301-370 reads `key_texts` for numbers: the field stays as it is.
- **Merge rules:** R1, R5, R7, R9.
- **For the closing sections (WP-37, WP-41, WP-42; R1-33).** `STAT_COMBOS_KNOWN` (test/test_statistical_truth.py; hygiene `TestEstimatorCombinations::test_every_known_difference_is_open`) holds documented rows that stay after 37-05 closes (A-10); `COLORVAR_KNOWN` (test/test_colorvar_truth.py; hygiene `TestTheKnownDifferences::test_every_known_difference_is_open`) holds rows keyed CV-1..CV-11 and any id the run finds. Their closing commits follow D-33-10.h and BRIEF's step (2) (`python3 test/known_differences.py <lead id>`, delete the plain rows -- or move a difference a ruling keeps into `STAT_COMBOS_DELIBERATE` or `COLORVAR_DELIBERATE` with the ruling id, D-33-10.a -- and run the hygiene command).
- **Seconds.** Report each S13 block's seconds (from its start and end lines) in the hand-back for D-33-01.i's WE step; the frame's `w33_secs` table is not edited here.
- **Commit body lines:** `Regression: test/test_statistical_truth.py::TestEstimatorCombinations::test_the_section_exists -- failed at <base> with KeyError: 'combos'`; `Fixture: test/fixtures/stat_truth.json (scripts/extract_stat_truth.do)`; `Fixture: test/fixtures/colorvar_truth.json (scripts/extract_colorvar_truth.do)`; `Flipped: test/test_colorvar_truth.py::TestAgainstTwoway::test_every_probe_partitions_the_observations_as_twoway_does -- skipping the continuous default hid CV-8, now listed`.
- **Help paragraphs owned:** none.
