# Section 46: Estimator, function, recast and data-join edges

> Part of: WP-31 · GAPS3 rows: C11, C12, C16, G6, G7, F5 · Risk: yellow · Batch: 15 · Depends on: 01 · Blocks: -- · Tasks: 4, 6 commits · Case-id prefix: U46

## Overview

**What is wrong today.** GAPS3 C11 (GAPS3.md:130): "lpoly edges: gaussian weights below 1e-14 counted toward the two-observation rule (3 vs 23 points), round-off cases D1-D5, `pwidth(0)` and `pwidth(+800)` rc differences; lpoly with its own `if` on five rows draws an empty line (twoway unmeasured)." C12 (:131): "`function` under `by()` evaluated once, twoway once per panel; a malformed y-form echoed as typed." C16 (:135): "A recast kdensity or histogram is marked stale after a move where the un-recast one is recounted." G6 (:231): "Fractional %t values floored on load (twoway unmeasured); join-order edge cases (rarea one bound missing, tied sort keys, connected markers under sort)." G7 (:232): "`%d`/`%tb` axis formats drawn `%9.0g` with a note; `xvarformat(bogus)` noted (twoway: 'bogus not found')." F5 (:212, NEW): "`map_qfitci` docstring still describes a 500-resample bootstrap; the code is analytic (bootstrap only on LinAlgError). The header comment at :364-381 narrates fpfitci's former bootstrap. `_dash_fold_typed`'s comment says line types are always joined in x order (false since WP-29)."

Register detail (DROPIN-REMAINING P2.36): "twoway counts a gaussian weight toward the two-observation rule only above about 1e-14, so `lpoly mpg weight, kernel(gaussian) bwidth(1)` draws 3 points in Stata and 23 in dash (SD-10); exact fits differ where Stata's round-off decides (D1 `ylin=2*weight+1` degree 0, D2 `yw=weight` degree 0/1, D3 `mpg*1e-150` degree 2: a zero line); lpolyci rows whose pilot has no residual degrees of freedom are pinched where Stata is often missing (D4), and the pilot's round-off moves the se at 2 of 50 rows of `r1000_d2_bw600` (D5); `if _n==1, pwidth(0)` is refused r(198) where twoway counts first, r(2001) (D6); invalid-option messages name the option in dash's words (D7); `pwidth(+800)` is accepted where twoway gives r(3000) (D8)." P2.37: lpoly with its own `if` on five rows draws an empty line. P2.31: function under by() once (FX-24); malformed y-form echoed as typed. P2.90: recast density/histogram stale after a move. P2.32: fractional period values floored on load. P2.30: rarea one bound missing (O1), tied keys, connected markers under sort (O6). P2.63: `%d`/`%tb` and `xvarformat(bogus)`.

**After this section**: `_compute_lpoly_fit` counts a weight toward the two-observation rule only above the measured threshold (twoway's 3 points); each of D1-D8 is matched where the rule is readable (D6's order of checks, D7's words, D8's rc) and documented where it is Stata's round-off (D1-D3, D5) with the measured values; lpoly on five rows draws what twoway draws; a `function` layer under `by()` with a per-panel range is evaluated per panel by twoway's generator and the malformed y-form message is twoway's token; a recast histogram or kdensity is recounted after a saved move (tagged like the un-recast one, with a `recast` key the JS branch writes as x/y) and never marked stale; fractional `%t` values are drawn where twoway draws them (measured); rarea with one bound missing on a row keeps the other bound as twoway's polygon does (measured); `%d` is read as `%td`, `%tb<cal>` is written as the calendar's `%td` dates through a dash.ado-written calendar map, and `xvarformat(bogus)` is refused with twoway's words; the three stale comments are true.

**Why these rows share a section.** Six small, independent edges of the computed layers and the data join; the index names S46 the batch-15 owner of "lpoly/function/stale-kind edges" and, by R12, of `_FILTER_JS` for batch 15 (S45 edits `_DASH_AXIS_FINISH_JS` only; S44 no JS).

