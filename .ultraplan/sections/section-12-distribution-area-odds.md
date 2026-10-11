# Section 12: Distribution, area and bar odds (kdensity area()/boundary, histogram gap(), function droplines()/base(), area nodropbase, bar baroffset())

> Part of: WP-31 · GAPS3 rows: C5 · Risk: yellow · Batch: 4 · Depends on: 04 · Blocks: -- · Tasks: 4, 1 commit · Case-id prefix: U12

## Overview

**What is wrong today.** GAPS3 C5 (GAPS3.md:124): "kdensity `area()`, `boundary`; histogram `gap()`; function `droplines()`, `base()`; area `nodropbase`; bar `baroffset()` named, not drawn." Evidence: dash_parse.mata:6263-6298 -- `_dash_rep_und_tab` rows `baroffset` (:6263, types `rbar`), `boundary` (:6272, `kdensity`), `dropbase`/`nodropbase` (:6297-6298, `*`); `area()`, `gap()` and `droplines()` have no row and fall to the catch-all; dash.sthlp:3075-3077 says twoway "also takes base() on dot ... and on function, as the base of droplines() -- neither of which dash draws". `base()` on function is declared (`BASE(string asis)`, dash.ado:1177) and written to the spec (:4443) but `map_function` (dash_render.py:20567-20688) never reads it. Each of the seven is accepted by twoway and drawn (research/stata-ground-truth.md §12).

**After this section** both renderers draw them:
- `histogram ..., gap(#)`: each bar's width is `binwidth * (100 - gap) / 100`, centred on its bin (`twoway_histogram_parse.class:193` `.bar_size = barwidth*(100-hist_gap)/100`); `gap()` outside `0 <= # < 100` is refused `option gap() must be between 0 and 100` r(198) (:63-66). `histogram ..., baroffset(#)` moves each bar by `# * bar_size` (`:195-196`, `yxview__barlike_draw.ado:68-69` `off = bar_offset*bar_size`).
- `kdensity ..., area(#)`: every density value is multiplied by `#` (`twoway__kdensity_gen.ado:174` `replace y = y*area`); `# <= 0` refused `option area() expects a positive number` r(198) (:66-68). `kdensity ..., boundary`: the evaluation range is `[min - h, max + h]` where `h` is the user's `width()`/`bwidth()` else `0.9*min(sd, (p75-p25)/1.349)/N^0.2` (:79-102; `summ, detail` so the percentiles are Stata's); `boundary` with `range()` refused `options range() and boundary may not be combined` r(198) -- twoway's `opts_exclusive "range() boundary"` text, measured in U12-02 and copied from the fixture, never typed.
- `function ..., droplines(numlist)`: a vertical line from `(x, base)` to `(x, f(x))` for each x, in the series line style, drawn BEFORE the curve (`_fr_droplines_draw.ado:16-51`: `gdi line x base x y`; horizontal when `horizontal`); x outside `range()` refused `some droplines not within range() option` r(198) (`twoway__function_gen.ado:152-155`). `base(#)` is the droplines' base; unset, twoway's default base: 0 when the y scale spans 0, else the scale end nearer 0 (`_fr_droplines_draw.ado:25-37`; the same rule as `_dash_finish_auto_bases` applies to bar/spike/dropline/area, WP-30 P1.17b).
- `area ..., nodropbase`: the polygon closes along the segment from `(x1, y1)` to `(xN, yN)` instead of dropping to the base (`twoway_area.sthlp:166-172`; `yxview_parse:189,280-282,1144-1146` `.drop_base = 0`).
- `bar ..., baroffset(#)`: every bar's centre moves by `# * barwidth` (`twoway_bar.sthlp:136-139`; `yxview__barlike_draw.ado:68-69`), negative left.

**Why one section.** The seven are small, independent geometric readers in five mappers S12 owns in batch 4 (`map_histogram` :17911, `_histogram_quads` :17863, `map_kdensity` :18258, `map_function` :20567, `map_area` :15166, `map_bar` :15272); none needs new Stata runs or JavaScript. The kdensity options also reach the saved page's `kdensity` recompute branch (`_FILTER_JS` :25285-25375) -- which S12 may NOT edit (S16 owns `_FILTER_JS` in batch 4, DECISIONS A22): S12 writes the config keys and S16 reads them in the same batch (D-12b).

**Test order and commit rule.** One row, one commit `(WP-31 C5)`: 12-01 failing tests + extractor; 12-02 dash.ado declarations and refusals; 12-03 renderer; 12-04 certify, document, commit.

### Section decisions (binding on the executor)

