# Section 33-12: Per-type by() truth and by() title positions

> Part of: WP-33 (Verification corpus and README gallery) · Items: BY-23, BY-24 · Risk: yellow · Batch: 33.4 · Depends on: 33-01, 33-10 (test/known_differences.py) · Blocks: WP-41 sections that fix the listed differences (they delete rows) · Tasks: 6, 2 commits · Case-id prefix: Q3312

## Overview

**What is wrong today.** BY-23 (with BY-31; audit :681-683, appendix :1626-1631, :3041-3047): "Per-type by() drawing is pinned against twoway only for function (default range) and lpoly". `test/test_wp31_truth.cscript:14395-14411` (U60-5) checks for histogram, kdensity, scatter, line and bar only that the drawn panel count equals `levelsof foreign` and that the saved and served glyphs match -- "it does not compare against twoway's drawing". Per panel against Stata: function (U46-04, :12968-13003, default range) and lpoly (`test/test_lpoly_rot.py::TestMapLpolyUsesTheRule::test_by_panels_use_their_own_bandwidth`, :639, parametrised saved/served; REVIEW-1 R1-37). No fixture holds twoway's per-panel data for the fits, ci bands, smooths, bins, range, pc or immediate types, "so a regression would pass". The audit's 93-command probe folder (`/private/tmp/claude-501/dropin-audit/byx/r2`) no longer exists; this section writes the probe list anew.

BY-24 (audit :696-698, appendix :1632-1638): "by() title/note/caption under position() has truth only for caption pos(5)". `scripts/extract_by_text_truth.do:155-193` (bp01-bp39) has no position() probe; twoway puts `by(foreign, note("N", position(5)))`'s N at the bottom right (x 5267) and `title("T", position(11))` at the top left (x 245). Only `test/test_legend_span_browser.py::TestByTitlesSpan` (:373) pins caption pos(5), from a 19oct2026 measurement.

**After this section.** `scripts/extract_by_types_truth.do` writes twoway's per-panel sersets for all 44 types under `by(foreign)` and `by(foreign, total)` into `test/fixtures/by_types_truth.json`; `test/test_by_types.py` compares dash's panels with them in both modes (panel count, rows, extents, sampled values), with a known-differences table keyed by GAPS4 ids. `extract_by_text_truth.do` gains 28 position() probes, and test_by_text.py's placement tests read them, with their own known table; a Chrome test compares the anchor edges for the corner clocks.

**Why one section.** Both are by() truth gaps closed by new probes and readers; neither changes dash.

**Test order and commit rule.** BY-23 (tasks 01-03), then BY-24 (tasks 04-06) on the tree BY-23's commit leaves.

### Section decisions (binding on the executor)