**Test order and commit rule.** Six cycles, one commit per row, in the order F5 (comments; no behaviour), C16, C11, C12, G6, G7. 46-01 measures and writes every red test (no commit); 46-02 commits F5 and C16; 46-03 commits C11 and C12; 46-04 commits G6 and G7 and hands back.

### Section decisions (binding on the executor)

- **D-46a. The lpoly weight threshold is measured, not assumed.** U46-02 records, for `lpoly mpg weight, kernel(gaussian) bwidth(1) n(50)`, the grid points where Stata's `lpoly` returns a non-missing smooth (through `lpoly ..., generate(xg yg) nograph`) beside dash's; the threshold is the largest power of ten t in {1e-10 .. 1e-20} such that counting weights `> t` gives exactly Stata's set for this probe and for `bwidth(0.5)`, `bwidth(2)` and `kernel(biweight)` (a biweight is exactly 0 outside the window, so the rule must not change it). `_LPOLY_WEIGHT_EPS` is written as that value with the probe in its comment; `pos = kw > _LPOLY_WEIGHT_EPS` at :17024-17026 (the one line), in Python and in the JS twin `dash_lpoly` (S19, landed batch 6) -- the JS edit is one comparison inside `_FILTER_JS`'s lpoly helper.
- **D-46b. D1-D8 branch on the measurement.** D6: dash's check order moves the observation count before `pwidth(0)` (twoway r(2001) "insufficient observations" first) -- dash.ado's lpoly rule in `_dash_option_rules` stays; `_dash_validate_opts` is not reordered (it has no row count); instead the renderer's `map_lpoly` raises the count refusal first and dash.ado's cell path... no: dash.ado does not count rows per layer. Ruling: D6 is matched in dash.ado by checking `pwidth(0)` AFTER the `if`/`in` row count that `_dash_plot` already computes for the cell cap (`count if ...` per segment exists for the weight check: reuse the segment's `_seg_n`); the refusal text is twoway's measured words. D7: the invalid-option messages for lpoly options take twoway's measured words (per option: `bwidth`, `pwidth`, `degree`, `n`, `kernel`) through the rules table's existing text slot (`_dash_validate_value`'s error form at :3615-3618 is dash's; a per-option override string in the rule token `opt=kind,...,msg=<id>` read from a fixture-driven Mata table is NOT built -- the words are typed into the rule as the fixture gives them, one `display as error` each). D8: `pwidth(+800)` -> twoway's rc (3000) and words, measured; dash refuses the `+` form with those words (a rule `pwidth=num,...` already exists; add the sign check in `_dash_validate_value`'s `num` kind only when the fixture says twoway refuses a leading `+` -- else nothing). D1-D3, D5: documented in the help's lpoly paragraph with the measured maximum difference (M17), no code.
- **D-46c. lpoly on five rows (P2.37) follows the probe.** U46-03 draws `lpoly mpg weight if foreign == 0` on the parity frame's five domestic rows (the frame of test_mode_parity `_DF`, exported to a dta by the extractor) and records the curve; dash matches (if twoway draws a curve, dash's empty line comes from the bandwidth rule `_default_lpoly_bwidth` returning non-finite on five rows -- then the rule is corrected by the measured r(bwidth)).
- **D-46d. `function` under by() is evaluated per panel only when the panel's range differs.** twoway's `twoway__function_gen` takes `range()` from the plotregion's x range (per panel under `xrescale`/`rescale`, the shared range otherwise); the function text itself cannot see the panel. dash.ado's `_dash_fn_points` (:8280-8394) is called once per layer at :7052 with `_fn_lo`/`_fn_hi`; under by() with a per-panel x range (S36's grammar: `xrescale`, `rescale`, `style(rescale)`), it is called once per panel with that panel's lo/hi and the points object gains a `panels` map (`"<k>": {"x0","dx","y"}` becomes `"<k>": {"panels": {"<by value>": {...}}}` -- or the flat form when one range). The renderer's `map_function` reads the panel's entry when present. The malformed y-form: U46-04 measures `function 2x`, `function y=`, `function =x` under twoway and copies the token twoway names (dash.ado :8280 region's refusal text).
- **D-46e. Recast density and histogram are tagged for the recount.** In `map_histogram`'s recast branch (:17995-18003) and the kdensity twin, the renderers returned by `_dash_draw_xy_as` get `_dash_agg_source = _mid`, `_dash_agg_config = dict(cfg, recast=<target>)` and `_dash_agg_rows` as the un-recast path tags them; `_FILTER_JS`'s histogram and kdensity branches, after computing bins/grid, write `src.data = {x: mids, y: tops}` when `ac.recast` is set (one `if` per branch); `_dash_stale_kind(ptype, options)` returns None when `options.get("recast")` on histogram/kdensity (today it never sees the recast because the type is still histogram -- the frozen tag comes from the missing config; with the config present the stale path is not taken: confirm by `test_saved_stale_cue.py` and keep `_dash_stale_kind` unchanged if so). js_runner gains a recast branch runner. `_FROZEN` in test_saved_stale_cue.py is unchanged (histogram/kdensity are not frozen types; the test gains a recast case).
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
(`_compute_lpoly_fit`, :16970-17060); `_lpoly_kernel_weights` (:22049) returns a gaussian that is positive everywhere, so every observation counts. `map_lpoly` options (:17150-17185): `bwidth` (warned to None when <= 0), `degree` 0-3, `kernel`, `n_grid`, the bandwidth rule `_default_lpoly_bwidth` (non-finite -> a zero line "as twoway"). `pwidth`: dash.ado:1912-1923 (lpolyci's `pwidth`/`var` sreturn), dash_render.py:17306 (`_positive("pwidth")`). test_statistical_truth.py::TestLpolyAgainstStata (:350-418) and `_lpoly_at` (:419).

### C12

dash.ado:8280-8300 (`_dash_fn_points raw_sc lo hi n k obj_sc` comment: "runs twoway__function_gen -- the generator twoway function itself calls -- as twoway calls it, and keeps the points"), :7052 (the one call per layer: `_dash_fn_points `_fx_raw' `_fn_lo_`_m'' `_fn_hi_`_m'' `_fn_n_`_m'' `_fn_k_`_m'' `_fp_sc'`), :6896 (range()/n() read), :5064 (comment). program_coverage_map.py:251 (`_dash_fn_points`: test_parser.cscript FX-01), :593, :598.

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
The agg tagging follows at :18011-18054 (histogram config keys `type, varname, bin_edges, ymode, wvar, wtype, discrete, start, width, bin`, dates) and :18380-18412 (kdensity); `_dash_stale_kind` (:1913-1930); `_frozen_layer_tag` (:43040), `_collect_frozen_layers` (:43078); the JS branches at :25213-25284 (histogram) and :25285-25375 (kdensity); js_runner.run_filter_js_block's cut markers (research codebase-mechanics §3). `_dash_draw_xy_as` (:20693).

### G6

Loader :606-620 ("a fraction is floored to the millisecond (%tc 1.9999 is .001 ...) or to the period that holds it (%tm 745.5 is 2022m2); a %td fraction keeps its time of day, as the value's place on an axis" -- measured 24sep2026 for DISPLAY; the AXIS position is P2.32's open question). `_join_order` (:16187-16236). `map_rarea` (:18494). P2.30 O1 (rarea one bound missing), O6.

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

- TR-46.1 (C11) `_LPOLY_WEIGHT_EPS` module constant after `_FIT_GRID` (:474) with the probe comment; `pos = kw > _LPOLY_WEIGHT_EPS` (:17024); copy list: constant after `_DASH_STALE_STATUS_HTML`'s group (R2) -- it is read inside `_compute_lpoly_fit`, which `_shared_stat_lines` copies, so the constant must be emitted before it: add to the constants tuple. JS: the same comparison in `dash_lpoly`'s weight loop (`_FILTER_JS`, S19's helper; grep `function dash_lpoly`). D6-D8 per D-46b in dash.ado (`_dash_process_segment`'s lpoly block near :5556-5574 and `_dash_validate_value` num kind :3166). The help's lpoly paragraph gains the D1-D3/D5 sentence with the fixture's maxima.
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
| SD-10 | `lpoly mpg weight, kernel(gaussian) bwidth(1)` | 3 finite points | 23 | threshold `_LPOLY_WEIGHT_EPS` (D-46a) |
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
JS twin: in `dash_lpoly`'s weight loop (S19), `if (kw[j] > <same literal>) { npos += 1; }` -- the literal is written through the `_FILTER_JS` constant substitution the module already uses for `_DASH_TS_PARAMS` (`_tok`/`repr(_val)` at :31452) so one Python constant feeds both.

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
- `_FILTER_JS`: the recast `if`s and the lpoly threshold comparison only; no new branch; helpers untouched.
- by() grammar is S36's; S46 reads its rescale state.
- `_join_order`'s stable sort stays (ties documented).

## Stata truth

Script `scripts/extract_estimator_edges_truth.do` -> `test/fixtures/estimator_edges_truth.json`.

| Key | Probe | Recorded |
|---|---|---|
| `lp.gauss_bw1`, `lp.gauss_bw05`, `lp.gauss_bw2`, `lp.biweight_bw1` | `lpoly mpg weight, kernel(k) bwidth(b) n(50) generate(xg yg) nograph` | xg, yg (missing as null) |
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

Truth block `* ==== S46 C11 C12 C16 G6 G7 F5: Estimator and data edges ====`: U46-01 fixture stamped; U46-02 dash's lpoly finite grid points (python helper running `GlyphMapper._compute_lpoly_fit`) equal `lp.gauss_*`/`lp.biweight_bw1`'s non-missing set; U46-03 `lp.five_rows` drawn equal in both modes; U46-04 `function` under by(foreign, xrescale): the spec's per-panel points' ranges equal `fn.by_rescale`; the four malformed forms give dash twoway's rc and words (same session); U46-05 the saved page's JS recast branch recounts after a move (python helper through js_runner) and no stale cue is tagged; U46-06 `dt.*` and `ra.one_bound` drawn as measured in both modes; U46-07 `%d`/`%tb` tick labels and tooltips equal `fmt.*` in both modes and `xvarformat(bogus)` returns twoway's rc and words; U46-08 D6-D8 rc/words equal twoway's. Refusal cases also appended to test_option_validation.cscript as U46-09.. (`_ov_assert`, `capture twoway` beside `capture dash`).

## TDD test stubs

### `test/test_estimator_edges.py` (new)

- `TestTheFixture::test_meta` (guard).
- `TestLpolyThreshold::test_gaussian_grid_points[case]` (red: 23 vs 3), `::test_biweight_unchanged` (guard), `::test_js_twin_agrees` (node; red), `::test_statistical_truth_still_green` (runs `_lpoly_at` over the existing truth; guard).
- `TestLpolyRefusals::test_D6_order` (cscript half U46-08; pytest: `map_lpoly` on one row raises the measured text? no -- dash.ado's; pytest pins the renderer draws a zero line silently on one row, guard), `::test_D7_words` and `::test_D8_plus` through the spec-level ado log fixture (red).
- `TestLpolyDocumented::test_help_names_the_maxima` (red).
- `TestLpolyFiveRows::test_matches_twoway[mode]` (red or guard by probe).
- `TestFunctionPerPanel::test_points_per_panel[mode]` (red), `::test_flat_form_when_one_range` (guard), `::test_malformed_words` (ado log; red).
- `TestRecastRefit::test_tagged[type]` (red: no `_dash_agg_config`), `::test_js_equals_python[type]` (red), `::test_not_frozen[type]` (red: tagged frozen), served `::test_served_recount[type]` (guard: served recomputes).
- `TestFractionalDates::test_tm_half[mode]`, `::test_td_half[mode]` (red or guard).
- `TestRareaOneBound::test_polygon_keeps_other_bound[mode]` (red if measured so).
- `TestFormats::test_percent_d_is_td`, `::test_tb_ticks[mode]`, `::test_tb_tooltip_js` (node), `::test_tb_bound_notes`, `::test_xvarformat_bogus_words` (ado log) (red).
- `TestComments::test_qfitci_docstring`, `::test_header_no_bootstrap_narrative`, `::test_fold_typed_comment` (source scans; red).

### Flips

From `<scratch>/s46/46-flips.txt` (gaussian point counts, `%d`/`%tb` refusal nodes, stale-cue recast node, dash's D7 words); reasons per row.

### cscript: U46-01..U46-08 (truth), U46-09.. (option validation). Parity: `CORPUS` "lpoly gaussian bwidth(1)", "histogram recast(line)", "%tb axis"; `MOVE_CORPUS` "histogram recast(line), dropdown to Foreign", "kdensity recast(area), range".

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| lpoly threshold, D1-D8, five rows | pytest + U46-02/03/08 + option cscript | estimator_edges_truth.json | yes |
| function per panel, malformed | pytest + U46-04 | same | yes |
| recast recount | pytest (node) + U46-05 + parity moves | -- | yes |
| fractional dates, rarea bound | pytest + U46-06 | same | yes |
| %d, %tb, xvarformat | pytest + U46-07 | same | yes |
| comments | pytest source scans | -- | n/a |

AC-46.1..AC-46.6 one per BR; AC-46.7 six green commits.

## Tasks

**Commit boundary.** 46-01 tests (no commit); 46-02 commits F5 `Correct the qfitci, header and fold_typed comments (WP-31 F5)` then C16 `Recount a recast histogram or kdensity after a saved move (WP-31 C16)`; 46-03 commits C11 `Match lpoly's weight threshold and option refusals to twoway's (WP-31 C11)` then C12 `Evaluate function layers per by() panel and copy twoway's malformed-form words (WP-31 C12)`; 46-04 commits G6 `Draw fractional dates and rarea's one-bound-missing rows as twoway does (WP-31 G6)` then G7 `Read %d and %tb formats and refuse xvarformat(bogus) with twoway's words (WP-31 G7)` and hands back. `$WT=<worktrees>/wp31-s46`.

<task type="auto" id="46-01">
  <name>Measure the six edges and write failing tests</name>
  <files>scripts/extract_estimator_edges_truth.do, test/fixtures/estimator_edges_truth.json, test/test_estimator_edges.py</files>
  <action><![CDATA[
    Check the worktree (wp31-s46 at the batch-15 base); re-read `_FILTER_JS`'s histogram/kdensity branches and `dash_lpoly` at this base and write their anchors to `<scratch>/s46/anchors.txt`. Create the extractor from the table (head as scripts/extract_date_axes_truth.do; the parity frame written to dta via python `pandas.DataFrame.to_stata` from test_mode_parity's `_DF`; `bcal create` in the work dir; `_meta`); run through the slot; `git add -f`. Create test/test_estimator_edges.py with the stub classes; add `test_a_recast_histogram_is_not_frozen` to test/test_saved_stale_cue.py. Run both `-q -n0 -p no:cacheprovider -rf > <scratch>/s46/46-01.log`; write `<scratch>/46-01-failure.txt` grouped by row. Write U46-01..U46-08 in the S46 block and U46-09.. in test_option_validation.cscript; run both through the driver (`WP31_ONLY=S46`); append FAIL lines. Simulated fix for the flips -> `<scratch>/s46/46-flips.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/estimator_edges_truth.json'));print(sorted(d['_meta']), sum(k.startswith('lp.') for k in d), 'fmt.tb_default' in d)"` prints the five keys, at least 13, True; `grep -c FAILED <scratch>/s46/46-01.log` is at least 15; `grep -c "U46-0[2-8] FAIL" <scratch>/s46/run_test_wp31_truth.log` is at least 5; `test -s <scratch>/46-01-failure.txt`.]]></verify>
  <done>twoway's lpoly grids, refusal words, per-panel function ranges, fractional-date positions, rarea polygon, business-date texts and xvarformat words were recorded, and every regression test and truth case was shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="46-02">
  <name>Fix the comments and recount recast layers, commit F5 and C16</name>
  <files>dash_render.py, dash.ado, test/js_runner.py</files>
  <action><![CDATA[
    Apply TR-46.6 (D-46h); run test_estimator_edges.py::TestComments; close BUGS.md F5, Tracked, marker (no CHANGELOG Results line: comments only -- replace the marker with a line under `### Fixed in WP-31`); commit `(WP-31 F5)`. Then apply TR-46.3 (tagging in both recast branches; the two `if (ac.recast)` writes in `_FILTER_JS`; js_runner's recast flag); run TestRecastRefit, test_saved_stale_cue.py, test_saved_filter_layers.py -k recast, test_statistical_helpers.py::TestFilterJavaScript, test_mode_parity.py -k recast, test_csp.py, and U46-05; help's recast sentence; close C16, Tracked, marker (Results: "recast histogram/kdensity after a saved move: frozen with the cue -> recounted"); commit `(WP-31 C16)`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_estimator_edges.py -k "Comments or RecastRefit" test/test_saved_stale_cue.py test/test_csp.py -q -p no:cacheprovider` ends 0 failed; `grep -c "U46-05 PASS" <scratch>/s46/run_test_wp31_truth.log` prints 1; `git log --format=%s -2 | grep -c "(WP-31 \(F5\|C16\))"` prints 2.]]></verify>
  <done>The three comments describe the code, and a recast histogram or kdensity is recounted by the saved page's own script after a move with no stale cue; the F5 and C16 commits landed.</done>
</task>

<task type="auto" id="46-03">
  <name>Match lpoly's threshold and refusals, evaluate function per panel, commit C11 and C12</name>
  <files>dash_render.py, dash.ado, dash_parse.mata</files>
  <action><![CDATA[
    Apply TR-46.1 per D-46a/D-46b/D-46c (the constant from the fixture; the JS comparison; D6-D8 in dash.ado by the fixture's rc/words; the five-row branch), copy-list entry for `_LPOLY_WEIGHT_EPS`, the help's lpoly sentences with `lp.D1..D5` maxima; flip the gaussian-count and D7-words nodes; run TestLpoly*, test_statistical_truth.py, test_statistical_helpers.py (lpoly JS twin), test_lpoly*.py, test_option_validation.py, test_option_validation.cscript (U46-09..) and U46-02/03/08; CHANGELOG Changed-behaviour lines for D6/D8 forms; close C11, Tracked, marker; commit `(WP-31 C11)`. Then apply TR-46.2 (per-panel `_dash_fn_points`, Mata JSON form, `map_function`'s panel read, the malformed words), program_coverage_map.py; run TestFunctionPerPanel, test_function*.py, test_by*.py -k function, test_parser.cscript (FX cases) through the driver, test_program_coverage_map.py, U46-04; help's function sentence; close C12; commit `(WP-31 C12)`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_estimator_edges.py -k "Lpoly or Function" test/test_statistical_truth.py test/test_option_validation.py test/test_program_coverage_map.py -q -p no:cacheprovider` ends 0 failed; `grep -c "U46-0[2348] PASS" <scratch>/s46/run_test_wp31_truth.log` prints 4; `grep -c "ALL CHECKS PASSED" <scratch>/s46/run_test_option_validation.log` prints 1; `git log --format=%s -2 | grep -c "(WP-31 C1[12])"` prints 2.]]></verify>
  <done>lpoly counts weights as twoway does and refuses as twoway refuses, with the round-off cases documented, and function layers are evaluated per rescaled panel with twoway's malformed-form words; the C11 and C12 commits landed.</done>
</task>

<task type="auto" id="46-04">
  <name>Draw fractional dates, rarea bounds, %d and %tb; commit G6 and G7</name>
  <files>dash_render.py, dash.ado, dash.sthlp</files>
  <action><![CDATA[
    Apply TR-46.4 per `dt.*`/`ra.one_bound` (D-46f); flip the date-position nodes; run TestFractionalDates, TestRareaOneBound, test_dates.py, test_range*.py, test_mode_parity.py -k rarea, U46-06; help's join-order and date sentences; close G6 (Resolution documents ties and O6 as twoway's random order), Tracked, marker; commit `(WP-31 G6)`. Then apply TR-46.5 (`%d`, `%tb` tables with the 10,000 bound, writer args, JS twin, `xvarformat(bogus)` words; `_dash_bcal_table` program version 19; program_coverage_map.py; function_test_map.py if a helper is added); flip the `%d`/`%tb` note nodes; run TestFormats, test_display_format_writer.py, test_dates.py, test_label_sinks.py::TestJavaScript, test_statistical_helpers.py::TestTheServedAppCarriesEveryName, U46-07; CHANGELOG Changed-behaviour line for `xvarformat(bogus)`; help's date-format paragraph; close G7, Tracked, marker; commit `(WP-31 G7)`. Run test_estimator_edges.py whole and the S46 block once more; write `<scratch>/s46/handback.txt` (six shas; the branches taken with measured values; D1-D3/D5 maxima; the `%tb` bound).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_estimator_edges.py test/test_display_format_writer.py test/test_dates.py test/test_help_conformance.py test/test_tracking_documents.py -q -p no:cacheprovider` ends 0 failed; `grep -c FAIL <scratch>/s46/run_test_wp31_truth.log` prints 0; `git log --format=%s <base>..HEAD | grep -c "(WP-31 "` prints 6; `test -s <scratch>/s46/handback.txt`.]]></verify>
  <done>Fractional dates and rarea's one-bound rows draw as twoway's measured pictures, %d and %tb formats write calendar dates in both renderers, xvarformat(bogus) is refused in twoway's words, and S46's six commits were verified green.</done>
</task>

## Section completion criteria

- lpoly grids equal twoway's on the probes; D6-D8 matched; D1-D3/D5 documented; five rows matched; function per panel; recast recounted, never frozen; fractional dates and rarea bound per probe; `%d`/`%tb`/xvarformat per probe; comments true.
- Six green commits; BUGS.md C11, C12, C16, G6, G7, F5 closed; Tracked lines; markers; fixture stamped and named; CHANGELOG Changed-behaviour lines for each newly refused form.

## Notes

- **R12:** S46 is batch 15's `_FILTER_JS` editor (two `if (ac.recast)` writes and one comparison in `dash_lpoly`); S45 edits `_DASH_AXIS_FINISH_JS` only.
- **JS slicing hazard** (research §3): the recast `if`s go inside the existing histogram/kdensity branches, after the `src.data` assembly and before `src.change.emit()`; js_runner's cut markers (`"src.data = { x: xs, y: ys };"`) must still match -- re-read the branch text before editing.
- **Copy lists (R2):** `_LPOLY_WEIGHT_EPS` in the constants tuple (emitted before `_shared_stat_lines` copies `_compute_lpoly_fit`); any `%tb` helper after `"_dash_reference_lines",`.
- **R6:** `version 19` for `_dash_bcal_table`; `_needed` for any Mata addition; the seven key lists unchanged (`_bcal` and `panels` are written where `graph_options`/points are assembled).
- **R1:** U46-09.. in test_option_validation.cscript; test_parser.cscript's FX cases are run, not edited, unless the malformed words change an existing expectation (then flipped in place with `Flipped:`).
- **Renderer order:** the served app recomputes recast layers in Python already; C16 is the saved page's; parity tests compare the saved JS result with the served Python result.
- **python_exec hazard** as S40.
- **For S47 (function fallback, batch 16):** the points object may carry `panels`; the fallback reads the flat form or the panel entry the same way.
- **Decisions for ratification:** D-46b (D1-D3/D5 documented, not matched), D-46d (per-panel only when the x range differs).
