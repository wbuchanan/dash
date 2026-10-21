# Section 37-02: rarea outlines break at gaps; contour key without a surface

> Part of: WP-37 (Statistical and computed layers) · Items: DG-5, DG-8 · Risk: yellow · Batch: 37.2 · Depends on: 37-01 · Blocks: 37-03 · Tasks: 3, 2 commits · Case-id prefix: Q3702

## Overview

**What is wrong today.** DG-5 (audit :643-645; appendix :3278-3283): "rarea with cmissing(n) draws its bound outlines across the gaps". `rarea lo hi weight in 1/20, cmissing(n) sort` in twoway draws one closed polygon per run of complete rows and nothing in a gap or for an isolated observation (area_cmissing_truth.json R02: three polygons). dash splits the fill correctly, but `map_rarea` (dash_render.py:22849) draws the two bound Lines on the rebuilt fill source (:22995-22998), whose zero-height gap vertices hold no NaN, so diagonal outline segments join the polygons across each gap and a spike stands at the lone observation (screenshots d_M05.png against t_M05.png). `map_area` routes its outline through `_dash_join_glyph` (:18718-18728), which breaks it; rarea does not, and no test checks rarea's outline (test_area_cmissing.py has `test_the_outline_breaks` for area only, :235).

DG-8 (audit :649-651; appendix :3296-3301): "A contour with no surface (two observations) draws no colour key". `twoway contour price mpg weight in 1/2` draws an empty plot and a four-band colour key labelled 4,000 to 4,800, titled Price (re-measured 20oct2026: SVG labels `4,000 4,200 4,400 4,600 4,800`, four key boxes, title `Price`). `map_contour` draws the key only `if not lines_only and drawable` (:24477-24478), and two points are `degenerate`, so no key.

**What will be true after.** Ruling M11-style fix (D40 left these open; Appendix A Kind = Fix): rarea's bound outlines are drawn through `_dash_join_glyph` from their own sources, so cmissing(n) breaks them where it breaks the fill, in both modes and after a filter move on the saved page; a contour whose surface cannot be drawn but whose z values exist draws its key from the levels it would cut at, in both modes. The two items share a section because both are small, late-drawing fixes in the same mappers' family and the batch's JS editor is this section (rarea's outline sources are rebuilt by the saved page's join code).

**Test order and commit rule.** Two items, two commits: DG-5 then DG-8. Task 37-02-01 writes DG-5's failing tests and S02 block and saves the failure text, no commit; 37-02-02 fixes DG-5 and commits `(WP-37 DG-5)`; 37-02-03 writes DG-8's tests red, fixes it and commits `(WP-37 DG-8)`.

### Section decisions

- **D-37-02.a rarea's outline sources.** Each bound Line gets a `ColumnDataSource` of its own holding the x column, that bound's column and the row id, taken from the columns as they were before `_dash_fill_rebuild` replaced the fill source's data, and is drawn by `_dash_join_glyph(self, fig, <options without connect>, dict(x=xvar, y=<bound>, source=<its source>, line_color=..., line_alpha=..., line_width=..., line_dash=...), role="aline")`, so its NaN breaks and `_dash_join` record are area's. Without cmissing(n) or a join style (`_expand` false) the outline stays on the fill source exactly as today.
- **D-37-02.b The saved page after a move.** The join rebuild the saved page already runs for every source carrying `_dash_join` (WP-31 H1/C6) rebuilds the outline sources; if the move parity entry shows the saved and served outlines differ, the twin is fixed in `_FILTER_JS`'s join rebuild (this section is batch 37.2's JS editor, R12) -- not by a new branch.
- **D-37-02.c The key without a surface.** Drawn whenever the layer is a filled contour and `math.isfinite(zmin)`; its levels are `_dash_contour_fill_levels(cuts, ticks, zmin, zmax)`, the ones `lv` already holds. A constant z (zmin == zmax) keeps today's key. Zero rows keep 37-01's empty key.

## Risk: [yellow] -- rarea's outline renderers move to new sources

