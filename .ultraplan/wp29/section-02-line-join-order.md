# Section 02: Line join order

> Part of: WP-29 · P0: P0.1 · Risk: red · Batch: 1 · Depends on: 01 · Blocks: 14 · Case prefix: JO · Tasks: 17, 1 commit (P0.1)
>
> Files: dash_render.py, dash.ado, dash_parse.mata, dash.sthlp, CHANGELOG.md, BUGS.md, scripts/extract_join_order_truth.do, test/fixtures/join_order_truth.json, test/test_join_order.py (new), test/test_polyline_ordering.py, test/test_glyphs.py, test/test_mode_parity.py, test/test_saved_filter_layers.py, test/test_unsupported_report_is_true.py, test/test_server_layer_defects.py, test/test_abbreviations.py, test/test_filters.py, test/test_help_claims_1.py, test/test_served_linked_views.py, test/function_test_map.py, test/program_coverage_map.py, test/test_fixtures_are_committed.py, test/test_tracking_documents.py, test/test_twoway_option_parity.cscript, test/test_wp29_truth.cscript, test/test_adversarial.cscript. Verified unchanged (no edit expected): test/test_statistical_defaults.py, test/test_help_claims_8.py, test/test_help_claims_8.cscript, test/test_help_conformance.py.

## Review amendments (u01 review "sound with amendments", 30sep2026) — binding; they override any conflicting text below

The reviewed design is u01-line-order. Every amendment is applied in this file:

- **A1 (refusal wording).** The names are checked with Stata's own `syntax , SORT1(namelist)`, as twoway checks them (twoway_yxview_parse.class:187). They are not checked with Mata `tokens()` and `st_isname()`. TR-02.11 adds the helper program `_dash_sort_names`. Re-measured here (Evidence E1.4): the helper prints exactly twoway's line and returns r(198) for all nine malformed forms.
- **A2 (repeated sort()).** `s(sort1)` is read only after `_dash_opts_repeats` (dash.ado:3938). The new check `_dash_sort_opt` runs after `_dash_fold_typed` (:3961). Once `sort1` is sreturned, `_dash_rep_keyof` keys `sort(...)` as `sort1`, not as `_p:sort`. JO-25 tests that the reduction keeps the rightmost copy.
- **A3 (tsline/tsrline).** The name check applies on every type, tsline and tsrline included. Only a well-formed name is accepted silently there.
- **A4 (reserved words).** The existence check reproduces twoway's words for every reserved word. These were re-measured here on 22 words (E1.5), which led to three rules:
  - `unab` gives twoway's first line, except for `if`, `in`, `using` and `with`. On those, twoway prints "<word> is invalid variable name".
  - `_all` is accepted by twoway (rc 0) and sorts on every variable.
- **A5 (order against `_dash_qual_gen`).** `_dash_sort_gen` runs after `_dash_qual_gen`. Its clash check counts `__dashs*` only. When it fails, the caller drops `_dash_qual_vars` before exiting.
- **A6 (estimates hold).** The hold condition becomes `_dq_n + _ds_n > 0` on both routes. JO-10 tests it: `regress`, then `sort(z)` with no qualifier.
- **A7 (metadata pop).** Both loaders pop every metadata map for the sort columns, by iterating `list(qual_masks) + list(sort_keys)` in the existing loops.
- **A8 (coupling with S14/P0.11).** A sort key is validated as distinct, finite, positive integers of at most 2^53. It is not required to be a permutation of 1..N. A test feeds a key that is not 1..N.
- **A9 (rline as two copies).** `map_rline`, and `map_tsrline` through it, always build both copies, an empty one included. The served redraw pairs live and fresh sources with `zip` (dash_render.py:31212-31232). `TestRangeBoundsKeepTheirOwnRows` tests a move that empties one bound.
- **A10 (missing-data fixture).** The fixture data are stated exactly ("Stata truth", dataset B), with each bound's own missing row.
- **A11 (area with missing y).** Area is added to J8 and to the regression tests.
- **A12 (cscripts outside the simulation).** Task 02-14 runs every cscript that draws a joining type before the flip list is frozen.

**Re-measurements made for this section** (StataNow 19.5, through `scripts/stata_slot.sh`, `dash_nobrowser=1`; quoted in Evidence E1):
- M1: the name check on all 40 types.
- M2: `unab` against twoway on the existence check.
- M3: 22 reserved words.
- M4: an empty `sort()` copy beside a full one.
- M5: what `sort`/`sort(r)` does to seven computed types' SVG.

**Architect calls on the design's open questions** (each binding here; S15 records them):
- **O1 rarea, one bound missing on a row.** Deferred as a documented residual. One VArea cannot hold twoway's polygon there. Today's behaviour (the row left out of both bounds) is kept unchanged and is not pinned.
- **O2 rline per-bound rule.** Ships in this section's single P0.1 commit: the same lines are edited, and BUGS.md has one P0.1 entry.
- **O3 sort and sort() on the computed and other non-joining types.** Still named in the note, as today. M5 measured that twoway's drawing of mspline, mband, lfit, qfit, lowess, lpoly and fpfit is byte-identical with and without `sort`/`sort(r)`, so a later P2 item may silence them. This section does not.
- **O4 spec shape.** Two keys:
  - a plot-level `"sortvars":"<names>"`;
  - `build_options.sort_cols` = `{"<names>": "__dashs<k>"}`.

  No Mata JSON rewrite is needed.
- **O5 a sort() variable dropped between `name()` and `dash build`.** Refused r(198) in twoway's two lines ("variable z not found", "option sort() incorrectly specified"), plus one line naming the cause. This is what twoway says for that command against the data in memory.
- **O6 marker paint order of connected/rconnected under sort.** Accepted residual: it affects overlap z-order only.
- **O7 the "()" on a bare flag in the note.** Out of scope.

**Deviations from the reviewed design** (each with its reason):
- **D-a.** The static pending line `if `: length local sort1' local _dash_pending ... sort` (dash.ado:1085) is KEPT. `_dash_sort_opt` takes `sort` off `s(_pending)` on the eight types it honours or that twoway ignores it on. This is the fitarea precedent at dash.ado:1752-1758. Removing the line would move five pins (`48` in test_unsupported_report_is_true.py:237, test_statistical_defaults.py:860, test_help_conformance.py:595 and :601) and the help's Unsupported list (test_help_conformance.py `TestTheUnsupportedSectionIsTrue`, test_help_claims_8.py `test_every_listed_option_is_still_listed`), and the u01 simulation did not see three of those. sort() is still unsupported on 32 types.
- **D-b.** The new program is `_dash_sort_opt`, not `_dash_fold_sort`. `test_help_conformance._fold_aliases` (test_help_conformance.py:416) reads every `^program define _dash_fold_\w+` as an option-alias fold.
- **D-c.** The design's single `_dash_sort_export(json)` becomes three Mata functions: `_dash_sort_reset`, `_dash_sort_scan(json)` and `_dash_sort_export()`. They mirror `_dash_qual_reset`/`_dash_qual_export`, because the build route scans each graph's rewritten JSON (`_qg_<k>`, dash.ado:7174) before `graphs_json` exists.
- **D-d.** The truth block goes in `test/test_wp29_truth.cscript` block S02 (index.md A3), not in `test_gaps2_truth.cscript`.
- **D-e.** New cscript case ids use the prefix JO (index.md "Section numbers in case ids"), so "TP-06c" becomes JO-21..JO-27.
- **D-f.** The CHANGELOG WP-09 line (CHANGELOG.md:97-98, "They now draw along x") is not edited (R3). The new Results line names it as the behaviour it replaces.
- **D-g.** Copy-list anchors follow index.md R2:
  - functions go after `"_dash_float_values"` (dash_render.py:28546);
  - the three constants go after `"_DASH_QUAL_PREFIX", "_DASH_QUAL_NAME_RE"` (:28441). The index row says "—" for constants, but the design needs three constants; no other batch-1 section adds constants.

## Overview

DROPIN-REMAINING.md:37 (P0.1): "line, connected, area, rline, rarea and rconnected always sort by x, so `twoway line y x` without `sort` draws a different picture, with no note." Measured at HEAD (E2):
- both render modes draw every joining type at x = 1800, 2010, 2200, … on the parity frame whose data order is 2930, 3350, 2200, …;
- after a filter move to Foreign, both draw 1800, 2010, 2650, 3100, 3350, where twoway draws 3350, 1800, 3100, 2010, 2650;
- `sort(varlist)` is accepted with "dash: ignoring unsupported option(s): sort()" even when twoway refuses it, r(198);
- `rline` leaves a row out of both bounds when one bound is missing; twoway leaves it out of that bound only.

After this section, dash joins as twoway does (M1):
- data order by default;
- x order under `sort`;
- the varlist's order under `sort(varlist)`, which wins over `sort`; of repeated copies the rightmost non-empty one wins;
- time order always for tsline and tsrline.

This holds in the saved page and the served app, at first paint, per by() panel, in the Total panel and after every filter move. Ties keep the data's order; twoway's tie order is random (E1.6). `sort()` is checked as twoway checks it: the same return codes and the same words on all 40 types. Each range line keeps its own rows.

**How it works.**
- **Order.** One renderer rule, `GlyphMapper._join_order`, orders the drawn rows in both modes. GlyphMapper is copied into the served app by source.
- **Ranks.** `sort(varlist)` is resolved in Stata. `_dash_sort_gen` writes one rank column `__dashs<k>` per distinct varlist, made by Stata's own `sort varlist obs`. Strings sort byte by byte and missing values as . < .a < .b, which the data writer cannot carry (it writes every missing value as null; dash_render.py:1394).
- **Taking the ranks out.** The renderer validates the rank columns and removes them from the frame, as it does the qualifier columns. They reach no page, source, tooltip, filter or download.
- **No JavaScript change.** The saved page's filter script already keeps each derived copy's rows in drawn order (`_FILTER_JS`, dash_render.py:15970-16030). The served redraw re-runs the mapper on the filtered frame.

**Test order (CLAUDE.md rule 7) and commit rule (index.md "Per P0 entry cycle").**
1. Tasks 02-01 and 02-02 run the mandatory impact analysis and report its HIGH risk.
2. Task 02-03 extracts Stata's truth into the fixture.
3. Tasks 02-04 and 02-05 write every regression test and run it against the unmodified tree. They save the failure text to `<scratch>/02-P0.1-failure.txt` and never commit.
4. Tasks 02-06 to 02-09 make the fix.
5. Tasks 02-10 to 02-14 flip every pin of x order, with reasons, and run the area cscripts.
6. Task 02-15 writes the help.
7. Task 02-16 runs the full verification.
8. Task 02-17 closes the BUGS.md entry, replaces both CHANGELOG markers, deletes the `WP29_OPEN` key and makes the section's ONE commit, subject ending `(WP-29 P0.1)`.

## Risk: [red] — a deliberate, visible change to every published line plot on unsorted data, made through four layers (Stata parse, Stata export, Python load, two renderers) that must agree

**Why.**
- Every `dash line|connected|area|rline|rarea|rconnected` on data not sorted by x changes shape (PLAN.md K15, likelihood "certain"). Areas become self-intersecting exactly where twoway's are.
- The sort keys add a new column family to the data file, which touches the same export lines as S06 (hover), S08 (private writer) and S14 (embed rows).
- R8 expects HIGH impact on `GlyphMapper.map_line`, `map_area`, `map_rline` and `map_rarea`.

**Risk factors.**
1. Parity drift: a helper on one copy list and not the other.
2. A rank that leaks to the page reveals the order of an unexported variable.
3. A tampered spec or data file indexing out of range.
4. rline drawn as two copies changes renderer and source counts that other tests read.
5. Pins of x order in 9 pytest files and 2 cscripts (E5), some found only by running the cscripts (A12).
6. dash.ado export-path conflicts with S06/S08 in the same batch.
7. Users' do-files need `sort` added.

**Mitigation.**
1. Both served-name guards, plus `TestBothModesJoinAsTwowayDoes` comparing saved == served == Stata.
2. `TestTheSortColumnsNeverReachTheUser`, and the sort variable itself is never exported (JO-12).
3. Every value is validated, ids are bounds-checked, and names are checked in Stata, Mata and Python.
4. Targeted runs of test_mode_parity, legend and hover before the full suite.
5. Task 02-14 runs every joining-type cscript before the commit.
6. The merge order S01, S09, S03, **S02**, S04, S06 puts S02's hunks first; Notes name the shared lines.
7. Two CHANGELOG lines, including a "Changed behaviour" line with the one-word fix, plus a help paragraph.

## Dependencies

- **Depends on: 01.** S01 opens the P0.1 BUGS.md entry and the `WP29_OPEN["P0.1"]` allowance. It places `<!-- WP-29 P0.1 -->` twice in CHANGELOG.md (the `**WP-29 (drop-in P0, 30sep2026)**` group of `### Results that change`, and `### Changed behaviour`). It creates `test/test_wp29_truth.cscript` with the marker line `* ==== append new blocks above this line ====`.
- **Blocks: 14.** S14 (P0.11) restricts each consumer to the rows it reads. `_join_order` orders the drawn rows, and the sort-key validation (A8) must accept the subset of rows S14 embeds.
- **Parallel batch:** 1, merge position 4 of 9 (`S01, S09, S03, S02, S04, S06, S07, S05, S08`).
- **Can run with:** 03, 04, 05, 06, 07, 08, 09. Symbols are disjoint, except `_make_figure_body`'s plot loop (S07 edits the per-plot qualifier view above it) and the dash.ado export blocks (Notes).

## Evidence

### E1. twoway's truth (measured, StataNow 19.5)

**E1.1 The default is data order for all six joining types** (u01 research run t1/truth1.do; data x = 2 5 3 6 1, y = 10x with y[5] = 20, y2 = y + 2, z = 6 - _n, g = 1 2 1 2 1):
- `twoway rline y y2 x, nodraw` gives a serset that `serset use, clear; list` prints in data order:
  ```
       y   y2   x
      20   22   2
      50   52   5
      30   32   3
      60   62   6
      20   22   1
  ```
  `line`, `connected`, `area`, `rarea`, `rconnected` and `line y y2 x` hold the same order.