- **D-33-12.a Probe list (BY-23).** 44 types x 2 by() forms = 88 probes, ids `bt_<type>_by` and `bt_<type>_total`, data auto, variables chosen to match the plot dict shapes of `test/test_server_layer_defects.py::plot_for` (:82-122) so the pytest side builds the same plot: yx types `<t> mpg weight` (with `sort` for line, connected and area; the range types rline and rconnected below take `sort` too); `histogram mpg`, `kdensity mpg`; range types (rarea rbar rspike rcap rline rconnected rcapsym rscatter) `<t> mpg price weight`; rpcap rpspike `<t> mpg price foreign weight`; pc types (pcspike pcarrow pcbarrow pcscatter pccapsym) `<t> mpg weight price foreign`; `scatteri 20 3000 30 4000`; `pci 20 3000 30 4000`; `pcarrowi 20 3000 30 4000 25 2000 22 3500`; `function y = x^2`; contour and contourline `<t> price mpg weight`; tsline and tsrline on auto after `generate t = _n` and `tsset t`: `tsline mpg`, `tsrline mpg price`. Each probe: `twoway <cmd>, by(foreign[, total]) nodraw` after `capture serset drop _all` and `capture graph drop _all`.
- **D-33-12.b Sersets per panel (measured here, scratch p1).** After a by() draw, `serset dir` lists one serset per plot per panel, panel-major, the Total panel last (`(scatter)(lfit), by(foreign, total)`: 6 sersets, 52/3/22/3/74/3 rows; `kdensity mpg, by(foreign)`: 2 x 300; `histogram mpg, by(foreign)`: 7 and 4). The extractor records every serset in order (`serset set <s>`, `serset use, clear`, `ds`), its variable names, N and either all rows (N <= 41) or the 11 sampled rows of extract_stat_truth.do's `zq_curve` rule (:138-205), plus each column's min and max. `per_panel = n_sersets / n_panels`; n_panels is read from the graph (`.Graph.graphs.arrnels`, as extract_by_text_truth.do reads its panels).
- **D-33-12.c What is compared (dash side, per panel figure from `test/by_panel_probe.py::by_grid` (:98), as test_by_text.py imports it).** (1) panel count; (2) for each panel, the plot's drawn rows (the GlyphRenderer's data_source length after its CDSView filter, if any) equals the serset's N after rows with a missing coordinate are dropped, for every type except the computed curves; (3) the x and y extents of the drawn coordinates (the renderer's x-like columns `x`, `x0`, `x1`, `left`, `right`, `xs` and y-like `y`, `y0`, `y1`, `y2`, `top`, `bottom`, `ys`, finite values only; read `map_<type>` to confirm each type's columns) equal the serset's min and max within rtol 1e-9 (1e-6 for computed curves); (4) for lfit qfit fpfit lowess lpoly mband mspline kdensity function and the ci types, the sampled rows' values equal dash's curve at the same positions within rtol 1e-6 (the `_at_samples` rule of test/test_statistical_truth.py). Contour and contourline compare (1) only, plus the number of fill levels per panel (BY-28's listed difference).
- **D-33-12.d Known differences.** `BY_TYPES_KNOWN = {"<probe id>:<check>": "<GAPS4 id>"}` in test/test_by_types.py, applying 33-10's rule and value forms (test/known_differences.py, D-33-10.a: `"<id>"`, `"<id> (documented)"`, `"<id> (residual)"`; A-10: a documented or residual row stays after its item closes). Expected owners: contour/contourline levels -> `BY-28` (41-01); function's range -> `BY-27` (41-03); lowess order among ties -> the check compares sorted values (no row needed when they agree; if they still differ, the row is `"stat:PT-21 (documented)"`, 37-05's documented item); weights not used here. Any other difference stops task 03 for the maintainer. Beside the table, `BY_TYPES_DELIBERATE = {}` (D-33-10.a's companion dict for a difference a ruling keeps; empty) is passed as `deliberate=` to every `known_problems` call over `BY_TYPES_KNOWN`.
- **D-33-12.e Tiers and spread (REVIEW-1 R1-38).** Each probe is its own test, so xdist spreads the 88 builds over its workers instead of one test holding them all: `TestPanelsMatchTwoway::test_saved[<probe id>]` and `::test_served[<probe id>]`, parametrised over the module tuple `_PROBE_IDS` (the 88 ids of D-33-12.a written out, so collection never depends on the fixture), each building its probe once and asserting `known_problems(<that probe's checks>, <the BY_TYPES_KNOWN rows whose key starts "<probe id>:">, "by_types", deliberate=BY_TYPES_DELIBERATE) == []` (rule 4 holds per probe because every key carries its probe id). Saved mode runs in the default tier; served mode (`ServerAppBuilder` + `load_app` + `Document`) is `pytest.mark.batch` (it runs in `make test-all`, not `make test`). Rule 3 over every row runs once, in the default tier, in `TestTheKnownDifferences::test_every_known_difference_is_open`. The hand-back reports the measured seconds of the saved and served classes (one `--durations=0` run of each) for 50-01.
- **D-33-12.f BY-24 probes.** Appended after bp39 (:193) as bp40-bp67, text first, then clock, each `bt bp<nn> "" \`"by(foreign, <text>("X", position(<c>)))"'`: `title` at clocks 11, 12, 1, 5, 6, 7 = bp40-bp45; `subtitle` at the same six = bp46-bp51; `note` = bp52-bp57; `caption` = bp58-bp63; then `title` at 3, 9 = bp64, bp65 and `note` at 3, 9 = bp66, bp67 (28 probes). So `note("X", position(5))` is bp55 and `title("X", position(11))` is bp40. The fixture's existing per-probe record (`svg` texts with x, y, anchor; `overall`) is written for them by the script's existing code.
- **D-33-12.g BY-24 comparison.** test_by_text.py's `TestPlacementMatchesTwoway` and `TestOverallTextMatchesTwoway` already loop over every rc-0 probe, so the new probes join them; one table, `BY_POSITION_KNOWN = {"<probe>": "<GAPS4 id>", "<probe>:offset": "<GAPS4 id>"}` in test/test_by_text.py (clocks 3 and 9 -> `BY-18`, 41-05; ring(0)-like drops -> `BY-1`, 41-02; D-33-10.a's value forms), with `BY_POSITION_DELIBERATE = {}` beside it (D-33-10.a; empty), is consulted through `known_problems(..., deliberate=BY_POSITION_DELIBERATE)`. Exact offsets: `test/test_legend_span_browser.py` gains `TestByTitlesAtPosition` (release tier, both modes, the `TestByTitlesSpan` pattern; A-10: Chrome position comparisons stay in the release tier) for the corner clocks 11, 1, 5, 7: the text's anchored edge as a fraction of the graph width (twoway: x / canvas width from the fixture; dash: the text's bounding box edge / the figure root's width) agrees within 0.02, its differences read from the table's `:offset` keys. The table's hygiene, `test/test_by_text.py::TestTheFixture::test_every_known_difference_is_open` (`dead_rows(BY_POSITION_KNOWN, "by_position") == []` and every key naming a probe of the fixture), runs in the default tier, so a WP-41 closing commit that leaves a plain row fails at its own gate (REVIEW-1 R1-34).

