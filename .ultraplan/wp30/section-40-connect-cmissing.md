# Section 40: connect() and cmissing() (P1.8 part a)

> Part of: WP-30 · Items: P1.8a (entry `P1.8a`; REM-§2-S06-connect, REM-S05-04-connect, GAPS2-A4-l, GAPS2-A4-m, GAPS2-B12-c, GAPS2-B12-d, GAPS2-G15-a, AUDIT-09, AUDIT-11) · Risk: yellow · Batch: 14 (merge order S39, S40, S41) · Depends on: 02, 11 · Blocks: 45 · Tasks: 14, 1 commit · Case prefix: CM

## Review amendments

- Fixed (major): CM's cscript run was placed "directly after S37's MV run". On `batch-14-base`, S38's RS run (batch 13) follows MV, so CM would have landed between MV and RS, against R1's "end of its last case block". Stata truth, 40-02 (action and verify) and the merge-rule note now place CM after RS, before `// Summary`, and the verify checks the order.
- Fixed (minor): the anchors are corrected to HEAD. `map_line`'s `dropna` is at :9942 (was :9937) and the per-y `seg_json` line at :4364 (was :4363).
- Resolved: Q-40.1. `:137` is `recast()`, which is S45's flip (S45 already takes it). The index R9 fix is filed, and no maintainer question remains.
- Cross-file (filed): index.md R10 omits S40 as a mover of the declared-plot pin (:607, +1 for `CMISSINGS`). It also lists S40 as a mover of the plot-pending pin (:240), which S40 does not move, because the pending lines stay.
- Checked at HEAD: dash.ado :941, :1060, :1063, :1182, :1184, :3150, :4104, :4125, :4134, :4137; dash_render.py `_FILTER_JS` :18562, `derived_use_json` guard :18735, `dash_spacing` :18744, `_DASH_JOIN_TYPES` :27616, `_dash_add_glyph` :28955, `_linked_scatter_view` :29706, scatter routing :30604, `_add_glyph` :30722, the callback args :32263, the copy-list anchor :33093; test_unsupported_report_is_true.py :95/:99/:137/:376; HC8-02 :387-395. The CM prefix and the new files are free.
- Checked the batch boundary: S40 is batch 14's only editor of `_make_figure_body`, `_FILTER_JS`, `_build_filter_widgets`, the mappers and `_dash_process_segment`. S39 and S41 edit none of them, and only `_needed` and the Mata header index are shared (context-only, R6).
- Rejected: "keep the stairstep-hover residual". IR-3 rules pre-expanded vertices on a Line, which keep hover, so the residual is struck.
- The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:98 (P1.8): "`connect()`, `cmissing()` and `recast()` are not honoured. `scatter y x, c(l)` draws no line, stairsteps and `connect(L)` panel lines are impossible, and missing values are always bridged." The BUGS.md entry S01 opened for this part is titled "connect() and cmissing() are not honoured: scatter y x, c(l) draws no line, stairsteps and connect(L) cannot be drawn, and cmissing(n) never breaks a line" (grade S2). Measured at `c96facd` (research `.ultraplan/wp30/research/p1-08.md` §1-§2 and its critic, StataNow 19.5):

```
dash scatter y x, c(l)            -> rc 0, "dash: ignoring unsupported option(s): connect()"; Scatter(n=6), no line
map_line {connect:J}              -> Line [(2,10),(5,20),(6,40),(1,50),(7,60),(4,70)]   (twoway: (2,10)(5,10)(5,20)(6,20)…)
map_line {connect:L}              -> the same single Line                               (twoway: 3 subpaths, broken where x drops)
map_line {cmissing:n}             -> the same bridged Line (dropna, dash_render.py:9942) (twoway: M(2,10)(5,20) | M(6,40)(1,50) | M(7,60)(4,70))
function y=sqrt(x^2-1), range(-2 2) -> Line with 150 NaN rows, drawn as two pieces    (twoway: one subpath, (-1.01,0.14) joined to (1.01,0.14))
dash scatter y x, c(l) clwidth(-1) -> rc 0                                              (twoway: r(198) "gm_linewidth must be between 0.000 and  1.0e+04")
dash scatter y x, c(l) sort       -> names connect() sort()                             (twoway: joins in x order, M(1,50)(2,10)(4,70)…)
```

**After this section**, in the saved page and the served app, before and after every saved and served filter move:
- `connect()` is drawn on scatter, line, connected, tsline, rline, rconnected, tsrline, scatteri and the fits (lfit, qfit, lowess, lpoly, fpfit, mspline, mband, kdensity, function and the fit lines of lfitci, qfitci, lpolyci, fpfitci) by twoway's measured rules: a scatter given `connect()` is twoway's connected type (its line, its `cl*` options, its `sort`); `l` direct; `L` breaks wherever x drops (a tie joins); `J`/`stairstep` flat-then-vertical and `stepstair` vertical-then-flat, drawn as a Line over pre-expanded stair vertices so every observation keeps today's tooltip (IR-3); `i`/`none` draws no line and keeps the key, out of the hover tool; an unknown name is drawn direct with twoway's own note;
- `cmissing(n)` breaks a line at each missing value of x or y on the same types (each range bound at its own), and the break holds after a move (NaN, never a vertex at 0); `function` bridges interior missing regions by default and breaks under `cmissing(n)` (P1.8.4);
- per-y lists (`c(l J)`, `c(. l)`, `c(l ..)`, `c(J =)`, `cmissing(n y)`) go through S11's splitter, `cmissings()` is accepted, and the rightmost copy wins;
- twoway's refusals are dash's (M5); where twoway draws the same picture, dash prints nothing (M6, P1.8.5); `cmissing(n)` on area/rarea and on the fits whose estimator makes its own missing points, and non-direct `connect()` on rarea, stay named (P2.42, P2.43).

**Why one section, one commit.** Everything here reads two options through one Stata fold (`_dash_connect_opt`), one renderer helper pair (`_dash_join_vertices`, `_dash_join_glyph`) and one JavaScript twin. `recast()` is S45's (P1.8b, batch 16), which builds on this section's type override.

**Test order and commit rule (rule 7).** One cycle on `wp30-s40`: 40-01 and 40-02 write the fixture and every regression test and run them against the unmodified batch-14 base, saving `$S/40-P1.8a-failure.txt` (no commit); 40-03 to 40-13 fix, flip and document; 40-14 closes the entry, deletes its `WP30_OPEN` key, replaces both markers and makes the one commit. No test-only commit exists, and no commit is red.

## Risk: [yellow] — two CRITICAL renderer symbols, a JavaScript twin on the saved filter path, and a type override that reroutes linked scatters

**Why.**
- `DashRenderer._make_figure_body` is CRITICAL (`gitnexus impact`: 4 impacted, 8 processes; re-run this pass). S40 is batch 14's only editor (R12).
- `DashRenderer._build_filter_widgets` is CRITICAL (12 impacted). S40 is batch 14's only editor (R12).
- `_FILTER_JS` is UNKNOWN (a string constant; used by `build_dropdown`/`build_slider`/`build_range` at :19525, :19587, :19650 and 116 test lines).
- The mappers reached through `_dash_glyph_dispatch` (:28501) are UNKNOWN to the index, confirmed by grep; the dispatch is LOW (4). `map_line` LOW (3), `map_function` LOW (3), `_add_glyph`/`_dash_add_glyph` LOW (3).
- Read only, never edited: `_join_order` (CRITICAL, 8), `_collect_derived_sources` (CRITICAL, 12), `_apply_line_opts` (CRITICAL, 40), `_carry_cols` (CRITICAL, 21), `_wire_brush_callbacks` (CRITICAL, 12), `_stale_cue_args`, `_collect_frozen_layers`.
- Every dash.ado and Mata symbol is UNKNOWN (not indexed): `_dash_parse_plot_opts` (897), `_dash_process_segment` (3454), `_dash_plot_opts_to_json` (3131), `_dash_fold_bw` (1545), `_dash_validate_opts` (2577), `_dash_fold_typed` (1749), `_dash_sort_opt` (1843).

**Risk factors.**
1. JSON snapshots turn NaN into null (`_dash_json_value` :17234, null at :17271-17273, through `_to_serialisable` at :32208-32211), and JS `null * k + b` is finite: a kept missing row would be drawn at 0 after a saved move.
2. Synthetic rows (stair vertices, ascending breaks) in a derived copy would enter the keep set, the brush and the KPI sums.
3. Rewriting a scatter to connected drops it from the `_linked_scatter_view` branch (`_make_figure_body` :30604), which keeps link selection on a scatter with a missing value (critic C2).
4. The cl options, `sort` and `sort(varlist)` are decided on `ptype` by `_dash_fold_cl`, `_dash_fold_typed` and `_dash_sort_opt` before any type rewrite (critic C1).
5. A Bokeh Step glyph has no hit test (critic C3), and a `line_alpha 0` line for `c(i)` still hit-tests.
6. kdensity is recomputed by the saved page's agg loop (`src.data = { x: xs, y: ys }`, :19273), which would write a plain line over a stepped one.

**Mitigation.**
1. The JS twin writes NaN for null in the join's x and y columns before it rebuilds; `TestAfterASavedMove::test_a_break_stays_a_break` asserts NaN, not 0, under node.
2. Synthetic rows carry a null row id and null in every carried column; the existing keep loop drops them (`_dkeep_ids.has(null)` is false) and `dash_apply_kpis` drops null values; the twin rebuilds them; a brush test sums a card over a stepped line.
3. Connected layers get the linked view for their markers only, through a new `marker_view` keyword; their line keeps the layer's view, so `cmissing(n)` rows survive (TR-40.10).
4. `_dash_connect_opt` runs right after `_dash_opts_repeats`, and the four steps receive `connected` for a scatter whose any y has a connect element (TR-40.4).
5. Stairs are a Line over pre-expanded vertices (IR-3); the `c(i)` renderer is left out of `HoverTool.renderers` and kept at alpha 0 after `_apply_line_opts`.
6. kdensity's agg config carries the join spec, and the agg loop rebuilds the stairs after recomputing (TR-40.11).

## Dependencies

