# WP-30 open questions: status (consolidated 06oct2026; all resolved 06oct2026)

Every question raised by section writers, the orchestrator and the review pass (review-notes/g01-g09, the S31-S36 review). RESOLVED gives how and where. **All resolved (06oct2026):** the maintainer answered every row of index.md "Decisions for maintainer ratification" (44 rows; A151) on 06oct2026, 35 as recommended, rows 4, 8, 12, 22, 25, 27, 32 and 36 CHANGED and row 29 otherwise than recommended; the section files carry each answer ("(ratification 06oct2026)" in their Review amendments). No question remains open.

## Section questions

- **Q-57.1 (S57)** S46's 64 MB estimator memo needs a lock for S57's worker. RESOLVED (orchestrator ruling, applied): S46 adds `state.memo_lock` (threading.Lock) around memo get/put in its own commit (section-46 TR-46.3, TR-46.8, `TestEstimatorMemo::test_the_lock_guards_get_and_put`); S57 relies on it, edits no memo, and 57-01 stops if the lock is absent.
- **Q-43.1 (S43)** Where S43 gives region colours their intensity base. RESOLVED: S43 edits only S38's `_dash_region_spec` `_read(arg, role)` step, passing `base=base_hex` (section-38 TR-38.2 "The S43 hook", section-43 TR-43.9); no `_make_figure_body` or template edit, no residual.
- **Q-38.1 (S38)** twoway's undocumented `shadestyle()`/`intensity()`/`iintensity()`/`ishadestyle()`/`marginonly` in regions. RESOLVED under M5: named, not drawn; S58 files a P2 row (section-38 Notes).
- **Q-39.1 (S39)** The `reflines` count over all observations' by() panels (an upper bound). RESOLVED: kept per A68 and the dash.ado:7520 precedent (rule 1); the message says "up to"; the renderer enforces only the 100,000 ceiling (section-39 Notes). The limit itself is ratification row 6.
- **Q-40.1 (S40)** `test_unsupported_report_is_true.py:137` is `recast()`. RESOLVED: S45 flips :137 and HC8-02's recast; S40 flips :95/:99 and HC8-02's cmissing, connect and sort (index R9, manifest S40 notes).
- **Q-41.1 (S41)** `bokeh serve`'s lenient origin matcher. RESOLVED in S41 TR-41.19: the bokeh-serve branch calls `_dash_harden_origin_check()` (register P1.30.9/A109 and rule 1); no P2 row; noted under ratification row 19.
- **Q-45.1 (S45)** `type` holds the drawn type and `recast_from` the typed one, against A60's "keep `type`, write `recast`". RESOLVED: ratification row 40, ratified 06oct2026 as recommended.
- **Q-48.1 (S48)** Refuse unknown by() words. RESOLVED under M5: refused in twoway's order, over the whole by() grammar (section-48 Notes).
- **Q-48.2 (S48)** The `iscale()` bound of 10,000. RESOLVED: ratification row 41, ratified 06oct2026 as recommended (the 10,000 bound).
- **Q-28.1 (S28; raised again by S53)** The filled box behind by() panel labels. RESOLVED: ratification row 36, answered 06oct2026, CHANGED: "Add to S53". S53 draws twoway's filled box behind each by() panel label; S58 files no P2 row for it (section-28 Notes, section-53, section-58).
- **S54** The "Toolbar, save as SVG" row of the Server Mode table. RESOLVED: an R3 exception in index R3 (S54 the only editor of that row in batch 19).
- **S55** The expected-CRITICAL list named `_build_filter_widgets`; may S55 edit S21's `_dash_axis_plan`. RESOLVED: S55 edits `_dash_build_hover` only; its 55-04 is a guard check that stops and reports, never an edit (index 19.0, A153, manifest S55).
- **S56** Ratification row 26 (IR-7) and the option-surface regeneration; the dash.sthlp:598-599 example in S06's paragraph. RESOLVED: TR-56.12/TR-56.16 handle both outcomes of row 26; the example is an R3 exception (index R3).
- **S44** BUGS.md:2523 closure wording. RESOLVED in section-44: the Resolution line is replaced in place ("Closed <date> by disposition, by WP-30 section 44 (entry P1.3b). …"), with no `(WP-30, P1.3b)` token.
- **S46/S47/S51/S40** Declared-plot and page-digest movers missing from R10. RESOLVED: R10 now lists S18, S32, S36, S40, S45, S49, S51 and S56 for :607 (not S37) and S18 and S47 among the digest movers; S46 moves neither.
- **Q-20.1 (S20)** dash's stricter per-element value checks. RESOLVED by register P1.1.5's precedent: keep the per-element refusal; "dash refuses what twoway accepts" is P2.14 (section-20 Notes).
- **Q-22.1 (S22)** "One line per dash command" (register P1.28.3). RESOLVED: ratification rows 35 and 16, ratified 06oct2026 as recommended (the per-file-writing-command reading).
- **Q-37.1 (S37)** Per-scheme text box sizes. RESOLVED under M1 and register P1.24.3: commit 2 regenerates the scheme files (index A152: S37 regenerates and still merges first in batch 13).
- **Q-34.1 / S34 Q1** Four one-line `_generate_app_source` edits in batch 12. RESOLVED: ratification row 38, granted 06oct2026 as recommended.
- **S33 Q1** The `color_idx=` keyword in seven mappers S32 edits (A139). RESOLVED: ratification row 37, granted 06oct2026 as recommended (option (a)).
- **S36 D-36c** 57 Stata-known style names outside the curated table. RESOLVED: ratification row 39, ratified 06oct2026 as recommended.
- **S08 Q1** `xsize()`/`ysize()` in the absolute-unit reference (register P1.12.4). RESOLVED: ratification row 30, ratified 06oct2026 as recommended (option (b); S58 files the `xsize()`/`ysize()` P2 row).
- **S10/S11/S12** The batch-4 A139 exception for `_dash_plot` and `_needed`. RESOLVED: ratification row 31, granted 06oct2026 as recommended.
- **S11 Q-11.1** A used blank quoted stylelist element. RESOLVED: ratification row 32, answered 06oct2026, CHANGED: "Refuse r(198)". A used blank quoted element is refused r(198) with dash's own clear message, not read as `.`; no M5 exception (section-11).
- **S12** `$dash__display` also fencing SB-07..SB-11 (register P1.27.6). RESOLVED: ratification row 33, ratified 06oct2026 as recommended.
- **S13 D-13b** Draw-time-only over-wide line widths noted, not refused. RESOLVED: ratification row 34, ratified 06oct2026 as recommended (D-13b).
- **S01 P-1** `PhilSchummSuggestion.md` in the package root makes the packaging root test red (re-run 06oct2026: 1 failed, 1 passed, 11 deselected). RESOLVED: ratification row 29, answered 06oct2026: "Ignore the file in the packaging root test". `PhilSchummSuggestion.md` is added to `test/test_packaging.py::_ROOT_ALSO` (uncommitted); the root test passes; the change lands before step 0a after one full run.
- **S21 D-21h** Help sentences S21 makes false. RESOLVED: S21 edits both (index R3: Exporting :1203-1204, Faceting :2084-2086). S21's ratification rows 1 and 3 stay on the list.
- **S15 P1.2.7** Minor ticks. RESOLVED by register P1.2.7: S21's (manifest S15 scope amended).
- **S16 Q1** The histogram's intensity until S24. RESOLVED by M1 and register P1.4.2.
- **S24 Q1** Who moves the directive-count pin first. RESOLVED by R10: S15 moves it and the help sentence to measured bounds, then S21 (only if red), S24 (renames), S33, S36, S37, S50 (only if red), S53.
- **S06** Note visibility classes and form. RESOLVED from register P1.26.2/P1.26.4 (A82/A84); ratification row 13 ratified 06oct2026 as recommended.