## Risk: [yellow] -- 88 probes over 44 renderers' column shapes; served builds are slow

**Risk factors.** (1) A type's drawn columns differ from the table in D-33-12.c. (2) A twoway type refuses by() (rc != 0) -- then the probe compares rc only. (3) Served builds' time. (4) Count pins move (test_by_text.py `len(t["probes"]) == 39`).

**Mitigation.** (1) D-33-12.c says to read each mapper; the extents rule is column-name tolerant. (2) A refused probe stores `rc` and its first line; dash must answer the same rc (the check becomes rc equality). (3) D-33-12.e. (4) R10 comment `# 39 -> 67: BY-24 position() probes (WP-33)`.

## Dependencies

- **Depends on: 33-01** (GAPS4.md, the BUGS entries, test_wp33_truth.cscript) and **33-10** (batch 33.2: `test/known_differences.py`, the known-differences rule D-33-10.a).
- **Parallel batch 33.4:** with 33-04 (scripts/corpus/ dash runner, test/range_probe.py read) and 33-13 (extract_stat_truth.do, extract_colorvar_truth.do). Disjoint files. 33-04 adds no block to test_wp33_truth.cscript; this section and 33-13 each append two directly above the marker (after S11, batch 33.3), and picks.sh's `blockorder.py` puts S12 before S13 when they merge (REVIEW-1 R1-31).

## Evidence

- U60-5 (test_wp31_truth.cscript:14395-14411): the five types, `_u60_compare` comparing saved with served only.
- `test/test_by_text.py`: `_probe_spec` (:83-95) parses `options` with `dr._dash_by_tokens`; `_draw(mode, spec)` (:109-143) returns panels, head, foot; `TestTheFixture::test_meta_and_probes` pins `len(t["probes"]) == 39` (:187) and bp32/bp35 rc 198; `TestPlacementMatchesTwoway::test_sides_and_alignment` (:243-291) maps SVG anchors to Bokeh alignment and the y order to above/below.
- `scripts/extract_by_text_truth.do`: probe program `bt id "if" "options"` (:141-153 region: per-panel `.Graph.graphs[k]` texts and serset N, SVG export), probes :155-193.
- `test/test_legend_span_browser.py:373` `TestByTitlesSpan` (caption pos(5) ends at 4257.4, or 5267.2 with span, 19oct2026).
- Serset order: measured here (D-33-12.b).
- `test/test_server_layer_defects.py:70-122`: `_RANGE`, `_PC`, `_RANGEPT`, `ALL_TYPES = sorted(dr._dash_plot_type_names())`, `plot_for`.

## User stories

- **US-33-12.1** As the Stata user with an existing by() command of any plot type, I want each panel drawn from that panel's data as twoway draws it, so that a fit or band per group is right.
- **US-33-12.2** As the Stata user, I want by()'s title, subtitle, note and caption at the clock position I gave, so that the graph's layout is twoway's.

## Business requirements

- **BR-33-12.1** For every plot type under by(foreign) and by(foreign, total), each panel's rows, extents and computed values equal twoway's, in both modes, or the difference is listed under a live GAPS4 row (D-33-10.a).
- **BR-33-12.2** by()'s four texts at clocks 11, 12, 1, 5, 6, 7, 3 and 9 are measured, and dash's side, alignment and corner offsets compared.

## Technical requirements