- **Depends on: 02, 11.**
  - S02 (batch 1): TR-02.9's extractor root stanza (`DASH_REPO`, no maintainer path) and `scripts/stata_slot.sh`.
  - S11 (batch 4): `_dash_stylelist_keys()` (its comment names "S40 `connect cmissing`"), `_dash_stylelist_norm`, `_dash_stylelist_pick(raw, i)` (`.` gives "", `=` the previous, `..` repeats), `_dash_stylelist_bad(raw)`, `_dash_stylelist_check`, `(string asis)` declarations, `_dash_plot_opts_to_json _opts_json <series>` (TR-11.1-TR-11.9).
  - S01: the open entry `P1.8a`, its `WP30_OPEN` key, the markers `<!-- WP-30 P1.8a -->` at the end of `### Results that change`'s WP-30 group and of `### Changed behaviour (may need your do-files changed)`, the S40 stub `* ==== S40 P1.8a: connect() and cmissing() ====` of `test/test_wp30_truth.cscript`, and the map anchors `# WP-30 S40 (P1.8a): connect() and cmissing() (P1.8 part a)`.
  - Landed before and read here: S06 (Mata `_dash_note(before, value, after)` prints `(note:  …)` as twoway does), S14 (deleted `GlyphMapper._tag_spacing`; `derived_spacing_json` may be gone at the base), S21/S27/S35 (the axis finisher at the end of `_FILTER_JS`, R11: not touched), S26 (`map_function`'s disposition note), S37 (HC8-02's `p_honoured` list; its MV run is the last block of `test_twoway_option_parity.cscript`).