**Why.** Saved-page moves, hover and legends read rarea's renderers; the served redraw pairs sources by position.

**Risk factors.** 1. The served redraw pairs a layer's sources by position (the `_dash_contour_sources` note shows the pattern); two new sources change rarea's source list. 2. The legend reads the fill first; the outlines must stay after it. 3. `_dash_rarea_one_bound` (:22915) rewrites columns before the expansion. 4. The key must not appear on contourline.

**Mitigation.** 1. TestBothModes and a MOVE_CORPUS entry compare the served redraw with the saved move. 2. The outlines are drawn after the VArea, as now. 3. The outline sources are built from `_cols` after `_dash_rarea_one_bound` and before `_dash_fill_rebuild`. 4. The condition keeps `not lines_only`.

## Dependencies

- **Depends on:** 37-01 (its empty-contour branch in `map_contour`; DG-8 edits the key condition next to it).
- **Blocks:** 37-03 (it edits `map_contour`'s surface after this section).
- **Parallel batch:** 37.2, alone.

## Evidence

### rarea (dash_render.py, re-read)

```python
22915             _cols, _ord = _dash_rarea_one_bound(_cols, _ord, xvar, y1var,
...
22921         if _expand:
22922             _ok = (np.isfinite(_cols[xvar]) & np.isfinite(_cols[y1var])
22923                    & np.isfinite(_cols[y2var]))
22924             _xi, _yi, _col = _dash_fill_vertices(_cols[xvar], _ok, _style,
22925                                                  _cmiss)
22926             _gap_rid = source.data.get(_ROW_ID_COLUMN)
22927             # A gap's zero-height pair sits on the lower bound.
22928             source.data = _dash_fill_rebuild(source.data, xvar,
...
22994         _outlines = []
22995         for _yb in (y1var, y2var):
22996             _o = fig.line(x=xvar, y=_yb, source=source,
...
23004             _o.tags = ["dash_rarea_outline"]
23005             self._apply_line_opts(_o, _lo, role="aline")
```
Helpers: `_dash_join_glyph` (:59766), `_dash_fill_vertices` (:59843), `_dash_fill_rebuild` (:59916), `_dash_fill_join` (:59956); JS `dash_fill_vertices` (:31933). area's outline: :18700-18728.

### contour key (re-read after 37-01 landed)

`lv = _dash_contour_fill_levels(cuts, ticks, zmin, zmax)` (:24411-24412); `drawable` (:24379-24381: not degenerate, a 2x2 grid, a finite node, a finite zmin); key `if not lines_only and drawable: self._contour_key(fig, cr, ticks, lo, hi, zvar, zmin, zmax)` (:24477-24478).

### Truth

- test/fixtures/area_cmissing_truth.json `R02` (`twoway rarea lo hi weight in 1/20, cmissing(n) sort`): `polys` / `paths` -- three closed polygons; the outline of each polygon is its own path.
- DG-8 (session w5/p1, 20oct2026): `twoway contour price mpg weight in 1/2`: rc 0; key labels `4,000`, `4,200`, `4,400`, `4,600`, `4,800`; four key paths; title `Price`.

### Tests today

test/test_area_cmissing.py `TestRareaConnect` (:248-279: `test_stairs`, `test_split` check the VArea only), `_line_runs` helper (used by area's `test_the_outline_breaks`, :235-240); contour key tests in test/test_contour*.py (grep `_contour_key\|ColorBar`).

## User stories

- US-37-02.1 As a Stata user drawing a confidence band with gaps (`rarea lo hi x, cmissing(n)`), I want no outline across the gaps, as twoway draws it.
- US-37-02.2 As a Stata user, I want a contour whose surface cannot be drawn to still show its colour key, as twoway does.

## Business requirements

- BR-37-02.1 (DG-5) Under cmissing(n), each rarea bound's outline has a break wherever the fill has one, and draws nothing for an isolated observation, in both modes and after a filter move.
- BR-37-02.2 (DG-8) A filled contour over data whose z has a range draws its colour key with twoway's levels even when no surface is drawn, in both modes.

## Technical requirements

- **TR-37-02.1 (DG-5).** In `map_rarea`, inside `if _expand:` and before `source.data = _dash_fill_rebuild(...)`, keep `_ol_data = {xvar: np.asarray(_cols[xvar], float), _ROW_ID_COLUMN: list(_gap_rid) if _gap_rid is not None else None}` and the two bounds' arrays; replace the outline loop (:22994-23006) with: when `_expand`, for each `_yb` build `ColumnDataSource({xvar: x, _yb: y, _ROW_ID_COLUMN: rid})` (the row id omitted when `_gap_rid` is None) and call `_o = _dash_join_glyph(self, fig, dict(_lo, cmissing=options.get("cmissing", ""), connect=_style), dict(x=xvar, y=_yb, source=_osrc, line_color=_b["line"], line_alpha=(1.0 if _b.get("line_alpha") is None else _b["line_alpha"]), line_width=_b["line_width"], line_dash=list(_b.get("line_dash") or [])), role="aline")` -- the options are `_lo` (the acolor/alcolor/alwidth/alpattern folds of :22991-22995) with rarea's own `connect` style kept (`_style`, the fill's, which `_dash_join_spec` (:59700) reads from `options["connect"]` beside `options["cmissing"]`; area drops `connect` because area ignores it, rarea does not), and `line_alpha` exactly as the loop at :22998-23001 computes it (REVIEW R3-20); then `_o.tags = ["dash_rarea_outline"]`. When not `_expand`, today's loop unchanged. `_dash_join_glyph` already calls `_apply_line_opts(r, options, role=role)`: do not call it twice. `_ROW_ID_COLUMN` above stands for the row-id column name exactly as `map_rarea` reads it at the batch-37.2 base (the key `_gap_rid` is read with; 35-08 made the name per-spec): use that same expression, never the 090d928 constant.
- **TR-37-02.2 (DG-5) saved page.** No new JS unless the move parity entry fails; then fix the join rebuild in `_FILTER_JS` that handles sources with `_dash_join` (find it with `grep -n "_dash_join" dash_render.py` in the `_FILTER_JS` text) so it rebuilds the outline sources from the kept rows (the twin of `_dash_join_vertices`), with a node test through test/js_runner.py's `run_filter_js_block` (R8).
- **TR-37-02.3 (DG-8).** In `map_contour` replace `if not lines_only and drawable:` (the drawn-key call) with `if not lines_only and math.isfinite(zmin) and math.isfinite(zmax) and not _no_rows:` (37-01's `_no_rows`; re-read its name); `lo, hi` are `lv[0], lv[-1]` from the fill branch, which runs whether or not the surface is drawable. A degenerate layer's band renderer stays the stub grid.
- **TR-37-02.4 Help (R3).** dash.sthlp contour paragraph (`{marker plottypes}` contour entry; find "draws no colour key" or the degenerate sentence with `grep -n -i 'degenerate\|no surface' dash.sthlp`): state "A {cmd:contour} over too few points to make a surface -- two observations, or points on one line -- draws its colour key from its levels, as {cmd:twoway} does." The rarea paragraph that states cmissing(n) (grep `cmissing(n)` near rarea) adds "the outline breaks where the fill does".

## Boundaries

- No change to rarea's fill, its one-bound rule, its legend item or `map_area`.
- No change to the contour surface, its cuts or the capped path (37-03 owns the surface).

## Stata truth

DG-5's truth is the committed fixture `area_cmissing_truth.json` R02 (no new extract). DG-8 measured live in the block. Blocks in test/test_wp37_truth.cscript in section order (BRIEF "Block order"; REVIEW R3-11): batch 37.1 landed S01, S04 and S05, so each S02 block is inserted directly above the first `* ==== S04 ` header line (above the marker only if no block with a higher section number exists), DG-5's before DG-8's; the closing task of each item runs `python3 -m pytest test/test_cscript_hygiene.py -k TestTheWpTruthScripts -q -n0 -p no:cacheprovider` (33-01's reader: blocks gated, timed and in non-decreasing section order):
- `* ==== S02 DG-5: rarea outlines break at gaps ====` -- Q3702-1: `dash rarea lo hi weight in 1/20, cmissing(n) sort saving(<tmp>.html, replace)` (the data as area_cmissing_truth.json's extract makes it: read scripts/extract_area_cmissing_truth.do for `lo` and `hi`) writes a page whose two rarea outline Lines (tag `dash_rarea_outline`) each have three NaN-separated runs and no run spans a gap of the fill (python helper over the page JSON).
- `* ==== S02 DG-8: contour key without a surface ====` -- Q3702-2: `capture noisily twoway contour price mpg weight in 1/2` and `graph export <tmp>.svg` give the key labels (cert_svg_texts) `4,000 ... 4,800`; `dash contour price mpg weight in 1/2, saving(...)` writes a page with one ColorBar titled `Price` whose ticks equal those five values.

## TDD test stubs

- DG-5 (task 01): test/test_area_cmissing.py::TestRareaConnect::test_the_outline_breaks[mode] (new node in the existing class: `_line_runs(fig)` over the two outline Lines is six runs, three each, matching R02's three polygons; red: two runs); ::test_no_outline_spike_at_a_lone_point[mode]; test/test_area_cmissing.py::TestRareaConnect::test_the_outline_follows_a_move (saved page through js_runner after a dropdown move: the outline sources' runs equal the served redraw's); cscript Q3702-1; parity `MOVE_CORPUS` entry "DG-5: rarea cmissing(n) outline, dropdown move" (R8).
- DG-8 (task 03): test/test_contour_key_degenerate.py::TestTheKey::test_two_points_draw_a_key[std|srv] (one ColorBar; title Price; ticks 4000..4800 by 200), ::test_contourline_draws_no_key[std|srv] (guard), ::test_constant_z_unchanged[std|srv] (guard); cscript Q3702-2; parity `CORPUS` entry "DG-8: contour over two observations".

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| rarea outline runs | pytest TestRareaConnect new nodes; cscript Q3702-1 | area_cmissing_truth.json R02 | yes (+ saved move) |
| outline after a move | js_runner node; MOVE_CORPUS entry | -- | yes |
| key without surface | pytest test_contour_key_degenerate.py; cscript Q3702-2 | live twoway SVG | yes |
| no plain DG-5 / DG-8 ledger or known-differences row; guard verdicts unchanged or regenerated | pytest test_corpus_ledger.py; `python3 test/known_differences.py <id>` and its hygiene command; S09 block of test_wp33_truth.cscript (`WP33_ONLY=S09`) | corpus_ledger.json, corpus_guard_truth.json | n/a |

- AC-37-02.1 Six outline runs for R02 in both modes and after a move; no spike at x = 9 (the lone observation).
- AC-37-02.2 Two-point contour: a ColorBar titled Price with ticks 4,000..4,800 in both modes.

## Tasks

**Commit boundary.** Two commits. DG-5 (37-02-02): `Break rarea's outline where cmissing(n) breaks its fill (WP-37 DG-5)`, staging dash_render.py, test/test_area_cmissing.py, test/test_mode_parity.py, test/js_runner.py (if TR-37-02.2 is needed), dash.sthlp (rarea sentence), the S02 DG-5 block, TWOWAY_COVERAGE_AUDIT.md (rarea row), BUGS/GAPS4/CHANGELOG/test_tracking_documents.py, and the corpus and known-differences files its closing steps change. DG-8 (37-02-03): `Draw a contour's colour key when no surface is drawn (WP-37 DG-8)`, staging dash_render.py, test/test_contour_key_degenerate.py, test/test_mode_parity.py, dash.sthlp (contour sentence), the S02 DG-8 block, TWOWAY_COVERAGE_AUDIT.md (contour row), BUGS/GAPS4/CHANGELOG/test_tracking_documents.py, and the corpus and known-differences files its closing steps change. The corpus and known-differences files are scripts/corpus/ledger.tsv and test/fixtures/corpus_ledger.json (and test/fixtures/corpus_guard_truth.json) when the ledger step changes them, and each test file whose `*_KNOWN` or `*_DELIBERATE` table the known-differences step edits (BRIEF "The corpus ledger and the known-differences tables"). `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp37-s02` (BRIEF "Pull form": every command names the worktree by this absolute path; `scripts/stata_slot.sh` runs `cd <scratch>` before Stata starts, so a relative path is not found).

<task type="auto" id="37-02-01">
  <name>Write the failing rarea outline tests</name>
  <files>test/test_area_cmissing.py, test/test_mode_parity.py, test/test_wp37_truth.cscript</files>
  <action><![CDATA[
    In $WT (batch 37.2 base, 37-01 landed), re-read dash_render.py:22849-23010, :18700-18730, `_dash_join_glyph` and `_dash_join_spec`, and the `_FILTER_JS` join rebuild for `_dash_join` sources; record anchors in `<scratch>/37-02-anchors.txt`. Add the DG-5 nodes to TestRareaConnect (reuse its `_figs`, `_rarea`, `_auto`, `_line_runs`; select the outline Lines by the `dash_rarea_outline` tag) and the move node; add the MOVE_CORPUS entry after the last rarea move entry; insert the `S02 DG-5` block directly above the first `* ==== S04 ` header (Stata truth). Run `node .gitnexus/run.cjs impact "map_rarea" --direction upstream --repo .` and the same for `map_contour`, `_dash_join_glyph` and `_dash_fill_rebuild` (and `_FILTER_JS`'s owner function if TR-37-02.2 is needed), writing callers and risk to `<scratch>/37-02/anchors.txt` (HIGH, CRITICAL or UNKNOWN named in the hand-back; an UNKNOWN confirmed with `grep -n` before editing; REVIEW R3-17). Run `python3 -m pytest test/test_area_cmissing.py -k "outline" -q -n0 -p no:cacheprovider -rf > <scratch>/37-02-01.log`, `python3 -m pytest test/test_mode_parity.py -k "DG-5" -q -n0 -p no:cacheprovider`, and the block through the driver (`WP37_ONLY=S02`); save failing nodes and FAIL lines to `<scratch>/37-02-01-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/37-02-01.log` is at least 4 (both modes of test_the_outline_breaks and the spike node); `grep -c "Q3702-1 FAIL" <scratch>/run_test_wp37_truth.log` prints 1; `test -s <scratch>/37-02-01-failure.txt`.]]></verify>
  <done>rarea's outline breaks were tested against twoway's three polygons and shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="37-02-02">
  <name>Break rarea outlines at gaps, commit DG-5</name>
  <files>dash_render.py, dash.sthlp, test/js_runner.py</files>
  <action><![CDATA[
    Apply TR-37-02.1 in `map_rarea`. Run the DG-5 nodes, test/test_area_cmissing.py whole, test/test_mode_parity.py -k "rarea or DG-5", test/test_legend*.py -k rarea and test/test_hover*.py -k rarea; if the move node or the parity move entry fails, apply TR-37-02.2 in `_FILTER_JS` (dash_render.py) with its node test in test/test_area_cmissing.py (through test/js_runner.py). Apply TR-37-02.4's rarea sentence. Run the S02 DG-5 block. Close the BUGS.md entry 33-01 opened for DG-5 (`grep -n 'WP-37 section 37-02 has not landed' BUGS.md`, the DG-5 one) in PD-4's closed form; Tracked line `commit pending`; delete DG-5 from `GAPS4_OPEN`; CHANGELOG `### Fixed in WP-37`: `- rarea with cmissing(n) drew its outline across the gaps; the outline breaks where the fill does (WP-37, DG-5)`; append to TWOWAY_COVERAGE_AUDIT.md's rarea row (:72, re-read) `[WP-37 DG-5: corrected -- under cmissing(n) the outline breaks where the fill does]`. Run the hygiene reader of Stata truth. The corpus ledger and the known-differences tables (BRIEF "The corpus ledger and the known-differences tables", steps 1-3; D-33-05.i, D-33-10.h): (1) run `awk -F'\t' '$1 == "DG-5" {print NR ": " $0}' scripts/corpus/ledger.tsv` and delete every line it prints (the item's plain rows; a `DG-5 (documented)` or `DG-5 (residual)` row stays, A-10), rerun `python3 scripts/corpus/ledger.py` (33-05; no run folder: `_meta` is kept, TR-33-05.3), `git add -f test/fixtures/corpus_ledger.json` (when no row was deleted the fixture is unchanged and nothing is staged) and run `python3 -m pytest test/test_corpus_ledger.py -q -n0 -p no:cacheprovider`; (2) run `python3 test/known_differences.py DG-5` (33-10) and delete every `<file>:<line>` row it prints from its `*_KNOWN` table -- a difference this item's ruling keeps moves instead into that table's deliberate dict, the companion dict 33-10 names for it (`DELIBERATE` in test/value_truth_known.py for `VALUE_KNOWN`, `ABBREV_DELIBERATE` in test/test_abbreviations.py for `ABBREV_KNOWN`, and beside 33-11..33-13's tables `SCALE_FRAME_DELIBERATE`, `BY_TYPES_DELIBERATE`, `BY_POSITION_DELIBERATE`, `STAT_COMBOS_DELIBERATE`, `COLORVAR_DELIBERATE`), as `"<key>": "<ruling id>: <what is kept>"` with a DECISIONS or index ruling id (P4-n, A-n, Q-n, M-n); no ruling of this section keeps one, so none is expected -- then run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`), which passes, and stage each table file the step edited, by the path the printed row names; (3) run the corpus guard block (`WP33_ONLY=S09 sh $WT/scripts/stata_slot.sh <scratch> <scratch>/run_test_wp33_truth.do`, the driver of BRIEF "Running one cscript" written for test/test_wp33_truth.cscript with `<repo>` = `$WT`) and, if Q3309-1 reports any change for a guard example -- an improved verdict (`<id> improved from ...`) or a changed field (`<id>: <field> was <old> now <new>`) -- regenerate test/fixtures/corpus_guard_truth.json with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s09 $WT/scripts/extract_corpus_guard_truth.do` (33-09), `git add -f` it, rerun the S09 block (it passes), and put each Q3309-1 message and the fixture's `Fixture:` line in DG-5's commit body (a worse verdict this item's change does not explain is a regression: fix the code first, CLAUDE.md rule 2). Before committing, in `$WT`: `git pull --ff-only . main` (CLAUDE.md rule 4; `Already up to date.` at the batch base -- if it refuses, stop and report to the orchestrator, never a merge commit on a section branch) and `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a `partial` or `truncated` result is run again; HIGH or CRITICAL risk named in the hand-back; REVIEW R3-17). Grep the message for `claude|anthropic`, commit, grep again.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_area_cmissing.py test/test_statistical_helpers.py::TestFilterJavaScript test/test_csp.py -q -p no:cacheprovider`'s last line reads `<n> passed in ...` with no `failed` or `error`; the parity run `-k "rarea or DG-5"`'s last line reads `<n> passed in ...` with no `failed` or `error`; `grep -c "Q3702-1 PASS" <scratch>/run_test_wp37_truth.log` prints 1; `awk -F'\t' '$1 == "DG-5"' scripts/corpus/ledger.tsv | wc -l` prints 0 and test/test_corpus_ledger.py passes; `python3 test/known_differences.py DG-5` prints no `<file>:<line>` row and the hygiene command it prints passes; the S09 guard block ends with its pass line; `git log -1 --format=%s | grep -c "(WP-37 DG-5)"` prints 1.]]></verify>
  <done>rarea's outline broke where cmissing(n) broke its fill in both modes and after a move, no ledger or known-differences row named DG-5 alone, and the DG-5 commit landed.</done>
</task>

<task type="auto" id="37-02-03">
  <name>Key a contour without surface, commit DG-8</name>
  <files>dash_render.py, test/test_contour_key_degenerate.py, dash.sthlp</files>
  <action><![CDATA[
    Create test/test_contour_key_degenerate.py (TestTheKey nodes of the stubs) and the CORPUS entry in test/test_mode_parity.py; insert the `S02 DG-8` block in test/test_wp37_truth.cscript directly after the DG-5 block (still above the first `* ==== S04 ` header); run them red and append to `<scratch>/37-02-01-failure.txt`. Apply TR-37-02.3 and TR-37-02.4's contour sentence. Run `python3 -m pytest test/test_contour_key_degenerate.py test/test_contour*.py test/test_zero_obs.py -q -n0 -p no:cacheprovider`, the parity entry, and the block. Close DG-8 (BUGS, GAPS4 `commit pending`, `GAPS4_OPEN`); CHANGELOG `### Fixed in WP-37`: `- A contour over too few points for a surface drew no colour key; it draws the key from its levels, as twoway does (WP-37, DG-8)`; append to TWOWAY_COVERAGE_AUDIT.md's contour row (:101, re-read) `[WP-37 DG-8: corrected -- a contour with no surface draws its colour key]`; run the hygiene reader. The corpus ledger and the known-differences tables (BRIEF "The corpus ledger and the known-differences tables", steps 1-3; D-33-05.i, D-33-10.h): (1) run `awk -F'\t' '$1 == "DG-8" {print NR ": " $0}' scripts/corpus/ledger.tsv` and delete every line it prints (the item's plain rows; a `DG-8 (documented)` or `DG-8 (residual)` row stays, A-10), rerun `python3 scripts/corpus/ledger.py` (33-05; no run folder: `_meta` is kept, TR-33-05.3), `git add -f test/fixtures/corpus_ledger.json` (when no row was deleted the fixture is unchanged and nothing is staged) and run `python3 -m pytest test/test_corpus_ledger.py -q -n0 -p no:cacheprovider`; (2) run `python3 test/known_differences.py DG-8` (33-10) and delete every `<file>:<line>` row it prints from its `*_KNOWN` table -- a difference this item's ruling keeps moves instead into that table's deliberate dict, the companion dict 33-10 names for it (`DELIBERATE` in test/value_truth_known.py for `VALUE_KNOWN`, `ABBREV_DELIBERATE` in test/test_abbreviations.py for `ABBREV_KNOWN`, and beside 33-11..33-13's tables `SCALE_FRAME_DELIBERATE`, `BY_TYPES_DELIBERATE`, `BY_POSITION_DELIBERATE`, `STAT_COMBOS_DELIBERATE`, `COLORVAR_DELIBERATE`), as `"<key>": "<ruling id>: <what is kept>"` with a DECISIONS or index ruling id (P4-n, A-n, Q-n, M-n); no ruling of this section keeps one, so none is expected -- then run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`), which passes, and stage each table file the step edited, by the path the printed row names; (3) run the corpus guard block (`WP33_ONLY=S09 sh $WT/scripts/stata_slot.sh <scratch> <scratch>/run_test_wp33_truth.do`, the driver of BRIEF "Running one cscript" written for test/test_wp33_truth.cscript with `<repo>` = `$WT`) and, if Q3309-1 reports any change for a guard example -- an improved verdict (`<id> improved from ...`) or a changed field (`<id>: <field> was <old> now <new>`) -- regenerate test/fixtures/corpus_guard_truth.json with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s09 $WT/scripts/extract_corpus_guard_truth.do` (33-09), `git add -f` it, rerun the S09 block (it passes), and put each Q3309-1 message and the fixture's `Fixture:` line in DG-8's commit body (a worse verdict this item's change does not explain is a regression: fix the code first, CLAUDE.md rule 2). Then, in `$WT`, `git pull --ff-only . main` and detect-changes as for DG-5. Grep the message for `claude|anthropic`, commit, grep again; write `<scratch>/37-02-handback.txt` with both shas and whether TR-37-02.2 was needed.
  ]]></action>
  <verify><![CDATA[The pytest run's last line reads `<n> passed in ...` with no `failed` or `error`; `grep -c "Q3702-2 PASS" <scratch>/run_test_wp37_truth.log` prints 1; `git log --format=%s -2 | grep -c "(WP-37 DG-[58])"` prints 2; `grep -c "DG-[58] Tracked:\*\* Closed in WP-37.*commit pending" GAPS4.md` prints 2; `awk -F'\t' '$1 == "DG-8"' scripts/corpus/ledger.tsv | wc -l` prints 0 and test/test_corpus_ledger.py passes; `python3 test/known_differences.py DG-8` prints no `<file>:<line>` row and the hygiene command it prints passes; the S09 guard block ends with its pass line.]]></verify>
  <done>A contour with no drawable surface showed twoway's colour key in both modes, no ledger or known-differences row named DG-8 alone, and both commits of 37-02 landed on wp37-s02.</done>
</task>

## Section completion criteria

- rarea outlines break at gaps (six runs for R02) in both modes and after a move; a two-point contour has its key; Q3702-1/2 pass; two BUGS entries closed; two Tracked lines; two `GAPS4_OPEN` deletions.
- No plain `DG-5` or `DG-8` row is left in scripts/corpus/ledger.tsv or in any `*_KNOWN` table (`python3 test/known_differences.py <id>` prints none for each); corpus_ledger.json is regenerated by `scripts/corpus/ledger.py` in each commit; test/test_corpus_ledger.py, the hygiene command and the S09 guard block pass; corpus_guard_truth.json is regenerated by its extract script in the commit whose S09 run reported a change for a guard example.

## Notes

- **Traps.** (1) `_dash_fill_rebuild` replaces `source.data` in place: take the outline columns before it. (2) `_dash_join_glyph` returns early to a plain `fig.line` when every point is finite and the style is direct with cmissing(y): rarea's outline then behaves as today. (3) The served app copies GlyphMapper whole: no copy-list entry for the method change; a new module helper (if any) goes after `"_dash_reference_lines",` in the functions tuple (R2).
- **GitNexus and rule 4.** `impact` on every function this section edits before its first edit (37-02-01); `git pull --ff-only . main` (in `$WT`, BRIEF "Pull form") and `detect-changes --scope all` before each commit (37-02-02, 37-02-03); HIGH, CRITICAL or UNKNOWN risk goes in the hand-back (REVIEW R3-17).
- **Help paragraphs owned (R3):** the rarea cmissing sentence and the contour degenerate-surface sentence (TR-37-02.4).
- **Merge rules touched:** R1 (two S02 blocks in section order, inserted above S04: BRIEF "Block order"), R2 (only if a helper is added), R8 (CORPUS and MOVE_CORPUS), R11/R12 (`_FILTER_JS` only if TR-37-02.2 is needed; this section is batch 37.2's only JS editor).
- **Commit-body line forms:** `Regression: test/test_area_cmissing.py::TestRareaConnect::test_the_outline_breaks[std] -- failed at <base> with 2 != 6`; `Fixture: test/fixtures/area_cmissing_truth.json (scripts/extract_area_cmissing_truth.do)`; `Fixture: test/fixtures/corpus_ledger.json (scripts/corpus/ledger.py)` and `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)` only in the commit whose ledger step changed them; `BUGS.md: "<title>" (closed)`; `GAPS4: DG-5 Tracked` / `GAPS4: DG-8 Tracked`.
- **The corpus ledger and the known-differences tables (BRIEF, from WP-34 on).** Each closing task (37-02-02 for DG-5, 37-02-03 for DG-8) deletes its item's plain rows of scripts/corpus/ledger.tsv and regenerates corpus_ledger.json (D-33-05.i), deletes every row `python3 test/known_differences.py <id>` prints and runs the hygiene command it prints (D-33-10.h), and regenerates corpus_guard_truth.json with its extract script if Q3309-1 reports any change for a guard example (33-09), before its own commit.