- **D-12a. `baroffset()` on bar and histogram, `gap()` on histogram only.** twoway factors `BAROFFset` for every bar-derived type (`yxview_parse:781-800`: bar, area, dot, dropline, scatteri, spike, rbspike) and declares it again for rbar/rbarm (`y2xview_parse:68-81`) and histogram (`histogram_parse:46-55`). S12 draws it on `bar` and `histogram` (C5's row); rbar's `baroffset()` is S03's (`map_rbar`, batch 1) and is noted in Boundaries; on area/dot/dropline/spike twoway accepts it and draws nothing different for a non-bar glyph except dot (`.bar_offset` moves dot rows too: S18 reads it in batch 6). Here `baroffset()` is declared for all and drawn where named; elsewhere it is silent (twoway draws nothing different), so it is not named -- it leaves the generic note entirely.
- **D-12b. The saved page's refit of `gap()`, `baroffset()`, `area()` and `boundary` goes through the config; S16 reads the new keys in batch 4.** `map_kdensity` writes `r._dash_agg_config` (:18380-18412) with `x_grid`, `bw_rule`, `bw_fixed`; `map_histogram` writes its config at :18011-18054. S12 adds the keys `gap`, `baroffset` (histogram) and `area` (the multiplier, default 1.0), `boundary` (`true`/`false`) (kdensity). S16, batch 4's `_FILTER_JS` owner (DECISIONS A22), reads them in the histogram and kdensity branches (section-16 TR-16.10): `left/right` from `ac.gap`/`ac.baroffset` by TR-12.4's formula, the density multiplied by `ac.area || 1`, the grid widened one bandwidth under `ac.boundary`; every read is default-safe when a key is absent, so the two worktrees merge in either order (16 then 12 in the batch table). No residual, no cue: C5 closes fully in batch 4 and the saved page matches the served app after a move.
- **D-12c. `boundary`'s bandwidth is dash's `_stata_kde_bandwidth`** (:21850), which is `0.9*min(sd, IQR/1.349)/n^0.2` with Stata's percentile definition and the weighted forms -- the same arithmetic `twoway__kdensity_gen.ado:88-96` writes; `bwidth()`/`width()` given, `h` is that value (:85 `wwidth = width`). The default grid is 300 points over `[min-h, max+h]`.
- **D-12d. The droplines base follows `_dash_finish_auto_bases`.** `map_function` draws the droplines as a Segment renderer tagged `_tag_base(r, "y0", auto, zero)` with a base column `__dash_base` (`_BASE_COL`, :15469) when `base()` is unset, so the base follows the axis after a move exactly as bar/spike/dropline do (WP-30 P1.17b). An explicit `base(#)` is a constant.
- **D-12e. `nodropbase` is a Patch, not a VArea.** A VArea fills between two y columns and cannot close along a chord; the nodropbase polygon is `fig.patch(x=[x1..xN], y=[y1..yN])` (the chord is the implicit closing edge) with the same fill/line styling `map_area` applies; the source carries the layer's rows in join order so the hover and saved move work as for the VArea (the saved page's row filter keeps rows; the chord re-closes on whatever rows remain -- twoway draws the same on a subset).

## Risk: [yellow] -- seven readers in five mappers, two of them on the histogram and kdensity paths that the saved page recomputes

**Why.** `map_histogram` and `map_kdensity` feed the saved page's JS recompute through `_dash_agg_config`; a width or range change in Python that the JS does not know re-appears on the first move. Histogram's `gap()` changes bar geometry the JS rebuilds from `start/width/bin`.

**Risk factors.** 1. Histogram gap: the JS branch draws bars `start + k*width .. start+(k+1)*width`; with `gap()` the Python bars are narrower; after a move the JS redraws full-width bars. 2. kdensity area()/boundary (D-12b). 3. droplines on a date axis (function x in date units, WP-30 P1.23a). 4. `nodropbase` changes the glyph class (VArea → Patch): tests that assert VArea on area. 5. `baroffset()` moves bars off their x: the axis hull (S21-era extents) reads `__dash_bar_xc`/width.