- **Blocks: 45** (P1.8b `recast()` places `_dash_recast_opt` beside `_dash_connect_opt`, reuses `_dash_join_glyph` in its draw-as helper, and splits HC8-02's remaining `recast` row).
- **Parallel batch: 14**, merge order S39, S40, S41.
- **Can run with:** S39 edits the `_dash_refline_*` functions, dash.ado's graph-option parse, a new `_dash_line_expand` and Mata `_dash_axreq_check`; S41 edits `main`, the launcher part of `_generate_app_source`, `_dash_served_template`, `_dash_harden_origin_check`, `_dash_token_auth` and `dash_setup`. S40 edits none of them, and neither partner edits `_make_figure_body`, `_FILTER_JS`, `_build_filter_widgets`, the mappers or `_dash_process_segment`.

## Evidence

Anchors re-verified with `grep -n` at `c96facd` (dash.ado 8,487 lines, dash_render.py 37,689, dash_parse.mata 6,093, dash.sthlp 3,822). Batches 1-13 move many; the executor re-finds each by symbol at `batch-14-base` and treats the numbers as approximate.

### E1. Declared, pending, serialised, never read (dash.ado)

```stata
941         CMISSing(string)          RECAST(string)            Connect(string) ///
1060    if `: length local cmissing' local _dash_pending `"`_dash_pending' cmissing"'
1063    if `: length local connect' local _dash_pending `"`_dash_pending' connect"'
1182    sreturn local cmissing         : copy local cmissing
1184    sreturn local connect          : copy local connect
3150                   bwidth degree pstyle cmissing recast connect bin width start ///
```

`_dash_process_segment`'s option pipeline: `_dash_opts_repeats` (:4104), `_dash_fold_bw "`ptype'"` (:4121, which calls `_dash_fold_cl` first), `_dash_validate_opts` (:4125), `_dash_fold_typed` (:4134), `_dash_sort_opt` (:4137); options JSON at :4330; the per-y loop writes `{"type":"`ptype'",…}` for every y (:4355-4365). `_dash_fold_cl` keeps `cl*` only on `cl_types` (:1657, scatter absent); `_dash_fold_typed` names a bare `sort` outside `sort_types` (:1780-1786); `_dash_sort_opt` writes `sortvars` only on `_so_six` (:1851, :1883).

### E2. The renderer (dash_render.py)

- `map_line` (9880) drops missing rows and joins (:9942-9944): `df = df.dropna(subset=[xvar, yvar])` then `df.loc[self._join_order(...)]`; its copy carries the row id (`_carry_cols`), so it is a derived source; one `fig.line`, then `_apply_line_opts`, then `fig.add_tools(self._hover_tool(yvar, xvar, renderers=[r]))` (:9988).
- `map_connected` (9991) = `map_line(..., connected=True)` + `map_scatter(..., view=view)`; `map_tsline` (14468) → `map_line(by_x)`; `map_rline` (13237) builds one copy per bound (`_bound_src[_yv]`) and two `fig.line`; `map_tsrline` → `map_rline`; `map_rconnected` (13313) → the bound lines plus markers; `map_scatteri` (13627) draws `fig.scatter` only.
- Fits: `map_lfit` 10840, `map_qfit` 10921, `map_lfitci` 10998, `map_qfitci` 11126, `map_lowess` 11230, `map_lpoly` 11678, `map_lpolyci` 11786, `map_fpfit` 12249, `map_fpfitci` 12326, `map_kdensity` 12779, `map_mspline` 14636, `map_mband` 14785, `map_function` 14854; each ends in `fig.line(...)` (and `_empty_fit_line`, 10822, when empty).
- `map_function` hands NaN to the Line (:14942-14946):

  ```python
  14942        fn_source = ColumnDataSource({"x_fn": x_arr, "y_fn": y_arr})
  14943        r = fig.line(x="x_fn", y="y_fn", source=fn_source,
  ```

  `_dash_function_points` (28635) turns a null point into NaN (:28675-28677).
- `_make_figure_body` (30203), scatter routing (:30604-30608):

  ```python
  30604                if ptype.lower() == "scatter":
  30605                    _plot_view = self._linked_scatter_view(
  30606                        source_for_plot, pyvar, pxvar, popts, _plot_view)
  ```

  `_linked_scatter_view` (29706) returns a BooleanFilter of the rows with both values; `map_scatter` draws from the shared source when given a view (:9802-9804), else from a dropna copy (:9805-9817). `map_line` applies any view as a row mask (`_view_mask`), so a linked view would drop `cmissing(n)` rows.
- `_DASH_JOIN_TYPES` (27616) = line, connected, area, rline, rarea, rconnected; `_dash_add_glyph` (28955) passes `order` to those only.
- The served app redraws a layer whose mapper built its sources (`_dash_redraw_for`, generated at :35039, used at :35382), so mapper changes reach it; `_dash_draw_layer` (:34922) calls `map_scatteri` and `map_function` with the plot's options.

### E3. The saved page's filter path

- `_FILTER_JS` (18562-19352). The derived loop (:18755-18782) keeps a copy's rows by row id and writes `_dsrcs[_di].data = _nd`; columns are created with `dash_own_col` (:18599). The agg loop's kdensity branch (:19195-19273) ends `src.data = { x: xs, y: ys };`.
- `_build_filter_widgets` (31899) builds the derived lists and their snapshots (:32193-32218) and sets every callback's args (:32247-32266), e.g. `_cb.args["derived_use_json"] = _der_use_json_all`.
- `_BRUSH_JS` (19372) passes every row when nothing is selected; `dash_apply_kpis` (18826) drops null values.

### E4. twoway's truth (research §2, critic; probes re-run this pass, `s40/p1.do`, `p2.do`)

- Stair, ascending, none, stylelist, repeats, cmissing, function and style-chain facts: research §2 (quoted in Stata truth and BR-40.*).
- Spellings (connectstyle/yesno `_unabbrev`, research §2): `l line d direct c connected` → direct; `L a asc ascending` → ascending; `J s stair stairstep` → stairstep; `u upstairstep step stepstair` → stepstair; `n none i` → none; case-sensitive. cmissing: `y yes on t…true` / `n no off f…false`.
- Same-picture types for `c(J)` (silent): area, bar, spike, dropline, dot, histogram, rbar, rspike, rcap, rcapsym, rscatter, the pc family, pci, pcarrowi. Drawn differently: the 22 of research §2 (rarea stays named, P2.42).
- Re-measured this pass (StataNow 19.5):

```
line y x, cmissing(x)          (note:  named style x not found in class yesno, default attributes used)
                               (note:  yesno not found in scheme, default attributes used)
                                not allowed            rc=101   (same for cmissing(N), lfit, line y y2 x cmissing(n x), cmissing(x y))
bar y x, cmissing(x)           the two notes            rc=0     (area y x, cmissing(x): the same; line …, cmissing(x) nodraw: rc 0)
scatter y x, c(bogus)          (note:  named style bogus not found in class connectstyle, default attributes used)  rc=0  (bar, rarea too)
line y x, c(l .. J)            connect(l .. J):  invalid syntax     rc=198
line y y2 x, cmissing(n .. y)  cmissings(n .. y):  invalid syntax   rc=198
scatter y x, c(i) clwidth(-1)  gm_linewidth must be between 0.000 and  1.0e+04   rc=198
scatter y x, c(l) cmissings(n); line y x, c(); cmissing(); c(l ...); c(L J); c(l) c(l); cmissing(n) cmissing(y); area y x, c(J); cmissing(yes|t)   rc=0
```

### E5. Tests that pin today's behaviour (flipped in place, never deleted; re-measured by 40-10 and 40-11)

- `test/test_unsupported_report_is_true.py` PLOT_VALUES `"cmissing": ("n", "y", "line")` (:95) and `"connect": ("l", "J", "line")` (:99), read by `test_a_plot_option_reported_unsupported_really_is[cmissing|connect]` and `test/test_help_claims_8.py::TestAnUnsupportedOptionIsInertWhenServed::test_plot_level[cmissing|connect]`. `"recast"` (:137) is S45's (Notes, Q-40.1).
- `test/test_help_claims_8.cscript` HC8-02 (:387-428): its scatter carries `cmissing(n) connect(l) recast(line) sort`, all in `p_names` (must be named).
- `test/test_stylelists.py` (S11) `_STYLE_KEYS`/`_NOT_YET`, and `test/test_varlist_expansion.cscript` SL-01's word count of `_dash_stylelist_keys()`.
- The declared-plot count `test_unsupported_report_is_true.py` (`len(_declared_plot())`, :607 at `c96facd`) and `ALIASES` (:376), which `CMISSINGS` moves (R10; Notes).
- Guards that must stay green: `test_help_claims_8.py:1353-1369` (line/connected bridge a missing row by default), `test_join_order.py` (join order unchanged), `test_twoway_option_parity.cscript` TP-01 and TP-06b (scatter without `connect()` unchanged), `test_help_claims_2.cscript` HC2-18m (twoway side).

## User stories

- **US-40.1** As a twoway user, I want `scatter y x, c(l)` to draw the connected plot twoway draws, with its `clcolor()`, `clwidth()` and `sort`, so a pasted do-file draws its line.
- **US-40.2** As a twoway user, I want `c(J)`, `c(stairstep)` and `c(stepstair)` to draw stairs, `c(L)` to break the line where x drops back, and `c(i)` to hide it, on lines and fits, with every point's tooltip kept.
- **US-40.3** As a twoway user, I want `cmissing(n)` to break a line at missing values, and `function` to bridge a gap as twoway does, in both modes and after I move a filter.
- **US-40.4** As a twoway user, I want per-y lists, `cmissings()` and the rightmost-copy rule read as twoway reads them, and twoway's refusals and notes reproduced in its words.

## Business requirements

- **BR-40.1** A scatter y whose `connect()` element is given (any value, `i` included) is drawn as twoway's connected type: its line by the element's style, its markers, the `cl*` options honoured and validated (`clwidth(-1)` r(198)), a bare `sort` joining in x order and `sort(varlist)` in that order, neither named. A y whose element is empty (`.`, missing) stays a scatter.
- **BR-40.2** Styles: direct joins consecutive points; ascending also breaks between j and j+1 where x[j+1] < x[j] (ties join), comparing consecutive drawn points; stairstep draws (x[j],y[j]) → (x[j+1],y[j]) → (x[j+1],y[j+1]); stepstair (x[j],y[j]) → (x[j],y[j+1]) → (x[j+1],y[j+1]); none draws no line and keeps the legend key without a sample. Spellings and case are twoway's; an unknown name prints twoway's connectstyle note and draws direct.
- **BR-40.3** `cmissing(n)` breaks the line at every row whose x or y is missing, in join order (under `sort` a missing x sorts last and makes no break; a row the layer's if/in or a filter drops makes no break); each range bound breaks at its own missing values and at a missing x. `cmissing(y)` (default) bridges. With a style, stairs and ascending breaks apply within each run.
- **BR-40.4** `function` bridges interior missing regions by default and breaks under `cmissing(n)`.
- **BR-40.5** The rules hold on scatter (BR-40.1), line, connected, tsline, rline, rconnected, tsrline, scatteri and the fits (lfit, qfit, lowess, lpoly, fpfit, mspline, mband, kdensity, function and the fit lines of the four ci types; the ci band steps where twoway's does), in both modes, before and after every saved and served filter move, with each real observation's tooltip kept and no tooltip over a `none` line.
- **BR-40.6** Per-y lists follow S11 (`c(l J)`, `c(. l)`, `c(l ..)`, `c(J =)`, `cmissing(n y)`); `cmissings()` and `cmiss()` are accepted; of repeated copies the rightmost wins.
- **BR-40.7** Refused in twoway's words and codes: a misplaced `..` (`connect(<v>):  invalid syntax`, `cmissings(<v>):  invalid syntax`, r(198)); an unknown `cmissing()` element on the types twoway refuses it on (two notes and ` not allowed`, r(101)); elsewhere the two notes and the default.
- **BR-40.8** Silent where twoway draws the same picture (M6). Named in the note and not drawn: `cmissing(n)` on area, rarea and on the fits whose own missing points twoway breaks at (P2.42, P2.43); a non-direct `connect()` on rarea (P2.42).

## Technical requirements

- **TR-40.1 Mata** (dash_parse.mata). New `string scalar _dash_connect_canon(string scalar kind, string scalar e)`, directly after S11's `_dash_stylelist_probe`: `kind` "connect" → `direct`/`ascending`/`stairstep`/`stepstair`/`none` by E4's table (exact, case-sensitive), "cmissing" → `y`/`n` (y yes on t tr tru true / n no off f fa fal fals false, per the fixture's `S` block); "" for an empty element; `"?"` for anything else. It reads by value, never executes text, and is O(len(e)). Header index entry after S11's five; `_needed` gains it (dash.ado :237-256). `_dash_stylelist_keys()` appends `connect cmissing` and its comment drops S40.
- **TR-40.2 Declarations** (`_dash_parse_plot_opts`). `Connect(string)` → `Connect(string asis)`, `CMISSing(string)` → `CMISSing(string asis)` (minimums unchanged); add `CMISSINGS(string asis)`. Directly before S11's normalise block: `if `"`macval(cmissings)'"' != "" local cmissing : copy local cmissings`, so a lone `cmissings()` copy sets `s(cmissing)` and the repeats probe keys it as `cmissing` (rightmost wins). The pending lines :1060 and :1063 stay (the `sort` precedent); their comment says `_dash_connect_opt` takes them off where drawn or silent.
- **TR-40.3 `_dash_connect_opt`** (new sclass program after `_dash_sort_opt`'s `end`, `version 19`, header comment citing E4; `args ptype nser`):
  1. Read `s(connect)`/`s(cmissing)` by value; both empty → `sreturn local _cn_types ""`, `exit`.
  2. `_dash_stylelist_bad` on each: `mata: _dash_say("err", "connect(", <raw>, "):  invalid syntax")` / `"cmissings("`, `exit 198`.
  3. For i = 1..`nser`, `_dash_stylelist_pick` then `_dash_connect_canon`. connect `"?"` → `mata: _dash_note("named style ", <e>, " not found in class connectstyle, default attributes used")` (as often as the fixture's `C_BOGUS2` shows twoway printing it) and `direct`. cmissing `"?"` → the two notes (`named style <e> not found in class yesno, default attributes used`; `yesno not found in scheme, default attributes used`); then on `cm_refuse` types `display as error " not allowed"` and `exit 101`, else the default. Elements past `nser` are read only if the fixture's `R_EXTRA` probe shows twoway reading them.
  4. Write back `s(connect)`/`s(cmissing)` as blank-separated canonical lists with `.` for an empty element, so S11's per-series writer gives each y its own value.
  5. ptype scatter: `s(_cn_types)` = per y `connected` (element non-empty) or `scatter`; `s(_cn_any)` 1 if any is connected.
  6. Pending: take `connect` off `s(_pending)` unless ptype is rarea and some element is not direct; take `cmissing` off unless some element is `n` and ptype is in `area rarea` or the fixture-derived `cm_named` list. Constants `cm_refuse` and `cm_named` are transcribed from the fixture's `M` block (types whose `cmissing(x)` rc is 101; fits whose `cmissing(n)` path differs from `cmissing(y)` on `sysuse auto` with a missing mpg, less `function`, which dash draws); `TestTheAdoTables` holds them equal.
  - Every echo goes through `_dash_say`/`_dash_note`; values never reach a command line.
- **TR-40.4 Wiring** (`_dash_process_segment`). Directly after the `_dash_opts_repeats` call (:4104): `local _cn_n 1`, `if `"`yvarlist'"' != "" local _cn_n : word count `yvarlist'`, `_dash_connect_opt "`ptype'" `_cn_n'`, then copy `s(_cn_types)`/`s(_cn_any)` into locals `_cn_types`/`_cn_any` and set `local _cn_ptype "`ptype'"`, `if "`ptype'" == "scatter" & "`_cn_any'" == "1" local _cn_ptype connected`. `_dash_fold_bw`, `_dash_validate_opts`, S11's `_dash_stylelist_check`, `_dash_fold_typed` and `_dash_sort_opt` take `"`_cn_ptype'"`. In the per-y loop (the `seg_json` line, :4364) the type is `word `_yi' of `_cn_types'` when `_cn_types` is non-empty, else `ptype`. No other line of the segment changes.
- **TR-40.5 Renderer helpers** (module functions, after `_dash_sort_cols_named`'s neighbours):
  - `_dash_join_vertices(xs, ys, style, cmiss) -> (xi, yi)`: pure; `xs`/`ys` float arrays in join order; returns two int64 arrays naming, per output row, the input row its x and y come from (-1 = a NaN break). Rules: rows non-finite in x or y are dropped unless `cmiss == "n"` (then kept as `(j, j)`, NaN breaks); `ascending` inserts `(-1, -1)` between finite j, j+1 with x[j+1] < x[j]; `stairstep` inserts `(j+1, j)`, `stepstair` `(j, j+1)` between finite j, j+1 (after the ascending check). `style` outside the five names → `direct`; `cmiss` other than `"n"` → `"y"`. O(n); at most 3n-2 rows.
  - `_dash_join_glyph(mapper, fig, source, xcol, ycol, options, line_kwargs, hover=None)`: reads `options["connect"]`/`["cmissing"]`; for direct with `cmissing` y on a source already clean, calls `fig.line(**line_kwargs)` exactly as today (byte-identical); otherwise builds the expanded source from `_dash_join_vertices` (synthetic rows: null row id and null in every carried column), sets `src._dash_join = {"x": xcol, "y": ycol, "style": s, "cmiss": c}` when the source carries `_ROW_ID_COLUMN`, draws `fig.line`, and for `none` forces `line_alpha`, `nonselection`/`muted`/`hover` line alphas to 0 after `mapper._apply_line_opts`. It adds `mapper._hover_tool(...)` with `renderers=[r]` only when `hover` is given and the style is not none. Returns the renderer.
- **TR-40.6 map_line** (hub): the `dropna` (:9942) is skipped under `cmissing n` (the view mask and `_join_order` unchanged, so missing x sorts last); the `fig.line` and hover lines become one `_dash_join_glyph` call over the joined frame. `map_rline` does the same per bound copy. `map_connected` gains `marker_view=None`, passed to `map_scatter` as `view` when given. `map_scatteri` draws its points through `_dash_join_glyph` when `connect` is given (no row id, no JS). `map_tsline`, `map_tsrline`, `map_rconnected` forward options unchanged (a test pins it).
- **TR-40.7 Fits.** Every fit line of E2 (and `_empty_fit_line`) draws through `_dash_join_glyph`; the ci bands of lfitci/qfitci/lpolyci/fpfitci use `fig.varea_step(mode="after"|"before")` under stairstep/stepstair where the fixture's band path is stepped, else stay `varea`. `cmissing` is not applied to fit output (P2.43; named per TR-40.3).
- **TR-40.8 map_function**: by default drop the non-finite rows of `x_fn`/`y_fn` before drawing (bridge, M1/P1.8.4); under `cmissing n` keep them; then `_dash_join_glyph`.
- **TR-40.9 kdensity**: when the style is not direct, `r._dash_agg_config["join"] = {"style": s}`; the drawn source holds the expanded vertices.
- **TR-40.10 `_make_figure_body`** (CRITICAL, warn; batch 14's only editor, R12): for `ptype.lower() == "connected"` compute `_mk_view = self._linked_scatter_view(source_for_plot, pyvar, pxvar, popts, _plot_view)` and pass `marker_view=_mk_view` to `self._add_glyph` (only when it differs from `_plot_view`); the scatter branch is unchanged. `DashRenderer._add_glyph` (30722) and `_dash_add_glyph` (28955) gain `marker_view=None`, forwarded to `connected` only.
- **TR-40.11 JS twin** (`_FILTER_JS`): a new `function dash_join_rebuild(nd, spec, ROW_ID)` beside `dash_spacing`, the twin of `_dash_join_vertices`: writes NaN for null/undefined in `spec.x` and `spec.y`, computes the same index pairs, and rebuilds every column with `dash_own_col` (synthetic rows null, `ROW_ID` null). In the derived loop, after the keep loop and before `_dsrcs[_di].data = _nd`: `const _jn = _djoin[_di]; if (_jn && _jn.x in _nd && _jn.y in _nd) _nd = dash_join_rebuild(_nd, _jn, ROW_ID);` with `_djoin` parsed from `derived_join_json` under a `typeof` guard. The kdensity branch writes `src.data = ac.join ? dash_join_rebuild({x: xs, y: ys}, {x: "x", y: "y", style: ac.join.style, cmiss: "y"}, null) : { x: xs, y: ys };`. No `eval`, no column name interpolated into code.
- **TR-40.12 `_build_filter_widgets`** (CRITICAL, warn; R12): beside the derived lists (after `_der_srcs_orig_all`), `_der_join = [getattr(s, "_dash_join", None) for s in _der_srcs_all]`; set `_cb.args["derived_join_json"] = json.dumps(_der_join)` only when any entry is not None, so a page without a join is unchanged. `_collect_derived_sources` and `_wire_brush_callbacks` are not edited.
- **TR-40.13 Served copy list** (R2 row S40): `"_dash_join_glyph", "_dash_join_vertices",` on one new line directly after `"_dash_sort_cols_named", "_dash_take_sort_columns",` (33093). The R2 row names the first; the second rides the same anchor (X.1, append only). `_generate_app_source` is not edited.
- **TR-40.14 Registries** (X.5), under S40's anchors, alphabetical: `function_test_map.py` `'_dash_join_glyph': 'test/test_connect_options.py::TestTheJoinGlyph::test_each_style'`, `'_dash_join_vertices': 'test/test_connect_options.py::TestTheVertices::test_every_rule'`; `program_coverage_map.py` `COVERAGE["dash.ado"]["_dash_connect_opt"] = ("test_twoway_option_parity.cscript:CM-01", "test_twoway_option_parity.cscript:CM-12")`, `COVERAGE["dash_parse.mata"]["_dash_connect_canon"] = ("test_twoway_option_parity.cscript:CM-08", "test_twoway_option_parity.cscript:CM-05")`.
- **TR-40.15 Help** (R3: Plot types, S40's in batch 14; Unsupported, as pending mover):
  - Plot types, a `{ul:Connecting and missing values.}` paragraph after `{ul:Join order.}` (:275-296): BR-40.1-BR-40.4, BR-40.6, the spellings, the named residuals (BR-40.8).
  - Unsupported "Not drawn" (:3728-3735): the `connect(list)` and `cmissing(y|n)` sentences become one: "`cmissing(n)` on area and rarea, and on lowess, fpfit, lpoly, mspline and mband (the list the fixture gives), and `connect()` other than direct on rarea -- see Plot types." The cl paragraph (:3737-3750) adds "and of a scatter given `connect()`" to the types whose line they style; the sort sentence (:3696-3701) adds "and on a scatter given `connect()`". Lines ≤ 79 characters.
- **TR-40.16 Security (rule 1).** Option values reach Stata command lines only inside `macval()`; canonicalisation is a fixed table; echoes go through `_dash_say`/`_dash_note` (bounded at 4000 characters, SMCL-escaped by S06). The renderer accepts only the five style names and `n`, everything else being the default, so a hand-written spec cannot select code paths; column names come from the source and pass through `json.dumps` as data; the JS reads them only as keys, creates columns with `dash_own_col`, and never evaluates text. Row growth is bounded (3n-2).

## Boundaries

- **Batch 14 partners:** S39's `_dash_refline_*`, graph-option parse, `_dash_line_expand`, `_dash_axreq_check`; S41's `main`, `_generate_app_source`, `_dash_served_template`, `_dash_harden_origin_check`, `_dash_token_auth`, `dash_setup`. Not touched.
- **Read only:** `_join_order`, `_collect_derived_sources`, `_apply_line_opts`, `_carry_cols`, `_wire_brush_callbacks`, `_stale_cue_args`, `_collect_frozen_layers`, the axis finishers (R11), S11's splitter functions (one key list extended), `_dash_fold_cl`, `_dash_fold_typed`, `_dash_sort_opt` (called with a different type, not edited).
- **S45 (P1.8b):** `recast()`, `recastas()`, `type()`, the ci-type recast refusal, PLOT_VALUES' `recast` row, HC8-02's `recast` split. **P2.42** area/rarea breaks and rarea `c(J)`; **P2.43** estimator-generated missing points; **P2.30** join-order edge cases.
- **Never:** `scripts/regen_option_surface.py` (IR-7); a hand patch of the fixture; `_DASH_FILTER_MASK_JS`; `build_dropdown`/`build_slider`/`build_range` (the `typeof` guard makes their defaults unnecessary).

## Stata truth

### `scripts/extract_connect_truth.do` → `test/fixtures/connect_truth.json`

TR-02.9's stanza (`<file>` = `extract_connect_truth.do`), then `adopath ++ "`repo'/"` and `global dash_nobrowser 1`. `_meta` as S19's `scripts/extract_series_label_truth.do` (`stata_version`, `born_date`, `dash_commit` from `git rev-parse HEAD` captured with `shell` into a local and read through `Macro.getLocal`, `extracted`; the python block never calls Stata, never uses `shell=True`, writes a backtick as `\x60`), plus `scheme: "stcolor"`. Each probe runs `capture noisily` inside a named log (`log using "<tmp>/cm_<id>.log", text replace name(cmp)`) so its notes and error lines are recorded; SVGs go to `c(tmpdir)` and are read only through `scripts/svg_truth.py` (`svg_document`, axis mapping by `svg_axis_reading`), each `<path d>` split at `M` into subpaths of `[x, y]` in data units rounded to 1e-6 (extract_join_order_truth.do's J8 reader, extended to y).

- **Data T** (research t1): `x = 2 5 3 6 1 . 7 4`, `y = 10 20 . 40 50 45 60 70`, `y2 = 12 22 32 42 . 47 62 72`, `y3 = y + 1`. **Data TIE**: x = 1 3 3 2 4 5 6, y = 10..70. **Data A**: `sysuse auto`, `replace mpg = . in 5`. **Data F**: none (function).
- **P (paths)**: P01 `scatter y x, c(l)`; P02 `line y x, c(J)`; P03 `line y x, c(stepstair) sort`; P04 `line y x, c(L)`; P05 TIE `line y x, c(L)`; P06 `line y x, c(i)` (legend on); P07 `scatter y x, c(bogus)`; P08 `line y x, cmissing(n)`; P09 `scatter y x, c(l) cmissing(n)`; P10 `scatter y x, c(l) cmissing(n) sort`; P11 `line y x if _n != 5, cmissing(n)`; P12 `line y y2 x, cmissing(n)`; P13 `line y y2 x, cmissing(n ..)`; P14 `rline y y2 x, cmissing(n)`; P15 `rconnected y y2 x, cmissing(n)`; P16 `line y x, cmissing(n) c(J)`; P17 `line y x, cmissing(n) c(L)`; P18 `function y=sqrt(x^2-1), range(-2 2)`; P19 P18 with `cmissing(n)`; P20 `scatter y y2 x, c(l)`; P21 `c(. l)`; P22 `scatter y y2 y3 x, c(l ..)`; P23 `c(J =)`; P24 `c(l . J)`; P25 `line y x, c(l) c(J)`; P26 `scatter y x, c(l) sort`; P27 `scatter y y2 x, c(l) sort(y2)`; P28 `scatter y x, c(l) clcolor(red)` (stroke recorded); P29 `tsline y, c(J)` and `tsrline y y2, cmissing(n)` (tsset t = _n); P30 `scatteri 1 2 3 4 2 6, c(J)`.
- **F (fits, Data A)**: each of lfit, qfit, lowess, lpoly, fpfit, mspline, mband (`mpg weight`), kdensity (`mpg`), `function y=x^2, range(0 4)`, and lfitci, qfitci, lpolyci, fpfitci with `c(J)`, `c(stepstair)`, `c(i)`; band paths recorded for the ci types.
- **S (spellings, Data T, `line y x`)**: `c()` with each spelling of E4 plus `dir`, `asce`, `stairs`, `Direct`, `j`; `cmissing()` with y yes on t tr tru true n no off f fa fal fals false ye N x; recorded `equal_to` the canonical probe and notes.
- **M (matrix)**: for each of the 40 plot types on Data T/A (vars as `test_twoway_option_parity.cscript:227`'s loop builds them), `c(J)`, `c(L)`, `c(i)`, `c(bogus)`, `cmissing(n)`, `cmissing(x)`: `rc`, `lines`, `same_as_base` (SVG equal apart from `<desc>`).
- **R (refusals)**: `c(l .. J)`; `line y y2 x, cmissing(n .. y)`; `cmissing(n x)` on `line y y2 x` and `R_EXTRA` on `line y x`; `cm(n)`; `cmiss(n)`; `cmissings(n)`; `scatter … c(i) clwidth(-1)`; `scatter … c(l) clwidth(-1)`; `C_BOGUS2` `scatter y y2 x, c(bogus bogus)`.
- **Records:** `probes[<id>]` for P, F, S and R (`cmd`, `rc`, `lines` = the log's `(note:` and error lines, `paths` for P and F, `equal_to` for S) and `matrix[<type>][<option as typed>]` for M (`rc`, `lines`, `same_as_base`).
- **Expected** (research §2, E4): P02 `[(2,10),(5,10),(5,20),(6,20),(6,40),(1,40),…]`; P04 three subpaths; P05 `(1,10)(3,20)(3,30) | (2,40)…`; P08 three subpaths; P18 one subpath, P19 two; M `cmissing(x)` rc 101 on line and lfit, 0 on bar and area.
- Run: `DASH_REPO="$WT" "$SLOT" "$S" "$WT/scripts/extract_connect_truth.do"` (log `$S/extract_connect_truth.log`, about 400 exports). `git add -f test/fixtures/connect_truth.json`.

### Area cases, `test/test_twoway_option_parity.cscript` (R1: one contiguous run at the end of its last case block, after S38's RS run (batch 13), before the `// Summary` divider)

Each runs live twoway (`capture noisily twoway … nodraw` where the case needs no draw, else drawn to `c(tmpdir)`) and dash (`_ztp_run`), comparing rc and the error/note lines, in the script's `nfail`/`faillist` form, printing `CM-nn PASS: …`. Data: Data T plus `sysuse auto`-based rows as the TP blocks build them.
- **CM-01** `line`, `scatter` with `c(l .. J)`: 198 both, `connect(l .. J):  invalid syntax`.
- **CM-02** `line y y2 x, cmissing(n .. y)`: 198 both, `cmissings(n .. y):  invalid syntax`.
- **CM-03** `cmissing(x)`, `cmissing(N)`, `cmissing(n x)` on line, lfit and every `cm_refuse` type: 101 both, the three lines equal.
- **CM-04** `cmissing(x)` on bar and area: rc 0 both, the two notes in both logs.
- **CM-05** `c(bogus)`, `c(Direct)` on scatter, line, bar: rc 0, twoway's note in both; dash's spec `connect` = `direct`.
- **CM-06** `scatter … c(l) clwidth(-1)`, `c(i) clwidth(-1)`: 198 both (dash's counterpart of HC2-18m); `c(l) clcolor(red)` keeps `clcolor` in the spec.
- **CM-07** `scatter … c(l) sort`: no note naming sort; `scatter y y2 x, c(l) sort(y2)`: the first plot's `sortvars` is `y2`.
- **CM-08** `cmissings(n)`, `cmiss(n)` rc 0 with spec `cmissing` `n`; `cm(n)` 198 both, `option cm() not allowed`; `c(stair)`, `c(u)`, `c(a)` canonical in the spec.
- **CM-09** `c(l) c(J)` → `stairstep`; `cmissing(n) cmissing(y)` → `y`.
- **CM-10** same-picture types (`bar`, `spike`, `dot`, `histogram`, `pcspike` with `c(J)`/`cmissing(n)`): rc 0, no "ignoring unsupported" note.
- **CM-11** named: `area … cmissing(n)`, `rarea … c(J)`, `lowess … cmissing(n)`: the note names the option.
- **CM-12** per-y spec: `scatter y y2 x, c(l)` → plot 1 `"type":"connected"` with `"connect":"direct"`, plot 2 `"type":"scatter"` without `connect`; `scatter y y2 y3 x, c(J =)` → stairstep, stairstep, scatter.

### The S40 block of `test/test_wp30_truth.cscript` (R1)

Helper `_s40_paths` (python, directly above S01's S40 header) reads a saved page's embedded document JSON, finds each Line/VAreaStep renderer and returns its vertex runs split at NaN. Between S01's S40 start and end lines:
- **CM-20** P01, P02, P03, P04, P05, P08, P09, P12, P16, P17: dash's saved runs equal twoway's subpaths drawn live (within 1e-6 relative).
- **CM-21** P18, P19 (function bridge and break).
- **CM-22** P20-P24 per y.
- **CM-23** lfit and kdensity `c(J)`, lpolyci `c(J)` band.
- **CM-24** P28: dash's connecting line colour equals twoway's stroke.

## TDD test stubs

### Regression tests, new `test/test_connect_options.py` (red at the batch-14 base unless marked guard; 40-01)

Module docstring: the defect (Overview), E4, the fixture. Imports: `dash_render as dr`; from `test_join_order`: `_plot`, `_spec`, `_saved`, `_served`, `_saved_move`, `_served_move`, `_saved_figs`, `_served_figs`; `js_runner.requires_node`. `_FIX = json.load(test/fixtures/connect_truth.json)`; `_runs(renderer)` = vertex runs split at non-finite values (datetimes as epoch ms).

- Test: stamped fixture (four `_meta` keys, `stata_version` `19.`, every probe id of Stata truth) — `TestTheFixture::test_it_is_stamped`
- Test: `_dash_join_vertices` reproduces P02, P03, P04, P05, P08, P16, P17 as runs; `none` gives the rows; unknown style → direct; 3n-2 bound; 10^6 rows within 1 s — `TestTheVertices::test_every_rule`
- Test: `_dash_join_glyph` per style: Line (never Step); synthetic rows null in every carried column and in the row id; `_dash_join` spec set only on a row-id source; direct/y on a clean source byte-identical to `fig.line` — `TestTheJoinGlyph::test_each_style`
- Test (both modes): `type connected` with `connect direct` from a scatter spec draws a Line in data order plus markers (P01) — `TestScatterConnectIsConnected::test_line_and_markers[saved|served]`
- Test (both modes): `clcolor red` and `sort` on that layer: red line, x order (P26, P28); `sortvars y2` joins in y2 order (P27) — `TestScatterConnectIsConnected::test_cl_options_and_sort[<case>-saved|served]`
- Test (both modes): J and stepstair equal P02/P03; the renderer is in its HoverTool's `renderers`; each real row's tooltip fields equal today's — `TestStairsteps::test_vertices_and_hover[<style>-saved|served]`
- Test (both modes): L breaks where x drops, ties join (P04, P05) — `TestAscendingBreaks::test_breaks[<case>-saved|served]`
- Test (both modes): cmissing n on line, connected, tsline, rline, rconnected, tsrline equals P08, P12-P15, P29; under sort missing x last (P10); if-dropped rows no break (P11) — `TestCmissingNo::test_breaks[<type>-saved|served]`
- Guard: cmissing y/absent bridges (P08's twoway default; `test_help_claims_8.py:1353` stays green) — `TestCmissingNo::test_the_default_bridges`
- Test (both modes): none: line alpha 0 also after `lcolor(red%50)`, legend item present, renderer absent from every HoverTool — `TestConnectNone::test_no_line_key_kept`
- Test (both modes): P18 one run (fails now: two), P19 two runs — `TestFunctionBridgesByDefault::test_bridge_and_break[saved|served]`
- Test (both modes): J, stepstair and none on the 9 fits and 4 ci fit lines, vertices equal F; ci bands stepped where F's are — `TestFitsHonourConnect::test_fit[<type>-<style>-saved|served]`
- Test (both modes): per-plot options as dash.ado writes them for P20-P24 draw as the fixture — `TestStylelistsPerY::test_case[<probe>-saved|served]`
- Test (node): after each saved move a cmissing n break is NaN (fails at the base by construction of the case: a vertex at 0), L breaks and J stairs are rebuilt from the kept rows and equal `_dash_join_vertices` of them; synthetic rows hold null row ids — `TestAfterASavedMove::test_a_break_stays_a_break`, `::test_breaks_and_stairs_are_rebuilt[<style>]`
- Test (node): kdensity `c(J)` after a move is stepped and equals `_dash_join_vertices` of the recomputed curve — `TestAfterASavedMove::test_kdensity_keeps_its_stairs`
- Test (node): a sum KPI brushed with nothing selected on a stepped line equals the plain line's — `TestAfterASavedMove::test_the_brush_ignores_synthetic_rows`
- Test (served): the same moves through `_served_move` — `TestAfterAServedMove::test_moves[<style>]`
- Test (node): a linked `connected` layer with a missing y shows another graph's selection on its markers, and its cmissing n line keeps its break — `TestLinkedConnectedMarkers::test_selection_and_break`
- Test (both modes): area cmissing n, rarea (with y2) `c(J)`, lowess cmissing n render as without the option — `TestTheResidualsStayNamed::test_inert[<case>-saved|served]`
- Test: hand-written specs (`connect` "Bogus", "<script>", 10,000 characters, a number; `cmissing` "x") draw direct and bridged without an exception — `TestHandWrittenSpecs::test_defaults`
- Test (node): 200 random series (NaN, ties, drops) per style and cmiss: JS `dash_join_rebuild` equals `_dash_join_vertices` — `TestTheJsTwin::test_agrees`
- Test: a page without connect()/cmissing() carries no `derived_join_json` arg — `TestTheJsTwin::test_no_join_no_arg`
- Test: the generated app defines both helpers — `TestTheServedCopy::test_the_app_defines_the_names`
- Test: dash.ado declares `Connect(string asis)`, `CMISSing(string asis)`, `CMISSINGS(string asis)`; `_dash_connect_opt` is called after `_dash_opts_repeats` and before `_dash_fold_bw`; the per-y type; Mata keys hold `connect cmissing` — `TestTheAdoText::test_declared_and_wired`
- Test: `cm_refuse` and `cm_named` in `_dash_connect_opt` equal the fixture's M block — `TestTheAdoTables::test_they_are_the_fixtures`
- Test: dash.sthlp's Plot types holds the new paragraph; the Unsupported entry names only the residuals — `TestTheHelp::test_documented`
- Shared: `test/test_mode_parity.py` CORPUS `_case("connect() styles (WP-30 P1.8a)", [_plot-equivalents of P02, P04, P06 and a scatter given connect])` and `_case("cmissing(n) and function (WP-30 P1.8a)", […])`; `test/test_saved_filter_layers.py` `_CORPUS` gains a J line and a cmissing n line under `_MOVES[0]`.
- Test (cscript): CM-01..CM-12; CM-20..CM-24.

### Pinned tests to flip (R9; re-measured by 40-10 and 40-11, never trusted)

- `test_unsupported_report_is_true.py` PLOT_VALUES `"cmissing": ("n", "y", "area")` and `"connect": ("l", "J", "rarea")`: the types where each stays named and inert; `ALIASES` gains `cmissings`; the declared-plot count +1 (R10 comment). `"recast"` untouched (Q-40.1).
- HC8-02: `cmissing`, `connect` and `sort` move from `p_names` to S37's `p_honoured` list; comment and done-text counts corrected; `recast` stays named (S45 splits).
- `test_stylelists.py` `_STYLE_KEYS` gains and `_NOT_YET` loses `connect`, `cmissing`; SL-01's count +2.

## Test plan

| What | How | Fixture / data | Both modes? |
|---|---|---|---|
| Parse, refusals, notes, spec | cscript CM-01..CM-12 against live twoway; pytest `TestTheAdoText`, `TestTheAdoTables` | Data T, auto; dash.ado | n/a |
| Vertex rules | pytest `TestTheVertices`, `TestTheJoinGlyph` | `connect_truth.json` | n/a |
| Drawing | pytest `TestScatterConnectIsConnected`, `TestStairsteps`, `TestAscendingBreaks`, `TestCmissingNo`, `TestConnectNone`, `TestFunctionBridgesByDefault`, `TestFitsHonourConnect`, `TestStylelistsPerY`; cscript CM-20..CM-24 | fixture P, F | yes |
| After moves | pytest `TestAfterASavedMove` (node), `TestAfterAServedMove`, saved-move corpus | `_DF`-style frames | yes |
| JS twin | pytest `TestTheJsTwin` (node) | random | saved |
| Link | pytest `TestLinkedConnectedMarkers` (node) | literal | saved |
| Residuals named | pytest `TestTheResidualsStayNamed`; CM-11 | literal | yes |
| Parity | `test_mode_parity.py` two CORPUS cases | `_DF` | yes |
| Served wiring | `TestTheServedCopy`; G4 guards | generated app | served |
| Help, pins, registries, tracking | `TestTheHelp`, `test_help_conformance.py`, `test_help_claims_8.py`, `test_unsupported_report_is_true.py`, `test_stylelists.py`, `test_function_test_map.py`, `test_program_coverage_map.py`, `test_file_headers.py`, `test_cscript_hygiene.py`, `test_tracking_documents.py`, `test_fixtures_are_committed.py` | — | n/a |

**Acceptance criteria.**
- **AC-40.1** (BR-40.1, BR-40.6, BR-40.7) CM-01..CM-12 PASS against live twoway; `TestTheAdoText`, `TestTheAdoTables` pass.
- **AC-40.2** (BR-40.2-BR-40.5) every drawing class passes in both modes for every fixture probe; CM-20..CM-24 PASS.
- **AC-40.3** (BR-40.3, BR-40.5) `TestAfterASavedMove` (not skipped), `TestAfterAServedMove`, `TestTheJsTwin`, `TestLinkedConnectedMarkers` pass; `test_mode_parity.py` passes with untouched `ALLOWED`/`_MUST_WARN`.
- **AC-40.4** (BR-40.8) `TestTheResidualsStayNamed` and CM-10/CM-11 pass; neither option appears in any "ignoring unsupported" note of a type it is drawn or silent on.
- **AC-40.5** Every flipped node passes with a `Flipped:` line; no test is deleted; the full suite through the queue reports 0 failed; G7 prints 0 twice.

## Tasks

**Commit boundary.** Tasks 40-01 to 40-14 form one commit, made by 40-14 on `wp30-s40` with the subject `Draw connect() styles and cmissing() breaks as twoway draws them (WP-30 P1.8a)`; it closes the entry, deletes its `WP30_OPEN` key and replaces both markers. `$S` is `/private/tmp/claude-501/-Users-billy-Desktop-Programs-StataPrograms-d-dash/55d6df3b-6200-4eb1-99b7-fa28b88519a2/scratchpad/wp30`, `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s40`, `$SLOT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh`; every command uses `git -C "$WT"` or `$WT` paths. A cscript runs through the driver: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" "<script>.cscript" > "$S/run_<script>.do"`, then `WP30_ONLY=S40 "$SLOT" "$S" "$S/run_<script>.do"` (log `$S/run_<script>.log`). Each task appends the files it changed to `$S/40-files.txt`.

<task type="auto" id="40-01">
  <name>Write the fixture and pytest regressions</name>
  <files>scripts/extract_connect_truth.do, test/test_connect_options.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    Check `git -C "$WT" rev-parse HEAD` equals `cat "$S/batch-14-base.txt"` and `git -C "$WT" branch --show-current` prints `wp30-s40`; stop otherwise. Create `scripts/extract_connect_truth.do` exactly as "Stata truth" describes (TR-02.9 stanza, data T/TIE/A, blocks P, F, S, M, R, named logs, `scripts/svg_truth.py` reader, S19's `_meta`) and run `DASH_REPO="$WT" "$SLOT" "$S" "$WT/scripts/extract_connect_truth.do"`; then check `~/.stata19/console/stata19.rc` still holds `python_exec`. Create `test/test_connect_options.py` with every stub of "TDD test stubs" (new names as `dr._dash_join_vertices`, `dr._dash_join_glyph`, so they fail with AttributeError now), and append the two CORPUS cases to `test/test_mode_parity.py` before `CORPUS`'s closing bracket, after any earlier section's cases. Run `python3 -m pytest test/test_connect_options.py -q -n 6 -p no:cacheprovider -rf > "$S/40-new.log" 2>&1` and the parity file with `-k "WP-30 P1.8a"` appended to the same log. Re-measure E5's pins (`-k "connect or cmissing or recast"` on `test_unsupported_report_is_true.py` and `test_help_claims_8.py`) and whether `test_varlist_expansion.py::_SINGLE_Y_BASELINE_SHA256` would move (it does only if its page has a filter). Write `$S/40-P1.8a-failure.txt`: the base sha, one line per failing node with its first error line, then "Guards (pass at the base)". Edit no shipped file; do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json; d=json.load(open('$WT/test/fixtures/connect_truth.json')); m=d['_meta']; print(all(k in m for k in ('stata_version','born_date','dash_commit','extracted')), len(d['probes']['P18']['paths']), len(d['probes']['P19']['paths']), d['matrix']['line']['cmissing(x)']['rc'], d['matrix']['bar']['cmissing(x)']['rc'])"` prints `True 1 2 101 0`; `grep -c FAILED "$S/40-new.log"` is at least 30; `git -C "$WT" diff --name-only -- dash.ado dash_parse.mata dash_render.py` prints nothing.]]></verify>
  <done>The twoway connect fixture existed and every pytest regression test was shown failing on the unmodified tree, with the failure text saved.</done>
</task>

<task type="auto" id="40-02">
  <name>Write the cscript and move cases</name>
  <files>test/test_twoway_option_parity.cscript, test/test_wp30_truth.cscript, test/test_saved_filter_layers.py</files>
  <action><![CDATA[
    In `test/test_twoway_option_parity.cscript`, directly before the `// Summary` divider (after S38's RS run, the last block on `batch-14-base`; never between S37's MV run and S38's RS run), add one contiguous run headed `// CM: connect() and cmissing(), read as twoway reads them (WP-30 P1.8a)` with CM-01..CM-12 of "Stata truth", in the script's `nfail`/`faillist` form. In `test/test_wp30_truth.cscript` put `_s40_paths` directly above S01's `* ==== S40 P1.8a: connect() and cmissing() ====` header and CM-20..CM-24 between S01's S40 start and end lines. Append the two `_CORPUS` cases to `test/test_saved_filter_layers.py`. Run both scripts through the driver on the unmodified shipped files and `test_saved_filter_layers.py -k "WP-30 P1.8a"`. Append every `CM-nn FAIL` line, with the twoway line it quotes, to `$S/40-P1.8a-failure.txt`, and list passing cases under the guards. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -cE "CM-(0[1-9]|1[0-2]) FAIL" "$S/run_test_twoway_option_parity.log"` is at least 8 (CM-04 and CM-10 may pass as guards); `grep -cE "CM-2[0-4] FAIL" "$S/run_test_wp30_truth.log"` is at least 4; `grep -c "MV-11 PASS" "$S/run_test_twoway_option_parity.log"` and `grep -c "RS-12 PASS" "$S/run_test_twoway_option_parity.log"` each print 1, and `grep -n "RS-12 PASS\|CM-01" "$WT/test/test_twoway_option_parity.cscript"` lists RS-12 above CM-01.]]></verify>
  <done>The area cases, the live twoway comparisons and the saved-move cases were in place and shown failing where the defect lies.</done>
</task>

<task type="auto" id="40-03">
  <name>Add the Mata canonicaliser and keys</name>
  <files>dash_parse.mata</files>
  <action><![CDATA[
    Apply TR-40.1: `_dash_connect_canon(kind, e)` directly after S11's `_dash_stylelist_probe`, with a comment citing E4's `_unabbrev` tables and the fixture's S block (transcribe the accepted spellings from the fixture where it differs from E4, never the reverse); its header index entry after S11's five, in their form; `connect cmissing` appended to `_dash_stylelist_keys()`'s returned list, and "S40 `connect cmissing`" removed from its comment. No other Mata function changes.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_file_headers.py -q -n0 -p no:cacheprovider` fails only on `_needed` lacking `_dash_connect_canon` (fixed by 40-04); `grep -c "_dash_connect_canon" "$WT/dash_parse.mata"` is at least 2.]]></verify>
  <done>Mata canonicalised every connectstyle and yesno spelling twoway accepts and listed both options as style lists.</done>
</task>

<task type="auto" id="40-04">
  <name>Fold connect and cmissing in Stata</name>
  <files>dash.ado</files>
  <action><![CDATA[
    These programs are UNKNOWN to the index; callers confirmed by grep (Risk). Apply TR-40.2 (the three declarations, the `cmissings` copy before S11's normalise block, the pending lines' comment), TR-40.3 (`_dash_connect_opt` after `_dash_sort_opt`'s `end`, `version 19`, `cm_refuse`/`cm_named` from the fixture's M block), `_dash_connect_canon` added to `_needed` (:237-256) after S11's names, and TR-40.4 (the call after `_dash_opts_repeats`, `_cn_ptype` passed to `_dash_fold_bw`, `_dash_validate_opts`, `_dash_stylelist_check`, `_dash_fold_typed`, `_dash_sort_opt`, and the per-y type at :4364). Edit no other program; never run `scripts/regen_option_surface.py`.
  ]]></action>
  <verify><![CDATA[`test_twoway_option_parity.cscript` through the driver prints `CM-01 PASS` to `CM-12 PASS` and no other new FAIL; `python3 -m pytest test/test_connect_options.py -q -n0 -p no:cacheprovider -k "TestTheAdoText or TestTheAdoTables"` and `test/test_file_headers.py` pass.]]></verify>
  <done>dash.ado wrote canonical per-y connect and cmissing values, rewrote a connected scatter's type, refused and noted as twoway does, and named only the residuals.</done>
</task>

<task type="auto" id="40-05">
  <name>Add the join helpers and serve them</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Apply TR-40.5 (`_dash_join_vertices` and `_dash_join_glyph` as module functions, each with a docstring citing E4's rules, the null-row-id rule and the 3n-2 bound) and, in the same edit, TR-40.13 (`"_dash_join_glyph", "_dash_join_vertices",` on one line directly after `"_dash_sort_cols_named", "_dash_take_sort_columns",`). Do not edit `_generate_app_source`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_connect_options.py -q -n0 -p no:cacheprovider -k "TestTheVertices or TestTheJoinGlyph or TestTheServedCopy or TestHandWrittenSpecs"` passes; `python3 -m pytest "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" "test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads" -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>One pure vertex rule and one glyph helper existed in both modes.</done>
</task>

<task type="auto" id="40-06">
  <name>Draw lines through the join helper</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Apply TR-40.6: `map_line` (keep rows under `cmissing n`, one `_dash_join_glyph` call with the hover tool), `map_rline` per bound, `map_connected`'s `marker_view` keyword, `map_scatteri` under `connect`. Leave `map_tsline`, `map_tsrline` and `map_rconnected` alone unless a `TestCmissingNo` case shows one strips the keys; then forward them and say so in the commit body. Do not edit `_join_order`, `_carry_cols` or `_apply_line_opts`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_connect_options.py -q -n 6 -p no:cacheprovider -k "TestScatterConnectIsConnected or TestStairsteps or TestAscendingBreaks or TestCmissingNo or TestConnectNone or TestStylelistsPerY"` passes in both modes; `python3 -m pytest test/test_join_order.py test/test_help_claims_8.py test/test_glyphs.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>Every line type drew twoway's connect styles and cmissing breaks with each observation's tooltip kept.</done>
</task>

<task type="auto" id="40-07">
  <name>Draw fits and function through it</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Apply TR-40.7 (every fit line and `_empty_fit_line` through `_dash_join_glyph`; the ci bands through `varea_step` where the fixture's F band paths are stepped), TR-40.8 (`map_function` bridges by default, breaks under `cmissing n`) and TR-40.9 (kdensity's agg config `join`). Keep S26's disposition note in `map_function` as it is.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_connect_options.py -q -n 6 -p no:cacheprovider -k "TestFitsHonourConnect or TestFunctionBridgesByDefault"` passes; `python3 -m pytest test/test_phase4_plots.py test/test_statistical_layers.py test/test_function_points.py -q -n 6 -p no:cacheprovider` reports 0 failed (each file that exists).]]></verify>
  <done>Every fit took each connect style in both modes and function bridged gaps as twoway does.</done>
</task>

<task type="auto" id="40-08">
  <name>Keep link selection on connected markers</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Warn in the task log that `_make_figure_body` is CRITICAL (4 impacted, 8 processes) and that S40 is batch 14's only editor (R12). Apply TR-40.10: the connected branch computing `_mk_view` beside the scatter branch (:30604), and `marker_view=None` on `DashRenderer._add_glyph` (30722) and `_dash_add_glyph` (28955), forwarded to connected only. Edit nothing else in `_make_figure_body`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_connect_options.py -q -n0 -p no:cacheprovider -k TestLinkedConnectedMarkers` passes under node; `python3 -m pytest test/test_link_missing.py test/test_linked_brushing.py test/test_mode_parity.py -q -n 6 -p no:cacheprovider` reports 0 failed (each file that exists; `grep -l _linked_scatter_view test/*.py` names the rest, run too).]]></verify>
  <done>A linked connected layer with a missing value showed the link selection on its markers while its line kept its breaks.</done>
</task>

<task type="auto" id="40-09">
  <name>Rebuild breaks and stairs after moves</name>
  <files>dash_render.py, test/test_varlist_expansion.py</files>
  <action><![CDATA[
    Warn in the task log that `_build_filter_widgets` is CRITICAL (12 impacted) and S40 its only batch-14 editor. Apply TR-40.11 (`dash_join_rebuild` beside `dash_spacing`, the derived-loop call before `_dsrcs[_di].data = _nd`, the kdensity branch) and TR-40.12 (`derived_join_json` beside the derived lists, set only when some entry exists). Leave the axis finisher at the end of `_FILTER_JS` untouched (R11). If 40-01 found `_SINGLE_Y_BASELINE_SHA256` moving, re-derive it in `test/test_varlist_expansion.py` with `# <old> -> <new>: P1.8a _FILTER_JS gained dash_join_rebuild` (R10).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_connect_options.py -q -n 6 -p no:cacheprovider -k "TestAfterASavedMove or TestAfterAServedMove or TestTheJsTwin"` passes with no skip; `python3 -m pytest test/test_saved_filter_layers.py test/test_filter_exclude.py test/test_kpi_brush.py test/test_varlist_expansion.py -q -n 6 -p no:cacheprovider` reports 0 failed (each file that exists).]]></verify>
  <done>Saved filter moves kept missing-value breaks as NaN and rebuilt ascending breaks and stairs, kdensity included, without touching KPI sums.</done>
</task>

<task type="auto" id="40-10">
  <name>Flip the unsupported-report pins</name>
  <files>test/test_unsupported_report_is_true.py, test/test_help_claims_8.cscript</files>
  <action><![CDATA[
    Re-measure E5's pins on this tree, then flip them in place, each with a comment "Flipped (WP-30 P1.8a): <old> was wrong because dash draws connect()/cmissing() as twoway does (connect_truth.json)": PLOT_VALUES `cmissing` to `("n", "y", "area")` and `connect` to `("l", "J", "rarea")`; `cmissings` into `ALIASES`; the declared-plot count to the measured value with `# <old> -> <new>: P1.8a cmissings() declared` (R10). In HC8-02 move `cmissing`, `connect` and `sort` from `p_names` to S37's `p_honoured` list and correct its counts. Leave `recast` (:137 at c96facd) untouched. Write one `Flipped:` line per node to `$S/40-flips.txt`. Delete no test.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_unsupported_report_is_true.py test/test_help_claims_8.py test/test_help_conformance.py -q -n 6 -p no:cacheprovider` reports 0 failed; `test_help_claims_8.cscript` through the driver prints `HC8-02 PASS`.]]></verify>
  <done>The pins that asserted connect() and cmissing() changed nothing now asserted where they stay named, with their reasons recorded.</done>
</task>

<task type="auto" id="40-11">
  <name>Move the stylelist key pins</name>
  <files>test/test_stylelists.py, test/test_varlist_expansion.cscript</files>
  <action><![CDATA[
    Add `connect` and `cmissing` to `test_stylelists.py`'s `_STYLE_KEYS` and drop them from `_NOT_YET`; set SL-01's word count of `_dash_stylelist_keys()` to the measured value with a `Flipped (WP-30 P1.8a)` comment. Append the two `Flipped:` lines to `$S/40-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_stylelists.py -q -n0 -p no:cacheprovider` passes; `test_varlist_expansion.cscript` through the driver prints `SL-01 PASS` and no FAIL.]]></verify>
  <done>S11's key-list pins counted connect and cmissing as style lists.</done>
</task>

<task type="auto" id="40-12">
  <name>Register the new functions and programs</name>
  <files>test/function_test_map.py, test/program_coverage_map.py</files>
  <action><![CDATA[
    Apply TR-40.14 under S01's `# WP-30 S40 (P1.8a): connect() and cmissing() (P1.8 part a)` anchors, alphabetically.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_function_test_map.py test/test_program_coverage_map.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>Both registries named a test for every function and program the section added.</done>
</task>

<task type="auto" id="40-13">
  <name>Document connect and cmissing in help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    Apply TR-40.15: the new Plot types paragraph after `{ul:Join order.}`, the Unsupported "Not drawn" sentence for the residuals, the cl paragraph and the sort sentence. Find each place by its text. Every new or changed line is at most 79 characters; no tool or vendor name.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_connect_options.py::TestTheHelp test/test_help_conformance.py test/test_help_claims_8.py test/test_help_claims_1.py -q -n 6 -p no:cacheprovider` reports 0 failed; `grep -c "use the {cmd:connected} plot type" "$WT/dash.sthlp"` prints 0.]]></verify>
  <done>The help documented every connect style, cmissing(), the function bridge and the named residuals.</done>
</task>

<task type="auto" id="40-14">
  <name>Close the entry and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Read the title as `WP30_OPEN["P1.8a"]`. Close that BUGS.md entry in place (`- [x]`) with "Notes: BUGS.md Resolution", today's date as `ddmonyyyy`. Delete the `"P1.8a"` key line of `WP30_OPEN`. Replace both `<!-- WP-30 P1.8a -->` markers in place with "Notes: CHANGELOG lines". Run `test_tracking_documents.py test_cscript_hygiene.py test_fixtures_are_committed.py test_connect_options.py test_mode_parity.py` with `-n 6`, the S40 block and both area scripts through the driver; `git -C "$WT" merge --no-edit main` (expect `Already up to date.`); one full run `"$S/full_suite_queue.sh" "$WT" "$S/40-full.log"` in the background, read when `exit=` appears (E6 for the known flaky tests). Stage exactly `$S/40-files.txt`'s files plus these three, with `git add -f test/fixtures/connect_truth.json`; check `git -C "$WT" diff --cached --name-only` equals that list (G6). Write `$S/40-message.txt` (Notes: commit message), check G7, confirm the branch, commit, check G7 again, and report the sha and message to the merger.
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/40-full.log"` shows 0 failed and `exit=0`; `grep -c '<!-- WP-30 P1.8a -->' "$WT/CHANGELOG.md"` prints 0; `grep -c '^    "P1.8a": "' "$WT/test/test_tracking_documents.py"` prints 0; `git -C "$WT" log -1 --format=%s` ends `(WP-30 P1.8a)`; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Entry P1.8a was closed naming existing tests, both markers carried the measured old and new behaviour, and one green commit on wp30-s40 was ready for the merger.</done>
</task>

## Section completion criteria

- `connect()` (every twoway spelling) and `cmissing()` are drawn on scatter, the line family, scatteri and the fits as `connect_truth.json` records, in the saved page and the served app, before and after saved and served filter moves; stairs keep every observation's tooltip; `c(i)` hides the line and keeps the key.
- `function` bridges by default and breaks under `cmissing(n)`.
- dash refuses and notes as twoway does (CM-01..CM-12), is silent on same-picture types, and names only P2.42/P2.43's cases.
- `_dash_join_vertices`, `_dash_join_glyph`, `_dash_connect_opt` and `_dash_connect_canon` exist, are mapped, and the two Python helpers travel to the served app; `dash_join_rebuild` agrees with its twin.
- The fixture is generated by its extractor, stamped, committed with `-f` and read by tests.
- Every pinned node is flipped with its reason; none is deleted.
- One green commit `(WP-30 P1.8a)` exists on `wp30-s40`; it closes the entry, deletes its key and replaces both markers.

## Notes

- **Q-40.1, resolved by the review (no maintainer question).** R9's S40 row and the manifest name `test_unsupported_report_is_true.py:137`. At HEAD that row is `"recast": ("line", "area", "scatter")`, and it pins `recast()`, which is P1.8b. S40 does not honour `recast()`, so the row stays true and green here, and 40-10 leaves it alone. S45 already flips it (section-45 :130, :306, "S40 leaves it to S45"). Moving it in S40 would either make it false or pre-empt S45's flip, against R9 ("a test that pins today's wrong behaviour is flipped in the fix commit"). Cross-file fix for the orchestrator, recorded in `review-notes/g06.md`: index.md R9's S40 row becomes ":95/:99 and HC8-02's cmissing, connect and sort; :137 (recast) is S45's". The manifest's S40 scope reads the same way under index precedence.
- **IR-3 applies:** the manifest's "draw as Step" and "hover on stairsteps is a residual" are replaced by pre-expanded stair vertices on a Line; the residual is struck.
- **R10 deviation:** `CMISSINGS` moves the declared-plot count (:607 at `c96facd`) by +1; R10's table lists no batch-14 mover for it, so it cannot conflict. The plot pending count (:240) and the two help-conformance counts do not move (the pending lines stay, per the `sort` precedent). The merger re-derives the single-y digest if 40-09 moved it.
- **Ordering difference (documented, not fixed):** twoway raises an unknown `cmissing()` r(101) at draw time, after every layer parsed, and accepts it under `nodraw`; dash refuses at the layer's parse, whatever `nodraw`, because it always builds the page. A command with a later layer's syntax error gets dash's r(101) where twoway gives r(198).
- **Shared lines with S39 (context conflicts only, R6):** S39 also adds a Mata function, so both touch dash.ado's `_needed` list (:237-256) and dash_parse.mata's header index; each adds its own names on its own line, and the merger keeps both.
- **A linked `connected` layer** (not only a rewritten scatter) gains link selection on its markers with a missing value, as dash.sthlp:1154-1157 already claims.
- **python_exec hazard.** Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`; the extractor and CM-20..CM-24 then fail or SKIP. Check after each slot run; a SKIP is not a pass.
- **Merge rules.** R1: CM-01..CM-12 as one run after S38's RS run, before `// Summary`; the S40 block and `_s40_paths` in their places. R2: one copy-list line at S40's anchor; map entries under S40's anchors. R3: Plot types (S40's) and the Unsupported entries (pending mover). R4/R5: the two `P1.8a` markers, the entry and its key. R6: `version 19` in `_dash_connect_opt`; one Mata function with header and `_needed` entries; S11's key list extended. R7: one new fixture and extractor. R8: two CORPUS cases appended. R9: E5's flips. R10: as above. R12: S40 is batch 14's only editor of `_make_figure_body`, `_FILTER_JS` and `_build_filter_widgets`. R13: the merger's detect-changes must name `_dash_join_vertices`, `_dash_join_glyph`, `_dash_add_glyph`, `DashRenderer._add_glyph`, `DashRenderer._make_figure_body`, `DashRenderer._build_filter_widgets`, `_FILTER_JS`, `GlyphMapper.map_line`, `map_rline`, `map_connected`, `map_scatteri`, `map_function`, the fit mappers, `_empty_fit_line`, `_glyph_layer_lines` and test symbols only.
- **Commit message.** Subject as in "Commit boundary". Body in order: `$S/40-P1.8a-failure.txt`; the measured defect (Overview's block); what changed and where (TR-40.1-TR-40.15, both modes) and the threats closed (TR-40.16); one `Regression: test/test_connect_options.py::<Class>::<test> -- failed at <base sha> with <text>` per regression node (cscripts as `test/test_twoway_option_parity.cscript CM-01`, `test/test_wp30_truth.cscript CM-20`); the lines of `$S/40-flips.txt`, e.g. `Flipped: test/test_help_claims_8.cscript HC8-02 -- connect(), cmissing() and sort named in the note was wrong because a scatter given connect() is drawn as twoway's connected plot`; `Fixture: test/fixtures/connect_truth.json (scripts/extract_connect_truth.do)`; `BUGS.md: "<WP30_OPEN["P1.8a"] title>" (closed)`. No tool or vendor name (G7).
- **BUGS.md Resolution** (one line, in place):

  ```
  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.8a). connect() and cmissing() are read as twoway reads them (dash.ado _dash_connect_opt with Mata _dash_connect_canon: twoway's spellings, per-y lists through S11's splitter, cmissings(), the rightmost copy; a misplaced .. refused r(198) and an unknown cmissing() r(101) in twoway's words; an unknown connect name drawn direct with twoway's note), a scatter given connect() is twoway's connected type (its line, cl options and sort), and every line, scatteri and fit draws through one rule (dash_render.py _dash_join_vertices, _dash_join_glyph: direct, ascending breaks, stairs as a Line over pre-expanded vertices so tooltips stay, none hiding the line; cmissing(n) breaks at missing values; function bridges by default), in the saved page and the served app, before and after filter moves (_FILTER_JS dash_join_rebuild, _build_filter_widgets derived_join_json, kdensity's recompute); a linked connected layer keeps link selection on its markers. Pinned by test/test_connect_options.py::TestStairsteps::test_vertices_and_hover, test/test_connect_options.py::TestCmissingNo::test_breaks, test/test_connect_options.py::TestAfterASavedMove::test_a_break_stays_a_break, test/test_connect_options.py::TestFunctionBridgesByDefault::test_bridge_and_break, test/test_twoway_option_parity.cscript CM-01, test/test_wp30_truth.cscript CM-20; fixture test/fixtures/connect_truth.json. Residual, deferred (WP-30): cmissing(n) on area and rarea and connect() on rarea are named, not drawn (P2.42); cmissing(n) at missing points lowess, fpfit, lpoly, mspline and mband generate is named, not drawn (P2.43); an unknown cmissing() is refused at the layer's parse, also under nodraw, where twoway refuses at draw time.
  ```
- **CHANGELOG lines** (each replaces its marker in place; the `###` lines only say which list):

  ```
  ### Results that change
  - `connect()` and `cmissing()` are drawn, in both modes and after filter moves (both were named in the note and ignored): `dash scatter y x, c(l)` drew markers only and now draws twoway's connected plot, its `clcolor()`, `clwidth()` and `sort` honoured; `c(J)`/`c(stairstep)` and `c(stepstair)` drew a straight line and now draw stairs, every point keeping its tooltip; `c(L)` now breaks the line wherever x drops; `c(i)` hides the line and keeps the key; `cmissing(n)` drew a bridged line and now breaks it at each missing value, on line, connected, tsline, rline, rconnected, tsrline, scatteri and a scatter given `connect()`; the fits take every `connect()` style; per-y lists and `cmissings()` are read as twoway reads them. `function y=sqrt(x^2-1), range(-2 2)` drew a gap over the missing middle and now bridges it as twoway does (`cmissing(n)` breaks it). A linked connected layer with a missing value now shows the link selection on its markers. (WP-30, P1.8a)

  ### Changed behaviour (may need your do-files changed)
  - `connect()` and `cmissing()` are checked as twoway checks them (each was rc 0 with a note before): a misplaced `..` is refused (`connect(l .. J):  invalid syntax`, `cmissings(n .. y):  invalid syntax`, r(198)); an unknown `cmissing()` value is refused on the types twoway refuses it on, after twoway's two notes (` not allowed`, r(101)), and noted elsewhere; an unknown `connect()` name prints twoway's note and draws direct; `clwidth()` out of range on a scatter given `connect()` is refused (`gm_linewidth must be between 0.000 and  1.0e+04`, r(198)). (WP-30, P1.8a)
  ```
- **Notes for the closeout (S58; A145).**
  - **GAPS2.md** A4 (:175-195; A4-l, A4-m), B12 (:476-489; B12-c, B12-d), G15 (:1484; G15-a): connect/cmissing parts closed by `<sha>`; A4 and B12 stay partly open until S45 (recast).
  - **REMAINING.md** §2 (REM-§2-S06-connect) and 05-04 (REM-S05-04-connect); **TWOWAY_COVERAGE_AUDIT.md** AUDIT-09 and AUDIT-11 (with S45); **DROPIN-REMAINING.md:98** (P1.8): "connect()/cmissing() closed by <sha> (WP-30 S40); recast() by S45"; **ROADMAP.md:1567** (`connect(bogus)` noted, pending) closed.
  - **P2 rows:** P2.42 and P2.43 with this section's measured cases; the stairstep-hover residual is struck (IR-3).
  - **Stale data, not tests:** `test/fixtures/rejected_options.json` `connect` entry (:4268), `test/fixtures/value_truth.json` `connect_1..3` (:2742-2764), `scripts/regen_option_surface.py:102` (`cmissing`/`connect` IGNORE; IR-7).
  - **AGENTS.md invariant:** "every connecting line is drawn through `_dash_join_glyph` from `_dash_join_vertices`' index pairs; synthetic rows carry a null row id; `dash_join_rebuild` is its saved-page twin."
  - **Unverified:** Stata 14-18.5 (M2); the lfitci/qfitci/fpfitci band under `c(J)` beyond the fixture's auto probes.
