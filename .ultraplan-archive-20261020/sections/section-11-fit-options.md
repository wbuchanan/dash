# Section 11: Fit options (atobs, estopts/predopts/estcmd, nofit, fitplot, ciplot)

> Part of: WP-31 · GAPS3 rows: C4 · Risk: yellow · Batch: 4 · Depends on: 04 · Blocks: -- · Tasks: 4, 1 commit · Case-id prefix: U11

## Overview

**What is wrong today.** GAPS3 C4 (GAPS3.md:123): "Fit options `atobs`, `estcmd()`, `estopts()` (incl. fpfit `estopts(degree())`), `predopts()`, `ciplot()`, `fitplot()`, `nofit` named, not drawn." Evidence: dash_parse.mata:6261-6276 (the `_dash_rep_und_tab` rows `atobs`, `xlog`, `ciplot`, `fitplot`, `fit`/`nofit`), and `grep -c "estopts" dash.ado` = 0. None of the seven is declared in `_dash_parse_plot_opts` (dash.ado:1167-1239); each falls to the trailing `*`, is matched by `_dash_foreign_scan` against its `_dash_rep_und_tab` row so it is not refused as foreign, and ends in the generic note `dash: ignoring unsupported option(s): atobs nofit ...` (`_dash_report_ignored`, dash.ado:6590-6635). The help says so at dash.sthlp:2908-2912 ("the few dash cannot compute -- ... atobs, estcmd(), estopts() and predopts() on the fits -- are named in the note as ignored") and :3210-3211 (fpfit's degree "which dash does not honour"). twoway honours all seven (research/stata-ground-truth.md §1.3, `lfit_parse:52-80`, `lfitci_parse:31-62`, `fpfit_parse:41-51`, `lpolyci_parse:34-64`).

**After this section** both renderers draw them as twoway does:
- `atobs` evaluates the fit at the observed x values instead of twoway's `_gs_x_create` grid (`twoway__lfit_serset.ado:67-74`: `if !atobs { _gs_x_create, points() }` else the x column itself). On the saved page lfit and qfit already refit in JavaScript after S10 (batch 3), so the config gains the key `atobs` (true when given) and the JS grid must honour it: S11 writes the key through `_fit_agg_config` (TR-11.6 f); S16, batch 4's `_FILTER_JS` owner, makes `dash_fit_grid` return the sorted distinct x when `ac.atobs` is true (section-16 TR-16.11), so the saved page and the served app draw the same vertices after a move (M8).
- `nofit` hides the fit line of lfitci, qfitci, fpfitci and lpolyci and keeps the band (`lfitci_parse:60-62` `.fit = 0`; `lpolyci_parse:63-64`).
- `fitplot(plottype)` and `ciplot(plottype)` (and lpolyci's `smoothplot()`, a synonym of `fitplot()` there, `lpolyci_parse:54-56` `.fittype`) recast the line and the band respectively through `_dash_draw_xy_as` and a new range twin `_dash_draw_range_as`; twoway's `type()`/`recast()` on the ci types stays refused r(198) as `_dash_recast_opt` already refuses it (dash.ado:2561-2566).
- `estopts()`, `predopts()` and `estcmd()` are run through Stata at registration: a new program `_dash_fit_points` (modelled on `_dash_fn_points`, dash.ado:8315-8362) calls twoway's own serset generator (`twoway__lfit_serset` for lfit/qfit/lfitci/qfitci, `twoway__fpfit_serset` for fpfit/fpfitci) with the typed options and stores the resulting (x, yhat[, lo, hi]) in the spec as the layer's `points`, exactly as a function layer carries its points today (`_dash_fn_points_json`, dash_parse.mata:5007). The renderer draws stored points instead of fitting; such a layer is frozen in BOTH modes with the existing stale cue after a move (DECISIONS D3): the JavaScript twins (S10, S13, S28) cannot run `regress, <estopts>`, and the served app makes no Stata call at move time either; it draws the stored points after a move with the same cue (D-11c).

**Why one section.** All seven ride the fit mappers (`map_lfit` :16244, `map_qfit` :16340, `map_lfitci` :16421, `map_qfitci` :16550, `map_fpfit` :17684, `map_fpfitci` :17765, `map_lpolyci` :17219), `_fit_grid` (:20969) and `_render_ci_band` (:12473); S11 is batch 4's owner of the fit mappers (index, batch 4 row).

**Test order and commit rule (rule 7, M6).** One row, one commit `(WP-31 C4)`: 11-01 writes the failing tests and the truth extractor and never commits; 11-02 declares the options and adds `_dash_fit_points`; 11-03 draws them in the renderer; 11-04 certifies, updates help/audit/BUGS/GAPS3/CHANGELOG (Tracked line `commit pending`, A11) and commits.

### Section decisions (binding on the executor)

- **D-11a. `atobs` is a grid rule, not a Stata run.** `_fit_grid(x, options, layer)` returns `np.unique(x)` sorted when `options.get("atobs")` is truthy; twoway evaluates at every observation (`touse2`), duplicates included, so the drawn line is identical and the unique grid only avoids repeated vertices. `atobs` with `range()` is refused by dash.ado with twoway's words `may not combine atobs with range()` r(198) (`lfit_parse:63-66`), measured in U11-02.
- **D-11b. `estopts()`, `predopts()` and `estcmd()` go through Stata.** They cannot be reproduced in numpy in general (`estopts(noconstant)`, `estcmd(glm)`, `predopts(xb)`); twoway itself hands them to `regress`/`predict`/`fracpoly`. `_dash_fit_points` runs the generator twoway runs and stores the serset's columns as `"points": {"x":[..],"y":[..],"lo":[..],"hi":[..]}` on the plot. A layer with `points` is drawn from them and marked frozen on the saved page by the existing `_frozen_layer_tag` path with the kind FORCED to "fit" (`_frozen_layer_tag(..., kind="fit")`, TR-11.6 b): after S10 (batch 3) `_dash_stale_kind` returns None for lfit and qfit (and S13/S28 make it None for the ci and fp types), so the kind cannot be read from the type; the `points` branch returns before S10's `_dash_agg_*` tagging lines, so the JS never refits such a layer from the raw rows (DECISIONS A20, R2-08). S11 does not edit `_dash_stale_kind` (R12). The words of the cue are the existing `_DASH_STALE_CUE_TEXT` and the " (unfiltered)" suffix of kind "fit", which S28 keeps for these layers (A20). Confirmed by maintainer decision D3.
- **D-11c. The served app does not refit a `points` layer** (DECISIONS D3: frozen in both modes, no sfi call at move time). `_dash_redraw_for` (:49267) re-runs the mapper; a mapper given `points` returns the stored points whatever rows a move keeps, and sets the status Div text `dash: <type> with estopts()/predopts()/estcmd() is drawn as registered; a filter move does not refit it` through the existing `_dash_note_empty_layer`-style note path (one note per layer per document). This is the M8 cue for served mode.
- **D-11d. `fitplot()`/`ciplot()` targets.** `fitplot()` takes the yxtype eight (`_RECAST_DRAWN`, :20690) through `_dash_draw_xy_as`; `ciplot()` takes y2xtype's range names (`rarea rbar rspike rcap rcapsym rscatter rline rconnected`) through the new `_dash_draw_range_as`. The name is canonicalised in dash.ado by the same spelling table `_dash_recast_opt` uses (`_sp_yx`, `_sp_rng`, dash.ado:2596-2598), in a new program `_dash_fitplot_opt` that writes `s(fitplot)`/`s(ciplot)` canonical and prints twoway's two notes for an unknown name (`named style X not found in class yxtype|y2xtype, default attributes used`), measured in U11-04.
- **D-11e. `xlog`/`xtransform()` stay out.** They are not in C4's row; they stay in `_dash_rep_und_tab` and the generic note (GAPS3 lists them nowhere as a gap). `n(3→100 under xlog)` therefore does not arise.

## Risk: [yellow] -- a new Stata-at-registration path, four spec keys, and the saved cue for a new frozen case

**Why.** `_dash_fit_points` runs `regress`/`predict` on the user's data under `preserve`; the renderer gains a `points` branch in six mappers; the pending-list and `_dash_rep_und_tab` edits shift three test counts.

**Risk factors.** 1. `estopts()` text reaches a Stata command line (injection surface). 2. `predopts()` and `range()` are exclusive in twoway (`lfit_parse:59-62`). 3. The served app's `agg_sources` registration (:49585-49604) registers any layer whose mapper built its own source; a `points` layer must still register so moves do not raise. 4. `nofit` hides a renderer the legend keys. 5. Counts in test_unsupported_report_is_true.py (196/85 declared) move.

**Mitigation.** 1. The option text reaches the command only through `macval()` and after `_dash_comma_pos`/`_dash_fn_stray_close` checks exactly as `_dash_fn_points` does (dash.ado:8319-8340, the predicate reused verbatim); a top-level `;`, a backtick, `$`, a `char(10)`/`char(13)` or a quote imbalance is refused r(198) with `error in expression`-style words naming the option (`option estopts() incorrectly specified`). 2. Refused in dash.ado with twoway's measured text (U11-02). 3. The `points` branch builds a `ColumnDataSource` of its own, so registration is unchanged; `TestServedMoveKeepsPoints` pins it. 4. `nofit` sets `line_r.visible = False` and `line_r.muted = True` and removes its `legend_label` (set `legend_label=None` before construction), pinned by `TestNofit`. 5. Counts move with `# <measured old> -> <new>: C4 <why>` comments, the old value re-read at the section's base with the file's `_declared_*()` helpers (R10, DECISIONS A33).

## Dependencies

- **Depends on: 04.** S04's applicability table refuses `atobs`/`nofit`/`fitplot()` on types that do not take them (`option atobs not allowed` r(198)); S11 declares them so S04's `applies` rows (`atobs@lfit|qfit|lfitci|qfitci|fpfitci`, `nofit|fitplot|ciplot@lfitci|qfitci|fpfitci|lpolyci`, `smoothplot@lpolyci`, `estopts|predopts@lfit|qfit|lfitci|qfitci|fpfit|fpfitci`, `estcmd@fpfit|fpfitci`) find a declared name. If S04 did not add these rows, 11-02 adds them in S04's format with the measured text from `applicability_truth.json`.
- **Blocks:** none. **Parallel batch 4** with S16 (`_FILTER_JS`, js-lowess; DECISIONS A22 swapped S13 and S16 so S13's `map_lfitci`/`map_qfitci` edits do not share S11's batch) and S12 (distribution mappers); merge order 16, 11, 12. **Can run with S16 and S12.** S11 never edits `_FILTER_JS`, `map_histogram`, `map_kdensity`, `map_function`, `map_area`, `map_bar` or `_dash_stale_kind`; S16 reads the `atobs` key S11 writes (TR-11.6 f). Copy-list anchor (R2): S11 appends `"_dash_fit_points_of",` after `"_dash_reference_lines",`; S12, merged after S11, anchors after `"_dash_fit_points_of",` (R2-20).

## Evidence

All anchors at `6370ca4` (dash_render.py 52,280 lines; dash.ado 11,039).

### The names today

dash_parse.mata:6261-6276 (`_dash_rep_und_tab`):
```
    t = t \ ("atobs",        "atobs",        "ato",       "0", fits,        "0", "")
    t = t \ ("xlog",         "xlog",         "xlog",      "0", fits,        "0", "")
    ...
    t = t \ ("ciplot",       "ciplot",       "cip",       "1", cis,         "0", "")
    t = t \ ("fitplot",      "fitplot",      "fitp",      "1", cis,         "0", "")
    t = t \ ("fit",          "fit",          "fit",       "0", cis,         "0", "")
    t = t \ ("fit",          "nofit",        "nofit",     "0", cis,         "0", "no")
    ...
    t = t \ ("smoothplot",   "smoothplot",   "smoothp",   "1", "lpolyci",   "0", "")
```
`fits = "lfit qfit lfitci qfitci fpfitci"`, `cis = "lfitci qfitci lpolyci fpfitci"` (:6255-6256). `estopts`, `predopts`, `estcmd` have no row: they fall through `_dash_foreign_scan` as lower-case words to the note.

### The grid

dash_render.py:20969-21005 `_fit_grid`: `n_pts` from `n()` (default `_FIT_GRID = 100`, :474), `lo, hi` the observed range or `range()`, `np.linspace`. `_fp_grid` (:21007) is fpfit's "no grid: evaluates at the distinct x" and is unaffected by `atobs`.

### The ci line and band

`_render_ci_band` (:12473-12545): `band_r, _outline_r = self._ci_band_glyphs(...)`, then `line_r = _dash_join_glyph(self, fig, options, dict(x=, y=, source=, line_color=, line_width=, legend_label=yvar, ...), role=False)`, `self._ci_line_restyle(line_r, options)`, `self._apply_line_opts(line_r, _nopstyle)`. Every ci mapper returns `[line_r, band_r]`.

### The function-points precedent

dash.ado:8315-8362 `_dash_fn_points raw_sc lo hi n k obj_sc`: refuses a top-level comma, sets `._Gr_Global.callerver`, `preserve` when `_N < n`, `capture twoway__function_gen ... generate(fy fx)`, appends `"<k>":{"x0":..,"dx":..,"y":[..]}` via `_dash_fn_points_json` (dash_parse.mata:5007). The renderer reads `points` in `map_function` (:20567, `points=None` argument; `_dash_function_points(points)` validates). The spec writer attaches them at dash.ado:7029-7052 (`_dash_fn_points` loop) and the renderer's `_dash_attach_function_points` (test_function_expr.py `TestAttach`).

### twoway's rule (research/stata-ground-truth.md §1.3)

- `lfit_parse:52-55` `ATObs n(integer .points) Range(numlist min=2 max=2 missingok) ESTopts(string) PREDopts(string) XTransform(string) XLOG`; `:59-66` refuses `predopts` with `range()` ("may not combine <popts> with range()") and `atobs` with `range()`; `:80-83` `.atobs`, `.points`, `.regress_opts`, `.predict_opts`.
- `lfitci_parse:30-33` `Level(real) STDP STDF STDR FITPlot(string) CIPlot(string) TYPE(string) RECASTas(string) noFIT`; `:50-56` `.fittype`, `.citype`; `:60-62` `.fit = 0`.
- `fpfit_parse:41-51`: `ESTCmd(string)`, `.regress_opts`, `.predict_opts`, `.est_cmd` (default `fracpoly`); `twoway__fpfit_serset.ado:27` `fracpred yhat, predopts`.
- `lpolyci_parse:34-38` `SMOOTHPlot(string) CIPlot(string) FITPlot(string) noFIT`; `:54-58` fitplot/smoothplot both set `.fittype`.
- `twoway__lfit_serset.ado:67-82`: `if !atobs { _gs_x_create, points() x() }` then `predict yhat if touse2, predopts`.

### Fixtures on disk

`test/fixtures/stat_truth.json` (WP-18, fit values), `recast_truth.json` (the recast targets). None carries atobs/estopts truth: `scripts/extract_fit_options_truth.do` is new (Stata truth).

### Pinned tests to flip (never delete)

- test/test_unsupported_report_is_true.py `test_the_blocks_were_actually_found` (:725-726 declared counts 196/85) -- counts move.
- test/test_abbreviations.py `TestNoPrefixIsClaimedTwice` (:406) and the abbrev_truth check (:277) -- the new minimums `ATObs ESTopts PREDopts ESTCmd FITPlot CIPlot SMOOTHPlot noFIT` must not collide (`fit` vs `fitopts`: `FITPlot` minimum `fitp`, `FITOPTS` has no abbreviation; `ESTopts` `est` -- no existing `est*`).
- test/test_help_claims_1.cscript / dash.sthlp:734-736, :775-779: "`(lfit mpg weight), atobs` ... `option atobs not allowed`" -- a second copy is still refused (now by `_dash_rep_unique`), so the claim stays true; 11-04 re-reads the sentence and keeps it.
- test/test_help_conformance.py `TestTheUnsupportedSectionIsTrue` -- no Unsupported entry names these today (GAPS3 J1), so nothing is removed from the list; the Statistical Layer Options paragraph is rewritten (R3: S11 owns dash.sthlp:3210-3211 and its new `{ul:Fit options.}` paragraph; the shared sentence at :2908-2912 is S12's, merged last in batch 4, which writes the final text with S11's clause "atobs, estcmd(), estopts() and predopts()" removed, R2-21).

## User stories

- US-11.1 As a Stata user pasting `twoway lfitci mpg weight, nofit`, I want only the band drawn, so that my figure matches twoway's.
- US-11.2 As a Stata user, I want `lfit mpg weight, atobs` evaluated at my observations, so that a sparse x draws the same vertices twoway draws.
- US-11.3 As a Stata user, I want `lfit mpg weight, estopts(noconstant)` and `fpfit mpg weight, estopts(degree(3))` fitted by Stata's own `regress`/`fracpoly`, so that the numbers are Stata's.
- US-11.4 As a Stata user, I want `lfitci ..., fitplot(scatter) ciplot(rcap)` drawn as markers and caps, so that twoway's recast forms work.
- US-11.5 As a dashboard user, I want to be told when a layer is drawn as registered and will not refit after a filter move (M8).

## Business requirements

- BR-11.1 `nofit` draws no fit line and keeps the band and the band's key; given on a type outside lfitci qfitci fpfitci lpolyci it is refused with twoway's words.
- BR-11.2 `atobs` evaluates the fit at the observed x; `atobs` with `range()` is refused `may not combine atobs with range()` r(198).
- BR-11.3 `estopts()`, `predopts()`, `estcmd()` give Stata's own fitted values; `predopts()` with `range()` is refused with twoway's words; a malformed value is refused before any data are touched.
- BR-11.4 `fitplot()`/`ciplot()`/`smoothplot()` draw the named target; an unknown name prints twoway's two notes and draws the default.
- BR-11.5 Nothing is printed for any honoured option (Q36); the saved page and the served app carry the frozen cue for a `points` layer.

## Technical requirements

- TR-11.1 **Declare** in `_dash_parse_plot_opts` syntax (dash.ado:1167-1239), after `STDR MEan NOWeight ///` (:1200): `ATObs ESTopts(string asis) PREDopts(string asis) ESTCmd(string) FITPlot(string) CIPlot(string) SMOOTHPlot(string) noFIT ///`. `sreturn local atobs/estopts/predopts/estcmd/fitplot/ciplot/smoothplot/fit : copy local ...` after `sreturn local stdp` (:1524). JSON keys appended to `_dash_plot_opts_to_json`'s list (:4441-4458) after `pwidth lpvar`: `atobs estopts predopts estcmd fitplot ciplot nofit`. `s(fit)` holds `nofit` when given; the JSON key is `nofit` with value `nofit` (write `local nofit : copy local fit` before the loop). None is a stylelist key; none is dropped by `p()`.
- TR-11.2 **Delete** the `_dash_rep_und_tab` rows `atobs`, `ciplot`, `fitplot`, `fit`, `nofit`, `smoothplot` (dash_parse.mata:6261, 6273-6276, 6283); add `"atobs", "estopts", "predopts", "estcmd", "fitplot", "ciplot", "smoothplot", "fit"` to `_dash_rep_unique`'s list (:6207-6214) -- twoway's `_parse combop ... rightmost` for FITType/CIType means a second `fitplot()` is NOT refused (lfitci_parse:27-29): so `fitplot`, `ciplot`, `smoothplot`, `estopts`, `predopts`, `estcmd` do NOT join `_dash_rep_unique`; only `atobs` and `fit` do (measured U11-01). Keep `xlog`.
- TR-11.3 **Exclusivity** in `_dash_process_segment` after the logit refusal (:5556-5563): `atobs` + `range()` → `display as error "may not combine atobs with range()"`, `exit 198`; `predopts()` + `range()` → `may not combine <predopts as typed> with range()`; `fitplot()` and `smoothplot()` together on lpolyci → the rightmost wins (combop rightmost), no refusal.
- TR-11.4 **`_dash_fitplot_opt ptype`** (new sclass program after `_dash_recast_named`, :2665-2671): canonicalises `s(fitplot)` through `_sp_yx` (class yxtype) and `s(ciplot)` through `_sp_yx _sp_rng` (class y2xtype) with the loop of `_dash_recast_opt` :2606-2615 extracted into a Mata helper `_dash_recast_canon(name, spellings)` (returns the full name or ""); an unknown name prints the two `_dash_note` lines (:2622-2623 form) and clears the key. Add both to `_dash_require_mata`'s `_needed` list (dash.ado:448-479, alphabetical) and the dash_parse.mata header index; `test/program_coverage_map.py` entries `"_dash_fitplot_opt": ("test_wp31_truth.cscript:U11-04",)`, `"_dash_recast_canon": ("test_wp31_truth.cscript:U11-04",)`.
- TR-11.5 **`_dash_fit_points ptype yvar xvar wexp ifin k obj_sc`** (new, after `_dash_fn_points`): when `s(estopts)`, `s(predopts)` or `s(estcmd)` is non-empty on lfit/qfit/lfitci/qfitci/fpfit/fpfitci: refuse a value holding a top-level `;`, a backtick, `$`, a newline or carriage return (`strpos("`macval(v)'", char(10))`, `char(13)`) or an unbalanced quote (`_dash_fn_stray_close`) with `option estopts() incorrectly specified` r(198) (the option as typed, never the value) -- reuse `_dash_fn_points`'s predicate (dash.ado:8319-8340) verbatim, extended by the two control characters (R2-34); `preserve`; `capture twoway__lfit_serset yvar xvar [wexp] if/in, points(n|atobs) estopts() predopts() level() std` for the lfit family (read `twoway__lfit_serset.ado:1-30` for its exact syntax before writing the call; the ci columns are `lo hi`), `capture twoway__fpfit_serset` for fpfit/fpfitci; on error echo `error in <estcmd>: ` + the generator's message through `_dash_say`, `exit rc`; store the serset columns as `"<k>":{"x":[..],"y":[..],"lo":[..],"hi":[..]}` through a new Mata `_dash_fit_points_json(sersetid|vars)` (mirror `_dash_fn_points_json`, :5007: `%21.17g`, missing as `null`). Called from `_dash_plot` beside the `_dash_fn_points` loop (:7029-7052) and attached in the renderer by the same path as function points (`_dash_attach_function_points`, which S11 generalises to read `points` for every plot type -- edit its one `ptype == "function"` test to `ptype in _DASH_FIT_TYPES | {"function"}`).
- TR-11.6 **Renderer.** (a) `_fit_grid`: `if str(options.get("atobs","")).strip(): return np.unique(np.asarray(x, float))` before the `n_pts` line. (b) Six mappers: at the top, `pts = _dash_fit_points_of(options)` (new module-level helper: validates `options.get("points")` as `{"x":[...],"y":[...]}` of equal finite-or-null lengths ≤ 100,000, returns `(x, y, lo, hi)` arrays or None); when not None, skip the fit and build the ci_source/line source from them, then `_render_ci_band`/`fig.line` as today, and RETURN from the mapper before S10's `_dash_agg_source`/`_dash_agg_config`/`_dash_agg_rows` tagging lines (map_lfit/map_qfit after batch 3) and before the tagging S13/S28 add later: a `points` renderer carries NO `_dash_agg_*` attribute, so `render()` step 3b never registers it and the JS never refits it (DECISIONS A20, R2-08). Mark the renderers frozen: set `r._dash_points_frozen = True` on each, and in `_make_figure_body`'s `_frozen_layer_tag` call site (:44049-44060) add, after the computed-only tagging, `for _fr in <the layer's renderers>: if getattr(_fr, "_dash_points_frozen", False): _fr._dash_frozen = _frozen_layer_tag(..., kind="fit")` -- `_frozen_layer_tag` (:43040) gains the keyword `kind=None` defaulting to `_dash_stale_kind(ptype, options)` (lines +12..14 return None when the kind is None; the forced "fit" bypasses that) -- `_make_figure_body` is not edited by S12 or S16 (owner table batch 4), so S11 is its one editor. `TestEstoptsPoints::test_saved_page_marks_it_frozen` is parametrised over `lfit` and `lfitci` (lfit is the type whose kind S10 made None). (c) `nofit`: in `_render_ci_band` after `_dash_join_hide`, `if str(options.get("nofit","")).strip(): line_r.visible = False; line_r.muted = True` and build the line with `legend_label=None` (the key is the band's, as twoway keys a nofit ci). (d) `fitplot`: when `options.get("fitplot")` names a `_RECAST_DRAWN` target, draw the line through `self._dash_draw_xy_as(fig, source, x_col, y_col, target, {k:v for k,v in options.items() if k not in ("fitplot","ciplot","recast","type")}, color_idx)` instead of `_dash_join_glyph`; `ciplot`: when it names a range target, draw the band through new `GlyphMapper._dash_draw_range_as(fig, source, xcol, locol, hicol, target, options, color_idx)` which calls `_dash_glyph_dispatch(self)[1][target](fig, pts, "y1", "y2", "x", opts, view=None, color_idx=color_idx)` on a fresh source `{"x","y1","y2"}`; `_dash_draw_range_as` is a method (no copy-list entry, R2). (e) `_dash_fit_points_of` is module-level: copy-list functions tuple after `_dash_reference_lines` (:47223) (R2; S12 anchors after S11's entry); (f) `atobs` on the saved page: in map_lfit and map_qfit the `_fit_agg_config(...)` call S10 added gets `cfg["atobs"] = bool(str(options.get("atobs", "")).strip())` (a type-specific key under D-10.a; S16 reads it in `dash_fit_grid`, section-16 TR-16.11); S11 does not edit `_FILTER_JS`; `test/function_test_map.py` entries `'_dash_fit_points_of': 'test/test_fit_options.py::TestEstoptsPoints::test_points_are_drawn_as_stored'`, `'GlyphMapper._dash_draw_range_as': 'test/test_fit_options.py::TestCiplot::test_ciplot_rcap_draws_caps[saved]'`.
- TR-11.7 **Served cue** (D-11c): in the served template's `_dash_draw_layer` (:49137-49225) no edit; the note is raised by the mapper through `_dash_warn_once(("fit-points", gname, idx), "dash: <type> with estopts()/predopts()/estcmd() is drawn as registered; a filter move does not refit it")`, which both modes surface as every other layer note.
- TR-11.8 **Tests/pins:** test_unsupported_report_is_true.py `LIVE_VALUES` entries: `"atobs": ({"atobs":"atobs"}, {}, "lfit", {})`, `"nofit": ({"nofit":"nofit"}, {}, "lfitci", {})`, `"fitplot": ({"fitplot":"scatter"}, {"fitplot":"line"}, "lfitci", {})`, `"ciplot": ({"ciplot":"rcap"}, {"ciplot":"rarea"}, "lfitci", {})`, `"smoothplot": ({"smoothplot":"scatter"}, {"smoothplot":"line"}, "lpolyci", {})`, `"estopts"`, `"predopts"`, `"estcmd"` in `NOT_IN_FILE`-style classification: they change the spec only through `points`, so classify them in `LIVE_VALUES` with a hand-written `points` pair: `"estopts": ({"estopts":"noconstant","points":{"x":[1,2],"y":[1,2]}}, {"estopts":"noconstant","points":{"x":[1,2],"y":[2,4]}}, "lfit", {})` and the same shape for `predopts` and `estcmd`. Declared plot count moves by +8: recount with the file's `_declared_plot_options()` helper at the section's base (196 at 6370ca4; S04's batch-1 edits may have moved it) and write `# <measured old> -> <measured old + 8>: C4 atobs estopts predopts estcmd fitplot ciplot smoothplot nofit declared` (A33). `FLAGS` gains `"atobs", "nofit"`.

## Boundaries

- No edit to `_FILTER_JS`, `js_runner.py`, `_dash_stale_kind`, `test_saved_stale_cue.py` (S16 owns them in batch 4, A22); the `atobs` JS read is S16's (TR-11.6 f).
- No edit to the shared help sentence dash.sthlp:2908-2912 (S12 writes its final text, R2-21).
- No edit to `map_histogram`, `map_kdensity`, `map_function`, `map_area`, `map_bar` (S12).
- `xlog`, `xtransform()` untouched (D-11e). `type()`/`recast()` refusal on ci types untouched (dash.ado:2561-2566).
- No numpy reimplementation of `estopts()` (D-11b). No new dependency (M22).

## Stata truth

New `scripts/extract_fit_options_truth.do` → `test/fixtures/fit_options_truth.json` (header, root guards, `adopath ++`, `global dash_nobrowser 1`, `shell git -C ... rev-parse HEAD > git_head.txt`, `_meta` as scripts/extract_default_base_truth.do:21-60, 147-186). On `sysuse auto`:
- `F01`: `twoway lfit mpg weight, atobs name(f1)` → `.f1.plotregion1.plot1.serset` x values (`serset` dump via `_dash_serset_values`-style python read of `.Graph.plotregion1.plot1.serset.sers[1]` -- read the serset with `serset use`/`serset summarize`, write x and y arrays).
- `F02`: `twoway lfit mpg weight, estopts(noconstant)` serset y at n(3); `F03`: `twoway fpfit mpg weight, estopts(degree(3))`; `F04`: `twoway lfitci mpg weight, predopts(stdp)`.
- `F05..F08` refusals: `capture noisily twoway lfit mpg weight, atobs range(1000 5000)` (rc, message line); `predopts(stdp) range(1 2)`; `atobs atobs`; `nofit nofit` (rc 0 expected: combop? no -- `noFIT` is a plain syntax flag, so twice is r(198) `option nofit not allowed`; measured, not assumed).
- `F09`: `lfitci mpg weight, nofit` → `.plot1.fit` = 0 and the plot count; `F10`: `lfitci ..., fitplot(scatter) ciplot(rcap)` → `.plot1.fittype`, `.plot1.citype`, and `.plot1.view.style` names; `F11`: `fitplot(bogus)` → the two notes' text and rc.
Run: `DASH_REPO=<repo> scripts/stata_slot.sh <scratch> <repo>/scripts/extract_fit_options_truth.do`; `git add -f test/fixtures/fit_options_truth.json`; add the name to test_fixtures_are_committed.py's list.

## TDD test stubs

New file `test/test_fit_options.py` (red at 6370ca4 unless marked guard):
- Test: `_fit_grid(x, {"atobs":"atobs"})` equals `np.unique(x)` and `lfit` draws F01's x values in both modes -- `TestAtobs::test_grid_is_the_observed_x[mode]` (red).
- Test: `nofit` leaves `[line_r, band_r]` with `line_r.visible is False` and no legend item for the line, band kept, both modes -- `TestNofit::test_line_hidden_band_kept[mode]` (red); on lpolyci too -- `::test_lpolyci[mode]` (red).
- Test: `fitplot(scatter)` draws a Scatter for the fit, `ciplot(rcap)` a spine + two `dash_cap` renderers, in both modes -- `TestFitplotCiplot::test_fitplot_scatter[mode]`, `::test_ciplot_rcap_draws_caps[mode]` (red); `smoothplot(line)` on lpolyci -- `::test_smoothplot_is_fitplot[mode]` (red).
- Test: a spec with `points` draws exactly those points, no fit computed (`_dash_wls` not called: monkeypatch raises) -- `TestEstoptsPoints::test_points_are_drawn_as_stored[mode]` (red); a malformed `points` draws the layer empty with the note (`_mark_needs_points` words) -- `::test_bad_points_note` (red); the saved page tags the layer frozen with kind "fit" and the " (unfiltered)" suffix, and the renderer carries no `_dash_agg_config` -- `::test_saved_page_marks_it_frozen[lfit|lfitci]` (red; lfit is the case S10's refit would otherwise take); the served app draws the stored points after a move and the note text appears once -- `::test_served_move_keeps_points` (red).
- Test: the fixture matches: F02/F03/F04 y values equal what `_dash_fit_points_of` returns from the spec `dash` writes (read via the cscript's saved spec file) -- `TestTheFixture::test_meta_and_values` (guard on the fixture; the spec comparison is U11-03's).
- Test: `_dash_fit_points_of` is on the served copy list -- `TestTheServedCopy::test_names_defined` (red).
- Test: `estopts("a`=char(10)'b")` and a value holding `char(13)` are refused r(198) by the ado predicate (U11-06's second and third cases) and `map_lfit`'s config carries `atobs: True` under `atobs` -- `TestAtobs::test_config_key` (red).
- Test: dash.ado declares the eight, the pending blocks name none, `_dash_rep_und_tab` has no `atobs|ciplot|fitplot|fit|smoothplot` row -- `TestTheAdoText::test_declared_not_pending` (red).

cscript cases, block `* ==== S11 C4: fit options ====` in test/test_wp31_truth.cscript (R1):
- U11-01 `atobs atobs` → rc 198 `option atobs not allowed` from dash and twoway alike; `fitplot(scatter) fitplot(line)` → rc 0 both, dash draws line (rightmost).
- U11-02 `lfit mpg weight, atobs range(1000 5000)` → dash rc = twoway rc (198), dash's message line equals twoway's (`cert_log_has`).
- U11-03 `dash lfit mpg weight, estopts(noconstant) name(u11c)` then `_dash_serve_spec, specpath() datapath()`: the spec's `points.y` equals F02's serset y to 1e-10; same for fpfit `estopts(degree(3))` vs F03.
- U11-04 `fitplot(bogus)`: dash prints the two notes twoway prints (`cert_log_has` each) and rc 0; `_dash_recast_canon("rsc", "<_sp_rng>")` returns `rscatter` (direct Mata call).
- U11-05 `lfitci mpg weight, nofit` → python render: one visible renderer among `[line, band]` in both modes.
- U11-06 `estopts("x; shell rm -rf")` (literal text with a semicolon) → rc 198, `option estopts() incorrectly specified`, nothing registered (`graph dir`/dash registry unchanged).
Area-script refusals (test_option_validation.cscript, prefix U11): U11-07 `scatter mpg weight, nofit` → rc 198 `option nofit not allowed` (S04's table), compared with `capture noisily twoway`.

Parity: test_mode_parity.py CORPUS appends `_case("lfitci nofit", [plot_for("lfitci", {"nofit":"nofit"})])`, `_case("lfitci fitplot(scatter) ciplot(rcap)", [...])`, `_case("lfit atobs", [...])`; MOVE_CORPUS appends `_case("lfit with points after a move", [plot_for("lfit", {"estopts":"noconstant","points":{...}})])` (R8).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| atobs grid | pytest TestAtobs; U11-01/02 | fit_options_truth F01, F05 | yes |
| nofit | pytest TestNofit; U11-05 | F09 | yes |
| fitplot/ciplot/smoothplot | pytest TestFitplotCiplot; U11-04 | F10, F11 | yes |
| estopts/predopts/estcmd points | pytest TestEstoptsPoints; U11-03, U11-06 | F02-F04 | yes (frozen cue) |
| refusals | U11-02, U11-07 | F05-F08 | n/a |
| copy list, ado text | pytest TestTheServedCopy, TestTheAdoText | -- | -- |

AC-11.1 every red stub above is green after 11-03; AC-11.2 U11-01..07 PASS under the console binary; AC-11.3 `grep -c "atobs\|nofit\|fitplot\|ciplot\|estopts\|predopts\|estcmd" <(sed -n 1320,1400p dash.ado)` = 0 and the help's Unsupported section still lists none (nothing to remove) while :3210-3211 no longer says fpfit's degree is not honoured (the :2908-2912 sentence is S12's to rewrite, R2-21); AC-11.4 TWOWAY_COVERAGE_AUDIT.md rows 29, 87, 89, 92 carry the `[WP-31 C4, commit pending: corrected -- ...]` annotation (the merger fills the sha at k.3b, A11).

## Tasks

**Commit boundary.** 11-01..11-03 are steps; 11-04 makes the one commit `Draw the fit options atobs, nofit, fitplot(), ciplot() and run estopts()/predopts()/estcmd() through Stata (WP-31 C4)` on branch `wp31-s11`.

<task type="auto" id="11-01">
  <name>Write the failing fit-option tests and the truth extractor</name>
  <files>test/test_fit_options.py, scripts/extract_fit_options_truth.do, test/test_fixtures_are_committed.py</files>
  <action><![CDATA[Create scripts/extract_fit_options_truth.do from scripts/extract_default_base_truth.do's skeleton (lines 1-60 root guards, 147-186 the python writer with _meta) measuring probes F01-F11 of this file's "Stata truth" section; run it with `DASH_REPO=<repo> scripts/stata_slot.sh <scratch> <repo>/scripts/extract_fit_options_truth.do`; `git add -f test/fixtures/fit_options_truth.json`; add "fit_options_truth.json" to test_fixtures_are_committed.py's list after "default_base_truth.json". Create test/test_fit_options.py with every stub of "TDD test stubs" (classes TestAtobs, TestNofit, TestFitplotCiplot, TestEstoptsPoints, TestTheFixture, TestTheServedCopy, TestTheAdoText; mode parametrised "saved"/"served" through test_mode_parity's helpers `_render_saved`/`_render_served`). Run `python3 -m pytest test/test_fit_options.py -q -p no:randomly > <scratch>/11-01-failure.txt; true` against the unmodified tree. Do not commit.]]></action>
  <verify><![CDATA[grep -c "FAILED" <scratch>/11-01-failure.txt prints a number >= 12; grep -c '"_meta"' test/fixtures/fit_options_truth.json prints 1; python3 -c "import json;d=json.load(open('test/fixtures/fit_options_truth.json'));print(sorted(d['_meta']))" prints ['born_date', 'dash_commit', 'extracted', 'source', 'stata_version'].]]></verify>
  <done>The regression tests exist and fail against 6370ca4, and the twoway truth fixture is committed with its provenance.</done>
</task>

<task type="auto" id="11-02">
  <name>Declare the eight options and add the Stata fit-points program</name>
  <files>dash.ado, dash_parse.mata, test/program_coverage_map.py</files>
  <action><![CDATA[In dash.ado: add `ATObs ESTopts(string asis) PREDopts(string asis) ESTCmd(string) FITPlot(string) CIPlot(string) SMOOTHPlot(string) noFIT ///` after line 1200 (`STDR MEan NOWeight ///`); add the eight `sreturn local` lines after :1524 (`sreturn local stdp`), with `sreturn local nofit : copy local fit`; append `atobs estopts predopts estcmd fitplot ciplot smoothplot nofit` to the `foreach key in` list at :4441-4458 after `pwidth lpvar`; add the exclusivity block of TR-11.3 after :5563; add program `_dash_fitplot_opt` (TR-11.4) after `_dash_recast_named` (:2671) and call it in `_dash_process_segment` right after `_dash_recast_opt` (:5516) with `_dash_fitplot_opt `ptype''; add program `_dash_fit_points` (TR-11.5) after `_dash_fn_points` (:8362) and call it from `_dash_plot` in a loop beside the `_dash_fn_points` loop at :7029-7052 for every plot whose type is in `lfit qfit lfitci qfitci fpfit fpfitci` and whose s(estopts)/s(predopts)/s(estcmd) is non-empty; append `_dash_recast_canon` and `_dash_fit_points_json` to `_dash_require_mata`'s `_needed` list (:448-479) in alphabetical place. In dash_parse.mata: delete the six `_dash_rep_und_tab` rows (TR-11.2); add "atobs", "fit" to `_dash_rep_unique`'s anyof list (:6207-6214) with the comment `// WP-31 C4: atobs and nofit are plain flags twoway takes once; fitplot()/ciplot()/smoothplot()/estopts()/predopts()/estcmd() are rightmost-wins (combop) and are NOT here`; add `_dash_recast_canon(string scalar name, string scalar spellings)` (the loop of dash.ado:2606-2615 as Mata) and `_dash_fit_points_json` (mirror of :5007 writing x, y, lo, hi arrays); list both in the header index (lines 1-420). Add the two program_coverage_map.py entries of TR-11.4 and `"_dash_fit_points": ("test_wp31_truth.cscript:U11-03",)`, `"_dash_fit_points_json": ("test_wp31_truth.cscript:U11-03",)`.]]></action>
  <verify><![CDATA[python3 -m pytest test/test_fit_options.py::TestTheAdoText test/test_unsupported_report_is_true.py test/test_abbreviations.py test/test_program_coverage_map.py -q prints "passed" with 0 failed after the test_unsupported counts are moved in 11-03 (run again then); `grep -c "program define _dash_fit_points" dash.ado` prints 1; `grep -c '"atobs"' dash_parse.mata` prints 1 (the _dash_rep_unique entry only).]]></verify>
  <done>dash.ado declares, validates and stores the eight options and runs estopts()/predopts()/estcmd() through twoway's own serset generators at registration.</done>
</task>

<task type="auto" id="11-03">
  <name>Draw the options in both renderers</name>
  <files>dash_render.py, test/function_test_map.py, test/test_unsupported_report_is_true.py</files>
  <action><![CDATA[In dash_render.py apply TR-11.6 (a)-(e) and TR-11.7: `_fit_grid` atobs branch before `n_pts` (:20993); the `points` branch at the top of map_lfit (:16244), map_qfit (:16340), map_lfitci (:16421), map_qfitci (:16550), map_fpfit (:17684), map_fpfitci (:17765) using the new module-level `_dash_fit_points_of(options)` placed right after `_dash_range_pair` (:20933-20967) and added to the functions copy tuple after "_dash_reference_lines" (:47223); `nofit` in `_render_ci_band` after `_dash_join_hide(line_r, options)` (:12543) with `legend_label=None` when nofit; `fitplot`/`ciplot`/`smoothplot` routing in `_render_ci_band` (read `options.get("fitplot") or options.get("smoothplot")`) through `_dash_draw_xy_as` and the new method `GlyphMapper._dash_draw_range_as` placed after `_dash_draw_xy_as` (:20693-20730); the frozen tag OR-in at `_make_figure_body` :44049-44060. Generalise `_dash_attach_function_points` to attach `points` for the fit types too. Add the function_test_map.py entries of TR-11.6 (e). Add TR-11.6 (f)'s `atobs` config key in map_lfit and map_qfit. In test_unsupported_report_is_true.py apply TR-11.8 (LIVE_VALUES entries, FLAGS, the declared plot count re-measured at the base and moved by +8 with the comment, A33). Run `python3 -m pytest test/test_fit_options.py test/test_unsupported_report_is_true.py test/test_function_test_map.py test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName test/test_mode_parity.py -k "nofit or fitplot or atobs or points" -q`.]]></action>
  <verify><![CDATA[The pytest line prints "passed" and "0 failed"; `python3 -c "import dash_render as d;print(callable(d._dash_fit_points_of))"` prints True; `grep -c "_dash_fit_points_of" dash_render.py` prints >= 8 (definition, six mappers, copy list).]]></verify>
  <done>Both renderers draw atobs, nofit, fitplot(), ciplot(), smoothplot() and stored estopts()/predopts()/estcmd() points, with the frozen cue in both modes.</done>
</task>

<task type="auto" id="11-04">
  <name>Certify, document and commit C4</name>
  <files>test/test_wp31_truth.cscript, test/test_option_validation.cscript, dash.sthlp</files>
  <action><![CDATA[Append block `* ==== S11 C4: fit options ====` (cases U11-01..U11-06, WP-30 form: `local only : env WP31_ONLY`, gate on `w31_run`, start/end display lines, `* ==== end S11 ====`) above `* ==== append new blocks above this line ====` in test/test_wp31_truth.cscript, and U11-07 in test/test_option_validation.cscript's last block. Run the two scripts through drivers: `printf 'global dash_nobrowser 1\ncd "%s/test"\ndo "%s/test/%s"\n' "<repo>" "<repo>" "test_wp31_truth.cscript" > <scratch>/run_wp31.do; WP31_ONLY=S11 scripts/stata_slot.sh <scratch> <scratch>/run_wp31.do` and the same for test_option_validation.cscript. Leave dash.sthlp:2908-2912 untouched (S12, merged last in batch 4, writes the final sentence with the clause "atobs, estcmd(), estopts() and predopts() on the fits" removed, R2-21); add, directly after that sentence's paragraph, one paragraph `{phang}{ul:Fit options.} {opt atobs} evaluates lfit, qfit, lfitci, qfitci and fpfitci at the observed x; {opt nofit} draws the band alone; {opt fitplot(plottype)}, {opt ciplot(plottype)} and lpolyci's {opt smoothplot(plottype)} draw the line and the band as the named type; {opt estopts(string)}, {opt predopts(string)} and {opt estcmd(cmd)} are run by Stata when the graph is registered, so the layer is drawn as registered and does not refit after a filter move -- the saved page and the served app say so.`; rewrite :3210-3211 to say `estopts(degree(#))` is honoured. In TWOWAY_COVERAGE_AUDIT.md append `[WP-31 C4, commit pending: corrected -- atobs, nofit, fitplot(), ciplot(), estopts(), predopts(), estcmd() drawn]` to rows 29, 87, 89 and 92. Close the BUGS.md entry for C4 (Resolution form of BRIEF, naming the forced "fit" kind and both modes' cue, D3), rewrite the GAPS3 line to `- **C4 Tracked:** Closed in WP-31, BUGS.md "<C4 title>", commit pending.` (A11: the merger's step k.3b fills the sha; the audit, BUGS.md, GAPS3.md and CHANGELOG.md are the closing task's implied files, A13), replace the `<!-- WP-31 C4 -->` markers (a Results line: "lfit mpg weight, atobs: evaluated at the 74 observed x (was: a 100-point grid)"; a Changed-behaviour line: "atobs range() and predopts() range() are refused, twoway's `may not combine ...`"). Run `python3 -m pytest test/test_fit_options.py test/test_help_conformance.py test/test_help_claims_1.py test/test_tracking_documents.py -q`; commit with the body forms of BRIEF (failure text from <scratch>/11-01-failure.txt; Regression/Flipped/Fixture/BUGS.md/GAPS3 lines); grep the message for `claude|anthropic` before and after.]]></action>
  <verify><![CDATA[The two Stata logs contain "U11-01 PASS" .. "U11-07 PASS" and no " FAIL"; the pytest line prints 0 failed; `git log -1 --format=%s` prints a subject ending "(WP-31 C4)"; `git log -1 --format=%B | grep -ci "claude\|anthropic"` prints 0; `grep -c "C4 Tracked:\*\* Closed in WP-31" GAPS3.md` prints 1.]]></verify>
  <done>C4 is closed in one commit with its tests, fixture, help, audit, BUGS.md entry, GAPS3 Tracked line and CHANGELOG lines.</done>
</task>

## Section completion criteria

- All stubs green; U11-01..07 PASS; no test deleted; counts moved with comments.
- `_dash_fit_points_of` on the copy list; `_dash_fit_points`, `_dash_fitplot_opt`, `_dash_recast_canon`, `_dash_fit_points_json` in `_needed`, the Mata header and program_coverage_map.py.
- Help :3210-3211 rewritten and the `{ul:Fit options.}` paragraph added (:2908-2912 is S12's); audit rows annotated; BUGS/GAPS3 (`commit pending`)/CHANGELOG closed in the commit; `points` renderers carry no `_dash_agg_*` attribute and are tagged kind "fit"; map_lfit/map_qfit configs carry `atobs`.

## Notes

- **Renderer order:** `_render_ci_band` draws fill, outline, line; `nofit` hides the line AFTER `_apply_line_opts` so a later style edit cannot un-hide it.
- **Copy list (R2):** `_dash_fit_points_of` after `_dash_reference_lines` in the functions tuple (:47223); S12 (merged after S11 in batch 4) anchors its entries after `"_dash_fit_points_of",`. `_dash_draw_range_as` is a method: no entry.
- **Fixture rule (R7):** `fit_options_truth.json` is never hand-patched; regenerate with the extractor.
- **python_exec hazard** (project memory): many concurrent sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`; the extractor exits 601 with the message if `c(python_exec)` is empty -- rerun after the slot is free.
- **Security:** the estopts/predopts/estcmd text never reaches the command line except through `macval()` inside `capture twoway__*_serset`, after the semicolon/backtick/quote checks; the spec stores numbers only (`points`); the renderer validates `points` and never evals text.
- **Merge rules cited:** R1 (one truth script), R2 (copy list), R6 (`_needed`), R8 (CORPUS append), R9 (flips), R10 (counts), R12 (S11 is batch 4's `_make_figure_body` editor for the forced-kind tagging loop; S16 owns `_FILTER_JS` and reads the `atobs` key, A22). R3: the :2908-2912 sentence is S12's (R2-21).
- **Commit body lines:** `Regression: test/test_fit_options.py::TestNofit::test_line_hidden_band_kept[saved] -- failed at 6370ca4 with <text>`; `Fixture: test/fixtures/fit_options_truth.json (scripts/extract_fit_options_truth.do)`; `BUGS.md: "<C4 title>" (closed)`; `GAPS3: C4 Tracked`.
- **Decisions:** D-11b/D-11c are CONFIRMED by maintainer decision D3 (frozen in both modes with the existing stale cue after a move; no sfi call at move time); D-11e (xlog/xtransform stay named) is for ratification.
- **Hand-off to S16 (same batch):** the `atobs` config key (TR-11.6 f) is read by S16's `dash_fit_grid` edit (section-16 TR-16.11); default-safe when absent, so the two worktrees merge in either order.