- The SVG path follows the serset: line_nosort.svg is `M1122 L3127 L1790 L3795 L454` (x = 2, 5, 3, 6, 1). With `sort` it is 1, 2, 3, 5, 6.
- area: the data-order path, then down to the base at the last x, along the base, Z.
- rarea: the lower bound forward in data order, then the upper bound reversed.
- Neither SVG sets a fill-rule. BokehJS VAreaView._paint draws y1 forward and y2 reversed with the nonzero default (bokeh.min.js 3.9.0), so a VArea given data-order rows fills twoway's region when both bounds are present.

**E1.2 Which option sets the order** (t1; twoway_yxview_parse.class:144, :266-271, :828-848; serset.class:81-94):
- `sort` gives x order (on range types too).
- `sort(z)` orders by z although z is not plotted.
- `sort(g x)` gives serset x = 1 2 3 5 6 (g then x).
- `sort sort(z)` uses z.
- `sort(zz) sort(x)` uses x (`_parse combop 0 : 0 , option(SORT1) rightmost`, :144).

Sort keys (research t4/truth4.do; re-measured here, M2 end): `twoway line y x, sort(z)` with z = .b 3 .a 1 . 2 gives serset y = 40 60 20 50 30 10. That is z = 1, 2, 3, ., .a, .b. Strings sort byte by byte: "", A, B, _, a, b. `sort(z)` with only `zz` in the data uses `zz`.

**E1.3 Missing values** (research t3/truth3.do, corrected by A10 and r4/r4.do):
- A missing x is never drawn.
- line and connected skip a missing y and bridge the gap (`cmissing(y)`).
- rline and rconnected skip missing values per bound. With x = 2 5 3 6 1 7, y missing at x = 3 and y2 missing at x = 5 (r4/r4.do):
  - `rline.svg` lower path `M1749.26 2336.68 L3482.33 1978.09 L4059.96 1260.73 L1171.63 902.14 L4637.59 543.38`, which is x = 2, 5, 6, 1, 7;
  - upper path `M1749.26 2300.91 L2326.89 1583.55 L4059.96 1224.96 L1171.63 866.19 L4637.59 507.60`, which is x = 2, 3, 6, 1, 7.
- rarea's polygon is lower 2,5,6,1,7, then upper reversed 7,1,6,3,2 (each bound drops its own missing rows).
- area (review r1/r1.do, `area y x` with y missing at x = 3): serset `10 2 / 20 5 / . 3 / 40 6 / 50 1`; area_miss.svg bridges in data order 2, 5, 6, 1, then the base.

**E1.4 The name check, all 40 types (M1, this section, `s02/m1/m1.do` and `s02/m5/m5.do`).**
- `capture noisily twoway <cmd>, sort(<s>) nodraw` on all 40 types gave r(198) for each of `x*`, `z+` and `L.x`, with the lines `* invalid name`, `+ invalid name` and `L.x invalid name` (`grep -c` of each: 40, 40, 40).
- Further cases on line (m5):
  - `sort(-zz)` gives `- invalid name`;
  - `sort(1x)` gives `1x invalid name`;
  - `sort(z-zz)` gives `- invalid name`;
  - `sort(z(1))` gives `( invalid name` (one line);
  - `sort(z, stable)` gives `, invalid name`;
  - `sort(a b c*)` gives `* invalid name`;
  - `x~`, `x?`, `x/`, `x=`, `x&`, `x#`, `x:`, `x;`, `x'` and `@x` each give the punctuation character's line;
  - `a.b` gives `a.b invalid name`, and `x.` gives `x. invalid name`.
- The helper `program _t_nm; version 16.0; syntax [, SORT1(namelist)]; end` printed exactly the same single line and r(198) for every case (`HNM[z(1)] rc=198` after the single line `( invalid name`).
- `confirm names` does NOT match. It returns r(7), prints every bad token (`z(1)` gave three lines) and refuses reserved words as "(reserved word)". So it is rejected.

**E1.5 The existence check (M2, M3; `s02/m2/m2.do`, `s02/m3/m3.do`).**
- On the 23 serset types (scatter line connected area bar spike dropline dot rarea rbar rspike rcap rcapsym rscatter rline rconnected pcspike pcarrow pcbarrow pcscatter pccapsym mband mspline), twoway prints Stata's varlist message, then `option sort() incorrectly specified`, r(198):
  - `variable nosuch not found`;
  - `z ambiguous abbreviation` (data holding zz and zb);
  - `variable _N not found`, likewise for `_n`, `_b`, `_coef`, `_cons`, `_pi`, `_pred`, `_rc` and `_se`;
  - `int not allowed`, likewise for `byte`, `double`, `float`, `long`, `str1`, `strL` and `_skip`;
  - `if is invalid variable name`, likewise for `in`, `using` and `with`.
- For the first bad token of `zz nosuch`, `nosuch zz`, `x z` and `int in`, twoway names the first bad one.
- On the other 17 types (lfit lfitci qfit qfitci fpfit fpfitci lowess lpoly lpolyci function tsline tsrline histogram kdensity scatteri pci pcarrowi), every one of those is rc 0.
- `twoway line y x, sort(_all)` is rc 0 and the serset is in x, then y, then zz order.
- `capture noisily unab _u : <tok>, max(1)` under `version 16.0` prints twoway's first line for every word above except `if` (`if not allowed`), `in` (`in range not allowed`), `using` (`using not allowed`), `with` (`invalid 'with'`) and `_all` (r(103)).
- `syntax [, sort(varlist)]` does not match: it prints `(error in option sort())` with rc 111, and for `in` it prints `sort() does not contain a valid varlist`.

**E1.6 Repeats, empty copies and ties.**
- Review r1/r1.do:
  - `line y x, sort(x*) sort(z)` rc 0;
  - `sort(z) sort(x*)` gives `* invalid name` r(198);
  - `sort(nosuch) sort(z)` rc 0;
  - `sort(z) sort(nosuch)` r(198);
  - `sort()` rc 0, with the data-order serset `2 5 3 6 1` (r2);
  - `sort(z z)` rc 0;
  - `tsline y, sort(x*)` gives `* invalid name` r(198).
- M4 (`s02/m1`): `twoway line y x, sort(zz) sort() nodraw` and `sort() sort(zz)` are both rc 0, and both sersets are in zz order (the empty copy is ignored, whichever side it is on).
- Ties: on 40, 400 and 5000 rows with x in 1..4, about half the adjacent pairs inside tied x are inversions for every seed (research t3, e.g. 2497 of 5000). HC8-15 (test_help_claims_8.cscript) already certifies that `sort(rep78)` joins differently on three draws.

