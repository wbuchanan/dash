# Section 45: recast() (P1.8 part b)

> Part of: WP-30 · Items: P1.8 (entry `P1.8b`; GAPS2-A4-n, GAPS2-B12-b, AUDIT-12; AUDIT-09, AUDIT-11 and GAPS2-G15-a recorded closed together with S40) · Risk: yellow · Batch: 16 (merge order S45, S46, S47) · Depends on: 19, 24, 40 · Blocks: 49, 57 · Tasks: 10, 1 commit · Case prefix: RC

## Review amendments

- Judged (Q-45.1, as the orchestrator asked): D-45a departs from register A60 ("keeps `type`, writes `recast`"). The departure is sound. A60's purpose, the key and titles from the typed type, holds through `recast_from`. S40 already rewrites `type`. Every type-keyed site then sees the drawn type with no edit, and the literal form needs both render loops' routing, held by S47 and S46 in this batch (R12). Kept, and marked in Notes as "Maintainer question (ratify)" with the reason and a recommendation to ratify, plus what a strike changes.
- Fixed (major): `$S` was this review session's scratchpad and shared by S45, S46 and S47 (parallel, same log names and slot directory). `$S` is now `<scratch>/s45`; the batch base and queue script are read from `<scratch>`.
- Fixed (major): 45-03's verify asked RC-01, RC-02 and RC-05 to pass, but `_dash_recast_opt` is first called by 45-04. 45-03 now verifies the abbreviation rows, the program's presence and the coverage map; 45-04 already checks RC-01..RC-13.
- Fixed (minor): TR-45.6 passed `order=None` to every target, but `map_scatter` (:9744) takes no `order`; it is now passed only for `_DASH_JOIN_TYPES`, as `_dash_add_glyph` does. The truth block states TR-01.10's form and its exact header (`recast()`).
- Checked: `RECAST(string)` at dash.ado:941, the pending line :1098 and the return :1183; `TYpe` collides with neither `TItle` nor `TEXT`; `_dash_glyph_dispatch` (:28501) returns `(dispatch, range_dispatch)`; the pins `test_unsupported_report_is_true.py:137/:240/:607` (48, 169) are as quoted; `_dash_legend_key` (:26925) keys by `type`, so `recast_from` first is the one change it needs (`_dash_axis_labels` keys only univariate types, which a recast never rewrites). No function is shared with S46 or S47; S45 edits no one-editor symbol.
- Rejected: the manifest's "per-y lists through S11's splitter". twoway reads one value for every y (E7, measured), so M1 binds D-45b.
- The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:98 (P1.8) reads: "`connect()`, `cmissing()` and `recast()` are not honoured." S40 (batch 14) closes the first two; this section closes `recast()`. Measured at `c96facd` (research `.ultraplan/wp30/research/p1-08.md` §1 e, g, h):

```
dash scatter y x, recast(line)        -> rc 0, "dash: ignoring unsupported option(s): recast()"; map_scatter draws Scatter(n=6)
dash kdensity x, recast(area)         -> rc 0, the same note; a Line is drawn
dash lfit y x, recast(scatter)        -> rc 0, the same note; a Line is drawn
dash lfitci y x, recast(line)         -> rc 0 and a note      (twoway: "recastas() option not allowed", r(198))
dash scatter y x, recastas(line)      -> "ignoring unsupported option(s): recastas()"   (twoway: a line)
dash scatter y x, type(line)          -> "ignoring unsupported option(s): type()"       (twoway: a line)
```

twoway draws a recast layer as the target type: within a group the whole look changes (`scatter y x, recast(line)` is byte-equal to `line y x`), derived types keep their computation and are drawn as the target (`kdensity x, recast(area)` is an area polygon, `lfit y x, recast(scatter)` gives markers), a range type cast to a yx name draws its first bound, and an out-of-group or unknown name falls back with two notes.

**After this section**, in the saved page and the served app, before and after every filter move:
- base yx, range, pc and time-series layers are drawn as the recast type, with twoway's spellings, its precedence (`recast()`/`recastas()` over `type()`), its fallbacks and its two notes (a yx source falls back to scatter, a range source to rspike, a pc source to pcspike, `function` to its own line), and a range type cast to a yx name draws its first bound; `dot` ignores `recast()` silently;
- fits, smoothers, `kdensity`, `function`, `histogram` and `scatteri` keep their computation and are drawn as the target (scatter, line, connected, area, bar, spike, dropline, dot) through one draw-as helper, styled on the target's scheme chain (S24), `recast(bar)` one x unit wide (S14), the key keeping the series label twoway gives (S19, A60);
- `recast()`, `recastas()` and `type()` on lfitci, qfitci, lpolyci and fpfitci are refused r(198) in twoway's words (M5);
- the only forms still named are `recast()` on `pci`/`pcarrowi` and a range or unknown target on `histogram` (P2.44).

**Why one section.** P1.8 was split at the type rewrite (A138): S40 owns `connect()`/`cmissing()` and the join helper, S45 owns the type a layer is drawn as. Both write the drawn type into the plot object (S40 for scatter plus connect, S45 for recast), and S45 runs first, as twoway sets `.viewtype` before `_maybe_override_type` (E8).

**Section decisions (this file; each cites its evidence).**
- **D-45a** The JSON `type` is the drawn type for base, range, pc and ts recasts, with the typed type kept as `recast_from`; derived layers keep `type` and write `options.recast` (Notes, Q-45.1).
- **D-45b** `recast()` is one value for every y; a value of one distinct word repeated is that word; any other multi-word value is an unknown name (E7, M1).
- **D-45c** Classes, spellings and fallbacks are Stata's four type classes (E7): yxtype → scatter, y2xtype → rspike, yxyxtype → pcspike, functiontype → `function`'s own line.
- **D-45d** A derived source given a range or unknown name takes the yxtype fallback with the notes (measured), except histogram, whose range targets and fallback stay named (P2.44).
- **D-45e** `dot` ignores `recast()` silently (M6, measured); pci and pcarrowi keep `recast()` named (register A22 "valid option dash cannot draw is named").
- **D-45f** `recast()`/`recastas()` beat `type()` in either order; each is rightmost among its own copies (E7).
- **D-45g** tsline and tsrline recasts join in time order, as twoway's `sort(t)` (twoway_tsline_parse.class:32).
- **D-45h** `rec()`, `reca()` and `recas()` are refused as twoway refuses them (M5).
- **D-45i** The recast is resolved before S40's connect override, which judges the drawn type (E8).
- **D-45j** The judge type of each later step (Notes).

**Test order and commit rule (rule 7).** One cycle on `wp30-s45`: 45-01 and 45-02 write the fixture and every regression test and run them against the unmodified batch-16 base, saving `$S/45-P1.8b-failure.txt` (no commit); 45-03 to 45-09 fix, flip and document; 45-10 closes the entry and makes the one commit. No test-only commit exists, and no commit is red.

## Risk: [yellow] — a type rewrite in the parser that every later step reads, eleven mapper tails, and a reconciliation of A60 that needs the maintainer's ratification