- **TR-33-12.1 (BY-23 extract)** Create `scripts/extract_by_types_truth.do` on the form of extract_by_text_truth.do (root guards, `set graphics off`, `version 19`, `set linesize 255`, a record file read by one trailing python block that never calls Stata; a backtick written `\x60`): the probe program `zbt id "cmd" "byopts"` runs `capture noisily twoway <cmd>, by(foreign<byopts>) nodraw` under a text log, records rc and the first line, and on rc 0 records `.Graph.graphs.arrnels` (panels), `serset dir`'s count, and every serset per D-33-12.b (a helper `zbt_serset` that loads with `serset use, clear`, renames inside the program as `zq_serset` does, extract_stat_truth.do:207-238, and writes rows with `string(<v>, "%20.17g")`). Fixture `test/fixtures/by_types_truth.json`: `{"_meta": {...five keys...}, "data": <the StataJSON of auto's mpg weight price foreign plus t>, "probes": {id: {"cmd", "by", "rc", "first_line", "n_panels", "sersets": [{"vars", "n", "rows" | "sample_index" + "samples", "min", "max"}]}}}`. GENERATORS row `"by_types_truth.json": "scripts/extract_by_types_truth.do"`.
- **TR-33-12.2 (BY-23 test)** Create `test/test_by_types.py`: `_by_spec(probe)` builds `{"graphs": [{"name": "g1", "plots": [plot_for-shaped dict for the probe's type and variables], "graph_options": {"name": "g1", "by": "foreign" or "foreign, total"}, "if_expr": "", "in_expr": ""}], "kpis": [], "build_options": <the test_by_text.py `_spec` build options>}` (tsline/tsrline: xvar `t`); `_draw(mode, spec)` copied from test_by_text.py:109-143 (or imported); `_panel_checks(probe, panels) -> {key: None | difference}` implementing D-33-12.c; `_PROBE_IDS` (D-33-12.e); classes `TestTheFixture::test_meta_and_probes` (88 probes, their ids equal to `_PROBE_IDS`, five meta keys), `TestPanelsMatchTwoway::test_saved[<probe id>]` and `::test_served[<probe id>]` (`@pytest.mark.batch`) by D-33-12.e, and `TestTheKnownDifferences::test_every_known_difference_is_open` (`dead_rows(BY_TYPES_KNOWN, "by_types") == []`, D-33-10.a's rule 3; every key's probe id in `_PROBE_IDS` and its check one of D-33-12.c's names).
- **TR-33-12.3 (BY-23 block)** `* ==== S12 BY-23: per-type by() truth ====`, directly above the marker (after S11), in BRIEF's block form (gate `WP33_ONLY`, `S12 start`/`S12 end` lines): `sysuse auto`; `twoway lfit mpg weight, by(foreign) nodraw`; sersets 0 and 1: N and the first row's two values equal the fixture's `bt_lfit_by` within 1e-9 (a python helper reads the fixture); same for `kdensity mpg, by(foreign, total)` (3 sersets of 300); `_w33_expect Q3312-1 ...`; `_w33_done Q3312-1 "twoway's per-panel sersets are the committed truth"`.
- **TR-33-12.4 (BY-24 extract)** Append D-33-12.f's 28 `bt` lines after :193 of scripts/extract_by_text_truth.do; regenerate.
- **TR-33-12.5 (BY-24 tests)** test/test_by_text.py: `BY_POSITION_KNOWN = {}` and `BY_POSITION_DELIBERATE = {}`; `TestPlacementMatchesTwoway` and `TestOverallTextMatchesTwoway` collect `{pid: None | difference}` and assert `known_problems(<them>, <the rows without :offset>, "by_position", deliberate=BY_POSITION_DELIBERATE) == []` over the keys without `:offset` (`# Flipped (WP-33 BY-24): the loops compare every probe; a listed difference belongs to its item`); `TestTheFixture` 39 -> 67 with the R10 comment, and `TestTheFixture::test_every_known_difference_is_open` (D-33-12.g). test/test_legend_span_browser.py: `TestByTitlesAtPosition` (D-33-12.g), reusing that file's Chrome page helpers and importing `BY_POSITION_KNOWN` from test_by_text.py (its `:offset` keys).
- **TR-33-12.6 (BY-24 block)** `* ==== S12 BY-24: by() text positions ====`, directly after `* ==== end S12 ====` of the BY-23 block (so above the marker), in BRIEF's block form, drawing exactly as extract_by_text_truth.do's `bt` draws: under `set scheme stcolor` (the script's scheme, :71; the session's scheme saved first in a local and restored at the block's end, never `permanently`), on `sysuse auto, clear` (`bt.dta` is auto with four added variables, its mpg, weight and foreign unchanged and in auto's order, :96-106), `twoway scatter mpg weight, by(foreign, note("X", position(5))) name(Graph, replace)` against bp55, and `twoway scatter mpg weight, by(foreign, title("X", position(11))) name(Graph, replace)` against bp40. For each (first bp55, then bp40): `local pid "<bp55 or bp40>"`, the draw, `cert_svg_export, name(Graph) file("\`w33_work'/s12_\`pid'.svg")`, `local svg "\`r(file)'"`, `cert_svg_texts, file("\`svg'")` (it writes the texts list and clobbers `r()`), `local tlist "\`r(list)'"`, then `python: __import__("__main__")._w33s12_text_x()` -- a top-level python helper directly above the BY-24 header, which reads the locals `tlist` and `pid` with `Macro.getLocal` (no macro expanded into Python text) and sets the locals `x` (the x of the list's first text `X`, `.` when there is none) and `fx` (the x of the first text `X` in `fixtures/by_text_truth.json`'s `probes[pid]["svg"]`; each probe draws one, measured: bp36's `title("X", ring(0))` holds one `X`); `_w33_expect Q3312-2 "(abs(\`x' - \`fx') <= 1)" "<pid>: X at x \`x', the fixture's \`fx'"`; `_w33_done Q3312-2 "by()'s note at clock 5 and title at clock 11 are where the committed truth puts them"`.
- **TR-33-12.7 Maps.** None (no dash code).

## Boundaries

- No edit of dash.ado, dash_parse.mata or dash_render.py; `_dash_by_chrome`, `_dash_text_annotations` belong to 41-02. No help edit.
- Do not change bp01-bp39 (their pins stay).
- No `graph set`; scheme stays the session default except where a probe names one.

## Stata truth

`scripts/extract_by_types_truth.do` (new, 88 probes) and `scripts/extract_by_text_truth.do` (28 probes added), each run once: `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s12 $WT/scripts/<script>`; `git add -f` both fixtures. Live cases Q3312-1, Q3312-2.

## TDD test stubs

BY-23 (red at the base):
- Test: `test/test_by_types.py::TestTheFixture::test_meta_and_probes` -- red: no fixture.
- Test: `test/test_by_types.py::TestPanelsMatchTwoway::test_saved[<probe id>]` (88), `::test_served[<probe id>]` (88, batch), `TestTheKnownDifferences::test_every_known_difference_is_open`.
- cscript: `Q3312-1`.

BY-24 (red after BY-23's commit):
- Test: `test/test_by_text.py::TestTheFixture::test_meta_and_probes` with 67 -- red: 39 probes.
- Test: `test/test_by_text.py::TestPlacementMatchesTwoway::test_sides_and_alignment[saved|served]` over bp40-bp67.
- Test: `test/test_by_text.py::TestTheFixture::test_every_known_difference_is_open` (default tier).
- Test: `test/test_legend_span_browser.py::TestByTitlesAtPosition::test_the_corner_clocks[saved|served]` (release).
- cscript: `Q3312-2`.

Flips: test_by_text.py's two loop assertions (TR-33-12.5) and the count pin.

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| per-panel data, 44 types x 2 | pytest, one test per probe (saved default tier, served batch tier) | by_types_truth.json | yes |
| known-table hygiene (both tables) | pytest, default tier | by_types_truth.json, by_text_truth.json, GAPS4.md | -- |
| twoway drift | cscript Q3312-1 | by_types_truth.json | -- |
| text side and alignment, 67 probes | pytest | by_text_truth.json | yes |
| corner offsets | pytest release, Chrome | by_text_truth.json | yes |
| twoway drift | cscript Q3312-2 | by_text_truth.json | -- |

- **AC-33-12.1** test_by_types.py green in both modes with only open-item rows; Q3312-1 and Q3312-2 PASS.
- **AC-33-12.2** by_text_truth.json holds 67 probes; test_by_text.py and TestByTitlesAtPosition green.
- **AC-33-12.3** Two commits ending `(WP-33 BY-23)` and `(WP-33 BY-24)`.

## Tasks

**Commit boundary.** 33-12-01..03: BY-23, subject `Measure every plot type's per-panel data under by() and compare both modes with it (WP-33 BY-23)`. 33-12-04..06: BY-24, subject `Measure by()'s titles and notes at each clock position and compare their placement (WP-33 BY-24)`. Branch `wp33-s12` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp33-s12`.

**Closing steps** (BRIEF "The corpus ledger and the known-differences tables", steps (1)-(3), and "Pull form"; D-33-10.h). Each closing task (33-12-03 for BY-23, 33-12-06 for BY-24) runs them in `$WT` before staging. Batch 33.4 lands before the corpus ledger (scripts/corpus/ledger.tsv and ledger.py, 33-05, batch 33.5) and the guard (Q3309-1, 33-09, batch 33.6) exist, so steps (1) and (3) have nothing to run on yet (BRIEF applies them from WP-34 on; 33-14 runs all three for TR-2 in batch 33.7); step (2) runs for the item's lead id `<id>`: run `python3 test/known_differences.py <id>` (33-10, D-33-10.h) and delete every `<file>:<line>` row it prints from its `*_KNOWN` table, staging each file edited; a difference the item's ruling keeps moves instead into that table's deliberate dict -- `DELIBERATE` for `VALUE_KNOWN` (test/value_truth_known.py), `ABBREV_DELIBERATE` for `ABBREV_KNOWN` (test/test_abbreviations.py), and `SCALE_FRAME_DELIBERATE`, `BY_TYPES_DELIBERATE`, `BY_POSITION_DELIBERATE`, `STAT_COMBOS_DELIBERATE` or `COLORVAR_DELIBERATE` beside 33-11..33-13's `SCALE_FRAME_KNOWN`, `BY_TYPES_KNOWN`, `BY_POSITION_KNOWN`, `STAT_COMBOS_KNOWN` and `COLORVAR_KNOWN` -- as `"<key>": "<ruling id>: <what is kept>"`, the ruling id a DECISIONS or index id (P4-n, A-n, Q-n, M-n) (no ruling of this section keeps a difference, so nothing is expected to move); then run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`), 0 failed. No row keyed to the closing item's own id is expected: BY_TYPES_KNOWN and BY_POSITION_KNOWN key each difference to the item that fixes or documents it (D-33-12.d, D-33-12.g), so they stay live when this item closes. Then it pulls from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main), runs `node .gitnexus/run.cjs detect-changes --scope all --repo .` and commits.

<task type="auto" id="33-12-01">
  <name>Write BY-23's failing tests</name>
  <files>test/test_by_types.py, test/test_wp33_truth.cscript</files>
  <action><![CDATA[In worktree $WT (wp33-s12) create test/test_by_types.py (TR-33-12.2, `BY_TYPES_KNOWN = {}` and `BY_TYPES_DELIBERATE = {}`) and append the S12 BY-23 block (TR-33-12.3) above the marker. Run `python3 -m pytest test/test_by_types.py -q -n0 -p no:cacheprovider > <scratch>/s12/01.log 2>&1` and save the failures (no fixture) to <scratch>/33-12-01-failure.txt. Do not commit.]]></action>
  <verify><![CDATA[`grep -c "FAILED\|ERROR" <scratch>/s12/01.log` is at least 1; `test -s <scratch>/33-12-01-failure.txt`.]]></verify>
  <done>BY-23's comparison tests existed and failed for want of the truth.</done>
</task>

<task type="auto" id="33-12-02">
  <name>Measure twoway's per-panel sersets</name>
  <files>scripts/extract_by_types_truth.do, test/fixtures/by_types_truth.json, test/test_fixtures_are_committed.py</files>
  <action><![CDATA[Create scripts/extract_by_types_truth.do (TR-33-12.1, D-33-12.a/b), add the GENERATORS row, run it through the slot, `git add -f test/fixtures/by_types_truth.json`. Run the S12 BY-23 block with `WP33_ONLY=S12` (Q3312-1 PASS) and `python3 -m pytest test/test_fixtures_are_committed.py "test/test_by_types.py::TestTheFixture" -q -p no:cacheprovider`.]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/by_types_truth.json'));p=d['probes'];print(len(p), sum(1 for v in p.values() if v['rc']==0))"` prints 88 and the number twoway drew; the two pytest targets pass; the driver log shows `Q3312-1 PASS`.]]></verify>
  <done>twoway's per-panel data for all 44 types under both by() forms were committed truth.</done>
</task>

<task type="auto" id="33-12-03">
  <name>List differences and commit BY-23</name>
  <files>test/test_by_types.py</files>
  <action><![CDATA[Run `python3 -m pytest test/test_by_types.py -q -n 8 -p no:cacheprovider --durations=0` and `DASH_TEST_TIER=batch python3 -m pytest test/test_by_types.py -k test_served -q -n 8 -p no:cacheprovider --durations=0` (record each class's seconds for the hand-back, D-33-12.e). For each problem `known_problems` reports, add the row by D-33-12.d; a difference with no owner stops the task (hand back the probe, check and both values). Close the BY-23 BUGS entry (title `GAPS4_OPEN["BY-23"]`): `Fixed <ddmonyyyy> (WP-33, BY-23). scripts/extract_by_types_truth.do records twoway's per-panel sersets for all 44 types under by(foreign) and by(foreign, total); test/test_by_types.py compares each panel's rows, extents and sampled values in both modes (served in the batch tier), differences listed under <ids>. Pinned by test/test_by_types.py::TestPanelsMatchTwoway, test/test_wp33_truth.cscript Q3312-1; fixture test/fixtures/by_types_truth.json. Closes GAPS4 BY-23 (WP-33, BY-23).`; `- [x]`; Tracked Closed `commit pending`; delete `"BY-23"` from `GAPS4_OPEN` in test/test_tracking_documents.py; CHANGELOG `- Every plot type's by() panels are compared with twoway's per-panel data (WP-33, BY-23)`. No existing function is edited (new files, a GENERATORS row and a new block), so no impact run is needed. Run the Closing steps for BY-23 (Tasks): steps (1) and (3) have nothing to run on at batch 33.4 (no ledger, no guard yet); (2) run `python3 test/known_differences.py BY-23`, delete every row it prints (none expected; nothing moves to a deliberate dict) and run the hygiene command it prints. Pull from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main); run `node .gitnexus/run.cjs detect-changes --scope all --repo .`; commit (body adds `Seconds: S12 BY-23 <n>; test_saved <n> s, test_served <n> s`).]]></action>
  <verify><![CDATA[Both pytest runs pass; `python3 test/known_differences.py BY-23` prints no `<file>:<line>` row and the hygiene command it prints reports 0 failed; `git log -1 --format=%s` ends `(WP-33 BY-23)`; the claude|anthropic grep prints 0.]]></verify>
  <done>BY-23 was closed with per-type by() truth compared in both modes.</done>
</task>

<task type="auto" id="33-12-04">
  <name>Write BY-24's failing tests</name>
  <files>test/test_by_text.py, test/test_legend_span_browser.py</files>
  <action><![CDATA[Run `node .gitnexus/run.cjs impact "<name>" --direction upstream --repo .` for `test_meta_and_probes`, `test_sides_and_alignment` and the `TestOverallTextMatchesTwoway` method you edit, and note the results (an UNKNOWN is unresolved: confirm with `grep -rn "<name>" test/`). Apply TR-33-12.5 to test/test_by_text.py (the 67 pin, `BY_POSITION_KNOWN = {}` and `BY_POSITION_DELIBERATE = {}`, the loops through `known_problems`, the hygiene test) and add `TestByTitlesAtPosition` to test/test_legend_span_browser.py. Run `python3 -m pytest test/test_by_text.py -q -n0 -p no:cacheprovider -k "TestTheFixture" > <scratch>/s12/04.log 2>&1` and save the failure (39 probes) to <scratch>/33-12-04-failure.txt. Do not commit.]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/s12/04.log` prints 1; `test -s <scratch>/33-12-04-failure.txt`.]]></verify>
  <done>BY-24's tests existed and failed on the committed fixture.</done>
</task>

<task type="auto" id="33-12-05">
  <name>Add the position() probes and regenerate</name>
  <files>scripts/extract_by_text_truth.do, test/fixtures/by_text_truth.json, test/test_wp33_truth.cscript</files>
  <action><![CDATA[Append D-33-12.f's 28 probes after :193 of scripts/extract_by_text_truth.do (re-read :141-193 first), run it through the slot, `git add -f test/fixtures/by_text_truth.json`; confirm bp01-bp39's records are unchanged (`python3 -c` diff of the two files' bp01-bp39 entries, old from `git show HEAD:test/fixtures/by_text_truth.json`); a changed old record is a Stata drift finding to report, not to hide. Append the S12 BY-24 block (TR-33-12.6) and run it (Q3312-2 PASS).]]></action>
  <verify><![CDATA[`python3 -c "import json;print(len(json.load(open('test/fixtures/by_text_truth.json'))['probes']))"` prints 67; the old-record diff prints nothing; the driver log shows `Q3312-2 PASS`.]]></verify>
  <done>by()'s texts at eight clock positions were committed truth beside the unchanged earlier probes.</done>
</task>

<task type="auto" id="33-12-06">
  <name>List placement differences and commit BY-24</name>
  <files>test/test_by_text.py, test/test_legend_span_browser.py</files>
  <action><![CDATA[Run `python3 -m pytest test/test_by_text.py -q -n 8 -p no:cacheprovider` and `DASH_TEST_TIER=release python3 -m pytest "test/test_legend_span_browser.py::TestByTitlesAtPosition" -q -n0 -p no:cacheprovider`; add each reported difference to BY_POSITION_KNOWN (an offset difference under its `<probe>:offset` key) by D-33-12.g; an ownerless difference stops the task. Close the BY-24 BUGS entry: `Fixed <ddmonyyyy> (WP-33, BY-24). scripts/extract_by_text_truth.do measures by()'s title, subtitle, note and caption at clocks 11, 12, 1, 5, 6, 7, 3 and 9 (bp40-bp67); test/test_by_text.py compares side and alignment in both modes and test/test_legend_span_browser.py::TestByTitlesAtPosition the corner offsets in Chrome, differences listed under <ids>. Pinned by those, test/test_wp33_truth.cscript Q3312-2; fixture test/fixtures/by_text_truth.json. Closes GAPS4 BY-24 (WP-33, BY-24).`; `- [x]`; Tracked Closed `commit pending`; delete `"BY-24"` from `GAPS4_OPEN` in test/test_tracking_documents.py; CHANGELOG `- by()'s titles and notes at each clock position are compared with twoway's (WP-33, BY-24)`. Run the Closing steps for BY-24 (Tasks): steps (1) and (3) have nothing to run on at batch 33.4 (no ledger, no guard yet); (2) run `python3 test/known_differences.py BY-24`, delete every row it prints (none expected; nothing moves to a deliberate dict) and run the hygiene command it prints. Pull from local main with `git -C $WT pull --ff-only . main` (BRIEF "Pull form"; a no-op when the batch base already contains main); run `node .gitnexus/run.cjs detect-changes --scope all --repo .`; commit with the `Flipped:` lines (body adds `Seconds: S12 BY-24 <n>`).]]></action>
  <verify><![CDATA[Both runs pass; `python3 test/known_differences.py BY-24` prints no `<file>:<line>` row and the hygiene command it prints reports 0 failed; `git log -1 --format=%s` ends `(WP-33 BY-24)`; the claude|anthropic grep prints 0.]]></verify>
  <done>BY-24 was closed with position() truth compared in both modes.</done>
</task>

## Section completion criteria

- Two commits (BY-23, BY-24); two fixtures from committed scripts; test_by_types.py, test_by_text.py and TestByTitlesAtPosition green; Q3312-1, Q3312-2 PASS; every known row is live (D-33-10.a rule 3).

## Notes

- **Serset reading.** `serset use` names columns `__00000k`, which Stata drops as temporaries when the program returns: rename inside the program (extract_stat_truth.do:198-206 explains). A kdensity serset can carry the raw variable and be as long as the data: drop rows missing in the first column (:229-233).
- **tsline** needs `tsset t`; reload auto for every probe after it.
- **Merge rules:** R1, R5, R7, R9/R10; no JS, no served copy list.
- **For the closing sections (WP-37, WP-41; R1-33).** `BY_TYPES_KNOWN` (test/test_by_types.py; hygiene `TestTheKnownDifferences::test_every_known_difference_is_open`) and `BY_POSITION_KNOWN` (test/test_by_text.py; hygiene `TestTheFixture::test_every_known_difference_is_open`) list rows keyed BY-28, BY-27, BY-18, BY-1 and any id the run finds; their closing commits follow D-33-10.h (`python3 test/known_differences.py <lead id>`). A Fix item's closing commit whose ruling keeps a listed difference moves that key into `BY_TYPES_DELIBERATE` or `BY_POSITION_DELIBERATE` with the ruling id (D-33-10.a); the `"<id> (documented)"` form is only for a Kind Document item's row (stat:PT-21's, D-33-12.d), which stays after 37-05 closes it (A-10).
- **Seconds.** Report each block's seconds (from its `S12 start`/`S12 end` lines) in the hand-back for D-33-01.i's WE step; the frame's `w33_secs` table is not edited here.
- **Commit body lines:** `Regression: test/test_by_types.py::TestTheFixture::test_meta_and_probes -- failed at <base> with FileNotFoundError`; `Fixture: test/fixtures/by_types_truth.json (scripts/extract_by_types_truth.do)`; `Fixture: test/fixtures/by_text_truth.json (scripts/extract_by_text_truth.do)`; `Flipped: test/test_by_text.py::TestTheFixture::test_meta_and_probes -- 39 probes was the pre-BY-24 count`.
- **Help paragraphs owned:** none.