**E1.7 by(), if/in, tsline.**
- Each by() panel joins in data order within its group: review r2 measured 0 inversions in each of three 100-row panels against the data order.
- The Total panel, with or without `missing`, joins in the original data order (research t7/tot.do).
- `in 2/6` and `if g==1` join in data order.
- tsline/tsrline join in time order whatever the data order, and `sort` and `sort(y)` change nothing, rc 0 (twoway_tsline_parse.class:21-32 marks SORT/SORT1 "ignored" and passes `sort(`t')`).

**E1.8 Computed types are unchanged by sort (M5, `s02/m4/m4.do`).** For each of mspline, mband, lfit, qfit, lowess, lpoly and fpfit, the md5 of the `<path d=...>` text of `twoway <t> y x`, `..., sort(r)` and `..., sort` is identical (40 random rows). Example: `mspline paths=1 none=52b4d86f r=52b4d86f s=52b4d86f`.

### E2. dash at HEAD (7421d3d)

Two-mode probe (u01 `py/probe_modes.py`, re-run for this section). The parity frame's data-order weight is 2930, 3350, 2200, 1800, 3000, 3100, 4080, 2010, 3600, 2650:
```
line {} SAVED  [[('Line', [1800.0, 2010.0, 2200.0, 2650.0, 2930.0, 3000.0, 3100.0, 3350.0, 3600.0, 4080.0])]]
rarea {} SERVED [[('VArea', [1800.0, 2010.0, 2200.0, 2650.0, 2930.0, 3000.0, 3100.0, 3350.0, 3600.0, 4080.0])]]
line move SERVED [[('Line', [1800.0, 2010.0, 2650.0, 3100.0, 3350.0])]]
line by(foreign) SAVED [[('Line', [2200.0, 2930.0, 3000.0, 3600.0, 4080.0])], [('Line', [1800.0, 2010.0, 2650.0, 3100.0, 3350.0])]]
```
The same holds for connected, area, rline, rconnected, tsline and tsrline, with and without `{"sort": "sort"}`, in both modes.

Range missing-value probe (u01 `py/probe_rmiss.py`, re-run). Data x = 2 5 3 6 1 . 7, y missing in row 3, y2 missing in rows 2 and 3:
```
map_rline Line y= y x path [1.0, 2.0, 6.0, 7.0]
map_rline Line y= y2 x path [1.0, 2.0, 6.0, 7.0]
map_rconnected Line y= y x path [1.0, 2.0, 5.0, 6.0, 7.0]
map_rarea VArea x path [1.0, 2.0, 6.0, 7.0]
```
twoway draws the lower bound at 2, 5, 6, 1, 7.

dash.ado at HEAD (u01 t5/dashnow.do):
- `dash line y x, sort(z)`, `sort(nosuch)`, `sort(L.x)` and `sort(z*)` are each rc 0 with `dash: ignoring unsupported option(s): sort()` (twoway: r(198) for the last three).
- `dash tsline y, sort(y)` names sort() (twoway is silent).
- `dash line y x, sort` is silent.

Cost at HEAD (`s02/py/cost.py`, 1,000,000 rows): `map_line 0.17 s`, `map_area 0.14 s`, `map_rline 0.17 s`; a stable argsort of 1e6 keys takes 0.105 s.

### E3. The code (anchors at 7421d3d; symbols are authoritative)

`GlyphMapper.map_line`, dash_render.py:7852. The docstring (:7866-7867) is false: "Data is sorted by the x variable before rendering to match Stata behaviour (Stata's twoway line auto-sorts by x)." The sort:
```python
7903        # The sort is stable, so the rows a saved-page filter move keeps
7904        # (by their row id, carried below) are in the order a sort of them
7905        # alone gives (_collect_derived_sources).
7906        df = df.dropna(subset=[xvar, yvar]).sort_values(xvar, kind="stable")
```
`map_area`, :7988; comment :8016-8026 ("Stata's twoway area draws along x", false per E1.1):
```python
8027        if len(x_arr):
8028            _order = np.argsort(x_arr, kind="stable")
8029            x_arr = x_arr[_order]
8030            y_arr = y_arr[_order]
8031            _area_idx = _area_idx[_order]
```
`_masked_index` :8605 (positions of the drawn rows, in source order) and `_masked_order` :8630:
```python
8635        idx = GlyphMapper._masked_index(source, view, xvar, *others)
8636        if len(idx):
8637            xs = _dash_float_values(source.data[xvar])[idx]
8638            idx = idx[np.argsort(xs, kind="stable")]
```
Its only callers are `map_rarea` :10591 and `map_rline` :10880. Both use `_masked_order(source, view, xvar, y1var, y2var)`, so a row missing either bound leaves both.

The other mappers:
- `map_rline` :10848 builds one source for both lines (:10889-10903).
- `map_rconnected` :10912 calls `map_line` per bound (:10949, :10952), so it already drops per bound.
- `map_connected` :7953 calls `map_line` :7981.
- `map_tsline` :12060 delegates to `map_line` :12085, and `map_tsrline` :12087 to `map_rline` :12114.

Dispatch:
- `_dash_add_glyph` :24840 dispatches through `_dash_glyph_dispatch` :24687 (`"line": mapper.map_line` :24706 … `"rconnected": mapper.map_rconnected` :24734).
- The saved plot loop calls `self._add_glyph` (:26374, a thin wrapper) in the range branch (:26244-26248) and the plain branch (:26271-26278). `source_for_plot` is set at :26167.
- Every saved source carries `__dash_row__`, the row's position in `self.df` (`_make_source` :25437, `_row_ids_for` :25604).
- The served `_dash_draw_layer` (emitted :30162-30245) builds sources with `_dash_range_source`/`_dash_layer_source`. A `ColumnDataSource(clean)` carries pandas' `index`, and the linked `shared_source` carries `index` explicitly (:30112).
- The served redraw closure (:30288-30303) re-runs `_dash_draw_layer` on the filtered frame.

Qualifier-column precedent, which the sort keys mirror:
- `_DASH_QUAL_PREFIX` / `_DASH_QUAL_NAME_RE` :24241-24243.
- `_dash_qual_cols_named` :24247.
- `_dash_take_qual_columns` :24283. It refuses any unnamed `__dash*` column (:24301-24307), so the sort columns must be taken out first.
- `_dash_qual_mask` :24328.
- Saved load :25197-25205; served load emitted :29918-29929; `meta['qual_masks']` :29936; `_qual_masks = meta['qual_masks']` :30032.

Served copy lists: the constants tuple holds `"_DASH_QUAL_PREFIX", "_DASH_QUAL_NAME_RE"` at :28441, and the functions tuple holds `"_dash_float_values"` at :28546.

Stale comments that describe x order as current behaviour:
- `_FILTER_JS` :15970-15979 ("a line stays sorted and an area stays a polygon along x");
- `_dash_own_redrawn_views` :21689;
- `_collect_derived_sources` :25444;
- emitted :30577 and :31018.

dash.ado:
- The parser declares `SORT` and `SORT1(string)` (:935-936).
- The static pending line (:1085) is commented at :1079-1084.
- `sreturn local sort : copy local sort` is at :1188. sort1 is never sreturned.
- `_dash_fold_typed` (:1708) silences a bare `sort` on `line connected area tsline rline rarea rconnected tsrline` (:1739-1744). Its ci-type block (:1752-1758) takes options off `s(_pending)` with `local _ftk : list _ftp - ci_drawn`, which is the precedent for D-a.
- In the segment (`_dash_process_segment` :3300): parse :3923, `_dash_opts_repeats` :3938, `_dash_validate_opts` :3956, `_dash_fold_typed` :3961, `_dash_plot_opts_to_json` :4145, plot JSON assembly :4160-4172.
- `_dash_qual_gen` :4394 refuses any `__dash*` variable, rc 110 (:4398-4404).
- Immediate route: `_dash_qual_export` :6063, cell cap :6084, `_estimates hold` :6104-6107, `_dash_qual_gen` :6108, `_dash_write_data` :6116, drop :6118-6120, `master_json` :6138.
- Build route: `_dash_qual_export` :7101, cell caps :7108-7113, hold :7128-7131, write :7134, drop :7136-7138, per-graph JSON `_qg_<k>` (:7076, joined at :7174), `master_json` :7281.
- `_dash_require_mata`'s `_needed` list :232-246.

dash_parse.mata:
- `_dash_qual_reset` :2654, `_dash_qual_export` :3123, `_dash_qual_orders` :3140.
- `_dash_qual_cols_in` :5482, the needle reader the sort scan copies.
- `_dash_rep_scan` :4288, `_dash_rep_keyof` :4347, `_dash_rep_reduce` :5077.
- The header index is at :1-260 (`*!` lines; the qual entries at :176-186).

### E4. Impact analysis (CLAUDE.md "Always Do"; index.md R8)

`mcp__gitnexus__list_repos` (30sep2026) lists only `TYME` and `PhotoShootPlannerPro`: **dash is not indexed**. Task 02-01 runs `gitnexus analyze` in the worktree first, then the mandatory `gitnexus_impact` calls. Task 02-02 reports HIGH/CRITICAL results to the maintainer before any edit.

Callers found by grep at 7421d3d:
- `map_line` ← `map_connected` :7981, `map_rconnected` :10949 and :10952, `map_tsline` :12085, dispatch :24706.
- `_masked_order` ← `map_rarea` :10591 and `map_rline` :10880 only.
- `map_rline` ← `map_tsrline` :12114 and dispatch :24733.
- `_dash_add_glyph` ← `DashRenderer._add_glyph` :26399 and the emitted `_dash_draw_layer` (:30220, :30229).

R8 expects HIGH on `map_line`, `map_area`, `map_rline` and `map_rarea`.

### E5. Tests that pin today's behaviour (flip, never delete; each gets a `Flipped:` line)

| Node | Today's expectation | Why it was wrong / new expectation |
|---|---|---|
| test/test_polyline_ordering.py::test_the_glyph_is_drawn_in_x_order[map_line\|map_connected\|map_area] | `got == sorted(got)` | twoway joins in data order (E1.1). Becomes `test_the_glyph_is_drawn_in_data_order` (`got == list(_X)`), plus `test_the_glyph_is_drawn_in_x_order_under_sort` with `{"sort": "sort"}`. The module docstring's WP-09 claim is rewritten. |
| test/test_polyline_ordering.py::test_a_range_path_is_drawn_in_x_order[map_rline\|map_rarea\|map_rconnected] | sorted | Becomes `test_a_range_path_is_drawn_in_data_order` for these three. `[map_tsrline]` stays in x (time) order, and a `[sort]` case is added. |
| test/test_glyphs.py::TestMapLine::test_line_sorted_by_x | sorted (P1A-89, "Stata auto-sorts") | Data order `[5,2,4,1,3]`, and sorted under `{"sort": "sort"}` |
| test/test_glyphs.py::TestMapConnected::test_connected_data_sorted | sorted | The `cds` fixture's data order, and sorted under sort |
| test/test_mode_parity.py::TestALinkedByGraphsLinesOnASavedBuild::test_each_panels_line_holds_its_own_rows (:3270) | `xs == sorted(xs)` | Each panel in data order within its group (E1.7). Docstring :3215 "in x order" changes too. |
| test/test_saved_filter_layers.py::TestTheLineFollowsTheMoveAsTwowayDraws::test_the_line_draws_the_foreign_cars_in_x_order[line\|connected] | 1800, 2010, 2650, 3100, 3350 | 3350, 1800, 3100, 2010, 2650 (twoway). `[tsline]` keeps 1800… (time order). Class docstring :311-314. |
| test/test_saved_filter_layers.py::TestTheCopiesAgainstHostileInput::test_a_variable_named_after_an_object_property_is_kept[__proto__\|constructor\|hasOwnProperty] | 1800, 2010, 2650, 3100, 3350 | 3350, 1800, 3100, 2010, 2650 (purpose kept: the name survives) |
| test/test_saved_filter_layers.py::TestALinesOwnQualifier::test_the_line_draws_the_observations_twoway_draws[line\|connected × in 3/8, if mpg > 18] | sorted lists | in 3/8 gives 2200, 1800, 3000, 3100, 4080, 2010; `if mpg > 18` gives 2930, 2200, 1800, 3000, 3100, 2010, 2650. tsline cases unchanged. Docstring :545-546. |
| test/test_saved_filter_layers.py::TestALinesOwnQualifier::test_rconnected_draws_both_ends_from_the_same_rows | `_IN_3_8` sorted | Data order 2200, 1800, 3000, 3100, 4080, 2010 |
| test/test_unsupported_report_is_true.py::test_a_plot_option_reported_unsupported_really_is[sort] (via `PLOT_VALUES["sort"] = ("sort", "", "line")`, :140) | bare sort inert on line | `sort` is honoured on line. PLOT_VALUES' ptype becomes `"scatter"`, where sort is still named (D-a). This also flips test_help_claims_8.py::TestAnUnsupportedOptionIsInertWhenServed::test_plot_level[sort], which imports PLOT_VALUES. |
| test/test_server_layer_defects.py::TestTheMaskedIndex::test_masked_order_is_the_same_rows_sorted_by_x and ::test_the_two_select_the_same_set (:1174, :1178) | `_masked_order` | `_masked_order` is deleted. Restated as `test_join_order_under_sort_is_the_same_rows_sorted_by_x` and `test_join_order_selects_the_masked_rows`, on `_join_order(src, _masked_index(...), "x", {"sort": "sort"})`. function_test_map.py:156 moves. |
| test/test_abbreviations.py::test_the_tr_23_6_scans_see_what_they_look_for (:604) | `len(with_syntax) == 12` | 13: `_dash_sort_names` declares `SORT1(namelist)` (E1.4). The `_dash_parse_plot_opts` comment count 108 (:618) is kept by rewriting :1079-1084 in six lines. If it moves, it is flipped to the measured number. |
| test/test_twoway_option_parity.cscript TP-06 row 1 (:451-453) | `dash line mpg weight, sort(mpg)` names sort() | Honoured. The row moves to `dash scatter mpg weight, sort(mpg)`. |
| test/test_twoway_option_parity.cscript TP-06 `sort sort(mpg)` block (:495-525) | named sort() once, no sort1 key | On line it is silent: no note line, no `sort1` key, and the spec carries `"sortvars":"mpg"` and `sort_cols` |
| test/test_twoway_option_parity.cscript TP-06b loop (:557) items `"line mpg weight, sort(price)"` and `"(line mpg weight, sort(price)) (scatter mpg weight)"` | sort() named | Not named. The scatter/bar items stay named. The comment at :527-534 is rewritten. |

Not affected, verified by D-a:
- test_unsupported_report_is_true.py:237 (48);
- test_statistical_defaults.py:860 (48, `"sort"` in pending);
- test_help_conformance.py:595, :601;
- test_help_claims_8.cscript HC8-02 (bare `sort` on scatter, still named);
- test_twoway_option_parity.py:271 `test_sort1_is_reported_as_sort_and_never_written` (the static line is unchanged and the writer gains no `sort1`).

Comment-only corrections in other tests (current-behaviour claims; the historical narratives stay):
- test_filters.py:1677 "a line sorted by x";
- test_help_claims_1.py:957 "a line sorted along x";
- test_served_linked_views.py:24 and :530 "a line sorted along x";
- test_mode_parity.py:3215;
- test_saved_filter_layers.py:311-314 and :545-546.

## User stories

- **US-02.1** As a twoway user, I want `dash line mpg weight` on my unsorted data to draw the path `twoway line mpg weight` draws, joined in my data's order, so that pasting a do-file into dash shows the same picture.
- **US-02.2** As a twoway user, I want `sort` to join the points in the order of x and `sort(varlist)` in the order of that varlist, as in twoway, on line, connected, area, rline, rarea and rconnected. That includes strings byte by byte and missing values . < .a < .b, and the rightmost `sort()` winning.
- **US-02.3** As a twoway user, I want an invalid `sort()` (`sort(x*)`, `sort(nosuch)` on a line, `sort(in)`) refused with twoway's message and r(198), so that a mistake is caught where twoway catches it.
- **US-02.4** As a dashboard reader, I want each line to keep its join order after any filter move, in every by() panel and in the Total panel, on the saved page and in the served app.
- **US-02.5** As an analyst, I want `rline` and `tsrline` to draw each bound through every row where that bound is present, as twoway does, so a missing upper value does not delete the lower point.
- **US-02.6** As a dashboard publisher, I want a variable named only in `sort()` never to reach the page, so `sort(salary)` cannot leak the order of an unexported variable.
- **US-02.7** As the maintainer, I want the join order pinned against Stata's own serset and SVG in both modes, so x order cannot return unnoticed.

## Business requirements

- **BR-02.1** Without `sort` or `sort(varlist)`, line, connected, area, rline, rarea and rconnected join the drawn points in the data's order, in both modes, before and after a filter move, in every by() panel and in the Total panel.
- **BR-02.2** With `sort`, they join in x order. With `sort(varlist)`, they join in the order Stata's `sort varlist` gives, whether or not `sort` is also given. Of several `sort()` copies, the rightmost non-empty one decides. Points whose keys tie keep the data's order.
- **BR-02.3** tsline and tsrline join in time order whatever option is given. A well-formed `sort`/`sort(varlist)` on them is accepted silently.
- **BR-02.4** A malformed name in `sort()` is refused on every plot type, r(198), with twoway's exact line. A name that is not a usable variable is refused on the 23 serset types, r(198), with twoway's two lines. On the other 17 types it is accepted (rc 0). A refusal leaves the data and the registry unchanged.
- **BR-02.5** `sort` and `sort(varlist)` are named in the "ignoring unsupported option(s)" note on every plot type except the six joining types, tsline and tsrline.
- **BR-02.6** Each bound of rline and tsrline is drawn through the rows where that bound and x are present. line, connected and area leave out a row whose y or x is missing and bridge the gap.
- **BR-02.7** The variables of `sort(varlist)` and the rank columns derived from them appear nowhere a reader can see: page, source, tooltip, filter, csv download, served document or note.
- **BR-02.8** A `sort()` variable dropped after its graph was registered stops `dash build`/`dash serve` with twoway's words, r(198). No dash column is left in the data.

## Technical requirements

- **TR-02.1 One join rule.** Add `GlyphMapper._join_order(source, idx, xvar, options, order=None, by_x=False)` as a `@staticmethod` directly after `_masked_index` (dash_render.py:8605). It returns positions into `source.data`. The precedence is:
  1. `by_x` gives a stable argsort of `_dash_float_values(source.data[xvar])[idx]` (dates as epoch ms).
  2. Else, when `order is not None`, it gives a stable argsort of `np.asarray(order, float)[idx]`. `order` must have one entry per source row, else `ValueError`.
  3. Else, when `(options or {}).get("sort") == "sort"`, it gives the x argsort.
  4. Else it returns `idx` unchanged (data order).

  An empty `idx` is returned as-is.
- **TR-02.2 The mappers.**
  - `map_line(..., line_kind=None, order=None, by_x=False)`: keep the view mask and `dropna(subset=[xvar, yvar])`, then `df = df.loc[self._join_order(source, df.index.to_numpy(), xvar, options, order, by_x)]`. Delete `.sort_values` and the :7903-7905 comment, and rewrite the docstring (:7866-7867) to state twoway's rule.
  - `map_connected(..., order=None)` forwards `order` to `map_line`.
  - `map_area(..., order=None)`: `_area_idx = self._join_order(source, self._masked_index(source, view, xvar, yvar), xvar, options, order)`. Take `x_arr`/`y_arr` as `_dash_float_values(...)[_area_idx]`. Delete the argsort block and the :8016-8026 comment. The border-line copy (:8070-8086) uses the same arrays and ids.
  - `map_rarea(..., order=None)`: `_ord = self._join_order(source, self._masked_index(source, view, xvar, y1var, y2var), xvar, options, order)`. One VArea: twoway's polygon when both bounds are present; O1 residual.
  - `map_rline(..., order=None, by_x=False)`:
    - `_lo = self._join_order(source, self._masked_index(source, view, xvar, y1var), ...)`;
    - `_hi = self._join_order(source, self._masked_index(source, view, xvar, y2var), ...)`.
    - Build TWO sources, `ColumnDataSource(self._carry_cols(source, {xvar: x[_lo], y1var: y1[_lo]}, _lo))` and the same for `_hi`/`y2var`. ALWAYS build both, empty or not (A9).
    - `r1` draws `y1var` from the lower source and `r2` draws `y2var` from the upper source. Styles and `legend_label` are unchanged.
  - `map_rconnected(..., order=None)` forwards `order` to both `map_line` calls.
  - `map_tsline` calls `map_line(..., by_x=True)`, and `map_tsrline` calls `map_rline(..., by_x=True)`. Rewrite both docstrings: "time order, whatever option is given (twoway_tsline_parse.class:21-32)".
  - Delete `GlyphMapper._masked_order`.
- **TR-02.3 Dispatch.** Add `_DASH_JOIN_TYPES = frozenset({"line", "connected", "area", "rline", "rarea", "rconnected"})`. `_dash_add_glyph(mapper, fig, source, plot_type, yvar, xvar, options, y2var="", view=None, color_idx=0, order=None)` passes `order=order` to the range function (:24862-24864) and to the plain function (:24879) only when `pt in _DASH_JOIN_TYPES and order is not None`. `DashRenderer._add_glyph` (:26374) gains `order=None` and forwards it.
- **TR-02.4 Sort-column helpers (module level, after `_dash_qual_mask`, ~:24345).**
  - Constants after `_DASH_QUAL_NAME_RE` (:24243): `_DASH_SORT_PREFIX = "__dashs"`, `_DASH_SORT_NAME_RE = re.compile(r"__dashs[1-9][0-9]{0,4}\Z")`, `_DASH_JOIN_TYPES`.
  - `_dash_sort_cols_named(spec)` returns `build_options.sort_cols` as a dict, validated:
    - the map is a dict;
    - each value is a `str` matching `_DASH_SORT_NAME_RE`, and no two keys share a value;
    - each key is a `str` of 1 to 120,000 space-separated tokens, each passing `_dash_is_stata_name` (:1287);
    - every plot of every graph whose `"sortvars"` is a non-empty value has it as a `str` that is a key of the map.

    Otherwise it raises `ValueError` (message names at most 40 characters of the offending text and `_DASH_SORT_PREFIX`).
  - `_dash_take_sort_columns(df, spec)` returns `(df without the named columns, {col: pd.Series(values, index=df.index)})`. Each named column must be in `df`. Its values, read by `pd.to_numeric(errors="coerce")`, must be finite, integer-valued, at least 1, at most 2**53, and distinct (`len(np.unique(v)) == len(v)`). Otherwise `ValueError`. Never require 1..N (A8).
  - `_dash_sort_col_of(plot, spec)` returns `""` when the plot has no `"sortvars"`, else the column the map names (`ValueError` when absent).
  - `_dash_join_key(source, sort_keys, col)`:
    - returns `None` when `col` is falsy;
    - otherwise reads `rank = sort_keys[col]` (missing: `ValueError`);
    - when `_ROW_ID_COLUMN` is in `source.data`, its ids must be integer-valued with `0 <= id < len(rank)`, and the key is `rank.to_numpy(float)[ids]`;
    - elif `"index"` is in `source.data`, the key is `rank.reindex(list(labels)).to_numpy(float)`, and any NaN raises;
    - else `ValueError`.
- **TR-02.5 Saved renderer.**
  - In `DashRenderer._load_data`, immediately before `_dash_take_qual_columns` (:25197), add `self.df, self.sort_keys = _dash_take_sort_columns(self.df, self.master_spec)`. Make the pop loop (:25199-25205) iterate `list(self.qual_masks) + list(self.sort_keys)`.
  - In `_make_figure_body`'s plot dispatch, compute once per plot, before the range branch: `_jo = (_dash_join_key(source_for_plot, getattr(self, "sort_keys", None) or {}, _dash_sort_col_of(plot, self.master_spec)) if ptype.lower() in _DASH_JOIN_TYPES else None)`. Pass `order=_jo` in the range branch (:26246) and the plain branch (:26277).
  - `self.sort_keys` is indexed exactly like `self.df`. Any later change to `self.df`'s rows must rebuild it (S14 note).
- **TR-02.6 Served app.**
  - Emitted load (:29918): `df, sort_keys = _dash_take_sort_columns(df, spec)` before the qual line. Both pop loops (:29919-29924, :29928-29929) iterate `list(qual_masks) + list(sort_keys)`. `meta` gains `'sort_keys': sort_keys`.
  - In `make_document`, after `_qual_masks = meta['qual_masks']` (:30032), add `_sort_keys = meta['sort_keys']`.
  - In the emitted `_dash_draw_layer`:
    - after `_dash_range_source(...)` (:30211-30215): `_jo = (_dash_join_key(_ly_src, _sort_keys, _dash_sort_col_of(plot, spec)) if ptype in _DASH_JOIN_TYPES and _ok else None)`, and `order=_jo` on the `_dash_add_glyph` call (:30220-30222);
    - in the else branch, after `_dash_layer_source(...)` (:30224-30227), the same with `_ly_src is not None`, and `order=_jo` on :30229-30231.

    The redraw closure (:30288-30303) is unchanged: it calls `_dash_draw_layer`.
  - Copy lists:
    - constants tuple after `"_DASH_QUAL_PREFIX", "_DASH_QUAL_NAME_RE"` (:28441): `"_DASH_SORT_PREFIX", "_DASH_SORT_NAME_RE", "_DASH_JOIN_TYPES"`;
    - functions tuple after `"_dash_float_values"` (:28546): `"_dash_join_key", "_dash_sort_col_of", "_dash_sort_cols_named", "_dash_take_sort_columns"`.

    `_join_order` travels with GlyphMapper.
- **TR-02.7 Comments.** Rewrite to "in its join order":
  - `_FILTER_JS` :15970-15979, comment text only, no code;
  - `_dash_own_redrawn_views` :21689;
  - `_collect_derived_sources` :25444;
  - emitted :30577-30582 and :31018.

  Also update the `_DASH_RESERVED_PREFIX` comment (:24236-24238) and `_dash_take_qual_columns`' docstring to name the sort columns `__dashs<k>`.
- **TR-02.8 The parser (dash.ado `_dash_parse_plot_opts`).**
  - Add `sreturn local sort1          : copy local sort1` directly after `sreturn local sort : copy local sort` (:1188).
  - Keep the static line :1085 (D-a). Rewrite its six-line comment :1079-1084 in exactly six comment lines saying:
    - the argument form arrives in `sort1`, which is also returned in `s(sort1)`;
    - `_dash_sort_opt` checks it as twoway does after the repeats are reduced;
    - it is honoured on the six types and silent on tsline/tsrline, where it comes off this list;
    - elsewhere it stays named.
- **TR-02.9 Repeats (dash_parse.mata).** twoway's `_parse combop ..., option(SORT1) rightmost` skips an empty copy (M4).
  - In `_dash_rep_scan` (:4288), when choosing `last[k]` for the spelling `sort(`, a token whose `strtrim(_dash_rep_value(tok)) == ""` does not replace a non-empty one.
  - In `_dash_rep_reduce` (:5077), for the key `sort1`, `lastpos[k]` advances only on a copy with a non-empty value. The empty copies are then left out of the output like every other non-last copy.
  - `sort() sort()` (all empty) is unchanged.
- **TR-02.10 The Stata order of checks.** `_dash_sort_opt "`ptype'"` is called in `_dash_process_segment` on the line after `_dash_fold_typed "`ptype'"` (:3961). This is after `_dash_opts_repeats` (A2).
- **TR-02.11 `_dash_sort_names` (new program, placed directly before `_dash_sort_opt`).** Body: `version 16.0` and `syntax [, SORT1(namelist)]`, nothing else. It is called as `capture noisily _dash_sort_names , sort1(`macval(_so_v)')`. Its message and r(198) are twoway's (E1.4).
- **TR-02.12 `_dash_sort_opt ptype` (new, `sclass`).**
  1. Read the value by value: `mata: st_local("_so_v", st_global("s(sort1)"))`. When it is empty, exit (a bare `sort` stays `_dash_fold_typed`'s).
  2. Run `capture noisily _dash_sort_names , sort1(`macval(_so_v)')`. On rc, `exit 198`. This applies on every type.
  3. On `tsline tsrline`, take `sort` off `s(_pending)` (read `mata: st_local("_so_p", st_global("s(_pending)"))`, `local _so_k : list _so_p - _so_rm` with `local _so_rm "sort"`, `sreturn local _pending `"`_so_k'"'`; the list holds option names only), then exit.
  4. On the 23 serset types, for each token (Mata `tokens()` of the now-validated value, all names):
     - On `if in using with`: `mata: _dash_say("err", st_local("_so_t"), " is invalid variable name")`, then `display as error "option sort() incorrectly specified"`, then `exit 198`.
     - On `_all`: `unab _u : _all`, appended whole.
     - Otherwise `capture noisily unab _u : `_so_t', max(1)`. On rc, `display as error "option sort() incorrectly specified"` and `exit 198`. Otherwise append `_u`.
  5. On the six joining types, `sreturn local sortvars "<unabbreviated names, single-spaced>"` and take `sort` off `s(_pending)` as in step 3.
  6. Every other type is left as it is (named through the static line).

  No user text is re-expanded. The only echo of user text goes through `_dash_say`.
- **TR-02.13 The spec.**
  - In `_dash_process_segment`, directly after `_dash_plot_opts_to_json _opts_json` (:4145): `mata: st_local("_jsv", st_global("s(sortvars)"))`, `local _jsvf ""`, and when it is non-empty `_dash_json_str "`_jsv'" _jsv2` and `local _jsvf `","sortvars":"`_jsv2'""'`.
  - Append ``_jsvf'`` after `"in_expr":"`_jin'"` in both assembly lines (:4166, :4171).
  - A plot without `sort(varlist)` writes nothing new, so the spec stays byte-identical.
- **TR-02.14 The Mata table (dash_parse.mata, after `_dash_qual_orders`, ~:3157; one header-index line each near :176-186).**
  - `void _dash_sort_reset()` empties `external string colvector _dash_sort_list`.
  - `void _dash_sort_scan(string scalar json)` reads every `"sortvars":"` value (needle `char(34)+"sortvars"+char(34)+":"+char(34)`, value up to the next byte 34, as `_dash_qual_cols_in` :5482 reads). It appends each distinct value in first-seen order. It sets the caller's `_ds_bad` to the first value with a token for which `st_isname()` is 0 (else "").
  - `void _dash_sort_export()` sets the caller's `_ds_n` and `_ds_v<k>`.

  Add all three to `_needed` (dash.ado:232-246).
- **TR-02.15 `_dash_sort_gen cmdname` (new program, `sortpreserve`, after `_dash_qual_gen_by`, dash.ado ~:4500).**
  1. Run `mata: _dash_sort_export()`. If `_ds_n` is 0: `c_local _dash_sort_vars ""` and exit.
  2. `capture unab _ds_clash : __dashs*`. If found, refuse rc 110 in `_dash_qual_gen`'s words (defence in depth; `_dash_qual_gen` already refused any `__dash*`, A5).
  3. Create `tempvar _ds_obs` and `generate double `_ds_obs' = _n` (the original order).
  4. For k = 1.._ds_n:
     - For each name, `capture confirm variable <name>, exact`. On failure, drop the columns made so far, then `mata: _dash_say("err", "variable ", st_local("_ds_nm"), " not found")`, `display as error "option sort() incorrectly specified"`, `display as error "      `cmdname': the variable was dropped or renamed after the graph was registered."` and `exit 198` (O5).
     - Then `sort <names> `_ds_obs'` and `quietly generate double __dashs<k> = _n`.
  5. `c_local _dash_sort_vars "<made>"`. sortpreserve restores the order.
- **TR-02.16 Both export routes.**
  - **Immediate route.**
    - Before the cell cap: `mata: _dash_sort_reset()`, `mata: _dash_sort_scan(st_local("json_spec"))`, refuse r(198) "option sort() incorrectly specified" if `_ds_bad` is non-empty, then `mata: _dash_sort_export()`.
    - The plain cell cap becomes `_dash_cell_cap `=`_dash_nvars' + `_dq_n' + `_ds_n''` (:6084).
    - The hold condition becomes `if `_dq_n' + `_ds_n' > 0` (:6104).
    - After `_dash_qual_gen "dash"`: `capture noisily _dash_sort_gen "dash"`. On rc, `capture drop `_dash_qual_vars'` and `exit` with that rc.
    - The write (:6116) appends `` `_dash_sort_vars' ``, and the drop (:6118-6120) drops both lists.
    - `master_json` (:6138) gains `,"sort_cols":{"<v1>":"__dashs1",...}` inside `build_options`, only when `_ds_n > 0`. Keys go through `_dash_json_str` (names only).
  - **Build route.** The same, except the scan loops over each non-KPI `_qg_<k>` (as :7171-7175 does) after `_dash_qual_rewrite`. The server branch's cell cap (:7110) adds `_ds_n`; the saved branch's (:7113) does not, because the sort columns are never on the page. Hold :7128, generation after :7132, write :7134, drop :7136, `master_json` :7281.
- **TR-02.17 `_dash_qual_gen`'s message** (:4400) names the join-order columns: "(its qualifier columns __dashq#, its join-order columns __dashs#, its row identity __dash_row__ …)".
- **TR-02.18 Maps.**
  - `test/function_test_map.py`: delete `'GlyphMapper._masked_order'` (:156). Add, in alphabetical place:
    - `'GlyphMapper._join_order': 'test/test_join_order.py::TestTheJoinOrderRule::test_the_precedence'`;
    - `'_dash_join_key': 'test/test_join_order.py::TestTheJoinKey::test_saved_source_by_row_id'`;
    - `'_dash_sort_col_of': 'test/test_join_order.py::TestTakingTheSortColumnsOut::test_the_column_of_a_plot'`;
    - `'_dash_sort_cols_named': 'test/test_join_order.py::TestTakingTheSortColumnsOut::test_the_map_is_validated'`;
    - `'_dash_take_sort_columns': 'test/test_join_order.py::TestTakingTheSortColumnsOut::test_the_frame_loses_the_columns_and_the_keys_hold_statas_ranks'`.
  - `test/program_coverage_map.py`:
    - `_dash_sort_opt` → `test_twoway_option_parity.cscript:JO-21`, `:JO-22`;
    - `_dash_sort_names` → `:JO-21`;
    - `_dash_sort_gen` → `test_wp29_truth.cscript:JO-09`, `test_adversarial.cscript:JO-33`;
    - the Mata `_dash_sort_reset`, `_dash_sort_scan`, `_dash_sort_export` → `test_wp29_truth.cscript:JO-01`.
- **TR-02.19 Security (rule 1).**
  - User text in `sort()` is checked by Stata's `namelist` and `unab`. It is carried by value and never evaluated or re-expanded.
  - Mata re-checks every token (`st_isname`) before any name reaches a `sort` command line.
  - Python validates each column name by regex and each key as Stata names. It validates values as distinct finite positive integers and bounds-checks ids.
  - The rank and sort variables reach no page, source, tooltip, filter, csv, served document or note.
  - No `shell=True`. No user text in `exec`/`eval`. Python blocks read macros only through `sfi.Macro.getLocal` (test_cscript_hygiene.py:514).
- **TR-02.20 Cost.** `_join_order` is O(n log n) per joined layer per redraw. At HEAD it costs 0.105 s at 1e6 keys, and map_line 0.17 s (E2). Bound: each of map_line (data order and keyed), map_area and map_rline at 1e6 rows under 2.0 s.

## Boundaries

- **Unchanged in this section.**
  - No JavaScript code changes (`_FILTER_JS` gets a comment edit only). S05 owns the `_FILTER_JS` aggregate loop, and S07 the per-plot qualifier view above the plot dispatch.
  - `connect()`/`cmissing()` on scatter and other types are P1 (PLAN.md §3).
  - `sort` on non-joining types stays named (O3). The note's "()" on bare flags is unchanged (O7).
  - rarea with exactly one bound missing on a row keeps today's drawing, as a residual (O1). Marker paint order under sort is a residual (O6).
- **Embedding and accounting.** No change to `_dash_embedded_cells` (dash_render.py:1167) or to the saved route's G3 accounting. The sort columns are not page cells. S14 owns embedding.
- **Tracking documents.** Do not edit ROADMAP.md, GAPS.md, GAPS2.md, REMAINING.md, TWOWAY_COVERAGE_AUDIT.md, DROPIN-REMAINING.md or AGENTS.md (A5; "Notes for the closeout" carries the text).
- **Shared test files and registries.**
  - Do not edit `test_gaps2_truth.cscript` (R1: S06 only), `test/run_all_cscripts.do` or `test/test_cscript_hygiene.py` (S01 only).
  - Do not edit `ALLOWED` or `_MUST_WARN` in test_mode_parity.py (R6). Only CORPUS cases are appended.
  - Do not re-baseline the SHA-256 page of test_varlist_expansion.py (R7). That page is a filterless scatter and carries no `_FILTER_JS`, so the comment edit cannot move it. If it does move, revert the comment edit.
- **Silent when honoured (DISCOVERY Q22).** The six types and tsline/tsrline print nothing for `sort`/`sort(varlist)`.

## Stata truth

**New script `scripts/extract_join_order_truth.do`**, writing **`test/fixtures/join_order_truth.json`**, in the form of `scripts/extract_filter_truth.do`:
- The header comment names the run command.
- `local repo : env DASH_REPO`, defaulting to `/Users/billy/Desktop/Programs/StataPrograms/d/dash`. The section runs it with `DASH_REPO=<worktree>`.
- `adopath ++ "`repo'/"`.
- Locals `stata_version` (`c(stata_version)`), `born_date` (`c(born_date)`), `dash_commit` (`shell git -C "`repo'" rev-parse HEAD > tempfile`, read with `file read`) and `extracted` (`c(current_date)`).
- Records are written as `|`-separated lines to a tempfile. A `python:` block reads the tempfile path and every value with `sfi.Macro.getLocal`, never calls back into Stata, never uses `shell=True`, writes a backtick as `\x60`, and writes the JSON with `indent=2, sort_keys=True`.

Run:
```
dash_nobrowser=1 DASH_REPO=<worktree> scripts/stata_slot.sh <scratch>/s02-truth <worktree>/scripts/extract_join_order_truth.do
```
Read `<scratch>/s02-truth/extract_join_order_truth.log`. Then `git add -f test/fixtures/join_order_truth.json`; `.git/info/exclude` hides `*.json`.

**Dataset A** (8 observations, tie-free under every key; the hand-derived orders are for sanity only, and the fixture is authoritative):

| obs | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| x | 4 | 1 | 3 | 2 | 8 | 5 | 7 | 6 |
| y = 100·obs | 100 | 200 | 300 | 400 | 500 | 600 | 700 | 800 |
| y2 = y + 1 | 101 | … | | | | | | 801 |
| z | 3 | .b | 1 | .a | 2 | . | 5 | 4 |
| s (str) | "b" | "B" | "a" | "" | "_" | "A" | "C" | "c" |
| zz | 2 | 1 | 2 | 1 | 1 | 2 | 1 | 2 |
| keyw | 8 | 7 | 6 | 5 | 4 | 3 | 2 | 1 |
| g | 1 | 2 | 1 | 2 | . | 1 | 2 | 1 |
| t | 3 | 8 | 1 | 6 | 2 | 7 | 4 | 5 |

Expected obs orders:
- x order: 2 4 3 1 6 8 7 5.
- `sort(z)`: 3 5 1 8 7 6 4 2.
- `sort(s)`: 4 6 2 7 5 3 1 8.
- `sort(zz x)`: 2 4 7 5 3 1 6 8.
- `sort(key)` (abbreviates keyw): 8 7 6 5 4 3 2 1.
- time order (t): 3 5 1 7 8 4 6 2.

For J11 the script runs `tsset t`, then `sort obs` to put the data back in obs order.

**Dataset B** (J8; 7 observations): x = 2 5 3 6 1 . 7; y = 10 20 . 40 50 45 60. Two upper bounds:
- `y2a` = 11 . 31 41 51 46 61: y missing in row 3, y2a missing in row 2, x missing in row 6.
- `y2b` = 11 21 . 41 51 46 61: both bounds missing in row 3 only.

**Records.** Before each command: `serset clear` and `graph drop _all`. Each record holds the command, the type, the option text and the result.
- **`orders`**: the serset's obs list (`serset use, clear` under `preserve`, obs = y/100, else read from x through dataset A's map):
  - **J1** `twoway <t> <v>` for t in line, connected, area (`y x`) and rline, rarea, rconnected (`y y2 x`);
  - **J2** `, sort`;
  - **J3** `, sort(z)`;
  - **J4** `, sort(s)`;
  - **J5** `, sort(zz x)`;
  - **J6** `, sort sort(z)`;
  - **J7** `, sort(z) sort(x)`;
  - **J10** `in 2/6` and `if g==1`, each with no option;
  - **J11** `tsline y` and `tsrline y y2` with "", `sort` and `sort(y)`.
- **`by`**: for each serset (`forvalues k = 0/40`, `capture serset set k`), its obs list.
  - **J9** `line y x` and `rline y y2 x` with `by(g)`, `by(g, total)` and `by(g, total missing)`, each with and without `sort`.
- **`missing`**: the vertex x sequence of every `<path d=...>` of `graph export "<scratch>/j8_<id>.svg"`, in document order (no `nodraw`; `xscale(range(0 8)) xlabel(0(2)8)`). Each pixel is mapped through a linear fit of `svg_truth.svg_axis_reading(svg, "x")["pairs"]` (`sys.path.insert(0, <repo>/scripts)`) and rounded. The block raises if a value is more than 1e-3 from an integer.
  - **J8a** `line y x`, `connected y x`, `area y x`, `rline y y2a x`, `rconnected y y2a x` and `rarea y y2a x`;
  - **J8b** `rarea y y2b x`;
  - each with and without `sort`.
- **`ranks`**: for keys `z`, `s`, `zz x`, `keyw` and `x`, the rank per obs made exactly as `_dash_sort_gen` makes it: `generate double o = _n; sort <key> o; generate double r = _n; sort o`.
- **`_meta`**: the four stamp keys.

Ties are excluded: twoway's tie order is random (E1.6). The return-code and message matrix (E1.4-E1.6) is checked live in JO-21..JO-27, not stored.

**Certification block** `* ==== S02 P0.1: line join order ====` in `test/test_wp29_truth.cscript`. It is appended above `* ==== append new blocks above this line ====` in section order and gated `local only : env WP29_ONLY` / `if inlist("`only'", "", "S02")`, with `S02 start/end` time lines. Run through the driver (index.md):
```
printf 'cd "%s/test"\ndo "%s/test/%s"\n' "<worktree>" "<worktree>" "test_wp29_truth.cscript" > <scratch>/run_test_wp29_truth.do
dash_nobrowser=1 WP29_ONLY=S02 scripts/stata_slot.sh <scratch> <scratch>/run_test_wp29_truth.do
```
Read `<scratch>/run_test_wp29_truth.log`; never relaunch a run to check on it. The script exits 222 when `c(python_exec)` is empty, and a SKIP is not a pass.

## TDD test stubs

All in **`test/test_join_order.py`** (new, task 02-04) unless noted.
- The module builds its own `_write(spec, df)`, `_saved(spec, df)`, `_served(spec, df)`, `_saved_move(spec, df, action)` and `_served_move(spec, df, action)`. They are modelled on test_mode_parity.py `_write`/`_standalone`/`_served` (:204-252), test_saved_filter_layers.py `_render`/`_move` (:102-137) and test_mode_parity.py `_served_after_move` (:1949). Each takes a frame, because the sort columns must be in the data.
- It reads `make_data_json` from conftest and passes `var_labels` explicitly (A7). It reads the fixture with `pytest.fail` naming task 02-03 if the file is absent (never skip).
- A layer's order is read as the x column of each Line/VArea data source, mapped to obs through the dataset's x → obs map (x is distinct in A and B).
- "FAILS at base" means it fails against the batch-1 base. Those failure texts go to `<scratch>/02-P0.1-failure.txt`. Every other stub is a guard.

- Test: `TestTheJoinOrderRule::test_the_precedence`: `_join_order` on x = [2, 5, 3, 6, 1]:
  - `{}` gives [0, 1, 2, 3, 4];
  - `{"sort": "sort"}` gives [4, 0, 2, 1, 3];
  - `order = [5, 4, 3, 2, 1]` with `{"sort": "sort"}` gives [4, 3, 2, 1, 0];
  - `by_x=True` with an order gives [4, 0, 2, 1, 3];
  - an empty idx gives an empty array;
  - a short order raises ValueError.

  FAILS at base (AttributeError).
- Test: `TestTheDefaultIsTheDataOrder::test_a_mapper_joins_in_data_order[map_line|map_connected|map_area|map_rline|map_rarea|map_rconnected]`: x = [2, 5, 3, 6, 1] is drawn [2, 5, 3, 6, 1], both lines for the range types. FAILS at base (`[1.0, 2.0, 3.0, 5.0, 6.0]`).
- Test: `TestTheDefaultIsTheDataOrder::test_bare_sort_joins_in_x_order[6 types]`. Guard.
- Test: `TestTheDefaultIsTheDataOrder::test_ties_keep_the_data_order_under_sort`: x = [2, 1, 2, 1], y = [10, 20, 30, 40] under sort draws y 20, 40, 10, 30. Guard.
- Test: `TestTheDefaultIsTheDataOrder::test_x_keeps_its_pairing_with_each_y[6 types]`. Guard.
- Test: `TestTheDefaultIsTheDataOrder::test_area_with_a_missing_y_bridges_in_data_order`: dataset B's `area y x` draws x 2, 5, 6, 1, 7 (A11; fixture J8a). FAILS at base ([1, 2, 5, 6, 7]).
- Test: `TestTimeSeriesJoinInTimeOrder::test_whatever_they_are_given[map_tsline|map_tsrline × {}, {sort}, key]`. The key case goes through `dr._dash_add_glyph(..., order=key)` and is time order in every case. FAILS at base for the key case (TypeError: `order`).
- Test: `TestASortKeySetsTheOrder::test_the_key_orders_the_rows[6 types]`, `::test_the_key_beats_a_bare_sort`, `::test_the_key_under_a_view` (a by() BooleanFilter view; the key is read at the view's positions). FAILS at base (TypeError).
- Test: `TestTheJoinKey::test_saved_source_by_row_id`, `::test_served_source_by_index_label`, `::test_no_identity_is_refused`, `::test_an_out_of_range_id_is_refused`, `::test_a_non_integer_id_is_refused`, `::test_an_unknown_column_is_refused`, `::test_no_column_gives_none`. FAIL at base (AttributeError).
- Test: `TestTakingTheSortColumnsOut` (mirrors test_qualifier_columns.py:131-200):
  - `::test_the_frame_loses_the_columns_and_the_keys_hold_statas_ranks` (the fixture's ranks);
  - `::test_the_map_is_validated`, parametrised: a value `__dashq1`, `__dashs0`, `__dashs123456`, `x`, a non-str; a key with a quote, a blank token, a 33-character name; two keys to one column;
  - `::test_a_plot_naming_an_unknown_list_is_refused`;
  - `::test_a_column_the_data_lack_is_refused`;
  - `::test_a_bad_value_is_refused[dup|0|-1|1.5|nan|inf|2**53+2]`;
  - `::test_a_key_that_is_not_one_to_n_is_taken` (A8: 10, 30, 20);
  - `::test_an_unnamed_dashs_column_is_refused` (a `__dashs9` the spec does not name is refused by the qualifier take-out's reserved-prefix rule);
  - `::test_qualifier_columns_are_still_taken`;
  - `::test_the_column_of_a_plot`;
  - `::test_labels_and_formats_lose_the_column` (A7: every metadata map, both loaders).

  FAIL at base (AttributeError).
- Test: `TestBothModesJoinAsTwowayDoes::test_saved_and_served_match_twoway[<fixture orders id>]`, for every J1-J7, J10 and J11 record. It builds the frame from dataset A, plus `__dashs1` = the fixture's rank for the record's sort key, and the spec plot (`{"sort": "sort"}` when bare sort is in effect, `"sortvars"`, `build_options.sort_cols`). It asserts the saved order == the served order == the record's obs. FAILS at base for J1, J3-J7 and J10.
- Test: `TestAFilterMoveKeepsTheJoinOrder::test_saved_page_under_node[line|connected|area|rline|rarea|rconnected]` and `::test_served_app[...]`:
  - test_mode_parity's `_DF`, a dropdown to Foreign: the Foreign rows in data order, weight 3350, 1800, 3100, 2010, 2650;
  - with a key that orders by descending price, the Foreign rows in that order.

  FAILS at base.
- Test: `TestByPanelsJoinInDataOrder::test_by[saved|served]`, `::test_by_total[saved|served]`, `::test_by_total_missing[saved|served]` against fixture J9 (per-panel obs tuples compared as a set). FAILS at base.
- Test: `TestRangeBoundsKeepTheirOwnRows`:
  - `::test_rline_bounds[saved|served]`: dataset B, `rline y y2a x`; lower x 2, 5, 6, 1, 7; upper x 2, 3, 6, 1, 7 (fixture J8a);
  - `::test_tsrline_bounds` (A9);
  - `::test_rconnected_bounds` (guard);
  - `::test_rarea_both_bounds_missing_together` (J8b; guard after the order fix);
  - `::test_a_move_that_empties_one_bound[saved|served]`: a filter whose kept rows all lack y2. Each side holds two Line sources, no warning matches `redrew`, and the remaining bound is in data order.

  FAILS at base (the per-bound rows; one source).
- Test: `TestTheSortColumnsNeverReachTheUser` (mirrors test_qualifier_columns.py:453-530):
  - `::test_not_in_the_saved_page_at_all` (`__dashs` absent from the HTML);
  - `::test_not_in_the_frame_or_its_labels`;
  - `::test_not_in_a_tooltip`;
  - `::test_not_among_a_filters_choices`;
  - `::test_not_in_the_csv_download` (`csv` "1");
  - `::test_not_in_the_served_document_at_all`;
  - `::test_not_in_a_note_or_axis`.

  FAILS at base: the column is refused, not taken.
- Test: `TestTheCostIsBounded::test_a_million_rows[map_line|map_line_keyed|map_area|map_rline]`, each under 2.0 s. FAILS at base for the keyed case.
- Test: `TestTheFixture::test_meta_stamp` (the four `_meta` keys) and `::test_the_rank_rule_is_twoways` (for J3-J5 on line, sorting obs by the recorded rank gives the recorded serset order). Guards once the fixture exists.

**Cscript cases** (task 02-05; each prints `JO-nn PASS` or `JO-nn FAIL: <why>` and never exits on a failure).

`test/test_wp29_truth.cscript` block S02, dataset A or B as each case says. Each compares dash's saved page with live twoway. The block's own python helper `_jo_page_orders(path)` copies `_he5_read`'s parse (test_gaps2_truth.cscript:259-283) and returns each Line/VArea source's x column. `_jo_serset(lab)` is a Stata program that preserves, runs `serset use, clear` and lists obs. `_jo_svg_xs(svg)` is as in the extract script.
- **JO-01** six types × no option, the data order. FAILS at base.
- **JO-02** six types × `sort`. Guard.
- **JO-03** six types × `sort(z)`, `sort(s)`, `sort(key)`, `sort(zz x)`, `sort(_all)`. FAILS at base.
- **JO-04** `sort sort(z)`, `sort(z) sort(x)`, `sort(x*) sort(z)`, `sort(zz) sort()` and `sort() sort(zz)`: dash rc 0 == twoway rc, and same order. FAILS at base.
- **JO-05** dataset B, J8a/J8b types × {none, sort}: each dash path == the live SVG path. FAILS at base for the rline/tsrline upper path and the none cases.
- **JO-06** `by(g)`, `by(g, total)` and `by(g, total missing)` on line and rline: per-panel tuples as a set. FAILS at base.
- **JO-07** `in 2/6` and `if g==1`. FAILS at base.
- **JO-08** tsline/tsrline × {none, sort, sort(y)}: time order, rc 0, no note. FAILS at base (the `sort(y)` note).
- **JO-09** the build route:
  - `dash line y x, sort(z) name(g1)` then `dash build, saving(<scratch>/jo09.html) replace`: JO-03's z order;
  - then `drop z` and `dash build ...` gives r(198), the log holds `variable z not found` and `option sort() incorrectly specified`, and afterwards `capture unab _l : __dash*` is r(111) (no column left, A5).

  FAILS at base.
- **JO-10** `regress y x`, then `dash line y x, sort(z) saving(...)` with no qualifier: rc 0, z order, and `e(cmd)` is still `regress` (A6). FAILS at base.
- **JO-11** the served app: `dash build, server saving(<scratch>/jo11.py) replace`, then a `python:` block that `exec`s the app file into a dict, calls `make_document(Document())`, and reads every Line/VArea source in document order. Line and rline × {none, sort(z)} equal JO-01/JO-03's. FAILS at base.
- **JO-12** `dash line y x, sort(keyw)`, where keyw is named nowhere else: the page holds no column `keyw` and no `__dashs`, and the spec's `sort_cols` maps `keyw` to `__dashs1`. FAILS at base (`sort_cols` absent).

`test/test_twoway_option_parity.cscript`, after TP-06b, a block `// JO -- sort() as twoway checks it (WP-29 S02)`. A local list holds the 40 types and their varlists. For pccapsym and pcarrowi, extend the file's `v_` locals. Each case runs twoway and dash through `_ztp_run` into two logs and compares rc and the expected lines in BOTH logs.
- **JO-21** 40 types × `sort(x*)`, `sort(z+)`, `sort(L.x)`, `sort(-zz)`, `sort(1x)`, `sort(z, stable)`, `sort(z(1))`: r(198), the single E1.4 line. FAILS at base (rc 0 plus note).
- **JO-22** 23 serset types × `sort(nosuch)`, `sort(z)` (data holding zz and zb), `sort(_N)`, `sort(int)`, `sort(in)`, `sort(if)`, `sort(using)`, `sort(with)`, `sort(_b)`, `sort(zz nosuch)`: r(198) and E1.5's two lines. FAILS at base.
- **JO-23** the 17 other types × `sort(nosuch)`: rc 0 in both. dash names sort() except on tsline/tsrline. FAILS at base for tsline/tsrline only.
- **JO-24** `sort(z)` with only `zz` in the data, and `sort(_all)`: rc 0; `_ztp_has` finds `"sortvars":"zz"` and the full `_all` list.
- **JO-25** repeats per E1.6 (rc and lines), plus `sort(zz) sort()` and `sort() sort(zz)` rc 0 with `"sortvars":"zz"`, and `sort()` rc 0 with no `sortvars` and no note.
- **JO-26** notes:
  - none on the six types for `sort`, `sort(z)` and `sort sort(z)`;
  - none on tsline/tsrline for `sort(y)`;
  - exactly one `ignoring unsupported option(s): sort()` line on scatter, bar and lfit with `sort(z)`.
- **JO-27** `sort(z z)`: rc 0, z order, `"sortvars":"z z"`.

`test/test_adversarial.cscript`, appended after P20-36 as one run, with its header `display` lines:
- **JO-31** Hostile `sort()` text built by value (`local c` with `macval`): `"a"`, a backtick-quoted local reference, `\$G` with `global G "zz; drop _all"`, and `zz)`. dash rc == twoway rc, the data signature is unchanged (`datasignature`), `$G` is unchanged, and no page is written.
- **JO-32** 1,000 copies of `zz` are rc 0 in under 10 s. 1,000 copies plus `x*` give r(198) `* invalid name`.
- **JO-33** A user variable `__dashs1` is refused rc 110 before export, with the data unchanged. A registered spec whose global is edited to `"sortvars":"zz; drop"` is refused r(198) at `dash build` (`_ds_bad`), with nothing exported.

FAILS at base: JO-31 and JO-32 are accepted with a note, and in JO-33 the edited global is accepted.

**Mutation table**

| Break this | Test that must die |
|---|---|
| keep `sort_values(xvar)` in `map_line` | `TestTheDefaultIsTheDataOrder::test_a_mapper_joins_in_data_order[map_line]`, JO-01 |
| `_join_order` lets bare sort beat the key | `TestASortKeySetsTheOrder::test_the_key_beats_a_bare_sort`, JO-04 |
| `map_tsline` without `by_x=True` | `TestTimeSeriesJoinInTimeOrder`, JO-08 |
| `map_rline` masks on (x, y1, y2) | `TestRangeBoundsKeepTheirOwnRows::test_rline_bounds`, JO-05 |
| `map_rline` skips the empty copy | `::test_a_move_that_empties_one_bound` |
| drop `_dash_join_key`'s bounds check | `TestTheJoinKey::test_an_out_of_range_id_is_refused` |
| take the sort columns out after the qual take-out | `TestTakingTheSortColumnsOut::test_the_frame_loses_the_columns_and_the_keys_hold_statas_ranks` (reserved-prefix refusal) |
| leave a name off a served copy list | `test_statistical_helpers.py::TestTheServedAppCarriesEveryName`, `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads` |
| validate with `confirm names` | JO-21 (rc 7, multi-line) |
| check existence with `unab` alone | JO-22 (`in range not allowed`) |
| read `s(sort1)` before `_dash_opts_repeats` | JO-25 (`sort(x*) sort(z)` refused) |
| hold estimates on `_dq_n > 0` only | JO-10 |
| export the sort variable | JO-12, `TestTheSortColumnsNeverReachTheUser` |

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| `_join_order` precedence | pytest unit | none | n/a (shared class) |
| Data order, sort, ties, pairing, area with a missing y | pytest mappers | none / J8a | n/a |
| tsline/tsrline time order | pytest mappers and dispatch | none | n/a |
| Key order, key over sort, key under a view | pytest | none | n/a |
| Join key, sort-column validation, metadata pop | pytest unit, both loaders | ranks | yes |
| Saved == served == Stata for J1-J7, J10, J11 | pytest | join_order_truth.json | yes |
| Filter move keeps order | pytest + node (saved), served callbacks | none (`_DF`) | yes |
| by(), by(, total), by(, total missing) | pytest | J9 | yes |
| Per-bound range rows; a move that empties one bound | pytest + node | J8a/J8b | yes |
| Sort columns never visible | pytest | none | yes |
| Cost at 1e6 rows | pytest timing | none | n/a |
| Live twoway order, the build route, e(sample), served, minimisation | `test_wp29_truth.cscript` JO-01..JO-12 | none (live) | yes |
| sort() refusals and notes match twoway | `test_twoway_option_parity.cscript` JO-21..JO-27 | none (live) | n/a |
| Hostile sort() text, the reserved column, an edited spec | `test_adversarial.cscript` JO-31..JO-33 | none | n/a |
| Parity of the joining types | `test_mode_parity.py` CORPUS cases (task 02-10) | none | yes |
| Every cscript that draws a joining type stays green | driver runs (task 02-14) | none | yes |

Acceptance criteria:
- **AC-02.1** `python3 -m pytest test/test_join_order.py test/test_polyline_ordering.py test/test_glyphs.py test/test_mode_parity.py test/test_saved_filter_layers.py test/test_unsupported_report_is_true.py test/test_server_layer_defects.py test/test_abbreviations.py test/test_help_claims_8.py -q -n0` passes with no new skip.
- **AC-02.2** Block S02 of `test/test_wp29_truth.cscript` prints JO-01..JO-12 `PASS` under `WP29_ONLY=S02`. `test_twoway_option_parity.cscript` prints JO-21..JO-27 `PASS` and every TP case `PASS`. `test_adversarial.cscript` prints JO-31..JO-33 `PASS`. Each log has no ` FAIL` line and no `r(...)` line.
- **AC-02.3** Both served-name guards and `test_function_test_map.py`, `test_program_coverage_map.py` and `test_fixtures_are_committed.py` pass. `grep -c "_masked_order" dash_render.py test/function_test_map.py` prints 0 for each.
- **AC-02.4** The full suite is green once in the worktree. The P0.1 BUGS.md entry is closed in place. Both `<!-- WP-29 P0.1 -->` markers are replaced by lines ending `(WP-29, P0.1)`. `WP29_OPEN` has no `"P0.1"` key. `test_tracking_documents.py` passes.
- **AC-02.5** One commit on `wp29-s02`, subject ending `(WP-29 P0.1)`, whose body opens with `<scratch>/02-P0.1-failure.txt`. `git log -1 --format=%B | grep -ciE 'claude|anthropic'` prints 0.

## Tasks

**Commit boundary.** ONE commit (P0.1) holding tasks 02-03 to 02-17, subject `Join line-type plots in twoway's order and check sort() as twoway does (WP-29 P0.1)`. Task 02-17 makes it on the worktree branch `wp29-s02` (worktree `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp29-s02`) after one full suite run there.
- **Body.** It opens with `<scratch>/02-P0.1-failure.txt`, then the measured defect, then what changed and where. Then one line each:
  - `Regression: test/<file>.py::<Class>::<test> -- failed at <batch-1 base sha> with <text>`;
  - `Flipped: <node> -- <old expectation> was wrong because <why>` (one per E5 row, from `<scratch>/02-flips.txt`);
  - `Fixture: test/fixtures/join_order_truth.json (scripts/extract_join_order_truth.do)`;
  - `BUGS.md: "<the P0.1 title>" (closed)`.
- **Landing.** The merger lands it with this message (index.md step 1).
- **Rules.** Stata runs only through `scripts/stata_slot.sh`. No AI reference anywhere. Never stage `CLAUDE.md` or `.gitignore`.

<task type="auto" id="02-01">
  <name>Index the repository and measure impact</name>
  <files>none</files>
  <action><![CDATA[
In the worktree, run `gitnexus analyze` (E4: dash is not indexed), then `mcp__gitnexus__list_repos` to confirm `dash` is listed. Run `gitnexus_impact({target, direction: "upstream"})` for each of:
- GlyphMapper.map_line, map_connected, map_area, map_rline, map_rarea, map_rconnected, map_tsline, map_tsrline, _masked_order;
- _dash_add_glyph;
- DashRenderer._load_data, _make_figure_body, _add_glyph;
- ServerAppBuilder._generate_app_source;
- _dash_take_qual_columns.

Write each result's direct callers, affected processes and risk level to `<scratch>/02-impact.txt`. Add the grep callers of E4 for the Stata and Mata symbols GitNexus does not index: _dash_parse_plot_opts, _dash_fold_typed, _dash_process_segment, _dash_qual_gen, _dash_rep_scan, _dash_rep_reduce. This changes no repository file.
  ]]></action>
  <verify><![CDATA[`grep -c "risk" <scratch>/02-impact.txt` prints at least 15; `git -C <worktree> status --short` prints nothing.]]></verify>
  <done>The blast radius of every symbol this section edits was recorded, with the risk level of each.</done>
</task>

<task type="checkpoint" id="02-02">
  <name>Report the high-risk blast radius</name>
  <files>none</files>
  <action><![CDATA[
Report to the maintainer every HIGH or CRITICAL result in `<scratch>/02-impact.txt`, with its direct callers and affected processes. R8 expects HIGH on map_line, map_area, map_rline, map_rarea and _make_figure_body. Ask for approval to edit them under this plan. Do not edit any file until the maintainer approves in chat.
  ]]></action>
  <verify><![CDATA[The maintainer's approval is recorded in `<scratch>/02-impact.txt` with its date.]]></verify>
  <done>The maintainer saw the HIGH-risk symbols and approved the edits.</done>
</task>

<task type="auto" id="02-03">
  <name>Extract the join-order truth from Stata</name>
  <files>scripts/extract_join_order_truth.do, test/fixtures/join_order_truth.json, test/test_fixtures_are_committed.py</files>
  <action><![CDATA[
Create `scripts/extract_join_order_truth.do` exactly as "Stata truth" specifies:
- datasets A and B with their values;
- records J1-J11, `ranks` and `_meta`, built as that section says;
- the SVG reader for J8.

Run it with `dash_nobrowser=1 DASH_REPO=<worktree> scripts/stata_slot.sh <scratch>/s02-truth <worktree>/scripts/extract_join_order_truth.do` and read the log. A record that does not match a hand-derived order in "Stata truth" (dataset A) is investigated, never patched. The fixture is never edited by hand (R5).

`git add -f test/fixtures/join_order_truth.json`. In `test/test_fixtures_are_committed.py::test_the_scan_found_the_fixtures`, beside the existing `stat_truth.json` assertion (:101), add `assert any(f.endswith("join_order_truth.json") for f in found)`.
  ]]></action>
  <verify><![CDATA[
- `grep -c '^r([0-9]*);' <scratch>/s02-truth/extract_join_order_truth.log` prints 0.
- `python3 -c "import json;d=json.load(open('test/fixtures/join_order_truth.json'));print(sorted(d['_meta']), [r['obs'] for r in d['orders'] if r['id']=='J1-line'])"` prints `['born_date', 'dash_commit', 'extracted', 'stata_version'] [[1, 2, 3, 4, 5, 6, 7, 8]]`.
- `python3 -m pytest test/test_fixtures_are_committed.py -q -n0` passes.
  ]]></verify>
  <done>Stata's serset orders, by() panel orders, SVG paths of the missing-value cases and the rank rule were recorded in a stamped, committed-ready fixture.</done>
</task>

<task type="auto" id="02-04">
  <name>Write the failing renderer tests</name>
  <files>test/test_join_order.py</files>
  <action><![CDATA[
Create `test/test_join_order.py` with every class and test named in "TDD test stubs", using exactly those names and the helpers that section describes. Parametrise the fixture-driven tests by the fixture's record ids. The node runs use `js_runner.JsSession`, as test_saved_filter_layers.py:48 does. Pass `var_labels` explicitly wherever a label could matter (A7).

Do not touch dash_render.py. Run `python3 -m pytest test/test_join_order.py -q -n0 -p no:cacheprovider` against the unmodified worktree. Do not commit. Save the output to `<scratch>/02-P0.1-failure.txt`, with a first line naming the base sha (`cat <scratch>/batch-1-base.txt`). Separate the regression tests that failed from the guards that passed.
  ]]></action>
  <verify><![CDATA[
- The run reports no collection error.
- `grep -c "test_a_mapper_joins_in_data_order\[map_line\] FAILED\|1.0, 2.0, 3.0, 5.0, 6.0" <scratch>/02-P0.1-failure.txt` prints at least 1.
- Every guard named in "TDD test stubs" passed, and every other test failed.
  ]]></verify>
  <done>Every pytest regression test of P0.1 existed and failed for its recorded reason against the base, with nothing committed.</done>
</task>

<task type="auto" id="02-05">
  <name>Write the failing Stata cases</name>
  <files>test/test_twoway_option_parity.cscript, test/test_adversarial.cscript, test/test_wp29_truth.cscript</files>
  <action><![CDATA[
Write JO-21..JO-27, JO-31..JO-33 and the S02 block JO-01..JO-12 as "TDD test stubs" specifies:
- JO-21..JO-27 after TP-06b's last line (:571), adding a header `*!   JO-21..27 ...` line;
- JO-31..JO-33 after P20-36, with `display` header lines beside :3072-3086;
- JO-01..JO-12 above `* ==== append new blocks above this line ====` in test_wp29_truth.cscript (index.md R1 gate and timing lines).

Each `python:` block reads values with `sfi.Macro.getLocal` (test_cscript_hygiene.py:514). Expected lines are literal text; every comparison against twoway is made live.

Run each script through the two-line driver of "Stata truth" (`WP29_ONLY=S02` for the truth script). Append each log's `FAIL` lines and their count to `<scratch>/02-P0.1-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[
- Each log ends without `r(` on a line of its own.
- `grep -c "JO-.* FAIL" <scratch>/run_test_twoway_option_parity.log` is at least 3.
- `grep -c "JO-.* FAIL" <scratch>/run_test_wp29_truth.log` is at least 8.
- `grep -c "JO-02 PASS" <scratch>/run_test_wp29_truth.log` prints 1.
  ]]></verify>
  <done>Every Stata-side regression case of P0.1 existed and failed against the base where the stubs say it fails, and its failure text was saved.</done>
</task>

<task type="auto" id="02-06">
  <name>Join every connecting type through one rule</name>
  <files>dash_render.py, test/function_test_map.py, test/test_server_layer_defects.py</files>
  <action><![CDATA[
In dash_render.py:
- Add `GlyphMapper._join_order` (TR-02.1) after `_masked_index` (:8605).
- Rewrite map_line, map_connected, map_area, map_rarea, map_rline (two copies, always both, A9), map_rconnected, map_tsline and map_tsrline as TR-02.2 says, with their docstrings and comments.
- Delete `_masked_order` (:8630-8640).
- Add `_DASH_JOIN_TYPES` after `_DASH_QUAL_NAME_RE` (:24243), and the `order` keyword to `_dash_add_glyph` (:24840) and `DashRenderer._add_glyph` (:26374) (TR-02.3).

In test/function_test_map.py, replace the `_masked_order` entry (:156) with `'GlyphMapper._join_order'` (TR-02.18).

In test/test_server_layer_defects.py, restate `TestTheMaskedIndex::test_masked_order_is_the_same_rows_sorted_by_x` and `::test_the_two_select_the_same_set` for `_join_order` (E5 table). Record both in `<scratch>/02-flips.txt` as `Flipped:` lines.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_join_order.py -q -n0 -k "JoinOrderRule or DefaultIsTheDataOrder or TimeSeries or ASortKeySetsTheOrder or (RangeBounds and not served and not move)"` passes; `python3 -m pytest test/test_server_layer_defects.py -q -n0 -k MaskedIndex` passes; `grep -c "_masked_order" dash_render.py` prints 0.]]></verify>
  <done>Every joining mapper drew in data order, x order under sort, key order with a key and time order for the ts types, and each range bound kept its own rows.</done>
</task>

<task type="auto" id="02-07">
  <name>Carry the sort keys through both renderers</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
In dash_render.py:
- Add the constants and the four functions of TR-02.4 (after `_dash_qual_mask`, ~:24345).
- Make the saved changes of TR-02.5 (`_load_data` :25197; the plot dispatch :26244-26278).
- Make the served changes of TR-02.6: emitted load :29918, meta, `_sort_keys`, `_dash_draw_layer` :30211-30231, and both copy-list entries at :28441 and :28546.
- Rewrite the comments of TR-02.7, editing comment text only inside `_FILTER_JS`.

In test/function_test_map.py, add the four function entries of TR-02.18 in alphabetical place.
  ]]></action>
  <verify><![CDATA[
- `python3 -m pytest test/test_join_order.py -q -n0 -k "not cscript"` passes (every pytest stub green).
- `python3 -m pytest test/test_statistical_helpers.py -q -n0 -k CarriesEveryName` passes.
- `python3 -m pytest test/test_resource_limits.py -q -n0 -k DefinesEveryName` passes.
- `python3 -m pytest test/test_function_test_map.py test/test_qualifier_columns.py test/test_varlist_expansion.py -q -n0` passes.
  ]]></verify>
  <done>Both renderers took the rank columns out of the frame, ordered each joining layer by them through the same helpers, and showed them nowhere.</done>
</task>

<task type="auto" id="02-08">
  <name>Check sort() as twoway checks it</name>
  <files>dash.ado, dash_parse.mata</files>
  <action><![CDATA[
In dash.ado:
- Add `sreturn local sort1 : copy local sort1` after :1188 (TR-02.8). Rewrite the comment :1079-1084 in exactly six lines, keeping the static line :1085 (D-a).
- Add the programs `_dash_sort_names` (TR-02.11) and `_dash_sort_opt` (TR-02.12) directly after `_dash_fold_typed` (:1708-1760).
- Call `_dash_sort_opt "`ptype'"` after :3961 (TR-02.10).
- Write `"sortvars"` in the plot JSON (TR-02.13, :4145-4172).

In dash_parse.mata, make the empty-copy rule of `_dash_rep_scan` (:4288) and `_dash_rep_reduce` (:5077) (TR-02.9), with a comment citing M4.

Run test_twoway_option_parity.cscript through the driver.
  ]]></action>
  <verify><![CDATA[In `<scratch>/run_test_twoway_option_parity.log`, `grep -c "JO-2[1-7] PASS"` prints 7 and `grep -c "JO-2.* FAIL"` prints 0; `python3 -m pytest test/test_twoway_option_parity.py test/test_help_conformance.py test/test_abbreviations.py -q -n0` shows only `test_the_tr_23_6_scans_see_what_they_look_for` failing (flipped in 02-11).]]></verify>
  <done>sort() was refused where and as twoway refuses it, honoured silently on the six joining types and tsline/tsrline, named elsewhere, and written to the spec as the unabbreviated varlist.</done>
</task>

<task type="auto" id="02-09">
  <name>Export the rank columns on both routes</name>
  <files>dash.ado, dash_parse.mata, test/program_coverage_map.py</files>
  <action><![CDATA[
In dash_parse.mata:
- Add `_dash_sort_reset`, `_dash_sort_scan` and `_dash_sort_export` (TR-02.14) after `_dash_qual_orders` (:3140-3157).
- Add their three header-index lines beside :176-186.

In dash.ado:
- Add the three names to `_needed` (:232-246).
- Add the program `_dash_sort_gen` (TR-02.15) after `_dash_qual_gen_by`.
- Make both routes' changes (TR-02.16): immediate :6060-6138, build :7086-7140 and :7281.
- Extend `_dash_qual_gen`'s message (TR-02.17).

Add the program_coverage_map.py entries of TR-02.18.

Run test_wp29_truth.cscript with `WP29_ONLY=S02` and test_adversarial.cscript through the driver.
  ]]></action>
  <verify><![CDATA[
- `grep -c "JO-0[0-9] PASS\|JO-1[0-2] PASS" <scratch>/run_test_wp29_truth.log` prints 12.
- `grep -c "JO-3[1-3] PASS" <scratch>/run_test_adversarial.log` prints 3.
- Neither log has a ` FAIL` line.
- `python3 -m pytest test/test_program_coverage_map.py -q -n0` passes.
  ]]></verify>
  <done>Stata wrote one rank column per distinct sort() varlist on both routes, under the estimates hold, counted, dropped on every exit, and the page and app joined as live twoway does.</done>
</task>

<task type="auto" id="02-10">
  <name>Flip the mapper-level x-order pins</name>
  <files>test/test_polyline_ordering.py, test/test_glyphs.py, test/test_mode_parity.py</files>
  <action><![CDATA[
Flip the E5 rows for these three files exactly as the table says:
- rename and re-assert the polyline tests, and add the `[sort]` cases;
- rewrite the module docstring's WP-09 claim to twoway's rule;
- re-assert P1A-89 and the connected test;
- the linked by() panel test asserts each panel's xs equal `_DF`'s weights of that group in data order; docstring :3215.

Append to test_mode_parity.py's CORPUS (:1126) cases for line, area, rline, rarea and rconnected with no option and with `{"sort": "sort"}`, unless `grep -n "_case(" test/test_mode_parity.py` shows a case with that type and options. Do not touch ALLOWED or _MUST_WARN (R6).

Add every flip to `<scratch>/02-flips.txt` as a `Flipped:` line.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_polyline_ordering.py test/test_glyphs.py test/test_mode_parity.py -q -n0` passes; `pytest --collect-only -q` node counts for the three files are no lower than at the base.]]></verify>
  <done>The pins that asserted x order asserted twoway's data order, the sort cases kept x order, and the parity corpus covered the joining types.</done>
</task>

<task type="auto" id="02-11">
  <name>Flip the page-level and structural pins</name>
  <files>test/test_saved_filter_layers.py, test/test_unsupported_report_is_true.py, test/test_abbreviations.py</files>
  <action><![CDATA[
Flip the E5 rows for these files:
- In test_saved_filter_layers.py:
  - set `[line|connected]` to 3350, 1800, 3100, 2010, 2650, keeping `[tsline]`, and rewrite the class docstring :311-314;
  - give the hostile-name test the same data-order list;
  - make `TestALinesOwnQualifier` hold a per-type expectation (the data-order lists for line and connected, the old sorted lists for tsline) and the data-order `_IN_3_8` for rconnected, rewriting docstring :545-546.
- In test_unsupported_report_is_true.py, set `PLOT_VALUES["sort"] = ("sort", "", "scatter")` (:140) with a comment citing P0.1.
- In test_abbreviations.py, change `len(with_syntax) == 12` to 13 (:604) and name `_dash_sort_names` in its comment. Keep 108 at :618 if the comment rewrite kept six lines, else set it to the measured count with the reason.

Record every flip in `<scratch>/02-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_saved_filter_layers.py test/test_unsupported_report_is_true.py test/test_abbreviations.py test/test_help_claims_8.py test/test_statistical_defaults.py test/test_help_conformance.py -q -n0` passes.]]></verify>
  <done>Every saved-page and structural pin of the old behaviour asserted the new one with its reason recorded, and the pending-list counts stayed 48.</done>
</task>

<task type="auto" id="02-12">
  <name>Flip the Stata note pins</name>
  <files>test/test_twoway_option_parity.cscript</files>
  <action><![CDATA[
Flip the three TP-06/TP-06b rows of E5:
- move row 1 (:451-453) to `dash scatter mpg weight, sort(mpg)`;
- turn the `sort sort(mpg)` block (:495-525) into: rc 0, no note, `_ztp_has zqtp sort1` not found, `_ztp_has zqtp sortvars` found;
- drop the two line items from the TP-06b loop (:557), and add them to a new loop that asserts no note;
- rewrite the comment :527-534 and the header line `*!   TP-06`.

Run the script through the driver. Record the flips in `<scratch>/02-flips.txt`.
  ]]></action>
  <verify><![CDATA[In `<scratch>/run_test_twoway_option_parity.log`, `grep -c " FAIL" ` prints 0, `grep -c "TP-06 PASS" ` is at least 8 and `grep -c "JO-2[1-7] PASS"` prints 7.]]></verify>
  <done>The parity script certified the new notes and refusals against live twoway with no TP case lost.</done>
</task>

<task type="auto" id="02-13">
  <name>Correct the stale x-order comments</name>
  <files>test/test_filters.py, test/test_help_claims_1.py, test/test_served_linked_views.py</files>
  <action><![CDATA[
Edit comment and docstring text only, replacing "a line sorted by x" / "a line sorted along x" with "a line in its join order":
- test_filters.py :1677;
- test_help_claims_1.py :957;
- test_served_linked_views.py :24 and :530.

Historical narratives elsewhere ("a copy sorted by x" describing a past defect) are left. No code changes.
  ]]></action>
  <verify><![CDATA[`git -C <worktree> diff --stat test/test_filters.py test/test_help_claims_1.py test/test_served_linked_views.py` shows only changed comment lines; `python3 -m pytest test/test_filters.py test/test_help_claims_1.py test/test_served_linked_views.py -q -n0` passes.]]></verify>
  <done>No test docstring still described x order as dash's current behaviour.</done>
</task>

<task type="auto" id="02-14">
  <name>Run every cscript that draws a joining type</name>
  <files>none</files>
  <action><![CDATA[
List the scripts with `grep -lE "\b(line|connected|area|rline|rarea|rconnected|tsline|tsrline)\b" test/*.cscript` (57 at 7421d3d). Run each one through the two-line driver of "Stata truth" with `scripts/stata_slot.sh` (at most three at once; the wrapper enforces it; `run_in_background` with a log per script). Read each log; never relaunch to check.

A FAIL that pins x order or the old sort() note is flipped in that script with a comment citing P0.1, recorded in `<scratch>/02-flips.txt` and added to this section's commit (rule 7 needs no new test for a flip). Any other FAIL is a regression of this section: fix the code, not the test. A SKIP for Python is investigated (python_exec hazard), never accepted.
  ]]></action>
  <verify><![CDATA[`for f in <scratch>/run_test_*.log; do grep -l " FAIL" "$f"; done` prints nothing, and every listed script has a log ending in its own summary line.]]></verify>
  <done>Every certification script that draws a joining type passed on the fixed tree, with any x-order pin flipped and recorded.</done>
</task>

<task type="auto" id="02-15">
  <name>Document the join order in help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
Make five edits:
1. After the "A range type takes three variables" paragraph in {marker plottypes} (:228-247), add a {pstd} paragraph "Join order":
   - line, connected, area, rline, rarea and rconnected join their points in the data's order, as twoway does;
   - sort joins them in the order of x;
   - sort(varlist) joins them in the order of the varlist, winning over sort, and of several copies the last one that is not empty wins;
   - ties keep the data's order (twoway's changes from run to run);
   - strings sort byte by byte and . before .a before .b;
   - tsline and tsrline join in time order and ignore both;
   - on unsorted data an area follows the data, as twoway draws it (add sort for a picture along x);
   - each bound of rline keeps its own missing values;
   - a malformed name in sort() is refused on every type, and a name that is no usable variable on the plot types that draw observations, r(198), in twoway's words;
   - the sort() variables are never written to the dashboard.
2. Rewrite the Unsupported entry "Connection order" (:3229-3241): sort and sort(varlist) are named on every plot type except the six and tsline/tsrline. Keep at least one `{opt sort` token so the Unsupported list still holds sort (D-a).
3. Make :1397 "a line still in its join order".
4. Add `{cmd:__dashs}{it:#}` (the join-order columns) to the reserved-names sentence :170-173.
5. Add to the repeats sentence (~:478-480) that of sort(varlist) the last copy that is not empty counts.

Write the refusal words exactly as E1.4/E1.5 quote them.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_conformance.py test/test_help_claims_8.py test/test_help_claims_1.py -q -n0` passes; `grep -c "join order\|Join order" dash.sthlp` is at least 2.]]></verify>
  <done>The help stated twoway's join rule, the sort() refusals, the reserved join-order columns and where sort is still named, and its conformance tests passed.</done>
</task>

<task type="auto" id="02-16">
  <name>Run the section's full verification</name>
  <files>none</files>
  <action><![CDATA[
Run `python3 -m pytest test/ -q` once in the worktree and read its log; never launch a second run while one executes. A failure that pins x order is flipped in its file with a `Flipped:` line. Anything else is fixed in the code.

Then run, targeted:
- test_mode_parity.py;
- the two served-name guards;
- test_function_test_map.py, test_program_coverage_map.py, test_fixtures_are_committed.py and test_varlist_expansion.py (the SHA-256 baseline is never re-baselined, R7).

Run `gitnexus_detect_changes()`. Confirm it lists only the files in this section's header and the symbols of TR-02.1 to TR-02.18, and save it to `<scratch>/02-detect.txt`.
  ]]></action>
  <verify><![CDATA[The full suite's tail reports 0 failed and no new skip; `<scratch>/02-detect.txt` names no symbol outside this section; `git -C <worktree> diff --name-only` lists no `CLAUDE.md`, `.gitignore`, scratch or `*.html` path.]]></verify>
  <done>The whole suite, the parity and registry guards and the change-scope check were green on the section's tree.</done>
</task>

<task type="auto" id="02-17">
  <name>Close P0.1 and make the commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
**BUGS.md.** In S01's open P0.1 entry, in place:
- turn `- [ ]` into `- [x]`;
- replace its Resolution with: `- Resolution: Fixed <ddmonyyyy> (WP-29, P0.1). GlyphMapper._join_order joins line, connected, area, rline, rarea and rconnected in data order, in x order under sort and in a Stata-made rank under sort(varlist) (dash.ado _dash_sort_opt checks sort() as twoway does; _dash_sort_gen writes __dashs<k>; _dash_take_sort_columns and _dash_join_key read it), in both renderers and after every filter move; tsline and tsrline join in time order; each bound of rline and tsrline keeps its own rows. Pinned by test/test_join_order.py::TestTheDefaultIsTheDataOrder::test_a_mapper_joins_in_data_order, test/test_join_order.py::TestBothModesJoinAsTwowayDoes::test_saved_and_served_match_twoway, test/test_join_order.py::TestAFilterMoveKeepsTheJoinOrder::test_saved_page_under_node, test/test_join_order.py::TestRangeBoundsKeepTheirOwnRows::test_rline_bounds, test/test_twoway_option_parity.cscript JO-21, test/test_wp29_truth.cscript JO-01; fixture test/fixtures/join_order_truth.json. Residual, deferred (WP-29): rarea with exactly one bound missing on a row leaves that row out of both bounds where twoway's polygon keeps the other; points whose keys tie keep the data's order where twoway's order is random; connected's markers paint in data order under sort.`

**CHANGELOG.md.** Replace the two `<!-- WP-29 P0.1 -->` markers, in place, with lines ending `(WP-29, P0.1)`:
- **Results** (in the `**WP-29 (drop-in P0, 30sep2026)**` group):
  - `dash line mpg weight` and connected, area, rline, rarea and rconnected on data not sorted by x joined in x order, the picture twoway draws only with `sort`; they now join in the data's order. Use the old/new values from the failure file: on the ten-car parity frame, 1800, 2010, 2200, … now 2930, 3350, 2200, ….
  - After a move to Foreign, 1800, 2010, 2650, 3100, 3350 now 3350, 1800, 3100, 2010, 2650.
  - `sort(varlist)` was ignored with a note; it is now honoured.
  - rline's lower path on x = 2 5 3 6 1 7 with the upper bound missing at 5 was 1 2 6 7, now 2 5 6 1 7.
  - The WP-09 line under "Geometry, dates and labels" ("now draw along x") describes the order this replaces.
- **Changed behaviour**:
  - The six types join in the data's order unless `sort` or `sort(varlist)` is given; add `sort` for the old picture.
  - An invalid `sort()` is refused r(198) in twoway's words (`sort(x*)`: `* invalid name`; `sort(nosuch)` on line: `variable nosuch not found`, `option sort() incorrectly specified`), where dash accepted it with a note.

Write nothing elsewhere.

**test/test_tracking_documents.py.** Delete only the `"P0.1"` line of `WP29_OPEN`.

**Commit.**
1. Run `python3 -m pytest test/test_tracking_documents.py -q -n0`.
2. Grep the three files and `<scratch>/02-commit-msg.txt` for `claude|anthropic`.
3. Stage exactly this section's files: the header list, `git add -f` for the fixture, and any cscript flipped in 02-14.
4. Commit on `wp29-s02` with `git commit -F <scratch>/02-commit-msg.txt`. The message is the subject of "Commit boundary" and the body it describes.
5. Grep `git log -1 --format=%B` again.
  ]]></action>
  <verify><![CDATA[
- `python3 -m pytest test/test_tracking_documents.py -q -n0` passes.
- `grep -c '<!-- WP-29 P0.1 -->' CHANGELOG.md` prints 0, and `grep -c '(WP-29, P0.1)' CHANGELOG.md BUGS.md` prints 2 and 1.
- `git log -1 --format=%s | grep -c '(WP-29 P0.1)'` prints 1.
- `git log -1 --format=%B | grep -ciE 'claude|anthropic'` prints 0.
- `git show --stat HEAD` lists no `CLAUDE.md` or `.gitignore`.
  ]]></verify>
  <done>P0.1 was closed in BUGS.md naming existing tests, both CHANGELOG markers were replaced, its allowance key was removed, and one green commit on `wp29-s02` carried the section.</done>
</task>

## Section completion criteria

- Both modes join line, connected, area, rline, rarea and rconnected as twoway does, at first paint, per by() panel, in the Total panel and after every filter move:
  - in data order by default;
  - in x order under `sort`;
  - in Stata's order of the varlist under `sort(varlist)`.

  tsline/tsrline join in time order. Each range-line bound keeps its own rows. `TestBothModesJoinAsTwowayDoes` and JO-01..JO-12 prove it against Stata.
- `sort()` is refused, named or silent exactly as twoway behaves on all 40 types (JO-21..JO-27). Hostile text is refused with nothing expanded (JO-31..JO-33).
- The rank columns and sort variables reach no reader-visible surface (`TestTheSortColumnsNeverReachTheUser`, JO-12). Every input is validated, and ids are bounds-checked.
- `_masked_order` is gone. Both copy lists, function_test_map.py and program_coverage_map.py are current.
- Every E5 pin was flipped with a `Flipped:` line, none deleted, and the node count never fell. Every cscript that draws a joining type passed (02-14).
- One commit, `(WP-29 P0.1)`, on a green tree. BUGS.md P0.1 is closed with a Resolution naming existing tests. Both CHANGELOG markers are replaced. `WP29_OPEN["P0.1"]` is gone.

## Notes

- **One rank column per distinct sort list.** One rank column per DISTINCT `sortvars` value, shared by every plot that names it, in `_dash_sort_scan`'s first-seen order. `__dashs<k>` is numbered independently of `__dashq<k>`.
- **Positions vs labels.**
  - Saved sources carry `__dash_row__`, positions into `self.df`. `sort_keys` Series are indexed like `self.df` at load time, so `rank.to_numpy()[ids]` is exact.
  - Served sources carry pandas `index` labels (the filtered frames keep the original labels), so `reindex` is exact.
  - A source with neither is a defect, and `_dash_join_key` raises.
- **Why a rank and not the variables.** The data writer turns every missing value into null (dash_render.py:1394), so `.`/`.a`/`.b` could not be ordered in Python. Exporting the sort variables would also embed data the dashboard does not show (BR-02.7, cf. P0.11).
- **The served redraw pairs sources by zip** (dash_render.py:31212-31232). rline's two copies must both exist on every draw (A9), or the count warning fires and the wrong source is refreshed.
- **`s(sort1)` is now in s().** `_dash_rep_keyof` keys `sort(...)` as `sort1` (A2). `_dash_validate_opts`' snapshot/restore (dash.ado:2447) carries it harmlessly. `_dash_plot_opts_to_json` never writes it (test_twoway_option_parity.py:271).
- **Shared files (merge rules).**
  - **R1:** JO cases append to test_twoway_option_parity.cscript (S02 only in batch 1), test_adversarial.cscript (S02, then S06, then S08, as contiguous runs in merge order) and block S02 of test_wp29_truth.cscript, in section order. The runner and hygiene pins are not touched.
  - **R2:** copy-list entries at the anchors of TR-02.6. Map entries go in alphabetical place.
  - **R3:** dash.sthlp edits are confined to the paragraphs of task 02-15. In CHANGELOG.md only the two P0.1 markers are replaced. BUGS.md is edited in place in the P0.1 entry only, and test_tracking_documents.py loses only the `"P0.1"` line.
  - **R4:** `sort()` validation is S02's.
  - **R5:** the fixture is never hand-patched, and carries `_meta`.
  - **R6:** CORPUS appends only.
  - **R7:** flips, never deletions.
  - **R8:** tasks 02-01, 02-02 and 02-16.
- **Batch-1 neighbours.**
  - S06 edits the dash.ado export path above :6060 and the hover extraction. S08 rewrites every temp-file writer, including `_dash_write_data`'s callers at :6116 and :7134. S02 lands before both, so their hunks apply to S02's text; the merger keeps the `_dash_sort_vars` argument on both write lines.
  - S07 edits the per-plot qualifier view block above the plot dispatch in `_make_figure_body` (:26170-26215). S02's `_jo` line sits below it.
  - S05 edits `_FILTER_JS` code. S02 changes comment text there only (:15970-15979).
- **For S14 (blocks).** `_dash_take_sort_columns` accepts any distinct positive integer key (A8), so writing a subset of rows keeps the ranks valid. If S14 changes `self.df`'s rows after `_load_data`, it must rebuild `self.sort_keys` on the new index. The saved `_dash_join_key` is positional.
- **Stata invocation.** Every Stata run goes through `scripts/stata_slot.sh <scratch-dir> <file>.do` with `dash_nobrowser=1`. Never the GUI, never a bare `stata-mp`, never `make cert` inside the section. A cscript is run through the two-line driver. Many concurrent sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`; check `c(python_exec)` before trusting a skip.
- **Line numbers** are 7421d3d's. S01, S09 and S03 merge before S02, but the worktree is cut from the batch-1 base, so the anchors hold inside the worktree. Symbols are authoritative.

### Notes for the closeout (S15; A5)

- **ROADMAP WP-29 entry, P0.1 line.** "Join order matches twoway (data order; sort; sort(varlist) by a Stata rank; ts types in time order; per-bound range rows); sort() checked as twoway checks it. Commit <sha>."
- **GAPS2.**
  - Fully closed by P0.1 if their Gap text is only join order or sort(varlist): A1-a, A1-c, A4-o, B12-e, G15-b. S15 reads each entry.
  - Partly closed if the entry also names connect()/cmissing() (P1) or the rarea one-bound polygon.
- **AUDIT and REMAINING.** AUDIT-08 and AUDIT-10 are closed. REM-§2-S06-sort and REM-S06-b are closed.
- **GAPS.md.** E1's "sort is inert" is now true only off the six joining types and tsline/tsrline.
- **AGENTS.md invariant "join order".** `GlyphMapper._join_order` is the only place a joining layer's rows are ordered. Rank columns `__dashs<k>` are made in Stata and taken out before any source exists. Pinned by test_join_order.py and JO-01.
- **Residuals to record.**
  - rarea with exactly one bound missing on a row (O1).
  - Stable vs random ties.
  - Marker paint order under sort (O6).
  - sort/sort() still named on mspline, mband, lfit, qfit, lowess, lpoly and fpfit although twoway's SVG is identical with and without them (M5). A P2 candidate.
  - connect() on scatter (P1).
  - `sort() sort()`, all copies empty: unpinned.
