# WP-28 plan review — consistency and dependencies

> Review categories 2 (consistency) and 3.5 (dependencies) of `.ultraplan/`.
> Read in full: `PRD.md`, `DISCOVERY.md`, `PLAN.md`, `sections/BRIEF.md`, `sections/index.md`,
> `sections/section-01` … `section-19` (12,267 lines). Claims about the tree were checked at
> the working copy (`test/test_cscript_hygiene.py:292,308`, `test/run_all_cscripts.do`,
> `test/test_statistical_helpers.py:817-860`, `dash_render.py` symbol lines, `CHANGELOG.md`
> headings, `test/test_mode_parity.py` names).
>
> Counts: **7 critical, 13 major, 16 minor** (36 findings). Section files are cited as
> `SNN:line` = `.ultraplan/sections/section-NN-*.md` line. `index` = `sections/index.md`.

---

## A. Findings

### Critical

**1. Every gap section writes its CHANGELOG line under the top-level headings; S01 and S19 expect it to replace a `<!-- WP-28 <ID> -->` marker under `### Fixed in WP-28`. S19 19-01 fails on the first run.**
- Severity: critical.
- Where the contract is: S01:287-323 (TR-01.7: markers under `### Fixed in WP-28`, "A section replaces its gap's marker with its line(s)"; "Section 19 removes any marker left and fails if one is"), S19:196-200 (TR-19.1 "no `<!-- WP-28 ` marker surviving"), S19:343-347 (AC-19.1: every id in a `(WP-28)` line under `### Fixed in WP-28`), S19:403 (verify awk over that block).
- Where it is broken: S05:650-651 (`### Results that change` / `**Statistical layers and their rows**` (:16)); S06:494-495 (`### Results that change` / `**Colours, schemes and appearance**` (:113)); S07:392 (`### Changed behaviour …` and `### Fixed`, top level); S08:305 and S08:345 (`### Changed behaviour …`, top level); S09:806-813 (writes the F1 line directly under `### Fixed in WP-28`, does not replace `<!-- WP-28 F1 -->`; "create it … if no other section has yet" — S01 already creates it in the same batch, so two headings result), S09:911-915 (K2 line under `### Fixed in WP-28` at large; S01 puts K2 under the `Requirements:` sub-list); S10:914-921 (a new group `**The two pages (WP-28, E14)**` under top-level `### Results that change`; S01 has two E14 markers, one under `Results that change:` and one under `Fixed:`); S11:556-560 (`"Results that change"` and a `"Security"` list that does not exist in the stub); S12:762-766, S13:376, S15:322 (`"Results that change"` with no heading path); S14:707 (top-level `### Results that change`), S14:757 (`### Fixed` (or `### New`) for G16 — S01 and S19 AC-19.1 put G16 under `Results that change`); S16:374 (top-level, plus `### New` and `### Fixed`); S17:391 (`### Results that change` → `**Qualifiers, filters and KPIs**` (60), and `### Fixed`); S18:727 (top-level `### Results that change` and `### Fixed`); S04:809-816 (no gap, but writes `New`/`Changed behaviour`/`Results that change` at top level with no `(WP-28)` suffix).
- Proposed edit (one sentence, inserted into every final task named above, replacing the heading path it gives):
  > "In `CHANGELOG.md`, replace the marker(s) `<!-- WP-28 <ID> -->` under `### Fixed in WP-28` (S01 TR-01.7) with this gap's line(s), in the sub-list the marker sits in (`Results that change:` / `Changed behaviour (may need your do-files changed):` / `Requirements:` / `Fixed:`); each line ends `(WP-28)`; write nothing under the top-level `### Results that change`, `### Fixed`, `### Changed behaviour …`, `### New` or `### Security` headings. E14 replaces both of its markers. S04's shared-component lines go at the end of the `Fixed:` sub-list, ending `(WP-28 S04)`."
  And in S09:806-808 delete "(create it immediately before `### Fixed after WP-27` at 338 if no other section has yet; keep one heading after merge)" — only S01 creates the heading (merge rule R1 puts S01 first). In S11:558-560 replace `"Security" — the page's card rebuild escapes its text` with "append the escaping sentence to the E1 line under `Results that change:`". S19:201-232 is then correct as written.

**2. Twelve sections omit the `(WP-28, <ID>)` qualifier on the BUGS.md Resolution field that S01 fixes and S19 counts; the S19 closure guard fails for 20 of the 22 gaps.**
- Severity: critical.
- Contract: S01:332 (`- Resolution (WP-28, <ID>): Fixed <ddmonyyyy>. …`), S01:341-342 ("The Resolution qualifier `(WP-28, <ID>)` is what section 19 counts and what `_GAPS2_CLOSED`'s cross-check reads"), S01:469-471 (the test requires `"(%s, %s)" % (wp, gid)` in the Resolution), S19:196-198 (TR-19.1: the entry "whose Resolution starts `  - Resolution (WP-28, <ID>):`"), S19:358-360 (AC-19.7: `grep -c '^  - Resolution (WP-28, ' BUGS.md` prints 22).
- Broken: S05:645 (`Resolution "Fixed. Certified by …"`), S06:489 (same form), S07:357 and S07:393 ("Resolution naming …"), S08:305 and S08:345 ("Resolution naming …"), S09:820 (`Resolution "Fixed 25sep2026 (WP-28)."` — qualifier lacks the id), S09:932 (same), S10:927 (`Resolution "Fixed 2026 (WP-28)…"`), S11:550 ("Resolution: fixed, naming"), S12:749 and S12:754 ("Resolution naming"), S13:376 (form unspecified), S14:707 and S14:757 ("Resolution names"), S15:322 ("Resolution naming"), S17:392 ("once each" — form unspecified), S18:727 (unspecified). Only S16:375 is correct (`Resolution "Fixed <date> (WP-28, X2). …"`).
- Proposed edit, in each place: replace the Resolution phrase with
  > `- Resolution (WP-28, <ID>): Fixed <ddmonyyyy>. <what changed, in which functions, in both renderers>. Pinned by <tests as listed>[; fixture test/fixtures/<name>.json]. [Residual, deferred (WP-28): …]` — the S01 TR-01.8 form verbatim; the qualifier is `(WP-28, <ID>)`, never `(WP-28)` alone.
  For S09:820/932 and S10:927 the literal fix is `(WP-28)` → `(WP-28, F1)` / `(WP-28, K2)` / `(WP-28, E14)` and moving the qualifier into the field name position (`- Resolution (WP-28, F1): Fixed 25sep2026. …`).