## For the orchestrator (no maintainer answer needed)

- **S28/S48 `t` spelling.** S48's grammar transcribes `Title` with minimum `t` from graph_g.class; S28's `_DASH_BY_TEXT_SPELLINGS["title"]` starts at `ti`. RESOLVED (orchestrator rule; the measurement is taken at batch 17, no maintainer answer needed): if S48's `accepted` probe shows `by(foreign, t("a"))` drawn as a title by twoway, S48 adds `t` to the tuple in its commit; S53's spellings-agree-with-grammar test catches any mismatch at batch 18.
- **S39 `_dash_by_panels`.** S39's TR called `_dash_by_panels` a new ado, but a program of that name exists at dash.ado:3340 (rclass, `r(kept)`) and S56 reads it. RESOLVED in the cross-file pass: S39's new program is `_dash_refline_panels` (section-39 TR-39.4, TR-39.8, 39-04).

## From the S31-S36 review (04oct2026)

All seven index/manifest fixes are applied (index R2 S31 and S35 rows, R3 S31/S36, R10 S36 movers, 11.0/12.0 expected lists, batch 12 / R12 S34 exception, manifest S36 notes). Its three maintainer questions are ratification rows 37 (S33 Q1), 38 (S34 Q1) and 39 (S36 D-36c), each ratified 06oct2026 as recommended.

## Maintainer ratification (06oct2026)

Rows not raised above as section questions, answered 06oct2026 (index.md "Decisions for maintainer ratification"):

- **Row 4 (A10, P1.4.4)** RESOLVED, CHANGED: no unread user-scheme key note at all; the scheme parser keeps reading and retaining every directive (none discarded) for later versions (section-33, section-34).
- **Row 8 (A34, P1.11.4)** RESOLVED, CHANGED: mirror twoway: a label holding `{c 0}` is emptied; C0/C1 codes are kept and escaped at every HTML/JS sink (rule 1) (section-29).
- **Row 12 (A77, P1.23.4)** RESOLVED, CHANGED: a literal coordinate outside 0100-9999 on a date axis is drawn, with no note; the Python and JS date conversion handles it safely (section-35).
- **Row 22 (A116, A117, P1.31.7-8)** RESOLVED, CHANGED: per-session growth bound 80 MB at 200k rows x 3; the 64 MB memo unchanged (section-46).
- **Row 25 (A125, P1.33.4)** RESOLVED, CHANGED: manual only: S05 measures the floor Python once in WP-30; the release gate gains no leg (section-05, section-58).
- **Row 27 (A37, P1.12.6)** RESOLVED, CHANGED: fixed in WP-30 by S08 (nonselection and muted copies follow the option appliers); P2.49 is not filed and its id is withdrawn (section-08, section-58).
- **Row 44 (S58 Q3)** RESOLVED as recommended: dash.sthlp's "named in a warning" stays unreworded and S58 files a P3.3 note (section-58, section-06).
- Every other row (1-3, 5-7, 9-11, 13-21, 23, 24, 26, 28, 42, 43): ratified 06oct2026 as recommended.
