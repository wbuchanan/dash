# Section 46: Estimator, function, recast and data-join edges

> Part of: WP-31 · GAPS3 rows: C11, C12, C16, G6, G7, F5 · Risk: yellow · Batch: 15 · Depends on: 01 · Blocks: -- · Tasks: 4, 6 commits · Case-id prefix: U46

## Overview

**What is wrong today.** GAPS3 C11 (GAPS3.md:130): "lpoly edges: gaussian weights below 1e-14 counted toward the two-observation rule (3 vs 23 points), round-off cases D1-D5, `pwidth(0)` and `pwidth(+800)` rc differences; lpoly with its own `if` on five rows draws an empty line (twoway unmeasured)." C12 (:131): "`function` under `by()` evaluated once, twoway once per panel; a malformed y-form echoed as typed." C16 (:135): "A recast kdensity or histogram is marked stale after a move where the un-recast one is recounted." G6 (:231): "Fractional %t values floored on load (twoway unmeasured); join-order edge cases (rarea one bound missing, tied sort keys, connected markers under sort)." G7 (:232): "`%d`/`%tb` axis formats drawn `%9.0g` with a note; `xvarformat(bogus)` noted (twoway: 'bogus not found')." F5 (:212, NEW): "`map_qfitci` docstring still describes a 500-resample bootstrap; the code is analytic (bootstrap only on LinAlgError). The header comment at :364-381 narrates fpfitci's former bootstrap. `_dash_fold_typed`'s comment says line types are always joined in x order (false since WP-29)."

Anchors corrected at 6370ca4 (REVIEW-3e F22): `map_rarea` is :18421 (not :18494); the `_dash_fn_points` program is dash.ado:8315 (its comment from :8280); `_frozen_layer_tag` (:43040) and `_collect_frozen_layers` (:43078) are DashRenderer METHODS, not module functions. Register detail (DROPIN-REMAINING P2.36): "twoway counts a gaussian weight toward the two-observation rule only above about 1e-14, so `lpoly mpg weight, kernel(gaussian) bwidth(1)` draws 3 points in Stata and 23 in dash (SD-10); exact fits differ where Stata's round-off decides (D1 `ylin=2*weight+1` degree 0, D2 `yw=weight` degree 0/1, D3 `mpg*1e-150` degree 2: a zero line); lpolyci rows whose pilot has no residual degrees of freedom are pinched where Stata is often missing (D4), and the pilot's round-off moves the se at 2 of 50 rows of `r1000_d2_bw600` (D5); `if _n==1, pwidth(0)` is refused r(198) where twoway counts first, r(2001) (D6); invalid-option messages name the option in dash's words (D7); `pwidth(+800)` is accepted where twoway gives r(3000) (D8)." P2.37: lpoly with its own `if` on five rows draws an empty line. P2.31: function under by() once (FX-24); malformed y-form echoed as typed. P2.90: recast density/histogram stale after a move. P2.32: fractional period values floored on load. P2.30: rarea one bound missing (O1), tied keys, connected markers under sort (O6). P2.63: `%d`/`%tb` and `xvarformat(bogus)`.

**After this section**: `_compute_lpoly_fit` counts a weight toward the two-observation rule only above the measured threshold (twoway's 3 points); each of D1-D8 is matched where the rule is readable (D6's order of checks, D7's words, D8's rc) and documented where it is Stata's round-off (D1-D3, D5) with the measured values; lpoly on five rows draws what twoway draws; a `function` layer under `by()` with a per-panel range is evaluated per panel by twoway's generator and the malformed y-form message is twoway's token; a recast histogram or kdensity is recounted after a saved move (tagged like the un-recast one, with a `recast` key the JS branch writes as x/y) and never marked stale; fractional `%t` values are drawn where twoway draws them (measured); rarea with one bound missing on a row keeps the other bound as twoway's polygon does (measured); `%d` is read as `%td`, `%tb<cal>` is written as the calendar's `%td` dates through a dash.ado-written calendar map, and `xvarformat(bogus)` is refused with twoway's words; the three stale comments are true.

**Why these rows share a section.** Six small, independent edges of the computed layers and the data join; the index names S46 the batch-15 owner of "lpoly/function/stale-kind edges" and, by R12, of `_FILTER_JS` for batch 15 (S45 edits `_DASH_AXIS_FINISH_JS` only; S44 no JS).