**3. S13's B6 BUGS.md title contains double quotes, which the GAPS2 `Closed in …, BUGS.md "<title>"` form cannot carry.**
- Severity: critical (S19 19-01 "Require … no title holding `"`" fails; `_GAPS2_CLOSED = … BUGS\.md "([^"]+)"` cannot match).
- Where: S13:376 `B6 "xtitle("") and ytitle("") do not remove the axis title"`; contract S01:337 ("the title holds no `"`"), S01:526-527 (Notes), S19:198.
- Proposed edit, S13:376: title → `xtitle() and ytitle() given empty text do not remove the axis title`. (S13's B3 and B7 titles are clean; keep them.) Add to S13's Notes: "BUGS.md titles hold no `"` (S01 TR-01.8): spell empty text as `given empty text`, not `("")`."

**4. Commit granularity contradicts S01 TR-01.9 and S19 TR-19.1 in three ways: red test-only commits, several commits per gap, and squash-if-you-like.**
- Severity: critical (rule 4 "never commit a red tree"; BR-01.2 "full pytest suite stays green at every commit"; S19:196-198 "exactly one fix commit … per id" from `grep -F "(GAPS2 <ID>)"`).
- Contract: S01:343-354 (one commit per gap; regression tests "are written and run first, their failure text saved to the scratch directory, and they land in the fix commit that turns them green"; shared-component commits end `(WP-28 Snn)`), S01:452-453 (01-01: "Do not commit: a red tree is never committed").
- Broken — test-only tasks that commit a red tree: S02:368 (02-01 "Commit on `s3-bugs`"), S03:251 (03-01 "Commit on `s3-bugs`"), S04:642 (04-01 "Commit on `s3-bugs`"), S06:419-422 (06-01 "paste the failure summary into the commit message"), S13:286 (13-01 same), S15:252 (15-01 same), S16:292 (16-01 "Commit on `s3-bugs`"), S17:314 (17-01 "Commit on `s3-bugs`"); ambiguous: S05:509, S11:431-432, S12:571-572, S10:753 ("paste … into the commit message" with no fix in the task). Several commits per gap: S09:676-678 ("Each task is one commit … can be produced by squashing each group before merge if the maintainer prefers"), S10:1001 ("One commit per task on `s3-bugs`"), S05:670-671 ("recorded as failing at 91d97be in 05-01's and 05-02's commit messages"), S06:534-535 ("in 06-01's commit message").
- Proposed edit: (a) in each test-only task listed, replace the commit sentence with S01's: "Do not commit. Save the failure output to the scratch directory as `<task-id>-failure.txt`; it becomes the opening paragraph of the gap's fix commit (S01 TR-01.9)." (b) S09:676-678 → "F1 is one commit (09-03..09-06) and K2 one commit (09-07..09-12), subjects `… (GAPS2 F1)` / `… (GAPS2 K2)`; the 12 tasks are checkpoints inside those two commits, not commits." (c) S10:1001 → "One commit for E14 (10-01..10-08), subject `… (GAPS2 E14)`." (d) S05:670-671, S06:534-535 → "in the C2/D1 commit's message". (e) S02/S03/S04 (shared components) may commit per task only when the tree is green, with subjects ending `(WP-28 S02)` etc.; add that sentence to S02:13, S03:13, S04:32-34.

**5. S12 and S14 (same batch) each rewrite `_dash_hover_row` and `_dash_build_hover` with incompatible signatures and both edit the saved (22348) and served (26451) hover call sites; S14 also inserts a redraw hook into `_on_filter_change`, which S17 rewrites in the same batch. No merge order is stated for any of it, and S14 claims no batch-2 section edits `_dash_build_hover`.**
- Severity: critical (a hard `patch -p1` conflict on four hunks plus a signature mismatch that no test catches until the served app raises at draw time).
- Where: S12:350-356 (TR-12.4: `_dash_hover_row(col, label, fmt="", kind="", storage="", cache=None)` returning `((label, "@{col}{custom}"), ("@{col}", hover))`; `_dash_build_hover(…, formats=None, storage_types=None, fmt_cache=None)`; call sites 22348 and 26451), S14:374-382 (TR-14.10: `_dash_hover_row(col, label, date_kind="", numeric_fmt="", text_col=None)`; `_dash_build_hover(…, layers=None, value_labels=None, value_label_names=None)`; call sites 22348-22359 and 26451-26463), S14:69-71 ("**Can run with:** 11, 12, 13, 15, 16, 17 — none of them edits … `_dash_build_hover`"), S14:403-406 (TR-14.14: redraw hook in `_on_filter_change` step 3), S17:194 (TR-17.11 rewrites `_on_filter_change`; 17-06 at S17:368 "Keep every other line … as it is"). Current signature on disk: `dash_render.py:19795 def _dash_hover_row(col, label, date_kind="", numeric_fmt="")`.
- Proposed edit: one merged contract written into both sections:
  > `_dash_hover_row(col, label, fmt="", kind="", storage="", cache=None, text_col=None) -> tuple[tuple[str, str], tuple[str, CustomJSHover] | None]`: with `text_col` (S14, a value-labelled `hover()` variable) return `((label, f"@{{{text_col}}}"), None)` — no formatter; otherwise S12's rule. `_dash_build_hover(fig, xvar, y1var, y2var, hover_extra, var_labels, date_vars, numeric_formats, univar, layers=None, formats=None, storage_types=None, fmt_cache=None, value_labels=None, value_label_names=None)`; the value-label column pass (S14 TR-14.10) runs before `_fields_for`, then S12's formatter pass. Both call sites pass all six keywords.
  Merge order: S14 lands first (its edits are additive and S18 depends on it); S12's task 12-04 is executed on the merged tree, not in S12's worktree (rule R2 below). S17 lands before S14; S14's TR-14.14 hook is a three-line insertion applied after S17's `_on_filter_change` rewrite (rule R2). Replace S14:69-71 with: "S12 rewrites `_dash_hover_row`/`_dash_build_hover` for formats and S17 rewrites `_on_filter_change`; merge order S17 → S14 → S12 (rule R2); the merged hover signature is the one above." Alternatively (structural fix, recommended, see §C): move S12 to batch 3.

**6. S15 depends on S13's `scripts/extract_text_truth.do` and regenerates `test/fixtures/text_truth.json`, but its header and `index.md` say it depends on S02 only and place it in batch 2 beside S13; its fallback creates the same new file in a second worktree.**
- Severity: critical (a regenerated JSON fixture cannot be merged with `patch -p1`; two agents authoring `extract_text_truth.do` guarantees a conflict).
- Where: S15:3 ("Depends on: 02") vs S15:23 ("section 13's `scripts/extract_text_truth.do` skeleton (merge order below)"), S15:282 (15-04: "If section 13's script is not yet in this worktree, create the skeleton exactly as section 13's task 13-02 specifies"), S15:338 (Notes: "Merge 13, then apply 15's diff … regenerate, never hand-merged"), S13:25 ("merge 13 before 15 and regenerate the fixture once on the merged tree"), S13:399, index:33 and index:60 (`| 15 | … | 2 | 02 | 19 | 8 |`), index:93-104 (graph shows 15 hanging off 02 only).
- Proposed edit (pick one; B is recommended because it keeps batch 3 short and removes the shared file entirely):
  - A. S15:3 → `Depends on: 02, 13 · Batch: 3`; index:33 → move S15 to "### Batch 3" with S18, row 60 → `| 15 | … | 3 | 02, 13 | 19 | 8 |`; graph: `13 ──► 15`; delete S15:282's "If section 13's script is not yet …" sentence.
  - B. S15 writes its own `scripts/extract_legend_truth.do` → `test/fixtures/legend_truth.json` (same `zp` shape and record format as S13's, copied, with the `legend` group only); S15:11, S15:143 (TR-15.8), S15:155-194, S15:279-286 (15-04) rename accordingly; S15:23 and S15:338 drop the S13 dependency; S13:25, S13:175 ("section 15 adds group `legend` after these"), S13:296 (the marked empty region) and S13:399 drop the S15 clause; `test_legend_order.py`/`.cscript` name `legend_truth.json`. Batch placement stays.

**7. Six batch-1 sections and four batch-2 sections add a cscript with colliding runner block numbers and three different values for the hygiene count pins; two sections never register their cscript at all.**
- Severity: critical (`test_cscript_hygiene.py::TestEveryCscriptIsWiredIntoTheRunner` (:418) and the `len(_CSCRIPTS) == 65` / `len(names) == 47` pins at :292/:308 turn the full suite red at the first batch merge; `scripts/cert_verdict.py` counts registrations).
- Where: S02:233 and S02:386-389 (block #66; count 65→66); S05:303-305 and S05:622 ("block 66"; no count); S06:242 and S06:467 ("block 67"; no count); S07:304 ("block 67"; "bump … 65 to 66 and 47 to 48 … if another batch-1 section has not already"); S08:275 ("Bump … to 67 and … to 48"), S08:265 ("next block"); S09:720-722 (09-02: append, "numbered after the last script"; no count); S11:532-534 ("as the next number"; no count); S13:284-286 (13-01 creates `test/test_textbox_grammar.cscript` — **no registration task anywhere in S13**, no count); S14:697 (registers; count "if Section 02's #66 made it a count"); S15:250-252 (15-01 creates `test/test_legend_order.cscript` — **no registration task anywhere in S15**); S16:362 (registers after the test_help_claims_7 block; no count); S17:357-359 (registers; no count); S18:717 (registers; no count). S02:452 (Notes) and S07:418 say "the merge reconciles" without saying how.
- Proposed edit: (a) add to S13 a task 13-01b (files `test/run_all_cscripts.do`) "Register `test_textbox_grammar.cscript` as the next block" and to S15 the same for `test_legend_order.cscript`; (b) in every section that gives a block number (S02:233, S02:388, S05:622, S06:467, S07:304) replace the number with "the next block, numbered by the merger (rule R3)"; (c) replace every count edit (S02:389, S07:304, S08:275, S14:697) with "leave `test/test_cscript_hygiene.py:292,308` unchanged; the merger sets both pins once per batch (rule R3)"; (d) `index.md` §How to execute gains rule R3 verbatim. Expected totals after each batch, for the merger to check: batch 1 adds 7 scripts (S02, S05, S06, S07, S08 ×2, S09) → 72; batch 2 adds 6 (S11, S13, S14, S15, S16, S17) → 78; batch 3 adds 1 (S18) → 79; `len(names)` is read from the hygiene test's own assertion message on the merged tree (every new script but `test_string_varlists.cscript` and possibly S06's skips for Python).

### Major

**8. S05 imports `_NODE` and `_run_filter_js_block` from `test_statistical_helpers`, which S03 (same batch) deletes.**
- Severity: major (ImportError in `test/test_histogram_edge_rule.py` once S03 and S05 are both merged).
- Where: S05:497-498 (`from test_statistical_helpers import _hist, _run_filter_js_block, _NODE`), S05:506-507 (`@pytest.mark.skipif(_NODE is None, …)` "exactly as `TestFilterJavaScript` does"), S05:33-36 ("S03's stateful node runner … is optional here"); S03:162 (TR-03.2: "Delete `_NODE` and `_run_filter_js_block` (812-856 …); `from js_runner import run_filter_js_block as _run_filter_js_block, requires_node`; `@requires_node` on `TestFilterJavaScript` in place of the `skipif`"); on disk `test/test_statistical_helpers.py:817` `_NODE = _shutil.which("node")`, :820, :859. PLAN.md:138 says "S05 uses the existing single-block runner and does not wait for it" — true only if the names survive.
- Proposed edit: S03:162 → "… `from js_runner import run_filter_js_block as _run_filter_js_block, requires_node, NODE as _NODE` (the `_NODE` alias is kept because S05's `test_histogram_edge_rule.py` imports it in the same batch)"; S05:497-498 unchanged; S05:506-507 → "Node tests carry `@pytest.mark.skipif(_NODE is None, reason=\"node is not installed; set DASH_NODE\")` (after S03, `_NODE` is `js_runner.NODE` re-exported)". Merge rule R1: S03 before S05.

**9. S14 relies on `_DASH_VARNAME_RE`, which S07 (batch 1) deletes and replaces with `_dash_is_stata_name`.**
- Severity: major (an executor following S14 literally reintroduces a deleted constant, or the served copy list entry S07 removed).
- Where: S14:218 ("passes `_DASH_VARNAME_RE` (19207 …), which `__dash_hover_foreign` passes"), S14:380 ("`_fields_for` keeps its presence and `_DASH_VARNAME_RE` checks"), S14:822 ("`_DASH_VARNAME_RE` still gates the variable name"); S07:198 (TR-07.8: the five sites call `_dash_is_stata_name(...)`; `_DASH_VARNAME_RE` (19207) is deleted and removed from the served constants list), S07:412-413.
- Proposed edit: in the three S14 lines replace `_DASH_VARNAME_RE` with `_dash_is_stata_name` (S07 TR-07.8; `__dash_hover_foreign` is an identifier, so it passes), and S14:62 add "Section 07 (`__dash` prefix rule, `_dash_is_stata_name`)" to **Depends on**; index:59 → `| 14 | … | 2 | 02, 07 | 18 |`.

**10. S11 and S17 (same batch) both rewrite the KPI region of `_FILTER_JS` and the per-card config; S17's per-group call removes the brush-wiring slice marker `dash_apply_kpis(new_data,` that S11 and the renderer depend on.**
- Severity: major.
- Where: S11:239-249 (TR-11.4 rewrites `dash_apply_kpis`' branches, deletes 14378-14482, "keep the `// ---- KPI recompute, shared by` and `dash_apply_kpis(new_data,` markers the brush wiring (:23483-23485) slices on"), S11:232-238 (TR-11.3: config fields `fmt`, `storage`, drops `numfmt` …), S11:60-64 ("S17 edits the dropdown branches of the masks and `_dash_option_value`, which this section never touches"); S17:193 (TR-17.10: "KPIs are grouped by `JSON.stringify(k.use)` … `dash_apply_kpis(new_data_g, group, divs_g, ROW_ID)` runs per group"), S17:192 (TR-17.9: `kpi_config` holds a `"use"` list), S17:378 (17-07: "per-group KPI application replacing the single call at 14702"). On disk the marker is `dash_render.py:14650 dash_apply_kpis(new_data, kpi_config, kpi_divs, ROW_ID);` sliced at :23484-23485 by the literal `"dash_apply_kpis(new_data,"`; `test_kpi_values.py::_js_format` and `test_date_range.py:995-1012` also slice on text S11 changes.
- Proposed edit: S17:193 and S17:378 → "the per-group loop ends with the literal line `dash_apply_kpis(new_data, kpi_config, kpi_divs, ROW_ID);` replaced by `for (const [_g, _grp] of _kpi_groups) { dash_apply_kpis(new_data_of(_g), _grp.config, _grp.divs, ROW_ID); }` **written so that the text `dash_apply_kpis(new_data,` still occurs exactly once before it** (keep a comment line `// dash_apply_kpis(new_data, …) is applied per exclusion group below`) or update the slice at :23483-23485 to the new marker and say so — never leave the brush wiring slicing on text that no longer exists." Add to S11:60-64 and S17:34: "S11 (`dash_apply_kpis` body, `_kpi_callback_config` fields) and S17 (`kpi_config[…].use`, the per-group call, the aggregate block) edit the same region of `_FILTER_JS`; merge order S17 → S11 (rule R2); S11's task 11-03 runs on the merged tree."

**11. S12 and S14 both change `_dash_apply_axis_spec` (same batch, no order).**
- Severity: major.
- Where: S12:361-370 (TR-12.5: the `format()` branch at 16800-16810 sets `_dash_fmt_tick_formatter(fmt, "", "", cache)` and "the cache is passed in"), S14:340-351 (TR-14.5: new signature `_dash_apply_axis_spec(axis_obj, grid_obj, spec, values=None, fmt_fallback="", grid_color=None, value_labels=None)`, `_dash_extra_ticks`, value-label overrides); S18:339-342 (batch 3, `_dash_norescale`) is fine.
- Proposed edit: both TRs state one signature: `_dash_apply_axis_spec(axis_obj, grid_obj, spec, values=None, fmt_fallback="", grid_color=None, value_labels=None, fmt_cache=None)`; S14 lands first; S12's 12-05 edit is confined to the `format()` branch and runs on the merged tree (rule R2).

**12. `GlyphMapper._apply_colorvar` is edited by four batch-2 sections; S16 (which rewrites its middle) names only S17's one line; S12's anchors (6418, 6467) no longer exist after S16.**
- Severity: major.
- Where: S16:34 ("The only shared edit region is `_apply_colorvar`'s string path (S17, one line at 6527)"), S16:164; S12:393-395 (TR-12.9: "`_vlookup`'s fallback and the four cut-label expressions" at 6418/6467 → `_dash_fmt_text(v, self.numeric_formats.get(varname, "%9.0g"), …)`), S12:659-666 (12-06 "**after** section 16's diff has been merged if it is ready"); S14:352-357 (TR-14.6 replaces the labelset lookup at 6399-6405 with `_dash_value_labels_for`); S17:191 (TR-17.8, line 6527). After S16 (S16:144-146) the cut labels live in `_dash_colorvar_bins(col_vals, cuts, discrete, label_of)` (`f"{c:g}"`, `≤c1`, `c1–c2`, `>ck`).
- Proposed edit: S16:34 → "Shared edit regions inside `_apply_colorvar`: S17 (line 6527, string path), S14 (the `_vlookup` labelset lookup at 6399-6405 → `_dash_value_labels_for`), S12 (the number-to-text expressions, which after this section are `label_of`'s `f"{c:g}"` fallback and the three interval labels inside `_dash_colorvar_bins`). Merge order S17 → S16 → S14 → S12 (rule R2)." S12:393-395 → "the `f"{v:g}"` fallback of `_vlookup` and the interval labels inside `_dash_colorvar_bins` (S16 TR-16.3) use `_dash_fmt_text(v, self.formats.get(varname, "%9.0g"), self.storage_types.get(varname))`". S14:352-357: add "(S16 rewrites the neighbouring lines 6459-6498; this section's hunk is the six-line lookup only; merge after S16)".

**13. S12 and S14 both edit `_dash_csv_meta`, `_dash_facet_label` and the saved filter builder / `_build_filter_widgets`, which S17 also rewrites; no order is stated.**
- Severity: major.
- Where: S14:352-357 (TR-14.6: `_dash_csv_meta` 13909-13912, `_dash_facet_label` 15601-15607, saved filter builder 23598-23603 → `_dash_value_labels_for`); S12:388-392 (TR-12.8: `_dash_csv_meta(…, storage_types=None)`; callers 23855, 27090), S12:383-387 (TR-12.7: `_dash_facet_label(formats=None)`, `_dash_stata_date_text(value, fmt)`), S12:582-592 (12-02: `_build_filter_widgets` passes `self.formats`, `self.storage_types`, `self._fmt_models`); S17:192 (TR-17.9 rewrites `_build_filter_widgets` 23723-23826), S17:334 (17-03 adds `"numeric"` to `_filter_specs` 23707-23714); S12:337-349 (TR-12.3 adds `"unit"` to the same spec at 23707-23714).
- Proposed edit: add to S12:786-791 (Notes "Merge order in batch 2") and S14:69-71: "`_dash_csv_meta`, `_dash_facet_label`, `_build_filter_widgets` and the `filter_specs_json` dict are edited by S14 (one-line lookup replacements), S17 (values, `numeric`, the per-target `use` args) and S12 (formats, `unit`); merge order S17 → S14 → S12; S12's 12-02, 12-03, 12-06 and 12-07 run on the merged tree."

**14. S13 reads a `font_size` key from `svg_texts` entries; S02 defines the key as `size`.**
- Severity: major (the fixture's `font_sizes` map would be empty or the script would raise `KeyError`).
- Where: S13:175 (`"font_sizes" ({text: px} from each svg_texts entry's font_size; the entries carry the keys of extract_axis_truth.do's text inventory, section 02)`); S02:159 (TR-02.1: `svg_texts` → `text`, `raw`, `x`, `y`, `size` (px, from `font-size`), `anchor`, `fill`, `rotate`, `font_family`), S02:158 (`svg_document()["texts"]` is `parse_svg` lifted, i.e. keeps `font_size`).
- Proposed edit, S13:175: `"font_sizes" ({text: px} from each svg_texts entry's size — S02 TR-02.1 names the key size; svg_document()["texts"] keeps parse_svg's font_size)`. Same line: `"fills" (sorted(svg_fills(svg)) — the dict's keys, lower-cased)`, and `"added_fills"` is a set difference (the fills list carries no counts).

**15. S12 and S17 both rewrite the same dash.sthlp paragraph (`type(dropdown)`, 1109-1128).**
- Severity: major (a text conflict in the help; `test_help_claims_*` pins may then read half a sentence).
- Where: S12:757-758 (12-11: "Rewrite dash.sthlp: :1110-1128 (dropdown labels in the display format; period sliders …)"), S17:390 (17-08: "`dash.sthlp` 1109-1116 (`type(dropdown)`): 'select widget listing every distinct value …'").
- Proposed edit: S17 owns the paragraph and writes both facts in one rewrite: append to S17:390's text "…; a listed value is written in the variable's display format, or its value label, and a `%tw`/`%tm`/`%tq`/`%th`/`%ty` variable's range slider moves over Stata's period numbers in steps of one (S12)"; S12:757-758 → ":1109-1128 is rewritten by S17 (17-08) with this section's sentence included; verify the wording after the merge, do not rewrite it".

**16. The shared registries and test-corpus files are edited by most sections of a batch with no reconciliation rule; `patch -p1` will reject hunks that insert "beside" the same anchor.**
- Severity: major (process). The files: `dash_render.py` served copy lists (constants 24326-24428, functions 24466-24687), `test/function_test_map.py`, `test/program_coverage_map.py`, `test/test_mode_parity.py` (`CORPUS`, `ALLOWED`, `_MUST_WARN`, `_VALUE_LABELS`/`_LABEL_NAMES`, profile functions), `test/test_suboption_warnings.py` (`SUBOPTIONS`, `TestTheHonouredOnesStayQuiet`), `test/test_axis_options.py`, `test/test_graph_options.py`, `test/test_help_claims_4.py`, `test/test_date_range.py`, `test/test_saved_filter_layers.py`, `test/test_export.py`, `test/test_label_sinks.py`, `test/test_server_layer_defects.py`, `dash.sthlp`, `BUGS.md`, `CHANGELOG.md`. Only S01:528-531 (BUGS/CHANGELOG), S02:452 (hygiene count), S09:987-990 (copy tuple: "section 04 adds its writer functions to the same tuple and `patch -p1` merges cleanly only when the two insertions do not overlap"), S12:786-791 and S17:412 (S17→S12) say anything. Full table in §B; rules R1-R6 in §C. Proposed edit: paste rules R1-R6 into `index.md` §How to execute and cite them from each section's Notes.

**17. S12 hands the `%tm` axis-label truth probe (E3 plan step 4) to S14 "in the commit message of 12-05"; S14 runs in the same batch and lists no such probe, so the E3 closure has no twoway-drawn truth for it.**
- Severity: major (a GAPS2 plan step lands nowhere).
- Where: S12:436-438, S12:798-802; S14:458-497 (probe tables: no `%tm` axis probe); S18:493 adds `sp500` data facts (batch 3).
- Proposed edit, S14 "Stata truth" `b1_label` table: add `| a1_tm_axis | sp500: gen m = mofd(date); format m %tm; twoway line close m | — | the x tick texts (\`2001m1\` …) |` (dataset `sp500` handled in the loop like `auto_vl`), and in S14 TDD stubs `TestAgainstTwoway` include it; S12 stub `TestDateAxis::test_ticks_read_as_stata_in_both_modes` gains "and the `%tm` tick texts of `axis_truth.json` probe `a1_tm_axis` are each produced by dash's formatter at that probe's tick values" (fails on the missing probe until S14 lands — S12 then depends on S14, see §C). Delete S12:437-438 and S12:801-802 ("hand it over in the commit message").

**18. S17 requires S12 to keep dropdown labels unique per widget; S12 has no such rule or test.**
- Severity: major (functional: with numeric option values BokehJS resolves a label to the first value that carries it — S17:26, S17:201, S17:412).
- Where: S12:330-336 (TR-12.2: `_label(rv)` → `_dash_fmt_text(float(rv), fmt or "%9.0g", storage)`), S12:451-455 (TestDropdown stubs).
- Proposed edit, S12 TR-12.2: append "Labels must be unique per widget: after formatting, any label carried by two or more values is suffixed with ` (` + `_dash_option_value`'s text + `)` for each of them (BokehJS maps a label back to the first value with that label; S17 TR-17.4). Test `TestDropdown::test_two_values_with_one_formatted_label_stay_distinct` (`%9.0f` on 1.2 and 1.4: labels `1 (1.2)`, `1 (1.4)`; selecting each keeps its own row in both modes)." Also S12:330-336 note: "`rv` is a float for a numeric column and exact text otherwise (S17 TR-17.2), never a string to parse."

**19. S06 defers its optional SVG comparison to S19; S19's Boundaries refuse gap work.**
- Severity: major (a dangling hand-off; S19:278-282 "Do not fix a gap here").
- Where: S06:264-265, S06:516-518 (06-05 "deferred to S19"), S06:529.
- Proposed edit: S06:517-518 → "record 'D1 SVG comparison not performed: test/cert_svg.do absent in this worktree' in the D1 BUGS.md entry's Resolution as an optional check, and list it in `index.md` as a batch-2 follow-up task 06-05b (files `test/test_custom_scheme_quoted.cscript`) to run on the merged tree"; S06:529 likewise. index §Batch 2 gains "06-05b (S06 CQ-04, after S02)".

**20. `index.md`/`PLAN.md` dependency graph omits five real edges; three of them cross within a batch.**
- Severity: major (the graph is what decides the batches).
- Where: index:93-104, PLAN.md:120-140. Missing: S05←S03 (finding 8), S14←S07 (finding 9), S15←S13 (finding 6), S12←S14/S16/S17 (findings 5, 11-13, 17; S12:47-54 and S12:60-63 state S16/S17 themselves), S11←S17 (finding 10).
- Proposed edit: see §C (rebatch) and the corrected graph there.

### Minor

**21. S03's public names are consumed loosely by S12 and S05.** S12:60 ("the stateful node runner, for the period-slider mask parity test"), S12:446 ("section 03's stateful runner"), S12:464-467, S12:563 ("the stateful runner from section 03's module") — the tool for "pandas mask equals the node mask" is `js_runner.mask_parity(df, filter_specs, widget_values)` (S03:147-153), and the one-move card/graph case is `js_runner.JsSession`. Proposed: name `from js_runner import JsSession, mask_parity` at S12:563 and use `mask_parity` in the stub at S12:464-467. S17:13 gets it right.

**22. S17 names `__mlabel__*` columns that S07 (batch 1) renames.** S17:86, S17:190 (TR-17.7 "`__mlabel__*` columns keep their text after a move"). Proposed: `__dash_mlabel_*` (S07 TR-07.2 `_DASH_MLABEL_PREFIX`).

**23. S14 writes `MUST_WARN`; the object is `_MUST_WARN` (`test/test_mode_parity.py:1440`).** S14:246, S14:248, S14:594; S12:253 and S12:713 are correct. Proposed: `_MUST_WARN`.

**24. S12 mixes `self.numeric_formats` and the full map it introduces.** S12:393-395 (TR-12.9 `self.numeric_formats.get(varname, "%9.0g")`) vs S12:371-382 (TR-12.6 adds `mapper.formats`, the full map). Proposed: `self.formats.get(varname, "%9.0g")` in TR-12.9 (covered by finding 12's replacement text).

**25. S12 exposes `_dash_fmt_tick_code(fmt, kind, storage)` "so section 14 can compose it"; no section consumes it and it is not in S12's copy-list/test-map lists.** S12:803-807 vs S12:396-403 (TR-12.10). Proposed: delete S12:803-807, or add `_dash_fmt_tick_code` to TR-12.1, TR-12.10 and `function_test_map.py` and name the consumer (none in WP-28 → delete).

**26. Stale forward references to who re-runs `extract_axis_truth.do` and how many scripts the cert suite has.** S02:254 ("section 18 extends and re-runs that script and is the point at which switching it to the module is safe" — S14 re-runs it first, S14:499-502); S02:356 (AC-02.2 "66 of 66" — 72 after the batch-1 merge); S19:82-83 and S19:478-479 ("65 scripts" — 79 at closeout). Proposed: S02:254 → "section 14 (then 18) extends and re-runs that script; the private reader stays until then"; S02:356 → "reports every registered script passed (66 when run alone; the batch total after the merge)"; S19:82-83, S19:479 → "every registered script (65 at 91d97be plus the 14 WP-28 adds)".

**27. PLAN.md file map is stale.** PLAN.md:481 lists `extract_stat_truth.do (extended) … 05/17`; S17 writes `scripts/extract_filter_truth.do` → `test/fixtures/filter_truth.json` (S17:195, S17:212-233) and S08 adds `scripts/gen_string_varlists_cscript.py` (S08:153); neither is in the map. Proposed: PLAN.md:481 → `… extract_stat_truth.do (extended), extract_filter_truth.do, extract_svg_truth_smoke.do; scripts/gen_string_varlists_cscript.py | 04, 13/15, 16, 14/18, 05, 17, 02; 08`.

**28. Fixture metadata key drift.** S13:296 writes `{"meta": {...}, "probes": {...}}`; S02:212, S04:482, S16:212, S17:225 and the existing fixtures use `_meta`. Proposed: S13:227 and S13:296 → `_meta`; S15 reads `['probes']` only, unaffected.

**29. S05 inserts its BUGS.md entry mid-file.** S05:636-637 ("add, after the entry at :1215 …") vs S01:335 ("appended at the end of BUGS.md with one blank line before it") and S01:528-531 (parallel merges append in section order). Proposed: S05:636-637 → "append at the end of BUGS.md (S01 TR-01.8) a closed entry … whose Description cites the entry at :1215 by title".

**30. Sections describe commit bodies without S01's `Regression:` / `Flipped:` / `Fixture:` / `BUGS.md:` line forms that S19 reads.** S19:245-246 (TR-19.4 "the tests flipped (from the commit bodies' `Flipped:` lines)"), S01:346-350; the sections say "record each old/new text in the commit message" (S07:358, S09:773, S11:491, S12:701, S14:707, S18:697 …). Proposed: one sentence in each section's Notes: "Commit bodies use S01 TR-01.9's line forms verbatim: `Regression: …`, `Flipped: <node> -- <old> was wrong because <why>` (one per flip), `Fixture: …`, `BUGS.md: "<title>" (closed)`."

**31. S09's K2 CHANGELOG placement and S04's shared-component lines** — folded into finding 1 (S09:911-915 → the `Requirements:` sub-list marker; S04:809-816 → `Fixed:` sub-list, suffix `(WP-28 S04)`).

**32. S14's cscript loads `cert_svg.do`, which skips for Python (`exit 222`), so it must also be counted in `len(names)`; S14:697 says only "bump the count … if Section 02's #66 made it a count".** Folded into finding 7's rule R3 (both pins set by the merger). Same for S13, S15, S16, S18 (all load `cert_svg.do`) and S11, S17 (own `c(python_exec)` guard).

**33. S16 uses S13's textbox reader without saying so.** S16:150 (`_dash_textbox(raw, "ztitle", seen, key)`; `ztitle("Repair", orientation(vertical))` must name the sub-option, S16:237) works before and after S13's canonicalisation (S13:152, TR-13.4), but S16:34 should list S13 among the sections whose diff changes a function S16 calls (`_dash_textbox`, `_DASH_TEXTBOX_HONOURED`) and merge after it (rule R2: S13 → S16).

**34. S13/S15 `zp` sixth argument is `control`; S15 registers every `<id>__off` companion "as its own probe with an empty control"** (S15:157, S15:183) — consistent with S13:173; but S15:184 orders `keys_in_drawn_order` by each `svg_texts` entry's `y` then `x` while S13:296 records `texts` in document order only. No conflict; note for the executor that the python block must keep the per-entry dicts (not just the `text` field) to sort. Proposed: S13:296 "calls `svg_texts` … and keeps the entry dicts for group `legend` (S15 sorts by `y`, `x`)". (Moot under finding 6 option B.)

**35. S18:3 "Depends on: 02, 14" is right, but S18 also reads S02's `cert_graph_scale` seven-value `r()` set and S14's `zp … ticks hull` signature (S14:442-444, S18:432-433): consistent.** No edit; recorded as verified. Likewise verified with no mismatch: S11/S12 ↔ S04 (`_dash_fmt`, `_dash_fmt_text`, `_dash_fmt_kind`, `_dash_fmt_refusal`, `_dash_stata_value_of`, `_DASH_FMT_JS` with `dash_fmt`, `dash_fmt_text`, `dash_stata_value_of`, `dash_float32_text`, `dash_html_escape`, export key `storageTypes`, served `_FORMATS`/`_storage_types`); S17 ↔ S03 (`JsSession.set/.run/.run_code/.state/.rows/.ids`, `mask_parity`); S14/S16/S18 ↔ S02 (`svg_texts`→`text`/`x`/`y`, `svg_axis_extent`→`low`/`high`/`space`/`reversed`, `svg_document`→`circles`/`paths` with lower-cased `fill`, `svg_marker_fills` per-colour dict — S16:183 and S16:395 use it correctly, not as per-marker fills; `cert_svg_export`→`r(rc)`/`r(file)`, `cert_svg_texts`→`r(n)`/`r(list)`/`r(maxsize)`, `cert_svg_has_text`→`r(found)`/`r(count)`, `cert_svg_fills`→`r(n)`/`r(colours)`/`r(list)`, `cert_svg_extent`→`r(low)`/`r(high)`/`r(reason)`, `cert_graph_scale`→`r(min) r(max) r(curmin) r(curmax) r(major_min) r(major_max) r(major_delta)`); S14 ↔ S07 (`__dash_hover_{var}`; S07:26, S14:369); S14 ↔ S18 (`_dash_expand_numlist`, `FixedTicker.ticks`, `ax._dash_extra_ticks`, CustomJSTicker `extra`, the honoured tuple gaining `valuelabel` then `norescale`); S10's dimming function `_dash_dim_nonselection(fig, alpha=_NONSELECTION_ALPHA)` (S10:431-439, :572, :812-820, :924) is one name throughout; S18's `_dash_hull_ranges` and `_dash_limit_ranges_to_primary` are one name throughout and "hull step" is used the same way in S14:67 and S18:23; S11 removes the guard S04 adds with the exact test name S04 gives (S04:564-566, S11:176-177, S11:488-490); S15's `lastlabel` index rule is deferred to the fixture consistently (S15:138, :339); `index.md` task counts (159) match the section files (3,7,5,9,6,5,10,10,12,8,7,11,10,12,8,8,8,12,8).

**36. S01's WP-28 field names are used consistently** (`**GAPS2 closed:**`, `#### GAPS2 traceability`, `_GAPS2_CLOSED`, `_GAPS2_DEFERRED`, `Closed in WP-28, BUGS.md "<title>", commit <hash>`, `Deferred (WP-28): …`) across S01:223-256, S19:120-126, S19:233-239, S19:348-350. One drift: S19:236 keeps the old text after `; was: <old>` and S01:234 says "Text after the first `;` is commentary … and is not read" — consistent. No edit.

---

## B. Shared-file table (sections in the same batch that modify one file)

"Order" = the merge order the plan states; **NONE** = no rule anywhere. R-n refers to §C.

| File / region | Batch 1 sections | Batch 2 sections | Batch 3/4 | Stated order | Rule needed |
|---|---|---|---|---|---|
| `test/run_all_cscripts.do` (registration blocks) | S02 (#66), S05 (66), S06 (67), S07 (67), S08 (×2, "next"), S09 ("after last") | S11, S14, S16, S17 (S13, S15 missing) | S18 | NONE (numbers collide) | R3 |
| `test/test_cscript_hygiene.py:292,308` (65 / 47 pins) | S02 (66), S07 (66/48), S08 (67/48); S05, S06, S09 silent | S14 (hedged); S11, S13, S15, S16, S17 silent | S18 silent | "the merge reconciles" (S02:452, S07:418) — no number | R3 |
| `test/function_test_map.py` | S04, S05, S06, S08, S09, S10 | S11, S12, S13, S14, S15, S16, S17 | S18 | NONE | R3 |
| `test/program_coverage_map.py` | S07, S08, S09 | S11, S13, S14, S15 | — | NONE | R3 |
| `dash_render.py` served constants list 24326-24428 | S04 (`_DASH_FMT_JS`+4 tables beside `_DASH_CSV_SERVED_JS`), S07 (beside `_ROW_ID_COLUMN`/`_DASH_QUAL_PREFIX`; deletes `_DASH_VARNAME_RE` :24372), S10 (beside `_DASH_CSP_SERVED` :24381; :24425-24428) | S13 (`_TEXTBOX_SUBOPTS`) | — | NONE | R3 |
| `dash_render.py` served functions list 24466-24687 | S04 (unspecified place), S07 (beside `_dash_parse_filter_raw`), S09 (END of tuple), S10 (beside `_dash_refresh_linked` :24641, `_dash_bs_grid` :24652) | S12, S13, S14, S15, S16, S17 (each "beside" a different neighbour) | S18 (7 names) | S09:987-990 only ("do not overlap") | R3 |
| `dash_render.py` `_DASH_FILTER_MASK_JS` / `_FILTER_JS` | S04 (prepend `_DASH_FMT_JS`), S05 (14800-14826), S07 (14219) | S11 (`dash_apply_kpis` 14484-14648, deletes 14378-14482), S12 (slider/range branches 14141-14160), S17 (dropdown branch, `use`, whole consumer chain 14186-14915) | — | S17→S12 (S12:62-63, S17:412); S11↔S17 NONE | R2 (S17→S11, S17→S12) |
| `dash_render.py` `_dash_hover_row`, `_dash_build_hover`, call sites 22348 / 26451 | — | S12, S14 | — | NONE | R2 (S14→S12), finding 5 |
| `dash_render.py` `_dash_apply_axis_spec` | — | S12, S14 | S18 | NONE | R2 (S14→S12) |
| `dash_render.py` `GlyphMapper._apply_colorvar` | S07 (6365) | S12, S14, S16, S17 | — | S16↔S17 disjoint (S16:164); S16→S12 (S12:659) | R2 (S17→S16→S14→S12) |
| `dash_render.py` `_dash_csv_meta`, `_dash_facet_label`, `_dash_stata_date_text` | — | S12, S14 | — | NONE | R2 (S14→S12) |
| `dash_render.py` `_dash_filter_widget`, `_build_filter_widgets`, `filter_specs_json` 23707-23714, `_dash_frame_filter_mask` | — | S12, S14 (23598-23603), S17 | — | S17→S12 (both); S14 NONE | R2 (S17→S14→S12) |
| `dash_render.py` `_kpi_callback_config`, `kpi_config` | — | S11, S17 | — | NONE | R2 (S17→S11), finding 10 |
| `dash_render.py` served template `make_document` (`_on_filter_change` 26758-26964; hover 26451; widgets 26703; z options 26120/26393; `_format_kpi` 25789; axes 26198; `_dash_add_secondary_axes` 26207; imports 25236-25262; `_fmt_cache`) | S04 (25860-25877), S07 (25002), S08 (24981), S09 (25198-25222, 25614, 27371), S10 (26012-26024, 26479, 27175-27180) | S11, S12, S13, S14, S16, S17 | S18 (26402) | NONE (batch 1 disjoint; batch 2: `_on_filter_change` S14/S17 and hover S12/S14 overlap) | R2 |
| `dash_render.py` saved `_make_figure_body` / `_build_sources_and_figures` / `_load_data` | S04 (21160-21187), S10 (23309, 23332, 22712-22731) | S12 (22029-22034, 22348), S13 (21030, 22096), S14 (22115, 22307, 22348-22359), S16 (21950, 22303) | S18 (22314-22330) | NONE | R2 |
| `dash_render.py` `_dash_attach_labels` (18745) neighbourhood | S04 (`storage_types=`) | S12 (`formats=`), S14 (new function immediately before it) | — | NONE | R2 |
| `dash.ado` | S04 (2294-2313), S07 (4255-4261, 6094-6100), S08 (1273-1358, 2735-2754, 5920, 6682-6820, 6875), S09 (205-207, 7349-7439) | S13 (3783, 4498), S14 (1853-1929 `_dash_option_rules`, `_dash_validate_value`, new program), S16 (699-724, 899-958, 801-856, 1206-1262, 1684, 1867, 2856-2860, the seven `foreach` lists 3951…4942) | — | NONE (regions disjoint; S14:1910-1912 and S16:1867 are the same program) | R2 note: the seven graph-key lists are S16's alone — verified, no other section names them |
| `dash_parse.mata` | S07 (beside 827), S08 (after 5083) | S13 (after 4727), S14 (beside 4064), S15 (4751-4766), S16 (4242-4258, 4271-4292, 4362) | — | NONE (S13's insertion sits between S15's and S16's targets) | R3 (rebuild the mlib once per batch) |
| `scripts/extract_text_truth.do` + `test/fixtures/text_truth.json` | — | S13 (creates), S15 (extends + regenerates) | — | S13→S15 stated in both, but batch and index say parallel | finding 6, R5 |
| `scripts/extract_axis_truth.do` + `test/fixtures/axis_truth.json` | S02 (pins only, no edit) | S14 (`zp` +2 args, groups `b1_label`, `g16_valuelabel`) | S18 (group `b2_extent`, `cert_graph_scale`) | S14→S18 (batches) | R5 (one regeneration per batch) |
| `scripts/extract_stat_truth.do` + `test/fixtures/stat_truth.json` | S05 only | — | — | n/a | R5 |
| `test/test_fixtures_are_committed.py` | nobody edits it; every section relies on "named by a test" + `git add -f` | | | n/a | none |
| `test/test_mode_parity.py` | S10 (`_glyph_profile`, `_bs_markup_page`, `_render_pair`, `ALLOWED` text, +2 CORPUS, +3 classes) | S12 (`_MUST_WARN` mlabformat, CORPUS re-profile), S13 (+3 CORPUS), S14 (`_MUST_WARN` case 1168-1169, `_VALUE_LABELS`/`_LABEL_NAMES`, +1 CORPUS, +1 class), S15 (+4 CORPUS), S16 (+7 CORPUS) | S18 (`_axes.rng`) | NONE | R3 |
| `test/test_suboption_warnings.py` | — | S13, S14, S15 | — | NONE | R3 |
| `test/test_axis_options.py` | — | S12 (176-190), S13 (`TestTitleTextFidelity`), S14 (maybe `test_increment_form_with_spaces`), S15 (`TestLegendOptions`) | S18 (`TestAxisScale`) | NONE | R3 |
| `test/test_graph_options.py` | — | S14 (436-441), S15 (452-600) | S18 | NONE | R3 |
| `test/test_help_claims_3.py` | S03 (321-348), S10 (735-739) | S17 (415-497, 404-408) | — | NONE | R1 (S03→S10) |
| `test/test_help_claims_4.py` | S10 (1643, 1671-1685) | S11 (780-810), S12 (1706), S17 (220, maybe) | — | NONE | R3 |
| `test/test_date_range.py` | S07 (805-807) | S11 (542-545, 995-1012), S12 (476-478, 582, 609, 652, 790-860, 944-961) | — | NONE | R3 |
| `test/test_saved_filter_layers.py` | S03 (deletes 85-214), S07 (475-478, 999-1035) | S12 (1212-1216), S17 (1219-1245) | — | S17:149 names S12's line but no order | R1 (S03→S07), R2 (S17→S12) |
| `test/test_statistical_helpers.py` | S03 (deletes 812-856), S05 (imports `_NODE`) | — | — | NONE | finding 8, R1 (S03→S05) |
| `test/test_export.py` | — | S12 (166-171, 548), S17 (199-201, 596-614) | — | NONE | R3 |
| `test/test_label_sinks.py` | — | S12 (855-857, new test), S16 (Sink rows beside 584/590) | — | NONE | R3 |
| `test/test_server_layer_defects.py` | — | S11 (1100-1106), S12 (`TestTheHoverBuilder` 1187-1200, "only if") | — | NONE | R3 |
| `test/test_help_claims_8.cscript` | S02 (83, 229-241, 354-366, 456-458), S09 (786) | — | — | NONE (disjoint) | R1 |
| `test/test_help_claims_2.py` | S09 only | — | — | n/a | — |
| `dash.sthlp` | S04 (1259-1261), S05 (2040-2052), S06 (2804-2814), S07 (166-171, 1108-1109, 1194-1197), S08 (181-193, 1519-1522, 1560-1572), S09 (727-729, 1353-1357, 1367-1374, 3131-3134), S10 (955-959, 1010-1020, 1321, 1345-1351, 1484-1496) | S11 (1242-1261), S12 (862-866, **1110-1128**, 1783-1784, 2361, 2441-2461), S13 (455-458, 519-525, 2396-2417), S14 (672-680, 2318-2331), S15 (2290-2312), S16 (2478-2507, graph-option table), S17 (**1109-1116, 1128-1138**) | S18 (2333-2335, 2431-2432) | NONE | R4 (S12/S17 overlap: finding 15) |
| `BUGS.md` | S05 (mid-file!), S06, S07, S08, S09, S10 | S11, S12, S13, S14, S15, S16, S17 | S18 | S01:528-531 (append in section order) | R4 |
| `CHANGELOG.md` | S01 (stub + markers), S04, S05, S06, S07, S08, S09, S10 | S11-S17 | S18, S19 | S01:320-323, 528-531 (replace markers) — not followed | R4, finding 1 |
| `test/js_runner.py` | S03 only | consumed by S12, S17 | — | S17:203 "S03 owns" | — |

Files the brief asked about that turned out to be single-owner: `scripts/extract_stat_truth.do` (S05), `test/test_fixtures_are_committed.py` (nobody), the seven `dash.ado` graph-key `foreach` lists (S16 alone; S14's edit is to `_dash_option_rules`, a different program).

---

## C. Proposed merge-order rules and batch placement

### Dependency graph (declared vs actual)

Declared (index:44-64, PLAN.md:94-114): 11←04; 12←03,04; 13←02; 14←02; 15←02; 16←02; 17←03; 18←02,14; 19←all. **Actual, from the task contents:**

```
Batch 1: 01  02  03  04  05  06  07  08  09  10
         |    |   |\   |            |
         |    |   | \  |            |
         |    |   |  05 (imports S03's names: finding 8; same batch)
         |    |   |
Batch 2: |    |   +──► 17 ──► 11 (KPI region of _FILTER_JS: finding 10; same batch)
         |    |   |     \
         |    |   +──────┼──► 12 ◄── 04   (12 also ← 14, 16, 17: findings 5, 11-13, 17)
         |    +───► 13 ──┼──► 15          (extract_text_truth.do: finding 6; same batch)
         |    +───► 14 ◄─┼── 07           (prefix, _dash_is_stata_name: finding 9)
         |    +───► 16   |
Batch 3: |          18 ◄─┴── 14, 02
Batch 4: 19 ◄── all
```

The graph is a DAG (no cycle: every edge points from a lower-numbered section to a higher one, except none). The batches are **not** consistent with it: four edges are intra-batch (05←03, 15←13, 12←14/16/17, 11←17).

### Proposed placement (structural fix; recommended)

- **Batch 1** unchanged in membership; merge order **S01, S03, S02, S04, S09, S07, S05, S06, S08, S10** (S01 first so the CHANGELOG stub and conventions exist; S03 before S05/S07/S10 for `test_statistical_helpers.py`, `test_saved_filter_layers.py`, `test_help_claims_3.py`; S02 before every cscript-adding section for block numbering; S04 before S09 for the function tuple).
- **Batch 2**: S13, S14, S16, S17 (and S15 if finding 6 option B is taken; otherwise S15 moves to batch 3). Merge order **S13, S17, S16, S14, S15**.
- **Batch 3**: S11, S12, S18 (S15 too under option A). S11 and S12 are disjoint from each other; S18 and S12 share `_dash_apply_axis_spec` in disjoint hunks — merge **S18, S11, S12**.
- **Batch 4**: S19.
- `index.md` edits: lines 27-38 (batch lists), 56-63 (rows: `| 11 | … | 3 | 04, 17 |`, `| 12 | … | 3 | 03, 04, 14, 16, 17 |`, `| 14 | … | 2 | 02, 07 |`, `| 15 | … | 2 or 3 | 02[, 13] |`), 93-104 (graph as above); PLAN.md:120-140 likewise; S12:3, S11:3, S14:3, S15:3 headers.

### Minimal alternative (keep the batches, add rules)

If the batches are kept, every overlapping task must be executed **after** the earlier section's diff is merged, on the merged tree, not in the worktree: S05 05-01 (after S03), S11 11-03 (after S17), S12 12-02/12-03/12-04/12-05/12-06/12-07 (after S17, S16, S14), S14 14-07/14-09 (after S16, S17), S15 15-04 (after S13). That is what R2 says; it costs the same wall-clock as the rebatch and is harder to police.

### Rules to add to `index.md` §How to execute (and cite from every section's Notes)

- **R1 — batch-1 merge order** `S01, S03, S02, S04, S09, S07, S05, S06, S08, S10`; reasons as above.
- **R2 — function ownership inside a batch.** A function two sections of one batch name is owned by the earlier section in the batch's merge order (batch 2: `S13, S17, S16, S14, S15`; batch 3: `S18, S11, S12`); the later section's task that edits it is run on the merged tree after the owner's diff has landed, with the merged signature written in both section files (findings 5, 10-13). Named pairs: `_dash_hover_row`/`_dash_build_hover` (S14→S12), `_dash_apply_axis_spec` (S14→S12; S18→S12), `_apply_colorvar` (S17→S16→S14→S12), `_dash_csv_meta`/`_dash_facet_label`/`_build_filter_widgets`/`filter_specs_json`/`_dash_filter_widget`/the masks (S17→S14→S12), `_FILTER_JS` KPI region and `kpi_config` (S17→S11), `_on_filter_change` (S17→S14), `_dash_textbox` consumers (S13→S16), `dash_parse.mata` insertions (S13, S15, S16: apply rejected hunks by hand, rebuild the `.mlib` once per batch).
- **R3 — registries are merged by hand, order-free, counted once.** For `test/run_all_cscripts.do`, `test/test_cscript_hygiene.py:292,308`, `test/function_test_map.py`, `test/program_coverage_map.py`, the two served copy tuples, `test_mode_parity.py` (`CORPUS`, `ALLOWED`, `_MUST_WARN`, `_VALUE_LABELS`, `_LABEL_NAMES`), `test_suboption_warnings.py` rows, and the other test files in §B: a rejected hunk is applied by hand keeping every entry; block numbers are assigned in merge order by the merger; the two hygiene pins are set once per batch to the numbers the hygiene test reports on the merged tree (72/78/79 scripts expected); after each batch run `test_cscript_hygiene.py`, `test_function_test_map.py`, `test_program_coverage_map.py`, `test_statistical_helpers.py::TestTheServedAppCarriesEveryName`, `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads`, `test_no_orphans.py` and `test_mode_parity.py` before the full suite. Sections never edit the two pins.
- **R4 — documents.** BUGS.md entries are appended at the end in merge order (never mid-file). CHANGELOG lines only replace `<!-- WP-28 <ID> -->` markers under `### Fixed in WP-28`; only S01 creates that heading. dash.sthlp paragraphs have one owner each (§B); where two sections list one paragraph (1109-1128: S17 writes both facts; 1259-1261: S04 then S11), the later merger checks the merged text.
- **R5 — fixtures.** A JSON fixture that two sections regenerate (`axis_truth.json`, `text_truth.json`, `stat_truth.json`) is never patched: the merger re-runs the extract script once on the merged tree from a scratch directory with `STATATMP=<dir>/tmp/`, reviews the diff for additions only, and `git add -f`s the result; `.svg`/`.scheme`/`.csv` fixtures are added once by their section.
- **R6 — commits.** Test-only tasks never commit; one commit per gap with the subject `… (GAPS2 <ID>)`; shared-component sections (S02, S03, S04) commit per task only on green trees with `… (WP-28 Snn)`; S09 and S10 are two and one commits respectively; every fix commit carries its closed BUGS.md entry with `- Resolution (WP-28, <ID>): …` and replaces its CHANGELOG marker(s).

---

## D. Naming-drift register (one line each; details in §A)

| Concept | Spellings found | Canonical |
|---|---|---|
| text entry font size | `size` (S02:159), `font_size` (S13:175) | `size` from `svg_texts`; `font_size` only inside `svg_document()["texts"]` |
| parity must-warn table | `_MUST_WARN` (S12, tree), `MUST_WARN` (S14:246,248,594) | `_MUST_WARN` |
| marker-label columns | `__dash_mlabel_*` (S07, S14), `__mlabel__*` (S17:86,190) | `__dash_mlabel_*` after S07 |
| name check | `_dash_is_stata_name` (S07), `_DASH_VARNAME_RE` (S14:218,380,822) | `_dash_is_stata_name` |
| fixture metadata key | `_meta` (S02, S04, S16, S17, tree), `meta` (S13:227,296) | `_meta` |
| hover row signature | S12:350 vs S14:378 | merged form in finding 5 |
| CHANGELOG location | top-level headings (S04-S18) vs `### Fixed in WP-28` markers (S01, S19) | markers |
| Resolution qualifier | `(WP-28)` (S09, S10), none (10 sections), `(WP-28, X2)` (S16) | `(WP-28, <ID>)` |
| "hull step" | S14:67, S18:23 | consistent |
| dimming function | `_dash_dim_nonselection` (S10 throughout) | consistent |
| dropdown `rv` type | string (S12:330-336) vs float/text (S17:185) | S17's |
| S03 runner in S12 | "section 03's runner/module" (S12:60,446,563) | `js_runner.JsSession`, `js_runner.mask_parity` |
| cert-suite size | 65 (S19), 66 (S02 AC) | "every registered script" |
| extract-script re-runner | S18 (S02:254) | S14 then S18 |
| legend probe fixture | `text_truth.json` (S13/S15) | keep, or `legend_truth.json` under finding 6 B |