**Mitigation.** 1. Histogram: the config gains `gap` and the Python side writes the quad edges from the SAME formula the JS uses plus the gap; S16 reads `ac.gap`/`ac.baroffset` in the same batch (D-12b; A22) -- S12's `TestHistogramGap::test_saved_refit_keeps_the_gap` is written against S16's branch and is green once both have landed (red in S12's worktree alone: run it last and record the red as expected in the hand-back if S16 has not landed). 2. D-12b. 3. The droplines' x pass through `_literal_on_axis` as the curve's x do (:20660-20662). 4. `TestMapArea` tests in test_glyphs.py (:260-290) assert VArea for a default area, untouched; `nodropbase` adds a new path with its own tests. 5. baroffset writes `__dash_bar_xc` shifted; `test_axis_extents.py TestBars` reads centre and width columns, so the hull follows.

## Dependencies

- **Depends on: 04.** S04's applicability refuses `gap()` outside histogram, `area()`/`boundary` outside kdensity, `droplines()` outside function, `nodropbase` outside area/rarea? -- NO: twoway factors `noDROPBase` for every yxview type (research §1.2), so it is accepted everywhere and draws nothing but on area (and rarea); S04's table must not refuse it. S12 declares the names; S04's rows find them.
- **Blocks:** none. **Parallel batch 4** with S16 (`_FILTER_JS`, js-lowess; S13 and S16 swapped batches, DECISIONS A22) and S11 (fit mappers); merge order 16, 11, 12. **Can run with S16 and S11.** S12 edits no fit mapper, no `_FILTER_JS`, no `_render_ci_band`; S16 reads the four config keys S12 writes (D-12b).

## Evidence

Anchors at `6370ca4`.

### Histogram bars

`_histogram_quads` (dash_render.py:17863-17910): `r = fig.quad(top="top", bottom=0, left="left", right="right", source=source, ...)`; `map_histogram` (:17911-18060) builds `left/right` from the bin edges and writes the config at :18011-18054 with keys `type, varname, bin_edges, ymode, wvar, wtype, discrete, start, width, bin` (+ date keys). No `gap` or `baroffset` is read anywhere (`grep -n "gap\|baroffset" dash_render.py` finds only mlabgap and the memo).

### kdensity

`map_kdensity` (:18258-18420): `bw = _stat_option_float(options, "bwidth", default_bw, ...)` (:18275), `_rng = _dash_range_pair(options, "kdensity", ...)` (:18306), `x_range = np.linspace(_lo, _hi, n)` (:18310), `density = _kde_curve(arr, x_range, bw, kernel, w)` (:18312); config :18380-18412. `area` and `boundary` are not read.

### function

`map_function` (:20567-20688): points from the stored `points` or the fallback grid; `fn_source = ColumnDataSource({"x_fn": x_arr, "y_fn": y_arr})`; one `_dash_join_glyph` line. `options["base"]` and `options.get("droplines")` are never read. dash.ado writes the function's `range` and `n` to the spec at :5905-5918 (`_fn_lo`, `_fn_hi`); `droplines()` is undeclared.

### area and bar

`map_area` (:15166-15271): `y1_base` column `f"{yvar}_base"` filled with `_zero`/`_base`; `fig.varea(x=xvar, y1=_y1_col, y2=yvar, source=area_source, ...)` (:15209); `_tag_base(r, "y1", _base is None, _zero)`. `map_bar` (:15272-15420): `x_field, width_spec, _bar_ext = self._bar_extent(xvar, df[xvar], bar_width, fig=fig, options=options)` (:15357-15358), `fig.vbar(x=x_field, width=width_spec, bottom=..., top=yvar, ...)` (:15381-15405). `_bar_extent` (:15510-15556) returns `(xvar, w, {})` on a numeric axis and `(self._BAR_XC, self._BAR_W, {cols})` on a period axis.

### twoway's rules (research/stata-ground-truth.md §12; sources read 10oct2026)

- `twoway_histogram_parse.class:63-66`: `if gap < 0 | 100 <= gap { di as err "option gap() must be between 0 and 100"; exit 198 }`; `:193` `.bar_size = barwidth*(100-hist_gap)/100`; `:195-196` `.bar_offset = baroffset`.
- `twoway__kdensity_gen.ado:42-48` `opts_exclusive "range() boundary"`; `:66-68` area message; `:79-102` the boundary bandwidth: `summ x [w], detail`, `wwidth = width` or `0.9*min(r(sd),(r(p75)-r(p25))/1.349)/r(N)^.2`, `min = r(min) - wwidth`, `max = r(max) + wwidth`; `:174` `replace y = y*area`.
- `twoway__function_gen.ado:152-155` droplines range check; `:184-191` `r(dropxy)` pairs `"x y"`; `_fr_droplines_draw.ado:16-51` base rule and `gdi line x base x y` before the curve (`BaseDraw` after unless `basestyle == "area"`).
- `twoway_function_parse.class:94-99` `option base() incorrectly specified, <v> is not a number` (printed, then `.base = base` -- rc 0? measured in U12-05, the fixture decides).
- `yxview__barlike_draw.ado:68-69` `off = bar_offset*bar_size`.

### Fixtures on disk

`test/fixtures/default_base_truth.json` (the base rule and axis scale per type: reused for the droplines base), `stat_truth.json` (kdensity bandwidths), `recast_truth.json`. New: `kde_hist_fn_truth.json` (Stata truth below).

### Pinned tests to flip (never delete)

- test/test_unsupported_report_is_true.py: declared plot count (:725-726; 196 at 6370ca4) moves by +6 (`GAP BAROFFset AREA BOUNDary DROPlines noDROPBase`; `base` is already declared): re-measure the old value at the section's base with the file's `_declared_plot_options()` helper (S04 and S11 may have moved it) and write `# <measured old> -> <measured old + 6>: C5 gap baroffset area boundary droplines nodropbase declared` (A33). `PLOT_VALUES` has no entry for any of the seven (none is pending); `LIVE_VALUES` gains seven entries (TR-12.8).
- test/test_glyphs.py `TestMapArea::test_area_baseline_is_zero` (:260-290) asserts a VArea with a base column: unchanged for the default; no flip.
- test/test_help_claims_6.py `TestRangeOnTheFits` / kdensity range tests: `boundary` adds a path but changes no existing expectation.
- test/test_abbreviations.py (:406 prefixes): `AREA` vs `AColor`/`ASTyle`/`ALstyle`: `area` claims the exact word `area` only (minimum 4 letters = full), no overlap with `ac`/`asty`/`als`; `GAP` is exact; `BOUNDary` minimum `bound` (twoway's is the full word `boundary` per `kdensity_parse:48-65` -- declare `BOUNDARY` with no abbreviation to match twoway; abbrev_truth.json decides in 12-02); `DROPlines` minimum `drop`: collides with nothing (`dropline` is a plot type, not an option); `noDROPBase` minimum `nodropb`.

## User stories

- US-12.1 As a Stata user pasting `twoway histogram mpg, gap(20)`, I want bars 80% of the bin width, so that the picture matches twoway.
- US-12.2 As a Stata user, I want `kdensity mpg, area(74)` to draw the density scaled to counts under the histogram, and `boundary` to extend the curve one bandwidth past the data, as twoway does.
- US-12.3 As a Stata user, I want `function y = x^2, range(-2 2) droplines(-1 1) base(1)` to draw the two drop lines from y = 1 to the curve.
- US-12.4 As a Stata user, I want `area mpg weight, nodropbase` to close along the chord, and `bar mpg weight, baroffset(.5)` to draw the bars half a bar to the right.
- US-12.5 As a Stata user, I want the refusals twoway gives (`gap(120)`, `area(0)`, `boundary range(...)`, a dropline outside range()) with twoway's words.

## Business requirements

- BR-12.1 Histogram bars are `binwidth*(100-gap)/100` wide, centred; `gap()` outside [0,100) is refused with twoway's text and rc.
- BR-12.2 kdensity densities are multiplied by `area()`; `area(<=0)` refused with twoway's text; `boundary` widens the evaluation range by one bandwidth each side; `boundary` with `range()` refused with twoway's text.
- BR-12.3 Function droplines are drawn from the base to the curve at each listed x, before the curve, in the line's style; an x outside `range()` is refused with twoway's text; `base()` unset uses twoway's default base.
- BR-12.4 `nodropbase` closes the area along the chord; `baroffset()` shifts bars by `#` bar widths on bar and histogram.
- BR-12.5 Nothing is printed for a drawn option; the served app draws every move exactly; the saved page's first picture is exact and its refit honours gap()/baroffset()/area()/boundary once S16's batch-4 read lands (D-12b).

## Technical requirements

- TR-12.1 **Declare** in `_dash_parse_plot_opts` syntax after `START(string) ///` (:1195): `GAP(string) BAROFFset(string) AREA(string) BOUNDARY DROPlines(string asis) noDROPBase ///` (twoway's minimums: `histogram_parse:46-55` writes `GAP(real 0) BAROFFSET(real 0)`; `y2xview_parse:68-81` `BAROFFset`; `kdensity_parse` `AREA(real 1)` and the bare word `boundary`; `function_parse:56-64` `DROPlines(numlist sort)`; `yxview_parse:189` `noDROPBase`). `sreturn local gap/baroffset/area/boundary/droplines/dropbase : copy local ...` after :1524. JSON keys after `pwidth lpvar` (:4458): `gap baroffset area boundary droplines nodropbase` (write `local nodropbase : copy local dropbase`). `_dash_option_rules` plot tokens (:2990-3008): `gap=num,0,100,x` is NOT used (the `x` strict flag applies to both ends; twoway's is `0 <= g < 100`): add kind `num,0,100` and refuse `gap(100)` explicitly in `_dash_process_segment` with twoway's text; `area=num,0,.,x` (strict > 0) with the extra sentence replaced by twoway's exact words (the `_dash_validate_value` error form is dash's own `dash: area() must be ...`; twoway's is `option area() expects a positive number` -- so do NOT use the rules table for area(); refuse it in `_dash_process_segment` with `display as error "option area() expects a positive number"`, `exit 198`); `baroffset=num`; `droplines=numlist,1`.
- TR-12.2 **Exclusivity and range checks** in `_dash_process_segment` after the barwidth-on-rcap refusal (:5564-5574): kdensity `boundary` + `range()` → the fixture's measured text (`options range() and boundary may not be combined`), r(198); function `droplines()` whose min < range lo or max > range hi → `some droplines not within range() option`, r(198) (the range is `_fn_lo`/`_fn_hi` computed at :5905-5918 -- move the check after them); function `base()` not a number → the fixture's measured behaviour (U12-05).
- TR-12.3 **Delete** `_dash_rep_und_tab` rows `baroffset` (:6263), `boundary` (:6272), `dropbase`, `nodropbase` (:6297-6298). None joins `_dash_rep_unique` (twoway's `syntax` refuses a repeated non-combop option with `option X() not allowed`? -- for `real`-typed options Stata's syntax refuses repeats r(198) `option gap() not allowed`; measured in U12-01 for gap() and area(); if refused, add `gap area baroffset boundary droplines dropbase` to `_dash_rep_unique`).
- TR-12.4 **Histogram** (`_histogram_quads`, `map_histogram`): read `gap = _stat_option_float(options, "gap", 0.0, "histogram", lo=0.0, hi=100.0)` and `off = _stat_option_float(options, "baroffset", 0.0, "histogram")`; for each bin with edges `(l, r)`, `w = r - l`, `bw = w*(100-gap)/100`, `c = (l+r)/2 + off*bw`, write `left = c - bw/2`, `right = c + bw/2`. Add `"gap": gap, "baroffset": off` to the config (:18011-18054); S16 reads them in batch 4 (D-12b).
- TR-12.5 **kdensity**: after `bw` is resolved (:18275-18290): `area = _stat_option_float(options, "area", 1.0, "kdensity", lo=0.0)`; `if str(options.get("boundary","")).strip(): _lo, _hi = float(np.min(arr)) - bw, float(np.max(arr)) + bw` (overriding the observed range; `range()` cannot coexist, dash.ado refused it); `density = _kde_curve(...) * area`; config gains `"area": float(area), "boundary": bool(...)`. Note `bw` here is the user's or `_stata_kde_bandwidth`'s (D-12c).
- TR-12.6 **function**: after `fn_source` is built (:20675) and before the curve: `drops = _dash_numlist_floats(options.get("droplines"))` (new module-level helper: splits on blanks, `float()` each, drops non-finite, sorted; returns `[]` on any error -- copy list after `_dash_reference_lines`, R2); `base = self._base_value(options, "function")`; `zero = self._base_zero("y_fn", fig, options)`; evaluate `f(x)` at each drop by linear interpolation on the stored points (`np.interp(drops, x_arr, y_arr)`; twoway evaluates the expression exactly -- for a stored-points layer dash.ado adds the drop x's to the generator call: `_dash_fn_points` passes `droplines()` to `twoway__function_gen` and stores `r(dropxy)` as `points["drops"] = [[x,y],...]`, which the renderer prefers when present; the interpolation is the hand-written-spec fallback); `drop_src = ColumnDataSource({"x0": xs, "y0": full(base or zero), "x1": xs, "y1": ys})`; `dr = fig.segment(x0="x0", y0="y0", x1="x1", y1="y1", source=drop_src, line_color=<the curve's line_color>, line_width=<the curve's line_width>)` BEFORE the curve's `_dash_join_glyph`; `self._apply_line_opts(dr, options)`; `self._tag_base(dr, "y0", base is None, zero)` -- `_BASE_PROPS` (:15496 assert) must include `"y0"`: add it. `horizontal`: swap x/y columns as the curve does under `_DASH_HORIZONTAL_TYPES` handling for function. Return `[dr, r]`.
- TR-12.7 **area/bar**: `map_area`: `if str(options.get("nodropbase","")).strip():` build `fig.patch(x=xvar, y=yvar, source=area_source, fill_color=..., fill_alpha=..., line_color=..., line_width=...)` with the same style resolution the VArea branch uses (:15209-15230) and `_apply_fill_opts`; no `_tag_base` (no base). `map_bar`: `off = _stat_option_float(options, "baroffset", 0.0, "bar")`; numeric axis: `x_field` becomes a new column `__dash_bar_xc = x + off*bar_width` (reuse `_BAR_XC`, so `_bar_extent`'s period branch and the numeric branch both write `_BAR_XC` when `off != 0`; the period branch adds `off*bw` to `xc`).
- TR-12.8 **Tests/pins**: LIVE_VALUES: `"gap": ({"gap":"10"},{"gap":"60"},"histogram",{})`, `"baroffset": ({"baroffset":".5"},{"baroffset":"-.5"},"bar",{})`, `"area": ({"area":"2"},{"area":"5"},"kdensity",{})`, `"boundary": ({"boundary":"boundary"},{},"kdensity",{})`, `"droplines": ({"droplines":"2500","range":"2000 5000"},{"droplines":"4000","range":"2000 5000"},"function",{})` -- the harness renders `yvar/xvar` plots; for function use `test_mode_parity`'s function spec form instead, or classify `droplines` in `NOT_IN_FILE`-style with a dedicated test in test_distribution_odds.py and a comment; `"nodropbase": ({"nodropbase":"nodropbase"},{},"area",{})`. FLAGS gains `boundary`, `nodropbase`. Declared counts comment `# 196 -> 202: C5 gap baroffset area boundary droplines nodropbase declared`.
- TR-12.9 **function_test_map.py**: `'_dash_numlist_floats': 'test/test_distribution_odds.py::TestDroplines::test_helper'`; **program_coverage_map.py**: no new program (the checks live in `_dash_process_segment`).

## Boundaries

- No `_FILTER_JS`, `js_runner.py`, `_dash_stale_kind`, `test_saved_stale_cue.py` edits (S16, batch 4, A22); the JS reads of the new keys are S16's TR-16.10.
- The dash.sthlp:2908-2912 sentence: S12 writes its FINAL text (merged last in batch 4; R2-21) -- its own clause and S11's fit clause both removed.
- No fit mapper or `_render_ci_band` edits (S11). No `map_rbar` edit (S03 owns rbar's `baroffset()`; S12 declares the option and `map_rbar` reads it in S03's follow-up or S18's batch if not yet -- record in Notes). No `map_dot` (S18 reads `baroffset()` for dot rows).
- PRD §7: nothing. `_dash_finish_auto_bases` is called, not edited.

## Stata truth

New `scripts/extract_kde_hist_fn_truth.do` → `test/fixtures/kde_hist_fn_truth.json`; `sysuse auto`:
- `H01` `twoway histogram mpg, gap(20) name(h1)`: `.h1.plotregion1.plot1.bar_size`, `.plot1.bar_offset`, the serset (bin centres, heights); `H02` `gap(100)` rc and message; `H03` `gap(-1)`; `H04` `baroffset(.5)` → `.plot1.bar_offset`, bar_size.
- `K01` `twoway kdensity mpg, area(74)` serset y vs `kdensity mpg, area(1)` (ratio 74); `K02` `area(0)` rc/message; `K03` `twoway kdensity mpg, boundary` serset x min/max and `r(width)` from `kdensity mpg` (= 1.9746142); `K04` `boundary range(10 30)` rc/message; `K05` `boundary bwidth(2)` serset x min/max.
- `F01` `twoway function y = x^2, range(-2 2) droplines(-1 1) base(1) name(f1)`: `.f1.plotregion1.plot1.droplines` (`"x y"` pairs), `.plot1.base`; `F02` `droplines(5)` rc/message; `F03` `function y = x^2, range(1 3) droplines(2)` → the default base from `.plotregion1.yscale.curmin/curmax` (expected 1: the scale does not span 0); `F04` `base(abc)` rc and message.
- `A01` `twoway area mpg weight, nodropbase` → `.plot1.drop_base` style; `B01` `twoway bar mpg weight in 1/5, baroffset(.5)` → `.plot1.bar_offset`, `.plot1.bar_size`.
`_meta` complete; `git add -f`; test_fixtures_are_committed.py entry.

## TDD test stubs

New `test/test_distribution_odds.py` (red at 6370ca4 unless guard):
- Test: histogram `gap(20)` quads are 0.8 bin wide, centred on the bin, both modes -- `TestHistogramGap::test_bars_are_shrunk_about_their_centre[mode]` (red); `gap(0)` equals today's picture -- `::test_gap_zero_is_unchanged` (guard); `baroffset(.5)` shifts left/right by half a bar -- `::test_baroffset_shifts[mode]` (red); the config carries `gap`/`baroffset` -- `::test_config_keys` (red).
- Test: kdensity `area(74)` y equals the unscaled curve × 74 -- `TestKdensityArea::test_density_times_area[mode]` (red); `boundary` grid runs `[min-h, max+h]` with `h` = `_stata_kde_bandwidth` or `bwidth()` -- `TestKdensityBoundary::test_grid_extends_one_bandwidth[mode]` (red); matches K03/K05's serset x min/max -- `::test_matches_twoway` (red).
- Test: function `droplines(-1 1) base(1)` draws a Segment renderer before the line with x0 = x1 = the drops, y0 = 1, y1 = f(x) -- `TestDroplines::test_segments_drawn_before_the_curve[mode]` (red); no `base()` tags `dash_base:` with `auto true` and the base follows `_dash_finish_auto_bases` -- `::test_default_base_is_tagged` (red); `_dash_numlist_floats` helper -- `::test_helper` (red); stored `points["drops"]` preferred over interpolation -- `::test_stored_drops_win` (red).
- Test: `nodropbase` draws a Patch whose polygon's first and last vertices are the first and last (x,y) -- `TestNodropbase::test_patch_closes_on_the_chord[mode]` (red); default area still VArea -- `::test_default_is_varea` (guard).
- Test: bar `baroffset(.5)` shifts `__dash_bar_xc` by half the width in both modes, and on a `%tm` axis the period branch adds the offset -- `TestBaroffset::test_numeric[mode]`, `::test_period_axis[mode]` (red).
- Test: the helper is on the copy list; dash.ado declares the six and `_dash_rep_und_tab` has no baroffset/boundary/dropbase row -- `TestTheServedCopy::test_names`, `TestTheAdoText::test_declared` (red).
- Test: fixture `_meta` -- `TestTheFixture::test_meta` (guard).

cscript, block `* ==== S12 C5: distribution, area and bar odds ====`:
- U12-01 `histogram mpg, gap(20)` dash vs twoway: `.bar_size` equals dash's quad width (python read of the saved page's quads through `_dash_serve_spec` + render); `gap(20) gap(30)` twice: dash rc = twoway rc.
- U12-02 refusals: `gap(100)`, `gap(-1)`, `area(0)`, `kdensity mpg, boundary range(10 30)`, `function y=x, range(0 1) droplines(2)`: dash rc = twoway rc and the message line matches (`cert_log_has`).
- U12-03 `kdensity mpg, area(74)`: dash's curve y / twoway serset y = 1 within 1e-9 at each x; `boundary`: dash's x min/max equal twoway's serset min/max within 1e-9.
- U12-04 `function y = x^2, range(-2 2) droplines(-1 1) base(1)`: the spec's `points.drops` equals `.plot1.droplines`; render has a Segment with y0 = 1.
- U12-05 `function ..., base(abc)`: dash's rc and message equal twoway's (the fixture F04 decides whether it is a refusal or a note).
- U12-06 `area mpg weight, nodropbase`: dash renders a Patch; twoway `.plot1.drop_base` is `no`.
- U12-07 `bar mpg weight in 1/5, baroffset(.5)`: dash's bar centres = x + 0.5*1 (twoway bar_size 1, bar_offset .5).
Area-script: U12-08 (test_option_validation.cscript) `scatter mpg weight, gap(5)` → rc 198 `option gap() not allowed` from dash and twoway (S04's table).

Parity (R8): CORPUS `_case("histogram gap(20) baroffset(.5)", ...)`, `_case("kdensity area(74) boundary", ...)`, `_case("function droplines", [{"type":"function","expr":"y = x^2","options":{"range":"-2 2","droplines":"-1 1","base":"1"}}])`, `_case("area nodropbase", ...)`, `_case("bar baroffset(.5)", ...)`; MOVE_CORPUS `_case("bar baroffset after a move", ...)`.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| gap()/baroffset() histogram | pytest TestHistogramGap; U12-01/02 | kde_hist_fn_truth H01-H04 | yes |
| area()/boundary | pytest TestKdensityArea/Boundary; U12-02/03 | K01-K05 | yes (saved refit through S16's read) |
| droplines()/base() | pytest TestDroplines; U12-04/05 | F01-F04 | yes |
| nodropbase | pytest TestNodropbase; U12-06 | A01 | yes |
| bar baroffset() | pytest TestBaroffset; U12-07 | B01 | yes |
| refusals | U12-02, U12-08 | H02 H03 K02 K04 F02 F04 | n/a |

AC-12.1 stubs green; AC-12.2 U12-01..08 PASS; AC-12.3 dash.sthlp:3075-3077 no longer says droplines/base on function are not drawn and :2908-2912 names neither area()/boundary nor S11's fit clause (S12 writes the final sentence, R2-21); AC-12.4 TWOWAY_COVERAGE_AUDIT.md rows 29, 64, 65, 98, 99, 100 annotated `commit pending`; AC-12.5 GAPS3 C5 reads `Closed in WP-31 ... commit pending` and no residual entry is opened.

## Tasks

**Commit boundary.** 12-01..12-03 steps; 12-04 commits `Draw histogram gap() and baroffset(), kdensity area() and boundary, function droplines() and base(), area nodropbase, bar baroffset() (WP-31 C5)` on `wp31-s12`.

<task type="auto" id="12-01">
  <name>Write the failing tests and the truth extractor</name>
  <files>test/test_distribution_odds.py, scripts/extract_kde_hist_fn_truth.do, test/test_fixtures_are_committed.py</files>
  <action><![CDATA[Create scripts/extract_kde_hist_fn_truth.do on the skeleton of scripts/extract_default_base_truth.do (root guards :21-43, adopath/mata/ado load :45-48, python writer with _meta :147-186) measuring probes H01-H04, K01-K05, F01-F04, A01, B01 of this file's "Stata truth" (class values read as `local v = `.h1.plotregion1.plot1.bar_size'`; sersets through `serset use` into a frame and written as arrays; refusal probes with `capture noisily` and the log line captured by `cert_log_has`-style tempfile logging). Run it through `DASH_REPO=<repo> scripts/stata_slot.sh <scratch> <repo>/scripts/extract_kde_hist_fn_truth.do`; `git add -f test/fixtures/kde_hist_fn_truth.json`; add the name to test_fixtures_are_committed.py. Create test/test_distribution_odds.py with every stub of "TDD test stubs". Run `python3 -m pytest test/test_distribution_odds.py -q -p no:randomly > <scratch>/12-01-failure.txt; true`. Do not commit.]]></action>
  <verify><![CDATA[grep -c "FAILED" <scratch>/12-01-failure.txt prints >= 14; python3 -c "import json;d=json.load(open('test/fixtures/kde_hist_fn_truth.json'));print(sorted(k for k in d if k!='_meta'))" prints the probe ids H01..B01.]]></verify>
  <done>The regression tests fail against 6370ca4 and twoway's truth for the seven options is committed.</done>
</task>

<task type="auto" id="12-02">
  <name>Declare the six options and add twoway's refusals</name>
  <files>dash.ado, dash_parse.mata, test/test_unsupported_report_is_true.py</files>
  <action><![CDATA[dash.ado: add `GAP(string) BAROFFset(string) AREA(string) BOUNDARY DROPlines(string asis) noDROPBase ///` after :1195 (`START(string) ///`); six `sreturn local` lines after :1524 (`sreturn local nodropbase : copy local dropbase`); append `gap baroffset area boundary droplines nodropbase` to the JSON key list after `pwidth lpvar` (:4458); in `_dash_option_rules` plot tokens add `gap=num,0,100  baroffset=num  droplines=numlist,1` after `start=num` (:3001); add to `_dash_process_segment` after :5574 the checks of TR-12.2 and TR-12.1's `gap(100)` and `area(<=0)` refusals with the texts copied from test/fixtures/kde_hist_fn_truth.json (H02, K02, K04, F02, F04) -- read them from the fixture while writing, type them as constants in the ado, and let U12-02 prove them; pass `droplines()` to `_dash_fn_points`' generator call (`twoway__function_gen ..., droplines(`droplines')`) and store `r(dropxy)` as `"drops":[[x,y],...]` in the points object through `_dash_fn_points_json` (extend it with an optional dropxy string argument). dash_parse.mata: delete the rows at :6263, :6272, :6297-6298; if U12-01's fixture shows twoway refuses a repeated gap()/area() (rc 198), add `gap area baroffset boundary droplines dropbase` to `_dash_rep_unique` (:6207-6214) with a `// WP-31 C5` comment. test_unsupported_report_is_true.py: apply TR-12.8 (LIVE_VALUES, FLAGS, declared count comment `# 196 -> 202: C5 ...`; recount with `python3 -c "from test.test_unsupported_report_is_true import _declared_plot as d;print(len(d()))"` and write the measured number).]]></action>
  <verify><![CDATA[python3 -m pytest test/test_distribution_odds.py::TestTheAdoText test/test_unsupported_report_is_true.py test/test_abbreviations.py -q prints 0 failed; grep -c '"baroffset"' dash_parse.mata prints 0 (row deleted) or 1 (the _dash_rep_unique entry only).]]></verify>
  <done>dash.ado declares the six options, refuses what twoway refuses with twoway's words, and stores droplines' (x, f(x)) pairs from twoway's own generator.</done>
</task>

<task type="auto" id="12-03">
  <name>Draw the seven options in the mappers</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[Apply TR-12.4 in `_histogram_quads`/`map_histogram` (:17863-18060; config keys gap/baroffset at :18011-18054), TR-12.5 in `map_kdensity` (:18275-18312, config :18380-18412), TR-12.6 in `map_function` (:20675-20688; add `"y0"` to `_BASE_PROPS` beside the assert at :15496; place `_dash_numlist_floats` right after `_dash_range_pair` :20933-20967 and add it to the functions copy tuple after `"_dash_fit_points_of",` -- S11's entry, merged before S12 -- or after "_dash_reference_lines" :47223 if S11 has not landed), TR-12.7 in `map_area` (:15209-15230) and `map_bar` (:15357-15405, `_bar_extent` :15510-15556). Add the function_test_map.py entry of TR-12.9. Run `python3 -m pytest test/test_distribution_odds.py test/test_glyphs.py -k "Area or Bar or Histogram or Dot" test/test_statistical_truth.py -k kdensity test/test_function_expr.py test/test_axis_extents.py test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName test/test_function_test_map.py -q`.]]></action>
  <verify><![CDATA[The pytest line prints 0 failed; `grep -c "_dash_numlist_floats" dash_render.py` prints >= 3; `python3 -c "import dash_render as d;print('y0' in d.GlyphMapper._BASE_PROPS)"` prints True.]]></verify>
  <done>Both renderers draw gap(), baroffset(), area(), boundary, droplines(), base() on function and nodropbase.</done>
</task>

<task type="auto" id="12-04">
  <name>Certify, document and commit C5</name>
  <files>test/test_wp31_truth.cscript, test/test_option_validation.cscript, dash.sthlp</files>
  <action><![CDATA[Append block `* ==== S12 C5: distribution, area and bar odds ====` with U12-01..U12-07 above the marker line of test/test_wp31_truth.cscript (after S11's block if present) and U12-08 to test_option_validation.cscript; run both through drivers under scripts/stata_slot.sh with `WP31_ONLY=S12`. dash.sthlp: rewrite :3075-3077 (`twoway also takes base() on dot ... and on function, as the base of droplines() -- neither of which dash draws`) to `... and on function, as the base of droplines(), which dash draws (default: twoway's base rule above); on dot it matters only with dotextend(no) (section 18)`; add `{synopt:{opt gap(#)}}histogram only: each bar is # percent narrower than its bin, 0 to 100 exclusive{p_end}`, `{synopt:{opt baroffset(#)}}bar and histogram: each bar moved # bar widths, negative left{p_end}`, `{synopt:{opt area(#)}}kdensity: densities multiplied by #, positive{p_end}`, `{synopt:{opt boundary}}kdensity: the curve evaluated one bandwidth past the data at each end; not with range(){p_end}`, `{synopt:{opt droplines(numlist)}}function: vertical lines from the base to the curve at each x, within range(){p_end}` to the Statistical Layer Options synoptset (after the `base()` entry at :3068-3078) and `{opt nodropbase}` to the area paragraph the plot-types section owns for area (grep "{ul:area" dash.sthlp); rewrite the sentence at :2908-2912 to its final text (S12 owns it, merged last in batch 4, R2-21): remove `area() and boundary on kdensity` AND S11's clause `atobs, estcmd(), estopts() and predopts() on the fits`, so it names only `a kernel written as an option of its own (a bare gaussian)` -- S11 does not touch this sentence. TWOWAY_COVERAGE_AUDIT.md rows 29, 64, 65, 98, 99, 100: append `[WP-31 C5, commit pending: corrected -- <the options of that row> drawn]`. BUGS.md: close C5's entry with the Resolution form (both renderers; the saved-page refit of the four keys is S16's batch-4 read, D-12b; no Residual clause). GAPS3 §9: `- **C5 Tracked:** Closed in WP-31, BUGS.md "<C5 title>", commit pending.` (A11: the merger's step k.3b fills the sha; the audit, BUGS.md, GAPS3.md and CHANGELOG.md are the closing task's implied files, A13). Replace the `<!-- WP-31 C5 -->` markers (Results: "histogram mpg, gap(20): bars 0.8 bin wide (was: full width)"; Changed behaviour: "gap() outside 0-100, area() not positive, boundary with range(), a dropline outside range() are refused, twoway's words"). Run `python3 -m pytest test/test_distribution_odds.py test/test_help_conformance.py test/test_tracking_documents.py -q`; commit with the BRIEF body forms; grep the message for `claude|anthropic`.]]></action>
  <verify><![CDATA[Stata logs show "U12-01 PASS" .. "U12-08 PASS" and no " FAIL"; pytest prints 0 failed; `git log -1 --format=%s` ends "(WP-31 C5)"; `grep -c "C5 Tracked:\*\* Closed in WP-31" GAPS3.md` prints 1; `grep -c "atobs, estcmd(), estopts() and predopts()" dash.sthlp` prints 0.]]></verify>
  <done>C5 is closed in one commit with its tests, fixture, help, audit, BUGS.md, GAPS3 and CHANGELOG lines.</done>
</task>

## Section completion criteria

- All stubs green, U12-01..08 PASS, no test deleted, counts moved with comments.
- `_dash_numlist_floats` on the copy list; `"y0"` in `_BASE_PROPS`; config keys `gap baroffset area boundary` written.
- Help (the final :2908-2912 sentence), audit, BUGS.md closed, GAPS3 `Closed ... commit pending` line, CHANGELOG lines in the one commit; the four config keys `gap`, `baroffset`, `area`, `boundary` written for S16.

## Notes

- **Renderer order:** droplines Segment is added BEFORE the curve (twoway `_fr_droplines_draw.ado:16-51` draws the drops first); `_apply_line_opts` on the Segment so `lcolor()` styles both.
- **Served copy list (R2):** `_dash_numlist_floats` after `"_dash_fit_points_of",` (S11's entry; else after `_dash_reference_lines` :47223). `_tag_base`/`_bar_extent` are methods: no entry.
- **Hull:** `test_axis_extents.py TestBars` reads `__dash_bar_xc`/`__dash_bar_w`; a numeric-axis bar with baroffset now writes `_BAR_XC`, which that test already accepts (both forms).
- **Same-batch help hand-off (R3, R2-21):** S12 (merged last in batch 4) owns the sentence at dash.sthlp:2908-2912 and writes its final text with both its own clause and S11's fit clause removed; S11 edits only :3210-3211 and adds its `{ul:Fit options.}` paragraph. S12 also owns :3068-3078 (the `base()` synopt) and the area paragraph.
- **Copy-list anchor (R2, R2-20):** `_dash_numlist_floats` goes after `"_dash_fit_points_of",` (S11's entry, landed before S12 in batch 4), falling back to `"_dash_reference_lines",` only if S11 has not landed.
- **Fixture rule (R7):** `kde_hist_fn_truth.json` is regenerated, never patched; the refusal texts in dash.ado are typed from it once and proved by U12-02.
- **python_exec hazard:** the extractor exits 601 when `c(python_exec)` is empty; rerun when the slot frees.
- **Security:** `droplines()` values reach the generator through `numlist`-validated text only (`_dash_option_rules` `droplines=numlist,1` runs first); `area()`/`gap()`/`baroffset()` are numbers through `_stat_option_float`; no text reaches HTML.
- **Merge rules cited:** R1, R2, R7, R8, R9, R10, R12 (S12 is batch 4's histogram/kdensity/function/area/bar mapper owner; S16 owns `_FILTER_JS` and reads S12's keys, A22).
- **Commit body lines:** `Regression: test/test_distribution_odds.py::TestHistogramGap::test_bars_are_shrunk_about_their_centre[saved] -- failed at 6370ca4 with <text>`; `Fixture: test/fixtures/kde_hist_fn_truth.json (scripts/extract_kde_hist_fn_truth.do)`; `BUGS.md: "<C5 title>" (closed)`; `GAPS3: C5 Tracked`.
- **Decisions for maintainer ratification:** D-12a (baroffset silent, not named, on types where twoway draws nothing different); D-12b is settled by DECISIONS A22 (S16 reads the new keys in batch 4; no residual, no cue needed); D-12e (nodropbase as a Patch).