**Test order and commit rule.** Six cycles, one commit per row, in the order F5 (comments; no behaviour), C16, C11, C12, G6, G7. 46-01 measures, writes the six per-row regression test files (DECISIONS A14: test/test_comments_true.py (F5), test/test_recast_refit.py (C16), test/test_lpoly_edges.py (C11), test/test_function_panels.py (C12), test/test_data_join_edges.py (G6), test/test_date_format_edges.py (G7)) and ONLY the first truth block (C16's: F5 compares nothing with twoway and has no block), and never commits; 46-02 commits F5 and C16; 46-03 commits C11 and C12; 46-04 commits G6 and G7 and hands back. Each row's closing step appends its own truth block (A14) and stages only its own test file; every Tracked line it writes reads `commit pending` (DECISIONS A11; the merger's step k.3b fills the sha; no amend).

### Section decisions (binding on the executor)

- **D-46a. The lpoly weight threshold is measured, not assumed.** U46-02 records, for `lpoly mpg weight, kernel(gaussian) bwidth(1) n(50)`, the grid points where Stata's `lpoly` returns a non-missing smooth (through `lpoly ..., generate(xg yg) nograph`) beside dash's; the threshold is the largest power of ten t in {1e-10 .. 1e-20} such that counting weights `> t` gives exactly Stata's set for this probe and for `bwidth(0.5)`, `bwidth(2)` and `kernel(biweight)` (a biweight is exactly 0 outside the window, so the rule must not change it). `_LPOLY_WEIGHT_EPS` is written as that value with the probe in its comment; `pos = kw > _LPOLY_WEIGHT_EPS` at BOTH sites where `pos = kw > 0` occurs -- :17025 in `_compute_lpoly_fit` AND :22079 in `_lpoly_local_wls`, the pilot/se path lpolyci takes (:22151, :22160; copied to the served app at :47482) -- so lpoly and lpolyci count weights alike (REVIEW-3e F19, DECISIONS A26), measured by the lpolyci probe `lp.gauss_bw1_ci` on the same gaussian data; in Python and in the JS twin `dash_lpoly` (S19, landed batch 6) -- the JS edit is one comparison inside `_FILTER_JS`'s lpoly helper, fed by S46's OWN substitution statement (TR-46.1, A26).
- **D-46b. D1-D8 branch on the measurement.** D6: dash's check order moves the observation count before `pwidth(0)` (twoway r(2001) "insufficient observations" first) -- dash.ado's lpoly rule in `_dash_option_rules` stays; `_dash_validate_opts` is not reordered (it has no row count); instead the renderer's `map_lpoly` raises the count refusal first and dash.ado's cell path... no: dash.ado does not count rows per layer. Ruling: D6 is matched in dash.ado by checking `pwidth(0)` AFTER the `if`/`in` row count that `_dash_plot` already computes for the cell cap (`count if ...` per segment exists for the weight check: reuse the segment's row-count local in `_dash_process_segment`, :4843ff -- read its actual name before editing; no local named `_seg_n` exists, REVIEW-3e F21); the refusal text is twoway's measured words. D7: the invalid-option messages for lpoly options take twoway's measured words (per option: `bwidth`, `pwidth`, `degree`, `n`, `kernel`) through the rules table's existing text slot (`_dash_validate_value`'s error form at :3615-3618 is dash's; a per-option override string in the rule token `opt=kind,...,msg=<id>` read from a fixture-driven Mata table is NOT built -- the words are typed into the rule as the fixture gives them, one `display as error` each). D8: `pwidth(+800)` -> twoway's rc (3000) and words, measured; dash refuses the `+` form with those words (a rule `pwidth=num,...` already exists; add the sign check in `_dash_validate_value`'s `num` kind only when the fixture says twoway refuses a leading `+` -- else nothing). D1-D3, D5: documented in the help's lpoly paragraph with the measured maximum difference (M17), no code.
- **D-46c. lpoly on five rows (P2.37) follows the probe.** U46-03 draws `lpoly mpg weight if foreign == 0` on the parity frame's five domestic rows (the frame of test_mode_parity `_DF`, exported to a dta by the extractor) and records the curve; dash matches (if twoway draws a curve, dash's empty line comes from the bandwidth rule `_default_lpoly_bwidth` returning non-finite on five rows -- then the rule is corrected by the measured r(bwidth)).
- **D-46d. `function` under by() is evaluated per panel only when the panel's range differs.** twoway's `twoway__function_gen` takes `range()` from the plotregion's x range (per panel under `xrescale`/`rescale`, the shared range otherwise); the function text itself cannot see the panel. dash.ado's `_dash_fn_points` (:8280-8394) is called once per layer at :7052 with `_fn_lo`/`_fn_hi`; under by() with a per-panel x range (S36's grammar: `xrescale`, `rescale`, `style(rescale)`), it is called once per panel with that panel's lo/hi and the points object gains a `panels` map (`"<k>": {"x0","dx","y"}` becomes `"<k>": {"panels": {"<by value>": {...}}}` -- or the flat form when one range). The renderer's `map_function` reads the panel's entry when present. The malformed y-form: U46-04 measures `function 2x`, `function y=`, `function =x` under twoway and copies the token twoway names (dash.ado :8280 region's refusal text).
- **D-46e. Recast density and histogram are tagged for the recount.** In `map_histogram`'s recast branch (:17995-18003) and the kdensity twin, the renderers returned by `_dash_draw_xy_as` get `_dash_agg_source = _mid`, `_dash_agg_config = dict(cfg, recast=<target>)` and `_dash_agg_rows` as the un-recast path tags them; `_FILTER_JS`'s histogram and kdensity branches, after computing bins/grid, write `src.data = {x: mids, y: tops}` when `ac.recast` is set (one `if` per branch); The exemption lives where the frozen tag is decided: `_frozen_layer_tag` (a DashRenderer method, :43040) tags EVERY `_DASH_COMPUTED_ONLY_TYPES` layer through `_dash_stale_kind` (:1913) regardless of `_dash_agg_config`, so the un-recast histogram must escape the cue in `_collect_frozen_layers` (method, :43078) -- 46-01 records where exactly (`grep -n "_dash_frozen\|_dash_agg_config" dash_render.py` over :43078-43120) in `<scratch>/s46/anchors.txt`, and the recast layer takes the same exit once it carries `_dash_agg_config` (REVIEW-3e F20). `_dash_stale_kind` is unchanged. js_runner gains a recast branch runner. `_FROZEN` in test_saved_stale_cue.py (:58-59) DOES list `"histogram"` and `"kdensity"` (as frozen when they lack a config); it is unchanged -- the test file gains a recast case that asserts the tagged recast layer is NOT in the frozen list.
- **D-46f. Fractional dates and rarea one-bound-missing follow the probes.** U46-05: `%tm` 745.5 and `%td` 20000.5 drawn in twoway (the point's x in the SVG against integer neighbours) -- today's loader rule (:612-620: a period fraction is floored to its period, a `%td` fraction keeps its time of day); match or confirm. U46-06: `rarea lo hi x` with `hi` missing on one row: the SVG polygon's vertices (does the row contribute `lo`'s vertex?) -- VArea with NaN in one bound breaks the area at that row; if twoway keeps the other bound, dash fills the missing bound with... the polygon twoway draws is measured and reproduced by substituting the present bound for the missing one on that row (one line in `map_rarea`'s source preparation) only if the probe says so. Tied sort keys and connected markers under sort (O6) are documented as today (twoway's order is random: `_join_order` docstring :16206-16207).
- **D-46g. `%d` and `%tb`.** `%d` is Stata's old `%td` (help datetime): `_DASH_FMT_DATE_RE` (:26935) and `_DATE_FMT_RE` (:529) accept `%-?d` as kind `td` (and the picture after it). `%tb<cal>[:picture]`: dash.ado, at registration, for each `%tb` variable writes `graph_options["_bcal"][var] = {"cal": name, "td": [dofb(k, cal) for k in min..max]}` bounded at 10,000 entries (else the note stays) through `bcal describe` + `dofb()`; the writers (Python `_dash_fmt_date`, JS `dash_fmt_date`) map a `%tb` value through the table to its `%td` and format with the picture (default `%tdDD mon CCYY`? -- measured: `display %tbsimple 5`'s default text in U46-07). `xvarformat(bogus)`: twoway's words measured; dash.ado's `format` kind (:3583) refuses with them (rc copied).
- **D-46h. F5's three comments** become: `map_qfitci` docstring (:16560-16563) "Analytic band from the fit's standard errors (`_dash_fitci_se`); a bootstrap (`_bootstrap_ci`) only when the design is singular (LinAlgError)."; header (:364-381): keep `_N_BOOT_DEFAULT` with "used only by `_bootstrap_ci`, the LinAlgError fallback of the CI layers" and delete the fpfitci bootstrap narrative; `_dash_fold_typed` comment (dash.ado:2228-2233): "twoway joins a connected type's points in the data's order, or in x order under `sort` (WP-29 P0.1); dash does the same, so a bare `sort` on `sort_types` is drawn and not named."

## Risk: [yellow] -- `_FILTER_JS` and the lpoly estimator change; six probes drive six branches

**Why.** The recast branch edits the saved filter script (shared by every page with a filter); the lpoly threshold changes which grid points are finite; dash.ado's function evaluation gains a per-panel loop.

**Risk factors.** 1. test_statistical_truth.py::TestLpolyAgainstStata (:350) pins lpoly against Stata already -- a threshold change must keep it green (it uses epanechnikov/biweight mostly). 2. The JS recast writer must produce the same x/y as Python's recast path (`_mid` columns). 3. Per-panel function points change the spec shape read by `map_function` and by test_function_*.py fixtures. 4. `%tb` tables grow the spec (bounded). 5. dash.ado's refusal reordering for D6 must not change other types' messages.

**Mitigation.** 1. The threshold is validated against four probes including biweight (D-46a). 2. `TestRecastRefit::test_js_equals_python` through js_runner. 3. The flat form is kept when one range (D-46d). 4. The 10,000 bound and the note. 5. The reorder is inside the lpoly-only block.

## Dependencies

- **Depends on: 01.** S19/S22 (JS lpoly/lpolyci, batches 6-7), S36 (by grammar, batch 12), S14 (recast, batch 5), S12 (histogram/kdensity options, batch 4) have landed.
- **Blocks: none.**
- **Parallel batch: 15**, merge order S44, S45, S46. **Can run with S44 and S45**: S44 edits `SchemeParser`; S45 edits the tick placers and `_DASH_AXIS_FINISH_JS` (not `_FILTER_JS`'s literal); dash.ado: S45 adds a program and a call in `_dash_plot`'s graph-JSON block; S46 edits `_dash_fn_points`, its call at :7052, the lpoly refusal block in `_dash_process_segment`, the `format` kind and `_dash_fold_typed`'s comment -- disjoint lines; merge S45 then S46.

## Evidence

### C11

```python
17024            pos = kw > 0
17025            if int(pos.sum()) < 2:
17026                y_fit[i] = np.nan
```
(`_compute_lpoly_fit`, :16970-17060; the second `pos = kw > 0` is :22079 in `_lpoly_local_wls`, the pilot/se path lpolyci calls at :22151 and :22160 -- REVIEW-3e F19); `_lpoly_kernel_weights` (:22049) returns a gaussian that is positive everywhere, so every observation counts. `map_lpoly` options (:17150-17185): `bwidth` (warned to None when <= 0), `degree` 0-3, `kernel`, `n_grid`, the bandwidth rule `_default_lpoly_bwidth` (non-finite -> a zero line "as twoway"). `pwidth`: dash.ado:1912-1923 (lpolyci's `pwidth`/`var` sreturn), dash_render.py:17306 (`_positive("pwidth")`). test_statistical_truth.py::TestLpolyAgainstStata (:350-418) and `_lpoly_at` (:419).

### C12

dash.ado:8280-8300 (the comment above `program define _dash_fn_points` at :8315; `_dash_fn_points raw_sc lo hi n k obj_sc`: "runs twoway__function_gen -- the generator twoway function itself calls -- as twoway calls it, and keeps the points"), :7052 (the one call per layer: `_dash_fn_points `_fx_raw' `_fn_lo_`_m'' `_fn_hi_`_m'' `_fn_n_`_m'' `_fn_k_`_m'' `_fp_sc'`), :6896 (range()/n() read), :5064 (comment). program_coverage_map.py:251 (`_dash_fn_points`: test_parser.cscript FX-01), :593, :598.

### C16

```python
17993        # recast(): the bars' midpoints and heights drawn as the target,
17994        # as twoway draws histogram's serset (WP-30 P1.8b).
17995        if options.get("recast"):
17996            _mid = ColumnDataSource({ "x": ..., "y": ...})
18001            return self._dash_draw_xy_as(fig, _mid, "x", "y",
18002                                         options["recast"], options,
18003                                         color_idx)
```
The agg tagging follows at :18011-18054 (histogram config keys `type, varname, bin_edges, ymode, wvar, wtype, discrete, start, width, bin`, dates) and :18380-18412 (kdensity); `_dash_stale_kind` (:1913-1930); the DashRenderer methods `_frozen_layer_tag` (:43040) and `_collect_frozen_layers` (:43078); the JS branches at :25213-25284 (histogram) and :25285-25375 (kdensity); js_runner.run_filter_js_block's cut markers (research codebase-mechanics §3). `_dash_draw_xy_as` (:20693).

### G6

Loader :606-620 ("a fraction is floored to the millisecond (%tc 1.9999 is .001 ...) or to the period that holds it (%tm 745.5 is 2022m2); a %td fraction keeps its time of day, as the value's place on an axis" -- measured 24sep2026 for DISPLAY; the AXIS position is P2.32's open question). `_join_order` (:16187-16236). `map_rarea` (:18421; REVIEW-3e F22). P2.30 O1 (rarea one bound missing), O6.

### G7

`_DASH_FMT_DATE_RE = re.compile(r"^%(-)?t([cCdhmqwy])(.*)$")` (:26935); `_DATE_FMT_RE` (:529); `_dash_fmt_kind` refuses `%x`/`%H`/`%L` and writes `%9.0g` with a note (BR-04.5 comment :26925-26931); `xvarformat()` rule `format` kind (dash.ado:3583). `grep -c '%tb' dash_render.py` = 0.

### F5

:16560-16563 ("Uses a bootstrap approach (500 resamples) ... because scipy does not provide analytical CIs"), :16627-16632 (the LinAlgError fallback that is the only bootstrap), :364-381 (`_N_BOOT_DEFAULT` narrative, fpfitci's "former bootstrap"), dash.ado:2228-2233 ("dash always joins line, connected, area, tsline and the range line and area types in that order").

### Tests pinning today's behaviour

test_statistical_truth.py::TestLpolyAgainstStata (guard, must stay green); test_lpoly*.py nodes counting finite grid points for gaussian; test_saved_stale_cue.py (a recast histogram case, if any, asserting the stale tag); test_function*.py fixtures with the flat points form (kept); test_dates.py nodes pinning `%tm` 745.5's position; test_display_format_writer.py::TestTheGuard (`%d` refused as unknown?) and the `%tb` note node; test_option_validation.py nodes pinning dash's words for lpoly options (D7) and `xvarformat(bogus)`'s note.

## User stories

- US-46.1 As a Stata user, I want `lpoly ..., kernel(gaussian) bwidth(1)` to draw the three points twoway draws, and its refusals to say what twoway says.
- US-46.2 As a user of `by(, xrescale)` with a `function` layer, I want each panel's curve over its own range.
- US-46.3 As a user who saved a page with `histogram ..., recast(line)`, I want the line recounted after a filter move, not greyed.
- US-46.4 As a user of business dates, I want `%tb` axes labelled with dates, and `%d` read as the date it is.
- US-46.5 As a maintainer, I want the comments to describe the code.

## Business requirements

- BR-46.1 lpoly's finite grid points equal twoway's on the four probes; D6-D8 behave as measured; D1-D3/D5 documented with measured maxima; the five-row case matches (C11).
- BR-46.2 `function` under a per-panel range is evaluated per panel; the malformed y-form message is twoway's (C12).
- BR-46.3 A recast histogram/kdensity is recounted after a saved move in both modes and carries no stale cue (C16).
- BR-46.4 Fractional dates and rarea's one-bound-missing rows draw as measured; ties and O6 documented (G6).
- BR-46.5 `%d` reads as `%td`; `%tb` axes and tooltips show calendar dates (bounded, noted beyond); `xvarformat(bogus)` refused with twoway's words (G7).
- BR-46.6 The three comments are true (F5).

## Technical requirements

- TR-46.1 (C11) `_LPOLY_WEIGHT_EPS` module constant after `_FIT_GRID` (:474) with the probe comment; `pos = kw > _LPOLY_WEIGHT_EPS` at BOTH :17025 (`_compute_lpoly_fit`) and :22079 (`_lpoly_local_wls`, lpolyci's pilot/se path; F19, A26); copy list: constant after `_DASH_STALE_STATUS_HTML`'s group (R2) -- it is read inside `_compute_lpoly_fit` and `_lpoly_local_wls`, which `_shared_stat_lines` copies (:47482), so the constant must be emitted before them: add to the constants tuple. JS: the same comparison in `dash_lpoly`'s weight loop (`_FILTER_JS`, S19's helper; grep `function dash_lpoly`): the literal is the token `@@DASH_LPOLY_EPS@@` in the helper's text, substituted by S46's OWN module statement `_FILTER_JS = _FILTER_JS.replace("@@DASH_LPOLY_EPS@@", repr(_LPOLY_WEIGHT_EPS))` placed directly BEFORE the `_FILTER_JS = (_FILTER_JS + _DASH_AXIS_FINISH_JS ...)` statement at :31459 -- NOT a row in the `_tok`/`repr(_val)` loop at :31446-31452, which substitutes into `_DASH_AXIS_FINISH_JS` (S45's R11 literal), where `dash_lpoly` does not live (REVIEW-3e F18, DECISIONS A26). D6-D8 per D-46b in dash.ado (`_dash_process_segment`'s lpoly block near :5556-5574 and `_dash_validate_value` num kind :3166). The help's lpoly paragraph gains the D1-D3/D5 sentence with the fixture's maxima.
- TR-46.2 (C12) dash.ado: `_dash_fn_points` gains an optional seventh arg `panel_key`; the caller at :7052 loops over the by() panels' ranges when `_dash_by_rescales_x` (S36's local naming the x-rescale state; read its actual name) is set, writing `"panels": {...}`; else the flat form. `_dash_fn_points_json` (Mata) writes the nested form. The y-form refusal text copied from the fixture (`fn.malformed.*`). dash_render.py `map_function`: read `points["panels"][panel_key]` when present (the panel key reaches the mapper through the by() facet value already passed for titles).
- TR-46.3 (C16) per D-46e: tagging in both recast branches; `_FILTER_JS`: in the histogram branch after `src.data = {...}` is assembled, `if (ac.recast) { src.data = { x: <mids>, y: <tops> }; }` and the kdensity twin (`x: xs, y: ys` already -- the kdensity recast source is the same shape: confirm and tag only); js_runner: `run_recast_block` or an `ac.recast` flag on the existing runners. `test_saved_stale_cue.py` gains `test_a_recast_histogram_is_not_frozen` (no `_FROZEN` change).
- TR-46.4 (G6) per D-46f: loader rule confirmed or changed at :606-620 (and `_dash_date_units`); `map_rarea` one-bound substitution line if measured; docstring of `_join_order` for ties/O6 unchanged.
- TR-46.5 (G7) `_DASH_FMT_DATE_RE` -> `r"^%(-)?(?:t([cCdhmqwy])|(d)|tb([A-Za-z_][A-Za-z0-9_]{0,31}))(.*)$"` with `d` mapped to kind `d`->`td` and `tb` to kind `tb` carrying the calendar name; `_DATE_FMT_RE` likewise; `_dash_fmt_date` and JS `dash_fmt_date` take a `bcal` table from the writer args (`_dash_fmt_model_args` adds `bcal` for a `%tb` variable: `{"td": [...], "min": k0}`); dash.ado writes `graph_options["_bcal"]` (bounded 10,000; else today's note). `xvarformat(bogus)`: `format` kind refuses with the fixture's words and rc.
- TR-46.6 (F5) per D-46h.
- TR-46.7 Both renderers: `_LPOLY_WEIGHT_EPS` on the constants tuple; `_dash_fmt_date`'s change is in a copied function; `map_*` are class members; js_runner is test-only. function_test_map.py: no new function unless `_dash_bcal_td(value, table)` is added (then an entry). program_coverage_map.py: `_dash_fn_points` entry gains `test_wp31_truth.cscript:U46-04`; a new ado program for `%tb` (`_dash_bcal_table`, version 19) gets `U46-07`.
- TR-46.8 Help (R3): lpoly paragraph (threshold, D1-D3/D5 maxima, D6-D8 words), function paragraph (per-panel evaluation under a rescaled x), recast sentence in Filters ("recounted after a move"), the date-format paragraph (`%d`, `%tb` with the bound), the join-order paragraph (ties). TWOWAY_COVERAGE_AUDIT.md rows for lpoly, function and `%tb`.


### Reference TR-46.A: the D1-D8 register cases and S46's disposition

| case | command (auto) | twoway | dash today | S46 |
|---|---|---|---|---|
| SD-10 | `lpoly mpg weight, kernel(gaussian) bwidth(1)` (and `lpolyci ...` on the same data, `lp.gauss_bw1_ci`) | 3 finite points | 23 | threshold `_LPOLY_WEIGHT_EPS` at both sites (D-46a, F19) |
| D1 | `generate ylin = 2*weight+1; lpoly ylin weight, degree(0)` | round-off differences | exact | documented with the fixture's max |diff| (help) |
| D2 | `generate yw = weight; lpoly yw weight, degree(0)` and `degree(1)` | round-off | exact | documented |
| D3 | `generate ys = mpg*1e-150; lpoly ys weight, degree(2)` | a zero line | fit | documented (twoway's quadcross underflow) |
| D4 | lpolyci rows whose pilot has no residual df | missing | pinched | documented; `TestLpolyDocumented` names it |
| D5 | `r1000_d2_bw600` pilot round-off, 2 of 50 se | differ | differ | documented |
| D6 | `lpoly mpg weight if _n==1, pwidth(0)` | r(2001) (count first) | r(198) (pwidth first) | dash.ado checks the segment's row count before the pwidth rule (D-46b) |
| D7 | `bwidth(abc)` `degree(9)` `n(0)` `kernel(x)` | twoway's words | dash's words | twoway's words typed into the rules (fixture `lp.D7.*`) |
| D8 | `lpolyci mpg weight, pwidth(+800)` | r(3000) | accepted | refused with the measured rc/words if twoway refuses the `+` form |

Constant and comparison (TR-46.1):

```python
#: A kernel weight below this counts as zero for lpoly's two-observation
#: rule: twoway draws `lpoly mpg weight, kernel(gaussian) bwidth(1)' at 3
#: grid points where every-weight counting gives 23 (WP-31 C11,
#: test/fixtures/estimator_edges_truth.json lp.gauss_*; the threshold is the
#: largest power of ten that reproduces all four probes).
_LPOLY_WEIGHT_EPS = <fixture value, e.g. 1e-14>
...
            pos = kw > _LPOLY_WEIGHT_EPS
```
JS twin: in `dash_lpoly`'s weight loop (S19), `if (kw[j] > @@DASH_LPOLY_EPS@@) { npos += 1; }` -- the token is replaced by S46's own statement `_FILTER_JS = _FILTER_JS.replace("@@DASH_LPOLY_EPS@@", repr(_LPOLY_WEIGHT_EPS))` written directly before :31459 (A26), so one Python constant feeds both; the `_tok`/`repr(_val)` loop at :31446-31452 is S45's (it substitutes into `_DASH_AXIS_FINISH_JS`) and is not touched. The same comparison in `_lpoly_local_wls` (:22079) keeps lpolyci's pilot in step (F19).

### Reference TR-46.B: the recast tagging (TR-46.3)

Python, replacing :18001-18003:

```python
            _recast = self._dash_draw_xy_as(fig, _mid, "x", "y",
                                            options["recast"], options,
                                            color_idx)
            # The recast layer is recounted after a saved move like the bars
            # it stands for (WP-31 C16): same source, same config plus the
            # target, so the JS branch writes x/y instead of top/left/right.
            _cfg = dict(<the histogram config dict the un-recast path builds at :18011-18054, factored into a local built before this branch>)
            _cfg["recast"] = str(options["recast"])
            for _r in (_recast if isinstance(_recast, list) else [_recast]):
                _r._dash_agg_source = _mid
                _r._dash_agg_config = _cfg
                _r._dash_agg_rows = <the un-recast path's _agg_member_ids value>
            return _recast
```
`_FILTER_JS` histogram branch, directly before its `src.change.emit()`:

```js
                if (ac.recast) {
                    // midpoints and heights, as the recast target reads them
                    const _mx = [], _my = [];
                    for (let b = 0; b < lefts.length; b++) { _mx.push((lefts[b] + rights[b]) / 2); _my.push(tops[b]); }
                    src.data = { x: _mx, y: _my };
                }
```
(`lefts`, `rights`, `tops` are the branch's own arrays; re-read their names at the base.) The kdensity branch already writes `{ x: xs, y: ys }`, the shape the recast kdensity source has: tagging alone suffices there. js_runner: `run_filter_js_block(..., recast=True)` sets `ac.recast = "line"` on the config before running the branch.

### Reference TR-46.C: `%d` and `%tb` (TR-46.5)

```python
_DASH_FMT_DATE_RE = re.compile(
    r"^%(-)?(?:t([cCdhmqwy])|(d)|tb([A-Za-z_][A-Za-z0-9_]{0,31}))(.*)$")
```
`_dash_fmt_parse`: group 3 (`d`) -> kind `"t"`, unit `"d"`, picture group 5; group 4 -> kind `"t"`, unit `"d"`, `bcal=<name>`, picture group 5 (default picture = `fmt.tb_default`'s measured form). `_dash_fmt_date(parsed, v, bcal_table=None)`: when `parsed.bcal` is set, `v = bcal_table["td"][int(v) - bcal_table["min"]]` if in range else the bare number (Stata prints the number past the calendar, measured `fmt.tb_*`). JS twin the same, `bcal_table` from the writer's `args`. The JS regex literal at :23396 is updated to the same pattern. dash.ado `_dash_bcal_table` (version 19): for a `%tb<cal>` variable, `quietly summarize` -> min/max, `bcal describe <cal>` for the calendar's range, and for k in max(min, range_lo)..min(max, range_hi) (at most 10,000) `dofb(k, "<cal>")` written as `{"cal": "<cal>", "min": k0, "td": [...]}` into `graph_options["_bcal"][var]`; over 10,000 the variable keeps today's `%9.0g` note.

### Verbatim TR-46.D

- CHANGELOG Changed-behaviour lines: `- lpoly ..., pwidth(0) on too few observations was refused as a pwidth error; it is refused as twoway refuses it, "<measured>" r(2001) (WP-31, C11)`; `- lpoly option errors used dash's words; they use twoway's: "<measured per option>" (WP-31, C11)`; `- xvarformat(bogus) was noted and %9.0g drawn; it is refused as twoway refuses it, "<measured>" r(<rc>) (WP-31, G7)`. Results lines: `- lpoly mpg weight, kernel(gaussian) bwidth(1) drew 23 points; it draws twoway's 3 (WP-31, C11)`; `- a recast histogram or kdensity on the saved page was frozen with the cue after a move; it is recounted (WP-31, C16)`; `- %d and %tb formats drew %9.0g with a note; they draw dates (WP-31, G7)`.
- dash.sthlp lpoly sentence: `A gaussian kernel weight below <eps> does not count toward lpoly's two-observation rule, as in Stata. Where Stata's result is decided by its own round-off ({cmd:lpoly ylin weight, degree(0)} with ylin = 2*weight+1, a variable near 1e-150 at degree(2), a pilot with no residual degrees of freedom), dash's exact arithmetic differs by at most <fixture maxima>.`
- test/program_coverage_map.py: `"_dash_bcal_table": ("test_wp31_truth.cscript:U46-07",),` and `_dash_fn_points`'s tuple gains `"test_wp31_truth.cscript:U46-04"`.
- The qfitci docstring (D-46h), verbatim replacement of :16560-16563: `"""Add a quadratic fit line with its confidence band to *fig*.` / `` / `The band is analytic (``_dash_fitci_se`` from the fit's standard errors, Stata's rule); ``_bootstrap_ci`` runs only when the design is singular (LinAlgError).`

## Boundaries

- No change to `_lpoly_rot_*`, `_default_lpoly_bwidth`'s formula (except D-46c's measured correction), the lpolyci band maths, or `_dash_stale_kind`'s fit rule.
- `_FILTER_JS`: the recast `if`s, the lpoly threshold token in `dash_lpoly` and S46's own `.replace` statement before :31459 only; no new branch; no row in S45's `_tok`/`repr(_val)` loop (A26).
- by() grammar is S36's; S46 reads its rescale state.
- `_join_order`'s stable sort stays (ties documented).

## Stata truth

Script `scripts/extract_estimator_edges_truth.do` -> `test/fixtures/estimator_edges_truth.json`.

| Key | Probe | Recorded |
|---|---|---|
| `lp.gauss_bw1`, `lp.gauss_bw05`, `lp.gauss_bw2`, `lp.biweight_bw1` | `lpoly mpg weight, kernel(k) bwidth(b) n(50) generate(xg yg) nograph` | xg, yg (missing as null) |
| `lp.gauss_bw1_ci` | `lpoly mpg weight, kernel(gaussian) bwidth(1) n(50) ci generate(xg yg) se(sg) nograph` | xg, yg, sg (the pilot/se path's finite set; REVIEW-3e F19) |
| `lp.D1`..`lp.D5` | the register's commands (auto: `generate ylin=2*weight+1`; `lpoly ylin weight, degree(0)`; `yw=weight` degree 0 and 1; `generate ys = mpg*1e-150`, degree 2; `lpolyci` with a pilot of no residual df; `r1000_d2_bw600` from test/fixtures as the register names) | grid and values / se |
| `lp.D6`, `lp.D7.<opt>`, `lp.D8` | `lpoly mpg weight if _n==1, pwidth(0)`; `lpoly ..., bwidth(abc)`, `degree(9)`, `n(0)`, `kernel(x)`; `lpolyci ..., pwidth(+800)` | rc, error text |
| `lp.five_rows` | the parity frame (written to dta by the extractor from test_mode_parity's `_DF` through python) `lpoly mpg weight if foreign == 0, generate(xg yg) nograph` | r(bwidth), xg, yg |
| `fn.by_rescale` | `twoway function y=x^2, range(0 10) || scatter mpg weight, by(foreign, xrescale)`? no: `function` with no range under `by(foreign, xrescale)`: `twoway scatter mpg weight || function y = x/1000, by(foreign, xrescale)`; `.Graph.graphs[k].plotregion1.plot2.serset` x min/max per panel | per-panel x0, x1, n |
| `fn.malformed.<i>` | `twoway function 2x`, `function y=`, `function =x`, `function y = ` | rc, error text |
| `rc.hist_line` | `twoway histogram mpg, recast(line)` (record only: dash's recount target) | rc |
| `dt.tm_frac`, `dt.td_frac` | `%tm` 745.5 and `%td` 20000.5 in a two-point scatter beside integers; SVG x positions | positions relative to neighbours |
| `ra.one_bound` | `rarea lo hi x, sort` with `hi` missing on row 3 of 6; SVG polygon vertices | vertex list |
| `fmt.d`, `fmt.tb_default`, `fmt.tb_picture` | `format x %d; display %d 20000`; `bcal create u46, from(date) ...`; `display %tbu46 5`; `display %tbu46:CCYY-NN-DD 5` | texts; `bcal describe u46` range |
| `fmt.tb_axis` | `scatter y bdate` with `%tbu46`; SVG tick labels | labels |
| `fmt.xvarformat_bogus` | `scatter mpg weight, xvarformat(bogus)` | rc, error text |

Truth blocks (R1; DECISIONS A14: one block per row, each appended by the row's closing step; F5 has none; 46-01 appends only the C16 block; helpers `_u46_*` above the first block; each block ends `* ==== end S46 <row> ====`): `* ==== S46 C16: Recast layers recounted ====` (U46-05 the saved page's JS recast branch recounts after a move -- python helper through js_runner -- and no stale cue is tagged); `* ==== S46 C11: lpoly edges ====` (U46-01 fixture stamped; U46-02 dash's lpoly finite grid points -- python helper running `GlyphMapper._compute_lpoly_fit` and the lpolyci pilot through `_lpoly_local_wls` -- equal `lp.gauss_*`/`lp.gauss_bw1_ci`/`lp.biweight_bw1`'s non-missing sets; U46-03 `lp.five_rows` drawn equal in both modes; U46-08 D6-D8 rc/words equal twoway's); `* ==== S46 C12: function per panel ====` (U46-04 `function` under by(foreign, xrescale): the spec's per-panel points' ranges equal `fn.by_rescale`; the four malformed forms give dash twoway's rc and words, same session); `* ==== S46 G6: Fractional dates and rarea bounds ====` (U46-06 `dt.*` and `ra.one_bound` drawn as measured in both modes); `* ==== S46 G7: %d, %tb and xvarformat ====` (U46-07 `%d`/`%tb` tick labels and tooltips equal `fmt.*` in both modes and `xvarformat(bogus)` returns twoway's rc and words). Refusal cases also appended to test_option_validation.cscript as U46-09.. (`_ov_assert`, `capture twoway` beside `capture dash`), each by its row's closing step.

## TDD test stubs

One new file per row (DECISIONS A14): F5 `test/test_comments_true.py` (`TestComments`), C16 `test/test_recast_refit.py` (`TestRecastRefit`; plus `test_a_recast_histogram_is_not_frozen` appended to test/test_saved_stale_cue.py), C11 `test/test_lpoly_edges.py` (`TestTheFixture`, `TestLpolyThreshold`, `TestLpolyRefusals`, `TestLpolyDocumented`, `TestLpolyFiveRows`), C12 `test/test_function_panels.py` (`TestFunctionPerPanel`), G6 `test/test_data_join_edges.py` (`TestFractionalDates`, `TestRareaOneBound`), G7 `test/test_date_format_edges.py` (`TestFormats`). Each row's commit stages that row's file only. The fixture is named by test_lpoly_edges.py::TestTheFixture and staged in the C11 commit (the first row that reads it; F5 and C16 read none).

### The classes

- `TestTheFixture::test_meta` (guard).
- `TestLpolyThreshold::test_gaussian_grid_points[case]` (red: 23 vs 3), `::test_lpolyci_pilot_agrees` (the `_lpoly_local_wls` site, fixture `lp.gauss_bw1_ci`; red -- F19), `::test_biweight_unchanged` (guard), `::test_js_twin_agrees` (node; red), `::test_substitution_is_own_statement` (source scan: `_FILTER_JS.replace("@@DASH_LPOLY_EPS@@"` precedes the :31459 statement and no `_LPOLY_WEIGHT_EPS` row sits in the `_tok` loop; red -- A26), `::test_statistical_truth_still_green` (runs `_lpoly_at` over the existing truth; guard).
- `TestLpolyRefusals::test_D6_order` (cscript half U46-08; pytest: `map_lpoly` on one row raises the measured text? no -- dash.ado's; pytest pins the renderer draws a zero line silently on one row, guard), `::test_D7_words` and `::test_D8_plus` through the spec-level ado log fixture (red).
- `TestLpolyDocumented::test_help_names_the_maxima` (red).
- `TestLpolyFiveRows::test_matches_twoway[mode]` (red or guard by probe).
- `TestFunctionPerPanel::test_points_per_panel[mode]` (red), `::test_flat_form_when_one_range` (guard), `::test_malformed_words` (ado log; red).
- `TestRecastRefit::test_tagged[type]` (red: no `_dash_agg_config`), `::test_js_equals_python[type]` (red), `::test_not_frozen[type]` (red: `_collect_frozen_layers` lists it; the exit is the method's, F20), served `::test_served_recount[type]` (guard: served recomputes).
- `TestFractionalDates::test_tm_half[mode]`, `::test_td_half[mode]` (red or guard).
- `TestRareaOneBound::test_polygon_keeps_other_bound[mode]` (red if measured so).
- `TestFormats::test_percent_d_is_td`, `::test_tb_ticks[mode]`, `::test_tb_tooltip_js` (node), `::test_tb_bound_notes`, `::test_xvarformat_bogus_words` (ado log) (red).
- `TestComments::test_qfitci_docstring`, `::test_header_no_bootstrap_narrative`, `::test_fold_typed_comment` (source scans; red).

### Flips

From `<scratch>/s46/46-flips.txt` (gaussian point counts, `%d`/`%tb` refusal nodes, stale-cue recast node, dash's D7 words); reasons per row.

### cscript: U46-01..U46-08 in the five row blocks (A14), U46-09.. (option validation). Parity: `CORPUS` "lpoly gaussian bwidth(1)", "histogram recast(line)", "%tb axis"; `MOVE_CORPUS` "histogram recast(line), dropdown to Foreign", "kdensity recast(area), range".

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| lpoly threshold (both sites), D1-D8, five rows | pytest test_lpoly_edges.py + U46-02/03/08 + option cscript | estimator_edges_truth.json | yes |
| function per panel, malformed | pytest test_function_panels.py + U46-04 | same | yes |
| recast recount | pytest test_recast_refit.py (node) + U46-05 + parity moves | -- | yes |
| fractional dates, rarea bound | pytest test_data_join_edges.py + U46-06 | same | yes |
| %d, %tb, xvarformat | pytest test_date_format_edges.py + U46-07 | same | yes |
| comments | pytest test_comments_true.py source scans | -- | n/a |

AC-46.1..AC-46.6 one per BR; AC-46.7 six green commits, each staging its own row's test file and truth block (A14), every Tracked line `commit pending` (A11).

## Tasks

**Commit boundary.** 46-01 tests (no commit); 46-02 commits F5 `Correct the qfitci, header and fold_typed comments (WP-31 F5)` then C16 `Recount a recast histogram or kdensity after a saved move (WP-31 C16)`; 46-03 commits C11 `Match lpoly's weight threshold and option refusals to twoway's (WP-31 C11)` then C12 `Evaluate function layers per by() panel and copy twoway's malformed-form words (WP-31 C12)`; 46-04 commits G6 `Draw fractional dates and rarea's one-bound-missing rows as twoway does (WP-31 G6)` then G7 `Read %d and %tb formats and refuse xvarformat(bogus) with twoway's words (WP-31 G7)` and hands back. Every Tracked line reads `commit pending` (A11). `$WT=<worktrees>/wp31-s46`.

<task type="auto" id="46-01">
  <name>Measure the six edges and write failing tests</name>
  <files>scripts/extract_estimator_edges_truth.do, test/fixtures/estimator_edges_truth.json, test/test_lpoly_edges.py</files>
  <action><![CDATA[
    Check the worktree (wp31-s46 at the batch-15 base); re-read `_FILTER_JS`'s histogram/kdensity branches, `dash_lpoly`, both `pos = kw > 0` sites (:17025, :22079; F19), the `_tok`/`repr(_val)` loop (:31446-31452, S45's; A26) and the :31459 statement at this base, and record where the un-recast histogram escapes the stale cue in `_collect_frozen_layers` (:43078-43120; F20); write every anchor to `<scratch>/s46/anchors.txt`. Create the extractor from the table (head as scripts/extract_date_axes_truth.do; the parity frame written to dta via python `pandas.DataFrame.to_stata` from test_mode_parity's `_DF`; `bcal create` in the work dir; `_meta`); run through the slot; `git add -f`. Create the six per-row test files of "TDD test stubs" (test/test_comments_true.py, test/test_recast_refit.py, test/test_lpoly_edges.py, test/test_function_panels.py, test/test_data_join_edges.py, test/test_date_format_edges.py) with exactly their classes; add `test_a_recast_histogram_is_not_frozen` to test/test_saved_stale_cue.py. Run the seven files `-q -n0 -p no:cacheprovider -rf > <scratch>/s46/46-01.log`; write `<scratch>/46-01-failure.txt` grouped by row. Append the `_u46_*` helpers and ONLY the C16 block (`* ==== S46 C16: Recast layers recounted ====`, U46-05) to test/test_wp31_truth.cscript above the marker (A14: the C11, C12, G6 and G7 blocks and the U46-09.. option-validation cases are appended by 46-03 and 46-04); run through the driver (`WP31_ONLY=S46`); append FAIL lines. Simulated fix for the flips -> `<scratch>/s46/46-flips.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/estimator_edges_truth.json'));print(sorted(d['_meta']), sum(k.startswith('lp.') for k in d), 'fmt.tb_default' in d)"` prints the five keys, at least 13, True; `grep -c FAILED <scratch>/s46/46-01.log` is at least 15; `grep -c "U46-05 FAIL" <scratch>/s46/run_test_wp31_truth.log` prints 1 and `grep -c "U46-0[1-46-8]" <scratch>/s46/run_test_wp31_truth.log` prints 0 (only the C16 block exists yet); `test -s <scratch>/46-01-failure.txt`.]]></verify>
  <done>twoway's lpoly grids, refusal words, per-panel function ranges, fractional-date positions, rarea polygon, business-date texts and xvarformat words were recorded, and every regression test and truth case was shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="46-02">
  <name>Fix the comments and recount recast layers, commit F5 and C16</name>
  <files>dash_render.py, dash.ado, test/js_runner.py</files>
  <action><![CDATA[
    Apply TR-46.6 (D-46h); run test_comments_true.py; close BUGS.md F5, Tracked (`commit pending`, A11), marker (no CHANGELOG Results line: comments only -- replace the marker with a line under `### Fixed in WP-31`); stage test/test_comments_true.py (F5 has no truth block); commit `(WP-31 F5)`. Then re-run test_recast_refit.py red on the F5 tree; apply TR-46.3 (tagging in both recast branches; the exit in `_collect_frozen_layers` per `<scratch>/s46/anchors.txt` (F20); the two `if (ac.recast)` writes in `_FILTER_JS`; js_runner's recast flag); run test_recast_refit.py, test_saved_stale_cue.py, test_saved_filter_layers.py -k recast, test_statistical_helpers.py::TestFilterJavaScript, test_mode_parity.py -k recast, test_csp.py, and U46-05; help's recast sentence; close C16, Tracked (`commit pending`), marker (Results: "recast histogram/kdensity after a saved move: frozen with the cue -> recounted"); stage test/test_recast_refit.py, test/test_saved_stale_cue.py and the C16 block; commit `(WP-31 C16)`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_comments_true.py test/test_recast_refit.py test/test_saved_stale_cue.py test/test_csp.py -q -p no:cacheprovider` ends 0 failed; `grep -c "U46-05 PASS" <scratch>/s46/run_test_wp31_truth.log` prints 1; `git log --format=%s -2 | grep -c "(WP-31 \(F5\|C16\))"` prints 2; `grep -c "\(F5\|C16\) Tracked:\*\* Closed in WP-31.*commit pending" GAPS3.md` prints 2.]]></verify>
  <done>The three comments describe the code, and a recast histogram or kdensity is recounted by the saved page's own script after a move with no stale cue; the F5 and C16 commits landed.</done>
</task>

<task type="auto" id="46-03">
  <name>Match lpoly's threshold and refusals, evaluate function per panel, commit C11 and C12</name>
  <files>dash_render.py, dash.ado, dash_parse.mata</files>
  <action><![CDATA[
    Append the C11 block (`* ==== S46 C11: lpoly edges ====`, U46-01, U46-02, U46-03, U46-08) above the marker and the C11 refusal cases (U46-09..) to test_option_validation.cscript before `// Summary`; re-run test_lpoly_edges.py and those cases red on the C16 tree (append to the failure file). Apply TR-46.1 per D-46a/D-46b/D-46c (the constant from the fixture; `pos = kw > _LPOLY_WEIGHT_EPS` at BOTH :17025 and :22079 (F19); the `@@DASH_LPOLY_EPS@@` token in `dash_lpoly` and S46's own `_FILTER_JS = _FILTER_JS.replace(...)` statement directly before :31459 (A26); D6-D8 in dash.ado by the fixture's rc/words; the five-row branch), copy-list entry for `_LPOLY_WEIGHT_EPS`, the help's lpoly sentences with `lp.D1..D5` maxima; flip the gaussian-count and D7-words nodes; run test_lpoly_edges.py, test_statistical_truth.py, test_statistical_helpers.py (lpoly JS twin), test_lpoly*.py, test_option_validation.py, test_option_validation.cscript (U46-09..) and U46-01/02/03/08; CHANGELOG Changed-behaviour lines for D6/D8 forms; close C11, Tracked (`commit pending`), marker; stage test/test_lpoly_edges.py, the C11 block, the option-validation cases and `git add -f test/fixtures/estimator_edges_truth.json`; commit `(WP-31 C11)`. Then append the C12 block (`* ==== S46 C12: function per panel ====`, U46-04); re-run test_function_panels.py and U46-04 red; apply TR-46.2 (per-panel `_dash_fn_points` (:8315), Mata JSON form, `map_function`'s panel read, the malformed words), program_coverage_map.py; run test_function_panels.py, test_function*.py, test_by*.py -k function, test_parser.cscript (FX cases) through the driver, test_program_coverage_map.py, U46-04; help's function sentence; close C12, Tracked (`commit pending`), marker; stage test/test_function_panels.py and the C12 block; commit `(WP-31 C12)`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_lpoly_edges.py test/test_function_panels.py test/test_statistical_truth.py test/test_option_validation.py test/test_program_coverage_map.py -q -p no:cacheprovider` ends 0 failed; `grep -c "pos = kw > _LPOLY_WEIGHT_EPS" dash_render.py` prints 2; `grep -c '_FILTER_JS.replace("@@DASH_LPOLY_EPS@@"' dash_render.py` prints 1; `grep -c "U46-0[12348] PASS" <scratch>/s46/run_test_wp31_truth.log` prints 5; `grep -c "ALL CHECKS PASSED" <scratch>/s46/run_test_option_validation.log` prints 1; `git log --format=%s -2 | grep -c "(WP-31 C1[12])"` prints 2.]]></verify>
  <done>lpoly counts weights as twoway does and refuses as twoway refuses, with the round-off cases documented, and function layers are evaluated per rescaled panel with twoway's malformed-form words; the C11 and C12 commits landed.</done>
</task>

<task type="auto" id="46-04">
  <name>Draw fractional dates, rarea bounds, %d and %tb; commit G6 and G7</name>
  <files>dash_render.py, dash.ado, dash.sthlp</files>
  <action><![CDATA[
    Append the G6 block (`* ==== S46 G6: Fractional dates and rarea bounds ====`, U46-06); re-run test_data_join_edges.py and U46-06 red on the C12 tree. Apply TR-46.4 per `dt.*`/`ra.one_bound` (D-46f; `map_rarea` :18421); flip the date-position nodes; run test_data_join_edges.py, test_dates.py, test_range*.py, test_mode_parity.py -k rarea, U46-06; help's join-order and date sentences; close G6 (Resolution documents ties and O6 as twoway's random order), Tracked (`commit pending`), marker; stage test/test_data_join_edges.py and the G6 block; commit `(WP-31 G6)`. Then append the G7 block (`* ==== S46 G7: %d, %tb and xvarformat ====`, U46-07) and G7's refusal case to test_option_validation.cscript; re-run test_date_format_edges.py and those cases red; apply TR-46.5 (`%d`, `%tb` tables with the 10,000 bound, writer args, JS twin, `xvarformat(bogus)` words; `_dash_bcal_table` program version 19; program_coverage_map.py; function_test_map.py if a helper is added); flip the `%d`/`%tb` note nodes; run test_date_format_edges.py, test_display_format_writer.py, test_dates.py, test_label_sinks.py::TestJavaScript, test_statistical_helpers.py::TestTheServedAppCarriesEveryName, U46-07; CHANGELOG Changed-behaviour line for `xvarformat(bogus)`; help's date-format paragraph; close G7, Tracked (`commit pending`), marker; stage test/test_date_format_edges.py, the G7 block and its option-validation case; commit `(WP-31 G7)`. Run the six S46 test files whole and the S46 blocks once more; write `<scratch>/s46/handback.txt` (six shas; the branches taken with measured values; D1-D3/D5 maxima; the `%tb` bound).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_comments_true.py test/test_recast_refit.py test/test_lpoly_edges.py test/test_function_panels.py test/test_data_join_edges.py test/test_date_format_edges.py test/test_display_format_writer.py test/test_dates.py test/test_help_conformance.py test/test_tracking_documents.py -q -p no:cacheprovider` ends 0 failed; `grep -c "U46-0[1-8] PASS" <scratch>/s46/run_test_wp31_truth.log` prints 8 and `grep -c FAIL` prints 0; `git log --format=%s <base>..HEAD | grep -c "(WP-31 "` prints 6; `grep -c "\(C11\|C12\|C16\|G6\|G7\|F5\) Tracked:\*\* Closed in WP-31.*commit pending" GAPS3.md` prints 6; `test -s <scratch>/s46/handback.txt`.]]></verify>
  <done>Fractional dates and rarea's one-bound rows draw as twoway's measured pictures, %d and %tb formats write calendar dates in both renderers, xvarformat(bogus) is refused in twoway's words, and S46's six commits were verified green.</done>
</task>

## Section completion criteria

- lpoly grids equal twoway's on the probes; D6-D8 matched; D1-D3/D5 documented; five rows matched; function per panel; recast recounted, never frozen; fractional dates and rarea bound per probe; `%d`/`%tb`/xvarformat per probe; comments true.
- Six green commits, each staging its own row's test file and truth block (A14); BUGS.md C11, C12, C16, G6, G7, F5 closed; six Tracked lines reading `commit pending` (A11); markers; fixture stamped and named; CHANGELOG Changed-behaviour lines for each newly refused form.

## Notes

- **R12:** S46 is batch 15's `_FILTER_JS` editor (two `if (ac.recast)` writes, the `@@DASH_LPOLY_EPS@@` token in `dash_lpoly` and its own `.replace` statement directly before :31459 -- A26); S45 edits `_DASH_AXIS_FINISH_JS` only, and its `_tok`/`repr(_val)` loop (:31446-31452) substitutes into that literal, not into `_FILTER_JS`, so S46 adds no row there.
- **JS slicing hazard** (research §3): the recast `if`s go inside the existing histogram/kdensity branches, after the `src.data` assembly and before `src.change.emit()`; js_runner's cut markers (`"src.data = { x: xs, y: ys };"`) must still match -- re-read the branch text before editing.
- **Copy lists (R2):** `_LPOLY_WEIGHT_EPS` in the constants tuple (emitted before `_shared_stat_lines` copies `_compute_lpoly_fit` and `_lpoly_local_wls`, :47482); any `%tb` helper after `"_dash_reference_lines",`.
- **R6:** `version 19` for `_dash_bcal_table`; `_needed` for any Mata addition; the seven key lists unchanged (`_bcal` and `panels` are written where `graph_options`/points are assembled).
- **R1:** five row blocks in the truth script (A14; F5 has none) and U46-09.. in test_option_validation.cscript, each appended by its row's closing step; test_parser.cscript's FX cases are run, not edited, unless the malformed words change an existing expectation (then flipped in place with `Flipped:`).
- **Renderer order:** the served app recomputes recast layers in Python already; C16 is the saved page's; parity tests compare the saved JS result with the served Python result.
- **python_exec hazard** as S40.
- **For S47 (function fallback, batch 16):** the points object may carry `panels`; the fallback reads the flat form or the panel entry the same way.
- **Decisions for ratification:** D-46b (D1-D3/D5 documented, not matched), D-46d (per-panel only when the x range differs).