**Why.**
- Every step of `_dash_process_segment` after the option parse keys on `ptype` (E2): the folds, validation, sort, sample checks, the JSON's `type` and `vfields`, and `c_local plottype_out`, which S49 reads for its horizontal refusals.
- The eleven derived mappers are UNKNOWN to the index: reached only through the `_dash_glyph_dispatch` dict (dash_render.py:28501) or by name (`map_scatteri`, `map_function` in both render loops; served template :34947-34955), confirmed by grep. Their effective risk is the dispatch's, LOW (4 impacted).
- `_stale_cue_args` and `_collect_frozen_layers` are CRITICAL (6 and 12 impacted; research critic C4). S45 does not edit them, but a recast fit must keep its frozen tag.
- `_dash_layer_series` (S19's helper) is read by keys and titles in both modes; S45 adds one lookup.
- Every Stata program is UNKNOWN (not indexed): `_dash_parse_plot_opts` (897), `_dash_process_segment` (3454), `_dash_fold_bw` (1545), `_dash_fold_cl` (1654), `_dash_fold_typed` (1749), `_dash_sort_opt` (1843), `_dash_validate_opts` (2577), `_dash_plot_opts_to_json` (3131), `_dash_opts_repeats` (6110).

**Risk factors.**
1. A60 says S45 "keeps `type`, writes `recast`"; the manifest says the base and range types are "rewritten". Keeping the typed name in `type` would need every type-routing site of both render loops changed (`_make_figure_body` :30551/:30604/:30617 and the served `_dash_draw_layer`), which R12 reserves to S47 and S46 in this batch.
2. `recast()` is not a per-y list in twoway (measured, E7), though the manifest scope says "per-y lists through S11's splitter".
3. A range type cast to a yx name changes the variable fields (`yvar1`/`yvar2` to `yvar`).
4. tsline and tsrline are line/rline views with `sort(t)` (twoway_tsline_parse.class:32); a plain rewrite would join in data order.
5. A recast derived layer drawn through a base mapper can gain a HoverTool labelled `y`/`x` and lose the JS recompute of its source.
6. S40's override writes `"type":"connected"` per y on a scatter with `connect()`; done before the recast, it would be undone.

**Mitigation.**
1. D-45a: the JSON `type` is the drawn type (as S40 writes it), the typed one is kept as `recast_from`, and `_dash_layer_series` keys by `recast_from` first, so the label rule of A60 holds. Maintainer question Q-45.1 (Notes) asks for ratification, with the reviewer's recommendation to ratify.
2. D-45b follows the measurement (M1); RC-08 pins it against live twoway.
3. `_dash_recast_opt` returns the first bound in `s(_recast_y)`, and the vfields block writes it as `yvar` (TR-45.4).
4. D-45g: a ts source's drawn type joins in time order through `sortvars` (TR-45.4).
5. `_dash_draw_xy_as` removes any HoverTool that names only its renderers, and carries `_dash_agg_source` and the frozen tag to the drawn renderers (TR-45.6); `TestRecastAfterAMove` runs both modes, the saved one under node.
6. `_dash_recast_opt` runs before S40's `_dash_connect_opt` and hands it the drawn type (D-45i); RC-12.

## Dependencies

- **Depends on: 19, 24, 40.**
  - S19 (batch 7): `_dash_layer_series` and `_dash_legend_key(s)` key the series label by the plot's `type` (S19 Notes "Key by `type`"); S45 makes them read `recast_from` first.
  - S24 (batch 8): scheme opacity and colour at construction through `GlyphMapper._scheme_alpha_kw` and `_cycle_for`; "a recast layer passes its new type to `_scheme_alpha_kw` and `_cycle_for`" (section-24 Notes).
  - S40 (batch 14): `_dash_connect_opt "`ptype'" <nser>` right after `_dash_opts_repeats` (TR-40.4), its `_cn_ptype` (connected for a scatter with any connect element) handed to `_dash_fold_bw`, `_dash_validate_opts`, `_dash_stylelist_check`, `_dash_fold_typed` and `_dash_sort_opt`, the per-y type `word _yi of _cn_types` at the assembly line, the module-level `_dash_join_vertices`/`_dash_join_glyph` at the end of the line family and the fits, and HC8-02 with `cmissing`, `connect` and `sort` moved to S37's `p_honoured` list and `recast` left named for S45 (S40 Q-40.1).
  - S01 provides the open entry `P1.8b`, its `WP30_OPEN` key, the markers `<!-- WP-30 P1.8b -->` in the WP-30 group of `### Results that change` and at the end of `### Changed behaviour (may need your do-files changed)`, the S45 stub of `test/test_wp30_truth.cscript` and the map anchors `# WP-30 S45 (P1.8b): recast() (P1.8 part b)`.
  - Landed before and read here: S02 (extractor stanza), S06 (notes as `(note: …)`), S11 (`string asis` lists), S14 (`GlyphMapper._bar_extent`, one x unit), S21 (`_dash_tag_hull_roles` reads the drawn `ptype`).
- **Blocks: 49, 57.** S49 judges `horizontal`'s refusals on the type `c_local plottype_out` returns, which is the drawn type after S45 (register P1.9.2, IR-13). S57 audits the served move path, which a recast layer reaches through the ordinary mappers.
- **Parallel batch: 16**, merge order S45, S46, S47.
- **Can run with:** S46 edits `_generate_app_source`, the launcher, `_dash_serve_spec`/`_dash_serve`/`_dash_build`; S47 edits S21's finishers, `_dash_plot_margin`, the scheme extractor and files. S45 edits none of them, and neither partner edits `_dash_process_segment`, the plot parser or a mapper.

## Evidence

Anchors are at `c96facd` (dash.ado 8,487 lines, dash_render.py 37,689, dash.sthlp 3,822). S19, S24, S40 and others move them before batch 16; the executor re-finds each by symbol at `batch-16-base`.

### E1. Declared, pending, serialised, never read (dash.ado)

`_dash_parse_plot_opts` (897) declares `CMISSing(string) RECAST(string) Connect(string)` (:941), puts `recast` on the pending list (:1098) and returns it (:1183); `_dash_plot_opts_to_json` writes it verbatim (key list :3150). `recastas()` and `type()` are not declared and reach the catch-all.

```stata
1098    if `: length local recast' local _dash_pending `"`_dash_pending' recast"'
1183    sreturn local recast           : copy local recast
```

### E2. The order of the segment's steps (dash.ado `_dash_process_segment`)

The varlist is read by family before the options (:3548-3880; tsline sets `xvar` to `_dta[_TStvar]`, :3801-3826). The options then run (:4088-4137): `_dash_parse_plot_opts`, `_dash_refuse_unbound`, `_dash_refuse_foreign`, `_dash_opts_repeats`, then (S40) `_dash_connect_opt`, then `_dash_fold_bw "`ptype'"` (:4121), `_dash_validate_opts` (:4125), `_dash_fold_typed` (:4134), `_dash_sort_opt` (:4137). The JSON is assembled by family (:4289-4370):

```stata
4296    else if `: list ptype in _pt_range' {
4300        local vfields `""yvar1":"`_jy1'","yvar2":"`_jy2'","xvar":"`_jxv'""'
...
4364            local seg_json `"`seg_json'{"type":"`ptype'",`vfields',"options":`_opts_json',...
4372    c_local `plottype_out' "`ptype'"
```

`_dash_sort_opt` writes `s(sortvars)` only for `line connected area rline rarea rconnected` (:1851-1883).

### E3. The renderer dispatches by the plot's `type` in both modes

`_dash_add_glyph` (28955) looks the type up in `_dash_glyph_dispatch` (28501-28550: 22 yx and derived names, 9 range names) and passes `order` only for `_DASH_JOIN_TYPES`. The saved loop routes by type in `_make_figure_body` (:30551, :30604 `_linked_scatter_view` for `ptype == "scatter"`, :30617 frozen tags from `_DASH_COMPUTED_ONLY_TYPES`, 1082). The served `_dash_draw_layer` (template from :34922) branches `scatteri`, `pci`, `pcarrowi`, `function` by name, then pc, range, else. Neither loop reads `options.recast`.

### E4. The derived mappers' tails (dash_render.py)

map_lfit (10840), map_qfit (10921), map_lowess (11230), map_lpoly (11678), map_fpfit (12249), map_histogram (12451), map_kdensity (12779), map_scatteri (13627), map_mspline (14636), map_mband (14785), map_function (14854). Each computes points and ends in one glyph call; map_lfit's at :10912-10918:

```python
10912        fit_source = ColumnDataSource({"x": x_fit, "y": y_fit})
10913        r = fig.line(x="x", y="y", source=fit_source,
10914                     line_color=self.scheme.default_color(color_idx, "line"),
...
10918        self._apply_line_opts(r, options)
```

S40 replaces these line calls by its module-level `_dash_join_glyph(...)`. map_kdensity tags its renderer for the saved page's recompute: `r._dash_agg_source = kd_source` (:12897).

### E5. Pinned tests

- `test/test_unsupported_report_is_true.py:137` `"recast": ("line", "area", "scatter")` (PLOT_VALUES; S40 leaves it to S45, S40 Q-40.1); `:240` plot pending 48; `:607` declared plot 169 (R10 movers).
- `test/test_help_claims_8.cscript:392-393` HC8-02 lists `recast(line)` on scatter in its composite list (S40 flips HC8-02 for connect/cmissing; S45 splits the recast part).
- `test/test_abbreviations.cscript:240` lists `recast` among DASH_PLOT_KEYS.
- dash.sthlp:3728-3735 "Not drawn" (`{opt recast(plottype)} -- name the plot type you want directly.`).

### E6. Blast radius (`gitnexus impact <symbol> -d upstream -r dash`, index at `c96facd`, from the research)

| Symbol | Risk | Note |
|---|---|---|
| `_dash_glyph_dispatch` | LOW (4) | read by the draw-as helper; not edited |
| `_dash_add_glyph` | LOW (3) | not edited |
| the 11 derived mappers | UNKNOWN | dispatch dict / by name; grep-confirmed |
| `_stale_cue_args`, `_collect_frozen_layers` | CRITICAL (6, 12) | not edited; RC tests pin the tag |
| `_dash_layer_series`, `_dash_legend_key` | not in research; run at 16.0 | one lookup added |
| dash.ado programs | UNKNOWN | grep-confirmed callers in Risk |

### E7. twoway's truth (StataNow 19.5; research §2 plus this pass's probes)

Research §2 (measured): within-group recasts equal the target type; derived types drawn as the target; `rarea…, recast(rline)` two lines; out-of-group names give `(note:  named style rline not found in class yxtype, default attributes used)` and `(note:  yxtype not found in scheme, default attributes used)`, rc 0; fallbacks yx → scatter, range → rspike, pc → pcspike, `function` its own line, `dot` all 10 targets the dot base; `rline y y2 x, recast(line)` one path of y; `recastas()`/`type()` synonyms; the ci types refuse.

This pass (`s45probe/rc2-rc5.do` through `scripts/stata_slot.sh`, 03oct2026; data x 1..8, y, y2 = y+3, tsset t; SVG element counts):

```
scatter y y2 x, recast(line)              paths=2 circles=0   (both y recast: not a per-y list)
scatter y y2 x, recast(line scatter)      2x the two notes ("named style scatterline ..."), circles=36 (scatter)
scatter y x, recast(scatter line)         the two notes, scatter
scatter y y2 x, recast(line line)         paths=2, no note
scatter y y2 x, recast(line ..)           notes naming "..", scatter;  recast(. line): notes naming ".", scatter
scatter y x, recast(l) / recast(LINE)     notes naming l / LINE, scatter;   recast(li): a line, no note
scatter y x, recast(line) type(bar)       line;  type(bar) recast(line): line;  recastas(bar) recast(line): line
scatter y x, recast(line) recast(bar)     bar (rightmost);  type(line) type(bar): bar
scatter y x, recasta(line)                line;  rec(line): "option rec() not allowed" r(198);  ty(line): line
lfitci y x, recastas(line)                "recastas() option not allowed" r(198)
lfitci y x, type(line)                    "type() option not allowed" r(198)
qfitci/fpfitci/lpolyci y x, recast(...)   "recastas() option not allowed" r(198)
tsline y, recast(connected)               = connected y t (16 circles, 1 path)
scatteri 1 1 2 2 3 1, recast(line)        paths=1 circles=0;  scatteri ..., recast(rline): notes (yxtype), markers
pci 1 1 2 2, recast(pcarrow)              arrows drawn (lines 477 -> 479)
dot y x, recast(line)                     the dot base, no note
function y=x, recast(scatter)             markers;  recast(rline): notes "class functiontype", its own line
lfit y x, recast(rline) / kdensity, recast(rarea) / lowess, recast(rspike)   notes (yxtype), markers
qfit y x, recast(dot)                     a dot plot;  kdensity y, recast(bar): 600 bars;  kdensity, recast(dropline): drops
histogram y, recast(line)                 one path;  recast(scatter): markers;  recast(rline): two lines (P2.44)
histogram y, recast(bogus)                notes "class y2xtype", spikes (the y2xtype fallback)
rline y y2 x, recast(rsc)                 rscatter;  rline ..., recast(rbarm): = rbar;  recast(bogus): notes, rspike
pcspike ..., recast(pcbar) / (pccaps)     pcbarrow / pccapsym;  recast(pcl): notes naming "pcline", pcspike
```

Stata's own classes (`ado/base/style/*type-*.style`, read as text): yxtype {area bar connected dot dropline line scatter spike}; y2xtype {the 8, rarea rbar rbarm rcap rcapsym rconnected rline rscatter rspike}; yxyxtype {pcarrow pcbarrow pccapsym pcscatter pcspike}; functiontype {the 8, function}. twoway_yxview_parse.class:246-247 makes `recastas` the `type`; :320-324 sets `.viewtype` before the connect override (:1080 `_maybe_override_type`).

### E8. The order twoway applies recast and connect

`line y x, recast(scatter) c(l)`: the type is set first (yxview :320-324), then `connect()` turns a scatter view into connected (:1074-1080). S40's override therefore judges the drawn type.

## User stories

- **US-45.1** As a twoway user, I want `scatter y x, recast(line)` and every within-group recast drawn as the target type, so that my do-file's graph looks the same in the dashboard.
- **US-45.2** As a twoway user, I want `kdensity x, recast(area)`, `lfit y x, recast(scatter)` and the other derived recasts drawn as the target, keeping their computation and series label, in both modes and after a filter move.
- **US-45.3** As a twoway user, I want an out-of-group or misspelt recast to fall back and print twoway's notes, so that I see the same message twoway gives.
- **US-45.4** As a twoway user, I want `recast()` on a ci fit refused with twoway's words, so that a do-file that fails in twoway fails here too.
- **US-45.5** As a dashboard publisher, I want the served app and the saved page to draw a recast layer identically before and after a move.

## Business requirements

- **BR-45.1** A base yx, range, pc or time-series layer with `recast()`, `recastas()` or `type()` is drawn exactly as the target type would be drawn with the same variables and options, in both modes (E7).
- **BR-45.2** A range layer recast to a yx name draws its first bound against x; tsline and tsrline recasts join in time order.
- **BR-45.3** A derived layer (lfit, qfit, lowess, lpoly, fpfit, mspline, mband, kdensity, function, histogram, scatteri) keeps its computed points and draws them as the target; `recast(bar)` is one x unit wide; its key reads as the un-recast layer's key; it gains no tooltip it did not have.
- **BR-45.4** Spellings, case, precedence, multi-word values, fallbacks and notes follow E7, the notes in twoway's words.
- **BR-45.5** `recast()`, `recastas()` and `type()` on lfitci, qfitci, lpolyci and fpfitci, and `rec()`/`reca()`/`recas()`, are refused r(198) in twoway's words.
- **BR-45.6** `dot` ignores `recast()` silently; `recast()` on pci and pcarrowi, and a range or unknown target on histogram, are named, not drawn.
- **BR-45.7** After a filter move a recast layer is redrawn as before the move in the served app and recomputed or marked by the stale cue as its un-recast type is on the saved page.

## Technical requirements

### dash.ado

- **TR-45.1 Declarations** (`_dash_parse_plot_opts`, :941). `RECAST(string)` becomes `RECASTas(string)` (twoway's minimum `recast`, E7), and `TYpe(string)` is declared beside it (minimum `ty`, measured). The pending line :1098 is deleted. The returns become `sreturn local recast : copy local recastas` and `sreturn local type : copy local type`. `_dash_plot_opts_to_json`'s key list (:3150) keeps `recast` (the canonical target, written by TR-45.3) and does not gain `type`.
- **TR-45.2 Repeats and precedence.** `_dash_opts_repeats` keeps both options rightmost (its default; the Mata `_dash_rep_unique` list does not name them). `recast()` and `recastas()` are one option (RECASTas), so the rightmost of the two wins; a non-empty `s(recast)` beats `s(type)` in either order (E7 cases 113-115).
- **TR-45.3 `_dash_recast_opt` (new sclass program, after `_dash_sort_opt`'s `end`, `version 19`, header comment).** `args ptype` (the typed type). It:
  1. Reads `v = s(recast)` if non-empty, else `s(type)`; empty → `sreturn local _recast_type "`ptype'"`, exit. An `s(_unknown)` token `rec(`, `reca(` or `recas(` is refused first: `option rec() not allowed`, r(198), naming the spelling as typed through `_dash_say`.
  2. On lfitci, qfitci, lpolyci, fpfitci: refuses r(198) with `recastas() option not allowed` when `s(recast)` is set, else `type() option not allowed` (E7).
  3. On dot: clears `s(recast)`/`s(type)` silently and exits with the typed type.
  4. Splits `v` into words (`tokens()`); one distinct word → that word; more → unknown (D-45b).
  5. Classifies the source: yxtype for scatter, line, connected, area, bar, spike, dropline, tsline, scatteri, lfit, qfit, lowess, lpoly, fpfit, mspline, mband, kdensity; y2xtype for the range types, tsrline and histogram; yxyxtype for pcspike, pccapsym, pcarrow, pcbarrow, pcscatter; functiontype for function; pci and pcarrowi → adds `recast` to `s(_pending)` and exits.
  6. Canonicalises the word by the class's spellings (E7, research §2: yx `sc`→scatter, `li`→line, `co`→connected, `b`→bar, prefixes up to the full name; range `rsc`, `rli`, `rco` likewise; pc `pcar`, `pcbar`, `pcl`→pcline, `pcsp`, `pccaps`, `pcsc`; every other name exact; case-sensitive; `rbarm` → rbar). A name not in the class prints, through S06's Stata note path, `(note:  named style <name> not found in class <class>, default attributes used)` and `(note:  <class> not found in scheme, default attributes used)`, `<name>` being the canonical spelling (`pcline`) or the value as typed, and takes the class fallback: yxtype scatter, y2xtype rspike, yxyxtype pcspike, functiontype function. For histogram a range target or the fallback adds `recast` to `s(_pending)` instead (P2.44) and exits with the typed type.
  7. Returns `s(_recast_type)` (the drawn type), `s(_recast_target)` (the canonical target), `s(_recast_kind)` (`base`, `range2yx`, `ts` or `derived`) and, for `range2yx`, nothing else (the caller holds the varlist).
  For base, range, pc and ts sources the drawn type is the target; for derived sources (the fits, kdensity, function, histogram, scatteri) the drawn type stays the typed type and the target is written as `options.recast`.
- **TR-45.4 The call and the JSON** (`_dash_process_segment`).
  - `local _ptype_typed "`ptype'"` before the option parse. `_dash_recast_opt "`ptype'"` runs directly after `_dash_opts_repeats` and before S40's `_dash_connect_opt`. For base/range/pc/ts kinds `local ptype "`s(_recast_type)'"`.
  - Judge type (D-45j): for base/range/pc/ts kinds S40's `_dash_connect_opt` runs on the drawn `ptype`, and S40's `_cn_ptype` reaches every later step as S40 wired it. For the derived kind `_dash_connect_opt` runs on `s(_recast_target)`; S40's wiring lines are edited so that `_dash_fold_bw` and `_dash_validate_opts` (and the sample checks) take the derived `ptype`, while `_dash_stylelist_check`, `_dash_fold_typed` and `_dash_sort_opt` take `_cn_ptype`; the target written as `options.recast` is `_cn_ptype` (so `lfit …, recast(scatter) c(l)` draws as connected, as twoway's yxview does, E8).
  - `ts` kind: when the drawn type is in `_so_six`, `sreturn local sort1 "`xvar'"` (the time variable) before `_dash_sort_opt`, replacing a user sort (twoway ignores it on tsline, twoway_tsline_parse.class:21-22, :32).
  - `range2yx` kind (a range or tsrline source, a yx target): the vfields block writes the yx form with `yvar` = the first bound (`yvar1`) and `xvar`; `yvar2` is not written.
  - The JSON `type` is the drawn `ptype` (S40's per-y `connected` override is applied on top, judged on it). When it differs from `_ptype_typed`, `,"recast_from":"<_ptype_typed>"` is written after `"type"` in each plot object (both assembly lines :4364, :4369). For the derived kind `_dash_plot_opts_to_json` writes `"recast":"<s(_recast_target)>"`; for the other kinds the `recast` key is cleared before the JSON is written. `c_local plottype_out` returns the drawn type.
  - `_ptype_typed` is a fixed vocabulary name (the type list), never user text; `recast_from` therefore needs no escaping beyond `_dash_json_str`.

### dash_render.py (both modes; GlyphMapper travels with its class)

- **TR-45.5 Labels.** `_dash_layer_series` (S19; and `_dash_legend_key` if it reads `type` directly) reads `plot.get("recast_from") or plot.get("type")` for its label rule, so a recast layer's key and default titles are the typed type's (A60).
- **TR-45.6 `GlyphMapper._dash_draw_xy_as(self, fig, source, target, options, color_idx=0, view=None)`** (new, directly after `map_function`), with the class constant `_RECAST_DRAWN = ("scatter", "line", "connected", "area", "bar", "spike", "dropline", "dot")`.
  - `target` not in `_RECAST_DRAWN` raises ValueError (Stata canonicalised it; a hand-made spec gets the "no glyph mapper" path's words, never `getattr` on user text).
  - It calls `_dash_glyph_dispatch(self)[0][target](fig, source, "y", "x", opts, view=view, color_idx=color_idx)`, with `opts = {k: v for k, v in options.items() if k not in ("recast", "type")}`, adding `order=None` only for a target in `_DASH_JOIN_TYPES`, as `_dash_add_glyph` does (map_scatter takes no `order`; the derived points are already in x order), so each target's scheme chain (S24's `_scheme_alpha_kw`/`_cycle_for` on the target name), S14's bar width and S40's `_dash_join_glyph` apply.
  - Afterwards: every renderer it added gets the derived layer's `_dash_agg_source` set to its own `data_source` when the derived renderer would have carried one (kdensity), and any `_dash_frozen`/hull role attribute the derived mapper sets; any HoverTool whose `renderers` are only renderers it added is removed from `fig.tools` (BR-45.3).
  - It returns the first renderer the target drew, as the derived mapper returned its line.
- **TR-45.7 The tails.** In each of the 11 mappers of E4, directly before the final glyph call (S40's `_dash_join_glyph` call, map_histogram's quads, map_scatteri's scatter): `if options.get("recast"): return self._dash_draw_xy_as(fig, <points source with columns x, y>, options["recast"], options, color_idx, view=None)`. map_histogram passes bin midpoints and heights; map_function the drawn points (S40's bridging applied first); map_scatteri its point source. Nothing else in a mapper changes.
- **TR-45.8 Not edited.** `_dash_glyph_dispatch` (read only; the manifest's mention is its use by TR-45.6), `_dash_add_glyph`, `_make_figure_body`, `_generate_app_source`, `_build_filter_widgets`, `_FILTER_JS`, `_stale_cue_args`, `_collect_frozen_layers`. The served copy lists gain nothing: `_dash_draw_xy_as` is a GlyphMapper method (R2 row S45: the anchor after `"_dash_glyph_dispatch",` (33130) is used only if the helper is made module-level, which this plan does not do).
- **TR-45.9 Maps.** Under `# WP-30 S45 (P1.8b): recast() (P1.8 part b)`: `test/function_test_map.py` `FUNCTIONS` gains `"GlyphMapper._dash_draw_xy_as"` → `test/test_recast.py::TestTheDrawAsHelper::test_each_target`; `test/program_coverage_map.py` `COVERAGE["dash.ado"]` gains `_dash_recast_opt` → `test/test_twoway_option_parity.cscript` (RC-01..RC-13).
- **TR-45.10 Help** (R3: Statistical Layer Options, Unsupported). dash.sthlp's "Not drawn" entry for `recast()` (:3734) is removed; a `{phang2}{ul:Recast.}` paragraph in Statistical Layer Options states BR-45.1-BR-45.6 in 79-column lines; the Unsupported section names only `recast()` on pci/pcarrowi and histogram's range targets.
- **TR-45.11 Security (rule 1).** The target reaching the renderer is one of eight fixed names checked by membership; `recast_from` is one of dash's type names; no option text reaches `getattr`, `eval`, HTML or JS. The note echoes the typed value through `_dash_say` (bounded by Stata's option length).

## Boundaries

- **Batch partners:** S46 (`_generate_app_source`, `_dash_launch_app`, `__main__`, `_dash_serve_spec`, `_dash_serve`, `_dash_build`'s Limits line, help Server Mode/Limits/Subcommands); S47 (`_dash_plot_margin`, `_dash_padded_range`, S21's finishers, `_make_figure_body` if needed, the scheme extractor and 26 files, help Region Styling). S45 touches none of them.
- **S40's, read only:** the bodies of `_dash_connect_opt`, `_dash_join_vertices`, `_dash_join_glyph`, `_join_order` and the cmissing breaks; S45 feeds `_dash_connect_opt` the drawn type and edits only S40's wiring lines for the derived kind (TR-45.4).
- **Later:** S49 refuses `horizontal`/`vertical` on the drawn type (IR-13) and transposes recast layers through the same mappers; S57 audits the move path.
- **Not this section's:** histogram → range targets (P2.44); `recast()` on pci/pcarrowi (new P2 row for S58); the exact note name twoway prints for a multi-word value (`scatterline`); `yvarlabel()`/`xvarlabel()`.
- **Never:** `scripts/regen_option_surface.py` (IR-7); a hand patch of a generated file; the served copy lists.

## Stata truth

### `scripts/extract_recast_truth.do` → `test/fixtures/recast_truth.json`

S02's stanza (TR-02.9) with `<file>` its own name, then `adopath ++ "`repo'/"` and `global dash_nobrowser 1`; `_meta` as `scripts/extract_series_label_truth.do` writes it (`stata_version`, `born_date`, `dash_commit` read back through `Macro.getLocal` from a `shell` git capture, `extracted`), plus `classes` (the four class lists read from `c(sysdir_base)/style/*type-*.style`). The python block reads SVGs through `scripts/svg_truth.py` (`svg_document`), never calls Stata, never uses `shell=True`, writes a backtick as `\x60`.

- **Data:** E7's 8 rows (x, y, y2, t descending, tsset t) and `sysuse auto` for the fit probes.
- **Probes** (each `capture noisily twoway <cmd> name(g, replace)` inside a named log; rc, the `(note:` lines and the first error line; for rc 0 an SVG export and per-element counts `circle`, `path`, `line`, `rect`, `polygon` plus the first path's vertices in data units): every line of E7, the base pairs they are compared with (`line y x`, `scatter y x`, `bar y x`, `rspike y y2 x`, `pcspike y x y2 x`, `connected y t, sort`), and `rline y y2 x, recast(line)` against `line y x`. Each probe records `equal_to` (the base probe whose counts and first path match) when one does.
- Run: `DASH_REPO="$WT" "$SLOT" "$S" "$WT/scripts/extract_recast_truth.do"` (log `$S/extract_recast_truth.log`, about 80 exports). `git add -f test/fixtures/recast_truth.json`.

### Area cases, `test/test_twoway_option_parity.cscript` (R1; one contiguous run at the end of its last case block, after S37's MV run)

Each case runs live twoway (`capture twoway … nodraw`, rc and notes from a named log) and dash (`_ztp_run`; the spec through `_dash_process_segment` and `_ztp_hasval`), in the script's `nfail`/`faillist` form, printing `RC-nn PASS: …`. Header `// RC: recast(), read as twoway reads it (WP-30 P1.8b)`.
- **RC-01** lfitci, qfitci, lpolyci, fpfitci × `recast(line)`, `recastas(line)`, `type(line)`: dash rc = twoway rc = 198, same error line.
- **RC-02** `scatter mpg weight, rec(line)`: 198 both, `option rec() not allowed`.
- **RC-03** `scatter mpg weight, recast(line)`: spec `"type":"line"`, `"recast_from":"scatter"`, no `recast` key; no note.
- **RC-04** fallbacks: `line … recast(rline)` → `"type":"scatter"`; `rline mpg turn weight, recast(pcspike)` → rspike; `pcspike …, recast(line)` → pcspike; `function y=x, range(1 5) recast(rline)` → function; dash's note lines equal twoway's (both lines, class names included).
- **RC-05** precedence: `recast(line) type(bar)`, `type(bar) recast(line)`, `recastas(bar) recast(line)` → line; `recast(line) recast(bar)` and `type(line) type(bar)` → bar.
- **RC-06** spellings and case: `li`, `sc`, `co`, `b`; `rsc` on rline (rscatter) and on scatter (note, scatter); `pcbar`, `pccaps`, `pcl` (note naming pcline); `LINE`, `l` (notes).
- **RC-07** `dot …, recast(line)`: no note, `"type":"dot"`; `pci 1 1 2 2, recast(pcarrow)` and `histogram mpg, recast(rline)`: rc 0, `recast()` named.
- **RC-08** `scatter mpg turn weight, recast(line line)` → line, no note; `recast(line scatter)` → twoway's notes, scatter (both y).
- **RC-09** tsset data: `tsline y, recast(connected)` → `"type":"connected"`, `"sortvars":"t"`.
- **RC-10** `rline mpg turn weight, recast(line)` → `"type":"line"`, `"yvar":"mpg"`, no `yvar2`.
- **RC-11** `lfit mpg weight, recast(scatter)` → `"type":"lfit"`, options `recast` scatter; `lfit …, recast(rline)` → notes, `recast` scatter.
- **RC-12** `line mpg weight, recast(scatter) c(l)` → `"type":"connected"` (S40's override on the drawn type).
- **RC-13** judge type: `lfit mpg weight, recast(scatter) msymbol(O)` names nothing; `scatter mpg weight, recast(line) sort` names nothing and writes `sortvars`.

`test/test_abbreviations.cscript`: `recasta(line)`, `recastas(line)` and `ty(line)` reach `s(recast)`/`s(type)` (its abbreviation table gains `recastas` and `type`, DASH_PLOT_KEYS :240 gains `type`).

### The S45 block of `test/test_wp30_truth.cscript` (R1)

Helpers `_s45_*` directly above S01's `* ==== S45 P1.8b: recast() ====` header: a `python:` reader returning, per renderer of a saved page, its glyph class and point count (any Stata helper declares `version 19`). Cases report through `_w30_expect`/`_w30_done`, write only under `` `w30_work' `` and erase their pages and SVGs before the `S45 end` line (TR-01.10 item 4); run alone (`WP30_ONLY=S45`) the block prints its PASS lines and `ALL CHECKS PASSED`. Inside the stub:
- **RC-20** `scatter y x, recast(line)`, `rline y y2 x, recast(line)`, `tsline y, recast(connected)`: dash's glyphs equal the fixture's `equal_to` base (one Line of y; markers plus line in time order).
- **RC-21** `kdensity mpg, recast(area)`, `lfit mpg weight, recast(scatter)`, `histogram mpg, recast(line)`, `function y=x^2, range(0 3) recast(scatter)`: dash's glyph kind and point count equal twoway's element counts.
- **RC-22** the fallbacks of RC-04: dash's notes printed and its glyph equals the fallback's.

## TDD test stubs

### Regression tests, new `test/test_recast.py` (red at the batch-16 base unless marked guard; 45-01)

Helpers reuse `test_join_order.py`'s `_saved`/`_served`/`_saved_move`/`_served_move` and S40's `test_connect_options.py` spec builders; specs are written as dash.ado writes them after TR-45.4.
- Test: `test/test_recast.py::TestTheDrawAsHelper::test_each_target[scatter|line|connected|area|bar|spike|dropline|dot]` — `_dash_draw_xy_as` on a 5-point source draws the glyph class `map_<target>` draws on the same source. Red: AttributeError.
- Test: `…::TestTheDrawAsHelper::test_an_unknown_target_raises` — `"bogus"`, `"__class__"` raise ValueError. Red: AttributeError.
- Test: `…::TestBaseRecast::test_drawn_as_the_target[<pair>-saved|served]` for scatter→line, line→scatter, scatter→connected, scatter→bar, line→area, rarea→rline, rspike→rcap, pcspike→pcarrow: the figure's renderers equal those of the plain target spec (glyph class, field values). Red at the base: the spec's `type` alone is what the base draws, so this is a guard of the renderer path; it turns red only through RC-03 (listed with the guards).
- Test: `…::TestRangeCastToYx::test_first_bound[saved|served]` — `{"type":"line","recast_from":"rline","yvar":"mpg"}` draws one Line of mpg. Guard (as above).
- Test: `…::TestDerivedRecast::test_type[<derived>-<target>-saved|served]` for lfit, qfit, lowess, lpoly, fpfit, mspline, mband, kdensity, function, histogram, scatteri × scatter, line, area, bar: the drawn glyph class is the target's and its x/y equal the un-recast layer's points (histogram: bin midpoints and heights). Red: the derived glyph is drawn.
- Test: `…::TestRecastBarIsOneUnitWide::test_kdensity_bar[saved|served]` — `width == 1.0` (S14's rule). Red.
- Test: `…::TestRecastKeepsTheSeriesLabel::test_key[lfit-scatter|kdensity-area|rline-line|scatter-line]` — the legend key text equals the un-recast spec's. Red for rline-line (the line label) and the derived cases (the glyph never drawn).
- Test: `…::TestNoTooltipIsAdded::test_fit_recast_scatter[saved|served]` — no HoverTool names the recast fit's renderers when the un-recast fit had none. Red.
- Test: `…::TestRecastAfterAMove::test_kdensity_area[saved|served]` — after a dropdown move the VArea's y equals the oracle density of the kept rows (saved through node, `_saved_move`; served through `_served_move`). Red.
- Test: `…::TestRecastAfterAMove::test_lfit_scatter_is_marked[saved]` — after a saved move the recast fit carries the stale cue as an un-recast lfit does (`_DASH_STALE_SUFFIX["fit"]` in its key). Red.
- Test: `…::TestRecastAfterAMove::test_histogram_line[saved|served]` — served: redrawn to the kept rows' heights; saved: the same treatment as the un-recast histogram at the base (recomputed or marked; 45-01 measures which and writes it into the test with a comment). Red.
- Test: `…::TestTheFixture::test_meta_and_classes` — the four `_meta` keys exist; `set(classes['yxtype']) == set(GlyphMapper._RECAST_DRAWN)`, and the other three classes equal E7's lists. Red: no fixture (45-01 writes it before the run; the test fails on `_RECAST_DRAWN`).
- Test: `…::TestTheHelp::test_recast_is_documented` and `::test_not_drawn_names_only_the_residuals`. Red.

Guards (pass at the base; listed apart in the failure file): `TestBaseRecast`, `TestRangeCastToYx`; `test/test_mode_parity.py` CORPUS gains, under `# WP-30 P1.8b: recast()`, `scatter recast line` (spec as TR-45.4), `lfit recast scatter`, `kdensity recast area` (the last two red), and `MOVE_CORPUS` `kdensity recast area after a dropdown move` (red).

### Pinned tests to flip (R9; re-measured at batch-16-base, never trusted)

- `test/test_unsupported_report_is_true.py` `PLOT_VALUES["recast"]` (:137 at `c96facd`; S40 left it, Q-40.1): moved to a `pci` row (`("pcarrow", "pcspike", "pci")`, still named and inert there) with `Flipped: … recast() on scatter was named and inert, which was wrong because twoway draws the target (recast_truth.json)`; `test_help_claims_8.py::TestAnUnsupportedOptionIsInertWhenServed::test_plot_level[recast]` follows the row.
- `test_unsupported_report_is_true.py:240` (plot pending) and `:607` (declared plot): re-derived (R10, `# <old> -> <new>: P1.8b …`).
- `test/test_help_claims_8.cscript` HC8-02: `recast(line)` and `recast` leave the composite scatter list (a recast would turn its scatter into a line); a new HC8-02r row checks `pci 1 1 2 2, recast(pcarrow)` names `recast()`, and `scatter …, recast(line)` names nothing. `test_help_claims_8.py` and `test_help_conformance.py` counts follow the help (R10).
- `test/test_abbreviations.cscript:240` gains `type`.
- `test/test_help_conformance.py:541` (`test_the_help_parser_handles_the_space_form_of_opt`) asserts `recast` is a help option; the residual Unsupported entry keeps the `{opt recast(plottype)}` form, so it holds (checked, not flipped).
- `test/test_help_claims_8.cscript` HC8-03's `taken` list keeps `scatter mpg weight, recast(line)` (twoway still accepts it).

## Test plan

| What | How | Fixture / data | Both modes? |
|---|---|---|---|
| Parse, precedence, spellings, refusals, notes | cscript RC-01..RC-13 against live twoway; `test_abbreviations.cscript` | sysuse auto; E7 data | n/a |
| Base, range, ts recasts drawn as the target | pytest `TestBaseRecast`, `TestRangeCastToYx`; truth RC-20 | `recast_truth.json` | yes |
| Derived recasts | pytest `TestDerivedRecast`, `TestRecastBarIsOneUnitWide`, `TestRecastKeepsTheSeriesLabel`, `TestNoTooltipIsAdded`; truth RC-21 | fixture | yes |
| After a move | pytest `TestRecastAfterAMove`; `test_mode_parity.py` MOVE_CORPUS | auto | saved (node), served |
| Fallbacks and notes | cscript RC-04, RC-06, RC-08; truth RC-22 | fixture | n/a |
| Registries, tracking | `test_function_test_map.py`, `test_program_coverage_map.py`, `test_tracking_documents.py`, `test_fixtures_are_committed.py`, `test_unsupported_report_is_true.py` | — | n/a |

**Acceptance criteria.**
- **AC-45.1** (BR-45.1, BR-45.2) RC-03, RC-09, RC-10 and RC-20 PASS; `TestBaseRecast` and `TestRangeCastToYx` pass in both modes.
- **AC-45.2** (BR-45.3, BR-45.7) `TestDerivedRecast`, `TestRecastBarIsOneUnitWide`, `TestRecastKeepsTheSeriesLabel`, `TestNoTooltipIsAdded`, `TestRecastAfterAMove` and RC-21 pass; the node tests are not skipped.
- **AC-45.3** (BR-45.4) RC-04..RC-08, RC-11..RC-13 and RC-22 PASS; dash's note lines equal twoway's.
- **AC-45.4** (BR-45.5, BR-45.6) RC-01, RC-02 and RC-07 PASS.
- **AC-45.5** `test_mode_parity.py` passes with the new CORPUS cases and `ALLOWED`/`_MUST_WARN` untouched; every flipped node passes with a `Flipped:` line; the full suite reports 0 failed; G7 prints 0 twice.

## Tasks

**Commit boundary.** Tasks 45-01 to 45-10 form one commit, made by 45-10 on `wp30-s45` with the subject `Draw a recast layer as its target type, as twoway does (WP-30 P1.8b)`. `<scratch>` is the orchestrator's WP-30 scratch directory (index.md "Deltas"), which holds `batch-16-base.txt`, `batch-16-impact.txt` and `full_suite_queue.sh`; `$S` is `<scratch>/s45` (45-01 runs `mkdir -p "$S"`), so S45, S46 and S47, which run in parallel, never share a log name or slot directory; `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s45`, `$SLOT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh`. A cscript runs through the driver: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" "<script>.cscript" > "$S/run_<script>.do"`, then `WP30_ONLY=S45 "$SLOT" "$S" "$S/run_<script>.do"`.

<task type="auto" id="45-01">
  <name>Write the recast fixture and tests</name>
  <files>scripts/extract_recast_truth.do, test/test_recast.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    Check `git -C "$WT" rev-parse HEAD` equals `cat "<scratch>/batch-16-base.txt"` and `git -C "$WT" branch --show-current` prints `wp30-s45`; stop otherwise. `mkdir -p "$S"`. Check the prefix is free: `grep -lE '(^|[^A-Za-z0-9_])RC-[0-9]' "$WT"/test/*.cscript "$WT"/test/*.py "$WT"/test/*.do` prints nothing. Create `scripts/extract_recast_truth.do` as "Stata truth" describes and run it with `DASH_REPO="$WT" "$SLOT" "$S" "$WT/scripts/extract_recast_truth.do"`; it writes `test/fixtures/recast_truth.json`. Create `test/test_recast.py` with every stub of "TDD test stubs" (new symbols named as `dr.GlyphMapper._dash_draw_xy_as` and `dr.GlyphMapper._RECAST_DRAWN`, so they fail with AttributeError now); for `TestRecastAfterAMove::test_histogram_line[saved]` first build an un-recast histogram, run a saved move under node, and write what it does (recomputed or marked) into the test with a comment naming the base sha. Append the CORPUS and MOVE_CORPUS cases to `test/test_mode_parity.py` after any earlier section's cases. Run `python3 -m pytest test/test_recast.py -q -n 6 -p no:cacheprovider -rf > "$S/45-new.log" 2>&1` and `python3 -m pytest test/test_mode_parity.py -q -n 6 -p no:cacheprovider -k "P1.8b" -rf >> "$S/45-new.log" 2>&1`. Write `$S/45-P1.8b-failure.txt`: the base sha, one line per failing node, then "Guards (pass at the base)". Edit no shipped file; do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json; d=json.load(open('$WT/test/fixtures/recast_truth.json')); m=d['_meta']; print(all(k in m for k in ('stata_version','born_date','dash_commit','extracted')), sorted(m['classes']))"` prints `True ['functiontype', 'y2xtype', 'yxtype', 'yxyxtype']`; `grep -c FAILED "$S/45-new.log"` is at least 40; `git -C "$WT" diff --name-only -- dash.ado dash_render.py` prints nothing.]]></verify>
  <done>The twoway recast fixture existed and every pytest regression test was shown failing on the unmodified tree, with the failure text and the guards saved.</done>
</task>

<task type="auto" id="45-02">
  <name>Write the refusal and truth cases</name>
  <files>test/test_twoway_option_parity.cscript, test/test_wp30_truth.cscript, test/test_abbreviations.cscript</files>
  <action><![CDATA[
    In `test/test_twoway_option_parity.cscript`, as one contiguous run at the end of its last case block (after S37's MV run) and before the `// Summary` divider, add the header `// RC: recast(), read as twoway reads it (WP-30 P1.8b)` and RC-01..RC-13 of "Stata truth", each comparing live twoway's rc, notes and first error line with dash's (rc, notes, and the segment JSON through `_dash_process_segment` and `_ztp_hasval`). In `test/test_wp30_truth.cscript` put the `_s45_*` helpers directly above S01's `* ==== S45 P1.8b: …` header and RC-20..RC-22 between its start and end lines. In `test/test_abbreviations.cscript` add `type` to DASH_PLOT_KEYS (:240 at c96facd) and the `recasta(line)`, `recastas(line)`, `ty(line)` rows. Run all three through the driver on the unmodified shipped files and append every `RC-nn FAIL` line, with the twoway text it quotes, to `$S/45-P1.8b-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -cE "RC-(0[1-9]|1[0-3]) FAIL" "$S/run_test_twoway_option_parity.log"` is at least 11 (RC-07's dot half may pass); `grep -cE "RC-2[0-2] FAIL" "$S/run_test_wp30_truth.log"` prints 3; every other case of the three scripts still prints PASS.]]></verify>
  <done>The refusal, spelling, note and spec cases and the live twoway comparisons were in place and shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="45-03">
  <name>Declare and resolve recast in Stata</name>
  <files>dash.ado, test/program_coverage_map.py</files>
  <action><![CDATA[
    `_dash_parse_plot_opts`, `_dash_process_segment` and the folds are UNKNOWN to the index; confirm their callers with `grep -n` and record them in `$S/45-notes.txt`. Apply TR-45.1 (the RECASTas and TYpe declarations at :941, the pending line :1098 deleted with its comment reworded, the returns) and TR-45.3 (the new program `_dash_recast_opt` after `_dash_sort_opt`'s `end`, `version 19`, a header comment citing E7 and the class files; the class lists and spellings as fixed locals; notes printed through S06's Stata note path in twoway's exact words; refusals through `_dash_say`). Add TR-45.9's `COVERAGE["dash.ado"]` entry for `_dash_recast_opt` under S45's anchor of `test/program_coverage_map.py`. Edit no other program in this task.
  ]]></action>
  <verify><![CDATA[`test_abbreviations.cscript` through the driver prints its new rows PASS (`recasta()`, `recastas()` and `ty()` reach `s(recast)`/`s(type)` through the declarations alone); `grep -c "^program define _dash_recast_opt" "$WT/dash.ado"` prints 1; `python3 -m pytest test/test_program_coverage_map.py -q -n0 -p no:cacheprovider` reports 0 failed. RC-01, RC-02 and RC-05 need 45-04's call of `_dash_recast_opt` and are verified there.]]></verify>
  <done>dash.ado declared recast(), recastas() and type() as twoway does, refused them on the ci fits in twoway's words, and resolved a target with twoway's classes, spellings, fallbacks and notes.</done>
</task>

<task type="auto" id="45-04">
  <name>Wire the drawn type into the spec</name>
  <files>dash.ado</files>
  <action><![CDATA[
    Apply TR-45.4 in `_dash_process_segment`: `_ptype_typed`; the `_dash_recast_opt` call directly after `_dash_opts_repeats` and before S40's `_dash_connect_opt`; the drawn `ptype` for base/range/pc/ts kinds; the judge-type arguments for the derived kind (D-45j; S40's five wiring lines, edited only for that kind); the ts `sort1` rule; the `range2yx` vfields; `recast_from` in both assembly lines (:4364, :4369 at c96facd); the `recast` key written only for the derived kind; `c_local plottype_out` the drawn type. Do not edit the bodies of S40's `_dash_connect_opt`, `_dash_fold_bw`, `_dash_validate_opts`, `_dash_fold_typed` or `_dash_sort_opt`.
  ]]></action>
  <verify><![CDATA[Through the driver `test_twoway_option_parity.cscript` prints RC-01..RC-13 PASS and `test_twoway_option_parity: ALL CHECKS PASSED`; `test_parser.cscript` and `test_join_order` cscripts named by `grep -l "_dash_process_segment" "$WT"/test/*.cscript` print no new FAIL.]]></verify>
  <done>Every recast layer reached the spec as its drawn type with the typed type kept for its label, its first bound or time order where twoway uses them, and the target recorded for derived layers.</done>
</task>

<task type="auto" id="45-05">
  <name>Add the draw-as helper and labels</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Run `gitnexus impact _dash_layer_series -d upstream -r dash` and `gitnexus impact _dash_legend_key -d upstream -r dash` in the main checkout and record the risk in `$S/45-notes.txt`; report any HIGH or CRITICAL before editing. Apply TR-45.5 (the `recast_from` lookup in S19's label helper) and TR-45.6 (`GlyphMapper._RECAST_DRAWN`; `GlyphMapper._dash_draw_xy_as` directly after `map_function`, with a docstring citing E7 and A60; dispatch read through `_dash_glyph_dispatch`; the agg-source, frozen and hull-role carry-over; the HoverTool removal). Do not edit `_dash_glyph_dispatch` or `_dash_add_glyph`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_recast.py -q -n 6 -p no:cacheprovider -k "TestTheDrawAsHelper or TestRecastKeepsTheSeriesLabel and rline"` passes; `python3 -m pytest test/test_legend_order.py test/test_server_legend.py test/test_mode_parity.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>A derived layer could be drawn as any of the eight yx types through their own mappers, and a recast layer's key read as its typed type's.</done>
</task>

<task type="auto" id="45-06">
  <name>End the derived mappers in draw-as</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    The 11 mappers are UNKNOWN to the index (dispatch dict and by-name calls; confirm with `grep -n "map_lfit\|map_scatteri\|map_function" dash_render.py`). Apply TR-45.7 to map_lfit, map_qfit, map_lowess, map_lpoly, map_fpfit, map_mspline, map_mband, map_kdensity, map_function, map_histogram and map_scatteri: one `if options.get("recast"):` return directly before each final glyph call, with the points source TR-45.7 names. Change nothing else in them.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_recast.py test/test_mode_parity.py -q -n 6 -p no:cacheprovider` passes, the node tests not skipped; `python3 -m pytest test/test_connect_options.py test/test_join_order.py test/test_saved_stale_cue.py test/test_stat_truth.py test/test_estimator_cost.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>Every derived layer with recast() kept its computation and was drawn as its target in both modes, recomputed or marked after moves as before.</done>
</task>

<task type="auto" id="45-07">
  <name>Run the truth block green</name>
  <files>test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Run `test_wp30_truth.cscript` through the driver with `WP30_ONLY=S45`. Where an RC-20..RC-22 case fails because of a counting detail of the reader (not of dash's drawing), fix the `_s45_*` helper only and record why in `$S/45-notes.txt`; a drawing difference goes back to 45-04 to 45-06. Check `~/.stata19/console/stata19.rc` still holds `python_exec` (a SKIP is not a pass).
  ]]></action>
  <verify><![CDATA[`grep -cE "RC-2[0-2] PASS" "$S/run_test_wp30_truth.log"` prints 3 and the log has no SKIP line for S45.]]></verify>
  <done>dash's drawing of recast layers matched live twoway's in the truth block.</done>
</task>

<task type="auto" id="45-08">
  <name>Document recast in the help</name>
  <files>dash.sthlp, test/test_help_conformance.py, test/test_help_claims_8.py</files>
  <action><![CDATA[
    Apply TR-45.10: find each place by its text (the "Not drawn" entry at :3734 at c96facd, a new Recast paragraph in Statistical Layer Options, the Unsupported entry); every changed line at most 79 characters; no tool or vendor name. Then re-measure the help counts that `test/test_help_conformance.py` (`test_the_ignored_list_was_found`, `test_the_unsupported_section_was_found`) and `test/test_help_claims_8.py`'s Unsupported equality pin hold, and set them in place with `# <old> -> <new>: P1.8b recast() honoured` (R10), one `Flipped:` line each in `$S/45-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "test/test_recast.py::TestTheHelp" test/test_help_conformance.py test/test_help_claims_8.py -q -n 6 -p no:cacheprovider` reports 0 failed; `awk 'length > 79' "$WT/dash.sthlp" | grep -ci recast` prints 0.]]></verify>
  <done>The help documented recast() as twoway draws it and named only the residual forms, and the help-count pins held the measured values.</done>
</task>

<task type="auto" id="45-09">
  <name>Flip the pinned pending entries</name>
  <files>test/test_unsupported_report_is_true.py, test/test_help_claims_8.cscript, test/function_test_map.py</files>
  <action><![CDATA[
    Re-measure "Pinned tests to flip" on this tree and flip in place, each with a comment "Flipped (WP-30 P1.8b): <old> was wrong because twoway draws the target (recast_truth.json)": the `recast` row of PLOT_VALUES (to the pci row); the plot pending (:240) and declared plot (:607) counts with `# <old> -> <new>: P1.8b recast() honoured` (R10); HC8-02's composite list without `recast(line)`/`recast`, its count comments corrected, plus the HC8-02r row. Append one `Flipped:` line per node to `$S/45-flips.txt`. Add TR-45.9's `FUNCTIONS` entry under S45's anchor of `test/function_test_map.py`. Delete no test.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_unsupported_report_is_true.py test/test_function_test_map.py test/test_program_coverage_map.py -q -n 6 -p no:cacheprovider` reports 0 failed; `test_help_claims_8.cscript` through the driver prints `HC8-02 PASS` and `HC8-02r PASS`.]]></verify>
  <done>Every pin that asserted recast() was ignored asserted it drawn, with the reason recorded and the pci and histogram residuals still named, and the new method was mapped to its test.</done>
</task>

<task type="auto" id="45-10">
  <name>Close the entry and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Read the title as `WP30_OPEN["P1.8b"]`. Close that BUGS.md entry in place (`- [x]`, the Resolution of Notes, today's date as ddmonyyyy). Delete the `"P1.8b"` key line of `WP30_OPEN`. Replace both `<!-- WP-30 P1.8b -->` markers in place with the two lines of Notes (Results that change; Changed behaviour). Run `test_tracking_documents.py`, `test_fixtures_are_committed.py`, `test_cscript_hygiene.py`, `test_recast.py` and `test_mode_parity.py` with `-n 6`, and the three cscripts through the driver. `git -C "$WT" merge --no-edit main` (expect `Already up to date.`); one full run `"<scratch>/full_suite_queue.sh" "$WT" "$S/45-full.log"` in the background, read when `exit=` appears, never relaunched (E6 for the flaky four). Stage exactly the files 45-01 to 45-10 changed plus `git add -f test/fixtures/recast_truth.json`; check `git -C "$WT" diff --cached --name-only` lists only those (G6). Write `$S/45-message.txt` in Notes' form, check G7, confirm the branch, commit, check G7 again.
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/45-full.log"` shows 0 failed and `exit=0`; `grep -c '<!-- WP-30 P1.8b -->' "$WT/CHANGELOG.md"` prints 0; `grep -c '^    "P1.8b": "' "$WT/test/test_tracking_documents.py"` prints 0; `git -C "$WT" log -1 --format=%s` ends `(WP-30 P1.8b)`; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Entry P1.8b was closed naming existing tests, its markers carried the measured old and new behaviour, and one green commit on wp30-s45 was ready for the merger.</done>
</task>

## Section completion criteria

- Base, range, pc and time-series recasts are drawn as the target, with twoway's spellings, precedence, fallbacks, notes, first-bound and time-order rules, in both modes and after moves (RC-03..RC-13, RC-20, RC-22, `TestBaseRecast`, `TestRangeCastToYx`).
- Derived recasts keep their computation, draw as the target with its scheme chain and S14's bar width, keep their key and gain no tooltip; after a move they are recomputed or marked as before (`TestDerivedRecast`, `TestRecastAfterAMove`, RC-21).
- The ci refusals and `rec()` are r(198) in twoway's words; `dot` is silent; pci/pcarrowi and histogram's range targets are named.
- `recast_truth.json` is generated by its extractor, stamped and committed with `-f`; `_dash_recast_opt` and `GlyphMapper._dash_draw_xy_as` are mapped; every pin is flipped with its reason.
- One green commit `(WP-30 P1.8b)` on `wp30-s45` closes the entry, deletes its key and replaces both markers.

## Notes

- **Maintainer question (ratify) Q-45.1: D-45a departs from register A60.** A60 (P1.16.5) reads "P1.8b keeps `type`, writes `recast`", for the reason "twoway keeps the original type's label". This plan writes the drawn type into `type` for base, range, pc and ts recasts and keeps the typed one as `recast_from`, which S19's label helper reads first; derived layers keep `type` and write `recast`, as A60 says. **Reviewed and judged sound; recommendation: ratify.** Why: (1) A60's purpose holds: the key and default titles come from the typed type (`TestRecastKeepsTheSeriesLabel`), never from the drawn glyph. (2) S40 already rewrites `type` for scatter plus `connect()` (`"type":"connected"` per y), so the spec has one meaning of `type`, "what is drawn", for both P1.8 parts. (3) Every type-keyed renderer site then sees what is drawn with no edit: the dispatch, join order (`_DASH_JOIN_TYPES`), hull roles (`_dash_tag_hull_roles`), the linked scatter view (:30604), frozen tags (`_DASH_COMPUTED_ONLY_TYPES`), S24's scheme chain and S49's horizontal refusals through `plottype_out` (IR-13). (4) The literal form would need the type routing of both render loops changed (`_make_figure_body`, the served `_dash_draw_layer` in `_generate_app_source`). R12 gives `_make_figure_body` to S47 and `_generate_app_source` to S46 in batch 16, and those routing edits would reach every recast site. If the maintainer strikes it, S45 keeps `type` as typed, adds `options.recast` for every kind, and moves to a batch where it holds both routing editors (re-planned before that batch's base, A151).
- **D-45b (measured, M1).** `recast()` is one value for every y (E7): `scatter y y2 x, recast(line)` recasts both, `recast(line scatter)` is an unknown name. The manifest's "per-y lists through S11's splitter" is read as: S11's tokeniser only detects a multi-word value. twoway names a two-word value `scatterline` in its note; dash names the value as typed (residual below).
- **D-45j (judge type).** Base/range/pc/ts kinds: every later step sees the drawn type, as twoway's view does. Derived kind: its own options (bandwidth, n(), range(), bins) are validated as the derived type, and the option families that depend on the drawn glyph (connect, cl*, colorvar, jitter, sort) are judged on the target.
- **Register P1.8.1 read with the measurement.** "function and dot ignore it": dot ignores every target (E7); `function` is drawn as a functiontype target (`function y=x, recast(scatter)` draws markers, research §2 and E7) and only an out-of-group name leaves it on its own line. M1 binds the measured picture.
- **Manifest wording read.** "Edits … `_dash_glyph_dispatch`": the draw-as helper reads it; it is not edited (TR-45.8). "The JS recompute and the stale cue still cover a recast layer": `TestRecastAfterAMove`. "Lands before S49": `c_local plottype_out` returns the drawn type.
- **python_exec hazard.** Check `~/.stata19/console/stata19.rc` after each slot run; a SKIP is not a pass.
- **Merge rules.** R1: RC-01..RC-13 as one run at the end of `test_twoway_option_parity.cscript`; RC-20..RC-22 in S45's stub, helpers above its header; the abbreviation rows in `test_abbreviations.cscript`. R2: no copy-list change (GlyphMapper method); map entries under S45's anchors. R3: Statistical Layer Options and the Unsupported list (pending mover). R4/R5: the two `P1.8b` markers, the entry and its key. R6: `version 19` in `_dash_recast_opt`; no Mata function added. R7: one new fixture and extractor. R8: CORPUS/MOVE_CORPUS appended; `ALLOWED`/`_MUST_WARN` untouched. R9: E5's flips. R10: the pending and declared counts, HC8-02's counts, the help-conformance counts. R12: S45 edits no one-editor symbol.
- **Landing (merger).** `gitnexus detect-changes --scope all --repo dash` must name `GlyphMapper._dash_draw_xy_as`, the 11 mappers, S19's label helper and test symbols; dash.ado programs do not appear (not indexed).
- **Commit message.** Subject as in "Commit boundary". Body: `$S/45-P1.8b-failure.txt`; the measured defect (Overview's block); what changed (TR-45.1-TR-45.10, both modes); then `Regression: test/test_recast.py::<Class>::<test> -- failed at <base sha> with <text>` per regression node (cscripts as `test/test_twoway_option_parity.cscript RC-01`, `test/test_wp30_truth.cscript RC-20`); the `Flipped:` lines of `$S/45-flips.txt`; `Fixture: test/fixtures/recast_truth.json (scripts/extract_recast_truth.do)`; `BUGS.md: "<WP30_OPEN["P1.8b"] title>" (closed)`. No tool or vendor name (G7).
- **BUGS.md Resolution** (one line, in place):

  ```
  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.8b). recast(), recastas() and type() are read as twoway reads them (dash.ado _dash_recast_opt: recast() and recastas() rightmost and over type(), twoway's spellings by class, case-sensitive, one value for every y, twoway's two notes and fallbacks -- scatter, rspike, pcspike, function's own line -- and refused r(198) on lfitci, qfitci, lpolyci and fpfitci in twoway's words); base, range, pc and time-series layers are written as the drawn type with the typed one kept for the key (a range type cast to a yx name draws its first bound, tsline and tsrline join in time order), and fits, kdensity, function, histogram and scatteri keep their computation and are drawn as the target through GlyphMapper._dash_draw_xy_as with the target's scheme chain, one-x-unit bars and no added tooltip, in the saved page and the served app, before and after filter moves; dot ignores recast() silently. Pinned by test/test_recast.py::TestDerivedRecast::test_type, test/test_recast.py::TestRecastAfterAMove::test_kdensity_area, test/test_recast.py::TestRecastKeepsTheSeriesLabel::test_key, test/test_twoway_option_parity.cscript RC-01, test/test_wp30_truth.cscript RC-20; fixture test/fixtures/recast_truth.json. Residual, deferred (WP-30): histogram recast to a range type or an unknown name stays named (P2.44); recast() on pci and pcarrowi stays named; twoway's note names a multi-word value differently (scatterline for line scatter).
  ```
- **CHANGELOG lines** (each replaces its marker in place; the `###` lines only say which list):

  ```
  ### Results that change
  - `recast()` is drawn: `dash scatter y x, recast(line)` drew markers and named the option, and now draws `line y x`; `kdensity x, recast(area)` drew a line and now draws an area; `lfit y x, recast(scatter)` drew a line and now draws the fitted points as markers; `recastas()` and `type()` are read as its synonyms, and an out-of-group or unknown name falls back as twoway does (a yx type to scatter, a range type to rspike, a pc type to pcspike) with twoway's two notes. (WP-30, P1.8b)

  ### Changed behaviour (may need your do-files changed)
  - `recast()`, `recastas()` and `type()` on lfitci, qfitci, lpolyci and fpfitci are refused as twoway refuses them (`recastas() option not allowed`, or `type() option not allowed`, r(198)), where dash took them with a note; `rec()`, `reca()` and `recas()` are refused with `option rec() not allowed`, r(198). (WP-30, P1.8b)
  ```
- **Notes for the closeout (S58; A145).**
  - **GAPS2.md A4** (A4-n) and **B12** (B12-b): closed by `<sha>` together with S40's A4-l/A4-m and B12-c/B12-d; **G15-a**, **AUDIT-09** and **AUDIT-11** close when both S40 and S45 have landed; **AUDIT-12** (TWOWAY_COVERAGE_AUDIT.md) closed by `<sha>`.
  - **P2.44** keeps histogram's range targets. **New P2 row:** `recast()` on pci and pcarrowi (twoway draws `pci …, recast(pcarrow)` as arrows).
  - **New P2 row:** the note name twoway prints for a multi-word `recast()` value.
  - **test/fixtures/rejected_options.json** `recast` entry (:4268 at `c96facd`) and `value_truth.json` are stale; refresh them.
  - **AGENTS.md invariant:** "a recast layer's drawn type is decided only by dash.ado `_dash_recast_opt`; the renderer reads `type` for drawing and `recast_from` first for labels; derived layers draw as a target only through `GlyphMapper._dash_draw_xy_as`."
  - **Unverified:** twoway's legend label for a range type cast to a yx name (A60's claim is kept, the label read from the typed type); Stata 14-18.5 (not run, M2).
